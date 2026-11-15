# La maqueta 3D: contrato `maqueta.json`

La «maqueta que vuela»: un mundo 3D simple (relieve, lugares, piezas) que una cámara recorre mientras la voz cuenta,
con una capa 2D encima (titular, pines que siguen al 3D, cifras, subtítulos). Decisiones del usuario (2026-11-14):

- **Motores:** three.js dentro de HyperFrames para unos estilos y Blender + capa 2D de HyperFrames para otros. El
  estilo decide el motor. Remotion quedó fuera.
- **Un solo estilo por video; nunca se mezclan.** Lo elige el orquestador entre los ocho; si no está seguro, pregunta.
- **Dentro de la maqueta la cámara se mueve** (es la excepción a la cámara quieta de la mesa de archivo).
- **El gancho manda y todo concuerda:** lo que se ve es lo que la voz está diciendo.
- **El cuadro 0 es la portada:** el primer cuadro ya trae su titular completo y el evento del gancho a la vista.
- **Lienzo completo:** el mundo llega a los cuatro bordes del cuadro; el texto va encima con un degradado.

`maqueta.json` es el único insumo del motor: tiempos **absolutos en segundos**, ya resueltos (quien lo escribe es
`scripts/video3d.py`, que convierte cada `dice` del guion en su segundo con la voz real, o estimado antes de la voz).
El motor no sabe de guiones ni de voz. `scripts/maqueta3d.py` lo valida (gates M3D, sobre los datos: nunca sobre
píxeles), saca cuadros sueltos y lo renderiza **con el motor del estilo**: los dos motores leen el mismo `maqueta.json`,
pasan los mismos gates y dejan las mismas salidas (ver «Motor Blender»).

## Forma

```json
{
  "version": 1,
  "estilo": "noche",
  "paleta": "obsidiana",
  "fps": 30,
  "duracion_s": 46.2,
  "protagonista": "motagua",
  "mundo": {
    "set": "guatemala",
    "exageracion": 5.0,
    "lugares": {"mi-aldea": {"lon": -89.10, "lat": 15.32, "nombre": "Mi aldea"}},
    "piezas": [
      {"id": "motagua", "tipo": "falla", "trazos": ["Motagua Fault", "Western Motagua Fault"]},
      {"id": "traza76", "tipo": "falla", "puntos": [[-90.70722, 14.86057], [-90.60010, 14.84294], [-89.00519, 15.29326]]},
      {"id": "pueblos", "tipo": "luces", "lugares": "todos"},
      {"id": "frontera", "tipo": "frontera"},
      {"id": "ca9", "tipo": "ruta", "lugares": ["guatemala", "guastatoya", "zacapa", "puerto-barrios"]}
    ]
  },
  "camara": [
    {"t": 0.0, "mira": [-90.25, 15.75], "dist_km": 1000, "azimut": 0, "elevacion": 68},
    {"t": 5.5, "mira": "los-amates", "dist_km": 220, "azimut": -12, "elevacion": 38}
  ],
  "eventos": [
    {"t": 0.3, "dur": 4.6, "tipo": "ruptura", "pieza": "motagua", "desde": "los-amates", "km_oeste": 160, "km_este": 20, "sfx": "grave"},
    {"t": 13.5, "dur": 5.0, "tipo": "deslizar", "pieza": "motagua", "en": [-89.9, 14.95], "km": 90, "sentido": "izquierdo"},
    {"t": 24.0, "dur": 5.5, "tipo": "onda", "pieza": "motagua", "radio_km": 170},
    {"t": 25.0, "dur": 3.0, "tipo": "parpadear", "lugares": ["guatemala", "chimaltenango"]}
  ],
  "marcas": [
    {"t": 6.1, "hasta": 11.0, "lugar": "los-amates", "texto": "Los Amates, Izabal", "sub": "Epicentro"},
    {"t": 20.0, "hasta": 26.0, "lugar": "guatemala", "texto": "Ciudad de Guatemala", "sub": "A 25 km", "separada_de": "motagua"}
  ],
  "capa": {
    "titulares": [{"t": 0.0, "hasta": 5.2, "kicker": "4 DE FEBRERO DE 1976", "texto": "La madrugada del terremoto"}],
    "cifras": [{"t": 7.3, "hasta": 11.0, "valor": "7.5", "rotulo": "de magnitud", "fuente": "USGS"}],
    "palabras": [{"text": "A", "start": 0.12, "end": 0.20}],
    "progreso": {"actos": [0.0, 12.4, 33.0]},
    "seguir": {"t": 22.0, "dur": 3.0},
    "pie": "Relieve: Mapzen Terrain Tiles · Fallas: GEM (CC BY-SA 4.0) · Lugares: © OpenStreetMap",
    "handle": "@DerekUrizar",
    "cierre": {"t": 40.1, "frase": "…", "redes": [{"nombre": "TikTok", "handle": "@derekurizargt"}]}
  }
}
```

