# La maqueta 3D: contrato `maqueta.json`

La «maqueta que vuela»: un mundo 3D simple (relieve, lugares, piezas) que una cámara recorre mientras la voz cuenta,
con una capa 2D encima (titular, pines que siguen al 3D, cifras, subtítulos). Decisiones del usuario (2026-11-14):

- **Motores:** three.js dentro de HyperFrames para unos estilos y Blender + capa 2D de HyperFrames para otros. El
  estilo decide el motor. Remotion quedó fuera.
- **Un solo estilo por video; nunca se mezclan.** Lo elige el orquestador entre los ocho; si no está seguro, pregunta.
- **Dentro de la maqueta la cámara se mueve** (es la excepción a la cámara quieta de la mesa de archivo).
- **El gancho manda y todo concuerda:** lo que se ve es lo que la voz está diciendo.

`maqueta.json` es el único insumo del motor: tiempos **absolutos en segundos**, ya resueltos (quien lo escribe es
`scripts/video3d.py`, que convierte cada `dice` del guion en su segundo con la voz real, o estimado antes de la voz).
El motor no sabe de guiones ni de voz. `scripts/maqueta3d.py` lo valida (gates M3D, sobre los datos: nunca sobre
píxeles), saca cuadros sueltos y lo renderiza.

## Forma

```json
{
  "version": 1,
  "estilo": "noche",
  "paleta": "obsidiana",
  "fps": 30,
  "duracion_s": 46.2,
  "mundo": {
    "set": "guatemala",
    "exageracion": 5.0,
    "lugares": {"los-amates": {"lon": -89.10, "lat": 15.32, "nombre": "Los Amates"}},
    "piezas": [
      {"id": "motagua", "tipo": "falla", "trazos": ["Motagua Fault", "Western Motagua Fault"]},
      {"id": "pueblos", "tipo": "luces", "lugares": ["guatemala", "chimaltenango"]},
      {"id": "frontera", "tipo": "frontera"}
    ]
  },
  "camara": [
    {"t": 0.0, "mira": "los-amates", "dist_km": 420, "azimut": 0, "elevacion": 55},
    {"t": 5.2, "mira": [-90.2, 14.95], "dist_km": 160, "azimut": -20, "elevacion": 35}
  ],
  "eventos": [
    {"t": 0.6, "dur": 2.4, "tipo": "ruptura", "pieza": "motagua", "desde": "los-amates", "hacia": "oeste", "km": 230},
    {"t": 9.0, "dur": 3.0, "tipo": "onda", "centro": "los-amates", "radio_km": 300}
  ],
  "marcas": [
    {"t": 6.1, "hasta": 11.0, "lugar": "los-amates", "texto": "Los Amates, Izabal", "sub": "Epicentro"}
  ],
  "capa": {
    "titulares": [{"t": 0.0, "hasta": 5.2, "kicker": "4 DE FEBRERO DE 1976", "texto": "La madrugada del terremoto"}],
    "cifras": [{"t": 7.3, "hasta": 11.0, "valor": "7.5", "rotulo": "de magnitud", "fuente": "INSIVUMEH"}],
    "palabras": [{"text": "A", "start": 0.12, "end": 0.20}],
    "progreso": {"actos": [0.0, 12.4, 33.0]},
    "seguir": {"t": 22.0, "dur": 3.0},
    "aviso": "Maqueta · no a escala",
    "pie": "Relieve: Mapzen Terrain Tiles · Fallas: GEM (CC BY-SA 4.0)",
    "handle": "@DerekUrizar",
    "cierre": {"t": 40.1, "frase": "…", "redes": [{"nombre": "TikTok", "handle": "@derekurizargt"}]}
  }
}
```

## Campos

- **`estilo`**: uno del catálogo `design/sets3d/estilos.json` (`id`, `motor: three|blender`, cuándo usarlo). three.js:
  `color`, `noche`, `contorno`, `voxel`, `plano`. Blender: `arquitecto`, `diorama`, `papel`.
- **`paleta`**: una de `design/tokens.json → noche.paletas`; de ahí salen el fondo, el texto crema y **el acento**. En
  la maqueta, una sola cosa va en acento (el protagonista del video); los pines y los titulares no compiten con ella.
