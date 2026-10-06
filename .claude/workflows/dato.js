export const meta = {
  name: 'dato',
  description: 'Un dato impactante de Guatemala en UNA tarjeta 1080×1080: candidatas con evidencia → verificación → elección y tuit → producción con QA visual',
  whenToUse: 'Invocado por /dato [pista] [smoke|fixture]. args: {pista, smoke, fixture, fecha, permitir_fallback} (fecha YYYY-MM-DD obligatoria, la pone el comando con `date +%F`). pista = orientación opcional (tema, ángulo, fuente o corazonada); sin pista el investigador elige por su cuenta un dato impactante de actualidad. smoke = corrida corta con web sin tocar memoria/ (sin pista usa «remesas familiares 2025»); fixture = sin web, copia sesiones/_fixture_dato y corre solo el productor. No lee ni toca ideas/.',
  phases: [
    { title: 'Investigación', detail: 'investigador: pista → tema final, encuadre ligero (sesión, paleta, hook_evitar) y candidatas a dato impactante con evidencia e impacto' },
    { title: 'Verificación', detail: 'verificador: segunda fuente independiente por candidata, veredicto y valor_final' },
    { title: 'Guion', detail: 'guionista: puntúa las candidatas (1–5 × 5 criterios), elige UNA, hook_tipo y un solo tuit con visual y alt-text' },
    { title: 'Producción', detail: 'productor: QA visual (materializar → Read PNG → ajuste) → consolidar → ensamblar.py --check → C1/C5/C7/alt → memoria.py → make validate' },
  ],
}

// Guías: referencias/flujo-dato.md, referencias/contrato-sesion.md («Sesión dato»),
// referencias/roles/*.md («Modo dato»), referencias/narrativa.md («Dato único»).
// Cuatro agentes reutilizados de /hilo (no hay editor ni visualistas): el investigador
// hace el encuadre ligero y el productor el QA visual. Los agentes escriben su artefacto
// COMPLETO en sesiones/<slug>/ y devuelven un resumen validado por schema; los gates se
// aplican sobre los retornos (el sandbox no lee disco ni tiene Date: el slug lo decide el
// investigador y la fecha llega en args).

const PALETAS = ['cielo', 'jade', 'maiz', 'terracota', 'cacao', 'jacaranda', 'atitlan', 'obsidiana']
const PLANTILLAS = ['linea', 'barras-v', 'barras-h', 'antes-despues', 'dona', 'pendiente', 'waffle', 'cifra', 'mapa', 'pesas', 'calor', 'bullet', 'embudo', 'divergente', 'apilada', 'piramide', 'treemap', 'dispersion']
const HOOKS = ['giro_inversion', 'escala_humana', 'brecha_territorial', 'pregunta_directa', 'curiosity_gap', 'mito_vs_dato', 'antes_despues', 'titular_clasico']
const REQ = {
  linea: ['etiquetasX', 'series'], 'barras-v': ['etiquetas', 'valores'], 'barras-h': ['items'],
  'antes-despues': ['antes', 'despues'], dona: ['partes'], pendiente: ['fechas', 'items'],
  waffle: ['porcentaje', 'cifra'], cifra: ['cifra'], mapa: ['valores'], pesas: ['fechas', 'items'], calor: ['filas', 'columnas', 'valores'],
  bullet: ['items'], embudo: ['etapas', 'misma_cohorte'], divergente: ['items'], apilada: ['etiquetas', 'partes'],
  piramide: ['grupos', 'izquierda', 'derecha'], treemap: ['partes'], dispersion: ['puntos', 'ejeX', 'ejeY'],
}
const RE_LINK = /https?:\/\/|www\.|\.com\b|\.gt\b/i
const RE_BAIT = /(dale|da|dame|dejen?)\s+(rt|like|me gusta)|s[ií]gue(me|nos)|retuitea|comparte si|like si|guarda este|no te lo pierdas/i
const RE_SUPER = /r[ée]cord|hist[óo]ric[oa]|m[áa]s alt[oa] de la historia|nunca antes/i
// Superlativos relativos («el más bajo desde 2020», «el más alto en los últimos 5 años»): exigen serie o desglose ≥5 puntos.
const RE_RELATIVO = /m[áa]s (alt|baj|grand|car|barat)\w*\s+(desde|en los [úu]ltimos|de los [úu]ltimos|en \d+ a[ñn]os)/i
const RE_ID = /^dat-c\d{2}$/
const RE_SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/
const TOPES = { normal: { busquedas: 8, fetch: 8, cifras: 8, series: 2 }, smoke: { busquedas: 4, fetch: 4, cifras: 4, series: 1 } }
const ITER_VISUAL = { normal: 3, smoke: 1 }
const PISTA_SMOKE = 'remesas familiares 2025'

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

