# Hilos · @DerekUrizar

Framework en español para producir **piezas con datos de Guatemala**: hilos de X (una tarjeta 1080×1080 por tuit, HTML →
PNG), datos sueltos, informes en PDF, carruseles, **videos verticales narrados** (9:16 + 4:5) y videos largos de YouTube
(16:9). Agentes orquestados investigan, verifican, escriben y producen; **la publicación es manual**.

Cada flujo tiene su comando en `.claude/commands/`, su guía en `referencias/` (léela antes de tocar ese flujo) y su
registro en `memoria/`. Dónde vive cada archivo, script, agente y maqueta: **`referencias/mapa.md`**. Este archivo lo
carga cada agente de cada corrida: aquí van solo las reglas, las decisiones del usuario y una línea por flujo.

## Flujos

| Comando | Qué produce | Guía | Entrega · registro |
|---|---|---|---|
| `/hilo [explica\|perfil] [tema\|idea:<id>]` | Hilo de X con investigación multi-agente y una tarjeta por tuit. Modos: `explica` (sin giro) y `perfil` (un sujeto frente al país; alias `/perfil`) | `flujo-hilo.md` | `hilos/<fecha>-<slug>/` con `redes/` (4:5 y 9:16) · `hilos.json` |
| `/dato [vs\|mapa\|antes] [pista]` | Un dato impactante en UNA tarjeta con texto y alt-text (alias `/vs`, `/mapa`, `/antes`) | `flujo-dato.md` | `datos/<fecha>-<slug>/` · `datos.json` |
| `/ideas [n] [enfoque]` | Temas con datos descargables para el banco de ideas | `roles/explorador.md` | `ideas/banco.json` |
| `/fecha [hoy\|fecha\|id\|texto]` | La pieza que toca según el calendario editorial; despacha a `/dato` o `/hilo` | `.claude/commands/fecha.md` | `ideas/calendario.json` |
| `/investigacion <tema\|idea:<id>\|desde:<slug>>` | Informe PDF Letter de 14–30 páginas (estilo clásico) y el hilo cuyas tarjetas son sus figuras | `flujo-investigacion.md` | `investigacion/<fecha>-<slug>/` · `informes.json` |
| `/video <slug\|ultimo> [corto\|medio\|largo]` | Un hilo entregado → video narrado (~2 min por defecto) | `flujo-video.md` | `hilos/<fecha>-<slug>/video/` · `videos.json` |
| `/historia <tema>` | Un evento o una historia de principio a fin, 2–3 min, en tres actos | `flujo-historia.md` | `historias/<fecha>-<slug>/` · `historias.json` |
| `/serie <tema> [3-5] [explica\|caso]` | Un tema en 3–5 partes de ≈ 90 s (caso: 3–8 de ≈ 130 s) con investigación compartida y plan versionado | `flujo-serie.md` | `series/<fecha>-<slug>/parte-N` · `series.json` |
| `/explica <tema> [corto\|medio\|largo]` | Un concepto, un proceso o una regla en ~2 min: la pregunta, el mecanismo, en tu vida | `flujo-explica.md` | `explicaciones/<fecha>-<slug>/` · `explicaciones.json` |
| `/sabias <slug\|ultimo\|pista>` | «¿Sabías que en Guatemala…?» de 20–30 s desde un dato de `/dato` | `flujo-sabias.md` | `datos/<fecha>-<slug>/video/` · `sabias.json` |
| `/departamento <nombre\|siguiente\|tablero>` | La serie de los 22: `/perfil` con el canon de dimensiones y luego `/video` en modo departamento | `flujo-departamento.md` | `videos.json` (`serie`, `sujeto`) |
| `/congreso [<iniciativa N>\|<tema>]` | Una ley del Congreso en < 1 min: qué buscaba, los votos frente al umbral, diputados de cada lado | `flujo-congreso.md` | `congreso/<fecha>-<slug>/` · `congreso.json` |
| `/video-3d <tema\|desde:<pieza>>` | La maqueta que vuela: de 45 s a 3 min, 100 % en 3D, cuando el lugar o el mecanismo se entienden viéndolos moverse; tantos mundos (tramos), eventos y escenas como la historia necesite | `flujo-video3d.md` | `videos3d/<fecha>-<slug>/` · `videos3d.json` |
| `/youtube-long <serie\|ultima>` | Una serie entregada → UN video 16:9 de 8–20 min: un montaje que reutiliza la voz grabada | `flujo-youtube.md` | `series/<fecha>-<slug>/youtube/` · `youtube.json` |
| `/carrusel <slug\|ultimo\|carpeta> [9:16]` | 5–10 láminas 4:5 y su 9:16 desde un hilo o un dato; sin voz, créditos ni agentes | `flujo-carrusel.md` | `<original>/carrusel/` · `carruseles.json` |
| `/agenda [hoy\|semana\|AAAA-MM-DD] [replan]` | El content manager: qué se publica cada día, dónde, a qué hora, y qué producir | `flujo-agenda.md` | `agenda/<AAAA-Wnn>/` |
| `/analyze-improve [plataformas] [desde:…]` | Mide lo publicado (Chrome, solo lectura), lo alinea con las escenas y propone mejoras | `flujo-analisis.md` | `memoria/metricas.json` |

