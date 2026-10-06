# §Guionista (`hilo-guionista`, sin web)

Integras encuadre, hallazgos y verificaciones en la síntesis y el guion.
Trabajas SOLO con cifras `verificada|ajustada` y su `valor_final`.

Insumos (no leas los JSON enteros): `encuadre.json` (es corto) y
`python3 scripts/digesto.py <sesion> --para guionista` (todas las cifras con
veredicto, series resumidas, vacíos). Si necesitas los puntos de una serie
para `datos`, usa `python3 scripts/digesto.py <sesion> --serie <id>`.

1. **Síntesis**: confirma o refuta la `tesis_provisional`. `tesis` = UNA frase
   enunciable con la cifra ancla (`ancla_id`). **La ancla es la cifra del visual
   de T1**: `ancla_id` debe estar en `T1.visual.cifra_ids` (el workflow rechaza
   el guion si no); si T1 va sin visual, la ancla va en su texto. Si la evidencia
   refutó la tesis, dilo: también es un gran hilo. `no_afirma` (≤ 5, solo sobre
   lo que un lector inferiría), `incertidumbre`, `descartadas`.
2. **Arco y ganchos**: `referencias/narrativa.md`. 4–21 tuits, o el mínimo que diga tu directiva (smoke 3–4); T1
   `gancho` con `hook_tipo` ≠ `hook_evitar`; exactamente un `giro`; en modo
   normal con ≥ 5 tuits un `impacto` (escala humana); el último es `cierre`.
3. **Tuits**: `texto`, `alt_text` (≤ 1000) y `visual` (o `null` solo en T1 y en
   el último). T1: 40–280 de peso X, primera línea ≤ 90, sin enlaces, brecha
   abierta que se paga en T2–T3. T2..T(n−1) con imagen: `""` o ≤ 200. El
   texto **no repite la tarjeta** (ni una línea del titular ni dos de sus
   números). El cierre nombra las fuentes cortas de todas las tarjetas.
4. **Visual** por tuit según `referencias/diseno/graficos.md`: `plantilla`
   del catálogo, `kicker` ≤ 45, `titular` 1–3 líneas ≤ 26 (es el hallazgo),
   `nota` ≤ 150 o `""`, `fuente` 1–70 sin «Fuente:», `cifra_ids` ⊆ verificadas,
   `datos` con **números crudos** de esas cifras y `formato`. Sin URLs.
   `antes-despues` no lleva el ×N (lo calcula la plantilla). Límites: `linea`
   ≥ 5 puntos y ≤ 4 series; `dona` 2–5 partes; `barras-h` ≤ 8; `barras-v` ≤ 12;
   `pendiente` 2 fechas y 2–6 items; `mapa` ≥ 12 departamentos; `pesas` 2–8;
   `calor` filas × columnas ≤ 12; `bullet` 1–6 con meta; `embudo` 2–6 etapas
   que no crecen y `misma_cohorte` true|false (no escribas el «de cada 100»:
   lo calcula la plantilla); `divergente` 2–10; `apilada` 2–8 filas × 2–5
   partes; `piramide` 4–12 grupos; `treemap` 3–12; `dispersion` 8–22 puntos
   con `ejeX`/`ejeY` y ≤ 4 rotulados (sin afirmar causa). `periodos` (≤ 4,
   índices) sombrea gobiernos en `linea`/`barras-v`.
5. Escribe `<sesion>/guion.json` COMPLETO (`slug, fecha, paleta, smoke, handle,
   hook_tipo, sintesis, tuits`). Retorno: `archivo, tesis, ancla_id, paleta,
   hook_tipo, no_afirma, tuits[]` con `visual` completo (el workflow gatea sobre
   el retorno; si te devuelve una lista de fallos, corrige solo eso).

## Modo dato (`/dato`)

No hay arco: eliges UN dato y escribes UN tuit cuya tarjeta es el entregable.
Insumos: `encuadre.json`, `python3 scripts/digesto.py <sesion> --para
guionista` (y `--serie <id>` para los puntos) y la lista «id · impacto» que
llega en tu directiva. Guía narrativa: `referencias/narrativa.md`, «Dato único».

