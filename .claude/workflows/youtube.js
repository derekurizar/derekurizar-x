export const meta = {
  name: 'youtube',
  description: 'Video largo de YouTube desde una serie entregada (/youtube-long): youtube-editor (el MONTAJE: quita lo que se repite al pegar las partes —hechos contados otra vez, personas presentadas otra vez, siglas explicadas otra vez—, recorta frases e incisos en silencios de ≥ 80 ms, escribe 1–2 oraciones de puente donde hay un salto de tiempo o de tema sin anunciar lo que viene, la promesa global y el título, la descripción y los capítulos; gate youtube.py montaje --check YT1–YT8, YT11) → historia-oyente en modo largo (el video entero de corrido: repeticiones, saltos, confusiones) → video-critico en modo largo (repetición, continuidad, uniones, ritmo, promesa, claridad; arreglos probados con youtube.py probar; ≤ 2 vueltas, desde la 2 acotadas) → se detiene con veredicto aprobar_montaje para que el usuario lo apruebe antes de gastar créditos. 0 créditos.',
  whenToUse: 'Invocado por /youtube-long <serie> DESPUÉS de `python3 scripts/youtube.py preparar <serie>`. args: {trabajo, permitir_fallback, desde, notas}. trabajo = sesiones/youtube-<slug> (la última línea de preparar). desde: "retoque" + notas = montaje.json ya existe: el editor aplica solo las notas del usuario → gate → oyente → crítica (1 vuelta). Devuelve veredicto aprobar_montaje (la sesión muestra youtube.py resumen y pregunta) o corregir + faltas_pendientes. La voz de las piezas nuevas, el armado, la grabación 16:9, el montaje, la miniatura y la entrega los hace la sesión después.',
  phases: [
    { title: 'Montaje', detail: 'youtube-editor: montaje.json desde el borrador (las marcas del formato corto ya quitadas): quitar, recortar (frases e incisos literales, en silencios ≥ 80 ms, sin partir nombres), puentes (1–2 oraciones con hechos, foto y titular, sin anunciar), promesa global, títulos de capítulo, título y descripción de YouTube; gate youtube.py montaje --check (YT1–YT8, YT11) y su RETORNO' },
    { title: 'Oyente', detail: 'historia-oyente en modo largo: el video entero de corrido (youtube.py digesto --para oyente); repeticiones, saltos y confusiones; vuelve a oír tras cada corrección' },
    { title: 'Crítica', detail: 'video-critico en modo largo: repeticion, continuidad, uniones, ritmo, promesa, claridad (Y-C1–Y-C6); cada confusión y salto del oyente se resuelve o se justifica; arreglos probados con youtube.py probar que el editor aplica tal cual con youtube.py aplicar; ≤ 2 vueltas (1 en retoque), desde la 2 acotadas; con «pasa», las mejoras ya probadas se aplican solas y el gate se repite' },
  ],
}

// Guías: referencias/flujo-youtube.md, referencias/roles/youtube-editor.md y el «Modo largo» de
// referencias/roles/{historia-oyente,video-critico}.md. Los gates viven en scripts/youtube.py (YT1–YT11). PUNTAJES y los
// límites son espejos literales de scripts/youtube.py (los vigila scripts/check_workflows.py, W14).

const PUNTAJES = ['repeticion', 'continuidad', 'uniones', 'ritmo', 'promesa', 'claridad', 'escalada']
const REGLA_DE = { repeticion: 'Y-C1', continuidad: 'Y-C2', uniones: 'Y-C3', ritmo: 'Y-C4', promesa: 'Y-C5', claridad: 'Y-C6', escalada: 'Y-C7' }
const PUENTE_ORACIONES = 2, PUENTE_CARACTERES = 160, REPRISE_MAX = 3, REVOZAR_MAX = 3   // W14: youtube.py
const DURACION_MIN = 480, DURACION_MAX = 1200                                       // W14: DURACION_S de youtube.py
const VUELTAS_CRITICA = 2, PUNTAJE_MIN = 3

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/(youtube-[a-z0-9-]+|_fixture_youtube\/[a-z0-9_-]+)$/.test(trabajo)) throw new Error('args.trabajo debe ser sesiones/youtube-<slug> (la última línea que imprime `python3 scripts/youtube.py preparar <serie>`).')
const DESDE = String(A.desde || '')
if (!['', 'retoque'].includes(DESDE)) throw new Error('args.desde: "retoque" (montaje.json ya existe + args.notas con lo que pidió el usuario) o nada.')
const RETOQUE = DESDE === 'retoque'
const notas = String(A.notas || '').trim()
if (RETOQUE && !notas) throw new Error('args.notas: en modo retoque, lo que pidió el usuario (quitar una unión, otra promesa, dejar la escena P3.e8…).')
const VUELTAS = RETOQUE ? 1 : VUELTAS_CRITICA

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

