"""Pieza «lagos»: los lagos y las lagunas grandes de un set de país (design/sets3d/<set>/lagos.json: OpenStreetMap), en km.
Resuelta: {anillos: [[x0, y0, x1, y1, …], …] (el contorno exterior de cada uno, del más grande al más chico), orilla, lagos: [ids]}."""
import os
import re
import unicodedata

_CAPA = {}


def _slug(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z0-9]+", "-", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip("-")


def _capa(X, que):
    ruta = os.path.join(getattr(X.S, "dir", ""), "lagos.json")
    if not os.path.isfile(ruta):
        raise X.m3.Falla("M3D2", "%s: el set «%s» no trae la capa de lagos (python3 scripts/build_set3d.py %s --capa lagos)" % (que, X.S.id, X.S.id))
    k = (ruta, os.path.getmtime(ruta))
    if k not in _CAPA:
        _CAPA.clear()
        _CAPA[k] = X.m3.cargar_json(ruta)["lagos"]
    return _CAPA[k]


def resolver(p, X, que):
    todos = _capa(X, que)
    lagos = todos
    if p.get("nombres"):          # por id («atitlan») o por nombre («Lago de Atitlán»)
        quiere = set()
        for n in p["nombres"]:
            s = _slug(n)
            hit = [l["id"] for l in todos if s in (l["id"], _slug(l["nombre"]))]
            if not hit:
                raise X.m3.Falla("M3D2", "%s: el set «%s» no tiene el lago «%s» (hay: %s)" % (que, X.S.id, n, ", ".join(l["id"] for l in todos)))
            quiere.update(hit)
        lagos = [l for l in todos if l["id"] in quiere]
    anillos = [[round(v, 2) for q in an for v in X.S.xy(q[0], q[1])] for l in lagos for an in l["anillos"]]
    if not anillos:
        raise X.m3.Falla("M3D2", "%s: ningún lago que dibujar" % que)
    return {"anillos": anillos, "orilla": p["orilla"], "lagos": [l["id"] for l in lagos]}


def centro(pz, G):
    an = pz["anillos"][0]         # el más grande (o el primero pedido): el centro de su contorno
    n = len(an) // 2
    return sum(an[0::2]) / n, sum(an[1::2]) / n
