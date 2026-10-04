# Flujo `/hilo` — índice

Un hilo es una **historia con datos** sobre UN tema de Guatemala, en 4–21
tuits (el usuario puede fijar un mínimo con `min_tuits`), cada uno con una tarjeta 1080×1080 (salvo, si conviene, el primero y el
último). El texto del tuit es opcional. La publicación en X es manual; el
framework deja todo en `hilos/YYYY-MM-DD-<slug>/`.

```
Encuadre (editor) → [Investigación → Verificación] por eje, en pipeline
→ Guion (guionista) → Visuales (visualistas en lotes de 3)
→ Ensamblado (productor: ensamblar.py --check + coherencia C1–C8 + memoria)
```

Orquesta `.claude/workflows/hilo.js` (invocado por `/hilo [tema] [smoke|fixture]`).
Los gates viven en el JS y en `scripts/ensamblar.py --check`; lo que se gatea
viaja en los retornos. Ninguna cifra `no_confirmada` llega al hilo.

Banco de ideas: `/ideas` (`.claude/workflows/ideas.js`, guía
`referencias/roles/explorador.md`) deja temas con datos comprobados en
`ideas/banco.json`. `/hilo idea:<id>` (o `/hilo` sin tema) parte de una idea; el
editor la copia a `encuadre.idea_id` y `memoria.py` la marca `hecha` al registrar.

- Contrato de archivos y reglas de datos: `referencias/contrato-sesion.md`
- Guía por rol: `referencias/roles/{editor,investigador,verificador,guionista,visualista,productor}.md`
- Narrativa, ganchos (`hook_tipo`), dato héroe, honestidad, alt-text: `referencias/narrativa.md`
- Sistema visual y gate de render: `referencias/diseno/sistema.md`
- Catálogo de gráficos, contrato `DATA`, flujo del visualista, checklist QA: `referencias/diseno/graficos.md`
