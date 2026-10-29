# Flujo `/investigacion` — índice

Una investigación es **un informe de datos en PDF (Letter, 14–30 páginas) y el
hilo de X que lo acompaña**, sobre UN tema de Guatemala. Las tarjetas del hilo
son figuras del informe; el informe cuenta con detalle lo que el hilo resume.
El entregable queda en `investigacion/YYYY-MM-DD-<slug>/`:

```
investigacion/2026-10-13-<slug>/
  informe.json                        ← lo escribe el redactor (fuente de verdad del PDF)
  salida/informe.pdf · informe.html · figuras/ · fonts/
  hilo/hilo.html · post.md · tuit_1..N.png · datos.json · hilo.json · contacto.png
```

```
Encuadre (editor: ejes + plan de capítulos) → [Investigación → Verificación] por eje, en pipeline
→ Guion (guionista: 6–12 tuits, bloque investigacion, cierre con [ENLACE AL INFORME])
→ Visuales (visualistas en lotes de 3)
→ Producción (productor: ensamblar.py --check --salida investigacion/…/hilo + coherencia C1–C8, sin memoria)
→ Informe (redactor: informe.json → informe.py --check --png, I1–I7 + P1–P5, ≤ 3 vueltas)
→ Revisión (revisor: ¿de dónde sale cada número, barra y afirmación? V1–V8 → el redactor corrige; ≤ 2 vueltas)
→ Cierre (productor: informe.py al entregable, QA de ≤ 3 páginas, memoria.py --informe, make validate)

desde:<slug>   Relectura (editor: añade el plan de capítulos a la sesión) → Informe → Revisión → Cierre
```

Orquesta `.claude/workflows/investigacion.js` (invocado por
`/investigacion <tema|idea:<id>|desde:<slug>> [smoke|fixture]`). `investigacion`
es un **modo** de tipo `hilo` (`guion.tipo = "hilo"`, `guion.modo =
"investigacion"`): el hilo pasa por `ensamblar.py --check` como cualquier
otro, con tres gates propios (6–12 tuits, bloque `guion.investigacion{numero,
informe_dir, capitulos[]}`, marcador `[ENLACE AL INFORME]` solo en el cierre).
El informe pasa por `scripts/informe.py --check` (I1–I7) y
`scripts/render_informe.js --check` (P1–P5). Ninguna cifra `no_confirmada`
llega al hilo ni al informe: los dos comparten `datos.json`.

| | normal | smoke | fixture |
|---|---|---|---|
| ejes | 2–5 | 1 | 1 (los del fixture) |
| tuits | 6–12 | 4–6 | 3 |
| páginas (gate · objetivo) | 14–30 · 16–28 | 8–12 | 6–10 · 8 |
| figuras / tablas / capítulos mínimos | 6 / 1 / 2 | 3 / 0 / 1 | 2 / 0 / 1 |
| lecturas de PNG (redactor / productor) | 6 / 3 | 3 / 2 | 2 / 1 |
| investigador: búsquedas / fetch / cifras / series | 14 / 16 / 16 / 6 | 7 / 8 / 8 / 3 | — |
| entregable | `investigacion/<fecha>-<slug>/` | `sesiones/<slug>/{salida,informe}/` | ídem |
| memoria | `hilos.json` (modo investigacion) + `informes.json` | no | no |

`desde:<slug>`: el hilo ya se entregó (`hilos/<fecha>-<slug>/`); el informe lo
referencia por ruta y no lo duplica; `informes.json` lo registra con `modo:
"desde"`. El número del informe lo da el comando con `python3 scripts/memoria.py
--informes` («siguiente N.º NN») y viaja en `args.numero` → `encuadre.informe`
→ `guion.investigacion` → `informe.json.meta.numero`.

Guía por rol: «Modo investigación» en editor (y «Modo desde»), investigador,
verificador, guionista, visualista y productor; el redactor tiene guía propia.

