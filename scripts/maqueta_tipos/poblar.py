"""Evento «poblar»: la orilla de una `orillalago` se llena de casas de verano y hoteles, lote a lote, de la fracción `de` a
la fracción `a` de los lotes de una franja paralela al agua. Ilustrativo: los lotes no cuentan edificios reales.

La FRANJA (unidades de la escena) sale de lo que la pieza publica, en este orden:
  1. `lugar` / `rumbo` del evento (el punto de la línea de agua en medio de la franja y hacia dónde queda la tierra);
  2. el `lugar` y el `rumbo` de la pieza (orillalago: su lugar es la línea del agua y su rumbo mira al lago: la tierra
     queda al revés); sin ellos, «<pieza>.linea-agua» y «<pieza>.agua-abierta».
  El fondo de la franja nunca pisa «<pieza>.camino».
Los lotes van en fila a lo largo de la orilla (`largo_m` × tamano), a `playa_m` del agua y con `fondo_m` de fondo; los
que caen a menos de 7 m (× tamano) del paso al «<pieza>.muelle», a lo largo de la orilla, se saltan.

Resuelto: {pieza, ox, oy, nx, ny, k (unidades por metro), lotes: [{x, y, w, d, hotel, rango, k}], n, de, a, epoca,
semilla}. `rango` = el orden en que brota (izquierda-derecha mirando desde el agua, centro-afuera o azar fijo).
`cerrar`: los `poblar` de una misma pieza se encadenan por t (sin `de`, empieza donde dejó el anterior; 0 el primero) y
comparten los lotes del primero."""
import math


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _hash(i, k):
    # el mismo azar fijo en Python y en JS no hace falta: el orden «azar» se resuelve aquí y viaja en `rango`
    x = math.sin(i * 127.1 + k * 311.7) * 43758.5453
    return x - math.floor(x)


def _pub(X, pid, nombre, que):
    ref = "%s.%s" % (pid, nombre)
    if ref in X.publicados or ref in (X.propios or {}):
        return X.lugar(ref, que)
    return None


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no está en mundo.piezas (poblar llena la orilla de esa pieza)" % (que, pid))
    um = float(getattr(X.S, "unidad_m", 1.0) or 1.0)
    tam = _num(pz.get("tamano")) or 1.0
    k = tam / um                                    # unidades de la escena por metro de la maqueta (× tamano)
    largo = float(e.get("largo_m", 300)) * k
    playa = float(e.get("playa_m", 16)) * k
    fondo = float(e.get("fondo_m", 34)) * k
    # ---- la franja: origen en la línea de agua y normal hacia tierra
    o = n = None
    if e.get("lugar") is not None:
        l = X.lugar(e["lugar"], que + " → lugar")
        o = (l["x"], l["y"])
    if _num(e.get("rumbo")) is not None:
        r = math.radians(float(e["rumbo"]))
        n = (math.cos(r), math.sin(r))
    elif _num(pz.get("rumbo")) is not None:          # orillalago: su rumbo mira al lago; la tierra, al revés
        r = math.radians(float(pz["rumbo"]))
        n = (-math.cos(r), -math.sin(r))
    if o is None and _num(pz.get("x")) is not None:
        o = (float(pz["x"]), float(pz["y"]))          # orillalago: su `lugar` es la línea del agua con el lago lleno
    la = _pub(X, pid, "linea-agua", que)
    aa = _pub(X, pid, "agua-abierta", que)
    if o is None and la:
        o = (la["x"], la["y"])
    if o is None:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no tiene un lugar: da `lugar` y `rumbo`" % (que, pid))
    if n is None and aa and math.hypot(o[0] - aa["x"], o[1] - aa["y"]) > 1e-6:
        dx, dy = o[0] - aa["x"], o[1] - aa["y"]
        L = math.hypot(dx, dy)
        n = (dx / L, dy / L)
    if n is None:
        n = (0.0, -1.0)
    ca = _pub(X, pid, "camino", que)
    if ca:                                          # la franja no pisa el camino
        dc = (ca["x"] - o[0]) * n[0] + (ca["y"] - o[1]) * n[1]
        if dc > playa + 12 * k:
            fondo = min(fondo, dc - playa - 8 * k)
    tg = (-n[1], n[0])                               # a la izquierda de quien mira a tierra desde el agua
    mu = _pub(X, pid, "muelle", que)
    s_mu = (mu["x"] - o[0]) * tg[0] + (mu["y"] - o[1]) * tg[1] if mu else None
    N = int(e.get("lotes", 16))
    w = largo / N
    hoteles = float(e.get("hoteles", 0.35))
    sem = int(e.get("semilla", 1) or 1)
    lotes = []
    for i in range(N):
        s = largo / 2 - w * (i + 0.5)                # de izquierda (s > 0) a derecha
        h = _hash(i + sem * 31, 3)
        d = fondo * (0.82 + 0.18 * _hash(i + sem * 31, 4))
        c = (o[0] + tg[0] * s + n[0] * (playa + d / 2), o[1] + tg[1] * s + n[1] * (playa + d / 2))
        if s_mu is not None and abs(s - s_mu) < 7 * k + w / 2:
            continue                                 # el paso público al muelle queda libre
        lotes.append({"x": round(c[0], 3), "y": round(c[1], 3), "s": round(s, 3), "w": round(w, 3), "d": round(d, 3),
                      "hotel": 1 if (h < hoteles and w / k >= 15) else 0, "k": i})
    if not lotes:
        raise X.m3.Falla("M3D2", "%s: no queda ningún lote en la orilla de «%s» (el muelle los tapa todos): sube `largo_m` o mueve `lugar`" % (que, pid))
    orden = e.get("orden", "izquierda-derecha")
    if orden == "centro-afuera":
        clave = lambda q: (abs(q["s"]), q["k"])
    elif orden == "azar":
        clave = lambda q: _hash(q["k"] + sem * 17, 9)
    else:
        clave = lambda q: -q["s"]
    for rg, q in enumerate(sorted(lotes, key=clave)):
        q["rango"] = rg
    epoca = e.get("epoca") or pz.get("epoca") or "hoy"
    if epoca not in ("antes", "hoy"):
        epoca = "hoy"
    de = _num(e.get("de"))
    a = max(0.0, min(1.0, float(e["a"])))
    return {"pieza": pid, "ox": round(o[0], 3), "oy": round(o[1], 3), "nx": round(n[0], 6), "ny": round(n[1], 6),
            "k": k, "lotes": lotes, "n": len(lotes), "de": de, "a": a, "epoca": epoca, "semilla": sem,
            "orden": orden, "personas": bool(e.get("personas", True))}


