"""Evento «hundir»: sobre una pieza `subduccion`, la placa oceánica avanza y baja (chevrones que corren por la placa en la
cara del corte, de la fosa hacia el manto) y, a la altura de placa-100, suelta gotas de agua que suben a la cuña de
manto. Esquema genérico: ni velocidad ni ángulo son datos.

La geometría es la de la pieza (scripts/maqueta_tipos/subduccion.py): el módulo (video/maqueta/eventos/hundir.js) la
lleva al mundo con el mismo centro, `rumbo` y `tamano`.
Resuelto: {pieza, fx, fy, rumbo, tamano, ta, ua, semilla, agua, vel, foco [x, y], boca [x, y]}."""
import math

from maqueta_tipos import subduccion as SB


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz or pz.get("tipo") != "subduccion":
        raise X.m3.Falla("M3D2", "%s: `pieza` tiene que ser una subduccion (la placa que baja es la suya)" % que)
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = float(pz["tamano"]) / um
    a = math.radians(float(pz["rumbo"]))
    ux, uy = math.cos(a), math.sin(a)

    def mundo(u, v):
        uu = u - SB.UC
        return [round(pz["x"] + (uu * ux - v * uy) * k, 2), round(pz["y"] + (uu * uy + v * ux) * k, 2)]

    return {"pieza": pid, "fx": pz["x"], "fy": pz["y"], "rumbo": float(pz["rumbo"]), "tamano": float(pz["tamano"]),
            "ta": pz["ta"], "ua": pz["u_arco"], "semilla": int(pz["semilla"]),
            "agua": bool(e.get("agua", True)), "vel": float(e.get("vel", 1.0)),
            "foco": mundo(pz["u_arco"] - 60, -SB.WV - 4), "boca": mundo(0.0, -SB.WV - 4)}


def puntos(e, u, G):
    """Primero la placa que entra por la fosa; desde el primer tercio, también donde suelta el agua."""
    p = [tuple(e["boca"])]
    if u > 0.3:
        p.append(tuple(e["foco"]))
    return p


def origen(e, G):
    return tuple(e["boca"])
