# Catálogo de gráficos y contrato `DATA`

Lo leen el **guionista** (para elegir plantilla y rellenar `visual.datos`) y el
**visualista** (para el QA). Las plantillas viven en `templates/graficos/`; se
ven todas con `make catalogo` (PNG en `templates/.galeria/`).

## Primero la pregunta, luego el gráfico (brief 6b)

| ¿Qué pregunta responde el tuit? | Gráfico | Plantilla | Nota |
|---|---|---|---|
| ¿Cómo cambió en el tiempo? | Línea · área | `linea` | 1 serie para un total; 2–4 para comparar. ≥ 5 puntos. |
| ¿Qué periodo fue mayor? | Barras verticales | `barras-v` | Periodos discretos (años, meses). Eje desde cero. ≤ 12. |
| ¿Quién está arriba? | Barras horizontales | `barras-h` | Rankings y etiquetas largas. Ordenar de mayor a menor. ≤ 8. |
| ¿Cómo se reparte el todo? | Dona | `dona` | 2–5 partes; si hay más, agrupar en «Todo lo demás». |
| ¿Cuánto cambió entre dos momentos? | Pendiente (slope) | `pendiente` | Dos fechas, 2–6 categorías: se lee dirección y magnitud. |
| ¿Cuánto cambió UNA cosa entre dos momentos? | Antes / después | `antes-despues` | Dos cifras grandes + ×N o +% **calculado por la plantilla**. |
| ¿Qué tan grande en términos humanos? | Waffle | `waffle` | Proporción de 100. |
| ¿Cuál es EL dato? | Cifra héroe | `cifra` | Ancla del T1 (pregunta abierta) o cierre. Sin gráfico. |
| ¿Dónde? (brecha territorial) | Mapa coroplético | `mapa` | 22 departamentos; ≥ 12 con valor; rampa por clases; «Mayor/Menor». |
| ¿Cuánto cambió cada categoría entre dos fechas? | Pesas (dumbbell) | `pesas` | 2–8 categorías; dos puntos unidos; alternativa a `pendiente` con etiquetas largas. |
| ¿Cuándo pasa? (estacionalidad) | Mapa de calor mensual | `calor` | Filas = años, columnas = meses (≤ 12); celdas `null` permitidas. |
| ¿Vamos hacia la meta? | Bullet | `bullet` | 1–6 items contra una meta o capacidad; el exceso se raya. Mejor que `barras-v` cuando todo está entre 85 y 100 %. |
| ¿Cuántos llegan al final? | Embudo | `embudo` | 2–6 etapas que no crecen (denuncias → capturas → sentencias). «N de cada 100» lo calcula la plantilla. |
| ¿Quién subió y quién bajó? | Barras divergentes | `divergente` | 2–10 cambios con signo desde un eje cero central. |
| ¿Cómo cambió el reparto? | Barras apiladas | `apilada` | 2–8 filas (años o categorías) × 2–5 partes; 100 % o absolutos. |
| ¿Cómo se distribuye? | Pirámide | `piramide` | 4–12 grupos (edades) con dos lados en la misma escala (sexo, urbano/rural). No usar dona. |
| ¿Cómo se reparte el todo? (> 5 partes) | Treemap | `treemap` | 3–12 partes; las chicas o sin sitio para el nombre se agrupan solas en «Todo lo demás». |
| ¿Van juntas dos cosas? | Dispersión | `dispersion` | 8–22 puntos (departamentos), ≤ 4 rotulados + destacado; el titular **no afirma causa**. |

En `linea` y `barras-v`, `periodos` sombrea tramos (gobiernos, etapas) sobre el
eje X: `[{desde, hasta, nombre}]`, índices sobre las etiquetas, en orden, sin
solaparse, ≤ 4. `barras-v` admite negativos (la base es el cero y el rótulo va
bajo la barra); para cambios con signo por categoría, mejor `divergente`.
`formato.signo: true` antepone «+» a los positivos (por defecto en `divergente`).

