#!/usr/bin/env python3
"""/video: un hilo entregado → video vertical 1080×1920 narrado (TikTok / Reels / Facebook).

La sesión principal coordina (el guion lo orquesta el Workflow `video`); este script hace todo lo determinista y
los gates V1–V10 (referencias/flujo-video.md). La voz y Scribe salen del MCP de ElevenLabs; la música viene SOLO
del catálogo fijo design/musica/catalogo.json y los efectos SOLO de design/sfx/catalogo.json (/video nunca genera
música ni efectos).

Subcomandos (TRABAJO = sesiones/<slug>/video):
  preparar <hilo|ultimo> [--duracion corto|medio|largo] [--musica ID] [--trabajo DIR] [--permitir-borrador] [--sin-rotacion]
        crea TRABAJO, elige la música y escribe digesto.md para el guionista (también lo imprime); medio por defecto
  ganchos TRABAJO --check      candidatos del agente video-gancho (ganchos.json): 4–5 familias distintas, R1–R10 cada uno
  ganchos TRABAJO --usar [ID] [--segundo ID]   el elegido (de seleccion.json si no se da) → escena 1 de guion.json
  guion TRABAJO --check        gate V1–V5 + V9 (estructura de retención, gancho R2–R10) sobre guion.json v2 → locucion.json
  voz TRABAJO [--pendientes | --solo N,N]   imprime JSON con la voz y el texto de cada nodo TTS (--pendientes: solo los que faltan o cambiaron)
  variante TRABAJO [--cerrar]  versión B con el segundo gancho: variante_b/ con la voz y los clips de las demás escenas;
        imprime solo el nodo de voz de la escena 1; --cerrar copia su video a salida/video_b.mp4
  descargar TRABAJO --estado ESTADO.json [...]   el JSON guardado de creative_get_flow_run_status (voz y Scribe) →
        audio/voz_N.mp3 (por el prompt), palabras_N.json (por el id de generación) y creditos.json (créditos cobrados)
  descargar TRABAJO --voz URLS.json | --palabras URLS.json   respaldo: {"<n>": "<url>"} → voz_N.mp3 | palabras_N.json
  voz-falsa TRABAJO            tono por palabra + tiempos sintéticos (fixture, 0 créditos)
  tiempos TRABAJO              atempo 1.1, alineación por palabra (V6), eventos y efectos por escena, V10 → escenas.json
  grabar TRABAJO [--fps 30] [--solo 1,3] [--formato 4:5]   clips por escena (Playwright) + V7 + V13 (zona segura); 4:5 = 1080×1350 para el feed en clips_4x5/
  montar TRABAJO [--sin-bucle]   voz + música con ducking + efectos + loudnorm en 2 pasadas (V8), cierre en bucle (el primer
        cuadro del gancho al final, con fundido), subtitulos.srt, caption.md, portada.png y portada_cierre/giro.png
  revisar TRABAJO [--formato 4:5]   revision/contacto.png (cifra completa · pico del foco · final de cada escena) y linea_tiempo.png
  entregar TRABAJO [--salida DIR]   copia a <hilo>/video/ (o DIR) con guion.json de entrega
  musica                       lista el catálogo fijo con cuántas veces y cuándo se usó cada pista

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import array
import datetime
import difflib
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
import wave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402

VOZ = {"voice_id": "8mBRP99B2Ng2QwsJMFQl", "nombre": "El Faraon 4", "modelo": "eleven_multilingual_v2", "idioma": "es"}
REDES = [{"red": "tiktok", "nombre": "TikTok", "handle": "@derekurizargt"},
         {"red": "instagram", "nombre": "Instagram", "handle": "@derekurizargt"},
         {"red": "facebook", "nombre": "Facebook", "handle": "Derek Urizar"},
         {"red": "youtube", "nombre": "YouTube", "handle": "@derekurizar"},
         {"red": "x", "nombre": "X", "handle": "@DerekUrizar"}]
# un maestro 9:16 sirve en las cuatro apps (misma zona segura, gate V13) y el 4:5 en el feed; cada plataforma lleva su
# texto (caption.md). Shorts admite hasta 3 min: un video más largo se publica en YouTube como video normal.
PLATAFORMAS = (("tiktok", "TikTok"), ("instagram", "Instagram Reels (y feed con video_4x5.mp4)"),
               ("facebook", "Facebook Reels (y feed con video_4x5.mp4)"), ("shorts", "YouTube Shorts"))
SHORTS_MAX_S, SHORTS_TITULO = 180, 100
VELOCIDAD = 1.1      # la voz se acelera con atempo (sin cambiar el tono); los tiempos de Scribe se dividen igual
CPS = 15.5           # caracteres de voz por segundo ya acelerada (medido en la prueba del hilo de crimen)
COLA = 0.7           # aire tras la última palabra de cada escena
COLA_SEGUIDA = 0.3   # (= TRANSICION) dentro de una secuencia de voz: la voz de la escena siguiente arranca donde acabó esta
COLA_CIERRE = 2.8    # «Sígueme en» se queda en pantalla tras la pregunta final
# secuencias de voz (/historia): grupos de 2–SECUENCIA_MAX escenas consecutivas cuya voz se genera en UN nodo TTS (la
# entonación no se reinicia en cada escena) y se corta después por escena con los tiempos de Scribe (`partir`)
SECUENCIA_MAX, SECUENCIA_CARACTERES = 5, 1200
# narración de corrido (V17–V18; las mismas reglas que H15, H16, H11 y H19 de /historia): el guion trae guion.narracion,
# 3 actos de texto corrido, y cada escena reparte un tramo sin cambiar una palabra; la causalidad vive en el texto
NARRACION_VIDEO = True             # historia.aplicar_extension lo apaga: /historia trae su propio gate (H15–H19)
CONECTORES_MIN_ACTO = {"corto": 1, "prueba": 1}   # conectores causales o temporales por acto; 2 en medio y largo
CONECTORES_MIN_ACTO_DEF = 2
SEGUN_MAX_DATO, SEGUN_MAX_ACTO_DATO = 3, 2
CORTES_MAX_POR_MIN, APERTURAS_ATRIBUIDAS_MAX = 6.5, 1
SIN_SECUENCIA = ()                 # tipos cuya voz se graba sola (la pausa de la adivina es un <break> de su prompt: entra)
# «En Guatemala» ya no se antepone a la voz del gancho (2026-10-23, decisión del usuario): abrir con contexto frena
# menos; «Guatemala» se dice o se lee en los primeros 6 s donde funcione mejor (R6, referencias/ganchos.md)
ANIO = int(os.environ.get("HILOS_ANIO") or datetime.date.today().year)   # R7: «hoy» solo con datos de este año
DURACION_DEFECTO = "medio"   # decisión del usuario (2026-10-20): en 1 min lo informativo «se siente como un resumen y corriendo»
DURACIONES = {  # objetivo en s · tarjetas y golpes (más el gancho y el cierre); «prueba» es solo para el fixture
    "corto": {"s": 60, "tarjetas": (3, 4), "golpes": (1, 2)},
    "medio": {"s": 120, "tarjetas": (6, 8), "golpes": (2, 4)},
    "largo": {"s": 240, "tarjetas": (11, 15), "golpes": (3, 6)},
    "prueba": {"s": 55, "tarjetas": (2, 3), "golpes": (0, 2)},
}
TIPOS = ("gancho", "tarjeta", "golpe", "definicion", "adivina", "mapa", "ranking", "escala", "tiempo", "explica")   # escenas del guion; locucion.json añade "cierre"
CON_TUIT = ("tarjeta", "mapa", "ranking", "tiempo")                # escenas que llevan una tarjeta del hilo (y su golpe)
ESCENAS_TEXTO = ("golpe", "definicion", "adivina")                 # texto cinético (golpe.html); «golpes» en DURACIONES las cuenta a todas
FORMULAS = ("cifra", "contradiccion", "pregunta", "resultado")   # fórmulas de los guiones anteriores al catálogo de ganchos
# catálogo de ganchos (referencias/ganchos.md): la familia es el mecanismo que frena el scroll y el visual lo que se ve
# en el cuadro 0; los escribe el agente video-gancho (4–5 candidatos de familias distintas) y los elige el crítico
FAMILIAS = ("contraste", "paradoja", "lugar", "escala", "tu", "pregunta", "ranking", "resultado")
FAMILIAS_ALIAS = {"cifra": "resultado", "contradiccion": "contraste"}   # la `formula` de un guion viejo → familia
VISUALES = ("cifra", "llenado", "pareja", "figuras", "lugar")
VISUALES_DE = {"contraste": ("llenado", "pareja", "cifra"), "paradoja": ("pareja", "figuras", "cifra"),
               "lugar": ("lugar", "llenado", "cifra"), "escala": ("figuras", "llenado", "pareja"),
               "tu": ("figuras", "llenado", "pareja", "cifra"), "pregunta": ("cifra", "pareja", "llenado"),
               "ranking": ("cifra", "lugar"), "resultado": ("cifra", "pareja", "figuras")}
CANDIDATOS = (4, 5)            # ganchos.json: candidatos por video, de familias distintas
CANDIDATOS_CON_VISUAL = 2      # … y al menos estos con un visual que no sea la cifra sola
ROTACION_FAMILIAS, ROTACION_VISUALES = 2, 1   # R9: la familia no repite la de los últimos 2 videos; el visual, la del último
VISUAL_UNIDAD, VISUAL_ETIQUETA, LUGAR_ETIQUETA = 20, 24, 30
# R3: la voz del gancho no abre con contexto (la institución, el anuncio del tema o «En Guatemala…»): abre con tensión
APERTURAS_PROHIBIDAS = re.compile(
    r"^[¿¡«\s]*(?:en guatemala\b|seg[uú]n\b|de acuerdo con\b|hoy (?:les|te|vamos|hablamos)\b|en este video\b|"
    r"(?:les|te) (?:cuento|voy a contar|explico)\b|hablemos\b|vamos a hablar\b|(?:un|el) (?:informe|estudio|reporte)\b|"
    r"(?:el|la|los|las) (?:sistema|ministerio|gobierno|instituto|congreso|direcci[oó]n|secretar[ií]a|procuradur[ií]a|"
    r"polic[ií]a|ine|mp|organismo)\b)", re.I)
# R7: «hoy» solo con un dato del año en curso
RE_AHORA = re.compile(r"\b(?:hoy|ahora mismo|ahora|actualmente|en este momento|hoy en d[ií]a)\b", re.I)
# V5: «no tenían 2 años», «no tenía ni un año» → «eran menores de 2 años»
RE_EDAD_NEGADA = re.compile(r"\bno\s+ten[ií]an?\s+(?:ni\s+)?(\d+|un|uno|una|dos|tres|cuatro|cinco)\s+a[ñn]os?\b", re.I)
RE_GUATEMALA = re.compile(r"\bguatemal\w*|\bchap[ií]n\w*", re.I)
# cierre (referencias/cierres.md): lo normal es un REMATE de CONSECUENCIA (lo que la cifra le hace a la gente: «34 familias
# ya enterraron a un hijo»; el dato va en las conclusiones, no en la frase final); a veces lo pendiente o quién decide; A
# VECES una PREGUNTA (nunca dos videos seguidos). Decisiones del usuario, 2026-10-23 y 2026-10-24 («terminar con un dato
# no es un buen punch, la consecuencia de un dato sí»): los remates de dato (bucle, cuenta, escala) salen del catálogo.
# En /historia lo normal es el LEGADO: lo que la gente hace hoy con lo que la historia dejó («sus hijos y sus nietos siguen
# tomando Incaparina»; decisión del usuario, 2026-10-26); solo /historia lo usa
CIERRE_FORMAS = {"remate": ("consecuencia", "legado", "pendiente", "quien_decide"),
                 "pregunta": ("elegir", "prediccion", "decidir", "lugar", "porque", "dato_faltante", "experiencia")}
CIERRE_TIPOS = tuple(CIERRE_FORMAS)          # espejo en video.js (W10)
# el mecanismo de la consecuencia: quién lo vive · lo que pierde · el reloj (mientras pasa el video, al día) · lo que
# sigue después para ellos · lo que esperan y no llega
MECANISMOS = ("quien", "perdida", "reloj", "despues", "espera")
FINAL_PALABRAS, FINAL_CARACTERES = 14, 90    # la frase final se lee sola en grande (pantalla B del cierre)
ROTACION_CIERRES = 2                         # F7: la forma no repite la de los últimos 2 videos (salvo consecuencia y
                                             # legado, las normales; la consecuencia rota su mecanismo, que no repite el del último)
# F6: el sujeto de la consecuencia es gente (o lo suyo: su casa, su escuela, su milpa), no una tasa ni una institución
HUMANO = re.compile(r"\b(?:familias?|hogar(?:es)?|ni[ñn][oa]s?|beb[eé]s?|hij[oa]s?|madres?|padres?|mam[aá]s?|pap[aá]s?|"
                    r"mujer(?:es)?|hombres?|j[oó]venes|adolescentes?|personas?|gente|vecin[oa]s?|comunidad(?:es)?|pueblos?|"
                    r"aldeas?|estudiantes?|alumn[oa]s?|maestr[oa]s?|trabajador(?:a|as|es)?|agricultor(?:a|as|es)?|"
                    r"campesin[oa]s?|productor(?:a|as|es)?|pacientes?|enferm[oa]s?|conductor(?:a|as|es)?|pasajer[oa]s?|"
                    r"pres[oa]s?|reos?|v[ií]ctimas?|migrantes?|abuel[oa]s?|ancian[oa]s?|guatemaltec[oa]s?|chapines|"
                    r"usuari[oa]s?|clientes?|vendedor(?:a|as|es)?|comerciantes?|due[ñn][oa]s?|inquilin[oa]s?|"
                    r"m[eé]dicos?|enfermer[oa]s?|polic[ií]as?|agentes?|jornaler[oa]s?|cada (?:uno|una|d[ií]a|hora)|"
                    r"niet[oa]s?|generaci[oó]n(?:es)?|lector(?:a|as|es)?|fieles|descendientes?|hereder[oa]s?|seguidor(?:a|as|es)?|"
                    r"consumidor(?:a|as|es)?|comprador(?:a|as|es)?|alumnado|emplead[oa]s?|obrer[oa]s?|panader[oa]s?)\b", re.I)
PASADO = re.compile(r"(?:o|aron|ieron|aba|aban|ia|ian)$")   # F6 legado: el verbo va en presente («siguen», «abren»), no «abrieron»
# F8: un remate no afirma lo que el hilo no dice: ni fatalismo («no hay nada que hacer») ni el futuro de una pérdida
FATALISMO = re.compile(r"no hay nada que|nada que (?:se )?(?:pueda|puede) hacer|nada que hacer|nadie (?:hace|har[aá]|hizo) "
                       r"nada|no tiene soluci[oó]n|sin soluci[oó]n|nunca va a cambiar|nunca cambiar[aá]|es inevitable|"
                       r"no se puede hacer nada|a nadie le importa|est[aá]n condenad", re.I)
FUTURO = re.compile(r"\b\w{3,}(?:ar|er|ir)(?:[aá]n|[aá]s|[aá]|emos)\b", re.I)   # «perderán», «morirá», «enterrarán»
# F4: cebo de interacción (Meta baja la distribución de lo que pide comentar, etiquetar o compartir, también en el audio)
CEBO = re.compile(r"\b(?:comenta\w*|etiquet\w*|menciona a\b|comparte\w*|dale (?:like|me gusta)|deja (?:tu|un) comentario|"
                  r"escribe (?:s[ií]|no|un|una|tu|\d)\b|te le(?:o|emos)\b|cu[eé]ntame\w*)", re.I)
# F5: en un tema sensible la pregunta no expone al espectador (víctima, familia, intimidad): quien responde miente o calla
TEMA_SENSIBLE = re.compile(r"c[aá]rcel|\bpres[oa]s\b|penal|penitenciari|homicid|asesin|extorsi|violen|secuestr|abuso|"
                           r"violaci|sexual|embaraz|\bmadres?\b|migra|deport|suicid|desaparec|\btrata\b|narco|pandill", re.I)
EXPONE = re.compile(r"\b(?:tu|tus) (?:casa|familia|mam[aá]|madre|pap[aá]|padre|hij[oa]s?|pareja|herman[oa]s?|cuerpo|salud)\b|"
                    r"\b(?:has|hayas|fuiste|estuviste|te han|te ha|conoces a)\b|alguna vez", re.I)
# F3: palabras que no anclan la frase final al tema (están en cualquier video)
GENERICAS = set("personas persona guatemala guatemaltecos guatemalteca pais nacional total datos cifra cifras porcentaje "
                "numero numeros millones miles junio julio enero febrero marzo abril mayo agosto septiembre octubre noviembre "
                "diciembre semana semanas meses dias anual cuanto cuantos cuantas mucho muchos menos crees tienes".split())
ENLACES = {"pero": r"pero|sin embargo|aunque|solo que|en cambio|aun así",
           "por_eso": r"por eso|así que|entonces|el resultado|de ahí que|la consecuencia",
           "y": r"y|además|también|encima|más aún"}
RE_ENLACE = {k: re.compile(r"^[¿¡]?\s*(?:%s)\b" % v, re.I) for k, v in ENLACES.items()}
CARACTERES = {"gancho": (30, 130), "tarjeta": (40, 230), "golpe": (20, 110), "definicion": (30, 160), "adivina": (40, 200),
              "mapa": (40, 230), "ranking": (40, 230), "escala": (30, 170), "tiempo": (40, 230), "explica": (40, 230),
              "cierre": (40, 200)}  # voz ya en palabras
GOLPE_PALABRAS, GOLPE_CARACTERES = 6, 40
TERMINO_PALABRAS, TERMINO_CARACTERES, DEFINICION_CARACTERES = 3, 24, 90   # escena definicion
# la voz de una definición avisa que viene un concepto ANTES de decir el término («Para entenderlo mejor: la Fase 3+…»)
ANUNCIOS_DEFINICION = (r"para entender\w*", r"para explicar\w*", "te explico", r"explicart\w*", "antes de seguir", "un concepto",
                       "que es", "que significa", "que quiere decir", "para que quede claro", "aclaremos", "primero")
PREGUNTA_CARACTERES, OPCION_CARACTERES = 70, 14                           # escena adivina: 3 opciones con cifra
# la adivina pide al espectador que pause para responder, entre las opciones y la respuesta («Pausa el video y piénsalo.»)
PAUSA_ADIVINA = (r"pausa\w*", r"deten\w*", r"para el video", r"piensa\w*", r"respond\w*", r"contest\w*")
# la promesa es una oración propia: no empieza con un conector suelto ni usa la muletilla que se copiaba de las guías
# («Y al final te digo cuántas…»); vale una familia variada («Quédate hasta el final y sabrás…», «Al final vas a ver…»)
PROMESA_CONECTOR = re.compile(r"^[¿¡«\s]*(?:y|e|pero|así que|asi que|entonces|aunque|además|ademas)\b", re.I)
PROMESA_PROHIBIDA = re.compile(r"al final te (?:lo )?(?:digo|cuento)|te lo (?:digo|cuento) al final", re.I)
FRASES_USADAS_VIDEOS = 6   # videos anteriores cuyas frases (promesa, gancho, aperturas, pregunta) ve el digesto
# cierre en dos pantallas: conclusiones (resumen) y luego la pregunta con «Sígueme en»; la voz necesita este tiempo antes
# de la pregunta para que las conclusiones se lean
RESUMEN_LINEAS, RESUMEN_CARACTERES, CIERRE_ANTES_S = (2, 3), 40, 3.0
PANTALLA_PALABRAS, PANTALLA_CARACTERES, LINEA_PALABRAS, LINEA_CARACTERES = 4, 24, 8, 60
RITMO_MAX_S = 6.0    # V9 (estimado) y V10 (real): hueco máximo entre eventos visuales
# el gancho en 3 segundos: primera oración, promesa (si va en la escena 1) y voz entera, en segundos estimados
GANCHO_ORACION_S, PROMESA_S, GANCHO_VOZ_S = 4.0, 3.0, 7.5
RE_FIN_ORACION = re.compile(r"[.?!:;…](?=\s|$)")
# pausas de la voz: «[pausa]» (0.6 s) y «[pausa larga]» (1.2 s) en el texto del guion; «[pausa adivina]» (2.0 s) la
# mete el script antes de la respuesta de una adivina (da tiempo de pausar el video) → <break> SOLO en el prompt de
# ElevenLabs (Multilingual v2 lo acepta; v3/v4 no); la locución alineada y subtitulada no las lleva. Pocas: la
# documentación avisa de que el exceso acelera o ensucia la voz
RE_PAUSA = re.compile(r"\[pausa(?:\s+(?:larga|adivina))?\]", re.I)
PAUSA_S = {"corta": 0.6, "larga": 1.2, "adivina": 2.0}
BREAK = '<break time="%.1fs" />'
PAUSAS_MAX_ESCENA, PAUSAS_MAX_VIDEO = 1, 3
RE_CIFRA_ID = re.compile(r"\b([a-z]{2,6}-c\d{2,3})(?:\.(serie|partes)\[(-?\d+)\])?")
CONSTANTES_CALCULO = {7, 12, 24, 30, 31, 52, 100, 365, 1000, 1000000}
PUNTAJES = ("gancho", "bucle", "ritmo", "flujo", "escala_humana", "pago", "cierre")   # critica.json (W10 lo coteja con video.js)
TOLERANCIA = 0.10    # V4 (estimada) · V6 avisa con 0.15 sobre la real
MUSICA_VOLUMEN = 0.22  # antes del ducking: bajo la voz queda ≈ 0.075
VOZ_LUFS = -18.0       # la voz se nivela antes de usarla como llave del sidechain
DUCK = "threshold=0.02:ratio=2.5:attack=20:release=450:detection=rms:level_sc=1"
LUFS, LUFS_TOL, TP_MAX = -14.0, 1.5, -1.0
PROHIBIDO_CIERRE = re.compile(r"fuente|en el hilo|guate en datos|s[ií]gue(me|nos)", re.I)
MESES = r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
PLANTILLAS_ANIMADAS = {"antes-despues", "cifra", "barras-v", "linea", "barras-h", "waffle", "dona", "pesas",
                       "mapa", "pendiente", "divergente", "apilada", "embudo", "bullet", "agrupadas", "treemap",
                       "area-apilada", "calor", "cascada", "combinado", "dispersion", "hemiciclo", "linea-tiempo",
                       "multiples", "pictograma", "piramide"}
SFX_DIR = os.path.join(RAIZ, "design", "sfx")
# V11 escucha independiente: whisper.cpp local (brew install whisper-cpp → whisper-cli) con el modelo multilingüe
# «small» (~466 MB) en la caché del proyecto; HILOS_WHISPER apunta a otro modelo
WHISPER_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
WHISPER_DIR = os.path.join(RAIZ, "sesiones", "_descargas", "whisper")
# V12 quietud real: diferencia media de luma (0–255) entre cuadros muestreados; la deriva da 0.1–0.9, una palabra que
# entra 0.3–1.0 y una pantalla congelada < 0.01 (medido sobre la sesión de sequía a 270 px de ancho)
QUIETUD_FPS, QUIETUD_UMBRAL, QUIETUD_S = 4, 0.02, 2.0
# transición de ENTRADA de cada escena (xfade de `montar`), por su papel y su tipo; todas del xfade de ffmpeg
PANTALLA_COMPLETA = ("mapa", "ranking", "escala", "tiempo")   # escenas con página propia a pantalla completa (≤ 1 de cada)
PLANTILLAS_DE = {"mapa": ("mapa",), "ranking": ("barras-h", "mapa"), "tiempo": ("antes-despues", "linea"),
                 "escala": ("waffle", "pictograma")}             # tarjetas que admite cada escena completa (escala: tuit opcional)
RANKING_TOP, RANKING_TOP_DEFECTO = (3, 6), 5                      # puestos de la cuenta regresiva
ESCALA_N, ESCALA_ETIQUETA = (2, 100), 40                          # «K de cada N» con N figuras; etiqueta debajo
TIEMPO_PUNTOS = 9                                                 # puntos máximos en la línea de tiempo
_NOMBRES_DEPTO = None
ANIMACIONES_DIR = os.path.join(RAIZ, "video", "animaciones")   # biblioteca de animaciones a medida (scripts/animaciones.py, K4)
# escena «explica»: una animación que explica el mecanismo (por qué o cómo), con 2–6 pasos que entran cuando la voz los dice
EXPLICA_PASOS, PASO_CARACTERES, TITULO_PALABRAS, TITULO_CARACTERES, BRIEF_CARACTERES = (2, 6), 28, 6, 40, (40, 400)
# el mecanismo que muestra la escena explica (y cada animación del catálogo, meta.mecanismo): una animación solo se
# reutiliza para el mismo mecanismo; si ninguna lo muestra, `animacion: null` y el animador la escribe
MECANISMOS_EXPLICA = {
    "cadena": "causa → efecto lineal: A lleva a B, B a C (sin vuelta atrás)",
    "ciclo": "se retroalimenta: el último paso vuelve a empujar el primero",
    "balance": "entra contra sale: un tanque que sube o baja según cuál pesa más",
    "onda": "se propaga o se contagia: algo que empieza en un punto y viaja",
    "embudo": "etapas que filtran o descartan: entran muchos, quedan pocos",
    "proporcion": "una división: si el denominador no crece, el cociente apenas cambia",
    "umbral": "se acumula hasta cruzar un límite y entonces cambia de estado",
    "cronologia": "eventos con fecha, uno tras otro en el tiempo",
    "exponencial": "crece sobre lo acumulado: cada vuelta suma un porcentaje de todo lo que ya hay (interés compuesto, contagio)",
}
ROTACION_ANIMACIONES = 2   # una animación no repite la de los últimos 2 videos (memoria/videos.json → frases.animaciones)
ICONOS_DIR = os.path.join(RAIZ, "design", "iconos")   # biblioteca FIJA de iconos (scripts/iconos.py --importar, K3)
ICONO_TIPOS = ("gancho", "golpe", "definicion")        # escenas que admiten `icono: "<id>"` (≤ 1, acento sobre la cifra)
# extensiones de los flujos que reusan este gate y estos tiempos con escenas propias (scripts/historia.py): el
# constructor de tiempos de cada tipo propio, f(S, e, ps, pal, fin_voz, dur, g) → (eventos, efectos) o None para seguir
# con el de aquí, y su transición de entrada (clave de TRANSICIONES); SIN_HUECO = tipos sin el hueco estimado de V9
CONSTRUCTORES, TRANSICION_DE = {}, {}
# tras el constructor de CUALQUIER escena: f(S, e, ps, pal, fin_voz, dur, g, ev, sfx) → (ev, sfx) (historia: rótulo de
# acto, presupuesto de efectos y transición dentro de una secuencia)
POST_CONSTRUCTORES = []
SIN_HUECO = ("cierre", "explica")


def animaciones_catalogo():
    """{id: entrada} de video/animaciones/catalogo.json (vacío si aún no hay biblioteca)."""
    ruta = os.path.join(ANIMACIONES_DIR, "catalogo.json")
    return {a["id"]: a for a in leer(ruta).get("animaciones") or []} if os.path.exists(ruta) else {}


def animaciones_recientes(slug_actual):
    """Las animaciones de las escenas explica de los últimos ROTACION_ANIMACIONES videos (memoria/videos.json →
    frases.animaciones; un registro anterior a ese campo se completa con los `usos` del catálogo)."""
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    regs = [v for v in (leer(vids)["videos"] if os.path.exists(vids) else []) if v.get("slug") != slug_actual]
    regs = sorted(regs, key=lambda v: (v.get("fecha", ""), v.get("id", "")))[-ROTACION_ANIMACIONES:]
    cat = animaciones_catalogo()
    out = []
    for v in regs:
        fr = v.get("frases") or {}
        ids = fr["animaciones"] if "animaciones" in fr else [k for k, a in cat.items() if v.get("slug") in (a.get("usos") or [])]
        out += [x for x in ids if x and x not in out]
    return out


def lineas_animaciones(recientes, sin_rotacion=False):
    """El bloque del digesto para la escena explica: los mecanismos, la biblioteca por mecanismo y las recientes."""
    cat = animaciones_catalogo()
    out = ["- Escena `explica`: PRIMERO nombra el `mecanismo` del fenómeno (qué hace, no el tema): " +
           " · ".join("%s (%s)" % (k, v) for k, v in MECANISMOS_EXPLICA.items()) + ".",
           "- Reutiliza una animación SOLO si muestra ESE mecanismo y no salió en los últimos videos; si no, `animacion: null` "
           "con `brief`: el animador la escribe y queda como plantilla para otros videos (pedir una nueva es lo normal). "
           "`cadena` es solo para causa → efecto lineal, nunca el comodín."]
    for m in MECANISMOS_EXPLICA:
        ids = ["%s (%s; %d–%d pasos)" % (k, v.get("descripcion", ""), *(v.get("pasos") or EXPLICA_PASOS))
               for k, v in sorted(cat.items()) if v.get("mecanismo") == m]
        out.append("  - %s: %s" % (m, " · ".join(ids) if ids else "ninguna aún (pide una nueva con `brief`)"))
    out.append("- Animaciones bloqueadas (salieron en los últimos %d videos): %s"
               % (ROTACION_ANIMACIONES, "(prueba: sin rotación)" if sin_rotacion else ", ".join(recientes) or "ninguna"))
    return out


def explica_mal_armada(e, catalogo, recientes=()):
    """V1/V9 de una escena explica: `mecanismo` declarado, `brief` siempre, animación del catálogo con ese mismo mecanismo
    que no salió en los últimos videos (o null: el animador la escribe), `titulo` corto y 2–6 `pasos`."""
    out = []
    anim, brief = e.get("animacion"), (e.get("brief") or "").strip()
    mec = e.get("mecanismo")
    if mec not in MECANISMOS_EXPLICA:
        out.append("«mecanismo» es uno de %s (qué hace el fenómeno, no el tema)" % "|".join(MECANISMOS_EXPLICA))
    if anim and anim not in catalogo:
        out.append("animación «%s» no está en video/animaciones/catalogo.json (usa una del digesto o deja `animacion: null` con "
                   "un `brief`)" % anim)
    elif anim and mec in MECANISMOS_EXPLICA and catalogo[anim].get("mecanismo") != mec:
        out.append("la animación «%s» muestra «%s», no «%s»: deja `animacion: null` con el `brief` y el animador escribe una "
                   "de «%s» (queda en la biblioteca para otros videos)" % (anim, catalogo[anim].get("mecanismo") or "?", mec, mec))
    elif anim and anim in recientes:
        out.append("la animación «%s» salió en uno de los últimos %d videos: usa otra del mismo mecanismo o deja `animacion: "
                   "null` (el animador escribe una nueva)" % (anim, ROTACION_ANIMACIONES))
    if not BRIEF_CARACTERES[0] <= len(brief) <= BRIEF_CARACTERES[1]:
        out.append("«brief» de %d–%d caracteres (qué se ve y cómo se mueve), también al reutilizar una animación" % BRIEF_CARACTERES)
    tit = (e.get("titulo") or "").strip()
    if not tit or palabras(tit) > TITULO_PALABRAS or len(tit) > TITULO_CARACTERES:
        out.append("«titulo» de 1–%d palabras y ≤ %d caracteres" % (TITULO_PALABRAS, TITULO_CARACTERES))
    ps = e.get("pasos")
    if not (isinstance(ps, list) and EXPLICA_PASOS[0] <= len(ps) <= EXPLICA_PASOS[1]
            and all(isinstance(x, str) and x.strip() and len(x) <= PASO_CARACTERES for x in ps)):
        out.append("«pasos»: %d–%d cadenas de ≤ %d caracteres" % (*EXPLICA_PASOS, PASO_CARACTERES))
        return out
    if anim in catalogo:
        lo, hi = catalogo[anim].get("pasos") or EXPLICA_PASOS
        if not lo <= len(ps) <= hi:
            out.append("la animación «%s» admite %d–%d pasos (llegaron %d)" % (anim, lo, hi, len(ps)))
    raices = {w[:5] for w in _plano(e.get("texto") or "").split() if len(w) >= 4}
    for x in ps:
        claves = [w for w in _plano(x).split() if len(w) >= 4 and w not in STOP and not w.isdigit()]
        if claves and not any(w[:5] in raices for w in claves):
            out.append("la voz no dice el paso «%s» (cada paso entra cuando la voz lo dice)" % x)
    return out


def iconos_catalogo():
    """{id: palabras clave} de design/iconos/catalogo.json, o None si la biblioteca no está importada."""
    ruta = os.path.join(ICONOS_DIR, "catalogo.json")
    if not os.path.exists(ruta):
        return None
    return {ic["id"]: ic.get("claves", "") for ic in leer(ruta).get("iconos") or []}
TRANSICIONES = {"primera": "smoothleft",  # del gancho a la primera tarjeta (zoomin de xfade se ve pixelado)
                "tarjeta": "slideleft",   # tarjeta → tarjeta
                "texto": "smoothleft",    # entrada a golpe o definición
                "adivina": "circleopen",  # entrada a la adivina
                "completa": "circleopen", # entrada a una escena a pantalla completa (mapa, ranking, escala, tiempo)
                "giro": "slideup",        # la escena del giro (manda sobre el tipo)
                "cierre": "fade",         # entrada al cierre
                "seguida": "fade",        # dentro de una secuencia de voz (historia): corte suave, la voz sigue
                "bucle": "fade"}          # el cuadro final en bucle
RE_DE_CADA = re.compile(r"\b(\d+)\s+de\s+cada\s+(\d+)\b")
TRANSICION = 0.3     # deslizamiento entre escenas (xfade); los primeros 0.3 s de cada escena quedan bajo la transición
BUCLE_S, BUCLE_FUNDIDO = 0.6, 0.25   # cierre en bucle: el primer cuadro del gancho vuelve al final (TikTok repite el video)
# palabras que no anclan solas la línea de pantalla a la voz (un «de» suelto no basta para fijar su tiempo)
VACIAS = set("de del la el los las en y a o que un una al lo se".split())
STOP = set("de del en los las una uno unos unas que para con por mas sin sobre entre hasta desde cada como pero este esta "
           "estos estas ano anos mil millones casi solo hace todo toda todos todas donde cuando mientras tambien ademas "
           "segun contra entonces resultado veces".split())


def pausas_mal_puestas(texto):
    """V9: una pausa va tras puntuación fuerte o justo antes de un conector «pero», y como mucho una por escena."""
    out = []
    ms = list(RE_PAUSA.finditer(texto))
    if len(ms) > PAUSAS_MAX_ESCENA:
        out.append("%d pausas en una escena (máximo %d: el exceso de <break> ensucia la voz)" % (len(ms), PAUSAS_MAX_ESCENA))
    for m in ms:
        antes, despues = texto[:m.start()].rstrip(), texto[m.end():].lstrip()
        if not antes:
            out.append("«%s» al inicio de la escena no sirve: la escena ya empieza en silencio" % m.group(0))
        elif not (antes[-1] in ".?!:;…") and not RE_ENLACE["pero"].match(despues):
            out.append("«%s» va tras puntuación fuerte o justo antes de «pero / sin embargo / aunque / aun así», no en «…%s %s %s…»"
                       % (m.group(0), antes[-20:], m.group(0), despues[:20]))
    return out


def con_pausa_de_revelado(texto):
    """Adivina: «[pausa adivina]» (2.0 s, el tiempo de pausar el video) antes de la última oración (la respuesta); si el
    guion ya puso una pausa justo ahí, la alarga."""
    ms = list(re.finditer(r"[.?!…]\s+(?=\S)", texto))
    if not ms:
        return texto
    antes, despues = texto[:ms[-1].end()], texto[ms[-1].end():]
    m = RE_PAUSA.match(despues)
    if m:
        despues = despues[m.end():].lstrip()
    elif re.search(r"\[pausa[^\]]*\]\s*$", antes, re.I):
        antes = re.sub(r"\[pausa[^\]]*\]\s*$", "", antes, flags=re.I)
    return antes + "[pausa adivina] " + despues


def adivina_mal_armada(e):
    """V9: `pregunta` ≤ PREGUNTA_CARACTERES y termina en «?»; 3 `opciones` ≤ OPCION_CARACTERES, con cifra y distintas;
    `correcta` 0–2; la voz nombra las tres y la ÚLTIMA cifra que dice es la correcta (la respuesta cierra la escena)."""
    out = []
    preg = (e.get("pregunta") or "").strip()
    if not preg or len(preg) > PREGUNTA_CARACTERES or not preg.endswith("?"):
        out.append("«pregunta» de 1–%d caracteres que termina en «?»" % PREGUNTA_CARACTERES)
    ops = e.get("opciones")
    if not (isinstance(ops, list) and len(ops) == 3 and all(isinstance(o, str) and o.strip() for o in ops)):
        out.append("«opciones» son 3 cadenas")
        return out
    ops = [o.strip() for o in ops]
    if any(len(o) > OPCION_CARACTERES for o in ops):
        out.append("cada opción tiene ≤ %d caracteres" % OPCION_CARACTERES)
    vals = [valor_de(o) for o in ops]
    if any(v is None for v in vals) or len(set(vals)) < 3:
        out.append("las 3 opciones llevan una cifra y son distintas")
        return out
    k = e.get("correcta")
    if k not in (0, 1, 2):
        out.append("«correcta» es 0, 1 o 2")
        return out
    nums = [float(m.group().replace(",", "")) for m in re.finditer(NE.NUM, e.get("texto") or "")]
    faltan = [o for o, v in zip(ops, vals) if not any(abs(x - v) < 1e-9 for x in nums)]
    if faltan:
        out.append("la voz nombra las 3 opciones; falta: %s" % ", ".join("«%s»" % o for o in faltan))
    if not nums or abs(nums[-1] - vals[k]) > 1e-9:
        out.append("la última cifra de la voz debe ser la opción correcta «%s» (la respuesta va al final, tras la pausa)" % ops[k])
    texto = sin_pausas(e.get("texto") or "").strip()
    fins = list(re.finditer(r"[.?!…](?=\s+\S)", texto))
    preg_fin = texto.rfind("?")
    medio = texto[preg_fin + 1:fins[-1].end()] if fins and 0 <= preg_fin < fins[-1].end() else ""
    if not re.search(r"\b(%s)\b" % "|".join(PAUSA_ADIVINA), _plano(medio)):
        out.append("tras las opciones y antes de la respuesta, una oración pide pausar para responder («Pausa el video y "
                   "piénsalo.», «Detén el video y responde.»)")
    return out


def cinetico_de(tipo, e):
    """Lo que golpe.html pone en pantalla: pantalla + línea (gancho y golpe), término + definición, pregunta + opciones."""
    if tipo in ("gancho", "golpe"):
        return {"pantalla": e.get("pantalla"), "linea": e.get("linea")}
    if tipo == "definicion":
        return {"pantalla": (e.get("termino") or "").strip(), "linea": (e.get("definicion") or "").strip()}
    if tipo == "adivina":
        return {"pantalla": (e.get("pregunta") or "").strip(), "linea": " · ".join(o.strip() for o in e.get("opciones") or [])}
    if tipo == "explica":
        return {"pantalla": (e.get("titulo") or "").strip(), "linea": " · ".join(str(x).strip() for x in e.get("pasos") or [])}
    return None


def mayuscula_inicial(segs):
    """Una cifra que abre oración sale de numeros_es en minúscula («¿Cuántos tenía? cuatro mil…»): mayúscula en la
    primera letra de la voz y en la de cada oración (tras . ? ! …), en el texto hablado (`v`) de los segmentos."""
    previo = ""
    for sg in segs:
        v = sg["v"]
        if (not sin_pausas(previo).strip() or re.search(r"[.?!…]\s*$", sin_pausas(previo))) and sin_pausas(v).strip():
            k = next((j for j, ch in enumerate(v) if ch.isalpha() and not RE_PAUSA.match(v[max(0, j - 1):]) and
                      "[" not in v[:j].split("]")[-1]), len(v) - len(v.lstrip()))
            if k >= len(v):
                previo += v
                continue
            v = v[:k] + v[k].upper() + v[k + 1:]
            sg["v"] = v
        previo += v


def con_breaks(voz):
    """El prompt de ElevenLabs: cada marca de pausa como <break time="…s" />."""
    def tipo(m):
        t = m.group(0).lower()
        return "adivina" if "adivina" in t else "larga" if "larga" in t else "corta"
    return RE_PAUSA.sub(lambda m: BREAK % PAUSA_S[tipo(m)], voz)


def sin_pausas(s):
    return re.sub(r"[ \t]*" + RE_PAUSA.pattern + r"[ \t]*", " ", s, flags=re.I)


def eco_entre_escenas(voz_anterior, voz):
    """Palabras (≥ 5 letras, sin vacías) con las que cierra una escena y abre la siguiente: «¿Y en dos mil
    veinticuatro?» → «El resultado: en dos mil veinticuatro…» se oye repetido."""
    cola = [w for w in _plano(voz_anterior).split()[-5:] if len(w) >= 5 and w not in STOP]
    cabeza = [w for w in _plano(voz).split()[:7] if len(w) >= 5 and w not in STOP]
    return [w for w in cabeza if w in cola]


def palabras_no_dichas(pantalla, voz):
    """Palabras clave de la pantalla (≥ 6 letras, sin vacías ni números) que la voz no dice: se comparan raíces de
    6 letras sin tildes («decomisados» ↔ «decomisada», «condenas» ↔ «condena»)."""
    raices = {w[:6] for w in _plano(voz).split() if len(w) >= 6}
    out = []
    for w in _plano(pantalla).split():
        if len(w) < 6 or w in STOP or w.isdigit() or w[:6] in raices:
            continue
        out.append(w)
    return out


# ---------- utilidades ----------
def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def rel(p):
    return os.path.relpath(p, RAIZ)


def falla(msg):
    print("ERROR:", msg, file=sys.stderr)
    return 1


def ffprobe_dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def estado(trabajo):
    return leer(os.path.join(trabajo, "video.json"))


def titular_de(html):
    """Kicker, titular y si hay nota en la tarjeta, leídos de DATA en tuit_N.html."""
    s = open(html, encoding="utf-8").read()
    t = re.search(r'"titular":\s*\[(.*?)\]', s, re.S)
    k = re.search(r'"kicker":\s*("(?:[^"\\]|\\.)*")', s)
    nota = bool(re.search(r'"nota":\s*"(?:[^"\\]|\\.){3,}"', s))
    return (json.loads(k.group(1)) if k else "", " ".join(json.loads("[" + t.group(1) + "]")) if t else "", nota)


def contraste(c1, c2):
    def lum(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
    a, b = sorted((lum(c1), lum(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def colores(paleta):
    """Colores de las escenas, estilo Noche (design/tokens.json · noche, los mismos roles que la tarjeta): fondo oscuro de
    la paleta, texto crema y el acento del tema para lo único que destaca en cada escena (la cifra, la palabra que suena,
    las figuras encendidas, la palabra que suena en el subtítulo). a2/a3 son la serie atenuada (crema y acento, ≥ 3.2:1). fondo_acto2 oscurece el acto 2 de
    /historia y fondo_golpe el golpe trágico; tinta_acento es el texto sobre el acento (subtítulo activo, píldoras)."""
    tk = leer(os.path.join(RAIZ, "design", "tokens.json"))
    n, q = tk["noche"], tk["noche"]["paletas"][paleta]
    return {"bg": q["fondo"], "ink": n["texto"], "a1": q["acento"], "a2": q["serie"][2], "a3": q["serie"][3],
            "fondo_acto2": q["fondo_acto2"], "fondo_golpe": q["fondo_golpe"], "tinta_acento": n["tinta_sobre_acento"],
            # la palabra que suena va en una caja del acento con tinta oscura (como el diseño del lienzo)
            "resalte_bg": q["acento"], "resalte_ink": n["tinta_sobre_acento"],
            "pregunta": q["acento"], "acento": q["acento"], "grafico": q["acento"]}


RE_CABECERA_VISUAL = re.compile(r"<!-- plantilla: ([\w-]+) · paleta: (\w+)")
RE_DATA_VISUAL = re.compile(r"const DATA = \{.*?\n\};\n", re.S)


def rebasar_tarjetas(hilo_dir, trabajo):
    """Rearma en TRABAJO/tarjetas/ cada tuit_N.html del hilo con la base de hoy y en estilo Noche (plantilla, paleta y
    DATA de su cabecera): un hilo entregado antes de Noche trae tarjetas de fondo plano que no casan con el fondo oscuro
    del video. La grabación y V7 usan esta carpeta (tarjetas_dir). Devuelve los avisos."""
    import nuevo_visual
    tk, avisos = nuevo_visual.tokens(), []
    dest = os.path.join(trabajo, "tarjetas")
    os.makedirs(dest, exist_ok=True)
    for html in sorted(glob.glob(os.path.join(hilo_dir, "tuit_*.html"))):
        src = open(html, encoding="utf-8").read()
        salida = os.path.join(dest, os.path.basename(html))
        cab, dat = RE_CABECERA_VISUAL.search(src), RE_DATA_VISUAL.search(src)
        if not cab or not dat:
            shutil.copyfile(html, salida)
            avisos.append("%s sin cabecera o DATA: se usa tal cual" % os.path.basename(html))
            continue
        ok, msg = nuevo_visual.ensamblar(cab.group(1), salida, cab.group(2), tk, "noche")
        if not ok:
            shutil.copyfile(html, salida)
            avisos.append("%s: %s (se usa tal cual)" % (os.path.basename(html), msg))
            continue
        base = open(salida, encoding="utf-8").read()
        nuevo, k = RE_DATA_VISUAL.subn(lambda _m: dat.group(0), base, count=1)
        if k != 1:
            shutil.copyfile(html, salida)
            avisos.append("%s: la plantilla no tiene un bloque DATA reconocible (se usa tal cual)" % os.path.basename(html))
            continue
        open(salida, "w", encoding="utf-8").write(nuevo)
    return avisos


def tarjetas_dir(trabajo, st):
    """Carpeta de las tarjetas que se graban: TRABAJO/tarjetas/ (rearmadas en Noche por preparar) o la del hilo."""
    propia = os.path.join(trabajo, "tarjetas")
    if os.path.isdir(propia) and glob.glob(os.path.join(propia, "tuit_*.html")):
        return propia
    return os.path.join(RAIZ, st["hilo"]) if st.get("hilo") else None


def palabras(s):
    return len((s or "").split())


def _plano(s):
    """Texto normalizado para comparar: minúsculas, sin tildes ni signos, espacios simples."""
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# ---------- preparar ----------
def resolver_hilo(arg):
    if arg == "ultimo":
        regs = leer(os.path.join(RAIZ, "memoria", "hilos.json"))["hilos"]
        regs = [h for h in regs if h.get("estado") in ("listo", "publicado")]
        if not regs:
            return None
        return os.path.join(RAIZ, sorted(regs, key=lambda h: (h["fecha"], h["id"]))[-1]["ruta"])
    for cand in (arg, os.path.join(RAIZ, arg), os.path.join(RAIZ, "hilos", arg)):
        if os.path.isfile(os.path.join(cand, "hilo.json")):
            return os.path.abspath(cand)
    hits = sorted(glob.glob(os.path.join(RAIZ, "hilos", "*-" + arg)))
    return hits[-1] if hits else None


def elegir_musica(paleta, forzada):
    cat = leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
    if forzada:
        p = next((x for x in cat if x["id"] == forzada), None)
        if not p:
            raise ValueError("música «%s» no está en el catálogo" % forzada)
        return p
    propias = [x for x in cat if x["paleta"] == paleta]
    if not propias:
        raise ValueError("el catálogo no tiene música para la paleta «%s»" % paleta)
    usos = {}
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    if os.path.exists(vids):
        for v in leer(vids)["videos"]:  # la usada hace más tiempo (o nunca) va primero
            usos[v.get("musica")] = max(usos.get(v.get("musica"), ""), v.get("fecha", ""))
    return sorted(propias, key=lambda x: (usos.get(x["id"], ""), x["id"]))[0]


def frases_usadas(slug_actual, n=FRASES_USADAS_VIDEOS):
    """Las frases de voz de los últimos n videos (memoria/videos.json → frases): el guionista no las repite y el crítico
    las coteja (C11). Los ejemplos de las guías son forma, no texto: copiarlos hacía que todos los videos sonaran igual."""
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    regs = [v for v in (leer(vids)["videos"] if os.path.exists(vids) else [])
            if v.get("slug") != slug_actual and v.get("frases")]
    regs = sorted(regs, key=lambda v: (v.get("fecha", ""), v.get("id", "")))[-n:]
    if not regs:
        return ["- (ningún video anterior registrado)"]
    out = ["Varía la fórmula de la promesa, la forma del gancho, cómo abres cada escena y la pregunta del cierre. "
           "Los conectores (pero / por eso / y) se repiten por fuerza; lo que no se repite es la frase que los sigue."]
    for v in reversed(regs):
        fr = v["frases"]
        out.append("- **%s** · promesa: «%s» · gancho: «%s» · cierre (%s · %s): «%s» · aperturas: %s"
                   % (v["slug"], fr.get("promesa", ""), fr.get("gancho", ""), fr.get("cierre_tipo") or "pregunta",
                      fr.get("cierre_forma") or "experiencia", fr.get("cierre") or fr.get("pregunta", ""),
                      " / ".join("«%s…»" % x for x in fr.get("aperturas", []))))
    return out


def ganchos_recientes(slug_actual):
    """R9: familias de los últimos ROTACION_FAMILIAS videos y visuales del último ROTACION_VISUALES (memoria/videos.json →
    frases.familia y frases.visual). Un video anterior al catálogo de ganchos no tiene familia y su visual era la cifra."""
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    regs = [v for v in (leer(vids)["videos"] if os.path.exists(vids) else []) if v.get("slug") != slug_actual]
    regs = sorted(regs, key=lambda v: (v.get("fecha", ""), v.get("id", "")))
    fr = [v.get("frases") or {} for v in regs]
    return {"familias": [x["familia"] for x in fr[-ROTACION_FAMILIAS:] if x.get("familia")],
            "visuales": [x.get("visual") or "cifra" for x in fr[-ROTACION_VISUALES:]]}


def cierres_recientes(slug_actual):
    """F7: el tipo de cierre del último video (una pregunta no sigue a otra), las formas de los últimos ROTACION_CIERRES y
    el mecanismo de consecuencia del último. Un video anterior al catálogo de cierres cerró con una pregunta sobre la
    experiencia del espectador."""
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    regs = [v for v in (leer(vids)["videos"] if os.path.exists(vids) else []) if v.get("slug") != slug_actual]
    fr = [v.get("frases") or {} for v in sorted(regs, key=lambda v: (v.get("fecha", ""), v.get("id", "")))]
    return {"tipos": [x.get("cierre_tipo") or "pregunta" for x in fr[-1:]],
            "formas": [x.get("cierre_forma") or "experiencia" for x in fr[-ROTACION_CIERRES:]],
            "mecanismos": [x["cierre_mecanismo"] for x in fr[-1:] if x.get("cierre_mecanismo")]}


def final_de(cierre):
    """La frase final del cierre (el remate o la pregunta); `pregunta` es el nombre del formato anterior."""
    cierre = cierre or {}
    return (cierre.get("final") or cierre.get("pregunta") or "").strip()


def vocabulario_tema(hilo, tarjetas, cifras=None):
    """Raíces (5 letras) de las palabras con contenido del tema, la tesis, los titulares y el concepto y la unidad de cada
    cifra verificada del hilo: F3 ancla la frase final al fenómeno del video (no a lo que el guion se invente)."""
    texto = " ".join([hilo.get("tema", ""), hilo.get("tesis", "")] + [t.get("titular") or "" for t in tarjetas] +
                     ["%s %s" % (c.get("concepto", ""), c.get("unidad", "")) for c in (cifras or {}).values()])
    return {w[:5] for w in _plano(texto).split() if len(w) >= 5 and w not in STOP and w not in GENERICAS and not w.isdigit()}


def reglas_cierre(cierre, st, hilo, tarjetas, numeros_gancho, cifras=None):
    """F1–F8 de la frase final del cierre (referencias/cierres.md) → fallas."""
    f = []
    tipo, forma, fin = cierre.get("tipo"), cierre.get("forma"), final_de(cierre)
    if tipo not in CIERRE_FORMAS:
        return ["F1 cierre.tipo «%s» no es remate|pregunta (lo normal es remate; a veces, pregunta)" % tipo]
    if forma not in CIERRE_FORMAS[tipo]:
        f.append("F1 cierre.forma «%s» no es una forma de %s (%s)" % (forma, tipo, "|".join(CIERRE_FORMAS[tipo])))
    if forma == "legado" and (hilo or {}).get("modo") != "historia":
        f.append("F1 la forma «legado» es de /historia (lo que la gente hace hoy con lo que la historia dejó); un video de datos cierra con consecuencia")
    if not fin:
        return f + ["F1 falta cierre.final (la frase con que termina la voz)"]
    if palabras(fin) > FINAL_PALABRAS or len(fin) > FINAL_CARACTERES:
        f.append("F2 la frase final «%s» tiene más de %d palabras o %d caracteres: se lee sola en grande" % (fin, FINAL_PALABRAS, FINAL_CARACTERES))
    if tipo == "pregunta" and (not fin.endswith("?") or fin.count("?") > 1):
        f.append("F2 una pregunta final: una sola y termina en «?»")
    if tipo == "remate" and "?" in fin:
        f.append("F2 un remate no es una pregunta (sin «?»); si quieres preguntar, tipo pregunta")
    vocab = vocabulario_tema(hilo, tarjetas, cifras)
    if not any(w[:5] in vocab for w in _plano(fin).split() if len(w) >= 5):
        pista = [w for w in dict.fromkeys(_plano(" ".join([hilo.get("tema", "")] + [t.get("titular") or "" for t in tarjetas])).split())
                 if len(w) >= 5 and w not in STOP and w not in GENERICAS and not w.isdigit()][:6]
        f.append("F3 «%s» no nombra nada del tema del video (%s…): la frase final habla del fenómeno del video, no de una "
                 "analogía de otro ámbito (los cuartos de una casa no son los espacios de una cárcel)" % (fin, ", ".join(pista)))
    m = CEBO.search(" ".join((fin, cierre.get("texto") or "")))
    if m:
        f.append("F4 «%s» es cebo de interacción (pedir comentar, etiquetar, compartir): Meta lo penaliza, también en el audio" % m.group())
    if tipo == "pregunta" and TEMA_SENSIBLE.search(" ".join((hilo.get("tema", ""), hilo.get("tesis", "")))):
        if forma == "experiencia":
            f.append("F5 tema sensible: la pregunta no pide la experiencia del espectador (lo expone como víctima o juzgado); "
                     "pregunta por el sistema (elegir, predicción, decidir, lugar, porqué)")
        m = EXPONE.search(fin)
        if m:
            f.append("F5 tema sensible: «%s» expone al espectador o a su familia" % m.group())
    con = cierre.get("consecuencia") or {}
    if tipo == "remate":
        # F6: un remate no termina con un dato (el dato va en las conclusiones): a lo más una cifra y nunca la del gancho
        nums = numeros_sin_anios(fin)
        if len(nums) > 1:
            f.append("F6 el remate «%s» dice %d cifras: terminar con un dato no es un remate; las cifras van en las "
                     "conclusiones y la frase final dice lo que le pasa a la gente (a lo más una cifra: cuántos lo viven)"
                     % (fin, len(nums)))
        repetidas = [v for v in numeros_gancho if escribe_numero(v, [fin])]
        if repetidas:
            f.append("F6 el remate repite la cifra del gancho (%s): eso es volver al dato; di su consecuencia (quién lo vive, "
                     "qué pierde, qué le sigue)" % ", ".join(clave(v) for v in repetidas))
    if forma in ("consecuencia", "legado"):
        if forma == "consecuencia" and con.get("mecanismo") not in MECANISMOS:
            f.append("F6 cierre.consecuencia.mecanismo «%s» no es uno de %s" % (con.get("mecanismo"), "|".join(MECANISMOS)))
        quien, verbo = (con.get("quien") or "").strip(), (con.get("verbo") or "").strip()
        if not quien or _plano(quien) not in _plano(fin):
            f.append("F6 cierre.consecuencia.quien «%s» tiene que estar en la frase final (quién vive la consecuencia)" % quien)
        elif not HUMANO.search(quien):
            f.append("F6 cierre.consecuencia.quien «%s» no es gente (familias, niños, madres, conductores, presos…): la "
                     "consecuencia le pasa a personas, no a una tasa ni a una institución" % quien)
        if not verbo or not re.search(r"\b%s\b" % re.escape(_plano(verbo)), _plano(fin)):
            f.append("F6 cierre.consecuencia.verbo «%s» tiene que estar en la frase final (lo que les pasa, conjugado)" % verbo)
        elif forma == "legado" and PASADO.search(_plano(verbo)):
            f.append("F6 legado: el verbo «%s» no está en presente; el legado es lo que hacen HOY con lo que dejó la historia "
                     "(siguen, abren, toman, encienden)" % verbo)
    if tipo == "remate":
        m = FATALISMO.search(" ".join((fin, cierre.get("texto") or "")))
        if m:
            f.append("F8 «%s» afirma lo que el hilo no dice (fatalismo): di lo que ya pasó o lo que sigue pendiente, no que "
                     "no tiene remedio" % m.group())
        m = FUTURO.search(fin)
        if m and not (con.get("proyeccion") and con["proyeccion"] in (cifras or {})):
            f.append("F8 «%s» proyecta al futuro una pérdida que la fuente no proyecta: usa lo que ya pasó («ya», «este año "
                     "van») o declara cierre.consecuencia.proyeccion con el id de una cifra que proyecte" % m.group())
    rec = st.get("cierres_recientes") or {}
    if tipo == "pregunta" and "pregunta" in (rec.get("tipos") or []):
        f.append("F7 el video anterior cerró con una pregunta: la pregunta va solo a veces; este cierra con un remate")
    if forma not in ("consecuencia", "legado") and forma in (rec.get("formas") or []):
        f.append("F7 la forma «%s» cerró uno de los últimos %d videos (%s): usa otra" % (forma, ROTACION_CIERRES, ", ".join(rec["formas"])))
    if forma == "consecuencia" and con.get("mecanismo") in (rec.get("mecanismos") or []):
        f.append("F7 el mecanismo «%s» cerró el último video: usa otro (%s)"
                 % (con["mecanismo"], "|".join(m for m in MECANISMOS if m != con["mecanismo"])))
    return f


def lineas_recientes(rec, sin_rotacion=False):
    if sin_rotacion:
        return ["- (prueba: sin rotación)"]
    return ["- Familias bloqueadas (últimos %d videos): %s" % (ROTACION_FAMILIAS, ", ".join(rec["familias"]) or "ninguna"),
            "- Visual bloqueado (último video): %s" % (", ".join(rec["visuales"]) or "ninguno"),
            "- Todas las familias: %s · visuales: %s (qué visual admite cada familia: referencias/ganchos.md)"
            % (", ".join(FAMILIAS), ", ".join(VISUALES))]


def gancho_elegido(trabajo):
    """El candidato que eligió el crítico (ganchos.json → elegido), o None si el video no pasó por la fase de ganchos."""
    ruta = os.path.join(trabajo, "ganchos.json")
    if not os.path.exists(ruta):
        return None
    G = leer(ruta)
    return next((c for c in G.get("candidatos") or [] if c.get("id") == G.get("elegido")), None)


CAMPOS_GANCHO = ("familia", "visual", "visual_datos", "pantalla", "linea", "verbo", "calculo", "icono")


def mismo_gancho(e, c, promesa=None):
    """La escena 1 es el candidato `c` tal cual; la voz puede llevar además la promesa si va en la escena 1."""
    if any((e.get(k) or None) != (c.get(k) or None) for k in CAMPOS_GANCHO):
        return False
    t, tc = _plano(e.get("texto")), _plano(c.get("texto"))
    if t == tc:
        return True
    return (promesa or {}).get("en") == 1 and t.startswith(tc) and _plano(promesa.get("texto")) in t


def sugerir_tarjetas(tuits, tarjetas, dur):
    """Orden sugerido: T1, luego giro e impacto, luego contexto con plantilla animada, luego el resto (sin el cierre)."""
    beats = {t["n"]: t.get("beat") for t in tuits}
    disp = {t["n"]: t for t in tarjetas}
    orden = [1] if 1 in disp else []
    for b in ("giro", "impacto"):
        orden += [n for n in sorted(disp) if beats.get(n) == b and n not in orden]
    orden += [n for n in sorted(disp) if n not in orden and beats.get(n) != "cierre"
              and disp[n]["plantilla"] in PLANTILLAS_ANIMADAS]
    orden += [n for n in sorted(disp) if n not in orden and beats.get(n) != "cierre"]
    return sorted(orden[:dur["tarjetas"][1]])


def escala_humana(cid, c):
    """Traducciones posibles de una cifra, con su `calculo` listo para el guion (≤ 2 líneas)."""
    out = []
    partes = [p.get("valor") for p in c.get("partes") or []]
    partes = [p for p in partes if isinstance(p, (int, float)) and not isinstance(p, bool)]
    v = c.get("valor")
    if len(partes) >= 2 and partes[0]:
        out.append("×%.1f entre las dos primeras partes (calculo: %s.partes[1]/%s.partes[0]) · %+.0f %% (calculo: (%s.partes[1]/%s.partes[0]-1)*100)"
                   % (partes[1] / partes[0], cid, cid, (partes[1] / partes[0] - 1) * 100, cid, cid))
    u = str(c.get("unidad", "")).lower()
    if isinstance(v, (int, float)) and not isinstance(v, bool) and ("%" in u or "porcentaje" in u or "por ciento" in u) and 0 < v < 100:
        out.append("1 de cada %d (calculo: 100/%s)" % (round(100 / v), cid))
    serie = c.get("serie") or []
    v0 = serie[0].get("v") if serie else None
    if len(serie) >= 2 and isinstance(v0, (int, float)) and v0 and isinstance(v, (int, float)) and not isinstance(v, bool):
        out.append("×%.1f desde %s (calculo: %s/%s.serie[0]) · %+.0f %% (calculo: (%s/%s.serie[0]-1)*100)"
                   % (v / v0, serie[0].get("p"), cid, cid, (v / v0 - 1) * 100, cid, cid))
    return out[:2]


RE_ANIO = re.compile(r"(?:19|20)\d\d(?!\d)")


def anios_de(t, cifras):
    """Años que la tarjeta tiene como etiqueta (los `p` de la serie o los nombres de las partes de sus cifras): si la
    voz los dice, `tiempos` hace latir esa columna (T.anios) y cuenta el evento para V10. «1997-98» cuenta como 1997."""
    out = []
    for cid in t.get("cifra_ids") or []:
        c = cifras.get(cid) or {}
        etiquetas = [str(p.get("p", "")) for p in (c.get("serie_final") or c.get("serie") or [])] + \
                    [str(p.get("nombre", p.get("etiqueta", ""))) for p in (c.get("partes_final") or c.get("partes") or [])]
        for et in etiquetas:
            m = RE_ANIO.match(et.strip())
            if m and m.group() not in out:
                out.append(m.group())
    return out


def nombres_depto():
    """{GT01: «Guatemala», …} del bloque NOMBRES de templates/base.html (el mismo que usa la tarjeta de mapa)."""
    global _NOMBRES_DEPTO
    if _NOMBRES_DEPTO is None:
        base = open(os.path.join(RAIZ, "templates", "base.html"), encoding="utf-8").read()
        m = re.search(r"const NOMBRES = \{([\s\S]*?)\};", base)
        _NOMBRES_DEPTO = dict(re.findall(r'(GT\d\d):\s*"([^"]+)"', m.group(1))) if m else {}
    return _NOMBRES_DEPTO


def items_de(datos, orden=None):
    """[(nombre, valor)] de una tarjeta barras-h (`items`) o mapa (`valores` por departamento), ordenados de mayor a
    menor (o al revés con orden «asc»): los puestos de la escena ranking."""
    datos = datos or {}
    if datos.get("items"):
        its = [(str(it.get("nombre", "")), float(it["valor"])) for it in datos["items"] if it.get("valor") is not None]
    elif datos.get("valores"):
        its = [(nombres_depto().get(k, k), float(v)) for k, v in datos["valores"].items() if v is not None]
    else:
        return []
    return sorted(its, key=lambda x: x[1], reverse=(orden != "asc"))


def puntos_de(datos, guardar_et=(), guardar_v=()):
    """[(etiqueta, valor, sub, destacado)] de una tarjeta antes-despues (2 puntos) o linea (la serie destacada o la
    primera; si tiene más de TIEMPO_PUNTOS, el primero, el último y los que la voz dice (etiquetas `guardar_et` o
    valores `guardar_v`), y el resto de los lugares equiespaciados entre los demás): la escena tiempo. Antes se
    muestreaba sin mirar la voz y se perdía el año que la voz decía (el pico de 2019 en cárceles)."""
    datos = datos or {}
    if datos.get("antes") and datos.get("despues"):
        a, b = datos["antes"], datos["despues"]
        return [(str(a.get("etiqueta", "")), float(a["valor"]), a.get("sub"), False),
                (str(b.get("etiqueta", "")), float(b["valor"]), b.get("sub"), True)]
    if datos.get("series"):
        serie = next((x for x in datos["series"] if x.get("destacar")), datos["series"][0])
        ets, vals = datos.get("etiquetasX") or [], serie.get("valores") or []
        idx = [k for k, v in enumerate(vals) if v is not None]
        if len(idx) > TIEMPO_PUNTOS:
            et_de = lambda k: str(ets[k]) if k < len(ets) else str(k + 1)  # noqa: E731
            fijos = {idx[0], idx[-1]} | {k for k in idx if et_de(k) in set(map(str, guardar_et))
                                         or any(abs(float(vals[k]) - float(g)) < 1e-6 for g in guardar_v)}
            otros = [k for k in idx if k not in fijos]
            libres = max(0, TIEMPO_PUNTOS - len(fijos))
            elegidos = [otros[round(j * (len(otros) - 1) / max(1, libres - 1))] for j in range(libres)] if otros and libres else []
            idx = sorted(fijos | set(elegidos))
        return [(str(ets[k]) if k < len(ets) else str(k + 1), float(vals[k]), None, k == idx[-1]) for k in idx]
    return []


def pildora_texto(antes, despues, modo="factor", dec=None):
    """La píldora de antes-despues («×1.77» o «+77%»), calculada como H.pildora en templates/base.html."""
    if modo == "ninguna" or not antes:
        return None
    d = 2 if dec is None else dec
    factor = despues / antes
    if modo == "factor":
        return "×" + ("%.*f" % (d, factor))
    pct = (factor - 1) * 100
    return ("−" if pct < 0 else "+") + ("%.*f" % (0 if d > 1 else d, abs(pct))) + "%"


def datos_tarjeta(html):
    """El bloque `const DATA = {…};` de la tarjeta evaluado con node (es un literal de JS, no JSON) → dict, o None.
    Las escenas a pantalla completa (ranking, tiempo, escala) lo necesitan en `tiempos` para saber qué valores entran."""
    m = re.search(r"const DATA = (\{[\s\S]*?\n\});", html)
    if not m:
        return None
    r = subprocess.run(["node", "-e", "const D = (%s); process.stdout.write(JSON.stringify(D));" % m.group(1)],
                       capture_output=True, text=True)
    if r.returncode or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def cmd_preparar(a):
    if a.duracion not in DURACIONES:
        return falla("duración «%s»: usa corto, medio (por defecto) o largo" % a.duracion)
    hilo_dir = resolver_hilo(a.hilo)
    if not hilo_dir:
        return falla("no encuentro el hilo «%s» (slug, carpeta de hilos/ o «ultimo»)" % a.hilo)
    hilo = leer(os.path.join(hilo_dir, "hilo.json"))
    datos = leer(os.path.join(hilo_dir, "datos.json"))
    if hilo.get("estado") not in ("listo", "publicado") and not a.permitir_borrador:
        return falla("el hilo está «%s»: /video solo convierte hilos listos o publicados" % hilo.get("estado"))
    try:
        musica = elegir_musica(hilo["paleta"], a.musica)
    except (ValueError, FileNotFoundError) as e:
        return falla(str(e))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", hilo["slug"], "video"))
    for sub in ("audio", "clips", "segs", "revision", "salida"):
        os.makedirs(os.path.join(trabajo, sub), exist_ok=True)

    cifras = {c["id"]: c for c in datos["cifras"]}
    tarjetas, lineas = [], []
    dur = DURACIONES[a.duracion]
    for t in hilo["tuits"]:
        html = os.path.join(hilo_dir, "tuit_%d.html" % t["n"])
        if not t.get("imagen") or not os.path.exists(html):
            continue
        kicker, titular, nota = titular_de(html)
        tarjetas.append({"n": t["n"], "plantilla": t.get("plantilla"), "titular": titular, "beat": t.get("beat"), "nota": nota,
                         "anios": anios_de(t, cifras), "datos": datos_tarjeta(open(html, encoding="utf-8").read())})
        anim = "animada" if t.get("plantilla") in PLANTILLAS_ANIMADAS else "aparece entera"
        pl, dat = t.get("plantilla"), tarjetas[-1]["datos"] or {}
        if pl == "mapa":
            anim += " · o como escena `mapa` o `ranking` a pantalla completa"
        elif pl == "barras-h" and len(items_de(dat)) >= RANKING_TOP[0]:
            anim += " · o como escena `ranking` (cuenta regresiva, top %d–%d)" % (RANKING_TOP[0], min(RANKING_TOP[1], len(items_de(dat))))
        elif pl in PLANTILLAS_DE["tiempo"] and len(puntos_de(dat)) >= 2:
            anim += " · o como escena `tiempo` (línea de tiempo a pantalla completa)"
        elif pl in PLANTILLAS_DE["escala"]:
            anim += " · o como escena `escala` (figuras «K de cada N»)"
        lineas.append("\n### T%d · %s · %s (%s)" % (t["n"], t.get("beat", ""), t.get("plantilla"), anim))
        lineas.append("- kicker: %s\n- titular: %s" % (kicker, titular))
        if t.get("texto"):
            lineas.append("- texto del tuit: %s" % t["texto"].replace("\n", " "))
        lineas.append("- alt-text: %s" % t.get("alt_text", ""))
        ids_num = []
        for cid in t.get("cifra_ids") or []:
            c = cifras.get(cid)
            if not c:
                continue
            serie = ", ".join("%s: %s" % (p.get("p"), p.get("v")) for p in (c.get("serie") or [])[-8:])
            partes = ", ".join("%s: %s" % (p.get("nombre", p.get("etiqueta", "")), p.get("valor")) for p in c.get("partes") or [])
            lineas.append("- cifra %s: %s = %s %s (%s)%s%s" % (
                cid, c.get("concepto", ""), c.get("valor"), c.get("unidad", ""), c.get("periodo", ""),
                " · serie (últimos): " + serie if serie else "", " · partes: " + partes if partes else ""))
            for eh in escala_humana(cid, c):
                lineas.append("  - escala humana posible: %s" % eh)
            if isinstance(c.get("valor"), (int, float)) and not isinstance(c.get("valor"), bool):
                ids_num.append((cid, c["valor"]))
        if len(ids_num) == 2 and ids_num[0][1]:
            (c1, v1), (c2, v2) = ids_num
            lineas.append("  - escala humana posible: ×%.1f entre %s y %s (calculo: %s/%s) · %+.0f %% (calculo: (%s/%s-1)*100)"
                          % (v2 / v1, c1, c2, c2, c1, (v2 / v1 - 1) * 100, c2, c1))
    if len(tarjetas) < dur["tarjetas"][0]:
        return falla("el hilo tiene %d tarjetas y «%s» pide al menos %d: usa una duración menor"
                     % (len(tarjetas), a.duracion, dur["tarjetas"][0]))
    recientes = {"familias": [], "visuales": []} if a.sin_rotacion else ganchos_recientes(hilo["slug"])
    cierres = {"tipos": [], "formas": []} if a.sin_rotacion else cierres_recientes(hilo["slug"])
    anim_rec = [] if a.sin_rotacion else animaciones_recientes(hilo["slug"])
    n_max = 1 + dur["tarjetas"][1] + dur["golpes"][1]
    caracteres = int((dur["s"] - COLA * n_max - COLA_CIERRE) * CPS)
    sugeridas = sugerir_tarjetas(hilo["tuits"], tarjetas, dur)
    st = {"hilo": rel(hilo_dir), "slug": hilo["slug"], "fecha_hilo": hilo.get("fecha"), "paleta": hilo["paleta"],
          "duracion": a.duracion, "objetivo_s": dur["s"], "musica": musica["id"],
          "ganchos_recientes": recientes, "cierres_recientes": cierres, "animaciones_recientes": anim_rec,
          "tarjetas": tarjetas, "sugeridas": sugeridas}
    escribir(os.path.join(trabajo, "video.json"), st)
    for aviso in rebasar_tarjetas(hilo_dir, trabajo):
        print("AVISO tarjetas: " + aviso, file=sys.stderr)

    giros = [x["n"] for x in tarjetas if x["beat"] == "giro"]
    impactos = [x["n"] for x in tarjetas if x["beat"] == "impacto"]
    dig = ["# Digesto para el guion del video · %s" % hilo["slug"], "",
           "- Tema: %s" % hilo.get("tema", ""), "- Tesis: %s" % hilo.get("tesis", ""),
           "- Paleta: %s · modo: %s · hook_tipo: %s" % (hilo["paleta"], hilo.get("modo", "hilo"), hilo.get("hook_tipo", "")),
           "- No afirma: %s" % "; ".join(hilo.get("no_afirma") or []),
           "", "## Presupuesto",
           "- Duración: **%s** = %d s ±%d %% · gancho + %d–%d tarjetas + %d–%d escenas de texto (golpes, ≤ 1 definición, ≤ 1 adivina) + cierre · voz total ≈ %d caracteres "
           "(con las cifras ya en palabras; %.1f car/s)"
           % (a.duracion, dur["s"], TOLERANCIA * 100, *dur["tarjetas"], *dur["golpes"], caracteres, CPS),
           "- Voz por escena: gancho %d–%d · tarjeta %d–%d · golpe %d–%d · cierre %d–%d caracteres."
           % (*CARACTERES["gancho"], *CARACTERES["tarjeta"], *CARACTERES["golpe"], *CARACTERES["cierre"]),
           "- El gancho en 3 segundos: la primera oración de la voz ≤ %.0f s (≈ %d caracteres ya en palabras: el dato con su verbo "
           "y nada más); la promesa ≤ %.0f s si va en la escena 1, y si no cabe va en T1 (`en: 2`, lo normal en medio y largo); "
           "la voz entera del gancho ≤ %.0f s. La primera tarjeta entra antes de 6.5 s." % (GANCHO_ORACION_S, int(GANCHO_ORACION_S * CPS), PROMESA_S, GANCHO_VOZ_S),
           "- Pausas: escribe `[pausa]` (0.6 s) tras un punto o justo antes de un «pero» cuando el silencio ayude (el giro del "
           "gancho, antes de la cifra del pago); ≤ %d por escena y ≤ %d en el video. No cuentan como caracteres." % (PAUSAS_MAX_ESCENA, PAUSAS_MAX_VIDEO),
           "- Ritmo: dentro de cada escena, como mucho %.0f s (≈ %d caracteres) entre el inicio, el fin de la primera "
           "oración, cada cifra y el fin: la cifra, pronto." % (RITMO_MAX_S, RITMO_MAX_S * CPS),
           "- Escenas a pantalla completa (≤ 1 de cada; la misma tarjeta no va dos veces): `mapa` (tarjeta mapa); `ranking` "
           "(tarjeta barras-h o mapa; `top` %d–%d, `orden` desc|asc; los puestos entran del último al primero cuando la voz dice "
           "su valor: la voz dice al menos el del primero); `tiempo` (tarjeta antes-despues o linea: riel con los puntos, el "
           "valor salta al decirlo); `escala` (sin tuit: `de_cada: [K, N]`, `etiqueta` ≤ %d, `calculo`, y la voz dice «K de "
           "cada N»; N figuras y se encienden K)." % (*RANKING_TOP, ESCALA_ETIQUETA),
           ("- Icono (opcional, `icono: \"<id>\"` en gancho, golpe o definición; ≤ 1 por escena y solo si nombra el tema de la "
            "cifra, nunca decorativo): " + " · ".join("%s (%s)" % (k, v) for k, v in (iconos_catalogo() or {}).items()))
           if iconos_catalogo() else "- Iconos: sin biblioteca (make iconos); no uses `icono`.",
           *lineas_animaciones(anim_rec, a.sin_rotacion),
           "- «Guatemala» se dice o se lee en los primeros 6 s (R6): en la voz o la pantalla del gancho, o en la primera oración "
           "de T1. El script ya no antepone «En Guatemala» y la voz no abre con contexto (R3).",
           "- Música: %s (%s)" % (musica["id"], musica.get("ambiente", "")),
           "", "## Narración (V17–V18: las reglas de narración de /historia)",
           "- PRIMERO escribe `narracion`: 3 actos de texto corrido que cuentan el hilo como una historia, en una sola voz: acto 1 "
           "= el gancho tal cual, T1 y quién vive la cifra (la gente, el lugar) hasta la promesa; acto 2 = el nudo (el giro); "
           "acto 3 = el impacto, el pago y el cierre. Cada oración sigue de la anterior con un porque, un pero o un entonces "
           "(≥ %d conectores causales o temporales por acto, nunca «y luego»); los saltos de tiempo y de lugar se dicen; cada "
           "institución se presenta la primera vez; las cifras van dentro de oraciones que cuentan algo, nunca «X: cifra, cifra»; "
           "«esos N…» solo si ya se dijo; «según» ≤ %d. Mídela: `python3 scripts/video.py narracion TRABAJO --check`."
           % (CONECTORES_MIN_ACTO.get(a.duracion, CONECTORES_MIN_ACTO_DEF), SEGUN_MAX_DATO),
           "- DESPUÉS repártela en escenas SIN cambiar una palabra (cada escena con su `acto`; cada acto es la suma literal de "
           "sus voces y, en el 3, del cierre). El gate agrupa las escenas seguidas de un acto en secuencias de voz grabadas de "
           "una vez.",
           "", "## Estructura (la comprueba el gate V9)",
           "1. Escena 1 = **gancho**: lo escribe el agente `video-gancho` (4–5 candidatos en ganchos.json) y lo elige el crítico; "
           "el guionista lo copia con `video.py ganchos TRABAJO --usar` y no lo cambia. `familia` (%s), `visual` (%s), "
           "`pantalla` (una cifra o ≤ %d palabras, ≤ %d caracteres) y `linea` (≤ %d palabras, ≤ %d caracteres) cuentan el gancho "
           "**en silencio**; la voz es una oración con `verbo`. Reglas R1–R12 en referencias/ganchos.md."
           % (" | ".join(FAMILIAS), " | ".join(VISUALES), PANTALLA_PALABRAS, PANTALLA_CARACTERES, LINEA_PALABRAS, LINEA_CARACTERES),
           "2. Escena 2 = la **tarjeta T1**, sin enlace. Luego tarjetas y golpes en el orden del arco.",
           "3. `enlace` (pero | por_eso | y) es opcional desde la escena 3: solo elige el efecto de sonido. La causalidad va en "
           "la narración (un «pero» o un «por eso» puede ir en medio de la oración); marca el giro con `enlace: \"pero\"`.",
           "4. Cada tarjeta lleva `golpe` (≤ %d palabras, ≤ %d caracteres): el re-gancho que va arriba, en lenguaje llano, con la "
           "cifra si cabe; nunca el titular de la tarjeta." % (GOLPE_PALABRAS, GOLPE_CARACTERES),
           "5. Las escenas `golpe` (texto a pantalla completa) llevan `pantalla` + `linea` + `verbo`; nunca dos seguidas ni en la escena 2; "
           "sirven para traducir la cifra anterior a escala humana, pagar la promesa o re-ganchar a mitad.",
           "6. `promesa`: {texto (10–80 caracteres, LITERAL en la voz de la escena `en` = 1 o 2), en, pago (escena del último tercio "
           "que cierra exactamente esa brecha)}. Es una oración propia con verbo que nombra qué falta saber: no empieza con «Y», "
           "«Pero» ni «Así que» suelto y nunca dice «al final te digo» (el gate lo rechaza). Varía la fórmula respecto de «Frases "
           "ya usadas»: «Quédate hasta el final y sabrás cuántas…», «Al final vas a ver…», «Espera al final: ahí está…».",
           "7. `calculo` (opcional en tarjetas y gancho; obligatorio en un golpe con un número nuevo): ids del digesto (%s), literales de "
           "datos.json, constantes 7/12/24/30/31/52/100/365/1000 y + − × ÷ ( ); su resultado debe aparecer escrito en la escena "
           "(«1 de cada 3», «×5», «52%%»)." % ", ".join(sorted(cifras)[:3] + [sorted(cifras)[0] + ".serie[0]", sorted(cifras)[0] + ".partes[1]"]),
           "8. Escena `definicion` (opcional, ≤ 1; escena de texto): `termino` (≤ %d palabras, ≤ %d caracteres), `definicion` (≤ %d "
           "caracteres, en lenguaje llano), `enlace` y `texto` que dice el término. Para el término que la cifra necesita y el espectador "
           "no leyó (Fase 3+ de la CIF, anomalía ONI). La voz **anuncia el concepto antes de decir el término** («Para "
           "entenderlo mejor: la Fase 3+ es…», «¿Qué es la Fase 3+?», «Antes de seguir, un concepto: …»); el gate lo exige." % (TERMINO_PALABRAS, TERMINO_CARACTERES, DEFINICION_CARACTERES),
           "9. Escena `adivina` (opcional, ≤ 1, desde la escena 3; escena de texto): `pregunta` (≤ %d caracteres, termina en «?»), "
           "`opciones` (3 cadenas ≤ %d caracteres con cifra: una con respaldo o `calculo`, las otras dos señuelos plausibles del mismo "
           "formato), `correcta` (0–2), `enlace` y `texto`: la pregunta (con las mismas palabras que la `pregunta` en pantalla: se escribe al ritmo de la voz), las tres opciones y, en una oración final, la respuesta (la "
           "última cifra de la voz); el script mete la pausa antes de la respuesta. Abre un bucle a mitad del video." % (PREGUNTA_CARACTERES, OPCION_CARACTERES),
           "10. Escena `mapa` (opcional, ≤ 1; cuenta como tarjeta): `tipo: \"mapa\"` con el `tuit` de la tarjeta de mapa del hilo, `golpe`, "
           "`enlace` y `texto`. El mapa de los 22 departamentos a pantalla completa, sin columna: se encienden uno a uno, el destacado "
           "entra al final con su rótulo y cada valor que diga la voz ilumina su departamento (di 2–3 valores con su nombre). Esa tarjeta "
           "no va además como `tarjeta`. Mejor que la tarjeta cuando el hilo es medio o largo.",
           "11. Escena `explica` (opcional, ≤ 1; 2 en largo; cuenta como escena de texto): una animación que explica el MECANISMO "
           "del fenómeno (por qué o cómo pasa: cómo se forma una cola, por qué la sequía da hambre), no los datos. `mecanismo` (de la "
           "lista de arriba), `brief` SIEMPRE (%d–%d caracteres: qué se ve y cómo se mueve), `animacion` (id de una ya hecha con "
           "ese mismo mecanismo y no bloqueada) o `null` (la escribe el animador a medida), `titulo` "
           "(≤ %d palabras), `pasos` (%d–%d, ≤ %d caracteres, sin cifras salvo con respaldo), `enlace` y `texto` que dice cada paso "
           "(entra cuando la voz lo dice). Cada afirmación causal es de conocimiento general o del hilo y no contradice `no_afirma` "
           "(«uno de los factores», nunca «la causa»)." % (*BRIEF_CARACTERES, TITULO_PALABRAS, *EXPLICA_PASOS, PASO_CARACTERES),
           "12. **Cierre**: las cifras van en las conclusiones (`texto` antes de la frase final y `resumen`); la frase final NO "
           "es un dato sino su **consecuencia**: `tipo` remate, `forma` consecuencia (lo normal) con `consecuencia` {mecanismo "
           "%s, quien (gente: «34 familias», «los conductores de la ruta»), verbo (conjugado, en pasado o presente)} — lo que "
           "la cifra le hace a quien la vive («Este año, 34 familias ya enterraron a un hijo por desnutrición.»), sin repetir la "
           "cifra del gancho, ≤ 1 cifra, sin fatalismo («no hay nada que hacer») ni futuro que la fuente no proyecta, sin "
           "adjetivos que lloren por el espectador; a veces `pendiente` o `quien_decide`; o pregunta (a veces: nunca si el "
           "video anterior cerró con pregunta). `final` (≤ %d palabras) = la última frase de `texto`; nombra el tema del "
           "video, sin cebo y, en un tema sensible, sin preguntar por la vida del espectador. Reglas F1–F8 en "
           "referencias/cierres.md." % ("|".join(MECANISMOS), FINAL_PALABRAS),
           "", "## Ganchos recientes (R9: no repitas familia ni visual)"] + lineas_recientes(recientes, a.sin_rotacion) + [
           "", "## Cierres recientes (F7)",
           "- %s" % ("(prueba: sin rotación)" if a.sin_rotacion else "Último cierre: %s · formas bloqueadas: %s · mecanismo de "
               "consecuencia bloqueado: %s%s" % (
               ", ".join(cierres["tipos"]) or "—",
               ", ".join(x for x in cierres["formas"] if x != "consecuencia") or "ninguna",
               ", ".join(cierres.get("mecanismos") or []) or "ninguno",
               " · **este video cierra con un remate**" if "pregunta" in cierres["tipos"] else "")),
           "- Remates: %s (consecuencia: %s) · preguntas: %s" % (", ".join(x for x in CIERRE_FORMAS["remate"] if x != "legado"), "|".join(MECANISMOS),
                                                               ", ".join(CIERRE_FORMAS["pregunta"])),
           "", "## Frases ya usadas (no las repitas: C11 del crítico)"] + frases_usadas(hilo["slug"]) + [
           "", "## Sugerencia de tarjetas (no obligatoria)",
           "- Orden sugerido: %s (T1, luego giro e impacto, luego contexto animado). Giro: %s · impacto: %s. Marca el giro como tu "
           "«pero» mayor y un impacto como pago de la promesa."
           % (", ".join("T%d" % n for n in sugeridas), ", ".join("T%d" % n for n in giros) or "—", ", ".join("T%d" % n for n in impactos) or "—"),
           "", "## Tarjetas disponibles (la escena 2 usa T1)"] + lineas
    out = os.path.join(trabajo, "digesto.md")
    open(out, "w", encoding="utf-8").write("\n".join(dig) + "\n")
    print("\n".join(dig))
    print("\n→ %s · trabajo: %s" % (rel(out), rel(trabajo)))
    return 0


# ---------- gate del guion (V1–V5, V9) ----------
def valores_respaldo(hilo_dir):
    """Como G10 de ensamblar.py, desde el entregable: `valor` ya es el final; `valor_original` no respalda.
    Devuelve (valores (número, factor), titulares, cifras verificadas por id)."""
    datos = leer(os.path.join(RAIZ, hilo_dir, "datos.json"))
    hilo = leer(os.path.join(RAIZ, hilo_dir, "hilo.json"))
    valores, por_id, cifras = set(), {}, {}
    for c in datos["cifras"]:
        if c.get("veredicto") not in ("verificada", "ajustada"):
            continue
        nums = [c.get("valor")] + [p.get("v") for p in c.get("serie") or []] + \
               [p.get("valor") for p in c.get("partes") or []]
        f = VM.factor_unidad(c.get("unidad"))
        valores |= {(round(float(x), 6), f) for x in nums if isinstance(x, (int, float)) and not isinstance(x, bool)}
        por_id[c["id"]] = c.get("valor")
        cifras[c["id"]] = c
    titulares = [por_id[i] for t in hilo["tuits"] for i in t.get("cifra_ids") or []
                 if isinstance(por_id.get(i), (int, float))]
    return sorted(valores), titulares, cifras


def oracion_de_la_pantalla(texto, pantalla):
    """La oración de la voz que dice la cifra de la pantalla (o la primera si la pantalla no lleva cifra). Se corta
    en . ? ! ; … (no en «:», que en la voz encadena)."""
    oraciones = [o.strip() for o in re.split(r"(?<=[.?!;…])\s+", (texto or "").strip()) if o.strip()]
    if not oraciones:
        return ""
    for n in re.findall(NE.NUM, pantalla or ""):
        for o in oraciones:
            if re.search(r"(?<![\d,.])%s(?!\d)" % re.escape(n), o):
                return o
    return oraciones[0]


def falta_verbo(e):
    """V9: la pantalla de un gancho o golpe puede ser titular («Casi 168 al día»), la voz no: la oración que la
    dice lleva un verbo conjugado, declarado en `verbo` («En Guatemala nacen casi 168 bebés al día…»).
    Devuelve el motivo de la falla o None."""
    verbo = (e.get("verbo") or "").strip()
    oracion = oracion_de_la_pantalla(e.get("texto"), e.get("pantalla"))
    if not verbo:
        return ("falta «verbo»: el verbo conjugado de la oración «%s» (p. ej. «nacen», «llegó», «es»); la pantalla "
                "puede ser titular, la voz es una oración completa" % oracion)
    if not re.fullmatch(r"[^\W\d_]+", verbo) or _plano(verbo) in STOP:
        return "verbo «%s» debe ser una sola palabra: el verbo conjugado de la oración que dice la pantalla" % verbo
    if _plano(verbo) not in _plano(oracion).split():
        return ("la oración «%s» no lleva el verbo «%s»: la voz no es el titular de la pantalla leído en voz alta, es una "
                "oración con verbo conjugado («En Guatemala nacen casi 168 bebés al día…», no «casi 168 bebés al día…»)"
                % (oracion, verbo))
    return None


def _coincide(x, v, tol):
    return VM.coincide(x, [(v, tol)], escalas=(1,))


def resolver_calculo(expr, cifras, valores):
    """Evalúa un `calculo` del guion: ids de cifra (pre-c01, pre-c01.serie[0], pre-c04.partes[1]) → su valor; los literales
    deben estar en el respaldo, en CONSTANTES_CALCULO o ser enteros ≤ 12. Devuelve (valor, None) o (None, motivo)."""
    expr = str(expr or "")
    if not expr.strip():
        return None, "vacío"

    def sust(m):
        cid, campo, idx = m.group(1), m.group(2), m.group(3)
        c = cifras.get(cid)
        if not c:
            raise KeyError("usa la cifra %s que no existe o no está verificada" % cid)
        if campo:
            lista = c.get(campo) or []
            try:
                p = lista[int(idx)]
            except IndexError:
                raise KeyError("%s.%s[%s] no existe" % (cid, campo, idx))
            v = p.get("v") if campo == "serie" else p.get("valor")
        else:
            v = c.get("valor")
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise KeyError("%s no tiene valor numérico" % m.group(0))
        return "(%r)" % float(v)
    try:
        sustituida = RE_CIFRA_ID.sub(sust, expr)
    except KeyError as e:
        return None, str(e)
    for m in re.finditer(NE.NUM, RE_CIFRA_ID.sub("", expr)):
        v = float(m.group().replace(",", ""))
        if v in CONSTANTES_CALCULO or (v.is_integer() and v <= 12):
            continue
        tol = 0.5 * 10 ** -VM.decimales(v)
        if any(VM.coincide(x, [(v, tol)], escalas=(f or 1.0,)) for x, f in valores):
            continue
        return None, "usa el literal %s que no está en datos.json" % m.group()
    r = VM.evaluar(sustituida)
    if r is None:
        return None, ("ilegible: ids (nar-c02, nar-c02.partes[1], nar-c02.serie[-1]), literales de datos.json, "
                      "constantes (7, 12, 24, 30, 31, 52, 100, 365, 1000) y + − × ÷ ( )")
    return r, None


def escribe_numero(r, textos):
    """True si el resultado r de un calculo aparece escrito (con su redondeo) en alguno de los textos."""
    for t in textos:
        t = VM.RE_FECHA.sub(" ", t or "")
        for m in RE_DE_CADA.finditer(t):
            a, b = float(m.group(1)), float(m.group(2))
            if a and (_coincide(r, b / a, 0.5 / a) or de_cada_pct(r, a, b)):
                return True
        for m in re.finditer(NE.NUM, t):
            v = float(m.group().replace(",", ""))
            if _coincide(r, v, 0.5 * 10 ** -VM.decimales(v)):
                return True
    return False


def de_cada_pct(r, a, b):
    """«A de cada B» como porcentaje r, con el redondeo que implica B: «7 de cada 10» vale para 65–75 % (70.74 % → 7 de
    cada 10), «71 de cada 100» para 70.5–71.5 %."""
    return _coincide(r, 100 * a / b, 50 / b)


def exentar_de_cada(texto, vals):
    """«A de cada B» deja de contar como números sueltos cuando B/A tiene respaldo en vals (o A lo tiene cuando
    B = 100): la escala humana («1 de cada 4», «77 de cada 100») se respalda por su `calculo`, no por A y B."""
    def de_cada(m):
        a, b = float(m.group(1)), float(m.group(2))
        if a and any(_coincide(x, b / a, 0.5 / a) or de_cada_pct(x, a, b) for x, f in vals):
            return " "
        return m.group(0)
    return RE_DE_CADA.sub(de_cada, texto or "")


def sin_respaldo(texto, valores, extra=()):
    """Números de un texto de pantalla (golpe, pantalla, linea) sin respaldo: como `sueltos` con max_entero=1, y
    «A de cada B» vale si B/A está respaldado (o A lo está cuando B = 100)."""
    vals = list(valores) + [(round(float(x), 6), 1.0) for x in extra]
    return VM.sueltos(exentar_de_cada(texto, vals), vals, max_entero=1)


def es_anio_o_fecha(seg_p, siguiente):
    m = re.search(NE.NUM, seg_p)
    if not m:
        return True
    v = float(m.group().replace(",", ""))
    return (v.is_integer() and 1900 <= v <= 2100) or bool(re.match(r"de %s" % MESES, siguiente.strip().lower()))


def hueco_maximo(segs, voz):
    """Ritmo estimado de una escena: segundos entre eventos consecutivos {inicio, fin de la primera oración, fin de
    cada cifra (sin años ni fechas), fin}. Devuelve (segundos, texto antes, texto después)."""
    marcas = [0]
    m = RE_FIN_ORACION.search(voz)
    if m:
        marcas.append(m.end())
    pos = 0
    for k, s in enumerate(segs):
        pos += len(s["v"])
        if s["num"] and not es_anio_o_fecha(s["p"], "".join(x["v"] for x in segs[k + 1:k + 3])):
            marcas.append(pos)
    marcas.append(len(voz))
    marcas = sorted(set(marcas))
    a, b = max(zip(marcas, marcas[1:]), key=lambda ab: ab[1] - ab[0])
    return (b - a) / CPS, voz[max(0, a - 25):a].strip(), voz[b:b + 25].strip()


# ---------- gancho (catálogo de familias y visuales: referencias/ganchos.md) ----------
def numeros_sin_anios(s):
    """Números de un texto sin los años (1900–2100 enteros)."""
    out = []
    for m in re.finditer(NE.NUM, VM.RE_FECHA.sub(" ", s or "")):
        v = float(m.group().replace(",", ""))
        if not (v.is_integer() and 1900 <= v <= 2100):
            out.append(v)
    return out


def valor_visual(x, cifras, valores):
    """Un número del visual: literal con respaldo en datos.json o expresión `calculo` (ids de cifra) → (valor, motivo)."""
    if isinstance(x, bool) or x is None or x == "":
        return None, "falta"
    if isinstance(x, (int, float)):
        sin = sin_respaldo(clave(float(x)), valores)
        return (None, "no tiene respaldo en datos.json (usa el id de la cifra: «pen-c02.partes[1]»)") if sin else (float(x), None)
    r, motivo = resolver_calculo(str(x), cifras, valores)
    return (None, motivo) if motivo else (r, None)


def visual_del_gancho(e, cifras, valores):
    """Datos del visual del gancho (VISUALES) resueltos, con respaldo (V2) → (resuelto, fallas). El resuelto lleva
    `numeros`: los valores que la voz o la pantalla deben decir (R4) y que V2 acepta como respaldados."""
    vis = e.get("visual") or "cifra"
    d = e.get("visual_datos") or {}
    out, f, nums = {"tipo": vis}, [], []

    def num(campo, x):
        v, motivo = valor_visual(x, cifras, valores)
        if motivo:
            f.append("visual %s: %s «%s» %s" % (vis, campo, x, motivo))
            return None
        nums.append(v)
        return v

    def etiqueta(campo, x, maximo):
        x = (x or "").strip()
        if not x or len(x) > maximo:
            f.append("visual %s: «%s» de 1–%d caracteres" % (vis, campo, maximo))
        return x
    if vis not in VISUALES:
        return out, ["visual «%s» no es %s" % (vis, "|".join(VISUALES))]
    if vis == "llenado":
        cap, tot = num("capacidad", d.get("capacidad")), num("total", d.get("total"))
        out.update(capacidad=cap, total=tot, unidad=etiqueta("unidad", d.get("unidad"), VISUAL_ETIQUETA))
        if cap is not None and tot is not None and not 0 < cap < tot:
            f.append("visual llenado: 0 < capacidad < total (llegaron %s y %s): el contenedor se desborda" % (clave(cap), clave(tot)))
    elif vis == "pareja":
        for k in ("a", "b"):
            p = d.get(k) or {}
            v = num(k + ".valor", p.get("valor"))
            out[k] = {"valor": v, "etiqueta": etiqueta(k + ".etiqueta", p.get("etiqueta"), VISUAL_ETIQUETA)}
            if v is not None and v <= 0:
                f.append("visual pareja: %s.valor debe ser mayor que 0" % k)
    elif vis == "figuras":
        dc = d.get("de_cada")
        if not (isinstance(dc, list) and len(dc) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in dc)
                and ESCALA_N[0] <= dc[1] <= ESCALA_N[1] and 1 <= dc[0] < dc[1]):
            f.append("visual figuras: de_cada [K, N] enteros con 1 ≤ K < N y N entre %d y %d" % ESCALA_N)
            dc = None
        out.update(etiqueta=etiqueta("etiqueta", d.get("etiqueta"), ESCALA_ETIQUETA))
        if dc:
            out.update(k=dc[0], n=dc[1])
            r, motivo = resolver_calculo(d.get("calculo"), cifras, valores) if d.get("calculo") else (None, "falta: «K de cada N» se respalda con un calculo")
            if motivo:
                f.append("visual figuras: calculo «%s» %s" % (d.get("calculo") or "", motivo))
            elif not escribe_numero(r, ["%d de cada %d" % tuple(dc)]):
                f.append("visual figuras: calculo %s da %.4g y no respalda «%d de cada %d»" % (d["calculo"], r, *dc))
            else:
                nums.append(r)
    elif vis == "lugar":
        dep, nombres = (d.get("depto") or "").strip(), nombres_depto()
        cod = dep if dep in nombres else next((k for k, v in nombres.items() if _plano(v) == _plano(dep)), None)
        if not cod:
            f.append("visual lugar: «depto» «%s» no es uno de los 22 departamentos (nombre o código GTxx)" % dep)
        out.update(depto=cod, nombre=nombres.get(cod), etiqueta=etiqueta("etiqueta", d.get("etiqueta"), LUGAR_ETIQUETA))
    out["numeros"] = nums
    return out, f


def periodos_de(nums, cifras):
    """Años de los periodos de las cifras cuyos valores (valor, serie o partes) aparecen en `nums`."""
    anios = []
    for c in cifras.values():
        vals = [c.get("valor")] + [p.get("v") for p in c.get("serie") or []] + [p.get("valor") for p in c.get("partes") or []]
        vals = [float(x) for x in vals if isinstance(x, (int, float)) and not isinstance(x, bool)]
        if any(_coincide(x, v, 0.5 * 10 ** -VM.decimales(v)) for v in nums for x in vals):
            anios += [int(y) for y in RE_ANIO.findall(str(c.get("periodo", "")))]
    return anios


def reglas_gancho(e, voz_p, ctx):
    """R2–R10 del gancho (referencias/ganchos.md) sobre una escena gancho → (fallas, avisos). `voz_p` es la voz con
    las cifras en dígitos (lo que se subtitula); ctx = {cifras, valores, recientes {familias, visuales}, anio,
    e2 (voz de la escena 2 o None si aún no hay guion), visual (lo que devolvió visual_del_gancho)}."""
    f, av = [], []
    fam, vis = e.get("familia"), e.get("visual") or "cifra"
    pant, lin, texto = e.get("pantalla") or "", e.get("linea") or "", sin_pausas(e.get("texto") or "").strip()
    V_ = ctx.get("visual") or {}
    if fam not in FAMILIAS:
        f.append("familia «%s» no es %s%s" % (fam, "|".join(FAMILIAS),
                 " (`formula` es del formato viejo: usa `familia`, referencias/ganchos.md)" if e.get("formula") and not fam else ""))
        return f, av
    if vis not in VISUALES_DE[fam]:
        f.append("el visual «%s» no va con la familia %s (admite %s)" % (vis, fam, ", ".join(VISUALES_DE[fam])))
    if e.get("icono") and vis != "cifra":
        f.append("el icono va solo con el visual cifra (con %s, el visual ya nombra el tema)" % vis)
    silencio = " ".join((pant, lin))
    # R2 referente: la cifra nunca va sola
    if fam != "pregunta" and vis in ("cifra", "lugar") and len(set(numeros_sin_anios(silencio))) < 2 and not (
            RE_DE_CADA.search(silencio) or re.search(r"×\s?\d|\d\s*veces\b|\bde\s+\d[\d,]*\b|\bpor\s+(?:cada\s+)?\w+", silencio, re.I)):
        f.append("R2 la cifra va sola en pantalla («%s»): dale un referente que se lea en silencio (dos cifras, «K de cada N», "
                 "«×N», «de 209», «por lugar») o un visual llenado, pareja o figuras" % silencio.strip())
    # R3 tensión primero
    if APERTURAS_PROHIBIDAS.match(texto):
        f.append("R3 la voz abre con contexto («%s…»): abre con la tensión (el contraste, la paradoja, el lugar, la escala); "
                 "«Guatemala» va dentro de la frase o en la segunda oración" % " ".join(texto.split()[:4]))
    # R4 triple alineación: los números del visual se dicen o se leen
    dichos = [pant, lin, voz_p]
    if vis in ("llenado", "pareja"):
        for v in [x for x in V_.get("numeros", []) if x is not None]:
            if not escribe_numero(v, dichos):
                f.append("R4 el visual %s muestra %s y ni la voz ni la pantalla lo dicen: imagen, pantalla y voz cuentan lo mismo"
                         % (vis, clave(v)))
    elif vis == "figuras" and V_.get("k"):
        if (V_["k"], V_["n"]) not in [(int(a), int(b)) for a, b in RE_DE_CADA.findall(" ".join(dichos))]:
            f.append("R4 el visual figuras muestra «%d de cada %d» y ni la voz ni la pantalla lo dicen" % (V_["k"], V_["n"]))
    elif vis == "lugar" and V_.get("nombre"):
        claves_lugar = [_plano(V_["nombre"])] + [w for w in _plano(V_.get("etiqueta")).split() if len(w) >= 4 and w not in STOP]
        if not any(c and c in _plano(" ".join(dichos)) for c in claves_lugar):
            f.append("R4 el visual lugar señala %s y ni la voz ni la pantalla nombran el lugar" % V_["nombre"])
    # R6 Guatemala en ≤ 6 s
    if not RE_GUATEMALA.search(" ".join((texto, pant, lin))):
        e2 = ctx.get("e2")
        if e2 is None:
            av.append("R6 el gancho no dice «Guatemala»: dilo en la primera oración de T1 o el gate del guion fallará")
        elif not RE_GUATEMALA.search(re.split(r"(?<=[.?!…])\s+", sin_pausas(e2).strip())[0]):
            f.append("R6 «Guatemala» no se dice ni se lee en los primeros 6 s: va en la voz o la pantalla del gancho, o en la "
                     "primera oración de T1 (ya no se antepone «En Guatemala»)")
    # R7 honestidad temporal
    etiquetas_v = " ".join(str(x) for x in (V_.get("etiqueta"), V_.get("unidad"), (V_.get("a") or {}).get("etiqueta"),
                                              (V_.get("b") or {}).get("etiqueta")) if x)
    m = RE_AHORA.search(" ".join((texto, pant, lin, etiquetas_v)))
    if m:
        anios = periodos_de(numeros_sin_anios(" ".join(dichos)) + list(V_.get("numeros") or []), ctx["cifras"])
        if not anios or max(anios) < ctx["anio"]:
            f.append("R7 «%s» con un dato de %s: di el periodo («en 2025 tenía…»), no «%s»"
                     % (m.group(), max(anios) if anios else "fecha desconocida", m.group()))
    # R8 la pregunta se contesta en el gancho
    if fam == "pregunta":
        if not (pant.rstrip().endswith("?") or lin.rstrip().endswith("?")):
            f.append("R8 familia pregunta: pantalla o línea terminan en «?»")
        q = voz_p.rfind("?")
        if q < 0 or not numeros_sin_anios(voz_p[q + 1:]):
            f.append("R8 la pregunta se contesta con una cifra en el mismo gancho (después del «?»): una pregunta sin respuesta "
                     "pronta es un titular de pregunta y rinde peor")
    # R9 rotación
    rec = ctx.get("recientes") or {}
    if fam in (rec.get("familias") or []):
        f.append("R9 la familia «%s» ya abrió uno de los últimos %d videos (%s): usa otra" % (fam, ROTACION_FAMILIAS, ", ".join(rec["familias"])))
    if vis in (rec.get("visuales") or []):
        f.append("R9 el visual «%s» abrió el video anterior: usa otro" % vis)
    # R10 al menos un número con respaldo en los primeros segundos
    if not (numeros_sin_anios(" ".join(dichos)) or V_.get("numeros")):
        f.append("R10 el gancho no trae ningún número (pantalla, línea, visual o voz): la cuenta es de datos")
    return f, av


def validar_estructura(g, st, dur, tarjetas):
    """V1 (tipos y rangos) y V9 (estructura de retención) sobre guion.json v2."""
    f = []
    escenas = g.get("escenas") or []
    if isinstance(g.get("gancho"), str):
        f.append("V1 «gancho» ya no existe: la escena 1 es {\"tipo\": \"gancho\", \"formula\", \"pantalla\", \"linea\", \"texto\"} "
                 "(referencias/roles/video-guionista.md)")
    tipos = [e.get("tipo") for e in escenas]
    for i, t in enumerate(tipos, 1):
        if t not in TIPOS:
            f.append("V1 escena %d: tipo «%s» desconocido (%s)" % (i, t, "|".join(TIPOS)))
    n_t, n_g = sum(1 for t in tipos if t in CON_TUIT), sum(1 for t in tipos if t in ESCENAS_TEXTO or t == "explica")
    if not dur["tarjetas"][0] <= n_t <= dur["tarjetas"][1]:
        f.append("V1 %d tarjetas; «%s» pide %d–%d" % (n_t, st["duracion"], *dur["tarjetas"]))
    if not dur["golpes"][0] <= n_g <= dur["golpes"][1]:
        f.append("V1 %d escenas de texto (golpes, definición, adivina, explica); «%s» pide %d–%d" % (n_g, st["duracion"], *dur["golpes"]))
    max_def = 2 if st["duracion"] == "largo" else 1
    if tipos.count("definicion") > max_def:
        f.append("V1 %d definiciones; máximo %d" % (tipos.count("definicion"), max_def))
    if tipos.count("adivina") > 1:
        f.append("V1 %d adivinas; máximo 1" % tipos.count("adivina"))
    if tipos.count("explica") > max_def:
        f.append("V1 %d escenas explica; máximo %d" % (tipos.count("explica"), max_def))
    if any(a == b == "explica" for a, b in zip(tipos, tipos[1:])):
        f.append("V1 dos escenas explica seguidas")
    cat_anim = animaciones_catalogo()
    for t in PANTALLA_COMPLETA:
        if tipos.count(t) > 1:
            f.append("V1 %d escenas %s; máximo 1" % (tipos.count(t), t))
    cat_iconos = iconos_catalogo()
    for i, e in enumerate(escenas, 1):   # icono: solo en escenas de texto cinético y solo de la biblioteca fija
        ic = e.get("icono")
        if not ic:
            continue
        if e.get("tipo") not in ICONO_TIPOS:
            f.append("V1 escena %d: `icono` solo va en gancho, golpe o definición (es %s)" % (i, e.get("tipo")))
        elif cat_iconos is None:
            f.append("V1 escena %d: icono «%s» sin biblioteca (make iconos)" % (i, ic))
        elif ic not in cat_iconos:
            f.append("V1 escena %d: icono «%s» no está en design/iconos/catalogo.json" % (i, ic))
    vistos = set()
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        if not (e.get("texto") or "").strip():
            f.append("V1 escena %d sin texto" % i)
        if tipo == "escala":   # «K de cada N» con N figuras; tuit opcional (waffle o pictograma)
            dc = e.get("de_cada")
            if not (isinstance(dc, list) and len(dc) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in dc)):
                f.append("V1 escena %d: escala necesita de_cada: [K, N] (enteros)" % i)
            elif not (ESCALA_N[0] <= dc[1] <= ESCALA_N[1] and 1 <= dc[0] < dc[1]):
                f.append("V1 escena %d: de_cada [%s, %s] fuera de rango (1 ≤ K < N, N entre %d y %d)" % (i, dc[0], dc[1], *ESCALA_N))
            if len(e.get("etiqueta") or "") > ESCALA_ETIQUETA:
                f.append("V1 escena %d: etiqueta de más de %d caracteres" % (i, ESCALA_ETIQUETA))
            if not e.get("calculo"):
                f.append("V2 escena %d: la escala necesita `calculo` que respalde «K de cada N»" % i)
            if e.get("tuit") is not None and (e["tuit"] not in tarjetas or tarjetas[e["tuit"]].get("plantilla") not in PLANTILLAS_DE["escala"]):
                f.append("V1 escena %d: el tuit de una escala es una tarjeta %s" % (i, " o ".join(PLANTILLAS_DE["escala"])))
        if tipo not in CON_TUIT:
            continue
        n = e.get("tuit")
        if n not in tarjetas:
            f.append("V1 escena %d: T%s no tiene tarjeta en el hilo" % (i, n))
        elif tipo in PLANTILLAS_DE and tarjetas[n].get("plantilla") not in PLANTILLAS_DE[tipo]:
            f.append("V1 escena %d: la escena %s necesita una tarjeta %s (T%s es %s)" % (i, tipo, " o ".join(PLANTILLAS_DE[tipo]), n, tarjetas[n].get("plantilla")))
        elif tipo in ("ranking", "tiempo") and tarjetas[n].get("datos") is None:
            f.append("V1 escena %d: la escena %s necesita los DATA de T%s (video.json sin «datos»: corre preparar de nuevo)" % (i, tipo, n))
        elif tipo == "ranking":
            top = e.get("top", RANKING_TOP_DEFECTO)
            its = items_de(tarjetas[n]["datos"], e.get("orden"))
            if not (isinstance(top, int) and RANKING_TOP[0] <= top <= RANKING_TOP[1]):
                f.append("V1 escena %d: top %r fuera de %d–%d" % (i, top, *RANKING_TOP))
            elif len(its) < top:
                f.append("V1 escena %d: T%s tiene %d items y el ranking pide top %d" % (i, n, len(its), top))
            if e.get("orden") not in (None, "desc", "asc"):
                f.append("V1 escena %d: orden «%s» (desc|asc)" % (i, e.get("orden")))
        elif tipo == "tiempo" and len(puntos_de(tarjetas[n]["datos"])) < 2:
            f.append("V1 escena %d: T%s no da dos puntos para la línea de tiempo (antes/despues o series con etiquetasX)" % (i, n))
        if n in vistos:
            f.append("V1 escena %d: T%s repetida" % (i, n))
        vistos.add(n)
    if not (g.get("contexto_superior") or "").strip() or len(g.get("contexto_superior", "")) > 40:
        f.append("V1 «contexto_superior» vacío o de más de 40 caracteres")
    # secuencias de voz (forma): listas de 2–SECUENCIA_MAX escenas consecutivas, disjuntas, sin la escena 1
    secs = g.get("secuencias")
    if secs is not None:
        vistas = set()
        if not isinstance(secs, list):
            f.append("V9 «secuencias»: lista de grupos de escenas ([[2,3],[4,5,6]…])")
            secs = []
        for k, grupo in enumerate(secs, 1):
            if not isinstance(grupo, list) or not all(isinstance(n, int) and not isinstance(n, bool) for n in grupo):
                f.append("V9 secuencia %d: lista de números de escena" % k)
                continue
            if not 2 <= len(grupo) <= SECUENCIA_MAX:
                f.append("V9 secuencia %d: %d escenas; van 2–%d" % (k, len(grupo), SECUENCIA_MAX))
            if grupo != list(range(grupo[0], grupo[0] + len(grupo))) if grupo else False:
                f.append("V9 secuencia %d: escenas consecutivas (%s)" % (k, grupo))
            if any(n < 2 or n > len(escenas) for n in grupo):
                f.append("V9 secuencia %d: escenas entre 2 y %d (el gancho y el cierre van solos)" % (k, len(escenas)))
            if vistas & set(grupo):
                f.append("V9 secuencia %d: escenas repetidas en otra secuencia" % k)
            vistas |= set(grupo)
    if g.get("voz_continua") and not secs:
        f.append("V9 voz_continua exige «secuencias»")
    cierre = g.get("cierre") or {}
    for k in ("texto", "tipo", "forma", "final"):
        if not (cierre.get(k) or "").strip():
            f.append("V1 cierre sin «%s» (tipo remate|pregunta, forma del catálogo y final = la última frase de la voz)" % k)
    res = cierre.get("resumen") or []
    if not RESUMEN_LINEAS[0] <= len(res) <= RESUMEN_LINEAS[1] or any(not str(x).strip() or len(str(x)) > RESUMEN_CARACTERES for x in res):
        f.append("V1 cierre.resumen: %d–%d líneas de ≤ %d caracteres (las conclusiones)" % (*RESUMEN_LINEAS, RESUMEN_CARACTERES))
    if not escenas:
        return f

    # V9: gancho
    g1 = escenas[0]
    if g1.get("tipo") != "gancho":
        f.append("V9 la escena 1 debe ser tipo gancho")
    for i, e in enumerate(escenas[1:], 2):
        if e.get("tipo") == "gancho":
            f.append("V9 solo la escena 1 puede ser gancho (escena %d)" % i)

    def cinetico(i, e, etiqueta):
        for campo, maxp, maxc, desc in (("pantalla", PANTALLA_PALABRAS, PANTALLA_CARACTERES, "una cifra o ≤ %d palabras" % PANTALLA_PALABRAS),
                                        ("linea", LINEA_PALABRAS, LINEA_CARACTERES, "≤ %d palabras" % LINEA_PALABRAS)):
            v = (e.get(campo) or "").strip()
            if not v:
                f.append("V9 %s: falta «%s»" % (etiqueta, campo))
            elif palabras(v) > maxp or len(v) > maxc:
                f.append("V9 %s: %s «%s» de más de %d palabras o %d caracteres (%s)" % (etiqueta, campo, v, maxp, maxc, desc))
    if g1.get("tipo") == "gancho":
        cinetico(1, g1, "gancho")   # familia, visual y R2–R10: reglas_gancho, en cmd_guion (necesita la voz)
    # V9: escena 2 = T1
    if len(escenas) < 2 or escenas[1].get("tipo") != "tarjeta" or escenas[1].get("tuit") != 1:
        f.append("V9 la escena 2 debe ser la tarjeta T1 (el gancho se paga con la primera tarjeta)")
    elif escenas[1].get("enlace"):
        f.append("V9 escena 2: la primera tarjeta no lleva enlace")
    # V9: enlaces (opcionales: solo eligen el efecto de sonido; la causalidad vive en la narración, V18), golpes y
    # escenas golpe
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        enl = e.get("enlace")
        if i >= 3 and tipo in CON_TUIT + ESCENAS_TEXTO + ("explica",) and enl and enl not in ENLACES:
            f.append("V9 escena %d: enlace «%s» no es pero|por_eso|y" % (i, enl))
        if tipo in CON_TUIT:
            golpe = (e.get("golpe") or "").strip()
            if not golpe:
                f.append("V9 escena %d: tarjeta sin «golpe»" % i)
            elif palabras(golpe) > GOLPE_PALABRAS or len(golpe) > GOLPE_CARACTERES:
                f.append("V9 escena %d: golpe «%s» de más de %d palabras o %d caracteres" % (i, golpe, GOLPE_PALABRAS, GOLPE_CARACTERES))
            else:
                tit = _plano(tarjetas.get(e.get("tuit"), {}).get("titular"))
                gp = _plano(golpe)
                if tit and len(gp) >= 8 and (gp in tit or tit in gp):
                    f.append("V9 escena %d: golpe repite el titular de T%s («%s»)" % (i, e.get("tuit"), golpe))
        if tipo == "ranking" and tarjetas.get(e.get("tuit"), {}).get("datos") is not None:
            its = items_de(tarjetas[e["tuit"]]["datos"], e.get("orden"))
            if its and not escribe_numero(its[0][1], [e.get("texto")]):
                f.append("V9 escena %d: la voz no dice el valor del primer puesto (%s: %s)" % (i, its[0][0], its[0][1]))
        if tipo == "escala":
            dc = e.get("de_cada") or [None, None]
            if [int(a) for a in dc if isinstance(a, int)] != list(dc) or (dc[0], dc[1]) not in [(int(a), int(b)) for a, b in RE_DE_CADA.findall(e.get("texto") or "")]:
                f.append("V9 escena %d: la voz no dice «%s de cada %s»" % (i, dc[0], dc[1]))
            golpe = (e.get("golpe") or "").strip()
            if golpe and (palabras(golpe) > GOLPE_PALABRAS or len(golpe) > GOLPE_CARACTERES):
                f.append("V9 escena %d: golpe «%s» de más de %d palabras o %d caracteres" % (i, golpe, GOLPE_PALABRAS, GOLPE_CARACTERES))
        if tipo == "golpe":
            cinetico(i, e, "golpe escena %d" % i)
        elif tipo == "definicion":
            termino, definicion = (e.get("termino") or "").strip(), (e.get("definicion") or "").strip()
            if not termino or palabras(termino) > TERMINO_PALABRAS or len(termino) > TERMINO_CARACTERES:
                f.append("V9 escena %d (definicion): «termino» de 1–%d palabras y ≤ %d caracteres" % (i, TERMINO_PALABRAS, TERMINO_CARACTERES))
            if not definicion or len(definicion) > DEFINICION_CARACTERES:
                f.append("V9 escena %d (definicion): «definicion» de 1–%d caracteres, en lenguaje llano" % (i, DEFINICION_CARACTERES))
        elif tipo == "adivina":
            for motivo in adivina_mal_armada(e):
                f.append("V9 escena %d (adivina): %s" % (i, motivo))
        elif tipo == "explica":
            for motivo in explica_mal_armada(e, cat_anim, st.get("animaciones_recientes") or ()):
                f.append("V9 escena %d (explica): %s" % (i, motivo))
        if tipo in ESCENAS_TEXTO and i >= 2 and escenas[i - 2].get("tipo") in ESCENAS_TEXTO:
            f.append("V9 escena %d: dos golpes seguidos (golpe, definición y adivina son escenas de texto: entre dos va una tarjeta)" % i)
    # V9: promesa y pago
    p = g.get("promesa")
    n = len(escenas)
    if not isinstance(p, dict) or not all(k in p for k in ("texto", "en", "pago")):
        f.append("V9 promesa: falta {texto, en, pago}")
    else:
        txt = (p.get("texto") or "").strip()
        if not 10 <= len(txt) <= 80:
            f.append("V9 promesa.texto de 10–80 caracteres")
        if p.get("en") not in (1, 2):
            f.append("V9 promesa.en debe ser 1 o 2 (llegó %s)" % p.get("en"))
        elif txt and _plano(txt) not in _plano(escenas[p["en"] - 1].get("texto")):
            f.append("V9 promesa.texto no aparece literal en la voz de la escena %d" % p["en"])
        if txt and PROMESA_CONECTOR.match(txt):
            f.append("V9 promesa.texto empieza con un conector suelto («%s»): la promesa es una oración propia "
                     "(«Quédate hasta el final y sabrás…», «Al final vas a ver…»)" % txt.split()[0])
        if txt and PROMESA_PROHIBIDA.search(txt):
            f.append("V9 promesa.texto usa «al final te digo»: es la muletilla copiada de las guías; varía la fórmula "
                     "(«Quédate hasta el final y sabrás…», «Al final vas a ver…», «Espera al final: ahí está…»)")
        lo = math.ceil(2 * n / 3)
        if not isinstance(p.get("pago"), int) or not lo <= p["pago"] <= n or p["pago"] == p.get("en"):
            f.append("V9 promesa.pago = %s debe estar en el último tercio (escenas %d–%d) y ser distinto de «en»" % (p.get("pago"), lo, n))
    return f


def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    try:
        g = leer(os.path.join(trabajo, "guion.json"))
    except (OSError, ValueError) as e:
        return falla("guion.json ilegible: %s" % e)
    dur = DURACIONES[st["duracion"]]
    tarjetas = {t["n"]: t for t in st["tarjetas"]}
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    if NARRACION_VIDEO and escenas and g.get("secuencias") is None and g.get("narracion"):
        # la voz de corrido: tramos del mismo acto grabados de una vez (la adivina, con su pausa, va sola)
        g["secuencias"] = secuencias_por_defecto(g, sueltas=SIN_SECUENCIA)
        g["voz_continua"] = bool(g["secuencias"])
    fallas = validar_estructura(g, st, dur, tarjetas)
    if NARRACION_VIDEO:
        fallas += revisar_narracion_video(g, st)

    # V5 reglas
    textos = [e.get("texto", "") for e in escenas] + [cierre.get("texto", "")]
    pantallas = [" ".join(filter(None, (e.get("golpe"), e.get("pantalla"), e.get("linea")))) for e in escenas]
    todo = " ".join(textos + pantallas + [" ".join(cierre.get("resumen") or []), final_de(cierre),
                                          json.dumps(g.get("caption") or {}, ensure_ascii=False)])
    if re.search(r"\ben suma\b", todo, re.I):
        fallas.append("V5 «en suma» está prohibido")
    # la edad de quien murió o enfermó no se dice «no tenía(n) N años» (usuario, 2026-10-24: «6 de cada 7 fallecidos
    # no tenían dos años» no tiene coherencia): «eran menores de N años» o «murieron antes de cumplir N años»
    for m in RE_EDAD_NEGADA.finditer(" ".join(textos + pantallas + [final_de(cierre)])):
        fallas.append("V5 «%s» no se entiende: di «eran menores de %s años» o «antes de cumplir %s años»"
                      % (m.group(), m.group(1), m.group(1)))
    if re.search(r"https?://|@\w", " ".join(textos + pantallas)):
        fallas.append("V5 la voz y la pantalla no llevan enlaces ni @handles")
    ct = (cierre.get("texto") or "").strip()
    fin = final_de(cierre)
    if fin and not ct.endswith(fin):
        fallas.append("V5 cierre.texto debe terminar con cierre.final (la frase final: el remate o la pregunta)")
    if fin and ct.endswith(fin):
        antes_preg = ct[:len(ct) - len(fin)].strip()
        NE.AVISOS.clear()
        try:
            s_antes = len(NE.convertir(sin_pausas(antes_preg))[1]) / CPS
        except ValueError:
            s_antes = len(antes_preg) / CPS
        NE.AVISOS.clear()
        if s_antes < CIERRE_ANTES_S:
            fallas.append("V9 cierre: %.1f s de voz antes de la frase final (mínimo %.0f s): las conclusiones van en su propia "
                          "pantalla y necesitan tiempo para leerse" % (s_antes, CIERRE_ANTES_S))
    cierre_pantalla = " ".join([ct, " ".join(cierre.get("resumen") or []), fin])
    if PROHIBIDO_CIERRE.search(cierre_pantalla):
        fallas.append("V5 el cierre no menciona fuentes, el hilo, la marca ni «sígueme» (va solo en pantalla)")
    for k, _ in PLATAFORMAS:
        if not ((g.get("caption") or {}).get(k) or "").strip():
            fallas.append("V5 falta caption.%s" % k)
    sh = ((g.get("caption") or {}).get("shorts") or "").strip()
    if sh:
        titulo = sh.splitlines()[0].strip()
        if len(titulo) > SHORTS_TITULO:
            fallas.append("V5 caption.shorts: la primera línea es el título de YouTube (≤ %d caracteres; llegó %d)" % (SHORTS_TITULO, len(titulo)))
        if "#shorts" not in sh.lower():
            fallas.append("V5 caption.shorts lleva #Shorts")
    for k, v in (g.get("caption") or {}).items():
        if isinstance(v, str) and PROMESA_PROHIBIDA.search(v):
            fallas.append("V5 caption.%s usa «al final te digo / te lo digo al final»: varía la fórmula" % k)

    # V2, V3, V4 y ritmo por escena (escenas + cierre)
    valores, titulares, cifras = valores_respaldo(st["hilo"])
    loc, avisos, n_pausas, numeros_gancho = [], [], 0, []
    secuencia_de = {n: k for k, grupo in enumerate(g.get("secuencias") or [] if isinstance(g.get("secuencias"), list) else [], 1)
                    for n in (grupo if isinstance(grupo, list) else [])}
    for i, e in enumerate(escenas + [{"tipo": "cierre", "tuit": None, "texto": ct}], 1):
        tipo = e.get("tipo") if e.get("tipo") in TIPOS else "cierre"
        texto = e.get("texto", "")
        # pausas del guion (cuentan para el límite); la adivina lleva además la suya antes de la respuesta (no cuenta)
        for motivo in pausas_mal_puestas(texto):
            fallas.append("V9 escena %d: %s" % (i, motivo))
        n_pausas += len(RE_PAUSA.findall(texto))
        if tipo == "adivina":
            texto = con_pausa_de_revelado(texto)
        NE.AVISOS.clear()
        try:
            segs = NE.segmentos(texto)
        except ValueError as ex:
            fallas.append("V3 escena %d: %s" % (i, ex))
            continue
        # pausas: en el prompt como <break>; fuera de la locución que se alinea (V6), se subtitula y se mide (V4)
        mayuscula_inicial(segs)   # «7 de cada 10…» → «Siete de cada diez…»; también tras «?» o «.»
        prompt = con_breaks("".join(s["v"] for s in segs))
        for s in segs:
            s["p"], s["v"] = sin_pausas(s["p"]), sin_pausas(s["v"])
        segs[0]["p"], segs[0]["v"] = segs[0]["p"].lstrip(), segs[0]["v"].lstrip()
        pantalla = "".join(s["p"] for s in segs)
        voz = "".join(s["v"] for s in segs)
        extra, valor_calculo = [], None
        if e.get("calculo"):
            valor_calculo, motivo = resolver_calculo(e["calculo"], cifras, valores)
            if motivo:
                fallas.append("V9 escena %d: calculo «%s» %s" % (i, e["calculo"], motivo))
            elif not escribe_numero(valor_calculo, [e.get("pantalla"), e.get("linea"), e.get("golpe"), pantalla]):
                fallas.append("V9 escena %d: calculo %s da %.4g y la escena no escribe ese número (pantalla/linea/golpe/texto)"
                              % (i, e["calculo"], valor_calculo))
            else:
                extra = [valor_calculo]
        # el visual del gancho: sus números (con id o calculo) respaldan lo que dice la voz y R4 exige que se digan
        vis_out = None
        if tipo == "gancho":
            vis_out, vis_f = visual_del_gancho(e, cifras, valores)
            fallas.extend("V9 gancho: " + x for x in vis_f)
            extra += [x for x in vis_out["numeros"] if x is not None]
        # adivina: la opción correcta necesita respaldo; las otras dos son señuelos de un juego (exentas de V2)
        senuelos = []
        if tipo == "adivina":
            ops, k = [o.strip() for o in e.get("opciones") or []], e.get("correcta")
            if len(ops) == 3 and k in (0, 1, 2):
                if sin_respaldo(ops[k], valores, extra):
                    fallas.append("V9 escena %d (adivina): la opción correcta «%s» no tiene respaldo en datos.json ni «calculo»" % (i, ops[k]))
                senuelos = [valor_de(o) for j, o in enumerate(ops) if j != k and valor_de(o) is not None]
        vals_v2 = valores + [(round(float(x), 6), 1.0) for x in extra + senuelos]
        sin = VM.sueltos(exentar_de_cada(pantalla, vals_v2), vals_v2, titulares)
        if sin:
            fallas.append("V2 escena %d: números sin respaldo en datos.json: %s" % (i, ", ".join(map(str, sin))))
        if tipo == "definicion":
            faltan = [w for w in _plano(e.get("termino") or "").split() if w not in _plano(pantalla).split()]
            if faltan:
                fallas.append("V9 escena %d (definicion): la voz no dice el término «%s» (falta «%s»)" % (i, e.get("termino"), "», «".join(faltan)))
            else:
                ws, t0 = _plano(pantalla).split(), (_plano(e.get("termino") or "").split() or [""])[0]
                antes = " ".join(ws[:ws.index(t0)] if t0 in ws else ws)
                if not re.search(r"\b(%s)\b" % "|".join(ANUNCIOS_DEFINICION), antes):
                    fallas.append("V9 escena %d (definicion): la voz debe anunciar el concepto antes de decir «%s» («Para entenderlo "
                                  "mejor: …», «¿Qué es …?», «Antes de seguir, un concepto: …»)" % (i, e.get("termino")))
        if tipo == "adivina":
            dichas = set(_plano(pantalla).split()) | set(_plano(voz).split())
            faltan = [w for w in _plano(e.get("pregunta") or "").split() if w not in dichas]
            if faltan:
                fallas.append("V9 escena %d (adivina): la pregunta en pantalla dice «%s» y la voz no: se escribe al ritmo de la voz, "
                              "así que las dos hacen la misma pregunta" % (i, "», «".join(faltan)))
        if tipo == "explica":
            for x in [e.get("titulo") or ""] + [p for p in e.get("pasos") or [] if isinstance(p, str)]:
                sin = sin_respaldo(x, valores, extra)
                if sin:
                    fallas.append("V2 escena %d (explica): «%s» tiene un número sin respaldo en datos.json ni «calculo»: %s"
                                  % (i, x, ", ".join(map(str, sin))))
        for campo in ("golpe", "pantalla", "linea"):
            if e.get(campo):
                sin = sin_respaldo(e[campo], valores, extra)
                if sin:
                    fallas.append("V9 escena %d: %s «%s» tiene un número sin respaldo en datos.json ni «calculo»: %s"
                                  % (i, campo, e[campo], ", ".join(map(str, sin))))
        if tipo == "gancho":   # los números del gancho (F6: el remate no los repite)
            numeros_gancho = numeros_sin_anios(" ".join((pantalla, e.get("pantalla") or "", e.get("linea") or ""))) + \
                [x for x in (vis_out or {}).get("numeros") or [] if x is not None]
        if tipo == "gancho":   # R2–R10 (referencias/ganchos.md) y que sea el gancho que eligió el crítico
            r_f, r_av = reglas_gancho(e, pantalla, {"cifras": cifras, "valores": valores, "anio": ANIO,
                                                     "recientes": st.get("ganchos_recientes"), "visual": vis_out,
                                                     "e2": escenas[1].get("texto", "") if len(escenas) > 1 else ""})
            fallas.extend("V9 gancho: " + x for x in r_f)
            avisos.extend("gancho: " + x for x in r_av)
            elegido = gancho_elegido(trabajo)
            if elegido and not mismo_gancho(e, elegido, (g.get("promesa") or {})):
                fallas.append("V9 gancho: la escena 1 no es el gancho elegido «%s» de ganchos.json (familia, visual, pantalla, "
                              "línea y voz van tal cual; corre `video.py ganchos TRABAJO --usar`)" % elegido.get("id"))
        # la pantalla y la voz cuentan lo mismo: en el gancho es falla (es el gancho), en un golpe es aviso
        if tipo in ("gancho", "golpe"):
            faltan = palabras_no_dichas(" ".join(filter(None, (e.get("pantalla"), e.get("linea")))), voz)
            if faltan and tipo == "gancho":
                fallas.append("V9 escena %d: la voz no dice «%s», que está en pantalla: la pantalla y la voz del gancho cuentan lo mismo"
                              % (i, "», «".join(faltan)))
            elif faltan:
                avisos.append("escena %d: la pantalla dice «%s» y la voz no (vale si es un sinónimo)" % (i, "», «".join(faltan)))
            motivo = falta_verbo(e)
            if motivo:
                fallas.append("V9 escena %d (%s): %s" % (i, tipo, motivo))
        # una escena no abre con las palabras que cerraron la anterior (regla del usuario: se oye repetitivo)
        if loc and tipo != "cierre":
            eco = eco_entre_escenas(loc[-1]["voz"], voz)
            if eco:
                fallas.append("V9 escena %d: empieza con «%s», que cierra la escena anterior; no repitas el cierre de una escena al "
                              "abrir la siguiente" % (i, "», «".join(eco)))
        for av in NE.AVISOS:
            fallas.append("V3 escena %d: %s" % (i, av))
        if re.search(r"\d", voz):
            fallas.append("V3 escena %d: la voz conserva dígitos: «%s»" % (i, voz))
        largo = len(voz)
        if not CARACTERES[tipo][0] <= largo <= CARACTERES[tipo][1]:
            fallas.append("V4 escena %d (%s): %d caracteres de voz (rango %d–%d)" % (i, tipo, largo, *CARACTERES[tipo]))
        if tipo == "gancho":   # el gancho en 3 segundos: una oración corta, la promesa corta o en T1
            oraciones = [o for o in re.split(r"(?<=[.?!…])\s+", voz.strip()) if o]
            o1 = oraciones[0] if oraciones else voz
            if len(o1) / CPS > GANCHO_ORACION_S:
                fallas.append("V9 gancho: la primera oración dura %.1f s estimados (máximo %.0f s ≈ %d caracteres en palabras): «%s»"
                              % (len(o1) / CPS, GANCHO_ORACION_S, int(GANCHO_ORACION_S * CPS), o1))
            if largo / CPS > GANCHO_VOZ_S:
                fallas.append("V9 gancho: la voz dura %.1f s estimados (máximo %.0f s): acorta o di la promesa en T1 (en: 2)" % (largo / CPS, GANCHO_VOZ_S))
            pr = g.get("promesa") or {}
            if pr.get("en") == 1 and pr.get("texto"):
                NE.AVISOS.clear()
                sp = len(NE.convertir(sin_pausas(pr["texto"]))[1]) / CPS
                NE.AVISOS.clear()
                if sp > PROMESA_S:
                    fallas.append("V9 gancho: la promesa dura %.1f s estimados (máximo %.0f s): acórtala o dila en T1 (en: 2)" % (sp, PROMESA_S))
        hueco, antes, despues = hueco_maximo(segs, voz) if tipo not in SIN_HUECO else (0.0, "", "")
        if hueco > RITMO_MAX_S:
            fallas.append("V9 escena %d: %.1f s sin evento entre «…%s» y «%s…» (máximo %.0f s): acorta o mueve la cifra"
                          % (i, hueco, antes, despues, RITMO_MAX_S))
        plantilla = tarjetas[e["tuit"]]["plantilla"] if tipo in CON_TUIT and e.get("tuit") in tarjetas else tipo
        cola = cola_de(tipo, secuencia_de.get(i), secuencia_de.get(i + 1))
        loc.append({"n": i, "tipo": tipo, "tuit": e.get("tuit") if tipo in CON_TUIT else None, "plantilla": plantilla,
                    "acto": e.get("acto") if tipo != "cierre" else None, "secuencia": secuencia_de.get(i), "cola": cola,
                    "foco": e.get("foco") if tipo in CON_TUIT else None,
                    "enlace": e.get("enlace") if i >= 2 else None, "golpe": e.get("golpe") if tipo in CON_TUIT or tipo == "escala" else None,
                    "top": e.get("top", RANKING_TOP_DEFECTO) if tipo == "ranking" else None, "orden": e.get("orden") if tipo == "ranking" else None,
                    "escala": {"de_cada": e.get("de_cada"), "etiqueta": (e.get("etiqueta") or "").strip()} if tipo == "escala" else None,
                    "cinetico": cinetico_de(tipo, e),
                    "adivina": {"pregunta": (e.get("pregunta") or "").strip(), "opciones": [o.strip() for o in e.get("opciones") or []],
                                "correcta": e.get("correcta")} if tipo == "adivina" else None,
                    "explica": {"animacion": e.get("animacion"), "mecanismo": e.get("mecanismo"), "brief": (e.get("brief") or "").strip(),
                                "titulo": (e.get("titulo") or "").strip(),
                                "pasos": [str(x).strip() for x in e.get("pasos") or []]} if tipo == "explica" else None,
                    "familia": e.get("familia") if tipo == "gancho" else None,
                    "visual": {k: v for k, v in vis_out.items() if k != "numeros"} if vis_out else None,
                    "icono": e.get("icono") if tipo in ICONO_TIPOS else None,
                    "calculo": e.get("calculo"), "valor_calculo": valor_calculo,
                    "pantalla": pantalla, "voz": voz, "prompt": prompt, "segmentos": segs,
                    "estimado_s": round(len(voz) / CPS + cola, 2),
                    "hueco_max_s": round(hueco, 2)})
    for etiqueta, txt in (("resumen", " ".join(cierre.get("resumen") or [])),
                          ("caption", json.dumps(g.get("caption") or {}, ensure_ascii=False))):
        sin = VM.sueltos(txt, valores, titulares)
        if sin:
            fallas.append("V2 %s: números sin respaldo: %s" % (etiqueta, ", ".join(map(str, sin))))

    # F1–F8: la frase final del cierre (remate de consecuencia o, a veces, pregunta; referencias/cierres.md)
    hilo = leer(os.path.join(RAIZ, st["hilo"], "hilo.json"))
    fallas.extend(reglas_cierre(cierre, st, hilo, st["tarjetas"], numeros_gancho, cifras))
    if n_pausas > PAUSAS_MAX_VIDEO:
        fallas.append("V9 %d pausas en el video (máximo %d: el exceso de <break> ensucia la voz)" % (n_pausas, PAUSAS_MAX_VIDEO))
    # las secuencias de voz: un prompt por grupo (las voces seguidas, cada una con su puntuación final)
    secuencias, por_sec = [], {}
    for x in loc:
        if x.get("secuencia"):
            por_sec.setdefault(x["secuencia"], []).append(x)
    for k in sorted(por_sec):
        xs = por_sec[k]
        prompt_sec = " ".join(p if p.rstrip().endswith((".", "?", "!", "…", ">")) else p.rstrip() + "." for p in (x.get("prompt") or x["voz"] for x in xs))
        car = sum(len(x["voz"]) for x in xs)
        if car > SECUENCIA_CARACTERES:
            fallas.append("V9 secuencia %d (escenas %s): %d caracteres de voz; van ≤ %d por nodo (parte la secuencia)"
                          % (k, ", ".join(str(x["n"]) for x in xs), car, SECUENCIA_CARACTERES))
        secuencias.append({"k": k, "escenas": [x["n"] for x in xs], "prompt": prompt_sec, "caracteres": car})
    # V4 presupuesto
    chars = sum(len(x["voz"]) for x in loc)
    estimado = chars / CPS + sum(x["cola"] for x in loc)
    tol = dur.get("tol", TOLERANCIA)
    lo, hi = dur["s"] * (1 - tol), dur["s"] * (1 + tol)
    if not lo <= estimado <= hi:
        fallas.append("V4 duración estimada %.0f s (%d caracteres de voz); «%s» pide %.0f–%.0f s"
                      % (estimado, chars, st["duracion"], lo, hi))
    print("escenas %d + cierre · voz %d caracteres · estimado %.0f s (objetivo %d s)"
          % (len(escenas), chars, estimado, dur["s"]))
    for x in loc:
        print("E%-2d %-7s T%-3s %-14s %5.1fs hueco %.1fs  %s" % (x["n"], x["tipo"], x["tuit"] or "-", x["plantilla"],
                                                             x["estimado_s"], x["hueco_max_s"], x["voz"]))
    for x in avisos:
        print("AVISO", x)
    if fallas:
        for f in fallas:
            print("FALLA", f)
        return 1
    escribir(os.path.join(trabajo, "locucion.json"),
             {"voz": VOZ, "caracteres": chars, "estimado_s": round(estimado, 1), "duracion": st["duracion"],
              "objetivo_s": dur["s"], "n_escenas": len(escenas), "promesa": g.get("promesa"),
              "voz_continua": bool(g.get("voz_continua")) and bool(secuencias), "secuencias": secuencias, "escenas": loc})
    print("→ %s · V1–V5, V9%s ok%s" % (rel(os.path.join(trabajo, "locucion.json")), ", V17–V18" if NARRACION_VIDEO else "",
                                     " · voz de corrido en %d secuencia(s)" % len(secuencias) if g.get("voz_continua") and secuencias else ""))
    return 0


# ---------- narración de corrido (compartida con /historia) ----------
RE_SEGUN = re.compile(r"\b(?:seg[uú]n|de acuerdo con)\b", re.I)
RE_SEGUN_FUENTE = re.compile(r"\b(?:[Ss]eg[uú]n|[Dd]e acuerdo con)\s+(?:la |el |los |las |un |una )?((?:[A-ZÁÉÍÓÚÑ][\w.&-]*)(?:\s+(?:de |del |la |y )?[A-ZÁÉÍÓÚÑ][\w.&-]*)*)")
APERTURA_ATRIBUIDA = re.compile(r"^[¿¡«\s]*(?:(?:pero|y|por eso|así que|asi que|entonces)[,\s]+)?(?:seg[uú]n|de acuerdo con)\b", re.I)
# conectores causales y temporales que hacen que la narración siga de corrido
CONECTORES_NARRACION = re.compile(
    r"\b(?:pero|sin embargo|aun así|en cambio|por eso|así que|asi que|entonces|hasta que|mientras tanto|porque|"
    r"(?:\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|doce|quince|veinte) (?:años?|meses|semanas|d[ií]as) (?:después|antes|más tarde|mas tarde)|"
    r"(?:ese|esa) (?:mismo |misma )?(?:d[ií]a|mes|año|semana|noche|tarde|mañana)|al d[ií]a siguiente|al año siguiente|"
    r"(?:poco|meses|años|semanas|décadas|decadas) después)\b", re.I)
# un demostrativo («esos 40 niños», «ese alimento») apunta a algo que ya se dijo o se leyó antes; los de tiempo no cuentan
RE_DEMOSTRATIVO = re.compile(r"\b(es[oa]s|ese|esa|aquel(?:l[oa]s?)?|dich[oa]s?)\s+(?:(\d[\d.,]*)\s+)?([a-záéíóúñü]{3,})", re.I)
HILO_LIBRES = {"año", "años", "epoca", "época", "épocas", "momento", "momentos", "vez", "veces", "fecha", "fechas", "dia",
               "día", "días", "tiempo", "tiempos", "decada", "década", "décadas", "mes", "meses", "siglo", "entonces",
               "fue", "era", "eran", "son", "sería", "que", "mismo", "misma", "mismos", "mismas", "otra", "otro", "otras",
               "otros", "sola", "solo", "parte", "forma", "manera", "idea"}


def acto_de(e, i):
    """El acto de la escena i: el gancho (escena 1) es el acto 1 (ganchos --usar lo reescribe sin el campo)."""
    return 1 if i == 1 else e.get("acto")


def narracion_de(g):
    """[(acto, texto)] de guion.narracion (3 entradas {acto, texto}); [] si no viene."""
    return [(x.get("acto"), (x.get("texto") or "").strip()) for x in g.get("narracion") or [] if isinstance(x, dict)]


def plano_voz(t):
    return _plano(sin_pausas(t or ""))


def estimado_guion_s(g):
    """Segundos estimados del guion sin locución (dígitos sin convertir): lo bastante para contar cortes por minuto."""
    es = g.get("escenas") or []
    return sum(len(sin_pausas(e.get("texto") or "")) for e in es + [g.get("cierre") or {}]) / CPS + COLA * len(es) + COLA_CIERRE


def revisar_reparto(g, cod="V17"):
    """La narración de corrido: 3 entradas {acto 1|2|3, texto} y, con escenas, cada acto es la suma EXACTA de las voces
    de sus escenas (el cierre, en el acto 3): el texto se escribe primero y se reparte sin cambiar una palabra."""
    f = []
    escenas, cierre = g.get("escenas") or [], g.get("cierre") or {}
    narr = narracion_de(g)
    if not narr or [a for a, _ in narr] != [1, 2, 3] or not all(t for _, t in narr):
        return ["%s «narracion»: 3 entradas {acto: 1|2|3, texto} con el texto corrido de cada acto (se escribe ANTES de "
                "repartirlo en escenas; cada escena toma un tramo sin cambiar una palabra)" % cod]
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    for ac, texto in (narr if escenas else []):
        voces = [e.get("texto") or "" for e, a in zip(escenas, actos) if a == ac]
        if ac == 3:
            voces.append(cierre.get("texto") or "")
        esperado, dado = plano_voz(" ".join(voces)), plano_voz(texto)
        if esperado != dado:
            k = next((j for j, (x, y) in enumerate(zip(esperado, dado)) if x != y), min(len(esperado), len(dado)))
            f.append("%s acto %d: la narración no es la suma de las voces de sus escenas%s; difieren desde «…%s» (narración) frente a "
                     "«…%s» (voces): reparte el texto tal cual o corrige la narración" % (cod, ac, " y el cierre" if ac == 3 else "",
                                                                                        dado[max(0, k - 20):k + 25], esperado[max(0, k - 20):k + 25]))
    return f


def revisar_hilo_voz(g, cod="V18", conectores_min=CONECTORES_MIN_ACTO_DEF, cortes_falla=True):
    """Flujo de la voz: ≥ conectores_min conectores causales o temporales por acto, ≤ 1 escena que abre con una
    atribución, dos escenas seguidas que no abren igual y ≤ 6.5 cortes por minuto (falla en /historia; en /video, cuyo
    ritmo cambia de escena cada pocos segundos, aviso). Sin escenas, solo los conectores."""
    f = []
    escenas, cierre = g.get("escenas") or [], g.get("cierre") or {}
    narr = narracion_de(g)
    for ac, texto in narr:
        n_c = len(CONECTORES_NARRACION.findall(sin_pausas(texto)))
        if n_c < conectores_min:
            f.append("%s acto %d: %d conector(es) causal o temporal («pero», «por eso», «entonces», «dos años después», «mientras "
                     "tanto»…); van ≥ %d: cada oración sigue de la anterior, nunca «y luego»" % (cod, ac, n_c, conectores_min))
    if not escenas:
        return f
    unidades = [sin_pausas(e.get("texto") or "").strip() for e in escenas] + [sin_pausas(cierre.get("texto") or "").strip()]
    ap = [i for i, u in enumerate(unidades[:-1], 1) if i >= 2 and APERTURA_ATRIBUIDA.match(u)]
    if len(ap) > APERTURAS_ATRIBUIDAS_MAX:
        f.append("%s %d escenas abren con una atribución («Según…», «Pero, según…»: escenas %s); va ≤ %d: la fuente en pantalla "
                 "y la voz narra" % (cod, len(ap), ", ".join(map(str, ap)), APERTURAS_ATRIBUIDAS_MAX))
    dos = [" ".join(plano_voz(u).split()[:2]) for u in unidades[:-1]]
    for i in range(1, len(dos)):
        if dos[i] and dos[i] == dos[i - 1]:
            f.append("%s escenas %d y %d abren con las mismas palabras («%s»): varía la apertura" % (cod, i, i + 1, dos[i]))
    primeras = {}
    for u in unidades[1:-1]:
        w = (plano_voz(u).split() or [""])[0]
        primeras[w] = primeras.get(w, 0) + 1
    for w, n in primeras.items():
        if n > 3 and w:
            print("AVISO %s %d escenas abren con «%s»: varía la apertura" % (cod, n, w))
    est = estimado_guion_s(g)
    cpm = (len(escenas) + 1) / max(1.0, est / 60)
    if cpm > CORTES_MAX_POR_MIN:
        msg = ("%s %.1f cortes por minuto (%d escenas más el cierre en %.0f s); van ≤ %.1f: una escena puede sostener un tramo "
               "más largo de narración" % (cod, cpm, len(escenas), est, CORTES_MAX_POR_MIN))
        if cortes_falla:
            f.append(msg)
        else:
            print("AVISO", msg)
    return f


def revisar_segun(g, cod="V18", maximo=SEGUN_MAX_DATO, por_acto_max=SEGUN_MAX_ACTO_DATO):
    """«Según» con medida: ≤ maximo en la voz, ≤ por_acto_max por acto, nunca en dos escenas seguidas, nunca la misma
    fuente dos veces en voz. Sin escenas, las unidades son los actos de la narración."""
    f = []
    escenas, cierre = g.get("escenas") or [], g.get("cierre") or {}
    narr = narracion_de(g)
    solo_narr = not escenas
    unidades = [t for _, t in narr] if solo_narr else \
        [sin_pausas(e.get("texto") or "").strip() for e in escenas] + [sin_pausas(cierre.get("texto") or "").strip()]
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    etiqueta = (lambda k: "acto %d" % (k + 1)) if solo_narr else (lambda k: "escena %d" % (k + 1))  # noqa: E731
    segs = [len(RE_SEGUN.findall(u)) for u in unidades]
    if sum(segs) > maximo:
        f.append("%s %d «según» en la voz; van ≤ %d: lo corroborado se narra llano con la fuente en pantalla; varía con una "
                 "aposición («AMSA, la autoridad del lago, …») o el verbo de la fuente («el tribunal calificó…»)" % (cod, sum(segs), maximo))
    por_acto = {}
    for k, n in enumerate(segs):
        ac = (k + 1) if solo_narr else (actos[k] if k < len(actos) else 3)
        por_acto[ac] = por_acto.get(ac, 0) + n
    for ac, n in sorted(por_acto.items(), key=lambda kv: str(kv[0])):
        if n > por_acto_max:
            f.append("%s acto %s: %d «según»; van ≤ %d por acto" % (cod, ac, n, por_acto_max))
    if not solo_narr:
        for i in range(1, len(segs)):
            if segs[i - 1] and segs[i]:
                f.append("%s escenas %d y %d: «según» en dos escenas seguidas; la segunda fuente va solo en pantalla" % (cod, i, i + 1))
    fuentes_voz = {}
    for k, u in enumerate(unidades):
        for m in RE_SEGUN_FUENTE.finditer(u):
            fuentes_voz.setdefault(_plano(m.group(1)), []).append(etiqueta(k))
    for fu, ns in fuentes_voz.items():
        if len(ns) > 1:
            f.append("%s «según %s» %d veces en voz (%s): la segunda vez va solo en pantalla" % (cod, fu, len(ns), ", ".join(ns)))
    return f


def hilo_referencias(escenas, cod="V18"):
    """Cada «esos 40 niños», «ese alimento», «esa línea» tiene su antecedente en lo que ya se oyó o se leyó antes: la cifra
    y la palabra salen en una escena anterior (voz, pantalla, línea, titular, golpe) o antes en la misma voz."""
    f, dicho = [], ""
    llano = lambda t: _plano(re.sub(r"\{([\d.,]+):\w+\}", r"\1", t or ""))  # noqa: E731
    for i, e in enumerate(escenas, 1):
        voz = e.get("texto") or ""
        for m in RE_DEMOSTRATIVO.finditer(voz):
            num, pal = m.group(2), m.group(3).lower()
            if pal in HILO_LIBRES or _plano(pal) in HILO_LIBRES:
                continue
            antes = dicho + " " + llano(voz[:m.start()])
            raiz = _plano(pal[:-1] if pal.endswith("s") and len(pal) > 4 else pal)
            falta = [x for x, ok in ((num, not num or re.search(r"\b%s\b" % re.escape(llano(num)), antes)),
                                     (pal, re.search(r"\b%s" % re.escape(raiz), antes))) if x and not ok]
            if falta:
                f.append("%s escena %d: «%s» apunta a algo que no se dijo antes (%s no sale en ninguna escena "
                         "anterior): di qué es aquí o cámbialo; si cambiaste el gancho u otra escena, relee el hilo "
                         "entero" % (cod, i, m.group(0), " ni ".join("«%s»" % x for x in falta)))
        dicho += " " + llano(" ".join(str(e.get(k) or "") for k in ("pantalla", "linea", "titular", "golpe", "titulo", "texto")))
    return f


def revisar_actos(g):
    """V17 /video: cada escena lleva su `acto` (1–3) y no baja; el gancho es del 1, y los actos 1, 2 y 3 tienen escenas
    propias (el cierre cierra el 3)."""
    f, escenas = [], g.get("escenas") or []
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    malos = [i for i, a in enumerate(actos, 1) if a not in (1, 2, 3)]
    if malos:
        return ["V17 escenas %s sin «acto» (1, 2 o 3: planteamiento, nudo, desenlace)" % ", ".join(map(str, malos))]
    if any(b < a for a, b in zip(actos, actos[1:])):
        f.append("V17 los actos no bajan: %s" % actos)
    if not {2, 3} <= set(actos[1:]):
        f.append("V17 los actos 2 y 3 llevan al menos una escena cada uno (el cierre no basta para el 3)")
    return f


def secuencias_por_defecto(g, rompe=None, sueltas=()):
    """Las secuencias de voz cuando el guion no las trae: tramos de escenas consecutivas del mismo acto, de 2 a
    SECUENCIA_MAX, que se cortan donde `rompe(e)` (un giro o un rótulo en /historia); el gancho, el cierre y los tipos
    de `sueltas` (la adivina, con su pausa) van solos."""
    es = g.get("escenas") or []
    tramos, actual = [], []
    for i, e in enumerate(es, 1):
        if i == 1:
            continue
        if e.get("tipo") in sueltas:
            if actual:
                tramos.append(actual)
            actual = []
            continue
        corta = not actual or acto_de(e, i) != acto_de(es[actual[-1] - 1], actual[-1]) or (rompe and rompe(e))
        if corta and actual:
            tramos.append(actual)
            actual = []
        actual.append(i)
    if actual:
        tramos.append(actual)
    out = []
    for t in tramos:
        while len(t) > SECUENCIA_MAX:
            corte = SECUENCIA_MAX if len(t) - SECUENCIA_MAX != 1 else SECUENCIA_MAX - 1
            out.append(t[:corte])
            t = t[corte:]
        if len(t) >= 2:
            out.append(t)
    return out


def narracion_corrida(g, loc=None):
    """[(acto, texto)]: la voz de corrido por acto, en palabras (locucion.json) si ya pasó el gate; si no, guion.narracion.
    Ordena por acto (el gancho es del 1, el cierre del 3) y, dentro, por escena."""
    es = g.get("escenas") or []
    if loc and es:
        por_acto = {}
        for L in sorted(loc["escenas"], key=lambda x: x["n"]):
            ac = acto_de(es[L["n"] - 1], L["n"]) if L["n"] - 1 < len(es) else 3
            por_acto.setdefault(ac if ac in (1, 2, 3) else 2, []).append(L["voz"])
        return [(ac, " ".join(por_acto[ac])) for ac in sorted(por_acto)]
    return narracion_de(g)


def lineas_oyente(g, loc, pantalla_de):
    """El digesto del oyente ingenuo: primero la narración de corrido (para oírla como un documental, sin pantalla) y
    luego, por escena, lo que se lee (pantalla_de(e)) y lo que dice la voz. Sin fuentes, sin ids, sin datos de más."""
    es = g.get("escenas") or []
    out = ["# Lo que se oye y se lee, en orden (%d escenas + cierre, ≈ %.0f s)" % (len(es), loc["estimado_s"]), "",
           "## La narración de corrido (óyela primero, de principio a fin, sin pantalla)", ""]
    out += ["%s" % t for _, t in narracion_corrida(g, loc)]
    out += ["", "## Escena por escena (lo que se lee en pantalla y lo que dice la voz)", ""]
    for L in loc["escenas"]:
        e = es[L["n"] - 1] if L["n"] - 1 < len(es) else dict(g.get("cierre") or {}, tipo="cierre")
        pant = pantalla_de(e)
        out += ["E%d · %s%s" % (L["n"], L["tipo"], " · PANTALLA: %s" % pant if pant else ""), "   VOZ: %s" % L["voz"]]
    return out


def pantalla_video(e, tarjetas):
    """Lo que se LEE en una escena de /video (sin ids ni fuentes): el golpe y el titular de su tarjeta."""
    t = e.get("tipo")
    if t == "gancho":
        partes = [e.get("pantalla"), e.get("linea"), (e.get("visual_datos") or {}).get("etiqueta")]
    elif t in CON_TUIT or t == "escala":
        tj = tarjetas.get(e.get("tuit")) or {}
        tit = (tj.get("datos") or {}).get("titular") or tj.get("titular")
        partes = [e.get("golpe"), (tj.get("datos") or {}).get("kicker"), " ".join(tit) if isinstance(tit, list) else tit, e.get("etiqueta")]
    elif t == "explica":
        partes = [e.get("titulo")] + [str(p) for p in e.get("pasos") or []]
    elif t == "cierre":
        partes = list(e.get("resumen") or []) + [e.get("final")]
    else:   # golpe, definicion, adivina
        partes = [e.get("pantalla"), e.get("linea"), e.get("termino"), e.get("definicion"), e.get("pregunta")] + list(e.get("opciones") or [])
    return " · ".join(str(x).strip() for x in partes if x and str(x).strip())


def revisar_narracion_video(g, st):
    """V17 (actos y reparto literal) + V18 (conectores por acto, aperturas, cortes, referencias y «según») de /video."""
    conectores = CONECTORES_MIN_ACTO.get(st.get("duracion"), CONECTORES_MIN_ACTO_DEF)
    f = revisar_reparto(g) + revisar_hilo_voz(g, conectores_min=conectores, cortes_falla=False) + revisar_segun(g)
    if g.get("escenas"):
        f = revisar_actos(g) + f + hilo_referencias(g["escenas"])
    return f


def cmd_narracion(a):
    """Mide la narración de corrido (guion.narracion) ANTES de repartirla: palabras, segundos, conectores y «según» por
    acto; --check falla con V17–V18 sobre la narración sola (sin escenas)."""
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    g = leer(os.path.join(trabajo, "guion.json"))
    narr = narracion_de(g)
    if not narr:
        return falla("guion.json sin «narracion»: escribe primero [{acto: 1, texto}, {acto: 2, texto}, {acto: 3, texto}]")
    total_p, total_s = 0, 0.0
    for ac, t in narr:
        pal, seg = palabras(t), len(sin_pausas(NE.convertir(t)[1])) / CPS
        con = CONECTORES_NARRACION.findall(sin_pausas(t))
        total_p, total_s = total_p + pal, total_s + seg
        print("acto %s · %d palabras · %.0f s · %d conector(es)%s · %d «según»"
              % (ac, pal, seg, len(con), (" (%s)" % ", ".join(c.lower() for c in con[:6])) if con else "", len(RE_SEGUN.findall(t))))
    dur = DURACIONES[st["duracion"]]
    print("total %d palabras · %.0f s de voz · «%s» pide ≈ %d s con las colas" % (total_p, total_s, st["duracion"], dur["s"]))
    if not getattr(a, "check", False):
        return 0
    f = revisar_reparto(dict(g, escenas=[])) + revisar_hilo_voz(dict(g, escenas=[]), conectores_min=CONECTORES_MIN_ACTO.get(
        st["duracion"], CONECTORES_MIN_ACTO_DEF)) + revisar_segun(dict(g, escenas=[]))
    for x in f:
        print("FALLA", x)
    print("narracion %s" % ("ok" if not f else "con %d falla(s)" % len(f)))
    return 1 if f else 0


def cmd_oyente(a):
    """El digesto del oyente ingenuo de /video (lo que se oye y se lee, en orden): necesita locucion.json."""
    trabajo = os.path.abspath(a.trabajo)
    ruta = os.path.join(trabajo, "locucion.json")
    if not os.path.exists(ruta):
        return falla("falta locucion.json: corre python3 scripts/video.py guion %s --check" % rel(trabajo))
    st = estado(trabajo)
    tarjetas = {t["n"]: t for t in st["tarjetas"]}
    print("\n".join(lineas_oyente(leer(os.path.join(trabajo, "guion.json")), leer(ruta), lambda e: pantalla_video(e, tarjetas))))
    return 0


def cola_de(tipo, secuencia, secuencia_siguiente):
    """El aire tras la voz de una escena: el del cierre; dentro de una secuencia de voz (la siguiente es de la misma),
    solo la transición; si no, COLA."""
    if tipo == "cierre":
        return COLA_CIERRE
    if secuencia and secuencia == secuencia_siguiente:
        return COLA_SEGUIDA
    return COLA


# ---------- ganchos (candidatos del agente video-gancho → elección del crítico → escena 1) ----------
def revisar_gancho(e, st, valores, cifras, titulares, e2=None):
    """Todas las reglas de una escena gancho suelta (candidato): R1 en silencio, voz en palabras (V3), presupuesto (V4),
    respaldo (V2), verbo, pantalla dicha, gancho en 3 s y R2–R10 → (fallas, avisos, voz en palabras)."""
    f = []
    for campo, maxp, maxc in (("pantalla", PANTALLA_PALABRAS, PANTALLA_CARACTERES), ("linea", LINEA_PALABRAS, LINEA_CARACTERES)):
        v = (e.get(campo) or "").strip()
        if not v or palabras(v) > maxp or len(v) > maxc:
            f.append("R1 «%s» de 1–%d palabras y ≤ %d caracteres (se lee en silencio)" % (campo, maxp, maxc))
    texto = e.get("texto") or ""
    f += ["V9 " + x for x in pausas_mal_puestas(texto)]
    NE.AVISOS.clear()
    try:
        segs = NE.segmentos(texto)
    except ValueError as ex:
        return f + ["V3 %s" % ex], [], ""
    f += ["V3 %s" % x for x in NE.AVISOS]
    NE.AVISOS.clear()
    for s_ in segs:
        s_["p"], s_["v"] = sin_pausas(s_["p"]), sin_pausas(s_["v"])
    segs[0]["v"] = segs[0]["v"].lstrip()
    mayuscula_inicial(segs)
    voz_p, voz = "".join(s_["p"] for s_ in segs).strip(), "".join(s_["v"] for s_ in segs).strip()
    if not CARACTERES["gancho"][0] <= len(voz) <= CARACTERES["gancho"][1]:
        f.append("V4 %d caracteres de voz (rango %d–%d)" % (len(voz), *CARACTERES["gancho"]))
    oraciones = [o for o in re.split(r"(?<=[.?!…])\s+", voz) if o]
    if oraciones and len(oraciones[0]) / CPS > GANCHO_ORACION_S:
        f.append("V9 la primera oración dura %.1f s estimados (máximo %.0f s): «%s»" % (len(oraciones[0]) / CPS, GANCHO_ORACION_S, oraciones[0]))
    if len(voz) / CPS > GANCHO_VOZ_S:
        f.append("V9 la voz dura %.1f s estimados (máximo %.1f s)" % (len(voz) / CPS, GANCHO_VOZ_S))
    extra = []
    if e.get("calculo"):
        r, motivo = resolver_calculo(e["calculo"], cifras, valores)
        if motivo:
            f.append("V9 calculo «%s» %s" % (e["calculo"], motivo))
        elif not escribe_numero(r, [e.get("pantalla"), e.get("linea"), voz_p]):
            f.append("V9 calculo %s da %.4g y el gancho no escribe ese número" % (e["calculo"], r))
        else:
            extra.append(r)
    vis, vf = visual_del_gancho(e, cifras, valores)
    f += vf
    extra += [x for x in vis["numeros"] if x is not None]
    vals = valores + [(round(float(x), 6), 1.0) for x in extra]
    sin = VM.sueltos(exentar_de_cada(voz_p, vals), vals, titulares)
    if sin:
        f.append("V2 números de la voz sin respaldo en datos.json: %s" % ", ".join(map(str, sin)))
    for campo in ("pantalla", "linea"):
        sin = sin_respaldo(e.get(campo) or "", valores, extra)
        if sin:
            f.append("V2 %s «%s» con un número sin respaldo: %s" % (campo, e.get(campo), ", ".join(map(str, sin))))
    faltan = palabras_no_dichas(" ".join(filter(None, (e.get("pantalla"), e.get("linea")))), voz)
    if faltan:
        f.append("V9 la voz no dice «%s», que está en pantalla" % "», «".join(faltan))
    motivo = falta_verbo(e)
    if motivo:
        f.append("V9 " + motivo)
    if e.get("icono") and e["icono"] not in (iconos_catalogo() or {}):
        f.append("V1 icono «%s» no está en design/iconos/catalogo.json" % e["icono"])
    rf, ra = reglas_gancho(e, voz_p, {"cifras": cifras, "valores": valores, "anio": ANIO, "visual": vis,
                                      "recientes": st.get("ganchos_recientes"), "e2": e2})
    return f + rf, ra, voz


def cmd_ganchos(a):
    """ganchos.json: --check (4–5 candidatos de familias distintas, cada uno con R1–R10) · --usar [ID] (el elegido del
    crítico, de seleccion.json si no se da ID, pasa a la escena 1 de guion.json; el segundo queda para la versión B)."""
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    ruta = os.path.join(trabajo, "ganchos.json")
    try:
        G = leer(ruta)
    except (OSError, ValueError) as e:
        return falla("ganchos.json ilegible: %s" % e)
    cands = G.get("candidatos") or []
    valores, titulares, cifras = valores_respaldo(st["hilo"])
    fallas, por_id = [], {}
    if not CANDIDATOS[0] <= len(cands) <= CANDIDATOS[1]:
        fallas.append("G %d candidatos; van %d–%d de familias distintas" % (len(cands), *CANDIDATOS))
    fams = [c.get("familia") for c in cands]
    if len(set(fams)) < len(fams):
        fallas.append("G familias repetidas (%s): cada candidato prueba un mecanismo distinto" % ", ".join(map(str, fams)))
    if sum(1 for c in cands if (c.get("visual") or "cifra") != "cifra") < CANDIDATOS_CON_VISUAL:
        fallas.append("G al menos %d candidatos con un visual que no sea la cifra sola (llenado, pareja, figuras o lugar)" % CANDIDATOS_CON_VISUAL)
    for k, c in enumerate(cands, 1):
        cid = c.get("id") or "g%d" % k
        if cid in por_id:
            fallas.append("G id «%s» repetido" % cid)
        por_id[cid] = c
        f, av, voz = revisar_gancho(c, st, valores, cifras, titulares)
        pr = (c.get("promesa_sugerida") or "").strip()
        if not 10 <= len(pr) <= 80 or PROMESA_CONECTOR.match(pr) or PROMESA_PROHIBIDA.search(pr):
            f.append("promesa_sugerida de 10–80 caracteres, oración propia, sin conector suelto ni «al final te digo»")
        if not (c.get("por_que") or "").strip():
            f.append("falta «por_que» (mecanismo y evidencia en una línea)")
        print("%-3s %-10s %-8s %-24s · %s%s" % (cid, c.get("familia"), c.get("visual") or "cifra", (c.get("pantalla") or "")[:24], voz,
                                               "" if f else "  ✓"))
        fallas += ["%s: %s" % (cid, x) for x in f]
        for x in av:
            print("AVISO %s: %s" % (cid, x))
    if a.usar is not None:
        if fallas:
            for x in fallas:
                print("FALLA", x)
            return falla("ganchos.json no pasa el gate: no se elige un candidato que no cumple las reglas")
        sel = leer(os.path.join(trabajo, "seleccion.json")) if not a.usar and os.path.exists(os.path.join(trabajo, "seleccion.json")) else {}
        gan, seg = a.usar or sel.get("ganador"), a.segundo or sel.get("segundo")
        if gan not in por_id or (seg and seg not in por_id) or gan == seg:
            return falla("--usar: el ganador «%s» y el segundo «%s» deben ser ids distintos de ganchos.json (o estar en "
                         "seleccion.json)" % (gan, seg))
        G["elegido"], G["segundo"] = gan, seg
        escribir(ruta, G)
        escena = {"tipo": "gancho", **{k: por_id[gan][k] for k in CAMPOS_GANCHO if por_id[gan].get(k) is not None},
                  "texto": por_id[gan]["texto"]}
        rg = os.path.join(trabajo, "guion.json")
        guion = leer(rg) if os.path.exists(rg) else {"escenas": []}
        esc = guion.get("escenas") or []
        if esc and esc[0].get("tipo") == "gancho":
            if len(esc) > 1 and texto_llano(esc[0].get("texto")) != texto_llano(escena.get("texto")):
                print("AVISO el guion ya tenía otro gancho: relee el hilo desde la escena 2 (lo que apuntaba al gancho "
                      "anterior queda colgado) y vuelve a pasar la crítica antes de grabar")
            esc[0] = escena
        else:
            esc.insert(0, escena)
        guion["escenas"] = esc
        escribir(rg, guion)
        print("→ escena 1 = %s (%s · %s); segundo para la versión B: %s · %s" % (gan, por_id[gan]["familia"],
              por_id[gan].get("visual") or "cifra", seg or "—", rel(rg)))
        return 0
    for x in fallas:
        print("FALLA", x)
    if fallas:
        return 1
    print("→ %s · %d candidatos · R1–R10 ok" % (rel(ruta), len(cands)))
    return 0


def cmd_variante(a):
    """Versión B del gancho (el segundo lugar de la selección) sobre el mismo video: arma <TRABAJO>/variante_b con el
    guion igual salvo la escena 1, reutiliza la voz, las palabras y los clips de las demás escenas e imprime el nodo de
    voz SOLO de la escena 1 (≈ 100 créditos). Con --cerrar, copia variante_b/salida/video.mp4 → salida/video_b.mp4."""
    trabajo = os.path.abspath(a.trabajo)
    vb = os.path.join(trabajo, "variante_b")
    if a.cerrar:
        src = os.path.join(vb, "salida", "video.mp4")
        if not os.path.exists(src):
            return falla("falta %s: descargar → tiempos → grabar --solo 1 → montar sobre variante_b" % rel(src))
        shutil.copy2(src, os.path.join(trabajo, "salida", "video_b.mp4"))
        print("→ %s (versión B: el gancho «%s»)" % (rel(os.path.join(trabajo, "salida", "video_b.mp4")),
                                                    (gancho_elegido(vb) or {}).get("pantalla")))
        return 0
    G = leer(os.path.join(trabajo, "ganchos.json"))
    seg = next((c for c in G.get("candidatos") or [] if c.get("id") == G.get("segundo")), None)
    if not seg:
        return falla("ganchos.json no tiene «segundo»: la versión B usa el segundo lugar de la selección (ganchos --usar)")
    for sub in ("audio", "clips", "segs", "revision", "salida"):
        os.makedirs(os.path.join(vb, sub), exist_ok=True)
    shutil.copy2(os.path.join(trabajo, "video.json"), os.path.join(vb, "video.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    pr = g.get("promesa") or {}
    texto = seg["texto"] + (" " + pr["texto"] if pr.get("en") == 1 and pr.get("texto") else "")
    viejo = (g["escenas"][0].get("texto") or "").strip()
    g["escenas"][0] = {"tipo": "gancho", **{k: seg[k] for k in CAMPOS_GANCHO if seg.get(k) is not None}, "texto": texto}
    for parte in g.get("narracion") or []:   # la narración de corrido abre con la voz del gancho: cambia con ella
        if viejo and parte.get("acto") == 1 and viejo in (parte.get("texto") or ""):
            parte["texto"] = parte["texto"].replace(viejo, texto, 1)
    escribir(os.path.join(vb, "guion.json"), g)
    escribir(os.path.join(vb, "ganchos.json"), dict(G, elegido=seg["id"], segundo=G.get("elegido")))
    if cmd_guion(argparse.Namespace(trabajo=vb)):
        return falla("la versión B no pasa el gate del guion (variante_b/guion.json)")
    n = len(g["escenas"]) + 1
    for k in range(2, n + 1):   # la voz, las palabras y los clips de las escenas 2…cierre son los del video A
        for f in ("audio/voz_%d.mp3", "audio/palabras_%d.json", "clips/e%d.mp4"):
            if os.path.exists(os.path.join(trabajo, f % k)):
                shutil.copy2(os.path.join(trabajo, f % k), os.path.join(vb, f % k))
    loc = leer(os.path.join(vb, "locucion.json"))
    e1 = loc["escenas"][0]
    print(json.dumps({"voz": loc["voz"], "model_parameters": {"language_code": loc["voz"]["idioma"]},
                      "caracteres": len(e1["voz"]), "nodos": [{"n": 1, "prompt": e1.get("prompt") or e1["voz"]}]},
                     ensure_ascii=False, indent=1))
    print("→ %s · luego: descargar %s --estado … (solo la escena 1), tiempos, grabar --solo 1, montar y variante --cerrar"
          % (rel(vb), rel(vb)))
    return 0


# ---------- voz ----------
def nodos_pendientes(trabajo, loc):
    """Las escenas que hay que (re)generar: sin audio/voz_N.mp3 o palabras_N.json, o cuya locución ya no es lo que Scribe
    alineó (la voz cambió en un retoque)."""
    out = []
    for e in loc["escenas"]:
        n, pw = e["n"], os.path.join(trabajo, "audio", "palabras_%d.json" % e["n"])
        if not os.path.exists(os.path.join(trabajo, "audio", "voz_%d.mp3" % n)) or not os.path.exists(pw) or \
                texto_llano(" ".join(w.get("text", "") for w in leer(pw))) != texto_llano(e["voz"]):
            out.append(n)
    return out


def cmd_voz(a):
    """El JSON con la voz y el prompt de cada nodo TTS: con voz de corrido (locucion.voz_continua), un nodo por secuencia
    («s3», sus escenas seguidas) más las escenas sueltas; --pendientes (solo lo que cambió o falta: las retomas; una
    secuencia entera si cambió una de sus escenas), --sueltas (las escenas pendientes como nodos propios, retoma barata
    con costura) y --solo."""
    trabajo = os.path.abspath(a.trabajo)
    loc = leer(os.path.join(trabajo, "locucion.json"))
    escenas = loc["escenas"]
    sueltas = bool(getattr(a, "sueltas", False) or getattr(a, "solo", None))
    if getattr(a, "solo", None):
        solo = {int(x) for x in a.solo.split(",")}
        escenas = [e for e in escenas if e["n"] in solo]
    pend = set(nodos_pendientes(trabajo, loc)) if getattr(a, "pendientes", False) else None
    if pend is not None:
        escenas = [e for e in escenas if e["n"] in pend]
    parcial = pend is not None or bool(getattr(a, "solo", None))
    nodos = []
    if loc.get("voz_continua") and not sueltas:
        en_sec = {}
        for s in loc.get("secuencias") or []:
            for n in s["escenas"]:
                en_sec[n] = s
        vistas = set()
        for e in escenas:
            s = en_sec.get(e["n"])
            if s is None:
                nodos.append({"n": e["n"], "prompt": e.get("prompt") or e["voz"]})
            elif s["k"] not in vistas:
                vistas.add(s["k"])
                nodos.append({"n": "s%d" % s["k"], "escenas": s["escenas"], "prompt": s["prompt"], "caracteres": s["caracteres"]})
                if pend is not None:
                    cambiadas = [n for n in s["escenas"] if n in pend]
                    print("secuencia s%d (E%d–E%d): ≈ %d créditos; cambió E%s" % (s["k"], s["escenas"][0], s["escenas"][-1], s["caracteres"],
                                                                                 ", E".join(map(str, cambiadas))), file=sys.stderr)
    else:
        nodos = [{"n": e["n"], "prompt": e.get("prompt") or e["voz"]} for e in escenas]
    creditos = sum(x.get("caracteres") or len(x["prompt"]) for x in nodos) if parcial else loc["caracteres"]
    if pend is not None:
        print("%d escena(s) sin cambio; %d por generar en %d nodo(s) (≈ %d créditos)" % (len(loc["escenas"]) - len(pend), len(escenas),
              len(nodos), creditos), file=sys.stderr)   # a stderr: el JSON de stdout sigue limpio
    print(json.dumps({"voz": loc["voz"], "model_parameters": {"language_code": loc["voz"]["idioma"]},
                      "caracteres": creditos, "nodos": nodos}, ensure_ascii=False, indent=1))
    return 0


def bajar_voz(trabajo, n, url):
    dst = os.path.join(trabajo, "audio", "voz_%s.mp3" % n)
    urllib.request.urlretrieve(url, dst)
    print("voz_%s.mp3 %.2f s" % (n, ffprobe_dur(dst)))


RE_ETIQUETA = re.compile(r'^(<\S*|\S*/?>|\w+="[^"]*")$')


def sin_etiquetas(ws):
    """Scribe, conectado al nodo TTS, alinea el prompt y devuelve la etiqueta `<break time="0.6s" />` como tres
    «palabras» de duración cero: no son voz y V6 las contaría de más."""
    return [w for w in ws if not RE_ETIQUETA.match(w["text"].strip())]


def bajar_palabras(trabajo, n, url):
    with urllib.request.urlopen(url) as r:
        d = json.loads(r.read().decode("utf-8"))
    ws = d["words"] if isinstance(d, dict) else d
    ws = sin_etiquetas([{"text": w["text"], "start": w["start"], "end": w["end"]} for w in ws
                        if w.get("type", "word") == "word" and not w["text"].startswith("[")])
    escribir(os.path.join(trabajo, "audio", "palabras_%s.json" % n), ws)
    print("palabras_%s.json %d palabras" % (n, len(ws)))


def texto_llano(s):
    """Para emparejar prompts con la locución: sin etiquetas <break>, minúsculas, solo letras y números."""
    return re.sub(r"[\W_]+", " ", re.sub(r"<[^>]+>", " ", s or "").lower()).strip()


def descargar_estado(trabajo, archivos):
    """Lee los JSON guardados de creative_get_flow_run_status (voz y Scribe, en uno o varios archivos) y baja lo que
    traigan: la voz por su prompt (= la locución de la escena; si una escena viene varias veces, la generación más
    reciente), las palabras por el id de generación de su fuente (o por el texto transcrito si la voz no viene en estos
    archivos). Los créditos cobrados van a audio/creditos.json por id de generación: una retoma suma, repetir el
    mismo archivo no."""
    loc = leer(os.path.join(trabajo, "locucion.json"))
    # cada voz se reconoce por su prompt: una escena (n) o una secuencia («sec_K», las voces seguidas)
    por_voz = {texto_llano(e["voz"]): e["n"] for e in loc["escenas"]}
    secs = {s["k"]: s for s in loc.get("secuencias") or []}
    por_escena = {e["n"]: e for e in loc["escenas"]}
    largo = {}   # caracteres de voz por nodo, para deshacer un prefijo ambiguo con la duración del audio
    for s in secs.values():
        por_voz[texto_llano(" ".join(por_escena[n]["voz"] for n in s["escenas"]))] = "sec_%d" % s["k"]
        largo["sec_%d" % s["k"]] = s["caracteres"]
    for e in loc["escenas"]:
        largo[e["n"]] = len(e["voz"])
    gens, trans, prompt_media = [], [], {}
    for f in archivos:
        d = leer(f)
        gens += d.get("generations") or []
        trans += d.get("transcripts") or []
        for m in d.get("media") or []:
            if m.get("generation_id") and m.get("prompt"):
                prompt_media[m["generation_id"]] = m["prompt"]

    def escena_por_prompt(p, dur_s=None):
        """El MCP recorta `generations[].prompt` a 200 caracteres (`media[].prompt` viene entero): si no casa entero,
        vale como prefijo cuando solo una escena empieza así; si una escena y su secuencia empiezan igual, decide la
        duración del audio (la voz cruda va a ≈ CPS/VELOCIDAD caracteres por segundo)."""
        if not p:
            return None
        ll = texto_llano(p)
        if ll in por_voz:
            return por_voz[ll]
        if len(p) >= 200:
            hits = [n for v, n in por_voz.items() if v.startswith(ll)]
            if len(hits) == 1:
                return hits[0]
            if hits and dur_s:
                return min(hits, key=lambda n: abs(dur_s - largo[n] / (CPS / VELOCIDAD)))
        return None
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    cred = leer(ruta_cred) if os.path.exists(ruta_cred) else {"generaciones": {}, "total": 0}
    escena_de_gen, voces, palabras = {}, {}, {}
    for g in gens:
        if g.get("modality") != "audio" or g.get("status") != "completed" or not g.get("content_url"):
            continue
        n = escena_por_prompt(prompt_media.get(g.get("id")), g.get("duration_secs"))
        if n is None:
            n = escena_por_prompt(g.get("prompt"), g.get("duration_secs"))
        if n is None:
            print("AVISO generación %s: su prompt no es la voz de ninguna escena ni secuencia" % g.get("id"))
            continue
        escena_de_gen[g.get("id")] = n
        if n not in voces or (g.get("created_at_unix_ms") or 0) >= (voces[n].get("created_at_unix_ms") or 0):
            voces[n] = g
    for tr in trans:
        m = re.search(r"/content_generation/[^/]+/([^/]+)/", (tr.get("source") or {}).get("url") or "")
        n = escena_de_gen.get(m.group(1)) if m else None
        if n is None:
            n = por_voz.get(texto_llano(tr.get("text")))
        if n is None or not tr.get("words_download_url"):
            print("AVISO transcripción %s: no sé de qué escena es" % tr.get("generation_id"))
            continue
        palabras[n] = tr["words_download_url"]
    orden = lambda n: (0, n) if isinstance(n, int) else (1, int(n[4:]))  # noqa: E731
    for n in sorted(voces, key=orden):
        bajar_voz(trabajo, n, voces[n]["content_url"])
        c = (voces[n].get("price") or {}).get("credits")
        if c is not None:
            cred["generaciones"][voces[n].get("id")] = {"n": n, "creditos": round(c, 2)}
    for n in sorted(palabras, key=orden):
        bajar_palabras(trabajo, n, palabras[n])
    for n in sorted(set(voces) | set(palabras), key=orden):   # las secuencias se cortan en sus escenas
        if isinstance(n, str) and n.startswith("sec_"):
            k = int(n[4:])
            if os.path.exists(os.path.join(trabajo, "audio", "voz_sec_%d.mp3" % k)) and os.path.exists(os.path.join(trabajo, "audio", "palabras_sec_%d.json" % k)):
                rc = partir_secuencia(trabajo, k, loc)
                if rc:
                    return rc
    if cred["generaciones"]:
        cred["total"] = round(sum(x["creditos"] for x in cred["generaciones"].values()), 2)
        escribir(ruta_cred, cred)
        print("creditos.json: %s créditos en %d generación(es)" % (cred["total"], len(cred["generaciones"])))
    faltan = ["voz_%d.mp3" % e["n"] for e in loc["escenas"] if not os.path.exists(os.path.join(trabajo, "audio", "voz_%d.mp3" % e["n"]))] + \
             ["palabras_%d.json" % e["n"] for e in loc["escenas"] if not os.path.exists(os.path.join(trabajo, "audio", "palabras_%d.json" % e["n"]))]
    if faltan:
        return falla("faltan en audio/: %s (rehaz esos nodos o pasa el estado que los trae)" % ", ".join(faltan))
    return 0


def cmd_descargar(a):
    trabajo = os.path.abspath(a.trabajo)
    os.makedirs(os.path.join(trabajo, "audio"), exist_ok=True)   # preparar la crea; puede faltar si se movió la carpeta
    if a.estado:
        return descargar_estado(trabajo, [os.path.abspath(f) for f in a.estado])
    origen, tipo = (a.voz, "voz") if a.voz else (a.palabras, "palabras")
    for n, url in sorted(leer(origen).items(), key=lambda kv: int(kv[0])):
        (bajar_voz if tipo == "voz" else bajar_palabras)(trabajo, n, url)
    return 0


def tono_falso(textos, salida_mp3, salida_json, pausa=0.0):
    """Fixture: un tono corto por palabra (para que el ducking y los efectos se prueben) con la duración que tendría la
    voz, y palabras repartidas por longitud; varios textos seguidos (una secuencia) llevan `pausa` s entre ellos."""
    cps_crudo = CPS / VELOCIDAD
    t, ws = 0.0, []
    for j, texto in enumerate(textos):
        if j:
            t += pausa
        for w in texto.split():
            d = (len(w) + 1) / cps_crudo
            ws.append({"text": w, "start": round(t, 3), "end": round(t + d * 0.85, 3)})
            t += d
    # el tono se escribe en un WAV con la stdlib (un aevalsrc con un between() por palabra no cabe en ffmpeg cuando la
    # secuencia pasa de ~40 s) y ffmpeg solo lo codifica
    sr = 44100
    muestras = array.array("h", bytes(2 * int(math.ceil(t * sr))))
    for w in ws:
        for i in range(int(w["start"] * sr), min(len(muestras), int(w["end"] * sr))):
            muestras[i] = int(0.28 * 32767 * math.sin(2 * math.pi * 165 * i / sr))
    wav = salida_mp3[:-4] + ".tono.wav"
    with wave.open(wav, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(muestras.tobytes())
    ff("-i", wav, "-c:a", "libmp3lame", "-b:a", "64k", salida_mp3)
    os.remove(wav)
    escribir(salida_json, ws)


def cmd_voz_falsa(a):
    """Fixture: voz falsa por escena; con voz de corrido (locucion.voz_continua), por secuencia y luego `partir` la corta
    en sus escenas: la maqueta ejercita el corte sin créditos."""
    trabajo = os.path.abspath(a.trabajo)
    loc = leer(os.path.join(trabajo, "locucion.json"))
    audio = os.path.join(trabajo, "audio")
    en_sec = {n for s in (loc.get("secuencias") or []) if loc.get("voz_continua") for n in s["escenas"]}
    for e in loc["escenas"]:
        if e["n"] in en_sec:
            continue
        tono_falso([e["voz"]], os.path.join(audio, "voz_%d.mp3" % e["n"]), os.path.join(audio, "palabras_%d.json" % e["n"]))
    por_escena = {e["n"]: e for e in loc["escenas"]}
    for s in (loc.get("secuencias") or []) if loc.get("voz_continua") else []:
        tono_falso([por_escena[n]["voz"] for n in s["escenas"]], os.path.join(audio, "voz_sec_%d.mp3" % s["k"]),
                   os.path.join(audio, "palabras_sec_%d.json" % s["k"]), pausa=0.35)
        rc = partir_secuencia(trabajo, s["k"], loc)
        if rc:
            return rc
    print("voz falsa: %d escenas%s" % (len(loc["escenas"]), " (%d secuencia(s) de corrido, cortadas)" % len(loc.get("secuencias") or []) if en_sec else ""))
    return 0


def partir_secuencia(trabajo, k, loc):
    """Corta la voz de una secuencia (audio/voz_sec_K.mp3 + palabras_sec_K.json de Scribe) en voz_N.mp3 y palabras_N.json
    por escena: asigna las palabras de Scribe a cada escena en orden (criterio de V6; repara un token fundido o partido en
    la frontera) y corta a mitad del silencio entre la última palabra de una escena y la primera de la siguiente, con un
    wav intermedio (el corte exacto, sin cuadros de mp3). → 0 ok · 1 falla V6 (rehaz la secuencia o `voz --sueltas`)."""
    audio = os.path.join(trabajo, "audio")
    s = next((x for x in loc.get("secuencias") or [] if x["k"] == k), None)
    if not s:
        return falla("locucion.json no tiene la secuencia %d" % k)
    por_escena = {e["n"]: e for e in loc["escenas"]}
    ws = sin_etiquetas(leer(os.path.join(audio, "palabras_sec_%d.json" % k)))
    # las palabras del guion de toda la secuencia, en orden, con su escena: un token fundido o partido por Scribe puede
    # caer justo en la frontera entre dos escenas
    toks = [(n, tok) for n in s["escenas"] for tok in re.findall(r"\S+", por_escena[n]["voz"])]
    mios, j = {n: [] for n in s["escenas"]}, 0
    for i, (n, tok) in enumerate(toks):
        if j >= len(ws):
            return falla("V6 secuencia s%d (E%d): Scribe se quedó sin palabras en «%s» · rehaz la secuencia (o voz --sueltas)" % (k, n, tok))
        a, b = _norm(tok), _norm(ws[j]["text"])
        if a == b:
            mios[n].append(ws[j])
            j += 1
        elif i + 1 < len(toks) and b == a + _norm(toks[i + 1][1]):   # Scribe fundió dos palabras («residuales.Según»)
            w, p = ws[j], len(a) / max(1, len(b))
            corte = w["start"] + (w["end"] - w["start"]) * p
            mios[n].append({"text": tok, "start": w["start"], "end": round(corte, 3)})
            ws[j] = {"text": toks[i + 1][1], "start": round(corte, 3), "end": w["end"]}
        elif j + 1 < len(ws) and a == b + _norm(ws[j + 1]["text"]):   # Scribe partió una palabra
            mios[n].append({"text": tok, "start": ws[j]["start"], "end": ws[j + 1]["end"]})
            j += 2
        else:
            return falla("V6 secuencia s%d (E%d): «%s» en el guion, «%s» en Scribe (t=%.2f) · rehaz la secuencia (o voz --sueltas)"
                         % (k, n, tok, ws[j]["text"], ws[j]["start"]))
    if j < len(ws):
        return falla("V6 secuencia s%d: Scribe oyó %d palabra(s) de más al final («%s»)" % (k, len(ws) - j, ws[j]["text"]))
    escenas_ws = [(n, mios[n]) for n in s["escenas"]]
    if any(not m for _, m in escenas_ws):
        return falla("V6 secuencia s%d: una escena quedó sin palabras" % k)
    src = os.path.join(audio, "voz_sec_%d.mp3" % k)
    wav = os.path.join(audio, "voz_sec_%d.wav" % k)
    ff("-i", src, "-ar", "44100", "-ac", "1", wav)
    total = ffprobe_dur(wav)
    cortes = [0.0]
    for (_, a_ws), (_, b_ws) in zip(escenas_ws, escenas_ws[1:]):
        cortes.append(round((a_ws[-1]["end"] + b_ws[0]["start"]) / 2, 3))
    cortes.append(round(total, 3))
    for (n, mios), a, b in zip(escenas_ws, cortes, cortes[1:]):
        ff("-i", wav, "-af", "atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.004,afade=t=out:st=%.3f:d=0.004" % (a, b, max(0.0, b - a - 0.004)),
           "-c:a", "libmp3lame", "-b:a", "192k", os.path.join(audio, "voz_%d.mp3" % n))
        escribir(os.path.join(audio, "palabras_%d.json" % n), [{"text": w["text"], "start": round(w["start"] - a, 3), "end": round(w["end"] - a, 3)} for w in mios])
    ruta = os.path.join(audio, "secuencias.json")
    reg = leer(ruta) if os.path.exists(ruta) else {}
    reg[str(k)] = {"escenas": s["escenas"], "cortes_s": cortes}
    escribir(ruta, reg)
    print("secuencia s%d → %s (cortes en %s s)" % (k, ", ".join("voz_%d.mp3" % n for n in s["escenas"]), ", ".join("%.2f" % c for c in cortes[1:-1])))
    return 0


def cmd_partir(a):
    """Rehace el corte de una secuencia (o de todas) sin volver a bajar nada."""
    trabajo = os.path.abspath(a.trabajo)
    loc = leer(os.path.join(trabajo, "locucion.json"))
    ks = [a.secuencia] if a.secuencia else [s["k"] for s in loc.get("secuencias") or []]
    for k in ks:
        if not os.path.exists(os.path.join(trabajo, "audio", "voz_sec_%d.mp3" % k)):
            return falla("falta audio/voz_sec_%d.mp3" % k)
        rc = partir_secuencia(trabajo, k, loc)
        if rc:
            return rc
    return 0


# ---------- tiempos (V6) ----------
def _norm(w):
    return re.sub(r"[^\wáéíóúñü]", "", w.lower())


def alinear(e, habladas):
    """Agrupa las palabras habladas en tokens de pantalla: cada segmento con p ≠ v (cifra, unidad) es UN token
    que dura lo que se tarda en decirlo; el texto llano va palabra por palabra."""
    segs = e["segmentos"]
    voz, dueno = "", []
    for k, s in enumerate(segs):
        voz += s["v"]
        dueno += [k if (s["num"] or s["p"] != s["v"]) else None] * len(s["v"])
    palabras_ = list(re.finditer(r"\S+", voz))
    if len(palabras_) != len(habladas):
        raise ValueError("E%d: el texto tiene %d palabras y Scribe %d" % (e["n"], len(palabras_), len(habladas)))
    for m, h in zip(palabras_, habladas):
        if _norm(m.group()) != _norm(h["text"]):
            raise ValueError("E%d: «%s» en el guion, «%s» en Scribe (t=%.2f)" % (e["n"], m.group(), h["text"], h["start"]))
    toks = []
    for m, h in zip(palabras_, habladas):
        unidad = next((dueno[i] for i in range(m.start(), m.end()) if dueno[i] is not None), None)
        if unidad is not None and toks and toks[-1]["unidad"] == unidad:
            toks[-1]["end"], toks[-1]["fin_c"] = h["end"], m.end()
            continue
        toks.append({"unidad": unidad, "ini_c": m.start(), "fin_c": m.end(), "start": h["start"], "end": h["end"]})
    out = []
    for t in toks:
        if t["unidad"] is None:
            texto = voz[t["ini_c"]:t["fin_c"]]
        else:  # «dos.» → «1,596.2.»: el segmento en pantalla con la puntuación pegada
            s = segs[t["unidad"]]
            ini = sum(len(x["v"]) for x in segs[:t["unidad"]])
            texto = voz[t["ini_c"]:ini] + s["p"].strip() + voz[ini + len(s["v"]):t["fin_c"]]
        out.append({"text": texto, "start": t["start"], "end": t["end"],
                    "seg": segs[t["unidad"]] if t["unidad"] is not None else None})
    return out


def fin_oracion_desde(pal, k0=0):
    """Fin (s) de la oración de la voz que contiene el token k0: el `end` del primer token desde k0 que termina en
    . ! ? …; si no hay, el fin del último token."""
    for p in pal[k0:]:
        if p["text"].rstrip().endswith((".", "!", "?", "…")):
            return p["end"]
    return pal[-1]["end"] if pal else 0.0


def alinear_linea(palabras_linea, pal, t_ini, t_fin):
    """La línea de pantalla palabra a palabra en sincronía con la voz: cada palabra que la voz dice literal entra
    0.05 s antes de que la voz la diga (nunca antes de t_ini); las que no dice se reparten entre los anclajes vecinos
    (o entre t_ini y t_fin). Monótona, ≥ 0.12 s entre palabras. → (lista [{text, start}], índice del último token
    anclado o None)."""
    n = len(palabras_linea)
    if not n:
        return [], None
    # alineación óptima y monótona (bloques comunes más largos primero): una búsqueda voraz anclaba un «de» de la
    # pantalla al «de» de otra oración y dejaba la línea quieta hasta ahí. Un bloque de una sola palabra vacía no ancla
    anclas, k_ult = [None] * n, None
    ln, pn = [_norm(w) for w in palabras_linea], [_norm(w["text"]) for w in pal]
    for a, b, m in difflib.SequenceMatcher(None, ln, pn, autojunk=False).get_matching_blocks():
        if m == 1 and ln[a] in VACIAS:
            continue
        for q in range(m):
            if ln[a + q]:
                anclas[a + q], k_ult = max(t_ini, pal[b + q]["start"] - 0.05), b + q
    if all(a is None for a in anclas):   # la voz no dice ninguna palabra literal: reparto hasta el fin de la oración
        return repartir(palabras_linea, t_ini, t_fin), None
    # las palabras no dichas se agrupan como frase: justo antes de la siguiente dicha (o justo después de la última)
    out, j = [None] * n, 0
    while j < n:
        if anclas[j] is not None:
            out[j] = anclas[j]
            j += 1
            continue
        j2 = j
        while j2 < n and anclas[j2] is None:
            j2 += 1
        m = j2 - j
        for q in range(m):
            out[j + q] = max(t_ini, anclas[j2] - 0.12 * (m - q)) if j2 < n else out[j - 1] + 0.12 * (q + 1)
        j = j2
    for j in range(1, n):
        out[j] = max(out[j], out[j - 1] + 0.12)
    return [{"text": w, "start": round(t, 3), **({"dicha": True} if anclas[j] is not None else {})}
            for j, (w, t) in enumerate(zip(palabras_linea, out))], k_ult


def indice_frase(pal, frase):
    """Índice del token de la voz donde empieza `frase` (sus 2 primeras palabras, normalizadas), o None."""
    NE.AVISOS.clear()
    ws = [_norm(w) for w in NE.convertir(sin_pausas(frase or ""))[1].split() if _norm(w)]
    NE.AVISOS.clear()
    if not ws:
        return None
    ws = ws[:2]
    for k in range(len(pal) - len(ws) + 1):
        if all(_norm(pal[k + q]["text"]) == ws[q] for q in range(len(ws))):
            return k
    return None


def clave(v):
    return ("%f" % v).rstrip("0").rstrip(".")


def valor_de(texto):
    m = re.search(NE.NUM, texto or "")
    return float(m.group().replace(",", "")) if m else None


def repartir(palabras_, t0, t1, minimo=0.18):
    """Palabras repartidas uniformemente en [t0, t1] (≥ `minimo` s por palabra, comprimiendo hacia t1 si no caben)."""
    n = max(1, len(palabras_))
    paso = max(minimo, (t1 - t0) / n) if n > 1 else 0
    ini = min(t0, max(0.0, t1 - paso * (n - 1)))
    return [{"text": w, "start": round(ini + paso * k, 3)} for k, w in enumerate(palabras_)]


UNIDADES_LLENADO = (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000, 25000, 50000, 100000)
LLENADO_PUNTOS = 240   # puntos máximos del visual llenado (cada punto = u unidades)


def tiempos_visual(vis, pal, fin_1, fin_voz):
    """El visual del gancho sincronizado con la voz (gancho.html lee S.V): está entero en el cuadro 0 (R12: miniatura y
    bucle) y cada número cambia cuando la voz lo dice → (V, eventos, efectos)."""
    def dicho(v):
        w = next((x for x in pal if v is not None and x.get("clave") == clave(v)), None)
        return [w["start"], w["end"]] if w else None
    tipo, V_ = vis.get("tipo"), {k: v for k, v in vis.items()}
    ev, sfx = [(0.0, "visual")], []
    if tipo == "llenado":
        cap, tot = vis["capacidad"], vis["total"]
        u = next(x for x in UNIDADES_LLENADO + (10 ** 9,) if tot / x <= LLENADO_PUNTOS)
        d = dicho(tot)
        a = d[0] if d else max(0.6, fin_1 - 1.6)
        b = max(a + 0.9, d[1] + 0.1 if d else a + 1.3)
        V_.update(u=u, puntos=math.ceil(tot / u), dentro=max(1, round(cap / u)), desborde=[round(a, 3), round(min(b, fin_voz + 0.6), 3)])
        ev += [(a, "desborde"), (V_["desborde"][1], "desborde_fin")]
        sfx += [(a, "whoosh"), (V_["desborde"][1], "resolucion")]
    elif tipo == "pareja":
        da, db = dicho(vis["a"]["valor"]), dicho(vis["b"]["valor"])
        tb = db[0] if db else max(0.8, fin_1 - 1.0)
        V_["t_a"] = round(da[0] if da and da[0] < tb else 0.15, 3)
        V_["t_b"] = [round(tb, 3), round(max(tb + 0.9, db[1] + 0.2 if db else tb + 1.2), 3)]
        ev += [(V_["t_b"][0], "pareja"), (V_["t_b"][1], "pareja_fin")]
        sfx += [(V_["t_b"][0], "whoosh"), (V_["t_b"][1], "pulso")]
    elif tipo == "figuras":
        dk = dicho(vis["k"])
        t = dk[0] if dk else max(0.8, fin_1 - 1.2)
        V_["destacadas"] = round(t, 3)
        paso = min(0.08, 0.9 / max(1, vis["k"]))
        ev += [(t, "destacadas"), (t + paso * vis["k"], "destacadas_fin")]
        sfx += [(t + paso * j, "tic") for j in range(min(vis["k"], 10))] + [(t + paso * vis["k"] + 0.1, "resolucion")]
    elif tipo == "lugar":
        claves_l = [_plano(vis.get("nombre"))] + [w for w in _plano(vis.get("etiqueta")).split() if len(w) >= 4 and w not in STOP]
        w = next((x for x in pal if any(c and _plano(x["text"]) and c.split()[0] == _plano(x["text"]) for c in claves_l)), None)
        t = w["start"] if w else 0.8
        V_["pin"] = round(t, 3)
        ev += [(t, "pin"), (t + 0.6, "pin_fin")]
        sfx += [(t, "foco")]
    V_.pop("numeros", None)
    return V_, ev, sfx


# ---------- V16: la voz no se corta dentro de un nombre ni de una cifra ----------
APRETAR_DB, APRETAR_MIN_S, APRETAR_DEJA_S = -35, 0.06, 0.03   # silencio que cuenta; lo que queda tras apretarlo
# desde cuánto se aprieta: dentro de una palabra, más que el cierre de una oclusiva («p», «t»: ≤ 0.1 s); entre dos
# palabras de la misma cifra o el mismo nombre, más que la juntura normal del habla de corrido
APRETAR_DENTRO_S, APRETAR_ENTRE_S = 0.10, 0.08
NEXOS_NOMBRE = {"de", "del", "la", "las", "los"}               # «Pérez de Antón», «Los Angeles Times»


def silencios(ruta):
    """Intervalos (s) de silencio de un audio con silencedetect."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", ruta, "-af",
                        "silencedetect=noise=%ddB:d=%.2f" % (APRETAR_DB, APRETAR_MIN_S), "-f", "null", "-"],
                       capture_output=True, text=True)
    ini, out = None, []
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", r.stderr):
        if m.group(1) == "start":
            ini = max(0.0, float(m.group(2)))
        elif ini is not None:
            fin = float(m.group(2))
            if out and ini - out[-1][1] < 0.02:   # silencedetect parte un mismo silencio en tramos pegados
                out[-1] = (out[-1][0], fin)
            else:
                out.append((ini, fin))
            ini = None
    return out


