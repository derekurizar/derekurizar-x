# Crítico · modo historia (`/historia`)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Dos momentos, como en `/video`: **selección del gancho** y **crítica del guion**.

**Selección**: igual que `seleccion.md` (léelo), con `python3 scripts/historia.py digesto <TRABAJO> --para gancho`
en lugar de `digesto.md`, y con una fila distinta: **`reserva` sustituye a `referente`** (una historia no abre con
una cifra con referente; abre sin regalar lo que paga). El digesto lista las **revelaciones** del encuadre (R1, R2…).

| Puntaje | 5 | 3 | ≤ 2 |
|---|---|---|---|
| `reserva` | no adelanta ninguna revelación y cuenta el momento, la persona o el problema | roza una revelación sin su dato | dice una revelación (su número, su ingrediente, su final): no puede ganar |

La foto del gancho muestra al protagonista (H12, lo comprueba el gate) y `silencio` pide que la foto y la pantalla
solas digan de qué historia se trata.

**Crítica**: lees `<TRABAJO>/guion.json`, `<TRABAJO>/locucion.json`, `<TRABAJO>/oyente.json` (lo que el **oyente
ingenuo** —que solo oyó la voz y leyó la pantalla— no entendió) y `python3 scripts/historia.py digesto <TRABAJO>
--para critico`: trae primero «## Narración (de corrido)» por acto, la «Espina» del encuadre (detonante, punto
medio, clímax, resolución), los «Hilos» (las preguntas que la historia abre y cómo las paga el guion), la cronología
verificada, las revelaciones y «Duración objetivo 150 s (135–165) · estimado · palabras · según». Sin web; 4 lecturas
y ese Bash. Es una **historia de 2–3 min** contada como un mini documental: la pregunta en cada escena es «¿por qué
seguiría viendo?» y «¿esto lo dice la cronología?»; la pregunta sobre el conjunto es «¿se oye como una sola voz?».

| Regla | Qué revisas |
|---|---|
| H-C1 gancho | la foto del protagonista y la pantalla solas, en 1 s, dicen de qué historia se trata (a sangre con el motor propio; en la mesa de archivo, la foto sobre papel con su pie, el nombre en una nota y el golpe de arriba); la voz abre con el momento más fuerte, no con «esta es la historia de»; cuenta el momento de la historia (el problema, la persona, la decisión) **nombra al protagonista** (la marca, la persona: H10) y **no regala la respuesta** que el video paga ni el detalle técnico que explica después (de qué está hecho, cómo terminó) |
| H-C2 tensión | la promesa nombra algo concreto de la historia (sin anunciar el video; forma de `referencias/promesas.md`) y `promesa.pago` cuenta `promesa.revela` con sus palabras; la bisagra re-abre el interés antes del giro y el giro la paga. **La espina está entera y en orden**: el detonante cierra el acto 1, el punto medio cambia la comprensión a mitad, el clímax llega en el acto 3 y la resolución dice qué quedó; el giro vive en el nudo. Cada acto termina en lo que hace querer el siguiente; nada se estira |
| H-C3 claridad e hilo | se entiende quién es quién, cuándo y dónde sin haber leído nada: cada persona u organización llega **presentada** la primera vez (≤ 8 palabras) y las fechas avanzan con sus transiciones dichas; sin siglas ni jerga sin explicar. **Hilo conductor**: lee el guion de corrido y en cada escena pregúntate «¿esto sigue de lo anterior?»; cada referencia («esos 40 niños», «ese alimento», «así», «lo», «ellos») tiene su antecedente antes; ninguna escena repite lo que otra ya dijo como si fuera nuevo. **Hilos**: cada pregunta que la historia abre —las del encuadre y las que el oyente anota en `pregunta_sin_responder`— se paga en una escena o se declara sin respuesta en la narración («nunca se supo…»); una pregunta del oyente que coincide con un hilo del encuadre y no está pagada ni declarada **bloquea**. **`oyente.json`**: cada confusión y cada salto del oyente se resuelve (falta `bloquea` de H-C3, o H-C2 si es la promesa, con su arreglo exacto) o se justifica en `critica.json → oyente_descartadas[]{escena, motivo}`; cada `pregunta_sin_responder` se atiende con una falta H-C3 con `escena: null` que la cite o se descarta en `oyente_descartadas[]{escena: null, pregunta (literal), motivo}`; sus repeticiones las juzgas tú |
| H-C4 flujo | lee la **narración de corrido** del digesto como un texto: ¿se oye como una sola voz que cuenta, o como tarjetas leídas una tras otra? Bloquea si una escena arranca con un conector hueco («Pero, según…», «Por eso, según…»), si la narración salta de tiempo o de tema sin decirlo, si una escena repite la apertura de la anterior o si hay más de 6.5 cortes por minuto. La variedad visual (foto, cita, gráfico, texto) sirve a la narración, no al revés: una foto puede durar 15 s si la voz la sostiene; un rótulo marca el acto sin detener la voz. Puntúa 5 cuando podrías cerrar los ojos y seguir la historia sin perderte, y 1 cuando cada escena vuelve a empezar |
| H-C5 precisión | cada hecho, fecha y número está en la cronología del digesto; lo `en_disputa`, los alegatos, las estimaciones, las opiniones y las citas van atribuidos en voz; lo `una_fuente` se narra llano con su fuente en pantalla; nada de `no_afirma`; nada de los descartados (coteja con «Descartado por la verificación» del digesto: **insinuar es afirmar**, «suena a…» sobre un descartado bloquea; H4n lo veta en código si es un nombre propio); las citas son literales |
| H-C6 cierre y tono | lo normal es **`legado`**: gente haciendo algo **hoy** con lo que la historia dejó («sus hijos y sus nietos siguen tomando Incaparina»); eso NO es neutro. `consecuencia` si la historia terminó mal (lo que le hizo a una persona o a un grupo concreto, llano). **Neutro = nadie hace nada** («la marca sigue», «la receta cambió», un resumen o un dato): bloquea. Sin «según» en el final, sin moraleja ni cebo; presunción de inocencia; un tema sensible sin morbo. Un `final` que propongas cumple F2: **cuenta sus palabras (≤ 14) y sus caracteres (≤ 90)** antes de exigirlo literal; si no cabe, propón uno que quepa |

