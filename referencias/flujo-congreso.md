# /congreso · una ley del Congreso en menos de un minuto

Un video vertical de **43–57 s estimados y ≤ 59.5 s reales** (9:16 + 4:5) sobre UNA ley votada en el Congreso de
Guatemala: qué buscaba, cuántos votos tuvo frente al umbral y quiénes votaron de cada lado. Inspirado en los videos de
parlamentos con hemiciclo animado (decisión del usuario, 2026-11-04): el hemiciclo que se llena asiento por asiento con su
contador y un pop por tanda, la línea de mayoría, el sello del resultado, los avatares de los diputados unidos a su
asiento y el **portal**: el círculo del gancho que se abre hacia el hemiciclo. Comando: `.claude/commands/congreso.md`.

## Datos

- **Votos**: el registro nominal oficial (congreso.gob.gt), capturado con Chrome (`referencias/congreso/captura.md`) e
  importado a `sesiones/_congreso/base/{votaciones,votos}.csv` (fuera de git; la misma base que la investigación N.º 03,
  `sesiones/como-vota-el-congreso/`). `importar` coteja lo que ya estaba (CG1).
- **La votación decisiva** (`preparar`): la redacción final; si no hay, el único debate; si no, el tercer debate. La
  urgencia nacional (si la hubo) va aparte, con su umbral de **107** (dos tercios). El umbral de aprobación es **81**
  (mayoría absoluta del total, Ley Orgánica art. 99). Cifras `cg-cNN` en `base/datos.json` con el listado nominal
  (`votos_ley.csv`) como archivo local: a favor, en contra, ausentes, licencia, 160, umbral, por bancada y la urgencia.
- **La ley** (`ley.json`, CG2): lo escribe la sesión con la nota oficial del Congreso, el PDF de la iniciativa o la prensa.

```json
{"iniciativa": "6347", "decreto": "26-2026", "titulo": "Decreto 26-2026, Ley Marco de Ciberseguridad",
 "nombre_corto": "Ley de Ciberseguridad",
 "que_busca": [{"texto": "Crea una fiscalía…", "url": "…", "archivo": "sesiones/_descargas/congreso/….txt", "cita": "<literal>"}],
 "estado": {"texto": "Entra en vigencia 30 días después de publicarse", "url": "…", "archivo": "…", "cita": "<literal>"},
 "cifras": [{"id": "ley-c01", "concepto": "…", "valor": 4, "unidad": "años", "periodo": "…", "url": "…", "archivo": "…", "cita": "<literal con el número>"}],
 "citas": [{"id": "ley-q01", "texto": "<frase literal>", "autor": "…", "cargo": "…", "cuando": "…", "documento": false, "url": "…", "archivo": "…"}]}
```

`ley --check` pasa las `cifras` a `base/datos.json` (respaldan la voz, V2) y el título y `que_busca` al tema del hilo base
(F3: la frase final nombra algo del tema).

- **Retratos**: la miniatura oficial de la portada (cara y hombros), en `design/diputados/<id>.jpg` (caché) y
  `TRABAJO/fotos/dip-<id>.jpg` con «Foto: Congreso de la República». La foto del gancho: la og:image de la nota oficial de la
  sesión (`congreso.py leer`) o una de Commons (`historia.py foto`).

## Narrativa (el formato)

Frases cortas que se encadenan con «pero» y «por eso»; cada escena responde la pregunta que dejó la anterior.

| # | Escena | Qué dice | Cómo se ve |
|---|---|---|---|
| 1 | `gancho` (`visual: foto`, `mini: decisiva\|urgencia`) | la tensión de la votación con su sujeto: «La ley de ciberseguridad pasó por 2 votos en el Congreso.» (≤ 4 s la primera oración, R3, R14) | la foto del pleno a sangre; el hemiciclo dentro de un círculo que se llena con su contador; la pantalla y la línea; al final el círculo se abre (portal) |
| 2 | `hemiciclo` (`fases: [llenar, umbral]`) | el umbral y el resultado: «Declarar urgente una ley pide 107 votos… Esta tuvo 109, y 10 en contra.» | los asientos se encienden con un pop por tanda; la línea del umbral entra cuando la voz dice el número; el sello «Aprobada» y el mazo |
| 3 | `golpe` / `foto` / `cita` (`afirma`) | qué buscaba, en lenguaje llano: a quién le toca y qué cambia | texto cinético o la foto/el documento |
| 4 | `hemiciclo` (`fases: [foco]`, opcional `barras`; con 3 y 3, dos escenas: en contra y «pero» a favor) | quiénes: hasta 3 nombres por lado, de partidos distintos y de peso en la votación (CG4) | el resto se apaga; anillos sobre los asientos; la ficha con el retrato unida al asiento por un cordel; la bancada entera |
| 5 | `golpe` (`estado`, enlace `por_eso`) | qué pasa ahora: vigencia, sanción, veto, la pena o el plazo | texto cinético |
| — | cierre de una pantalla | la consecuencia para quien vive la ley (F1–F8): «Las víctimas de un ciberdelito ya tienen una fiscalía propia.» | la frase y «Sígueme en» |

