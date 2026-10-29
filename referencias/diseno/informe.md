# Informe de investigación · contrato de `informe.json`

Las plantillas viven en `investigacion/`; ensambla `scripts/informe.py` y renderiza
`scripts/render_informe.js`. Este documento fija:
- el contrato de datos de `informe.json`;
- las reglas de diseño que el documento hereda de las tarjetas (`sistema.md`).

## Sistema: de la tarjeta al documento

**El informe se queda en el estilo clásico** (`sistema.md`, apéndice «Estilo clásico»): papel, paletas planas e
Instrument Serif. Las tarjetas y los videos pasaron a Noche; el informe no, y las tarjetas de su hilo tampoco
(`materializar.py` las arma clásicas con `guion.modo = "investigacion"`). `informe.py` arma clásicas sus figuras
`tarjeta` y rearma clásica cualquier tarjeta Noche que copie (`desde`, `tarjetas`/`desde_hilo` sobre un `/hilo`
entregado): el documento nunca mezcla un fondo casi negro con el papel.

| Rol | Tarjeta 1080 (clásica) | Informe Letter (816×1056 px) |
|---|---|---|
| Kicker | 20 px Mono 500, .16em | 12 px Mono 500, .16em, mayúsculas, en `papel_tinta` |
| Titular | 88 px Instrument Serif | portada 104 · h1 72 · h2 56 · apertura 80 · h3 36 |
| Lead | 27 px Archivo | 17–19 px Archivo, 1.5 |
| Cuerpo | — | 16 px Archivo, 1.62, medida ≤ 560 px |
| Cifra grande | 120–220 px serif | portada 228 · destacado 200 · resumen 64 · tablero 48 |
| Nota y fuente | 18 px Mono | 12 px Mono (piso del documento) |
| Pie | Fuente + badge X + handle | encabezado corrido + pie con «Informe N.º · fecha», número y handle |

**Color:**
- Las páginas de lectura van sobre papel `#F6F2E8` con tinta `#0C1520`.
- El acento solo aparece en kickers, cifras, la marca destacada y los rótulos de figura:
  - `papel_tinta` para texto (≥ 4.5:1 sobre papel, lo comprueba `validate.py`);
  - `papel_barra` para marcas.
- Portada, aperturas, página destacada y contraportada van a sangre con el `bg/ink/a1` de la tarjeta clásica. Es la tarjeta hecha página.

**Márgenes y numeración:**
- Margen de 72 px a los lados; arriba 56 y abajo 48.
- Cada hoja lleva encabezado corrido, número y handle.
- Portada y contraportada no llevan número.

## Archivo

```jsonc
{
  "meta": {
    "titulo": "…", "corrido": "Tema · Informe de datos", "corto": "Tema",
    "pie": "Informe N.º 01 · Mes Año", "numero_largo": "Informe de datos · N.º 01", "fecha": "Mes Año",
    "handle": "@DerekUrizar", "paleta": "terracota",
    "numero": "01",                                 // N.º del informe (dos dígitos; memoria.py --informes da el siguiente)
    "datos": ["hilos/<carpeta>/datos.json"],       // contra estos se valida toda cifra con id
    "fuentes": ["Fuente 1 …", "Fuente 2 …"]        // la lista numerada de la página de método
  },
  "paginas": [ { "tipo": "portada", … }, … ]       // en orden; 1 a 100
}
```

**Campos comunes de página:**
- `id`: destino de `{pag:id}`.
- `seccion`: texto del encabezado derecho.
- `indice`: `{titulo, clase: "simple"|"anexo"}` la lleva al índice.
  - Las páginas `capitulo` entran solas, salvo que lleven `"indice": false`.
  - `clase: "anexo"` las agrupa en la franja inferior del índice.

## Tipos de página

