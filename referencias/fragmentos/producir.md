# `producir`: de la voz al video, en un comando

Vale para todos los flujos de video. Con la voz ya descargada (`referencias/fragmentos/voz-mcp.md`):

```
python3 scripts/<script> producir <TRABAJO>
```

(`<script>` = `video.py`, `historia.py`, `explica.py`, `sabias.py`, `congreso.py`, `video3d.py` o `youtube.py`; todos
lo reenvían a `scripts/producir.py`.) Corre la cadena del TRABAJO, se detiene en la primera falla diciendo en qué paso
y, al repetirlo, **reanuda ahí**: no rehace lo que ya terminó con esta voz, este guion y este plano.

| TRABAJO | Cadena |
|---|---|
| mesa de archivo (`"realizacion": "mesa"`) | `tiempos` → `escuchar` → `plano --check --hoja` → `grabar` → `montar` → `revisar` → lo mismo en 4:5 |
| motor propio (trabajos viejos) | lo mismo sin `plano` |
| `/video-3d` | `tiempos` → `escuchar` → `render` → `montar` |
| `/youtube-long` | `armar` → `plano --check --hoja` → `grabar` → `proyecto` → `revisar`; y con `--render`: `audio` → `render` → `montar` |

## El ciclo

1. `producir <TRABAJO>`.
2. **Código 3 = pausa por el plano**: el trabajo va en mesa y todavía no tiene `plano.json`. Lanza el Workflow que el
   mensaje indica (`plano` con `{trabajo}`; en el largo, `youtube` con `desde: "plano"`), muestra al usuario
   `<TRABAJO>/plano.md` y lo que dijo el juez del plano, y repite `producir`: sigue en `plano --check`.
3. **Código 1 = un paso falló**: lee su salida (la `FALLA` del gate dice qué arreglar: una retoma de voz, el plano, el
   guion con un retoque), arréglalo y repite `producir`. Lo que falle en pantalla se arregla en el plano, nunca en el
   guion ni en la voz.
4. **Código 0**: están el 9:16 y el 4:5 en `<TRABAJO>/salida`. Lee **una vez** la hoja de contacto de `revisar` y
   sigue con `entregar`. En el largo, tras el primer `producir` mira las hojas y corre `producir --render`.

## Banderas

- `--pasos`: lista la cadena de ese TRABAJO y sale.
- `--hasta PASO` / `--desde PASO`: acotan (`--hasta plano` para parar antes de grabar).
- `--todo`: rehace todo aunque conste hecho.
- `--sin-escucha`: salta `escuchar` (V11).
- `--borrador`: maquetas y `sin-voz`: usa el borrador del plano y no se detiene a esperar al realizador.
- `--solo N`: pasa `--solo N` a `grabar` (motor propio).

El estado queda en `<TRABAJO>/producir.json` (por paso: si terminó bien y la huella de la voz, el guion y el plano que
usó). Si cambia la voz o el guion, rehace desde `tiempos`; si cambia el plano, desde `plano`.

Los pasos sueltos (`tiempos`, `grabar`, `montar`, `revisar`…) siguen existiendo: sirven para diagnosticar el paso que
falló o para rehacer solo uno.
