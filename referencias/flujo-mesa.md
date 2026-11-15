# La mesa de archivo en vertical (9:16 y 4:5)

El video vertical dibujado como el 16:9 de `/youtube-long`: una mesa fija donde **entra lo que la voz nombra**. Decisión
del usuario (2026-11-14), tras aprobar el lienzo «Animador vertical» en Claude Design. Motor: HyperFrames
(`scripts/video_hf.py`; núcleo común con el 16:9 en `scripts/mesa.py`). El motor propio (`video/*.html` +
`scripts/video_grabar.js`) sigue vivo para los flujos sin migrar y para grabar los tableros.

**Estado (2026-11-14).** El usuario aprobó los pilotos (Bancafé parte 1 y La Línea parte 3) y pidió aplicar lo mismo a
los demás flujos «con las reglas, animaciones y todo», sin otro piloto. Todos los flujos de video nacen en mesa (los
noticieros, que seguían en el motor propio, se retiraron del framework ese mismo día).

| Flujo | Quién dibuja | Cómo cae en la mesa |
|---|---|---|
| /historia, /serie (motor historia) | **la mesa** | Fotos, notas, documentos y personas: su lenguaje desde el principio. |
| /explica, /serie explica | **la mesa** | La pizarra `cuenta`, la animación `explica`, `adivina`, `escala` y las tarjetas son tableros; el gancho (pareja → `barra`), los golpes y las definiciones, piezas; el chip «Ejemplo» lo pone la mesa. |
| /sabias | **la mesa** | Gancho «¿Sabías que…?» con su visual ya puesto en el cuadro 0; la tarjeta del dato, tablero; cierre de una pantalla. |
| /video, /departamento | **la mesa** | Las tarjetas del hilo, `ranking`, `mapa`, `escala` y `tiempo` son tableros; gancho, golpes y definiciones, piezas (nota, cifra, `barra`, mapa de los 22). Versión B con `variante --plano`. |
| /congreso | **la mesa** | El `hemiciclo` es tablero (asientos, umbral, sello, foco con retrato); el gancho deja el portal y abre con la foto del pleno y la `barra` de votos frente al umbral. |

`realizacion` la fija `preparar` al crear el TRABAJO (`VD.MESA_FLUJOS`; `--realizacion propio|mesa` la fuerza): un trabajo
empezado con un motor termina con ese motor. Migrar un flujo es añadir su `tipo` a `MESA_FLUJOS` cuando sus piezas existan.

Pendiente en el motor: la pregunta P6 en el pago y las piezas `paso` (cronología),
`brecha`, `hoja` (la pizarra como pieza; hoy es tablero), `tabla` y `diagrama`. Mientras no existan, lo suyo va como tablero.

## 1. Reglas (lo que no se negocia)

1. **Dinamismo = piezas que entran.** Con cada oración cae una pieza que la voz nombra y se queda quieta. La cámara no se
   mueve; nada se escala, desliza ni late para aparentar ritmo. Ningún gate mide píxeles ni movimiento.
2. **El texto da tiempo de leerse (MV8).** Una pieza queda al frente al menos `0.5 s + 0.3 s × palabras que la voz no
   dice` (nunca menos de 1 s) antes de replegarse o barrerse. Lo que la voz dice mientras la pieza está en pantalla se oye
   a la vez que se ve y no cuenta; por eso la cita y el documento que la voz lee no tienen mínimo.
3. **Repliegue por corte.** En 1080×1920 caben 2–3 piezas (hasta 4 si la última es chica). Cuando la que entra no cabe, las de al frente pasan **de un
   corte** a su versión compacta, arriba y atenuadas (a lo más dos). Solo ocurre cuando entra otra pieza: nunca para dar
   ritmo, nunca animando la escala.
4. **Archivo real primero.** Foto con crédito, recorte con el titular o el extracto literal de la nota leída, página de
   documento con la frase subrayada, lugar en el mapa. Una ficha de texto es el último recurso.
5. **Personas y justicia.** La foto de alguien en un proceso solo va donde la voz lo nombra; nada de «culpable» sin
   sentencia firme; un alegato se atribuye («según la acusación»).
