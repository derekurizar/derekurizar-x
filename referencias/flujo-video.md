# Flujo `/video` — índice

Un video es **un hilo ya entregado contado en vertical** (1080×1920, 30 fps) para TikTok, Reels y Facebook,
escrito para retener: una escena de **gancho** a pantalla completa elegida entre 4–5 candidatos de familias
distintas (la cifra con su referente o un visual que se entiende sin sonido desde el primer cuadro; catálogo, reglas
R1–R12 y evidencia en `referencias/ganchos.md`), las tarjetas del hilo animadas mientras la voz las narra (con **zoom** al número cuando
se dice), **golpes** de texto cinético que re-ganchan o traducen una cifra a escala humana, subtítulos
sincronizados con la cifra resaltada, barra de progreso arriba, música con **ducking** bajo la voz y efectos
de sonido del catálogo fijo. No investiga ni verifica nada nuevo: solo usa las cifras de `datos.json` del
hilo (y derivados declarados con `calculo`). La publicación es manual; el entregable queda en
`hilos/<fecha>-<slug>/video/` (`video.mp4` fuera de git, `subtitulos.srt`, `caption.md`, `guion.json`,
`portada.png`, `contacto.png`) y se registra en `memoria/videos.json`.

```
preparar (video.py: hilo → TRABAJO, digesto con estructura y sugerencias, música por paleta)
→ Workflow video [video-gancho → ganchos.json (4–5 candidatos) → gate R1–R10 (video.py ganchos --check)
                  → crítico en modo selección (en silencio; seleccion.json: ganador y segundo para la versión B)
                  → guionista (ganchos --usar: el ganador es la escena 1) → guion.json v2 → gate V1–V5 + V9 (video.py guion --check)
                  → crítico de retención (C1–C11, puntajes, faltas) → el guionista corrige lo que bloquea
                    (≤ 2 vueltas) o, una sola vez, pule las mejoras si el crítico aprueba con algún puntaje de 3
                  → animador (solo si hay una escena explica nueva: video/animaciones/<id>.js, animaciones.py --check)]
→ voz (MCP ElevenLabs: un nodo TTS por escena, 1 toma) → Scribe por escena (tiempos por palabra, 0 créditos)
→ descargar --estado (el JSON de estado guardado → voz_N.mp3, palabras_N.json, creditos.json)
→ tiempos (V16 aprieta la voz, atempo 1.1, V6, eventos y efectos por escena, V10 ritmo) → escuchar (whisper.cpp local, V11: las cifras
  dichas) → grabar (Playwright cuadro a cuadro, N escenas a la vez con `--paralelo`, V7)
→ montar (ducking + efectos + loudnorm en dos pasadas, V8) → revisar (hoja de contacto, V12 quietud, V15 primer cuadro)
→ [opcional: variante (versión B: el segundo gancho, solo la voz de la escena 1)] → entregar
→ memoria.py --video → make validate
```

El **guion lo orquesta el Workflow `.claude/workflows/video.js`** (0 créditos: ganchos + selección + guionista + crítico +
animador). La voz y todo
lo que gasta créditos sigue en la **sesión principal** (`.claude/commands/video.md`), porque las llamadas al
MCP de ElevenLabs se hacen desde ahí. `TRABAJO` = `sesiones/<slug>/video/` (memoria de trabajo: audio, clips,
cuadros, `critica.json`).

## Formato fijo (decisiones del usuario)

- **Sin cara**: texto cinético (gancho y golpes) y las tarjetas del hilo animadas. Ni presentador ni avatar.
- Voz **El Faraon 4** (`8mBRP99B2Ng2QwsJMFQl`), `eleven_multilingual_v2`, `language_code: es`, a **1.1×**
  (atempo, sin cambiar el tono). Las cifras se dicen en palabras (`scripts/numeros_es.py`).
- **Pausas**: `[pausa]` (0.6 s) y `[pausa larga]` (1.2 s) en el texto del guion (más `[pausa adivina]`, 2.0 s, que el
  script mete antes de la respuesta de la adivina) salen como `<break time="…s" />`
  **solo en el prompt** de ElevenLabs (Multilingual v2 lo acepta; v3 y v4 no). Van tras puntuación fuerte o justo
  antes de un «pero»; ≤ 1 por escena y ≤ 3 por video (V9): la documentación avisa de que el exceso acelera o ensucia
  la voz. La locución alineada (V6), los subtítulos y el conteo de caracteres no las llevan (ElevenLabs sí las
  cobra, ~25 caracteres cada una). Scribe, conectado al nodo TTS, devuelve la etiqueta como tres «palabras» de
  duración cero (`<break`, `time="0.6s"`, `/>`): `descargar` y `tiempos` las quitan (`sin_etiquetas`). El MCP
  recorta `generations[].prompt` a 200 caracteres en el estado: `descargar --estado` casa la voz por
  `media[].prompt` (entero) y, si no viene, por prefijo.
