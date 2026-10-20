# §Verificador · modo dato (`/dato`)

Complemento de `referencias/roles/verificador.md` (léela primero): solo lo lee `/dato` y sus modos
`vs`, `mapa` y `antes`.

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

## Modos vs · mapa · antes

- **`vs`**: en cada desglose por país comprueba que TODAS las partes salgan de
  la misma fuente, edición y periodo (misma definición y unidad). Si un país
  viene de otra fuente o de otro año, la candidata queda `no_confirmada`.
- **`mapa`**: verifica el total y los extremos del desglose (los 3 mayores y
  los 3 menores) y, en la tasa, recalcula al menos dos departamentos desde
  numerador y denominador (la segunda fuente de una tasa propia es ese
  recálculo: `independencia: "baja"`, dilo).
- **`antes`**: verifica los dos extremos (hace N años y hoy) en la misma fuente
  y que la definición no cambió entre ambos; en dinero, confirma si es nominal.
