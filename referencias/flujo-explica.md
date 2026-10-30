# Flujo `/explica` — índice

Un **concepto, un proceso o una regla explicado** en un video vertical (1080×1920, 30 fps) de **~2 min** (`medio`,
120 s; `corto` 60 s; `largo` 165 s) para TikTok, Reels y Shorts, más su 4:5 para el feed. El objetivo es uno: que quien lo
vea **pueda explicárselo a otro**. Misma línea que `/video` y `/historia`:
- voz El Faraon 4 con las cifras en palabras;
- música y efectos de los catálogos fijos;
- barra de progreso por acto, subtítulos y zona segura (V13);
- 9:16 + 4:5 y caption por plataforma;
- cierre con **«Sígueme en»**.

La publicación es manual. El hilo en modo explica (tarjetas, sin video) es `/hilo explica`.

```
preparar (explica.py: TRABAJO = sesiones/explica-<slug>/, duración, paleta provisional y música)
→ Workflow explica [explica-editor → encuadre.json (pregunta, intuicion, mecanismo + mecanismo_frase, leyenda, glosario,
                      personajes, ejemplos de la calculadora, anclas de Guatemala, revelaciones, 1–3 ejes) · gate E1
                    → explica-investigador por eje (en paralelo) → hallazgos_<eje>.json
                    ⇢ explica-verificador por eje (pipeline) → verificacion_<eje>.json · gate afirmaciones --check (E2)
                    → consolidar (explicacion.json, base/ y la CALCULADORA: ejemplos.json + cifras ej-cNN)
                    → video-gancho en modo explica → gate ganchos --check (R1–R12) → video-critico elige
                    → explica-guionista (ganchos --usar → narración de corrido → narracion --check (E9) → escenas →
                      guion --check (E1–E12 + V1–V5, V9, F1–F8))
                    → historia-oyente en modo explica (confusiones + explicacion_devuelta)
                    → video-critico en modo explica (≤ 2 vueltas, acotadas; arreglos probados) → mejoras
                    → video-animador por escena explica sin animación]
   desde: "guion" → salta a Guion · desde: "retoque" + notas → Guion (conserva las voces) → oyente → crítica (1) → animación
→ ejemplos (revisión de los números) → [sin-voz: voz-falsa] | voz (MCP ElevenLabs, por secuencias, como /historia)
→ tiempos (V16, V6, V10) → escuchar (V11) → grabar (V7, V13) → montar (V8) → revisar (9:16 y 4:5)
→ entregar (explicaciones/<fecha>-<slug>/) → memoria.py --explica (memoria/explicaciones.json) → make validate (M12)
```

`scripts/explica.py` escribe el **mismo TRABAJO que `/video`**: arma en `TRABAJO/base/` un «hilo base»:
- `hilo.json`;
- `datos.json` con las cifras verificadas y las de los ejemplos `ej-cNN`;
- las tarjetas `tuit_N.html` materializadas.

Así el gate, los ganchos, los tiempos y el render salen de `scripts/video.py`, con la escena propia `cuenta` enchufada por
`CONSTRUCTORES`, `TRANSICION_DE`, `SIN_HUECO` y `POST_CONSTRUCTORES` (rótulo de acto y chip «Ejemplo»). Reutiliza de
`scripts/historia.py`:
- `leer`, la clasificación de fuentes y la evidencia;
- las tarjetas, el rótulo de acto y la voz por secuencias;
- `probar` y `aplicar`.

## La dramaturgia (decisiones del usuario, 2026-10-29)

**Principio rector — la prueba de retorno**: el oyente ingenuo devuelve en una oración cómo funciona lo que le
explicaron (`explicacion_devuelta`). Si no casa con la `mecanismo_frase` del encuadre, el crítico bloquea (E-C2).

| Acto | Qué cuenta | Termina en |
|---|---|---|
| 1 · **La pregunta** (≈ 25 %) | el gancho, la promesa y **la idea equivocada** que casi todos tienen, dicha con justicia (`intuicion: true`); a veces una `adivina` | el **detonante**: «pero eso no es lo que pasa» |
| 2 · **El mecanismo** (≈ 45 %) | la cuenta con quetzales (`corrige: true`) → la definición → la animación → **el «ajá»** del punto medio | el **giro** (`giro: true`, 40–75 %): la otra cara del mecanismo |
| 3 · **En tu vida** (≈ 30 %) | el mecanismo con **datos reales de Guatemala** (con su fecha y su fuente), el pago de la promesa y **la regla práctica** | el cierre de **consecuencia**: lo que el mecanismo le hace a quien lo vive |

