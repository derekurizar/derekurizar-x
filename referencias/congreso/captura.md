# Captura del registro nominal del Congreso (/congreso)

congreso.gob.gt está detrás de Incapsula: `curl`, `historia.py leer` y Playwright reciben un desafío. Dentro de una
pestaña de Chrome (Claude in Chrome) un `fetch` del mismo origen sí funciona. Solo lectura: GET a páginas públicas, sin
clics que envíen nada, sin iniciar sesión. Una pestaña nueva del grupo MCP; ciérrala al terminar.

## Rutas del sitio (comprobadas el 2026-11-04)

| Qué | Ruta |
|---|---|
| Todas las sesiones (1,095 en un solo HTML) | `/seccion_informacion_legislativa/votaciones_pleno` → filas «tipo · número · No. 56, Fase 1, Fecha 03/11/2026 12:57:59 · Ver Votaciones» |
| Votaciones de una sesión | `/eventos_votaciones/<id_sesion>` → pregunta, número, hora, `detalle_de_votacion/<id_votacion>/<id_sesion>` y su PDF |
| Votos de una votación | `/detalle_de_votacion/<id_votacion>/<id_sesion>` → 4 tablas (a favor, contra, ausencia, licencia/excusa) con «Apellidos Nombres · ESTADO · VOTO»; sin totales aparte |
| Los 160 diputados | la portada `/`: tarjetas `.event-box` «Nombre Bloque: X Distrito: Y» (los independientes: «INDEPENDIENTE Distrito: …») con su miniatura (`uploads/diputados/thumbs/…-peq.jpg`, cara y hombros) |
| Perfil | `/perfil_diputado/<id>`: foto de cuerpo entero con bandera (no sirve para el avatar), comisiones |
| Notas oficiales | `/noticias_congreso/<id>/<año>/<n>`: el texto de la sesión (qué aprobó, con cuántos votos) y su og:image |
| Iniciativa | el número de `detalle_pdf/iniciativas/<id>` es un id interno, **no** el número de iniciativa: busca la ley por la nota oficial |

## Cómo sale el JSON

`javascript_tool` corta su salida cerca de 1 KB. `CG.correr` deja el JSON en un `<textarea id="cg-salida">` arriba a la
izquierda; luego `computer left_click (150, 60)` → `key cmd+a` → `key cmd+c` y en Bash `pbpaste > <archivo>.json`.
Un bucle largo corre sin `await`: consulta `CG.estado` (y `CG.error`, `CG.bytes`) en otra llamada hasta «listo».

```text
1. pega referencias/congreso/captura.js completo (define window.CG)
2. CG.correr({desde: "2026-10-30"})                 sesiones desde esa fecha, sus votaciones y los 160 votos de cada una
   CG.correr({padron: true})                        los 160 de la portada (nombre, bloque, distrito, miniatura)
   CG.correr({fotos: ["39", "770"]})                 miniaturas de esos perfiles (los nombrados) como dataURL
   CG.correr({textos: ["/noticias_congreso/17397/2026/4"]})   texto y foto de notas oficiales
   CG.correr({pdfs: ["/assets/uploads/info_legislativo/…pdf"]})   PDFs como dataURL
3. CG.estado → «listo»; copia el textarea y guárdalo en sesiones/_congreso/capturas/<fecha>_<qué>.json
```

Luego, según lo capturado: `congreso.py importar` (votaciones), `congreso.py padron` (padrón: pásale también una captura
con votaciones, que da el orden «Apellidos Nombres» para partir los nombres), `congreso.py fotos --captura` (retratos) y
`congreso.py leer` (textos, PDFs y la foto de la nota).

## Trampas

- Una votación que ya está en la base se **coteja** voto por voto (la base vino de los xlsx oficiales): si no coincide,
  `importar` falla (CG1) y no escribe nada.
- La bancada que guarda la base es la del sistema de votación (la actual); la portada da otra etiqueta («VAMOS» para
  todo el bloque original). `padron` usa la de la base.
- Apodos en la portada («Willy Ralda» = Guillermo Antonio Ralda Conde): `padron` los liga por apellido y distrito.
- Un diputado presente que no marca su voto queda «ausente» (Ley Orgánica, art. 94; ver la investigación N.º 03).
