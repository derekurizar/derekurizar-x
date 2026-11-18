"""Evento «correranios»: sobre una pieza coberturaceldas, el año corre de `de` a `a` durante `dur`; cada año que llega
apaga las celdas que perdieron cobertura ese año (lo dibuja la pieza) y un contador de año, en la capa 2D, lo dice.
Varios eventos sobre la misma pieza siguen donde quedó el anterior (el siguiente empieza en un año mayor).

Resuelto: {pieza, de, a, contador, pos, rotulo, queda, cifra_por_anio}. Los años mostrados (de..a) son cifras en
pantalla: `cifra_por_anio` es el prefijo del id verificado de cada uno («anio-» → anio-2001, anio-2002…; C3D5)."""


def resolver(e, X, que):
    pz = X.por_id.get(e["pieza"])
    if not pz or pz.get("tipo") != "coberturaceldas":
        raise X.m3.Falla("M3D2", "%s: `pieza` «%s» no es una pieza coberturaceldas de esta maqueta" % (que, e["pieza"]))
    de, a = int(e["de"]), int(e["a"])
    if a < de:
        raise X.m3.Falla("M3D2", "%s: el año corre hacia adelante (`a` %d ≥ `de` %d)" % (que, a, de))
    base = int(pz.get("anio_base", 2000))
    if de <= base:
        raise X.m3.Falla("M3D2", "%s: `de` (%d) va después del año base de «%s» (%d): ese año no tiene pérdida" % (que, de, e["pieza"], base))
    anios = pz.get("anios") or []
    if anios and a > max(anios) + 1:
        X.avisos.append("%s: «%s» no trae pérdidas después de %d; el contador llega a %d sin que se apague nada" % (que, e["pieza"], max(anios), a))
    return {"pieza": e["pieza"], "de": de, "a": a, "contador": e.get("contador", True) is not False,
            "pos": e.get("pos", "arriba"), "rotulo": e.get("rotulo") or "", "queda": e.get("queda", True) is not False,
            "cifra_por_anio": e.get("cifra_por_anio") or ""}


def cerrar(lista, X):
    """Los eventos de una misma pieza, en orden de t, no vuelven atrás en el año ni se pisan."""
    por = {}
    for e in sorted(lista, key=lambda e: e["t"]):
        por.setdefault(e["pieza"], []).append(e)
    for pid, evs in por.items():
        for p, q in zip(evs, evs[1:]):
            if q["de"] < p["a"]:
                raise X.m3.Falla("M3D2", "correranios sobre «%s»: el de t = %.2f empieza en %d, antes de %d, donde quedó el de t = %.2f"
                                 % (pid, q["t"], q["de"], p["a"], p["t"]))
            if q["t"] < p["t"] + p["dur"] - 1e-6:
                raise X.m3.Falla("M3D2", "correranios sobre «%s»: el de t = %.2f empieza antes de que termine el de t = %.2f (%.2f)"
                                 % (pid, q["t"], p["t"], p["t"] + p["dur"]))


def _celdas(e, G):
    pz = G["por_id"].get(e["pieza"]) or {}
    anios = pz.get("anios") or []
    ks = {k for k, a in enumerate(anios) if e["de"] <= a <= e["a"]}
    cs = [(c[0], c[1]) for c in pz.get("celdas") or [] if any(k in ks for k, _ in c[3])]
    if not cs:
        cs = [(c[0], c[1]) for c in pz.get("celdas") or []]
    paso = max(1, len(cs) // 60)
    return cs[::paso]


def puntos(e, u, G):
    """Las celdas que se apagan en el tramo de años (o todas): ≥ la mitad en cámara (M3D6)."""
    return _celdas(e, G)


def origen(e, G):
    cs = _celdas(e, G)
    if not cs:
        return None
    return sum(c[0] for c in cs) / len(cs), sum(c[1] for c in cs) / len(cs)
