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
4. Comprueba definición del indicador, unidad, periodo y que no se mezclen
   universos (país vs región, referencia vs bomba, OPS vs MSPAS).
5. Veredicto: `verificada` · `ajustada` (la primaria manda: `valor_final`
   distinto y `nota` que lo explica) · `no_confirmada` (no aparecerá en el
   hilo). Siempre `valor_final` numérico en verificada/ajustada.

Smoke: basta la cita más una segunda fuente por cifra; extremos de cada serie.

Escribe `<sesion>/verificacion_<eje>.json` COMPLETO. Retorno: `eje`, `archivo`,
`ok[]{id, valor_final}`, `no_confirmadas[]`.
