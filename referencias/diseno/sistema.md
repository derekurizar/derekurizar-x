# Sistema visual «Hilos» (@DerekUrizar)

Referencia viva del brief `referencias/diseno/brief/Graficos Guatemala.dc.html`
(no se edita; se abre en el navegador para ver las 20+ opciones). Fuente de
verdad ejecutable: `design/tokens.json` → `templates/base.html`.

## Tarjeta

- **Lienzo** 1080×1080 px CSS, exportado a 2160×2160 (`deviceScaleFactor: 2`).
- **Padding** 76 px arriba/abajo · 80 px a los lados → **ancho útil 920 px**.
- Columna flex: kicker → titular → (leyenda) → **gráfico con `margin-top:auto`**
  (se pega al pie y deja aire arriba, como en el brief) → (nota) → pie.
- Un solo `<svg>` por tarjeta, `viewBox` 1:1 con los px CSS (así `font-size`
  en el SVG son px reales). Los gráficos sin geometría (cifra, antes-después,
  dona, waffle) son HTML/CSS puro.

## Tipografía (Google Fonts, OFL, servidas en local desde `design/fonts/`)

| Bloque | CSS | Límite |
|---|---|---|
| Kicker | `500 20px/1 'JetBrains Mono'; letter-spacing:.16em; uppercase` | ≤ 45 caracteres · «TEMA · UNIDAD» |
| Titular `h1` | `400 88px/.98 'Instrument Serif'; letter-spacing:-.015em` | 1–3 líneas · ≤ 26 caracteres por línea · la base mide el ancho real y falla si excede 920 px |
| Lead (opcional) | `400 27px/1.45 Archivo` | ≤ 2 líneas |
| Leyenda | swatch 36×6 (línea) · 22×22 (cuadro/punto) + `600 24px Archivo` | ≤ 4 items |
| Ejes | `500 17px 'JetBrains Mono'` | piso tipográfico 17 px (R1) |
| Valores | `700 22px 'JetBrains Mono'` (destacado 24) | |
| Categorías | `600 23px Archivo` (destacada `800 26px`) | |
| Cifras grandes | Instrument Serif 400: 120 px (antes/después), 132 (waffle), 200–220 (cifra) | auto-ajuste si no cabe |
| Nota | `500 18px/1.4 'JetBrains Mono'` | ≤ 150 caracteres |
| Pie | `Fuente: …` `400 18px 'JetBrains Mono'` · badge «X» 34×34 radius 8 · `@DerekUrizar` `600 21px Archivo` | fuente 1–70 caracteres, sin el prefijo «Fuente:» |

Sin emoji dentro del PNG (tofu en headless). La flecha → se dibuja con CSS; las
flechas ▲▼ y el signo × sí están en el subconjunto latino.

## Paletas (brief 6a) — una por hilo

El **fondo identifica el tema**; dentro del gráfico solo la **tinta** y **un
acento**. El dato que importa va en `a1`; el resto atenuado (tinta a opacidad
.45–.88 o `a2`/`a3`).

| paleta | bg | ink | a1 | a2 | a3 | Temas |
|---|---|---|---|---|---|---|
| `cielo` | #4B92DB | #0C1520 | #F6F2E8 | #2B4A66 | #8FB8E6 | economía · energía/combustibles · precios · población · remesas · empleo · inflación · nacional |
| `jade` | #1E6B5C | #F6F2E8 | #9FD4BF | #0E3B32 | #5FA38C | ambiente · bosques · agua · biodiversidad |
| `maiz` | #E0A33C | #1A1208 | #F3D08A | #B97A1C | #6E440B | agricultura · alimentos · clima · lluvias · canasta básica |
| `terracota` | #B23A26 | #F6F2E8 | #3A0F08 | #E8836F | #F2C2B6 | salud · seguridad · violencia · pobreza · desnutrición |
| `cacao` | #4A2F22 | #F6F2E8 | #D9A66B | #A8744A | #7A5038 | comercio · exportaciones · café · industria |
| `jacaranda` | #6B4E96 | #F6F2E8 | #1F1530 | #B9A3DB | #8E73B8 | sociedad · educación · cultura · idiomas |
| `atitlan` | #3FA3A0 | #0C1520 | #F6F2E8 | #7CC3C0 | #1D5E5C | turismo · transporte · infraestructura |
| `obsidiana` | #16181D | #F6F2E8 | #F08A4B | #8C8F96 | #3A3D44 | riesgo · sismos · volcanes · política · elecciones · justicia |

Contraste: `ink/bg` ≥ 4.5:1 en las ocho (`make validate` lo comprueba). `a1/bg`
queda entre 1.5 y 3:1 en varias paletas: **`a1` solo en cifras grandes, barras y
líneas, nunca en texto pequeño**. En `obsidiana` el kicker va en `a1` (brief 7a).

Asignación de colores por rol (linea/pendiente/dona): destacada → `a1`; las
demás → `ink`, `a2`, `a3` en ese orden.

## Reglas del brief (verbatim)

- «Regla: el fondo identifica el tema; dentro del gráfico solo la tinta y un
  acento. El dato que importa va en el color de mayor contraste, el resto
  atenuado.»
- «Siempre: sin 3D · barras desde cero · fuente visible · rotular directo en
  lugar de leyendas cuando se pueda.»
- «Primero la pregunta, luego el gráfico» (tabla en `graficos.md`).
- Escalas que no parten de cero se declaran en la tarjeta («eje desde N»).
- Redondeos y periodos van en la `nota` (p. ej. «Promedio mensual», «Porcentajes
  redondeados al entero»).

## Lo que hace la base automáticamente (`templates/base.html`)

1. Carga las fuentes (`H.fuentesListas`) antes de medir nada.
2. `H.cabecera(DATA)`: kicker, titular (líneas unidas con `<br>`), leyenda,
   nota, «Fuente: …», handle. Valida que no haya URLs en la tarjeta.
3. `render(DATA)` de la plantilla: dibuja el gráfico en `#grafico` con
   `H.espacio(max, min)` para no invadir el pie.
4. `H.verificar(DATA)`: cada línea del titular cabe en 920 px; `#grafico` ≥ 200
   px y con hijos; el pie no desborda 1080 px.
5. Marca `body[data-listo]`. Si algo lanza, deja `body[data-error]` y el render
   falla (nunca sale un PNG a medias que «pase» el QA).

## Gate de render (`make visual FILE=…` → `scripts/render.js --check`)

- Cero peticiones externas (solo `fonts/*.woff2`, servidas desde `design/fonts/`).
- `pageerror` fatal · espera `body[data-listo]` · comprueba `document.fonts.check`
  de las tres familias.
- **R1** texto < 17 px reales · **R2** algo fuera del lienzo · **R3** textos
  solapados > 25 % · **R4** `<svg>` a 300×150 o más de un svg · **R5** pie sin
  «Fuente:» · **R6** `#grafico` vacío o < 200 px.
