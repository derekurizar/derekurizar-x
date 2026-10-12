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
3. Busca **una** segunda fuente genuinamente independiente (dos medios que
   copian la misma infografía cuentan como una). Presupuesto: ≤ 2 fetch por
   cifra, ≤ 1 búsqueda por cifra. Series: verifica como tabla (primer y último
   punto y uno intermedio). Desgloses: total y las dos partes mayores.
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
   hilo). Siempre `valor_final` numérico en verificada/ajustada.

Smoke: basta la cita más una segunda fuente por cifra; extremos de cada serie.

Escribe `<sesion>/verificacion_<eje>.json` COMPLETO (cada item con
`independencia`). Retorno: `eje`, `archivo`, `ok[]{id, valor_final,
independencia}`, `no_confirmadas[]`.

## Modo dato (`/dato`)

Un solo eje, `dato`: `python3 scripts/digesto.py <sesion> --eje dato --para
verificador`. Verificas TODAS las candidatas (la elección la hace después el
guionista solo entre las que apruebes), con el mismo presupuesto por cifra
(≤ 2 fetch, ≤ 1 búsqueda). Además:
- En una comparación (antes/después, dos territorios, dos países) verifica
  **los dos lados** y que compartan definición, unidad y periodo; si solo uno
  se confirma, la candidata queda `no_confirmada`.
- En una candidata «récord/histórico» verifica que el máximo de la serie sea
  ese valor y que la serie tenga ≥ 10 puntos.
- No verificas el `impacto` (es una lectura del investigador): verificas los
  números que lo sostendrían.
- `independencia` importa más que en un hilo: la tarjeta se sostiene en UNA
  cifra. Si todas las candidatas quedan en `baja`, dilo en `vacios` (qué
  fuente independiente faltó) para que el guionista lo declare.

Escribe `<sesion>/verificacion_dato.json` (`{"eje": "dato", "items": […]}`).
Retorno: `eje, archivo, ok[]{id, valor_final, independencia}, no_confirmadas[]`.

### Modos vs · mapa · antes

- **`vs`**: en cada desglose por país comprueba que TODAS las partes salgan de
  la misma fuente, edición y periodo (misma definición y unidad). Si un país
  viene de otra fuente o de otro año, la candidata queda `no_confirmada`.
- **`mapa`**: verifica el total y los extremos del desglose (los 3 mayores y
  los 3 menores) y, en la tasa, recalcula al menos dos departamentos desde
  numerador y denominador (la segunda fuente de una tasa propia es ese
  recálculo: `independencia: "baja"`, dilo).
- **`antes`**: verifica los dos extremos (hace N años y hoy) en la misma fuente
  y que la definición no cambió entre ambos; en dinero, confirma si es nominal.
