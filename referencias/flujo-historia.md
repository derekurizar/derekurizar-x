# Flujo `/historia` — índice

Un **evento o una historia de Guatemala contada de principio a fin** en un video vertical (1080×1920, 30 fps) de
**2–3 min** (objetivo 150 s, tope 180 por YouTube Shorts) para TikTok, Reels y Shorts, más su 4:5 para el feed. Sirve
para cualquier historia que se narre: cómo llegó una marca, cómo nació una empresa, la vida de un presidente, por qué
el país exporta café, un caso de justicia desde que se descubrió hasta hoy. No tiene modos: el editor nombra el arco
que le toca a cada una. Misma línea que `/video`: voz El Faraon 4 con las cifras en palabras, música y efectos de los
catálogos fijos, barra de progreso, subtítulos, zona segura (V13), 9:16 + 4:5, caption por plataforma, cierre con
**«Sígueme en»**. La publicación es manual.

```
preparar (historia.py: TRABAJO = sesiones/historia-<slug>/, paleta provisional y música)
→ Workflow historia [historia-editor → encuadre.json (pregunta, protagonista, revelaciones, fotos_clave, arco,
                       tres actos y la espina (detonante, punto medio, clímax, resolución), 2–6 hilos, personajes
                       con su presentación, 2–5 periodos que reparten 2–3 ejes, paleta, sensibles)
                     → historia-investigador por eje (en paralelo) → hallazgos_<eje>.json
                     ⇢ historia-verificador por eje (pipeline: verifica en cuanto su investigador termina): segunda
                       fuente por hecho, fechas en conflicto, estado actual de los casos, fotos con licencia
                       (historia.py foto; --de-fuente = la og:image de una nota leída; --protagonista) →
                       verificacion_<eje>.json → gate hechos --check (H1–H3, H7, H12; sin foto del protagonista, un
                       verificador la baja antes de seguir)
                     → consolidar → historia.json (cronología) + base/ (hilo.json, datos.json) + la paleta del encuadre
                     → video-gancho en modo historia (5 candidatos con la foto del protagonista) → gate ganchos --check
                       (R1–R9, H10, H12, H13) → video-critico elige (reserva: no regala una revelación)
                     → historia-guionista (ganchos --usar → la narración de corrido por acto → gate narracion --check
                       (H16–H19) → la reparte en escenas con acto, rótulos y secuencias → guion.json) → gate guion
                       --check (H3–H20 + V1–V5, V9, F1–F8) y su línea RETORNO
                     → historia-oyente (oyente ingenuo: primero la narración de corrido, luego la pantalla por escena
                       → oyente.json)
                     → video-critico en modo historia (espina, hilos y flujo; resuelve o justifica cada confusión y
                       cada pregunta sin responder del oyente; ≤ 2 vueltas con el guionista, desde la 2 ACOTADAS: solo
                       bloquea lo que cambió, lo pendiente, H-C5 o un puntaje ≤ 2; cada arreglo probado trae sus
                       `cambios` y el guionista los aplica tal cual con `historia.py aplicar`; si la última vuelta
                       solo bloquea con arreglos probados, se aplican y queda aprobado (`aprobado_por:
                       arreglos_probados`); con «pasa», el guionista aplica sus mejoras, también las de voz, y el
                       oyente las vuelve a oír: se revierte solo la escena que confunde, nunca una de precisión)
                     → video-animador por cada escena explica sin animación (reusa o crea y registra en la biblioteca)]
   desde: "encuadre" → el editor re-encuadra (actos, espina, hilos, personajes sobre la cronología verificada) y salta
   a Guion · desde: "guion" → salta a Guion · desde: "retoque" + notas → salta a Guion (el guionista aplica las notas y
   conserva las voces) → oyente → crítica (1 vuelta) → mejoras → animación; devuelve voces_cambiadas
→ QA de fotos (historia.py fotos-contacto) → [sin-voz: voz-falsa] | voz (MCP ElevenLabs, como /noticias)
   (un nodo por secuencia de 2–5 escenas; descargar --estado corta cada secuencia en sus escenas)
→ tiempos (V16, V6; V10 solo con el motor propio) → escuchar (V11)
→ Plano (solo con realizacion: mesa) [Workflow plano: video-realizador → plano.json (qué pieza entra con cada oración)
                     → gate plano --check --hoja (MV1–MV14) → plano.md (la hoja de golpes); notas → retoque de pantalla]
→ grabar (mesa: gates del plano, tableros limpios (V7), proyecto de HyperFrames, hyperframes check, render con un
   proceso · motor propio: V7, V13) → montar (V8) → revisar (hoja de contacto), en 9:16 y luego en 4:5
→ entregar (historias/<fecha>-<slug>/) → memoria.py --historia (memoria/historias.json) → make validate (M10)
```

`scripts/historia.py` hace lo propio de la historia y escribe el **mismo TRABAJO que `/video`**: arma en
`TRABAJO/base/` un «hilo base» (`hilo.json` con el tema y la tesis, `datos.json` con las cifras y los números de los
hechos verificados, y las tarjetas `tuit_N.html` materializadas con `scripts/materializar.py` desde el `grafico` de
cada escena), así el gate del guion, los ganchos, los tiempos y el render salen de `scripts/video.py`, con las escenas
propias enchufadas por sus extensiones (`CONSTRUCTORES`, `TRANSICION_DE`, `SIN_HUECO`). Con el motor propio, las
páginas son `video/noticia.html` (gancho con foto y escena `foto`), `video/historia.html` (`cita` y `capitulo`) y las de
`/video` para el resto, y el **rótulo de acto** lo dibuja `video/comun.js` sobre cualquiera de ellas mientras la voz
sigue; en la mesa de archivo esas páginas solo graban los tableros.

## Quién dibuja: la mesa de archivo (desde 2026-11-14)

Decisión del usuario (2026-11-14): `/historia` y `/serie` (motor historia) ya no se dibujan con el motor propio (las
páginas `video/*.html` grabadas con `video_grabar.js`), sino con la **mesa de archivo** en HyperFrames
(`scripts/video_hf.py` sobre `scripts/mesa.py`). Guía: `referencias/flujo-mesa.md` (cuadro, piezas, plano y gates
MV1–MV14); rol: `referencias/roles/video-realizador.md`. Lo esencial:

- Con cada oración de la voz entra una **pieza** que la voz nombra (foto, recorte con su titular real, página de
  documento, ficha de persona o institución, lugar en el mapa, fecha, cifra, cita que se entinta, lista, jerarquía de
  personas `red`) y se queda quieta. La cámara no se mueve y el texto da tiempo de leerse (MV8).
- Las escenas con animación propia (`explica`, `tarjeta`, `mapa`, `ranking`, `tiempo`, `escala`, `vias`, `deptos`,
  `lupa`, `cortina`) son **tableros**: su clip limpio, grabado con el motor propio, va solo en su mesa.
- `video.json` lleva `"realizacion": "mesa"` (lo fija `historia.py preparar` o `serie.py preparar`). `--realizacion
  propio` deja el motor viejo; un trabajo empezado con un motor termina con él. Los demás flujos siguen en el propio.
