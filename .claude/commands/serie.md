---
description: Un tema contado en 3–5 partes de ≈ 90 s (TikTok, Reels, Shorts y 4:5), con una investigación compartida y un plan versionado — motor /historia (una historia partida por periodos) o /explica (un temario: un mecanismo por parte); cada parte se entiende sola, cierra con un puente hacia la siguiente sin anunciarla y lleva «Serie · Parte N de M» en el chip y en los captions (uso — /serie <tema> [3-5|3-8 con caso] [explica|caso] [sin-voz|fixture]; caso = un caso complejo en 3–8 partes de ≈ 130 s repartidas por temas (SE10–SE12); p. ej. /serie la historia de La Aurora 4 · /serie cómo funciona el crédito 3 explica; la parte N no se publica hasta que la N+1 tenga el guion aprobado)
---

Eres el coordinador de **/serie** de @DerekUrizar. Argumentos: "$ARGUMENTS".
- `<tema>`: lo que la serie cuenta. Sin tema, pregúntalo.
- `3`–`5`: cuántas partes (por defecto 3).
- `explica`: el motor temario (/explica); sin él, /historia.
- `caso`: modo caso (motor /historia): 3–8 partes de ≈ 130 s por TEMAS (`serie.py preparar … --caso`; el editor reparte los ids en `partes[].hechos`, SE10–SE12). En el Workflow, pasa `serie: {partes: M, caso: true}` y, en cada parte, `serie: {parte, de, titulo, siguiente, caso: true}`.
- `sin-voz`: cada parte con voz falsa (0 créditos), sin entrega ni registro.
- `fixture`: corre `make serie-fixture` (o `make serie-explica-fixture` con `explica`), abre el video de la parte 1 y termina.

La guía es `referencias/flujo-serie.md`. Nunca publiques. La serie reutiliza el motor entero: lee también
`.claude/commands/historia.md` (o `explica.md`). Sus reglas valen en cada parte: el usuario elige gancho y cierre, el
guion que el crítico rechaza no se graba, la voz va por secuencias y el reporte termina con «Mejoras al framework».

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - `python3 scripts/serie.py preparar "<tema>" --partes <M> [--motor explica]` → imprime `SERIE` (la carpeta
     `series/<fecha>-<slug>`) y, en la última línea, el `TRABAJO` de la investigación compartida (`sesiones/serie-<slug>`).
   - Avisa: la investigación tarda ~25–45 min (0 créditos). Cada parte, ~15–25 min y ≈ 1,100–1,400 créditos de voz (en modo caso, medido en Bancafé: 141–169 s y ≈ 2,100–2,450 créditos por parte).
2. **PLAN E INVESTIGACIÓN COMPARTIDA** (Workflow del motor, una vez)
   - Workflow `historia` (o `explica`) con `args: {"trabajo": "<TRABAJO>", "tema": "<tema>", "serie": {"partes": M},
     "hasta": "consolidar"}`. El editor escribe el encuadre del tema entero y el plan de partes (`encuadre.serie.partes`,
     `serie.py plan --check`: SE1, SE2). Los investigadores y verificadores cubren TODA la serie. El Workflow se detiene
     con `veredicto: "investigada"`.
   - `python3 scripts/serie.py cobertura <TRABAJO> --check` (SE3: ≥ 4 hechos por parte en su periodo, o ≥ 2 afirmaciones
     o cifras por parte en el temario). Si falla, relanza solo el eje que falta o propón al usuario juntar dos partes.
   - **Muéstrale el plan al usuario** (`python3 scripts/serie.py digesto <SERIE>`): títulos, preguntas, periodos o
     mecanismos, lo que revela cada parte y los puentes. Con su visto bueno (o sus cambios: el editor re-encuadra y el
     plan sube de versión), `python3 scripts/serie.py plan <TRABAJO> --check --aprobar`.
