---
description: Hilo de X con datos de Guatemala sobre UN tema — investigación multi-agente, tarjetas 1080×1080 y vista previa hilo.html (uso — /hilo [tema|idea:<id>] [smoke|fixture]; sin tema toma la mejor idea pendiente de ideas/banco.json)
---

Eres el coordinador del flujo **/hilo** de @DerekUrizar. El usuario quiere un
hilo de X que cuente una historia con datos sobre: "$ARGUMENTS" (puede venir
vacío). Si contiene `smoke` es una corrida corta con web (1 eje, 3 tuits); si
contiene `fixture` es una prueba SIN web que copia `sesiones/_fixture` y solo
ejercita guion → visuales → productor. La guía vive en `referencias/flujo-hilo.md`.

1. PREFLIGHT: corre `make doctor` (node, Playwright, fuentes, agentes; exit 0).
   Salvo en `fixture`, haz una búsqueda de prueba con WebSearch; si falla →
   DETENTE y repórtalo. Obtén la fecha con `date +%F`. Lee `memoria/hilos.json`:
   si ya hay un hilo con tema parecido, díselo al usuario (el editor tendrá que
   declarar un ángulo nuevo; no abortes).
   **Banco de ideas** (`ideas/banco.json`; nunca lo edites: solo `scripts/ideas.py`).
   Salvo en `fixture`, resuelve `idea` así:
   - Si los argumentos traen `idea:<id>` → `python3 scripts/ideas.py --ver <id>`
     (exit 1 = no existe: DETENTE y dilo); `idea = <id>` y `tema = titulo` de la idea.
   - Sin tema (y sin smoke) → `python3 scripts/ideas.py --siguiente`: si devuelve una idea, díselo
     al usuario («tomo la idea <id>: <titulo>, puntaje N») y úsala igual que arriba;
     si sale 1 (banco vacío), sin idea: el editor elige un tema de actualidad.
   - Con tema libre → `python3 scripts/ideas.py --buscar "<tema>"`: si hay una
     coincidencia `FUERTE`, avisa al usuario y pasa su `idea` (el tema se queda
     como lo escribió); si solo hay débiles, sin idea.
2. Avisa al usuario: una corrida normal tarda ~25–40 minutos con 8–12 agentes;
   smoke ~10–15 minutos; fixture ~5 minutos. La publicación en X es manual.
3. Invoca la herramienta **Workflow** con `name: "hilo"` y `args` como OBJETO:
   `{ "tema": "<tema sin smoke/fixture>", "smoke": <bool>, "fixture": <bool>, "fecha": "<YYYY-MM-DD>", "idea": "<id>"|null }`.
   - Si `.claude/workflows/hilo.js` se editó en ESTA sesión, `name` resuelve una
     copia en caché: usa `scriptPath: ".claude/workflows/hilo.js"`.
   - Si el workflow falla con «no está registrado en esta sesión», los agentes
     `.claude/agents/hilo-*.md` se crearon o cambiaron en esta sesión: pide al
     usuario reiniciar Claude Code y relanzar. Solo si lo autoriza, relanza con
     `"permitir_fallback": true` (corre todo con general-purpose: más caro).
   - Para reanudar tras un fallo o una edición del script:
     `Workflow({ scriptPath, resumeFromRunId: "<run>", args })` reutiliza los
     agentes ya terminados.
   El workflow orquesta: editor → investigador y verificador por eje (pipeline)
   → guionista (con reparación) → visualistas en lotes (con reparación) →
   productor. Si lanza un error de gate, muéstralo tal cual: dice qué tuit o
   cifra falló y por qué.
4. POST-WORKFLOW: verifica que exista la carpeta `ruta` (relativa:
   `hilos/<fecha>-<slug>/`, o `sesiones/<slug>/salida/` en smoke/fixture) con
   `hilo.html`, `post.md`, `datos.json`, `hilo.json`, `contacto.png` y tantos
   `tuit_N.png` como `n_png`. En smoke/fixture comprueba que `memoria/hilos.json`
   NO cambió (ni `ideas/banco.json`). Si hubo idea y no es smoke, comprueba con
   `python3 scripts/ideas.py --ver <id>` que quedó `hecha` (o `en_curso` si el
   hilo quedó incompleto) con su `hilo_id`; si no, corre
   `python3 scripts/ideas.py --conciliar` y dilo. Corre `make validate` (exit 0) y `make costo` (tokens, herramientas
   y tiempo por agente de esta corrida) y resume su tabla al usuario; señala si
   algún agente quedó `failed` o superó 150 K de contexto.
5. Muestra al usuario: la tesis, el gancho (`hook_tipo`) y la paleta; cada tuit
   con su texto (o «sin texto: la imagen lo dice»), el marcador `[📸 tuit_N.png]`
   y el alt-text; `no_afirma`; los avisos del productor; y las rutas de
   `hilo.html` (para abrir en el navegador), `contacto.png` y `post.md`. Si el
   estado quedó `incompleto`, dilo primero y explica qué gate falló.

Reglas: las cifras `no_confirmada` nunca aparecen como hechos; ninguna tarjeta
lleva URLs ni emoji; el hilo no se marca `listo` si el gate de coherencia falla;
`sesiones/<slug>/` se conserva como memoria de trabajo (`make limpiar
SESION=sesiones/<slug>` para borrarla). Coste de arranque: los agentes
`hilo-*` declaran `tools:` y NO heredan los MCP de la sesión; su contexto base
medido es de 13–16 K tokens (columna `cache_cr` de `make costo`, corrida
wf_f01bd5ac-4d5), así que no hace falta abrir la sesión con un MCP mínimo. El
coste lo dominan los investigadores (búsquedas y fetch), no el arranque.
