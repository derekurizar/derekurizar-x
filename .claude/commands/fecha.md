---
description: Pieza atada a una fecha — efeméride, día internacional o publicación de una fuente — desde el calendario editorial ideas/calendario.json; despacha a /dato (con su modo) o a /hilo (uso — /fecha [hoy|<YYYY-MM-DD>|<MM-DD>|<id>|<texto>] [smoke|fixture]; sin argumento lista los próximos 30 días; «/fecha buscar [mes o tema]» lanza un explorador que propone entradas nuevas)
---

Eres el coordinador del flujo **/fecha** de @DerekUrizar. El calendario
editorial vive en `ideas/calendario.json` y lo escribe SOLO
`scripts/calendario.py` (nunca lo edites a mano). Argumentos: "$ARGUMENTS".
Obtén la fecha de hoy con `date +%F`.

1. **Sin argumento** (o `proximas`): corre `python3 scripts/calendario.py
   --proximas 30` y muestra la lista tal cual (fecha, id, título, formato/modo,
   «hace N años»). Termina sugiriendo `/fecha <id>` para producir una; no
   lances nada.

2. **`buscar [mes o tema]`**: propone entradas nuevas. `date +%F-%H%M%S` →
   `dir = sesiones/_ideas/<fecha-hora>`; `mkdir -p <dir>`. Lanza UN agente
   `ideas-explorador` (herramienta Agent, `subagent_type: "ideas-explorador"`)
   con esta directiva: «Lee `referencias/roles/explorador.md`, sección "Modo
   calendario". Fecha: <hoy>. Ámbito: <mes o tema; sin argumento, los próximos
   60 días>. Propón 5–10 entradas (efemérides de Guatemala, días
   internacionales con dato oficial del país, publicaciones periódicas de
   fuentes) con fecha, pista, formato (dato|hilo), modo
   (dato|vs|mapa|antes|hilo|explica|perfil|null) y fuentes; ≤ 6 búsquedas, ≤ 6
   fetch. Escribe `<dir>/calendario_<ambito>.json` como `{"entradas": [...]}`
   y devuelve el mismo contenido». Después: `python3 scripts/calendario.py
   --importar <dir>` (valida y deduplica), `make validate` (exit 0) y muestra
   las entradas añadidas (líneas `+`) y las descartadas.

3. **Con argumento** (todo lo demás): resuelve la entrada.
   - `hoy` → `python3 scripts/calendario.py --dia <hoy>`.
   - `YYYY-MM-DD` o `MM-DD` → `--dia <fecha>`.
   - Un id (`[a-z0-9-]+` que exista) → `--ver <id>`.
   - Texto libre → `--buscar "<texto>"`; si hay una coincidencia `FUERTE`, úsala.
   Si hay varias candidatas, pregunta al usuario cuál (AskUserQuestion). Si no
   hay ninguna, la pieza sale igual con el texto literal como efeméride
   (`formato = dato`, `modo = null`) y no se marca nada en el calendario.
   Si la nota de la entrada dice «fecha estimada», díselo al usuario antes de
   seguir (la cifra de la fuente manda; la fecha solo decide cuándo publicar).

4. **Despacho.** Construye la pista: «FECHA: <titulo> (<fecha de la
   ocurrencia>; hace N años si `anio_origen`). <pista de la entrada>». Si el
   argumento traía `smoke` o `fixture`, consérvalo.
   - `formato: "dato"` → sigue `.claude/commands/dato.md` con `"modo"` =
     `modo` de la entrada (o `"dato"` si es null) y esa pista.
   - `formato: "hilo"` → sigue `.claude/commands/hilo.md` con `tema` = la
     pista; si `modo` es `explica` o `perfil`, pásalo como `"modo"` en `args`
     (cuando `hilo.js` lo admita; hasta entonces, tema libre).

5. **Cierre.** Si no fue smoke ni fixture y el estado quedó `listo` o
   `incompleto`: `python3 scripts/calendario.py --marcar <id> --estado hecha
   --pieza <ruta relativa>`; luego `make validate` (exit 0). Muestra la entrada
   usada (id, fecha, «hace N años») y todo lo que `dato.md` o `hilo.md` piden
   mostrar.

Reglas: `/fecha` no inventa fechas (las estimadas se confirman con la fuente);
la pieza pasa por investigador y verificador como cualquier `/dato` o `/hilo`;
el calendario no es memoria de cifras, solo de ocasiones.
