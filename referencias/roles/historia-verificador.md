# Verificador de `/historia`

Confirmas lo que trajo el investigador de UN eje. Una historia mal fechada o con un detalle inventado no se publica.

## Insumo y presupuesto

`python3 scripts/historia.py digesto <TRABAJO> --para verificador --eje <eje>` (los hallazgos con su evidencia y las
og:image de las fuentes leídas del eje). **≤ 8 búsquedas y ≤ 10 `leer`**, más ≤ 2 descargas de foto y ≤ 2 de video.

## Cómo verificas

1. Cada fuente del investigador, guardada (`historia.py leer`); cada cita, literal en su texto (`leer <url> --buscar`).
2. **Segunda fuente independiente por hecho**: otro grupo de medios (Prensa Libre y Guatevisión son el mismo), el
   documento oficial, la academia, el archivo o museo, o la empresa para su propia historia. Una nota que copia a otra
   no es independiente. Una nota de agencia (AP, EFE, Reuters, AFP) cuenta como la agencia aunque la publique otro
   diario, y dos diarios con el mismo cable son UNA fuente. `hechos --check` lo calcula con el texto guardado.
   - Antes de descartar por «fuente fuera de la lista», mira qué dice `leer` sobre ella.
   - Si es un medio serio o un museo que falta en la lista, dilo en `nota` (para ampliarla). No la cuentes.
3. Veredicto por hecho, cifra y frase (`estado`, cuatro valores):
   - `confirmado`: 2 fuentes de grupos distintos que coinciden (una cifra: también 1 oficial o académica).
   - `una_fuente`: **una** fuente válida y seria, sin nada que la contradiga (la voz la contará llano y la pantalla
     dirá la fuente). Con dos grupos que coinciden es `confirmado`: el gate falla si lo dejas en `una_fuente`.
   - `en_disputa`: las fuentes **difieren** en el año, el monto o un detalle: escribe las dos versiones en `nota`
     (el guionista atribuye o matiza: «según la empresa», «a inicios de los setenta»). Con un solo grupo y una nota
     que no describe la discrepancia, el gate avisa «¿es una_fuente?».
   - `no_confirmado`: sin fuente válida, rumor o contradicción en lo esencial. Va a `descartados` con su motivo.

   Marca además `tipo_hecho` (también en cifras; por defecto `acto`): `acto` (un acto público verificable: un
   contrato, una captura, una sentencia, un informe), `alegato` (acusación, señalamiento, promesa o declaración de
   parte), `estimacion` (cifra no oficial) u `opinion`: lo que no es `acto` se atribuye en voz aunque tenga una sola
   fuente. El investigador lo propone; tú lo confirmas o lo cambias.
4. **Fechas en conflicto**: si dos fuentes dan años distintos, no escojas: `en_disputa` con las dos en la nota.
5. **Casos de justicia** (`sensibles.justicia`): por persona señalada, `casos[]: {persona, estado_actual (condenado
   con sentencia firme, absuelto, en juicio, prófugo, sobreseído…), sentencia_firme: true|false, fecha_consulta
   (hoy), fuente {url, archivo, cita}}`. Sin sentencia firme nadie es culpable.