Las guías están en `referencias/`. Sufijos comunes: `sin-voz` (voz falsa, 0 créditos, sin entrega), `fixture` (la maqueta
del flujo, sin web ni créditos: `make <flujo>-fixture`) y `smoke` (corrida corta con web). Los mp4 quedan fuera de git.
`/noticias` y `/semana` se retiraron el 2026-11-14 (el usuario no publica noticieros); queda el histórico en `noticias/`
y `memoria/noticias.json`.

## Reglas de oro

1. **Ninguna cifra `no_confirmada` aparece en una pieza.** Solo `verificada|ajustada`, y manda `valor_final` (y
   `serie_final`/`partes_final`: el valor original de una ajustada ya no respalda nada). Cada cifra lleva evidencia (url
   + cita + archivo local) y, si es derivada, `calculo`; el verificador busca segunda fuente por niveles y cierra con
   `scripts/verificacion.py` en 0 fallas; tras el guion, un **rechequeo** adversarial revisa lo que sostiene la
   conclusión. No inventar, extrapolar ni redondear lo que la fuente no redondea.
2. **Los agentes no leen JSON de sesión enteros ni código**: usan los digestos (`scripts/digesto.py`, `<flujo>.py
   digesto`), `scripts/fuentes.py` y los límites de su directiva. Presupuestos por rol en `referencias/roles/`; un rol
   con modos lee su núcleo y **solo el archivo de su modo** (`referencias/roles/<rol>/<modo>.md`).
3. **`guion.json` es la fuente de verdad.** Las tarjetas se regeneran con `scripts/materializar.py`; nadie edita
   `tuit_N.html` a mano. Los visualistas escriben solo `tuit_N.ajuste.json`; consolida el productor, único escritor de
   `guion.json` desde entonces. En video, un guion aprobado se cambia con `aplicar` o con un retoque del Workflow, nunca
   a mano.
4. **Cero dependencias externas en lo que se renderiza** (ni `https://` ni emoji). Fuentes tipográficas desde
   `design/fonts/`; colores solo por variables (ningún hex en plantillas, páginas de escena ni animaciones). El pie
   lleva siempre «Fuente: …» y el handle. **Sin Playwright MCP** (descargas con `make tabla`, `make pdf`,
   `fetch_api.py`, cacheadas).
