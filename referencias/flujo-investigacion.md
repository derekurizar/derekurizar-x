# Flujo `/investigacion` — índice

Una investigación es **un informe de datos en PDF (Letter, 14–30 páginas) y el
hilo de X que lo acompaña**, sobre UN tema de Guatemala. Las tarjetas del hilo
son figuras del informe; el informe cuenta con detalle lo que el hilo resume.
El entregable queda en `investigacion/YYYY-MM-DD-<slug>/`:

```
investigacion/2026-10-13-<slug>/
  informe.json                        ← lo escribe el redactor (fuente de verdad del PDF)
  salida/informe.pdf · informe.html · figuras/ · fonts/
  hilo/hilo.html · post.md · tuit_1..N.png · datos.json · hilo.json · contacto.png
```

```
Encuadre (editor: ejes + plan de capítulos) → [Investigación → Verificación] por eje, en pipeline
→ Guion (guionista: 6–12 tuits, bloque investigacion, cierre con [ENLACE AL INFORME])
→ Visuales (visualistas en lotes de 3)
→ Producción (productor: ensamblar.py --check --salida investigacion/…/hilo + coherencia C1–C8, sin memoria)
→ Informe (redactor: informe.json → informe.py --check --png, I1–I7 + P1–P5, ≤ 3 vueltas)
→ Cierre (productor: informe.py al entregable, QA de ≤ 3 páginas, memoria.py --informe, make validate)

desde:<slug>   Relectura (editor: añade el plan de capítulos a la sesión) → Informe → Cierre
```

Orquesta `.claude/workflows/investigacion.js` (invocado por
`/investigacion <tema|idea:<id>|desde:<slug>> [smoke|fixture]`). `investigacion`
es un **modo** de tipo `hilo` (`guion.tipo = "hilo"`, `guion.modo =
"investigacion"`): el hilo pasa por `ensamblar.py --check` como cualquier
otro, con tres gates propios (6–12 tuits, bloque `guion.investigacion{numero,
informe_dir, capitulos[]}`, marcador `[ENLACE AL INFORME]` solo en el cierre).
El informe pasa por `scripts/informe.py --check` (I1–I7) y
`scripts/render_informe.js --check` (P1–P5). Ninguna cifra `no_confirmada`
llega al hilo ni al informe: los dos comparten `datos.json`.

| | normal | smoke | fixture |
|---|---|---|---|
| ejes | 2–5 | 1 | 1 (los del fixture) |
| tuits | 6–12 | 4–6 | 3 |
| páginas (gate · objetivo) | 14–30 · 16–28 | 8–12 | 6–10 · 8 |
| figuras / tablas / capítulos mínimos | 6 / 1 / 2 | 3 / 0 / 1 | 2 / 0 / 1 |
| lecturas de PNG (redactor / productor) | 6 / 3 | 3 / 2 | 2 / 1 |
| investigador: búsquedas / fetch / cifras / series | 14 / 16 / 16 / 6 | 7 / 8 / 8 / 3 | — |
| entregable | `investigacion/<fecha>-<slug>/` | `sesiones/<slug>/{salida,informe}/` | ídem |
| memoria | `hilos.json` (modo investigacion) + `informes.json` | no | no |

`desde:<slug>`: el hilo ya se entregó (`hilos/<fecha>-<slug>/`); el informe lo
referencia por ruta y no lo duplica; `informes.json` lo registra con `modo:
"desde"`. El número del informe lo da el comando con `python3 scripts/memoria.py
--informes` («siguiente N.º NN») y viaja en `args.numero` → `encuadre.informe`
→ `guion.investigacion` → `informe.json.meta.numero`.

Guía por rol: «Modo investigación» en editor (y «Modo desde»), investigador,
verificador, guionista, visualista y productor; el redactor tiene guía propia.

- Contrato de archivos y reglas de datos: `referencias/contrato-sesion.md` («Sesión investigación»)
- Guía por rol: `referencias/roles/{editor,investigador,verificador,guionista,visualista,productor,redactor}.md`
- Narrativa del hilo de investigación: `referencias/narrativa.md`, «Hilo de investigación»
- Contrato de `informe.json`, tipos de página y gráficos del documento: `referencias/diseno/informe.md`
- Catálogo de gráficos (mismo contrato en tarjeta y documento): `referencias/diseno/graficos.md`
- Prueba sin agentes: `make informe-fixture` (tras el fixture de hilo) y `make informe-catalogo`
