"""Pieza «avenidareforma»: la Avenida La Reforma de hoy sobre su trazo de OpenStreetMap (capa `calles` del set de ciudad:
las vías «Avenida Reforma» y «Carril Auxiliar Avenida Reforma»), en todo su largo dentro de la caja.

Del set salen cuatro cadenas (cosidas extremo con extremo): la vía principal hacia el norte (la del este) y hacia el sur
(la del oeste), y los dos carriles auxiliares. Entre las dos principales va el ARRIATE (el camellón), muestreado por y cada
`PASO` m; entre principal y auxiliar, el separador verde. La plaza del Obelisco va en el centro del anillo «Plaza Obelisco»
del set (si no está, 60 m al sur del extremo). Los CRUCES son las calles del set que atraviesan el eje del arriate: ahí el
arriate se abre, van los pasos de cebra y los semáforos (ubicación genérica: la fuente no dice dónde están).

Todo lo que se planta (árboles, bancas, farolas, monumentos, el depósito de agua) lo decide aquí la `semilla`, una vez,
y viaja al motor ya colocado: motor.js solo dibuja.

Publica:
- `_caminos`: «<id>.norte-1…3» (principal hacia el norte; el 1 junto al arriate), «<id>.sur-1…3» (hacia el sur) y
  «<id>.aux-norte», «<id>.aux-sur» (los auxiliares), en el sentido de la marcha.
- `_lugares`: obelisco, arriate (el medio del camellón), jacarandas (donde se juntan), semaforos (el cruce del medio),
  norte y sur (los extremos del eje).
Elementos para «resaltar» con `elemento` (el lugar exacto de la pieza): 0 la avenida entera (cualquier otro lugar),
1 jacarandas, 2 obelisco, 3 semáforos, 4 arriate."""
import math
import random

import maqueta_escena as ME
from maqueta_tipos import _mundo as MU
from maqueta_tipos.esquema import cadena, desplazar

PASO = 8.0                    # m entre secciones del arriate
ANCHO_VIA, ANCHO_AUX = 10.5, 6.5
CARRIL = 3.5
NOMBRE, NOMBRE_AUX = "Avenida Reforma", "Carril Auxiliar Avenida Reforma"
EL = {"jacarandas": 1, "obelisco": 2, "semaforos": 3, "arriate": 4}


def _largo(c):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(c, c[1:]))


def _cadenas(segs):
    """Segmentos [[x, y], …] → cadenas cosidas por sus extremos (en el sentido de OSM), de la más larga a la más corta."""
    segs = [[tuple(q) for q in s] for s in segs if len(s) >= 2]
    ini, fines = {}, {s[-1] for s in segs}
    for i, s in enumerate(segs):
        ini.setdefault(s[0], []).append(i)
    usados, out = set(), []
    for i in [i for i, s in enumerate(segs) if s[0] not in fines] + list(range(len(segs))):
        if i in usados:
            continue
        usados.add(i)
        c = list(segs[i])
        while True:
            nx = [j for j in ini.get(c[-1], []) if j not in usados]
            if not nx:
                break
            usados.add(nx[0])
            c += segs[nx[0]][1:]
        out.append(c)
    return sorted(out, key=_largo, reverse=True)


def _x_en(c, y):
    """x de la cadena (monótona en y) a la altura y; None fuera de su rango."""
    for a, b in zip(c, c[1:]):
        if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
            u = (y - a[1]) / (b[1] - a[1])
            return a[0] + (b[0] - a[0]) * u
    return None


def _pend(c, y):
    """dx/dy de la cadena cerca de y (para pasar anchos perpendiculares a anchos en x)."""
    a, b = _x_en(c, y - 6), _x_en(c, y + 6)
    if a is None or b is None:
        return 0.0
    return (b - a) / 12.0


def _cruce(p, q, r, s):
    """Intersección de los segmentos pq y rs → (x, y) o None."""
    d = (q[0] - p[0]) * (s[1] - r[1]) - (q[1] - p[1]) * (s[0] - r[0])
    if abs(d) < 1e-9:
        return None
    u = ((r[0] - p[0]) * (s[1] - r[1]) - (r[1] - p[1]) * (s[0] - r[0])) / d
    v = ((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0])) / d
    if 0 <= u <= 1 and 0 <= v <= 1:
        return p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u
    return None


def _monotona(c):
    return all((b[1] - a[1]) * (c[-1][1] - c[0][1]) >= 0 for a, b in zip(c, c[1:]))


