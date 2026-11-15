# Crítico · modo semana (`/semana`, modo semana de /noticias)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Lo pide el Workflow `noticias` con `modo: semana` tras el gate del editor (SM1–SM11). Lees `<TRABAJO>/guion.json`,
`<TRABAJO>/locucion.json` y `python3 scripts/semana.py digesto <TRABAJO> --para editor` (las cifras de la semana con su
cita). Sin web; presupuesto: 3 lecturas y ese Bash. Es una **cuenta regresiva de 62–90 s**: cinco cifras de cinco
noticias, de la #5 a la #1; tu pregunta en cada escena es «¿por qué esperaría a la siguiente?».

| Regla | Qué revisas |
|---|---|
| SM-C1 gancho | la pantalla sola dice que vienen las 5 cifras de la semana; la voz dice «Guatemala» y «semana» en ≤ 6 s; no adelanta la #1 (ni su número, ni su foto, ni su tema) |
| SM-C2 orden | la cuenta sube: la #1 es la que más pesa para la gente (alcance, impacto, novedad), no la más llamativa; ninguna #5 más fuerte que la #2; secciones alternadas |
| SM-C3 claridad | cada cifra se entiende en una pasada: qué mide, de dónde y de cuándo; la cifra en pantalla es la que dice la voz, con su unidad |
| SM-C4 escala | ≥ 3 cifras con su `humana` (a escala de una persona o un hogar), respaldada por la cita o un `calculo`; nada de equivalencias forzadas |
| SM-C5 tono | sin «ganamos / perdemos», sin sensacionalismo; presunción de inocencia; un dato oficial suena oficial («según el INE») |
| SM-C6 cierre | las 5 líneas del resumen se leen de un vistazo (una por cifra, en el orden de la cuenta); la frase final cierra la semana y cita al domingo que viene, sin cebo |

Puntajes 1–5: `gancho` (SM-C1), `orden` (SM-C2), `claridad` (SM-C3), `escala` (SM-C4), `tono` (SM-C5), `cierre`
(SM-C6); un puntaje ≤ 2 exige una falta `bloquea` de su regla. **Bloquea**: un gancho que revela la #1; una cifra que no
se entiende; una afirmación sin cita; un orden que deja lo más fuerte en medio; cualquier puntaje ≤ 2. Lo demás es
mejora. `critica.json` y el retorno, como en el modo noticiero.
