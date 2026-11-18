"""Evento «arrastrar»: una crecida arrastra basura por el cauce de un río y la abre en abanico en su boca, sobre un lago.

Resuelto: {pieza, cauce: [x0, y0, x1, y1, …] (km, de la fuente a la boca, a pasos ≤ 0.25 km), largo_km, boca: [x, y],
mancha: [x0, y0, …] (km: dónde queda flotando cada partícula, dentro del lago si hay una pieza lagos que lo contenga),
barda: [x0, y0, …] (km: las boyas de la barda, si se pide), intensidad, abanico_km, queda, prota}.

El cauce sale de `puntos` ([[lon, lat], …] de la fuente a la boca) o, sin ellos, de la pieza: una que publique `cauce`
(km: [x0, y0, …] o [[x, y], …], de la fuente a la boca) o una `afluente` con sus `puntos` en [lon, lat]. Una pieza `rios`
no trae un cauce con sentido: con ella, `puntos` es obligatorio (la pieza solo se aviva mientras baja la crecida).
El azar (dónde cae cada partícula) es fijo: sale de los parámetros del evento, no de la corrida."""
import math
import random

PASO = 0.25        # km entre muestras del cauce


def _par(v):
    return isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(q, (int, float)) for q in v)


def _como_km(pts, X):
    """[[a, b], …]: si parecen [lon, lat] del set (caen dentro del set al convertirlos), a km; si no, ya son km."""
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
    p = pz.get("puntos")
    if pz.get("tipo") == "afluente" and isinstance(p, list) and p and all(_par(q) for q in p):
        return _como_km(p, X)
    return None


def _densificar(pts):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(math.ceil(d / PASO)))
        for k in range(1, n + 1):
            out.append((x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n))
    return out


def _dentro(x, y, an):
    """Punto en polígono (anillo plano [x0, y0, …])."""
    n, c = len(an) // 2, False
    j = n - 1
    for i in range(n):
        xi, yi, xj, yj = an[2 * i], an[2 * i + 1], an[2 * j], an[2 * j + 1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            c = not c
        j = i
    return c


def _dist_anillo(x, y, an):
    n, best = len(an) // 2, float("inf")
    for i in range(n):
        ax, ay, bx, by = an[2 * i], an[2 * i + 1], an[2 * ((i + 1) % n)], an[2 * ((i + 1) % n) + 1]
        dx, dy = bx - ax, by - ay
        u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / ((dx * dx + dy * dy) or 1e-12)))
        best = min(best, math.hypot(x - ax - u * dx, y - ay - u * dy))
    return best


def _lago(X, bx, by, R):
    """El anillo de una pieza lagos que contiene la boca o queda a ≤ max(2 km, R) de ella (el más cercano)."""
    mejor = None
    for pz in X.piezas:
        for an in (pz.get("anillos") or []) if pz.get("tipo") == "lagos" else []:
            d = 0.0 if _dentro(bx, by, an) else _dist_anillo(bx, by, an)
            if d <= max(2.0, R) and (mejor is None or d < mejor[0]):
                mejor = (d, an)
    return mejor[1] if mejor else None


