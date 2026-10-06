# Hilos · @DerekUrizar

Framework en español para producir **hilos de X con datos de Guatemala**: a
partir de UN tema, agentes orquestados investigan, verifican, escriben el guion
y generan una tarjeta 1080×1080 por tuit (HTML → PNG). La publicación es manual;
el entregable queda en `hilos/YYYY-MM-DD-<slug>/` con `hilo.html` (vista previa
con imagen + texto opcional + alt-text), `contacto.png`, `post.md`, `datos.json`
y los PNG. Un segundo flujo, `/ideas`, llena un **banco de ideas** (`ideas/`)
del que `/hilo` toma temas; al entregar un hilo, su idea queda `hecha`. Un
tercer flujo, `/dato [pista]`, produce **un solo dato impactante** en una
tarjeta 1080×1080 con el texto del tuit y su alt-text (sin hilo, sin banco de
ideas), entregado en `datos/YYYY-MM-DD-<slug>/` y registrado en `memoria/datos.json`.

## Mapa del proyecto

- `.claude/commands/hilo.md` — `/hilo [tema|idea:<id>] [smoke|fixture]`: preflight (`make doctor`, idea del banco; sin tema → `ideas.py --siguiente`) → Workflow `hilo` → post-checks (`make validate`, `make costo`)
- `.claude/commands/ideas.md` · `.claude/workflows/ideas.js` · `.claude/agents/ideas-explorador.md` (sonnet) — `/ideas [n] [enfoque]`: exploradores en paralelo → `ideas.py --importar`; guía `referencias/roles/explorador.md`
- `.claude/commands/dato.md` · `.claude/workflows/dato.js` — `/dato [pista] [smoke|fixture]`: un dato impactante en UNA tarjeta; reutiliza 4 agentes `hilo-*` (investigador con encuadre ligero → verificador → guionista que puntúa candidatas → productor con QA visual); guía `referencias/flujo-dato.md`
- `.claude/workflows/hilo.js` — orquestación con schemas, presupuestos y gates en código; bucles de reparación; fail-fast si los agentes no están registrados
- `.claude/agents/hilo-*.md` — los seis roles (opus: editor, investigador, guionista, productor; sonnet: verificador, visualista); cada uno apunta solo a su guía
- `referencias/flujo-hilo.md` (índice) · `flujo-dato.md` (índice de /dato) · `contrato-sesion.md` (incluye «Sesión dato») · `narrativa.md` (arco, ganchos `hook_tipo`, dato héroe, dato único) · `roles/<rol>.md` (con sección «Modo dato» en investigador, verificador, guionista y productor)
- `referencias/diseno/sistema.md` (anatomía, paletas, checks R1–R6) · `diseno/graficos.md` (pregunta→gráfico, contrato `DATA`, flujo del visualista, checklist QA) · `diseno/brief/` (brief original)
- `design/tokens.json` (paletas) · `design/fonts/` (woff2 locales) · `design/mapa_geometria.svg` (22 departamentos)
- `templates/base.html` (anatomía + helpers `H.*`) · `templates/graficos/*.html` (18 plantillas con `DATA` de ejemplo) · `templates/.pruebas/` · `templates/hilo.html` · `templates/dato.html` (vista previa de un dato)
- `scripts/` — `render.js` (HTML→PNG + checks), `nuevo_visual.py`, `materializar.py` (guion → tarjetas), `ensamblar.py` (sesión → carpeta + gate G1–G8; modo dato por `guion.tipo`, nunca escribe un dato en `hilos/`), `digesto.py` (resumen de sesión para agentes), `fuentes.py` (catálogo filtrado), `contar_x.py/.js` (peso X), `contacto.js` (hoja de contacto), `tabla.py` (agregar CSV), `fetch_tabla.py` / `fetch_pdf.sh` / `fetch_api.py` (descargas con caché), `memoria.py` (registro: hilos o datos según `guion.tipo`, series y fuentes halladas; marca la idea `hecha`; `--datos` lista los datos publicados), `ideas.py` (banco de ideas: importar, siguiente, ver, buscar, marcar, conciliar), `costo.py` (tokens por corrida), `test.sh`, `doctor.sh`, `validate.py`, `build_mapa.py`
- `memoria/fuentes.json` (fuentes con notas de acceso + `series[]`) · `memoria/hilos.json` (registro de hilos) · `memoria/datos.json` (registro de datos de /dato); ambos registros los escribe `memoria.py`
- `ideas/banco.json` (banco de ideas; lo escribe `ideas.py`) · `ideas/README.md` (índice generado)
- `sesiones/<slug>/` (memoria de trabajo; `_ideas/` propuestas de los exploradores; `_fixture/` sesión de prueba de hilo; `_fixture_dato/` sesión de prueba de /dato; `_descargas/` caché con `indice.json`) · `hilos/` (entregables de /hilo) · `datos/` (entregables de /dato)

## Reglas de oro

