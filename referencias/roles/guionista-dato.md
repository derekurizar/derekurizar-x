# §Guionista · modo dato (`/dato`)

Complemento de `referencias/roles/guionista.md` (léela primero): solo lo lee `/dato` y sus modos
`vs`, `mapa` y `antes`.

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
   - La tarjeta sale en estilo Noche (`referencias/diseno/sistema.md`): fondo
     casi negro de la paleta, titular en Archivo 800 (caja normal, nunca en
     mayúsculas) y **una sola cosa en acento**: la cifra del dato (en `vs`,
     Guatemala; en `mapa`, el departamento que nombra el titular). La cifra
     protagonista sale condensada y en mayúsculas (un sufijo « mil» se ve
     «MIL»): todo se escribe en caja normal y la plantilla pone la caja.
   - `visual` obligatorio: `cifra` por defecto (`cifra.valor`, `cifra.texto`,
     `contexto` ≤ 60 cuya aritmética sale de `cifra.valor` y
     `comparacion.valor`, `tendencia`, `comparacion` opcional). Cambia de
     plantilla cuando el dato lo pide: `antes-despues` (dos momentos), `waffle`
     (N de cada 100), `dona` (reparto), `bullet` (contra meta), `mapa` (brecha
     territorial), `linea` (récord con serie), `pictograma` (K de N unidades
     contables), `cascada` (de un total a otro sumando y restando),
     `linea-tiempo` (hitos con fecha y magnitud), `hemiciclo` (curules por
     bloque). `visual.cifra_ids` incluye
     `dato.cifra_id`; la fuente va en el pie; no hay cierre que nombre fuentes.
   - `alt_text` 20–1000: tipo de gráfico, cifra con unidad y periodo, fuente.
5. Escribe `<sesion>/guion.json` COMPLETO: `slug, fecha, tipo: "dato", paleta,
   smoke, handle, hook_tipo, dato, candidatas, sintesis, tuits`. Retorno:
   `archivo, tipo, tesis, ancla_id, paleta, hook_tipo, dato, candidatas,
   no_afirma, tuits[]` con `visual` completo. Si el workflow devuelve fallos,
   corrige solo eso.

## Modos vs · mapa · antes

La directiva trae `MODO DEL POST`. Escribe `modo` en `guion.json` y el bloque
del modo; el gate exige gancho y plantillas por modo
(`referencias/narrativa.md`, «Modos de un dato»).
- **`vs`**: `vs{paises[] (como aparecen en partes y en el visual, Guatemala
  incluida), fuente_comun, periodo, per_capita (false exige motivo ≥ 20)}`.
  Cifra elegida: el desglose por país. Plantillas: `barras-h` (`orden: "desc"`
  y `destacar` = índice de Guatemala tras ordenar), `pesas`, `pendiente` o
  `dispersion` con los países como items/puntos, o `cifra` con `comparacion`
  (el otro país). `nota` con fuente común y año. Sin «ganamos/perdemos».
- **`mapa`**: `mapa{per_capita, denominador («población INE 2026» o null),
  motivo (≥ 20 si per_capita es false)}`. Cifra elegida: el desglose
  departamental (≥ 12). Plantilla `mapa` con la tasa, extremos rotulados o
  `destacar`; `hook_tipo: "brecha_territorial"`; titular con la brecha (razón
  o diferencia entre extremos); `nota` con unidad y año.
- **`antes`**: `antes{anio_antes, anio_despues (≥ 5 años), nominal (true si es
  dinero corriente, false si es real o no es dinero, null si no aplica)}`.
  `hook_tipo: "antes_despues"`. Plantillas: `antes-despues` (etiquetas con los
  años; la píldora la calcula la plantilla), `pendiente` o `pesas` (`fechas` =
  los dos años), `agrupadas` (las dos series se llaman como los años) o `linea`. Si `nominal` es true, la `nota` dice «quetzales
  corrientes» (o «dólares corrientes»).
