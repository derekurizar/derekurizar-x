"""Pieza «drenajeorilla»: el drenaje de un pueblo de orilla, genérico, de cerca. Centrada en `lugar` (la línea del agua frente
al pueblo) y orientada por `rumbo` (u: hacia el lago; v: a su izquierda). METROS × `tamano`.

Franjas (u): el lago (u > 0), la playa en rampa (−12…0), la fila de casas del frente (u ≈ −40), la calle con el colector
(u = U_CALLE), la fila de atrás (u ≈ −82). A lo largo de v: el pueblo (v −95…40) y, a su izquierda, la planta de tratamiento
(cercada, v 50…114). Las casas con v ≥ `corte` van a la planta; las de v < `corte`, a los desagües que bajan crudos a la
playa entre las casas del frente. `a_planta` mueve el corte (ilustrativo: la parte del pueblo, no una cifra).
La pieza PUBLICA:
- `_alturas`: la tierra (un plano a HL m) y la playa en rampa (perfiles), para que la gente quede encima;
- `_lugares` (también «<id>.<lugar>»): pueblo, planta, desague (el primer desagüe crudo; sin desagües, la salida de la planta),
  desague-2, desague-3 (si los hay), salida-planta, orilla, lago, calle, mancha (frente al primer desagüe);
- `_caminos`: «<id>.calle» (la calle del pueblo, a lo largo de v).
La misma geometría vive en video/maqueta/piezas/drenajeorilla.js (constantes con el mismo nombre).
Resuelta: {x, y, rumbo, tamano, a_planta, sin_drenaje, personas, semilla, corte, desagues, usa}."""
import math

from maqueta_tipos import _relieve as RL
from maqueta_tipos.esquema import cadena

HL = 0.6            # la tierra sobre el suelo del mundo (m)
HA = 0.08           # el agua del lago
U_PLAYA = -12.0     # donde empieza la playa
U_CALLE = -60.0     # el eje de la calle (y del colector)
U_TIERRA = -150.0   # el fondo de la tierra
LV = 150.0          # medio largo de la pieza a lo largo de v
HV0, HPASO, NH = -95.0, 15.0, 10      # las casas de cada fila: v = HV0 + HPASO·j
SAL_V = 83.0        # donde sale el efluente de la planta
U_BOCA = -2.5       # la boca de los desagües (sobre la playa)


def corte_v(a_planta):
    """Las casas con v ≥ corte van a la planta."""
    return 45.0 - 150.0 * a_planta


def desagues_v(a_planta):
    """Dónde bajan los desagües crudos (v de los huecos entre casas del frente), 0–3."""
    vc = corte_v(a_planta)
    if vc <= HV0:
        return []
    huecos = [HV0 - HPASO / 2 + HPASO * k for k in range(NH)]          # −102.5 … 32.5
    cand = [g for g in huecos if g < vc - 2]
    largo = min(vc, 45.0) - (HV0 - 5)
    nd = max(1, min(3, int(round(largo / 55.0))))
    nd = min(nd, len(cand))
    return [cand[min(len(cand) - 1, int(round((i + 0.5) * len(cand) / nd - 0.5)))] for i in range(nd)]


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "a_planta": float(p["a_planta"]), "sin_drenaje": float(p["sin_drenaje"]), "personas": int(p["personas"]),
         "semilla": int(p["semilla"])}
    r["corte"] = round(corte_v(r["a_planta"]), 2)
    r["desagues"] = desagues_v(r["a_planta"])
    r["usa"] = ["persona"] if r["personas"] else []
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    tierra = [mundo(u, v) for u, v in ((U_PLAYA, -LV), (U_PLAYA, LV), (U_TIERRA, LV), (U_TIERRA, -LV))]
    campos = [RL.plano(tierra, HL * k)]
    for i in range(4):
        u = U_PLAYA + 1.5 + 3.0 * i
        z = HL + (HA + 0.04 - HL) * (u - U_PLAYA) / (-U_PLAYA)
        campos.append(RL.perfil([mundo(u, -LV) + [z * k], mundo(u, LV) + [z * k]], 1.6 * k))
    r["_alturas"] = campos

    d = r["desagues"]
    lug = {"pueblo": ("Pueblo", (U_CALLE, -30.0), 0.7), "planta": ("Planta", (-33.0, 84.0), 0.7),
           "salida-planta": ("Salida de la planta", (U_BOCA, SAL_V), 0.6),
           "desague": ("Desagüe", (U_BOCA, d[0] if d else SAL_V), 0.7),
           "orilla": ("Orilla", (-5.0, -30.0), 0.5), "lago": ("Lago", (60.0, -10.0), 0.5),
           "calle": ("Calle", (U_CALLE, -30.0), 0.5), "mancha": ("Agua turbia", (15.0, d[0] if d else SAL_V), 0.5)}
    for i, g in enumerate(d[1:], start=2):
        lug["desague-%d" % i] = ("Desagüe", (U_BOCA, g), 0.5)
    r["_lugares"] = {}
    for i, (nombre, (u, v), peso) in lug.items():
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": nombre, "x": round(x, 2), "y": round(y, 2), "peso": peso}
    r["_caminos"] = {p["id"] + ".calle": cadena([mundo(U_CALLE + 1.6, v) for v in range(-140, 141, 20)])}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo (a lo largo de u, de la tierra al lago) y medio ancho (m), y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 160 * k, 150 * k, math.radians(pz.get("rumbo", 0))
