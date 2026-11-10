# Investigación: qué sostiene cada regla

Lo que se sabe (y lo que no) sobre retención, curiosidad, historia, plataformas y movimiento, con su nivel de evidencia
y la regla del framework que sostiene. Búsqueda del 2026-11-10. Se revisa cuando `/analyze-improve` traiga métricas
propias que confirmen o contradigan algo.

**Niveles**
- **A · sólida**: estudios revisados por pares o metaanálisis.
- **B · plataforma**: lo que la plataforma dice de sí misma (aquí casi siempre leído de segunda mano).
- **C · oficio**: blogs de creadores y de vendedores de herramientas. Hipótesis a medir, nunca regla por sí sola.

Una regla nueva se apoya en A, o en B + una medición propia. Lo de nivel C entra como opción o como aviso.

## 1. Aprendizaje multimedia (A)

Mayer, revisión de video instruccional:

| Principio | Qué dice | Evidencia | Regla que sostiene |
|---|---|---|---|
| Coherencia | Quitar lo que no explica | 18 de 19 pruebas, efecto 0.86 | Noche, una sola cosa en acento, el margen del 16:9 solo con quien la voz nombra |
| Señalización | Resaltar lo esencial cuando se dice | 26 de 28 pruebas, efecto 0.70 | V26 (la cifra se señala cuando la voz la dice), zoom a la cifra, subrayado |
| Redundancia | Texto que repite la voz estorba poco | 8 de 12 pruebas, efecto 0.10 | «Sin subtítulo doble» basta; no vale endurecerlo |
| Segmentar | Trozos cortos | A favor | Actos, rótulos, capítulos |

Guo, Kim y Rubin (2014), 6.9 millones de sesiones de video en edX: los videos cortos retienen más; recomiendan trozos de
menos de 6 minutos. Sostiene capítulos de 85–140 s en el largo.

Límite: son materiales educativos de laboratorio y de cursos, no videos de redes.

## 2. Curiosidad (A)

- Loewenstein (1994): la curiosidad sale del hueco entre lo que sé y lo que quiero saber.
- Kang y otros (2009) y réplicas (2023): es máxima cuando la persona cree saber **a medias** (U invertida). Lo
  totalmente desconocido y lo obvio enganchan menos.
- Kang (2009): quien arriesga una respuesta y falla recuerda mejor la correcta, una o dos semanas después.

Sostiene: P6 (`promesa.pregunta` que el espectador pueda intentar contestar y cuya respuesta lo contradiga), la escena
`adivina`, R8.

Sin evidencia: que un cliffhanger suba la finalización de una serie. El efecto Zeigarnik tiene réplicas fallidas. El
puente de `/serie` se mide (`metricas.py rendimiento --por parte`), no se endurece.

## 3. Historia y personas (A, con un matiz)

- van Laer y otros (2014), metaanálisis de 76 artículos: personajes identificables, trama imaginable y verosimilitud
  llevan al «transporte» narrativo, que cambia creencias y actitudes.
- Víctima identificable: una persona con nombre, edad y foto mueve más que una estadística. Pero el efecto es de **una**
  persona (con ocho desaparece) y poner la estadística junto a la historia personal lo debilita. En apoyo a políticas
  públicas el resultado es el contrario: pesan más los muchos.

Sostiene: R14 (sujeto reconocible), H12 (foto del protagonista), tarjetas de persona, y «el rostro de la cifra» (la
persona y el número en escenas distintas). Nunca se inventa una persona.

## 4. Plataformas (B y C)

| Hallazgo | Nivel | Fuente | Qué hacemos |
|---|---|---|---|
| Reels: tiempo de visualización, «me gusta» por alcance y envíos por alcance | B (segunda mano; Mosseri, enero 2025) | Buffer y otros | Medir envíos por alcance (AN13) |
| Shorts: bajo 60 % de «vistos frente a deslizados» casi ninguno despega | C (Galloway, 5,400 Shorts, 2023, preliminar) | Hilo del autor | Medirlo (AN14); el primer cuadro como miniatura (R12) |
| YouTube largo: la intro son los primeros 30 s; marca picos y caídas | B | Ayuda de YouTube | Promesa antes del segundo 15 (YT8); capturar intro y caídas |
| 69 % ve sin sonido en público | C (Verizon y Publicis, 2019, encuesta) | 3Play Media | Subtítulos quemados en vertical; `.srt` en el largo |
| Los subtítulos suben más la interacción que el tiempo de visualización | C | TechRadar (patrocinado) | Nada nuevo |
| Video social para noticias: 52 % (2020) → 65 % (2025); YouTube 30 %, TikTok 16 % | A (encuesta, ≈ 95,000 personas) | Digital News Report 2025 | Invertir en el largo de YouTube y en llevar de los cortos al largo |

Huecos: no encontré la documentación oficial de TikTok ni datos por país de Latinoamérica.

Sin sustento: cifras como «el 80 % se decide en los primeros 5 segundos» o «+40 % de tiempo con subtítulos» vienen de
vendedores de herramientas. Lo que sí tenemos es medición propia (`benchmarks.md`): en nuestras historias queda 62 % a
los 3 s y 42 % a los 10 s.

## 5. Movimiento (C)

- Sistemas de diseño (Material, Atlassian): 100–150 ms para cambios chicos, 200–250 ms medianos, hasta 400–500 ms
  grandes; la salida más corta que la entrada. No hay estudios sobre calidad percibida.
- Estilo documental: mapa con ruta, resaltador sobre documentos, collage de fotos, paralaje 2.5D.

Sostiene: una tabla única de duraciones (`V.D`), el mapa con ruta, el subrayado, el tablero. El paralaje se descarta:
es adorno (coherencia) y choca con la cámara quieta.

## Fuentes

- Mayer: https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-research-based-principles-for-designing-multimedia-instruction-mayer.pdf
- Guo, Kim y Rubin 2014: https://www.cs.rochester.edu/hci/pubs/pdfs/edX-MOOC-video-production-and-engagement_LAS-2014.pdf
- Kang y otros 2009: https://www.cmu.edu/dietrich/sds/docs/loewenstein/WickCandleLearning.pdf
- Réplica 2023: https://pmc.ncbi.nlm.nih.gov/articles/PMC10243256
- van Laer y otros 2014: https://openaccess.city.ac.uk/id/eprint/6755/
- Víctima identificable: https://pmc.ncbi.nlm.nih.gov/articles/PMC6051573
- Digital News Report 2025: https://reutersinstitute.politics.ox.ac.uk/digital-news-report/2025/dnr-executive-summary
- YouTube, momentos clave: https://support.google.com/youtube/answer/9314415
- Instagram (segunda mano): https://buffer.com/resources/instagram-algorithms/
- Galloway: https://threadreaderapp.com/thread/1646898356419981315.html
- Sonido apagado: https://www.3playmedia.com/blog/verizon-media-and-publicis-media-find-viewers-want-captions/
- Movimiento: https://atlassian.design/foundations/motion/applying-motion
