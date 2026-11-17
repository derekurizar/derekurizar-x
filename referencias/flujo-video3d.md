# /video-3d: la maqueta que vuela

Un video vertical 100 % en 3D (9:16 + 4:5, de 45 s a 3 min como los demás videos; `--duracion S`, 20–180, por defecto 45; C3D9 falla por encima de 180 s estimados o reales): un mundo simple (el relieve del país, una ciudad, una plaza)
que una cámara recorre mientras la voz cuenta, con una capa 2D encima (titular, pines que siguen al 3D, cifras,
subtítulos). Sirve cuando **el lugar o el mecanismo se entienden mejor viéndolos moverse** (2026-11-15; antes: «cuando el
lugar es la información»): una falla que cruza el país, una ruta, una cuenca, un cierre vial; o cómo se forma una cola,
cómo viaja una señal, cómo se llena un embalse (un mundo `esquema`, genérico, con el aviso «Esquema»). Si ni el lugar ni
el mecanismo lo piden, es otro flujo.

Decisiones del usuario (2026-11-14):

1. **Motores:** three.js dentro de HyperFrames para unos estilos, Blender + capa 2D de HyperFrames para otros. El
   estilo decide el motor. Remotion quedó fuera.
2. **Un estilo por mundo** (2026-11-16; antes «uno por video»): con varios mundos cada uno puede tener el suyo y cambia solo con el mundo. Lo elige el orquestador; si no está seguro
   (`estilo.confianza: "baja"`), le muestra al usuario el mismo cuadro en los dos o tres candidatos y pregunta.
3. **Dentro de la maqueta la cámara se mueve** (la excepción a la cámara quieta de la mesa de archivo).
4. **El gancho manda y todo concuerda:** lo que se ve es lo que la voz está diciendo.
5. Otros flujos (/historia, /serie, /explica, /youtube-long) pueden alojar una maqueta dentro de su mesa de archivo:
   el realizador la declara en `plano.json` y se renderiza con el **modo pieza** del motor (`maqueta3d.py pieza`, el
   mundo y sus pines en el lienzo que pida el anfitrión). Ver «La maqueta» en `referencias/flujo-mesa.md`. Una maqueta
   de escala `esquema` puede explicar un mecanismo dentro de la mesa (como una animación `explica`); lo que el catálogo
   no tiene, el realizador lo pide con un brief y el Workflow `plano` lo pasa al constructor una vez.
6. **Tantos mundos, eventos y escenas como la historia necesite** (usuario, 2026-11-15): un video puede pasar por varios
   mundos (la finca en esquema → la ruta en el mapa del país → el muelle) sin volver a uno a mitad del video (C3D13; el cierre sí puede volver al del gancho); cada mundo con su estilo si hace sentido.
   Contrato: «Varios mundos: tramos» en `referencias/diseno/maqueta3d.md`.
7. **«Maqueta · no a escala» no es obligatorio.** El aviso sale solo cuando el guion lo pide (`aviso`); el pie con las
   fuentes de los geodatos sí va siempre.

Contrato del motor: `referencias/diseno/maqueta3d.md`. Scripts: `scripts/video3d.py` (guion, voz, tiempos, audio,
entrega) y `scripts/maqueta3d.py` (gates M3D, cuadros sueltos, render).

## Pasos

