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
- **Visual `foto`**: la foto de la historia a sangre, oscurecida, con `pantalla` en el chip y `linea` entera desde el
  cuadro 0, que se enciende cuando la voz la dice. `visual_datos: {"foto": "<id de foto verificada>", "etiqueta":
  "<lugar · año> (≤ 30)"}`. Los visuales de `/video` (cifra, pareja, llenado, figuras, lugar) siguen disponibles.
- **Sin cifra obligatoria** (no hay R10): una historia puede abrir con el hecho. Pero cada número dicho tiene
  respaldo, cada **año** está en un hecho del digesto y R7 prohíbe «hoy / ahora» en el gancho de una historia.
- La voz no abre con «Esta es la historia de…», «Te cuento…», «En el año…»: abre con el momento más fuerte.
- Un hecho `en_disputa` no va al gancho.
- Gate: `python3 scripts/historia.py ganchos <TRABAJO> --check` (no el de `video.py`).