Aún no hay plantilla para: hemiciclo, pequeños múltiplos, combinado barras +
línea, línea de tiempo con magnitud (brief 7a, 7d, 7f, 6h). Si el material lo
pide, el guionista elige la más cercana del catálogo y lo anota en
`incertidumbre`; **no se inventa una plantilla en el HTML**.

Ejemplos de traducción: hogares receptores / beneficiarios / dependencia →
`waffle` («24 de cada 100 hogares»), `barras-h` con `orden: "dado"` (tramos) o
`cifra` con `comparacion`; una serie mensual larga → `calor` (años × meses) en
vez de `linea` con 90 puntos; ejecución presupuestaria contra el 100 % →
`bullet`; denuncias → capturas → sentencias → `embudo` (con
`misma_cohorte: false` si no son los mismos casos); presupuesto por ministerio
o exportaciones por producto con más de 5 partes → `treemap`, no `dona`;
comparación por gobierno sobre una serie anual → `linea`/`barras-v` con
`periodos`.

## Cabecera común (todas las plantillas)

```json
{
  "kicker": "REMESAS · MILLONES DE US$",
  "titular": ["2025 fue el año", "más alto de la historia"],
  "leyenda": [],
  "nota": "",
  "fuente": "Banguat · remesas familiares · 2025",
  "cifra_ids": ["eco-c01"],
  "datos": { "formato": { "prefijo": "", "sufijo": "", "decimales": 0, "miles": true, "escala": 1 }, "…": "bloque específico" }
}
```

- `kicker` ≤ 45 · `titular` 1–3 líneas de ≤ 26 · `nota` ≤ 150 (o `""`) ·
  `fuente` 1–70 sin «Fuente:» · nada de URLs.
- `datos.formato` rotula los valores: `prefijo` («Q», «US$»), `sufijo` («%»,
  « M»), `decimales`, `miles` (coma), `escala` (divide antes de rotular: 1e6
  para millones). **Los números de `datos` van crudos, en la unidad de la
  fuente**, nunca como texto formateado: el gate mecánico los coteja contra
  las cifras verificadas (C3).
- `leyenda` solo la usan cifra/antes-después si quieren un texto libre; `linea`
  la construye sola desde las series.

## Bloque específico por plantilla

