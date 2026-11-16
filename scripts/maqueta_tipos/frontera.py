"""Pieza «frontera»: los anillos del contorno del país (los del set), en km."""


def resolver(p, X, que):
    r = {"anillos": [[[round(v, 3) for v in X.S.xy(q[0], q[1])] for q in an] for an in X.S.frontera]}
    if p.get("vecinos"):   # los bordes de los países de alrededor, tenues: para leer dónde queda cada cosa
        if not getattr(X.S, "vecinos", None):
            raise X.m3.Falla("M3D2", "%s: el set «%s» no trae vecinos (rehaz la capa: build_set3d.py %s --capa frontera)" % (que, X.S.id, X.S.id))
        r["vecinos"] = [[[round(v, 3) for v in X.S.xy(q[0], q[1])] for q in ln] for ln in X.S.vecinos]
    return r


def tramos(pz):
    return [[(q[0], q[1], False) for q in an + an[:1]] for an in pz["anillos"]]