Reglas del explicador:
1. **Un ejemplo conductor**: los mismos personajes y los mismos números de principio a fin.
2. **Lo concreto antes que lo abstracto**: la cuenta va antes de la definición; la fórmula algebraica no sale en
   pantalla (salvo en `largo`).
3. **La idea equivocada se nombra y se rompe** de forma visible.
4. **Jerga presentada**: cada término del glosario llega definido.
5. **Un solo código de color** (`leyenda`): el mismo concepto, el mismo color en la pizarra, la animación, las
   tarjetas y el cierre.
6. **No es consejo**: ni órdenes, ni bancos, ni productos.
7. **«Guatemala» o «quetzales» en ≤ 6 s**.

## Números de ejemplo (decisión del usuario, 2026-10-29)

Se permiten, con tres condiciones:
- **los calcula el script** (`explica.py`, la calculadora; nunca un agente);
- **la voz los dice como ejemplo** («imagina», «supón», «por ejemplo», «hagamos la cuenta»), en la primera escena de
  cada acto que los usa;
- **la pantalla lleva el chip «Ejemplo»**: lo pone sola en cada escena con números ilustrativos (E4).

Un número de ejemplo nunca va en la misma oración que «en Guatemala», y una tarjeta con números de ejemplo dice
`Fuente: Ejemplo ilustrativo (cálculo propio)`. Los datos de Guatemala (tasas, precios, leyes) van verificados como
siempre. `ejemplos.md` acompaña la entrega con cada fórmula.

Catálogo de modelos (`MODELOS`):

| Modelo | Calcula |
|---|---|
| `compuesto` | saldo por periodo, interés total, interés simple, interés sobre interés y su porcentaje, años para duplicar |
| `simple` | lo mismo con interés simple |
| `aporte_periodico` | ahorro con aportes iguales |
| `regla72` | 72 ÷ tasa y el valor exacto |
| `tasa_real` | tasa nominal menos inflación |
| `cuota` | cuota de un préstamo, total e intereses |
| `porcentaje` | un porcentaje de una base |
| `proporcion` | una parte entre el todo |

Un parámetro es un número ilustrativo o `{cifra: "<eje>-cNN"}`: un dato real verificado. Con todos los parámetros
reales, el resultado es un dato real derivado y no lleva chip.

## Cómo se ve

En estilo Noche, igual que `/video` y `/historia`: fondo de la paleta casi negro con grano, crema y una sola cosa en
acento; el acto 2 baja a `fondo_acto2`.

**Escenas**:
- de `/video`: `gancho` (visuales `cifra`, `llenado`, `pareja`, `figuras`), `golpe`, `definicion`, `adivina`,
  `tarjeta` (las 26 plantillas), `escala`, `tiempo`, `ranking` y `explica` (la animación de la biblioteca);
- **`cuenta`**, propia (la pizarra, `video/cuenta.html`): 2–5 renglones «a op b = r» que se escriben al ritmo de la voz.
  - Cada renglón entra cuando la voz dice su primer número, y el resultado cae con un rebote cuando la voz lo dice.
  - Los renglones viejos bajan a media luz.
  - Un renglón puede llevar `resalta` (la celda en acento, con su subrayado y su `etiqueta`).
  - `saldo` pone el último resultado en grande, contando; `fuente` lleva el pie.
- **Chip «Ejemplo»** (`video/comun.js`, `S.ejemplo`): arriba a la derecha, en Mono, dentro de la zona segura.
- **Rótulo de acto** sobre la primera escena de los actos 2 y 3 (`rotulo {etiqueta, titulo}`), el de `/historia`.

**Animaciones**: el mecanismo `exponencial` (crece sobre lo acumulado) se suma a `MECANISMOS_EXPLICA`. Su semilla es
`bola-nieve`: columnas en tres capas (capital tenue, interés del capital en crema, interés sobre interés en acento) y
la cámara que se aleja cuando la capa de acento engorda.

## Gates (`scripts/explica.py`)

