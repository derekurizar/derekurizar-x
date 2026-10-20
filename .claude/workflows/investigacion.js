export const meta = {
  name: 'investigacion',
  description: 'Informe de investigación (PDF Letter) + hilo de X cuyas tarjetas son figuras del informe: encuadre → investigación ⇢ verificación por eje → guion → visuales → producción del hilo → informe (redactor) → revisión de justificación (revisor) → cierre',
  whenToUse: 'Invocado por /investigacion <tema|idea:<id>|desde:<slug>> [smoke|fixture]. args: {tema, idea, desde, desde_hilo, numero, smoke, fixture, fecha, min_tuits, permitir_fallback, auditoria}. fecha (YYYY-MM-DD) y numero ("NN", de `python3 scripts/memoria.py --informes`) son obligatorios: los pone el comando. desde = slug de una sesión existente cuyo hilo ya se entregó (desde_hilo = su ruta relativa): salta a Relectura → Informe → Cierre y no re-entrega el hilo. smoke = 1 eje, 4–6 tuits, 8–12 páginas, todo en sesiones/<slug>/{salida,informe}, sin tocar memoria/. fixture = sin web, copia sesiones/_fixture (3 tuits, 6–10 páginas). auditoria = {inventario, slug, plan, ejes[{id, nombre, prefijo, compromisos[]}], capitulos[{n, titulo, pregunta, ejes[]}]}: variante que evalúa cada compromiso de un plan de gobierno (scripts/auditoria.py): un eje por grupo de compromisos, evaluacion_<eje>.json, fase Puntaje y informe de 30–140 páginas con fichas («de dónde sale cada barra») y anexo de enlaces generados.',
  phases: [
    { title: 'Encuadre', detail: 'editor: pregunta, tesis, paleta, 2–5 ejes y plan de capítulos (encuadre.informe)' },
    { title: 'Relectura', detail: 'solo desde:<slug>: el editor relee la sesión y el hilo entregado y añade encuadre.informe' },
    { title: 'Investigación', detail: 'un investigador por eje con presupuesto ampliado: series completas y desgloses' },
    { title: 'Verificación', detail: 'un verificador por eje: segunda fuente, veredicto, independencia' },
    { title: 'Rechequeo', detail: 'verificador en modo rechequeo: en auditoría, los compromisos que mueven la conclusión antes del puntaje; después del guion, la ancla y T1' },
    { title: 'Puntaje', detail: 'solo auditoría: auditoria.py --calcular → % por compromiso, semilla y global; cifras derivadas aud-cNN' },
    { title: 'Guion', detail: 'guionista: 6–12 tuits con giro e impacto, bloque investigacion{numero, informe_dir, capitulos[]}, cierre con [ENLACE AL INFORME]' },
    { title: 'Visuales', detail: 'visualistas en lotes de 3: materializar → gate R1–R6 → QA' },
    { title: 'Producción', detail: 'productor: ensamblar.py --check --salida investigacion/<fecha>-<slug>/hilo + coherencia C1–C8 (sin memoria todavía)' },
    { title: 'Informe', detail: 'redactor: informe.json → informe.py --check --png (I1–I7, P1–P5) en bucle, ≤ 3 corridas' },
    { title: 'Revisión', detail: 'revisor: ¿de dónde sale cada número, barra y afirmación? (V1–V8 y los avisos R1–R6 de revision.py; auditoría: J1–J5) → el redactor corrige las faltas que bloquean, ≤ 3 vueltas' },
    { title: 'Cierre', detail: 'productor: informe.py al entregable, QA de ≤ 3 páginas, memoria.py --registrar --informe, make validate' },
  ],
}

// Guías: referencias/flujo-investigacion.md, referencias/contrato-sesion.md («Sesión investigación»),
// referencias/roles/*.md («Modo investigación»; el redactor tiene guía propia). Los agentes escriben su
// artefacto COMPLETO en sesiones/<slug>/ y devuelven aquí un resumen validado por schema; los gates se
// aplican sobre los retornos (el sandbox del workflow no lee disco ni tiene Date).
// Constantes compartidas con hilo.js (PALETAS, PLANTILLAS, BEATS, HOOKS, REQ, RE_*, pesoX): copias literales,
// las vigila scripts/check_workflows.py (W1–W4). MODOS declara solo el modo que sirve este workflow (W5 por
// unión con hilo.js); TIPOS_PAGINA y MARCADOR_INFORME son espejos de informe.py y ensamblar.py (W6).

const PALETAS = ['cielo', 'jade', 'maiz', 'terracota', 'cacao', 'jacaranda', 'atitlan', 'obsidiana']
const PLANTILLAS = ['linea', 'barras-v', 'barras-h', 'antes-despues', 'dona', 'pendiente', 'waffle', 'cifra', 'mapa', 'pesas', 'calor', 'bullet', 'embudo', 'divergente', 'apilada', 'piramide', 'treemap', 'dispersion', 'hemiciclo', 'multiples', 'combinado', 'linea-tiempo', 'agrupadas', 'pictograma', 'area-apilada', 'cascada']
const BEATS = ['gancho', 'contexto', 'giro', 'impacto', 'cierre', 'paso', 'dimension'] // paso: modo explica · dimension: modo perfil
const HOOKS = ['giro_inversion', 'escala_humana', 'brecha_territorial', 'pregunta_directa', 'curiosity_gap', 'mito_vs_dato', 'antes_despues', 'titular_clasico']
const REQ = {
  linea: ['etiquetasX', 'series'], 'barras-v': ['etiquetas', 'valores'], 'barras-h': ['items'],
  'antes-despues': ['antes', 'despues'], dona: ['partes'], pendiente: ['fechas', 'items'],
  waffle: ['porcentaje', 'cifra'], cifra: ['cifra'], mapa: ['valores'], pesas: ['fechas', 'items'], calor: ['filas', 'columnas', 'valores'],
  bullet: ['items'], embudo: ['etapas', 'misma_cohorte'], divergente: ['items'], apilada: ['etiquetas', 'partes'],
  piramide: ['grupos', 'izquierda', 'derecha'], treemap: ['partes'], dispersion: ['puntos', 'ejeX', 'ejeY'],
  hemiciclo: ['total', 'bloques'], multiples: ['etiquetasX', 'paneles'], combinado: ['etiquetas', 'barras', 'linea'], 'linea-tiempo': ['eventos'],
  agrupadas: ['etiquetas', 'series'], pictograma: ['total', 'destacado', 'texto'], 'area-apilada': ['etiquetasX', 'partes'], cascada: ['pasos'],
}
const RE_LINK = /https?:\/\/|www\.|\.com\b|\.gt\b/i
const RE_BAIT = /(dale|da|dame|dejen?)\s+(rt|like|me gusta)|s[ií]gue(me|nos)|retuitea|comparte si|like si|guarda este|no te lo pierdas/i
const RE_SUPER = /r[ée]cord|hist[óo]ric[oa]|m[áa]s alt[oa] de la historia|nunca antes/i
const LOTE = 3
const MAX_TUITS = 21
// Marcador literal del cierre (el usuario lo sustituye por la URL del PDF al publicar); espejo de ensamblar.MARCADOR_INFORME.
const MARCADOR_INFORME = '[ENLACE AL INFORME]'
// Modo único de este workflow; su clave entra en ensamblar.MODOS["hilo"] (W5 por unión con hilo.js).
const MODOS = {
  investigacion: { beatMedio: null, min: 6, max: 12, giro: 1, impacto: true, minCifras: 10 },
}
const TOPES = {
  normal: { busquedas: 14, fetch: 16, cifras: 16, series: 6, desgloses: 4 },
  smoke: { busquedas: 7, fetch: 8, cifras: 8, series: 3, desgloses: 2 },
}
const PAGINAS = { normal: [14, 30], smoke: [8, 12], fixture: [6, 10] }
const MIN_FIGURAS = { normal: 6, smoke: 3, fixture: 2 }
const MIN_TABLAS = { normal: 1, smoke: 0, fixture: 0 }
const MIN_CAPITULOS = { normal: 2, smoke: 1, fixture: 1 }
const MAX_CAPITULOS = { normal: 5, smoke: 2, fixture: 2 }
const PAGINAS_OBLIGATORIAS = {
  normal: ['portada', 'indice', 'resumen', 'capitulo', 'conclusiones', 'metodo', 'tarjetas', 'contraportada'],
  smoke: ['portada', 'resumen', 'capitulo', 'conclusiones', 'metodo', 'tarjetas', 'contraportada'],
  fixture: ['portada', 'resumen', 'capitulo', 'conclusiones', 'metodo', 'tarjetas', 'contraportada'],
}
// Espejo de informe.TIPOS_PAGINA (scripts/informe.py); lo vigila check_workflows W6.
const TIPOS_PAGINA = ['portada', 'indice', 'resumen', 'tablero', 'capitulo', 'cuerpo', 'apaisada', 'cronologia', 'conclusiones', 'metodo', 'glosario', 'anexo', 'tarjetas', 'contraportada']
const QA = { vueltas_revision: 3, iter_informe: 3, lecturas_redactor: { normal: 6, smoke: 3, fixture: 2 }, lecturas_productor: { normal: 3, smoke: 2, fixture: 1 } }
const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'] // sin Date en el sandbox: «Mes Año» sale de args.fecha
const TEMA_SMOKE = 'remesas familiares 2025'
// Instrucciones del modo que viajan en los prompts (el detalle vive en referencias/roles/*.md «Modo investigación»).
const INSTR = {
  editor: 'MODO INVESTIGACIÓN (informe PDF + hilo): cada eje pide series COMPLETAS (≥5 puntos, todos los publicados) y ≥1 desglose (el informe necesita tablas y figuras propias); un eje incluye la pregunta de escala humana (beat impacto); escribe en encuadre.json modo: "investigacion" e informe {numero, capitulos[1–4]{n: "01"…, titulo ≤60, pregunta, ejes[]}} (un capítulo ≈ un eje o un par de ejes; todo eje en algún capítulo). ',
  investigador: 'MODO INVESTIGACIÓN: series COMPLETAS con todos los puntos publicados (n_puntos y periodo siempre; cambios de base en nota); ≥1 desglose por eje (partes[] por categoría, departamento o año, con el total; departamentales, los 22); fuentes[]{nombre, url, nivel} cuidadas (van a la página de método del informe). ',
  verificador: 'MODO INVESTIGACIÓN: series con cuatro puntos comprobados (primero, último y dos intermedios); desgloses: total y las tres partes mayores; cualquier discontinuidad de la serie en nota (el informe la publica entera). ',
  guionista: 'MODO INVESTIGACIÓN: el hilo es la versión corta del informe (referencias/narrativa.md «Hilo de investigación»): arco normal con giro e impacto; T1 con visual; escribe modo: "investigacion" y el bloque investigacion {numero, informe_dir, capitulos[]{n, titulo, tuits[]}} con los capítulos del encuadre (cada tuit intermedio en exactamente uno); el cierre nombra las fuentes y termina con el marcador literal [ENLACE AL INFORME] (solo ahí; el gate mide su peso con una URL en su lugar); titulares autosuficientes, fuente completa y nota con la salvedad: el redactor reutiliza las tarjetas tal cual. ',
  productor: 'MODO INVESTIGACIÓN (Producción): C1 incluye que cada tarjeta se sostiene sola (irá en el anexo del informe) y C8 que el cierre lleva [ENLACE AL INFORME]. ',
}

