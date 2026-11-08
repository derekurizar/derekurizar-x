# Referencias externas de retención (/analyze-improve)

Lo que dice la web sobre cada problema que detectan AN1–AN12. **Ninguna plataforma publica umbrales oficiales**: casi
todo es de blogs y agencias (fuerza C de `referencias/ganchos.md` §1) y se usa como referencia junto a la **línea base
del propio canal** (`metricas.py diagnostico`), nunca como regla. Cada fila lleva la fecha en que se buscó. El comando
no vuelve a buscar una fila de menos de 30 días: la actualiza o añade filas nuevas con su fuente.

| Tema (AN) | Lo que dicen | Fuerza | Fuente · fecha |
|---|---|---|---|
| Gancho, TikTok (AN1) | Retener 70–85 % a los 3 s se cita como «bueno»; < 60 % recibe poco empuje. Otras agencias miden «thumbstop» (vistas de 3 s / impresiones) > 25 % | C | [socialync](https://www.socialync.io/blog/tiktok-viral-retention-rate-2026), [opus.pro](https://www.opus.pro/blog/tiktok-length-format-retention-data) · 2026-11-03 |
| Gancho, Shorts (AN1) | «Visto frente a deslizado» ≥ 70 % es la zona buena que se cita; < 60 % rinde mal; YouTube no publica un umbral | C | [subscribr](https://subscribr.ai/youtube-strategy/youtube-shorts-analytics-metrics-viral), [creatoressentials](https://www.creatoressentials.com/glossary/viewed-vs-swiped-away/) · 2026-11-03 |
| Completado (AN5, AN10) | 50 % es fuerte en 30 s; 25–30 % es excelente en videos de más de 1 min; el tiempo total de visionado pesa junto al completado | C | [opus.pro](https://www.opus.pro/blog/tiktok-length-format-retention-data) · 2026-11-03 |
| Medir (todas) | Comparar contra las propias piezas de los últimos 30–60 días y probar variantes de gancho entre sí vale más que un umbral genérico; reescalar las curvas para comparar | C | [Social Media Examiner](https://www.socialmediaexaminer.com/how-to-analyze-your-youtube-shorts/), [formatfinder](https://formatfinder.onepeakcreative.com/resources/how-to/analyze-your-tiktok-retention-curve) · 2026-11-03 |
| Caída de 5–15 s (AN3) | La mayoría pierde entre los 5 y los 15 s por falta de impulso tras el gancho. Lo que se repite como arreglo es un «re-gancho» en cada beat (corte + resaltado de texto + pausa breve, o un cambio de ángulo o de energía de la voz) y un solo tema por video. La cadencia citada va de 3–5 s a 15–30 s: probar contra la propia curva | C | [membership.io](https://membership.io/blog/social-media-hooks-why-yours-stopped-working-and-how-to-fix-it), [skills.sh retention-editing](https://skills.sh/thecraighewitt/skills/retention-editing), [opus.pro](https://www.opus.pro/blog/youtube-retention-graphs-explained) · 2026-11-03 |
| Caída en el cierre (AN4 cierre) | La gente se va en cuanto reconoce el final («outro»). Lo que se cita: cortar pausas de > 1 s al final, cerrar con un bucle (repetir la línea del inicio, cortar a media frase o terminar en un cuadro que case con el primero) y dejar abierto un bucle hasta el último segundo. Que la repetición pese 2–3× es una afirmación sin fuente oficial | C | [socialk.it](https://socialk.it/en/blog/tiktok-retention-watch-time-guide), [crayo.ai](https://crayo.ai/blog/how-to-make-looping-content-for-tiktok), [joyspace open loop](https://joyspace.ai/open-loop-technique-force-viewers-watch-end) · 2026-11-03 |
| Duración por plataforma (AN5, AN10) | No hay ningún estudio independiente de 60–90 s narrativos. Las guías ponen el punto dulce de TikTok en 24–60 s, el de Reels en 25–40 s (Reels admite 90 s; 3 min en beta) y el de Shorts en 30–58 s (Shorts admite hasta 3 min). En Facebook se ve mucho sin sonido. La regla útil: la duración es el tiempo que pide cumplir una promesa | C | [shortimize](https://www.shortimize.com/blog/video-length-sweet-spots-tiktok-reels-shorts), [reap.video](https://reap.video/blog/best-video-length-youtube-shorts-reels-tiktok), [quso.ai](https://quso.ai/blog/social-media-video-length-best-practices) · 2026-11-03 |
| Caption y búsqueda (AN7) | El 49 % de los usuarios ya usa TikTok como buscador (Adobe). Las guías dicen que pesan las palabras clave en los primeros ≈ 100 caracteres del caption, más que los hashtags, y que también cuentan la voz y el texto en pantalla. Desde abril de 2026, TikTok muestra al creador las palabras de búsqueda asignadas a cada video. Medir con la fuente de tráfico «Buscar» | B (Adobe) / C | [riseatseven](https://riseatseven.com/blog/tiktok-seo-statistics/), [Darkroom](https://www.darkroomagency.com/observatory/tiktok-seo), [ttcalculator](https://ttcalculator.net/guides/growth/tiktok-seo-search-ranking/) · 2026-11-03 |
| API (captura) | La API pública de TikTok no da tiempo medio ni curva por video; solo TikTok Studio (de ahí la captura con Chrome) | C | [ttcalculator](https://ttcalculator.net/guides/growth/tiktok-analytics-api-creators/) · 2026-11-03 |

## Lo que mide el propio canal (2026-11-03, 21 piezas)

- TikTok, retención a los 3 s: historias con marca o personaje 62–69 %; historias con gancho de cifra o «¿Sabías
  que…?» 42–56 %; `/video` de hilos de datos 28–40 %. Al primer segundo se va el 11–17 % en las ganadoras y el
  39–45 % en las de datos.
- Entre los 3 y los 10 s se pierden ≈ 25 puntos en todas (la escena de la promesa).
- Historias de 2:45–2:52: completado de 2.5–10 % en TikTok (tiempo medio 14–49 s), pero 47–70 % «visto» y 1:47–1:57 de
  tiempo medio en YouTube: el mismo corte rinde distinto según la plataforma.
- Facebook: los noticieros son lo que más se ve (1.2–1.5K vistas, distribución +1.9 a +2.3×); lo demás ronda 200.
