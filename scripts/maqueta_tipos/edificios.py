"""Pieza «edificios»: los edificios del mundo extruidos con su altura (de un set de ciudad o de la receta de un esquema),
en metros. Resuelta: {edificios: [[altura_m, x0, y0, x1, y1, …]], destacado: índice | −1, nombres: {índice: nombre}}."""
from maqueta_tipos import _mundo as MU


def resolver(p, X, que):
    C = MU.capa(X, "edificios", que)
    nombres = C.get("nombres") or {}
    sel = [(i, e) for i, e in enumerate(C["edificios"]) if e[0] >= p["altura_min_m"]]
    if not sel:
        raise X.m3.Falla("M3D2", "%s: ningún edificio mide %g m o más (`altura_min_m`)" % (que, p["altura_min_m"]))
    r = {"edificios": [e for _, e in sel], "nombres": {str(k): nombres[str(i)] for k, (i, _) in enumerate(sel) if str(i) in nombres}, "destacado": -1}
    if p.get("destacar") is not None:
        l = X.lugar(p["destacar"], que + " → destacar")
        r["destacado"] = elemento(r, l["x"], l["y"])
    return r


def elemento(pz, x, y):
    """El edificio en (x, y) (el que lo contiene o, si ninguno, el de centro más cercano): su índice en pz["edificios"]."""
    mejor, dmin = 0, 1e18
    for i, e in enumerate(pz["edificios"]):
        pts = MU.pares(e, 1)
        if MU.dentro_pol(x, y, pts):
            return i
        cx, cy = MU.centroide(pts)
        d = (cx - x) ** 2 + (cy - y) ** 2
        if d < dmin:
            mejor, dmin = i, d
    return mejor


def centro(pz, G):
    i = pz.get("destacado", -1)
    return MU.centroide(MU.pares(pz["edificios"][i], 1)) if i >= 0 else MU.caja_de(G["R"])
