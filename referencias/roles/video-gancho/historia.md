# video-gancho · Modo historia (`/historia`)

> Parte de `referencias/roles/video-gancho.md` (léelo primero); aquí está solo lo de este modo.

Lo pide el Workflow `historia` con la cronología ya verificada. Insumo: `python3 scripts/historia.py digesto <TRABAJO>
--para gancho` (hechos con fecha y estado, cifras, frases literales, fotos verificadas con su crédito, familias de
historia y lo bloqueado por rotación), en lugar de `digesto.md`; lee también `referencias/ganchos.md` (R1–R14 valen
igual). Lo que cambia:

- **Familias de historia**: `resultado` (el final primero: «El químico que iba a salvar el lago era agua con sal»),
  `paradoja`, `contraste` (antes / después), `misterio` (lo que nadie sabía), `personaje` (una persona y un objeto
  concretos), `lugar`, `pregunta`, `escala`. El digesto dice qué visuales admite cada una.
- **Visual `foto`, siempre** (H7). Con el motor propio, la foto de la historia a sangre cubre toda la pantalla,
  oscurecida (estilo Noche: brillo 0.45–0.6, sombra del fondo arriba y abajo; `referencias/ganchos.md` §3), con
  `pantalla` en el chip y `linea` entera desde el cuadro 0, que se enciende en el acento cuando la voz la dice; en la
  mesa de archivo el cuadro 0 es otro (abajo, «Con la mesa de archivo»). `visual_datos:
  {"foto": "<id de foto verificada>", "etiqueta": "<lugar · año> (≤ 30)"}`. **La foto muestra al protagonista**
  (H12; el digesto marca PROTAGONISTA las que sirven): entre ellas, la más fuerte (el producto, la persona, el lugar).
  Cifra, pareja, llenado, figuras y lugar no abren una historia; una foto «de referencia» tampoco.
- **El gancho nombra al protagonista** (H10; `protagonista` del encuadre, en el digesto): la Incaparina, Pollo Campero,
  Yolanda Fernández. En la pantalla, la línea o la voz: quien desliza tiene que saber de qué historia se trata.
- **El gancho cuenta el momento de la historia, no su respuesta**: el problema que la hizo nacer, la persona, la
  decisión, lo que estaba en juego. Nunca adelanta lo que el video paga ni el detalle técnico que explica después (de
  qué está hecho, cómo funciona, cómo terminó): quien ve tiene que quedarse para saberlo. «La Incaparina llevaba más
  semilla de algodón que maíz» regala la respuesta; «En Guatemala, los niños morían al dejar el pecho. La Incaparina se
  inventó para salvarlos» abre la historia y nombra a su protagonista. El digesto lista las **revelaciones** del
  encuadre (R1, R2…): ninguna va en el gancho; H13 veta sus números y el crítico puntúa `reserva`.
- **Sin cifra obligatoria** (no hay R10): una historia puede abrir con el hecho. Pero cada número dicho tiene
  respaldo, cada **año** está en un hecho del digesto y R7 prohíbe «hoy / ahora» en el gancho de una historia.
- La voz no abre con «Esta es la historia de…», «Te cuento…», «En el año…»: abre con el momento más fuerte.
- Un hecho `en_disputa` no va al gancho.
- Gate: `python3 scripts/historia.py ganchos <TRABAJO> --check` (no el de `video.py`).

**Con la mesa de archivo** (2026-11-14; `referencias/flujo-mesa.md`, MV14). En /video, /sabias, /explica, /departamento y /congreso
(todos en mesa desde el 2026-11-14) el cuadro 0 es la `pantalla` (o la `linea`, si es larga) como golpe de arriba y
el visual ya puesto como pieza: `pareja` → barras a la misma escala, `llenado` o `figuras` → la cifra con su rótulo,
`lugar` → el mapa de los 22 con el departamento; en /congreso, la foto del pleno y la barra de votos frente al umbral
(el portal era del motor propio). Lo que escribes no cambia. `/historia` y `/serie` ya no abren con una
foto a sangre ni con un chip. El cuadro 0 son piezas **ya puestas** antes de que suene nada: la **foto del
protagonista sobre papel**, con su pie y su crédito; **su nombre en una nota**; y el **golpe de arriba** (≤ 6
palabras). Lo demás del gancho entra con la palabra que lo nombra. Lo que escribes no cambia de forma (`visual: foto`,
`visual_datos`, `pantalla`, `linea`, `voz`; el mismo gate), pero piensa el cuadro así:

- `pantalla` es la semilla del golpe de arriba: ≤ 6 palabras (mejor ≤ 21 caracteres, un renglón), sin la cifra ni el
  desenlace.
- La foto se ve entera, a tamaño de tarjeta y con su pie (2–5 palabras de lo que se ve): elige la que muestra al
  protagonista de modo reconocible, no una que solo funcionaba oscurecida y a pantalla completa. `etiqueta` (lugar ·
  año) ya no es un chip: sirve de pie.
- La voz nombra al protagonista con las palabras de la nota (su nombre tal como va en `protagonista`).
- Cada cosa que la voz nombra después (un lugar, un año, una cifra con respaldo) puede entrar como pieza: una por
  oración, no tres en la misma.
