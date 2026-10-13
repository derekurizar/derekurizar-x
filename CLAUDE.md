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
`/dato` tiene **modos** (`/dato vs|mapa|antes [pista]`, con alias `/vs`, `/mapa`, `/antes`):
mismos agentes y entregable, distinto género (Guatemala frente a otros países · brecha por
departamento · hace N años frente a hoy); el modo viaja en `guion.modo` y `tipo` sigue siendo `dato`.
`/hilo` tiene los suyos (`/hilo explica|perfil`, alias `/explica`, `/perfil`): el tema explicado con
sus números sin giro, y el retrato de un departamento o grupo frente al país. `/fecha` produce la
pieza que toca según el calendario editorial (`ideas/calendario.json`). Un quinto flujo, **`/investigacion
<tema|idea:<id>|desde:<slug>>`**, produce un **informe de investigación** (documento Letter → PDF de 14–30 páginas
con el mismo sistema visual) **y el hilo que lo acompaña** (sus tarjetas son figuras del informe): `investigacion/`
guarda las plantillas del documento, `scripts/informe.py` arma el PDF desde un `informe.json` cuyas cifras se
cruzan con `datos.json`, y el entregable queda en `investigacion/YYYY-MM-DD-<slug>/` (`informe.json`, `salida/`,
`hilo/`), registrado en `memoria/informes.json`.

## Mapa del proyecto

