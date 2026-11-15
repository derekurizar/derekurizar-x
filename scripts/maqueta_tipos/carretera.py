"""Pieza «carretera»: una vía de N carriles con su línea central y sus rayas, en metros. En un esquema, la de su receta
(`camino`: «eje», el de la receta carretera) o cualquier camino con nombre de la receta; en una ciudad, una arteria con
nombre del set (calles.json → arterias: «roosevelt», «bolivar»…).

Publica sus CAMINOS (ctx.caminos, para que otras piezas los sigan): «<id>» (el eje) y «<id>.carril-k», k = 1…N: los
carriles 1…N/2 van en el sentido del eje, a su derecha; los demás en sentido contrario, y sus puntos ya van en el sentido
de la marcha. Resuelta: {eje: [[x, y], …], carriles, ancho_carril, mediana}."""
import math

from maqueta_tipos import _mundo as MU
from maqueta_tipos.esquema import cadena, desplazar


def resolver(p, X, que):
    S, nombre = X.S, p["camino"]
    rec = getattr(S, "carretera", None)
    if S.escala == "esquema":
        if nombre == "eje" and rec:
            eje = rec["eje"]
        elif nombre in S.caminos:
            eje = [[q[0], q[1]] for q in S.caminos[nombre]]
        else:
            raise X.m3.Falla("M3D2", "%s: «%s» no es un camino de la receta %s (hay: %s)" % (que, nombre, S.receta, ", ".join(sorted(S.caminos)) or "ninguno"))
        n = p.get("carriles") or (rec["carriles"] if rec and nombre == "eje" else 2)
        med = p["mediana_m"] if p.get("mediana_m") is not None else (rec["mediana"] if rec and nombre == "eje" else 0.0)
    else:
        art = MU.capa(X, "calles", que).get("arterias") or {}
        if nombre not in art:
            raise X.m3.Falla("M3D2", "%s: «%s» no es una arteria con nombre del set %s (hay: %s)" % (que, nombre, S.id, ", ".join(sorted(art)) or "ninguna"))
        eje, n = art[nombre]["puntos"], p.get("carriles") or 4
        med = p["mediana_m"] if p.get("mediana_m") is not None else 2.0
    n = int(n) + int(n) % 2
    w = p["ancho_carril_m"]
    eje = [[round(x, 1), round(y, 1)] for x, y in eje]
    caminos = {p["id"]: cadena(eje)}
    for k in range(1, n + 1):
        if k <= n // 2:
            caminos["%s.carril-%d" % (p["id"], k)] = cadena(desplazar(eje, -(med / 2 + (k - 0.5) * w)))
        else:
            caminos["%s.carril-%d" % (p["id"], k)] = cadena(desplazar(eje, med / 2 + (k - n // 2 - 0.5) * w)[::-1])
    return {"eje": eje, "carriles": n, "ancho_carril": w, "mediana": med, "largo_m": round(caminos[p["id"]][-1][2], 1), "_caminos": caminos}


def tramos(pz):
    return [[(x, y, False) for x, y in pz["eje"]]]


def centro(pz, G):
    eje = pz["eje"]
    L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(eje, eje[1:]))
    s = 0.0
    for a, b in zip(eje, eje[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if s + d >= L / 2:
            u = (L / 2 - s) / (d or 1)
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        s += d
    return eje[0][0], eje[0][1]


def elemento(pz, x, y):
    return 0
