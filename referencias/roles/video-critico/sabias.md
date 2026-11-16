# Crítico · modo sabías (`/sabias`)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Lo pide la sesión de `/sabias` tras el gate (`scripts/sabias.py guion --check`). Lees `<TRABAJO>/guion.json`,
`<TRABAJO>/locucion.json` (la voz en palabras y los segundos por escena) y `<TRABAJO>/digesto.md` (el dato, sus cifras
verificadas, `no_afirma`, la rotación y «Frases ya usadas»). Sin web; presupuesto: esas 3 lecturas. Es un video de
20–30 s con la fórmula fija «¿Sabías que…?»: no hay promesa, pago ni narración por actos, y la apertura «¿Sabías que»
es el formato (no cuenta para C11; el resto de la frase sí). Tu pregunta: ¿alguien que desliza se queda los 25 s y se
va sabiendo algo que no sabía?

| Regla | Qué revisas |
|---|---|
| SQ-C1 gancho | en silencio, «¿SABÍAS QUE…?», la línea y el visual dicen el dato en 1 s; la voz es UNA pregunta con verbo que nombra Guatemala; el dato sorprende (si el espectador ya lo sabía, no es un «sabías que») |
| SQ-C2 referente | la cifra llega con algo para medirla: el antes, el año, «de cada», una escala humana con `calculo`; nunca la cifra sola |
| SQ-C3 ritmo | la escena del dato no repite la pregunta del gancho: añade el referente o la fuente; el apoyo (si hay) suma algo nuevo; ninguna escena se estira; ≤ 30 s |
| SQ-C4 precisión | nada más allá de las cifras del digesto ni contra `no_afirma`; el periodo se dice o se lee; sin «hoy» con un dato viejo |
| SQ-C5 cierre | la frase final es la consecuencia del dato para la gente que lo vive, no el dato otra vez ni una moraleja; sin «sígueme» en la voz; no repite una frase ya usada |

Puntajes 1–5: `gancho` (SQ-C1), `escala_humana` (SQ-C2), `ritmo` (SQ-C3), `precision` (SQ-C4), `cierre` (SQ-C5);
un puntaje ≤ 2 exige una falta `bloquea` de su regla. **Bloquea**: un gancho que no se entiende sin sonido; una cifra
sin referente; una afirmación que el digesto no respalda; un cierre que repite el dato; cualquier puntaje ≤ 2. Lo
demás es mejora. El arreglo, como siempre: escena, campo y texto exacto, con las cifras tal como están en el digesto
y respetando el gate (pantalla del gancho fija, `texto` = `final` en el cierre).

Escribes `<TRABAJO>/critica.json` con la forma de «Salida» (los puntajes de esta tabla) y devuelves `{archivo,
vuelta, veredicto, puntajes, bloqueantes, mejoras, faltas[]}`; `veredicto` es `pasa` solo sin faltas `bloquea` y con
todos los puntajes ≥ 3.
