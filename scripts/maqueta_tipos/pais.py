"""Mundo «pais»: el relieve nacional de un set de geodatos de escala pais (design/sets3d/<set>/), en km. Es el `Set` de
scripts/maqueta3d.py (relieve, lugares, fallas, frontera); aquí solo se comprueba el set y se le pasa la exageración."""


def mundo(o, f, m3):
    return m3.Set(m3.set_de(o, "pais"), o.get("exageracion", 5.0))