| # | Paso | Comando |
|---|---|---|
| 1 | Preparar (con `--desde` reutiliza las cifras verificadas de una pieza ya investigada) | `video3d.py preparar <slug> --tema "…" --musica-tema <tema>` |
| 2 | Investigar y verificar lo que falte, incluidos los geodatos (qué se dibuja y de dónde sale) | agentes de /historia; `video3d.py datos --sumar` |
| 3 | Dirección visual por frase (idea visual, criterio, escala, estilo, mundo, el verbo del catálogo por oración); lo que falta, al constructor | Workflow `video3d`: `video3d-director` → `maqueta-constructor` |
| 3b | **Referencia visual:** un verificador por mundo de cerca (cómo se ve el lugar, qué pasa ahí, con qué; lo que no se puede afirmar) → `verificacion_visual_<mundo>.json` | Workflow `video3d`: `historia-verificador` (≤ 3 a la vez) |
| 4 | Ganchos: 5 candidatos con su cuadro renderizado; el crítico recomienda y **el usuario elige** (y el estilo, si la confianza es baja) | Workflow: `ganchos --check --cuadros` → para con `elegir_gancho` |
| 5 | Guion: la narración de corrido primero; luego las escenas y el `caption` por plataforma | Workflow: el director, `guion --check` (C3D1–C3D19, V2–V5, M3D1–M3D19) |
| 6 | Storyboard: un cuadro por clave de cámara y evento (y uno en el cruce de cada fundido), más **una hoja y la medida de cada mundo** en `escenas/`; limpia sus carpetas antes de escribir | Workflow: `storyboard` (`--sin-escenas` deja solo la hoja) |
| 7 | Crítico (retención y concordancia) y cierre: **el usuario elige el cierre** | Workflow: `video-critico` en «Modo 3D» → 5 cierres (`elegir_cierre`) |
| 7b | **Revisión de escenas:** una hoja por mundo y su medida; el crítico puntúa detalle, vida, realismo y claridad; ≤ 2 vuelve al director o al constructor. Las mejoras probadas se aplican solas | `maqueta3d.py escena --hoja` · Workflow |
| — | **Retoque visual** (la voz ya existe): cambia solo lo que se ve; lo que el crítico ve se corrige en la misma corrida (una pasada del director; `correcciones` suma lo que se vio en las hojas) y, si algo cambió, el crítico vuelve a mirar solo esos mundos (`segunda_lectura`: los puntajes del retorno son los de después de corregir). Con 5 o más mundos de cerca en `mundos`, el director trabaja de 3 en 3 | Workflow con `desde: "retoque_visual"` + `notas` [+ `mundos`, `correcciones`] |
| 8 | Voz (ElevenLabs, El Faraon 4) y escucha independiente (V11) | `voz` → MCP → `descargar --estado` (o `--nodos` si el estado llegó en el chat) → `escuchar` |
| 9 | Tiempos reales | `tiempos` |
| 10 | Render en 9:16 y 4:5 | `render` |
| 11 | Montaje: voz, música del tema con ducking, efectos, −14 LUFS; `.srt` y portada | `montar` |
| 12 | Entrega en `videos3d/<fecha>-<slug>/` y registro (M21) | `entregar` → `memoria.py --video3d <entrega>` |

## La orquestación (Workflow `video3d`, 2026-11-15)

Desde el 2026-11-15 la dirección, los ganchos, el guion y el `maqueta.json` no los escribe la sesión a mano (cerró m193):

| Fase | Quién | Qué deja |
|---|---|---|
| Dirección | `video3d-director` (opus; `referencias/roles/video3d-director.md`) | `direccion.json`: idea visual, criterio (`lugar` o `mecanismo`), escala (`pais`, `ciudad`, `esquema`), estilo con `razon` y `confianza`, mundo, borrador y **la dirección por frase**: para cada oración, el verbo visual del catálogo que la cuenta; `briefs[]` con lo que falta |
| Constructor | `maqueta-constructor` (opus; `referencias/roles/maqueta-constructor.md`), uno por brief, ≤ 3 a la vez | un módulo nuevo del vocabulario (`video/maqueta/<clase>/<tipo>.js` + ficha), probado con `scripts/maqueta_modulo.py check` (lint, pureza, hojas) y registrado; o «ya existía» |
| — | el usuario | el estilo, si la confianza es baja (`elegir_estilo`, cuadros en `estilos/<id>/`) |
| Ganchos | el director (el único que tiene el estilo, el mundo y el catálogo: más simple que darle a `video-gancho` un modo 3D) | `ganchos.json` + hojas (`ganchos --check --cuadros`) |
| Selección | `video-critico` (selección del gancho 3D) | `seleccion.json`; luego **el usuario elige** (`elegir_gancho`) |
| Guion | el director | narración, `direccion.json` final, `guion.json`, `guion --check` en 0, `storyboard`; un brief nuevo va al constructor UNA vez |
| Crítica | `video-critico` en «Modo 3D» (≤ 2 pasadas; el director corrige) | `critica.json` |
| Cierres | el director | `cierres.json` (5, cada uno probado en una copia con `guion --check`); **el usuario elige** (`elegir_cierre`) |

