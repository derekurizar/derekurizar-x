"""Pieza «cafetal»: una ladera sembrada de café sobre el suelo del mundo: el polígono (`area`: una zona del mundo por su
id; o `puntos`: [x, y] en metros en un esquema) sube hacia `rumbo` hasta `pendiente_m` en un talud suave (sin muros de
terraza), con `hileras` hileras de cafetos y sus racimos de cereza (`maduras`: la parte roja, en el rojo del estilo) y, con
`sombra` > 0, árboles de sombra encima. Resuelta: {poligono: [x0, y0, …], hileras, pendiente_m, rumbo, maduras, sombra,
semilla, personas, usa}. La pieza PUBLICA su relieve (`_alturas`: la ladera, la misma que dibuja cafetal.js): un actor
de pie o que camine dentro del polígono, la cámara que mire ahí y las marcas quedan sobre la ladera, sin `lev_m`."""
import math

from maqueta_tipos import _movimiento as MV
from maqueta_tipos import _mundo as MU
from maqueta_tipos import _relieve as RL

TAU = 2 * math.pi


def ladera(pol, rumbo, hileras, pendiente, semilla, orden, m1):
    """La altura de la ladera sobre su base, f(x, y), en unidades de la escena: el MISMO perfil de cafetal.js (`alto`).
    pol: [x0, y0, …]; pendiente y m1 (un metro) en unidades; orden: cuántos cafetales van antes (el azar de la curva)."""
    r = math.radians(rumbo)
    ux, uy = math.cos(r), math.sin(r)
    vx, vy = -uy, ux
    pts = MU.pares(pol)
    S, Wv = [x * ux + y * uy for x, y in pts], [x * vx + y * vy for x, y in pts]
    s0, L, N = min(S), (max(S) - min(S)) or 1e-9, int(hileras)
    w0, WS, RS = min(Wv), max(Wv) - min(Wv), ((max(S) - min(S)) or 1e-9) / int(hileras)
    BETA, C0 = 0.6, 0.12
    g0 = math.sin(-TAU * C0)
    AMP, fase, lam0 = 0.16 * RS, MV.hash_(semilla * 7919 + orden * 104729, 90) * TAU, 1.7 * max(WS, m1)

    def alto(x, y):
        s = (x * ux + y * uy) - AMP * math.sin(TAU * ((x * vx + y * vy) - w0) / lam0 + fase)
        u = min(max((s - s0) / L * N, 0.0), float(N))
        k = min(N - 1, int(math.floor(u)))
        f = u - k
        return 0.15 * m1 + pendiente / N * (k + f - BETA * (math.sin(TAU * (f - C0)) - g0) / TAU)
    return alto, RS


def resolver(p, X, que):
    if (p.get("area") is None) == (p.get("puntos") is None):
        raise X.m3.Falla("M3D2", "%s: un cafetal lleva `area` (el id de una zona del mundo) o `puntos` (el polígono), una de las dos" % que)
    if p.get("puntos") is not None:
        if len(p["puntos"]) < 3:
            raise X.m3.Falla("M3D2", "%s: `puntos` necesita al menos 3" % que)
        pol = [v for ref in p["puntos"] for v in (lambda l: (l["x"], l["y"]))(X.lugar(ref, que))]
    else:
        Z = MU.capa(X, "zonas", que)["zonas"]
        pols = [MU.plano(z["puntos"]) for z in Z if z["id"] == p["area"]]
        if not pols:
            ids = [z["id"] for z in Z]
            raise X.m3.Falla("M3D2", "%s: «%s» no es una zona del mundo (hay: %s%s)" % (que, p["area"], ", ".join(ids[:12]), "…" if len(ids) > 12 else ""))
        pol = pols[0]
    xs, ys = pol[0::2], pol[1::2]
    if max(xs) - min(xs) < 20 or max(ys) - min(ys) < 20:
        raise X.m3.Falla("M3D2", "%s: el cafetal mide menos de 20 m de lado: no se lee como ladera" % que)
    r = {"poligono": [round(v, 1) for v in pol], "hileras": int(p["hileras"]), "pendiente_m": float(p["pendiente_m"]),
         "rumbo": float(p["rumbo"]), "maduras": float(p["maduras"]), "sombra": float(p.get("sombra") or 0), "semilla": int(p["semilla"]), "personas": int(p["personas"])}
    if r["personas"]:
        r["usa"] = ["persona"]
    # su relieve: la ladera en una malla de ≈ un cuarto de hilera (1–2.5 m), sobre el suelo del mundo bajo cada punto
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    orden = sum(1 for q in X.piezas if q.get("tipo") == "cafetal")
    alto, RS = ladera(r["poligono"], r["rumbo"], r["hileras"], r["pendiente_m"] / um, r["semilla"], orden, 1 / um)
    suelo = getattr(X.S, "suelo_base", X.S.suelo)
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    base0 = suelo(*centro_sw(r["poligono"], r["rumbo"]))
    paso = min(2.5 / um, max(1.0 / um, RS / 4))
    r["_alturas"] = [RL.malla([x0, y0, x1, y1], min(160, math.ceil((x1 - x0) / paso) + 1), min(160, math.ceil((y1 - y0) / paso) + 1),
                              lambda x, y: base0 - suelo(x, y) + alto(x, y), r["poligono"])]
    return r


def centro_sw(pol, rumbo):
    """El centro de la caja del polígono en sus ejes (sube, ancho): donde cafetal.js toma su base."""
    r = math.radians(rumbo)
    ux, uy = math.cos(r), math.sin(r)
    pts = MU.pares(pol)
    S, Wv = [x * ux + y * uy for x, y in pts], [-x * uy + y * ux for x, y in pts]
    s, w = (min(S) + max(S)) / 2, (min(Wv) + max(Wv)) / 2
    return s * ux - w * uy, s * uy + w * ux


def tramos(pz):
    pts = MU.pares(pz["poligono"])
    return [[(x, y, False) for x, y in pts + pts[:1]]]


def centro(pz, G):
    return MU.centroide(MU.pares(pz["poligono"]))
