---
description: Un evento o una historia de Guatemala contada de principio a fin en un video vertical de 2–3 min para TikTok, Reels y Shorts, más su 4:5 — editor que encuadra (pregunta, arco, tres actos y espina, hilos, personajes), investigadores y verificadores por eje (hechos con fecha y cita guardada, segunda fuente, cuatro veredictos, fotos con licencia), gancho elegido por el crítico, guionista que escribe primero la narración de corrido y la reparte en escenas de foto, cita, gráficos de los hilos y animaciones de la biblioteca con rótulos de acto; voz grabada por secuencias; cierre siempre con «Sígueme en» (uso — /historia <tema> [sin-voz]; p. ej. /historia cómo nació Pollo Campero; voz de ElevenLabs ≈ 1,800–2,600 créditos; sin-voz arma el video con voz falsa, 0 créditos)
---

Eres el coordinador del flujo **/historia** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- `<tema>`: la historia que se cuenta (cualquier evento o historia de Guatemala: una marca, una empresa, una persona, un
  proceso, un caso de justicia de principio a fin…). Sin tema, pregúntalo.
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos), para revisar el video antes de gastar (sin entrega ni registro).
- `fixture`: corre `make historia-fixture` (la maqueta, sin web ni voz), abre el video y termina.

La guía es `referencias/flujo-historia.md`. Nunca publiques. Nunca generes música ni efectos (catálogos fijos de
`/video`). **El guion que el crítico rechaza no se graba con voz sin decisión del usuario.**

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - `python3 scripts/historia.py preparar "<tema>"`: anota `TRABAJO` (la última línea: `sesiones/historia-<slug>`).
     Si avisa que la historia ya se contó, dilo y pregunta si sigue con otro ángulo. Si `TRABAJO` ya tiene
     `guion.json`, pregunta si se reutiliza o se empieza de nuevo.
   - Salvo con `sin-voz`, carga con ToolSearch `creative_create_flow`, `creative_add_flow_node`,
     `creative_run_flow_nodes`, `creative_get_flow_run_status` y `creative_transcribe_audio` del MCP de ElevenLabs.
   - Avisa: el Workflow tarda ~20–40 min (investigación y verificación con web, 0 créditos); la voz y el render,
     ~8–12 min; la voz cuesta ≈ 1 crédito por carácter (~1,800–2,600 en 2–3 min).
2. **INVESTIGACIÓN, GUION Y CRÍTICA (Workflow `historia`)**
   - Lanza el Workflow con `name: "historia"` y `args: {"trabajo": "<TRABAJO>", "tema": "<tema>"}`. Si editaste
     `.claude/workflows/historia.js` o los agentes en esta sesión, pásalo con `scriptPath:
     ".claude/workflows/historia.js"`; para reanudar, `resumeFromRunId`.
   - `desde` admite tres entradas sobre un TRABAJO que ya tiene `historia.json`, `ganchos.json` y `seleccion.json`:
     `"encuadre"` (re-encuadre: el editor añade actos, espina, hilos y personajes sobre la cronología verificada y
     sigue al guion; para volver a contar por actos una historia vieja, antes `python3 scripts/historia.py hechos
     <TRABAJO> --reclasificar` y, revisado, `--aplicar`), `"guion"` (salta directo a Guion) y `"retoque"` (paso 9).
   - Si falla con «no está registrado», pide al usuario reiniciar Claude Code; solo si lo autoriza, relanza con
     `args.permitir_fallback: true`.
   - Si falla por pocos hechos publicables, muestra lo descartado (`historia.json → descartados`) y pregunta si se
     cambia el ángulo.
   - Si avisa «sigue sin foto del protagonista» (H12), baja una tú (`python3 scripts/historia.py hechos <TRABAJO>
     --check` imprime las og:image candidatas con el comando `foto --de-fuente … --protagonista` listo) y relanza con
     `resumeFromRunId`.
   - Al volver, lee `veredicto`, `puntajes` (con `flujo`), `faltas_pendientes`, `mejoras_no_aplicadas`, `oyente` (lo
     que un oyente que solo oyó la voz no entendió; el crítico lo resolvió o lo justificó) y, del guion, `actos`,
     `palabras` (320–400), `segun` (≤ 4) e `hilos` (pagados y sin respuesta). `aprobado_por: "arreglos_probados"`
     quiere decir que la última crítica solo bloqueaba con arreglos ya probados y el Workflow los aplicó
     (`aplicadas_al_cierre`): dilo en el reporte. Si `veredicto` no es `"pasa"`, muestra las faltas y **pregunta al
     usuario** si sigue así o lanza un retoque con ellas (paso 9; las que traen `cambios` se aplican tal cual con
     `historia.py aplicar`); nunca edites `guion.json` a mano. Si pasa, el Workflow ya hizo
     que el guionista aplicara las mejoras del crítico (también las de voz) y repasara el gate; las que no pudo aplicar
     (`mejoras_no_aplicadas`, con su motivo) van al reporte: no las apliques a mano.
   - Corre tú `python3 scripts/historia.py guion <TRABAJO> --check` (exit 0: confirma `locucion.json`).