const VISUAL = {
  type: 'object', required: ['plantilla', 'kicker', 'titular', 'fuente', 'cifra_ids', 'datos'],
  properties: {
    plantilla: { type: 'string', enum: PLANTILLAS }, kicker: { type: 'string' },
    titular: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'string' } },
    leyenda: { type: 'array', items: { type: 'string' } },
    nota: { type: 'string' }, fuente: { type: 'string' },
    cifra_ids: { type: 'array', minItems: 1, items: { type: 'string' } },
    datos: { type: 'object' },
  },
}
const S = {
  // Retorno del investigador: encuadre ligero + resumen de hallazgos_dato.json.
  hallazgos_dato: {
    type: 'object',
    required: ['slug', 'sesion_dir', 'pista', 'tema', 'pregunta', 'paleta', 'archivo', 'n_busquedas', 'cifras'],
    properties: {
      slug: { type: 'string' }, sesion_dir: { type: 'string' },
      pista: { type: ['string', 'null'] }, tema: { type: 'string', maxLength: 80 }, pregunta: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS }, hook_evitar: { type: ['string', 'null'] }, repetido: { type: 'boolean' },
      archivo: { type: 'string', pattern: 'hallazgos_dato\\.json$' }, n_busquedas: { type: 'number' }, n_fetch: { type: 'number' },
      cifras: {
        type: 'array', minItems: 1, maxItems: 8,
        items: {
          type: 'object', required: ['id', 'tipo', 'impacto'],
          properties: {
            id: { type: 'string' }, tipo: { type: 'string', enum: ['puntual', 'serie', 'desglose'] },
            n_puntos: { type: 'integer' }, impacto: { type: 'string', maxLength: 160 }, candidata_ancla: { type: 'boolean' },
          },
        },
      },
      vacios: { type: 'array', items: { type: 'string' } },
    },
  },
  verificacion: {
    type: 'object',
    required: ['eje', 'archivo', 'ok', 'no_confirmadas'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string', pattern: 'verificacion_dato\\.json$' },
      ok: { type: 'array', items: { type: 'object', required: ['id'], properties: { id: { type: 'string' }, valor_final: { type: 'number' }, independencia: { type: 'string', enum: ['alta', 'baja'] } } } },
      no_confirmadas: { type: 'array', items: { type: 'string' } },
    },
  },
  guion_dato: {
    type: 'object',
    required: ['archivo', 'tipo', 'tesis', 'ancla_id', 'paleta', 'hook_tipo', 'dato', 'candidatas', 'no_afirma', 'tuits'],
    properties: {
      archivo: { type: 'string' }, tipo: { type: 'string', enum: ['dato'] }, tesis: { type: 'string' }, ancla_id: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS }, hook_tipo: { type: 'string', enum: HOOKS },
      dato: {
        type: 'object', required: ['cifra_id', 'titular', 'por_que_impacta'],
        properties: { cifra_id: { type: 'string' }, titular: { type: 'string', maxLength: 120 }, por_que_impacta: { type: 'string', maxLength: 300 } },
      },
      candidatas: {
        type: 'array', minItems: 1, maxItems: 8,
        items: {
          type: 'object', required: ['id', 'puntaje', 'elegida', 'motivo'],
          properties: {
            id: { type: 'string' }, puntaje: { type: 'integer', minimum: 5, maximum: 25 }, elegida: { type: 'boolean' }, motivo: { type: 'string', maxLength: 200 },
            criterios: {
              type: 'object',
              properties: {
                sorpresa: { type: 'integer', minimum: 1, maximum: 5 }, magnitud: { type: 'integer', minimum: 1, maximum: 5 },
                comparacion: { type: 'integer', minimum: 1, maximum: 5 }, actualidad: { type: 'integer', minimum: 1, maximum: 5 }, solidez: { type: 'integer', minimum: 1, maximum: 5 },
              },
            },
          },
        },
      },
      no_afirma: { type: 'array', items: { type: 'string' } },
      tuits: {
        type: 'array', minItems: 1, maxItems: 1,
        items: {
          type: 'object', required: ['n', 'beat', 'texto', 'alt_text', 'visual'],
          properties: { n: { type: 'integer' }, beat: { type: 'string', enum: ['gancho'] }, texto: { type: 'string', maxLength: 400 }, alt_text: { type: 'string', maxLength: 1000 }, visual: VISUAL },
        },
      },
    },
  },
  produccion_dato: {
    type: 'object',
    required: ['ruta', 'n_png', 'estado', 'gates', 'iteraciones_visual'],
    properties: {
      ruta: { type: 'string' }, n_png: { type: 'integer' }, registro_id: { type: 'string' },
      estado: { type: 'string', enum: ['listo', 'incompleto'] },
      iteraciones_visual: { type: 'integer' }, dudoso: { type: 'boolean' }, plantilla_final: { type: 'string' },
      gates: {
        type: 'object', required: ['mecanico', 'coherencia', 'validate'],
        properties: { mecanico: { type: 'string', enum: ['ok', 'falla'] }, coherencia: { type: 'string', enum: ['ok', 'incompleto', 'falla'] }, validate: { type: 'string', enum: ['ok', 'falla'] } },
      },
      // Solo lo exige el modo fixture (no hay guionista): lo copia de guion.json.
      resumen: {
        type: 'object',
        properties: { titular: { type: 'string' }, cifra_id: { type: 'string' }, hook_tipo: { type: 'string' }, plantilla: { type: 'string' }, paleta: { type: 'string' }, texto: { type: 'string' }, alt_text: { type: 'string' } },
      },
      avisos: { type: 'array', items: { type: 'string' } },
    },
  },
}

// Resumen de límites que viaja en los prompts: así nadie lee dato.js ni ensamblar.py.
const LIMITES =
  'LÍMITES (los comprueba el workflow y ensamblar.py --check en modo dato): EXACTAMENTE un tuit {n:1, beat:"gancho"} con visual obligatorio y hook_tipo; ' +
  'el texto es el tuit entero: 40–280 de peso X (URL=23, emoji=2), primera línea ≤90, sin enlaces ni engagement bait; ' +
  'dato héroe: el texto no repite ninguna línea del titular de la tarjeta ni ≥2 de sus números (da el «y qué», el contexto o la salvedad; la cifra ya está en la imagen); ' +
  'alt_text 20–1000 (tipo de gráfico, cifra con unidad y periodo, fuente); hook_tipo ∈ los ocho y ≠ hook_evitar; curiosity_gap y pregunta_directa solo si el titular de la tarjeta paga el gap; ' +
  `plantilla ∈ ${PLANTILLAS.join('|')} (cifra por defecto); kicker ≤45; titular 1–3 líneas de ≤26 (es el hallazgo); nota ≤150; fuente 1–70 sin «Fuente:»; sin URLs en la tarjeta; ` +
  'cifra_ids ⊆ verificadas e incluye dato.cifra_id; datos con números crudos de esas cifras y formato (en cifra: cifra.valor y comparacion.valor se cotejan; contexto ≤60 y su aritmética sale de esos dos valores); ' +
  'linea ≥5 puntos y ≤4 series; dona 2–5; barras-h ≤8; barras-v ≤12; pendiente 2 fechas y 2–6; mapa ≥12 departamentos; pesas 2–8; calor filas×columnas ≤12; bullet 1–6 con meta; ' +
  'embudo 2–6 etapas no crecientes y misma_cohorte true|false; divergente 2–10; apilada 2–8 filas y 2–5 partes; piramide 4–12 grupos; treemap 3–12; dispersion 8–22 puntos con ejeX/ejeY; periodos (linea, barras-v) ≤4 por índices; ' +
  '«récord/histórico» solo con serie ≥10 puntos cuyo máximo sea el valor; candidatas[] cubre TODAS las cifras verificadas (una elegida:true = dato.cifra_id, el resto con motivo).'

