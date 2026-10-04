export const meta = {
  name: 'ideas',
  description: 'Banco de ideas: exploradores en paralelo proponen temas de Guatemala con datos descargables',
  whenToUse: 'Invocado por /ideas [n] [enfoque]. args: {fecha, dir, enfoque, n, excluir[], permitir_fallback} (fecha YYYY-MM-DD y dir los pone el comando). El banco lo escribe después scripts/ideas.py --importar <dir>.',
  phases: [
    { title: 'Exploración', detail: 'un explorador (sonnet) por grupo de áreas: agenda → fuentes.py → ≤1 fetch de acceso por idea' },
  ],
}

// Guía: referencias/roles/explorador.md. Los exploradores escriben <dir>/ideas_<grupo>.json;
// aquí solo se valida el retorno. Dedup contra el banco y contra memoria/hilos.json, y la
// escritura del banco, las hace scripts/ideas.py --importar (el sandbox no lee disco).

const AREAS = ['economia', 'seguridad', 'salud', 'educacion', 'clima-agro', 'energia', 'fiscal', 'poblacion', 'otra']
const HOOKS = ['giro_inversion', 'escala_humana', 'brecha_territorial', 'pregunta_directa', 'curiosity_gap', 'mito_vs_dato', 'antes_despues', 'titular_clasico']
const PALETAS = ['cielo', 'jade', 'maiz', 'terracota', 'cacao', 'jacaranda', 'atitlan', 'obsidiana']
const FORMATOS = ['xlsx', 'xls', 'csv', 'html', 'pdf', 'json', 'api']
const GRUPOS = [
  { id: 'economia', areas: ['economia', 'fiscal'], foco: 'precios, empleo, remesas, comercio, deuda, presupuesto y recaudación' },
  { id: 'sociedad', areas: ['seguridad', 'poblacion'], foco: 'violencia, justicia, migración, demografía y pobreza' },
  { id: 'territorio', areas: ['salud', 'educacion', 'clima-agro', 'energia'], foco: 'salud, educación, clima, agro, agua y energía' },
]
const PRESUPUESTO = { busquedas: 6, fetch: 6 }

const S = {
  lote: {
    type: 'object',
    required: ['grupo', 'archivo', 'n_busquedas', 'ideas'],
    properties: {
      grupo: { type: 'string' }, archivo: { type: 'string', pattern: 'ideas_[a-z0-9-]+\\.json$' },
      n_busquedas: { type: 'number' }, n_fetch: { type: 'number' },
      ideas: {
        type: 'array', minItems: 1, maxItems: 8,
        items: {
          type: 'object',
          required: ['id', 'titulo', 'area', 'pregunta', 'por_que_ahora', 'hook_sugerido', 'paleta_sugerida', 'datos', 'puntaje'],
          properties: {
            id: { type: 'string', pattern: '^[a-z0-9-]+$' }, titulo: { type: 'string', maxLength: 100 },
            area: { type: 'string', enum: AREAS }, pregunta: { type: 'string' }, por_que_ahora: { type: 'string' }, angulo: { type: 'string' },
            hook_sugerido: { type: 'string', enum: HOOKS }, paleta_sugerida: { type: 'string', enum: PALETAS },
            datos: {
              type: 'array', minItems: 1,
              items: {
                type: 'object', required: ['fuente', 'indicador', 'url', 'evidencia'],
                properties: { fuente: { type: 'string' }, indicador: { type: 'string' }, url: { type: 'string' }, formato: { type: 'string', enum: FORMATOS }, periodo: { type: 'string' }, evidencia: { type: 'string' } },
              },
            },
            puntaje: {
              type: 'object', required: ['interes', 'datos', 'actualidad'],
              properties: { interes: { type: 'integer', minimum: 1, maximum: 5 }, datos: { type: 'integer', minimum: 1, maximum: 5 }, actualidad: { type: 'integer', minimum: 1, maximum: 5 } },
            },
            nota: { type: 'string' },
          },
        },
      },
    },
  },
}

