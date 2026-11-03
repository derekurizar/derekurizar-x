# /carrusel · índice

Un hilo (`hilos/<fecha>-<slug>/`) o un dato (`datos/<fecha>-<slug>/`) ya entregados → un **carrusel** de 5–10
láminas: 4:5 (1080×1350) para Instagram y Facebook, y 9:16 (1080×1920) para el modo foto de TikTok. Sin voz, sin
créditos, sin agentes: el texto (`carrusel.json`) lo escribe la sesión con el digesto, como en `/sabias`. Los
carruseles se guardan más que los videos; este flujo da una pieza más por cada hilo o dato sin gastar.

- Comando: `.claude/commands/carrusel.md` · script: `scripts/carrusel.py` (`preparar`, `digesto`, `guion --check`,
  `render`, `entregar`) · página: `scripts/carrusel.js` (Playwright) · plantillas: `templates/carrusel/lamina.html` y
  `carrusel.css` (sobre `video/comun.css`; la tarjeta en modo vertical con `video/vertical.css`).
- Maqueta: `sesiones/_fixture_carrusel/` (`carrusel.json` sobre el hilo de prueba, `carrusel_dato.json` sobre el dato
  de prueba); `make carrusel-fixture`.
- Registro: `memoria/carruseles.json` (`memoria.py --carrusel`; M14 en `validate.py`). Nunca en fixture.

## Flujo
1. `preparar <slug|ultimo|carpeta>`: exige `listo|publicado`; copia el original a `TRABAJO/base/` (un dato se arma
   como hilo de una tarjeta con `sabias.hilo_base`), **re-materializa** cada tarjeta en Noche
   (`video.rebasar_tarjetas` → `TRABAJO/tarjetas/`; nunca se recortan los PNG) y escribe `digesto.md`: tuits con beat,
   plantilla, titular, texto, alt, fuente y cifras; las cifras que no usa ninguna tarjeta; tesis; no_afirma; la forma
   de la última portada. Un original sin cabecera de plantilla (anterior a `nuevo_visual.py`) se bloquea.
2. La sesión escribe `TRABAJO/carrusel.json` y pasa `guion --check` (CA1–CA8).
3. `render` (4:5) y `render --formato 9:16` → `TRABAJO/salida/lamina_NN.png` (+ `9x16/`) y `contacto.png`
   (`contacto.js --prefijo lamina_`, celdas con la proporción real). Un Read del contacto.
4. `entregar` → `<original>/carrusel/` (PNG, `9x16/`, `carrusel.json`, `caption.md` por plataforma con la nota
   «elige el sonido en la app», `alt.md`, `contacto.png`). Un carrusel por original: rehacerlo lo reemplaza. Un
   TRABAJO de prueba solo con `--salida`.
5. `memoria.py --carrusel <original>/carrusel` y `make validate`.

## Anatomía
| Tipo | Lleva | Límite (CA2) |
|---|---|---|
| `portada` | contexto (Mono), cifra grande en el acento, `contra` (forma contraste), título, «Desliza →» | título ≤ 8 palabras, cifra 1 token |
| `tarjeta` | golpe arriba + la tarjeta N (sin titular ni handle; la fuente va al pie de la lámina) | golpe ≤ 10 |
| `texto` | golpe + cuerpo | golpe ≤ 10, cuerpo ≤ 30 |
| `porque` | «Por qué importa» + cuerpo (qué cambia para la gente) | ≤ 40 |
| `cierre` | frase (la consecuencia), «Guárdalo.», «Sígueme en» con los handles (los pone la plantilla) | ≤ 12 |

Todas llevan el pie: «Fuente: …» (menos el cierre), el handle `@derekurizargt` y el contador n/N. Una sola cosa en el
acento por lámina: la cifra de la portada, la última cifra del golpe, «Por qué importa» o «Guárdalo». Formas de
portada (`portada_forma`, rotan: CA8): `cifra` · `pregunta` (título con «?») · `contraste` (`contra`) · `lista` (el
título empieza con el número de puntos).

