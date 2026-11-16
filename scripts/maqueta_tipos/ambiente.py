"""Pieza «ambiente»: viste un mundo de cerca (esquema o ciudad) con lo que hay en un lugar así, sin pisar sus calles,
caminos, ríos, edificios, el mar ni las huellas que lleguen en `evitar` ([[x, y, radio_m], …]) o las de las piezas con
polígono ya resueltas (un cafetal). Todo se coloca AQUÍ, una vez y determinista por `semilla` (los gates y el motor ven
lo mismo); motor.js solo lo dibuja. Tope: 600 elementos (cada poste de una cerca o de un tendido cuenta).

`ambiente` (`tipo` es el de la pieza): campo (árboles sueltos y en grupos, arbustos, matorrales, piedras, cercas de postes con alambre junto a caminos y
lindes, postes de luz con cable junto al camino principal, ranchos lejanos, manchas de flores y pasto alto) · ciudad
(farolas, árboles de alcorque, bancas, basureros, postes con cables, semáforos en los cruces de calles mayores, paradas)
· costa (palmeras, rocas en la orilla, botes varados en la arena, postes con cable y bolardos en la costanera) · plaza
(una fuente al centro de la plaza, jardineras, bancas y farolas; alrededor, lo de la ciudad a media densidad).

Resuelta: {ambiente, semilla, centro: [x, y], radio_m, items: {clase: [x, y, rumbo_rad, escala, …]}, lineas: {cerca:
[[x0, y0, …]], cable: [[x0, y0, …]], cable_bajo: [[…]]}, fuente: [x, y, r] | None, n}. Las clases de `items`: copa, pino,
arbusto, matorral, piedra, rancho, flores, pasto, farola, alcorque, banca, basurero, semaforo, parada, palmera, roca,
bote, bolardo, jardinera, poste (de luz, el de los tendidos), postec (de cerca)."""
import math

from maqueta_tipos import _mundo as MU

TIPOS = ("campo", "ciudad", "costa", "plaza")
TOPE = 600
ANCHOS = {"autopista": 20.0, "primaria": 14.0, "secundaria": 11.0, "terciaria": 9.0, "residencial": 7.0, "peatonal": 4.0}
RANGO = {"autopista": 0, "primaria": 1, "secundaria": 2, "terciaria": 3, "residencial": 4, "peatonal": 5}
CEL = 24.0


class Azar:
    def __init__(self, semilla):
        self.s = (int(semilla) * 2654435761 + 97531) & 0xFFFFFFFF or 1

    def u(self):
        x = self.s
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.s = x & 0xFFFFFFFF
        return self.s / 4294967296.0

    def entre(self, a, b):
        return a + (b - a) * self.u()