5. **Una paleta por pieza**, elegida por tema. El **estilo** no se elige: tarjetas y videos en **Noche**;
   `/investigacion` en clásico (`referencias/diseno/sistema.md`). T1 siempre con texto (40–280 de peso X, sin enlaces,
   gancho `hook_tipo`); con imagen ≤ 200; el texto nunca repite la tarjeta. Los **modos** no crean tipos: `guion.tipo`
   es `hilo` o `dato` y `guion.modo` (tabla `MODOS` en cada workflow, espejo en `ensamblar.py`) fuerza gancho,
   plantillas y gates; `scripts/check_workflows.py` mantiene las constantes alineadas.
6. **Los gates viven en código** (los workflows, `ensamblar.py --check`, `render.js --check`, `validate.py`,
   `<flujo>.py guion --check`, `plano --check`), sobre los datos y nunca sobre píxeles. Una pieza que no pasa su gate
   de coherencia se entrega `incompleto`, nunca `listo`.
7. **El agente nunca publica.** `memoria/` la escribe solo `scripts/memoria.py` (un registro por flujo; nunca en
   smoke ni fixture), salvo `memoria/metricas.json`, que escribe solo `scripts/metricas.py`. `ideas/banco.json` lo
   escribe solo `scripts/ideas.py`, `ideas/calendario.json` solo `scripts/calendario.py` y `agenda/` solo
   `scripts/agenda.py`.
8. **Al terminar cualquier corrida**: `make validate` sale 0; `make costo` mide la corrida y, en un video, `costo.py
   --registrar` la guarda en `memoria/costos.json` (de ahí salen las medianas que usa `/agenda`).
9. **Los videos nunca generan música ni efectos**: solo `design/musica/catalogo.json` y `design/sfx/catalogo.json`; la
   música se elige por **tema** y la biblioteca crece solo cuando el usuario lo pide. Cada número de la locución tiene
   respaldo (V2). El guion pasa la estructura de retención (V9): un gancho que cumple R1–R14 de
   `referencias/ganchos.md` (se lee en silencio, sujeto reconocible, «Guatemala» en ≤ 6 s, voz ≤ 6 s con verbo, medida también
   sobre la voz real; familia y visual que rotan **sobre todo el feed**, no por flujo); una promesa que abre una pregunta de la historia, **nunca anuncia el video** («al final», «vas
   a ver», «quédate») y se paga en el último tercio, con su bisagra antes del giro (`referencias/promesas.md`, P1–P6);
   ninguna frase de plantilla repetida entre videos (C11); un cierre que dice la consecuencia y no anuncia el final
   (`referencias/cierres.md`, F1–F9). El **crítico de retención aprueba el guion antes de gastar créditos**. Todo lo
   visible queda en la zona segura (V13); la voz nunca se corta, estira ni pausa dentro de un nombre, una sigla o una
   cifra (V16); cada video sale en 9:16 y 4:5 con un caption por plataforma.
10. **Al final de cada video** el reporte termina con «Mejoras al framework» (o «ninguna»): lo que se trabó o se hizo a
    mano, con el archivo y el cambio propuesto. Se registran con `memoria.py --mejoras` y **no se aplican sin que el
    usuario lo pida**. El crítico prueba cada arreglo de texto con `probar` antes de escribirlo.
11. **El usuario elige el gancho y el cierre de cada video** entre 5 opciones distintas, o dicta el suyo. Los workflows
    se detienen tras la selección (`veredicto: "elegir_gancho"`) y devuelven 5 `cierres` antes de la voz; el crítico
    solo recomienda (`args.auto` deja su recomendación).

## Decisiones del usuario

Mandan sobre el criterio de cualquier agente. La fecha dice desde cuándo; la guía trae el detalle y sus gates.

- **Nunca «en suma»** en hilos, datos ni informes; la sección de cierre se titula «Conclusiones» (G2, I3).
- **Sin cara, voz El Faraon 4** (`eleven_multilingual_v2`, cifras en palabras), barra de progreso, «Sígueme en» en el
  cierre, 9:16 + 4:5 (`flujo-video.md`).
