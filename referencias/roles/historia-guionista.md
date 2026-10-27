# Guionista de `/historia`

Cuentas la historia en 2–3 min (apunta a 150 s, entre 135 y 165: ≈ 320–400 palabras a 145 palabras por minuto; el
tope de 180 es para emergencias y el gate avisa si pasas de 165) para alguien que desliza: una sola voz que cuenta de
principio a fin, cada escena le da una razón para quedarse, y nada se dice que la cronología no sostenga.

## Insumos

1. `python3 scripts/historia.py ganchos <TRABAJO> --usar`: el gancho que eligió el crítico pasa a la escena 1. No lo
   cambias (el gate lo comprueba).
2. `python3 scripts/historia.py digesto <TRABAJO> --para guionista`: los actos y la espina del encuadre, los hilos,
   los personajes con su presentación, la cronología verificada (id · fecha · estado · tipo de hecho), las cifras,
   las frases literales, las fotos con su crédito, los casos, los límites y las frases ya usadas.

## Primero la narración (H15, H16)

Escribe primero el **texto corrido** de la historia, por acto, como lo diría una sola voz de principio a fin:
320–400 palabras (≈ 150 s). Léelo en voz alta antes de pensar en escenas: cada oración sigue de la anterior con un
**porque**, un **pero** o un **entonces**, nunca con un «y luego»; los saltos de tiempo se dicen («dos años después»,
«esa misma semana», «mientras tanto»); cada persona u organización se presenta la primera vez con una aposición de
≤ 8 palabras («Mario Baldetti, hermano de la vicepresidenta»); cada pregunta que abres la cierras o la declaras
(«nunca se supo si…»). Mídela con `python3 scripts/historia.py narracion <TRABAJO> --check`. Solo entonces repártela
en escenas: cada escena toma un tramo **sin cambiar una palabra** (H15) y decide qué se ve mientras se oye; agrupa
las escenas de un mismo tramo en `secuencias` (2–5) para que la voz se grabe de corrido. La imagen añade una capa;
la voz no describe lo que ya se ve.

- Va en `guion.narracion[3]` `{acto, texto}`: el acto 1 empieza con la voz del gancho tal cual y el acto 3 termina
  con `cierre.texto`. H15 compara, por acto, la narración con las voces de sus escenas (sin tildes ni signos) e
  imprime el primer punto donde divergen: si cambias una voz, cambia el mismo tramo de la narración.
- `narracion <TRABAJO>` imprime por acto las palabras, los segundos estimados, los conectores, cada «según» con su
  fuente, las primeras menciones de los personajes y los hilos; con `--check` falla con H16–H19.
- H16 pide ≥ 2 conectores causales o temporales por acto, a lo sumo una escena (desde la 2) que abra con atribución,
  que dos escenas seguidas no abran con las mismas dos palabras y ≤ 6.5 cortes por minuto.

## Estructura (gates H8, H17, H18, H20)

- **E1 gancho** (dado): siempre la foto a sangre del protagonista (H12). Si no dijo «Guatemala», la primera oración
  de la escena 2 lo dice. Lo que el gancho calla (las **revelaciones** del digesto: la respuesta, de qué está hecho,
  cómo terminó) es lo que el video revela después. El gancho es acto 1 (el gate se lo pone: `ganchos --usar` lo
  reescribe).
- **Promesa** `{texto (10–80, literal en la voz de la escena en), en: 2, pago, revela}`: una oración propia que nombra
  qué falta saber («Al final vas a ver qué quedó de sus 25 sucursales»); `pago` es la escena del último tercio que la
  cierra y `revela` es el número R de la revelación que esa escena cuenta **con sus palabras** (H14).
- **Tres actos** (`acto` 1–3 en cada escena, no decreciente, los tres presentes): el **planteamiento** presenta el
  mundo y al protagonista y termina en el **detonante**; el **nudo** sube la apuesta (el **punto medio** y el giro
  van aquí); el **desenlace** trae el **clímax** y la **resolución** (qué quedó, qué nunca se supo). Los actos y la
  espina vienen del encuadre (el digesto los lista): cuelga las escenas de esa espina y cierra cada acto en lo que
  hace querer el siguiente.
