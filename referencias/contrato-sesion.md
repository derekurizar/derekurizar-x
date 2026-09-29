# Contrato de sesión (`sesiones/<slug>/`)

Cada agente escribe su artefacto COMPLETO aquí y devuelve al workflow solo un
resumen. **Nadie lee los JSON de sesión enteros**: se usan los digestos
(`python3 scripts/digesto.py <sesion> --para <rol>`), que caben en un solo
resultado de herramienta.

| Archivo | Lo escribe | Contenido |
|---|---|---|
| `encuadre.json` | editor | `slug, tema, fecha, pregunta, tesis_provisional, angulo, paleta, necesita_serie, repetido, hook_evitar, ejes[2–4]{id, prefijo (3 letras únicas), brief, preguntas[], fuentes_sugeridas[], series_sugeridas[]}, sesion_dir, smoke, fixture` |
| `hallazgos_<eje>.json` | investigador | `eje, n_busquedas, n_fetch, cifras[≤12]{id "<prefijo>-cNN", concepto, valor:number, unidad, anio, fuente, url, tipo: puntual\|serie\|desglose, n_puntos, periodo, candidata_ancla, evidencia{url, cita ≤200, archivo_local?}, serie:[{p, v}], partes:[{nombre, valor}], nota}, fuentes[]{nombre, url, nivel}, vacios[]` |
| `verificacion_<eje>.json` | verificador | `eje, items[]{id, veredicto: verificada\|ajustada\|no_confirmada, valor_final, fuente_2, url_2, nota}` |
| `guion.json` | guionista | `slug, fecha, paleta, smoke, handle, hook_tipo, sintesis{pregunta, tesis, ancla_id, arco[], no_afirma[≤5], incertidumbre[], descartadas[]}, tuits[]{n, beat, texto, alt_text ≤1000, visual\|null}` con `visual = {plantilla, kicker, titular[], leyenda[], nota, fuente, cifra_ids[], datos{}}` |
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
