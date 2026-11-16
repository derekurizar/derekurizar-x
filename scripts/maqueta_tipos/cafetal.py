"""Pieza «cafetal»: una ladera de cafetal en terrazas sobre el suelo del mundo: el polígono (`area`: una zona del mundo por
su id; o `puntos`: [x, y] en metros en un esquema) sube hacia `rumbo` hasta `pendiente_m` en `hileras` terrazas, cada una
con su hilera de cafetos y sus racimos de cereza (`maduras`: la parte roja, en el rojo del estilo). Resuelta: {poligono: [x0, y0,
…], hileras, pendiente_m, rumbo, maduras, semilla, personas, usa}. El relieve es de la pieza (el mundo sigue plano): un
actor que se quiera de pie en la terraza k (0 = la de abajo) va con `lev_m` = pendiente_m · k / hileras."""
from maqueta_tipos import _mundo as MU


def resolver(p, X, que):
    if (p.get("area") is None) == (p.get("puntos") is None):
        raise X.m3.Falla("M3D2", "%s: un cafetal lleva `area` (el id de una zona del mundo) o `puntos` (el polígono), una de las dos" % que)
    if p.get("puntos") is not None:
        if len(p["puntos"]) < 3:
            raise X.m3.Falla("M3D2", "%s: `puntos` necesita al menos 3" % que)
        pol = [v for ref in p["puntos"] for v in (lambda l: (l["x"], l["y"]))(X.lugar(ref, que))]
    else:
        Z = MU.capa(X, "zonas", que)["zonas"]
        pols = [MU.plano(z["puntos"]) for z in Z if z["id"] == p["area"]]
        if not pols:
            ids = [z["id"] for z in Z]
            raise X.m3.Falla("M3D2", "%s: «%s» no es una zona del mundo (hay: %s%s)" % (que, p["area"], ", ".join(ids[:12]), "…" if len(ids) > 12 else ""))
        pol = pols[0]
    xs, ys = pol[0::2], pol[1::2]
    if max(xs) - min(xs) < 20 or max(ys) - min(ys) < 20:
        raise X.m3.Falla("M3D2", "%s: el cafetal mide menos de 20 m de lado: no se lee como ladera" % que)
    r = {"poligono": [round(v, 1) for v in pol], "hileras": int(p["hileras"]), "pendiente_m": float(p["pendiente_m"]),
         "rumbo": float(p["rumbo"]), "maduras": float(p["maduras"]), "semilla": int(p["semilla"]), "personas": int(p["personas"])}
    if r["personas"]:
        r["usa"] = ["persona"]
    return r


def tramos(pz):
    pts = MU.pares(pz["poligono"])
    return [[(x, y, False) for x, y in pts + pts[:1]]]


def centro(pz, G):
    return MU.centroide(MU.pares(pz["poligono"]))
