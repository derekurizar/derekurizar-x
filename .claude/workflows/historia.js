export const meta = {
  name: 'historia',
  description: 'Historia narrada para /historia: historia-editor (encuadre: pregunta, protagonista, revelaciones, fotos_clave, arco, 3–5 capítulos, 2–3 ejes) → un historia-investigador por eje ⇢ su historia-verificador (pipeline; segunda fuente por hecho, fechas, estado de los casos, fotos con licencia y la del protagonista; gate H1–H3, H7, H12) → consolidar (cronología y base) → video-gancho en modo historia (4–5 candidatos con la foto del protagonista; gate R1–R9, H10, H12, H13) → video-critico elige (reserva: no regala una revelación) → historia-guionista (gate H3–H14 + V1–V5, V9, F1–F8) → historia-oyente (oyente ingenuo: solo la voz y la pantalla) → crítico en modo historia (resuelve o justifica cada confusión del oyente; ≤ 2 vueltas; con «pasa», el guionista aplica sus mejoras) → video-animador por escena explica sin animación. 0 créditos de ElevenLabs.',
  whenToUse: 'Invocado por /historia <tema> DESPUÉS de `python3 scripts/historia.py preparar "<tema>"`. args: {trabajo, tema, permitir_fallback, desde, notas}. trabajo = sesiones/historia-<slug> (lo imprime preparar). Produce y aprueba <trabajo>/encuadre.json, hallazgos_*.json, verificacion_*.json, fotos/, historia.json, base/, ganchos.json, seleccion.json, guion.json, locucion.json, oyente.json y critica.json; la voz (o la voz falsa), los tiempos, la grabación y el montaje los hace la sesión principal después. Si el crítico sigue en «corregir» tras 2 vueltas, el workflow NO falla: devuelve veredicto corregir + faltas_pendientes y el comando pregunta al usuario. desde: "retoque" + notas (lo que pidió el usuario) = guion.json ya aprobado y con voz: salta a Guion (RETOQUE: aplica solo las notas y conserva las voces que no cambian) → gate → oyente → crítica (1 vuelta) → mejoras → animación; devuelve voces_cambiadas para regrabar solo esas.',
  phases: [
    { title: 'Encuadre', detail: 'historia-editor: encuadre.json con la pregunta central, el protagonista, las revelaciones (lo que el video paga y el gancho no dice), fotos_clave (la primera es la imagen del protagonista), el arco, 3–5 capítulos con su pregunta, 2–3 ejes de investigación, paleta, no_afirma y lo sensible (justicia)' },
    { title: 'Investigación', detail: 'un historia-investigador por eje en paralelo: hechos con fecha y cita literal del texto guardado (historia.py leer: HTML, PDF o Wayback), cifras, frases literales y fotos candidatas → hallazgos_<eje>.json' },
    { title: 'Verificación', detail: 'un historia-verificador por eje en cuanto su investigador termina: segunda fuente independiente por hecho, fechas en conflicto, estado actual de los casos, fotos con licencia (historia.py foto; la og:image de las notas leídas con --de-fuente; la del protagonista con --protagonista) → verificacion_<eje>.json; gate historia.py hechos --check (H1–H3, H7, H12); si ninguna muestra al protagonista, un verificador la baja antes de los ganchos' },
    { title: 'Ganchos', detail: 'video-gancho en modo historia: consolidar (cronología y base) y 4–5 candidatos de familias de historia (resultado, paradoja, contraste, misterio, personaje, lugar, pregunta, escala), todos con la foto del protagonista a sangre y sin adelantar una revelación; gate historia.py ganchos --check (R1–R9, H10, H12, H13)' },
    { title: 'Selección', detail: 'video-critico en modo selección: en silencio y con la voz; puntúa silencio, reserva (no regala una revelación), tension, alineacion, honestidad, novedad; ganador y segundo en seleccion.json; si ninguno llega a 3, video-gancho rehace una vez' },
    { title: 'Guion', detail: 'historia-guionista: ganchos --usar → guion.json (promesa con revela, capítulos que responden su pregunta, foto, cita, tarjeta, golpe, explica, giro, cierre legado, captions); gate historia.py guion --check (H3–H14 + V1–V5, V9, F1–F8) y su línea RETORNO; en retoque aplica las notas del usuario y conserva las voces' },
    { title: 'Oyente', detail: 'historia-oyente (sonnet): solo la voz en orden y lo que hay en pantalla (digesto --para oyente); oyente.json con de qué es la historia, qué prometió y qué dio, confusiones, saltos, repeticiones y preguntas sin responder; vuelve a correr tras cada corrección' },
    { title: 'Crítica', detail: 'video-critico en modo historia: gancho, tensión, claridad e hilo, ritmo, precisión, cierre; resuelve (bloquea) o justifica cada confusión y salto del oyente; lo que bloquea vuelve al guionista, ≤ 2 vueltas (1 en retoque); con «pasa», el guionista aplica las mejoras (también las de voz) y repasa el gate, sin otra crítica' },
    { title: 'Animación', detail: 'video-animador por cada escena explica con animacion null (solo si el crítico aprueba): reusa del catálogo o escribe video/animaciones/<id>.js, --check, --registrar y --asignar' },
  ],
}

