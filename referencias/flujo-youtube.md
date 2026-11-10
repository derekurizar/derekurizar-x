# Flujo · `/youtube-long` (una serie → un video largo de YouTube)

Una serie de `/serie` entrega partes verticales de 90–150 s, cada una hecha para entenderse **sola**. `/youtube-long`
las convierte en **un video 16:9 de 8–20 min** que se oye como UN documental. No es un guion nuevo: es un **montaje** de
escenas ya verificadas y grabadas, con cortes y unas pocas piezas de voz nueva.

## Por qué una serie pegada se siente repetitiva

Medido en `series/2026-11-06-el-caso-la-linea` (7 partes, 17.3 min tal cual):

| Qué se repite | Cuánto | Quién lo resuelve |
|---|---|---|
| Ganchos de las partes 2–7 y cierres con «Sígueme: en la N parte…» de las partes 1–6 | 12 escenas | el script (fijo) |
| El resumen de la serie (SE14) de la última parte | 1 escena, 26 s | el script (fijo) |
| El mismo hecho contado en dos o tres partes (las capturas del 16 de abril, la escucha a Miao Miao, la sentencia…) | 23 hechos | el editor: quitar, recortar o `reprise` |
| La misma persona presentada otra vez | Monzón ×6, Velásquez ×4, Eco ×4… | el editor: `quitar` el inciso |
| La misma sigla explicada otra vez | CICIG ×6, SAT ×4 | el editor: `quitar` el inciso |
| Muletillas («Ninguna fuente explica la diferencia») | ×3 | el editor |
| Saltos atrás en el tiempo (una serie de caso va por tema) | casi en cada capítulo | el editor: un puente |

`youtube.py preparar` lo mide en código (`repeticiones.json`): hechos por id (`escenas[].hechos` de cada guion), frases
de ≥ 8 palabras, presentaciones (nombre + raíces de su `presentacion` en la misma escena) y glosas («la X, la …,»).

## Las operaciones

| Operación | Costo | Audio |
|---|---|---|
| `op: quitar` | 0 | se omite |
| `quitar: ["texto literal"]` (frase o inciso) | 0 | `voz_N_r.mp3` cortado con los tiempos por palabra de `escenas.json`, a mitad del silencio, con fundidos de 4 ms (como `partir_secuencia`); solo en silencios ≥ 80 ms y sin partir un nombre (YT6); los tiempos de la escena (palabras, eventos, efectos, titular, oraciones, rótulo, tarjetas de persona) se corren con el corte |
| `puente` (1–2 oraciones, foto, titular, hechos) | ~1 crédito por carácter | voz nueva en `nuevas/` (un TRABAJO de /historia con solo las piezas nuevas: `historia.py tiempos` arma su escena `foto`) |
| `promesa` global (una oración) | ~1 crédito por carácter | igual |
| `op: revozar` (solo `foto`, ≤ 3) | ~1 crédito por carácter | igual: la escena se vuelve a cronometrar entera |

Las marcas del formato corto también salen del render: el kicker «Serie · <tema>», el chip «Parte N de M», «Parte N+1», «Empieza por la Parte 1»,
la invitación del cierre, el bucle final, la barra de progreso y los subtítulos quemados (van en el `.srt`). Los
**rótulos de acto se quedan**: llevan el año y ubican en el tiempo, que es justo lo que un video largo necesita. Las
**tarjetas de persona** salen la primera vez y otra vez solo si pasaron ≥ 5 min.

## Estructura del video

```
0:00  gancho de la parte 1 · promesa global (voz nueva) · rótulo «Capítulo 1 de N» · escenas de la parte 1…
      rótulo «Capítulo k de N» (2.8 s, sin voz, el año cuenta, música nueva) · [puente] · escenas de la parte k…
fin   cierre de la última parte (legado) en la columna izquierda + 12 s de pantalla final para los elementos de
      YouTube en la mitad derecha
```

La música alterna las dos pistas de la paleta por capítulo, fundidas 2 s en cada rótulo. Las promesas y bisagras de
cada parte se quedan: son mini-ganchos de capítulo.

## Orquestación

