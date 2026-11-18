"""Pieza «bulevar1890»: el Bulevar 30 de Junio de la década de 1890 sobre el trazo REAL de la Avenida Reforma (calles.json del
set de la ciudad: los tramos «Avenida Reforma» de OpenStreetMap, sus dos sentidos promediados en un solo eje), entre `desde`
y `hacia`, sin la ciudad moderna. Corte (de oeste a este, ancho total `ancho_*_m`, por defecto 40 m genéricos): acera de
peatones · jardín con árboles · calzada de carruajes · jardín central (estatuas y fuentes) · calzada · jardín · acera.

Publica sus CAMINOS: «<id>» y «<id>.eje» (el eje, de desde a hacia), «<id>.carruajes-1» (la calzada a la derecha del eje, en
su sentido), «<id>.carruajes-2» (la otra, en sentido contrario), «<id>.peatones-este» y «<id>.peatones-oeste» (las aceras,
de desde a hacia). Sus LUGARES: inicio (el eje junto a `desde`), jardin (el jardín central a la mitad), estatuas (entre las
dos estatuas de en medio), fuente-1..3 (las fuentes del jardín central, de desde a hacia), estanque-1..2 (los de los
jardines laterales), palacio (el centro del palacio, al extremo SUR del tramo) y plaza (la explanada frente al palacio: el
refugio del terremoto). `grupos_paseantes` y `escala_gente` pasan tal cual al módulo (grupos, escala_gente).

Elementos para «resaltar» con `elemento`: palacio → 0 (con el monumento), jardin → 1 (los jardines), estatuas → 2 (todas,
encendidas EN ORDEN de desde a hacia a lo largo del resaltado), inicio → 3 (el primer tramo); otro punto → la estatua más
cercana (100 + j) o, si lejos, la parte más cercana.
Resuelta: {eje, anchos, largo_m, estatuas: [[x, y, dx, dy], …], fuentes, estanques, quintas, palacio, plaza, monumento,
carruajes, paseantes, semilla, lug, usa}."""
import math
import random

import maqueta_escena as ME
from maqueta_tipos import _mundo as MU
from maqueta_tipos.esquema import cadena

NOMBRE = "Avenida Reforma"
ANCHO = 40.0        # el ancho total genérico (m) si no se da `ancho_inicio_m`/`ancho_fin_m`
# el corte, en fracciones del medio ancho (22 partes): jardín central, calzada, jardín lateral, acera
F_CENTRAL, F_CALZ, F_JARDIN, F_ACERA = 4.5 / 22, 7.0 / 22, 7.0 / 22, 3.5 / 22
PAL_FONDO, PAL_ANCHO, PAL_GAP = 26.0, 50.0, 36.0