// Variante auditoría: instrucciones que se suman a las del modo (detalle en referencias/flujo-investigacion.md «Variante auditoría»).
// El inicio del mandato sale de args.auditoria.mandato_inicio (por defecto el del plan auditado hasta hoy, 2024-01-14).
const MANDATO_INI = String(((args && typeof args === 'object' && args.auditoria) || {}).mandato_inicio || '2024-01-14')
const ANIO_INI = Number(MANDATO_INI.slice(0, 4)), ANIO_BASE = ANIO_INI - 1
const INI_TXT = `${Number(MANDATO_INI.slice(8, 10))}-${['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'][Number(MANDATO_INI.slice(5, 7)) - 1]}-${ANIO_INI}`
const INSTR_AUD_ATRIB = () => INSTR_AUD.atribucion
const INSTR_AUD = {
  atribucion:
    `solo cuenta lo ocurrido en el mandato (desde el ${INI_TXT}): fecha_dato dentro del mandato; cada meta y monto lleva base_fecha (desde cuándo se mide el cambio); las metas se miden desde el nivel de ${ANIO_BASE} o el primer dato del mandato (base_obs con su cifra), NUNCA contra un dato anterior a ${ANIO_BASE} ni contra la base del plan; los conteos acumulados llevan base_fecha "${MANDATO_INI.slice(0, 7)}" (base_obs null o 0); los montos cuentan la ejecución desde ${ANIO_INI}; los hitos, solo hechos del mandato. Sin dato que mida dentro del mandato, no_verificable, que cuenta 0 en el puntaje.`,
  investigador: (ses, eje, ids, fechaCorte) =>
    `VARIANTE AUDITORÍA: tu eje evalúa ${ids.length} compromisos del plan (${ids.join(', ')}). (1) python3 scripts/auditoria.py ${ses} --eje ${eje} los lista con meta, monto, indicador y fuentes sugeridas; --plantilla ${eje} da el esqueleto de evaluacion_${eje}.json. ` +
    `(2) Por compromiso busca el dato oficial más reciente al ${fechaCorte}: ejecución SICOIN/Minfin para montos (devengado acumulado 2024–2026 en millones de Q; 2026 a la fecha, dilo), memorias de labores, informes presidenciales al Congreso (enero 2025 y enero 2026), Segeplán, portales y comunicados institucionales, decretos y acuerdos (Congreso, Diario de Centro América) para hitos; prensa y centros de pensamiento solo si citan el documento oficial (dilo en nota). Agrupa: una misma fuente (p. ej. la ejecución por institución de SICOIN o el informe presidencial) suele servir para varios compromisos. ` +
    `(3) Todo número que uses como observado o base_obs es una cifra de hallazgos_${eje}.json (evidencia {url, cita, archivo_local}) y va en cifra_ids; si el observado es una operación (suma de años, diferencia de matrícula frente a 2023), la cifra lleva la serie o las partes y el resumen dice la operación; --validar coteja observado y base_obs con los valores de sus cifras (redondeo, escala, operación de dos o suma de hasta cuatro) y, si no salen, exige calculo_observado / calculo_base_obs con la operación ("2108803+11000000+11000000"). Retroceso = peor que la base, aunque sea por poco; exactamente igual = no_iniciado. ` +
    'ATRIBUCIÓN: ' + INSTR_AUD_ATRIB() + ' ' +
    '(4) HITOS ATRIBUIBLES: fecha_dato de un hito es la fecha del HECHO del mandato que sostiene el estado (creación, aprobación, inauguración, firma), nunca la de la consulta del portal; si lo que existe se creó antes del ' + INI_TXT + ' y no hay un hecho del mandato que lo amplíe o lo cambie (seguir aplicando o seguir operando no cuenta), el estado es no_atribuible con existe_desde "<YYYY | YYYY-MM | YYYY-MM-DD>" (anterior al mandato) y nota con la fuente (cuenta 0), aunque opere hoy; igual una meta que ya se cumplía en 2023 (el script la marca sola). Estado de hitos y declarativos: cumplido (existe y opera), en_proceso (creado o aprobado y en ejecución parcial, o iniciativa con trámite real), anunciado (solo anuncio, plan o iniciativa presentada sin trámite), no_iniciado (no hay nada), incumplido (se hizo lo contrario de lo prometido), retroceso (empeoró); no_verificable SOLO si buscaste a fondo y no hay información pública (la nota dice qué buscaste): cuenta 0, así que agota fuentes (y proxies oficiales del mismo fenómeno medidos en el mandato) antes de dejarlo así. En metas y montos el script recalcula el estado. ' +
    '(5) resumen de 20–260 caracteres, autosuficiente, con la cifra y su año, sin adjetivos ni juicios («Mineduc reporta 2,310 aulas nuevas en 2024–2025, frente a 70,000 prometidas.»); fuente corta ≤90; no inventes ni extrapoles (si el dato es de 2024, fecha_dato 2024). ' +
    `(6) Escribe ${ses}/evaluacion_${eje}.json y corre python3 scripts/auditoria.py ${ses} --validar ${eje} hasta OK. Devuelve además evaluacion {archivo, n_compromisos, validacion, estados}. `,
  verificador: (ses, eje, ids) =>
    `VARIANTE AUDITORÍA: además revisa los ${ids.length} compromisos de ${ses}/evaluacion_${eje}.json (léelo: es solo tu eje) con python3 scripts/auditoria.py ${ses} --eje ${eje} al lado. Hitos y declarativos: confirma el estado con UNA fuente distinta (≤1 búsqueda y ≤1 fetch por compromiso) y que el hecho que lo sostiene es DEL MANDATO (fecha de creación o aprobación ≥ 14-ene-2024): un programa, norma o evaluación anterior que solo sigue operando se corrige a estado no_atribuible con existe_desde (fecha anterior al mandato) y nota con la fuente; si lo único del mandato es un anuncio, a anunciado. Metas y montos: comprueba que observado, base_obs, base_fecha y fecha_dato salen de cifras que verificaste, que la línea base es de 2023 o del mandato (nunca anterior) y que la operación del resumen es correcta. ` +
    `Añade a verificacion_${eje}.json la clave "compromisos": [{"id", "veredicto": "confirmado|corregido|sin_sustento", y si corriges los campos corregidos ("estado", "observado", "base_obs", "base_fecha", "fecha_dato", "medida_usada", "resumen", "existe_desde"), "url_2", "nota"}] (uno por compromiso; NO edites evaluacion_${eje}.json) y corre python3 scripts/auditoria.py ${ses} --validar ${eje} --verificacion hasta OK. Devuelve además revision {revisados, corregidos[], sin_sustento[], validacion}. `,
  guionista: (ses) =>
    (REV ? `MODO REVISIÓN (${REV.motivo || 'reglas nuevas'}): ${ses}/guion.json es de la pasada anterior: escríbelo de nuevo desde --resumen y el digesto actuales; no reutilices ningún número viejo. ` : '') +
    (pun ? `PUNTAJE VIGENTE: global ${pun.global}% (con dato ${pun.global_con_dato}%), ${pun.n_verificables}/${pun.n_unicos} verificables, ${pun.transcurrido}% del mandato. ` : '') +
    `VARIANTE AUDITORÍA: el hilo resume la auditoría del plan. Corre python3 scripts/auditoria.py ${ses} --resumen (puntaje por semilla y compromiso; las cifras derivadas aud-cNN tienen fuente «Cálculo propio sobre el Plan de Gobierno y fuentes oficiales»). ` +
    'El hilo resume y DESTACA (preferencia del usuario): nada de una tarjeta por semilla que repita lo mismo con otra gráfica; los generales, la mejor y la peor, datos interesantes y los retrocesos uno por uno. Pon auditoria: true en guion.investigacion (tope de 20 tuits). ' +
    'Arco: T1 con el avance global (aud-c02) frente al mandato transcurrido (aud-c05); una tarjeta cifra grande con el % de compromisos cumplidos sin contar el avance parcial (aud-c09; no cumplidos aud-c10); el método en una línea y lo que resta la falta de datos (aud-c02 frente a aud-c03, aud-c08, aud-c07) y lo no atribuible; los compromisos por estado (aud-c04); el avance de las semillas (aud-c01, con la referencia de aud-c05); la semilla que más avanza y la que menos, con lo que las explica (sus compromisos de aud-c1N); 1–3 datos interesantes del avance (el marco fiscal aud-c21/aud-c41, el avance por tipo de compromiso aud-c22, la cobertura aud-c06…); los RETROCESOS: una tarjeta que los cuenta y UNA tarjeta por retroceso con la gráfica de sus datos reales (las cifras de sus cifra_ids: línea base de 2023 frente al último dato) y un texto que explica por qué es retroceso (si no caben todos, los de mayor caída y una lista con el resto); los incumplidos si caben; conclusiones con tarjeta; cierre. ' +
    'Los % son derivados: su tarjeta lleva la fuente «Cálculo propio sobre el Plan de Gobierno y fuentes oficiales» y la nota dice el método en una línea. No afirmes intención ni culpa; «no verificable» cuenta 0 porque no se puede comprobar con datos oficiales: dilo así (no «incumplido» ni «no se hizo») y di que la falta de datos también pesa en el resultado; no compares con otros gobiernos. Nunca escribas «en suma». Asigna cada tuit intermedio al capítulo de su semilla (los capítulos sin tuit van con tuits: []). ',
  redactor: (ses) =>
    (REV ? `MODO REVISIÓN (${REV.motivo || 'reglas nuevas'}): ${ses}/informe.json es de la pasada anterior: reescribe todo texto con %, estados o método y coteja cada número con --resumen y el digesto actuales; las referencias a tarjetas del hilo cambian con el guion nuevo. ` : '') +
    (pun ? `PUNTAJE VIGENTE: global ${pun.global}% (con dato ${pun.global_con_dato}%), ${pun.n_verificables}/${pun.n_unicos} verificables. ` : '') +
    `VARIANTE AUDITORÍA: la exhaustividad es el encargo (todas las semillas, todos los compromisos). Insumo extra: python3 scripts/auditoria.py ${ses} --resumen --para redactor (puntaje de cada compromiso con cifras, fuente y resumen). ` +
    'Estructura: portada (cifra aud-c02) · índice · resumen (aud-c02, aud-c05, aud-c08 y los cumplidos de aud-c04) · tablero (6 cifras) · cuerpo «Cómo medimos» (meta = logrado ÷ meta o desde la línea base; monto = ejecutado ÷ prometido; hito 0/25/50/100; tendencia ≥10 % = 100; no verificable (sin dato oficial, sin línea base atribuible o con su cifra sin confirmar) cuenta 0, y aparte se publican el avance con dato (aud-c03) y los puntos que restan (aud-c08); no atribuible (existía o ya se cumplía antes del ' + INI_TXT + ' y solo se sostiene) cuenta 0 y sí entra en el avance con dato; atribución: línea base de 2023 o del inicio del mandato, nunca anterior; montos desde 2024; hitos por hechos del mandato; espejos; ritmo frente al mandato transcurrido; semilla = promedio simple, global = promedio de las semillas, marco fiscal aparte; figura barras_h con aud-c01) · ' +
    'un capítulo por semilla en el orden del plan: página capitulo (banda o destacado) con lo prometido, el % de la semilla y su lectura; ≥1 cuerpo con figura papel barras_h de aud-c1N (items = partes de aud-c1N por nombre, tal cual) y figuras de las series reales de sus ejes donde las haya; luego {"tipo": "cuerpo", "auto": "fichas:<N>"} (las tablas de fichas las genera el script; el capítulo del marco fiscal usa fichas:F) · ' +
    'conclusiones con titulo «Conclusiones» (nunca «En suma», ni como título ni en el texto; un hallazgo por semilla; no_afirma: «no verificable» cuenta 0 por falta de dato oficial pero no afirma que no se hizo nada, los % no miden impacto ni calidad del gasto) · metodo (las cifras de las figuras; si no caben, una segunda metodo con fuentes: false) · glosario · {"tipo": "anexo", "auto": "evidencias:todas"} · tarjetas · contraportada. ' +
    `Corre python3 scripts/auditoria.py ${ses} --insertar ${ses}/informe.json ANTES de cada informe.py --check (idempotente; no edites a mano las páginas con "auto"; si P2 salta en una, pon "lineas" menor en su placeholder). Las páginas fichas cuentan en capitulos[].paginas y sus tablas en n_tablas. ` +
    `JUSTIFICACIÓN (lo revisa después el informe-revisor, V1–V8): las fichas («de dónde sale cada barra») dan por compromiso el hallazgo, la fuente y el cálculo, y --insertar remite cada gráfico a ellas; además el TEXTO de cada capítulo explica los compromisos que pesan (cada cumplido, cada retroceso o incumplido, los ceros sin dato y todo hito en proceso o anunciado que nombres: qué hecho y cuándo) y todo % dice de qué es y cómo sale. Antes de devolver, python3 scripts/auditoria.py ${ses} --justificar ${ses}/informe.json debe salir OK (J1–J5). `,
}

// Peso de un texto según X (copia de scripts/contar_x.js: el sandbox no importa).
const RE_URL = /https?:\/\/\S+|www\.\S+|\b[a-z0-9-]+(\.[a-z0-9-]+)*\.(com|gt|org|net|io|edu|gov|mx|sv|hn|es|info|co)(\/\S*)?/gi
function pesoX(texto) {
  let t = String(texto || '').normalize('NFC')
  let peso = 0
  t = t.replace(RE_URL, () => { peso += 23; return '' })
  const cps = Array.from(t)
  for (let i = 0; i < cps.length; i++) {
    const cp = cps[i].codePointAt(0)
    if (cp >= 0x1f1e6 && cp <= 0x1f1ff && i + 1 < cps.length) {
      const n = cps[i + 1].codePointAt(0)
      if (n >= 0x1f1e6 && n <= 0x1f1ff) { peso += 2; i++; continue }
    }
    peso += (cp <= 4351 || (cp >= 8192 && cp <= 8205) || (cp >= 8208 && cp <= 8223) || (cp >= 8242 && cp <= 8247)) ? 1 : 2
    while (i + 1 < cps.length) {
      const n = cps[i + 1].codePointAt(0)
      if (n === 0xfe0f || n === 0x20e3 || (n >= 0x1f3fb && n <= 0x1f3ff)) { i++; continue }
      if (n === 0x200d && i + 2 < cps.length) { i += 2; continue }
      break
    }
  }
  return peso
}

// Resumen de límites que viaja en los prompts: así nadie lee investigacion.js ni ensamblar.py.
const LIMITES =
  'LÍMITES (los comprueba el workflow y ensamblar.py --check): tuits numerados 1..n; T1 gancho, último cierre, un solo giro y, con ≥5 tuits, un impacto; ' +
  'T1 con texto de 40–280 de peso X (URL=23, emoji=2), primera línea ≤90, sin enlaces; T2..T(n−1) con visual obligatorio y texto "" o ≤200; ' +
  `el cierre nombra las fuentes cortas de las tarjetas y termina con el marcador literal ${MARCADOR_INFORME} (en ningún otro tuit; con una URL en su lugar debe pesar ≤280); ` +
  'el texto no repite el titular de su tarjeta ni ≥2 de sus números; sin engagement bait; alt_text 20–1000 por visual; ' +
  `plantilla ∈ ${PLANTILLAS.join('|')}; kicker ≤45; titular 1–3 líneas de ≤26; nota ≤150; fuente 1–70 sin «Fuente:»; sin URLs en la tarjeta; ` +
  'cifra_ids ⊆ verificadas; datos con números crudos de esas cifras y formato; linea ≥5 puntos y ≤4 series; dona 2–5; barras-h ≤8; barras-v ≤12; ' +
  'pendiente 2 fechas y 2–6; mapa ≥12 departamentos; pesas 2–8; calor filas×columnas ≤12; bullet 1–6 con meta; embudo 2–6 etapas no crecientes y misma_cohorte true|false; divergente 2–10; apilada 2–8 filas y 2–5 partes; piramide 4–12 grupos; treemap 3–12; dispersion 8–22 puntos con ejeX/ejeY; periodos (linea, barras-v) ≤4 por índices; ' +
  'hemiciclo 10–300 curules en 2–8 bloques que suman total (mayoria simple|calificada la calcula la plantilla); multiples 4–9 paneles con ≥4 puntos en la misma escala; combinado 3–12 periodos con barras y linea de igual longitud (dos ejes declarados; el titular no afirma causa); linea-tiempo 3–8 eventos {fecha, nombre, valor} y proporcional true|false; ' +
  'agrupadas 2–6 categorías × 2–3 series; pictograma total 2–200 unidades y destacado ≤ total (enteros; «K de N» lo compone la plantilla); area-apilada 5–30 puntos × 2–5 partes; cascada 2–8 pasos con efecto suma|resta más inicio y/o fin (acumulados y fin los calcula la plantilla; fin.valor, si va, se coteja); «récord/histórico» solo con serie ≥10 puntos cuyo máximo sea el valor.'

// ── Argumentos ─────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { tema: args } : (args || {})
const temaBruto = String(A.tema || '')
const fixture = !!A.fixture || /\bfixture\b/i.test(temaBruto)
const smoke = fixture || !!A.smoke || /\bsmoke\b/i.test(temaBruto)
const tema = temaBruto.replace(/\b(smoke|fixture)\b/gi, '').trim()
const fecha = String(A.fecha || '')
if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) throw new Error('args.fecha (YYYY-MM-DD) es obligatoria: /investigacion la obtiene con `date +%F` y la pasa en args.')
const numero = String(A.numero || '')
if (!/^\d{2}$/.test(numero)) throw new Error('args.numero ("NN") es obligatorio: /investigacion lo toma de `python3 scripts/memoria.py --informes` («siguiente N.º NN»).')
const desde = /^[a-z0-9-]+$/.test(String(A.desde || '')) ? String(A.desde) : null
const desdeHilo = String(A.desde_hilo || '').replace(/\/$/, '')
if (desde && fixture) throw new Error('desde:<slug> no se combina con fixture.')
if (desde && !/^(hilos|investigacion)\/\d{4}-\d{2}-\d{2}-[a-z0-9-]+(\/hilo)?$/.test(desdeHilo)) throw new Error('args.desde_hilo debe ser la ruta relativa del hilo ya entregado (hilos/<fecha>-<slug> o investigacion/<fecha>-<slug>/hilo).')
const modo = fixture ? 'fixture' : smoke ? 'smoke' : 'normal'
// Variante auditoría (args.auditoria): cada compromiso de un plan de gobierno se evalúa y puntúa con scripts/auditoria.py
// (guía: referencias/flujo-investigacion.md «Variante auditoría»). Solo en modo normal.
const AUD = A.auditoria && typeof A.auditoria === 'object' && Array.isArray(A.auditoria.ejes) && A.auditoria.ejes.length ? A.auditoria : null
if (AUD && (smoke || desde)) throw new Error('args.auditoria solo corre en modo normal (sin smoke, fixture ni desde).')
if (AUD && !/^investigacion\/auditorias\/[a-z0-9-]+\/compromisos\.json$/.test(String(AUD.inventario || ''))) throw new Error('args.auditoria.inventario debe ser investigacion/auditorias/<plan>/compromisos.json')
if (AUD && !/^[a-z0-9-]+$/.test(String(AUD.slug || ''))) throw new Error('args.auditoria.slug (minúsculas y guiones) es obligatorio')
if (AUD && !(Array.isArray(AUD.capitulos) && AUD.capitulos.length)) throw new Error('args.auditoria.capitulos[] es obligatorio (un capítulo por semilla)')
const AUD_LIM = { paginas: [30, 140], figuras: 12, tablas: 11, iter: 6, lecturas: 10 }
// Revisión (args.auditoria.revision {motivo, ids: {<eje>: [compromisos a reinvestigar]}}): rehace una auditoría sobre su
// sesión existente: cada eje corrige y amplía evaluacion/hallazgos/verificacion en su lugar; luego Puntaje → … → Cierre.
const REV = AUD && AUD.revision && typeof AUD.revision === 'object' ? AUD.revision : null
if (REV && !(REV.ids && typeof REV.ids === 'object')) throw new Error('args.auditoria.revision.ids debe ser {<eje>: [ids]}')
const revIds = (eje) => (REV && REV.ids[eje.id]) || []
const topesRev = (eje) => { const n = revIds(eje).length; return { busquedas: Math.min(36, 6 + 3 * n), fetch: Math.min(36, 6 + 3 * n), cifras: Math.min(24, 4 + 2 * n) } }
const topesEje = (eje) => {
  if (!AUD) return T
  const n = ((AUD.ejes.find((e) => e.id === eje.id) || {}).compromisos || []).length || 10
  return { busquedas: Math.min(36, 8 + 2 * n), fetch: Math.min(40, 10 + 2 * n), cifras: Math.min(40, 8 + 2 * n), series: 6, desgloses: 4 }
}
const modoPost = 'investigacion'
const MP = MODOS.investigacion
const T = TOPES[smoke ? 'smoke' : 'normal']
const minT = Math.min(MP.max, Math.max(MP.min, parseInt(A.min_tuits, 10) || MP.min))
const minN = fixture ? 3 : smoke ? 4 : minT
const maxN = fixture ? 4 : smoke ? 6 : AUD ? 20 : MP.max // auditoría: espejo de ensamblar.MAX_TUITS_AUDITORIA
const [minPag, maxPag] = AUD ? AUD_LIM.paginas : PAGINAS[modo]
const minCap = AUD ? AUD.capitulos.length : MIN_CAPITULOS[modo]
const maxCap = AUD ? AUD.capitulos.length : MAX_CAPITULOS[modo]
const minFig = AUD ? AUD_LIM.figuras : MIN_FIGURAS[modo]
const minTab = AUD ? AUD_LIM.tablas : MIN_TABLAS[modo]
const iterInf = AUD ? AUD_LIM.iter : QA.iter_informe
const mesAnio = (() => { const m = MESES[parseInt(fecha.slice(5, 7), 10) - 1] || ''; return m.charAt(0).toUpperCase() + m.slice(1) + ' ' + fecha.slice(0, 4) })()
// Idea del banco (ideas/banco.json): la resuelve /investigacion en el preflight y llega como id.
const idea = /^[a-z0-9-]+$/.test(String(A.idea || '')) ? String(A.idea) : null
// <comun> generado por scripts/armar_workflows.py desde scripts/workflow_comun.js: no editar aquí
// Código común de los workflows hilo.js, dato.js, investigacion.js y video.js (el sandbox de Workflow no importa módulos).
// Fuente ÚNICA: este archivo. scripts/armar_workflows.py lo copia entre los marcadores de bloque común
// de cada workflow; scripts/check_workflows.py (W9) falla si una copia difiere.
// Requiere en el workflow, antes del bloque: `A` (args), `meta` y un esquema `S.rechequeo`.
const fail = (msg) => { throw new Error(msg) }
// Los avisos del workflow viajan también en el retorno (el journal no conserva los log()).
const AVISOS_WF = []
const avisar = (m) => { AVISOS_WF.push(String(m)); log(m) }