| Plantilla | `datos` específico | Reglas que aplica la plantilla |
|---|---|---|
| `cifra` | `cifra:{valor, texto}`, `contexto` (≤ 60, opcional), `tendencia: "sube"\|"baja"\|null`, `comparacion:{etiqueta, valor}` (opcional, dibuja dos barras proporcionales) | Cifra a 220 px con auto-ajuste. |
| `linea` | `etiquetasX[≥3]`, `series[1–4]{nombre, valores[], destacar}` (`null` = hueco), `yDesdeCero` (true), `ejeY` (true), `valoresBajoEje` (null=auto: 1 serie y ≤ 12 puntos), `rotularFin` (null=auto: >1 serie), `hitos[≤1]{i, texto}`, `periodos[≤4]{desde, hasta, nombre}` (bandas) | Destacada en `a1` grosor 6; punto final en cada serie; rótulos finales con anti-solape; `yDesdeCero:false` escribe «eje desde N (no desde cero)». |
| `barras-v` | `etiquetas[]`, `valores[2–12]`, `destacar` (índice; −1 = última), `rotular: "todas"\|"destacada"`, `referencia:{valor, texto}` (opcional), `periodos[≤4]{desde, hasta, nombre}` (bandas) | Desde cero; negativos bajo el eje con el rótulo debajo. Destacada en `a1`, resto tinta con opacidad ascendente. |
| `barras-h` | `items[2–8]{nombre, valor, valor_texto?}`, `destacar` (índice tras ordenar), `orden: "desc"\|"dado"` | Barra a lo ancho (máx = 100 %). `valor_texto` permite «3.02 M» sin tocar el número. |
| `antes-despues` | `antes:{etiqueta, valor, sub}`, `despues:{etiqueta, valor, sub}`, `pildora: "factor"\|"pct"\|"ninguna"`, `decimales_pildora` (2) | **Calcula** ×N o +% desde los dos valores: el guionista nunca lo escribe. |
| `dona` | `partes[2–5]{nombre, valor}` (absolutos o %), `destacar`, `centro:{valor, texto}` (opcional) | Normaliza a 100 %; destacada en `a1`. Declarar redondeo en `nota`. |
| `pendiente` | `fechas[2]`, `items[2–6]{nombre, a, b}`, `destacar` | Eje no parte de cero (compara posiciones); anti-solape a ambos lados. |
| `waffle` | `porcentaje` (0–100], `etiqueta_dentro`, `etiqueta_resto`, `cifra:{valor, texto}` | 10×10; si el porcentaje no es entero, escribe el redondeo en la nota. |
| `mapa` | `valores: {"GT01"\|"Guatemala": v, …}` (≥ 12 con valor), `cortes: null\|[c1…c5]` (límites internos), `clases: 5` (3–6; se ignora con `cortes`), `metodo: "cuantiles"\|"iguales"`, `redondear: true` (cortes automáticos a múltiplos de 1·2·5×10ⁿ; `false` = exactos), `destacar: "GT09"\|null`, `rotular: "extremos"\|"ninguno"` | Ids GT01–GT22 o nombres oficiales; rampa `H.rampa` del fondo a la tinta; sin dato = rayado + «N departamentos sin dato» al pie del gráfico; destacado con halo y contorno `a1`; columna derecha con leyenda y Mayor 3 / Menor 3. Los cortes automáticos se redondean a múltiplos «bonitos» (`redondear: false` los deja exactos); para límites a medida usa `cortes`. |
| `pesas` | `fechas[2]`, `items[2–8]{nombre, a, b}`, `destacar` (índice tras ordenar), `orden: "dado"\|"desc"`, `desdeCero: true` | `a` en tinta, `b` en `a1` unidos por barra de 8 px; valores junto a cada punto con anti-solape; `desdeCero:false` escribe «eje desde N». Con 8 items evita titulares de 3 líneas. |
| `calor` | `filas[1–12]`, `columnas[2–12]`, `valores[filas][columnas]` (`null` = sin dato), `clases: 5` (3–7), `destacar: {fila, col}\|null` | Color `H.rampaColor` sobre [mín, máx]; valor en celda solo si ≤ 6 filas; celda nula atenuada con «—»; leyenda mín · rampa · máx. |
| `bullet` | `items[1–6]{nombre, valor, meta?}`, `meta` común (si el item no trae la suya), `texto_meta` («meta», «capacidad»), `maximo` (tope de escala; null = el mayor entre valores y metas), `destacar` | Pista hasta `maximo`, barra en `ink` (destacada `a1`), marcador de 6 px en la meta; el tramo que excede la meta va rayado. Meta común: un rótulo al pie; metas propias: en la línea del nombre. Toda meta se coteja en C3 salvo un 100 (el total, que es definición). |
| `embudo` | `etapas[2–6]{nombre, valor}` (no crecientes), `porcentaje: "inicio"\|"anterior"\|"ninguno"`, `misma_cohorte: true\|false` (**obligatorio**) | **Calcula** «N de cada 100» del inicio (o de cada 1,000 si no llega a 1; un decimal por debajo de 10) o el % de la etapa anterior: el guionista no lo escribe. La última etapa en `a1`. Con `misma_cohorte: false` añade a la nota «Etapas del mismo periodo, no de los mismos casos». |
| `divergente` | `items[2–10]{nombre, valor}` con signo, `orden: "desc"\|"dado"`, `destacar` (índice tras ordenar) | Eje cero vertical; negativos a la izquierda en tinta tenue, positivos a la derecha en tinta, destacado en `a1`; valor con signo (`formato.signo` por defecto) fuera de la barra. |
| `apilada` | `etiquetas[2–8]` (filas), `partes[2–5]{nombre, valores[]}` (un valor ≥ 0 por fila), `normalizar` (true = 100 %), `destacar` (índice de parte), `rotular: "todas"\|"destacada"` | Con `normalizar` calcula los % y avisa en la nota si el redondeo no suma 100; sin él, apila absolutos y rotula el total. Segmento destacado en `a1`, resto en tonos de la tinta; % dentro solo si cabe. |
| `piramide` | `grupos[4–12]` (de arriba abajo), `izquierda:{nombre, valores[]}`, `derecha:{nombre, valores[]}`, `destacar` (índice de grupo), `rotular: null\|"todos"\|"destacado"` | Misma escala a ambos lados; grupos en la columna central; grupo destacado en `a1` en los dos lados; valores en todos si hay ≤ 8 grupos. |
| `treemap` | `partes[3–12]{nombre, valor > 0}`, `destacar` (nombre o índice tras ordenar), `minimo_rotulo` (% · 2) | Squarified. Agrupa en «Todo lo demás» las partes < `minimo_rotulo` (si son ≥ 2) y, una a una, las que no caben con nombre; lo explica en la nota. Cada rect lleva nombre y %. |
| `dispersion` | `puntos[8–22]{nombre, x, y}`, `ejeX`/`ejeY` (títulos ≤ 40), `formatoX`/`formatoY` (null = `formato`), `rotular[≤4]` (nombres), `destacar` (nombre), `guias:{x?, y?, texto}\|null` (líneas «promedio»; son dato), `desdeCero` (false) | Sin regresión. Rótulos colocados donde menos pisan (con línea guía si se alejan) y con halo; escribe «ejes sin cero» si no parten de cero. |

