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
- **Promesa** `{texto (10–80, literal en la voz de la escena en), forma, en: 2, pago, revela}`: una oración propia que
  abre una pregunta concreta de la historia **sin anunciar el video** (nada de «al final», «vas a ver», «quédate»,
  «falta saber», «el último capítulo»: P2). `forma` del catálogo de `referencias/promesas.md`: una `pregunta`
  dramática («¿Cómo pasa una panadería de 25 sucursales a ninguna?»), un `presagio` (lo que el protagonista todavía
  no sabía: «Décadas después, la marca llegaría a Estados Unidos, donde ya la esperaban»), lo que estaba en juego
  (`apuesta`), un plazo (`reloj`), dos hechos que chocan (`contradiccion`) o lo que nunca se supo (`secreto`); no
  repite la de las últimas piezas (P3). Un presagio adelanta **que** algo pasa, nunca **qué** revela (H13). `pago`
  es la escena del último tercio que la cierra y `revela` es el número R de la revelación que esa escena cuenta
  **con sus palabras** (H14).
- **Bisagra** `{texto (10–90), forma (otra que la promesa), en, pago}` (P4): el segundo enganche, justo antes del
  giro: la última oración de la escena anterior al giro o la primera de la escena del giro. Va **dentro de la
  narración de corrido** (H15: literal) y la paga el giro o una escena posterior («Nadie en la familia imaginaba quién
  tocaría la puerta», y la escena del giro abre con la inspección).
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
- **El contraste se dice antes del nombre** (La Línea P4, 2026-11-07): si una escena cuenta que alguien escapó, faltó
  o no cayó, primero el hueco y después quién: «Arrestaron a más de veinte. Entre los detenidos faltaba uno: el
  secretario, Juan Carlos Monzón». No «Ese secretario era Monzón. Pero ese día estaba en Corea»: el «pero» llega
  antes de que el oyente sepa qué contradice.
- Un año anterior al del rótulo de su acto (el museo de 2019 dentro de «2021») es un flashback: el gate avisa.
  Muévelo al acto que le toca o dilo como recuerdo.
- `enlace` (pero | por_eso | y) es opcional en tarjeta, golpe y explica y solo decide el efecto de sonido de la
  entrada; la voz **no** tiene que empezar con el conector: la causalidad vive en la narración (H16).

## Escenas

Campos comunes desde la escena 2: `acto` (1–3), `rotulo?` (solo la primera escena de los actos 2 y 3), `paga?: [ids
de hilos]`, `fuente?` (≤ 44; en pantalla, obligatoria cuando la escena cita un hecho `una_fuente` o `en_disputa` cuya
fuente no se mostró ni se nombró antes en el mismo acto). Topes de voz: foto 40–280, cita 30–280, tarjeta, mapa,
ranking, tiempo y explica 40–260, golpe 20–130, capitulo 10–90; gancho y cierre como en `/video`.

**Cómo se ve** (estilo Noche; «Cómo se ve» en `referencias/flujo-historia.md`): fondo casi negro de la paleta (más
oscuro en todo el acto 2), fotos **a sangre** y oscurecidas, **una sola cosa en acento** por escena (el nombre, el año,
la cifra o la palabra que suena), titulares en Archivo 800 crema y nombres, años y cifras en Archivo condensado en
mayúsculas. Lo que eso le pide al guion: escribe todo en caja normal (la página pone la caja); en una `cita` la frase
en pantalla se enciende mientras la voz la lee y en ese tramo no hay subtítulo, por eso la voz la dice **literal** y
el resto de la voz (quién habla, lo que sigue) va antes o después de la frase, no en medio; en una tarjeta,
`grafico.datos.destacar` apunta a lo que la voz cuenta (es lo único en acento).

- **toma**: ya no existe (retiradas el 2026-11-06: muchas veces sin coherencia con lo que se narra; TM0 las rechaza). Una declaración que importa va como **cita** con la frase literal leída por la voz; el
  contexto, con una foto.
