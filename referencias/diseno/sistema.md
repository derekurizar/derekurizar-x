# Sistema visual «Hilos» (@DerekUrizar)

Dos estilos con la misma anatomía y los mismos roles de color:

- **Noche** — todas las tarjetas de X (`/hilo`, `/dato` y sus modos) y todos los videos (`/video`, `/noticias`,
  `/historia`): el color del tema llevado casi a negro, texto crema, un solo acento claro y Archivo condensado.
- **Clásico** — solo `/investigacion`: el informe en papel y las tarjetas de su hilo (son figuras del informe).
  Paletas planas e Instrument Serif; está en el apéndice.

Fuente de verdad ejecutable: `design/tokens.json` (bloque `noche`; `paletas` y `documento` para el clásico) →
`templates/base.html` (tarjeta) y `video/comun.css` + `scripts/video.py colores()` (video). Referencia del brief
original: `referencias/diseno/brief/Graficos Guatemala.dc.html` (no se edita; anatomía y reglas siguen valiendo).

## El interruptor

- `scripts/nuevo_visual.py <plantilla> <destino.html> --paleta P --estilo noche|clasico` (noche por defecto) pone
  `data-estilo` en el `<body>` y lo anota en la cabecera (`<!-- plantilla: … · paleta: … · estilo: … -->`).
  `--galeria` acepta el mismo `--estilo`.
- `scripts/materializar.py` lo elige solo: `clasico` si `guion.modo == "investigacion"`; `noche` en todo lo demás.
- `scripts/informe.py`: siempre clásico. Las figuras `plantilla` + `datos` se arman clásicas y una tarjeta copiada
  (`desde`, `tarjetas`/`desde_hilo`) que sea Noche (un `/hilo` entregado, `desde:<slug>`) se **rearma clásica** desde su
  `tuit_N.html` (plantilla, paleta y `DATA` de la cabecera) y repasa R1–R6.
- Video: `video.py colores()` emite siempre Noche; `preparar` rearma en Noche (`TRABAJO/tarjetas/`) las tarjetas de un
  hilo entregado antes de Noche, para que no lleguen con fondo plano al fondo oscuro del video.
- Nadie elige el estilo a mano en `guion.json` ni edita `data-estilo` en un HTML.

## Reglas Noche

1. **Fondo** = el color del tema llevado casi a negro (`noche.paletas.<p>.fondo`). El color plano del tema ya no es
   fondo: en Noche identifica el tema el tinte del fondo y el acento.
2. **Acento = una sola cosa** por tarjeta o escena: la cifra, el nombre o la palabra que suena. Si dos cosas compiten
   por el acento, una pasa a crema.
3. **Texto crema** (`noche.texto`). Lo ya dicho o lo que falta va al 26–55 %, **solo en tamaños grandes** (cifras,
   golpes, subtítulos, marcas); ejes, valores, nota y fuente nunca bajan de lo que pone la base.
4. **Fotos a sangre** (video), brillo 0.45–0.6, con una sombra del color del fondo arriba (bajo la barra) y abajo
   (bajo los subtítulos). Ya no hay foto en marco.
5. **Grano fijo**: ruido SVG en mosaico de 180 px sobre `var(--bg)` en el fondo del `body`. No depende de t ni del
   render: dos renders dan el mismo PNG y los cuadros de video salen iguales en serie y en paralelo; además ayuda a
   que los oscuros no se partan en bandas al comprimir.
6. **Tipos**: Archivo condensado 900 en mayúsculas para cifras, nombres, años y el golpe de arriba de las escenas de
   video; Archivo 800 para titulares de tarjeta y subtítulos; JetBrains Mono 600 para kicker, fuente y crédito. **Instrument Serif no entra** en tarjetas Noche ni en
   ninguna escena de video (sigue en el clásico).
7. **Sin subtítulo doble**: si la pantalla ya dice lo que dice la voz (golpe, cita, titular que se enciende), el
   subtítulo se calla.
8. **Zona segura sin cambios** (V13): lo que se lee va dentro de `V.zona()`; las capas a sangre (foto, velo, sombra)
   llevan `data-fuera-de-zona`.