## Campos

- **`estilo`**: uno del catálogo `design/sets3d/estilos.json` (`id`, `motor: three|blender`, `cuando` usarlo, y para
  cada uno sus colores y medidas). three.js: `color`, `noche`, `contorno`, `voxel`, `plano`. Blender: `arquitecto`,
  `diorama`, `papel` (fondo claro y capa 2D en tinta; necesitan Blender instalado para `cuadro`, `render` y `pieza`, no
  para `check`).
- **`paleta`**: una de `design/tokens.json → noche.paletas`; de ahí salen el fondo, el texto crema y **el acento**.
- **`protagonista`**: el `id` de la pieza que va en el acento. **Es lo único que se pinta con el acento de la paleta**:
  una falla que no es la protagonista se enciende en crema (el color `secundario` del estilo), y la capa 2D nunca usa
  el acento (los pines, los titulares y la palabra que suena van en crema). Si falta, es la primera pieza `falla`
  (con aviso). Puede ser una falla, la frontera, una ruta o unas luces.
- **`mundo.set`**: una carpeta de `design/sets3d/<set>/` (geodatos ya bajados con `scripts/build_set3d.py`, con su
  fuente y licencia en `fuente.json`; el render no llama a la red). `exageracion` multiplica la altura del relieve
  (5 por defecto).
- **`mundo.lugares`**: puntos con `lon`, `lat` y `nombre`; los del set (`lugares.json`: las 22 cabeceras y los ≈ 300
  pueblos de OpenStreetMap, por id en minúsculas con guiones: `guatemala`, `los-amates`, `tecpan`…) se usan sin
  declararlos. Donde el contrato pide un lugar vale también `[lon, lat]`.
- **`mundo.piezas`**: lo que hay sobre el mundo. Ninguna pieza lleva texto ni cifras: eso va en la capa. Tipos v1:
  - `falla`: `trazos` (nombres del set, `fallas.json → nombres`) **o** `puntos: [[lon, lat], …]` (un trazo propio, p. ej.
    la traza publicada de una ruptura; se suaviza con una curva por los puntos, salvo `"suave": false`), o los dos. Se
    posa sobre el relieve. Los trazos se encadenan en una sola línea ordenada de oeste a este (o de sur a norte); el
    hueco entre dos trazos no se dibuja pero el frente de la ruptura lo cruza. Dormida es una línea tenue; un evento
    `ruptura` la enciende. **No es una grieta abierta ni un escalón:** es una línea encendida sobre el terreno, con su
    brillo en el suelo.
  - `luces`: un punto de luz por lugar; `lugares` es una lista o `"todos"` (los del set); `encendidas: false` las deja
    apagadas hasta un evento `encender`. El tamaño sale del `peso` del lugar.
  - `frontera`: el borde del país del set.
  - `ruta`: una línea de rayas entre `lugares` (≥ 2), posada sobre el relieve.
- **`camara`**: claves ordenadas por `t`, la primera en `t = 0`. Cada clave: `mira` (id de lugar o `[lon, lat]`),
  `dist_km` (del ojo al punto que mira; 15–1600), `azimut` (grados; 0 = el ojo al sur del punto, mirando al norte;
  positivo gira el ojo hacia el este), `elevacion` (grados sobre el horizonte; 8–89) y `fov` opcional (vertical, 50 por
  defecto; 20–75). El punto que mira está a la altura del relieve ahí (ya exagerada). Entre claves se interpola cada
  parámetro (también esa altura) con `e = -(cos(pi*u) - 1)/2`; antes de la primera y después de la última, la cámara
  queda en esa clave. La misma función vive en `video/maqueta/motor.js` y en `maqueta3d.py` (para proyectar pines y
  eventos en los gates). Una clave puede caer al final de una escena: solo cambia su `t`. Referencia: con `fov` 50, el
  país entero cabe en 9:16 desde `dist_km` ≈ 1000–1150 con `elevacion` ≈ 68; a 150–250 km se lee un valle.