// ── Argumentos ─────────────────────────────────────────────────────────────
const A = typeof args === 'string' ? { enfoque: args } : (args || {})
const fecha = String(A.fecha || '')
if (!/^\d{4}-\d{2}-\d{2}$/.test(fecha)) throw new Error('args.fecha (YYYY-MM-DD) es obligatoria: /ideas la obtiene con `date +%F` y la pasa en args.')
const dir = String(A.dir || `sesiones/_ideas/${fecha}`).replace(/\/+$/, '')
if (!/^sesiones\/_ideas\//.test(dir)) throw new Error(`args.dir debe estar bajo sesiones/_ideas/ (llegó ${dir}).`)
const enfoque = String(A.enfoque || '').trim()
const n = Math.min(15, Math.max(3, parseInt(A.n, 10) || 9))
const excluir = (Array.isArray(A.excluir) ? A.excluir : []).map(String).filter(Boolean)
const fail = (msg) => { throw new Error(msg) }

// Con enfoque, o con menos de 9 ideas, basta UN explorador (más barato que 3 con 1 idea cada uno).
const grupos = enfoque
  ? [{ id: 'enfoque', areas: AREAS, foco: enfoque }]
  : n < 3 * GRUPOS.length
    ? [{ id: 'general', areas: AREAS, foco: 'todas las áreas; varía de área entre ideas' }]
    : GRUPOS
const porGrupo = grupos.length === 1 ? Math.min(8, n) : Math.min(5, Math.ceil(n / grupos.length))

// Mismo patrón que hilo.js: fail-fast si el agente no está registrado (se cargan al arrancar).
const agentRol = async (prompt, opts) => {
  try {
    return await agent(prompt, opts)
  } catch (e) {
    if (!opts || !opts.agentType || !/agent type .* not found/i.test(String(e && e.message))) throw e
    if (!A.permitir_fallback) fail(`El agente ${opts.agentType} no está registrado en esta sesión (los .claude/agents/ se cargan al arrancar). Reinicia Claude Code y vuelve a lanzar /ideas, o pasa args.permitir_fallback: true para correr con general-purpose.`)
    log(`AVISO: ${opts.agentType} no registrado; se usa general-purpose (permitir_fallback).`)
    const { agentType, ...resto } = opts
    return agent(`Asume el rol definido en .claude/agents/${agentType}.md: léelo primero y sigue sus instrucciones y sus límites. ` + prompt, { ...resto, agentType: 'general-purpose' })
  }
}

// Problemas de una idea que el schema no atrapa (vacía = válida).
const problemas = (i) => {
  const F = []
  if (!i.datos.some((d) => /^https?:\/\//.test(d.url || '') && (d.evidencia || '').trim().length >= 10)) F.push('ningún dato con url y evidencia (≥10 caracteres) de que la fuente lo publica')
  if (!(i.pregunta || '').trim() || !(i.por_que_ahora || '').trim()) F.push('pregunta o por_que_ahora vacíos')
  return F
}

// ── EXPLORACIÓN ────────────────────────────────────────────────────────────
phase('Exploración')
const explorar = async (gr) => {
  const archivo = `${dir}/ideas_${gr.id}.json`
  const prompt = (fallos) =>
    `Eres el explorador del grupo "${gr.id}" (lee referencias/roles/explorador.md). Fecha: ${fecha}. ` +
    (enfoque ? `ENFOQUE pedido por el usuario: «${enfoque}»; area de cada idea ∈ ${AREAS.join('|')}. ` : `Áreas: ${gr.areas.join(', ')} (${gr.foco}); area de cada idea ∈ ${gr.areas.join('|')}. `) +
    `Propón EXACTAMENTE ${porGrupo} ideas. PRESUPUESTO: ≤${PRESUPUESTO.busquedas} búsquedas, ≤${PRESUPUESTO.fetch} fetch (≤1 por idea, para confirmar acceso al dato). ` +
    `EVITA (ya están en el banco o ya son hilos; solo con ángulo claramente distinto): ${excluir.length ? excluir.map((x) => `«${x}»`).join('; ') : 'nada'}. ` +
    `Crea ${dir}/ con mkdir -p y escribe ${archivo} completo como {"grupo": "${gr.id}", "ideas": [...]}; devuelve el mismo contenido con archivo, n_busquedas y n_fetch.` +
    (fallos.length ? `\nTU RETORNO ANTERIOR FUE RECHAZADO; corrige y vuelve a escribir ${archivo}:\n - ${fallos.join('\n - ')}` : '')
  const opts = { agentType: 'ideas-explorador', schema: S.lote, phase: 'Exploración' }
  let r = await agentRol(prompt([]), { ...opts, label: `explorar-${gr.id}` })
  if (!r) { log(`AVISO: el explorador ${gr.id} no terminó.`); return null }
  let malas = r.ideas.map((i) => ({ i, F: problemas(i) })).filter((x) => x.F.length)
  // Una reparación solo si menos de la mitad sirve: las inválidas sueltas las descarta ideas.py.
  if (malas.length * 2 > r.ideas.length) {
    const fallos = malas.map((x) => `${x.i.id}: ${x.F.join('; ')}`)
    log(`${gr.id}: ${malas.length}/${r.ideas.length} ideas sin evidencia de datos → reparación`)
    const r2 = await agentRol(prompt(fallos), { ...opts, label: `explorar-${gr.id}-reparacion` })
    if (r2) { r = r2; malas = r.ideas.map((i) => ({ i, F: problemas(i) })).filter((x) => x.F.length) }
  }
  if (r.n_busquedas > PRESUPUESTO.busquedas || (r.n_fetch || 0) > PRESUPUESTO.fetch) log(`AVISO: ${gr.id} excedió el presupuesto (${r.n_busquedas} búsquedas, ${r.n_fetch || '?'} fetch).`)
  if (!new RegExp(`ideas_${gr.id}\\.json$`).test(r.archivo)) log(`AVISO: ${gr.id} reportó el archivo ${r.archivo}; se esperaba ${archivo}.`)
  for (const x of malas) log(`AVISO: ${gr.id}/${x.i.id} se descartará al importar: ${x.F.join('; ')}`)
  const buenas = r.ideas.filter((i) => !problemas(i).length)
  return { grupo: gr.id, archivo, ideas: buenas, descartadas: malas.map((x) => x.i.id) }
}
const lotes = (await parallel(grupos.map((gr) => () => explorar(gr)))).filter(Boolean)
if (!lotes.length) fail('Ningún explorador terminó: no hay ideas que importar.')

// Ids repetidos entre grupos: ideas.py se queda con la primera; aquí solo se avisa.
const vistos = new Map()
for (const l of lotes) for (const i of l.ideas) {
  if (vistos.has(i.id)) log(`AVISO: id ${i.id} propuesto por ${vistos.get(i.id)} y ${l.grupo}; ideas.py importará solo el primero.`)
  else vistos.set(i.id, l.grupo)
}
const ideas = lotes.flatMap((l) => l.ideas.map((i) => ({
  id: i.id, titulo: i.titulo, area: i.area, grupo: l.grupo,
  puntaje: i.puntaje.interes + i.puntaje.datos + i.puntaje.actualidad,
  fuentes: [...new Set(i.datos.map((d) => d.fuente))],
})))
if (!ideas.length) fail('Los exploradores no devolvieron ninguna idea con evidencia de datos.')
log(`Ideas válidas: ${ideas.length} de ${lotes.length} grupo(s) · importar con: python3 scripts/ideas.py --importar ${dir}`)

return {
  dir,
  fecha,
  enfoque: enfoque || null,
  grupos_caidos: grupos.map((g) => g.id).filter((id) => !lotes.some((l) => l.grupo === id)),
  ideas: ideas.sort((a, b) => b.puntaje - a.puntaje),
  descartadas: lotes.flatMap((l) => l.descartadas),
}
