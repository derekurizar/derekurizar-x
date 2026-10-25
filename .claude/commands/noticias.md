---
description: Las noticias del día de Guatemala en un video vertical de ≤ 70 s para TikTok, Reels y Shorts, más su 4:5 — rastreadores por sección, un verificador por noticia (segunda fuente, citas guardadas, foto oficial o del medio con crédito), editor que elige 3–4 y escribe el guion, crítico en modo noticiero; cierre siempre con «Sígueme en» (uso — /noticias [hoy|YYYY-MM-DD] [sin-voz|fixture]; voz de ElevenLabs ≈ 850 créditos y entrega en noticias/<fecha>/; sin-voz arma el video con voz falsa, 0 créditos; fixture corre la maqueta)
---

Eres el coordinador del flujo **/noticias** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- `hoy` (por defecto) o una fecha `YYYY-MM-DD`: el día del noticiero.
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos), para revisar el video antes de gastar.
- `fixture`: corre `make noticias-fixture` (la maqueta: noticias de ejemplo, sin web ni voz), abre el video y termina.

La guía es `referencias/flujo-noticias.md`. Nunca publiques. Nunca generes música ni efectos (catálogos fijos de
`/video`). **El guion que el crítico rechaza no se graba con voz sin decisión del usuario.**

1. **PREFLIGHT**
   - `make doctor` (exit 0; ffmpeg, ffprobe y `design/sfx/` completos).
   - `python3 scripts/noticias.py preparar --fecha <fecha>`: anota `TRABAJO` (la última línea:
     `sesiones/noticias-<fecha>`), la paleta del día y la música. Si `TRABAJO` ya tiene `guion.json` de una corrida
     anterior, pregunta si se reutiliza o se empieza de nuevo.
   - Salvo con `sin-voz`, comprueba que el MCP de ElevenLabs responde: carga `creative_create_flow`,
     `creative_add_flow_node`, `creative_run_flow_nodes`, `creative_get_flow_run_status` y `creative_transcribe_audio`
     con ToolSearch.
   - Avisa: el Workflow tarda ~10–20 min (rastreo, verificación y edición con web, 0 créditos); la voz y el render,
     ~5–8 min; la voz cuesta ≈ 1 crédito por carácter (~850 en un noticiero de 60 s).
2. **NOTICIAS, GUION Y CRÍTICA (Workflow `noticias`)**
   - Lanza el Workflow con `name: "noticias"` y `args: {"trabajo": "<TRABAJO>", "fecha": "<fecha>"}`. Si editaste
     `.claude/workflows/noticias.js` o los agentes en esta sesión, pásalo con
     `scriptPath: ".claude/workflows/noticias.js"`; para reanudar, `resumeFromRunId`.
   - Si falla con «no está registrado», pide al usuario reiniciar Claude Code (los agentes se cargan al arrancar);
     solo si lo autoriza, relanza con `args.permitir_fallback: true`.
   - Si falla por pocas noticias publicables, muestra las descartadas con su motivo y pregunta si se reintenta más
     tarde o con otra fecha.
   - Al volver, lee `veredicto`, `puntajes`, `faltas_pendientes` y `mejoras`. Si `veredicto` no es `"pasa"`, muestra
     las faltas y **pregunta al usuario** si sigue así o corrige a mano. Si pasa y quedan mejoras que solo cambian
     texto en pantalla (`titular`, `seccion`, `fuente`, `cifra.etiqueta`, `resumen`, captions), aplícalas en
     `guion.json`; las que tocan la voz van al reporte.
   - Corre tú `python3 scripts/noticias.py guion <TRABAJO> --check` (exit 0: confirma `locucion.json`).
3. **QA DE FOTOS**
   - `python3 scripts/noticias.py fotos-contacto <TRABAJO>` y lee **una vez** `<TRABAJO>/fotos/contacto.png`. Si una
     foto muestra víctimas, cadáveres, heridos o menores identificables, o es un logo o una portada genérica, cámbiala:
     cada noticia lleva foto (N7). Busca una **de referencia** (la institución, el lugar o la persona; galería oficial,
     Wikimedia Commons con licencia libre vía `python3 scripts/historia.py commons "<búsqueda>"`, o foto de archivo de
     un medio; nunca de otro hecho ni generada), bájala con `python3 scripts/noticias.py foto <TRABAJO> --id <id> --url
     <url> --credito "Foto de referencia: <fuente>" --origen referencia`, copia su `foto` de `verificacion_<id>.json` a
     esa noticia de `guion.json`, repasa `guion --check` y vuelve a mirar la hoja.
