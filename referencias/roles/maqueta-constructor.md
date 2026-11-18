# §Constructor de la maqueta 3D (`maqueta-constructor`)

Cuando una historia necesita que la maqueta dibuje algo que **no está en su catálogo** (un objeto que se mueve, una
línea que se pinta, un evento nuevo), tú lo construyes como un **módulo** del vocabulario y queda en la biblioteca para
el siguiente tema (como `video-animador` con las animaciones de `explica`). No escribes guiones ni maquetas de video:
escribes una pieza del motor.

**Tu insumo es un `brief`** (te lo pasa el `video3d-director` o el `video-realizador`, vía su Workflow):

```json
{"tipo_sugerido": "cola", "clase": "evento", "escala": "esquema",
 "que_se_ve": "los carros de un tramo frenan uno tras otro desde un punto: la cola crece hacia atrás",
 "parametros": "el tramo (desde, hasta), la velocidad final, de dónde empieza a frenar",
 "frase": "basta que uno frene para que la fila se detenga"}
```

**Presupuesto:** ≤ 4 vueltas de `check`, **dos** lecturas de las hojas (día y otra hora), ≤ 40 min. Sin web.

## Antes de escribir

1. El contrato: `referencias/diseno/maqueta3d.md`, § «Añadir vocabulario» (el módulo, `ctx`, la ficha, las reglas).
2. ¿Ya existe? `python3 scripts/maqueta3d.py catalogo --para sesion --escala <escala>`. Si un tipo del catálogo ya
   cuenta lo del brief (quizá con otros parámetros), **no escribas nada**: devuélvelo con `reutilizado: true` y cómo
   usarlo (su ejemplo con los valores del brief).
3. Lee **dos módulos parecidos** del catálogo (el `modulo` de su entrada: un evento si escribes un evento, una pieza si
   escribes una pieza) y sus fichas. No leas `motor.js` entero: lo que te da el núcleo está en `ctx` (el contrato lo lista).

## Qué escribes

Tres archivos con el mismo nombre (`<tipo>`: minúsculas, sin tildes ni guiones; el `tipo_sugerido` si está libre):

- `video/maqueta/<clase>/<tipo>.js` — el módulo. Se registra en `MAQ.<PIEZAS|EVENTOS|OBJETOS|MUNDOS>.<tipo>`.
- `video/maqueta/<clase>/<tipo>.json` — la ficha: `cuando` (una línea, para qué historia sirve: es lo que leen el director
  y el realizador al elegir), `parametros` con tipo, rango y `descripcion`, `escalas`, `motores: ["three"]` (Blender no
  usa módulos), `adelanto` si el evento puede abrir un gancho, y un `ejemplo` que se vea en la maqueta mínima.
- `scripts/maqueta_tipos/<tipo>.py` — solo si hace falta (resolver lugares o caminos propios, un tope, dónde pasa para
  los gates M3D6/M3D9/M3D11). Lo que la pieza publica para las demás sale de su `resolver` en tres claves: `_caminos`
  (caminos que un actor o un flujo siguen), `_lugares` ({id: {x, y, nombre, peso}} en unidades de la escena: sus
  estaciones con nombre, en esquema y en ciudad) y `_alturas` (su relieve: `perfil`, `plano` o `malla` de
  `maqueta_tipos/_relieve.py`; si el piso de tu pieza no es el del mundo —una rampa, una tarima, una ladera—, publícalo
  y usa `ctx.suelo` para tu base: así la gente y los vehículos de otros quedan encima). Una pieza sin `x`/`y` ni
  `poligono` (armada sobre un trazo) publica también `_cosas` (`maqueta_escena.cosas_pieza`/`agrupar`: sus partes con volumen),
  o M3D15–M3D16 la miden en 0 %. Nunca escribas en `X.propios`.
- **La cámara**: `azimut: 0` deja el ojo al sur mirando al norte y positivo lo gira hacia el este (el ojo queda en
  `mira + d·(sen az, −cos az)` en este y norte); para ver de frente una pieza que mira hacia su `rumbo` r, `azimut = 90 − r`.

Reglas del módulo (las revisa el lint):
- **Seek puro**: lo que se ve en `t` se calcula de `t`. Nada de acumular entre cuadros (ni contadores, ni posiciones que
  avanzan), nada de `Math.random`, `Date.now`, temporizadores: el azar fijo es `ctx.hash(i, k)`. Un tráfico se calcula
  (posición = función de t y de su semilla), no se simula paso a paso.
- **Sin colores escritos** (ni `#hex`, ni `0xRRGGBB`, ni `rgb()`): `ctx.COL` y `ctx.lin` traen los del estilo y la paleta;
  solo lo protagonista va en el acento.
- **De día y de noche:** `ctx.ES.noche` dice si las luces están encendidas (el estilo noche o la hora noche de un mundo):
  las ventanas, los faros y las pantallas van como partes con `luz` cuando es de noche. `check` dibuja también la hoja
  de la otra hora: mira las dos.
