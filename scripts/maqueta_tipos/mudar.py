"""Evento «mudar»: los dos extremos del salto (`desde`, `hacia`) en unidades de la escena y, si son ids, sus nombres (así,
con `pieza`, aviva la luz de `hacia` y deja tenue la de `desde`)."""
import math


def resolver(e, X, que):
    a = X.lugar(e["desde"], que + " → desde")
    b = X.lugar(e["hacia"], que + " → hacia")
    if math.hypot(b["x"] - a["x"], b["y"] - a["y"]) < 1e-6:
        raise X.m3.Falla("M3D2", "%s: `desde` y `hacia` son el mismo lugar: mudar necesita dos" % que)
    r = {"x0": a["x"], "y0": a["y"], "x1": b["x"], "y1": b["y"],
         "desde_id": e["desde"] if isinstance(e["desde"], str) else "",
         "hacia_id": e["hacia"] if isinstance(e["hacia"], str) else "",
         "altura_km": float(e.get("altura_km", 12)), "queda": e.get("queda", True) is not False}
    if e.get("pieza"):
        r["pieza"] = e["pieza"]
        pz = X.por_id.get(e["pieza"])
        ids = {q[3] for q in (pz or {}).get("puntos", [])}
        for k in ("desde_id", "hacia_id"):
            if r[k] and ids and r[k] not in ids:
                X.avisos.append("%s: «%s» no es una luz de la pieza «%s»: el arco cae igual, pero esa luz no cambia" % (que, r[k], e["pieza"]))
    return r


def puntos(e, u, G):
    """Los dos extremos: el salto se lee si se ven de dónde sale y dónde cae."""
    return [(e["x0"], e["y0"]), (e["x1"], e["y1"])]


def origen(e, G):
    return e["x0"], e["y0"]
