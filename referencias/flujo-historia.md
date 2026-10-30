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
                     → video-gancho en modo historia (4–5 candidatos con la foto del protagonista) → gate ganchos --check
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
→ tiempos (V16, V6, V10) → escuchar (V11) → grabar (V7, V13) → montar (V8) → revisar (9:16 y 4:5)
→ entregar (historias/<fecha>-<slug>/) → memoria.py --historia (memoria/historias.json) → make validate (M10)
```

`scripts/historia.py` hace lo propio de la historia y escribe el **mismo TRABAJO que `/video`**: arma en
`TRABAJO/base/` un «hilo base» (`hilo.json` con el tema y la tesis, `datos.json` con las cifras y los números de los
hechos verificados, y las tarjetas `tuit_N.html` materializadas con `scripts/materializar.py` desde el `grafico` de
cada escena), así el gate del guion, los ganchos, los tiempos y el render salen de `scripts/video.py`, con las escenas
propias enchufadas por sus extensiones (`CONSTRUCTORES`, `TRANSICION_DE`, `SIN_HUECO`). Las páginas son
`video/noticia.html` (gancho con foto y escena `foto`), `video/historia.html` (`cita` y `capitulo`) y las de `/video`
para el resto; el **rótulo de acto** lo dibuja `video/comun.js` sobre cualquiera de ellas mientras la voz sigue.

## Formato (decisiones del usuario, 2026-10-24 y 2026-10-27)

Una historia se cuenta en **tres actos**, no en capítulos por año. El **planteamiento** presenta el mundo y al
protagonista y termina en el **detonante** (lo que lo cambia todo). El **nudo** sube la apuesta: el **punto medio**
cambia lo que el espectador creía saber y el **giro** (`giro: true`) va aquí. El **desenlace** trae el **clímax** y
la **resolución**: qué quedó, y qué nunca se supo. Los actos 2 y 3 se marcan con un **rótulo** (año y ≤ 4 palabras)
dibujado sobre la primera escena del acto mientras la voz sigue; una tarjeta de capítulo que detiene la voz es la
excepción. El editor escribe la espina (detonante, punto medio, clímax, resolución) con los ejes que la sostienen; el
guionista cuelga las escenas de esa espina. Y antes de colgar nada escribe la **narración de corrido** (320–400
palabras ≈ 150 s a 145 palabras por minuto): las escenas la reparten sin cambiar una palabra (H15).

| Bloque | Qué | Gate |
|---|---|---|
| E1 gancho (≤ 7.5 s) | **siempre una foto a sangre del protagonista** que cubre toda la pantalla (visual `foto`, como la Cajita Feliz; H12); el momento más fuerte de la historia (el problema que la hizo nacer, la persona, la decisión), **nombra al protagonista** (la marca, la persona: `protagonista` del encuadre), en medias res, **nunca una revelación** del encuadre (lo que el video paga: de qué está hecho, cómo terminó; H13 veta sus números, el crítico puntúa `reserva`); se lee en silencio; «Guatemala» en ≤ 6 s; sin «Esta es la historia de…» | `ganchos --check` (R1–R9, R11–R12; sin R10; H7 visual foto; H10, H12, H13) |
| promesa | una oración propia en la escena 2 que nombra qué falta saber; `revela` dice qué revelación paga y la escena `pago` (último tercio) la cuenta con sus palabras | V9 · H14 |
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
animación de la biblioteca `video/animaciones/`: `cadena`, `cronologia`, y las que el animador vaya creando) y
`cierre`. ≤ 3 seguidas del mismo tipo. ≤ 19 escenas más el cierre. `enlace` (pero | por_eso | y) es opcional y solo
decide el efecto de la entrada: la voz no tiene que empezar con el conector (la causalidad vive en la narración).
Topes de voz: foto 40–280, cita 30–280, tarjeta/mapa/ranking/tiempo/explica 40–260, golpe 20–130, capitulo 10–90.

**Cómo se ve** (estilo Noche, `referencias/diseno/sistema.md`; lo mismo que `/video` y `/noticias`):
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
| H5 duración | `guion --check` (V4 ±20 % de 150 s) · `tiempos` | 120–180 s estimados; aviso si el estimado pasa de 165 s (apunta a 150, 135–165) y si la real pasa de 180 s; 320–400 palabras orientan (AVISO fuera; FALLA fuera de 280–430) |
| H6 pantalla | `guion --check` | titular ≤ 9 palabras, chip ≤ 14, lugar ≤ 24, fuente ≤ 44, cifra ≤ 18 con etiqueta ≤ 30, `grafico` con plantilla y `datos`; tarjetas por `materializar.py` (R1–R6); cita en otro idioma con `traduccion` ≤ 140 que la voz dice |
| H7 fotos | `foto` · `hechos --check` · `guion --check` · `ganchos --check` | archivo, crédito «Foto: …» (o «Foto de referencia: …»), origen, licencia libre de Commons, lado ≥ 480 px; ≥ 2 fotos por eje; el gancho con visual `foto`; cada escena foto con una foto verificada (nunca icono ni mapa); retrato con `retrato_de` = autor de la cita; una imagen en ≤ 2 escenas; chip sin un año anterior a la foto |
| H10 protagonista | `ganchos --check` · `guion --check` | el encuadre trae `protagonista` y el gancho lo nombra (pantalla, línea o voz) |
| H12 foto del protagonista | `foto` · `hechos --check` · `consolidar` · `ganchos --check` · `guion --check` | una foto verificada con `muestra: protagonista` (o `retrato_de` del protagonista); la del gancho lo es |
| H13 reserva | `ganchos --check` · `guion --check` | ningún número escrito en una revelación del encuadre aparece en la pantalla, la línea ni la voz del gancho (sin números, lo juzga el crítico con `reserva`) |
| H14 pago | `guion --check` | `promesa.revela` (1–n) y la escena `promesa.pago` dice esa revelación (una raíz de 5 letras, en voz o pantalla) |
| H11 hilo | `guion --check` · crítico (H-C3) | cada demostrativo con cifra o sustantivo («esos 40 niños», «ese alimento») tiene su antecedente en una escena anterior; `ganchos --usar` sobre un guion ya escrito avisa que se relea el hilo y se vuelva a pedir la crítica |
| H9 cierre | `guion --check` | el `final` del cierre sin «según»: lo último que se oye se apoya en un hecho confirmado |
| H8 estructura | `guion --check` | `acto` 1–3 en cada escena, no decreciente y los tres presentes; `rotulo` válido en la primera escena de los actos 2 y 3 (o `capitulo` con AVISO «prefiere rotulo»); `rotulo` en otra escena o en un tipo vetado → FALLA; `capitulo` 0–2; giro en el acto 2 entre el 40 y el 75 %; ≤ 3 escenas seguidas del mismo tipo; al menos una foto o cita; ≤ 19 escenas; aviso si una escena cuenta un año anterior al del rótulo de su acto (flashback) |
| H15 narración | `guion --check` | `narracion` con 3 entradas `{acto, texto}`; por acto, el texto sin tildes ni signos es igual a las voces de sus escenas (el acto 3 incluye el cierre); imprime el primer punto de divergencia; palabras en rango |
| H16 flujo | `narracion --check` · `guion --check` | ≥ 2 conectores causales o temporales por acto; ≤ 1 escena desde la 2 que abra con atribución («Según…»); dos escenas seguidas no abren con las mismas dos palabras; ≤ 6.5 cortes por minuto |
| H17 hilos | `narracion --check` · `guion --check` | cada `encuadre.hilos[].id` está en `guion.hilos` con `escena` (≥ 3, cuyo `paga` lo incluye) o con `sin_respuesta` (una raíz de 5 letras en la narración del acto 3 o en el cierre) |
| H18 primera mención | `narracion --check` · `guion --check` | cada personaje del encuadre (no el protagonista) lleva ≥ 1 raíz de su `presentacion` en la voz de su primera mención o en la escena anterior |
| H19 «según» | `narracion --check` · `guion --check` | ≤ 4 «según» por video, ≤ 2 por acto, nunca en dos escenas seguidas, nunca la misma fuente dos veces en voz |
| H20 secuencias | `guion --check` | `secuencias` de 2–5 escenas consecutivas, disjuntas, sin la escena 1 ni el cierre, del mismo acto, giro o rótulo solo al inicio; `voz_continua` exige `secuencias`; prompt de cada secuencia ≤ 1,200 caracteres; AVISO si una escena queda fuera de toda secuencia entre dos del mismo acto |

Además corren los de `/video`: V1–V5 y V9 (sin «la escena 2 es T1»; en historia tampoco exige que la voz empiece con
el conector ni que haya `enlace`), F1–F8, V6 (por secuencia: las palabras de Scribe se reparten entre sus escenas; si
no casan, FALLA «rehaz la secuencia (o `voz --sueltas`)»), V7, V8, V10, V11, V12, V13, V15 y V16 (la voz se aprieta
donde ElevenLabs la cortó dentro de un nombre o una cifra).

El crítico prueba cada arreglo de texto antes de escribirlo con `historia.py probar <TRABAJO> --cambios …` (una copia
sin audio: narracion + guion --check); un arreglo que el gate rechaza va como mejora con la falla, nunca como falta que
bloquea (`probado: false` vuelve al crítico). El guionista devuelve en `arreglos_rechazados` lo que no pudo aplicar.

## Voz y costos

Como `/noticias`, pero por **nodo**: una secuencia de 2–5 escenas o una escena suelta; 1 toma, Scribe por nodo y la
llamada de estado que lee `historia.py descargar --estado`. Las herramientas aceptan ≤ 20 ids por llamada: el estado
final va en lotes (cada voz con su Scribe) y `descargar --estado A B …` recibe todos. Las cifras con dinero van con
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
  subtítulos siguen y los efectos van solo en la frontera, el giro y los golpes (≈ 17 por video, no 45).
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
`escenas.json`, `clips/`, `salida/`, `revision/`.

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
