# /analyze-improve: métricas reales → framework

El framework se juzgaba con sus propias reglas (R1–R14, V9, el crítico). `/analyze-improve` cierra el ciclo:
mide cómo les fue a las piezas publicadas, encuentra en qué segundo y en qué escena se va la gente, busca cómo se
resuelve y propone el cambio al framework con su evidencia. El usuario aprueba cada cambio (regla 10 de CLAUDE.md).

## Piezas

| Archivo | Qué hace |
|---|---|
| `.claude/commands/analyze-improve.md` | El coordinador: captura → registro y vínculo → diagnóstico → web → propuesta → reporte |
| `referencias/analisis/captura.md` | Los fragmentos de JavaScript que leen TikTok Studio, YouTube Studio, Facebook e Instagram (solo lectura) y cómo sale el JSON por el portapapeles |
| `scripts/metricas.py` | `importar`, `vincular`, `alinear`, `diagnostico` (AN1–AN12), `rendimiento`, `--check` (M17) |
| `memoria/metricas.json` | Publicaciones con su pieza, sus snapshots fechados y la última curva de retención por segundo |
| `referencias/analisis/benchmarks.md` | Lo que dice la web por problema, con fuerza, fuente y fecha, y lo que mide el propio canal |
| `referencias/analisis/publicacion.md` | La lista de publicación manual (caption de `caption.md`, la pregunta de audiencia de YouTube, restricciones, hora) |
| `sesiones/_analisis/<fecha>/` | Las capturas crudas y el borrador de mejoras de cada corrida |
| `sesiones/_fixture_analisis/` | Capturas de prueba (3 piezas) para `make analisis-fixture` |

## Qué mide cada plataforma

| Plataforma | Por publicación | Curva |
|---|---|---|
| TikTok | vistas, me gusta, comentarios, compartidos, guardados, seguidores, tiempo medio, completado, % «Para ti» | sí, por segundo |
| YouTube | vistas, comentarios, «se quedaron viendo» (visto frente a deslizado), tiempo medio | no (en la web resumida) |
| Facebook | vistas, seguidores netos, distribución (×), tiempo medio, vistas de 3 s y de 1 min | no |
| Instagram | vistas, me gusta, comentarios, guardados, compartidos, seguidores; caption, fecha y duración por la API web | no |

## Alineación

El inicio de cada escena es Σ(dur − transición) de las escenas anteriores. Se toma de `escenas.json` de la sesión
(tiempos medidos tras la voz) o, si no está, del `guion.json` entregado. Por escena: la retención al entrar y al salir,
los puntos perdidos y la **tasa relativa** (qué % de quienes seguían viendo se va por segundo). La curva siempre cae más
al principio, así que en puntos absolutos toda escena temprana parecería mala.

## Detectores

| Código | Qué ve | Archivo que implica |
|---|---|---|
| AN1 | Retención a 3 s < min(60 %, la mediana del canal) | `referencias/ganchos.md` (R14) |
| AN2 | > 25 % se va en el primer segundo | `referencias/ganchos.md` (R12, cuadro 0) |
| AN3 | La escena de la promesa (`promesa.en`, si no la 2) pierde > 1.5× la mediana y ≥ 5 puntos | `referencias/promesas.md` |
| AN4 | Una escena pierde > 2× la mediana (cierre aparte) | la plantilla o la animación de la escena; `referencias/cierres.md` para el cierre |
| AN5 | Completado < 10 % en una pieza de > 90 s | `referencias/flujo-video.md` (duración) |
| AN6 | Una publicación con < 5 % de la mediana de su plataforma | `referencias/analisis/publicacion.md` |
| AN7 | Título publicado distinto de `caption.md` o con erratas (palabra cercana a una del guion, o que cambia entre plataformas) | `<entrega>/caption.md` |
| AN8 | Familia de gancho con mediana < 0.8× la del canal (n ≥ 2) | `referencias/ganchos.md` |
| AN9 | Cuántos llegan al cierre y seguidores por 1,000 vistas (informativo) | `referencias/cierres.md` |
| AN10 | Tiempo medio / duración ≥ 2.5× distinto entre plataformas | `referencias/flujo-video.md` |
| AN11 | Retención y vistas por flujo (historia, video, noticias, sabias…) (informativo) | `referencias/roles/explorador.md` |
| AN12 | Vistas por franja horaria, solo con ≥ 10 piezas por franja | `referencias/analisis/publicacion.md` |

## Cómo vuelve al framework

- `video.py`, `historia.py` y `explica.py` ponen **«Rendimiento real»** en el digesto del gancho y del guion
  (`metricas.lineas_rendimiento()`): la retención a 3 s, el tiempo medio y las vistas por familia, visual y cierre. Una
  categoría ▼ (< 0.8× la mediana, n ≥ 2) se puede elegir, pero su `por_que` dice qué la hace distinta esta vez.
- La regla **R14** (sujeto reconocible) nació de la primera medición (2026-11-03). Ver `referencias/ganchos.md` §1 y §4.
- Lo demás entra como mejora en `memoria/mejoras.json` (`flujo: analisis`) y se aplica cuando el usuario lo pide.