| tipo | Campos (obligatorios en **negrita**) |
|---|---|
| `portada` | **titulo**, kicker_izq, kicker_der, lead, cifra `{valor, etiqueta, texto, id}`, fuentes. Los capítulos se listan solos |
| `indice` | titulo, leer `[…]` (caja «Cómo leer»). Entradas, anexos y lista de figuras: automáticos. Con más de 6 capítulos, los capítulos van a dos columnas sin descripción; con más de 6 capítulos o más de 24 figuras y tablas, la lista sigue en hojas «Figuras y tablas» insertadas tras el índice (≤ 40 entradas por hoja, repartidas parejo; cuentan como páginas) |
| `resumen` | **tesis**, **cifras** `[{kicker, valor, texto, fuente, id}]` (4), no_afirma `[…]` |
| `tablero` | **cifras** `[{kicker, valor, contexto, fuente, grafico}]` (6), titulo, subtitulo |
| `capitulo` | **numero**, **titulo**, variante `banda` (kicker, lead, bloques) · `dividida` (kicker, kicker2, lead, secciones `[{texto, pag:"{pag:id}"}]`) · `destacado` (kicker, lead, **dato** `{kicker, antes:{valor,etiqueta}, despues:{valor,etiqueta}}`, **fuente**). Además: titulo_corto, descripcion (índice) |
| `cuerpo` | **bloques**, seccion |
| `apaisada` | **lateral** (bloques `titulo`, `texto`, `notas`), **figura** (una sola, ancha). Hoja 11×8.5 in |
| `cronologia` | **titulo**, **eventos** `[{fecha, sub, texto, detalle, destacar, pendiente}]`, **fuente**, lead |
| `conclusiones` | **hallazgos** `[{titulo, texto, ref}]`, cierre, no_afirma, limites |
| `metodo` | **cifras** `[{id, concepto, valor, aparece}]`. El veredicto sale de `datos.json`; las fuentes, de `meta.fuentes`. pasos (por defecto los tres del flujo; `[]` los omite), `fuentes: false` omite la lista (segunda página), nota |
| `glosario` | **terminos** `[{t, d}]`, siglas `[{s, d}]`, corte (cuántos términos van en la columna izquierda) |
| `anexo` | **titulo**, **bloques**, seccion («Anexo A»), lead |
| `tarjetas` | **titulo**, **items** `[{desde: "hilos/…/tuit_N.png", n, beat, titulo, alt}]`, lead, tuit `{gancho, texto, publicado}`. Con `desde_hilo: "<carpeta del hilo>"` `informe.py` llena `items` y `tuit` desde su `hilo.json` (y el `DATA` de cada `tuit_N.html`); `tuits: [n…]` elige un subconjunto para partir en dos páginas; la caja `tuit` se omite sola con más de 8 tarjetas y más de 12 es I1. Una tarjeta Noche se imprime rearmada clásica |
| `contraportada` | **lema**, ficha `[[clave, valor], …]` (`{paleta}` se sustituye por el nombre de la paleta) |

## Bloques (`cuerpo`, `anexo`, `capitulo` banda)

| b | Campos |
|---|---|
| `titulo` | texto → h3 |
| `texto` | parrafos `[…]`, capitular (letra capitular), margen `[{termino, texto}]` (notas al margen, 136 px) |
| `figura` | ver abajo |
| `figuras` | items `[figura, figura]`: dos figuras a media página |
| `tabla` | columnas `[{t, num, ancho}]`, filas `[{c:[…], dest, total, b:[índices en negrita], detalle}]` (`detalle`: una segunda línea a lo ancho bajo la fila, sin la columna del id; la usan las fichas de auditoría para «qué encontramos»), **fuente**, pie, titulo, numero («A1»; si no, se numera sola), notas `[{m, texto}]`, indice |
| `cita` | etiqueta, texto (frase en serif cursiva entre reglas) |
| `caja` | etiqueta, items `[…]` (p. ej. «No afirma») |
| `lectura` | titulo, items `[{n, texto}]`, nota: lectura guiada con marcadores ① ② que el gráfico pinta con `marcadores` |

En todo texto, `**negrita**` y `*cursiva serif*`. Nada de HTML: se escapa.

## Figuras

