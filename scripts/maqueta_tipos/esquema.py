"""Mundo «esquema»: un lugar GENÉRICO hecho a mano por una receta (una ciudad, una carretera que la cruza, el campo, la
costa, una plaza), determinista por `semilla` y sin archivos. No afirma geografía: lleva el aviso «Esquema» en el pie y
sus lugares no se llaman como un lugar real (M3D12).

La receta se calcula AQUÍ, una sola vez, y viaja resuelta al motor (MAQUETA.mundo: suelos y lo que dibujan las piezas):
así los gates, las reglas de cada pieza y video/maqueta/mundos/esquema.js ven exactamente lo mismo. Todo en METROS
locales: el centro del mundo es (0, 0), x = este, y = norte. Lo que la receta deja (los mismos formatos que un set de
ciudad, para que `calles`, `edificios`, `agua` y `zona` lean igual de los dos):

  calles     [{clase, nombre, puntos}]              clase: autopista|primaria|secundaria|terciaria|residencial|peatonal
  edificios  [[altura_m, x0, y0, x1, y1, …]]         anillo exterior sin cerrar
  agua       {poligonos: [{nombre, puntos}], rios: [{nombre, clase, puntos}]}
  zonas      [{id, nombre, clase, puntos}]          parques, la plaza
  suelos     [{clase, puntos}]                      lo que pinta el propio mundo: arena, campo (dos tonos), pavimento
  carretera  {eje, carriles, ancho_carril, mediana} (solo la receta carretera)
  caminos    {nombre: [[x, y, s, 0], …]}            con nombre, para que otras piezas los sigan (Fase 2: carros, gente)
  lugares    {id: {nombre, x, y, peso}}             ids genéricos: centro, norte, sur, este, oeste y los de su receta
"""
import math

RECETAS = ("ciudad", "carretera", "campo", "costa", "plaza")
ANCHO_CALLE = {"autopista": 22.0, "primaria": 16.0, "secundaria": 13.0, "terciaria": 11.0, "residencial": 9.0, "peatonal": 5.0}


