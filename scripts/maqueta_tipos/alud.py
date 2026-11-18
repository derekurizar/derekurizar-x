"""Evento «alud»: un flujo de escombros (lodo, piedras y árboles) que se desprende en lo alto de una pieza `faldavolcan`,
baja por su cauce y se abre en un lóbulo sobre el pueblo. Sin erupción ni lava: solo lo que baja del monte.

El camino del lodo sale de la misma cuenta que la pieza (faldavolcan.cauce_local): de `desde` (su proyección sobre el
cauce) al final del cauce en la plaza, de ahí recto a `hacia` y, pasado `hacia`, la punta del lóbulo. Todo en METROS
LOCALES de la pieza (u: hacia el volcán; v: a su izquierda); el módulo lo lleva al mundo con el mismo `rumbo`, `tamano` y
centro que la pieza.

- `ancho_m` (metros reales): el ancho del frente cuando llega al pueblo; en la ladera va de 0.35 a 0.65 de eso.
- `cubre` (0–1): qué tanto del pueblo tapa el lóbulo: 0 = solo la franja de `ancho_m`; 1 = hasta LOBULO m del eje.
- `frente(x)` (la MISMA cuenta en alud.js): dónde va el frente (m locales desde el inicio) en la fracción x de `dur`.
Resuelto: {pieza, fx, fy, rumbo, tamano, semilla, k, camino [[u, v, s]], s_pie, s_hacia, s_fin, s_tope, hw0, lobulo,
lr, arboles}."""
import math

from maqueta_tipos import faldavolcan as FV

LOBULO = 175.0      # m locales: con cubre = 1, el lodo llega hasta aquí a cada lado del eje (el pueblo entero)
S0 = 26.0           # m locales: lo que ya se desprendió en el instante 0 (la portada)
RAMPA = 14.0        # m locales: el largo del frente (de nada a todo el espesor)
CONVEXO = 0.55      # cuánto se atrasan las orillas del frente (× medio ancho × w²)


def frente(x, s0, s_tope):
    x = min(1.0, max(0.0, x))
    return s0 + (s_tope - s0) * (0.5 - 0.5 * math.cos(math.pi * x ** 0.8))


def _lugar(X, ref, pid, que):
    if isinstance(ref, str) and ref in X.publicados:
        return X.lugar(ref, que)
    if isinstance(ref, str) and (pid + "." + ref) in X.publicados:
        return X.lugar(pid + "." + ref, que)
    return X.lugar(ref, que)


def _cerca(pts, u, v):
    best, bi = 1e18, 0
    for i, (a, b) in enumerate(pts):
        d = (a - u) ** 2 + (b - v) ** 2
        if d < best:
            best, bi = d, i
    return bi, math.sqrt(best)


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz or pz.get("tipo", "faldavolcan") != "faldavolcan" or "rumbo" not in pz:
        raise X.m3.Falla("M3D2", "%s: `pieza` tiene que ser una faldavolcan (el alud baja por su cauce)" % que)
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    tam = float(pz["tamano"])
    k = tam / um
    a = math.radians(float(pz["rumbo"]))
    ux, uy = math.cos(a), math.sin(a)
    ph = FV.fase(int(pz["semilla"]))

    def local(x, y):
        dx, dy = (x - pz["x"]) / k, (y - pz["y"]) / k
        return dx * ux + dy * uy, -dx * uy + dy * ux

    l0 = _lugar(X, e.get("desde", "ladera-alta"), pid, que + " → desde")
    l1 = _lugar(X, e.get("hacia", "pueblo"), pid, que + " → hacia")
    u0, v0 = local(l0["x"], l0["y"])
    u1, v1 = local(l1["x"], l1["y"])
    cl = FV.cauce_local(ph)
    i0, d0 = _cerca(cl, u0, v0)
    i1, d1 = _cerca(cl, u1, v1)
    if i1 <= i0:
        raise X.m3.Falla("M3D2", "%s: el alud baja: `desde` tiene que quedar más arriba que `hacia` sobre el cauce de «%s»" % (que, pid))
    pts = []
    if d0 > 15:
        pts.append((u0, v0))
    pts += cl[i0:i1 + 1]
    if d1 > 15:
        pts.append((u1, v1))
    # la punta del lóbulo: más allá de `hacia`, en la dirección de los últimos ~40 m
    ancho_l = float(e.get("ancho_m", 120)) / tam
    cubre = float(e.get("cubre", 0.7))
    lob = max(ancho_l / 2, ancho_l / 2 + cubre * max(0.0, LOBULO - ancho_l / 2))
    lr = 0.75 * lob
    S = [0.0]
    for i in range(1, len(pts)):
        S.append(S[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    s_hacia = S[-1]
    j = len(pts) - 1
    while j > 0 and S[-1] - S[j] < 40:
        j -= 1
    du, dv = pts[-1][0] - pts[j][0], pts[-1][1] - pts[j][1]
    L = math.hypot(du, dv) or 1.0
    du, dv = du / L, dv / L
    for q in range(1, 7):
        f = lr * q / 6
        pts.append((pts[len(S) - 1][0] + du * f, pts[len(S) - 1][1] + dv * f))
        S.append(s_hacia + f)
    # el pie: donde el cauce sale del cono (r ≥ RB desde la cumbre)
    s_pie = s_hacia
    for (u, v), s in zip(pts, S):
        if math.hypot(u - FV.US, v) >= FV.RB:
            s_pie = s
            break
    s_pie = min(s_pie, s_hacia)
    s_fin = S[-1]
    s_tope = s_fin + CONVEXO * lob + RAMPA
    return {"pieza": pid, "fx": pz["x"], "fy": pz["y"], "rumbo": float(pz["rumbo"]), "tamano": tam,
            "semilla": int(pz["semilla"]), "k": k,
            "camino": [[round(u, 2), round(v, 2), round(s, 2)] for (u, v), s in zip(pts, S)],
            "s_pie": round(s_pie, 2), "s_hacia": round(s_hacia, 2), "s_fin": round(s_fin, 2), "s_tope": round(s_tope, 2),
            "hw0": round(ancho_l / 2, 2), "lobulo": round(lob, 2), "lr": round(lr, 2),
            "arboles": int(e.get("arboles", 12))}


def _mundo(e, u, v):
    a = math.radians(e["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    return e["fx"] + (u * ux - v * uy) * e["k"], e["fy"] + (u * uy + v * ux) * e["k"]


def _en(e, s):
    C = e["camino"]
    for i in range(1, len(C)):
        if C[i][2] >= s:
            a, b = C[i - 1], C[i]
            f = (s - a[2]) / ((b[2] - a[2]) or 1e-9)
            return _mundo(e, a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
    return _mundo(e, C[-1][0], C[-1][1])


def puntos(e, u, G):
    """El frente en la fracción u (y, cuando ya llegó, el centro del lóbulo y de dónde salió)."""
    s = min(e["s_fin"], frente(u, S0, e["s_tope"]))
    p = [_en(e, s)]
    if s > e["s_hacia"]:
        p.append(_en(e, e["s_hacia"]))
    return p


def origen(e, G):
    return _en(e, 0.0)