3. **LOS GUIONES DE TODAS LAS PARTES** (en orden, sin voz; regla del usuario 2026-11-09, SE17)
   - Para cada parte: `serie.py parte`, el Workflow con `desde: "ganchos"` (el usuario elige gancho y cierre), el crítico
     aprueba, `serie.py guion-aprobado`. **No se graba ninguna voz todavía.**
   - Con TODAS las partes con guion: `python3 scripts/serie.py completa <SERIE> --check` (SE17: faltan guiones, hechos,
     citas, frases, presentaciones y siglas repetidas entre CUALQUIER par de partes, y la cadena real de puentes) y
     escribe `<TRABAJO>/serie_completa.md`. Luego un `video-critico` en «modo serie completa» lee ese archivo entero:
     coherencia del arco, repeticiones, saltos, revelaciones adelantadas o pagadas dos veces, conceptos explicados dos
     veces o nunca. Sus arreglos van con `historia.py aplicar` en la parte que toca (una parte ya entregada queda fija
     salvo que el usuario pida tocarla). Repite `completa --check` hasta 0 fallas y `--aprobar`.
   - **La sesión lee ella misma `serie_completa.md` de principio a fin** (no basta el crítico ni el script): ambigüedades («que lo detuviera»), hechos que el oyente no entiende, cifras que chocan. Lo arregla con `historia.py aplicar` y vuelve a `completa --check --aprobar`.
   - `historia.py voz` se niega a grabar una parte nueva hasta que la serie completa está aprobada y ningún guion cambió
     después (huella).
4. **VOZ Y VIDEO DE CADA PARTE** (en orden; una parte puede hacerse otro día)
   - (El TRABAJO de la parte ya existe del paso 3.) `python3 scripts/serie.py parte <SERIE> <N>` → el TRABAJO de la parte (`<TRABAJO>/parte-N`): la investigación
     copiada, el encuadre de la parte, formato ≈ 90 s, paleta y música de la serie y la parte siguiente. En /historia la
     parte solo ve los hechos hasta el fin de su periodo (las revelaciones de las partes siguientes no se adelantan).
   - Workflow del motor con `args: {"trabajo": "<TRABAJO>/parte-N", "tema": "<tema> · Parte N: <título>", "desde":
     "ganchos", "serie": {"parte": N, "de": M, "titulo": "<título>", "siguiente": {"n": N+1, "titulo": "…"}}}`. Lo demás,
     como en `/historia` (o `/explica`): el usuario elige el gancho, el crítico aprueba, el usuario elige el cierre (en
     las partes 1…M−1 las opciones son puentes).
   - Con el guion aprobado: `python3 scripts/serie.py guion-aprobado <TRABAJO>/parte-N` (habilita publicar la parte
     anterior).
   - Voz (MCP, por secuencias) o voz falsa con `sin-voz`, `tiempos`, `grabar`, `montar`, `revisar` en 9:16 y 4:5, con
     los comandos del motor sobre `<TRABAJO>/parte-N` (o de una vez: `python3 scripts/historia.py producir <TRABAJO>/parte-N`).
   - `python3 scripts/serie.py entregar-parte <TRABAJO>/parte-N` → `series/<fecha>-<slug>/parte-N/` y `serie.md`.
5. **CIERRE**
   - `python3 scripts/memoria.py --serie <SERIE>` y `make validate` (exit 0) tras cada parte entregada.
6. **REPORTE**
   - La tabla de `serie.md`: cada parte con su estado y si ya se puede publicar (la N, cuando la N+1 tiene guion
     aprobado). Qué fijar en el perfil (la Parte 1) y el nombre de la playlist o lista.
   - Por parte, lo del reporte del motor (gancho, cierre, duración, créditos).
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo), registradas con
     `python3 scripts/memoria.py --mejoras <archivo>` (`flujo: serie`) y sin aplicarlas sin que el usuario lo pida.

Reglas:
- Una sola investigación para toda la serie; cada parte se cuenta sola (SE4: nada de «como vimos»).
- El puente pregunta, no responde ni anuncia («en la próxima parte» lo rechazan P2 y F9). Después del puente, la voz
  invita (`cierre.invitacion`, SE9): «Sígueme: en la segunda parte te cuento …», con lo que cuenta la siguiente; la
  última parte no invita.
- Desde la parte 2, la pantalla final y los captions mandan a la Parte 1 fijada en el perfil (SE8); fíjala al publicarla.
- Paleta y música de la serie en todas las partes (SE5); 75–110 s por parte (< 61 s falla, SE7).
