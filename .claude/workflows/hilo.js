export const meta = {
  name: 'hilo',
  description: 'Hilo de X con datos de Guatemala: encuadre → investigación ⇢ verificación por eje → guion → visuales → ensamblado',
  whenToUse: 'Invocado por /hilo [modo] [tema] [smoke|fixture] (y por los alias /explica y /perfil). args: {tema, modo, smoke, fixture, fecha, min_tuits, idea, permitir_fallback} (fecha YYYY-MM-DD obligatoria, la pone el comando con `date +%F`). modo = hilo (defecto, historia con giro) | explica (el tema explicado con sus números en 3–6 tarjetas, sin giro) | perfil (retrato de un departamento o grupo frente al país en 5–8 tarjetas; tema = el sujeto). smoke = corrida corta sin tocar memoria/; fixture = sin web, copia sesiones/_fixture. idea = id de ideas/banco.json (el editor parte de ella; memoria.py la marca hecha al registrar).',
  phases: [
    { title: 'Encuadre', detail: 'editor: pregunta, tesis provisional, paleta, ejes con prefijo y fuentes sugeridas' },
    { title: 'Investigación', detail: 'un investigador por eje (SIFT, con presupuesto): cifras con evidencia' },
    { title: 'Verificación', detail: 'un verificador por eje: parte de la evidencia, una segunda fuente, veredicto' },
    { title: 'Guion', detail: 'guionista: tesis final + 4–21 tuits (min_tuits opcional) con gancho (hook_tipo), visual y alt-text' },
    { title: 'Visuales', detail: 'visualistas en lotes de 3: materializar → gate R1–R6 → QA' },
    { title: 'Ensamblado', detail: 'productor: consolidar → ensamblar.py --check → C1–C8 → memoria.py → make validate' },
  ],
}

// Guías: referencias/contrato-sesion.md, referencias/roles/*.md, referencias/narrativa.md.
// Los agentes escriben su artefacto COMPLETO en sesiones/<slug>/ y devuelven aquí
// un resumen validado por schema; los gates se aplican sobre los retornos (el
// sandbox del workflow no lee disco ni tiene Date).

