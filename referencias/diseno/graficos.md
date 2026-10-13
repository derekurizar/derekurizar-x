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
| ¿Quién controla el Congreso? | Hemiciclo | `hemiciclo` | 10–300 curules en 2–8 bloques contiguos; «N para mayoría» lo calcula la plantilla. |
| ¿Cómo cambió cada uno? (muchas series) | Pequeños múltiplos | `multiples` | 4–9 mini-líneas en la MISMA escala; último valor rotulado; referencia opcional. Con 9 paneles, titular ≤ 2 líneas. |
| ¿Van juntas dos magnitudes en el tiempo? | Barras + línea | `combinado` | 3–12 periodos; barras (izq., desde cero) y línea (der.); ambas rotuladas; el titular **no afirma causa**. |
| ¿Cuándo pasó y cuánto pesó cada hito? | Línea de tiempo | `linea-tiempo` | 3–8 eventos en filas (fecha · nombre · magnitud desde cero); declara si los intervalos son proporcionales. |
| ¿Cómo se compara A con B en cada categoría? | Barras agrupadas | `agrupadas` | 2–6 categorías × 2–3 series (sujeto vs país; año vs año), horizontales, desde cero. |
| ¿Cuántos de los N? (unidades contables) | Pictograma | `pictograma` | 2–200 unidades absolutas, K en `a1`; «K de N» lo compone la plantilla. Proporciones de 100 → `waffle`. |
| ¿Cómo cambió el reparto a lo largo de una serie? | Área apilada 100 % | `area-apilada` | 5–30 puntos × 2–5 partes; % al inicio y al fin de cada banda. Para ≤ 8 momentos discretos, `apilada`. |
| ¿Cómo se llega del inicio al fin sumando y restando? | Cascada | `cascada` | inicio → 2–8 pasos (suma \| resta) → fin; ≤ 10 filas; acumulados y fin los calcula la plantilla. |

En `linea` y `barras-v`, `periodos` sombrea tramos (gobiernos, etapas) sobre el
eje X: `[{desde, hasta, nombre}]`, índices sobre las etiquetas, en orden, sin
solaparse, ≤ 4. `barras-v` admite negativos (la base es el cero y el rótulo va
bajo la barra); para cambios con signo por categoría, mejor `divergente`.
`formato.signo: true` antepone «+» a los positivos (por defecto en `divergente`).

Si el material no encaja en ninguna plantilla, el guionista elige la más cercana
del catálogo y lo anota en `incertidumbre`; **no se inventa una plantilla en el
HTML**.

