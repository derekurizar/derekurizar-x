---
description: El tema explicado con sus números en 3–6 tarjetas, sin giro ni tesis — alias de /hilo en modo explica: cada tuit intermedio es un paso con su cifra y un texto que lo explica en lenguaje llano; evergreen (uso — /explica <tema> [smoke|fixture]; p. ej. /explica cómo se calcula la tarifa de luz)
---

Eres el coordinador del flujo **/hilo** de @DerekUrizar en modo **explica**.
Argumentos del usuario (el tema; puede traer `smoke` o `fixture`):
"$ARGUMENTS". Sigue `.claude/commands/hilo.md` al pie de la letra (preflight,
Workflow `hilo`, post-checks, reglas) con tres diferencias:

1. El modo es fijo: `"modo": "explica"` en `args` (no lo tomes del tema ni lo
   quites de él; el tema va literal como `tema`).
2. No se consulta el banco de ideas (`idea = null`) salvo `idea:<id>` explícito.
3. Al final muestra además el bloque del modo (`bloque_modo`: la pregunta y los pasos).
