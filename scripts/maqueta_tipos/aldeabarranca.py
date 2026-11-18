"""Pieza «aldeabarranca»: una aldea rural pequeña en la falda baja de un volcán, con la barranca ancha de piedra y arena
gris a un lado y una carretera asfaltada que la cruza por un puente y pasa junto a la aldea. Centrada en `lugar` (el
centro de la aldea) y orientada por `rumbo` (u: hacia el volcán; v: a su izquierda, el lado de la barranca). Todo en
METROS locales (u, v) × `tamano`.

- EL TERRENO: una meseta (Z0 = 22 m sobre el suelo del mundo; sube 8 m hacia el volcán) que baja a cero en 200 m por
  fuera del recuadro; el CONO (cumbre en (US, VS), alto HS, radio de base RB), una LOMA al sur de la aldea (el valle
  estrecho) y la BARRANCA, cuyo eje baja del cono (u = UTOP) hasta pasar el borde (u = UBOT), con medio ancho `hw(u)`
  (ancho_barranca_m / 2 en el llano, más angosta arriba) y fondo plano a 3–9 m sobre el suelo del mundo.
- La pieza PUBLICA su relieve (`_alturas`): una malla de la meseta, el cono y la loma con la muesca de la barranca, el
  perfil del fondo de la barranca y el perfil de la carretera (sobre el puente, la losa: manda el más alto).
- Sus LUGARES: cumbre, barranca-alta, puente, carretera, aldea, lado-barranca, escuela, salon, cisterna.
- Sus CAMINOS: «<id>.cauce» (de la barranca alta por el fondo hasta pasar la aldea) y «<id>.carretera» (de sur a norte,
  por el puente).
La misma cuenta vive en video/maqueta/piezas/aldeabarranca.js (función `geo`).
Resuelta: {x, y, rumbo, tamano, casas, personas, vehiculos, ancho_barranca_m, semilla, usa}."""
import math

from maqueta_tipos import _relieve as RL
from maqueta_tipos.esquema import cadena

US, VS, HS, RB, RC = 820.0, -40.0, 480.0, 640.0, 0.075
Z0, UA, UB, VA, VB, FD = 22.0, -600.0, 1500.0, -640.0, 680.0, 200.0
UR, UTOP, UBOT = 170.0, 740.0, -820.0
VEH = ("carro", "camion", "bus", "carro")


def liso(a, b, x):
    v = min(1.0, max(0.0, (x - a) / (b - a)))
    return v * v * (3 - 2 * v)


def fase(semilla):
    return (semilla * 0.6180339887 % 1.0) * 2 * math.pi