- **`eventos`**: lo que pasa en el mundo, con `t` y `dur`. Un evento puede llevar `sfx` (id de
  `design/sfx/catalogo.json`): el motor no lo suena; `maqueta3d.py render` lo lista en `efectos.json` para la mezcla
  (también el `sfx` de un titular, una cifra, una marca, `seguir` o el `cierre`). **Un evento con `t ≤ 0.1` ya se ve en
  el cuadro 0**: el motor lo dibuja como si llevara un avance (ruptura ≈ 0.25 s: el destello de origen encendido y un
  primer tramo de línea; onda: el anillo ya abierto; deslizar y resaltar: ya a plena fuerza) y termina cuando dice el
  `maqueta.json`. Tipos v1:
  - `ruptura`: la falla `pieza` se enciende desde el punto del trazo más cercano a `desde`. O bien `hacia:
    este|oeste|norte|sur|ambos` con `km` (con `ambos`, `km` es el largo total: la mitad a cada lado), o bien
    **`km_oeste` y `km_este`** (o `km_norte` / `km_sur`): ruptura bilateral y asimétrica, **cada frente avanza a su
    ritmo y los dos llegan en `dur`**. Si el trazo es más corto que lo pedido, llega hasta el final del trazo y `check`
    lo avisa (no falla). Lo roto queda encendido hasta el final del video. Hasta 4 rupturas.
  - `onda`: un anillo de luz que crece hasta `radio_km` desde `centro` (un lugar) o desde una falla (`pieza`: el anillo
    sale de todo el trazo). Al pasar aviva las luces de los pueblos.
  - `deslizar`: flechas a los dos lados de la falla `pieza`, en sentidos opuestos: el corrimiento lateral. `en` (lugar;
    el centro del tramo; por defecto el medio del trazo), `km` (largo del tramo, 60) y **`sentido: "izquierdo"|"derecho"`**
    (por defecto `izquierdo`: el lado norte va al oeste y el sur al este). Opcionales: `periodo_km` (7) y `vel_km_s` (6)
    de las flechas.
  - `encender` / `apagar` / `parpadear`: luces de `lugares` (lista de lugares que estén en una pieza `luces`, o
    `"todos"`, que es el valor por defecto).
  - `resaltar`: un `lugar` (un núcleo brillante con halo y dos anillos que se abren, en crema y con tamaño en
    píxeles: se lee a tamaño de teléfono con el país entero en cuadro, mucho más fuerte que las luces de los pueblos)
    o una `pieza` (sube de brillo mientras dura; una falla todavía dormida engorda y aclara su línea).
- **`marcas`**: pines pegados al 3D: un punto en el ancla proyectada, una línea y una tarjeta con `texto` (y `sub`).
  Visibles de `t` a `hasta`. `alto` (px de la línea, 110) sirve para separar dos tarjetas que se pisan. La tarjeta no
  se sale de los márgenes y se desvanece sola antes de pisar el titular o la banda de abajo. **`separada_de`** (el id
  de una pieza `falla`, `ruta` o `frontera`): la marca dice que está LEJOS de esa pieza («A 25 km de la falla»), así que
  no puede dibujarse pegada a ella; con la cámara rasante las distancias se aplastan y M3D11 lo detiene.
- **`capa`**: el cuadro 2D, de la familia de `video/comun.css` (Noche: crema, Archivo condensado, JetBrains Mono).
  - `titulares`: `kicker` + `texto` (≤ 3 renglones), arriba a la izquierda bajo la barra, de `t` a `hasta`. Un titular
    con `t ≤ 0.1` está completo desde el cuadro 0 (sin animación de entrada); los demás entran animados.
  - `cifras`: `valor` grande + `rotulo` + `fuente` (se pinta «Fuente: …»), abajo a la izquierda sobre los subtítulos.
    Una a la vez.
  - `palabras`: la voz palabra por palabra (`text`, `start`, `end`), para los subtítulos (trozos de ≤ 26 caracteres,
    como `/video`).
  - `progreso.actos`: los segundos en que empieza cada acto (el primero, 0): un tramo de la barra por acto.
  - `seguir`: el botón «Sígueme» a mitad (`t`, `dur` ≥ 2 s). En 9:16 no puede coincidir con un titular largo.
    `seguir` y `cierre` son obligatorios para `check` y `render`, pero `cuadro` dibuja una maqueta sin ellos (los
    ganchos candidatos son maquetas de una sola escena).
  - `pie` (las fuentes de los geodatos, ≤ 132 caracteres; obligatorio: OpenStreetMap y las demás licencias piden
    atribución) y `handle`: fijos todo el video. `aviso` («Maqueta · no a escala») es **opcional** (usuario,
    2026-11-14: no hace falta en todos los videos): si falta no se dibuja y el `handle` ocupa su lugar.
  - `cierre`: desde `t` (≥ 3 s antes del final) un velo del fondo cubre el mundo (que sigue vivo debajo), la `frase` se
    enciende palabra por palabra (con la voz, si las últimas `palabras` son la frase; si no, a ritmo parejo) y entra
    «Sígueme en» con las `redes` (`nombre` en TikTok, Instagram, Facebook, YouTube o X para su icono, y `handle`).
    Titulares, cifras y marcas terminan antes; los subtítulos se apagan en el cierre (la pantalla ya dice la frase).

