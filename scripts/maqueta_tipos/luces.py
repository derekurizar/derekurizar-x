"""Pieza «luces»: un punto [x, y, peso, id] por lugar («todos»: los del set y luego los propios)."""


def resolver(p, X, que):
    refs = p.get("lugares", "todos")
    if refs == "todos":
        refs = list(X.S.lugares) + [k for k in X.propios if k not in X.S.lugares]
    puntos = []
    for ref in refs:
        l = X.lugar(ref, que)
        puntos.append([l["x"], l["y"], l["peso"], ref if isinstance(ref, str) else ""])
    return {"puntos": puntos, "encendidas": p.get("encendidas", True)}
