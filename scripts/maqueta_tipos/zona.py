"""Pieza «zona»: un polígono teñido sobre el suelo (un barrio, un parque, la plaza, el área de lo que pasó): una zona del
mundo por su id (`area`; «parques» = todas las zonas verdes) o los `puntos` dados ([lon, lat] en ciudad, [x, y] en
metros en esquema). Resuelta: {poligonos: [[x0, y0, …]], tono, opacidad, borde}."""
from maqueta_tipos import _mundo as MU


def resolver(p, X, que):
    if (p.get("area") is None) == (p.get("puntos") is None):
        raise X.m3.Falla("M3D2", "%s: una zona lleva `area` (el id de una zona del mundo, o «parques») o `puntos`, una de las dos" % que)
    if p.get("puntos") is not None:
        if len(p["puntos"]) < 3:
            raise X.m3.Falla("M3D2", "%s: `puntos` necesita al menos 3" % que)
        pols = [[v for ref in p["puntos"] for v in (lambda l: (l["x"], l["y"]))(X.lugar(ref, que))]]
    else:
        Z = MU.capa(X, "zonas", que)["zonas"]
        if p["area"] == "parques":
            pols = [MU.plano(z["puntos"]) for z in Z if z.get("clase") in ("park", "garden", "village_green", "recreation_ground", "grass")]
        else:
            pols = [MU.plano(z["puntos"]) for z in Z if z["id"] == p["area"]]
            if not pols:
                ids = [z["id"] for z in Z if z.get("nombre")] or [z["id"] for z in Z]
                raise X.m3.Falla("M3D2", "%s: «%s» no es una zona del mundo (hay: parques, %s%s)" % (que, p["area"], ", ".join(ids[:12]), "…" if len(ids) > 12 else ""))
        if not pols:
            raise X.m3.Falla("M3D2", "%s: el mundo no tiene zonas verdes" % que)
    return {"poligonos": [[round(v, 1) for v in q] for q in pols], "tono": p["tono"], "opacidad": p["opacidad"], "borde": p["borde"]}


def tramos(pz):
    out = []
    for q in pz["poligonos"]:
        pts = MU.pares(q)
        out.append([(x, y, False) for x, y in pts + pts[:1]])
    return out


def centro(pz, G):
    return MU.centroide(MU.pares(pz["poligonos"][0]))