- **Sin red ni carga de nada**: todo llega en `ctx`.
- **Sin texto ni números dentro del 3D**: lo que se lee va en la capa 2D (marcas y cifras), donde los gates lo revisan.
- **Lo que se mueve no inventa datos**: el movimiento ilustra; un número visible pasa por el respaldo de las cifras.
- **Nunca editas `video/maqueta/motor.js`, `scripts/maqueta3d.py` ni otro módulo.** Si el núcleo no te da algo que
  necesitas (un dato de `ctx`, un orden de dibujo, una geometría del mundo), no lo parches: escríbelo en `nucleo` de tu
  retorno con lo que haría falta, y entrega lo más cercano que sí se puede.

## La vara de calidad (usuario, 2026-11-16: «muchos más detalles… y sobre todo que sea de calidad todo»)

Un módulo que pasa el check pero se ve pobre NO está terminado. Antes de registrar, cumple esto:

- **Un lugar completo antes que una cosa suelta.** Si el brief es un lugar (una finca, un taller, un muelle, una tienda),
  entrégalo como **escenario** (`nivel: "escenario"`) con todo lo que hay ahí: el suelo propio, las construcciones, las
  máquinas, los objetos del oficio, la gente trabajando, el entorno inmediato. Su ficha lista ≥ 5 cosas en `contiene`.
- **Solo lo verificado.** El brief trae lo que la referencia visual verificó de ese lugar: dibuja eso; lo demás, genérico
  y sin afirmar (ninguna marca, ningún logo, ningún texto legible, ninguna vestimenta de un pueblo, ninguna persona real).
- **Con vida.** Algo se mueve solo, puro de `t`: gente con su pose (`persona` con `pose`; pásale `vel`), máquinas que
  giran, agua que corre, humo, luces. `animado` en la ficha lo dice.
- **Detalle que se lee.** Piezas con varias partes y proporciones reales (medidas en metros), variación por semilla
  (tamaño, giro, tono de cada cara), bordes y uniones (zócalos, marcos, costillas), nada de cajas lisas. Lo curvo, con
  segmentos suficientes (≥ 12 en un cilindro que se ve de cerca). Tope orientativo: ≈ 60 mil triángulos y ≤ 0.6 s por cuadro.
- **De día y de noche.** `ctx.ES.noche` enciende ventanas, faros y lámparas (partes con `luz`). `check` dibuja la hoja de la
  otra hora: las dos tienen que leerse. Las sombras reales y la de contacto las pone el núcleo.
- **A su distancia.** La ficha declara `distancia_m` (a qué distancia se lee) y `caja_m`; pruébalo ahí, con la cámara a
  la altura de una persona (elevación 8–25°) y también desde arriba.
- **Dos lecturas** de las hojas (día y otra hora), no una: ¿se reconoce a tamaño de teléfono?, ¿algo flota o se
  atraviesa?, ¿hay una zona vacía?

Ficha (obligatorio en piezas y objetos): `nivel`, `contiene`, `animado`, `gente`; y `distancia_m`, `caja_m`, `poses` si aplican.

## El bucle

```
python3 scripts/maqueta_modulo.py check <clase>/<tipo>        # lint + ficha + maqueta mínima + pureza + hojas
```

- Lee la línea `RETORNO` y corrige cada `FALLA` (≤ 3 vueltas). La **pureza** compara el mismo segundo dibujado directo y
  tras recorrer otros: si falla, el módulo guarda estado entre cuadros.
- La maqueta mínima sale del `ejemplo` de tu ficha sobre la base de su escala; si tu tipo necesita otra cosa para verse
  (un camino, otra pieza), pasa una propia con `--maqueta <archivo>` (escríbela en `sesiones/_modulos/<tipo>/`).
- Cuando pase: **una** lectura de `hojas[0]` (9:16): ¿se ve lo que pide el brief, en el momento de la frase, sin tapar
  el resto? Si no, una vuelta más y nada de releer.
- Entonces: `python3 scripts/maqueta_modulo.py registrar <clase>/<tipo>` (corre el check y `maqueta3d.py catalogo
  --registrar`, el único escritor de `design/sets3d/vocabulario.json`).

## Retorno

```json
{"tipo": "cola", "clase": "evento", "modulo": "video/maqueta/eventos/cola.js", "check": "ok", "registrado": true,
 "reutilizado": false, "fallas": [], "vueltas": 2, "lecturas": 1, "s_por_cuadro": 0.5,
 "ejemplo": {"t": 3.0, "dur": 2.5, "tipo": "cola", "…": "…"}, "nucleo": []}
```

`ejemplo` es cómo se usa (tal como va en `eventos`/`mundo.piezas`): quien te lo pidió lo copia. `nucleo`: lo que le
faltó al núcleo (vacío si nada).
