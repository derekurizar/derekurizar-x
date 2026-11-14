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
4. Avisa el tiempo (≈ 30–50 min de agentes, ≈ 15–25 min de tableros y render) y los créditos. Solo se graban las
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

## 4. ARMAR, PLANO, PROYECTO Y RENDER (el 16:9 es una «mesa de archivo» en HyperFrames)
Qué es dinamismo (decisión del usuario, 2026-11-13): que **entre en pantalla lo que la voz nombra**. Con cada oración cae
una pieza sobre la mesa: una foto, un recorte de prensa, la página de un documento, la ficha de una persona, un lugar en
el mapa, una fecha, una cifra con su rótulo. La cámara no se mueve nunca para aparentar ritmo.

1. `python3 scripts/youtube.py armar <TRABAJO>`: las escenas unidas, el audio recortado por palabra, los recursos de cada
   parte y `plano.borrador.json` (lo que las escenas ya traen).
2. **Plano** (0 créditos, ≈ 15–30 min): `Workflow({name: "youtube", args: {trabajo, desde: "plano", capitulos: N}})`
   (N = capítulos de `capitulos.json`).
   - Un `youtube-realizador` por capítulo escribe `plano_<N>.json` y baja los recursos que falten; un cierre deja
     `python3 scripts/youtube.py plano <TRABAJO> --check` en 0 fallas (YT13–YT19). Guía: `referencias/roles/youtube-realizador.md`.
   - Con `plano_pendiente`, muestra las fallas y pregunta.
3. `python3 scripts/youtube.py plano <TRABAJO> --check --hoja` escribe `plano.md` («la voz dice | entra en pantalla»).
   Léela entera antes de renderizar: el gate cuenta piezas, no juzga si la pieza es la correcta. Busca fotos de personas
   en un proceso sobre oraciones que no las nombran, piezas que adelantan lo que el video cuenta después y rótulos de relleno.
4. `python3 scripts/youtube.py grabar <TRABAJO>` (en segundo plano): solo los tableros, las escenas `explica` y `tarjeta`
   con su animación ya hecha, grabadas limpias con el motor propio → `clips_tablero/`.
5. `python3 scripts/youtube.py proyecto <TRABAJO>`: un proyecto de HyperFrames por capítulo en `hf/cap-N/`.
6. `python3 scripts/youtube.py revisar <TRABAJO>`: `hyperframes check` y una hoja de contacto por capítulo
   (`revision/hf_cap-N*.jpg`, cada mesa con todas sus piezas). **Mira todas las hojas.** Si una pieza tapa a otra o
   queda cortada, corrígela en `plano_<N>.json` con `x`, `y` o `w` y repite 5–6. No pases de aquí con una hoja fea.
7. `python3 scripts/youtube.py audio <TRABAJO>`: la voz, la música por capítulo y un efecto por pieza, a −14 LUFS; el
   `.srt` y los capítulos. Deja en cada proyecto el audio de su capítulo.
8. Vista previa para el usuario si la pide: `cd <TRABAJO>/hf/cap-N && npx hyperframes preview --background`.
9. `python3 scripts/youtube.py render <TRABAJO>` (en segundo plano; ≈ 1.6× la duración del video): cada capítulo con
   **un solo proceso** (`--workers 1`; con varios el video tiembla), uno tras otro → `segs_16x9/video_solo.mp4`.
10. `python3 scripts/youtube.py montar <TRABAJO>` → `salida/video.mp4` (YT9). Mira el video entero antes de enseñarlo.

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
- En el 16:9 no hay subtítulos quemados (van en el `.srt`) ni cámara que se mueva: el ritmo lo dan las piezas que entran
  cuando la voz las nombra. No se entrega un largo con YT13–YT19 en falla.
- Antes de rehacer un video entero con un estilo nuevo, un piloto de 60–90 s que el usuario apruebe.