class Azar:
    """Azar fijo por semilla (xorshift32): la misma semilla da los mismos números en cualquier Python."""

    def __init__(self, semilla):
        self.s = (int(semilla) * 2654435761 + 0x9E3779B9) & 0xFFFFFFFF or 0x12345678

    def u(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.s = s & 0xFFFFFFFF
        return self.s / 4294967296.0

    def entre(self, a, b):
        return a + (b - a) * self.u()


def cadena(pts):
    """[[x, y], …] → [[x, y, s, 0], …] (s: metros desde el inicio): el formato de los caminos y de las cadenas de motor.js."""
    out, s = [], 0.0
    for i, (x, y) in enumerate(pts):
        if i:
            s += math.hypot(x - pts[i - 1][0], y - pts[i - 1][1])
        out.append([round(x, 2), round(y, 2), round(s, 2), 0])
    return out


def desplazar(pts, d):
    """Una polilínea corrida `d` metros a su izquierda (d < 0: a la derecha)."""
    out = []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append([x - dy / L * d, y + dx / L * d])
    return out


def caja_pol(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def plano(pol):
    return [round(v, 1) for q in pol for v in q]


class Esquema:
    escala, unidad_m, km, exag = "esquema", 1.0, 0.001, 1.0
    como_lugar = "decláralo con x e y en metros (el centro del mundo es 0, 0; x = este, y = norte), o usa [x, y]"

    def __init__(self, receta, semilla=1, tamano_m=1600.0, carriles=4, manzana_m=90.0, altura_max_m=60.0):
        self.receta, self.semilla, self.T = receta, int(semilla), float(tamano_m)
        self.id = "esquema-%s" % receta
        self.fuente = {"pie": "", "pie_claves": {}}
        self.calles, self.edificios, self.zonas, self.suelos = [], [], [], []
        self.agua = {"poligonos": [], "rios": []}
        self.carretera, self.caminos, self.lugares = None, {}, {}
        self.carriles, self.manzana, self.hmax = int(carriles), float(manzana_m), float(altura_max_m)
        self.az = Azar(self.semilla * 7919 + RECETAS.index(receta))
        h = self.T / 2
        self.x0, self.y0, self.x1, self.y1 = -h, -h, h, h
        getattr(self, "_" + receta)()
        for i, (nombre, x, y) in enumerate((("Centro", 0, 0), ("Norte", 0, 0.36 * self.T), ("Sur", 0, -0.36 * self.T),
                                             ("Este", 0.36 * self.T, 0), ("Oeste", -0.36 * self.T, 0))):
            self.lugares.setdefault(nombre.lower(), {"nombre": nombre, "x": round(x, 1), "y": round(y, 1), "peso": 0.6})

    # ---------- lo que el resolver y los gates usan ----------
    @property
    def caja(self):
        return (self.x0, self.y0, self.x1, self.y1)

    def dentro(self, x, y, margen=0.0):
        return self.x0 + margen <= x <= self.x1 - margen and self.y0 + margen <= y <= self.y1 - margen

    def suelo(self, x, y):
        return 0.0

    def punto(self, a, b):
        return float(a), float(b)

    def lugar_xy(self, l):
        return float(l["x"]), float(l["y"])

    def xy(self, lon, lat):
        return None

    def archivos(self):
        return []

    def datos_R(self):
        return {}

    def datos_mundo(self):
        return {"receta": self.receta, "semilla": self.semilla, "tamano_m": self.T, "suelos": self.suelos}

    def capa(self, nombre):
        """Lo que leen las piezas, con el mismo formato que las capas de un set de ciudad."""
        return {"calles": {"calles": self.calles, "arterias": {}}, "edificios": {"edificios": self.edificios, "nombres": {}},
                "agua": self.agua, "zonas": {"zonas": self.zonas}}[nombre]

    def datos(self):
        """Todo lo de la receta (para las pruebas: la misma semilla da exactamente esto)."""
        return {"calles": self.calles, "edificios": self.edificios, "zonas": self.zonas, "suelos": self.suelos, "agua": self.agua,
                "carretera": self.carretera, "caminos": self.caminos, "lugares": self.lugares, "caja": list(self.caja)}

    # ---------- piezas de las recetas ----------
    def calle(self, clase, nombre, pts, camino=True):
        pts = [[round(x, 1), round(y, 1)] for x, y in pts]
        self.calles.append({"clase": clase, "nombre": nombre, "puntos": pts})
        if camino and nombre:
            self.caminos[nombre] = cadena(pts)

    def manzanas(self, xs, ys, fuera=None, centro=(0.0, 0.0), parques=0.08, plaza=None, factor=None):
        """Los edificios de cada manzana entre las calles xs × ys (bordes de las manzanas); `fuera(x0, y0, x1, y1)` → True
        si esa manzana no va (el corredor de una carretera, el mar). Alturas: más altas cerca del centro."""
        n_parque = 0
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                x0, x1, y0, y1 = xs[i], xs[i + 1], ys[j], ys[j + 1]
                if x1 - x0 < 20 or y1 - y0 < 20 or (fuera and fuera(x0, y0, x1, y1)):
                    continue
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if plaza and abs(cx - plaza[0]) < 1 and abs(cy - plaza[1]) < 1:
                    continue
                if self.az.u() < parques:
                    n_parque += 1
                    self.zonas.append({"id": "parque-%d" % n_parque, "nombre": "Parque", "clase": "park", "puntos": caja_pol(x0 + 3, y0 + 3, x1 - 3, y1 - 3)})
                    continue
                r = math.hypot(cx - centro[0], cy - centro[1]) / (0.32 * self.T)
                base = (0.12 + 0.88 * math.exp(-r * r)) * (factor(cx, cy) if factor else 1.0)
                # 1–3 lotes por lado: edificios con retiro, cada uno con su altura
                nx, ny = (1 if x1 - x0 < 60 else 2), (1 if y1 - y0 < 60 else 2)
                for a in range(nx):
                    for b in range(ny):
                        lx0, lx1 = x0 + (x1 - x0) * a / nx, x0 + (x1 - x0) * (a + 1) / nx
                        ly0, ly1 = y0 + (y1 - y0) * b / ny, y0 + (y1 - y0) * (b + 1) / ny
                        m = 3.0 + 2.0 * self.az.u()
                        h = max(6.0, self.hmax * base * (0.35 + 0.75 * self.az.u()))
                        h = round(h / 3.0) * 3.0
                        self.edificios.append([h] + plano(caja_pol(lx0 + m, ly0 + m, lx1 - m, ly1 - m)))

    def rejilla(self, lim, paso, fase=0.0):
        """Las coordenadas de las calles de una cuadrícula entre −lim y lim."""
        k0 = math.ceil((-lim - fase) / paso)
        return [fase + k * paso for k in range(k0, int((lim - fase) // paso) + 1)]

    def _ciudad(self):
        T, p = self.T, self.manzana + 12.0
        lim = T / 2 - 40
        xs, ys = self.rejilla(lim, p, p / 2), self.rejilla(lim, p, p / 2)
        for k, x in enumerate(xs):
            ix = round((x - p / 2) / p)
            clase = "primaria" if ix == 0 else ("secundaria" if ix % 4 == 0 else "residencial")
            self.calle(clase, "ns-%d" % ix, [[x, -lim], [x, lim]])
        for k, y in enumerate(ys):
            iy = round((y - p / 2) / p)
            clase = "primaria" if iy == 0 else ("secundaria" if iy % 4 == 0 else "residencial")
            self.calle(clase, "eo-%d" % iy, [[-lim, y], [lim, y]])
        self.caminos["eje-ns"], self.caminos["eje-eo"] = self.caminos["ns-0"], self.caminos["eo-0"]
        bx = [x + s * 6.5 for x in xs for s in (-1, 1)]
        by = [y + s * 6.5 for y in ys for s in (-1, 1)]
        self.manzanas(bx[1:-1], by[1:-1], fuera=lambda x0, y0, x1, y1: x1 - x0 < 30 or y1 - y0 < 30, centro=(p / 2, p / 2))
        if self.zonas:
            z = self.zonas[0]["puntos"]
            self.lugares["parque"] = {"nombre": "Parque", "x": round((z[0][0] + z[2][0]) / 2, 1), "y": round((z[0][1] + z[2][1]) / 2, 1), "peso": 0.5}

    def _carretera(self):
        T, p = self.T, self.manzana + 12.0
        lim, w, med = T / 2 - 20, 3.6, 4.0
        n = max(2, self.carriles + self.carriles % 2)
        corredor = med / 2 + n / 2 * w + 3.0            # media anchura: mediana + carriles de un sentido + acotamiento
        eje = [[-lim + i * (2 * lim) / 16, 0.0] for i in range(17)]
        self.carretera = {"eje": eje, "carriles": n, "ancho_carril": w, "mediana": med}
        self.caminos["eje"] = cadena(eje)
        for k in range(1, n + 1):
            # carriles 1…n/2: en el sentido del eje (hacia el este), a su derecha; los demás, al oeste: puntos en el sentido de la marcha
            if k <= n // 2:
                self.caminos["carril-%d" % k] = cadena(desplazar(eje, -(med / 2 + (k - 0.5) * w)))
            else:
                j = k - n // 2
                self.caminos["carril-%d" % k] = cadena(desplazar(eje, med / 2 + (j - 0.5) * w)[::-1])
        lc = T / 2 - 60
        xs = self.rejilla(lc, p, p / 2)
        ys = [y for y in self.rejilla(lc, p, p / 2) if abs(y) > corredor + 40]
        for x in xs:
            ix = round((x - p / 2) / p)
            for lado, (a, b) in (("n", (corredor + 12, lc)), ("s", (-lc, -corredor - 12))):
                self.calle("secundaria" if ix % 3 == 0 else "residencial", "ns-%d-%s" % (ix, lado), [[x, a], [x, b]])
        for y in ys:
            iy = round((y - p / 2) / p)
            self.calle("residencial", "eo-%d" % iy, [[-lc, y], [lc, y]])
        for lado in (1, -1):   # las calles laterales, junto a la autopista
            y = lado * (corredor + 12)
            self.calle("terciaria", "lateral-%s" % ("norte" if lado > 0 else "sur"), [[-lc, y], [lc, y]] if lado < 0 else [[lc, y], [-lc, y]])
        bx = [x + s * 6.5 for x in xs for s in (-1, 1)]
        by = sorted([y + s * 6.5 for y in ys for s in (-1, 1)] + [corredor + 18.5, -corredor - 18.5])
        self.manzanas(bx[1:-1], by, fuera=lambda x0, y0, x1, y1: (y0 < corredor + 15 and y1 > -corredor - 15) or x1 - x0 < 30, centro=(0, 0.25 * T), parques=0.05,
                      factor=lambda cx, cy: 0.25 + 0.75 * min(1.0, max(0.0, (abs(cy) - corredor) / 260.0)))
        self.suelos.append({"clase": "pavimento", "puntos": caja_pol(-lim - 20, -corredor, lim + 20, corredor)})
        self.lugares.update({"entrada": {"nombre": "Entrada", "x": round(-0.45 * T, 1), "y": 0.0, "peso": 0.6},
                             "salida": {"nombre": "Salida", "x": round(0.45 * T, 1), "y": 0.0, "peso": 0.6},
                             "puente": {"nombre": "Puente", "x": 0.0, "y": 0.0, "peso": 0.6}})

    def _campo(self):
        T = self.T
        lim = T / 2
        # las parcelas: una cuadrícula torcida con dos tonos
        n = 6
        for j in range(n):
            for i in range(n):
                x0, x1 = -lim + i * T / n, -lim + (i + 1) * T / n
                y0, y1 = -lim + j * T / n, -lim + (j + 1) * T / n
                d = 0.04 * T / n
                pol = [[x0 + d * self.az.u(), y0 + d * self.az.u()], [x1 - d * self.az.u(), y0 + d * self.az.u()],
                       [x1 - d * self.az.u(), y1 - d * self.az.u()], [x0 + d * self.az.u(), y1 - d * self.az.u()]]
                self.suelos.append({"clase": "campo" if self.az.u() < 0.55 else "campo2", "puntos": [[round(x, 1), round(y, 1)] for x, y in pol]})
        # el camino: una curva suave de oeste a este
        cam = [[-lim + 20 + i * (T - 40) / 24, round(0.12 * T * math.sin(i / 24 * math.pi * 1.6 + 0.4), 1)] for i in range(25)]
        self.calle("primaria", "camino", cam)
        # el río: de norte a sur, cruzando el camino
        rio = [[round(0.18 * T * math.sin(j / 20 * math.pi * 1.2) + 0.2 * T, 1), round(lim - j * T / 20, 1)] for j in range(21)]
        self.agua["rios"].append({"nombre": "Río", "clase": "river", "puntos": rio})
        self.caminos["rio"] = cadena(rio)
        # el pueblo: unas casas junto al camino
        px, py = -0.18 * T, 0.12 * T * math.sin(((-0.18 * T + lim - 20) / (T - 40)) * math.pi * 1.6 + 0.4)
        for k in range(14):
            a, r = self.az.entre(0, 2 * math.pi), self.az.entre(25, 110)
            cx, cy, s = px + math.cos(a) * r, py + math.sin(a) * r + (26 if math.sin(a) > 0 else -26), self.az.entre(7, 12)
            self.edificios.append([round(self.az.entre(4, 7), 1)] + plano(caja_pol(cx - s, cy - s * 0.7, cx + s, cy + s * 0.7)))
        self.lugares.update({"pueblo": {"nombre": "Pueblo", "x": round(px, 1), "y": round(py, 1), "peso": 0.7},
                             "puente": {"nombre": "Puente", "x": round(0.2 * T + 0.18 * T * math.sin(0.5 * math.pi * 1.2), 1), "y": 0.0, "peso": 0.5}})

    def _costa(self):
        T, p = self.T, self.manzana + 12.0
        lim = T / 2
        yc = -0.18 * T
        costa = [[round(-lim + i * T / 30, 1), round(yc + 0.03 * T * math.sin(i / 30 * math.pi * 3.0) + self.az.entre(-4, 4), 1)] for i in range(31)]
        mar = costa + [[lim, -lim], [-lim, -lim]]
        self.agua["poligonos"].append({"nombre": "Mar", "puntos": mar})
        self.suelos.append({"clase": "agua", "puntos": mar})        # el mar es parte del suelo (la pieza agua lo repite encima)
        playa = costa + [[x, y + 45] for x, y in costa[::-1]]
        self.suelos.append({"clase": "arena", "puntos": playa})
        self.calle("primaria", "costanera", [[x, y + 60] for x, y in costa])
        self.caminos["orilla"] = cadena([[x, y + 4] for x, y in costa])
        y_ini = yc + 0.03 * T + 80
        xs = self.rejilla(lim - 40, p, p / 2)
        ys = [y for y in self.rejilla(lim - 40, p, p / 2) if y > y_ini]
        for x in xs:
            self.calle("residencial", "ns-%d" % round((x - p / 2) / p), [[x, y_ini - 10], [x, lim - 40]])
        for y in ys:
            self.calle("residencial", "eo-%d" % round((y - p / 2) / p), [[-lim + 40, y], [lim - 40, y]])
        bx = [x + s * 6.5 for x in xs for s in (-1, 1)]
        by = [y_ini] + [y + s * 6.5 for y in ys for s in (-1, 1)]
        self.manzanas(bx[1:-1], by, centro=(0, y_ini + 0.15 * T), parques=0.06)
        self.lugares.update({"playa": {"nombre": "Playa", "x": 0.0, "y": round(yc + 20, 1), "peso": 0.7},
                             "mar": {"nombre": "Mar", "x": 0.0, "y": round(yc - 0.15 * T, 1), "peso": 0.5},
                             "centro": {"nombre": "Centro", "x": 0.0, "y": round(y_ini + 0.15 * T, 1), "peso": 0.6}})

    def _plaza(self):
        T, p = self.T, self.manzana + 12.0
        lim = T / 2 - 40
        xs, ys = self.rejilla(lim, p, p / 2), self.rejilla(lim, p, p / 2)
        for x in xs:
            self.calle("residencial", "ns-%d" % round((x - p / 2) / p), [[x, -lim], [x, lim]])
        for y in ys:
            self.calle("residencial", "eo-%d" % round((y - p / 2) / p), [[-lim, y], [lim, y]])
        bx = [x + s * 6.5 for x in xs for s in (-1, 1)]
        by = [y + s * 6.5 for y in ys for s in (-1, 1)]
        # la plaza: la manzana del centro (la que contiene 0, 0) queda abierta, con el edificio principal al norte
        cx = min((x for x in bx[1:-1]), key=lambda v: abs(v))
        i = [k for k in range(len(bx) - 1) if bx[k] <= 0 <= bx[k + 1]][0]
        j = [k for k in range(len(by) - 1) if by[k] <= 0 <= by[k + 1]][0]
        x0, x1, y0, y1 = bx[i], bx[i + 1], by[j], by[j + 1]
        self.zonas.append({"id": "plaza", "nombre": "Plaza", "clase": "plaza", "puntos": caja_pol(x0 + 2, y0 + 2, x1 - 2, y1 - 2)})
        self.suelos.append({"clase": "pavimento", "puntos": caja_pol(x0, y0, x1, y1)})
        self.manzanas(bx[1:-1], by[1:-1], centro=(0, 0), parques=0.04, plaza=((x0 + x1) / 2, (y0 + y1) / 2))
        # el edificio principal, en la manzana de arriba de la plaza
        yn0, yn1 = by[j + 2], by[j + 3] if j + 3 < len(by) else by[j + 2] + self.manzana
        self.edificios = [e for e in self.edificios if not (x0 - 1 <= e[1] <= x1 + 1 and yn0 - 1 <= e[2] <= yn1 + 1)]
        self.edificios.append([round(min(self.hmax, 24.0), 1)] + plano(caja_pol(x0 + 6, yn0 + 6, x1 - 6, yn1 - 6)))
        self.lugares.update({"plaza": {"nombre": "Plaza", "x": round((x0 + x1) / 2, 1), "y": round((y0 + y1) / 2, 1), "peso": 0.8},
                             "edificio-principal": {"nombre": "Edificio principal", "x": round((x0 + x1) / 2, 1), "y": round((yn0 + yn1) / 2, 1), "peso": 0.7}})
        self.caminos["vuelta-plaza"] = cadena([[x0 - 6.5, y0 - 6.5], [x1 + 6.5, y0 - 6.5], [x1 + 6.5, y1 + 6.5], [x0 - 6.5, y1 + 6.5], [x0 - 6.5, y0 - 6.5]])


def mundo(o, f, m3):
    if o.get("set"):
        raise m3.Falla("M3D1", "mundo de escala esquema: no lleva `set` (es un lugar genérico hecho por su `receta`); un lugar real va en escala ciudad o pais")
    return Esquema(o["receta"], o.get("semilla", 1), o.get("tamano_m", 1600.0), o.get("carriles", 4), o.get("manzana_m", 90.0), o.get("altura_max_m", 60.0))
