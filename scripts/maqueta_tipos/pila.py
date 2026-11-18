"""Pieza «pila»: un volumen («¿cuánto es eso?») puesto sobre un lugar conocido: basura mezclada, tierra o agua con la
planta de un rectángulo (`lugar` + `largo_m` × `ancho_m`, girado por `rumbo`) o de un polígono (`puntos`) y un alto final
`alto_m` en metros. Resuelta: {x, y (el centro, en unidades de la escena), rumbo, largo_m, ancho_m, alto_m, inicio,
material, acento, semilla, puntos (plano [x0, y0, …] en unidades de la escena) o None}. La planta y los metros los pasa
tal cual: el módulo los lleva a la escena con ctx.metros. El centro (M3D6/M3D9) es el de la planta."""
from maqueta_tipos import _mundo as MU


def resolver(p, X, que):
    rect = p.get("lugar") is not None
    if p.get("puntos") is not None:
        if rect:
            raise X.m3.Falla("M3D2", "%s: una pila lleva `lugar` con `largo_m` y `ancho_m`, o `puntos`, no las dos" % que)
        if len(p["puntos"]) < 3:
            raise X.m3.Falla("M3D2", "%s: `puntos` necesita al menos 3 (la planta de la pila)" % que)
        pts = [(lambda l: (l["x"], l["y"]))(X.lugar(ref, que + " → puntos")) for ref in p["puntos"]]
        cx, cy = MU.centroide(pts)
        flat = [round(v, 3) for xy in pts for v in xy]
    else:
        if not rect:
            raise X.m3.Falla("M3D2", "%s: una pila lleva `lugar` (su centro) con `largo_m` y `ancho_m`, o `puntos` (su planta)" % que)
        if p.get("largo_m") is None or p.get("ancho_m") is None:
            raise X.m3.Falla("M3D2", "%s: con `lugar`, la pila necesita `largo_m` y `ancho_m` (su planta en metros)" % que)
        l = X.lugar(p["lugar"], que + " → lugar")
        cx, cy, flat = l["x"], l["y"], None
    return {"x": round(cx, 3), "y": round(cy, 3), "rumbo": float(p["rumbo"]),
            "largo_m": float(p.get("largo_m") or 0), "ancho_m": float(p.get("ancho_m") or 0),
            "alto_m": float(p["alto_m"]), "inicio": float(p["inicio"]), "material": p["material"],
            "acento": bool(p["acento"]), "semilla": int(p["semilla"]), "puntos": flat}


def centro(pz, G):
    return pz["x"], pz["y"]
