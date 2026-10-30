export const meta = {
  name: 'explica',
  description: 'Video explicativo para /explica (un concepto, un proceso o una regla en ~2 min): explica-editor (encuadre: la pregunta, la idea equivocada que casi todos tienen, el mecanismo y la oración que el oyente tiene que poder devolver, la leyenda de color, el glosario, el ejemplo conductor con sus modelos de la calculadora, las anclas de Guatemala, las revelaciones y 1–3 ejes; gate E1) → un explica-investigador por eje ⇢ su explica-verificador (pipeline; afirmaciones y cifras con cita guardada, segunda fuente o la oficial, cuatro veredictos; gate E2) → consolidar (la calculadora: los ejemplos ilustrativos los calcula el script, ej-cNN) → video-gancho en modo explica (4–5 candidatos; gate R1–R12) → video-critico elige → explica-guionista (PRIMERO la narración de corrido en tres actos: la pregunta, el mecanismo, en tu vida; DESPUÉS las escenas: cuenta (la pizarra), definición, explica, escala, tarjetas, rótulos de acto, secuencias de voz; gate E1–E12 + V1–V5, V9, F1–F8) → historia-oyente (oyente ingenuo que además explica de vuelta el mecanismo) → crítico en modo explica (claridad = la explicación devuelta casa con el mecanismo; ≤ 2 vueltas, acotadas desde la 2; arreglos probados que se aplican tal cual) → mejoras → video-animador por escena explica sin animación. 0 créditos de ElevenLabs.',
  whenToUse: 'Invocado por /explica <tema> DESPUÉS de `python3 scripts/explica.py preparar "<tema>"`. args: {trabajo, tema, permitir_fallback, desde, notas}. trabajo = sesiones/explica-<slug> (lo imprime preparar). Produce y aprueba <trabajo>/encuadre.json, hallazgos_*.json, verificacion_*.json, explicacion.json, ejemplos.json, base/, ganchos.json, seleccion.json, guion.json, locucion.json, oyente.json y critica.json; la voz, los tiempos, la grabación y el montaje los hace la sesión principal después. Si el crítico sigue en «corregir» tras 2 vueltas y sus faltas traen arreglos probados, se aplican y devuelve pasa con aprobado_por: arreglos_probados; si no, devuelve veredicto corregir + faltas_pendientes y el comando pregunta al usuario. desde: "guion" = salta a Guion (explicacion.json, ganchos.json y seleccion.json ya existen); desde: "retoque" + notas = guion.json aprobado y con voz: el guionista aplica solo las notas conservando las voces → gate → oyente → crítica (1 vuelta) → mejoras → animación; devuelve voces_cambiadas.',
  phases: [
    { title: 'Encuadre', detail: 'explica-editor: encuadre.json con la pregunta, la intuición (la idea equivocada), el mecanismo y su frase, la leyenda de color, el glosario, los personajes del ejemplo, los ejemplos (modelos de la calculadora), las anclas de Guatemala, las revelaciones, 1–3 ejes, la paleta, no_afirma y lo sensible; gate explica.py encuadre --check (E1)' },
    { title: 'Investigación', detail: 'un explica-investigador por eje en paralelo: afirmaciones (definición, regla, proceso, norma) y cifras de Guatemala con la cita literal del texto guardado (explica.py leer) → hallazgos_<eje>.json' },
    { title: 'Verificación', detail: 'un explica-verificador por eje en cuanto su investigador termina: segunda fuente o la oficial, vigencia, cuatro veredictos (confirmado | una_fuente | en_disputa | no_confirmado) → verificacion_<eje>.json; gate explica.py afirmaciones --check (E2)' },
    { title: 'Ganchos', detail: 'consolidar (explicacion.json, base/ y la calculadora: ejemplos.json y las cifras ej-cNN) en el código; video-gancho en modo explica: 4–5 candidatos de familias distintas (contraste, paradoja, pregunta, tu, escala, resultado) que plantean la pregunta sin dar el mecanismo; gate explica.py ganchos --check (R1–R12)' },
    { title: 'Selección', detail: 'video-critico en modo selección: silencio, reserva, tension, alineacion, honestidad, novedad; ganador y segundo en seleccion.json; si ninguno llega a 3, video-gancho rehace una vez' },
    { title: 'Guion', detail: 'explica-guionista: ganchos --usar → PRIMERO guion.narracion (tres actos: la pregunta, el mecanismo, en tu vida; explica.py narracion --check) → DESPUÉS las escenas sin cambiar una palabra (intuicion y corrige, cuenta, definicion, explica, escala, tarjetas, giro, rótulos, secuencias, cierre de consecuencia, captions); gate explica.py guion --check (E1–E12 + V1–V5, V9, F1–F8) y su RETORNO; en retoque aplica las notas y conserva las voces' },
    { title: 'Oyente', detail: 'historia-oyente en modo explica: la narración de corrido y luego la pantalla por escena (explica.py digesto --para oyente); confusiones, saltos, repeticiones, preguntas sin responder y explicacion_devuelta (el mecanismo con sus palabras)' },
    { title: 'Crítica', detail: 'video-critico en modo explica: gancho, claridad (la explicación devuelta del oyente casa con mecanismo_frase), intuicion (se rompe de forma visible), flujo, precision (ejemplos como ejemplos, datos con fecha, sin consejo), cierre; ≤ 2 vueltas (1 en retoque), acotadas desde la 2; arreglos probados (explica.py probar) que el guionista aplica tal cual (explica.py aplicar); con «pasa», las mejoras y el oyente las vuelve a oír' },
    { title: 'Animación', detail: 'video-animador por cada escena explica con animacion null (solo si el crítico aprueba): reusa del catálogo una del mismo mecanismo o escribe video/animaciones/<id>.js, --check, --registrar y --asignar' },
  ],
}

// Guías: referencias/flujo-explica.md, referencias/roles/explica-{editor,investigador,verificador,guionista}.md y el «Modo
// explica» de referencias/roles/video-{gancho,critico,animador}.md e historia-oyente.md. Los agentes escriben su artefacto
// COMPLETO en <trabajo>/ y devuelven aquí un resumen validado por schema; los gates de contenido viven en
// scripts/explica.py (E1–E12, que llama a video.py para V1–V5, V9 y F1–F8). TIPOS, FAMILIAS, VISUALES, PUNTAJES y MODELOS
// son espejos literales de scripts/explica.py (los vigila scripts/check_workflows.py, W13).