class Geo:
    """La cuenta del terreno (la misma de aldeabarranca.js → geo)."""

    def __init__(self, W, ph):
        self.W, self.ph, self.VB0 = W, ph, 95.0 + W / 2

    def plain(self, u):
        return Z0 + 8 * liso(-200, 500, u)

    def cone(self, u, v):
        du, dv = u - US, v - VS
        r = math.hypot(du, dv)
        x = r / RB
        if x >= 1:
            return 0.0
        th = math.atan2(dv, -du)
        h = HS * (1 - x) ** 1.45
        h *= 1 + 0.05 * math.sin(9 * th + self.ph) * 4 * x * (1 - x)
        h += 5 * math.exp(-((x - RC) / 0.025) ** 2)
        if x < RC:
            h -= 38 * (1 - (x / RC) ** 2)
        return h

    def loma(self, u, v):
        return 26 * math.exp(-((v + 330) / 120) ** 2) * (0.75 + 0.25 * math.sin(u / 170 + self.ph)) * (1 - liso(500, 900, u))

    def base(self, u, v):
        return self.plain(u) + self.cone(u, v) + self.loma(u, v)

    def fade(self, u, v):
        return liso(UA - FD, UA, u) * liso(UB + FD, UB, u) * liso(VA - FD, VA, v) * liso(VB + FD, VB, v)

    def va(self, u):
        return self.VB0 + 30 * math.sin(u / 210 + self.ph) - 150 * liso(350, UTOP, u)

    def hw(self, u):
        return self.W / 2 * (0.18 + 0.82 * (1 - liso(150, UTOP, u))) * (1 + 0.12 * math.sin(u / 90 + 2 * self.ph))

    def floor(self, u):
        b = self.base(u, self.va(u))
        flp = 3 + 6 * liso(-600, 500, u)
        dep = min(32.0, max(0.0, b - flp)) * (1 - liso(UTOP - 160, UTOP, u))
        return b - dep

    def carved(self, u, v):
        b = self.base(u, v)
        if u > UTOP:
            return b
        m = abs(v - self.va(u)) / max(1e-6, self.hw(u))
        pr = 1 - liso(0.7, 1.12, m)
        return b + (self.floor(u) - b) * pr

    def alto(self, u, v):
        return self.fade(u, v) * self.carved(u, v)

    def vis(self, u, v):
        return max(0.0, self.alto(u, v) - 0.6)

    def vis_base(self, u, v):
        return max(0.0, self.fade(u, v) * self.base(u, v) - 0.6)

    # la carretera: u = ur(v), de sur a norte
    def ur(self, v):
        return UR + 18 * math.sin(v / 260 + self.ph * 0.7)

    def cruce(self):
        """La v donde la carretera cruza el eje de la barranca, y los dos estribos del puente."""
        v = self.va(UR)
        for _ in range(30):
            v = self.va(self.ur(v))
        h = self.hw(self.ur(v))
        return v, v - h * 1.25 - 6, v + h * 1.25 + 6

    def hroad(self, v):
        vb, v0, v1 = self.cruce()
        if v0 <= v <= v1:
            a = self.vis(self.ur(v0), v0) + 0.12
            b = self.vis(self.ur(v1), v1) + 0.12
            return a + (b - a) * (v - v0) / (v1 - v0)
        return self.vis(self.ur(v), v) + 0.12


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "casas": int(p["casas"]), "personas": int(p["personas"]), "vehiculos": int(p["vehiculos"]),
         "ancho_barranca_m": float(p["ancho_barranca_m"]), "semilla": int(p["semilla"])}
    usa = ["persona"] if r["personas"] else []
    for t in VEH[:r["vehiculos"]]:
        if t not in usa:
            usa.append(t)
    r["usa"] = usa
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    G = Geo(r["ancho_barranca_m"], fase(r["semilla"]))

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    # los caminos
    cauce = []
    u = UTOP - 40
    while u > UBOT:
        cauce.append((u, G.va(u)))
        u -= 12
    vb, v0, v1 = G.cruce()
    road = []
    v = VA - FD - 120
    while v < VB + FD + 120:
        road.append((G.ur(v), v))
        v += 8
    r["_caminos"] = {p["id"] + ".cauce": cadena([mundo(*q) for q in cauce]),
                     p["id"] + ".carretera": cadena([mundo(*q) for q in road])}

    # el relieve: la malla (sin la barranca) con la muesca del corredor, el perfil del fondo y el de la carretera
    rim = 1.12
    norte = [mundo(uu, G.va(uu) + G.hw(uu) * rim) for uu, _ in cauce]
    sur = [mundo(uu, G.va(uu) - G.hw(uu) * rim) for uu, _ in cauce]
    E0, E1, F0, F1 = UA - FD, UB + FD, VA - FD, VB + FD
    # de la punta (arriba) por la orilla sur hasta el borde de abajo, la vuelta por el recuadro y de regreso por la norte
    caja_loc = [(E0, F0), (E1, F0), (E1, F1), (E0, F1)]
    pol = sur + [mundo(*q) for q in caja_loc] + norte[::-1]
    poligono = [c for q in pol for c in q]
    xs = [mundo(*q)[0] for q in caja_loc]
    ys = [mundo(*q)[1] for q in caja_loc]

    def f(x, y):
        dx, dy = (x - r["x"]) / k, (y - r["y"]) / k
        uu, vv = dx * ux + dy * uy, -dx * uy + dy * ux
        return G.vis_base(uu, vv) * k

    campos = [RL.malla([min(xs), min(ys), max(xs), max(ys)], 110, 110, f, poligono)]
    campos.append(RL.perfil([mundo(uu, vv) + [G.vis(uu, vv) * k] for uu, vv in cauce], G.W / 2 * 0.72 * k))
    campos.append(RL.perfil([mundo(G.ur(vv), vv) + [G.hroad(vv) * k] for _, vv in road], 4.6 * k))
    r["_alturas"] = campos

    # los lugares
    vr = vb - G.hw(G.ur(vb)) - 14
    lug = {"cumbre": ("Cumbre", (US, VS), 0.8), "barranca-alta": ("Barranca alta", (560.0, G.va(560.0)), 0.6),
           "puente": ("Puente", (G.ur(vb), vb), 0.7), "carretera": ("Carretera", (G.ur(-60.0), -60.0), 0.5),
           "aldea": ("Aldea", (-20.0, -20.0), 0.8),
           "lado-barranca": ("Lado de la barranca", (-60.0, G.va(-60.0) - G.hw(-60.0) * 1.2 - 10), 0.6),
           "escuela": ("Escuela", (26.0, -44.0), 0.4), "salon": ("Salón comunal", (-90.0, 22.0), 0.4),
           "cisterna": ("Cisterna", (-62.0, 30.0), 0.3)}
    del vr
    r["_lugares"] = {}
    for i, (nombre, (uu, vv), peso) in lug.items():
        x, y = mundo(uu, vv)
        r["_lugares"][i] = {"nombre": nombre, "x": round(x, 2), "y": round(y, 2), "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 1050 * k, 660 * k, math.radians(pz.get("rumbo", 0))