1. `youtube.py preparar SERIE`: `youtube.json`, `indice.json`, `repeticiones.json` y `montaje.borrador.json`.
2. Workflow `youtube` (0 créditos):
   - `youtube-editor` escribe `montaje.json` (gate `youtube.py montaje --check`);
   - `historia-oyente` en «Modo largo» lo oye de corrido;
   - `video-critico` en «Modo largo» lo critica (Y-C1–Y-C6, arreglos probados con `youtube.py probar`, ≤ 2 vueltas);
   - con «pasa», las mejoras que el crítico ya probó se aplican solas con `youtube.py aplicar` y el gate se repite (si
     juntas no pasan, el montaje queda como estaba y vuelven como mejoras; m113);
   - el Workflow se detiene con `aprobar_montaje`.
3. El usuario aprueba (`youtube.py resumen`) o pide un retoque.
4. `youtube.py voz` (nodos para el MCP en `lotes` de ≤ 3, o `--falsa`) → `video.py descargar <T>/nuevas --estado <archivo|->`
   (el estado pegado tal cual vale) → `youtube.py tiempos` (sin el aviso de duración V6: `nuevas/` son piezas sueltas).
5. `youtube.py armar` → `grabar` (16:9) → `montar`.
6. `youtube.py miniatura` (3 opciones; el usuario elige) → `entregar` → `memoria.py --youtube`.

## Render 16:9

`video_grabar.js --formato 16:9` (1920×1080, `clips_16x9/`, `?f=169`).

**Páginas.** Las que tienen layout horizontal propio (`PAGINAS_169`) son `noticia` (foto, gancho, toma), `historia`
(cita, capítulo), `golpe`, `escena` (tarjeta), `explica`, `red` y `cierre`. Las demás (mapa, ranking, escala, tiempo,
cuenta, hemiciclo, `gancho.html`) se dibujan en 4:5 dentro de `video/escenario.html`.

**Reglas en el código.** `comun.js` pone `html.f169` sobre `html.f45`, así hereda lo compacto del 4:5. Cada página pisa
lo suyo con `html.f169.f45 …`. La zona del 16:9 tiene márgenes de título del 5 % (96 px), y V13 la mide igual (YT9).

**Fotos.** Una foto vertical o casi cuadrada va entera en un panel a la derecha, sobre su copia ampliada, borrosa y
oscura: recortada para llenar el cuadro, quedaba una corbata en lugar de la cara. En la miniatura, el foco (la cara)
manda también en las horizontales; si cae en la columna del texto (centro x < 0.55), la foto va en panel.

**Tarjetas.** En `escena.html` la tarjeta crece hasta llenar una ventana de 1728×860 (≤ 1.5×) y se centra: a escala 1
los gráficos se veían chicos en pantalla grande. Los focos acercan desde ahí.

## El expediente en pantalla (2026-11-10)

El 16:9 dejaba media pantalla vacía en cita, golpe, tarjeta y explica (columna centrada con 300–460 px lisos por lado).

- **Margen de expediente** (`S.margen`, `youtube.py margenes`; `V.margen` en `video/comun.js`): con ≥ 3 personas ya
  nombradas, el contenido va a la izquierda y a la derecha queda el expediente: capítulo y título, los **cuadritos** de
  las personas nombradas hasta ahí (3 × 3), el nombre y cargo de quien la voz dice, y la línea de capítulos. La tarjeta
  de persona no se dibuja en esas escenas.
- **Regla del margen (coherencia):** nada entra al margen si la voz no lo nombró; no es decoración. Si un video no
  tiene personas (un `/explica` largo), no hay margen.
- **Tablero** en el rótulo de capítulo (`S.H.tablero`): los ya vistos atenuados y los que aparecen en ese capítulo
  entrando, unidos por hilos (solo las aristas de las escenas `red`, H23). **Sin tachas ni marcas**: solo se ilumina a
  quien se nombra (decisión del usuario). El tablero se arma de capítulo en capítulo; el rótulo dura 3.8 s.
- **Transiciones con sentido** (`transiciones_con_sentido`): un documento entra como hoja (`coverup`); si el año de los
  hechos avanza, empuja a la izquierda; si retrocede, a la derecha. Nunca por reloj.
- **Pantalla final**: «Suscríbete» con el handle de YouTube y «Sigue viendo →» hacia la mitad derecha.
- **Sonido**: sin efecto de entrada entre escenas de la misma parte, un `tic` cada 8 s y ≤ 6 efectos por minuto
  (`ralear_sfx_largo`); con `musica_tema` en `youtube.json`, las pistas del tema
  alternan por capítulo.
