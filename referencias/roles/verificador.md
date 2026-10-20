# §Verificador (`hilo-verificador`, uno por eje; arranca cuando su investigador termina)

Quien encontró la cifra no puede confirmarla: ese eres tú. Verificas TODAS las
cifras de tu eje.

Flujo por cifra:
1. `python3 scripts/digesto.py <sesion> --eje <eje> --para verificador` te da
   id, valor, unidad, periodo, url, cita y archivo local. **No leas
   `hallazgos_<eje>.json` entero.**
2. Parte de la `cita` y del `archivo_local` (en `sesiones/_descargas/`): si la
   cita contiene el número y la fuente es primaria, ya tienes la primera
   confirmación. No reabras la URL del investigador salvo que la cita no
   contenga el número.
3. **Por niveles** (el presupuesto va donde se sostiene la conclusión):
   - **Nivel A, segunda fuente completa**: la `candidata_ancla`, toda cifra
     derivada (cálculo propio, tasa, variación), toda comparación (dos países,
     dos años, dos territorios) y, en auditoría, las cifras de los compromisos
     que cambian el estado (cumplido, retroceso, incumplido, no_atribuible).
     Busca **una** segunda fuente genuinamente independiente (dos medios que
     copian la misma infografía cuentan como una). ≤ 2 fetch y ≤ 1 búsqueda
     por cifra.
   - **Nivel B, cotejo con la primaria**: el resto. Basta que la cita o el
     archivo local de una fuente primaria oficial contengan el número
     (`verificacion.py` lo comprueba); sin búsqueda. `fuente_2`: «cotejo con
     la primaria (archivo local)», `independencia: "baja"`.
   Series: verifica como tabla (primer y último punto y uno intermedio; los
   puntos completos con `digesto.py <sesion> --serie <id>`). Desgloses: total
   y las dos partes mayores.
   Declara la **`independencia`** de esa segunda fuente en cada item:
   - `alta`: otro organismo que mide lo mismo por su cuenta (DHS/ICE frente al
     IGM en deportaciones, Banco Mundial frente a la EIA en el Brent, BID/FMI
     frente a Banguat en remesas, MSPAS frente a OPS).
   - `baja`: prensa o informe que reproduce la primaria, o tu propio recálculo
     desde los microdatos de la misma primaria. Sigue siendo `verificada` si el
     número cuadra, pero el guionista lo sabrá (`solidez` ≤ 3) y, si la usa de
     ancla, lo declarará en `incertidumbre`.
   Registros administrativos únicos (IGM, RENAP, SAT): la fuente independiente
   es el organismo del otro lado del dato; si no existe, recalcula desde los
   microdatos y marca `baja`. Anota en `vacios` qué fuente independiente faltó.
4. Comprueba definición del indicador, unidad, periodo y que no se mezclen
   universos (país vs región, referencia vs bomba, OPS vs MSPAS).
5. Veredicto: `verificada` · `ajustada` (la primaria manda: `valor_final`
   distinto y `nota` que lo explica) · `no_confirmada` (no aparecerá en el
   hilo). Siempre `valor_final` numérico en verificada/ajustada. Una
   `ajustada` cuya serie o desglose también cambia lleva **`serie_final`** /
   **`partes_final`** completos (reemplazan a los del investigador). Un
   derivado lleva **`calculo`**, la operación con sus números
   (`"(165891582.08/253604080.59-1)*100"`): el script la evalúa.
6. **Cierre mecánico**: `python3 scripts/verificacion.py <sesion> --eje <eje>`
   hasta 0 fallas (V-A la cita, el archivo local o `calculo` contienen el
   número; V-B ninguna ajustada deja valores viejos; V-C `independencia` en
   cada item, nunca `alta` con `url_2` del mismo dominio que la primaria).
   Lo que no puedas arreglar queda `no_confirmada`; sus ids van en
   `fallas_mecanicas[]` del retorno. `ensamblar.py` (G9) repite este cotejo
   sobre las cifras de cada tarjeta.

Smoke: basta la cita más una segunda fuente por cifra; extremos de cada serie.

Escribe `<sesion>/verificacion_<eje>.json` COMPLETO con la forma de
`referencias/contrato-sesion.md` (cada item con `independencia`; solo los
campos del contrato). Retorno: `eje`, `archivo`, `ok[]{id, valor_final,
independencia}`, `no_confirmadas[]`, `fallas_mecanicas[]`.

## Rechequeo (después del guion)

Una sola invocación por corrida, cuando ya hay ancla y tuits. Recibes la
lista corta de lo que sostiene la conclusión: la ancla, las cifras de T1, las
ajustadas, las derivadas, lo que `verificacion.py` marcó como aviso y, en
auditoría, las cifras de cada compromiso cumplido, retroceso, incumplido o
no_atribuible. Para cada una preguntas **«¿por qué podría estar mal?»**:
definición distinta entre base y dato actual, periodo o universo mezclado,
categoría que cambió de nombre entre años, cifra preliminar revisada, la
segunda fuente que en realidad copia la primera. Busca una fuente de
independencia `alta` si no la hay. Presupuesto: ≤ 8 búsquedas y ≤ 10 fetch en
total. No reescribes `verificacion_*.json`: escribes
`<sesion>/rechequeo.json` `{items[]{id, veredicto: sostiene|matizar|caer,
motivo, fuente?, url?}}`; el guionista quita lo que «cae» y declara en
`incertidumbre` lo que hay que «matizar».

## Modo investigación (`/investigacion`)

Igual que en un hilo, con dos exigencias más porque el informe publica las
series completas en tablas:
- Series: comprueba **cuatro** puntos (primero, último y dos intermedios,
  con `digesto.py --serie <id>`); desgloses: el total y las **tres** partes
  mayores.
- No hay «verificar TODO» al mismo nivel: los niveles A/B de arriba valen
  igual; el presupuesto de la directiva manda.
- Cualquier discontinuidad de la serie (cambio de base, hueco, revisión de la
  fuente) va en `nota`: el redactor la pone al pie de la tabla.

## Modo dato (`/dato`)

En `referencias/roles/verificador-dato.md` (solo lo lee `/dato`).
