export const meta = {
  name: 'plano',
  description: 'El paso «Plano» de la mesa de archivo vertical: el video-realizador escribe plano.json (qué pieza entra con cada oración) y deja `plano --check` en 0.',
  whenToUse: 'Tras `<flujo>.py tiempos` con la voz real y antes de `grabar`, en todo video con "realizacion": "mesa". args: {trabajo, notas, sin_juez, permitir_fallback}. Devuelve plano_listo o plano_pendiente + fallas, y juez (lo que unos ojos frescos vieron en la hoja de golpes).',
  phases: [
    { title: 'Plano', detail: 'video-realizador: plano.json desde el digesto (video.py plano --digesto): el cuadro 0 con sujeto, una pieza por oración con su `dice`, mesas con `titulo`, los tableros solos, la jerarquía de personas con sus alegatos atribuidos; baja los recursos que falten; gate video.py plano --check --hoja (MV1–MV14) y su RETORNO; ≤ 2 reparaciones' },
    { title: 'Juez', detail: 'historia-oyente en modo plano (sonnet): lee SOLO plano.md, la hoja de golpes, como quien ve el video por primera vez, y anota dónde la pantalla adelanta, contradice o no acompaña a la voz; lo que bloquea vuelve al realizador UNA vez (m183). args.sin_juez lo salta' },
  ],
}

// Guías: referencias/flujo-mesa.md y referencias/roles/video-realizador.md. Los gates viven en scripts/video_hf.py (MV1–MV14,
// sobre los datos: nunca sobre píxeles) y scripts/mesa.py.

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/[a-z0-9_-]+(\/[a-z0-9_-]+){0,2}$/.test(trabajo)) throw new Error('args.trabajo debe ser el TRABAJO del video (sesiones/<slug> o sesiones/<serie>/parte-N), ya con su voz y sus tiempos.')
const notas = String(A.notas || '').trim()

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

