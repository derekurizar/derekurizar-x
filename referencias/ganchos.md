# Ganchos de /video: catálogo, reglas y evidencia

El gancho es la escena 1: decide en 1–3 segundos si alguien deja de deslizar. Esta guía es la fuente única para el
agente que los escribe (`video-gancho`, `referencias/roles/video-gancho.md`), el crítico que elige
(`video-critico`, «Selección de gancho») y el guionista que construye el resto del video encima. Las reglas que se pueden
medir viven en código (`scripts/video.py ganchos --check` y `guion --check`); las demás las juzga el crítico.

**Por qué existe** (2026-10-23): los cinco primeros videos abrieron igual, con «En Guatemala + una cifra suelta» (8,000
kilos, 168 bebés, 23 lugares, 2,000 vehículos, 4.7 presos). Una investigación con cuatro agentes encontró que eso
reúne los dos errores más comunes del contenido informativo: **abrir con contexto en vez de tensión** y **dar la cifra
sin un referente**.

## 1. Lo que dice la evidencia

Fuerza de la evidencia: **A** = fuente oficial o estudio revisado · **B** = práctica documentada de creadores con
resultados · **C** = opinión o blog sin método. Casi no hay datos publicados de retención por tipo de gancho: lo firme
es poco y se usa como regla; lo demás, como criterio.

