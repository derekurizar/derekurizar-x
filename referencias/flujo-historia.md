# Flujo `/historia` — índice

Un **evento o una historia de Guatemala contada de principio a fin** en un video vertical (1080×1920, 30 fps) de
**2–3 min** (objetivo 150 s, tope 180 por YouTube Shorts) para TikTok, Reels y Shorts, más su 4:5 para el feed. Sirve
para cualquier historia que se narre: cómo llegó una marca, cómo nació una empresa, la vida de un presidente, por qué
el país exporta café, un caso de justicia desde que se descubrió hasta hoy. No tiene modos: el editor nombra el arco
que le toca a cada una. Misma línea que `/video`: voz El Faraon 4 con las cifras en palabras, música y efectos de los
catálogos fijos, barra de progreso, subtítulos, zona segura (V13), 9:16 + 4:5, caption por plataforma, cierre con
**«Sígueme en»**. La publicación es manual.

```
preparar (historia.py: TRABAJO = sesiones/historia-<slug>/, paleta provisional y música)
→ Workflow historia [historia-editor → encuadre.json (pregunta, arco, 3–5 capítulos, 2–3 ejes, paleta, sensibles)
                     → historia-investigador por eje (en paralelo) → hallazgos_<eje>.json
                     ⇢ historia-verificador por eje (pipeline: verifica en cuanto su investigador termina): segunda
                       fuente por hecho, fechas en conflicto, estado actual de los casos, fotos con licencia
                       (historia.py foto) → verificacion_<eje>.json → gate hechos --check (H1–H3, H7)
                     → consolidar → historia.json (cronología) + base/ (hilo.json, datos.json) + la paleta del encuadre
                     → video-gancho en modo historia (4–5 candidatos) → gate ganchos --check → video-critico elige
                     → historia-guionista (ganchos --usar → guion.json) → gate guion --check (H3–H8 + V1–V5, V9, F1–F8)
                     → video-critico en modo historia (≤ 2 vueltas con el guionista; con «pasa», el guionista aplica
                       sus mejoras, también las de voz, y repasa el gate, sin otra crítica)
                     → video-animador por cada escena explica sin animación (reusa o crea y registra en la biblioteca)]
→ QA de fotos (historia.py fotos-contacto) → [sin-voz: voz-falsa] | voz (MCP ElevenLabs, como /noticias)
→ tiempos (V6, V10) → escuchar (V11) → grabar (V7, V13) → montar (V8) → revisar (9:16 y 4:5)
→ entregar (historias/<fecha>-<slug>/) → memoria.py --historia (memoria/historias.json) → make validate (M10)
```

`scripts/historia.py` hace lo propio de la historia y escribe el **mismo TRABAJO que `/video`**: arma en
`TRABAJO/base/` un «hilo base» (`hilo.json` con el tema y la tesis, `datos.json` con las cifras y los números de los
hechos verificados, y las tarjetas `tuit_N.html` materializadas con `scripts/materializar.py` desde el `grafico` de
cada escena), así el gate del guion, los ganchos, los tiempos y el render salen de `scripts/video.py`, con las escenas
propias enchufadas por sus extensiones (`CONSTRUCTORES`, `TRANSICION_DE`, `SIN_HUECO`). Las páginas son
`video/noticia.html` (gancho con foto y escena `foto`), `video/historia.html` (`cita` y `capitulo`) y las de `/video`
para el resto.

## Formato (decisiones del usuario, 2026-10-24)

| Bloque | Qué | Gate |
|---|---|---|
| E1 gancho (≤ 7.5 s) | el momento más fuerte, en medias res; se lee en silencio; «Guatemala» en ≤ 6 s; sin «Esta es la historia de…» | `ganchos --check` (R1–R9, R11–R12; sin R10) |
| promesa | una oración propia en la escena 2 que nombra qué falta saber; se paga en el último tercio | V9 |
| 3–5 capítulos | cada uno abre con `capitulo` (el año grande que cuenta desde el anterior + ≤ 4 palabras) y trae 1–4 escenas; termina en un giro o una pregunta | H8 |
| giro | una escena con `giro: true` entre el 40 y el 75 % | H8 |
| cierre | `cierre.html` en dos pantallas (rótulo «Lo que dejó» + 2–3 líneas, luego el remate) y «Sígueme en» | F1–F8 |

