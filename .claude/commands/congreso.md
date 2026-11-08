---
description: Una ley del Congreso de Guatemala en un video vertical de menos de un minuto para TikTok, Reels y Shorts, más su 4:5 — qué buscaba, cuántos votos tuvo a favor y en contra frente al umbral, y algunos diputados de cada lado, con el hemiciclo que se llena asiento por asiento, el portal desde el gancho y los retratos oficiales; votos del registro nominal oficial (congreso.gob.gt vía Chrome), cierre con «Sígueme en» (uso — /congreso [<iniciativa N>|<tema>] [sin-voz|fixture]; sin argumento propone las leyes votadas en los últimos días; voz de ElevenLabs ≈ 700–900 créditos; sin-voz arma el video con voz falsa, 0 créditos; fixture corre la maqueta)
---

Eres el coordinador del flujo **/congreso** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- Un número («6347», «iniciativa 6347»): la iniciativa del video.
- Un texto («la ley de ciberseguridad», «decreto 26-2026») o nada: **propones** (paso 1) y el usuario elige.
- `sin-voz`: todo el flujo con **voz falsa** (0 créditos), para revisar el video antes de gastar; no entrega.
- `fixture`: corre `make congreso-fixture` (la Ley de Ciberseguridad congelada, sin web ni voz), abre el video y termina.

La guía es `referencias/flujo-congreso.md`. Nunca publiques. Nunca generes música ni efectos (catálogos fijos).
**Quién votó qué es un hecho del registro: el video no califica a nadie (CG5) y nombra a los dos lados (CG4).**
**El guion que el crítico rechaza no se graba con voz sin decisión del usuario.**

1. **DATOS** (Claude in Chrome, solo lectura; `referencias/congreso/captura.md`)
   - `make doctor` (exit 0).
   - Abre una pestaña nueva en `https://www.congreso.gob.gt/seccion_informacion_legislativa/votaciones_pleno`, pega
     `referencias/congreso/captura.js` con `javascript_tool` y corre `CG.correr({desde: "<día siguiente a la última
     fecha de la base>"})` (la última fecha la imprime `python3 scripts/congreso.py proponer`). Si hay diputados nuevos o
     pasaron más de 30 días desde el corte del padrón, añade `padron: true`.
   - Saca el JSON (textarea → `cmd+a cmd+c` → `pbpaste > sesiones/_congreso/capturas/<fecha>_<sesiones>.json`) y corre
     `python3 scripts/congreso.py importar <captura>` (CG1; con `padron: true`, antes `congreso.py padron <captura>`).
   - Sin iniciativa: `python3 scripts/congreso.py proponer` y pregunta con AskUserQuestion cuál (4 opciones con la
     votación decisiva y el margen; busca antes el nombre de cada ley en las notas del Congreso con `CG.textos`).
2. **LA LEY**
   - `python3 scripts/congreso.py preparar <iniciativa> --slug <ley-de-…>` → `TRABAJO` y la votación decisiva.
   - Busca qué buscaba la ley: la nota oficial del Congreso de esa sesión (`/noticias_congreso/…`, la portada las enlaza)
     y, si hace falta, el PDF de la iniciativa (`CG.correr({textos: [...], pdfs: [...]})`) o una nota de prensa con
     `historia.py leer`. `congreso.py leer <TRABAJO> <captura>` guarda los textos y la foto oficial de la nota.
   - Escribe `<TRABAJO>/ley.json` (plantilla en `referencias/flujo-congreso.md`): título, `nombre_corto`, 1–4
     `que_busca` con su cita literal, `estado` (vigencia, sanción, veto) con cita, `cifras` (penas, plazos, montos) y
     `citas`. `python3 scripts/congreso.py ley <TRABAJO> --check` hasta exit 0 (CG2).
   - Elige a quién nombrar con el digesto («Cruzados», bancadas, `notoriedad` del padrón: el presidente del Congreso,
     quien propuso la urgencia, un exjefe de bancada): **hasta 3 por lado, cada uno de un partido distinto y de los
     partidos que más votos dieron a ese lado** (menos solo si votaron menos partidos; CG4, decisión del usuario 2026-11-04). Captura sus retratos (`CG.correr({fotos: [ids]})`)
     y `congreso.py fotos <TRABAJO> --captura <json> --diputados "Nombre completo" …`.
3. **GUION** (lo escribes tú con `<TRABAJO>/digesto.md`; 5–7 escenas, < 60 s)
   - Gancho con la foto del pleno y `mini` (el hemiciclo del círculo que abre el portal) → hemiciclo `llenar` + `umbral`
     → qué buscaba (`afirma`) → hemiciclo `foco` con los nombres (`diputados` declarados) → por eso (`estado`) → cierre de
     una pantalla. Frases cortas, «pero / por eso», cifras en dígitos y solo las del digesto.
   - **El usuario elige gancho y cierre** (2026-11-03): propón 5 ganchos de familias distintas (contraste del umbral,
     paradoja, la cifra a escala, quién decidió, qué cambia para ti) y, con el guion armado, 5 cierres de una pantalla
     (`referencias/cierres.md`); AskUserQuestion (4 botones, la quinta en el texto; en «Otro» dicta el suyo).
   - `python3 scripts/congreso.py guion <TRABAJO> --check` hasta exit 0 (CG3–CG10, V1–V5, V9, F1–F8).
4. **CRÍTICA** (0 créditos): el agente `video-critico` en **Modo congreso** (`referencias/roles/video-critico.md`) con
   `TRABAJO` y `vuelta: 1`; aplica sus `bloquea` con el texto exacto, repasa el gate y, si hubo faltas, `vuelta: 2`. Si no
   pasa tras 2 vueltas, pregunta al usuario antes de gastar.
5. **VOZ** — igual que `/sabias` paso 4 (`congreso.py voz`, nodos `tts` con el prompt exacto, `generations_count: 1`,
   Scribe, `descargar --estado`); el flujo de ElevenLabs se llama «Congreso · <slug>». Con `sin-voz`: `voz-falsa`.
6. **TIEMPOS, GRABAR, MONTAR Y REVISAR**: `tiempos` (CG7: ≤ 59.5 s reales; V6, V10, V16) → `escuchar` (V11, con voz real)
   → `grabar` (V13) → `montar` (V8) → `revisar`; lee **una vez** `revision/contacto.png` (el hemiciclo, el sello, la
   ficha del diputado, el portal). Luego el 4:5 con `--formato 4:5`.
7. **ENTREGAR** (no con `sin-voz`): `congreso.py entregar <TRABAJO>` → `congreso/<fecha>-<slug>/`;
   `python3 scripts/memoria.py --congreso congreso/<fecha>-<slug>` y `make validate` (exit 0). Abre el video.
8. **REPORTE**: rutas, duración, la ley y la votación (a favor, en contra, umbral, margen), a quién nombró y por qué,
   por escena `E<n> · tipo · voz`, puntajes del crítico, créditos, el caption de TikTok listo para pegar y, al final,
   **Mejoras al framework** (`memoria.py --mejoras` con `flujo: "congreso"`; no se aplican sin el usuario).

Reglas:
- Las cifras de la votación salen del listado nominal oficial; el umbral, de la Ley Orgánica (81; 107 en urgencia nacional).
- La bancada es la actual del sistema de votación: en una ley vieja, dilo («hoy en Vamos»).
- Cierra la pestaña de Chrome al terminar. Nunca envíes formularios ni inicies sesión en el sitio del Congreso.
