"""Ayuda compartida de los eventos que mueven luces (encender, apagar, parpadear): sus `lugares` son ids de luces."""


def resolver(e, X, que):
    refs = e.get("lugares", "todos")
    if refs != "todos":
        en_luces = {q[3] for p in X.piezas if p["tipo"] == "luces" for q in p["puntos"]}
        for ref in refs:
            if ref not in en_luces:
                raise X.m3.Falla("M3D2", "%s: «%s» no es una luz de ninguna pieza `luces`" % (que, ref))
    return {"lugares": refs}


def puntos(e, u, G):
    """Las luces que nombra (con «todos» no se mide: el país entero no tiene que estar en cuadro)."""
    if e["lugares"] == "todos":
        return []
    return [(q[0], q[1]) for p in G["R"]["piezas"] if p["tipo"] == "luces" for q in p["puntos"] if q[3] in e["lugares"]]
