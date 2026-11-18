"""Evento «terremoto»: la sacudida sobre un escenario con edificios. Resuelve, en unidades de la escena, el CENTRO del daño
(`centro`; si no, el refugio, la plaza que publica la pieza, su `x, y` o el centro de sus edificios), el RADIO dentro del
cual se rompe lo que está en pie, los puntos que caen sí o sí (`lugares`) y el REFUGIO al que corre la gente (`refugio`;
si no, «<pieza>.plaza», la plaza del mundo o el centro).

Resuelto: {pieza, cx, cy, radio, caen: [[x, y], …], rx, ry, rr, intensidad, danos, polvo, personas, previo, semilla, usa}."""


def _intenta(X, ref, que):
    try:
        return X.lugar(ref, que)
    except Exception:
        return None


def _um(X):
    return float(getattr(X.S, "unidad_m", 1.0) or 1.0)


def _centro_pieza(pz):
    if not pz:
        return None
    if isinstance(pz.get("x"), (int, float)) and isinstance(pz.get("y"), (int, float)):
        return float(pz["x"]), float(pz["y"])
    eds = pz.get("edificios")
    if eds:
        xs, ys = [], []
        for e in eds:
            for k in range(1, len(e) - 1, 2):
                xs.append(e[k]); ys.append(e[k + 1])
        if xs:
            return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return None


def resolver(e, X, que):
    um = _um(X)
    pid = e["pieza"]
    pz = X.por_id.get(pid)
    if pz is None:
        raise X.m3.Falla("M3D2", "%s: la pieza «%s» no está en mundo.piezas (el terremoto sacude una pieza con edificios)" % (que, pid))
    plaza = _intenta(X, pid + ".plaza", que) or _intenta(X, "plaza", que)
    ref = _intenta(X, e["refugio"], que + " → refugio") if e.get("refugio") is not None else None
    if e.get("refugio") is not None and ref is None:
        X.lugar(e["refugio"], que + " → refugio")          # que la falla diga por qué
    cen = X.lugar(e["centro"], que + " → centro") if e.get("centro") is not None else None
    cp = _centro_pieza(pz)
    if cen:
        cx, cy = cen["x"], cen["y"]
    elif ref:
        cx, cy = ref["x"], ref["y"]
    elif plaza:
        cx, cy = plaza["x"], plaza["y"]
    elif cp:
        cx, cy = cp
    else:
        cx, cy = 0.0, 0.0
        X.avisos.append("%s: la pieza «%s» no dice dónde está: el terremoto se centra en (0, 0); pasa `centro`" % (que, pid))
    r = ref or plaza or {"x": cx, "y": cy}
    caen = []
    for i, l in enumerate(e.get("lugares") or []):
        q = X.lugar(l, "%s → lugares[%d]" % (que, i))
        caen.append([round(q["x"], 3), round(q["y"], 3)])
    radio = float(e.get("radio_m", 180)) / um
    for q in caen:
        if (q[0] - cx) ** 2 + (q[1] - cy) ** 2 > radio ** 2:
            X.avisos.append("%s: un lugar de `lugares` cae fuera de `radio_m` (%g m): ahí no se rompe nada; sube el radio" % (que, e.get("radio_m", 180)))
    personas = int(e.get("personas", 14))
    return {"pieza": pid, "cx": round(cx, 3), "cy": round(cy, 3), "radio": round(radio, 4), "caen": caen,
            "rx": round(r["x"], 3), "ry": round(r["y"], 3), "rr": round(float(e.get("radio_refugio_m", 22)) / um, 4),
            "intensidad": float(e.get("intensidad", 0.8)), "danos": float(e.get("danos", 0.6)),
            "polvo": e.get("polvo", True) is not False, "personas": personas, "previo": bool(e.get("previo", False)),
            "semilla": int(e.get("semilla", 1)), "usa": ["persona"] if personas else []}


def puntos(e, u, G):
    """El centro del daño y lo que cae sí o sí: el terremoto se lee si se ven los edificios que se rompen."""
    return [(e["cx"], e["cy"])] + [(q[0], q[1]) for q in e.get("caen", [])]


def origen(e, G):
    return e["cx"], e["cy"]