- **`mundo.set`**: una carpeta de `design/sets3d/<set>/` (geodatos ya bajados, con su fuente y licencia en
  `fuente.json`; el render no llama a la red). `exageracion` multiplica la altura del relieve.
- **`mundo.lugares`**: puntos con `lon`, `lat` y `nombre`; los del set (`lugares.json`) se pueden usar sin declararlos.
- **`mundo.piezas`**: lo que hay sobre el mundo. Tipos v1: `falla` (trazos del set por nombre; dormida hasta que un
  evento la rompe), `luces` (un punto de luz por lugar), `frontera` (el borde del país), `ruta` (una línea entre
  lugares). Ninguna pieza lleva texto ni cifras: eso va en la capa.
- **`camara`**: claves ordenadas por `t`. Cada clave: `mira` (id de lugar o `[lon, lat]`), `dist_km` (del ojo al punto
  que mira), `azimut` (grados; 0 = el ojo al sur del punto, mirando al norte; positivo gira el ojo hacia el este),
  `elevacion` (grados sobre el horizonte; 90 = cenital) y `fov` opcional (vertical, 50 por defecto). Entre claves se
  interpola cada parámetro con `e = -(cos(pi*u) - 1)/2`; antes de la primera y después de la última, la cámara queda
  en esa clave. La misma función vive en el motor y en `maqueta3d.py` (para proyectar pines en los gates).
- **`eventos`**: lo que pasa en el mundo, con `t` y `dur`. Tipos v1: `ruptura` (la falla se abre en acento desde un
  lugar, `hacia: este|oeste|ambos`, a lo largo de `km`), `onda` (un anillo que crece desde `centro` hasta `radio_km`),
  `deslizar` (flechas opuestas a los dos lados de la falla: el corrimiento), `encender` / `apagar` / `parpadear`
  (luces de `lugares`), `resaltar` (un lugar o una pieza sube de brillo). Un evento puede llevar `sfx` (id de
  `design/sfx/catalogo.json`): el motor no lo suena; `maqueta3d.py` lo lista en `efectos.json` para la mezcla.
- **`marcas`**: pines pegados al 3D: un punto en el ancla proyectada, una línea y una tarjeta con `texto` (y `sub`).
  Visibles de `t` a `hasta`.
- **`capa`**: el cuadro 2D. `titulares` (kicker + texto, arriba), `cifras` (valor grande + rótulo + fuente),
  `palabras` (la voz palabra por palabra, para los subtítulos), `progreso` (barra con sus actos), `seguir` (el botón
  «Sígueme» a mitad), `aviso`, `pie` (las fuentes de los geodatos), `handle` y `cierre` (la frase final y «Sígueme
  en» con las redes).

## Gates M3D (`maqueta3d.py check`, en 9:16 y 4:5)

| Gate | Qué revisa |
|---|---|
| M3D1 | Forma y versión; `estilo` del catálogo y con motor disponible; `set` y `paleta` existen |
| M3D2 | Piezas, trazos y lugares referenciados existen en el set o en `mundo.lugares` |
| M3D3 | Cámara: claves crecientes desde `t = 0`, parámetros en rango y velocidad tope (no marear) |
| M3D4 | Cada marca cae dentro del cuadro y fuera de la banda del titular y del pie ≥ 80 % de su ventana, y dura lo que se tarda en leer (0.5 s + 0.3 s por palabra, mínimo 1.2 s); ≤ 3 marcas a la vez |
| M3D5 | Titulares y cifras: tiempo de lectura; dos titulares no se pisan; la cifra no tapa una marca viva |
| M3D6 | Cada evento cabe en la duración y su centro se ve en cámara mientras ocurre |
| M3D7 | `aviso`, `pie`, `handle` y `cierre` presentes; el pie nombra las fuentes del set |
| M3D8 | Un solo estilo (no hay estilo por toma ni por pieza) |
| M3D9 | El gancho es un evento: hay un evento con `t ≤ 1.0` |
| M3D10 | Todo lo anterior se cumple en los dos formatos (9:16 y 4:5 encuadran distinto) |

La concordancia con la voz (cada toma, evento, marca y cifra nace en una frase que la voz dice; cada lugar que la voz
nombra tiene su marca o es el foco; cada número con respaldo) la revisa `video3d.py guion --check`, que es quien
conoce el guion.
