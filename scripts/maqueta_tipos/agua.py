"""Pieza «agua»: lagos, estanques, el mar (polígonos) y ríos (líneas) del mundo, en metros.
Resuelta: {poligonos: [[x0, y0, …]], rios: [[x0, y0, …]]}."""
from maqueta_tipos import _mundo as MU


def resolver(p, X, que):
    A = MU.capa(X, "agua", que)
    r = {"poligonos": [MU.plano(q["puntos"]) for q in A["poligonos"]], "rios": [MU.plano(q["puntos"]) for q in A["rios"]] if p["rios"] else []}
    if not r["poligonos"] and not r["rios"]:
        raise X.m3.Falla("M3D2", "%s: el mundo no tiene agua (ni lagos ni ríos)" % que)
    return r


def centro(pz, G):
    pts = MU.pares(pz["poligonos"][0]) if pz["poligonos"] else MU.pares(pz["rios"][0])
    return MU.centroide(pts)