3. **QA DE FOTOS**
   - `python3 scripts/historia.py fotos-contacto <TRABAJO>` y lee **una vez** `<TRABAJO>/fotos/contacto.png`. Si una
     foto muestra víctimas, cadáveres o menores identificables, es de otra persona u otro lugar que el que dice su
     descripción, o es un logo genérico: cámbiala en `guion.json` por otra foto verificada (o una de referencia con
     `foto … --referencia`; nunca un icono ni un mapa, H7), o cambia el gancho por el segundo de `seleccion.json` con
     `ganchos --usar <id>`, y repasa `guion --check`.
   - Comprueba también que la foto del gancho muestra al protagonista (H12; el gate lo exige).
   - **Cualquier cambio después de la crítica** (otro gancho, otra foto, una escena, el cierre) va por **RETOQUES**
     (paso 9), nunca editando `guion.json` a mano.
4. **VOZ** (con `sin-voz`: `python3 scripts/historia.py voz-falsa <TRABAJO>` y salta al paso 5)
   - Di al usuario los caracteres de voz (`locucion.json → caracteres`) antes de gastar.
   - La voz va por **nodo**: una secuencia de 2–5 escenas grabada de corrido (`locucion.json → secuencias`) o una
     escena suelta (el gancho, el cierre, las que no caben en ninguna). `python3 scripts/historia.py voz <TRABAJO>`
     imprime un `prompt` por nodo; en una retoma, `voz <TRABAJO> --pendientes` imprime las secuencias enteras que hay
     que regrabar (y sus créditos) y `voz <TRABAJO> --sueltas` solo las escenas cambiadas como nodos propios.
   - `creative_create_flow` «Historia · <tema corto>»; un `creative_add_flow_node` por nodo (`node_type: "tts"`,
     `model_id: "eleven_multilingual_v2"`, el `voice_id` de la salida, `model_parameters: {"language_code": "es"}`, el
     `prompt` **exacto**); `creative_run_flow_nodes` con todos y **`generations_count: 1`**; sondea solo los
     `session_ids` pendientes; luego `creative_transcribe_audio` (`eleven_scribe_v1`) por nodo; **una sola**
     `creative_get_flow_run_status` con voz y Scribe (queda en un archivo) y `python3 scripts/historia.py descargar
     <TRABAJO> --estado <ese archivo>`: baja cada nodo y **corta** cada secuencia en sus escenas con los tiempos de
     Scribe (`audio/secuencias.json`). Si el prefijo de un prompt es ambiguo, el estado tiene que traer
     `media[].prompt` entero.
   - **Límite de 20**: `creative_run_flow_nodes` y `creative_get_flow_run_status` aceptan ≤ 20 ids. Con más de 10
     nodos, el estado final va en lotes de ≤ 20 sesiones (la voz de cada nodo con su Scribe en el mismo lote) y
     `descargar --estado A B …` recibe todos los archivos. Una respuesta muy grande la guarda la herramienta en un
     archivo: ese archivo es el que se pasa. Mientras sondeas, pide solo las sesiones pendientes.
5. **TIEMPOS Y ESCUCHA**
   - `python3 scripts/historia.py tiempos <TRABAJO>` (V6; V10 y H5, avisos). Si una escena no se alinea, rehaz SOLO
     ese nodo y repite; si falla la frontera de una secuencia, regrábala entera o esas escenas con `voz --sueltas`.
   - Con voz real, `python3 scripts/historia.py escuchar <TRABAJO>` (V11). Una `FALLA V11` → retoma de esa escena una
     vez; si vuelve a fallar, pide al usuario oírla.
6. **GRABAR, MONTAR Y REVISAR**
   - `grabar <TRABAJO>` (V7, V13) → `montar <TRABAJO>` (V8) → `revisar <TRABAJO>`; lee **una vez**
     `revision/contacto.png` y **una vez** `revision/linea_tiempo.png` (texto cortado, una foto mal encuadrada, una
     cita ilegible, un rótulo de acto que tapa el titular). Si falla V13, acorta ese texto en `guion.json`, repasa
     `guion --check` y repite desde `tiempos`.
   - Luego el 4:5: `grabar <TRABAJO> --formato 4:5`, `montar <TRABAJO> --formato 4:5`, `revisar <TRABAJO> --formato 4:5`.
   - Abre `<TRABAJO>/salida/video.mp4` con `open`.
