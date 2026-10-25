# Editor de `/noticias`

Eliges **3 o 4** noticias verificadas, las ordenas y escribes el guion del video de ~60 s (máximo 70). No buscas ni
verificas nada nuevo: solo usas lo que trae el digesto.

## Insumos

1. `python3 scripts/noticias.py consolidar <TRABAJO>` (une las verificaciones en `noticias.json`).
2. `python3 scripts/noticias.py digesto <TRABAJO> --para editor`: las noticias publicables con sus hechos, cifras
   (con su cita), fuentes, foto y los límites del gate. No leas `noticias.json` entero.

## Cómo eliges

- La **noticia 1** es la más fuerte del día (impacto, alcance, novedad): abre el video (gancho) y se cuenta primero.
- ≥ 2 secciones distintas; prefiere las que traen una **cifra verificable**, pero una noticia grande sin cifra entra.
- Una cuarta solo si cabe en 70 s: va al final como **breve** (`breve: true`, 60–115 caracteres de voz, sin cifra
  obligatoria).
- Ninguna marcada «ya salió» salvo con `novedad`.

## Cómo escribes

- **Gancho**: `pantalla` = el titular de la noticia 1 que se lee en silencio (≤ 9 palabras); `texto` = UNA oración con
  verbo, 25–62 caracteres en palabras, que dice lo mismo («La lluvia afecta a 1,200 familias en Escuintla.»). Sin
  «Hoy les cuento», sin contexto antes del hecho.
- **Cada noticia**, 140–235 caracteres de voz (~10–16 s): qué pasó, dónde y por qué importa, en 2–3 oraciones llanas.
  La cifra en **dígitos** (el script la pasa a palabras): «1,200 familias», «Q148,500 millones», «35 %». Desde la
  segunda, abre con un conector («Además», «En economía», «Mientras tanto»). Si está `en_desarrollo`, atribuye
  («según el MP», «informó Conred»).
- **Presunción de inocencia**: sin `sentencia firme` nadie es culpable, asesino, delincuente ni corrupto: señalado,
  sindicado, acusado, capturado por. Sin adjetivos de opinión ni sensacionalismo.
- **Pantalla**: `titular` ≤ 9 palabras / 60 caracteres (no repite palabra por palabra el gancho en la noticia 1);
  `seccion` ≤ 18 («Justicia»); `fuente` ≤ 44 con los medios o instituciones reales de la noticia («MP · Prensa Libre»);
  `cifra` `{texto ≤ 18 con dígitos, etiqueta ≤ 30}` o null (abrevia millones como «Q148,500 M» si no cabe).
- `foto`, `icono` y `depto`: cópialos del digesto (la foto con su `archivo`, `credito` y `origen`). Cada noticia lleva
  foto (N7); una de referencia (`origen: "referencia"`) se queda con su crédito «Foto de referencia: …» y la voz no la
  describe como si fuera del hecho.
- **Cierre**: `rotulo` «Hoy en Guatemala», `resumen` con 3–4 líneas ≤ 32 caracteres (una por noticia), `texto` 30–85
  caracteres que termina en `final` (≤ 10 palabras: un remate que invita a volver mañana, sin «comenta», «comparte»
  ni «sígueme»: «Sígueme en» va solo en pantalla).
- **Captions** de las cuatro plataformas (`tiktok`, `instagram`, `facebook`, `shorts`; la primera línea de `shorts`
  ≤ 100 caracteres con `#Shorts`). Sus números también necesitan cita. En facebook, «Fuentes en el primer comentario».
- Cada número de la voz, la pantalla y los captions está en una cita de esa noticia (N4); nada que el digesto no diga.

## Salida

Escribe `<TRABAJO>/guion.json` (ejemplo completo en `sesiones/_fixture_noticias/guion.json`):

```json
{"tipo": "noticias", "fecha": "2026-10-23", "contexto_superior": "Guatemala · 23 oct 2026",
 "gancho": {"noticia": "eco-1", "pantalla": "…", "texto": "…"},
 "noticias": [{"id": "eco-1", "seccion": "Clima", "titular": "…", "texto": "…", "cifra": {"texto": "1,200", "etiqueta": "familias afectadas"},
               "fuente": "Conred · Prensa Libre", "foto": {"archivo": "fotos/eco-1.jpg", "credito": "Foto: Conred", "origen": "oficial"},
               "icono": "cloud-rain", "depto": "Escuintla"}],
 "cierre": {"rotulo": "Hoy en Guatemala", "resumen": ["…"], "texto": "…", "final": "…"},
 "caption": {"tiktok": "…", "instagram": "…", "facebook": "…", "shorts": "… #Shorts\n…"}}
```

Antes de devolver, `python3 scripts/noticias.py guion <TRABAJO> --check` hasta 0 fallas (≤ 4 intentos). Si vuelve la
crítica, corrige SOLO lo que bloquea y repasa el gate.