6. Lo de siempre: colores por variables de la paleta, fuentes locales, sin red en el render (GSAP en
   `design/vendor/`), render con `--workers 1`.

## 2. El cuadro

| Elemento | 9:16 (1080×1920) | 4:5 (1080×1350) |
|---|---|---|
| Kicker de serie («Parte N de M · título») | y 222, mono 22 px, en el acento | y 66 |
| Barra de progreso (un tramo por acto y el cierre) | y 262 (226 sin serie), 7 px | y 106 |
| Golpe de arriba (`titulo` de la mesa, ≤ 6 palabras) | bajo la barra, 92 px (76 si pasa de 2 renglones) | igual |
| Mesa | desde el fin del golpe + 30 hasta y 1370; x 85–876 (hasta 1023 sobre y 1070) | hasta y 1090; x 85–995; todo a escala 0.87 |
| Subtítulos | y 1400 (1500 en el cierre), 60 px, trozos ≤ 26 caracteres; la palabra activa en caja de acento, las que faltan al 38 %; callan mientras la voz lee una cita en pantalla | y 1120 |
| «Sígueme» a mitad (V25) | hacia el 50 %, 3.4 s, arriba a la derecha de la mesa (la mesa baja 104 px) | igual |
| Cierre | pantalla 1: tres conclusiones (la última en acento); pantalla 2: frase final, «Sígueme en», logo y usuario de las cinco redes; el golpe de arriba anuncia la parte siguiente de una serie y, desde la parte 2, sale «Empieza por la Parte 1 · fijada en mi perfil» | redes en dos columnas |
| Bucle | tras el cierre, el cuadro 0 del gancho vuelve 0.6 s con la barra en cero (TikTok repite el video) | igual |
| Portada | `salida/portada.png`: el cuadro del gancho con su golpe de arriba, sin subtítulos ni barra | — |

La barra va fija arriba del golpe (en las láminas iba debajo): si el golpe cambia de uno a dos renglones, la barra no
salta.

## 3. Piezas

Las del 16:9, con las medidas del vertical (`medida_v`): `foto` · `recorte` · `documento` (página con marcador o
portada) · `persona` · `institucion` · `lugar` (mundo con ruta, o Guatemala con el departamento) · `fecha` (sello o
calendario) · `cifra` (con `cuenta` y `cuadros`) · `termino` (nota, o ficha con `definicion`) · `cita` (se entinta
palabra por palabra) · `lista` (un chip por `dice`, con `lazo`).

- Letra: lectura ≥ 42 px, rótulos ≥ 28 px; créditos y fuentes en 22 px (no son lectura).
- Una pieza con `w` usa ese ancho (p. ej. una foto chica junto a una nota).
- Dos piezas chicas (≤ 470 px) caben lado a lado; una hoja a todo el ancho va sola en su renglón.
- El rótulo de acto de una escena (`S.R`) abre su mesa como ficha: «Acto 2 de 3 · lugar», título y periodo.
- Una mesa sin golpe de arriba propio conserva el de la mesa anterior.
- **`red`: la jerarquía de personas.** Cartas por nivel (retrato, nombre corto, cargo), hilos entre ellas, quien acusa
  aparte y sin hilos, y el estado del caso si un hecho lo trae. Hilo sólido = hecho; **punteado = alegato**, con la etiqueta
  «Según…» arriba, que entra antes que las caras. Una carta con `clave` entra como apodo («El Uno») y se voltea a la cara
  cuando la voz dice el nombre. Va sola en su mesa: ≤ 3 niveles, ≤ 2 por nivel, ≤ 2 acusadores. Una escena `red` del
  guion ya la trae en el borrador.
- **`barra`: la cifra con su medida.** 2–5 barras `{etiqueta, valor, texto?, dice?, acento?}` a la misma escala (`valor`
  numérico, `texto` lo que se lee: «Q45,259»); la pieza entra con su `titulo` y cada barra crece cuando la voz dice su
  `dice`; la de `acento` (o la última) en el color de acento. MV4: el largo corresponde a lo escrito. Reemplaza al visual
  `pareja` del gancho y a la mini-votación de /congreso (a favor, los que hacían falta, en contra).
