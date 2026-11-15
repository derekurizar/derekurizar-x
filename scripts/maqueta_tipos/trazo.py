"""Pieza «trazo»: una línea brillante sobre un camino con nombre (la de Google Maps sobre una calle), que un evento
`trazar` DIBUJA con el tiempo y un evento `pintar` PINTA POR TRAMOS (bien · medio · mal: verde, ámbar, rojo del estilo).
Generaliza `ruta` (que une lugares en un país) para ciudad y esquema: aquí la línea va sobre un camino y se le puede
cambiar el color por tramos. `desde` y `hasta` (posiciones sobre el camino: metros, «40%» o un lugar) recortan el trazo; si
`desde` > `hasta`, el trazo va en contra del camino. `desplazar_m` lo corre a su izquierda (negativo: a la derecha).

Resuelta: {puntos: [[x, y, s_local], …] (s_local: unidades desde el inicio del trazo), largo, color, ancho, brillo}. La
posición de un evento sobre el trazo la da `local(id, ref)` (la usan trazar y pintar)."""
import math

from maqueta_tipos import _movimiento as MV
from maqueta_tipos.esquema import desplazar

COLORES = ("bien", "medio", "mal", "acento", "texto")


def resolver(p, X, que):
    cad = MV.camino(X, p["camino"], que + " → camino")
    L = cad[-1][2]
    a = MV.posicion_en(X, p["desde"], cad, que + " → desde") if p.get("desde") is not None else 0.0
    b = MV.posicion_en(X, p["hasta"], cad, que + " → hasta") if p.get("hasta") is not None else L
    if abs(b - a) < 1e-6:
        raise X.m3.Falla("M3D2", "%s: `desde` y `hasta` caen en el mismo punto del camino: el trazo no tiene largo" % que)
    paso = 4.0 / X.S.unidad_m
    n = max(2, int(math.ceil(abs(b - a) / paso)) + 1)
    sentido = 1 if b > a else -1
    # los vértices del camino entre a y b, más los puntos intermedios (para que la línea siga las curvas)
    ss = sorted({a + (b - a) * i / (n - 1) for i in range(n)} | {q[2] for q in cad if min(a, b) < q[2] < max(a, b)}, key=lambda s: s * sentido)
    pts = [MV.en_cadena(cad, s)[:2] for s in ss]
    d = float(p.get("desplazar_m", 0)) / X.S.unidad_m
    if d:
        pts = desplazar([list(q) for q in pts], d)
    loc, acc = [], 0.0
    for i, q in enumerate(pts):
        if i:
            acc += math.hypot(q[0] - pts[i - 1][0], q[1] - pts[i - 1][1])
        loc.append([round(q[0], 2), round(q[1], 2), round(acc, 2)])
    X.__dict__.setdefault("trazos", {})[p["id"]] = {"cad": cad, "a": a, "b": b, "sentido": sentido, "largo": acc, "loc": loc}
    return {"puntos": loc, "largo": round(acc, 2), "color": p["color"], "ancho": p["ancho_px"], "brillo": p["brillo"]}


def local(X, tid, ref, que):
    """Una posición del maqueta.json (metros sobre el CAMINO, «40%» DEL TRAZO o un lugar) → unidades desde el inicio del trazo."""
    T = X.trazos[tid]
    if isinstance(ref, str) and ref.strip().endswith("%"):
        try:
            return min(max(float(ref.strip()[:-1]) / 100, 0.0), 1.0) * T["largo"]
        except ValueError:
            raise X.m3.Falla("M3D2", "%s: «%s» no es una fracción (va «40%%»)" % (que, ref))
    if isinstance(ref, (int, float)) and not isinstance(ref, bool):
        s = float(ref) / X.S.unidad_m
        x, y, _, _ = MV.en_cadena(T["cad"], s)
    else:
        l = X.lugar(ref, que)
        x, y = l["x"], l["y"]
    # el punto del trazo más cercano (el trazo puede ir corrido o en contra del camino)
    return MV.proyectar([[q[0], q[1], q[2], 0] for q in T["loc"]], x, y)[0]


def con_eventos(lista, eventos, X):
    for pz in lista:
        if pz["color"] == "acento" and not pz.get("protagonista"):
            raise X.m3.Falla("M3D2", "pieza «%s»: el acento es solo del `protagonista` (este trazo no lo es): usa bien, medio, mal o texto" % pz["id"])


def tramos(pz):
    return [[(q[0], q[1], False) for q in pz["puntos"]]]


def centro(pz, G):
    P = pz["puntos"]
    return P[len(P) // 2][0], P[len(P) // 2][1]


def punto_local(pz, s):
    """(x, y) del trazo a s unidades de su inicio."""
    return MV.en_cadena([[q[0], q[1], q[2], 0] for q in pz["puntos"]], s)[:2]
