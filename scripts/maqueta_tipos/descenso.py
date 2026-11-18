"""Evento «descenso»: un flujo piroclástico que baja en pulsos por el cauce de una barranca, desde el cráter.

Resuelto: {pieza, cauce: [x0, y0, x1, y1, …] (km, del cráter hacia abajo, a pasos ≤ 0.12 km), largo_km, alcance_km
(= hasta · largo), ancho_km, pulsos, hasta, fin: [x, y] (adonde llega el último pulso), abanico: [x0, y0, …] (km: dónde
queda cada bloque del depósito que se sale del cauce, si hay `desborde`), dir_abanico: [dx, dy], abanico_km, queda,
apaga: [[x, y, modo, u], …] (cada luz que queda cubierta: modo 0 = por el cauce, u = s/alcance; modo 1 = por el
abanico, u = distancia/abanico_km), apaga_ids, prota}.

El cauce sale de `puntos` ([[lon, lat], …] del cráter hacia abajo) o de la pieza: una que publique `cauce` (km, plano o
pares), `cadena` ([[x, y, s, …]] km), un camino propio (`_caminos`) o sus `puntos` en [lon, lat] (barranca, afluente).
El azar (dónde cae cada bloque) es fijo: sale de los parámetros del evento, no de la corrida."""
import math
import random

PASO = 0.12        # km entre muestras del cauce


def _par(v):
    return isinstance(v, (list, tuple)) and len(v) >= 2 and all(isinstance(q, (int, float)) for q in v[:2])


def _como_km(pts, X):
    if all(-180 <= a <= 180 and -90 <= b <= 90 for a, b in pts):
        km = [X.S.xy(a, b) for a, b in pts]
        if all(abs(x) < 3000 and abs(y) < 3000 for x, y in km):
            return [(float(x), float(y)) for x, y in km]
    return [(float(a), float(b)) for a, b in pts]


def _cauce_de_pieza(pz, X):
    c = pz.get("cauce")
    if isinstance(c, list) and c:
        if all(isinstance(v, (int, float)) for v in c):
            return [(float(c[i]), float(c[i + 1])) for i in range(0, len(c) - 1, 2)]
        if all(_par(q) for q in c):
            return [(float(q[0]), float(q[1])) for q in c]
    c = pz.get("cadena")
    if isinstance(c, list) and len(c) >= 2 and all(_par(q) for q in c):
        return [(float(q[0]), float(q[1])) for q in c]
    cam = pz.get("_caminos") or {}
    for nombre in sorted(cam, key=lambda k: (k != pz.get("id"), k)):
        c = cam[nombre]
        if isinstance(c, list) and len(c) >= 2 and all(_par(q) for q in c):
            return [(float(q[0]), float(q[1])) for q in c]
    p = pz.get("puntos")
    if isinstance(p, list) and len(p) >= 2 and all(_par(q) for q in p):
        return _como_km([(q[0], q[1]) for q in p], X)
    return None


def _densificar(pts):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(math.ceil(d / PASO)))
        for k in range(1, n + 1):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out


