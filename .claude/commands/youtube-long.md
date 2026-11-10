---
description: Una serie ya entregada convertida en UN video largo 16:9 para YouTube — el montaje quita lo que se repite al pegar las partes (ganchos y cierres de cada parte, hechos contados otra vez, personas y siglas presentadas otra vez), une los capítulos con 1–2 oraciones que cuentan la historia sin anunciar lo que viene, reutiliza la voz grabada (solo se graban las uniones y la promesa), regraba las escenas en 16:9 y entrega video, miniatura, capítulos, subtítulos y fuentes (uso — /youtube-long <serie|ultima> [sin-voz|fixture])
---

Argumentos: `$ARGUMENTS`
- La serie: su carpeta (`series/<fecha>-<slug>`), su slug o `ultima` (la serie completa más reciente de
  `memoria/series.json`).
- `sin-voz`: las uniones con voz falsa, 0 créditos, sin entrega ni memoria.
- `fixture`: `make youtube-fixture` (la maqueta, sin web ni créditos) y para.

Nunca publiques. Lee `referencias/flujo-youtube.md` antes de empezar.

## 1. PREFLIGHT
1. `make doctor`.
2. `python3 scripts/youtube.py preparar <serie>`: exige la serie completa y entregada, con la voz final de cada escena.
   Escribe el índice, el informe de repeticiones y el borrador del montaje, e imprime el TRABAJO en la última línea.
3. Muestra al usuario el informe en 4–6 líneas: minutos tal cual, hechos repetidos, personas presentadas de nuevo y
   siglas explicadas de nuevo.
4. Avisa el tiempo (≈ 15–25 min de agentes, ≈ 60–120 min de grabación 16:9) y los créditos. Solo se graban las
   uniones y la promesa: ≈ 600–1,000 créditos.

## 2. MONTAJE (Workflow `youtube`, 0 créditos)
1. `Workflow({name: "youtube", args: {trabajo}})`. Si el agente no está registrado, usa `scriptPath`.
2. Si devuelve `aprobar_montaje` (las mejoras ya probadas por el crítico vienen aplicadas en `mejoras_aplicadas`; no
   las apliques otra vez), muestra `python3 scripts/youtube.py resumen <TRABAJO>`: duración, capítulos con su
   minuto, cada unión y la promesa (texto literal), las escenas reescritas, los cortes y la voz nueva en caracteres.
3. Pregunta con AskUserQuestion: aprobar, o pedir cambios. Con cambios, relanza con
   `args: {trabajo, desde: "retoque", notas}`.
4. Si devuelve `corregir`, muestra `faltas_pendientes` y pregunta qué hacer. No sigas sin el usuario.

## 3. VOZ (solo las piezas nuevas)
1. `python3 scripts/youtube.py voz <TRABAJO>` arma `<TRABAJO>/nuevas/` e imprime los nodos. Con `sin-voz`, pasa
   `--falsa` y salta al paso 4.
2. Con el MCP de ElevenLabs, igual que en `/historia` (`.claude/commands/historia.md`, paso de voz): un flow y un nodo
   TTS por pieza (voz, modelo y `language_code` del JSON). **Por lotes** (`lotes` del JSON, ≤ 3 nodos; m112):
   `creative_run_flow_nodes` con un lote, sondea sus sesiones con `creative_get_flow_run_status` hasta `all_completed`
   (para esperar, un `sleep` en segundo plano) y sigue con el siguiente. Luego Scribe por nodo y un
   `creative_get_flow_run_status` final con todas las sesiones.
3. `python3 scripts/video.py descargar <TRABAJO>/nuevas --estado <archivo>`. Si el estado llega en el chat, pégalo tal
   cual en un archivo (con lo que traiga alrededor, o varias respuestas seguidas) o por stdin con `--estado -` (m111):
   `descargar` saca de ahí `generations`, `media` y `transcripts`.
4. `python3 scripts/youtube.py tiempos <TRABAJO>` y `python3 scripts/video.py escuchar <TRABAJO>/nuevas` (V11).

## 4. ARMAR, GRABAR Y MONTAR (en segundo plano)
1. `python3 scripts/youtube.py armar <TRABAJO>`: escenas unidas, audio recortado por palabra, recursos de cada parte y
   rótulos de capítulo.
2. `python3 scripts/youtube.py grabar <TRABAJO>` en segundo plano (16:9, YT9 márgenes).
3. `python3 scripts/youtube.py montar <TRABAJO>`: el video por tramos, la música alternada por capítulo, ducking,
   efectos y −14 LUFS.
4. Revisa la hoja de contacto y oye cada escena recortada: el corte no debe notarse. Si algo suena mal, corrige el
   montaje (retoque) y vuelve a armar.

## 5. MINIATURA, TÍTULO Y ENTREGA
1. Propón 3 miniaturas: `python3 scripts/youtube.py miniatura <TRABAJO> --texto "…" --foto <id> [--cifra "…"]
   [--chip "…"] --nombre a|b|c`. Lleva ≤ 5 palabras y la foto del protagonista. Muéstralas y el usuario elige; la
   elegida se rehace sin `--nombre`.
2. Con `sin-voz`, termina aquí: reporta y no entregues.
   - El teaser vertical para llevar de los cortos al largo: `python3 scripts/youtube.py teaser <TRABAJO>` (→ `salida/teaser.mp4` y
     `teaser.md`; 0 créditos). Si la serie tiene un momento alto, proponle al usuario un `adelanto` en el montaje.
3. `python3 scripts/youtube.py entregar <TRABAJO>` → `series/<fecha>-<slug>/youtube/` con `video.mp4`, `miniatura.png`,
   `caption.md` (título, descripción con capítulos), `subtitulos.srt`, `fuentes.md`, `montaje.json`, `capitulos.json` y
   `contacto.png`.
4. `python3 scripts/memoria.py --youtube series/<fecha>-<slug>/youtube`, luego `make validate` y `make costo`.

## 6. REPORTE
- Duración, capítulos con su minuto, cuánto se cortó (de cuántos min a cuántos), las uniones y la promesa, los
  créditos gastados y las rutas.
- Cómo subirlo (de `caption.md`): video normal, miniatura, subtítulos en español, fuentes en el primer comentario y la
  pantalla final con un video de la serie a la derecha.
- Termina con «Mejoras al framework» (o «ninguna»), registradas con `memoria.py --mejoras` con `flujo: youtube`.

## Reglas
- Ninguna palabra nueva sin respaldo: los puentes llevan hechos `confirmado | una_fuente` y sus números pasan V2.
- No se reordena una parte y no se recorta una cita.
- El usuario aprueba el montaje y elige la miniatura antes de gastar créditos o entregar.
