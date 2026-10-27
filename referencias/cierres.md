# Cierres de /video: la consecuencia (lo normal), otro remate o una pregunta (a veces)

El cierre es la última pantalla: primero las **Conclusiones** (el `resumen` mientras la voz las dice) y después la
**frase final** sola, en grande, con «Sígueme en». Esta guía dice qué frase final escribir. La lee el guionista
(`referencias/roles/video-guionista.md`, regla 9) y la juzga el crítico (C8). Las reglas que se pueden medir viven en
`scripts/video.py guion --check` (F1–F8).

**Por qué existe** (2026-10-23): los cinco primeros videos cerraron con el mismo molde, una pregunta sobre la vida del
espectador:

| Video | Pregunta |
|---|---|
| Crimen | «Y tú, ¿has denunciado alguna vez una extorsión?» |
| Madres niñas | «Y tú, ¿a qué edad fue mamá tu mamá?» |
| Sequía | «Y en tu comunidad, ¿se perdió la milpa este año?» |
| Tráfico | «¿Cuánto tardas tú en llegar al trabajo?» |
| Cárceles | «¿Cuántas personas duermen en tu casa por cada cuarto?» |

Los defectos:
- **Siempre el mismo formato.**
- **Analogías falsas:** los cuartos de una casa no son los espacios de una cárcel. El hacinamiento carcelario se mide
  como población frente a la capacidad oficial, no por cuarto, y compararlo con las casas lo minimiza.
- **Preguntas invasivas:** la edad de la madre o haber sido víctima de extorsión.

Venían de la regla anterior, que exigía una pregunta «sobre la experiencia del espectador, nunca una opinión».

**Decisión del usuario** (2026-10-23): «Me gusta más el remate y a veces pregunta».

**Segunda decisión** (2026-10-24), al ver el video de desnutrición, que cerró con un remate `bucle`: «De cada 7 niños
muertos por desnutrición, 6 no tenían 2 años.» El usuario dijo: «terminar con un dato no es un buen punch, la
consecuencia de un dato sí». Su ejemplo: si hay 10 muertes al año, «este año 10 padres de familia perderán a sus
hijos». Por eso:
- **Las cifras van en las conclusiones** (la voz antes de la frase final y el `resumen`).
- **La frase final dice la consecuencia**: lo que esa cifra le hace a quien la vive. Ese video quedó en «Este año, 34
  familias ya enterraron a un hijo por desnutrición.»
- Los remates de dato (`bucle`, `cuenta`, `escala`) **salen del catálogo**. El final ya empalma con el inicio porque el
  montaje repite el primer cuadro del gancho después de «Sígueme en».
- Del ejemplo del usuario se ajustan dos cosas, y las dos son reglas del gate (F8):
  - «perderán» **proyecta** lo que la fuente no proyecta: el año está abierto y `no_afirma` dice que 2026 no tiene por
    qué cerrar como 2025.
  - «de momento parece que no hay nada que se pueda hacer» es **fatalismo** que el hilo no sostiene: el 56 % de los
    niños en seguimiento se recupera.

## 1. Lo que dice la evidencia

