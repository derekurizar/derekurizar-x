"""Evento «verter»: sobre una pieza `drenajeorilla`, el agua residual corre en pulsos por los tubos: de cada casa conectada,
por su acometida y el colector, a los desagües crudos (que la sueltan turbia en la playa y abren en el lago una MANCHA que
crece hasta `mancha` y se queda) o a la planta (cuya salida suelta pulsos menos turbios, sin mancha). Ilustrativo: ni la
mancha ni los pulsos son una medida.

La geometría es la de la pieza (scripts/maqueta_tipos/drenajeorilla.py y video/maqueta/piezas/drenajeorilla.js): el módulo
(video/maqueta/eventos/verter.js) rehace sus casas y sus tubos con el mismo centro, `rumbo`, `tamano` y `semilla`.
Resuelto: {pieza, x, y, rumbo, tamano, semilla, np, corte, desagues, a_planta, sin_drenaje, mancha, vel, boca, centro, calle}."""
import math

U_CALLE = -60.0
U_BOCA = -2.5
SAL_V = 83.0
R_MIN, R_MAX = 12.0, 60.0   # radio de la mancha con mancha = 0 y = 1 (m × tamano; ilustrativo)


def _radio(m):
    return R_MIN + (R_MAX - R_MIN) * m


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz or pz.get("tipo") != "drenajeorilla":
        raise X.m3.Falla("M3D2", "%s: `pieza` tiene que ser una drenajeorilla (el agua corre por sus tubos)" % que)
    np_ = 0
    for p in X.piezas:
        if p.get("id") == pid:
            break
        if p.get("tipo") == "drenajeorilla":
            np_ += 1
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = float(pz.get("tamano", 1) or 1) / um
    a = math.radians(float(pz.get("rumbo", 0) or 0))
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        return [round(pz["x"] + (u * ux - v * uy) * k, 2), round(pz["y"] + (u * uy + v * ux) * k, 2)]

    des = list(pz.get("desagues") or [])
    m = max(0.0, min(1.0, float(e.get("mancha", 0.6))))
    if not des:
        X.avisos.append("%s: la drenajeorilla «%s» no tiene desagües crudos (a_planta ≈ 1): no se abre mancha, solo corre el agua a la planta" % (que, pid))
    g = des[0] if des else SAL_V
    R = _radio(m)
    return {"pieza": pid, "x": pz["x"], "y": pz["y"], "rumbo": float(pz.get("rumbo", 0) or 0), "tamano": float(pz.get("tamano", 1) or 1),
            "semilla": int(pz.get("semilla", 1)), "np": np_, "corte": float(pz["corte"]), "desagues": des,
            "a_planta": float(pz.get("a_planta", 0.3)), "sin_drenaje": float(pz.get("sin_drenaje", 0.35)),
            "mancha": m, "vel": float(e.get("vel", 1.0)),
            "boca": mundo(U_BOCA, g), "centro": mundo(0.5 * R + 1.0, g), "calle": mundo(U_CALLE, -30.0)}


def puntos(e, u, G):
    """Primero la calle y la boca (el agua que corre); desde la mitad, también la mancha que crece."""
    p = [tuple(e["calle"]), tuple(e["boca"])]
    if u > 0.5 and e.get("desagues"):
        p.append(tuple(e["centro"]))
    return p


def origen(e, G):
    return tuple(e["boca"])