- El guion visual es `TRABAJO/plano.json`: lo escribe el `video-realizador` en el paso **Plano** (Workflow `plano`),
  tras `tiempos` con la voz real y antes de `grabar`, y lo valida `historia.py plano <TRABAJO> --check --hoja` (deja
  la hoja de golpes `plano.md`). Lo que falle en pantalla (MV8, MV10, MV11, MV2) se arregla en el plano, sin tocar el
  guion ni la voz. Los comandos no cambian; lo que hace cada uno está en «Producción en la mesa», más abajo.

**Qué de este documento es del motor propio** (solo aplica con `realizacion: propio`; lleva una primera línea «(Motor
propio: …)»): «Cómo se ve», «Personas, red y dinamismo» (tarjeta de persona, cámara y sub-planos, estilos de `red`,
señales, transiciones) y el dibujo de cada escena en «Escenas» y en las escenas con archivos reales. No corren en la
mesa: V7 (solo en los tableros), V10, V12, V13 (→ MV10), V15 (→ MV14), V21, V22, V26 (→ MV1), A3, H7b y la parte de H26
sobre fotos fijas (→ MV3, MV6; mientras `guion --check` los marque sobre el guion, se cumplen ahí). Siguen valiendo los
gates de texto, verdad y voz: H1–H25 (salvo lo dicho), V1–V6, V8, V9, V11, V16–V20, V23–V25, P*, F* y SE*.

## Formato (decisiones del usuario, 2026-10-24 y 2026-10-27)

Una historia se cuenta en **tres actos**, no en capítulos por año. El **planteamiento** presenta el mundo y al
protagonista y termina en el **detonante** (lo que lo cambia todo). El **nudo** sube la apuesta: el **punto medio**
cambia lo que el espectador creía saber y el **giro** (`giro: true`) va aquí. El **desenlace** trae el **clímax** y la
**resolución**: qué quedó, y qué nunca se supo. Los actos 2 y 3 se marcan con un **rótulo** (año y ≤ 4 palabras)
dibujado sobre la primera escena del acto mientras la voz sigue (en la mesa, el rótulo abre la mesa de esa escena como
ficha: «Acto 2 de 3 · lugar», título y periodo); una tarjeta de capítulo que detiene la voz es la excepción. El editor
escribe la espina (detonante, punto medio, clímax, resolución) con los ejes que la sostienen; el guionista cuelga las
escenas de esa espina. Y antes de colgar nada escribe la **narración de corrido** (320–400 palabras ≈ 150 s a 145
palabras por minuto): las escenas la reparten sin cambiar una palabra (H15).

| Bloque | Qué | Gate |
|---|---|---|
| E1 gancho (≤ 7.5 s) | **siempre una foto a sangre del protagonista** que cubre toda la pantalla (visual `foto`, como la Cajita Feliz; H12); el momento más fuerte de la historia (el problema que la hizo nacer, la persona, la decisión), **nombra al protagonista** (la marca, la persona: `protagonista` del encuadre), en medias res, **nunca una revelación** del encuadre (lo que el video paga: de qué está hecho, cómo terminó; H13 veta sus números, el crítico puntúa `reserva`); se lee en silencio; «Guatemala» en ≤ 6 s; sin «Esta es la historia de…». **En la mesa** el cuadro 0 no es a sangre: la foto del protagonista sobre papel con su pie y su crédito, su nombre en una nota y el golpe de arriba (≤ 6 palabras), ya puestos antes de que suene nada (MV14) | `ganchos --check` (R1–R9, R11–R12; sin R10; H7 visual foto; H10, H12, H13) |
| promesa | una oración propia en la escena 2 que abre una pregunta concreta de la historia sin anunciar el video (forma del catálogo de `referencias/promesas.md`, que rota); `revela` dice qué revelación paga y la escena `pago` (último tercio) la cuenta con sus palabras | V9 · H14 · P1–P3 |
| bisagra | el segundo enganche justo antes del giro, con otra forma, literal en la narración; lo paga el giro o una escena posterior | P4 |
| narración | `narracion[3]` `{acto, texto}`: el texto corrido por acto, 320–400 palabras; cada voz de escena es un tramo literal; ≥ 2 conectores causales o temporales por acto; ≤ 1 escena que abra con atribución; ≤ 6.5 cortes por minuto | H15 · H16 |
| tres actos | `acto` 1–3 en cada escena, no decreciente; el detonante cierra el 1, el punto medio y el giro van en el 2, el clímax y la resolución en el 3 | H8 · crítico (H-C2) |
| rótulo de acto | `rotulo {anio ≤ 12, titulo ≤ 4 palabras, lugar?}` en la primera escena de los actos 2 y 3 (opcional en la escena 2), sobre foto, cita, tarjeta, mapa, ranking, tiempo, golpe o explica (nunca gancho, adivina ni cierre); una escena `capitulo` con voz propia solo como excepción (0–2, aviso) | H8 |
| giro | una escena con `giro: true` en el acto 2, entre el 40 y el 75 % | H8 |
| hilos y personajes | cada hilo del encuadre se paga en una escena (`paga: [id]`) o se declara sin respuesta en la narración; cada personaje llega presentado en su primera mención (≤ 8 palabras) | H17 · H18 |
| secuencias de voz | `secuencias`: grupos de 2–5 escenas consecutivas del mismo acto (sin el gancho ni el cierre; giro o rótulo solo al inicio) cuya voz se graba de corrido en un nodo; sin ellas, el script las deriva | H20 |
| cierre | `cierre.html` en dos pantallas (rótulo «Lo que dejó» + 2–3 líneas, luego el remate) y «Sígueme en». **Lo normal es el legado**: lo que la gente hace hoy con lo que la historia dejó («sus hijos y sus nietos siguen tomando Incaparina»); `consecuencia` si termina mal; nunca neutro (nadie hace nada: «la marca sigue»); sin «según» | F1–F8 (`legado`) · H9 · crítico (H-C6) |

**Escenas**: `foto` (la foto de archivo a sangre con Ken Burns, chip con fecha y lugar, titular, cifra opcional,
fuente y «Foto: autor · licencia»), `cita` (la frase literal de una persona, o de un documento con su membrete y un
resaltador; una cita en otro idioma lleva `traduccion`, en pantalla bajo la frase y dicha por la voz), `capitulo`
(solo como excepción), `tarjeta`/`mapa`/`ranking`/`tiempo` (un gráfico de las 26 plantillas de `templates/graficos/`
con su `DATA`; `foco: false` deja la tarjeta sin zoom a la cifra), `golpe`, `definicion`, `escala`, `explica` (una
animación de la biblioteca `video/animaciones/`: `cadena`, `cronologia`, y las que el animador vaya creando), `red` (el
organigrama o el tablero del caso), las **escenas con archivos reales** (`vias`, `lupa`, `deptos`, `pagina`, `cortina`,
`archivo`, `bandos`; H27–H33, abajo) y `cierre`. ≤ 3 seguidas del mismo tipo. ≤ 19 escenas más el cierre. `enlace` (pero | por_eso | y) es opcional y solo
decide el efecto de la entrada: la voz no tiene que empezar con el conector (la causalidad vive en la narración).
Topes de voz: foto 40–280, cita 30–280, tarjeta/mapa/ranking/tiempo/explica 40–260, golpe 20–130, capitulo 10–90,
red, vias, lupa, deptos, pagina y bandos 60–320, cortina 50–300, archivo 50–320.

