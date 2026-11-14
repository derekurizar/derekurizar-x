---
description: Un evento o una historia de Guatemala contada de principio a fin en un video vertical de 2–3 min para TikTok, Reels y Shorts, más su 4:5 — editor que encuadra (pregunta, arco, tres actos y espina, hilos, personajes), investigadores y verificadores por eje (hechos con fecha y cita guardada, segunda fuente, cuatro veredictos, fotos con licencia), gancho elegido por el crítico, guionista que escribe primero la narración de corrido y la reparte en escenas de foto, cita, gráficos de los hilos y animaciones de la biblioteca con rótulos de acto; voz grabada por secuencias; cierre siempre con «Sígueme en» (uso — /historia <tema> [sin-voz]; p. ej. /historia cómo nació Pollo Campero; voz de ElevenLabs ≈ 1,800–2,600 créditos; sin-voz arma el video con voz falsa, 0 créditos)
---

Eres el coordinador del flujo **/historia** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- `<tema>`: la historia que se cuenta (cualquier evento o historia de Guatemala: una marca, una empresa, una persona, un
  proceso, un caso de justicia de principio a fin…). Sin tema, pregúntalo.
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos), para revisar el video antes de gastar (sin entrega ni registro).
- `fixture`: corre `make historia-fixture` (la maqueta, sin web ni voz) y termina. La maqueta corre en la mesa con
  `MESA_RENDER=0`: pasa los gates del plano y `hyperframes check`, pero el video es un doble sin render (un fondo liso
  con el audio; no se puede entregar). Para ver el dibujo real, `make video-fixture-mesa` (render en HyperFrames) y abre
  `sesiones/_fixture_mesa/trabajo/salida/video.mp4`.

La guía es `referencias/flujo-historia.md`. Nunca publiques. Nunca generes música ni efectos (catálogos fijos de
`/video`). **El guion que el crítico rechaza no se graba con voz sin decisión del usuario.**

**Quién dibuja** (decisión del usuario, 2026-11-14): el video se dibuja con la **mesa de archivo** en HyperFrames
(`referencias/flujo-mesa.md`): con cada oración de la voz entra en pantalla una pieza que la voz nombra y se queda
quieta. `preparar` lo fija en `video.json` (`"realizacion": "mesa"`) y de ahí sale el paso **Plano** (paso 6), entre
la voz y la grabación. Los comandos de producción son los mismos. Un TRABAJO creado con
`preparar … --realizacion propio` (o anterior al 2026-11-14, sin `realizacion` en `video.json`) se dibuja con el motor
propio (`video/*.html` + `video_grabar.js`): no lleva Plano y sigue los pasos 3, 5, 7 y 10 en su variante «motor
propio». Un trabajo empezado con un motor termina con ese motor.

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - `python3 scripts/historia.py preparar "<tema>"`: anota `TRABAJO` (la última línea: `sesiones/historia-<slug>`).
     Deja `"realizacion": "mesa"` en `video.json`; `--realizacion propio` solo si el usuario pide el motor viejo.
     Si avisa que la historia ya se contó, dilo y pregunta si sigue con otro ángulo. Si `TRABAJO` ya tiene
     `guion.json`, pregunta si se reutiliza o se empieza de nuevo.
   - Salvo con `sin-voz`, carga con ToolSearch `creative_create_flow`, `creative_add_flow_node`,
     `creative_run_flow_nodes`, `creative_get_flow_run_status` y `creative_transcribe_audio` del MCP de ElevenLabs.
   - Avisa: el Workflow tarda ~20–40 min (investigación y verificación con web, 0 créditos); después van la voz, el
     Plano (un agente, 0 créditos) y el render: en la mesa, ≈ 1.6× la duración por formato con un solo proceso (≈ 4 min
     por formato para 2.5 min de video; el 9:16 y el 4:5 van en fila). La voz cuesta ≈ 1 crédito por carácter
     (~1,800–2,600 en 2–3 min).