El vocabulario (qué se puede dibujar) **no se lista en ningún workflow ni guía**: todos leen el catálogo
(`maqueta3d.py catalogo --para sesion|realizador|critico [--escala E]`), que escribe solo `maqueta3d.py catalogo
--registrar` desde las fichas (W15 de `check_workflows.py` y `scripts/pruebas/maqueta_orquestacion.py` lo vigilan).

## A la par de los demás flujos de video

- **Caption obligatorio (V5).** `guion.caption` lleva `tiktok`, `instagram`, `facebook` y `shorts` (el título de ≤ 100
  caracteres en la primera línea y `#Shorts`), con las cifras en dígitos y sin anunciar el video. Sin él, `guion
  --check` falla y `entregar` no entrega. Las reglas son las de `video.py` (están escritas dentro de su `cmd_guion`;
  `video3d.revisar_caption` las repite con las mismas constantes).
- **Portada.** `montar` (con el 9:16) deja `salida/portada.png`: el cuadro cero del video sin subtítulos, dibujado por
  `maqueta3d.py cuadro` (`video3d.py portada <TRABAJO>` la rehace sola). Es el archivo que `caption.md` pide como
  miniatura; `entregar` falla si falta.
- **Escucha (V11).** `video3d.py escuchar <TRABAJO>` reenvía a `video.py escuchar` (whisper.cpp local: transcribe cada
  voz sin el guion y coteja las cifras). Con voz falsa no se corre.
- **9:16 y 4:5.** `entregar` falla si falta `salida/video_4x5.mp4`; `--sin-4x5` entrega solo el 9:16 a propósito.
- **Subtítulos y mezcla comunes.** El `.srt` es el de `video.texto_srt` (por oración, 2 líneas de ≤ 42 caracteres, sin
  solapes) y la mezcla, la de `youtube.mezclar_voz` + `youtube.pista_final` (la de los videos de mesa: ducking, tres
  tomas de cada efecto, fundido final de 4 s, limitador).
- **Estimación.** Los segundos estimados salen de `video.segundos_voz` (≈ 15.5 caracteres por segundo con las cifras ya
  en palabras), como en los demás flujos.
- **Rotación (G3D2).** La familia del gancho de los últimos 2 videos 3D (`memoria/videos3d.json`) queda marcada «NO
  REPETIR» en el digesto; `ganchos --check`, `ganchos --usar` y `guion --check` avisan si se repite (aviso, no falla).
- **Rendimiento real.** El digesto trae lo medido con `/analyze-improve` (retención por familia, visual, cierre y tramo
  de duración). `metricas.py alinear <slug>` cruza la curva con las escenas del video 3D: usa el `tiempos.json` que
  `entregar` copia a la entrega (o las palabras de `maqueta.json`) y dice qué eventos y cuántas claves de cámara caen
  en cada escena.
- **Pruebas sin render:** `python3 scripts/pruebas/ola1_video3d.py` (los 22 negativos M3D del motor y lo de esta lista).

## La idea visual

Antes de escribir una palabra, una oración: **qué imagen es el video**. De ahí salen el gancho, el estilo, lo único
que va en acento (`protagonista`) y el cierre. Ejemplo: «La falla es lo único encendido: una grieta naranja que
cruza el país a oscuras». Si la idea visual no se puede decir en una oración, el video todavía no existe.

## El estilo (uno por video)

