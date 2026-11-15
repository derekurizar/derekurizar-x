"""Pieza «frontera»: los anillos del contorno del país (los del set), en km."""


def resolver(p, X, que):
    return {"anillos": [[[round(v, 3) for v in X.S.xy(q[0], q[1])] for q in an] for an in X.S.frontera]}


def tramos(pz):
    return [[(q[0], q[1], False) for q in an + an[:1]] for an in pz["anillos"]]
