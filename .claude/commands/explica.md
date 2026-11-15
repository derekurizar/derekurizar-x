---
description: Un concepto, un proceso o una regla explicado en un video vertical de ~2 min (9:16 + 4:5) para que quien lo vea pueda explicárselo a otro: la pregunta, el mecanismo y en tu vida, con números de ejemplo calculados por el script (uso — /explica &lt;tema&gt; [corto|medio|largo] [sin-voz|fixture]; voz ≈ 1,700 créditos en medio; el hilo en modo explica es /hilo explica)
---

Eres el coordinador del flujo **/explica** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- `<tema>`: el concepto, el proceso o la regla que se explica (el interés compuesto, cómo se calcula la tarifa de luz,
  cómo se elige a un diputado…). Sin tema, pregúntalo.
- `corto` (~60 s) · `medio` (~2 min, por defecto) · `largo` (~165 s).
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos), para revisar el video antes de gastar (sin entrega ni registro).
- `fixture`: corre `make explica-fixture` (la maqueta del interés compuesto, sin web ni voz), abre el video y termina.

La guía es `referencias/flujo-explica.md`. Nunca publiques. Nunca generes música ni efectos (catálogos fijos de
`/video`). **El guion que el crítico rechaza no se graba con voz sin decisión del usuario.** El hilo en modo explica
(tarjetas, sin video) es `/hilo explica`: si el usuario pidió un hilo, no es este flujo.

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - `python3 scripts/explica.py preparar "<tema>" [--duracion corto|largo]`: anota `TRABAJO` (la última línea:
     `sesiones/explica-<slug>`). Si avisa que el tema ya se explicó, dilo y pregunta si sigue con otro ángulo. Si
     `TRABAJO` ya tiene `guion.json`, pregunta si se reutiliza o se empieza de nuevo.
   - Salvo con `sin-voz`, carga con ToolSearch `creative_create_flow`, `creative_add_flow_node`,
     `creative_run_flow_nodes`, `creative_get_flow_run_status` y `creative_transcribe_audio` del MCP de ElevenLabs.
   - Avisa: el Workflow tarda ~15–30 min (investigación y verificación con web, 0 créditos); la voz y el render, ~8–12
     min; la voz cuesta ≈ 1 crédito por carácter (~1,700 en medio).
2. **INVESTIGACIÓN, GUION Y CRÍTICA (Workflow `explica`)**
   - Lanza el Workflow con `name: "explica"` y `args: {"trabajo": "<TRABAJO>", "tema": "<tema>"}`. Si editaste
     `.claude/workflows/explica.js` o los agentes en esta sesión, pásalo con `scriptPath: ".claude/workflows/explica.js"`;
     para reanudar, `resumeFromRunId`. `desde: "guion"` salta directo a Guion (con `explicacion.json`, `ganchos.json` y
     `seleccion.json`); `desde: "retoque"` es el paso 9.
   - **El usuario elige el gancho** (usuario, 2026-11-03: «siempre me pones a escoger entre 5 opciones»): sin
     `args.gancho`, el Workflow se detiene tras la Selección con `veredicto: "elegir_gancho"` (los 5 candidatos y el
     recomendado del crítico). Corre `python3 scripts/explica.py ganchos <TRABAJO> --opciones` y pregunta con AskUserQuestion:
     4 botones con la pantalla y la voz de cada opción (la recomendada primero, con «(Recomendado)»), la quinta escrita en
     el texto de la pregunta («o escribe 5 en Otro»); en «Otro» también puede dictar su propio gancho. Con un id:
     `python3 scripts/explica.py ganchos <TRABAJO> --elegir <id>` y relanza el Workflow con `resumeFromRunId` y los mismos args
     más `"gancho": "<id>"` (lo ya hecho vuelve de la caché); con su texto, los mismos args más `"gancho_usuario": "<su
     texto literal>"` (el agente de ganchos lo arma como candidato `gu` y lo elige). Si ya no se puede reanudar (otra
     sesión), escribe la elección con `ganchos --elegir <id>` y lanza con `"desde": "guion"`. `"auto": true` deja la recomendación del crítico (solo si el usuario lo pide).
   - **El usuario elige el cierre**: con el guion aprobado, el Workflow devuelve `cierres` (5 opciones en
     `cierres.json`; `c1` es la del guion). ANTES de la voz, `python3 scripts/explica.py cierres <TRABAJO> --opciones` y
     pregunta igual (`c1` primero). Con el id que elija (también `c1`: así queda registrado quién eligió; con `auto`, `--usar c1 --por critico`): `python3 scripts/explica.py cierres <TRABAJO> --usar <id>`; con su texto:
     `--propio "<su texto>"` con `--forma`, `--mecanismo`, `--quien` y `--verbo` que casen con su frase
     (`referencias/cierres.md`; si dicta solo la frase final, se queda la oración del guion que la prepara). El script repasa narracion y guion: si fallan, deja el guion como estaba.
     Si el gate la rechaza, muéstrale la falla y propón la versión más cercana que pasa; nunca edites `guion.json` a
     mano. Si `cierres` viene `null` (el agente no pudo), pregunta con el cierre del guion o el suyo (`--propio`).
   - Si falla con «no está registrado», pide al usuario reiniciar Claude Code; solo si lo autoriza, relanza con
     `args.permitir_fallback: true`.
   - Al volver, lee `veredicto`, `puntajes` (con `claridad` e `intuicion`), `oyente.explicacion_devuelta` (cómo un
     oyente que solo oyó la voz te devuelve el mecanismo), `faltas_pendientes`, `mejoras_no_aplicadas` y, del guion,
     `palabras`, `intuicion` → `corrige`, `ilustrativas` (escenas con el chip «Ejemplo»). Si `veredicto` no es `"pasa"`,
     muestra las faltas y **pregunta al usuario** si sigue así o lanza un retoque (paso 9); nunca edites `guion.json` a
     mano.
   - Corre tú `python3 scripts/explica.py guion <TRABAJO> --check` (exit 0: confirma `locucion.json`).
