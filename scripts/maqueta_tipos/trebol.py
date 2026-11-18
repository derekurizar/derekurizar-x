"""Pieza «trebol»: el nudo de El Trébol sobre su traza REAL de OpenStreetMap (capa `calles` del set de ciudad), con volumen:
las vías del nudo (clase autopista y primaria dentro de RADIO m del centro), sus cruces a desnivel y la altura de cada
tramo. OSM (calles.json) no trae qué vía es puente: la altura es ILUSTRATIVA y sale de la traza (no se afirma cuántos
tableros, niveles ni lazos tiene el nudo ni cuál es Pamplona, Bolívar o Roosevelt):

1. El CENTRO: cerca de `lugar` (hasta 900 m), el punto de las autopistas donde más vías con nombre distinto se juntan a
   menos de 90 m (ahí convergen las calzadas); luego el promedio de los puntos de autopista a menos de 140 m.
2. Las VÍAS: cada vía de la capa con algún punto a menos de RADIO m, recortada al círculo y remuestreada cada ≤ 6 m. Un
   LAZO es una vía corta que gira más de 200° (las hojas del trébol).
3. Los CRUCES: dos vías que se cortan lejos de sus extremos (no es una incorporación). Se colorean por BFS desde la vía más
   larga (abajo); la otra va ARRIBA. Si las dos ya están del mismo lado, sube la más corta.
4. La ALTURA de cada muestra: el máximo de H − pendiente·(d − meseta) desde cada cruce donde la vía va arriba (d por el
   grafo de las vías: sigue por las incorporaciones, así una rampa que se une a un tablero llega a su altura) y nunca más
   que pendiente·(d − meseta) desde cada cruce donde va abajo (el techo: la de abajo pasa a ras).
5. Los TABLEROS: los tramos con altura ≥ H_TABLERO (van sobre pilas); los PUENTES se numeran por su cruce (sin nombre).

Épocas (`epoca`): callecitas (sin nudo: callecitas genéricas por las calzadas que convergen, casas bajas y una nave
industrial genérica), obra (tierra removida, pilas a medio hacer, cimbras genéricas, tableros por tramos, obreros), 1959
(tableros nuevos sin los lazos: «construidos después», pocos carros) y hoy (asfalto con rayas, barandas, postes de luz).

Publica:
- `_caminos`: «<id>.carril-1…N» (cada vía del nudo, en el sentido de OSM; en 1959 sin los lazos; en callecitas, las
  callecitas). Van a ras del suelo del mundo: un `flujo` sobre ellos no sube a los tableros (lo dibuja la pieza con `carros`).
- `_lugares`: centro, puentes (el medio de los tableros) y fabrica (la nave industrial; en callecitas y obra se dibuja).
- `_cosas` (M3D15–M3D16, maqueta_escena): lo que la pieza dibuja con volumen EN SU ÉPOCA, con las medidas de trebol.js:
  callecitas → casas, nave, chimenea y gente; obra → pilas (a medio hacer), tableros por tramos, cimbras, rampas de tierra,
  montículos, obreros y la nave; 1959 y hoy → tableros, pilas, rampas, lazos (hoy), postes de luz y carros. El asfalto a ras
  no cuenta (no tiene volumen). Un `transformar` sobre la pieza añade lo suyo y marca con `hasta` lo viejo que hunde.
Elementos para «resaltar» con `elemento`: «<id>.puentes» → 1 (enciende todos los tableros, sin decir cuál es cuál);
«<id>.fabrica» → 2; otro lugar → 0 (el nudo entero)."""
import heapq
import math
import random

import maqueta_escena as ME
from maqueta_tipos import _mundo as MU

RADIO = 240.0             # m: el nudo que se dibuja (desde el centro)
H1, H2 = 7.2, 13.0        # m: un nivel y dos (cruce sobre un tablero)
PEND, MESETA = 0.06, 14.0  # rampa (6 %) y meseta a cada lado del cruce
H_TABLERO = 4.2           # m: desde aquí, el tramo va sobre pilas
PASO = 6.0
EPOCAS = ("callecitas", "obra", "1959", "hoy")
EL = {"puentes": 1, "fabrica": 2}


def _remuestrear(pts, paso=PASO):
    out = [tuple(pts[0])]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(math.ceil(L / paso)))
        for j in range(1, k + 1):
            out.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return out


