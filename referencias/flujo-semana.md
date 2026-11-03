# Flujo `/semana` — «Las 5 cifras de la semana en Guatemala»

Índice del modo `semana` de `/noticias`. Comando: `.claude/commands/semana.md`. Script: `scripts/semana.py` (importa
`noticias.py` y `video.py`). Workflow: `noticias` con `modo: semana` (`.claude/workflows/noticias.js`, tabla `MODOS`).

## Formato (decisiones del usuario, 2026-11-03)

- **Se publica el domingo.** La ventana es **lunes → domingo** de esa semana. `/semana` sin fecha = la semana que
  termina el domingo más reciente (hoy si es domingo); una fecha entre semana se lleva a su domingo.
- Video vertical 1080×1920 de **62–90 s** (objetivo 75; **< 61 s reales es falla**: TikTok Creator Rewards paga desde
  60 s) y su 4:5. Cuenta regresiva **5 → 1**: gancho, cinco cifras de cinco noticias, cierre con las cinco en cinco
  líneas y «Sígueme en».
- **Solo cifras de noticias `confirmada` o de fuentes oficiales.** `en_desarrollo` nunca entra.
- **Paleta y música fijas de marca**: `cielo` y `cielo-2` (`PALETA_SEMANA`, `MUSICA_SEMANA` en `semana.py`; cambiables
  ahí o con `preparar --paleta/--musica`). El ciclo diario de `/noticias` pasa por cielo uno de cada 8 días: ese domingo
  el diario y la semana comparten color, no la pista si el diario cae en `cielo-1`.
- Voz El Faraon 4 como `/video` (≈ 1,100–1,300 créditos); efectos y música de los catálogos fijos.

## De dónde salen las cifras

1. **Cosecha** (`semana.py cosechar`): los 7 `sesiones/noticias-<día>/noticias.json` de la semana. Entra cada noticia
   `confirmada` con cifras; N2 se rehace en código con la ventana de 7 días, se exige una fuente guardada con `leer`
   cuya fecha caiga en la ventana (SM2) y se copia su foto. Se descarta lo `en_desarrollo`, `no_confirmada`, sin
   cifras, fuera de ventana o repetido entre días. Los días sin noticiero se listan (ahí rastrean los nuevos).
2. **Lo nuevo** (Workflow): dos rastreadores con el mismo agente, `ofi` (datos oficiales nuevos: Banguat, INE, MSPAS,
   SAT, PNC, `*.gob.gt`) y `sem` (lo que no cubrieron los diarios). Un verificador por candidata nueva; un dato
   oficial puede ir `confirmada` con su sola fuente oficial si cada cifra sale de ella (SM3).
3. `semana.py consolidar` une todo en `noticias.json` y da a cada cifra un id de la semana (`sm-c01`…, con su
   `id_original`).

## Escenas

| Escena | Página | Qué lleva |
|---|---|---|
| gancho (`titular`) | `video/noticia.html` | la foto de la #5, «Semana · 19–25 oct · 5 cifras», «Las 5 cifras de la semana» |
| cifra #5 → #1 (`noticia`) | `video/noticia.html` | chip «Sección · día», numeral `#N` grande, titular, la cifra en el acento, la línea `humana` bajo la cifra, fuente y crédito |
| cierre | `video/cierre.html` | «La semana en Guatemala», 5 líneas (una por cifra, en el orden de la cuenta), la frase final y «Sígueme en» |

No se usa `ranking.html`: las cinco cifras tienen unidades distintas.

## `guion.json` (lo escribe el editor en «Modo semana»)

`{tipo: "semana", fecha, ventana, contexto_superior, gancho {pantalla, texto}, cifras: [{puesto 5→1, noticia,
cifra_id, seccion, titular, texto, cifra {texto, etiqueta}, humana?, calculo?, fuente, foto?, publicada}], cierre
{rotulo, resumen[5], texto, final}, caption {tiktok, instagram, facebook, shorts}}`. Ejemplo:
`sesiones/_fixture_semana/guion.json`.

