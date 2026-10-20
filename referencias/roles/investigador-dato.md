# §Investigador · modo dato (`/dato`)

Complemento de `referencias/roles/investigador.md` (léela primero): solo lo lee `/dato` y sus modos
`vs`, `mapa` y `antes`.

Hay un solo eje (`dato`, prefijo `dat`) y no hay editor: tú haces el
**encuadre ligero** antes de investigar, empezando por decidir el tema.

1. **Pista → tema.** La directiva trae una `pista` opcional del usuario: un
   tema («remesas»), un ángulo («lo que cuesta llenar el tanque»), una fuente
   («lo último del INE») o una corazonada («un dato de educación que
   sorprenda»). Es orientación, no encargo cerrado: empieza por ahí y desvíate
   si en su vecindad (misma área, misma fuente) hay un dato más fuerte. Sin
   pista, elige por tu cuenta: revisa publicaciones recientes de fuentes
   oficiales (boletines, tableros, informes de las últimas semanas) y
   `python3 scripts/fuentes.py --tema "…" --series` en varias áreas, y
   quédate con la que tenga un dato duro que sorprenda. En `encuadre.json`
   escribe **las dos cosas**: `pista` (literal del usuario, o null) y `tema`
   (el tema final que elegiste: ≤ 80 caracteres, sin dos puntos; es el título
   de `post.md` y de la vista previa; el detalle va en `pregunta` y `brief`).
2. Dedup y gancho: `python3 scripts/memoria.py --datos "<tema>"` lista los
   datos ya publicados que casan con el tema (no repitas misma cifra y
   periodo); `python3 scripts/memoria.py --datos` sin tema da el más reciente
   primero: su `hook` es tu `hook_evitar` (null si no hay ninguno). Lee
   `memoria/hilos.json` solo para `repetido` (si el tema ya tuvo hilo, busca
   otro ángulo o periodo). No abras `memoria/datos.json` ni `memoria/fuentes.json`.
3. Paleta por tema (`design/tokens.json → paletas.*.temas`; energía y
   combustibles → `cielo`; en duda, la del tema principal del dato).
4. Crea `sesiones/<slug>/` (slug del tema final, sin fecha; si existe, sufijo
   `-2`) y escribe `encuadre.json` mínimo: `slug, pista, tema, fecha, tipo:
   "dato", paleta, pregunta, hook_evitar, repetido, sesion_dir, smoke,
   fixture: false, ejes: [{id: "dato", prefijo: "dat", brief, preguntas[],
   fuentes_sugeridas[]}]`, con la salida de `fuentes.py` para el tema final.

Qué buscar: no una historia sino **candidatas a dato impactante**. Una
candidata vale si (a) contradice la intuición o sorprende, (b) se traduce a
escala humana (N de cada M, per cápita, «lo que cuesta…»), (c) trae una
comparación clara (antes/después, Guatemala vs región, departamento vs país) o
(d) es reciente. Prefiere datos con las cuatro. Cada cifra lleva, además de la
evidencia, `impacto` (≤ 160: por qué sorprende o a qué escala humana se
traduce; es lo que el guionista puntúa). Si la candidata vive de una
comparación, captura los dos lados (como `partes[]` o como cifra aparte con su
propia evidencia). «Récord/histórico» solo con la serie completa (≥ 10 puntos);
si no la tienes, no la llames récord. Un desglose departamental completo (22)
habilita la plantilla `mapa`.

Presupuesto (normal / smoke): ≤ 8 / 4 búsquedas, ≤ 8 / 4 fetch, ≤ 8 / 4
cifras, ≤ 2 / 1 series. En smoke sin pista la directiva trae una fija. Ids
`dat-cNN`. Escribe `<sesion>/hallazgos_dato.json` COMPLETO (`eje: "dato"`).
Retorno: `slug, sesion_dir, pista, tema, modo, pregunta, paleta, hook_evitar,
repetido, archivo, n_busquedas, n_fetch, cifras[]{id, tipo, n_puntos,
impacto}, vacios[]`.

## Modos vs · mapa · antes

La directiva trae `MODO DEL POST` (`dato` por defecto). Escribe `modo` en
`encuadre.json` y busca lo que el modo exige; si no lo encuentras, dilo en
`vacios` (el guion fallará sin eso).
- **`vs`**: el indicador en UNA fuente internacional que cubra a todos los
  países (CEPAL, Banco Mundial/WDI, OPS, UN Comtrade, OLADE, FMI, SIECA), misma
  edición, periodo y unidad; captúralo como UNA cifra `tipo: "desglose"` con
  `partes[]` = un valor por país (Guatemala incluida; ≥ 2 países: Centroamérica
  o la región que pida el indicador). Si las poblaciones difieren mucho, la
  versión per cápita como otra cifra desglose. Nunca prensa para un país y
  organismo para otro.
- **`mapa`**: un desglose por departamento (≥ 12, ideal 22) con los nombres
  oficiales del INE y el denominador de población del INE del mismo año
  (proyecciones por departamento). La TASA va como cifra propia `desglose`
  «cálculo propio» con evidencia del numerador y del denominador, además del
  absoluto.
- **`antes`**: dos puntos de la MISMA serie y fuente separados ≥ 5 años (o la
  serie completa ≥ 5 puntos) con definición y unidad sin cambios; si cambió la
  base o la metodología, en `nota`. Si es dinero, anota si es corriente y, si
  existe, la versión real o el deflactor.