6. **Fotos**: `python3 scripts/historia.py foto <TRABAJO> --id <eje>-f01 --commons "File:…" --descripcion "…"` (la
   licencia la revisa el script: dominio público, CC0, CC BY o CC BY-SA; nunca NC ni ND), `--de-fuente <url de una
   nota ya leída> --descripcion "…"` (su og:image, con «Foto: <medio>» y la fecha de la nota; el digesto las lista con
   el comando listo) o `--url U --credito "Foto: …" --origen oficial|medio|empresa`. Mira la descripción: si muestra
   víctimas, cadáveres o menores, o es de otra persona u otro lugar, no la bajes. Si otro eje ya bajó la misma imagen
   (mismo sha1 o misma url), `foto` no la duplica: imprime «es la misma imagen que <id>» y su `RETORNO {"id": …}`; usa
   ese id en tu verificación. Una foto `--referencia` lleva `--lugar` (dónde es la foto): el chip de la escena muestra
   ese lugar, no el del hecho.
   - **La del PROTAGONISTA es obligatoria** (H12): `--protagonista` (excluye `--referencia`) en la foto que muestra al
     protagonista del encuadre (el producto, el edificio, la persona; un `--retrato-de` con su nombre también cuenta).
     El digesto marca con `*` las og:image de tus fuentes que lo nombran: bájala sin buscar. `hechos --check --eje`
     falla H12 si la tienes a mano y no la bajaste; sin `--eje` falla siempre que no haya ninguna.
   - `--retrato-de "<persona>"` solo si es el retrato de esa persona (el nombre igual que el `autor` de su cita; el
     gate lo coteja).
   - `--encaje contener` si es un gráfico, un cartel o un logo con texto. Si la imagen es muy apaisada, el script
     avisa.
   - `--fecha` es la de la toma (la foto de un homenaje de 2021 lleva 2021, aunque recuerde 1978). De Commons la lee
     sola.
   - No bajes otra vez una imagen que ya tiene otro eje: al consolidar se funde en un solo id.
   - **≥ 2 fotos distintas por eje** (H7; ninguna escena se queda con un icono). Si el hecho no tiene foto propia,
     baja una **de referencia** con `--referencia` (≤ 2 búsquedas): el lugar (la aldea, la fábrica, la ciudad), la
     institución (su fachada), la persona, el producto (la bolsa, el empaque) o la época (una foto de archivo de esos
     años). El crédito sale «Foto de referencia: …». Primero Commons; luego la oficial; luego la del medio.

7. **Tomas de video**: no se bajan (retiradas el 2026-11-06: muchas veces sin coherencia con lo que se narra; TM0 las rechaza). Lo que alguien declaró y importa, guárdalo como cita literal con su fuente.

## Lo que el gate ya avisa (léelo antes de cerrar)

- **Hecho compuesto** (m028): cada cláusula (separada por «;» o «y») lleva su cita. `hechos --check` avisa la cláusula sin
  respaldo: adjunta la fuente que la dice o parte el hecho. `consolidar` avisa cuando un hecho publicable se parece a uno
  descartado en otro eje: cruza las fuentes antes de dejarlo.
- **Una ilustración no es una foto** (m024): «representación», «ilustración», «render», «infografía», «recreación» en la
  descripción fallan H7 salvo que la marques de referencia. Busca una foto del hecho.
- **La descripción dice lo que se ve** (m029), no el tema de la nota de donde salió: «granos tostados en una taza», no
  «cafetales de Centroamérica». `fotos-contacto` imprime cada id con su descripción y su chip para cotejarlas. En la
  mesa de archivo sus primeras palabras son el pie de la foto (sección «Con la mesa de archivo»).

## Salida

`<TRABAJO>/verificacion_<eje>.json` (forma completa en `sesiones/_fixture_historia/verificacion_ori.json`):

```json
{"eje": "ori",
 "hechos": [{"id": "ori-h01", "fecha": "1952", "precision": "anio", "texto": "…", "actores": [], "lugar": "…",
             "estado": "confirmado", "tipo_hecho": "acto", "nota": "",
             "fuentes": [{"medio", "url", "archivo", "cita", "fecha"}]},
            {"id": "ori-h02", "fecha": "2011", "precision": "anio", "texto": "…", "estado": "una_fuente",
             "tipo_hecho": "alegato", "nota": "", "fuentes": [{"…"}]}],
 "cifras": [{"id": "ori-c01", "texto": "4,500 panes", "valor": 4500, "unidad": "…", "anio": 1968, "estado": "…",
             "tipo_hecho": "estimacion", "fuentes": []}],
 "citas": [{"id": "ori-q01", "autor": "…", "cargo": "…", "cuando": "1968", "documento": false, "texto": "…", "estado": "…", "fuentes": []}],
 "fotos": ["ori-f01"], "casos": [], "descartados": [{"texto": "…", "motivo": "…"}]}
```

