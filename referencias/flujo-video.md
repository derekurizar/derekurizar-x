# Flujo `/video` — índice

Un video es **un hilo ya entregado contado en vertical** (1080×1920, 30 fps) para TikTok, Reels y Facebook,
escrito para retener: una escena de **gancho** a pantalla completa (la cifra enorme desde el primer cuadro,
legible en silencio), las tarjetas del hilo animadas mientras la voz las narra (con **zoom** al número cuando
se dice), **golpes** de texto cinético que re-ganchan o traducen una cifra a escala humana, subtítulos
sincronizados con la cifra resaltada, barra de progreso arriba, música con **ducking** bajo la voz y efectos
de sonido del catálogo fijo. No investiga ni verifica nada nuevo: solo usa las cifras de `datos.json` del
hilo (y derivados declarados con `calculo`). La publicación es manual; el entregable queda en
`hilos/<fecha>-<slug>/video/` (`video.mp4` fuera de git, `subtitulos.srt`, `caption.md`, `guion.json`,
`portada.png`, `contacto.png`) y se registra en `memoria/videos.json`.

```
preparar (video.py: hilo → TRABAJO, digesto con estructura y sugerencias, música por paleta)
→ Workflow video [guionista → guion.json v2 → gate V1–V5 + V9 (video.py guion --check)
                  → crítico de retención (C1–C10, puntajes, faltas) → el guionista corrige lo que bloquea
                    (o pule las mejoras si el crítico aprueba con algún puntaje justo de 3), ≤ 2 vueltas]
→ voz (MCP ElevenLabs: un nodo TTS por escena, 1 toma) → Scribe por escena (tiempos por palabra, 0 créditos)
→ tiempos (atempo 1.1, V6, eventos y efectos por escena, V10 ritmo) → grabar (Playwright cuadro a cuadro, V7)
→ montar (ducking + efectos + loudnorm en dos pasadas, V8) → revisar (hoja de contacto) → entregar
→ memoria.py --video → make validate
```

El **guion lo orquesta el Workflow `.claude/workflows/video.js`** (0 créditos: guionista + crítico). La voz y todo
lo que gasta créditos sigue en la **sesión principal** (`.claude/commands/video.md`), porque las llamadas al
MCP de ElevenLabs se hacen desde ahí. `TRABAJO` = `sesiones/<slug>/video/` (memoria de trabajo: audio, clips,
cuadros, `critica.json`).

## Formato fijo (decisiones del usuario)

- **Sin cara**: texto cinético (gancho y golpes) y las tarjetas del hilo animadas. Ni presentador ni avatar.
- Voz **El Faraon 4** (`8mBRP99B2Ng2QwsJMFQl`), `eleven_multilingual_v2`, `language_code: es`, a **1.1×**
  (atempo, sin cambiar el tono). Las cifras se dicen en palabras (`scripts/numeros_es.py`).
- **Estructura de retención** (la comprueba V9): escena 1 = gancho con fórmula (`cifra`, `contradiccion`,
  `pregunta`, `resultado`) cuya pantalla funciona en silencio; **promesa** literal en la escena 1–2 que se
  **paga** en el último tercio; cada escena desde la 3 empieza con «pero» o «por eso» (y «y» como máximo en un
  tercio); un **golpe** ≤ 6 palabras arriba de cada tarjeta; escenas `golpe` para traducir a escala humana
  («1 de cada 3», con `calculo` verificado), pagar o re-ganchar; ≤ 6 s entre eventos.
- **Barra de progreso** arriba en todas las escenas, un tramo por escena (cierre incluido).
- **«En Guatemala»** (sin dos puntos) al inicio de la voz del gancho cuando no dice «Guatemala» (automático): la
  voz sigue la frase, «En Guatemala nacen casi 168 bebés al día…».
- **La voz es una oración, la pantalla puede ser titular.** En el gancho y en cada golpe, la oración de la voz que
  dice la pantalla lleva un verbo conjugado, declarado en `verbo` (V9): «Casi 168 al día» en pantalla → «Nacen casi
  168 bebés al día de madres de 10 a 19 años» en la voz. «Casi 168 bebés al día, de madres de 10 a 19 años» (el
  titular leído en voz alta) no se entiende (usuario, 2026-10-20).
- **Cierre**: resumen + pregunta al espectador (voz y pantalla) y luego «Sígueme en» con TikTok
  @derekurizargt, Instagram @derekurizargt y X @DerekUrizar **solo en pantalla**. Sin logo, sin fuentes, sin la
  marca en la voz.
- **Música** solo del catálogo fijo `design/musica/catalogo.json` (2 pistas por paleta; se elige la de la paleta
  del hilo usada hace más tiempo), con **ducking** bajo la voz (sidechain). **Efectos** solo del catálogo fijo
  `design/sfx/catalogo.json` (8 WAV: whoosh, tic, pulso, impacto, grave, riser, resolucion, foco), disparados
  por los eventos de cada escena. **`/video` nunca genera música ni efectos.**
