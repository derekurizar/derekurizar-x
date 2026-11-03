export const meta = {
  name: 'noticias',
  description: 'Dos modos. diario (/noticias): noticias del día: 3 rastreadores (pol · seg · eco) proponen candidatas (gate N1) → preselección en código (6 mejores, ≥ 2 secciones) → un verificador por noticia (segunda fuente, citas en el texto guardado, foto; gate N2 + N7) → editor (elige 3–4 y escribe el guion de ≤ 70 s; gate N3–N6, N8) → crítico en modo noticiero (≤ 2 vueltas). semana (/semana, «Las 5 cifras de la semana»): la cosecha de los diarios ya verificada (semana.py cosechar) + 2 rastreadores (ofi: datos oficiales nuevos; sem: lo que no contaron los diarios) → verificación solo de lo nuevo (confirmada o dato oficial) → editor (5 cifras 5→1, SM1–SM11) → crítico en modo semana. 0 créditos de ElevenLabs.',
  whenToUse: 'Invocado por /noticias [hoy|YYYY-MM-DD] DESPUÉS de `python3 scripts/noticias.py preparar`, o por /semana [YYYY-MM-DD] después de `python3 scripts/semana.py preparar` y `cosechar`. args: {trabajo, fecha, modo?: diario|semana (por defecto, semana si trabajo es sesiones/semana-<domingo>), cosecha?: [{id, seccion, titular}] (semana), permitir_fallback}. trabajo = sesiones/noticias-<fecha> (lo imprime preparar). Produce y aprueba <trabajo>/candidatas_*.json, verificacion_*.json, fotos/, noticias.json, guion.json, locucion.json y critica.json; la voz (o la voz falsa), los tiempos, la grabación, el montaje y la entrega los hace la sesión principal después. Si el crítico sigue en «corregir» tras 2 vueltas, el workflow NO falla: devuelve veredicto corregir + faltas_pendientes y el comando pregunta al usuario.',
  phases: [
    { title: 'Rastreo', detail: '3 noticias-rastreador en paralelo (pol, seg, eco): candidatas_<sec>.json con ≤ 5 noticias de hoy o ayer, guardadas con noticias.py leer; gate noticias.py candidatas --check (N1)' },
    { title: 'Verificación', detail: 'un noticias-verificador por preseleccionada (las 6 mejores por puntaje, ≥ 2 secciones, sin duplicadas): segunda fuente independiente u oficial, hechos y cifras con cita literal, foto (noticias.py foto); gate noticias.py verificacion --check (N2 + N7); si quedan < 3 publicables, una segunda ronda con las siguientes' },
    { title: 'Edición', detail: 'noticias-editor: consolidar → digesto → guion.json (gancho, 3–4 noticias, cierre «Hoy en Guatemala», captions); gate noticias.py guion --check (N3–N6, N8, V3)' },
    { title: 'Crítica', detail: 'video-critico en modo noticiero: gancho, claridad, ritmo, precisión, tono, cierre; lo que bloquea vuelve al editor, ≤ 2 vueltas' },
  ],
}

// Guías: referencias/flujo-noticias.md y referencias/roles/noticias-{rastreador,verificador,editor}.md (+ «Modo
// noticiero» de referencias/roles/video-critico.md). Los agentes escriben su artefacto COMPLETO en <trabajo>/ y
// devuelven aquí un resumen validado por schema; los gates de contenido viven en scripts/noticias.py (N1–N8). SECCIONES
// es espejo literal de noticias.SECCIONES (lo vigila scripts/check_workflows.py, W11).

