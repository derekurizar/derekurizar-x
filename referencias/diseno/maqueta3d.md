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
  "anotaciones": [
    {"t": 8.0, "hasta": 11.0, "tipo": "pulso", "sobre": ["guatemala"], "radio_m": 20000}
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
- **`mundo.escala`**: `pais` (por defecto: el relieve de un territorio, en km), `ciudad` (un lugar real de pocos km,
  en metros) o `esquema` (un lugar genérico hecho por una receta, en metros). Lo que cambia con la escala, la unidad de la
  cámara y lo que se puede dibujar en cada una: § «Mundos: pais, ciudad y esquema».
- **`mundo.set`** (pais y ciudad): una carpeta de `design/sets3d/<set>/` de esa escala (geodatos ya bajados con
  `scripts/build_set3d.py`, con su fuente y licencia en `fuente.json`; el render no llama a la red). `exageracion`
  multiplica la altura del relieve (5 por defecto en pais; 1.5 en ciudad, donde los edificios guardan su altura real).
- **`mundo.lugares`**: puntos con `lon`, `lat` y `nombre`; los del set (`lugares.json`: las 22 cabeceras y los ≈ 300
  pueblos de OpenStreetMap, por id en minúsculas con guiones: `guatemala`, `los-amates`, `tecpan`…) se usan sin
  declararlos. Donde el contrato pide un lugar vale también `[lon, lat]`.
- **`mundo.capas`**: las capas del dibujo del terreno que se pueden apagar: `curvas` (curvas de nivel), `batimetria`
  (líneas del fondo del mar) y `reticula` (paralelos y meridianos cada medio grado); todas encendidas por defecto, una
  clave desconocida falla M3D1. Hoy las dibuja el estilo `plano` (motor three.js). **Con `plano` se pregunta siempre al
  usuario si quiere todas las capas o una versión limpia** (usuario, 2026-11-15: en la frontera recta con México las
  curvas de la sierra de Chiapas ensuciaban el cuadro; quedó `{"curvas": false, "batimetria": false}`).
- **`mundo.piezas`**: lo que hay sobre el mundo. Ninguna pieza lleva texto ni cifras: eso va en la capa. **Los tipos, sus
  parámetros (con tipo, rango y defecto), las escalas y los motores que los dibujan están en el catálogo**
  (`design/sets3d/vocabulario.json`; legible: `python3 scripts/maqueta3d.py catalogo`); un tipo que no está ahí es FALLA
  M3D2. Notas de los tipos de hoy:
  - `falla`: `trazos` (nombres del set, `fallas.json → nombres`) **o** `puntos: [[lon, lat], …]` (un trazo propio, p. ej.
    la traza publicada de una ruptura; se suaviza con una curva por los puntos, salvo `"suave": false`), o los dos. Se
    posa sobre el relieve. Los trazos se encadenan en una sola línea ordenada de oeste a este (o de sur a norte); el
    hueco entre dos trazos no se dibuja pero el frente de la ruptura lo cruza. Dormida es una línea tenue; un evento
    `ruptura` la enciende. **No es una grieta abierta ni un escalón:** es una línea encendida sobre el terreno, con su
    brillo en el suelo.
  - `luces`: un punto de luz por lugar; `lugares` es una lista o `"todos"` (los del set); `encendidas: false` las deja
    apagadas hasta un evento `encender`. El tamaño sale del `peso` del lugar.
  - `frontera`: el borde del país del set. Con **`vecinos: true`** dibuja también, más finos y tenues, los bordes y la
    costa de los países de alrededor (México, Belice, Honduras, El Salvador y Nicaragua en el set `guatemala`; salen de
    Natural Earth con `build_set3d.py <set> --capa frontera` y quedan en `frontera.json → vecinos`), para que se entienda
    dónde queda cada cosa. Los dos motores los dibujan; nunca van en el acento.
  - `ruta`: una línea de rayas entre `lugares` (≥ 2), posada sobre el relieve.
- **`camara`**: claves ordenadas por `t`, la primera en `t = 0`. Cada clave: `mira` (id de lugar o `[lon, lat]`; en un
  esquema, `[x, y]` en metros; o algo que se MUEVE: `{"actor": id}` o un vehículo de un flujo `{"flujo": id, "n": k}` /
  `{"flujo": id, "carril": 2, "cerca": lugar, "t": s}`, con `desfase_m` (metros por delante, o `[adelante, izquierda]`): la
  cámara lo sigue, § «La cámara que sigue»), `cenital: true` (atajo de `elevacion: 89`), `dist_km` (del ojo al punto que mira; 15–1600) en un mundo `pais`, o **`dist_m`** en
  `ciudad` (40–9000 m) y `esquema` (15–5000 m): la unidad y el rango los fija la ficha del mundo (`camara`) y M3D3 los
  revisa, `azimut` (grados; 0 = el ojo al sur del punto, mirando al norte;
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
  `maqueta.json`. Cuánto avance lleva cada tipo lo dice su ficha (`adelanto`). Los tipos y sus parámetros: el catálogo
  (`maqueta3d.py catalogo`). Notas de los de hoy:
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
  de una pieza que sea una línea: hoy `falla`, `ruta` o `frontera`, las que traen `tramos` en sus reglas): la marca dice que está LEJOS de esa pieza («A 25 km de la falla»), así que
  no puede dibujarse pegada a ella; con la cámara rasante las distancias se aplastan y M3D11 lo detiene.
- **`anotaciones`**: la capa 2D ATADA AL 3D (clase `anotacion` del catálogo: `pulso`, `medida`, `etiqueta`, `reloj`), cada
  una con `tipo`, `t`, `hasta` y sus parámetros; sus anclas son lugares o algo que se mueve (§ «Anotaciones»). Opcional.
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
| M3D1 | Forma y versión; `estilo` del catálogo (de motor three o blender); `set` y `paleta` existen; el `set` es de la escala del mundo |
| M3D2 | Piezas, trazos, lugares, `protagonista` y `sfx` referenciados existen; cada evento con sus campos; el mundo, cada pieza y cada evento están en el catálogo, su motor dibuja el estilo y **su ficha incluye la escala del mundo** |
| M3D3 | Cámara: claves crecientes desde `t = 0`, la distancia en la unidad de la escala (`dist_km` en pais, `dist_m` en ciudad y esquema) y en su rango, parámetros en rango, velocidad tope por tramo (paneo ≤ 0.85 de la distancia por segundo, giro ≤ 45°/s, cabeceo ≤ 30°/s, zoom ≤ ×3 por segundo; el pico de la curva es π/2 veces la media) y el ojo siempre por encima del suelo (más el despeje de su escala: 1.5 km, 6 m, 4 m) |
| M3D4 (anotaciones) | Cada anotación cabe en el video, lo que dice se alcanza a leer (sus reglas → `textos`) y, si está atada al 3D (reglas → `anclas`), al menos la mitad de sus anclas está en cuadro ≥ 80 % de su ventana; ninguna sigue en pantalla cuando entra el cierre (M3D5) |
| M3D4 | Cada marca cae dentro del cuadro, con su tarjeta bajo el titular vivo y su ancla sobre la banda de abajo, ≥ 80 % de su ventana, y dura lo que se tarda en leer (0.5 s + 0.3 s por palabra, mínimo 1.2 s); ≤ 3 marcas a la vez; dos tarjetas no se pisan |
| M3D5 | Titulares y cifras: tiempo de lectura; dos titulares no se pisan; una cifra a la vez; la cifra no tapa una marca viva; nada sigue en pantalla cuando entra el cierre; `seguir` no cae sobre un titular |
| M3D6 | Cada evento cabe en la duración y su centro se ve en cámara ≥ 60 % de lo que dura (en una ruptura, sus frentes) |
| M3D7 | `pie`, `handle`, `seguir` y `cierre` presentes (`aviso` es opcional); el pie nombra las fuentes de las capas del set que se usan (`fuente.json → pie_claves`): las del mundo (`capas` de su ficha: el relieve), las de las piezas (`capas` de su ficha o un parámetro con `capa`) y los lugares si hay marcas. Un set de ciudad pide «Mapzen» y «OpenStreetMap» |
| M3D8 | Un solo estilo (ningún `estilo` por toma, pieza o evento) |
| M3D9 | El gancho es un evento que se VE en el cuadro 0: hay un evento visible en la portada (los que traen `adelanto` en su ficha: hoy `ruptura`, `onda`, `deslizar`, `resaltar`) con `t ≤ 0.1` y su origen cae dentro del cuadro en `t = 0` (aviso si ningún titular empieza en `t ≤ 0.1`: la portada saldría sin titular) |
| M3D10 | Todo lo anterior se cumple en los dos formatos (9:16 y 4:5 encuadran distinto) |
| M3D12 | Un `esquema` no se lee como un lugar real: lleva `capa.aviso` con «Esquema» (en modo pieza sin capa lo pone la mesa que lo aloja: aviso), y ni sus lugares (id y nombre, los de la receta y los de `mundo.lugares`) ni el texto de sus marcas llevan el nombre de un lugar real de `design/sets3d/guatemala/lugares.json` |
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
| `render MAQUETA --dir DIR [--formato F] [--borrador]` | Exige `check` en 0 (salvo `--borrador`: un candidato para mirar, nunca para entregar); `DIR/<9x16\|4x5>/video.mp4` (H.264 yuv420p, sin audio, `duracion_s` ± 1 cuadro; HyperFrames (versión en `scripts/versiones.py`) con `--workers 1`) y `DIR/efectos.json` (`[[t, id], …]`); ≈ 1.8 s por segundo de video y formato con three.js; con un estilo de Blender, ver los tiempos de «Motor Blender» |
| `estilos` · `sets` | Los catálogos |
| `catalogo [--para sesion\|realizador\|critico] [--escala E] [--motor M]` | El vocabulario legible (≤ 1 página por escala): cada pieza, evento, objeto o mundo con para qué sirve, sus parámetros y un ejemplo. Lo imprimen `video3d.py digesto` y el digesto del plano de la mesa |
| `catalogo --registrar` · `catalogo --check` | Revisa las fichas y sus módulos y escribe `design/sets3d/vocabulario.json` (su único escritor); `--check` falla si el catálogo no está al día |
| `prueba [--dir DIR]` | Sobre `video/maqueta/fixture/maqueta.json`: check, negativos y positivos de gate (también el modo pieza en tres lienzos y los tres estilos de Blender), hoja y render en los dos formatos con three.js, y al final un caso corto del motor Blender (el fixture en `arquitecto`: check y un cuadro; se salta con un aviso si Blender no está) |
| `prueba --blender-render ESTILO [--formato F]` | Solo el render completo del fixture en un estilo de Blender (minutos) |

Los geodatos: `python3 scripts/build_set3d.py guatemala [--check] [--capa relieve|fallas|frontera|lugares]`
(descargas en caché en `sesiones/_descargas/sets3d/`).

## Cómo está hecho el motor (`video/maqueta/`)

- `maqueta3d.py` **resuelve** el `maqueta.json` (lugares → km, cadenas de falla, alturas, tiempos del cierre, colores
  del estilo y de la paleta, zona del formato) y se lo entrega al motor en `assets/datos.js`: la geometría vive en un
  solo sitio y el motor solo dibuja.
- `motor.js` (three.js 0.187, `design/vendor/`) es el NÚCLEO: el fondo y el plano exterior, las cintas con ancho en
  píxeles, las superficies de mundo (`malla`, `tonos`, `sombra`), la cámara del contrato y el registro del vocabulario.
  **No sabe de relieves**: el suelo es un MUNDO (`mundos/<escala>.js`; el relieve nacional con su shader de una rama por
  estilo y las columnas de `voxel` es `mundos/pais.js`, movido sin cambiar un píxel). Las piezas y los eventos son
  **módulos** (`piezas/`, `eventos/`, `objetos/`, `anotaciones/`) que se registran solos; el proyecto copia solo los que usa la maqueta
  (`assets/modulos/`) y la plantilla los carga antes del núcleo. `capa.js` + `capa.css`: la capa 2D. `plantilla.html`:
  la composición.
- Todo es función pura del tiempo que pide HyperFrames (evento `hf-seek`): sin reloj, sin azar, sin red. El mismo
  cuadro sale byte a byte igual en dos cargas distintas.
- Ningún color escrito en el motor ni en la capa: salen de `design/sets3d/estilos.json` (con `@acento`, `@texto`,
  `@fondo3`… de la paleta) y entran como uniformes y variables CSS.

## Añadir vocabulario

El vocabulario (lo que la maqueta sabe dibujar) es un **catálogo de módulos**, como la biblioteca de animaciones de la
escena `explica`: el motor, los gates y la orquestación leen el mismo catálogo y nadie mantiene listas a mano.

**Una entrada son hasta tres archivos con el mismo nombre (`<tipo>`, minúsculas, sin tildes ni guiones):**

| Archivo | Qué es |
|---|---|
| `video/maqueta/<clase>/<tipo>.js` | El MÓDULO de motor.js (`<clase>`: `piezas`, `eventos`, `objetos`, `anotaciones`, `mundos`; las anotaciones las corre capa.js) |
| `video/maqueta/<clase>/<tipo>.json` | La FICHA: lo que el catálogo, el validador y la orquestación saben del tipo |
| `scripts/maqueta_tipos/<tipo>.py` | Opcional: las REGLAS que no caben en la ficha (resolver, topes, dónde pasa para los gates) |

**El módulo** se registra solo (es un script clásico; la plantilla lo carga antes de `motor.js`) y no importa nada:
todo le llega en `ctx`.

```js
(function (MAQ) {
  MAQ.EVENTOS.onda = {                 // MAQ.PIEZAS · MAQ.EVENTOS · MAQ.OBJETOS · MAQ.MUNDOS
    orden: 60,                         // orden de armado (los de hoy: 10–72); empate: piezas antes que eventos, luego por tipo
    armar(ctx, lista) { return estado; },          // una vez: `lista` = las piezas (o eventos) de este tipo, en orden
    inicio(t, estado, ctx) {},                     // cada cuadro, antes de los eventos (deja el estado en reposo)
    aplicar(t, e, ctx, estado) {},                 // SOLO eventos: cada evento, en el orden del maqueta.json
    en(t, estado, ctx) {},                         // cada cuadro, después de todos los eventos
  };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
```

Todo es opcional salvo `aplicar` en un evento. Un cuadro es: cámara → `inicio` de todos → `aplicar` de cada evento →
`en` de todos → render → capa 2D. **Seek puro**: lo que se ve en `t` se calcula de `t` (nada de acumular entre cuadros,
ni `Math.random`, ni reloj: `ctx.hash(i, k)` da el azar fijo). Sin colores escritos (`ctx.COL` y `ctx.lin`), sin red.

`ctx` (lo que comparte el núcleo): `THREE`, `M` (el maqueta.json resuelto), `W`, `H`, `COL`, `CFG` (el estilo),
`ES` (`aditivo`, `cubos`), `EXAG`, `scene`, `renderer`, `camera`, `lin`, `clamp`, `suave`, `hash`; el MUNDO (§ «Mundos»):
`escala`, `unidad_m`, `metros(v)`, `caja`, `altura(x, y)`, `V3(x, y, lev)`, `geo(lon, lat)` (= `km`), `caminos`,
`camino(nombre)`, `enCamino(nombre, s)`, `lugares`, `puntoEnS`, `distCadena`, `proyectar(x, y, z)`; superficies de mundo:
`malla` (`nueva`, `banda`, `poligono`, `geometria`, `material`, `poner`), `tonos`, `sombra(nx, ny, nz)`; líneas:
`cinta(pts, color, ancho_px, alfa, orden, {raya, oculta})`, `pegar(polilínea, paso_km, lev)`, `geoCinta`, `VERT_CINTA`,
`linea(id, cinta)` (una línea que «resaltar» aviva por el id de su pieza); la superficie (el shader del relieve):
`superficie` (sus uniformes: `uCad`, `cPieza`, `uBrillo`, `uOnda`…), `uRuptura`, `uComun()`, `GLSL_COMUN`,
`GLSL_RUPTURA`, `NR`, `NC`, `NO`; lo que publican otros módulos: `fallas`, `idxFalla(id)`, `fallas3d`, `luces`; y
lo que se mueve (Fase 2): `tray` (evaluar una trayectoria T/S suavizada: `tray.nueva(T, S)`, `tray.suave(r, h, t)` → [s, v]),
`moviles` (id → (t, n) → {x, y, dx, dy, v, vis}: lo registran actor y flujo), `ancla(A, t)` (un ancla resuelta → dónde está),
`flota(tipo, n, {tamano, lev, luces, color, orden})` (n objetos de un tipo en una malla instanciada: `poner(i, x, y, dx, dy, k,
freno)` y `listo()`), `tonos.bien|medio|mal` y `tonos.vehiculos`;
`cuadro` = `{t, k, pxKm, dist, dist_km, brillo, elementos, ondas, rupturas}` (lo de este cuadro: `brillo[id]` y
`elementos[id] = [{i, k}]` los pone `resaltar`, `ondas` las pone `onda`). Lo propio del relieve nacional (`superficie`,
`uRuptura`, `GLSL_RUPTURA`, `NR`, `NC`, `NO`) lo publica el mundo `pais`: una pieza que lo usa es de escala pais.

**La ficha** (`<tipo>.json`):

```json
{"tipo": "onda", "clase": "evento",
 "cuando": "la sacudida que se propaga: un anillo que crece desde un lugar o desde toda una falla",
 "parametros": {
   "radio_km": {"tipo": "numero", "requerido": true, "rango": [1, 3000], "descripcion": "hasta dónde llega el anillo"},
   "centro": {"tipo": "lugar", "requerido": false, "descripcion": "de dónde sale (o `pieza`)"},
   "pieza": {"tipo": "pieza", "piezas": ["falla"], "requerido": false, "descripcion": "la falla de la que sale (o `centro`)"}},
 "escalas": ["pais"], "motores": ["three", "blender"], "adelanto": {"dur": 0.08},
 "ejemplo": {"t": 6.4, "dur": 2.8, "tipo": "onda", "pieza": "motagua", "radio_km": 140}}
```

- `clase`: `pieza` · `evento` · `objeto` · `mundo`. `cuando`: una línea, para qué historia sirve (es lo que lee quien elige).
- `parametros` (sin los comunes: `id`, `tipo` en una pieza; `tipo`, `t`, `dur`, `sfx` en un evento): cada uno con
  `tipo` (`numero`, `entero`, `texto`, `bool`, `lugar` (id o `[lon, lat]`), `lugares` (lista; con `"todos": true` vale
  también `"todos"`), `pieza` (id de una pieza; `piezas` restringe su tipo), `puntos` (`[[lon, lat], …]`), `lista`
  (de textos)), `requerido`, `descripcion` y, si aplica, `rango`, `valores`, `defecto`, `min` (elementos de una lista) y
  `capa` (la capa de geodatos del set que usa: el pie tiene que nombrar su fuente, M3D7).
- `escalas`: `pais` · `ciudad` · `esquema`. `motores`: `three` · `blender` (un estilo cuyo motor no está aquí no puede
  usar el tipo: FALLA M3D2 «este estilo no dibuja <tipo>: usa un estilo de three.js»).
- `adelanto` (eventos): si se ve en la portada, cuánto avance lleva cuando empieza en `t ≤ 0.1` (`{"s": 0.25}` o
  `{"dur": 0.08}`); sin él, el tipo no sirve de gancho (M3D9). `usa` (opcional): otros tipos del catálogo que el módulo
  necesita en el proyecto (un objeto que una pieza dibuja).
- `ejemplo`: tal como va en el `maqueta.json`; se valida contra la propia ficha.

**Las reglas** (`scripts/maqueta_tipos/<tipo>.py`, todas opcionales; la referencia de cada función está en
`scripts/maqueta_tipos/__init__.py`): `resolver(o, X, que)` (lo que el tipo añade al maqueta.json resuelto; sin él, los
parámetros pasan tal cual con los lugares en km), `cerrar(lista, X)` (reglas sobre todas las de su tipo: el tope de 4
rupturas, la simplificación de las fallas), y para los gates `tramos(pieza)` (es una línea: vale para `separada_de`,
M3D11), `centro(pieza, G)`, `puntos(evento, u, G)` (M3D6) y `origen(evento, G)` (M3D9).

**El validador genérico** (`maqueta3d.validar_campos`) revisa cada pieza y cada evento contra su ficha (requerido,
tipo, rango, valores, mínimo, a qué pieza apunta) con la descripción del parámetro en el mensaje; lo que la ficha no
declara se avisa y se ignora.

**Pasos para una entrada nueva:**
1. Escribe `video/maqueta/<clase>/<tipo>.js` y su `<tipo>.json` (copia una parecida); si hace falta,
   `scripts/maqueta_tipos/<tipo>.py`.
2. `python3 scripts/maqueta3d.py catalogo --registrar`: revisa las fichas (completas, cada módulo con ficha y cada
   ficha con módulo, el módulo se registra, sin colores escritos, sin red ni azar, el ejemplo pasa su ficha) y escribe
   `design/sets3d/vocabulario.json`. Nadie más escribe ese archivo.
3. Un caso en un `maqueta.json` de prueba: `maqueta3d.py check` y `maqueta3d.py cuadro --t …` en 9:16 y 4:5.
4. `python3 scripts/pruebas/maqueta_registro.py` (el catálogo, el validador y el motor de cada tipo).

Atajo para los pasos 2 y 3 (lo usa el agente `maqueta-constructor`, que escribe las entradas nuevas cuando un video pide
algo que el catálogo no tiene): `python3 scripts/maqueta_modulo.py check <clase>/<tipo>` (lint más estricto, la ficha,
una maqueta mínima armada con el `ejemplo`, la **pureza** —el mismo segundo dibujado directo y tras recorrer otros da el
mismo cuadro—, el tiempo por cuadro y las hojas 9:16 y 4:5) y `registrar <clase>/<tipo>` (el check y luego `catalogo
--registrar`).

Ninguna entrada nueva toca `motor.js`, `maqueta3d.py` ni otra entrada: el núcleo no conoce ningún tipo. El motor
Blender (`maqueta_blender.py`) no usa módulos: dibuja los tipos de hoy con sus propias ramas; una entrada nueva declara
`"motores": ["three"]` hasta que alguien la escriba ahí.

## Lo que se mueve, las líneas que se pintan y las anotaciones (Fases 2 y 3)

Para contar un MECANISMO (cómo se forma una cola, cómo viaja una señal, quién manda su ubicación): objetos que se mueven
por caminos, una línea que se pinta por tramos y lo que se dibuja encima. Todo en escala `ciudad` o `esquema` (metros) y
solo con el motor three. Caso de prueba que lo usa todo: `video/maqueta/fixture/trafico.json`; pruebas sin render:
`scripts/pruebas/maqueta_movimiento.py`.

**Objetos** (`video/maqueta/objetos/<tipo>.js`, clase `objeto`): `carro`, `bus`, `camion`, `moto`, `persona`, `casa`,
`arbol`, `torre`, `telefono`, `pin`. Low-poly con primitivas de three.js, en METROS reales (x adelante, y arriba, z a su
derecha); su ficha trae `medidas` (`largo_m`, `ancho_m`, `alto_m`: el largo separa los vehículos en la cola). El módulo da
`partes(ctx)` → `[{geo, color, tinte, luz}]` (las partes con `tinte` toman el color de la instancia, una de `variantes(ctx)`
por semilla; `luz` = brilla sola), y los vehículos `faros` y `pilotos` (puntos locales). No los recorre el núcleo: los dibuja
una pieza con `ctx.flota` (una `InstancedMesh` por tipo, con la luz del estilo en el shader porque el objeto gira; de noche,
faros cálidos con un cono tenue en el suelo y pilotos en el tono «mal» que se avivan al frenar). Colores: `ctx.tonos`
(`tonos.vehiculos`: carrocerías claras de noche, de tinta en los fondos claros), nunca escritos.

**Pieza `actor`**: un objeto que sigue un camino: `camino` (con nombre), `desde` + `hacia` (dos lugares), `puntos` o `lugar`
(quieto, mirando a `rumbo`). `claves` `[{t, s | lugar | vel_kmh}]`: con posición (`s`: metros desde el inicio del camino o
«40%»; `lugar`: su proyección) está ahí en t y entre dos claves va en línea recta en el tiempo; con `vel_kmh` sigue a esa
velocidad; tras la última, a su última velocidad, y se detiene al final del camino. El evento `mover` (`actor`, `a`: un
lugar) añade dos claves. Va orientado en la dirección del camino; el protagonista, en el acento.

**Pieza `flujo`** (el tráfico): `carriles` (caminos en el sentido de la marcha), `tipos` (`{"carro": 0.8, "bus": 0.1, …}`),
`densidad` (vehículos por km y carril), `vel_kmh`, `reaccion_s`, `suavizado_s`, `semilla`, `tamano`, `luces`. **El modelo**
(`scripts/maqueta_tipos/_movimiento.py`; lo calcula Python al resolver, una vez, y motor.js solo evalúa: así la cámara que
sigue, los gates y el dibujo ven lo mismo):
1. Cada vehículo tiene una trayectoria s(t) LINEAL POR TRAMOS (listas T y S). Lo que se dibuja es la media móvil de ±h s:
   `s̄(t) = (F(t+h) − F(t−h)) / 2h` con `F = ∫ s` (cuadrática por tramos): forma cerrada, sin pasos de simulación.
2. `libre_i(t)`: el vehículo solo en el campo de velocidades del carril, la base (que `acelerar` sin tramo cambia) y los
   TRAMOS `[a, b)` con su velocidad en el tiempo (`frenar` crea uno; `acelerar` sobre él lo suelta; cada cambio es una
   escalera de 6 escalones en `dur`). Se calcula por eventos: al cruzar un borde de tramo o al llegar un cambio de tiempo.
3. Newell (2002), que es LWR con diagrama triangular: `x_i(t) = min(libre_i(t), x_{i−1}(t − τ) − δ_i)`, del primero al
   último de cada carril (τ = `reaccion_s`; δ_i = los dos medios largos + 2 m). El mínimo de lineales por tramos es lineal por
   tramos.
4. La cola crece HACIA ATRÁS sola, a `w = δ/τ` (≈ 8 m/s con carros y τ = 0.8 s) mientras lleguen más vehículos de los que el
   tramo deja pasar, y se suelta desde adelante tras `acelerar`. Nadie atraviesa a nadie: `x_i ≤ x_{i−1}(t − τ) − δ ≤
   x_{i−1}(t) − δ`, y la media móvil (lineal y monótona) lo conserva.
5. El hueco inicial es ≥ δ + v·τ (si no, el de atrás saltaría en el arranque): la `densidad` tiene tope y M3D2 lo dice.
Un vehículo se ve mientras está sobre su carril (0 ≤ s ≤ largo); los de atrás arrancan fuera del mundo y entran por el borde.

**Eventos de lo que se mueve**: `frenar` (`flujo`, `en`: una posición sobre su primer carril, `longitud_m` hacia adelante,
`vel_kmh`, `carriles`; `dur` = lo que tardan en frenar), `acelerar` (lo mismo con `en` opcional: sin él, todo el flujo),
`aparecer` / `desaparecer` (`pieza`: un actor o un flujo; escriben `ctx.cuadro.vis[id]`, la escala 0–1, y van en el orden del
maqueta.json por t), `mover`. `frenar`, `acelerar` y `mover` no dibujan nada en motor.js: su efecto ya va en las trayectorias.

**La cámara que sigue**: `mira` acepta `{actor: id}` o un vehículo `{flujo: id, n}` / `{flujo, carril, cerca, t}` (el de ese
carril más cercano a `cerca` en el segundo `t`), con `desfase_m`. La clave resuelta lleva `sigue` (motor.js: `miraDe`) y, solo
en Python, `_pos` (t → x, y, alt; `camara_en`): entre claves se interpola igual que siempre, pero el punto de una clave que
sigue es dónde está el móvil en t (una clave fija da exactamente lo mismo que antes: los cuadros de las maquetas existentes son
idénticos byte a byte). `cenital: true` = `elevacion: 89`; con `azimut: 90` la vía este–oeste queda vertical en el 9:16.

**Pieza `trazo`** (generaliza `ruta` para ciudad y esquema): una línea brillante (núcleo + halo, que de noche suma luz) sobre
un camino, de `desde` a `hasta` (posiciones; al revés va en contra del camino), corrida `desplazar_m`, en `color` `bien` ·
`medio` · `mal` (verde, ámbar y rojo del estilo: `estilos.json → colores.bien|medio|mal`), `texto`, o `acento` solo si es el
protagonista. `trazar` la DIBUJA en `dur` (un trazo con algún trazar no se ve antes; con `adelanto`, sirve de gancho en el
cuadro 0) y `pintar` la PINTA POR TRAMOS: el color nuevo avanza como un frente de `desde` a `hasta` (de adelante hacia atrás:
la cola que crece) y se queda; el último pintado manda. `ruta` sigue igual.

**Anotaciones** (clase `anotacion`, `video/maqueta/anotaciones/<tipo>.js`, lista `anotaciones` del maqueta.json, con `t` y
`hasta`). *Arquitectura:* van en la CAPA 2D (texto nítido, crema, sin el acento) pero atadas al 3D: `maqueta3d.py` resuelve
sus anclas (lugar → `{x, y}`; algo que se mueve → `{movil, n, desfase, lev}`); el proyecto añade un clip `#anot` con una capa
SVG y una de texto; motor.js llama `window.__capa(t, proyectar, mundo)` y capa.js arma cada tipo la primera vez y le pasa `A`:
`A.ancla(ancla, t)` (dónde está en pantalla), `A.suelo(x, y, r_m)` (un círculo de r metros en el suelo, proyectado),
`A.svg(tag, clase)`, `A.div(clase, texto)`, `A.p`, `A.vida`, `A.Z`. Así una anotación nueva es un módulo más, como una pieza.
Sus reglas (`scripts/maqueta_tipos/<tipo>.py`) dicen `anclas(a)` y `textos(a, escala)` para M3D4 y el respaldo.
- `pulso`: anillos que se abren en el suelo sobre `sobre` (anclas; `{flujo, cerca, t, cuantos: k}` da k vehículos), `radio_m`,
  `periodo_s`, `anillos`.
- `medida`: un círculo de `radio_m` en el suelo alrededor de `en` (o una `regla` hacia adelante) con su rótulo («5 m»).
- `etiqueta`: una píldora que SIGUE a `sigue` («102 km/h»).
- `reloj`: una hora que corre de `de` a `a` entre `corre_desde` y `corre_hasta` (arriba, abajo o sobre un ancla).
**Cada número que muestran pasa por el respaldo de las cifras** (C3D5 en `video3d.py guion --check`, que ahora lee las
`anotaciones` de cada escena con su `dice`: `maqueta3d.textos_anotacion`; «5 m» se lee como 5 metros). Excepción: un `reloj`
`ilustrativo` sobre un ESQUEMA (no es un momento real; la voz no dice esa hora como dato).


## Mundos: pais, ciudad y esquema

El suelo de la maqueta es un **mundo**: un módulo `video/maqueta/mundos/<escala>.js` (registrado en `MAQ.MUNDOS`) con su
ficha `<escala>.json` y sus reglas `scripts/maqueta_tipos/<escala>.py`. El maqueta.json lo elige con `mundo.escala`
(`pais` por defecto). Un mundo da a las piezas el suelo, la proyección y la escala; las piezas y los eventos declaran en
su ficha en qué `escalas` sirven (M3D2). `python3 scripts/maqueta3d.py catalogo --escala ciudad|esquema` lista lo que se
puede usar en cada una; `maqueta3d.py sets`, los sets con su escala.

| Escala | Unidad de la escena | Cámara | El suelo | Qué se dibuja (hoy) |
|---|---|---|---|---|
| `pais` | 1 km | `dist_km` 15–1600 | el relieve de un set de país (`guatemala`), con mar y máscara del país | `falla`, `luces`, `frontera`, `ruta` y todos los eventos |
| `ciudad` | 1 m | `dist_m` 40–9000 | el relieve de un set de ciudad a ≈ 15 m por celda, con su punto más bajo en 0 | `calles`, `edificios`, `agua`, `zona`, `carretera`; `resaltar`; lo que se mueve (`actor`, `flujo`), `trazo` y las anotaciones |
| `esquema` | 1 m | `dist_m` 15–5000 | plano, con los suelos de su receta (arena, campos, pavimento, el mar de la costa) | las mismas que ciudad (y lo que se mueve) |

**El contrato de un mundo** (`video/maqueta/mundos/<escala>.js`): `async cargar(ctx) → estado` (lo que baja: el
relieve.png; publica `ctx.altura(x, y)` en unidades ya exageradas y `ctx.geo(lon, lat) → [x, y]`, o `null` en un
esquema), `armar(ctx, estado)` (el suelo, antes que las piezas) y `en(t, estado, ctx)` (al final de cada cuadro). Su
ficha añade `unidad_m`, `camara` (`campo`, `unidad`, `rango`, `despeje`, `cerca`, `lejos`, `niebla`), `plano` (el plano
exterior) y `capas` (las del set que usa siempre: el pie las nombra, M3D7); sus reglas, `mundo(o, ficha, m3)` → el
objeto que el resolver y los gates usan (`suelo`, `dentro`, `punto`, `lugares`, `caminos`, `capa(nombre)`…).

**Lo que el mundo da a las piezas** (la API de la Fase 2: carros y gente que siguen caminos):
- `ctx.altura(x, y)`: la altura del suelo en unidades de la escena (ya exagerada); `ctx.V3(x, y, lev)` el punto en three.
- `ctx.geo(lon, lat) → [x, y]` (pais en km; ciudad en metros; `null` en esquema, donde todo va en metros desde el centro).
- `ctx.unidad_m` (metros por unidad: 1000 en pais, 1 en ciudad y esquema) y `ctx.metros(v)` (metros → unidades).
- `ctx.caja = [x0, y0, x1, y1]`.
- `ctx.caminos = {nombre: [[x, y, s, 0], …]}` (s: unidades desde el inicio; el mismo formato de las cadenas de falla, así
  que `ctx.puntoEnS(cadena, s)` vale), `ctx.camino(nombre)` y `ctx.enCamino(nombre, s) → {x, y, dx, dy}` (el punto y su
  dirección unitaria). Vienen de la receta del esquema y de cada `carretera` (`<id>`, `<id>.carril-k`).
- `ctx.lugares = {id: {x, y, nombre}}`: los del mundo (ciudad y esquema) y los de `mundo.lugares`.

**Sets de ciudad** (`scripts/build_set3d.py <set>`; el primero, `capital`: el centro de la Ciudad de Guatemala, zonas 1–5,
8–11 y 13, ≈ 6.5 × 7.2 km, 1 MB). Todo en metros locales (`x = (lon − lon0)·m_lon`, `y = (lat − lat0)·m_lat`; la
proyección en `relieve.json`): `relieve.png` (Mapzen terrarium z14, ≈ 15 m por celda, `base_m`), `calles.json` (por clase y
las arterias con nombre de la receta de `design/vias/<vias>.fuente.json`, de la misma consulta y caché de
`build_vias.py`), `edificios.json` (`[altura_m, x0, y0, …]`: `height`, o `building:levels` × 3 m; sin dato, 6 m),
`agua.json`, `zonas.json` (parques y áreas verdes, con id por su nombre) y `lugares.json` (los de la receta de las vías y
los nodos con nombre). Atribución en `fuente.json` («© OpenStreetMap», ODbL; Mapzen); el pie la nombra (M3D7). La caja de
`design/vias/capital.json` (26 × 34 km) se dejó para las vías: con calles menores y edificios pesaría decenas de MB.

**Recetas de esquema** (`mundo.receta`; `semilla`, `tamano_m`, `carriles`, `manzana_m`, `altura_max_m`). Las calcula
`scripts/maqueta_tipos/esquema.py` una vez (la misma semilla da los mismos datos) y viajan resueltas al motor, así los
gates y el dibujo ven lo mismo:
- `ciudad`: cuadrícula de manzanas (lotes con retiro, más altos cerca del centro, algún parque). Caminos `ns-<k>`, `eo-<k>`,
  `eje-ns`, `eje-eo`; lugar `parque`.
- `carretera`: una autopista de `carriles` (la mitad por sentido) que cruza una ciudad de oeste a este, con edificios más
  bajos junto a ella. Caminos `eje`, `carril-1…N` (1…N/2 hacia el este, a la derecha del eje; los demás hacia el oeste, con
  sus puntos en el sentido de la marcha), `lateral-norte|sur`; lugares `entrada`, `salida`, `puente`.
- `campo`: parcelas en dos tonos, un camino curvo (`camino`), un río (`rio`) y un pueblo; lugares `pueblo`, `puente`.
- `costa`: el mar al sur con su orilla ondulada, la playa, la costanera (`costanera`, `orilla`) y un pueblo en cuadrícula;
  lugares `playa`, `mar`.
- `plaza`: una plaza central con el edificio principal al norte; caminos `vuelta-plaza`; lugares `plaza`,
  `edificio-principal`.
Toda receta trae los lugares `centro`, `norte`, `sur`, `este`, `oeste`; `mundo.lugares` añade otros con `x` e `y` en metros.
**Un esquema no afirma geografía** (M3D12): «Esquema» en el aviso, nombres genéricos. Para un lugar real: `ciudad` o `pais`.

**Las piezas de mundo**: `calles` (por clase, bandas de su ancho real), `edificios` (extruidos con su altura; `destacar`
uno en el acento; en contorno y plano, sus aristas en línea), `agua`, `zona` (un polígono teñido: `area` de una zona del
mundo o «parques», o `puntos`), `carretera` (carriles, línea central y orillas sobre el eje de la receta o una arteria del
set). `resaltar` con `pieza` + `elemento` (un lugar) enciende en el acento el edificio o la calle de ese lugar (o la
carretera entera). Casos de prueba: `video/maqueta/fixture/esquema_carretera.json` y `ciudad_capital.json` (los revisa
`maqueta3d.py prueba`; sus negativos, `scripts/pruebas/maqueta_mundos.py`).

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
