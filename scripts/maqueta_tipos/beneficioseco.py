"""Pieza «beneficioseco»: el beneficio seco por dentro (pergamino → café oro), genérico, centrado en `lugar` y orientado por
`rumbo` (hacia dónde mira el frente abierto de la galera de corte). Huella ≈ 24 × 14 m por `tamano`, más el patio de
maniobras con el camión del lado derecho (v−): caja ≈ 30 × 16 m. Resuelta: {x, y, rumbo, tamano, personas, semilla, usa}.

Las ESTACIONES quedan como lugares con nombre del mundo (`_lugares`: para anclar marcas, cámara y resaltar): recibo,
limpieza, trilla, clasificacion y empaque, y siempre «<id>.recibo»… (un lugar del mismo id declarado en mundo.lugares
manda; con dos beneficios secos, el nombre corto es del primero). El centro (M3D6/M3D9) es `lugar`."""
import math

# (u, v) en metros: u hacia el frente abierto, v a su izquierda (el proceso corre de v− a v+, de derecha a izquierda
# vista desde el frente)
ESTACIONES = {
    "recibo": ("Recibo", 1.0, -9.6),
    "limpieza": ("Limpieza", -2.2, -5.2),
    "trilla": ("Trilla", -2.2, -0.6),
    "clasificacion": ("Clasificación", 0.0, 4.0),
    "empaque": ("Empaque", -3.2, 9.6),
}


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "personas": int(p["personas"]), "semilla": int(p["semilla"])}
    r["usa"] = ["camionsacos"] + (["persona"] if r["personas"] else [])
    k, a = r["tamano"] / float(getattr(X.S, "unidad_m", 1.0) or 1.0), math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    r["_lugares"] = {i: {"nombre": nombre, "x": r["x"] + (u * ux - v * uy) * k, "y": r["y"] + (u * uy + v * ux) * k, "peso": 0.5}
                     for i, (nombre, u, v) in ESTACIONES.items()}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo y medio ancho de la huella con el camión, en metros, y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 8.0 * k, 15.0 * k, math.radians(pz.get("rumbo", 0))
