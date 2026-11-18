"""Pieza «orillalago»: la orilla de un lago de montaña genérico, de cerca. Centrada en `lugar` (la línea del agua con el
lago lleno: donde la playa toca el agua) y orientada por `rumbo` (u: hacia el lago; v: a su izquierda). METROS × `tamano`.

Franjas (u): el lago (u > linea del agua; con `seco` el agua se retira hasta SECO_M y deja un lecho de lodo y el tul en seco),
la playa angosta (−10…0), los lotes de hoteles y casas de campo (−14…−80, en ranuras fijas a lo largo de v; el acceso
público al muelle en v ≈ 0), el camino (u = U_CAMINO), los huertos y el pueblito (detrás del camino).
La pieza PUBLICA:
- `_alturas`: la tierra (un plano a HL m), la playa en rampa (perfiles) y la cubierta del muelle (un plano a H_MUELLE m), para
  que la gente y los vehículos queden encima;
- `_lugares` (también «<id>.<lugar>»): orilla, muelle, tular, camino, pueblo, huertos, agua-abierta, linea-agua, hotel, casas;
- `_caminos`: «<id>.camino» (el camino, a lo largo de v) y «<id>.orilla» (por la playa).
La misma geometría vive en video/maqueta/piezas/orillalago.js (constantes con el mismo nombre).
Resuelta: {x, y, rumbo, tamano, tul, seco, construcciones, epoca, camino, personas, cargadores, vendedoras (−1 = los de
`personas`), dispersion, gente_escala, cayucos, lanchas, aves, semilla, usa}."""
import math

from maqueta_tipos import _relieve as RL
from maqueta_tipos.esquema import cadena

HL = 0.6            # la tierra sobre el suelo del mundo (m)
HA = 0.08           # el agua del lago
H_MUELLE = 1.3      # la cubierta del muelle
SECO_M = 24.0       # cuánto se retira el agua con seco = 1 (m; ilustrativo, sin medida)
U_PLAYA = -10.0     # donde empieza la playa (borde de la tierra)
U_CAMINO = -95.0    # el eje del camino
MUELLE_U = (-6.0, 48.0)
MUELLE_V = 1.6
LV_TIERRA = 700.0   # medio largo de la tierra y del lago a lo largo de v


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "tul": float(p["tul"]), "seco": float(p["seco"]), "construcciones": float(p["construcciones"]),
         "epoca": p["epoca"], "camino": p["camino"], "personas": int(p["personas"]), "cayucos": int(p["cayucos"]),
         "lanchas": int(p["lanchas"]), "aves": int(p["aves"]), "semilla": int(p["semilla"]),
         "cargadores": int(p["cargadores"]) if p.get("cargadores") is not None else -1,
         "vendedoras": int(p["vendedoras"]) if p.get("vendedoras") is not None else -1,
         "dispersion": float(p.get("dispersion") or 0), "gente_escala": float(p.get("gente_escala") or 1.25)}
    usa = ["persona"]
    usa += ["carro", "bus", "camion"]
    r["usa"] = usa
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    useco = SECO_M * r["seco"]
    # el relieve: la tierra, la playa en rampa y la cubierta del muelle (alturas en unidades de la escena)
    tierra = [mundo(u, v) for u, v in ((U_PLAYA, -LV_TIERRA), (U_PLAYA, LV_TIERRA), (-380, LV_TIERRA), (-380, -LV_TIERRA))]
    campos = [RL.plano(tierra, HL * k)]
    for i in range(4):
        u = U_PLAYA + 1.25 + 2.5 * i
        z = HL + (HA + 0.04 - HL) * (u - U_PLAYA) / (-U_PLAYA)
        campos.append(RL.perfil([mundo(u, -260) + [z * k], mundo(u, 260) + [z * k]], 1.3 * k))
    deck = [mundo(u, v) for u, v in ((MUELLE_U[0], -MUELLE_V), (MUELLE_U[1], -MUELLE_V), (MUELLE_U[1], MUELLE_V), (MUELLE_U[0], MUELLE_V))]
    campos.append(RL.plano(deck, H_MUELLE * k))
    r["_alturas"] = campos

    lug = {"orilla": ("Orilla", (-4.0, -26.0), 0.7), "muelle": ("Muelle", (MUELLE_U[1] - 2, 0.0), 0.7),
           "tular": ("Tular", (20.0, 110.0), 0.7), "camino": ("Camino", (U_CAMINO, 0.0), 0.6),
           "pueblo": ("Pueblo", (-160.0, 40.0), 0.6), "huertos": ("Huertos", (-120.0, -125.0), 0.5),
           "agua-abierta": ("Agua abierta", (260.0, 0.0), 0.5), "linea-agua": ("Línea del agua", (useco + 1.0, -60.0), 0.6),
           "hotel": ("Hotel", (-46.0, 70.0), 0.6), "casas": ("Casas de campo", (-46.0, -110.0), 0.5)}
    r["_lugares"] = {}
    for i, (nombre, (u, v), peso) in lug.items():
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": nombre, "x": round(x, 2), "y": round(y, 2), "peso": peso}
    r["_caminos"] = {p["id"] + ".camino": cadena([mundo(U_CAMINO + 1.8, v) for v in range(-420, 421, 20)]),
                     p["id"] + ".orilla": cadena([mundo(-4.0, v) for v in range(-220, 221, 20)])}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo (a lo largo de u, de la tierra al lago) y medio ancho (m), y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 300 * k, 260 * k, math.radians(pz.get("rumbo", 0))
