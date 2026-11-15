---
description: Un video vertical 100 % en 3D, la «maqueta que vuela» (9:16 + 4:5, 45–75 s), para temas donde el lugar es la información: una cámara recorre un mundo simple mientras la voz cuenta (uso — /video-3d &lt;tema|desde:&lt;pieza&gt;&gt; [sin-voz])
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
   `ganchos --usar <id>`. La familia de los últimos 2 videos 3D no se repite: el digesto la marca «NO REPETIR» y
   `ganchos` avisa (G3D2); si el usuario la elige igual, díselo.
6. **Guion.** Primero la narración de corrido; luego las escenas con sus anclas `dice` y el **`caption`** (obligatorio:
   `tiktok`, `instagram`, `facebook` y `shorts` con su título de ≤ 100 caracteres y `#Shorts`; cifras en dígitos).
   `video3d.py guion <TRABAJO> --check` hasta 0 fallas (C3D1–C3D11, V2–V5 y M3D en 9:16 y 4:5). El aviso «Maqueta · no
   a escala» es opcional: ponlo (`aviso`) solo si el dibujo simplifica algo que se podría tomar al pie de la letra.
7. **Storyboard y crítica.** `video3d.py storyboard <TRABAJO>` → mira la hoja. Lanza `video-critico` en «Modo 3D»
   (`referencias/roles/video-critico.md` + `video-critico/3d.md`) con `guion.json`, `locucion.json` y la hoja; aplica las faltas que bloquean
   (≤ 2 vueltas). Propón 5 cierres y **el usuario elige el cierre**.
8. **Voz.** Sigue `referencias/fragmentos/voz-mcp.md` con `<script>` = `video3d.py` y el flow «Video 3D · <slug>».
   Luego `python3 scripts/video3d.py escuchar <TRABAJO>` (V11: whisper transcribe la voz sin el guion; una falta se
   arregla con una retoma de esa escena). Con `sin-voz`: `video3d.py voz-falsa <TRABAJO>` (sin escucha).
9. **Tiempos, render y montaje.** `video3d.py tiempos` → `render` → `montar` (9:16 y 4:5). `montar` deja también
   `salida/subtitulos.srt` y `salida/portada.png` (el cuadro cero sin subtítulos). Mira el resultado (una hoja de
   cuadros del mp4) y la portada antes de entregar.
10. **Entrega.** `video3d.py entregar <TRABAJO>` → `videos3d/<fecha>-<slug>/` (video, 4:5, portada, `caption.md`,
    `.srt`, `tiempos.json`, fuentes) y `python3 scripts/memoria.py --video3d <entrega>`; `make validate` sale 0. Sin
    el 4:5, sin portada o sin caption no entrega (`--sin-4x5` solo si el usuario pide entregar el 9:16 solo). Nunca
    con voz falsa.
11. **Reporte.** Qué se entregó y dónde, tiempos y créditos, y «Mejoras al framework» (o «ninguna»), registradas con
    `memoria.py --mejoras` (flujo `video3d`).

`make video3d-fixture` corre la maqueta de prueba de punta a punta sin créditos.