def _recortar(pts, cx, cy, R):
    """Las partes de la polilínea dentro del círculo (cada una con ≥ 2 puntos)."""
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
    return [_remuestrear([p[0]] + p[::2][1:] + [p[-1]] if len(p) > 4 else p) for p in partes if len(p) >= 3]


def _largo(c):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(c, c[1:]))


def _giro(c):
    g = 0.0
    for a, b, d in zip(c, c[1:], c[2:]):
        a1, a2 = math.atan2(b[1] - a[1], b[0] - a[0]), math.atan2(d[1] - b[1], d[0] - b[0])
        g += (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
    return abs(math.degrees(g))


def _corte(p, q, r, s):
    d = (q[0] - p[0]) * (s[1] - r[1]) - (q[1] - p[1]) * (s[0] - r[0])
    if abs(d) < 1e-9:
        return None
    u = ((r[0] - p[0]) * (s[1] - r[1]) - (r[1] - p[1]) * (s[0] - r[0])) / d
    v = ((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0])) / d
    if 0 <= u <= 1 and 0 <= v <= 1:
        return u, v
    return None


def _centro(calles, lx, ly):
    nombradas = [q for q in calles if q["clase"] in ("autopista", "primaria") and q.get("nombre")
                 and min(math.hypot(a[0] - lx, a[1] - ly) for a in q["puntos"]) < 1100]
    mejor = None
    for q in calles:
        if q["clase"] != "autopista":
            continue
        for a in q["puntos"]:
            d0 = math.hypot(a[0] - lx, a[1] - ly)
            if d0 > 900:
                continue
            nom = {r["nombre"] for r in nombradas if min(math.hypot(b[0] - a[0], b[1] - a[1]) for b in r["puntos"]) < 90}
            k = (len(nom), -d0)
            if mejor is None or k > mejor[0]:
                mejor = (k, a)
    if mejor is None:
        return None
    bx, by = mejor[1]
    cerca = [a for q in calles if q["clase"] == "autopista" for a in q["puntos"] if math.hypot(a[0] - bx, a[1] - by) < 140]
    return sum(a[0] for a in cerca) / len(cerca), sum(a[1] for a in cerca) / len(cerca)


def _coser(ways):
    """Las vías de OSM [(clase, puntos)] cosidas extremo con extremo donde solo se juntan dos (un nodo de grado 2)."""
    key = lambda q: (round(q[0]), round(q[1]))
    grado = {}
    for _, c in ways:
        for q in (c[0], c[-1]):
            grado[key(q)] = grado.get(key(q), 0) + 1
    ini = {}
    for i, (_, c) in enumerate(ways):
        ini.setdefault(key(c[0]), []).append(i)
    usados, out = set(), []
    orden = sorted(range(len(ways)), key=lambda i: grado.get(key(ways[i][1][0]), 0) == 2)
    for i in orden:
        if i in usados:
            continue
        usados.add(i)
        cl, c = ways[i][0], [tuple(q) for q in ways[i][1]]
        while grado.get(key(c[-1]), 0) == 2:
            nx = [j for j in ini.get(key(c[-1]), []) if j not in usados]
            if not nx:
                break
            usados.add(nx[0])
            c += [tuple(q) for q in ways[nx[0]][1][1:]]
            if key(c[-1]) == key(c[0]):
                break
        out.append((cl, c))
    return out


