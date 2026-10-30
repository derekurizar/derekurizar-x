# Flujo /sabias · «¿Sabías que…?» en video

Un dato ya entregado por `/dato` (`datos/<fecha>-<slug>/`) se convierte en un video vertical de **20–30 s** con la
fórmula clásica «¿Sabías que en Guatemala…?»: siempre animado, con la tarjeta Noche del dato y cerrando con «Sígueme
en». Sale en 9:16 (TikTok, Reels, Shorts) y 4:5 (feed), con `caption.md` por plataforma. Decisiones del usuario
(2026-10-29): basado en un dato, corto, «el clásico sabías que en Guatemala…» y «el sígueme al final, siempre animando
y usando los visuales».

## Piezas

- `.claude/commands/sabias.md` — el coordinador (`/sabias <slug|ultimo|pista> [sin-voz|fixture]`; una pista que no es un
  dato entregado corre `/dato` primero).
- `scripts/sabias.py` — preparar, digesto, gate S1–S3, tiempos y entrega; arma en `TRABAJO/base/` un hilo de una
  tarjeta (hilo.json desde dato.json, datos.json, tuit_1.html) y reusa `scripts/video.py` para todo lo demás (gate
  V1–V5, V9, F1–F8; voz, tiempos, grabar, montar, revisar), enchufando su estructura como `/historia`.
- `video/cierre.html` — sin `resumen`, el cierre es una sola pantalla (frase final y «Sígueme en»).
- «Modo sabías» en `referencias/roles/video-critico.md` (SQ-C1–C5).
- `memoria/sabias.json` (lo escribe `scripts/memoria.py --sabias`; M13 en `validate.py`).
- `sesiones/_fixture_sabias/guion.json` + `make sabias-fixture` (el dato de prueba, voz falsa, 0 créditos).

TRABAJO = `sesiones/<slug>/sabias/`; entrega en `datos/<fecha>-<slug>/video/` (el mp4 fuera de git).

## Formato

| Escena | Tipo | Qué se ve | Qué dice la voz |
|---|---|---|---|
| 1 | `gancho`, `familia: "sabias"` | «¿SABÍAS QUE…?» grande, la línea con el dato y su cifra, y el visual (cifra, llenado, pareja, figuras o lugar) | UNA pregunta: «¿Sabías que en Guatemala…?» con verbo |
| 2 | `tarjeta` (o `tiempo`, `ranking`, `mapa` si la plantilla lo admite), `tuit: 1` | la tarjeta Noche del dato con zoom a la cifra que dice la voz, con su golpe arriba | la cifra con su referente (el antes, el año, «de cada») |
| 3 (opcional) | `golpe`, `escala` o `explica` (de la biblioteca) | la cifra a escala humana o el mecanismo | una oración que suma algo nuevo |
| cierre | una pantalla | la frase final palabra a palabra y «Sígueme en» | la consecuencia del dato para quien lo vive |

Sin promesa, sin narración por actos y sin conclusiones: en 25 s no hay nada que esperar. La música (catálogo fijo por
paleta, la usada hace más tiempo contando /video, /historia y /sabias), el ducking, los efectos, los subtítulos, la
barra de progreso y la zona segura son los de `/video`.

## Gates

- **S1 estructura**: 2–3 escenas más el cierre; la escena 2 es el dato (`tuit: 1`); la 3, un apoyo; `explica` solo con
  una animación ya hecha; sin `promesa`; `cierre.resumen: []` y `cierre.texto` = `cierre.final`.
- **S2 gancho**: `pantalla` = «¿Sabías que…?»; la voz abre con «¿Sabías que» y su primera oración dice «Guatemala»
  (≤ 6.5 s); la línea o el visual traen la cifra; más R4 (lo que muestra el visual se dice), R7 («hoy» solo con datos
  del año) y R10 de `referencias/ganchos.md`.
- **S3 rotación** (contra `memoria/sabias.json`): el visual del gancho y el apoyo no repiten los del «¿Sabías que…?»
  anterior; F7 rota el cierre.
- De `/video`: V1 (1 tarjeta, ≤ 1 escena de texto), V2 (cada número con respaldo en datos.json o `calculo`), V3, V4
  (20–30 s estimados), V5, V9 (golpe, verbo, ritmo ≤ 6 s), F1–F8 del cierre; V6–V8, V10–V13, V16 en tiempos, grabar,
  montar y revisar.

## Costos

≈ 300–450 caracteres de voz (≈ 1 crédito por carácter) y ~3–5 min de render. `sin-voz` usa la voz falsa (0 créditos) y
no entrega.
