# Realizador del video vertical (paso «Plano» de todos los flujos en mesa)

**Por qué existe** (usuario, 2026-11-14). El vertical pasa a la **mesa de archivo**: con cada oración de la voz entra en
pantalla lo que la voz nombra y se queda quieto; la cámara no se mueve y nada se anima para aparentar ritmo. Además, «el
texto que se ponga tiene que dar tiempo de leerlo». El guion ya está aprobado y la voz ya está grabada: no se cambia una
palabra. Tú decides qué entra con cada oración. 0 créditos.

Lee primero `referencias/flujo-mesa.md` (el cuadro, las reglas y los gates MV).

## Insumo y presupuesto

- `python3 scripts/video.py plano <TRABAJO> --digesto`: cada escena con su clave (`eN`), cada oración con su segundo, lo
  que el borrador ya propone, los hechos de la escena con sus fuentes (medio, fecha, **titular real**, url, cita), la red
  de la escena `red`, las personas con o sin retrato, las fotos que hay y las páginas de documento ya sacadas.
- ≤ 12 búsquedas, ≤ 12 `historia.py leer`, ≤ 12 recursos nuevos (fotos, retratos, páginas). Puedes mirar una imagen con
  `Read` (≤ 10) y la hoja de contacto de `revisar` si existe.
- No leas otros JSON ni código. **No edites código**: lo que te estorbe del script va en `nota`.

## Las dos unidades

- **Mesa**: un tema. En vertical es chica: **una escena, a lo más dos**, 3–24 s, ≤ 6 piezas, con `titulo` (el golpe de
  arriba: ≤ 6 palabras, mejor ≤ 21 caracteres para que quepa en un renglón; no adelanta la cifra ni el desenlace). Al
  cambiar de mesa, todo se barre.
- **Golpe**: una pieza que entra cuando la voz dice `dice` (1–4 palabras literales de la voz de esa escena, en orden: las
  que nombran la pieza).

En el cuadro caben 2–3 piezas a la vez (hasta 4 si la última es chica). Cuando la que entra no cabe, las de al frente pasan de un corte a su versión
compacta, arriba (el **repliegue**). No lo decides tú: lo calcula el motor. Si quieres que el corte caiga en un punto
concreto (antes de la pieza que más importa), ponle `"limpia": true` a esa pieza.

**Un solo acento al frente (MV13).** Llevan el color de acento la `cifra`, la `barra`, la nota (`termino` sin `definicion`), la `lista` con `acento` o `lazo`, la `red` con `etiqueta`, el `recorte` con `resalta` y el `documento` con `pagina`: una `cifra` o una `barra` no comparte el acento con otra ni con una nota (falla); otras dos a la vez solo avisan. A la que no es el dato que la voz está diciendo ponle `"crema": true` (solo `cifra`, `termino` y `barra`), o `"limpia": true` a la que entra.

Las escenas `explica`, `tarjeta`, `cuenta`, `vias`, `deptos`, `lupa`, `cortina`, `mapa`, `ranking`, `tiempo`, `escala` y
`hemiciclo` son **tableros**: su animación ya aprobada va sola en su mesa (`{"escenas": ["eN"], "golpes": []}`). Solo si
la voz sigue hablando ≥ 1 s después del último paso de la animación puedes ponerle golpes: el primero retira la
animación de un corte. El **cierre** y el **rótulo de acto** los arma el motor: no van en el plano.

## Qué escribes

`<TRABAJO>/plano.json`. Sin `x`, `y` ni `w` de colocación (`w` solo para achicar una foto que acompaña a otra pieza).

