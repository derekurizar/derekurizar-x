# Contrato de sesión (`sesiones/<slug>/`)

Cada agente escribe su artefacto COMPLETO aquí y devuelve al workflow solo un
resumen. **Nadie lee los JSON de sesión enteros**: se usan los digestos
(`python3 scripts/digesto.py <sesion> --para <rol>`), que caben en un solo
resultado de herramienta.

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `encuadre.json` | editor | `slug, tema, fecha, modo: "hilo"\|"explica"\|"perfil", pregunta, tesis_provisional, angulo, paleta, necesita_serie, repetido, hook_evitar, idea_id (id del banco de ideas o null), ejes[2–4]{id, prefijo (3 letras únicas), brief, preguntas[], fuentes_sugeridas[], series_sugeridas[]}, sesion_dir, smoke, fixture` |
| `hallazgos_<eje>.json` | investigador | `eje, n_busquedas, n_fetch, cifras[≤12]{id "<prefijo>-cNN", concepto, valor:number, unidad, anio, fuente, url, tipo: puntual\|serie\|desglose, n_puntos, periodo, candidata_ancla, evidencia{url, cita ≤200, archivo_local?}, serie:[{p, v}], partes:[{nombre, valor}], nota}, fuentes[]{nombre, url, nivel}, vacios[]` |
| `verificacion_<eje>.json` | verificador | `eje, items[]{id, veredicto: verificada\|ajustada\|no_confirmada, valor_final, fuente_2, url_2, independencia: alta\|baja (baja = la 2ª fuente reproduce la primaria o es recálculo de sus microdatos), nota}` |
| `guion.json` | guionista | `slug, fecha, modo, paleta, smoke, handle, hook_tipo, sintesis{pregunta, tesis, ancla_id, arco[], no_afirma[≤5], incertidumbre[], descartadas[]}, tuits[]{n, beat, texto, alt_text ≤1000, visual\|null}` con `visual = {plantilla, kicker, titular[], leyenda[], nota, fuente, cifra_ids[], datos{}}`; en modo `explica` el bloque `explica{pregunta, pasos[]{n, titulo}}` y en `perfil` el bloque `perfil{sujeto, tipo: departamento\|grupo, dimensiones[]{n, nombre, anio}}` |
| `visuales/tuit_N.html/.png` | visualista (vía `materializar.py`) | tarjeta ensamblada y su PNG |
| `visuales/tuit_N.ajuste.json` | visualista | cambios parciales al `visual` de ese tuit; los consolida el productor |
| `salida/` | productor (solo smoke/fixture) | carpeta de entrega cuando no se toca `hilos/` |

Reglas del contrato:
- Ids de cifra `<prefijo>-cNN` (`pre-c01`); el prefijo lo fija el editor y es
  único por eje. Una serie es UNA cifra (`valor` = último punto, `serie[]`
  completa, `n_puntos`); un desglose es UNA cifra (`valor` = total o parte
  mayor, `partes[]`).
- Desde la verificación **manda `valor_final`**. `no_confirmada` nunca llega al hilo.
- Los números de `visual.datos` van crudos, en la unidad de la fuente; el gate
  mecánico (`ensamblar.py --check`, G4) los coteja contra `valor_final`, los
  puntos de la serie o las partes del desglose.
- Descargas oficiales: `make tabla URL=` (xlsx/html/csv → CSV), `make pdf URL=`
  (pdf → txt), `python3 scripts/fetch_api.py URL` (JSON). Todas cachean en
  `sesiones/_descargas/` (índice en `indice.json`): la misma URL no se baja dos
  veces. Para agregar CSV grandes sin volcarlos: `python3 scripts/tabla.py`.
- Sitios con WAF (MEM, INE, IGM, INGUAT): `python3 scripts/fetch_tabla.py
  --enlaces '\.xlsx$' URL` lista los archivos; `make pdf` lleva UA de navegador.
  **No se usa el navegador Playwright MCP.**
- Modo `smoke`: 1 eje, ≤ 6 cifras, ≤ 5 búsquedas, 3 tuits, salida en
  `<sesion>/salida/`, sin tocar `memoria/`. Modo `fixture`: se copia
  `sesiones/_fixture` y se saltan investigación y verificación.