- **Rótulo de acto** `rotulo {anio (el año o la época, ≤ 12), titulo (≤ 4 palabras), lugar? (≤ 24)}` en la
  **primera escena de los actos 2 y 3** (opcional en la escena 2 para el acto 1): se dibuja sobre la imagen mientras
  la voz sigue. Lo admiten foto, cita, tarjeta, mapa, ranking, tiempo, golpe y explica; nunca gancho, adivina ni
  cierre. Una escena `capitulo` `{numero, anio, titulo, lugar?}` con voz propia (10–90: «2015. Un lago enfermo.») es
  la excepción: 0–2 y el gate avisa «prefiere rotulo».
- Una escena con `"giro": true` en el acto 2, entre el 40 y el 75 % del video: el momento en que la historia cambia.
  ≤ 3 escenas seguidas del mismo tipo. **≤ 19 escenas** más el cierre.
- **Secuencias** `secuencias: [[2, 3], [4, 5, 6], …]`: grupos de 2–5 escenas consecutivas del mismo acto, disjuntos,
  sin la escena 1 ni el cierre; un giro o un rótulo solo como primera de su secuencia. La voz de cada secuencia se
  graba de corrido en un solo nodo (H20). Si no las escribes, el script las deriva; el gate avisa si una escena queda
  fuera de toda secuencia entre dos del mismo acto.
- **Hilos** (H17): `guion.hilos[]` con cada `id` de los hilos del encuadre: `{id, escena}` cuando una escena (≥ 3) lo
  paga (esa escena lleva `paga: ["h1"]`) o `{id, sin_respuesta: "…"}` cuando la narración del acto 3 o el cierre lo
  declara («nunca se supo cuántos litros entraron al lago»).
- **Personajes** (H18): cada persona u organización del digesto que no es el protagonista llega presentada en la voz
  de su primera mención (o la escena anterior) con una raíz de su `presentacion` («Mario Baldetti, hermano de la
  vicepresidenta»). Prefiere el nombre completo si un alias lo comparten dos personas.
- **Hilo conductor** (H11 en el gate; H-C3 en el crítico): léelo de corrido como quien lo oye por primera vez. Cada
  escena sigue de la anterior; cada «esos…», «ese…», «así», «lo», «ellos» apunta a algo que ya se oyó o se leyó; nada
  se dice dos veces como si fuera nuevo. Si cambias el gancho o una escena, relee el hilo entero: lo que apuntaba a la
  versión anterior queda colgado.
- Un año anterior al del rótulo de su acto (el museo de 2019 dentro de «2021») es un flashback: el gate avisa.
  Muévelo al acto que le toca o dilo como recuerdo.
- `enlace` (pero | por_eso | y) es opcional en tarjeta, golpe y explica y solo decide el efecto de sonido de la
  entrada; la voz **no** tiene que empezar con el conector: la causalidad vive en la narración (H16).

## Escenas

Campos comunes desde la escena 2: `acto` (1–3), `rotulo?` (solo la primera escena de los actos 2 y 3), `paga?: [ids
de hilos]`, `fuente?` (≤ 44; en pantalla, obligatoria cuando la escena cita un hecho `una_fuente` o `en_disputa` cuya
fuente no se mostró ni se nombró antes en el mismo acto). Topes de voz: foto 40–280, cita 30–280, tarjeta, mapa,
ranking, tiempo y explica 40–260, golpe 20–130, capitulo 10–90; gancho y cierre como en `/video`.

- **foto** `{foto: "<id>" | null, fecha (chip ≤ 14: «Feb 2015»), lugar (≤ 24), titular (≤ 9 palabras), hechos: [ids],
  cifra?: {texto ≤ 18 con dígitos, etiqueta ≤ 30}, fuente? (≤ 44), texto (40–280)}`.
  - **Siempre con foto**: nunca `null`, `icono` ni `depto` (H7). Si el hecho no tiene foto propia, usa una de
    referencia del digesto (crédito «Foto de referencia: …») y pon en el chip «De referencia» o la época sin año. Si
    no queda ninguna, cuenta ese tramo con una cita, un gráfico o un golpe.
  - **El chip no le cambia la época a la foto**: una foto de 2021 (su `fecha` en el digesto) no va bajo «1978». Pon
    «Foto de 2021», «De referencia» o la época sin año.
  - **Una misma imagen, en ≤ 2 escenas** (contando el gancho y los retratos). Para un tramo sin foto, usa una cita,
    un gráfico o un golpe.
