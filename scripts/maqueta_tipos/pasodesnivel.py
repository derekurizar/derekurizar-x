"""Pieza «pasodesnivel»: un paso a desnivel sobre un cruce REAL de la traza de OpenStreetMap (capa `calles` de un set de
ciudad). La vía principal (el EJE) sube en puente (`forma: sobre`) o baja en trinchera (`forma: bajo`) y las calles que
cruza siguen a nivel.

1. El EJE: si no se da `rumbo`, la vía de la capa cuyo nombre dice «desnivel» más cercana a `lugar` (hasta 450 m),
   cosida extremo con extremo y suavizada (la traza de OSM trae quiebres de pocos metros). Si no la hay, o si se da
   `rumbo` (grados; 0 = este, 90 = norte), una recta por el punto de la red vial más cercano a `lugar`. `largo_m` (solo si
   se verificó) recorta o alarga el eje desde su medio; sin él, el largo es el de la traza (o 360 m en la recta).
2. Las CALLES A NIVEL: las vías de la capa (autopista a terciaria) a menos de R m del medio del eje, recortadas al
   círculo; las que cortan el eje lejos de sus extremos son las que CRUZA.
3. El PERFIL (ilustrativo: ni la altura ni el número de pilas se afirman): a H m en cada cruce con una meseta de 14 m y
   rampas de ≤ 7.5 % hasta los extremos, que quedan a nivel (en `bajo`, lo mismo hacia abajo).

Publica:
- `_caminos`: «<id>.arriba-1» y «<id>.arriba-2» (el eje, un carril en cada sentido) y «<id>.abajo-1» y «<id>.abajo-2» (la
  calle que cruza, en sus dos sentidos). En `sobre`, abajo es la calle a nivel y arriba el puente; en `bajo`, abajo es la
  trinchera y arriba la calle a nivel. Van a ras del suelo del mundo (sin relieve: la pieza no levanta lo que pasa debajo
  del tablero): los carros que suben y bajan los dibuja la pieza con `carros`.
- `_lugares`: entrada y salida (los extremos del eje), cruce (donde el eje pasa sobre o bajo la calle principal) y centro.
- `_cosas` (las partes con volumen que mide maqueta_escena, M3D15–M3D16), con las medidas de pasodesnivel.js: el tablero
  y las rampas en tramos de ≈ 24 m (con los carros que suben y bajan), las pilas con su viga cabezal, las jardineras, los
  postes de luz y de señal; en `bajo`, los pretiles de la trinchera y la losa del cruce. La calle que cruza, donde corren
  los carros a nivel, y las aceras donde camina la gente van en tramos de ≈ 40 m (como las arboledas de `agrupar`: lo
  que se mueve por ahí, sin afirmar dónde va cada uno en t)."""
import math
import random

import maqueta_escena as ME
from maqueta_tipos import _mundo as MU

H_SOBRE, H_BAJO = 7.4, -6.6     # m: el tablero sobre la calle / el fondo de la trinchera
MESETA, PEND, PEND_FIN = 14.0, 0.05, 0.075
ANCHO_EJE = 9.0
PASO = 4.0
CLASES = {"autopista": 10.5, "primaria": 8.5, "secundaria": 7.0, "terciaria": 6.0}
RANGO = {"autopista": 0, "primaria": 1, "secundaria": 2, "terciaria": 3}


def _largo(c):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(c, c[1:]))


def _remuestrear(pts, paso):
    out = [tuple(pts[0])]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(math.ceil(L / paso)))
        for j in range(1, k + 1):
            out.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return out


def _parejo(pts, paso):
    """La polilínea remuestreada cada `paso` m exactos (por longitud de arco)."""
    d = _remuestrear(pts, 0.5)
    L = _largo(d)
    n = max(2, int(round(L / paso)) + 1)
    out, acc, i = [], 0.0, 0
    for k in range(n):
        s = L * k / (n - 1)
        while i < len(d) - 2 and acc + math.hypot(d[i + 1][0] - d[i][0], d[i + 1][1] - d[i][1]) < s:
            acc += math.hypot(d[i + 1][0] - d[i][0], d[i + 1][1] - d[i][1])
            i += 1
        lg = math.hypot(d[i + 1][0] - d[i][0], d[i + 1][1] - d[i][1]) or 1e-9
        u = min(1.0, max(0.0, (s - acc) / lg))
        out.append((d[i][0] + (d[i + 1][0] - d[i][0]) * u, d[i][1] + (d[i + 1][1] - d[i][1]) * u))
    return out