## Formatos y zonas

El mismo `maqueta.json` sale en 9:16 (1080×1920) y en 4:5 (1080×1350). La cámara es la misma (mismo `fov` vertical:
el 4:5 ve más a los lados) y la capa se recoloca. Las medidas viven en `ZONAS` de `maqueta3d.py` (de ahí salen las
variables CSS de la capa y lo que miden los gates).

**El 3D ocupa todo el lienzo**, de borde a borde: el relieve del set cubre mucho más que el país (de México a Honduras
y el fondo de los dos mares, que se insinúa), fuera de la caja sigue un plano de mar hondo y a lo lejos todo se funde
con el fondo. Encima va un degradado del color del fondo que crece hacia abajo (subtítulos, aviso y pie conservan
contraste y el terreno se sigue adivinando debajo) y uno más corto arriba, bajo la barra y el titular. **El punto que
mira la cámara no cae en el centro geométrico del lienzo sino en el centro de la zona libre** (`centro_y`: entre un
titular de dos renglones y la banda de abajo), con un desplazamiento de lente que no cambia el plano; lo aplican igual
el motor y la proyección de los gates.

| | 9:16 | 4:5 |
|---|---|---|
| Columna de texto (x) | 85–876 (iconos de la app desde x 900, y ≥ 1070) | 85–995 |
| Barra de progreso · titular | y 222 · y 256 | y 56 · y 86 |
| Zona libre para marcas | bajo el titular (o y 300) hasta y 1282 | bajo el titular (o y 120) hasta y 1008 |
| Cifra (termina en) · aviso y handle | y 1270 · y 1300 | y 1000 · y 1026 |
| Subtítulos · pie | y 1400 · y 1574 (antes del texto de la app, y 1645) | y 1100 · y 1284 |
| Donde cae el punto que mira la cámara (`centro_y`) | y 880 (el centro del lienzo es 960) | y 650 (675) |

## Gates M3D (`maqueta3d.py check`, en 9:16 y 4:5)

| Gate | Qué revisa |
|---|---|
| M3D1 | Forma y versión; `estilo` del catálogo (de motor three o blender); `set` y `paleta` existen |
| M3D2 | Piezas, trazos, lugares, `protagonista` y `sfx` referenciados existen; cada evento con sus campos |
| M3D3 | Cámara: claves crecientes desde `t = 0`, parámetros en rango, velocidad tope por tramo (paneo ≤ 0.85 del `dist_km` por segundo, giro ≤ 45°/s, cabeceo ≤ 30°/s, zoom ≤ ×3 por segundo; el pico de la curva es π/2 veces la media) y el ojo siempre por encima del relieve |
| M3D4 | Cada marca cae dentro del cuadro, con su tarjeta bajo el titular vivo y su ancla sobre la banda de abajo, ≥ 80 % de su ventana, y dura lo que se tarda en leer (0.5 s + 0.3 s por palabra, mínimo 1.2 s); ≤ 3 marcas a la vez; dos tarjetas no se pisan |
| M3D5 | Titulares y cifras: tiempo de lectura; dos titulares no se pisan; una cifra a la vez; la cifra no tapa una marca viva; nada sigue en pantalla cuando entra el cierre; `seguir` no cae sobre un titular |
| M3D6 | Cada evento cabe en la duración y su centro se ve en cámara ≥ 60 % de lo que dura (en una ruptura, sus frentes) |
| M3D7 | `pie`, `handle`, `seguir` y `cierre` presentes (`aviso` es opcional); el pie nombra las fuentes de las capas del set que se usan (`fuente.json → pie_claves`) |
| M3D8 | Un solo estilo (ningún `estilo` por toma, pieza o evento) |
| M3D9 | El gancho es un evento que se VE en el cuadro 0: hay una `ruptura`, `onda`, `deslizar` o `resaltar` con `t ≤ 0.1` y su origen cae dentro del cuadro en `t = 0` (aviso si ningún titular empieza en `t ≤ 0.1`: la portada saldría sin titular) |
| M3D10 | Todo lo anterior se cumple en los dos formatos (9:16 y 4:5 encuadran distinto) |
| M3D11 | Separación: una marca con `separada_de` guarda ≥ 60 px en pantalla entre su ancla y el punto más cercano de esa pieza en ≥ 80 % de su ventana (en 9:16 y 4:5, o en el lienzo de la pieza). La falla dice cuántos px hubo y propone una cámara más cenital o más cercana |

