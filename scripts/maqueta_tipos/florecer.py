"""Evento «florecer»: sobre un lago de una pieza `lagos` aparecen manchas verde vivo (un florecimiento de cianobacteria) que
nacen en unos focos y se extienden en vetas. Ilustrativo: `cobertura` es la fracción del lago que queda verde al terminar
(no es una medida y no se rotula).

Resuelto: {pieza, lago, anillos: [[x0, y0, …], …] (km, el contorno del lago pedido), focos: [x0, y0, …] (km, dentro del
lago), viento (rad: hacia dónde se estiran las vetas), cobertura, semilla, caja: [x0, y0, x1, y1]}."""
import math
import random

from maqueta_tipos import lagos as LG


def _dentro(x, y, an):
    n, c, j = len(an) // 2, False, len(an) // 2 - 1
    for i in range(n):
        xi, yi, xj, yj = an[2 * i], an[2 * i + 1], an[2 * j], an[2 * j + 1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            c = not c
        j = i
    return c


def _dist(x, y, an):
    n, best = len(an) // 2, float("inf")
    for i in range(n):
        ax, ay, bx, by = an[2 * i], an[2 * i + 1], an[2 * ((i + 1) % n)], an[2 * ((i + 1) % n) + 1]
        dx, dy = bx - ax, by - ay
        u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / ((dx * dx + dy * dy) or 1e-12)))
        best = min(best, math.hypot(x - ax - u * dx, y - ay - u * dy))
    return best


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no está en mundo.piezas (florecer pinta un lago de esa pieza lagos)" % (que, pid))
    if pz.get("tipo") not in (None, "lagos"):
        raise X.m3.Falla("M3D2", "%s: «%s» es %s; florecer necesita una pieza lagos" % (que, pid, pz.get("tipo")))
    capa = LG._capa(X, que)
    s = LG._slug(e["lago"])
    hit = [l for l in capa if s in (l["id"], LG._slug(l["nombre"]))]
    if not hit:
        raise X.m3.Falla("M3D2", "%s: el set no tiene el lago «%s» (hay: %s)" % (que, e["lago"], ", ".join(l["id"] for l in capa)))
    lago = hit[0]
    if pz.get("lagos") and lago["id"] not in pz["lagos"]:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no dibuja el lago «%s» (dibuja: %s): añádelo a sus `nombres`" % (que, pid, lago["id"], ", ".join(pz["lagos"])))
    anillos = [[round(v, 3) for q in an for v in X.S.xy(q[0], q[1])] for an in lago["anillos"]]
    xs = [v for an in anillos for v in an[0::2]]
    ys = [v for an in anillos for v in an[1::2]]
    caja = [min(xs), min(ys), max(xs), max(ys)]
    lado = max(caja[2] - caja[0], caja[3] - caja[1])
    sem = int(e.get("semilla", 1) or 1)
    cob = max(0.0, min(1.0, float(e.get("cobertura", 0.6))))
    rnd = random.Random("florecer|%s|%d" % (lago["id"], sem))
    # los focos: 3–5 puntos dentro del agua, lejos de la orilla y separados entre sí
    nf = 3 + int(round(2 * cob))
    focos = []
    for _ in range(nf):
        mejor = None
        for intento in range(220):
            x = caja[0] + (caja[2] - caja[0]) * rnd.random()
            y = caja[1] + (caja[3] - caja[1]) * rnd.random()
            if not any(_dentro(x, y, an) for an in anillos):
                continue
            borde = min(_dist(x, y, an) for an in anillos)
            sep = min([math.hypot(x - fx, y - fy) for fx, fy in focos] or [lado])
            v = min(borde, 0.08 * lado) + 0.6 * min(sep, 0.4 * lado) + 0.02 * lado * rnd.random()
            if mejor is None or v > mejor[0]:
                mejor = (v, x, y)
        if mejor:
            focos.append((mejor[1], mejor[2]))
    if not focos:
        raise X.m3.Falla("M3D2", "%s: el lago «%s» es muy chico para florecer" % (que, lago["id"]))
    return {"pieza": pid, "lago": lago["id"], "anillos": anillos, "focos": [round(v, 3) for f in focos for v in f],
            "viento": round(2 * math.pi * rnd.random(), 4), "cobertura": cob, "semilla": sem,
            "caja": [round(v, 3) for v in caja]}


def puntos(e, u, G):
    """Dónde pasa: los focos al empezar; luego también el centro de la caja del lago (M3D6)."""
    f = e["focos"]
    pts = [(f[i], f[i + 1]) for i in range(0, len(f), 2)]
    if u > 0.4:
        c = e["caja"]
        pts.append(((c[0] + c[2]) / 2, (c[1] + c[3]) / 2))
    return pts


def origen(e, G):
    """La portada: el primer foco."""
    return (e["focos"][0], e["focos"][1])