- **Estructura de retención** (la comprueba V9): escena 1 = el gancho elegido (`familia` contraste | paradoja | lugar |
  escala | tu | pregunta | ranking | resultado y `visual` cifra | llenado | pareja | figuras | lugar; R1–R10 de
  `referencias/ganchos.md`), cuya pantalla y visual funcionan en silencio; **promesa** literal en la escena 1–2 que se
  **paga** en el último tercio; cada escena desde la 3 empieza con «pero» o «por eso» (y «y» como máximo en un
  tercio); un **golpe** ≤ 6 palabras arriba de cada tarjeta; escenas `golpe` para traducir a escala humana
  («1 de cada 3», con `calculo` verificado), pagar o re-ganchar; ≤ 6 s entre eventos. Dos escenas de texto más,
  opcionales: **`definicion`** (término ≤ 3 palabras + una línea llana ≤ 90 caracteres; ≤ 1, 2 en largo) y
  **`adivina`** (pregunta con «?», tres opciones con cifra, `correcta`, una oración que pide pausar para responder
  («Pausa el video y piénsalo.», V9) con la píldora «Pausa y responde» en pantalla y el revelado tras 2 s de silencio;
  ≤ 1, desde la escena 3). Y **`explica`** (≤ 1, 2 en largo; cuenta en el presupuesto de escenas de texto; página
  `video/explica.html`): una **animación a medida que explica el mecanismo** del fenómeno (por qué o cómo pasa), con
  `titulo` arriba y 2–6 `pasos` que entran cuando la voz los dice. La animación sale de la **biblioteca**
  `video/animaciones/` (`<id>.js` con `ANIM.registrar(id, {meta, pintar, seek})`, `catalogo.json` que escribe solo
  `scripts/animaciones.py`; organizada **por mecanismo**): el guionista nombra el `mecanismo` del fenómeno, escribe
  siempre el `brief` y reutiliza una del digesto **solo si muestra ese mecanismo y no salió en los últimos 2 videos**
  (`ROTACION_ANIMACIONES`, `memoria/videos.json` → `frases.animaciones`); si no, `animacion: null`, y tras la crítica el agente `video-animador` la escribe, la prueba (`animaciones.py --check`: lint sin azar,
  reloj, red ni colores fijos; grabación doble con framemd5 igual; 4:5; quietud; hoja de contacto por paso), la
  registra para otros videos y la asigna (`--asignar`, que repasa el gate). `entregar` suma el uso al catálogo.

  | mecanismo | qué hace el fenómeno | semilla |
  |---|---|---|
  | `cadena` | causa → efecto lineal: A lleva a B, B a C | `cadena` |
  | `ciclo` | se retroalimenta: el último paso empuja el primero | `ciclo-vicioso` |
  | `balance` | entra contra sale: el nivel sube o baja según cuál pesa más | `tanque-balance` |
  | `onda` | se propaga o se contagia desde un punto (el frenazo que viaja hacia atrás) | `onda-frenado` |
  | `embudo` | etapas que filtran: entran muchos, quedan pocos (sospechas → confirmados) | `embudo-filtro` |
  | `proporcion` | una división: si el denominador no crece, el cociente apenas baja (presos ÷ espacios) | `fraccion-espacios` |
  | `umbral` | se acumula hasta cruzar un límite y cambia de estado | — (la escribe el primer video que la pida) |
  | `cronologia` | eventos con fecha, uno tras otro (/historia) | `cronologia` |

  `cadena` es solo para causa → efecto lineal, nunca el comodín: forzar otro mecanismo en cajas apiladas lo
  rechaza el gate (el `mecanismo` de la escena ≠ el de la animación) y el crítico (C9). K4 (`validate.py`) cuida la biblioteca. Golpe, definición y adivina son escenas de texto (`golpe.html`): nunca dos seguidas. Y la
  escena **`mapa`** (≤ 1; cuenta como tarjeta): la tarjeta de mapa del hilo a pantalla completa (`video/mapa.html`,
  con el bloque `H` de `base.html` y la `GEOMETRIA` de la plantilla): los 22 departamentos se encienden uno a uno,
  el destacado entra al final con su rótulo y cada valor que dice la voz ilumina su departamento. Tres escenas más
  a pantalla completa, con página propia (≤ 1 de cada; la misma tarjeta no va dos veces): **`ranking`**
  (`video/ranking.html`; tarjeta barras-h o mapa, `top` 3–6, `orden` desc|asc): cuenta regresiva en la que cada
  puesto entra del último al primero cuando la voz dice su valor (la voz dice al menos el del primero, V9); el
  primero (o el `destacar` de la tarjeta) va con el acento. **`tiempo`** (`video/tiempo.html`; tarjeta
  antes-despues o linea, hasta 9 puntos): un riel con los puntos equiespaciados, un marcador que lo recorre y el
  valor de cada punto que salta cuando la voz lo dice (o cuando el marcador llega); en antes-despues, la píldora
  (×1.77 o +77 %) al final. **`escala`** (`video/escala.html`; sin tuit, u opcionalmente waffle o pictograma):
  `de_cada: [K, N]` (N entre 2 y 100), `etiqueta` (≤ 40) y `calculo` que respalda «K de cada N» (la voz lo dice,
  V9): N figuras de persona y las K primeras se encienden al decir K. `preparar` guarda los `DATA` de cada tarjeta
  (`datos` en `video.json`, evaluados con node) para que `tiempos` sepa qué valores entran y cuándo.