// Guías: referencias/flujo-historia.md, referencias/roles/historia-{editor,investigador,verificador,guionista}.md y el
// «Modo historia» de referencias/roles/video-{gancho,critico,animador}.md. Los agentes escriben su artefacto COMPLETO en
// <trabajo>/ y devuelven aquí un resumen validado por schema; los gates de contenido viven en scripts/historia.py
// (H1–H14, que llama a video.py para V1–V5, V9 y F1–F8). FAMILIAS, VISUALES, TIPOS y PUNTAJES son espejos literales de
// scripts/historia.py (los vigila scripts/check_workflows.py, W12). Modo retoque (args.desde = "retoque" + args.notas): las
// fases 1–5 se saltan y el guionista aplica las notas del usuario sobre el guion aprobado conservando las voces grabadas.

const TIPOS = ['gancho', 'tarjeta', 'golpe', 'definicion', 'adivina', 'mapa', 'ranking', 'escala', 'tiempo', 'explica', 'foto', 'cita', 'capitulo']
const FAMILIAS = ['resultado', 'paradoja', 'contraste', 'misterio', 'personaje', 'lugar', 'pregunta', 'escala']
const VISUALES = ['foto']
const PUNTAJES = ['gancho', 'tension', 'claridad', 'ritmo', 'precision', 'cierre']
const REGLA_DE = { gancho: 'H-C1', tension: 'H-C2', claridad: 'H-C3', ritmo: 'H-C4', precision: 'H-C5', cierre: 'H-C6' }
const EJES_MIN = 2, EJES_MAX = 3, CAPITULOS_MIN = 3, CAPITULOS_MAX = 5, HECHOS_MIN = 6
const CANDIDATOS_MIN = 4, CANDIDATOS_MAX = 5, DURACION_MAX_S = 180
const VUELTAS_CRITICA = 2, PUNTAJE_MIN = 3

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/(historia-[a-z0-9-]+|_fixture_historia\/[a-z0-9_-]+)$/.test(trabajo)) throw new Error('args.trabajo debe ser sesiones/historia-<slug> (la última línea que imprime `python3 scripts/historia.py preparar "<tema>"`).')
const tema = String(A.tema || '').trim()
if (!tema) throw new Error('args.tema: el tema de la historia, tal como lo dio el usuario.')
const RETOQUE = String(A.desde || '') === 'retoque'
const notas = String(A.notas || '').trim()
if (A.desde && !RETOQUE) throw new Error('args.desde: solo "retoque" (guion.json aprobado en TRABAJO + args.notas con lo que pidió el usuario).')
if (RETOQUE && !notas) throw new Error('args.notas: en modo retoque, lo que pidió el usuario (cambiar el gancho por g3, reescribir la escena 7, otro cierre, quitar la cita de la 10…).')
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

