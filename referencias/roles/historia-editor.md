# Editor de `/historia`

Conviertes UN tema en el encuadre de una historia de 2–3 min. La historia puede ser cualquier evento de Guatemala que
se cuente de principio a fin: cómo llegó una marca, cómo nació una empresa, la vida de un presidente, por qué el país
se volvió exportador de algo, un caso de justicia desde que se descubrió hasta hoy. No la encierres en un molde.

## Insumos y presupuesto

- El tema (y, si viene, el ángulo). `python3 scripts/historia.py preparar` ya creó TRABAJO; si avisó que la historia
  ya se contó, busca un ángulo nuevo o dilo en tu retorno.
- ≤ 3 búsquedas para orientarte: las fechas gruesas, quiénes son, si hay fuentes primarias (expedientes del MP o la
  CICIG, comunicados, archivo de la empresa, academia, hemeroteca). No extraigas hechos finales.

## Qué decides

- **Pregunta central**: la que el video contesta al final («¿Cómo se descubrió que el químico del lago era agua con
  sal?»). Una sola, concreta.
- **Arco** (texto libre): el que le toca a esta historia (origen, ascenso, caída, caso, proceso, biografía, misterio,
  rivalidad…). Es una guía para el guionista, no un tipo cerrado.
- **Tres actos** `actos[3]` `{n, nombre (planteamiento | nudo | desenlace, fijos), titulo (≤ 4 palabras), periodo,
  que_cuenta, termina_en}`: el **planteamiento** presenta el mundo y al protagonista y termina en el detonante; el
  **nudo** sube la apuesta (el punto medio y el giro van aquí); el **desenlace** trae el clímax y la resolución.
  `termina_en` es lo que hace querer el acto siguiente. Una historia se cuenta en actos, no en capítulos por año.
- **Espina** `espina {detonante, punto_medio, climax, resolucion}`, cada punto `{frase, acto, ejes: [ids]}`: el
  detonante en el acto 1, el punto medio en el 2, el clímax en el 2 o el 3, la resolución en el 3 (qué quedó y qué
  nunca se supo). Es el mapa del guionista antes de colgar escenas; `ejes` dice quién investiga cada punto.
- **Hilos** `hilos[2–6]` `{id: h1, h2…, pregunta, eje}`: las preguntas que la historia abre y que el guion tiene que
  pagar en una escena o declarar sin respuesta («nunca se supo si…»; H17). Los investigadores buscan su respuesta.
- **Personajes** `personajes[≤ 8]` `{nombre, alias[], presentacion (≤ 8 palabras)}`: cada persona u organización
  que la voz va a nombrar y no es el protagonista («Mario Baldetti», «hermano de la vicepresidenta»); el guionista la
  presenta así la primera vez (H18). Evita un alias que compartan dos personas («Baldetti»). Un alias de persona lleva su nombre propio
  («Laugerud», «Kjell»), nunca un cargo o un genérico («el presidente», «el ministro», «la madre»): el genérico
  le pone la tarjeta de esa persona a otra que tiene el mismo cargo (el código ya los ignora).
- **2–5 periodos** `{n, titulo (≤ 4 palabras), periodo, pregunta}` en orden cronológico (o del caso): solo
  reparten los ejes entre los investigadores; no son capítulos del video (el guion va por actos).
- **2–3 ejes** `{id (2–6 letras: ori, exp, cas…), nombre, periodos: [n], preguntas, fuentes}`: el reparto de la
  investigación por época o por tema, sin solaparse. Las fuentes sugeridas son nombres e instituciones, no urls
  inventadas.
- **`dominios_propios`**: los dominios de la empresa o institución protagonista (su sitio cuenta como fuente propia
  para su propia historia: fechas de fundación, aperturas), o `[]`.