// Guías por modo (2026-11-14): el rol lee su núcleo (referencias/roles/<rol>.md) y SOLO los archivos de su modo
// (referencias/roles/<rol>/<modo>.md). Antes leía la guía entera, con todos los modos, en cada pasada.
const guia = (rol, ...modos) =>
  `lee referencias/roles/${rol}.md (el núcleo) y, de referencias/roles/${rol}/, SOLO ${modos.map((m) => m + '.md').join(' y ')}`

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
  plano: {
    type: 'object', required: ['archivo', 'gate', 'fallas', 'piezas', 'recursos'],
    properties: { archivo: { type: 'string', pattern: 'plano\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, piezas: { type: 'integer' }, archivo_real: { type: 'integer' },
      recursos: { type: 'array', items: { type: 'string' } }, nota: { type: 'string' } },
  },
  juez: {
    type: 'object', required: ['archivo', 'entendi', 'desajustes'],
    properties: { archivo: { type: 'string', pattern: 'juez_plano\\.json$' }, entendi: { type: 'string' },
      desajustes: { type: 'array', items: { type: 'object', required: ['tiempo', 'dice', 'clase', 'gravedad', 'problema'],
        properties: { tiempo: { type: 'string' }, dice: { type: 'string' }, pieza: { type: 'string' },
          clase: { type: 'string', enum: ['adelanta', 'contradice', 'ajena', 'vacio', 'repite', 'cortada', 'golpe'] },
          gravedad: { type: 'string', enum: ['bloquea', 'mejora'] }, problema: { type: 'string' } } } } },
  },
}
const rel = (p) => String(p || '').replace(/^\.\//, '').replace(/^.*?\/(?=sesiones\/)/, '')

phase('Plano')
const directiva = (fallos) => `Eres el REALIZADOR del video vertical (lee referencias/roles/video-realizador.md y referencias/flujo-mesa.md). TRABAJO = ${trabajo}. ` +
  `Insumo: python3 scripts/video.py plano ${trabajo} --digesto. ` +
  (notas
    ? `RETOQUE: ${trabajo}/plano.json ya existe y el usuario pidió esto: ${notas}. Cambia solo lo que piden esas notas y lo que el gate exija por ellas. `
    : `Escribe ${trabajo}/plano.json (si ya existe, consérvalo y arregla solo lo que el gate marque). `) +
  `Corre python3 scripts/video.py plano ${trabajo} --check --hoja hasta que no quede ninguna falla. No edites código ni cambies el guion ni la voz. ` +
  `Devuelve el RETORNO del gate, recursos (los ids que bajaste) y nota.` +
  (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : '')
let r = await conReparacion('plano', (fallos) => agentRol(directiva(fallos),
  { agentType: 'video-realizador', schema: S.plano, phase: 'Plano', label: 'plano' }),
(x) => [...(rel(x.archivo) !== `${trabajo}/plano.json` ? [`archivo debe ser ${trabajo}/plano.json`] : []), ...(x.gate !== 'ok' ? (x.fallas.length ? x.fallas : ['el gate falló sin detalle: corre video.py plano --check y copia sus líneas FALLA']) : [])], 2)
  .catch((e) => { avisar(`AVISO: el plano no dejó el gate en 0 (${String(e.message).split('\n')[0]})`); return null })

// ── Juez del plano (m183): el oyente y el crítico juzgaron el guion ANTES de la voz, con la pantalla de las escenas;
// el dibujo final es este plano y nadie lo había visto con ojos frescos. Un oyente (sonnet) lee la hoja de golpes y lo
// que bloquea (la pantalla adelanta, contradice o no tiene que ver con la voz) vuelve al realizador UNA sola vez. ──
const validarPlano = (x) => [...(rel(x.archivo) !== `${trabajo}/plano.json` ? [`archivo debe ser ${trabajo}/plano.json`] : []), ...(x.gate !== 'ok' ? (x.fallas.length ? x.fallas : ['el gate falló sin detalle: corre video.py plano --check y copia sus líneas FALLA']) : [])]
let juez = null, corregidos = []
if (r && r.gate === 'ok' && !A.sin_juez) {
  phase('Juez')
  juez = await agentRol(
    `Eres el OYENTE INGENUO en MODO PLANO, el juez del plano (${guia('historia-oyente', 'plano')}). TRABAJO = ${trabajo}. ` +
      `Lee SOLO ${trabajo}/plano.md (la hoja de golpes: por oración de la voz, el golpe de arriba y lo que entra en pantalla). ` +
      `Anota los desajustes (adelanta, contradice, ajena: bloquean; vacio, repite, cortada, golpe: mejora) con la fila, la frase literal y la pieza; si no hay, lista vacía. ` +
      `Escribe ${trabajo}/juez_plano.json. Retorno: {archivo, entendi, desajustes[]{tiempo, dice, pieza, clase, gravedad, problema}}.`,
    { agentType: 'historia-oyente', schema: S.juez, phase: 'Juez', label: 'juez-plano' })
    .catch((e) => { avisar(`AVISO: el juez del plano no terminó (${String(e.message).split('\n')[0]}); el plano queda como lo dejó el gate.`); return null })
  const bloquean = juez ? juez.desajustes.filter((x) => x.gravedad === 'bloquea') : []
  if (juez) log(`Juez del plano: ${bloquean.length} desajuste(s) que bloquean · ${juez.desajustes.length - bloquean.length} mejora(s)`)
  if (bloquean.length) {
    const r2 = await conReparacion('plano (juez)', (fallos) => agentRol(directiva(fallos) +
      ` JUEZ DEL PLANO: un espectador que solo vio la hoja de golpes encontró esto; corrige SOLO estas filas en ${trabajo}/plano.json (otra pieza, otro golpe de arriba o mover la pieza a la oración que la nombra), sin tocar el resto, y deja el gate en 0: ${JSON.stringify(bloquean)}.`,
    { agentType: 'video-realizador', schema: S.plano, phase: 'Juez', label: 'plano-corrige' }), validarPlano, 1)
      .catch((e) => { avisar(`AVISO: el realizador no dejó el gate en 0 tras el juez (${String(e.message).split('\n')[0]}): revisa ${trabajo}/juez_plano.json y relanza con args.notas.`); return null })
    if (r2) { r = r2; corregidos = bloquean.map((x) => x.tiempo) }
  }
}

return {
  juez: juez ? { archivo: `${trabajo}/juez_plano.json`, entendi: juez.entendi, desajustes: juez.desajustes, corregidos } : null,
  veredicto: r && r.gate === 'ok' ? 'plano_listo' : 'plano_pendiente',
  archivo: `${trabajo}/plano.json`,
  hoja: `${trabajo}/plano.md`,
  piezas: r ? r.piezas : null,
  archivo_real: r ? r.archivo_real : null,
  recursos: r ? (r.recursos || []) : [],
  nota: r ? (r.nota || '') : '',
  fallas: r ? r.fallas : ['el realizador no terminó: corre python3 scripts/video.py plano <TRABAJO> --check'],
  avisos: AVISOS_WF,
}