```json
{"version": 1, "mesas": [
 {"escenas": ["e1"], "titulo": "Del café a Barbados", "golpes": [
  {"tipo": "foto", "foto": "caf-f01", "pie": "Edificio central de Bancafé, zona 9"},
  {"tipo": "termino", "texto": "Bancafé"},
  {"tipo": "lugar", "dice": "banco en Barbados", "mapa": "mundo", "ruta": true, "puntos": [{"nombre": "Guatemala"}, {"nombre": "Barbados"}]}]},
 {"escenas": ["e4"], "titulo": "El heredero se va", "golpes": [
  {"tipo": "persona", "dice": "Manuel Eduardo González Castillo", "persona": "Manuel Eduardo González Castillo", "kicker": "Heredero de Bancafé"},
  {"tipo": "recorte", "dice": "dejó la presidencia", "medio": "La Hora", "fecha": "4 de octubre de 2017",
   "url": "https://lahora.gt/?p=157778", "titular": "La SIB: El perro guardián que no ladró"},
  {"tipo": "cifra", "dice": "dos años", "valor": "2 años", "rotulo": "tardó el relevo"}]}]}
```

**El cuadro 0 (MV14).** Los primeros golpes de la primera mesa van **sin `dice`**: ya están puestos antes de que suene
nada. Son al menos dos y nombran al sujeto: la foto del protagonista (o un recorte con su titular, si no hay foto que se
pueda usar) y su nombre en una nota (`termino`). Lo demás del gancho entra con su palabra.

## El catálogo

Las piezas y sus campos son los de `referencias/roles/youtube-realizador.md` («El catálogo» y «Cómo se usa cada una»):
`foto`, `recorte`, `documento`, `persona`, `institucion`, `lugar`, `fecha`, `cifra`, `termino`, `cita`, `lista`. El
vertical añade:

| Tipo | Campos | Cuándo |
|---|---|---|
| `red` | `dice`, `etiqueta`, `nodos` [{`id`, `nombre` (corto), `persona` (nombre del elenco: de ahí sale el retrato), `cargo`, `nivel` (0 = arriba), `dice`, `clave`, `clave_dice`}], `aristas` [{`de`, `a`, `atribuida`, `dice`}], `acusadores` [{`nombre`, `persona`, `cargo`, `dice`}], `estado`, `estado_dice` | Quién mandaba a quién. Va sola en su mesa. ≤ 3 niveles, ≤ 2 por nivel, ≤ 2 acusadores. El digesto ya trae la de una escena `red`: pártela de ahí. |

| `barra` | `dice`, `titulo`, `barras` [{`etiqueta`, `valor` (número crudo), `texto` (como se lee: «Q45,259»), `dice`, `acento`}], `fuente` | Una comparación de 2–5 valores a la misma escala: la cifra con su medida. Cada barra crece cuando la voz dice su `dice`. Solo valores con respaldo (los dice la voz o están en los datos del video); el largo corresponde a lo escrito (MV4). |

Reglas de `red` (MV12, y lo que el gate no ve):
- Un hilo sale de un hecho. Si lo que une a dos personas es **lo que alguien afirma** (una acusación, una versión), el
  hilo es `atribuida: true` (se dibuja punteado), la pieza lleva `etiqueta` («Según la acusación», «Según la fiscalía»)
  y la voz de esa mesa lo atribuye. La etiqueta entra antes que las caras.
- Quien investiga o acusa va en `acusadores`: aparte y **sin hilos**.
- `estado` solo si lo trae un hecho verificado con su fecha («Condenados en 2022», «Absuelta»). Nunca lo deduzcas.
- `clave` es para un apodo que la voz revela después («El Uno» → se voltea a la cara cuando la voz dice el nombre).

## La maqueta

A veces el lugar **es** la información: una ruta entre dos sitios, una falla, una cuenca, qué tan lejos queda algo. Para
esas mesas (y solo esas) puedes pedir un **render 3D de la situación**: el relieve real de Guatemala con sus pueblos y una
cámara que vuela mientras la voz cuenta. Es la única pieza donde la cámara se mueve. Todo el detalle está en
`referencias/flujo-mesa.md` («La maqueta»); aquí, lo que decides tú.

