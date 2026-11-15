---
description: Convierte un hilo ya entregado en un video vertical narrado (9:16 + 4:5) con guion de retención aprobado por un crítico antes de gastar créditos (uso — /video &lt;slug|ultimo&gt; [corto|medio|largo] [musica:&lt;id&gt;] [fixture]; medio ≈ 2 min por defecto; entrega en hilos/&lt;fecha&gt;-&lt;slug&gt;/video/)
---

Eres el coordinador del flujo **/video** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- La primera palabra es el **hilo**: un slug (`crimen-organizado-respuesta-estado`), la carpeta
  (`hilos/2026-10-19-…`) o `ultimo` (el hilo listo más reciente).
- `corto`, `medio` o `largo` fijan la **duración**. Sin ella se usa `medio` (120 s).
- `musica:<id>` fuerza una pista del catálogo (`make musica` las lista).
- Siempre salen dos videos con la misma voz y los mismos tiempos: `video.mp4` (9:16, el mismo para TikTok, Instagram
  y Facebook Reels y YouTube Shorts; es el que se abre) y `video_4x5.mp4` (1080×1350, el feed de Facebook e
  Instagram), más `caption.md` con el texto de cada plataforma (`referencias/flujo-video.md` «Plataformas»). La voz
  se genera una sola vez.
- `fixture` corre la prueba sin créditos (`make video-fixture`) y termina.

La guía es `referencias/flujo-video.md`. **`/video` nunca genera música ni efectos**: solo los catálogos
`design/musica/` y `design/sfx/`. Nunca publiques. **El guion que el crítico rechaza no se graba sin
decisión del usuario.**

1. **PREFLIGHT**
   - Corre `make doctor` (exit 0; ffmpeg y ffprobe deben estar; `design/sfx/` completo).
   - Corre `python3 scripts/video.py preparar <hilo> --duracion <d> [--musica <id>]` (sin `--duracion` es
     `medio`). Si sale ≠ 0, muestra el error y DETENTE (hilo no encontrado, borrador, pocas tarjetas para la
     duración).
   - Anota `TRABAJO` (la última línea; es `sesiones/<slug>/video`).
   - Lee en la salida de `make doctor` si hay `whisper-cli` con modelo (escucha V11) y `design/iconos/` (iconos):
     los dos son opcionales; si faltan, dilo en el aviso al usuario y sigue (`brew install whisper-cpp` + `make whisper`;
     `make iconos`).
   - Comprueba que el MCP de ElevenLabs responde: carga `creative_add_flow_node`, `creative_run_flow_nodes`,
     `creative_get_flow_run_status`, `creative_transcribe_audio` y `creative_create_flow` con ToolSearch.
   - Avisa al usuario de la duración, la música y el costo estimado de la voz (≈ 1 crédito por carácter:
     corto ≈ 850, medio ≈ 1,700, largo ≈ 3,450). El Workflow tarda ~5–10 min sin créditos (~10 más si escribe una
     animación nueva); la voz y el render, otros ~5–10 min.
   - **Foto para el gancho** (m055, /analyze-improve: con la foto a sangre se va un tercio menos de gente en el primer
     segundo): busca en Wikimedia Commons 1–3 fotos del sujeto del hilo (el lugar, el objeto o la gente de la que habla:
     una gasolinera, el penal, el lago; nunca víctimas ni menores identificables) con
     `python3 scripts/historia.py commons "<búsqueda>"` y baja la mejor con
     `python3 scripts/historia.py foto <TRABAJO> --id gan-f01 --commons "File:…" --descripcion "<qué muestra>"`
     (o `--url U --credito "Foto: <institución>" --origen oficial`). `python3 scripts/video.py fotos <TRABAJO>` las
     lista. Sin una foto con licencia, sigue sin ella (el gate solo pide un candidato con foto si hay fotos).