- **El gancho en 3 segundos**: la cifra (o el visual) está entera desde el cuadro 0 (R12: miniatura y bucle; aviso V15)
  y late cuando la voz la dice; el visual cambia cuando la voz dice cada número (el contenedor se desborda, el bloque
  crece, las figuras se encienden, cae el pin); la
  `linea` entra palabra a palabra **en sincronía con la voz** (cada palabra que la voz dice literal, al decirla; las
  demás, agrupadas como frase; sin ninguna coincidencia, repartidas hasta el fin de la primera oración); igual en
  golpes, definición y la pregunta de la adivina. V9 exige primera oración ≤ 4 s estimados, promesa ≤ 3 s si va en
  la escena 1 (si no, `en: 2`) y voz del gancho ≤ 7.5 s. La promesa es un evento (`promesa`, con `tic`). En las
  escenas de texto el subtítulo se oculta mientras solo repite lo que ya está en pantalla (y hasta que aterriza
  la cifra): aparece para lo que no está (la promesa, la respuesta de la adivina, la explicación).
- **Barra de progreso** arriba en todas las escenas, un tramo por escena (cierre incluido) de largo proporcional a su
  duración (`V.pintarProgreso`; `/noticias` agrupa por noticia y `/historia` por acto).
- **«Guatemala» en los primeros 6 s** (R6), donde funcione mejor: en la voz o la pantalla del gancho o en la
  primera oración de T1. Desde 2026-10-23 el script **ya no antepone «En Guatemala»** y la voz del gancho no abre con
  contexto (R3): los cinco primeros videos abrían igual y abrir con contexto frena menos (usuario, 2026-10-23).
- **La voz es una oración, la pantalla puede ser titular.** En el gancho y en cada golpe, la oración de la voz que
  dice la pantalla lleva un verbo conjugado, declarado en `verbo` (V9): «Casi 168 al día» en pantalla → «Nacen casi
  168 bebés al día de madres de 10 a 19 años» en la voz. «Casi 168 bebés al día, de madres de 10 a 19 años» (el
  titular leído en voz alta) no se entiende (usuario, 2026-10-20).
- **Cierre en dos pantallas** (una sola voz): primero **Conclusiones** (rótulo, eco de la cifra del gancho y el
  `resumen` de 2–3 líneas mientras la voz las dice; V9 pide ≥ 3 s de voz antes de la frase final); cuando la voz llega a
  la **frase final** (`cierre.final`: lo normal un **remate de consecuencia**, lo que la cifra le hace a quien la vive
  y no el dato otra vez; a veces una **pregunta**, nunca dos videos seguidos; catálogo, evidencia y reglas F1–F8 en
  `referencias/cierres.md`: anclada al tema sin analogías de otro ámbito, sin cebo, sin exponer al espectador en temas
  sensibles, gente como sujeto, sin fatalismo ni futuro que la fuente no proyecta, la forma y el mecanismo rotan;
  usuario, 2026-10-23 y 2026-10-24), las
  conclusiones salen hacia arriba y queda la frase final sola en grande y luego «Sígueme en» con TikTok
  @derekurizargt, Instagram @derekurizargt, Facebook Derek Urizar, YouTube @derekurizar y X @DerekUrizar **solo en
  pantalla** (`REDES` en `scripts/video.py`, íconos en `video/cierre.html`). Sin logo, sin fuentes, sin la
  marca en la voz.
- **Cierre en bucle**: tras «Sígueme en», el primer cuadro del gancho (barra de progreso en 0) durante 0.5 s con un
  fundido de 0.25 s: cuando TikTok repite el video, el reinicio no se nota (`montar --sin-bucle` lo quita).
- **Formato 4:5** (siempre; `entregar` lo exige): además del 9:16, `video_4x5.mp4` a 1080×1350 para el feed de
  Facebook e Instagram, con los mismos tiempos y audio; las páginas de escena cambian de layout con `?f=45` (`html.f45`: sin zona
  segura de teléfono, golpe en y=70, tarjeta en y=250–1090, subtítulos en y=1120). `grabar/montar/revisar --formato 4:5`
  (`clips_4x5/`, `segs_4x5/`, `contacto_4x5.png`); V8 espera 1080×1350.
- **Portadas**: cuadros **limpios** (Playwright vuelve a dibujar la escena en ese segundo con `&portada=1`: sin
  subtítulos ni barra de progreso; `video_grabar.js --portadas`): `portada.png` (el gancho leído en silencio),
  `portada_texto.png` (`video/portada.html`: solo el gancho en texto, para la miniatura del feed) y, para elegir,
  `portada_cierre.png` (el cierre con la frase final, remate o pregunta, en pantalla), `portada_giro.png` (la escena del giro con su cifra
  ya contada) y `portada_adivina.png` (las opciones a la vista). `entregar` copia todas.