// ── Argumentos ─────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { pista: args } : (args || {})
const pistaBruta = String(A.pista || A.tema || '') // `tema` solo como alias tolerado
const fixture = !!A.fixture || /\bfixture\b/i.test(pistaBruta)
const smoke = fixture || !!A.smoke || /\bsmoke\b/i.test(pistaBruta)
// Pista literal del usuario (o null). En smoke sin pista, una fija (como hilo con «remesas familiares 2025»).
const pistaUsuario = pistaBruta.replace(/\b(smoke|fixture)\b/gi, '').trim() || null
const pista = pistaUsuario || (smoke && !fixture ? PISTA_SMOKE : null)
const fecha = String(A.fecha || '')
if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) throw new Error('args.fecha (YYYY-MM-DD) es obligatoria: /dato la obtiene con `date +%F` y la pasa en args.')
const modo = smoke ? 'smoke' : 'normal'
const T = TOPES[modo]
const maxIter = ITER_VISUAL[modo]
const sesionFixture = `sesiones/fixture-dato-${fecha.replace(/-/g, '')}`
const fail = (msg) => { throw new Error(msg) }
// Los avisos del workflow viajan también en el retorno (el journal no conserva los log()).
const AVISOS_WF = []
const avisar = (m) => { AVISOS_WF.push(String(m)); log(m) }