- **cita** `{cita: "<id>", resalte? (trozo literal de la frase que el resaltador barre; en documentos), retrato?: "<id
  de foto>", hechos?, fuente?, texto (30–280)}`: la voz dice **quién habla antes de la frase** y **lee la frase
  literal** («…lo resumió así: Cada pan sale del mismo horno…»; H4).
  - `retrato` solo con una foto cuyo `retrato_de` es el autor de la cita. Un objeto, una caja o un edificio no es un
    retrato.
  - Una frase en **otro idioma** lleva `traduccion` (≤ 140, en español). Se ve bajo la frase y la voz la dice justo
    después del original: «…kids want something to do while they're eating. Los niños quieren algo que hacer
    mientras comen.»
- **tarjeta / mapa / ranking / tiempo** `{tuit: 1, 2…, golpe (≤ 6 palabras), grafico: {plantilla, kicker, titular[],
  nota, fuente, datos}, enlace?, foco?, texto (40–260)}`: el gráfico se dibuja con una plantilla de
  `templates/graficos/` y su contrato `DATA` (`referencias/diseno/graficos.md`; las cifras crudas, de las cifras o
  los hechos del digesto). `mapa` y `ranking` piden la plantilla mapa o barras-h; `tiempo`, antes-despues o linea.
  `grafico.fuente` es la fuente en pantalla de la tarjeta. `foco: false` deja la tarjeta entera, sin zoom a la cifra
  (cuando la voz habla de todas las barras y no de una).
- **golpe**, **definicion**, **escala**, **explica** como en `/video` (`referencias/roles/video-guionista.md`). En
  `explica`, primero el `mecanismo` (cadena · ciclo · balance · onda · embudo · proporcion · umbral · cronologia:
  lo que HACE la historia en ese tramo), `brief` siempre (40–400 caracteres: qué se ve y cómo se mueve) y
  `animacion` = un id del catálogo **con ese mismo mecanismo** y no bloqueado por los últimos videos, o `null` (la
  escribe el animador y queda en la biblioteca como plantilla). Pedir una nueva es lo normal; `cadena` no es el
  comodín.

## Verdad y atribución (H3, H4, H19)

- Cada número de la voz, la pantalla y los captions viene de una cifra o de un hecho del digesto, escrito en
  **dígitos** (el script lo pasa a palabras). El dinero va con su prefijo: `US$1.15`, `Q2.50` (la voz dice «un dólar
  con quince centavos»). Cada **año** dicho o escrito está en un hecho, una frase o una cifra.
- Se atribuye en voz lo que **no está corroborado o es de parte**: un hecho `en_disputa` (las fuentes difieren: se
  atribuye o se matiza), un **alegato** (acusación, promesa, declaración de parte), una **estimación** no oficial,
  una **opinión** y toda **cita** (la voz dice quién lo dijo). Un hecho `una_fuente` —una fuente seria sobre un acto
  público: un contrato, una captura, una sentencia, un informe— se **narra llano**, con la fuente **en pantalla**
  (`fuente: "Prensa Libre"`; en tarjetas, `grafico.fuente`); si esa fuente ya se mostró o se nombró en el mismo
  acto, basta el chip. El digesto marca cada hecho con su estado y ` · ALEGATO`, ` · ESTIMACIÓN` u ` · OPINIÓN`.
- Presupuesto hablado (H19): **≤ 4 «según» por video, ≤ 2 por acto, nunca en dos escenas seguidas, nunca la misma
  fuente dos veces en voz** (la segunda vez va solo en pantalla). Varía la forma: la **aposición** («AMSA, la
  autoridad del lago, calculó…»), el **verbo de la fuente como acción** («el tribunal calificó…», «el Ministerio de
  Salud analizó…»), la **primera mención** que nombra y después solo el chip. El `final` del cierre nunca lleva
  «según» (H9).
