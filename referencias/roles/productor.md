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
   - C8 FUENTES: el cierre nombra las fuentes de todas las tarjetas (G8 lo
     comprueba mecánicamente).
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