| Estilo | Motor | Cuándo |
|---|---|---|
| `noche` | three.js | De noche, o temas oscuros (desastre, crimen, cortes de luz); una sola cosa encendida. Es el más cercano a la marca |
| `color` | three.js | Lugares de día que se reconocen por sus colores (Antigua, un mercado, una fiesta) |
| `plano` | three.js | Infraestructura y mecanismos: redes, tuberías, cómo funciona algo |
| `contorno` | three.js | Historias con personajes y tono de ilustración |
| `voxel` | three.js | Tono ligero; pierde el detalle de los monumentos |
| `arquitecto` | Blender | Explicar un espacio: todo blanco y solo el protagonista en color |
| `diorama` | Blender | Un solo lugar aislado (un volcán, un lago); no sirve para vuelos largos |
| `papel` | Blender | Historia y efemérides, tono de libro ilustrado |

`estilo` lleva `id`, `razon` (por qué ese y no otro, atado a la idea visual) y `confianza` (`alta` o `baja`).

**Con `plano`, se pregunta por las capas** (usuario, 2026-11-15): junto con el estilo, muestra el mismo cuadro con todas
las capas y en versión limpia (`mundo.capas`: sin `curvas` de nivel ni `batimetria`; la `reticula` de paralelos y
meridianos se puede apagar también) y pregunta cuál quiere. Las curvas de nivel se amontonan en la sierra y ensucian el
cuadro cuando la cámara se aleja.

**Los vecinos:** `{"tipo": "frontera", "vecinos": true}` dibuja además los bordes y la costa de los países de alrededor
(Natural Earth, ya en el set). Úsalo cuando el video sale del país o habla de una frontera.

## El gancho en 3D

El gancho es **un evento en el segundo cero**, no un vuelo vacío: algo se rompe, cae, se enciende, se apaga o se
revela. Reglas (además de R1–R14 de `referencias/ganchos.md` en lo que aplica):

- La escena 1 lleva un evento sin `dice` (empieza en el cuadro 0) y una clave de cámara sin `dice`.
- La voz del gancho dura ≤ 6 s y es una oración con verbo; «Guatemala» se oye antes del segundo 6. Un año dicho en
  palabras cuesta dos segundos: el año va en el kicker, no en la voz del gancho.
- El titular hace que el cuadro 0 se entienda sin sonido.
- Lo que el gancho enciende es el protagonista del video: el cierre vuelve a él (el bucle).

Familias de gancho 3D (los 5 candidatos son de familias distintas):

| Familia | El evento del segundo cero |
|---|---|
| `ruptura` | Algo se rompe o se abre ante la cámara |
| `caida` | La cámara cae en picada desde el país entero hasta un punto |
| `revelacion` | Algo oculto se enciende o aparece sobre lo conocido |
| `escala` | Una longitud o un área crece sobre el mapa hasta que se entiende su tamaño |
| `contraste` | Dos estados del mismo lugar: se apaga uno y queda el otro |
| `recorrido` | Un trazo sale de un punto y la cámara lo persigue |

## El guion (`guion.json`)

