"""Evento «resaltar»: una pieza (por su id; con `elemento`, el edificio o la calle de ella en ese lugar) o un lugar
(sus coordenadas y, si es un id, el nombre: así aviva su luz)."""


def resolver(e, X, que):
    if e.get("pieza"):
        if e.get("elemento") is None:
            return {"pieza": e["pieza"]}
        # un edificio o una calle de la pieza: el que está en ese lugar (las reglas de su tipo saben buscarlo)
        pz = X.por_id.get(e["pieza"]) or next((p for p in X.piezas if p["id"] == e["pieza"]), None)
        rg = X.m3.reglas(pz["tipo"]) if pz else None
        if not rg or not hasattr(rg, "elemento"):
            raise X.m3.Falla("M3D2", "%s: `elemento` solo vale con una pieza de edificios, calles o carretera (la de «%s» no tiene elementos)" % (que, e["pieza"]))
        l = X.lugar(e["elemento"], que + " → elemento")
        return {"pieza": e["pieza"], "elemento": [l["x"], l["y"]], "indice": rg.elemento(pz, l["x"], l["y"]), "x": l["x"], "y": l["y"]}
    if e.get("lugar") is None:
        raise X.m3.Falla("M3D2", "%s: resaltar lleva `pieza` (el id de una pieza) o `lugar` (%s)" % (que, "un lugar del set, de mundo.lugares o [lon, lat]"))
    l = X.lugar(e["lugar"], que)
    return {"lugar": e["lugar"] if isinstance(e["lugar"], str) else "", "x": l["x"], "y": l["y"]}


def _donde(e, G):
    if "x" in e:
        return (e["x"], e["y"])
    pz = G["por_id"][e["pieza"]]
    c = G["m3"].reglas(pz["tipo"])
    return c.centro(pz, G) if c and hasattr(c, "centro") else None


def puntos(e, u, G):
    p = _donde(e, G)
    return [p] if p else []


def origen(e, G):
    return _donde(e, G)
