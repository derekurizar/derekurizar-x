"""Pieza «garitasur»: la entrada de una ciudad de fines del siglo XIX por una garita (genérica, en metros reales), centrada en
`lugar` (la puerta) y orientada por `rumbo` (u: hacia dónde entra el camino a la ciudad; v: a su izquierda). El camino real
llega de u −300 (afuera) a u +140 (adentro); a 110 m de la puerta, afuera, se le juntan dos ramales (tres caminos que
convergen). La tranca cruza el camino 8 m antes de la puerta. El cantón (manzanas trazadas sobre el potrero) queda adentro a
la izquierda (u 18…128, v 24…134) y el potrero abierto a la derecha. Con `tren`, un ramal de vía con su estación a la
derecha, adentro.
Publica sus CAMINOS: «camino-real» y «<id>.camino-real» (de afuera hacia la ciudad, por la puerta), «<id>.ramal-izq» y
«<id>.ramal-der» (los dos ramales, de afuera hasta el cruce). Sus LUGARES: garita (la puerta), tranca, cruce (donde
convergen los tres caminos), canton (el centro de las manzanas), potrero (el pastizal abierto) y, con tren, estacion.
Resuelta: {x, y, rumbo, tamano, carretas, mulas, arrieros, guardas, canton, tranca_s, tren, semilla, vecinos, usa}."""
import math

from maqueta_tipos.esquema import cadena

# (u, v) en metros de los lugares que publica
LUGARES = {"garita": ("Garita", 0.0, 0.0, 0.9), "tranca": ("Tranca", -8.0, 0.0, 0.6), "cruce": ("Cruce de caminos", -110.0, 0.0, 0.5),
           "canton": ("Cantón", 73.0, 79.0, 0.7), "potrero": ("Potrero", 84.0, -105.0, 0.5)}
ESTACION = ("Estación", 52.0, -95.0, 0.5)


def _geom(p, l, um):
    r = math.radians(float(p["rumbo"]))
    ux, uy, K = math.cos(r), math.sin(r), float(p["tamano"]) / um

    def W(u, v):
        return [round(l["x"] + (u * ux - v * uy) * K, 3), round(l["y"] + (u * uy + v * ux) * K, 3)]
    return W


def resolver(p, X, que):
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "carretas": int(p["carretas"]), "mulas": int(p["mulas"]), "arrieros": int(p["arrieros"]), "guardas": int(p["guardas"]),
         "canton": float(p["canton"]), "tranca_s": float(p["tranca_s"]), "tren": bool(p.get("tren", False)),
         "semilla": int(p["semilla"]), "vecinos": int(p.get("vecinos", 0) or 0)}
    if r["carretas"] + r["mulas"] == 0 and r["arrieros"]:
        X.avisos.append("%s: hay arrieros pero ni carretas ni mulas: los arrieros esperan a pie en la fila" % que)
    if r["arrieros"] + r["guardas"] + r["vecinos"]:
        r["usa"] = ["persona"]
    W = _geom(p, l, um)
    pid = p["id"]
    real = cadena([W(u, 0.0) for u in range(-300, 141, 10)])
    izq = cadena([W(-300.0 + 190.0 * k / 12, 170.0 * (1 - k / 12) ** 1.4) for k in range(13)])
    der = cadena([W(-300.0 + 190.0 * k / 12, -170.0 * (1 - k / 12) ** 1.4) for k in range(13)])
    r["_caminos"] = {"camino-real": real, pid + ".camino-real": real, pid + ".ramal-izq": izq, pid + ".ramal-der": der}
    lug = dict(LUGARES)
    if r["tren"]:
        lug["estacion"] = ESTACION
    r["_lugares"] = {}
    for k, (nom, u, v, peso) in lug.items():
        x, y = W(u, v)
        r["_lugares"][k] = {"nombre": nom, "x": x, "y": y, "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo (a lo largo del camino, desde la puerta), medio ancho y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 220 * k, 150 * k, math.radians(pz.get("rumbo", 0))
