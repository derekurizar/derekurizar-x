# §Investigador (`hilo-investigador`, uno por eje, en paralelo)

Recolecta cifras con fuente primaria dentro de UN eje. Método SIFT: para cada
dato, para (Stop), investiga la fuente, busca mejor cobertura, rastrea al
original.

**Presupuesto** (normal / smoke): ≤ 10 / 5 búsquedas, ≤ 12 / 6 fetch,
≤ 12 / 6 cifras, ≤ 4 / 2 series. Si lo agotas, cierra con lo que tienes y
anota en `vacios[]` lo que faltó. Menos cifras bien documentadas valen más que
muchas: solo ~1 de cada 4 acaba en una tarjeta.

Reglas:
- Empieza por las `fuentes_sugeridas` y `series_sugeridas` de tu eje en
  `encuadre.json` (ya traen url, formato y nota de acceso). No abras
  `memoria/fuentes.json`.
- Fuente primaria antes que prensa; la prensa solo si reproduce un dato oficial
  con su origen. Registra `valor` NUMÉRICO en la unidad de la fuente; si
  conviertes (litros→galones, MXN→US$) explícalo en `nota`.
- **Evidencia hacia adelante**: cada cifra lleva `evidencia {url, cita ≤ 200
  caracteres con el número tal como aparece, archivo_local si lo descargaste}`.
  El verificador parte de ahí y no repite tus descargas.
- Series completas (`serie[]`, `n_puntos`, `periodo`) cuando el dato es temporal
  (una tarjeta de línea necesita ≥ 5 puntos); desgloses (`partes[]`) cuando es
  comparativo. Si el desglose es por departamento, captura los 22 (para la
  plantilla `mapa`).
- Marca `candidata_ancla` en la cifra que mejor sostiene la tesis provisional.
- Descargas: `make tabla URL=`, `make pdf URL=`, `python3 scripts/fetch_api.py
  URL` (todo cachea en `sesiones/_descargas/`); CSV grandes con `python3
  scripts/tabla.py <csv> --columnas|--serie|--agrupar` en vez de volcarlos.
  Sitios con WAF: `fetch_tabla.py --enlaces PATRON URL`. **Sin Playwright MCP.**
- No inventes, no extrapoles, no redondees lo que la fuente no redondea.

Escribe `<sesion>/hallazgos_<eje>.json` COMPLETO. Retorno: `eje`, `archivo`,
`n_busquedas`, `n_fetch`, `cifras[]{id, tipo, n_puntos, candidata_ancla}`,
`vacios[]` (el detalle queda en disco).

Modos de hilo (la directiva lo dice): en **`explica`** cada cifra cuantifica un
paso del mecanismo (componentes, tasas, montos) y los desgloses (`partes[]`)
deben sumar al total, que también se captura; en **`perfil`** cada dimensión
necesita el valor del sujeto **y** el nacional de la MISMA fuente y año (como
desglose con `partes [sujeto, nacional]` o como dos cifras) y, para tasas, la
población INE del sujeto y del país.

## Modo investigación (`/investigacion`)

Mismo método, más material: el informe publica tablas enteras y figuras
propias además de las tarjetas del hilo.
- **Presupuesto** (normal / smoke): ≤ 14 / 7 búsquedas, ≤ 16 / 8 fetch,
  ≤ 16 / 8 cifras, ≤ 6 / 3 series.
- Series **completas**: todos los puntos que la fuente publica (no solo los
  cinco que pide una tarjeta), con `n_puntos` y `periodo` siempre; si la serie
  cambia de base o de método, en `nota`.
- ≥ 1 **desglose** por eje (`partes[]` por categoría, departamento o año) con
  el total si la fuente lo da; los departamentales, los 22.
- `fuentes[]{nombre, url, nivel}` cuidadas: el informe las lista numeradas en
  la página de método (`nivel: "primaria"` es lo que entra).
- Lo que no encuentres va a `vacios[]`: el informe lo declara en «Límites de
  los datos».

## Modo dato (`/dato`)

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

### Modos vs · mapa · antes

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
