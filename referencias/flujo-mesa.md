# La mesa de archivo en vertical (9:16 y 4:5)

El video vertical dibujado como el 16:9 de `/youtube-long`: una mesa fija donde **entra lo que la voz nombra**. Decisión
del usuario (2026-11-14), tras aprobar el lienzo «Animador vertical» en Claude Design. Motor: HyperFrames
(`scripts/video_hf.py`; núcleo común con el 16:9 en `scripts/mesa.py`). El motor propio (`video/*.html` +
`scripts/video_grabar.js`) sigue vivo para los flujos sin migrar y para grabar los tableros.

**Estado (2026-11-14).** El usuario aprobó el piloto (Bancafé parte 1) y pidió migrar.

| Flujo | Quién dibuja | Por qué |
|---|---|---|
| /historia, /serie (motor historia) | **la mesa** (`video.json → "realizacion": "mesa"`, por defecto) | Tienen fotos, notas, documentos y personas: es su lenguaje. |
| /sabias, /explica | motor propio, por ahora | Ganan con la mesa, pero antes hacen falta: el chip «Ejemplo» y el rótulo de acto sobre un tablero, la pizarra `cuenta` como pieza (`hoja`), la `barra`, el documento desde la evidencia de un dato y el cuadro 0 de un gancho sin foto. |
| /video, /departamento | motor propio | Son casi todo tarjetas con gráfico: en la mesa quedarían como una fila de clips al 86 % con fichas de texto, peor que hoy. Antes hacen falta `barra`, `serie`, `brecha` (los 22 con valores) y `tabla`. |
| /congreso | motor propio | Su hemiciclo con portal no existe en la mesa; decidirlo con el usuario. |
| /noticias, /semana | motor propio | No se publican. |

`realizacion` la fija `preparar` al crear el TRABAJO (`VD.MESA_FLUJOS`; `--realizacion propio|mesa` la fuerza): un trabajo
empezado con un motor termina con ese motor. Migrar un flujo es añadir su `tipo` a `MESA_FLUJOS` cuando sus piezas existan.

Pendiente en el motor: MV13 (un solo acento a la vez), la pregunta P6 en el pago, la versión B del gancho, y las piezas
`paso` (cronología), `barra`, `brecha`, `hoja`, `tabla` y `diagrama`.

## 1. Reglas (lo que no se negocia)

1. **Dinamismo = piezas que entran.** Con cada oración cae una pieza que la voz nombra y se queda quieta. La cámara no se
   mueve; nada se escala, desliza ni late para aparentar ritmo. Ningún gate mide píxeles ni movimiento.
2. **El texto da tiempo de leerse (MV8).** Una pieza queda al frente al menos `0.5 s + 0.3 s × palabras que la voz no
   dice` (nunca menos de 1 s) antes de replegarse o barrerse. Lo que la voz dice mientras la pieza está en pantalla se oye
   a la vez que se ve y no cuenta; por eso la cita y el documento que la voz lee no tienen mínimo.
3. **Repliegue por corte.** En 1080×1920 caben 2–3 piezas. Cuando la que entra no cabe, las de al frente pasan **de un
   corte** a su versión compacta, arriba y atenuadas (a lo más dos). Solo ocurre cuando entra otra pieza: nunca para dar
   ritmo, nunca animando la escala.
4. **Archivo real primero.** Foto con crédito, recorte con el titular o el extracto literal de la nota leída, página de
   documento con la frase subrayada, lugar en el mapa. Una ficha de texto es el último recurso.
5. **Personas y justicia.** La foto de alguien en un proceso solo va donde la voz lo nombra; nada de «culpable» sin
   sentencia firme; un alegato se atribuye («según la acusación»).
6. Lo de siempre: colores por variables de la paleta, fuentes locales, sin red en el render (GSAP en
   `design/vendor/`), render con `--workers 1`.

## 2. El cuadro

