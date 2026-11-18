"""Pieza «fosa»: la fosa oceánica como línea esquemática mar adentro, que pasa por `por` y corre paralela a la recta que
mejor ajusta a `paralela_a` (el eje principal de esos lugares). Con `flechas`, unos carriles de galones que avanzan hacia
la fosa desde el mar (perpendiculares a ella, girados `desvio_grados`) y se meten bajo la costa.

Resuelta: {cadena: [[x, y, s, salto]] (km), largo_km, dir: [dx, dy], normal: [nx, ny] (hacia tierra), esquematica,
carriles: [cadena con s = 0 en el cruce de la fosa], adentro_km}. Publica SUS LUGARES (`_lugares`): «fosa» (en `por`),
«placa-oceanica» (mar afuera) y «placa-continental» (del lado de tierra). Las posiciones de las placas son ilustrativas."""
import math

PASO = 5.0          # km entre puntos de la cadena
AFUERA = 150.0      # km de carril de flecha mar afuera de la fosa
N_CARRILES = 5


def _eje(pts):
    """Dirección del eje principal (unitaria) de una nube de puntos [(x, y)]."""
    n = len(pts)
    mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return (math.cos(th), math.sin(th)), (mx, my)


def _recta(S, cx, cy, ux, uy, a, b):
    """Cadena [[x, y, s, salto]] de cx+u·a a cx+u·b cada PASO km, solo lo que cae dentro del set (s medido desde a)."""
    k = max(2, int(math.ceil((b - a) / PASO)))
    out = []
    for j in range(k + 1):
        s = a + (b - a) * j / k
        x, y = cx + ux * s, cy + uy * s
        if S.dentro(x, y):
            out.append([round(x, 3), round(y, 3), round(s - a, 3), False])
    if out:
        out[-1][3] = True
    return out


def resolver(p, X, que):
    M3, S = X.m3, X.S
    if getattr(S, "escala", "pais") != "pais":
        raise M3.Falla("M3D2", "%s: «fosa» es de escala pais (km sobre el relieve del set)" % que)
    c = X.lugar(p["por"], "%s → por" % que)
    cx, cy = c["x"], c["y"]
    tierra = [X.lugar(r, "%s → paralela_a[%d]" % (que, i)) for i, r in enumerate(p["paralela_a"])]
    (dx, dy), (mx, my) = _eje([(l["x"], l["y"]) for l in tierra])
    if dx < 0 or (dx == 0 and dy < 0):
        dx, dy = -dx, -dy
    nx, ny = -dy, dx                                   # normal: la que apunta hacia los lugares en tierra
    D = (mx - cx) * nx + (my - cy) * ny
    if D < 0:
        nx, ny, D = -nx, -ny, -D
    if D < 10:
        raise M3.Falla("M3D2", "%s: `por` queda sobre la recta de `paralela_a` (a %.0f km): la fosa va mar adentro" % (que, D))
    L = float(p.get("largo_km", 500))
    cadena = _recta(S, cx, cy, dx, dy, -L / 2, L / 2)
    if len(cadena) < 2:
        raise M3.Falla("M3D2", "%s: la fosa cae fuera de la caja del set %s" % (que, S.id))
    out = {"cadena": cadena, "largo_km": cadena[-1][2], "dir": [round(dx, 4), round(dy, 4)],
           "normal": [round(nx, 4), round(ny, 4)], "esquematica": bool(p.get("esquematica", True)),
           "carriles": [], "adentro_km": round(0.55 * D, 2)}
    if p.get("flechas"):
        g = math.radians(float(p.get("desvio_grados", 0) or 0))
        ax, ay = nx * math.cos(g) - ny * math.sin(g), nx * math.sin(g) + ny * math.cos(g)
        adentro = 0.55 * D
        for i in range(N_CARRILES):
            off = (i - (N_CARRILES - 1) / 2) * (0.7 * L / (N_CARRILES - 1))
            px, py = cx + dx * off, cy + dy * off
            car = _recta(S, px, py, ax, ay, -AFUERA, adentro)
            if len(car) >= 2:
                for q in car:                           # s = 0 en el cruce de la fosa
                    q[2] = round(q[2] - AFUERA, 3)
                out["carriles"].append(car)
    lug = {"fosa": (cx, cy, "Fosa", 0.6),
           "placa-oceanica": (cx - nx * 110, cy - ny * 110, "Placa oceánica", 0.5),
           "placa-continental": (cx + nx * 0.6 * D, cy + ny * 0.6 * D, "Placa continental", 0.5)}
    out["_lugares"] = {k: {"x": round(x, 3), "y": round(y, 3), "nombre": n, "peso": w}
                       for k, (x, y, n, w) in lug.items() if S.dentro(x, y)}
    return out


def tramos(pz):
    return [[(q[0], q[1], bool(q[3])) for q in pz["cadena"]]]


def centro(pz, G):
    return G["m3"].punto_en_s([q[:3] for q in pz["cadena"]], pz["largo_km"] / 2)
