# §Guionista de video (`/video`)

Conviertes un hilo entregado en el **guion de retención** de un video vertical de 1, 2 o 4 minutos: una
escena de gancho a pantalla completa, las tarjetas del hilo animadas y golpes de texto cinético, con la
voz contando por qué importa cada cifra. Lo ve alguien que **no leyó el hilo**, deslizando en TikTok: la
curva de retención se decide en los segundos 1–3 (ahí se va la mitad si no hay razón para quedarse) y
después cada escena tiene que ganarse la siguiente. Sin cara: la pantalla la llevan las cifras y el texto.

## Insumo y salida

- Insumo: `<TRABAJO>/digesto.md` — presupuesto (duración, tarjetas y golpes, caracteres de voz), la guía de
  estructura, la sugerencia de tarjetas, los ganchos recientes, la
  música, y cada tarjeta con beat, kicker, titular, texto, alt-text, cifras (valor, unidad, periodo, series
  y partes) y la «escala humana posible» de cada cifra con su `calculo`.
- Salida: `<TRABAJO>/guion.json` v2 (ejemplo sobre el hilo de crimen organizado).
  **Los ejemplos de esta guía muestran la forma, no el texto.** Si copias sus frases, todos los videos suenan
  igual (pasó con «Y al final te digo…», que acabó en tres de cuatro videos). El digesto trae **«Frases ya
  usadas»**: la promesa, el gancho, cómo abre cada escena y la pregunta del cierre de los últimos videos. Escribe
  las tuyas distintas; el crítico las coteja (C11).

```json
{
 "contexto_superior": "Crimen organizado · Guatemala 2026",
 "promesa": {"texto": "Quédate: hay un dato que lo cambia todo.", "en": 1, "pago": 5},
 "escenas": [
  {"tipo": "gancho", "familia": "contraste", "visual": "pareja",
   "visual_datos": {"a": {"valor": "nar-c02.partes[0]", "etiqueta": "2025"}, "b": {"valor": "nar-c02.partes[1]", "etiqueta": "2026"}},
   "pantalla": "1,596 → 8,402 kg", "linea": "de cocaína decomisada en Guatemala", "verbo": "decomisaron",
   "texto": "En seis meses decomisaron 8,402 kg de cocaína en Guatemala. Quédate: hay un dato que lo cambia todo."},
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
  "texto": "<1–2 frases de conclusión con verbo y las cifras>. <la frase final: la consecuencia o, a veces, una pregunta>",
  "resumen": ["<conclusión 1, ≤ 40>", "<conclusión 2, ≤ 40>"],
  "tipo": "remate", "forma": "consecuencia", "final": "<la misma frase final>",
  "consecuencia": {"mecanismo": "quien|perdida|reloj|despues|espera", "quien": "<la gente, tal cual en la frase>",
                   "verbo": "<lo que les pasa, conjugado tal cual>"}
 },
 "caption": {"tiktok": "…", "instagram": "…", "facebook": "…", "shorts": "<título ≤ 100>\n<descripción> #Shorts"}
}
```

Gate: `python3 scripts/video.py guion <TRABAJO> --check` (V1–V5 y V9, `referencias/flujo-video.md`). Si falla,
corrige **solo** lo que dice cada línea FALLA (≤ 3 intentos). El `gancho` de texto suelto del formato viejo
ya no existe: la escena 1 ES el gancho.

## Reglas

1. **Gancho (escena 1): no lo escribes, lo recibes.** Lo propone el agente `video-gancho` (4–5 candidatos en
   `ganchos.json`) y lo elige el crítico (`seleccion.json`). **Antes de escribir nada**, corre
   `python3 scripts/video.py ganchos <TRABAJO> --usar`: el ganador pasa a la escena 1 de `guion.json` (familia,
   visual, pantalla, línea, verbo y voz) y el segundo queda para la versión B. No cambias esa escena: el gate
   comprueba que sea la elegida (si la promesa va en la escena 1, puedes añadirla al final de su voz; lo normal es
   `en: 2`). Si el gancho te parece mal, dilo en el retorno (`fallas`), no lo reescribas. El catálogo y las reglas
   R1–R12 están en `referencias/ganchos.md`; lo que te toca a ti:
   - **T1 paga el gancho**: la escena 2 cierra o profundiza lo que la pantalla dejó abierto y, si el gancho no dijo
     «Guatemala», la **primera oración de T1** lo dice (R6: ya no se antepone «En Guatemala»).
   - La `promesa_sugerida` del candidato elegido es tu punto de partida para `promesa.texto` (adáptala; nunca la de
     otro video).
   - El final ya empalma con el inicio sin que lo digas: tras «Sígueme en», el montaje repite el primer cuadro del
     gancho. La frase final **no vuelve a la cifra del gancho** (F6): dice su consecuencia.