const S = {
  rechequeo: { type: 'object', required: ['items'], properties: { items: { type: 'array' } } },
  montaje: {
    type: 'object', required: ['archivo', 'gate', 'fallas', 'duracion_min', 'escenas', 'recortadas', 'revozadas', 'puentes', 'promesa'],
    properties: {
      archivo: { type: 'string', pattern: 'montaje\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, duracion_min: { type: 'number' }, escenas: { type: 'integer' },
      recortadas: { type: 'integer' }, revozadas: { type: 'integer' }, puentes: { type: 'integer' }, promesa: { type: 'boolean' },
    },
  },
  oyente: {
    type: 'object', required: ['archivo', 'de_que', 'promesa', 'confusiones', 'saltos', 'repeticiones', 'pregunta_sin_responder'],
    properties: {
      archivo: { type: 'string', pattern: 'oyente\\.json$' }, de_que: { type: 'string' },
      promesa: { type: 'object', required: ['me_prometio', 'me_dio'], properties: { me_prometio: { type: 'string' }, me_dio: { type: 'string' } } },
      confusiones: { type: 'array', items: { type: 'object', required: ['escena', 'cita_de_la_voz', 'que_no_entendi'],
        properties: { escena: { type: 'integer' }, cita_de_la_voz: { type: 'string' }, que_no_entendi: { type: 'string' } } } },
      saltos: { type: 'array', items: { type: 'object', required: ['de', 'a', 'por_que'], properties: { de: { type: 'integer' }, a: { type: 'integer' }, por_que: { type: 'string' } } } },
      repeticiones: { type: 'array', items: { type: 'string' } },
      pregunta_sin_responder: { type: 'array', items: { type: 'string' } },
    },
  },
  critica: {
    type: 'object', required: ['archivo', 'vuelta', 'veredicto', 'puntajes', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'critica\\.json$' }, vuelta: { type: 'integer' }, veredicto: { type: 'string', enum: ['pasa', 'corregir'] },
      puntajes: { type: 'object', required: PUNTAJES, properties: Object.fromEntries(PUNTAJES.map((k) => [k, { type: 'integer', minimum: 1, maximum: 5 }])) },
      faltas: { type: 'array', items: { type: 'object', required: ['escena', 'regla', 'gravedad', 'problema', 'arreglo'],
        properties: { n: { type: 'integer' }, escena: { type: ['integer', 'null'] }, regla: { type: 'string', enum: Object.values(REGLA_DE) },
          gravedad: { type: 'string', enum: ['bloquea', 'mejora'] }, problema: { type: 'string' }, arreglo: { type: 'string' },
          probado: { type: 'boolean' }, cambios: { type: 'array', items: { type: 'object' } } } } },
      oyente_descartadas: { type: 'array', items: { type: 'object', required: ['escena', 'motivo'], properties: { escena: { type: ['integer', 'null'] }, pregunta: { type: 'string' }, motivo: { type: 'string' } } } },
    },
  },
}

