"""Pieza «afluente»: un río que el set no trae, dibujado desde una traza dada (puntos [lon, lat], de la FUENTE a la BOCA).

El orden de los puntos manda: s = 0 en la fuente y s = largo en la boca (no se reordena por eje, como en una falla), así
la línea se dibuja río abajo y las rayas de corriente bajan hacia la boca. Con `suave`, una Catmull-Rom que pasa por cada
punto dado (no los mueve).

Resuelta: {cadena: [[x, y, s, salto]] (km), largo_km, grosor, corriente, nombre}. Publica SUS LUGARES (`_lugares`):
«fuente» (el primer punto) y «boca» (el último): «<id>.boca» sirve a una etiqueta, un pulso o un resaltar."""
import math

PASO_KM = 0.4       # muestreo de la curva suave


def resolver(p, X, que):
    M3, S = X.m3, X.S
    pts = p.get("puntos") or []
    if len(pts) < 2:
        raise M3.Falla("M3D2", "%s: un afluente necesita `puntos` con al menos dos [lon, lat] (de la fuente a la boca)" % que)
    ln = [S.xy(q[0], q[1]) for q in pts]
    if not all(S.dentro(x, y) for x, y in ln):
        raise M3.Falla("M3D2", "%s: hay puntos del afluente fuera de la caja del set %s" % (que, S.id))
    if p.get("suave", True) and len(ln) >= 3:
        ln = M3.suavizar(ln, PASO_KM)
    cad, s = [], 0.0
    for i, (x, y) in enumerate(ln):
        if i:
            s += math.hypot(x - ln[i - 1][0], y - ln[i - 1][1])
        cad.append([round(x, 3), round(y, 3), round(s, 3), 0])
    cad[-1][3] = 1
    if s < 0.5:
        raise M3.Falla("M3D2", "%s: la traza del afluente mide %.2f km: muy corta para verse a escala de país" % (que, s))
    nombre = p.get("nombre") or "Río"
    fx, fy = ln[0]
    bx, by = ln[-1]
    return {"cadena": cad, "largo_km": round(s, 3), "grosor": p.get("grosor", 1.5), "corriente": p.get("corriente", True),
            "nombre": nombre,
            "_lugares": {"fuente": {"x": round(fx, 3), "y": round(fy, 3), "nombre": "%s · fuente" % nombre, "peso": 0.4},
                         "boca": {"x": round(bx, 3), "y": round(by, 3), "nombre": "%s · boca" % nombre, "peso": 0.6}}}


def tramos(pz):
    return [[(q[0], q[1], bool(q[3])) for q in pz["cadena"]]]


def centro(pz, G):
    return G["m3"].punto_en_s(pz["cadena"], pz["largo_km"] / 2)
