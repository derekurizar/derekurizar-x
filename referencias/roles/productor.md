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

## Modo dato (`/dato`)

Hay una sola tarjeta y no hay visualistas: el QA visual lo haces tú. Eres el
único que escribe `guion.json` desde el principio.

0. **Fixture** (solo si la directiva lo dice): `mkdir -p <sesion> && cp -R
   sesiones/_fixture_dato/. <sesion>/` y pon `fixture: true`, `smoke: true`,
   `fecha` y `sesion_dir` en `encuadre.json` y `guion.json` copiados.
1. **QA visual** (de `referencias/roles/visualista.md` y la checklist de
   `graficos.md`): `python3 scripts/materializar.py <sesion> --tuit 1` (exit
   0 = pasa R1–R6) → **un solo `Read`** de `<sesion>/visuales/tuit_1.png` por
   iteración → correcciones SOLO en `<sesion>/visuales/tuit_1.ajuste.json` →
   repetir. Máximo 3 iteraciones (smoke/fixture 1). Cambio de tipo:
   `--forzar-plantilla <otra>`. Si queda dudoso, `dudoso: true` y nota en
   `avisos`.
2. `python3 scripts/materializar.py <sesion> --consolidar`.
3. `python3 scripts/ensamblar.py <sesion> --check` (modo dato por
   `guion.tipo`): gate mecánico y carpeta `datos/<fecha>-<slug>/` (o
   `<sesion>/salida/` en smoke/fixture) con `dato.png`, `tarjeta.html`,
   `dato.html`, `post.md`, `datos.json`, `dato.json`. Si falla, corrige
   `guion.json`, re-materializa y repite (máx. 3 vueltas).
4. **Gate de coherencia reducido** sobre `post.md` (`digesto.py --para
   productor` + `sed -n`) y el último PNG que ya leíste (no hay
   `contacto.png`; no gastes otro `Read`):
   - C1 TESIS: tarjeta (titular), `dato.titular` y texto cuentan el MISMO dato,
     con la misma dirección y periodo. Tapa el kicker: ¿el titular dice de qué
     habla la tarjeta (el sujeto)? Si no, corrige el titular.
   - C5 CAUSALIDAD: «por», «debido a», «impulsado por» solo con fuente; si no,
     «coincide con».
   - C7 ARITMÉTICA: recalcula desde los valores crudos todo porcentaje, factor
     o per cápita del texto y de la tarjeta (`contexto`, `comparacion`,
     píldora de `antes-despues`); p. ej. `cifra.valor` 102 y
     `comparacion.valor` 67 dan «52 % más», no «54 % más». Un «más alto/bajo
     desde X» se comprueba contra la serie con X inclusive; si X es ambiguo
     («desde la pandemia»), el texto nombra el año o el número de años.
   - INDEP: si la cifra elegida lleva `independencia: "baja"` (post.md la
     marca «2ª fuente no indep.»), `incertidumbre` lo declara.
   - ALT: el `alt_text` describe lo que el PNG muestra (tipo, cifra con unidad
     y periodo, fuente).
   Cada corrección pasa por `guion.json` → materializar → ensamblar. Máximo 3
   vueltas; si en la tercera falla C1, C5, C7, INDEP o ALT → `coherencia:
   "incompleto"` y `estado: "incompleto"`.
5. `python3 scripts/ensamblar.py <sesion> --solo-estado --estado
   listo|incompleto` (también en smoke/fixture).
6. Registro (no en smoke ni fixture): `python3 scripts/memoria.py --registrar
   <sesion> --ruta <ruta relativa> --estado listo|incompleto` → escribe
   `memoria/datos.json` (detecta `guion.tipo`); series y fuentes primarias van
   a `memoria/fuentes.json`; el banco de ideas no se toca.
7. `make validate` → exit 0.

Retorno: `{ruta (RELATIVA), n_png: 1, iteraciones_visual, dudoso,
plantilla_final, registro_id ("smoke"|"fixture" cuando no se registra), estado,
gates{mecanico, coherencia, validate}, avisos[]}`; en fixture añade
`resumen{titular, cifra_id, hook_tipo, plantilla, paleta, texto, alt_text}`
copiado de `guion.json`.

### Modos vs · mapa · antes

El modo llega en la directiva; `ensamblar.py` copia el bloque del modo a
`dato.json` y `post.md` («## Modo …»). En el gate de coherencia añade:
- **`vs`**: C7 recalcula la brecha entre países desde los valores crudos; la
  `nota` nombra la fuente común y el año; en el PNG Guatemala está destacada.
- **`mapa`**: en el PNG los extremos están rotulados y el titular nombra la
  brecha; C7 recalcula la razón máximo/mínimo y al menos una tasa desde
  numerador y denominador (`digesto.py --serie` no aplica: usa las partes).
- **`antes`**: C7 recalcula el factor o el porcentaje entre los dos años; si es
  dinero corriente, la `nota` lo declara.
