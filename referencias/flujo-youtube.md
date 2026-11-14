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
5. `youtube.py armar` → Workflow `youtube` con `desde: "plano"` (un `youtube-realizador` por capítulo) → `plano --check --hoja` →
   `grabar` (solo los tableros) → `proyecto` → `revisar` → `audio` → `render` → `montar`.
6. `youtube.py miniatura` (3 opciones; el usuario elige) → `entregar` → `memoria.py --youtube`.

## El 16:9: una mesa de archivo en HyperFrames (2026-11-13)

**Qué pasó.** El 16:9 falló dos veces con Bancafé.
1. Con el motor propio era una foto por escena con un titular chico: 54 % del tiempo casi quieto, 10 fotos en 9 min.
2. El «arreglo» fue un gate que medía píxeles que cambian (el YT14 viejo). Se cumplió moviendo la cámara: de 176 tramos de
   voz, 61 recibieron un salto de escala sobre una cita, una tarjeta o una animación, 32 un plano de detalle sobre la
   misma foto, y solo 12 una foto nueva. El usuario: «pésimo… el dinamismo no implica que muevas una imagen solita de un
   lado a otro o hagas pequeña y grande una animación que ya está animada… Con dinamismo es que siempre estén
   apareciendo elementos, transiciones, datos, fotos». Era el error que ya había corregido el 2026-11-07 (CÁMARA QUIETA).

**Qué se decidió** (con un piloto de 83 s que el usuario aprobó: «todo está perfecto»):
- **Mesa de archivo.** Con cada oración cae una pieza real sobre una mesa: foto, recorte de prensa con su titular,
  página de un documento con la frase subrayada, ficha de persona o institución, lugar en el mapa, fecha, cifra con su
  rótulo. La pieza nueva queda al frente; con 3 encima, la de abajo se atenúa; al cambiar de tema, la mesa se barre.
- **La cámara no se mueve.** Una pieza que aterrizó se queda quieta. Las animaciones ya hechas (`explica`, `tarjeta`)
  van enteras y quietas dentro de un marco (el **tablero**), con las piezas a su lado.
- **HyperFrames dibuja y renderiza** el 16:9; el framework decide y verifica qué se muestra. El vertical va por el
  mismo camino desde el 2026-11-14 (en piloto: `referencias/flujo-mesa.md`, `scripts/video_hf.py`); el núcleo común es
  `scripts/mesa.py`.
- **Nunca un gate de dinamismo sobre píxeles o movimiento.** Se mide sobre los datos: cada oración tiene un golpe con
  respaldo.

**Las piezas** (todo en `scripts/youtube_hf.py`):
- `plano.json`: `{"mesas": [{"escenas": [claves], "golpes": [{"tipo", "escena", "dice", …}]}]}`. `dice` son las palabras
  literales de la voz que hacen entrar la pieza (la lógica de `historia.entradas_dice`); cae 0.3 s antes y aterriza en la
  palabra. El catálogo y el respaldo de cada tipo están en `referencias/roles/youtube-realizador.md`.
- `armar` escribe `plano.borrador.json` con lo que las escenas ya traen (su foto, su cifra, los años y las cifras que
  dice la voz, las personas que nombra). La maqueta lo usa tal cual (`plano --borrador`).
- El Workflow `youtube` con `desde: "plano"` lanza un `youtube-realizador` (opus) por capítulo y un cierre.
- `plano --check` corre YT13–YT19; `plano --hoja` escribe `plano.md` («la voz dice | entra en pantalla») para leerla
  antes de renderizar.
- `grabar` solo graba los **tableros** con el motor propio (16:9 limpio, recortado al centro, un cuadro clave por
  segundo) → `clips_tablero/`.
- `proyecto` genera un proyecto de HyperFrames **por capítulo** (`hf/cap-N/`: `index.html`, una composición por mesa,
  `assets/` con enlaces duros) y `hf/efectos.json` (un efecto del catálogo fijo por pieza: `papel`, `sello`,
  `marcador`, `impacto`, `tic`, `whoosh` al barrer). Las piezas se colocan solas (`colocar`: el sitio que menos tapa a
  las tres últimas y queda cerca de la anterior); `x`, `y`, `w` en un golpe lo fijan a mano.