// Modos (W11: MODOS.diario.secciones es espejo de noticias.SECCIONES; MODOS.semana.secciones, puntajes y cifras, de
// semana.SECCIONES, semana.PUNTAJES y semana.CIFRAS). diario = /noticias; semana = /semana («Las 5 cifras de la semana»:
// la cosecha de los diarios ya verificada la hace semana.py antes del workflow; aquí solo se rastrea y verifica lo nuevo).
const MODOS = {
  diario: {
    secciones: ['pol', 'seg', 'eco'],
    puntajes: ['gancho', 'claridad', 'ritmo', 'precision', 'tono', 'cierre'],
    cifras: 0,
  },
  semana: {
    secciones: ['ofi', 'sem'],
    puntajes: ['gancho', 'orden', 'claridad', 'escala', 'tono', 'cierre'],
    cifras: 5,
  },
}
const TODAS_SECCIONES = [...new Set(Object.values(MODOS).flatMap((m) => m.secciones))]
const ESTADOS = ['confirmada', 'en_desarrollo', 'no_confirmada']
const PRESELECCION = 6, NOTICIAS_MIN = 3, SECCIONES_MIN = 2, RONDA_EXTRA = 3
const PRESELECCION_SEMANA = 4, DURACION_MAX = { diario: 70, semana: 90 }
const VUELTAS_CRITICA = 2
const PUNTAJE_MIN = 3
const REGLA_DE = {
  diario: { gancho: 'N-C1', claridad: 'N-C2', ritmo: 'N-C3', precision: 'N-C4', tono: 'N-C5', cierre: 'N-C6' },
  semana: { gancho: 'SM-C1', orden: 'SM-C2', claridad: 'SM-C3', escala: 'SM-C4', tono: 'SM-C5', cierre: 'SM-C6' },
}

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/(noticias-\d{4}-\d{2}-\d{2}|semana-\d{4}-\d{2}-\d{2}|_fixture_noticias\/[a-z0-9_-]+|_fixture_semana\/[a-z0-9_-]+)$/.test(trabajo)) throw new Error('args.trabajo debe ser sesiones/noticias-<fecha> o sesiones/semana-<domingo> (la última línea que imprime `python3 scripts/noticias.py preparar` o `python3 scripts/semana.py preparar`).')
const MODO = String(A.modo || (/semana/.test(trabajo) ? 'semana' : 'diario'))
if (!MODOS[MODO]) throw new Error(`args.modo: ${Object.keys(MODOS).join(' | ')} (semana = /semana).`)
const MD = MODOS[MODO], SEMANA = MODO === 'semana'
const SECCIONES = MD.secciones, PUNTAJES = MD.puntajes
const SCRIPT = SEMANA ? 'scripts/semana.py' : 'scripts/noticias.py'
const fecha = String(A.fecha || (trabajo.match(/\d{4}-\d{2}-\d{2}/) || [''])[0])
if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) throw new Error('args.fecha va como YYYY-MM-DD.')
// /semana: lo que ya trae la cosecha de los diarios (semana.py cosechar; el comando lo pasa): [{id, seccion, titular}]
const COSECHA = SEMANA ? (Array.isArray(A.cosecha) ? A.cosecha : []) : []
const QUE = SEMANA ? `la semana que termina el ${fecha} (lunes a domingo)` : `el noticiero del ${fecha}`
const MODO_ROL = SEMANA ? ' Sigue la sección «Modo semana» de tu guía.' : ""

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
  rechequeo: { type: 'object', properties: { items: { type: 'array' } } },   // lo pide el bloque común; aquí no se usa
  rastreo: {
    type: 'object',
    required: ['seccion', 'archivo', 'gate', 'candidatas'],
    properties: {
      seccion: { type: 'string', enum: TODAS_SECCIONES },
      archivo: { type: 'string', pattern: 'candidatas_(pol|seg|eco|ofi|sem)\\.json$' },
      gate: { type: 'string', enum: ['ok', 'falla'] },
      candidatas: {
        type: 'array',
        items: {
          type: 'object', required: ['id', 'titular', 'puntaje'],
          properties: {
            id: { type: 'string' }, titular: { type: 'string' }, seccion_tema: { type: 'string' }, cifra: { type: ['string', 'null'] },
            puntaje: { type: 'object', required: ['impacto', 'alcance', 'novedad'], properties: { impacto: { type: 'integer' }, alcance: { type: 'integer' }, novedad: { type: 'integer' } } },
          },
        },
      },
    },
  },
  verificacion: {
    type: 'object',
    required: ['id', 'archivo', 'estado', 'gate'],
    properties: {
      id: { type: 'string' }, archivo: { type: 'string', pattern: 'verificacion_[a-z]+-\\d+\\.json$' },
      estado: { type: 'string', enum: ESTADOS }, gate: { type: 'string', enum: ['ok', 'falla'] },
      foto: { type: ['string', 'null'] }, fuentes: { type: 'integer' }, motivo: { type: 'string' },
    },
  },
  edicion: {
    type: 'object',
    required: ['archivo', 'gate', 'noticias', 'gancho', 'estimado_s'],
    properties: {
      archivo: { type: 'string', pattern: 'guion\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      noticias: { type: 'array', items: { type: 'string' } }, gancho: { type: 'string' }, estimado_s: { type: 'number' },
      fallas: { type: 'array', items: { type: 'string' } },
    },
  },
  critica: {
    type: 'object',
    required: ['archivo', 'vuelta', 'veredicto', 'puntajes', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'critica\\.json$' }, vuelta: { type: 'integer' },
      veredicto: { type: 'string', enum: ['pasa', 'corregir'] },
      puntajes: { type: 'object', required: PUNTAJES, properties: Object.fromEntries(PUNTAJES.map((k) => [k, { type: 'integer', minimum: 1, maximum: 5 }])) },
      bloqueantes: { type: 'integer' }, mejoras: { type: 'integer' },
      faltas: {
        type: 'array',
        items: {
          type: 'object', required: ['regla', 'gravedad', 'problema', 'arreglo'],
          properties: { n: { type: 'integer' }, escena: { type: ['integer', 'null'] }, regla: { type: 'string' }, gravedad: { type: 'string', enum: ['bloquea', 'mejora'] }, problema: { type: 'string' }, arreglo: { type: 'string' } },
        },
      },
    },
  },
}