- `.claude/commands/hilo.md` — `/hilo [explica|perfil] [tema|idea:<id>] [smoke|fixture]`: preflight (`make doctor`, idea del banco; sin tema → `ideas.py --siguiente`) → Workflow `hilo` → post-checks (`make validate`, `make costo`); tabla `MODOS` en `hilo.js` (explica: 3–6 tuits sin giro con beat `paso`; perfil: 5–8 sin giro con beat `dimension` y comparación con el país) y espejo en `ensamblar.py`
- `.claude/commands/explica.md` · `perfil.md` — alias de `/hilo` con el modo fijado (delegan en `hilo.md`; no consultan el banco de ideas)
- `.claude/commands/ideas.md` · `.claude/workflows/ideas.js` · `.claude/agents/ideas-explorador.md` (sonnet) — `/ideas [n] [enfoque]`: exploradores en paralelo → `ideas.py --importar`; guía `referencias/roles/explorador.md`
- `.claude/commands/dato.md` · `.claude/workflows/dato.js` — `/dato [vs|mapa|antes] [pista] [smoke|fixture]`: un dato impactante en UNA tarjeta; reutiliza 4 agentes `hilo-*` (investigador con encuadre ligero → verificador → guionista que puntúa candidatas → productor con QA visual); tabla `MODOS` (gancho, plantillas y gates por modo) con espejo mínimo en `ensamblar.py`; guía `referencias/flujo-dato.md`
- `.claude/commands/vs.md` · `mapa.md` · `antes.md` — alias de `/dato` con el modo fijado (8 líneas cada uno; delegan en `dato.md`)
- `.claude/commands/investigacion.md` · `.claude/workflows/investigacion.js` · `.claude/agents/informe-redactor.md` (opus) — `/investigacion <tema|idea:<id>|desde:<slug>> [smoke|fixture]`: preflight (`make doctor`, `memoria.py --informes` da el N.º, banco de ideas) → Workflow `investigacion` (Encuadre con plan de capítulos → Investigación ⇢ Verificación → Guion 6–12 tuits con bloque `investigacion` y cierre `[ENLACE AL INFORME]` → Visuales → Producción del hilo en `investigacion/<fecha>-<slug>/hilo` → Informe (redactor: `informe.json` + `informe.py --check --png`, I1–I7/P1–P5) → Cierre (PDF al entregable, `memoria.py --informe`, validate)) → post-checks; `desde:<slug>` salta a Relectura → Informe → Cierre sobre un hilo ya entregado; `investigacion` es un **modo** de tipo `hilo` (tabla `MODOS` propia, W5 por unión con `hilo.js`); guías `referencias/flujo-investigacion.md`, `referencias/roles/redactor.md` (estructura canónica, presupuestos de página medidos, bucle de QA) y «Modo investigación» en los demás roles
- `.claude/commands/fecha.md` · `scripts/calendario.py` · `ideas/calendario.json` — `/fecha [hoy|fecha|id|texto] [smoke|fixture]`: calendario editorial (efemérides, días internacionales, publicaciones de fuentes; fechas `MM-DD` anuales, `DD` mensuales, `YYYY-MM-DD` puntuales) que despacha a `/dato` (con su modo) o `/hilo` y marca la entrada `hecha`; `/fecha buscar [mes]` lanza un `ideas-explorador` («Modo calendario» en `referencias/roles/explorador.md`) y `calendario.py --importar`
- `.claude/workflows/hilo.js` — orquestación con schemas, presupuestos y gates en código; bucles de reparación; fail-fast si los agentes no están registrados
- `.claude/agents/hilo-*.md` — los seis roles (opus: editor, investigador, guionista, productor; sonnet: verificador, visualista); cada uno apunta solo a su guía
- `referencias/flujo-hilo.md` (índice) · `flujo-dato.md` (índice de /dato) · `contrato-sesion.md` (incluye «Sesión dato») · `narrativa.md` (arco, ganchos `hook_tipo`, dato héroe, dato único) · `roles/<rol>.md` (con sección «Modo dato» en investigador, verificador, guionista y productor)
- `referencias/diseno/sistema.md` (anatomía, paletas, checks R1–R6) · `diseno/graficos.md` (pregunta→gráfico, contrato `DATA`, flujo del visualista, checklist QA) · `diseno/brief/` (brief original)
- `investigacion/` — informes: `base.html` (hoja Letter, `@page apaisada`), `paginas/*.js` (`PAGINAS.<tipo>`: portada, indice, resumen, tablero, capitulo banda|dividida|destacado, cuerpo, apaisada, cronologia, conclusiones, metodo, glosario, anexo, tarjetas (con `desde_hilo` se llena sola desde `hilo.json`), contraportada), `graficos/*.js` (`G.<tipo>` dibujados en el documento con el **mismo contrato `datos` que la tarjeta** (`graficos.md`), nombre kebab o snake; más `chispa`, `cuadros`, `comparacion`, `columnas`), `ejemplos/dengue-2026/` (`informe.json` + `salida/informe.pdf`), `ejemplos/catalogo/` (generado por `scripts/catalogo_informe.py`: todos los `G.*` en papel, panel y media página), `YYYY-MM-DD-<slug>/` (entregables de `/investigacion`); contrato en `referencias/diseno/informe.md`
- `design/tokens.json` (paletas; `papel_tinta`/`papel_barra` y bloque `documento` para informes) · `design/fonts/` (woff2 locales) · `design/mapa_geometria.svg` (22 departamentos)
- `templates/base.html` (anatomía + helpers `H.*`) · `templates/graficos/*.html` (26 plantillas con `DATA` de ejemplo) · `templates/.pruebas/` · `templates/hilo.html` · `templates/dato.html` (vista previa de un dato)
- `scripts/` — `render.js` (HTML→PNG + checks), `nuevo_visual.py`, `materializar.py` (guion → tarjetas), `ensamblar.py` (sesión → carpeta + gate G1–G8; modo dato por `guion.tipo`, nunca escribe un dato en `hilos/`), `digesto.py` (resumen de sesión para agentes; `--para redactor [--hilo DIR]` da series completas, guion y síntesis), `fuentes.py` (catálogo filtrado), `contar_x.py/.js` (peso X), `contacto.js` (hoja de contacto), `tabla.py` (agregar CSV), `fetch_tabla.py` / `fetch_pdf.sh` / `fetch_api.py` (descargas con caché), `memoria.py` (registro: hilos o datos según `guion.tipo`, series y fuentes halladas; marca la idea `hecha`; `--datos` lista los datos publicados; `--informe DIR` registra el informe en `memoria/informes.json` (`--solo-informe` en `desde:`); `--informes` lista y da el siguiente N.º), `ideas.py` (banco de ideas: importar, siguiente, ver, buscar, marcar, conciliar), `costo.py` (tokens por corrida), `calendario.py` (calendario editorial: próximas, día, buscar, importar, marcar), `check_workflows.py` (W1–W8: constantes y modos alineados entre `hilo.js`, `dato.js`, `ideas.js`, `investigacion.js`, tokens, plantillas y `ensamblar.py`; `TIPOS_PAGINA` y `MARCADOR_INFORME`; `G.*` del informe frente al catálogo de tarjetas y sin helpers del DOM de la tarjeta), `informe.py` (informe.json → informe.html + PDF; gates I1–I7 (I2 coteja cada número de los gráficos con `ensamblar.CLAVES_DATO`; I7 avisa de números del cuerpo sin respaldo), numeración, índice, figuras tarjeta con las plantillas, `desde_hilo`), `catalogo_informe.py` (catálogo de gráficos del informe), `render_informe.js` (PDF Letter + checks P1–P5), `fuentes_ruta.js` (ruta de fuentes y bloqueo de externas, común a los dos render), `test.sh`, `doctor.sh`, `validate.py`, `build_mapa.py`
- `memoria/fuentes.json` (fuentes con notas de acceso + `series[]`) · `memoria/hilos.json` (registro de hilos) · `memoria/datos.json` (registro de datos de /dato) · `memoria/informes.json` (registro de informes de /investigacion, con su N.º); los tres registros los escribe `memoria.py`
- `ideas/banco.json` (banco de ideas; lo escribe `ideas.py`) · `ideas/README.md` (índice generado) · `ideas/calendario.json` (calendario editorial; lo escribe solo `calendario.py`)
- `sesiones/<slug>/` (memoria de trabajo; `_ideas/` propuestas de los exploradores; `_fixture/` sesión de prueba de hilo (con `informe.json` de ejemplo para `make informe-fixture`); `_fixture_dato/` sesión de prueba de /dato; `_descargas/` caché con `indice.json`) · `hilos/` (entregables de /hilo) · `datos/` (entregables de /dato) · `investigacion/<fecha>-<slug>/` (entregables de /investigacion)

