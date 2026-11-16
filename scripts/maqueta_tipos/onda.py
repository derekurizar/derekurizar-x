"""Evento «onda»: el centro del anillo (un lugar, o la mitad de la falla de la que sale)."""


def resolver(e, X, que):
    r = {"radio_km": float(e.get("radio_km", 0))}
    if e.get("pieza"):
        f = X.por_id[e["pieza"]]
        r["pieza"] = f["id"]
        r["x"], r["y"] = X.m3.punto_en_s(f["cadena"], f["largo_km"] / 2)
    elif e.get("centro") is not None:
        l = X.lugar(e["centro"], que)
        r["x"], r["y"] = l["x"], l["y"]
    else:
        raise X.m3.Falla("M3D2", "%s: una onda sale de `centro` (un lugar) o de `pieza` (una falla)" % que)
    return r


def puntos(e, u, G):
    return [(e["x"], e["y"])]


def origen(e, G):
    return e["x"], e["y"]
