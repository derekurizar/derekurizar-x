export const meta = {
  name: 'video3d',
  description: 'Guion de /video-3d: director (dirección visual por frase con el catálogo de la maqueta) → constructor por cada brief → ganchos 3D → selección → el usuario elige → guion y storyboard → crítico en modo 3D (≤ 2 pasadas) → 5 cierres. 0 créditos.',
  whenToUse: 'Tras `video3d.py preparar` (y la investigación). Se detiene con elegir_estilo (confianza baja; reanuda con args.estilo) y con elegir_gancho (reanuda con args.gancho); al final devuelve 5 cierres. args: {trabajo, tema, angulo, estilo, gancho, auto, fixture, sin_referencia, desde, notas, mundos, correcciones, permitir_fallback}. desde: "retoque_visual" + notas = la voz ya existe: cambia solo lo que se ve, aplica lo que el crítico vio (y args.correcciones) y devuelve retoque_listo. La voz y el render los hace la sesión.',
  phases: [
    { title: 'Dirección', detail: 'video3d-director: direccion.json con la idea visual, el criterio (lugar o mecanismo), los mundos que la historia necesite (cada uno con su escala: pais, ciudad o esquema; tantos como haga falta, y se puede volver a uno), el estilo con razón y confianza, el borrador de la narración y el verbo visual del catálogo por frase; lo que el catálogo no tiene va en briefs[]' },
    { title: 'Referencia visual', detail: 'un historia-verificador por mundo de cerca (≤ 3 a la vez): cómo se ve ese lugar en la realidad, qué pasa ahí, con qué, y qué no se puede afirmar → verificacion_visual_<mundo>.json (los hechos que sostienen cada escena, C3D15)' },
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
const CANDIDATOS = 5, CIERRES_N = 5, BRIEFS_MAX = 12, BRIEFS_POR_MUNDO = 3, CONSTRUCTORES_MAX = 3   // encargos al constructor: ≤ 3 por mundo, ≤ 12 por video, 3 a la vez
const BRIEFS_CORRECCION = 2   // lo que la corrección de un retoque puede pedir al constructor
const TANDA_MUNDOS = 3, TANDA_DESDE = 5   // retoque: con 5 o más mundos de cerca, el director trabaja de 3 en 3 (una pasada con 7 llegó a 325 K de contexto)
const ESCENAS_TOPE = Math.max(ESCENAS_MAX, Math.floor(DURACION_MAX_S / 7))   // un video largo lleva las que necesite (video3d.py: SEG_POR_ESCENA)
const VERIFICADORES_MAX = 3, PUNTAJE_ESCENA_MIN = 3
const PUNTAJES_ESCENA = ['detalle', 'vida', 'realismo', 'claridad']
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
    type: 'object', required: ['archivo', 'idea_visual', 'criterio', 'mundos', 'estilo', 'protagonista', 'frases', 'briefs'],
    properties: {
      archivo: { type: 'string', pattern: 'direccion\\.json$' }, idea_visual: { type: 'string' },
      criterio: { type: 'string', enum: ['lugar', 'mecanismo', 'ninguno'] },
      mundos: { type: 'array', items: { type: 'object', required: ['id', 'escala'], properties: { id: { type: 'string' }, escala: { type: 'string' }, para: { type: 'string' } } } },
      estilo: { type: 'object', required: ['id', 'razon', 'confianza'], properties: { id: { type: 'string' }, razon: { type: 'string' },
        confianza: { type: 'string', enum: ['alta', 'baja'] }, candidatos: { type: 'array', items: { type: 'string' } },
        cuadros: { type: 'array', items: { type: 'string' } } } },
      protagonista: { type: 'string' },
      frases: { type: 'array', items: { type: 'object', required: ['frase', 'verbo'], properties: { frase: { type: 'string' }, mundo: { type: 'string' }, verbo: { type: 'string' }, que_se_ve: { type: 'string' }, brief: { type: ['string', 'null'] } } } },
      briefs: { type: 'array', items: { type: 'object', required: ['id', 'clase', 'escala', 'que_se_ve', 'frase'],
        properties: { id: { type: 'string' }, mundo: { type: 'string' }, tipo_sugerido: { type: 'string' }, clase: { type: 'string', enum: ['pieza', 'evento', 'objeto'] }, escala: { type: 'string' },
          que_se_ve: { type: 'string' }, parametros: { type: 'string' }, frase: { type: 'string' } } } },
      nota: { type: 'string' },
    },
  },
  referencia: {
    type: 'object', required: ['archivo', 'mundo', 'se_puede_dibujar', 'no_afirmar'],
    properties: { archivo: { type: 'string', pattern: 'verificacion_visual_[a-z0-9_-]+\\.json$' }, mundo: { type: 'string' },
      se_puede_dibujar: { type: 'array', items: { type: 'object', required: ['que', 'hecho'], properties: { que: { type: 'string' }, hecho: { type: 'string' }, estado: { type: 'string' } } } },
      no_afirmar: { type: 'array', items: { type: 'string' } }, nota: { type: 'string' } },
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
      escenas: { type: 'array', items: { type: 'object', required: ['mundo', ...PUNTAJES_ESCENA],
        properties: { mundo: { type: 'string' }, ...Object.fromEntries(PUNTAJES_ESCENA.map((k) => [k, { type: 'integer', minimum: 1, maximum: 5 }])), que_falta: { type: 'string' } } } },
      faltas: { type: 'array', items: { type: 'object', required: ['regla', 'gravedad', 'que', 'arreglo'],
        properties: { escena: { type: ['integer', 'null'] }, regla: { type: 'string', pattern: '^(3C1[01]|3C[1-9]|C1[0-2]|C[1-9])$' }, gravedad: { type: 'string', enum: ['bloquea', 'mejora'] },
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
  const porMundo = {}
  const lista = (briefs || []).filter((b) => { const k = b.mundo || '(sin mundo)'; porMundo[k] = (porMundo[k] || 0) + 1; return porMundo[k] <= BRIEFS_POR_MUNDO }).slice(0, BRIEFS_MAX)
  if ((briefs || []).length > lista.length) avisar(`AVISO: ${briefs.length} briefs; se construyen ${lista.length} (≤ ${BRIEFS_POR_MUNDO} por mundo, ≤ ${BRIEFS_MAX} por video).`)
  if (!lista.length) return []
  phase('Constructor')
  const hechos = []
  for (let i = 0; i < lista.length; i += CONSTRUCTORES_MAX) {
    const tanda = await Promise.all(lista.slice(i, i + CONSTRUCTORES_MAX).map((b) => agentRol(
      `Eres el CONSTRUCTOR de la maqueta 3D (lee referencias/roles/maqueta-constructor.md, con su VARA DE CALIDAD: un lugar completo antes que un objeto suelto, con vida, de día y de noche). BRIEF (${etapa}, para ${trabajo}): ${JSON.stringify(b)}. ` +
        (REFERENCIA_TXT ? `Lo que la referencia visual verificó de ese lugar (dibuja solo eso; lo demás es genérico): ${REFERENCIA_TXT} ` : '') +
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

// ── La referencia visual: cómo es cada lugar de cerca en la realidad (lo que se dibuja también se afirma) ─────────────
// Un historia-verificador por mundo de cerca (≤ VERIFICADORES_MAX a la vez), con la misma plantilla → {refs, txt}.
const referenciar = async (cerca, deDonde) => {
  const refs = []
  for (let i = 0; i < cerca.length; i += VERIFICADORES_MAX) {
    const tanda = await Promise.all(cerca.slice(i, i + VERIFICADORES_MAX).map((m) => agentRol(
      `Eres el verificador de la REFERENCIA VISUAL de un mundo de /video-3d (lee referencias/roles/historia-verificador.md para el método: cita literal guardada con python3 scripts/historia.py leer <url>, cuatro veredictos; sin fotos). TRABAJO = ${trabajo} · tema: «${tema}» · mundo «${m.id}» (${m.escala}): ${m.para || ''}. ` +
        `No hay encuadre.json: no corras historia.py digesto. ${deDonde} y los verificacion_*.json que ya existan (no repitas lo verificado). ` +
        'En un video 3D lo que se dibuja también se afirma. Verifica, con fuente primaria u oficial antes que prensa (≤ 8 búsquedas, ≤ 10 lecturas): 1) CÓMO SE VE ese lugar en la realidad (el entorno, las construcciones, los materiales); 2) QUÉ PASA ahí y en qué orden (el proceso); 3) QUIÉN lo hace y CON QUÉ (herramientas, máquinas, vehículos); 4) A QUÉ HORA o en qué época pasa, si importa; 5) lo que NO se puede afirmar (lo que ninguna fuente sostiene: va a no_afirmar y se dibuja genérico o no se dibuja). ' +
        `Escribe ${trabajo}/verificacion_visual_${m.id}.json {eje: "visual-${m.id}", hechos[] (ids visual-${m.id}-hNN, con estado confirmado|una_fuente|en_disputa|no_confirmado, fuentes[{url, medio, archivo, cita, fecha}] y nota), cifras[], fotos: [], videos: [], huecos[], no_afirmar[]}. Si historia.py hechos --check falla solo por fotos o por dominios sin clasificar, dilo y sigue. ` +
        'Retorno: {archivo, mundo, se_puede_dibujar[]{que, hecho (id), estado}, no_afirmar[], nota}.',
      { agentType: 'historia-verificador', schema: S.referencia, phase: 'Referencia visual', label: `referencia-${m.id}` })
      .catch((e) => { avisar(`AVISO: la referencia visual del mundo ${m.id} no terminó (${String(e.message).split('\n')[0]}): ese mundo se dibuja genérico (escena.ilustrativa) o con lo ya verificado.`); return null })))
    refs.push(...tanda.filter(Boolean))
  }
  const linea = (r) => `[${r.mundo}] se puede dibujar: ${r.se_puede_dibujar.map((x) => `${x.que} (${x.hecho})`).join('; ') || 'nada verificado'} · no afirmar: ${(r.no_afirmar || []).join('; ') || '—'}`
  return { refs, txt: refs.map(linea).join(' ‖ '), por: Object.fromEntries(refs.map((r) => [r.mundo, linea(r)])) }
}

// ── RETOQUE VISUAL (args.desde: "retoque_visual" + args.notas): la voz ya existe y NO se toca; cambia solo lo que se ve ──
// El director rehace mundos, cámaras, eventos y marcas con las notas del usuario → (constructor) → guion --check + tiempos
// (la voz real) + storyboard + hojas de escenas → el crítico revisa las escenas. Devuelve `retoque_listo` o `corregir`.
if (A.desde === 'retoque_visual') {
  const notas = String(A.notas || '').trim()
  if (!notas) fail('args.notas: qué quiere el usuario que cambie en lo que se ve.')
  // args.mundos [{id, escala, para}]: los lugares de cerca que el video tiene o va a tener (la sesión los lee del guion y
  // de las notas); cada uno pasa por la referencia visual antes de que el director toque nada
  let REFERENCIA_TXT = '', REFERENCIA_POR = {}
  const cercaR = (Array.isArray(A.mundos) ? A.mundos : []).filter((m) => m && m.id && m.escala !== 'pais')
  if (cercaR.length && !A.sin_referencia && !A.fixture) {
    phase('Referencia visual')
    const RV = await referenciar(cercaR, `Lee ${trabajo}/guion.json (ese mundo y las escenas que pasan en él) y estas notas del usuario: «${notas}»`)
    REFERENCIA_TXT = RV.txt
    REFERENCIA_POR = RV.por
    log(`Referencia visual: ${RV.refs.length}/${cercaR.length} mundos`)
  }
  phase('Guion')
  // Con TANDA_DESDE o más mundos de cerca, el director trabaja por TANDAS de TANDA_MUNDOS (una pasada tras otra, cada una
  // con sus mundos y solo la referencia de esos mundos): el contexto de cada pasada queda acotado.
  const tandasR = cercaR.length >= TANDA_DESDE ? cercaR.map((_, i) => i).filter((i) => i % TANDA_MUNDOS === 0).map((i) => cercaR.slice(i, i + TANDA_MUNDOS)) : [null]
  const referenciaDe = (tanda) => tanda ? tanda.map((m) => REFERENCIA_POR[m.id]).filter(Boolean).join(' ‖ ') : REFERENCIA_TXT
  const directivaRetoque = (extra, tanda, n) => DIRECTOR +
    `MODO RETOQUE VISUAL. LA VOZ YA ESTÁ GRABADA Y NO SE REGRABA: no cambies ni una palabra de ningún \`texto\`, ni el número de escenas, ni n, tipo, acto, secuencia, el titular y la voz del gancho ni el \`final\` del cierre. Cambia SOLO lo visual (mundos con su ficha \`escena\`, su hora y su estilo; el mundo de cada escena y sus \`cambios\`; cámaras, eventos, marcas, anotaciones). NOTAS DEL USUARIO: «${notas}». ` +
    `Itera con python3 scripts/video3d.py guion ${trabajo} --check hasta 0, LUEGO python3 scripts/video3d.py tiempos ${trabajo} (la voz real: tiene que quedar en 0), python3 scripts/video3d.py storyboard ${trabajo} y python3 scripts/maqueta3d.py escena ${trabajo}/maqueta.json --hoja --salida ${trabajo}/escenas; mira la hoja de cada mundo. ` +
    (tanda ? `EN ESTA PASADA (${n + 1} de ${tandasR.length}) trabaja SOLO estos mundos y las escenas que pasan en ellos: ${tanda.map((m) => m.id).join(', ')}. Los demás mundos y sus escenas NO se tocan (los hace otra pasada); las hojas, solo las de tus mundos. ` : '') +
    (referenciaDe(tanda) ? `REFERENCIA VISUAL (usa sus ids en escena.sostiene; lo que no esté ahí es \`generico\` o va a no_afirmar; suma sus verificacion_visual_<mundo>.json con video3d.py datos si traen cifras): ${referenciaDe(tanda)} ` : '') +
    `Lo que el catálogo no tenga, en briefs (≤ ${BRIEFS_POR_MUNDO} por mundo, con su \`mundo\`; ESCENARIOS completos antes que objetos sueltos). ` + (extra || '') +
    'Retorno: {archivo, gate, fallas[], escenas, estimado_s, tipos_usados[], storyboard, briefs[], aplicadas[]}.'
  let GR = null
  const briefsT = [], aplicadasT = []
  for (const [n, tanda] of tandasR.entries()) {
    GR = await conReparacion(tanda ? `Retoque visual (${tanda.map((m) => m.id).join(', ')})` : 'Retoque visual', (fallos) => agentRol(directivaRetoque(fallos.length ? `REPARACIÓN: ${fallos.join('; ')}. ` : '', tanda, n),
      { agentType: 'video3d-director', schema: S.guion, phase: 'Guion', label: tanda ? `retoque-visual-${n + 1}` : 'retoque-visual' }),
      (r) => r.gate !== 'ok' ? fallasDe(r, 'video3d.py guion --check y tiempos') : [...archivoEs(r, 'guion.json'), ...(!r.storyboard ? ['devuelve la ruta de la hoja del storyboard'] : [])], 2)
    briefsT.push(...(GR.briefs || [])); aplicadasT.push(...(GR.aplicadas || []))
  }
  GR = { ...GR, briefs: briefsT, aplicadas: [...new Set(aplicadasT)] }
  if (tandasR.length > 1) log(`Retoque visual: ${tandasR.length} pasadas del director (${cercaR.length} mundos de cerca, de ${TANDA_MUNDOS} en ${TANDA_MUNDOS})`)
  if (GR.briefs.length) {
    const lista = GR.briefs.slice(0, BRIEFS_MAX), hechosR = []
    for (let i = 0; i < lista.length; i += CONSTRUCTORES_MAX) {
      hechosR.push(...await Promise.all(lista.slice(i, i + CONSTRUCTORES_MAX).map((b) => agentRol(
        `Eres el CONSTRUCTOR de la maqueta 3D (lee referencias/roles/maqueta-constructor.md, con su vara de calidad). BRIEF (retoque visual, para ${trabajo}): ${JSON.stringify(b)}. ` +
          (REFERENCIA_TXT ? `Lo que la referencia visual verificó de ese lugar (dibuja solo eso; lo demás, genérico): ${REFERENCIA_TXT} ` : '') +
          'Si el catálogo ya lo tiene (python3 scripts/maqueta3d.py catalogo --para sesion --escala <escala>), devuélvelo reutilizado; si no, escríbelo, deja python3 scripts/maqueta_modulo.py check <clase>/<tipo> en 0, mira sus hojas (día y otra hora) y regístralo. ' +
          'Retorno: {tipo, clase, modulo, check, registrado, reutilizado, fallas[], vueltas, lecturas, s_por_cuadro, ejemplo, nucleo[]}.',
        { agentType: 'maqueta-constructor', schema: S.modulo, phase: 'Constructor', label: `constructor-${b.id || i}` })
        .then((r) => ({ brief: b.id, ...r })).catch(() => ({ brief: b.id, check: 'falla', registrado: false, reutilizado: false })))))
    }
    const usables = hechosR.filter((r) => r.check === 'ok' && (r.registrado || r.reutilizado)).map((r) => `${r.brief} → «${r.tipo}» (${JSON.stringify(r.ejemplo || {})})`).join('; ')
    if (usables) GR = await conReparacion('Retoque visual (con lo construido)', (fallos) => agentRol(directivaRetoque(`El constructor registró: ${usables}: úsalo. ${fallos.length ? `REPARACIÓN: ${fallos.join('; ')}. ` : ''}`),
      { agentType: 'video3d-director', schema: S.guion, phase: 'Guion', label: 'retoque-construido' }),
      (r) => r.gate !== 'ok' ? fallasDe(r, 'video3d.py guion --check y tiempos') : archivoEs(r, 'guion.json'), 1)
    for (const r of hechosR) if ((r.nucleo || []).length) avisar(`NÚCLEO (brief ${r.brief}, tipo ${r.tipo}): ${r.nucleo.join(' · ')}`)
  }
  phase('Crítica')
  const CR = await agentRol(
    `MODO 3D (${guia('video-critico', '3d')}), ACOTADO A LO VISUAL de un retoque: TRABAJO = ${trabajo}. La voz y el texto no se juzgan. Lee ${trabajo}/guion.json, ${trabajo}/direccion.json y UNA hoja por mundo en ${trabajo}/escenas/<tramo>/hoja_9x16.jpg (python3 scripts/maqueta3d.py escena ${trabajo}/maqueta.json imprime la medida de cada tramo). ` +
      `NOTAS DEL USUARIO que el retoque debía cumplir: «${notas}». Puntúa cada mundo de cerca en \`escenas[]\` (detalle, vida, realismo, claridad; 1–5, con que_falta) y escribe las faltas (3C2, 3C5, 3C9–3C11) con su arreglo. Escribe ${trabajo}/critica.json.`,
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: 'critica-retoque' })
  const flojasR = (CR.escenas || []).filter((e) => PUNTAJES_ESCENA.some((k) => e[k] < PUNTAJE_ESCENA_MIN))
  // Lo que el crítico vio se corrige aquí mismo, en UNA pasada del director y sin otra crítica (antes las mejoras volvían
  // en el reporte y la sesión las aplicaba a mano). args.correcciones: lo que la sesión o el usuario vieron en las hojas.
  const correcciones = String(A.correcciones || '').trim()
  let aplicadasR = [], sinAplicarR = []
  if (CR.faltas.length || flojasR.length || correcciones) {
    const antes = GR
    GR = await conReparacion('Correcciones del retoque', (fallos) => agentRol(DIRECTOR +
      `MODO CORRECCIÓN DE UN RETOQUE VISUAL. LA VOZ YA ESTÁ GRABADA: no cambies ningún texto, ni n, tipo, acto, secuencia, el gancho ni el final. ` +
      `Aplica las faltas del crítico: las que traen probado true, TAL CUAL; las demás, resuélvelas tú con el catálogo (cámara, parámetros de una pieza, un actor, un evento, la hora) y pruébalas con el gate. ` +
      `Si una rompe un gate, déjala fuera y dilo en fallas[] con el prefijo «SIN APLICAR:»; si una pide algo que el catálogo no tiene, pídelo en briefs[] (≤ ${BRIEFS_CORRECCION}, ESCENARIOS completos, con su mundo) y aplica todo lo demás. FALTAS: ${JSON.stringify(CR.faltas)}. ` +
      (flojasR.length ? `MUNDOS CON UN PUNTAJE BAJO (sube lo que les falta): ${JSON.stringify(flojasR)}. ` : '') +
      (correcciones ? `ADEMÁS, lo que se vio en las hojas: «${correcciones}». ` : '') +
      `Deja python3 scripts/video3d.py guion ${trabajo} --check en 0, LUEGO python3 scripts/video3d.py tiempos ${trabajo} en 0 y python3 scripts/video3d.py storyboard ${trabajo} (rehace también las hojas de escenas); mira la hoja de cada mundo que cambiaste y corrige lo que siga mal. ` +
      'Retorno: {archivo, gate, fallas[] (solo las «SIN APLICAR: …» si el gate quedó en 0), escenas, estimado_s, tipos_usados[], storyboard, briefs[], aplicadas[] (escenas cambiadas)}.' +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video3d-director', schema: S.guion, phase: 'Crítica', label: 'correcciones-retoque' }),
    (r) => r.gate !== 'ok' ? fallasDe(r, 'video3d.py guion --check y tiempos') : archivoEs(r, 'guion.json'), 1)
      .catch((e) => { avisar(`AVISO: las correcciones del retoque no se pudieron aplicar (${String(e.message).split('\n')[0]}): quedan en el reporte.`); return antes })
    aplicadasR = GR === antes ? [] : (GR.aplicadas || [])
    sinAplicarR = GR === antes ? [] : (GR.fallas || []).filter((x) => /^SIN APLICAR/i.test(x))
    // lo que la corrección pide y el catálogo no tiene: el constructor lo hace y el director lo pone (una pasada más)
    const briefsC = GR === antes ? [] : (GR.briefs || []).slice(0, BRIEFS_CORRECCION)
    if (briefsC.length) {
      phase('Constructor')
      const hechosC = await Promise.all(briefsC.map((b, i) => agentRol(
        `Eres el CONSTRUCTOR de la maqueta 3D (lee referencias/roles/maqueta-constructor.md, con su vara de calidad). BRIEF (corrección de un retoque visual, para ${trabajo}): ${JSON.stringify(b)}. ` +
          (REFERENCIA_TXT ? `Lo que la referencia visual verificó de ese lugar (dibuja solo eso; lo demás, genérico): ${REFERENCIA_TXT} ` : '') +
          'Si el catálogo ya lo tiene (python3 scripts/maqueta3d.py catalogo --para sesion --escala <escala>), devuélvelo reutilizado; si no, escríbelo, deja python3 scripts/maqueta_modulo.py check <clase>/<tipo> en 0, mira sus hojas (día y otra hora) y regístralo. ' +
          'Retorno: {tipo, clase, modulo, check, registrado, reutilizado, fallas[], vueltas, lecturas, s_por_cuadro, ejemplo, nucleo[]}.',
        { agentType: 'maqueta-constructor', schema: S.modulo, phase: 'Constructor', label: `constructor-correccion-${b.id || i}` })
        .then((r) => ({ brief: b.id, ...r })).catch(() => ({ brief: b.id, check: 'falla', registrado: false, reutilizado: false }))))
      for (const r of hechosC) if ((r.nucleo || []).length) avisar(`NÚCLEO (brief ${r.brief}, tipo ${r.tipo}): ${r.nucleo.join(' · ')}`)
      const usablesC = hechosC.filter((r) => r.check === 'ok' && (r.registrado || r.reutilizado)).map((r) => `${r.brief} → «${r.tipo}» (${JSON.stringify(r.ejemplo || {})})`).join('; ')
      sinAplicarR.push(...hechosC.filter((r) => !(r.check === 'ok' && (r.registrado || r.reutilizado))).map((r) => `SIN APLICAR: el constructor no entregó el brief ${r.brief}`))
      if (usablesC) {
        phase('Crítica')
        const previo = GR
        GR = await conReparacion('Correcciones del retoque (con lo construido)', (fallos) => agentRol(DIRECTOR +
          `MODO CORRECCIÓN DE UN RETOQUE VISUAL. LA VOZ YA ESTÁ GRABADA: no cambies ningún texto, ni n, tipo, acto, secuencia, el gancho ni el final. ` +
          `El constructor registró lo que pediste: ${usablesC}. Ponlo donde lo pediste (briefs: ${JSON.stringify(briefsC)}) y no toques nada más. ` +
          `Deja python3 scripts/video3d.py guion ${trabajo} --check en 0, LUEGO python3 scripts/video3d.py tiempos ${trabajo} en 0 y python3 scripts/video3d.py storyboard ${trabajo}; mira la hoja de ese mundo y corrige lo que siga mal. ` +
          'Retorno: {archivo, gate, fallas[], escenas, estimado_s, tipos_usados[], storyboard, briefs[] (vacío), aplicadas[] (escenas cambiadas)}.' +
          (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
        { agentType: 'video3d-director', schema: S.guion, phase: 'Crítica', label: 'correcciones-construido' }),
        (r) => r.gate !== 'ok' ? fallasDe(r, 'video3d.py guion --check y tiempos') : archivoEs(r, 'guion.json'), 1)
          .catch((e) => { avisar(`AVISO: lo construido en la corrección no se pudo poner (${String(e.message).split('\n')[0]}): queda en el catálogo.`); return previo })
        aplicadasR = [...new Set([...aplicadasR, ...(GR.aplicadas || [])])]
        // lo que quedó «sin aplicar» a la espera del constructor ya está puesto: manda lo que diga esta última pasada
        if (GR !== previo) sinAplicarR = [...(GR.fallas || []).filter((x) => /^SIN APLICAR/i.test(x)), ...sinAplicarR.filter((x) => /el constructor no entregó/.test(x))]
      }
    }
  }
  // SEGUNDA LECTURA (corta): si la corrección cambió algo, el crítico vuelve a mirar SOLO los mundos que cambiaron o que
  // estaban flojos; sus puntajes y sus faltas reemplazan a los de antes (el retorno ya no trae la nota de lo ya corregido).
  let escenasR = CR.escenas || [], faltasR = CR.faltas, segunda = false
  if (aplicadasR.length) {
    const CR2 = await agentRol(
      `MODO 3D (${guia('video-critico', '3d')}), SEGUNDA LECTURA CORTA de un retoque visual ya corregido: TRABAJO = ${trabajo}. La voz y el texto no se juzgan. ` +
        `Tu primera lectura está en ${trabajo}/critica.json (no la reescribas). El director corrigió estas escenas: ${JSON.stringify(aplicadasR)}${flojasR.length ? `; los mundos con un puntaje bajo eran: ${flojasR.map((e) => e.mundo).join(', ')}` : ''}. ` +
        `Mira SOLO la hoja de los mundos de esas escenas y de esos mundos flojos (${trabajo}/escenas/<tramo>/hoja_9x16.jpg; python3 scripts/maqueta3d.py escena ${trabajo}/maqueta.json imprime la medida de cada tramo). ` +
        'Puntúa de nuevo SOLO esos mundos en escenas[] (detalle, vida, realismo, claridad; 1–5, con que_falta) y deja en faltas[] SOLO lo que sigue mal en ellos tras la corrección (lo ya corregido no se repite; no propongas rehacer lo que no viste). ' +
        `Escribe ${trabajo}/critica_2.json.`,
      { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: 'critica-retoque-2' })
      .catch((e) => { avisar(`AVISO: la segunda lectura del crítico no terminó (${String(e.message).split('\n')[0]}): los puntajes son los de antes de corregir.`); return null })
    if (CR2) {
      const vistos = new Set((CR2.escenas || []).map((e) => e.mundo))
      escenasR = [...escenasR.filter((e) => !vistos.has(e.mundo)), ...(CR2.escenas || [])]
      faltasR = CR2.faltas || []
      segunda = true
    }
  }
  const flojasFin = escenasR.filter((e) => PUNTAJES_ESCENA.some((k) => e[k] < PUNTAJE_ESCENA_MIN))
  return { trabajo, tema, veredicto: flojasFin.length || faltasR.some((x) => x.gravedad === 'bloquea') ? 'corregir' : 'retoque_listo', etapa: 'retoque_visual',
    escenas: escenasR, segunda_lectura: segunda, faltas_pendientes: faltasR.filter((x) => x.gravedad === 'bloquea'), mejoras: faltasR.filter((x) => x.gravedad === 'mejora'),
    corregidas: aplicadasR, sin_aplicar: sinAplicarR,
    storyboard: GR.storyboard, tipos_usados: GR.tipos_usados, avisos: AVISOS_WF }
}

// ── 1. Dirección ─────────────────────────────────────────────────────────────
// (la directiva no depende de args.estilo ni de args.gancho: al reanudar con resumeFromRunId esta llamada sale de la caché)
phase('Dirección')
const validarDireccion = (r) => [
  ...archivoEs(r, 'direccion.json'),
  ...(r.criterio === 'ninguno' ? [] : (!r.frases.length ? ['frases: una entrada por oración del borrador (frase, verbo del catálogo, que_se_ve)'] : [])),
  ...(r.briefs.length > BRIEFS_MAX ? [`${r.briefs.length} briefs; van ≤ ${BRIEFS_MAX} (≤ ${BRIEFS_POR_MUNDO} por mundo; cuenta lo demás con lo que hay en el catálogo)`] : []),
  ...(r.criterio !== 'ninguno' && !(r.mundos || []).length ? ['mundos: al menos uno, cada uno con su id y su escala'] : []),
  ...(r.estilo.confianza === 'baja' && (r.estilo.candidatos || []).length < 2 ? ['estilo con confianza baja: candidatos (2–3) y el mismo cuadro en cada uno (estilos/<id>/)'] : []),
]
const DIR = await conReparacion('Dirección', (fallos) => agentRol(DIRECTOR +
  `MODO DIRECCIÓN: escribe ${trabajo}/direccion.json (idea_visual, criterio lugar|mecanismo, mundos {id: mundo} — TANTOS COMO LA HISTORIA NECESITE, cada uno con su escala (el lugar en pais o ciudad; la escena humana o el mecanismo en esquema), y se puede volver a uno —, con su FICHA DE ESCENA («escena»: que_pasa, quien, con_que, se_mueve, sostiene[]; C3D14), su «hora» con «hora_razon» si no es de día (C3D19) y su «estilo» si no es el global —, estilo {id, razon, confianza, candidatos} (el global; cada mundo puede llevar el suyo), protagonista, borrador de la narración, frases[] con el mundo y el verbo visual del catálogo por oración, dudas_visuales por mundo (lo que quieres dibujar y hay que verificar: cómo se ve, qué pasa, con qué), briefs[] (≤ ${BRIEFS_POR_MUNDO} por mundo, ≤ ${BRIEFS_MAX}; cada uno con su «mundo»; ESCENARIOS completos antes que objetos sueltos), no_afirmar). ` +
    'Si ni el lugar ni el mecanismo se entienden mejor viéndolos moverse, criterio "ninguno" y en nota el flujo que le toca. ' +
    'Retorno: {archivo, idea_visual, criterio, mundos[]{id, escala, para}, estilo, protagonista, frases[], briefs[], nota}.' +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video3d-director', schema: S.direccion, phase: 'Dirección', label: 'direccion' }), validarDireccion, 2)
log(`Dirección: «${DIR.idea_visual}» · ${DIR.criterio} · mundos ${DIR.mundos.map((m) => `${m.id} (${m.escala})`).join(' → ')} · estilo ${DIR.estilo.id} (${DIR.estilo.confianza}) · ${DIR.frases.length} frases · ${DIR.briefs.length} brief(s)`)
if (DIR.criterio === 'ninguno') {
  return { trabajo, tema, veredicto: 'no_es_3d', etapa: 'direccion', nota: DIR.nota || '', avisos: AVISOS_WF }
}

// ── 1b. Referencia visual: cómo es cada lugar de cerca en la realidad (lo que se dibuja también se afirma) ───────────
// Un verificador por mundo de cerca (≤ VERIFICADORES_MAX a la vez), con la misma plantilla; en fixture no hay web: se salta.
let REFERENCIA_TXT = ''
const REFERENCIAS = []
if (!A.fixture && !A.sin_referencia) {
  phase('Referencia visual')
  const cerca = (DIR.mundos || []).filter((m) => m.escala && m.escala !== 'pais')
  const RV = await referenciar(cerca, `Lee ${trabajo}/direccion.json (la ficha «escena» de ese mundo, sus dudas_visuales y no_afirmar)`)
  REFERENCIAS.push(...RV.refs); REFERENCIA_TXT = RV.txt
  log(`Referencia visual: ${REFERENCIAS.length}/${cerca.length} mundos · ${REFERENCIAS.reduce((n, r) => n + r.se_puede_dibujar.length, 0)} cosas con respaldo`)
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
  ...(r.escenas < ESCENAS_MIN || r.escenas > ESCENAS_TOPE ? [`${r.escenas} escenas; van ${ESCENAS_MIN}–${ESCENAS_TOPE} (≈ una cada 7 s del objetivo)`] : []),
  ...(r.estimado_s > DURACION_MAX_S * 1.2 ? [`estimado ${r.estimado_s} s: el tope es ${DURACION_MAX_S} s`] : []),
  ...(!r.storyboard ? ['corre python3 scripts/video3d.py storyboard y devuelve la ruta de la hoja'] : []),
]
const directivaGuion = (extra) => DIRECTOR +
  `MODO GUION: el gancho es «${gancho}» (python3 scripts/video3d.py ganchos ${trabajo} --usar ${gancho} --por ${elegidoPor}); estilo «${estilo}». ` +
  `Escribe PRIMERO la narración de corrido (guion.narracion), actualiza direccion.json → frases con ella y DESPUÉS repártela sin cambiar una palabra en las escenas que necesite (≥ ${ESCENAS_MIN}; ≈ una cada 7 s) con camara, eventos, marcas y cifras con anclas dice, el cierre y el caption. Cada mundo de cerca con su ficha \`escena\` (C3D14–C3D18) y su hora (C3D19). ` +
  (REFERENCIA_TXT ? `REFERENCIA VISUAL (usa sus ids en escena.sostiene; lo que no esté ahí es \`generico\` o va a no_afirmar): ${REFERENCIA_TXT} ` : '') +
  `Corre python3 scripts/video3d.py guion ${trabajo} --check hasta 0 fallas (C3D1–C3D19, M3D1–M3D19: cada escena de cerca llena, variada y viva), luego python3 scripts/video3d.py storyboard ${trabajo}, python3 scripts/maqueta3d.py escena ${trabajo}/maqueta.json --hoja --salida ${trabajo}/escenas, y mira la hoja del storyboard y UNA hoja por mundo. ` +
  (construidos.length ? `Tipos del constructor: ${resumenConstruidos(construidos) || 'ninguno usable'}. ` : '') +
  `Si aparece algo que el catálogo no tiene, cuéntalo con lo que hay y devuélvelo en briefs (≤ ${BRIEFS_POR_MUNDO} por mundo, con su \`mundo\`). ` + (extra || '') +
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
      `Insumos: ${trabajo}/guion.json, ${trabajo}/locucion.json, ${trabajo}/direccion.json (frases: el verbo visual de cada oración), UNA lectura de ${G.storyboard} y UNA de la hoja de cada mundo en ${trabajo}/escenas/<tramo>/hoja_9x16.jpg (si faltan: python3 scripts/maqueta3d.py escena ${trabajo}/maqueta.json --hoja --salida ${trabajo}/escenas; ese comando también imprime la medida de cada tramo). No critiques lo que eligió el usuario (gancho, estilo, duración). ` +
      `REVISIÓN DE ESCENAS: por cada mundo de cerca, puntúa (1–5) detalle (¿es un lugar completo o cosas sueltas?), vida (¿se mueve gente y máquinas?), realismo (¿se parece a lo que pasa ahí? coteja con verificacion_visual_<mundo>.json) y claridad (¿se entiende qué es cada cosa a tamaño de teléfono?) en \`escenas[]\` con \`que_falta\`; un puntaje ≤ 2 es una falta que bloquea (regla 3C11) con arreglo «brief al constructor: …» o el cambio de cámara o de piezas. ` +
      `Cada arreglo, probado en una copia del TRABAJO con python3 scripts/video3d.py guion <copia> --check (probado: true/false). Escribe ${trabajo}/critica.json.` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: `critica-${vuelta}` }),
  (r) => {
    const f = []
    const flojas = (r.escenas || []).filter((e) => PUNTAJES_ESCENA.some((k) => e[k] < PUNTAJE_ESCENA_MIN))
    const bloquea = r.faltas.some((x) => x.gravedad === 'bloquea') || PUNTAJES.some((k) => r.puntajes[k] < PUNTAJE_MIN) || flojas.length > 0
    if (flojas.length && !r.faltas.some((x) => x.gravedad === 'bloquea' && x.regla === '3C11')) f.push(`las escenas ${flojas.map((e) => e.mundo).join(', ')} tienen un puntaje < ${PUNTAJE_ESCENA_MIN}: escribe su falta 3C11 que bloquea, con el arreglo`)
    if ((r.veredicto === 'pasa') === bloquea) f.push(`veredicto ${r.veredicto} incoherente con las faltas y los puntajes`)
    for (const x of r.faltas) if (x.gravedad === 'bloquea' && x.probado === false) f.push(`la falta de la escena ${x.escena} bloquea con un arreglo que el gate rechaza: ajústalo hasta que pase o dala como mejora`)
    return f
  }, 1)
  log(`Crítica ${vuelta}: ${critica.veredicto} · ${PUNTAJES.map((k) => `${k} ${critica.puntajes[k]}`).join(' · ')}`)
  if (critica.veredicto === 'pasa' || vuelta === VUELTAS_CRITICA) break
  const bloquean = critica.faltas.filter((x) => x.gravedad === 'bloquea')
  G = await conReparacion('Corrección', (fallos) => agentRol(DIRECTOR +
    `MODO CORRECCIÓN: aplica SOLO estas faltas del crítico (los arreglos probados, tal cual), sin tocar el gancho: ${JSON.stringify(bloquean)}. ` +
    `Escenas flojas (puntaje < ${PUNTAJE_ESCENA_MIN}): ${JSON.stringify((critica.escenas || []).filter((e) => PUNTAJES_ESCENA.some((k) => e[k] < PUNTAJE_ESCENA_MIN)))}: llénalas con lo que el catálogo tiene (escenarios, gente con su pose, ambiente, cámara más cerca) y, si falta un tipo, devuélvelo en briefs con su \`mundo\`. ` +
    `Deja python3 scripts/video3d.py guion ${trabajo} --check en 0 y rehaz python3 scripts/video3d.py storyboard ${trabajo} y python3 scripts/maqueta3d.py escena ${trabajo}/maqueta.json --hoja --salida ${trabajo}/escenas. ` +
    'Retorno: {archivo, gate, fallas[], escenas, estimado_s, tipos_usados[], storyboard, briefs[], aplicadas[] (escenas cambiadas)}.' +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video3d-director', schema: S.guion, phase: 'Crítica', label: `correccion-${vuelta}` }), validarGuion, 1)
  if (G.briefs.length) {   // lo que el crítico pidió y el catálogo no tiene: el constructor lo hace y el director lo usa
    const H3 = await construir(G.briefs, `crítica ${vuelta}`)
    if (resumenConstruidos(H3)) {
      G = await conReparacion('Corrección (con lo construido)', (fallos) => agentRol(directivaGuion(`MODO CORRECCIÓN: el constructor registró lo que pediste (${resumenConstruidos(H3)}): úsalo en sus mundos, sin tocar el texto ni el gancho. ${fallos.length ? `REPARACIÓN: ${fallos.join('; ')}. ` : ''}`),
        { agentType: 'video3d-director', schema: S.guion, phase: 'Crítica', label: `correccion-construido-${vuelta}` }), validarGuion, 1)
    }
  }
}
if (critica.veredicto !== 'pasa') {
  return { trabajo, tema, veredicto: 'corregir', etapa: 'critica', puntajes: critica.puntajes, faltas_pendientes: critica.faltas.filter((x) => x.gravedad === 'bloquea'),
    gancho, estilo, construidos, avisos: AVISOS_WF }
}

// ── 6b. Las mejoras PROBADAS del crítico se aplican solas (antes hacían falta a mano); una sola pasada, sin otra crítica ──
const probadas = critica.faltas.filter((x) => x.gravedad === 'mejora' && x.probado === true)
if (probadas.length) {
  const antes = G
  G = await conReparacion('Mejoras probadas', (fallos) => agentRol(DIRECTOR +
    `MODO CORRECCIÓN: el guion ya está aprobado; aplica TAL CUAL estas mejoras que el crítico probó (si una rompe un gate, déjala fuera y dilo): ${JSON.stringify(probadas)}. ` +
    `Sin tocar el gancho. Deja python3 scripts/video3d.py guion ${trabajo} --check en 0 y rehaz el storyboard y las hojas de escenas. ` +
    'Retorno: {archivo, gate, fallas[], escenas, estimado_s, tipos_usados[], storyboard, briefs[] (vacío), aplicadas[] (escenas cambiadas)}.' +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video3d-director', schema: S.guion, phase: 'Crítica', label: 'mejoras-probadas' }), validarGuion, 1)
    .catch((e) => { avisar(`AVISO: las mejoras probadas no se pudieron aplicar (${String(e.message).split('\n')[0]}): quedan en el reporte.`); return antes })
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
  idea_visual: DIR.idea_visual, mundos: DIR.mundos, puntajes: critica.puntajes, escenas: critica.escenas || [],
  referencias: REFERENCIAS.map((r) => ({ mundo: r.mundo, archivo: r.archivo, con_respaldo: r.se_puede_dibujar.length })),
  mejoras: critica.faltas.filter((x) => x.gravedad === 'mejora' && x.probado !== true),
  storyboard: G.storyboard, tipos_usados: G.tipos_usados,
  cierres: CIERRES ? CIERRES.candidatos.filter((c) => CIERRES.elegibles.includes(c.id)) : null,
  construidos, avisos: AVISOS_WF,
}