(Motor propio: lo que el párrafo anterior dice de cómo se dibuja cada escena —la foto a sangre, el chip, el resaltador,
el zoom a la cifra— es el dibujo viejo.) **En la mesa** los tipos, los topes de voz y los gates del guion son los mismos,
pero la escena es unidad de **voz y de respaldo** (sus hechos, su foto semilla, su cita, su página), no de dibujo: el
realizador decide en el plano qué pieza entra con cada oración. `explica`, `tarjeta`, `mapa`, `ranking`, `tiempo`,
`escala`, `vias`, `deptos`, `lupa` y `cortina` ocupan una mesa solas, como tableros; `foto`, `cita`, `golpe`,
`definicion`, `pagina`, `archivo`, `bandos` y `red` dan las piezas de su mesa (la foto con su pie, la cita que se
entinta, la página con la frase subrayada, las fichas de persona, la jerarquía). El `titular` de una escena `foto` es el
golpe de arriba de su mesa (≤ 6 palabras, sin adelantar la cifra).

**Cómo se ve** (estilo Noche, `referencias/diseno/sistema.md`; lo mismo que `/video` y `/noticias`):

(Motor propio: esta lista describe las páginas `video/*.html`. En la mesa valen la paleta, el grano, la tipografía y el
acento en una sola cosa; el cuadro, las piezas y sus medidas están en `referencias/flujo-mesa.md` §2–3. No hay fotos a
sangre: la foto va sobre papel con su pie y su crédito. La cita se entinta palabra por palabra y los subtítulos callan
mientras la voz la lee. La barra de progreso lleva un tramo por acto y otro para el cierre.)

- Fondo de la paleta casi negro con grano fijo; en el **acto 2** (el nudo) toda la escena baja a `fondo_acto2`
  (fondo × 0.5), cuerpo y velos incluidos: el nudo se ve más oscuro sin que la voz lo diga.
- **Fotos a sangre** (gancho y `foto`), brillo 0.45–0.6, con una sombra del color del fondo arriba (bajo la barra) y
  abajo (bajo los subtítulos); la capa a sangre lleva `data-fuera-de-zona` y lo que se lee queda en la zona segura (V13).
  En la escena `foto` la imagen ocupa una lámina de 1080×1200 arriba (proporción 0.9); con `foto --encaje contener`
  el gráfico entra entero en ella y la página lo muestra a brillo 0.7 y casi sin Ken Burns.
- **Acento en una sola cosa** por escena: el nombre del protagonista, el año, la cifra o la palabra que suena. Nombres,
  años y cifras en Archivo condensado 900 en mayúsculas; titulares y subtítulos en Archivo 800 crema; chip, fuente y
  crédito en JetBrains Mono 600; nada en Instrument Serif.
- **Rótulo de acto**: el año grande condensado en el acento, el título en Archivo 800 y el lugar en Mono, sobre un velo
  del fondo, mientras la voz sigue.
- **Cita**: la frase está entera en pantalla y **se enciende al ritmo de la voz** que la lee; mientras la lee no hay
  subtítulo (sin subtítulo doble). El subtítulo vuelve para lo que la pantalla no dice (el autor, lo que sigue). La
  frase clave va subrayada en el acento y la comilla grande es atmósfera en el acento al 13 %, fuera de la zona.
- **Barra de progreso por acto** (tres tramos de largo proporcional a su duración; el gancho entra en el primero y el
  cierre en el último).

## Tomas de video (retiradas el 2026-11-07)

El tipo `toma` (un clip de video de una nota, con o sin su audio) **ya no existe**: el gate TM0 rechaza una escena
`toma` y el código que bajaba y cortaba los clips se borró el 2026-11-14. Una declaración que importa va como
**`cita`**: su frase literal en pantalla, leída por la voz, con quién la dijo y dónde.

## Personas, red y dinamismo (decisión del usuario, 2026-11-06)

(Motor propio: la tarjeta de persona de 2.2 s, los planos de la foto, el dibujo de la escena `red`, las señales y las
transiciones de esta sección son del dibujo viejo. **En la mesa**: cada persona que la voz nombra entra como pieza
`persona` (retrato, nombre y cargo; si un hecho verificado con fecha lo trae, su situación: «Absuelta», «Condenado en
2022») y se queda en la mesa; la escena `red` se dibuja como jerarquía de personas, con ≤ 3 niveles, ≤ 2 por nivel y
≤ 2 acusadores aparte y sin hilos, y un alegato lleva hilo punteado y la etiqueta «Según…» (MV12); no hay sub-planos,
empuje de la foto ni transiciones. Los retratos, los focos y los gates H21–H23 valen igual: son el
respaldo de esas piezas.)

**Cada persona tiene cara.** La primera vez que la voz nombra a una persona del encuadre (`personajes[]` con `tipo: persona`, `cargo` ≤ 28 caracteres y `bando`), la escena muestra su **tarjeta**: retrato en círculo, nombre y cargo, bajo la barra de arriba durante 2.2 s. La arma `tiempos` sola (`S.personas`). Si la foto de la escena ya la muestra (una cara marcada con su nombre), solo va la franja del nombre y hay un corte limpio a su cara en ese instante.

**Retratos y focos.** El retrato es una foto con `retrato_de`, o una cara marcada en una foto de grupo:
- `historia.py focos TRABAJO` detecta las caras con Vision de macOS (`scripts/caras.swift`).
- `historia.py focos TRABAJO --foto ID --cara K --persona "Nombre" --evidencia "pie o categoría"` dice de quién es cada cara.
- `foto` guarda los focos solo y acepta `--retrato-evidencia`.

**Cámara quieta (corrección del usuario, 2026-11-07).** Los sub-planos por reloj (un encuadre nuevo cada 3–4.5 s) y el salto de cámara en las escenas sin foto se retiraron: «mover solo por mover» desorienta. Con `CAMARA_QUIETA` en `scripts/video.py`, una foto lleva un solo empuje lento y, a lo más, **un** corte limpio a la cara de la persona que la voz nombra (`video.planos_foto`, `S.N.planos`); las tarjetas, las animaciones y la red quedan quietas y se mueve lo de adentro. La imagen cambia cuando cambia de qué se habla. Detalle en `referencias/flujo-video.md`, «Cámara y edición».

**Escena `red`, el organigrama.** Nodos con retrato o sigla en ≤ 3 niveles: arriba (nivel 0) quien manda, uno o los dos que mandan juntos; los de la misma altura del caso van lado a lado (nunca una fila de uno por nivel); los investigadores que la voz nombra, en su franja de abajo. La relación va en una pastilla al centro de su línea (nunca encima de un nombre o un cargo); la cámara no se mueve: los nodos entran cuando la voz los nombra (2026-11-06). Cada arista sale de un hecho verificado con `relaciones: [{de, a, rel}]`. Los alegatos van punteados, con el chip «Según la acusación» y voz atribuida.

**Más señales en pantalla.**
- **Documento:** la hoja entra deslizándose y al final cae el sello con la fecha y la fuente (efectos `papel` y `sello`).
- **Subrayado:** marca el año o la cifra del titular cuando la voz lo dice (`marcador`).
- **Pantalla dividida:** `dividida: [foto_a, foto_b]`, dos personas frente a frente.
- **Mini-mapa:** aparece si la escena tiene departamento y foto.
- **Transiciones:** corte o fundido. El empuje lateral según avanza o retrocede el año y el whip en un «pero» se retiraron con la cámara quieta (2026-11-07).