Ejemplo completo de cada bloque: el `const DATA` de cada archivo en
`templates/graficos/` (son las tarjetas del brief).

## Flujo del visualista (sin editar HTML a mano)

1. `python3 scripts/materializar.py sesiones/<slug> --tuit N` → ensambla la
   plantilla con el `visual` del guion y corre el gate de render. Exit 0 = pasa.
2. `Read` del PNG (`sesiones/<slug>/visuales/tuit_N.png`) y **checklist QA**.
3. Si algo hay que cambiar, escribe **solo** `sesiones/<slug>/visuales/tuit_N.ajuste.json`
   con las claves del `visual` a sustituir (`titular`, `nota`, `datos`,
   `plantilla`…) y repite el paso 1. Nunca toques `guion.json` ni el HTML:
   otros visualistas trabajan en paralelo y el productor consolida.
4. Máximo 3 iteraciones. Si el material no da para la plantilla pedida, usa
   `--forzar-plantilla <otra>` y explícalo en tu retorno.

## Checklist de QA visual (sobre el PNG, no sobre el código)

1. **¿Es el gráfico correcto para la pregunta?** ¿O debería ser una cifra héroe?
2. **Saliencia**: lo primero que se ve es el dato de la tesis (`a1`), no un
   detalle. Un solo acento por tarjeta.
3. **Escala honesta**: barras desde cero; si la línea no parte de cero, lo dice;
   la diferencia visual es proporcional a la diferencia real.
4. **Legible a 400 px** (vista de X en móvil): nada por debajo de 17 px, rótulos
   sin solape, ≤ 8 marcas o ≤ 4 series.
5. **Rótulo directo** antes que leyenda; el último punto siempre con valor.
6. **Titular = hallazgo**, no descripción («Guatemala alcanzó a México», no
   «Precios de gasolina por país»). Kicker = tema · unidad.
7. **Pie**: fuente real y año; handle presente.
8. **Ortografía y tildes**; sin emoji; cifras con miles y decimales coherentes
   con la unidad del kicker.
9. **Plantillas con trampa**: `embudo` declara si las etapas son los mismos
   casos; `dispersion` no sugiere causa en el titular y, si los rotulados están
   apiñados, rotula menos; `treemap` con «Todo lo demás» enorme pide
   `barras-h`.
10. **Coherencia con el guion**: los números del PNG son los del `visual.datos`
   (el gate mecánico lo comprueba, pero mira que el redondeo no engañe).
