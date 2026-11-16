"""Pieza «muelle»: un muelle genérico de carga en la costa, centrado en `lugar` (la orilla: donde la plataforma del patio toca
el mar) y orientado por `rumbo` (hacia el mar). La plataforma del patio va de 32 m tierra adentro a 72 m mar adentro y 144 m
de ancho; el muelle sale de ella 128 m más; la calle de acceso con la fila de camiones baja por el costado derecho (mirando al
mar) hasta 140 m del centro. Huella ≈ 240 × 150 m por `tamano`. Resuelta: {x, y, rumbo, tamano, gruas, personas, camiones,
barcos, semilla, usa}. Usa el objeto `barco` si hay barcos y `persona` si hay gente. El centro (para M3D6/M3D9) es `lugar`."""
import math


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "gruas": int(p["gruas"]), "personas": int(p["personas"]), "camiones": int(p["camiones"]),
         "barcos": int(p["barcos"]), "semilla": int(p["semilla"])}
    usa = (["barco"] if r["barcos"] else []) + (["persona"] if r["personas"] else [])
    if usa:
        r["usa"] = usa
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo (hacia el mar, desde el centro de la huella) y medio ancho, en metros, y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 120 * k, 75 * k, math.radians(pz.get("rumbo", 0))