- **Texto cinético del motor propio en la mesa** (gancho, golpe, definición de /video, /sabias, /explica, /departamento,
  /congreso): la línea de pantalla es el golpe de arriba o una nota, nunca las dos; un golpe con número es una `cifra` con
  la línea como rótulo; la definición, una ficha `termino` con `definicion`; el gancho sin foto abre con dos piezas ya
  puestas (MV14): la nota y su visual (pareja → `barra`, llenado o figuras → `cifra`, lugar → `lugar` con el departamento).
- **Chip «Ejemplo»** (/explica, E3–E4): arriba a la derecha, en la línea del kicker, mientras está una mesa con números de
  ejemplo (también sobre un tablero: su clip se graba sin chip).
- `"limpia": true` en un golpe: el plano pide el repliegue justo antes de esa pieza.
- `"crema": true` en una `cifra`, una nota (`termino`) o una `barra`: se dibuja sin el color de acento (MV13: un solo
  acento al frente; § 5b).
- **Tablero**: `explica`, `tarjeta`, `cuenta`, `hemiciclo`, `vias`, `deptos`, `ranking`, `mapa`, `escala`, `tiempo`,
  `lupa`, `cortina`, `adivina` se graban limpias con el motor propio (`video_hf.py tableros`) y van solas en su mesa. Si el plano
  les pone golpes, el primero entra ≥ 1 s después del último paso y la animación le cede la mesa de un corte.

## 3b. La maqueta

**Qué es** (usuario, 2026-11-14). A veces un video incluye un **render 3D de una situación**: el relieve real de Guatemala
con sus pueblos, una ruta, una falla o la frontera, y una cámara que lo recorre mientras la voz cuenta. Es un clip de
three.js (`scripts/maqueta3d.py` en **modo pieza**; contrato en `referencias/diseno/maqueta3d.md`) que la mesa aloja como
aloja un tablero, pero no viene del guion: lo decide el realizador **después de la voz**, a nivel de mesa. **Dentro de la
maqueta la cámara sí se mueve**: es la única excepción a la cámara quieta, y vale solo dentro de su marco (la mesa, el
golpe de arriba y las piezas siguen quietos).

**Cuándo sí.** Cuando **el lugar es la información**: una ruta entre dos sitios, una falla, una cuenca, qué tan lejos
queda algo de otra cosa, por dónde pasó, qué pueblos alcanzó. La voz nombra lugares y la oración se entiende mejor
viéndolos en su sitio.

**Cuándo no.** Para ubicar un solo lugar (eso es la pieza `lugar`, que es archivo y cuesta nada); para adornar una
oración que no habla de un lugar; en una escena que ya es tablero; en el gancho (el cuadro 0 es del sujeto: MV14); cuando
hay una foto, un recorte o un documento que prueban lo que se dice (la maqueta **no es archivo real**: no suma a MV5).
Es cara de mirar y de producir: **≤ 2 por video vertical** (≤ 4 en el 16:9, ≤ 2 por capítulo).

**La forma.** `maqueta` en la mesa, junto a `escenas`, `titulo` y `golpes`:

```json
{"escenas": ["e4", "e5"], "titulo": "De la capital al puerto",
 "maqueta": {"set": "guatemala", "estilo": "noche", "protagonista": "ruta",
  "piezas": [{"id": "ruta", "tipo": "ruta", "lugares": ["guatemala", "escuintla"]},
             {"id": "pueblos", "tipo": "luces", "lugares": "todos"}, {"id": "frontera", "tipo": "frontera"}],
  "lugares": {},
  "camara": [{"mira": "guatemala", "dist_km": 420, "azimut": 0, "elevacion": 55},
             {"dice": "hasta Escuintla", "mira": "escuintla", "dist_km": 160, "azimut": -15, "elevacion": 40}],
  "eventos": [{"dice": "hasta Escuintla", "tipo": "resaltar", "lugar": "escuintla", "dur": 2.0}],
  "marcas": [{"dice": "Escuintla", "lugar": "escuintla", "texto": "Escuintla"}]},
 "golpes": [{"tipo": "cifra", "dice": "sesenta kilómetros", "valor": "60 km", "rotulo": "de carretera"}]}
```

