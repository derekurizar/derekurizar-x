---
description: Un video vertical 100 % en 3D, la «maqueta que vuela» (9:16 + 4:5, 45–75 s) — un mundo simple (relieve, ciudad, plaza) recorrido por una cámara mientras la voz cuenta, con titular, pines que siguen al 3D, cifras y subtítulos; un solo estilo por video elegido entre ocho (three.js o Blender sobre HyperFrames); el gancho es un evento 3D en el segundo cero y cada toma muestra lo que la voz dice (uso — /video-3d <tema|desde:<pieza>> [sin-voz]; voz de ElevenLabs ≈ 700 créditos en 45 s; sin-voz arma el video con voz falsa, 0 créditos y sin entrega)
---

# /video-3d $ARGUMENTS

Guía completa: `referencias/flujo-video3d.md` (léela antes de empezar). Contrato del motor:
`referencias/diseno/maqueta3d.md`. El guion lo escribe la sesión con el digesto (como /sabias y /congreso).

1. **Preflight.** `make doctor`. Decide si el tema es de 3D: tiene que pasar en un lugar (el lugar es la
   información). Si no, propón el flujo que sí le toca y no sigas.
2. **Preparar.** `python3 scripts/video3d.py preparar <slug> --tema "<tema>" --musica-tema <tema de MUSICA_TEMAS>
   [--desde <trabajo o entrega ya investigada>] [--duracion 45]`. Con `desde:` se reutilizan las cifras verificadas.
3. **Investigación.** Lo que falte se investiga y verifica con los agentes de /historia (`historia-investigador` ⇢
   `historia-verificador`, cita literal guardada con `historia.py leer`). **Los geodatos también se verifican**: qué
   tramo, de dónde a dónde, hacia dónde. Suma lo verificado con `video3d.py datos <TRABAJO> --sumar <archivo>` y
   anota en el guion lo que NO se puede dibujar (`no_afirmar`).
4. **Dirección.** Con `video3d.py digesto <TRABAJO>`: escribe la `idea_visual` (una oración), elige el `estilo`
   entre los ocho con su `razon` y arma el `mundo` (set, piezas, lugares). Si no estás seguro del estilo
   (`confianza: "baja"`), renderiza el mismo cuadro en los dos o tres candidatos (`maqueta3d.py cuadro`) y
   **pregunta al usuario**. Un solo estilo por video.
5. **Ganchos.** Escribe `ganchos.json` con 5 candidatos de familias distintas (cada uno, la escena 1 completa:
   evento en el segundo cero, cámara, titular y voz ≤ 6 s). `video3d.py ganchos <TRABAJO> --check --cuadros`
   renderiza un cuadro por candidato. **El usuario elige** (muéstrale los cuadros y la voz de cada uno) →
   `ganchos --usar <id>`.
6. **Guion.** Primero la narración de corrido; luego las escenas con sus anclas `dice`. `video3d.py guion
   <TRABAJO> --check` hasta 0 fallas (C3D1–C3D10, V2–V4 y M3D en 9:16 y 4:5).
7. **Storyboard y crítica.** `video3d.py storyboard <TRABAJO>` → mira la hoja. Lanza `video-critico` con la sección
   «Crítico en Modo 3D» de la guía, `guion.json`, `locucion.json` y la hoja; aplica las faltas que bloquean (≤ 2
   vueltas). Propón 5 cierres y **el usuario elige el cierre**.
8. **Voz.** `video3d.py voz <TRABAJO>` → nodos para el MCP de ElevenLabs (como /video) → `video3d.py descargar
   <TRABAJO> --estado <archivo>`. Con `sin-voz`: `video3d.py voz-falsa <TRABAJO>`.
9. **Tiempos, render y montaje.** `video3d.py tiempos` → `render` → `montar` (9:16 y 4:5). Mira el resultado (una
   hoja de cuadros del mp4) antes de entregar.
10. **Entrega.** `video3d.py entregar <TRABAJO>` → `videos3d/<fecha>-<slug>/`. Nunca con voz falsa.
11. **Reporte.** Qué se entregó y dónde, tiempos y créditos, y «Mejoras al framework» (o «ninguna»).