```json
{
  "tipo": "video3d", "version": 1,
  "idea_visual": "…",
  "estilo": {"id": "noche", "razon": "…", "confianza": "alta"},
  "protagonista": "motagua",
  "mundo": {"set": "guatemala", "exageracion": 5, "lugares": {}, "piezas": [{"id": "motagua", "tipo": "falla", "trazos": ["Motagua Fault"]}]},
  "narracion": "la voz de corrido, como se escribió antes de repartirla",
  "escenas": [
    {"n": 1, "tipo": "gancho", "acto": 1, "secuencia": 1,
     "texto": "la voz de esta escena, con las cifras en dígitos",
     "titular": {"kicker": "4 DE FEBRERO DE 1976", "texto": "…"},
     "camara": [{"mira": "los-amates", "dist_km": 520, "azimut": 0, "elevacion": 62},
                {"dice": "frase", "al": "fin", "mira": [-90.2, 14.9], "dist_km": 200, "azimut": -20, "elevacion": 40}],
     "eventos": [{"tipo": "ruptura", "pieza": "motagua", "desde": "los-amates", "hacia": "oeste", "km": 230, "dur": 2.6, "sfx": "grave"}],
     "marcas": [{"dice": "Los Amates", "lugar": "los-amates", "texto": "Los Amates, Izabal", "sub": "Epicentro", "hasta": 3}],
     "cifras": [{"dice": "7.5", "valor": "7.5", "rotulo": "de magnitud", "cifra": "noche-c09", "fuente": "INSIVUMEH"}]},
    {"n": 6, "tipo": "cierre", "acto": 3, "texto": "…", "final": "la frase que queda en pantalla", "camara": [{"al": "fin", "mira": "los-amates", "dist_km": 520, "azimut": 0, "elevacion": 62}]}
  ],
  "caption": {"tiktok": "…", "instagram": "…", "facebook": "…", "shorts": "…"}
}
```

- **Varios mundos:** en vez de `mundo`, `"mundos": {"finca": {…}, "pais": {…}}`, y cada escena dice el suyo
  (`"mundo": "finca"`); la primera escena de un cambio puede llevar `"transicion": "corte|fundido|oscuro"` y `fundido_s`.
  Las escenas seguidas del mismo mundo forman un tramo. Sin `mundos`, un solo mundo como siempre.
- **Cambio de mundo a mitad de una escena** (2026-11-16): `"cambios": [{"dice": "Y en una cafetería", "mundo": "ciudad",
  "transicion": "fundido"}]`. Desde esa frase la escena sigue en el otro mundo: cada cámara, evento, marca y anotación va
  al mundo vivo en su `dice` (sin `dice`, al del inicio; con `al: "fin"`, al del final). Sirve cuando una sola oración
  pasa por dos lugares (la tostaduría y luego la calle con la cafetería) sin regrabar la voz. C3D12 revisa que la frase
  se diga y el mundo exista; C3D13 cuenta el cambio como un mundo más.
- **Primero la narración de corrido** (≈ 15.5 caracteres por segundo: 45 s ≈ 700 caracteres), como una sola voz;
  después se reparte en escenas sin cambiar una palabra. `secuencia` agrupa las escenas cuya voz se graba de corrido.
- **Anclas:** `dice` es una frase de la voz de esa escena (escrita como en `texto`; `vez: 2` si se repite). Sin
  `dice`, el elemento nace al empezar la escena. `al: "fin"` lo pone al terminar la frase (o, sin `dice`, al terminar
  la voz de la escena).
- **`caption` es obligatorio** (V5): un texto por plataforma; ver «A la par de los demás flujos de video».
- **Cámara:** cada clave es el encuadre al que la cámara **llega** en ese momento; el vuelo ocurre entre claves. Una
  clave con `al: "fin"` hace que el vuelo dure toda la escena.
- **Marcas y cifras:** viven hasta el final de su escena, o `hasta: N` (el final de la escena N), `hasta_dice` o
  `dura` (segundos). Las cifras llevan `cifra` (el id verificado), `rotulo` y, si salen de una sola fuente, `fuente`.
- **Eventos:** `dur` en segundos o `hasta_dice`; `sfx` es un id de `design/sfx/catalogo.json`.

## Concordancia: gates C3D (`video3d.py guion --check`)

