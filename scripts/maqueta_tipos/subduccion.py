"""Pieza «subduccion»: un bloque-diagrama genérico de la Tierra cortada (esquema, no a escala), centrado en `lugar` y
orientado por `rumbo` (u: del mar hacia la tierra, el sentido en que entra la placa oceánica; v: a su izquierda, a lo largo
de la fosa). Todo en METROS de maqueta × `tamano`; z es la altura sobre el nivel del mar del bloque (negativa hacia abajo).

- EL BLOQUE: u de −L1 (el canto del mar) a L2 (el canto de la tierra) con la FOSA en u = 0, v de −WV (la CARA DEL CORTE, la
  que se ve de frente) a +WV, y D de hondo. Se apoya en el suelo del mundo: la tapa queda D más arriba.
- La PLACA OCEÁNICA: su techo `techo(u)` (hondura bajo el mar) es el fondo del mar hasta la fosa, se dobla y baja con
  `angulo_grados` (ilustrativo); grosor TP. La PLACA CONTINENTAL va del suelo hasta TC (o hasta la placa, en la punta).
  La CUÑA DE MANTO queda entre la continental y la placa; el manto, debajo.
- LA FILA: los conos van sobre donde el techo de la placa pasa por Z100 (un nivel sin número), a lo largo de v; el primero
  queda partido por la cara del corte (se ve su conducto).
- La pieza PUBLICA su relieve (`_alturas`: la tapa del bloque, con el mar a ras y los conos) y sus lugares: fosa,
  placa-oceanica, placa-continental, manto, placa-100, cono y fila (manto y placa-100, 4 m delante de la cara del corte:
  la cámara los mira con `mira_lev_m`) y placa (a media pendiente, sobre la banda de la placa que baja, delante del corte:
  publica ahí un descanso de 8 × 5 m a la altura de la placa para que su marca quede encima). `resaltar` con `pieza` + `elemento` aviva cada uno (el índice, en ELEMENTOS).
La misma cuenta del corte vive en video/maqueta/piezas/subduccion.js (techo, tierra, perfil de cono).
Resuelta: {x, y, rumbo, tamano, angulo, ta, u_arco, z100, conos [[u, v, R, H]], flechas, magma, semilla, elementos}."""
import math

from maqueta_tipos import _relieve as RL

L1, L2, WV, D = 600.0, 1300.0, 450.0, 600.0     # el bloque (m de maqueta)
W0, DIP, FW = 45.0, 55.0, 110.0                  # el mar, lo que se hunde la fosa y su ancho del lado del mar
UCOSTA = 170.0                                   # donde la costa sale del agua
TC, TP, BEND = 150.0, 90.0, 150.0                # grosor de la continental, de la oceánica y largo del doblez
Z100 = 330.0                                     # el nivel bajo la fila (sin número: «unos 100 km» en la voz, no aquí)
UC = (L2 - L1) / 2.0                             # el centro del bloque en u (ahí cae `lugar`)
RC = 0.1                                         # el cráter (fracción del radio)
ELEMENTOS = ("fosa", "placa-oceanica", "placa-continental", "manto", "placa-100", "cono", "fila", "placa")
NOMBRES = {"fosa": "Fosa", "placa-oceanica": "Placa oceánica", "placa-continental": "Placa continental", "manto": "Manto",
           "placa-100": "La placa bajo la fila", "cono": "Cono", "fila": "Fila de volcanes",
           "placa": "La placa que baja"}
UPLACA = 0.5                                     # `placa`: a qué fracción del camino de la fosa a la fila (media pendiente)


def liso(a, b, x):
    v = min(1.0, max(0.0, (x - a) / (b - a)))
    return v * v * (3 - 2 * v)


def techo(u, ta):
    """La hondura (m bajo el mar, positiva) del techo de la placa oceánica en u."""
    if u <= 0:
        return W0 + DIP * math.exp(-(u / FW) ** 2)
    return W0 + DIP + ta * (u - BEND * (1 - math.exp(-u / BEND)))


def fase(semilla):
    return (semilla * 0.6180339887 % 1.0) * 2 * math.pi


def tierra(u, v, ph):
    """La altura de la tierra (m sobre el mar) pasada la costa: sube suave tierra adentro, con lomas."""
    if u < UCOSTA:
        return 0.0
    return 22.0 * liso(UCOSTA, UCOSTA + 260, u) + 6.0 * math.sin(u / 95.0 + ph) * math.sin(v / 140.0 + 1.3 * ph) * liso(UCOSTA + 40, UCOSTA + 240, u)


def arco(ta, r):
    """Dónde va la fila: la u en que el techo de la placa llega a Z100 (con lugar para el cono en tierra y en el bloque)."""
    a, b = 0.0, 5000.0
    for _ in range(60):
        m = (a + b) / 2
        if techo(m, ta) < Z100:
            a = m
        else:
            b = m
    return min(max(a, UCOSTA + 1.4 * r), L2 - 1.6 * r)


def azar(i, k):
    x = math.sin(i * 127.1 + k * 311.7) * 43758.5453
    return x - math.floor(x)


def conos(n, ua, sem):
    """[[u, v, R, H], …]: el primero, partido por la cara del corte (v = −WV)."""
    r = min(88.0, max(34.0, 0.62 * 2 * WV / n))
    sp = (2 * WV - r) / max(1, n - 1)
    out = []
    for i in range(n):
        h1, h2, h3 = azar(sem + i, 1), azar(sem + i, 2), azar(sem + i, 3)
        ri = r * (0.86 + 0.24 * h1) if i else r
        hi = ri * (1.1 + 0.3 * h2)
        u = ua if i == 0 else ua + (h3 - 0.5) * 0.3 * r
        out.append([round(u, 2), round(-WV + i * sp, 2), round(ri, 2), round(hi, 2)])
    return out