3. **REVISIÓN DE LOS NÚMEROS**
   - `python3 scripts/explica.py ejemplos <TRABAJO>`: cada número de ejemplo con su fórmula. Comprueba que lo que dice la
     voz es lo que calculó el script y que las cifras reales de Guatemala dicen de cuándo son (`explicacion.json`).
   - Cualquier cambio después de la crítica va por **RETOQUES** (paso 9), nunca editando `guion.json` a mano.
4. **VOZ** (con `sin-voz`: `python3 scripts/explica.py voz-falsa <TRABAJO>` y salta al paso 5)
   - Sigue `referencias/fragmentos/voz-mcp.md` (lee ese archivo: nodos por secuencia, lotes de ≤ 3, `generations_count: 1`, Scribe y
     `descargar --nodos`) con `<script>` = `explica.py` y el flow «Explica · <tema corto>».
5. **TIEMPOS Y ESCUCHA**
   - `python3 scripts/explica.py tiempos <TRABAJO>` (V6, V10, V16; cada renglón de la pizarra cae cuando la voz dice su
     resultado). Si una escena no se alinea, rehaz SOLO ese nodo y repite.
   - Con voz real, `python3 scripts/explica.py escuchar <TRABAJO>` (V11: las cifras se oyen como se escriben). Una
     `FALLA V11` → retoma de esa escena una vez; si vuelve a fallar, pide al usuario oírla.
6. **GRABAR, MONTAR Y REVISAR**
   - **PLANO** (mesa de archivo, desde el 2026-11-14; todo TRABAJO nuevo trae `"realizacion": "mesa"` en `video.json`):
     después de `tiempos` y antes de `grabar`, lanza `Workflow({ name: "plano", args: { trabajo: "<TRABAJO>" } })`.
     Si falla con «agente no registrado», pide
     reiniciar Claude Code (los agentes se cargan al arrancar); el plano no se relanza con `permitir_fallback`: un
     realizador sin su agente triplica el contexto. El
     `video-realizador` escribe `<TRABAJO>/plano.json` (qué pieza entra con cada oración) y deja
     `python3 scripts/explica.py plano <TRABAJO> --check --hoja` en 0 (MV1–MV14). Con `plano_listo`, muestra
     `<TRABAJO>/plano.md` y sigue; con `plano_pendiente`, muestra las `fallas` y relánzalo (conserva el plano). Lo que
     falle en pantalla se arregla en el plano, nunca en el guion ni en la voz. `grabar`, `montar` y `revisar` despachan
     solos a la mesa (render con un proceso, ≈ 1.6× la duración por formato; `revisar` deja `revision/mesa_<formato>_N.jpg`);
     en `sin-voz` y `fixture`, `grabar` usa el borrador del plano. En la mesa, la pizarra (`cuenta`), la animación (`explica`), `adivina`, `escala` y las tarjetas son **tableros** (se graban limpios con el motor propio, solos en su mesa) y el chip «Ejemplo» lo pone la mesa arriba a la derecha sobre cada mesa con números de ejemplo; el gancho y los golpes pasan a piezas (nota, cifra, `barra` para la pareja). Guía: `referencias/flujo-mesa.md`.
   - `grabar <TRABAJO>` (V7, V13) → `montar <TRABAJO>` (V8) → `revisar <TRABAJO>`; lee **una vez**
     `revision/contacto.png` y **una vez** `revision/linea_tiempo.png`. Revisa:
     - la pizarra legible, con su resaltado en acento;
     - el chip «Ejemplo» solo donde hay números de ejemplo;
     - la animación del mecanismo;
     - los rótulos de acto.
   - Luego el 4:5: `grabar <TRABAJO> --formato 4:5`, `montar <TRABAJO> --formato 4:5`, `revisar <TRABAJO> --formato 4:5`.
   - Abre `<TRABAJO>/salida/video.mp4` con `open`.
