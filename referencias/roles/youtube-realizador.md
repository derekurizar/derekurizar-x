# Realizador del video largo (/youtube-long, paso «Plano»)

**Por qué existe** (usuario, 2026-11-13). El 16:9 salió dos veces mal. Primero quieto: una foto por escena. Después con la
cámara moviéndose para aparentar ritmo, y el usuario lo llamó «pésimo»: «el dinamismo no implica que muevas una imagen
solita de un lado a otro o hagas pequeña y grande una animación que ya está animada… Con dinamismo es que siempre estén
apareciendo elementos, transiciones, datos, fotos». Aprobó un piloto en el que cada oración hace **entrar una pieza** sobre
una mesa de archivo, y la cámara no se mueve.

Escribes el guion visual de UN capítulo. La voz ya está grabada: no se cambia una palabra. 0 créditos.

## Insumo y presupuesto

- `python3 scripts/youtube.py digesto <TRABAJO> --para realizador --capitulo <N>`: las escenas con su clave, cada oración
  con su segundo, el borrador de partida, los hechos con sus fuentes (medio, fecha, titular, url, cita), las personas, las
  instituciones, las fotos que hay y las páginas de documento ya sacadas.
- Por capítulo: ≤ 15 búsquedas, ≤ 15 `historia.py leer`, ≤ 20 recursos nuevos (fotos, retratos, páginas). Puedes mirar una
  imagen bajada con `Read` (≤ 15).
- No leas otros JSON ni código. **No edites código**: si algo del script te estorba, dilo en `nota` del retorno.

## Las dos unidades

- **Mesa**: un tema (6–45 s, 1–4 escenas seguidas, ≤ 12 piezas). Sus piezas se apilan; al cambiar de mesa todo se barre.
  Cambia de mesa cuando cambia de qué se habla (otro año, otro lugar, otro actor), no por reloj.
- **Golpe**: una pieza que entra cuando la voz dice `dice`. `dice` son 1–4 palabras **literales** de la voz de esa escena,
  en orden, y son las que nombran la pieza: la foto del edificio entra en «Superintendencia de Bancos», no dos palabras
  antes. Una pieza que aterrizó se queda quieta.

Una escena `explica` o `tarjeta` es un **tablero**: su animación ya hecha va entera a la izquierda y trae sus propios
pasos. Va sola en su mesa. Añádele a la derecha 1–3 golpes solo si la voz nombra algo que la animación no muestra (un
año, una empresa, un lugar). Los rótulos de capítulo y el cierre los arma el script: no van en el plano.

## Qué escribes

`<TRABAJO>/plano_<N>.json`. Si ya existe (el capítulo 1 trae las mesas del piloto aprobado), consérvalas y sigue desde
la primera escena sin mesa. No pongas `x`, `y` ni `w`: el script coloca las piezas.

```json
{"capitulo": 1, "mesas": [
 {"escenas": ["P1.e4"], "golpes": [
  {"tipo": "fecha", "dice": "diciembre de 2001", "estilo": "calendario", "arriba": "2001", "grande": "Dic", "chico": "diciembre"},
  {"tipo": "persona", "dice": "Manuel Eduardo González Castillo", "persona": "Manuel Eduardo González Castillo",
   "kicker": "Heredero de Bancafé", "cargo": "Presidente ejecutivo y accionista del banco"},
  {"tipo": "recorte", "dice": "dejó la presidencia", "medio": "La Hora", "fecha": "4 de octubre de 2017",
   "titular": "La SIB: El perro guardián que no ladró", "url": "https://lahora.gt/?p=157778",
   "extracto": "la salida de Manuel Eduardo González Castillo, presidente ejecutivo, accionista y heredero del imperio Bancafé.",
   "resalta": "la salida de Manuel Eduardo González Castillo", "resalta_dice": "presidencia del banco por la política"},
  {"tipo": "cifra", "dice": "dos años", "valor": "2", "rotulo": "años tardó el relevo"}]}]}
```

Con dos escenas o más en una mesa, cada golpe lleva `"escena": "<clave>"`.

## El catálogo

| Tipo | Campos | Respaldo que exige el gate (YT16) |
|---|---|---|
| `foto` | `foto` (id), `pie` (1–9 palabras: qué se ve), `recorte` [x, y, ancho, alto] en fracciones (opcional) | Ficha con crédito (`historia.py foto`) |
| `recorte` | `medio`, `fecha`, `url`, `titular` y/o `extracto`, `resalta`, `resalta_dice` | Nota ya leída; titular igual al de la nota; extracto literal en su texto |
| `documento` | `pagina` (id de `historia.py pagina`), `titulo`, `lee`, `lee_hasta`; o `portada` {url, pagina} con `kicker`, `titulo`, `subtitulo` | La frase literal en el PDF; el PDF ya leído |
| `persona` | `persona`, `cargo` (≤ 8 palabras), `kicker` | Del elenco, o su nombre como lo dice la voz |
| `institucion` | `nombre`, `kicker` y/o `rol` (qué es, ≤ 9 palabras), `fuente` | — |
| `lugar` | `mapa: "guatemala"` + `depto` + `rotulo`; o `mapa: "mundo"` + `puntos` [{nombre}] + `ruta` | Lugar de la lista, o `lon` y `lat` |
| `fecha` | `grande` («1978»), `chico` («16 de octubre»); `estilo: "calendario"` con `arriba`, `grande`, `chico` | El año lo dice la voz |
| `cifra` | `valor` (corto: «165», «US$256 M», «4.º»), `rotulo` (de qué es), `cuenta` (entero: cuenta desde 0), `cuadros`, `fuente` | El número lo dice la voz o está en los datos |
| `termino` | `texto` (1–6 palabras), `definicion` (opcional, ≤ 16 palabras) | — |
| `cita` | `texto` (literal, como la lee la voz), `autor`, `cargo` | Las palabras se entintan mientras la voz las lee |
| `lista` | `items` [{texto, dice}] (2–6), `acento` (índice), `lazo` {dice} | — |

