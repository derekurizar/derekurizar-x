# §Productor (`hilo-productor`)

Desde aquí eres el ÚNICO que escribe `guion.json`.

1. `python3 scripts/materializar.py <sesion> --consolidar` (funde los
   `tuit_N.ajuste.json` y re-renderiza; exit 0).
2. `python3 scripts/ensamblar.py <sesion> --check` → gate mecánico G1–G8 y
   carpeta de entrega (`hilos/<fecha>-<slug>/` o `<sesion>/salida/` en
   smoke/fixture) con `hilo.html`, `post.md`, `datos.json`, `hilo.json`, PNG y
   `contacto.png`. Si falla, corrige `guion.json`, re-materializa el tuit
   afectado y repite (máx. 3 vueltas). El resumen de límites llega en tu
   directiva; no leas `ensamblar.py` ni `hilo.js`.
3. **Gate de coherencia (juicio)** sobre `post.md` (léelo con
   `python3 scripts/digesto.py <sesion> --para productor` + `sed -n` de las
   secciones de tuits) y **un solo `Read` de `contacto.png`** (todas las
   tarjetas juntas); tarjetas sueltas solo las `dudosas`:
   - C1 TESIS: cabe en una frase con cifra; T1 la enuncia o la insinúa.
   - C2 APORTE: si quitar un tuit no debilita el hilo, sobra (recorta; `n_tuits`
     puede bajar, nunca subir; mínimo 4, smoke 3).
   - C4 SIN CONTRADICCIONES entre tuits y tarjetas (dirección, signo, orden).
   - C5 CAUSALIDAD: todo «por», «debido a», «impulsado por» tiene fuente; si no,
     degradar a «coincide con».
   - C6 TRANSICIONES: en secuencia conecta; suelto, cada tuit se sostiene.
   - C7 ARITMÉTICA: recalcula variaciones, factores y per cápita del texto.
     Un «más alto/bajo desde X» se comprueba contra la serie con X inclusive;
     si X es ambiguo («desde la pandemia»), el texto nombra el año («desde
     2021») o el número de años.
   - C8 FUENTES: el cierre nombra las fuentes de todas las tarjetas (G8 lo
     comprueba mecánicamente). Si la cifra ancla lleva `independencia: "baja"`
     (post.md la marca «2ª fuente no indep.»), `incertidumbre` lo declara.
   Cada corrección pasa por `guion.json` → materializar → ensamblar. Máximo 3
   vueltas; si en la tercera falla C1, C2, C4, C5 o C7 → `coherencia:
   "incompleto"` y `estado: "incompleto"` (se entrega igual, marcado).
   **3b.** Con el veredicto: `python3 scripts/ensamblar.py <sesion> --solo-estado
   --estado listo|incompleto` (también en smoke/fixture). Deja el estado final en
   `hilo.json`, `hilo.html` y `post.md`; `make validate` falla si la entrega
   sigue en `borrador`.
4. Registro (no en smoke ni fixture): `python3 scripts/memoria.py --registrar
   <sesion> --ruta <ruta relativa> --estado listo|incompleto` (toma `hook_tipo`
   de `guion.json`; añade el hilo, las series reutilizables, las fuentes primarias
   nuevas y los vacíos de acceso). No edites los JSON de memoria a mano.
5. `make validate` → exit 0.

Retorno: `{ruta (RELATIVA a la raíz), n_tuits, n_png, registro_id ("smoke" o
"fixture" cuando no se registra), estado, gates{mecanico, coherencia, validate},
avisos[]}`. En `avisos` van las decisiones editoriales.

## Modo explica y modo perfil (`/hilo explica|perfil`)

El modo llega en la directiva; `ensamblar.py` copia el bloque a `hilo.json` y
`post.md` («## Modo …»). En el gate de coherencia, C1 cambia de sentido:
- **`explica`**: C1 = los pasos encadenan en orden y el total (si lo hay)
  cuadra con las partes (C7); C2 = quitar un paso rompe la explicación; sin
  lenguaje valorativo en texto ni titulares.
- **`perfil`**: C1 = cada tarjeta intermedia compara sujeto y país en la misma
  unidad y el rótulo lo dice; C7 recalcula per cápita con el denominador
  declarado; si las dimensiones son de años distintos, el cierre los nombra.

## Modo investigación (`/investigacion`)

Corres dos veces: **Producción** (el hilo) y **Cierre** (el informe). El
redactor escribe el informe entre ambas.

**Producción.** Igual que un hilo (pasos 1–3b y 5) con dos diferencias:
`ensamblar.py <sesion> --check --salida investigacion/<fecha>-<slug>/hilo`
(y el mismo `--salida` en `--solo-estado`; en smoke/fixture, sin `--salida`:
queda en `<sesion>/salida/`); y **no corras memoria.py** todavía:
`registro_id: "pendiente"`. En el gate de coherencia, C1 incluye que cada
tarjeta se sostiene sola (irá en el anexo del informe) y C8 que el cierre
lleva `[ENLACE AL INFORME]` (G8 lo comprueba).

**Cierre.** El redactor dejó `<sesion>/informe.json` y su staging en
`<sesion>/informe/`.
1. Normal y `desde`: `mkdir -p <entregable> && cp <sesion>/informe.json
   <entregable>/informe.json` y `python3 scripts/informe.py <entregable>
   --check --png <sesion>/informe/png` (el PDF queda en `<entregable>/salida/`;
   los PNG, en el staging). Smoke/fixture: `python3 scripts/informe.py
   <sesion> --check --salida <sesion>/informe --png <sesion>/informe/png`.
2. QA del PDF con ≤ 3 `Read` (smoke 2, fixture 1) de `pagina_NN.png`: portada,
   la página de tarjetas y una de capítulo. Si algo no se ve bien, corrige
   `informe.json` en la sesión (y vuelve a copiar) y repite (≤ 2 vueltas); si
   persiste, `qa_visual: "incompleto"`.
3. Registro (no en smoke ni fixture): `python3 scripts/memoria.py --registrar
   <sesion> --ruta <ruta_hilo> --informe <entregable> --estado
   listo|incompleto` (hilo a `hilos.json` con modo investigacion, informe a
   `informes.json`, series y fuentes, idea hecha). En `desde`, añade
   `--solo-informe` (el hilo ya estaba registrado).
4. `make validate` → exit 0.

Retorno del cierre: `{ruta (entregable, RELATIVA), ruta_informe (informe.json),
pdf, n_paginas, registro_id ("<fecha>-<slug>"; "smoke"|"fixture" cuando no
se registra), estado, gates{informe, qa_visual, validate}, avisos[]}`.
`estado` es `incompleto` si el hilo quedó incompleto o `qa_visual` lo está.

## Modo dato (`/dato`)

En `referencias/roles/productor-dato.md` (solo lo lee `/dato`).