- Contrato de archivos y reglas de datos: `referencias/contrato-sesion.md` («Sesión investigación»)
- Guía por rol: `referencias/roles/{editor,investigador,verificador,guionista,visualista,productor,redactor}.md`
- Narrativa del hilo de investigación: `referencias/narrativa.md`, «Hilo de investigación»
- Contrato de `informe.json`, tipos de página y gráficos del documento: `referencias/diseno/informe.md`
- Catálogo de gráficos (mismo contrato en tarjeta y documento): `referencias/diseno/graficos.md`
- **Estilo**: el informe y las tarjetas de su hilo se quedan en el **estilo clásico** (papel, paletas planas,
  Instrument Serif; apéndice de `referencias/diseno/sistema.md`), aunque las tarjetas de `/hilo` y `/dato` y los
  videos vayan en Noche. `materializar.py` lo elige solo por `guion.modo = "investigacion"`; `informe.py` arma
  clásicas sus figuras y rearma clásica cualquier tarjeta Noche que copie (`desde:<slug>` sobre un `/hilo`
  entregado: el hilo de `hilos/` se queda Noche, sus figuras en el PDF salen clásicas)
- Prueba sin agentes: `make informe-fixture` (tras el fixture de hilo) y `make informe-catalogo`

## Variante auditoría (`args.auditoria`)

Evalúa **cada compromiso** de un plan de gobierno. El inventario
(`investigacion/auditorias/<plan>/compromisos.json`, con el texto del plan en
`plan.txt`) lista cada compromiso con id (`S1-02`, `F-19`), semilla, eje,
`medida` (meta · monto · hito · tendencia · declarativo), `meta {valor, unidad,
base, sentido, techo?, nivel?}`, `monto_mq` y `espejo_de` (el mismo compromiso
repetido en otra semilla: se evalúa una vez y cuenta en las dos). Todo pasa por
`scripts/auditoria.py`:

```
Encuadre (ejes y capítulos fijados por args) → [Investigación → Verificación] por eje
→ Puntaje (auditoria.py --calcular → auditoria.json + cifras derivadas aud-cNN)
→ Guion → Visuales → Producción → Informe (30–140 págs., fichas y enlaces generados) → Revisión → Cierre
```

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `compromisos.json` | editor (copia del inventario) | el inventario; nadie lo edita en la sesión |
| `evaluacion_<eje>.json` | investigador | `{eje, corte, items[]{id, estado, medida_usada: meta\|monto\|hito, observado, base_obs, base_fecha, fecha_dato, cifra_ids[], resumen ≤260, fuente ≤90, evidencia[]{url, cita, archivo_local}, nota}}`; `--validar <eje>` hasta OK |
| `verificacion_<eje>.json` | verificador | lo de siempre más `compromisos[]{id, veredicto: confirmado\|corregido\|sin_sustento, campos corregidos, url_2, nota}`; `--validar <eje> --verificacion` |
| `auditoria.json` · `hallazgos_aud.json` · `verificacion_aud.json` | `auditoria.py --calcular` | puntaje por compromiso, semilla y global; cifras `aud-c01…` (fuente «Cálculo propio…», independencia baja) que el hilo y el informe citan con id |

**Atribución (para todo compromiso).** Solo cuenta lo ocurrido en el mandato
(desde el 14-ene-2024). `fecha_dato` cae dentro del mandato. Cada meta y monto
lleva `base_fecha`, desde cuándo se mide el cambio:
- las metas, desde el nivel de 2023 o el primer dato del mandato (`base_obs`, con su
  cifra), **nunca** contra un dato anterior a 2023 ni contra la base del plan
  (una encuesta de 2014-15 no sirve para medir a un gobierno que empezó en 2024);
- los conteos acumulados, desde `"2024-01"`;
- los montos, la ejecución desde 2024;
- los hitos, solo por hechos del mandato.

Sin un dato que mida dentro del mandato, el compromiso queda no_verificable.
`--validar` y `--calcular` aplican la regla.

**Método (mixto).** Meta = observado ÷ meta (acumulativa) o (observado − base_obs)
÷ (meta − base_obs) (nivel, con la base de 2023 o del inicio del mandato); `techo`: 100 si
observado ≤ meta. Monto = ejecutado ÷ prometido. Tendencia = cambio relativo en
el sentido deseado frente a `base_obs`: ≥ 10 % → 100, > 0 → 50, 0 → 0, en
contra → retroceso. Hito y declarativo por estado: cumplido 100 · en_proceso 50
· anunciado 25 · no_iniciado, incumplido, retroceso 0. Tope 100. Un número
solo cuenta si alguna de sus `cifra_ids` es verificada|ajustada; si no, el
compromiso queda **no_verificable**. Un no_verificable **cuenta 0**: lo que no se
puede comprobar con datos oficiales no se da por logrado. Aparte se publican la
cobertura, el avance «con dato» (`aud-c03`, solo verificables) y los puntos que
restan los no verificables (`aud-c08`). Los textos dicen «sin dato oficial», no
«incumplido» ni «no se hizo». Semilla = promedio simple;
global = promedio de las 10 semillas; el marco fiscal (F) se informa aparte.
Ritmo (metas acumulativas y montos): avance frente al % del mandato transcurrido
a la fecha del dato.