2. **GANCHOS, SELECCIÓN, GUION Y CRÍTICA (Workflow `video`)**
   - Lanza el Workflow con `name: "video"` y `args: {"trabajo": "<TRABAJO>", "duracion": "<d>", "slug":
     "<slug>", "fixture": false}`. Si editaste `.claude/workflows/video.js` en esta sesión, pásalo con
     `scriptPath: ".claude/workflows/video.js"`. Para reanudar una corrida interrumpida, `resumeFromRunId`.
   - El Workflow corre primero al `video-gancho` (5 candidatos de familias distintas en `ganchos.json`, gate
     `ganchos --check` con R1–R10 y la rotación; `referencias/ganchos.md`) y al `video-critico` en **modo selección**
     (los mira en silencio y recomienda ganador y segundo en `seleccion.json`; el usuario elige; si ninguno llega a 3, el agente de ganchos
     rehace una vez). Si aun así no hay ganador, vuelve `veredicto: "corregir"` con las faltas de la selección:
     muéstralas y **pregunta al usuario**. Después corre al `video-guionista` (copia el ganador con `ganchos --usar`,
     PRIMERO la narración de corrido en 3 actos que cuenta el hilo como una historia, `narracion --check`;
     DESPUÉS la reparte en escenas sin cambiar una palabra: guion v2 + gate `guion --check`, V1–V5, V9 y V17–V18, que
     agrupa la voz en secuencias por acto), al oyente ingenuo (`historia-oyente` con `video.py oyente`: lo que no
     entendió, insumo del crítico) y al `video-critico` (C1–C12, puntajes 1–5 con `flujo`, faltas con arreglo); lo que bloquea vuelve al guionista, y si
     aprueba con algún puntaje de 3 dejando mejoras, el guionista las pule; en total ≤ 2
     vueltas. Si el guion aprobado tiene una escena `explica` con `animacion: null`, corre además al
     `video-animador`: escribe `video/animaciones/<id>.js` desde el `brief`, pasa `animaciones.py --check`, la
     registra en la biblioteca y la asigna a la escena. No gasta créditos.
   - **El usuario elige el gancho** (usuario, 2026-11-03: «siempre me pones a escoger entre 5 opciones»): sin
     `args.gancho`, el Workflow se detiene tras la Selección con `veredicto: "elegir_gancho"` (los 5 candidatos y el
     recomendado del crítico). Corre `python3 scripts/video.py ganchos <TRABAJO> --opciones` y pregunta con AskUserQuestion:
     4 botones con la pantalla y la voz de cada opción (la recomendada primero, con «(Recomendado)»), la quinta escrita en
     el texto de la pregunta («o escribe 5 en Otro»); en «Otro» también puede dictar su propio gancho. Con un id:
     `python3 scripts/video.py ganchos <TRABAJO> --elegir <id>` y relanza el Workflow con `resumeFromRunId` y los mismos args
     más `"gancho": "<id>"` (lo ya hecho vuelve de la caché); con su texto, los mismos args más `"gancho_usuario": "<su
     texto literal>"` (el agente de ganchos lo arma como candidato `gu` y lo elige). Si ya no se puede reanudar (otra
     sesión), vuelve a lanzar el Workflow completo (0 créditos) y repite la elección. `"auto": true` deja la recomendación del crítico (solo si el usuario lo pide).
   - **El usuario elige el cierre**: con el guion aprobado, el Workflow devuelve `cierres` (5 opciones en
     `cierres.json`; `c1` es la del guion). ANTES de la voz, `python3 scripts/video.py cierres <TRABAJO> --opciones` y
     pregunta igual (`c1` primero). Con el id que elija (también `c1`: así queda registrado quién eligió; con `auto`, `--usar c1 --por critico`): `python3 scripts/video.py cierres <TRABAJO> --usar <id>`; con su texto:
     `--propio "<su texto>"` con `--forma`, `--mecanismo`, `--quien` y `--verbo` que casen con su frase
     (`referencias/cierres.md`; si dicta solo la frase final, se queda la oración del guion que la prepara). Después corre `python3 scripts/video.py narracion <TRABAJO> --check` y `guion <TRABAJO> --check` (si fallan, `guion.previo.json` tiene el de antes).
     Si el gate la rechaza, muéstrale la falla y propón la versión más cercana que pasa; nunca edites `guion.json` a
     mano. Si `cierres` viene `null` (el agente no pudo), pregunta con el cierre del guion o el suyo (`--propio`).
   - Si falla con «no está registrado», pide al usuario reiniciar Claude Code (los agentes y el workflow se
     cargan al arrancar). Solo si lo autoriza, relanza con `args.permitir_fallback: true`.
   - Al volver, lee `veredicto`, `puntajes` (con `flujo`), `faltas_pendientes`, `narracion` (actos, palabras,
     secuencias de voz) y `oyente`. Si `veredicto` no es `"pasa"`, muestra las
     faltas pendientes y **pregunta al usuario** si sigue así o corrige a mano; no gastes créditos sin su
     respuesta.
   - Si `veredicto` es `"pasa"` y quedan `mejoras`, aplica tú las que solo cambien `golpe`, `pantalla`, `linea`
     o `caption` (texto en pantalla o debajo del video, no la voz) editando `guion.json`; las que toquen la voz van
     al reporte sin aplicarse (cambiar la voz sin que el crítico la relea no vale). La `pregunta` de una adivina y el
     `termino` de una definición se dicen en la voz y la pantalla los escribe a su ritmo: no los cambies solos (el
     gate rechaza una pregunta con palabras que la voz no dice).
   - Si vuelven `animaciones_pendientes` (el guion no pasó la crítica y el usuario decidió seguir, o el animador no
     pasó `--check`), lanza tú un Agent `video-animador` por escena con su `brief`, `titulo` y `pasos` (la directiva
     de la fase Animación de `video.js`); si tampoco sale, propón al usuario cambiar esa escena `explica` por otra.
     Lee una vez `sesiones/_animaciones/<id>/contacto.png` de cada animación nueva antes de gastar créditos.
   - Corre tú `python3 scripts/video.py guion <TRABAJO> --check` (exit 0) para confirmar `locucion.json`.
   - En el reporte, qué gancho y qué cierre eligió el usuario y cuáles recomendaba el crítico (`seleccion.json`, `cierres.json`).