- **2026-10-26 · /historia**: el gancho nombra al protagonista y lleva su foto (obligatoria, H10–H12); foto de
  referencia con su crédito, **nunca un icono**; cierre `legado`: lo que la gente hace hoy con lo que la historia dejó.
- **2026-10-27 · narración de corrido primero**: el guionista escribe la narración por actos y luego la reparte en
  escenas sin cambiar una palabra; la voz se graba por secuencias; atribución hablada solo para lo contestado, los
  alegatos y las citas (`flujo-historia.md`; desde entonces también en `/video` y `/explica`).
- **2026-10-28 · estilo Noche** para tarjetas y videos; `/investigacion` queda en clásico (`diseno/sistema.md`).
- **2026-11-02 · la promesa nunca anuncia el video**; sus formas rotan (`promesas.md`).
- **2026-11-03 · el usuario elige gancho y cierre** (regla 11). **Sin noticieros.** Con la primera medición
  (`/analyze-improve`): R14 (sujeto reconocible), voz del gancho ≤ 6 s, escena 2 ≤ 12 s (P5), el cierre no anuncia el
  final y su voz va de 160 caracteres para abajo (F9), `caption.md` en bloques para copiar (`flujo-analisis.md`).
- **2026-11-04 · cada hilo entrega `redes/`** (4:5 y 9:16 por tarjeta, H4). Los hilos explicativos llevan contexto:
  fecha, actor, cita y consecuencia por tuit (`flujo-hilo.md`).
- **2026-11-05 · /serie**: la parte que no es la última cierra con un puente y la voz invita («Sígueme: en la segunda
  parte…»); desde la parte 2, «Empieza por la Parte 1 · fijada en mi perfil» (SE8–SE9, `flujo-serie.md`).
- **2026-11-07 · cámara quieta**: la imagen cambia cuando cambia el tema, nunca por reloj. **Sin tomas de video**: una
  declaración va como cita leída por la voz. Las animaciones no hacen nada antes de la voz (A2) y quedan quietas entre
  pasos (A1). La última parte de una serie lleva su resumen final (SE14).
- **2026-11-08 · /youtube-long es un montaje**, no un guion nuevo: escenas ya verificadas y grabadas, con solo las
  uniones y la promesa grabadas de nuevo; el usuario aprueba el montaje y la miniatura (`flujo-youtube.md`).
- **2026-11-09 · en una serie cada parte trae lo nuevo** (SE15–SE16) y ninguna parte se graba hasta revisar la serie
  completa (SE17). **Color y música por tema**, no por costumbre (H8p, H8m); dos escenas seguidas nunca repiten imagen
  (H7b).
- **2026-11-10 · recompensa y tensión**: «Sígueme» a mitad del video (V25); la pregunta de la promesa sale en pantalla
  **solo en el pago** (P6); cada tercio abre o paga algo (H25); una foto fija ≤ 12 s (H26). «Revisa y mejora» incluye
  mejoras generales.
- **2026-11-12 · «interactivo» = escenas con archivos reales** (mapa vial de OpenStreetMap, fotos que se interrogan,
  páginas de documentos, departamentos), no controles para el espectador (`flujo-historia.md`).
- **2026-11-13 · dinamismo = entra en pantalla lo que la voz nombra**; nunca mover la cámara ni escalar una escena para
  aparentar ritmo. Un piloto antes de rehacer algo grande.
- **2026-11-14 · todo video vertical va en mesa de archivo** (abajo). **/video-3d**: three.js o Blender sobre
  HyperFrames (Remotion quedó fuera); **un estilo por mundo**, lo elige el orquestador entre ocho y pregunta si no
  está seguro; dentro de la maqueta la cámara sí se mueve; el gancho es un evento 3D en el cuadro cero y cada toma nace
  en una frase de la voz; los geodatos se verifican como las cifras; «Maqueta · no a escala» es opcional
  (`flujo-video3d.md`).

## La mesa de archivo

