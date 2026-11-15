"""Lo común de `frenar` y `acelerar` (eventos de un flujo): el punto `en` sobre el primer carril que el evento toca, su
largo y su velocidad. El efecto (la cola) lo calcula el flujo en con_eventos (scripts/maqueta_tipos/flujo.py)."""
from maqueta_tipos import _movimiento as MV
from maqueta_tipos import flujo as FL


def resolver(e, X, que):
    pz = X.por_id[e["flujo"]]
    cads = X.flujos[pz["id"]]["cads"]
    carriles = FL.carriles_de(pz, e, que, X)
    r = {"flujo": e["flujo"], "vel_kmh": float(e["vel_kmh"]), "_carriles": carriles, "carriles": [pz["carriles"][c] for c in carriles],
         "largo": float(e.get("longitud_m", 60)) / X.S.unidad_m}
    if e.get("en") is not None:
        cad = cads[carriles[0]]
        s = MV.posicion_en(X, e["en"], cad, que + " → en")
        x, y, _, _ = MV.en_cadena(cad, s)
        r.update(x=round(x, 3), y=round(y, 3))
    return r


def puntos(e, u, G):
    if e.get("x") is not None:
        return [(e["x"], e["y"])]
    pz = G["por_id"][e["flujo"]]
    c = G["m3"].reglas("flujo").centro(pz, G)
    return [c] if c else []
