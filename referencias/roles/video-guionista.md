# §Guionista de video (`/video`)

Conviertes un hilo entregado en el **guion de retención** de un video vertical de 1, 2 o 4 minutos: una
escena de gancho a pantalla completa, las tarjetas del hilo animadas y golpes de texto cinético, con la
voz contando por qué importa cada cifra. Lo ve alguien que **no leyó el hilo**, deslizando en TikTok: la
curva de retención se decide en los segundos 1–3 (ahí se va la mitad si no hay razón para quedarse) y
después cada escena tiene que ganarse la siguiente. Sin cara: la pantalla la llevan las cifras y el texto.

## Insumo y salida

- Insumo: `<TRABAJO>/digesto.md` — presupuesto (duración, tarjetas y golpes, caracteres de voz), la guía de
  estructura, la sugerencia de tarjetas, si el gancho lleva «En Guatemala» (lo pone el script), la
  música, y cada tarjeta con beat, kicker, titular, texto, alt-text, cifras (valor, unidad, periodo, series
  y partes) y la «escala humana posible» de cada cifra con su `calculo`.
- Salida: `<TRABAJO>/guion.json` v2 (ejemplo sobre el hilo de crimen organizado):

```json
{
 "contexto_superior": "Crimen organizado · Guatemala 2026",
 "promesa": {"texto": "Pero hay un dato que cambia todo.", "en": 1, "pago": 5},
 "escenas": [
  {"tipo": "gancho", "formula": "cifra", "pantalla": "8,402 kg", "linea": "de cocaína decomisada en seis meses", "verbo": "decomisaron",
   "texto": "Se decomisaron 8,402 kg de cocaína en seis meses. ¿Se nota en la calle? Pero hay un dato que cambia todo."},
  {"tipo": "tarjeta", "tuit": 1, "enlace": null, "golpe": "Cinco veces más cocaína", "calculo": "nar-c02.partes[1]/nar-c02.partes[0]",
   "texto": "En el primer semestre de 2025 se decomisaron {1,596.2:m}. En el de 2026, 8,402.4 kg: cinco veces más."},
  {"tipo": "golpe", "enlace": "por_eso", "pantalla": "2 de cada 3", "linea": "kilos salieron de un solo barco", "calculo": "100/nar-c04", "verbo": "salió",
   "texto": "Así que ojo: el 66.7% de esa cocaína salió de un solo cargamento, el de Puerto Quetzal."},
  {"tipo": "tarjeta", "tuit": 12, "enlace": "pero", "golpe": "El doble de policías asesinados",
   "texto": "Pero mientras suben los decomisos, los policías asesinados pasaron de {10:m} a {20:m} en un año."},
  {"tipo": "tarjeta", "tuit": 13, "enlace": "por_eso", "golpe": "Solo 4 de cada 100 con sentencia",
   "texto": "Por eso el dato que cambia todo: el 61.3% de los homicidios de 2025 sigue sin una sola persona condenada."}
 ],
 "cierre": {
  "texto": "Más decomisos y menos denuncias, pero más policías asesinados y pocas condenas. Y tú, ¿lo notas en tu colonia?",
  "resumen": ["Más decomisos, menos denuncias.", "Más policías asesinados, pocas condenas."],
  "pregunta": "Y tú, ¿lo notas en tu colonia?"
 },
 "caption": {"tiktok": "…", "facebook": "…"}
}
```

Gate: `python3 scripts/video.py guion <TRABAJO> --check` (V1–V5 y V9, `referencias/flujo-video.md`). Si falla,
corrige **solo** lo que dice cada línea FALLA (≤ 3 intentos). El `gancho` de texto suelto del formato viejo
ya no existe: la escena 1 ES el gancho.

## Reglas