El lenguaje de todos los videos menos `/video-3d` (`referencias/flujo-mesa.md`; motor HyperFrames: `scripts/mesa.py`,
`video_hf.py` en vertical, `youtube_hf.py` en 16:9).

- **Con cada oración entra una pieza que la voz nombra** (foto, recorte de prensa, página de documento, ficha de
  persona o institución, lugar en el mapa, fecha, cifra con su rótulo, red de personas, barra) **y se queda quieta**.
  La cámara no se mueve.
- **Paso «Plano»**: después de la voz real (`tiempos`) y antes de `grabar`, el Workflow `plano` lanza al
  `video-realizador`, que escribe `plano.json` y deja `<flujo>.py plano <TRABAJO> --check --hoja` en 0 (MV1–MV19; en
  16:9, YT13–YT24). Lo que falle en pantalla se arregla en el plano, nunca en el guion ni en la voz.
- **Lo que no tiene pieza propia va como tablero** (`cuenta`, `explica`, `tarjeta`, `ranking`, `mapa`, `escala`,
  `tiempo`, `hemiciclo`, `vias`…), grabado limpio con el motor propio (`scripts/video_grabar.js`).
- **Repliegue por corte** cuando la pieza que entra no cabe; nunca para dar ritmo, nunca animando la escala.
- **Tiempo de lectura** (MV8): un texto queda al frente ≥ 0.5 s + 0.3 s por palabra que la voz no dice.
- **Una maqueta 3D puede vivir dentro de una mesa** (bloque `maqueta` del plano; ≤ 2 por video vertical).
- **Render con un solo proceso** (`--workers 1`: con varios el video tiembla) y un render a la vez. Un trabajo empezado
  con un motor (`video.json → realizacion`) termina con él.
- **De la voz al video en un comando**: `<flujo>.py producir <TRABAJO>` corre la cadena, se detiene con código 3 a
  esperar el plano y reanuda donde quedó (`referencias/fragmentos/producir.md`).

## Mantenimiento

- Tras cualquier cambio: `make validate`, `python3 scripts/check_workflows.py`, `python3 scripts/armar_workflows.py
  --check`, `python3 scripts/check_docs.py` y `make test RAPIDO=1` (sin `RAPIDO`, también los renders). `make doctor`
  comprueba el entorno.
- El código común de los workflows vive en `scripts/workflow_comun.js`; `armar_workflows.py` lo copia en cada uno.
- Los agentes y los workflows se registran al arrancar Claude Code: tras crear o editar `.claude/agents/` o
  `.claude/workflows/`, **reiniciar**. Si un Workflow falla con «agente no registrado», se reinicia; no se relanza con
  `permitir_fallback` (triplica el contexto).
- La voz sale del MCP de ElevenLabs con un solo protocolo: `referencias/fragmentos/voz-mcp.md`.
- `make podar-intermedios` lista los intermedios de lo ya entregado (≈ 30 GB en `sesiones/`); solo borra con
  `CONFIRMAR=1`, y eso lo decide el usuario.
- Este archivo no pasa de ≈ 3,000 palabras (`check_docs.py`, D1): lo nuevo va a la guía de su flujo y a
  `referencias/mapa.md`; aquí, a lo más una línea.

## Convenciones

- Todo en español; nombres de archivo en minúsculas sin tildes. Scripts Python de stdlib pura con `argparse` y
  `--help`; exit 0 ok · 1 fallo · 2 uso incorrecto (· 3 pausa por el plano en `producir`).
- Las cifras en `visual.datos` van crudas y en la unidad de la fuente; el formato lo pone `datos.formato`.
- Slug: minúsculas, sin tildes, guiones, sin fecha; la carpeta de entrega antepone la fecha; las rutas en retornos y
  memoria son relativas a la raíz.
- `sesiones/<slug>/` es la memoria de trabajo (fuera de git salvo las maquetas `_fixture*`); `sesiones/_descargas/`
  es la caché de descargas.
