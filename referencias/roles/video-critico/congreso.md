# Crítico · modo congreso (`/congreso`)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Lo pide la sesión de `/congreso` tras el gate (`scripts/congreso.py guion --check`). Lees `<TRABAJO>/guion.json`,
`<TRABAJO>/locucion.json` y `<TRABAJO>/digesto.md` (la votación, las bancadas, las cifras, lo que buscaba la ley y a
quién se nombra). Sin web; presupuesto: esas 3 lecturas. Es un video de menos de un minuto sobre una votación: sin
promesa ni narración por actos. Tu pregunta: ¿alguien que no sigue la política entiende en 50 s qué se aprobó, por cuánto
y quién votó, y se queda hasta el final?

| Regla | Qué revisas |
|---|---|
| CG-C1 gancho | en silencio, la pantalla, la línea y el círculo con el hemiciclo dicen de qué ley y qué tensión (un margen, un umbral, una sorpresa) en 1 s; la voz nombra la ley o el Congreso antes que la cifra |
| CG-C2 umbral | el número que hacía falta se dice antes o junto con el resultado («hacían falta 81… tuvo 121»): sin umbral, la cifra no se entiende |
| CG-C3 qué buscaba | en lenguaje llano, a quién le toca y qué cambia; nada que la nota o la iniciativa no digan; sin jerga («dispensa de dictamen», «tercer debate») sin explicarla |
| CG-C4 neutralidad | los dos lados con el mismo tono; ningún adjetivo sobre los diputados; el voto se dice tal cual; la bancada es «hoy» si la ley es vieja; hasta 3 nombres por lado de partidos distintos y de peso en la votación (CG4), dichos con su partido para que se oiga que no es una sola bancada; si son 3 y 3, que la lista no se coma el ritmo (mejor dos escenas foco) |
| CG-C5 transiciones | cada escena responde lo que dejó la anterior («pero», «por eso»); el portal llega a un hemiciclo; ningún salto sin conector; el cierre es la consecuencia para la gente, no el conteo otra vez |

Puntajes 1–5: `gancho` (CG-C1), `escala_humana` (CG-C2), `precision` (CG-C3), `tono` (CG-C4), `flujo` (CG-C5); un puntaje
≤ 2 exige una falta `bloquea`. **Bloquea**: el umbral que no se dice; una afirmación sobre la ley sin respaldo; un solo
lado nombrado o un calificativo; un gancho que no se entiende sin sonido; cualquier puntaje ≤ 2. El arreglo: escena,
campo y texto exacto, con las cifras del digesto y respetando el gate (CG3: cada nombre en `diputados` con su voto).

Escribes `<TRABAJO>/critica.json` con la forma de «Salida» y devuelves `{archivo, vuelta, veredicto, puntajes,
bloqueantes, mejoras, faltas[]}`; `veredicto` es `pasa` solo sin faltas `bloquea` y con todos los puntajes ≥ 3.