Cada falla dice el gate, el formato, la pieza y cómo arreglarlo. Los avisos (no fallan): una ruptura que pide más
kilómetros de los que tiene el trazo, un `desde` lejos del trazo, un video sin `protagonista`, una portada sin titular.

La concordancia con la voz (cada toma, evento, marca y cifra nace en una frase que la voz dice; cada lugar que la voz
nombra tiene su marca o es el foco; cada número con respaldo) la revisa `video3d.py guion --check`, que es quien
conoce el guion.

## Modo pieza: la maqueta dentro del cuadro de otro flujo

/historia, /serie y /youtube-long pueden alojar una maqueta en su propio cuadro: ellos ponen el titular, los
subtítulos, la barra y el cierre; **la maqueta solo pone el mundo y sus pines**.

- **Lienzo libre** (`--lienzo ANCHOxALTO`; lados pares de 320 a 3840 px): 950x1040 para la mesa vertical, 1120x1080 y
  1920x1080 para el 16:9. El punto que mira la cámara cae en el centro del lienzo; mismo `fov` vertical.
- **Se dibuja** el mundo, las piezas, los eventos y las `marcas`. De `capa` todo es opcional (y `capa` puede faltar
  entera): `titulares`, `cifras`, `palabras`, `progreso`, `seguir`, `cierre`, `handle`, `aviso` y `pie` se dibujan solo
  si vienen (`pie` y `aviso`, abajo y pequeños). Sin degradados para el texto: el mundo llena el lienzo y los cuatro
  bordes se funden con el fondo del anfitrión, que es el fondo de la paleta (`noche.paletas.<paleta>.fondo`).
- **Gates:** M3D1–M3D4, M3D6, M3D8 y M3D11. Las marcas guardan 40 px con los bordes del lienzo (sin bandas de titular
  ni de pie). M3D5, M3D7, M3D9 y M3D10 no aplican: el cuadro es del anfitrión. La atribución de los geodatos la pone
  el anfitrión si la maqueta no trae `pie`.
- **Salida:** `ARCHIVO.mp4` (H.264 yuv420p, sin audio, del tamaño del lienzo, `duracion_s` ± 1 cuadro, un solo
  proceso) y, junto a él, `ARCHIVO.efectos.json` (`[[t, id], …]` de los `sfx` de eventos y marcas),
  `ARCHIVO.render.log` y `ARCHIVO_proyecto/`. ≈ 1.8 s de render por segundo de video en 950x1040. Con un estilo de
  Blender la forma y las salidas son las mismas (más `ARCHIVO.blender.log`); tarda lo que dice «Motor Blender».

## Comandos (`scripts/maqueta3d.py`; 0 ok · 1 gate o paso fallido · 2 uso incorrecto)

| Comando | Qué hace |
|---|---|
| `check MAQUETA [--formato 9:16\|4:5\|ambos]` | Gates M3D1–M3D11 (sin navegador; décimas de segundo) |
| `check MAQUETA --pieza --lienzo ANCHOxALTO` | Los gates del modo pieza en ese lienzo |
| `cuadro MAQUETA --pieza --lienzo ANCHOxALTO --t S … --salida DIR [--hoja]` | Cuadros sueltos del modo pieza (`DIR/pieza_<lienzo>_tSSS.SSS.png`) |
| `pieza MAQUETA --lienzo ANCHOxALTO --salida ARCHIVO.mp4 [--borrador]` | El mp4 del modo pieza y su `ARCHIVO.efectos.json`; exige sus gates en 0 salvo `--borrador` |
| `cuadro MAQUETA --t S [--t S …] --salida DIR [--formato F] [--hoja]` | PNG de cuadros sueltos (`DIR/<9x16\|4x5>_tSSS.SSS.png`) y `hoja_<formato>.jpg`; ≈ 4–7 s en total (con un estilo de Blender, ≈ 4–5 s un cuadro y ≈ 9–11 s seis: la placa a resolución completa y con las muestras del render, más la capa 2D). No exige pasar los gates ni traer `seguir` y `cierre`: sirve para ver ganchos candidatos |
| `proyecto MAQUETA --dir DIR [--formato F]` | El proyecto de HyperFrames en `DIR/<9x16\|4x5>/proyecto/` (con un estilo de Blender, solo la capa 2D: la placa `assets/placa.mp4` la pone `render`) |
| `render MAQUETA --dir DIR [--formato F] [--borrador]` | Exige `check` en 0 (salvo `--borrador`: un candidato para mirar, nunca para entregar); `DIR/<9x16\|4x5>/video.mp4` (H.264 yuv420p, sin audio, `duracion_s` ± 1 cuadro; HyperFrames 0.9.28 con `--workers 1`) y `DIR/efectos.json` (`[[t, id], …]`); ≈ 1.8 s por segundo de video y formato con three.js; con un estilo de Blender, ver los tiempos de «Motor Blender» |
| `estilos` · `sets` | Los catálogos |
| `prueba [--dir DIR]` | Sobre `video/maqueta/fixture/maqueta.json`: check, negativos y positivos de gate (también el modo pieza en tres lienzos y los tres estilos de Blender), hoja y render en los dos formatos con three.js, y al final un caso corto del motor Blender (el fixture en `arquitecto`: check y un cuadro; se salta con un aviso si Blender no está) |
| `prueba --blender-render ESTILO [--formato F]` | Solo el render completo del fixture en un estilo de Blender (minutos) |