def _suavizar(c, pasadas, ventana):
    c = list(c)
    for _ in range(pasadas):
        n = len(c)
        c = [c[0]] + [(sum(c[j][0] for j in range(max(0, i - ventana), min(n, i + ventana + 1))) / (min(n, i + ventana + 1) - max(0, i - ventana)),
                       sum(c[j][1] for j in range(max(0, i - ventana), min(n, i + ventana + 1))) / (min(n, i + ventana + 1) - max(0, i - ventana)))
                      for i in range(1, n - 1)] + [c[-1]]
    return c


def _coser(segs):
    segs = [[tuple(q) for q in s] for s in segs if len(s) >= 2]
    if not segs:
        return []
    key = lambda q: (round(q[0]), round(q[1]))
    i0 = max(range(len(segs)), key=lambda i: _largo(segs[i]))
    c = list(segs[i0])
    usados = {i0}
    cambio = True
    while cambio:
        cambio = False
        for i, s in enumerate(segs):
            if i in usados:
                continue
            if key(s[0]) == key(c[-1]):
                c += s[1:]
            elif key(s[-1]) == key(c[0]):
                c = s[:-1] + c
            elif key(s[-1]) == key(c[-1]):
                c += s[::-1][1:]
            elif key(s[0]) == key(c[0]):
                c = s[::-1][:-1] + c
            else:
                continue
            usados.add(i)
            cambio = True
    return c


def _corte(p, q, r, s):
    d = (q[0] - p[0]) * (s[1] - r[1]) - (q[1] - p[1]) * (s[0] - r[0])
    if abs(d) < 1e-9:
        return None
    u = ((r[0] - p[0]) * (s[1] - r[1]) - (r[1] - p[1]) * (s[0] - r[0])) / d
    v = ((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0])) / d
    if 0 <= u <= 1 and 0 <= v <= 1:
        return u, v
    return None


def _recortar(pts, cx, cy, R):
    d = _remuestrear(pts, 3.0)
    partes, cur = [], []
    for q in d:
        if math.hypot(q[0] - cx, q[1] - cy) <= R:
            cur.append(q)
        elif cur:
            partes.append(cur)
            cur = []
    if cur:
        partes.append(cur)
    return [_parejo(p, 6.0) for p in partes if len(p) >= 3 and _largo(p) >= 15]


def _cerca(pts, x, y):
    return min(math.hypot(a[0] - x, a[1] - y) for a in pts)


def _punto_en(c, s):
    acc = 0.0
    for a, b in zip(c, c[1:]):
        lg = math.hypot(b[0] - a[0], b[1] - a[1])
        if acc + lg >= s:
            u = (s - acc) / (lg or 1e-9)
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        acc += lg
    return c[-1]


def _ajustar_largo(c, L):
    """El eje recortado o alargado (en recta, por sus puntas) a L m, desde su medio."""
    L0 = _largo(c)
    if L >= L0:
        e = (L - L0) / 2
        a, b = c[0], c[1]
        da = math.hypot(a[0] - b[0], a[1] - b[1]) or 1
        y, z = c[-1], c[-2]
        dz = math.hypot(y[0] - z[0], y[1] - z[1]) or 1
        return [(a[0] + (a[0] - b[0]) / da * e, a[1] + (a[1] - b[1]) / da * e)] + list(c) + [(y[0] + (y[0] - z[0]) / dz * e, y[1] + (y[1] - z[1]) / dz * e)]
    s0 = (L0 - L) / 2
    d = _parejo(c, 1.0)
    acc, out = 0.0, []
    for i, q in enumerate(d):
        if i:
            acc += math.hypot(q[0] - d[i - 1][0], q[1] - d[i - 1][1])
        if s0 <= acc <= s0 + L:
            out.append(q)
    return out