| Gate | Qué pide |
|---|---|
| H21 | El retrato de cada persona tiene evidencia (pie, categoría o descripción) que dice su apellido. |
| H22 | Toda persona que la voz nombra tiene retrato. |
| H23 | Escena `red`: 3–8 nodos, ≤ 3 niveles, 1–2 en el nivel 0 y nunca una fila de uno por nivel. Cada arista con un hecho publicable que registra esa relación. Los alegatos van con `atribuida: true` y la voz atribuye. Cada nodo suena en la voz y en orden. Una escena `red` por video. |

## Reglas de verdad

- Cuatro estados. Solo se cuentan hechos `confirmado` (dos fuentes de grupos distintos: un documento oficial, la
  academia, el archivo o la empresa para su propia historia, y otra que lo respalde; una cifra vale también con una
  fuente oficial o académica), `una_fuente` (una fuente válida y seria sin nada que la contradiga) o `en_disputa` (las
  fuentes **difieren** en el año, el monto o un detalle: las dos versiones en `nota`). `no_confirmado` no se cuenta.
  Cada hecho y cada cifra lleva `tipo_hecho`: `acto` (un acto público verificable: contrato, captura, sentencia,
  informe), `alegato` (acusación, señalamiento, promesa o declaración de parte), `estimacion` (cifra no oficial) u
  `opinion`.
- **Atribución**. Se atribuye en voz lo que **no está corroborado o es de parte**: un hecho `en_disputa` (las fuentes
  difieren: se atribuye o se matiza), un **alegato** (acusación, promesa, declaración de parte), una **estimación** no
  oficial, una **opinión** y toda **cita** (la voz dice quién lo dijo). Un hecho `una_fuente` —una fuente seria sobre
  un acto público: un contrato, una captura, una sentencia, un informe— se **narra llano**, con la fuente **en
  pantalla** («Fuente: Prensa Libre»); si esa fuente ya se mostró o se nombró en el mismo acto, basta el chip.
  Presupuesto hablado: **≤ 4 «según» por video, ≤ 2 por acto, nunca en dos escenas seguidas, nunca la misma fuente
  dos veces en voz** (la segunda vez va solo en pantalla). Varía la forma: la **aposición** («AMSA, la autoridad del
  lago, calculó…»), el **verbo de la fuente como acción** («el tribunal calificó…», «el Ministerio de Salud
  analizó…»), la **primera mención** que nombra y después solo el chip. El `final` del cierre nunca lleva «según»
  (H9). El chip «Fuente:» de la escena ya no depende de que la voz diga «según».
- Cada fuente con su texto guardado (`historia.py leer`: HTML, PDF o Wayback) y la cita literal dentro; la cita de un
  hecho trae su **año** y cada número del texto. **Wikipedia no cuenta**: es el mapa para llegar a sus referencias.
- **Qué fuentes cuentan** (`clasificar`, lista cerrada; `leer` avisa «NO CUENTA» al guardar):
  - oficial: gob.gt, MP, CICIG, organismos;
  - medio: la lista de `/noticias` más prensa internacional y de negocios (Forbes, E&N, Bloomberg y Bloomberg Línea,
    NYT, El País, Axios, Chicago Tribune…), un grupo por casa editorial;
  - **agencia**: una nota firmada por AP, EFE, Reuters o AFP («(AP)», «Por/By Associated Press» en el texto guardado)
    cuenta como la agencia aunque la publique otro diario. Dos diarios con el mismo cable no son independientes;
  - académica: `.edu`, SciELO, JSTOR, Britannica…;
  - archivo y museos: archive.org, hemerotecas, Library of Congress, The Henry Ford, Smithsonian;
  - empresa: los `dominios_propios` del encuadre, solo para su propia historia.
  
  No cuentan: Wikipedia, revistas de curiosidades (Mental Floss), blogs ni foros.
- Cada número y cada **año** de la voz, la pantalla y los captions están en un hecho, una frase o una cifra
  verificada (H4 + V2 sobre `base/datos.json`).
- **Casos de justicia**: presunción de inocencia (vocabulario vetado de `/noticias` sin sentencia firme) y el **estado
  del caso a la fecha de la consulta** de cada persona señalada (`casos[]`).
- **Fotos**: Wikimedia Commons con licencia libre (dominio público, CC0, CC BY, CC BY-SA; nunca NC ni ND; el script
  lee la licencia y arma el crédito), oficial, la og:image del medio con «Foto: medio» o la de prensa de la empresa;
  lado corto ≥ 480 px (aviso < 600); sin víctimas, cadáveres ni menores identificables.
  - **`foto --de-fuente <url>`**: la og:image de una fuente ya leída (`leer` la guarda y la imprime con el comando
    listo; el digesto del verificador lista las de su eje), con «Foto: <medio>» y la fecha de la nota.
  - **La foto del protagonista es obligatoria** (H12; `--protagonista`, o un `--retrato-de` con su nombre): el gancho
    abre con ella. `hechos --check` falla sin ella e imprime las og:image de fuentes leídas que nombran al
    protagonista; `consolidar` también falla; en el Workflow, un verificador la baja antes de los ganchos.
  - **Nunca un icono ni un mapa en lugar de la foto** (decisión del usuario, 2026-10-26, como en `/noticias`): cada
    escena `foto` lleva una foto verificada. Si no hay del hecho, una **de referencia**: el lugar, la institución, la
    persona, el producto o la época (`foto … --referencia`; el crédito dice «Foto de referencia: …» y el chip «De
    referencia» o la época sin año). Si no hay ninguna, ese tramo se cuenta con otra escena (cita, gráfico, golpe).
  - Cada eje trae **≥ 2 fotos** distintas (H7 en `hechos --check`).
  - **Retrato** (`foto --retrato-de "<persona>"`): solo si es de esa persona. Un objeto o un lugar va como foto de
    escena, nunca como retrato de una cita.
  - **Gráfico, cartel o logo con texto**: `foto --encaje contener`, para que el corte a sangre no lo recorte (se ve
    entero sobre el fondo).
  - **Sin repetir**: la misma imagen (sha1) se funde en un id al consolidar y sale en ≤ 2 escenas.
  - **El chip no inventa época**: una foto de 2021 no va bajo «1978»; el chip dice «Foto de 2021», «De referencia» o
    la época sin año.

## Gates (`scripts/historia.py`)

