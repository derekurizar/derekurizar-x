# Hilos · @DerekUrizar

Framework de Claude Code para producir **hilos de X con datos de Guatemala**
que cuentan una historia: a partir de un tema, agentes orquestados investigan,
verifican cifras, escriben el guion y generan una tarjeta 1080×1080 por tuit.

```
/hilo precios de combustibles en Guatemala 2026
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
con fuente y handle. Once plantillas: cifra, línea, barras verticales y
horizontales, antes/después, dona, pendiente, pesas, waffle, mapa de calor y
mapa por departamento.

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
