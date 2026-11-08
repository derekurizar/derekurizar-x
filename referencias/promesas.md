# Promesas de /video, /historia y /explica: intriga desde la historia, nunca anunciando el video

La **promesa** es la oración de la escena 1 o 2 que da una razón concreta para quedarse; la **bisagra** es el segundo
enganche, justo antes del giro, para que el interés no se caiga a mitad. Esta guía dice cómo escribirlas. La leen los
guionistas (`referencias/roles/video-guionista.md` regla 2, `historia-guionista.md`, `explica-guionista.md`) y el
agente `video-gancho` (`promesa_sugerida` + `forma_sugerida`); la juzga el crítico (C2, C6, C11 y sus modos). Lo que
se puede medir vive en `scripts/video.py guion --check` (**P1–P4**), que también corre dentro de `historia.py` y
`explica.py`.

**Por qué existe** (2026-11-02): de las 16 piezas narradas hasta entonces, 12 prometían anunciando el propio video:

| Pieza | Promesa |
|---|---|
| Madres niñas | «Algunas de esas madres tenían 12 años o menos: la cifra viene después.» |
| Sequía | «Al final te digo qué año tuvo más hambre.» |
| Tráfico | «Quédate hasta el final y sabrás cuántas vidas cobra el tránsito.» |
| Cárceles | «Hay un penal todavía más lleno que Pavón, y vas a ver cuál.» |
| Desnutrición | «Antes del cierre verás cuántas muertes siguen sin dictamen.» |
| Cajita Feliz | «Lo que falta saber es a quién le da el crédito la corporación.» |
| Incaparina | «El último capítulo cuenta hasta dónde llegó su bebida.» |
| Amatitlán | «Al final sabrás si la justicia ya cerró el caso de ese líquido.» |
| Sputnik V | «Vas a ver dónde terminaron muchas de esas vacunas.» |
| Café soluble | «Al final vas a ver qué nombre quedó en el frasco.» |
| Duolingo | «Ese examen va a volver al final.» |
| Volcán 2018 | «Falta saber si alguien respondió ante un juez por la orden que no llegó.» |

Las cuatro que no lo hacían eran las mejores: «Décadas después, la marca llegaría a Estados Unidos, donde ya la
esperaban» (Campero) y «Más de un siglo después, un rival de afuera vendría a pelearle el mercado» (Gallo) adelantan
**que** algo pasará sin decir **qué**; «cuánta gente quedó bajo la ceniza es una cuenta que nunca cerró» (Volcán hora a
hora) deja un secreto. El molde venía de las guías: sus ejemplos eran «Quédate hasta el final y sabrás…», «Al final vas
a ver…», «Espera al final…».

**Decisión del usuario** (2026-11-02): «la manera en como de template dice siempre "va a volver al final"… tiene que ser
más emocionante y no igual en todos los videos». Elegido: **fuera del todo** el anuncio explícito («al final»,
«quédate», «vas a ver», «más adelante»); la intriga sale de la historia misma. Y un **segundo enganche a mitad**,
antes del giro, en todos los flujos con promesa.

## 1. Lo que dice la evidencia