| Gate | Dónde | Qué exige |
|---|---|---|
| H1 forma | `hechos --check` | ids `<eje>-hNN/cNN/qNN`, fecha `YYYY[-MM[-DD]]` y precisión, texto ≤ 240, estado; ≥ 6 hechos publicables al consolidar |
| H2 evidencia | `hechos --check` | cita ≥ 20 caracteres en el texto guardado; año en la cita; números del texto en las citas; la frase literal de cada cita en su fuente; cuatro estados: `confirmado` = 2 grupos que coinciden; `una_fuente` = 1 fuente válida sin contradicción (FALLA si tiene 2 grupos); `en_disputa` = ≥ 1 válida + nota con la diferencia (AVISO si un solo grupo y la nota no describe discrepancia: «¿es una_fuente?»); `tipo_hecho` válido |
| H3 justicia | `hechos --check` · `guion --check` | `casos[]` con estado actual, fecha de consulta y fuente si el encuadre es de justicia; vetadas sin sentencia firme |
| H4 respaldo y atribución | `guion --check` | años y números de voz, pantalla, pasos, resumen y captions en la cronología; los `hechos` citados existen; la voz atribuye o matiza solo si la escena cita un hecho `en_disputa` o con `tipo_hecho` `alegato`, `estimacion` u `opinion`; un hecho `una_fuente` pide `fuente` en pantalla (o `grafico.fuente`) salvo que esa fuente ya se mostró o se nombró en el mismo acto; en una `cita`, la voz dice el autor antes de la frase |
| H5 duración | `guion --check` (V4 ±20 % de 150 s) · `tiempos` | apunta a 150 s (135–165): aviso entre 165 y 170 s estimados, **FALLA por encima de 170 s** (también en `aplicar` y en los retoques: un lote de arreglos que alarga el video no pasa; m052) y aviso si la real pasa de 180 s; 320–400 palabras orientan (AVISO fuera; FALLA fuera de 280–410) |
| H6 pantalla | `guion --check` | titular ≤ 9 palabras, chip ≤ 14, lugar ≤ 24, fuente ≤ 44, cifra ≤ 18 con etiqueta ≤ 30, `grafico` con plantilla y `datos`; tarjetas por `materializar.py` (R1–R6); cita en otro idioma con `traduccion` ≤ 140 que la voz dice |
| H7 fotos | `foto` · `hechos --check` · `guion --check` · `ganchos --check` | archivo, crédito «Foto: …» (o «Foto de referencia: …»), origen, licencia libre de Commons, lado ≥ 480 px; ≥ 2 fotos por eje; el gancho con visual `foto`; cada escena foto con una foto verificada (nunca icono ni mapa); retrato con `retrato_de` = autor de la cita; una imagen en ≤ 2 escenas y **nunca en dos escenas seguidas** (H7b, el gancho y la escena 2 incluidos; decisión del usuario 2026-11-09); chip sin un año anterior a la foto; una foto bajada después de consolidar entra sola a `historia.json` (y a la investigación compartida si es una parte de serie; m120) |
| H7c foto de un proceso | `foto --proceso "<nombre>"` · `guion --check` | una foto con alguien detenido, esposado o en audiencia va solo en la escena cuya voz nombra a esa persona; sin marcar, su descripción («esposado», «audiencia», «tribunal»…) da un aviso para marcarla (m122, 2026-11-09) |
| H24 pantalla = voz | `guion --check` | una cifra en pantalla (`cifra.texto`; en titular o golpe la que lleva moneda, % o «mil/millones»; años fuera) que la voz de la escena no dice falla; un alegato, estimación u opinión con número en pantalla lleva «según…/dice/cuenta» en el titular o la etiqueta (solo con `fuente` en pantalla, aviso) (m124, 2026-11-09) |
| H10 protagonista | `ganchos --check` · `guion --check` | el encuadre trae `protagonista` y el gancho lo nombra (pantalla, línea o voz) |
| H12 foto del protagonista | `foto` · `hechos --check` · `consolidar` · `ganchos --check` · `guion --check` | una foto verificada con `muestra: protagonista` (o `retrato_de` del protagonista); la del gancho lo es |
| H13 reserva | `ganchos --check` · `guion --check` | ningún número escrito en una revelación del encuadre aparece en la pantalla, la línea ni la voz del gancho (sin números, lo juzga el crítico con `reserva`) |
| H14 pago | `guion --check` | `promesa.revela` (1–n) y la escena `promesa.pago` dice esa revelación (una raíz de 5 letras, en voz o pantalla) |
| P1–P4 promesa y bisagra | `guion --check` (de `video.py`) | forma del catálogo, sin anunciar el video, rotación entre piezas, bisagra antes del giro (`referencias/promesas.md`) |
| H11 hilo | `guion --check` · crítico (H-C3) | cada demostrativo con cifra o sustantivo («esos 40 niños», «ese alimento») tiene su antecedente en una escena anterior; `ganchos --usar` sobre un guion ya escrito avisa que se relea el hilo y se vuelva a pedir la crítica |
| H9 cierre | `guion --check` | el `final` del cierre sin «según»: lo último que se oye se apoya en un hecho confirmado |
| H8p paleta | `encuadre --check` (historia, serie, explica) | la paleta sale del tinte del tema (marca, partido, institución, material o lugar) y lo dice `paleta_por_que`; no repite la de las últimas 2 piezas de video de ningún flujo (`paletas_recientes`); `preparar` ya propone una que no repite (decisión del usuario 2026-11-09) |
| H8m música | `encuadre --check` (historia, serie, explica) | `musica_tema` de `video.MUSICA_TEMAS`; `consolidar` elige la pista del tema (catálogo `temas`) usada hace más tiempo en cualquier flujo; la paleta ya no decide la música (decisión del usuario 2026-11-09) |
| H8 estructura | `guion --check` | `acto` 1–3 en cada escena, no decreciente y los tres presentes; `rotulo` válido en la primera escena de los actos 2 y 3 (o `capitulo` con AVISO «prefiere rotulo»); `rotulo` en otra escena o en un tipo vetado → FALLA; `capitulo` 0–2; giro en el acto 2 entre el 40 y el 75 %; ≤ 3 escenas seguidas del mismo tipo; al menos una foto o cita; ≤ 19 escenas; aviso si una escena cuenta un año anterior al del rótulo de su acto (flashback) |
| H15 narración | `guion --check` | `narracion` con 3 entradas `{acto, texto}`; por acto, el texto sin tildes ni signos es igual a las voces de sus escenas (el acto 3 incluye el cierre); imprime el primer punto de divergencia; palabras en rango |
| H16 flujo | `narracion --check` · `guion --check` | ≥ 2 conectores causales o temporales por acto; ≤ 1 escena desde la 2 que abra con atribución («Según…»); dos escenas seguidas no abren con las mismas dos palabras; ≤ 6.5 cortes por minuto |
| H17 hilos | `narracion --check` · `guion --check` | cada `encuadre.hilos[].id` está en `guion.hilos` con `escena` (≥ 3, cuyo `paga` lo incluye) o con `sin_respuesta` (una raíz de 5 letras en la narración del acto 3 o en el cierre) |
| H18 primera mención | `narracion --check` · `guion --check` | cada personaje del encuadre (no el protagonista) lleva ≥ 1 raíz de su `presentacion` en la voz de su primera mención o en la escena anterior |
| H19 «según» | `narracion --check` · `guion --check` | ≤ 4 «según» por video, ≤ 2 por acto, nunca en dos escenas seguidas, nunca la misma fuente dos veces en voz |
| TM1 toma | `guion --check` | la toma existe en `historia.json → tomas`; origen medio, oficial o empresa; crédito «Video: …»; sus hechos son publicables y al menos uno es de la escena (la toma tiene que ver con lo que se narra) |
| TM2 derechos y ritmo | `guion --check` · `toma` | sin audio ≤ 6 s y la voz encima ≤ su duración / 0.7; con audio ≤ 10 s; todas ≤ 25 % de la duración objetivo; ≤ 2 con audio; cada toma una vez; nunca dos con audio seguidas |
| TM3 toma con audio | `guion --check` · `toma` | cita ≥ 4 palabras que casa ≥ 80 % con la transcripción del tramo (o `ambiente`); la voz de entrada nombra a quien habla (un personaje del encuadre o el `--retrato-de` del video) |
| TM4 fecha de la toma | `guion --check` | el chip lleva el año de la toma; si el material es más viejo que el hecho, «Video de archivo»; el año de la toma vale en H4 |
| TM5 secuencia | `guion --check` | una toma con audio cierra su secuencia de voz (las secuencias por defecto se cortan tras ella) |
| TM6 archivos | `tiempos` | los cuadros (`tomas/<id>/00001.jpg…`) y el audio (`tomas/<id>.wav`, −18 LUFS) existen |
| H20 secuencias | `guion --check` | `secuencias` de 2–5 escenas consecutivas, disjuntas, sin la escena 1 ni el cierre, del mismo acto, giro o rótulo solo al inicio; `voz_continua` exige `secuencias`; prompt de cada secuencia ≤ 1,200 caracteres; AVISO si una escena queda fuera de toda secuencia entre dos del mismo acto |