- **foto** `{foto: "<id>" | null, fecha (chip ≤ 14: «Feb 2015»), lugar (≤ 24), titular (≤ 9 palabras), hechos: [ids],
  cifra?: {texto ≤ 18 con dígitos, etiqueta ≤ 30}, fuente? (≤ 44), texto (40–280)}`.
  - **Siempre con foto**: nunca `null`, `icono` ni `depto` (H7). Si el hecho no tiene foto propia, usa una de
    referencia del digesto (crédito «Foto de referencia: …») y pon en el chip «De referencia» o la época sin año. Si
    no queda ninguna, cuenta ese tramo con una cita, un gráfico o un golpe. En una foto de referencia, el `lugar` del
    chip es **el de la foto** (su `lugar` en el digesto), no el del hecho: un local de Nueva York no va bajo «Miami»
    (sin `lugar` en la foto, el chip lo omite).
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
  comodín. Lo que la animación dibuja tiene nombre (2026-11-07):
  - `rotulos: {limite, base}` (≤ 18 caracteres): qué es la línea («Renuncia», nunca «límite» a secas) y qué es lo que
    ya había al empezar («La plaza»).
  - `sujeto: "<personaje>"`: si el mecanismo le pasa a una persona, su retrato y su nombre quedan fijos sobre el lienzo.
  - Los `pasos` se escriben como en pantalla (siglas en mayúsculas: «El CACIF», aunque la voz diga «el Cacif»).
  - **`continua: true`**: si la escena siguiente sigue hablando de lo mismo (una fuente que resume lo que la animación
    ya mostró), no la cambies por un golpe de texto: hazla otra `explica` con la misma `animacion`, su `titulo` y 1–4
    pasos nuevos. La pantalla sigue con corte invisible, no cuenta como otra explica (V1) y solo entra lo nuevo.

## La imagen cambia cuando cambia el tema (decisión del usuario, 2026-11-06)

- **Corta las escenas por contenido, no por reloj.** Una escena nueva cuando la voz pasa a otra persona, otro lugar,
  otro documento u otra fecha clave. Mientras la voz siga en lo mismo, la misma imagen se queda (aunque dure 12 s):
  partirla solo para «que se mueva» confunde.
- **La cámara no hace nada por su cuenta**: una foto lleva un solo empuje lento, y a lo más un corte limpio a la cara
  de la persona que la voz nombra (la tarjeta de persona). Las tarjetas, las animaciones y la red quedan quietas: se
  mueve lo de adentro. Transiciones limpias (corte o fundido); nada de barridos ni empujes laterales.
- **Sin tomas de video** (retiradas): una declaración que importa va como **cita** con su frase literal leída por la voz.
- **En una serie, nada se repite** (SE13): una cita o una frase de ≥ 8 palabras que ya salió en una parte anterior no
  vuelve a salir; dilo de otra forma o usa otra cita.

- **El organigrama (`red`)**: ≤ 3 niveles; arriba quien manda (uno, o los dos que mandaban juntos: «el Uno» y «la Dos»
  en el mismo nivel 0); los de la misma altura, lado a lado; nunca una fila de una persona por nivel (H23). Si la voz
  nombra a quienes investigaron, van como nodos `bando: investigador` en la franja de abajo.

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
- **La pantalla dice lo que la voz dice (H24, m124).** Una cifra en pantalla (`cifra.texto`; en el titular o el golpe,
  la que lleva moneda, % o «mil/millones») la dice también la voz de esa escena: si quitas una cifra de la voz, quítala
  de la pantalla. Un alegato, una estimación o una opinión con número en pantalla lleva su atribución también ahí
  («según Óscar Alvarado» en la etiqueta, «Óscar Alvarado cuenta lo que perdió» en el titular), no solo en la voz.
- **Fotos de un proceso (H7c, m122).** Una foto con alguien detenido, esposado o en audiencia (marcada `proceso` en
  `fotos/<id>.json`) va solo en la escena cuya voz nombra a esa persona y cuenta ese proceso; nunca ilustra el tamaño
  de un banco, una transferencia ni un alegato de otro: insinúa culpa por imagen. Para lo genérico, el lugar o la
  institución.
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

## Cierres para el usuario (fase Cierres del workflow)