def perfil(x):
    """La forma del cono (0–1 de su alto) a la distancia x (fracción del radio): empinado, cóncavo, con cráter."""
    if x >= 1:
        return 0.0
    if x < RC:
        return (1 - RC) ** 1.55 - 0.12 * (1 - (x / RC) ** 2)
    return (1 - x) ** 1.55


def alto_tapa(u, v, p):
    """La tapa del bloque (m sobre el mar): el mar a ras (0), la tierra y los conos."""
    h = max(0.0, tierra(u, v, p["_ph"])) if u >= UCOSTA else 0.0
    for cu, cv, R, H in p["conos"]:
        x = math.hypot(u - cu, v - cv) / R
        if x < 1:
            h = max(h, tierra(u, v, p["_ph"]) + H * perfil(x))
    return h


def resolver(p, X, que):
    l = X.lugar(p["lugar"], que + " → lugar")
    ang = float(p["angulo_grados"])
    ta = math.tan(math.radians(ang))
    r = {"x": round(l["x"], 2), "y": round(l["y"], 2), "rumbo": float(p["rumbo"]), "tamano": float(p["tamano"]),
         "angulo": ang, "ta": ta, "semilla": int(p["semilla"]), "flechas": bool(p["flechas"]), "magma": bool(p["magma"]),
         "fondo": str(p.get("fondo") or "campo"), "manto_brillo": float(p.get("manto_brillo", 0.4))}
    n = int(p["conos"])
    r0 = min(88.0, max(34.0, 0.62 * 2 * WV / n))
    ua = arco(ta, r0)
    r["u_arco"] = round(ua, 2)
    r["z100"] = round(techo(ua, ta), 2)
    r["conos"] = conos(n, ua, r["semilla"])
    S = X.S
    um = float(getattr(S, "unidad_m", 1.0) or 1.0)
    k = r["tamano"] / um
    a = math.radians(r["rumbo"])
    ux, uy = math.cos(a), math.sin(a)
    ph = fase(r["semilla"])

    def mundo(u, v):
        uu = u - UC
        return [r["x"] + (uu * ux - v * uy) * k, r["y"] + (uu * uy + v * ux) * k]

    def local(x, y):
        dx, dy = (x - r["x"]) / k, (y - r["y"]) / k
        return dx * ux + dy * uy + UC, -dx * uy + dy * ux

    # el relieve: la tapa del bloque (sobre el suelo del mundo: D + la tapa)
    q = dict(r, _ph=ph)
    esq = [mundo(-L1, -WV), mundo(L2, -WV), mundo(L2, WV), mundo(-L1, WV)]
    xs, ys = [c[0] for c in esq], [c[1] for c in esq]
    pol = [c for e in esq for c in e]

    def f(x, y):
        u, v = local(x, y)
        if u < -L1 - 1 or u > L2 + 1 or abs(v) > WV + 1:
            return 0.0
        return (D + alto_tapa(u, v, q)) * k

    r["_alturas"] = [RL.malla([min(xs), min(ys), max(xs), max(ys)], 97, 97, f, pol)]
    # `placa`: a media pendiente, sobre la banda de la placa que baja, delante de la cara del corte. Para que su marca quede
    # sobre la banda (y no al pie del bloque) publica un descanso chico ahí, a la altura del medio de la placa.
    up = UPLACA * ua
    zp = D - techo(up, ta) - 0.28 * TP * math.hypot(1, ta * (1 - math.exp(-up / BEND)))
    r["u_placa"], r["z_placa"] = round(up, 2), round(zp - D, 2)
    r["_alturas"].append(RL.plano([c for e in (mundo(up - 4, -WV - 7), mundo(up + 4, -WV - 7), mundo(up + 4, -WV - 1.5), mundo(up - 4, -WV - 1.5)) for c in e], zp * k))

    # los lugares (y los elementos que `resaltar` aviva, en el mismo orden)
    c0 = r["conos"][0]
    sitios = {"fosa": (0.0, 0.0, 0.7), "placa-oceanica": (-L1 * 0.5, 0.0, 0.6),
              "placa-continental": (min(L2 - 120, ua + 280), 0.0, 0.6),
              "manto": (ua - 70, -WV - 4, 0.6), "placa-100": (ua, -WV - 4, 0.6),
              "cono": (c0[0], c0[1] + 0.3 * c0[2], 0.7), "fila": (ua, 0.0, 0.8), "placa": (up, -WV - 4, 0.7)}
    r["_lugares"], r["elementos"] = {}, []
    for i in ELEMENTOS:
        u, v, peso = sitios[i]
        x, y = mundo(u, v)
        r["_lugares"][i] = {"nombre": NOMBRES[i], "x": round(x, 2), "y": round(y, 2), "peso": peso}
        r["elementos"].append([round(x, 2), round(y, 2)])
    return r


def elemento(pz, x, y):
    """El elemento en (x, y) (el lugar de la pieza más cercano): su índice en ELEMENTOS."""
    es = pz["elementos"]
    return min(range(len(es)), key=lambda i: (es[i][0] - x) ** 2 + (es[i][1] - y) ** 2)


def centro(pz, G):
    return pz["x"], pz["y"]


def huella_m(pz):
    """Medio largo, medio ancho (m) y el rumbo en radianes (del mar a la tierra)."""
    k = pz.get("tamano", 1)
    return (L1 + L2) / 2 * k, WV * k, math.radians(pz.get("rumbo", 0))
