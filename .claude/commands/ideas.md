---
description: Banco de ideas para hilos — exploradores (sonnet) buscan temas de Guatemala con datos descargables y los añaden a ideas/banco.json (uso — /ideas [n] [enfoque])
---

Eres el coordinador del flujo **/ideas** de @DerekUrizar. El usuario quiere ideas
nuevas para hilos de datos: "$ARGUMENTS" (puede venir vacío). Un número al
inicio es `n` (ideas en total, 3–15; por defecto 9); el resto es el `enfoque`
(vacío y n ≥ 9 = tres exploradores: economía/fiscal · seguridad/población ·
salud/educación/clima-agro/energía; con enfoque o n < 9, uno solo). El banco vive en `ideas/banco.json` y lo
escribe SOLO `scripts/ideas.py`; `ideas/README.md` es su índice legible.

1. PREFLIGHT: `make doctor` (exit 0) y una búsqueda de prueba con WebSearch (si
   falla → DETENTE y repórtalo). `date +%F` → fecha; `date +%F-%H%M%S` → sufijo
   de la carpeta `dir = sesiones/_ideas/<fecha-hora>`.
   `python3 scripts/ideas.py --conciliar` (marca hechas las ideas enlazadas a
   hilos ya registrados; si lista «posible», díselo al usuario sin marcar nada).
   `python3 scripts/ideas.py --resumen` → arma `excluir` con los títulos de las
   ideas del banco (cualquier estado) y los temas de los hilos producidos
   (recortados a ~80 caracteres).
2. Avisa: ~5–10 minutos, 1–3 agentes sonnet.
3. Invoca **Workflow** con `name: "ideas"` y `args` como OBJETO:
   `{ "fecha": "<YYYY-MM-DD>", "dir": "<dir>", "n": <n>, "enfoque": "<texto>"|"", "excluir": ["…"] }`.
   - Si `.claude/workflows/ideas.js` se editó en ESTA sesión, usa
     `scriptPath: ".claude/workflows/ideas.js"`.
   - Si falla con «no está registrado en esta sesión», el agente
     `.claude/agents/ideas-explorador.md` es nuevo: pide reiniciar Claude Code.
     Solo si el usuario lo autoriza, relanza con `"permitir_fallback": true`.
4. POST-WORKFLOW: `python3 scripts/ideas.py --importar <dir> --fecha <fecha>`
   (valida, deduplica contra el banco y contra `memoria/hilos.json`, escribe el
   banco y regenera `ideas/README.md`). Luego `make validate` (exit 0) y
   `make costo`; resume su tabla.
5. Muestra al usuario las ideas **añadidas** (las líneas `+` del importador)
   ordenadas por puntaje: id, título, por qué ahora, fuentes; cuántas se
   descartaron por repetidas o sin evidencia; y cómo producir una:
   `/hilo idea:<id>` (o `/hilo` sin tema, que toma la de mayor puntaje).

Reglas: nunca edites `ideas/banco.json` ni `ideas/README.md` a mano; para
descartar una idea: `python3 scripts/ideas.py --marcar <id> --estado descartada`.
Las ideas no son cifras: nada de lo que digan llega a un hilo sin pasar por
investigador y verificador en `/hilo`.
