# Flujo `/dato` — índice

Un dato es **UNA cifra impactante** de Guatemala en una tarjeta 1080×1080 con
el texto del tuit y su alt-text: la investigación y la verificación son las de
`/hilo`, pero el guionista elige un solo dato entre varias candidatas y no hay
hilo. La publicación en X es manual; el framework deja todo en
`datos/YYYY-MM-DD-<slug>/` (`dato.png`, `tarjeta.html`, `dato.html`, `post.md`,
`datos.json`, `dato.json`).

```
Investigación (investigador: pista → tema final, encuadre ligero, candidatas con `impacto`)
→ Verificación (verificador: todas las candidatas)
→ Guion (guionista: puntúa 1–5 × 5 criterios, elige UNA, un tuit con visual)
→ Producción (productor: QA visual → consolidar → ensamblar.py --check
  → C1/C5/C7/alt → --solo-estado → memoria.py → make validate)
```

Orquesta `.claude/workflows/dato.js` (invocado por `/dato [pista] [smoke|fixture]`)
con los cuatro agentes `hilo-investigador`, `hilo-verificador`, `hilo-guionista`
y `hilo-productor` reutilizados (sin editor ni visualistas). La pista es
opcional: un tema, un ángulo, una fuente o una corazonada; sin pista, el
investigador elige un dato de actualidad. No usa `ideas/`. Los gates viven en
el JS y en `scripts/ensamblar.py --check` (modo dato por `guion.tipo`); lo que
se gatea viaja en los retornos. Ninguna cifra `no_confirmada` llega a la tarjeta.

- Contrato de archivos: `referencias/contrato-sesion.md`, «Sesión dato»
- Guía por rol: sección «Modo dato» de `referencias/roles/{investigador,verificador,guionista,productor}.md`
- Qué hace impactante un dato, reparto tarjeta/texto, ganchos: `referencias/narrativa.md`, «Dato único»
- Sistema visual y catálogo (`cifra` = «¿Cuál es EL dato?»): `referencias/diseno/sistema.md`, `referencias/diseno/graficos.md`
- Registro y consulta: `python3 scripts/memoria.py --registrar <sesion> --ruta datos/<fecha>-<slug>` · `python3 scripts/memoria.py --datos ["tema"]`
- Prueba sin agentes: `python3 scripts/materializar.py sesiones/_fixture_dato && python3 scripts/ensamblar.py sesiones/_fixture_dato --check` → abre `sesiones/_fixture_dato/salida/dato.html`