def _cadena(pts, um, rev=False, d=0.0):
    """[[x, y, s, 0]] en unidades de la escena, corrida d m a la izquierda de su sentido (rev: el sentido contrario)."""
    c = list(pts[::-1] if rev else pts)
    out, s = [], 0.0
    for i, q in enumerate(c):
        a, b = c[max(0, i - 1)], c[min(len(c) - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        x, y = q[0] - (b[1] - a[1]) / L * d, q[1] + (b[0] - a[0]) / L * d
        if out:
            s += math.hypot(x - out[-1][0] * um, y - out[-1][1] * um)
        out.append([round(x / um, 2), round(y / um, 2), round(s / um, 2), 0])
    return out


def resolver(p, X, que):
    S = X.S
    if S.escala != "ciudad":
        raise X.m3.Falla("M3D2", "%s: el paso a desnivel sale de la traza de OpenStreetMap de un set de ciudad (este mundo es %s)" % (que, S.escala))
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    l = X.lugar(p["lugar"], que + " → lugar")
    lx, ly = l["x"] * um, l["y"] * um
    calles = MU.capa(X, "calles", que)["calles"]
    forma = p.get("forma") or "bajo"
    rumbo = p.get("rumbo")

    # ---- 1. el eje
    eje, de_osm = None, False
    if rumbo is None:
        cand = [q for q in calles if "desnivel" in (q.get("nombre") or "").lower() and _cerca(q["puntos"], lx, ly) < 450]
        if cand:
            nombre = min(cand, key=lambda q: _cerca(q["puntos"], lx, ly))["nombre"]
            segs = [q["puntos"] for q in cand if q["nombre"] == nombre]
            c = _coser(segs)
            if c and _largo(c) >= 60:
                eje, de_osm = c, True
    if eje is None:
        red = [q for q in calles if q["clase"] in CLASES]
        mejor = None
        for q in red:
            for a, b in zip(q["puntos"], q["puntos"][1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                h = min(1.0, max(0.0, ((lx - a[0]) * dx + (ly - a[1]) * dy) / ((dx * dx + dy * dy) or 1e-9)))
                x, y = a[0] + dx * h, a[1] + dy * h
                d = math.hypot(x - lx, y - ly)
                if d < 300 and (mejor is None or d < mejor[0]):
                    mejor = (d, x, y, math.atan2(dy, dx))
        cx, cy = (mejor[1], mejor[2]) if mejor else (lx, ly)
        r = math.radians(float(rumbo)) if rumbo is not None else ((mejor[3] + math.pi / 2) if mejor else 0.0)
        L = float(p.get("largo_m") or 360.0)
        eje = [(cx - math.cos(r) * L / 2, cy - math.sin(r) * L / 2), (cx + math.cos(r) * L / 2, cy + math.sin(r) * L / 2)]
    eje = _suavizar(_parejo(eje, 2.0), 6, 4) if de_osm else _parejo(eje, 2.0)
    if p.get("largo_m") and de_osm:
        eje = _ajustar_largo(eje, float(p["largo_m"]))
    eje = _parejo(eje, PASO)
    L = _largo(eje)
    if L < 80:
        raise X.m3.Falla("M3D2", "%s: el eje del paso a desnivel mide %d m: hacen falta ≥ 80 m (da `largo_m` o un `lugar` junto a la vía)" % (que, L))
    sA = [0.0]
    for a, b in zip(eje, eje[1:]):
        sA.append(sA[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    mx, my = _punto_en(eje, L / 2)

    # ---- 2. las calles a nivel (y cuáles cruza)
    R = max(240.0, L / 2 + 90)
    vias = []
    for q in calles:
        if q["clase"] not in CLASES or "desnivel" in (q.get("nombre") or "").lower():
            continue
        if _cerca(q["puntos"], mx, my) > R + 40:
            continue
        for c in _recortar(q["puntos"], mx, my, R):
            vias.append({"c": c, "clase": q["clase"], "nombre": q.get("nombre") or "", "ancho": CLASES[q["clase"]]})
    cruces = []
    for k, v in enumerate(vias):
        c = v["c"]
        for i in range(len(eje) - 1):
            for j in range(len(c) - 1):
                r = _corte(eje[i], eje[i + 1], c[j], c[j + 1])
                if not r:
                    continue
                s = sA[i] + (sA[i + 1] - sA[i]) * r[0]
                if s < 18 or s > L - 18:
                    continue
                x, y = eje[i][0] + (eje[i + 1][0] - eje[i][0]) * r[0], eje[i][1] + (eje[i + 1][1] - eje[i][1]) * r[0]
                cruces.append({"via": k, "s": s, "x": x, "y": y})
                v["cruza"] = True
    # ---- 3. el perfil
    H = H_SOBRE if forma == "sobre" else H_BAJO
    sig = 1 if H > 0 else -1
    Hm = abs(H)
    z = []
    for s in sA:
        if cruces:
            h = max(Hm - PEND * max(0.0, abs(s - c["s"]) - MESETA) for c in cruces)
        else:
            h = Hm
        h = max(0.0, min(h, PEND_FIN * s, PEND_FIN * (L - s), Hm))
        z.append(h)
    for _ in range(3):
        z = [z[0]] + [(z[i - 1] + z[i] + z[i + 1]) / 3 for i in range(1, len(z) - 1)] + [z[-1]]
    z = [round(sig * h, 2) for h in z]

    # ---- la calle principal que cruza (la de mayor clase; con su pareja del mismo nombre, el otro sentido)
    cruzan = sorted({c["via"] for c in cruces}, key=lambda k: (RANGO[vias[k]["clase"]], -_largo(vias[k]["c"])))
    if cruces:
        k1 = cruzan[0]
        c1 = min((c for c in cruces if c["via"] == k1), key=lambda c: abs(c["s"] - L / 2))
        par = [k for k in cruzan[1:] if vias[k]["nombre"] and vias[k]["nombre"] == vias[k1]["nombre"] and vias[k]["clase"] == vias[k1]["clase"]]
        abajo1 = _cadena(vias[k1]["c"], um, d=-vias[k1]["ancho"] * 0.25 if not par else 0)
        abajo2 = _cadena(vias[par[0]]["c"], um) if par else _cadena(vias[k1]["c"], um, rev=True, d=-vias[k1]["ancho"] * 0.25)
        crx, cry = c1["x"], c1["y"]
    else:
        # sin cruce en la traza: una calle a nivel genérica perpendicular por el medio (ilustrativa)
        a, b = eje[len(eje) // 2 - 1], eje[len(eje) // 2 + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        tr = [(mx + dy / n * 160, my - dx / n * 160), (mx - dy / n * 160, my + dx / n * 160)]
        tr = _parejo(tr, 6.0)
        vias.append({"c": tr, "clase": "secundaria", "nombre": "", "ancho": 9.0, "cruza": True})
        X.avisos.append("%s: el eje no corta ninguna calle de la traza: va una calle a nivel genérica por el medio" % que)
        abajo1 = _cadena(tr, um, d=-2.2)
        abajo2 = _cadena(tr, um, rev=True, d=-2.2)
        crx, cry = mx, my
    arriba1 = _cadena(eje, um, d=-ANCHO_EJE * 0.25)
    arriba2 = _cadena(eje, um, rev=True, d=-ANCHO_EJE * 0.25)
    if forma == "sobre":
        caminos = {"arriba-1": arriba1, "arriba-2": arriba2, "abajo-1": abajo1, "abajo-2": abajo2}
    else:
        caminos = {"abajo-1": arriba1, "abajo-2": arriba2, "arriba-1": abajo1, "arriba-2": abajo2}

    Rnd = random.Random(int(p["semilla"]) * 7919 + 17)
    r = {"forma": forma, "carros": int(p["carros"]), "personas": int(p["personas"]), "semilla": int(p["semilla"]),
         "eje": [[round(q[0], 2), round(q[1], 2)] for q in eje], "z": z, "ancho": ANCHO_EJE,
         "vias": [{"c": [[round(q[0], 1), round(q[1], 1)] for q in v["c"]], "ancho": v["ancho"], "clase": v["clase"],
                   "cruza": bool(v.get("cruza"))} for v in vias],
         "cruces": [[round(c["x"], 1), round(c["y"], 1), round(c["s"], 1)] for c in cruces],
         "centro": [round(mx, 1), round(my, 1)], "cruce": [round(crx, 1), round(cry, 1)], "fase": round(Rnd.random(), 3),
         "de_osm": de_osm, "largo": round(L, 1)}
    usa = []
    if r["carros"]:
        usa.append("carro")
    if r["personas"]:
        usa.append("persona")
    r["usa"] = usa
    r["_caminos"] = {"%s.%s" % (p["id"], k): v for k, v in caminos.items()}
    r["_cosas"] = _cosas(eje, sA, z, vias, cruces, forma, r["carros"], r["personas"], um)
    lug = {"entrada": ("Entrada", eje[0][0], eje[0][1], 0.6), "salida": ("Salida", eje[-1][0], eje[-1][1], 0.6),
           "cruce": ("Cruce", crx, cry, 0.8), "centro": ("Paso a desnivel", mx, my, 0.9)}
    r["_lugares"] = {k: {"nombre": v[0], "x": round(v[1] / um, 2), "y": round(v[2] / um, 2), "peso": v[3]} for k, v in lug.items()}
    return r


LEV, LOSA, HT, PRETIL = 0.36, 1.4, 4.0, 1.42   # las de pasodesnivel.js: calzada sobre el perfil, losa, altura de pila, baranda


def _trozos(c, largo):
    """La polilínea c (m) en trozos de ≤ largo m → [(i0, i1, x, y, dx, dy, l)] (el medio, la dirección y el largo de cada uno)."""
    s = [0.0]
    for a, b in zip(c, c[1:]):
        s.append(s[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    n = max(1, int(math.ceil(s[-1] / largo)))
    out, i0 = [], 0
    for k in range(1, n + 1):
        i1 = i0
        while i1 < len(c) - 1 and s[i1] < s[-1] * k / n - 1e-6:
            i1 += 1
        if i1 > i0:
            a, b = c[i0], c[i1]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-9
            m = c[(i0 + i1) // 2] if (i1 - i0) % 2 == 0 else ((c[(i0 + i1) // 2][0] + c[(i0 + i1) // 2 + 1][0]) / 2, (c[(i0 + i1) // 2][1] + c[(i0 + i1) // 2 + 1][1]) / 2)
            out.append((i0, i1, m[0], m[1], (b[0] - a[0]) / L, (b[1] - a[1]) / L, s[i1] - s[i0]))
        i0 = i1
    return out


def _cosas(eje, sA, z, vias, cruces, forma, carros, personas, um):
    """Las partes con volumen (`_cosas`) en unidades de la escena, con las medidas y las reglas de pasodesnivel.js."""
    co, N = [], len(eje)
    C = lambda clave, x, y, l, a, h, dx=1.0, dy=0.0, **k: co.append(ME.cosas_pieza(clave, x / um, y / um, l, a, h, dx, dy, **k))

    def normal(i):
        a, b = eje[max(0, i - 1)], eje[min(N - 1, i + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-9
        return (b[0] - a[0]) / L, (b[1] - a[1]) / L, -(b[1] - a[1]) / L, (b[0] - a[0]) / L

    def sobre_via(x, y, m):
        return any(math.hypot(q[0] - x, q[1] - y) < v["ancho"] / 2 + m for v in vias for q in v["c"])

    vivo = {"animado": True, "contiene": ["carros"]} if carros else {}
    if forma == "sobre":
        # el tablero (sobre pilas, z ≥ HT) y las rampas macizas (0.25 < z < HT), en trozos de ≈ 24 m, hasta la baranda
        for i0, i1, x, y, dx, dy, l in _trozos(eje, 24.0):
            zm = max(z[i0:i1 + 1])
            if zm <= 0.25:
                continue
            C("tablero elevado" if min(z[i0:i1 + 1]) >= HT else "rampa", x, y, l, ANCHO_EJE, zm + LEV + PRETIL, dx, dy, **vivo)
        # las pilas (dos columnas y su viga cabezal, cada ≈ 26 m, nunca sobre una calle) y su jardinera con arbustos
        sig = 10.0
        for i in range(N):
            if sA[i] < sig or z[i] < HT:
                continue
            tx, ty, nx, ny = normal(i)
            if any(sobre_via(eje[i][0] + nx * d, eje[i][1] + ny * d, 1.2) for d in (-2.7, 2.7)):
                sig = sA[i] + 4
                continue
            sig = sA[i] + 26
            C("pila con viga cabezal", eje[i][0], eje[i][1], 2.2, ANCHO_EJE * 0.94, z[i] + LEV - LOSA, tx, ty)
            C("jardinera", eje[i][0], eje[i][1], 2.6, 11.0, 1.6, tx, ty, contiene=["arbustos"])
        # los postes de luz sobre el eje, cada ≈ 40 m alternando lado
        sl, lado = 12.0, 1
        for i in range(N):
            if sA[i] < sl or sA[i] > sA[-1] - 10:
                continue
            sl, lado = sA[i] + 40, -lado
            tx, ty, nx, ny = normal(i)
            d = lado * (ANCHO_EJE / 2 - 0.15)
            C("poste de luz", eje[i][0] + nx * d, eje[i][1] + ny * d, 0.6, 3.4, max(0.0, z[i]) + LEV + 1.0 + 9.0, nx, ny)
    else:
        # la trinchera: sus pretiles a nivel (lo hundido no asoma) y la losa por donde la calle cruza encima
        for i0, i1, x, y, dx, dy, l in _trozos(eje, 24.0):
            if min(z[i0:i1 + 1]) < -0.25:
                C("trinchera", x, y, l, ANCHO_EJE + 0.7, 1.72, dx, dy, **vivo)
        for cx, cy, s in cruces:
            i = min(range(N), key=lambda j: abs(sA[j] - s))
            tx, ty, _, _ = normal(i)
            C("losa del cruce", cx, cy, 14.0, ANCHO_EJE + 0.8, 0.3, tx, ty)
    # los postes de señal (sin texto) al pie de cada rampa
    for fin in (0, 1):
        i, st = (N - 1, -1) if fin else (0, 1)
        while 0 < i < N - 1 and abs(z[i]) < 0.6:
            i += st
        i = min(N - 1, max(0, i - st * 3))
        tx, ty, nx, ny = normal(i)
        d = (-1 if fin else 1) * (ANCHO_EJE / 2 + 2.2)
        x, y = eje[i][0] + nx * d, eje[i][1] + ny * d
        if not sobre_via(x, y, 0.5):
            C("poste de señal", x, y, 0.3, 3.2, 5.3, tx, ty)
    # la calle que cruza, donde corren los carros a nivel (la mitad de `carros`), en tramos de ≈ 40 m
    if carros > 1:
        for v in vias:
            if v.get("cruza") and _largo(v["c"]) > 60:
                for i0, i1, x, y, dx, dy, l in _trozos(v["c"], 40.0):
                    C("tráfico a nivel", x, y, l, v["ancho"], 1.5, dx, dy, animado=True, contiene=["carros"])
    # las aceras donde camina la gente (las mismas de pasodesnivel.js: hasta 3 calles, primero las que cruza y las largas)
    if personas:
        ac = sorted([v for v in vias if v["clase"] != "autopista" and _largo(v["c"]) > 40], key=lambda v: (-bool(v.get("cruza")), -_largo(v["c"])))
        for v in ac[:min(3, personas)]:
            for i0, i1, x, y, dx, dy, l in _trozos(v["c"], 40.0):
                C("acera con gente", x, y, l, v["ancho"] + 4.4, 1.8, dx, dy, animado=True, gente=True, contiene=["gente"])
    return co


def centro(pz, G):
    return pz["centro"][0], pz["centro"][1]


def tramos(pz):
    return [[(q[0], q[1], False) for q in pz["eje"]]]


def elemento(pz, x, y):
    """Cualquier lugar de la pieza resalta el paso entero."""
    return 0
