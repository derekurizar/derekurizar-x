"""Evento «cerrarcalle»: el domingo de paseo sobre una `avenidareforma`. En un TRAMO de la vía principal (entre dos cruces)
aparecen vallas atravesadas en las dos calzadas, el `flujo` que corría por ella sale y las dos calzadas se llenan de gente
que camina, corre y pedalea en los dos sentidos. Ilustrativo: la fuente dice que los domingos se cierran «algunos puntos»
a los carros, no cuáles ni con qué vallas (las vallas, el tramo y la cantidad de gente son genéricos).

El TRAMO (unidades de la escena, sobre el eje del arriate que publica la pieza: `eje`, `sec`, `cruces`):
  - su centro: el punto del eje más cercano a `lugar` (sin él, el medio del eje);
  - su largo: `largo_m`; cada extremo se ajusta al cruce más cercano (a menos de 120 m), del lado de adentro, para que la
    valla quede justo pasando la calle que cruza y esa calle siga abierta.
Las VALLAS van en los extremos del tramo y a los dos lados de cada cruce de adentro, atravesando las dos calzadas.

Resuelto: {pieza, flujo, s0, s1, eje, sec (las filas del eje que cubren el tramo y su margen), cs (s de cada fila),
barreras: [s], ancho_via, personas, bicicletas, vallas, gente_tamano, semilla, cx, cy}."""
import math

OFF = 10.0          # m de la valla al centro del cruce (deja pasar la calle que cruza)


def _num(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz or pz.get("tipo") != "avenidareforma":
        raise X.m3.Falla("M3D2", "%s: «%s» no es una pieza avenidareforma de mundo.piezas (cerrarcalle cierra la vía de esa pieza)" % (que, pid))
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    k = 1.0 / um
    eje, sec, cruces = pz["eje"], pz["sec"], pz.get("cruces") or []
    cs = [0.0]
    for a, b in zip(eje, eje[1:]):
        cs.append(cs[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = cs[-1]
    # ---- el centro del tramo
    sc = L / 2
    if e.get("lugar") is not None:
        l = X.lugar(e["lugar"], que + " → lugar")
        best = None
        for i in range(len(eje) - 1):
            a, b = eje[i], eje[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            d2 = dx * dx + dy * dy or 1e-9
            u = max(0.0, min(1.0, ((l["x"] - a[0]) * dx + (l["y"] - a[1]) * dy) / d2))
            d = math.hypot(a[0] + dx * u - l["x"], a[1] + dy * u - l["y"])
            if best is None or d < best[0]:
                best = (d, cs[i] + math.sqrt(d2) * u)
        sc = best[1]
    largo = max(80.0, min(L, (_num(e.get("largo_m"), 500.0)) * k))
    s0, s1 = max(6 * k, sc - largo / 2), min(L - 6 * k, sc + largo / 2)
    # ---- los extremos, al cruce más cercano (del lado de adentro)
    cr = [c[0] for c in cruces]
    near0 = [c for c in cr if abs(c - s0) < 120 * k]
    if near0:
        s0 = min(near0, key=lambda c: abs(c - s0)) + OFF * k
    near1 = [c for c in cr if abs(c - s1) < 120 * k and c + OFF * k > s0 + 60 * k]
    if near1:
        s1 = min(near1, key=lambda c: abs(c - s1)) - OFF * k
    if s1 - s0 < 60 * k:
        s0, s1 = max(6 * k, sc - 40 * k), min(L - 6 * k, sc + 40 * k)
    barreras = [s0, s1] + [s for c in cr if s0 + 25 * k < c < s1 - 25 * k for s in (c - OFF * k, c + OFF * k)]
    barreras = sorted(round(s, 2) for s in barreras) if e.get("vallas", True) else []
    # ---- las filas del eje que cubren el tramo (con margen): lo que viaja al motor
    i0 = max(0, next((i for i, s in enumerate(cs) if s >= s0 - 20 * k), 0) - 1)
    i1 = min(len(eje), next((i for i, s in enumerate(cs) if s > s1 + 20 * k), len(eje) - 1) + 2)
    mid = (s0 + s1) / 2
    j = min(range(len(cs)), key=lambda i: abs(cs[i] - mid))
    return {"pieza": pid, "flujo": e.get("flujo"), "s0": round(s0, 2), "s1": round(s1, 2),
            "eje": eje[i0:i1], "sec": sec[i0:i1], "cs": [round(s, 2) for s in cs[i0:i1]], "barreras": barreras,
            "ancho_via": float(pz.get("ancho_via", 10.5)), "k": k,
            "personas": int(_num(e.get("personas"), 30)), "bicicletas": int(_num(e.get("bicicletas"), 8)),
            "vallas": bool(e.get("vallas", True)),
            "gente_tamano": _num(e.get("gente_tamano"), float(pz.get("gente_tamano", 1.0) or 1.0)),
            "semilla": int(_num(e.get("semilla"), 1)), "cx": round(eje[j][0], 2), "cy": round(eje[j][1], 2)}


def _en(e, s):
    cs, eje = e["cs"], e["eje"]
    for i in range(len(cs) - 1):
        if cs[i] <= s <= cs[i + 1]:
            u = (s - cs[i]) / ((cs[i + 1] - cs[i]) or 1)
            return eje[i][0] + (eje[i + 1][0] - eje[i][0]) * u, eje[i][1] + (eje[i + 1][1] - eje[i][1]) * u
    return e["cx"], e["cy"]


def puntos(e, u, G):
    """Las vallas al principio; luego la gente que llena el tramo (sus dos extremos y el medio)."""
    if u < 0.3 and e["barreras"]:
        return [_en(e, s) for s in e["barreras"]]
    return [_en(e, e["s0"]), (e["cx"], e["cy"]), _en(e, e["s1"])]


def origen(e, G):
    return e["cx"], e["cy"]
