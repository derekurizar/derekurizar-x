export const meta = {
  name: 'video',
  description: 'Guion de retención para /video: video-gancho propone 4–5 ganchos de familias distintas (R1–R10 en código) → el crítico elige en silencio ganador y segundo → guionista (el gancho elegido → promesa → tarjetas y golpes encadenados con «pero» / «por eso» → pago → cierre con un remate o, a veces, una pregunta) → gate V1–V5 + V9 en código → crítico de retención (lee el guion como espectador) → el guionista corrige lo que bloquea (≤ 2 vueltas). 0 créditos de ElevenLabs.',
  whenToUse: 'Invocado por /video <slug|ultimo> [corto|medio|largo] DESPUÉS de `python3 scripts/video.py preparar`. args: {trabajo, duracion, slug, fixture, permitir_fallback}. trabajo = sesiones/<slug>/video (lo imprime preparar); duracion = corto (por defecto) | medio | largo | prueba. Solo produce y aprueba <trabajo>/ganchos.json, seleccion.json, guion.json, locucion.json y critica.json; si el crítico no aprueba ningún gancho tras una vuelta, devuelve veredicto corregir con las faltas de la selección y sin guion; la voz (MCP ElevenLabs), tiempos, grabación, montaje y entrega los hace la sesión principal después. Si el crítico sigue en «corregir» tras 2 vueltas, el workflow NO falla: devuelve veredicto corregir + faltas_pendientes y el comando pregunta al usuario antes de gastar créditos.',
  phases: [
    { title: 'Ganchos', detail: 'video-gancho: ganchos.json con 4–5 candidatos de familias distintas (≥ 2 con visual), referencias/ganchos.md; gate python3 scripts/video.py ganchos --check (R1–R10, rotación R9); ≤ 3 autoreparaciones' },
    { title: 'Selección', detail: 'video-critico en modo selección: mira cada candidato en silencio y luego con la voz, puntúa silencio, referente, tensión, alineación, honestidad y novedad, aplica R11 y escribe seleccion.json (ganador y segundo para la versión B); si ninguno llega a 3, video-gancho rehace una vez' },
    { title: 'Guion', detail: 'video-guionista: guion.json v2 (gancho, promesa, tarjetas y golpes con enlace, cierre, captions); gate python3 scripts/video.py guion --check (V1–V5, V9); ≤ 3 autoreparaciones' },
    { title: 'Crítica', detail: 'video-critico: lee guion.json, locucion.json y digesto.md como espectador (C1–C11); puntajes 1–5 y faltas bloquea|mejora con arreglo; lo que bloquea vuelve al guionista, ≤ 2 vueltas' },
    { title: 'Animación', detail: 'video-animador (solo si el crítico aprueba y hay una escena explica con animacion null): escribe video/animaciones/<id>.js desde el brief, pasa scripts/animaciones.py --check, la registra en la biblioteca y la asigna a la escena' },
  ],
}

// Guías: referencias/flujo-video.md, referencias/ganchos.md, referencias/roles/video-gancho.md,
// referencias/roles/video-guionista.md, referencias/roles/video-critico.md y referencias/roles/video-animador.md.
// Los agentes escriben su artefacto COMPLETO en <trabajo>/ y devuelven aquí un resumen validado por schema; los
// gates de contenido viven en scripts/video.py (V1–V5, V9) y aquí solo se valida el retorno (el sandbox del
// workflow no lee disco ni tiene Date). Las listas de abajo son ESPEJOS literales de scripts/video.py
// (DURACIONES, TIPOS, FAMILIAS, VISUALES, MECANISMOS_EXPLICA, ENLACES, PUNTAJES); las vigila scripts/check_workflows.py (W10). Las demás
// constantes del gate (CPS, COLA, rangos, RITMO_MAX_S, CARACTERES, DURACION_DEFECTO, VISUALES_DE, R1–R10) viven SOLO
// en video.py.

