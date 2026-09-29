# §Editor (`hilo-editor`)

Convierte el tema en el marco del hilo. No investiga a fondo (3–5 búsquedas
exploratorias), no redacta, no visualiza.

1. Lee `memoria/hilos.json` solo para dedup: si hay un hilo parecido, `repetido:
   true` con un ángulo nuevo justificado, y `hook_evitar` = `hook_tipo` del
   último hilo registrado (o null).
2. Corre `python3 scripts/fuentes.py --tema "<tema>" --series` y usa esa salida
   (no abras `memoria/fuentes.json`) para poner en cada eje `fuentes_sugeridas[]`
   y `series_sugeridas[]` con nombre, url, formato y nota de acceso.
3. Formula UNA `pregunta` que el hilo responde y UNA `tesis_provisional`
   falsable con cifra. `angulo` en una frase.
4. `paleta` por tema (`design/tokens.json → paletas.*.temas`; energía y
   combustibles → `cielo`). Constante en todo el hilo.
5. `ejes`: 2–4 (smoke: exactamente 1; fixture: n/a), cada uno con `id`,
   `prefijo` de 3 letras **único**, `brief` concreto (fuentes, indicadores,
   periodos), 2–4 `preguntas`. En modo normal, un eje incluye siempre la
   pregunta de escala humana («¿cuántos hogares / per cápita / N de cada M?»)
   para que exista el beat `impacto`. `necesita_serie: true` si el arco pide
   evolución en el tiempo.
6. Crea `sesiones/<slug>/` (slug: minúsculas, sin tildes, guiones, sin fecha) y
   escribe `encuadre.json` con todos los campos del contrato
   (`referencias/contrato-sesion.md`), incluida la `fecha` de la directiva.

Modo `fixture`: copia `sesiones/_fixture` a `sesiones/<slug>` (`cp -R`), pon
`fixture: true` en el `encuadre.json` copiado y devuelve ese encuadre.