**Informe.** Un capítulo por semilla (más el marco fiscal) con su figura
`barras_h` de `aud-c1N` (`aud-c21` el fiscal) y las páginas generadas
`{"tipo": "cuerpo", "auto": "fichas:<N|F>"}`; el anexo
`{"tipo": "anexo", "auto": "evidencias:todas"}`. `auditoria.py --insertar
<informe.json>` las expande (idempotente) antes de cada `informe.py --check`.
Las fichas («de dónde sale cada barra») dan, por compromiso, una fila con
estado, **cálculo** (`Q64,642 M ÷ Q110,000 M = 58.8%`, `(91.5 − 90.39) ÷
(100 − 90.39) = 11.6%`, `Hito: en proceso = 50`, `No verificable: cuenta 0`)
y avance, y debajo **qué encontramos**: el hallazgo, la línea base o el motivo
del 0, el ritmo y la fuente con la fecha del dato. `--insertar` además añade
al pie de cada gráfico de avance por compromiso la remisión
`{tabla:fichas-N} (p. {pag:fichas-N})`; el anexo queda para la trazabilidad
(sitio del documento y verificación con segunda fuente). El gate
`auditoria.py --justificar <informe.json>` (J1–J5) exige que cada barra tenga
su ficha con hallazgo, fuente, fecha (los hitos) y cálculo completo, y que el
gráfico remita a ella; el texto de cada capítulo explica además los
compromisos que pesan (lo revisa el `informe-revisor`, V2);
`"lineas"` en el placeholder baja el tope si salta P2. Topes: 30–140 páginas,
un capítulo por entrada de `args.auditoria.capitulos`, ≥ 12 figuras, ≥ 11
tablas, ≤ 10 lecturas de PNG del redactor. Presupuesto del investigador por
eje: 8 + 2n búsquedas (≤ 36), 10 + 2n fetch (≤ 40), 8 + 2n cifras (≤ 40), con n
= compromisos del eje.

`args.auditoria = {inventario, slug, plan, mandato_inicio? ("YYYY-MM-DD", por
defecto 2024-01-14: fija las fechas de atribución de los prompts), ejes[{id,
nombre, prefijo, compromisos[]}], capitulos[{n, titulo, pregunta, ejes[]}]}`; los ejes salen de
`python3 scripts/auditoria.py --inventario <compromisos.json> --ejes`. Solo en
modo normal.

### Revisión (`args.auditoria.revision`)

`revision = {motivo, ids: {<eje>: [compromisos a reinvestigar]}}` rehace una
auditoría sobre su sesión existente, con los mismos `args.auditoria`, `numero` y
`fecha`, y el entregable se sobrescribe:
- **Encuadre:** el editor devuelve `encuadre.json` tal cual.
- **Revisión por eje:** el `revisar-<eje>` (investigador) corrige y amplía
  `evaluacion_<eje>.json` y `hallazgos_<eje>.json` en su lugar (cifras nuevas con
  ids que siguen la numeración) y reinvestiga a fondo los `ids`. Devuelve todas las
  cifras más `nuevas[]` y `revisados[]`.
- **Reverificación:** el `reverificar-<eje>` (verificador) verifica solo `nuevas`,
  revisa los `revisados` y conserva lo demás.
- **Después:** Puntaje → Guion → Visuales → Producción → Informe → Cierre, como
  siempre; el guion y el informe se reescriben con los números nuevos.

Presupuesto de la revisión por eje, con n = número de `ids`: 6 + 3n búsquedas y
6 + 3n fetch (≤ 36 cada uno), y 4 + 2n cifras nuevas (≤ 24). Antes de relanzar,
mueve a un respaldo el `hilo/` y el `salida/` del entregable y los `visuales/`
de la sesión: `ensamblar.py` no borra las tarjetas sobrantes.