def unidades_continuas(e, ws):
    """Por palabra de Scribe, la unidad que se dice de corrido (o None): cada cifra (segmento con num o p ≠ v, como
    `alinear`) y cada nombre propio (palabras seguidas con mayúscula o siglas, unidas por de/del/la/las/los; la corrida
    acaba en coma, punto o dos puntos)."""
    segs = e.get("segmentos") or [{"p": e.get("voz") or "", "v": e.get("voz") or "", "num": False}]
    voz, dueno = "", []
    for k, s in enumerate(segs):
        voz += s["v"]
        dueno += [k if (s["num"] or s["p"] != s["v"]) else None] * len(s["v"])
    toks = list(re.finditer(r"\S+", voz))
    if len(toks) != len(ws):
        return [None] * len(ws)   # V6 lo dirá en alinear; sin alineación no se aprieta nada
    def limpio(m):
        return m.group().strip("¿¡«»\"'()")

    uni, nombre, en_nombre = [], 0, False
    for i, m in enumerate(toks):
        cifra = next((dueno[c] for c in range(m.start(), m.end()) if dueno[c] is not None), None)
        if cifra is not None:
            uni.append(("c", cifra))
            en_nombre = False
            continue
        cap = limpio(m)[:1].isupper()
        nexo = en_nombre and limpio(m).lower() in NEXOS_NOMBRE and i + 1 < len(toks) and limpio(toks[i + 1])[:1].isupper()
        if cap or nexo:
            if not en_nombre:
                nombre += 1
            uni.append(("n", nombre))
            en_nombre = not re.search(r"[,.;:?!…»]$", m.group())
        else:
            uni.append(None)
            en_nombre = False
    return uni