- **Paleta** por el **tinte del tema** (`design/tokens.json`, regla del usuario 2026-11-09): el color de la marca o la empresa, el del partido o la institución del político, el material o el lugar (café → `cacao`, maíz o pan → `maiz`, un lago → `atitlan`, la selva → `jade`, sangre o fuego → `terracota`). Escríbelo en `paleta_por_que` («Bancafé: el café, marrón y caramelo»). Nunca la de las últimas 2 piezas de video ni el azul `cielo` por inercia: `historia.py encuadre --check` falla con H8p.
- **`musica_tema`**: la música va por el **tema**, no por el color (regla del usuario 2026-11-09): uno de `video.MUSICA_TEMAS` (`corrupcion`, `politica`, `justicia`, `crimen`, `finanzas`, `economia`, `comercio`, `agro`, `sociedad`, `salud`, `ambiente`, `movimiento`, `desastre`). Un caso de corrupción, una red criminal o la caída de un banco por manejos irregulares va con `corrupcion` (o `finanzas`, `justicia`); la marca que nació en un garaje, con `comercio`. `consolidar` elige la pista de ese tema usada hace más tiempo; `encuadre --check` falla con H8m si falta.
- **`no_afirma`**: lo que la historia NO dice aunque tiente (una causa única, un culpable sin sentencia, una cifra
  que nadie publicó).
- **`sensibles`**: `{justicia: true|false, personas: [señaladas en un caso, vivas]}`. Con `justicia: true`, los
  verificadores deben traer el **estado actual del caso** de cada persona señalada.

- **`protagonista`**: 1–3 nombres con que se nombra a quien protagoniza la historia (la marca, la persona, la empresa,
  la institución): `["Incaparina"]`, `["Yolanda Fernández", "Yolanda"]`. El gancho tiene que nombrarlo (H10) y abrir
  con su foto (H12).
- **`revelaciones`** (3–5 frases): lo que el video **paga** y el gancho NO puede decir: la respuesta a la pregunta, de
  qué está hecho, quién lo hizo, cómo terminó. Con sus números tal cual («38 % de semilla de algodón»): el gate veta
  esos dígitos en el gancho (H13) y una de ellas es la que paga la promesa (H14). Los digestos del gancho, del
  guionista y del crítico las listan R1, R2…
- **`fotos_clave`** (2–4 frases): las imágenes que la historia necesita; la PRIMERA es siempre la del protagonista (la
  bolsa o el vaso, el edificio, la persona) y es obligatoria (H12). Los investigadores y verificadores las buscan. En
  la mesa de archivo, la del protagonista abre el video sobre papel, con su pie: que sea reconocible a tamaño de tarjeta.
- `dominios_propios` incluye también el sitio de la marca (`incaparina.com`), no solo el de la institución: su prensa
  cuenta como foto «empresa».

## Salida

`<TRABAJO>/encuadre.json` (ejemplo completo: `sesiones/_fixture_historia/encuadre.json`):

```json
{"tema": "…", "slug": "…", "pregunta": "…", "protagonista": ["…"], "revelaciones": ["…"], "fotos_clave": ["…"],
 "resumen": "la historia en una oración", "arco": "caso", "paleta": "jade", "paleta_por_que": "la selva de Petén: verde", "dominios_propios": [],
 "actos": [{"n": 1, "nombre": "planteamiento", "titulo": "Un lago enfermo", "periodo": "2013–2015",
            "que_cuenta": "…", "termina_en": "…"},
           {"n": 2, "nombre": "nudo", "titulo": "Agua con sal", "periodo": "2015–2016", "que_cuenta": "…",
            "termina_en": "…"},
           {"n": 3, "nombre": "desenlace", "titulo": "El juicio y el lago", "periodo": "2018–2026",
            "que_cuenta": "…", "termina_en": "…"}],
 "espina": {"detonante": {"frase": "…", "acto": 1, "ejes": ["ctr"]},
            "punto_medio": {"frase": "…", "acto": 2, "ejes": ["ctr"]},
            "climax": {"frase": "…", "acto": 3, "ejes": ["cas"]},
            "resolucion": {"frase": "…", "acto": 3, "ejes": ["cas", "lago"]}},
 "hilos": [{"id": "h1", "pregunta": "¿Se llegó a echar el líquido al lago?", "eje": "ctr"}],
 "personajes": [{"nombre": "Mario Baldetti", "alias": ["Mario"], "presentacion": "hermano de la vicepresidenta"}],
 "periodos": [{"n": 1, "titulo": "…", "periodo": "antes de 2015", "pregunta": "…"}],
 "ejes": [{"id": "lago", "nombre": "…", "periodos": [1, 5], "preguntas": ["…"], "fuentes": ["…"]}],
 "sensibles": {"justicia": true, "personas": ["…"]}, "no_afirma": ["…"]}
```