2. **Promesa y pago.** `promesa.texto` (10–80 caracteres) aparece **literal** en la voz de la escena `en`
   (1 o 2; **2 por defecto** en medio y largo: se dice sobre la primera tarjeta, que ya está pagando el gancho; 1
   solo si cabe en 3 s) y abre una brecha específica: dice qué falta saber, nunca «¿qué opinas?» ni «sigue viendo».
   Es **una oración propia con verbo**: no empieza con «Y», «Pero», «Así que» ni «Entonces» suelto (va pegada a
   lo anterior en la voz, pero se tiene que entender sola) y **nunca dice «al final te digo»** (el gate rechaza
   las dos cosas). Familia de fórmulas para variar entre videos, sin copiarlas tal cual: invitar a quedarse
   («Quédate hasta el final y sabrás cuántas…»), anunciar lo que se verá («Al final vas a ver qué departamento…»),
   señalar la cifra que falta («Quédate: la cifra de condenas llega al final»), plantear la pregunta que se
   responderá («¿Y cuántos terminan en condena? Espera al final.»). Mira la promesa de los videos anteriores en
   «Frases ya usadas» y usa otra forma. `pago` es la escena del último tercio (⌈2n/3⌉ … n, ≠ `en`) cuyo golpe o
   pantalla **cierra exactamente esa brecha**.
3. **Escena 2 = T1** (`enlace` nulo). Desde la escena 3, cada escena lleva `enlace` y su voz **empieza** con
   el conector: `pero` (pero, sin embargo, aunque, solo que, en cambio, aun así), `por_eso` (por eso, así que,
   entonces, el resultado, de ahí que, la consecuencia) o `y` (y, además, también, encima, más aún). Nunca
   «y luego»; `y` como máximo en un tercio de los enlaces. El **giro** del hilo (beat `giro` en el digesto) es
   tu «pero» mayor.
   **Un `por_eso` respeta el tiempo**: la causa ocurre antes (o a la vez) que la consecuencia. «El Niño calentó
   el océano de junio a agosto» → «así que faltó lluvia de **enero a junio**» es falso (el efecto va antes que la
   causa) y el crítico lo bloquea. Mira los periodos de las dos tarjetas: si no encajan, reordena las escenas o usa `y`.
   **Nunca abras una escena con las palabras que cerraron la anterior**: si la escena 4 termina «¿Y en 2024?», la 5 no empieza «El resultado: en 2024…» (se oye repetido; el gate lo rechaza). La siguiente escena responde o avanza: «Solo 1 de cada 25…».
