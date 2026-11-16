"""Evento «mover»: el actor va de donde esté a un lugar (su proyección sobre el camino del actor) en `dur` segundos; lo
añade el actor a sus claves (actor.con_eventos). Resuelto: {actor, s} (s: unidades desde el inicio de su camino)."""
from maqueta_tipos import _movimiento as MV


def resolver(e, X, que):
    info = X.actores.get(e["actor"]) if hasattr(X, "actores") else None
    if not info:
        raise X.m3.Falla("M3D2", "%s: «%s» no es un actor" % (que, e["actor"]))
    if info["quieto"]:
        raise X.m3.Falla("M3D2", "%s: el actor «%s» está quieto (`lugar`): para moverlo dale un camino (`camino`, `desde` + `hacia` o `puntos`)" % (que, e["actor"]))
    s = MV.posicion_en(X, e["a"], info["cad"], que + " → a")
    return {"actor": e["actor"], "s": round(s, 3)}


def puntos(e, u, G):
    M = G["R"]["_moviles"].get(e["actor"])
    return [M.en(e["t"] + e["dur"] * u, 0)[:2]] if M else []