| Elemento | 9:16 (1080×1920) | 4:5 (1080×1350) |
|---|---|---|
| Kicker de serie («Parte N de M · título») | y 222, mono 22 px, en el acento | y 66 |
| Barra de progreso (un tramo por acto y el cierre) | y 262 (226 sin serie), 7 px | y 106 |
| Golpe de arriba (`titulo` de la mesa, ≤ 6 palabras) | bajo la barra, 92 px (76 si pasa de 2 renglones) | igual |
| Mesa | desde el fin del golpe + 30 hasta y 1370; x 85–876 (hasta 1023 sobre y 1070) | hasta y 1090; x 85–995; todo a escala 0.87 |
| Subtítulos | y 1400 (1500 en el cierre), 60 px, trozos ≤ 26 caracteres; la palabra activa en caja de acento, las que faltan al 38 %; callan mientras la voz lee una cita en pantalla | y 1120 |
| «Sígueme» a mitad (V25) | hacia el 50 %, 3.4 s, arriba a la derecha de la mesa (la mesa baja 104 px) | igual |
| Cierre | pantalla 1: tres conclusiones (la última en acento); pantalla 2: frase final, «Sígueme en», logo y usuario de las cinco redes; el golpe de arriba anuncia la parte siguiente de una serie y, desde la parte 2, sale «Empieza por la Parte 1 · fijada en mi perfil» | redes en dos columnas |
| Bucle | tras el cierre, el cuadro 0 del gancho vuelve 0.6 s con la barra en cero (TikTok repite el video) | igual |
| Portada | `salida/portada.png`: el cuadro del gancho con su golpe de arriba, sin subtítulos ni barra | — |

La barra va fija arriba del golpe (en las láminas iba debajo): si el golpe cambia de uno a dos renglones, la barra no
salta.

## 3. Piezas

Las del 16:9, con las medidas del vertical (`medida_v`): `foto` · `recorte` · `documento` (página con marcador o
portada) · `persona` · `institucion` · `lugar` (mundo con ruta, o Guatemala con el departamento) · `fecha` (sello o
calendario) · `cifra` (con `cuenta` y `cuadros`) · `termino` (nota, o ficha con `definicion`) · `cita` (se entinta
palabra por palabra) · `lista` (un chip por `dice`, con `lazo`).

- Letra: lectura ≥ 42 px, rótulos ≥ 28 px; créditos y fuentes en 22 px (no son lectura).
- Una pieza con `w` usa ese ancho (p. ej. una foto chica junto a una nota).
- Dos piezas chicas (≤ 470 px) caben lado a lado; una hoja a todo el ancho va sola en su renglón.
- El rótulo de acto de una escena (`S.R`) abre su mesa como ficha: «Acto 2 de 3 · lugar», título y periodo.
- Una mesa sin golpe de arriba propio conserva el de la mesa anterior.
- **`red`: la jerarquía de personas.** Cartas por nivel (retrato, nombre corto, cargo), hilos entre ellas, quien acusa
  aparte y sin hilos, y el estado del caso si un hecho lo trae. Hilo sólido = hecho; **punteado = alegato**, con la etiqueta
  «Según…» arriba, que entra antes que las caras. Una carta con `clave` entra como apodo («El Uno») y se voltea a la cara
  cuando la voz dice el nombre. Va sola en su mesa: ≤ 3 niveles, ≤ 2 por nivel, ≤ 2 acusadores. Una escena `red` del
  guion ya la trae en el borrador.
- `"limpia": true` en un golpe: el plano pide el repliegue justo antes de esa pieza.
- **Tablero**: `explica`, `tarjeta`, `cuenta`, `hemiciclo`, `vias`, `deptos`, `ranking`, `mapa`, `escala`, `tiempo`,
  `lupa`, `cortina` se graban limpias con el motor propio (`video_hf.py tableros`) y van solas en su mesa. Si el plano
  les pone golpes, el primero entra ≥ 1 s después del último paso y la animación le cede la mesa de un corte.

## 4. El plano

`TRABAJO/plano.json`, el mismo esquema del 16:9, sin `x` ni `y` (el motor coloca por regla):

```json
{"mesas": [{"escenas": ["e1"], "titulo": "Del café a Barbados", "golpes": [
  {"tipo": "foto", "foto": "caf-f01", "pie": "Edificio central de Bancafé, zona 9"},
  {"tipo": "termino", "texto": "Bancafé"},
  {"tipo": "lugar", "dice": "banco en Barbados", "mapa": "mundo", "ruta": true, "puntos": [{"nombre": "Guatemala"}, {"nombre": "Barbados"}]}]}]}
```

- Las escenas se nombran `eN`. El cierre no va en el plano (lo arma el motor).
- Los golpes sin `dice` al inicio de la primera mesa ya están puestos en el cuadro 0 (el gancho: la foto del
  protagonista y su nombre).
- Escribir para el vertical: **una pieza por oración, texto corto** (lo que la voz ya dice no hace falta repetirlo en
  la ficha), mesas de una escena o dos.

## 5. Gates MV (`video_hf.py plano --check`, sobre los datos)

