---
description: Un «¿Sabías que en Guatemala…?» en video vertical de 20–30 s (9:16 + 4:5) desde un dato de /dato (uso — /sabias &lt;slug|ultimo|pista&gt; [sin-voz|fixture]; una pista que no es un dato entregado corre /dato primero; voz ≈ 300–450 créditos)
---

Eres el coordinador del flujo **/sabias** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- `ultimo`, el slug de un dato de `datos/` (`lago-atitlan-nivel`) o su carpeta: el dato del video.
- Cualquier otro texto es una **pista** para `/dato`: primero se produce el dato y luego su video.
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos), para revisar el video antes de gastar; no entrega.
- `fixture`: corre `make sabias-fixture` (el dato de prueba, sin web ni voz), abre el video y termina.

La guía es `referencias/flujo-sabias.md`. Nunca publiques. Nunca generes música ni efectos (catálogos fijos de
`/video`). **El guion que el crítico rechaza no se graba con voz sin decisión del usuario.**

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - Resuelve el dato: `ultimo`, un slug con carpeta `datos/*-<slug>/` o una carpeta con `dato.json`. Si no resuelve, es
     una pista: corre el flujo `/dato` con ella (Skill `dato`; su modo si la pista empieza por `vs`, `mapa` o `antes`)
     y sigue con el slug que entregó. Si el dato quedó `incompleto`, detente y repórtalo.
   - `python3 scripts/sabias.py preparar <dato>`: imprime el digesto y, al final, `TRABAJO` (`sesiones/<slug>/sabias`).
     Si avisa que el dato ya tiene su «¿Sabías que…?», pregunta si se rehace.
   - Salvo con `sin-voz`, carga con ToolSearch `creative_create_flow`, `creative_add_flow_node`,
     `creative_run_flow_nodes`, `creative_get_flow_run_status` y `creative_transcribe_audio` del MCP de ElevenLabs.
2. **GUION** (lo escribes tú: 3–4 escenas, sin agentes de guion)
   - Lee `<TRABAJO>/digesto.md` y escribe `<TRABAJO>/guion.json` con su plantilla: el gancho con la pantalla
     «¿Sabías que…?», la línea con la cifra, un visual con respaldo (no el bloqueado) y la voz en UNA pregunta «¿Sabías
     que en Guatemala…?»; la escena del dato con su referente; a lo más un apoyo (golpe a escala humana con `calculo`,
     escala o una explica de la biblioteca; no el bloqueado); el cierre de una pantalla con la consecuencia; captions
     de las cuatro plataformas. Cifras en dígitos (el script las pasa a palabras), solo las del digesto.
   - **El usuario elige gancho y cierre** (usuario, 2026-11-03): antes de escribir el guion final, propón 5 ganchos
     distintos («¿Sabías que en Guatemala…?» con otra cifra a la vista, otro visual u otro ángulo; ninguno bloqueado
     por S3) y, con el guion armado, 5 cierres de una pantalla (otra consecuencia: quién lo vive, qué pierde, qué
     espera…; `referencias/cierres.md`). Pregunta con AskUserQuestion (4 botones, la quinta en el texto de la pregunta;
     en «Otro» puede dictar el suyo, que va casi literal) y escribe en `guion.json` lo que elija.
     Deja en `guion.json` quién eligió, para medirlo: `"gancho": {"id", "elegido_por": "usuario|critico|propio",
     "recomendado": "<el que tú recomendabas>"}` y, dentro de `cierre`, `elegido_por` y `recomendado`.
   - `python3 scripts/sabias.py guion <TRABAJO> --check` hasta exit 0 (S1–S3, V1–V5, V9, F1–F8; la tabla da los
     segundos estimados: 20–30 s).
3. **CRÍTICA** (0 créditos)
   - Lanza el agente `video-critico` (Agent, `subagent_type: "video-critico"`) en **Modo sabías** (su guía:
     `referencias/roles/video-critico.md` y `referencias/roles/video-critico/sabias.md`) con `TRABAJO` y `vuelta: 1`. Aplica sus faltas `bloquea` con el texto exacto
     del arreglo, repasa `guion --check` y, si hubo faltas, una segunda vuelta (`vuelta: 2`, con la lista anterior).
   - Si tras 2 vueltas no pasa, muestra las faltas y **pregunta al usuario** antes de gastar créditos.
4. **VOZ** (con `sin-voz`: `python3 scripts/sabias.py voz-falsa <TRABAJO>` y salta al paso 5)
   - Sigue `referencias/fragmentos/voz-mcp.md` (lee ese archivo: nodos por secuencia, lotes de ≤ 3, `generations_count: 1`, Scribe y
     `descargar --nodos`) con `<script>` = `sabias.py` y el flow «Sabías que · <slug>».