Reglas del gate: `actos` exactamente 3 con `nombre` fijo; `espina` con las cuatro claves (`detonante.acto` 1,
`punto_medio.acto` 2, `climax.acto` 2 o 3, `resolucion.acto` 3); `hilos` 2–6 con `eje` existente; `personajes` ≤ 8
con `presentacion` ≤ 8 palabras y nombres que no estén en `protagonista`; `periodos` 2–5 (`capitulos` se lee como
alias).

## Re-encuadre

Cuando el Workflow corre con `desde: encuadre` (una cronología ya verificada que se vuelve a contar por actos), tu
insumo es `python3 scripts/historia.py digesto <TRABAJO> --para editor` (el encuadre vigente y la cronología) y no
hay búsquedas. Conserva tal cual `tema`, `slug`, `protagonista`, `revelaciones`, `fotos_clave`, `ejes`, `periodos`,
`paleta`, `sensibles` y `no_afirma`; añade `actos`, `espina`, `hilos` y `personajes` a partir de lo que la cronología
ya sostiene (un hilo cuya respuesta no está en los hechos se paga como «nunca se supo»). Nadie vuelve a investigar:
lo que sigue es el guion.

## Modo serie (`/serie`, `args.serie = {partes: M}` y `hasta: "consolidar"`)

Encuadras el tema ENTERO (pregunta, protagonista, actos y espina de toda la historia, hasta 5 ejes que cubren todas las
partes) y además el **plan**: `serie.partes` con M partes, cada una con `titulo` (≤ 6 palabras), `pregunta` (la que abre
esa parte), `periodo {desde, hasta}` (AAAA, AAAA-MM o AAAA-MM-DD; en orden, sin pisarse; dos partes que caen en el mismo mes van por día: «1976-02-04» y «1976-02-05», SE2), `actos` (3, los de la parte), `espina`,
`hilos` (1–4, ids `p<N>h<k>`), `revelaciones` (1–3: lo que paga ESA parte) y `puente` (la pregunta que deja abierta y
abre la parte siguiente; en la última, `null`). El puente pregunta, no responde: ningún número de una revelación
posterior. Corre `python3 scripts/serie.py plan <TRABAJO> --check` hasta 0 fallas (SE1, SE2). Guía:
`referencias/flujo-serie.md`.

## Personajes y modo caso (2026-11-06)
- **Personajes.** Hasta 12. Cada uno lleva `tipo` (persona | institucion), `cargo` (≤ 28 caracteres: va en su tarjeta en pantalla; en la mesa de archivo, en su ficha) y `bando` (acusado | investigador | juez | otro).
- **Toda persona que la voz nombre tendrá su retrato en pantalla (H22).** Por eso incluye a las personas clave del caso (operadores, jefes, testigos, fiscales) aunque aparezcan poco.
- **Modo caso** (`/serie … caso`): reparte por TEMA.
  - `serie.columna`: los temas en orden.
  - En cada parte: `tema`, `hechos` (ids, ≥ 8 hechos) y `obligatorio`.
  - `serie.fuera`: `{id: motivo}`.
  - ≥ 85 % de lo publicable repartido (SE10–SE11). Una parte puede contar en su tema algo que se supo años después.
- **Cada parte cuenta lo nuevo** (SE15–SE16, 2026-11-09): reparte de modo que ninguna parte necesite volver a contar
  lo de otra para entenderse: si depende de un hecho anterior, lo recuerda en una oración (SE15 deja ≤ 2 ids ya
  contados). Dos partes nunca se reparten el mismo momento desde dos ángulos (las capturas del 16 de abril, una vez).
