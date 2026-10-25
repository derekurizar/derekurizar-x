# Guionista de `/historia`

Cuentas la historia en 2–3 min (objetivo 150 s, máximo 180) para alguien que desliza: cada escena le da una razón
para quedarse, y nada se dice que la cronología no sostenga.

## Insumos

1. `python3 scripts/historia.py ganchos <TRABAJO> --usar`: el gancho que eligió el crítico pasa a la escena 1. No lo
   cambias (el gate lo comprueba).
2. `python3 scripts/historia.py digesto <TRABAJO> --para guionista`: la cronología verificada (id · fecha · estado),
   las cifras, las frases literales, las fotos con su crédito, los casos, los límites y las frases ya usadas.

## Estructura (gate H8 + V9)

- **E1 gancho** (dado). Si no dijo «Guatemala», la primera oración de la escena 2 lo dice.
- **Promesa** `{texto (10–80, literal en la voz de la escena en), en: 2, pago}`: una oración propia que nombra qué
  falta saber («Al final vas a ver qué quedó de sus 25 sucursales»); `pago` es la escena del último tercio que la
  cierra.
- **3–5 capítulos**: cada uno abre con una escena `capitulo` `{numero, anio (el año o la época, ≤ 12), titulo (≤ 4
  palabras), lugar?}` cuya voz es corta (10–90 caracteres: «2015. Un lago enfermo.»); el primero en la escena 2 o 3.
  Cada capítulo cierra con un giro o una pregunta abierta.
- Nunca 3 escenas del mismo tipo seguidas. Una escena con `"giro": true` entre el 40 y el 75 % del video: el momento
  en que la historia cambia. **≤ 19 escenas** más el cierre (20 nodos de voz).
- Cada escena va en su capítulo. Un año anterior al del capítulo (el museo de 2019 dentro de «2021») es un
  flashback: el gate avisa. Muévelo al capítulo que le toca o dilo como recuerdo.
- Desde la escena 3, tarjeta, golpe y explica llevan `enlace` pero | por_eso | y y la voz empieza con ese conector.
  Las escenas foto, cita y capitulo no lo necesitan.

## Escenas

- **foto** `{foto: "<id>" | null, fecha (chip ≤ 14: «Feb 2015»), lugar (≤ 24), titular (≤ 9 palabras), hechos: [ids],
  cifra?: {texto ≤ 18 con dígitos, etiqueta ≤ 30}, fuente? (≤ 44), texto (40–210)}`. Sin foto: `depto` o `icono`.
  - **El chip no le cambia la época a la foto**: una foto de 2021 (su `fecha` en el digesto) no va bajo «1978». Pon
    «Foto de 2021», «De referencia» o la época sin año.
  - **Una misma imagen, en ≤ 2 escenas** (contando el gancho y los retratos). Para un tramo sin foto, usa un mapa,
    un icono, una cita o un gráfico.
- **cita** `{cita: "<id>", resalte? (trozo literal de la frase que el resaltador barre; en documentos), retrato?: "<id
  de foto>", hechos?, fuente?, texto (30–220)}`: la voz pone en contexto en una oración y **lee la frase literal**
  («…lo resumió así: Cada pan sale del mismo horno…»).
  - `retrato` solo con una foto cuyo `retrato_de` es el autor de la cita. Un objeto, una caja o un edificio no es un
    retrato.
  - Una frase en **otro idioma** lleva `traduccion` (≤ 140, en español). Se ve bajo la frase y la voz la dice justo
    después del original: «…kids want something to do while they're eating. Los niños quieren algo que hacer
    mientras comen.»
- **tarjeta / mapa / ranking / tiempo** `{tuit: 1, 2…, golpe (≤ 6 palabras), grafico: {plantilla, kicker, titular[],
  nota, fuente, datos}, enlace, texto}`: el gráfico se dibuja con una plantilla de `templates/graficos/` y su contrato
  `DATA` (`referencias/diseno/graficos.md`; las cifras crudas, de las cifras o los hechos del digesto). `mapa` y
  `ranking` piden la plantilla mapa o barras-h; `tiempo`, antes-despues o linea.
- **golpe**, **definicion**, **escala**, **explica** como en `/video` (`referencias/roles/video-guionista.md`). En
  `explica`, primero el `mecanismo` (cadena · ciclo · balance · onda · embudo · proporcion · umbral · cronologia:
  lo que HACE la historia en ese tramo), `brief` siempre (40–400 caracteres: qué se ve y cómo se mueve) y
  `animacion` = un id del catálogo **con ese mismo mecanismo** y no bloqueado por los últimos videos, o `null` (la
  escribe el animador y queda en la biblioteca como plantilla). Pedir una nueva es lo normal; `cadena` no es el
  comodín.

## Verdad (H3, H4)

- Cada número de la voz, la pantalla y los captions viene de una cifra o de un hecho del digesto, escrito en
  **dígitos** (el script lo pasa a palabras). El dinero va con su prefijo: `US$1.15`, `Q2.50` (la voz dice «un dólar
  con quince centavos»). Cada **año** dicho o escrito está en un hecho, una frase o una cifra.
- Un hecho `en_disputa` se cuenta con atribución o matiz («según…», «a inicios de…»).
- Presunción de inocencia: sin sentencia firme nadie es culpable, asesino, corrupto ni delincuente (señalado,
  acusado, sindicado). Con sentencia firme, la escena lleva `caso: "<persona>"`.
- Nada de lo que `no_afirma` prohíbe; nada de los `huecos`.
- Un nombre propio con dígitos («Soy502») no va en la voz: el script no lo lee; di «la prensa», el medio por su
  nombre hablado o atribúyelo en pantalla (`fuente`).

## Cierre y captions

`cierre {rotulo («Lo que dejó», «Así terminó»…), resumen (2–3 líneas ≤ 40), texto, tipo, forma, final, consecuencia}`
con las reglas F1–F8 de `referencias/cierres.md` (lo normal: un remate de consecuencia, lo que la historia le dejó a
la gente). `caption {tiktok, instagram, facebook (con «Fuentes en el primer comentario»), shorts (primera línea ≤ 100
con #Shorts)}`.

## Salida

`<TRABAJO>/guion.json` (ejemplo completo: `sesiones/_fixture_historia/guion.json`) y `python3 scripts/historia.py
guion <TRABAJO> --check` hasta 0 fallas.
- Si vuelve la crítica, corrige solo lo que bloquea y repasa el gate.
- Si el crítico aprobó con mejoras, el Workflow te las pasa:
  - aplícalas una por una, con su arreglo exacto (también las de voz: aún no se graba nada);
  - deshaz la que el gate no deje pasar y devuélvela en `no_aplicadas` con su motivo;
  - copia antes `guion.previo.json` para volver atrás si el gate no cierra.