Además corren los de `/video`: V1–V5 y V9 (sin «la escena 2 es T1»; en historia tampoco exige que la voz empiece con
el conector ni que haya `enlace`), F1–F8, V6 (por secuencia: las palabras de Scribe se reparten entre sus escenas; si
no casan, FALLA «rehaz la secuencia (o `voz --sueltas`)»), V7, V8, V10, V11, V12, V13, V15 y V16 (la voz se aprieta
donde ElevenLabs la cortó dentro de un nombre o una cifra). En la mesa de archivo, de esa lista corren V1–V6, V8, V9,
V11 y V16 (más V17–V20 y V23–V25); V7 queda para los clips de tablero, y V10, V12, V13 y V15 los reemplazan los gates
MV del plano (`referencias/flujo-mesa.md` §5 y §7).

El crítico prueba cada arreglo de texto antes de escribirlo con `historia.py probar <TRABAJO> --cambios …` (una copia
sin audio: narracion + guion --check); un arreglo que el gate rechaza va como mejora con la falla, nunca como falta que
bloquea (`probado: false` vuelve al crítico). El guionista devuelve en `arreglos_rechazados` lo que no pudo aplicar.

`probar` y `aplicar` también **insertan una escena** en un guion ya grabado (m108): `{"insertar": N, "escena": {tipo,
texto, …}, "despues_de": "frase literal de la narración"}`. El texto entra en la narración tras esa frase; las escenas
N… corren un lugar (con `promesa.pago` y `bisagra.en/pago`); la secuencia de voz que la escena parte deja de serlo. Con el
gate en verde, `aplicar` corre `voz_N`, `voz_N_r`, `palabras_N` y `escucha_N` de las escenas siguientes (el cierre
incluido), `escucha.json` y `creditos.json`, y rehace `audio/secuencias.json`: la secuencia rota va a `audio/_previo/`.
Las demás voces se conservan; `voz --pendientes --sueltas` pide solo la escena nueva.

## Tensión, imagen y producción (2026-11-10)

| Gate | Qué comprueba |
|---|---|
| H8 `en_juego` | Cada acto del encuadre dice qué se puede perder ahí y a quién alcanza; no se repite entre actos. Que suba lo juzga el crítico. |
| H25 escalera | Cada tercio del video abre o paga algo (promesa, bisagra, giro o un hilo en `paga`). Los hilos no se pagan todos en la misma escena. Aviso: más de 35 s sin ningún peldaño, o ningún hilo pagado antes del último tercio. |
| H26 imagen | Una escena `foto` de más de 12 s estimados falla: se reparte en dos, cada una con la imagen de lo que cuenta. Aviso: menos de una composición distinta (dividida, mini-mapa, subrayado, documento, tarjeta, animación) por cada 4 fotos; ≥ 5 personas en el encuadre sin escena `red`. |
| P6 | La pregunta del video en pantalla (`referencias/promesas.md` §5). |

Un trabajo con fecha anterior al 2026-11-10 recibe H25, H26 y P6 como aviso.

(Motor propio: el tope de 12 s de una foto fija y las «composiciones distintas» de H26 miden el dibujo viejo. En la
mesa, cuánto dura cada pieza y cuánta variedad hay lo miden MV5, MV6 y MV8 sobre el plano.)

Una escena `foto` admite `ruta` (2–4 departamentos en orden): el localizador se acerca y un trazo los une (H26 revisa
que existan y sean distintos).

(Motor propio: las páginas y el dibujo de `vias` y de las demás escenas con archivos reales, abajo. En la mesa, `vias`,
`deptos`, `lupa` y `cortina` son tableros: el mismo clip, limpio, solo en su mesa, recortado a la columna central;
`pagina`, `archivo` y `bandos` dan piezas a su mesa: la página con la frase subrayada, las fotos, las fichas de
persona. Sus gates H27–H33 sobre el guion valen igual.)

**La escena `vias` (2026-11-12): el mapa vial real, por capas.** Dibuja la red de calles de una ciudad tomada de
OpenStreetMap (`design/vias/<id>.json`; la arma `scripts/build_vias.py` desde la receta `<id>.fuente.json` y queda en el
repositorio: el video no llama a ningún servicio) y la anima con 2–6 `capas`, una por frase de la voz. Cada capa entra
cuando la voz dice su `dice` y puede:

- encender `arterias` (su trazo real crece del centro hacia afuera; `sentido: "entra"` lo invierte; `nivel` 0–1 dice
  hasta dónde: la misma arteria en dos capas crece de un nivel al otro);
- marcar un `lugar` con su aro y su rótulo, con una `etiqueta` corta;
- poner el dato de arriba (`cifra` + `rotulo`);
- inflar una `burbuja` en un lugar (área ∝ valor; el mismo lugar en dos capas crece);
- encender la vía del tren (`riel`);
- mover la cámara (`zoom` a un lugar o `"todo"`; `acerca` 1.4–4). La cámara solo se mueve cuando una capa lo pide.

Lo de la capa que suena va en el acento; lo anterior queda en crema. Todo queda quieto entre capas (A1). El pie lleva la
fuente y «Mapa: © colaboradores de OpenStreetMap» (licencia ODbL). Página `video/vias.html`, en 9:16 y 4:5 (el 16:9 la
muestra dentro del escenario). Se prueba sin sesión con `python3 scripts/escena_prueba.py vias`, que la arma con el
constructor real sobre los casos de `sesiones/_fixture_escenas/vias.json` y mide pureza, V13, A3 y A1.

| Gate | Qué exige |
|---|---|
| H27 | Escena `vias`: la red existe en `design/vias/`; título de un renglón (≤ 30); 2–6 capas, cada una con su `dice` (sin cifras) que suena en la voz y en orden, y con algo que mostrar; arterias, lugares y zoom son ids de la red; cada número en pantalla (cifra, rótulo, etiqueta, título, valor de la burbuja) con respaldo y cada año en un hecho; con un dato en pantalla, `fuente`; ≥ 1.6 s de voz por capa y la primera suena en el primer 35 % de la voz; ≤ 2 por video. |