def _eje_set(X, que):
    calles = MU.capa(X, "calles", que).get("calles") or []
    segs = [s["puntos"] for s in calles if s.get("nombre") == NOMBRE and s.get("clase") in ("primaria", "secundaria", "troncal")]
    if not segs:
        raise X.m3.Falla("M3D2", "%s: el set %s no tiene la «%s» en calles.json (la pieza va sobre su trazo real)" % (que, X.S.id, NOMBRE))
    P = []
    for pts in segs:
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            k = max(1, int(L // 5))
            for j in range(k):
                P.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
        P.append(tuple(pts[-1]))
    mx, my = sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P)
    sxx = sum((p[0] - mx) ** 2 for p in P); syy = sum((p[1] - my) ** 2 for p in P); sxy = sum((p[0] - mx) * (p[1] - my) for p in P)
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ax, ay = math.cos(ang), math.sin(ang)
    if ay < 0:
        ax, ay = -ax, -ay                      # de sur a norte
    B = 25.0
    bins = {}
    for x, y in P:
        k = int(math.floor(((x - mx) * ax + (y - my) * ay) / B))
        bins.setdefault(k, []).append((x, y))
    eje = [(sum(q[0] for q in v) / len(v), sum(q[1] for q in v) / len(v)) for k, v in sorted(bins.items())]
    for _ in range(3):                         # suavizado (media de 5)
        eje = [eje[0]] + [tuple(sum(eje[j][c] for j in range(max(0, i - 2), min(len(eje), i + 3))) / (min(len(eje), i + 3) - max(0, i - 2)) for c in (0, 1))
                          for i in range(1, len(eje) - 1)] + [eje[-1]]
    return eje


def _proyectar(cad, x, y):
    """(s, distancia) del punto más cercano de la cadena [[x, y, s, 0], …]."""
    mejor = (0.0, 1e18)
    for a, b in zip(cad, cad[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        u = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        px, py = a[0] + dx * u, a[1] + dy * u
        d = math.hypot(x - px, y - py)
        if d < mejor[1]:
            mejor = (a[2] + (b[2] - a[2]) * u, d)
    return mejor


def _en(cad, s):
    """(x, y, dx, dy) en la posición s de la cadena."""
    s = max(0.0, min(cad[-1][2], s))
    for a, b in zip(cad, cad[1:]):
        if b[2] >= s:
            L = (b[2] - a[2]) or 1e-9
            u = (s - a[2]) / L
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, (b[0] - a[0]) / L, (b[1] - a[1]) / L
    a, b = cad[-2], cad[-1]
    L = (b[2] - a[2]) or 1e-9
    return b[0], b[1], (b[0] - a[0]) / L, (b[1] - a[1]) / L


def _corrida(eje, offs):
    """La polilínea corrida offs[i] metros a su izquierda en cada vértice (negativo: a la derecha)."""
    out = []
    for i, (x, y) in enumerate(eje):
        a, b = eje[max(0, i - 1)], eje[min(len(eje) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append([x - dy / L * offs[i], y + dx / L * offs[i]])
    return out


def resolver(p, X, que):
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    if X.S.escala != "ciudad":
        raise X.m3.Falla("M3D2", "%s: bulevar1890 va sobre el trazo real de la %s: solo en un mundo de escala ciudad (set capital)" % (que, NOMBRE))
    base = cadena([list(q) for q in _eje_set(X, que)])
    la, lb = X.lugar(p["desde"], que + " → desde"), X.lugar(p["hacia"], que + " → hacia")
    sa, da = _proyectar(base, la["x"], la["y"])
    sb, db = _proyectar(base, lb["x"], lb["y"])
    for nom, d in (("desde", da), ("hacia", db)):
        if d * um > 150:
            X.avisos.append("%s: `%s` queda a %d m de la %s: el tramo empieza en su punto más cercano" % (que, nom, d * um, NOMBRE))
    if abs(sb - sa) * um < 150:
        raise X.m3.Falla("M3D2", "%s: entre `desde` y `hacia` hay %d m de la %s: el bulevar necesita ≥ 150 m" % (que, abs(sb - sa) * um, NOMBRE))
    paso = 8.0 / um
    n = max(2, int(abs(sb - sa) / paso))
    eje = [list(_en(base, sa + (sb - sa) * i / n)[:2]) for i in range(n + 1)]
    cad = cadena(eje)
    L = cad[-1][2]
    w0 = p.get("ancho_inicio_m") or p.get("ancho_fin_m") or ANCHO
    w1 = p.get("ancho_fin_m") or p.get("ancho_inicio_m") or ANCHO
    anchos = [round((w0 + (w1 - w0) * q[2] / (L or 1)) / um, 2) for q in cad]
    H = [w / 2 for w in anchos]
    off = lambda f: [h * f for h in H]
    c_cal = F_CENTRAL + F_CALZ / 2
    c_ace = F_CENTRAL + F_CALZ + F_JARDIN + F_ACERA / 2
    pid = p["id"]
    car1 = _corrida(eje, off(-c_cal))
    car2 = _corrida(eje, off(c_cal))[::-1]
    izq, der = _corrida(eje, off(c_ace)), _corrida(eje, off(-c_ace))
    # la acera de la izquierda del eje, ¿es la del este? (la normal izquierda del tramo medio)
    xm, ym, dxm, dym = _en(cad, L / 2)
    izq_este = -dym > 0
    caminos = {pid: cadena(eje), pid + ".eje": cadena(eje), pid + ".carruajes-1": cadena(car1), pid + ".carruajes-2": cadena(car2),
               pid + ".peatones-este": cadena(izq if izq_este else der), pid + ".peatones-oeste": cadena(der if izq_este else izq)}
    rnd = random.Random(int(p.get("semilla", 1)) * 7919 + 13)

    def punto(s, v):
        x, y, dx, dy = _en(cad, s)
        return x - dy * v, y + dx * v, dx, dy

    def hm(s):
        return H[min(len(H) - 1, int(round(s / (L or 1) * (len(H) - 1))))]

    # las fuentes del jardín central (genéricas) y los estanques de los jardines laterales (sin forma precisa)
    fuentes = []
    for f in (0.2, 0.5, 0.8):
        x, y, dx, dy = punto(f * L, 0.0)
        fuentes.append([round(x, 2), round(y, 2), round(dx, 4), round(dy, 4)])
    estanques = []
    for f, lado in ((0.36, 1), (0.64, -1)):
        s = f * L
        v = lado * hm(s) * (F_CENTRAL + F_CALZ + F_JARDIN / 2)
        x, y, dx, dy = punto(s, v)
        estanques.append([round(x, 2), round(y, 2), round(dx, 4), round(dy, 4)])
    # las estatuas: en los bordes del jardín central, alternando lados, de desde a hacia; nunca encima de una fuente
    N = int(p.get("estatuas", 30))
    estatuas = []
    if N:
        m0, m1 = 24.0 / um, L - 24.0 / um
        for j in range(N):
            s = m0 + (m1 - m0) * (j + 0.5) / N
            for f in (0.2, 0.5, 0.8):
                if abs(s - f * L) < 7.5 / um:
                    s = f * L + (7.5 / um if s >= f * L else -7.5 / um)
            lado = 1 if j % 2 == 0 else -1
            v = lado * (hm(s) * F_CENTRAL - 1.4 / um)
            x, y, dx, dy = punto(s, v)
            estatuas.append([round(x, 2), round(y, 2), round(-dy * lado, 4), round(dx * lado, 4)])
    # el palacio al extremo SUR del tramo, mirando a lo largo del paseo; el monumento ecuestre y la explanada al frente
    sur_fin = cad[-1][1] < cad[0][1]
    palacio = plaza = monumento = None
    if p.get("palacio", True):
        if sur_fin:
            ex, ey, dx, dy = _en(cad, L)
        else:
            ex, ey, dx, dy = _en(cad, 0.0)
            dx, dy = -dx, -dy
        pc = (ex + dx * (PAL_GAP + PAL_FONDO / 2) / um, ey + dy * (PAL_GAP + PAL_FONDO / 2) / um)
        palacio = [round(pc[0], 2), round(pc[1], 2), round(-dx, 4), round(-dy, 4)]
        plaza = [round(ex + dx * 13 / um, 2), round(ey + dy * 13 / um, 2)]
        monumento = [round(ex + dx * 24 / um, 2), round(ey + dy * 24 / um, 2), round(-dx, 4), round(-dy, 4)]
    # las quintas: dispersas en el campo a los dos lados, mirando al paseo, separadas entre sí y lejos del palacio
    quintas = []
    NQ = int(p.get("quintas", 6))
    intentos = 0
    while len(quintas) < NQ and intentos < 400:
        intentos += 1
        s = rnd.uniform(0.06, 0.94) * L
        lado = 1 if rnd.random() < 0.5 else -1
        v = lado * (hm(s) + rnd.uniform(38, 120) / um)
        x, y, dx, dy = punto(s, v)
        if any(math.hypot(x - q[0], y - q[1]) < 85 / um for q in quintas):
            continue
        if palacio and math.hypot(x - palacio[0], y - palacio[1]) < 95 / um:
            continue
        quintas.append([round(x, 2), round(y, 2), round(dy * lado, 4), round(-dx * lado, 4), rnd.randint(0, 2)])
    # los lugares que publica
    lug = {}
    x, y, _, _ = punto(min(L, 14 / um), 0.0)
    lug["inicio"] = ("Inicio del paseo", x, y, 0.6)
    x, y, _, _ = punto(0.5 * L + 18 / um, 0.0)
    lug["jardin"] = ("Jardín central", x, y, 0.6)
    if estatuas:
        a, b = estatuas[max(0, len(estatuas) // 2 - 1)], estatuas[len(estatuas) // 2]
        lug["estatuas"] = ("Estatuas", (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.5)
    for j, q in enumerate(fuentes):            # las fuentes del jardín central y los estanques: donde apunta la cámara con «jardines»
        lug["fuente-%d" % (j + 1)] = ("Fuente", q[0], q[1], 0.4)
    for j, q in enumerate(estanques):
        lug["estanque-%d" % (j + 1)] = ("Estanque", q[0], q[1], 0.35)
    if palacio:
        lug["palacio"] = ("Palacio", palacio[0], palacio[1], 0.9)
        lug["plaza"] = ("Explanada", plaza[0], plaza[1], 0.4)
    r = {"eje": [[round(q[0], 2), round(q[1], 2)] for q in eje], "anchos": anchos, "largo_m": round(L * um, 1),
         "estatuas": estatuas, "fuentes": fuentes, "estanques": estanques, "quintas": quintas, "palacio": palacio, "plaza": plaza,
         "monumento": monumento, "carruajes": int(p.get("carruajes", 4)), "paseantes": int(p.get("paseantes", 12)),
         "semilla": int(p.get("semilla", 1)), "izq_este": izq_este,
         "grupos": int(p.get("grupos_paseantes", 0)), "escala_gente": float(p.get("escala_gente", 1.0)),
         "lug": {k: [round(v[1], 2), round(v[2], 2)] for k, v in lug.items()}}
    r["usa"] = ["arbol"] + (["persona"] if r["paseantes"] or r["grupos"] else [])
    # LAS PARTES CON VOLUMEN (`_cosas`, las mide maqueta_escena: M3D15–M3D16), con las medidas de bulevar1890.js
    co = []
    if palacio:
        co.append(ME.cosas_pieza("palacio", palacio[0], palacio[1], 2 * 13 + 2.4, 2 * 25 + 2.4, 16.5, palacio[2], palacio[3]))
        co.append(ME.cosas_pieza("monumento ecuestre", monumento[0], monumento[1], 5, 5, 7, monumento[2], monumento[3]))
    for q in quintas:
        co.append(ME.cosas_pieza("quinta", q[0], q[1], 36, 44, 7.2 if q[4] == 2 else 4.0, q[2], q[3]))
    for q in estatuas:
        co.append(ME.cosas_pieza("estatua", q[0], q[1], 1.9, 1.9, 2.4, q[2], q[3]))
    for q in fuentes:
        co.append(ME.cosas_pieza("fuente", q[0], q[1], 7, 7, 3, q[2], q[3]))
    filas = []   # la fila de árboles de cada jardín lateral (la misma regla que bulevar1890.js), en arboledas de ≈ 56 m
    for sg in (1, -1):
        s = 6 / um
        while s < L - 4 / um:
            filas.append(punto(s, sg * hm(s) * (F_CENTRAL + F_CALZ + F_JARDIN * 0.5))[:2])
            s += 14 / um
    co += ME.agrupar(filas, 56 / um, lambda q: "arboleda", 7.0, 4.4, um)
    r["_cosas"] = co
    r["_caminos"] = caminos
    r["_lugares"] = {k: {"nombre": v[0], "x": round(v[1], 2), "y": round(v[2], 2), "peso": v[3]} for k, v in lug.items()}
    return r


def tramos(pz):
    return [[(x, y, False) for x, y in pz["eje"]]]


def centro(pz, G):
    e = pz["eje"]
    return e[len(e) // 2][0], e[len(e) // 2][1]


def huella_m(pz):
    e = pz["eje"]
    (x0, y0), (x1, y1) = e[0], e[-1]
    return math.hypot(x1 - x0, y1 - y0) / 2 + 80, max(pz["anchos"]) / 2 + 130, math.atan2(y1 - y0, x1 - x0)


def elemento(pz, x, y):
    lug = pz.get("lug") or {}
    codigos = {"palacio": 0, "plaza": 0, "jardin": 1, "estatuas": 2, "inicio": 3}
    codigos.update({k: 1 for k in lug if k.startswith(("fuente-", "estanque-"))})   # una fuente o un estanque: los jardines
    for k, (lx, ly) in lug.items():
        if math.hypot(x - lx, y - ly) < 0.6 and k in codigos:
            return codigos[k]
    est = pz.get("estatuas") or []
    if est:
        j, d = min(((j, math.hypot(x - q[0], y - q[1])) for j, q in enumerate(est)), key=lambda t: t[1])
        if d < 6:
            return 100 + j
    cand = [(codigos[k], math.hypot(x - lx, y - ly)) for k, (lx, ly) in lug.items() if k in codigos]
    return min(cand, key=lambda t: t[1])[0] if cand else 1
