---
description: Hace N años frente a hoy en UNA tarjeta — alias de /dato en modo antes: dos puntos de la misma serie y fuente separados ≥5 años, gancho antes_despues, nominal declarado (uso — /antes [pista] [smoke|fixture]; p. ej. /antes tipo de cambio hace 20 años)
---

Eres el coordinador del flujo **/dato** de @DerekUrizar en modo **antes**.
Argumentos del usuario (una pista opcional; puede traer `smoke` o `fixture`):
"$ARGUMENTS". Sigue `.claude/commands/dato.md` al pie de la letra (preflight,
Workflow `dato`, post-checks, reglas) con dos diferencias:

1. El modo es fijo: `"modo": "antes"` en `args` (no lo tomes de la pista ni lo
   quites de ella; la pista va literal).
2. Al final muestra además el bloque del modo (`bloque_modo`: los dos años y si es nominal).
