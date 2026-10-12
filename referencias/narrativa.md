# Narrativa: cómo cuenta una historia un hilo de datos

## Arco

`gancho → contexto → giro → impacto → cierre` en 4–21 tuits (en hilos largos, varios `contexto` e `impacto`, un solo `giro`). Exactamente un
`giro` (el hecho que cambia la lectura); el `impacto` traduce a escala humana
(N de cada M hogares, per cápita, «lo que cuesta llenar el tanque»); el cierre
aterriza la tesis, reconoce lo que NO se afirma y lista las fuentes. **La
escalada la produce el orden de los hechos, no los adjetivos.**

## Gancho (T1): ocho tipos de `hook_tipo`

T1 siempre lleva texto (40–280 de peso X; primera línea ≤ 90; sin enlaces).
Elegir el tipo por la forma de la historia y registrarlo en `guion.hook_tipo`.
No repetir el `hook_evitar` del encuadre (el del último hilo).

| `hook_tipo` | Fórmula | Cuándo |
|---|---|---|
| `giro_inversion` | `[Dato en una dirección]. Pero [dato que la invierte].` | Récord con matiz, mejora con nivel bajo, per cápita. El ganador probado |
| `escala_humana` | Cifra macro → «N de cada M hogares/personas» | Totales en millones que no significan nada solos |
| `brecha_territorial` | `En [A], X. En [B], Y. Mismo país.` | Mapas, brechas urbano-rural |
| `pregunta_directa` | `¿[Pregunta contraintuitiva]? No es [lo obvio].` | Rankings; la respuesta llega en T2–T3 |
| `curiosity_gap` | Afirmación sorprendente; la cifra ancla en la línea siguiente | Guatemala vs mundo. **El gap se paga dentro del hilo (T2–T3)**, nunca «abrimos hilo para descubrirlo» |
| `mito_vs_dato` | `Podría pensarse X. Los datos dicen otra cosa: Y.` | Creencia común cuantificablemente falsa |
| `antes_despues` | `En [año], X. Hoy, Y.` | Series temporales, efemérides |
| `titular_clasico` | `TITULAR: cifra` | Solo récords o alertas literales; máximo 1 de cada 5 hilos; «récord» solo con una serie ≥ 10 puntos que lo respalde |

Anti-reglas: urgencia falsa («URGENTE», «ALERTA» solo para alertas reales);
rage-bait, encuadre partidista, culpables sin dato; engagement-bait («RT si…»,
«dale like», «no vas a creer»); superlativos no verificables; preguntas que la
cuenta no puede responder con datos; máximo una palabra en MAYÚSCULAS por tuit;
sin hashtags de campaña (0–2, `#Guatemala` opcional).

## Tarjeta y texto: la regla del dato héroe

Cada tarjeta tiene UN dato héroe y su titular es el hallazgo en lenguaje llano
(«Llenar el tanque cuesta 77% más que en enero»); el kicker es tema · unidad.
**El texto del tuit no repite la tarjeta**: no contiene ninguna línea del
titular ni dos o más de los números que la tarjeta muestra. El texto añade lo
que la imagen no puede: la pregunta, la comparación humana, la salvedad, la
transición al siguiente tuit. Si la tarjeta ya lo dice todo, el texto vacío pesa
más. Con imagen, T2..T(n−1) llevan ≤ 200 (ideal ≤ 140).

## Dato único (`/dato`)

Un dato solo, sin hilo, compite con todo el timeline en un segundo. Lo que lo
hace impactante no son los adjetivos sino: (1) **sorpresa** (contradice lo que
el lector creía), (2) **escala humana** (N de cada M, per cápita, «cuesta
tanto como…»), (3) una **comparación** que se lee de un vistazo (antes/después,
Guatemala vs vecinos, un departamento vs el país), (4) **actualidad** y (5)
una **fuente que no admite discusión**. El guionista puntúa cada candidata en
esos cinco criterios y elige una; las demás quedan en `candidatas` con motivo.

Reparto del trabajo entre tarjeta y texto (el dato héroe, llevado al límite):
- **La tarjeta** lleva la cifra (grande), el hallazgo en palabras (titular),
  el contexto mínimo (`contexto`, `comparacion`, `nota` con la salvedad) y la
  fuente en el pie. Es autosuficiente: quien solo vea la imagen entiende el
  dato y sabe de dónde sale. **El titular nombra el sujeto** («Las
  deportaciones suben 45%…»), no «2026 sube 45%»: el kicker precisa, no
  explica.
- **El texto** es el tuit entero (40–280, primera línea ≤ 90, sin enlaces) y
  añade lo que la imagen no puede: el «y qué», la pregunta, la comparación
  humana, la salvedad, el «podría pensarse X». **No repite ninguna línea del
  titular ni dos números de la tarjeta**; un número puede reaparecer si el
  gancho lo necesita. No hay cierre: la fuente ya va en el pie.
- **Alt-text** como siempre: tipo de gráfico, cifra con unidad y periodo,
  fuente.

Ganchos: los ocho `hook_tipo` valen, con dos ajustes. `curiosity_gap` y
`pregunta_directa` no «se pagan en T2–T3» sino **en la tarjeta**: el titular
es la respuesta y el texto no promete nada que la imagen no muestre.
`titular_clasico` solo para récords literales con serie ≥ 10 puntos. Se evita
el `hook_tipo` del último dato publicado (`memoria.py --datos`).

## Modos de un dato (`/vs`, `/mapa`, `/antes`)

Tres géneros que salen con la maquinaria de `/dato`; cada uno añade una regla
que el gate comprueba.

