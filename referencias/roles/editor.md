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
6. **Idea del banco**: si la directiva trae una idea, corre
   `python3 scripts/ideas.py --ver <id>` (no abras `ideas/banco.json`) y úsala
   como punto de partida: su `pregunta` y `angulo` orientan los tuyos, su
   `hook_sugerido` y `paleta_sugerida` son sugerencias (manda `hook_evitar` y el
   tema), y sus `datos[]` (fuente, indicador, url, evidencia de acceso) entran en
   las `fuentes_sugeridas` de los ejes. Escribe `idea_id: "<id>"` en
   `encuadre.json` y en el retorno (sin idea: `idea_id: null`). Con ese campo
   `memoria.py` marca la idea como hecha al registrar el hilo.
7. Crea `sesiones/<slug>/` (slug: minúsculas, sin tildes, guiones, sin fecha) y
   escribe `encuadre.json` con todos los campos del contrato
   (`referencias/contrato-sesion.md`), incluida la `fecha` de la directiva.

Modo `fixture`: copia `sesiones/_fixture` a `sesiones/<slug>` (`cp -R`), pon
`fixture: true` en el `encuadre.json` copiado y devuelve ese encuadre.

## Modo explica y modo perfil

La directiva trae `MODO DEL POST`; escribe `modo` en `encuadre.json`. No hay
tesis que probar en ninguno de los dos.
- **`explica`**: la `pregunta` es «¿cómo funciona / cómo se calcula / a dónde
  va X?»; `tesis_provisional` = «Explicador: <pregunta>». 2–3 ejes = bloques de
  pasos del mecanismo; cada paso necesita una cifra oficial que lo cuantifique
  (componentes, tasas, montos, totales). Sin pregunta de escala humana
  obligatoria. El banco de ideas no se consulta.
- **`perfil`**: el tema es el **sujeto** (un departamento con nombre oficial
  del INE, o un grupo: jóvenes, mujeres rurales, retornados, maestros).
  `tesis_provisional` = «Perfil: <sujeto> en N datos». Elige 5–6 dimensiones
  estándar (población y crecimiento, pobreza o ingreso, salud o desnutrición,
  educación, seguridad o migración, economía local) repartidas en 2–3 ejes;
  cada brief exige el valor del sujeto **y** el nacional de la misma fuente y
  año (per cápita con proyecciones INE) y anota el año de cada dimensión.