- Colores de la paleta del hilo (`design/tokens.json`).
- **Zona segura de TikTok** (medida en un iPhone con la app): el video se escala para llenar el alto y pierde
  ~57 px por lado; la barra de pestañas tapa hasta y≈215, los íconos de la derecha x ≥ 900 desde y≈1070 y el
  nombre y el texto empiezan en y≈1645. Golpe y barra desde y=250 en la columna x 85–876; subtítulos en y=1400
  (1500 en el cierre).
- **Layout vertical de la tarjeta** (`video/vertical.css`, decisión del usuario tras el primer video: «en redes el
  layout es distinto»): la tarjeta no se incrusta al 86 %; se inyecta una hoja que oculta el titular y el handle,
  deja kicker → gráfico a todo el ancho (escala 1, y≈420–1220: por encima de la franja de íconos todo el ancho es
  seguro) → nota → «Fuente» pequeña. El **foco** hace zoom de 1.25–1.45 a la cifra mientras la voz la dice (el resto
  se sale de cuadro), con **deriva** lenta cuando no hay foco; el golpe entra desde la izquierda. V7 compara el
  render vertical contra el animado vertical (`video_animar.js` inyecta la misma hoja; `--cuadrada` para el modo
  viejo). Entre escenas, **transición de deslizamiento** de 0.3 s (`xfade` en `montar`, vertical en el giro).

## Duraciones

| Duración | Objetivo | Escenas (más el cierre) | Voz | Costo de voz |
|---|---|---|---|---|
| `corto` | 60 s ±10 % | gancho + 3–4 tarjetas + 1–2 golpes | ≈ 810 caracteres | ≈ 850 créditos |
| `medio` (por defecto) | 120 s ±10 % | gancho + 6–8 tarjetas + 2–4 golpes | ≈ 1,675 | ≈ 1,700 |
| `largo` | 240 s ±10 % | gancho + 11–15 tarjetas + 3–6 golpes | ≈ 3,437 | ≈ 3,450 |
| `prueba` (solo fixture) | 45 s ±10 % | gancho + 2–3 tarjetas + 0–1 golpes | ≈ 599 | 0 (voz falsa) |

Medido: 15.5 caracteres de voz por segundo a 1.1×, más 0.7 s por escena y 2.8 s de cierre; presupuesto =
`(s − 0.7·(1 + máx tarjetas + máx golpes) − 2.8)·15.5`. Por escena: gancho 30–130 caracteres, tarjeta 40–230,
golpe 20–110, cierre 40–200. Scribe, música y efectos: 0 créditos. Los estudios de video de datos en TikTok
dan una media de 84 s y recomiendan ≤ 90 s, pero el usuario prefiere `medio` por defecto (2026-10-20): en un minuto «algo muy informativo se siente como un resumen y corriendo»; `corto` se pide a propósito.

## Gates (`scripts/video.py` y `video.js`)

| Gate | Dónde | Qué exige |
|---|---|---|
| V1 escenas | `guion --check` | tipos `gancho|tarjeta|golpe`; tarjetas y golpes en el rango de la duración; cada `tuit` con tarjeta y sin repetir; contexto ≤ 40; cierre con texto, 2 líneas de resumen y pregunta; el `gancho` de texto suelto del formato viejo se rechaza |
| V2 cifras | `guion --check` | cada número de la voz, la pantalla, la línea, el golpe, el resumen y los captions tiene respaldo en `datos.json` (`verificacion.sueltos`, como G10) o en el `valor_calculo` de su escena |
| V3 voz | `guion --check` | sin dígitos en la voz; ida y vuelta de cada conversión; ninguna cifra de género ambiguo sin `{n:f}`/`{n:m}` |
| V4 presupuesto | `guion --check` | caracteres de voz por tipo (gancho 30–130, tarjeta 40–230, golpe 20–110, cierre 40–200); duración estimada en ±10 % del objetivo |
| V5 reglas | `guion --check` | cierre termina en la pregunta; el cierre no menciona fuentes, el hilo, la marca ni «sígueme»; sin «en suma», enlaces ni @handles en voz, golpes, pantallas ni líneas; captions presentes |
| **V9 estructura** | `guion --check` | escena 1 = gancho único con `formula` válida, `pantalla` (cifra o ≤ 4 palabras, ≤ 24) y `linea` (≤ 8 palabras, ≤ 60) que pasan la prueba en silencio **y cuyas palabras clave la voz dice** (en un golpe, solo aviso: vale un sinónimo); en gancho y golpes, la oración de la voz que dice la cifra de la pantalla (o la primera) contiene el `verbo` declarado; escena 2 = T1 sin enlace; cada tarjeta con `golpe` (1–6 palabras, ≤ 40, ≠ titular); `enlace ∈ pero|por_eso|y` desde la escena 3 con su conector al inicio de la voz y «y» ≤ ⌊n/3⌋; golpes con pantalla y línea, nunca dos seguidos ni en la escena 2; `promesa.texto` (10–80) literal en la escena `en` ∈ {1, 2} y `pago` en el último tercio; `calculo` legible (ids de cifra, literales de `datos.json`, constantes) cuyo resultado aparece escrito en la escena; **ritmo estimado** ≤ 6 s entre inicio, fin de la primera oración, cada cifra y fin |
| Workflow | `video.js` | retorno del guionista coherente (gate ok, tipos, gancho primero, T1 segunda, promesa/pago en rango, pregunta con «?»); retorno del crítico coherente (bloqueantes, veredicto, cada puntaje ≤ 2 con falta `bloquea` de su regla); ≤ 3 vueltas (corrección de lo que bloquea, o pulido mientras el crítico deje mejoras); si sigue en `corregir`, el comando pregunta al usuario antes de gastar créditos |
| V6 alineación | `tiempos` | las palabras de Scribe coinciden con la locución (si no, rehacer la voz de esa escena); duración real fuera de ±15 % = aviso |
| **V10 ritmo** | `tiempos` | con tiempos reales, hueco máximo entre eventos visuales (golpe, entrada, cifra, foco, nota, fin de línea, fin) ≤ 6 s; **aviso**, no falla. `tiempos` también fija la transición de entrada de cada escena (`slideleft`; `slideup` en el giro) y desplaza golpe y cifra 0.3 s para que no queden bajo el `xfade` |
| V7 animación | `grabar` | el último cuadro de cada tarjeta animada es idéntico a su render estático (`scripts/video_animar.js --check`, ≤ 0.1 % de píxeles); el foco vive fuera del iframe y `__caja` no lanza |
| V8 salida | `montar` | 1080×1920 con audio; −14 ±1.5 LUFS; true peak ≤ −1 dBTP (música 0.22 con ducking; efectos del catálogo; loudnorm en dos pasadas) |
| K2 efectos | `validate.py` / `sfx.py --check` | `design/sfx/catalogo.json` con los 8 ids fijos, cada WAV presente, duración 0.2–4 s coherente con la cabecera, ganancia −40–0 dB |