- **`set`**: los geodatos (`design/sets3d/<set>/`; hoy `guatemala`: relieve, las 22 cabeceras y ≈ 300 pueblos, fallas,
  frontera). Un lugar se nombra por su id (minúsculas, sin tildes, con guiones: `guatemala`, `puerto-barrios`), por
  `[lon, lat]`, o se declara en `lugares` (`{"mi-aldea": {"lon": …, "lat": …, "nombre": "…"}}`). El digesto del plano
  trae los lugares del set que la voz nombra.
- **`estilo`**: uno del catálogo cuyo motor renderice (`python3 scripts/maqueta3d.py estilos` los lista con su «cuándo
  usarlo»; los de three.js: `noche`, `color`, `contorno`, `voxel`, `plano`). **Un solo estilo por video**: si el plano
  trae dos maquetas, llevan el mismo.
- **`piezas`** y **`protagonista`**: lo que hay sobre el mundo y la única pieza que va en el acento. Ninguna lleva texto.
  Los tipos, sus parámetros y un ejemplo de cada uno están en el catálogo del vocabulario (el digesto del plano lo trae;
  a mano: `python3 scripts/maqueta3d.py catalogo --para realizador`). Lo que no está en el catálogo no se dibuja.
- **`camara`**: claves `{mira, dist_km, azimut, elevacion}`. **La primera va sin `dice`**: es el encuadre con que abre la
  mesa. Cada una de las demás lleva el `dice` con el que la cámara **llega** a ese encuadre (`"al": "fin"` = llega al
  terminar la frase; sin `dice` y con `"al": "fin"`, al terminar la mesa: un acercamiento lento de cierre). Entre claves
  la cámara vuela sola. Referencia: el país entero cabe desde `dist_km` ≈ 700–800 con `elevacion` ≈ 62; a 150–250 km se
  lee un valle. El punto que mira cae en el centro del marco.
- **`eventos`**: los del catálogo (`maqueta3d.py catalogo --para realizador`: cada uno con sus parámetros y un ejemplo),
  con `dice` y `dur` en segundos (o `hasta_dice`); `sfx` opcional del catálogo fijo.
- **`marcas`**: pines pegados al mundo: `dice`, `lugar`, `texto` (y `sub`). Entra 0.3 s antes de su palabra y se queda
  hasta el final de la mesa (`dura` en segundos o `hasta_dice` la acortan; a lo más 3 a la vez).
- Cada `dice` son palabras literales de la voz **de las escenas de esa mesa** (`"escena": "e5"` lo fija a una; `"vez": 2`
  = la segunda vez que se dice). Sin `dice`, al empezar la mesa.
- No lleva titulares, cifras ni subtítulos: el golpe de arriba es el `titulo` de la mesa, las cifras son **golpes** y
  los subtítulos los pone la mesa. El pie del marco (la atribución de los geodatos que usa) lo pone la mesa también; un
  aviso como «Maqueta · no a escala» o «Traza esquemática» sale solo si el bloque trae `aviso` (no va por costumbre).

**En el cuadro.** El clip ocupa el marco de un tablero (950×1040, uno para 9:16 y 4:5) todo lo que dura la mesa. Los
golpes de la mesa caen **encima**, abajo a la izquierda, **uno a la vez** (cada uno se va de un corte cuando entra el
siguiente) y sin taparle más del 35 % del alto: una `cifra`, una `fecha` o una nota corta. Por eso el lugar que importa
va en la mitad de arriba del marco (la cámara lo centra) y el número que la voz dice, en su golpe.

**Reglas (gates MV15–MV19, sobre los datos).**