// Los roles viven en .claude/agents/ (hilo-*, informe-*) y se registran al arrancar la
// sesión. Si no existen todavía se falla con instrucciones claras: correr todo
// en general-purpose es caro, ignora los modelos por rol y rompe la caché de
// resume. Solo con args.permitir_fallback se degrada a general-purpose.
const agentRol = async (prompt, opts) => {
  try {
    return await agent(prompt, opts)
  } catch (e) {
    if (!opts || !opts.agentType || !/agent type .* not found/i.test(String(e && e.message))) throw e
    if (!A.permitir_fallback) fail(`El agente ${opts.agentType} no está registrado en esta sesión (los .claude/agents/ se cargan al arrancar). Reinicia Claude Code y vuelve a lanzar /${meta.name}, o pasa args.permitir_fallback: true para correr con general-purpose.`)
    avisar(`AVISO: ${opts.agentType} no registrado; se usa general-purpose (permitir_fallback).`)
    const { agentType, ...resto } = opts
    return agent(`Asume el rol definido en .claude/agents/${agentType}.md: léelo primero y sigue sus instrucciones y sus límites. ` + prompt, { ...resto, agentType: 'general-purpose' })
  }
}

// Verificación mecánica (scripts/verificacion.py V-A–V-E): forma única del veredicto, cierre que el verificador
// corre antes de devolver y una vuelta de reparación si quedan fallas; lo que siga fallando no se usa.
const FORMA_ITEM = '{"id", "veredicto": "verificada|ajustada|no_confirmada", "valor_final", "fuente_2", "url_2", "independencia": "alta|baja", "calculo"?, "serie_final"?, "partes_final"?, "nota"}'
const cierreVer = (ses, eje) =>
  `ANTES DE DEVOLVER corre python3 scripts/verificacion.py ${ses} --eje ${eje} y corrige cada FALLA: V-A, que la cita contenga el número o, si es derivado, «calculo» con la operación (p. ej. "(188442390/226077000-1)*100"); V-B, serie_final/partes_final con los puntos corregidos de una ajustada; V-C, independencia alta|baja (alta nunca con url_2 del mismo dominio que la primaria). Si no puedes, marca la cifra no_confirmada. Devuelve fallas_mecanicas[] con los ids que sigan fallando (vacío si 0). `
async function conMecanico(v, prompt, opts, ses, eje) {
  if (!v || !(v.fallas_mecanicas || []).length) return v
  avisar(`${eje}: verificacion.py deja ${v.fallas_mecanicas.length} falla(s) (${v.fallas_mecanicas.join(', ')}) → una vuelta de reparación.`)
  const r = await agentRol(`${prompt} REPARACIÓN: verificacion_${eje}.json ya existe; no repitas la verificación. Corre python3 scripts/verificacion.py ${ses} --eje ${eje} y corrige solo ${v.fallas_mecanicas.join(', ')} (o márcalas no_confirmada); devuelve el retorno completo del eje.`, { ...opts, label: `${opts.label}-mecanico` })
  const w = r || v
  const quedan = new Set(w.fallas_mecanicas || [])
  if (quedan.size) {
    avisar(`AVISO: ${eje}: ${[...quedan].join(', ')} siguen sin pasar verificacion.py; no se usan.`)
    w.ok = w.ok.filter((it) => !quedan.has(it.id))
    w.no_confirmadas = [...new Set([...(w.no_confirmadas || []), ...quedan])]
  }
  return w
}

// Rechequeo adversarial (referencias/roles/verificador.md «Rechequeo»): una invocación tras el guion sobre las
// pocas cifras que sostienen la conclusión; las que «caen» vuelven al guionista para quitarlas.
async function rechequear(ses, ids, extra, presupuesto) {
  if (!ids.length) return { items: [] }
  const r = await agentRol(
    `Eres el verificador en MODO RECHEQUEO (lee referencias/roles/verificador.md, sección «Rechequeo»). Sesión: ${ses}. ` +
      `Cifras que sostienen la conclusión: ${ids.join(', ')} (python3 scripts/digesto.py ${ses} --para verificador y --serie <id>; python3 scripts/verificacion.py ${ses} para sus avisos; no leas los JSON enteros). ${extra || ''}` +
      'Para cada una, ¿por qué podría estar mal? (definición o categoría distinta entre la base y el dato actual, periodo o universo mezclado, cifra preliminar revisada, segunda fuente que copia la primera). Busca una fuente de independencia alta si no la hay. ' +
      `Presupuesto: ${presupuesto}. No reescribas verificacion_*.json. Escribe ${ses}/rechequeo.json {"items": [{"id", "veredicto": "sostiene|matizar|caer", "motivo", "fuente"?, "url"?}]} y devuelve el mismo contenido.`,
    { agentType: 'hilo-verificador', schema: S.rechequeo, phase: 'Rechequeo', label: 'rechequeo' }
  )
  if (!r) { avisar('AVISO: el rechequeo no terminó; sigue la verificación de la primera pasada.'); return { items: [] } }
  const caen = r.items.filter((x) => x.veredicto === 'caer').map((x) => x.id)
  avisar(`Rechequeo: ${r.items.length} cifra(s) · ${caen.length} caen${caen.length ? ' (' + caen.join(', ') + ')' : ''} · ${r.items.filter((x) => x.veredicto === 'matizar').length} a matizar`)
  return r
}

// Bucle de reparación: valida el retorno y reinvoca con la lista de fallos.
async function conReparacion(etiqueta, invocar, validar, max = 2) {
  let fallos = []
  for (let intento = 0; intento <= max; intento++) {
    const r = await invocar(fallos, intento)
    if (!r) fail(`${etiqueta}: el agente no terminó.`)
    fallos = validar(r)
    if (!fallos.length) return r
    avisar(`${etiqueta}: ${fallos.length} fallo(s)${intento < max ? ` → reparación ${intento + 1}/${max}` : ''}:\n - ${fallos.join('\n - ')}`)
  }
  fail(`${etiqueta} rechazado tras ${max} reparaciones:\n - ${fallos.join('\n - ')}`)
}
// </comun>

// ── Schemas de retorno ─────────────────────────────────────────────────────
const INFORME_PLAN = {
  type: 'object', required: ['numero', 'capitulos'],
  properties: {
    numero: { type: 'string', pattern: '^\\d{2}$' },
    capitulos: {
      type: 'array', minItems: 1, maxItems: AUD ? 14 : 5,
      items: { type: 'object', required: ['n', 'titulo', 'ejes'], properties: { n: { type: 'string', pattern: '^\\d{2}$' }, titulo: { type: 'string', maxLength: 60 }, pregunta: { type: 'string' }, ejes: { type: 'array', minItems: 1, items: { type: 'string' } } } },
    },
  },
}
const VISUAL = {
  anyOf: [
    { type: 'null' },
    {
      type: 'object', required: ['plantilla', 'kicker', 'titular', 'fuente', 'cifra_ids', 'datos'],
      properties: {
        plantilla: { type: 'string', enum: PLANTILLAS }, kicker: { type: 'string' },
        titular: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'string' } },
        leyenda: { type: 'array', items: { type: 'string' } },
        nota: { type: 'string' }, fuente: { type: 'string' },
        cifra_ids: { type: 'array', minItems: 1, items: { type: 'string' } },
        datos: { type: 'object' },
      },
    },
  ],
}
const S = {
  encuadre: {
    type: 'object',
    required: ['slug', 'tema', 'pregunta', 'tesis_provisional', 'paleta', 'ejes', 'sesion_dir', 'fecha', 'smoke', 'informe'],
    properties: {
      slug: { type: 'string' }, tema: { type: 'string' }, pregunta: { type: 'string' },
      tesis_provisional: { type: 'string' }, angulo: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS },
      necesita_serie: { type: 'boolean' }, repetido: { type: 'boolean' },
      hook_evitar: { type: ['string', 'null'] },
      idea_id: { type: ['string', 'null'] },
      modo: { type: 'string', enum: ['investigacion'] },
      ejes: {
        type: 'array', minItems: 1, maxItems: AUD ? 14 : 5,
        items: {
          type: 'object', required: ['id', 'brief'],
          properties: {
            id: { type: 'string' }, prefijo: { type: 'string' }, brief: { type: 'string' },
            preguntas: { type: 'array', items: { type: 'string' } },
            fuentes_sugeridas: { type: 'array', items: { type: 'string' } },
            series_sugeridas: { type: 'array', items: { type: 'string' } },
          },
        },
      },
      informe: INFORME_PLAN,
      sesion_dir: { type: 'string' }, fecha: { type: 'string' }, smoke: { type: 'boolean' }, fixture: { type: 'boolean' },
    },
  },
  relectura: {
    type: 'object',
    required: ['slug', 'sesion_dir', 'tema', 'tesis', 'paleta', 'hook_tipo', 'ruta_hilo', 'n_tuits', 'tuits', 'ok_ids', 'informe'],
    properties: {
      slug: { type: 'string' }, sesion_dir: { type: 'string' }, tema: { type: 'string' }, tesis: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS }, hook_tipo: { type: 'string', enum: HOOKS }, modo_hilo: { type: 'string' },
      ruta_hilo: { type: 'string' }, fecha_hilo: { type: 'string' }, n_tuits: { type: 'integer' },
      tuits: { type: 'array', minItems: 3, items: { type: 'object', required: ['n', 'beat'], properties: { n: { type: 'integer' }, beat: { type: 'string', enum: BEATS }, imagen: { type: ['string', 'null'] }, plantilla: { type: ['string', 'null'] }, cifra_ids: { type: 'array', items: { type: 'string' } }, titular: { type: 'array', items: { type: 'string' } } } } },
      ok_ids: { type: 'array', items: { type: 'string' } },
      no_afirma: { type: 'array', items: { type: 'string' } },
      informe: INFORME_PLAN,
    },
  },
  hallazgos: {
    type: 'object',
    required: ['eje', 'archivo', 'n_busquedas', 'cifras'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string' }, n_busquedas: { type: 'number' }, n_fetch: { type: 'number' },
      cifras: {
        type: 'array', maxItems: AUD ? 60 : 16,
        items: {
          type: 'object', required: ['id', 'tipo'],
          properties: {
            id: { type: 'string' }, tipo: { type: 'string', enum: ['puntual', 'serie', 'desglose'] },
            n_puntos: { type: 'integer' }, candidata_ancla: { type: 'boolean' },
          },
        },
      },
      vacios: { type: 'array', items: { type: 'string' } },
      nuevas: { type: 'array', items: { type: 'string' } }, revisados: { type: 'array', items: { type: 'string' } },
      evaluacion: { type: 'object', properties: { archivo: { type: 'string' }, n_compromisos: { type: 'integer' }, validacion: { type: 'string', enum: ['ok', 'falla'] }, estados: { type: 'object' } } },
    },
  },
  rechequeo: {
    type: 'object',
    required: ['items'],
    properties: {
      archivo: { type: 'string' },
      items: { type: 'array', items: { type: 'object', required: ['id', 'veredicto', 'motivo'], properties: { id: { type: 'string' }, veredicto: { type: 'string', enum: ['sostiene', 'matizar', 'caer'] }, motivo: { type: 'string' }, fuente: { type: 'string' }, url: { type: 'string' } } } },
    },
  },
  verificacion: {
    type: 'object',
    required: ['eje', 'archivo', 'ok', 'no_confirmadas'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string' },
      ok: { type: 'array', items: { type: 'object', required: ['id'], properties: { id: { type: 'string' }, valor_final: { type: 'number' }, independencia: { type: 'string', enum: ['alta', 'baja'] } } } },
      no_confirmadas: { type: 'array', items: { type: 'string' } },
      fallas_mecanicas: { type: 'array', items: { type: 'string' } },
      revision: { type: 'object', properties: { revisados: { type: 'integer' }, corregidos: { type: 'array', items: { type: 'string' } }, sin_sustento: { type: 'array', items: { type: 'string' } }, validacion: { type: 'string', enum: ['ok', 'falla'] } } },
    },
  },
  puntaje: {
    type: 'object',
    required: ['global', 'global_con_dato', 'transcurrido', 'corte', 'n_compromisos', 'n_unicos', 'n_verificables', 'estados', 'semillas', 'cifras_aud', 'ejes_sin_evaluacion'],
    properties: {
      global: { type: ['number', 'null'] }, global_con_dato: { type: ['number', 'null'] }, global_compromisos: { type: ['number', 'null'] },
      transcurrido: { type: 'number' }, corte: { type: 'string' }, fiscal: { type: ['number', 'null'] },
      n_compromisos: { type: 'integer' }, n_unicos: { type: 'integer' }, n_verificables: { type: 'integer' }, estados: { type: 'object' },
      semillas: { type: 'array', items: { type: 'object', required: ['id', 'avance'], properties: { id: { type: ['integer', 'string'] }, avance: { type: ['number', 'null'] }, con_dato: { type: ['number', 'null'] }, n: { type: 'integer' }, verificables: { type: 'integer' } } } },
      cifras_aud: { type: 'array', items: { type: 'string' } },
      ejes_sin_evaluacion: { type: 'array', items: { type: 'string' } },
    },
  },
  guion: {
    type: 'object',
    required: ['archivo', 'tesis', 'ancla_id', 'paleta', 'hook_tipo', 'no_afirma', 'tuits', 'investigacion'],
    properties: {
      archivo: { type: 'string' }, tesis: { type: 'string' }, ancla_id: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS }, hook_tipo: { type: 'string', enum: HOOKS },
      no_afirma: { type: 'array', items: { type: 'string' } },
      modo: { type: 'string', enum: ['investigacion'] },
      investigacion: {
        type: 'object', required: ['numero', 'informe_dir', 'capitulos'],
        properties: {
          numero: { type: 'string', pattern: '^\\d{2}$' }, informe_dir: { type: 'string' },
          capitulos: { type: 'array', minItems: 1, items: { type: 'object', required: ['n', 'titulo', 'tuits'], properties: { n: { type: 'string' }, titulo: { type: 'string' }, tuits: { type: 'array', items: { type: 'integer' } } } } },
        },
      },
      tuits: {
        type: 'array', minItems: 3, maxItems: MAX_TUITS,
        items: {
          type: 'object', required: ['n', 'beat', 'texto', 'alt_text', 'visual'],
          properties: {
            n: { type: 'integer' }, beat: { type: 'string', enum: BEATS },
            texto: { type: 'string', maxLength: 400 }, alt_text: { type: 'string', maxLength: 1000 },
            visual: VISUAL,
          },
        },
      },
    },
  },
  lote_visual: {
    type: 'object',
    required: ['producidos'],
    properties: {
      producidos: {
        type: 'array',
        items: {
          type: 'object', required: ['n', 'archivo_html', 'archivo_png', 'gate'],
          properties: {
            n: { type: 'integer' }, plantilla_final: { type: 'string' },
            archivo_html: { type: 'string', pattern: 'tuit_\\d+\\.html$' }, archivo_png: { type: 'string', pattern: 'tuit_\\d+\\.png$' },
            gate: { type: 'string', enum: ['ok', 'falla'] },
            fuente_en_pie: { type: 'boolean' }, iteraciones: { type: 'integer' },
            dudoso: { type: 'boolean' }, nota: { type: 'string' },
          },
        },
      },
      omitidos: { type: 'array', items: { type: 'string' } },
    },
  },
  produccion: {
    type: 'object',
    required: ['ruta', 'n_tuits', 'n_png', 'estado', 'gates'],
    properties: {
      ruta: { type: 'string' }, n_tuits: { type: 'integer' }, n_png: { type: 'integer' },
      registro_id: { type: 'string' }, estado: { type: 'string', enum: ['listo', 'incompleto'] },
      gates: {
        type: 'object', required: ['mecanico', 'coherencia', 'validate'],
        properties: { mecanico: { type: 'string', enum: ['ok', 'falla'] }, coherencia: { type: 'string', enum: ['ok', 'incompleto', 'falla'] }, validate: { type: 'string', enum: ['ok', 'falla'] } },
      },
      avisos: { type: 'array', items: { type: 'string' } },
    },
  },
  informe: {
    type: 'object',
    required: ['archivo', 'numero', 'n_paginas', 'n_figuras', 'n_tablas', 'cifras_usadas', 'capitulos', 'tarjetas_incluidas', 'paginas', 'gates', 'iteraciones', 'lecturas_png'],
    properties: {
      archivo: { type: 'string', pattern: 'informe\\.json$' }, numero: { type: 'string', pattern: '^\\d{2}$' },
      n_paginas: { type: 'integer' }, n_figuras: { type: 'integer' }, n_tablas: { type: 'integer' },
      cifras_usadas: { type: 'array', items: { type: 'string' } },
      capitulos: {
        type: 'array', minItems: 1,
        items: { type: 'object', required: ['n', 'titulo', 'paginas', 'n_figuras'], properties: { n: { type: 'string' }, titulo: { type: 'string' }, paginas: { type: 'array', items: { type: 'integer' } }, n_figuras: { type: 'integer' }, n_tablas: { type: 'integer' } } },
      },
      tarjetas_incluidas: { type: 'array', items: { type: 'integer' } },
      paginas: { type: 'array', items: { type: 'object', required: ['n', 'tipo'], properties: { n: { type: 'integer' }, tipo: { type: 'string', enum: TIPOS_PAGINA }, id: { type: 'string' } } } },
      gates: { type: 'object', required: ['i', 'p'], properties: { i: { type: 'string', enum: ['ok', 'falla'] }, p: { type: 'string', enum: ['ok', 'falla'] } } },
      iteraciones: { type: 'integer' }, lecturas_png: { type: 'integer' },
      marcadores: { type: 'array', items: { type: 'string' } },
      avisos: { type: 'array', items: { type: 'string' } },
    },
  },
  revision: {
    type: 'object',
    required: ['archivo', 'vuelta', 'veredicto', 'revisadas', 'bloqueantes', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'revision_informe\\.json$' }, vuelta: { type: 'integer' },
      veredicto: { type: 'string', enum: ['ok', 'reparar'] }, revisadas: { type: 'integer' },
      bloqueantes: { type: 'integer' }, mejoras: { type: 'integer' },
      faltas: {
        type: 'array',
        items: {
          type: 'object', required: ['pagina', 'regla', 'gravedad', 'detalle', 'arreglo'],
          properties: {
            n: { type: 'integer' }, pagina: { type: 'integer' }, donde: { type: 'string' },
            regla: { type: 'string', pattern: '^(V[1-8]|R[1-6]|J[1-5])$' },
            gravedad: { type: 'string', enum: ['bloquea', 'mejora'] }, detalle: { type: 'string' }, arreglo: { type: 'string' },
          },
        },
      },
    },
  },
  cierre: {
    type: 'object',
    required: ['ruta', 'ruta_informe', 'pdf', 'n_paginas', 'registro_id', 'estado', 'gates'],
    properties: {
      ruta: { type: 'string' }, ruta_informe: { type: 'string' }, pdf: { type: 'string' }, n_paginas: { type: 'integer' },
      registro_id: { type: 'string' }, estado: { type: 'string', enum: ['listo', 'incompleto'] },
      gates: {
        type: 'object', required: ['informe', 'qa_visual', 'validate'],
        properties: { informe: { type: 'string', enum: ['ok', 'falla'] }, qa_visual: { type: 'string', enum: ['ok', 'incompleto', 'falla'] }, validate: { type: 'string', enum: ['ok', 'falla'] } },
      },
      avisos: { type: 'array', items: { type: 'string' } },
    },
  },
}