| Hallazgo | Fuerza | Fuente |
|---|---|---|
| La curiosidad es la respuesta a un **hueco específico** de información: una pregunta concreta, ya activada en quien escucha y que siente que se puede contestar. «Hay más» no abre ningún hueco | A (teoría con experimentos) | Loewenstein 1994, *Psychological Bulletin*; [Golman y Loewenstein, «Information Gaps»](https://www.cmu.edu/dietrich/sds/docs/golman/Information%20Gaps--Golman%20and%20Loewenstein.pdf); [Golman y Loewenstein, curiosidad](https://www.cmu.edu/dietrich/sds/docs/golman/golman_loewenstein_curiosity.pdf) |
| El orden de los hechos decide la emoción: **suspenso** (sabemos lo que está en juego y no cómo termina), **curiosidad** (sabemos el resultado y no cómo se llegó) o **sorpresa** (falta un dato que aparece después). La versión con suspenso gustó más; la que no resolvía, mucho menos | B (experimentos de lectura) | [Brewer y Lichtenstein 1981](https://sites.ualberta.ca/~dmiall/694Empirical/Brewer_Lichtenstein_1981.htm); Brewer y Lichtenstein 1982, «Stories are to entertain» |
| Adelantar **que** algo pasará no arruina la historia y a veces la mejora; las réplicas son mixtas: un spoiler del **qué** sí baja el suspenso | B, discutido | [Leavitt y Christenfeld 2011](https://www.psychologicalscience.org/news/releases/spoiler-alert-stories-are-not-spoiled-byspoilers.html); [réplicas](https://scholarworks.uark.edu/psycuht/10) |
| Un plazo (el «reloj») concentra la tensión también en no ficción | C (práctica de oficio) | [Killer Nashville](https://www.killernashville.com/articles/literary-alchemy-the-ticking-clock); [Mobile Movie Making](https://mobilemoviemaking.com/?p=8425) |
| Repetir «espera al final» entrena al público a ignorarlo; lo que se recomienda es **rotar** el tipo de intriga y **apilar** un segundo enganche a mitad. Ninguna fuente mide esto con un estudio controlado | C (blogs de creadores) | [Socialync](https://www.socialync.io/blog/open-loops-in-content-2026); [Autonolab, «loop ladder»](https://blog.autonolab.com/blog/2025-10-02-the-loop-ladder-building-curiosity-that-compounds/); [SocialKit](https://socialk.it/en/blog/tiktok-retention-watch-time-guide) |
| Meta baja la distribución de lo que pide la interacción de forma explícita («comenta SÍ»). Pedir que se queden es un pedido del mismo tipo: es una analogía, no un estudio | analogía | [Meta, cebo de interacción](https://transparency.meta.com/features/approach-to-ranking/content-distribution-guidelines/engagement-bait/) |

**De aquí salen cinco reglas.** La promesa nombra una pregunta concreta de la historia, no del video. Puede adelantar
**que** algo pasa, nunca **qué** revela (H13). Siempre se paga. La forma rota entre piezas. Y un segundo enganche
re-abre el interés justo antes del giro.

## 2. El catálogo de formas

Los ejemplos muestran **la forma, no el texto**: si se copian, todas las piezas vuelven a sonar igual.

| `forma` | Mecanismo | Forma del ejemplo | Cuándo |
|---|---|---|---|
| `pregunta` | pregunta dramática concreta sobre la historia (Loewenstein) | «¿Cómo pasa un niño sin asiento para un examen a dueño del examen?» | hay un contraste fuerte entre el inicio y el final |
| `presagio` | ironía dramática: el espectador sabe que algo viene y el protagonista no (curiosidad de Brewer) | «Todavía no sabía que ese examen iba a perseguirlo veinte años.» · «Décadas después, la marca llegaría a Estados Unidos, donde ya la esperaban.» | historias con un desenlace que cambia el sentido del inicio |
| `apuesta` | lo que estaba en juego, lo que se perdía (suspenso) | «Sin ese papel, no había universidad.» · «Si el agua no bajaba, la cosecha entera se perdía.» | el protagonista o la gente arriesga algo concreto |
| `reloj` | un plazo o una cuenta atrás (suspenso) | «Le quedaban tres semanas para encontrar un asiento.» | hay una fecha límite verificada |
| `contradiccion` | dos hechos que no caben juntos | «La app que nació para ser gratis hoy cotiza en bolsa.» · «Ana no ahorró más: solo empezó antes.» | datos y explicadores: la cifra choca con lo que se cree |
| `secreto` | algo que nunca se supo, que alguien calló o que la cifra esconde | «Hay una cifra de esta historia que nadie ha dicho.» · «Un vecino paga todavía más.» | un hilo sin respuesta, una cifra oculta, una disputa |

**Cómo se escribe:**
- **Concreta**: nombra a alguien, un objeto, un lugar o una cifra de la historia («ese examen», «la planta», «el
  galón»); «algo increíble» no abre ningún hueco.
- **Emocional**: lo que una persona gana, pierde o no sabe pesa más que lo que el video «va a mostrar».
- **Honesta**: presagio y contradicción solo con hechos verificados, sin adelantar la revelación (H13 en
  /historia) ni afirmar lo que `no_afirma` prohíbe.
- **Una oración propia con verbo** (V9): no empieza con «Y», «Pero» ni «Así que» suelto.

**Lo que ya no vale (P2):** cualquier frase que hable del video en lugar de la historia: «al final», «hasta el
final», «antes del cierre», «más adelante», «vas a ver», «verás», «sabrás», «quédate», «espera», «no te vayas»,
«te digo/cuento/explico», «en este video», «va a volver», «viene después», «falta saber», «el último capítulo»,
«sigue viendo». Tampoco en los captions (V5).

## 3. La bisagra (el segundo enganche)

- Va **justo antes del giro**: al final de la escena anterior o al abrir la escena del giro (`giro: true` en
  /historia y /explica; en /video, la tarjeta del beat giro). Sin giro, entre el 35 y el 70 % de las escenas.
- Usa **otra forma** que la promesa. Si la promesa fue una pregunta, la bisagra puede ser un presagio («Nadie en la
  familia imaginaba quién tocaría la puerta»), una apuesta o un reloj.
- La paga **el giro o una escena posterior** (`bisagra.pago`).
- Va **dentro de la narración de corrido** del acto donde cae (H15 y V17: literal en la voz).
- 10–90 caracteres. Puede empezar con «Pero» si es el giro mismo; con otro conector suelto, no.

## 4. Reglas del gate

| Regla | Qué comprueba |
|---|---|
| **P1** | `promesa.forma` y `bisagra.forma` están en el catálogo y no son la misma |
| **P2** | ni la promesa ni la bisagra anuncian el video; V5 aplica lo mismo a los captions |
| **P3** | la forma de la promesa no repite la de las últimas 2 piezas narradas (videos, historias y explicaciones juntos). Las piezas viejas sin forma cuya promesa anunciaba el video cuentan como «anuncio», que ya no es forma válida |
| **P4** | `bisagra {texto, forma, en, pago}`: literal en la voz de `en`; `en` justo antes del giro (o a mitad sin giro) y distinto de `promesa.en`; `pago` en el giro o después |
| **P2 en /serie** | ni la promesa ni el cierre anuncian «la próxima parte» o «el siguiente video»: el puente es una pregunta de la historia (F9 lo vigila en la voz) |
| **P5** | la escena 2 (después del gancho) dura ≤ 12 s estimados; si pasa de 8 s es aviso, y la imagen cambia o entra un golpe a los 3–4 s. Medido el 2026-11-03 (/analyze-improve): ahí se pierden 9–24 puntos en 14 de 20 piezas, el doble en las escenas quietas y largas. La web coincide: la caída de 5–15 s se corrige con un re-gancho por beat (`referencias/analisis/benchmarks.md`). `/sabias` está exento |

Además siguen V9 (promesa literal en la escena 1 o 2, pago en el último tercio), H14 en /historia y E12 en /explica
(la escena del pago cuenta la revelación prometida).

`guion.json`:

```json
"promesa": {"texto": "…", "forma": "pregunta", "en": 2, "pago": 11, "revela": 4},
"bisagra": {"texto": "…", "forma": "presagio", "en": 8, "pago": 9}
```

`memoria.py` guarda `promesa_forma`, `bisagra` y `bisagra_forma` en `frases`; el digesto los muestra en «Promesas
recientes (P3)» y en «Frases ya usadas» (C11).