3. **VOZ (MCP)**
   - Sigue `referencias/fragmentos/voz-mcp.md` (lee ese archivo: nodos por secuencia, lotes de ≤ 3, `generations_count: 1`, Scribe y
     `descargar --nodos`) con `<script>` = `video.py` y el flow «Video · <slug>».
4. **TIEMPOS**
   - **En un comando**: `python3 scripts/video.py producir <TRABAJO>` corre este paso y los siguientes hasta `revisar` en 9:16 y
     4:5; se detiene con código 3 a esperar el plano (lanza el Workflow `plano` y repítelo) y reanuda donde quedó
     (`referencias/fragmentos/producir.md`; con `sin-voz`, añade `--borrador`). Los pasos de abajo son lo que corre, uno
     por uno: sirven para entender una falla o rehacer solo uno.
   - Corre `python3 scripts/video.py tiempos <TRABAJO>` (V6 alineación; V10 ritmo real, aviso).
   - Si una escena no se alinea, rehaz SOLO ese nodo («Retomas» en `referencias/fragmentos/voz-mcp.md`) y repite `tiempos`.
   - Corre `python3 scripts/video.py escuchar <TRABAJO>` (V11: whisper.cpp local transcribe cada voz SIN el guion y
     coteja las cifras; Scribe solo alinea el prompt). Una escena con `FALLA V11` → la misma retoma de un solo nodo y
     `escuchar --solo N`; si vuelve a fallar, no insistas: anótalo en el reporte y pide al usuario oír esa escena. Si
     imprime `AVISO V11` (sin `whisper-cli` o sin modelo: `brew install whisper-cpp` y `make whisper`), sigue y dilo
     en el reporte. Los avisos de palabras no numéricas («Zacatepeques» por Sacatepéquez) son ortografía de whisper.
