# /serie: un tema en 3–5 partes

Las series convierten vistas en seguidores: quien ve la Parte 1 y quiere la 2 sigue la cuenta. `/serie` cuenta un tema
en 3–5 partes de ≈ 90 s con **una sola investigación** y un **plan versionado**, sobre uno de dos motores:

| Motor | Qué parte la serie | La parte | Fixture |
|---|---|---|---|
| `/historia` | los periodos de la historia (cada parte, un tramo de tiempo) | formato `historia-serie`: 75–110 s, 190–250 palabras, 1–4 hilos, ≥ 4 hechos | `sesiones/_fixture_serie` (La Espiga en 3 partes) · `make serie-fixture` |
| `/explica` (temario) | un mecanismo por parte | formato `explica-serie`: 90 s (70–110), 190–250 palabras | `sesiones/_fixture_serie_explica` (el interés en 3 partes) · `make serie-explica-fixture` |

## Archivos

- `scripts/serie.py`: `preparar`, `plan --check [--aprobar]`, `cobertura --check`, `parte`, `digesto`, `estado`,
  `guion-aprobado`, `entregar-parte`, `--revisar` (M16) y `revisar_parte` (SE4–SE9, que llaman `historia.py` y
  `explica.py` en `guion --check`).
- `series/<fecha>-<slug>/serie.json` (el estado, versionado: cada cambio de plan sube `version` y guarda las partes de ese
  momento en `historial`) y `serie.md` (el orden, los captions, qué publicar y qué fijar). Los videos de cada parte van
  en `series/<fecha>-<slug>/parte-N/` (los mp4, fuera de git).
- Trabajo: `sesiones/serie-<slug>/` (la investigación compartida) y `sesiones/serie-<slug>/parte-N/` (cada parte).
- Registro: `memoria/series.json` (`memoria.py --serie`, M16 en `validate.py`).

## El plan (`encuadre.json → serie.partes`)

```json
{"serie": {"partes": [
  {"n": 1, "titulo": "El primer horno", "pregunta": "¿Cómo llenó Xela de pan un solo horno?",
   "periodo": {"desde": "1952", "hasta": "1975"},
   "actos": [3 × {n, nombre, titulo, periodo, que_cuenta, termina_en}], "espina": {detonante, punto_medio, climax, resolucion},
   "hilos": [{"id": "p1h1", "pregunta": "…", "eje": "ori"}], "revelaciones": ["…"],
   "puente": "¿Qué le pasaría a La Espiga cuando la tierra tembló?"}]}}
```

En el temario (`/explica`), cada parte lleva `mecanismo`, `mecanismo_frase`, `intuicion` y `ejes` (los de la
investigación que la sostienen), en lugar de `periodo`, `actos`, `espina` e `hilos`.

## Gates

| Gate | Dónde | Qué comprueba |
|---|---|---|
| SE1 | `serie.py plan --check` | 3–5 partes en orden, cada una con título (≤ 6 palabras), pregunta, periodo (o mecanismo con su frase, intuición y ejes), actos y espina (historia), 1–4 hilos sin ids repetidos entre partes, 1–3 revelaciones |
| SE2 | `serie.py plan --check` | la cadena de puentes: el puente de la parte N comparte raíz con la pregunta de la N+1; la última no tiene puente; ningún puente dice un número de una revelación posterior; los periodos van en orden y no se pisan |
| SE3 | `serie.py cobertura --check` | ≥ 4 hechos publicables por parte en su periodo (historia); ≥ 2 afirmaciones o cifras por parte en sus ejes (temario) |
| SE4 | `guion --check` de la parte | cada parte se entiende sola: sin «como vimos», «en la parte anterior», «en el video anterior» |
| SE5 | `guion --check` | paleta y música de la serie |
| SE6 | `guion --check` | partes 1…M−1: cierre forma `puente` cuya frase final deja la pregunta del puente; la última: sin puente y sin hilos que pasen |
| SE7 | `guion --check` | 75–110 s estimados (< 61 s falla: TikTok Creator Rewards; 61–75, aviso); el video real además pasa el piso de 61 s |
| SE8 | `guion --check` | captions de TikTok, Instagram y Facebook que abren con «Serie · Parte N de M: <título>»; título de Shorts con «(N/M)»; en las partes 2…M, esos tres captions dicen que la Parte 1 está fijada en el perfil |
| SE9 | `guion --check` | partes 1…M−1: `cierre.invitacion`, la última oración de la voz (después de la frase final): pide seguir la cuenta («Sígueme»), nombra la parte siguiente en palabras («en la segunda parte») y dice qué cuenta (una raíz de su título o su pregunta); ≤ 18 palabras, sin cifras, sin cebo; la última parte no lleva |
| M16 | `validate.py`, `serie.py --revisar` | `memoria/series.json` y cada `serie.json`: campos, 3–5 partes en orden, estados conocidos, entregada ⇒ `guion.json` |