def resolver(p, X, que):
    S = X.S
    if S.escala != "ciudad":
        raise X.m3.Falla("M3D2", "%s: la avenida La Reforma sale del trazo de OpenStreetMap de un set de ciudad (este mundo es %s)" % (que, S.escala))
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    calles = MU.capa(X, "calles", que)["calles"]
    pr = [q["puntos"] for q in calles if q.get("nombre") == NOMBRE and q["clase"] == "primaria"]
    au = [q["puntos"] for q in calles if q.get("nombre") == NOMBRE_AUX or (q.get("nombre") == NOMBRE and q["clase"] != "primaria")]
    cp = [c for c in _cadenas(pr) if _largo(c) > 400 and _monotona(c)][:2]
    if len(cp) < 2:
        raise X.m3.Falla("M3D2", "%s: el set %s no trae las dos vías de «%s» (calles.json): esta pieza solo sirve donde está la avenida" % (que, S.id, NOMBRE))
    # la que va al norte (y crece) es la del este; la otra, la del oeste
    pn, ps = (cp[0], cp[1]) if cp[0][-1][1] > cp[0][0][1] else (cp[1], cp[0])
    ca = [c for c in _cadenas(au) if _largo(c) > 300 and _monotona(c)][:2] if p["auxiliares"] else []
    an = next((c for c in ca if c[-1][1] > c[0][1]), None)
    as_ = next((c for c in ca if c[-1][1] < c[0][1]), None)

    # ---- las secciones del arriate: entre las dos principales, en el rango de y que comparten
    ylo = max(min(q[1] for q in pn), min(q[1] for q in ps)) + 2
    yhi = min(max(q[1] for q in pn), max(q[1] for q in ps)) - 2
    n = max(2, int((yhi - ylo) / PASO))
    hv, ha = ANCHO_VIA / 2, ANCHO_AUX / 2
    sec, eje = [], []
    for i in range(n + 1):
        y = ylo + (yhi - ylo) * i / n
        xw, xe = _x_en(ps, y), _x_en(pn, y)
        if xw is None or xe is None:
            continue
        fw, fe = math.sqrt(1 + _pend(ps, y) ** 2), math.sqrt(1 + _pend(pn, y) ** 2)
        e3, e4 = xw + hv * fw, xe - hv * fe
        e2, e5 = xw - hv * fw, xe + hv * fe
        e1 = e6 = None
        if as_ is not None:
            xa = _x_en(as_, y)
            if xa is not None and xa < xw:
                e1 = xa + ha * math.sqrt(1 + _pend(as_, y) ** 2)
        if an is not None:
            xa = _x_en(an, y)
            if xa is not None and xa > xe:
                e6 = xa - ha * math.sqrt(1 + _pend(an, y) ** 2)
        sec.append([round(y, 1), round(e1, 2) if e1 is not None and e2 - e1 > 0.8 else None, round(e2, 2), round(e3, 2),
                    round(e4, 2), round(e5, 2), round(e6, 2) if e6 is not None and e6 - e5 > 0.8 else None])
        eje.append([round((e3 + e4) / 2, 2), round(y, 2)])
    if len(eje) < 10:
        raise X.m3.Falla("M3D2", "%s: las dos vías de la avenida no corren juntas en el set %s" % (que, S.id))
    eje_c = cadena(eje)
    L = eje_c[-1][2]

    # ---- los cruces: las calles del set que atraviesan el eje (ahí se abre el arriate)
    cruces = []
    for q in calles:
        nm = q.get("nombre") or ""
        if nm in (NOMBRE, NOMBRE_AUX) or nm.startswith("Plaza Obelisco") or q["clase"] in ("peatonal",):
            continue
        pts = q["puntos"]
        for a, b in zip(pts, pts[1:]):
            for k in range(len(eje) - 1):
                c = _cruce(a, b, eje[k], eje[k + 1])
                if c:
                    s = eje_c[k][2] + math.hypot(c[0] - eje[k][0], c[1] - eje[k][1])
                    ang = math.atan2(b[1] - a[1], b[0] - a[0])
                    cruces.append([s, c[0], c[1], ang, pts])
    cruces.sort()
    sel = []
    for c in cruces:
        if 40 < c[0] < L - 40 and all(abs(c[0] - o[0]) > 70 for o in sel):
            sel.append(c)
    # cada cruce: [s sobre el eje, x, y, ángulo de la calle que cruza]
    cx_out = []
    for s, x, y, ang, pts in sel:
        cx_out.append([round(s, 1), round(x, 2), round(y, 2), round(ang, 4)])
    sem = bool(p["semaforos"])

    # ---- la plaza del Obelisco: el anillo «Plaza Obelisco» del set, cerca del extremo sur
    sx, sy = eje[0]
    anillo = [pt for q in calles if (q.get("nombre") or "").startswith("Plaza Obelisco") for pt in q["puntos"] if math.hypot(pt[0] - sx, pt[1] - sy) < 260]
    via_plaza = [q["puntos"] for q in calles if (q.get("nombre") or "").startswith("Plaza Obelisco")
                 and any(math.hypot(pt[0] - sx, pt[1] - sy) < 260 for pt in q["puntos"])]
    if len(anillo) >= 6:
        xs, ys = [q[0] for q in anillo], [q[1] for q in anillo]
        ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        r_pl = max(16.0, min(36.0, min(max(xs) - min(xs), max(ys) - min(ys)) / 2 - 8))
    else:
        d = eje_c[min(len(eje_c) - 1, 6)]
        ux, uy = sx - d[0], sy - d[1]
        nn = math.hypot(ux, uy) or 1
        ox, oy, r_pl = sx + ux / nn * 60, sy + uy / nn * 60, 24.0
        via_plaza = []

    # ---- lo que se planta en el arriate y en los separadores (la semilla, una vez)
    R = random.Random(int(p["semilla"]) * 7919 + 17)
    denso = p["arboles"] == "denso"
    fj = float(p["jacarandas"])

    def seccion_en(s):
        k = max(0, min(len(eje_c) - 2, int(s / (L / (len(eje_c) - 1)))))
        while k < len(eje_c) - 2 and eje_c[k + 1][2] < s:
            k += 1
        while k > 0 and eje_c[k][2] > s:
            k -= 1
        a, b = sec[k], sec[k + 1]
        u = (s - eje_c[k][2]) / ((eje_c[k + 1][2] - eje_c[k][2]) or 1)
        return [None if a[j] is None or b[j] is None else a[j] + (b[j] - a[j]) * u for j in range(7)]

    def libre(s, holgura=9.0):
        return all(abs(s - c[0]) > holgura for c in cx_out) and 6 < s < L - 6

    arboles = []           # [x, y, especie (0 frondoso · 1 ciprés · 2 jacaranda · 3 manzanote), tamaño]
    paso_a = 9.0 if denso else 16.0
    s = 4.0
    while s < L - 4:
        if libre(s, 8):
            q = seccion_en(s)
            w = q[4] - q[3]
            filas = [0.24, 0.76] if w > 11 else ([0.2, 0.8] if w > 6.5 else [])
            for f in filas:
                if R.random() < (0.12 if denso else 0.3):
                    continue
                x = q[3] + w * f + (R.random() - 0.5) * 1.6
                y = q[0] + (R.random() - 0.5) * 3
                r = R.random()
                esp = 2 if r < fj else (1 if r < fj + 0.14 else (3 if r < fj + 0.24 else 0))
                arboles.append([round(x, 2), round(y, 2), esp, round(0.8 + 0.45 * R.random() + (0.35 if esp == 1 else 0), 2)])
        s += paso_a * (0.8 + 0.4 * R.random())
    # los separadores entre principal y auxiliar
    s = 6.0
    while s < L - 6:
        if libre(s, 9):
            q = seccion_en(s)
            for a, b in ((q[1], q[2]), (q[5], q[6])):
                if a is not None and b is not None and b - a > 2.6 and R.random() < (0.85 if denso else 0.55):
                    r = R.random()
                    esp = 2 if r < fj * 0.6 else 0
                    arboles.append([round((a + b) / 2, 2), round(q[0] + (R.random() - 0.5) * 2, 2), esp, round(0.7 + 0.35 * R.random(), 2)])
        s += (15.0 if denso else 24.0) * (0.85 + 0.3 * R.random())

    # bancas a los lados del camino, farolas, monumentos y el depósito de agua (todo genérico)
    bancas, farolas, monumentos = [], [], []
    s = 20.0
    while s < L - 20:
        if libre(s, 12):
            bancas.append([round(s, 1), 1 if R.random() < 0.5 else -1])
        s += 34 + 18 * R.random()
    s = 12.0
    while s < L - 12:
        if libre(s, 6):
            farolas.append(round(s, 1))
        s += 38
    nmon = max(3, int(L / 280))
    for k in range(nmon):
        sm = L * (k + 0.5) / nmon + (R.random() - 0.5) * 40
        if not libre(sm, 20):
            sm += 30
        monumentos.append([round(sm, 1), R.randrange(3)])
    s_dep = L * 0.42
    while not libre(s_dep, 22):
        s_dep += 15
    # los árboles no van encima de un monumento, del depósito ni de la gente del camino central (±1.6 m)
    def pos_s(sv):
        q = seccion_en(sv)
        return (q[3] + q[4]) / 2, q[0]
    ocupado = [pos_s(m[0]) + (7.5,) for m in monumentos] + [pos_s(s_dep) + (9.0,)]
    arboles = [a for a in arboles if all(math.hypot(a[0] - ox_, a[1] - oy_) > r_ for ox_, oy_, r_ in ocupado)]
    arboles = [a for a in arboles if math.hypot(a[0] - ox, a[1] - oy) > r_pl + 14]

    # ---- los caminos que publica
    caminos = {}
    for nombre, c in (("norte", pn), ("sur", ps)):
        base = [[float(q[0]) / um, float(q[1]) / um] for q in c]
        for k in (1, 2, 3):
            caminos["%s.%s-%d" % (p["id"], nombre, k)] = cadena(desplazar(base, CARRIL * (2 - k) / um))
    if an is not None:
        caminos["%s.aux-norte" % p["id"]] = cadena([[q[0] / um, q[1] / um] for q in an])
    if as_ is not None:
        caminos["%s.aux-sur" % p["id"]] = cadena([[q[0] / um, q[1] / um] for q in as_])

    # ---- los lugares que publica
    jac = sorted([a for a in arboles if a[2] == 2], key=lambda a: a[1])
    jl = jac[len(jac) // 2] if jac else None
    if cx_out:
        cm = min(cx_out, key=lambda c: abs(c[0] - L / 2))
    mx, my = pos_s(L / 2)
    lug = {
        "obelisco": ("Obelisco", ox, oy, 0.9),
        "arriate": ("Arriate central", mx, my, 0.6),
        "norte": ("Extremo norte", eje[-1][0], eje[-1][1], 0.5),
        "sur": ("Extremo sur", eje[0][0], eje[0][1], 0.5),
    }
    if jl:
        lug["jacarandas"] = ("Jacarandas", jl[0], jl[1], 0.6)
    if cx_out and sem:
        lug["semaforos"] = ("Semáforos", cm[1], cm[2], 0.5)
    elementos = [[round(lug[k][1], 2), round(lug[k][2], 2), EL[k]] for k in EL if k in lug]

    r = {"semilla": int(p["semilla"]), "arboles_denso": denso, "jacaranda_flor": bool(p["jacaranda_flor"]),
         "semaforos": sem, "obelisco": bool(p["obelisco"]), "auxiliares": bool(p["auxiliares"]),
         "personas": int(p["personas"]), "gente_tamano": float(p["gente_tamano"]),
         "vias": {"norte": [[round(q[0], 1), round(q[1], 1)] for q in pn], "sur": [[round(q[0], 1), round(q[1], 1)] for q in ps],
                  "aux_norte": [[round(q[0], 1), round(q[1], 1)] for q in an] if an else None,
                  "aux_sur": [[round(q[0], 1), round(q[1], 1)] for q in as_] if as_ else None},
         "via_plaza": [[[round(u, 1), round(v, 1)] for u, v in c] for c in via_plaza],
         "ancho_via": ANCHO_VIA, "ancho_aux": ANCHO_AUX, "carril": CARRIL,
         "sec": sec, "eje": eje, "largo_m": round(L * um, 1),
         "cruces": cx_out, "plaza": [round(ox, 2), round(oy, 2), round(r_pl, 2)],
         "arbolado": arboles, "bancas": bancas, "farolas": farolas, "monumentos": monumentos, "deposito": round(s_dep, 1),
         "elementos": elementos,
         "usa": ["persona"] if int(p["personas"]) else []}
    # LAS PARTES CON VOLUMEN (`_cosas`, las mide maqueta_escena: M3D15–M3D16), con las medidas de avenidareforma.js
    co = ME.agrupar(arboles, 40 / um, lambda a: "jacaranda" if a[2] == 2 else "arboleda", 8.0, 5.0, um)
    if p["obelisco"]:
        co.append(ME.cosas_pieza("obelisco", ox, oy, 4, 4, 23))
        co.append(ME.cosas_pieza("plaza del obelisco", ox, oy, 2 * r_pl * um, 2 * r_pl * um, 3.0))
    for sm, _ in monumentos:
        x, y = pos_s(sm)
        co.append(ME.cosas_pieza("monumento", x, y, 4, 4, 6))
    x, y = pos_s(s_dep)
    co.append(ME.cosas_pieza("depósito de agua", x, y, 14, 14, 6))
    r["_cosas"] = co
    r["_caminos"] = caminos
    r["_lugares"] = {k: {"nombre": v[0], "x": round(v[1], 2), "y": round(v[2], 2), "peso": v[3]} for k, v in lug.items()}
    return r


def tramos(pz):
    return [[(x, y, False) for x, y in pz["eje"]]]


def centro(pz, G):
    eje = pz["eje"]
    return eje[len(eje) // 2][0], eje[len(eje) // 2][1]


def elemento(pz, x, y):
    """El lugar exacto de la pieza que se nombra: jacarandas 1, obelisco 2, semáforos 3, arriate 4; otro lugar: la avenida 0."""
    for ex, ey, i in pz.get("elementos", []):
        if math.hypot(ex - x, ey - y) < 1.5:
            return i
    return 0
