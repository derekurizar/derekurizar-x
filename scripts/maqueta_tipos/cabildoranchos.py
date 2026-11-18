"""Pieza «cabildoranchos»: un llano abierto y modesto donde UN rancho de paja hace de casa consistorial, con su rancherío de
alojamiento alrededor, el camino de llegada y, si se pide, una ermita sencilla sobre una loma al fondo. Genérica: sin lugar
real ni nombres. Centrada en `lugar` (la mesa bajo el rancho) y orientada por `rumbo` (u: hacia donde queda la ermita; v: a
su izquierda). Todo en METROS locales (u, v) × `tamano`.

- La pieza PUBLICA sus lugares (`_lugares`; siempre también «<id>.<lugar>»): rancho (el frente abierto del rancho del
  cabildo), mesa (la mesa bajo el rancho), iglesia (la ermita; solo con `iglesia`), llegada (donde se detiene lo que entra
  por el camino), ranchos (entre el rancherío) y llano (el campo abierto junto al camino).
- Su RELIEVE (`_alturas`): el piso del llano, un plano a 0.12 m sobre el suelo del mundo (queda encima de las parcelas de la
  receta campo y la gente y los vehículos de otros lo pisan).
- Su CAMINO «<id>.llegada»: de la orilla del llano hasta el frente del rancho (por donde entran las mulas y la carreta).
La misma traza vive en video/maqueta/piezas/cabildoranchos.js (CAMINO, ERMITA, RANCHOS).
Resuelta: {x, y, rumbo, tamano, ranchos, enlucidas, cabildantes, llegan, vecinos, mulas, carretas, iglesia, llegada_s,
semilla, usa}."""
import math

from maqueta_tipos import _relieve as RL
from maqueta_tipos.esquema import cadena

ERMITA = (58.0, 20.0)
CAMINO = ((-96.0, -30.0), (-72.0, -23.0), (-50.0, -14.0), (-32.0, -7.5), (-19.0, -4.0), (-6.0, -1.4))
BASE, R_LLANO = 0.12, 90.0             # el piso del llano: un plano a 0.12 m de 90 m de radio (sobre las parcelas del mundo)
ALTO_PARADA = 11.0                       # lo que entra se detiene a esta distancia del final del camino (m)


def _en_camino(s):
    """El punto del camino a s metros de su inicio."""
    for (a, b), (c, d) in zip(CAMINO, CAMINO[1:]):
        l = math.hypot(c - a, d - b)
        if s <= l:
            f = s / l if l else 0.0
            return a + (c - a) * f, b + (d - b) * f
        s -= l
    return CAMINO[-1]


def _largo():
    return sum(math.hypot(c - a, d - b) for (a, b), (c, d) in zip(CAMINO, CAMINO[1:]))


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "ranchos": int(p["ranchos"]), "enlucidas": int(p["enlucidas"]), "cabildantes": int(p["cabildantes"]),
         "llegan": int(p["llegan"]), "vecinos": int(p["vecinos"]), "mulas": int(p["mulas"]),
         "carretas": int(p["carretas"]), "iglesia": bool(p["iglesia"]), "llegada_s": float(p["llegada_s"]),
         "semilla": int(p["semilla"]), "usa": ["persona"]}
    S = X.S
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    r["_alturas"] = [RL.plano([mundo(R_LLANO * math.cos(2 * math.pi * i / 48), R_LLANO * math.sin(2 * math.pi * i / 48)) for i in range(48)], BASE * k)]
    r["_caminos"] = {p["id"] + ".llegada": cadena([mundo(u, v) for u, v in CAMINO])}
    lug = {"rancho": ("Rancho", (-4.6, 0.0), 0.8), "mesa": ("Mesa", (0.0, 0.0), 0.6),
           "llegada": ("Llegada", _en_camino(_largo() - ALTO_PARADA - 1.0), 0.6),
           "ranchos": ("Ranchos", (-10.0, 21.0), 0.6), "llano": ("Llano", (-28.0, 8.0), 0.5)}
    if r["iglesia"]:
        lug["iglesia"] = ("Iglesia", ERMITA, 0.6)
    r["_lugares"] = {}
    for i, (nombre, (u, v), peso) in lug.items():
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": nombre, "x": round(x, 2), "y": round(y, 2), "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes (del rancho hacia la ermita)."""
    k = pz.get("tamano", 1)
    return 90 * k, 90 * k, math.radians(pz.get("rumbo", 0))
