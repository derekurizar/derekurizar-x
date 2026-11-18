"""Pieza «doselcuadricula»: un parche de selva tropical de tierras bajas visto de cerca y desde arriba (copas densas de varios
verdes, emergentes, sotobosque oscuro) con una cuadrícula fina de `celdas_lado` × `celdas_lado` cuadros de `celda_m` metros
encima; cada cuadro puede cambiar de estado en un segundo dado (`cuadros`: «f-c:estado@t») y teñirse como bosque, pérdida
o rebrote. Genérico: sin especies, sin gente, sin máquinas, sin causa ni actor.

- Centrada en `lugar` y girada por `rumbo` (u: a lo largo de las columnas, hacia `rumbo`; v: a su izquierda). La fila 1 es
  la del lado +v (al norte con rumbo 0) y la columna 1 la del lado −u (al oeste con rumbo 0).
- PUBLICA sus lugares (`_lugares`; también «<id>.<lugar>»): «c-<fila>-<col>» (el centro de cada cuadro) y «centro».
- `elemento(pz, x, y)`: el cuadro en (x, y) (para `resaltar` con `elemento`: el borde del cuadro se enciende en el acento).
Resuelta: {x, y, rumbo, n, celda (unidades), celda_m, densidad, emergentes, cuadricula, cuadricula_desde, tinte, semilla,
cambios: [[i, estado, t]]} (i = (fila − 1)·n + col − 1, en orden de t)."""
import math
import re

ESTADOS = ("bosque", "tala", "fuego", "quemado", "viento", "rebrote")
PATRON = re.compile(r"^\s*(?:c-)?(\d+)-(\d+)\s*:\s*([a-z]+)\s*(?:@\s*(\d+(?:\.\d+)?))?\s*$")


def _ejes(r):
    a = math.radians(r["rumbo"])
    return math.cos(a), math.sin(a)


def _centro_celda(r, f, c):
    """El centro del cuadro (fila f, columna c; desde 1), en unidades de la escena."""
    n, k = r["n"], r["celda"]
    u, v = (c - (n + 1) / 2) * k, ((n + 1) / 2 - f) * k
    ux, uy = _ejes(r)
    return r["x"] + u * ux - v * uy, r["y"] + u * uy + v * ux


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    n = int(p["celdas_lado"])
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "n": n,
         "celda_m": float(p["celda_m"]), "celda": float(p["celda_m"]) / um, "densidad": float(p["densidad"]),
         "emergentes": float(p["emergentes"]), "cuadricula": bool(p["cuadricula"]),
         "cuadricula_desde": float(p["cuadricula_desde"]), "tinte": float(p["tinte"]), "semilla": int(p["semilla"])}
    cambios = []
    for txt in p.get("cuadros") or []:
        m = PATRON.match(str(txt).lower())
        if not m:
            raise X.m3.Falla("M3D2", "%s: «%s» no se entiende: cada cuadro va como «fila-col:estado@segundo» (p. ej. «2-3:fuego@4.5»)" % (que, txt))
        f, c, est, t = int(m.group(1)), int(m.group(2)), m.group(3), float(m.group(4) or 0)
        if not (1 <= f <= n and 1 <= c <= n):
            raise X.m3.Falla("M3D2", "%s: «%s»: la cuadrícula va de 1-1 a %d-%d" % (que, txt, n, n))
        if est not in ESTADOS:
            raise X.m3.Falla("M3D2", "%s: «%s»: el estado es uno de %s" % (que, txt, ", ".join(ESTADOS)))
        if t > 600:
            raise X.m3.Falla("M3D2", "%s: «%s»: el segundo va de 0 a 600" % (que, txt))
        cambios.append([(f - 1) * n + (c - 1), est, t])
    cambios.sort(key=lambda q: (q[2], q[0]))
    r["cambios"] = cambios
    r["_lugares"] = {"centro": {"nombre": "Centro de la cuadrícula", "x": r["x"], "y": r["y"], "peso": 0.4}}
    for f in range(1, n + 1):
        for c in range(1, n + 1):
            x, y = _centro_celda(r, f, c)
            r["_lugares"]["c-%d-%d" % (f, c)] = {"nombre": "Cuadro %d-%d" % (f, c), "x": round(x, 2), "y": round(y, 2), "peso": 0.3}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def elemento(pz, x, y):
    """El cuadro en (x, y) (el más cercano si cae fuera): su índice (fila − 1)·n + col − 1."""
    ux, uy = _ejes(pz)
    dx, dy = x - pz["x"], y - pz["y"]
    u, v = dx * ux + dy * uy, -dx * uy + dy * ux
    n, k = pz["n"], pz["celda"]
    c = min(n, max(1, int(math.floor(u / k + n / 2)) + 1))
    f = min(n, max(1, int(math.floor(n / 2 - v / k)) + 1))
    return (f - 1) * n + (c - 1)


def huella_m(pz):
    """Medio lado (m) del parche de selva (la cuadrícula más su orla de bosque) y el rumbo en radianes."""
    h = pz.get("celda_m", 30) * (pz.get("n", 5) / 2 + 0.8)
    return h, h, math.radians(pz.get("rumbo", 0))