const TIPOS = ['gancho', 'tarjeta', 'golpe', 'definicion', 'adivina', 'mapa', 'ranking', 'escala', 'tiempo', 'explica', 'cuenta']
const FAMILIAS = ['contraste', 'paradoja', 'pregunta', 'tu', 'escala', 'resultado']
const VISUALES = ['cifra', 'llenado', 'pareja', 'figuras']
const PUNTAJES = ['gancho', 'claridad', 'intuicion', 'flujo', 'precision', 'cierre']
const MODELOS = ['compuesto', 'simple', 'aporte_periodico', 'regla72', 'tasa_real', 'cuota', 'porcentaje', 'proporcion']
const REGLA_DE = { gancho: 'E-C1', claridad: 'E-C2', intuicion: 'E-C3', flujo: 'E-C4', precision: 'E-C5', cierre: 'E-C6' }
const EJES_MIN = 1, EJES_MAX = 3, CANDIDATOS_MIN = 4, CANDIDATOS_MAX = 5, DURACION_MAX_S = 180
const VUELTAS_CRITICA = 2, PUNTAJE_MIN = 3, SEGUN_MAX = 2

// ── Argumentos ───────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { trabajo: args } : (args || {})
const trabajo = String(A.trabajo || '').replace(/\/+$/, '')
if (!/^sesiones\/(explica-[a-z0-9-]+|_fixture_explica\/[a-z0-9_-]+)$/.test(trabajo)) throw new Error('args.trabajo debe ser sesiones/explica-<slug> (la última línea que imprime `python3 scripts/explica.py preparar "<tema>"`).')
const tema = String(A.tema || '').trim()
if (!tema) throw new Error('args.tema: el tema del video, tal como lo dio el usuario.')
const DESDE = String(A.desde || '')
if (!['', 'guion', 'retoque'].includes(DESDE)) throw new Error('args.desde: "guion" (saltar al guion) o "retoque" (guion.json aprobado en TRABAJO + args.notas con lo que pidió el usuario).')
const RETOQUE = DESDE === 'retoque', DESDE_GUION = DESDE === 'guion'
const notas = String(A.notas || '').trim()
if (RETOQUE && !notas) throw new Error('args.notas: en modo retoque, lo que pidió el usuario (otro gancho, reescribir la escena 5, otro cierre…).')
const VUELTAS = RETOQUE ? 1 : VUELTAS_CRITICA

