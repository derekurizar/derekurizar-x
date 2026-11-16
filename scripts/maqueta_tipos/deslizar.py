"""Evento «deslizar»: dónde se centran las flechas sobre la traza (s0) y su sentido (+1 izquierdo, −1 derecho)."""


def resolver(e, X, que):
    M3 = X.m3
    f = X.por_id[e["pieza"]]
    cad = f["cadena"]
    if e.get("en") is not None:
        l = X.lugar(e["en"], que)
        s0 = M3.mas_cercano(cad, l["x"], l["y"])[0]
    else:
        s0 = f["largo_km"] / 2
    r = {"pieza": f["id"], "s0": round(s0, 3), "km": float(e.get("km", 60)), "periodo_km": float(e.get("periodo_km", 7)),
         "vel": float(e.get("vel_km_s", 6)), "sentido": 1 if e.get("sentido", "izquierdo") == "izquierdo" else -1}
    r["x"], r["y"] = M3.punto_en_s(cad, s0)
    return r


def puntos(e, u, G):
    return [(e["x"], e["y"])]


def origen(e, G):
    return e["x"], e["y"]