7. **ENTREGA** (salvo con `sin-voz`)
   - `python3 scripts/historia.py entregar <TRABAJO>` → `historias/<fecha>-<slug>/` (`video.mp4` para TikTok, Reels y
     Shorts, `video_4x5.mp4` para el feed, `caption.md`, `subtitulos.srt`, portadas, `fuentes.md` por acto con los
     créditos de las fotos, `cronologia.md` y el `guion.json` de entrega; las fotos no se copian).
   - `python3 scripts/memoria.py --historia historias/<fecha>-<slug>` (`--estado incompleto` si el crítico no
     aprobó y el usuario decidió seguir) y `make validate` (M10).
8. **REPORTE**
   - La ruta del video (9:16 y 4:5), la duración (120–180 s), la paleta y la música.
   - El encuadre (pregunta, arco, los tres actos con su espina, los hilos) y, por escena, `E<n> · acto · tipo · lo que
     muestra · foto (origen y licencia)`; los rótulos de acto.
   - La narración: palabras (320–400), «según» en voz (≤ 4) y con qué fuentes, hilos pagados (en qué escena) y sin
     respuesta, secuencias de voz (cuántas y qué escenas).
   - Hechos confirmados, de una fuente, en disputa y descartados por eje (con su motivo); casos y su estado si es de
     justicia.
   - El gancho elegido y el segundo; los puntajes del crítico, las vueltas y las mejoras no aplicadas (con su motivo).
   - Las animaciones reutilizadas o creadas (quedan en la biblioteca).
   - Los créditos de voz (`audio/creditos.json`) y V11; los avisos (H5, V10, V12, V15, flashback).
   - La carpeta de entrega y el registro en `memoria/historias.json`.
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo): lo que en esta corrida se trabó o se
     resolvió a mano (un arreglo del crítico que el gate rechazó: `arreglos_rechazados`) —una falla o un aviso que se
     repite entre corridas, un gate con falso positivo o negativo, un paso que hubo que hacer a mano, uno lento o
     frágil, un recorte V16 que se repite—, cada una con el archivo y el cambio propuesto. Regístralas con `python3
     scripts/memoria.py --mejoras <TRABAJO>/mejoras.json` (`{"flujo": "historia", "pieza": "<carpeta de entrega>",
     "mejoras": [{"area", "archivo", "problema", "propuesta"}]}`) y no las apliques sin que el usuario lo pida; las
     que ya quedaron arregladas van con `"estado": "hecha"`. Con `sin-voz` o `fixture` se listan, no se registran.
9. **RETOQUES** (cuando el usuario pida un cambio tras aprobar o grabar: otro gancho, otra foto, reescribir una
   escena, otro cierre, quitar una cita)
   - NO edites `guion.json` a mano. Lanza el Workflow `historia` con `args: {"trabajo": "<TRABAJO>", "tema": "<tema>",
     "desde": "retoque", "notas": "<lo que pidió el usuario, literal>"}`: el guionista aplica solo eso y conserva las
     demás voces → gate → oyente → crítico (1 vuelta) → mejoras → animación. Lee `veredicto` y `voces_cambiadas`; si no
     pasa, pregunta. Si las voces que cambian cuestan créditos que el usuario no pidió, dilo antes de generarlas.
   - `python3 scripts/historia.py voz <TRABAJO> --pendientes` (las secuencias enteras con alguna escena cuya voz
     difiere de `audio/palabras_N.json` o sin audio, con sus créditos; o `--sueltas` para regrabar solo esas escenas
     como nodos propios) → genera SOLO esos nodos en el MCP (paso 4) → `descargar --estado` (corta las secuencias).
   - `tiempos` → `escuchar` → `grabar <TRABAJO> --solo <n,…>` (y `--formato 4:5`) → `montar` → `revisar` → `entregar`
     → `memoria.py --historia` (reemplaza el registro del mismo slug) → `make validate`.

Reglas:
- Solo hechos `confirmado`, `una_fuente` (narrados llano con la fuente en pantalla) o `en_disputa` (atribuidos en voz,
  como los alegatos, las estimaciones, las opiniones y las citas; ≤ 4 «según»); cada número y cada año con su cita
  guardada.
- Wikipedia no es fuente. Fotos solo con licencia libre o crédito de su dueño.
- Presunción de inocencia: nadie es culpable sin sentencia firme; el estado del caso, a la fecha.
- El cierre siempre termina con «Sígueme en» (solo en pantalla).
- `sesiones/historia-<slug>/` queda como memoria de trabajo; los mp4 (también los de `historias/`) no se commitean.
