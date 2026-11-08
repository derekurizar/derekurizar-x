---
description: Mide cómo les fue a los videos publicados (TikTok Studio, YouTube Studio, Instagram y Facebook vía Claude in Chrome, solo lectura), alinea cada curva de retención con las escenas de su guion, detecta los problemas (gancho, cuadro 0, promesa, ritmo, animaciones, cierre, duración, caption, publicación, horario; AN1–AN12), busca en la web cómo se resuelven y propone mejoras al framework con su evidencia; no aplica nada sin que el usuario lo pida (uso — /analyze-improve [tiktok,youtube,instagram,facebook] [desde:AAAA-MM-DD] [solo-diagnostico] [fixture])
---

Eres el coordinador de **/analyze-improve** de @DerekUrizar. Argumentos: "$ARGUMENTS".
- Plataformas separadas por coma (por defecto las cuatro).
- `desde:AAAA-MM-DD`: solo las publicaciones desde esa fecha (por defecto, 30 días antes de hoy).
- `solo-diagnostico`: no captura; diagnostica lo que ya está en `memoria/metricas.json`.
- `fixture`: corre `make analisis-fixture` (sin Chrome ni web), muestra su diagnóstico y termina.

La guía es `referencias/flujo-analisis.md`. La captura es **solo lectura**: no publiques, no edites ni borres nada en
las plataformas, no aceptes avisos, no descargues archivos y no escribas contraseñas. Sin agentes: lo haces tú.

1. **PREFLIGHT**
   - `make doctor` (exit 0) y `python3 scripts/memoria.py --ver-mejoras pendiente` (lo que ya estaba propuesto).
   - Carga las herramientas de Chrome en UNA llamada a ToolSearch (`tabs_context_mcp, tabs_create_mcp, navigate,
     javascript_tool, computer, get_page_text, tabs_close_mcp`), `tabs_context_mcp` y abre una pestaña nueva.
2. **CAPTURA** (salta con `solo-diagnostico`)
   - Por plataforma, los fragmentos de `referencias/analisis/captura.md`, en este orden: TikTok (lista → analítica por
     video con la curva por segundo) → YouTube (lista → «visto» y tiempo medio) → Facebook (tabla) → Instagram
     (tarjetas → API de medios). Cada captura sale por el textarea + `cmd+a cmd+c` + `pbpaste >
     sesiones/_analisis/<hoy>/captura_<plataforma>.json`, y se comprueba que el JSON se lea.
   - Si una plataforma pide iniciar sesión o cambió su página y el fragmento no encuentra datos tras 2 intentos,
     sáltala, dilo en el reporte y propón el arreglo del fragmento como mejora (archivo
     `referencias/analisis/captura.md`).
   - Si una pieza tiene muy pocas vistas en una plataforma, abre su página de detalles y lee (sin cambiar nada) si
     tiene una restricción, una pregunta obligatoria sin responder o un reclamo.
   - Cierra la pestaña.
3. **REGISTRO Y VÍNCULO**
   - `python3 scripts/metricas.py importar sesiones/_analisis/<hoy>/captura_*.json`
   - `python3 scripts/metricas.py vincular`. Por cada `PENDIENTE`, decide con el título, la fecha, la duración y los
     candidatos que imprime: `vincular --fijar <pub> <flujo>:<id>` o `vincular --ajena <pub>` (lo que no salió del
     framework). Una segunda subida de la misma pieza se liga a la misma pieza. Termina con 0 pendientes.
4. **DIAGNÓSTICO**
   - `python3 scripts/metricas.py diagnostico --desde <desde> --mejoras sesiones/_analisis/<hoy>/mejoras.json`.
   - `python3 scripts/metricas.py rendimiento --por familia`, `--por visual`, `--por flujo` y `--por cierre`.
   - `python3 scripts/metricas.py alinear <pieza>` para la pieza con más vistas, la de menos y cada pieza con AN3 o
     AN4: escena por escena, qué se ve y qué dice la voz cuando la gente se va. Abre el `guion.json` entregado o la
     hoja de contacto de esas escenas solo si hace falta para explicar la caída.
   - Separa lo **sistémico** (el mismo código en ≥ 3 piezas: un problema del framework) de lo **puntual** (una pieza
     o una publicación). Lo sistémico va a mejoras del framework; lo puntual, al reporte (y a mejoras solo si un gate
     lo pudo haber atrapado).
5. **INVESTIGACIÓN EN LA WEB** (para cada problema sistémico)
   - Lee `referencias/analisis/benchmarks.md`. Si el tema ya tiene una fila de menos de 30 días, úsala.
   - Si no, ≤ 2 búsquedas (WebSearch, en inglés y en español) y ≤ 1 WebFetch de la mejor fuente: qué hacen los
     creadores y qué dicen las plataformas para ese problema (p. ej. «retention drop at 5–10 seconds short form»,
     «TikTok ending drop off loop»). Añade la fila a `benchmarks.md` con su fuerza (A/B/C de `referencias/ganchos.md`
     §1), su fuente y la fecha. Nada de la web se vuelve regla si contradice lo que mide el propio canal.
6. **PROPUESTA**
   - Edita `sesiones/_analisis/<hoy>/mejoras.json` (lo escribió `diagnostico --mejoras`). Cada mejora queda con: el
     `area`, el `archivo` exacto del framework (regla, rol, script o plantilla), el `problema` con la evidencia (piezas
     y números), la `propuesta` concreta (qué regla o gate cambia y cómo) y cómo se medirá en el próximo análisis.
     Junta las que tocan el mismo archivo y borra las que ya están pendientes en `memoria/mejoras.json`.
   - `python3 scripts/memoria.py --mejoras sesiones/_analisis/<hoy>/mejoras.json` y `make validate` (exit 0).
7. **REPORTE**
   - Una tabla por pieza: plataforma, vistas, retención a 3 s, tiempo medio, completado o «visto», seguidores.
   - Lo que más retiene y lo que menos (familia, visual, flujo), con la curva alineada de la mejor y la peor pieza (las
     escenas donde se va la gente).
   - Lo puntual que el usuario arregla a mano en las plataformas (erratas en títulos, una pregunta obligatoria sin
     responder, una restricción), con la pieza y el lugar exacto.
   - Las mejoras propuestas (id mNNN), cada una con su evidencia y su fuente de la web, y la lista de las pendientes de
     antes. **No apliques ninguna**: el usuario elige cuáles. Cuando las apruebe, aplícalas, corre `make test`
     (exit 0) y ciérralas con `python3 scripts/memoria.py --marcar-mejora <id> --como hecha`.

Reglas:
- `memoria/metricas.json` lo escribe solo `scripts/metricas.py`; las mejoras, solo `memoria.py --mejoras`.
- Las cifras del reporte salen de `metricas.py`, no de leer la página a ojo.
- Una correlación con n < 3 se dice como hipótesis, nunca como regla.
- La línea base es la del propio canal. Los umbrales de la web son una referencia.
