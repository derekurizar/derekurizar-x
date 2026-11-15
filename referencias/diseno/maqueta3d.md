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
píxeles), saca cuadros sueltos y lo renderiza.

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
    {"t": 6.1, "hasta": 11.0, "lugar": "los-amates", "texto": "Los Amates, Izabal", "sub": "Epicentro"}
  ],
  "capa": {
    "titulares": [{"t": 0.0, "hasta": 5.2, "kicker": "4 DE FEBRERO DE 1976", "texto": "La madrugada del terremoto"}],
    "cifras": [{"t": 7.3, "hasta": 11.0, "valor": "7.5", "rotulo": "de magnitud", "fuente": "USGS"}],
    "palabras": [{"text": "A", "start": 0.12, "end": 0.20}],
    "progreso": {"actos": [0.0, 12.4, 33.0]},
    "seguir": {"t": 22.0, "dur": 3.0},
    "aviso": "Maqueta · no a escala",
    "pie": "Relieve: Mapzen Terrain Tiles · Fallas: GEM (CC BY-SA 4.0) · Lugares: © OpenStreetMap",
    "handle": "@DerekUrizar",
    "cierre": {"t": 40.1, "frase": "…", "redes": [{"nombre": "TikTok", "handle": "@derekurizargt"}]}
  }
}
```

## Campos

- **`estilo`**: uno del catálogo `design/sets3d/estilos.json` (`id`, `motor: three|blender`, `cuando` usarlo, y para
  los de three sus colores y medidas). three.js: `color`, `noche`, `contorno`, `voxel`, `plano`. Blender:
  `arquitecto`, `diorama`, `papel` (`check` los rechaza con «motor blender: aún no disponible»).
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
  se sale de los márgenes y se desvanece sola antes de pisar el titular o la banda de abajo.
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
  - `aviso`, `pie` (las fuentes de los geodatos, ≤ 132 caracteres) y `handle`: fijos todo el video.
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
| M3D1 | Forma y versión; `estilo` del catálogo y con motor disponible; `set` y `paleta` existen |
| M3D2 | Piezas, trazos, lugares, `protagonista` y `sfx` referenciados existen; cada evento con sus campos |
| M3D3 | Cámara: claves crecientes desde `t = 0`, parámetros en rango, velocidad tope por tramo (paneo ≤ 0.85 del `dist_km` por segundo, giro ≤ 45°/s, cabeceo ≤ 30°/s, zoom ≤ ×3 por segundo; el pico de la curva es π/2 veces la media) y el ojo siempre por encima del relieve |
| M3D4 | Cada marca cae dentro del cuadro, con su tarjeta bajo el titular vivo y su ancla sobre la banda de abajo, ≥ 80 % de su ventana, y dura lo que se tarda en leer (0.5 s + 0.3 s por palabra, mínimo 1.2 s); ≤ 3 marcas a la vez; dos tarjetas no se pisan |
| M3D5 | Titulares y cifras: tiempo de lectura; dos titulares no se pisan; una cifra a la vez; la cifra no tapa una marca viva; nada sigue en pantalla cuando entra el cierre; `seguir` no cae sobre un titular |
| M3D6 | Cada evento cabe en la duración y su centro se ve en cámara ≥ 60 % de lo que dura (en una ruptura, sus frentes) |
| M3D7 | `aviso`, `pie`, `handle`, `seguir` y `cierre` presentes; el pie nombra las fuentes de las capas del set que se usan (`fuente.json → pie_claves`) |
| M3D8 | Un solo estilo (ningún `estilo` por toma, pieza o evento) |
| M3D9 | El gancho es un evento que se VE en el cuadro 0: hay una `ruptura`, `onda`, `deslizar` o `resaltar` con `t ≤ 0.1` y su origen cae dentro del cuadro en `t = 0` (aviso si ningún titular empieza en `t ≤ 0.1`: la portada saldría sin titular) |
| M3D10 | Todo lo anterior se cumple en los dos formatos (9:16 y 4:5 encuadran distinto) |

Cada falla dice el gate, el formato, la pieza y cómo arreglarlo. Los avisos (no fallan): una ruptura que pide más
kilómetros de los que tiene el trazo, un `desde` lejos del trazo, un video sin `protagonista`, una portada sin titular.

La concordancia con la voz (cada toma, evento, marca y cifra nace en una frase que la voz dice; cada lugar que la voz
nombra tiene su marca o es el foco; cada número con respaldo) la revisa `video3d.py guion --check`, que es quien
conoce el guion.

## Comandos (`scripts/maqueta3d.py`; 0 ok · 1 gate o paso fallido · 2 uso incorrecto)

| Comando | Qué hace |
|---|---|
| `check MAQUETA [--formato 9:16\|4:5\|ambos]` | Gates M3D1–M3D10 (sin navegador; décimas de segundo) |
| `cuadro MAQUETA --t S [--t S …] --salida DIR [--formato F] [--hoja]` | PNG de cuadros sueltos (`DIR/<9x16\|4x5>_tSSS.SSS.png`) y `hoja_<formato>.jpg`; ≈ 4–7 s en total. No exige pasar los gates ni traer `seguir` y `cierre`: sirve para ver ganchos candidatos |
| `proyecto MAQUETA --dir DIR [--formato F]` | El proyecto de HyperFrames en `DIR/<9x16\|4x5>/proyecto/` |
| `render MAQUETA --dir DIR [--formato F]` | Exige `check` en 0; `DIR/<9x16\|4x5>/video.mp4` (H.264 yuv420p, sin audio, `duracion_s` ± 1 cuadro; HyperFrames 0.9.28 con `--workers 1`) y `DIR/efectos.json` (`[[t, id], …]`); ≈ 1.8 s por segundo de video y formato |
| `estilos` · `sets` | Los catálogos |
| `prueba [--dir DIR]` | Sobre `video/maqueta/fixture/maqueta.json`: check, negativos de gate, hoja y render en los dos formatos |

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
