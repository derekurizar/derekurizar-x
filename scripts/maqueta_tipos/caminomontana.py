"""Pieza «caminomontana»: un camino de montaña genérico de dos carriles que sube en curvas por una ladera, centrado en
`lugar` y orientado por `rumbo` (hacia dónde sube: u). La ladera sube a la izquierda de quien sube (v+: talud cortado y
monte) y cae a su derecha (v−: guardavía y barranco). El eje va de u = −170 a u = +170 m (× `tamano`) con `curvas`
medias ondas de un seno de amplitud ≤ 28 m (radio ≥ 50 m) y sube `pendiente_m` de punta a punta, desde 5 m sobre el
suelo. Huella ≈ 340 × 260 m por `tamano`.

Publica sus CAMINOS (ctx.caminos): «<id>» (el eje, de abajo arriba), «<id>.carril-1» (el de subida, a la derecha del eje)
y «<id>.carril-2» (el de bajada, en sentido contrario). OJO: son caminos 2D; un actor que los siga va a la altura del
suelo del mundo, no a la del camino: los vehículos que suben y bajan los trae la pieza (`vehiculos` y el camión de sacos).

Y sus LUGARES (solo en esquema; `setdefault`: un lugar del mismo id en mundo.lugares manda): curva (el ápice de la curva
más cercana al centro), talud (el corte junto a esa curva) y mirador (el guardavía frente a la curva, mirando al valle).
Resuelta: {x, y, rumbo, tamano, curvas, pendiente_m, guardavia, vehiculos, camion_s, semilla, usa}."""
import math

from maqueta_tipos.esquema import cadena, desplazar

U = 170.0          # medio largo del eje (m)
H0 = 5.0           # altura del camino al pie (m sobre el suelo)
CARRIL = 1.65      # del eje al centro de cada carril (m)
W = 3.7            # medio ancho del asfalto con su acotamiento (m)
OTROS = ("carro", "moto", "carro", "camion", "carro", "moto")   # los vehículos de más, en orden (el mismo de caminomontana.js)


def amplitud(n):
    k = math.pi * n / (2 * U)
    return min(28.0, 1.0 / (50.0 * k * k)), k


def eje_local(n, paso=4.0):
    """El eje en metros locales (u, v): de u = −U a +U."""
    A, k = amplitud(n)
    m = int(2 * U / paso)
    return [(-U + 2 * U * i / m, A * math.sin(k * (2 * U * i / m))) for i in range(m + 1)]


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    n = int(p["curvas"])
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "curvas": n, "pendiente_m": float(p["pendiente_m"]), "guardavia": bool(p["guardavia"]),
         "vehiculos": int(p["vehiculos"]), "camion_s": float(p["camion_s"]), "semilla": int(p["semilla"])}
    r["usa"] = list(dict.fromkeys(["camionsacos"] + list(OTROS[:r["vehiculos"]])))
    S = X.S
    k = r["tamano"] / float(getattr(S, "unidad_m", 1.0) or 1.0)
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        return [r["x"] + (u * ux - v * uy) * k, r["y"] + (u * uy + v * ux) * k]

    eje_l = eje_local(n)
    eje = [mundo(u, v) for u, v in eje_l]
    caminos = {p["id"]: cadena(eje),
               p["id"] + ".carril-1": cadena(desplazar(eje, -CARRIL * k)),
               p["id"] + ".carril-2": cadena(desplazar(eje, CARRIL * k)[::-1])}
    r["_caminos"] = caminos
    if getattr(S, "escala", "") == "esquema" and isinstance(X.propios, dict):
        A, kk = amplitud(n)
        # el ápice más cercano al centro: sin(kk (u + U)) = ±1
        apices = [(j + 0.5) * math.pi / kk - U for j in range(n)]
        uc = min(apices, key=abs)
        vc = A * math.sin(kk * (uc + U))
        for i, nombre, d in (("curva", "Curva", 0.0), ("talud", "Talud", W + 4.5), ("mirador", "Mirador", -(W + 1.0))):
            x, y = mundo(uc, vc + d)
            if not hasattr(S, "dentro") or S.dentro(x, y):
                X.propios.setdefault(i, {"nombre": nombre, "x": round(x, 1), "y": round(y, 1), "peso": 0.5})
    return r


def tramos(pz):
    k, a = pz.get("tamano", 1), math.radians(pz.get("rumbo", 0))
    ux, uy = math.cos(a), math.sin(a)
    return [[(pz["x"] + (u * ux - v * uy) * k, pz["y"] + (u * uy + v * ux) * k, False) for u, v in eje_local(pz["curvas"], 10.0)]]


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes."""
    k = pz.get("tamano", 1)
    return 175 * k, 135 * k, math.radians(pz.get("rumbo", 0))
