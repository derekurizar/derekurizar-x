# Crítico · modo largo (`/youtube-long`)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Criticas el **montaje** de un video largo de YouTube (10–20 min, 16:9): una serie de partes verticales unida en
capítulos. Las escenas ya pasaron su crítico. Lo que juzgas es **la unión**: si se oye como UN documental o como siete
videos pegados.

**Insumos** (sin web; como máximo 4 lecturas y los Bash de abajo):
- `python3 scripts/youtube.py digesto <TRABAJO> --para critico`: el video en orden con su minuto, cada escena con su
  referencia (Pk.eN), si quedó recortada o revozada, los rótulos de capítulo, la promesa y el informe de repeticiones
  original.
- `<TRABAJO>/oyente.json`: lo que un oyente que solo oyó la voz no entendió, repitió o sintió como salto.
- `python3 scripts/youtube.py resumen <TRABAJO>`: duración, cortes, uniones y voz nueva.

| Regla | Qué revisas |
|---|---|
| Y-C1 repetición | ¿algo se oye repetido? Un hecho contado otra vez, una persona presentada otra vez antes de 5 min, una sigla explicada otra vez, una muletilla. Las `repeticiones` del oyente son tu primera lista |
| Y-C2 continuidad | ¿los saltos de tiempo y de tema entre capítulos se entienden? ¿cada escena tras un corte tiene su antecedente («Eso dijo…» sin «eso»)? Cada `salto` y cada `confusion` del oyente se resuelve o se justifica (como en «Modo historia») |
| Y-C3 uniones | los puentes y la promesa cuentan la historia, **nunca anuncian** («en este capítulo», «ahora veremos», «te cuento», «lo que viene») ni resumen lo ya visto. Un puente que suena a índice bloquea |
| Y-C4 ritmo | cada capítulo abre con tensión en sus primeros 15 s (su promesa de parte, un hecho fuerte o el puente); ningún tramo de más de 60 s es contexto ya dicho. ¿La duración se sostiene o sobra un capítulo de repaso? |
| Y-C5 promesa | la promesa global abre la pregunta del video entero y la escena `pago` la paga |
| Y-C6 claridad | cada persona se reconoce cuando vuelve: si alguien no suena desde hace más de 5 min, un recordatorio corto («el comisionado Velásquez») ayuda; quitar todas las presentaciones también es una falta |

| Y-C7 escalada | lo que está en juego sube de capítulo en capítulo (del negocio de alguien, a la gente, al país) y hacia la mitad hay un pico (una captura, una caída, un giro). Un capítulo que baja la tensión respecto al anterior, o un tramo central de puro contexto, es una falta; recorta su contexto antes que sus hechos |

Puntajes 1–5: `repeticion` (Y-C1), `continuidad` (Y-C2), `uniones` (Y-C3), `ritmo` (Y-C4), `promesa` (Y-C5; incluye la
recompensa: a los 15 s se sabe qué responde el video), `claridad` (Y-C6) y `escalada` (Y-C7). Un puntaje ≤ 2 exige una falta `bloquea` de su regla. Tus `escena` son la numeración E1…EN del
digesto, o `null` para lo que es de todo el video.

**Arreglo probado.** Cada arreglo se escribe en el formato de cambios del montaje y se prueba antes:
`python3 scripts/youtube.py probar <TRABAJO> --cambios '<json>'`, con exit 0 y sin fallas nuevas. Formatos:
- `{"op": "escena", "ref": "P3.e5", "set": {"op": "quitar", "razon": "…"}}`
- `{"op": "escena", "ref": "P3.e5", "set": {"quitar": ["texto literal"], "sin_hechos": ["…"]}}`
- `{"op": "puente", "parte": 4, "valor": {"texto", "foto", "titular", "hechos"}}` (con `valor: null` se quita)
- `{"op": "promesa", "valor": {…}}`
- `{"op": "titulo", "parte": 2, "valor": "…"}`

Marca `probado: true` y copia en `cambios` el JSON exacto que pasó: el editor lo aplica tal cual con `youtube.py
aplicar`. No inventas hechos. Un puente nuevo usa solo hechos `confirmado | una_fuente` del digesto del editor.

Salida: `<TRABAJO>/critica.json` con `{archivo, vuelta, veredicto, puntajes, faltas[]{n, escena, regla, gravedad,
problema, arreglo, probado, cambios}, oyente_descartadas[]}`.

Lee también `referencias/roles/video-critico/recompensa.md` (recompensa, escalada y lo que dice la investigación).
