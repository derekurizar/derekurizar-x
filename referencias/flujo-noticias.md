# Flujo `/noticias` — índice

El **resumen del día de Guatemala** en un video vertical (1080×1920, 30 fps) de **≤ 70 s** (objetivo 60) para
TikTok, Reels y Shorts, más su 4:5 para el feed: un gancho con la noticia más fuerte, 3 noticias verificadas de ~15 s
(y una breve opcional de ~7 s), cada una con su imagen y su fuente en pantalla, y el cierre con **«Sígueme en»
siempre** (es la marca @DerekUrizar). Misma línea que `/video`: voz El Faraon 4 con las cifras en palabras, música del
catálogo fijo con ducking, efectos fijos, barra de progreso, subtítulos, zona segura (V13), 9:16 + 4:5. La publicación
es manual; el entregable queda en `noticias/<fecha>/` y se registra en `memoria/noticias.json`.

```
preparar (noticias.py: TRABAJO = sesiones/noticias-<fecha>/, paleta del día y su música)
→ Workflow noticias [3 noticias-rastreador en paralelo (pol · seg · eco) → candidatas_<sec>.json → gate N1
                     → preselección en código (las 6 mejores, ≥ 2 secciones, sin repetidas)
                     → un noticias-verificador por preseleccionada (en paralelo): segunda fuente, citas en el texto
                       guardado (noticias.py leer), foto (noticias.py foto) → verificacion_<id>.json → gate N2 + N7
                     → noticias-editor: consolidar → noticias.json → elige 3–4 → guion.json → gate N3–N6, N8, V3
                     → video-critico en modo noticiero (≤ 2 vueltas con el editor)]
→ QA de fotos (noticias.py fotos-contacto: sin víctimas, cadáveres ni menores identificables)
→ [sin-voz: voz-falsa] | voz (MCP ElevenLabs: un nodo TTS por escena, 1 toma, Scribe, descargar --estado)
→ tiempos (V6) → escuchar (V11) → grabar (V13) → montar (V8) → revisar (9:16 y 4:5)
→ entregar (noticias/<fecha>/) → memoria.py --noticias → make validate
```

`scripts/noticias.py` hace lo propio del noticiero y escribe el **mismo TRABAJO que `/video`**; la voz, la grabación,
el montaje y la revisión salen de `scripts/video.py` (los subcomandos `voz`, `voz-falsa`, `descargar`, `escuchar`,
`grabar`, `montar` y `revisar` de `noticias.py` solo los reenvían). La página de escena es `video/noticia.html`; el
cierre, `video/cierre.html` con el rótulo «Hoy en Guatemala».

## Formato fijo (decisiones del usuario, 2026-10-23)

| Escena | Tiempo | Voz (≈ 15.5 car/s a 1.1×) | Pantalla |
|---|---|---|---|
| E1 `titular` (gancho) | 0–4 s | 25–62 caracteres, una oración con verbo | la foto de la noticia 1 a sangre, oscurecida; su titular entero desde el cuadro 0 (las palabras que la voz dice se encienden con `realce`); «Hoy · 23 oct» y «4 noticias» |
| E2–E4 `noticia` | ~10–16 s c/u | 140–235 caracteres | chip «2/4 · Sección»; foto en marco con Ken Burns y «Foto: …»; titular con la voz; la cifra que cuenta y late cuando la voz la dice; «Fuente: …» |
| E5 `noticia` breve (opcional) | ~5–8 s | 60–115 caracteres | igual, sin cifra obligatoria |
| E6 cierre | ~5–8 s | 30–85 caracteres | «Hoy en Guatemala» con 3–4 titulares cortos → la frase final → «Sígueme en» (5 redes, solo en pantalla) |

- **Imagen: cada noticia lleva foto, siempre** (N7). Primero la foto **oficial** (la og:image de la fuente oficial), si
  no la og:image del **medio** con «Foto: <medio>»; si ninguna sirve (no hay, es pequeña o no pasa el QA), una **foto de
  referencia**: la institución (la fachada de la SAT, el Congreso), el lugar (la cárcel, el municipio) o la persona de
  la noticia, de la galería oficial (Flickr del Gobierno, AGN, el sitio de la institución), de Wikimedia Commons con
  licencia libre (`python3 scripts/historia.py commons "<búsqueda>"`) o de la foto de archivo de un medio; en pantalla
  dice «Foto de referencia: <fuente>» (`origen: "referencia"`) para que nadie la tome por la del hecho. Nunca de otro
  hecho distinto ni generada. Ya no hay tarjeta tipográfica.
- **Enfoque**: las más importantes del día (política, justicia, seguridad, economía, salud, clima, sociedad,
  deportes); el editor prioriza las que traen una cifra verificable y la pone en pantalla, pero una noticia grande sin
  cifra también entra.
- **Una paleta por día**: el ciclo de las 8 paletas por fecha (`PALETAS_CICLO`; dos días seguidos nunca repiten), la
  música va con la paleta y el gancho usa `realce` (el primer color claro de la paleta que se lee sobre la foto oscurecida).
- **Conectores** entre noticias («Además», «En economía», «Mientras tanto»), no «pero / por eso».
- **Cierre siempre con «Sígueme en»**; la voz del cierre no dice fuentes ni «sígueme».
- Sin cara; sin música ni efectos generados (catálogos fijos de `/video`).

## Reglas editoriales

- **Solo noticias `confirmada` o `en_desarrollo`**. Confirmada = dos fuentes independientes (grupos de medios
  distintos, tabla `MEDIOS`) o una oficial (`*.gob.gt`, `OFICIALES`) y un medio. En desarrollo = una fuente válida, y
  la voz **atribuye** («según el MP», «informó Conred»).