5. **GRABAR Y MONTAR**
   - **PLANO** (mesa de archivo, desde el 2026-11-14; todo TRABAJO nuevo trae `"realizacion": "mesa"` en `video.json`):
     después de `tiempos` y antes de `grabar`, lanza `Workflow({ name: "plano", args: { trabajo: "<TRABAJO>" } })`.
     Si falla con «agente no registrado», pide
     reiniciar Claude Code (los agentes se cargan al arrancar); el plano no se relanza con `permitir_fallback`: un
     realizador sin su agente triplica el contexto. El
     `video-realizador` escribe `<TRABAJO>/plano.json` (qué pieza entra con cada oración) y deja
     `python3 scripts/video.py plano <TRABAJO> --check --hoja` en 0 (MV1–MV14). Con `plano_listo`, muestra
     `<TRABAJO>/plano.md` y sigue; con `plano_pendiente`, muestra las `fallas` y relánzalo (conserva el plano). Lo que
     falle en pantalla se arregla en el plano, nunca en el guion ni en la voz. `grabar`, `montar` y `revisar` despachan
     solos a la mesa (render con un proceso, ≈ 1.6× la duración por formato; `revisar` deja `revision/mesa_<formato>_N.jpg`);
     en `sin-voz` y `fixture`, `grabar` usa el borrador del plano. En la mesa, las tarjetas del hilo, `ranking`, `mapa`, `escala`, `tiempo` y `explica` son **tableros**; el gancho, los golpes y las definiciones pasan a piezas (nota, cifra, `barra`, mapa). La versión B: `variante <TRABAJO>` → voz de la escena 1 → `tiempos` sobre `variante_b` → `variante <TRABAJO> --plano` (el plano del A con la mesa del gancho rehecha) → `grabar` (el video entero) → `montar` → `variante --cerrar`. Guía: `referencias/flujo-mesa.md`.
   - Corre `python3 scripts/video.py grabar <TRABAJO>` (V7 y **V13 zona segura**; graba 3 escenas a la vez: ~20–30 s
     por minuto de video; `--paralelo 1` para ir en serie). Si falla V13, la línea `FALLA V13 eN` dice qué elemento
     sale de la zona y por dónde (`revision/zona.json`): corrige la página de esa escena (no el guion) y `grabar --solo N`.
   - Corre `python3 scripts/video.py montar <TRABAJO>` (V8: música con ducking, efectos del catálogo, dos
     pasadas de loudnorm).
   - Corre `python3 scripts/video.py revisar <TRABAJO>` y lee **una vez** `<TRABAJO>/revision/contacto.png`
     (por escena: el cuadro al completar la cifra, el pico del foco y el final) y **una vez**
     `<TRABAJO>/revision/linea_tiempo.png` (el video final de corrido, un cuadro cada 2 s, transiciones
     incluidas): es lo más cerca de «verlo» que tienes; busca escenas quietas, texto cortado o pantallas vacías. El
     rectángulo rojo de `contacto.png` es la zona segura y la esquina sombreada, la columna de íconos.
   - Coteja las cifras con los `tuit_N.png` del hilo; revisa que el gancho se lea sin sonido, que el golpe no
     se monte sobre la tarjeta, que el foco no corte el número y que los subtítulos se lean. Si algo está mal
     en una escena, corrígelo y corre `grabar --solo N` y `montar` de nuevo.
   - Cuando el 9:16 esté bien, **siempre** el 4:5 (misma voz, mismos tiempos): `grabar <TRABAJO> --formato 4:5`,
     `montar <TRABAJO> --formato 4:5` y `revisar <TRABAJO> --formato 4:5` (lee una vez `revision/contacto_4x5.png`).
     `entregar` lo exige.
5b. **VERSIÓN B (opcional, si el usuario la pide o la aprobó)**: el segundo gancho sobre el mismo video.
   - `python3 scripts/video.py variante <TRABAJO>` arma `<TRABAJO>/variante_b/` (mismo guion salvo la escena 1; copia
     la voz, las palabras y los clips de las demás escenas) e imprime el nodo de voz SOLO de la escena 1 (≈ 100
     créditos: dilo antes de gastarlos).
   - En el mismo flow: un nodo TTS con ese `prompt` (1 toma) y su Scribe; una llamada de estado con las dos sesiones →
     `descargar <TRABAJO>/variante_b --estado <archivo>`; luego `tiempos`, `escuchar --solo 1`, `grabar --solo 1` y
     `montar` sobre `<TRABAJO>/variante_b`; lee una vez su `revision/contacto.png` tras `revisar`.
   - `python3 scripts/video.py variante <TRABAJO> --cerrar` deja `salida/video_b.mp4`; `entregar` lo copia.
