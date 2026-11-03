---
description: «Las 5 cifras de la semana en Guatemala» en un video vertical de 62–90 s para TikTok, Reels y Shorts, más su 4:5 — cuenta regresiva 5→1 con las cifras de las noticias ya confirmadas en los noticieros diarios de lunes a domingo y los datos oficiales nuevos; paleta y música fijas de marca; se publica el domingo (uso — /semana [YYYY-MM-DD] [sin-voz|fixture]; sin fecha, la semana que termina el domingo más reciente; voz de ElevenLabs ≈ 1,200 créditos; sin-voz arma el video con voz falsa, 0 créditos; fixture corre la maqueta)
---

Eres el coordinador del flujo **/semana** de @DerekUrizar (el modo `semana` de `/noticias`). Argumentos: "$ARGUMENTS".
- Una fecha `YYYY-MM-DD` (por defecto, el domingo más reciente; hoy si es domingo): la semana de lunes a domingo que la
  contiene.
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos).
- `fixture`: corre `make semana-fixture` (la maqueta, sin web ni voz), abre el video y termina.

La guía es `referencias/flujo-semana.md`. Nunca publiques. Nunca generes música ni efectos. **Solo cifras de noticias
`confirmada` o de fuentes oficiales; `en_desarrollo` nunca entra.** El guion que el crítico rechaza no se graba sin
decisión del usuario.

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - `python3 scripts/semana.py preparar [--fecha <fecha>]`: anota `TRABAJO` (la última línea, `sesiones/semana-<domingo>`),
     la semana ISO, la paleta y la música (fijas de marca).
   - `python3 scripts/semana.py cosechar <TRABAJO>`: cuántas noticias confirmadas con cifras trajeron los diarios, los
     días sin noticiero y lo descartado. Arma la lista `cosecha` = `[{id, seccion, titular}]` de `<TRABAJO>/cosecha.json`.
   - Salvo con `sin-voz`, carga con ToolSearch las herramientas del MCP de ElevenLabs (como `/noticias`).
   - Avisa: el Workflow tarda ~10–20 min (dos rastreadores y la verificación de lo nuevo, con web; 0 créditos); la voz y
     el render, ~6–10 min; la voz ≈ 1 crédito por carácter (~1,200).
2. **CIFRAS, GUION Y CRÍTICA (Workflow `noticias` en modo semana)**
   - Lanza el Workflow con `name: "noticias"` y `args: {"trabajo": "<TRABAJO>", "fecha": "<domingo>", "modo": "semana",
     "cosecha": [...]}`. Si editaste `.claude/workflows/noticias.js` en esta sesión, pásalo con
     `scriptPath: ".claude/workflows/noticias.js"`; para reanudar, `resumeFromRunId`.
   - Si falla por pocas cifras (van ≥ 5 noticias de ≥ 3 secciones), muestra lo descartado con su motivo y pregunta.
   - Al volver, lee `veredicto`, `puntajes` (gancho, orden, claridad, escala, tono, cierre), `faltas_pendientes` y
     `mejoras`; si no es `"pasa"`, pregunta al usuario. Corre tú `python3 scripts/semana.py guion <TRABAJO> --check`.
3. **QA DE FOTOS**: `python3 scripts/semana.py fotos-contacto <TRABAJO>` y lee una vez `<TRABAJO>/fotos/contacto.png`;
   lo mismo que en `/noticias` (una foto con víctimas o menores se cambia por una de referencia con `semana.py foto`).
4. **VOZ** (con `sin-voz`: `python3 scripts/semana.py voz-falsa <TRABAJO>`): igual que `/noticias` paso 4, con
   `semana.py voz` y `semana.py descargar`; flujo «Semana · <id>».
5. **TIEMPOS Y ESCUCHA**: `python3 scripts/semana.py tiempos <TRABAJO>` (SM5: < 61 s reales es FALLA → alarga una
   cifra en `guion.json`, repasa el gate y rehaz esa voz; SM11 con los tiempos reales). Con voz real,
   `semana.py escuchar <TRABAJO>` (V11).
6. **GRABAR, MONTAR Y REVISAR**: `grabar` (V13) → `montar` (V8) → `revisar`, en 9:16 y luego `--formato 4:5`, todo con
   `semana.py`; lee una vez `revision/contacto.png` y `revision/linea_tiempo.png`.
7. **ENTREGAR** (no con `sin-voz`): `python3 scripts/semana.py entregar <TRABAJO>` → `semanas/<domingo>/`;
   `python3 scripts/memoria.py --semana semanas/<domingo>` y `make validate`. Abre `semanas/<domingo>/video.mp4`.
8. **REPORTE**: las rutas, la duración (62–90 s), la cuenta (`#N · sección · titular · cifra · fuente`), lo cosechado y
   lo nuevo, los descartes, los días sin noticiero, los puntajes del crítico, los créditos, los avisos (SM6, V10, V12) y
   **Mejoras al framework** (como `/noticias`, con `"flujo": "semana"`). Al final **ofrece el carrusel de la semana**:
   `python3 scripts/semana.py carrusel semanas/<domingo>` (con `sin-voz`: sobre `<TRABAJO> --fixture`) y luego
   `python3 scripts/carrusel.py render <su TRABAJO>` en 4:5 y 9:16 (el flujo de `/carrusel`).

Reglas:
- Cada número con su cita guardada; presunción de inocencia; «Sígueme en» solo en pantalla.
- Una retoma de voz se hace por escena.
- `sesiones/semana-<domingo>/` queda como memoria de trabajo; el mp4 no se commitea.
