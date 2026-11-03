# /departamento — la serie de los 22

Un video por departamento, «<departamento> frente al país», para que la gente de ahí lo reconozca y lo pase. No es un
flujo nuevo: es **`/perfil <depto>` (hilo) → `/video`** sobre ese hilo. El comando es
`.claude/commands/departamento.md`; el canon y el tablero, `scripts/departamentos.py`.

## Canon (`referencias/departamentos.json`)

- `orden`: los 22 códigos de mayor a menor población (`--siguiente` toma el primero sin video).
- `nombres` (= `H.NOMBRES` de `templates/base.html`; `--check` falla si divergen) y `alias` («Huehue», «Xela»…): la
  palabra clave del video es el nombre y sus alias.
- `dimensiones` (5–6): `{id, nombre, fuente_id, fuente, claves_fuente, indicador, anio, periodo, unidad, per_capita,
  denominador, desglose_22, estado, nota}`. Misma fuente y año para los 22 episodios. `anio: null` = el último que la
  fuente publique para los 22 (se fija al aprobar). `estado: propuesta | aprobada`. Un cambio de fuente o de año sube
  `version`.
- `alternativas`: dimensiones de repuesto, sin uso hasta que el usuario las pase al canon.

## Hilo: /perfil con canon

`departamentos.py --directiva GTxx` → `args.canon` del Workflow `hilo` (modo perfil, `min_tuits: 7`). El editor y el
investigador usan las dimensiones del canon; el guionista escribe `perfil {sujeto, tipo: "departamento", codigo,
canon_version, dimensiones[]{n, nombre, anio, canon, motivo?}, omitidas?[{canon, motivo}]}`. `hilo.js` y G1 de
`ensamblar.py` exigen ≥ 1 tarjeta `mapa` con los 22 que destaca al departamento (el perfil de un grupo no). El hilo
entregado lleva el bloque `perfil` en `hilo.json` y `datos.json` conserva `denominador` y `calculo` de las tasas.

## Video: el modo se detecta solo

`video.py preparar` ve `modo: perfil` + `perfil.tipo: departamento` y escribe en `video.json`:
`departamento {codigo, nombre, alias, puestos {<cifra|T<n>>: {puesto, de: 22, orden, valor}}, canon_version}`,
`palabra_clave` (nombre + alias), `piso_s: 61` y `serie: "departamentos"`; el digesto suma «Modo departamento». Los
puestos calculados respaldan en V2 «N.º 17 de 22». Escena `ranking` con `ventana: true` y `destacar: "GTxx"`: los 2
primeros, una fila «…», el departamento con sus vecinos y «N.º X de 22» (`video/ranking.html`, `ranking_ventana` en
`video.py`); sin tipo de escena nuevo.

## Gates D (`departamentos.py`, llamados desde `video.py`)

| Gate | Qué comprueba | Dónde |
|---|---|---|
| D1 | el nombre (o alias) suena en la voz del gancho en ≤ 3 s (V19 con max_s 3) | `guion --check` (estimado), `tiempos` (real) |
| D2 | el nombre se lee en la pantalla del gancho, o el visual es `lugar` con su código | `guion --check` |
| D3 | 1.ª línea de TikTok, Instagram, Facebook y título de Shorts con el nombre; «Para alguien de <depto>» en algún caption; aviso sin `#<Depto>` | `guion --check`, `entregar` |
| D4 | cada tarjeta con el valor del departamento trae el del país, misma fuente y periodo | `guion --check` |
| D5 | dimensiones = canon en fuente y año (desvío sin `motivo` falla; con motivo, aviso; faltante sin `omitidas`, falla) | `guion --check` |
| D6 | el puesto dicho = el calculado; tasas por habitante con denominador INE del mismo año | `guion --check` |
| D7 | escena `mapa` (destaca al depto) y `ranking` con ventana, de tarjetas distintas | `guion --check` |
| D8 | duración real ≥ 61 s (`piso_duracion`) | `tiempos` |
| D9 | la frase final nombra el departamento (F4 sigue prohibiendo pedir compartir) | `guion --check` |

Con el modo activo, V19 genérico no corre (D1–D3 lo sustituyen). `entregar` añade `serie`, `sujeto` y `departamento`
al guion de entrega; `memoria.py --video` registra `sujeto`, `serie` y `codigo`, y `departamentos.py --tablero` los lee.

## Prueba

`make departamento-fixture`: `sesiones/_fixture_perfil/` (Huehuetenango con cifras de MAQUETA, 8 tuits, dos mapas de
los 22) → `sesiones/_fixture_departamento/` (guion, ganchos y selección fijos; corto, voz falsa) → 9:16 y 4:5 ≥ 61 s.
Los negativos de D1–D9 y G1 están en `scripts/test.sh`.