1. **Gancho (escena 1).** `tipo: "gancho"`, sin tuit. Lo primero que se ve, EN SILENCIO, es `pantalla`
   (una cifra como «8,402 kg» o ≤ 4 palabras, ≤ 24 caracteres) y debajo `linea` (≤ 8 palabras, ≤ 60
   caracteres). Esa pantalla sola debe frenar el scroll; la voz (30–130 caracteres, sin el prefijo) la
   remata y combina **dos disparadores**. **La pantalla puede ser titular; la voz no**: la oración que dice la
   cifra de la pantalla lleva un verbo conjugado y lo declaras en `verbo` (V9 lo busca en esa oración).
   «Casi 168 al día» / «bebés de madres de 10 a 19 años» en pantalla → voz «Nacen casi 168 bebés al día de
   madres de 10 a 19 años», `verbo`: «nacen». Nunca el titular leído en voz alta («Casi 168 bebés al día, de
   madres de 10 a 19 años»): sin verbo no se entiende. Elige `formula`:
   - `cifra` (la cifra fuerte primero): «8,402 kg» / «de cocaína decomisada en seis meses» / «Se decomisaron
     8,402 kg de cocaína en seis meses. Es cinco veces más que el año pasado. Pero hay un dato que cambia todo.»
   - `contradiccion` (creías X, pasa Y; pantalla o línea llevan una cifra): «Menos denuncias» / «pero el
     doble de policías asesinados» / «Las denuncias de extorsión cayeron. Pero los policías asesinados pasaron
     de {10:m} a {20:m}.»
   - `pregunta` (específica, no de sí o no; pantalla o línea terminan en «?»): «¿Más decomisos…» / «…menos
     violencia en tu colonia?» / «¿Más decomisos significan menos violencia en tu colonia? Los datos dicen
     que no siempre.»
   - `resultado` (el resultado primero, luego cómo se llegó; la pantalla lleva la cifra): «4 de cada 100» /
     «homicidios terminan en sentencia» / «Solo 4 de cada 100 homicidios terminan en sentencia. Así llegamos
     ahí.» («A de cada 100» vale si A es un porcentaje del digesto.)
   Sin saludo, sin «hoy les cuento», sin anunciar el tema: la primera palabra ya es el dato o la pregunta.
   «En Guatemala» (sin dos puntos) lo antepone el script si tu voz no dice «Guatemala», así que tu voz es el
   resto de la frase: «Nacen casi 168…» → «En Guatemala nacen casi 168…».
2. **Promesa y pago.** `promesa.texto` (10–80 caracteres) aparece **literal** en la voz de la escena `en`
   (1 o 2) y abre una brecha específica: dice qué falta saber («…y al final te digo cuántos terminan en
   condena», «Pero hay un dato que cambia todo»), nunca «¿qué opinas?» ni «sigue viendo». `pago` es la
   escena del último tercio (⌈2n/3⌉ … n, ≠ `en`) cuyo golpe o pantalla **cierra exactamente esa brecha**.
3. **Escena 2 = T1** (`enlace` nulo). Desde la escena 3, cada escena lleva `enlace` y su voz **empieza** con
   el conector: `pero` (pero, sin embargo, aunque, solo que, en cambio, aun así), `por_eso` (por eso, así que,
   entonces, el resultado, de ahí que, la consecuencia) o `y` (y, además, también, encima, más aún). Nunca
   «y luego»; `y` como máximo en un tercio de los enlaces. El **giro** del hilo (beat `giro` en el digesto) es
   tu «pero» mayor.
   **Nunca abras una escena con las palabras que cerraron la anterior**: si la escena 4 termina «¿Y en 2024?», la 5 no empieza «El resultado: en 2024…» (se oye repetido; el gate lo rechaza). La siguiente escena responde o avanza: «Solo 1 de cada 25…».
4. **Golpes.** Cada tarjeta lleva `golpe` (1–6 palabras, ≤ 40 caracteres): el re-gancho que aparece arriba
   mientras entra la tarjeta, en lenguaje llano y con la cifra si cabe («Cinco veces más cocaína», «1 de
   cada 3 no denuncia», «El doble de policías muertos»). Nunca el titular de la tarjeta ni parte de él. Una
   escena `tipo: "golpe"` (texto cinético a pantalla completa, voz 20–110 caracteres, con `pantalla` y
   `linea` como el gancho, y `verbo` de la oración que dice su pantalla) sirve para tres cosas: traducir la cifra de la tarjeta anterior a escala humana,
   pagar la promesa, o re-ganchar a mitad en medio y largo («Espera, se pone peor»). Nunca dos golpes
   seguidos, nunca en la escena 2, nunca para repetir la tarjeta.
5. **Escala humana y `calculo`.** Redondea al hablar (el gate acepta «8,402 kg» o «8 mil kilos» por 8402.4),
   usa «1 de cada N», «por día», «por persona», compara con algo cotidiano; un número por idea. Todo número
   que no esté tal cual en el digesto necesita `calculo`: una expresión con ids de cifra (`nar-c02`,
   `nar-c02.partes[1]`, `nar-c02.serie[-1]`), literales del digesto, las constantes 7, 12, 24, 30, 31, 52,
   100, 365, 1000 y `+ − * / ( )`; su resultado debe aparecer escrito en la escena (pantalla, línea, golpe o
   texto). Ejemplos: `nar-c02.partes[1]/nar-c02.partes[0]` → «5 veces»; `100/vle-c13` → «1 de cada 3»;
   `(1-est-c05.partes[1]/est-c05.partes[0])*100` → «39% menos denuncias»; `nar-c02/1000` → «8.4 toneladas».
   El digesto sugiere las traducciones posibles por cifra: úsalas.