Los geodatos: `python3 scripts/build_set3d.py guatemala [--check] [--capa relieve|fallas|frontera|lugares]`
(descargas en caché en `sesiones/_descargas/sets3d/`).

## Cómo está hecho el motor (`video/maqueta/`)

- `maqueta3d.py` **resuelve** el `maqueta.json` (lugares → km, cadenas de falla, alturas, tiempos del cierre, colores
  del estilo y de la paleta, zona del formato) y se lo entrega al motor en `assets/datos.js`: la geometría vive en un
  solo sitio y el motor solo dibuja.
- `motor.js` (three.js 0.187, `design/vendor/`): relieve en malla + textura de normales con un shader que tiene una
  rama por estilo (`voxel` usa columnas), cintas con ancho en píxeles para falla, frontera, ruta y flechas, luces
  como puntos, y la cámara del contrato. `capa.js` + `capa.css`: la capa 2D. `plantilla.html`: la composición.
- Todo es función pura del tiempo que pide HyperFrames (evento `hf-seek`): sin reloj, sin azar, sin red. El mismo
  cuadro sale byte a byte igual en dos cargas distintas.
- Ningún color escrito en el motor ni en la capa: salen de `design/sets3d/estilos.json` (con `@acento`, `@texto`,
  `@fondo3`… de la paleta) y entran como uniformes y variables CSS.

## Motor Blender (`scripts/maqueta_blender.py` + `video/maqueta/placa.js`)

Los estilos `arquitecto`, `diorama` y `papel` no los dibuja three.js: **Blender renderiza la placa** (el mundo, sin
texto) y **la misma capa 2D de HyperFrames va encima**. El estilo decide el motor (`estilos.json → motor`); el
`maqueta.json`, los gates, los comandos y las salidas son los mismos.

```
maqueta.json ─► maqueta3d.py (resuelve: lugares → km, cadenas, cámara, colores)
   ├─► Blender -b --python scripts/maqueta_blender.py  ─► c_NNNNN.png ─► ffmpeg crf 8 ─► assets/placa.mp4
   └─► marcas proyectadas por cuadro (la misma cámara y proyección de los gates) ─► assets/datos.js → MAQUETA.anclas
proyecto de HyperFrames (plantilla.html con <video id="placa"> + capa.js + placa.js) ─► render --workers 1 ─► video.mp4
```

- **Qué necesita:** Blender ≥ 5.0 (probado con 5.3) en `/Applications/Blender.app`, en `$BLENDER` (la ruta del
  ejecutable) o como `blender` en el PATH. Corre sin ventana (`-b --factory-startup`); no usa el MCP de Blender ni la
  red. `check` no lo necesita; `cuadro`, `render` y `pieza` fallan con un mensaje claro si falta; `estilos` lo avisa.
- **Una sola geometría:** `maqueta_blender.py` importa de `maqueta3d.py` la resolución del `maqueta.json`, la función
  de cámara y la proyección. La cámara se pone **cuadro a cuadro** con `camara_en` (posición, mira, `fov`, el
  desplazamiento de lente de `centro_y`): no hay curvas de animación que Blender pueda volver a suavizar. Antes de
  renderizar compara su cámara con `proyector()` en cinco puntos y se detiene si difieren más de 1.5 px (da 0.00 px).
- **Modo placa de la capa:** `capa.js` es la misma; en lugar de la cámara de three.js recibe de `placa.js` la posición
  de cada marca **ya proyectada por cuadro** (`MAQUETA.anclas`, calculada en Python con la proyección de los gates), y
  el mundo es `#placa`: un `<video>` en el render o fotos apiladas en los cuadros sueltos. El cuadro `n` de la placa
  está en `t = n / fps`.
- **Capa en tinta:** los tres estilos son de fondo claro, así que su bloque `capa` invierte los papeles: `ink` oscuro
  (titulares, cifras, subtítulos, pie, barra), `sombra` y el velo del cierre del color claro del estilo, `tinta` crema
  (el texto sobre lo que va en tinta: la palabra que suena, el botón). El acento sigue siendo solo del protagonista.