const rel = (p) => String(p || '').replace(/^\.\//, '').replace(/^.*?\/(?=sesiones\/)/, '')
const fallasDe = (r) => (r.fallas && r.fallas.length) ? r.fallas : ['el gate `youtube.py montaje --check` falló sin detalle: córrelo y copia sus líneas FALLA']

// ── 1. Montaje ───────────────────────────────────────────────────────────────
phase('Montaje')
const directivaEditor = `Eres el EDITOR DEL VIDEO LARGO (lee referencias/roles/youtube-editor.md). TRABAJO = ${trabajo}. ` +
  `Insumos: python3 scripts/youtube.py digesto ${trabajo} --para editor y ${trabajo}/montaje.borrador.json. ` +
  (RETOQUE ? `RETOQUE: ${trabajo}/montaje.json ya existe y está aprobado; aplica SOLO estas notas del usuario: «${notas}». `
    : `Escribe ${trabajo}/montaje.json desde el borrador: cada escena que repite un hecho de otra parte se quita o se recorta (sin_hechos) o, si la referencia atrás ayuda, va con reprise y razón (≤ ${REPRISE_MAX}); ` +
      `las presentaciones de personas y las glosas de siglas van UNA vez (un recordatorio de ≤ 4 palabras vale tras 5 min); los saltos de tiempo o de tema entre capítulos llevan un puente de 1–${PUENTE_ORACIONES} oraciones (≤ ${PUENTE_CARACTERES} caracteres c/u) que cuenta la historia y NUNCA anuncia; ` +
      `la promesa global tras el gancho de la parte 1 se paga en el último 40 %; títulos de capítulo; youtube {titulo, descripcion, hashtags}. Revozar solo como último recurso (≤ ${REVOZAR_MAX}). Duración ${DURACION_MIN / 60}–${DURACION_MAX / 60} min. `) +
  `Corre python3 scripts/youtube.py montaje ${trabajo} --check hasta 0 fallas y devuelve su línea RETORNO tal cual.`
const validarMontaje = (r) => [
  ...(rel(r.archivo) !== `${trabajo}/montaje.json` ? [`archivo debe ser ${trabajo}/montaje.json`] : []),
  ...(r.gate !== 'ok' ? fallasDe(r) : []),
  ...(!r.promesa ? ['falta la promesa global'] : []),
]
let MJ = await conReparacion('Montaje', (fallos) => agentRol(directivaEditor + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'youtube-editor', schema: S.montaje, phase: 'Montaje', label: 'editor' }), validarMontaje, 2)
log(`Montaje: ${MJ.duracion_min} min · ${MJ.escenas} escenas · ${MJ.recortadas} recortadas · ${MJ.revozadas} revozadas · ${MJ.puentes} puentes`)