5. **TIEMPOS Y ESCUCHA**
   - **En un comando**: `python3 scripts/sabias.py producir <TRABAJO>` corre este paso y los siguientes hasta `revisar` en 9:16 y
     4:5; se detiene con código 3 a esperar el plano (lanza el Workflow `plano` y repítelo) y reanuda donde quedó
     (`referencias/fragmentos/producir.md`; con `sin-voz`, añade `--borrador`). Los pasos de abajo son lo que corre, uno
     por uno: sirven para entender una falla o rehacer solo uno.
   - `python3 scripts/sabias.py tiempos <TRABAJO>` (V6, V10, V16). Si una escena no se alinea, rehaz SOLO ese nodo
     («Retomas» en `referencias/fragmentos/voz-mcp.md`) y repite `tiempos`.
   - Con voz real, `python3 scripts/sabias.py escuchar <TRABAJO>` (V11). Una `FALLA V11` → la misma retoma de un nodo.
6. **GRABAR, MONTAR Y REVISAR**
   - **PLANO** (mesa de archivo, desde el 2026-11-14; todo TRABAJO nuevo trae `"realizacion": "mesa"` en `video.json`):
     después de `tiempos` y antes de `grabar`, lanza `Workflow({ name: "plano", args: { trabajo: "<TRABAJO>" } })`.
     Si falla con «agente no registrado», pide
     reiniciar Claude Code (los agentes se cargan al arrancar); el plano no se relanza con `permitir_fallback`: un
     realizador sin su agente triplica el contexto. El
     `video-realizador` escribe `<TRABAJO>/plano.json` (qué pieza entra con cada oración) y deja
     `python3 scripts/sabias.py plano <TRABAJO> --check --hoja` en 0 (MV1–MV14). Con `plano_listo`, muestra
     `<TRABAJO>/plano.md` y sigue; con `plano_pendiente`, muestra las `fallas` y relánzalo (conserva el plano). Lo que
     falle en pantalla se arregla en el plano, nunca en el guion ni en la voz. `grabar`, `montar` y `revisar` despachan
     solos a la mesa (render con un proceso, ≈ 1.6× la duración por formato; `revisar` deja `revision/mesa_<formato>_N.jpg`);
     en `sin-voz` y `fixture`, `grabar` usa el borrador del plano. En la mesa, el gancho abre con «¿Sabías que…?» y su visual ya puestos en el cuadro 0 (pareja → `barra`, llenado o figuras → cifra, lugar → mapa); la tarjeta del dato es un **tablero**; el cierre es una sola pantalla con «Sígueme en». Guía: `referencias/flujo-mesa.md`.
   - `grabar <TRABAJO>` (V13) → `montar <TRABAJO>` (V8) → `revisar <TRABAJO>`; lee **una vez** `revision/contacto.png`
     (texto cortado, una pantalla vacía o quieta, el «¿SABÍAS QUE…?» que no se lee). Si falla V13, acorta ese texto en
     `guion.json`, repasa `guion --check` y repite desde `tiempos`.
   - Luego el 4:5: `grabar`, `montar` y `revisar` con `--formato 4:5`.
7. **ENTREGAR** (no con `sin-voz`: ahí abre `<TRABAJO>/salida/video.mp4` y pasa al reporte)
   - `python3 scripts/sabias.py entregar <TRABAJO>` → `datos/<fecha>-<slug>/video/`.
   - `python3 scripts/memoria.py --sabias datos/<fecha>-<slug>/video` y `make validate` (exit 0).
   - Abre el `video.mp4` entregado con `open`.
8. **REPORTE**
   - Las rutas de `video.mp4` y `video_4x5.mp4`, la duración, la paleta y la música.
   - El dato y la cifra; por escena `E<n> · tipo · lo que dice la voz`; el visual del gancho y el apoyo.
   - Los puntajes del crítico y las vueltas; los créditos gastados (`audio/creditos.json`) y V11; los avisos.
   - El caption de TikTok, listo para pegar.
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo): lo que se trabó o se hizo a mano, con el
     archivo y el cambio propuesto. Regístralas con `python3 scripts/memoria.py --mejoras <TRABAJO>/mejoras.json`
     (`{"flujo": "sabias", "pieza": "<carpeta de entrega>", "mejoras": [{"area", "archivo", "problema", "propuesta"}]}`)
     y no las apliques sin que el usuario lo pida. Con `sin-voz` o `fixture` se listan, no se registran.

Reglas:
- Solo cifras verificadas del dato (V2); el gancho dice el dato, no lo esconde.
- El cierre siempre termina con «Sígueme en» (solo en pantalla; la voz no lo dice).
- Una retoma de voz se hace por nodo, nunca del video entero.
- `sesiones/<slug>/sabias/` queda como memoria de trabajo; el mp4 no se commitea.