## Reglas de oro

1. **Ninguna cifra `no_confirmada` aparece en el hilo.** Solo `verificada|ajustada`, y manda `valor_final`. Cada cifra lleva evidencia (url + cita + archivo local); el verificador parte de ella y busca UNA segunda fuente. No inventar, extrapolar ni redondear lo que la fuente no redondea.
2. **Los agentes no leen JSON de sesión enteros ni código**: usan `scripts/digesto.py`, `scripts/fuentes.py` y los límites que llegan en su directiva. Presupuestos por rol (búsquedas, fetch, cifras, lecturas de PNG) en `referencias/roles/`.
3. **`guion.json` es la fuente de verdad de las tarjetas.** Los visuales se regeneran con `scripts/materializar.py`; nadie edita `tuit_N.html` a mano. Los visualistas escriben solo `tuit_N.ajuste.json`; consolida el productor, único escritor de `guion.json` desde entonces.
4. **Cero dependencias externas en las tarjetas** (ni `https://` ni emoji). Fuentes tipográficas desde `design/fonts/`. El pie lleva siempre «Fuente: …» y el handle. **Sin Playwright MCP** (descargas con `make tabla`/`make pdf`/`fetch_api.py`, cacheadas).
5. **Una paleta por hilo** (o por dato), elegida por tema en el encuadre. T1 siempre con texto (40–280 de peso X, sin enlaces, gancho `hook_tipo`); los demás pueden ir sin texto; con imagen ≤ 200; el texto nunca repite la tarjeta (dato héroe). Los **modos** no crean tipos nuevos: `guion.tipo` es `hilo` o `dato` y `guion.modo` (`MODOS` en `ensamblar.py`, tabla `MODOS` en cada workflow; `investigacion` es un modo de `hilo` que vive en `investigacion.js`) fuerza gancho, plantillas y gates; G1 rechaza tipos y modos desconocidos y `scripts/check_workflows.py` mantiene las constantes alineadas. En el informe, `grafico.tipo` y `datos` siguen el **mismo contrato que la tarjeta** y I2 coteja cada número con las cifras.
6. Los gates viven en código (`hilo.js`, `ensamblar.py --check` G1–G8, `render.js --check` R1–R6). Un hilo que no pasa C1–C8 se entrega marcado `incompleto`, nunca como `listo`.
7. El agente nunca publica en X. `memoria/` la escribe solo `scripts/memoria.py` desde el productor (`hilos.json` en /hilo, `datos.json` en /dato, según `guion.tipo`; `informes.json` con `--informe` en /investigacion; nunca en smoke/fixture); `ideas/banco.json` lo escribe solo `scripts/ideas.py` (también vía `memoria.py`, que marca `hecha` la idea del `idea_id` del encuadre; `/dato` no toca el banco) e `ideas/calendario.json` solo `scripts/calendario.py` (`/fecha` lo marca al cerrar).
8. Al terminar cualquier corrida: `make validate` sale 0; `make costo` mide la corrida.