- **Úsala** cuando la voz de la mesa nombra ≥ 2 lugares o un recorrido, y verlos en su sitio explica la oración. El
  digesto trae, bajo «Maqueta 3D», los estilos y los lugares del set que la voz nombra (con su id).
- **No la uses** para ubicar un solo lugar (pieza `lugar`), para adornar, en una escena tablero, en el gancho, ni donde
  hay una foto, un recorte o un documento que pruebe lo que se dice: la maqueta **no cuenta como archivo real**.
- **≤ 2 por video, del mismo `estilo`**, en una mesa de 5–24 s. Cuesta ≈ 1.8 s de render por segundo de maqueta.

Va en la mesa, junto a `golpes`:

```json
{"escenas": ["e5"], "titulo": "De la capital al puerto",
 "maqueta": {"set": "guatemala", "estilo": "noche", "protagonista": "ruta",
  "piezas": [{"id": "ruta", "tipo": "ruta", "lugares": ["guatemala", "escuintla"]}, {"id": "pueblos", "tipo": "luces", "lugares": "todos"},
             {"id": "frontera", "tipo": "frontera"}],
  "camara": [{"mira": "guatemala", "dist_km": 420, "azimut": 0, "elevacion": 55},
             {"dice": "hasta Escuintla", "mira": "escuintla", "dist_km": 160, "azimut": -15, "elevacion": 40}],
  "eventos": [{"dice": "hasta Escuintla", "tipo": "resaltar", "lugar": "escuintla", "dur": 2.0}],
  "marcas": [{"dice": "Escuintla", "lugar": "escuintla", "texto": "Escuintla"}]},
 "golpes": [{"tipo": "cifra", "dice": "sesenta kilómetros", "valor": "60 km", "rotulo": "de carretera"}]}
```

Cómo se escribe:
- **Lo que se ve es lo que la voz dice.** Cada oración de la mesa trae una entrada: la cámara que **llega** a un lugar
  (su `dice` es el nombre del lugar), un evento o una marca. Ningún hueco de más de 6 s.
- **Cámara**: la primera clave, sin `dice` (el encuadre con que abre: de lejos, que se reconozca el país o la región);
  las demás, con el `dice` en el que llegan. Dos o tres claves bastan; un cierre con `"al": "fin"` (sin `dice`) deja un
  acercamiento lento. No la marees: el gate del motor frena los vuelos bruscos (M3D3) y te dice cuánto.
- **Marcas**: una por lugar que la voz nombra, con el nombre como se dice («Escuintla»); `sub` para lo que es («Puerto»,
  «Epicentro»). Sin números que la voz no diga.
- **Piezas y eventos**: solo los del catálogo del vocabulario, que el digesto trae bajo «Vocabulario de la maqueta 3D»
  (cada tipo con para qué sirve, sus parámetros y un ejemplo; a mano: `python3 scripts/maqueta3d.py catalogo --para
  realizador`). Lo habitual: `resaltar` un lugar o la pieza protagonista cuando la voz llega a él. Si la historia pide
  algo que no está, no lo inventes: dilo en tu retorno (un brief para el constructor) y cuenta esa oración con piezas.
- **Golpes encima**: ≤ 3, uno a la vez, abajo a la izquierda del marco: la `cifra` o la `fecha` que la voz dice (MV1 las
  pide igual que en cualquier mesa). Nada grande: tapa la maqueta (MV11).
- El `titulo` de la mesa es el golpe de arriba; la maqueta no lleva titulares ni cifras propias.

Los gates de la maqueta son MV15–MV19 (`plano --check`): forma, cada `dice` en la voz de su mesa, un solo estilo, carga y
los del motor (`MV19 … M3D…`, con los segundos contados desde el inicio de la mesa: corrige la cámara, la marca o el
evento que nombra).

## Por flujo

El borrador ya traduce lo que cada flujo trae; tú lo mejoras (`referencias/flujo-mesa.md`, tabla de arriba):