// ── Estado compartido entre fases ──────────────────────────────────────────
const CIF = new Map()
const VER = new Map()
let enc = null
let g = null
let okIds = null // null = fixture (los gates de ids los aplican ensamblar.py e informe.py sobre el disco)
let noConf = 0
let bajas = []
const ejesCaidos = []
let conVisual = []
let dudosos = []
let prod = null
let rutaHilo = null
const entregableDe = (slug) => `investigacion/${fecha}-${slug}`
const prefijoDe = (e) => String(e.prefijo || e.id.slice(0, 3)).toLowerCase()
const validarPlan = (inf, ejes) => {
  const F = []
  if (!inf) { F.push('falta informe {numero, capitulos[]}'); return F }
  if (inf.numero !== numero) F.push(`informe.numero ${inf.numero} ≠ ${numero} (el número lo da la directiva)`)
  const caps = inf.capitulos || []
  if (caps.length < minCap || caps.length > maxCap) F.push(`${caps.length} capítulos (deben ser ${minCap}–${maxCap} en ${modo})`)
  const ids = new Set((ejes || []).map((e) => e.id))
  for (const c of caps) for (const e of c.ejes || []) if (ids.size && !ids.has(e)) F.push(`capítulo ${c.n}: eje ${e} no existe (hay ${[...ids].join(', ')})`)
  const ns = caps.map((c) => c.n)
  if (new Set(ns).size !== ns.length) F.push('números de capítulo repetidos')
  const cubiertos = new Set(caps.flatMap((c) => c.ejes || []))
  const sinCap = [...ids].filter((e) => !cubiertos.has(e))
  if (sinCap.length) avisar(`AVISO: ejes sin capítulo en el plan: ${sinCap.join(', ')}`)
  return F
}

if (!desde) {
  // ── FASE 1: ENCUADRE ──────────────────────────────────────────────────────
  phase('Encuadre')
  enc = await agentRol(
    fixture
      ? `Eres el editor del flujo /investigacion (lee referencias/roles/editor.md, «Modo fixture» y «Modo investigación»). MODO FIXTURE: copia sesiones/_fixture a sesiones/fixture-${fecha.replace(/-/g, '')} con cp -R, ` +
        `edita el encuadre.json copiado poniendo fixture:true, smoke:true, fecha "${fecha}", sesion_dir "sesiones/fixture-${fecha.replace(/-/g, '')}", modo: "investigacion" e informe: {numero: "${numero}", capitulos: [{n: "01", titulo: "Del crudo al tanque", pregunta: "¿Cuánto subió el combustible?", ejes: ["precios"]}]}, y devuélvelo tal cual.`
      : REV
      ? `Eres el editor del flujo /investigacion en VARIANTE AUDITORÍA, MODO REVISIÓN: la sesión sesiones/${AUD.slug} ya existe. No crees, copies ni edites nada. ` +
        `Lee sesiones/${AUD.slug}/encuadre.json y devuélvelo tal cual (mismos campos y valores; no abras otros archivos).`
      : AUD
      ? `Eres el editor del flujo /investigacion en VARIANTE AUDITORÍA (lee referencias/roles/editor.md «Modo investigación» y referencias/flujo-investigacion.md «Variante auditoría»). ` +
        `Tema: "${tema}". Fecha: ${fecha}. Número del informe: ${numero}. MODO DEL POST: investigacion. Se audita el cumplimiento de: ${AUD.plan || AUD.inventario}. ` +
        `(1) mkdir -p sesiones/${AUD.slug} && cp ${AUD.inventario} sesiones/${AUD.slug}/compromisos.json (slug "${AUD.slug}", sesion_dir "sesiones/${AUD.slug}"). ` +
        `(2) Los ejes son EXACTAMENTE estos ${AUD.ejes.length} (id = prefijo): ${AUD.ejes.map((e) => `${e.id} «${e.nombre}» (${e.compromisos.length} compromisos)`).join(' · ')}. Para cada eje corre python3 scripts/auditoria.py sesiones/${AUD.slug} --eje <id> (no abras compromisos.json entero) y escribe brief (qué compromisos evalúa y con qué indicadores y fuentes), preguntas (3–6) y fuentes_sugeridas (python3 scripts/fuentes.py --tema "…" y las del inventario). ` +
        `(3) informe {numero: "${numero}", capitulos} con EXACTAMENTE estos capítulos: ${JSON.stringify(AUD.capitulos)}. ` +
        '(4) pregunta, tesis_provisional falsable y neutra (sin calificar al gobierno), ángulo; paleta neutra (no la del partido: evita cielo y jade); necesita_serie true; idea_id null; smoke false; modo "investigacion". ' +
        `Lee memoria/hilos.json solo para repetido y hook_evitar. Escribe sesiones/${AUD.slug}/encuadre.json completo con fecha "${fecha}" y devuélvelo.`
      : `Eres el editor del flujo /investigacion (lee referencias/roles/editor.md y referencias/contrato-sesion.md «Sesión investigación»). ` +
        `Tema: ${tema ? `"${tema}"` : '(no dado: elige uno de actualidad con datos duros y series largas)'}. Fecha: ${fecha}. Número del informe: ${numero}. MODO DEL POST: investigacion. ` + INSTR.editor +
        (idea ? `IDEA DEL BANCO: corre python3 scripts/ideas.py --ver ${idea} (no abras ideas/banco.json) y parte de su pregunta, ángulo, hook_sugerido, paleta_sugerida y datos; pon idea_id: "${idea}" en encuadre.json y en tu retorno. ` : 'idea_id: null. ') +
        `${smoke ? `MODO SMOKE: exactamente 1 eje y 1–2 capítulos, smoke:true; sin tema usa «${TEMA_SMOKE}». ` : 'Modo normal: 2–5 ejes y 2–5 capítulos, smoke:false; un eje incluye la pregunta de escala humana (beat impacto). '}` +
        `Usa python3 scripts/fuentes.py --tema "…" --series para las fuentes_sugeridas de cada eje (no abras memoria/fuentes.json). Cada eje lleva un prefijo de 3 letras único. ` +
        `Lee memoria/hilos.json solo para repetido y hook_evitar; python3 scripts/memoria.py --informes lista los informes previos. Crea sesiones/<slug>/ y escribe encuadre.json completo con fecha "${fecha}", modo: "investigacion" e informe{} (devuélvelo también).`,
    { agentType: 'hilo-editor', schema: S.encuadre, label: 'editor' }
  )
  if (!enc) fail('Encuadre sin resultado: el editor no terminó.')
  if (!enc.sesion_dir || !enc.ejes || !enc.ejes.length) fail('Encuadre incompleto: hacen falta sesion_dir y ejes.')
  if (!fixture && smoke && enc.ejes.length !== 1) fail(`Smoke exige exactamente 1 eje (hay ${enc.ejes.length}).`)
  if (!fixture && !smoke && enc.ejes.length < 2) fail('Modo normal exige ≥2 ejes.')
  if (AUD) {
    const esp = AUD.ejes.map((e) => e.id).join(',')
    const lleg = enc.ejes.map((e) => e.id).join(',')
    if (esp !== lleg) fail(`Auditoría: los ejes deben ser exactamente ${esp} (llegaron ${lleg}).`)
    for (const e of enc.ejes) if (prefijoDe(e) !== String(AUD.ejes.find((x) => x.id === e.id).prefijo)) fail(`Auditoría: el eje ${e.id} debe tener prefijo ${AUD.ejes.find((x) => x.id === e.id).prefijo}.`)
    if (enc.sesion_dir !== `sesiones/${AUD.slug}`) fail(`Auditoría: sesion_dir debe ser sesiones/${AUD.slug} (llegó ${enc.sesion_dir}).`)
    const capEsp = AUD.capitulos.map((c) => c.n).join(',')
    if (enc.informe.capitulos.map((c) => c.n).join(',') !== capEsp) fail(`Auditoría: los capítulos deben ser ${capEsp}.`)
  }
  {
    const pref = enc.ejes.map(prefijoDe)
    if (new Set(pref).size !== pref.length) fail(`Prefijos de eje repetidos (${pref.join(', ')}): cada eje necesita un prefijo de 3 letras único.`)
    const F = validarPlan(enc.informe, enc.ejes)
    if (F.length) fail(`Plan de capítulos rechazado:\n - ${F.join('\n - ')}`)
  }
  if (idea && enc.idea_id !== idea) avisar(`AVISO: el editor no devolvió idea_id "${idea}"; memoria.py no podrá marcar la idea (corrígelo en encuadre.json antes del registro).`)
  if (enc.modo && enc.modo !== modoPost) avisar(`AVISO: el editor devolvió modo ${enc.modo}; encuadre.json debe decir modo: "investigacion".`)
  if (enc.repetido) avisar('AVISO: tema ya cubierto en memoria/hilos.json; el editor declara ángulo nuevo en encuadre.json.')
  avisar(`Pregunta: ${enc.pregunta} · informe N.º ${numero} · paleta ${enc.paleta} · ${enc.ejes.length} eje(s) · ${enc.informe.capitulos.length} capítulo(s) · sesión ${enc.sesion_dir}${idea ? ' · idea ' + idea : ''}${fixture ? ' · FIXTURE' : ''}`)
} else {
  // ── FASE 1b: RELECTURA (desde:<slug>) ─────────────────────────────────────
  phase('Relectura')
  const sesionDesde = `sesiones/${desde}`
  const rl = await agentRol(
    `Eres el editor del flujo /investigacion en «Modo desde» (lee referencias/roles/editor.md, «Modo desde»). Sesión: ${sesionDesde}; hilo ya entregado en ${desdeHilo} (lee su hilo.json: tuits con imagen, plantilla, cifra_ids, titular; no lo modifiques). ` +
      `Número del informe: ${numero}. Fecha del informe: ${fecha}. Corre python3 scripts/digesto.py ${sesionDesde} --para guionista --solo-ok para los ids ok (no leas hallazgos_*.json ni verificacion_*.json enteros). ` +
      `Diseña informe {numero: "${numero}", capitulos[${minCap}–${maxCap}]{n, titulo ≤60, pregunta, ejes[]}} agrupando los tuits por eje o tema y AÑÁDELO a ${sesionDesde}/encuadre.json sin cambiar ningún otro campo. ` +
      `Devuelve slug "${desde}", sesion_dir "${sesionDesde}", tema, tesis (la del guion), paleta, hook_tipo, modo_hilo, ruta_hilo "${desdeHilo}", fecha_hilo, n_tuits, tuits[]{n, beat, imagen, plantilla, cifra_ids, titular}, ok_ids[], no_afirma[] e informe.`,
    { agentType: 'hilo-editor', schema: S.relectura, label: 'relectura' }
  )
  if (!rl) fail('Relectura sin resultado: el editor no terminó.')
  if (rl.slug !== desde) fail(`La relectura devolvió slug ${rl.slug}; se pidió ${desde}.`)
  if (rl.ruta_hilo.replace(/\/$/, '') !== desdeHilo) fail(`ruta_hilo ${rl.ruta_hilo} ≠ ${desdeHilo}.`)
  if (rl.n_tuits !== rl.tuits.length) fail(`n_tuits ${rl.n_tuits} ≠ ${rl.tuits.length} tuits devueltos.`)
  if ((rl.ok_ids || []).length < 6) fail(`Solo ${(rl.ok_ids || []).length} cifras ok en la sesión: no hay material para un informe (mínimo 6).`)
  {
    const F = validarPlan(rl.informe, null)
    if (F.length) fail(`Plan de capítulos rechazado:\n - ${F.join('\n - ')}`)
  }
  enc = { slug: desde, sesion_dir: rl.sesion_dir, tema: rl.tema, paleta: rl.paleta, informe: rl.informe, hook_evitar: null, idea_id: null, ejes: [] }
  g = { tesis: rl.tesis, hook_tipo: rl.hook_tipo, paleta: rl.paleta, no_afirma: rl.no_afirma || [], tuits: rl.tuits.map((t) => ({ n: t.n, beat: t.beat, visual: t.imagen ? { plantilla: t.plantilla || '', cifra_ids: t.cifra_ids || [], titular: t.titular || [] } : null })) }
  okIds = new Set(rl.ok_ids)
  rutaHilo = desdeHilo
  conVisual = g.tuits.filter((t) => t.visual)
  avisar(`Relectura: ${rl.tema} · ${rl.n_tuits} tuits (${conVisual.length} con tarjeta) · ${okIds.size} cifras ok · ${rl.informe.capitulos.length} capítulo(s) · informe N.º ${numero}`)
}
const slug = enc.slug
const entregable = smoke ? null : entregableDe(slug)
const informeDir = smoke ? enc.sesion_dir : entregable
const lecturasRed = AUD ? AUD_LIM.lecturas : QA.lecturas_redactor[modo], lecturasProd = QA.lecturas_productor[modo]