**Escenas**: `foto` (la foto de archivo en marco con Ken Burns, chip con fecha y lugar, titular, cifra opcional,
fuente y «Foto: autor · licencia»), `cita` (la frase literal de una persona, o de un documento con su membrete y un
resaltador; una cita en otro idioma lleva `traduccion`, en pantalla bajo la frase y dicha por la voz), `capitulo`, `tarjeta`/`mapa`/`ranking`/`tiempo` (un gráfico de las 26 plantillas de
`templates/graficos/` con su `DATA`), `golpe`, `definicion`, `escala`, `explica` (una animación de la biblioteca
`video/animaciones/`: `cadena`, `cronologia`, y las que el animador vaya creando) y `cierre`. Nunca tres seguidas del
mismo tipo. ≤ 19 escenas más el cierre (20 nodos de voz: el tope de ElevenLabs por llamada).

## Reglas de verdad

- Solo hechos `confirmado` (dos fuentes de grupos distintos: un documento oficial, la academia, el archivo o la
  empresa para su propia historia, y otra que lo respalde) o `en_disputa` (una fuente o fuentes que difieren en un
  detalle: la voz **atribuye o matiza**). Una cifra confirmada vale también con una fuente oficial o académica.
- Cada fuente con su texto guardado (`historia.py leer`: HTML, PDF o Wayback) y la cita literal dentro; la cita de un
  hecho trae su **año** y cada número del texto. **Wikipedia no cuenta**: es el mapa para llegar a sus referencias.
- **Qué fuentes cuentan** (`clasificar`, lista cerrada; `leer` avisa «NO CUENTA» al guardar):
  - oficial: gob.gt, MP, CICIG, organismos;
  - medio: la lista de `/noticias` más prensa internacional y de negocios (Forbes, E&N, Bloomberg y Bloomberg Línea,
    NYT, El País, Axios, Chicago Tribune…), un grupo por casa editorial;
  - **agencia**: una nota firmada por AP, EFE, Reuters o AFP («(AP)», «Por/By Associated Press» en el texto guardado)
    cuenta como la agencia aunque la publique otro diario. Dos diarios con el mismo cable no son independientes;
  - académica: `.edu`, SciELO, JSTOR, Britannica…;
  - archivo y museos: archive.org, hemerotecas, Library of Congress, The Henry Ford, Smithsonian;
  - empresa: los `dominios_propios` del encuadre, solo para su propia historia.
  
  No cuentan: Wikipedia, revistas de curiosidades (Mental Floss), blogs ni foros.
- Cada número y cada **año** de la voz, la pantalla y los captions están en un hecho, una frase o una cifra
  verificada (H4 + V2 sobre `base/datos.json`).
- **Casos de justicia**: presunción de inocencia (vocabulario vetado de `/noticias` sin sentencia firme) y el **estado
  del caso a la fecha de la consulta** de cada persona señalada (`casos[]`).
- **Fotos**: Wikimedia Commons con licencia libre (dominio público, CC0, CC BY, CC BY-SA; nunca NC ni ND; el script
  lee la licencia y arma el crédito), oficial, la og:image del medio con «Foto: medio» o la de prensa de la empresa;
  lado corto ≥ 480 px (aviso < 600); sin víctimas, cadáveres ni menores identificables. Sin foto: tarjeta tipográfica
  (mapa con el departamento o icono).
  - **Retrato** (`foto --retrato-de "<persona>"`): solo si es de esa persona. Un objeto o un lugar va como foto de
    escena, nunca como retrato de una cita.
  - **Gráfico, cartel o logo con texto**: `foto --encaje contener`, para que el marco no lo recorte.
  - **Sin repetir**: la misma imagen (sha1) se funde en un id al consolidar y sale en ≤ 2 escenas.
  - **El chip no inventa época**: una foto de 2021 no va bajo «1978»; el chip dice «Foto de 2021», «De referencia» o
    la época sin año.

## Gates (`scripts/historia.py`)