9. **Colores solo por variables** (roles de abajo, `var(--…)` en video): ningún hex nuevo en plantillas, páginas de
   escena ni animaciones.

## Tarjeta

- **Lienzo** 1080×1080 px CSS, exportado a 2160×2160 (`deviceScaleFactor: 2`).
- **Padding** 76 px arriba/abajo · 80 px a los lados → **ancho útil 920 px**.
- Columna flex: kicker → titular → (leyenda) → **gráfico con `margin-top:auto`**
  (se pega al pie y deja aire arriba, como en el brief) → (nota) → pie.
- Un solo `<svg>` por tarjeta, `viewBox` 1:1 con los px CSS (así `font-size`
  en el SVG son px reales). Los gráficos sin geometría (cifra, antes-después,
  dona, waffle) son HTML/CSS puro.

## Color Noche (`design/tokens.json → noche`)

`fondo` = `bg` × 0.2 (obsidiana, ya casi negra, se queda; cacao, ya oscuro, × 0.4) · `fondo_acto2` = fondo × 0.5
(acto 2 de `/historia`) · `fondo_golpe` = fondo × 0.275 (el golpe que tiene que pesar) · `acento` = el tono claro del
tema, el que se distingue de los grises por luminancia y no solo por tono (en cielo y atitlán, el claro de la paleta) ·
`serie` = [acento, texto, texto atenuado, acento atenuado]. Comunes: `texto` **#F6F2E8** (crema) y
`tinta_sobre_acento` **#1A1208** (texto sobre una caja de acento).

| paleta | fondo | fondo_acto2 | fondo_golpe | acento | serie[2] | serie[3] | Temas |
|---|---|---|---|---|---|---|---|
| `cielo` | #0F1D2C | #080E16 | #04080C | #8FB8E6 | #8E9293 | #557292 | economía · energía/combustibles · precios · población · remesas · empleo · inflación · nacional |
| `jade` | #061512 | #030A09 | #020605 | #9FD4BF | #8A8F88 | #5A7E71 | ambiente · bosques · agua · biodiversidad |
| `maiz` | #2D210C | #161006 | #0C0903 | #E0A33C | #9C9485 | #916A27 | agricultura · alimentos · clima · lluvias · canasta básica |
| `terracota` | #240C08 | #120604 | #0A0302 | #E8836F | #988A83 | #985245 | salud · seguridad · violencia · pobreza · desnutrición |
| `cacao` | #1E130E | #0F0A07 | #080504 | #D9A66B | #958E86 | #856441 | comercio · exportaciones · café · industria |
| `jacaranda` | #15101E | #0A080F | #060408 | #B9A3DB | #918C8D | #6F6186 | sociedad · educación · cultura · idiomas |
| `atitlan` | #0D2120 | #061010 | #040909 | #7CC3C0 | #8D948E | #4A7A78 | turismo · transporte · infraestructura |
| `obsidiana` | #16181D | #0B0C0E | #060708 | #F08A4B | #91908D | #975B38 | riesgo · sismos · volcanes · política · elecciones · justicia |

**Roles**: en Noche los mismos roles cambian de valor; las plantillas no cambian de rol (lo que pintaban en `a1`
sigue en `a1`).

| rol | Noche | qué va |
|---|---|---|
| `--bg` | `fondo` | el fondo (con el grano encima) |
| `--ink` | `texto` (crema) | texto y marcas de base; `--ink-rgb` 246,242,232 para las opacidades |
| `--a1` | `acento` | **lo único** que destaca: la cifra, la barra, la serie o el departamento de la tesis |
| `--a2` | `serie[2]` (crema atenuado) | segunda serie, texto secundario |
| `--a3` | `serie[3]` (acento atenuado) | tercera serie y marcas; nunca texto pequeño |
| `--x-fg` | `fondo` | la «X» del badge del pie (el badge es crema) |

