# La voz con el MCP de ElevenLabs

El paso de voz de todos los flujos de video (`/video`, `/historia`, `/serie`, `/explica`, `/sabias`, `/congreso`,
`/youtube-long`, `/video-3d`). Cada comando lo cita y dice solo lo suyo: el nombre del flow y su script
(`<script>` = `video.py`, `historia.py`, `explica.py`, `sabias.py`, `congreso.py` o `video3d.py`; todos reenvían
`voz`, `voz-falsa`, `descargar` y `partir` a `video.py`). Con `sin-voz`: `python3 scripts/<script> voz-falsa
<TRABAJO>` (0 créditos) y se salta este paso.

## Antes de gastar

- Carga con **una sola** llamada a ToolSearch: `creative_create_flow`, `creative_add_flow_node`,
  `creative_run_flow_nodes`, `creative_get_flow_run_status` y `creative_transcribe_audio`.
- Di al usuario los caracteres de voz (`locucion.json → caracteres`; ≈ 1 crédito por carácter).
- `python3 scripts/<script> voz <TRABAJO>` imprime la voz (`voice_id`) y un `prompt` por **nodo**: una secuencia de
  2–5 escenas grabada de corrido (`locucion.json → secuencias`) o una escena suelta (el gancho, el cierre, las que
  no caben en ninguna). En una retoma: `voz --pendientes` (las secuencias enteras que hay que regrabar, con sus
  créditos) o `voz --sueltas` (solo las escenas cambiadas, como nodos propios).

## Generar

1. `creative_create_flow` con el nombre que dice el comando.
2. Un `creative_add_flow_node` por nodo: `node_type: "tts"`, `model_id: "eleven_multilingual_v2"`, el `voice_id` de la
   salida, `model_parameters: {"language_code": "es"}` y el `prompt` **exacto** (las cifras ya van en palabras).
3. `creative_run_flow_nodes` con **`generations_count: 1`**: la locución es determinista y el usuario ya eligió la
   voz. **Nunca** se relanza un nodo para reintentar: cobra otra generación.
4. **Lotes de ≤ 3 nodos**: ElevenLabs corre pocas generaciones a la vez y las demás quedan pendientes. Corre un lote,
   sondea `creative_get_flow_run_status` **solo con los `session_ids` pendientes** hasta `all_completed` y sigue con
   el siguiente. Para esperar, un `sleep` en segundo plano.
5. Con la voz completa, `creative_transcribe_audio` por nodo (`eleven_scribe_v1`, `connect_from: [nodo]`; 0 créditos).

## Descargar

Lo normal, y lo más corto: escribe `<TRABAJO>/audio/nodos.json` con las dos URL de cada nodo

```json
{"s1": {"voz": "<content_url>", "palabras": "<words_download_url>", "creditos": 177}, "7": {"voz": "…", "palabras": "…", "creditos": 92}}
```

(la clave es el id del nodo que imprimió `voz`: `s1` una secuencia, `7` la escena 7) y corre

```
python3 scripts/<script> descargar <TRABAJO> --nodos <TRABAJO>/audio/nodos.json
```

El resto del estado sale de `locucion.json`. `descargar` baja cada nodo, **corta** cada secuencia en sus escenas con
los tiempos de Scribe (`audio/secuencias.json`), escribe `palabras_N.json` y suma `audio/creditos.json`. Exit 1 lista
lo que falta.

La otra vía, con el estado entero del MCP: **una sola** `creative_get_flow_run_status` con las sesiones de voz y de
Scribe (≤ 20 ids por llamada; con más, en lotes, la voz de cada nodo con su Scribe en el mismo lote) y
`descargar <TRABAJO> --estado A [B …]`. Si la respuesta es grande, la herramienta la guarda en un archivo: ese es el
que se pasa. Si llega en el chat, vale pegada como venga en `<TRABAJO>/audio/estado.json` (con texto alrededor,
varias respuestas seguidas, o por stdin con `--estado -`); se usan `generations[]`, `media[]` y `transcripts[]`.
`descargar` falla si una transcripción no casa con ninguna escena.

## Retomas

- Una escena que no se alinea en `tiempos` (V6) o falla la escucha (V11): se regraba **solo ese nodo** (1 toma), se
  transcribe y se pasa por `descargar` (actualiza esa escena y suma sus créditos); luego `tiempos` otra vez.
- Si falla la frontera de una secuencia: se regraba entera, o esas escenas con `voz --sueltas`.
- Una segunda falla de V11 en la misma escena no se insiste: va al reporte y el usuario la oye.
