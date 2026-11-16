"""Pieza «falla»: la cadena de la traza (del set o dibujada) y su versión simplificada para el shader."""


def resolver(p, X, que):
    M3, S = X.m3, X.S
    lineas = []
    if p.get("puntos"):
        ln = [S.xy(q[0], q[1]) for q in p["puntos"]]
        if not all(S.dentro(x, y) for x, y in ln):
            raise M3.Falla("M3D2", "%s: hay puntos del trazo fuera de la caja del set %s" % (que, S.id))
        lineas.append(M3.suavizar(ln) if p.get("suave", True) else ln)
    for nombre in p.get("trazos") or []:
        hay = [t for t in S.fallas["trazos"] if t["nombre"] == nombre]
        if not hay:
            raise M3.Falla("M3D2", "%s: el trazo «%s» no está en el set %s (ver design/sets3d/%s/fallas.json → nombres)" % (que, nombre, S.id, S.id))
        lineas += [[S.xy(q[0], q[1]) for q in t["puntos"]] for t in hay]
    if not lineas:
        raise M3.Falla("M3D2", "%s: una falla necesita `trazos` (nombres del set) o `puntos` ([[lon, lat], …])" % que)
    cadena = M3.encadenar(lineas)
    return {"cadena": cadena, "largo_km": cadena[-1][2]}


def cerrar(fallas, X):
    """Tope del shader (FALLAS_MAX) y las cadenas simplificadas de todas juntas en NC_MAX puntos."""
    M3 = X.m3
    if len(fallas) > M3.FALLAS_MAX:
        raise M3.Falla("M3D2", "hay %d piezas `falla` y el motor dibuja hasta %d" % (len(fallas), M3.FALLAS_MAX))
    tol = 0.5
    while True:
        for f in fallas:
            f["simple"] = M3.simplificar(f["cadena"], tol)
        if sum(len(f["simple"]) for f in fallas) <= M3.NC_MAX:
            break
        tol *= 1.5


def tramos(pz):
    return [[(q[0], q[1], bool(q[3])) for q in pz["cadena"]]]


def centro(pz, G):
    return G["m3"].punto_en_s(pz["cadena"], pz["largo_km"] / 2)