Asignación por rol: en `linea` y `dona` la destacada → `a1` y las demás → `ink`, `a2`, `a3` en ese orden (la quinta
parte de la dona, crema al 28 % en Noche; al 45 % en clásico); en Noche la línea destacada de `linea` va a 7 px y las
demás a 4.5 (`a1` y `a3` son el mismo tono). En `pendiente` la destacada → `a1` y, en Noche, las demás → `a2` con su
rótulo en crema (con `a3` repetido habría varios acentos). Las partes no destacadas de `apilada`, `area-apilada`,
`agrupadas` y `piramide` usan tonos de crema separados entre sí (≥ 1.35:1) y del acento (≥ 1.25:1); las de `treemap`,
tonos bajos de crema con texto crema encima (≥ 4.6:1); en `combinado` la barra clave va en el tono de crema más claro
que se aparta del acento (≥ 1.5:1) y las demás en uno bajo, nunca crema plena; en `bullet` y `embudo` lo no destacado
va en `a2`; en `dispersion` el rótulo y la guía del destacado van en `a1`; en `pesas` la barra que une los puntos va en
`a3` y el acento queda en los puntos de la fecha reciente. La crema plena es para texto y contornos, no para rellenos
grandes. La rampa (`H.rampa`: mapa, calor) va del fondo oscuro a la crema, con
el escalón más bajo a ≥ 2:1 del fondo en Noche (1.5:1 en clásico), y deja `a1` para el destacado. Texto sobre una caja de acento:
`H.textoSobre` en la tarjeta (elige la tinta oscura), `tinta_sobre_acento` en el video.

**Contraste medido** (tokens actuales, WCAG): texto/fondo ≥ **14.1:1** (maíz; hasta 16.7 en jade) · acento/fondo
≥ **7.0:1** (terracota; hasta 11.3 en jade) · `serie[2]` ≥ 5.2:1 · `serie[3]` ≥ 3.2:1 · tinta_sobre_acento/acento
≥ 7.0:1. Sobre `fondo_acto2` y `fondo_golpe` todo sube. `make validate` (M3) falla si texto o acento bajan de 4.5:1
o un color de la serie de 3:1 sobre `fondo` o `fondo_acto2`. Por eso en Noche el acento sí puede ir en texto (el
nombre, el año, la palabra que suena), a diferencia del `a1` clásico.

## Tipografía Noche (Google Fonts, OFL, servidas en local desde `design/fonts/`)

| Bloque | CSS | Límite |
|---|---|---|
| Kicker | `600 20px/1 'JetBrains Mono'; letter-spacing:.16em; uppercase`, crema al 85 % | ≤ 45 caracteres · «TEMA · UNIDAD» |
| Titular `h1` | `800 64px/1.04 Archivo; letter-spacing:-.01em` (margen 20 px) | 1–3 líneas · ≤ 26 caracteres por línea · la base mide el ancho real y falla si excede 920 px |
| Cifra protagonista | `.cifra-heroe`: Archivo 900, `font-stretch: 62.5%`, mayúsculas (la base pone familia, peso, ancho y caja; la plantilla, solo tamaño e interlínea) | auto-ajuste si no cabe |
| Lead · leyenda · ejes · valores · categorías · nota | como en el clásico (Archivo y JetBrains Mono, mismos tamaños; piso 17 px) | |
| Pie | `Fuente: …` `500 18px 'JetBrains Mono'`, crema al 80 % · badge «X» 34×34 crema · `@DerekUrizar` `600 21px Archivo` | fuente 1–70 caracteres, sin el prefijo «Fuente:» |

- **Archivo con eje de ancho**: `design/fonts/archivo-wdth.woff2` (variable, wdth 62–125 y wght 100–900), declarada con
  `font-stretch: 62% 125%` en `templates/base.html` y `video/comun.css`. Condensado = `font-stretch: 62.5%` en CSS y
  `ctx.fontStretch = "extra-condensed"` en el lienzo (el shorthand de `ctx.font` no admite porcentajes). **El shorthand
  `font:` resetea `font-stretch`**: escríbelo después del shorthand.