| Gate | Pide |
|---|---|
| MV15 | forma: `set` que existe, `estilo` del catálogo y con motor, `piezas` con `id` y `tipo`, `protagonista` que es una pieza, cámara con sus campos y la primera clave sin `dice`, eventos con `tipo` y `dur`, marcas con `lugar` y `texto`; nada de titulares ni cifras dentro; no en una escena tablero |
| MV16 | concordancia: cada `dice` (y `hasta_dice`) lo dice la voz de esa mesa; las claves de cámara, en el orden en que la voz las dice |
| MV17 | un solo estilo de maqueta por video |
| MV18 | carga: la mesa de la maqueta dura 5–24 s; ≤ 3 golpes encima; ≤ 2 maquetas por video |
| MV19 | `maqueta3d.py check --pieza --lienzo 950x1040` en 0 fallas (M3D1–M3D4, M3D6, M3D8, M3D11: lugares y piezas que existen, velocidad de cámara, marcas dentro del cuadro y sin pisarse, eventos a la vista); el mensaje del motor llega tal cual, con sus segundos contados desde el inicio de la mesa |

Además: la cámara que llega, cada evento y cada marca cuentan como **entradas** para MV2 (cada oración trae una; ningún
hueco de más de 6 s dentro de la maqueta); cada cifra o año que la voz dice se ve en un golpe o en una marca (MV1); un
número en una marca necesita respaldo (MV4); la pieza de encima cabe y da tiempo de leerse (MV8, MV11).

**Producción.** `plano --check` escribe `TRABAJO/maquetas/<mesa>/maqueta.json` (segundos relativos al inicio de la
mesa, paleta del video) y lo valida; `grabar` (en el paso de los tableros; o `video_hf.py maquetas T`) lo renderiza a
`TRABAJO/clips_maqueta/<mesa>.mp4` con su `.efectos.json` (los `sfx` van a la mezcla con el desfase de la mesa). Solo
se renderiza la que cambió (`clips_maqueta/huellas.json`), a los fps de `grabar` (el motor acepta de 10 a 60). **Costo: ≈ 1.8 s de render por segundo de maqueta** (a 30
fps; una vez para los dos formatos verticales, otra para el 16:9). `MESA_RENDER=0` deja un doble del tamaño y la
duración exactos sin llamar al motor (un doble nunca se reusa como render). `make video-fixture-maqueta` = la maqueta
de /serie con una mesa de maqueta, de punta a punta.

## 4. El plano

`TRABAJO/plano.json`, el mismo esquema del 16:9, sin `x` ni `y` (el motor coloca por regla):

```json
{"mesas": [{"escenas": ["e1"], "titulo": "Del café a Barbados", "golpes": [
  {"tipo": "foto", "foto": "caf-f01", "pie": "Edificio central de Bancafé, zona 9"},
  {"tipo": "termino", "texto": "Bancafé"},
  {"tipo": "lugar", "dice": "banco en Barbados", "mapa": "mundo", "ruta": true, "puntos": [{"nombre": "Guatemala"}, {"nombre": "Barbados"}]}]}]}
```

- Las escenas se nombran `eN`. El cierre no va en el plano (lo arma el motor).
- Los golpes sin `dice` al inicio de la primera mesa ya están puestos en el cuadro 0 (el gancho: la foto del
  protagonista y su nombre).
- Escribir para el vertical: **una pieza por oración, texto corto** (lo que la voz ya dice no hace falta repetirlo en
  la ficha), mesas de una escena o dos.

## 5. Gates MV (`video_hf.py plano --check`, sobre los datos)

| Gate | Pide |
|---|---|
| MV1 | cada cifra o año que la voz dice se ve cuando se dice |
| MV2 | cada oración trae una pieza, una marca o un paso; ningún hueco de más de 4 s |
| MV3 | una foto, una sola vez |
| MV4 | respaldo por tipo (ficha y crédito de la foto, nota leída del recorte, página del documento…); foto de un proceso judicial solo donde la voz nombra a alguien |
| MV5 | no relleno: ≥ 50 % de oraciones con pieza nueva, ≥ 35 % de archivo real (aviso bajo 50 %), ≥ 4 tipos, ≤ 2 rótulos de texto seguidos |
| MV6 | carga: mesa de 3–24 s y ≤ 6 piezas; entradas a ≥ 0.4 s; el golpe de un tablero, tras su último paso |
| MV7 | sin cámara |
| MV8 | lectura: `0.5 + 0.3 × palabras no dichas` s al frente (≥ 1 s) |
| MV9 | pila (no es un gate: no hay `FALLA MV9`; sale de cómo `componer` coloca las piezas): ≤ 4 piezas al frente (3 en fila, `PILA_LEGIBLES`, más una chica al lado de la tercera) y ≤ 2 compactas arriba (`PILA_COMPACTAS`) |
| MV10 | zona segura por geometría, en 9:16 y en 4:5 |
| MV11 | ninguna pieza se dibuja a menos del 72 % de su tamaño |
| MV12 | alegato: los hilos de una `red` atribuida van punteados, con `etiqueta` «Según…» y con la voz de la mesa atribuyendo; quien acusa, sin hilos |
| MV13 | un solo acento al frente a la vez: falla si una cifra o una barra comparte el acento con otra o con una nota; otras dos piezas en acento a la vez, aviso (§ 5b); `crema` solo en `cifra`, `termino` y `barra` |
| MV14 | el cuadro 0 abre con ≥ 2 piezas ya puestas (el gancho no lleva maqueta) |
| MV15–MV19 | la maqueta 3D de una mesa: forma, concordancia con la voz, un solo estilo, carga y los gates del motor (§ 3b) |

