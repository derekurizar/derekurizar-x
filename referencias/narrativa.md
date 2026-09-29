# Narrativa: cómo cuenta una historia un hilo de datos

## Arco

`gancho → contexto → giro → impacto → cierre` en 4–8 tuits. Exactamente un
`giro` (el hecho que cambia la lectura); el `impacto` traduce a escala humana
(N de cada M hogares, per cápita, «lo que cuesta llenar el tanque»); el cierre
aterriza la tesis, reconoce lo que NO se afirma y lista las fuentes. **La
escalada la produce el orden de los hechos, no los adjetivos.**

## Gancho (T1): ocho tipos de `hook_tipo`

T1 siempre lleva texto (40–280 de peso X; primera línea ≤ 90; sin enlaces).
Elegir el tipo por la forma de la historia y registrarlo en `guion.hook_tipo`.
No repetir el `hook_evitar` del encuadre (el del último hilo).

| `hook_tipo` | Fórmula | Cuándo |
|---|---|---|
| `giro_inversion` | `[Dato en una dirección]. Pero [dato que la invierte].` | Récord con matiz, mejora con nivel bajo, per cápita. El ganador probado |
| `escala_humana` | Cifra macro → «N de cada M hogares/personas» | Totales en millones que no significan nada solos |
| `brecha_territorial` | `En [A], X. En [B], Y. Mismo país.` | Mapas, brechas urbano-rural |
| `pregunta_directa` | `¿[Pregunta contraintuitiva]? No es [lo obvio].` | Rankings; la respuesta llega en T2–T3 |
| `curiosity_gap` | Afirmación sorprendente; la cifra ancla en la línea siguiente | Guatemala vs mundo. **El gap se paga dentro del hilo (T2–T3)**, nunca «abrimos hilo para descubrirlo» |
| `mito_vs_dato` | `Podría pensarse X. Los datos dicen otra cosa: Y.` | Creencia común cuantificablemente falsa |
| `antes_despues` | `En [año], X. Hoy, Y.` | Series temporales, efemérides |
| `titular_clasico` | `TITULAR: cifra` | Solo récords o alertas literales; máximo 1 de cada 5 hilos; «récord» solo con una serie ≥ 10 puntos que lo respalde |

Anti-reglas: urgencia falsa («URGENTE», «ALERTA» solo para alertas reales);
rage-bait, encuadre partidista, culpables sin dato; engagement-bait («RT si…»,
«dale like», «no vas a creer»); superlativos no verificables; preguntas que la
cuenta no puede responder con datos; máximo una palabra en MAYÚSCULAS por tuit;
sin hashtags de campaña (0–2, `#Guatemala` opcional).

## Tarjeta y texto: la regla del dato héroe

Cada tarjeta tiene UN dato héroe y su titular es el hallazgo en lenguaje llano
(«Llenar el tanque cuesta 77% más que en enero»); el kicker es tema · unidad.
**El texto del tuit no repite la tarjeta**: no contiene ninguna línea del
titular ni dos o más de los números que la tarjeta muestra. El texto añade lo
que la imagen no puede: la pregunta, la comparación humana, la salvedad, la
transición al siguiente tuit. Si la tarjeta ya lo dice todo, el texto vacío pesa
más. Con imagen, T2..T(n−1) llevan ≤ 200 (ideal ≤ 140).

## Honestidad = credibilidad

- Lo que la evidencia no permite afirmar va en `no_afirma` (≤ 5 ítems, solo
  sobre cosas que un lector podría inferir del hilo).
- La salvedad de un dato va en la `nota` de su tarjeta («incluye los meses de
  subsidio», «promedio de 11 meses»).
- Conectores causales («por», «debido a», «impulsado por») solo con fuente que
  lo afirme; si no, «coincide con», «en paralelo a».
- «Récord», «histórico», «el más alto» exigen una serie ≥ 10 puntos en las
  cifras del tuit cuyo máximo sea ese valor.
- El cierre lista todas las fuentes de las cifras usadas (nombre corto de cada
  `visual.fuente`).

## Alt-text

Siempre, ≤ 1000 caracteres: tipo de gráfico, dato principal con su cifra y
unidad, y la fuente. Es la única versión textual del PNG.

## Estilo

Español guatemalteco neutro; lenguaje accesible; precisión («~», «cerca de» si
es aproximado); tono informativo ante datos negativos, sin exagerar los
positivos; emoji solo en el texto del tuit (nunca en la tarjeta) y con medida.
