"""Pieza «tostaduria»: el interior de una tostaduría de café, genérico, centrado en `lugar` y orientado por `rumbo` (hacia
dónde mira el frente abierto de la maqueta de corte). Huella ≈ 19 × 13 m por `tamano`. Resuelta: {x, y, rumbo, tamano,
tostadoras, personas, semilla, usa}. Siempre usa el objeto `tostadora`; `persona` si hay gente. El centro (para M3D6/M3D9)
es `lugar`."""
import math


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "tostadoras": int(p["tostadoras"]), "personas": int(p["personas"]), "semilla": int(p["semilla"])}
    r["usa"] = ["tostadora"] + (["persona"] if r["personas"] else [])
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo y medio ancho de la huella, en metros, y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 9.5 * k, 6.5 * k, math.radians(pz.get("rumbo", 0))
