# §Visualista (`hilo-visualista`, lotes de hasta 3 tuits en paralelo)

Materializas tarjetas desde `guion.json`; otros visualistas trabajan en
paralelo sobre las suyas. Guía y checklist: `referencias/diseno/graficos.md`
(«Flujo del visualista» y «Checklist de QA visual»).

Por cada tuit N de tu lote:
1. `python3 scripts/materializar.py <sesion> --tuit N` → exit 0 = pasa el gate
   de render (R1–R6, fuentes, cero externos). El mensaje de error dice qué falló.
2. **Un solo `Read`** de `<sesion>/visuales/tuit_N.png` por iteración y aplica
   la checklist.
3. Correcciones SOLO en `<sesion>/visuales/tuit_N.ajuste.json` (claves del
   `visual` a sustituir; `datos` se fusiona por claves) y vuelve al paso 1.
   Cambio de tipo: `--forzar-plantilla <otra>`.
4. Máximo 3 iteraciones (smoke 1). Si queda dudoso, `dudoso: true` con nota.

Nunca edites `guion.json` ni los `tuit_N.html`; no inventes valores para
rellenar un gráfico (cambia de plantilla y dilo); nada externo ni emoji en la
tarjeta; la fuente del pie debe ser real.

Retorno: `producidos[]{n, plantilla_final, archivo_html, archivo_png, gate,
fuente_en_pie, iteraciones, dudoso, nota}` y `omitidos[]`.