- **Mismo cuadro, no mismos bytes:** en la prueba anterior de estos estilos (`sesiones/_video3d/antigua/estilos/
  blender/NOTAS.md`) dos renders del mismo cuadro diferían en ±1 nivel en algunos píxeles (el denoise de Cycles y la
  oclusión en pantalla de Eevee). Con este motor **no se volvió a medir**; por eso ninguna prueba compara hashes de la
  placa.
- **Placa y capa en el mismo cuadro (medido):** en el render de prueba, el cuadro N del mp4 final se parece al cuadro N
  de la placa (PSNR ≈ 42 dB en una franja sin texto) y no a sus vecinos (23–26 dB en N ± 1), en los cuadros 30, 135 y
  150, con la cámara en movimiento.

### Los tres estilos (qué se decidió)

| | `arquitecto` | `diorama` | `papel` |
|---|---|---|---|
| Motor | Cycles en GPU (Metal), 16 muestras + OpenImageDenoise | Eevee, 32 muestras, foco con jitter | Eevee, 24 muestras, oclusión en pantalla |
| Relieve (`blender.relieve`) | `liso`: malla 720×675 con sombreado suave; **el mar, un escalón de 2.5 km por debajo** de la costa (la costa se lee por su sombra) | `base`: **la caja del país** (`fuente.json → caja`) más 30 km, **recortada en una base de 55 km de canto** en tres estratos, sobre un piso de estudio claro; el mar es resina (brilla) | `capas`: el relieve suavizado y **partido en cartulinas cada 600 m** (3 km de maqueta con exageración 5; el mar baja en 3 capas cada 1,500 m); el corte de cada capa ocupa ≈ 3 celdas |
| Color | Todo blanco mate cálido; fuera del país y el mar, un tono más gris. **Solo el protagonista en el acento** (con luz propia: se lee igual a la sombra) | Tinta por altura de maqueta escolar (verde, paja, café); fuera del país, sin pintar | Cartulinas apagadas por nivel (salvia, paja, terracota), fuera del país crema; **canto claro** en cada corte y grano de papel |
| Luz | Sol bajo (36°) de penumbra ancha + cielo parejo, un rebote: oclusión y sombras del trazado de rayos | Luz de estudio suave; **foco en lo que mira la cámara** y apertura calculada por cuadro para ≈ 44 px de desenfoque en el infinito | Sol bajo (34°) y duro + oclusión del material: sombra de contacto en cada capa |
| Pueblos (`luces`) | Bloques blancos, como edificios de maqueta | Bloques crema con algo de luz propia | Cuadritos de cartulina |
| Líneas | Tubos finos | Tubos finos | Cintas planas (tiras de papel) |

### Lo que se ve distinto frente a three.js

- **Líneas con grosor en kilómetros, no en píxeles.** El ancho de falla, frontera, ruta y flechas se calcula en cada
  cuadro para que mida los píxeles del estilo **a la distancia del punto que mira la cámara**; con la cámara rasante,
  lo lejano se ve más fino. Son mallas con sombra: una montaña delante puede tapar un tramo (three dibuja la falla
  encendida siempre encima).
- **`ruptura`**: la línea encendida es un tubo (o una cinta) del acento que crece desde el origen, cada frente a su
  ritmo, con una bolita en cada frente. No hay halo ni «recién roto más caliente»; en `arquitecto` la luz propia del
  tubo tiñe apenas el blanco de alrededor, en `diorama` y `papel` no alumbra el suelo.
- **`onda`**: un anillo **pintado** sobre el relieve (mezcla hacia el color `onda` del estilo) que crece; no suma luz.
  Al pasar, los bloques de los pueblos crecen un momento.
- **`encender` / `apagar` / `parpadear`**: los pueblos son bloques, no puntos de luz: apagado es un bloque bajo y del
  color `luces_apagadas`; encendido, alto y claro; parpadear alterna entre los dos.
- **`deslizar`**: puntas de flecha en relieve a los dos lados de la falla, en sentidos opuestos (mismo `sentido`,
  `periodo_km` y `vel_km_s`).
- **`resaltar`**: un lugar es un núcleo y dos anillos **planos** que se abren (en el color `resalte`: oscuro sobre
  blanco y papel, blanco en el diorama); una pieza engorda mientras dura.
- **Sin niebla ni fondo que se funde:** el mundo termina en la mesa (`arquitecto`, `papel`: la orilla de la caja se
  funde en `borde_km` con el color de la mesa) o en el canto de la base (`diorama`).