def _largo(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _en(pts, s):
    """El punto a `s` metros del inicio de la polilínea y su dirección unitaria."""
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L <= 1e-9:
            continue
        if s <= L:
            dx, dy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            return a[0] + dx * s, a[1] + dy * s, dx, dy
        s -= L
    a, b = pts[-2], pts[-1]
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    return b[0], b[1], (b[0] - a[0]) / L, (b[1] - a[1]) / L


class Lienzo:
    """Lo que no se puede pisar (en una rejilla de CEL m) y lo ya puesto."""

    def __init__(self, cx, cy, R, caja):
        self.cx, self.cy, self.R, self.caja = cx, cy, R, caja
        self.seg, self.cajas, self.circ, self.puestos = {}, {}, [], {}
        self.agua, self.pav = [], []

    def _celdas(self, x0, y0, x1, y1):
        for i in range(int(math.floor(x0 / CEL)), int(math.floor(x1 / CEL)) + 1):
            for j in range(int(math.floor(y0 / CEL)), int(math.floor(y1 / CEL)) + 1):
                yield (i, j)

    def cerca_del(self, x0, y0, x1, y1, pad=0.0):
        cx, cy, R = self.cx, self.cy, self.R + pad
        return not (max(x0, x1) < cx - R or min(x0, x1) > cx + R or max(y0, y1) < cy - R or min(y0, y1) > cy + R)

    def linea(self, pts, hw, clave=None):
        for a, b in zip(pts, pts[1:]):
            if not self.cerca_del(a[0], a[1], b[0], b[1], hw + 40):
                continue
            o = (a[0], a[1], b[0], b[1], hw, clave)
            for c in self._celdas(min(a[0], b[0]) - hw, min(a[1], b[1]) - hw, max(a[0], b[0]) + hw, max(a[1], b[1]) + hw):
                self.seg.setdefault(c, []).append(o)

    def rect(self, x0, y0, x1, y1):
        if not self.cerca_del(x0, y0, x1, y1, 40):
            return
        o = (x0, y0, x1, y1)
        for c in self._celdas(x0, y0, x1, y1):
            self.cajas.setdefault(c, []).append(o)

    def dist_lineas(self, x, y, salvo=None):
        """La holgura a la calle más cercana (distancia − medio ancho)."""
        m = 1e9
        for (ax, ay, bx, by, hw, clave) in self.seg.get((int(math.floor(x / CEL)), int(math.floor(y / CEL))), ()):
            if salvo is not None and clave == salvo:
                continue
            dx, dy = bx - ax, by - ay
            h = min(1, max(0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1e-9)))
            m = min(m, math.hypot(x - ax - dx * h, y - ay - dy * h) - hw)
        return m

    def libre(self, x, y, r, salvo=None, pavimento_ok=False, agua_ok=False, dentro_r=True):
        x0, y0, x1, y1 = self.caja
        if not (x0 + 4 <= x <= x1 - 4 and y0 + 4 <= y <= y1 - 4):
            return False
        if dentro_r and math.hypot(x - self.cx, y - self.cy) > self.R:
            return False
        # la rejilla: las líneas que pasan a menos de una celda; un radio mayor que la celda se revisa en las vecinas
        for dx in ((0,) if r < CEL / 2 else (-1, 0, 1)):
            for dy in ((0,) if r < CEL / 2 else (-1, 0, 1)):
                if self.dist_lineas(x + dx * CEL * 0.5, y + dy * CEL * 0.5, salvo) < r - (abs(dx) + abs(dy)) * CEL * 0.5:
                    return False
        if self.dist_lineas(x, y, salvo) < r:
            return False
        for (ax, ay, bx, by) in self.cajas.get((int(math.floor(x / CEL)), int(math.floor(y / CEL))), ()):
            if ax - r <= x <= bx + r and ay - r <= y <= by + r:
                return False
        for (cx, cy, cr) in self.circ:
            if math.hypot(x - cx, y - cy) < cr + r:
                return False
        if not agua_ok and any(MU.dentro_pol(x, y, p) for p in self.agua):
            return False
        if not pavimento_ok and any(MU.dentro_pol(x, y, p) for p in self.pav):
            return False
        for c in self._celdas(x - r - 6, y - r - 6, x + r + 6, y + r + 6):
            for (px, py, pr) in self.puestos.get(c, ()):
                if math.hypot(x - px, y - py) < r + pr:
                    return False
        return True

    def poner(self, x, y, r):
        self.puestos.setdefault((int(math.floor(x / CEL)), int(math.floor(y / CEL))), []).append((x, y, r))


