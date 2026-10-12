---
description: Guatemala frente a otros países en UNA tarjeta — alias de /dato en modo vs: todos los países de la misma fuente, edición y periodo, Guatemala destacada, sin «ganamos/perdemos» (uso — /vs [pista] [smoke|fixture]; p. ej. /vs carga tributaria en Centroamérica)
---

Eres el coordinador del flujo **/dato** de @DerekUrizar en modo **vs**.
Argumentos del usuario (una pista opcional; puede traer `smoke` o `fixture`):
"$ARGUMENTS". Sigue `.claude/commands/dato.md` al pie de la letra (preflight,
Workflow `dato`, post-checks, reglas) con dos diferencias:

1. El modo es fijo: `"modo": "vs"` en `args` (no lo tomes de la pista ni lo
   quites de ella; la pista va literal).
2. Al final muestra además el bloque del modo (`bloque_modo`: países, fuente común, periodo y per cápita).
