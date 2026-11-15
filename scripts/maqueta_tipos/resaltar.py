"""Evento «resaltar»: una pieza (por su id) o un lugar (sus km y, si es un id, el nombre: así aviva su luz)."""


def resolver(e, X, que):
    if e.get("pieza"):
        return {"pieza": e["pieza"]}
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
