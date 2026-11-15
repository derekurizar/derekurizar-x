"""Pieza «ruta»: los lugares por los que pasa, en km (la ficha exige al menos dos)."""


def resolver(p, X, que):
    return {"puntos": [[l["x"], l["y"]] for l in (X.lugar(ref, que) for ref in p["lugares"])]}


def tramos(pz):
    return [[(q[0], q[1], False) for q in pz["puntos"]]]
