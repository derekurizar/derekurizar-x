"""Evento «magma»: sobre una pieza `subduccion`, el manto de encima de la placa (la cuña, sobre placa-100) se enciende,
una gota de magma sube por el conducto del cono partido hasta su cráter, que se enciende en el acento; con `fila`, después
se encienden uno tras otro los cráteres del resto de la fila (paralela a la fosa) y quedan encendidos.

Usa la misma cuenta del corte que la pieza (maqueta_tipos/subduccion.py y video/maqueta/piezas/subduccion.js): el evento
copia de la pieza resuelta su centro, rumbo, tamano, la inclinación (ta), la u de la fila y los conos. Las fases (las
MISMAS en magma.js) van en fracciones de `dur`; la secuencia es didáctica: ni velocidad ni duración del ascenso.
Resuelto: {pieza, x, y, rumbo, tamano, k, ta, u_arco, conos, semilla, fila, orden}."""
import math

from maqueta_tipos import subduccion as SB

# las fases (fracción de dur): [manto encendido, ascenso, cráter del frente]; con fila, el resto hasta 1
FASES = {False: (0.25, 0.2, 0.85, 0.82, 1.0), True: (0.15, 0.12, 0.5, 0.48, 0.58)}


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz or pz.get("tipo", "subduccion") != "subduccion" or "conos" not in pz:
        raise X.m3.Falla("M3D2", "%s: `pieza` tiene que ser una subduccion (el magma sube por su conducto)" % que)
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    tam = float(pz["tamano"])
    orden = e.get("orden", "frente-fondo")
    if orden not in ("frente-fondo", "fondo-frente"):
        raise X.m3.Falla("M3D2", "%s: `orden` es frente-fondo o fondo-frente" % que)
    return {"pieza": pid, "x": pz["x"], "y": pz["y"], "rumbo": float(pz["rumbo"]), "tamano": tam, "k": tam / um,
            "ta": pz["ta"], "u_arco": pz["u_arco"], "conos": pz["conos"], "semilla": int(pz["semilla"]),
            "fila": bool(e.get("fila", False)), "orden": orden}


def _mundo(e, u, v):
    a = math.radians(e["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    uu = u - SB.UC
    return e["x"] + (uu * ux - v * uy) * e["k"], e["y"] + (uu * uy + v * ux) * e["k"]


def _secuencia(e):
    n = len(e["conos"])
    rest = list(range(1, n))
    return rest if e["orden"] == "frente-fondo" else rest[::-1]


def puntos(e, u, G):
    """Dónde pasa: el manto encendido, la gota que sube por el corte, el cráter del frente y, con fila, el que se enciende."""
    a1, b0, b1, c0, c1 = FASES[e["fila"]]
    cono = e["conos"][0]
    um = e["u_arco"] - 25
    if u < b0:
        return [_mundo(e, um, -SB.WV - 4)]
    if u < b1:
        f = (u - b0) / (b1 - b0)
        return [_mundo(e, um + (cono[0] - um) * f, -SB.WV - 4)]
    if u < c1 or not e["fila"]:
        return [_mundo(e, cono[0], cono[1] + 0.3 * cono[2])]
    seq = _secuencia(e)
    if not seq:
        return [_mundo(e, cono[0], cono[1])]
    j = min(len(seq) - 1, int((u - c1) / max(1e-6, 1 - c1) * len(seq)))
    c = e["conos"][seq[j]]
    return [_mundo(e, c[0], c[1])]


def origen(e, G):
    return _mundo(e, e["u_arco"] - 25, -SB.WV - 4)
