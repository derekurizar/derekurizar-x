"""Pieza «estacioncable»: una estación genérica de teleférico urbano (cable aéreo con cabinas), en metros reales × `tamano`,
centrada en `lugar` (el centro de la estación) y orientada por `rumbo` (u: hacia donde sale el cable; v: a su izquierda).
Dos estados:
- `obra`: el predio vallado (u −42…42, v −30…30) con la excavación de la cimentación, las zapatas, arranques de columnas y
  la base del mástil; grúas torre genéricas, una excavadora, montículos de tierra, caseta de obra y obreros sin rostro.
  Sin cable ni cabinas.
- `lista`: la estación elevada (losa a 7 m sobre columnas, techo en arco, la rueda horizontal bajo el techo), las cabinas
  que entran, giran en la rueda y salen por un cable que se pierde a 240 m hacia `rumbo` (dos mástiles; el trazo es
  ilustrativo: no afirma el de ninguna línea), la plaza con su acceso y la gente.
Publica sus LUGARES («<id>.<lugar>» y, si nadie más lo usa, «<lugar>»): estacion (el centro), acceso (la entrada a pie,
en la plaza) y, en obra, excavacion (la fosa de la cimentación) y, con grúas, grua; en lista, rueda y linea (el primer
mástil del cable).
Resuelta: {x, y, rumbo, tamano, estado, gruas, obreros, semilla, usa}."""
import math

# (nombre, u, v, peso) de los lugares que publica, en metros antes de `tamano`
COMUNES = {"estacion": ("Estación", 0.0, 0.0, 0.9), "acceso": ("Acceso", -34.0, 0.0, 0.5)}
OBRA = {"excavacion": ("Excavación", 2.0, 0.0, 0.7)}
GRUA = ("Grúa", -26.0, -19.0, 0.4)
LISTA = {"rueda": ("Rueda", -10.0, 0.0, 0.6), "linea": ("Línea", 70.0, 0.0, 0.4)}


def resolver(p, X, que):
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    l = X.lugar(p["lugar"], que + " → lugar")
    estado = p.get("estado") or "obra"
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "estado": estado, "gruas": int(p["gruas"]), "obreros": int(p["obreros"]), "semilla": int(p["semilla"])}
    if estado == "lista" and r["gruas"]:
        X.avisos.append("%s: estado lista: las grúas solo se dibujan en obra" % que)
    usa = []
    if r["obreros"]:
        usa.append("persona")
    if estado == "obra":
        usa.append("volteo")
    else:
        usa.append("arbol")
    r["usa"] = usa
    ang = math.radians(r["rumbo"])
    ux, uy, K = math.cos(ang), math.sin(ang), r["tamano"] / um

    def W(u, v):
        return round(l["x"] + (u * ux - v * uy) * K, 3), round(l["y"] + (u * uy + v * ux) * K, 3)
    lug = dict(COMUNES)
    if estado == "obra":
        lug.update(OBRA)
        if r["gruas"]:
            lug["grua"] = GRUA
    else:
        lug.update(LISTA)
    r["_lugares"] = {}
    for k, (nom, u, v, peso) in lug.items():
        x, y = W(u, v)
        r["_lugares"][k] = {"nombre": nom, "x": x, "y": y, "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo (a lo largo de `rumbo`), medio ancho, en metros, y el rumbo en radianes: el predio o la plaza (el cable
    de la estación lista sale 240 m más hacia `rumbo`, en el aire)."""
    k = pz.get("tamano", 1)
    return 45 * k, 32 * k, math.radians(pz.get("rumbo", 0))
