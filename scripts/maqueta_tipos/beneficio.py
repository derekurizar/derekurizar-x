"""Pieza «beneficio»: el beneficio húmedo de una finca, genérico, centrado en `lugar` y orientado por `rumbo` (hacia dónde
avanza el proceso: de la despulpadora al patio). Huella ≈ 62 × 26 m por `tamano` (1 = medidas reales de un beneficio
chico, con la cereza y el rastrillo agrandados para leerse a 20–80 m). Resuelta: {x, y, rumbo, tamano, personas, semilla,
usa}. El centro (para M3D6/M3D9) es `lugar`; el patio queda hacia `rumbo`, la despulpadora hacia el lado contrario."""
import math


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "personas": int(p["personas"]), "semilla": int(p["semilla"])}
    if r["personas"]:
        r["usa"] = ["persona"]
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo y medio ancho de la huella, en metros (por si una regla quiere separar otras piezas)."""
    k = pz.get("tamano", 1)
    return 31 * k, 13 * k, math.radians(pz.get("rumbo", 0))