Además:
- H17 acepta `pasa_a: N+1` en un hilo que sigue abierto (solo en una parte que no es la última).
- F1 acepta la forma `puente` solo en una parte de serie.
- F9 y P2 rechazan «en la próxima parte» en la frase final y en la promesa; la invitación va aparte, en
  `cierre.invitacion` (no entra en `cierre.texto` ni en la narración, ni en el tope de 160 caracteres del cierre).

Las partes de una serie no llevan tomas de video (retiradas el 2026-11-06: muchas veces sin coherencia con lo que se narra; TM0 las rechaza).

## Modo caso (decisión del usuario, 2026-11-06)

`/serie <tema> 7 caso` (`serie.py preparar … --partes 7 --caso`) cuenta un caso complejo **por temas**: de 3 a 8 partes de ≈ 130 s (115–150), con el formato `historia-caso` de 290–350 palabras y al menos 8 hechos por parte.

El editor escribe:
- `serie.columna`: los temas en orden.
- En cada parte, `tema`, `hechos` (los ids de hechos, cifras y citas que cuenta esa parte) y `obligatorio`.
- `serie.fuera`: `{id: motivo}` para lo que no entra.

Cómo filtra cada parte: entra lo que se le repartió aunque se haya revelado después (el mecanismo de una red se supo en el juicio), y queda fuera lo repartido a una parte siguiente. Los periodos pueden pisarse. Una familia de gancho puede volver a 3 partes de distancia.

| Gate | Qué pide |
|---|---|
| SE10 | Inventario: ≥ 85 % de lo publicable repartido o con motivo; ≥ 8 hechos por parte; un id va a una sola parte. |
| SE11 | Columna: cada parte tiene un tema de la columna y cada tema lo cubre al menos una parte. |
| SE12 | Densidad: la parte cita ≥ 60 % de sus hechos repartidos y todos los `obligatorio`; no usa lo de las partes siguientes. |

## El resumen de la última parte (SE14, decisión del usuario, 2026-11-07)

La última parte de **toda** serie (caso, historia o explica) lleva un resumen de la serie entera: simple, para recordar
lo que pasó, y con impacto (termina en lo que más pesa).

- **Una escena** con `resumen_serie: true` en el acto 3, antes de la última cita o del cierre. Lo normal es una `explica`
  con la animación `cronologia`: los momentos se encienden cuando la voz los dice, como «2015 · Las escuchas».
- **20–30 s de voz** (300–480 caracteres): una oración por momento, en orden, abierta con un conector («Así fue todo.»).
- **Nada nuevo:** sus `hechos` son ids que ya contó alguna parte (o esta misma), de ≥ 5 partes anteriores (o de todas,
  si hay menos). Los alegatos se atribuyen igual que en el resto del video («para la acusación…», H4).
- **Fuera de SE13** (repetir es su trabajo), de V1 (no cuenta como explica) y del aviso de flashback.
- **Duración:** sus segundos se suman al límite de la parte: +30 s en SE7 y en H5/V4, hasta 180 s (el tope de Shorts).
- Primera vez: La Línea, Parte 7 (147 → 172 s).

## En pantalla

- Chip «Parte N de M» en el acento desde el cuadro 0 del gancho (`V.chip`).
- En la pantalla final, sobre «Sígueme en»: «Parte N+1 · <título>» (`video/cierre.html`, `escenas.json → serie`), que
  entra cuando la voz empieza la invitación.
- En las partes 2…M, debajo: «Empieza por la Parte 1 · fijada en mi perfil» (solo texto; la voz no lo dice: SE4).

## La invitación (decisión del usuario, 2026-11-05)

Al terminar cada parte que no es la última, después de la pregunta del puente, la voz invita a seguir la cuenta y dice
qué cuenta la parte siguiente: «Sígueme: en la segunda parte te cuento cómo sobrevivió La Espiga al terremoto.» La
frase final sigue siendo el puente (la pregunta queda abierta); la invitación es la consecuencia práctica: para la
respuesta, sigue la cuenta. Nunca adelanta una cifra ni una revelación de la parte siguiente.

## Publicación

La parte N se publica cuando la N+1 ya tiene el guion aprobado (`serie.py guion-aprobado`): así el puente siempre tiene
respuesta en camino. Se fija la Parte 1 en el perfil y se arma una playlist (YouTube) o lista (TikTok) con las partes
en orden. `serie.md` dice qué parte ya se puede publicar. Desde la Parte 2, el caption y la pantalla final mandan a
la Parte 1 fijada.