| Gate | Dónde | Qué exige |
|---|---|---|
| E1 encuadre | `encuadre --check` | `pregunta`, `intuicion` (≤ 22 palabras), `mecanismo` (de `MECANISMOS_EXPLICA`) y `mecanismo_frase` (30–220), `leyenda` 2–4 con un acento, `glosario` ≤ 3, `anclas` ≥ 1, `ejemplos` del catálogo (≤ 4 ilustrativos) con sus parámetros, `revelaciones`, 1–3 `ejes`, `sensible` |
| E2 evidencia | `afirmaciones --check` · `guion --check` | afirmaciones (`<eje>-aNN`, tipo `definicion\|regla\|proceso\|dato\|norma`), cifras (`<eje>-cNN` con valor, unidad y periodo) y citas con su fuente guardada y la cita literal; `confirmado` = 2 grupos o 1 oficial o académica; `en_disputa` con nota (la voz la atribuye) |
| E3 ejemplos | `consolidar` | cada parámetro es un número o `{cifra: id}` verificado; todo número de ejemplo es un `ej-cNN` calculado por el script |
| E4 marcado | `guion --check` | la primera escena de cada acto con números de ejemplo los dice como ejemplo; nunca un número de ejemplo junto a «en Guatemala»; una tarjeta de ejemplo dice «Ejemplo ilustrativo» en su fuente; el chip lo pone el script |
| E5 estructura | `guion --check` | 3 actos en orden; `intuicion` (acto 1, no el gancho) y `corrige` (acto 2, después); ≥ 1 `explica` o `cuenta` en el acto 2; un `giro` en el acto 2 entre el 40 y el 75 %; el acto 3 dice una cifra real; rótulo en la primera escena de los actos 2 y 3; ≤ 3 escenas seguidas del mismo tipo; ≤ 2 explica; ≤ 19 escenas |
| E6 ejemplo conductor | `guion --check` | los personajes del gancho vuelven después de la escena 2 |
| E7 leyenda | `guion --check` | `acento` de una escena = un concepto en acento de la leyenda |
| E8 glosario | `guion --check` | cada término llega definido en su primera mención (o con una escena `definicion`) |
| E9 narración | `narracion --check` · `guion --check` | `narracion` = suma literal de las voces por acto; palabras de la duración (medio 250–300, aviso; falla fuera de 210–345); ≥ 2 conectores por acto; ≤ 2 «según» (≤ 1 por acto); referencias con antecedente; secuencias dentro de un acto; > 6.5 cortes por minuto es aviso |
| E10 no consejo | `guion --check` | sin «deberías», «te recomiendo», «invierte en», «la mejor opción», bancos ni productos en voz, pantalla y captions; en salud, ni dosis ni diagnóstico |
| E11 cuenta | `guion --check` | 2–5 renglones con op `+ − × ÷`, celdas ≤ 12, `a op b = r` con el redondeo de `r` (`aprox: true`: ±2 %), un solo resaltado con su etiqueta, golpe ≤ 6 palabras; ≤ 3 cuentas, nunca dos seguidas |
| E12 promesa | `guion --check` | `promesa.revela` y la escena `pago` cuenta esa revelación |

Además corren los de `/video`:
- en `guion --check`: V1–V5, V9 (sin «la escena 2 es T1») y F1–F8;
- R1–R12 en los ganchos (R6 acepta «quetzales»);
- al grabar y montar: V6, V7, V8, V10, V11, V12, V13, V15 y V16.

## Voz y costos

Como `/historia`: un nodo TTS por secuencia de 2–5 escenas del mismo acto o por escena suelta, Scribe por nodo,
`descargar --estado` corta cada secuencia. Cuesta ≈ 1 crédito por carácter: **≈ 1,700** en `medio`, ≈ 850 en `corto`
y ≈ 2,400 en `largo`. El Workflow cuesta 0 créditos (≈ 9–12 agentes, 15–30 min).

## Archivos del trabajo

- `encuadre.json`, `hallazgos_<eje>.json` y `verificacion_<eje>.json`;
- `explicacion.json` (afirmaciones, cifras, citas, ejemplos) y `ejemplos.json`;
- `base/`;
- `ganchos.json`, `seleccion.json`, `guion.json`, `oyente.json` y `critica.json`;
- luego lo de `/video`: `locucion.json` (con `ejemplo` por escena), `audio/`, `escenas.json`, `clips/`, `salida/` y
  `revision/`.

## Entrega y registro

- `explica.py entregar TRABAJO` → `explicaciones/<fecha>-<slug>/`:
  - `video.mp4` y `video_4x5.mp4`;
  - `caption.md`, `subtitulos.srt`, portadas y hojas de contacto;
  - `fuentes.md`, `ejemplos.md` y el `guion.json` de entrega (con `explicacion_devuelta`).

  Los mp4 están fuera de git.
- `memoria.py --explica explicaciones/<fecha>-<slug>` → `memoria/explicaciones.json`. `explica.py` lo lee para avisar
  si el tema ya se explicó, rotar gancho, cierre, animaciones y música, y para las frases ya usadas (C11). M12 lo valida.

## Prueba sin web ni créditos

`make explica-fixture`: la maqueta del interés compuesto (`sesiones/_fixture_explica/`, fuentes de ejemplo guardadas,
voz falsa). Genera el 9:16 y el 4:5 en `sesiones/_fixture_explica/salida/`. Es también el ejemplo de guion de
`referencias/roles/explica-guionista.md`.