const DURACIONES = ['corto', 'medio', 'largo', 'prueba']
const TIPOS = ['gancho', 'tarjeta', 'golpe', 'definicion', 'adivina', 'mapa', 'ranking', 'escala', 'tiempo', 'explica']
const FAMILIAS = ['contraste', 'paradoja', 'lugar', 'escala', 'tu', 'pregunta', 'ranking', 'resultado']
const VISUALES = ['cifra', 'llenado', 'pareja', 'figuras', 'lugar']
const MECANISMOS_EXPLICA = ['cadena', 'ciclo', 'balance', 'onda', 'embudo', 'proporcion', 'umbral', 'cronologia']
const CIERRE_TIPOS = ['remate', 'pregunta']
const CANDIDATOS_MIN = 4, CANDIDATOS_MAX = 5
const ENLACES = ['pero', 'por_eso', 'y']
const PUNTAJES = ['gancho', 'bucle', 'ritmo', 'escala_humana', 'pago', 'cierre']
const VUELTAS_CRITICA = 2
const PUNTAJE_MIN = 3
// Qué regla del crítico (C1–C11) sostiene cada puntaje: un puntaje ≤ 2 exige una falta «bloquea» de su regla.
const REGLA_DE = { gancho: ['C1'], bucle: ['C2', 'C4', 'C11'], ritmo: ['C3', 'C7', 'C10'], escala_humana: ['C5'], pago: ['C6'], cierre: ['C8', 'C11'] }

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/[a-z0-9_-]+\/(video|trabajo)$/.test(trabajo)) throw new Error('args.trabajo debe ser sesiones/<slug>/video (la última línea que imprime `python3 scripts/video.py preparar`).')
const duracion = String(A.duracion || 'corto')
if (!DURACIONES.includes(duracion)) throw new Error(`args.duracion "${A.duracion}" desconocida (${DURACIONES.join('|')}).`)
const slug = String(A.slug || trabajo.split('/')[1])
const fixture = !!A.fixture || duracion === 'prueba'

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

// ── Schemas de retorno ───────────────────────────────────────────────────────
const S = {
  ganchos: {
    type: 'object',
    required: ['archivo', 'gate', 'candidatos', 'intentos'],
    properties: {
      archivo: { type: 'string', pattern: 'ganchos\\.json$' },
      gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } },
      candidatos: {
        type: 'array',
        items: {
          type: 'object', required: ['id', 'familia', 'visual', 'pantalla'],
          properties: { id: { type: 'string' }, familia: { type: 'string', enum: FAMILIAS }, visual: { type: 'string', enum: VISUALES }, pantalla: { type: 'string' } },
        },
      },
      intentos: { type: 'integer' },
    },
  },
  seleccion: {
    type: 'object',
    required: ['archivo', 'ganador', 'segundo', 'puntajes', 'por_que', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'seleccion\\.json$' },
      ganador: { type: ['string', 'null'] }, segundo: { type: ['string', 'null'] },
      puntajes: { type: 'object' },
      por_que: { type: 'string' },
      faltas: {
        type: 'array',
        items: { type: 'object', required: ['candidato', 'regla', 'problema', 'arreglo'],
          properties: { candidato: { type: 'string' }, regla: { type: 'string' }, problema: { type: 'string' }, arreglo: { type: 'string' } } },
      },
    },
  },
  guion: {
    type: 'object',
    required: ['archivo', 'gate', 'n_escenas', 'tipos', 'estimado_s', 'promesa', 'gancho', 'cierre', 'intentos', 'animaciones_nuevas'],
    properties: {
      archivo: { type: 'string', pattern: 'guion\\.json$' },
      gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } },
      n_escenas: { type: 'integer' },
      tipos: { type: 'array', items: { type: 'string', enum: TIPOS } },
      estimado_s: { type: 'number' },
      promesa: { type: 'object', required: ['texto', 'en', 'pago'], properties: { texto: { type: 'string' }, en: { type: 'integer' }, pago: { type: 'integer' } } },
      gancho: { type: 'object', required: ['familia', 'visual', 'pantalla', 'linea'], properties: { familia: { type: 'string', enum: FAMILIAS }, visual: { type: 'string', enum: VISUALES }, pantalla: { type: 'string' }, linea: { type: 'string' } } },
      cierre: { type: 'object', required: ['tipo', 'forma', 'final'], properties: { tipo: { type: 'string', enum: CIERRE_TIPOS }, forma: { type: 'string' }, final: { type: 'string' }, mecanismo: { type: ['string', 'null'] } } },
      intentos: { type: 'integer' },
      // escenas explica con `animacion: null` (piden una animación nueva al animador); [] si no hay
      animaciones_nuevas: {
        type: 'array',
        items: {
          type: 'object', required: ['escena', 'mecanismo', 'brief', 'titulo', 'pasos'],
          properties: { escena: { type: 'integer' }, mecanismo: { type: 'string', enum: MECANISMOS_EXPLICA }, brief: { type: 'string' }, titulo: { type: 'string' }, pasos: { type: 'array', items: { type: 'string' } } },
        },
      },
    },
  },
  animacion: {
    type: 'object',
    required: ['id', 'archivo', 'check', 'reutilizada'],
    properties: {
      id: { type: 'string', pattern: '^[a-z0-9]+(-[a-z0-9]+)*$' },
      archivo: { type: 'string' },
      check: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } },
      lecturas: { type: 'integer' }, vueltas: { type: 'integer' },
      reutilizada: { type: 'boolean' },
    },
  },
  critica: {
    type: 'object',
    required: ['archivo', 'vuelta', 'veredicto', 'puntajes', 'bloqueantes', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'critica\\.json$' },
      vuelta: { type: 'integer' },
      veredicto: { type: 'string', enum: ['pasa', 'corregir'] },
      puntajes: {
        type: 'object', required: PUNTAJES,
        properties: Object.fromEntries(PUNTAJES.map((p) => [p, { type: 'integer', minimum: 1, maximum: 5 }])),
      },
      bloqueantes: { type: 'integer' }, mejoras: { type: 'integer' },
      faltas: {
        type: 'array',
        items: {
          type: 'object', required: ['regla', 'gravedad', 'problema', 'arreglo'],
          properties: {
            n: { type: 'integer' }, escena: { type: ['integer', 'null'] },
            regla: { type: 'string', pattern: '^C(1[01]|[1-9])$' },
            gravedad: { type: 'string', enum: ['bloquea', 'mejora'] },
            problema: { type: 'string' }, arreglo: { type: 'string' },
          },
        },
      },
    },
  },
}