// ── 2. Oyente ────────────────────────────────────────────────────────────────
const oir = (vuelta) => conReparacion(`oyente ${vuelta}`, (fallos) => agentRol(
  `Eres el OYENTE INGENUO en MODO LARGO (lee referencias/roles/historia-oyente.md, «Modo largo»). TRABAJO = ${trabajo}. ` +
    `Lee SOLO python3 scripts/youtube.py digesto ${trabajo} --para oyente: un video de YouTube de unos ${Math.round(MJ.duracion_min)} min, de corrido, una sola vez. ` +
    `Escribe ${trabajo}/oyente.json y devuelve lo mismo.` + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-oyente', schema: S.oyente, phase: 'Oyente', label: `oyente-${vuelta}` }),
(r) => [
  ...(rel(r.archivo) !== `${trabajo}/oyente.json` ? [`archivo debe ser ${trabajo}/oyente.json`] : []),
  ...(!r.de_que.trim() ? ['de_que: una oración'] : []),
], 1).catch((e) => { avisar(`AVISO: el oyente no terminó (${String(e.message).split('\n')[0]}); la crítica va sin oyente.json.`); return null })
phase('Oyente')
let O = await oir(1)
if (O) log(`Oyente: «${O.de_que}» · ${O.confusiones.length} confusiones · ${O.saltos.length} saltos · ${O.repeticiones.length} repeticiones`)

// ── 3. Crítica (≤ 2 vueltas; 1 en retoque; desde la 2, acotada) ───────────────
phase('Crítica')
const validarCritica = (r, O, acotada) => {
  const f = []
  for (const k of PUNTAJES) if (r.puntajes[k] <= 2 && !r.faltas.some((x) => x.gravedad === 'bloquea' && x.regla === REGLA_DE[k])) f.push(`puntaje ${k} = ${r.puntajes[k]} sin falta «bloquea» de ${REGLA_DE[k]}`)
  const bloquea = r.faltas.some((x) => x.gravedad === 'bloquea') || PUNTAJES.some((k) => r.puntajes[k] < PUNTAJE_MIN)
  if ((r.veredicto === 'pasa') === bloquea) f.push(`veredicto ${r.veredicto} incoherente con las faltas y los puntajes`)
  for (const x of r.faltas) if (x.gravedad === 'bloquea' && x.probado === false) f.push(`la falta ${x.n ?? ''} bloquea con un arreglo que el gate rechaza: ajústalo con youtube.py probar o dala como mejora`)
  for (const x of r.faltas) if (x.probado === true && !(x.cambios || []).length) f.push(`la falta ${x.n ?? ''} trae probado: true sin cambios: copia el JSON exacto que pasaste a youtube.py probar`)
  if (!acotada && O) {
    const atendida = (n) => r.faltas.some((x) => x.escena === n || new RegExp(`\\bE?${n}\\b`).test(`${x.problema} ${x.arreglo}`)) ||
      (r.oyente_descartadas || []).some((d) => d.escena === n)
    for (const c of O.confusiones) if (!atendida(c.escena)) f.push(`la confusión del oyente en E${c.escena} («${c.que_no_entendi}») no tiene falta ni entrada en oyente_descartadas`)
    for (const s of O.saltos) if (!atendida(s.a)) f.push(`el salto E${s.de}→E${s.a} del oyente no tiene falta ni entrada en oyente_descartadas`)
  }
  return f
}
let critica = null, previas = []
for (let vuelta = 1; vuelta <= VUELTAS + 1; vuelta++) {
  if (vuelta > 1) O = (await oir(vuelta)) || O
  const acotada = vuelta > 1 || RETOQUE
  critica = await conReparacion(`crítica ${vuelta}`, (fallos) => agentRol(
    `MODO LARGO (lee la sección «Modo largo» de referencias/roles/video-critico.md). TRABAJO = ${trabajo}. Vuelta ${vuelta}. ` +
      `Insumos: python3 scripts/youtube.py digesto ${trabajo} --para critico, python3 scripts/youtube.py resumen ${trabajo}` + (O ? ` y ${trabajo}/oyente.json (cada confusión y salto se resuelve con una falta bloquea de Y-C2 o se justifica en oyente_descartadas; sus repeticiones son tu primera lista para Y-C1)` : '') + '. ' +
      `La pregunta: ¿se oye como UN documental o como partes pegadas? Y-C3: un puente o la promesa que anuncia («en este capítulo», «ahora veremos», «te cuento») o resume lo visto bloquea. ` +
      (acotada ? `VUELTA ACOTADA: solo bloquea lo que cambió en la corrección, lo que la vuelta anterior dejó sin resolver o un puntaje ≤ 2; lo demás va como mejora. ` : '') +
      (RETOQUE ? `RETOQUE con notas del usuario: «${notas}»; lo que el usuario pidió no bloquea. ` : '') +
      `ARREGLOS PROBADOS: cada arreglo en el formato de cambios del montaje, probado con python3 scripts/youtube.py probar ${trabajo} --cambios '<json>' (exit 0, sin fallas nuevas); marca probado y copia en cambios el JSON que pasó. ` +
      `Escribe ${trabajo}/critica.json.` + (previas.length ? ` Faltas de la vuelta anterior (comprueba primero cada una): ${JSON.stringify(previas)}` : '') +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: `critica-${vuelta}` }), (r) => validarCritica(r, O, acotada), 2)
  log(`Crítica ${vuelta}: ${critica.veredicto} · ${PUNTAJES.map((k) => `${k} ${critica.puntajes[k]}`).join(' · ')}`)
  if (critica.veredicto === 'pasa' || vuelta > VUELTAS) break
  previas = critica.faltas.filter((x) => x.gravedad === 'bloquea')
  const cambios = previas.flatMap((x) => x.cambios || [])
  MJ = await conReparacion(`corrección ${vuelta}`, (fallos) => agentRol(directivaEditor +
    ` CORRECCIÓN ${vuelta}: montaje.json ya existe; corrige SOLO lo que bloquea: ${JSON.stringify(previas)}. ` +
    (cambios.length ? `Las que traen cambios se aplican TAL CUAL con UNA llamada: python3 scripts/youtube.py aplicar ${trabajo} --cambios '<archivo o json con ${JSON.stringify(cambios)}>'. ` : '') +
    `Las demás las redactas tú. Devuelve el RETORNO del gate.` + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'youtube-editor', schema: S.montaje, phase: 'Crítica', label: `editor-corrige-${vuelta}` }), validarMontaje, 1)
}