MV1–MV7 son YT13–YT19 del núcleo con las constantes del vertical (`REGLAS`), y MV15–MV19 son YT20–YT24. `hyperframes check` añade sus propios
avisos (texto bajo 28 px, texto sin tiempo de lectura, tramos sin cambio): se leen en `video_hf.py revisar`.

### 5b. MV13: un solo acento al frente

La regla Noche («acento = una sola cosa»; `referencias/diseno/sistema.md`) en la mesa. El gate lee **los datos del plano**
(`mesa.en_acento`, lo mismo que el motor pinta con el color de acento) y los tiempos de `componer`; nunca píxeles.

| Pieza | Lo que lleva en acento | Peso |
|---|---|---|
| `cifra` | el valor (y sus `cuadros`) | dato |
| `barra` | la barra destacada (`acento`, o la última) y su valor | dato |
| `termino` sin `definicion` (la nota) | la nota entera; con `definicion` es una ficha de papel y no cuenta | bloque |
| `lista` con `acento` | el chip destacado | bloque |
| `red` con `etiqueta` o con una `clave` | la etiqueta «Según…» o la clave | bloque |
| `recorte` con `resalta` | el subrayado | marca |
| `documento` con `pagina` | el marcador sobre la página (una `portada` no lleva) | marca |
| `lista` con `lazo` (sin `acento`) | el lazo | marca |

- Se mira cuando una de esas piezas entra y otra **sigue al frente**. Una pieza replegada no cuenta (su compacta va
  atenuada, arriba); en una mesa con maqueta las piezas van de una en una y nunca coinciden.
- **Falla** si una es un **dato** y la otra es otro dato o un bloque (`mesa.acento_compite`): con una cifra en pantalla
  el acento es solo suyo (la cifra y su nota, la barra y la cifra). **Avisa** en lo demás: dos notas, una nota junto a un
  subrayado, una cifra junto a la frase subrayada de la que sale. Así salieron los dos pilotos aprobados (Bancafé parte 1 y
  La Línea parte 3: 9 coincidencias de las que avisan y ninguna de las que fallan), y el gate no rechaza la referencia
  aprobada; el aviso queda a la vista del realizador y del juez del plano.
- No cuentan las marcas chicas (los puntos de un mapa del mundo, la línea de crédito de la pestaña de un documento) ni el
  cuadro (kicker, palabra activa del subtítulo, cierre): no son piezas.
- **Cómo se arregla, en el plano:** `"crema": true` en la que no es el dato que la voz está diciendo (solo `cifra`,
  `termino` y `barra`: el motor la dibuja en crema, también replegada); `"limpia": true` en la que entra (repliega lo
  anterior); quitar el `resalta`, el `lazo` o el `acento` que sobra; o llevarla a otra mesa.
- El borrador ya lo trae resuelto donde lo causa él: en el gancho de texto cinético, la nota que acompaña a la `cifra` o a
  la `barra` va en crema, y la línea bajo un golpe, también.
- Solo vertical. En el 16:9 (`youtube_hf.py`) las piezas se colocan a mano y el gate no existe (no hay código YT libre:
  YT12 está retirado y no se reusa); `mesa.en_acento` y `mesa.acentos_a_la_vez` están en el núcleo para cuando lo tenga, y
  su hoja de estilos aún no dibuja `crema`.