- **`diorama`: la base es la caja del país.** Un lugar o una marca fuera de ella (un pueblo de Honduras lejos de la
  frontera) cae sobre el piso del estudio; con el país entero en 9:16 los cantos de los lados quedan fuera de cuadro
  (se ven el de arriba y el de abajo; en 4:5 y en lienzos anchos se ve la base entera).
- **`papel`: las alturas van por escalones.** La superficie queda hasta 1.5 km (de maqueta) por encima o por debajo de
  la altura real, y las marcas se proyectan con la altura real: el ancla puede quedar unos píxeles fuera del suelo en
  un plano muy cercano. Las piezas sí se posan en la superficie visible. **En planos cercanos (≈ 250 km o menos) el
  corte de las capas sale dentado**: la malla es la rejilla del relieve (celdas de 0.7 km) y no da para un canto limpio.
- **Color (sin comprobar):** la prueba anterior midió que la cadena placa → HyperFrames → mp4 oscurecía ≈ 1.5 %. Aquí
  la placa se codifica con matriz y etiquetas BT.709 para evitarlo, pero **el color final no se cotejó contra los PNG**.
- **Sin probar:** la ruta sin Blender instalado (el mensaje de `cuadro`/`render` y el salto de `prueba`), un render
  completo en 4:5, un render completo de `arquitecto` o `diorama` en 9:16 (solo cuadros sueltos y, de `arquitecto`, un
  clip de 4 s en modo pieza), `prueba --blender-render`, otras paletas que `obsidiana`, la frontera o las luces como
  protagonista, dos fallas a la vez y `encendidas: false`.

### Tiempos (M4 Max, 1080×1920; medidos el 2026-11-14)

| | `arquitecto` | `diorama` | `papel` |
|---|---|---|---|
| Armar la escena | 0.4 s | 0.4 s | 0.8 s |
| Primer cuadro (carga de la GPU) | ≈ 4 s | ≈ 1.7 s | ≈ 1.3 s |
| Placa, por cuadro (en tres corridas) | 0.74–0.84 s | 0.49–0.55 s | 0.65–0.77 s |
| `cuadro` de punta a punta, 1 cuadro con su capa 2D | 5.0 s | 4.3 s | 4.7 s |
| `cuadro` de punta a punta, 6 cuadros | 11.3 s | 8.7 s | 9.8 s |
| Video de 45 s en un formato (estimado: 1,350 cuadros de placa + capa 2D) | ≈ 22 min | ≈ 16 min | ≈ 20 min |

Las cifras por cuadro salen de corridas de 45, 150 y 390 cuadros con otros agentes usando la misma GPU: son un rango,
no una medida limpia. El único render completo: 13 s del piloto en `papel`, 9:16, con su capa (390 cuadros) = 381 s: la placa 310 s (0.79 s por
cuadro, con otro render corriendo en la máquina) y la capa 2D 71 s (HyperFrames extrae los cuadros del `<video>` en
PNG: ≈ 5 s por segundo de video, contra ≈ 1.8 de three.js). Un clip de 4 s en modo pieza (950x1040, `arquitecto`):
61 s (0.43 s por cuadro de placa + 9 s de capa). Frente a three.js (≈ 1.8 s por segundo de video) el motor Blender
cuesta **≈ 12–16 veces más**: un video de 45 s en los dos formatos son ≈ 30–45 min.

- **La primera vez que Cycles corre en una máquina compila los kernels de Metal: ≈ 3.5 min** con Blender al 0 % de
  CPU (parece colgado; no lo es). Queda en caché: después arranca en segundos. Solo afecta a `arquitecto`. (Dato de la
  prueba anterior; en esta máquina los kernels ya estaban compilados y no se volvió a ver.)
- `MAQUETA_BLENDER_PROCESOS=N` (1–4) reparte la placa en N procesos de Blender a la vez (cada cuadro es independiente).
  Medido con 150 cuadros: en Eevee gana poco (`diorama` 0.55 → 0.42 → 0.40 s por cuadro con 1, 2 y 3 procesos;
  `papel` 0.73 → 0.62 → 0.61) y **en Cycles empeora** (`arquitecto` 0.74 → 0.92 → 1.19: la GPU ya está llena). Por
  defecto, 1.
- Los PNG de la placa (≈ 3–4 MB por cuadro) viven en `…/proyecto/_placa/` solo durante el render y se borran al armar
  `assets/placa.mp4`. El registro de Blender queda junto al de HyperFrames (`blender.log`, `ARCHIVO.blender.log`).
- `prueba` corre al final un caso corto de este motor (el fixture en `arquitecto`: `check` y un cuadro) y lo salta con
  un aviso si Blender no está. El render completo no entra (minutos): `python3 scripts/maqueta3d.py prueba
  --blender-render arquitecto|diorama|papel [--formato 9:16]`.