- **Presunción de inocencia**: sin sentencia firme nadie es «culpable», «asesino», «delincuente» ni «corrupto»
  (señalado, sindicado, acusado, capturado por…). El gate lo rechaza.
- Cada número de la voz, la pantalla y los captions está en una **cita** guardada de esa noticia (N4).
- No repetir una noticia de los últimos 3 días (`memoria/noticias.json`, por url o titular) salvo `novedad`.
- Tono de noticiero, sin sensacionalismo ni adjetivos de opinión; temas sensibles sin detalle morboso.

## Gates (`scripts/noticias.py`)

| Gate | Dónde | Qué exige |
|---|---|---|
| N1 candidatas | `candidatas --check` | 1–5 por sección con id `<sec>-N`; titular y `que_paso` ≤ 200; una url de la lista o oficial publicada hoy o ayer; puntaje impacto, alcance y novedad 1–5 |
| N2 verificación | `verificacion --check` | cada fuente con su texto guardado (`leer`) y la cita literal dentro (≥ 20 caracteres); confirmada / en desarrollo según la regla de arriba; ≥ 1 fuente válida de hoy o ayer; hechos y cifras con cita en el texto; el número de cada cifra en su cita |
| N3 selección | `guion --check` | 3–4 noticias publicables de ≥ 2 secciones, sin repetir; la breve al final |
| N4 voz | `guion --check` | V3 (cifras en palabras, ida y vuelta, género); números con cita; vocabulario vetado sin sentencia; sin «en suma»; atribución en las noticias en desarrollo |
| N5 tiempos | `guion --check` / `tiempos` | caracteres por escena (arriba); total estimado 45–70 s; aviso si la duración real pasa de 70 s |
| N6 pantalla | `guion --check` | titulares ≤ 9 palabras y ≤ 60 caracteres; sección ≤ 18; fuente ≤ 44; cifra ≤ 18 con dígitos y etiqueta ≤ 30 |
| N7 foto | `verificacion` / `guion --check` | cada noticia publicable y cada escena con foto: archivo en `TRABAJO/fotos/`, lado corto ≥ 600 px, origen `oficial` o `medio` con crédito «Foto: …», o `referencia` con «Foto de referencia: …» (≤ 44) |
| N8 cierre | `guion --check` | rótulo, 3–4 líneas ≤ 32 caracteres, `final` ≤ 10 palabras = la última frase de la voz, sin cebo ni «sígueme» en la voz |

Además corren los de `/video`: V6 (alineación), V8 (salida), V10 (ritmo, aviso), V11 (escucha), V12 (quietud), V13
(zona segura) y V15 (primer cuadro).

## Voz, entrega y registro

- **Voz**: la de `/video` (El Faraon 4, `eleven_multilingual_v2`, `language_code: es`, 1.1× con atempo), un nodo TTS
  por escena con `generations_count: 1`, Scribe por nodo (0 créditos) y una sola llamada de estado guardada que lee
  `noticias.py descargar --estado` (pasos 4–5 de `.claude/commands/noticias.md`). Cuesta ≈ 1 crédito por carácter:
  ~850 en un noticiero de 60 s (`locucion.json → caracteres`). Una retoma es por escena.
- **Música**: la de la paleta del día; sus 2 pistas se alternan cada vez que el ciclo vuelve a esa paleta (cada 8
  días). Nunca se genera.
- **Entrega** (`noticias.py entregar`): `noticias/<fecha>/` con `video.mp4` (TikTok, Reels, Shorts), `video_4x5.mp4`
  (feed), `caption.md` (una sección por plataforma), `fuentes.md` (los enlaces de cada noticia y los créditos de foto,
  para el primer comentario o la descripción), `subtitulos.srt`, portadas, `contacto.png` y `guion.json` de entrega.
  Los mp4 quedan fuera de git; las fotos no se copian (son de terceros). Sin voz de ElevenLabs (`audio/creditos.json`)
  solo se entrega con `--salida` (pruebas).
- **Registro** (`memoria.py --noticias noticias/<fecha>`): `memoria/noticias.json` con las noticias del día (id,
  sección, titular, urls). El digesto del rastreador y el gate N3 lo leen para no repetir una noticia de los últimos 3
  días; `make validate` lo comprueba (M9).

## Archivos del trabajo

- `candidatas_<pol|seg|eco>.json` (rastreadores): `{"seccion", "candidatas": [{"id": "pol-1", "titular", "que_paso",
  "seccion_tema", "depto", "urls": [{"medio", "url", "fecha"}], "cifra_posible", "puntaje": {"impacto", "alcance",
  "novedad"}}]}`.
- `verificacion_<id>.json` (verificadores): la noticia lista para el editor (forma en
  `referencias/roles/noticias-verificador.md`).
- `noticias.json` (`consolidar`): todas las verificaciones. `guion.json` (editor; forma en
  `referencias/roles/noticias-editor.md`). `critica.json` (crítico). Luego lo de `/video`: `locucion.json`, `audio/`,
  `escenas.json`, `clips/`, `salida/`, `revision/`.

## Prueba sin web ni créditos

`make noticias-fixture` (maqueta: `sesiones/_fixture_noticias/`, noticias **de ejemplo** con «Maqueta» arriba, fotos
generadas con ffmpeg, voz falsa; 9:16 y 4:5 en `sesiones/_fixture_noticias/trabajo/salida/`).
