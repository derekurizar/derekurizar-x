"""Pieza «faldavolcan»: la falda de un volcán genérico con un pueblo al pie, centrada en `lugar` (la plaza) y orientada por
`rumbo` (hacia dónde queda el volcán visto desde la plaza: u). Todo en METROS locales (u, v) × `tamano`.

- EL VOLCÁN: un cono con la cumbre en u = US (760 m), alto HS (480 m; maqueta, no a escala) y radio de base RB (640 m: la
  falda empieza en u ≈ 120, pasado el pueblo), perfil cóncavo (1 − x)^1.45 con x = r / RB, un cráter poco hondo y su labio,
  costillas suaves y BARRANCOS radiales; el primero (k = 0) es el CAUCE, que baja hacia el pueblo.
- La pieza PUBLICA su relieve (`_alturas`): una malla bilineal del cono (sin el corredor del cauce) y un perfil exacto del
  fondo del cauce, para que un actor, una marca o un evento que lo siga queden sobre el lodo y no en el aire.
- Sus LUGARES (`_lugares`; siempre también «<id>.<lugar>»): cumbre, ladera-alta (el cauce arriba), barranco (el cauce a
  media falda), pueblo (entre las casas, detrás de la plaza), plaza (el centro) e iglesia.
- Su CAMINO «<id>.cauce»: de la ladera alta por el fondo del barranco hasta la plaza (de arriba abajo).
La misma cuenta del relieve vive en video/maqueta/piezas/faldavolcan.js (función `alto`).
Resuelta: {x, y, rumbo, tamano, casas, lluvia, ventanas, personas, teja, traza, semilla, usa}."""
import math

from maqueta_tipos import _relieve as RL
from maqueta_tipos.esquema import cadena

US, HS, RB = 760.0, 480.0, 640.0           # cumbre (u), alto y radio de base del cono (m)
RC = 0.075                                  # radio del cráter (fracción de RB)
X_ALTA, X_BARRANCO = 0.22, 0.55             # dónde quedan «ladera-alta» y «barranco» sobre el cauce (fracción de RB)
PLAZA = 46.0                                # lado de la plaza (m)
IGLESIA = (PLAZA / 2 + 6 + 13, 0.0)         # el centro de la nave (u, v): la fachada mira a la plaza
PUEBLO = (-58.0, 4.0)                       # un punto entre las casas, detrás de la plaza
ANCHO_CAUCE = 12.0                          # medio ancho del corredor del cauce que publica el perfil (m)
# los barrancos: (ángulo desde la cumbre, 0 = hacia el pueblo; hondo m; ancho m). El 0 es el cauce.
BARRANCOS = ((0.08, 30.0, 1.0), (-0.58, 20.0, 0.85), (0.66, 22.0, 0.9), (-1.18, 18.0, 0.8), (1.28, 19.0, 0.85),
             (-1.92, 16.0, 0.8), (2.02, 17.0, 0.8), (2.72, 15.0, 0.75), (-2.62, 16.0, 0.75))


def fase(semilla):
    return (semilla * 0.6180339887 % 1.0) * 2 * math.pi


def eje_barranco(k, x, ph):
    """El ángulo del fondo del barranco k a la distancia x (fracción de RB) de la cumbre."""
    return BARRANCOS[k][0] + 0.045 * math.sin(x * 9.0 + k * 1.7 + ph)


def hondo(k, x):
    """La hondura del barranco k a la distancia x: cero en la cumbre y al pie."""
    f = min(1.0, max(0.0, (x - 0.1) / 0.86))
    return BARRANCOS[k][1] * math.sin(math.pi * f) ** 0.8


def ancho(k, x):
    return (9.0 + 24.0 * x) * BARRANCOS[k][2]


def alto(u, v, ph):
    """La altura del terreno (m sobre el suelo del mundo) en (u, v) locales: el cono, su cráter, sus costillas y barrancos."""
    du = u - US
    r = math.hypot(du, v)
    x = r / RB
    if x >= 1.0:
        return 0.0
    th = math.atan2(v, -du)
    h = HS * (1.0 - x) ** 1.45
    h *= 1.0 + 0.035 * math.sin(7.0 * th + ph) * 4.0 * x * (1.0 - x)
    h += 5.0 * math.exp(-((x - RC) / 0.025) ** 2)
    if x < RC:
        h -= 38.0 * (1.0 - (x / RC) ** 2)
    for k in range(len(BARRANCOS)):
        d = hondo(k, x)
        if d <= 0:
            continue
        dt = (th - eje_barranco(k, x, ph) + math.pi) % (2 * math.pi) - math.pi
        m = dt * r / ancho(k, x)
        if abs(m) < 3.5:
            h -= d * math.exp(-m * m)
    return h


def visible(h):
    """Lo que se ve del terreno: se hunde 0.6 m al pie para no pelear con el suelo del mundo."""
    return max(0.0, h - 0.6)