- **Medidas** (Chromium, 2026-10-28): una línea de 26 caracteres de texto corriente ocupa ≈ 810–910 px a 64 px
  («Guatemala alcanzó a México» = 906): cabe, pero justo; mayúsculas seguidas o cifras anchas no caben y la base falla.
  `titular_escala` (1–1.5) multiplica los 64 px. La cifra condensada a 220 px es ≈ 15 % más ancha que Instrument
  Serif al mismo tamaño («1,234,567» = 753 px): el auto-ajuste entra antes.
- **Helpers** (`templates/base.html`): `H.estilo()` («noche» | «clasico»), `H.fuenteCifra(px)` (la fuente de
  `.cifra-heroe` para el lienzo), `H.medirCifra(str, px)` (mide en mayúsculas y condensado en Noche) y
  `H.medir(str, font, ancho)` (`ancho` = keyword de `font-stretch`). Una plantilla que mide o dibuja la cifra en el
  lienzo usa estos, nunca una familia escrita a mano.

Sin emoji dentro del PNG (tofu en headless). La flecha → se dibuja con CSS; las
flechas ▲▼ y el signo × sí están en el subconjunto latino.

## Video (resumen; formato completo en `referencias/flujo-video.md`)

- `video.py colores(paleta)` → `escenas.json → colores`, que `V.cargar` vuelca como variables: `bg` (fondo), `ink`
  (crema), `a1`/`acento`/`grafico`/`pregunta` (el acento), `a2`/`a3` (serie atenuada), `resalte_bg` (acento) y
  `resalte_ink`/`tinta_acento` (#1A1208), `fondo_acto2`, `fondo_golpe`; `/noticias` y `/historia` suman `realce`
  (= acento: se lee sobre la foto oscurecida).
- `video/comun.css`: fondo `var(--bg)` con el mismo grano fijo · `.condensada` (Archivo 900, 62.5 %, mayúsculas) ·
  arriba, la barra de progreso primero y debajo el golpe como titular: Archivo condensado 900 en mayúsculas, 96 px (se
  achica hasta 60), crema, con UNA palabra en el acento (`V.acentoDe`: la primera con cifra; si no hay, la primera de
  cantidad, «menos», «más», «casi»…; un titular solo de cifras va entero en el acento; la pantalla del gancho sigue la
  misma regla) · subtítulos Archivo 800 60 px/1.24 con la palabra activa en una caja del acento con tinta oscura (una sola palabra a
  la vez; el trozo no termina en «el», «de», «y»…; si ≥ 60 % de sus palabras
  ya se leen en pantalla, no se muestra)
  (`--resalte-bg` / `--resalte-ink`) y las que faltan al 38 % · rótulo de acto con el año condensado en acento, el
  título en Archivo 800 66 px y el lugar en Mono 600 24 px.
- Barra de progreso por grupos (`V.pintarProgreso`): un tramo por escena en `/video`, por noticia en `/noticias` y por
  acto en `/historia`, de largo proporcional a su duración. En el acto 2 de `/historia`, `--bg` pasa a `fondo_acto2`.

## Reglas del brief (verbatim)

- «Regla: el fondo identifica el tema; dentro del gráfico solo la tinta y un
  acento. El dato que importa va en el color de mayor contraste, el resto
  atenuado.» (En Noche: el tinte del fondo y el acento identifican el tema; la
  tinta es la crema.)
- «Siempre: sin 3D · barras desde cero · fuente visible · rotular directo en
  lugar de leyendas cuando se pueda.»
- «Primero la pregunta, luego el gráfico» (tabla en `graficos.md`).
- Escalas que no parten de cero se declaran en la tarjeta («eje desde N»).
- Redondeos y periodos van en la `nota` (p. ej. «Promedio mensual», «Porcentajes
  redondeados al entero»).

## Lo que hace la base automáticamente (`templates/base.html`)

1. Carga las fuentes (`H.fuentesListas`, incluidas `800 64px Archivo` y la condensada) antes de medir nada.
2. `H.cabecera(DATA)`: kicker, titular (líneas unidas con `<br>`), leyenda,
   nota, «Fuente: …», handle. Valida que no haya URLs en la tarjeta.
3. `render(DATA)` de la plantilla: dibuja el gráfico en `#grafico` con
   `H.espacio(max, min)` para no invadir el pie.
4. `H.verificar(DATA)`: cada línea del titular cabe en 920 px medida con la fuente de su estilo (Archivo 800 64 en
   Noche, Instrument Serif 88 en clásico, por `titular_escala`); `#grafico` ≥ 200 px y con hijos; el pie no desborda
   1080 px.
5. Marca `body[data-listo]`. Si algo lanza, deja `body[data-error]` y el render
   falla (nunca sale un PNG a medias que «pase» el QA).

## Gate de render (`make visual FILE=…` → `scripts/render.js --check`)

- Cero peticiones externas (solo `fonts/*.woff2`, servidas desde `design/fonts/`).
- `pageerror` fatal · espera `body[data-listo]` · comprueba `document.fonts.check` de las tipografías de su estilo:
  Noche → `500 20px 'JetBrains Mono'`, `800 64px Archivo` y `extra-condensed 900 120px Archivo`; clásico →
  `400 88px 'Instrument Serif'`, `500 20px 'JetBrains Mono'` y `600 24px Archivo`.
- **R1** texto < 17 px reales · **R2** algo fuera del lienzo · **R3** textos
  solapados > 25 % · **R4** `<svg>` a 300×150 o más de un svg · **R5** pie sin
  «Fuente:» · **R6** `#grafico` vacío o < 200 px.
- Los checks Noche (fondo oscuro, una cosa en acento, texto crema, nada ilegible) son de juicio: los aplica el QA
  visual (`graficos.md`) y el gate de coherencia del productor sobre `contacto.png`.

## Apéndice · Estilo clásico (solo `/investigacion`)

El informe PDF y las tarjetas del hilo de `/investigacion` (`guion.modo = "investigacion"`) se quedan en el estilo
de siempre: `body` sin `data-estilo="noche"`, paletas planas de `design/tokens.json → paletas` e Instrument Serif. Las
tarjetas clásicas deben salir idénticas a como salían antes de Noche.

### Tipografía clásica

| Bloque | CSS | Límite |
|---|---|---|
| Kicker | `500 20px/1 'JetBrains Mono'; letter-spacing:.16em; uppercase` | ≤ 45 caracteres · «TEMA · UNIDAD» |
| Titular `h1` | `400 88px/.98 'Instrument Serif'; letter-spacing:-.015em` | 1–3 líneas · ≤ 26 caracteres por línea · la base mide el ancho real y falla si excede 920 px |
| Lead (opcional) | `400 27px/1.45 Archivo` | ≤ 2 líneas |
| Leyenda | swatch 36×6 (línea) · 22×22 (cuadro/punto) + `600 24px Archivo` | ≤ 4 items |
| Ejes | `500 17px 'JetBrains Mono'` | piso tipográfico 17 px (R1) |
| Valores | `700 22px 'JetBrains Mono'` (destacado 24) | |
| Categorías | `600 23px Archivo` (destacada `800 26px`) | |
| Cifras grandes | `.cifra-heroe` = Instrument Serif 400: 120 px (antes/después), 132 (waffle), 200–220 (cifra) | auto-ajuste si no cabe |
| Nota | `500 18px/1.4 'JetBrains Mono'` | ≤ 150 caracteres |
| Pie | `Fuente: …` `400 18px 'JetBrains Mono'` · badge «X» 34×34 radius 8 · `@DerekUrizar` `600 21px Archivo` | fuente 1–70 caracteres, sin el prefijo «Fuente:» |

### Paletas clásicas (brief 6a) — una por hilo

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
líneas, nunca en texto pequeño** (el aviso M3 de `validate.py` remite aquí). En `obsidiana` el kicker va en `a1`
(brief 7a; solo en clásico). El informe usa además `papel_tinta`/`papel_barra` y el bloque `documento`
(`referencias/diseno/informe.md`).

Asignación de colores por rol (linea/pendiente/dona): destacada → `a1`; las
demás → `ink`, `a2`, `a3` en ese orden.
