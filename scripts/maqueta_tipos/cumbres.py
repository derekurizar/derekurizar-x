"""Evento «cumbres»: sobre una pieza volcanes, los cráteres se encienden uno tras otro y quedan encendidos.

Resuelto: {pieza, cumbres: [[i, x, y, top, R], …] (en el orden en que se encienden; i = índice de la cumbre en la pieza;
x, y en km; top en unidades de la escena, ya exagerado, el mismo de volcanes.py), prota (la pieza es la protagonista:
acento; si no, crema), queda}. `lugares` elige un subconjunto: cada uno es el id con que la pieza nombró la cumbre, su
lugar publicado («volcan-<id>», «volcan-<n>») o un [lon, lat]; manda la cumbre más cercana a menos de un radio."""
import math


def resolver(e, X, que):
    pz = X.por_id.get(e["pieza"])
    if not pz or pz.get("tipo") != "volcanes" or not pz.get("cumbres"):
        raise X.m3.Falla("M3D2", "%s: `pieza` «%s» no es una pieza volcanes de esta maqueta" % (que, e["pieza"]))
    cs, nombres = pz["cumbres"], pz.get("nombres") or []
    sel = e.get("lugares", "todos")
    if sel in (None, "todos"):
        idx = list(range(len(cs)))
    else:
        idx = []
        for n, ref in enumerate(sel):
            i = None
            if isinstance(ref, str):
                for k, nm in enumerate(nombres):
                    if nm and (ref == nm or ref == "volcan-%s" % nm):
                        i = k
                m = ref[len("volcan-"):] if ref.startswith("volcan-") else None
                if i is None and m and m.isdigit() and 1 <= int(m) <= len(cs):
                    i = int(m) - 1
            if i is None:
                l = X.lugar(ref, "%s → lugares[%d]" % (que, n))
                d, k = min((math.hypot(c[0] - l["x"], c[1] - l["y"]), k) for k, c in enumerate(cs))
                if d > cs[k][2]:
                    raise X.m3.Falla("M3D2", "%s: lugares[%d] queda a %.1f km de la cumbre más cercana de «%s»: no es uno de sus volcanes"
                                     % (que, n, d, e["pieza"]))
                i = k
            if i not in idx:
                idx.append(i)
    orden = e.get("orden", "lista")
    if orden == "oeste-este":
        idx.sort(key=lambda i: cs[i][0])
    elif orden == "este-oeste":
        idx.sort(key=lambda i: -cs[i][0])
    return {"pieza": e["pieza"], "cumbres": [[i, cs[i][0], cs[i][1], cs[i][3], cs[i][2]] for i in idx],
            "prota": bool(pz.get("protagonista")), "queda": e.get("queda", True) is not False}


def puntos(e, u, G):
    """Las cumbres que el evento enciende: la fila se lee si se ven (M3D6)."""
    return [(c[1], c[2]) for c in e["cumbres"]]


def origen(e, G):
    """La portada: la primera cumbre que se enciende."""
    c = e["cumbres"][0]
    return c[1], c[2]