Ejemplos de traducción: hogares receptores / beneficiarios / dependencia →
`waffle` («24 de cada 100 hogares»), `barras-h` con `orden: "dado"` (tramos) o
`cifra` con `comparacion`; una serie mensual larga → `calor` (años × meses) en
vez de `linea` con 90 puntos; ejecución presupuestaria contra el 100 % →
`bullet`; denuncias → capturas → sentencias → `embudo` (con
`misma_cohorte: false` si no son los mismos casos); presupuesto por ministerio
o exportaciones por producto con más de 5 partes → `treemap`, no `dona`;
comparación por gobierno sobre una serie anual → `linea`/`barras-v` con
`periodos`.
Sujeto vs país por dimensión (`/perfil`) o año anterior vs actual por categoría
→ `agrupadas`; ingresos → gasto → déficit, o partes que suman y restan hasta un
total → `cascada` (en `/explica`); reparto que cambia en ≥ 5 periodos →
`area-apilada` (≤ 8 momentos discretos → `apilada`); «37 volcanes, 3 activos» o
«22 departamentos, 5 con…» → `pictograma` (unidades reales; proporciones →
`waffle`); curules por bloque → `hemiciclo`; más de 4 series comparables →
`multiples`; dos magnitudes distintas en el tiempo (visitantes y gasto) →
`combinado`; hitos con fecha y magnitud (sismos, erupciones) → `linea-tiempo`.

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
| `hemiciclo` | `total` (entero 10–300), `bloques[2–8]{nombre, curules ≥ 0}` (de izquierda a derecha; suman `total`; vacantes = bloque «Vacantes»), `mayoria: "simple"\|"calificada"\|null`, `destacar` (índice) | Arco de asientos por filas con cuñas contiguas; destacado en `a1`, resto en la rampa; marcador y «N para mayoría» **calculados** (⌊total/2⌋+1 o ⌈2·total/3⌉): el guionista nunca escribe el 81; columna derecha con curules por bloque. |
| `multiples` | `etiquetasX[4–30]`, `paneles[4–9]{nombre, valores[]}` (`null` = hueco, ≥ 2 válidos), `destacar` (índice\|null), `referencia:{valor, texto}\|null`, `yDesdeCero` (true) | Rejilla 2×2 / 2×3 / 3×3 con la **misma escala**; último valor en la cabecera de cada panel; referencia punteada; etiquetas X solo abajo; escribe «Misma escala en todos los paneles.» (y «eje desde N» si aplica). |
| `combinado` | `etiquetas[3–12]`, `barras{nombre ≤ 30, valores[] ≥ 0, formato\|null}`, `linea{nombre ≤ 30, valores[], formato\|null, desdeCero}`, `destacar` (periodo; −1 = último), `rotular: null\|"todas"\|"destacada"` | Barras en tinta desde cero (eje izq.), línea en `a1` (eje der.); títulos de eje con nombre y unidad; valores rotulados sin solape; escribe «Dos escalas: …» con el origen del eje derecho. |
| `linea-tiempo` | `eventos[3–8]{fecha (empieza por AAAA), nombre ≤ 40, valor ≥ 0, sub?, valor_texto?}`, `proporcional: false\|true`, `forma: "barra"\|"circulo"\|"ninguna"`, `destacar` | Filas de arriba abajo (fecha · nombre · magnitud desde cero); con `proporcional: true` separa por fecha y falla si dos hitos quedan a < 52 px; escribe «Intervalos (no) proporcionales al tiempo.». `ninguna` para escalas no lineales (Richter en `valor_texto`). |
| `agrupadas` | `etiquetas[2–6]`, `series[2–3]{nombre, valores[] ≥ 0, destacar?}` (si ninguna, la última), `rotular: "todas"\|"destacada"`, `referencia:{valor, texto}\|null` | Horizontales desde cero; la serie destacada en `a1`, las otras en tinta y tinta al 50 %; valores al final de cada barra; referencia vertical punteada (promedio nacional, meta). |
| `pictograma` | `total` (entero 2–200), `destacado` (entero 0–total), `texto` (≤ 60), `etiqueta_destacado`, `etiqueta_resto`, `forma: "punto"\|"cuadro"\|"persona"`, `por_fila: null\|2–25` | Una forma por unidad (CSS, sin emoji); K en `a1`; el «K de N …» lo **compone** la plantilla; columnas automáticas (filas completas, múltiplos de 5); falla si la celda baja de 18 px («usa waffle»). |
| `area-apilada` | `etiquetasX[5–30]`, `partes[2–5]{nombre, valores[] ≥ 0}` (partes[0] abajo), `normalizar` (true), `destacar` (índice de parte) | Bandas 100 % (o absolutos con eje); % al inicio y nombre + % al fin de cada banda con anti-solape y guías; destacada en `a1`; avisa si el redondeo no suma 100. |
| `cascada` | `inicio:{nombre, valor}\|null`, `pasos[2–8]{nombre, valor ≥ 0, efecto: "suma"\|"resta"}`, `fin:{nombre, valor?}\|null` (al menos uno de inicio/fin), `destacar: "inicio"\|"fin"\|índice\|null` | Filas horizontales con eje cero; **calcula** acumulados y el fin; si `fin.valor` va (la cifra oficial, verificada), coteja su magnitud con lo calculado y falla si no cuadra; sin `fin.valor` escribe «<fin> calculado desde los pasos.»; rótulos con signo fuera del extremo móvil, nunca sobre el eje. |

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
   `barras-h`; `combinado` no sugiere causa (dos escalas no son una relación)
   y declara el origen del eje derecho; `linea-tiempo` declara si los
   intervalos son proporcionales; `cascada` cuadra con `fin.valor`;
   `multiples` comparte escala (una serie plana se ve plana: es el punto);
   `pictograma` con más de 100 unidades se vuelve textura (mejor `waffle`).
10. **Coherencia con el guion**: los números del PNG son los del `visual.datos`
   (el gate mecánico lo comprueba, pero mira que el redondeo no engañe).