| Gate | Qué revisa |
|---|---|
| C3D1 | Un estilo con su razón (y nadie más declara estilo), la idea visual, el protagonista, 4 escenas o más (tope: ≈ una cada 7 s del objetivo, y nunca menos de 9), gancho primero y cierre al final |
| C3D2 | Cada `dice` y `hasta_dice` es una frase que la voz de esa escena dice |
| C3D3 | Cada lugar que la voz nombra tiene su marca (en esa escena o viva de antes) o es adonde mira la cámara; las marcas y la cámara usan lugares que existen |
| C3D4 | Cada cifra entra cuando la voz la dice, con su id verificado y su rótulo; la de una sola fuente lleva la fuente |
| C3D5 | Cada número que se lee en pantalla tiene respaldo (como V2 para la voz) |
| C3D6 | El gancho: evento y cámara en el cuadro cero, voz ≤ 6 s, «Guatemala» en ≤ 6 s, titular |
| C3D7 | Ritmo: aviso a los 6 s sin nada nuevo en pantalla; falla a los 9 s |
| C3D8 | El cierre: frase final corta, sin anunciar el final, sin «sígueme» ni fuentes en la voz, ≤ 160 caracteres |
| C3D9 | Duración estimada dentro del objetivo ±20 % |
| C3D10 | El cierre lleva su cámara; aviso si no vuelve a mirar lo que abrió el gancho (el bucle) |
| C3D12 | Varios mundos: cada escena dice un mundo de `mundos` (y no hay `mundo` a la vez), la `transicion` es `corte`, `fundido` u `oscuro`, y todo mundo se usa |
| C3D13 | No se vuelve a un mundo a mitad del video (solo el cierre puede volver al del gancho) |
| C3D14 | **La ficha de escena:** cada mundo de cerca (`esquema`, `ciudad`) trae `escena: {que_pasa, quien, con_que, se_mueve, sostiene[]}`: lo que ocurre ahí en la realidad, quién lo hace, con qué y qué se mueve en pantalla |
| C3D15 | **Realidad:** cada entrada de `escena.sostiene` es `{que, hecho: <id verificado>}` o `{que, generico: true}`; si todo es genérico, `escena.ilustrativa` dice por qué (un mecanismo, un lugar cualquiera) |
| C3D16 | **Se explica:** al entrar a un mundo de cerca, un titular o una marca dice dónde estamos en los primeros 3 s |
| C3D17 | **Gente:** si `escena.quien` nombra personas, en la escena hay ≥ 2 haciendo algo (objetos con `gente`, piezas con `personas`) |
| C3D18 | **Un objeto, un papel:** el mismo objeto no se rotula como dos cosas distintas (la casa no es beneficio, bodega y tostador) |
| C3D19 | **La hora:** `mundos.<id>.hora` (`amanecer`, `dia`, `atardecer`, `noche`) distinta del día lleva `hora_razon`; un salto de hora entre escenas de cerca seguidas entra con `oscuro` o lleva `salto_hora` (la frase de la voz) |
| C3D11 | Un pin cuyo texto dice una distancia («A 25 km») declara `separada_de` con la pieza de la que está a esa distancia: M3D11 mide que en pantalla no queden pegados |

Los gates M3D (dónde cae cada pin, velocidad de la cámara, tiempos de lectura, separación, en 9:16 y 4:5) los corre
`maqueta3d.py check` sobre `maqueta.json`, al final de `guion --check` y de `tiempos`.

## Verdad

- El pie nombra siempre las fuentes de los geodatos (las licencias lo piden). En un video con tramos sale solo
  mientras se ve un mapa: un mundo `esquema` no usa geodatos y su tramo no lo lleva (`pie_ventanas`). El aviso (`aviso` en el guion) es
  opcional: úsalo cuando el dibujo simplifica algo que el espectador podría tomar al pie de la letra («Traza
  esquemática», «Maqueta · no a escala»); no va por costumbre en todos los videos (usuario, 2026-11-14).
- **Lo que se dibuja también se afirma.** Un trazo, un extremo, una dirección o un alcance se dibujan solo si un
  hecho verificado los sostiene (con su cita guardada); lo que las fuentes no sostienen va en `no_afirmar` y no se
  dibuja. Una cámara rasante puede pegar dos cosas que están lejos, una onda puede dibujar una hipótesis como un
  hecho y unas flechas largas dicen que todo ese tramo se movió: se revisa en el storyboard.
