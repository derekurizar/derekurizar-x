---
description: Brecha por departamento en UNA tarjeta (mapa de los 22 + extremos) — alias de /dato en modo mapa: tasa per cápita con denominador INE y gancho brecha_territorial (uso — /mapa [pista] [smoke|fixture]; p. ej. /mapa retornados por cada mil habitantes)
---

Eres el coordinador del flujo **/dato** de @DerekUrizar en modo **mapa**.
Argumentos del usuario (una pista opcional; puede traer `smoke` o `fixture`):
"$ARGUMENTS". Sigue `.claude/commands/dato.md` al pie de la letra (preflight,
Workflow `dato`, post-checks, reglas) con dos diferencias:

1. El modo es fijo: `"modo": "mapa"` en `args` (no lo tomes de la pista ni lo
   quites de ella; la pista va literal).
2. Al final muestra además el bloque del modo (`bloque_modo`: per cápita y denominador).