**Modos de hilo** (`/hilo explica|perfil`, alias `/explica`, `/perfil`): el
workflow pasa `args.modo`; `tipo` sigue siendo `hilo`. `explica`: 3–6 tuits,
sin giro ni impacto, intermedios con beat `paso` (uno por paso del bloque) y
texto no vacío. `perfil`: 5–8 tuits, sin giro ni impacto, intermedios con beat
`dimension` (una por dimensión del bloque), cada tarjeta compara sujeto y país
y el sujeto aparece en T1. El bloque viaja a `hilo.json`, `post.md` («## Modo
…») y `memoria/hilos.json` (`modo`, y `sujeto` en perfil).

## Sesión dato (`/dato`)

Mismo contrato con un solo eje `dato` (prefijo `dat`) y sin editor ni
visualistas. Los digestos funcionan igual (`--eje dato`).

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `encuadre.json` | investigador (encuadre ligero) | `slug, pista (literal del usuario o null), tema (tema final elegido por el investigador), fecha, tipo: "dato", modo: "dato"\|"vs"\|"mapa"\|"antes", paleta, pregunta, hook_evitar, repetido, sesion_dir, smoke, fixture, ejes: [{id: "dato", prefijo: "dat", brief, preguntas[], fuentes_sugeridas[]}]` |
| `hallazgos_dato.json` | investigador | como `hallazgos_<eje>.json` (`eje: "dato"`, ≤ 8 cifras `dat-cNN`) y en cada cifra `impacto` (≤ 160) |
| `verificacion_dato.json` | verificador | `eje: "dato", items[]{id, veredicto, valor_final, fuente_2, url_2, independencia, nota}` |
| `guion.json` | guionista | `slug, fecha, tipo: "dato", modo, paleta, smoke, handle, hook_tipo, dato{cifra_id, titular, por_que_impacta}, candidatas[]{id, puntaje, criterios{sorpresa, magnitud, comparacion, actualidad, solidez}, elegida, motivo}, sintesis{pregunta, tesis, ancla_id, no_afirma, incertidumbre, descartadas}, tuits[EXACTAMENTE 1]{n: 1, beat: "gancho", texto, alt_text, visual}` y, si el modo no es `dato`, su bloque: `vs{paises[], fuente_comun, periodo, per_capita, motivo?}` · `mapa{per_capita, denominador, motivo?}` · `antes{anio_antes, anio_despues, nominal}` |
| `visuales/tuit_1.html/.png` · `tuit_1.ajuste.json` | productor (vía `materializar.py`) | la tarjeta y sus ajustes de QA; el propio productor consolida |
| `salida/` | productor (solo smoke/fixture) | carpeta de entrega cuando no se toca `datos/` |

**Modos** (`/dato vs|mapa|antes`, alias `/vs`, `/mapa`, `/antes`): el workflow
pasa `args.modo`; el investigador lo escribe en `encuadre.json` y el guionista
en `guion.json` con el bloque del modo. `tipo` sigue siendo `"dato"`; el gate
fuerza gancho y plantillas por modo (`vs`: cifra elegida tipo `desglose` por
país con Guatemala, misma fuente y periodo; `mapa`: desglose por departamento
≥ 12 y tasa; `antes`: dos años a ≥ 5 de distancia, nominal declarado). El bloque
viaja a `dato.json` (clave del modo), `post.md` («## Modo …») y `memoria/datos.json`
(`modo`).

Entregable: `datos/YYYY-MM-DD-<slug>/` con `dato.png`, `tarjeta.html`,
`dato.html` (vista previa), `post.md`, `datos.json`, `dato.json`. Registro en
`memoria/datos.json` (solo `memoria.py --registrar`, que detecta
`guion.tipo`); series y fuentes halladas a `memoria/fuentes.json` como hoy.
`ensamblar.py` nunca escribe un dato en `hilos/` ni un hilo en `datos/`.
Modo `smoke`: ≤ 4 búsquedas, ≤ 4 fetch, ≤ 4 cifras, 1 serie, 1 iteración de QA
visual, salida en `<sesion>/salida/`, sin tocar `memoria/` (sin pista usa
«remesas familiares 2025»). Modo `fixture`: el productor copia
`sesiones/_fixture_dato` a `sesiones/fixture-dato-<YYYYMMDD>` y se saltan
investigación, verificación y guion.
