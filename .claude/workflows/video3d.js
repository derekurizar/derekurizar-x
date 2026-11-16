export const meta = {
  name: 'video3d',
  description: 'Guion de /video-3d: director (dirección visual por frase con el catálogo de la maqueta) → constructor por cada brief → ganchos 3D → selección → el usuario elige → guion y storyboard → crítico en modo 3D (≤ 2 pasadas) → 5 cierres. 0 créditos.',
  whenToUse: 'Tras `video3d.py preparar` (y la investigación). Se detiene con elegir_estilo (confianza baja; reanuda con args.estilo) y con elegir_gancho (reanuda con args.gancho); al final devuelve 5 cierres. args: {trabajo, tema, angulo, estilo, gancho, auto, fixture, permitir_fallback}. La voz y el render los hace la sesión.',
  phases: [
    { title: 'Dirección', detail: 'video3d-director: direccion.json con la idea visual, el criterio (lugar o mecanismo), la escala (pais, ciudad o esquema), el estilo con razón y confianza, el mundo, el borrador de la narración y el verbo visual del catálogo por frase; lo que el catálogo no tiene va en briefs[]' },
    { title: 'Constructor', detail: 'un maqueta-constructor por brief (≤ 3 a la vez): módulo + ficha, maqueta_modulo.py check (lint, pureza, hojas 9:16 y 4:5) y registrar; o reutiliza un tipo del catálogo' },
    { title: 'Ganchos', detail: 'el director en modo ganchos: 5 candidatos de familias 3D distintas (evento en el segundo cero), video3d.py ganchos --check --cuadros' },
    { title: 'Selección', detail: 'video-critico en modo selección (gancho 3D, con las hojas de cada candidato): ganador y segundo; luego el usuario elige (elegir_gancho)' },
    { title: 'Guion', detail: 'el director: ganchos --usar, narración de corrido, dirección por frase final, escenas con camara, eventos, marcas y cifras con anclas dice, caption; video3d.py guion --check (C3D, V2–V5, M3D) y storyboard; los briefs nuevos van al constructor UNA vez' },
    { title: 'Crítica', detail: 'video-critico en modo 3D (3C1–3C8): ¿cada movimiento cuenta lo que la voz dice?, ¿un esquema se lee como lugar real?, ¿lo que se mueve insinúa un dato sin verificar?; arreglos probados en una copia; ≤ 2 pasadas, el director corrige' },
    { title: 'Cierres', detail: 'el director escribe 5 cierres (c1 = el del guion) probados en una copia con guion --check; el usuario elige antes de la voz' },
  ],
}

