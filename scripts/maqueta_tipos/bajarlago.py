"""Evento «bajarlago»: el nivel de una `orillalago` baja. El agua se retira hacia el lago y deja al aire una franja de
lodo (con charcos que se secan) y el tul queda fuera del agua: pasa de verde a pardo y se dobla. Ilustrativo: no dibuja
metros ni cuenta juncos.

Geometría (la misma de video/maqueta/piezas/orillalago.js): u hacia el lago desde la línea del agua con el lago lleno
(`lugar` de la pieza), v a su izquierda; METROS × `tamano`. Con `baja` = 1 la orilla del agua se va U_MAX m mar adentro
(con su borde irregular); el tular del evento ocupa de TU0 a TU1 (el mismo trecho que el de la pieza).

Resuelto: {pieza, x, y, rumbo, tamano, k, seco0, tul, de, baja, seca, semilla}. `cerrar`: los bajarlago de una misma pieza
se encadenan por t (sin `de`, empieza donde dejó el anterior; 0 el primero) y comparten el tular del primero (tul, semilla)."""
import math

U_MAX = 44.0        # cuánto se retira el agua con baja = 1 (m; ilustrativo, sin medida)
SECO_M = 24.0       # el `seco` de la pieza (orillalago.js): el agua ya retirada antes del evento
TU0 = 5.0           # donde empieza el tular (m mar adentro)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no está en mundo.piezas (bajarlago baja el agua de esa orillalago)" % (que, pid))
    if pz.get("tipo") not in (None, "orillalago"):
        raise X.m3.Falla("M3D2", "%s: «%s» es %s; bajarlago necesita una orillalago" % (que, pid, pz.get("tipo")))
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    tam = _num(pz.get("tamano")) or 1.0
    if (_num(pz.get("tul")) or 0) > 0.01:
        X.avisos.append("%s: la orillalago «%s» tiene su propio tul (%.2f), que no se seca: ponlo en 0 (el tular lo dibuja bajarlago con `tul`)" % (que, pid, float(pz["tul"])))
    if (_num(pz.get("aves")) or 0) > 0 or (_num(pz.get("cayucos")) or 0) > 0:
        X.avisos.append("%s: la orillalago «%s» tiene aves o cayucos junto a la orilla: al bajar el agua quedarían sobre el lodo; ponlos en 0" % (que, pid))
    de = _num(e.get("de"))
    return {"pieza": pid, "x": float(pz["x"]), "y": float(pz["y"]), "rumbo": float(pz.get("rumbo", 0) or 0), "tamano": tam,
            "k": tam / um, "seco0": max(0.0, min(1.0, _num(pz.get("seco")) or 0.0)),
            "tul": max(0.0, min(1.0, float(e.get("tul", 0.8)))), "de": de,
            "baja": max(0.0, min(1.0, float(e["baja"]))), "seca": max(0.0, min(1.0, float(e.get("seca", 0.8)))),
            "semilla": int(e.get("semilla", 1) or 1)}


def cerrar(lista, X):
    por = {}
    for e in lista:
        por.setdefault(e["pieza"], []).append(e)
    for pid, evs in por.items():
        evs.sort(key=lambda e: float(e["t"]))
        prev = None
        for e in evs:
            if e["de"] is None:
                e["de"] = prev["baja"] if prev else 0.0
            e["de"] = max(0.0, min(1.0, float(e["de"])))
            if prev:
                e["tul"], e["semilla"] = prev["tul"], prev["semilla"]
                if abs(e["de"] - prev["baja"]) > 1e-3:
                    X.avisos.append("bajarlago en t=%.2f sobre «%s»: empieza en %.3f y el anterior dejó %.3f (sin `de`, sigue donde quedó)" % (float(e["t"]), pid, e["de"], prev["baja"]))
            if e["baja"] < e["de"]:
                X.avisos.append("bajarlago en t=%.2f sobre «%s»: `baja` (%.2f) es menor que `de` (%.2f): el agua solo baja, se queda en %.2f" % (float(e["t"]), pid, e["baja"], e["de"], e["de"]))
                e["baja"] = e["de"]
            prev = e


def _frente(e, f):
    """La orilla del agua (m mar adentro) con el nivel f (0–1)."""
    return max(SECO_M * e.get("seco0", 0.0), U_MAX * f)


def _mundo(e, u, v):
    a = math.radians(e["rumbo"])
    ux, uy, k = math.cos(a), math.sin(a), e["k"]
    return (e["x"] + (u * ux - v * uy) * k, e["y"] + (u * uy + v * ux) * k)


def puntos(e, u, G):
    """La orilla del agua que avanza (en tres puntos a lo largo de la orilla) y el tular que queda al aire."""
    f = e["de"] + (e["baja"] - e["de"]) * u
    U = _frente(e, f)
    pts = [_mundo(e, U, v) for v in (-60.0, 40.0, 120.0)]
    if U > TU0:
        pts.append(_mundo(e, (TU0 + U) / 2, 110.0))
    return pts


def origen(e, G):
    return _mundo(e, _frente(e, e["de"]), 40.0)
