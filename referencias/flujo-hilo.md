# Flujo `/hilo` — índice

Un hilo es una **historia con datos** sobre UN tema de Guatemala, en 4–21
tuits (el usuario puede fijar un mínimo con `min_tuits`), cada uno con una tarjeta 1080×1080 (salvo, si conviene, el primero y el
último). El texto del tuit es opcional. La publicación en X es manual; el
framework deja todo en `hilos/YYYY-MM-DD-<slug>/`.

```
Encuadre (editor) → [Investigación → Verificación (+ verificacion.py)] por eje, en pipeline
→ Guion (guionista) → Rechequeo (verificador: ancla, T1, segunda fuente baja)
→ Visuales (visualistas en lotes de 3)
→ Ensamblado (productor: ensamblar.py --check + coherencia C1–C8 + memoria)
```

Orquesta `.claude/workflows/hilo.js` (invocado por `/hilo [tema] [smoke|fixture]`).
Los gates viven en el JS y en `scripts/ensamblar.py --check`; lo que se gatea
viaja en los retornos. Ninguna cifra `no_confirmada` llega al hilo.

**Modos** (`args.modo`, tabla `MODOS` en `hilo.js`; espejo mínimo en
`ensamblar.py`; alias `/explica`, `/perfil`): mismos agentes y entregable;
cambian el arco y los gates, y el guion lleva un bloque del modo.

| modo | qué publica | arco | gate propio |
|---|---|---|---|
| `explica` | el tema explicado con sus números | `gancho → paso… → cierre`, 3–6 tuits, sin giro ni impacto | un paso por tuit intermedio con cifra y texto no vacío; `explica{pregunta, pasos[]}`; cero adjetivos valorativos |
| `perfil` | retrato de un departamento o grupo frente al país | `gancho → dimension… → cierre`, 5–8 tuits, sin giro ni impacto | cada tarjeta compara sujeto y país (rótulo «Guatemala/nacional/país», `comparacion` o `mapa`); sujeto en T1; `perfil{sujeto, tipo, dimensiones[]{n, nombre, anio}}`; años distintos nombrados en el cierre |

Guía por rol: «Modo explica» y «Modo perfil» en editor, investigador,
guionista y productor; reglas editoriales en `referencias/narrativa.md`,
«Explicador» y «Perfil».

Banco de ideas: `/ideas` (`.claude/workflows/ideas.js`, guía
`referencias/roles/explorador.md`) deja temas con datos comprobados en
`ideas/banco.json`. `/hilo idea:<id>` (o `/hilo` sin tema) parte de una idea; el
editor la copia a `encuadre.idea_id` y `memoria.py` la marca `hecha` al registrar.

- Contrato de archivos y reglas de datos: `referencias/contrato-sesion.md`
- Guía por rol: `referencias/roles/{editor,investigador,verificador,guionista,visualista,productor}.md`
- Narrativa, ganchos (`hook_tipo`), dato héroe, honestidad, alt-text: `referencias/narrativa.md`
- Sistema visual y gate de render: `referencias/diseno/sistema.md`
- Catálogo de gráficos, contrato `DATA`, flujo del visualista, checklist QA: `referencias/diseno/graficos.md`