Campos comunes:
- **fuente** y pie (leyenda bajo la figura);
- id (destino de `{fig:id}`), indice (título corto para la lista de figuras; `false` la deja fuera, p. ej. una tabla que continúa), kicker, titular (texto o líneas), nota;
- leyenda `[{texto, estilo: dest|base|fuerte, forma: linea}]`;
- alto (px del gráfico);
- derivado (`true` añade «Incluye cálculo propio»).

| tipo | Qué es |
|---|---|
| `panel` | La anatomía de la tarjeta a escala de página: fondo de paleta, kicker, titular, gráfico con `ink`/`a1`, nota y pie con «Fuente:» y handle |
| `papel` | El gráfico sobre papel: regla superior, kicker en acento, marca destacada en `papel_barra`, el resto en tinta al 20 % |
| `tarjeta` | Una tarjeta 1080 como PNG. Con `plantilla` + `datos` (contrato de `graficos.md`), se arma con `templates/graficos/` en la paleta del informe, pasa el gate de tarjeta R1–R6 y, con `cifra_ids`, I2 coteja sus números. Con `desde`, copia un PNG ya publicado; si es Noche, lo rearma clásico desde su `tuit_N.html` (plantilla, paleta y `DATA` de la cabecera) y repasa R1–R6 |

Gráficos del documento (`grafico.tipo`): **el mismo contrato que la tarjeta**. `tipo` admite el nombre de la
plantilla (`barras-v`) o su forma snake (`barras_v`); los campos y límites son los de `graficos.md`, con las
extensiones del documento como opcionales. Los tipos válidos son los `G.<tipo>` definidos en
`investigacion/graficos/*.js` (W7 los cruza con el catálogo de tarjetas); `make informe-catalogo` los
dibuja todos en papel, panel y media página. Campos obligatorios en negrita (I1, `CAMPOS_GRAFICO`).

| `G.` | plantilla | campos | extensiones del documento |
|---|---|---|---|
| `barras_v` | barras-v | **etiquetas**, **valores**, destacar (−1 = última), rotular, referencia `{valor, texto}`, periodos | nivel (línea punteada a la altura de esa barra), banda `{desde, hasta, texto}`, marcadores `[{i, n, lado}]`, claves |
| `barras_h` | barras-h | **items** `[{nombre, valor, valor_texto?}]`, destacar, orden | hasta 12 items |
| `divergente` | divergente | **items** con signo, orden, destacar, formato `{signo, sufijo}` | — |
| `agrupadas` | agrupadas | **etiquetas**, **series** `[{nombre, valores, destacar?}]` (barras horizontales), rotular, referencia | `series[].id` |
| `columnas` | — (solo doc.) | **etiquetas**, **series** `[{nombre, valores (null = sin dato), estilo}]` en columnas verticales, destacar `{serie, i}`, rotular `[[serie, i]…]` | `series[].id` |
| `bullet` | bullet | **items** `[{nombre, valor, meta?}]`, meta, texto_meta, maximo, destacar | — |
| `apilada` · `area_apilada` · `piramide` | apilada · area-apilada · piramide | como la tarjeta (`partes`, `etiquetasX`, `grupos`, `izquierda`/`derecha`…) | `partes[].id`, `izquierda.id`, `derecha.id` |
| `linea` | linea | **etiquetas** o **etiquetasX**, **series** `[{nombre, valores, destacar}]`, yDesdeCero (false exige `nota`), ejeY, valoresBajoEje, rotularFin, hitos, periodos | max, sufijo, anotaciones `[{serie, i, texto, lado}]`, `series[].id` |
| `multiples` · `combinado` | multiples · combinado | como la tarjeta | `paneles[].id`, `barras.id`, `linea.id` |
| `pendiente` · `pesas` · `antes_despues` · `cascada` | pendiente · pesas · antes-despues · cascada | como la tarjeta (`pesas` con desdeCero false exige `nota`) | `items[].id` |
| `cifra` · `waffle` · `pictograma` | cifra · waffle · pictograma | como la tarjeta (en SVG) | — |
| `dona` · `treemap` · `hemiciclo` · `embudo` | dona · treemap · hemiciclo · embudo | como la tarjeta | `partes[].id` |
| `dispersion` · `calor` · `linea_tiempo` | dispersion · calor · linea-tiempo | como la tarjeta | — |
| `mapa` | mapa | **valores** `{GTxx\|nombre: v}` (≥ 12), clases, cortes, metodo, redondear, destacar, rotular (coroplético) | marcados `[GTxx]` (sin `valores`: solo sombreado), marcadores `[{id, n, dx, dy}]` en el centroide, ancho (acota el dibujo; a toda columna mide 705 px). Con `figura.lista` `[{n, nombre, valor, destacar}]`, el ranking va al lado |
| `chispa` · `cuadros` · `comparacion` | — (solo tablero) | etiquetas, valores, destacar · total, marcados, texto · items `[{nombre, valor, destacar}]` | — |