// ── 4. Cierre con arreglos probados: si la última crítica solo bloquea con arreglos que ya pasaron probar, se aplican ──
let aprobadoPor = critica.veredicto === 'pasa' ? 'critico' : null
const pendientes = critica.faltas.filter((x) => x.gravedad === 'bloquea')
if (critica.veredicto !== 'pasa' && pendientes.length && pendientes.every((x) => x.probado === true && (x.cambios || []).length) &&
    PUNTAJES.every((k) => critica.puntajes[k] > 2)) {
  const C = await conReparacion('cierre con arreglos probados', (fallos) => agentRol(directivaEditor +
    ` CIERRE CON ARREGLOS PROBADOS: aplícalos todos juntos y sin reescribirlos con UNA llamada a python3 scripts/youtube.py aplicar ${trabajo} --cambios con este JSON: ${JSON.stringify(pendientes.flatMap((x) => x.cambios))}. ` +
    `Si sale 1, NO lo arregles: devuelve gate: "falla" con sus líneas FALLA. Con exit 0, corre youtube.py montaje --check y devuelve el RETORNO.` + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'youtube-editor', schema: S.montaje, phase: 'Crítica', label: 'editor-cierre' }), validarMontaje, 0)
    .catch((e) => { avisar(`AVISO: los arreglos probados no pasaron el gate juntos (${String(e.message).split('\n')[0]}); queda «corregir».`); return null })
  if (C) {
    MJ = C
    aprobadoPor = 'arreglos_probados'
    critica = { ...critica, veredicto: 'pasa', faltas: critica.faltas.filter((x) => x.gravedad !== 'bloquea') }
  }
}

// ── 5. Mejoras probadas (m113): con «pasa», las mejoras que el crítico ya probó se aplican tal cual y el gate se repite;
//      si juntas no pasan, el montaje queda como estaba y vuelven como mejoras ──
let mejorasAplicadas = []
const probadas = critica.veredicto === 'pasa' ? critica.faltas.filter((x) => x.gravedad === 'mejora' && x.probado === true && (x.cambios || []).length) : []
if (probadas.length) {
  const C = await conReparacion('mejoras probadas', (fallos) => agentRol(directivaEditor +
    ` MEJORAS PROBADAS: el crítico aprobó el montaje y estas mejoras ya pasaron youtube.py probar. Aplícalas todas juntas y sin reescribirlas con UNA llamada a python3 scripts/youtube.py aplicar ${trabajo} --cambios con este JSON: ${JSON.stringify(probadas.flatMap((x) => x.cambios))}. ` +
    `Si sale 1, NO lo arregles (aplicar ya dejó el montaje como estaba): devuelve gate: "falla" con sus líneas FALLA. Con exit 0, corre youtube.py montaje --check y devuelve el RETORNO.` + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'youtube-editor', schema: S.montaje, phase: 'Crítica', label: 'editor-mejoras' }), validarMontaje, 0)
    .catch((e) => { avisar(`AVISO: las mejoras probadas no pasaron el gate juntas (${String(e.message).split('\n')[0]}); el montaje queda sin ellas.`); return null })
  if (C) {
    MJ = C
    mejorasAplicadas = probadas
    log(`Mejoras probadas aplicadas: ${probadas.length} · ${MJ.duracion_min} min`)
  }
}

return {
  veredicto: critica.veredicto === 'pasa' ? 'aprobar_montaje' : 'corregir',
  aprobado_por: aprobadoPor,
  montaje: MJ,
  puntajes: critica.puntajes,
  mejoras: critica.faltas.filter((x) => x.gravedad === 'mejora' && !mejorasAplicadas.includes(x)),
  mejoras_aplicadas: mejorasAplicadas,
  faltas_pendientes: critica.veredicto === 'pasa' ? [] : critica.faltas.filter((x) => x.gravedad === 'bloquea'),
  oyente: O ? { de_que: O.de_que, repeticiones: O.repeticiones, saltos: O.saltos.length, confusiones: O.confusiones.length } : null,
  avisos: AVISOS_WF,
}