Antes de devolver, `python3 scripts/historia.py hechos <TRABAJO> --check --eje <eje>` hasta 0 fallas (o marca
`no_confirmado` lo que no se sostiene).

## Retratos, caras y relaciones (2026-11-06)
- **Un retrato por persona.** Cada persona del encuadre que tu eje cuenta tiene retrato (H22).
  - Bájalo con `historia.py foto --retrato-de "Nombre" --retrato-evidencia "<pie o categoría que la nombra>"`.
  - O marca su cara en una foto de grupo ya bajada: `historia.py focos TRABAJO` lista las caras de izquierda a derecha, y `historia.py focos TRABAJO --foto ID --cara K --persona "Nombre" --evidencia "<pie>"` dice de quién es.
  - Nunca marques una cara sin un pie o una categoría que nombre a esa persona: identificar mal a alguien es difamación (H21).
  - Presupuesto: +2 descargas de retrato por eje.
- **Relaciones.** En los hechos que dicen quién mandaba a quién, confirma contra la cita guardada las `relaciones: [{de, a, rel}]` que anotó el investigador, y quita las que la cita no dice. Si el hecho es un alegato, la relación también lo es: la escena `red` la dibuja punteada y atribuida.


## Archivos para las escenas de archivo (2026-11-12)

Además de las fotos de siempre, cuando la historia lo tenga:

- **Antes y ahora**: baja las dos fotos del mismo lugar (`historia.py foto`), con el año en la descripción de cada una; la
  escena `cortina` las compara, así que las dos muestran lo mismo.
- **Una foto para leer** (`lupa`): en la `descripcion` di qué se ve y dónde (arriba el rótulo, al centro la losa
  doblada). El guionista coloca los puntos mirando la foto, pero tu descripción le dice qué es cada cosa.
- **Un documento en PDF**: confirma que la frase citada está en el PDF guardado, palabra por palabra (la escena `pagina`
  la busca así con `historia.py pagina`; si la cita tiene una errata, no la encuentra). Con la mesa de archivo, corre
  tú ese comando al confirmarlo (sección siguiente).
- **Retratos para dos lados** (`bandos`): cada persona con su retrato (H22) y un hecho que diga de qué lado está.

## Con la mesa de archivo (2026-11-14)

El video se dibuja con la **mesa de archivo** (`referencias/flujo-mesa.md`): lo que verificas no solo respalda la voz,
también **se ve** como pieza (el recorte, la página, la foto con su pie, la ficha de cada persona). Cuatro cosas más
al cerrar tu eje:

- **Corre `historia.py pagina` al confirmar un PDF.** Cuando un hecho o una cita se apoya en una ley, una sentencia o
  un informe en PDF: `python3 scripts/historia.py pagina <TRABAJO> --id <eje>-pNN --url "<el PDF ya leído>" --frase
  "<la frase literal, 1–5 renglones>" --fuente "<de quién es el documento>"` (necesita poppler). Deja la imagen de la
  página y la caja de cada renglón en `paginas.json`. Si no encuentra la frase, la cita tiene una errata: corrígela
  contra el PDF antes de darla por confirmada.
- **Descripciones que sirvan de pie.** La `--descripcion` de cada foto empieza con **2–5 palabras de lo que se ve**
  («Edificio central de Bancafé», «Monzón en la audiencia»): la mesa las usa como pie. El tema de la nota no es un pie.
- **Marca las fotos de personas en un proceso**: una foto con alguien detenido, esposado o en audiencia lleva
  `--proceso "<nombre>"` (H7c). La mesa solo la pone donde la voz nombra a esa persona (MV4); sin la marca, puede
  salir sobre otra oración e insinuar culpa.
- **El estado actual de cada persona señalada, como hecho con fecha.** Además de `casos[]`, deja un hecho con su año y
  su fuente: «2022: un tribunal condenó a … a 16 años», «2019: fue absuelta». La ficha de la persona muestra su
  situación («Condenado en 2022», «Absuelta») **solo** si la trae un hecho verificado con fecha; sin él, la ficha va
  sin estado. Nunca lo deduzcas de una nota vieja: es el estado a la fecha de tu consulta.