def resolver(e, X, que):
    pz = None
    if e.get("pieza"):
        pz = X.por_id.get(e["pieza"])
        if not pz:
            raise X.m3.Falla("M3D2", "%s: `pieza` «%s» no es una pieza de esta maqueta" % (que, e["pieza"]))
    if e.get("puntos"):
        pts = [X.S.xy(q[0], q[1]) for q in e["puntos"]]
    else:
        pts = _cauce_de_pieza(pz, X) if pz else None
    if not pts or len(pts) < 2:
        raise X.m3.Falla("M3D2", "%s: arrastrar necesita el cauce: `puntos` [[lon, lat], …] de la fuente a la boca, o una pieza "
                         "(afluente) que lo publique; una pieza rios no trae uno con sentido" % que)
    cad = _densificar([(float(x), float(y)) for x, y in pts])
    L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(cad, cad[1:]))
    if L < 0.8:
        raise X.m3.Falla("M3D2", "%s: el cauce mide %.2f km: arrastrar necesita al menos 0.8 km de río" % (que, L))
    I = float(e.get("intensidad", 0.7))
    R = float(e.get("abanico_km", 1.2))
    bx, by = cad[-1]
    # el sentido del río en la boca: del punto a ≈ 1.5 km aguas arriba hasta la boca
    s, k = 0.0, len(cad) - 1
    while k > 0 and s < min(1.5, L / 3):
        s += math.hypot(cad[k][0] - cad[k - 1][0], cad[k][1] - cad[k - 1][1])
        k -= 1
    dx, dy = bx - cad[k][0], by - cad[k][1]
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    an = _lago(X, bx, by, R)
    if an is None:
        X.avisos.append("%s: ninguna pieza lagos junto a la boca: el abanico se abre igual, sobre el relieve" % que)
    else:   # el abanico mira hacia el agua: el promedio de lo que es lago a menos de R de la boca, mezclado con el río
        sx = sy = c = 0
        for i in range(-12, 13):
            for j in range(-12, 13):
                x, y = bx + R * i / 12, by + R * j / 12
                if math.hypot(x - bx, y - by) <= R and _dentro(x, y, an):
                    sx, sy, c = sx + x - bx, sy + y - by, c + 1
        if c:
            lx, ly = sx / c, sy / c
            ln = math.hypot(lx, ly)
            if ln > 1e-6:
                dx, dy = 0.35 * dx + 0.65 * lx / ln, 0.35 * dy + 0.65 * ly / ln
                n = math.hypot(dx, dy) or 1.0
                dx, dy = dx / n, dy / n
        else:
            X.avisos.append("%s: el lago no queda a menos de abanico_km de la boca: el abanico se abre en el sentido del río" % que)
    barda = bool(e.get("barda", False))
    rnd = random.Random("arrastrar|%.3f|%.3f|%.3f|%.3f" % (bx, by, I, R))
    N = int(round(260 + 640 * I))
    medio = math.radians(38 + 30 * I)          # medio ángulo del abanico
    px, py = -dy, dx
    mancha = []
    for _ in range(N):
        for intento in range(40):
            u, v = rnd.random(), rnd.random()
            r = R * ((0.6 + 0.36 * u ** 0.45) if barda else (0.1 + 0.9 * u ** 0.7))
            a = (2 * v - 1) * medio * (0.55 + 0.45 * (r / R))
            x, y = bx + r * (dx * math.cos(a) + px * math.sin(a)), by + r * (dy * math.cos(a) + py * math.sin(a))
            if an is None or _dentro(x, y, an):
                mancha += [round(x, 3), round(y, 3)]
                break
    if len(mancha) < 40:
        raise X.m3.Falla("M3D2", "%s: el abanico no cabe en el lago junto a la boca (¿la boca está en el lago? sube abanico_km)" % que)
    boyas = []
    if barda:      # la barda: una hilera de boyas en arco a R de la boca, solo donde hay agua
        arco = 2 * medio * R
        nb = max(12, min(140, int(arco / 0.03)))
        for i in range(nb):
            a = -medio + 2 * medio * i / (nb - 1)
            x, y = bx + R * (dx * math.cos(a) + px * math.sin(a)), by + R * (dy * math.cos(a) + py * math.sin(a))
            if an is None or _dentro(x, y, an):
                boyas += [round(x, 3), round(y, 3)]
    return {"pieza": e.get("pieza") or "", "cauce": [round(v, 3) for q in cad for v in q], "largo_km": round(L, 3),
            "boca": [round(bx, 3), round(by, 3)], "mancha": mancha, "barda": boyas, "intensidad": I, "abanico_km": R,
            "queda": e.get("queda", True) is not False, "prota": bool(pz and pz.get("protagonista"))}


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
    """Dónde pasa: el frente que baja por el cauce y la boca; luego la boca y el abanico (M3D6)."""
    b = tuple(e["boca"])
    if u < 0.62:
        return [_en_s(e, e["largo_km"] * min(1.0, 0.3 + u / 0.62 * 0.7)), b]
    m = e["mancha"]
    lejos = max(range(0, len(m), 2), key=lambda i: math.hypot(m[i] - b[0], m[i + 1] - b[1]))
    return [b, (m[lejos], m[lejos + 1])]


def origen(e, G):
    """La portada: la boca (allí se lee la mancha)."""
    return tuple(e["boca"])