## 6. Cómo se produce

Los comandos son los de siempre; con `realizacion: mesa` despachan a la mesa (`VD.es_mesa`):

```
<flujo>.py tiempos T                  la voz real → escenas.json (igual que antes)
Workflow «plano» {trabajo: T}         video-realizador escribe T/plano.json desde `<flujo>.py plano T --digesto` (tras la voz);
                                      luego el juez del plano (historia-oyente, modo plano) lee plano.md con ojos frescos y lo que
                                      bloquea vuelve al realizador una vez (T/juez_plano.json; `sin_juez: true` lo salta)
<flujo>.py plano T --check --hoja     gates MV1–MV14 y la hoja de golpes (plano.md)
<flujo>.py grabar T [--formato 4:5]   plano --check → tableros limpios y maquetas 3D → proyecto → hyperframes check → render (un proceso)
<flujo>.py montar T [--formato 4:5]   una mezcla para los dos formatos (−14 LUFS), .srt, caption.md y portada.png
<flujo>.py revisar T [--formato 4:5]  hoja de contacto del video final (revision/contacto[_4x5].png)
<flujo>.py entregar T                 igual que antes
historia.py producir T                la cadena entera; se detiene si falta plano.json («falta la fase Plano»)
```

- El **borrador** (`plano.borrador.json`, `video_hf.borrador_v`) sale del código: una mesa por escena con su foto, su cita,
  sus cifras y años dichos, las personas nombradas, la página de documento, la `red`, un recorte con el titular real de la
  nota de un hecho, y el cuadro 0 con el protagonista. No pasa los gates por sí solo y no se publica: lo mejora el realizador
  (en una maqueta se usa tal cual y los gates solo avisan).
- Lo que falle en pantalla se arregla **en el plano**: no se toca el guion ni la voz. Un retoque = el Workflow «plano» con
  `notas`. Si cambia una voz: `tiempos`, `plano --check` y volver a grabar (no hay `grabar --solo`).
- Render: ≈ 1.6× la duración por formato, en fila (HyperFrames renderiza de uno en uno). `MESA_CALIDAD=draft` para probar.
- `MESA_RENDER=0` (maquetas): `grabar` hace todo menos el render y deja un doble de la duración exacta, **marcado por
  formato** (`salida/.maqueta_sin_render.<9x16|4x5>`); la marca la quita `montar` cuando monta un render de verdad de
  ese formato, y `entregar` real rechaza un trabajo con cualquier formato marcado.
- El render tiene límite de tiempo (600 s + 20 s por segundo de video; `MESA_RENDER_LIMITE_S` lo fija a mano): al
  vencer se mata el grupo de procesos entero. GSAP sale de `design/vendor/` (sin red) y las versiones de HyperFrames,
  GSAP y three.js viven en `scripts/versiones.py`.
- `make historia-fixture` y `make serie-fixture` van con `MESA_RENDER=0`; `make video-fixture-mesa` renderiza de verdad.
- `video_hf.py` también se puede llamar directo: `piloto` (copia un TRABAJO ya producido para rehacerlo en mesa),
  `importar-plano` (los golpes del 16:9 de una parte, como punto de partida), `borrador`, `digesto`, `tableros`, `maquetas`, `proyecto`,
  `revisar` (hyperframes check + hojas por mesa), `audio`, `render`, `montar`, `portada`, `contacto`.

## 7. Qué pasa con las reglas del motor propio

- **Se conservan** (guion, voz, audio): V1–V6, V8, V9, V11, V16–V20, V23, R1–R14, P1–P6, F1–F9, H*, E*, SE*.
- **Pasan a gates MV**: V13 → MV10 · V15/R12 → MV14 · V10/V26 → MV2/MV1 · V22 → MV6 · H6/H7/H7c → MV11/MV3/MV4.
- **No corren en la mesa** (siguen en el motor propio): V12, V21, el catálogo `TRANSICIONES`, el empuje de la foto, la
  foto a sangre, A3. V7, A1 y A2 quedan para los clips de tablero.