const PALETAS = ['cielo', 'jade', 'maiz', 'terracota', 'cacao', 'jacaranda', 'atitlan', 'obsidiana']
const PLANTILLAS = ['linea', 'barras-v', 'barras-h', 'antes-despues', 'dona', 'pendiente', 'waffle', 'cifra', 'mapa', 'pesas', 'calor', 'bullet', 'embudo', 'divergente', 'apilada', 'piramide', 'treemap', 'dispersion']
const BEATS = ['gancho', 'contexto', 'giro', 'impacto', 'cierre', 'paso', 'dimension'] // paso: modo explica · dimension: modo perfil
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
const LOTE = 3
const MAX_TUITS = 21
const TOPES = { normal: { busquedas: 10, fetch: 12, cifras: 12 }, smoke: { busquedas: 5, fetch: 6, cifras: 6 } }
// Modos de /hilo (args.modo): cambian el arco y los gates; guion.tipo sigue siendo "hilo".
// Las claves coinciden con ensamblar.MODOS["hilo"] (lo comprueba scripts/check_workflows.py). min null = min_tuits.
const MODOS = {
  hilo:    { beatMedio: null,        min: null, max: MAX_TUITS, giro: 1, impacto: true,  minCifras: 6 },
  explica: { beatMedio: 'paso',      min: 3,    max: 6,         giro: 0, impacto: false, minCifras: 3 },
  perfil:  { beatMedio: 'dimension', min: 5,    max: 8,         giro: 0, impacto: false, minCifras: 5 },
}
const RE_PAIS = /guatemala|nacional|pa[ií]s/i
const TEMA_SMOKE = { hilo: 'remesas familiares 2025', explica: 'cómo se calcula la tarifa de electricidad en Guatemala', perfil: 'Alta Verapaz' }
// Instrucciones por modo que viajan en los prompts (el detalle vive en referencias/roles/*.md «Modo explica» y «Modo perfil»).
const INSTR = {
  hilo: { editor: '', investigador: '', guionista: '', productor: '' },
  explica: {
    editor: 'MODO EXPLICA (el tema explicado con sus números): no hay tesis que probar; la pregunta es «¿cómo funciona / cómo se calcula / a dónde va X?»; tesis_provisional = "Explicador: <pregunta>"; 2–3 ejes = bloques de pasos del mecanismo, cada paso con una cifra oficial que lo cuantifique (componentes, tasas, montos, totales); sin pregunta de escala humana obligatoria. ',
    investigador: 'MODO EXPLICA: cada cifra cuantifica un paso del mecanismo (componentes, tasas, montos); captura desgloses (partes[]) que sumen al total y la cifra del total. ',
    guionista: 'MODO EXPLICA: escribe modo: "explica" y el bloque explica {pregunta, pasos[]{n, titulo ≤40}} con un paso por tuit intermedio (T2..T(n−1)); los tuits intermedios llevan beat "paso" y NO hay giro ni impacto (esto manda sobre «un solo giro» de los límites); cada paso es una tarjeta con la cifra del paso y un texto que lo explica en lenguaje llano (≤200 con imagen; nunca vacío); T1 gancho plantea la pregunta (pregunta_directa o curiosity_gap: T2 empieza a pagarla); el cierre resume («en resumen…») y nombra las fuentes. Cero adjetivos valorativos. ',
    productor: 'MODO EXPLICA: C1 = los pasos encadenan en orden y el total (si lo hay) cuadra con las partes (C7); C2 = quitar un paso rompe la explicación; sin lenguaje valorativo. ',
  },
  perfil: {
    editor: 'MODO PERFIL (retrato de un departamento o grupo frente al país): el tema es el SUJETO; sin tesis que probar (tesis_provisional = "Perfil: <sujeto> en N datos"); elige 5–6 dimensiones estándar (población y crecimiento, pobreza o ingreso, salud o desnutrición, educación, seguridad o migración, economía local) repartidas en 2–3 ejes; cada dimensión necesita el valor del sujeto Y el nacional de la misma fuente y año (per cápita con proyecciones INE); anota en cada brief el año de cada dimensión. ',
    investigador: 'MODO PERFIL: para cada dimensión captura el valor del sujeto Y el nacional de la MISMA fuente y año (como desglose con partes [sujeto, nacional] o como dos cifras) y, si hace falta, la población INE del sujeto y del país para la tasa. ',
    guionista: 'MODO PERFIL: escribe modo: "perfil" y el bloque perfil {sujeto, tipo: departamento|grupo, dimensiones[]{n, nombre, anio}} con una dimensión por tuit intermedio; los tuits intermedios llevan beat "dimension" y NO hay giro ni impacto (esto manda sobre «un solo giro» de los límites); cada tarjeta intermedia compara sujeto y país (un item o serie rotulado «Guatemala», «nacional» o «país», la comparacion de cifra, o un mapa con el sujeto destacado); el sujeto aparece en el kicker o el titular de T1; el cierre dice qué hace distinto al sujeto, nombra los años si difieren y las fuentes. ',
    productor: 'MODO PERFIL: C1 = cada tarjeta intermedia compara sujeto y país en la misma unidad y el rótulo lo dice; C7 recalcula per cápita con el denominador declarado; los años de las dimensiones aparecen en el cierre si difieren. ',
  },
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

const S = {
  encuadre: {
    type: 'object',
    required: ['slug', 'tema', 'pregunta', 'tesis_provisional', 'paleta', 'ejes', 'sesion_dir', 'fecha', 'smoke'],
    properties: {
      slug: { type: 'string' }, tema: { type: 'string' }, pregunta: { type: 'string' },
      tesis_provisional: { type: 'string' }, angulo: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS },
      necesita_serie: { type: 'boolean' }, repetido: { type: 'boolean' },
      hook_evitar: { type: ['string', 'null'] },
      idea_id: { type: ['string', 'null'] },
      modo: { type: 'string', enum: Object.keys(MODOS) },
      ejes: {
        type: 'array', minItems: 1, maxItems: 4,
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
      sesion_dir: { type: 'string' }, fecha: { type: 'string' }, smoke: { type: 'boolean' }, fixture: { type: 'boolean' },
    },
  },
  hallazgos: {
    type: 'object',
    required: ['eje', 'archivo', 'n_busquedas', 'cifras'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string' }, n_busquedas: { type: 'number' }, n_fetch: { type: 'number' },
      cifras: {
        type: 'array', maxItems: 12,
        items: {
          type: 'object', required: ['id', 'tipo'],
          properties: {
            id: { type: 'string' }, tipo: { type: 'string', enum: ['puntual', 'serie', 'desglose'] },
            n_puntos: { type: 'integer' }, candidata_ancla: { type: 'boolean' },
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
      eje: { type: 'string' }, archivo: { type: 'string' },
      ok: { type: 'array', items: { type: 'object', required: ['id'], properties: { id: { type: 'string' }, valor_final: { type: 'number' }, independencia: { type: 'string', enum: ['alta', 'baja'] } } } },
      no_confirmadas: { type: 'array', items: { type: 'string' } },
    },
  },
  guion: {
    type: 'object',
    required: ['archivo', 'tesis', 'ancla_id', 'paleta', 'hook_tipo', 'no_afirma', 'tuits'],
    properties: {
      archivo: { type: 'string' }, tesis: { type: 'string' }, ancla_id: { type: 'string' },
      paleta: { type: 'string', enum: PALETAS }, hook_tipo: { type: 'string', enum: HOOKS },
      no_afirma: { type: 'array', items: { type: 'string' } },
      modo: { type: 'string', enum: Object.keys(MODOS) },
      // Bloques por modo (el workflow exige el del modo pedido).
      explica: {
        type: 'object', required: ['pregunta', 'pasos'],
        properties: { pregunta: { type: 'string' }, pasos: { type: 'array', items: { type: 'object', required: ['n', 'titulo'], properties: { n: { type: 'integer' }, titulo: { type: 'string' } } } } },
      },
      perfil: {
        type: 'object', required: ['sujeto', 'tipo', 'dimensiones'],
        properties: { sujeto: { type: 'string' }, tipo: { type: 'string', enum: ['departamento', 'grupo'] }, dimensiones: { type: 'array', items: { type: 'object', required: ['n', 'nombre', 'anio'], properties: { n: { type: 'integer' }, nombre: { type: 'string' }, anio: { type: 'integer' } } } } },
      },
      tuits: {
        type: 'array', minItems: 3, maxItems: MAX_TUITS,
        items: {
          type: 'object', required: ['n', 'beat', 'texto', 'alt_text', 'visual'],
          properties: {
            n: { type: 'integer' }, beat: { type: 'string', enum: BEATS },
            texto: { type: 'string', maxLength: 400 }, alt_text: { type: 'string', maxLength: 1000 },
            visual: {
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
            },
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
            // rutas con el nombre exacto del archivo: un retorno mal escrito (tuit_2.html como PNG) no debe costar una reparación
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
}

// Resumen de límites que viaja en los prompts: así nadie lee hilo.js ni ensamblar.py.
const LIMITES =
  'LÍMITES (los comprueba el workflow y ensamblar.py --check): tuits numerados 1..n; T1 gancho, último cierre, un solo giro; ' +
  'T1 con texto de 40–280 de peso X (URL=23, emoji=2), primera línea ≤90, sin enlaces; T2..T(n−1) con visual obligatorio y texto "" o ≤200; ' +
  'el texto no repite el titular de su tarjeta ni ≥2 de sus números; sin engagement bait; alt_text 20–1000 por visual; ' +
  `plantilla ∈ ${PLANTILLAS.join('|')}; kicker ≤45; titular 1–3 líneas de ≤26; nota ≤150; fuente 1–70 sin «Fuente:»; sin URLs en la tarjeta; ` +
  'cifra_ids ⊆ verificadas; datos con números crudos de esas cifras y formato; linea ≥5 puntos y ≤4 series; dona 2–5; barras-h ≤8; barras-v ≤12; ' +
  'pendiente 2 fechas y 2–6; mapa ≥12 departamentos; pesas 2–8; calor filas×columnas ≤12; bullet 1–6 con meta; embudo 2–6 etapas no crecientes y misma_cohorte true|false; divergente 2–10; apilada 2–8 filas y 2–5 partes; piramide 4–12 grupos; treemap 3–12; dispersion 8–22 puntos con ejeX/ejeY; periodos (linea, barras-v) ≤4 por índices; «récord/histórico» solo con serie ≥10 puntos cuyo máximo sea el valor.'

// ── Argumentos ─────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { tema: args } : (args || {})
const temaBruto = String(A.tema || '')
const fixture = !!A.fixture || /\bfixture\b/i.test(temaBruto)
const smoke = fixture || !!A.smoke || /\bsmoke\b/i.test(temaBruto)
const tema = temaBruto.replace(/\b(smoke|fixture)\b/gi, '').trim()
const fecha = String(A.fecha || '')
if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) throw new Error('args.fecha (YYYY-MM-DD) es obligatoria: /hilo la obtiene con `date +%F` y la pasa en args.')
const modo = smoke ? 'smoke' : 'normal'
// Mínimo de tuits en modo normal (4 por defecto; el usuario puede pedir un hilo largo).
const minT = Math.min(MAX_TUITS, Math.max(4, parseInt(A.min_tuits, 10) || 4))
// Modo del post (hilo | explica | perfil): lo fija el comando; desconocido = error, no silencio.
const modoPost = A.modo ? String(A.modo).toLowerCase() : 'hilo'
if (!MODOS[modoPost]) throw new Error(`args.modo "${A.modo}" desconocido (${Object.keys(MODOS).join('|')}).`)
const MP = MODOS[modoPost]
const IM = INSTR[modoPost]
const minN = smoke ? 3 : (MP.min || minT)
const maxN = smoke ? 4 : MP.max
const T = TOPES[modo]
// Idea del banco (ideas/banco.json): la resuelve /hilo en el preflight y llega como id.
const idea = /^[a-z0-9-]+$/.test(String(A.idea || '')) ? String(A.idea) : null
const fail = (msg) => { throw new Error(msg) }
// Los avisos del workflow viajan también en el retorno (el journal no conserva los log()).
const AVISOS_WF = []
const avisar = (m) => { AVISOS_WF.push(String(m)); log(m) }

// Los roles viven en .claude/agents/hilo-*.md y se registran al arrancar la
// sesión. Si no existen todavía se falla con instrucciones claras: correr todo
// en general-purpose es caro, ignora los modelos por rol y rompe la caché de
// resume. Solo con args.permitir_fallback se degrada a general-purpose.
const agentRol = async (prompt, opts) => {
  try {
    return await agent(prompt, opts)
  } catch (e) {
    if (!opts || !opts.agentType || !/agent type .* not found/i.test(String(e && e.message))) throw e
    if (!A.permitir_fallback) fail(`El agente ${opts.agentType} no está registrado en esta sesión (los .claude/agents/ se cargan al arrancar). Reinicia Claude Code y vuelve a lanzar /hilo, o pasa args.permitir_fallback: true para correr con general-purpose.`)
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

// ── FASE 1: ENCUADRE ────────────────────────────────────────────────────────
phase('Encuadre')
const enc = await agentRol(
  fixture
    ? `Eres el editor del flujo /hilo (lee referencias/roles/editor.md, «Modo fixture»). MODO FIXTURE: copia sesiones/_fixture a sesiones/fixture-${fecha.replace(/-/g, '')} con cp -R, ` +
      `edita el encuadre.json copiado poniendo fixture:true, smoke:true, fecha "${fecha}", sesion_dir "sesiones/fixture-${fecha.replace(/-/g, '')}", y devuélvelo tal cual.`
    : `Eres el editor del flujo /hilo (lee referencias/roles/editor.md y referencias/contrato-sesion.md). ` +
      `${modoPost === 'perfil' ? 'Sujeto del perfil' : 'Tema'}: ${tema ? `"${tema}"` : (modoPost === 'hilo' ? '(no dado: elige uno de actualidad con datos duros)' : `(no dado: usa «${TEMA_SMOKE[modoPost]}»)`)}. Fecha: ${fecha}. ` +
      `MODO DEL POST: ${modoPost}. ` + IM.editor +
      (idea ? `IDEA DEL BANCO: corre python3 scripts/ideas.py --ver ${idea} (no abras ideas/banco.json) y parte de su pregunta, ángulo, hook_sugerido, paleta_sugerida y datos (fuentes con evidencia de acceso); pon idea_id: "${idea}" en encuadre.json y en tu retorno. ` : 'idea_id: null. ') +
      `${smoke ? `MODO SMOKE: exactamente 1 eje, smoke:true; sin tema usa «${TEMA_SMOKE[modoPost]}». ` : `Modo normal: ${minT >= 10 ? '3–4 ejes (hilo largo: ≥' + minT + ' tuits, hacen falta series comparables para muchas tarjetas)' : '2–4 ejes'}, smoke:false${MP.impacto ? '; un eje incluye la pregunta de escala humana (beat impacto)' : ''}. `}` +
      `Usa python3 scripts/fuentes.py --tema "…" --series para las fuentes_sugeridas de cada eje (no abras memoria/fuentes.json). Cada eje lleva un prefijo de 3 letras único. ` +
      `Lee memoria/hilos.json solo para repetido y hook_evitar. Crea sesiones/<slug>/ y escribe encuadre.json completo con fecha "${fecha}" y modo: "${modoPost}" (devuélvelo también).`,
  { agentType: 'hilo-editor', schema: S.encuadre, label: 'editor' }
)
if (!enc) fail('Encuadre sin resultado: el editor no terminó.')
if (!enc.sesion_dir || !enc.ejes || !enc.ejes.length) fail('Encuadre incompleto: hacen falta sesion_dir y ejes.')
if (!fixture && smoke && enc.ejes.length !== 1) fail(`Smoke exige exactamente 1 eje (hay ${enc.ejes.length}).`)
if (!fixture && !smoke && enc.ejes.length < 2) fail('Modo normal exige ≥2 ejes.')
const prefijoDe = (e) => String(e.prefijo || e.id.slice(0, 3)).toLowerCase()
{
  const pref = enc.ejes.map(prefijoDe)
  if (new Set(pref).size !== pref.length) fail(`Prefijos de eje repetidos (${pref.join(', ')}): cada eje necesita un prefijo de 3 letras único.`)
}
if (idea && enc.idea_id !== idea) { avisar(`AVISO: el editor no devolvió idea_id "${idea}"; memoria.py no podrá marcar la idea (corrígelo en encuadre.json antes del registro).`) }
if (!fixture && enc.modo && enc.modo !== modoPost) avisar(`AVISO: el editor devolvió modo ${enc.modo}; la directiva pedía ${modoPost} (encuadre.json debe decir modo: "${modoPost}").`)
if (fixture && modoPost !== 'hilo') avisar(`AVISO: el fixture es un hilo con giro; el modo ${modoPost} solo se ejercita en smoke o normal.`)
if (enc.repetido) avisar('AVISO: tema ya cubierto en memoria/hilos.json; el editor declara ángulo nuevo en encuadre.json.')
avisar(`Pregunta: ${enc.pregunta}${modoPost !== 'hilo' ? ' · modo ' + modoPost : ''} · paleta ${enc.paleta} · ${enc.ejes.length} eje(s) · sesión ${enc.sesion_dir}${idea ? ' · idea ' + idea : ''}${fixture ? ' · FIXTURE' : ''}`)

// ── FASE 2: INVESTIGACIÓN ⇢ VERIFICACIÓN (pipeline por eje, sin barrera) ────
const CIF = new Map()
const VER = new Map()
let okIds = null // null = fixture (los gates de ids los aplica ensamblar.py sobre el disco)
let noConf = 0
let bajas = [] // cifras cuya segunda fuente reproduce la primaria (independencia baja)
const ejesCaidos = []
if (!fixture) {
  const investigar = (eje) =>
    agentRol(
      `Eres el investigador del eje "${eje.id}" (lee referencias/roles/investigador.md y referencias/contrato-sesion.md). Sesión: ${enc.sesion_dir} ` +
        `(lee encuadre.json: tu brief, preguntas y fuentes_sugeridas). Prefijo de ids: "${prefijoDe(eje)}-cNN". ` + IM.investigador +
        `PRESUPUESTO: ≤${T.busquedas} búsquedas, ≤${T.fetch} fetch, ≤${T.cifras} cifras, ≤${smoke ? 2 : 4} series; cada cifra con evidencia {url, cita, archivo_local}. ` +
        `Sin Playwright MCP. Escribe ${enc.sesion_dir}/hallazgos_${eje.id}.json completo y devuelve solo el resumen (ids, tipo, n_puntos).`,
      { agentType: 'hilo-investigador', schema: S.hallazgos, phase: 'Investigación', label: `investigar-${eje.id}` }
    )
  const verificar = async (h, eje) => {
    if (!h) { ejesCaidos.push(eje.id); return null }
    if (h.n_busquedas > T.busquedas || (h.n_fetch || 0) > T.fetch || h.cifras.length > T.cifras) avisar(`AVISO: ${eje.id} excedió el presupuesto (${h.n_busquedas} búsquedas, ${h.n_fetch || '?'} fetch, ${h.cifras.length} cifras).`)
    const prompt =
      `Eres el verificador del eje "${eje.id}" (lee referencias/roles/verificador.md). Sesión: ${enc.sesion_dir}. ` +
      `Corre python3 scripts/digesto.py ${enc.sesion_dir} --eje ${eje.id} --para verificador (no leas ${h.archivo} entero). ` +
      `Verifica TODAS: ${h.cifras.map((c) => c.id).join(', ')}. Parte de la cita y del archivo local; una segunda fuente independiente por cifra; ≤2 fetch por cifra. ` +
      `${smoke ? 'MODO SMOKE: cita + una segunda fuente; extremos de cada serie. ' : ''}` +
      `Escribe ${enc.sesion_dir}/verificacion_${eje.id}.json completo con EXACTAMENTE esta forma: {"eje": "${eje.id}", "items": [{"id", "veredicto": "verificada|ajustada|no_confirmada", "valor_final", "fuente_2", "url_2", "nota"}]} (la clave es items, no cifras) y devuelve ok[] (id, valor_final) y no_confirmadas[].`
    const opts = { agentType: 'hilo-verificador', schema: S.verificacion, phase: 'Verificación', label: `verificar-${eje.id}` }
    let v = await agentRol(prompt, opts)
    if (!v) { avisar(`AVISO: el verificador de ${eje.id} no terminó; se reintenta una vez.`); v = await agentRol(prompt, { ...opts, label: `verificar-${eje.id}-2` }) }
    if (!v) { ejesCaidos.push(eje.id); return null }
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
  if (okIds.size < (smoke ? 3 : MP.minCifras)) fail(`Solo ${okIds.size} cifras verificadas/ajustadas: no hay material para el ${modoPost} (mínimo ${smoke ? 3 : MP.minCifras}).`)
  const seriesOk = [...okIds].filter((id) => CIF.get(id) && CIF.get(id).tipo === 'serie' && (CIF.get(id).n_puntos || 0) >= 5)
  if (enc.necesita_serie && !seriesOk.length) {
    if (smoke) avisar('AVISO smoke: el encuadre pedía una serie y no hay ninguna verificada con ≥5 puntos.')
    else fail('El encuadre pedía evolución en el tiempo y no hay ninguna serie verificada con ≥5 puntos.')
  }
  const total = okIds.size + noConf
  if (total && noConf / total >= 0.5) avisar(`AVISO: ${noConf} de ${total} cifras no se confirmaron (calidad de fuentes baja).`)
  avisar(`Verificación: ${okIds.size} cifras utilizables (${noConf} descartadas) · ${seriesOk.length} series con ≥5 puntos`)
}

// ── FASE 3: GUION (síntesis + tuits, con reparación) ────────────────────────
phase('Guion')
const validarGuion = (g) => {
  const Tt = g.tuits, n = Tt.length
  const F = []
  if (n < minN || n > maxN) F.push(`el ${modoPost} tiene ${n} tuits (${smoke ? '3–4 en smoke' : `${minN}–${maxN}`}${modoPost !== 'hilo' ? ' en modo ' + modoPost : ''})`)
  if (Tt.some((t, i) => t.n !== i + 1)) F.push('los tuits no están numerados 1..n')
  if (g.paleta !== enc.paleta) F.push(`paleta del guion (${g.paleta}) ≠ encuadre (${enc.paleta})`)
  if (Tt[0].beat !== 'gancho') F.push('T1 debe ser gancho')
  if (Tt[n - 1].beat !== 'cierre') F.push(`T${n} debe ser cierre`)
  const giros = Tt.filter((t) => t.beat === 'giro').length
  if (giros !== MP.giro) F.push(MP.giro ? 'debe haber exactamente un giro' : `modo ${modoPost}: no lleva giro (hay ${giros})`)
  if (MP.impacto && !smoke && n >= 5 && !Tt.some((t) => t.beat === 'impacto')) F.push('en modo normal con ≥5 tuits debe haber un beat impacto (escala humana)')
  if (MP.impacto && !smoke && n === 4 && !Tt.some((t) => t.beat === 'impacto')) avisar('AVISO: hilo de 4 tuits sin beat impacto.')
  if (MP.beatMedio) {
    const malos = Tt.slice(1, n - 1).filter((t) => t.beat !== MP.beatMedio).map((t) => `T${t.n} (${t.beat})`)
    if (malos.length) F.push(`modo ${modoPost}: los tuits intermedios deben ser beat ${MP.beatMedio}: ${malos.join(', ')}`)
  }
  const modoG = g.modo || 'hilo'
  if (modoG !== modoPost) F.push(`modo del guion (${modoG}) ≠ modo pedido (${modoPost}): escribe modo: "${modoPost}" en guion.json`)
  const medios = Tt.slice(1, n - 1)
  const esperados = medios.map((t) => t.n)
  if (modoPost === 'explica') {
    const X = g.explica
    if (!X) F.push('modo explica: falta el bloque explica {pregunta, pasos[]{n, titulo}}')
    else {
      if (!String(X.pregunta || '').trim()) F.push('modo explica: pregunta vacía')
      const P = Array.isArray(X.pasos) ? X.pasos : []
      if (JSON.stringify(P.map((q) => q && q.n)) !== JSON.stringify(esperados)) F.push(`modo explica: pasos[].n debe ser exactamente ${esperados.map((k) => 'T' + k).join(', ')} (llegó ${P.map((q) => q && q.n).join(', ') || 'nada'})`)
      for (const q of P) if (!String((q || {}).titulo || '').trim() || String(q.titulo).length > 40) F.push(`modo explica: paso ${q && q.n}: titulo de 1–40 caracteres`)
      for (const t of medios) if (!String(t.texto || '').trim()) F.push(`modo explica: T${t.n} sin texto (la explicación del paso va en el texto)`)
    }
  }
  if (modoPost === 'perfil') {
    const Pf = g.perfil
    if (!Pf) F.push('modo perfil: falta el bloque perfil {sujeto, tipo, dimensiones[]{n, nombre, anio}}')
    else {
      const suj = String(Pf.sujeto || '').trim()
      if (!suj) F.push('modo perfil: sujeto vacío')
      if (!['departamento', 'grupo'].includes(Pf.tipo)) F.push('modo perfil: tipo debe ser departamento|grupo')
      const v1 = Tt[0].visual
      const cab = [(v1 && v1.kicker) || '', ...((v1 && v1.titular) || []), Tt[0].texto || ''].join(' ').toLowerCase()
      if (suj && !cab.includes(suj.toLowerCase())) F.push(`modo perfil: el sujeto «${suj}» debe aparecer en el kicker, el titular o el texto de T1`)
      const Dm = Array.isArray(Pf.dimensiones) ? Pf.dimensiones : []
      if (JSON.stringify(Dm.map((q) => q && q.n)) !== JSON.stringify(esperados)) F.push(`modo perfil: dimensiones[].n debe ser exactamente ${esperados.map((k) => 'T' + k).join(', ')} (llegó ${Dm.map((q) => q && q.n).join(', ') || 'nada'})`)
      for (const q of Dm) {
        if (!String((q || {}).nombre || '').trim()) F.push(`modo perfil: dimensión ${q && q.n} sin nombre`)
        if (!Number.isInteger(q && q.anio)) F.push(`modo perfil: dimensión ${q && q.n} sin anio`)
      }
      for (const t of medios) {
        if (!t.visual || t.visual.plantilla === 'mapa') continue
        const rotulos = JSON.stringify(t.visual.datos || {}) + ' ' + (t.visual.kicker || '') + ' ' + (t.visual.titular || []).join(' ')
        if (!RE_PAIS.test(rotulos)) F.push(`modo perfil: T${t.n} no compara con el país (ningún rótulo «Guatemala», «nacional» o «país» en la tarjeta)`)
      }
      const anios = [...new Set(Dm.map((q) => q && q.anio).filter(Number.isInteger))]
      if (anios.length > 1) {
        const faltan = anios.filter((a) => !String(Tt[n - 1].texto || '').includes(String(a)))
        if (faltan.length) F.push(`modo perfil: las dimensiones son de varios años (${anios.join(', ')}) y el cierre no nombra ${faltan.join(', ')}`)
      }
    }
  }
  if (enc.hook_evitar && g.hook_tipo === enc.hook_evitar) F.push(`hook_tipo ${g.hook_tipo} es el del último hilo (hook_evitar); elige otro`)
  if (okIds && !okIds.has(g.ancla_id)) F.push(`ancla_id ${g.ancla_id} no está verificada`)
  const t1 = Tt[0].texto || '', p1 = pesoX(t1)
  if (p1 < 40 || p1 > 280) F.push(`T1 debe pesar 40–280 en X (pesa ${p1})`)
  if (t1.split('\n')[0].length > 90) F.push('T1: primera línea > 90')
  if (RE_LINK.test(t1)) F.push('T1 lleva enlace o dominio')
  if (Tt[0].visual && !Tt[0].visual.cifra_ids.includes(g.ancla_id)) F.push('el visual de T1 no usa la cifra ancla')
  const numerosDe = (d) => {
    const out = []
    const rec = (x) => { if (typeof x === 'number') out.push(x); else if (Array.isArray(x)) x.forEach(rec); else if (x && typeof x === 'object') Object.entries(x).forEach(([k, v]) => { if (!['decimales', 'escala', 'destacar', 'clases', 'decimales_pildora', 'i', 'fila', 'col', 'miles', 'cortes', 'maximo', 'minimo_rotulo', 'desde', 'hasta'].includes(k)) rec(v) }) }
    rec(d); return out
  }
  const formatos = (v) => { const a = Math.abs(v); const s = new Set([String(v), String(a), a.toFixed(1), a.toFixed(2), a.toLocaleString('en-US'), a.toLocaleString('en-US', { maximumFractionDigits: 2 })]); return [...s].filter((x) => x && x !== '0') }
  Tt.forEach((t, i) => {
    const tx = t.texto || '', p = pesoX(tx)
    if (i > 0 && p > 280) F.push(`T${t.n} pesa ${p} en X (>280)`)
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
      const malo = !P || P.length > 4 || P.some((p) => { const ok = p && p.nombre && Number.isInteger(p.desde) && Number.isInteger(p.hasta) && p.desde > prev && p.desde <= p.hasta && p.hasta < nP; prev = p ? p.hasta : prev; return !ok })
      if (malo) F.push(`T${t.n} ${v.plantilla}: periodos ≤4 con nombre y desde/hasta índices en orden, sin solaparse`)
    }
    if (v.plantilla === 'bullet' && (largo(d.items) < 1 || largo(d.items) > 6 || d.items.some((it) => typeof (it || {}).meta !== 'number' && typeof d.meta !== 'number'))) F.push(`T${t.n} bullet: 1–6 items, cada uno con meta (propia o común)`)
    if (v.plantilla === 'embudo') {
      const E = Array.isArray(d.etapas) ? d.etapas : []
      if (E.length < 2 || E.length > 6 || E.some((e, i) => i && (e || {}).valor > (E[i - 1] || {}).valor)) F.push(`T${t.n} embudo: 2–6 etapas que no crecen`)
      if (typeof d.misma_cohorte !== 'boolean') F.push(`T${t.n} embudo: misma_cohorte debe ser true o false`)
    }
    if (v.plantilla === 'divergente' && (largo(d.items) < 2 || largo(d.items) > 10)) F.push(`T${t.n} divergente: 2–10 items`)
    if (v.plantilla === 'apilada' && (largo(d.etiquetas) < 2 || largo(d.etiquetas) > 8 || largo(d.partes) < 2 || largo(d.partes) > 5 || d.partes.some((p) => largo((p || {}).valores) !== largo(d.etiquetas)))) F.push(`T${t.n} apilada: 2–8 filas, 2–5 partes y un valor por fila`)
    if (v.plantilla === 'piramide' && (largo(d.grupos) < 4 || largo(d.grupos) > 12 || largo((d.izquierda || {}).valores) !== largo(d.grupos) || largo((d.derecha || {}).valores) !== largo(d.grupos))) F.push(`T${t.n} piramide: 4–12 grupos y un valor por grupo en cada lado`)
    if (v.plantilla === 'treemap' && (largo(d.partes) < 3 || largo(d.partes) > 12)) F.push(`T${t.n} treemap: 3–12 partes`)
    if (v.plantilla === 'dispersion' && (largo(d.puntos) < 8 || largo(d.puntos) > 22 || largo(d.rotular) > 4)) F.push(`T${t.n} dispersion: 8–22 puntos y ≤4 rotulados`)
    if (v.titular.some((l) => !l.trim() || l.length > 26)) F.push(`T${t.n} titular: líneas de ≤26 caracteres`)
    if (!v.kicker.trim() || v.kicker.length > 45) F.push(`T${t.n} kicker vacío o >45`)
    if ((v.nota || '').length > 150) F.push(`T${t.n} nota >150`)
    if (!v.fuente.trim() || v.fuente.length > 70 || /^fuente:/i.test(v.fuente.trim())) F.push(`T${t.n} fuente vacía, >70 o con prefijo «Fuente:»`)
    if (/https?:/.test(JSON.stringify(v))) F.push(`T${t.n} el visual contiene una URL`)
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
const g = await conReparacion(
  'Guion',
  (fallos) =>
    agentRol(
      `Eres el guionista (lee referencias/roles/guionista.md, referencias/narrativa.md y referencias/diseno/graficos.md). Sesión: ${enc.sesion_dir}. ` +
        `Lee encuadre.json y corre python3 scripts/digesto.py ${enc.sesion_dir} --para guionista (no leas los hallazgos_*.json ni verificacion_*.json enteros; para copiar puntos de una serie usa --serie <id>). ` +
        `Paleta: ${enc.paleta}. Fecha: ${fecha}. hook_evitar: ${enc.hook_evitar || 'ninguno'}. MODO DEL POST: ${modoPost}. ` + IM.guionista +
        `ancla_id debe ser una cifra del visual de T1 (T1.visual.cifra_ids la incluye); si T1 va sin visual, la ancla va en su texto. ` +
        (okIds ? `Solo cifras verificada|ajustada con su valor_final: ${[...okIds].join(', ')}. ` : 'MODO FIXTURE: usa las cifras verificadas de la sesión copiada. ') +
        (bajas.length ? `Cifras con segunda fuente NO independiente (reproduce la primaria): ${bajas.join(', ')}: no sostengas la ancla solo en ellas si hay alternativa; si las usas, decláralo en sintesis.incertidumbre. ` : '') +
        `${smoke ? 'MODO SMOKE: 3–4 tuits, smoke:true. ' : `${minN}–${maxN} tuits${MP.impacto ? ' con un beat impacto' : ''}, smoke:false. `}` +
        LIMITES + ' ' +
        (fallos.length ? `TU GUION ANTERIOR FUE RECHAZADO; corrige SOLO esto y vuelve a escribir guion.json completo:\n - ${fallos.join('\n - ')}\n` : '') +
        `Escribe ${enc.sesion_dir}/guion.json completo (con modo: "${modoPost}"${modoPost !== 'hilo' ? ` y el bloque ${modoPost}` : ''}) y devuelve el mismo contenido compacto (con modo, visual.datos en números crudos${modoPost !== 'hilo' ? ' y el bloque ' + modoPost : ''}).`,
      { agentType: 'hilo-guionista', schema: S.guion, label: fallos.length ? 'guionista-reparacion' : 'guionista' }
    ),
  validarGuion,
  2
)
avisar(`Tesis: ${g.tesis} · gancho ${g.hook_tipo}${modoPost !== 'hilo' ? ' · modo ' + modoPost : ''} · ${g.tuits.length} tuits (${g.tuits.map((t) => t.beat[0].toUpperCase()).join('')}) · ${g.tuits.filter((t) => t.visual).length} visuales`)

// ── FASE 4: VISUALES (lotes de 3 en paralelo, con reparación por tuit) ──────
phase('Visuales')
const conVisual = g.tuits.filter((t) => t.visual)
const promptVisualista = (lote, reparar) =>
  `Eres un visualista (lee referencias/roles/visualista.md y referencias/diseno/graficos.md «Flujo del visualista» y «Checklist de QA visual»). ` +
  `Sesión: ${enc.sesion_dir} (guion.json es de solo lectura). Tus tuits: ${lote.map((t) => `T${t.n} (${t.visual.plantilla})`).join(', ')}. ` +
  `Para cada uno: python3 scripts/materializar.py ${enc.sesion_dir} --tuit N (exit 0), UN Read del PNG, checklist; correcciones SOLO en ${enc.sesion_dir}/visuales/tuit_N.ajuste.json y re-materializar. ` +
  `Máximo ${smoke ? 1 : 3} iteraciones por visual.` + (reparar ? ` REPARACIÓN: estos tuits fallaron antes: ${reparar}.` : '')
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
        // Ruta mal reportada pero gate ok y HTML correcto: es un typo del retorno, no del disco
        // (G5 de ensamblar.py comprueba el PNG real después). No gastar una reparación en eso.
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
const dudosos = [...producidos.values()].filter((p) => p.dudoso).map((p) => `T${p.n}: ${p.nota || 'dudoso'}`)
avisar(`Visuales: ${conVisual.length}/${conVisual.length} ok · ${dudosos.length} dudosos`)

// ── FASE 5: ENSAMBLADO (con una reparación) ─────────────────────────────────
phase('Ensamblado')
const reRuta = smoke ? /\/salida\/?$/ : new RegExp(`(^|/)hilos/${fecha}-`)
const validarProd = (p) => {
  const F = []
  if (!p.ruta) F.push('ruta vacía')
  if (/^\//.test(p.ruta || '')) F.push(`la ruta debe ser RELATIVA a la raíz del repo (llegó absoluta: ${p.ruta})`)
  if (!reRuta.test(p.ruta || '')) F.push(smoke ? `en smoke/fixture la salida debe estar en ${enc.sesion_dir}/salida/ (ruta: ${p.ruta})` : `la ruta debe ser hilos/${fecha}-<slug>/ (ruta: ${p.ruta})`)
  if (smoke && !['smoke', 'fixture'].includes(p.registro_id)) F.push('en smoke/fixture registro_id debe ser "smoke" o "fixture"')
  if (p.n_tuits > g.tuits.length || p.n_tuits < minN) F.push(`n_tuits ${p.n_tuits} fuera de rango (guion ${g.tuits.length}, mínimo ${minN})`)
  if (p.n_png > conVisual.length) F.push(`n_png ${p.n_png} > ${conVisual.length}`)
  if (p.gates.mecanico !== 'ok') F.push(`gate mecánico: ${p.gates.mecanico}`)
  if (!['ok', 'incompleto'].includes(p.gates.coherencia)) F.push(`gate coherencia: ${p.gates.coherencia}`)
  if (p.gates.validate !== 'ok') F.push(`make validate: ${p.gates.validate}`)
  if (p.gates.coherencia === 'incompleto' && p.estado !== 'incompleto') F.push('coherencia incompleta exige estado incompleto')
  return F
}
const prod = await conReparacion(
  'Ensamblado',
  (fallos) =>
    agentRol(
      `Eres el productor (lee referencias/roles/productor.md y referencias/narrativa.md). Sesión: ${enc.sesion_dir}. Fecha: ${fecha}. Gancho: ${g.hook_tipo}. Modo del post: ${modoPost}. ` + IM.productor +
        `Tuits dudosos según los visualistas: ${dudosos.length ? dudosos.join(' | ') : 'ninguno'}. ` +
        `Ejecuta: (1) python3 scripts/materializar.py ${enc.sesion_dir} --consolidar; (2) python3 scripts/ensamblar.py ${enc.sesion_dir} --check ` +
        `(si falla, corrige guion.json, re-materializa el tuit y repite; máx. 3 vueltas); (3) gate de coherencia C1–C8 con UN Read de contacto.png y tarjetas sueltas solo si son dudosas; ` +
        `(3b) con el veredicto de C1–C8: python3 scripts/ensamblar.py ${enc.sesion_dir} --solo-estado --estado listo|incompleto (deja el estado final en hilo.json, hilo.html y post.md); ` +
        (smoke
          ? `(4) MODO ${fixture ? 'FIXTURE' : 'SMOKE'}: la salida queda en ${enc.sesion_dir}/salida/, NO toques memoria/, registro_id = "${fixture ? 'fixture' : 'smoke'}"; (5) make validate (exit 0). `
          : `(4) python3 scripts/memoria.py --registrar ${enc.sesion_dir} --ruta <ruta relativa> --estado listo|incompleto (el hook lo toma de guion.json; también guarda series y fuentes primarias${idea ? ` y marca la idea ${idea} del banco con el idea_id de encuadre.json` : ''}); (5) make validate (exit 0). `) +
        LIMITES + ' Devuelve la ruta RELATIVA a la raíz del repo y los gates EXACTAMENTE como "ok" | "falla" | "incompleto" (los detalles van en avisos).' +
        (fallos.length ? `\nTU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}` : ''),
      { agentType: 'hilo-productor', schema: S.produccion, label: fallos.length ? 'productor-reparacion' : 'productor' }
    ),
  validarProd,
  1
)
if (prod.estado === 'incompleto') avisar(`AVISO: el hilo queda INCOMPLETO (coherencia ${prod.gates.coherencia}); revisa post.md antes de publicar.`)

return {
  tesis: g.tesis,
  hook_tipo: g.hook_tipo,
  paleta: g.paleta,
  estado: prod.estado,
  n_tuits: prod.n_tuits,
  n_png: prod.n_png,
  ruta: prod.ruta,
  beats: g.tuits.map((t) => t.beat),
  no_afirma: g.no_afirma,
  cifras_utilizables: okIds ? okIds.size : null,
  cifras_descartadas: noConf,
  independencia_baja: bajas,
  ejes_caidos: ejesCaidos,
  avisos_workflow: AVISOS_WF,
  visuales_dudosos: dudosos,
  avisos: prod.avisos || [],
  sesion_dir: enc.sesion_dir,
  idea_id: enc.idea_id || null,
  modo: modoPost,
  bloque_modo: modoPost !== 'hilo' ? (g[modoPost] || null) : null,
  smoke,
  fixture,
}
