"""Las reglas de cada tipo del vocabulario de la maqueta 3D que no caben en su ficha (video/maqueta/<clase>/<tipo>.json).

Un archivo por tipo (`<tipo>.py`, el mismo nombre que su módulo y su ficha); los que empiezan con «_» son ayudas
compartidas. scripts/maqueta3d.py los carga por nombre (`maqueta3d.reglas(tipo)`) y no los importa nadie más. Todo es
opcional: un tipo sin archivo se resuelve con su ficha sola (los parámetros validados, los lugares en km).

  resolver(o, X, que) → dict      lo que el tipo le añade a {id, tipo} (pieza) o a {tipo, t, dur, sfx} (evento) en el
                                  maqueta.json RESUELTO (window.MAQUETA); `o` ya pasó el validador de la ficha y trae los
                                  defectos. X: m3 (el módulo maqueta3d: Falla, helpers, topes), S (el set), lugar(ref, que)
                                  → {x, y, nombre, peso}, propios (mundo.lugares), piezas y por_id (las ya resueltas),
                                  avisos (lista), alt_km(x, y). Falla: raise X.m3.Falla("M3D2", "…")
  cerrar(lista, X)                las reglas sobre todas las de su tipo juntas (un tope, una simplificación)
  # para los gates (G: R = el maqueta.json resuelto, por_id, m3)
  tramos(pz) → [[(x, y, salto)]]  pieza que es una LÍNEA: se puede declarar `separada_de` ella (M3D11)
  centro(pz, G) → (x, y) | None   pieza: el punto que se mira cuando se la resalta (M3D6, M3D9)
  puntos(e, u, G) → [(x, y)]      evento: dónde pasa en la fracción u de su duración (M3D6: ≥ la mitad en cámara); [] = no se mide
  origen(e, G) → (x, y) | None    evento visible en la portada (ficha con `adelanto`): de dónde sale (M3D9); None = siempre se ve
"""
