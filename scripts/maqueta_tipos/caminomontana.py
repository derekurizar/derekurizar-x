"""Pieza «caminomontana»: un camino de montaña genérico de dos carriles que sube en curvas por una ladera, centrado en
`lugar` y orientado por `rumbo` (hacia dónde sube: u). La ladera sube a la izquierda de quien sube (v+: talud cortado y
monte) y cae a su derecha (v−: guardavía y barranco). El eje va de u = −170 a u = +170 m (× `tamano`) con `curvas`
medias ondas de un seno de amplitud ≤ 28 m (radio ≥ 50 m) y sube `pendiente_m` de punta a punta, desde 5 m sobre el
suelo. Huella ≈ 340 × 260 m por `tamano`.

Publica sus CAMINOS (ctx.caminos): «<id>» (el eje, de abajo arriba), «<id>.carril-1» (el de subida, a la derecha del eje)
y «<id>.carril-2» (el de bajada, en sentido contrario), y SU RELIEVE (`_alturas`: la calzada a su altura): un actor o un
flujo que siga sus carriles sube y baja con el camino y se inclina con la pendiente (con `vehiculos: 0` y
`camion: false` no trae los suyos).

Y sus LUGARES (`_lugares`: «curva», «talud», «mirador», y siempre «<id>.curva»…; un lugar del mismo id en mundo.lugares
manda): curva (el ápice de la curva más cercana al centro), talud (el corte junto a esa curva) y mirador (el guardavía
frente a la curva, mirando al valle).
Resuelta: {x, y, rumbo, tamano, curvas, pendiente_m, guardavia, vehiculos, camion, camion_s, semilla, usa}."""
import math

from maqueta_tipos import _relieve as RL
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
         "vehiculos": int(p["vehiculos"]), "camion": bool(p.get("camion", True)), "camion_s": float(p["camion_s"]), "semilla": int(p["semilla"])}
    r["usa"] = list(dict.fromkeys((["camionsacos"] if r["camion"] else []) + list(OTROS[:r["vehiculos"]])))
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
    # SU RELIEVE (`_alturas`): la calzada, a la altura a la que la dibuja caminomontana.js (H0 al pie y `pendiente_m` más
    # arriba, sobre el suelo del centro de la pieza). Con él, un actor o un flujo en sus carriles sube con el camino.
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    suelo = getattr(S, "suelo_base", S.suelo)
    cad, base0 = caminos[p["id"]], suelo(r["x"], r["y"])
    L = cad[-1][2] or 1.0
    r["_alturas"] = [RL.perfil([[q[0], q[1], base0 - suelo(q[0], q[1]) + ((H0 + 0.06) * r["tamano"] + r["pendiente_m"] * q[2] / L) / um] for q in cad],
                               (W + 0.3) * k)]
    # SUS LUGARES (`_lugares`): el ápice de la curva más cercana al centro, el talud junto a ella y el mirador de enfrente
    A, kk = amplitud(n)
    apices = [(j + 0.5) * math.pi / kk - U for j in range(n)]        # sin(kk (u + U)) = ±1
    uc = min(apices, key=abs)
    vc = A * math.sin(kk * (uc + U))
    r["_lugares"] = {}
    for i, nombre, d in (("curva", "Curva", 0.0), ("talud", "Talud", W + 4.5), ("mirador", "Mirador", -(W + 1.0))):
        x, y = mundo(uc, vc + d)
        r["_lugares"][i] = {"nombre": nombre, "x": x, "y": y, "peso": 0.5}
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
