---
description: Serie de 22 videos «<departamento> frente al país» — /perfil del departamento con el canon de dimensiones y luego /video sobre ese hilo, con el modo departamento detectado solo (gancho de identidad, mapa, ranking en ventana «N.º X de 22», cierre que nombra el departamento, caption «Para alguien de…»; gates D1–D9) (uso — /departamento <nombre|siguiente|tablero> [corto|medio] [sin-voz|fixture]; p. ej. /departamento Huehuetenango; siguiente = el primero del orden sin video; tablero = el avance de los 22; fixture corre la maqueta)
---

Eres el coordinador del flujo **/departamento** de @DerekUrizar. Argumentos: "$ARGUMENTS".
- La primera palabra es el **departamento** (nombre, alias como «Huehue» o «Xela», o código `GT13`), `siguiente`
  (el primero del orden del canon sin video) o `tablero` (solo muestra el avance de la serie y termina).
- `corto` o `medio` fijan la duración del video (por defecto `medio`; nunca menos de 61 s reales: D8).
- `sin-voz` arma el video con voz falsa (0 créditos) y no entrega ni registra; `fixture` corre `make
  departamento-fixture` (la maqueta de Huehuetenango, sin web ni créditos), muestra su resultado y termina.

Es **/perfil → /video**: no hay workflow propio. La guía es `referencias/flujo-departamento.md`; el canon de
dimensiones, el orden y los alias viven en `referencias/departamentos.json` (lo lee solo `scripts/departamentos.py`).
Nunca publiques. La invitación a compartir es **implícita**: la frase final nombra el departamento y el caption dice
«Para alguien de <depto>»; nunca se pide en la voz (F4 sigue vigente).

1. **PREFLIGHT**
   - `tablero` → corre `python3 scripts/departamentos.py --tablero`, muéstralo y termina.
   - `fixture` → corre `make departamento-fixture`, muestra la ruta de `sesiones/_fixture_departamento/salida/`
     (video.mp4, video_4x5.mp4, contacto.png, caption.md) y termina.
   - `python3 scripts/departamentos.py --check` (exit 0). Si el canon sigue en «propuesta», dilo al usuario en una línea
     (las dimensiones no están aprobadas) y sigue solo si lo confirma.
   - Resuelve el departamento: `siguiente` → `python3 scripts/departamentos.py --siguiente --json`; si no,
     `python3 scripts/departamentos.py --resolver "<nombre>"` (exit 1 = no lo reconoce: DETENTE y dilo). Anota `GTxx` y
     el nombre oficial.
   - Mira su fila en `python3 scripts/departamentos.py --tablero --json`: si ya tiene **video**, avísalo y pregunta
     si se rehace. Si tiene **hilo** (`hilo_ruta`), ese hilo es el que va a video (salta el paso 2).
2. **HILO (/perfil con el canon)** — solo si no hay hilo perfil listo de ese departamento.
   - `python3 scripts/departamentos.py --directiva <GTxx>` imprime el **canon** para el editor, el investigador y el
     guionista.
   - Sigue `.claude/commands/perfil.md` (que sigue `hilo.md`) con el sujeto = el nombre oficial y, en `args` del
     Workflow `hilo`, además: `"canon": "<la salida de --directiva, tal cual>"` y `"min_tuits": 7`. Si editaste
     `.claude/workflows/hilo.js` en esta sesión, pásalo con `scriptPath`.
   - El workflow exige ≥ 7 tuits, `perfil.codigo`, el `canon` de cada dimensión y una tarjeta `mapa` con los 22 que
     destaca al departamento (también G1 de `ensamblar.py`). Al volver, la ruta es `hilos/<fecha>-perfil-…/`.
3. **VIDEO (/video sobre ese hilo)**
   - Sigue `.claude/commands/video.md` al pie de la letra con el slug del hilo y la duración (por defecto `medio`).
     `video.py preparar` detecta solo el modo (hilo `modo: perfil` y `perfil.tipo: departamento`): `video.json` lleva
     `departamento` (código, alias, puestos calculados de cada desglose de los 22), `palabra_clave` y `piso_s: 61`, y el
     digesto la sección «Modo departamento» que leen el agente de ganchos, el guionista y el crítico.
   - `guion --check` corre además D1–D7 y D9; `tiempos`, D1 con la voz real y D8; `entregar`, D3. Una falla D se arregla
     como cualquier otra del gate (el guionista o el crítico); no la saltes.
   - `sin-voz`: después del Workflow `video`, en lugar de la voz del MCP corre `voz-falsa`, `tiempos`, `grabar`, `montar`
     y `revisar` (9:16 y 4:5) sobre `TRABAJO`; muestra `revision/contacto.png` y NO corras `entregar` ni `memoria.py`.
   - Con voz: `entregar` y `python3 scripts/memoria.py --video hilos/<fecha>-<slug>/video` (registra `sujeto`,
     `serie: "departamentos"` y `codigo`), `make validate` (exit 0).
4. **CIERRE**: muestra lo que muestra `/video` (y el bloque del perfil si hiciste el hilo), luego
   `python3 scripts/departamentos.py --tablero` con la fila nueva, y termina con «Mejoras al framework» (regla 10).
