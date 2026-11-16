"""Pieza «cafeteriacalle»: una cafetería genérica de mostrador abierta a la calle (sin marca ni texto), centrada en `lugar`
(el pie de su fachada) y orientada por `rumbo` (hacia dónde mira la fachada: la calle). Huella ≈ 20 × 22 m por `tamano`
(el local, sus dos vecinos, la acera y un carril de calle). Resuelta: {x, y, rumbo, tamano, clientes, paseantes, semilla,
usa}. Usa siempre el objeto `persona` (la barista). El centro (para M3D6/M3D9) es `lugar`."""
import math


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "clientes": int(p["clientes"]), "paseantes": int(p["paseantes"]), "semilla": int(p["semilla"])}
    r["usa"] = ["persona"]
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo y medio ancho de la huella, en metros, y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 10.0 * k, 11.0 * k, math.radians(pz.get("rumbo", 0))