- Los rótulos de capítulo y el cierre («Suscríbete», mitad derecha libre para la pantalla final de YouTube) los arma
  `proyecto`: no van en el plano.
- `revisar` corre `hyperframes check` y copia una hoja de contacto por capítulo a `revision/hf_cap-N*.jpg`.
- `audio` mezcla la voz en su segundo (el de `escenas.json`: ya no se miden clips), la música por capítulo con ducking y
  los efectos, a −14 LUFS; escribe el `.srt` y los capítulos, y deja en cada proyecto su tramo como guía.
- `render` usa **un proceso por capítulo** (`--workers 1`), un capítulo tras otro (HyperFrames no deja correr dos renders a
  la vez: tiene un candado global), y los une sin recodificar. Tarda ≈ 1.6× la duración del video.
- `montar` pone la pista sobre el video (`-c:v copy`) y comprueba YT9.

**Lo medido en el piloto.**
- Render: 83 s de video en 41 s con 8 procesos y en 2 min 11 s con uno. El motor propio tardó cerca de una hora en 9 min.
- **Con varios procesos el video tiembla** («como una tele»): cada Chrome dibuja las piezas giradas con diferencias
  mínimas y los cuadros se intercalan. En un tramo quieto, la diferencia entre cuadros seguidos fue 1.9 con 8 procesos y
  0.00 con uno (90 MB frente a 24 MB). `--no-browser-gpu` no lo arregla. Por eso `--workers 1`.
- Ninguna pieza prehecha del catálogo de HyperFrames quedó en uso: las piezas son HTML y CSS propios en el estilo Noche
  (el bloque del mapa mundial bajaba datos de internet al renderizar). El mapa del mundo sale de
  `design/mapas/paises-50m.json` (Natural Earth, dominio público) y el de Guatemala de `design/mapa_geometria.svg`.

**Se retiró del motor propio** (era solo del 16:9): la grabación de todas las escenas en 16:9 y el montaje por tramos, el
margen de expediente y el tablero de los rótulos, las llamadas de cifras, la galería de fotos, los saltos de cámara y los
planos de detalle, el paso «Imágenes» (`youtube-imagenes`) y los gates de píxeles (YT12 de fondo liso y el YT14 viejo).
Las páginas conservan su layout `?f=169` porque los tableros lo usan.

## Otras reglas del largo (2026-11-10)

- **Pantalla final**: «Suscríbete» con el handle de YouTube; la mitad derecha queda libre para los elementos finales.
- **Música**: con `musica_tema` en `youtube.json`, las pistas del tema alternan por capítulo.
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
| YT13 | Cada cifra o año que dice la voz se ve en una pieza de la mesa, cuando se dice (`plano --check`) |
| YT14 | Cada oración trae un golpe (una pieza, un subrayado o un paso del tablero) cuyo `dice` está en la voz, y ningún hueco pasa de 6 s. La cámara y una foto repetida no cuentan |
| YT15 | Una foto ≤ 2 veces en el video y a ≥ 180 s de su otra aparición |
| YT16 | Cada pieza con su respaldo: foto con ficha y crédito; recorte con titular y extracto literales de una nota ya leída; documento con la frase en el PDF; números dichos por la voz o en los datos. Una foto de personas en un proceso solo sobre una oración que nombra a alguien |
| YT17 | Que no sea relleno: ≥ 50 % de las oraciones con pieza nueva; ≥ 35 % de las piezas son archivo real (aviso bajo 50 %); ≥ 4 tipos por capítulo; ≤ 2 rótulos de solo texto seguidos |
| YT18 | Carga: la mesa dura 4–45 s y lleva ≤ 12 piezas; dos piezas no entran a menos de 0.3 s; un tablero va solo en su mesa |
| YT19 | Ninguna escena lleva saltos de cámara |

YT12 (fondo liso medido en píxeles) se retiró el 2026-11-13 junto con el YT14 viejo.

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