Con el guion ya aprobado, el usuario elige el cierre entre 5 (usuario, 2026-11-03: «siempre me pones a escoger entre 5
opciones de hooks y cierres»). Escribes `<TRABAJO>/cierres.json` = `{"candidatos": [...]}` **sin tocar `guion.json`**:
- `c1` es `guion.cierre` tal cual (texto, final, tipo, forma, consecuencia).
- `c2`–`c5`: cada uno con otra frase final y otra forma o mecanismo (`referencias/cierres.md`: consecuencia
  quien|perdida|reloj|despues|espera, legado, pendiente, quien_decide; a lo más una pregunta). Al usuario le gusta la
  consecuencia humana para quien vive el tema, dicha llano («Y mientras tanto, los guatemaltecos pasan tiempo en el
  tráfico y no con sus familias»): su tiempo, su familia, su bolsillo, lo que espera.
- Cada uno: `id`, `texto` (una oración que prepara, ≥ 3 s de voz, y la frase final), `final` (≤ 14 palabras),
  `tipo`, `forma`, `consecuencia {mecanismo?, quien, verbo}` si es consecuencia o legado, y `por_que` (una línea).
- Solo lo que el guion y sus cifras sostienen (F6, F8). Pasa `<script> cierres <TRABAJO> --check` hasta 0 fallas.

## Salida

`<TRABAJO>/guion.json` (ejemplo completo: `sesiones/_fixture_historia/guion.json`). Primero `python3
scripts/historia.py narracion <TRABAJO> --check` hasta 0 fallas (H16–H19 sobre la narración) y luego `python3
scripts/historia.py guion <TRABAJO> --check` hasta 0 fallas. Devuelves **tal cual la última línea `RETORNO {…}`** que
imprime el gate (trae `tipos` con el tipo de cada escena, sin el cierre, y además `actos`, `palabras`, `segun`,
`rotulos`, `hilos_pagados` y `hilos_sin_respuesta`).
- Si vuelve la crítica, corrige solo lo que bloquea, conserva las demás voces (y el mismo tramo de la narración:
  H15) y repasa los dos gates; añade al retorno `voces_cambiadas` (los n de las escenas cuya voz cambió; el cierre es
  N+1). Una voz cambiada regraba su **secuencia entera** (o solo esa escena con `voz --sueltas`).
  Una falta que trae **`cambios`** (el crítico ya la probó) se aplica **tal cual**, sin reescribirla:
  `python3 scripts/historia.py aplicar <TRABAJO> --cambios '<sus cambios>'` (el mismo texto va a la escena, la
  narración, la promesa y el candidato del gancho; si el gate la rechaza, sale 1 y deja `guion.json` como estaba;
  con 0, su `RETORNO {"escenas_cambiadas": […]}`). Las faltas que se probaron juntas, en una sola llamada.
  Un arreglo que el gate rechaza no se reescribe en silencio: aplica lo más cercano que pase (pruébalo antes con
  `python3 scripts/historia.py probar <TRABAJO> --cambios '[{"escena": N, "texto": "…"}]'`, que no toca el TRABAJO)
  y devuélvelo en `arreglos_rechazados: [{n, falla}]` con la línea FALLA del gate; el coordinador lo lleva al
  reporte y a las mejoras del framework.
- **Retoque** (la directiva trae las notas del usuario sobre un guion aprobado y con voz grabada): aplica solo eso.
  Si piden otro gancho, `ganchos --usar <id>` y relee el hilo entero (H11). Conserva palabra por palabra la voz de
  todo lo que no necesite cambiar: cada voz cambiada se vuelve a generar y cuesta créditos. Devuelve
  `voces_cambiadas`.
- Si el crítico aprobó con mejoras, el Workflow te las pasa:
  - copia antes `guion.json` a `guion.aprobado.json` (`aplicar` reescribe `guion.previo.json` en cada llamada);
  - aplícalas una por una, con su arreglo exacto (también las de voz: aún no se graba nada); la que trae `cambios`,
    con `historia.py aplicar`;
  - deshaz la que el gate no deje pasar y devuélvela en `no_aplicadas` con su motivo;
  - devuelve `voces_cambiadas`: si cambiaron voces, el oyente las vuelve a oír, y una confusión o un salto nuevo en
    una escena revierte **solo esa escena** (su texto de `guion.aprobado.json`, con `aplicar`); una mejora de
    precisión (H-C5) se queda aunque confunda.

## Modo serie (una parte de `/serie`)

