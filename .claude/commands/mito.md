---
description: «Mito o realidad» en un video vertical de 62–90 s para TikTok, Reels y Shorts, más su 4:5 — alias de /explica en modo mito: una creencia que circula en Guatemala decidida con cifras verificadas; el veredicto (MITO · REALIDAD · A MEDIAS) lo calcula el código y se ve en el cuadro 0; si no hay datos suficientes, se detiene sin video (uso — /mito <creencia> [sin-voz|fixture]; p. ej. /mito la remesa promedio es de $1,000)
---

Eres el coordinador del flujo **/explica** de @DerekUrizar en modo **mito**.
Argumentos del usuario (la creencia; puede traer `sin-voz` o `fixture`): "$ARGUMENTS". Sigue
`.claude/commands/explica.md` al pie de la letra (preflight, Workflow `explica`, voz, render, entrega, reporte, retoques)
con tres diferencias:

1. El modo es fijo: `preparar "<creencia>" --modo mito` y `"modo": "mito"` en `args` (la creencia va literal como tema;
   sin duración: un mito dura ≈ 75 s). `fixture` = `make mito-fixture`.
2. Si el Workflow devuelve `veredicto: "sin_datos"`: **detente** y avisa «sin datos para un veredicto» con sus faltas
   (`faltas_pendientes`); no hay video.
3. En el reporte, primero el veredicto (`mito.veredicto`), la creencia, la cifra que decide con su periodo y fuente, lo
   que vio el oyente del primer cuadro (`mito.primer_cuadro`, MI10) y la evidencia de circulación.
