---
description: "Informe de investigación en PDF (Letter, 14–30 páginas) + hilo de X cuyas tarjetas son figuras del informe, sobre UN tema de Guatemala — Workflow multi-agente con un redactor propio (uso — /investigacion <tema|idea:<id>|desde:<slug>> [smoke|fixture]; sin tema toma la mejor idea pendiente de ideas/banco.json; desde:<slug> escribe solo el informe sobre un hilo ya entregado; entregable en investigacion/<fecha>-<slug>/ con informe.json, salida/informe.pdf y hilo/)"
---

Produce una **investigación**: un informe de datos en PDF y el hilo de X que lo acompaña. Sigue
`referencias/flujo-investigacion.md`. El flujo es `/hilo` más dos fases (el redactor escribe el
informe; el productor cierra con el PDF y el registro) y entrega todo en `investigacion/<fecha>-<slug>/`.

## Interpretación de `$ARGUMENTS`

- `desde:<slug>` → **informe sobre un hilo ya entregado** (no se investiga ni se re-entrega el hilo).
  Puede combinarse con `smoke` (informe corto en staging, sin memoria); con `fixture` es error.
- `idea:<id>` → parte de esa idea del banco. `smoke` / `fixture` (en cualquier posición) activan ese
  modo. El resto es el tema libre. Sin nada → `python3 scripts/ideas.py --siguiente` (como `/hilo`).

## 1. Preflight (sin lanzar el workflow)

1. `make doctor` → exit 0 y sin errores. Debe listar `.claude/agents/informe-redactor.md`,
   `.claude/workflows/investigacion.js` y `.claude/commands/investigacion.md`; si falta el agente,
   DETENTE: hay que crearlo y **reiniciar Claude Code** (los agentes se registran al arrancar).
2. Salvo en `fixture` y `desde`: una búsqueda web de prueba (WebSearch «INE Guatemala»); si falla, DETENTE.
3. `fecha="$(date +%F)"`.
4. **Número del informe**: `python3 scripts/memoria.py --informes` → toma la última línea
   «siguiente N.º NN» → `numero = "NN"`. Si el tema ya tiene un informe listado, avísalo (no abortes).
5. Dedup: `grep -i` del tema en `memoria/hilos.json` (avisa si hay un hilo parecido; el editor declara
   ángulo nuevo).
6. Banco de ideas (no en `desde` ni `fixture`): `idea:<id>` → `python3 scripts/ideas.py --ver <id>`
   (exit 1 = DETENTE); sin tema → `python3 scripts/ideas.py --siguiente` (si no hay ideas pendientes,
   DETENTE y dilo); tema libre → `python3 scripts/ideas.py --buscar "<tema>"` y, si hay coincidencia
   FUERTE, pasa esa idea.
7. **`desde:<slug>`**: comprueba `sesiones/<slug>/guion.json` (si no existe, DETENTE: `sesiones/` no
   va en git) y busca en `memoria/hilos.json` el registro cuyo `slug` es ese → `desde_hilo = ruta`
   (debe existir con `hilo.json`; si no, DETENTE). Si `--informes` ya lista un informe con ese
   `hilo_id`, avisa («se creará el N.º NN nuevo»).
8. Avisa de la duración: normal ~45–70 min (12–16 agentes), `desde` ~15–25, `smoke` ~20, `fixture` ~10.

## 2. Invocación

```
Workflow({ name: "investigacion", args: { tema, idea, desde, desde_hilo, numero, smoke, fixture, fecha } })
```
(`tema` null en `desde`; `idea` null si no hay; `smoke`/`fixture` booleanos.) Si editaste
`investigacion.js` en esta sesión, usa `scriptPath: ".claude/workflows/investigacion.js"`. Si el
workflow falla con «agente no registrado», pide reiniciar Claude Code; `permitir_fallback: true` solo
con autorización expresa del usuario (corre ese rol en general-purpose). Para reanudar una corrida
interrumpida: `Workflow({ scriptPath, resumeFromRunId: "wf_…", args })` con los mismos args. Los
errores de gate se muestran tal cual (son accionables).

## 3. Post-checks

1. `ruta` existe y tiene `informe.json`, `salida/informe.pdf`, `salida/informe.html` y `salida/figuras/`.
   Si no es `desde`: `hilo/` con `hilo.html`, `post.md`, `datos.json`, `hilo.json`, `contacto.png` y
   `n_png` PNG. En `smoke`/`fixture`: nada nuevo en `investigacion/` y `git diff --stat memoria/` vacío.
2. Normal: `python3 scripts/memoria.py --informes` lista el nuevo con su N.º; si hubo idea,
   `python3 scripts/ideas.py --ver <id>` dice `hecha` (si no, `python3 scripts/ideas.py --conciliar`).
3. `make validate` → exit 0.
4. `make costo` → tokens y tiempo por agente; señala agentes `failed` o con más de 150 K de contexto
   (el redactor es el más caro después de los investigadores; si pasa de 150 K, hay que bajar
   `--max-bytes` del digesto o el rango de páginas).

## 4. Reporte al usuario

- Si `estado` es `incompleto`, eso va primero, con los avisos del productor y del redactor.
- Informe: N.º, fecha, tesis, páginas / figuras / tablas, capítulos (`capitulos[]` con sus páginas y
  figuras), `marcadores` pendientes (`[FECHA]`, `[ENLACE AL HILO]`) y la ruta del PDF.
- Hilo: gancho (`hook_tipo`) y paleta; cada tuit con su texto, `[📸 tuit_N.png]` y alt; el cierre con
  `[ENLACE AL INFORME]` resaltado: «sustitúyelo por la URL del PDF al publicar».
- `no_afirma`, `independencia_baja`, `avisos_workflow`, `visuales_dudosos`.
- Rutas: `salida/informe.pdf`, `hilo/hilo.html`, `hilo/contacto.png`, `hilo/post.md` (o, en `desde`,
  la ruta del hilo previo).

Reglas: el agente nunca publica en X; `memoria/` la escribe solo `memoria.py` desde el productor en el
Cierre (hilo en `hilos.json`, informe en `informes.json`); el hilo y el informe comparten `datos.json`
(ninguna cifra del informe sale de otra parte); los agentes `hilo-*` e `informe-redactor` declaran
`tools:` y no heredan los MCP.