def _alturas(vias, cruces):
    """La altura de cada muestra de cada vía (lista de listas), por el grafo de las vías."""
    nodos, idx = [], {}
    for w, c in enumerate(vias):
        for i, q in enumerate(c):
            idx[(w, i)] = len(nodos)
            nodos.append(q)
    ady = [[] for _ in nodos]

    def une(a, b):
        d = math.hypot(nodos[a][0] - nodos[b][0], nodos[a][1] - nodos[b][1])
        ady[a].append((b, d))
        ady[b].append((a, d))
    for w, c in enumerate(vias):
        for i in range(len(c) - 1):
            une(idx[(w, i)], idx[(w, i + 1)])
    # las incorporaciones: el extremo de una vía con la muestra más cercana de otra (≤ 4.5 m)
    for w, c in enumerate(vias):
        for i in (0, len(c) - 1):
            a = idx[(w, i)]
            mejor = None
            for w2, c2 in enumerate(vias):
                if w2 == w:
                    continue
                for j, q in enumerate(c2):
                    d = math.hypot(q[0] - c[i][0], q[1] - c[i][1])
                    if d < 4.5 and (mejor is None or d < mejor[0]):
                        mejor = (d, idx[(w2, j)])
            if mejor:
                une(a, mejor[1])

    def dist(desde):
        D = [math.inf] * len(nodos)
        D[desde] = 0.0
        h = [(0.0, desde)]
        while h:
            d, a = heapq.heappop(h)
            if d > D[a] or d > 260:
                continue
            for b, l in ady[a]:
                if d + l < D[b]:
                    D[b] = d + l
                    heapq.heappush(h, (d + l, b))
        return D
    alto = [0.0] * len(nodos)
    techo = [math.inf] * len(nodos)
    for cr in cruces:
        Ds = dist(idx[(cr["arriba"], cr["i_arriba"])])
        for n, d in enumerate(Ds):
            if d < math.inf:
                alto[n] = max(alto[n], cr["h"] - PEND * max(0.0, d - MESETA))
        Dt = dist(idx[(cr["abajo"], cr["i_abajo"])])
        for n, d in enumerate(Dt):
            if d < math.inf:
                techo[n] = min(techo[n], cr["h_abajo"] + PEND * max(0.0, d - MESETA))
    out = []
    for w, c in enumerate(vias):
        z = [max(0.0, min(alto[idx[(w, i)]], techo[idx[(w, i)]])) for i in range(len(c))]
        # suavizado (media de 3, dos pasadas): sin escalones entre muestras
        for _ in range(2):
            z = [z[0]] + [(z[i - 1] + z[i] + z[i + 1]) / 3 for i in range(1, len(z) - 1)] + [z[-1]] if len(z) > 2 else z
        out.append([round(v, 2) for v in z])
    return out


def _nudo(cosidas, cx, cy):
    # ---- las vías del nudo
    vias, clases = [], []
    for cl, pts in cosidas:
        if min(math.hypot(a[0] - cx, a[1] - cy) for a in pts) > RADIO:
            continue
        for c in _recortar(pts, cx, cy, RADIO):
            if _largo(c) >= 12:
                vias.append(c)
                clases.append(cl)
    lazo = [_largo(c) < 260 and _giro(c) > 200 for c in vias]
    largo = [_largo(c) for c in vias]

    # ---- los cruces a desnivel
    pares = []
    for a in range(len(vias)):
        for b in range(a + 1, len(vias)):
            ca, cb = vias[a], vias[b]
            for i in range(len(ca) - 1):
                for j in range(len(cb) - 1):
                    r = _corte(ca[i], ca[i + 1], cb[j], cb[j + 1])
                    if not r:
                        continue
                    x = ca[i][0] + (ca[i + 1][0] - ca[i][0]) * r[0]
                    y = ca[i][1] + (ca[i + 1][1] - ca[i][1]) * r[0]
                    # lejos de los extremos de las dos (si no, es una incorporación)
                    if min(math.hypot(x - e[0], y - e[1]) for e in (ca[0], ca[-1], cb[0], cb[-1])) < 10:
                        continue
                    if all(math.hypot(x - o[2], y - o[3]) > 6 for o in pares):
                        pares.append([a, b, x, y, i + (1 if r[0] > 0.5 else 0), j + (1 if r[1] > 0.5 else 0)])
    # colorear: BFS desde la vía más larga (abajo = 0)
    lado = {}
    vec = {}
    for a, b, *_ in pares:
        vec.setdefault(a, []).append(b)
        vec.setdefault(b, []).append(a)
    for raiz in sorted(vec, key=lambda w: -largo[w]):
        if raiz in lado:
            continue
        lado[raiz] = 0
        cola = [raiz]
        while cola:
            w = cola.pop(0)
            for v in vec[w]:
                if v not in lado:
                    lado[v] = 1 - lado[w]
                    cola.append(v)
    cruces = []
    for a, b, x, y, ia, ib in pares:
        if lado[a] != lado[b]:
            up, dn, iu, idn, h, hd = (a, b, ia, ib, H1, 0.0) if lado[a] == 1 else (b, a, ib, ia, H1, 0.0)
        else:                                       # del mismo lado: sube la más corta, un nivel más
            up, dn, iu, idn = (a, b, ia, ib) if largo[a] < largo[b] else (b, a, ib, ia)
            h, hd = (H2, H1) if lado[a] == 1 else (H1, 0.0)
        cruces.append({"arriba": up, "abajo": dn, "i_arriba": iu, "i_abajo": idn, "h": h, "h_abajo": hd, "x": x, "y": y})
    return vias, clases, lazo, largo, cruces