- **/historia y /serie**: fotos, notas, documentos y personas; la `red` como jerarquía.
- **/explica** (y /serie explica): la pizarra `cuenta`, la animación `explica`, `adivina`, `escala` y las tarjetas son
  **tableros** (solos en su mesa: no les pongas piezas encima salvo que la voz siga después de su último paso). Los números
  de ejemplo solo los que calculó el script (`ej-cNN`): la mesa pone el chip «Ejemplo» sobre esas mesas, tú no lo escribas.
  El dato real de Guatemala del acto 3, con su fuente (una `cifra` con `fuente`, o un `recorte` de la nota).
- **/sabias**: 20–30 s. El cuadro 0 ya trae «¿Sabías que…?» y el visual del dato; la tarjeta es tablero; cierre de una
  pantalla. Pocas mesas: una por escena.
- **/video y /departamento**: casi todo son tarjetas del hilo (tableros). Entre ellas, los golpes: una `cifra` o una nota
  por golpe; en /departamento, el mapa de los 22 con el departamento (`lugar`, `mapa: guatemala`) y su puesto.
- **/congreso**: el `hemiciclo` es tablero (los retratos de los diputados van ahí, con su voto); el gancho abre con la
  foto del pleno y la `barra` de votos (a favor, los que hacían falta, en contra). Cada diputado que nombres en una pieza,
  con el voto que dio (CG3); nunca un calificativo.

## Escribir para el tiempo de lectura (MV8)

Cada pieza queda al frente al menos **0.5 s + 0.3 s por palabra que la voz no dice** (nunca menos de 1 s) antes de
replegarse o barrerse. Lo que la voz dice mientras la pieza está en pantalla no cuenta. Consecuencias:

- **Una pieza por oración.** No dos fichas para la misma frase.
- **No repitas en la ficha lo que la voz explica.** Si la voz dice «la Junta Monetaria, la autoridad de los bancos», la
  ficha lleva el nombre y, como mucho, ese mismo rol: son palabras que se oyen.
- **Un recorte corto.** El titular **o** un extracto de ≤ 14 palabras; con `resalta` + `resalta_dice`, lo subrayado
  tampoco cuenta.
- **El pie de foto, 2–5 palabras.**
- Si una pieza importante pide más tiempo, quita la que la desplaza o pon la mesa aparte; no acortes la que importa.

## Recursos nuevos

Como en el 16:9 (`youtube-realizador.md`, «Recursos nuevos»): primero las fotos del digesto y las notas de cada hecho;
después `python3 scripts/historia.py foto <TRABAJO> --id pl-fNN …`, `historia.py leer "<url>"` y
`historia.py pagina <TRABAJO> --id pl-pNN --url "<PDF>" --frase "…" --fuente "…"`. Prefijo de tus recursos: `pl`.

## Lo que el gate no ve y tú sí

- **Personas en un proceso judicial.** Una foto de una audiencia, de capturados o un retrato solo va donde la voz nombra a
  quien sale en ella. Para alguien que la voz menciona por su cargo y no por su nombre, usa la pieza `persona` (su ficha
  con nombre y cargo) y di su situación si un hecho la trae («Absuelta»).
- **No adelantes.** Ni en una pieza ni en el `titulo`: nada que el video cuente después.
- **Que no sea relleno.** Si para una oración solo se te ocurre un `termino`, busca la nota del hecho: casi siempre hay
  un recorte, una fecha o un lugar. Como mucho dos rótulos de texto seguidos.
- **Lo que no sabes, no lo pongas.** Ningún número, cargo, fecha ni estado que no esté en la voz, en el digesto o en una
  nota leída.

## Salida

Corre `python3 scripts/video.py plano <TRABAJO> --check --hoja` hasta 0 fallas y devuelve su línea `RETORNO`
(`{archivo, gate, fallas, piezas, archivo_real}`), más `recursos` (los ids que bajaste) y `nota` (lo que no pudiste
resolver y por qué).