La parte dura ≈ 90 s (190–250 palabras; H15 con el formato `historia-serie`) y solo ve los hechos hasta el fin de su
periodo. Se entiende sola (SE4): quien llega por la parte 3 no vio las otras, así que lo que hace falta lo cuentas en una
oración, sin «como vimos» ni «en la parte anterior». En las partes 1…M−1 el cierre es `tipo: pregunta` (o remate) con
`forma: "puente"`: la frase final deja la pregunta del puente del plan, que abre la parte siguiente, sin anunciarla
(«en la próxima parte» lo rechazan P2 y F9). Después, en `cierre.invitacion` (aparte de `cierre.texto` y de la
narración), una oración que pide seguir la cuenta y dice qué cuenta la parte siguiente: «Sígueme: en la segunda parte te
cuento cómo …» (SE9: «Sígueme», la parte en palabras, su tema, ≤ 18 palabras, sin cifras ni revelaciones); un hilo que sigue abierto va `{id, pasa_a: N+1}` (H17). En la última, todos
los hilos se pagan o se declaran sin respuesta y el cierre es legado o consecuencia. Captions: TikTok, Instagram y
Facebook abren con «Serie · Parte N de M: <título>»; el título de Shorts lleva «(N/M)»; desde la parte 2, esos tres
captions llevan una línea que manda al inicio («¿Llegaste por aquí? La Parte 1 está fijada en mi perfil.») (SE8). La
última parte no lleva invitación. El chip «Parte N de M» y la
línea «Parte N+1 · título» del cierre los pone el script.

**Cada parte trae lo NUEVO (SE15–SE16, decisión del usuario, 2026-11-09).** Pegadas en `/youtube-long` y vistas de
seguido, las partes se repetían: 17 hechos contados dos o tres veces, Monzón presentado ×6, la Cicig explicada ×6.
- El digesto marca `[YA CONTADO EN Pk]` en la cronología y lista lo que ya contaron las partes anteriores. Eso entra
  solo como **contexto**: ≤ 2 ids en ≤ 2 escenas (el gancho cuenta como una). Lo demás sale de TU reparto.
- Quien ya se presentó entero en otra parte vuelve con **un recordatorio de una palabra** de su presentación («el
  secretario Monzón»; el digesto lo da), no con la aposición completa. H18 sigue pidiendo esa palabra.
- Una sigla ya explicada va con ≤ 4 palabras de glosa («la Cicig, de la ONU,») o sin glosa.
- SE4 no cambia: sin «como vimos». Lo que hace falta para entender cabe en una oración de contexto.
- **La frase final no se parece a la de otra parte (SE13, m131).** Dos partes no rematan con la misma imagen: «¿dónde
  tenía el dinero de sus ahorrantes?» y «¿qué pasaría con el dinero de sus ahorrantes?» fallan (≥ 2 raíces en común que
  son la mitad de la frase más corta). Cambia el sujeto o la imagen del remate.
- Una serie que explica conceptos admite **hasta 2 escenas `definicion` por parte** (V1, m119; formatos
  `historia-caso`, `historia-serie` y `explica-serie`): una por concepto nuevo.

## Escenas nuevas y personas (2026-11-06)
- **`red`** (≤ 1 por video): cuando hay ≥ 4 actores conectados y la voz cuenta quién mandaba.
  - Forma: `{tipo: "red", titulo, texto, nodos: [{id, personaje, nivel (0 = quien manda), dice}], aristas: [{de, a, rel, hecho}], atribuida, fuente}`.
  - Cada arista lleva el id del hecho cuyas `relaciones` la dicen.
  - Si alguna es un alegato: `atribuida: true` y la voz atribuye («según la fiscalía…»). Gate H23.
  - Cada `dice` suena en la voz en el orden de los nodos.
- **`dividida`**: dos personas frente a frente en una escena foto. Escribe `dividida: [foto_a, foto_b]`, con un retrato de cada una.
- **Cita de un documento:** entra como hoja con sello (fecha y fuente). No hace falta escribir nada más.
- **Tarjeta de persona:** la primera mención la arma el script sola. Tu trabajo es que la voz diga el nombre completo o su alias la primera vez.
- **Modo caso:** cita en `hechos` de cada escena los ids que cuentas; la parte debe citar ≥ 60 % de los que se le repartieron (SE12).
- **Última parte de una serie: el resumen** (SE14). Una escena `resumen_serie: true` en el acto 3, antes de la última cita o
  del cierre, de 20–30 s de voz: repasa en orden toda la serie (un momento por oración, de ≥ 5 partes, con sus ids en
  `hechos`) y termina en lo que más pesa. Nada nuevo; los alegatos, atribuidos. Va también en la narración de corrido.
  Visual: `explica` con `cronologia` (pasos «año · momento» con palabras que la voz dice; aquí hasta 8, uno por oración).
  Ver `referencias/flujo-serie.md`.