def resolver(p, X, que):
    tipo = p.get("ambiente") or "campo"
    if tipo not in TIPOS:
        raise X.m3.Falla("M3D2", "%s: `ambiente` vale %r y va uno de: %s" % (que, tipo, ", ".join(TIPOS)))
    S = X.S
    if not hasattr(S, "capa"):
        raise X.m3.Falla("M3D2", "%s: el ambiente viste un mundo de cerca (escala esquema o ciudad)" % que)
    caja = tuple(S.caja)
    if p.get("centro") is not None:
        l = X.lugar(p["centro"], que + " → centro")
        cx, cy = l["x"], l["y"]
    else:
        cx, cy = (caja[0] + caja[2]) / 2, (caja[1] + caja[3]) / 2
    R = float(p["radio_m"]) if p.get("radio_m") else 0.5 * math.hypot(caja[2] - caja[0], caja[3] - caja[1])
    dens = max(0.0, min(1.0, float(p.get("densidad", 0.5))))
    az = Azar(int(p.get("semilla", 1)) * 31 + TIPOS.index(tipo))
    L = Lienzo(cx, cy, R, caja)

    # ---- lo que no se pisa: calles (con su ancho), caminos y ríos, la carretera, edificios, agua, pavimento, piezas, evitar
    calles = MU.capa(X, "calles", que)["calles"]
    for k, q in enumerate(calles):
        L.linea([tuple(v) for v in q["puntos"]], ANCHOS.get(q.get("clase"), 7.0) / 2, ("calle", k))
    for nombre, cad in (getattr(S, "caminos", None) or {}).items():
        hw = 6.0 if nombre == "rio" else 2.0 if nombre.startswith("carril") or nombre == "orilla" else 3.5
        if nombre == "orilla":
            continue
        L.linea([(v[0], v[1]) for v in cad], hw, ("camino", nombre))
    carr = getattr(S, "carretera", None)
    if carr:
        hw = carr.get("mediana", 4) / 2 + carr.get("carriles", 4) / 2 * carr.get("ancho_carril", 3.6) + 4
        L.linea([tuple(v) for v in carr["eje"]], hw, ("carretera", 0))
    for e in MU.capa(X, "edificios", que)["edificios"]:
        xs, ys = e[1::2], e[2::2]
        L.rect(min(xs) - 0.5, min(ys) - 0.5, max(xs) + 0.5, max(ys) + 0.5)
    A = MU.capa(X, "agua", que)
    for q in A.get("poligonos") or []:
        L.agua.append([tuple(v) for v in q["puntos"]])
    for q in A.get("rios") or []:
        L.linea([tuple(v) for v in q["puntos"]], 7.0, ("rio", 0))
    for s in getattr(S, "suelos", None) or []:
        if s.get("clase") == "pavimento":
            L.pav.append([tuple(v) for v in s["puntos"]])
    for pz in (getattr(X, "piezas", None) or []):
        if isinstance(pz, dict) and pz.get("poligono") and pz.get("tipo") not in ("zona", "ambiente"):
            pts = MU.pares(pz["poligono"])
            xs, ys = [v[0] for v in pts], [v[1] for v in pts]
            L.rect(min(xs) - 3, min(ys) - 3, max(xs) + 3, max(ys) + 3)
    ev = p.get("evitar") or []
    if not isinstance(ev, list) or not all(isinstance(v, (list, tuple)) and len(v) == 3 and all(isinstance(z, (int, float)) and not isinstance(z, bool) for z in v) for v in ev):
        raise X.m3.Falla("M3D2", "%s: `evitar` es una lista de [x, y, radio_m] (las huellas de las demás piezas, en metros)" % que)
    L.circ = [(float(a), float(b), float(c)) for a, b, c in ev]

    items, lineas, cuenta = {}, {"cerca": [], "cable": [], "cable_bajo": []}, [0]

    def hay():
        return cuenta[0] < TOPE

    lim_lineas = [TOPE * 0.3]

    def poner(clase, x, y, rot, esc, r):
        if not hay():
            return False
        items.setdefault(clase, []).extend([round(x, 2), round(y, 2), round(rot, 3), round(esc, 3)])
        L.poner(x, y, r)
        cuenta[0] += 1
        return True

    def intentar(clase, r, n, gen, **kw):
        """Hasta n intentos de poner uno de `clase` en el punto que da gen() → (x, y, rot, esc)."""
        for _ in range(n):
            x, y, rot, esc = gen()
            if L.libre(x, y, r * esc, **kw):
                return poner(clase, x, y, rot, esc, r * esc)
        return False

    def al_azar():
        # más denso cerca del centro: la mitad de los puntos en el primer tercio del radio
        a = az.u() * 2 * math.pi
        u = az.u()
        r = R * (az.u() ** 0.5 if u < 0.3 else 0.4 * az.u() ** 0.5 if u < 0.75 else 0.2 * az.u() ** 0.5)
        return cx + math.cos(a) * r, cy + math.sin(a) * r

    def tendido(pts, off, paso, clase, r, salvo, lista="cable", ini=0.0, prob=1.0, salto=0):
        """Postes a `off` m de la polilínea cada `paso` m; los seguidos van unidos por cable (lista) o alambre."""
        Lg, s, run = _largo(pts), ini, []
        while s < Lg and hay():
            x, y, dx, dy = _en(pts, s)
            px, py = x - dy * off, y + dx * off
            ok = az.u() < prob and L.libre(px, py, r, salvo=salvo)
            if ok:
                sg = 1 if off >= 0 else -1      # el rumbo mira a la calle (x local): el brazo de la farola sale hacia ella
                poner(clase, px, py, math.atan2(-sg * dx, sg * dy), 1.0, r)
                run += [round(px, 2), round(py, 2)]
            elif len(run) >= 4:
                if lista:
                    lineas[lista].append(run)
                run = []
            else:
                run = []
            s += paso + (az.entre(-salto, salto) if salto else 0)
        if lista and len(run) >= 4:
            lineas[lista].append(run)

    def cercas(pts, off, salvo, on=(50, 140), off_=(20, 80)):
        Lg, s = _largo(pts), az.entre(0, 40)
        while s < Lg and hay():
            tramo = az.entre(*on)
            run, t = [], s
            while t < min(Lg, s + tramo) and hay():
                x, y, dx, dy = _en(pts, t)
                px, py = x - dy * off, y + dx * off
                if cuenta[0] < lim_lineas[0] and L.libre(px, py, 0.4, salvo=salvo):
                    poner("postec", px, py, math.atan2(dy, dx), 1.0, 0.4)
                    cuenta[0] -= 0.75
                    run += [round(px, 2), round(py, 2)]
                elif len(run) >= 4:
                    lineas["cerca"].append(run)
                    run = []
                else:
                    run = []
                t += 4.0
            if len(run) >= 4:
                lineas["cerca"].append(run)
            s += tramo + az.entre(*off_)

    def calles_cerca(clases):
        out = []
        for k, q in enumerate(calles):
            if q.get("clase") not in clases:
                continue
            pts = [tuple(v) for v in q["puntos"]]
            if any(L.cerca_del(a[0], a[1], b[0], b[1], 10) for a, b in zip(pts, pts[1:])):
                out.append((k, q, pts))
        return out

    def recortar(pts, margen=0):
        """La parte de la polilínea dentro del radio (densificada a 8 m), en tramos."""
        out, run = [], []
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 8))
            for i in range(n):
                x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
                if math.hypot(x - cx, y - cy) <= R + margen:
                    run.append((x, y))
                elif len(run) > 1:
                    out.append(run)
                    run = []
                else:
                    run = []
        if pts and math.hypot(pts[-1][0] - cx, pts[-1][1] - cy) <= R + margen:
            run.append(tuple(pts[-1]))
        if len(run) > 1:
            out.append(run)
        return out

    fuente = None

    # ======================================================================== campo
    if tipo == "campo":
        # el camino principal: el de mayor rango y más largo; postes de luz con cable a un lado, cerca al otro
        prin = sorted(calles_cerca(set(ANCHOS)), key=lambda c: (RANGO.get(c[1].get("clase"), 9), -_largo(c[2])))
        for i, (k, q, pts) in enumerate(prin[:3]):
            hw = ANCHOS.get(q.get("clase"), 7.0) / 2
            for tr in recortar(pts):
                if i == 0:
                    tendido(tr, hw + 3.0, 34, "poste", 0.6, ("calle", k), ini=az.entre(0, 30))
                cercas(tr, -(hw + 5.5) if i == 0 else (hw + 5.0) * (1 if az.u() < 0.5 else -1), ("calle", k))
        # lindes de parcelas: cercas en algunos bordes cercanos al centro
        lindes = []
        for s in getattr(S, "suelos", None) or []:
            if s.get("clase") in ("campo", "campo2"):
                pts = [tuple(v) for v in s["puntos"]]
                for a, b in zip(pts, pts[1:] + pts[:1]):
                    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                    lindes.append((math.hypot(m[0] - cx, m[1] - cy), a, b))
        lindes.sort(key=lambda z: z[0])
        for _, a, b in lindes[:8]:
            if az.u() < 0.2 + 0.3 * dens:
                for tr in recortar([a, b]):
                    cercas(tr, 2.5, None, on=(60, 220), off_=(10, 40))
        # grupos de árboles (3–9 de 2–3 formas, con arbustos al pie) y sueltos
        n_grupos = int(4 + 22 * dens)
        for g in range(n_grupos):
            if not hay():
                break
            gx, gy = al_azar()
            if not L.libre(gx, gy, 6):
                continue
            pino = az.u() < 0.35
            for _ in range(int(az.entre(3, 10))):
                a, r = az.u() * 2 * math.pi, az.entre(2, 16)
                clase = "pino" if (pino and az.u() < 0.8) or az.u() < 0.15 else "copa"
                intentar(clase, 2.6 if clase == "copa" else 1.6, 2,
                         lambda: (gx + math.cos(a) * r + az.entre(-2, 2), gy + math.sin(a) * r + az.entre(-2, 2), az.u() * 6.283, az.entre(0.75, 1.3)))
            for _ in range(int(az.entre(1, 4))):
                a, r = az.u() * 2 * math.pi, az.entre(4, 18)
                intentar("arbusto", 1.4, 2, lambda: (gx + math.cos(a) * r, gy + math.sin(a) * r, az.u() * 6.283, az.entre(0.7, 1.3)))
        # los ranchos lejanos (1–3), en el borde del radio
        for _ in range(1 + int(2 * dens)):
            def lejos():
                a = az.u() * 2 * math.pi
                r = R * az.entre(0.45, 0.85) if R < 600 else az.entre(220, 520)
                return cx + math.cos(a) * r, cy + math.sin(a) * r, az.u() * 6.283, az.entre(0.9, 1.15)
            intentar("rancho", 7.0, 30, lejos)
        # lo suelto: árboles, arbustos, matorrales, piedras, manchas de flores y de pasto alto
        mezcla = (("copa", 2.6, 0.18), ("pino", 1.6, 0.08), ("arbusto", 1.4, 0.14), ("matorral", 1.0, 0.2), ("piedra", 0.9, 0.14),
                  ("flores", 2.5, 0.12), ("pasto", 2.5, 0.14))
        objetivo = int(TOPE * (0.35 + 0.65 * dens))
        intentos = 0
        while cuenta[0] < objetivo and intentos < 6000:
            intentos += 1
            u, acc = az.u(), 0
            for clase, r, w in mezcla:
                acc += w
                if u <= acc:
                    break
            x, y = al_azar()
            esc = az.entre(0.7, 1.35)
            if L.libre(x, y, r * esc):
                poner(clase, x, y, az.u() * 6.283, esc, r * esc)

    # ======================================================================== ciudad (y alrededor de la plaza)
    def ciudad(k_dens):
        mayores = calles_cerca({"autopista", "primaria", "secundaria"})
        menores = calles_cerca({"terciaria", "residencial"})
        # semáforos: en los cruces de dos calles mayores (dos esquinas opuestas)
        cruces = []
        for i, (ka, qa, pa) in enumerate(mayores):
            for kb, qb, pb in mayores[i + 1:]:
                for a, b in zip(pa, pa[1:]):
                    for c, d in zip(pb, pb[1:]):
                        den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
                        if abs(den) < 1e-6:
                            continue
                        t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
                        u = ((c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])) / den
                        if 0 <= t <= 1 and 0 <= u <= 1:
                            x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
                            if math.hypot(x - cx, y - cy) <= R:
                                La, Lb = math.hypot(b[0] - a[0], b[1] - a[1]) or 1, math.hypot(d[0] - c[0], d[1] - c[1]) or 1
                                cruces.append((math.hypot(x - cx, y - cy), x, y, ((b[0] - a[0]) / La, (b[1] - a[1]) / La), ((d[0] - c[0]) / Lb, (d[1] - c[1]) / Lb),
                                               ANCHOS.get(qa["clase"], 7) / 2, ANCHOS.get(qb["clase"], 7) / 2))
        cruces.sort(key=lambda z: z[0])
        for _, x, y, da, db, ha, hb in cruces[:10]:
            for sg in (1, -1):
                px = x + sg * (da[0] * (hb + 1.6) + db[0] * (ha + 1.6))
                py = y + sg * (da[1] * (hb + 1.6) + db[1] * (ha + 1.6))
                if L.libre(px, py, 0.4):
                    poner("semaforo", px, py, math.atan2(-sg * da[1], -sg * da[0]), 1.0, 0.8)
        # calles mayores: farolas a los dos lados, árboles de alcorque entre ellas, bancas, basureros, paradas
        for k, q, pts in mayores:
            hw = ANCHOS.get(q["clase"], 7.0) / 2
            for tr in recortar(pts):
                for sg in (1, -1):
                    ini = az.entre(0, 10) + (14 if sg < 0 else 0)
                    tendido(tr, sg * (hw + 1.1), 28, "farola", 0.5, ("calle", k), lista=None, ini=ini)
                    Lg, s = _largo(tr), ini + 14
                    while s < Lg and hay():
                        x, y, dx, dy = _en(tr, s)
                        px, py = x - dy * sg * (hw + 1.9), y + dx * sg * (hw + 1.9)
                        u = az.u()
                        if u < 0.45 + 0.4 * k_dens and L.libre(px, py, 0.8, salvo=("calle", k)):
                            poner("alcorque", px, py, az.u() * 6.283, az.entre(0.8, 1.15), 0.8)
                        elif u < 0.75 + 0.15 * k_dens and L.libre(px, py, 1.0, salvo=("calle", k)):
                            poner("banca", px, py, math.atan2(dy, dx) + (math.pi if sg > 0 else 0), 1.0, 1.0)
                            bx, by = px + dx * 1.8, py + dy * 1.8
                            if az.u() < 0.6 and L.libre(bx, by, 0.35, salvo=("calle", k)):
                                poner("basurero", bx, by, 0, 1.0, 0.35)
                        s += 28
                    Lg, s = _largo(tr), az.entre(40, 160)
                    while s < Lg and hay():
                        x, y, dx, dy = _en(tr, s)
                        px, py = x - dy * sg * (hw + 2.4), y + dx * sg * (hw + 2.4)
                        if L.libre(px, py, 2.2, salvo=("calle", k)):
                            poner("parada", px, py, math.atan2(dy, dx) + (math.pi if sg > 0 else 0), 1.0, 2.4)
                        s += az.entre(200, 300)
        # calles menores: postes de luz con cables de un lado (la luz cuelga del poste) y árboles del otro
        for k, q, pts in menores:
            hw = ANCHOS.get(q["clase"], 7.0) / 2
            sg = 1 if az.u() < 0.5 else -1
            for tr in recortar(pts):
                tendido(tr, sg * (hw + 0.8), 32, "poste", 0.5, ("calle", k), lista="cable", ini=az.entre(0, 16))
                Lg, s = _largo(tr), az.entre(4, 20)
                while s < Lg and hay():
                    x, y, dx, dy = _en(tr, s)
                    px, py = x + dy * sg * (hw + 1.6), y - dx * sg * (hw + 1.6)
                    u = az.u()
                    if u < 0.25 + 0.45 * k_dens and L.libre(px, py, 0.8, salvo=("calle", k)):
                        poner("alcorque", px, py, az.u() * 6.283, az.entre(0.75, 1.1), 0.8)
                    elif u < 0.32 + 0.45 * k_dens and L.libre(px, py, 0.35, salvo=("calle", k)):
                        poner("basurero", px, py, 0, 1.0, 0.35)
                    s += az.entre(14, 24)
        # los parques del mundo: árboles y bancas
        for z in (MU.capa(X, "zonas", que).get("zonas") or []):
            if z.get("clase") not in ("park", "parque", "garden"):
                continue
            pol = [tuple(v) for v in z["puntos"]]
            xs, ys = [v[0] for v in pol], [v[1] for v in pol]
            if not L.cerca_del(min(xs), min(ys), max(xs), max(ys)):
                continue
            n = int((max(xs) - min(xs)) * (max(ys) - min(ys)) / (260 - 140 * k_dens))
            for _ in range(min(n, 40)):
                x, y = az.entre(min(xs), max(xs)), az.entre(min(ys), max(ys))
                if MU.dentro_pol(x, y, pol):
                    c = "copa" if az.u() < 0.7 else "banca" if az.u() < 0.6 else "arbusto"
                    esc = az.entre(0.8, 1.2) if c != "banca" else 1.0
                    if L.libre(x, y, 2.4 * esc if c == "copa" else 1.2):
                        poner(c, x, y, az.u() * 6.283, esc, 2.4 * esc if c == "copa" else 1.2)

    # ======================================================================== plaza
    if tipo == "plaza":
        zonas = MU.capa(X, "zonas", que).get("zonas") or []
        cand = [z for z in zonas if z.get("clase") == "plaza" or z.get("id") == "plaza"]
        if cand:
            z = min(cand, key=lambda z: math.hypot(MU.centroide(z["puntos"])[0] - cx, MU.centroide(z["puntos"])[1] - cy))
            xs, ys = [v[0] for v in z["puntos"]], [v[1] for v in z["puntos"]]
            px0, py0, px1, py1 = min(xs), min(ys), max(xs), max(ys)
        else:
            h = min(36.0, R)
            px0, py0, px1, py1 = cx - h, cy - h, cx + h, cy + h
        mx, my, W, Hh = (px0 + px1) / 2, (py0 + py1) / 2, px1 - px0, py1 - py0
        rf = max(2.5, min(5.5, 0.07 * min(W, Hh)))
        if L.libre(mx, my, rf, pavimento_ok=True, dentro_r=False):
            fuente = [round(mx, 2), round(my, 2), round(rf, 2)]
            L.poner(mx, my, rf + 1.5)
            cuenta[0] += 1
        # jardineras: en las esquinas y en medio de cada lado; con un árbol las de las esquinas
        for fx, fy in ((0.18, 0.18), (0.82, 0.18), (0.18, 0.82), (0.82, 0.82), (0.5, 0.12), (0.5, 0.88), (0.12, 0.5), (0.88, 0.5)):
            x, y = px0 + W * fx, py0 + Hh * fy
            rot = 0.0 if fy in (0.12, 0.88) else math.pi / 2 if fx in (0.12, 0.88) else math.pi / 4
            if L.libre(x, y, 2.6, pavimento_ok=True, dentro_r=False):
                poner("jardinera", x, y, rot, 1.0, 2.6)
                if fx != 0.5 and fy != 0.5:
                    items.setdefault("copa", []).extend([round(x, 2), round(y, 2), round(az.u() * 6.283, 3), round(az.entre(0.8, 1.0), 3)])
                    cuenta[0] += 1
        # bancas en anillo mirando a la fuente; farolas en un anillo más afuera y en el borde
        rb = 0.27 * min(W, Hh)
        for i in range(8):
            a = i / 8 * 2 * math.pi + math.pi / 8
            x, y = mx + math.cos(a) * rb, my + math.sin(a) * rb
            if L.libre(x, y, 1.0, pavimento_ok=True, dentro_r=False):
                poner("banca", x, y, a + math.pi / 2, 1.0, 1.0)
        for i in range(8):
            a = i / 8 * 2 * math.pi
            x, y = mx + math.cos(a) * (rb + 3.5), my + math.sin(a) * (rb + 3.5)
            if L.libre(x, y, 0.5, pavimento_ok=True, dentro_r=False):
                poner("farola", x, y, a, 1.0, 0.5)
        for i in range(12):
            u = i / 12
            for x, y in ((px0 + 1.2 + (W - 2.4) * u, py0 + 1.2), (px0 + 1.2 + (W - 2.4) * u, py1 - 1.2)):
                if i % 3 == 1 and L.libre(x, y, 0.5, pavimento_ok=True, dentro_r=False):
                    poner("farola", x, y, 0, 1.0, 0.5)
            for x, y in ((px0 + 1.2, py0 + 1.2 + (Hh - 2.4) * u), (px1 - 1.2, py0 + 1.2 + (Hh - 2.4) * u)):
                if i % 3 == 1 and L.libre(x, y, 0.5, pavimento_ok=True, dentro_r=False):
                    poner("farola", x, y, 0, 1.0, 0.5)
        for i in range(6):
            a = az.u() * 2 * math.pi
            x, y = mx + math.cos(a) * (rb + 1.6), my + math.sin(a) * (rb + 1.6)
            if L.libre(x, y, 0.35, pavimento_ok=True, dentro_r=False):
                poner("basurero", x, y, 0, 1.0, 0.35)
        L.rect(px0, py0, px1, py1)
        ciudad(dens * 0.5)

    if tipo == "ciudad":
        ciudad(dens)

    # ======================================================================== costa
    if tipo == "costa":
        orilla = None
        cad = (getattr(S, "caminos", None) or {}).get("orilla")
        if cad:
            orilla = [(v[0], v[1]) for v in cad]
        elif L.agua:
            orilla = max(L.agua, key=len)
        if orilla:
            # de qué lado está el mar: a la izquierda (+n) o a la derecha
            x, y, dx, dy = _en(orilla, _largo(orilla) / 2)
            mar = 1 if any(MU.dentro_pol(x - dy * 12, y + dx * 12, q) for q in L.agua) else -1
            for tr in recortar(orilla):
                Lg = _largo(tr)
                # rocas en grupos sobre la orilla (pueden mojarse)
                s = az.entre(0, 30)
                while s < Lg and hay():
                    x, y, dx, dy = _en(tr, s)
                    for _ in range(int(az.entre(2, 6))):
                        o = az.entre(-5, 2) * -mar
                        px, py = x - dy * o * -1 + dx * az.entre(-5, 5), y + dx * o * -1 + dy * az.entre(-5, 5)
                        esc = az.entre(0.6, 1.6)
                        if L.libre(px, py, 1.0 * esc, agua_ok=True):
                            poner("roca", px, py, az.u() * 6.283, esc, 1.0 * esc)
                    s += az.entre(25, 70) / (0.5 + dens)
                # botes varados en la arena, la proa al mar (en grupos de 2–3)
                s = az.entre(10, 40)
                while s < Lg and hay():
                    x, y, dx, dy = _en(tr, s)
                    for b in range(int(az.entre(2, 4))):
                        o = -mar * az.entre(7, 16)
                        px, py = x - dy * o + dx * b * 4.2, y + dx * o + dy * b * 4.2
                        rot = math.atan2(dx * mar, -dy * mar) + az.entre(-0.35, 0.35)
                        if L.libre(px, py, 2.2):
                            poner("bote", px, py, rot, az.entre(0.85, 1.1), 2.2)
                    s += az.entre(60, 140) / (0.5 + dens)
                # palmeras en la arena, sueltas y en grupos
                s = az.entre(0, 15)
                while s < Lg and hay():
                    x, y, dx, dy = _en(tr, s)
                    for _ in range(1 + (az.u() < 0.4) * int(az.entre(1, 3))):
                        o = -mar * az.entre(20, 44)
                        px, py = x - dy * o + dx * az.entre(-4, 4), y + dx * o + dy * az.entre(-4, 4)
                        intentar("palmera", 1.6, 2, lambda: (px, py, az.u() * 6.283, az.entre(0.8, 1.25)))
                    s += az.entre(12, 30) / (0.4 + dens)
        # la costanera: bolardos del lado del mar, palmeras y postes con cable del otro
        for k, q, pts in calles_cerca({"primaria", "secundaria"}):
            if q.get("nombre") != "costanera" and cad:
                continue
            hw = ANCHOS.get(q["clase"], 7.0) / 2
            for tr in recortar(pts):
                x, y, dx, dy = _en(tr, _largo(tr) / 2)
                lado_mar = 1 if any(MU.dentro_pol(x - dy * 60, y + dx * 60, a) for a in L.agua) else -1
                tendido(tr, lado_mar * (hw + 1.0), 7.0, "bolardo", 0.3, ("calle", k), lista=None, ini=az.entre(0, 7))
                tendido(tr, -lado_mar * (hw + 1.0), 34, "poste", 0.5, ("calle", k), lista="cable", ini=az.entre(0, 30))
                tendido(tr, lado_mar * (hw + 3.2), 16, "palmera", 1.4, ("calle", k), lista=None, ini=8, prob=0.5 + 0.4 * dens)
        # el pueblo: lo de la ciudad a media densidad
        ciudad(dens * 0.45)

    if not cuenta[0]:
        raise X.m3.Falla("M3D2", "%s: no cupo nada (todo el radio es calle, agua o `evitar`): agranda `radio_m` o cambia `centro`" % que)
    return {"ambiente": tipo, "semilla": int(p.get("semilla", 1)), "centro": [round(cx, 1), round(cy, 1)], "radio_m": round(R, 1),
            "items": items, "lineas": lineas, "fuente": fuente, "n": int(round(cuenta[0]))}


def centro(pz, G):
    return tuple(pz["centro"])