// Los roles viven en .claude/agents/hilo-*.md (los mismos de /hilo) y se registran al
// arrancar la sesión. Si no existen se falla con instrucciones claras; solo con
// args.permitir_fallback se degrada a general-purpose.
const agentRol = async (prompt, opts) => {
  try {
    return await agent(prompt, opts)
  } catch (e) {
    if (!opts || !opts.agentType || !/agent type .* not found/i.test(String(e && e.message))) throw e
    if (!A.permitir_fallback) fail(`El agente ${opts.agentType} no está registrado en esta sesión (los .claude/agents/ se cargan al arrancar). Reinicia Claude Code y vuelve a lanzar /dato, o pasa args.permitir_fallback: true para correr con general-purpose.`)
    avisar(`AVISO: ${opts.agentType} no registrado; se usa general-purpose (permitir_fallback).`)
    const { agentType, ...resto } = opts
    return agent(`Asume el rol definido en .claude/agents/${agentType}.md: léelo primero y sigue sus instrucciones y sus límites. ` + prompt, { ...resto, agentType: 'general-purpose' })
  }
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

// ── FASE 1: INVESTIGACIÓN (incluye el encuadre ligero) ──────────────────────
const CIF = new Map()
const VER = new Map()
let enc = null      // encuadre ligero (lo devuelve el investigador)
let okIds = null    // null = fixture (los gates de ids los aplica ensamblar.py sobre el disco)
let noConf = 0
let bajas = []      // cifras cuya segunda fuente reproduce la primaria (independencia baja)
let g = null        // guion (null en fixture)

if (fixture) {
  enc = { slug: sesionFixture.replace(/^sesiones\//, ''), sesion_dir: sesionFixture, tema: 'fixture dato', pista: null, paleta: null, hook_evitar: null }
  avisar(`FIXTURE: el productor copiará sesiones/_fixture_dato a ${sesionFixture} y correrá solo la producción.`)
} else {
  phase('Investigación')
  const hal = await agentRol(
    `Eres el investigador del flujo /dato (lee referencias/roles/investigador.md, sección «Modo dato», y referencias/contrato-sesion.md, «Sesión dato»). Fecha: ${fecha}. ${smoke ? 'MODO SMOKE: presupuesto corto. ' : 'Modo normal. '}` +
      (pista
        ? `PISTA del usuario: «${pista}». Es una orientación, no un encargo cerrado: puede ser un tema, un ángulo, una fuente o una corazonada. Úsala para empezar y desvíate si en su vecindad (misma área o misma fuente) encuentras un dato más fuerte; el tema final lo decides tú. `
        : 'SIN PISTA: elige por tu cuenta UN dato impactante de actualidad sobre Guatemala: empieza por publicaciones recientes de fuentes oficiales (boletines, tableros, informes de las últimas semanas) y por python3 scripts/fuentes.py --tema "…" --series en distintas áreas; quédate con el área donde hay un dato duro que sorprenda. ') +
      `ENCUADRE LIGERO (no hay editor, lo haces tú): (1) corre python3 scripts/memoria.py --datos "<tema>" (y sin tema) para no repetir un dato ya publicado y para hook_evitar = hook de la primera línea de la lista sin tema (el dato más reciente; null si no hay); lee memoria/hilos.json SOLO para marcar repetido si el tema ya tuvo hilo. ` +
      `(2) Elige la paleta por tema (design/tokens.json → paletas.*.temas). (3) Crea sesiones/<slug>/ (slug del tema final: minúsculas, sin tildes, guiones, sin fecha; si la carpeta existe, sufijo -2) y escribe encuadre.json ` +
      `{slug, pista: ${pista ? JSON.stringify(pista) : 'null'}, tema (el tema final que elegiste: ≤80 caracteres, sin dos puntos; el detalle va en pregunta y brief), fecha: "${fecha}", tipo: "dato", paleta, pregunta, hook_evitar, repetido, sesion_dir: "sesiones/<slug>", smoke: ${smoke}, fixture: false, ejes: [{id: "dato", prefijo: "dat", brief, preguntas[], fuentes_sugeridas[]}]} ` +
      `con la salida de python3 scripts/fuentes.py --tema "<tema final>" --series (no abras memoria/fuentes.json). ` +
      `INVESTIGACIÓN: busca CANDIDATAS a dato impactante (no una historia): cifras que sorprendan, contradigan la intuición o tengan escala humana, con comparación clara (antes/después, Guatemala vs región, per cápita, departamento vs país). ` +
      `Ids "dat-cNN". PRESUPUESTO: ≤${T.busquedas} búsquedas, ≤${T.fetch} fetch, ≤${T.cifras} cifras, ≤${T.series} series. Cada cifra con evidencia {url, cita, archivo_local} y un campo impacto (una línea ≤160: por qué sorprende o a qué escala humana se traduce). ` +
      `Si una candidata vive de una comparación, captura los dos lados (en partes[] o como cifra aparte); «récord/histórico» solo con la serie completa (≥10 puntos). Sin Playwright MCP. ` +
      `Escribe sesiones/<slug>/hallazgos_dato.json COMPLETO (eje: "dato") y devuelve solo el resumen: slug, sesion_dir, pista, tema, pregunta, paleta, hook_evitar, repetido, archivo, n_busquedas, n_fetch, cifras[]{id, tipo, n_puntos, impacto}, vacios[].`,
    { agentType: 'hilo-investigador', schema: S.hallazgos_dato, label: 'investigador' }
  )
  if (!hal) fail('Investigación sin resultado: el investigador no terminó.')
  if (!RE_SLUG.test(hal.slug) || /^(_|fixture-)/.test(hal.slug)) fail(`slug inválido: "${hal.slug}" (minúsculas, sin tildes, guiones, sin fecha, sin prefijo _ ni fixture-).`)
  if (hal.sesion_dir !== `sesiones/${hal.slug}`) fail(`sesion_dir (${hal.sesion_dir}) debe ser sesiones/${hal.slug}.`)
  const malos = hal.cifras.filter((c) => !RE_ID.test(c.id)).map((c) => c.id)
  if (malos.length) fail(`Ids de cifra fuera del patrón dat-cNN: ${malos.join(', ')}`)
  if (new Set(hal.cifras.map((c) => c.id)).size !== hal.cifras.length) fail('Ids de cifra repetidos en hallazgos_dato.json')
  if (hal.n_busquedas > T.busquedas || (hal.n_fetch || 0) > T.fetch || hal.cifras.length > T.cifras) avisar(`AVISO: el investigador excedió el presupuesto (${hal.n_busquedas} búsquedas, ${hal.n_fetch || '?'} fetch, ${hal.cifras.length} cifras).`)
  if (hal.cifras.length < 3) avisar(`AVISO: solo ${hal.cifras.length} candidata(s); el guionista tendrá poco donde elegir.`)
  if (hal.repetido) avisar('AVISO: tema ya cubierto en memoria/; el investigador declara ángulo o periodo nuevo en encuadre.json.')
  if ((hal.pista || null) !== pista) avisar(`AVISO: el investigador devolvió pista ${JSON.stringify(hal.pista || null)}; la directiva traía ${JSON.stringify(pista)} (corrígelo en encuadre.json si importa para el registro).`)
  if (pista && hal.tema && hal.tema.toLowerCase() !== pista.toLowerCase()) avisar(`Pista «${pista}» → tema final «${hal.tema}».`)
  for (const c of hal.cifras) CIF.set(c.id, c)
  enc = hal
  avisar(`Tema: ${enc.tema}${pista ? ` (pista: «${pista}»)` : ' (sin pista)'} · pregunta: ${enc.pregunta} · paleta ${enc.paleta} · ${hal.cifras.length} candidatas · sesión ${enc.sesion_dir}${enc.hook_evitar ? ' · hook_evitar ' + enc.hook_evitar : ''}`)

  // ── FASE 2: VERIFICACIÓN ──────────────────────────────────────────────────
  phase('Verificación')
  const promptV =
    `Eres el verificador del flujo /dato (lee referencias/roles/verificador.md, sección «Modo dato»). Sesión: ${enc.sesion_dir}. ` +
    `Corre python3 scripts/digesto.py ${enc.sesion_dir} --eje dato --para verificador (no leas hallazgos_dato.json entero). ` +
    `Verifica TODAS las candidatas: ${hal.cifras.map((c) => c.id).join(', ')}. Parte de la cita y del archivo local; una segunda fuente genuinamente independiente por cifra; ≤2 fetch y ≤1 búsqueda por cifra. ` +
    `En una comparación verifica los dos lados (misma definición, unidad y periodo); en una candidata «récord» verifica que el máximo de la serie sea ese valor. ${smoke ? 'MODO SMOKE: cita + una segunda fuente; extremos de cada serie. ' : ''}` +
    `Escribe ${enc.sesion_dir}/verificacion_dato.json COMPLETO con EXACTAMENTE esta forma: {"eje": "dato", "items": [{"id", "veredicto": "verificada|ajustada|no_confirmada", "valor_final", "fuente_2", "url_2", "nota"}]} (la clave es items, no cifras) y devuelve ok[] (id, valor_final) y no_confirmadas[].`
  const optsV = { agentType: 'hilo-verificador', schema: S.verificacion, label: 'verificador' }
  let ver = await agentRol(promptV, optsV)
  if (!ver) { avisar('AVISO: el verificador no terminó; se reintenta una vez.'); ver = await agentRol(promptV, { ...optsV, label: 'verificador-2' }) }
  if (!ver) fail('Verificación sin resultado: el verificador no terminó dos veces.')
  for (const it of ver.ok) { if (CIF.has(it.id)) VER.set(it.id, it); else avisar(`AVISO: el verificador devolvió ${it.id}, que no está en hallazgos_dato.json; se ignora.`) }
  noConf = (ver.no_confirmadas || []).length
  okIds = new Set(VER.keys())
  bajas = [...VER.values()].filter((it) => it.independencia === 'baja').map((it) => it.id)
  if (bajas.length) avisar(`AVISO: segunda fuente NO independiente (reproduce la primaria) en ${bajas.length} candidata(s): ${bajas.join(', ')}`)
  if (!okIds.size) fail(`Ninguna candidata quedó verificada|ajustada (${noConf} no confirmadas): no hay dato que publicar.`)
  if (okIds.size < 3) avisar(`AVISO: solo ${okIds.size} candidata(s) verificada(s); la elección será entre pocas.`)
  avisar(`Verificación: ${okIds.size} candidata(s) utilizable(s) (${noConf} descartadas): ${[...okIds].join(', ')}`)

  // ── FASE 3: GUION (elección del dato + un tuit, con reparación) ───────────
  phase('Guion')
  const numerosDe = (d) => {
    const out = []
    const rec = (x) => { if (typeof x === 'number') out.push(x); else if (Array.isArray(x)) x.forEach(rec); else if (x && typeof x === 'object') Object.entries(x).forEach(([k, v]) => { if (!['decimales', 'escala', 'destacar', 'clases', 'decimales_pildora', 'i', 'fila', 'col', 'miles', 'cortes', 'maximo', 'minimo_rotulo', 'desde', 'hasta'].includes(k)) rec(v) }) }
    rec(d); return out
  }
  const formatos = (v) => { const a = Math.abs(v); const s = new Set([String(v), String(a), a.toFixed(1), a.toFixed(2), a.toLocaleString('en-US'), a.toLocaleString('en-US', { maximumFractionDigits: 2 })]); return [...s].filter((x) => x && x !== '0') }
  const largo = (x) => (Array.isArray(x) ? x.length : 0)
  const validarGuion = (gg) => {
    const F = []
    const Tt = gg.tuits || []
    if (Tt.length !== 1) { F.push(`el guion tiene ${Tt.length} tuits: /dato produce EXACTAMENTE uno`); return F }
    const t = Tt[0], v = t.visual, tx = t.texto || '', p = pesoX(tx)
    if (t.n !== 1) F.push('el tuit debe ser n: 1')
    if (t.beat !== 'gancho') F.push('el tuit debe ser beat gancho')
    if (gg.paleta !== enc.paleta) F.push(`paleta del guion (${gg.paleta}) ≠ encuadre (${enc.paleta})`)
    if (enc.hook_evitar && gg.hook_tipo === enc.hook_evitar) F.push(`hook_tipo ${gg.hook_tipo} es el del último dato publicado (hook_evitar); elige otro`)
    // Dato elegido
    const D = gg.dato || {}
    const cid = D.cifra_id
    if (!okIds.has(cid)) F.push(`dato.cifra_id ${cid} no está verificada (verificadas: ${[...okIds].join(', ')})`)
    if (gg.ancla_id !== cid) F.push(`ancla_id (${gg.ancla_id}) debe ser dato.cifra_id (${cid})`)
    if (!(D.titular || '').trim() || D.titular.length > 90) F.push('dato.titular: una sola línea de 1–90 caracteres (el hallazgo en palabras)')
    if ((D.por_que_impacta || '').trim().length < 20) F.push('dato.por_que_impacta: ≥20 caracteres (por qué sorprende o qué escala humana tiene)')
    // Candidatas: todas las verificadas, una elegida, el resto con motivo
    const C = gg.candidatas || [], cIds = C.map((c) => c.id)
    if (new Set(cIds).size !== cIds.length) F.push('candidatas con ids repetidos')
    for (const id of okIds) if (!cIds.includes(id)) F.push(`candidatas no incluye la cifra verificada ${id} (elegida o descartada con motivo)`)
    for (const c of C) {
      if (!okIds.has(c.id)) F.push(`candidata ${c.id} no está verificada`)
      if (!c.elegida && (c.motivo || '').trim().length < 10) F.push(`candidata ${c.id} descartada sin motivo`)
    }
    const eleg = C.filter((c) => c.elegida)
    if (eleg.length !== 1 || eleg[0].id !== cid) F.push(`candidatas debe marcar elegida: true exactamente en ${cid}`)
    for (const c of C) if (bajas.includes(c.id) && c.criterios && (c.criterios.solidez || 0) > 3) F.push(`candidata ${c.id}: solidez ${c.criterios.solidez} con segunda fuente NO independiente (máximo 3)`)
    if (eleg.length === 1 && C.length > 1) { const max = Math.max(...C.map((c) => c.puntaje || 0)); if ((eleg[0].puntaje || 0) < max) avisar(`AVISO: la elegida (${eleg[0].puntaje}) no es la de mayor puntaje (${max}); motivo: ${eleg[0].motivo}`) }
    // Texto = el tuit entero
    if (!tx.trim()) F.push('el texto es obligatorio: es el tuit entero')
    if (p < 40 || p > 280) F.push(`el texto debe pesar 40–280 en X (pesa ${p})`)
    if (tx.split('\n')[0].length > 90) F.push('texto: primera línea > 90')
    if (RE_LINK.test(tx)) F.push('el texto lleva enlace o dominio')
    if (RE_BAIT.test(tx)) F.push('el texto contiene engagement bait')
    // Visual obligatorio
    if (!v) { F.push('visual obligatorio: la tarjeta es el entregable'); return F }
    if ((t.alt_text || '').trim().length < 20) F.push('alt_text < 20 caracteres')
    const fuera = v.cifra_ids.filter((c) => !okIds.has(c))
    if (fuera.length) F.push(`cifra_ids no verificadas: ${fuera.join(', ')}`)
    if (!v.cifra_ids.includes(cid)) F.push(`visual.cifra_ids no incluye dato.cifra_id ${cid}`)
    const d = v.datos || {}
    for (const k of REQ[v.plantilla] || []) if (!(k in d)) F.push(`(${v.plantilla}) falta datos.${k}`)
    const pl = v.plantilla
    if (pl === 'cifra') {
      if (!(d.cifra && typeof d.cifra.valor === 'number')) F.push('cifra: datos.cifra.valor debe ser un número crudo')
      if (!(d.cifra && String(d.cifra.texto || '').trim())) F.push('cifra: datos.cifra.texto vacío (qué es la cifra y de cuándo)')
      if ((d.contexto || '').length > 60) F.push('cifra: contexto > 60')
      if (d.comparacion && typeof d.comparacion.valor !== 'number') F.push('cifra: comparacion.valor debe ser un número crudo')
    }
    // Chequeos por plantilla (copia de hilo.js)
    if (pl === 'linea') {
      if ((d.series || []).length > 4) F.push('linea: más de 4 series')
      const cortas = v.cifra_ids.filter((c) => CIF.get(c) && CIF.get(c).tipo === 'serie' && (CIF.get(c).n_puntos || 0) < 5)
      if (cortas.length) F.push(`linea con series de <5 puntos: ${cortas.join(', ')}`)
    }
    if (pl === 'pendiente' && (!Array.isArray(d.fechas) || d.fechas.length !== 2 || (d.items || []).length < 2 || (d.items || []).length > 6)) F.push('pendiente: 2 fechas y 2–6 items')
    if (pl === 'pesas' && (!Array.isArray(d.fechas) || d.fechas.length !== 2 || (d.items || []).length < 2 || (d.items || []).length > 8)) F.push('pesas: 2 fechas y 2–8 items')
    if (pl === 'dona' && ((d.partes || []).length < 2 || (d.partes || []).length > 5)) F.push('dona: 2–5 partes')
    if (pl === 'barras-h' && (d.items || []).length > 8) F.push('barras-h: ≤8 items')
    if (pl === 'barras-v' && (!Array.isArray(d.valores) || d.valores.length > 12 || (d.etiquetas || []).length !== d.valores.length)) F.push('barras-v: ≤12 barras y etiquetas = valores')
    if (pl === 'waffle' && !(d.porcentaje > 0 && d.porcentaje <= 100)) F.push('waffle: porcentaje en (0,100]')
    if (pl === 'mapa' && Object.keys(d.valores || {}).length < 12) F.push('mapa: ≥12 departamentos con valor')
    if (pl === 'calor' && ((d.filas || []).length * (d.columnas || []).length > 144 || (d.columnas || []).length > 12)) F.push('calor: ≤12 columnas y ≤12 filas')
    if (['linea', 'barras-v'].includes(pl) && d.periodos != null) {
      const nP = largo(pl === 'linea' ? d.etiquetasX : d.etiquetas)
      const P = Array.isArray(d.periodos) ? d.periodos : null
      let prev = -1
      const malo = !P || P.length > 4 || P.some((pp) => { const ok = pp && pp.nombre && Number.isInteger(pp.desde) && Number.isInteger(pp.hasta) && pp.desde > prev && pp.desde <= pp.hasta && pp.hasta < nP; prev = pp ? pp.hasta : prev; return !ok })
      if (malo) F.push(`${pl}: periodos ≤4 con nombre y desde/hasta índices en orden, sin solaparse`)
    }
    if (pl === 'bullet' && (largo(d.items) < 1 || largo(d.items) > 6 || d.items.some((it) => typeof (it || {}).meta !== 'number' && typeof d.meta !== 'number'))) F.push('bullet: 1–6 items, cada uno con meta (propia o común)')
    if (pl === 'embudo') {
      const E = Array.isArray(d.etapas) ? d.etapas : []
      if (E.length < 2 || E.length > 6 || E.some((e, i) => i && (e || {}).valor > (E[i - 1] || {}).valor)) F.push('embudo: 2–6 etapas que no crecen')
      if (typeof d.misma_cohorte !== 'boolean') F.push('embudo: misma_cohorte debe ser true o false')
    }
    if (pl === 'divergente' && (largo(d.items) < 2 || largo(d.items) > 10)) F.push('divergente: 2–10 items')
    if (pl === 'apilada' && (largo(d.etiquetas) < 2 || largo(d.etiquetas) > 8 || largo(d.partes) < 2 || largo(d.partes) > 5 || d.partes.some((pp) => largo((pp || {}).valores) !== largo(d.etiquetas)))) F.push('apilada: 2–8 filas, 2–5 partes y un valor por fila')
    if (pl === 'piramide' && (largo(d.grupos) < 4 || largo(d.grupos) > 12 || largo((d.izquierda || {}).valores) !== largo(d.grupos) || largo((d.derecha || {}).valores) !== largo(d.grupos))) F.push('piramide: 4–12 grupos y un valor por grupo en cada lado')
    if (pl === 'treemap' && (largo(d.partes) < 3 || largo(d.partes) > 12)) F.push('treemap: 3–12 partes')
    if (pl === 'dispersion' && (largo(d.puntos) < 8 || largo(d.puntos) > 22 || largo(d.rotular) > 4)) F.push('dispersion: 8–22 puntos y ≤4 rotulados')
    if (v.titular.some((l) => !l.trim() || l.length > 26)) F.push('titular: líneas de ≤26 caracteres')
    if (!v.kicker.trim() || v.kicker.length > 45) F.push('kicker vacío o >45')
    if ((v.nota || '').length > 150) F.push('nota >150')
    if (!v.fuente.trim() || v.fuente.length > 70 || /^fuente:/i.test(v.fuente.trim())) F.push('fuente vacía, >70 o con prefijo «Fuente:»')
    if (/https?:/.test(JSON.stringify(v))) F.push('el visual contiene una URL')
    // Dato héroe: en dato las dos reglas son fallo (el texto da el «y qué», no la cifra).
    const linea = v.titular.find((l) => l.trim().length >= 8 && tx.toLowerCase().includes(l.trim().toLowerCase()))
    if (linea) F.push(`el texto repite una línea del titular: «${linea}»`)
    const repetidos = numerosDe(d).filter((num) => formatos(num).some((f) => new RegExp('(?<![\\d.,])' + f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '(?!\\d|[.,]\\d)').test(tx)))
    if (new Set(repetidos).size >= 2) F.push(`el texto repite ${new Set(repetidos).size} números de su tarjeta (dato héroe)`)
    // Récord/histórico
    if (RE_SUPER.test(tx) || RE_SUPER.test(v.titular.join(' ')) || RE_SUPER.test(D.titular || '')) {
      const largas = v.cifra_ids.filter((c) => CIF.get(c) && CIF.get(c).tipo === 'serie' && (CIF.get(c).n_puntos || 0) >= 10)
      if (!largas.length) F.push('usa «récord/histórico» sin una serie ≥10 puntos en cifra_ids')
    }
    // Superlativo relativo («el más bajo desde…»): serie o desglose ≥5 puntos; el productor lo comprueba contra la serie (C7).
    if (RE_RELATIVO.test(tx) || RE_RELATIVO.test(v.titular.join(' ')) || RE_RELATIVO.test(D.titular || '')) {
      const base = v.cifra_ids.filter((c) => CIF.get(c) && ['serie', 'desglose'].includes(CIF.get(c).tipo) && (CIF.get(c).n_puntos || 0) >= 5)
      if (!base.length) F.push('usa «más alto/bajo desde…» sin una serie o desglose ≥5 puntos en cifra_ids')
      else avisar('AVISO: superlativo relativo («más alto/bajo desde…») en el guion; el productor lo comprueba contra la serie con el año de partida inclusive (C7).')
    }
    return F
  }
  const impactos = [...okIds].map((id) => `${id} · ${(CIF.get(id) || {}).impacto || '(sin impacto declarado)'}${bajas.includes(id) ? ' (2ª fuente NO independiente: solidez ≤3)' : ''}`).join('; ')
  g = await conReparacion(
    'Guion',
    (fallos) =>
      agentRol(
        `Eres el guionista del flujo /dato (lee referencias/roles/guionista.md «Modo dato», referencias/narrativa.md «Dato único» y referencias/diseno/graficos.md). Sesión: ${enc.sesion_dir}. ` +
          `Lee encuadre.json y corre python3 scripts/digesto.py ${enc.sesion_dir} --para guionista (no leas hallazgos_dato.json ni verificacion_dato.json enteros; para los puntos de una serie usa --serie <id>). ` +
          `Paleta: ${enc.paleta}. Fecha: ${fecha}. hook_evitar: ${enc.hook_evitar || 'ninguno'}. ${smoke ? 'MODO SMOKE (smoke: true). ' : 'smoke: false. '}` +
          `CANDIDATAS VERIFICADAS (id · impacto según el investigador): ${impactos}. ` +
          `Puntúa CADA candidata de 1 a 5 en sorpresa, magnitud (escala humana), comparacion, actualidad y solidez (puntaje = suma, 5–25); elige UNA (dato.cifra_id = ancla_id) y escribe candidatas[] con todas: {id, puntaje, criterios, elegida, motivo} (las descartadas dicen por qué pierden). ` +
          `Escribe dato: {cifra_id, titular (una línea ≤90: el hallazgo en palabras), por_que_impacta}. ` +
          `Escribe EXACTAMENTE UN tuit {n: 1, beat: "gancho", texto, alt_text, visual}: plantilla cifra por defecto (antes-despues, waffle, dona, bullet, mapa, linea si el dato lo pide); visual.titular es el hallazgo, el pie lleva la fuente. ` +
          LIMITES + ' ' +
          (fallos.length ? `TU GUION ANTERIOR FUE RECHAZADO; corrige SOLO esto y vuelve a escribir guion.json completo:\n - ${fallos.join('\n - ')}\n` : '') +
          `Escribe ${enc.sesion_dir}/guion.json COMPLETO {slug, fecha, tipo: "dato", paleta, smoke, handle, hook_tipo, dato, candidatas, sintesis{pregunta, tesis, ancla_id, no_afirma, incertidumbre, descartadas}, tuits} y devuelve el mismo contenido compacto (archivo, tipo, tesis, ancla_id, paleta, hook_tipo, dato, candidatas, no_afirma, tuits con visual.datos en números crudos).`,
        { agentType: 'hilo-guionista', schema: S.guion_dato, label: fallos.length ? 'guionista-reparacion' : 'guionista' }
      ),
    validarGuion,
    2
  )
  const vf = VER.get(g.dato.cifra_id)
  avisar(`Dato: ${g.dato.titular} · ${g.dato.cifra_id} = ${vf ? vf.valor_final : '?'} · gancho ${g.hook_tipo} · ${g.tuits[0].visual.plantilla} · texto ${pesoX(g.tuits[0].texto)} de peso X`)
}

// ── FASE 4: PRODUCCIÓN (QA visual + ensamblado + coherencia, una reparación) ─
phase('Producción')
const reRuta = smoke ? /\/salida\/?$/ : new RegExp(`(^|/)datos/${fecha}-`)
const validarProd = (p) => {
  const F = []
  if (!p.ruta) F.push('ruta vacía')
  if (/^\//.test(p.ruta || '')) F.push(`la ruta debe ser RELATIVA a la raíz del repo (llegó absoluta: ${p.ruta})`)
  if (!reRuta.test(p.ruta || '')) F.push(smoke ? `en smoke/fixture la salida debe estar en ${enc.sesion_dir}/salida/ (ruta: ${p.ruta})` : `la ruta debe ser datos/${fecha}-<slug>/ (ruta: ${p.ruta})`)
  if (smoke && !['smoke', 'fixture'].includes(p.registro_id)) F.push('en smoke/fixture registro_id debe ser "smoke" o "fixture"')
  if (p.n_png !== 1) F.push(`n_png ${p.n_png}: /dato entrega exactamente 1 PNG (dato.png)`)
  if (p.gates.mecanico !== 'ok') F.push(`gate mecánico: ${p.gates.mecanico}`)
  if (!['ok', 'incompleto'].includes(p.gates.coherencia)) F.push(`gate coherencia: ${p.gates.coherencia}`)
  if (p.gates.validate !== 'ok') F.push(`make validate: ${p.gates.validate}`)
  if (p.gates.coherencia === 'incompleto' && p.estado !== 'incompleto') F.push('coherencia incompleta exige estado incompleto')
  if (fixture && !(p.resumen && p.resumen.titular && p.resumen.texto)) F.push('en fixture devuelve resumen{titular, cifra_id, hook_tipo, plantilla, paleta, texto, alt_text} copiado de guion.json')
  if (p.iteraciones_visual > maxIter) avisar(`AVISO: el productor hizo ${p.iteraciones_visual} iteraciones de QA visual (máximo ${maxIter}).`)
  return F
}
const prod = await conReparacion(
  'Producción',
  (fallos) =>
    agentRol(
      `Eres el productor del flujo /dato (lee referencias/roles/productor.md «Modo dato», referencias/roles/visualista.md y la «Checklist de QA visual» de referencias/diseno/graficos.md). Sesión: ${enc.sesion_dir}. Fecha: ${fecha}. ` +
        (fixture
          ? `MODO FIXTURE: primero mkdir -p ${enc.sesion_dir} && cp -R sesiones/_fixture_dato/. ${enc.sesion_dir}/ (con el punto final: así no anida si ya existe); en encuadre.json y guion.json copiados pon fixture: true, smoke: true, fecha "${fecha}" y sesion_dir "${enc.sesion_dir}". `
          : `Gancho: ${g.hook_tipo}. Dato elegido: ${g.dato.cifra_id} (${g.dato.titular}). ${smoke ? 'MODO SMOKE. ' : ''}` +
            (bajas.includes(g.dato.cifra_id) ? 'La cifra elegida tiene segunda fuente NO independiente (reproduce la primaria): comprueba que sintesis.incertidumbre lo declare; si no, añádelo en guion.json y re-ensambla. ' : '')) +
        `Ejecuta: (1) QA VISUAL tú mismo (no hay visualistas): python3 scripts/materializar.py ${enc.sesion_dir} --tuit 1 (exit 0 = pasa R1–R6), UN Read de ${enc.sesion_dir}/visuales/tuit_1.png por iteración, checklist; correcciones SOLO en ${enc.sesion_dir}/visuales/tuit_1.ajuste.json y re-materializar; máximo ${maxIter} iteración(es); si queda dudoso, dudoso: true con nota en avisos. ` +
        `(2) python3 scripts/materializar.py ${enc.sesion_dir} --consolidar. (3) python3 scripts/ensamblar.py ${enc.sesion_dir} --check (modo dato automático por guion.tipo; si falla, corrige guion.json, re-materializa y repite; máx. 3 vueltas). ` +
        `(4) GATE DE COHERENCIA REDUCIDO sobre post.md (python3 scripts/digesto.py ${enc.sesion_dir} --para productor + sed -n) y el último PNG que leíste (sin Read adicional): C1 TESIS = el dato (titular de la tarjeta, dato.titular y texto cuentan lo mismo, misma dirección y periodo); C5 CAUSALIDAD (todo «por», «debido a», «impulsado por» tiene fuente o se degrada a «coincide con»); C7 ARITMÉTICA (recalcula contexto, comparacion, variaciones y per cápita del texto y de la tarjeta a partir de los valores crudos: 102 frente a 67 es +52%, no +54%); ALT: el alt_text describe lo que el PNG muestra (tipo, cifra con unidad y periodo, fuente). Cada corrección pasa por guion.json → materializar → ensamblar. ` +
        `(5) python3 scripts/ensamblar.py ${enc.sesion_dir} --solo-estado --estado listo|incompleto (si C1, C5, C7, INDEP o ALT siguen fallando en la tercera vuelta: coherencia "incompleto" y estado "incompleto"). ` +
        (smoke
          ? `(6) MODO ${fixture ? 'FIXTURE' : 'SMOKE'}: la salida queda en ${enc.sesion_dir}/salida/, NO toques memoria/, registro_id = "${fixture ? 'fixture' : 'smoke'}". `
          : `(6) python3 scripts/memoria.py --registrar ${enc.sesion_dir} --ruta <ruta relativa> --estado listo|incompleto (detecta guion.tipo = "dato" y escribe memoria/datos.json; series y fuentes primarias van a memoria/fuentes.json; no toca ideas/). `) +
        `(7) make validate (exit 0). ` + LIMITES +
        ` Devuelve ruta RELATIVA a la raíz (datos/${fecha}-<slug>/ o <sesion>/salida/), n_png (1), iteraciones_visual, dudoso, plantilla_final, estado, registro_id y los gates EXACTAMENTE como "ok" | "falla" | "incompleto" (los detalles van en avisos)` +
        (fixture ? ', y resumen{titular, cifra_id, hook_tipo, plantilla, paleta, texto, alt_text} copiado de guion.json (dato.titular, dato.cifra_id, hook_tipo, tuits[0].visual.plantilla, paleta, tuits[0].texto, tuits[0].alt_text).' : '.') +
        (fallos.length ? `\nTU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}` : ''),
      { agentType: 'hilo-productor', schema: S.produccion_dato, label: fallos.length ? 'productor-reparacion' : 'productor' }
    ),
  validarProd,
  1
)
if (prod.estado === 'incompleto') avisar(`AVISO: el dato queda INCOMPLETO (coherencia ${prod.gates.coherencia}); revisa post.md antes de publicar.`)
if (prod.dudoso) avisar('AVISO: el productor marcó la tarjeta como dudosa; mira dato.png antes de publicar.')

const R = g
  ? { titular: g.dato.titular, cifra_id: g.dato.cifra_id, hook_tipo: g.hook_tipo, plantilla: g.tuits[0].visual.plantilla, paleta: g.paleta, texto: g.tuits[0].texto, alt_text: g.tuits[0].alt_text }
  : (prod.resumen || {})
const valorFinal = g && VER.get(g.dato.cifra_id) ? VER.get(g.dato.cifra_id).valor_final : null
return {
  dato: R.titular || null,
  cifra_id: R.cifra_id || null,
  valor: valorFinal === undefined ? null : valorFinal,
  por_que_impacta: g ? g.dato.por_que_impacta : null,
  hook_tipo: R.hook_tipo || null,
  paleta: R.paleta || null,
  plantilla: prod.plantilla_final || R.plantilla || null,
  estado: prod.estado,
  ruta: prod.ruta,
  texto: R.texto || null,
  peso_texto: R.texto ? pesoX(R.texto) : null,
  alt_text: R.alt_text || null,
  candidatas: g ? g.candidatas : [],
  candidatas_verificadas: okIds ? okIds.size : null,
  candidatas_descartadas_por_verificacion: noConf,
  independencia_baja: bajas,
  no_afirma: g ? g.no_afirma : [],
  avisos_workflow: AVISOS_WF,
  iteraciones_visual: prod.iteraciones_visual,
  dudoso: !!prod.dudoso,
  avisos: prod.avisos || [],
  sesion_dir: enc.sesion_dir,
  pista,
  pista_usuario: pistaUsuario,
  tema: enc.tema || null,
  smoke,
  fixture,
}
