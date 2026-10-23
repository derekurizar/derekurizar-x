---
description: Convierte un hilo ya entregado en un video vertical narrado para TikTok, Instagram y Facebook Reels y YouTube Shorts, más su versión 4:5 para el feed (uso — /video <slug|ultimo> [corto|medio|largo] [musica:<id>] [fixture]; corto ≈ 1 min, medio ≈ 2 min (por defecto), largo ≈ 4 min; guion de retención sin cara (gancho con cifra a pantalla completa, golpes de texto cinético, «pero / por eso», promesa y pago) aprobado por un crítico ANTES de gastar créditos; voz de ElevenLabs con las cifras en palabras, tarjetas del hilo animadas con zoom a la cifra, subtítulos, barra de progreso, música con ducking y efectos del catálogo fijo; entrega en hilos/<fecha>-<slug>/video/)
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
     `corto`). Si sale ≠ 0, muestra el error y DETENTE (hilo no encontrado, borrador, pocas tarjetas para la
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
2. **GUION Y CRÍTICA (Workflow `video`)**
   - Lanza el Workflow con `name: "video"` y `args: {"trabajo": "<TRABAJO>", "duracion": "<d>", "slug":
     "<slug>", "fixture": false}`. Si editaste `.claude/workflows/video.js` en esta sesión, pásalo con
     `scriptPath: ".claude/workflows/video.js"`. Para reanudar una corrida interrumpida, `resumeFromRunId`.
   - El Workflow corre al `video-guionista` (guion v2 + gate `guion --check`, V1–V5 y V9) y al
     `video-critico` (C1–C10, puntajes 1–5, faltas con arreglo); lo que bloquea vuelve al guionista, y si
     aprueba con algún puntaje de 3 dejando mejoras, el guionista las pule; en total ≤ 2
     vueltas. Si el guion aprobado tiene una escena `explica` con `animacion: null`, corre además al
     `video-animador`: escribe `video/animaciones/<id>.js` desde el `brief`, pasa `animaciones.py --check`, la
     registra en la biblioteca y la asigna a la escena. No gasta créditos.
   - Si falla con «no está registrado», pide al usuario reiniciar Claude Code (los agentes y el workflow se
     cargan al arrancar). Solo si lo autoriza, relanza con `args.permitir_fallback: true`.
   - Al volver, lee `veredicto`, `puntajes` y `faltas_pendientes`. Si `veredicto` no es `"pasa"`, muestra las
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
3. **VOZ (MCP)**
   - `python3 scripts/video.py voz <TRABAJO>` imprime la voz y un `prompt` por escena (gancho, tarjetas,
     golpes y cierre).
   - `creative_create_flow` con el nombre «Video · <slug>».
   - Por cada escena, `creative_add_flow_node`: `node_type: "tts"`, `model_id: "eleven_multilingual_v2"`,
     `voice_id` de la salida, `model_parameters: {"language_code": "es"}` y `prompt` **exacto**.
   - `creative_run_flow_nodes` con TODOS los nodos y **`generations_count: 1`**: la locución es determinista y
     el usuario eligió esta voz; no pidas variaciones.
   - Sondea `creative_get_flow_run_status` **solo con los `session_ids` que sigan pendientes** (cada sondeo
     devuelve las URL completas: con los 10 son ~15k caracteres). ElevenLabs limita cuántas voces genera a la
     vez y reintenta solo («concurrency limit»): no relances nodos.
   - Cuando la voz esté completa, por cada nodo TTS `creative_transcribe_audio` (`eleven_scribe_v1`,
     `connect_from: [nodo]`; cuesta 0).
   - Luego **una sola** llamada a `creative_get_flow_run_status` con los `session_ids` de la voz Y de Scribe
     (20 en un video medio): la respuesta supera el límite y queda guardada en un archivo. Corre
     `python3 scripts/video.py descargar <TRABAJO> --estado <ese archivo>`: baja `voz_N.mp3` (por el prompt de
     cada generación), `palabras_N.json` (por el id de generación de cada transcripción) y escribe
     `audio/creditos.json` con los créditos cobrados. Exit 1 lista lo que falte.
   - Respaldo, solo si la respuesta llegó en línea y no se guardó: escribe `<TRABAJO>/audio/urls_voz.json`
     (`{"<n>": "<content_url>"}`) y `urls_palabras.json` (`words_download_url`) y corre `descargar --voz …` y
     `descargar --palabras …`.
4. **TIEMPOS**
   - Corre `python3 scripts/video.py tiempos <TRABAJO>` (V6 alineación; V10 ritmo real, aviso).
   - Si una escena no se alinea, rehaz SOLO ese nodo: corre `creative_run_flow_nodes` de ese nodo con 1 toma,
     transcríbelo, pide el estado de esas dos sesiones y pásalo a `descargar --estado` (solo actualiza esa
     escena y suma sus créditos a `creditos.json`); repite `tiempos`.
   - Corre `python3 scripts/video.py escuchar <TRABAJO>` (V11: whisper.cpp local transcribe cada voz SIN el guion y
     coteja las cifras; Scribe solo alinea el prompt). Una escena con `FALLA V11` → la misma retoma de un solo nodo y
     `escuchar --solo N`; si vuelve a fallar, no insistas: anótalo en el reporte y pide al usuario oír esa escena. Si
     imprime `AVISO V11` (sin `whisper-cli` o sin modelo: `brew install whisper-cpp` y `make whisper`), sigue y dilo
     en el reporte. Los avisos de palabras no numéricas («Zacatepeques» por Sacatepéquez) son ortografía de whisper.
5. **GRABAR Y MONTAR**
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
6. **ENTREGAR**
   - Corre `python3 scripts/video.py entregar <TRABAJO>`, que copia a `hilos/<fecha>-<slug>/video/` el 9:16, el 4:5 y
     `caption.md` (avisa si el video pasa de los 3 min de Shorts).
   - Luego `python3 scripts/memoria.py --video hilos/<fecha>-<slug>/video` y `make validate` (exit 0).
   - Abre `video.mp4` (la versión de TikTok) con `open`.
7. **REPORTE**
   - Las rutas de `video.mp4` (TikTok, Instagram y Facebook Reels, YouTube Shorts) y `video_4x5.mp4` (feed), y la
     duración frente al objetivo (incluye el medio segundo del cierre en bucle); si pasa de 180 s, que no entra
     como Short.
   - Las portadas para elegir la miniatura, todas sin subtítulos ni barra: `portada.png` (gancho),
     `portada_texto.png` (solo el gancho en texto, para el feed), `portada_pregunta.png`, `portada_giro.png` y, si
     hay adivina, `portada_adivina.png`.
   - La estructura: por escena `tipo · T<tuit> · golpe o pantalla · una línea de lo que dice`; la promesa y en
     qué escena se paga.
   - Los **puntajes del crítico** (gancho, bucle, ritmo, escala_humana, pago, cierre), las vueltas y las
     mejoras no aplicadas (`<TRABAJO>/critica.json`).
   - Las animaciones de las escenas `explica`: id, si es nueva (queda en `video/animaciones/` para otros videos) o
     reutilizada, y la ruta de su hoja de contacto.
   - La pregunta del cierre, la música y los créditos de voz gastados (`creditos_voz` en `guion.json`: la suma
     de `audio/creditos.json` cuando la voz bajó con `--estado`, retomas incluidas; si no, los caracteres, más las
     retomas).
   - Los avisos (V6, V10, V12 quietud de `revisar`), el resultado de V13 en los dos formatos y la ruta de
     `caption.md` (una sección por plataforma).
   - El resultado de la escucha (V11): escenas cotejadas por whisper, % de palabras distintas y avisos; si se saltó,
     **pide al usuario escuchar las cifras** (Scribe alinea el guion, no es una escucha independiente).

Reglas:
- Solo cifras del hilo o derivadas con `calculo`, que pasan V2 y V9.
- El guion que el crítico rechaza no se graba sin decisión del usuario.
- El mp4 no se commitea (`.gitignore`).
- `sesiones/<slug>/video/` queda como memoria de trabajo.
- Una retoma de voz se hace por escena, nunca del video entero.