// ── Utilidades ───────────────────────────────────────────────────────────────
const peso = (c) => 2 * c.puntaje.impacto + c.puntaje.alcance + c.puntaje.novedad
const palabras = (t) => new Set(String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter((w) => w.length > 3))
const parecidas = (a, b) => { const x = palabras(a), y = palabras(b); if (!x.size || !y.size) return false; let k = 0; for (const w of x) if (y.has(w)) k++; return k / Math.min(x.size, y.size) >= 0.6 }

// ── 1. Rastreo ───────────────────────────────────────────────────────────────
phase('Rastreo')
const rastreos = await parallel(SECCIONES.map((sec) => () => conReparacion(`rastreo ${sec}`, (fallos) => agentRol(
  `Eres el rastreador de la sección «${sec}» para ${QUE}. TRABAJO: ${trabajo}. Lee referencias/roles/noticias-rastreador.md.${MODO_ROL} ` +
    `Insumo: python3 ${SCRIPT} digesto ${trabajo} --para rastreador. Escribe ${trabajo}/candidatas_${sec}.json (≤ 5, ids ${sec}-1, ${sec}-2…) ` +
    `y corre python3 ${SCRIPT} candidatas ${trabajo} --check --seccion ${sec} hasta 0 fallas.` +
    (fallos.length ? ` REPARACIÓN: tu retorno anterior falló: ${fallos.join('; ')}. Corrige el archivo y vuelve a correr el gate.` : ''),
  { agentType: 'noticias-rastreador', schema: S.rastreo, phase: 'Rastreo', label: `rastreo-${sec}` }),
(r) => [
  ...(r.gate !== 'ok' ? ['el gate N1 no quedó en ok'] : []),
  ...(r.seccion !== sec ? [`seccion ${r.seccion} ≠ ${sec}`] : []),
  ...(!r.candidatas.length && !SEMANA ? ['ninguna candidata'] : []),
  ...r.candidatas.filter((c) => !c.id.startsWith(sec + '-')).map((c) => `id ${c.id} sin el prefijo ${sec}-`),
], 1)))
const candidatas = rastreos.filter(Boolean).flatMap((r) => r.candidatas.map((c) => ({ ...c, sec: r.seccion })))
if (rastreos.some((r) => !r)) avisar(`AVISO: ${SECCIONES.filter((_, k) => !rastreos[k]).join(', ')} sin candidatas (el rastreador no terminó).`)
const MINIMO = SEMANA ? MD.cifras : NOTICIAS_MIN
if (candidatas.length + COSECHA.length < MINIMO) fail(`Solo ${candidatas.length} candidatas${SEMANA ? ` + ${COSECHA.length} cosechadas` : ''} en total: no alcanza (van ≥ ${MINIMO}).`)

// ── 2. Preselección (código): las mejores por peso, sin duplicadas entre secciones (ni con la cosecha, en semana) ──
const orden = [...candidatas].sort((a, b) => peso(b) - peso(a) || a.id.localeCompare(b.id))
const unicas = []
for (const c of orden) {
  const dup = unicas.find((u) => parecidas(u.titular, c.titular)) || COSECHA.find((u) => parecidas(u.titular, c.titular))
  if (dup) { avisar(`${c.id} parece la misma noticia que ${dup.id} («${c.titular}»): se descarta.`); continue }
  unicas.push(c)
}
let pre = unicas.slice(0, SEMANA ? PRESELECCION_SEMANA : PRESELECCION)
const secs = new Set(pre.map((c) => c.sec))
if (!SEMANA && secs.size < SECCIONES_MIN) {
  const otra = unicas.find((c) => !secs.has(c.sec))
  if (otra) pre = [...pre.slice(0, PRESELECCION - 1), otra]
}
const resto = unicas.filter((c) => !pre.includes(c))
log(`Preselección: ${pre.map((c) => `${c.id} (${peso(c)})`).join(', ') || 'ninguna nueva'}${resto.length ? ` · fuera: ${resto.map((c) => c.id).join(', ')}` : ''}${SEMANA ? ` · cosecha: ${COSECHA.length}` : ''}`)