El orden puede cambiar (qué buscaba antes de la votación, si el gancho ya dijo la cifra), pero la votación entra en la
escena 2 o 3 (CG10).

## Escenas propias

- **`hemiciclo`** (`video/hemiciclo.html`, `congreso.py t_hemiciclo`): `votacion` (decisiva|urgencia), `fases` (`llenar`,
  `umbral`, `foco`, `barras`), `focos` [{`diputado`: nombre completo} | {`bancada`: «VAMOS», `voto`}], `barras_en` (la
  palabra de la voz que dispara las columnas), `golpe` arriba. Los 160 asientos de izquierda a derecha: a favor por
  bancada (la mayor primero), ausentes, licencia y en contra (la mayor al extremo derecho). A favor en el acento, en
  contra en crema, el resto apagado; **sin colores de partido**.
- **gancho con `mini`** (`congreso.py t_gancho`): la misma página en modo gancho; el portal se abre si la escena 2 es un hemiciclo.
- `foto` y `cita` son las de `/historia` (`historia.t_foto`, `historia.t_cita`), con las fotos de `TRABAJO/fotos` y las
  citas de `ley.json`.
- Efectos (catálogo fijo, `scripts/sfx.py`): `voto` (cada tanda de asientos, ≤ 12 por tramo), `mazo` (el resultado),
  `sello` (documento o estado), más los de siempre.

## Gates

| Código | Dónde | Qué exige |
|---|---|---|
| CG1 | `importar` | 160 filas por votación, sin nombres repetidos, votos conocidos, cada nombre en la base o el padrón; lo que ya estaba coincide voto por voto |
| CG2 | `ley --check` | título, nombre corto (≤ 34), 1–4 `que_busca`, cada cita literal en su texto guardado, cada cifra escrita en su cita, ids `ley-qNN`/`ley-cNN` |
| CG3 | `guion --check` | cada diputado que la voz nombra está declarado en `diputados` con el voto que dio; cada foco existe y tiene retrato |
| CG4 | `guion --check` | hasta 3 nombres por lado, **cada uno de un partido distinto** (los independientes ex X cuentan como X) y de los partidos que más votos dieron a ese lado (los N + 1 de más peso; un nombre con `notoriedad` vale aunque su partido sea chico); menos solo si votaron menos partidos; si hubo votos en contra, los dos lados |
| CG5 | `guion --check` | sin calificativos («traidores», «vendidos», «corruptos», «pacto de corruptos», «madrugonazo»…) en voz, pantalla ni captions |
| CG6 | `guion --check` | una escena con `afirma` (qué buscaba); `estado` solo con `ley.estado`; las fotos y citas existen |
| CG7 | `tiempos` | ≤ 59.5 s reales con el bucle (menos de un minuto) |
| CG8 | `guion --check` | ≥ 2 escenas con «pero / por eso / así que / entonces»; el gancho dice «Congreso», «diputados» o «pleno» |
| CG9 | `guion --check` | 4–8 escenas; cierre de una pantalla (`resumen: []`, `texto` = `final`) |
| CG10 | `guion --check` | una escena hemiciclo con «llenar» en la escena 2 o 3; su voz dice los votos a favor y el umbral; `fases` y `votacion` válidas |
| M19 | `make validate` | `memoria/congreso.json`: campos, estado, < 60 s, los dos lados, la entrega (guion, caption, fuentes.md, votos.csv) |

Además V1–V5, V9 (sin promesa: en < 60 s no hay nada que esperar), F1–F8 y R2–R14 de `/video`; V6–V16 y V13 en tiempos y grabar.

## Entrega

`congreso/<fecha>-<slug>/`: `video.mp4` (9:16, fuera de git), `video_4x5.mp4`, `caption.md`, `guion.json` (con la
iniciativa, la votación y los nombrados), `fuentes.md` (el listado nominal, la Ley Orgánica, la nota y las fotos) y
`votos.csv` (el listado nominal de la decisiva y la urgencia). Registro: `memoria.py --congreso`. La maqueta:
`make congreso-fixture` (la Ley de Ciberseguridad, iniciativa 6347, con su votación, notas y retratos congelados en
`sesiones/_fixture_congreso/`).
