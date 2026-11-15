# video-gancho · Modo explica (`/explica`)

> Parte de `referencias/roles/video-gancho.md` (léelo primero); aquí está solo lo de este modo.

Lo pide el Workflow `explica` con las afirmaciones y los datos ya verificados y los ejemplos ya calculados. Insumo:
`python3 scripts/explica.py digesto <TRABAJO> --para gancho` (encuadre, afirmaciones, cifras reales, ejemplos con sus
ids `ej-cNN`, revelaciones y lo bloqueado por rotación), en lugar de `digesto.md`. R1–R14 valen igual. Lo que cambia:
- **Familias**: `contraste`, `paradoja`, `pregunta`, `tu`, `escala`, `resultado` (sin `lugar` ni `ranking`: el
  explicador no es un mapa). **Visuales**: `cifra`, `llenado`, `pareja`, `figuras`.
  - `pareja` es el ejemplo conductor frente a frente (Ana y Luis con el mismo dinero y finales distintos);
  - `figuras`, el «ajá» en escala humana («77 de cada 100 quetzales no los pusiste tú»).
- **El gancho plantea la pregunta del video sin dar el mecanismo**: el resultado sorprendente, la paradoja, el
  espectador como protagonista. Nunca la revelación (la otra cara del mecanismo) ni la definición.
- **Números de ejemplo**: solo los `ej-cNN` (o un `calculo` con ellos), dichos como ejemplo («Imagina…», «Supón…»).
  Nunca «en Guatemala» junto a un número de ejemplo. El chip «Ejemplo» sale solo.
- **R6**: «Guatemala» o «quetzales» en la voz o la pantalla (el concepto es universal; el anclaje es la moneda).
- Gate: `python3 scripts/explica.py ganchos <TRABAJO> --check` (no el de `video.py`).
