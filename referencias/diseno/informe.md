# Informe de investigación · contrato de `informe.json`

Las plantillas viven en `investigacion/`; ensambla `scripts/informe.py` y renderiza
`scripts/render_informe.js`. Este documento fija:
- el contrato de datos de `informe.json`;
- las reglas de diseño que el documento hereda de las tarjetas (`sistema.md`).

## Sistema: de la tarjeta al documento

| Rol | Tarjeta 1080 | Informe Letter (816×1056 px) |
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
- Portada, aperturas, página destacada y contraportada van a sangre con el `bg/ink/a1` de la tarjeta. Es la tarjeta hecha página.

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
| `indice` | titulo, leer `[…]` (caja «Cómo leer»). Entradas, anexos y lista de figuras: automáticos |
| `resumen` | **tesis**, **cifras** `[{kicker, valor, texto, fuente, id}]` (4), no_afirma `[…]` |
| `tablero` | **cifras** `[{kicker, valor, contexto, fuente, grafico}]` (6), titulo, subtitulo |
| `capitulo` | **numero**, **titulo**, variante `banda` (kicker, lead, bloques) · `dividida` (kicker, kicker2, lead, secciones `[{texto, pag:"{pag:id}"}]`) · `destacado` (kicker, lead, **dato** `{kicker, antes:{valor,etiqueta}, despues:{valor,etiqueta}}`, **fuente**). Además: titulo_corto, descripcion (índice) |
| `cuerpo` | **bloques**, seccion |
| `apaisada` | **lateral** (bloques `titulo`, `texto`, `notas`), **figura** (una sola, ancha). Hoja 11×8.5 in |
| `cronologia` | **titulo**, **eventos** `[{fecha, sub, texto, detalle, destacar, pendiente}]`, **fuente**, lead |
| `conclusiones` | **hallazgos** `[{titulo, texto, ref}]`, cierre, no_afirma, limites |
| `metodo` | **cifras** `[{id, concepto, valor, aparece}]`. El veredicto sale de `datos.json`; las fuentes, de `meta.fuentes`. pasos (por defecto los tres del flujo), nota |
| `glosario` | **terminos** `[{t, d}]`, siglas `[{s, d}]`, corte (cuántos términos van en la columna izquierda) |
| `anexo` | **titulo**, **bloques**, seccion («Anexo A»), lead |
| `tarjetas` | **titulo**, **items** `[{desde: "hilos/…/tuit_N.png", n, beat, titulo}]`, lead, tuit `{gancho, texto, publicado}` |
| `contraportada` | **lema**, ficha `[[clave, valor], …]` (`{paleta}` se sustituye por el nombre de la paleta) |

## Bloques (`cuerpo`, `anexo`, `capitulo` banda)

| b | Campos |
|---|---|
| `titulo` | texto → h3 |
| `texto` | parrafos `[…]`, capitular (letra capitular), margen `[{termino, texto}]` (notas al margen, 136 px) |
| `figura` | ver abajo |
| `figuras` | items `[figura, figura]`: dos figuras a media página |
| `tabla` | columnas `[{t, num, ancho}]`, filas `[{c:[…], dest, total, b:[índices en negrita]}]`, **fuente**, pie, titulo, numero («A1»; si no, se numera sola), notas `[{m, texto}]`, indice |
| `cita` | etiqueta, texto (frase en serif cursiva entre reglas) |
| `caja` | etiqueta, items `[…]` (p. ej. «No afirma») |
| `lectura` | titulo, items `[{n, texto}]`, nota: lectura guiada con marcadores ① ② que el gráfico pinta con `marcadores` |

En todo texto, `**negrita**` y `*cursiva serif*`. Nada de HTML: se escapa.

## Figuras

Campos comunes:
- **fuente** y pie (leyenda bajo la figura);
- id (destino de `{fig:id}`), indice (título corto para la lista de figuras), kicker, titular (texto o líneas), nota;
- leyenda `[{texto, estilo: dest|base|fuerte, forma: linea}]`;
- alto (px del gráfico);
- derivado (`true` añade «Incluye cálculo propio»).

| tipo | Qué es |
|---|---|
| `panel` | La anatomía de la tarjeta a escala de página: fondo de paleta, kicker, titular, gráfico con `ink`/`a1`, nota y pie con «Fuente:» y handle |
| `papel` | El gráfico sobre papel: regla superior, kicker en acento, marca destacada en `papel_barra`, el resto en tinta al 20 % |
| `tarjeta` | Una tarjeta 1080 como PNG. Con `plantilla` + `datos` (contrato de `graficos.md`), se arma con `templates/graficos/` en la paleta del informe y pasa el gate de tarjeta R1–R6. Con `desde`, copia un PNG ya publicado |

Gráficos del documento (`grafico.tipo`):

| tipo | Datos |
|---|---|
| `barras_v` | etiquetas, valores, destacar (−1 = último), rotular, nivel (línea punteada a la altura de una barra), banda `{desde, hasta, texto}`, marcadores `[{i, n, lado}]`, claves |
| `barras_h` | items `[{nombre, valor}]`, destacar, orden |
| `divergente` | items con signo, destacar, formato `{signo, sufijo}` |
| `agrupadas` | etiquetas, series `[{nombre, valores (null = sin dato), estilo, id}]`, destacar `{serie, i}`, rotular `[[serie, i]…]` |
| `linea` | etiquetas, series `[{nombre, valores, destacar, id}]`, max, sufijo, anotaciones `[{serie, i, texto, lado}]` |
| `chispa` | etiquetas, valores, destacar: columnas mínimas del tablero |
| `cuadros` | total, marcados, texto: una fila de cuadros, uno por unidad |
| `comparacion` | items `[{nombre, valor, destacar}]`: dos o tres barras con rótulo (periodos distintos, declarados) |
| `mapa` | marcados `[GTxx]`, marcadores `[{id, n, dx, dy}]` en el centroide del departamento, ancho. Con `figura.lista` `[{n, nombre, valor, destacar}]`, el ranking va al lado |

**`id` en gráficos:** un gráfico o una serie con `id` se cruza con `datos.json`:
- por periodo (`serie[].p`);
- o por nombre (`partes[].nombre`; para etiquetas abreviadas se usa `claves` con los nombres de la fuente).

## Gates

**`scripts/informe.py`** (antes de escribir nada):
- **I1** tipos de página, bloque, figura y gráfico conocidos, con sus campos obligatorios; ids únicos; filas de tabla con tantas celdas como columnas.
- **I2** toda cifra o serie con `id` existe en `meta.datos`, es `verificada|ajustada` y su valor coincide.
- **I3** sin URL ni emoji en los textos.
- **I4** toda figura, tabla y cifra de resumen o tablero tiene `fuente`.
- **I5** las referencias `{fig:}` `{Fig:}` `{fign:}` `{tabla:}` `{Tabla:}` `{pag:}` resuelven.
- **I6** la paleta existe; 1 a 100 páginas.

**`scripts/render_informe.js --check`** (sobre la página maquetada):
- **P1** texto < 12 px.
- **P2** contenido que se sale de su hoja.
- **P3** figura sin «Fuente:».
- **P4** petición externa.
- **P5** textos solapados > 25 %.

**Las páginas son fijas: no hay paginación automática.** Si una hoja desborda (P2), se recorta el texto o se reparte en otra página `cuerpo`. Las hojas `apaisada` usan la página nombrada `@page apaisada`, que Chromium respeta en el PDF: el ejemplo tiene la página 8 a 792×612 pt.