**Las demás escenas con archivos reales (2026-11-12).** Todas siguen el patrón de `vias`: lo que entra en pantalla lo
dispara un `dice` (la palabra o el nombre que la voz dice, sin cifras, en orden), lo que suena va en el acento y lo
anterior en crema, la cámara solo se mueve cuando la escena lo pide y todo queda quieto entre entradas (A1). Cada número
en pantalla lleva respaldo y cada foto es una foto verificada de `historia.json`.

| Escena | Qué es | Página | Gate |
|---|---|---|---|
| `lupa` | Una foto real que se interroga punto por punto (`puntos` con `x`, `y` en 0–1 y una etiqueta). Estilo `puntos`: la cámara se acerca y un velo apaga el resto. Estilo `pistas`: las etiquetas se quedan (la anatomía de un objeto). | `video/lupa.html` | H28 |
| `deptos` | El mapa de los 22 departamentos por `capas`: departamentos que se encienden, `arco` desde el de la capa anterior (el viaje de algo), `onda` (un anillo que sale de un departamento y va encendiendo a los demás), dato de arriba y `zoom`. | `video/deptos.html` | H29 |
| `pagina` | La página real de un documento con la frase subrayada en su sitio. `historia.py pagina <TRABAJO> --id … --url <PDF ya leído> --frase «…»` saca la imagen de la página y la caja de cada renglón (necesita poppler). La voz lee la frase y el marcador la recorre a su paso. | `video/pagina.html` | H30 |
| `cortina` | Antes y ahora: dos fotos reales del mismo lugar; una cortina descubre la segunda cuando la voz dice el `dice`. | `video/cortina.html` | H31 |
| `archivo` | Varias piezas reales, una por frase. Estilos: `tira` (línea de tiempo con fotos), `capas` (recortes que caen uno sobre otro), `mesa` (las pruebas sobre una mesa; la cámara va de una a otra), `conteo` (una foto por cada cosa que se cuenta) y `barras` (una serie que sube sobre la foto). | `video/archivo.html` | H32 |
| `bandos` | Las personas toman partido en dos columnas (quién votó a favor y quién en contra), con su retrato; `umbral` opcional (la barra de lo alcanzado frente a lo que hacía falta). | `video/bandos.html` | H33 |

`vias` admite además `carrera {arteria, veces}` en una capa: dos puntos hacen el mismo viaje hacia el centro, uno sin
tráfico y el de hoy, que tarda `veces` más (`veces` con respaldo).

| Gate | Qué exige |
|---|---|
| H28 | `lupa`: foto verificada; título ≤ 30; 2–5 puntos con `x`, `y` entre 0 y 1, etiqueta ≤ 28 y su `dice` en la voz y en orden; ≥ 1.8 s de voz por punto. |
| H29 | `deptos`: 2–6 capas; `deptos` son departamentos que existen (1–6 por capa); `arco` pide una capa anterior con departamentos; `zoom` es un departamento o «todo»; con un dato, `fuente`; ≥ 1.6 s por capa; ≤ 2 por video. |
| H30 | `pagina`: la página existe en `paginas.json` con 1–5 renglones; `fuente` (de quién es el documento); la voz lee la frase tal como está; ≤ 2 por video. |
| H31 | `cortina`: dos fotos verificadas y distintas; dos etiquetas ≤ 14 con sus años en un hecho; el `dice` suena pasado el 20 % de la voz; 1 por video. |
| H32 | `archivo`: estilo válido; piezas con fotos verificadas y distintas (tira y capas 2–5, mesa 3–4; ≥ 2.2 s por pieza); `conteo` con `cuenta` 2–24 con respaldo y `unidad`; `barras` 2–6 con valores con respaldo y `fuente`; ≤ 2 por video. |
| H33 | `bandos`: dos lados con nombre ≤ 16; 2–6 personas del encuadre con retrato, ≤ 3 por lado y al menos una en cada uno; `umbral` con sus números con respaldo; 1 por video. |

Las siete se prueban sin sesión con `python3 scripts/escena_prueba.py <tipo>` (o `--todas`): cada caso de
`sesiones/_fixture_escenas/<tipo>.json` se arma con su constructor real sobre una voz falsa y se graba dos veces en 9:16
(mismos cuadros: `seek(t)` puro) y una en 4:5, con V13, A3 y A1. En 16:9 se muestran dentro del escenario.

La escena `red` admite `estilo: "tablero"` (`video/tablero.html`): los mismos nodos y aristas y el mismo gate H23,
como tablero de investigación con cuadritos e hilos, sin tachas. En 9:16, 4:5 y 16:9. (Motor propio: en la mesa los dos
estilos se dibujan igual, como la jerarquía de personas de la pieza `red`.)

`historia.py producir <TRABAJO> [--solo n] [--sin-escucha]` corre la cadena tiempos → escuchar → grabar → montar →
revisar en 9:16 y luego grabar → montar → revisar en 4:5, y para en la primera falla. En la mesa añade `plano --check
--hoja` después de la escucha y se detiene con «falta la fase Plano» si el TRABAJO no tiene `plano.json`; `--solo` es
del motor propio.

### Producción en la mesa (2026-11-14)

- **Plano**: `Workflow({ name: "plano", args: { trabajo: "<TRABAJO>" } })` tras `tiempos` con la voz real. El
  `video-realizador` parte de `historia.py plano <TRABAJO> --digesto`, escribe `plano.json` y deja `plano --check
  --hoja` en 0. Devuelve `plano_listo` (la sesión muestra `plano.md` y sigue) o `plano_pendiente` con sus fallas.
- **`grabar`**: los gates del plano, los tableros limpios, el proyecto de HyperFrames (`TRABAJO/hf/<9x16|4x5>/`),
  `hyperframes check` y el render con **un solo proceso** (≈ 1.6× la duración por formato: ≈ 4 min para 2.5 min de
  video; los dos formatos van en fila). No hay `grabar --solo`: si cambia una voz o el plano, se graba entero.
- **`montar`**: una sola mezcla de audio para los dos formatos (voz, música, efectos del plano, −14 LUFS), el `.srt`,
  `caption.md` y la portada limpia (el cuadro del gancho sin subtítulos ni barra). El 4:5 se monta después del 9:16.
- **`revisar`**: la hoja de contacto del video final (`revision/contacto.png`, `contacto_4x5.png`).
- La versión B del gancho (`variante`) aún no existe en la mesa.

## Voz y costos

Como `/noticias`, pero por **nodo**: una secuencia de 2–5 escenas o una escena suelta; 1 toma, Scribe por nodo y la
llamada de estado que lee `historia.py descargar --estado`. Las herramientas aceptan ≤ 20 ids por llamada: el estado
final va en lotes (cada voz con su Scribe) y `descargar --estado A B …` recibe todos. Con pocos nodos el MCP devuelve
el estado en el chat y no en un archivo: pide el estado con las sesiones de dos partes a la vez (pasa de ~50k caracteres
y queda en archivo) y pásalo entero a `descargar` de cada parte: las voces y los Scribe de la otra parte se ignoran con
un aviso (m129); una generación sin `modality`/`status`/`content_url` nunca se salta en silencio (m105). Las cifras con dinero van con
prefijo (`US$1.15`, `Q2.50`; también se entiende «1.15 dólares»): la voz dice «un dólar con quince centavos». ≈ 1
crédito por carácter: **≈ 1,800–2,600** en una historia de 2–3 min (`locucion.json → caracteres`). El Workflow cuesta
0 créditos (≈ 13–18 agentes, 20–40 min).