| Hallazgo | Fuerza | Fuente |
|---|---|---|
| En video corto pesan más ver hasta el final y compartir que comentar: Instagram no pone «comentar» entre las señales principales de Reels y YouTube no nombra los comentarios entre las suyas; TikTok sí los cuenta como interés | A | [Instagram](https://about.instagram.com/blog/announcements/instagram-ranking-explained) · [YouTube](https://blog.youtube/inside-youtube/on-youtubes-recommendation-system/) · [TikTok](https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you) |
| Meta baja la distribución de lo que pide comentar, votar, etiquetar o compartir de forma explícita («comenta SÍ»), y lo detecta también en el audio; pedir ayuda o una opinión genuina no se castiga | A | [Meta, cebo de interacción](https://transparency.meta.com/features/approach-to-ranking/content-distribution-guidelines/engagement-bait/) |
| Las preguntas íntimas, que juzgan o exponen hacen que la gente no responda o mienta | A (encuestas) | Tourangeau y Yan 2007, *Psychological Bulletin* |
| Hablar del grupo contrario sube un 67 % los compartidos y la ira; los comentarios incivilizados reciben más votos y más denuncias | A | [Rathje y otros 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8256037/); Muddiman y Stroud 2017 |
| Las preguntas con pocas opciones dan comentarios más civilizados que las abiertas | B | Engaging News Project (U. de Texas) |
| De unos 40 Shorts de explicadores y medios en español, solo 4 piden comentarios; en temas duros (cárceles, violencia, migración) nadie pregunta por la vida del espectador: cierran con un dato, con lo que no se sabe o con una pregunta sobre el sistema | B (correlación) | El Faro, Divergentes, Ocote, El Orden Mundial, VisualPolitik, Kurzgesagt (frases en §4) |
| Traducir la cifra a algo conocido («perspectiva») mejora el recuerdo, la estimación y la detección de cifras manipuladas; el efecto dura semanas | B+ (3 experimentos, más de 3,200 personas) | [Barrio, Goldstein y Hofman, CHI 2016](https://www.microsoft.com/en-us/research/?p=215388) |
| La emoción y la donación caen desde la segunda vida en peligro; se recuperan cuando el grupo se presenta como **una unidad** («una familia», «un aula entera») y no como «miles» | B (4 experimentos) | [Västfjäll, Slovic y otros 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4062481/) |
| La gente apaga la emoción por adelantado cuando espera que le pidan algo: un cierre que suena a «haz algo ya» o que abruma, no conmueve | B (3 experimentos, un laboratorio) | [Cameron y Payne 2011](https://bkpayne.web.unc.edu/wp-content/uploads/sites/7990/2015/02/CameronPayne2011.pdf) |
| La víctima identificable mueve más que la cifra, y apilar estadísticas encima de ella la debilita; el efecto es pequeño y no siempre replica | B, discutido (metaanálisis r = .05; la réplica de 2024 no lo encontró) | [Small, Loewenstein y Slovic 2007](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Sympathy_and_callousness.pdf) · [réplica](https://forrt.org/flora-replication-atlas/doi/10.1016/j.obhdp.2006.01.005/) |
| Sobre niños: no identificar ni estigmatizar a un niño ni culpar a la familia; ante la duda, la situación general y no un caso. Dignidad, sin sensacionalismo | A (guías) | [UNICEF](https://www.unicef.org/media/reporting-guidelines) · [Código Dóchas](https://www.dsaireland.org/download/pdf/dochas_code_of_conduct.pdf) · [EJN](https://ethicaljournalismnetwork.org/?p=17) |
| Responder los primeros comentarios (con video en TikTok o con un corazón en YouTube) se asocia con más comentarios | A/B | [TikTok](https://newsroom.tiktok.com/en-us/product-tutorial-reply-to-comments-with-video) · [arXiv 2404.03612](https://www.arxiv.org/abs/2404.03612) |

## 2. Catálogo

`cierre.tipo` es `remate` (lo normal) o `pregunta` (a veces). `cierre.forma` dice cuál, y `cierre.final` es la frase
con la que termina la voz (la última de `texto`), ≤ 14 palabras.

**Remates** (una frase que se queda con el espectador, sin pedirle nada). **Lo normal es `consecuencia`**: la frase final
no es un dato sino lo que el dato le hace a la gente. Va con `consecuencia` {`mecanismo`, `quien`, `verbo`}:

| mecanismo | Qué dice | Ejemplo |
|---|---|---|
| `quien` | quién lo vive, como unidad que se pueda imaginar | «Este año, 34 familias ya enterraron a un hijo por desnutrición.» |
| `perdida` | lo que pierden: tiempo, dinero, escuela, años de vida, la cosecha | «Un conductor paga casi el doble por el mismo galón de diésel.» |
| `reloj` | lo que pasa mientras: al día, a la semana (con `calculo` del hilo) | «Cada día, 61 niños más llegan a un centro de salud con desnutrición.» |
| `despues` | lo que les toca después | «Y mañana esas familias vuelven a la misma fila del centro de salud.» (solo si el hilo lo sostiene) |
| `espera` | lo que esperan y no llega | «Y los presos sin condena siguen esperando juicio.» (cárceles, si el hilo lo sostiene) |

Los otros remates, a veces:

| forma | Qué hace | Ejemplo (cárceles) |
|---|---|---|
| `legado` | **solo `/historia`, y ahí es lo normal**: lo que la gente hace hoy con lo que la historia dejó; `consecuencia {quien, verbo en presente}`, sin `mecanismo` | «Hoy, sus hijos y sus nietos siguen tomando Incaparina.» · «Y los niños la siguen abriendo.» |
| `pendiente` | deja lo que no se sabe o lo que sigue sin resolver (del hilo, nunca inventado) | «Y nadie sabe cuántos metros mide un espacio.» |
| `quien_decide` | dice en quién está la decisión, con lo que el hilo afirma | «Los Q226 millones son para remozar, no para abrir espacios.» |

**Retirados** (2026-10-24, son datos y no remates): `bucle` (volver a la cifra del gancho), `cuenta` y `escala`. Su
contenido va en las conclusiones.

**Preguntas** (solo a veces; sobre el sistema, nunca sobre la intimidad):

| forma | Qué hace | Ejemplo (cárceles) |
|---|---|---|
| `elegir` | dos o tres opciones de política pública; ninguna castiga a un grupo | «¿Qué primero: más cárceles o juicios más rápidos?» |
| `prediccion` | qué pasará con la cifra; se contesta con lo que el video mostró | «Para 2030, ¿habrá más o menos presos por espacio?» |
| `decidir` | «si tú decidieras…» con un presupuesto o una regla real del hilo | «Si tú decidieras los Q226 millones, ¿remozarías o abrirías cárceles nuevas?» |
| `lugar` | lo que el espectador sabe de su municipio o departamento, sin identificar a nadie | «¿Hay una cárcel en tu departamento?» |
| `porque` | el porqué que el video no cierra, sin bandos | «¿Por qué crees que los espacios casi no crecen?» |
| `dato_faltante` | pide ayuda para el siguiente video (no es cebo) | «¿Qué dato de las cárceles quieres que busque?» |
| `experiencia` | la vida del espectador, **solo** en temas que no exponen (tráfico, precios, clima) y con la misma unidad que el dato | «¿Cuánto pagaste por el galón esta semana?» |

## 3. Reglas

| # | Regla | Dónde |
|---|---|---|
| F1 | `tipo` remate o pregunta y `forma` del catálogo; `final` es la última frase de `texto` | gate |
| F2 | `final` ≤ 14 palabras y ≤ 90 caracteres; una pregunta es una sola y termina en «?»; un remate no lleva «?» | gate |
| F3 | **Anclada al tema**: la frase final nombra el fenómeno del video (una palabra del tema, de los titulares o del concepto de una cifra del hilo). Nada de analogías de otro ámbito (la casa por la cárcel); si compara con la vida del espectador, la misma unidad y la misma definición | gate (la palabra) + crítico (la analogía) |
| F4 | **Sin cebo**: ni «comenta», «etiqueta», «comparte», «escribe sí», «te leo», en la voz ni en pantalla | gate |
| F5 | **No expone**: en un tema sensible (cárcel, violencia, delito, salud sexual o reproductiva, migración) la pregunta no es de `experiencia` ni toca la casa, la familia o «alguna vez» del espectador; el grupo vulnerable nunca es blanco («¿merecen…?», «¿qué harías con ellos?») | gate + crítico |
| F6 | **Un remate no es un dato**: a lo más una cifra (cuántos lo viven) y nunca la del gancho. La `consecuencia` y el `legado` declaran `quien` (gente: familias, niños, nietos, conductores, presos…, tal cual en la frase) y `verbo` (lo que les pasa, conjugado, en la frase; en el legado, en presente); solo la consecuencia lleva `mecanismo` (quien, perdida, reloj, despues, espera) | gate |
| F7 | **Rotación**: una pregunta nunca sigue a otra (si el video anterior cerró con pregunta, este cierra con remate); la `forma`, salvo `consecuencia` y `legado` (las normales), no repite la de los últimos 2 videos, y el `mecanismo` de consecuencia no repite el del último (`memoria/videos.json`; el digesto los lista en «Cierres recientes») | gate |
| F8 | **No afirma de más**: sin fatalismo («no hay nada que hacer», «nadie hace nada», «no tiene solución») y sin futuro de una pérdida («perderán», «morirán») salvo que `consecuencia.proyeccion` dé el id de una cifra que proyecte; lo que ya pasó va en pasado o presente («ya», «este año van») | gate |

Además, para el crítico (C8):
- Un final que solo repite o reformula una cifra **bloquea**.
- La consecuencia se sigue del dato **sin suponer de más**. «34 familias» por 34 muertes sí vale. «Sus hermanos dejaron la
  escuela» no, si el hilo no lo dice.
- La consecuencia se oye como algo que le pasó a alguien, no como un titular.
- La pregunta se contesta en una línea sin buscar nada.
- Ninguna afirma más que el hilo (`no_afirma` manda) ni repite la de otro video (C11).

Cómo escribir la consecuencia (de la evidencia de §1):
1. **El sujeto es gente, como colectivo o unidad**: familias, madres, una comunidad. Nunca un niño identificable (UNICEF).
   Mejor una unidad que se imagina («un aula entera», «34 familias») que «miles».
2. **El verbo es lo que les pasó**, en el tiempo de la fuente: pasado o presente para lo que ya ocurrió.
3. **Ninguna cifra nueva** y la cifra no se apila sobre la persona: a lo más una, la de cuántos lo viven.
4. **Sin adverbios ni adjetivos de emoción** («lamentablemente», «desgarrador», «trágicamente»): la emoción la pone quien mira.
5. **Sin culpa ni fatalismo**: si hay responsable, es el sistema («no llegó el programa»), nunca la familia; nada de «no
   hay remedio». Tampoco suena a «haz algo ya»: la gente se protege y deja de sentir.
6. **La prueba**: ¿la firmaría la fuente y la aceptaría la familia?

**En `/historia`** (decisiones del usuario, 2026-10-26): lo normal es el **`legado`**, lo que la gente hace hoy con lo
que la historia dejó («de un edificio de adobe a la taza que hoy toman sus nietos»): es emotivo sin ser duro. La
`consecuencia` queda para la historia que termina mal (un caso, una caída): lo que le hizo a una persona o a un grupo
concreto, dicho llano. Lo que no vale es lo **neutro**, donde nadie hace nada («la receta cambió y la marca sigue»,
«la empresa creció»), ni una atribución en el final («según…», H9); las reglas de arriba siguen valiendo (la emoción la
pone el hecho, no los adjetivos).

## 4. Cierres reales de referencia (forma, no texto)

- El Faro (muertes en cárceles): «…el gobierno ha declarado información reservada todo lo relacionado con fallecidos en
  centros penales.» → `pendiente`.
- VisualPolitik (alquiler): «Esto, amigos, no va de ideologías, va de aritmética.» → `cuenta` (forma retirada: es un dato).
- Kurzgesagt: «…for the price of a coffee a week, we can still protect what's left.» → `escala` (retirada; leída como lo
  que se pierde, sería `consecuencia · perdida`).
- Plaza Pública (nombramientos): «La decisión final no está en la IA. Está en la comisión de postulación…» → `quien_decide`.
- El Orden Mundial (Auschwitz): «¿Dónde pondrías el límite? ¿Interés histórico o morbo?» → `elegir`.
- Divergentes (hospitales): «¿Ustedes sienten este déficit presupuestario en su día a día?» → `experiencia` sobre un
  servicio público, que no expone.
- New York Times (1,000 nombres de muertos por covid, 24-may-2020): «They were not simply names on a list. They were
  us.» → `consecuencia · quien` (es el subtítulo de la portada, no un cierre de video).
- Washington Post, «Cut Short» (2022): cada barra es una frase sobre una persona, cortada a media palabra → `consecuencia
  · perdida`.
- Periscopic, muertes por armas en EE. UU. (2013): 9,595 personas, 413,908 «años robados» → `consecuencia · perdida`.
- UNICEF/OMS (2018): «A child under 15 dies every five seconds.» → `consecuencia · reloj` (es un titular).
- Prensa Libre (Jocotán): «Los programas sociales no llegaron a Jocotán» → `consecuencia · espera` (es un titular); la
  nota muestra el riesgo: los funcionarios culpan a la comadrona.
- Our World in Data (Roser 2022): «the world is awful, the world is much better, and the world can be much better.» →
  contrapeso al fatalismo.
- Contraejemplo: VisualPolitik (Venezuela): «…una de las tantas catástrofes que conlleva el régimen bolivariano.»
  (remate partidista).

Después de publicar, responder los primeros comentarios (un corazón en YouTube, un video de respuesta en TikTok) suma
más que pedirlos en la voz.
