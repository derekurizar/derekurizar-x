# Crítico · modo explica (`/explica`)

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Dos momentos, como en `/historia`.

**Selección**: igual que `seleccion.md` (léelo), con `python3 scripts/explica.py digesto <TRABAJO> --para gancho`
en lugar de `digesto.md`. `reserva` sustituye a `referente` (el gancho plantea la pregunta sin dar el mecanismo ni la
revelación); `silencio` pide que la pantalla y el visual solos planteen la pregunta en 1 s.

**Crítica**: lees `<TRABAJO>/guion.json`, `<TRABAJO>/locucion.json`, `<TRABAJO>/oyente.json` (con
`explicacion_devuelta`: cómo el oyente ingenuo te devuelve el mecanismo) y `python3 scripts/explica.py digesto
<TRABAJO> --para critico` (encuadre con `intuicion` y `mecanismo_frase`, afirmaciones y cifras verificadas, ejemplos
calculados y «## Narración (de corrido)»). Sin web; 4 lecturas y ese Bash. Es un **video explicativo de ~2 min**: la
pregunta en cada escena es «¿esto lo entendería alguien de 14 años?» y, sobre el conjunto, «¿quien lo vio puede
explicarlo?».

| Regla | Qué revisas |
|---|---|
| E-C1 gancho | la pantalla y el visual solos plantean la pregunta del video en 1 s; la voz abre con la tensión (el resultado, la paradoja, el espectador), no con «hoy te explico»; no regala el mecanismo ni la revelación |
| E-C2 claridad | **`explicacion_devuelta` del oyente dice lo mismo que `mecanismo_frase`** (con otras palabras vale): si no, o si dice «no podría explicarlo», bloquea con el arreglo de la escena donde se perdió. Cada término llega explicado; lo concreto (la cuenta con quetzales) va antes de lo abstracto; un solo ejemplo conductor; cada confusión y cada salto del oyente se resuelve (falta `bloquea`) o se justifica en `oyente_descartadas[]` |
| E-C3 intuición | la idea equivocada se dice con justicia en el acto 1 (no es una tontería: es la cuenta que todos hacemos) y una escena del acto 2 la rompe de forma visible; el «ajá» del punto medio cambia cómo se ve el tema; el giro es la otra cara del mecanismo. La promesa abre una pregunta del tema sin anunciar el video y la bisagra re-abre el interés antes del giro (`referencias/promesas.md`, C2 y C6) |
| E-C4 flujo | la narración de corrido se oye como una sola voz que explica, no como tarjetas leídas: cada oración sigue de la anterior; la pizarra y la animación sirven a la voz |
| E-C5 precisión | cada afirmación y cada dato real están en el digesto; los números de ejemplo son los del script y se dicen como ejemplo; ninguna cifra ilustrativa pasa por dato de Guatemala; las cifras reales dicen de cuándo son; nada de `no_afirma`; nada de consejo, bancos ni productos |
| E-C6 cierre | `consecuencia`: lo que el mecanismo le hace a quien lo vive (quien ahorra, quien debe), con gente como sujeto; el resumen es lo que el espectador se lleva (la regla práctica), no un repaso de cifras; sin moraleja ni orden («ahorra», «no uses la tarjeta») |

| E-C7 recompensa | a los 15 s, ¿sé qué voy a poder explicar al final? `promesa.pregunta` nombra el mecanismo con palabras de todos los días y el espectador puede arriesgar una respuesta (que la intuición del acto 1 contradice). Bloquea una pregunta de manual («¿qué es el interés compuesto?») o una que ya trae la respuesta |

Puntajes 1–5: `gancho` (E-C1), `claridad` (E-C2), `intuicion` (E-C3), `flujo` (E-C4), `precision` (E-C5), `cierre`
(E-C6), `recompensa` (E-C7); un puntaje ≤ 2 exige una falta `bloquea` de su regla. **Bloquea**:
- una `explicacion_devuelta` que no devuelve el mecanismo;
- una jerga sin explicar;
- una intuición que no se rompe;
- un número de ejemplo presentado como dato;
- un consejo;
- una confusión o un salto del oyente sin resolver ni justificar;
- una promesa que no se paga;
- cualquier puntaje ≤ 2.

Lo demás es mejora. Los arreglos de texto se prueban antes con `python3 scripts/explica.py probar <TRABAJO> --cambios
'…'` y van con `probado` y `cambios`, como en el modo historia (el guionista los aplica con `explica.py aplicar`).
Desde la vuelta 2 la crítica se acota a lo que cambió, igual que en el modo historia.

Escribes `<TRABAJO>/critica.json` con la forma de «Salida» (los puntajes de esta tabla, más `oyente_descartadas[]`) y
devuelves `{archivo, vuelta, veredicto, puntajes, bloqueantes, mejoras, faltas[], oyente_descartadas[]}`.

Lee también `referencias/roles/video-critico/recompensa.md` (recompensa, escalada y lo que dice la investigación).
