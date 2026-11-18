"""Pieza «lagocorte»: un lago en corte como bloque-diagrama (esquema, no a escala), centrado en `lugar` y orientado por
`rumbo` (u: de la orilla con la desembocadura hacia el lago abierto; v: a su izquierda). Todo en METROS de maqueta ×
`tamano`; z es la altura sobre el espejo del agua (negativa hacia abajo).

- EL BLOQUE: u de −UL (el canto de tierra) a UR (el canto del lago), v de −WV (la CARA DEL CORTE, la que se ve de frente) a
  +WV, y DB de hondo bajo el espejo. Se apoya en el suelo del mundo: el espejo queda DB − SUB más arriba.
- LA ORILLA: tierra a HT sobre el agua hasta UO, donde baja al lago y el fondo cae a DW (sin número: un esquema). Un RÍO
  (canal de ancho 2·WC centrado en v = VC) entra por la tierra y desemboca en UO; la barda lo cruza ahí.
- LOS PECES van en una franja pegada a la cara del corte, en la zona FU0–FU1 × FZ0–FZ1 (lejos de la barda y de la basura).
La pieza PUBLICA su relieve (`_alturas`: la tapa del bloque, con el agua a ras) y sus lugares: peces (delante de la cara
del corte, a media agua: publica ahí un descanso para que su marca quede a esa altura), barda, basura, rio, lago y orilla.
La misma cuenta del relieve vive en video/maqueta/piezas/lagocorte.js (h0, canal, alto).
Resuelta: {x, y, rumbo, tamano, peces, marcados, basura, barda, personas, semilla}."""
import math

from maqueta_tipos import _relieve as RL

UL, UR, WV, DB, DW, HT, UO = 26.0, 30.0, 11.0, 30.0, 24.0, 1.6, -9.0
VC, WC, DC, SUB = 2.0, 4.5, 2.2, 0.2
FU0, FU1, FZ0, FZ1 = 1.5, 28.5, -21.5, -2.5
UCEN = (UR - UL) / 2.0
NOMBRES = {"peces": "Los peces", "barda": "La barda", "basura": "La basura", "rio": "El río", "lago": "El lago",
           "orilla": "La orilla"}


def liso(a, b, x):
    v = min(1.0, max(0.0, (x - a) / (b - a)))
    return v * v * (3 - 2 * v)


def fase(semilla):
    return (semilla * 0.6180339887 % 1.0) * 2 * math.pi


def h0(u, v, ph):
    """La tierra y el fondo a lo largo de u (m sobre el espejo): la orilla a HT, el talud y el fondo del lago."""
    return (HT - (HT + 0.6) * liso(UO - 2.5, UO, u) - (DW - 0.6) * liso(UO, UO + 12, u)
            + 0.15 * math.sin(u / 2.3 + ph) * math.sin(v / 3.1 + ph) * (1 - liso(UO - 3, UO - 1, u))
            + 0.5 * math.sin(u / 3.1 + ph) * math.sin(v / 2.7 + 0.7 * ph) * liso(UO + 2, UO + 8, u))


def canal(v):
    d = abs(v - VC)
    if d < WC:
        return -DC * (1 - (d / WC) ** 2)
    return HT * liso(WC, WC + 1.4, d)


def alto(u, v, ph):
    return min(h0(u, v, ph), canal(v))


def resolver(p, X, que):
    n, m = int(p["peces"]), int(p["marcados"])
    if m > n:
        raise X.m3.Falla("M3D2", "%s: `marcados` (%d) no puede pasar de `peces` (%d)" % (que, m, n))
    l = X.lugar(p["lugar"], que + " → lugar")
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "peces": n, "marcados": m, "basura": float(p["basura"]), "barda": bool(p["barda"]),
         "personas": int(p["personas"]), "semilla": int(p["semilla"])}
    S = X.S
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    ph = fase(r["semilla"])

    def mundo(u, v):
        uu = u - UCEN
        return [r["x"] + (uu * ux - v * uy) * k, r["y"] + (uu * uy + v * ux) * k]

    def local(x, y):
        dx, dy = (x - r["x"]) / k, (y - r["y"]) / k
        return dx * ux + dy * uy + UCEN, -dx * uy + dy * ux

    esq = [mundo(-UL, -WV), mundo(UR, -WV), mundo(UR, WV), mundo(-UL, WV)]
    xs, ys = [c[0] for c in esq], [c[1] for c in esq]
    pol = [c for e in esq for c in e]

    def f(x, y):
        u, v = local(x, y)
        if u < -UL - 0.5 or u > UR + 0.5 or abs(v) > WV + 0.5:
            return 0.0
        return (DB - SUB + max(0.0, alto(u, v, ph))) * k

    r["_alturas"] = [RL.malla([min(xs), min(ys), max(xs), max(ys)], 113, 45, f, pol)]
    # `peces`: delante de la cara del corte, a media agua de la zona de los peces (un descanso chico a esa altura)
    up, zp = (FU0 + FU1) / 2.0, (FZ0 + FZ1) / 2.0
    r["_alturas"].append(RL.plano([c for e in (mundo(up - 4, -WV - 6), mundo(up + 4, -WV - 6), mundo(up + 4, -WV - 1.5),
                                                mundo(up - 4, -WV - 1.5)) for c in e], (DB - SUB + zp) * k))
    sitios = {"peces": (up, -WV - 3.0, 0.8), "barda": (UO - 0.2, VC, 0.7), "basura": (UO - 6.0, VC, 0.7),
              "rio": (-UL + 4.0, VC, 0.5), "lago": (UR - 10.0, 0.0, 0.6), "orilla": (UO - 7.0, VC - WC - 3.5, 0.5)}
    r["_lugares"] = {}
    for i, (u, v, peso) in sitios.items():
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": NOMBRES[i], "x": round(x, 2), "y": round(y, 2), "peso": peso}
    return r


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes (de la orilla al lago)."""
    k = pz.get("tamano", 1)
    return (UL + UR) / 2 * k, WV * k, math.radians(pz.get("rumbo", 0))