Anchos reales: cuerpo papel 672 · cuerpo panel 612 · `figuras` 324 (papel) / 284 (panel compacto) · tablero 324
· apaisada 600. Alturas sin `alto`: `barras_h` 30·n, `divergente` 31·n, mini 64, `mapa` = ancho × 1.05 + 70.
A media página: `calor` ≤ 8 columnas, `dispersion` ≤ 2 rotulados, `hemiciclo` ≤ 160 curules, `multiples` ≤ 6
paneles. Cuándo `tarjeta`: la pieza ya existe publicada (`desde`) o se quiere mostrar la tarjeta como objeto;
`panel` para la figura tesis de la página (fondo de paleta); `papel` para todo lo demás.

**`id` en gráficos:** un gráfico o una serie con `id` se cruza con `datos.json`:
- por periodo (`serie[].p`);
- o por nombre (`partes[].nombre`; para etiquetas abreviadas se usa `claves` con los nombres de la fuente);
- y, para cualquier contrato, **todos los números de los datos** (según `ensamblar.CLAVES_DATO` de su
  plantilla) deben estar entre los valores de las cifras declaradas (`id`, `cifra_ids` de la figura o del
  gráfico, ids anidados en `series`, `partes`, `paneles`, `items`, `izquierda`/`derecha`, `barras`/`linea`).

## Gates

**`scripts/informe.py`** (antes de escribir nada):
- **I1** tipos de página, bloque, figura y gráfico conocidos, con sus campos obligatorios (por tipo de gráfico, `CAMPOS_GRAFICO`); ids únicos; filas de tabla con tantas celdas como columnas; `meta.numero` de dos dígitos; `desde_hilo` con `hilo.json`.
- **I2** toda cifra o serie con `id` existe en `meta.datos`, es `verificada|ajustada` y su valor coincide; en todo gráfico y toda figura `tarjeta` con datos, cada número está entre los valores de sus cifras.
- **I3** sin URL ni emoji en los textos.
- **I4** toda figura, tabla y cifra de resumen o tablero tiene `fuente`.
- **I5** las referencias `{fig:}` `{Fig:}` `{fign:}` `{tabla:}` `{Tabla:}` `{pag:}` resuelven (`{pag:id}` da la página de una página, una figura o una tabla con ese id).
- **I6** la paleta existe; 1 a 160 páginas (cada flujo pone su rango: 14–30 normal, 30–140 auditoría).
- **I7** (solo aviso) números del cuerpo (párrafos, leads, tesis, hallazgos, cierre) que no son una cifra verificada, un año, un entero ≤ 100 ni un derivado declarado en la misma página (un pie, nota o margen con ÷ × − o «cálculo propio»).

**`scripts/render_informe.js --check`** (sobre la página maquetada):
- **P1** texto < 12 px.
- **P2** contenido que se sale de su hoja.
- **P3** figura sin «Fuente:».
- **P4** petición externa.
- **P5** textos solapados > 25 %.

**Las páginas son fijas: no hay paginación automática.** Si una hoja desborda (P2), se recorta el texto o se reparte en otra página `cuerpo`. Las hojas `apaisada` usan la página nombrada `@page apaisada`, que Chromium respeta en el PDF: el ejemplo tiene la página 8 a 792×612 pt.