| Gate | Dónde | Qué exige |
|---|---|---|
| H1 forma | `hechos --check` | ids `<eje>-hNN/cNN/qNN`, fecha `YYYY[-MM[-DD]]` y precisión, texto ≤ 240, estado; ≥ 6 hechos publicables al consolidar |
| H2 evidencia | `hechos --check` | cita ≥ 20 caracteres en el texto guardado; independencia (confirmado / en disputa); año en la cita; números del texto en las citas; la frase literal de cada cita en su fuente |
| H3 justicia | `hechos --check` · `guion --check` | `casos[]` con estado actual, fecha de consulta y fuente si el encuadre es de justicia; vetadas sin sentencia firme |
| H4 respaldo | `guion --check` | años y números de voz, pantalla, pasos, resumen y captions en la cronología; atribución en lo `en_disputa`; los `hechos` citados existen |
| H5 duración | `guion --check` (V4 ±20 % de 150 s) · `tiempos` | 120–180 s estimados; aviso si la real pasa de 180 s |
| H6 pantalla | `guion --check` | titular ≤ 9 palabras, chip ≤ 14, lugar ≤ 24, fuente ≤ 44, cifra ≤ 18 con etiqueta ≤ 30, `grafico` con plantilla y `datos`; tarjetas por `materializar.py` (R1–R6); cita en otro idioma con `traduccion` ≤ 140 que la voz dice |
| H7 fotos | `foto` · `hechos --check` · `guion --check` | archivo, crédito «Foto: …», origen, licencia libre de Commons, lado ≥ 480 px; las escenas usan fotos verificadas; retrato con `retrato_de` = autor de la cita; una imagen en ≤ 2 escenas; chip sin un año anterior a la foto |
| H8 estructura | `guion --check` | 3–5 capítulos numerados (el primero en la escena 2 o 3), ≤ 2 escenas seguidas del mismo tipo, un giro entre el 40 y el 75 %, al menos una foto o cita, ≤ 19 escenas; aviso si una escena cuenta un año anterior al de su capítulo (flashback) |

Además corren los de `/video`: V1–V5 y V9 (sin «la escena 2 es T1»), F1–F8, V6, V7, V8, V10, V11, V12, V13 y V15.

## Voz y costos

Como `/noticias`: un nodo TTS por escena, 1 toma, Scribe por nodo y la llamada de estado que lee `historia.py descargar
--estado`. Las herramientas aceptan ≤ 20 ids por llamada: el estado final va en lotes (cada voz con su Scribe) y
`descargar --estado A B …` recibe todos. Las cifras con dinero van con prefijo (`US$1.15`, `Q2.50`; también se entiende
«1.15 dólares»): la voz dice «un dólar con quince centavos». ≈ 1 crédito por carácter: **≈ 1,800–2,600** en una historia de 2–3 min (`locucion.json →
caracteres`). Una retoma es por escena. El Workflow cuesta 0 créditos (≈ 12–16 agentes, 20–40 min).

## Archivos del trabajo

`encuadre.json` (editor) · `hallazgos_<eje>.json` (investigadores) · `verificacion_<eje>.json` y `fotos/<id>.jpg|json`
(verificadores) · `historia.json` (`consolidar`: hechos ordenados, cifras, citas, fotos, casos, descartados,
conflictos) · `base/` (hilo base) · `ganchos.json`, `seleccion.json` · `guion.json` · `critica.json` · luego lo de
`/video`: `locucion.json`, `audio/`, `escenas.json`, `clips/`, `salida/`, `revision/`.

## Entrega y registro

- `historia.py entregar TRABAJO` → `historias/<fecha>-<slug>/`:
  - `video.mp4` (TikTok, Reels, Shorts), `video_4x5.mp4` (feed), `caption.md`, `subtitulos.srt`, portadas y hojas de
    contacto;
  - `fuentes.md`: por capítulo, cada hecho con sus urls, más las fotos con crédito y licencia;
  - `cronologia.md`: la línea de tiempo de lo que cuenta el video, con su estado;
  - el `guion.json` de entrega.
  
  Las fotos no se copian (son de terceros) y los mp4 están fuera de git.
- `memoria.py --historia historias/<fecha>-<slug>` → `memoria/historias.json`. `historia.py` lo lee para:
  - avisar si la historia ya se contó;
  - rotar la familia y el visual del gancho, el cierre, las animaciones y la música;
  - las frases ya usadas (C11).
  
  M10 lo valida.

## Prueba sin web ni créditos

`make historia-fixture` (maqueta: `sesiones/_fixture_historia/`, una panadería **inventada** con fuentes de ejemplo
guardadas, fotos dibujadas con ffmpeg y voz falsa; 9:16 y 4:5 en `sesiones/_fixture_historia/trabajo/salida/`).