def apretar_voz(src, ws, e, dst_wav):
    """V16: quita el silencio que la voz metió DENTRO de una palabra («B…BC») o entre dos palabras de la misma cifra o
    del mismo nombre («dos mil… dos»): lo deja en APRETAR_DEJA_S. Escribe dst_wav (sin tocar src) y devuelve las
    palabras con sus tiempos movidos, lo recortado [{palabra, quitado_s}] y los avisos de palabra alargada sin silencio."""
    uni = unidades_continuas(e, ws)
    cortes, recortes = [], []
    for a, b in silencios(src):
        dentro = next((w for w in ws if a >= w["start"] + 0.03 and b <= w["end"] - 0.05), None) if b - a >= APRETAR_DENTRO_S else None
        entre = next((i for i in range(len(ws) - 1) if uni[i] and uni[i] == uni[i + 1]
                      and ws[i]["end"] - 0.05 <= (a + b) / 2 <= ws[i + 1]["start"] + 0.05), None) if b - a >= APRETAR_ENTRE_S else None
        if dentro is None and entre is None:
            continue
        x0, x1 = a + APRETAR_DEJA_S / 2, b - APRETAR_DEJA_S / 2
        cortes.append((x0, x1))
        palabra = dentro["text"] if dentro is not None else "%s %s" % (ws[entre]["text"], ws[entre + 1]["text"])
        recortes.append({"palabra": palabra.strip(",.;:"), "quitado_s": round(x1 - x0, 3)})

    def mover(t):
        return t - sum(min(max(t - x0, 0.0), x1 - x0) for x0, x1 in cortes)

    if cortes:
        sel = "+".join("between(t,%.4f,%.4f)" % c for c in cortes)
        ff("-i", src, "-af", "aselect='not(%s)',asetpts=N/SR/TB" % sel, "-ar", "44100", dst_wav)
    else:
        ff("-i", src, "-ar", "44100", dst_wav)
    movidas = [dict(w, start=round(mover(w["start"]), 3), end=round(mover(w["end"]), 3)) for w in ws]
    # alargada sin silencio: una palabra de cifra o de nombre que dura mucho más de lo que pide su largo
    sil = silencios(dst_wav) if cortes else silencios(src)
    avisos = []
    for w, u in zip(movidas, uni):
        if not u:
            continue
        limpio = re.sub(r"[^\wáéíóúñü]", "", w["text"])
        sigla = limpio.isupper() and 2 <= len(limpio) <= 5
        esperado = 0.3 * len(limpio) if sigla else 0.085 * len(limpio) + 0.1
        dur = (w["end"] - w["start"]) - sum(max(0.0, min(b, w["end"]) - max(a, w["start"])) for a, b in sil)
        if dur > 0.5 and dur > 1.6 * esperado:
            avisos.append("«%s» dura %.2f s (esperado ≈ %.2f s)" % (limpio, dur, esperado))
    return movidas, recortes, avisos


