"""Ayudas comunes de las piezas de mundo (calles, edificios, agua, zona, carretera): leen sus capas del mundo, sea un
set de ciudad (design/sets3d/<set>/<capa>.json) o la receta de un esquema (los dos con el mismo formato, en metros)."""
import math


def capa(X, nombre, que):
    if not hasattr(X.S, "capa"):
        raise X.m3.Falla("M3D2", "%s: un mundo de escala %s no tiene la capa «%s» (sirve en ciudad y esquema)" % (que, X.S.escala, nombre))
    return X.S.capa(nombre)


def plano(pts):
    """[[x, y], …] → [x0, y0, x1, y1, …] redondeado a decímetros (lo que viaja a motor.js)."""
    return [round(v, 1) for q in pts for v in q]


def pares(flat, desde=0):
    return [(flat[i], flat[i + 1]) for i in range(desde, len(flat) - 1, 2)]


def centroide(pts):
    n = len(pts)
    return sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n


def dentro_pol(x, y, pts):
    c = False
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / ((by - ay) or 1e-9) + ax:
            c = not c
    return c


def dist_linea(x, y, pts):
    m = 1e18
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        h = min(1, max(0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1e-9)))
        m = min(m, math.hypot(x - ax - dx * h, y - ay - dy * h))
    return m


def caja_de(R):
    x0, y0, x1, y1 = R["mundo"]["caja"]
    return (x0 + x1) / 2, (y0 + y1) / 2
