"""Pieza «carreteras»: la red troncal de un set de país (design/sets3d/<set>/carreteras.json: OpenStreetMap), en km.
Resuelta: {lineas: [[clase, x0, y0, x1, y1, …], …] (clase 1 = troncal, 2 = primaria), grosor, rutas: [ids]}."""
import os
import re
import unicodedata

_CAPA = {}
_CLASE = {"troncal": 1, "primaria": 2}


def _slug(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip("-")


def _capa(X, que):
    ruta = os.path.join(getattr(X.S, "dir", ""), "carreteras.json")
    if not os.path.isfile(ruta):
        raise X.m3.Falla("M3D2", "%s: el set «%s» no trae la capa de carreteras (python3 scripts/build_set3d.py %s --capa carreteras)" % (que, X.S.id, X.S.id))
    k = (ruta, os.path.getmtime(ruta))
    if k not in _CAPA:
        _CAPA.clear()
        _CAPA[k] = X.m3.cargar_json(ruta)["carreteras"]
    return _CAPA[k]


def resolver(p, X, que):
    todas = _capa(X, que)
    if p.get("nombres"):          # por número de ruta («CA-9») o por id («ca-9»): todos sus tramos, sean troncales o primarios
        rutas = []
        for n in p["nombres"]:
            s = _slug(n)
            hit = [k for k in todas if s in (_slug(k["ref"]), k["id"]) and k["ref"]]
            if not hit:
                refs = sorted({k["ref"] for k in todas if k["ref"]}, key=lambda r: (not r.startswith("CA-"), len(r), r))
                raise X.m3.Falla("M3D2", "%s: el set «%s» no tiene la ruta «%s» (hay: %s…; todas en design/sets3d/%s/carreteras.json)"
                                 % (que, X.S.id, n, ", ".join(refs[:16]), X.S.id))
            rutas += [k for k in hit if k not in rutas]
    else:
        rutas = [k for k in todas if p["clase"] in ("todas", k["clase"])]
    lineas = []
    for k in rutas:
        for ln in k["lineas"]:
            lineas.append([_CLASE[k["clase"]]] + [round(v, 2) for q in ln for v in X.S.xy(q[0], q[1])])
    if not lineas:
        raise X.m3.Falla("M3D2", "%s: ninguna carretera que dibujar" % que)
    return {"lineas": lineas, "grosor": p["grosor"], "rutas": [k["id"] for k in rutas]}


def tramos(pz):
    return [[(ln[i], ln[i + 1], False) for i in range(1, len(ln) - 1, 2)] for ln in pz["lineas"]]


def centro(pz, G):
    ln = max(pz["lineas"], key=len)   # el tramo con más puntos: su punto medio
    i = 1 + 2 * ((len(ln) - 1) // 4)
    return ln[i], ln[i + 1]
