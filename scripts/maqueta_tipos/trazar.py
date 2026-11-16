"""Evento «trazar»: el trazo se DIBUJA de su inicio hasta `hasta` (por defecto, el final) en `dur` segundos; un trazo con
algún trazar no se ve antes del primero. Resuelto: {trazo, de, a} (unidades desde el inicio del trazo)."""
from maqueta_tipos import trazo as TZ


def resolver(e, X, que):
    T = X.trazos[e["trazo"]]
    a = TZ.local(X, e["trazo"], e["hasta"], que + " → hasta") if e.get("hasta") is not None else T["largo"]
    de = TZ.local(X, e["trazo"], e["desde"], que + " → desde") if e.get("desde") is not None else 0.0
    return {"trazo": e["trazo"], "de": round(de, 2), "a": round(a, 2)}


def _frente(e, u, G):
    pz = G["por_id"][e["trazo"]]
    return TZ.punto_local(pz, e["de"] + (e["a"] - e["de"]) * u)


def puntos(e, u, G):
    return [_frente(e, u, G)]


def origen(e, G):
    return _frente(e, 0.0, G)
