---
description: Un dato impactante de Guatemala en UNA tarjeta 1080×1080 — investigación y verificación como /hilo, pero una sola imagen con texto del tuit y alt-text, sin hilo (uso — /dato [pista] [smoke|fixture]; la pista es opcional, tema, ángulo, fuente o corazonada; sin pista el investigador elige un dato de actualidad; no usa el banco de ideas)
---

Eres el coordinador del flujo **/dato** de @DerekUrizar. El usuario quiere UN
dato impactante, muy bien elaborado, en una sola tarjeta con su tuit. Su
argumento es una **pista** opcional: "$ARGUMENTS" (puede venir vacío). La
pista puede ser un tema («remesas»), un ángulo («lo que cuesta llenar el
tanque»), una fuente («lo último del INE») o una corazonada («un dato de
educación que sorprenda»); el investigador la usa como orientación y puede
desviarse si encuentra un dato más fuerte en su vecindad. Sin pista, elige por
su cuenta un dato de actualidad (fuentes oficiales recientes y
`scripts/fuentes.py`). Si contiene `smoke` es una corrida corta con web
(presupuestos cortos, salida en `sesiones/<slug>/salida/`; sin pista usa
«remesas familiares 2025»); si contiene `fixture` es una prueba SIN web que
copia `sesiones/_fixture_dato` y solo ejercita al productor. La guía vive en
`referencias/flujo-dato.md`. `/dato` no lee ni escribe `ideas/`.

1. PREFLIGHT: corre `make doctor` (exit 0). Salvo en `fixture`, haz una
   búsqueda de prueba con WebSearch; si falla → DETENTE y repórtalo. Obtén la
   fecha con `date +%F`. Si hay pista, corre `python3 scripts/memoria.py
   --datos "<pista>"` y mira `memoria/hilos.json`: si ya hay un dato o un hilo
   parecido, díselo al usuario (el investigador buscará otro ángulo o periodo;
   no abortes). No conviertas la pista en tema ni la reformules: pásala literal.
2. Avisa al usuario: una corrida normal tarda ~8–15 minutos con 4 agentes
   (investigador, verificador, guionista, productor); smoke ~5–8 minutos;
   fixture ~3 minutos. La publicación en X es manual.
3. Invoca la herramienta **Workflow** con `name: "dato"` y `args` como OBJETO:
   `{ "pista": "<pista literal sin smoke/fixture>"|null, "smoke": <bool>, "fixture": <bool>, "fecha": "<YYYY-MM-DD>" }`.
   - Si `.claude/workflows/dato.js` se editó en ESTA sesión, `name` resuelve una
     copia en caché: usa `scriptPath: ".claude/workflows/dato.js"`.
   - Si el workflow falla con «no está registrado en esta sesión», los agentes
     `.claude/agents/hilo-*.md` (los mismos de /hilo) se crearon o cambiaron en
     esta sesión: pide al usuario reiniciar Claude Code y relanzar. Solo si lo
     autoriza, relanza con `"permitir_fallback": true` (corre todo con
     general-purpose: más caro).
   - Para reanudar tras un fallo o una edición del script:
     `Workflow({ scriptPath, resumeFromRunId: "<run>", args })` reutiliza los
     agentes ya terminados.
   El workflow orquesta: investigador (encuadre ligero: pista → tema final,
   paleta, sesión; candidatas con evidencia e `impacto`) → verificador (todas
   las candidatas) → guionista (puntúa, elige UNA, un tuit; con reparación) →
   productor (QA visual, ensamblado, coherencia reducida, memoria). Si lanza
   un error de gate, muéstralo tal cual: dice qué candidata, campo o gate
   falló y por qué.
4. POST-WORKFLOW: verifica que exista la carpeta `ruta` (relativa:
   `datos/<fecha>-<slug>/`, o `sesiones/<slug>/salida/` en smoke/fixture) con
   los seis archivos `dato.png`, `tarjeta.html`, `dato.html`, `post.md`,
   `datos.json` y `dato.json`. En smoke/fixture comprueba que `memoria/datos.json`
   NO cambió (ni `memoria/hilos.json`, ni `memoria/fuentes.json`). Corre
   `make validate` (exit 0) y `make costo` (tokens, herramientas y tiempo por
   agente de esta corrida) y resume su tabla al usuario; señala si algún agente
   quedó `failed` o superó 150 K de contexto.
5. Muestra al usuario: si el estado quedó `incompleto`, dilo PRIMERO y explica
   qué gate falló. Luego: la pista y el tema final que eligió el investigador
   (`pista` → `tema`; di si se desvió), el dato (`dato`, una línea), la cifra
   con su unidad, periodo y fuente (`cifra_id`, `valor`), por qué impacta
   (`por_que_impacta`), el gancho (`hook_tipo`), la paleta y la plantilla; las
   candidatas descartadas con puntaje y motivo (`candidatas`); el texto del
   tuit con su peso X (`peso_texto`) y el alt-text; `no_afirma`; los avisos del
   productor (y si la tarjeta quedó `dudoso`); los avisos del propio workflow
   (`avisos_workflow`: reparaciones, presupuestos excedidos, pista → tema,
   hook_evitar) y las cifras con segunda fuente no independiente
   (`independencia_baja`, sobre todo si incluye la elegida); y las rutas de
   `dato.html` (para abrir en el navegador), `dato.png` y `post.md`.

Reglas: ninguna cifra `no_confirmada` aparece como hecho; la tarjeta no lleva
URLs ni emoji; el dato no se marca `listo` si la coherencia falla; el texto del
tuit no repite la cifra de la tarjeta (dato héroe); `sesiones/<slug>/` se
conserva como memoria de trabajo (`make limpiar SESION=sesiones/<slug>`). Los
agentes `hilo-*` se reutilizan tal cual: no crees agentes nuevos para /dato.