Cómo se usa cada una:
- **`recorte`**: es la prueba de que algo se publicó. El `extracto` es una oración literal de la nota (≤ 22 palabras; si
  recortas el principio, empieza donde empieza la idea). `resalta` es el trozo que se subraya cuando la voz dice
  `resalta_dice`. Comprueba la frase con `python3 scripts/historia.py leer "<url>" --buscar "frase"`. Si el titular habla
  de algo que el video todavía no contó, deja solo el extracto.
- **`documento`**: si la voz cita una ley, un acuerdo o un informe, muestra la página real:
  `python3 scripts/historia.py pagina <TRABAJO> --id <prefijo>-pNN --url "<url del PDF>" --frase "frase literal" --fuente "Ley …"`.
  `lee` y `lee_hasta` son las primeras y las últimas palabras que la voz lee: el marcador las sigue.
  Si la voz no lee el documento sino que lo parafrasea, deja `lee` fuera: la frase sale subrayada al entrar la página.
- **`recorte` sin `resalta`** vale. No subrayes una frase del medio sobre una oración que atribuye el dato a otro («dice
  la acusación»): parecería que lo dijo ese otro.
- **`persona`**: en su primera mención del capítulo. Sin retrato va la ficha de texto, y está bien. Un retrato nuevo solo
  con pie de foto que la nombre: `historia.py foto --retrato-de "Nombre" --retrato-evidencia "<pie>"`.
- **`lugar`**: cuando la voz nombra un lugar por primera vez o el dinero viaja (`ruta: true`).
- **`cifra`**: el `rotulo` dice de qué es el número con las palabras de la voz. Nunca una cifra sin rótulo.
- **`termino`**: una palabra clave o un remate. Úsalo poco: es la pieza más fácil y la que menos muestra.
  Con `definicion`, el término y su definición entran juntos.
- **Números y años**: valen los que dice la voz en cualquier parte del video y los de los hechos de tus escenas (el año
  de un hecho fechado puede ir en el calendario aunque la voz diga solo «el doce de enero»).
- **Tableros**: el digesto dice qué muestra ya cada uno («el tablero ya muestra») y qué oraciones no tienen paso propio
  («sin paso propio»): esas son las que necesitan un golpe tuyo.

## Recursos nuevos

- Primero lo que ya está: las fotos del digesto y las notas de cada hecho (su titular y su cita ya están verificados).
- Fotos: `python3 scripts/historia.py foto <TRABAJO> --id <prefijo>-fNN --de-fuente "<url de una nota ya leída>" --descripcion "…"`
  (su og:image, con «Foto: <medio>»), o `--commons "File:…"` (`historia.py commons "<búsqueda>"` lista las que tienen
  licencia libre). Si el hecho no tiene foto propia: `--referencia --lugar "<dónde es>"`, y el crédito dirá «Foto de
  referencia».
- Notas nuevas: `python3 scripts/historia.py leer "<url>"` (solo fuentes de la lista de la serie; mira qué dice sobre la
  fuente antes de usarla).
- La `--descripcion` dice lo que se ve, no el tema de la nota. Mira la foto con `Read` antes de usarla.

## Lo que el gate revisa (`plano --check`)

- **YT13**: cada cifra o año que dice la voz se ve en una pieza, cuando se dice.
- **YT14**: cada oración trae un golpe (una pieza, un subrayado o un paso del tablero) y ningún hueco pasa de 6 s.
- **YT15**: una foto ≤ 2 veces en todo el video, a ≥ 180 s una de otra.
- **YT16**: cada pieza con su respaldo (la tabla).
- **YT17**: ≥ 50 % de las oraciones con pieza nueva; ≥ 35 % de las piezas son archivo real (la meta es 50 %: fotos,
  recortes, documentos, mapas, retratos); ≥ 4 tipos; ≤ 2 rótulos de solo texto seguidos.
- **YT18**: la mesa dura 6–45 s y lleva ≤ 12 piezas; dos piezas no entran a menos de 0.3 s.

## Lo que el gate no ve y tú sí

- **Personas en un proceso judicial.** Una foto de una audiencia, de capturados o de alguien escoltado solo va sobre una
  oración que **nombra** a quien sale en ella. Sobre «llegó la primera condena» o sobre un cliente que perdió su dinero
  da a entender que esas personas son los condenados. Ahí va un edificio, un documento o un recorte.
- **No adelantes.** Una pieza no muestra lo que el video cuenta después (el titular de la quiebra antes de la quiebra).
- **Que no sea relleno.** Si para una oración solo se te ocurre un `termino`, busca primero la nota del hecho: casi
  siempre hay un recorte, una fecha o un lugar.
- **Variedad.** Tres fotos seguidas son un carrusel; alterna con el dato, el documento y el mapa.
- **Lo que no sabes, no lo pongas.** Ningún número, cargo o fecha que no esté en la voz, en el digesto o en una nota leída.

## Cierre (lo corre un agente al final, con todos los capítulos)

`python3 scripts/youtube.py plano <TRABAJO> --check` sin `--capitulo`: resuelve lo que queda entre capítulos (una foto
usada en dos capítulos a menos de 180 s: cambia una de las dos) editando los `plano_<N>.json`.

## Salida

Corre `python3 scripts/youtube.py plano <TRABAJO> --check --capitulo <N>` hasta 0 fallas y devuelve su línea `RETORNO`
(`{archivo, gate, fallas, piezas, archivo_real}`), más `recursos` (los ids que bajaste) y `nota` (lo que no pudiste
resolver y por qué).
