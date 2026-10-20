---
description: Convierte un hilo ya entregado en un video vertical narrado para TikTok, Reels y Facebook (uso — /video <slug|ultimo> [corto|medio|largo] [musica:<id>] [fixture]; corto ≈ 1 min (por defecto), medio ≈ 2 min, largo ≈ 4 min; guion de retención sin cara (gancho con cifra a pantalla completa, golpes de texto cinético, «pero / por eso», promesa y pago) aprobado por un crítico ANTES de gastar créditos; voz de ElevenLabs con las cifras en palabras, tarjetas del hilo animadas con zoom a la cifra, subtítulos, barra de progreso, música con ducking y efectos del catálogo fijo; entrega en hilos/<fecha>-<slug>/video/)
---

Eres el coordinador del flujo **/video** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- La primera palabra es el **hilo**: un slug (`crimen-organizado-respuesta-estado`), la carpeta
  (`hilos/2026-10-19-…`) o `ultimo` (el hilo listo más reciente).
- `corto`, `medio` o `largo` fijan la **duración**. Sin ella se usa `corto` (60 s).
- `musica:<id>` fuerza una pista del catálogo (`make musica` las lista).
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
   - Comprueba que el MCP de ElevenLabs responde: carga `creative_add_flow_node`, `creative_run_flow_nodes`,
     `creative_get_flow_run_status`, `creative_transcribe_audio` y `creative_create_flow` con ToolSearch.
   - Avisa al usuario de la duración, la música y el costo estimado de la voz (≈ 1 crédito por carácter:
     corto ≈ 850, medio ≈ 1,700, largo ≈ 3,450). El Workflow tarda ~5–10 min sin créditos; la voz y el render,
     otros ~5–10 min.
2. **GUION Y CRÍTICA (Workflow `video`)**
   - Lanza el Workflow con `name: "video"` y `args: {"trabajo": "<TRABAJO>", "duracion": "<d>", "slug":
     "<slug>", "fixture": false}`. Si editaste `.claude/workflows/video.js` en esta sesión, pásalo con
     `scriptPath: ".claude/workflows/video.js"`. Para reanudar una corrida interrumpida, `resumeFromRunId`.
   - El Workflow corre al `video-guionista` (guion v2 + gate `guion --check`, V1–V5 y V9) y al
     `video-critico` (C1–C9, puntajes 1–5, faltas con arreglo); lo que bloquea vuelve al guionista, y si
     aprueba con algún puntaje de 3 dejando mejoras, el guionista las pule; en total ≤ 2
     vueltas. No gasta créditos.
   - Si falla con «no está registrado», pide al usuario reiniciar Claude Code (los agentes y el workflow se
     cargan al arrancar). Solo si lo autoriza, relanza con `args.permitir_fallback: true`.
   - Al volver, lee `veredicto`, `puntajes` y `faltas_pendientes`. Si `veredicto` no es `"pasa"`, muestra las
     faltas pendientes y **pregunta al usuario** si sigue así o corrige a mano; no gastes créditos sin su
     respuesta.
   - Corre tú `python3 scripts/video.py guion <TRABAJO> --check` (exit 0) para confirmar `locucion.json`.
3. **VOZ (MCP)**
   - `python3 scripts/video.py voz <TRABAJO>` imprime la voz y un `prompt` por escena (gancho, tarjetas,
     golpes y cierre).
   - `creative_create_flow` con el nombre «Video · <slug>».
   - Por cada escena, `creative_add_flow_node`: `node_type: "tts"`, `model_id: "eleven_multilingual_v2"`,
     `voice_id` de la salida, `model_parameters: {"language_code": "es"}` y `prompt` **exacto**.
   - `creative_run_flow_nodes` con TODOS los nodos y **`generations_count: 1`**: la locución es determinista y
     el usuario eligió esta voz; no pidas variaciones.
   - Sondea `creative_get_flow_run_status` hasta `all_completed`.
   - Escribe `<TRABAJO>/audio/urls_voz.json` como `{"<n>": "<content_url>"}`, siguiendo el orden de los nodos,
     y corre `python3 scripts/video.py descargar <TRABAJO> --voz <TRABAJO>/audio/urls_voz.json`.
   - Por cada nodo TTS, `creative_transcribe_audio` (`eleven_scribe_v1`, `connect_from: [nodo]`; cuesta 0).
   - Sondea el estado. Si la respuesta es enorme, léela con python desde el archivo guardado.
   - Escribe `<TRABAJO>/audio/urls_palabras.json` con cada `words_download_url` y corre
     `python3 scripts/video.py descargar <TRABAJO> --palabras <TRABAJO>/audio/urls_palabras.json`.
4. **TIEMPOS**
   - Corre `python3 scripts/video.py tiempos <TRABAJO>` (V6 alineación; V10 ritmo real, aviso).
   - Si una escena no se alinea, rehaz SOLO ese nodo: corre `creative_run_flow_nodes` de ese nodo con 1 toma,
     descárgalo, transcríbelo y repite. Cuenta los créditos extra.
5. **GRABAR Y MONTAR**
   - Corre `python3 scripts/video.py grabar <TRABAJO>` (V7; ~1 min por cada minuto de video).
   - Corre `python3 scripts/video.py montar <TRABAJO>` (V8: música con ducking, efectos del catálogo, dos
     pasadas de loudnorm).
   - Corre `python3 scripts/video.py revisar <TRABAJO>` y lee **una vez** `<TRABAJO>/revision/contacto.png`.
     Muestra, por escena, el cuadro al completar la cifra, el pico del foco (zoom) y el final.
   - Coteja las cifras con los `tuit_N.png` del hilo; revisa que el gancho se lea sin sonido, que el golpe no
     se monte sobre la tarjeta, que el foco no corte el número y que los subtítulos se lean. Si algo está mal
     en una escena, corrígelo y corre `grabar --solo N` y `montar` de nuevo.
6. **ENTREGAR**
   - Corre `python3 scripts/video.py entregar <TRABAJO>`, que copia a `hilos/<fecha>-<slug>/video/`.
   - Luego `python3 scripts/memoria.py --video hilos/<fecha>-<slug>/video` y `make validate` (exit 0).
   - Abre el video con `open`.
7. **REPORTE**
   - La ruta del video y su duración frente al objetivo.
   - La estructura: por escena `tipo · T<tuit> · golpe o pantalla · una línea de lo que dice`; la promesa y en
     qué escena se paga.
   - Los **puntajes del crítico** (gancho, bucle, ritmo, escala_humana, pago, cierre), las vueltas y las
     mejoras no aplicadas (`<TRABAJO>/critica.json`).
   - La pregunta del cierre, la música y los créditos de voz gastados (`creditos_voz` en `guion.json`, más las
     retomas).
   - Los avisos (V6, V10) y la ruta de `caption.md`.
   - **Pide al usuario escuchar las cifras**: Scribe alinea el guion, no es una escucha independiente.

Reglas:
- Solo cifras del hilo o derivadas con `calculo`, que pasan V2 y V9.
- El guion que el crítico rechaza no se graba sin decisión del usuario.
- El mp4 no se commitea (`.gitignore`).
- `sesiones/<slug>/video/` queda como memoria de trabajo.
- Una retoma de voz se hace por escena, nunca del video entero.