def _corta(cad, s_fin):
    out, acum = [cad[0]], 0.0
    for a, b in zip(cad, cad[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if acum + d >= s_fin:
            u = (s_fin - acum) / (d or 1)
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            return out
        acum += d
        out.append(b)
    return out


def _proy(cad, x, y):
    """(s, distancia) del punto más cercano del cauce."""
    best, acum = (0.0, float("inf")), 0.0
    for a, b in zip(cad, cad[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        d2 = dx * dx + dy * dy or 1e-12
        u = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / d2))
        dd = math.hypot(x - a[0] - u * dx, y - a[1] - u * dy)
        if dd < best[1]:
            best = (acum + u * math.sqrt(d2), dd)
        acum += math.sqrt(d2)
    return best


def resolver(e, X, que):
    pz = X.por_id.get(e.get("pieza")) if e.get("pieza") else None
    if e.get("pieza") and not pz:
        raise X.m3.Falla("M3D2", "%s: `pieza` «%s» no es una pieza de esta maqueta" % (que, e["pieza"]))
    if e.get("puntos"):
        pts = [X.S.xy(q[0], q[1]) for q in e["puntos"]]
    else:
        pts = _cauce_de_pieza(pz, X) if pz else None
    if not pts or len(pts) < 2:
        raise X.m3.Falla("M3D2", "%s: descenso necesita el cauce: una pieza barranca (o afluente) que lo publique, o `puntos` "
                         "[[lon, lat], …] del cráter hacia abajo" % que)
    cad = _densificar([(float(x), float(y)) for x, y in pts])
    L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(cad, cad[1:]))
    if L < 0.8:
        raise X.m3.Falla("M3D2", "%s: el cauce mide %.2f km: descenso necesita al menos 0.8 km" % (que, L))
    hasta = float(e.get("hasta", 1))
    alc = max(0.4, L * hasta)
    tramo = _corta(cad, alc)
    fx, fy = tramo[-1]
    # el sentido en el extremo: del punto a ≈ 1 km cauce arriba hasta el fin
    s, k = 0.0, len(tramo) - 1
    while k > 0 and s < min(1.0, alc / 3):
        s += math.hypot(tramo[k][0] - tramo[k - 1][0], tramo[k][1] - tramo[k - 1][1])
        k -= 1
    dx, dy = fx - tramo[k][0], fy - tramo[k][1]
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    R = float(e.get("abanico_km", 1))
    ancho = float((pz or {}).get("ancho_km", 0.3) or 0.3)
    ancho = max(0.08, min(1.2, ancho))
    desb = []
    for ref in e.get("desborde") or []:
        l = X.lugar(ref, que + " → desborde")
        desb.append((float(l["x"]), float(l["y"])))
    abanico = []
    if desb:
        cx = sum(p[0] for p in desb) / len(desb) - fx
        cy = sum(p[1] for p in desb) / len(desb) - fy
        cn = math.hypot(cx, cy)
        if cn > 1e-6:
            dx, dy = 0.3 * dx + 0.7 * cx / cn, 0.3 * dy + 0.7 * cy / cn
            n = math.hypot(dx, dy) or 1.0
            dx, dy = dx / n, dy / n
        lejos = max(math.hypot(p[0] - fx, p[1] - fy) for p in desb)
        if lejos > R * 1.05:
            X.avisos.append("%s: un lugar de `desborde` queda a %.2f km del fin del cauce y el abanico llega a %.2f km: no lo cubre "
                            "(sube abanico_km)" % (que, lejos, R))
        rnd = random.Random("descenso|%.3f|%.3f|%.3f|%d" % (fx, fy, R, len(desb)))
        px, py = -dy, dx
        medio = math.radians(48)
        N = 520
        for i in range(N):
            u, v = rnd.random(), rnd.random()
            if i < N * 0.3 and desb:     # un tercio se junta sobre los lugares que cubre
                q = desb[i % len(desb)]
                rr, aa = 0.28 * R * math.sqrt(u), 6.2832 * v
                x, y = q[0] + rr * math.cos(aa), q[1] + rr * math.sin(aa)
                if math.hypot(x - fx, y - fy) > R:
                    continue
            else:
                r = R * (0.05 + 0.95 * u ** 0.6)
                a = (2 * v - 1) * medio * (0.5 + 0.5 * r / R)
                x = fx + r * (dx * math.cos(a) + px * math.sin(a))
                y = fy + r * (dy * math.cos(a) + py * math.sin(a))
            abanico += [round(x, 3), round(y, 3)]
    # las luces que quedan cubiertas
    pedidas = e.get("apaga")
    apaga, ids = [], []
    if pedidas:
        for p in X.piezas:
            if p.get("tipo") != "luces":
                continue
            for q in p.get("puntos") or []:
                if not (pedidas == "todos" or q[3] in pedidas):
                    continue
                x, y = float(q[0]), float(q[1])
                sq, dq = _proy(tramo, x, y)
                df = math.hypot(x - fx, y - fy)
                if abanico and df <= R * 1.02:
                    apaga.append([round(x, 3), round(y, 3), 1, round(min(1.0, df / R), 3)]); ids.append(q[3])
                elif dq <= ancho * 1.5 + 0.1:
                    apaga.append([round(x, 3), round(y, 3), 0, round(min(1.0, sq / alc), 3)]); ids.append(q[3])
                elif pedidas != "todos":
                    X.avisos.append("%s: la luz «%s» queda lejos del depósito: no se apaga" % (que, q[3]))
        if pedidas != "todos":
            faltan = [r for r in pedidas if r not in ids and not any(r == q[3] for p in X.piezas if p.get("tipo") == "luces" for q in p.get("puntos") or [])]
            for r in faltan:
                X.avisos.append("%s: «%s» no es una luz de ninguna pieza `luces`: no hay nada que apagar ahí" % (que, r))
    return {"pieza": e.get("pieza") or "", "cauce": [round(v, 3) for q in cad for v in q], "largo_km": round(L, 3),
            "alcance_km": round(alc, 3), "ancho_km": round(ancho, 3), "pulsos": int(e.get("pulsos", 3)), "hasta": hasta,
            "fin": [round(fx, 3), round(fy, 3)], "abanico": abanico, "dir_abanico": [round(dx, 4), round(dy, 4)],
            "abanico_km": R, "queda": e.get("queda", True) is not False, "apaga": apaga, "apaga_ids": ids,
            "prota": bool(pz and pz.get("protagonista"))}


def _en_s(e, s):
    c, acum = e["cauce"], 0.0
    for i in range(2, len(c) - 1, 2):
        d = math.hypot(c[i] - c[i - 2], c[i + 1] - c[i - 1])
        if acum + d >= s:
            u = (s - acum) / (d or 1)
            return c[i - 2] + (c[i] - c[i - 2]) * u, c[i - 1] + (c[i + 1] - c[i - 1]) * u
        acum += d
    return c[-2], c[-1]


def puntos(e, u, G):
    """Dónde pasa: el cráter y el frente que baja; al final, el fin del cauce y lo más lejano del abanico (M3D6)."""
    c0 = (e["cauce"][0], e["cauce"][1])
    f = tuple(e["fin"])
    if u < 0.8:
        return [c0, _en_s(e, e["alcance_km"] * min(1.0, 0.25 + u))]
    m = e["abanico"]
    if not m:
        return [c0, f]
    lejos = max(range(0, len(m), 2), key=lambda i: math.hypot(m[i] - f[0], m[i + 1] - f[1]))
    return [f, (m[lejos], m[lejos + 1])]


def origen(e, G):
    """La portada: el cráter, de donde salen los pulsos."""
    return e["cauce"][0], e["cauce"][1]
