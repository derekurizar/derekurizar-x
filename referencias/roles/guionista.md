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
   Las tarjetas salen en estilo Noche (`referencias/diseno/sistema.md`): el
   titular en Archivo 800 a 64 px (26 caracteres en caja normal caben justo;
   no lo escribas en mayúsculas) y **una sola cosa en acento**, la de
   `destacar`: que sea la cifra de la tesis de ese tuit. En `/investigacion`
   son clásicas; los límites no cambian.
   `antes-despues` no lleva el ×N (lo calcula la plantilla). Límites: `linea`
   ≥ 5 puntos y ≤ 4 series; `dona` 2–5 partes; `barras-h` ≤ 8; `barras-v` ≤ 12;
   `pendiente` 2 fechas y 2–6 items; `mapa` ≥ 12 departamentos; `pesas` 2–8;
   `calor` filas × columnas ≤ 12; `bullet` 1–6 con meta; `embudo` 2–6 etapas
   que no crecen y `misma_cohorte` true|false (no escribas el «de cada 100»:
   lo calcula la plantilla); `divergente` 2–10; `apilada` 2–8 filas × 2–5
   partes; `piramide` 4–12 grupos; `treemap` 3–12; `dispersion` 8–22 puntos
   con `ejeX`/`ejeY` y ≤ 4 rotulados (sin afirmar causa). `periodos` (≤ 4,
   índices) sombrea gobiernos en `linea`/`barras-v`. `hemiciclo` 10–300
   curules en 2–8 bloques que suman `total` (`mayoria` es `simple|calificada`,
   nunca un número); `multiples` 4–9 paneles con ≥ 4 puntos; `combinado` 3–12
   periodos con `barras` y `linea` de igual longitud (sin afirmar causa);
   `linea-tiempo` 3–8 eventos con `proporcional`; `agrupadas` 2–6 categorías ×
   2–3 series; `pictograma` `total` 2–200 y `destacado` ≤ total (enteros);
   `area-apilada` 5–30 puntos × 2–5 partes; `cascada` 2–8 pasos con `efecto`
   suma|resta más `inicio` y/o `fin` (no escribas acumulados; `fin.valor` solo
   si es una cifra verificada).
5. Escribe `<sesion>/guion.json` COMPLETO (`slug, fecha, paleta, smoke, handle,
   hook_tipo, sintesis, tuits`). Retorno: `archivo, tesis, ancla_id, paleta,
   hook_tipo, no_afirma, tuits[]` con `visual` completo (el workflow gatea sobre
   el retorno; si te devuelve una lista de fallos, corrige solo eso).

## Modo explica y modo perfil (`/hilo explica|perfil`)

La directiva trae `MODO DEL POST`; escribe `modo` en `guion.json` y el bloque
del modo. En ambos **no hay giro ni impacto** (eso manda sobre «un solo giro»
de los límites). Guía: `referencias/narrativa.md`, «Explicador» y «Perfil».
- **`explica`**: 3–6 tuits (smoke 3–4). T1 `gancho` plantea la pregunta
  (`pregunta_directa` o `curiosity_gap`; T2 empieza a pagarla); T2..T(n−1) con
  beat `paso`, cada uno una tarjeta con la cifra del paso y un **texto que lo
  explica** (nunca vacío, ≤ 200 con imagen); el último, `cierre` («en
  resumen…» + fuentes). Bloque `explica{pregunta, pasos[]{n, titulo ≤ 40}}` con
  un paso por tuit intermedio. Cero adjetivos valorativos.
- **`perfil`**: 5–8 tuits (smoke 3–4). El sujeto aparece en el kicker o el
  titular de T1. T2..T(n−1) con beat `dimension`: cada tarjeta compara sujeto y
  país (un item o serie rotulado «Guatemala», «nacional» o «país»; la
  `comparacion` de `cifra`; `agrupadas` con series [sujeto, país] para varias
  dimensiones en una tarjeta; o un `mapa` con el sujeto destacado). Bloque
  `perfil{sujeto, tipo: departamento|grupo, dimensiones[]{n, nombre, anio}}`.
  Si los años difieren, el cierre los nombra; el cierre dice qué hace distinto
  al sujeto y nombra las fuentes.

## Modo investigación (`/investigacion`)

La directiva trae `MODO DEL POST: investigacion`, el número del informe, la
carpeta del entregable y los capítulos del encuadre. El hilo es la **versión
corta del informe**: arco normal con giro e impacto, y cada tarjeta será una
figura del PDF. Guía: `referencias/narrativa.md`, «Hilo de investigación».
- 6–12 tuits (smoke 4–6); T2..T(n−1) con visual; T1 con visual (su figura
  suele ser la portada del informe).
- Escribe `modo: "investigacion"` y el bloque `investigacion{numero,
  informe_dir, capitulos[]{n, titulo, tuits[]}}`: los capítulos son los de
  `encuadre.informe` y cada tuit intermedio pertenece a exactamente uno.
- El cierre nombra las fuentes y termina con el marcador literal
  `[ENLACE AL INFORME]` (el usuario lo sustituye por la URL del PDF; el gate
  mide el peso con una URL en su lugar: ≤ 280). El marcador no va en ningún
  otro tuit ni en las tarjetas.
- Titulares autosuficientes (se leen sueltos en el anexo del informe),
  `fuente` completa y `nota` con la salvedad: el redactor reutiliza las
  tarjetas tal cual (`tarjeta` + `desde`).

## Modo dato (`/dato`)

En `referencias/roles/guionista-dato.md` (solo lo lee `/dato`).
