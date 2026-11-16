"""Anotación «medida»: el tamaño de algo, dibujado en el suelo con su rótulo («5 m»): un CÍRCULO de `radio_m` alrededor
del ancla, o una REGLA de `radio_m` desde el ancla hacia adelante (la dirección del móvil; de un lugar, al este). El
número del rótulo pasa por el respaldo de las cifras (C3D5 en video3d.py). Sin `rotulo`, «<radio_m> m»."""


def numero(v):
    return ("%g" % v).replace(".", ",") if abs(v - round(v)) > 1e-9 else "%d" % round(v)


def rotulo(a):
    return a.get("rotulo") or "%s m" % numero(float(a["radio_m"]))


def resolver(a, X, que):
    from maqueta_tipos import _movimiento as MV
    return {"en": MV.resolver_ancla(a["en"], X, que + " → en")[0], "radio_m": float(a["radio_m"]), "forma": a["forma"], "rotulo": rotulo(a)}


def anclas(a):
    return [a["en"]]


def textos(a, escala=None):
    return [rotulo(a)]
