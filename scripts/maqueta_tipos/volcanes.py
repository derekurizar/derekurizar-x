"""Pieza «volcanes»: conos nítidos sobre el relieve del país (el modelo de elevación a ~700 m deja los volcanes romos y
bajos a 60–120 km). Cada cumbre es un cono de `radio_km` con su cráter, que sube desde el pie (el suelo más bajo de su
borde) hasta `alto_m` (o, sin él, hasta lo más alto del relieve cerca de la cumbre). Dos conos que se tocan forman un
macizo (Fuego y Acatenango): la superficie es el MÁXIMO de los conos y del suelo, la misma cuenta aquí y en volcanes.js.

Resuelta: {cumbres: [[x, y, R, top, base, fase], …] (km; top y base en unidades de la escena, ya exageradas), crater,
nombres: [id o ""]}. Publica SU RELIEVE (`_alturas`: lo que el cono sube sobre el suelo, una malla por macizo: así las
marcas, las luces y la cámara pisan el cono) y SUS LUGARES (`_lugares`: «volcan-<id>» o «volcan-<n>» en cada cumbre)."""
import math

from maqueta_tipos import _relieve as RL

CRATER = 0.06          # radio del cráter, fracción del radio del cono
HONDO = 0.05           # hondura del cráter, fracción del alto del cono sobre su pie
POT = 1.6              # el perfil: base + alto · (1 − v)^POT (cóncavo, como un estratovolcán)
BARRANCAS = 0.06      # amplitud de las barrancas radiales, fracción del alto


def forma(c, x, y, crater, liso=False):
    """La altura del cono c = [x, y, R, top, base, fase] en (x, y) (unidades de la escena), o None fuera de su radio.
    La misma cuenta que `forma` en video/maqueta/piezas/volcanes.js."""
    cx, cy, R, top, base, fase = c
    dx, dy = x - cx, y - cy
    r = math.hypot(dx, dy)
    u = r / R
    if u >= 1.0:
        return None
    alto = top - base
    uc = CRATER if crater else 0.0
    if u <= uc:
        q = u / uc
        return top - HONDO * alto * (1.0 - q * q)
    v = (u - uc) / (1.0 - uc)
    h = base + alto * (1.0 - v) ** POT
    if liso:              # forma «cono»: sin barrancas
        return h
    n = 9 + int(fase) % 4
    th = math.atan2(dy, dx)
    h -= BARRANCAS * alto * 4.0 * v * (1.0 - v) * (0.5 + 0.5 * math.sin(n * th + fase * 2.4)) ** 3
    return h


def resolver(p, X, que):
    S = X.S
    if getattr(S, "escala", "pais") != "pais":
        raise X.m3.Falla("M3D2", "%s: «volcanes» es de escala pais (km sobre el relieve del set)" % que)
    exag = float(S.exag)
    suelo = getattr(S, "suelo_base", S.suelo)
    R = float(p["radio_km"])
    altos = p.get("alto_m") or {}
    crater = bool(p.get("crater", True))
    liso = p.get("forma") == "cono"
    cumbres, nombres, lugares = [], [], {}
    for i, ref in enumerate(p["lugares"]):
        l = X.lugar(ref, "%s → lugares[%d]" % (que, i))
        x, y = l["x"], l["y"]
        clave = ref if isinstance(ref, str) else str(i)
        if clave in altos or str(i) in altos:
            top_m = float(altos.get(clave, altos.get(str(i))))
        else:                     # sin alto: lo más alto del relieve a menos de 0.35 R de la cumbre
            top_m, paso = 0.0, 0.25
            k = int(0.35 * R / paso) + 1
            for a in range(-k, k + 1):
                for b in range(-k, k + 1):
                    if math.hypot(a, b) * paso <= 0.35 * R:
                        top_m = max(top_m, S.metros(x + a * paso, y + b * paso))
        top = top_m / 1000.0 * exag
        base = min(suelo(x + R * math.cos(2 * math.pi * j / 32), y + R * math.sin(2 * math.pi * j / 32)) for j in range(32))
        base = min(base, top - 0.3 * exag)            # al menos 300 m de cono
        cumbres.append([round(x, 3), round(y, 3), round(R, 3), round(top, 4), round(max(0.0, base), 4), i])
        nombres.append(ref if isinstance(ref, str) else "")
        lid = "volcan-%s" % (ref if isinstance(ref, str) else i + 1)
        lugares[lid] = {"nombre": l.get("nombre") or "Volcán", "x": x, "y": y, "peso": 0.5}
    # SU RELIEVE: lo que el macizo sube sobre el suelo del mundo, una malla por grupo de conos que se tocan
    alturas = []
    for grupo in macizos(cumbres):
        cs = [cumbres[i] for i in grupo]
        x0, y0 = min(c[0] - c[2] for c in cs), min(c[1] - c[2] for c in cs)
        x1, y1 = max(c[0] + c[2] for c in cs), max(c[1] + c[2] for c in cs)
        paso = max(0.2, R / 30.0)
        nx, ny = int(math.ceil((x1 - x0) / paso)) + 1, int(math.ceil((y1 - y0) / paso)) + 1

        def sube(x, y, cs=cs):
            h = max([v for v in (forma(c, x, y, crater, liso) for c in cs) if v is not None] or [-1e9])
            return max(0.0, h - suelo(x, y))
        alturas.append(RL.malla([x0, y0, x1, y1], nx, ny, sube))
    return {"cumbres": cumbres, "crater": crater, "nombres": nombres, "_alturas": alturas, "_lugares": lugares}


def macizos(cumbres):
    """Los grupos de conos que se tocan (índices)."""
    n, padre = len(cumbres), list(range(len(cumbres)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            a, b = cumbres[i], cumbres[j]
            if math.hypot(a[0] - b[0], a[1] - b[1]) < a[2] + b[2]:
                padre[raiz(i)] = raiz(j)
    grupos = {}
    for i in range(n):
        grupos.setdefault(raiz(i), []).append(i)
    return list(grupos.values())


def elemento(pz, x, y):
    """La cumbre más cercana a (x, y): su índice (la resalta `resaltar` con `pieza` + `elemento`)."""
    return min(range(len(pz["cumbres"])), key=lambda i: math.hypot(pz["cumbres"][i][0] - x, pz["cumbres"][i][1] - y))


def centro(pz, G):
    cs = pz["cumbres"]
    return sum(c[0] for c in cs) / len(cs), sum(c[1] for c in cs) / len(cs)