### Voz por secuencias

- Un nodo TTS por secuencia (`locucion.json → secuencias[{k, escenas, prompt, caracteres}]`; `voz_continua: true` por
  defecto en historia): la entonación no se reinicia en cada escena. `voz <TRABAJO>` imprime un `prompt` por nodo
  (las voces de la secuencia unidas, cada una con su puntuación final; ≤ 1,200 caracteres).
- `descargar --estado` reconoce el prompt de cada secuencia, baja `audio/voz_sec_K.mp3` + `palabras_sec_K.json` y la
  **corta en sus escenas** con los tiempos de Scribe (a mitad del silencio entre la última palabra de una y la primera
  de la siguiente): `voz_N.mp3` y `palabras_N.json` de siempre, más `audio/secuencias.json {K: {escenas, cortes_s,
  generacion_id}}`. Con un prefijo de prompt ambiguo exige `media[].prompt` entero. `partir <TRABAJO> [--secuencia K]`
  repite el corte.
- Dentro de una secuencia la cola entre escenas es 0.3 s (0.7 en la frontera), la transición es `fade`, los
  subtítulos siguen y los efectos van solo en la frontera, el giro y los golpes (≈ 17 por video, no 45). (Motor
  propio: en la mesa no hay transiciones entre escenas y los efectos salen del plano.)
- Retomas: `voz --pendientes` marca la **secuencia entera** si cambió una de sus escenas (e imprime sus créditos);
  `voz --sueltas` emite solo las escenas cambiadas como nodos propios (el retroceso si V6 no casa en la frontera).
  Mismos créditos por carácter.

## Archivos del trabajo

`encuadre.json` (editor: actos, espina, hilos, personajes, periodos, ejes) · `hallazgos_<eje>.json` (investigadores)
· `verificacion_<eje>.json` y `fotos/<id>.jpg|json` (verificadores) · `historia.json` (`consolidar`: hechos ordenados
con estado y `tipo_hecho`, cifras, citas, fotos, casos, descartados, conflictos, más actos, espina, hilos y
personajes) · `base/` (hilo base) · `ganchos.json`, `seleccion.json` · `guion.json` (`narracion`, `hilos`,
`secuencias`, escenas con `acto`) · `oyente.json` (oyente ingenuo) · `critica.json` · luego lo de `/video`:
`locucion.json` (con `secuencia` y `cola` por escena), `audio/` (con `voz_sec_K.mp3` y `secuencias.json`),
`escenas.json`, `clips/`, `salida/`, `revision/`. En la mesa, además: `video.json` con `"realizacion": "mesa"`,
`plano.borrador.json` (lo que el script propone desde las escenas), `plano.json` (el realizador), `plano.md` (la hoja
de golpes) y `hf/<9x16|4x5>/` (el proyecto de HyperFrames de cada formato).

## Retoques

Cuando el usuario pide un cambio después de la crítica o de la voz (otro gancho, reescribir una escena, otro cierre,
quitar una cita), nadie edita `guion.json` a mano: el Workflow `historia` con `args {trabajo, tema, desde: "retoque",
notas: "<lo que pidió>"}` salta a Guion, el guionista aplica solo eso conservando las voces grabadas (y el mismo tramo
de la narración, H15), y vuelven a correr los gates, el oyente, la crítica (1 vuelta, acotada a las escenas que
cambiaron: lo demás que el oyente encuentre va como mejora), las mejoras y la animación;
devuelve `voces_cambiadas`. Después, `historia.py voz <TRABAJO> --pendientes` imprime las **secuencias enteras** que
hay que regrabar (y los créditos aproximados) o, con `--sueltas`, solo las escenas cambiadas como nodos propios: se
generan esos, `descargar --estado`, `tiempos`, `escuchar`, `grabar --solo n,…` (9:16 y 4:5), `montar`, `revisar`,
`entregar` y `memoria.py --historia` (reemplaza el registro del mismo slug).

**En la mesa** hay dos clases de retoque. Uno **de pantalla** (otra pieza, otra foto, quitar un recorte, otro golpe de
arriba, un texto que no da tiempo de leerse) no toca el guion ni la voz: Workflow `plano` con `args.notas`, y luego
`grabar`, `montar` y `revisar` en los dos formatos. Uno **de texto o de voz** sigue el camino de arriba hasta `escuchar`
y después repite `plano <TRABAJO> --check --hoja` (los `dice` del plano son palabras de la voz: lo que falle en las
escenas que cambiaron se arregla con el Workflow `plano` y sus `notas`) y vuelve a grabar **entero**: no hay `grabar
--solo` en la mesa.

Otros dos puntos de entrada: `desde: "encuadre"` vuelve a contar por actos una cronología ya verificada (el editor
re-encuadra con `digesto --para editor`: conserva tema, slug, protagonista, revelaciones, fotos_clave, ejes,
periodos, paleta, sensibles y no_afirma, y añade actos, espina, hilos y personajes; luego salta a Guion) y
`desde: "guion"` salta directo a Guion. Los dos exigen `historia.json`, `ganchos.json` y `seleccion.json`.
`hechos --reclasificar [--aplicar]` propone pasar a `una_fuente` cada `en_disputa` de un solo grupo cuya nota no
describe discrepancia (para rehacer una historia vieja sin créditos).

## Entrega y registro

- `historia.py entregar TRABAJO` → `historias/<fecha>-<slug>/`:
  - `video.mp4` (TikTok, Reels, Shorts), `video_4x5.mp4` (feed), `caption.md`, `subtitulos.srt`, portadas y hojas de
    contacto;
  - `fuentes.md`: por acto, cada hecho con sus urls (etiquetas *(una fuente: X)* y *(en disputa)*), más las fotos con
    crédito y licencia;
  - `cronologia.md`: la línea de tiempo de lo que cuenta el video, con su estado;
  - el `guion.json` de entrega.
  
  Las fotos no se copian (son de terceros) y los mp4 están fuera de git.
- `memoria.py --historia historias/<fecha>-<slug>` → `memoria/historias.json`. `historia.py` lo lee para:
  - avisar si la historia ya se contó;
  - rotar la familia y el visual del gancho, el cierre, las animaciones y la música;
  - las frases ya usadas (C11).
  
  M10 lo valida.

## Prueba sin web ni créditos

`make historia-fixture` (maqueta: `sesiones/_fixture_historia/`, una panadería **inventada** con fuentes de ejemplo
guardadas, fotos dibujadas con ffmpeg y voz falsa; 9:16 y 4:5 en `sesiones/_fixture_historia/trabajo/salida/`).
La maqueta corre en la mesa con `MESA_RENDER=0`: pasa los gates del plano y `hyperframes check`, y el video es un doble
sin render de la duración exacta (no se puede entregar). `make serie-fixture` hace lo mismo; el render real lo prueba
`make video-fixture-mesa` (`sesiones/_fixture_mesa/`).