2. **INVESTIGACIÓN, GUION Y CRÍTICA (Workflow `historia`)**
   - Lanza el Workflow con `name: "historia"` y `args: {"trabajo": "<TRABAJO>", "tema": "<tema>"}`. Si editaste
     `.claude/workflows/historia.js` o los agentes en esta sesión, pásalo con `scriptPath:
     ".claude/workflows/historia.js"`; para reanudar, `resumeFromRunId`.
   - `desde` admite tres entradas sobre un TRABAJO que ya tiene `historia.json`, `ganchos.json` y `seleccion.json`:
     `"encuadre"` (re-encuadre: el editor añade actos, espina, hilos y personajes sobre la cronología verificada y
     sigue al guion; para volver a contar por actos una historia vieja, antes `python3 scripts/historia.py hechos
     <TRABAJO> --reclasificar` y, revisado, `--aplicar`), `"guion"` (salta directo a Guion) y `"retoque"` (paso 10).
   - **El usuario elige el gancho** (usuario, 2026-11-03: «siempre me pones a escoger entre 5 opciones»): sin
     `args.gancho`, el Workflow se detiene tras la Selección con `veredicto: "elegir_gancho"` (los 5 candidatos y el
     recomendado del crítico). Corre `python3 scripts/historia.py ganchos <TRABAJO> --opciones` y pregunta con AskUserQuestion:
     4 botones con la pantalla y la voz de cada opción (la recomendada primero, con «(Recomendado)»), la quinta escrita en
     el texto de la pregunta («o escribe 5 en Otro»); en «Otro» también puede dictar su propio gancho. Con un id:
     `python3 scripts/historia.py ganchos <TRABAJO> --elegir <id>` y relanza el Workflow con `resumeFromRunId` y los mismos args
     más `"gancho": "<id>"` (lo ya hecho vuelve de la caché); con su texto, los mismos args más `"gancho_usuario": "<su
     texto literal>"` (el agente de ganchos lo arma como candidato `gu` y lo elige). Si ya no se puede reanudar (otra
     sesión), escribe la elección con `ganchos --elegir <id>` y lanza con `"desde": "guion"`. `"auto": true` deja la recomendación del crítico (solo si el usuario lo pide).
   - **El usuario elige el cierre**: con el guion aprobado, el Workflow devuelve `cierres` (5 opciones en
     `cierres.json`; `c1` es la del guion). ANTES de la voz, `python3 scripts/historia.py cierres <TRABAJO> --opciones` y
     pregunta igual (`c1` primero). Con otro id: `python3 scripts/historia.py cierres <TRABAJO> --usar <id>`; con su texto:
     `--propio "<su texto>"` con `--forma`, `--mecanismo`, `--quien` y `--verbo` que casen con su frase
     (`referencias/cierres.md`; si dicta solo la frase final, se queda la oración del guion que la prepara). El script repasa narracion y guion: si fallan, deja el guion como estaba.
     Si el gate la rechaza, muéstrale la falla y propón la versión más cercana que pasa; nunca edites `guion.json` a
     mano. Si `cierres` viene `null` (el agente no pudo), pregunta con el cierre del guion o el suyo (`--propio`).
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
     usuario** si sigue así o lanza un retoque con ellas (paso 10; las que traen `cambios` se aplican tal cual con
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
     (paso 10), nunca editando `guion.json` a mano.
   - **En la mesa**, las fotos del guion son la **semilla** del plano, no el dibujo final: la del gancho va en el cuadro
     0 sobre papel, con su pie y su crédito (no a sangre), y el realizador puede bajar otras en el paso Plano (ids
     `pl-fNN`, en `recursos` de su retorno). Si las baja, repite `fotos-contacto` después del Plano y aplica el mismo
     criterio; una foto del plano que no sirve se cambia con un retoque de pantalla (paso 10), no en `guion.json`.
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
   - **El estado en línea** (m045, m047): si `creative_get_flow_run_status` devuelve la respuesta en el chat y no en un archivo
     (pasa con pocas sesiones), escríbela TAL CUAL a `<TRABAJO>/audio/estado.json` y pásale ese archivo a `descargar --estado`;
     valen las `words` en línea de Scribe. `descargar` falla si una transcripción no casa con ninguna escena.
     Pegado vale como venga (m111): con texto alrededor, la lista de bloques del MCP o varias respuestas seguidas en un
     mismo archivo (un estado por lote), o por stdin con `--estado -`. Lo mínimo que se usa: `generations[]` (id,
     modality, status, content_url, prompt, price), `media[]` (generation_id, prompt) y `transcripts[]` (text, words o
     words_download_url, source.url). No hace falta reconstruir nada a mano.
   - **Concurrencia** (m112): ElevenLabs corre pocas generaciones a la vez; con más de 3 nodos, las demás quedan
     pendientes y se reintentan solas. Corre los nodos en lotes de ≤ 3 (`creative_run_flow_nodes` con ese lote),
     sondea sus sesiones con `creative_get_flow_run_status` hasta `all_completed` y sigue con el lote siguiente; para
     esperar, un `sleep` en segundo plano (en primer plano está bloqueado).
5. **TIEMPOS Y ESCUCHA**
   - `python3 scripts/historia.py tiempos <TRABAJO>` (V6; V10 y H5, avisos). Si una escena no se alinea, rehaz SOLO
     ese nodo y repite; si falla la frontera de una secuencia, regrábala entera o esas escenas con `voz --sueltas`.
     En la mesa, `tiempos` no avisa V10, V22 ni V26: el ritmo, la carga y las cifras se miden sobre el plano (MV1,
     MV2, MV6) en el paso 6.
   - Con voz real, `python3 scripts/historia.py escuchar <TRABAJO>` (V11). Una `FALLA V11` → retoma de esa escena una
     vez; si vuelve a fallar, pide al usuario oírla.
6. **PLANO** (solo en la mesa: `video.json` con `"realizacion": "mesa"`; con el motor propio, salta al paso 7)
   - El guion visual es `<TRABAJO>/plano.json`: qué pieza entra con cada oración. Se escribe **después de `tiempos`**
     (con la voz real ya medida) y **antes de `grabar`**. No cambia el guion ni la voz y cuesta 0 créditos.
   - Lanza `Workflow({ name: "plano", args: { trabajo: "<TRABAJO>" } })`. Hasta reiniciar Claude Code (el workflow y
     el agente `video-realizador` son nuevos), con `scriptPath: ".claude/workflows/plano.js"` y
     `args.permitir_fallback: true`. El realizador (opus) parte de `python3 scripts/historia.py plano <TRABAJO>
     --digesto`, escribe `plano.json` y deja `python3 scripts/historia.py plano <TRABAJO> --check --hoja` (gates
     MV1–MV14, `referencias/flujo-mesa.md`) en 0 fallas.
   - **`veredicto: "plano_listo"`**: muestra al usuario `<TRABAJO>/plano.md` (la hoja de golpes: cada mesa con su
     golpe de arriba y, por oración, la pieza que entra) y sigue con el paso 7. Lee `nota` (lo que el realizador no
     pudo resolver) y `recursos` (lo que bajó: si hay fotos, repite `fotos-contacto`, paso 3).
   - **`veredicto: "plano_pendiente"`**: muestra las `fallas`. Relanza el mismo Workflow (conserva el plano y arregla
     solo lo que el gate marca) o, si la falla pide una decisión (no hay archivo real para un tramo, una foto de un
     proceso sin nombre en la voz), pregunta al usuario. Nunca grabes con el gate en falla: `grabar` lo vuelve a correr
     y se detiene.
   - Lo que falle en pantalla (MV8 tiempo de lectura, MV10 zona segura, MV11 tamaño, MV2 hueco sin pieza) se arregla
     **en el plano**, sin tocar `guion.json` ni la voz. Para retocar un plano ya escrito (quitar una pieza, otra foto,
     otro golpe de arriba), el mismo Workflow con `args.notas: "<lo que pidió el usuario, literal>"`.
   - Con `sin-voz` el paso corre igual, sobre los tiempos de la voz falsa; si después se graba la voz real, repite
     `tiempos` y `plano <TRABAJO> --check --hoja` antes de grabar.
7. **GRABAR, MONTAR Y REVISAR**
   - En segundo plano desde el inicio (`run_in_background`: el render pasa los 600 s del Bash; m042). De una vez:
     `python3 scripts/historia.py producir <TRABAJO>` (tiempos → escuchar → `plano --check --hoja` → grabar → montar →
     revisar en 9:16 y luego en 4:5; se detiene con «falta la fase Plano» si no hay `plano.json`).
   - **En la mesa**:
     - `grabar <TRABAJO>` = los gates del plano, los tableros limpios (las escenas con animación propia, grabadas con
       el motor propio: V7, A1 y A2 valen ahí), el proyecto de HyperFrames, `hyperframes check` y el render con **un
       solo proceso** (≈ 1.6× la duración). No hay `grabar --solo`: si cambia una voz o el plano, se graba entero.
     - `montar <TRABAJO>` (V8) = una sola mezcla de audio para los dos formatos (voz, música, efectos del plano,
       −14 LUFS), el `.srt`, `caption.md` y la portada limpia (el cuadro del gancho sin subtítulos ni barra).
     - `revisar <TRABAJO>` = la hoja de contacto del video final. Lee **una vez** `revision/contacto.png`: una pieza
       cortada, un texto que no se lee, una foto mal elegida, una mesa vacía. Lo que veas mal se arregla con un
       retoque de pantalla (paso 10: Workflow `plano` con `notas`) y otro `grabar`; nunca acortando el guion.
     - Luego el 4:5, **después** del 9:16 (usa su mezcla de audio): `grabar <TRABAJO> --formato 4:5`, `montar <TRABAJO>
       --formato 4:5`, `revisar <TRABAJO> --formato 4:5` (`revision/contacto_4x5.png`).
     - La versión B del gancho (`variante`) aún no existe en la mesa.
   - **Con el motor propio** (`--realizacion propio`): `grabar <TRABAJO>` (V7, V13) → `montar <TRABAJO>` (V8) →
     `revisar <TRABAJO>`; lee **una vez** `revision/contacto.png` y **una vez** `revision/linea_tiempo.png` (texto
     cortado, una foto mal encuadrada, una cita ilegible, un rótulo de acto que tapa el titular). Si falla V13, acorta
     ese texto en `guion.json`, repasa `guion --check` y repite desde `tiempos`. Luego el 4:5 con los mismos tres
     comandos y `--formato 4:5`.
   - Abre `<TRABAJO>/salida/video.mp4` con `open`.
8. **ENTREGA** (salvo con `sin-voz`)
   - `python3 scripts/historia.py entregar <TRABAJO>` → `historias/<fecha>-<slug>/` (`video.mp4` para TikTok, Reels y
     Shorts, `video_4x5.mp4` para el feed, `caption.md`, `subtitulos.srt`, portadas, `fuentes.md` por acto con los
     créditos de las fotos, `cronologia.md` y el `guion.json` de entrega; las fotos no se copian).
   - `python3 scripts/memoria.py --historia historias/<fecha>-<slug>` (`--estado incompleto` si el crítico no
     aprobó y el usuario decidió seguir) y `make validate` (M10).
9. **REPORTE**
   - La ruta del video (9:16 y 4:5), la duración (120–180 s), la paleta y la música.
   - El encuadre (pregunta, arco, los tres actos con su espina, los hilos) y, por escena, `E<n> · acto · tipo · lo que
     muestra · foto (origen y licencia)`; los rótulos de acto.
   - En la mesa, el plano: mesas, piezas, cuántas son archivo real (`piezas` y `archivo_real` del retorno del
     Workflow `plano`), los recursos que bajó el realizador y su `nota`.
   - La narración: palabras (320–400), «según» en voz (≤ 4) y con qué fuentes, hilos pagados (en qué escena) y sin
     respuesta, secuencias de voz (cuántas y qué escenas).
   - Hechos confirmados, de una fuente, en disputa y descartados por eje (con su motivo); casos y su estado si es de
     justicia.
   - El gancho elegido y el segundo; los puntajes del crítico, las vueltas y las mejoras no aplicadas (con su motivo).
   - Las animaciones reutilizadas o creadas (quedan en la biblioteca).
   - Los créditos de voz (`audio/creditos.json`) y V11; los avisos (H5 y flashback; con el motor propio, también
     V10, V12 y V15; en la mesa, los de `plano --check` y de `hyperframes check`).
   - La carpeta de entrega y el registro en `memoria/historias.json`.
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo): lo que en esta corrida se trabó o se
     resolvió a mano (un arreglo del crítico que el gate rechazó: `arreglos_rechazados`) —una falla o un aviso que se
     repite entre corridas, un gate con falso positivo o negativo, un paso que hubo que hacer a mano, uno lento o
     frágil, un recorte V16 que se repite—, cada una con el archivo y el cambio propuesto. Regístralas con `python3
     scripts/memoria.py --mejoras <TRABAJO>/mejoras.json` (`{"flujo": "historia", "pieza": "<carpeta de entrega>",
     "mejoras": [{"area", "archivo", "problema", "propuesta"}]}`) y no las apliques sin que el usuario lo pida; las
     que ya quedaron arregladas van con `"estado": "hecha"`. Con `sin-voz` o `fixture` se listan, no se registran.