- **La última parte lleva el resumen de toda la serie** (SE14, 2026-11-07): 20–30 s en su acto 3 que repasan lo que contaron las demás. Dale ese margen en su plan: puede durar hasta 30 s más que las otras.

## Archivos que la historia puede mostrar (2026-11-12)

El guionista tiene escenas que ponen en pantalla un archivo real (`vias`, `lupa`, `deptos`, `pagina`, `cortina`,
`archivo`, `bandos`; `referencias/flujo-historia.md`). Solo existen si la investigación trae el archivo: pídelo en el
encuadre, en las `fuentes_sugeridas` o en `fotos_clave` del eje que corresponda, cuando la historia lo tenga.

- **Un lugar que cambió** (antes y ahora): dos fotos del mismo sitio, una de la época y una de hoy.
- **Un documento que lo dice** (un decreto, un informe, una sentencia en PDF): la fuente en PDF y la frase que importa.
- **Una foto donde hay algo que ver** (un edificio dañado, un objeto, una firma): que el verificador la baje con buena
  resolución y describa qué se ve y dónde.
- **Dos lados con caras** (una votación, una firma, una ruptura): el retrato de cada persona y el hecho que la pone en su lado.
- **Calles de una ciudad**: la red vial que hay en `design/vias/` (hoy, `capital`); si la historia pasa en otra ciudad,
  dilo en tu salida para que se arme antes del guion (`scripts/build_vias.py`).
- **Una serie corta de una cifra** (3–5 censos, 4 años): los valores completos, para barras o burbujas.

No fuerces una **escena** de archivo que la historia no pide (un mapa vial, una cortina). Los archivos básicos —notas
con su titular, documentos, lugares y un retrato por persona— ya no son opcionales: «Con la mesa de archivo», abajo.

## Lo que está en juego (H8, H25; 2026-11-10)

Cada acto lleva `en_juego`: qué se puede perder ahí y a quién alcanza, en una frase («el ahorro de un millón de
cuentas»). Sube de acto en acto: del negocio de alguien, a la gente que dependía de él, al país. No se repite. En una
serie, cada parte del plan lleva también su `en_juego` (mayor que el de la anterior) y el plan lleva
`serie.promesa.pregunta`: la pregunta que responde la serie entera, no la de una parte.

## Con la mesa de archivo (2026-11-14)

El video de `/historia` y de `/serie` se dibuja con la **mesa de archivo** (`referencias/flujo-mesa.md`): con cada
oración de la voz entra en pantalla una pieza que la voz nombra, y la pieza es un archivo real antes que una ficha de
texto (MV5 mide cuánto del video es archivo real). Lo que el encuadre no pide no llega al plano. Por eso los archivos
que la historia puede mostrar **dejan de ser opcionales**: por cada acto, di qué hace falta, en las `preguntas` y las
`fuentes` del eje que lo sostiene (y en `fotos_clave` lo imprescindible).

- **Notas con titular**: qué notas de prensa cuentan los momentos del acto (el detonante, el punto medio, el clímax),
  con el medio y la época. El investigador las guarda con su titular real: de ahí salen los recortes.
- **Documentos en PDF**: qué ley, sentencia, informe o comunicado dice lo que el acto afirma, y qué frase importa. De
  ahí sale la página con la frase subrayada.
- **Lugares**: dónde pasa cada acto (municipio y departamento; el país si la historia sale de Guatemala). La mesa los
  pone en el mapa.
- **Un retrato por persona**: cada persona de `personajes` (y el protagonista, si es una persona). Quien no lo tenga
  entra como ficha sin cara; H22 sigue pidiendo el retrato de toda persona que la voz nombre.
- **Qué es cada institución**: su `presentacion` sirve de rol en su ficha; que quepa en ≤ 6 palabras («la autoridad de
  los bancos»).

La forma del encuadre y sus gates no cambian. En una serie, el reparto vale por parte: cada parte necesita sus notas,
sus documentos, sus lugares y sus retratos (y SE19 sigue limitando una misma foto a ≤ 2 partes).
