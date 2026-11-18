"""Pieza «barranca»: el cauce de una barranca hundido en el relieve, desde una traza dada (puntos [lon, lat]) de la
CUMBRE hacia ABAJO.

El orden de los puntos manda: s = 0 en la cumbre y s = largo al pie (no se reordena), así se dibuja cuesta abajo. Con
`esquematica` (por defecto), una curva suave que pasa por cada punto dado (no los mueve): la traza es esquemática y el
pie de la pieza lo dice; con false, tramos rectos entre los puntos dados.

Resuelta: {cadena: [[x, y, s, salto]] (km), largo_km, ancho_km, profundidad_m, nombre, esquematica}. Publica:
- `_caminos`: {<id>: cadena} (de la cumbre hacia abajo): un evento o un actor baja por el cauce.
- `_lugares`: «cumbre» (el primer punto), «medio» (a la mitad del cauce) y «pie» (el último)."""
import math

PASO_KM = 0.15      # muestreo de la curva suave


def resolver(p, X, que):
    M3, S = X.m3, X.S
    if getattr(S, "escala", "pais") != "pais":
        raise M3.Falla("M3D2", "%s: «barranca» es de escala pais (km sobre el relieve del set)" % que)
    pts = p.get("puntos") or []
    if len(pts) < 2:
        raise M3.Falla("M3D2", "%s: una barranca necesita `puntos` con al menos dos [lon, lat] (de la cumbre hacia abajo)" % que)
    ln = [S.xy(q[0], q[1]) for q in pts]
    if not all(S.dentro(x, y) for x, y in ln):
        raise M3.Falla("M3D2", "%s: hay puntos de la barranca fuera de la caja del set %s" % (que, S.id))
    esq = bool(p.get("esquematica", True))
    if esq and len(ln) >= 3:
        ln = M3.suavizar(ln, PASO_KM)
    cad, s = [], 0.0
    for i, (x, y) in enumerate(ln):
        if i:
            s += math.hypot(x - ln[i - 1][0], y - ln[i - 1][1])
        cad.append([round(x, 3), round(y, 3), round(s, 3), 0])
    cad[-1][3] = 1
    if s < 0.5:
        raise M3.Falla("M3D2", "%s: la traza de la barranca mide %.2f km: muy corta para verse a escala de país" % (que, s))
    nombre = p.get("nombre") or "Barranca"
    cx, cy = M3.punto_en_s([q[:3] for q in cad], s / 2)[:2]
    fx, fy = ln[0]
    bx, by = ln[-1]
    return {"cadena": cad, "largo_km": round(s, 3), "ancho_km": float(p.get("ancho_km", 0.3)),
            "profundidad_m": float(p.get("profundidad_m", 40)), "nombre": nombre, "esquematica": esq,
            "_caminos": {p["id"]: [list(q) for q in cad]},
            "_lugares": {"cumbre": {"x": round(fx, 3), "y": round(fy, 3), "nombre": "%s · cumbre" % nombre, "peso": 0.4},
                         "medio": {"x": round(cx, 3), "y": round(cy, 3), "nombre": nombre, "peso": 0.6},
                         "pie": {"x": round(bx, 3), "y": round(by, 3), "nombre": "%s · pie" % nombre, "peso": 0.5}}}


def tramos(pz):
    return [[(q[0], q[1], bool(q[3])) for q in pz["cadena"]]]


def centro(pz, G):
    return G["m3"].punto_en_s([q[:3] for q in pz["cadena"]], pz["largo_km"] / 2)
