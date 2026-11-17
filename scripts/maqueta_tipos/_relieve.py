"""El RELIEVE DE PIEZA: lo que una pieza le suma al suelo del mundo (un camino que sube, una ladera sembrada, una
plataforma), para que TODO lo demás lo pise: un actor o un flujo que siga sus caminos, la gente que otra pieza ponga
encima, la cámara que mira o sigue, las marcas, las anotaciones y los gates. El resolver de la pieza lo publica en
`_alturas` (una lista de campos, como `_caminos`); maqueta3d.resolver los junta en el mundo (S.alturas → MAQUETA.mundo.alturas)
y desde ahí S.suelo(x, y) en Python y ctx.altura(x, y) en motor.js devuelven el suelo del mundo MÁS el relieve. El suelo
sin relieve queda en S.suelo_base y ctx.suelo (lo usa la pieza dueña del relieve para no contarse dos veces).

Un campo, en UNIDADES DE LA ESCENA (esquema y ciudad: metros), con su `caja` [x0, y0, x1, y1]:
  perfil(puntos, ancho)             {"tipo": "perfil", "puntos": [[x, y, z], …], "ancho": w}: la altura z a lo largo de una
                                    polilínea, hasta `ancho` a cada lado (un camino, una rampa)
  plano(poligono, z)                {"tipo": "plano", "poligono": [x0, y0, …], "z": h}: una plataforma a una altura
  malla(caja, nx, ny, z, poligono)  {"tipo": "malla", "caja", "nx", "ny", "z": [fila por fila, de y0 a y1], "poligono"?}:
                                    una cuadrícula bilineal (cualquier otra forma: una ladera con terrazas)
Donde varios campos cubren un punto manda el más alto; donde ninguno, el relieve es 0. El mismo cálculo que `relieve` de
video/maqueta/motor.js (los dos leen los mismos números, redondeados a centímetros)."""
import math


def _caja(xs, ys, margen=0.0):
    return [round(min(xs) - margen, 2), round(min(ys) - margen, 2), round(max(xs) + margen, 2), round(max(ys) + margen, 2)]


def perfil(puntos, ancho):
    """puntos: [[x, y, z], …] (≥ 2); ancho: hasta dónde vale a cada lado de la línea."""
    pts = [[round(float(q[0]), 2), round(float(q[1]), 2), round(float(q[2]), 2)] for q in puntos]
    return {"tipo": "perfil", "puntos": pts, "ancho": round(float(ancho), 2),
            "caja": _caja([q[0] for q in pts], [q[1] for q in pts], float(ancho))}


def plano(poligono, z):
    """poligono: [x0, y0, x1, y1, …] o [[x, y], …]."""
    pol = [round(float(v), 2) for q in poligono for v in (q if isinstance(q, (list, tuple)) else [q])]
    return {"tipo": "plano", "poligono": pol, "z": round(float(z), 2), "caja": _caja(pol[0::2], pol[1::2])}


def malla(caja, nx, ny, f, poligono=None):
    """f(x, y) → altura, muestreada en nx × ny puntos de la caja [x0, y0, x1, y1] (los bordes incluidos); `poligono`
    ([x0, y0, …]): fuera de él el campo no vale."""
    x0, y0, x1, y1 = [float(v) for v in caja]
    nx, ny = max(2, int(nx)), max(2, int(ny))
    z = [round(float(f(x0 + (x1 - x0) * i / (nx - 1), y0 + (y1 - y0) * j / (ny - 1))), 2) for j in range(ny) for i in range(nx)]
    c = {"tipo": "malla", "caja": [round(v, 2) for v in (x0, y0, x1, y1)], "nx": nx, "ny": ny, "z": z}
    if poligono:
        c["poligono"] = [round(float(v), 2) for v in poligono]
    return c


def _dentro(pol, x, y):
    c, n = False, len(pol) // 2
    for i in range(n):
        ax, ay, bx, by = pol[2 * i], pol[2 * i + 1], pol[2 * ((i + 1) % n)], pol[2 * ((i + 1) % n) + 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / ((by - ay) or 1e-9) + ax:
            c = not c
    return c


def campo_en(c, x, y):
    """La altura del campo en (x, y), o None si no lo cubre."""
    x0, y0, x1, y1 = c["caja"]
    if x < x0 or x > x1 or y < y0 or y > y1:
        return None
    t = c["tipo"]
    if t == "plano":
        return c["z"] if _dentro(c["poligono"], x, y) else None
    if t == "malla":
        if c.get("poligono") and not _dentro(c["poligono"], x, y):
            return None
        nx, ny, z = c["nx"], c["ny"], c["z"]
        fx, fy = (x - x0) / ((x1 - x0) or 1e-9) * (nx - 1), (y - y0) / ((y1 - y0) or 1e-9) * (ny - 1)
        i, j = min(nx - 2, max(0, int(math.floor(fx)))), min(ny - 2, max(0, int(math.floor(fy))))
        u, v = fx - i, fy - j
        a, b, cc, d = z[j * nx + i], z[j * nx + i + 1], z[(j + 1) * nx + i], z[(j + 1) * nx + i + 1]
        return (a * (1 - u) + b * u) * (1 - v) + (cc * (1 - u) + d * u) * v
    if t == "perfil":
        P, mejor, zm = c["puntos"], math.inf, None
        for a, b in zip(P, P[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            h = min(1.0, max(0.0, ((x - a[0]) * dx + (y - a[1]) * dy) / ((dx * dx + dy * dy) or 1e-9)))
            d = math.hypot(x - a[0] - dx * h, y - a[1] - dy * h)
            if d < mejor:
                mejor, zm = d, a[2] + (b[2] - a[2]) * h
        return zm if mejor <= c["ancho"] else None
    return None


def en(campos, x, y):
    """El relieve de pieza en (x, y): el campo más alto que lo cubre; 0 si ninguno."""
    h = None
    for c in campos or ():
        v = campo_en(c, x, y)
        if v is not None and (h is None or v > h):
            h = v
    return h or 0.0


def revisar(campos, que, Falla):
    """Lo que publica una pieza en `_alturas` está bien formado (lo llama maqueta3d.resolver)."""
    for c in campos:
        t = c.get("tipo") if isinstance(c, dict) else None
        ok = isinstance(c, dict) and isinstance(c.get("caja"), list) and len(c["caja"]) == 4
        if t == "perfil":
            ok = ok and len(c.get("puntos") or []) >= 2 and c.get("ancho", 0) > 0
        elif t == "plano":
            ok = ok and len(c.get("poligono") or []) >= 6 and isinstance(c.get("z"), (int, float))
        elif t == "malla":
            ok = ok and c.get("nx", 0) >= 2 and c.get("ny", 0) >= 2 and len(c.get("z") or []) == c["nx"] * c["ny"]
        else:
            ok = False
        if not ok:
            raise Falla("M3D2", "%s: publica un relieve (`_alturas`) mal formado: va perfil(puntos, ancho), plano(poligono, z) o malla(caja, nx, ny, f) de maqueta_tipos/_relieve.py" % que)
