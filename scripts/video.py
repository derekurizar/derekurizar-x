#!/usr/bin/env python3
"""/video: un hilo entregado → video vertical 1080×1920 narrado (TikTok / Reels / Facebook).

La sesión principal coordina (el guion lo orquesta el Workflow `video`); este script hace todo lo determinista y
los gates V1–V10 (referencias/flujo-video.md). La voz y Scribe salen del MCP de ElevenLabs; la música viene SOLO
del catálogo fijo design/musica/catalogo.json y los efectos SOLO de design/sfx/catalogo.json (/video nunca genera
música ni efectos).

Subcomandos (TRABAJO = sesiones/<slug>/video):
  preparar <hilo|ultimo> [--duracion corto|medio|largo] [--musica ID] [--trabajo DIR] [--permitir-borrador]
        crea TRABAJO, elige la música y escribe digesto.md para el guionista (también lo imprime); medio por defecto
  guion TRABAJO --check        gate V1–V5 + V9 (estructura de retención) sobre guion.json v2 → locucion.json
  voz TRABAJO                  imprime JSON con la voz y el texto de cada nodo TTS
  descargar TRABAJO --estado ESTADO.json [...]   el JSON guardado de creative_get_flow_run_status (voz y Scribe) →
        audio/voz_N.mp3 (por el prompt), palabras_N.json (por el id de generación) y creditos.json (créditos cobrados)
  descargar TRABAJO --voz URLS.json | --palabras URLS.json   respaldo: {"<n>": "<url>"} → voz_N.mp3 | palabras_N.json
  voz-falsa TRABAJO            tono por palabra + tiempos sintéticos (fixture, 0 créditos)
  tiempos TRABAJO              atempo 1.1, alineación por palabra (V6), eventos y efectos por escena, V10 → escenas.json
  grabar TRABAJO [--fps 30] [--solo 1,3] [--formato 4:5]   clips por escena (Playwright) + V7; 4:5 = 1080×1350 para el feed en clips_4x5/
  montar TRABAJO [--sin-bucle]   voz + música con ducking + efectos + loudnorm en 2 pasadas (V8), cierre en bucle (el primer
        cuadro del gancho al final, con fundido), subtitulos.srt, caption.md, portada.png y portada_pregunta/giro.png
  revisar TRABAJO [--formato 4:5]   revision/contacto.png (cifra completa · pico del foco · final de cada escena) y linea_tiempo.png
  entregar TRABAJO [--salida DIR]   copia a <hilo>/video/ (o DIR) con guion.json de entrega
  musica                       lista el catálogo fijo con cuántas veces y cuándo se usó cada pista

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
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

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402

VOZ = {"voice_id": "8mBRP99B2Ng2QwsJMFQl", "nombre": "El Faraon 4", "modelo": "eleven_multilingual_v2", "idioma": "es"}
REDES = [{"red": "tiktok", "nombre": "TikTok", "handle": "@derekurizargt"},
         {"red": "instagram", "nombre": "Instagram", "handle": "@derekurizargt"},
         {"red": "x", "nombre": "X", "handle": "@DerekUrizar"}]
VELOCIDAD = 1.1      # la voz se acelera con atempo (sin cambiar el tono); los tiempos de Scribe se dividen igual
CPS = 15.5           # caracteres de voz por segundo ya acelerada (medido en la prueba del hilo de crimen)
COLA = 0.7           # aire tras la última palabra de cada escena
COLA_CIERRE = 2.8    # «Sígueme en» se queda en pantalla tras la pregunta final
PREFIJO = "En Guatemala"   # sin dos puntos (2026-10-20): con «:» la voz sonaba a titular sin verbo
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
FORMULAS = ("cifra", "contradiccion", "pregunta", "resultado")
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
PUNTAJES = ("gancho", "bucle", "ritmo", "escala_humana", "pago", "cierre")   # critica.json (W10 lo coteja con video.js)
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
ICONOS_DIR = os.path.join(RAIZ, "design", "iconos")   # biblioteca FIJA de iconos (scripts/iconos.py --importar, K3)
ICONO_TIPOS = ("gancho", "golpe", "definicion")        # escenas que admiten `icono: "<id>"` (≤ 1, acento sobre la cifra)


def animaciones_catalogo():
    """{id: entrada} de video/animaciones/catalogo.json (vacío si aún no hay biblioteca)."""
    ruta = os.path.join(ANIMACIONES_DIR, "catalogo.json")
    return {a["id"]: a for a in leer(ruta).get("animaciones") or []} if os.path.exists(ruta) else {}


def explica_mal_armada(e, catalogo):
    """V1/V9 de una escena explica: animación del catálogo o `brief` para una nueva, `titulo` corto y 2–6 `pasos`."""
    out = []
    anim, brief = e.get("animacion"), (e.get("brief") or "").strip()
    if anim and anim not in catalogo:
        out.append("animación «%s» no está en video/animaciones/catalogo.json (usa una del digesto o deja `animacion: null` con "
                   "un `brief`)" % anim)
    if not anim and not BRIEF_CARACTERES[0] <= len(brief) <= BRIEF_CARACTERES[1]:
        out.append("una animación nueva necesita `brief` de %d–%d caracteres (qué muestra y cómo se mueve)" % BRIEF_CARACTERES)
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
    p = leer(os.path.join(RAIZ, "design", "tokens.json"))["paletas"][paleta]
    # resaltado del subtítulo activo: a3 de fondo con a1 de texto si se lee bien; si no, ink sobre bg invertido
    if contraste(p["a3"], p["a1"]) >= 4.5:
        rbg, rink = p["a3"], p["a1"]
    else:
        rbg, rink = p["ink"], p["bg"]
    return {"bg": p["bg"], "ink": p["ink"], "a1": p["a1"], "a2": p["a2"], "a3": p["a3"],
            "resalte_bg": rbg, "resalte_ink": rink,
            "pregunta": p["a3"] if contraste(p["a3"], p["bg"]) >= 3 else p["ink"],
            "acento": p["a1"] if contraste(p["a1"], p["bg"]) >= 3 else p["ink"]}  # la cifra grande del gancho/golpe


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


def puntos_de(datos):
    """[(etiqueta, valor, sub, destacado)] de una tarjeta antes-despues (2 puntos) o linea (la serie destacada o la
    primera; si tiene más de TIEMPO_PUNTOS, los equiespaciados con el primero y el último): la escena tiempo."""
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
            idx = [idx[round(j * (len(idx) - 1) / (TIEMPO_PUNTOS - 1))] for j in range(TIEMPO_PUNTOS)]
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
    t1 = next((x for x in tarjetas if x["n"] == 1), None)
    prefijo = bool(t1) and "guatemala" not in t1["titular"].lower()
    n_max = 1 + dur["tarjetas"][1] + dur["golpes"][1]
    caracteres = int((dur["s"] - COLA * n_max - COLA_CIERRE) * CPS)
    sugeridas = sugerir_tarjetas(hilo["tuits"], tarjetas, dur)
    st = {"hilo": rel(hilo_dir), "slug": hilo["slug"], "fecha_hilo": hilo.get("fecha"), "paleta": hilo["paleta"],
          "duracion": a.duracion, "objetivo_s": dur["s"], "musica": musica["id"], "prefijo": prefijo,
          "tarjetas": tarjetas, "sugeridas": sugeridas}
    escribir(os.path.join(trabajo, "video.json"), st)

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
           "- Animaciones ya hechas para la escena `explica` (reutiliza antes de pedir una nueva): " +
           (" · ".join("%s (%s; %d–%d pasos)" % (k, v.get("descripcion", ""), *(v.get("pasos") or EXPLICA_PASOS))
                       for k, v in animaciones_catalogo().items()) or "ninguna"),
           "- «En Guatemala» al inicio de la voz del gancho: %s (lo pone el script si tu texto no dice «Guatemala»; no lo escribas; "
           "tu voz sigue la frase: «Nacen casi 168 bebés al día…» → «En Guatemala nacen casi 168 bebés al día…»)."
           % ("SÍ" if prefijo else "no"),
           "- Música: %s (%s)" % (musica["id"], musica.get("ambiente", "")),
           "", "## Estructura (la comprueba el gate V9)",
           "1. Escena 1 = **gancho**: `formula` cifra | contradiccion | pregunta | resultado; `pantalla` (una cifra o ≤ %d palabras, "
           "≤ %d caracteres) y `linea` (≤ %d palabras, ≤ %d caracteres) deben contar el gancho **en silencio**: cifra/resultado → la "
           "cifra en pantalla; pregunta → termina en «?»; contradiccion → una cifra en pantalla o línea. La pantalla puede ser "
           "titular; la **voz no**: la oración que dice la pantalla lleva verbo conjugado, declarado en `verbo` (gancho y golpes): "
           "«Casi 168 al día» en pantalla → «Nacen casi 168 bebés al día de madres de 10 a 19 años» en la voz (`verbo`: «nacen»)."
           % (PANTALLA_PALABRAS, PANTALLA_CARACTERES, LINEA_PALABRAS, LINEA_CARACTERES),
           "2. Escena 2 = la **tarjeta T1**, sin enlace. Luego tarjetas y golpes en el orden del arco.",
           "3. Desde la escena 3, `enlace` pero | por_eso | y, y la voz EMPIEZA con ese conector (pero / sin embargo / aunque / "
           "solo que / en cambio / aun así · por eso / así que / entonces / el resultado / de ahí que / la consecuencia · y / además / "
           "también / encima / más aún). «y» como máximo en un tercio de los enlaces; nunca «y luego».",
           "4. Cada tarjeta lleva `golpe` (≤ %d palabras, ≤ %d caracteres): el re-gancho que va arriba, en lenguaje llano, con la "
           "cifra si cabe; nunca el titular de la tarjeta." % (GOLPE_PALABRAS, GOLPE_CARACTERES),
           "5. Las escenas `golpe` (texto a pantalla completa) llevan `pantalla` + `linea` + `verbo`; nunca dos seguidas ni en la escena 2; "
           "sirven para traducir la cifra anterior a escala humana, pagar la promesa o re-ganchar a mitad.",
           "6. `promesa`: {texto (10–80 caracteres, LITERAL en la voz de la escena `en` = 1 o 2), en, pago (escena del último tercio "
           "que cierra exactamente esa brecha)}.",
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
           "del fenómeno (por qué o cómo pasa: cómo se forma una cola, por qué la sequía da hambre), no los datos. `animacion` (id de "
           "las ya hechas) o `null` con `brief` (%d–%d caracteres: qué muestra y cómo se mueve; la escribe el animador), `titulo` "
           "(≤ %d palabras), `pasos` (%d–%d, ≤ %d caracteres, sin cifras salvo con respaldo), `enlace` y `texto` que dice cada paso "
           "(entra cuando la voz lo dice). Cada afirmación causal es de conocimiento general o del hilo y no contradice `no_afirma` "
           "(«uno de los factores», nunca «la causa»)." % (*BRIEF_CARACTERES, TITULO_PALABRAS, *EXPLICA_PASOS, PASO_CARACTERES),
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


def con_prefijo(texto):
    """«Nacen casi 168…» → «En Guatemala nacen casi 168…»; una pregunta o exclamación va tras coma:
    «En Guatemala, ¿cuánto…?»."""
    if texto[:1] in "¿¡":
        return PREFIJO + ", " + texto[0] + texto[1].lower() + texto[2:]
    return PREFIJO + " " + texto[0].lower() + texto[1:]


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
            if a and (_coincide(r, b / a, 0.5 / a) or (b == 100 and _coincide(r, a, 0.5))):
                return True
        for m in re.finditer(NE.NUM, t):
            v = float(m.group().replace(",", ""))
            if _coincide(r, v, 0.5 * 10 ** -VM.decimales(v)):
                return True
    return False


def exentar_de_cada(texto, vals):
    """«A de cada B» deja de contar como números sueltos cuando B/A tiene respaldo en vals (o A lo tiene cuando
    B = 100): la escala humana («1 de cada 4», «77 de cada 100») se respalda por su `calculo`, no por A y B."""
    def de_cada(m):
        a, b = float(m.group(1)), float(m.group(2))
        if a and any(_coincide(x, b / a, 0.5 / a) or (b == 100 and _coincide(x, a, 0.5)) for x, f in vals):
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
    cierre = g.get("cierre") or {}
    for k in ("texto", "pregunta"):
        if not (cierre.get(k) or "").strip():
            f.append("V1 cierre sin «%s»" % k)
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
        if g1.get("formula") not in FORMULAS:
            f.append("V9 gancho: formula «%s» no es cifra|contradiccion|pregunta|resultado" % g1.get("formula"))
        cinetico(1, g1, "gancho")
        pant, lin = g1.get("pantalla") or "", g1.get("linea") or ""
        tiene_cifra = lambda s: bool(re.search(NE.NUM, s))  # noqa: E731
        if g1.get("formula") in ("cifra", "resultado") and not tiene_cifra(pant):
            f.append("V9 gancho (%s): la pantalla debe llevar la cifra" % g1["formula"])
        if g1.get("formula") == "pregunta" and not (pant.rstrip().endswith("?") or lin.rstrip().endswith("?")):
            f.append("V9 gancho (pregunta): pantalla o linea deben terminar en «?»")
        if g1.get("formula") == "contradiccion" and not (tiene_cifra(pant) or tiene_cifra(lin)):
            f.append("V9 gancho (contradiccion): pantalla o linea deben llevar una cifra")
    # V9: escena 2 = T1
    if len(escenas) < 2 or escenas[1].get("tipo") != "tarjeta" or escenas[1].get("tuit") != 1:
        f.append("V9 la escena 2 debe ser la tarjeta T1 (el gancho se paga con la primera tarjeta)")
    elif escenas[1].get("enlace"):
        f.append("V9 escena 2: la primera tarjeta no lleva enlace")
    # V9: enlaces, golpes y escenas golpe
    n_y, n_enl = 0, 0
    ejemplos = {"pero": "«Pero …», «Sin embargo …»", "por_eso": "«Por eso …», «Así que …»", "y": "«Y …», «Además …»"}
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        if i >= 3 and tipo in CON_TUIT + ESCENAS_TEXTO + ("explica",):
            enl = e.get("enlace")
            if not enl:
                f.append("V9 escena %d: falta enlace (pero|por_eso|y)" % i)
            elif enl not in ENLACES:
                f.append("V9 escena %d: enlace «%s» no es pero|por_eso|y" % (i, enl))
            else:
                n_enl += 1
                n_y += enl == "y"
                if not RE_ENLACE[enl].match(sin_pausas(e.get("texto") or "").strip()):
                    f.append("V9 escena %d: la voz no empieza con un conector de tipo «%s» (p. ej. %s): «%s…»"
                             % (i, enl, ejemplos[enl], (e.get("texto") or "")[:40]))
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
            for motivo in explica_mal_armada(e, cat_anim):
                f.append("V9 escena %d (explica): %s" % (i, motivo))
        if tipo in ESCENAS_TEXTO and i >= 2 and escenas[i - 2].get("tipo") in ESCENAS_TEXTO:
            f.append("V9 escena %d: dos golpes seguidos (golpe, definición y adivina son escenas de texto: entre dos va una tarjeta)" % i)
    if n_enl and n_y > n_enl // 3:
        f.append("V9 %d enlaces «y» de %d; máximo %d (encadena con «pero» o «por eso»)" % (n_y, n_enl, n_enl // 3))
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
    fallas = validar_estructura(g, st, dur, tarjetas)

    # V5 reglas (antes de convertir: el prefijo cambia el texto del gancho)
    textos = [e.get("texto", "") for e in escenas] + [cierre.get("texto", "")]
    pantallas = [" ".join(filter(None, (e.get("golpe"), e.get("pantalla"), e.get("linea")))) for e in escenas]
    todo = " ".join(textos + pantallas + [" ".join(cierre.get("resumen") or []), cierre.get("pregunta", ""),
                                          json.dumps(g.get("caption") or {}, ensure_ascii=False)])
    if re.search(r"\ben suma\b", todo, re.I):
        fallas.append("V5 «en suma» está prohibido")
    if re.search(r"https?://|@\w", " ".join(textos + pantallas)):
        fallas.append("V5 la voz y la pantalla no llevan enlaces ni @handles")
    ct = (cierre.get("texto") or "").strip()
    if not ct.endswith("?"):
        fallas.append("V5 el cierre debe terminar en pregunta")
    if cierre.get("pregunta") and not ct.endswith(cierre["pregunta"].strip()):
        fallas.append("V5 cierre.texto debe terminar con cierre.pregunta")
    if cierre.get("pregunta") and ct.endswith(cierre["pregunta"].strip()):
        antes_preg = ct[:len(ct) - len(cierre["pregunta"].strip())].strip()
        NE.AVISOS.clear()
        try:
            s_antes = len(NE.convertir(sin_pausas(antes_preg))[1]) / CPS
        except ValueError:
            s_antes = len(antes_preg) / CPS
        NE.AVISOS.clear()
        if s_antes < CIERRE_ANTES_S:
            fallas.append("V9 cierre: %.1f s de voz antes de la pregunta (mínimo %.0f s): las conclusiones van en su propia "
                          "pantalla y necesitan tiempo para leerse" % (s_antes, CIERRE_ANTES_S))
    cierre_pantalla = " ".join([ct, " ".join(cierre.get("resumen") or []), cierre.get("pregunta", "")])
    if PROHIBIDO_CIERRE.search(cierre_pantalla):
        fallas.append("V5 el cierre no menciona fuentes, el hilo, la marca ni «sígueme» (va solo en pantalla)")
    for k in ("tiktok", "facebook"):
        if not ((g.get("caption") or {}).get(k) or "").strip():
            fallas.append("V5 falta caption.%s" % k)

    # V2, V3, V4 y ritmo por escena (escenas + cierre)
    valores, titulares, cifras = valores_respaldo(st["hilo"])
    loc, avisos, n_pausas = [], [], 0
    for i, e in enumerate(escenas + [{"tipo": "cierre", "tuit": None, "texto": ct}], 1):
        tipo = e.get("tipo") if e.get("tipo") in TIPOS else "cierre"
        texto = e.get("texto", "")
        prefijado = False
        if i == 1 and st.get("prefijo") and "guatemala" not in texto.lower():
            texto, prefijado = con_prefijo(texto), True
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
        largo = len(voz) - (len(PREFIJO) + 1 if prefijado else 0)
        if not CARACTERES[tipo][0] <= largo <= CARACTERES[tipo][1]:
            fallas.append("V4 escena %d (%s): %d caracteres de voz (rango %d–%d)" % (i, tipo, largo, *CARACTERES[tipo]))
        if tipo == "gancho":   # el gancho en 3 segundos: una oración corta, la promesa corta o en T1
            voz_sin = re.sub(r"^%s,?\s*" % re.escape(PREFIJO), "", voz) if prefijado else voz
            oraciones = [o for o in re.split(r"(?<=[.?!…])\s+", voz_sin.strip()) if o]
            o1 = oraciones[0] if oraciones else voz_sin
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
        hueco, antes, despues = hueco_maximo(segs, voz) if tipo not in ("cierre", "explica") else (0.0, "", "")
        if hueco > RITMO_MAX_S:
            fallas.append("V9 escena %d: %.1f s sin evento entre «…%s» y «%s…» (máximo %.0f s): acorta o mueve la cifra"
                          % (i, hueco, antes, despues, RITMO_MAX_S))
        plantilla = tarjetas[e["tuit"]]["plantilla"] if tipo in CON_TUIT and e.get("tuit") in tarjetas else tipo
        loc.append({"n": i, "tipo": tipo, "tuit": e.get("tuit") if tipo in CON_TUIT else None, "plantilla": plantilla,
                    "enlace": e.get("enlace") if i >= 2 else None, "golpe": e.get("golpe") if tipo in CON_TUIT or tipo == "escala" else None,
                    "top": e.get("top", RANKING_TOP_DEFECTO) if tipo == "ranking" else None, "orden": e.get("orden") if tipo == "ranking" else None,
                    "escala": {"de_cada": e.get("de_cada"), "etiqueta": (e.get("etiqueta") or "").strip()} if tipo == "escala" else None,
                    "cinetico": cinetico_de(tipo, e),
                    "adivina": {"pregunta": (e.get("pregunta") or "").strip(), "opciones": [o.strip() for o in e.get("opciones") or []],
                                "correcta": e.get("correcta")} if tipo == "adivina" else None,
                    "explica": {"animacion": e.get("animacion"), "brief": (e.get("brief") or "").strip(),
                                "titulo": (e.get("titulo") or "").strip(),
                                "pasos": [str(x).strip() for x in e.get("pasos") or []]} if tipo == "explica" else None,
                    "formula": e.get("formula") if tipo == "gancho" else None,
                    "icono": e.get("icono") if tipo in ICONO_TIPOS else None,
                    "calculo": e.get("calculo"), "valor_calculo": valor_calculo,
                    "pantalla": pantalla, "voz": voz, "prompt": prompt, "segmentos": segs,
                    "estimado_s": round(len(voz) / CPS + (COLA_CIERRE if tipo == "cierre" else COLA), 2),
                    "hueco_max_s": round(hueco, 2)})
    for etiqueta, txt in (("resumen", " ".join(cierre.get("resumen") or [])),
                          ("caption", json.dumps(g.get("caption") or {}, ensure_ascii=False))):
        sin = VM.sueltos(txt, valores, titulares)
        if sin:
            fallas.append("V2 %s: números sin respaldo: %s" % (etiqueta, ", ".join(map(str, sin))))

    if n_pausas > PAUSAS_MAX_VIDEO:
        fallas.append("V9 %d pausas en el video (máximo %d: el exceso de <break> ensucia la voz)" % (n_pausas, PAUSAS_MAX_VIDEO))
    # V4 presupuesto
    chars = sum(len(x["voz"]) for x in loc)
    estimado = chars / CPS + COLA * (len(loc) - 1) + COLA_CIERRE
    lo, hi = dur["s"] * (1 - TOLERANCIA), dur["s"] * (1 + TOLERANCIA)
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
              "objetivo_s": dur["s"], "n_escenas": len(escenas), "promesa": g.get("promesa"), "escenas": loc})
    print("→ %s · V1–V5, V9 ok" % rel(os.path.join(trabajo, "locucion.json")))
    return 0


# ---------- voz ----------
def cmd_voz(a):
    loc = leer(os.path.join(a.trabajo, "locucion.json"))
    print(json.dumps({"voz": loc["voz"], "model_parameters": {"language_code": loc["voz"]["idioma"]},
                      "caracteres": loc["caracteres"],
                      "nodos": [{"n": e["n"], "prompt": e.get("prompt") or e["voz"]} for e in loc["escenas"]]},
                     ensure_ascii=False, indent=1))
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
    por_voz = {texto_llano(e["voz"]): e["n"] for e in loc["escenas"]}
    gens, trans, prompt_media = [], [], {}
    for f in archivos:
        d = leer(f)
        gens += d.get("generations") or []
        trans += d.get("transcripts") or []
        for m in d.get("media") or []:
            if m.get("generation_id") and m.get("prompt"):
                prompt_media[m["generation_id"]] = m["prompt"]

    def escena_por_prompt(p):
        """El MCP recorta `generations[].prompt` a 200 caracteres (`media[].prompt` viene entero): si no casa entero,
        vale como prefijo cuando solo una escena empieza así."""
        if not p:
            return None
        ll = texto_llano(p)
        if ll in por_voz:
            return por_voz[ll]
        if len(p) >= 200:
            hits = [n for v, n in por_voz.items() if v.startswith(ll)]
            if len(hits) == 1:
                return hits[0]
        return None
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    cred = leer(ruta_cred) if os.path.exists(ruta_cred) else {"generaciones": {}, "total": 0}
    escena_de_gen, voces, palabras = {}, {}, {}
    for g in gens:
        if g.get("modality") != "audio" or g.get("status") != "completed" or not g.get("content_url"):
            continue
        n = escena_por_prompt(prompt_media.get(g.get("id")))
        if n is None:
            n = escena_por_prompt(g.get("prompt"))
        if n is None:
            print("AVISO generación %s: su prompt no es la voz de ninguna escena" % g.get("id"))
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
    for n in sorted(voces):
        bajar_voz(trabajo, n, voces[n]["content_url"])
        c = (voces[n].get("price") or {}).get("credits")
        if c is not None:
            cred["generaciones"][voces[n].get("id")] = {"n": n, "creditos": round(c, 2)}
    for n in sorted(palabras):
        bajar_palabras(trabajo, n, palabras[n])
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


def cmd_voz_falsa(a):
    """Fixture: un tono corto por palabra (para que el ducking y los efectos se prueben) con la duración que tendría
    la voz, y palabras repartidas por longitud."""
    trabajo = os.path.abspath(a.trabajo)
    loc = leer(os.path.join(trabajo, "locucion.json"))
    cps_crudo = CPS / VELOCIDAD
    for e in loc["escenas"]:
        palabras_ = e["voz"].split()
        total = len(e["voz"]) / cps_crudo
        t, ws = 0.0, []
        for w in palabras_:
            d = (len(w) + 1) / cps_crudo
            ws.append({"text": w, "start": round(t, 3), "end": round(t + d * 0.85, 3)})
            t += d
        puerta = "+".join("between(t,%.3f,%.3f)" % (w["start"], w["end"]) for w in ws)
        ff("-f", "lavfi", "-i", "aevalsrc=exprs='0.28*sin(2*PI*165*t)*(%s)':s=44100:d=%.3f" % (puerta, total),
           "-c:a", "libmp3lame", "-b:a", "64k", os.path.join(trabajo, "audio", "voz_%d.mp3" % e["n"]))
        escribir(os.path.join(trabajo, "audio", "palabras_%d.json" % e["n"]), ws)
    print("voz falsa: %d escenas" % len(loc["escenas"]))
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
                  peros[0] if peros else None)
    escenas, avisos = [], []
    for e in loc["escenas"]:
        n, tipo = e["n"], e.get("tipo") or ("cierre" if e["plantilla"] == "cierre" else "tarjeta")
        src, dst = [os.path.join(trabajo, "audio", x % n) for x in ("voz_%d.mp3", "voz_%d_r.mp3")]
        ff("-i", src, "-af", "atempo=%s" % VELOCIDAD, "-c:a", "libmp3lame", "-b:a", "192k", dst)
        habladas = [dict(w, start=w["start"] / VELOCIDAD, end=w["end"] / VELOCIDAD)
                    for w in sin_etiquetas(leer(os.path.join(trabajo, "audio", "palabras_%d.json" % n)))]
        try:
            ps = alinear(e, habladas)
        except ValueError as ex:
            return falla("V6 %s · rehaz la voz de esa escena" % ex)
        cierre = tipo == "cierre"
        fin_voz = ps[-1]["end"]
        dur = round(ffprobe_dur(dst) + (COLA_CIERRE if cierre else COLA), 3)
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
             "icono": e.get("icono"), "dur": dur, "fin_voz": round(fin_voz, 3), "palabras": pal, "arriba": None}
        ev, sfx = [], []
        if cierre:
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
                      "nota": round(min(max(fin_vals + 0.4, fin_oracion), dur - 1.2), 3), "linea_fin": round(fin_voz - 1.0, 3), "foco": True}
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
                pts = puntos_de(dat)
                ma, mb = ini + 0.3, max(ini + 1.5, fin_voz - 0.8)
                puntos = []
                for k, (et, v, sub, hi) in enumerate(pts):   # el marcador recorre el riel; el valor salta cuando la voz lo dice
                    llega = ma + (mb - ma) * k / max(1, len(pts) - 1)
                    d = dicho_de(v)
                    an = T["anios"].get(et) if et.isdigit() else None
                    start = d[0] + 0.4 if d else (an[0] if an else llega)
                    puntos.append({"etiqueta": et, "valor": v, "sub": sub, "hi": hi, "start": round(start, 3),
                                   "dicho": [round(d[0] + 0.5, 3), round(d[1], 3)] if d else None})
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
        S["transicion"] = None if n == 1 else TRANSICIONES[
            "giro" if n == giro_n else "cierre" if tipo == "cierre" else "primera" if len(escenas) == 1 else
            "texto" if tipo in ("golpe", "definicion") else "adivina" if tipo == "adivina" else
            "completa" if tipo in PANTALLA_COMPLETA + ("explica",) else "tarjeta"]
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
        "cierre": {"resumen": g["cierre"]["resumen"], "pregunta": g["cierre"]["pregunta"]},
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
    hilo_dir = os.path.join(RAIZ, st["hilo"])
    args = ["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, "--hilo", hilo_dir,
            "--fps", str(a.fps), "--formato", a.formato]
    if a.solo:
        args += ["--solo", a.solo]
    if a.paralelo:
        args += ["--paralelo", str(a.paralelo)]
    if subprocess.run(args, cwd=RAIZ).returncode:
        return falla("la grabación falló")
    # V7: el último cuadro de cada tarjeta animada es idéntico a su render estático
    esc = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    htmls = [os.path.join(hilo_dir, "tuit_%d.html" % e["tuit"]) for e in esc if e["tuit"]]
    if subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_animar.js"), "--check", *htmls], cwd=RAIZ).returncode:
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
    cap = g["caption"]
    open(os.path.join(sal, "caption.md"), "w", encoding="utf-8").write(
        "# Texto para publicar\n\n## TikTok / Reels\n%s\n\n## Facebook\n%s\n\nSígueme: %s\n"
        % (cap["tiktok"].strip(), cap["facebook"].strip(), redes))
    e1 = E["escenas"][0]
    if e1.get("tipo") in ("gancho", "golpe"):  # la portada se lee en silencio: cifra completa y línea entera
        t_port = max(e1["T"]["pant"]["hasta"], (e1["T"]["linea"] or [{"start": 0}])[-1]["start"]) + 0.35
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
    if subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, "--hilo", os.path.join(RAIZ, st["hilo"]),
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
    elif tipo == "explica":
        pasos_ = [x["t"] for x in ev if x["tipo"] == "paso"]
        ts_ = ([pasos_[len(pasos_) // 2] + 0.5] if len(pasos_) > 2 else []) + [(pasos_[-1] if pasos_ else e["dur"] * 0.5) + 0.8]
    else:
        f, c = primero("foco"), ultimo("conteo_fin")
        ts_ = ([f + 0.6] if f is not None else []) + [(c + 0.3) if c is not None else e["dur"] * 0.5]
    ts_.append(e["dur"] - 0.35)
    return [min(t, e["dur"] - 0.35) for t in ts_]


def modelo_whisper():
    return os.environ.get("HILOS_WHISPER") or os.path.join(WHISPER_DIR, "ggml-small.bin")


_GENERO = {"uno": "un", "una": "un", "veintiuno": "veintiun", "veintiuna": "veintiun"}


def tokens_escucha(texto, oido=False):
    """Palabras comparables: minúsculas, sin tildes ni puntuación, sin género en los numerales (una/uno → un,
    doscientas → doscientos). En lo oído, antes, la coma decimal de whisper («1,8») pasa a punto y los dígitos a
    palabras con numeros_es, igual que la locución."""
    t = texto or ""
    if oido:
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


def comparar_escucha(segmentos, oido):
    """Compara la locución (los `segmentos` p/v/num de locucion.json) con lo que whisper oyó → (faltas, avisos,
    % de palabras distintas). Un tramo distinto que toca una palabra numérica es falta; el resto, aviso."""
    esperado, numerico = [], []
    for sg in segmentos:
        toks = tokens_escucha(sg["v"])
        esperado += toks
        numerico += [bool(sg.get("num"))] * len(toks)
    oidos = tokens_escucha(oido, oido=True)
    faltas, avisos, distintos = [], [], 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, esperado, oidos, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        distintos += max(i2 - i1, j2 - j1)
        msg = "esperaba «%s», oyó «%s»" % (" ".join(esperado[i1:i2]) or "—", " ".join(oidos[j1:j2]) or "—")
        (faltas if any(numerico[i1:i2]) else avisos).append(msg)
    return faltas, avisos, round(100.0 * distintos / max(1, len(esperado)), 1)


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
        faltas, avisos, pct = comparar_escucha(e.get("segmentos") or [{"v": e["voz"], "num": False}], oido)
        informe["escenas"][str(n)] = {"oido": oido, "faltas": faltas, "avisos": avisos, "distinto_pct": pct}
        if faltas:
            con_faltas.append(n)
            for f in faltas:
                print("E%-2d FALLA V11: %s" % (n, f))
        else:
            print("E%-2d ok · %.0f %% de palabras distintas%s" % (n, pct, " · aviso: " + " · ".join(avisos) if avisos else ""))
    escribir(ruta, informe)
    if con_faltas:
        return falla("V11: rehaz la voz de %s (una retoma por escena) o escúchala tú" % ", ".join("E%d" % n for n in con_faltas))
    return 0


def movimiento_de(clip, fps=QUIETUD_FPS):
    """Diferencia media de luma (0–255) entre cuadros consecutivos, muestreados a `fps` y a 270 px de ancho."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostats", "-i", clip, "-vf",
                        "fps=%d,scale=270:-1,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" % fps,
                        "-f", "null", "-"], capture_output=True, text=True)
    return [float(x) for x in re.findall(r"YAVG=([0-9.]+)", r.stdout)]


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
    ff("-framerate", "1", "-i", os.path.join(rev, "c%s_%%03d.png" % suf), "-vf",
       "scale=270:%d,tile=%dx%d:padding=6:color=white" % (alto, cols, filas), "-frames:v", "1", out)
    print("hoja de contacto (%d cuadros: cifra completa · pico del foco · final de cada escena) → %s" % (k, rel(out)))
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
    """[(nombre, índice de escena, segundo)] de las portadas además de la del gancho: «pregunta» (el cierre con la
    pregunta ya en pantalla) y «giro» (la escena que entra con slideup, con su cifra ya contada)."""
    out = []
    ec = escenas[-1]
    if ec.get("tipo") == "cierre" and (ec.get("T") or {}).get("preg") is not None:
        out.append(("pregunta", len(escenas) - 1, min(ec["T"]["preg"] + 0.8, ec["dur"] - 0.1)))
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
def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))
    loc = leer(os.path.join(trabajo, "locucion.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, st["hilo"], "video"))
    os.makedirs(destino, exist_ok=True)
    for f in ("video.mp4", "subtitulos.srt", "caption.md", "portada.png"):
        shutil.copy2(os.path.join(trabajo, "salida", f), os.path.join(destino, f))
    for f in glob.glob(os.path.join(destino, "portada_*.png")):
        os.remove(f)
    for f in glob.glob(os.path.join(trabajo, "salida", "portada_*.png")):
        shutil.copy2(f, os.path.join(destino, os.path.basename(f)))
    for f in ("salida/video_4x5.mp4", "revision/contacto_4x5.png"):  # la versión 4:5 para el feed, si se grabó
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
        "gancho": {"formula": g1.get("formula"), "pantalla": g1.get("pantalla"), "linea": g1.get("linea")},
        "promesa": g.get("promesa"), "critica": critica,
        "escenas": [{"n": e["n"], "tipo": e.get("tipo"), "tuit": e["tuit"], "plantilla": e["plantilla"], "enlace": e.get("enlace"),
                     "golpe": e.get("golpe"), "cinetico": e.get("cinetico"), "adivina": e.get("adivina"), "icono": e.get("icono"), "pantalla": e["pantalla"], "voz": e["voz"],
                     "dur": s["dur"]} for e, s in zip(loc["escenas"], E["escenas"])],
        "cierre": g["cierre"], "caption": g["caption"],
    }
    escribir(os.path.join(destino, "guion.json"), entrega)
    print("entregado en %s (%.1f s)" % (rel(destino), entrega["duracion_s"]))
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
    p = sub.add_parser("guion")
    p.add_argument("trabajo")
    p.add_argument("--check", action="store_true", required=True)
    for nombre in ("voz", "voz-falsa", "tiempos"):
        sub.add_parser(nombre).add_argument("trabajo")
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
    return {"preparar": cmd_preparar, "guion": cmd_guion, "voz": cmd_voz, "descargar": cmd_descargar,
            "voz-falsa": cmd_voz_falsa, "tiempos": cmd_tiempos, "grabar": cmd_grabar, "montar": cmd_montar,
            "revisar": cmd_revisar, "entregar": cmd_entregar, "musica": cmd_musica, "escuchar": cmd_escuchar,
            "whisper": cmd_whisper}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