// <comun>
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
    type: 'object', required: ['archivo', 'pregunta', 'intuicion', 'mecanismo', 'mecanismo_frase', 'leyenda', 'glosario', 'ejemplos', 'anclas', 'revelaciones', 'ejes', 'paleta', 'sensible'],
    properties: {
      archivo: { type: 'string', pattern: 'encuadre\\.json$' }, pregunta: { type: 'string' }, intuicion: { type: 'string' },
      mecanismo: { type: 'string' }, mecanismo_frase: { type: 'string' },
      leyenda: { type: 'array', items: { type: 'string' } }, glosario: { type: 'array', items: { type: 'string' } },
      ejemplos: { type: 'array', items: { type: 'string' } }, anclas: { type: 'array', items: { type: 'string' } },
      revelaciones: { type: 'array', items: { type: 'string' } },
      ejes: { type: 'array', items: { type: 'string', pattern: '^[a-z]{2,4}$' } }, paleta: { type: 'string' }, sensible: { type: 'string' },
    },
  },
  hallazgos: {
    type: 'object', required: ['eje', 'archivo', 'afirmaciones', 'cifras', 'citas'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string', pattern: 'hallazgos_[a-z]+\\.json$' },
      afirmaciones: { type: 'integer' }, cifras: { type: 'integer' }, citas: { type: 'integer' },
      huecos: { type: 'array', items: { type: 'string' } }, busquedas: { type: 'integer' }, lecturas: { type: 'integer' },
    },
  },
  verificacion: {
    type: 'object', required: ['eje', 'archivo', 'gate', 'confirmados', 'una_fuente', 'en_disputa', 'no_confirmados'],
    properties: {
      eje: { type: 'string' }, archivo: { type: 'string', pattern: 'verificacion_[a-z]+\\.json$' },
      gate: { type: 'string', enum: ['ok', 'falla'] }, fallas: { type: 'array', items: { type: 'string' } },
      confirmados: { type: 'integer' }, una_fuente: { type: 'integer' }, en_disputa: { type: 'integer' }, no_confirmados: { type: 'integer' },
    },
  },
  ganchos: {
    type: 'object', required: ['archivo', 'gate', 'candidatos', 'intentos'],
    properties: {
      archivo: { type: 'string', pattern: 'ganchos\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } },
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
    type: 'object', required: ['archivo', 'gate', 'escenas', 'tipos', 'actos', 'rotulos', 'palabras', 'segun', 'intuicion', 'corrige', 'ilustrativas', 'estimado_s', 'explica_sin_animacion'],
    properties: {
      archivo: { type: 'string', pattern: 'guion\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, escenas: { type: 'integer' },
      tipos: { type: 'array', items: { type: 'string', enum: TIPOS } }, estimado_s: { type: 'number' },
      actos: { type: 'integer' }, rotulos: { type: 'integer' }, palabras: { type: 'integer' }, segun: { type: 'integer' },
      intuicion: { type: ['integer', 'null'] }, corrige: { type: ['integer', 'null'] },
      ilustrativas: { type: 'array', items: { type: 'integer' } }, secuencias: { type: 'integer' },
      explica_sin_animacion: { type: 'array', items: { type: 'integer' } },
      voces_cambiadas: { type: 'array', items: { type: 'integer' } },
      arreglos_rechazados: { type: 'array', items: { type: 'object', required: ['n', 'falla'], properties: { n: { type: 'integer' }, falla: { type: 'string' } } } },
    },
  },
  critica: {
    type: 'object', required: ['archivo', 'vuelta', 'veredicto', 'puntajes', 'faltas'],
    properties: {
      archivo: { type: 'string', pattern: 'critica\\.json$' }, vuelta: { type: 'integer' }, veredicto: { type: 'string', enum: ['pasa', 'corregir'] },
      puntajes: { type: 'object', required: PUNTAJES, properties: Object.fromEntries(PUNTAJES.map((k) => [k, { type: 'integer', minimum: 1, maximum: 5 }])) },
      bloqueantes: { type: 'integer' }, mejoras: { type: 'integer' },
      faltas: { type: 'array', items: { type: 'object', required: ['regla', 'gravedad', 'problema', 'arreglo'],
        properties: { n: { type: 'integer' }, escena: { type: ['integer', 'null'] }, regla: { type: 'string', pattern: '^E-C[1-6]$' }, gravedad: { type: 'string', enum: ['bloquea', 'mejora'] }, problema: { type: 'string' }, arreglo: { type: 'string' },
          probado: { type: 'boolean' }, cambios: { type: 'array', items: { type: 'object' } } } } },
      oyente_descartadas: { type: 'array', items: { type: 'object', required: ['escena', 'motivo'], properties: { escena: { type: ['integer', 'null'] }, pregunta: { type: 'string' }, motivo: { type: 'string' } } } },
    },
  },
  oyente: {
    type: 'object', required: ['archivo', 'de_que', 'promesa', 'confusiones', 'saltos', 'repeticiones', 'pregunta_sin_responder', 'explicacion_devuelta'],
    properties: {
      archivo: { type: 'string', pattern: 'oyente\\.json$' }, de_que: { type: 'string' }, explicacion_devuelta: { type: 'string' },
      promesa: { type: 'object', required: ['me_prometio', 'me_dio'], properties: { me_prometio: { type: 'string' }, me_dio: { type: 'string' } } },
      confusiones: { type: 'array', items: { type: 'object', required: ['escena', 'cita_de_la_voz', 'que_no_entendi'],
        properties: { escena: { type: 'integer' }, cita_de_la_voz: { type: 'string' }, que_no_entendi: { type: 'string' } } } },
      saltos: { type: 'array', items: { type: 'object', required: ['de', 'a', 'por_que'], properties: { de: { type: 'integer' }, a: { type: 'integer' }, por_que: { type: 'string' } } } },
      repeticiones: { type: 'array', items: { type: 'string' } },
      pregunta_sin_responder: { type: 'array', items: { type: 'string' } },
    },
  },
  mejoras: {
    type: 'object', required: ['archivo', 'gate', 'escenas', 'tipos', 'estimado_s', 'explica_sin_animacion', 'aplicadas', 'no_aplicadas'],
    properties: {
      archivo: { type: 'string', pattern: 'guion\\.json$' }, gate: { type: 'string', enum: ['ok', 'falla'] },
      fallas: { type: 'array', items: { type: 'string' } }, escenas: { type: 'integer' },
      tipos: { type: 'array', items: { type: 'string', enum: TIPOS } }, estimado_s: { type: 'number' },
      explica_sin_animacion: { type: 'array', items: { type: 'integer' } }, voces_cambiadas: { type: 'array', items: { type: 'integer' } },
      aplicadas: { type: 'array', items: { type: 'integer' } },
      no_aplicadas: { type: 'array', items: { type: 'object', required: ['n', 'motivo'], properties: { n: { type: 'integer' }, motivo: { type: 'string' } } } },
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
const sh = (s) => String(s).replace(/'/g, "'\\''")

let ENC = null, ver = [], K = { candidatos: [] }, SEL = { ganador: null, segundo: null, por_que: `${DESDE}: el gancho ya estaba elegido (seleccion.json)`, faltas: [] }
if (!RETOQUE && !DESDE_GUION) {
// ── 1. Encuadre ──────────────────────────────────────────────────────────────
phase('Encuadre')
ENC = await conReparacion('Encuadre', (fallos) => agentRol(
  `Eres el editor de /explica (lee referencias/roles/explica-editor.md). TRABAJO = ${trabajo} · tema: «${tema}». ` +
    `Escribe ${trabajo}/encuadre.json: pregunta (como la haría alguien en la calle), intuicion (la idea equivocada que casi todos tienen, dicha con justicia, ≤ 22 palabras), ` +
    `mecanismo (de MECANISMOS_EXPLICA: lo que HACE el fenómeno) y mecanismo_frase (la oración que quien vea el video tiene que poder devolver), leyenda (2–4 {concepto, papel: tenue|ink|acento}: el código de color de TODO el video), ` +
    `glosario (≤ 3 {termino, definicion}), personajes (0–2 del ejemplo conductor), ejemplos (modelos de la calculadora: ${MODELOS.join(', ')}; parámetros ilustrativos o {cifra: "<eje>-cNN"}; ≤ 4 ilustrativos), ` +
    `anclas (≥ 1 dato real de Guatemala para el acto 3), revelaciones (lo que el video paga y el gancho no dice: la otra cara del mecanismo), ${EJES_MIN}–${EJES_MAX} ejes {id de 2–4 letras, nombre, preguntas, fuentes}, paleta, no_afirma y sensible (financiero|salud|legal|ninguno). ` +
    `Corre python3 scripts/explica.py encuadre ${trabajo} --check hasta 0 fallas.` +
    (fallos.length ? ` REPARACIÓN: tu retorno anterior falló: ${fallos.join('; ')}.` : ''),
  { agentType: 'explica-editor', schema: S.encuadre, phase: 'Encuadre', label: 'editor' }),
(r) => [
  ...(rel(r.archivo) !== `${trabajo}/encuadre.json` ? [`archivo debe ser ${trabajo}/encuadre.json`] : []),
  ...(r.ejes.length < EJES_MIN || r.ejes.length > EJES_MAX ? [`${r.ejes.length} ejes (van ${EJES_MIN}–${EJES_MAX})`] : []),
  ...(new Set(r.ejes).size !== r.ejes.length ? ['ids de eje repetidos'] : []),
  ...(!r.intuicion.trim() ? ['intuicion vacía: la idea equivocada que el video rompe'] : []),
  ...(!r.mecanismo_frase.trim() ? ['mecanismo_frase vacía: lo que el oyente tiene que poder devolver'] : []),
  ...(!r.anclas.length ? ['anclas vacías: ≥ 1 dato real de Guatemala'] : []),
  ...(!r.revelaciones.length ? ['revelaciones vacías: la promesa paga una'] : []),
  ...(!r.ejemplos.length ? ['ejemplos vacíos: ≥ 1 modelo de la calculadora'] : []),
], 1)
log(`Encuadre: «${ENC.pregunta}» · intuición «${ENC.intuicion}» · mecanismo ${ENC.mecanismo} · ejemplos ${ENC.ejemplos.join(', ')} · ejes ${ENC.ejes.join(', ')} · paleta ${ENC.paleta} · ${ENC.sensible}`)

// ── 2–3. Investigación ⇢ Verificación (pipeline por eje) ─────────────────────
const verificaciones = await pipeline(ENC.ejes,
  (eje) => conReparacion(`investigación ${eje}`, (fallos) => agentRol(
    `Eres el investigador del eje «${eje}» del video explicativo «${tema}» (lee referencias/roles/explica-investigador.md). TRABAJO = ${trabajo}. ` +
      `Insumo: python3 scripts/explica.py digesto ${trabajo} --para investigador --eje ${eje}. Guarda cada fuente con python3 scripts/explica.py leer <url>; ` +
      `escribe ${trabajo}/hallazgos_${eje}.json (ids ${eje}-a01, ${eje}-c01, ${eje}-q01; las cifras que el encuadre pide como {cifra: id}, con ESE id).` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'explica-investigador', schema: S.hallazgos, phase: 'Investigación', label: `investiga-${eje}` }),
  (r) => [...(r.eje !== eje ? [`eje ${r.eje} ≠ ${eje}`] : []), ...(r.afirmaciones + r.cifras < 1 ? ['ninguna afirmación ni cifra: busca más'] : [])], 1),
  (hz, eje) => conReparacion(`verificación ${eje}`, (fallos) => agentRol(
    `Eres el verificador del eje «${eje}» del video explicativo «${tema}» (lee referencias/roles/explica-verificador.md). TRABAJO = ${trabajo}. ` +
      `Insumo: python3 scripts/explica.py digesto ${trabajo} --para verificador --eje ${eje} (${hz.afirmaciones} afirmaciones, ${hz.cifras} cifras, ${hz.citas} citas). ` +
      `Cuatro veredictos: confirmado (2 grupos, o 1 oficial o académica) · una_fuente · en_disputa (nota con las dos versiones) · no_confirmado; vigencia de la norma o del dato a hoy. ` +
      `Escribe ${trabajo}/verificacion_${eje}.json y corre python3 scripts/explica.py afirmaciones ${trabajo} --check --eje ${eje} hasta 0 fallas.` +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'explica-verificador', schema: S.verificacion, phase: 'Verificación', label: `verifica-${eje}` }),
  (r) => [...(r.eje !== eje ? [`eje ${r.eje} ≠ ${eje}`] : []), ...(r.gate !== 'ok' ? fallasDe(r, `explica.py afirmaciones --check --eje ${eje}`) : [])], 1)
    .catch((e) => { avisar(`AVISO: el eje ${eje} no quedó verificado (${String(e.message).split('\n')[0]}).`); return null }))
ver = verificaciones.filter(Boolean)
log(`Verificación: ${ver.map((v) => `${v.eje} ${v.confirmados}✓ ${v.una_fuente}¹ ${v.en_disputa}≈ ${v.no_confirmados}✗`).join(' · ')}`)
if (!ver.length) fail('Ningún eje quedó verificado: el video no se sostiene todavía.')

// ── 4. Ganchos (consolidar + calculadora + candidatos) ───────────────────────
phase('Ganchos')
const invocarGanchos = (fallos, faltasSel) => agentRol(
  `MODO EXPLICA (lee referencias/ganchos.md y la sección «Modo explica» de referencias/roles/video-gancho.md). TRABAJO = ${trabajo} · «${tema}».\n` +
    `PRIMERO corre python3 scripts/explica.py consolidar ${trabajo} (explicacion.json, base/ y la calculadora de los ejemplos; exit 1 = falta una cifra real o un ejemplo no se calcula: devuélvelo en fallas). ` +
    `Lee SOLO python3 scripts/explica.py digesto ${trabajo} --para gancho. Escribe ${trabajo}/ganchos.json con ${CANDIDATOS_MIN}–${CANDIDATOS_MAX} candidatos de FAMILIAS DISTINTAS (${FAMILIAS.join(', ')}), ≥ 2 con visual (${VISUALES.filter((v) => v !== 'cifra').join(', ')}), ` +
    `que plantean la pregunta del video SIN dar el mecanismo ni la revelación; números de ejemplo solo los ej-cNN (dichos como ejemplo: «Imagina…», «Supón…»); «Guatemala» o «quetzales» en la voz o la pantalla. ` +
    `Corre python3 scripts/explica.py ganchos ${trabajo} --check hasta exit 0 (≤ 3 intentos).\n` +
    (faltasSel ? `EL CRÍTICO NO APROBÓ NINGUNO; rehaz los señalados:\n - ${faltasSel.map((f) => `[${f.candidato} · ${f.regla}] ${f.problema} → ${f.arreglo}`).join('\n - ')}\n` : '') +
    (fallos.length ? `REPARACIÓN: ${fallos.join('; ')}\n` : '') +
    'Retorno: {archivo, gate, fallas[], candidatos[]{id, familia, visual, pantalla}, intentos}.',
  { agentType: 'video-gancho', schema: S.ganchos, phase: 'Ganchos', label: faltasSel ? 'ganchos-rehacer' : 'ganchos' })
const validarGanchos = (r) => {
  if (r.gate !== 'ok') return fallasDe(r, 'explica.py ganchos --check')
  const cs = r.candidatos
  return [
    ...(rel(r.archivo) !== `${trabajo}/ganchos.json` ? [`archivo debe ser ${trabajo}/ganchos.json`] : []),
    ...(cs.length < CANDIDATOS_MIN || cs.length > CANDIDATOS_MAX ? [`${cs.length} candidatos (van ${CANDIDATOS_MIN}–${CANDIDATOS_MAX})`] : []),
    ...(new Set(cs.map((c) => c.familia)).size !== cs.length ? ['familias repetidas'] : []),
    ...(cs.filter((c) => c.visual !== 'cifra').length < 2 ? ['≥ 2 candidatos con un visual que no sea la cifra sola'] : []),
  ]
}
K = await conReparacion('Ganchos', (f) => invocarGanchos(f, null), validarGanchos, 2)
log(`Ganchos: ${K.candidatos.map((c) => `${c.id} ${c.familia}/${c.visual} «${c.pantalla}»`).join(' · ')}`)

// ── 5. Selección ─────────────────────────────────────────────────────────────
phase('Selección')
const seleccionar = (vuelta) => conReparacion('Selección', (fallos) => agentRol(
  `MODO SELECCIÓN DE GANCHO de un VIDEO EXPLICATIVO (lee «Modo selección de gancho» y «Modo explica» de referencias/roles/video-critico.md). TRABAJO = ${trabajo} · vuelta ${vuelta}. ` +
    `Lee SOLO referencias/ganchos.md, ${trabajo}/ganchos.json y python3 scripts/explica.py digesto ${trabajo} --para gancho. Cada candidato primero en silencio y luego con la voz; puntúa silencio, reserva (plantea la pregunta sin regalar el mecanismo ni la revelación), tension, alineacion, honestidad (un número de ejemplo dicho como ejemplo, nunca como dato) y novedad; ganador (ninguno ≤ 2) y segundo de otra familia, o ganador null con faltas. Escribe ${trabajo}/seleccion.json.` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'video-critico', schema: S.seleccion, phase: 'Selección', label: `seleccion-${vuelta}` }),
(r) => {
  const ids = K.candidatos.map((c) => c.id)
  return [
    ...(r.ganador !== null && !ids.includes(r.ganador) ? [`ganador «${r.ganador}» no es un candidato`] : []),
    ...(r.ganador !== null && (r.segundo === r.ganador || (r.segundo !== null && !ids.includes(r.segundo))) ? ['segundo debe ser otro candidato'] : []),
    ...(r.ganador === null && !r.faltas.length ? ['sin ganador: escribe las faltas con su arreglo'] : []),
    ...(r.ganador !== null && !(((r.puntajes || {})[r.ganador] || {}).reserva >= PUNTAJE_MIN) ? [`el ganador «${r.ganador}» necesita reserva ≥ ${PUNTAJE_MIN} (puntajes[id].reserva)`] : []),
  ]
}, 1)
SEL = await seleccionar(1)
if (SEL.ganador === null) {
  avisar('Selección 1: ningún gancho aprobado → video-gancho rehace')
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
const directivaBase = `Eres el guionista de /explica (lee referencias/roles/explica-guionista.md). TRABAJO = ${trabajo} · «${tema}». ` +
  (DESDE_GUION ? `PRIMERO corre python3 scripts/explica.py consolidar ${trabajo}. ` : '') +
  `Lee SOLO python3 scripts/explica.py digesto ${trabajo} --para guionista. Corre python3 scripts/explica.py guion ${trabajo} --check hasta 0 fallas ` +
  `y devuelve TAL CUAL su última línea RETORNO (tipos trae el tipo de CADA escena en orden, sin el cierre). `
const directivaGuion = RETOQUE
  ? directivaBase + `RETOQUE: ${trabajo}/guion.json ya existe, aprobado y con voz grabada. Notas del usuario: «${notas}». Aplica SOLO lo que piden ` +
    `(si piden otro gancho: python3 scripts/explica.py ganchos ${trabajo} --usar <id> y relee el hilo entero). Conserva palabra por palabra la voz (texto) de toda escena que no ` +
    `necesite cambiar (y su tramo de narracion): cada voz cambiada cuesta créditos (con voz de corrido, la secuencia entera). Añade al RETORNO voces_cambiadas: [n de cada escena cuya voz cambió; el cierre es la escena N+1]. `
  : directivaBase + `PRIMERO python3 scripts/explica.py ganchos ${trabajo} --usar (el gancho ${SEL.ganador || 'elegido en seleccion.json'} pasa a la escena 1 y NO lo cambias). ` +
    `DESPUÉS escribe la NARRACIÓN: guion.narracion = [{acto: 1, texto}, {acto: 2, texto}, {acto: 3, texto}] (1 LA PREGUNTA: gancho, promesa, la idea equivocada dicha con justicia, el detonante; ` +
    `2 EL MECANISMO: la cuenta con quetzales antes de la definición, la animación, el «ajá» del punto medio, el giro = la otra cara del mecanismo; 3 EN TU VIDA: el mecanismo con datos reales de Guatemala con su fecha, la regla práctica, el pago de la promesa), ` +
    `empezando con la voz del gancho tal cual, un ejemplo conductor, cada oración sigue de la anterior, ≤ ${SEGUN_MAX} «según», nada de consejo; mídela con python3 scripts/explica.py narracion ${trabajo} --check hasta 0 fallas. ` +
    `SOLO ENTONCES repártela en escenas SIN cambiar una palabra: acto en cada escena, intuicion: true (acto 1) y corrige: true (acto 2), cuenta (la pizarra) con renglones que el gate rehace, definicion, explica (mecanismo, brief, animacion o null), escala, tarjetas con grafico, ` +
    `giro: true en el acto 2, rotulo {etiqueta, titulo} en la primera escena de los actos 2 y 3, promesa con revela, cierre de consecuencia y captions. Números de ejemplo solo los ej-cNN, dichos como ejemplo. `
const voces = new Set()
const sumaVoces = (r) => { if (r) (r.voces_cambiadas || []).forEach((n) => voces.add(n)); return r }
const validarGuion = (r) => {
  if (r.gate !== 'ok') return fallasDe(r, 'explica.py guion --check')
  return [
    ...(rel(r.archivo) !== `${trabajo}/guion.json` ? [`archivo debe ser ${trabajo}/guion.json`] : []),
    ...(r.tipos[0] !== 'gancho' ? ['la escena 1 es el gancho'] : []),
    ...(r.actos !== 3 ? [`${r.actos} actos (van 3)`] : []),
    ...(r.intuicion === null || r.corrige === null ? ['falta la escena intuicion (acto 1) o la corrige (acto 2)'] : []),
    ...(r.segun > SEGUN_MAX ? [`${r.segun} «según» en voz (van ≤ ${SEGUN_MAX})`] : []),
    ...(r.estimado_s > DURACION_MAX_S ? [`${r.estimado_s} s estimados (máximo ${DURACION_MAX_S})`] : []),
    ...(r.tipos.length !== r.escenas ? [`tipos trae ${r.tipos.length} elementos: debe traer el tipo de CADA escena, en orden (${r.escenas})`] : []),
    ...(r.tipos.length === r.escenas ? r.explica_sin_animacion.filter((n) => r.tipos[n - 1] !== 'explica').map((n) => `la escena ${n} no es explica`) : []),
  ]
}
let G = sumaVoces(await conReparacion('Guion', (fallos) => agentRol(directivaGuion + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'explica-guionista', schema: S.guion, phase: 'Guion', label: 'guionista' }), validarGuion, 2))
log(`Guion: ${G.escenas} escenas · ${G.palabras} palabras · intuición E${G.intuicion} → corrige E${G.corrige} · ejemplo en ${G.ilustrativas.join(', ') || '—'} · ${G.segun} «según» · ${G.estimado_s} s estimados${RETOQUE ? ` · voces cambiadas ${[...voces].join(', ') || 'ninguna'}` : ''}`)

// ── 6b. Oyente ingenuo: oye la voz, lee la pantalla y explica de vuelta el mecanismo ─────────────────────────────────
const oir = (vuelta) => conReparacion(`oyente ${vuelta}`, (fallos) => agentRol(
  `Eres el OYENTE INGENUO en MODO EXPLICA (lee referencias/roles/historia-oyente.md, también su «Modo explica»). TRABAJO = ${trabajo}. ` +
    `Lee SOLO python3 scripts/explica.py digesto ${trabajo} --para oyente (primero la narración de corrido, luego el desglose por escena con la pantalla; no sabes nada más del tema). ` +
    `Dos pasadas, sin volver atrás. Al final, explicacion_devuelta: en UNA oración y con tus palabras, cómo funciona lo que te explicaron (si no puedes, «no podría explicarlo» y por qué en confusiones). ` +
    `Escribe ${trabajo}/oyente.json y devuelve lo mismo.` + (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'historia-oyente', schema: S.oyente, phase: 'Oyente', label: `oyente-${vuelta}` }),
(r) => [
  ...(rel(r.archivo) !== `${trabajo}/oyente.json` ? [`archivo debe ser ${trabajo}/oyente.json`] : []),
  ...(!r.de_que.trim() ? ['de_que: una oración'] : []),
  ...(!r.explicacion_devuelta.trim() ? ['explicacion_devuelta: una oración (o «no podría explicarlo»)'] : []),
  ...r.confusiones.filter((c) => c.escena < 1 || c.escena > G.escenas + 1).map((c) => `confusión en la escena ${c.escena}: no existe (1–${G.escenas + 1})`),
], 1).catch((e) => { avisar(`AVISO: el oyente no terminó (${String(e.message).split('\n')[0]}); la crítica va sin oyente.json.`); return null })
phase('Oyente')
let O = await oir(1)
if (O) log(`Oyente: «${O.de_que}» · devuelve «${O.explicacion_devuelta}» · ${O.confusiones.length} confusiones · ${O.saltos.length} saltos · ${O.pregunta_sin_responder.length} sin responder`)

// ── 7. Crítica (≤ 2 vueltas; 1 en retoque; acotadas desde la 2) ──────────────
phase('Crítica')
const validarCritica = (r, O, cambiadas = null, previas = []) => {
  const f = []
  const acotada = cambiadas !== null
  for (const k of PUNTAJES) if (r.puntajes[k] <= 2 && !r.faltas.some((x) => x.gravedad === 'bloquea' && x.regla === REGLA_DE[k])) f.push(`puntaje ${k} = ${r.puntajes[k]} sin falta «bloquea» de ${REGLA_DE[k]}`)
  const bloquea = r.faltas.some((x) => x.gravedad === 'bloquea') || PUNTAJES.some((k) => r.puntajes[k] < PUNTAJE_MIN)
  if ((r.veredicto === 'pasa') === bloquea) f.push(`veredicto ${r.veredicto} incoherente con las faltas y los puntajes`)
  for (const x of r.faltas) if (x.gravedad === 'bloquea' && x.probado === false) f.push(`la falta ${x.n ?? ''} (escena ${x.escena}) bloquea con un arreglo que el gate rechaza: ajústalo con explica.py probar hasta que pase, o dala como mejora con la falla del gate en problema`)
  for (const x of r.faltas) if (x.probado === true && !(x.cambios || []).length) f.push(`la falta ${x.n ?? ''} (escena ${x.escena}) trae probado: true sin cambios: copia en cambios el JSON exacto que pasaste a explica.py probar`)
  if (acotada) {
    const deRegla = (x) => PUNTAJES.some((k) => REGLA_DE[k] === x.regla && r.puntajes[k] <= 2)
    for (const x of r.faltas.filter((y) => y.gravedad === 'bloquea')) {
      const vale = cambiadas.has(x.escena) || previas.some((p) => p.escena === x.escena && p.regla === x.regla) || x.regla === 'E-C5' || deRegla(x)
      if (!vale) f.push(`la falta ${x.n ?? ''} (escena ${x.escena}, ${x.regla}) bloquea en una vuelta acotada: solo bloquea lo que cambió (escenas ${[...cambiadas].join(', ') || 'ninguna'}), lo pendiente o la precisión (E-C5); dala como mejora`)
    }
  }
  const nombra = (x, n) => new RegExp(`\\b(?:escena|escenas|la)\\s+(?:\\d+\\s*(?:,|y|→|-|–)\\s*)*${n}\\b`).test(`${x.problema || ''} ${x.arreglo || ''} ${x.motivo || ''}`)
  const atendida = (n) => r.faltas.some((x) => x.escena === n || nombra(x, n)) || (r.oyente_descartadas || []).some((d) => d.escena === n || nombra(d, n))
  const toca = (n) => !acotada || cambiadas.has(n)
  for (const c of (O ? O.confusiones : [])) if (toca(c.escena) && !atendida(c.escena)) f.push(`la confusión del oyente en la escena ${c.escena} («${c.que_no_entendi}») no tiene falta ni entrada en oyente_descartadas`)
  for (const s of (O ? O.saltos : [])) if (toca(s.a) && !atendida(s.a)) f.push(`el salto ${s.de}→${s.a} del oyente no tiene falta en la escena ${s.a} ni entrada en oyente_descartadas`)
  return f
}
let critica = null, previas = [], arreglosRechazados = []
let cambiadas = RETOQUE ? new Set(G.voces_cambiadas || []) : null
const conCambios = (lista) => lista.filter((x) => (x.cambios || []).length)
const aplicarDirectiva = (lista) => `Las que traen cambios se aplican TAL CUAL, sin reescribirlas: python3 scripts/explica.py aplicar ${trabajo} --cambios '<sus cambios>' ` +
  `(los cambios de varias faltas juntos en una sola llamada, como los probó el crítico: ${JSON.stringify(conCambios(lista).flatMap((x) => x.cambios))}); las que no traen cambios las redactas tú con su arreglo. `
for (let vuelta = 1; vuelta <= VUELTAS + 1; vuelta++) {
  if (vuelta > 1) O = await oir(vuelta)
  const acotada = cambiadas !== null
  critica = await conReparacion(`crítica ${vuelta}`, (fallos) => agentRol(
    `MODO EXPLICA (lee la sección «Modo explica» de referencias/roles/video-critico.md). TRABAJO = ${trabajo}. Vuelta ${vuelta}. ` +
      `Insumos: ${trabajo}/guion.json, ${trabajo}/locucion.json, ` +
      (O ? `${trabajo}/oyente.json (lo que un oyente que SOLO oyó la voz no entendió y su explicacion_devuelta: E-C2 compara esa oración con mecanismo_frase; si no casan, bloquea con el arreglo de la escena donde se perdió; cada confusión y cada salto se resuelve con una falta o se justifica en oyente_descartadas[]{escena, motivo}) y ` : '') +
      `python3 scripts/explica.py digesto ${trabajo} --para critico (encuadre, afirmaciones, cifras, ejemplos y la NARRACIÓN DE CORRIDO). ` +
      `E-C3: la idea equivocada se dice con justicia en el acto 1 y se rompe de forma visible en el 2; E-C5: los números de ejemplo son del script y se dicen como ejemplo, las cifras reales con su fecha, nada de consejo ni bancos; E-C6: el cierre es la consecuencia para quien lo vive, sin orden ni moraleja. ` +
      (acotada ? `VUELTA ACOTADA: cambiaron las escenas ${[...cambiadas].join(', ') || 'ninguna'}. Solo BLOQUEA lo que cambió, lo pendiente, la precisión (E-C5) o un puntaje ≤ 2; lo demás va como mejora. ` : '') +
      (RETOQUE ? `RETOQUE con notas del usuario: «${notas}». Lo que las notas piden conservar no va como falta bloquea. ` : '') +
      `ARREGLOS PROBADOS: antes de escribir cada arreglo de texto, pruébalo con python3 scripts/explica.py probar ${trabajo} --cambios '[{"escena": N, "texto": "…"}]' ` +
      `(también {"escena": N, "campo": "golpe", "valor": "…"}, {"promesa": "…"}, {"cierre": "…"}); marca probado: true|false y, con true, copia en cambios el JSON exacto que pasó. Escribe ${trabajo}/critica.json.` +
      (previas.length ? ` Faltas de la vuelta anterior (comprueba primero cada una): ${JSON.stringify(previas)}` : '') +
      (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
    { agentType: 'video-critico', schema: S.critica, phase: 'Crítica', label: `critica-${vuelta}` }), (r) => validarCritica(r, O, cambiadas, previas), 2)
  log(`Crítica ${vuelta}${acotada ? ' (acotada)' : ''}: ${critica.veredicto} · ${PUNTAJES.map((k) => `${k} ${critica.puntajes[k]}`).join(' · ')}`)
  if (critica.veredicto === 'pasa' || vuelta > VUELTAS) break
  previas = critica.faltas.filter((x) => x.gravedad === 'bloquea')
  G = sumaVoces(await conReparacion(`corrección ${vuelta}`, (fallos) => agentRol(directivaGuion +
    ` CORRECCIÓN ${vuelta}: guion.json ya existe; corrige SOLO lo que bloquea (con el arreglo exacto), conserva las demás voces y repasa el gate: ${JSON.stringify(previas)}. ` +
    aplicarDirectiva(previas) +
    `Un arreglo que el gate rechaza no lo reescribas en silencio: aplica lo más cercano que pase y devuélvelo en arreglos_rechazados [{n, falla}]. ` +
    `Añade al RETORNO voces_cambiadas: [n de cada escena cuya voz cambió; el cierre es la escena N+1].` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'explica-guionista', schema: S.guion, phase: 'Crítica', label: `guionista-corrige-${vuelta}` }), validarGuion, 1))
  cambiadas = new Set([...(G.voces_cambiadas || []), ...previas.map((x) => x.escena).filter((n) => Number.isInteger(n))])
  for (const x of G.arreglos_rechazados || []) {
    arreglosRechazados.push({ ...x, vuelta })
    avisar(`AVISO: el gate rechazó el arreglo ${x.n} de la crítica ${vuelta} (${x.falla}); el guionista aplicó lo más cercano que pasa.`)
  }
}

// ── 7a. Cierre con arreglos probados ─────────────────────────────────────────
let aprobadoPor = critica.veredicto === 'pasa' ? 'critico' : null, aplicadasAlCierre = []
const pendientes = critica.faltas.filter((x) => x.gravedad === 'bloquea')
if (critica.veredicto !== 'pasa' && pendientes.length && pendientes.every((x) => x.probado === true && (x.cambios || []).length) &&
    PUNTAJES.every((k) => critica.puntajes[k] > 2)) {
  const C = await conReparacion('cierre con arreglos probados', (fallos) => agentRol(directivaGuion +
    ` CIERRE CON ARREGLOS PROBADOS: aplícalos TODOS juntos y sin reescribirlos con UNA llamada: python3 scripts/explica.py aplicar ${trabajo} --cambios '${sh(JSON.stringify(pendientes.flatMap((x) => x.cambios)))}'. ` +
    `Si sale 1, NO lo arregles: devuelve gate: "falla" con sus líneas FALLA. Con exit 0 corre python3 scripts/explica.py guion ${trabajo} --check y devuelve su RETORNO con voces_cambiadas.` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'explica-guionista', schema: S.guion, phase: 'Crítica', label: 'guionista-cierre' }), validarGuion, 0)
    .catch((e) => { avisar(`AVISO: los arreglos probados no pasaron el gate juntos (${String(e.message).split('\n')[0]}); queda «corregir».`); return null })
  if (C) {
    G = sumaVoces(C)
    aplicadasAlCierre = pendientes
    aprobadoPor = 'arreglos_probados'
    critica = { ...critica, veredicto: 'pasa', faltas: critica.faltas.filter((x) => x.gravedad !== 'bloquea') }
    avisar(`AVISO: la última crítica solo bloqueaba con arreglos probados: se aplicaron ${pendientes.length} y el guion queda aprobado.`)
    O = (await oir('cierre')) || O
  }
}

// ── 7b. Mejoras: con «pasa», el guionista aplica las mejoras antes de gastar voz; el oyente las vuelve a oír ──────────
let mejorasNoAplicadas = critica.veredicto === 'pasa' ? critica.faltas.filter((x) => x.gravedad === 'mejora') : []
if (mejorasNoAplicadas.length) {
  const lista = mejorasNoAplicadas
  const M = await conReparacion('mejoras', (fallos) => agentRol(directivaGuion +
    ` MEJORAS: el crítico aprobó el guion; aplica estas mejoras con su arreglo exacto, sin tocar nada más: ${JSON.stringify(lista)}. ` +
    `ANTES copia ${trabajo}/guion.json a ${trabajo}/guion.aprobado.json. La que trae cambios, tal cual con python3 scripts/explica.py aplicar ${trabajo} --cambios '<sus cambios>' ` +
    `(si sale 1, va en no_aplicadas con su FALLA); la que no, a mano y corre python3 scripts/explica.py guion ${trabajo} --check; si al final el gate no llega a 0 fallas, restaura guion.aprobado.json, ` +
    `vuelve a correr el gate y devuelve aplicadas: []. Devuelve aplicadas (los n), no_aplicadas y voces_cambiadas.` +
    (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
  { agentType: 'explica-guionista', schema: S.mejoras, phase: 'Crítica', label: 'guionista-mejoras' }), (r) => (r.gate !== 'ok' ? fallasDe(r, 'explica.py guion --check') : []), 1)
    .catch((e) => { avisar(`AVISO: las mejoras no se aplicaron (${String(e.message).split('\n')[0]}); queda el guion aprobado.`); return null })
  if (M) {
    sumaVoces(M)
    G = { ...G, ...M }
    mejorasNoAplicadas = lista.filter((x) => !M.aplicadas.includes(x.n)).map((x) => ({ ...x, motivo: (M.no_aplicadas.find((y) => y.n === x.n) || {}).motivo || 'no aplicada' }))
    log(`Mejoras: ${M.aplicadas.length} aplicadas · ${mejorasNoAplicadas.length} no aplicadas`)
    if (M.aplicadas.length && (M.voces_cambiadas || []).length) {
      const O3 = await oir('mejoras')
      const cambiadasM = new Set(M.voces_cambiadas)
      const antes = new Set([...(O ? O.confusiones.map((c) => c.escena) : []), ...(O ? O.saltos.map((s) => s.a) : [])])
      const nuevas = new Set(O3 ? [...O3.confusiones.map((c) => c.escena), ...O3.saltos.map((s) => s.a)].filter((n) => cambiadasM.has(n) && !antes.has(n)) : [])
      const revertir = lista.filter((x) => M.aplicadas.includes(x.n) && nuevas.has(x.escena) && x.regla !== 'E-C5')
      if (revertir.length) {
        const escenas = [...new Set(revertir.map((x) => x.escena))]
        avisar(`AVISO: las mejoras ${revertir.map((x) => x.n).join(', ')} confundieron al oyente en las escenas ${escenas.join(', ')}: se revierten solo esas escenas.`)
        const R = await conReparacion('revertir mejoras', (fallos) => agentRol(directivaGuion +
          ` REVIERTE SOLO las escenas ${escenas.join(', ')}: toma el texto de cada una de ${trabajo}/guion.aprobado.json y aplícalo con python3 scripts/explica.py aplicar ${trabajo} --cambios '[{"escena": N, "texto": "…"}, …]' ` +
          `(el cierre, con {"cierre": "…"}); las demás mejoras se quedan. Corre python3 scripts/explica.py guion ${trabajo} --check y devuelve su RETORNO.` +
          (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
        { agentType: 'explica-guionista', schema: S.guion, phase: 'Crítica', label: 'guionista-revierte' }), validarGuion, 1)
          .catch((e) => { avisar(`AVISO: no se pudo revertir (${String(e.message).split('\n')[0]}); revisa guion.json contra guion.aprobado.json.`); return null })
        if (R) { G = R; escenas.forEach((n) => voces.delete(n)) }
        mejorasNoAplicadas = [...mejorasNoAplicadas, ...revertir.map((x) => ({ ...x, motivo: 'confundió al oyente: revertida esa escena' }))]
      }
      if (O3) O = O3
    }
  }
}

// ── 8. Animación (solo si el crítico aprueba) ────────────────────────────────
phase('Animación')
const animaciones = []
if (critica.veredicto === 'pasa') {
  for (const n of G.explica_sin_animacion || []) {
    const r = await conReparacion(`animación escena ${n}`, (fallos) => agentRol(
      `MODO EXPLICA (lee referencias/roles/video-animador.md, también su «Modo explica»). TRABAJO = ${trabajo}. La escena ${n} de ${trabajo}/guion.json es explica con animacion null: lee su mecanismo, brief, titulo, pasos y acento ahí (solo esa escena) y la leyenda de ${trabajo}/encuadre.json. ` +
        `Reutiliza del catálogo SOLO una del mismo mecanismo que cuente lo mismo (python3 scripts/animaciones.py --lista) o escribe video/animaciones/<id>.js con meta.mecanismo (queda como plantilla); --check, --registrar <id> --video ${trabajo.split('/').pop()} y --asignar ${trabajo} --escena ${n} --id <id>.` +
        (fallos.length ? ` REPARACIÓN: ${fallos.join('; ')}.` : ''),
      { agentType: 'video-animador', schema: S.animacion, phase: 'Animación', label: `animacion-${n}` }),
    (x) => [...(x.archivo !== `video/animaciones/${x.id}.js` ? [`archivo debe ser video/animaciones/${x.id}.js`] : []),
      ...(x.check !== 'ok' && !(x.fallas || []).length ? ['check falla sin detalle'] : [])], 1).catch((e) => { avisar(`AVISO: la escena ${n} sigue sin animación (${String(e.message).split('\n')[0]}).`); return null })
    if (r) animaciones.push({ escena: n, id: r.id, reutilizada: r.reutilizada, check: r.check })
  }
}

return {
  trabajo, tema, veredicto: critica.veredicto, puntajes: critica.puntajes,
  aprobado_por: aprobadoPor, aplicadas_al_cierre: aplicadasAlCierre,
  faltas_pendientes: critica.faltas.filter((x) => x.gravedad === 'bloquea'),
  mejoras: critica.faltas.filter((x) => x.gravedad === 'mejora'),
  mejoras_no_aplicadas: mejorasNoAplicadas, arreglos_rechazados: arreglosRechazados,
  encuadre: ENC ? { pregunta: ENC.pregunta, intuicion: ENC.intuicion, mecanismo: ENC.mecanismo, mecanismo_frase: ENC.mecanismo_frase, ejemplos: ENC.ejemplos, anclas: ENC.anclas, revelaciones: ENC.revelaciones, paleta: ENC.paleta, sensible: ENC.sensible } : null,
  verificacion: ver.map((v) => ({ eje: v.eje, confirmados: v.confirmados, una_fuente: v.una_fuente, en_disputa: v.en_disputa, no_confirmados: v.no_confirmados })),
  gancho: { ganador: SEL.ganador, segundo: SEL.segundo, por_que: SEL.por_que },
  guion: { escenas: G.escenas, palabras: G.palabras, segun: G.segun, intuicion: G.intuicion, corrige: G.corrige, ilustrativas: G.ilustrativas, secuencias: G.secuencias || 0, estimado_s: G.estimado_s, explica_sin_animacion: G.explica_sin_animacion },
  desde: DESDE, retoque: RETOQUE, voces_cambiadas: [...voces].sort((a, b) => a - b),
  oyente: O ? { de_que: O.de_que, explicacion_devuelta: O.explicacion_devuelta, promesa: O.promesa, confusiones: O.confusiones.length, saltos: O.saltos.length, pregunta_sin_responder: O.pregunta_sin_responder } : null,
  animaciones, avisos: AVISOS_WF,
}
