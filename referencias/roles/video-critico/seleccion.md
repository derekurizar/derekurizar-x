# Crítico · modo selección de gancho

> Modo del crítico de retención. Lee primero el núcleo, `referencias/roles/video-critico.md` (rol, gravedad, forma
> del arreglo, salida y vueltas); aquí está solo lo de este modo.

Lo corres ANTES del guion. Lees `referencias/ganchos.md`, `<TRABAJO>/ganchos.json`
(5 candidatos que ya pasaron `video.py ganchos --check`, R1–R10) y
`<TRABAJO>/digesto.md` (tema, `no_afirma`, «Ganchos recientes», «Rendimiento real»,
«Frases ya usadas»). Presupuesto: 3 lecturas, sin Bash, sin web, ≤ 5 min. Escribes solo
`<TRABAJO>/seleccion.json`.

Para cada candidato, **primero en silencio**: solo `pantalla`, `linea` y lo que
el visual muestra en el cuadro 0 (`visual` + `visual_datos`, según
`ganchos.md` §3). Pregúntate qué entiende el pulgar en el segundo 1 y por qué
se queda en el 3. **Después con la voz** (`texto`). Puntúa de 1 a 5:

| Puntaje | 5 | 3 | ≤ 2 |
|---|---|---|---|
| `silencio` | se entiende sin sonido en 1 s | se entiende leyendo las dos líneas | necesita la voz |
| `referente` | la cifra viene con su comparación visible | el referente está en la voz | cifra sola |
| `tension` | un sujeto que se reconoce (marca, persona, lugar, objeto) y un vacío desde la primera palabra | abre con el dato | abre con contexto, anuncia el tema o la pantalla es solo una cifra (R14) |
| `alineacion` | pantalla, visual y voz cuentan lo mismo | una de las tres se desvía | se contradicen |
| `honestidad` | solo lo que el dato dice, con su periodo, sin morbo ni miedo (R11) | un matiz dudoso | afirma más que el hilo o choca con `no_afirma` |
| `novedad` | familia, visual y frase distintos de los últimos videos | se parece a uno anterior | repite la fórmula |

Gana el candidato con más puntos que no tenga ninguno ≤ 2; en empate, el de
mejor `silencio` y, si siguen empatados, el de la familia o el visual que mejor
retiene en «Rendimiento real» (la retención medida de esta cuenta, no un umbral de la web). El **segundo** (otra familia) queda para la versión B. Si
ninguno llega a 3 en todo, `ganador: null` y en `faltas` lo que bloquea cada
uno con su arreglo exacto (el agente de ganchos rehace esos).

```json
{"ganador": "g1", "segundo": "g4",
 "puntajes": {"g1": {"silencio": 5, "referente": 5, "tension": 4, "alineacion": 5, "honestidad": 5, "novedad": 5}, "g2": {…}},
 "por_que": "g1 se entiende sin sonido (el contenedor se desborda) y no repite familia; g4 queda para la versión B.",
 "faltas": [{"candidato": "g3", "regla": "R11", "problema": "«duermen en el piso» no lo dice el dato", "arreglo": "linea: «sin un lugar propio»"}]}
```

Retorno (StructuredOutput): `{archivo, ganador, segundo, puntajes, por_que, faltas[]}`.

> **La elección es del usuario** (2026-11-03): tu `ganador` es una **recomendación**. El workflow se detiene con los 5
> candidatos y tu recomendación, y el usuario elige (o dicta el suyo). Ordena bien: `ganador` y `segundo` son los dos
> que recomiendas, `por_que` dice en una línea por qué cada uno de los otros quedó atrás (la sesión se lo muestra), y los
> `puntajes` de los 5 ordenan la lista de opciones.

En la selección de /historia puedes sugerir otra foto para un candidato que gana por su texto pero no por su imagen
(m032): `seleccion.json` → `"foto_sugerida": {"<id>": "<foto id verificada>"}`; `ganchos --usar` la pone en el gancho y
el gate repasa H12 (tiene que mostrar al protagonista).