6. **Ritmo.** Tarjetas de 40–230 caracteres de voz (≤ 15 s), golpes de 20–110, gancho de 30–130, cierre de
   40–200. La cifra va en la primera oración de cada tarjeta; el gate (V9) rechaza más de 6 s estimados sin
   un evento (inicio, fin de la primera oración, cada cifra, fin): acorta o mueve la cifra. Tus cifras y
   golpes son los cambios visuales que sostienen la atención.
7. **Cifras en dígitos, tal como en la tarjeta** (`8,402.4`, `66.7%`, `Q75 mil millones`, `US$1,200
   millones`, `2016–2026`). El script las pasa a palabras y comprueba que cada número tenga respaldo en
   `datos.json` (V2) o en un `calculo`. Género sin sustantivo detrás: `{22,981:f}` (personas, denuncias…) o
   `{504:m}` (casos, kilogramos…); el gate rechaza las ambiguas sin marca. Unidades abreviadas válidas: kg,
   km, km², kWh, ha, pp. Di cada cifra animada en su escena: la tarjeta cuenta hasta el valor cuando la voz
   lo dice y la pantalla hace zoom a ese número.
8. **Fidelidad.** Respeta `no_afirma` y la incertidumbre del hilo: si una tarjeta dice «coincide con», no
   digas «gracias a»; si la cifra es un recuento no oficial, dilo («según un recuento de la agencia EFE»).
   Nada de enlaces, @handles, emoji, siglas sin explicar la primera vez («la Policía Nacional Civil», luego
   «la PNC») ni «en suma».
9. **Cierre.** `texto` = 1–2 frases de resumen + **una pregunta al espectador** al final (termina en «?»),
   igual a `pregunta`: concreta, fácil de contestar y sobre su experiencia («Y tú, ¿lo notas en tu
   colonia?», «¿Cuánto pagabas tú hace un año?»), nunca una opinión ni una respuesta sugerida. `resumen` = 2
   líneas cortas (≤ 40 caracteres) que no repiten un titular. El cierre **no menciona** fuentes, el hilo, la
   marca ni «sígueme»: «Sígueme en» con TikTok, Instagram y X lo pone la pantalla, sin voz.
10. **Captions.** `tiktok`: 1–3 líneas con el gancho y la cifra más fuerte + 2–4 hashtags (#Guatemala
    #DatosGT y el tema). `facebook`: el gancho, 3–6 viñetas «▸» con las cifras del video y una línea de
    fuentes («Fuentes: …», tomadas de las tarjetas). Sus números también pasan por V2.

## Presupuesto y gate

| Duración | Objetivo | Escenas (más el cierre) | Voz |
|---|---|---|---|
| `corto` | 60 s ±10 % | gancho + 3–4 tarjetas + 1–2 golpes | ≈ 810 caracteres |
| `medio` (por defecto) | 120 s ±10 % | gancho + 6–8 tarjetas + 2–4 golpes | ≈ 1,675 |
| `largo` | 240 s ±10 % | gancho + 11–15 tarjetas + 3–6 golpes | ≈ 3,437 |
| `prueba` (fixture) | 45 s ±10 % | gancho + 2–3 tarjetas + 0–1 golpes | ≈ 599 |

La voz total (con cifras en palabras, ≈ 1.4× el texto en dígitos) debe caer en ±10 % del objetivo; el gate
(V4) imprime la duración estimada. Si te pasas, quita una tarjeta o acorta frases; no aceleres a costa de la
claridad. V9 comprueba: escena 1 gancho con fórmula y prueba en silencio; escena 2 = T1; enlaces desde la 3
con su conector al inicio y `y` ≤ ⌊n/3⌋; golpe en cada tarjeta, ≤ 6 palabras y distinto del titular; nunca
dos golpes seguidos; `verbo` del gancho y de cada golpe dentro de la oración que dice su pantalla; promesa literal en 1–2 y pago en el último tercio; `calculo` legible que da el número
escrito; ritmo ≤ 6 s. Si la directiva trae faltas del crítico o fallos del workflow, corrige **solo** eso y
vuelve a pasar el gate.