// ── 3. Verificación (un verificador por noticia NUEVA, en paralelo; lo cosechado ya está verificado) ──────────
phase('Verificación')
const verificar = (c) => conReparacion(`verificación ${c.id}`, (fallos) => agentRol(
  `Eres el verificador de la noticia ${c.id} («${c.titular}») para ${QUE}. TRABAJO: ${trabajo}. Lee referencias/roles/noticias-verificador.md.${MODO_ROL} ` +
    `Insumo: python3 ${SCRIPT} digesto ${trabajo} --para verificador --id ${c.id}. Escribe ${trabajo}/verificacion_${c.id}.json, ` +
    `corre python3 ${SCRIPT} foto ${trabajo} --id ${c.id} (cada noticia lleva foto: si sale SIN FOTO, una de referencia de la institución, el lugar o la persona con --origen referencia) y luego python3 ${SCRIPT} verificacion ${trabajo} --check --id ${c.id} hasta 0 fallas ` +
    '(o márcala no_confirmada si no se sostiene).' +
    (fallos.length ? ` REPARACIÓN: tu retorno anterior falló: ${fallos.join('; ')}. Corrige el archivo y vuelve a correr el gate.` : ''),
  { agentType: 'noticias-verificador', schema: S.verificacion, phase: 'Verificación', label: `verifica-${c.id}` }),
(r) => [...(r.id !== c.id ? [`id ${r.id} ≠ ${c.id}`] : []), ...(r.gate !== 'ok' ? ['el gate N2 no quedó en ok'] : [])], 1).catch((e) => { avisar(`AVISO: ${c.id} sin verificar (${String(e.message).split('\n')[0]}).`); return null })
let verificadas = (await parallel(pre.map((c) => () => verificar(c)))).filter(Boolean)
// en semana solo cuenta lo confirmado (en_desarrollo nunca entra); en el diario, todo lo que no es no_confirmada
const publicables = () => verificadas.filter((v) => (SEMANA ? v.estado === 'confirmada' : v.estado !== 'no_confirmada'))
const total = () => publicables().length + COSECHA.length
if (total() < MINIMO && resto.length) {
  const extra = resto.slice(0, RONDA_EXTRA)
  avisar(`Solo ${total()} publicables: segunda ronda con ${extra.map((c) => c.id).join(', ')}.`)
  verificadas = verificadas.concat((await parallel(extra.map((c) => () => verificar(c)))).filter(Boolean))
}
const descartadas = verificadas.filter((v) => !publicables().includes(v)).map((v) => ({ id: v.id, estado: v.estado, motivo: v.motivo || '' }))
log(`Verificación: ${verificadas.map((v) => `${v.id} ${v.estado}${v.foto ? ' · foto ' + v.foto : ''}`).join(' · ') || 'ninguna nueva'}`)
if (total() < MINIMO) fail(`Solo ${total()} noticias publicables (van ≥ ${MINIMO}). Descartadas: ${descartadas.map((d) => `${d.id} (${d.estado}: ${d.motivo})`).join('; ')}`)

// ── 4. Edición ───────────────────────────────────────────────────────────────
phase('Edición')
const ids = new Set([...publicables().map((v) => v.id), ...COSECHA.map((c) => c.id)])
const directivaEditor = (SEMANA
  ? `Eres el editor de «Las 5 cifras de la semana» (${QUE}). TRABAJO: ${trabajo}. Lee referencias/roles/noticias-editor.md, sección «Modo semana». ` +
    `Corre python3 ${SCRIPT} consolidar ${trabajo} y lee python3 ${SCRIPT} digesto ${trabajo} --para editor. ` +
    `Noticias disponibles (cosecha + nuevas confirmadas): ${[...ids].join(', ')}. Escribe ${trabajo}/guion.json (5 cifras, puestos 5→1) y corre python3 ${SCRIPT} guion ${trabajo} --check hasta 0 fallas (SM1–SM11). ` +
    'En el retorno, `noticias` = los ids de noticia de las 5 cifras en el orden de la cuenta.'
  : `Eres el editor del noticiero del ${fecha}. TRABAJO: ${trabajo}. Lee referencias/roles/noticias-editor.md. ` +
    `Corre python3 ${SCRIPT} consolidar ${trabajo} y lee python3 ${SCRIPT} digesto ${trabajo} --para editor. ` +
    `Publicables: ${[...ids].join(', ')}. Escribe ${trabajo}/guion.json y corre python3 ${SCRIPT} guion ${trabajo} --check hasta 0 fallas.`)