1. **Ninguna cifra `no_confirmada` aparece en el hilo.** Solo `verificada|ajustada`, y manda `valor_final`. Cada cifra lleva evidencia (url + cita + archivo local); el verificador parte de ella y busca UNA segunda fuente. No inventar, extrapolar ni redondear lo que la fuente no redondea.
2. **Los agentes no leen JSON de sesión enteros ni código**: usan `scripts/digesto.py`, `scripts/fuentes.py` y los límites que llegan en su directiva. Presupuestos por rol (búsquedas, fetch, cifras, lecturas de PNG) en `referencias/roles/`.
3. **`guion.json` es la fuente de verdad de las tarjetas.** Los visuales se regeneran con `scripts/materializar.py`; nadie edita `tuit_N.html` a mano. Los visualistas escriben solo `tuit_N.ajuste.json`; consolida el productor, único escritor de `guion.json` desde entonces.
4. **Cero dependencias externas en las tarjetas** (ni `https://` ni emoji). Fuentes tipográficas desde `design/fonts/`. El pie lleva siempre «Fuente: …» y el handle. **Sin Playwright MCP** (descargas con `make tabla`/`make pdf`/`fetch_api.py`, cacheadas).
5. **Una paleta por hilo** (o por dato), elegida por tema en el encuadre. T1 siempre con texto (40–280 de peso X, sin enlaces, gancho `hook_tipo`); los demás pueden ir sin texto; con imagen ≤ 200; el texto nunca repite la tarjeta (dato héroe).
6. Los gates viven en código (`hilo.js`, `ensamblar.py --check` G1–G8, `render.js --check` R1–R6). Un hilo que no pasa C1–C8 se entrega marcado `incompleto`, nunca como `listo`.
7. El agente nunca publica en X. `memoria/` la escribe solo `scripts/memoria.py` desde el productor (`hilos.json` en /hilo, `datos.json` en /dato, según `guion.tipo`; nunca en smoke/fixture); `ideas/` la escribe solo `scripts/ideas.py` (también vía `memoria.py`, que marca `hecha` la idea del `idea_id` del encuadre; `/dato` no toca `ideas/`).
8. Al terminar cualquier corrida: `make validate` sale 0; `make costo` mide la corrida.

## Comandos

| Comando | Qué hace |
|---|---|
| `/hilo [tema] [smoke\|fixture]` | Produce un hilo completo (Workflow multi-agente). `smoke` = corta con web; `fixture` = sin web, solo guion → visuales → productor |
| `/ideas [n] [enfoque]` | Busca temas con datos descargables y los añade a `ideas/banco.json` (1–3 exploradores sonnet, ~5–10 min) |
| `/dato [pista] [smoke\|fixture]` | Un dato impactante en UNA tarjeta 1080×1080 con texto y alt-text (4 agentes `hilo-*`, ~8–15 min). La pista (tema, ángulo, fuente o corazonada) es opcional: sin ella el investigador elige un dato de actualidad. `smoke` = corta con web; `fixture` = sin web, solo productor sobre `sesiones/_fixture_dato` |
| `make test [RAPIDO=1]` | Pruebas: validate, catálogo, fixture, negativos de gate, vectores de peso X, sintaxis de `hilo.js` |
| `make doctor` | Comprueba node, Playwright, python, fuentes, agentes y workflow |
| `make costo [RUN=wf_xxx]` | Tokens, herramientas y tiempo por agente de una corrida |
| `make catalogo [PALETAS=todas]` | Ensambla y renderiza todas las plantillas + pruebas de estrés |
| `python3 scripts/materializar.py sesiones/<slug> [--tuit N] [--consolidar]` | Guion → tarjetas |
| `python3 scripts/ensamblar.py sesiones/<slug> --check` | Sesión → carpeta de entrega + gate G1–G8 + `contacto.png` |
| `make digesto SESION= [PARA=]` · `make fuentes TEMA=` | Insumos compactos para agentes |
| `make ideas` · `python3 scripts/ideas.py --siguiente\|--ver ID\|--marcar ID --estado E [--hilo H]\|--conciliar` | Banco de ideas |
| `python3 scripts/memoria.py --datos ["tema"]` | Datos ya publicados por /dato (el más reciente primero; con tema, filtrados) |
| `make validate` · `make limpiar [SESION=]` · `make contacto DIR=` | Utilidades |
| `make tabla URL=` · `make pdf URL=` · `python3 scripts/tabla.py` | Descargas oficiales cacheadas y agregación de CSV |

Prueba sin agentes: `python3 scripts/materializar.py sesiones/_fixture && python3 scripts/ensamblar.py sesiones/_fixture --check` → abre `sesiones/_fixture/salida/hilo.html`. Para `/dato`: `python3 scripts/materializar.py sesiones/_fixture_dato && python3 scripts/ensamblar.py sesiones/_fixture_dato --check` → abre `sesiones/_fixture_dato/salida/dato.html`.

## Convenciones

- Todo en español; nombres de archivo en minúsculas sin tildes. Scripts Python stdlib puro con `argparse`, `--help`; exit 0 ok · 1 fallo · 2 uso incorrecto.
- Las cifras en `visual.datos` van crudas y en la unidad de la fuente; el formato lo pone `datos.formato`.
- Slug: minúsculas, sin tildes, guiones, sin fecha; la carpeta de entrega antepone la fecha (`hilos/` para hilos, `datos/` para datos); las rutas en retornos y memoria son relativas a la raíz.
- Los agentes personalizados se registran al arrancar Claude Code: tras crear o editar `.claude/agents/` o `.claude/workflows/`, reiniciar (o usar `scriptPath`).
