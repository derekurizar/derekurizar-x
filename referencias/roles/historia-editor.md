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
  presenta así la primera vez (H18). Evita un alias que compartan dos personas («Baldetti»).
- **2–5 periodos** `{n, titulo (≤ 4 palabras), periodo, pregunta}` en orden cronológico (o del caso): solo
  reparten los ejes entre los investigadores; no son capítulos del video (el guion va por actos).
- **2–3 ejes** `{id (2–6 letras: ori, exp, cas…), nombre, periodos: [n], preguntas, fuentes}`: el reparto de la
  investigación por época o por tema, sin solaparse. Las fuentes sugeridas son nombres e instituciones, no urls
  inventadas.
- **`dominios_propios`**: los dominios de la empresa o institución protagonista (su sitio cuenta como fuente propia
  para su propia historia: fechas de fundación, aperturas), o `[]`.
- **Paleta** del tema (`design/tokens.json`), distinta de la de la última historia si `preparar` la nombró.
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
  bolsa o el vaso, el edificio, la persona) y es obligatoria (H12). Los investigadores y verificadores las buscan.
- `dominios_propios` incluye también el sitio de la marca (`incaparina.com`), no solo el de la institución: su prensa
  cuenta como foto «empresa».

## Salida

`<TRABAJO>/encuadre.json` (ejemplo completo: `sesiones/_fixture_historia/encuadre.json`):

```json
{"tema": "…", "slug": "…", "pregunta": "…", "protagonista": ["…"], "revelaciones": ["…"], "fotos_clave": ["…"],
 "resumen": "la historia en una oración", "arco": "caso", "paleta": "jade", "dominios_propios": [],
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
