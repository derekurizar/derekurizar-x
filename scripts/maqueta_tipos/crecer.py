"""Evento «crecer»: una pila sube de una fracción de su alto a otra mientras dura el evento, capa por capa (objetos que
caen y se asientan). Se puede llamar varias veces sobre la misma pieza: crece con la voz, se detiene y sigue.

La pila se posa en el lugar de su `pieza` (o en `lugar`), con su huella (`ancho_m` a lo largo de `rumbo`, `fondo_m`) y
su `alto_m`: lo que el evento no dice lo toma de la pieza (las mismas claves) y, si no, los defectos. Las fracciones son
del ALTO de la pila: 0.17 de 30 m = 5.1 m. Ninguna medida se inventa aquí: quien la pide pone la que respalda la cifra.

Con una pieza `pila` (piezas/pila.js publica MAQ.PILA.pilas[id]) la pila dibuja su cuerpo: el evento le fija la fracción
de cada cuadro y solo dibuja lo que cae sobre su cima; su `alto_m` es el de la pila y el primer `de`, su `inicio`.
Resuelto: {pieza, pieza_tipo, x, y, rumbo, ancho_m, fondo_m, alto_m, de, a, inicio, caida, cuerpo, semilla}.
`cerrar`: los `crecer` de una misma pieza se encadenan por t (sin `de`, empieza donde dejó el anterior; 0 el primero),
comparten la huella del primero y no se pisan."""
import math

DEF = {"ancho_m": 60.0, "fondo_m": 40.0, "alto_m": 30.0}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def resolver(e, X, que):
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if not pz:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no está en mundo.piezas (crecer sube la pila de esa pieza)" % (que, pid))
    prev = [q for q in (getattr(X, "eventos", None) or []) if q.get("tipo") == "crecer" and q.get("pieza") == pid]
    if e.get("lugar") is not None:
        l = X.lugar(e["lugar"], que + " → lugar")
        x, y = l["x"], l["y"]
    elif _num(pz.get("x")) is not None and _num(pz.get("y")) is not None:
        x, y = float(pz["x"]), float(pz["y"])
    elif prev:                            # la misma pila de un crecer anterior (cerrar le copia la huella)
        x, y = prev[-1]["x"], prev[-1]["y"]
    else:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» (%s) no tiene un lugar: da `lugar` (dónde se apila)" % (que, pid, pz.get("tipo")))
    r = {"pieza": pid, "pieza_tipo": pz.get("tipo", ""), "x": round(x, 3), "y": round(y, 3)}
    # una pieza `pila` llama `largo_m` al lado de su rumbo y `ancho_m` al otro
    de_pieza = {"ancho_m": "largo_m", "fondo_m": "ancho_m", "alto_m": "alto_m"} if pz.get("tipo") == "pila" else {k: k for k in DEF}
    for k, d in DEF.items():
        v = _num(e.get(k))
        if v is None:
            v = _num(pz.get(de_pieza[k]))
        r[k] = round(v if v is not None and v > 0 else d, 3)
    rb = _num(e.get("rumbo"))
    r["rumbo"] = rb if rb is not None else (_num(pz.get("rumbo")) or 0.0)
    r["de"] = _num(e.get("de"))           # None: lo pone cerrar (donde dejó el anterior; en una pila, su `inicio`)
    r["inicio"] = _num(pz.get("inicio")) if pz.get("tipo") == "pila" else None
    r["a"] = max(0.0, min(1.0, float(e["a"])))
    r["caida"] = e.get("caida", True) is not False
    r["cuerpo"] = e.get("cuerpo", True) is not False
    r["semilla"] = int(e.get("semilla", 1) or 1)
    return r


def cerrar(lista, X):
    por = {}
    for e in lista:
        por.setdefault(e["pieza"], []).append(e)
    for pid, evs in por.items():
        evs.sort(key=lambda e: float(e["t"]))
        prev = None
        for e in evs:
            if e["de"] is None:
                e["de"] = prev["a"] if prev else (e.get("inicio") or 0.0)
            e["de"] = max(0.0, min(1.0, float(e["de"])))
            if prev:
                for k in ("x", "y", "rumbo", "ancho_m", "fondo_m", "alto_m"):
                    e[k] = prev[k]                   # una pila: la huella del primero
                if abs(e["de"] - prev["a"]) > 1e-3:
                    X.avisos.append("crecer en t=%.2f sobre «%s»: empieza en %.3f y el anterior dejó %.3f: la pila salta (sin `de`, sigue donde quedó)" % (float(e["t"]), pid, e["de"], prev["a"]))
                if float(e["t"]) < float(prev["t"]) + float(prev["dur"]) - 1e-6:
                    X.avisos.append("crecer en t=%.2f sobre «%s» empieza antes de que termine el anterior: manda el último que empezó" % (float(e["t"]), pid))
            if not prev and e.get("inicio") is not None and abs(e["de"] - e["inicio"]) > 1e-3:
                X.avisos.append("crecer en t=%.2f sobre la pila «%s»: empieza en %.3f y la pila arranca en %.3f (`inicio`): salta al empezar" % (float(e["t"]), pid, e["de"], e["inicio"]))
            prev = e


def puntos(e, u, G):
    return [(e["x"], e["y"])]


def origen(e, G):
    return e["x"], e["y"]