4. **VOZ** (con `sin-voz`: `python3 scripts/noticias.py voz-falsa <TRABAJO>` y salta al paso 5)
   - Di al usuario los caracteres de voz (`locucion.json → caracteres`) antes de gastar.
   - `python3 scripts/noticias.py voz <TRABAJO>` imprime la voz y un `prompt` por escena (gancho, noticias, cierre).
   - `creative_create_flow` con el nombre «Noticias · <fecha>».
   - Por cada escena, `creative_add_flow_node`: `node_type: "tts"`, `model_id: "eleven_multilingual_v2"`, `voice_id` de
     la salida, `model_parameters: {"language_code": "es"}` y el `prompt` **exacto**.
   - `creative_run_flow_nodes` con TODOS los nodos y **`generations_count: 1`** (la voz es la elegida; sin variaciones).
   - Sondea `creative_get_flow_run_status` **solo con los `session_ids` pendientes**; ElevenLabs reintenta solo cuando
     llega al límite de concurrencia: no relances nodos.
   - Con la voz completa, por cada nodo TTS `creative_transcribe_audio` (`eleven_scribe_v1`, `connect_from: [nodo]`;
     cuesta 0).
   - Luego **una sola** `creative_get_flow_run_status` con los `session_ids` de la voz Y de Scribe (la respuesta queda
     guardada en un archivo) y `python3 scripts/noticias.py descargar <TRABAJO> --estado <ese archivo>` (baja
     `voz_N.mp3`, `palabras_N.json` y `audio/creditos.json`; exit 1 lista lo que falte). La llamada acepta ≤ 20
     sesiones: con más de 10 escenas, en lotes (cada voz con su Scribe) y `descargar --estado A B …` con todos.
5. **TIEMPOS Y ESCUCHA**
   - `python3 scripts/noticias.py tiempos <TRABAJO>` (V6 alineación; N5 y V10, avisos). Si una escena no se alinea,
     rehaz SOLO ese nodo (1 toma), transcríbelo, pide el estado de esas dos sesiones y pásalo a `descargar --estado`;
     repite `tiempos`.
   - Con voz real, `python3 scripts/noticias.py escuchar <TRABAJO>` (V11: whisper.cpp transcribe sin el guion y coteja
     las cifras). Una `FALLA V11` → la misma retoma de un nodo y `escuchar --solo N`; si vuelve a fallar, anótalo y pide
     al usuario oír esa escena. Con `AVISO V11` (sin whisper), sigue y dilo.
6. **GRABAR, MONTAR Y REVISAR**
   - `grabar <TRABAJO>` (V13) → `montar <TRABAJO>` (V8) → `revisar <TRABAJO>`; lee **una vez** `revision/contacto.png`
     y **una vez** `revision/linea_tiempo.png` (texto cortado, pantallas vacías, una foto mal encuadrada, la fuente que
     no se lee). Si falla V13, la línea `FALLA V13 eN` dice qué sale de la zona: acorta ese texto en `guion.json` (no
     la página), repasa `guion --check` y repite desde `tiempos` (la voz no cambia si no tocaste `texto`).
   - Luego el 4:5: `grabar <TRABAJO> --formato 4:5`, `montar <TRABAJO> --formato 4:5`, `revisar <TRABAJO> --formato 4:5`.
7. **ENTREGAR** (no con `sin-voz`: ahí abre `<TRABAJO>/salida/video.mp4` y pasa al reporte)
   - `python3 scripts/noticias.py entregar <TRABAJO>` → `noticias/<fecha>/` (9:16, 4:5, `caption.md`, `fuentes.md`,
     subtítulos, portadas, `guion.json` de entrega; las fotos no se copian).
   - `python3 scripts/memoria.py --noticias noticias/<fecha>` y `make validate` (exit 0).
   - Abre `noticias/<fecha>/video.mp4` con `open`.
8. **REPORTE**
   - Las rutas de `video.mp4` (TikTok, Reels, Shorts) y `video_4x5.mp4` (feed), la duración (máximo 70 s), la paleta
     del día y la música.
   - Por escena: `E<n> · sección · titular · fuente · foto (oficial/medio/referencia)`; el gancho.
   - Las verificadas y las descartadas (con su motivo), y cuántas candidatas trajo el rastreo.
   - Los puntajes del crítico, las vueltas y las mejoras no aplicadas (`<TRABAJO>/critica.json`).
   - Los créditos de voz gastados (`audio/creditos.json`, retomas incluidas) y el resultado de V11.
   - Los avisos (N5, V10, V12, V15) y la ruta de `fuentes.md` (los enlaces para el primer comentario).

Reglas:
- Solo noticias `confirmada` o `en_desarrollo` (con atribución); cada número con su cita guardada.
- Presunción de inocencia: nadie es culpable sin sentencia firme.
- El cierre siempre termina con «Sígueme en» (solo en pantalla).
- Una retoma de voz se hace por escena, nunca del noticiero entero.
- `sesiones/noticias-<fecha>/` queda como memoria de trabajo; el mp4 no se commitea.
