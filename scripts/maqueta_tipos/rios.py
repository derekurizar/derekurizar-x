"""Pieza «rios»: los ríos principales de un set de país (design/sets3d/<set>/rios.json: OpenStreetMap), en km.
Resuelta: {lineas: [[orden, x0, y0, x1, y1, …], …] (orden 1 = los grandes), grosor, rios: [ids]}."""
import os
import re
import unicodedata

_CAPA = {}


def _slug(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip("-")


def _capa(X, que):
    ruta = os.path.join(getattr(X.S, "dir", ""), "rios.json")
    if not os.path.isfile(ruta):
        raise X.m3.Falla("M3D2", "%s: el set «%s» no trae la capa de ríos (python3 scripts/build_set3d.py %s --capa rios)" % (que, X.S.id, X.S.id))
    k = (ruta, os.path.getmtime(ruta))
    if k not in _CAPA:
        _CAPA.clear()
        _CAPA[k] = X.m3.cargar_json(ruta)["rios"]
    return _CAPA[k]


def _elegir(todos, nombres, X, que):
    """`nombres` → los ríos pedidos (por id, «motagua», o por nombre, «Río Motagua»), en el orden del set (por largo)."""
    if not nombres:
        return list(todos)
    quiere = set()
    for n in nombres:
        s = _slug(n)
        hit = [r["id"] for r in todos if s in (r["id"], _slug(r["nombre"]))] or [r["id"] for r in todos if _slug(r["nombre"]).endswith("-" + s)]
        if not hit:
            raise X.m3.Falla("M3D2", "%s: el set «%s» no tiene el río «%s» (los más largos: %s; todos en design/sets3d/%s/rios.json)"
                             % (que, X.S.id, n, ", ".join(r["id"] for r in todos[:14]), X.S.id))
        quiere.update(hit)
    return [r for r in todos if r["id"] in quiere]


def resolver(p, X, que):
    rios = [r for r in _elegir(_capa(X, que), p.get("nombres"), X, que) if p.get("nombres") or r["orden"] <= p["hasta_orden"]]
    lineas = []
    for r in rios:
        for ln in r["lineas"]:
            lineas.append([r["orden"]] + [round(v, 2) for q in ln for v in X.S.xy(q[0], q[1])])
    if not lineas:
        raise X.m3.Falla("M3D2", "%s: ningún río que dibujar" % que)
    return {"lineas": lineas, "grosor": p["grosor"], "rios": [r["id"] for r in rios]}


def tramos(pz):
    return [[(ln[i], ln[i + 1], False) for i in range(1, len(ln) - 1, 2)] for ln in pz["lineas"]]


def centro(pz, G):
    ln = pz["lineas"][0]          # el más largo (o el primero pedido): su punto medio
    i = 1 + 2 * ((len(ln) - 1) // 4)
    return ln[i], ln[i + 1]