## Comandos

| Comando | Qué hace |
|---|---|
| `/hilo [explica\|perfil] [tema] [smoke\|fixture]` | Produce un hilo completo (Workflow multi-agente). `smoke` = corta con web; `fixture` = sin web, solo guion → visuales → productor (hilo con giro) |
| `/explica <tema>` | El tema explicado con sus números en 3–6 tarjetas, sin giro ni tesis; cada tuit intermedio es un paso con cifra y texto (= `/hilo explica`) |
| `/perfil <departamento o grupo>` | Retrato del sujeto frente al país en 5–8 tarjetas sin giro; cada dimensión compara sujeto y país en la misma fuente y año (= `/hilo perfil`) |
| `/ideas [n] [enfoque]` | Busca temas con datos descargables y los añade a `ideas/banco.json` (1–3 exploradores sonnet, ~5–10 min) |
| `/dato [vs\|mapa\|antes] [pista] [smoke\|fixture]` | Un dato impactante en UNA tarjeta 1080×1080 con texto y alt-text (4 agentes `hilo-*`, ~8–15 min). La pista (tema, ángulo, fuente o corazonada) es opcional: sin ella el investigador elige un dato de actualidad. `smoke` = corta con web; `fixture` = sin web, solo productor sobre `sesiones/_fixture_dato` (dato simple) |
| `/vs [pista]` | Guatemala frente a otros países en una tarjeta: todos de la misma fuente, edición y periodo; Guatemala destacada; sin «ganamos/perdemos» (= `/dato vs`) |
| `/mapa [pista]` | Brecha por departamento: mapa de los 22 con extremos, tasa per cápita con denominador INE, gancho `brecha_territorial` (= `/dato mapa`) |
| `/antes [pista]` | Hace N años frente a hoy: misma serie y fuente a ≥5 años, gancho `antes_despues`, dinero corriente declarado (= `/dato antes`) |
| `/investigacion [tema\|idea:<id>\|desde:<slug>] [smoke\|fixture]` | Informe de investigación en PDF (14–30 páginas) + hilo de 6–12 tuits cuyas tarjetas son figuras del informe (Workflow de 7 fases con el agente `informe-redactor`, ~45–70 min). `desde:<slug>` escribe solo el informe sobre un hilo ya entregado; `smoke` = 1 eje y 8–12 páginas en staging; `fixture` = sin web sobre `sesiones/_fixture` |
| `/fecha [hoy\|fecha\|id\|texto]` | Pieza atada a una fecha del calendario editorial; sin argumento lista los próximos 30 días; `buscar [mes]` propone entradas nuevas con un explorador. Despacha a `/dato` o `/hilo` y marca la entrada `hecha` |
| `make informe DIR=<carpeta> [PAL=paleta]` · `make informe-ejemplo` · `make informe-fixture` · `make informe-catalogo` | Informe de investigación desde `informe.json`: gates I1–I7 (cifras con `id` contra `datos.json`), PDF Letter en `<carpeta>/salida/` y checks P1–P5; el ejemplo de dengue, el fixture de 8 páginas y el catálogo de gráficos del informe |
| `make test [RAPIDO=1]` | Pruebas: validate, catálogo, fixture, negativos de gate (incluidos tipo y modo), vectores de peso X, informe de ejemplo (PDF + negativos I1–I6, P1, P2), sintaxis de los workflows, `check_workflows.py` |
| `make doctor` | Comprueba node, Playwright, python, fuentes, agentes y workflow |
| `make costo [RUN=wf_xxx]` | Tokens, herramientas y tiempo por agente de una corrida |
| `make catalogo [PALETAS=todas]` | Ensambla y renderiza todas las plantillas + pruebas de estrés |
| `python3 scripts/materializar.py sesiones/<slug> [--tuit N] [--consolidar]` | Guion → tarjetas |
| `python3 scripts/ensamblar.py sesiones/<slug> --check` | Sesión → carpeta de entrega + gate G1–G8 + `contacto.png` |
| `make digesto SESION= [PARA=]` · `make fuentes TEMA=` | Insumos compactos para agentes |
| `make ideas` · `python3 scripts/ideas.py --siguiente\|--ver ID\|--marcar ID --estado E [--hilo H]\|--conciliar` | Banco de ideas |
| `make calendario [DIAS=30]` · `python3 scripts/calendario.py --proximas\|--dia F\|--ver ID\|--buscar T\|--importar DIR\|--marcar ID --estado E [--pieza R]` | Calendario editorial de `/fecha` |
| `python3 scripts/memoria.py --datos ["tema"]` · `--informes ["tema"]` | Datos ya publicados por /dato, o informes de /investigacion con el siguiente N.º (el más reciente primero; con tema, filtrados) |
| `make validate` · `make limpiar [SESION=]` · `make contacto DIR=` | Utilidades |
| `make tabla URL=` · `make pdf URL=` · `python3 scripts/tabla.py` | Descargas oficiales cacheadas y agregación de CSV |

Prueba sin agentes: `python3 scripts/materializar.py sesiones/_fixture && python3 scripts/ensamblar.py sesiones/_fixture --check` → abre `sesiones/_fixture/salida/hilo.html`. Para `/dato`: `python3 scripts/materializar.py sesiones/_fixture_dato && python3 scripts/ensamblar.py sesiones/_fixture_dato --check` → abre `sesiones/_fixture_dato/salida/dato.html`. Para el informe (tras el fixture de hilo): `make informe-fixture` → abre `sesiones/_fixture/informe/informe.pdf`.

## Convenciones

- Todo en español; nombres de archivo en minúsculas sin tildes. Scripts Python stdlib puro con `argparse`, `--help`; exit 0 ok · 1 fallo · 2 uso incorrecto.
- Las cifras en `visual.datos` van crudas y en la unidad de la fuente; el formato lo pone `datos.formato`.
- Slug: minúsculas, sin tildes, guiones, sin fecha; la carpeta de entrega antepone la fecha (`hilos/` para hilos, `datos/` para datos); las rutas en retornos y memoria son relativas a la raíz.
- Los agentes personalizados se registran al arrancar Claude Code: tras crear o editar `.claude/agents/` o `.claude/workflows/`, reiniciar (o usar `scriptPath`).