| Gate | Pide |
|---|---|
| MV1 | cada cifra o año que la voz dice se ve cuando se dice |
| MV2 | cada oración trae una pieza, una marca o un paso; ningún hueco de más de 4 s |
| MV3 | una foto, una sola vez |
| MV4 | respaldo por tipo (ficha y crédito de la foto, nota leída del recorte, página del documento…); foto de un proceso judicial solo donde la voz nombra a alguien |
| MV5 | no relleno: ≥ 50 % de oraciones con pieza nueva, ≥ 35 % de archivo real (aviso bajo 50 %), ≥ 4 tipos, ≤ 2 rótulos de texto seguidos |
| MV6 | carga: mesa de 3–24 s y ≤ 6 piezas; entradas a ≥ 0.4 s; el golpe de un tablero, tras su último paso |
| MV7 | sin cámara |
| MV8 | lectura: `0.5 + 0.3 × palabras no dichas` s al frente (≥ 1 s) |
| MV9 | pila: ≤ 3 piezas al frente y ≤ 2 compactas (por construcción) |
| MV10 | zona segura por geometría, en 9:16 y en 4:5 |
| MV11 | ninguna pieza se dibuja a menos del 72 % de su tamaño |
| MV12 | alegato: los hilos de una `red` atribuida van punteados, con `etiqueta` «Según…» y con la voz de la mesa atribuyendo; quien acusa, sin hilos |
| MV13 | (pendiente) un solo acento legible a la vez |
| MV14 | el cuadro 0 abre con ≥ 2 piezas ya puestas |

MV1–MV7 son YT13–YT19 del núcleo con las constantes del vertical (`REGLAS`). `hyperframes check` añade sus propios
avisos (texto bajo 28 px, texto sin tiempo de lectura, tramos sin cambio): se leen en `video_hf.py revisar`.

## 6. Cómo se produce

Los comandos son los de siempre; con `realizacion: mesa` despachan a la mesa (`VD.es_mesa`):

```
<flujo>.py tiempos T                  la voz real → escenas.json (igual que antes)
Workflow «plano» {trabajo: T}         video-realizador escribe T/plano.json desde `<flujo>.py plano T --digesto` (tras la voz)
<flujo>.py plano T --check --hoja     gates MV1–MV14 y la hoja de golpes (plano.md)
<flujo>.py grabar T [--formato 4:5]   plano --check → tableros limpios → proyecto → hyperframes check → render (un proceso)
<flujo>.py montar T [--formato 4:5]   una mezcla para los dos formatos (−14 LUFS), .srt, caption.md y portada.png
<flujo>.py revisar T [--formato 4:5]  hoja de contacto del video final (revision/contacto[_4x5].png)
<flujo>.py entregar T                 igual que antes
historia.py producir T                la cadena entera; se detiene si falta plano.json («falta la fase Plano»)
```

- El **borrador** (`plano.borrador.json`, `video_hf.borrador_v`) sale del código: una mesa por escena con su foto, su cita,
  sus cifras y años dichos, las personas nombradas, la página de documento, la `red`, un recorte con el titular real de la
  nota de un hecho, y el cuadro 0 con el protagonista. No pasa los gates por sí solo y no se publica: lo mejora el realizador
  (en una maqueta se usa tal cual y los gates solo avisan).
- Lo que falle en pantalla se arregla **en el plano**: no se toca el guion ni la voz. Un retoque = el Workflow «plano» con
  `notas`. Si cambia una voz: `tiempos`, `plano --check` y volver a grabar (no hay `grabar --solo`).
- Render: ≈ 1.6× la duración por formato, en fila (HyperFrames renderiza de uno en uno). `MESA_CALIDAD=draft` para probar.
- `MESA_RENDER=0` (maquetas): `grabar` hace todo menos el render y deja un doble de la duración exacta; `entregar` real lo
  rechaza. `make historia-fixture` y `make serie-fixture` van así; `make video-fixture-mesa` renderiza de verdad.
- `video_hf.py` también se puede llamar directo: `piloto` (copia un TRABAJO ya producido para rehacerlo en mesa),
  `importar-plano` (los golpes del 16:9 de una parte, como punto de partida), `borrador`, `digesto`, `tableros`, `proyecto`,
  `revisar` (hyperframes check + hojas por mesa), `audio`, `render`, `montar`, `portada`, `contacto`.

## 7. Qué pasa con las reglas del motor propio

- **Se conservan** (guion, voz, audio): V1–V6, V8, V9, V11, V16–V20, V23, R1–R14, P1–P6, F1–F9, H*, E*, SE*.
- **Pasan a gates MV**: V13 → MV10 · V15/R12 → MV14 · V10/V26 → MV2/MV1 · V22 → MV6 · H6/H7/H7c → MV11/MV3/MV4.
- **No corren en la mesa** (siguen en el motor propio): V12, V21, el catálogo `TRANSICIONES`, el empuje de la foto, la
  foto a sangre, A3. V7, A1 y A2 quedan para los clips de tablero.