10. **RETOQUES** (cuando el usuario pida un cambio tras aprobar o grabar: otro gancho, otra foto, reescribir una
   escena, otro cierre, quitar una cita)
   - **Retoque de pantalla** (en la mesa: otra pieza, otra foto, quitar un recorte, otro golpe de arriba, una pieza
     que no da tiempo de leerse): no toca el guion ni la voz. Workflow `plano` con `args: {"trabajo": "<TRABAJO>",
     "notas": "<lo que pidió el usuario, literal>"}` → `plano_listo` → muestra `plano.md` → `grabar` → `montar` →
     `revisar` en 9:16 y en 4:5 (el video se graba entero) → `entregar`.
   - **Retoque de texto o de voz**: NO edites `guion.json` a mano. Lanza el Workflow `historia` con `args: {"trabajo":
     "<TRABAJO>", "tema": "<tema>", "desde": "retoque", "notas": "<lo que pidió el usuario, literal>"}`: el guionista
     aplica solo eso y conserva las demás voces → gate → oyente → crítico (1 vuelta) → mejoras → animación. Lee
     `veredicto` y `voces_cambiadas`; si no pasa, pregunta. Si las voces que cambian cuestan créditos que el usuario
     no pidió, dilo antes de generarlas.
   - `python3 scripts/historia.py voz <TRABAJO> --pendientes` (las secuencias enteras con alguna escena cuya voz
     difiere de `audio/palabras_N.json` o sin audio, con sus créditos; o `--sueltas` para regrabar solo esas escenas
     como nodos propios) → genera SOLO esos nodos en el MCP (paso 4) → `descargar --estado` (corta las secuencias).
   - **En la mesa**: `tiempos` → `escuchar` → `plano <TRABAJO> --check --hoja` (los `dice` del plano son palabras de
     la voz: si la voz de una escena cambió, sus golpes pueden quedar sin palabra o sin tiempo de lectura; lo que
     falle se arregla con el Workflow `plano` y `notas` que digan qué escenas cambiaron) → `grabar` (entero; no hay
     `--solo`) → `montar` → `revisar`, en 9:16 y luego en 4:5 → `entregar` → `memoria.py --historia` (reemplaza el
     registro del mismo slug) → `make validate`.
   - **Con el motor propio**: `tiempos` → `escuchar` → `grabar <TRABAJO> --solo <n,…>` (y `--formato 4:5`) → `montar`
     → `revisar` → `entregar` → `memoria.py --historia` → `make validate`.

Reglas:
- Solo hechos `confirmado`, `una_fuente` (narrados llano con la fuente en pantalla) o `en_disputa` (atribuidos en voz,
  como los alegatos, las estimaciones, las opiniones y las citas; ≤ 4 «según»); cada número y cada año con su cita
  guardada.
- Wikipedia no es fuente. Fotos solo con licencia libre o crédito de su dueño.
- Presunción de inocencia: nadie es culpable sin sentencia firme; el estado del caso, a la fecha.
- El cierre siempre termina con «Sígueme en» (solo en pantalla).
- `sesiones/historia-<slug>/` queda como memoria de trabajo; los mp4 (también los de `historias/`) no se commitean.
