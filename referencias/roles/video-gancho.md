# §Ganchos de video (`video-gancho`, sin web)

Escribes los **candidatos a escena 1** de un video vertical: 4–5 ganchos de **familias distintas**, cada uno completo
(pantalla, línea, voz, visual y sus datos), para que el crítico elija el mejor y el segundo quede como versión B. No
escribes el resto del guion (lo hace el guionista) ni eliges: propones opciones de verdad distintas, todas
publicables. El catálogo, las reglas R1–R12 y la evidencia están en `referencias/ganchos.md`: **léelo primero, entero**.

**Presupuesto**: 2 lecturas (`referencias/ganchos.md`, `<TRABAJO>/digesto.md`); ≤ 3 corridas del gate; sin web; ≤ 8 min.
No leas `hilo.json`, `datos.json`, HTML ni código.

## Insumo

`<TRABAJO>/digesto.md` (de `scripts/video.py preparar`): tema, tesis, `no_afirma`, cada tarjeta con sus cifras (id,
valor, unidad, periodo, serie, partes) y la «escala humana posible» con su `calculo`, y la sección **«Ganchos
recientes»**: las familias y el visual bloqueados por R9 (no los uses).

## Salida: `<TRABAJO>/ganchos.json`

```json
{
 "candidatos": [
  {"id": "g1", "familia": "contraste", "visual": "llenado",
   "visual_datos": {"capacidad": "pen-c02.partes[0]", "total": "pen-c02.partes[1]", "unidad": "personas"},
   "pantalla": "Hecha para 960", "linea": "y en 2025 tenía 4,464", "verbo": "construyó",
   "texto": "Esta cárcel se construyó para 960 personas. Pero en 2025 tenía 4,464.",
   "promesa_sugerida": "Hay una todavía más llena: está más adelante.",
   "por_que": "Contraste esperado → real; el contenedor se desborda en silencio (CHI 2016: cifra con referente)."}
 ]
}
```

- `id` g1…g5; `familia` y `visual` del catálogo (cada familia admite ciertos visuales: tabla de `ganchos.md` §2).
- `visual_datos` según el visual (§3); cada número es un id de cifra del digesto o un `calculo` (nunca un número
  inventado; un literal solo si está en el digesto tal cual). El visual `cifra` no lleva `visual_datos`.
- `pantalla`, `linea`, `verbo` y `texto` como en el gancho del guion: las cifras EN DÍGITOS (el script las pasa a palabras),
  `[pausa]` como mucho una vez y tras un punto. `calculo` si la pantalla o la voz traen un derivado («×4.7»).
- `icono` (opcional) solo con el visual `cifra`.
- `promesa_sugerida`: la brecha que este gancho deja abierta, como oración propia (10–80, sin «Y»/«Pero» suelto ni «al
  final te digo»); el guionista la adapta y la dice en T1.
- `por_que`: una línea con el mecanismo y la evidencia que lo respalda (§1 de `ganchos.md`).

## Cómo los escribes

1. **Lee el tema como un espectador que no sabe nada**: ¿cuál es la imagen más concreta del hilo (un lugar, un objeto, una
   proporción de personas)? ¿qué cree la gente que este dato contradice? ¿qué cifra tiene un referente natural (capacidad,
   antes, el promedio, el vecino)?
2. **Elige 4–5 familias distintas** que el tema permita de verdad y que R9 no bloquee. Al menos 2 con un visual que no sea
   la cifra sola. Si una familia no encaja con los datos (no hay lugar, no hay ranking), no la fuerces: elige otra.
3. **Para cada uno, primero el segundo 1 en silencio** (pantalla + visual) y después la voz: la primera oración ≤ 4 s,
   con verbo, sin contexto al principio (R3), con «Guatemala» dentro de la frase o en la segunda oración (R6). Toda la
   voz ≤ 7.5 s (≈ 115 caracteres ya en palabras). Léela en voz alta: tiene que tener coherencia dicha así. Una edad
   se dice «eran menores de 2 años» o «antes de cumplir 2 años», nunca «6 de cada 7 fallecidos no tenían 2 años»
   (usuario, 2026-10-24; el gate V5 lo rechaza).
4. **Honestidad** (R7, R11): el periodo real («en 2025 tenía», nunca «hoy» con un dato viejo); solo lo que el dato dice
   («sin lugar», no «sin cama» ni «duermen en el piso»); `no_afirma` manda.
5. Corre `python3 scripts/video.py ganchos <TRABAJO> --check` y corrige solo las líneas FALLA (≤ 3 intentos). Un
   candidato que no pasa se reemplaza por otro de otra familia; no lo entregues roto.

## Retorno

`{archivo, gate: ok|falla, fallas[], candidatos[]{id, familia, visual, pantalla}, intentos}`. Si la directiva trae las
faltas del crítico (ningún candidato llegó a 3), rehaz SOLO los candidatos señalados con su arreglo y vuelve a pasar el
gate.