def cerrar(lista, X):
    por = {}
    for e in lista:
        por.setdefault(e["pieza"], []).append(e)
    for pid, evs in por.items():
        evs.sort(key=lambda e: float(e["t"]))
        prev = None
        for e in evs:
            if e["de"] is None:
                e["de"] = prev["a"] if prev else 0.0
            e["de"] = max(0.0, min(1.0, float(e["de"])))
            if prev:
                for k in ("ox", "oy", "nx", "ny", "k", "lotes", "n", "epoca", "semilla", "orden"):
                    e[k] = prev[k]                   # una orilla: los lotes del primero
                if abs(e["de"] - prev["a"]) > 1e-3:
                    X.avisos.append("poblar en t=%.2f sobre «%s»: empieza en %.3f y el anterior dejó %.3f (sin `de`, sigue donde quedó)" % (float(e["t"]), pid, e["de"], prev["a"]))
            if e["a"] < e["de"]:
                X.avisos.append("poblar en t=%.2f sobre «%s»: `a` (%.2f) es menor que `de` (%.2f): poblar solo suma, la orilla se queda en %.2f" % (float(e["t"]), pid, e["a"], e["de"], e["de"]))
                e["a"] = e["de"]
            prev = e


def _ventana(e):
    n0, n1 = int(round(e["de"] * e["n"])), int(round(e["a"] * e["n"]))
    return n0, n1


def puntos(e, u, G):
    """Los lotes que brotan en la fracción u (y el último que ya brotó)."""
    n0, n1 = _ventana(e)
    if n1 <= n0:
        return []
    r = n0 + min(n1 - n0 - 1, int(u * (n1 - n0)))
    return [(q["x"], q["y"]) for q in e["lotes"] if q["rango"] in (r, max(n0, r - 1))]


def origen(e, G):
    n0, n1 = _ventana(e)
    for q in e["lotes"]:
        if q["rango"] == n0:
            return q["x"], q["y"]
    return e["ox"], e["oy"]
