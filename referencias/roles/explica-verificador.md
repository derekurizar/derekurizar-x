# §Verificador de `/explica` (`explica-verificador`)

Nada de lo que el video afirma sale sin su fuente guardada y su cita literal. Partes de los hallazgos del investigador
y das un veredicto por afirmación y por cifra. Índice: `referencias/flujo-explica.md`.

**Presupuesto**: ≤ 6 búsquedas, ≤ 8 lecturas nuevas, ≤ 15 min.

## Insumo

`python3 scripts/explica.py digesto <TRABAJO> --para verificador --eje <EJE>`: el encuadre, tu eje y los hallazgos
(cada uno con sus citas).

## Cómo verificas

1. Abre el texto guardado de cada fuente y comprueba que la cita está TAL CUAL (el gate lo mide).
2. Busca una segunda fuente independiente (otro grupo) o la oficial. Una definición o una regla con UNA fuente oficial o
   académica ya cuenta como confirmada. Un dato de prensa necesita la fuente oficial o un segundo grupo.
3. **Vigencia**: una norma, a la fecha (¿la reformaron?); un dato, el último publicado (si hay uno más nuevo, cámbialo
   y dilo en `nota`).
4. **Veredicto** (`estado`), uno por afirmación y por cifra:
   - `confirmado`: 2 grupos, o 1 oficial o académica;
   - `una_fuente`: una fuente seria sin contradicción;
   - `en_disputa`: las fuentes difieren; la `nota` trae las dos versiones y la voz atribuye;
   - `no_confirmado`: no se cuenta.
5. Lo que el encuadre pide como `{cifra: id}` conserva ese id: la calculadora lo busca.

## Salida

`<TRABAJO>/verificacion_<EJE>.json`: las mismas listas (`afirmaciones`, `cifras`, `citas`) con `estado`, `fuentes`
(todas las que cuentan, cada una con `archivo` y `cita`) y `nota`, más `descartados` con su motivo. Luego `python3
scripts/explica.py afirmaciones <TRABAJO> --check --eje <EJE>` (E2) hasta exit 0. Forma en
`sesiones/_fixture_explica/verificacion_gt.json`.