4. **Golpes.** Cada tarjeta lleva `golpe` (1–6 palabras, ≤ 40 caracteres): el re-gancho que aparece arriba
   mientras entra la tarjeta, en lenguaje llano y con la cifra si cabe («Cinco veces más cocaína», «1 de
   cada 3 no denuncia», «El doble de policías muertos»). Nunca el titular de la tarjeta ni parte de él. Una
   escena `tipo: "golpe"` (texto cinético a pantalla completa, voz 20–110 caracteres, con `pantalla` y
   `linea` como el gancho, y `verbo` de la oración que dice su pantalla) sirve para tres cosas: traducir la cifra de la tarjeta anterior a escala humana,
   pagar la promesa, o re-ganchar a mitad en medio y largo (con una frase propia, no una de «Frases ya usadas»). Nunca dos golpes
   seguidos, nunca en la escena 2, nunca para repetir la tarjeta.
   Otras dos escenas de texto, opcionales y con las mismas reglas de adyacencia (golpe, definición y adivina
   nunca van seguidas; `enlace` desde la escena 3):
   - `tipo: "definicion"` (≤ 1; 2 en largo): `termino` (≤ 3 palabras, ≤ 24 caracteres) y `definicion` (≤ 90
     caracteres, en lenguaje llano, sin siglas nuevas); la voz (30–160 caracteres) dice el término. Para el
     término que la cifra necesita y el espectador no leyó («Fase 3+ de la CIF», «anomalía ONI»).
     **La voz anuncia que viene un concepto antes de decir el término**, para que quien mira sepa que se va a
     explicar algo: «…Para entenderlo mejor: la CIF lo mide en fases, y la Fase 3 o más es crisis o peor.» ·
     «¿Qué es la anomalía ONI?…» · «Antes de seguir, un concepto: …» (formas; varía la pregunta que lleva al
     concepto respecto de «Frases ya usadas»). El gate lo exige
     (`para entender`, `para explicar`, `te explico`, `antes de seguir`, `un concepto`, `qué es`, `qué significa`,
     `qué quiere decir`, `para que quede claro`, `aclaremos`, `primero`, antes del término) y la pantalla pone el
     rótulo «Para entender» sobre el término.
     La línea `definicion` usa **las mismas palabras que la voz** (se escribe al ritmo de la voz: una palabra
     que la voz no dice queda sola en pantalla y el ritmo real, V10, avisa del hueco).
   - `tipo: "adivina"` (≤ 1, desde la escena 3): `pregunta` (≤ 70 caracteres, termina en «?»), `opciones` (3
     cadenas ≤ 14 caracteres con cifra: una es la del hilo, con respaldo o `calculo`; las otras dos son señuelos
     plausibles del mismo formato) y `correcta` (0–2). La voz (40–200): la pregunta **con las mismas palabras
     que `pregunta`** (en pantalla se escribe al ritmo de la voz; el gate rechaza una palabra que la voz no
     dice), las tres opciones, **una oración que pide pausar para responder** («Pausa el video y piénsalo.»,
     «Detén el video y responde.»; el gate la exige entre las opciones y la respuesta y la pantalla pone la píldora
     «Pausa y responde») y, en una oración final aparte, la respuesta (la última cifra que dice la voz es la
     correcta); el script mete 2 s de silencio antes de esa oración. Abre un bucle a mitad del video («¿Cuántas?
     ¿Ocho, quince o veintitrés? Pausa y piénsalo. … Veintitrés»).
   - `tipo: "mapa"` (≤ 1; cuenta como tarjeta): la tarjeta de mapa del hilo a pantalla completa, sin columna de
     leyenda: `tuit` de esa tarjeta, `golpe`, `enlace` y `texto` (40–230). Los 22 departamentos se encienden uno a
     uno, el destacado entra al final con su rótulo y cada valor que diga la voz ilumina su departamento: nombra
     2–3 departamentos con su cifra. Esa tarjeta no va además como `tarjeta`. Úsala en medio y largo.
   - `tipo: "ranking"` (≤ 1; cuenta como tarjeta): cuenta regresiva a pantalla completa de una tarjeta barras-h o
     mapa (`tuit`, `golpe`, `enlace`, `texto` 40–230, `top` 3–6 (5), `orden` desc|asc). Los puestos entran del
     último al primero cuando la voz dice su valor: nombra en la voz al menos el primero con su cifra («…y el que
     más paga: México, cinco punto nueve»), mejor dos o tres, del menor al mayor. Esa tarjeta no va además como
     `tarjeta` ni como `mapa`. Es un re-gancho a mitad («¿quién está primero?»).
   - `tipo: "tiempo"` (≤ 1; cuenta como tarjeta): línea de tiempo a pantalla completa de una tarjeta antes-despues
     o linea (`tuit`, `golpe`, `enlace`, `texto` 40–230): el marcador recorre los años y el valor de cada punto
     salta cuando la voz lo dice; di las cifras en el orden del tiempo y termina en el último (el destacado).
   - `tipo: "escala"` (≤ 1; sin tuit, o `tuit` de una waffle o pictograma): la escala humana con figuras:
     `de_cada: [K, N]` (enteros, N entre 2 y 100), `etiqueta` (≤ 40, «personas en Fase 3+»), `calculo` que
     respalde «K de cada N» (como el «1 de cada 4» del digesto), `enlace`, `golpe` opcional y `texto` (30–170) que
     DICE «K de cada N». Las N figuras aparecen y las K se encienden al decirlo. Para la cifra que el espectador
     tiene que sentir en su cuerpo; no la uses dos veces ni junto a una waffle de lo mismo.
   - `tipo: "explica"` (≤ 1; 2 en largo; cuenta como escena de texto; nunca dos seguidas): una **animación que
     explica el mecanismo** del fenómeno, no los datos: cómo se forma una cola en un anillo de tránsito, por qué la
     sequía termina en hambre, cómo crece una deuda. **Primero nombra el `mecanismo`**, lo que HACE el fenómeno y no
     su tema: `cadena` (causa → efecto lineal) · `ciclo` (se retroalimenta) · `balance` (entra contra sale) · `onda`
     (se propaga o se contagia) · `embudo` (etapas que filtran) · `proporcion` (una división: si el denominador no
     crece…) · `umbral` (se acumula hasta un límite) · `cronologia` (eventos con fecha). Campos: `mecanismo`, `brief`
     **siempre** (40–400 caracteres: qué se ve y cómo se mueve; si reutilizas, el crítico lo usa para ver si encaja),
     `animacion` (id del digesto **con ese mismo mecanismo** y que no esté en «Animaciones bloqueadas») o `null` (el
     animador la escribe a medida y la guarda como plantilla para otros videos). **Pedir una nueva es lo normal**
     cuando la biblioteca no tiene ese mecanismo; nunca fuerces el fenómeno en cajas de `cadena` porque es la que hay
     (el gate rechaza un mecanismo distinto del de la animación). `titulo` (≤ 6 palabras, ≤ 40; va arriba como golpe), `pasos`
     (2–6, ≤ 28 caracteres, sin cifras salvo con respaldo), `enlace` y `texto` (40–230) que **dice cada paso** (cada
     uno entra cuando la voz lo dice; el gate lo comprueba). Va bien justo después de una `definicion` o antes del
     giro («¿por qué pasa esto?»). Cada afirmación causal es de conocimiento general o del hilo y **no contradice
     `no_afirma`**: «uno de los factores», nunca «la causa» si el hilo no lo afirma. Ejemplo:
     `{"tipo": "explica", "enlace": "por_eso", "mecanismo": "onda", "animacion": "onda-frenado", "brief": "Una fila
     de carros en un carril; el primero frena y la luz roja de frenado viaja hacia atrás de carro en carro, más
     rápido que los carros, hasta que la fila queda quieta.", "titulo": "Cómo nace una cola", "pasos": ["Más carros
     por kilómetro", "Menos espacio entre ellos", "Un frenazo se contagia", "Se forma la cola"], "texto": "Entonces,
     ¿cómo nace una cola? Uno de los factores: más carros por kilómetro, menos espacio entre ellos, un frenazo se
     contagia y se forma la cola."}`. Otros: «cómo se confirma una muerte» es un `embudo` (sospechas que se
     descartan), «por qué la ocupación no cede» una `proporcion` (presos ÷ espacios), «por qué la sequía da
     hambre» una `cadena`.
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
   golpes son los cambios visuales que sostienen la atención. Si la tarjeta tiene años en su eje (el digesto
   los lista como serie o partes), nombrarlos en la voz también mueve la pantalla: esa columna late. Para un
   silencio que ayude (el giro del gancho: «…de su historia. [pausa] Pero con el hambre…»; antes de la cifra del
   pago) escribe `[pausa]` (0.6 s) o `[pausa larga]` (1.2 s) tras un punto o justo antes de un «pero»: ≤ 1 por
   escena y ≤ 3 por video (V9). No cuentan como caracteres.
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
9. **Cierre (dos pantallas, una voz).** `texto` = 1–2 frases de conclusión (**≥ 3 s de voz**, ≈ 46 caracteres:
   mientras se dicen se ve la pantalla «Conclusiones» con el `resumen`) + **la frase final** (`final`, la última de
   `texto`, ≤ 14 palabras): cuando la voz llega a ella, las conclusiones salen y queda sola en grande con «Sígueme en».
   **Las cifras van en las conclusiones; la frase final dice su consecuencia** (usuario, 2026-10-24: «terminar con un
   dato no es un buen punch, la consecuencia de un dato sí»). **Lo normal es un remate de consecuencia**
   (`tipo: "remate"`, `forma: "consecuencia"`): lo que la cifra le hace a quien la vive, con **gente como sujeto** y un
   **verbo de lo que les pasa** en pasado o presente: «Este año, 34 familias ya enterraron a un hijo por
   desnutrición.» (no «De cada 7 niños muertos, 6 no tenían 2 años.»). Declara `consecuencia` {`mecanismo`: quien,
   perdida, reloj, despues o espera; `quien` y `verbo` tal cual en la frase}. A lo más una cifra (cuántos lo viven,
   del hilo), nunca la del gancho; sin fatalismo («no hay nada que hacer») ni futuro que la fuente no proyecta
   («perderán»); sin adverbios que lloren por el espectador («lamentablemente», «trágicamente»): el hecho pesa solo. A
   veces, `pendiente` o `quien_decide`. **A veces, una pregunta** (`tipo: "pregunta"`; nunca si el video
   anterior cerró con pregunta, lo dice «Cierres recientes» del digesto): sobre el sistema (elegir, prediccion, decidir,
   lugar, porque, dato_faltante) y, solo en temas que no exponen, sobre la experiencia. Catálogo, ejemplos y reglas
   F1–F8 en `referencias/cierres.md`: la frase nombra el fenómeno del video (nada de analogías de otro ámbito: los
   cuartos de una casa no son los espacios de una cárcel), sin cebo («comenta», «etiqueta») y, en un tema sensible,
   sin tocar la casa, la familia ni la intimidad de quien mira. La forma (salvo consecuencia) no repite la de los últimos videos y el mecanismo de consecuencia no repite el del último. `resumen` = 2–3
   líneas cortas (≤ 40 caracteres): las conclusiones del video, que no repiten un titular. El cierre **no menciona** fuentes, el hilo, la
   marca ni «sígueme»: «Sígueme en» con TikTok, Instagram, Facebook, YouTube y X lo pone la pantalla, sin voz.
