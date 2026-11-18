"""Pieza «ciudadcolonial»: una ciudad colonial GENÉRICA en damero alrededor de su plaza mayor, centrada en `lugar` (la fuente)
y orientada por `rumbo` (hacia dónde queda el volcán de fondo visto desde la plaza: u; v a su izquierda). Todo en METROS
locales (u, v) × `tamano`; manzanas de 64 m y calles de 9 m (paso 73 m).

- Los lados de la plaza (solo el orden relativo): la catedral a la izquierda (+v), enfrente las casas con balcones (−v),
  el palacio hacia el volcán (+u) y el cabildo del otro lado (−u). Ningún lado es un dato de brújula.
- Sus LUGARES (`_lugares`; siempre también «<id>.<lugar>»): plaza, fuente, mercado, catedral, palacio, cabildo, portal y,
  con `volcan_fondo`, volcan (la cumbre).
- Su CAMINO «<id>.ronda»: la vuelta a la plaza por las calles que la rodean (sentido antihorario), por donde va el carretón;
  sirve para que un actor dé la vuelta a la plaza.
La misma cuenta de la ronda vive en video/maqueta/piezas/ciudadcolonial.js (función `ronda`).
Resuelta: {x, y, rumbo, tamano, manzanas, personas, volcan_fondo, semilla, usa}."""
import math

from maqueta_tipos.esquema import cadena

BLK, CALLE = 64.0, 9.0
PASO = BLK + CALLE
H2 = BLK / 2
VU, VH, VR = 1750.0, 560.0, 950.0            # el volcán de fondo: cumbre a VU por u, alto y radio de base (maqueta)
RONDA, RR = H2 + CALLE / 2 - 2.1, 3.0        # el carril de la ronda y el radio de sus esquinas
LUGARES = {
    "plaza": ("Plaza", (0.0, 0.0), 0.7),
    "fuente": ("Fuente", (0.0, 0.0), 0.5),
    "mercado": ("Mercado", (0.0, -21.0), 0.5),
    "catedral": ("Catedral", (15.0, 41.0 + 22.0), 0.7),
    "palacio": ("Palacio", (41.0 + 9.0, 0.0), 0.6),
    "cabildo": ("Cabildo", (-41.0 - 8.0, 0.0), 0.6),
    "portal": ("Portal", (0.0, -41.0 - 6.0), 0.5),
}


def ronda(a=RONDA, rc=RR):
    """El rectángulo de esquinas redondeadas alrededor de la plaza (u, v), antihorario y cerrado."""
    pts = []
    q = ((a, -a), (a, a), (-a, a), (-a, -a))
    for k, (cu, cv) in enumerate(q):
        a0 = -math.pi / 2 + k * math.pi / 2
        ccu = cu - math.copysign(rc, cu)
        ccv = cv - math.copysign(rc, cv)
        for j in range(7):
            a1 = a0 + (math.pi / 2) * j / 6
            pts.append((ccu + rc * math.cos(a1), ccv + rc * math.sin(a1)))
    pts.append(pts[0])
    return pts


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "manzanas": int(p["manzanas"]), "personas": int(p["personas"]), "volcan_fondo": bool(p["volcan_fondo"]),
         "semilla": int(p["semilla"])}
    r["usa"] = ["persona"] if r["personas"] else []
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    r["_caminos"] = {p["id"] + ".ronda": cadena([mundo(u, v) for u, v in ronda()])}
    lug = dict(LUGARES)
    if r["volcan_fondo"]:
        lug["volcan"] = ("Volcán", (VU, 0.0), 0.8)
    r["_lugares"] = {}
    for i, (nombre, (u, v), peso) in lug.items():
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": nombre, "x": round(x, 2), "y": round(y, 2), "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes: la ciudad (≈ 255 m de la plaza) y, si va, el volcán."""
    k = pz.get("tamano", 1)
    if pz.get("volcan_fondo", True):
        return (VU + VR + 255.0) / 2 * k, VR * k, math.radians(pz.get("rumbo", 0))
    return 255.0 * k, 255.0 * k, math.radians(pz.get("rumbo", 0))