- **Regrabar solo lo que cambió**: `armar` conserva los clips y borra el de cada escena cuya entrada cambió
  (`huellas_escenas`); `grabar` sin `--solo` graba las que faltan. `armar --todo` los borra todos (cambió una página).
- **Entrega**: `fuentes.md` solo con los hechos de las escenas que quedaron y sin URL repetidas; `comentario.txt`
  (≤ 9,500 caracteres) para el comentario fijado; `caption.md` con etiquetas, playlist, miniaturas a probar y los Shorts
  que deben enlazar al largo; la hoja de contacto toma un cuadro por escena en su estado final.
- **YT8** pide además la promesa antes del segundo 15 y `promesa.pregunta` (P6).
## El adelanto y el teaser (2026-11-10)

YouTube mide la intro en los primeros 30 s, y nada llevaba de los cortos al largo.

- **Adelanto** (opcional, `montaje.adelanto = {ref: "Pk.eN", texto: "…"}`): los primeros 3–9 s del video son un momento
  alto que ya está grabado (una cita, una confesión), cortado de su escena; después entra el gancho. `texto` son las
  palabras literales **como las dice la voz** (las cifras en palabras). No es voz nueva y la escena completa sigue en su
  sitio. YT8 lo revisa (escena que queda en el video, ni gancho ni cierre, duración). No anuncia nada: es la historia.
- **Teaser** (`youtube.py teaser <TRABAJO>`): un 9:16 de ≈ 20 s con el arranque de la Parte 1 ya entregada (hasta el
  final de una escena, 12–26 s) y una pantalla final «Video completo · En YouTube». Deja `salida/teaser.mp4` y
  `teaser.md` con su texto. Se publica como Short, Reel y TikTok el día del largo.
## Gates

| Gate | Qué exige |
|---|---|
| YT1 | Cada escena de cada parte, una vez y en orden, en el capítulo de su parte. Un capítulo por parte, con título de ≤ 60 caracteres. El gancho de la parte 1 se usa. Toda op que no sea usar lleva `razon` |
| YT2 | Las marcas del formato corto se quitan. Nada de «Sígueme», «parte» con ordinal, «capítulo» ni anuncios en la voz que queda (en la voz nueva, tampoco P2/META_PROMESA) |
| YT3 | Puentes de 1–2 oraciones de ≤ 160 caracteres, con hechos `confirmado | una_fuente`, una foto de la serie y un titular de 1–7 palabras. Sus números pasan V2 |
| YT4 | Cada hecho una vez (`reprise` ≤ 3, con razón). Sin frases de ≥ 8 palabras repetidas. Una presentación y una glosa por persona y por sigla (tras 5 min, un recordatorio es aviso) |
| YT5 | Lo que sigue a un corte no abre con «Eso», «Ese», «Su»… sin `ancla` (aviso) |
| YT6 | Cortes en silencios de ≥ 80 ms, sin partir un nombre. Una cita no se recorta. ≤ 3 `revozar` |
| YT7 | 8–20 min. Cada capítulo de ≥ 60 s |
| YT8 | Promesa global de una oración, con una forma del catálogo, pagada en el último 40 % |
| YT9 | 1920×1080, márgenes del 16:9, −14 LUFS ±1.5, pico ≤ −1 dBTP |
| YT10 | Miniatura 1280×720, ≤ 5 palabras, texto ≥ 120 px a 1920 (≥ 18 px a 320×180), cifra con respaldo |
| YT11 | Título ≤ 100 caracteres. Descripción sin anuncios, ≤ 5,000 caracteres. ≥ 3 capítulos, el primero en 0:00 y cada uno de ≥ 10 s |

## Entrega

`series/<fecha>-<slug>/youtube/` contiene:
- `video.mp4` (fuera de git);
- `miniatura.png` (y las variantes);
- `caption.md` (título y descripción con los capítulos, listos para copiar, y cómo subirlo);
- `subtitulos.srt`;
- `fuentes.md` (las de cada parte, por capítulo: para el primer comentario);
- `montaje.json`, `capitulos.json` y `contacto.png`;
- `guion.json` (`tipo: youtube`).

Queda registrado en `memoria/youtube.json` (M20).