| Hallazgo | Fuerza | Fuente |
|---|---|---|
| Una cifra con su comparación (razón, ranking, cambio de unidad) se entiende, se estima y se recuerda mejor que sola; el efecto dura semanas | A | Barrio, Goldstein y Hofman, CHI 2016 ([MSR](https://microsoft.com/en-us/research/?p=215388)); Riederer y otros, CHI 2018 ([MSR](https://www.microsoft.com/en-us/research/?p=594019)); «escalas concretas», Chevalier y otros, InfoVis 2013 ([aviz](https://aviz.fr/concretescale)) |
| Cada palabra negativa sube los clics ≈ 2.3 %, cada positiva los baja ≈ 1 %; la tristeza suma, el miedo resta, la ira no cambia nada (105,000 titulares) | A (titulares, no video) | Robertson y otros 2023, *Nature Human Behaviour* ([PDF](https://epub.ub.uni-muenchen.de/94951/1/s41562-023-01538-4.pdf)) |
| Mucha gente ve sin sonido: el texto en pantalla debe contar el gancho; di de qué va el video pronto, sin cebo | A | Mosseri, Instagram ([Inman](https://news.inman.com/2025/03/07/head-of-instagram-reveals-secrets-to-social-media-success/)); guía de Meta ([Marketing Dive](https://www.marketingdive.com/news/facebook-offers-tips-for-converting-tv-ads-to-mobile/448510/)) |
| La propuesta en ≤ 3 s, el gancho en ≤ 6 s, 5–10 palabras por segundo en texto (guía para anuncios) | A (anuncios) | TikTok Ads ([guía](https://ads.tiktok.com/help/article/creative-best-practices)) |
| Desde el 31-mar-2025 cada repetición de un Short cuenta como vista: el bucle final → inicio vale | A | YouTube, vía [Brandwatch](https://social-media-management-help.brandwatch.com/hc/en-us/articles/26214254055709-YouTube-Changes-to-Views-Counts-on-Shorts) |
| La curiosidad funciona cuando la respuesta llega; un titular en forma de pregunta genera expectativas más negativas que uno que anuncia lo que viene | A (lab.) | Kang y otros 2009 ([PDF](https://www.cmu.edu/dietrich/sds/docs/loewenstein/WickCandleLearning.pdf)); Brod 2019 ([PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6803639/)); [Journalism.co.uk](https://www.journalism.co.uk/readers-perceive-question-based-headlines-more-negatively-study-shows/) |
| Texto, imagen y voz dicen lo mismo («triple hook»); 3–5 palabras grandes; contexto → «pero» → giro | B | Kallaway ([resumen](https://opentools.ai/youtube-summary/how-to-create-irresistible-hooks-and-blow-up-your-content)) |
| Entrar directo, no narrar lo que ya se ve | B | Jenny Hoyos ([Demand Curve](https://www.demandcurve.com/newsletters/growth-newsletter-187)) |
| Los explicadores en español con más vistas señalan algo concreto (un lugar, un objeto, un mapa) antes de la cifra y la traducen a escala humana en la misma oración; le hablan a una persona («usas», «tu cocina») | B (correlación) | El Orden Mundial, Johnny Harris, Vox, VisualPolitik, Curiometro (frases en §5) |
| Temas duros: entrar por el espacio o el objeto, no por los cuerpos; exhibir presos, «son animales» o el superlativo sin fuente restan credibilidad | B | críticas a Luisito Comunica en el CECOT ([Publimetro](https://www.publimetro.com.mx/entretenimiento/2024/02/09/luisito-comunica-es-criticado-por-exhibir-a-prisioneros-del-cecot/)); INDH Chile ([The Clinic](https://www.theclinic.cl/2016/10/04/gendarmes-en-picada-contra-programas-de-tv-al-interior-de-la-carcel-la-privacion-de-libertad-no-puede-ser-un-show/)) |
| Movimiento y sonido en el primer segundo, cortes cada 2–4 s, voz desde el cuadro 0 | C | consenso de guías sin método |

Lo que **no** está probado y no se usa como regla: «el 71 % decide en 3 s», «≥ 70 % de visto frente a deslizado»,
«+18 % con un whoosh». Para saber qué funciona con esta cuenta, la **versión B** (§7) compara dos ganchos del mismo video
en «Visto frente a deslizado» de YouTube Studio.

## 2. Familias (`familia`)

Cada candidato prueba un **mecanismo** distinto. Los ejemplos son del hilo de cárceles: Pavón tiene 4,464 presos en un
penal para 960, el país 23,382 para 6,842 espacios, 16,540 (7 de cada 10) sin lugar, puesto 9 de 209 y una granja al
515 %.

| familia | Mecanismo | Plantilla | Ejemplo (pantalla · voz) | Visuales |
|---|---|---|---|---|
| `contraste` | rompe una expectativa que el propio gancho plantea | lo esperado → «pero» → lo real, con las dos cifras | «Hecha para 960» · «Esta cárcel se construyó para 960 personas. Pero en 2025 tenía 4,464.» | llenado, pareja, cifra |
| `paradoja` | una frase que choca con lo que se cree; las cifras van en pantalla | «hay más X que Y», «X baja y Y sube» | «16,540 contra 6,842» · «En las cárceles de Guatemala hay más presos sin lugar que con lugar.» | pareja, figuras, cifra |
| `lugar` | señala algo concreto antes de la cifra («Esto es…») | lugar u objeto → la cifra traducida | «Pavón» · «Esto es Pavón, en Fraijanes. Lo hicieron para 960 personas y tenía 4,464.» | lugar, llenado, cifra |
| `escala` | traduce la cifra a algo que se ve en 1 s | «Donde cabe 1, hay 3», «7 de cada 10» | «7 de cada 10» · «7 de cada 10 presos de Guatemala no tienen un lugar en la cárcel.» | figuras, llenado, pareja |
| `tu` | segunda persona: el espectador es el protagonista; escala doméstica | «Tu…», «Si tú…», «Imagina…» y la cifra en tu escala | «1 lugar, 3 presos» · «Imagina tu cuarto, hecho para uno, con tres personas adentro: así están las cárceles de Guatemala.» | figuras, llenado, pareja, cifra |
| `pregunta` | predicción que se contesta enseguida | pregunta específica + respuesta con cifra en el mismo gancho | «Para 960. ¿Cuántos hay?» · «Un penal para 960 personas. ¿Cuántas hay adentro? 4,464.» | cifra, pareja, llenado |
| `ranking` | comparación social con fuente | «De N, solo K…», «el puesto X de N» | «9 de 209» · «De 209 países, solo 8 tienen cárceles más llenas que Guatemala.» | cifra, lugar |
| `resultado` | el final primero, luego el cómo | el resultado con su referente | «×4.7» · «Pavón tiene casi cinco presos por cada lugar: así se llegó ahí.» | cifra, pareja, figuras |

Una familia no es una frase hecha: la del ejemplo no se copia (el crítico la coteja con «Frases ya usadas», C11).

## 3. Visuales (`visual` y `visual_datos`)

El visual es lo que se ve en el cuadro 0 y lo que el pulgar entiende antes de leer. Todos sus números llevan respaldo:
el id de la cifra (`"pen-c02.partes[1]"`) o una expresión `calculo`; un literal solo vale si está en `datos.json`.

| visual | Qué se ve | `visual_datos` | Cuándo |
|---|---|---|---|
| `cifra` | la cifra grande y la línea (golpe.html) | — | la cifra ya trae su referente en pantalla («×4.7», «9 de 209») |
| `llenado` | un contenedor con la capacidad ya llena de puntos; al decir el total, los puntos lo desbordan y el contador sube | `{capacidad, total, unidad}` (0 < capacidad < total; `unidad` ≤ 24) | capacidad frente a ocupación, presupuesto frente a gasto, lo previsto frente a lo real |
| `pareja` | dos bloques de área proporcional; el primero entero, el segundo crece al decirlo | `{a: {valor, etiqueta}, b: {valor, etiqueta}}` (etiquetas ≤ 24) | dos magnitudes comparables: con lugar frente a sin lugar, Guatemala frente a la región |
| `figuras` | N personas; las K primeras se encienden al decir «K de cada N» | `{de_cada: [K, N], etiqueta, calculo}` (N 2–100; el `calculo` da K/N·100 o N/K) | proporciones de personas |
| `lugar` | los 22 departamentos; al nombrar el lugar cae el pin, el departamento se enciende y la cámara se acerca | `{depto, etiqueta}` (nombre o GTxx; etiqueta ≤ 30, p. ej. «Pavón · Fraijanes») | la familia lugar y los rankings territoriales |

El visual y la pantalla van juntos: con un visual, la pantalla es corta («Hecha para 960») y el visual cuenta el resto.
El icono (`icono`) va solo con el visual `cifra`.

## 4. Reglas

| # | Regla | Dónde |
|---|---|---|
| R1 | **Se cuenta en silencio**: `pantalla` (una cifra o ≤ 4 palabras, ≤ 24 caracteres) y `linea` (≤ 8 palabras, ≤ 60) se leen solas y **nombran de qué o de quién se habla** («Penal para 960», no «960 lugares»; «presos» o «cárcel» en pantalla, no solo en la voz); la familia `pregunta` termina en «?» | gate (forma) + crítico (sujeto) |
| R2 | **Referente**: la cifra nunca va sola. Pantalla y línea traen dos cifras, «K de cada N», «×N», «de 209», «por lugar», o el visual es llenado, pareja o figuras | gate |
| R3 | **Tensión primero**: la voz no abre con contexto («En Guatemala…», «Según…», «Hoy les cuento», «En este video», «Hablemos», «El Ministerio / La Dirección / El Sistema…») | gate |
| R4 | **Triple alineación**: la voz dice las palabras clave de la pantalla y los números del visual (o la pantalla los muestra); la oración que dice la pantalla lleva verbo (`verbo`) | gate |
| R5 | **3 segundos**: primera oración ≤ 4 s (≈ 62 caracteres ya en palabras), voz del gancho ≤ 7.5 s, T1 antes de 6.5 s | gate |
| R6 | **Guatemala en ≤ 6 s**: dicha o leída en el gancho o en la primera oración de T1; el script ya no antepone «En Guatemala» | gate |
| R7 | **Honestidad temporal**: «hoy / ahora / actualmente» solo con datos del año en curso; si no, el periodo («en 2025 tenía»). El presente sin esas palabras («hay», «así están») con un dato viejo lo marca el crítico | gate + crítico |
| R8 | La `pregunta` se contesta con una cifra dentro del mismo gancho | gate |
| R9 | **Rotación**: la familia no repite la de los últimos 2 videos ni el visual el del último (`memoria/videos.json`; el digesto los lista) | gate |
| R10 | Cada gancho trae al menos un número con respaldo en sus primeros segundos (pantalla, línea, visual o voz) | gate |
| R11 | **Encuadre**: pérdida y tristeza sí, miedo no; sin morbo, sin deshumanizar («personas presas», no «reos peligrosos»), sin superlativo sin fuente; ninguna palabra que el dato no dice («duermen», «camas», «celdas de 3×3») | crítico |
| R12 | **Primer cuadro lleno**: la cifra o el visual están desde el cuadro 0 (miniatura del feed y vuelta del bucle) | render + aviso V15 de `revisar` |

Fuera de reglas, para elegir entre candidatos: un gancho que funciona en la cuenta de otra persona sobre otro tema no
basta; gana el que mejor contesta **¿qué ve el pulgar en el segundo 1 y por qué se queda en el 3?**

## 5. Frases reales de referencia (forma, no texto)

- El Orden Mundial: «Rusia está dentro de Europa. Y no, no te voy a hablar de la guerra de Ucrania. Te lo explico con un
  mapa en un minuto.» (afirmación que choca + promesa con plazo)
- VisualPolitik: «Desde 2018 España ha ganado 2,6 millones de habitantes, pero solo ha construido 690.000 viviendas. Casi
  cuatro personas nuevas por cada casa nueva.» (contraste + escala humana en la misma oración)
- Vox: «Instant ramen… the number one sold item at prison commissaries.» (objeto cotidiano como puerta a la cárcel)
- Johnny Harris: «Quiero mostrarte este mapa de los 54 países que participaron en un programa secreto…» (mapa + cifra)
- Curiometro: «Hay una cárcel donde el Estado no te da una celda, te la vende.» (paradoja con mecanismo)
- Contraejemplo (7.9k vistas): «Los centros carcelarios han sobrepasado en un 100 % su capacidad» (contexto, cifra sin
  referente, institución como sujeto).

## 6. Cómo se elige

1. `video-gancho` escribe 4–5 candidatos de familias distintas en `ganchos.json`, al menos 2 con un visual que no sea
   la cifra sola, y pasa `python3 scripts/video.py ganchos <TRABAJO> --check`.
2. `video-critico` (modo selección) los mira **en silencio** (pantalla, línea y visual) y luego con la voz; puntúa
   `silencio, referente, tension, alineacion, honestidad, novedad` (1–5) y aplica R11; escribe `seleccion.json` con el
   ganador y el segundo. En `/historia`, `reserva` (no regala una revelación del encuadre) sustituye a `referente`
   (ver «Modo historia» de `referencias/roles/video-critico.md`).
3. Si el crítico dejó arreglos para el ganador o el segundo, `video-gancho` los aplica (mismo id, familia y visual) y
   vuelve a pasar el gate: el guionista no puede tocar la escena 1.
4. El guionista corre `video.py ganchos <TRABAJO> --usar` (el ganador pasa a la escena 1) y escribe el resto sin tocar el
   gancho. El gate del guion comprueba que la escena 1 sea la elegida y repite R1–R10 con T1 a la vista (R6).

## 7. Versión B

El segundo lugar queda en `ganchos.json`. `python3 scripts/video.py variante <TRABAJO>` arma `variante_b/` con el mismo
video salvo la escena 1 y la voz de esa escena sola (≈ 100 créditos); al terminar, `variante --cerrar` deja
`salida/video_b.mp4` y `entregar` lo copia junto a `video.mp4`. Se publican las dos versiones y se compara «Visto frente a
deslizado» (YouTube Studio) o la retención a 3 s (TikTok): con el tiempo, esa comparación reemplaza a las reglas C.