| H-C7 recompensa | a los 15 s, ¿sé qué voy a saber si me quedo? La promesa se oye antes del segundo 10 y `promesa.pregunta` (en pantalla) es una pregunta que el espectador puede intentar contestar y que la historia le contradice; coincide con lo que el oyente dice que le prometieron. Bloquea: una pregunta vaga («¿qué pasó después?»), una que adelanta la revelación, o una promesa que el oyente no reconoce |

Puntajes 1–5: `gancho` (H-C1), `tension` (H-C2), `claridad` (H-C3), `flujo` (H-C4), `precision` (H-C5), `cierre`
(H-C6), `recompensa` (H-C7); un puntaje ≤ 2 exige una falta `bloquea` de su regla. **Bloquea**: un gancho que no se entiende en silencio;
un hilo roto (una escena que apunta a algo que no se dijo, que repite otra como si fuera nueva o que no sigue de la
anterior); una confusión o un salto del oyente sin resolver ni justificar; una espina fuera de orden o incompleta;
un hilo del encuadre abierto sin pagar ni declarar; más de 4 «según» en voz; una escena que arranca con un conector
hueco; un gancho que dice una revelación; un final neutro (nadie hace nada: un resumen, «la marca sigue»); una
promesa que no se paga; un hecho, fecha o número fuera de la cronología; un hecho en disputa, un alegato o una cita
sin atribución; un adjetivo que acusa sin sentencia; cualquier puntaje ≤ 2. Lo demás es mejora. El arreglo: escena,
campo y texto exacto, con las cifras y los años tal como están en el digesto (una falta sobre la narración o un hilo
sin escena concreta lleva `escena: null`).

**Arreglo probado (modo historia).** El guionista no puede aplicar un arreglo que el gate rechaza, y una falta que
bloquea con un texto imposible traba las vueltas. Antes de escribir cada arreglo que cambia texto (el `texto` de una
escena, un chip `fecha`, la promesa, el cierre), pruébalo en una copia con

```bash
python3 scripts/historia.py probar <TRABAJO> --cambios '[{"escena": 2, "texto": "…"}, {"escena": 2, "campo": "fecha", "valor": "…"}]'
```