## Recompensa, escalera e imagen (P6, H25, H26; 2026-11-10)

- `promesa.pregunta`: la pregunta que el video responde, para la pantalla («¿…?», ≤ 9 palabras, con el sujeto del
  gancho). La voz no cambia. La promesa se oye antes del segundo 10: en la escena 2 es la primera oración.
- La tensión sube por peldaños: cada tercio abre o paga algo (promesa, bisagra, giro, un hilo en `paga`). Al pagar un
  hilo en el nudo, que otro siga abierto; no los pagues todos en la misma escena.
- Una `foto` no pasa de 12 s: si el tramo es más largo, son dos escenas con dos imágenes (cambia el tema, cambia la
  imagen). Por cada 4 fotos, al menos una composición distinta: pantalla dividida, mini-mapa, subrayado, documento,
  tarjeta o animación. Con ≥ 5 personas, una escena `red`.
- Última parte de una serie con `serie.promesa`: `guion.responde_serie = N`, la escena que contesta la pregunta de la
  serie. En una serie, una foto no sale en más de 2 partes (SE19): usa las que el digesto marca sin usar.

## Señalar, arriesgar y el rostro de la cifra (2026-11-10)

- Cada cifra que la voz dice se ve entrar o resaltarse en ese momento (V26): si la escena es una foto, lleva `cifra`; si
  no cabe, la cifra va en un golpe o una tarjeta. Una cifra dicha sobre una foto sin nada es la que nadie recuerda.
- La `promesa.pregunta` es una que el espectador puede intentar contestar, y la respuesta lo sorprende.
- Si la cronología trae a una persona afectada con nombre (verificada), cuéntala en su escena antes de dar el número de
  afectados; no en la misma. Sin persona verificada, no hay rostro.
- La escena `adivina` vale una vez por historia, justo antes de la revelación mayor, con sus reglas (la opción correcta
  con respaldo; las otras dos son señuelos, no cifras).

## El tablero de investigación (2026-11-10)

La escena `red` tiene dos estilos. Sin `estilo` es el organigrama por niveles. Con `"estilo": "tablero"` son los mismos
`nodos` y `aristas`, dibujados como tablero: cada persona en un cuadrito tipo foto de expediente que entra cuando la voz
la nombra, y un hilo que une a dos cuando el hecho los relaciona. Mismas reglas (H23): cada persona es del encuadre y
tiene retrato; cada hilo es un hecho publicable que registra esa relación; con un alegato, `atribuida: true`.

- Sin tachas ni marcas sobre las caras (decisión del usuario): el tablero solo ilumina a quien se nombra.
- Úsalo cuando importa **quiénes** son y que se conocen (un caso con 4–8 personas); el organigrama, cuando importa
  **quién manda a quién**.
- Cabe 3 × 2 en 9:16 (hasta 6 personas cómodas; 8 como máximo).

## El mapa con ruta y el cierre que se envía (2026-11-10)

- **`ruta`** en una escena `foto`: 2–4 departamentos en el orden del recorrido (`"ruta": ["Escuintla", "Guatemala"]`).
  El localizador se acerca a esa zona, enciende cada departamento a su turno y un trazo los une. Úsalo cuando la
  historia se mueve (el contenedor del puerto a la capital, la caravana, la ruta del dinero); cada lugar sale de un
  hecho de la escena. Con un solo lugar basta `depto`. Cuenta como composición distinta (H26).
- **Una de las cinco opciones de cierre se puede enviar.** Instagram cuenta los envíos por alcance entre sus señales, y
  en nuestras métricas varias piezas tienen cero. Entre las cinco opciones que le llevas al usuario, una es la frase que
  alguien le mandaría a una persona concreta: la consecuencia dicha para quien la vive («Si tu ahorro estaba en la
  offshore, ese seguro no te cubría»). Dentro de las formas del catálogo (consecuencia, legado, quién decide), sin
  pedir que lo envíen ni que comenten (F4). Es una opción: el usuario elige.
