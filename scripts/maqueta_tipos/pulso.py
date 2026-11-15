"""Anotación «pulso»: anillos que se abren en el suelo alrededor de una o varias anclas (un actor, vehículos de un flujo,
un lugar): «este manda su señal». Sin texto. Las anclas ya vienen resueltas por el validador (`sobre`: anclas)."""


def anclas(a):
    return a.get("sobre") or []


def textos(a, escala=None):
    return []