6. **ENTREGAR**
   - Corre `python3 scripts/video.py entregar <TRABAJO>`, que copia a `hilos/<fecha>-<slug>/video/` el 9:16, el 4:5 y
     `caption.md` (avisa si el video pasa de los 3 min de Shorts).
   - Luego `python3 scripts/memoria.py --video hilos/<fecha>-<slug>/video` y `make validate` (exit 0).
   - Abre `video.mp4` (la versión de TikTok) con `open`.
   - **Prueba A/B de duración** (m058; solo si el usuario la pide): el corte `corto` en `sesiones/<slug>/video-corto` →
     `hilos/<fecha>-<slug>/video-corto` (se registra como `<id>-corto`), para TikTok, Reels y Facebook; el principal va
     a YouTube. Pasos en `referencias/flujo-video.md` («Prueba A/B de duración»).
7. **REPORTE**
   - Las rutas de `video.mp4` (TikTok, Instagram y Facebook Reels, YouTube Shorts) y `video_4x5.mp4` (feed), y la
     duración frente al objetivo (incluye el medio segundo del cierre en bucle); si pasa de 180 s, que no entra
     como Short.
   - Las portadas para elegir la miniatura, todas sin subtítulos ni barra: `portada.png` (gancho),
     `portada_texto.png` (solo el gancho en texto, para el feed), `portada_cierre.png`, `portada_giro.png` y, si
     hay adivina, `portada_adivina.png`.
   - La estructura: por escena `tipo · T<tuit> · golpe o pantalla · una línea de lo que dice`; la promesa y en
     qué escena se paga.
   - El **gancho**: los candidatos (familia · visual · pantalla), el ganador y el segundo con sus puntajes de selección
     y el porqué (`seleccion.json`); si hay `video_b.mp4`, cuál es A y cuál B, y que se compara en «Visto frente a
     deslizado» (YouTube Studio) o la retención a 3 s (TikTok).
   - La **narración**: palabras por acto, conectores, secuencias de voz (cuántas y qué escenas) y lo que el oyente
     no entendió (`oyente`).
   - Los **puntajes del crítico** (gancho, bucle, ritmo, flujo, escala_humana, pago, cierre), las vueltas y las
     mejoras no aplicadas (`<TRABAJO>/critica.json`).
   - Las animaciones de las escenas `explica`: id, si es nueva (queda en `video/animaciones/` para otros videos) o
     reutilizada, y la ruta de su hoja de contacto.
   - La frase final del cierre (remate o pregunta, con su forma), la música y los créditos de voz gastados (`creditos_voz` en `guion.json`: la suma
     de `audio/creditos.json` cuando la voz bajó con `--estado`, retomas incluidas; si no, los caracteres, más las
     retomas).
   - Los avisos (V6, V10, V12 quietud y V15 primer cuadro de `revisar`), el resultado de V13 en los dos formatos y la ruta de
     `caption.md` (una sección por plataforma).
   - El resultado de la escucha (V11): escenas cotejadas por whisper, % de palabras distintas y avisos; si se saltó,
     **pide al usuario escuchar las cifras** (Scribe alinea el guion, no es una escucha independiente).
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo): lo que en esta corrida se trabó o se
     resolvió a mano (un arreglo del crítico que el gate rechazó) —una falla o un aviso que se repite entre corridas,
     un gate con falso positivo o negativo, un paso que hubo que hacer a mano, uno lento o frágil, un recorte V16 que
     se repite—, cada una con el archivo y el cambio propuesto. Regístralas con `python3 scripts/memoria.py --mejoras
     <TRABAJO>/mejoras.json` (`{"flujo": "video", "pieza": "<carpeta de entrega>", "mejoras": [{"area", "archivo",
     "problema", "propuesta"}]}`) y no las apliques sin que el usuario lo pida; las que ya quedaron arregladas van con
     `"estado": "hecha"`. Con `fixture` se listan, no se registran.

Reglas:
- Solo cifras del hilo o derivadas con `calculo`, que pasan V2 y V9.
- El guion que el crítico rechaza no se graba sin decisión del usuario.
- El mp4 no se commitea (`.gitignore`).
- `sesiones/<slug>/video/` queda como memoria de trabajo.
- Una retoma de voz se hace por nodo: la secuencia entera si cambió una de sus escenas (`voz --pendientes`) o solo
  esas escenas como nodos propios (`voz --sueltas`), nunca del video entero.