// ── Validadores de los retornos (los gates de contenido ya corrieron en video.py) ─
// la ruta del archivo, relativa a la raíz aunque el agente la dé absoluta o con ./ delante
const rel = (p) => String(p || '').replace(/^\.\//, '').replace(/^.*?\/(?=sesiones\/)/, '')
const validarGanchos = (r) => {
  const F = []
  if (rel(r.archivo) !== `${trabajo}/ganchos.json`) F.push(`archivo debe ser ${trabajo}/ganchos.json (llegó ${r.archivo})`)
  if (r.gate !== 'ok') { F.push(...((r.fallas && r.fallas.length) ? r.fallas : ['el gate `python3 scripts/video.py ganchos --check` falló sin detalle: corre el gate y copia sus líneas FALLA'])); return F }
  const cs = r.candidatos || []
  if (cs.length < CANDIDATOS_MIN || cs.length > CANDIDATOS_MAX) F.push(`${cs.length} candidatos; van ${CANDIDATOS_MIN}–${CANDIDATOS_MAX}`)
  if (new Set(cs.map((c) => c.familia)).size !== cs.length) F.push('familias repetidas: cada candidato prueba un mecanismo distinto')
  if (cs.filter((c) => c.visual !== 'cifra').length < 2) F.push('al menos 2 candidatos con un visual que no sea la cifra sola')
  if (r.intentos > 3) avisar(`AVISO: video-gancho necesitó ${r.intentos} intentos con el gate (presupuesto 3).`)
  return F
}
const validarSeleccion = (r) => {
  const F = []
  if (rel(r.archivo) !== `${trabajo}/seleccion.json`) F.push(`archivo debe ser ${trabajo}/seleccion.json (llegó ${r.archivo})`)
  const ids = (K ? K.candidatos : []).map((c) => c.id)
  if (r.ganador !== null && !ids.includes(r.ganador)) F.push(`ganador «${r.ganador}» no es un candidato (${ids.join(', ')})`)
  if (r.ganador !== null && (r.segundo === r.ganador || (r.segundo !== null && !ids.includes(r.segundo)))) F.push(`segundo «${r.segundo}» debe ser otro candidato`)
  if (r.ganador === null && !(r.faltas || []).length) F.push('sin ganador: escribe en faltas lo que bloquea a cada candidato y su arreglo')
  for (const id of ids) if (!(r.puntajes || {})[id]) F.push(`faltan los puntajes de ${id}`)
  return F
}
const validarGuion = (r) => {
  const F = []
  if (rel(r.archivo) !== `${trabajo}/guion.json`) F.push(`archivo debe ser ${trabajo}/guion.json (llegó ${r.archivo})`)
  if (r.gate !== 'ok') { F.push(...((r.fallas && r.fallas.length) ? r.fallas : ['el gate `python3 scripts/video.py guion --check` falló sin detalle: corre el gate y copia sus líneas FALLA'])); return F }
  const n = r.n_escenas
  if (!Array.isArray(r.tipos) || r.tipos.length !== n) F.push(`tipos[] tiene ${(r.tipos || []).length} entradas y n_escenas es ${n} (una por escena, sin contar el cierre)`)
  if (r.tipos && r.tipos[0] !== 'gancho') F.push('la escena 1 debe ser de tipo gancho')
  if (r.tipos && r.tipos[1] !== 'tarjeta') F.push('la escena 2 debe ser la tarjeta T1')
  const p = r.promesa || {}
  if (![1, 2].includes(p.en)) F.push(`promesa.en debe ser 1 o 2 (llegó ${p.en})`)
  if (!(p.pago >= Math.ceil((2 * n) / 3) && p.pago <= n) || p.pago === p.en) F.push(`promesa.pago = ${p.pago} debe estar en el último tercio (escenas ${Math.ceil((2 * n) / 3)}–${n}) y ser distinto de promesa.en`)
  const c = r.cierre || {}, fin = String(c.final || '').trim()
  if (c.tipo === 'pregunta' && !/\?$/.test(fin)) F.push('cierre de tipo pregunta: la frase final termina en «?»')
  if (c.tipo === 'remate' && /\?/.test(fin)) F.push('cierre de tipo remate: la frase final no es una pregunta')
  if (r.intentos > 3) avisar(`AVISO: el guionista necesitó ${r.intentos} intentos con el gate (presupuesto 3).`)
  for (const a of r.animaciones_nuevas || []) {
    if (!(r.tipos || [])[a.escena - 1] || r.tipos[a.escena - 1] !== 'explica') F.push(`animaciones_nuevas: la escena ${a.escena} no es de tipo explica`)
  }
  return F
}
const validarAnimacion = (r) => {
  const F = []
  if (r.archivo !== `video/animaciones/${r.id}.js`) F.push(`archivo debe ser video/animaciones/${r.id}.js (llegó ${r.archivo})`)
  if (r.check !== 'ok' && !(r.fallas && r.fallas.length)) F.push('check falla sin detalle: copia las líneas FALLA de scripts/animaciones.py --check')
  if (r.lecturas > 3) avisar(`AVISO: el animador leyó la hoja de contacto ${r.lecturas} veces (presupuesto 3).`)
  return F
}
const validarCritica = (r) => {
  const F = []
  if (rel(r.archivo) !== `${trabajo}/critica.json`) F.push(`archivo debe ser ${trabajo}/critica.json (llegó ${r.archivo})`)
  const faltas = r.faltas || []
  const bloq = faltas.filter((f) => f.gravedad === 'bloquea').length
  if (r.bloqueantes !== bloq) F.push(`bloqueantes ${r.bloqueantes} ≠ ${bloq} faltas con gravedad bloquea`)
  const min = Math.min(...PUNTAJES.map((k) => (r.puntajes || {})[k] ?? 0))
  const deberiaPasar = bloq === 0 && min >= PUNTAJE_MIN
  if ((r.veredicto === 'pasa') !== deberiaPasar) F.push(`veredicto ${r.veredicto} con ${bloq} falta(s) que bloquean y puntaje mínimo ${min} (pasa solo sin bloqueantes y con todos los puntajes ≥ ${PUNTAJE_MIN})`)
  for (const k of PUNTAJES) {
    const v = (r.puntajes || {})[k]
    if (v <= 2 && !faltas.some((f) => f.gravedad === 'bloquea' && REGLA_DE[k].includes(f.regla))) F.push(`puntaje ${k} = ${v} sin una falta que bloquee de su regla (${REGLA_DE[k].join('/')}): sube el puntaje o escribe la falta`)
  }
  for (const f of faltas) {
    if (f.escena != null && !(f.escena >= 1 && f.escena <= (G ? G.n_escenas + 1 : 99))) F.push(`falta ${f.n || '?'}: escena ${f.escena} fuera de rango (1–${G ? G.n_escenas + 1 : '?'}; null = global)`)
  }
  return F
}

// ── FASE 1: GANCHOS (video-gancho → gate R1–R10 en video.py) ─────────────────
phase('Ganchos')
let K = null
const invocarGanchos = (fallos, intento, faltasSel, pulir) =>
  agentRol(
    `Eres el autor de ganchos de video (lee referencias/ganchos.md y referencias/roles/video-gancho.md). TRABAJO = ${trabajo} · hilo ${slug} · duración ${duracion}${fixture ? ' (FIXTURE)' : ''}.\n` +
      `Lee SOLO ${trabajo}/digesto.md (NO hilo.json, datos.json, HTML ni código). Escribe ${trabajo}/ganchos.json con ${CANDIDATOS_MIN}–${CANDIDATOS_MAX} candidatos a escena 1 de FAMILIAS DISTINTAS (${FAMILIAS.join(', ')}), al menos 2 con un visual que no sea la cifra sola (${VISUALES.join(', ')}), sin las familias ni el visual que «Ganchos recientes» bloquea. Cada uno: id, familia, visual, visual_datos (ids de cifra o calculo), pantalla, linea, verbo, texto (cifras en dígitos), calculo si hace falta, promesa_sugerida y por_que. Primero el segundo 1 en silencio, después la voz: sin abrir con contexto, «Guatemala» dentro de la frase, solo lo que el dato dice y con su periodo.\n` +
      `Corre python3 scripts/video.py ganchos ${trabajo} --check hasta exit 0 (≤ 3 intentos; corrige SOLO las líneas FALLA).\n` +
      (faltasSel && faltasSel.length ? `${pulir ? `EL CRÍTICO ELIGIÓ ${pulir[0]} (ganador)${pulir[1] ? ` y ${pulir[1]} (segundo)` : ''}; aplica SOLO a esos candidatos estos arreglos (mismo id, misma familia y visual; el texto exacto viene en ARREGLO) y vuelve a pasar el gate:` : 'EL CRÍTICO NO APROBÓ NINGÚN CANDIDATO; rehaz los señalados con su arreglo (o cámbialos por otra familia) y vuelve a pasar el gate:'}\n - ${faltasSel.map((f) => `[${f.candidato} · ${f.regla}] ${f.problema} → ARREGLO: ${f.arreglo}`).join('\n - ')}\n` : '') +
      (fallos.length ? `TU RETORNO ANTERIOR FUE RECHAZADO; corrige SOLO esto:\n - ${fallos.join('\n - ')}\n` : '') +
      'Retorno: {archivo, gate: ok|falla, fallas[], candidatos[]{id, familia, visual, pantalla}, intentos}.',
    { agentType: 'video-gancho', schema: S.ganchos, label: pulir ? 'ganchos-pulir' : faltasSel ? 'ganchos-rehacer' : 'ganchos' }
  )
K = await conReparacion('Ganchos', (f, i) => invocarGanchos(f, i, null), validarGanchos, 2)
avisar(`Ganchos: ${K.candidatos.map((c) => `${c.id} ${c.familia}/${c.visual} «${c.pantalla}»`).join(' · ')}`)

// ── FASE 2: SELECCIÓN (el crítico elige en silencio; si ninguno pasa, video-gancho rehace una vez) ─
phase('Selección')
const seleccionar = (vuelta) =>
  conReparacion(
    'Selección',
    (fallos) =>
      agentRol(
        `Eres el crítico de retención en MODO SELECCIÓN DE GANCHO (lee referencias/roles/video-critico.md, sección «Modo selección de gancho», y referencias/ganchos.md). TRABAJO = ${trabajo} · vuelta ${vuelta}.\n` +
          `Lee SOLO referencias/ganchos.md, ${trabajo}/ganchos.json y ${trabajo}/digesto.md. Mira cada candidato PRIMERO EN SILENCIO (pantalla, línea y lo que muestra el visual en el cuadro 0) y después con la voz; puntúa silencio, referente, tension, alineacion, honestidad y novedad (1–5) y aplica R11 (miedo, morbo, palabras que el dato no dice). Elige ganador (ninguno ≤ 2) y segundo de otra familia (la versión B); si ninguno llega a 3 en todo, ganador null y las faltas con su arreglo exacto. Escribe ${trabajo}/seleccion.json.\n` +
          (fallos.length ? `TU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}\n` : '') +
          'Retorno: {archivo, ganador, segundo, puntajes{<id>: {silencio, referente, tension, alineacion, honestidad, novedad}}, por_que, faltas[]{candidato, regla, problema, arreglo}}.',
        { agentType: 'video-critico', schema: S.seleccion, label: `seleccion-${vuelta}` }
      ),
    validarSeleccion,
    1
  )
let SEL = await seleccionar(1)
if (SEL.ganador === null) {
  avisar(`Selección 1: ningún gancho aprobado (${SEL.faltas.length} falta(s)) → video-gancho rehace`)
  K = await conReparacion('Ganchos (rehacer)', (f, i) => invocarGanchos(f, i, i === 0 ? SEL.faltas : null), validarGanchos, 1)
  SEL = await seleccionar(2)
}
if (SEL.ganador === null) {
  avisar(`AVISO: el crítico no aprobó ningún gancho tras rehacerlos (${trabajo}/seleccion.json): decide con el usuario antes de seguir.`)
  return {
    trabajo, slug, duracion, fixture, archivo_ganchos: `${trabajo}/ganchos.json`, archivo_seleccion: `${trabajo}/seleccion.json`,
    veredicto: 'corregir', ganchos: K.candidatos, seleccion: SEL,
    faltas_pendientes: SEL.faltas.map((f) => ({ escena: 1, regla: f.regla, gravedad: 'bloquea', problema: `[${f.candidato}] ${f.problema}`, arreglo: f.arreglo })),
    mejoras: [], animaciones: [], animaciones_pendientes: [], avisos_workflow: AVISOS_WF,
  }
}
avisar(`Selección: gana ${SEL.ganador} (${(K.candidatos.find((c) => c.id === SEL.ganador) || {}).familia}) · segundo ${SEL.segundo || '—'} · ${SEL.por_que}`)
// los arreglos que el crítico dejó al ganador y al segundo se aplican ANTES de que el ganador pase al guion (una vuelta;
// el guionista no puede tocar la escena 1). Mismo id, familia y visual: la elección no cambia
const elegidos = [SEL.ganador, SEL.segundo].filter(Boolean)
const arreglos = SEL.faltas.filter((f) => elegidos.includes(f.candidato))
if (arreglos.length) {
  avisar(`Selección: ${arreglos.length} arreglo(s) para ${elegidos.join(' y ')} → video-gancho los aplica`)
  const antes = K
  K = await conReparacion('Ganchos (pulir)', (f, i) => invocarGanchos(f, i, i === 0 ? arreglos : null, elegidos), validarGanchos, 1)
  for (const id of elegidos) {
    const a = antes.candidatos.find((c) => c.id === id), b = K.candidatos.find((c) => c.id === id)
    if (!b || b.familia !== a.familia || b.visual !== a.visual) fail(`Ganchos (pulir): ${id} cambió de familia o de visual (o desapareció): la elección ya no vale.`)
  }
}

// ── FASE 3: GUION (guionista → gate V1–V5 + V9 en video.py) ──────────────────
phase('Guion')
let G = null
const invocarGuionista = (fallos) =>
  agentRol(
    `Eres el guionista de video (lee referencias/roles/video-guionista.md). TRABAJO = ${trabajo} · hilo ${slug} · duración ${duracion}${fixture ? ' (FIXTURE: sin créditos, voz falsa)' : ''}.\n` +
      `PRIMERO corre python3 scripts/video.py ganchos ${trabajo} --usar: el gancho que eligió el crítico (${SEL.ganador}) pasa a la escena 1 de ${trabajo}/guion.json y NO lo cambias (el gate lo comprueba; si el crítico de guion bloquea el gancho y propone otro candidato, cámbialo con --usar <id> --segundo <otro>). Lee SOLO ${trabajo}/digesto.md y, de ${trabajo}/ganchos.json, la promesa_sugerida del elegido (NO hilo.json, datos.json, HTML ni código). Completa ${trabajo}/guion.json v2: contexto_superior, promesa{texto, en, pago} (en: 2 lo normal), escenas[] (la 1 es el gancho elegido; la 2 la tarjeta T1, que lo paga y, si el gancho no dijo «Guatemala», lo dice en su primera oración; luego tarjetas y golpes con enlace pero|por_eso|y, golpe ≤ 6 palabras, calculo cuando traduzcas una cifra; las escenas golpe con pantalla/linea/verbo; opcionales, como dice el digesto: UNA escena definicion {termino, definicion}, UNA adivina {pregunta, opciones[3], correcta}, UNA escena explica {mecanismo (cadena|ciclo|balance|onda|embudo|proporcion|umbral|cronologia: lo que HACE el fenómeno), brief (siempre), animacion (id del digesto con ESE mecanismo y no bloqueada) o null (lo normal si no hay una de ese mecanismo: el animador la escribe y queda como plantilla), titulo, pasos[]} que explique el mecanismo del fenómeno y, si el hilo tiene tarjeta de mapa, UNA escena mapa {tuit, golpe} en su lugar). La pantalla puede ser titular, la voz NO: la oración que dice la pantalla lleva verbo conjugado («Nacen casi 168 bebés al día…», nunca «Casi 168 bebés al día…»), cierre{texto, resumen[2–3], tipo, forma, final, consecuencia{mecanismo, quien, verbo}} (las cifras van en las conclusiones; la frase final NO es un dato sino su CONSECUENCIA: lo normal un remate forma consecuencia, lo que la cifra le hace a quien la vive, con gente como sujeto y un verbo en pasado o presente («Este año, 34 familias ya enterraron a un hijo por desnutrición.»), sin repetir la cifra del gancho, sin fatalismo ni futuro que la fuente no proyecta; a veces pendiente o quien_decide; a veces una PREGUNTA, nunca si el video anterior cerró con pregunta; referencias/cierres.md F1–F8: la frase final nombra el fenómeno del video, sin analogías de otro ámbito, sin cebo y, en un tema sensible, sin tocar la vida del espectador) y caption{tiktok, instagram, facebook, shorts}. La promesa, el gancho, cómo abres cada escena y la frase final del cierre NO repiten las de «Frases ya usadas» ni «Cierres recientes» del digesto (los ejemplos de las guías son forma, no texto).\n` +
      `Corre python3 scripts/video.py guion ${trabajo} --check hasta exit 0 (≤ 3 intentos; corrige SOLO las líneas FALLA).\n` +
      (fallos.length ? `TU GUION FUE RECHAZADO; corrige SOLO esto, no toques lo que ya pasó, y vuelve a pasar el gate:\n - ${fallos.join('\n - ')}\n` : '') +
      'Retorno: {archivo, gate: ok|falla, fallas[], n_escenas (sin el cierre), tipos[] (uno por escena), estimado_s, promesa{texto, en, pago}, gancho{familia, visual, pantalla, linea}, cierre{tipo, forma, final, mecanismo}, intentos, animaciones_nuevas[]{escena, mecanismo, brief, titulo, pasos} (las escenas explica con animacion null; [] si no hay)}.',
    { agentType: 'video-guionista', schema: S.guion, label: fallos.length ? 'guionista-reparacion' : 'guionista' }
  )
G = await conReparacion('Guion', invocarGuionista, validarGuion, 2)
avisar(`Guion: ${G.n_escenas} escenas (${G.tipos.map((t) => t[0].toUpperCase()).join('')}) + cierre · ${G.estimado_s} s estimados · gancho ${G.gancho.familia}/${G.gancho.visual} «${G.gancho.pantalla}» · promesa en E${G.promesa.en} → pago E${G.promesa.pago} · ${G.intentos} intento(s)`)

// ── FASE 4: CRÍTICA (crítico de retención → el guionista corrige lo que bloquea) ─
phase('Crítica')
const fmtFaltas = (fs) => fs.map((f) => `[${f.regla} · ${f.escena != null ? 'escena ' + f.escena : 'global'} · ${f.gravedad}] ${f.problema} → ARREGLO: ${f.arreglo}`)
const criticar = (vuelta, previas) =>
  conReparacion(
    'Crítica',
    (fallos) =>
      agentRol(
        `Eres el crítico de retención (lee referencias/roles/video-critico.md). TRABAJO = ${trabajo} · vuelta ${vuelta}/${VUELTAS_CRITICA + 1} · duración ${duracion}${fixture ? ' (FIXTURE)' : ''}.\n` +
          `Lee SOLO ${trabajo}/guion.json, ${trabajo}/locucion.json y ${trabajo}/digesto.md (con su sección «Frases ya usadas», para C11). Léelo como alguien que desliza en TikTok y no leyó el hilo: primero los 3 primeros segundos EN SILENCIO (solo pantalla y línea del gancho), luego escena por escena «¿por qué seguiría viendo?».\n` +
          `Comprueba C1–C11; una falta por problema; el arreglo lleva el texto exacto y SOLO cifras del digesto (si hace falta un derivado, escribe su calculo). Escribe ${trabajo}/critica.json.\n` +
          (previas && previas.length ? `FALTAS DE LA VUELTA ANTERIOR (comprueba primero cada una; omite las resueltas):\n - ${fmtFaltas(previas).join('\n - ')}\n` : '') +
          (fallos.length ? `TU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}\n` : '') +
          'Retorno: {archivo, vuelta, veredicto: pasa|corregir, puntajes{gancho, bucle, ritmo, escala_humana, pago, cierre} (1–5), bloqueantes, mejoras, faltas[]{n, escena (null = global), regla C1–C11, gravedad bloquea|mejora, problema, arreglo}}.',
        { agentType: 'video-critico', schema: S.critica, label: `critico-${vuelta}` }
      ),
    validarCritica,
    1
  )
let C = await criticar(1, null)
// vuelve al guionista lo que bloquea (≤ VUELTAS_CRITICA vueltas en total); y si el crítico aprueba con algún
// puntaje justo (= PUNTAJE_MIN) dejando mejoras, UNA sola vuelta de pulido con esas mejoras (0 créditos: la voz aún
// no se ha generado). Aprobado con todo ≥ 4 no se pule: las mejoras que queden van al reporte.
let pulido = false
let intentosGuionista = G.intentos
const pulir = (c) => c.veredicto === 'pasa' && !pulido &&
  Math.min(...PUNTAJES.map((k) => (c.puntajes || {})[k] ?? 5)) <= PUNTAJE_MIN && c.faltas.some((f) => f.gravedad === 'mejora')
for (let k = 0; k < VUELTAS_CRITICA && (C.veredicto !== 'pasa' || pulir(C)); k++) {
  if (C.veredicto === 'pasa') pulido = true
  const faltas = C.faltas.filter((f) => f.gravedad === 'bloquea').concat(C.faltas.filter((f) => f.gravedad === 'mejora'))
  const cabecera = C.veredicto === 'pasa'
    ? 'EL CRÍTICO APROBÓ TU GUION CON PUNTAJES JUSTOS; aplica estas mejoras (el texto exacto viene en ARREGLO; si un arreglo pide una cifra que no está en el digesto, no la inventes: declara la falta de dato) sin tocar lo que ya funciona. Después vuelve a pasar el gate:'
    : 'TU GUION FUE RECHAZADO POR EL CRÍTICO; corrige TODAS las faltas que bloquean y las mejoras que quepan (el texto exacto viene en ARREGLO; si un arreglo pide una cifra que no está en el digesto, no la inventes: declara la falta de dato). Después vuelve a pasar el gate:'
  avisar(`Crítica ${k + 1}: ${C.veredicto} · ${C.bloqueantes} falta(s) que bloquean · ${faltas.length - C.bloqueantes} mejora(s) · puntajes ${PUNTAJES.map((p) => p + ' ' + C.puntajes[p]).join(' · ')} → el guionista ${C.veredicto === 'pasa' ? 'pule' : 'corrige'}`)
  G = await conReparacion(
    'Guion (crítica)',
    (fallos, intento) => invocarGuionista(intento === 0 ? [cabecera].concat(fmtFaltas(faltas)) : fallos),
    validarGuion,
    1
  )
  intentosGuionista += G.intentos
  C = await criticar(k + 2, C.faltas)
}
const pendientes = C.faltas.filter((f) => f.gravedad === 'bloquea')
const mejoras = C.faltas.filter((f) => f.gravedad === 'mejora')
if (C.veredicto !== 'pasa') avisar(`AVISO: la crítica deja ${pendientes.length} falta(s) que bloquean tras ${VUELTAS_CRITICA} vueltas (${trabajo}/critica.json): no gastes créditos de voz sin decidirlo con el usuario.`)
else avisar(`Crítica: pasa · puntajes ${PUNTAJES.map((p) => p + ' ' + C.puntajes[p]).join(' · ')} · ${mejoras.length} mejora(s) anotadas`)

// ── FASE 5: ANIMACIÓN (solo con el guion aprobado: una animación a medida por escena explica nueva) ─────
phase('Animación')
const animaciones = [], animacionesPendientes = []
const nuevas = G.animaciones_nuevas || []
if (nuevas.length && (C.veredicto !== 'pasa' || fixture)) {
  animacionesPendientes.push(...nuevas)
  avisar(`AVISO: ${nuevas.length} animación(es) sin escribir (${fixture ? 'fixture' : 'el guion no pasó la crítica'}): lanza video-animador cuando el guion quede decidido.`)
} else {
  for (const a of nuevas) {
    const r = await conReparacion(
      `Animación E${a.escena}`,
      (fallos) =>
        agentRol(
          `Eres el animador de video (lee referencias/roles/video-animador.md; para el contrato mira UNA animación de video/animaciones/, mejor una de otro mecanismo que cadena.js: no copies su forma de cajas). TRABAJO = ${trabajo} · hilo ${slug} · escena ${a.escena} (explica).\n` +
            `MECANISMO: ${a.mecanismo} (meta.mecanismo de la animación; muéstralo, no lo conviertas en una lista)\nBRIEF: ${a.brief}\nTÍTULO (va arriba, no lo repitas en el lienzo): ${a.titulo}\nPASOS (cada uno entra cuando la voz lo dice): ${a.pasos.map((p, i) => `${i + 1}. ${p}`).join(' · ')}\n` +
            `Primero python3 scripts/animaciones.py --lista: reutiliza una SOLO si es del mecanismo ${a.mecanismo} y cuenta lo mismo (el gate rechaza otro mecanismo y las de los últimos videos). Si no, escribe video/animaciones/<id>.js (id por lo que HACE, no por el video) y pasa python3 scripts/animaciones.py --check <id> (≤ 3 vueltas, ≤ 3 lecturas de su contacto.png). Con check ok: --registrar <id> --video ${slug} y --asignar ${trabajo} --escena ${a.escena} --id <id> (exit 0).\n` +
            (fallos.length ? `TU RETORNO ANTERIOR FUE RECHAZADO; corrige:\n - ${fallos.join('\n - ')}\n` : '') +
            'Retorno: {id, archivo, check: ok|falla, fallas[], lecturas, vueltas, reutilizada}.',
          { agentType: 'video-animador', schema: S.animacion, label: `animador-e${a.escena}` }
        ),
      validarAnimacion,
      1
    )
    if (r.check === 'ok') { animaciones.push({ escena: a.escena, ...r }); avisar(`Animación E${a.escena}: «${r.id}»${r.reutilizada ? ' (reutilizada)' : ' (nueva, en la biblioteca)'}`) }
    else { animacionesPendientes.push({ ...a, fallas: r.fallas }); avisar(`AVISO: la animación de E${a.escena} no pasó animaciones.py --check: ${(r.fallas || []).join(' · ')}`) }
  }
}

return {
  trabajo,
  slug,
  duracion,
  fixture,
  archivo_guion: `${trabajo}/guion.json`,
  archivo_locucion: `${trabajo}/locucion.json`,
  archivo_critica: `${trabajo}/critica.json`,
  archivo_ganchos: `${trabajo}/ganchos.json`,
  archivo_seleccion: `${trabajo}/seleccion.json`,
  ganchos: K.candidatos,
  seleccion: { ganador: SEL.ganador, segundo: SEL.segundo, puntajes: SEL.puntajes, por_que: SEL.por_que },
  n_escenas: G.n_escenas,
  tipos: G.tipos,
  estimado_s: G.estimado_s,
  promesa: G.promesa,
  gancho: G.gancho,
  cierre: G.cierre,
  intentos_guionista: intentosGuionista,
  veredicto: C.veredicto,
  puntajes: C.puntajes,
  vueltas_critica: C.vuelta,
  faltas_pendientes: pendientes,
  mejoras,
  animaciones,
  animaciones_pendientes: animacionesPendientes,
  avisos_workflow: AVISOS_WF,
}
