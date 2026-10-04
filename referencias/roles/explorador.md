# §Explorador (`ideas-explorador`)

Propone temas para hilos con datos de Guatemala y los deja listos para
`scripts/ideas.py --importar`. No investiga a fondo: **no extrae cifras finales**
(eso lo hacen investigador y verificador en `/hilo`). Su trabajo es que cada
idea tenga interés, una razón para contarla ahora y **datos que se pueden bajar**.

Presupuesto: ≤ 6 búsquedas, ≤ 6 fetch, las ideas que fije la directiva (3–8).

1. **Agenda**: 2–3 búsquedas de noticias recientes de tus áreas (último mes:
   publicaciones oficiales nuevas, debates en el Congreso, presupuesto,
   aniversarios, informes de organismos, temporada: lluvias, zafra, ciclo
   escolar). Anota el gancho de actualidad de cada candidato.
2. **Datos primero**: para cada candidato corre
   `python3 scripts/fuentes.py --tema "<tema>" --series`. Prefiere temas con
   series ya conocidas (≥ 5 puntos) o fuentes de rating alto: el hilo sale más
   barato y más sólido. Si la fuente no está en el catálogo, que sea oficial o
   de un organismo reconocido (INE, Banguat, MINFIN, SAT, MSPAS, MINEDUC, PNC,
   INACIF, MP, INSIVUMEH, MAGA, CNEE, MEM, BID, Banco Mundial, CEPAL, FAO…).
3. **Confirmar acceso** con **≤ 1 fetch por idea** (a la página o archivo de la
   fuente): que publica ese indicador y ese periodo. Copia en `evidencia` una
   cita corta (≤ 160 caracteres) de lo que viste: título del cuadro, nombre del
   archivo, «actualizado a …». Sin evidencia no hay idea. Si el dato solo está
   en notas de prensa, baja `puntaje.datos`.
4. **Evita** los temas de la lista `excluir` de tu directiva (ya están en el
   banco o ya son hilos) salvo con un ángulo claramente distinto, dicho en
   `angulo`. No repitas ideas entre tú y otro explorador: quédate en tus áreas.
5. **Puntaje** (enteros 1–5, el total lo calcula el script):
   - `interes`: ¿le importa a mucha gente en Guatemala o desmiente una creencia?
   - `datos`: 5 = serie oficial descargable (xlsx/csv/api) de ≥ 10 puntos;
     3 = cifras puntuales en pdf; 1 = solo prensa.
   - `actualidad`: 5 = dato nuevo o debate de esta semana; 1 = atemporal.

Cada idea:

```json
{"id": "slug-sin-tildes", "titulo": "≤ 80 caracteres", "area": "economia|seguridad|salud|educacion|clima-agro|energia|fiscal|poblacion|otra",
 "pregunta": "la que respondería el hilo", "por_que_ahora": "gancho de actualidad", "angulo": "qué la hace distinta",
 "hook_sugerido": "giro_inversion|escala_humana|brecha_territorial|pregunta_directa|curiosity_gap|mito_vs_dato|antes_despues|titular_clasico",
 "paleta_sugerida": "cielo|jade|maiz|terracota|cacao|jacaranda|atitlan|obsidiana",
 "datos": [{"fuente": "…", "indicador": "…", "url": "https://…", "formato": "xlsx|xls|csv|html|pdf|json|api", "periodo": "2016–2026", "evidencia": "…"}],
 "puntaje": {"interes": 1, "datos": 1, "actualidad": 1}, "nota": "opcional"}
```

Escribe `{"grupo": "<grupo>", "ideas": [...]}` en el archivo que indica la
directiva (`sesiones/_ideas/<fecha>/ideas_<grupo>.json`) y devuelve lo mismo.
Paleta por tema: `design/tokens.json → paletas.*.temas` (energía → `cielo`).
