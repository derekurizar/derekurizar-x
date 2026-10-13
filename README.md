# Hilos · @DerekUrizar

Framework de Claude Code para producir **hilos de X con datos de Guatemala**
que cuentan una historia: a partir de un tema, agentes orquestados investigan,
verifican cifras, escriben el guion y generan una tarjeta 1080×1080 por tuit.
También produce **datos sueltos** (una tarjeta) en varios géneros.

```
/hilo precios de combustibles en Guatemala 2026
/dato remesas                      # un dato impactante en una tarjeta
/vs carga tributaria               # Guatemala frente a otros países
/mapa retornados por cada mil      # brecha por departamento
/antes tipo de cambio hace 20 años # hace N años frente a hoy
/explica cómo se calcula la luz    # el tema explicado con sus números (3–6 tarjetas)
/perfil Alta Verapaz               # retrato frente al país (5–8 tarjetas)
/fecha                             # qué ocasiones con dato vienen en 30 días
/ideas                             # banco de ideas para hilos
```

Deja en `hilos/2026-09-28-<slug>/`:

- `hilo.html` — vista previa: cada tuit con su texto (a menudo vacío: la imagen
  lo dice), la tarjeta y el alt-text, con contador de peso X y botones de copiar.
- `contacto.png` — todas las tarjetas en una hoja; `tuit_N.png` — tarjetas
  2160×2160 listas para subir a X.
- `post.md` — texto listo para pegar, datos clave, lo que el hilo NO afirma, fuentes.
- `datos.json` — cifras verificadas con evidencia, veredicto y dónde aparecen.

## Quickstart

```bash
git clone … && cd derekurizar-x
npm install          # Playwright 1.59.1 (reutiliza el Chromium instalado)
make doctor          # node, Playwright, python, fuentes, agentes
make test RAPIDO=1   # pruebas rápidas (sin catálogo)
```

Luego **reinicia Claude Code** en esta carpeta (los agentes de `.claude/agents/`
se registran al arrancar) y:

```
/hilo fixture                  # ~5 min, sin web: prueba guion → tarjetas → entrega
/hilo smoke remesas 2025       # ~10–15 min con web, 1 eje, 3 tuits
/hilo <tema>                   # corrida completa (~25–40 min)
/dato fixture                  # ~3 min, sin web: solo el productor
/dato [vs|mapa|antes] <pista>  # un dato (~8–15 min); con modo cambia el género
/hilo [explica|perfil] <tema>  # hilo sin giro: explicador o perfil
```

Abre `hilo.html`, revisa `contacto.png`, y publica a mano: PNG + texto + alt-text.

## Cómo funciona

```
/hilo [tema] ──▶ Workflow hilo.js
   editor ──▶ investigador ⇢ verificador (por eje, en paralelo, con presupuesto)
          ──▶ guionista (tesis + 4–8 tuits con gancho (`hook_tipo`), visual por tuit)
          ──▶ visualistas (guion → tarjetas, gate de render, QA sobre el PNG)
          ──▶ productor (ensamblado, gate de coherencia, hoja de contacto, memoria)
```

Las tarjetas siguen el brief visual (`referencias/diseno/brief/`): una paleta
por tema, titular en Instrument Serif, kicker y cifras en JetBrains Mono, pie
con fuente y handle. Veintiséis plantillas (`templates/graficos/`): cifra, línea,
barras verticales y horizontales, antes/después, dona, pendiente, pesas, waffle,
mapa de calor, mapa por departamento, bullet, embudo, divergente, apilada,
pirámide, treemap, dispersión, hemiciclo, pequeños múltiplos, barras + línea,
línea de tiempo, barras agrupadas, pictograma, área apilada y cascada.

## Informes de investigación

Además de tarjetas, el mismo sistema visual arma **documentos largos** (Letter, PDF)
desde un `informe.json`: portada, índice automático, resumen, tablero de cifras,
aperturas de capítulo, páginas de cuerpo con figuras (la tarjeta del hilo embebida
o el gráfico redibujado sobre papel), mapa, cronología, tablas, conclusiones,
método, glosario, anexos y contraportada. Las cifras con `id` se cruzan con
`datos.json` (solo verificadas o ajustadas) antes de escribir nada.

```bash
make informe-ejemplo                         # investigacion/ejemplos/dengue-2026 → salida/informe.pdf
make informe DIR=<carpeta con informe.json>  # cualquier informe; PAL=<paleta> para probar otra
```

Plantillas en `investigacion/` (ver su `README.md`); contrato en `referencias/diseno/informe.md`.

## Cuando algo falla

- **«El agente hilo-… no está registrado en esta sesión»**: reinicia Claude
  Code (los agentes se cargan al arrancar). Si editaste `hilo.js` en la sesión,
  lanza con `scriptPath: ".claude/workflows/hilo.js"`.
- **El workflow se cayó a mitad**: `Workflow({ scriptPath, resumeFromRunId, args })`
  reutiliza los agentes ya terminados.
- **Un gate rechazó el guion o una tarjeta**: el mensaje dice el tuit y el
  motivo; el workflow ya intentó repararlo hasta dos veces.
- **Medir una corrida**: `make costo` (tokens, herramientas y minutos por agente).

## Estructura

Ver `CLAUDE.md` (mapa del proyecto, reglas de oro y comandos),
`referencias/flujo-hilo.md` (índice del flujo) y `referencias/roles/` (guía por agente).