- **`vs` — Guatemala frente a…** Una comparación solo vale si todos los lados
  salen de la misma fuente, edición, periodo y unidad (CEPAL, Banco Mundial,
  OPS, UN Comtrade, OLADE, FMI). Nunca prensa para un país y organismo para
  otro. Si las poblaciones difieren mucho, per cápita. Guatemala va destacada;
  el titular dice la brecha («Guatemala recauda la mitad que Costa Rica»), no
  el marcador: nada de «ganamos», «perdemos», «somos los peores». La `nota`
  nombra la fuente común y el año. El texto da la salvedad (definiciones,
  informalidad, tipo de cambio) o la escala humana.
- **`mapa` — brecha territorial.** Siempre tasa (por 1,000 o 100,000 habitantes,
  o %) con el denominador del INE del mismo año; el absoluto solo con motivo
  declarado (el departamento de Guatemala siempre «gana» en absolutos). Gancho
  `brecha_territorial`: «En [A], X. En [B], Y. Mismo país». El titular nombra la
  brecha (razón o diferencia entre extremos), no «el mapa de…». Mínimo 12
  departamentos con valor, ideal los 22 con nombres oficiales; los extremos
  rotulados. La `nota` lleva unidad y año.
- **`antes` — hace N años frente a hoy.** Dos puntos de la misma serie y fuente
  separados al menos cinco años, con la definición sin cambios (si cambió la
  base o la metodología, se dice). Dinero en quetzales o dólares corrientes se
  declara en la `nota» («quetzales corrientes»); si se deflacta, también. El
  gancho es `antes_despues` («En 2006, X. Hoy, Y.»); el texto lee el cambio o
  lo que no cambió. «Récord» solo con serie ≥ 10 puntos, como siempre.

## Explicador (`/explica`)

Un explicador no prueba una tesis: enseña cómo funciona o cómo se calcula algo
con sus números («¿Cómo se calcula tu tarifa de luz?», «¿A dónde va cada
quetzal del presupuesto?», «¿Cómo llega una remesa?»). Su valor es la
claridad, no la sorpresa; es lo que la gente guarda.

- Arco: `gancho → paso → paso … → cierre`, 3–6 tuits, **sin giro ni impacto**.
  T1 plantea la pregunta (`pregunta_directa` o `curiosity_gap`; T2 empieza a
  pagarla). Cada `paso` es una tarjeta con la cifra de ese paso (componentes
  en `dona`/`apilada`/`treemap`, tasas en `cifra`, metas en `bullet`, flujos en
  `embudo`) y un **texto que explica el paso en lenguaje llano** (nunca vacío,
  ≤ 200 con imagen). El cierre resume («en resumen…») y nombra las fuentes.
- Cada paso lleva una cifra verificada; si un paso no se puede cuantificar,
  no es un paso: va en la nota o se omite.
- Cero adjetivos valorativos («abusivo», «ridículo»); las comparaciones van en
  números. El total, si lo hay, cuadra con las partes (C7).

## Perfil (`/perfil`)

Un perfil es un retrato sin tesis: «Alta Verapaz en 6 datos», «Los jóvenes de
Guatemala en 6 datos», «Los retornados: quiénes son». Su valor es el retrato
completo y comparable.

- Arco: `gancho → dimension × 3–6 → cierre`, 5–8 tuits, **sin giro ni
  impacto**. El sujeto aparece en el kicker o el titular de T1. Dimensiones
  estándar: población y crecimiento, pobreza o ingreso, salud o desnutrición,
  educación, seguridad o migración, economía local.
- **Cada tarjeta compara sujeto y país** en la misma fuente, unidad y año: un
  item rotulado «Guatemala», «nacional» o «país», la `comparacion` de `cifra`, o
  un `mapa` con el sujeto destacado. Per cápita con proyecciones INE.
- Si los datos son de años distintos, el cierre los nombra. El cierre dice qué
  hace distinto al sujeto y nombra las fuentes. Sin ranking moral: la brecha se
  describe, no se juzga.

## Honestidad = credibilidad

- Lo que la evidencia no permite afirmar va en `no_afirma` (≤ 5 ítems, solo
  sobre cosas que un lector podría inferir del hilo).
- La salvedad de un dato va en la `nota` de su tarjeta («incluye los meses de
  subsidio», «promedio de 11 meses»).
- Conectores causales («por», «debido a», «impulsado por») solo con fuente que
  lo afirme; si no, «coincide con», «en paralelo a».
- «Récord», «histórico», «el más alto» exigen una serie ≥ 10 puntos en las
  cifras del tuit cuyo máximo sea ese valor. «El más bajo/alto desde X» exige
  una serie o desglose ≥ 5 puntos que cubra desde X **inclusive**; si X es
  ambiguo («desde la pandemia»), se nombra el año o el número de años.
- La segunda fuente de una cifra puede ser `independencia: "baja"` (reproduce
  la primaria). Vale como verificación del número, no como respaldo
  independiente: si sostiene la ancla, `incertidumbre` lo dice.
- El cierre lista todas las fuentes de las cifras usadas (nombre corto de cada
  `visual.fuente`).

## Alt-text

Siempre, ≤ 1000 caracteres: tipo de gráfico, dato principal con su cifra y
unidad, y la fuente. Es la única versión textual del PNG.

## Estilo

Español guatemalteco neutro; lenguaje accesible; precisión («~», «cerca de» si
es aproximado); tono informativo ante datos negativos, sin exagerar los
positivos; emoji solo en el texto del tuit (nunca en la tarjeta) y con medida.