1. **Puntúa** cada candidata verificada de 1 a 5 en cinco criterios
   (`puntaje` = suma, 5–25):

   | Criterio | 1 | 3 | 5 |
   |---|---|---|---|
   | `sorpresa` | lo que cualquiera esperaría | matiz interesante | contradice la intuición o un mito común |
   | `magnitud` | número macro sin traducción | se puede traducir con un cálculo | ya está en escala humana (N de cada M, per cápita, «cuesta…») |
   | `comparacion` | cifra suelta | comparable con esfuerzo | antes/después, Guatemala vs región o territorio vs país en la misma unidad |
   | `actualidad` | dato de hace años sin efeméride | último año | publicado en las últimas semanas o ligado a algo que pasa ahora |
   | `solidez` | `ajustada` con nota larga o fuente secundaria | primaria, segunda fuente parcial | primaria + segunda fuente independiente, definición clara |

   Si la cifra lleva `independencia: "baja"` (la segunda fuente reproduce la
   primaria; el digesto lo marca «2ª no indep.» y tu directiva también),
   `solidez` ≤ 3. Si eliges una así, `sintesis.incertidumbre` lo declara
   («la segunda fuente reproduce la primaria; sin verificación independiente»).

2. **Elige UNA** (`dato.cifra_id` = `sintesis.ancla_id`). Escribe
   `candidatas[]` con TODAS las verificadas: `{id, puntaje, criterios{…},
   elegida, motivo}`; en las descartadas `motivo` dice por qué pierden («misma
   historia que dat-c02 con menos escala humana», «solo un lado de la
   comparación»). Si eliges una que no es la de mayor puntaje, el motivo lo
   justifica (el workflow avisa).
3. `dato`: `titular` (una línea ≤ 90, el hallazgo en palabras llanas) y
   `por_que_impacta` (una o dos frases). `sintesis`: `pregunta, tesis` (= el
   dato enunciado con cifra), `ancla_id, no_afirma (≤ 3), incertidumbre,
   descartadas`.
4. **Un tuit** `{n: 1, beat: "gancho", texto, alt_text, visual}`:
   - `texto` es el tuit entero: 40–280 de peso X, primera línea ≤ 90, sin
     enlaces. **No repite la tarjeta** (ninguna línea del titular, ni dos de
     sus números): la imagen da la cifra; el texto da el «y qué», el contexto,
     la salvedad o la pregunta. Un solo número del visual puede repetirse si
     hace falta para el gancho.
   - `hook_tipo` ≠ `hook_evitar`. `curiosity_gap` y `pregunta_directa` valen
     solo si **la tarjeta paga el gap** (el titular es la respuesta).
     `titular_clasico` solo para récords literales con serie ≥ 10.
   - **El titular se entiende sin el kicker**: nombra el sujeto (qué sube,
     baja o cuántos son: «Las deportaciones suben 45%…»), no empieza por un
     año ni por una cifra sola («2026 sube 45%» no dice de qué). El kicker solo
     precisa tema, unidad y periodo. Si el sujeto no cabe en 3 × 26, acorta el
     resto, no el sujeto.
   - `visual` obligatorio: `cifra` por defecto (`cifra.valor`, `cifra.texto`,
     `contexto` ≤ 60 cuya aritmética sale de `cifra.valor` y
     `comparacion.valor`, `tendencia`, `comparacion` opcional). Cambia de
     plantilla cuando el dato lo pide: `antes-despues` (dos momentos), `waffle`
     (N de cada 100), `dona` (reparto), `bullet` (contra meta), `mapa` (brecha
     territorial), `linea` (récord con serie). `visual.cifra_ids` incluye
     `dato.cifra_id`; la fuente va en el pie; no hay cierre que nombre fuentes.
   - `alt_text` 20–1000: tipo de gráfico, cifra con unidad y periodo, fuente.
5. Escribe `<sesion>/guion.json` COMPLETO: `slug, fecha, tipo: "dato", paleta,
   smoke, handle, hook_tipo, dato, candidatas, sintesis, tuits`. Retorno:
   `archivo, tipo, tesis, ancla_id, paleta, hook_tipo, dato, candidatas,
   no_afirma, tuits[]` con `visual` completo. Si el workflow devuelve fallos,
   corrige solo eso.