## Gates (`semana.py guion --check` y `tiempos`)

| Gate | Qué comprueba |
|---|---|
| SM1 | 5 cifras en orden 5, 4, 3, 2, 1, sin repetir; el gancho no dice ni muestra la #1 (su número, su titular ni su foto) |
| SM2 | `publicada` entre el lunes y el domingo, igual a la de la noticia, y una fuente guardada por `leer` fechada en la ventana |
| SM3 | la noticia está `confirmada` (o es un dato oficial); la cita de la cifra trae su valor y la pantalla muestra ese valor |
| SM4 | ≥ 3 secciones, ≤ 2 por sección, una cifra por noticia (también en `consolidar`: ≥ 5 noticias en ≥ 3 secciones) |
| SM5 | 62–90 s estimados (y por escena: gancho 40–115, cifra 110–205, cierre 40–125 caracteres de voz); en `tiempos`, < 61 s reales es FALLA (`video.piso_duracion`) |
| SM6 | ninguna cifra de las últimas 8 semanas (`memoria/semanas.json`: misma url y valor, o titular ≥ 60 %); aviso si el valor salió en `/dato` o `/sabias` en 30 días |
| SM7 | fuente en pantalla de 1–44 caracteres que nombra un medio u organismo de la noticia |
| SM8 | ≥ 3 cifras con `humana` ≤ 40 caracteres, sus números en la cita o en un `calculo` (ids `sm-cNN`) |
| SM9 | N6 (titular, sección, cifra) y N7 (foto con crédito) de `/noticias` |
| SM10 | cierre de 5 líneas ≤ 26 con su cifra; `final` ≤ 12 palabras y última frase de la voz; sin cebo ni «sígueme» en la voz |
| SM11 | «Guatemala» y «semana» en la voz del gancho (≤ 6 s; en `tiempos`, con los tiempos reales), en su pantalla y en la 1.ª línea de los captions de TikTok y Shorts (`video.revisar_palabra_clave`, V19) |

Más N4 (cada número con cita), V3 (cifras en palabras), V5 (captions) y, de `video.py`, V6, V8, V10–V13 y V16.
Crítico: «Modo semana» de `referencias/roles/video-critico.md` (SM-C1–SM-C6).

## Entrega y memoria

- `semana.py entregar` → `semanas/<domingo>/`: `video.mp4` (TikTok, Reels, Shorts), `video_4x5.mp4`, `caption.md`,
  `subtitulos.srt`, portadas, `fuentes.md` (cada cifra con su cita y sus urls) y `guion.json` de entrega con las 5
  cifras completas (valor, unidad, cita, url, respaldo). El mp4 queda fuera de git. Sin voz real, solo con `--salida`.
- `memoria.py --semana semanas/<domingo>` → `memoria/semanas.json` (id = semana ISO `AAAA-Wnn`); nunca en fixture.
  `validate.py` M15. `/noticias` guarda ahora las `cifras` de cada noticia en su entrega y en `memoria/noticias.json`.
- **Carrusel**: `semana.py carrusel semanas/<domingo>` arma el TRABAJO de `/carrusel` (origen `semana`: las 5 cifras
  como láminas `texto`) con su `carrusel.json` ya pasado por `carrusel.py guion --check`; luego `carrusel.py render`
  (4:5 y 9:16) y `entregar` (→ `semanas/<domingo>/carrusel/`).

## Prueba

`make semana-fixture`: 3 diarios de ejemplo (`sesiones/_fixture_semana/diarios/`: con una noticia `en_desarrollo`, una
fuera de ventana y una `no_confirmada`, que la cosecha descarta), un dato oficial (`oficial/verificacion_ofi-1.json`),
el guion fijo y una semana previa (`semanas.json`) para SM6; voz falsa, 9:16 y 4:5 de ≥ 61 s, entrega en
`sesiones/_fixture_semana/salida`.