def resolver(p, X, que):
    S = X.S
    if S.escala != "ciudad":
        raise X.m3.Falla("M3D2", "%s: El Trébol sale de la traza de OpenStreetMap de un set de ciudad (este mundo es %s)" % (que, S.escala))
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    l = X.lugar(p["lugar"], que + " → lugar")
    lx, ly = l["x"] * um, l["y"] * um          # en metros
    capa = MU.capa(X, "calles", que)
    calles = capa["calles"]
    c0 = _centro(calles, lx, ly)
    if c0 is None:
        raise X.m3.Falla("M3D2", "%s: no hay autopistas a menos de 900 m de `lugar` en el set %s: esta pieza va sobre un nudo vial" % (que, S.id))
    cx, cy = c0
    epoca = p["epoca"]
    R = random.Random(int(p["semilla"]) * 7919 + 31)

    cosidas = _coser([(q["clase"], q["puntos"]) for q in calles if q["clase"] in ("autopista", "primaria")
                      and min(math.hypot(a[0] - cx, a[1] - cy) for a in q["puntos"]) < RADIO + 300])
    vias, clases, lazo, largo, cruces = _nudo(cosidas, cx, cy)
    if len(cruces) >= 2:                          # el centro de verdad: el medio de los cruces
        cx = sum(c["x"] for c in cruces) / len(cruces)
        cy = sum(c["y"] for c in cruces) / len(cruces)
        vias, clases, lazo, largo, cruces = _nudo(cosidas, cx, cy)
    if len(vias) < 2:
        raise X.m3.Falla("M3D2", "%s: el nudo cerca de `lugar` no tiene vías en el set %s" % (que, S.id))
    z = _alturas(vias, cruces)

    # ---- los puentes: un tablero por cruce (el tramo ≥ H_TABLERO alrededor del cruce sobre la vía de arriba)
    puentes = []
    for k, cr in enumerate(cruces):
        w, i = cr["arriba"], cr["i_arriba"]
        if z[w][i] < H_TABLERO:
            continue
        i0, i1 = i, i
        while i0 > 0 and z[w][i0 - 1] >= H_TABLERO:
            i0 -= 1
        while i1 < len(z[w]) - 1 and z[w][i1 + 1] >= H_TABLERO:
            i1 += 1
        if not any(pt[0] == w and not (i1 < pt[1] or i0 > pt[2]) for pt in puentes):
            puentes.append([w, i0, i1, round(cr["x"], 1), round(cr["y"], 1)])

    # ---- las callecitas (época callecitas): las calzadas que convergen, angostas (genéricas)
    callecitas = []
    for k, art in (capa.get("arterias") or {}).items():
        for c in _recortar(art["puntos"], cx, cy, RADIO + 40):
            if _largo(c) > 60:
                callecitas.append(c)
    if not callecitas:
        callecitas = [c for c, lz in zip(vias, lazo) if not lz][:4]
    # las direcciones de las callecitas desde el centro: la nave va en el hueco más grande entre dos
    angs = sorted({round(math.atan2(q[1] - cy, q[0] - cx), 2) for c in callecitas for q in (c[0], c[-1]) if math.hypot(q[0] - cx, q[1] - cy) > 80})
    if len(angs) >= 2:
        gaps = [((angs[(i + 1) % len(angs)] - angs[i]) % (2 * math.pi), angs[i]) for i in range(len(angs))]
        g, a0 = max(gaps)
        af = a0 + g / 2
    else:
        af = 0.6
    fx, fy = cx + math.cos(af) * 110, cy + math.sin(af) * 110

    def lejos_de(x, y, cs, d):
        return all(MU.dist_linea(x, y, c) > d for c in cs)
    # que la nave no pise una callecita: se acerca al centro o se aleja hasta que quepa
    for r_f in (110, 130, 150, 90, 170):
        fx, fy = cx + math.cos(af) * r_f, cy + math.sin(af) * r_f
        if lejos_de(fx, fy, callecitas, 34):
            break
    rumbo_f = af + math.pi / 2
    # casas bajas a los lados de las callecitas (genéricas), lejos de la nave
    casas = []
    for c in callecitas:
        L = _largo(c)
        s = 14.0
        while s < L - 8:
            # el punto a s y la dirección
            acc = 0.0
            for a, b in zip(c, c[1:]):
                lg = math.hypot(b[0] - a[0], b[1] - a[1])
                if acc + lg >= s:
                    u = (s - acc) / (lg or 1)
                    x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
                    dx, dy = (b[0] - a[0]) / (lg or 1), (b[1] - a[1]) / (lg or 1)
                    break
                acc += lg
            for sg in (1, -1):
                if R.random() < 0.3:
                    continue
                off = 9.5 + 3 * R.random()
                hx, hy = x - dy * off * sg, y + dx * off * sg
                if math.hypot(hx - cx, hy - cy) > RADIO + 30 or not lejos_de(hx, hy, callecitas, 7.5):
                    continue
                if math.hypot(hx - fx, hy - fy) < 42 or any(math.hypot(hx - o[0], hy - o[1]) < 10.5 for o in casas):
                    continue
                casas.append([round(hx, 1), round(hy, 1), round(math.atan2(-dx * sg, dy * sg), 3)])
            s += 11 + 7 * R.random()
    casas = casas[:70]

    # ---- los caminos que publica
    usar = [w for w in range(len(vias)) if not (epoca == "1959" and lazo[w])]
    caminos = {}
    fuente = callecitas if epoca == "callecitas" else [vias[w] for w in usar]
    for k, c in enumerate(fuente):
        cad, s = [], 0.0
        for i, q in enumerate(c):
            if i:
                s += math.hypot(q[0] - c[i - 1][0], q[1] - c[i - 1][1])
            cad.append([round(q[0] / um, 2), round(q[1] / um, 2), round(s / um, 2), 0])
        caminos["%s.carril-%d" % (p["id"], k + 1)] = cad

    # ---- los lugares
    if puentes:
        pxm = sum(q[3] for q in puentes) / len(puentes)
        pym = sum(q[4] for q in puentes) / len(puentes)
    else:
        pxm, pym = cx, cy
    lug = {"centro": ("El Trébol", cx, cy, 0.9), "puentes": ("Puentes", pxm + 0.5, pym + 0.5, 0.7),
           "fabrica": ("Fábrica", fx, fy, 0.5)}
    elementos = [[round(lug[k][1] / um, 2), round(lug[k][2] / um, 2), EL[k]] for k in EL]

    r = {"epoca": epoca, "fabrica": bool(p["fabrica"]), "obreros": int(p["obreros"]), "carros": int(p["carros"]),
         "semilla": int(p["semilla"]), "centro": [round(cx, 1), round(cy, 1)], "radio": RADIO,
         "vias": [[[round(q[0], 1), round(q[1], 1)] for q in c] for c in vias], "z": z, "clases": clases,
         "lazo": lazo, "puentes": puentes, "cruces": [[c["arriba"], c["abajo"], round(c["x"], 1), round(c["y"], 1)] for c in cruces],
         "callecitas": [[[round(q[0], 1), round(q[1], 1)] for q in c] for c in callecitas], "casas": casas,
         "nave": [round(fx, 1), round(fy, 1), round(rumbo_f, 3)], "elementos": elementos}
    usa = []
    if epoca == "callecitas" and casas:
        usa.append("casa")
    if int(p["obreros"]) and epoca == "obra":
        usa.append("persona")
    if int(p["carros"]) and epoca in ("1959", "hoy"):
        usa.append("carro")
    r["usa"] = usa
    r["_caminos"] = caminos
    r["_lugares"] = {k: {"nombre": v[0], "x": round(v[1] / um, 2), "y": round(v[2] / um, 2), "peso": v[3]} for k, v in lug.items()}
    r["_cosas"] = _cosas(r, um)
    return r