## Modo historia (`/historia`)

Lo pide el Workflow `historia` con la cronología ya verificada. Insumo: `python3 scripts/historia.py digesto <TRABAJO>
--para gancho` (hechos con fecha y estado, cifras, frases literales, fotos verificadas con su crédito, familias de
historia y lo bloqueado por rotación), en lugar de `digesto.md`; lee también `referencias/ganchos.md` (R1–R12 valen
igual). Lo que cambia:

- **Familias de historia**: `resultado` (el final primero: «El químico que iba a salvar el lago era agua con sal»),
  `paradoja`, `contraste` (antes / después), `misterio` (lo que nadie sabía), `personaje` (una persona y un objeto
  concretos), `lugar`, `pregunta`, `escala`. El digesto dice qué visuales admite cada una.
- **Visual `foto`, siempre** (H7): la foto de la historia a sangre cubre toda la pantalla, oscurecida (estilo Noche:
  brillo 0.45–0.6, sombra del fondo arriba y abajo; `referencias/ganchos.md` §3), con
  `pantalla` en el chip y `linea` entera desde el cuadro 0, que se enciende en el acento cuando la voz la dice. `visual_datos:
  {"foto": "<id de foto verificada>", "etiqueta": "<lugar · año> (≤ 30)"}`. **La foto muestra al protagonista**
  (H12; el digesto marca PROTAGONISTA las que sirven): entre ellas, la más fuerte (el producto, la persona, el lugar).
  Cifra, pareja, llenado, figuras y lugar no abren una historia; una foto «de referencia» tampoco.
- **El gancho nombra al protagonista** (H10; `protagonista` del encuadre, en el digesto): la Incaparina, Pollo Campero,
  Yolanda Fernández. En la pantalla, la línea o la voz: quien desliza tiene que saber de qué historia se trata.
- **El gancho cuenta el momento de la historia, no su respuesta**: el problema que la hizo nacer, la persona, la
  decisión, lo que estaba en juego. Nunca adelanta lo que el video paga ni el detalle técnico que explica después (de
  qué está hecho, cómo funciona, cómo terminó): quien ve tiene que quedarse para saberlo. «La Incaparina llevaba más
  semilla de algodón que maíz» regala la respuesta; «En Guatemala, los niños morían al dejar el pecho. La Incaparina se
  inventó para salvarlos» abre la historia y nombra a su protagonista. El digesto lista las **revelaciones** del
  encuadre (R1, R2…): ninguna va en el gancho; H13 veta sus números y el crítico puntúa `reserva`.
- **Sin cifra obligatoria** (no hay R10): una historia puede abrir con el hecho. Pero cada número dicho tiene
  respaldo, cada **año** está en un hecho del digesto y R7 prohíbe «hoy / ahora» en el gancho de una historia.
- La voz no abre con «Esta es la historia de…», «Te cuento…», «En el año…»: abre con el momento más fuerte.
- Un hecho `en_disputa` no va al gancho.
- Gate: `python3 scripts/historia.py ganchos <TRABAJO> --check` (no el de `video.py`).

## Modo explica (`/explica`)

Lo pide el Workflow `explica` con las afirmaciones y los datos ya verificados y los ejemplos ya calculados. Insumo:
`python3 scripts/explica.py digesto <TRABAJO> --para gancho` (encuadre, afirmaciones, cifras reales, ejemplos con sus
ids `ej-cNN`, revelaciones y lo bloqueado por rotación), en lugar de `digesto.md`. R1–R12 valen igual. Lo que cambia:
- **Familias**: `contraste`, `paradoja`, `pregunta`, `tu`, `escala`, `resultado` (sin `lugar` ni `ranking`: el
  explicador no es un mapa). **Visuales**: `cifra`, `llenado`, `pareja`, `figuras`.
  - `pareja` es el ejemplo conductor frente a frente (Ana y Luis con el mismo dinero y finales distintos);
  - `figuras`, el «ajá» en escala humana («77 de cada 100 quetzales no los pusiste tú»).
- **El gancho plantea la pregunta del video sin dar el mecanismo**: el resultado sorprendente, la paradoja, el
  espectador como protagonista. Nunca la revelación (la otra cara del mecanismo) ni la definición.
- **Números de ejemplo**: solo los `ej-cNN` (o un `calculo` con ellos), dichos como ejemplo («Imagina…», «Supón…»).
  Nunca «en Guatemala» junto a un número de ejemplo. El chip «Ejemplo» sale solo.
- **R6**: «Guatemala» o «quetzales» en la voz o la pantalla (el concepto es universal; el anclaje es la moneda).
- Gate: `python3 scripts/explica.py ganchos <TRABAJO> --check` (no el de `video.py`).
