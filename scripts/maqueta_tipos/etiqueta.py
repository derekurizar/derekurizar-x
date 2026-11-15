"""Anotación «etiqueta»: un rótulo corto que SIGUE a un ancla (un actor, un vehículo de un flujo, un lugar), encima de él:
«102 km/h», «Tu carro». Cada número que muestra pasa por el respaldo de las cifras (C3D5 en video3d.py)."""


def anclas(a):
    return [a["sigue"]]


def textos(a, escala=None):
    return [x for x in (a.get("texto"), a.get("sub")) if x]
