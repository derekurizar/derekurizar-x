"""Evento «pintar»: un tramo del trazo cambia de color (`color`: bien · medio · mal · texto, o acento si el trazo es el
protagonista). El color avanza como un frente de `desde` a `hasta` en `dur` segundos (de `hasta` a `desde` si va al revés:
una cola que crece hacia atrás) y se queda. Resuelto: {trazo, de, a, color} (unidades desde el inicio del trazo)."""
from maqueta_tipos import trazo as TZ


def resolver(e, X, que):
    pz = X.por_id[e["trazo"]]
    if e["color"] == "acento" and pz["id"] != getattr(X, "protagonista", None):
        raise X.m3.Falla("M3D2", "%s: el acento es solo del `protagonista` (el trazo «%s» no lo es): usa bien, medio, mal o texto" % (que, e["trazo"]))
    de = TZ.local(X, e["trazo"], e["desde"], que + " → desde")
    a = TZ.local(X, e["trazo"], e["hasta"], que + " → hasta")
    return {"trazo": e["trazo"], "de": round(de, 2), "a": round(a, 2), "color": e["color"]}


def puntos(e, u, G):
    pz = G["por_id"][e["trazo"]]
    return [TZ.punto_local(pz, e["de"] + (e["a"] - e["de"]) * u)]
