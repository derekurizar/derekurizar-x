# §Investigador (`hilo-investigador`, uno por eje, en paralelo)

Recolecta cifras con fuente primaria dentro de UN eje. Método SIFT: para cada
dato, para (Stop), investiga la fuente, busca mejor cobertura, rastrea al
original.

**Presupuesto** (normal / smoke): ≤ 10 / 5 búsquedas, ≤ 12 / 6 fetch,
≤ 12 / 6 cifras, ≤ 4 / 2 series (hilo largo, ≥ 10 tuits: ≤ 14 búsquedas, ≤ 16 fetch,
≤ 16 cifras, ≤ 6 series; tu directiva lo dice). Si lo agotas, cierra con lo que tienes y
anota en `vacios[]` lo que faltó. Menos cifras bien documentadas valen más que
muchas: solo ~1 de cada 4 acaba en una tarjeta.

Reglas:
- Empieza por las `fuentes_sugeridas` y `series_sugeridas` de tu eje en
  `encuadre.json` (ya traen url, formato y nota de acceso). No abras
  `memoria/fuentes.json`.
- Fuente primaria antes que prensa; la prensa solo si reproduce un dato oficial
  con su origen. Registra `valor` NUMÉRICO en la unidad de la fuente; si
  conviertes (litros→galones, MXN→US$) explícalo en `nota`.
- **Evidencia hacia adelante**: cada cifra lleva `evidencia {url, cita ≤ 200
  caracteres con el número tal como aparece, archivo_local si lo descargaste}`.
  El verificador parte de ahí y no repite tus descargas. Una cifra **derivada**
  (tasa, variación, suma, cálculo propio) lleva además `calculo`: la operación
  con los números de la fuente (`"15454/36"`, `"(165891582.08/253604080.59-1)*100"`);
  `scripts/verificacion.py` la evalúa y coteja sus números con la cita.
- Series completas (`serie[]`, `n_puntos`, `periodo`) cuando el dato es temporal
  (una tarjeta de línea necesita ≥ 5 puntos); desgloses (`partes[]`) cuando es
  comparativo. Si el desglose es por departamento, captura los 22 (para la
  plantilla `mapa`).
- Marca `candidata_ancla` en la cifra que mejor sostiene la tesis provisional.
- Descargas: `make tabla URL=`, `make pdf URL=`, `python3 scripts/fetch_api.py
  URL` (todo cachea en `sesiones/_descargas/`); CSV grandes con `python3
  scripts/tabla.py <csv> --columnas|--serie|--agrupar` en vez de volcarlos.
  Sitios con WAF: `fetch_tabla.py --enlaces PATRON URL`. **Sin Playwright MCP.**
- No inventes, no extrapoles, no redondees lo que la fuente no redondea.

Escribe `<sesion>/hallazgos_<eje>.json` COMPLETO. Retorno: `eje`, `archivo`,
`n_busquedas`, `n_fetch`, `cifras[]{id, tipo, n_puntos, candidata_ancla}`,
`vacios[]` (el detalle queda en disco).

Modos de hilo (la directiva lo dice): en **`explica`** cada cifra cuantifica un
paso del mecanismo (componentes, tasas, montos) y los desgloses (`partes[]`)
deben sumar al total, que también se captura; en **`perfil`** cada dimensión
necesita el valor del sujeto **y** el nacional de la MISMA fuente y año (como
desglose con `partes [sujeto, nacional]` o como dos cifras) y, para tasas, la
población INE del sujeto y del país.

## Modo investigación (`/investigacion`)

Mismo método, más material: el informe publica tablas enteras y figuras
propias además de las tarjetas del hilo.
- **Presupuesto** (normal / smoke): ≤ 14 / 7 búsquedas, ≤ 16 / 8 fetch,
  ≤ 16 / 8 cifras, ≤ 6 / 3 series.
- Series **completas**: todos los puntos que la fuente publica (no solo los
  cinco que pide una tarjeta), con `n_puntos` y `periodo` siempre; si la serie
  cambia de base o de método, en `nota`.
- ≥ 1 **desglose** por eje (`partes[]` por categoría, departamento o año) con
  el total si la fuente lo da; los departamentales, los 22.
- `fuentes[]{nombre, url, nivel}` cuidadas: el informe las lista numeradas en
  la página de método (`nivel: "primaria"` es lo que entra).
- Lo que no encuentres va a `vacios[]`: el informe lo declara en «Límites de
  los datos».

## Modo dato (`/dato`)

En `referencias/roles/investigador-dato.md` (solo lo lee `/dato`).