def voz_de_escena(trabajo, e):
    """V16 + atempo: aprieta la voz de la escena (voz_N.mp3 queda intacto) y la acelera a VELOCIDAD en voz_N_r.mp3.
    Devuelve las palabras habladas en el tiempo final, lo recortado y los avisos (lo comparten /video, /noticias y
    /historia)."""
    n = e["n"]
    audio = os.path.join(trabajo, "audio")
    src, wav, dst = [os.path.join(audio, x % n) for x in ("voz_%d.mp3", "voz_%d_apretada.wav", "voz_%d_r.mp3")]
    ws = sin_etiquetas(leer(os.path.join(audio, "palabras_%d.json" % n)))
    ws, recortes, avisos = apretar_voz(src, ws, e, wav)
    ff("-i", wav, "-af", "atempo=%s" % VELOCIDAD, "-c:a", "libmp3lame", "-b:a", "192k", dst)
    os.remove(wav)
    for r in recortes:
        print("V16 E%d «%s» −%.2f s de silencio dentro del nombre o la cifra (apretado)" % (n, r["palabra"], r["quitado_s"]))
    habladas = [dict(w, start=w["start"] / VELOCIDAD, end=w["end"] / VELOCIDAD) for w in ws]
    return habladas, recortes, ["V16 E%d %s: suena alargada sin silencio · retoma esa escena (voz --sueltas %d)" % (n, x, n)
                                for x in avisos]


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    st, loc = estado(trabajo), leer(os.path.join(trabajo, "locucion.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    beats = {t["n"]: t.get("beat") for t in st["tarjetas"]}
    notas = {t["n"]: t.get("nota") for t in st["tarjetas"]}
    anios_tarjeta = {t["n"]: t.get("anios") or [] for t in st["tarjetas"]}
    datos_t = {t["n"]: t.get("datos") for t in st["tarjetas"]}
    pago_n = (loc.get("promesa") or {}).get("pago")
    promesa_en, promesa_txt = (loc.get("promesa") or {}).get("en"), (loc.get("promesa") or {}).get("texto")
    # el giro: la escena «pero» cuyo tuit tiene beat giro; si no hay, el primer «pero»
    peros = [e["n"] for e in loc["escenas"] if e.get("enlace") == "pero"]
    giro_n = next((e["n"] for e in loc["escenas"] if e.get("enlace") == "pero" and beats.get(e.get("tuit")) == "giro"),
                  next((e["n"] for e in loc["escenas"] if e["n"] > 2 and beats.get(e.get("tuit")) == "giro"), peros[0] if peros else None))
    escenas, avisos = [], []
    for e in loc["escenas"]:
        n, tipo = e["n"], e.get("tipo") or ("cierre" if e["plantilla"] == "cierre" else "tarjeta")
        dst = os.path.join(trabajo, "audio", "voz_%d_r.mp3" % n)
        habladas, apretado, av16 = voz_de_escena(trabajo, e)
        avisos += av16
        try:
            ps = alinear(e, habladas)
        except ValueError as ex:
            return falla("V6 %s · rehaz la voz de esa escena" % ex)
        cierre = tipo == "cierre"
        fin_voz = ps[-1]["end"]
        k_e = loc["escenas"].index(e)
        sec = e.get("secuencia")
        cola = e.get("cola") if isinstance(e.get("cola"), (int, float)) else (COLA_CIERRE if cierre else COLA)
        dur = round(ffprobe_dur(dst) + cola, 3)
        pal = []
        for k, p in enumerate(ps):
            w = {"text": p["text"], "start": round(p["start"], 3), "end": round(p["end"], 3)}
            seg = p["seg"]
            if seg and seg["num"]:
                w["num"] = True
                if not es_anio_o_fecha(seg["p"], " ".join(x["text"] for x in ps[k + 1:k + 3])):
                    w["clave"] = clave(valor_de(seg["p"]))
            pal.append(w)
        S = {"n": n, "tipo": tipo, "tuit": e.get("tuit"), "plantilla": e["plantilla"], "enlace": e.get("enlace"),
             "icono": e.get("icono"), "dur": dur, "fin_voz": round(fin_voz, 3), "palabras": pal, "arriba": None,
             "acto": e.get("acto"), "secuencia": sec, "cola": cola, "apretado": apretado,
             # seguida: la anterior es de la misma secuencia (la voz viene de corrido); sigue: la siguiente lo es
             "seguida": bool(sec) and k_e > 0 and loc["escenas"][k_e - 1].get("secuencia") == sec,
             "sigue": bool(sec) and k_e + 1 < len(loc["escenas"]) and loc["escenas"][k_e + 1].get("secuencia") == sec}
        ev, sfx = [], []
        propio = CONSTRUCTORES.get(tipo)
        hecho = propio(S, e, ps, pal, fin_voz, dur, g) if propio else None
        if hecho is not None:
            ev, sfx = hecho
        elif cierre:
            # la frase final (remate o pregunta) empieza donde la voz la dice; si no se encuentra, tras el último punto
            k_preg = indice_frase(ps, final_de(g.get("cierre")))
            if k_preg is None or k_preg == 0:
                k_preg = max([k for k, p in enumerate(ps[:-1]) if p["text"].endswith((".", "!"))] or [-1]) + 1
            # pantalla A (conclusiones): las líneas del resumen se reparten entre el inicio y la pregunta; pantalla B
            # (desde «preg»): la pregunta sola y luego «Sígueme en»
            n_r = len((g.get("cierre") or {}).get("resumen") or []) or 2
            rs = [0.1] + [ps[max(1, k_preg * q // n_r)]["start"] if k_preg > 2 else 0.6 + 0.5 * q for q in range(1, n_r)]
            S["T"] = {"r": [round(x, 3) for x in rs], "r2": round(rs[1], 3), "preg": round(max(0.2, ps[k_preg]["start"] - 0.1), 3),
                      "sigue": round(fin_voz + 0.1, 3)}
            ev = [(x, "r%d" % (q + 1)) for q, x in enumerate(S["T"]["r"])] + [(S["T"]["preg"], "pregunta"), (S["T"]["sigue"], "sigue")]
            sfx = [(S["T"]["preg"], "resolucion")]
        elif tipo == "adivina":
            ad, cin = e.get("adivina") or {}, e.get("cinetico") or {}
            t0 = TRANSICION + 0.05
            k_q = next((k for k, p in enumerate(ps) if p["text"].rstrip().endswith("?")), None)
            fin_preg = ps[k_q]["end"] if k_q is not None else min(fin_voz - 1.5, t0 + 2.5)
            # la pregunta en sincronía con la voz (cada palabra que la voz dice entra al decirla; las demás, como frase)
            pregunta, _ = alinear_linea((ad.get("pregunta") or cin.get("pantalla") or "").split(), pal, t0, max(t0 + 0.4, fin_preg - 0.2))
            opciones = [{"text": op, "start": round(fin_preg + 0.25 + 0.3 * k, 3)} for k, op in enumerate(ad.get("opciones") or [])]
            # el revelado: la última cifra de la voz (la respuesta, tras la pausa)
            nums = [p for p in ps if p["seg"] and p["seg"]["num"]]
            revelado = max((opciones[-1]["start"] + 0.6) if opciones else t0 + 1.5, (nums[-1]["start"] - 0.1) if nums else fin_voz - 1.0)
            # «pausa y responde»: la píldora entra cuando la voz lo pide (tras la última «?») y se vacía hasta el revelado
            k_ult_q = max([k for k, p in enumerate(ps) if p["text"].rstrip().endswith("?")] or [-1])
            re_p = re.compile(r"^(%s)$" % "|".join(PAUSA_ADIVINA))
            k_p = next((k for k in range(k_ult_q + 1, len(ps)) if re_p.match(_plano(ps[k]["text"]))
                        or (_plano(ps[k]["text"]) == "para" and k + 2 < len(ps) and _plano(ps[k + 2]["text"]).startswith("video"))), None)
            pausa = round(max(opciones[-1]["start"] + 0.3 if opciones else t0, ps[k_p]["start"] - 0.05), 3) if k_p is not None else None
            if pausa is not None and pausa >= revelado - 0.3:
                pausa = None
            S["T"] = {"pregunta": pregunta, "opciones": opciones, "correcta": ad.get("correcta"), "revelado": round(revelado, 3),
                      "pausa": pausa, "fin": round(fin_voz, 3)}
            # la pregunta entra palabra a palabra: cuenta al empezar y al terminar (como la línea del golpe)
            ev = [(t0, "pregunta")] + ([(pregunta[-1]["start"], "pregunta_fin")] if len(pregunta) > 1 else []) + \
                 [(w["start"], "pregunta_dicha") for w in pregunta[1:-1] if w.get("dicha")] + \
                 [(o["start"], "opcion") for o in opciones] + ([(pausa, "pausa")] if pausa is not None else []) + [(revelado, "revelado")]
            sfx = [(0.0, "grave" if e.get("enlace") == "pero" else "impacto")] + [(o["start"], "tic") for o in opciones] + \
                  ([(pausa, "tic")] if pausa is not None else []) + [(revelado, "resolucion")]
        elif tipo == "explica":
            ex = e.get("explica") or {}
            S["arriba"] = [{"text": w, "start": round(TRANSICION + 0.12 * k, 3)} for k, w in enumerate((ex.get("titulo") or "").split())]
            S["animacion"], S["P"] = ex.get("animacion"), {"titulo": ex.get("titulo"), "pasos": ex.get("pasos") or []}
            ini = TRANSICION + 0.3
            # cada paso entra cuando la voz lo dice: los pasos seguidos se alinean juntos con la voz (monótono) y cada uno
            # toma su primera palabra dicha; los que la voz no dice literal se reparten entre sus vecinos
            ws, de = [], []
            for k, paso in enumerate(ex.get("pasos") or []):
                for w in paso.split():
                    ws.append(w)
                    de.append(k)
            al, _ = alinear_linea(ws, pal, ini, max(ini + 0.4, fin_voz - 0.3))
            n_p = len(ex.get("pasos") or [])
            starts = [None] * n_p
            for w, k in zip(al, de):
                if w.get("dicha") and starts[k] is None:
                    starts[k] = max(ini, w["start"] - 0.1)
            for k in range(n_p):
                if starts[k] is None:
                    a = next((starts[j] for j in range(k - 1, -1, -1) if starts[j] is not None), None)
                    b = next(((j, starts[j]) for j in range(k + 1, n_p) if starts[j] is not None), None)
                    a = ini if a is None else a
                    bj, bt = b if b else (n_p, max(a + 0.6, fin_voz - 0.5))
                    starts[k] = a + (bt - a) * 1 / (bj - k + 1)
            for k in range(1, n_p):
                starts[k] = max(starts[k], starts[k - 1] + 0.3)
            pasos = [{"texto": x, "start": round(t, 3)} for x, t in zip(ex.get("pasos") or [], starts)]
            S["T"] = {"ini": round(ini, 3), "pasos": pasos, "fin": round(fin_voz, 3), "dur": dur}
            ev = [(ini, "lienzo")] + [(p_["start"], "paso") for p_ in pasos]
            sfx = [(0.0, "grave" if e.get("enlace") == "pero" else "impacto")] + [(p_["start"], "tic") for p_ in pasos]
        elif tipo in ("gancho", "golpe", "definicion"):
            cin = e.get("cinetico") or {}
            texto_p = cin.get("pantalla") or ""
            v = None if tipo == "definicion" else valor_de(cin.get("pantalla"))  # el término no cuenta
            dicho = next((w for w in pal if v is not None and w.get("clave") == clave(v)), None)
            pulso = None
            # la cifra cuenta desde el primer cuadro (la pantalla funciona en silencio) y late cuando la voz la dice.
            # Tras la transición de entrada (no en la escena 1) empieza 0.35 s después
            t0 = 0.15 if n == 1 else TRANSICION + 0.05
            desde, hasta = t0, t0 + 0.95
            if dicho:
                pulso = [dicho["start"], dicho["end"]]
            # la línea en sincronía con la voz: cada palabra entra cuando la voz la dice; lo que la voz no dice literal se
            # reparte hasta el fin de la primera oración (en una definición, de la oración de la última palabra dicha)
            t_ini = hasta + 0.1
            fin_1 = fin_oracion_desde(pal, 0)
            linea, k_ult = alinear_linea((cin.get("linea") or "").split(), pal, t_ini, max(t_ini + 0.4, min(fin_1 - 0.1, fin_voz - 0.3)))
            if tipo == "definicion" and k_ult is not None and fin_oracion_desde(pal, k_ult) > fin_1:
                linea, k_ult = alinear_linea((cin.get("linea") or "").split(), pal, t_ini,
                                             max(t_ini + 0.4, min(fin_oracion_desde(pal, k_ult) - 0.1, fin_voz - 0.3)))
            S["T"] = {"pant": {"texto": texto_p, "v": v, "desde": round(desde, 3), "hasta": round(hasta, 3),
                               "pulso": [round(x, 3) for x in pulso] if pulso else None},
                      "linea": linea, "fin": round(fin_voz, 3)}
            # la línea entra palabra a palabra: cuenta como evento al empezar, al terminar y en cada palabra que la voz dice
            ev = [(desde, "cifra"), (hasta, "cifra_fin")] + ([(linea[0]["start"], "linea"), (linea[-1]["start"], "linea_fin")] if linea else []) + \
                 [(w["start"], "linea_dicha") for w in linea[1:-1] if w.get("dicha")] + ([(pulso[0], "pulso")] if pulso else [])
            if tipo == "gancho":
                sfx = [(0.1, "impacto"), (pulso[1] if pulso else hasta, "pulso")]
                vis = e.get("visual") or {}
                if vis.get("tipo") not in (None, "cifra"):   # gancho con visual: página gancho.html (S.V)
                    S["V"], ev_v, sfx_v = tiempos_visual(vis, pal, fin_1, fin_voz)
                    ev += ev_v
                    sfx += sfx_v
            else:
                sfx = [(0.0, "grave" if e.get("enlace") == "pero" else "impacto"), (hasta, "tic")]
        else:
            valores = {}
            for k, p in enumerate(ps):
                seg = p["seg"]
                if not seg or not seg["num"] or es_anio_o_fecha(seg["p"], " ".join(x["text"] for x in ps[k + 1:k + 3])):
                    continue
                valores.setdefault(clave(valor_de(seg["p"])), [round(p["start"] - 0.5, 3), round(p["end"], 3)])
            # años que la voz dice y la tarjeta tiene en su eje: la columna late (sin zoom) y cuenta para V10
            anios = {}
            for p in ps:
                seg = p["seg"]
                m = re.search(NE.NUM, seg["p"]) if seg and seg["num"] else None
                v = float(m.group().replace(",", "")) if m else None
                if v is not None and v.is_integer() and str(int(v)) in anios_tarjeta.get(e.get("tuit"), []):
                    anios.setdefault(str(int(v)), [round(p["start"], 3), round(min(p["end"], dur - 0.9), 3)])
            golpe = (e.get("golpe") or "").split()
            if golpe:  # el golpe entra cuando termina la transición de la escena
                S["arriba"] = [{"text": w, "start": round(TRANSICION + 0.12 * k, 3)} for k, w in enumerate(golpe)]
            # en el layout vertical no hay titular: el gráfico entra en cuanto termina la transición (el golpe, a la vez)
            tit = TRANSICION + 0.05
            ini = TRANSICION + 0.3
            fin_vals = max([w[1] for w in valores.values()] or [ini + 1.5])
            # la nota entra al terminar la última cifra o, si la primera oración sigue después, al cerrarla: el gate
            # estima el ritmo contando ese cierre como evento y aquí es la nota la que lo hace visible
            k1 = next((k for k, p in enumerate(ps[:-1]) if p["text"].endswith((".", "!", "?"))), None)
            fin_oracion = ps[k1]["end"] + 0.1 if k1 is not None else 0.0
            con_alias = dict(valores)
            for k, w in valores.items():
                for esc in (1e3, 1e6):
                    con_alias.setdefault(clave(float(k) * esc), w)
            S["T"] = {"tit": round(tit, 3), "ini": round(ini, 3), "valores": con_alias, "anios": anios,
                      "nota": round(min(max(fin_vals + 0.4, fin_oracion), dur - 1.2), 3), "linea_fin": round(fin_voz - 1.0, 3),
                      "foco": e.get("foco") is not False}   # foco: false en el guion = sin zoom a la cifra
            ev = ([(0.0, "golpe_arriba")] if golpe else []) + [(tit, "entra")]
            sfx = [(tit, "whoosh")]
            ultimo_tic = -9
            for desde, hasta in sorted(valores.values()):
                ev += [(desde, "foco"), (hasta, "conteo_fin")]
                if desde - tit >= 1.0:
                    sfx.append((desde, "foco"))
                if hasta - ultimo_tic >= 1.2:
                    sfx.append((hasta, "tic"))
                    ultimo_tic = hasta
            for desde, hasta in sorted(anios.values()):
                ev += [(desde, "anio"), (hasta, "anio_fin")]
                if desde - ultimo_tic >= 1.2:
                    sfx.append((desde, "tic"))
                    ultimo_tic = desde
            if notas.get(e.get("tuit")):
                ev.append((S["T"]["nota"], "nota"))
            if n == giro_n:
                sfx.append((0.0, "grave"))
        if tipo in ("ranking", "tiempo", "escala"):
            # escenas a pantalla completa con página propia: parten de la rama de tarjeta (valores dichos, golpe arriba)
            T = S["T"]
            T.pop("foco", None)
            T.pop("nota", None)
            ev = [x for x in ev if x[1] != "nota"]
            dat = datos_t.get(e.get("tuit")) or {}
            dicho_de = lambda v: T["valores"].get(clave(float(v)))  # noqa: E731  [inicio − 0.5, fin] de la palabra que lo dice
            if tipo == "ranking":
                its = items_de(dat, e.get("orden"))[:(e.get("top") or RANKING_TOP_DEFECTO)]
                top = len(its)
                hi = dat.get("destacar") if dat.get("items") and isinstance(dat.get("destacar"), int) and 0 <= dat["destacar"] < top else 0
                # la voz manda: cada puesto que la voz dice entra al decirlo; los que no dice entran antes, del último
                # al primero, repartidos entre el inicio y el primer puesto dicho
                dichos = {k: dicho_de(valor) for k, (nombre, valor) in enumerate(its)}
                primero_dicho = min([d[0] + 0.4 for d in dichos.values() if d] or [fin_voz - 1.2])
                sin_decir = sorted((k for k in range(top) if not dichos[k]), reverse=True)
                a0 = ini + 0.6
                a1 = max(a0 + 0.3 * (len(sin_decir) - 1), primero_dicho - 0.5)
                items = []
                for k, (nombre, valor) in enumerate(its):
                    d = dichos[k]
                    j = sin_decir.index(k) if k in sin_decir else None
                    start = d[0] + 0.4 if d else a0 + (a1 - a0) * j / max(1, len(sin_decir) - 1)
                    items.append({"puesto": k + 1, "nombre": nombre, "valor": valor, "hi": k == hi, "start": round(start, 3),
                                  "dicho": [round(d[0] + 0.5, 3), round(d[1], 3)] if d else None})
                T["items"] = items
                ev += [(it["start"], "item") for it in items]
                sfx += [(it["start"], "resolucion" if it["hi"] else "tic") for it in items]
            elif tipo == "tiempo":
                dichos_v = [float(k) for k in valores]   # los valores que dice la voz (sin los alias ×1000)
                pts = puntos_de(dat, T["anios"].keys(), dichos_v)
                ma, mb = ini + 0.3, max(ini + 1.5, fin_voz - 0.8)
                puntos = []
                for k, (et, v, sub, hi) in enumerate(pts):   # el marcador recorre el riel; el valor salta cuando la voz lo dice
                    llega = ma + (mb - ma) * k / max(1, len(pts) - 1)
                    d = dicho_de(v)
                    an = T["anios"].get(et) if et.isdigit() else None
                    start = d[0] + 0.4 if d else (an[0] if an else llega)
                    # el valor se rotula solo si la voz lo dice, en los extremos o en el destacado: nueve valores no caben
                    puntos.append({"etiqueta": et, "valor": v, "sub": sub, "hi": hi, "start": round(start, 3),
                                   "dicho": [round(d[0] + 0.5, 3), round(d[1], 3)] if d else None,
                                   "rotulo": bool(d) or hi or k in (0, len(pts) - 1)})
                T["puntos"], T["marcador"] = puntos, [round(ma, 3), round(mb, 3)]
                ev += [(p["start"], "punto") for p in puntos]
                sfx += [(p["start"], "resolucion" if p["hi"] else "tic") for p in puntos]
                if dat.get("antes") and dat.get("despues"):
                    txt = pildora_texto(float(dat["antes"]["valor"]), float(dat["despues"]["valor"]), dat.get("pildora") or "factor", dat.get("decimales_pildora"))
                    if txt:
                        t_p = min(max(max(p["start"] for p in puntos) + 0.7, fin_vals + 0.3), dur - 1.0)
                        T["pildora"] = {"texto": txt, "start": round(t_p, 3)}
                        ev.append((t_p, "pildora"))
                        sfx.append((t_p, "pulso"))
            else:
                K, N = e["escala"]["de_cada"]
                d = dicho_de(K)
                destacadas = d[0] + 0.5 if d else ini + 1.4
                paso_k = min(0.08, 0.9 / max(1, K))
                T.update({"k": K, "n": N, "etiqueta": e["escala"].get("etiqueta") or "", "figuras": round(ini + 0.2, 3),
                          "destacadas": round(destacadas, 3), "etiqueta_t": round(min(destacadas + paso_k * K + 0.5, dur - 1.0), 3)})
                ev += [(ini + 0.2, "figuras"), (destacadas, "destacadas"), (T["etiqueta_t"], "etiqueta")]
                sfx += [(destacadas + paso_k * j, "tic") for j in range(min(K, 10))] + [(destacadas + paso_k * K + 0.1, "resolucion")]
        # la promesa es un evento visual-sonoro (tic) donde la voz la empieza: el tramo línea → promesa no queda vacío
        if n == promesa_en and promesa_txt:
            k_pr = indice_frase(pal, promesa_txt)
            if k_pr is not None:
                ev.append((pal[k_pr]["start"], "promesa"))
                sfx.append((pal[k_pr]["start"], "tic"))
        if n == pago_n and n != 1:
            sfx.append((-2.0, "riser"))
        # transición de entrada (xfade en montar) del catálogo TRANSICIONES: por papel (giro, primera tarjeta, cierre)
        # y, si no, por tipo (texto, adivina, pantalla completa, tarjeta)
        clave_tr = None if n == 1 else (
            "giro" if n == giro_n else TRANSICION_DE[tipo] if tipo in TRANSICION_DE else "cierre" if tipo == "cierre" else "primera" if len(escenas) == 1 else
            "texto" if tipo in ("golpe", "definicion") else "adivina" if tipo == "adivina" else
            "completa" if tipo in PANTALLA_COMPLETA + ("explica",) else "tarjeta")
        S["transicion"] = TRANSICIONES[clave_tr] if clave_tr else None
        if S["seguida"] and clave_tr in ("tarjeta", "texto"):
            # dentro de una secuencia la voz viene de corrido: la tarjeta o el texto se funden y no entran con golpe de
            # efecto (el giro, el cierre, la adivina y lo que va a pantalla completa conservan su transición)
            S["transicion"] = TRANSICIONES["seguida"]
            sfx = [(t, k) for t, k in sfx if not (t <= TRANSICION + 0.1 and k in ("whoosh", "impacto"))]
        for post in POST_CONSTRUCTORES:
            ev, sfx = post(S, e, ps, pal, fin_voz, dur, g, ev, sfx)
        ev.append((dur, "fin"))
        S["eventos"] = [{"t": round(t, 3), "tipo": k} for t, k in sorted(ev, key=lambda x: x[0])]
        S["sfx"] = [{"t": round(t, 3), "id": k} for t, k in sorted(sfx, key=lambda x: x[0])]
        escenas.append(S)
        print("E%-2d %-7s %6.2f s  eventos=%d  %s" % (n, tipo, dur, len(S["eventos"]), json.dumps(S["T"], ensure_ascii=False)[:140]))
    total = sum(s["dur"] for s in escenas) - TRANSICION * (len(escenas) - 1)
    obj = st["objetivo_s"]
    if abs(total - obj) > obj * 0.15:
        avisos.append("V6 duración real %.1f s fuera de ±15 %% de %d s" % (total, obj))
    # V10 ritmo real: hueco máximo entre eventos consecutivos de todo el video (las escenas se solapan TRANSICION s)
    linea_t, off, pago_t = [], 0.0, None
    for s in escenas:
        if s["n"] == pago_n:
            pago_t = off
        linea_t += [(off + x["t"], x["tipo"], s["n"]) for x in s["eventos"]]
        off += s["dur"] - TRANSICION
    linea_t.sort()
    peor = max(zip(linea_t, linea_t[1:]), key=lambda ab: ab[1][0] - ab[0][0]) if len(linea_t) > 1 else None
    if peor and peor[1][0] - peor[0][0] > RITMO_MAX_S:
        avisos.append("V10 ritmo: %.1f s sin evento entre «%s» (E%d) y «%s» (E%d)"
                      % (peor[1][0] - peor[0][0], peor[0][1], peor[0][2], peor[1][1], peor[1][2]))
    e1 = loc["escenas"][0]
    escribir(os.path.join(trabajo, "escenas.json"), {
        "version": 2, "colores": colores(st["paleta"]), "contexto_superior": g["contexto_superior"], "redes": REDES,
        "gancho": {"pantalla": (e1.get("cinetico") or {}).get("pantalla"), "linea": (e1.get("cinetico") or {}).get("linea")},
        "pago": {"n": pago_n, "t": round(pago_t, 3) if pago_t is not None else None},
        "cierre": {"resumen": g["cierre"]["resumen"], "final": final_de(g["cierre"]), "pregunta": final_de(g["cierre"]),
                   "tipo": g["cierre"].get("tipo") or "pregunta"},
        "transicion_s": TRANSICION, "total_s": round(total, 2), "escenas": escenas})
    for x in avisos:
        print("AVISO", x)
    print("total %.1f s (objetivo %d s) · hueco máximo %.1f s → %s"
          % (total, obj, (peor[1][0] - peor[0][0]) if peor else 0, rel(os.path.join(trabajo, "escenas.json"))))
    return 0


# ---------- grabar (V7) ----------
def cmd_grabar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    hilo_dir = tarjetas_dir(trabajo, st)   # /noticias no tiene hilo ni tarjetas; las de /video, rearmadas en Noche
    args = ["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, *(["--hilo", hilo_dir] if hilo_dir else []),
            "--fps", str(a.fps), "--formato", a.formato]
    if a.solo:
        args += ["--solo", a.solo]
    if a.paralelo:
        args += ["--paralelo", str(a.paralelo)]
    rc = subprocess.run(args, cwd=RAIZ).returncode
    if rc == 3:   # los clips quedaron escritos; algo visible sale de la zona segura (revision/zona[_4x5].json)
        return falla("V13 algo visible sale de la zona segura de TikTok, Reels y Shorts (ver las líneas FALLA V13 y "
                     "revision/zona%s.json): corrige la escena y vuelve a grabar" % ("_4x5" if a.formato == "4:5" else ""))
    if rc:
        return falla("la grabación falló")
    # V7: el último cuadro de cada tarjeta animada es idéntico a su render estático
    esc = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    htmls = [os.path.join(hilo_dir, "tuit_%d.html" % e["tuit"]) for e in esc if e.get("tuit")] if hilo_dir else []
    if htmls and subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_animar.js"), "--check", *htmls], cwd=RAIZ).returncode:
        return falla("V7 el estado final de alguna tarjeta animada no coincide con su PNG")
    return 0


# ---------- montar (V8) ----------
def musica_bucle(archivo, total, salida):
    """La pista en bucle con crossfades de 4 s hasta cubrir `total` segundos."""
    largo = ffprobe_dur(archivo)
    copias = max(1, math.ceil((total - largo) / (largo - 4)) + 1) if total > largo else 1
    entradas = sum([["-i", archivo] for _ in range(copias)], [])
    if copias == 1:
        filtro = "[0:a]atrim=0:%.3f[m]" % total
    else:
        filtro, prev = "", "[0:a]"
        for i in range(1, copias):
            out = "[x%d]" % i
            filtro += "%s[%d:a]acrossfade=d=4:c1=tri:c2=tri%s;" % (prev, i, out)
            prev = out
        filtro += "%satrim=0:%.3f[m]" % (prev, total)
    ff(*entradas, "-filter_complex", filtro, "-map", "[m]", "-ar", "48000", salida)


def medir(audio):
    """Medidas de loudnorm (input_i, input_tp, input_lra, input_thresh, target_offset) de un archivo."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", "loudnorm=I=%s:TP=-1.5:LRA=11:print_format=json" % LUFS,
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    return {k: float(j[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def ts(s):
    h, r = divmod(s, 3600)
    m, s = divmod(r, 60)
    return ("%02d:%02d:%06.3f" % (h, m, s)).replace(".", ",")


def muestras(t):
    return "%dS" % round(t * 48000)


def titulo_shorts(tk):
    """Respaldo para un guion sin caption.shorts: las oraciones del caption de TikTok que caben en el título (nunca una
    palabra a medias), y #Shorts."""
    if not tk:
        return ""
    lim, titulo = SHORTS_TITULO - 9, ""
    for o in re.split(r"(?<=[.?!])\s+", tk.splitlines()[0].strip()):
        if len((titulo + " " + o).strip()) > lim:
            break
        titulo = (titulo + " " + o).strip()
    if not titulo:
        titulo = tk.splitlines()[0][:lim].rsplit(" ", 1)[0]
    return titulo + " #Shorts"


def escribir_caption(ruta, cap, redes, dur):
    """caption.md: una sección por plataforma (PLATAFORMAS). Un guion anterior a los cuatro captions toma el de TikTok
    para Instagram y Shorts."""
    tk = (cap.get("tiktok") or "").strip()
    txt = {"tiktok": tk, "instagram": (cap.get("instagram") or tk).strip(), "facebook": (cap.get("facebook") or tk).strip(),
           "shorts": (cap.get("shorts") or titulo_shorts(tk)).strip()}
    partes = ["# Texto para publicar", "",
              "Un solo video para las cuatro apps: **video.mp4** (9:16). Para el feed de Facebook e Instagram, "
              "**video_4x5.mp4**. Miniatura: una de las portada_*.png (lo importante queda en el 3:4 central, que es lo "
              "que muestran las cuadrículas de perfil).", ""]
    for k, nombre in PLATAFORMAS:
        partes += ["## " + nombre]
        if k == "shorts":
            partes += ["Título (primera línea, ≤ %d caracteres) y descripción." % SHORTS_TITULO]
            if dur > SHORTS_MAX_S:
                partes += ["**Este video dura %.0f s: pasa de los %d s de Shorts.** Súbelo como video normal o usa la "
                           "versión corta o media." % (dur, SHORTS_MAX_S)]
        partes += [txt[k], ""]
    partes += ["Sígueme: %s" % redes]
    open(ruta, "w", encoding="utf-8").write("\n".join(partes) + "\n")


def cmd_montar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    f45 = a.formato == "4:5"   # 1080×1350 para el feed: mismos tiempos y audio, otros clips; sin subtítulos ni portadas nuevos
    segs = os.path.join(trabajo, "segs_4x5" if f45 else "segs")
    os.makedirs(segs, exist_ok=True)
    clips = [os.path.join(trabajo, "clips_4x5" if f45 else "clips", "e%d.mp4" % e["n"]) for e in E["escenas"]]
    durs = [ffprobe_dur(c) for c in clips]  # lo que grabó Playwright (round(dur·fps)/fps)
    TR = E.get("transicion_s", 0.0) if len(clips) > 1 else 0.0
    # cierre en bucle: tras el cierre, el primer cuadro del gancho (barra de progreso en 0) durante BUCLE_S, con un
    # fundido: cuando TikTok repite el video, el reinicio no se nota
    if not getattr(a, "sin_bucle", False):
        cuadro, bucle = os.path.join(segs, "bucle.png"), os.path.join(segs, "bucle.mp4")
        fps = fps_de(clips[0])
        ff("-i", clips[0], "-frames:v", "1", cuadro)
        ff("-loop", "1", "-framerate", fps, "-i", cuadro, "-t", "%.2f" % BUCLE_S, "-r", fps,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", bucle)
        clips.append(bucle)
        durs.append(ffprobe_dur(bucle))
    n_esc = len(E["escenas"])
    offs, off = [], 0.0
    for k, d in enumerate(durs):  # desplazamientos exactos: cada escena entra TR s antes de que acabe la anterior
        offs.append(off)
        off += d - ((BUCLE_FUNDIDO if k + 1 == n_esc < len(durs) else TR) if k < len(durs) - 1 else 0.0)
    D = off
    # 1. solo video: las escenas encadenadas con un deslizamiento (xfade) de TR s
    video_solo = os.path.join(segs, "voz_video.mp4")
    if TR > 0:
        fc, prev = "", "[0:v]"
        for k in range(1, len(clips)):
            out = "[x%d]" % k
            es_bucle = k >= n_esc
            tr = TRANSICIONES["bucle"] if es_bucle else (E["escenas"][k].get("transicion") or TRANSICIONES["tarjeta"])
            if tr not in TRANSICIONES.values():
                return falla("V8 E%d: transición «%s» fuera del catálogo (%s)" % (E["escenas"][k]["n"], tr, ", ".join(sorted(set(TRANSICIONES.values())))))
            fc += "%s[%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f%s;" % (
                prev, k, tr, BUCLE_FUNDIDO if es_bucle else TR, offs[k], out)
            prev = out
        ff(*sum([["-i", c] for c in clips], []), "-filter_complex", fc.rstrip(";"), "-map", prev, "-an",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium", video_solo)
    else:
        lista = os.path.join(segs, "lista.txt")
        with open(lista, "w") as f:
            for c in clips:
                f.write("file '%s'\n" % c)
        ff("-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", "-an", video_solo)
    D = ffprobe_dur(video_solo)  # el audio se corta a lo que mide el video (los clips redondean a cuadros enteros)
    # 2. la voz en una sola pista, nivelada a VOZ_LUFS (llave determinista del ducking)
    voces = [os.path.join(trabajo, "audio", "voz_%d_r.mp3" % e["n"]) for e in E["escenas"]]
    fc = "".join("[%d:a]aresample=48000,aformat=channel_layouts=stereo,adelay=%s:all=1[v%d];" % (i, muestras(o), i)
                 for i, o in enumerate(offs[:len(voces)]))  # el bucle final no tiene voz
    fc += "".join("[v%d]" % i for i in range(len(voces))) + "amix=inputs=%d:duration=longest:normalize=0,apad=whole_dur=%.3f[vz]" % (len(voces), D)
    voz = os.path.join(segs, "voz.wav")
    ff(*sum([["-i", v] for v in voces], []), "-filter_complex", fc, "-map", "[vz]", "-ar", "48000", voz)
    gv = VOZ_LUFS - medir(voz)["input_i"]
    # 3. música en bucle
    pista = next(p for p in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
                 if p["id"] == st["musica"])
    fondo = os.path.join(segs, "musica.wav")
    musica_bucle(os.path.join(RAIZ, "design", "musica", pista["archivo"]), D, fondo)
    # 4. efectos del catálogo fijo, en su tiempo global
    cat = {x["id"]: x for x in leer(os.path.join(SFX_DIR, "catalogo.json"))["efectos"]}
    efectos = []
    for e, o in zip(E["escenas"], offs):
        for s in e.get("sfx") or []:
            t = o + s["t"]
            if t >= 0 and s["id"] in cat:
                efectos.append((t, s["id"]))
    efectos.sort()
    # 5. mezcla: voz + música con ducking (sidechain) + efectos
    entradas = ["-i", voz, "-i", fondo] + sum([["-i", os.path.join(SFX_DIR, cat[i]["archivo"])] for _, i in efectos], [])
    fc = ("[0:a]volume=%.2fdB,asplit=2[v][k];"
          "[1:a]aformat=channel_layouts=stereo,volume=%s,afade=t=in:st=0:d=1,afade=t=out:st=%.2f:d=2.5[m0];"
          "[m0][k]sidechaincompress=%s[m1];[m1]asplit=2[m][mdbg];" % (gv, MUSICA_VOLUMEN, D - 2.5, DUCK))
    for j, (t, i) in enumerate(efectos):
        fc += "[%d:a]aformat=channel_layouts=stereo,adelay=%s:all=1,volume=%ddB[f%d];" % (j + 2, muestras(t), cat[i]["ganancia_db"], j)
    fc += "[v][m]" + "".join("[f%d]" % j for j in range(len(efectos))) + "amix=inputs=%d:duration=first:normalize=0[a]" % (len(efectos) + 2)
    mezcla = os.path.join(segs, "mezcla.wav")
    ff(*entradas, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", mezcla,
       "-map", "[mdbg]", "-ar", "48000", os.path.join(segs, "musica_duck.wav"))
    # 6. loudnorm en dos pasadas (lineal: no deshace el ducking) y el video final
    m1 = medir(mezcla)
    sal = os.path.join(trabajo, "salida")
    video = os.path.join(sal, "video_4x5.mp4" if f45 else "video.mp4")
    v916 = os.path.join(sal, "video.mp4")
    if f45 and os.path.exists(v916) and abs(ffprobe_dur(v916) - D) < 0.1:
        # el feed lleva la pista ya masterizada del 9:16: el mismo sonido, sin otra pasada de AAC que mueva el pico
        ff("-i", video_solo, "-i", v916, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", video)
    else:
        ff("-i", video_solo, "-i", mezcla, "-filter_complex",
           "[1:a]loudnorm=I=%s:TP=-1.5:LRA=11:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:measured_thresh=%.2f:offset=%.2f:linear=true[a]"
           % (LUFS, m1["input_i"], m1["input_tp"], m1["input_lra"], m1["input_thresh"], m1["target_offset"]),
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", video)

    # V8
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate",
                                    "-of", "json", video], capture_output=True, text=True).stdout)["streams"]
    v = next((s for s in pr if s["codec_type"] == "video"), {})
    fallas = []
    esperado = (1080, 1350) if f45 else (1080, 1920)
    if (v.get("width"), v.get("height")) != esperado:
        fallas.append("V8 tamaño %sx%s (se espera %d×%d)" % (v.get("width"), v.get("height"), *esperado))
    if not any(s["codec_type"] == "audio" for s in pr):
        fallas.append("V8 sin audio")
    mf = medir(video)
    lufs, tp = mf["input_i"], mf["input_tp"]
    if abs(lufs - LUFS) > LUFS_TOL or tp > TP_MAX:
        fallas.append("V8 sonoridad %.1f LUFS / %.1f dBTP (se espera %.0f ±%.1f, ≤ %.0f)" % (lufs, tp, LUFS, LUFS_TOL, TP_MAX))

    if f45:  # subtítulos, caption y portadas son los del 9:16
        print("video 4:5 %.1f s · %.1f LUFS · %.1f dBTP → %s" % (ffprobe_dur(video), lufs, tp, rel(video)))
        for f in fallas:
            print("FALLA", f)
        return 1 if fallas else 0
    # subtítulos, caption y portada
    out, k = [], 1
    for e, off in zip(E["escenas"], offs):
        cur = []
        for p in e["palabras"] + [None]:
            if p is None or (cur and len(" ".join(x["text"] for x in cur)) + len(p["text"]) + 1 > 42):
                if cur:
                    out.append("%d\n%s --> %s\n%s\n" % (k, ts(off + cur[0]["start"]), ts(off + cur[-1]["end"] + 0.15),
                                                        " ".join(x["text"] for x in cur)))
                    k += 1
                cur = []
            if p is None:
                break
            cur.append(p)
            if p["text"][-1] in ".?:;":
                out.append("%d\n%s --> %s\n%s\n" % (k, ts(off + cur[0]["start"]), ts(off + cur[-1]["end"] + 0.15),
                                                    " ".join(x["text"] for x in cur)))
                k, cur = k + 1, []
    open(os.path.join(sal, "subtitulos.srt"), "w", encoding="utf-8").write("\n".join(out))
    redes = " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in REDES)
    escribir_caption(os.path.join(sal, "caption.md"), g["caption"], redes, ffprobe_dur(video))
    e1 = E["escenas"][0]
    if e1.get("tipo") in ("gancho", "golpe"):  # la portada se lee en silencio: cifra completa, línea entera y el visual completo
        fin_visual = max([x["t"] for x in e1.get("eventos") or [] if x["tipo"] in ("desborde_fin", "pareja_fin", "destacadas_fin", "pin_fin")] or [0])
        t_port = max(e1["T"]["pant"]["hasta"], (e1["T"]["linea"] or [{"start": 0}])[-1]["start"], fin_visual) + 0.35
    else:
        t_port = e1["T"]["tit"] + 1.2
    # portadas: cuadros limpios (sin subtítulos ni barra) que Playwright vuelve a dibujar en el segundo elegido: la del
    # gancho, las alternativas (pregunta del cierre, giro, adivina) y una de texto (video/portada.html) para el feed
    for f in glob.glob(os.path.join(sal, "portada_*.png")):
        os.remove(f)
    portadas = [{"nombre": "", "n": e1["n"], "t": round(min(t_port, e1["dur"] - 0.1), 2), "archivo": os.path.join(sal, "portada.png")}]
    for nombre, k, t in portadas_alternativas(E["escenas"]):
        portadas.append({"nombre": nombre, "n": E["escenas"][k]["n"], "t": round(t, 2), "archivo": os.path.join(sal, "portada_%s.png" % nombre)})
    if e1.get("tipo") == "gancho":
        portadas.append({"nombre": "texto", "pagina": "portada", "archivo": os.path.join(sal, "portada_texto.png")})
    escribir(os.path.join(segs, "portadas.json"), portadas)
    st = estado(trabajo)
    if subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, *(["--hilo", tarjetas_dir(trabajo, st)] if st.get("hilo") else []),
                       "--portadas", os.path.join(segs, "portadas.json")], cwd=RAIZ, stdout=subprocess.DEVNULL).returncode:
        return falla("las portadas no se dibujaron")
    print("video %.1f s · %.1f LUFS · %.1f dBTP · %d subtítulos · efectos %d · música %.2f con ducking → %s"
          % (ffprobe_dur(video), lufs, tp, k - 1, len(efectos), MUSICA_VOLUMEN, rel(video)))
    for f in fallas:
        print("FALLA", f)
    return 1 if fallas else 0


# ---------- revisar ----------
def cuadros_de(e):
    """Tiempos de los cuadros de revisión de una escena, según sus eventos (≤ 3)."""
    ev = e.get("eventos") or []
    primero = lambda tipo: next((x["t"] for x in ev if x["tipo"] == tipo), None)  # noqa: E731
    ultimo = lambda tipo: next((x["t"] for x in reversed(ev) if x["tipo"] == tipo), None)  # noqa: E731
    tipo = e.get("tipo")
    if tipo in ("gancho", "golpe", "definicion"):
        ts_ = [(primero("cifra_fin") or 0.5) + 0.15]
        fin_v = next((x["t"] for x in ev if x["tipo"] in ("desborde_fin", "pareja_fin", "destacadas_fin", "pin_fin")), None)
        if fin_v is not None:
            ts_.append(fin_v + 0.3)
    elif tipo == "adivina":
        ts_ = [(ultimo("opcion") or 1.0) + 0.5] + ([primero("pausa") + 0.5] if primero("pausa") is not None else []) + \
              [(primero("revelado") or e["dur"] * 0.6) + 0.4]
    elif tipo == "cierre":
        p_ = primero("pregunta") or e["dur"] * 0.5
        ts_ = [max(0.3, p_ - 0.3), p_ + 0.8]
    elif tipo == "ranking":
        ts_ = [(ultimo("item") or e["dur"] * 0.6) + 0.6]
    elif tipo == "tiempo":
        ts_ = [(primero("pildora") or ultimo("punto") or e["dur"] * 0.6) + 0.5]
    elif tipo == "escala":
        ts_ = [(primero("destacadas") or e["dur"] * 0.5) + 1.0]
    elif tipo in ("titular", "noticia", "foto"):   # /noticias y la foto de /historia: el titular entero, la cifra contada (o la fuente)
        ts_ = [(ultimo("titular") or 0.8) + 0.4] + ([primero("cifra") + 1.1] if primero("cifra") is not None else
                                                    [(primero("fuente") or e["dur"] * 0.6) + 0.5])
    elif tipo == "explica":
        pasos_ = [x["t"] for x in ev if x["tipo"] == "paso"]
        ts_ = ([pasos_[len(pasos_) // 2] + 0.5] if len(pasos_) > 2 else []) + [(pasos_[-1] if pasos_ else e["dur"] * 0.5) + 0.8]
    else:
        f, c = primero("foco"), ultimo("conteo_fin")
        ts_ = ([f + 0.6] if f is not None else []) + [(c + 0.3) if c is not None else e["dur"] * 0.5]
    rot = primero("acto_cuenta_fin")   # el rótulo de acto (historia): el año ya contado, el título entero
    if rot is not None:
        ts_.insert(0, rot + 0.3)
    ts_.append(e["dur"] - 0.35)
    return [min(t, e["dur"] - 0.35) for t in ts_]


def modelo_whisper():
    return os.environ.get("HILOS_WHISPER") or os.path.join(WHISPER_DIR, "ggml-small.bin")


_GENERO = {"uno": "un", "una": "un", "veintiuno": "veintiun", "veintiuna": "veintiun"}
_ROMANOS = {"I": 1, "V": 5, "X": 10}


def romano_a_entero(r):
    """«XIX» → 19 (solo I, V y X: los siglos y los ordinales que whisper escribe en romanos); None si no es válido."""
    total = 0
    for k, c in enumerate(r):
        v = _ROMANOS[c]
        total += -v if k + 1 < len(r) and _ROMANOS[r[k + 1]] > v else v
    return total if 0 < total < 40 else None


def clave_fonetica(texto):
    """Lo que suena igual en español, igual: sin espacios ni h muda, v → b, g ante e/i → j, ll → y, z y c ante e/i → s,
    qu → k, sin letras dobles ni s final. V11 no avisa cuando lo esperado y lo oído tienen la misma clave (Córdova y
    Córdoba, Brahva y brava, Monge y monje, «Centro Americana» y «centroamericana», «a la Gallo» y «al agallo»)."""
    t = re.sub(r"[^a-z]", "", texto.lower())
    t = re.sub(r"(?<![cs])h", "", t)
    t = t.replace("v", "b").replace("ll", "y").replace("qu", "k")
    t = re.sub(r"g(?=[ei])", "j", t)
    t = re.sub(r"c(?=[ei])", "s", t).replace("z", "s")
    t = re.sub(r"(.)\1+", r"\1", t)
    return re.sub(r"s$", "", t)


def tokens_escucha(texto, oido=False):
    """Palabras comparables: minúsculas, sin tildes ni puntuación, sin género en los numerales (una/uno → un,
    doscientas → doscientos). En lo oído, antes, el punto de miles de whisper («4.464», «12.878») se quita, la coma
    decimal («1,8») pasa a punto y los dígitos a palabras con numeros_es, igual que la locución."""
    t = texto or ""
    if oido:
        # whisper escribe en romanos los siglos y los ordinales («siglo XIX»): a dígitos, y luego a palabras
        t = re.sub(r"\b[IVX]{2,}\b", lambda m: str(romano_a_entero(m.group(0)) or m.group(0)), t)
        t = re.sub(r"(?<![\d.])\d{1,3}(?:\.\d{3})+(?![.,]?\d)", lambda m: m.group(0).replace(".", ""), t)
        t = re.sub(r"(?<=\d),(?=\d{1,2}(?!\d))", ".", t)
        NE.AVISOS.clear()
        try:
            t = NE.convertir(t)[1]
        except ValueError:
            pass
        NE.AVISOS.clear()
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [re.sub(r"cientas$", "cientos", _GENERO.get(w, w)) for w in re.findall(r"[a-z0-9]+", t)]


def comparar_escucha(segmentos, oido, omitir=None):
    """Compara la locución (los `segmentos` p/v/num de locucion.json) con lo que whisper oyó → (faltas, avisos,
    % de palabras distintas). Un tramo distinto que toca una palabra numérica es falta; el resto, aviso. `omitir`: una
    cita en otro idioma (whisper corre con -l es y no la transcribe): sus palabras no se comparan ni cuentan."""
    esperado, numerico = [], []
    for sg in segmentos:
        toks = tokens_escucha(sg["v"])
        esperado += toks
        numerico += [bool(sg.get("num"))] * len(toks)
    om, fuera = (tokens_escucha(omitir) if omitir else []), [False] * len(esperado)
    for k in (range(len(esperado) - len(om) + 1) if om else []):
        if esperado[k:k + len(om)] == om:
            fuera[k:k + len(om)] = [True] * len(om)
            break
    oidos = tokens_escucha(oido, oido=True)
    faltas, avisos, distintos = [], [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, esperado, oidos, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        resto = [i for i in range(i1, i2) if not fuera[i]]
        if (i2 > i1 and not resto) or (i1 == i2 and any(fuera[max(0, i1 - 1):i1 + 1])):
            continue   # el tramo es la cita en otro idioma (o lo que whisper oyó en su lugar): no se compara
        num = any(numerico[i] for i in resto)
        if not num and resto and j2 > j1 and clave_fonetica("".join(esperado[i] for i in resto)) == clave_fonetica("".join(oidos[j1:j2])):
            continue   # suena igual (homófonos, palabras juntas o separadas): whisper lo escribió distinto, la voz lo dijo bien
        distintos += max(len(resto), j2 - j1) if resto else 0
        msg = "esperaba «%s», oyó «%s»" % (" ".join(esperado[i] for i in resto) or "—", " ".join(oidos[j1:j2]) or "—")
        (faltas if num else avisos).append(msg)
    return faltas, avisos, round(100.0 * distintos / max(1, len(esperado) - sum(fuera)), 1)


def cmd_whisper(a):
    """Baja el modelo de whisper.cpp una sola vez (make whisper)."""
    destino = modelo_whisper()
    if os.path.exists(destino):
        print("ya está: %s (%.0f MB)" % (rel(destino), os.path.getsize(destino) / 1e6))
        return 0
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    print("bajando %s → %s" % (WHISPER_URL, rel(destino)))
    ultimo = [-1]

    def avance(bloques, tam, total):
        pct = int(100 * bloques * tam / total) if total > 0 else 0
        if pct // 10 != ultimo[0] // 10:
            ultimo[0] = pct
            print("  %d %%" % pct)
    urllib.request.urlretrieve(WHISPER_URL, destino + ".parte", avance)
    os.replace(destino + ".parte", destino)
    print("listo: %s (%.0f MB)" % (rel(destino), os.path.getsize(destino) / 1e6))
    return 0


def cmd_escuchar(a):
    """V11: transcribe cada voz con whisper.cpp (sin el guion) y coteja con la locución: Scribe, conectado al nodo TTS,
    alinea el prompt y no detecta una cifra mal dicha; esto sí. Sin whisper-cli o sin modelo, avisa y sale 0."""
    trabajo = os.path.abspath(a.trabajo)
    loc = leer(os.path.join(trabajo, "locucion.json"))
    modelo = os.path.abspath(a.modelo) if a.modelo else modelo_whisper()
    if not shutil.which("whisper-cli") or not os.path.exists(modelo):
        print("AVISO V11: sin whisper-cli o sin modelo (%s): la escucha se salta · brew install whisper-cpp · make whisper" % rel(modelo))
        return 0
    solo = {int(x) for x in a.solo.split(",")} if a.solo else None
    ruta = os.path.join(trabajo, "audio", "escucha.json")
    informe = leer(ruta) if os.path.exists(ruta) else {"escenas": {}}
    informe["modelo"] = os.path.basename(modelo)
    hilos = str(max(1, min(8, (os.cpu_count() or 2) // 2)))
    con_faltas = []
    for e in loc["escenas"]:
        n = e["n"]
        if solo and n not in solo:
            continue
        voz = os.path.join(trabajo, "audio", "voz_%d.mp3" % n)
        if not os.path.exists(voz):
            return falla("falta %s" % rel(voz))
        base = os.path.join(trabajo, "audio", "escucha_%d" % n)
        ff("-i", voz, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", base + ".wav")
        r = subprocess.run(["whisper-cli", "-m", modelo, "-l", "es", "-np", "-oj", "-of", base, "-t", hilos, "-f", base + ".wav"],
                           capture_output=True, text=True)
        if r.returncode or not os.path.exists(base + ".json"):
            return falla("whisper-cli falló en E%d: %s" % (n, (r.stderr or r.stdout).strip()[-300:]))
        oido = " ".join(x.get("text", "") for x in leer(base + ".json").get("transcription") or []).strip()
        faltas, avisos, pct = comparar_escucha(e.get("segmentos") or [{"v": e["voz"], "num": False}], oido, e.get("escucha_omitir"))
        informe["escenas"][str(n)] = {"oido": oido, "faltas": faltas, "avisos": avisos, "distinto_pct": pct}
        if faltas:
            con_faltas.append(n)
            for f in faltas:
                print("E%-2d FALLA V11: %s" % (n, f))
        else:
            print("E%-2d ok · %.0f %% de palabras distintas%s%s" % (n, pct, " · aviso: " + " · ".join(avisos) if avisos else "",
                                                               " · (cita en otro idioma: no se compara)" if e.get("escucha_omitir") else ""))
    escribir(ruta, informe)
    if con_faltas:
        return falla("V11: rehaz la voz de %s (una retoma por escena) o escúchala tú" % ", ".join("E%d" % n for n in con_faltas))
    return 0


def movimiento_de(clip, fps=QUIETUD_FPS):
    """Diferencia media de luma (0–255) entre cuadros consecutivos, muestreados a `fps` y a 270 px de ancho. La media
    sale del plano Y crudo de los cuadros de diferencia, no de signalstats: con el grano fijo de Noche, x264 retoca unos
    pocos píxeles en ±1 entre cuadros de una pantalla congelada y signalstats da YAVG de 1.5–7.7 en esos cuadros casi
    negros (la media real es < 0.001), así que V12 no veía la pantalla quieta. Con movimiento, las dos medidas coinciden."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", clip], capture_output=True, text=True)
    try:
        ancho, alto = (int(x) for x in r.stdout.strip().split(",")[:2])
    except ValueError:
        return []
    w, h = 270, max(2, 2 * round(270 * alto / ancho / 2))   # alto par: yuv420p
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostats", "-i", clip, "-vf",
                        "fps=%d,scale=%d:%d,tblend=all_mode=difference,format=yuv420p" % (fps, w, h), "-f", "rawvideo", "-"],
                       capture_output=True)
    n, b = w * h, r.stdout
    paso = n * 3 // 2   # cada cuadro yuv420p: el plano Y (n bytes) y luego U y V a un cuarto
    return [sum(b[i:i + n]) / n for i in range(0, len(b) - paso + 1, paso)]


def ventanas_quietas(vals, fps=QUIETUD_FPS, minimo=QUIETUD_S, umbral=QUIETUD_UMBRAL, saltar=TRANSICION):
    """[(inicio_s, dur_s)] de los tramos de ≥ `minimo` s en que ningún cuadro muestreado se mueve (YAVG < umbral);
    los primeros `saltar` s (la transición de entrada) no cuentan."""
    out, ini, k0 = [], None, int(round(saltar * fps))
    for k, v in enumerate(vals + [umbral]):   # centinela: cierra el último tramo
        if k >= k0 and v < umbral:
            ini = k if ini is None else ini
        elif ini is not None:
            if (k - ini) / fps >= minimo:
                out.append((round(ini / fps, 2), round((k - ini) / fps, 2)))
            ini = None
    return out


PRIMER_CUADRO_MIN = 0.015   # V15: fracción mínima de la zona de contenido con algo dibujado en el cuadro 0 del gancho


def llenado_primer_cuadro(clip, f45=False):
    """V15 (R12): fracción de píxeles de la zona de contenido (bajo la barra de arriba, sobre los subtítulos) que se
    distinguen del fondo en el cuadro 0: el primer cuadro es la miniatura del feed y el del bucle."""
    w, h = (108, 135) if f45 else (108, 192)
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-frames:v", "1", "-vf", "scale=%d:%d,format=gray" % (w, h),
                        "-f", "rawvideo", "-"], capture_output=True)
    px = r.stdout
    if len(px) < w * h:
        return None
    y0, y1 = (int(h * 0.12), int(h * 0.80)) if f45 else (int(h * 0.17), int(h * 0.71))
    zona = [px[y * w + x] for y in range(y0, y1) for x in range(int(w * 0.08), int(w * 0.81))]
    fondo = max(set(zona), key=zona.count)
    return sum(1 for v in zona if abs(v - fondo) > 24) / len(zona)


def cmd_revisar(a):
    trabajo = os.path.abspath(a.trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    f45 = a.formato == "4:5"
    suf, clips_dir, alto = ("_4x5", "clips_4x5", 338) if f45 else ("", "clips", 480)
    rev = os.path.join(trabajo, "revision")
    for f in glob.glob(os.path.join(rev, "c%s_*.png" % suf)):
        os.remove(f)
    k = 0
    for e in E:
        for t in cuadros_de(e):
            k += 1
            ff("-ss", "%.2f" % t, "-i", os.path.join(trabajo, clips_dir, "e%d.mp4" % e["n"]),
               "-frames:v", "1", os.path.join(rev, "c%s_%03d.png" % (suf, k)))
    cols = 3 * min(len(E), 4)
    filas = math.ceil(k / cols)
    out = os.path.join(rev, "contacto%s.png" % suf)
    # la zona segura (V13, video/comun.css) dibujada encima en 9:16: el rectángulo rojo es donde va el contenido
    # (recorte lateral, barra de arriba, fin antes de los subtítulos) y la esquina sombreada, la columna de íconos
    zona = "" if f45 else ("drawbox=x=57:y=215:w=966:h=1155:color=red@0.55:t=5,"
                           "drawbox=x=900:y=1070:w=180:h=850:color=red@0.18:t=fill,")
    ff("-framerate", "1", "-i", os.path.join(rev, "c%s_%%03d.png" % suf), "-vf",
       "%sscale=270:%d,tile=%dx%d:padding=6:color=white" % (zona, alto, cols, filas), "-frames:v", "1", out)
    print("hoja de contacto (%d cuadros: cifra completa · pico del foco · final de cada escena%s) → %s"
          % (k, "" if f45 else "; en rojo, la zona segura", rel(out)))
    # línea de tiempo del video final: un cuadro cada 2 s, para verlo «de corrido» (transiciones incluidas)
    video = os.path.join(trabajo, "salida", "video%s.mp4" % suf)
    if os.path.exists(video):
        n = math.ceil(ffprobe_dur(video) / 2)
        lt = os.path.join(rev, "linea_tiempo%s.png" % suf)
        ff("-i", video, "-vf", "fps=0.5,scale=270:%d,tile=8x%d:padding=4:color=white" % (alto, math.ceil(n / 8)), "-frames:v", "1", lt)
        print("línea de tiempo (%d cuadros, uno cada 2 s) → %s" % (n, rel(lt)))
    # V12 quietud real: tramos en que nada se mueve en pantalla (la deriva cuenta como movimiento)
    quietud, avisos = {"fps": QUIETUD_FPS, "umbral": QUIETUD_UMBRAL, "minimo_s": QUIETUD_S, "escenas": {}}, []
    for e in E:
        vals = movimiento_de(os.path.join(trabajo, clips_dir, "e%d.mp4" % e["n"]))
        tramos = ventanas_quietas(vals)
        quietud["escenas"][str(e["n"])] = {"movimiento": [round(v, 3) for v in vals], "quieto": tramos}
        avisos += ["V12 quietud: E%d %.1f s sin movimiento desde %.1f s" % (e["n"], d, t0) for t0, d in tramos]
    escribir(os.path.join(rev, "quietud%s.json" % suf), quietud)
    # V15 primer cuadro (R12): el cuadro 0 del gancho ya cuenta algo (miniatura del feed y vuelta del bucle)
    lleno = llenado_primer_cuadro(os.path.join(trabajo, clips_dir, "e1.mp4"), f45)
    if lleno is not None and lleno < PRIMER_CUADRO_MIN:
        avisos.append("V15 primer cuadro: el cuadro 0 del gancho está casi vacío (%.1f %% dibujado): la cifra o el visual "
                      "van desde el primer cuadro" % (100 * lleno))
    for x in avisos:
        print("AVISO " + x)
    if avisos and getattr(a, "estricto", False):
        return falla("V12: %d tramo(s) quietos" % len(avisos))
    return 0


def fps_de(clip):
    """r_frame_rate del clip («30/1»), tal como lo aceptan -framerate y -r."""
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", clip], capture_output=True, text=True).stdout.strip() or "30/1"


def portadas_alternativas(escenas):
    """[(nombre, índice de escena, segundo)] de las portadas además de la del gancho: «cierre» (la frase final, remate o
    pregunta, ya en pantalla) y «giro» (la escena que entra con slideup, con su cifra ya contada)."""
    out = []
    ec = escenas[-1]
    if ec.get("tipo") == "cierre" and (ec.get("T") or {}).get("preg") is not None:
        out.append(("cierre", len(escenas) - 1, min(ec["T"]["preg"] + 0.8, ec["dur"] - 0.1)))
    kg = next((k for k, e in enumerate(escenas) if e.get("transicion") == "slideup"), None)
    if kg is not None:
        eg, ev = escenas[kg], escenas[kg].get("eventos") or []
        fines = [x["t"] for x in ev if x["tipo"] in ("conteo_fin", "cifra_fin")]
        t = max(fines) + 0.3 if fines else eg["dur"] / 2
        out.append(("giro", kg, min(t, eg["dur"] - 0.1)))
    ka = next((k for k, e in enumerate(escenas) if e.get("tipo") == "adivina"), None)
    if ka is not None and (escenas[ka].get("T") or {}).get("opciones"):
        ea = escenas[ka]
        out.append(("adivina", ka, min(ea["T"]["opciones"][-1]["start"] + 0.6, ea["T"]["revelado"] - 0.1, ea["dur"] - 0.1)))
    return out


# ---------- entregar ----------
def resumen_ganchos(trabajo):
    """Para la entrega: los candidatos (familia, visual, pantalla), el elegido, el segundo (versión B) y los puntajes de
    la selección; None si el video no pasó por la fase de ganchos."""
    ruta = os.path.join(trabajo, "ganchos.json")
    if not os.path.exists(ruta):
        return None
    G = leer(ruta)
    sel = leer(os.path.join(trabajo, "seleccion.json")) if os.path.exists(os.path.join(trabajo, "seleccion.json")) else {}
    return {"elegido": G.get("elegido"), "segundo": G.get("segundo"),
            "candidatos": [{"id": c.get("id"), "familia": c.get("familia"), "visual": c.get("visual") or "cifra",
                            "pantalla": c.get("pantalla")} for c in G.get("candidatos") or []],
            "puntajes": sel.get("puntajes"),
            "version_b": os.path.exists(os.path.join(trabajo, "salida", "video_b.mp4"))}


def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))
    loc = leer(os.path.join(trabajo, "locucion.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, st["hilo"], "video"))
    if not os.path.exists(os.path.join(trabajo, "salida", "video_4x5.mp4")):
        return falla("falta salida/video_4x5.mp4: graba, monta y revisa también --formato 4:5 (el feed de Facebook e "
                     "Instagram) antes de entregar")
    os.makedirs(destino, exist_ok=True)
    for f in ("video.mp4", "subtitulos.srt", "caption.md", "portada.png"):
        shutil.copy2(os.path.join(trabajo, "salida", f), os.path.join(destino, f))
    for f in glob.glob(os.path.join(destino, "portada_*.png")):
        os.remove(f)
    for f in glob.glob(os.path.join(trabajo, "salida", "portada_*.png")):
        shutil.copy2(f, os.path.join(destino, os.path.basename(f)))
    for f in ("salida/video_4x5.mp4", "revision/contacto_4x5.png", "salida/video_b.mp4"):  # el 4:5 del feed y la versión B
        if os.path.exists(os.path.join(trabajo, f)):
            shutil.copy2(os.path.join(trabajo, f), os.path.join(destino, os.path.basename(f)))
    shutil.copy2(os.path.join(trabajo, "revision", "contacto.png"), os.path.join(destino, "contacto.png"))
    hilo = leer(os.path.join(RAIZ, st["hilo"], "hilo.json"))
    critica, rc = None, os.path.join(trabajo, "critica.json")
    if os.path.exists(rc):
        c = leer(rc)
        critica = {"veredicto": c.get("veredicto"), "vuelta": c.get("vuelta"),
                   "puntajes": {k: (c.get("puntajes") or {}).get(k) for k in PUNTAJES}}
    else:
        print("AVISO sin critica.json: el video se entrega sin la revisión del crítico")
    g1 = g["escenas"][0]
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    creditos = leer(ruta_cred)["total"] if os.path.exists(ruta_cred) else loc["caracteres"]
    entrega = {
        "id": "%s-%s" % (hilo.get("fecha"), st["slug"]), "slug": st["slug"], "hilo": st["hilo"],
        "paleta": st["paleta"], "duracion": st["duracion"], "duracion_s": round(ffprobe_dur(os.path.join(destino, "video.mp4")), 1),
        "n_escenas": len(loc["escenas"]) - 1, "musica": st["musica"], "voz": loc["voz"], "velocidad": VELOCIDAD,
        "creditos_voz": creditos, "contexto_superior": g["contexto_superior"],
        "gancho": {"familia": g1.get("familia"), "visual": g1.get("visual") or "cifra", "pantalla": g1.get("pantalla"),
                   "linea": g1.get("linea"), **({"formula": g1["formula"]} if g1.get("formula") else {})},
        "ganchos": resumen_ganchos(trabajo),
        "promesa": g.get("promesa"), "critica": critica,
        "escenas": [{"n": e["n"], "tipo": e.get("tipo"), "tuit": e["tuit"], "plantilla": e["plantilla"], "enlace": e.get("enlace"),
                     "golpe": e.get("golpe"), "cinetico": e.get("cinetico"), "adivina": e.get("adivina"), "icono": e.get("icono"), "pantalla": e["pantalla"], "voz": e["voz"],
                     **({"animacion": s.get("animacion"), "mecanismo": (e.get("explica") or {}).get("mecanismo")}
                        if e.get("tipo") == "explica" else {}),
                     "dur": s["dur"]} for e, s in zip(loc["escenas"], E["escenas"])],
        "cierre": g["cierre"], "caption": g["caption"],
    }
    escribir(os.path.join(destino, "guion.json"), entrega)
    for aid in dict.fromkeys(x["animacion"] for x in entrega["escenas"] if x.get("animacion")):   # usos del catálogo
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "animaciones.py"), "--registrar", aid, "--video", st["slug"]],
                           capture_output=True, text=True)
        print(r.stdout.strip() if r.returncode == 0 else "AVISO no se sumó el uso de «%s» al catálogo: %s" % (aid, r.stdout.strip()))
    print("entregado en %s (%.1f s) · video.mp4 (TikTok, Reels, Shorts) + video_4x5.mp4 (feed) · caption.md con %d "
          "plataformas" % (rel(destino), entrega["duracion_s"], len(PLATAFORMAS)))
    if entrega["duracion_s"] > SHORTS_MAX_S:
        print("AVISO dura %.0f s: pasa de los %d s de YouTube Shorts (súbelo como video normal)" % (entrega["duracion_s"], SHORTS_MAX_S))
    return 0


def cmd_musica(a):
    cat = leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    usos = {}
    for v in (leer(vids)["videos"] if os.path.exists(vids) else []):
        n, f = usos.get(v.get("musica"), (0, ""))
        usos[v.get("musica")] = (n + 1, max(f, v.get("fecha", "")))
    for p in cat:
        n, f = usos.get(p["id"], (0, ""))
        print("%-13s %-10s %5.0f s · %d uso(s)%s · %s" % (p["id"], p["paleta"], p["duracion_s"], n,
                                                      " (último %s)" % f if f else "", p["ambiente"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("preparar")
    p.add_argument("hilo")
    p.add_argument("--duracion", default=DURACION_DEFECTO)
    p.add_argument("--musica")
    p.add_argument("--trabajo")
    p.add_argument("--permitir-borrador", action="store_true", help="solo para el fixture")
    p.add_argument("--sin-rotacion", action="store_true", help="pruebas: sin bloquear las familias y visuales recientes (R9)")
    p = sub.add_parser("ganchos", help="ganchos.json: --check de los candidatos o --usar el elegido como escena 1")
    p.add_argument("trabajo")
    x = p.add_mutually_exclusive_group(required=True)
    x.add_argument("--check", action="store_true")
    x.add_argument("--usar", nargs="?", const="", help="id del ganador (sin id: el de seleccion.json)")
    p.add_argument("--segundo", help="id del segundo lugar (versión B); sin él, el de seleccion.json")
    p = sub.add_parser("guion")
    p.add_argument("trabajo")
    p.add_argument("--check", action="store_true", required=True)
    p = sub.add_parser("narracion", help="mide la narración de corrido (guion.narracion) antes de repartirla en escenas (V17–V18)")
    p.add_argument("trabajo")
    p.add_argument("--check", action="store_true")
    sub.add_parser("oyente", help="el digesto del oyente ingenuo: la narración de corrido y luego voz y pantalla por escena").add_argument("trabajo")
    p = sub.add_parser("variante", help="versión B del gancho (el segundo lugar): solo la voz de la escena 1")
    p.add_argument("trabajo")
    p.add_argument("--cerrar", action="store_true", help="copia variante_b/salida/video.mp4 → salida/video_b.mp4")
    p = sub.add_parser("voz", help="JSON con la voz y el prompt de cada nodo TTS")
    p.add_argument("trabajo")
    p.add_argument("--pendientes", action="store_true", help="solo las escenas sin audio o cuya voz cambió desde la última descarga (retomas)")
    p.add_argument("--sueltas", action="store_true", help="con voz de corrido: las escenas pendientes como nodos propios (sin regrabar la secuencia)")
    p.add_argument("--solo", help="escenas, p. ej. 2,5")
    for nombre in ("voz-falsa", "tiempos"):
        sub.add_parser(nombre).add_argument("trabajo")
    p = sub.add_parser("partir", help="corta la voz de una secuencia (audio/voz_sec_K.mp3 + Scribe) en sus escenas")
    p.add_argument("trabajo")
    p.add_argument("--secuencia", type=int, help="solo esa (por defecto todas)")
    p = sub.add_parser("revisar")
    p.add_argument("trabajo")
    p.add_argument("--formato", choices=("9:16", "4:5"), default="9:16")
    p.add_argument("--estricto", action="store_true", help="un tramo quieto (V12) es fallo, no aviso")
    p = sub.add_parser("escuchar", help="V11: whisper.cpp transcribe la voz sin el guion y coteja las cifras")
    p.add_argument("trabajo")
    p.add_argument("--solo", help="escenas, p. ej. 2,5")
    p.add_argument("--modelo", help="modelo ggml (por defecto el de make whisper o HILOS_WHISPER)")
    sub.add_parser("whisper", help="baja el modelo ggml-small de whisper.cpp una sola vez")
    p = sub.add_parser("montar")
    p.add_argument("trabajo")
    p.add_argument("--sin-bucle", action="store_true", help="sin el primer cuadro del gancho al final")
    p.add_argument("--formato", choices=("9:16", "4:5"), default="9:16", help="4:5 = 1080×1350 para el feed (clips_4x5/ → salida/video_4x5.mp4)")
    p = sub.add_parser("descargar")
    p.add_argument("trabajo")
    x = p.add_mutually_exclusive_group(required=True)
    x.add_argument("--estado", nargs="+", help="JSON guardado de creative_get_flow_run_status (uno o varios)")
    x.add_argument("--voz")
    x.add_argument("--palabras")
    p = sub.add_parser("grabar")
    p.add_argument("trabajo")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--solo")
    p.add_argument("--formato", choices=("9:16", "4:5"), default="9:16", help="4:5 = 1080×1350 para el feed (clips_4x5/)")
    p.add_argument("--paralelo", type=int, default=0, help="escenas a la vez (0 = automático: min(4, núcleos/4)); 1 = en serie")
    sub.add_parser("musica")
    p = sub.add_parser("entregar")
    p.add_argument("trabajo")
    p.add_argument("--salida")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    if a.cmd == "ganchos" and a.check:
        a.usar = None
    return {"preparar": cmd_preparar, "ganchos": cmd_ganchos, "guion": cmd_guion, "narracion": cmd_narracion, "oyente": cmd_oyente, "variante": cmd_variante, "voz": cmd_voz, "descargar": cmd_descargar,
            "voz-falsa": cmd_voz_falsa, "partir": cmd_partir, "tiempos": cmd_tiempos, "grabar": cmd_grabar, "montar": cmd_montar,
            "revisar": cmd_revisar, "entregar": cmd_entregar, "musica": cmd_musica, "escuchar": cmd_escuchar,
            "whisper": cmd_whisper}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
