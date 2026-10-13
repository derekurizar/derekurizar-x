# investigacion/ · informes de investigación

Plantillas de **documento largo** con el sistema visual de las tarjetas: la misma tipografía
(Instrument Serif, Archivo, JetBrains Mono), las ocho paletas de `design/tokens.json` y la
anatomía kicker → titular → gráfico → «Fuente:» + handle, llevadas a páginas Letter.
Son la base de la futura función de investigación: un flujo que, en vez de solo tarjetas,
entregue un informe en PDF.

Diseño de referencia: lienzo «Informe de investigación» (claude.ai, artefacto
`W7cJpZrUxaMFZHwnDmPVhH`), 21 páginas y la hoja de sistema.

```bash
make informe-ejemplo                         # construye ejemplos/dengue-2026 (21 páginas)
make informe DIR=<carpeta con informe.json>  # PAL=<paleta> para probar otra paleta
python3 scripts/informe.py <dir> [--salida D] [--paleta X] [--check] [--sin-pdf] [--png DIR]
```

## Qué hay aquí

| Ruta | Qué es |
|---|---|
| `base.html` | La hoja: `@page` Letter (y `apaisada`), `.pagina` 816×1056, CSS de todas las piezas, arranque que marca `body[data-listo]` |
| `paginas/_comun.js` | `C(R, P)`: encabezado corrido, pie con número y handle, bloques, figuras y tablas |
| `paginas/aperturas.js` | `portada`, `capitulo` (variantes `banda` · `dividida` · `destacado`), `contraportada` |
| `paginas/lectura.js` | `cuerpo`, `anexo`, `apaisada`, `cronologia` |
| `paginas/sintesis.js` | `indice` (automático), `resumen`, `tablero`, `conclusiones` |
| `paginas/anexos.js` | `metodo` (cifras desde `datos.json`), `glosario`, `tarjetas` (hoja de contacto del hilo) |
| `graficos/*.js` | Gráficos dibujados en el documento: `barras_v`, `barras_h`, `divergente`, `agrupadas`, `linea`, `chispa`, `cuadros`, `comparacion`, `mapa` |
| `ejemplos/dengue-2026/` | `informe.json` del hilo de dengue 2026 y su `salida/` (`informe.pdf`, `informe.html`, `figuras/`) |

`scripts/informe.py` ensambla todo en un solo `informe.html`:
- las paletas salen de los tokens;
- el bloque `H` sale de `templates/base.html`, entre `// H:INICIO` y `// H:FIN`;
- la geometría del mapa sale de `design/mapa_geometria.svg`.

Después, `scripts/render_informe.js` lo imprime a PDF. Nada se edita a mano en `salida/`.

## Reglas

- **`informe.json` es la fuente de verdad.** La numeración de páginas, figuras y tablas, el índice y las referencias se calculan solos: en el texto se escribe `{fig:id}`, `{Fig:id}`, `{fign:id}`, `{tabla:id}`, `{Tabla:id}` o `{pag:id}`.
- **Ninguna cifra no confirmada.** Toda cifra o serie con `id` se cruza con los `datos.json` de `meta.datos` (gate I2).
- **Papel y tinta fijos** (`#F6F2E8` y `#0C1520`); el acento sale de la paleta (`papel_tinta`, `papel_barra`). Portada, aperturas, destacado y contraportada van a sangre con el `bg/ink/a1` de la tarjeta.
- **Tipografía y medida:** piso de 12 px, una columna de texto de ≤ 560 px y margen de 72 px.
- **Cero peticiones externas:** las fuentes se copian a `salida/fonts/`.

Contrato completo, tipos de página y de bloque, y gates: `referencias/diseno/informe.md`.