def ancho_via(c, lazo, clase):
    """El ancho (m) de una vía, como trebol.js."""
    L = _largo(c)
    return 6.0 if lazo else 8.5 if clase == "primaria" else 10.5 if L > 300 else 8.0 if L > 160 else 6.8


def _cosas(r, um):
    """Las partes con volumen de la época (en unidades de la escena; medidas en metros, como trebol.js)."""
    ep, co = r["epoca"], []
    CALLE, OBRA, N59, HOY = ep == "callecitas", ep == "obra", ep == "1959", ep == "hoy"
    P = lambda x, y: (x / um, y / um)
    LEV, HT = 0.32, 4.2
    gente = int(r["obreros"])
    if r["fabrica"] and (CALLE or OBRA):
        fx, fy, ang = r["nave"]
        ca, sa = math.cos(ang), math.sin(ang)
        co.append(ME.cosas_pieza("nave industrial", *P(fx, fy), 56.4, 24.4, 11.0, ca, sa, contiene=["techo de dientes de sierra"]))
        chx, chy = fx + (-28 + 6) * ca - (12 + 5) * sa, fy + (-28 + 6) * sa + (12 + 5) * ca
        co.append(ME.cosas_pieza("chimenea", *P(chx, chy), 6.0, 6.4, 24.8, ca, sa, animado=True))
        co.append(ME.cosas_pieza("cajas y tambos", *P(fx + 31 * ca + 5 * sa, fy + 31 * sa - 5 * ca), 1.6, 13.0, 2.0, ca, sa))
    if CALLE:
        for i, (x, y, a) in enumerate(r["casas"]):
            co.append(ME.cosas_pieza("casa", *P(x, y), 8.0 * 1.1, 7.0 * 1.1, 5.4 * 1.1, math.cos(a), math.sin(a), casa=i))
        cs = r["callecitas"]
        for i in range(min(12, gente)):
            c = cs[i % len(cs)] if cs else None
            if not c:
                break
            q = c[int(len(c) * (0.2 + 0.6 * ((i * 0.618) % 1)))]
            co.append(ME.cosas_pieza("gente", *P(q[0], q[1]), 0.5 * 1.6, 0.5 * 1.6, 1.75 * 1.6, gente=True, animado=True, persona=i))
        return co
    vias, z, lazo, clases = r["vias"], r["z"], r["lazo"], r["clases"]
    usar = [not (N59 and lazo[w]) for w in range(len(vias))]
    ancho = [ancho_via(c, lazo[w], clases[w]) for w, c in enumerate(vias)]
    pu = {q[0]: q for q in r["puentes"]}

    def sin_tablero(w, i):   # en obra, la mitad lejana de cada puente aún sin tablero (trebol.js lo sortea por puente)
        q = pu.get(w)
        return OBRA and q is not None and q[1] <= i <= q[2] and i - q[1] > (q[2] - q[1]) * 0.55

    def trozos(w, f, paso=24.0):
        """Los trozos (≤ paso m) de la vía w donde f(i) es cierto → [(i0, i1)]."""
        c, out, i0, acc = vias[w], [], None, 0.0
        for i in range(len(c)):
            if f(i):
                if i0 is None:
                    i0, acc = i, 0.0
                elif acc >= paso:
                    out.append((i0, i))
                    i0, acc = i, 0.0
                if i + 1 < len(c):
                    acc += math.hypot(c[i + 1][0] - c[i][0], c[i + 1][1] - c[i][1])
            elif i0 is not None:
                if i - 1 > i0:
                    out.append((i0, i - 1))
                i0 = None
        if i0 is not None and len(c) - 1 > i0:
            out.append((i0, len(c) - 1))
        return out

    def trozo(clave, w, i0, i1, extra_h, **ex):
        c = vias[w]
        a, b = c[i0], c[i1]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        h = max(z[w][i0:i1 + 1]) + LEV + extra_h
        co.append(ME.cosas_pieza(clave, *P((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), L + 2, ancho[w] + 0.6, h, (b[0] - a[0]) / L, (b[1] - a[1]) / L, **ex))

    pret = 0.0 if OBRA else 0.8 if N59 else 1.35
    for w, c in enumerate(vias):
        if not usar[w]:
            continue
        for i0, i1 in trozos(w, lambda i: z[w][i] >= HT and not sin_tablero(w, i)):
            trozo("lazo" if lazo[w] else "tablero", w, i0, i1, pret, contiene=["viga cabezal"] if not OBRA else [])
        for i0, i1 in trozos(w, lambda i: 0.3 < z[w][i] < HT):
            trozo("rampa de tierra" if OBRA else "lazo" if lazo[w] else "rampa", w, i0, i1, pret)
        if OBRA:
            for i0, i1 in trozos(w, lambda i: sin_tablero(w, i)):
                trozo("cimbra", w, i0, i1, -0.2)
    # las pilas: cada ≈ 22 m bajo los tableros (no sobre el asfalto de otra vía)
    pilas = []
    for w, c in enumerate(vias):
        if not usar[w]:
            continue
        s, sig = 0.0, 8.0
        for i, q in enumerate(c):
            if i:
                s += math.hypot(q[0] - c[i - 1][0], q[1] - c[i - 1][1])
            if s < sig or z[w][i] < HT:
                continue
            sig = s + 22
            if any(w2 != w and usar[w2] and any(z[w2][j] < 2 and math.hypot(c2[j][0] - q[0], c2[j][1] - q[1]) < ancho[w2] / 2 + 3 for j in range(len(c2)))
                   for w2, c2 in enumerate(vias)):
                continue
            a, b = c[max(0, i - 1)], c[min(len(c) - 1, i + 1)]
            L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            st = sin_tablero(w, i)
            top = z[w][i] + LEV - 1.3
            pilas.append((q[0], q[1], (b[0] - a[0]) / L, (b[1] - a[1]) / L))
            co.append(ME.cosas_pieza("pila a medio hacer" if st else "pila", *P(q[0], q[1]), 2.0, min(ancho[w] * 0.6, 5.2) + 1.9,
                                     top * 0.65 + 1.6 if st else top, (b[0] - a[0]) / L, (b[1] - a[1]) / L, contiene=["varillas"] if st else []))
    if OBRA:
        for k, (x, y, dx, dy) in enumerate(pilas):
            nx, ny = -dy, dx
            if k % 2 == 0:
                co.append(ME.cosas_pieza("montículo", *P(x + 9 * nx, y + 9 * ny), 8.0, 8.0, 2.4))
            else:
                co.append(ME.cosas_pieza("tablones", *P(x - 7 * nx, y - 7 * ny), 4.4, 1.0, 0.8, dx, dy))
        for i in range(min(12, gente) if pilas else 0):
            x, y, dx, dy = pilas[(i * 7) % len(pilas)]
            co.append(ME.cosas_pieza("obrero", *P(x - dy * 5, y + dx * 5), 0.8, 0.8, 1.75 * 1.6, gente=True, animado=True, persona=i))
        return co
    # los postes de luz (no en los lazos) y los carros (las vías largas, primero las que tienen puente)
    ejes = []
    for w, c in enumerate(vias):
        if not usar[w] or lazo[w]:
            continue
        L = _largo(c)
        s, sl = 0.0, 15.0
        for i, q in enumerate(c):
            if i:
                s += math.hypot(q[0] - c[i - 1][0], q[1] - c[i - 1][1])
            if s >= sl:
                sl = s + 62
                co.append(ME.cosas_pieza("poste de luz", *P(q[0], q[1]), 0.6, 3.6, z[w][i] + LEV + (8 if N59 else 10)))
        if L > 70:
            ejes.append(w)
    ejes.sort(key=lambda w: (-(w in pu), -_largo(vias[w])))
    NC = max(0, min(12, int(r["carros"]))) if ejes else 0
    for i in range(NC):
        w = ejes[i % len(ejes)]
        c = vias[w]
        n_en = (NC - 1 - i % len(ejes)) // len(ejes) + 1
        j = int((len(c) - 1) * ((i // len(ejes)) + 0.5) / n_en)
        a, b = c[max(0, j - 1)], c[min(len(c) - 1, j + 1)]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        co.append(ME.cosas_pieza("carro", *P(c[j][0], c[j][1]), 4.5, 1.8, z[w][j] + LEV + 1.5, (b[0] - a[0]) / L, (b[1] - a[1]) / L, animado=True))
    return co


def centro(pz, G):
    return pz["centro"][0], pz["centro"][1]


def tramos(pz):
    return [[(q[0], q[1], False) for q in c] for c in pz["vias"]]


def elemento(pz, x, y):
    """El lugar exacto de la pieza que se nombra: puentes 1, fábrica 2; otro lugar: el nudo entero 0."""
    for ex, ey, i in pz.get("elementos", []):
        if math.hypot(ex - x, ey - y) < 1.5:
            return i
    return 0