**Hitos atribuibles.** La `fecha_dato` de un hito es la del hecho del mandato
que sostiene su estado (creación, aprobación, firma, inauguración), no la de la
consulta. Un programa o norma de antes del 14 de enero de 2024 que solo sigue
operando es `no_atribuible` con `existe_desde` (fecha anterior al mandato,
obligatoria: `--validar` la exige) y cuenta 0 (casos del plan
de Semilla: el IGSS para migrantes rige desde noviembre de 2023; Graduandos se
aplica desde 2013; el Plan Estratégico del IGSS es de 2023). Una meta que ya se
cumplía al inicio del mandato también es `no_atribuible` (el script la marca
sola: el adulto mayor, 212,102 en diciembre de 2023 frente a 200,000). A
diferencia del no verificable, hay dato: entra en el avance «con dato» y no
resta en `aud-c08`. Si lo único del mandato es un anuncio, es `anunciado`.
`--validar` avisa cuando el texto de un hito con puntos habla de algo anterior
al mandato; el verificador lo confirma y el revisor lo vigila (V8). Un hito con
`fecha_dato` anterior al mandato falla con la sugerencia `no_atribuible`.

**Reglas en el código** (`auditoria.py`, no solo en los prompts):
- **Retroceso**: peor que la línea base de 2023, aunque sea por poco;
  exactamente igual es «sin iniciar». `cambio_rel` lleva 2 decimales cuando es
  menor que 1% («−0.02%», nunca «−0.0%») y `fmt` conserva hasta 2 decimales de la
  fuente (102.13 y 102.11 nunca se imprimen igual).
- **Observado con respaldo**: `--validar` coteja `observado` y `base_obs` con
  los valores de sus `cifra_ids` (redondeo, escala, operación de dos o suma de
  hasta cuatro: acumulados del mandato); si no salen, exige
  `calculo_observado` / `calculo_base_obs` con la operación, que se evalúa.
- **Línea base mínima** = 1 de enero del año anterior al inicio del mandato
  (sale del inventario); días del mandato y nombre del plan, también.
- **Rechequeo de auditoría** (fase Rechequeo, antes del Puntaje): un verificador
  revisa los compromisos cumplidos, en retroceso, incumplidos y no atribuibles
  con «¿por qué podría estar mal?» (atribución, misma definición y categoría en
  la base y en el dato actual, magnitud real, cifra preliminar) y corrige en
  `verificacion_<eje>.json`; `--calcular` lo recoge.
- **Rehacer sin agentes**: tras corregir a mano evaluaciones o verificaciones,
  `make auditoria-rehacer SESION=sesiones/<slug> [DIR=investigacion/<fecha>-<slug>]`
  encadena validar → calcular → insertar → `informe.py --check` → J1–J5 → R1–R6.
- Pruebas: `sesiones/_fixture_auditoria` (2 semillas, 8 compromisos) en `make test`.
- **Tarjetas que ya no están en el hilo**: si el informe conserva figuras `tarjeta`
  de una versión anterior del guion (el hilo se rehízo), sus PNG viven en
  `investigacion/<fecha>-<slug>/tarjetas-informe/` y son parte del entregable:
  no se regeneran desde el guion actual, así que se commitean con el informe.

## Revisión de justificación (`informe-revisor`)

Tras el Informe, el revisor (guía `referencias/roles/revisor.md`) lee
`python3 scripts/revision.py <sesion>` (por página: texto, figuras con sus
valores y pies, tablas y los avisos mecánicos R1–R6: R4 otro redondeo del mismo
número en la página, R5 conteo de estados distinto de su figura, R6 sigla sin
glosario) y, en auditoría,
`auditoria.py --justificar` y `--resumen --para redactor`. Comprueba V1–V8:
cada figura se explica, cada valor tiene origen, cada % dice de qué es, cada
afirmación lleva respaldo, coherencia entre lead, texto, figura, ficha y
conclusiones, nada sin definir, nada falta, honestidad. Devuelve las faltas
(`bloquea` | `mejora`) con un arreglo exacto y las deja en
`<sesion>/revision_informe.json`. Si hay faltas que bloquean, el redactor las
corrige (vuelve a pasar I1–I7, P1–P5 y J1–J5) y el revisor relee: hasta 3
vueltas. En la primera, el revisor resuelve antes los avisos mecánicos (cada uno
es una falta con su regla R/J o se descarta con motivo). Si siguen quedando, el informe se entrega `incompleto`.