if (!desde && !fixture) {
  // ── FASE 2: INVESTIGACIÓN ⇢ VERIFICACIÓN (pipeline por eje, sin barrera) ──
  const idsDe = (eje) => (AUD ? (AUD.ejes.find((e) => e.id === eje.id) || {}).compromisos || [] : [])
  const investigarRev = (eje) => { const T = topesRev(eje), ses = enc.sesion_dir, ids = revIds(eje); return agentRol(
    `Eres el investigador del eje "${eje.id}" en MODO REVISIÓN de una auditoría ya hecha (lee referencias/roles/investigador.md «Modo investigación» y referencias/flujo-investigacion.md «Variante auditoría», «Revisión»). Sesión: ${ses}. ` +
      `Ya existen evaluacion_${eje.id}.json, hallazgos_${eje.id}.json y verificacion_${eje.id}.json de la primera pasada: no los rehagas desde cero; corrígelos y amplíalos en su lugar. Motivo de la revisión: ${REV.motivo || 'reglas nuevas de atribución y puntaje'}. ` +
      `Reglas (las aplica python3 scripts/auditoria.py ${ses} --validar ${eje.id}): ${INSTR_AUD.atribucion} ` +
      `TAREAS: (1) corre --validar ${eje.id}: añade base_fecha a cada meta y monto (sale de la evidencia que ya tienes; dilo en nota) y corrige observado y base_obs donde la comparación partía de antes de 2023 o de la base del plan (busca el nivel de 2023 o el primer dato del mandato, como cifra nueva). ` +
      `(2) Reinvestiga a fondo ${ids.length ? `estos compromisos: ${ids.join(', ')} (los no_verificable de la primera pasada y los que se medían contra una base anterior a 2023 o la del plan)` : 'solo lo que --validar marque'}. ` +
      'Para cada uno agota fuentes antes de dejarlo no_verificable: SICOIN/Minfin (ejecución por programa y actividad, metas físicas), informes presidenciales al Congreso (enero de 2025 y de 2026), memorias de labores 2024 y 2025 del ministerio, información pública de oficio (Ley de Acceso, art. 10), Segeplán (SIPLAN, SNIP), Guatecompras, INE, Banguat, SAT, registros administrativos (MSPAS/SIGSA, Mineduc), encuestas nacionales recientes, y prensa o centros de pensamiento que citen el documento oficial (dilo en nota). ' +
      'Si el indicador del plan no se mide desde 2023, busca un indicador oficial del mismo fenómeno medido dentro del mandato y dilo en el resumen; si tampoco hay, no_verificable con la nota de lo que buscaste. ' +
      `(3) Cifras nuevas: AÑÁDELAS a hallazgos_${eje.id}.json con ids que sigan la numeración (${prefijoDe(eje)}-cNN mayor que el último), con evidencia {url, cita, archivo_local}; no borres ni renumeres las existentes. ` +
      `(4) Escribe evaluacion_${eje.id}.json corregido (resumen y nota al día: nunca una comparación contra un dato anterior a 2023) y corre --validar ${eje.id} hasta OK. ` +
      `PRESUPUESTO de la revisión: ≤${T.busquedas} búsquedas, ≤${T.fetch} fetch, ≤${T.cifras} cifras nuevas. Sin Playwright MCP. ` +
      `Devuelve el resumen de hallazgos_${eje.id}.json COMPLETO (todas las cifras, viejas y nuevas: id, tipo, n_puntos; n_busquedas y n_fetch de esta revisión), nuevas[] (ids de cifras nuevas o cambiadas), revisados[] (compromisos que cambiaste) y evaluacion {archivo, n_compromisos, validacion, estados}.`,
    { agentType: 'hilo-investigador', schema: S.hallazgos, phase: 'Investigación', label: `revisar-${eje.id}` }
  ) }
  const investigar = (eje) => { if (REV) return investigarRev(eje); const T = topesEje(eje); return (
    agentRol(
      `Eres el investigador del eje "${eje.id}" (lee referencias/roles/investigador.md «Modo investigación» y referencias/contrato-sesion.md). Sesión: ${enc.sesion_dir} ` +
        `(lee encuadre.json: tu brief, preguntas y fuentes_sugeridas). Prefijo de ids: "${prefijoDe(eje)}-cNN". ` + INSTR.investigador +
        `PRESUPUESTO: ≤${T.busquedas} búsquedas, ≤${T.fetch} fetch, ≤${T.cifras} cifras, ≤${T.series} series; cada cifra con evidencia {url, cita, archivo_local}. ` +
        (AUD ? INSTR_AUD.investigador(enc.sesion_dir, eje.id, idsDe(eje), fecha) : '') +
        `Sin Playwright MCP. Escribe ${enc.sesion_dir}/hallazgos_${eje.id}.json completo y devuelve solo el resumen (ids, tipo, n_puntos).`,
      { agentType: 'hilo-investigador', schema: S.hallazgos, phase: 'Investigación', label: `investigar-${eje.id}` }
    )) }
  const verificar = async (h, eje) => {
    if (!h) { ejesCaidos.push(eje.id); return null }
    const T = topesEje(eje)
    if (AUD) {
      const ev = h.evaluacion || {}
      if (ev.validacion !== 'ok') avisar(`AVISO: ${eje.id}: evaluacion_${eje.id}.json no pasó auditoria.py --validar (${ev.validacion || 'sin dato'}); el puntaje marcará no_verificable lo que falte.`)
      if (ev.n_compromisos !== idsDe(eje).length) avisar(`AVISO: ${eje.id}: ${ev.n_compromisos} compromisos evaluados de ${idsDe(eje).length}.`)
    }
    if (REV) {
      const TR = topesRev(eje)
      if (h.n_busquedas > TR.busquedas || (h.n_fetch || 0) > TR.fetch || (h.nuevas || []).length > TR.cifras) avisar(`AVISO: revisión de ${eje.id} excedió el presupuesto (${h.n_busquedas} búsquedas, ${h.n_fetch || '?'} fetch, ${(h.nuevas || []).length} cifras nuevas).`)
    } else if (h.n_busquedas > T.busquedas || (h.n_fetch || 0) > T.fetch || h.cifras.length > T.cifras) avisar(`AVISO: ${eje.id} excedió el presupuesto (${h.n_busquedas} búsquedas, ${h.n_fetch || '?'} fetch, ${h.cifras.length} cifras).`)
    const formaVer = `{"eje": "${eje.id}", "items": [${FORMA_ITEM}]${AUD ? ', "compromisos": [...]' : ''}}`
    const prompt = REV
      ? `Eres el verificador del eje "${eje.id}" en MODO REVISIÓN (lee referencias/roles/verificador.md «Modo investigación»). Sesión: ${enc.sesion_dir}. verificacion_${eje.id}.json ya tiene los veredictos de la primera pasada: consérvalos. ` +
        `(1) Verifica SOLO las cifras nuevas o cambiadas: ${(h.nuevas || []).join(', ') || '(ninguna)'} (python3 scripts/digesto.py ${enc.sesion_dir} --eje ${eje.id} --para verificador; no leas hallazgos enteros): parte de la cita y del archivo local; una segunda fuente por cifra; ≤2 fetch por cifra; sus items reemplazan a los de mismo id en verificacion_${eje.id}.json. ` +
        `(2) Revisa de nuevo los compromisos cambiados (${(h.revisados || []).join(', ') || 'ninguno'}): base_fecha de 2023 o del mandato (nunca anterior), observado, base_obs y la operación; reemplaza su entrada en "compromisos" (confirmado | corregido, que puede traer base_fecha | sin_sustento). En los demás compromisos comprueba solo que su base_fecha corresponda a su evidencia (sin búsquedas). ` +
        `Reglas: ${INSTR_AUD.atribucion} ` +
        `(3) python3 scripts/auditoria.py ${enc.sesion_dir} --validar ${eje.id} --verificacion hasta OK. verificacion_${eje.id}.json queda con la forma ${formaVer}. ` +
        cierreVer(enc.sesion_dir, eje.id) +
        'Devuelve ok[] con TODAS las cifras ok del eje (viejas y nuevas: id, valor_final, independencia), no_confirmadas[] (todas), fallas_mecanicas[] y revision {revisados, corregidos[], sin_sustento[], validacion}.'
      : `Eres el verificador del eje "${eje.id}" (lee referencias/roles/verificador.md «Modo investigación»). Sesión: ${enc.sesion_dir}. ` +
      `Corre python3 scripts/digesto.py ${enc.sesion_dir} --eje ${eje.id} --para verificador (no leas ${h.archivo} entero). ` +
      `Verifica TODAS: ${h.cifras.map((c) => c.id).join(', ')}. Parte de la cita y del archivo local; una segunda fuente independiente por cifra; ≤2 fetch por cifra. ` + INSTR.verificador +
      `${smoke ? 'MODO SMOKE: cita + una segunda fuente; extremos de cada serie. ' : ''}` +
      (AUD ? INSTR_AUD.verificador(enc.sesion_dir, eje.id, idsDe(eje)) : '') +
      `Escribe ${enc.sesion_dir}/verificacion_${eje.id}.json completo con EXACTAMENTE esta forma: ${formaVer} (la clave es items, no cifras). ` + cierreVer(enc.sesion_dir, eje.id) +
      'Devuelve ok[] (id, valor_final, independencia), no_confirmadas[] y fallas_mecanicas[].'
    const opts = { agentType: 'hilo-verificador', schema: S.verificacion, phase: 'Verificación', label: `${REV ? 'reverificar' : 'verificar'}-${eje.id}` }
    let v = await agentRol(prompt, opts)
    if (!v) { avisar(`AVISO: el verificador de ${eje.id} no terminó; se reintenta una vez.`); v = await agentRol(prompt, { ...opts, label: `verificar-${eje.id}-2` }) }
    if (!v) { ejesCaidos.push(eje.id); return null }
    v = await conMecanico(v, prompt, opts, enc.sesion_dir, eje.id)
    if (AUD && (!v.revision || v.revision.validacion !== 'ok')) avisar(`AVISO: ${eje.id}: la revisión de compromisos no pasó auditoria.py --validar --verificacion; se usa la evaluación del investigador donde falte.`)
    return { eje: eje.id, hallazgos: h, verificacion: v }
  }
  const porEje = (await pipeline(enc.ejes, investigar, verificar)).filter(Boolean)
  if (ejesCaidos.length) avisar(`AVISO: ejes sin verificación (no se usan): ${ejesCaidos.join(', ')}`)
  if (porEje.length < (smoke ? 1 : 2)) fail(`Investigación/verificación incompleta: solo ${porEje.length} eje(s) terminaron.`)
  for (const r of porEje) {
    for (const c of r.hallazgos.cifras) {
      if (CIF.has(c.id)) fail(`Id de cifra duplicado entre ejes: ${c.id}`)
      CIF.set(c.id, c)
    }
    for (const it of r.verificacion.ok) VER.set(it.id, it)
    noConf += (r.verificacion.no_confirmadas || []).length
  }
  okIds = new Set(VER.keys())
  bajas = [...VER.values()].filter((it) => it.independencia === 'baja').map((it) => it.id)
  if (bajas.length) avisar(`AVISO: segunda fuente NO independiente (reproduce la primaria) en ${bajas.length} cifra(s): ${bajas.join(', ')}`)
  if (okIds.size < (smoke ? 3 : MP.minCifras)) fail(`Solo ${okIds.size} cifras verificadas/ajustadas: no hay material para una investigación (mínimo ${smoke ? 3 : MP.minCifras}).`)
  const seriesOk = [...okIds].filter((id) => CIF.get(id) && CIF.get(id).tipo === 'serie' && (CIF.get(id).n_puntos || 0) >= 5)
  const desglosesOk = [...okIds].filter((id) => CIF.get(id) && CIF.get(id).tipo === 'desglose')
  if (seriesOk.length < 2 || desglosesOk.length < 2) {
    const msg = `hay ${seriesOk.length} serie(s) ok con ≥5 puntos y ${desglosesOk.length} desglose(s) ok: el informe necesita al menos 2 y 2 (tablas y figuras propias).`
    if (smoke || AUD) avisar('AVISO ' + (AUD ? 'auditoría' : 'smoke') + ': ' + msg); else fail('Material insuficiente: ' + msg)
  }
  const total = okIds.size + noConf
  if (total && noConf / total >= 0.5) avisar(`AVISO: ${noConf} de ${total} cifras no se confirmaron (calidad de fuentes baja).`)
  avisar(`Verificación: ${okIds.size} cifras utilizables (${noConf} descartadas) · ${seriesOk.length} series con ≥5 puntos · ${desglosesOk.length} desgloses`)
}

// ── FASE 2b: PUNTAJE (solo auditoría; determinista vía auditoria.py) ───────
let pun = null
if (AUD) {
  // Rechequeo de auditoría: los compromisos que mueven la conclusión (cumplido, retroceso, incumplido,
  // no_atribuible) se revisan con la pregunta «¿por qué podría estar mal?» ANTES del puntaje final; lo que cae
  // entra como «corregido» en verificacion_<eje>.json y --calcular lo recoge.
  if (!fixture) {
    phase('Rechequeo')
    const rqa = await agentRol(
      `Eres el verificador en MODO RECHEQUEO DE AUDITORÍA (lee referencias/roles/verificador.md, «Rechequeo», y «Modo investigación»). Sesión: ${enc.sesion_dir}. ` +
        `(1) python3 scripts/auditoria.py ${enc.sesion_dir} --calcular y luego --resumen --para redactor. (2) Toma TODOS los compromisos en estado cumplido, retroceso, incumplido o no_atribuible (y, en metas, los que avanzan o retroceden por menos que el redondeo de la fuente). ` +
        `Para cada uno: ¿por qué podría estar mal? Atribución (el hecho es del mandato, desde el ${INI_TXT}; si ya existía antes, no_atribuible con existe_desde), base y dato actual con la MISMA definición y categoría (si la fuente cambió de nombre o de cobertura entre años, no son comparables), magnitud real del cambio, cifra preliminar revisada. ` +
        `Reglas: ${INSTR_AUD.atribucion} ` +
        `(3) Si un compromiso no se sostiene, añade o reemplaza su entrada en "compromisos" de verificacion_<eje>.json con veredicto corregido (estado y nota con el motivo y la fuente) o sin_sustento, y corre python3 scripts/auditoria.py ${enc.sesion_dir} --validar <eje> --verificacion hasta OK. No toques los items de cifras. ` +
        `Presupuesto: ${smoke ? '≤ 3 búsquedas y ≤ 4 fetch' : '≤ 10 búsquedas y ≤ 12 fetch en total'}. Escribe ${enc.sesion_dir}/rechequeo.json {"items": [{"id" (del compromiso), "veredicto": "sostiene|matizar|caer", "motivo", "fuente"?, "url"?}]} y devuelve el mismo contenido.`,
      { agentType: 'hilo-verificador', schema: S.rechequeo, phase: 'Rechequeo', label: 'rechequeo-auditoria' }
    )
    if (!rqa) avisar('AVISO: el rechequeo de auditoría no terminó; el puntaje usa la verificación de primera pasada.')
    else avisar(`Rechequeo de auditoría: ${rqa.items.length} compromiso(s) · ${rqa.items.filter((x) => x.veredicto === 'caer').length} corregidos · ${rqa.items.filter((x) => x.veredicto === 'matizar').length} a matizar`)
  }
  phase('Puntaje')
  pun = await agentRol(
    `Paso determinista de la auditoría (no escribas ni edites ningún archivo a mano). Sesión: ${enc.sesion_dir}. ` +
      `(1) python3 scripts/auditoria.py ${enc.sesion_dir} --calcular (sin dato oficial = 0; exit 1 = falta la evaluación de algún eje: sigue igual). (2) python3 scripts/auditoria.py ${enc.sesion_dir} --resumen | head -20 para comprobar. ` +
      'Devuelve EXACTAMENTE el JSON que imprimió --calcular (una línea), sin cambiar ningún número.',
    { agentType: 'hilo-guionista', schema: S.puntaje, phase: 'Puntaje', label: 'puntaje' }
  )
  if (!pun) fail('Puntaje sin resultado.')
  if (pun.ejes_sin_evaluacion.length) avisar(`AVISO: ejes sin evaluacion_<eje>.json: ${pun.ejes_sin_evaluacion.join(', ')} (sus compromisos quedan no_verificable).`)
  for (const id of pun.cifras_aud) {
    okIds.add(id)
    VER.set(id, { id, independencia: 'baja' })
    CIF.set(id, { id, tipo: ['aud-c02', 'aud-c03', 'aud-c05', 'aud-c07', 'aud-c08', 'aud-c09', 'aud-c10'].includes(id) ? 'puntual' : 'desglose' })
  }
  avisar(`Puntaje: avance global ${pun.global}% (sin dato = 0; con dato ${pun.global_con_dato}%) con ${pun.transcurrido}% del mandato transcurrido · ${pun.n_verificables}/${pun.n_unicos} compromisos verificables · ` +
    pun.semillas.map((x) => `${x.id === 'F' ? 'F' : 'S' + x.id} ${x.avance}%`).join(' · '))
}