def cauce_local(ph, paso=0.01):
    """El fondo del cauce en (u, v) locales, de la ladera alta al pie, y del pie a la plaza."""
    pts = []
    x = X_ALTA
    while x < 0.995:
        th = eje_barranco(0, x, ph)
        r = x * RB
        pts.append((US - r * math.cos(th), r * math.sin(th)))
        x += paso
    th = eje_barranco(0, 1.0, ph)
    pie = (US - RB * math.cos(th), RB * math.sin(th))
    pts.append(pie)
    fin = (PLAZA * 0.32, PLAZA * 0.18)
    for i in range(1, 9):
        f = i / 8.0
        pts.append((pie[0] + (fin[0] - pie[0]) * f, pie[1] + (fin[1] - pie[1]) * f + 4.0 * math.sin(math.pi * f)))
    return pts


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "casas": int(p["casas"]), "lluvia": float(p["lluvia"]), "ventanas": bool(p["ventanas"]),
         "personas": int(p["personas"]), "teja": float(p["teja"]), "traza": float(p["traza"]), "semilla": int(p["semilla"])}
    r["usa"] = ["persona"] if r["personas"] else []
    S = X.S
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    ph = fase(r["semilla"])

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    def local(x, y):
        dx, dy = (x - r["x"]) / k, (y - r["y"]) / k
        return dx * ux + dy * uy, -dx * uy + dy * ux

    # el camino del cauce (de arriba abajo)
    cl = cauce_local(ph)
    r["_caminos"] = {p["id"] + ".cauce": cadena([mundo(u, v) for u, v in cl])}

    # el relieve: la malla del cono sin el corredor del cauce + el perfil exacto del fondo del cauce
    esc = r["tamano"] / um
    ladera = [q for q in cl if math.hypot(q[0] - US, q[1]) < RB]
    izq, der = [], []
    for i, (u, v) in enumerate(ladera):
        a0, b0 = ladera[max(0, i - 1)], ladera[min(len(ladera) - 1, i + 1)]
        tu, tv = b0[0] - a0[0], b0[1] - a0[1]
        L = math.hypot(tu, tv) or 1.0
        nu, nv = -tv / L, tu / L
        izq.append(mundo(u + nu * ANCHO_CAUCE, v + nv * ANCHO_CAUCE))
        der.append(mundo(u - nu * ANCHO_CAUCE, v - nv * ANCHO_CAUCE))
    # el contorno del cono (de un lado del cauce al otro, por detrás) y la muesca del corredor hasta la ladera alta
    th0 = eje_barranco(0, 1.0, ph)
    vuelta = []
    n = 72
    for i in range(1, n):
        t = th0 + 2 * math.pi * i / n
        vuelta.append(mundo(US - RB * 1.01 * math.cos(t), RB * 1.01 * math.sin(t)))
    # el contorno da la vuelta por detrás del volcán, de un lado del cauce al otro; luego sube por la orilla del corredor
    # que queda junto a su final hasta la ladera alta y baja por la otra orilla hasta el pie (la muesca del cauce)
    fin = vuelta[-1]
    if math.hypot(izq[-1][0] - fin[0], izq[-1][1] - fin[1]) <= math.hypot(der[-1][0] - fin[0], der[-1][1] - fin[1]):
        sube, baja = izq[::-1], der
    else:
        sube, baja = der[::-1], izq
    pol_pts = vuelta + sube + baja
    poligono = [c for q in pol_pts for c in q]
    cx, cy = mundo(US, 0)
    R = RB * 1.02 * k

    def f(x, y):
        u, v = local(x, y)
        return visible(alto(u, v, ph)) * esc

    campos = [RL.malla([cx - R, cy - R, cx + R, cy + R], 65, 65, f, poligono)]
    perf = []
    for u, v in cl:
        x, y = mundo(u, v)
        perf.append([x, y, visible(alto(u, v, ph)) * esc])
    campos.append(RL.perfil(perf, ANCHO_CAUCE * k))
    r["_alturas"] = campos

    # los lugares
    def en_cauce(x):
        th = eje_barranco(0, x, ph)
        return US - x * RB * math.cos(th), x * RB * math.sin(th)

    lug = {"cumbre": ("Cumbre", (US, 0.0), 0.8), "ladera-alta": ("Ladera alta", en_cauce(X_ALTA), 0.6),
           "barranco": ("Barranco", en_cauce(X_BARRANCO), 0.6), "pueblo": ("Pueblo", PUEBLO, 0.7),
           "plaza": ("Plaza", (0.0, 0.0), 0.6), "iglesia": ("Iglesia", IGLESIA, 0.5)}
    r["_lugares"] = {}
    for i, (nombre, (u, v), peso) in lug.items():
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": nombre, "x": round(x, 2), "y": round(y, 2), "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes (del pueblo a la espalda del volcán)."""
    k = pz.get("tamano", 1)
    return 780 * k, 660 * k, math.radians(pz.get("rumbo", 0))
