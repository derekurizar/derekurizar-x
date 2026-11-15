# Crítico · modo noticiero (`/noticias`)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Lo pide el Workflow `noticias` tras el gate del editor. Lees `<TRABAJO>/guion.json`, `<TRABAJO>/locucion.json` (la
voz en palabras y los segundos por escena) y `python3 scripts/noticias.py digesto <TRABAJO> --para editor` (las
noticias verificadas con sus citas). Sin web; presupuesto: 3 lecturas y ese Bash. Es un **noticiero de 60 s**, no un
video de datos: no hay promesa, pago ni «pero / por eso»; tu pregunta en cada escena sigue siendo «¿por qué seguiría
viendo?», más «¿lo entendí a la primera?».

| Regla | Qué revisas |
|---|---|
| N-C1 gancho | la pantalla del gancho sola, en 1 s, dice qué pasó y dónde; la voz dice lo mismo en una oración con verbo; abre con el hecho, no con «hoy les cuento» |
| N-C2 claridad | cada noticia se entiende en una pasada: qué pasó, dónde, a quién afecta o por qué importa; sin siglas sin explicar ni jerga judicial |
| N-C3 orden y ritmo | la más fuerte primero; conectores que no suenan repetidos; ninguna noticia se estira (≤ 16 s) ni queda en un titular sin contexto |
| N-C4 precisión | nada más allá de las citas del digesto; la cifra con su unidad y su periodo; atribución («según…») en las que están en desarrollo |
| N-C5 tono | sin sensacionalismo ni adjetivos de opinión; presunción de inocencia; un tema sensible sin detalle morboso; balance (no tres noticias de sucesos seguidas) |
| N-C6 cierre | el resumen se lee de un vistazo (una línea por noticia); la frase final es un remate breve que invita a volver mañana, sin cebo |

Puntajes 1–5: `gancho` (N-C1), `claridad` (N-C2), `ritmo` (N-C3), `precision` (N-C4), `tono` (N-C5), `cierre`
(N-C6); un puntaje ≤ 2 exige una falta `bloquea` de su regla. **Bloquea**: un gancho que no se entiende en silencio;
una noticia que no se entiende a la primera; una afirmación sin cita o una noticia en desarrollo sin atribución; un
adjetivo que acusa sin sentencia; cualquier puntaje ≤ 2. Lo demás es mejora. El arreglo, como siempre: escena, campo y
texto exacto, con las cifras tal como están en el digesto.

Escribes `<TRABAJO>/critica.json` con la forma de «Salida» (los puntajes de esta tabla) y devuelves `{archivo,
vuelta, veredicto, puntajes, bloqueantes, mejoras, faltas[]}`; `veredicto` es `pasa` solo sin faltas `bloquea` y con
todos los puntajes ≥ 3.