const validarEdicion = (r) => [
  ...(r.gate !== 'ok' ? ['el gate del guion no quedó en ok' + (r.fallas && r.fallas.length ? ': ' + r.fallas.join('; ') : '')] : []),
  ...(SEMANA
    ? (r.noticias.length !== MD.cifras ? [`${r.noticias.length} cifras (van ${MD.cifras}, una por noticia)`] : [])
    : (r.noticias.length < NOTICIAS_MIN || r.noticias.length > 4 ? [`${r.noticias.length} noticias (van ${NOTICIAS_MIN}–4)`] : [])),
  ...r.noticias.filter((x) => !ids.has(x)).map((x) => `${x} no es publicable`),
  ...(r.estimado_s > DURACION_MAX[MODO] ? [`${r.estimado_s} s estimados (máximo ${DURACION_MAX[MODO]})`] : []),
]
let edicion = await conReparacion('edición', (fallos) => agentRol(directivaEditor +
  (fallos.length ? ` REPARACIÓN: tu retorno anterior falló: ${fallos.join('; ')}.` : ''),
{ agentType: 'noticias-editor', schema: S.edicion, phase: 'Edición', label: 'editor' }), validarEdicion, 2)

// ── 5. Crítica (≤ 2 vueltas) ─────────────────────────────────────────────────
phase('Crítica')
const validarCritica = (r) => {
  const f = []
  for (const k of PUNTAJES) if (r.puntajes[k] <= 2 && !r.faltas.some((x) => x.gravedad === 'bloquea' && x.regla === REGLA_DE[MODO][k])) f.push(`puntaje ${k} = ${r.puntajes[k]} sin falta «bloquea» de ${REGLA_DE[MODO][k]}`)
  const bloquea = r.faltas.some((x) => x.gravedad === 'bloquea') || PUNTAJES.some((k) => r.puntajes[k] < PUNTAJE_MIN)
  if ((r.veredicto === 'pasa') === bloquea) f.push(`veredicto ${r.veredicto} incoherente con las faltas y los puntajes`)
  return f
}
const MODO_CRITICO = SEMANA ? 'MODO SEMANA (lee la sección «Modo semana» de referencias/roles/video-critico.md; puntajes ' + PUNTAJES.join(', ') + ')'
  : 'MODO NOTICIERO (lee la sección «Modo noticiero» de referencias/roles/video-critico.md)'
let critica = null, previas = []
for (let vuelta = 1; vuelta <= VUELTAS_CRITICA + 1; vuelta++) {
  critica = await conReparacion(`crítica ${vuelta}`, (fallos) => agentRol(
    `${MODO_CRITICO}. TRABAJO: ${trabajo}. Vuelta ${vuelta}. ` +
      `Insumos: ${trabajo}/guion.json, ${trabajo}/locucion.json y python3 ${SCRIPT} digesto ${trabajo} --para editor. Escribe ${trabajo}/critica.json.` +
      (previas.length ? ` Faltas de la vuelta anterior (comprueba primero cada una y omite las resueltas): ${JSON.stringify(previas)}` : '') +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: `critica-${vuelta}` }), validarCritica, 1)
  log(`Crítica ${vuelta}: ${critica.veredicto} · ${PUNTAJES.map((k) => `${k} ${critica.puntajes[k]}`).join(' · ')}`)
  if (critica.veredicto === 'pasa' || vuelta > VUELTAS_CRITICA) break
  previas = critica.faltas.filter((x) => x.gravedad === 'bloquea')
  edicion = await conReparacion(`corrección ${vuelta}`, (fallos) => agentRol(directivaEditor +
    ` CORRECCIÓN ${vuelta}: el crítico pide (corrige SOLO lo que bloquea, con el arreglo exacto, y repasa el gate): ${JSON.stringify(previas)}` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'noticias-editor', schema: S.edicion, phase: 'Crítica', label: `editor-corrige-${vuelta}` }), validarEdicion, 1)
}

return {
  trabajo, fecha, modo: MODO, veredicto: critica.veredicto, puntajes: critica.puntajes,
  faltas_pendientes: critica.faltas.filter((x) => x.gravedad === 'bloquea'),
  mejoras: critica.faltas.filter((x) => x.gravedad === 'mejora'),
  noticias: edicion.noticias, gancho: edicion.gancho, estimado_s: edicion.estimado_s,
  verificadas: verificadas.map((v) => ({ id: v.id, estado: v.estado, foto: v.foto || null })), descartadas,
  candidatas: candidatas.length, cosechadas: COSECHA.length, avisos: AVISOS_WF,
}