Crítico (`referencias/roles/video-critico.md`, C1–C10): gancho en silencio · razón para quedarse · «¿por qué seguiría
viendo?» por escena · pero/por eso reales · escala humana · pago · ritmo y re-gancho · cierre · lenguaje y honestidad.
Puntajes 1–5: gancho, bucle, ritmo, escala_humana, pago, cierre. `pasa` = sin faltas `bloquea` y todos ≥ 3.

## Piezas

- `scripts/video.py` (subcomandos, `--help`) · `scripts/numeros_es.py` (`--prueba`) · `scripts/video_grabar.js`
  · `scripts/video_animar.js` (V7) · `scripts/sfx.py` (`--importar`, `--check` = K2).
- `video/golpe.html` (gancho y golpes: cifra que cuenta + línea palabra a palabra) · `video/escena.html` (tarjeta con
  golpe arriba, foco y subtítulos con `.cifra`) · `video/cierre.html` · `video/animar.js` (animadores por plantilla:
  antes-despues, cifra, barras-v, linea, barras-h, waffle, dona, pesas, mapa, pendiente; el resto aparece con wipe;
  `__caja(clave)` para el foco).
- `design/musica/` y `design/sfx/` (bibliotecas fijas) · `.claude/workflows/video.js` · `.claude/agents/video-guionista.md`
  + `referencias/roles/video-guionista.md` · `.claude/agents/video-critico.md` + `referencias/roles/video-critico.md`.
- Prueba sin créditos: `make video-fixture` (hilo `sesiones/_fixture/salida`, duración `prueba` de 45 s, voz falsa
  tonal para probar el ducking). Los espejos de `video.js` los vigila `scripts/check_workflows.py` (W10).

## Biblioteca de efectos (una sola vez)

`creative_create_flow` «Biblioteca de efectos» → un nodo `sfx` (`eleven_text_to_sound_v2`) por efecto con su
`duration_seconds` y `prompt_influence` → `creative_run_flow_nodes` con `generations_count: 2` →
`creative_get_flow_run_status` → `urls.json {id: content_url}` → `python3 scripts/sfx.py --importar urls.json`
(descarga, recorta el silencio, normaliza al pico −3 dBFS, WAV mono 48 kHz, escribe `catalogo.json`). Para
cambiar una variación se reimporta solo esa url. Nunca se vuelve a generar desde `/video`.

## Revisión antes de entregar

`revisar` deja dos hojas: `contacto.png` (por escena: cifra completa · pico del foco · final) y `linea_tiempo.png`
(el video final, un cuadro cada 2 s, transiciones incluidas). La segunda es la que hay que mirar «de corrido»:
en la primera entrega real los cuadros fijos escondieron una pantalla vacía tras una transición y un golpe cuyas
palabras se montaban al entrar. Lo que el coordinador no puede hacer es escuchar: por eso el gate exige que la
voz del gancho diga lo que la pantalla muestra y el crítico lee la locución completa seguida (C10).

## Pendiente de cada corrida real

Scribe devuelve el texto del guion alineado al audio, no una escucha independiente: **el usuario escucha las
cifras** antes de publicar. Si una cifra suena mal, se rehace solo el nodo de esa escena. Tras la primera
corrida real, comparar en TikTok con el video anterior (retención a 3 s y tiempo medio) y recalibrar
`RITMO_MAX_S` y los umbrales del crítico con ese dato.