- Los geodatos se verifican como las cifras: qué tramo, de dónde a dónde, hacia dónde, con su fuente guardada (el USGS,
  la NOAA y la NASA cuentan como oficiales en `historia.py leer`).
- **El esquema no es un lugar.** Un mundo de escala `esquema` (una ciudad, una carretera, el campo, la costa o una plaza
  hechos por una receta; `referencias/diseno/maqueta3d.md` § «Mundos») sirve para mostrar un MECANISMO (cómo se forma una
  cola, cómo cruza una autopista), no para afirmar geografía: lleva «Esquema» en el aviso y sus lugares y marcas usan
  nombres genéricos (centro, plaza, entrada), nunca el de un lugar real (M3D12). Si la historia pasa en un lugar real, el
  mundo es `ciudad` (un set con sus calles y edificios de OpenStreetMap, que el pie nombra) o `pais`.
- Ninguna cifra ni texto dentro del 3D: van en la capa, donde los gates los revisan.
- Personas: muñecos sin rostro; nunca el parecido de una persona real.

## Crítico en «Modo 3D»

El `video-critico` tiene su modo 3D en `referencias/roles/video-critico/3d.md` (3C1–3C8: el cuadro
cero, la concordancia, un protagonista, el estilo, lo dibujado también se afirma, el bucle, quien no sabe nada y lo que
se lee tres veces). Prueba cada arreglo en una copia del TRABAJO antes de proponerlo.

## Lo aprendido en el piloto (terremoto de 1976, 2026-11-14)

- Un año dicho en palabras cuesta dos segundos de voz: va en el kicker.
- El cuadro cero es la portada: el titular y el evento se ven desde `t = 0`.
- La voz tiene que nombrar el hecho («el terremoto»), no solo sus piezas (la falla, el epicentro).
- Con la voz real los tiempos se mueven: `tiempos` vuelve a correr los gates M3D y a veces hay que ajustar una clave de
  cámara o la duración de un titular, sin tocar la voz.

## Costos (medidos el 2026-11-14 en un M4 Max)

- Voz: ≈ 1 crédito por carácter (45 s ≈ 700 créditos).
- Render three.js en HyperFrames: ≈ 1.7× la duración por formato (45 s ≈ 80 s; 3 min ≈ 5 min por formato).
- Con mundos de cerca llenos y sombras reales (el café, 2026-11-16: 112 s en 9 tramos): 1.7–2.1 s por segundo de video
  en cada tramo y, con el encadenado y la placa de la capa, 402 s en 9:16 y 313 s en 4:5 (≈ 3.6× y 2.8× la duración).
  El mismo video sin sombras y con 6 tramos tardaba 331 s y 222 s: el detalle y las sombras cuestan ≈ +20–40 %.
- Render Blender (`arquitecto`, `diorama`, `papel`): 0.5–0.85 s por cuadro de placa más ≈ 5 s de capa 2D por segundo
  de video: un video de 45 s tarda ≈ 16–22 min por formato (3 min ≈ 65–90 min por formato) (12–16 veces más que three.js). Elige un estilo de Blender
  cuando la forma o la luz lo valgan, no por costumbre. La primera vez, Cycles compila sus kernels (≈ 3.5 min).
- Un cuadro suelto de three.js: segundos (por eso los ganchos y el storyboard se ven antes de la voz).
- **Límite del render:** 600 s + 40 s por segundo de video (un render 3D va a ≈ 2–4× la duración); si lo pasa se detiene con
  todos sus procesos y dice dónde está el registro. `MAQUETA_RENDER_LIMITE_S=<segundos>` lo sube en una máquina lenta.
- **El pie se arma solo con lo que el video dibuja** (las capas de sus mundos, agrupadas por fuente); `guion.pie` lo fija
  a mano cuando hay una fuente propia (una traza, un tratado).
- **La carpeta de entrega lleva la fecha de la entrega**; volver a entregar el mismo video reutiliza su carpeta.
- `memoria/videos3d.json` guarda `estilos` y `por_mundo` (estilo y hora de cada mundo).
