# /agenda: el content manager

`/agenda [hoy|semana|AAAA-MM-DD] [replan]` planifica de hoy al domingo qué se publica cada día, en qué plataforma y a
qué hora, y qué hay que producir para llenar cada espacio. Comando: `.claude/commands/agenda.md`; script:
`scripts/agenda.py` (el único que escribe `agenda/<AAAA-Wnn>/agenda.json` y `agenda.md`).

## Espacios por día

Sin noticieros: el usuario no los publica (2026-11-03) y `/noticias` y `/semana` se retiraron del framework el
2026-11-14.

- **A · pieza fuerte**, 09:00: historia, explica, parte de serie, `/video` o `/video-3d`.
- **B · pieza corta**, 19:30: «¿Sabías que…?» o departamento.
- **C · carrusel** (opcional), 13:00.

Como máximo 2 videos al día; cada video va a las cuatro plataformas en 9:16, con su 4:5 al feed.

En Facebook, cada video lleva un estilo de descripción que rota (historia, pregunta, dato, lista). La sesión la escribe
con `agenda.py facebook`, y `metricas.py rendimiento --por estilo_fb` mide cuál rinde.

## Cómo se llenan los espacios

En este orden:

1. Lo listo sin publicar, cruzando `memoria/` con `memoria/metricas.json`: lo corto al B, lo demás al A.
2. Las partes de `/serie` que ya se pueden publicar (A): la parte N se publica cuando la N+1 tiene el guion aprobado.
3. ≤ 2 fechas del calendario (`ideas/calendario.json`): un dato a «¿Sabías que…?» en el B, un hilo a `/video` en el A,
   nunca antes de su fecha.
4. El siguiente `/departamento` (B).
5. La mezcla: el A con ≥ 3 historias y 1 explica; el B es «¿Sabías que…?».

Lo que no tiene pieza es una **orden de producción** con su comando, su día, sus minutos y sus créditos. Los temas los
propone la sesión y **los elige el usuario**.

## Comandos de `scripts/agenda.py`

- `plan [--desde] [--memoria] [--dir]`: inventario de los registros cruzado con `memoria/metricas.json` (`listas`,
  `incompletas`, `calendario_en`, `series_publicables`, `departamento_siguiente`, `mezcla` por
  `metricas.rendimiento --por flujo`). Conserva lo de antes de `desde` y lo que tiene tema, está producido o publicado.
- `tema SLOT "<tema>"` (AG4) → `producido SLOT --ruta` → `publicado SLOT [--plataforma]`.
- `hoy`: los archivos 9:16 y 4:5 del día y los bloques de `caption.md`.
- `facebook`: la descripción de Facebook con el estilo que toca.
- `--check`: gates **AG1–AG9** (M18 en `validate.py`, solo semanas sin terminar).

Maqueta: `sesiones/_fixture_agenda/memoria` (registros congelados; `make agenda-fixture` = la semana del 4 al 8 de
noviembre).