- **Música** solo del catálogo fijo `design/musica/catalogo.json` (2 pistas por paleta; se elige la de la paleta
  del hilo usada hace más tiempo), con **ducking** bajo la voz (sidechain). **Efectos** solo del catálogo fijo
  `design/sfx/catalogo.json` (8 WAV: whoosh, tic, pulso, impacto, grave, riser, resolucion, foco), disparados
  por los eventos de cada escena. **`/video` nunca genera música ni efectos.**
- **Estilo Noche** (decisión del usuario, 2026-10-28; reglas y tokens en `referencias/diseno/sistema.md`), el mismo de
  las tarjetas de X:
  - **Fondo** = el color del tema llevado casi a negro (`noche.paletas.<p>.fondo`; `video.py colores()` →
    `escenas.json → colores`), con un **grano fijo** en el fondo del `body` (no depende de t: los cuadros salen
    idénticos en serie y en paralelo, y los oscuros no se parten en bandas al comprimir).
  - **Acento = una sola cosa por escena**: la cifra, el nombre o la palabra que suena (`--acento`, `--grafico`,
    `--pregunta` y la caja del subtítulo activo son el mismo tono). Texto **crema**; lo ya dicho o lo que falta, al
    26–55 %, solo en tamaños grandes.
  - **Tipos**: Archivo condensado 900 en mayúsculas (`.condensada`) para cifras, nombres y años; Archivo 800 para el
    golpe de arriba (68 px), los titulares y los subtítulos; JetBrains Mono 600 para kicker, fuente y crédito.
    **Instrument Serif no entra en ninguna escena** (la condensada se declara con su eje de ancho en `comun.css`;
    `font-stretch` va después del shorthand `font:`, que lo resetea).
  - **Golpe de arriba** (tarjeta, mapa, ranking, escala, tiempo, explica): la barra de progreso va primero y el golpe
    debajo, como titular, en Archivo condensado 900 en mayúsculas (96 px, se achica hasta 60) y en crema, con **una**
    palabra en el acento: la primera con cifra («220 frente a 86»), si no la primera de cantidad («Menos niños
    diagnosticados»); un titular solo de cifras va entero en el acento (`V.acentoDe` en `comun.js`; la pantalla del
    gancho usa la misma regla).
  - **Subtítulos** Archivo 800 a 60 px (y=1400), una sola palabra activa a la vez en una caja del acento
    con tinta oscura (#1A1208) y las que faltan al 38 %; un trozo no termina en «el», «de», «y»;
    **sin subtítulo doble**: si ≥ 60 % de las palabras del trozo ya se leen en pantalla, el subtítulo se calla.
  - **Colores solo por variables**: `--bg`, `--ink`, `--a1`, `--a2`, `--a3`, `--acento`, `--grafico`, `--pregunta`,
    `--resalte-bg`, `--resalte-ink`, `--tinta-acento` y `--fondo-golpe` (el fondo más oscuro, para el golpe que tiene
    que pesar); ningún hex en páginas de escena ni animaciones.
  - Las tarjetas del hilo se graban en Noche aunque el hilo sea de antes: `preparar` las rearma en `TRABAJO/tarjetas/`
    (plantilla, paleta y `DATA` de cada `tuit_N.html`) y `grabar` y V7 usan esa carpeta.
- **Zona segura** (medida en un iPhone con la app; vale para TikTok, Reels y Shorts, ver «Plataformas»): el video
  se escala para llenar el alto y pierde ~57 px por lado; la barra de pestañas tapa hasta y≈215, los íconos de la
  derecha x ≥ 900 desde y≈1070 y el nombre y el texto empiezan en y≈1645. Golpe y barra desde y=250 en la columna
  x 85–876; subtítulos en y=1400 (1500 en el cierre); **el contenido termina 30 px antes de los subtítulos**. Las
  variables viven en `video/comun.css` (`--corte`, `--sup`, `--fin`, `--iconos-x`, `--iconos-y`; sus valores 4:5 en
  `html.f45`), las páginas las leen con `V.zona()` (escala, ranking, mapa y el encaje de la tarjeta se dimensionan
  con ella) y el gate **V13** (`V.medirZona()`, cada 0.5 s mientras graba) rechaza lo que se salga.
- **Layout vertical de la tarjeta** (`video/vertical.css`, decisión del usuario tras el primer video: «en redes el
  layout es distinto»): la tarjeta no se incrusta al 86 %; se inyecta una hoja que oculta el titular y el handle,
  deja kicker → gráfico a todo el ancho (escala 1, y≈420–1220: por encima de la franja de íconos todo el ancho es
  seguro) → nota → «Fuente» pequeña. El **foco** hace zoom de 1.25–1.45 a la cifra mientras la voz la dice (el resto
  se sale de cuadro), con **deriva** lenta cuando no hay foco; el golpe entra desde la izquierda. V7 compara el
  render vertical contra el animado vertical (`video_animar.js` inyecta la misma hoja; `--cuadrada` para el modo
  viejo). Entre escenas, **transición de deslizamiento** de 0.3 s (`xfade` en `montar`, vertical en el giro).

## Plataformas

Un solo **maestro 9:16** (`video.mp4`, 1080×1920) se sube igual a **TikTok, Instagram Reels, Facebook Reels y YouTube
Shorts**; es el que se abre al entregar. Las cuatro apps tapan casi lo mismo: la zona segura medida (arriba) sale de
TikTok y cubre las otras en publicaciones normales; las guías de anuncios de Meta y YouTube reservan más abajo
(y > 1248), pero solo aplican a anuncios. **4:5** (`video_4x5.mp4`) para el feed de Facebook e Instagram.

- **Duración**: Shorts admite hasta 3 min (`SHORTS_MAX_S`); el `largo` (~4 min) se sube a YouTube como video normal
  (`entregar` y `caption.md` lo avisan). TikTok, Reels y Facebook admiten los tres.
- **Texto**: `caption.md` con una sección por plataforma (`caption.tiktok|instagram|facebook|shorts`; V5 exige las
  cuatro; la primera línea de `shorts` es el título de YouTube, ≤ 100 caracteres, y lleva `#Shorts`).
- **Miniatura**: una `portada_*.png` (1080×1920); lo importante va en el 3:4 central, que es lo que muestran las
  cuadrículas de perfil de Instagram y TikTok. En Shorts se elige en la app.
- **Sonido**: −14 LUFS y −1 dBTP (V8) sirven en las cuatro; ninguna publica un objetivo.

## Duraciones

| Duración | Objetivo | Escenas (más el cierre) | Voz | Costo de voz |
|---|---|---|---|---|
| `corto` | 60 s ±10 % | gancho + 3–4 tarjetas + 1–2 golpes | ≈ 810 caracteres | ≈ 850 créditos |
| `medio` (por defecto) | 120 s ±10 % | gancho + 6–8 tarjetas + 2–4 golpes | ≈ 1,675 | ≈ 1,700 |
| `largo` | 240 s ±10 % | gancho + 11–15 tarjetas + 3–6 golpes | ≈ 3,437 | ≈ 3,450 |
| `prueba` (solo fixture) | 55 s ±10 % | gancho + 2–3 tarjetas + 0–2 escenas de texto | ≈ 744 | 0 (voz falsa) |

Medido: 15.5 caracteres de voz por segundo a 1.1×, más 0.7 s por escena y 2.8 s de cierre; presupuesto =
`(s − 0.7·(1 + máx tarjetas + máx golpes) − 2.8)·15.5`. Por escena: gancho 30–130 caracteres, tarjeta 40–230,
golpe 20–110, cierre 40–200. Scribe, música y efectos: 0 créditos. Los estudios de video de datos en TikTok
dan una media de 84 s y recomiendan ≤ 90 s, pero el usuario prefiere `medio` por defecto (2026-10-20): en un minuto «algo muy informativo se siente como un resumen y corriendo»; `corto` se pide a propósito.

## Gates (`scripts/video.py` y `video.js`)

| Gate | Dónde | Qué exige |
|---|---|---|
| V1 escenas | `guion --check` | tipos `gancho|tarjeta|golpe|definicion|adivina|mapa|ranking|escala|tiempo|explica`; tarjetas y escenas de texto (con `explica`) en el rango de la duración; cada `tuit` con tarjeta y sin repetir; contexto ≤ 40; cierre con texto, 2–3 líneas de resumen (≤ 40) y pregunta; ≤ 1 `explica` (2 en largo), nunca dos seguidas; el `gancho` de texto suelto del formato viejo se rechaza |
| V2 cifras | `guion --check` | cada número de la voz, la pantalla, la línea, el golpe, el resumen y los captions tiene respaldo en `datos.json` (`verificacion.sueltos`, como G10) o en el `valor_calculo` de su escena; «K de cada N» en la voz o en pantalla no cuenta como números sueltos cuando su `calculo` respalda N/K (o K con N = 100): así se escribe la escala humana y la escena `escala` |
| V3 voz | `guion --check` | sin dígitos en la voz; ida y vuelta de cada conversión; ninguna cifra de género ambiguo sin `{n:f}`/`{n:m}` |
| V4 presupuesto | `guion --check` | caracteres de voz por tipo (gancho 30–130, tarjeta 40–230, golpe 20–110, cierre 40–200); duración estimada en ±10 % del objetivo |
| V5 reglas | `guion --check` | cierre termina en la pregunta; el cierre no menciona fuentes, el hilo, la marca ni «sígueme»; sin «en suma», enlaces ni @handles en voz, golpes, pantallas ni líneas; captions presentes |
| **V14 ganchos** | `ganchos --check` | `ganchos.json`: 4–5 candidatos de familias distintas, ≥ 2 con visual ≠ `cifra`; cada uno pasa R1–R10 (`referencias/ganchos.md`): pantalla y línea en silencio, referente, sin abrir con contexto, pantalla y visual dichos, 3 s, «Guatemala» (aviso si va en T1), «hoy» solo con datos del año, pregunta contestada, rotación (familia ≠ últimos 2 videos, visual ≠ último), un número con respaldo; voz en palabras (V3), presupuesto, respaldo (V2) y `verbo`; `visual_datos` con ids de cifra o `calculo`; `--usar` copia el ganador (de `seleccion.json`) a la escena 1 |
| **V9 estructura** | `guion --check` | escena 1 = gancho único, **el elegido** (`ganchos.json` → `elegido`: familia, visual, pantalla, línea y voz tal cual) y R1–R10 de nuevo con T1 a la vista (R6), `pantalla` (cifra o ≤ 4 palabras, ≤ 24) y `linea` (≤ 8 palabras, ≤ 60) que pasan la prueba en silencio **y cuyas palabras clave la voz dice** (en un golpe, solo aviso: vale un sinónimo); en gancho y golpes, la oración de la voz que dice la cifra de la pantalla (o la primera) contiene el `verbo` declarado; escena 2 = T1 sin enlace; cada tarjeta con `golpe` (1–6 palabras, ≤ 40, ≠ titular); `enlace ∈ pero|por_eso|y` desde la escena 3 con su conector al inicio de la voz y «y» ≤ ⌊n/3⌋; golpes con pantalla y línea, nunca dos escenas de texto seguidas ni en la escena 2; `definicion` con `termino` (≤ 3 palabras, ≤ 24) y `definicion` (≤ 90), la voz dice el término y **antes** anuncia que viene un concepto (`ANUNCIOS_DEFINICION`: «para entender», «qué es», «antes de seguir»…; la pantalla pone el rótulo «Para entender»); `adivina` con `pregunta` (≤ 70, «?») cuyas palabras dice la voz (se escribe a su ritmo), 3 `opciones` (≤ 14, con cifra, distintas) y `correcta`, la voz nombra las tres, después pide pausar para responder (`PAUSA_ADIVINA`) y su última cifra es la correcta, que lleva respaldo (V2) mientras las otras dos son señuelos exentos; `explica` con `mecanismo` (cadena|ciclo|balance|onda|embudo|proporcion|umbral|cronologia), `brief` siempre (40–400) y `animacion` del catálogo con ese mismo mecanismo y fuera de las de los últimos 2 videos, o null, `titulo` (≤ 6 palabras, ≤ 40), 2–6 `pasos` (≤ 28, cifras con respaldo) que la voz dice uno por uno; cierre con ≥ 3 s de voz antes de la pregunta (la pantalla de conclusiones); ≤ 1 definición (2 en largo) y ≤ 1 adivina; `mapa`, `ranking`, `tiempo` y `escala` ≤ 1 cada una, con `tuit` de una tarjeta de la plantilla que admiten (mapa; barras-h o mapa; antes-despues o linea; waffle o pictograma, opcional) y `golpe`; `ranking` con `top` 3–6 ≤ items y la voz dice el primer valor; `escala` con `de_cada` [K, N] válido, `etiqueta` ≤ 40, `calculo` y la voz dice «K de cada N»; `promesa.texto` (10–80) literal en la escena `en` ∈ {1, 2} y `pago` en el último tercio; `calculo` legible (ids de cifra, literales de `datos.json`, constantes) cuyo resultado aparece escrito en la escena; **ritmo estimado** ≤ 6 s entre inicio, fin de la primera oración, cada cifra y fin (la `explica` marca su ritmo con los pasos: lo mide V10 con los tiempos reales); **gancho en 3 s**: primera oración de la voz ≤ 4 s estimados, promesa ≤ 3 s si `en: 1`, voz del gancho ≤ 7.5 s |
| Workflow | `video.js` | retorno de video-gancho coherente (gate ok, 4–5 candidatos, familias distintas, ≥ 2 con visual); selección coherente (ganador y segundo entre los candidatos, puntajes de todos; sin ganador, faltas con arreglo → video-gancho rehace una vez; si sigue sin ganador, devuelve `corregir` y el comando pregunta al usuario); retorno del guionista coherente (gate ok, tipos, gancho primero, T1 segunda, promesa/pago en rango, pregunta con «?»); retorno del crítico coherente (bloqueantes, veredicto, cada puntaje ≤ 2 con falta `bloquea` de su regla); ≤ 2 vueltas de corrección de lo que bloquea; una sola vuelta de pulido, solo si aprueba con algún puntaje de 3 (aprobado con todo ≥ 4 no se pule: las mejoras van al reporte y el coordinador aplica las que son solo texto en pantalla); si sigue en `corregir`, el comando pregunta al usuario antes de gastar créditos |
| V6 alineación | `tiempos` | las palabras de Scribe coinciden con la locución (si no, rehacer la voz de esa escena); duración real fuera de ±15 % = aviso |
| **V10 ritmo** | `tiempos` | con tiempos reales, hueco máximo entre eventos visuales (golpe, entrada, cifra, foco, nota, línea y cada palabra de la línea que la voz dice, promesa, fin, y cada año dicho que la tarjeta tiene en su eje: la columna late sin zoom) ≤ 6 s; **aviso**, no falla. `tiempos` también fija la transición de entrada de cada escena del catálogo `TRANSICIONES` (del gancho a la primera tarjeta `smoothleft`; tarjeta → tarjeta `slideleft`; entrada a golpe o definición `smoothleft`; a la adivina `circleopen`; a una escena a pantalla completa `circleopen`; el giro `slideup`; el cierre `fade`; el bucle `fade`; `zoomin` queda fuera: escala con píxeles enteros y se ve pixelado) y desplaza golpe y cifra 0.3 s para que no queden bajo el `xfade`; `montar` rechaza (V8) una transición fuera del catálogo |
| **V11 escucha** | `escuchar` | **whisper.cpp local** (`brew install whisper-cpp` + `make whisper`, modelo `ggml-small` en `sesiones/_descargas/whisper/`; opcional) transcribe cada `voz_N.mp3` **sin el guion** y lo coteja con la locución: dígitos → palabras con `numeros_es`, coma decimal, género de los numerales y tildes no cuentan; un tramo distinto que toca una palabra numérica es **FALLA** (retoma de esa escena), el resto aviso (ortografía de whisper). Scribe, conectado al nodo TTS, alinea el prompt (devuelve hasta `<break>`): V6 no detecta una cifra mal dicha. Sin whisper, `AVISO V11` y sigue. Resultado en `audio/escucha.json` |
| **V12 quietud** | `revisar` | por clip, diferencia media de luma entre cuadros muestreados a 4 fps y 270 px (`tblend=difference` + `signalstats`): un tramo de ≥ 2.0 s con todo < 0.02 es pantalla congelada → **aviso** («E7 2.3 s sin movimiento desde 7.5 s»; `--estricto` lo vuelve fallo). La deriva (0.1–0.9) y cada palabra que entra (0.3–1.0) cuentan como movimiento; una pantalla quieta mide < 0.01. `revision/quietud.json` guarda la serie por escena |
| **F1–F8 cierre** | `guion --check` | `cierre.tipo` remate o pregunta y `forma` del catálogo (remates: consecuencia, pendiente, quien_decide); `final` = la última frase de la voz, ≤ 14 palabras (una pregunta, una sola con «?»; un remate, sin «?»); nombra el tema (una raíz del tema, los titulares o el concepto de una cifra del hilo); sin cebo («comenta», «etiqueta», «te leo»…); en un tema sensible, ni pregunta de experiencia ni la casa, la familia o «alguna vez» del espectador; **F6** un remate dice ≤ 1 cifra y nunca la del gancho, y la consecuencia declara `mecanismo`, `quien` (gente, en la frase) y `verbo` (en la frase); **F8** un remate sin fatalismo («no hay nada que hacer») ni futuro de una pérdida que la fuente no proyecta; **F7** una pregunta no sigue a otra, la forma (salvo consecuencia) no repite la de los últimos 2 videos y el mecanismo no repite el del último (`cierres_recientes`) |
| **V16 voz de corrido** | `tiempos` | ElevenLabs a veces mete un silencio **dentro** de un nombre propio, una sigla o una cifra («que le dijo a la B…BC», «dos mil… dos»). Antes del `atempo`, `apretar_voz` (`video.py`) busca con `silencedetect` (−35 dB, ≥ 0.06 s; los tramos pegados se unen) los silencios que caen dentro de una palabra (≥ 0.10 s, lejos de sus bordes: más que el cierre de una «p» o una «t») o entre dos palabras de la misma cifra (el segmento `p ≠ v` de la locución) o del mismo nombre (palabras seguidas con mayúscula o siglas, unidas por de/del/la/las/los; la corrida acaba en coma, punto o dos puntos) (≥ 0.08 s), y los deja en 0.03 s; mueve los tiempos de Scribe lo recortado. `voz_N.mp3` queda intacto (repetir `tiempos` da lo mismo); lo recortado se imprime («V16 E4 «BBC» −0.21 s…») y queda en `escenas.json → escenas[].apretado`. Una palabra de cifra o de nombre que sigue alargada sin silencio (> 1.6 × lo que pide su largo) es **aviso**: retoma esa escena (`voz --sueltas N`). Nunca se estira ni se pausa la voz para que case con la pantalla: la pantalla sigue a la voz |
| **V15 primer cuadro** | `revisar` | el cuadro 0 del gancho tiene algo dibujado (≥ 1.5 % de la zona de contenido distinta del fondo): es la miniatura del feed y la vuelta del bucle (R12); **aviso** |
| **V13 zona segura** | `grabar` (y `animaciones.py --check`) | cada 0.5 s y en el último cuadro, `V.medirZona()` (`video/comun.js`) mide lo visible al menos a media opacidad (texto, SVG, imágenes, cajas con fondo; también dentro de la tarjeta, con su transform): nada sale del recorte lateral (57 px), entra en la barra de arriba (y < 215), baja de los subtítulos (top de `#subs` − 30) ni entra en la columna de íconos (x > 900 desde y 1070); en 4:5, solo el fin antes de los subtítulos. Durante un foco de la tarjeta se mide solo la caja enfocada (el resto sale de cuadro a propósito) y el paso de un foco a otro no se mide. Escribe `revision/zona[_4x5].json`; falla (los clips quedan escritos). `revisar` dibuja la zona en rojo sobre `contacto.png` |
| V7 animación | `grabar` | el último cuadro de cada tarjeta animada es idéntico a su render estático (`scripts/video_animar.js --check`, ≤ 0.1 % de píxeles); el foco vive fuera del iframe y `__caja` no lanza |
| V8 salida | `montar` | 1080×1920 con audio; −14 ±1.5 LUFS; true peak ≤ −1 dBTP (música 0.22 con ducking; efectos del catálogo; loudnorm en dos pasadas) |
| K2 efectos | `validate.py` / `sfx.py --check` | `design/sfx/catalogo.json` con los 8 ids fijos, cada WAV presente, duración 0.2–4 s coherente con la cabecera, ganancia −40–0 dB |
| K3 iconos | `validate.py` / `iconos.py --check` | `design/iconos/catalogo.json` (biblioteca FIJA: 50 iconos Lucide, tag fijado, licencia ISC; `make iconos` la baja UNA vez): cada SVG presente, 24×24, ninguno fuera del catálogo, `LICENSE.txt`. Solo se comprueba si el catálogo existe; el guion la usa con `icono: "<id>"` en gancho, golpe y definición (V1) |

Crítico (`referencias/roles/video-critico.md`, C1–C11): gancho en silencio · razón para quedarse · «¿por qué seguiría
viendo?» por escena · pero/por eso reales · escala humana · pago · ritmo y re-gancho · cierre · lenguaje y honestidad ·
lectura de corrido · plantilla (C11: la promesa, el gancho (familia, visual y frase), las aperturas y la pregunta no repiten
las de «Frases ya usadas» y «Ganchos recientes»). Antes del guion, el mismo crítico elige el gancho en **modo selección**
(silencio, referente, tensión, alineación, honestidad, novedad; R11).
Puntajes 1–5: gancho, bucle, ritmo, escala_humana, pago, cierre. `pasa` = sin faltas `bloquea` y todos ≥ 3.

## Piezas

- `scripts/video.py` (subcomandos, `--help`) · `scripts/numeros_es.py` (`--prueba`) · `scripts/video_grabar.js`
  · `scripts/video_animar.js` (V7) · `scripts/sfx.py` (`--importar`, `--check` = K2) · `scripts/iconos.py` (`--importar`,
  `--check` = K3, `--lista`) · `video/portada.html` (portada de texto).
- `video/golpe.html` (gancho con visual `cifra` y golpes: cifra + línea palabra a palabra) · `video/gancho.html` (gancho con
  visual llenado, pareja, figuras o lugar, sincronizado con la voz por `tiempos_visual`) · `video/escena.html` (tarjeta con
  golpe arriba, foco y subtítulos con `.cifra`) · `video/mapa.html` (la tarjeta de mapa a pantalla completa) · `video/ranking.html` · `video/escala.html` · `video/tiempo.html` (escenas a pantalla completa) ·
  `video/cierre.html` · `video/animar.js` (animador propio para las 26 plantillas: estado = f(t), en p = 1 el DOM queda igual que el render, V7; `__caja` para el foco).
- `video/comun.css` y `video/comun.js` (módulo común `V`): fuentes, lienzo con el fondo Noche y su grano, `.condensada`,
  golpe de arriba, barra de progreso por grupos, subtítulos, rótulo de acto, portada limpia y base 4:5; parámetros de la URL, curvas (`V.eo`, `V.prog`), `V.cargar` (escenas.json y
  paleta), `V.tarjeta` (los `DATA` de una tarjeta), `V.subtitulos`. **Una escena nueva** enlaza `comun.css` antes de su
  `<style>`, carga `comun.js` antes de su script, usa `V.*` y escribe solo lo propio; su `seek(t)` sigue siendo
  función pura de t (sin relojes ni animaciones CSS), y `video_grabar.js` la añade a su lista blanca.
- `design/musica/` y `design/sfx/` (bibliotecas fijas) · `.claude/workflows/video.js` · `.claude/agents/video-gancho.md`
  + `referencias/roles/video-gancho.md` + `referencias/ganchos.md` · `.claude/agents/video-guionista.md`
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

## Versión B del gancho

El segundo lugar de la selección queda en `ganchos.json` (`segundo`). Tras entregar el video A (o antes de
`entregar`): `video.py variante TRABAJO` arma `TRABAJO/variante_b/` con el mismo guion salvo la escena 1, copia la voz,
las palabras y los clips de las demás escenas e imprime el nodo de voz SOLO de la escena 1 (≈ 100 créditos). Con el
MCP: un nodo TTS + Scribe, `descargar variante_b --estado …`, `tiempos variante_b`, `grabar variante_b --solo 1`,
`montar variante_b` y `variante TRABAJO --cerrar` (deja `salida/video_b.mp4`); `entregar` lo copia junto a
`video.mp4` y `guion.json` de entrega lleva `ganchos` (candidatos, elegido, segundo y puntajes). Se publican las dos
y se compara «Visto frente a deslizado» (YouTube Studio) o la retención a 3 s (TikTok).

## Pendiente de cada corrida real

Scribe devuelve el texto del guion alineado al audio, no una escucha independiente: **el usuario escucha las
cifras** antes de publicar. Si una cifra suena mal, se rehace solo el nodo de esa escena. Tras la primera
corrida real, comparar en TikTok con el video anterior (retención a 3 s y tiempo medio) y recalibrar
`RITMO_MAX_S` y los umbrales del crítico con ese dato.