10. **Captions (uno por plataforma; el mismo video se sube a las cuatro).** `tiktok`: 1–3 líneas con el gancho y
    la cifra más fuerte + 2–4 hashtags (#Guatemala #DatosGT y el tema). `instagram`: el gancho en 1–2 líneas, una
    línea que invita a guardar o compartir («Guárdalo para…») y 3–5 hashtags al final. `facebook`: el gancho, 3–6
    viñetas «▸» con las cifras del video y una línea de fuentes («Fuentes: …», tomadas de las tarjetas). `shorts`:
    la primera línea es el **título de YouTube** (≤ 100 caracteres, con la cifra; se lee en buscadores), luego 1–2
    líneas de descripción y `#Shorts` con 1–2 hashtags más. Sus números también pasan por V2.
    **Los captions no adelantan el pago**: se leen mientras corre el video, así que abren la misma brecha que la
    promesa («¿Qué año tuvo más hambre? La respuesta llega al final del video.»; nunca «te lo digo al final»: el
    gate lo rechaza), nunca la respuesta. Las viñetas de Facebook, que
    se leen tras «ver más», sí pueden darla.

11. **Icono (opcional).** En gancho, golpe y definición puedes poner `icono: "<id>"` de la biblioteca fija
    (`design/iconos/`; el digesto lista los ids con sus palabras clave): un trazo monocromo que se dibuja sobre la
    cifra. Solo si nombra el tema de la cifra («cloud-rain» en una cifra de lluvia, «wheat» en una de maíz); nunca
    decorativo, ≤ 1 por escena y en como mucho la mitad de las escenas de texto. Un id fuera del catálogo es falta V1.

## Presupuesto y gate

| Duración | Objetivo | Escenas (más el cierre) | Voz |
|---|---|---|---|
| `corto` | 60 s ±10 % | gancho + 3–4 tarjetas + 1–2 golpes | ≈ 810 caracteres |
| `medio` (por defecto) | 120 s ±10 % | gancho + 6–8 tarjetas + 2–4 golpes | ≈ 1,675 |
| `largo` | 240 s ±10 % | gancho + 11–15 tarjetas + 3–6 golpes | ≈ 3,437 |
| `prueba` (fixture) | 45 s ±10 % | gancho + 2–3 tarjetas + 0–1 golpes | ≈ 599 |

La voz total (con cifras en palabras, ≈ 1.4× el texto en dígitos) debe caer en ±10 % del objetivo; el gate
(V4) imprime la duración estimada. Si te pasas, quita una tarjeta o acorta frases; no aceleres a costa de la
claridad. V9 comprueba: escena 1 = el gancho elegido (familia, visual y R1–R10 de `referencias/ganchos.md`); escena 2 = T1; enlaces desde la 3
con su conector al inicio y `y` ≤ ⌊n/3⌋; golpe en cada tarjeta, ≤ 6 palabras y distinto del titular; nunca
dos golpes seguidos; `verbo` del gancho y de cada golpe dentro de la oración que dice su pantalla; promesa literal en 1–2 y pago en el último tercio; `calculo` legible que da el número
escrito; ritmo ≤ 6 s. Si la directiva trae faltas del crítico o fallos del workflow, corrige **solo** eso y
vuelve a pasar el gate.