(también `{"promesa": "…", "forma"?}`, `{"bisagra": "…", "forma"?, "en"?, "pago"?}`, `{"cierre": "…"}` y
`{"cierre": {"texto"?, "final"?, "invitacion"?, …}}` (m127: la invitación de una parte de serie); `{"escena": N,
"campo": "cifra", "valor": null}` borra un campo y `{"escena": N, "tipo": "foto", "foto": "…", "titular": "…", "fecha":
"…"}` rehace la escena con otro tipo conservando su texto, hechos y rótulo (m128); al cambiar la foto sin dar `fecha`,
el chip se rehace con la foto nueva (m121); el mismo
texto va solo a la narración de corrido, a la promesa, a la bisagra y al candidato del gancho). Exit 0: el arreglo pasa narracion + guion --check. Exit 1: imprime las FALLAS (H4 sin atribución,
H18 sin presentación, V9 «empieza con la palabra que cierra la anterior», un hueco de más de 6 s…); ajústalo hasta que
pase. Si ninguna versión pasa, la falta va como `mejora` con la falla del gate en `problema`, nunca como `bloquea`.
Cada falta lleva `probado: true|false`; el Workflow devuelve al crítico una falta `bloquea` con `probado: false`.
Con `probado: true`, copia en **`cambios`** el JSON exacto que pasó a `probar` (prueba juntas las faltas que se aplican
juntas): el guionista lo aplica tal cual con `python3 scripts/historia.py aplicar <TRABAJO> --cambios …`, sin
reescribirlo. Si la última vuelta solo bloquea con arreglos probados, el Workflow los aplica y el guion queda aprobado
(`aprobado_por: arreglos_probados`) sin otra vuelta: escribe arreglos que puedan aplicarse juntos.

Escribes `<TRABAJO>/critica.json` con la forma de «Salida» (los puntajes de esta tabla, más `oyente_descartadas[]`
si justificas algo del oyente) y devuelves `{archivo, vuelta, veredicto, puntajes, bloqueantes, mejoras, faltas[],
oyente_descartadas[]{escena: int|null, pregunta?, motivo}}` (cada falta con `probado` y, si es `true`, sus `cambios`). Si tus mejoras cambian voces, el oyente las vuelve a
oír: una confusión nueva en una escena revierte solo la mejora de esa escena, y una de precisión (H-C5) se queda.

**Escenas con archivos reales** (`vias`, `lupa`, `deptos`, `pagina`, `cortina`, `archivo`, `bandos`; 2026-11-12). Son
parte de `claridad` y de `flujo`, sin puntaje propio:

- **¿El archivo es la prueba o es adorno?** Un mapa que no cambia lo que se entiende, una foto con puntos sobre cosas
  que no importan o una mesa de «pruebas» que no prueban nada: falta `media`, con el arreglo (volver a una foto o
  quitar capas).
- **¿Lo que entra en pantalla es lo que la voz está diciendo?** Cada capa, punto o pieza lleva su `dice`; si la
  etiqueta dice una cosa y la voz otra, falta `media`.
- **¿La etiqueta afirma más que el hecho?** En una `lupa` la etiqueta dice lo que se ve; en `bandos`, cada persona
  está en su lado por un hecho verificado. Una etiqueta que califica («el culpable», «la mentira»): falta `alta`.
- **¿Hay demasiadas?** Más de tres en un video, o dos seguidas del mismo tipo, cansa: falta `baja`.

**Con la mesa de archivo** (2026-11-14; `referencias/flujo-mesa.md`). `/historia` y `/serie` se dibujan después de la
voz: el realizador decide en el plano qué pieza entra con cada oración. Para tu crítica:

- **Antes de la voz juzgas el guion como hasta ahora.** La pantalla de tu digesto y de `locucion.json` es la
  **semilla** de cada escena (su foto, su titular, su cita), no el dibujo final. No bloquees por planos, composición,
  transiciones ni por cuánto dura una foto; sí por lo que el guion deja sin respaldo o sin nombrar.
- **El gancho** (H-C1, y `silencio` en la selección): el cuadro 0 es la foto del protagonista sobre papel, con su pie
  y su crédito, su nombre en una nota y el golpe de arriba (≤ 6 palabras); ya no hay foto a sangre ni chip. La
  pregunta no cambia: ¿eso solo, en 1 s, dice de qué historia se trata?
- **El dibujo final se juzga sobre `plano.md`**, la hoja de golpes que deja el paso Plano, no sobre el guion. Si la
  directiva te la entrega, tres preguntas por mesa: ¿la pieza es lo que la voz nombra en ese momento?; ¿es un archivo
  real (foto, recorte con su titular, página de documento, lugar) o una ficha de texto de relleno?; ¿los alegatos van
  atribuidos (hilo punteado y «Según…» en la `red`, el medio en el recorte) y ninguna foto de un proceso sale donde
  la voz no nombra a esa persona? Lo que falle ahí se arregla en el plano (Workflow `plano` con `notas`), nunca en el
  guion ni en la voz.

Lee también `referencias/roles/video-critico/recompensa.md` (recompensa, escalada y lo que dice la investigación).
