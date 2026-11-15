---
description: Un video vertical 100 % en 3D, la «maqueta que vuela» (9:16 + 4:5, de 45 s a 3 min), para temas donde el lugar o el mecanismo se entienden mejor viéndolos moverse: una cámara recorre un mundo simple mientras la voz cuenta (uso — /video-3d &lt;tema|desde:&lt;pieza&gt;&gt; [sin-voz])
---

# /video-3d $ARGUMENTS

Guía completa: `referencias/flujo-video3d.md` (léela antes de empezar). Contrato del motor:
`referencias/diseno/maqueta3d.md`. El guion lo escribe el Workflow `video3d` (director, constructor y crítico); la sesión prepara, investiga, pregunta y produce.

1. **Preflight.** `make doctor`. Decide si el tema es de 3D: **el lugar o el mecanismo se entienden mejor viéndolos
   moverse** (una falla, una ruta, un barrio; cómo se forma una cola, cómo viaja una señal). Si no, propón el flujo que sí le
   toca y no sigas.
2. **Preparar.** `python3 scripts/video3d.py preparar <slug> --tema "<tema>" --musica-tema <tema de MUSICA_TEMAS>
   [--desde <trabajo o entrega ya investigada>] [--duracion 45]` (de 20 a 180 s: hasta 3 min, como los demás videos; elige la duración por lo que hay que recorrer, y un estilo de Blender en un video largo tarda más de una hora por formato). Con `desde:` se reutilizan las cifras verificadas.
3. **Investigación.** Lo que falte se investiga y verifica con los agentes de /historia (`historia-investigador` ⇢
   `historia-verificador`, cita literal guardada con `historia.py leer`). **Los geodatos también se verifican**: qué
   tramo, de dónde a dónde, hacia dónde. Suma lo verificado con `video3d.py datos <TRABAJO> --sumar <archivo>` y
   anota en el guion lo que NO se puede dibujar (`no_afirmar`).
4. **Workflow `video3d`** (0 créditos; `.claude/workflows/video3d.js`): `{trabajo: <TRABAJO>, tema: "<tema>", angulo?}`.
   La sesión ya no escribe a mano la dirección, los ganchos, el guion ni el `maqueta.json`: el agente `video3d-director`
   escribe la **dirección visual por frase** (`direccion.json`: idea visual, criterio, escala `pais|ciudad|esquema`,
   estilo con razón y confianza, el verbo del catálogo que cuenta cada oración), un `maqueta-constructor` construye lo
   que el catálogo no tiene (sus `briefs`, ≤ 3 a la vez; `scripts/maqueta_modulo.py check` → `registrar`), el director
   escribe los 5 ganchos (`ganchos --check --cuadros`), el `video-critico` recomienda uno, el director escribe el guion
   (`guion --check`, `storyboard`), el crítico en «Modo 3D» lo revisa (≤ 2 pasadas) y el director propone 5 cierres.
5. **El estilo, si hay duda** (`veredicto: "elegir_estilo"`): muestra al usuario los cuadros de `<TRABAJO>/estilos/<id>/`
   de cada candidato con la `razon`; reanuda con `resumeFromRunId` y `args.estilo`. Un solo estilo por video.
6. **El gancho** (`veredicto: "elegir_gancho"`): muéstrale las hojas de `<TRABAJO>/ganchos/<id>/` y la voz de cada uno
   (y la recomendación del crítico); reanuda con `args.gancho`. Si elige una familia marcada «NO REPETIR» (G3D2), díselo.
   `args.auto` deja la recomendación del crítico (solo si el usuario lo pide).
7. **El cierre** (`veredicto: "elegir_cierre"`, `cierres`): el usuario elige uno de los 5 o dicta el suyo; ponlo en la
   escena de cierre de `guion.json` y vuelve a correr `video3d.py guion <TRABAJO> --check` y `storyboard`. Con
   `veredicto: "corregir"`, decide con el usuario las `faltas_pendientes`; con `"no_es_3d"`, propón el flujo de la `nota`.
   Los avisos `NÚCLEO` del Workflow son cambios que el constructor no pudo hacer en `motor.js`: anótalos en «Mejoras al
   framework».
8. **Voz.** Sigue `referencias/fragmentos/voz-mcp.md` con `<script>` = `video3d.py` y el flow «Video 3D · <slug>».
   Luego `python3 scripts/video3d.py escuchar <TRABAJO>` (V11: whisper transcribe la voz sin el guion; una falta se
   arregla con una retoma de esa escena). Con `sin-voz`: `video3d.py voz-falsa <TRABAJO>` (sin escucha).
9. **Tiempos, render y montaje.** En un comando: `python3 scripts/video3d.py producir <TRABAJO>` (`tiempos` → `escuchar` →
   `render` → `montar`, reanudable; `referencias/fragmentos/producir.md`). Paso a paso: `video3d.py tiempos` → `render` → `montar` (9:16 y 4:5). `montar` deja también
   `salida/subtitulos.srt` y `salida/portada.png` (el cuadro cero sin subtítulos). Mira el resultado (una hoja de
   cuadros del mp4) y la portada antes de entregar.
10. **Entrega.** `video3d.py entregar <TRABAJO>` → `videos3d/<fecha>-<slug>/` (video, 4:5, portada, `caption.md`,
    `.srt`, `tiempos.json`, fuentes) y `python3 scripts/memoria.py --video3d <entrega>`; `make validate` sale 0; costo medido: `python3 scripts/costo.py
    --registrar --pieza <id> --flujo video3d --entrega <entrega>`. Sin
    el 4:5, sin portada o sin caption no entrega (`--sin-4x5` solo si el usuario pide entregar el 9:16 solo). Nunca
    con voz falsa.
11. **Reporte.** Qué se entregó y dónde, tiempos y créditos, y «Mejoras al framework» (o «ninguna»), registradas con
    `memoria.py --mejoras` (flujo `video3d`).

`make video3d-fixture` corre la maqueta de prueba de punta a punta sin créditos.