// ── Schemas de retorno ───────────────────────────────────────────────────────
const S = {
  rechequeo: { type: 'object', properties: { items: { type: 'array' } } },   // lo pide el bloque común; aquí no se usa
  encuadre: {
    type: 'object', required: ['archivo', 'pregunta', 'protagonista', 'revelaciones', 'fotos_clave', 'arco', 'capitulos', 'ejes', 'paleta', 'justicia'],
    properties: {
      archivo: { type: 'string', pattern: 'encuadre\\.json$' }, pregunta: { type: 'string' }, arco: { type: 'string' },
      protagonista: { type: 'array', items: { type: 'string' } },
      revelaciones: { type: 'array', items: { type: 'string' } }, fotos_clave: { type: 'array', items: { type: 'string' } },
      capitulos: { type: 'array', items: { type: 'string' } }, ejes: { type: 'array', items: { type: 'string', pattern: '^[a-z]{2,6}$' } },
      paleta: { type: 'string' }, justicia: { type: 'boolean' },
    },
  },
  hallazgos: {
    type: 'object', required: ['eje', 'archivo', 'hechos', 'cifras', 'citas', 'fotos'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string', pattern: 'hallazgos_[a-z]+\\.json$' },
      hechos: { type: 'integer' }, cifras: { type: 'integer' }, citas: { type: 'integer' }, fotos: { type: 'integer' },
      huecos: { type: 'array', items: { type: 'string' } },
    },
  },
  verificacion: {
    type: 'object', required: ['eje', 'archivo', 'gate', 'confirmados', 'en_disputa', 'descartados', 'fotos'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string', pattern: 'verificacion_[a-z]+\\.json$' },
      gate: { type: 'string', enum: ['ok', 'falla'] }, fallas: { type: 'array', items: { type: 'string' } },
      confirmados: { type: 'integer' }, en_disputa: { type: 'integer' }, descartados: { type: 'integer' },
      fotos: { type: 'integer' }, casos: { type: 'integer' }, protagonista: { type: 'integer' },
    },
  },
  ganchos: {
    type: 'object', required: ['archivo', 'gate', 'hechos', 'candidatos', 'intentos'],
    properties: {
      archivo: { type: 'string', pattern: 'ganchos\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, hechos: { type: 'integer' },
      candidatos: {
        type: 'array',
        items: { type: 'object', required: ['id', 'familia', 'visual', 'pantalla'],
          properties: { id: { type: 'string' }, familia: { type: 'string', enum: FAMILIAS }, visual: { type: 'string', enum: VISUALES }, pantalla: { type: 'string' } } },
      },
      intentos: { type: 'integer' },
    },
  },
  seleccion: {
    type: 'object', required: ['archivo', 'ganador', 'segundo', 'puntajes', 'por_que', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'seleccion\\.json$' },
      ganador: { type: ['string', 'null'] }, segundo: { type: ['string', 'null'] }, puntajes: { type: 'object' }, por_que: { type: 'string' },
      faltas: { type: 'array', items: { type: 'object', required: ['candidato', 'regla', 'problema', 'arreglo'],
        properties: { candidato: { type: 'string' }, regla: { type: 'string' }, problema: { type: 'string' }, arreglo: { type: 'string' } } } },
    },
  },
  guion: {
    type: 'object', required: ['archivo', 'gate', 'escenas', 'tipos', 'capitulos', 'estimado_s', 'explica_sin_animacion'],
    properties: {
      archivo: { type: 'string', pattern: 'guion\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, escenas: { type: 'integer' },
      tipos: { type: 'array', items: { type: 'string', enum: TIPOS } }, capitulos: { type: 'integer' }, estimado_s: { type: 'number' },
      explica_sin_animacion: { type: 'array', items: { type: 'integer' } },
      voces_cambiadas: { type: 'array', items: { type: 'integer' } },
    },
  },
  mejoras: {
    type: 'object', required: ['archivo', 'gate', 'escenas', 'tipos', 'capitulos', 'estimado_s', 'explica_sin_animacion', 'aplicadas', 'no_aplicadas'],
    properties: {
      archivo: { type: 'string', pattern: 'guion\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, escenas: { type: 'integer' },
      tipos: { type: 'array', items: { type: 'string', enum: TIPOS } }, capitulos: { type: 'integer' }, estimado_s: { type: 'number' },
      explica_sin_animacion: { type: 'array', items: { type: 'integer' } },
      voces_cambiadas: { type: 'array', items: { type: 'integer' } },
      aplicadas: { type: 'array', items: { type: 'integer' } },
      no_aplicadas: { type: 'array', items: { type: 'object', required: ['n', 'motivo'], properties: { n: { type: 'integer' }, motivo: { type: 'string' } } } },
    },
  },
  critica: {
    type: 'object', required: ['archivo', 'vuelta', 'veredicto', 'puntajes', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'critica\\.json$' }, vuelta: { type: 'integer' }, veredicto: { type: 'string', enum: ['pasa', 'corregir'] },
      puntajes: { type: 'object', required: PUNTAJES, properties: Object.fromEntries(PUNTAJES.map((k) => [k, { type: 'integer', minimum: 1, maximum: 5 }])) },
      bloqueantes: { type: 'integer' }, mejoras: { type: 'integer' },
      faltas: { type: 'array', items: { type: 'object', required: ['regla', 'gravedad', 'problema', 'arreglo'],
        properties: { n: { type: 'integer' }, escena: { type: ['integer', 'null'] }, regla: { type: 'string', pattern: '^H-C[1-6]$' }, gravedad: { type: 'string', enum: ['bloquea', 'mejora'] }, problema: { type: 'string' }, arreglo: { type: 'string' } } } },
      oyente_descartadas: { type: 'array', items: { type: 'object', required: ['escena', 'motivo'], properties: { escena: { type: ['integer', 'null'] }, motivo: { type: 'string' } } } },
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
  animacion: {
    type: 'object', required: ['id', 'archivo', 'check', 'reutilizada'],
    properties: {
      id: { type: 'string', pattern: '^[a-z0-9]+(-[a-z0-9]+)*$' }, archivo: { type: 'string' }, check: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, lecturas: { type: 'integer' }, vueltas: { type: 'integer' }, reutilizada: { type: 'boolean' },
    },
  },
}

const rel = (p) => String(p || '').replace(/^\.\//, '').replace(/^.*?\/(?=sesiones\/)/, '')
const fallasDe = (r, gate) => (r.fallas && r.fallas.length) ? r.fallas : [`el gate \`${gate}\` falló sin detalle: córrelo y copia sus líneas FALLA`]

// En retoque las fases 1–5 no corren: el gancho ya está en guion.json y la cronología en historia.json
let ENC = null, ver = [], K = { candidatos: [] }, SEL = { ganador: null, segundo: null, por_que: 'retoque: el gancho ya estaba elegido', faltas: [] }
if (!RETOQUE) {
// ── 1. Encuadre ──────────────────────────────────────────────────────────────
phase('Encuadre')
ENC = await conReparacion('Encuadre', (fallos) => agentRol(
  `Eres el editor de /historia (lee referencias/roles/historia-editor.md). TRABAJO = ${trabajo} · tema: «${tema}». ` +
    `Escribe ${trabajo}/encuadre.json: pregunta central, protagonista (1–3 nombres con que se nombra a quien protagoniza: la marca, la persona, la empresa; el gancho lo nombra), ` +
    `revelaciones (3–5 frases: lo que el video revela y el gancho NO puede decir —la respuesta a la pregunta, de qué está hecho, quién lo hizo, cómo terminó— con sus números tal cual: el gate veta esos dígitos en el gancho), ` +
    `fotos_clave (2–4 imágenes que la historia necesita; la PRIMERA es siempre la del protagonista: el producto, el edificio, la persona), arco (el que le toca a ESTA historia; abierto), ${CAPITULOS_MIN}–${CAPITULOS_MAX} capítulos cada uno con su pregunta, ${EJES_MIN}–${EJES_MAX} ejes con id de 2–6 letras, paleta del tema, dominios_propios (también el sitio de la marca), no_afirma y sensibles.` +
    (fallos.length ? ` REPARACIÓN: tu retorno anterior falló: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-editor', schema: S.encuadre, phase: 'Encuadre', label: 'editor' }),
(r) => [
  ...(rel(r.archivo) !== `${trabajo}/encuadre.json` ? [`archivo debe ser ${trabajo}/encuadre.json`] : []),
  ...(r.capitulos.length < CAPITULOS_MIN || r.capitulos.length > CAPITULOS_MAX ? [`${r.capitulos.length} capítulos (van ${CAPITULOS_MIN}–${CAPITULOS_MAX})`] : []),
  ...(r.ejes.length < EJES_MIN || r.ejes.length > EJES_MAX ? [`${r.ejes.length} ejes (van ${EJES_MIN}–${EJES_MAX})`] : []),
  ...(new Set(r.ejes).size !== r.ejes.length ? ['ids de eje repetidos'] : []),
  ...(!r.protagonista.some((x) => x.trim()) ? ['protagonista vacío (el nombre de la marca, la persona o la empresa)'] : []),
  ...(r.revelaciones.length < 3 || r.revelaciones.length > 5 ? [`${r.revelaciones.length} revelaciones (van 3–5: lo que el video paga y el gancho no dice)`] : []),
  ...(!r.fotos_clave.some((x) => x.trim()) ? ['fotos_clave vacío (la primera es la imagen del protagonista)'] : []),
], 1)
log(`Encuadre: «${ENC.pregunta}» · arco ${ENC.arco} · ${ENC.capitulos.join(' / ')} · ejes ${ENC.ejes.join(', ')} · paleta ${ENC.paleta}${ENC.justicia ? ' · justicia' : ''}`)

// ── 2–3. Investigación ⇢ Verificación (pipeline por eje) ─────────────────────
const verificaciones = await pipeline(ENC.ejes,
  (eje) => conReparacion(`investigación ${eje}`, (fallos) => agentRol(
    `Eres el investigador del eje «${eje}» de la historia «${tema}» (lee referencias/roles/historia-investigador.md). TRABAJO = ${trabajo}. ` +
      `Insumo: python3 scripts/historia.py digesto ${trabajo} --para investigador --eje ${eje}. Guarda cada fuente con python3 scripts/historia.py leer <url>; ` +
      `escribe ${trabajo}/hallazgos_${eje}.json (ids ${eje}-h01, ${eje}-c01, ${eje}-q01, ${eje}-f01).` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'historia-investigador', schema: S.hallazgos, phase: 'Investigación', label: `investiga-${eje}` }),
  (r) => [...(r.eje !== eje ? [`eje ${r.eje} ≠ ${eje}`] : []), ...(r.hechos < 2 ? [`solo ${r.hechos} hechos: busca más (≥ 2 por eje)`] : [])], 1),
  (hz, eje) => conReparacion(`verificación ${eje}`, (fallos) => agentRol(
    `Eres el verificador del eje «${eje}» de la historia «${tema}» (lee referencias/roles/historia-verificador.md). TRABAJO = ${trabajo}. ` +
      `Insumo: python3 scripts/historia.py digesto ${trabajo} --para verificador --eje ${eje} (${hz.hechos} hechos, ${hz.cifras} cifras, ${hz.citas} citas, ${hz.fotos} fotos candidatas). ` +
      `${ENC.justicia ? 'Historia de JUSTICIA: cada persona señalada lleva casos[] con su estado a hoy y su fuente. ' : ''}` +
      `Fotos: ≥ 2 por eje con python3 scripts/historia.py foto; la del PROTAGONISTA es obligatoria (H12): el digesto marca con * las og:image de tus fuentes que lo nombran, bájalas con historia.py foto ${trabajo} --id ${eje}-fNN --de-fuente <url> --descripcion "…" --protagonista. ` +
      `Escribe ${trabajo}/verificacion_${eje}.json (fotos[] con los ids) y corre python3 scripts/historia.py hechos ${trabajo} --check --eje ${eje} hasta 0 fallas. Devuelve también protagonista (cuántas de tus fotos lo muestran).` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'historia-verificador', schema: S.verificacion, phase: 'Verificación', label: `verifica-${eje}` }),
  (r) => [...(r.eje !== eje ? [`eje ${r.eje} ≠ ${eje}`] : []), ...(r.gate !== 'ok' ? fallasDe(r, `historia.py hechos --check --eje ${eje}`) : [])], 1)
    .catch((e) => { avisar(`AVISO: el eje ${eje} no quedó verificado (${String(e.message).split('\n')[0]}).`); return null }))
ver = verificaciones.filter(Boolean)
const publicables = ver.reduce((s, v) => s + v.confirmados + v.en_disputa, 0)
log(`Verificación: ${ver.map((v) => `${v.eje} ${v.confirmados}✓ ${v.en_disputa}≈ ${v.descartados}✗ · ${v.fotos} fotos · ${v.protagonista || 0} del protagonista`).join(' · ')}`)
if (publicables < HECHOS_MIN) fail(`Solo ${publicables} hechos publicables (van ≥ ${HECHOS_MIN}): la historia no se sostiene todavía.`)

// ── 3b. La foto del protagonista (H12): sin ella consolidar fallaría dentro de video-gancho, que no tiene web ──────
if (ver.reduce((s, v) => s + (v.protagonista || 0), 0) === 0) {
  const F = await conReparacion('foto del protagonista', (fallos) => agentRol(
    `Eres el verificador de /historia (lee referencias/roles/historia-verificador.md). TRABAJO = ${trabajo} · «${tema}». SOLO UNA TAREA: la foto del PROTAGONISTA (H12). ` +
      `Corre python3 scripts/historia.py hechos ${trabajo} --check: su FALLA H12 imprime las og:image de fuentes ya leídas con el comando foto --de-fuente listo; si no hay, busca en Commons "${ENC.protagonista[0]}" o la prensa de la empresa (≤ 4 búsquedas o descargas). ` +
      `Baja 1–2 con --protagonista (id <eje>-fNN del eje de esa fuente), añade los ids a fotos[] de esa verificacion_<eje>.json y repite hechos --check hasta 0 fallas. Devuelve el retorno de ese eje con protagonista = cuántas fotos lo muestran.` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'historia-verificador', schema: S.verificacion, phase: 'Verificación', label: 'foto-protagonista' }),
  (r) => [...(r.gate !== 'ok' ? fallasDe(r, 'historia.py hechos --check') : []), ...(!(r.protagonista > 0) ? ['ninguna foto marcada --protagonista'] : [])], 1)
    .catch((e) => { avisar(`AVISO: sigue sin foto del protagonista (${String(e.message).split('\n')[0]}); consolidar fallará H12: bájala tú y relanza.`); return null })
  if (F) log(`Foto del protagonista: ${F.protagonista} (eje ${F.eje})`)
}

// ── 4. Ganchos (consolidar + candidatos) ─────────────────────────────────────
phase('Ganchos')
const invocarGanchos = (fallos, faltasSel) => agentRol(
  `MODO HISTORIA (lee referencias/ganchos.md y la sección «Modo historia» de referencias/roles/video-gancho.md). TRABAJO = ${trabajo} · «${tema}».\n` +
    `PRIMERO corre python3 scripts/historia.py consolidar ${trabajo} (cronología y base; exit 1 = pocos hechos: devuélvelo en fallas). ` +
    `Lee SOLO python3 scripts/historia.py digesto ${trabajo} --para gancho. Escribe ${trabajo}/ganchos.json con ${CANDIDATOS_MIN}–${CANDIDATOS_MAX} candidatos de FAMILIAS DISTINTAS (${FAMILIAS.join(', ')}), TODOS con visual foto (la foto verificada a sangre que cubre la pantalla), TODOS nombrando al protagonista del encuadre (H10), cada uno con el momento de la historia (el problema que la hizo nacer, la persona, la decisión) y NUNCA la respuesta que el video paga ni el detalle técnico que explica después (de qué está hecho, cómo terminó), sin lo que bloquea la rotación. ` +
    `Corre python3 scripts/historia.py ganchos ${trabajo} --check hasta exit 0 (≤ 3 intentos).\n` +
    (faltasSel ? `EL CRÍTICO NO APROBÓ NINGUNO; rehaz los señalados:\n - ${faltasSel.map((f) => `[${f.candidato} · ${f.regla}] ${f.problema} → ${f.arreglo}`).join('\n - ')}\n` : '') +
    (fallos.length ? `REPARACIÓN: ${fallos.join('; ')}\n` : '') +
    'Retorno: {archivo, gate, fallas[], hechos (publicables según consolidar), candidatos[]{id, familia, visual, pantalla}, intentos}.',
  { agentType: 'video-gancho', schema: S.ganchos, phase: 'Ganchos', label: faltasSel ? 'ganchos-rehacer' : 'ganchos' })
const validarGanchos = (r) => {
  if (r.gate !== 'ok') return fallasDe(r, 'historia.py ganchos --check')
  const cs = r.candidatos
  return [
    ...(rel(r.archivo) !== `${trabajo}/ganchos.json` ? [`archivo debe ser ${trabajo}/ganchos.json`] : []),
    ...(cs.length < CANDIDATOS_MIN || cs.length > CANDIDATOS_MAX ? [`${cs.length} candidatos (van ${CANDIDATOS_MIN}–${CANDIDATOS_MAX})`] : []),
    ...(new Set(cs.map((c) => c.familia)).size !== cs.length ? ['familias repetidas'] : []),
    ...(cs.some((c) => c.visual !== 'foto') ? ['todos los candidatos abren con visual foto (la foto a sangre)'] : []),
  ]
}
let K = await conReparacion('Ganchos', (f) => invocarGanchos(f, null), validarGanchos, 2)
log(`Ganchos: ${K.candidatos.map((c) => `${c.id} ${c.familia}/${c.visual} «${c.pantalla}»`).join(' · ')}`)

// ── 5. Selección ─────────────────────────────────────────────────────────────
phase('Selección')
const seleccionar = (vuelta) => conReparacion('Selección', (fallos) => agentRol(
  `MODO SELECCIÓN DE GANCHO de una HISTORIA (lee «Modo selección de gancho» y «Modo historia» de referencias/roles/video-critico.md). TRABAJO = ${trabajo} · vuelta ${vuelta}. ` +
    `Lee SOLO referencias/ganchos.md, ${trabajo}/ganchos.json y python3 scripts/historia.py digesto ${trabajo} --para gancho. Cada candidato primero en silencio y luego con la voz; puntúa silencio, reserva (no regala ninguna revelación del digesto: cuenta el momento, la persona, el problema; un candidato que dice una revelación tiene reserva ≤ 2 y no puede ganar), tension, alineacion, honestidad y novedad; ganador (ninguno ≤ 2) y segundo de otra familia, o ganador null con faltas. Escribe ${trabajo}/seleccion.json.` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video-critico', schema: S.seleccion, phase: 'Selección', label: `seleccion-${vuelta}` }),
(r) => {
  const ids = K.candidatos.map((c) => c.id)
  return [
    ...(r.ganador !== null && !ids.includes(r.ganador) ? [`ganador «${r.ganador}» no es un candidato`] : []),
    ...(r.ganador !== null && (r.segundo === r.ganador || (r.segundo !== null && !ids.includes(r.segundo))) ? ['segundo debe ser otro candidato'] : []),
    ...(r.ganador === null && !r.faltas.length ? ['sin ganador: escribe las faltas con su arreglo'] : []),
    ...(r.ganador !== null && !(((r.puntajes || {})[r.ganador] || {}).reserva >= PUNTAJE_MIN) ? [`el ganador «${r.ganador}» necesita reserva ≥ ${PUNTAJE_MIN} (puntajes[id].reserva: no regala una revelación)`] : []),
  ]
}, 1)
SEL = await seleccionar(1)
if (SEL.ganador === null) {
  avisar(`Selección 1: ningún gancho aprobado → video-gancho rehace`)
  K = await conReparacion('Ganchos (rehacer)', (f, i) => invocarGanchos(f, i === 0 ? SEL.faltas : null), validarGanchos, 1)
  SEL = await seleccionar(2)
}
if (SEL.ganador === null) {
  avisar('AVISO: el crítico no aprobó ningún gancho: decide con el usuario antes de seguir.')
  return { trabajo, tema, veredicto: 'corregir', etapa: 'seleccion', faltas_pendientes: SEL.faltas, ganchos: K.candidatos, avisos: AVISOS_WF }
}
log(`Selección: gana ${SEL.ganador} · segundo ${SEL.segundo || '—'} · ${SEL.por_que}`)
}

// ── 6. Guion ─────────────────────────────────────────────────────────────────
phase('Guion')
const directivaBase = `Eres el guionista de /historia (lee referencias/roles/historia-guionista.md). TRABAJO = ${trabajo} · «${tema}». ` +
  `Lee SOLO python3 scripts/historia.py digesto ${trabajo} --para guionista. Corre python3 scripts/historia.py guion ${trabajo} --check hasta 0 fallas ` +
  `y devuelve TAL CUAL su última línea RETORNO (tipos trae el tipo de CADA escena en orden, sin el cierre). `
const directivaGuion = RETOQUE
  ? directivaBase + `RETOQUE: ${trabajo}/guion.json ya existe, aprobado y con voz grabada. Notas del usuario: «${notas}». Aplica SOLO lo que piden ` +
    `(si piden otro gancho: python3 scripts/historia.py ganchos ${trabajo} --usar <id> y relee el hilo entero, H11). Conserva palabra por palabra la voz ` +
    `(texto) de toda escena que no necesite cambiar: cada voz cambiada se vuelve a generar y cuesta créditos; lo que las notas piden conservar (el cierre, ` +
    `una escena, «ninguna voz») NO se toca ni por una falta del crítico. Si el gate te obliga a cambiar una voz (H11…), el cambio mínimo. Añade al RETORNO ` +
    `voces_cambiadas: [n de cada escena cuya voz cambió; el cierre es la escena N+1, como en locucion.json]. `
  : directivaBase + `PRIMERO python3 scripts/historia.py ganchos ${trabajo} --usar (el gancho ${SEL.ganador} pasa a la escena 1 y NO lo cambias). ` +
    `Escribe ${trabajo}/guion.json: promesa con revela (la R que paga), ${CAPITULOS_MIN}–${CAPITULOS_MAX} capítulos que responden su pregunta del encuadre, ` +
    `escenas foto, cita, tarjeta con grafico, golpe, explica, un giro, cierre legado (o consecuencia si termina mal) y captions; apunta a 150 s (135–165). `
const voces = new Set()
const sumaVoces = (r) => { if (r) (r.voces_cambiadas || []).forEach((n) => voces.add(n)); return r }
const validarGuion = (r) => {
  if (r.gate !== 'ok') return fallasDe(r, 'historia.py guion --check')
  return [
    ...(rel(r.archivo) !== `${trabajo}/guion.json` ? [`archivo debe ser ${trabajo}/guion.json`] : []),
    ...(r.tipos[0] !== 'gancho' ? ['la escena 1 es el gancho'] : []),
    ...(r.capitulos < CAPITULOS_MIN || r.capitulos > CAPITULOS_MAX ? [`${r.capitulos} capítulos (van ${CAPITULOS_MIN}–${CAPITULOS_MAX})`] : []),
    ...(r.estimado_s > DURACION_MAX_S ? [`${r.estimado_s} s estimados (máximo ${DURACION_MAX_S})`] : []),
    ...(r.tipos.length !== r.escenas ? [`tipos trae ${r.tipos.length} elementos: debe traer el tipo de CADA escena, en orden (${r.escenas})`] : []),
    ...(r.tipos.length === r.escenas ? r.explica_sin_animacion.filter((n) => r.tipos[n - 1] !== 'explica').map((n) => `la escena ${n} no es explica`) : []),
  ]
}
let G = sumaVoces(await conReparacion('Guion', (fallos) => agentRol(directivaGuion + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-guionista', schema: S.guion, phase: 'Guion', label: 'guionista' }), validarGuion, 2))
log(`Guion: ${G.escenas} escenas · ${G.capitulos} capítulos · ${G.estimado_s} s estimados${RETOQUE ? ` · voces cambiadas ${[...voces].join(', ') || 'ninguna'}` : ''}`)

// ── 6b. Oyente ingenuo: solo oye la voz y lee la pantalla; lo que no entiende va al crítico ─────────────────────────
const oir = (vuelta) => conReparacion(`oyente ${vuelta}`, (fallos) => agentRol(
  `Eres el OYENTE INGENUO de /historia (lee referencias/roles/historia-oyente.md). TRABAJO = ${trabajo}. ` +
    `Lee SOLO python3 scripts/historia.py digesto ${trabajo} --para oyente (la voz en orden y lo que hay en pantalla; no sabes nada más de la historia). ` +
    `Una pasada, en orden, sin volver atrás. Escribe ${trabajo}/oyente.json y devuelve lo mismo.` + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-oyente', schema: S.oyente, phase: 'Oyente', label: `oyente-${vuelta}` }),
(r) => [
  ...(rel(r.archivo) !== `${trabajo}/oyente.json` ? [`archivo debe ser ${trabajo}/oyente.json`] : []),
  ...(!r.de_que.trim() ? ['de_que: una oración'] : []),
  ...r.confusiones.filter((c) => c.escena < 1 || c.escena > G.escenas + 1).map((c) => `confusión en la escena ${c.escena}: no existe (1–${G.escenas + 1})`),
], 1).catch((e) => { avisar(`AVISO: el oyente no terminó (${String(e.message).split('\n')[0]}); la crítica va sin oyente.json.`); return null })
phase('Oyente')
let O = await oir(1)
if (O) log(`Oyente: «${O.de_que}» · ${O.confusiones.length} confusiones · ${O.saltos.length} saltos · ${O.repeticiones.length} repeticiones · ${O.pregunta_sin_responder.length} sin responder`)

// ── 7. Crítica (≤ 2 vueltas; 1 en retoque) ───────────────────────────────────
phase('Crítica')
const validarCritica = (r, O) => {
  const f = []
  for (const k of PUNTAJES) if (r.puntajes[k] <= 2 && !r.faltas.some((x) => x.gravedad === 'bloquea' && x.regla === REGLA_DE[k])) f.push(`puntaje ${k} = ${r.puntajes[k]} sin falta «bloquea» de ${REGLA_DE[k]}`)
  const bloquea = r.faltas.some((x) => x.gravedad === 'bloquea') || PUNTAJES.some((k) => r.puntajes[k] < PUNTAJE_MIN)
  if ((r.veredicto === 'pasa') === bloquea) f.push(`veredicto ${r.veredicto} incoherente con las faltas y los puntajes`)
  const atendida = (n) => r.faltas.some((x) => x.escena === n) || (r.oyente_descartadas || []).some((d) => d.escena === n)
  for (const c of (O ? O.confusiones : [])) if (!atendida(c.escena)) f.push(`la confusión del oyente en la escena ${c.escena} («${c.que_no_entendi}») no tiene falta ni entrada en oyente_descartadas`)
  for (const s of (O ? O.saltos : [])) if (!atendida(s.a)) f.push(`el salto ${s.de}→${s.a} del oyente no tiene falta en la escena ${s.a} ni entrada en oyente_descartadas`)
  return f
}
let critica = null, previas = []
for (let vuelta = 1; vuelta <= VUELTAS + 1; vuelta++) {
  if (vuelta > 1) O = await oir(vuelta)   // la corrección cambió la voz: el oyente vuelve a oírla
  critica = await conReparacion(`crítica ${vuelta}`, (fallos) => agentRol(
    `MODO HISTORIA (lee la sección «Modo historia» de referencias/roles/video-critico.md). TRABAJO = ${trabajo}. Vuelta ${vuelta}. ` +
      `Insumos: ${trabajo}/guion.json, ${trabajo}/locucion.json, ` +
      (O ? `${trabajo}/oyente.json (lo que un oyente que SOLO oyó la voz no entendió: cada confusión y cada salto se resuelve con una falta bloquea de H-C3 ` +
           `—H-C2 si es la promesa— con su arreglo exacto, o se justifica en critica.json → oyente_descartadas[]{escena, motivo}; sus repeticiones y preguntas sin responder las juzgas tú) y ` : '') +
      `python3 scripts/historia.py digesto ${trabajo} --para critico (cronología, preguntas de los capítulos y revelaciones: en H-C2 comprueba que la escena promesa.pago ` +
      `cuenta la revelación promesa.revela y que cada capítulo responde su pregunta o la deja abierta a propósito; en H-C6, legado = gente haciendo algo hoy, no es neutro). ` +
      (RETOQUE ? `RETOQUE con notas del usuario: «${notas}». Lo que las notas piden conservar (el cierre, una escena, «ninguna voz») el usuario ya lo aprobó: no va como ` +
                 `falta bloquea; si el oyente lo confunde, va en oyente_descartadas con el motivo «lo aprobó el usuario» y, si quieres, como mejora. ` : '') +
      `Escribe ${trabajo}/critica.json.` +
      (previas.length ? ` Faltas de la vuelta anterior (comprueba primero cada una): ${JSON.stringify(previas)}` : '') +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: `critica-${vuelta}` }), (r) => validarCritica(r, O), 1)
  log(`Crítica ${vuelta}: ${critica.veredicto} · ${PUNTAJES.map((k) => `${k} ${critica.puntajes[k]}`).join(' · ')}`)
  if (critica.veredicto === 'pasa' || vuelta > VUELTAS) break
  previas = critica.faltas.filter((x) => x.gravedad === 'bloquea')
  G = sumaVoces(await conReparacion(`corrección ${vuelta}`, (fallos) => agentRol(directivaGuion +
    ` CORRECCIÓN ${vuelta}: guion.json ya existe; corrige SOLO lo que bloquea (con el arreglo exacto), conserva las demás voces y repasa el gate: ${JSON.stringify(previas)}` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-guionista', schema: S.guion, phase: 'Crítica', label: `guionista-corrige-${vuelta}` }), validarGuion, 1))
}

// ── 7b. Mejoras: con «pasa», el guionista aplica las mejoras del crítico antes de gastar voz (sin otra crítica) ──
let mejorasNoAplicadas = critica.veredicto === 'pasa' ? critica.faltas.filter((x) => x.gravedad === 'mejora') : []
if (mejorasNoAplicadas.length) {
  const lista = mejorasNoAplicadas
  const M = await conReparacion('mejoras', (fallos) => agentRol(directivaGuion +
    ` MEJORAS: el crítico aprobó el guion; aplica estas mejoras (también las de voz: aún no se graba nada) con su arreglo exacto, sin tocar nada más: ${JSON.stringify(lista)}. ` +
    `ANTES copia ${trabajo}/guion.json a ${trabajo}/guion.previo.json. Aplica una por una y corre python3 scripts/historia.py guion ${trabajo} --check; ` +
    `una mejora que el gate no deja pasar (ni con un ajuste mínimo) la deshaces y va en no_aplicadas con su motivo. Si al final el gate no llega a 0 fallas, ` +
    `restaura guion.previo.json, vuelve a correr el gate (locucion.json debe corresponder al guion final) y devuelve aplicadas: []. Devuelve aplicadas (los n de las mejoras) y no_aplicadas.` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-guionista', schema: S.mejoras, phase: 'Crítica', label: 'guionista-mejoras' }), validarGuion, 1)
    .catch((e) => { avisar(`AVISO: las mejoras no se aplicaron (${String(e.message).split('\n')[0]}); queda el guion aprobado.`); return null })
  if (M) {
    G = sumaVoces(M)
    mejorasNoAplicadas = lista.filter((x) => !M.aplicadas.includes(x.n)).map((x) => ({ ...x, motivo: (M.no_aplicadas.find((y) => y.n === x.n) || {}).motivo || 'no aplicada' }))
    log(`Mejoras: ${M.aplicadas.length} aplicadas · ${mejorasNoAplicadas.length} no aplicadas`)
  }
}

// ── 8. Animación (solo si el crítico aprueba) ────────────────────────────────
phase('Animación')
const animaciones = []
if (critica.veredicto === 'pasa') {
  for (const n of G.explica_sin_animacion) {
    const r = await conReparacion(`animación escena ${n}`, (fallos) => agentRol(
      `MODO HISTORIA (lee referencias/roles/video-animador.md, también su «Modo historia»). TRABAJO = ${trabajo}. La escena ${n} de ${trabajo}/guion.json es explica con animacion null: lee su mecanismo, brief, titulo y pasos ahí (solo esa escena). ` +
        `Reutiliza del catálogo SOLO una del mismo mecanismo que cuente lo mismo (python3 scripts/animaciones.py --lista; el gate rechaza otro mecanismo y las de los últimos videos) o escribe video/animaciones/<id>.js con meta.mecanismo (queda como plantilla para otros videos; no copies la forma de cajas de cadena.js); --check, --registrar <id> --video ${trabajo.split('/').pop()} y --asignar ${trabajo} --escena ${n} --id <id>.` +
        (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
      { agentType: 'video-animador', schema: S.animacion, phase: 'Animación', label: `animacion-${n}` }),
    (x) => [...(x.archivo !== `video/animaciones/${x.id}.js` ? [`archivo debe ser video/animaciones/${x.id}.js`] : []),
      ...(x.check !== 'ok' && !(x.fallas || []).length ? ['check falla sin detalle'] : [])], 1).catch((e) => { avisar(`AVISO: la escena ${n} sigue sin animación (${String(e.message).split('\n')[0]}).`); return null })
    if (r) animaciones.push({ escena: n, id: r.id, reutilizada: r.reutilizada, check: r.check })
  }
}

return {
  trabajo, tema, veredicto: critica.veredicto, puntajes: critica.puntajes,
  faltas_pendientes: critica.faltas.filter((x) => x.gravedad === 'bloquea'),
  mejoras: critica.faltas.filter((x) => x.gravedad === 'mejora'),
  mejoras_no_aplicadas: mejorasNoAplicadas,
  encuadre: ENC ? { pregunta: ENC.pregunta, arco: ENC.arco, capitulos: ENC.capitulos, paleta: ENC.paleta, justicia: ENC.justicia, revelaciones: ENC.revelaciones } : null,
  verificacion: ver.map((v) => ({ eje: v.eje, confirmados: v.confirmados, en_disputa: v.en_disputa, descartados: v.descartados, fotos: v.fotos, protagonista: v.protagonista || 0, casos: v.casos || 0 })),
  gancho: { ganador: SEL.ganador, segundo: SEL.segundo, por_que: SEL.por_que },
  guion: { escenas: G.escenas, capitulos: G.capitulos, estimado_s: G.estimado_s, explica_sin_animacion: G.explica_sin_animacion },
  retoque: RETOQUE, voces_cambiadas: [...voces].sort((a, b) => a - b),
  oyente: O ? { de_que: O.de_que, promesa: O.promesa, confusiones: O.confusiones.length, saltos: O.saltos.length, repeticiones: O.repeticiones, pregunta_sin_responder: O.pregunta_sin_responder } : null,
  animaciones, avisos: AVISOS_WF,
}
