---
description: Carrusel de 5–10 láminas 4:5 (1080×1350) para Instagram y Facebook, más su 9:16 para el modo foto de TikTok, desde un hilo o un dato ya entregados — portada legible en miniatura, las tarjetas del original rearmadas en Noche con un golpe arriba, «Por qué importa» y cierre con «Guárdalo» y «Sígueme en»; sin voz ni créditos (uso — /carrusel <slug|ultimo|carpeta> [9:16] [fixture]; siempre sale en 4:5 y 9:16; «9:16» rehace solo el 9:16 de un carrusel ya escrito; fixture corre la maqueta)
---

Eres el coordinador del flujo **/carrusel** de @DerekUrizar. Sus argumentos son: "$ARGUMENTS".
- `ultimo`, el slug de un hilo de `hilos/` o de un dato de `datos/`, o su carpeta: el original.
- `9:16`: rehace solo el 9:16 (TikTok, modo foto) de un carrusel cuyo 4:5 ya está en el TRABAJO.
- `fixture`: corre `make carrusel-fixture` (hilo y dato de prueba, sin web), lee una vez
  `sesiones/_fixture_carrusel/salida/contacto.png` y termina.

La guía es `referencias/flujo-carrusel.md`. Nunca publiques. Sin agentes: el `carrusel.json` lo escribes tú.

1. **PREFLIGHT**
   - `make doctor` (exit 0).
   - `python3 scripts/carrusel.py preparar <original>`: exige estado `listo|publicado`, rearma las tarjetas en Noche
     (un original sin cabecera de plantilla se bloquea: dilo y detente) e imprime el digesto y `TRABAJO`
     (`sesiones/<slug>/carrusel`). Si avisa que el original ya tiene carrusel, pregunta si se rehace (lo reemplaza).
2. **TEXTO** (lo escribes tú)
   - Lee `<TRABAJO>/digesto.md` y escribe `<TRABAJO>/carrusel.json` con su plantilla: 5–10 láminas (portada → 2+
     `tarjeta`/`texto` → `porque` → `cierre`), una `palabra_clave` que la gente busca, una `portada_forma` distinta de
     la última (CA8), la portada con una cifra con respaldo y un título de ≤ 8 palabras que se lea en miniatura, un
     golpe por tarjeta que no repita su titular, captions de tiktok, instagram y facebook (1.ª línea con la palabra
     clave; la de Instagram ≤ 125 caracteres) y el alt de cada lámina. Solo cifras del digesto; un derivado con
     `calculo`. Nada de lo que el original no afirma.
   - `python3 scripts/carrusel.py guion <TRABAJO> --check` hasta exit 0 (CA1–CA8).
3. **RENDER**
   - `python3 scripts/carrusel.py render <TRABAJO>` (4:5, CA9–CA12) y `… --formato 9:16` (zona segura del modo foto).
   - Lee **una vez** `<TRABAJO>/salida/contacto.png`: texto cortado, una tarjeta encogida o vacía, la portada que no se
     lee en chico, dos cosas en el acento. Si algo se ve mal, ajusta el texto en `carrusel.json`, repite `guion
     --check` y `render`.
4. **ENTREGAR**
   - `python3 scripts/carrusel.py entregar <TRABAJO>` → `<carpeta del original>/carrusel/` (PNG, `9x16/`,
     `carrusel.json`, `caption.md`, `alt.md`, `contacto.png`).
   - `python3 scripts/memoria.py --carrusel <carpeta del original>/carrusel` y `make validate` (exit 0).
5. **REPORTE**
   - La ruta de la entrega, el número de láminas y sus tipos, la palabra clave y la forma de la portada.
   - El caption de Instagram, listo para pegar (y la nota: el sonido se elige en la app).
   - Los avisos (CA8) y lo que corregiste tras ver el contacto.
   - **Mejoras al framework** (siempre el último punto; «ninguna» si no hubo): lo que se trabó o se hizo a mano, con el
     archivo y el cambio propuesto. Regístralas con `python3 scripts/memoria.py --mejoras <TRABAJO>/mejoras.json`
     (`{"flujo": "carrusel", "pieza": "<carpeta de entrega>", "mejoras": [...]}`) y no las apliques sin que el usuario
     lo pida. Con `fixture` se listan, no se registran.

Reglas:
- Solo cifras verificadas o ajustadas del original (CA4); la portada dice el dato, no lo esconde.
- Nunca se recortan los PNG del original: las tarjetas se re-materializan en Noche y se encajan en la lámina.
- Un carrusel por original; `sesiones/<slug>/carrusel/` queda como memoria de trabajo.
