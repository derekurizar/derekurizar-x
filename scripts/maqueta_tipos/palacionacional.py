"""Pieza «palacionacional»: el Palacio Nacional de la Cultura simplificado como un volumen de 127 × 70 × 30 m, centrado en
`lugar` (el centro de su planta) y orientado por `rumbo` (hacia dónde mira la fachada que da a la plaza: u; v a su izquierda,
a lo largo de esa fachada). Todo en METROS locales (u, v) × `tamano`.

- Sus LUGARES (`_lugares`; siempre también «<id>.<lugar>»): centro (el centro de la planta: donde se apila lo que lo llena),
  fachada (el pie de la fachada del frente, al medio) y, con `entorno`, acera (la acera de enfrente, donde camina la gente)
  y plaza (la franja de plaza al frente).
- Ningún lado es un dato de brújula: `rumbo` lo pone quien arma la maqueta.
La misma geometría vive en video/maqueta/piezas/palacionacional.js (constantes DU, DV, UA, UC, UE, UP).
Resuelta: {x, y, rumbo, tamano, cristal, cristal_desde, cristal_dur, aristas, personas, gente_tamano, entorno, semilla, usa}."""
import math

DU, DV, HT = 35.0, 63.5, 30.0                 # medio fondo, medio frente y alto de la caja (127 × 70 × 30 m)
AC, CA, AE, PZ, AR, CR, VX = 6.0, 10.0, 6.0, 30.0, 4.0, 10.0, 80.0
UA = DU + AC
UC = UA + CA
UE = UC + AE
UP = UE + PZ
LUGARES = {
    "centro": ("Palacio", (0.0, 0.0), 0.8),
    "fachada": ("Fachada", (DU, 0.0), 0.6),
}
LUGARES_ENTORNO = {
    "acera": ("Acera de enfrente", ((UC + UE) / 2, 0.0), 0.5),
    "plaza": ("Plaza", ((UE + UP) / 2, 0.0), 0.5),
}


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "cristal": float(p["cristal"]), "cristal_desde": float(p["cristal_desde"]), "cristal_dur": float(p["cristal_dur"]),
         "aristas": float(p.get("aristas", 1)), "personas": int(p["personas"]), "gente_tamano": float(p.get("gente_tamano", 1)), "entorno": bool(p["entorno"]), "semilla": int(p["semilla"])}
    r["usa"] = ["persona"] if r["personas"] else []
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    lug = dict(LUGARES)
    if r["entorno"]:
        lug.update(LUGARES_ENTORNO)
    r["_lugares"] = {}
    for i, (nombre, (u, v), peso) in lug.items():
        r["_lugares"][i] = {"nombre": nombre, "x": round(r["x"] + (u * ux - v * uy) * k, 2),
                            "y": round(r["y"] + (u * uy + v * ux) * k, 2), "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo (por u), medio ancho (por v) en metros y el rumbo en radianes; con entorno, hasta el fondo de la plaza."""
    k = pz.get("tamano", 1)
    if pz.get("entorno", True):
        return (UP + DU + AR + CR) / 2 * k, VX * k, math.radians(pz.get("rumbo", 0))
    return (DU + AR) * k, (DV + AR) * k, math.radians(pz.get("rumbo", 0))