```json
{"version": 1, "origen": {"tipo": "hilo", "ruta": "hilos/<fecha>-<slug>"}, "slug": "…", "paleta": "maiz",
 "palabra_clave": "canasta básica", "portada_forma": "cifra",
 "laminas": [{"tipo": "portada", "contexto": "…", "cifra": "0.95", "titulo": "…", "fuente": "…", "cifra_ids": ["…"]},
             {"tipo": "tarjeta", "tuit": 1, "golpe": "…"}, {"tipo": "texto", "golpe": "…", "cuerpo": "…", "fuente": "…",
              "calculo": "sal-c11 * 100"}, {"tipo": "porque", "cuerpo": "…", "fuente": "…"}, {"tipo": "cierre", "frase": "…"}],
 "caption": {"tiktok": "…", "instagram": "…", "facebook": "…"}, "alt": {"1": "…"}}
```

## Gates
En `carrusel.py guion --check` (y antes de `render` y `entregar`):
- **CA1** estructura: 5–10 láminas; 1.ª portada, última cierre, penúltima porque; ≥ 2 tarjeta|texto; cada tarjeta, un
  tuit con imagen que no se repite; `portada_forma` válida y coherente; `origen` = el original preparado.
- **CA2** palabras por campo (tabla de arriba; contexto ≤ 10, contra ≤ 6).
- **CA3** palabra clave (1–3 palabras): en la portada, en ≥ 1 lámina más y en la 1.ª línea de los captions de tiktok,
  instagram y facebook (`video.revisar_palabra_clave` sin voz).
- **CA4** cada número de una lámina (y de su alt propio) con respaldo en `datos.json` (`video.sin_respaldo` +
  `valores_respaldo`), o en el `calculo` de su lámina (`resolver_calculo`); `cifra_ids` verificadas o ajustadas.
- **CA5** fuente en cada lámina menos el cierre (la de una tarjeta es la de su tuit).
- **CA6** nada de «en suma», enlaces, emoji, «#», «Sígueme» fuera del cierre ni lo que el original no afirma.
- **CA7** captions sin enlaces, ≤ 5 hashtags, 1.ª línea de Instagram ≤ 125 caracteres; alt de 20–1000 por lámina (una
  tarjeta sin alt usa el de su tuit).
- **CA8** (aviso) la forma de la portada repite la del carrusel anterior.

En `carrusel.js --check` (por lámina):
- **CA9** lienzo: `body[data-listo]` sin error; todo texto fuera de la tarjeta ≥ 28 px y dentro del lienzo; ninguna
  petición externa; JetBrains Mono, Archivo y Archivo condensada cargadas.
- **CA10** miniatura: cifra de la portada ≥ 220 px y título ≥ 96 px dentro del recorte 3:4 central (4:5: x 34–1046;
  9:16: y 240–1680); en 9:16, todo (textos y la tarjeta) en la zona segura del modo foto (x 57–1023, y 215–1645,
  fuera de los íconos: x ≤ 900 desde y 1070).
- **CA11** ≤ 1 texto en el acento fuera de la tarjeta; `templates/carrusel/*` sin hex ni https.
- **CA12** pie con «Fuente: …» en ≤ 2 líneas (menos el cierre), handle y contador n/N.

## Plataformas
- **Instagram y Facebook**: las láminas 4:5 en orden; el caption de cada una en `caption.md`. La 1.ª línea es lo que
  se ve sin «más»: la palabra clave va ahí.
- **TikTok (modo foto)**: las de `9x16/`; el sonido se elige en la app (el carrusel no trae audio).
- El alt de cada lámina va en `alt.md` (Instagram: «Configuración avanzada → Escribir texto alternativo»).

## Origen semana

Una semana de `/semana` (`semanas/<domingo>/` o su TRABAJO) también sirve de original: `python3 scripts/semana.py
carrusel <carpeta>` llama a `carrusel.py preparar` (origen `semana`: `semana.base_carrusel` arma `base/` con las 5 cifras
como un hilo sin imágenes y sus `datos.json`) y escribe un `carrusel.json` de 8 láminas `texto` que pasa CA1–CA8; luego
`render` y `entregar` (→ `semanas/<domingo>/carrusel/`) como siempre.
