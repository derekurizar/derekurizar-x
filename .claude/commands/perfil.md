---
description: Retrato de un departamento o grupo frente al país en 5–8 tarjetas, sin giro — alias de /hilo en modo perfil: cada tuit intermedio es una dimensión (población, pobreza, salud, educación, seguridad, economía) que compara sujeto y país en la misma fuente y año (uso — /perfil <departamento o grupo> [smoke|fixture]; p. ej. /perfil Alta Verapaz)
---

Eres el coordinador del flujo **/hilo** de @DerekUrizar en modo **perfil**.
Argumentos del usuario (el sujeto; puede traer `smoke` o `fixture`):
"$ARGUMENTS". Sigue `.claude/commands/hilo.md` al pie de la letra (preflight,
Workflow `hilo`, post-checks, reglas) con tres diferencias:

1. El modo es fijo: `"modo": "perfil"` en `args` (no lo tomes del sujeto ni lo
   quites de él; el sujeto va literal como `tema`).
2. No se consulta el banco de ideas (`idea = null`) salvo `idea:<id>` explícito.
3. Al final muestra además el bloque del modo (`bloque_modo`: el sujeto, el tipo y las dimensiones con su año).