// Guías: referencias/flujo-video3d.md, referencias/roles/video3d-director.md, referencias/roles/maqueta-constructor.md,
// referencias/roles/video-critico/3d.md. Los gates viven en scripts/video3d.py (C3D, G3D, V2–V5) y scripts/maqueta3d.py
// (M3D); el vocabulario de la maqueta (qué tipos existen) NO se lista aquí: lo leen los agentes con
// `maqueta3d.py catalogo` y lo valida el gate. ESCENAS_*, GANCHO_VOZ_S y DURACION_* son espejos de scripts/video3d.py (W15).
const ESCENAS_MIN = 4, ESCENAS_MAX = 9
const GANCHO_VOZ_S = 6.0
const DURACION_MIN_S = 20, DURACION_MAX_S = 180
const CANDIDATOS = 5, CIERRES_N = 5, BRIEFS_MAX = 3, CONSTRUCTORES_MAX = 3
const VUELTAS_CRITICA = 2, PUNTAJE_MIN = 3
const PUNTAJES = ['gancho', 'claridad', 'concordancia', 'ritmo', 'promesa', 'cierre']

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/(video3d-[a-z0-9-]+|_fixture_video3d\/[a-z0-9_-]+)$/.test(trabajo)) throw new Error('args.trabajo debe ser sesiones/video3d-<slug> (la última línea de `python3 scripts/video3d.py preparar`).')
const tema = String(A.tema || '').trim()
if (!tema) throw new Error('args.tema: el tema del video, tal como lo dio el usuario.')
const angulo = String(A.angulo || '').trim()
const ANGULO = angulo ? ` ÁNGULO Y PEDIDOS DEL USUARIO (mandan sobre tu criterio): «${angulo}».` : ''
const ELIGE_USUARIO = !(A.auto || !!A.fixture)   // regla de oro 11: el usuario elige estilo dudoso, gancho y cierre

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
  rechequeo: { type: 'object', properties: { items: { type: 'array' } } },   // lo pide el bloque común; aquí no se usa
  direccion: {
    type: 'object', required: ['archivo', 'idea_visual', 'criterio', 'escala', 'estilo', 'protagonista', 'frases', 'briefs'],
    properties: {
      archivo: { type: 'string', pattern: 'direccion\\.json$' }, idea_visual: { type: 'string' },
      criterio: { type: 'string', enum: ['lugar', 'mecanismo', 'ninguno'] }, escala: { type: 'string' },
      estilo: { type: 'object', required: ['id', 'razon', 'confianza'], properties: { id: { type: 'string' }, razon: { type: 'string' },
        confianza: { type: 'string', enum: ['alta', 'baja'] }, candidatos: { type: 'array', items: { type: 'string' } },
        cuadros: { type: 'array', items: { type: 'string' } } } },
      protagonista: { type: 'string' },
      frases: { type: 'array', items: { type: 'object', required: ['frase', 'verbo'], properties: { frase: { type: 'string' }, verbo: { type: 'string' }, que_se_ve: { type: 'string' }, brief: { type: ['string', 'null'] } } } },
      briefs: { type: 'array', items: { type: 'object', required: ['id', 'clase', 'escala', 'que_se_ve', 'frase'],
        properties: { id: { type: 'string' }, tipo_sugerido: { type: 'string' }, clase: { type: 'string', enum: ['pieza', 'evento', 'objeto'] }, escala: { type: 'string' },
          que_se_ve: { type: 'string' }, parametros: { type: 'string' }, frase: { type: 'string' } } } },
      nota: { type: 'string' },
    },
  },
  modulo: {
    type: 'object', required: ['tipo', 'clase', 'check', 'registrado', 'reutilizado'],
    properties: { tipo: { type: 'string', pattern: '^[a-z][a-z0-9_]*$' }, clase: { type: 'string' }, modulo: { type: 'string' },
      check: { type: 'string', enum: ['ok', 'falla'] }, registrado: { type: 'boolean' }, reutilizado: { type: 'boolean' },
      fallas: { type: 'array', items: { type: 'string' } }, vueltas: { type: 'integer' }, lecturas: { type: 'integer' },
      s_por_cuadro: { type: ['number', 'null'] }, ejemplo: { type: 'object' }, nucleo: { type: 'array', items: { type: 'string' } } },
  },
  ganchos: {
    type: 'object', required: ['archivo', 'gate', 'fallas', 'candidatos'],
    properties: { archivo: { type: 'string', pattern: 'ganchos\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } },
      candidatos: { type: 'array', items: { type: 'object', required: ['id', 'familia', 'titular', 'voz'],
        properties: { id: { type: 'string' }, familia: { type: 'string' }, titular: { type: 'string' }, voz: { type: 'string' }, evento: { type: 'string' } } } },
      hojas: { type: 'array', items: { type: 'string' } } },
  },
  seleccion: {
    type: 'object', required: ['archivo', 'ganador', 'segundo', 'puntajes', 'por_que', 'faltas'],
    properties: { archivo: { type: 'string', pattern: 'seleccion\\.json$' }, ganador: { type: ['string', 'null'] }, segundo: { type: ['string', 'null'] },
      puntajes: { type: 'object' }, por_que: { type: 'string' },
      faltas: { type: 'array', items: { type: 'object', required: ['candidato', 'regla', 'problema', 'arreglo'],
        properties: { candidato: { type: 'string' }, regla: { type: 'string' }, problema: { type: 'string' }, arreglo: { type: 'string' } } } } },
  },
  guion: {
    type: 'object', required: ['archivo', 'gate', 'fallas', 'escenas', 'estimado_s', 'briefs', 'tipos_usados'],
    properties: { archivo: { type: 'string', pattern: 'guion\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, escenas: { type: 'integer' }, estimado_s: { type: 'number' },
      tipos_usados: { type: 'array', items: { type: 'string' } }, storyboard: { type: 'string' },
      briefs: { type: 'array', items: { type: 'object' } }, aplicadas: { type: 'array', items: { type: 'integer' } } },
  },
  critica: {
    type: 'object', required: ['archivo', 'vuelta', 'veredicto', 'puntajes', 'faltas'],
    properties: { archivo: { type: 'string', pattern: 'critica\\.json$' }, vuelta: { type: 'integer' }, veredicto: { type: 'string', enum: ['pasa', 'corregir'] },
      puntajes: { type: 'object', required: PUNTAJES, properties: Object.fromEntries(PUNTAJES.map((k) => [k, { type: 'integer', minimum: 1, maximum: 5 }])) },
      faltas: { type: 'array', items: { type: 'object', required: ['regla', 'gravedad', 'que', 'arreglo'],
        properties: { escena: { type: ['integer', 'null'] }, regla: { type: 'string', pattern: '^(3C[1-9]|C1[0-2]|C[1-9])$' }, gravedad: { type: 'string', enum: ['bloquea', 'mejora'] },
          que: { type: 'string' }, arreglo: { type: 'string' }, probado: { type: 'boolean' } } } } },
  },
  cierres: {
    type: 'object', required: ['archivo', 'candidatos', 'elegibles'],
    properties: { archivo: { type: 'string', pattern: 'cierres\\.json$' },
      candidatos: { type: 'array', items: { type: 'object', required: ['id', 'forma', 'final'], properties: { id: { type: 'string' }, forma: { type: 'string' }, final: { type: 'string' } } } },
      elegibles: { type: 'array', items: { type: 'string' } },
      rechazadas: { type: 'array', items: { type: 'object', required: ['id', 'falla'], properties: { id: { type: 'string' }, falla: { type: 'string' } } } } },
  },
}

const rel = (p) => String(p || '').replace(/^\.\//, '').replace(/^.*?\/(?=sesiones\/)/, '')
const fallasDe = (r, gate) => (r.fallas && r.fallas.length) ? r.fallas : [`el gate \`${gate}\` falló sin detalle: córrelo y copia sus líneas FALLA`]
const archivoEs = (r, nombre) => rel(r.archivo) === `${trabajo}/${nombre}` ? [] : [`archivo debe ser ${trabajo}/${nombre}`]
const DIRECTOR = `Eres el DIRECTOR de /video-3d (lee referencias/roles/video3d-director.md y referencias/flujo-video3d.md). TRABAJO = ${trabajo} · tema: «${tema}».${ANGULO} ` +
  `Insumo: python3 scripts/video3d.py digesto ${trabajo} (trae el catálogo del vocabulario; nunca inventes un tipo: lo que falte va en briefs). `

// ── Constructor: un maqueta-constructor por brief, ≤ CONSTRUCTORES_MAX a la vez ─────────────────────────────────────
const construidos = []
async function construir(briefs, etapa) {
  const lista = (briefs || []).slice(0, BRIEFS_MAX)
  if ((briefs || []).length > BRIEFS_MAX) avisar(`AVISO: ${briefs.length} briefs; se construyen los primeros ${BRIEFS_MAX}.`)
  if (!lista.length) return []
  phase('Constructor')
  const hechos = []
  for (let i = 0; i < lista.length; i += CONSTRUCTORES_MAX) {
    const tanda = await Promise.all(lista.slice(i, i + CONSTRUCTORES_MAX).map((b) => agentRol(
      `Eres el CONSTRUCTOR de la maqueta 3D (lee referencias/roles/maqueta-constructor.md). BRIEF (${etapa}, para ${trabajo}): ${JSON.stringify(b)}. ` +
        'Mira primero si el catálogo ya lo tiene (python3 scripts/maqueta3d.py catalogo --para sesion --escala <escala>); si no, escribe el módulo y su ficha, deja python3 scripts/maqueta_modulo.py check <clase>/<tipo> en 0, mira UNA vez su hoja y regístralo con maqueta_modulo.py registrar. ' +
        'Retorno: {tipo, clase, modulo, check, registrado, reutilizado, fallas[], vueltas, lecturas, s_por_cuadro, ejemplo, nucleo[]}.',
      { agentType: 'maqueta-constructor', schema: S.modulo, phase: 'Constructor', label: `constructor-${b.id || i}` })
      .then((r) => ({ brief: b.id, ...r }))
      .catch((e) => { avisar(`AVISO: el constructor del brief ${b.id} no terminó (${String(e.message).split('\n')[0]}).`); return { brief: b.id, check: 'falla', registrado: false, reutilizado: false, fallas: ['no terminó'] } })))
    hechos.push(...tanda)
  }
  for (const r of hechos) {
    if (r.check !== 'ok' || !(r.registrado || r.reutilizado)) avisar(`AVISO: brief ${r.brief}: no quedó un tipo usable (${(r.fallas || []).join('; ') || r.check}); el director cuenta esa frase con lo que hay.`)
    if ((r.nucleo || []).length) avisar(`NÚCLEO (brief ${r.brief}, tipo ${r.tipo}): ${r.nucleo.join(' · ')} — cambio para quien mantiene motor.js / maqueta3d.py.`)
  }
  construidos.push(...hechos)
  return hechos
}
const resumenConstruidos = (hs) => hs.filter((r) => r.check === 'ok' && (r.registrado || r.reutilizado))
  .map((r) => `${r.brief} → tipo «${r.tipo}» (${r.clase}${r.reutilizado ? ', ya existía' : ', nuevo'}; ejemplo: ${JSON.stringify(r.ejemplo || {})})`).join('; ')

// ── 1. Dirección ─────────────────────────────────────────────────────────────
// (la directiva no depende de args.estilo ni de args.gancho: al reanudar con resumeFromRunId esta llamada sale de la caché)
phase('Dirección')
const validarDireccion = (r) => [
  ...archivoEs(r, 'direccion.json'),
  ...(r.criterio === 'ninguno' ? [] : (!r.frases.length ? ['frases: una entrada por oración del borrador (frase, verbo del catálogo, que_se_ve)'] : [])),
  ...(r.briefs.length > BRIEFS_MAX ? [`${r.briefs.length} briefs; van ≤ ${BRIEFS_MAX} (cuenta lo demás con lo que hay en el catálogo)`] : []),
  ...(r.estilo.confianza === 'baja' && (r.estilo.candidatos || []).length < 2 ? ['estilo con confianza baja: candidatos (2–3) y el mismo cuadro en cada uno (estilos/<id>/)'] : []),
]
const DIR = await conReparacion('Dirección', (fallos) => agentRol(DIRECTOR +
  `MODO DIRECCIÓN: escribe ${trabajo}/direccion.json (idea_visual, criterio lugar|mecanismo, escala, estilo {id, razon, confianza, candidatos}, protagonista, mundo, borrador de la narración, frases[] con el verbo visual del catálogo por oración, briefs[] ≤ ${BRIEFS_MAX}, no_afirmar). ` +
    'Si ni el lugar ni el mecanismo se entienden mejor viéndolos moverse, criterio "ninguno" y en nota el flujo que le toca. ' +
    'Retorno: {archivo, idea_visual, criterio, escala, estilo, protagonista, frases[], briefs[], nota}.' +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video3d-director', schema: S.direccion, phase: 'Dirección', label: 'direccion' }), validarDireccion, 2)
log(`Dirección: «${DIR.idea_visual}» · ${DIR.criterio} · escala ${DIR.escala} · estilo ${DIR.estilo.id} (${DIR.estilo.confianza}) · ${DIR.frases.length} frases · ${DIR.briefs.length} brief(s)`)
if (DIR.criterio === 'ninguno') {
  return { trabajo, tema, veredicto: 'no_es_3d', etapa: 'direccion', nota: DIR.nota || '', avisos: AVISOS_WF }
}

// ── 2. Constructor (lo que el catálogo no tiene) ─────────────────────────────
const H1 = await construir(DIR.briefs, 'dirección')

// ── Estilo dudoso: el usuario elige (la sesión muestra los cuadros y reanuda con args.estilo) ─────────────────────
const estilo = A.estilo || DIR.estilo.id
if (ELIGE_USUARIO && !A.estilo && DIR.estilo.confianza === 'baja') {
  avisar(`Estilo: confianza baja entre ${(DIR.estilo.candidatos || []).join(', ')} → el usuario elige (cuadros en ${trabajo}/estilos/)`)
  return { trabajo, veredicto: 'elegir_estilo', etapa: 'estilo', candidatos: DIR.estilo.candidatos, recomendado: DIR.estilo.id, razon: DIR.estilo.razon,
    cuadros: DIR.estilo.cuadros || [], construidos, avisos: AVISOS_WF }
}

// ── 3. Ganchos (los escribe el director: ganchos.json necesita su estilo, su mundo y eventos del catálogo) ──────
phase('Ganchos')
const invocarGanchos = (fallos, faltasSel) => agentRol(DIRECTOR +
  `MODO GANCHOS: escribe ${trabajo}/ganchos.json con el estilo «${estilo}» y lo de direccion.json, ${CANDIDATOS} candidatos de familias 3D distintas (evento en el segundo cero, voz ≤ ${GANCHO_VOZ_S} s con verbo, titular que se entiende sin sonido). ` +
    (H1.length ? `Tipos nuevos o confirmados por el constructor: ${resumenConstruidos(H1) || 'ninguno usable'}. ` : '') +
    `Corre python3 scripts/video3d.py ganchos ${trabajo} --check --cuadros hasta 0 fallas y mira UNA vez las hojas. ` +
    (faltasSel ? `EL CRÍTICO NO APROBÓ NINGUNO; rehaz los señalados: ${faltasSel.map((f) => `[${f.candidato} · ${f.regla}] ${f.problema} → ${f.arreglo}`).join(' · ')}. ` : '') +
    'Retorno: {archivo, gate, fallas[], candidatos[]{id, familia, titular, voz, evento}, hojas[]}.' +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video3d-director', schema: S.ganchos, phase: 'Ganchos', label: faltasSel ? 'ganchos-rehacer' : 'ganchos' })
const validarGanchos = (r) => r.gate !== 'ok' ? fallasDe(r, 'video3d.py ganchos --check') : [
  ...archivoEs(r, 'ganchos.json'),
  ...(r.candidatos.length !== CANDIDATOS ? [`${r.candidatos.length} candidatos; van ${CANDIDATOS} (el usuario elige)`] : []),
  ...(new Set(r.candidatos.map((c) => c.familia)).size < r.candidatos.length - 1 ? ['los candidatos son de familias distintas'] : []),
]
let K = await conReparacion('Ganchos', (f) => invocarGanchos(f, null), validarGanchos, 2)
log(`Ganchos: ${K.candidatos.map((c) => `${c.id} ${c.familia} «${c.titular}»`).join(' · ')}`)

// ── 4. Selección ─────────────────────────────────────────────────────────────
phase('Selección')
const seleccionar = (vuelta) => conReparacion('Selección', (fallos) => agentRol(
  `MODO SELECCIÓN DE UN GANCHO 3D (${guia('video-critico', 'seleccion', '3d')}: de 3d.md, «Selección del gancho 3D»). TRABAJO = ${trabajo} · vuelta ${vuelta}.${ANGULO} ` +
    `Lee ${trabajo}/ganchos.json (la escena 1 de cada candidato), mira UNA vez la hoja de cada uno en ${trabajo}/ganchos/<id>/ y el digesto (python3 scripts/video3d.py digesto ${trabajo}: rotación y rendimiento real). ` +
    `Primero en silencio (el cuadro cero y el titular), luego con la voz; puntúa silencio, tension, alineacion, honestidad y novedad; ganador (ninguno ≤ 2) y segundo de otra familia, o ganador null con faltas. Escribe ${trabajo}/seleccion.json.` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video-critico', schema: S.seleccion, phase: 'Selección', label: `seleccion-${vuelta}` }),
(r) => {
  const ids = K.candidatos.map((c) => c.id)
  return [...(r.ganador !== null && !ids.includes(r.ganador) ? [`ganador «${r.ganador}» no es un candidato`] : []),
    ...(r.ganador !== null && r.segundo !== null && (r.segundo === r.ganador || !ids.includes(r.segundo)) ? ['segundo debe ser otro candidato'] : []),
    ...(r.ganador === null && !r.faltas.length ? ['sin ganador: escribe las faltas con su arreglo'] : [])]
}, 1)
let SEL = await seleccionar(1)
if (SEL.ganador === null) {
  K = await conReparacion('Ganchos (rehacer)', (f, i) => invocarGanchos(f, i === 0 ? SEL.faltas : null), validarGanchos, 1)
  SEL = await seleccionar(2)
}
if (SEL.ganador === null) return { trabajo, tema, veredicto: 'corregir', etapa: 'seleccion', faltas_pendientes: SEL.faltas, ganchos: K.candidatos, avisos: AVISOS_WF }
if (ELIGE_USUARIO && !A.gancho) {
  avisar(`Ganchos: el usuario elige entre ${K.candidatos.length} (recomendado ${SEL.ganador}, segundo ${SEL.segundo || '—'}); hojas en ${trabajo}/ganchos/<id>/`)
  return { trabajo, veredicto: 'elegir_gancho', etapa: 'gancho', estilo, candidatos: K.candidatos, recomendado: SEL.ganador, segundo: SEL.segundo, por_que: SEL.por_que, construidos, avisos: AVISOS_WF }
}
const gancho = A.gancho || SEL.ganador
if (!K.candidatos.some((c) => c.id === gancho)) fail(`args.gancho «${gancho}» no es un candidato de ganchos.json (${K.candidatos.map((c) => c.id).join(', ')}).`)
const elegidoPor = A.gancho ? 'usuario' : 'critico'

// ── 5. Guion (+ storyboard; los briefs nuevos van al constructor UNA vez) ───────────────────────────────────────
phase('Guion')
const validarGuion = (r) => r.gate !== 'ok' ? fallasDe(r, 'video3d.py guion --check') : [
  ...archivoEs(r, 'guion.json'),
  ...(r.escenas < ESCENAS_MIN || r.escenas > ESCENAS_MAX ? [`${r.escenas} escenas; van ${ESCENAS_MIN}–${ESCENAS_MAX}`] : []),
  ...(r.estimado_s > DURACION_MAX_S * 1.2 ? [`estimado ${r.estimado_s} s: el tope es ${DURACION_MAX_S} s`] : []),
  ...(!r.storyboard ? ['corre python3 scripts/video3d.py storyboard y devuelve la ruta de la hoja'] : []),
]
const directivaGuion = (extra) => DIRECTOR +
  `MODO GUION: el gancho es «${gancho}» (python3 scripts/video3d.py ganchos ${trabajo} --usar ${gancho} --por ${elegidoPor}); estilo «${estilo}». ` +
  `Escribe PRIMERO la narración de corrido (guion.narracion), actualiza direccion.json → frases con ella y DESPUÉS repártela sin cambiar una palabra en ${ESCENAS_MIN}–${ESCENAS_MAX} escenas con camara, eventos, marcas y cifras con anclas dice, el cierre y el caption. ` +
  `Corre python3 scripts/video3d.py guion ${trabajo} --check hasta 0 fallas, luego python3 scripts/video3d.py storyboard ${trabajo} y mira UNA vez la hoja. ` +
  (construidos.length ? `Tipos del constructor: ${resumenConstruidos(construidos) || 'ninguno usable'}. ` : '') +
  `Si aparece algo que el catálogo no tiene, cuéntalo con lo que hay y devuélvelo en briefs (≤ ${BRIEFS_MAX}). ` + (extra || '') +
  'Retorno: {archivo, gate, fallas[], escenas, estimado_s, tipos_usados[] (los tipos del catálogo que usa), storyboard (ruta de la hoja), briefs[], aplicadas[]}.'
let G = await conReparacion('Guion', (fallos) => agentRol(directivaGuion(fallos.length ? `REPARACIÓN: ${fallos.join('; ')}. ` : ''),
  { agentType: 'video3d-director', schema: S.guion, phase: 'Guion', label: 'guion' }), validarGuion, 2)
if (G.briefs.length) {
  const H2 = await construir(G.briefs, 'guion')
  if (resumenConstruidos(H2)) {
    G = await conReparacion('Guion (con lo construido)', (fallos) => agentRol(directivaGuion(`El constructor registró lo que pediste: usa esos tipos en las frases de sus briefs (no pidas más). ${fallos.length ? `REPARACIÓN: ${fallos.join('; ')}. ` : ''}`),
      { agentType: 'video3d-director', schema: S.guion, phase: 'Guion', label: 'guion-construido' }), validarGuion, 1)
  }
}
log(`Guion: ${G.escenas} escenas · ≈ ${G.estimado_s} s · tipos ${G.tipos_usados.join(', ')}`)

// ── 6. Crítica en modo 3D (≤ 2 pasadas) ──────────────────────────────────────
phase('Crítica')
let critica = null
for (let vuelta = 1; vuelta <= VUELTAS_CRITICA; vuelta++) {
  critica = await conReparacion('Crítica', (fallos) => agentRol(
    `MODO 3D (${guia('video-critico', '3d')}). TRABAJO = ${trabajo} · vuelta ${vuelta}${vuelta > 1 ? ' (ACOTADA: solo bloquea lo que cambió o lo que la vuelta anterior dejó pendiente)' : ''}. ` +
      `Insumos: ${trabajo}/guion.json, ${trabajo}/locucion.json, ${trabajo}/direccion.json (frases: el verbo visual de cada oración) y UNA lectura de ${G.storyboard}. No critiques lo que eligió el usuario (gancho, estilo, duración). ` +
      `Cada arreglo, probado en una copia del TRABAJO con python3 scripts/video3d.py guion <copia> --check (probado: true/false). Escribe ${trabajo}/critica.json.` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: `critica-${vuelta}` }),
  (r) => {
    const f = []
    const bloquea = r.faltas.some((x) => x.gravedad === 'bloquea') || PUNTAJES.some((k) => r.puntajes[k] < PUNTAJE_MIN)
    if ((r.veredicto === 'pasa') === bloquea) f.push(`veredicto ${r.veredicto} incoherente con las faltas y los puntajes`)
    for (const x of r.faltas) if (x.gravedad === 'bloquea' && x.probado === false) f.push(`la falta de la escena ${x.escena} bloquea con un arreglo que el gate rechaza: ajústalo hasta que pase o dala como mejora`)
    return f
  }, 1)
  log(`Crítica ${vuelta}: ${critica.veredicto} · ${PUNTAJES.map((k) => `${k} ${critica.puntajes[k]}`).join(' · ')}`)
  if (critica.veredicto === 'pasa' || vuelta === VUELTAS_CRITICA) break
  const bloquean = critica.faltas.filter((x) => x.gravedad === 'bloquea')
  G = await conReparacion('Corrección', (fallos) => agentRol(DIRECTOR +
    `MODO CORRECCIÓN: aplica SOLO estas faltas del crítico (los arreglos probados, tal cual), sin tocar el gancho: ${JSON.stringify(bloquean)}. ` +
    `Deja python3 scripts/video3d.py guion ${trabajo} --check en 0 y rehaz python3 scripts/video3d.py storyboard ${trabajo}. ` +
    'Retorno: {archivo, gate, fallas[], escenas, estimado_s, tipos_usados[], storyboard, briefs[] (vacío), aplicadas[] (escenas cambiadas)}.' +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video3d-director', schema: S.guion, phase: 'Crítica', label: `correccion-${vuelta}` }), validarGuion, 1)
}
if (critica.veredicto !== 'pasa') {
  return { trabajo, tema, veredicto: 'corregir', etapa: 'critica', puntajes: critica.puntajes, faltas_pendientes: critica.faltas.filter((x) => x.gravedad === 'bloquea'),
    gancho, estilo, construidos, avisos: AVISOS_WF }
}

// ── 7. Cierres: 5 opciones para el usuario (regla de oro 11) ─────────────────
phase('Cierres')
let CIERRES = null
if (ELIGE_USUARIO) {
  CIERRES = await conReparacion('Cierres', (fallos) => agentRol(DIRECTOR +
    `MODO CIERRES: el guion está aprobado; NO cambies guion.json. Escribe ${trabajo}/cierres.json con ${CIERRES_N} cierres (c1 = el del guion tal cual; formas distintas de referencias/cierres.md) y prueba cada uno puesto en una copia con video3d.py guion --check (como dice tu guía); reescribe los que fallen. ` +
      'Retorno: {archivo, candidatos[]{id, forma, final}, elegibles[] (los que pasan), rechazadas[]{id, falla}}.' +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video3d-director', schema: S.cierres, phase: 'Cierres', label: 'cierres' }),
  (r) => [...archivoEs(r, 'cierres.json'), ...(r.candidatos.length !== CIERRES_N ? [`${r.candidatos.length} cierres; van ${CIERRES_N}`] : []),
    ...(r.elegibles.length < CIERRES_N ? [`solo ${r.elegibles.length} elegibles: reescribe ${(r.rechazadas || []).map((x) => x.id).join(', ')}`] : [])], 1)
    .catch((e) => { avisar(`AVISO: cierres incompletos (${String(e.message).split('\n')[0]}): ofrece el del guion y que el usuario dicte el suyo.`); return null })
}

return {
  trabajo, tema, veredicto: CIERRES ? 'elegir_cierre' : 'aprobado', etapa: 'cierres', gancho, gancho_elegido_por: elegidoPor, estilo,
  idea_visual: DIR.idea_visual, escala: DIR.escala, puntajes: critica.puntajes,
  mejoras: critica.faltas.filter((x) => x.gravedad === 'mejora'),
  storyboard: G.storyboard, tipos_usados: G.tipos_usados,
  cierres: CIERRES ? CIERRES.candidatos.filter((c) => CIERRES.elegibles.includes(c.id)) : null,
  construidos, avisos: AVISOS_WF,
}