- Presunción de inocencia: sin sentencia firme nadie es culpable, asesino, corrupto ni delincuente (señalado,
  acusado, sindicado). Con sentencia firme, la escena lleva `caso: "<persona>"`.
- Nada de lo que `no_afirma` prohíbe; nada de los `huecos`.
- Un nombre propio con dígitos («Soy502») no va en la voz: el script no lo lee; di «la prensa», el medio por su
  nombre hablado o atribúyelo en pantalla (`fuente`).

## Cierre y captions

`cierre {rotulo («Lo que dejó», «Así terminó»…), resumen (2–3 líneas ≤ 40), texto, tipo remate, forma, final,
consecuencia}` con las reglas F1–F8 de `referencias/cierres.md`.
- **Lo normal es `legado`** (decisión del usuario, 2026-10-26): lo que la gente hace **hoy** con lo que la historia
  dejó. «Hoy, sus hijos y sus nietos siguen tomando Incaparina.» · «Y los niños la siguen abriendo.» ·
  `consecuencia {quien (gente: nietos, clientes, trabajadores…, tal cual en la frase), verbo (en presente, en la
  frase)}`, sin `mecanismo`. Emotivo: de un edificio de adobe a la taza de hoy.
- **`consecuencia`** (con `mecanismo`) cuando la historia termina mal: lo que le hizo a una persona o a un grupo
  concreto, dicho llano y sin suavizar.
- **Neutro = nadie hace nada**: «la receta cambió y la marca sigue», «la empresa creció», un resumen o un dato.
  Bloquea en H-C6. Sin «según» en el `final` (H9): se apoya en un hecho confirmado. La emoción la pone el hecho, no
  los adjetivos («desgarrador», «lamentablemente»).
- `caption {tiktok, instagram, facebook (con «Fuentes en el primer comentario»), shorts (primera línea ≤ 100 con
  #Shorts)}`.

## Salida

`<TRABAJO>/guion.json` (ejemplo completo: `sesiones/_fixture_historia/guion.json`). Primero `python3
scripts/historia.py narracion <TRABAJO> --check` hasta 0 fallas (H16–H19 sobre la narración) y luego `python3
scripts/historia.py guion <TRABAJO> --check` hasta 0 fallas. Devuelves **tal cual la última línea `RETORNO {…}`** que
imprime el gate (trae `tipos` con el tipo de cada escena, sin el cierre, y además `actos`, `palabras`, `segun`,
`rotulos`, `hilos_pagados` y `hilos_sin_respuesta`).
- Si vuelve la crítica, corrige solo lo que bloquea, conserva las demás voces (y el mismo tramo de la narración:
  H15) y repasa los dos gates; añade al retorno `voces_cambiadas` (los n de las escenas cuya voz cambió; el cierre es
  N+1). Una voz cambiada regraba su **secuencia entera** (o solo esa escena con `voz --sueltas`).
- **Retoque** (la directiva trae las notas del usuario sobre un guion aprobado y con voz grabada): aplica solo eso.
  Si piden otro gancho, `ganchos --usar <id>` y relee el hilo entero (H11). Conserva palabra por palabra la voz de
  todo lo que no necesite cambiar: cada voz cambiada se vuelve a generar y cuesta créditos. Devuelve
  `voces_cambiadas`.
- Si el crítico aprobó con mejoras, el Workflow te las pasa:
  - aplícalas una por una, con su arreglo exacto (también las de voz: aún no se graba nada);
  - deshaz la que el gate no deje pasar y devuélvela en `no_aplicadas` con su motivo;
  - copia antes `guion.previo.json` para volver atrás si el gate no cierra;
  - si cambiaron voces, el oyente las vuelve a oír: una confusión o un salto nuevo en esas escenas restaura
    `guion.previo.json` y todas las mejoras van a `no_aplicadas` («confundió al oyente»).
