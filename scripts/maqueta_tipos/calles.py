"""Pieza «calles»: las calles del mundo por clase (de un set de ciudad o de la receta de un esquema), en metros.
Resuelta: {clases: [...], anchos: [m por clase], calles: [[i_clase, x0, y0, x1, y1, …]], nombres: [...]}."""
from maqueta_tipos import _mundo as MU

CLASES = ("autopista", "primaria", "secundaria", "terciaria", "residencial", "peatonal")
ANCHOS = {"autopista": 20.0, "primaria": 14.0, "secundaria": 11.0, "terciaria": 9.0, "residencial": 7.0, "peatonal": 4.0}


def resolver(p, X, que):
    malas = [c for c in p["clases"] if c not in CLASES]
    if malas:
        raise X.m3.Falla("M3D2", "%s: `clases` lleva %s, y van: %s" % (que, ", ".join("«%s»" % c for c in malas), ", ".join(CLASES)))
    usa = [c for c in CLASES if c in p["clases"]]
    calles = [q for q in MU.capa(X, "calles", que)["calles"] if q["clase"] in usa]
    if not calles:
        raise X.m3.Falla("M3D2", "%s: el mundo no tiene calles de las clases %s" % (que, ", ".join(usa)))
    return {"clases": usa, "anchos": [round(ANCHOS[c] * p["grosor"], 2) for c in usa],
            "calles": [[usa.index(q["clase"])] + MU.plano(q["puntos"]) for q in calles], "nombres": [q.get("nombre", "") for q in calles]}


def elemento(pz, x, y):
    """La calle más cercana a (x, y): su índice en pz["calles"] (la resalta `resaltar` con `elemento`)."""
    return min(range(len(pz["calles"])), key=lambda i: MU.dist_linea(x, y, MU.pares(pz["calles"][i], 1)))


def centro(pz, G):
    return MU.caja_de(G["R"])