7. **ENTREGA** (salvo con `sin-voz`)
   - `python3 scripts/explica.py entregar <TRABAJO>` → `explicaciones/<fecha>-<slug>/`:
     - `video.mp4` (TikTok, Reels, Shorts) y `video_4x5.mp4` (feed);
     - `caption.md`, `subtitulos.srt` y portadas;
     - `fuentes.md`, `ejemplos.md` (cada número de ejemplo con su fórmula) y el `guion.json` de entrega.
   - `python3 scripts/memoria.py --explica explicaciones/<fecha>-<slug>` (`--estado incompleto` si el crítico no aprobó
     y el usuario decidió seguir) y `make validate` (M12).
8. **REPORTE**
   - La ruta del video (9:16 y 4:5), la duración, la paleta y la música.
   - El encuadre: la pregunta, la idea equivocada, el mecanismo y su frase; lo que el oyente devolvió
     (`explicacion_devuelta`).
   - Por escena: `E<n> · acto · tipo · lo que muestra · «Ejemplo» si va`, con los rótulos de acto.
   - La narración: palabras, «según» en voz, secuencias de voz.
   - Las afirmaciones y los datos de Guatemala con su estado y su fuente; los ejemplos calculados (ilustrativos y reales).
   - El gancho elegido y el segundo; los puntajes del crítico, las vueltas y las mejoras no aplicadas.
   - Las animaciones reutilizadas o creadas (quedan en la biblioteca).
   - Los créditos de voz y V11; los avisos (E9, V10, V12).
   - La carpeta de entrega y el registro en `memoria/explicaciones.json`.
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo), como en `/historia`. Regístralas con
     `python3 scripts/memoria.py --mejoras <TRABAJO>/mejoras.json` (`{"flujo": "explica", …}`) y no las apliques sin que
     el usuario lo pida. Con `sin-voz` o `fixture` se listan, no se registran.
9. **RETOQUES** (cuando el usuario pida un cambio tras aprobar o grabar)
   - NO edites `guion.json` a mano. Lanza el Workflow `explica` con `args: {"trabajo": "<TRABAJO>", "tema": "<tema>",
     "desde": "retoque", "notas": "<lo que pidió el usuario, literal>"}`. Lee `veredicto` y `voces_cambiadas`; si no
     pasa, pregunta. Si las voces que cambian cuestan créditos que el usuario no pidió, dilo antes de generarlas.
   - `python3 scripts/explica.py voz <TRABAJO> --pendientes` (o `--sueltas`) → genera SOLO esos nodos → `descargar
     --estado` → `tiempos` → `escuchar` → `grabar --solo <n,…>` (y `--formato 4:5`) → `montar` → `revisar` → `entregar`
     → `memoria.py --explica` → `make validate`.

Reglas:
- Lo que el video afirma y cada dato de Guatemala salen de `explicacion.json` (verificados, con su cita guardada). Los
  números de ejemplo los calcula `explica.py`: nunca un agente; la voz los dice como ejemplo y la pantalla lleva el chip
  «Ejemplo».
- No es consejo: ni «deberías», ni bancos, ni productos (E10).
- El cierre siempre termina con «Sígueme en» (solo en pantalla).
- `sesiones/explica-<slug>/` queda como memoria de trabajo; los mp4 (también los de `explicaciones/`) no se commitean.
