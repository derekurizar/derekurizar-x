# Flujo `/dato` — índice

Un dato es **UNA cifra impactante** de Guatemala en una tarjeta 1080×1080 con
el texto del tuit y su alt-text: la investigación y la verificación son las de
`/hilo`, pero el guionista elige un solo dato entre varias candidatas y no hay
hilo. La publicación en X es manual; el framework deja todo en
`datos/YYYY-MM-DD-<slug>/` (`dato.png`, `tarjeta.html`, `dato.html`, `post.md`,
`datos.json`, `dato.json`).

```
Investigación (investigador: pista → tema final, encuadre ligero, candidatas con `impacto`)
→ Verificación (verificador: todas las candidatas, cierre con verificacion.py)
→ Guion (guionista: puntúa 1–5 × 5 criterios, elige UNA, un tuit con visual)
→ Rechequeo (verificador: la cifra elegida y su comparación; si cae, otra candidata)
→ Producción (productor: QA visual → consolidar → ensamblar.py --check
  → C1/C5/C7/alt → --solo-estado → memoria.py → make validate)
```

Orquesta `.claude/workflows/dato.js` (invocado por `/dato [modo] [pista] [smoke|fixture]`)
con los cuatro agentes `hilo-investigador`, `hilo-verificador`, `hilo-guionista`
y `hilo-productor` reutilizados (sin editor ni visualistas). La pista es
opcional: un tema, un ángulo, una fuente o una corazonada; sin pista, el
investigador elige un dato de actualidad. No usa `ideas/`. Los gates viven en
el JS y en `scripts/ensamblar.py --check` (modo dato por `guion.tipo`); lo que
se gatea viaja en los retornos. Ninguna cifra `no_confirmada` llega a la tarjeta.

**Modos** (`args.modo`, tabla `MODOS` en `dato.js`; espejo mínimo en
`ensamblar.py`; alias `/vs`, `/mapa`, `/antes`): mismos cuatro agentes y mismo
entregable; cambian el gancho, las plantillas y los gates, y el guion lleva un
bloque del modo.

| modo | qué publica | gancho | plantillas | gate propio |
|---|---|---|---|---|
| `vs` | Guatemala frente a otros países | libre | `barras-h`, `pesas`, `pendiente`, `dispersion`, `cifra`+comparación | todos de la misma fuente, edición y periodo; cifra elegida `desglose` por país con Guatemala; Guatemala destacada; nota con fuente común y año; sin «ganamos/perdemos» |
| `mapa` | brecha por departamento | `brecha_territorial` | `mapa` | desglose ≥ 12 departamentos (ideal 22, nombres INE); tasa per cápita con denominador INE (absoluto solo con motivo); nota con unidad y año |
| `antes` | hace N años frente a hoy | `antes_despues` | `antes-despues`, `pendiente`, `pesas`, `linea`, `agrupadas` (series = los dos años) | misma serie y fuente, ≥ 5 años de distancia; etiquetas con los años; dinero corriente declarado en la nota |

Guía por rol: apartado «Modos vs · mapa · antes» de cada `roles/<rol>-dato.md`; reglas
editoriales en `referencias/narrativa.md`, «Modos de un dato».

- Contrato de archivos: `referencias/contrato-sesion.md`, «Sesión dato»
- Guía por rol: `referencias/roles/{investigador,verificador,guionista,productor}.md` y su complemento `roles/<rol>-dato.md`
- Qué hace impactante un dato, reparto tarjeta/texto, ganchos: `referencias/narrativa.md`, «Dato único»
- Sistema visual y catálogo (`cifra` = «¿Cuál es EL dato?»): `referencias/diseno/sistema.md`, `referencias/diseno/graficos.md`
- Registro y consulta: `python3 scripts/memoria.py --registrar <sesion> --ruta datos/<fecha>-<slug>` · `python3 scripts/memoria.py --datos ["tema"]`
- Prueba sin agentes: `python3 scripts/materializar.py sesiones/_fixture_dato && python3 scripts/ensamblar.py sesiones/_fixture_dato --check` → abre `sesiones/_fixture_dato/salida/dato.html`