if (!desde) {
  // ── FASE 3: GUION (síntesis + tuits, con reparación) ──────────────────────
  phase('Guion')
  const validarGuion = (gg) => {
    const Tt = gg.tuits, n = Tt.length
    const F = []
    if (n < minN || n > maxN) F.push(`el hilo tiene ${n} tuits (${minN}–${maxN} en modo investigacion${smoke ? ' ' + modo : ''})`)
    if (Tt.some((t, i) => t.n !== i + 1)) F.push('los tuits no están numerados 1..n')
    if (gg.paleta !== enc.paleta) F.push(`paleta del guion (${gg.paleta}) ≠ encuadre (${enc.paleta})`)
    if (Tt[0].beat !== 'gancho') F.push('T1 debe ser gancho')
    if (Tt[n - 1].beat !== 'cierre') F.push(`T${n} debe ser cierre`)
    const giros = Tt.filter((t) => t.beat === 'giro').length
    if (giros !== MP.giro) F.push('debe haber exactamente un giro')
    if (MP.impacto && !smoke && n >= 5 && !Tt.some((t) => t.beat === 'impacto')) F.push('con ≥5 tuits debe haber un beat impacto (escala humana)')
    const modoG = gg.modo || 'hilo'
    if (modoG !== modoPost) F.push(`modo del guion (${modoG}) ≠ investigacion: escribe modo: "investigacion" en guion.json`)
    const medios = Tt.slice(1, n - 1)
    // Bloque investigacion: número, carpeta del entregable y capítulos del encuadre con sus tuits.
    const inv = gg.investigacion
    if (!inv) F.push('falta el bloque investigacion {numero, informe_dir, capitulos[]}')
    else {
      if (inv.numero !== numero) F.push(`investigacion.numero ${inv.numero} ≠ ${numero}`)
      if (String(inv.informe_dir || '').replace(/\/$/, '') !== informeDir) F.push(`investigacion.informe_dir debe ser "${informeDir}" (llegó ${inv.informe_dir})`)
      const plan = enc.informe.capitulos.map((c) => c.n)
      const caps = Array.isArray(inv.capitulos) ? inv.capitulos : []
      const ns = caps.map((c) => c.n)
      if (JSON.stringify(ns) !== JSON.stringify(plan)) F.push(`investigacion.capitulos[].n debe ser exactamente ${plan.join(', ')} (los del encuadre; llegó ${ns.join(', ') || 'nada'})`)
      const asignados = caps.flatMap((c) => c.tuits || [])
      const medioN = medios.map((t) => t.n)
      const fuera = asignados.filter((k) => !medioN.includes(k))
      if (fuera.length) F.push(`investigacion.capitulos asigna tuits que no son intermedios: ${fuera.join(', ')}`)
      if (new Set(asignados).size !== asignados.length) F.push('investigacion.capitulos repite tuits entre capítulos')
      const sinCap = medioN.filter((k) => !asignados.includes(k))
      if (sinCap.length) F.push(`tuits intermedios sin capítulo: ${sinCap.map((k) => 'T' + k).join(', ')}`)
      for (const c of caps) if (!String(c.titulo || '').trim()) F.push(`capítulo ${c.n} sin título`)
    }
    // Cierre con el marcador del informe (solo ahí), medido con una URL en su lugar.
    const cierreTx = Tt[n - 1].texto || ''
    if (!cierreTx.includes(MARCADOR_INFORME)) F.push(`el cierre debe terminar con el marcador literal ${MARCADOR_INFORME}`)
    else if (pesoX(cierreTx.replace(MARCADOR_INFORME, 'https://x.co/i')) > 280) F.push(`el cierre con la URL del informe (peso 23) pesaría ${pesoX(cierreTx.replace(MARCADOR_INFORME, 'https://x.co/i'))} (>280)`)
    Tt.slice(0, n - 1).forEach((t) => { if ((t.texto || '').includes(MARCADOR_INFORME)) F.push(`T${t.n}: el marcador ${MARCADOR_INFORME} solo va en el cierre`) })
    if (/https?:/.test(JSON.stringify(Tt.map((t) => t.visual)))) F.push('ningún visual puede contener una URL')
    if (enc.hook_evitar && gg.hook_tipo === enc.hook_evitar) F.push(`hook_tipo ${gg.hook_tipo} es el del último hilo (hook_evitar); elige otro`)
    if (okIds && !okIds.has(gg.ancla_id)) F.push(`ancla_id ${gg.ancla_id} no está verificada`)
    const t1 = Tt[0].texto || '', p1 = pesoX(t1)
    if (p1 < 40 || p1 > 280) F.push(`T1 debe pesar 40–280 en X (pesa ${p1})`)
    if (t1.split('\n')[0].length > 90) F.push('T1: primera línea > 90')
    if (RE_LINK.test(t1)) F.push('T1 lleva enlace o dominio')
    if (!Tt[0].visual) avisar('AVISO: T1 sin visual (la portada del informe suele usar la tarjeta de T1).')
    if (Tt[0].visual && !Tt[0].visual.cifra_ids.includes(gg.ancla_id)) F.push('el visual de T1 no usa la cifra ancla')
    const numerosDe = (d) => {
      const out = []
      const rec = (x) => { if (typeof x === 'number') out.push(x); else if (Array.isArray(x)) x.forEach(rec); else if (x && typeof x === 'object') Object.entries(x).forEach(([k, v]) => { if (!['decimales', 'escala', 'destacar', 'clases', 'decimales_pildora', 'i', 'fila', 'col', 'miles', 'cortes', 'maximo', 'minimo_rotulo', 'desde', 'hasta', 'por_fila'].includes(k)) rec(v) }) }
      rec(d); return out
    }
    const formatos = (v) => { const a = Math.abs(v); const s = new Set([String(v), String(a), a.toFixed(1), a.toFixed(2), a.toLocaleString('en-US'), a.toLocaleString('en-US', { maximumFractionDigits: 2 })]); return [...s].filter((x) => x && x !== '0') }
    Tt.forEach((t, i) => {
      const tx = t.texto || '', p = pesoX(tx)
      if (i > 0 && i < n - 1 && p > 280) F.push(`T${t.n} pesa ${p} en X (>280)`)
      if (i > 0 && i < n - 1 && t.visual && p > 200) F.push(`T${t.n} con imagen pesa ${p} (>200): que la tarjeta hable`)
      if (i > 0 && p > 140 && p <= 200) avisar(`AVISO: T${t.n} pesa ${p} (ideal ≤140 con imagen).`)
      if (RE_BAIT.test(tx)) F.push(`T${t.n} contiene engagement bait`)
      const v = t.visual
      if (!v) { if (i > 0 && i < n - 1) F.push(`T${t.n} sin visual (obligatorio en T2..T${n - 1})`); return }
      const alt = (t.alt_text || '').trim()
      if (alt.length < 20) F.push(`T${t.n} alt_text < 20 caracteres`)
      if (okIds) {
        const fuera = v.cifra_ids.filter((c) => !okIds.has(c))
        if (fuera.length) F.push(`T${t.n} cifra_ids no verificadas: ${fuera.join(', ')}`)
      }
      const d = v.datos || {}
      for (const k of REQ[v.plantilla] || []) if (!(k in d)) F.push(`T${t.n} (${v.plantilla}) falta datos.${k}`)
      if (v.plantilla === 'linea') {
        if ((d.series || []).length > 4) F.push(`T${t.n} linea con más de 4 series`)
        const cortas = v.cifra_ids.filter((c) => CIF.get(c) && CIF.get(c).tipo === 'serie' && (CIF.get(c).n_puntos || 0) < 5)
        if (cortas.length) F.push(`T${t.n} linea con series de <5 puntos: ${cortas.join(', ')}`)
      }
      if (v.plantilla === 'pendiente' && (!Array.isArray(d.fechas) || d.fechas.length !== 2 || (d.items || []).length < 2 || (d.items || []).length > 6)) F.push(`T${t.n} pendiente: 2 fechas y 2–6 items`)
      if (v.plantilla === 'pesas' && (!Array.isArray(d.fechas) || d.fechas.length !== 2 || (d.items || []).length < 2 || (d.items || []).length > 8)) F.push(`T${t.n} pesas: 2 fechas y 2–8 items`)
      if (v.plantilla === 'dona' && ((d.partes || []).length < 2 || (d.partes || []).length > 5)) F.push(`T${t.n} dona: 2–5 partes`)
      if (v.plantilla === 'barras-h' && (d.items || []).length > 8) F.push(`T${t.n} barras-h: ≤8 items`)
      if (v.plantilla === 'barras-v' && (!Array.isArray(d.valores) || d.valores.length > 12 || (d.etiquetas || []).length !== d.valores.length)) F.push(`T${t.n} barras-v: ≤12 barras y etiquetas = valores`)
      if (v.plantilla === 'waffle' && !(d.porcentaje > 0 && d.porcentaje <= 100)) F.push(`T${t.n} waffle: porcentaje en (0,100]`)
      if (v.plantilla === 'mapa' && Object.keys(d.valores || {}).length < 12) F.push(`T${t.n} mapa: ≥12 departamentos con valor`)
      if (v.plantilla === 'calor' && ((d.filas || []).length * (d.columnas || []).length > 144 || (d.columnas || []).length > 12)) F.push(`T${t.n} calor: ≤12 columnas y ≤12 filas`)
      const largo = (x) => (Array.isArray(x) ? x.length : 0)
      if (['linea', 'barras-v'].includes(v.plantilla) && d.periodos != null) {
        const nP = largo(v.plantilla === 'linea' ? d.etiquetasX : d.etiquetas)
        const P = Array.isArray(d.periodos) ? d.periodos : null
        let prev = -1
        const malo = !P || P.length > 4 || P.some((q) => { const ok = q && q.nombre && Number.isInteger(q.desde) && Number.isInteger(q.hasta) && q.desde > prev && q.desde <= q.hasta && q.hasta < nP; prev = q ? q.hasta : prev; return !ok })
        if (malo) F.push(`T${t.n} ${v.plantilla}: periodos ≤4 con nombre y desde/hasta índices en orden, sin solaparse`)
      }
      if (v.plantilla === 'bullet' && (largo(d.items) < 1 || largo(d.items) > 6 || d.items.some((it) => typeof (it || {}).meta !== 'number' && typeof d.meta !== 'number'))) F.push(`T${t.n} bullet: 1–6 items, cada uno con meta (propia o común)`)
      if (v.plantilla === 'embudo') {
        const E = Array.isArray(d.etapas) ? d.etapas : []
        if (E.length < 2 || E.length > 6 || E.some((e, k) => k && (e || {}).valor > (E[k - 1] || {}).valor)) F.push(`T${t.n} embudo: 2–6 etapas que no crecen`)
        if (typeof d.misma_cohorte !== 'boolean') F.push(`T${t.n} embudo: misma_cohorte debe ser true o false`)
      }
      if (v.plantilla === 'divergente' && (largo(d.items) < 2 || largo(d.items) > 10)) F.push(`T${t.n} divergente: 2–10 items`)
      if (v.plantilla === 'apilada' && (largo(d.etiquetas) < 2 || largo(d.etiquetas) > 8 || largo(d.partes) < 2 || largo(d.partes) > 5 || d.partes.some((q) => largo((q || {}).valores) !== largo(d.etiquetas)))) F.push(`T${t.n} apilada: 2–8 filas, 2–5 partes y un valor por fila`)
      if (v.plantilla === 'piramide' && (largo(d.grupos) < 4 || largo(d.grupos) > 12 || largo((d.izquierda || {}).valores) !== largo(d.grupos) || largo((d.derecha || {}).valores) !== largo(d.grupos))) F.push(`T${t.n} piramide: 4–12 grupos y un valor por grupo en cada lado`)
      if (v.plantilla === 'treemap' && (largo(d.partes) < 3 || largo(d.partes) > 12)) F.push(`T${t.n} treemap: 3–12 partes`)
      if (v.plantilla === 'dispersion' && (largo(d.puntos) < 8 || largo(d.puntos) > 22 || largo(d.rotular) > 4)) F.push(`T${t.n} dispersion: 8–22 puntos y ≤4 rotulados`)
      if (v.plantilla === 'hemiciclo' && (largo(d.bloques) < 2 || largo(d.bloques) > 8 || !Number.isInteger(d.total) || d.bloques.reduce((s, b) => s + ((b || {}).curules || 0), 0) !== d.total)) F.push(`T${t.n} hemiciclo: 2–8 bloques cuyas curules suman total`)
      if (v.plantilla === 'multiples' && (largo(d.etiquetasX) < 4 || largo(d.paneles) < 4 || largo(d.paneles) > 9 || d.paneles.some((q) => largo((q || {}).valores) !== largo(d.etiquetasX)))) F.push(`T${t.n} multiples: ≥4 puntos, 4–9 paneles y un valor por punto`)
      if (v.plantilla === 'combinado' && (largo(d.etiquetas) < 3 || largo(d.etiquetas) > 12 || largo((d.barras || {}).valores) !== largo(d.etiquetas) || largo((d.linea || {}).valores) !== largo(d.etiquetas))) F.push(`T${t.n} combinado: 3–12 periodos y un valor de barras y de linea por periodo`)
      if (v.plantilla === 'linea-tiempo' && (largo(d.eventos) < 3 || largo(d.eventos) > 8 || d.eventos.some((e) => !(e || {}).fecha || !(e || {}).nombre || typeof (e || {}).valor !== 'number'))) F.push(`T${t.n} linea-tiempo: 3–8 eventos con fecha, nombre y valor`)
      if (v.plantilla === 'agrupadas' && (largo(d.etiquetas) < 2 || largo(d.etiquetas) > 6 || largo(d.series) < 2 || largo(d.series) > 3 || d.series.some((s) => largo((s || {}).valores) !== largo(d.etiquetas)))) F.push(`T${t.n} agrupadas: 2–6 categorías, 2–3 series y un valor por categoría`)
      if (v.plantilla === 'pictograma' && !(Number.isInteger(d.total) && d.total >= 2 && d.total <= 200 && Number.isInteger(d.destacado) && d.destacado >= 0 && d.destacado <= d.total)) F.push(`T${t.n} pictograma: total 2–200 y destacado 0–total, enteros`)
      if (v.plantilla === 'area-apilada' && (largo(d.etiquetasX) < 5 || largo(d.etiquetasX) > 30 || largo(d.partes) < 2 || largo(d.partes) > 5 || d.partes.some((q) => largo((q || {}).valores) !== largo(d.etiquetasX)))) F.push(`T${t.n} area-apilada: 5–30 puntos, 2–5 partes y un valor por punto`)
      if (v.plantilla === 'cascada' && (largo(d.pasos) < 2 || largo(d.pasos) > 8 || (!d.inicio && !d.fin) || d.pasos.some((q) => typeof (q || {}).valor !== 'number' || (q || {}).valor < 0 || !['suma', 'resta'].includes((q || {}).efecto)))) F.push(`T${t.n} cascada: 2–8 pasos {nombre, valor ≥ 0, efecto suma|resta} e inicio o fin`)
      if (v.titular.some((l) => !l.trim() || l.length > 26)) F.push(`T${t.n} titular: líneas de ≤26 caracteres`)
      if (!v.kicker.trim() || v.kicker.length > 45) F.push(`T${t.n} kicker vacío o >45`)
      if ((v.nota || '').length > 150) F.push(`T${t.n} nota >150`)
      if (!v.fuente.trim() || v.fuente.length > 70 || /^fuente:/i.test(v.fuente.trim())) F.push(`T${t.n} fuente vacía, >70 o con prefijo «Fuente:»`)
      // Dato héroe: el texto no repite la tarjeta.
      if (tx.trim()) {
        const linea = v.titular.find((l) => l.trim().length >= 8 && tx.toLowerCase().includes(l.trim().toLowerCase()))
        if (linea) F.push(`T${t.n} el texto repite una línea del titular: «${linea}»`)
        const repetidos = numerosDe(d).filter((num) => formatos(num).some((f) => new RegExp('(?<![\\d.,])' + f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?!\\d|[.,]\\d)').test(tx)))
        if (new Set(repetidos).size >= 2) { const msg = `T${t.n} el texto repite ${new Set(repetidos).size} números de su tarjeta (dato héroe)`; if (i === 0) F.push(msg); else avisar('AVISO: ' + msg) }
      }
      if (RE_SUPER.test(tx) || RE_SUPER.test(v.titular.join(' '))) {
        const largas = v.cifra_ids.filter((c) => CIF.get(c) && CIF.get(c).tipo === 'serie' && (CIF.get(c).n_puntos || 0) >= 10)
        if (okIds && !largas.length) F.push(`T${t.n} usa «récord/histórico» sin una serie ≥10 puntos en sus cifra_ids`)
      }
    })
    const visuales = Tt.filter((t) => t.visual)
    if (visuales.length < n - 2) F.push(`hay ${visuales.length} visuales; mínimo ${n - 2}`)
    if (n >= 5 && new Set(visuales.map((t) => t.visual.plantilla)).size === 1) avisar('AVISO: todas las tarjetas usan la misma plantilla.')
    return F
  }
  const capsTxt = enc.informe.capitulos.map((c) => `${c.n} «${c.titulo}» (ejes ${(c.ejes || []).join(', ')})`).join(' · ')
  const invocarGuion = (fallos) =>
      agentRol(
        `Eres el guionista (lee referencias/roles/guionista.md «Modo investigación», referencias/narrativa.md y referencias/diseno/graficos.md). Sesión: ${enc.sesion_dir}. ` +
          `Lee encuadre.json y corre python3 scripts/digesto.py ${enc.sesion_dir} --para guionista (no leas los hallazgos_*.json ni verificacion_*.json enteros; para copiar puntos de una serie usa --serie <id>). ` +
          `Paleta: ${enc.paleta}. Fecha: ${fecha}. hook_evitar: ${enc.hook_evitar || 'ninguno'}. MODO DEL POST: investigacion. Número del informe: ${numero}. informe_dir: "${informeDir}". Capítulos del encuadre: ${capsTxt}. ` + INSTR.guionista + (AUD ? INSTR_AUD.guionista(enc.sesion_dir) : '') +
          `ancla_id debe ser una cifra del visual de T1 (T1.visual.cifra_ids la incluye). ` +
          (okIds ? `Solo cifras verificada|ajustada con su valor_final: ${[...okIds].join(', ')}. ` : 'MODO FIXTURE: usa las cifras verificadas de la sesión copiada; 3–4 tuits. ') +
          (bajas.length ? `Cifras con segunda fuente NO independiente (reproduce la primaria): ${bajas.join(', ')}: no sostengas la ancla solo en ellas si hay alternativa; si las usas, decláralo en sintesis.incertidumbre. ` : '') +
          `${fixture ? 'smoke:true. ' : smoke ? 'MODO SMOKE: 4–6 tuits, smoke:true. ' : `${minN}–${maxN} tuits con un beat impacto, smoke:false. `}` +
          LIMITES + ' ' +
          (fallos.length ? `TU GUION ANTERIOR FUE RECHAZADO; corrige SOLO esto y vuelve a escribir guion.json completo:\n - ${fallos.join('\n - ')}\n` : '') +
          `Escribe ${enc.sesion_dir}/guion.json completo (con modo: "investigacion" y el bloque investigacion) y devuelve el mismo contenido compacto (con modo, el bloque investigacion y visual.datos en números crudos).`,
        { agentType: 'hilo-guionista', schema: S.guion, label: fallos.length ? 'guionista-reparacion' : 'guionista' }
      )
  g = await conReparacion('Guion', invocarGuion, validarGuion, 2)

  // Rechequeo adversarial de lo que sostiene el hilo (ancla, T1, segunda fuente baja); las aud-cNN son cálculo
  // propio sobre compromisos que ya pasaron su rechequeo de auditoría.
  if (!fixture) {
    phase('Rechequeo')
    const t1 = ((g.tuits[0] || {}).visual || {}).cifra_ids || []
    const usadas = new Set(g.tuits.flatMap((t) => (t.visual || {}).cifra_ids || []))
    const ids = [...new Set([g.ancla_id, ...t1, ...bajas.filter((b) => usadas.has(b))])].filter((x) => x && CIF.has(x) && !/^aud-/.test(x)).slice(0, smoke ? 3 : 8)
    const rq = await rechequear(enc.sesion_dir, ids, '', smoke ? '≤ 2 búsquedas y ≤ 3 fetch' : '≤ 8 búsquedas y ≤ 10 fetch en total')
    const caen = new Set(rq.items.filter((x) => x.veredicto === 'caer').map((x) => x.id))
    const matizar = rq.items.filter((x) => x.veredicto === 'matizar').map((x) => `${x.id}: ${x.motivo}`)
    if (caen.size || matizar.length) {
      for (const c of caen) okIds.delete(c)
      const pedido = [
        ...(caen.size ? [`el rechequeo descartó ${[...caen].join(', ')} (rechequeo.json): quítalas de cifra_ids, del texto y de la ancla y rehaz esos tuits con otras cifras verificadas`] : []),
        ...(matizar.length ? [`declara en sintesis.incertidumbre lo que el rechequeo pide matizar: ${matizar.join(' · ')}`] : []),
      ]
      const validarSinCaidas = (r) => [...validarGuion(r), ...r.tuits.filter((t) => ((t.visual || {}).cifra_ids || []).some((c) => caen.has(c))).map((t) => `T${t.n} usa una cifra descartada por el rechequeo`), ...(caen.has(r.ancla_id) ? ['ancla_id descartada por el rechequeo'] : [])]
      g = await conReparacion('Guion (rechequeo)', (f, i) => invocarGuion(i === 0 ? pedido : f), validarSinCaidas, 2)
    }
  }
  conVisual = g.tuits.filter((t) => t.visual)
  avisar(`Tesis: ${g.tesis} · gancho ${g.hook_tipo} · ${g.tuits.length} tuits (${g.tuits.map((t) => t.beat[0].toUpperCase()).join('')}) · ${conVisual.length} visuales · ${g.investigacion.capitulos.length} capítulos`)

  // ── FASE 4: VISUALES (lotes de 3 en paralelo, con reparación por tuit) ────
  phase('Visuales')
  const promptVisualista = (lote, reparar) =>
    `Eres un visualista (lee referencias/roles/visualista.md y referencias/diseno/graficos.md «Flujo del visualista» y «Checklist de QA visual»). ` +
    `Sesión: ${enc.sesion_dir} (guion.json es de solo lectura). Tus tuits: ${lote.map((t) => `T${t.n} (${t.visual.plantilla})`).join(', ')}. ` +
    `Para cada uno: python3 scripts/materializar.py ${enc.sesion_dir} --tuit N (exit 0), UN Read del PNG, checklist; correcciones SOLO en ${enc.sesion_dir}/visuales/tuit_N.ajuste.json y re-materializar. ` +
    `Las tarjetas se imprimen además a 156 px en el anexo del informe: nada de rótulos que solo se entiendan a 1080. Máximo ${smoke ? 1 : 3} iteraciones por visual.` + (reparar ? ` REPARACIÓN: estos tuits fallaron antes: ${reparar}.` : '')
  const producidos = new Map()
  let pendientes = conVisual
  for (let intento = 0; intento <= 2 && pendientes.length; intento++) {
    const lotes = []
    for (let i = 0; i < pendientes.length; i += LOTE) lotes.push(pendientes.slice(i, i + LOTE))
    const res = (await parallel(lotes.map((lote, idx) => () =>
      agentRol(promptVisualista(lote, intento ? lote.map((t) => `T${t.n}: ${(producidos.get(t.n) || {}).nota || 'sin producir'}`).join(' | ') : ''),
        { agentType: 'hilo-visualista', schema: S.lote_visual, phase: 'Visuales', effort: 'low', label: `visuales-${intento ? 'rep' + intento + '-' : ''}${idx + 1}` })
    ))).filter(Boolean)
    for (const p of res.flatMap((r) => r.producidos || [])) producidos.set(p.n, p)
    const fallidos = []
    for (const t of pendientes) {
      const p = producidos.get(t.n)
      const problemas = []
      if (!p) problemas.push('no fue producido')
      else {
        if (p.gate !== 'ok') problemas.push(`no pasa el gate de render: ${p.nota || ''}`)
        if (!new RegExp(`tuit_${t.n}\\.png$`).test(p.archivo_png || '')) {
          if (p.gate === 'ok' && new RegExp(`tuit_${t.n}\\.html$`).test(p.archivo_html || '')) avisar(`AVISO: T${t.n} reportó mal la ruta del PNG (${p.archivo_png}); se asume visuales/tuit_${t.n}.png`)
          else problemas.push(`el PNG no se llama tuit_${t.n}.png (${p.archivo_png})`)
        }
        if (p.fuente_en_pie === false) problemas.push('sin fuente en el pie')
        if (p.plantilla_final && p.plantilla_final !== t.visual.plantilla) avisar(`AVISO: T${t.n} cambió de ${t.visual.plantilla} a ${p.plantilla_final}: ${p.nota || ''}`)
      }
      if (problemas.length) { fallidos.push(t); producidos.set(t.n, { ...(p || { n: t.n }), nota: problemas.join('; ') }) }
    }
    pendientes = fallidos
    if (pendientes.length) avisar(`Visuales con fallos${intento < 2 ? ` → reparación ${intento + 1}/2` : ''}: ${pendientes.map((t) => `T${t.n} (${producidos.get(t.n).nota})`).join(' | ')}`)
  }
  if (pendientes.length) fail(`Visuales rechazados tras 2 reparaciones: ${pendientes.map((t) => `T${t.n}: ${producidos.get(t.n).nota}`).join(' | ')}`)
  dudosos = [...producidos.values()].filter((p) => p.dudoso).map((p) => `T${p.n}: ${p.nota || 'dudoso'}`)
  avisar(`Visuales: ${conVisual.length}/${conVisual.length} ok · ${dudosos.length} dudosos`)

  // ── FASE 5: PRODUCCIÓN DEL HILO (con una reparación; sin memoria todavía) ─
  phase('Producción')
  const reRuta = smoke ? /\/salida\/?$/ : new RegExp(`^investigacion/${fecha}-[a-z0-9-]+/hilo/?$`)
  const validarProd = (p) => {
    const F = []
    if (!p.ruta) F.push('ruta vacía')
    if (/^\//.test(p.ruta || '')) F.push(`la ruta debe ser RELATIVA a la raíz del repo (llegó absoluta: ${p.ruta})`)
    if (!reRuta.test(p.ruta || '')) F.push(smoke ? `en smoke/fixture la salida debe estar en ${enc.sesion_dir}/salida/ (ruta: ${p.ruta})` : `la ruta debe ser ${entregable}/hilo/ (ruta: ${p.ruta})`)
    if (p.registro_id !== 'pendiente') F.push('en Producción no se registra: registro_id debe ser "pendiente" (memoria.py corre en el Cierre)')
    if (p.n_tuits > g.tuits.length || p.n_tuits < minN) F.push(`n_tuits ${p.n_tuits} fuera de rango (guion ${g.tuits.length}, mínimo ${minN})`)
    if (p.n_png !== conVisual.length) F.push(`n_png ${p.n_png} ≠ ${conVisual.length} tarjetas del guion (todas van al anexo del informe)`)
    if (p.gates.mecanico !== 'ok') F.push(`gate mecánico: ${p.gates.mecanico}`)
    if (!['ok', 'incompleto'].includes(p.gates.coherencia)) F.push(`gate coherencia: ${p.gates.coherencia}`)
    if (p.gates.validate !== 'ok') F.push(`make validate: ${p.gates.validate}`)
    if (p.gates.coherencia === 'incompleto' && p.estado !== 'incompleto') F.push('coherencia incompleta exige estado incompleto')
    return F
  }
  const salidaArg = smoke ? '' : ` --salida ${entregable}/hilo`
  prod = await conReparacion(
    'Producción',
    (fallos) =>
      agentRol(
        `Eres el productor en la fase PRODUCCIÓN de /investigacion (lee referencias/roles/productor.md «Modo investigación» y referencias/narrativa.md). Sesión: ${enc.sesion_dir}. Fecha: ${fecha}. Gancho: ${g.hook_tipo}. Modo del post: investigacion. ` + INSTR.productor +
          `Tuits dudosos según los visualistas: ${dudosos.length ? dudosos.join(' | ') : 'ninguno'}. ` +
          `Ejecuta: (1) python3 scripts/materializar.py ${enc.sesion_dir} --consolidar; (2) python3 scripts/ensamblar.py ${enc.sesion_dir} --check${salidaArg} ` +
          `(si falla, corrige guion.json, re-materializa el tuit y repite; máx. 3 vueltas); (3) gate de coherencia C1–C8 con UN Read de contacto.png y tarjetas sueltas solo si son dudosas; ` +
          `(3b) con el veredicto de C1–C8: python3 scripts/ensamblar.py ${enc.sesion_dir} --solo-estado --estado listo|incompleto${salidaArg} (deja el estado final en hilo.json, hilo.html y post.md); ` +
          `(4) NO corras memoria.py (el informe aún no existe; se registra todo en el Cierre): registro_id = "pendiente"; (5) make validate (exit 0). ` +
          (smoke ? `MODO ${fixture ? 'FIXTURE' : 'SMOKE'}: la salida queda en ${enc.sesion_dir}/salida/, NO toques memoria/. ` : `El hilo se entrega en ${entregable}/hilo/ (carpeta del informe; make validate avisa de que aún no está registrado: es lo esperado). `) +
          LIMITES + ' Devuelve la ruta RELATIVA a la raíz del repo y los gates EXACTAMENTE como "ok" | "falla" | "incompleto" (los detalles van en avisos).' +
          (fallos.length ? `\nTU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}` : ''),
        { agentType: 'hilo-productor', schema: S.produccion, label: fallos.length ? 'productor-reparacion' : 'productor' }
      ),
    validarProd,
    1
  )
  rutaHilo = prod.ruta.replace(/\/$/, '')
  if (prod.estado === 'incompleto') avisar(`AVISO: el hilo queda INCOMPLETO (coherencia ${prod.gates.coherencia}); revisa post.md antes de publicar.`)
}

// ── FASE 6: INFORME (redactor, con dos reparaciones) ─────────────────────────
phase('Informe')
const tarjetasHilo = conVisual.map((t) => `T${t.n} tuit_${t.n}.png ${t.visual.plantilla || ''}${(t.visual.cifra_ids || []).length ? ' [' + t.visual.cifra_ids.join(',') + ']' : ''}`).join(' · ')
const nTarjetas = conVisual.map((t) => t.n)
const validarInforme = (r) => {
  const F = []
  if (r.archivo.replace(/^\.\//, '') !== `${enc.sesion_dir}/informe.json`) F.push(`archivo debe ser ${enc.sesion_dir}/informe.json (llegó ${r.archivo})`)
  if (r.numero !== numero) F.push(`numero ${r.numero} ≠ ${numero}`)
  if (r.gates.i !== 'ok' || r.gates.p !== 'ok') F.push(`el último informe.py --check no pasó (I: ${r.gates.i}, P: ${r.gates.p}): corrige y vuelve a correrlo hasta exit 0`)
  if (r.n_paginas < minPag || r.n_paginas > maxPag) F.push(`${r.n_paginas} páginas (deben ser ${minPag}–${maxPag} en ${modo})`)
  if (r.n_paginas !== r.paginas.length) F.push(`n_paginas ${r.n_paginas} ≠ ${r.paginas.length} páginas listadas`)
  const tipos = r.paginas.map((p) => p.tipo)
  const faltan = PAGINAS_OBLIGATORIAS[modo].filter((t) => !tipos.includes(t))
  if (faltan.length) F.push(`faltan páginas obligatorias: ${faltan.join(', ')}`)
  if (tipos[0] !== 'portada') F.push('la primera página debe ser portada')
  if (tipos[tipos.length - 1] !== 'contraportada') F.push('la última página debe ser contraportada')
  const plan = enc.informe.capitulos.map((c) => c.n)
  const ns = r.capitulos.map((c) => c.n)
  if (r.capitulos.length < minCap) F.push(`${r.capitulos.length} capítulos (mínimo ${minCap})`)
  const ajenos = ns.filter((k) => !plan.includes(k))
  if (ajenos.length) F.push(`capítulos fuera del plan del encuadre (${plan.join(', ')}): ${ajenos.join(', ')}`)
  const perdidos = plan.filter((k) => !ns.includes(k))
  if (perdidos.length) avisar(`AVISO: capítulos del plan sin página en el informe: ${perdidos.join(', ')} (el redactor lo justifica en avisos)`)
  for (const c of r.capitulos) if (!(c.n_figuras >= 1)) F.push(`capítulo ${c.n} sin figura con id (mínimo 1)`)
  for (const c of r.capitulos) if (!(c.paginas || []).length || (c.paginas || []).length < 2) F.push(`capítulo ${c.n} con ${(c.paginas || []).length} página(s): mínimo 2`)
  if (r.n_figuras < minFig) F.push(`${r.n_figuras} figuras (mínimo ${minFig})`)
  if (r.n_tablas < minTab) F.push(`${r.n_tablas} tablas (mínimo ${minTab})`)
  if (okIds) {
    const fuera = (r.cifras_usadas || []).filter((c) => !okIds.has(c))
    if (fuera.length) F.push(`cifras usadas sin verificar: ${fuera.join(', ')}`)
    if (!(r.cifras_usadas || []).length) F.push('cifras_usadas vacío: el informe debe citar cifras con id')
  }
  const sinTarjeta = nTarjetas.filter((k) => !(r.tarjetas_incluidas || []).includes(k))
  if (sinTarjeta.length) F.push(`tarjetas del hilo que no están en la página tarjetas (desde_hilo): ${sinTarjeta.map((k) => 'T' + k).join(', ')}`)
  if (r.iteraciones > iterInf) avisar(`AVISO: el redactor corrió informe.py ${r.iteraciones} veces (presupuesto ${iterInf}).`)
  if (r.lecturas_png > lecturasRed) avisar(`AVISO: el redactor leyó ${r.lecturas_png} PNG (presupuesto ${lecturasRed}).`)
  return F
}
const invocarRedactor = (fallos, intento, etiqueta) =>
    agentRol(
      `INFORME DE INVESTIGACIÓN · redactor · vuelta ${intento + 1}/${iterInf} (lee referencias/roles/redactor.md y referencias/diseno/informe.md).\n` +
        `Sesión: ${enc.sesion_dir} → escribe ${enc.sesion_dir}/informe.json; staging en ${enc.sesion_dir}/informe/ (html, pdf, figuras, png/).\n` +
        `Hilo YA ensamblado (no lo toques): ${rutaHilo} con datos.json, hilo.json y tuit_N.png · ${prod ? `estado ${prod.estado} · ` : ''}${g.tuits.length} tuits · hook ${g.hook_tipo}.\n` +
        `meta: titulo (lo eliges tú) · corrido «<Tema corto> · Informe de datos» · corto «<Tema corto>» · pie «Informe N.º ${numero} · ${mesAnio}» · numero_largo «Informe de datos · N.º ${numero}» · fecha «${mesAnio}» · numero "${numero}" · handle @DerekUrizar · paleta ${enc.paleta} · datos ["${rutaHilo}/datos.json"] · fuentes (las primarias del digesto).\n` +
        `Modo ${modo}: ${minPag}–${maxPag} páginas · ${minCap}–${maxCap} capítulos · ≥${minFig} figuras · ≥${minTab} tablas · páginas obligatorias: ${PAGINAS_OBLIGATORIAS[modo].join(', ')} · ≤${lecturasRed} lecturas de PNG · ≤${iterInf} corridas.\n` +
        `Plan de capítulos (encuadre.informe): ${enc.informe.capitulos.map((c) => `${c.n} «${c.titulo}»${c.ejes && c.ejes.length ? ' (ejes ' + c.ejes.join(', ') + ')' : ''}`).join(' · ')}. Cada capítulo del plan es un capítulo del PDF (≥2 páginas, ≥1 figura con id); si uno no tiene material, dilo en avisos.\n` +
        (okIds ? `Cifras ok (solo estas llevan id): ${[...okIds].join(', ')}.\n` : 'MODO FIXTURE: las cifras ok son las de la sesión copiada (el digesto las lista); sobrescribe el informe.json copiado.\n') +
        `Ancla: ${g.ancla_id || 'la del guion'} (portada.cifra; si no cabe en 5 caracteres, otra cifra ok de la tesis y avísalo). Tesis: ${g.tesis}.\n` +
        (bajas.length ? `Independencia baja: ${bajas.join(', ')} → decláralo en metodo.nota y en el pie de su figura o tabla.\n` : '') +
        `Tarjetas del hilo: ${tarjetasHilo || 'ninguna'} → reúsalas como figuras tarjeta + desde "${rutaHilo}/tuit_N.png" donde convenga y TODAS en la página tarjetas con desde_hilo: "${rutaHilo}" (tarjetas_incluidas = [${nTarjetas.join(', ')}]).\n` +
        `Insumos: encuadre.json · python3 scripts/digesto.py ${enc.sesion_dir} --para redactor --hilo ${rutaHilo}${AUD ? ' --max-bytes 60000' : ''} (y --eje <eje> si se recortó) · puntos exactos: --serie <id>.\n` +
        (AUD ? INSTR_AUD.redactor(enc.sesion_dir) + '\n' : '') +
        `Gate: python3 scripts/informe.py ${enc.sesion_dir} --check --salida ${enc.sesion_dir}/informe --png ${enc.sesion_dir}/informe/png (exit 0 = pasa I1–I7 y P1–P5).\n` +
        `El workflow gatea tu retorno: n_paginas en rango · tipos obligatorios · capitulos[].n ⊆ plan · cada capítulo ≥2 páginas y ≥1 figura con id · cifras_usadas ⊆ ok · tarjetas_incluidas ⊇ las del hilo · gates i y p en ok.\n` +
        (fallos.length ? `TU INFORME ANTERIOR FUE RECHAZADO; corrige SOLO esto (con Edit) y vuelve a pasar el gate:\n - ${fallos.join('\n - ')}\n` : '') +
        `Retorno: {archivo, numero, n_paginas, n_figuras, n_tablas, cifras_usadas[], capitulos[]{n, titulo, paginas[], n_figuras, n_tablas}, tarjetas_incluidas[], paginas[]{n, tipo, id}, gates{i, p}, iteraciones, lecturas_png, marcadores[], avisos[]}.`,
      { agentType: 'informe-redactor', schema: S.informe, label: etiqueta || (fallos.length ? 'redactor-reparacion' : 'redactor') }
    )
let inf = await conReparacion('Informe', (fallos, intento) => invocarRedactor(fallos, intento), validarInforme, 2)
avisar(`Informe N.º ${numero}: ${inf.n_paginas} páginas · ${inf.n_figuras} figuras · ${inf.n_tablas} tablas · ${inf.capitulos.length} capítulos · ${(inf.cifras_usadas || []).length} cifras · ${inf.iteraciones} corrida(s)`)

// ── FASE 6b: REVISIÓN (revisor: ¿de dónde sale cada cosa? → el redactor corrige) ─
phase('Revisión')
const archivoRev = `${enc.sesion_dir}/revision_informe.json`
const validarRevision = (r) => {
  const F = []
  if ((r.archivo || '').replace(/^\.\//, '') !== archivoRev) F.push(`archivo debe ser ${archivoRev} (llegó ${r.archivo})`)
  const bloq = (r.faltas || []).filter((f) => f.gravedad === 'bloquea').length
  if (r.bloqueantes !== bloq) F.push(`bloqueantes ${r.bloqueantes} ≠ ${bloq} faltas con gravedad bloquea`)
  if ((r.veredicto === 'ok') !== (bloq === 0)) F.push(`veredicto ${r.veredicto} con ${bloq} falta(s) que bloquean (ok solo sin ninguna)`)
  if (!(r.revisadas > 0)) F.push('revisadas debe ser el número de páginas leídas (> 0)')
  return F
}
const fmtFaltas = (fs) => fs.map((f) => `[${f.regla} · p. ${f.pagina}${f.donde ? ' · ' + f.donde : ''}] ${f.detalle} → ARREGLO: ${f.arreglo}`)
const revisar = (vuelta, previas) =>
  conReparacion(
    'Revisión',
    (fallos) =>
      agentRol(
        `REVISIÓN DE JUSTIFICACIÓN · revisor · vuelta ${vuelta}/${QA.vueltas_revision + 1} (lee referencias/roles/revisor.md). Sesión: ${enc.sesion_dir} · informe ${enc.sesion_dir}/informe.json (ya pasó I1–I7 y P1–P5; PNG en ${enc.sesion_dir}/informe/png/) · hilo ${rutaHilo}.\n` +
          `Insumos: python3 scripts/revision.py ${enc.sesion_dir}${AUD ? ` · python3 scripts/auditoria.py ${enc.sesion_dir} --justificar ${enc.sesion_dir}/informe.json · python3 scripts/auditoria.py ${enc.sesion_dir} --resumen --para redactor` : ''} · cotejo: python3 scripts/digesto.py ${enc.sesion_dir} --para redactor --hilo ${rutaHilo}.\n` +
          `Revisa V1–V8 en TODO el informe: cada figura se explica, cada valor tiene origen, cada % dice de qué es, cada afirmación lleva respaldo, coherencia, nada sin definir, nada falta, honestidad. ` +
          `EN LA PRIMERA VUELTA resuelve primero los avisos mecánicos (python3 scripts/revision.py ${enc.sesion_dir} --avisos: R1–R6${AUD ? '; y --justificar: J1–J5' : ''}): cada uno es una falta (regla R4, R6, J2…) o se descarta con motivo; así las vueltas siguientes solo comprueban arreglos. ` +
          (AUD ? 'AUDITORÍA: las fichas generadas cubren cada barra (J1–J5); exige además que el texto de cada capítulo explique los compromisos que pesan (cumplidos, retrocesos o incumplidos, ceros sin dato, hitos en proceso o anunciados que nombre). ' : '') +
          `Una falta por problema; arreglo con el texto exacto y solo cifras y fechas de los digestos. Escribe ${archivoRev}.\n` +
          (previas && previas.length ? `FALTAS DE LA VUELTA ANTERIOR (comprueba primero cada una):\n - ${fmtFaltas(previas).join('\n - ')}\n` : '') +
          (fallos.length ? `TU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}\n` : '') +
          'Retorno: {archivo, vuelta, veredicto: ok|reparar, revisadas, bloqueantes, mejoras, faltas[]{n, pagina, donde, regla, gravedad, detalle, arreglo}}.',
        { agentType: 'informe-revisor', schema: S.revision, label: `revisor-${vuelta}` }
      ),
    validarRevision,
    1
  )
let rev = await revisar(1, null)
for (let k = 0; k < QA.vueltas_revision && rev.bloqueantes > 0; k++) {
  const faltas = rev.faltas.filter((f) => f.gravedad === 'bloquea').concat(rev.faltas.filter((f) => f.gravedad === 'mejora'))
  avisar(`Revisión ${k + 1}: ${rev.bloqueantes} falta(s) que bloquean y ${rev.faltas.length - rev.bloqueantes} mejora(s) → el redactor corrige`)
  inf = await conReparacion(
    'Informe (revisión)',
    (fallos, intento) => invocarRedactor(intento === 0 ? ['REVISIÓN DE JUSTIFICACIÓN: corrige TODAS las faltas que bloquean y las mejoras que quepan (con Edit; el texto exacto viene en ARREGLO; si un arreglo pide una cifra que no está en el digesto, no la inventes: declara la falta de dato). Después vuelve a correr los gates:'].concat(fmtFaltas(faltas)) : fallos, intento, 'redactor-revision'),
    validarInforme,
    1
  )
  rev = await revisar(k + 2, rev.faltas)
}
const revPendiente = rev.bloqueantes > 0
if (revPendiente) avisar(`AVISO: la revisión de justificación deja ${rev.bloqueantes} falta(s) que bloquean tras ${QA.vueltas_revision} vueltas: el informe se entrega incompleto (${archivoRev}).`)
else avisar(`Revisión de justificación: ok (${rev.faltas.length} mejora(s) anotadas en ${archivoRev}).`)

// ── FASE 7: CIERRE (productor: informe final, QA, memoria, validate) ─────────
phase('Cierre')
const registroEsperado = fixture ? 'fixture' : smoke ? 'smoke' : `${fecha}-${slug}`
const validarCierre = (c) => {
  const F = []
  if (!c.ruta || /^\//.test(c.ruta)) F.push(`ruta vacía o absoluta (${c.ruta})`)
  const rutaEsp = smoke ? enc.sesion_dir : entregable
  if ((c.ruta || '').replace(/\/$/, '') !== rutaEsp) F.push(`la ruta debe ser ${rutaEsp} (llegó ${c.ruta})`)
  if (!new RegExp(smoke ? `^${enc.sesion_dir}/informe/informe\\.pdf$` : `^${entregable}/salida/informe\\.pdf$`).test(c.pdf || '')) F.push(`pdf debe ser ${smoke ? enc.sesion_dir + '/informe/informe.pdf' : entregable + '/salida/informe.pdf'} (llegó ${c.pdf})`)
  if (c.n_paginas !== inf.n_paginas) F.push(`n_paginas ${c.n_paginas} ≠ ${inf.n_paginas} del redactor`)
  if (c.gates.informe !== 'ok') F.push(`informe.py --check: ${c.gates.informe}`)
  if (!['ok', 'incompleto'].includes(c.gates.qa_visual)) F.push(`qa_visual: ${c.gates.qa_visual}`)
  if (c.gates.validate !== 'ok') F.push(`make validate: ${c.gates.validate}`)
  if (c.registro_id !== registroEsperado) F.push(`registro_id debe ser "${registroEsperado}" (llegó ${c.registro_id})`)
  const debeIncompleto = (prod && prod.estado === 'incompleto') || c.gates.qa_visual === 'incompleto' || revPendiente
  if (debeIncompleto && c.estado !== 'incompleto') F.push('el hilo, el QA visual o la revisión de justificación quedaron incompletos: estado debe ser incompleto')
  return F
}
const cierre = await conReparacion(
  'Cierre',
  (fallos) =>
    agentRol(
      `Eres el productor en la fase CIERRE de /investigacion (lee referencias/roles/productor.md «Modo investigación», apartado Cierre). Sesión: ${enc.sesion_dir}. Fecha: ${fecha}. Informe N.º ${numero} (${inf.n_paginas} páginas). Hilo en ${rutaHilo}${prod ? ` (estado ${prod.estado})` : ' (ya entregado y registrado: flujo desde)'}. ` +
        (smoke
          ? `MODO ${fixture ? 'FIXTURE' : 'SMOKE'}: (1) python3 scripts/informe.py ${enc.sesion_dir} --check --salida ${enc.sesion_dir}/informe --png ${enc.sesion_dir}/informe/png (exit 0); (2) QA del PDF con ≤${lecturasProd} Read de ${enc.sesion_dir}/informe/png/pagina_NN.png (portada y la página de tarjetas); si algo no se ve bien, corrige ${enc.sesion_dir}/informe.json y repite (≤2 vueltas; si persiste, qa_visual "incompleto"); (3) NO toques memoria/: registro_id = "${registroEsperado}"; (4) make validate (exit 0). Devuelve ruta "${enc.sesion_dir}", ruta_informe "${enc.sesion_dir}/informe.json" y pdf "${enc.sesion_dir}/informe/informe.pdf". `
          : `(1) mkdir -p ${entregable} && cp ${enc.sesion_dir}/informe.json ${entregable}/informe.json; (2) python3 scripts/informe.py ${entregable} --check --png ${enc.sesion_dir}/informe/png (exit 0; el PDF queda en ${entregable}/salida/); (3) QA del PDF con ≤${lecturasProd} Read de ${enc.sesion_dir}/informe/png/pagina_NN.png (portada, la página de tarjetas y una de capítulo); si algo no se ve bien, corrige ${enc.sesion_dir}/informe.json, vuelve a copiar y repite (≤2 vueltas; si persiste, qa_visual "incompleto"); ` +
            `(4) python3 scripts/memoria.py --registrar ${enc.sesion_dir} --ruta ${rutaHilo} --informe ${entregable} --estado listo|incompleto${desde ? ' --solo-informe' : ''} (${desde ? 'solo el informe: el hilo ya estaba registrado' : 'registra el hilo en hilos.json con modo investigacion, el informe en informes.json, series y fuentes' + (enc.idea_id ? ' y marca la idea ' + enc.idea_id : '')}); registro_id = "${registroEsperado}"; (5) make validate (exit 0). Devuelve ruta "${entregable}", ruta_informe "${entregable}/informe.json" y pdf "${entregable}/salida/informe.pdf". `) +
        `estado = "incompleto" si el hilo quedó incompleto, el QA visual lo está${revPendiente ? ' o (como ahora) la revisión de justificación dejó faltas que bloquean' : ''}; si no, "listo". Gates EXACTAMENTE como "ok" | "falla" | "incompleto"; los detalles van en avisos.` +
        (fallos.length ? `\nTU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}` : ''),
      { agentType: 'hilo-productor', schema: S.cierre, label: fallos.length ? 'cierre-reparacion' : 'cierre' }
    ),
  validarCierre,
  1
)
if (cierre.estado === 'incompleto') avisar('AVISO: la investigación queda INCOMPLETA; revisa los avisos antes de publicar.')

return {
  tesis: g.tesis,
  hook_tipo: g.hook_tipo,
  paleta: enc.paleta,
  numero,
  estado: cierre.estado,
  modo: modoPost,
  desde: desde || null,
  ruta: cierre.ruta,
  ruta_informe: cierre.pdf,
  ruta_hilo: rutaHilo,
  n_paginas: cierre.n_paginas,
  n_figuras: inf.n_figuras,
  revision: { archivo: archivoRev, veredicto: rev.veredicto, vueltas: rev.vuelta, bloqueantes: rev.bloqueantes, mejoras: rev.faltas.length - rev.bloqueantes },
  n_tablas: inf.n_tablas,
  capitulos: inf.capitulos,
  n_tuits: prod ? prod.n_tuits : g.tuits.length,
  n_png: prod ? prod.n_png : conVisual.length,
  beats: g.tuits.map((t) => t.beat),
  no_afirma: g.no_afirma,
  cifras_utilizables: okIds ? okIds.size : null,
  cifras_descartadas: noConf,
  cifras_usadas: inf.cifras_usadas,
  independencia_baja: bajas,
  ejes_caidos: ejesCaidos,
  visuales_dudosos: dudosos,
  marcadores: inf.marcadores || [],
  avisos_workflow: AVISOS_WF,
  avisos: [...((prod && prod.avisos) || []), ...(inf.avisos || []), ...(cierre.avisos || [])],
  sesion_dir: enc.sesion_dir,
  idea_id: enc.idea_id || null,
  auditoria: pun,
  smoke,
  fixture,
}
