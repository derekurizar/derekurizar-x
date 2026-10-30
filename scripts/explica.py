#!/usr/bin/env python3
"""/explica: un concepto, un proceso o una regla explicado en un video vertical 1080×1920 de ~2 min (TikTok / Reels /
Shorts) y 4:5, para que quien lo vea pueda explicárselo a otro.

Dramaturgia fija en tres actos: LA PREGUNTA (gancho, promesa y la idea equivocada que casi todos tienen) → EL MECANISMO
(definición, la cuenta paso a paso, la animación; el punto medio es el «ajá» y el giro, la otra cara del mecanismo) →
EN TU VIDA (el mecanismo con datos reales de Guatemala, la regla práctica y el cierre de consecuencia). Este script
hace lo propio del explicador: el estado del trabajo, el gate de las afirmaciones y las cifras verificadas (E2), la
calculadora de los ejemplos (los números ilustrativos los calcula el script, nunca un agente: E3), la base que respalda
la voz y el gate del guion (E1–E12). Escribe el MISMO trabajo que /video: arma en TRABAJO/base/ un «hilo base»
(hilo.json, datos.json con las cifras verificadas y las de los ejemplos `ej-cNN`, tarjetas tuit_N.html materializadas),
así que V1–V5, V9, F1–F8, los ganchos (R1–R12), los tiempos, la voz, la grabación, el montaje y la revisión salen de
scripts/video.py, con la escena propia `cuenta` (video/cuenta.html, la pizarra) enchufada por sus extensiones
(CONSTRUCTORES, TRANSICION_DE, SIN_HUECO, POST_CONSTRUCTORES). Guía: referencias/flujo-explica.md.

Subcomandos (TRABAJO = sesiones/explica-<slug>/):
  preparar <tema> [--duracion corto|medio|largo] [--slug S] [--trabajo DIR] [--paleta P] [--musica ID] [--fixture]
        crea TRABAJO y video.json (--fixture copia la maqueta de sesiones/_fixture_explica: el interés compuesto)
  leer URL [--buscar CITA] [--otra-vez]   → historia.py leer (HTML, PDF o Wayback; lista cerrada de fuentes)
  encuadre TRABAJO --check     E1: pregunta, intuición, mecanismo y su frase, ejemplos, leyenda, glosario, anclas, ejes
  afirmaciones TRABAJO --check [--eje E]   E2 sobre verificacion_<eje>.json (afirmaciones y cifras con cita guardada)
  consolidar TRABAJO           verificaciones → explicacion.json + base/ (hilo.json, datos.json) + la paleta, y corre
        ejemplos (los modelos del encuadre → ejemplos.json y las cifras ej-cNN en base/datos.json)
  ejemplos TRABAJO             solo la calculadora: imprime cada ejemplo y su tabla (y la vuelve a escribir)
  digesto TRABAJO --para investigador|verificador --eje E | gancho | guionista | critico | oyente
  ganchos TRABAJO --check | --usar [ID] [--segundo ID]   → video.py ganchos con las familias y visuales de /explica
  narracion TRABAJO [--check]  mide guion.narracion antes de repartirla (E9: palabras, conectores, «según»)
  tarjetas TRABAJO             las escenas con gráfico → base/tuit_N.html (materializar.py, R1–R6)
  guion TRABAJO --check        E3–E12 + video.py guion (V1–V5, V9, F1–F8) → locucion.json; última línea RETORNO {...}
  probar | aplicar TRABAJO --cambios JSON|ARCHIVO   el arreglo del crítico en una copia | en el TRABAJO (como /historia)
  tiempos TRABAJO              video.py tiempos con el constructor de la cuenta, el rótulo de acto y el chip «Ejemplo»
  entregar TRABAJO [--salida DIR]   → explicaciones/<fecha>-<slug>/ (video, 4:5, caption, fuentes.md, ejemplos.md)
  voz | voz-falsa | descargar | partir | escuchar | grabar | montar | revisar TRABAJO [...]   → video.py

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import contextlib
import datetime
import glob
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import historia as HI  # noqa: E402
import noticias as NT  # noqa: E402
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402
import video as VD  # noqa: E402

# ---- formato (decisión del usuario, 2026-10-29: ~2 min por defecto, 90–150 s) ----
# duración → (clave en VD.DURACIONES, objetivo s, tolerancia, palabras de narración (aviso), palabras (falla))
# (≈ 145 palabras por minuto de voz; las colas entre escenas suman ≈ 10 s en medio)
FORMATOS = {"corto": ("explica-corto", 60, 0.25, (125, 150), (105, 175)),
            "medio": ("explica", 120, 0.25, (250, 300), (210, 345)),
            "largo": ("explica-largo", 165, 0.10, (350, 410), (300, 450))}
DURACION_DEFECTO, DURACION_MAX_S = "medio", 180
for _d, (_k, _s, _tol, _p, _pd) in FORMATOS.items():
    VD.DURACIONES[_k] = {"s": _s, "tarjetas": (0, {"corto": 3, "medio": 5, "largo": 7}[_d]),
                         "golpes": (0, {"corto": 4, "medio": 7, "largo": 9}[_d]), "tol": _tol}
CLAVE_DE = {v[0]: k for k, v in FORMATOS.items()}
TIPOS_PROPIOS = ("cuenta",)
TIPOS = VD.TIPOS + TIPOS_PROPIOS   # W13: espejo literal en .claude/workflows/explica.js
CARACTERES = {"cuenta": (30, 260)}
# en un explicador una tarjeta, un golpe o una animación sostienen un tramo más largo de narración que en /video
CARACTERES_VIDEO_EN_EXPLICA = {"tarjeta": (40, 260), "explica": (40, 260), "golpe": (20, 130), "definicion": (30, 200),
                               "escala": (30, 200), "tiempo": (40, 260)}
# los tres actos del explicador (los nombres del encuadre; la estructura es la de /historia)
ACTOS = (("pregunta", 1), ("mecanismo", 2), ("en_tu_vida", 3))
ESCENAS_MAX, SEGUIDAS_MAX, GIRO_ENTRE = 19, 3, (0.40, 0.75)
EXPLICA_MAX, CUENTAS_MAX = 2, 3
ROTULO_TIPOS = ("tarjeta", "golpe", "definicion", "explica", "cuenta", "escala", "mapa", "ranking", "tiempo")
ROTULO_ETIQUETA, ROTULO_TITULO = 12, 4
# la cuenta (la pizarra): 2–5 renglones «a op b = r», cada celda ≤ 12 caracteres, nota ≤ 14, etiqueta del resaltado ≤ 3 palabras
RENGLONES, CELDA_CARACTERES, NOTA_CARACTERES, ETIQUETA_PALABRAS, ETIQUETA_CARACTERES = (2, 5), 12, 14, 3, 26
OPS = {"+": "+", "-": "−", "−": "−", "×": "×", "x": "×", "*": "×", "÷": "÷", "/": "÷"}
# ganchos del explicador: el concepto se juega en la vida del espectador (sin lugar ni ranking: no es un mapa)
FAMILIAS = ("contraste", "paradoja", "pregunta", "tu", "escala", "resultado")
VISUALES = ("cifra", "llenado", "pareja", "figuras")
VISUALES_DE = {f: tuple(v for v in VD.VISUALES_DE[f] if v in VISUALES) for f in FAMILIAS}
ROTACION_FAMILIAS = 2
PUNTAJES = ("gancho", "claridad", "intuicion", "flujo", "precision", "cierre")   # critica.json en modo explica (W13)
REGLA_DE = {"gancho": "E-C1", "claridad": "E-C2", "intuicion": "E-C3", "flujo": "E-C4", "precision": "E-C5", "cierre": "E-C6"}
# la calculadora de los ejemplos: un catálogo CERRADO de modelos; cada uno con sus parámetros (un id de cifra verificada o
# un número ilustrativo) y sus salidas, que van a base/datos.json como cifras ej-cNN (W13: claves espejo en explica.js)
MODELOS = {
    "compuesto": ("capital, tasa (% por periodo), periodos [, capitalizacion: veces por periodo]",
                  "final, interes_total, interes_simple, interes_sobre_interes, pct_interes_sobre_interes, duplica_en, "
                  "duplicaciones, serie (saldo por periodo), interes_periodo (serie), interes_sobre_interes_periodo (serie)"),
    "simple": ("capital, tasa, periodos", "interes_periodo, interes_total, final, serie"),
    "aporte_periodico": ("aporte, tasa, periodos", "final, aportado, interes, serie"),
    "regla72": ("tasa", "anios (72 ÷ tasa), exacto (ln 2 ÷ ln(1 + tasa))"),
    "tasa_real": ("nominal, inflacion", "real ((1 + i) ÷ (1 + π) − 1), aprox (i − π)"),
    "cuota": ("monto, tasa (% anual), meses", "cuota, total, intereses"),
    "porcentaje": ("base, pct", "valor"),
    "proporcion": ("parte, todo", "pct"),
}
PARAMETROS = {"compuesto": ("capital", "tasa", "periodos"), "simple": ("capital", "tasa", "periodos"),
              "aporte_periodico": ("aporte", "tasa", "periodos"), "regla72": ("tasa",), "tasa_real": ("nominal", "inflacion"),
              "cuota": ("monto", "tasa", "meses"), "porcentaje": ("base", "pct"), "proporcion": ("parte", "todo")}
EJEMPLOS_ILUSTRATIVOS_MAX = 4
LEYENDA_PAPELES = ("tenue", "ink", "acento")
SENSIBLES = ("financiero", "salud", "legal", "ninguno")
GLOSARIO_MAX, ANCLAS_MIN, EJES = 3, 1, (1, 3)
INTUICION_PALABRAS, MECANISMO_FRASE = 22, (30, 220)
# E4: lo ilustrativo se dice como ejemplo («supón», «imagina», «por ejemplo»…)
RE_SUPON = re.compile(r"\b(?:sup[oó]n\w*|supongamos|imagin\w+|por ejemplo|digamos|pongamos|en este ejemplo|un ejemplo|"
                      r"hagamos la cuenta|haz la cuenta)\b", re.I)
RE_GUATEMALA_FRASE = re.compile(r"\ben guatemala\b|\bguatemaltec\w*|\bel pa[ií]s\b", re.I)
# E10: un explicador no aconseja ni vende: ni órdenes de inversión ni nombres de bancos o productos
RE_CONSEJO = re.compile(
    r"\bdeber[ií]as\b|\bdebes (?:invertir|ahorrar|pedir|sacar|comprar|abrir|pagar)\b|\bte (?:recomiendo|aconsejo|conviene)\b|"
    r"\b(?:les|les) recomiendo\b|\brecomendamos\b|\binvierte en\b|\binvierta en\b|\bla mejor (?:opci[oó]n|inversi[oó]n|tarjeta|cuenta)\b|"
    r"\bbanrural\b|\bbanco industrial\b|\bbantrab\b|\bg&t\b|\bbam\b|\bpromerica\b|\bficohsa\b|\binterbanco\b|\bbac\b|"
    r"\bagromercantil\b|\bbanco azteca\b|\bcuscatl[aá]n\b|\bbinance\b|\bbitcoin\b", re.I)
RE_SALUD = re.compile(r"\b\d+\s*(?:mg|ml|miligramos|mililitros)\b|\btoma\w*\s+\d+\b|\bdiagn[oó]stic\w+\b", re.I)
# rótulo de cierre de un explicador
CIERRE_ROTULO = "Lo que te llevas"
# flujo (E9): mismos topes de /historia, con menos «según» (un explicador cita poco: la cuenta habla)
CONECTORES_MIN_POR_ACTO, SEGUN_MAX_VIDEO, SEGUN_MAX_ACTO = 2, 2, 1
SECUENCIA = HI.SECUENCIA
ESTADOS, PUBLICABLES = HI.ESTADOS, HI.PUBLICABLES
TIPOS_AFIRMACION = ("definicion", "regla", "proceso", "dato", "norma")
FIXTURE = os.path.join(RAIZ, "sesiones", "_fixture_explica")
SALIDA_ENTREGA = ("video.mp4", "video_4x5.mp4", "caption.md", "subtitulos.srt")
TRABAJO_ACTUAL, ORIGINALES = None, {}
E_ACTUAL = None   # explicacion.json del trabajo (afirmaciones, cifras, ejemplos)


def leer(p):
    return VD.leer(p)


def escribir(p, obj):
    VD.escribir(p, obj)


def falla(msg):
    return VD.falla(msg)


def encuadre(trabajo):
    ruta = os.path.join(trabajo, "encuadre.json")
    return leer(ruta) if os.path.exists(ruta) else {}


def plano(s):
    return VD._plano(s or "")


# ---------- registros anteriores (rotación de ganchos y cierres, C11, música, animaciones) ----------
def explicaciones_registradas(slug_actual=None):
    ruta = os.path.join(RAIZ, "memoria", "explicaciones.json")
    regs = (leer(ruta).get("explicaciones") or []) if os.path.exists(ruta) else []
    return sorted([h for h in regs if h.get("slug") != slug_actual], key=lambda h: (h.get("fecha", ""), h.get("id", "")))


def frases_explicaciones(slug_actual, n=VD.FRASES_USADAS_VIDEOS):
    regs = [h for h in explicaciones_registradas(slug_actual) if h.get("frases")][-n:]
    if not regs:
        return ["- (ninguna explicación anterior registrada)"]
    return ["- explicación **%s** · promesa: «%s» · gancho: «%s» · cierre (%s · %s): «%s» · aperturas: %s"
            % (h["slug"], h["frases"].get("promesa", ""), h["frases"].get("gancho", ""), h["frases"].get("cierre_tipo") or "remate",
               h["frases"].get("cierre_forma") or "", h["frases"].get("cierre") or "",
               " / ".join("«%s…»" % x for x in h["frases"].get("aperturas", []))) for h in reversed(regs)]


def recientes(slug_actual):
    fr = [h.get("frases") or {} for h in explicaciones_registradas(slug_actual)]
    return ({"familias": [x["familia"] for x in fr[-ROTACION_FAMILIAS:] if x.get("familia")],
             "visuales": [x["visual"] for x in fr[-1:] if x.get("visual")]},
            {"tipos": [x.get("cierre_tipo") or "remate" for x in fr[-1:]],
             "formas": [x.get("cierre_forma") for x in fr[-VD.ROTACION_CIERRES:] if x.get("cierre_forma")],
             "mecanismos": [x["cierre_mecanismo"] for x in fr[-1:] if x.get("cierre_mecanismo")]})


def animaciones_recientes(slug_actual):
    out = list(HI.animaciones_recientes(slug_actual))
    for h in explicaciones_registradas(slug_actual)[-VD.ROTACION_ANIMACIONES:]:
        out += [x for x in (h.get("frases") or {}).get("animaciones") or [] if x and x not in out]
    return out


def elegir_musica(paleta, forzada=None):
    """La pista de la paleta usada hace más tiempo (o nunca) entre videos, historias y explicaciones."""
    if forzada:
        return VD.elegir_musica(paleta, forzada)
    cat = [x for x in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"] if x["paleta"] == paleta]
    if not cat:
        raise ValueError("el catálogo no tiene música para la paleta «%s»" % paleta)
    usos = {}
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    regs = ((leer(vids).get("videos") or []) if os.path.exists(vids) else []) + HI.historias_registradas() + explicaciones_registradas()
    for v in regs:
        usos[v.get("musica")] = max(usos.get(v.get("musica"), ""), v.get("fecha", ""))
    return sorted(cat, key=lambda x: (usos.get(x["id"], ""), x["id"]))[0]


# ---------- preparar ----------
def cmd_preparar(a):
    slug = HI.slug_de(a.slug or a.tema)
    if not slug:
        print("el tema no da un slug (letras o números)", file=sys.stderr)
        return 2
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "explica-" + slug))
    for d in ("audio", "salida", "revision", "base"):
        os.makedirs(os.path.join(trabajo, d), exist_ok=True)
    previas = explicaciones_registradas(slug)
    pal = HI.paletas()
    paleta = a.paleta or next((p for p in pal if not previas or p != previas[-1].get("paleta")), pal[0])
    if paleta not in pal:
        print("--paleta: una de %s" % ", ".join(pal), file=sys.stderr)
        return 2
    try:
        pista = elegir_musica(paleta, a.musica)
    except ValueError as ex:
        return falla(str(ex))
    clave, objetivo = FORMATOS[a.duracion][0], FORMATOS[a.duracion][1]
    rec_g, rec_c = ({"familias": [], "visuales": []}, {"tipos": [], "formas": [], "mecanismos": []}) if a.fixture else recientes(slug)
    ruta = os.path.join(trabajo, "video.json")
    st = leer(ruta) if os.path.exists(ruta) else {}
    st.update({"tipo": "explica", "slug": slug, "tema": a.tema, "fecha": datetime.date.today().isoformat(),
               "hilo": VD.rel(os.path.join(trabajo, "base")), "paleta": paleta, "musica": pista["id"], "musica_forzada": a.musica,
               "duracion": clave, "objetivo_s": objetivo, "ganchos_recientes": rec_g, "cierres_recientes": rec_c,
               "animaciones_recientes": [] if a.fixture else animaciones_recientes(slug)})
    st.setdefault("tarjetas", [])
    escribir(ruta, st)
    if a.fixture:
        for f in ["encuadre.json", "ganchos.json", "seleccion.json", "guion.json"] + \
                [os.path.basename(x) for x in glob.glob(os.path.join(FIXTURE, "verificacion_*.json"))]:
            shutil.copy(os.path.join(FIXTURE, f), os.path.join(trabajo, f))
        print("maqueta: encuadre, verificaciones (fuentes de ejemplo ya guardadas), ganchos y guion → %s" % VD.rel(trabajo))
    if any(plano(h.get("tema")) == plano(a.tema) or h.get("slug") == slug for h in previas):
        print("AVISO este tema ya se explicó (memoria/explicaciones.json): explícalo solo con un ángulo nuevo")
    print("explica «%s» · %s (%d s) · paleta provisional %s (el editor elige la del tema) · música %s"
          % (a.tema, a.duracion, objetivo, paleta, pista["id"]))
    print(VD.rel(trabajo))
    return 0


# ---------- E1 encuadre ----------
def revisar_encuadre(enc):
    f = []
    for k in ("tema", "pregunta", "intuicion", "mecanismo_frase"):
        if not (enc.get(k) or "").strip():
            f.append("E1 falta «%s»" % k)
    if VD.palabras(enc.get("intuicion") or "") > INTUICION_PALABRAS:
        f.append("E1 «intuicion» de ≤ %d palabras: la idea equivocada en una oración, dicha con justicia" % INTUICION_PALABRAS)
    if not MECANISMO_FRASE[0] <= len(enc.get("mecanismo_frase") or "") <= MECANISMO_FRASE[1]:
        f.append("E1 «mecanismo_frase» de %d–%d caracteres: la oración que el oyente tiene que poder devolver" % MECANISMO_FRASE)
    if enc.get("mecanismo") not in VD.MECANISMOS_EXPLICA:
        f.append("E1 «mecanismo» es uno de %s (qué hace el fenómeno)" % "|".join(VD.MECANISMOS_EXPLICA))
    if enc.get("sensible") not in SENSIBLES:
        f.append("E1 «sensible»: %s" % "|".join(SENSIBLES))
    ley = enc.get("leyenda") or []
    if not 2 <= len(ley) <= 4 or any(not isinstance(x, dict) or not (x.get("concepto") or "").strip()
                                      or x.get("papel") not in LEYENDA_PAPELES for x in ley):
        f.append("E1 «leyenda»: 2–4 {concepto, papel: %s}, el código de color de TODO el video" % "|".join(LEYENDA_PAPELES))
    elif not any(x["papel"] == "acento" for x in ley):
        f.append("E1 «leyenda»: un concepto en acento (lo que el espectador tiene que ver crecer)")
    glo = enc.get("glosario") or []
    if len(glo) > GLOSARIO_MAX or any(not (x.get("termino") or "").strip() or not (x.get("definicion") or "").strip() for x in glo):
        f.append("E1 «glosario»: ≤ %d {termino, definicion en lenguaje llano}" % GLOSARIO_MAX)
    if len(enc.get("anclas") or []) < ANCLAS_MIN:
        f.append("E1 «anclas»: ≥ %d dato real de Guatemala que el acto 3 usa (concepto y fuente sugerida)" % ANCLAS_MIN)
    ejes = enc.get("ejes") or []
    if not EJES[0] <= len(ejes) <= EJES[1] or any(not re.fullmatch(r"[a-z]{2,4}", x.get("id") or "") for x in ejes):
        f.append("E1 «ejes»: %d–%d con id de 2–4 letras minúsculas (con, gt…)" % EJES)
    ilus = 0
    ids = set()
    for x in enc.get("ejemplos") or []:
        if x.get("id") in ids or not re.fullmatch(r"[a-z0-9_]{1,16}", x.get("id") or ""):
            f.append("E1 ejemplo «%s»: id único de minúsculas y números" % x.get("id"))
        ids.add(x.get("id"))
        if x.get("modelo") not in MODELOS:
            f.append("E1 ejemplo %s: modelo %s" % (x.get("id"), "|".join(MODELOS)))
            continue
        par = x.get("parametros") or {}
        for p in PARAMETROS[x["modelo"]]:
            if p not in par:
                f.append("E1 ejemplo %s: falta el parámetro «%s» (%s)" % (x.get("id"), p, MODELOS[x["modelo"]][0]))
        ilus += any(not (isinstance(v, dict) and v.get("cifra")) for v in par.values())
    if not enc.get("ejemplos"):
        f.append("E1 «ejemplos»: ≥ 1 modelo de la calculadora (%s)" % "|".join(MODELOS))
    if ilus > EJEMPLOS_ILUSTRATIVOS_MAX:
        f.append("E1 %d ejemplos ilustrativos (≤ %d): un ejemplo conductor, no una lista" % (ilus, EJEMPLOS_ILUSTRATIVOS_MAX))
    revs = enc.get("revelaciones") or []
    if not revs or not all(isinstance(r, str) and r.strip() for r in revs):
        f.append("E1 «revelaciones»: ≥ 1 (lo que el video paga y el gancho no adelanta; la promesa paga una)")
    return f


def cmd_encuadre(a):
    trabajo = os.path.abspath(a.trabajo)
    f = revisar_encuadre(encuadre(trabajo))
    for x in f:
        print("FALLA", x)
    print("encuadre %s" % ("ok" if not f else "con %d falla(s)" % len(f)))
    return 1 if f else 0


# ---------- E2 afirmaciones y cifras ----------
def revisar_eje(v, propios=()):
    """E2 sobre verificacion_<eje>.json: afirmaciones (<eje>-aNN), cifras (<eje>-cNN) y citas (<eje>-qNN) con su fuente
    guardada y la cita literal dentro (historia.revisar_fuentes). Una afirmación o una cifra `confirmado` pide 2 grupos o
    una fuente oficial o académica; `una_fuente`, una válida sin contradicción. → (fallas, avisos)."""
    fallas, avisos = [], []
    eje = v.get("eje") or "?"
    if not (v.get("afirmaciones") or v.get("cifras")):
        fallas.append("E2 %s: sin afirmaciones ni cifras" % eje)
    for clase, pre in (("afirmaciones", "a"), ("cifras", "c"), ("citas", "q")):
        for x in v.get(clase) or []:
            xid, est = x.get("id") or "?", x.get("estado")
            if not re.fullmatch(r"%s-%s\d{2}" % (re.escape(eje), pre), xid):
                fallas.append("E2 %s: id «%s» (va %s-%s01…)" % (eje, xid, eje, pre))
            if est not in ESTADOS:
                fallas.append("E2 %s: estado %s" % (xid, " | ".join(ESTADOS)))
                continue
            if est == "no_confirmado":
                continue
            validas, _ = HI.revisar_fuentes(x, propios, fallas, avisos, xid)
            grupos, clases = {g for _, g, _ in validas}, {k for k, _, _ in validas}
            if est == "confirmado" and len(grupos) < 2 and not clases & {"oficial", "academica"}:
                fallas.append("E2 %s: confirmado pide 2 fuentes independientes o una oficial o académica" % xid)
            if est in ("una_fuente", "en_disputa") and not validas:
                fallas.append("E2 %s: %s pide ≥ 1 fuente válida" % (xid, est))
            if est == "en_disputa" and len((x.get("nota") or "").strip()) < 10:
                fallas.append("E2 %s: en_disputa lleva la nota con la diferencia (la voz la atribuye)" % xid)
            citas = " ".join(HI.plano(f.get("cita")) for _, _, f in validas)
            nums = [(round(float(m.group().replace(",", "")), 6), None) for m in HI.RE_NUMERO.finditer(citas)]
            if clase == "afirmaciones":
                if x.get("tipo") not in TIPOS_AFIRMACION:
                    fallas.append("E2 %s: tipo %s" % (xid, "|".join(TIPOS_AFIRMACION)))
                if not 10 <= len(x.get("texto") or "") <= HI.HECHO_CARACTERES:
                    fallas.append("E2 %s: texto de 10–%d caracteres" % (xid, HI.HECHO_CARACTERES))
                for tok, _, _ in HI.numeros_de(x.get("texto")):
                    if NT.sueltos(tok, nums):
                        fallas.append("E2 %s: el número «%s» del texto no está en sus citas" % (xid, tok))
            elif clase == "cifras":
                if not isinstance(x.get("valor"), (int, float)) or isinstance(x.get("valor"), bool):
                    fallas.append("E2 %s: valor numérico" % xid)
                    continue
                if not str(x.get("periodo") or x.get("anio") or "").strip():
                    fallas.append("E2 %s: «periodo» (el año o el mes del dato: la voz dice de cuándo es)" % xid)
                if NT.sueltos(x.get("texto") or "", [(round(float(x["valor"]), 6), VM.factor_unidad(x.get("unidad"))), (round(float(x["valor"]), 6), None)]):
                    fallas.append("E2 %s: «%s» no es su valor %s" % (xid, x.get("texto"), x["valor"]))
                elif NT.sueltos(x.get("texto") or "", nums):
                    fallas.append("E2 %s: ninguna cita trae el número «%s»" % (xid, x.get("texto")))
            else:
                frase = HI.plano(x.get("texto"))
                if not (x.get("autor") or "").strip():
                    fallas.append("E2 %s: la cita lleva autor (persona, ley o documento)" % xid)
                if not any(frase and frase in (HI.texto_de(f.get("archivo")) or "") for f in x.get("fuentes") or []):
                    fallas.append("E2 %s: la frase no está literal en el texto guardado de ninguna de sus fuentes" % xid)
    return fallas, avisos


def cmd_afirmaciones(a):
    trabajo = os.path.abspath(a.trabajo)
    rutas = sorted(glob.glob(os.path.join(trabajo, "verificacion_%s.json" % (a.eje or "*"))))
    if not rutas:
        return falla("no hay verificacion_%s.json en %s" % (a.eje or "*", VD.rel(trabajo)))
    fallas, n = [], 0
    for r in rutas:
        v = leer(r)
        f, av = revisar_eje(v, encuadre(trabajo).get("dominios_propios") or ())
        fallas += f
        for x in av:
            print("AVISO", x)
        pub = sum(1 for k in ("afirmaciones", "cifras", "citas") for x in v.get(k) or [] if x.get("estado") in PUBLICABLES)
        n += pub
        print("%s · %d publicables · %d falla(s)" % (os.path.basename(r), pub, len(f)))
    for x in fallas:
        print("FALLA", x)
    print("E2 %s" % ("ok" if not fallas else "con %d falla(s)" % len(fallas)))
    return 1 if fallas else 0


# ---------- la calculadora de los ejemplos (E3) ----------
def redondo(x, d=2):
    return round(float(x), d)


def modelo(nombre, p):
    """→ [(salida, valor | None, serie | None, unidad, calculo)] de un modelo del catálogo con sus parámetros ya resueltos."""
    if nombre == "compuesto":
        C, r, n = p["capital"], p["tasa"] / 100.0, int(p["periodos"])
        m = int(p.get("capitalizacion") or 1)
        saldo = [C * (1 + r / m) ** (m * k) for k in range(n + 1)]
        final = saldo[-1]
        ip = [saldo[k] - saldo[k - 1] for k in range(1, n + 1)]
        iip = [x - C * r for x in ip]
        isimple = C * r * n
        iis = final - C - isimple
        dup = math.log(2) / math.log(1 + r / m) / m if r > 0 else None
        f = "%g × (1 + %g/100)^%d" % (C, p["tasa"], n) if m == 1 else "%g × (1 + %g/100/%d)^(%d×%d)" % (C, p["tasa"], m, m, n)
        return [("final", redondo(final), None, "quetzales", f),
                ("interes_total", redondo(final - C), None, "quetzales", f + " − %g" % C),
                ("interes_simple", redondo(isimple), None, "quetzales", "%g × %g/100 × %d" % (C, p["tasa"], n)),
                ("interes_sobre_interes", redondo(iis), None, "quetzales", "final − capital − interés simple"),
                ("pct_interes_sobre_interes", redondo(100 * iis / final, 1), None, "%", "interés sobre interés ÷ final × 100"),
                ("duplica_en", redondo(dup, 1) if dup else None, None, "periodos", "ln 2 ÷ ln(1 + tasa)"),
                ("duplicaciones", redondo(n / dup, 1) if dup else None, None, "veces", "periodos ÷ duplica_en"),
                ("serie", None, [{"periodo": str(k), "v": redondo(x)} for k, x in enumerate(saldo)], "quetzales", "saldo al final de cada periodo"),
                ("interes_periodo", None, [{"periodo": str(k), "v": redondo(x)} for k, x in enumerate(ip, 1)], "quetzales", "saldo_k − saldo_(k−1)"),
                ("interes_sobre_interes_periodo", None, [{"periodo": str(k), "v": redondo(x)} for k, x in enumerate(iip, 1)], "quetzales",
                 "interés del periodo − capital × tasa")]
    if nombre == "simple":
        C, r, n = p["capital"], p["tasa"] / 100.0, int(p["periodos"])
        return [("interes_periodo", redondo(C * r), None, "quetzales", "%g × %g/100" % (C, p["tasa"])),
                ("interes_total", redondo(C * r * n), None, "quetzales", "%g × %g/100 × %d" % (C, p["tasa"], n)),
                ("final", redondo(C * (1 + r * n)), None, "quetzales", "%g × (1 + %g/100 × %d)" % (C, p["tasa"], n)),
                ("serie", None, [{"periodo": str(k), "v": redondo(C * (1 + r * k))} for k in range(n + 1)], "quetzales", "capital + interés × k")]
    if nombre == "aporte_periodico":
        A, r, n = p["aporte"], p["tasa"] / 100.0, int(p["periodos"])
        saldo, s = [], 0.0
        for _ in range(n):
            s = s * (1 + r) + A
            saldo.append(s)
        return [("final", redondo(s), None, "quetzales", "%g × ((1 + %g/100)^%d − 1) ÷ (%g/100)" % (A, p["tasa"], n, p["tasa"])),
                ("aportado", redondo(A * n), None, "quetzales", "%g × %d" % (A, n)),
                ("interes", redondo(s - A * n), None, "quetzales", "final − aportado"),
                ("serie", None, [{"periodo": str(k), "v": redondo(x)} for k, x in enumerate(saldo, 1)], "quetzales", "saldo tras cada aporte")]
    if nombre == "regla72":
        r = p["tasa"]
        return [("anios", redondo(72.0 / r, 1), None, "años", "72 ÷ %g" % r),
                ("exacto", redondo(math.log(2) / math.log(1 + r / 100.0), 1), None, "años", "ln 2 ÷ ln(1 + %g/100)" % r)]
    if nombre == "tasa_real":
        i, pi = p["nominal"] / 100.0, p["inflacion"] / 100.0
        return [("real", redondo(100 * ((1 + i) / (1 + pi) - 1), 2), None, "%", "(1 + %g/100) ÷ (1 + %g/100) − 1" % (p["nominal"], p["inflacion"])),
                ("aprox", redondo(p["nominal"] - p["inflacion"], 2), None, "%", "%g − %g" % (p["nominal"], p["inflacion"]))]
    if nombre == "cuota":
        P, i, n = p["monto"], p["tasa"] / 100.0 / 12, int(p["meses"])
        c = P * i / (1 - (1 + i) ** -n) if i else P / n
        return [("cuota", redondo(c), None, "quetzales", "%g × i ÷ (1 − (1 + i)^−%d), i = %g/100/12" % (P, n, p["tasa"])),
                ("total", redondo(c * n), None, "quetzales", "cuota × %d" % n),
                ("intereses", redondo(c * n - P), None, "quetzales", "total − %g" % P)]
    if nombre == "porcentaje":
        return [("valor", redondo(p["base"] * p["pct"] / 100.0), None, "", "%g × %g/100" % (p["base"], p["pct"]))]
    if nombre == "proporcion":
        return [("pct", redondo(100.0 * p["parte"] / p["todo"], 1), None, "%", "%g ÷ %g × 100" % (p["parte"], p["todo"]))]
    raise ValueError(nombre)


def calcular_ejemplos(enc, cifras_reales):
    """Los ejemplos del encuadre → (ejemplos [{id, modelo, descripcion, ilustrativo, parametros, salidas}], cifras ej-cNN,
    fallas E3). Un parámetro {cifra: id} toma el valor de una cifra verificada; {valor, ilustrativo} o un número suelto es
    ilustrativo: el ejemplo entero lo es."""
    fallas, out, cifras, k = [], [], [], 0
    reales = {c["id"]: c for c in cifras_reales}
    for x in enc.get("ejemplos") or []:
        if x.get("modelo") not in MODELOS:
            continue
        par, ilus, usados = {}, False, {}
        for nombre, v in (x.get("parametros") or {}).items():
            if isinstance(v, dict) and v.get("cifra"):
                c = reales.get(v["cifra"])
                if not c:
                    fallas.append("E3 ejemplo %s: «%s» usa la cifra %s, que no está verificada (o no existe)" % (x["id"], nombre, v["cifra"]))
                    continue
                par[nombre], usados[nombre] = float(c["valor"]), {"cifra": c["id"], "valor": c["valor"]}
            else:
                val = v.get("valor") if isinstance(v, dict) else v
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    fallas.append("E3 ejemplo %s: «%s» es un número o {cifra: id}" % (x["id"], nombre))
                    continue
                par[nombre], usados[nombre], ilus = float(val), {"valor": val, "ilustrativo": True}, True
        if any(p not in par for p in PARAMETROS[x["modelo"]]):
            continue
        try:
            salidas = modelo(x["modelo"], par)
        except (ZeroDivisionError, ValueError, OverflowError) as ex:
            fallas.append("E3 ejemplo %s: el modelo %s no se puede calcular con esos parámetros (%s)" % (x["id"], x["modelo"], ex))
            continue
        regs = []
        for nombre, val, serie, unidad, calculo in salidas:
            if val is None and serie is None:
                continue
            k += 1
            cid = "ej-c%02d" % k
            c = {"id": cid, "concepto": "%s · %s (%s)" % (x["id"], nombre, x.get("descripcion") or x["modelo"]), "unidad": unidad,
                 "periodo": "", "veredicto": "verificada", "ilustrativo": ilus, "calculo": calculo, "ejemplo": x["id"], "salida": nombre}
            if val is not None:
                c["valor"] = val
            if serie is not None:
                c["serie"] = serie
                c.setdefault("valor", serie[-1]["v"])
            cifras.append(c)
            regs.append({"id": cid, "salida": nombre, "valor": c.get("valor"), "serie": serie, "unidad": unidad, "calculo": calculo})
        # los parámetros ilustrativos (el capital, la tasa, los años del ejemplo) también respaldan lo que se dice
        for nombre, u in usados.items():
            if u.get("ilustrativo"):
                k += 1
                cifras.append({"id": "ej-c%02d" % k, "concepto": "%s · parámetro %s" % (x["id"], nombre), "valor": u["valor"], "unidad": "",
                               "periodo": "", "veredicto": "verificada", "ilustrativo": True, "calculo": "dado", "ejemplo": x["id"],
                               "salida": "parametro_" + nombre})
        out.append({"id": x["id"], "modelo": x["modelo"], "descripcion": x.get("descripcion"), "ilustrativo": ilus,
                    "parametros": usados, "salidas": regs})
    return out, cifras, fallas


def lineas_ejemplos(ejs, serie_max=12):
    out = []
    for x in ejs:
        par = ", ".join("%s=%s%s" % (k, v["valor"], " (%s)" % v["cifra"] if v.get("cifra") else "") for k, v in x["parametros"].items())
        out.append("- %s · %s%s · %s · %s" % (x["id"], x["modelo"], " · ILUSTRATIVO (voz «supón/imagina», chip «Ejemplo»)" if x["ilustrativo"]
                                              else " · real (parámetros verificados)", par, x.get("descripcion") or ""))
        for s in x["salidas"]:
            if s["serie"]:
                pts = s["serie"]
                ver = pts if len(pts) <= serie_max else pts[:4] + [None] + pts[-4:]
                out.append("  - %s · %s (%s): %s" % (s["id"], s["salida"], s["unidad"], ", ".join(
                    "…" if p is None else "%s→%s" % (p["periodo"], VD.clave(p["v"])) for p in ver)))
                out.append("    (cada punto: %s.serie[k])" % s["id"])
            else:
                out.append("  - %s · %s = %s %s · %s" % (s["id"], s["salida"], VD.clave(s["valor"]), s["unidad"], s["calculo"]))
    return out


# ---------- consolidar ----------
def consolidar(trabajo):
    st = VD.estado(trabajo)
    enc = encuadre(trabajo)
    ejes = [leer(r) for r in sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))]
    X = {"tema": st.get("tema"), "slug": st["slug"], "pregunta": enc.get("pregunta"), "intuicion": enc.get("intuicion"),
         "mecanismo": enc.get("mecanismo"), "mecanismo_frase": enc.get("mecanismo_frase"), "leyenda": enc.get("leyenda") or [],
         "glosario": enc.get("glosario") or [], "personajes": enc.get("personajes") or [], "revelaciones": enc.get("revelaciones") or [],
         "no_afirma": enc.get("no_afirma") or [], "sensible": enc.get("sensible"),
         "afirmaciones": [], "cifras": [], "citas": [], "descartados": []}
    for v in ejes:
        for k in ("afirmaciones", "cifras", "citas"):
            for x in v.get(k) or []:
                (X[k] if x.get("estado") in PUBLICABLES else X["descartados"]).append(dict(x, eje=v.get("eje"), clase=k))
        X["descartados"] += [dict(x, eje=v.get("eje")) for x in v.get("descartados") or []]
    cifras = []
    for c in X["cifras"]:
        fuente = (c.get("fuentes") or [{}])[0]
        cifras.append({"id": c["id"], "concepto": c.get("concepto") or c.get("texto"), "valor": c["valor"], "unidad": c.get("unidad") or "",
                       "periodo": str(c.get("periodo") or c.get("anio") or ""), "veredicto": "verificada", "url": fuente.get("url"),
                       "fuente": fuente.get("medio") or NT.dominio(fuente.get("url") or ""), "ilustrativo": False})
    for x in X["afirmaciones"] + X["citas"]:
        for k, (tok, val, despues) in enumerate(HI.numeros_de(x.get("texto")), 1):
            cifras.append({"id": "%s-n%d" % (x["id"], k), "concepto": x.get("texto"), "valor": val, "unidad": HI.unidad_de(despues),
                           "periodo": "", "veredicto": "verificada", "ilustrativo": False})
    ejs, ej_cifras, fallas = calcular_ejemplos(enc, [c for c in cifras if not c["id"].endswith(tuple("-n%d" % i for i in range(1, 30)))])
    X["ejemplos"] = ejs
    escribir(os.path.join(trabajo, "explicacion.json"), X)
    escribir(os.path.join(trabajo, "ejemplos.json"), {"ejemplos": ejs})
    base = os.path.join(trabajo, "base")
    os.makedirs(base, exist_ok=True)
    paleta = enc.get("paleta") if enc.get("paleta") in HI.paletas() else st["paleta"]
    hilo_b = leer(os.path.join(base, "hilo.json")) if os.path.exists(os.path.join(base, "hilo.json")) else {}
    hilo_b.update({"slug": st["slug"], "fecha": st.get("fecha"), "tema": st.get("tema") or enc.get("tema", ""),
                   "tesis": enc.get("mecanismo_frase") or enc.get("pregunta") or "", "paleta": paleta, "estado": "listo",
                   "modo": "explica", "no_afirma": X["no_afirma"]})
    hilo_b.setdefault("tuits", [])
    escribir(os.path.join(base, "hilo.json"), hilo_b)
    escribir(os.path.join(base, "datos.json"), {"slug": st["slug"], "fecha": st.get("fecha"), "cifras": cifras + ej_cifras})
    if paleta != st["paleta"]:
        st["paleta"] = paleta
        st["musica"] = elegir_musica(paleta, st.get("musica_forzada"))["id"]
        escribir(os.path.join(trabajo, "video.json"), st)
    return X, fallas


def cmd_consolidar(a):
    trabajo = os.path.abspath(a.trabajo)
    f = revisar_encuadre(encuadre(trabajo))
    if f:
        for x in f:
            print("FALLA", x)
        return falla("el encuadre no pasa E1 (explica.py encuadre %s --check)" % VD.rel(trabajo))
    X, f = consolidar(trabajo)
    for x in X["afirmaciones"]:
        print("%-9s %-11s %-10s %s" % (x["id"], x["estado"], x.get("tipo"), x.get("texto")))
    for c in X["cifras"]:
        print("%-9s %-11s %s %s (%s) · %s" % (c["id"], c["estado"], c["valor"], c.get("unidad", ""), c.get("periodo") or c.get("anio") or "", c.get("texto") or c.get("concepto")))
    print("afirmaciones %d · cifras %d · citas %d · ejemplos %d · descartados %d" % (len(X["afirmaciones"]), len(X["cifras"]), len(X["citas"]),
                                                                                   len(X["ejemplos"]), len(X["descartados"])))
    print("\n".join(lineas_ejemplos(X["ejemplos"])))
    for x in f:
        print("FALLA", x)
    st = VD.estado(trabajo)
    print("→ %s · base %s · paleta %s · música %s" % (VD.rel(os.path.join(trabajo, "explicacion.json")), st["hilo"], st["paleta"], st["musica"]))
    if f:
        return 1
    if not X["cifras"]:
        return falla("E5 ninguna cifra real verificada: el acto 3 («en tu vida») necesita ≥ 1 dato de Guatemala (las anclas del encuadre)")
    return 0


def cmd_ejemplos(a):
    trabajo = os.path.abspath(a.trabajo)
    X, f = consolidar(trabajo)
    print("\n".join(lineas_ejemplos(X["ejemplos"], serie_max=60)))
    for x in f:
        print("FALLA", x)
    return 1 if f else 0


def explicacion_de(trabajo):
    ruta = os.path.join(trabajo, "explicacion.json")
    if not os.path.exists(ruta):
        raise SystemExit(falla("falta explicacion.json: corre python3 scripts/explica.py consolidar %s" % VD.rel(trabajo)))
    return leer(ruta)


# ---------- extensión de video.py: escena cuenta, estructura del explicador, ganchos con «quetzales» ----------
def aplicar_extension(trabajo):
    """Enchufa en video.py lo propio de /explica (una vez por proceso): el tipo cuenta con su voz, sus tiempos y su
    transición; las familias y los visuales del explicador; la estructura E5 en lugar de la de /video; «quetzales» cuenta
    para R6 (el concepto es universal; el anclaje es la moneda y los datos)."""
    global TRABAJO_ACTUAL, E_ACTUAL
    TRABAJO_ACTUAL = trabajo
    E_ACTUAL = leer(os.path.join(trabajo, "explicacion.json")) if os.path.exists(os.path.join(trabajo, "explicacion.json")) else {}
    if ORIGINALES:
        return
    ORIGINALES.update(estructura=VD.validar_estructura)
    VD.NARRACION_VIDEO = False   # la narración la revisa revisar_narracion (E9), con los topes de /explica
    VD.TIPOS = VD.TIPOS + tuple(t for t in TIPOS_PROPIOS if t not in VD.TIPOS)
    VD.CARACTERES.update(CARACTERES)
    VD.CARACTERES.update(CARACTERES_VIDEO_EN_EXPLICA)
    VD.SIN_HUECO = VD.SIN_HUECO + TIPOS_PROPIOS
    VD.FAMILIAS, VD.VISUALES = FAMILIAS, VISUALES
    VD.VISUALES_DE = dict(VD.VISUALES_DE, **VISUALES_DE)
    VD.ROTACION_FAMILIAS = ROTACION_FAMILIAS
    VD.RE_GUATEMALA = re.compile(r"\bguatemal\w*|\bchap[ií]n\w*|\bquetzal\w*", re.I)
    VD.POST_CONSTRUCTORES.append(post_explica)
    VD.validar_estructura = estructura
    VD.CONSTRUCTORES.update(cuenta=t_cuenta)
    VD.TRANSICION_DE.update(cuenta="texto")


def rotulo_de(e):
    """El rótulo de acto de una escena: `rotulo {etiqueta (≤ 12, grande), titulo (≤ 4 palabras)}` dibujado sobre la
    primera escena del acto mientras la voz sigue (el «anio» de /historia: aquí la palabra grande del acto)."""
    r = e.get("rotulo")
    if not isinstance(r, dict):
        return None
    return {"anio": str(r.get("etiqueta") or r.get("anio") or "").strip(), "titulo": (r.get("titulo") or "").strip(),
            "lugar": r.get("lugar") or "", "numero": r.get("numero"), "capitulo": False}


acto_de = VD.acto_de


def V9_de_video(x):
    """Las líneas de /video que el explicador no hereda: la escena 2 = T1 (no hay hilo detrás), la voz que empieza con
    el conector (la causalidad vive en la narración) y el tope de una escena explica (aquí ≤ 2)."""
    return HI.V9_de_video(x) or bool(re.match(r"V1 \d+ escenas explica; máximo", x))


def estructura(g, st, dur, tarjetas):
    """V1/V9 de /video sin lo que el explicador no hereda + E5 (tres actos, rótulos, intuición y corrección, giro,
    variedad), E11 (la cuenta en forma) y las secuencias de voz (H20 de /historia)."""
    f = [x for x in ORIGINALES["estructura"](g, st, dur, tarjetas) if not V9_de_video(x)]
    escenas = g.get("escenas") or []
    tipos = [e.get("tipo") for e in escenas]
    n = len(escenas)
    if n > ESCENAS_MAX:
        f.append("E5 %d escenas: van ≤ %d (más el cierre son los 20 nodos que ElevenLabs genera de una vez)" % (n, ESCENAS_MAX))
    if tipos.count("explica") > EXPLICA_MAX:
        f.append("E5 %d escenas explica; máximo %d" % (tipos.count("explica"), EXPLICA_MAX))
    if tipos.count("cuenta") > CUENTAS_MAX:
        f.append("E11 %d escenas cuenta; máximo %d (la pizarra es un acento, no el video)" % (tipos.count("cuenta"), CUENTAS_MAX))
    if any(a == b == "cuenta" for a, b in zip(tipos, tipos[1:])):
        f.append("E11 dos escenas cuenta seguidas: entre dos cuentas va la imagen (una tarjeta, una animación, un golpe)")
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    for i, ac in enumerate(actos, 1):
        if i > 1 and ac not in (1, 2, 3):
            f.append("E5 escena %d: «acto» 1, 2 o 3 (la pregunta, el mecanismo, en tu vida)" % i)
    validos = [a for a in actos if a in (1, 2, 3)]
    if validos != sorted(validos):
        f.append("E5 los actos van en orden (1 → 2 → 3): una escena vuelve a un acto anterior")
    if validos and set(validos) != {1, 2, 3}:
        f.append("E5 faltan actos: %s (van los tres)" % ", ".join(str(a) for a in (1, 2, 3) if a not in validos))
    primeras = {}
    for i, ac in enumerate(actos, 1):
        primeras.setdefault(ac, i)
    rotulos = []
    for i, e in enumerate(escenas, 1):
        r = rotulo_de(e)
        if r is None:
            continue
        rotulos.append(i)
        ac = actos[i - 1]
        if e.get("tipo") not in ROTULO_TIPOS:
            f.append("E5 escena %d: el rótulo va sobre una escena %s, no en %s" % (i, "|".join(ROTULO_TIPOS), e.get("tipo")))
        if ac not in (2, 3) or primeras.get(ac) != i:
            f.append("E5 escena %d: el rótulo marca la PRIMERA escena de los actos 2 y 3" % i)
        if not r["anio"] or len(r["anio"]) > ROTULO_ETIQUETA:
            f.append("E5 escena %d: rótulo «etiqueta» (la palabra grande del acto: «El motor», «En tu vida»; ≤ %d caracteres)" % (i, ROTULO_ETIQUETA))
        if VD.palabras(r["titulo"]) > ROTULO_TITULO:
            f.append("E5 escena %d: rótulo «titulo» de ≤ %d palabras" % (i, ROTULO_TITULO))
    for ac in (2, 3):
        if primeras.get(ac) and primeras[ac] not in rotulos:
            f.append("E5 el acto %d empieza en la escena %d sin rótulo: rotulo {etiqueta, titulo?} sobre esa escena (la voz sigue)" % (ac, primeras[ac]))
    for k in range(SEGUIDAS_MAX, n):
        if len(set(tipos[k - SEGUIDAS_MAX:k + 1])) == 1:
            f.append("E5 escenas %d–%d: %d escenas %s seguidas (máximo %d)" % (k - SEGUIDAS_MAX + 1, k + 1, SEGUIDAS_MAX + 1, tipos[k], SEGUIDAS_MAX))
    intu = [i for i, e in enumerate(escenas, 1) if e.get("intuicion")]
    corr = [i for i, e in enumerate(escenas, 1) if e.get("corrige")]
    if len(intu) != 1 or (validos and actos[intu[0] - 1] != 1) or (intu and intu[0] == 1):
        f.append("E5 una escena del acto 1 (no el gancho) con «intuicion»: true: la que dice la idea equivocada (llegaron %d)" % len(intu))
    if len(corr) != 1 or (validos and actos[corr[0] - 1] != 2) or (intu and corr and corr[0] < intu[0]):
        f.append("E5 una escena del acto 2 con «corrige»: true: la que rompe la idea equivocada, después de la de intuicion (llegaron %d)" % len(corr))
    if not any(t in ("explica", "cuenta") for t, ac in zip(tipos, actos) if ac == 2):
        f.append("E5 el acto 2 (el mecanismo) lleva ≥ 1 escena explica o cuenta: el mecanismo se ve, no solo se dice")
    giros = [k for k, e in enumerate(escenas) if e.get("giro")]
    if len(giros) != 1:
        f.append("E5 una escena con «giro»: true (la otra cara del mecanismo); llegaron %d" % len(giros))
    elif not GIRO_ENTRE[0] <= giros[0] / max(1, n - 1) <= GIRO_ENTRE[1]:
        f.append("E5 el giro (escena %d) va entre el %d y el %d %% del video" % (giros[0] + 1, GIRO_ENTRE[0] * 100, GIRO_ENTRE[1] * 100))
    elif validos and actos[giros[0]] != 2:
        f.append("E5 el giro (escena %d) va en el acto 2 (está en el acto %s)" % (giros[0] + 1, actos[giros[0]]))
    # secuencias de voz: la forma la revisa video.py (V9); aquí lo semántico (H20 de /historia)
    secs = g.get("secuencias") or []
    if g.get("voz_continua") and not secs:
        f.append("E9 voz_continua exige «secuencias» (grupos de %d–%d escenas consecutivas del mismo acto)" % SECUENCIA)
    for k, grupo in enumerate(secs if isinstance(secs, list) else [], 1):
        if not (isinstance(grupo, list) and all(isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= n for x in grupo)):
            continue
        if len({actos[x - 1] for x in grupo}) > 1:
            f.append("E9 secuencia %d (escenas %s): cruza actos; una secuencia vive dentro de un acto" % (k, ", ".join(map(str, grupo))))
        for x in grupo[1:]:
            if escenas[x - 1].get("giro") or rotulo_de(escenas[x - 1]):
                f.append("E9 secuencia %d: la escena %d (giro o rótulo) solo puede ABRIR una secuencia" % (k, x))
    for i, e in enumerate(escenas, 1):
        if e.get("tipo") == "cuenta":
            f += ["E11 escena %d: %s" % (i, m) for m in cuenta_mal_armada(e)]
        elif e.get("tipo") in VD.CON_TUIT:
            gr = e.get("grafico") or {}
            if not os.path.exists(os.path.join(RAIZ, "templates", "graficos", "%s.html" % gr.get("plantilla"))):
                f.append("E5 escena %d: «grafico.plantilla» «%s» no es una de templates/graficos/" % (i, gr.get("plantilla")))
            if not isinstance(gr.get("datos"), dict):
                f.append("E5 escena %d: «grafico.datos» (el contrato DATA de la plantilla: referencias/diseno/graficos.md)" % i)
        if e.get("enlace") not in (None, "") and e.get("enlace") not in VD.ENLACES:
            f.append("E5 escena %d: enlace «%s» no es pero|por_eso|y" % (i, e.get("enlace")))
    f += VD.hilo_referencias(escenas, cod="E9")
    f += pago_revelacion(g, escenas)
    final = ((g.get("cierre") or {}).get("final") or "").strip()
    if re.search(r"\bseg[uú]n\b", final, re.I):
        f.append("E9 el final del cierre no lleva «según»: lo último que se oye es la consecuencia, no la fuente")
    return f


def pago_revelacion(g, escenas):
    """E12 (H14 de /historia): la promesa declara qué revelación del encuadre paga y la escena `pago` la cuenta."""
    revs = (encuadre(TRABAJO_ACTUAL).get("revelaciones") or []) if TRABAJO_ACTUAL else []
    p = g.get("promesa") or {}
    if not revs:
        return []
    k = p.get("revela")
    if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= len(revs):
        return ["E12 promesa.revela: el número (1–%d) de la revelación del encuadre que la promesa paga (el digesto las lista R1, R2…)" % len(revs)]
    pago = p.get("pago")
    if not isinstance(pago, int) or not 1 <= pago <= len(escenas):
        return []
    e = escenas[pago - 1]
    dicho = plano(" ".join(str(e.get(c) or "") for c in ("texto", "pantalla", "linea", "golpe", "titulo")))
    raices = HI.raices_de(revs[k - 1])
    if raices and not any(re.search(r"\b" + re.escape(r), dicho) for r in raices):
        return ["E12 la escena %d (promesa.pago) no cuenta la revelación R%d («%s»): la promesa se paga ahí, con sus palabras"
                % (pago, k, revs[k - 1][:70])]
    return []


# ---------- la cuenta (E11) ----------
def numero_de(celda):
    """«Q1,000» → 1000 · «10 %» → (10, %) · «7.2 años» → 7.2. → (valor, es_porcentaje) o (None, False)."""
    m = re.search(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?", str(celda or ""))
    if not m:
        return None, False
    return float(m.group().replace(",", "")), "%" in str(celda)


def renglones_de(e):
    out = []
    for x in e.get("renglones") or []:
        if not isinstance(x, dict):
            continue
        out.append({"a": str(x.get("a") or "").strip(), "op": OPS.get(str(x.get("op") or "").strip(), str(x.get("op") or "").strip()),
                    "b": str(x.get("b") or "").strip(), "r": str(x.get("r") or "").strip(), "nota": (x.get("nota") or "").strip(),
                    "resalta": x.get("resalta"), "etiqueta": (x.get("etiqueta") or "").strip(), "aprox": bool(x.get("aprox"))})
    return out


def cuenta_mal_armada(e):
    out = []
    rs = renglones_de(e)
    if not RENGLONES[0] <= len(rs) <= RENGLONES[1]:
        out.append("%d–%d «renglones» {a, op, b, r, nota?, resalta?, etiqueta?}" % RENGLONES)
    resaltados = [x for x in rs if x["resalta"]]
    if len(resaltados) > 1:
        out.append("un solo renglón con «resalta» (una sola cosa en acento por escena)")
    golpe = (e.get("golpe") or "").strip()
    if not golpe or VD.palabras(golpe) > VD.GOLPE_PALABRAS or len(golpe) > VD.GOLPE_CARACTERES:
        out.append("«golpe» de 1–%d palabras y ≤ %d caracteres (el título de la pizarra)" % (VD.GOLPE_PALABRAS, VD.GOLPE_CARACTERES))
    for k, x in enumerate(rs, 1):
        for c in ("a", "b", "r"):
            if not x[c] or len(x[c]) > CELDA_CARACTERES:
                out.append("renglón %d: «%s» de 1–%d caracteres" % (k, c, CELDA_CARACTERES))
        if x["op"] not in ("+", "−", "×", "÷"):
            out.append("renglón %d: op + | − | × | ÷" % k)
            continue
        if len(x["nota"]) > NOTA_CARACTERES:
            out.append("renglón %d: «nota» ≤ %d caracteres («Año 2», «Tarjeta»)" % (k, NOTA_CARACTERES))
        if x["resalta"] not in (None, False, "a", "b", "r"):
            out.append("renglón %d: «resalta» a | b | r (la celda en acento)" % k)
        if x["resalta"] and (not x["etiqueta"] or VD.palabras(x["etiqueta"]) > ETIQUETA_PALABRAS or len(x["etiqueta"]) > ETIQUETA_CARACTERES):
            out.append("renglón %d: el resaltado lleva «etiqueta» de 1–%d palabras (qué es: «interés sobre interés»)" % (k, ETIQUETA_PALABRAS))
        (a, pa), (b, pb), (r, _) = numero_de(x["a"]), numero_de(x["b"]), numero_de(x["r"])
        if None in (a, b, r):
            out.append("renglón %d: a, b y r llevan un número" % k)
            continue
        if pb and x["op"] == "×":
            b = b / 100.0
        calc = {"+": a + b, "−": a - b, "×": a * b, "÷": a / b if b else float("nan")}[x["op"]]
        tol = max(0.5 * 10 ** -VM.decimales(r), 0.02 * abs(r) if x["aprox"] else 0)
        if not abs(calc - r) <= tol + 1e-9:
            out.append("renglón %d: %s %s %s da %s, no %s (la pizarra no se equivoca: corrige r o marca aprox: true si es una "
                       "aproximación que la voz dice como tal)" % (k, x["a"], x["op"], x["b"], VD.clave(round(calc, 4)), x["r"]))
    return out


# ---------- E3, E4, E6–E8, E10: verdad del explicador ----------
def valores_por_clase(trabajo):
    """(valores reales, valores ilustrativos) de base/datos.json: cada uno [(número, factor)] como valores_respaldo."""
    datos = leer(os.path.join(trabajo, "base", "datos.json"))
    reales, ilus = set(), set()
    for c in datos["cifras"]:
        nums = [c.get("valor")] + [p.get("v") for p in c.get("serie") or []]
        f = VM.factor_unidad(c.get("unidad"))
        destino = ilus if c.get("ilustrativo") else reales
        destino |= {(round(float(x), 6), f) for x in nums if isinstance(x, (int, float)) and not isinstance(x, bool)}
    return sorted(reales), sorted(ilus)


def textos_de_escena(e):
    partes = [e.get("texto"), e.get("pantalla"), e.get("linea"), e.get("golpe"), e.get("titulo"), e.get("pregunta")] + \
        [str(p) for p in e.get("pasos") or []] + list(e.get("opciones") or [])
    for x in renglones_de(e) if e.get("tipo") == "cuenta" else []:
        partes += [x["a"], x["b"], x["r"]]
    vd = e.get("visual_datos") or {}
    for k in ("a", "b"):
        if isinstance(vd.get(k), dict) and isinstance(vd[k].get("valor"), (int, float)):
            partes.append(VD.clave(vd[k]["valor"]))
    return [str(x) for x in partes if x]


def es_ilustrativa(e, reales, ilus):
    """True si la escena dice o muestra un número que solo respaldan los ejemplos ilustrativos (ninguna cifra real)."""
    if e.get("ejemplo") is True:
        return True
    texto = " ".join(textos_de_escena(e))
    sin_real = VM.sueltos(VD.exentar_de_cada(texto, reales), reales)
    return any(not VM.sueltos(tok, ilus) for tok in sin_real)


def revisar_verdad(g, X, trabajo):
    """E4 (lo ilustrativo se dice como ejemplo y nunca como dato de Guatemala), E6 (los personajes del gancho vuelven),
    E7 (el acento de cada escena es un concepto en acento de la leyenda), E8 (la jerga llega presentada), E10 (no es
    consejo) y E5 (el acto 3 trae un dato real). → (fallas, escenas ilustrativas)."""
    f = []
    escenas = g.get("escenas") or []
    reales, ilus = valores_por_clase(trabajo)
    enc = encuadre(trabajo)
    ilustrativas = []
    vistos_acto = set()
    for i, e in enumerate(escenas, 1):
        ac = acto_de(e, i)
        if not es_ilustrativa(e, reales, ilus):
            continue
        ilustrativas.append(i)
        voz = VD.sin_pausas(e.get("texto") or "")
        if ac not in vistos_acto:
            vistos_acto.add(ac)
            antes = VD.sin_pausas((escenas[i - 2].get("texto") or "")) if i >= 2 and acto_de(escenas[i - 2], i - 1) == ac else ""
            if not RE_SUPON.search(voz) and not RE_SUPON.search(antes):
                f.append("E4 escena %d: es la primera del acto %s con números de ejemplo y la voz no lo dice como ejemplo («supón», "
                         "«imagina», «por ejemplo», «hagamos la cuenta»)" % (i, ac))
        for o in re.split(r"(?<=[.?!;…])\s+", voz):
            if RE_GUATEMALA_FRASE.search(o) and any(not VM.sueltos(tok, ilus) for tok in VM.sueltos(VD.exentar_de_cada(o, reales), reales)):
                f.append("E4 escena %d: «%s» pone un número de ejemplo junto a Guatemala: un número ilustrativo nunca se dice como "
                         "dato del país" % (i, o[:80]))
        fuente = (e.get("grafico") or {}).get("fuente") or ""
        if e.get("tipo") in VD.CON_TUIT and not re.search(r"ejemplo|ilustrativ|c[aá]lculo propio", fuente, re.I):
            f.append("E4 escena %d: la tarjeta muestra números de ejemplo: «grafico.fuente» dice «Ejemplo ilustrativo (cálculo propio)», "
                     "nunca una institución" % i)
    if not any(acto_de(e, i) == 3 and VM.sueltos(" ".join(textos_de_escena(e)), reales) != VM.sueltos(" ".join(textos_de_escena(e)), [])
               for i, e in enumerate(escenas, 1)):
        f.append("E5 el acto 3 («en tu vida») no dice ninguna cifra real verificada: el mecanismo aterriza en un dato de Guatemala "
                 "(las anclas del encuadre)")
    # E6 personajes del gancho que vuelven
    nombres = [p.get("nombre") for p in enc.get("personajes") or [] if (p.get("nombre") or "").strip()]
    g1 = plano(" ".join(textos_de_escena(escenas[0]))) if escenas else ""
    for nom in nombres:
        if re.search(r"\b%s\b" % re.escape(plano(nom)), g1) and not any(
                re.search(r"\b%s\b" % re.escape(plano(nom)), plano(" ".join(textos_de_escena(e)))) for e in escenas[2:] + [g.get("cierre") or {}]):
            f.append("E6 %s abre el gancho y no vuelve: el ejemplo conductor reaparece (≥ 1 vez después de la escena 2) para pagar el gancho" % nom)
    # E7 acento declarado
    ley = {plano(x.get("concepto")): x.get("papel") for x in enc.get("leyenda") or [] if isinstance(x, dict)}
    for i, e in enumerate(escenas, 1):
        if e.get("acento") is not None and ley.get(plano(e["acento"])) != "acento":
            f.append("E7 escena %d: «acento» «%s» no es un concepto en acento de la leyenda (%s): el mismo concepto, el mismo color en todo el video"
                     % (i, e["acento"], ", ".join(k for k, v in ley.items() if v == "acento")))
    # E8 glosario: cada término llega definido
    voces = [plano(VD.sin_pausas(e.get("texto") or "")) for e in escenas] + [plano(VD.sin_pausas((g.get("cierre") or {}).get("texto") or ""))]
    for x in enc.get("glosario") or []:
        t = plano(x.get("termino"))
        k = next((j for j, v in enumerate(voces) if t and re.search(r"\b%s\b" % re.escape(t), v)), None)
        if k is None:
            continue
        if k < len(escenas) and escenas[k].get("tipo") == "definicion" and plano(escenas[k].get("termino")) == t:
            continue
        cerca = " ".join([voces[k]] + ([voces[k - 1]] if k else []))
        raices = HI.raices_de(x.get("definicion") or "")
        if raices and not any(re.search(r"\b" + re.escape(r), cerca) for r in raices):
            f.append("E8 escena %d: «%s» aparece sin explicarse: dilo con su definición («%s») en esa voz o en la anterior, o con una "
                     "escena definicion" % (k + 1, x.get("termino"), x.get("definicion")))
    # E10 no consejo
    todo = [(i, " ".join(textos_de_escena(e))) for i, e in enumerate(escenas, 1)] + \
        [(len(escenas) + 1, " ".join([(g.get("cierre") or {}).get("texto") or ""] + list((g.get("cierre") or {}).get("resumen") or [])))] + \
        [(0, json.dumps(g.get("caption") or {}, ensure_ascii=False))]
    for i, t in todo:
        m = RE_CONSEJO.search(t)
        if m:
            f.append("E10 %s: «%s»: un explicador no aconseja ni nombra bancos o productos; di la consecuencia, no la orden"
                     % ("captions" if i == 0 else "escena %d" % i, m.group()))
        if enc.get("sensible") == "salud" and RE_SALUD.search(t):
            f.append("E10 %s: «%s»: en salud, ni dosis ni diagnóstico" % ("captions" if i == 0 else "escena %d" % i, RE_SALUD.search(t).group()))
    # E2 en el guion: cada afirmación citada existe y es publicable; lo en_disputa se atribuye
    afs = {x["id"]: x for x in (X.get("afirmaciones") or []) + (X.get("citas") or [])}
    for i, e in enumerate(escenas, 1):
        for aid in e.get("afirmaciones") or []:
            if aid not in afs:
                f.append("E2 escena %d: la afirmación «%s» no está entre las publicables de explicacion.json" % (i, aid))
            elif afs[aid].get("estado") == "en_disputa" and not HI.ATRIBUCION.search(VD.sin_pausas(e.get("texto") or "")):
                f.append("E2 escena %d: %s está en disputa: la voz la atribuye («según…», «calcula…»)" % (i, aid))
    return f, ilustrativas


def revisar_narracion(g, st):
    """E9: la narración de corrido (H15 de /historia: cada acto es la suma literal de sus voces), las palabras de la
    duración, el flujo (conectores por acto, aperturas, cortes por minuto: H16) y el presupuesto de «según» (H19)."""
    d = CLAVE_DE.get(st["duracion"], DURACION_DEFECTO)
    pal_av, pal_duro = FORMATOS[d][3], FORMATOS[d][4]
    f = VD.revisar_reparto(g, cod="E9")
    narr = VD.narracion_de(g)
    if not narr or [a for a, _ in narr] != [1, 2, 3] or not all(t for _, t in narr):
        narr = []
    g_narr = dict(g, narracion=[{"acto": a, "texto": t} for a, t in narr])
    if narr:
        total = sum(VD.palabras(t) for _, t in narr)
        if not pal_duro[0] <= total <= pal_duro[1]:
            f.append("E9 %d palabras de narración; «%s» pide %d–%d (≈ %d s a 145 palabras por minuto)" % (total, d, *pal_av, FORMATOS[d][1]))
        elif not pal_av[0] <= total <= pal_av[1]:
            print("AVISO E9 %d palabras de narración: apunta a %d–%d (≈ %d s)" % (total, *pal_av, FORMATOS[d][1]))
    # un explicador cambia de imagen más seguido que una historia: más de 6.5 cortes por minuto es aviso, como en /video
    f += VD.revisar_hilo_voz(g_narr, cod="E9", conectores_min=1 if d == "corto" else CONECTORES_MIN_POR_ACTO, cortes_falla=False)
    f += VD.revisar_segun(g_narr, cod="E9", maximo=SEGUN_MAX_VIDEO, por_acto_max=SEGUN_MAX_ACTO)
    if g.get("escenas"):
        f += [x.replace("V17", "E9", 1) for x in VD.revisar_actos(g)]
    return f


def cmd_narracion(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    g = leer(os.path.join(trabajo, "guion.json"))
    narr = VD.narracion_de(g)
    if not narr:
        return falla("guion.json sin «narracion»: escribe primero [{acto: 1, texto}, {acto: 2, texto}, {acto: 3, texto}]")
    total_p, total_s = 0, 0.0
    for ac, t in narr:
        pal, seg = VD.palabras(t), len(VD.sin_pausas(NE.convertir(t)[1])) / VD.CPS
        con = VD.CONECTORES_NARRACION.findall(VD.sin_pausas(t))
        total_p, total_s = total_p + pal, total_s + seg
        print("acto %s · %d palabras · %.0f s · %d conector(es) · %d «según»" % (ac, pal, seg, len(con), len(VD.RE_SEGUN.findall(t))))
    d = CLAVE_DE.get(st["duracion"], DURACION_DEFECTO)
    print("total %d palabras · %.0f s de voz · «%s» pide %d–%d palabras (≈ %d s con las colas)" % (total_p, total_s, d, *FORMATOS[d][3], FORMATOS[d][1]))
    if not a.check:
        return 0
    f = revisar_narracion(dict(g, escenas=[]), st)
    for x in f:
        print("FALLA", x)
    print("narracion %s" % ("ok" if not f else "con %d falla(s)" % len(f)))
    return 1 if f else 0


# ---------- gate del guion ----------
def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    try:
        g = leer(os.path.join(trabajo, "guion.json"))
    except (OSError, ValueError) as ex:
        return falla("guion.json ilegible: %s" % ex)
    st = VD.estado(trabajo)
    X = explicacion_de(trabajo)
    if g.get("voz_continua", True) and not g.get("secuencias") and g.get("escenas"):
        g["secuencias"] = VD.secuencias_por_defecto(g, rompe=lambda e: e.get("giro") or rotulo_de(e))
        g["voz_continua"] = bool(g["secuencias"])
        escribir(os.path.join(trabajo, "guion.json"), g)
        print("secuencias por defecto (voz de corrido): %s" % " · ".join("–".join(map(str, (s[0], s[-1]))) for s in g["secuencias"]))
    fallas = HI.construir_tarjetas(trabajo, g, st)
    fallas = [x.replace("H6", "E5", 1) for x in fallas]
    aplicar_extension(trabajo)
    f_verdad, ilustrativas = revisar_verdad(g, X, trabajo)
    fallas += f_verdad
    fallas += revisar_narracion(g, VD.estado(trabajo))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):   # las FALLA de video.py (V1–V5, V9, F1–F8, E5, E11, E12) van también al RETORNO
        rc = VD.cmd_guion(argparse.Namespace(trabajo=trabajo, check=True))
    salida = buf.getvalue()
    print(salida, end="")
    for x in fallas:
        print("FALLA", x)
    todas = fallas + [l[len("FALLA "):] for l in salida.splitlines() if l.startswith("FALLA ")]
    loc = os.path.join(trabajo, "locucion.json")
    if fallas and rc == 0 and os.path.exists(loc):
        os.remove(loc)   # una locución que no pasó E1–E12 no se graba
    ok = rc == 0 and not fallas
    if ok:
        L = leer(loc)
        for le in L["escenas"]:
            le["ejemplo"] = le["n"] in ilustrativas
        escribir(loc, L)
        print("E1–E12 ok · escenas con números de ejemplo (chip «Ejemplo»): %s" % (", ".join(map(str, ilustrativas)) or "ninguna"))
        if L["estimado_s"] > DURACION_MAX_S:
            print("AVISO %.0f s estimados: pasa de %d s (el tope de YouTube Shorts)" % (L["estimado_s"], DURACION_MAX_S))
    print("RETORNO " + json.dumps(retorno_guion(trabajo, g, ok, todas, ilustrativas), ensure_ascii=False))
    return 0 if ok else 1


def retorno_guion(trabajo, g, ok, fallas, ilustrativas):
    es = g.get("escenas") or []
    loc = os.path.join(trabajo, "locucion.json")
    est = leer(loc)["estimado_s"] if ok and os.path.exists(loc) else round(VD.estimado_guion_s(g), 1)
    return {"archivo": VD.rel(os.path.join(trabajo, "guion.json")), "gate": "ok" if ok else "falla", "fallas": fallas,
            "escenas": len(es), "tipos": [e.get("tipo") for e in es],
            "actos": len({acto_de(e, i) for i, e in enumerate(es, 1)} & {1, 2, 3}),
            "rotulos": sum(1 for e in es if rotulo_de(e)),
            "palabras": sum(VD.palabras(t) for _, t in VD.narracion_de(g)),
            "segun": sum(len(VD.RE_SEGUN.findall(VD.sin_pausas(e.get("texto") or ""))) for e in es + [g.get("cierre") or {}]),
            "intuicion": next((i for i, e in enumerate(es, 1) if e.get("intuicion")), None),
            "corrige": next((i for i, e in enumerate(es, 1) if e.get("corrige")), None),
            "ilustrativas": ilustrativas, "secuencias": len(g.get("secuencias") or []), "estimado_s": est,
            "explica_sin_animacion": [i for i, e in enumerate(es, 1) if e.get("tipo") == "explica" and not e.get("animacion")]}


def cmd_ganchos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    if a.check:
        a.usar = None
    return VD.cmd_ganchos(a)


def cmd_tarjetas(a):
    return HI.cmd_tarjetas(a)


# ---------- tiempos: la cuenta, el rótulo de acto y el chip «Ejemplo» ----------
def t_cuenta(S, e, ps, pal, fin_voz, dur, g):
    """La pizarra (video/cuenta.html): el golpe arriba; cada renglón entra cuando la voz dice su primer número y el
    resultado «cae» cuando la voz lo dice (si no lo dice, a mitad de su tramo); el resaltado se enciende tras su resultado."""
    esc = HI.escena_guion(S, g)
    rs = renglones_de(esc)
    S["pagina"] = "cuenta"
    golpe = (esc.get("golpe") or "").split()
    S["arriba"] = [{"text": w, "start": round(VD.TRANSICION + 0.12 * k, 3)} for k, w in enumerate(golpe)]
    ini = VD.TRANSICION + 0.45
    nums = [(w["start"], w["clave"]) for w in pal if w.get("clave")]
    ptr, entradas, resultados = 0, [], []
    for x in rs:
        claves = {c: VD.clave(v) for c, (v, pct) in ((c, numero_de(x[c])) for c in ("a", "b", "r")) if v is not None}
        t_a = t_r = None
        for j in range(ptr, len(nums)):
            t, cl = nums[j]
            if t_a is None and cl in (claves.get("a"), claves.get("b"), claves.get("r")):
                t_a = t
            if cl == claves.get("r"):
                t_r, ptr = t, j + 1
                break
        entradas.append(t_a)
        resultados.append(t_r)
    n = len(rs)
    for k in range(n):   # lo que la voz no dice se reparte entre sus vecinos
        if resultados[k] is None:
            a = next((resultados[j] for j in range(k - 1, -1, -1) if resultados[j] is not None), ini)
            b = next(((j, resultados[j]) for j in range(k + 1, n) if resultados[j] is not None), (n, max(a + 0.8, fin_voz - 0.4)))
            resultados[k] = a + (b[1] - a) / (b[0] - k + 1)
        if entradas[k] is None or entradas[k] > resultados[k]:
            entradas[k] = max(ini if k == 0 else resultados[k - 1] + 0.3, resultados[k] - 1.1)
    renglones = []
    for k, x in enumerate(rs):
        t_e = max(entradas[k], ini if k == 0 else renglones[-1]["start"] + 0.5)
        t_r = max(resultados[k], t_e + 0.45)
        renglones.append(dict(x, start=round(t_e, 3), tr=round(min(t_r, dur - 0.6), 3)))
    S["T"] = {"ini": round(ini, 3), "renglones": renglones, "fin": round(fin_voz, 3), "dur": dur,
              "saldo": bool(esc.get("saldo")), "fuente": (esc.get("fuente") or "").strip() or None}
    ev = [(ini, "lienzo")] + [(x["start"], "renglon") for x in renglones] + [(x["tr"], "resultado") for x in renglones]
    sfx = [(0.0, "grave" if e.get("enlace") == "pero" else "whoosh")] + [(x["tr"], "tic") for x in renglones]
    for x in renglones:
        if x["resalta"]:
            ev.append((x["tr"] + 0.35, "resalta"))
            sfx.append((x["tr"] + 0.35, "resolucion"))
    return ev, sfx


def post_explica(S, e, ps, pal, fin_voz, dur, g, ev, sfx):
    """Tras el constructor de cualquier escena: el chip «Ejemplo» (la escena dice números ilustrativos), el rótulo de
    acto sobre la primera escena de los actos 2 y 3 (lo propio espera a que se vaya), y la transición dentro de una
    secuencia de voz (fundido; la del giro manda). Reutiliza el rótulo de /historia (armar_rotulo, eventos_rotulo)."""
    esc = HI.escena_guion(S, g)
    tipo = S.get("tipo")
    S["ejemplo"] = bool(e.get("ejemplo"))
    if tipo not in ("gancho", "cierre", "adivina"):
        R = rotulo_de(esc)
        if R:
            d = HI.DESFASE_ROTULO
            for w in S.get("arriba") or []:
                w["start"] = round(w["start"] + d, 3)
            T = S.get("T") or {}
            for k in ("tit", "ini"):
                if isinstance(T.get(k), (int, float)):
                    T[k] = round(T[k] + d, 3)
            if isinstance(T.get("pant"), dict):
                for k in ("desde", "hasta"):
                    if isinstance(T["pant"].get(k), (int, float)):
                        T["pant"][k] = round(T["pant"][k] + d, 3)
            for lista in (T.get("linea") or [], T.get("pasos") or [], T.get("items") or [], T.get("puntos") or [], T.get("renglones") or []):
                for w in lista:
                    w["start"] = round(max(w["start"], HI.ROTULO_S), 3)
                    if "tr" in w:
                        w["tr"] = round(max(w["tr"], w["start"] + 0.45), 3)
            for v in (T.get("valores") or {}).values():
                v[0] = round(max(v[0], HI.ROTULO_S), 3)
            for k in ("nota", "figuras", "destacadas", "etiqueta_t"):
                if isinstance(T.get(k), (int, float)):
                    T[k] = round(max(T[k], HI.ROTULO_S + (1.0 if k == "nota" else 0.0)), 3)
            ev = [(max(t, HI.ROTULO_S) if k in HI.ENTRADAS_ROTULO + ("renglon", "resultado", "resalta") else t, k) for t, k in ev]
            S["R"] = HI.armar_rotulo(S, esc, ps, g, R)
            ev_r, sfx_r = HI.eventos_rotulo(S)
            sfx = [(t, k) for t, k in sfx if not (t <= VD.TRANSICION + 0.1 and k in ("whoosh", "impacto"))] + [(0.0, "whoosh")] + sfx_r
            ev += ev_r
        elif S.get("seguida") and not esc.get("giro"):
            sfx = [(t, k) for t, k in sfx if not (t <= VD.TRANSICION + 0.1 and k in ("whoosh", "impacto"))]
    if S.get("transicion") and tipo != "cierre":
        if esc.get("giro"):
            S["transicion"] = VD.TRANSICIONES["giro"]
        elif S.get("seguida") and not rotulo_de(esc):
            S["transicion"] = VD.TRANSICIONES["seguida"]
    return ev, sfx


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    rc = VD.cmd_tiempos(argparse.Namespace(trabajo=trabajo))
    if rc:
        return rc
    ruta = os.path.join(trabajo, "escenas.json")
    E = leer(ruta)
    g = leer(os.path.join(trabajo, "guion.json"))
    E["tipo"] = "explica"
    E["cierre"]["rotulo"] = (g.get("cierre") or {}).get("rotulo") or CIERRE_ROTULO
    escribir(ruta, E)
    if E["total_s"] + VD.BUCLE_S > DURACION_MAX_S:
        print("AVISO duración real %.1f s: pasa de %d s (el tope de YouTube Shorts)" % (E["total_s"] + VD.BUCLE_S, DURACION_MAX_S))
    return 0


# ---------- probar y aplicar los arreglos del crítico (los de /historia, con los gates de /explica) ----------
def correr_gates(trabajo):
    rc = 0
    for cmd in ("narracion", "guion"):
        r = subprocess.run([sys.executable, os.path.abspath(__file__), cmd, trabajo, "--check"], capture_output=True, text=True, cwd=RAIZ)
        for linea in (r.stdout + r.stderr).splitlines():
            if linea.startswith(("FALLA", "AVISO")):
                print("%s · %s" % (cmd, linea))
        rc = rc or (1 if r.returncode else 0)
    return rc


def cmd_probar(a):
    trabajo = os.path.abspath(a.trabajo)
    try:
        cambios = HI.leer_cambios(a.cambios)
    except (OSError, ValueError) as ex:
        print("FALLA --cambios ilegible: %s" % ex)
        return 2
    tmp = os.path.join(RAIZ, "sesiones", "_probar-%s-%d" % (os.path.basename(trabajo), os.getpid()))
    shutil.copytree(trabajo, tmp, ignore=shutil.ignore_patterns("audio", "salida", "revision", "clips*", "segs*"))
    try:
        g = leer(os.path.join(tmp, "guion.json"))
        ruta_g = os.path.join(tmp, "ganchos.json")
        gan = leer(ruta_g) if os.path.exists(ruta_g) else None
        rc, msg, _ = HI.aplicar_cambios(g, gan, cambios)
        if rc:
            print(msg)
            return rc
        escribir(os.path.join(tmp, "guion.json"), g)
        if gan is not None:
            escribir(ruta_g, gan)
        rc = correr_gates(tmp)
        print("probar: %s" % ("pasa el gate (narracion + guion)" if rc == 0 else "el gate lo rechaza: ajusta el arreglo o dalo como mejora con esta falla"))
        return rc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_aplicar(a):
    trabajo = os.path.abspath(a.trabajo)
    try:
        cambios = HI.leer_cambios(a.cambios)
    except (OSError, ValueError) as ex:
        print("FALLA --cambios ilegible: %s" % ex)
        return 2
    ruta, ruta_g = os.path.join(trabajo, "guion.json"), os.path.join(trabajo, "ganchos.json")
    g = leer(ruta)
    gan = leer(ruta_g) if os.path.exists(ruta_g) else None
    rc, msg, escenas = HI.aplicar_cambios(g, gan, cambios)
    if rc:
        print(msg)
        return rc
    shutil.copyfile(ruta, os.path.join(trabajo, "guion.previo.json"))
    if gan is not None:
        shutil.copyfile(ruta_g, os.path.join(trabajo, "ganchos.previo.json"))
    escribir(ruta, g)
    if gan is not None:
        escribir(ruta_g, gan)
    if correr_gates(trabajo):
        shutil.copyfile(os.path.join(trabajo, "guion.previo.json"), ruta)
        if gan is not None:
            shutil.copyfile(os.path.join(trabajo, "ganchos.previo.json"), ruta_g)
        correr_gates(trabajo)
        print("aplicar: el gate lo rechaza; guion.json queda como estaba")
        return 1
    print("aplicar: %d cambio(s) en el TRABAJO · gate ok" % len(cambios))
    print("RETORNO %s" % json.dumps({"escenas_cambiadas": sorted(escenas)}, ensure_ascii=False))
    return 0


# ---------- digestos ----------
def lineas_verificado(X):
    out = ["## Afirmaciones verificadas (id · estado · tipo — texto [fuentes])"]
    for x in X.get("afirmaciones") or []:
        out.append("- %s · %s · %s — %s [%s]%s" % (x["id"], x["estado"], x.get("tipo"), x.get("texto"),
                                                  ", ".join(f.get("medio") or NT.dominio(f.get("url") or "") for f in x.get("fuentes") or []),
                                                  " · en disputa: %s" % x.get("nota") if x["estado"] == "en_disputa" else ""))
    out += ["", "## Cifras reales de Guatemala (id · valor · periodo — concepto [fuente]; la voz dice de cuándo es)"]
    for c in X.get("cifras") or []:
        out.append("- %s · %s %s · %s — %s [%s]" % (c["id"], c["valor"], c.get("unidad") or "", c.get("periodo") or c.get("anio") or "",
                                                  c.get("concepto") or c.get("texto"), ", ".join(f.get("medio") or NT.dominio(f.get("url") or "")
                                                                                                for f in c.get("fuentes") or [])))
    if X.get("citas"):
        out += ["", "## Citas literales (id · autor — frase)"] + ["- %s · %s — «%s»" % (q["id"], q.get("autor"), q.get("texto")) for q in X["citas"]]
    out += ["", "## Ejemplos calculados (la calculadora de explica.py; NUNCA calcules tú: usa estos ids)"] + lineas_ejemplos(X.get("ejemplos") or [])
    return out


def lineas_encuadre(enc):
    return ["- Pregunta: %s" % enc.get("pregunta"), "- La idea equivocada (intuicion): %s" % enc.get("intuicion"),
            "- Mecanismo: %s · lo que el oyente tiene que poder devolver: «%s»" % (enc.get("mecanismo"), enc.get("mecanismo_frase")),
            "- Leyenda de color (TODO el video): %s" % " · ".join("%s = %s" % (x.get("concepto"), x.get("papel")) for x in enc.get("leyenda") or []),
            "- Glosario (cada término llega definido, E8): %s" % ("; ".join("%s: %s" % (x.get("termino"), x.get("definicion")) for x in enc.get("glosario") or []) or "—"),
            "- Personajes del ejemplo: %s" % ("; ".join("%s — %s" % (p.get("nombre"), p.get("presentacion")) for p in enc.get("personajes") or []) or "ninguno"),
            "- Anclas de Guatemala (acto 3): %s" % "; ".join("%s (%s)" % (x.get("concepto"), x.get("fuente_sugerida")) for x in enc.get("anclas") or []),
            "- Revelaciones (lo que el video PAGA; la promesa paga una con promesa.revela):"] + \
        ["  R%d. %s" % (k, r) for k, r in enumerate(enc.get("revelaciones") or [], 1)] + \
        ["- No afirma: %s" % "; ".join(enc.get("no_afirma") or []), "- Sensible: %s" % enc.get("sensible")]


def pantalla_de(e, tarjetas):
    """Lo que se LEE en una escena (sin ids ni fuentes)."""
    if e.get("tipo") == "cuenta":
        rs = renglones_de(e)
        return " · ".join([e.get("golpe") or ""] + ["%s%s %s %s = %s%s" % ("%s: " % x["nota"] if x["nota"] else "", x["a"], x["op"], x["b"], x["r"],
                                                                        " (%s)" % x["etiqueta"] if x["etiqueta"] else "") for x in rs])
    r = rotulo_de(e)
    rot = "%s · %s · " % (r["anio"], r["titulo"]) if r else ""
    return rot + VD.pantalla_video(e, tarjetas)


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    enc = encuadre(trabajo)
    if a.para in ("investigador", "verificador"):
        eje = next((x for x in enc.get("ejes") or [] if x.get("id") == a.eje), None)
        if not eje:
            return falla("el encuadre no tiene el eje «%s»" % a.eje)
        out = ["# %s · eje %s (%s)" % (st.get("tema"), eje["id"], eje.get("nombre")), ""] + lineas_encuadre(enc) + [
            "", "## Tu eje", "- Qué buscar: %s" % "; ".join(eje.get("preguntas") or []),
            "- Fuentes sugeridas: %s" % "; ".join(eje.get("fuentes") or []),
            "- Ejemplos que el encuadre quiere calcular (si un parámetro es {cifra: id}, esa cifra la traes tú con ese id): %s"
            % "; ".join("%s %s %s" % (x.get("id"), x.get("modelo"), json.dumps(x.get("parametros"), ensure_ascii=False)) for x in enc.get("ejemplos") or []),
            "- Afirmaciones (<eje>-aNN, tipo definicion|regla|proceso|dato|norma) y cifras (<eje>-cNN con periodo y unidad), cada una con "
            "fuentes [{url, archivo (historia.py leer), cita literal ≥ 20 caracteres que trae el número}] y estado confirmado (2 grupos o "
            "1 oficial/académica) · una_fuente · en_disputa (nota) · no_confirmado",
            "- Wikipedia y los blogs de finanzas personales NO cuentan: úsalos para llegar a la fuente oficial, la ley o la academia."]
        if a.para == "verificador":
            ruta = os.path.join(trabajo, "hallazgos_%s.json" % a.eje)
            if not os.path.exists(ruta):
                return falla("falta %s" % VD.rel(ruta))
            hz = leer(ruta)
            out += ["", "## Hallazgos del investigador (verifícalos uno por uno)"]
            for k in ("afirmaciones", "cifras", "citas"):
                for x in hz.get(k) or []:
                    out.append("- %s · %s — %s" % (x.get("id"), (x.get("texto") or x.get("concepto") or "")[:200],
                               " | ".join("%s «%s»" % (ev.get("url"), (ev.get("cita") or "")[:140]) for ev in x.get("fuentes") or [])))
        out += ["", "## Clases de fuente que cuentan", "- oficial: *.gob.gt, %s, %s" % (", ".join(sorted(NT.OFICIALES)), ", ".join(sorted(HI.OTROS_OFICIALES))),
                "- academica: *.edu, %s" % ", ".join(sorted(HI.ACADEMICAS)),
                "- medio (dominio → grupo): %s" % ", ".join("%s→%s" % kv for kv in sorted({**NT.MEDIOS, **HI.INTERNACIONALES}.items()))]
        print("\n".join(out))
        return 0
    X = explicacion_de(trabajo)
    if a.para == "oyente":
        ruta = os.path.join(trabajo, "locucion.json")
        if not os.path.exists(ruta):
            return falla("falta locucion.json: corre python3 scripts/explica.py guion %s --check" % VD.rel(trabajo))
        tarjetas = {t["n"]: t for t in st["tarjetas"]}
        print("\n".join(VD.lineas_oyente(leer(os.path.join(trabajo, "guion.json")), leer(ruta), lambda e: pantalla_de(e, tarjetas)) + [
            "", "## Al terminar: explícalo de vuelta", "- `explicacion_devuelta`: en UNA oración, cómo funciona lo que te explicaron, con tus "
            "palabras, como se lo dirías a un amigo. Si no puedes, dilo: es la confusión más grave."]))
        return 0
    rec_g = st.get("ganchos_recientes") or {}
    d = CLAVE_DE.get(st["duracion"], DURACION_DEFECTO)
    base = ["# Explica · %s (%s, %d s · paleta %s · música %s)" % (st.get("tema"), d, FORMATOS[d][1], st["paleta"], st["musica"]), ""] + \
        lineas_encuadre(enc) + [""] + lineas_verificado(X)
    if a.para == "gancho":
        out = base + ["", "## Ganchos del explicador (4–5 candidatos de familias distintas; ≥ 2 con visual)",
                      "- Familias: %s · visuales: %s (pareja = dos bloques de área proporcional: el ejemplo conductor frente a frente)"
                      % (", ".join(FAMILIAS), ", ".join(VISUALES)),
                      "- El gancho plantea la PREGUNTA del video sin dar el mecanismo (la revelación la paga el video): una paradoja del "
                      "ejemplo conductor, un resultado sorprendente con su referente, el espectador como protagonista («tú»).",
                      "- Números de ejemplo: solo los ej-cNN de arriba (o un calculo con ellos); la voz los dice como ejemplo («imagina», "
                      "«supón») y la pantalla lleva el chip «Ejemplo» sola. Nunca «en Guatemala» junto a un número de ejemplo.",
                      "- «Guatemala» o «quetzales» en la voz o la pantalla del gancho (R6).",
                      "- Bloqueadas por rotación: familias %s · visual %s" % (", ".join(rec_g.get("familias") or []) or "ninguna",
                                                                           ", ".join(rec_g.get("visuales") or []) or "ninguno")]
        print("\n".join(out))
        return 0
    if a.para == "critico":
        g = leer(os.path.join(trabajo, "guion.json")) if os.path.exists(os.path.join(trabajo, "guion.json")) else {}
        ruta = os.path.join(trabajo, "locucion.json")
        narr = VD.narracion_corrida(g, leer(ruta) if os.path.exists(ruta) else None)
        base += ["", "## Narración (de corrido): léela como quien la oye sin pantalla"] + ["- Acto %s: %s" % (ac, t) for ac, t in narr]
    c = VD.CARACTERES
    out = base + ["", "## Límites del guion (explica.py guion --check: E1–E12 + V1–V5, V9, F1–F8; devuelve TAL CUAL su línea RETORNO)",
                  "- PRIMERO la narración: guion.narracion = [{acto: 1, texto}, {acto: 2, texto}, {acto: 3, texto}] (%d–%d palabras en "
                  "total ≈ %d s; con dígitos). Mídela con python3 scripts/explica.py narracion <TRABAJO> --check. DESPUÉS repártela en "
                  "escenas SIN cambiar una palabra (la suma de las voces de cada acto, más el cierre en el 3, es la narración: E9)"
                  % (*FORMATOS[d][3], FORMATOS[d][1]),
                  "- Actos: 1 LA PREGUNTA (gancho, promesa y la escena «intuicion»: true que dice la idea equivocada con justicia; "
                  "termina en el detonante «pero eso no es lo que pasa»), 2 EL MECANISMO (definicion, cuenta, explica; la escena "
                  "«corrige»: true rompe la intuición; el punto medio es el «ajá»; el «giro»: true es la otra cara del mecanismo, "
                  "entre el %d y el %d %%), 3 EN TU VIDA (el mecanismo con una cifra real de Guatemala, la regla práctica y el pago de "
                  "la promesa). La primera escena de los actos 2 y 3 lleva rotulo {etiqueta ≤ %d («El motor», «En tu vida»), titulo ≤ %d "
                  "palabras} sobre %s" % (GIRO_ENTRE[0] * 100, GIRO_ENTRE[1] * 100, ROTULO_ETIQUETA, ROTULO_TITULO, "|".join(ROTULO_TIPOS)),
                  "- Lo concreto antes que lo abstracto: la cuenta con quetzales va antes de la definición o justo después; la fórmula "
                  "algebraica no sale en pantalla. Un ejemplo conductor: los mismos personajes y los mismos números de principio a fin "
                  "(E6: los personajes del gancho vuelven)",
                  "- Números de ejemplo (ej-cNN): la primera escena de cada acto que los usa los dice como ejemplo («supón», «imagina», "
                  "«por ejemplo», «hagamos la cuenta»: E4); el chip «Ejemplo» sale solo; nunca junto a «en Guatemala»; en una tarjeta, "
                  "grafico.fuente = «Ejemplo ilustrativo (cálculo propio)». Las cifras reales dicen de cuándo son y su fuente va en "
                  "pantalla (grafico.fuente o «fuente» de la cuenta) o en la voz",
                  "- cuenta (la pizarra): golpe ≤ %d palabras, renglones %d–%d {a, op (+ − × ÷), b, r, nota? ≤ %d («Año 2»), resalta? "
                  "(a|b|r: la celda en acento, una por escena), etiqueta? ≤ %d palabras (qué es lo resaltado), aprox?}, saldo? (el "
                  "último resultado en grande), fuente?; el gate rehace cada cuenta (E11); la voz dice el resultado de cada renglón; "
                  "≤ %d cuentas, nunca dos seguidas"
                  % (VD.GOLPE_PALABRAS, *RENGLONES, NOTA_CARACTERES, ETIQUETA_PALABRAS, CUENTAS_MAX),
                  "- «acento»: el concepto de la leyenda que esa escena muestra en acento (E7). Jerga del glosario: definida en su "
                  "primera mención (E8). Nada de consejo, bancos ni productos (E10)",
                  "- Flujo (E9): ≥ %d conectores causales o temporales por acto; ≤ %d «según» (≤ %d por acto). Voz por escena: gancho "
                  "%d–%d · tarjeta %d–%d · cuenta %d–%d · golpe %d–%d · definicion %d–%d · explica %d–%d · cierre %d–%d caracteres (en "
                  "palabras; %.1f car/s)" % (CONECTORES_MIN_POR_ACTO, SEGUN_MAX_VIDEO, SEGUN_MAX_ACTO, *c["gancho"], *CARACTERES_VIDEO_EN_EXPLICA["tarjeta"],
                                             *CARACTERES["cuenta"], *CARACTERES_VIDEO_EN_EXPLICA["golpe"], *CARACTERES_VIDEO_EN_EXPLICA["definicion"],
                                             *CARACTERES_VIDEO_EN_EXPLICA["explica"], *c["cierre"], VD.CPS),
                  "- promesa {texto (10–80, literal en la voz de la escena en), en: 2, pago (último tercio), revela (R del encuadre)}",
                  "- Secuencias: grupos de %d–%d escenas consecutivas del mismo acto (sin gancho ni cierre; giro o rótulo solo al inicio); "
                  "si no las escribes, el gate las deriva" % SECUENCIA,
                  "- tarjeta: tuit (1, 2…), golpe ≤ %d palabras, grafico {plantilla de templates/graficos/, kicker, titular, nota, fuente, "
                  "datos}; para la curva simple contra compuesto, `linea` con dos series de ej-cNN.serie" % VD.GOLPE_PALABRAS,
                  *VD.lineas_animaciones(st.get("animaciones_recientes") or []),
                  "- Cierre: rotulo «%s», resumen %d–%d líneas ≤ %d (lo que el espectador se lleva), texto, tipo remate, forma "
                  "consecuencia (lo que el mecanismo le hace a quien lo vive; mecanismo, quien, verbo), ≤ 1 cifra y nunca la del gancho, "
                  "sin «según», sin consejo" % (CIERRE_ROTULO, *VD.RESUMEN_LINEAS, VD.RESUMEN_CARACTERES),
                  "", "## Frases ya usadas (C11)"] + VD.frases_usadas(st["slug"]) + HI.frases_historias(st["slug"]) + frases_explicaciones(st["slug"])
    print("\n".join(out))
    return 0


# ---------- entrega ----------
def cmd_entregar(a):
    """Copia la explicación a explicaciones/<fecha>-<slug>/ (o --salida) con guion.json de entrega, fuentes.md y
    ejemplos.md (cada número de ejemplo con su fórmula). No vuelve a correr los gates: entrega lo grabado."""
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    sal = os.path.join(trabajo, "salida")
    for f in SALIDA_ENTREGA:
        if not os.path.exists(os.path.join(sal, f)):
            return falla("falta salida/%s: graba, monta y revisa (también --formato 4:5) antes de entregar" % f)
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    if not os.path.exists(ruta_cred) and not a.salida:
        return falla("sin audio/creditos.json: la voz no salió de ElevenLabs (una maqueta o una voz falsa solo se entrega con --salida)")
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, "explicaciones", "%s-%s" % (st["fecha"], st["slug"])))
    os.makedirs(destino, exist_ok=True)
    for f in glob.glob(os.path.join(destino, "portada*.png")):
        os.remove(f)
    for f in list(SALIDA_ENTREGA) + [os.path.basename(x) for x in glob.glob(os.path.join(sal, "portada_*.png"))]:
        shutil.copy2(os.path.join(sal, f), os.path.join(destino, f))
    for f in ("contacto.png", "contacto_4x5.png"):
        if os.path.exists(os.path.join(trabajo, "revision", f)):
            shutil.copy2(os.path.join(trabajo, "revision", f), os.path.join(destino, f))
    g, X, enc = leer(os.path.join(trabajo, "guion.json")), explicacion_de(trabajo), encuadre(trabajo)
    loc, E = leer(os.path.join(trabajo, "locucion.json")), leer(os.path.join(trabajo, "escenas.json"))
    escenas_g = g.get("escenas") or []
    critica, rc = None, os.path.join(trabajo, "critica.json")
    if os.path.exists(rc):
        c = leer(rc)
        critica = {"veredicto": c.get("veredicto"), "vuelta": c.get("vuelta"), "puntajes": c.get("puntajes")}
    else:
        print("AVISO sin critica.json: la explicación se entrega sin la revisión del crítico")
    oy = os.path.join(trabajo, "oyente.json")
    devuelta = leer(oy).get("explicacion_devuelta") if os.path.exists(oy) else None
    escenas = []
    for e, s_ in zip(loc["escenas"], E["escenas"]):
        eg = escenas_g[e["n"] - 1] if e["n"] - 1 < len(escenas_g) else {}
        escenas.append({"n": e["n"], "tipo": e["tipo"], "acto": e.get("acto"), "pantalla": e.get("pantalla"), "voz": e.get("voz"),
                        "dur": s_["dur"], "ejemplo": bool(e.get("ejemplo")), "afirmaciones": eg.get("afirmaciones") or [],
                        "animacion": eg.get("animacion"), "mecanismo": eg.get("mecanismo")})
    e1 = escenas_g[0] if escenas_g else {}
    entrega = {
        "id": "%s-%s" % (st["fecha"], st["slug"]), "tipo": "explica", "slug": st["slug"], "tema": st.get("tema"), "fecha": st["fecha"],
        "duracion": CLAVE_DE.get(st["duracion"], DURACION_DEFECTO), "pregunta": enc.get("pregunta"), "intuicion": enc.get("intuicion"),
        "mecanismo": enc.get("mecanismo"), "mecanismo_frase": enc.get("mecanismo_frase"), "explicacion_devuelta": devuelta,
        "actos": [{"numero": acto_de(e, i), "etiqueta": rotulo_de(e)["anio"], "titulo": rotulo_de(e)["titulo"], "escena": i}
                  for i, e in enumerate(escenas_g, 1) if rotulo_de(e)],
        "narracion": g.get("narracion"), "secuencias": g.get("secuencias"), "paleta": st["paleta"], "musica": st["musica"],
        "voz": loc["voz"], "velocidad": VD.VELOCIDAD, "creditos_voz": leer(ruta_cred)["total"] if os.path.exists(ruta_cred) else None,
        "duracion_s": round(VD.ffprobe_dur(os.path.join(destino, "video.mp4")), 1), "critica": critica,
        "gancho": {k: e1.get(k) for k in ("familia", "visual", "pantalla", "linea")}, "promesa": g.get("promesa"),
        "ejemplos": [{"id": x["id"], "modelo": x["modelo"], "ilustrativo": x["ilustrativo"]} for x in X.get("ejemplos") or []],
        "escenas": escenas, "cierre": g.get("cierre"), "caption": g.get("caption")}
    escribir(os.path.join(destino, "guion.json"), entrega)
    open(os.path.join(destino, "fuentes.md"), "w", encoding="utf-8").write(fuentes_md(st, escenas_g, X))
    open(os.path.join(destino, "ejemplos.md"), "w", encoding="utf-8").write(ejemplos_md(st, X))
    print("entregado en %s (%.1f s) · video.mp4 (TikTok, Reels, Shorts) + video_4x5.mp4 (feed) · caption.md · fuentes.md · ejemplos.md%s"
          % (VD.rel(destino), entrega["duracion_s"], "" if entrega["creditos_voz"] is None else " · %s créditos de voz" % entrega["creditos_voz"]))
    return 0


def fuentes_md(st, escenas, X):
    L = ["# Fuentes · %s" % st.get("tema"), "",
         "Para la descripción o el primer comentario. Lo que el video afirma y los datos de Guatemala que usa, con sus fuentes. "
         "Los números marcados «Ejemplo» son ilustrativos: están calculados en ejemplos.md.", ""]
    usadas = {a for e in escenas for a in e.get("afirmaciones") or []}
    for titulo, xs in (("Afirmaciones", [x for x in X.get("afirmaciones") or [] if not usadas or x["id"] in usadas]),
                       ("Datos de Guatemala", X.get("cifras") or [])):
        if not xs:
            continue
        L += ["## %s" % titulo, ""]
        for x in xs:
            txt = x.get("texto") or "%s: %s %s (%s)" % (x.get("concepto"), x.get("valor"), x.get("unidad") or "", x.get("periodo") or "")
            L.append("- %s%s" % (txt, HI.etiqueta_estado(x)))
            for f in x.get("fuentes") or []:
                if f.get("url"):
                    L.append("  - %s: %s" % (f.get("medio") or NT.dominio(f["url"]), f["url"]))
        L.append("")
    L.append("Sígueme: %s" % " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES))
    return "\n".join(L) + "\n"


def ejemplos_md(st, X):
    L = ["# Ejemplos · %s" % st.get("tema"), "", "Cada número de ejemplo del video, con su fórmula (calculado por scripts/explica.py).", ""]
    for x in X.get("ejemplos") or []:
        par = ", ".join("%s = %s%s" % (k, v["valor"], " (dato real: %s)" % v["cifra"] if v.get("cifra") else "") for k, v in x["parametros"].items())
        L += ["## %s · %s%s" % (x["id"], x.get("descripcion") or x["modelo"], " (ilustrativo)" if x["ilustrativo"] else ""), "", "Parámetros: %s" % par, ""]
        for s in x["salidas"]:
            if s["serie"]:
                L.append("- %s: %s" % (s["salida"], ", ".join("%s → %s" % (p["periodo"], VD.clave(p["v"])) for p in s["serie"])))
            else:
                L.append("- %s = %s %s · %s" % (s["salida"], VD.clave(s["valor"]), s["unidad"], s["calculo"]))
        L.append("")
    return "\n".join(L) + "\n"


REENVIO = ("voz", "voz-falsa", "descargar", "partir", "escuchar", "grabar", "montar", "revisar")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in REENVIO:
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video.py")] + sys.argv[1:], cwd=RAIZ).returncode
    if len(sys.argv) > 1 and sys.argv[1] == "leer":
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "historia.py")] + sys.argv[1:], cwd=RAIZ).returncode
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("preparar")
    q.add_argument("tema")
    q.add_argument("--duracion", choices=list(FORMATOS), default=DURACION_DEFECTO)
    q.add_argument("--slug")
    q.add_argument("--trabajo")
    q.add_argument("--paleta")
    q.add_argument("--musica")
    q.add_argument("--fixture", action="store_true", help="la maqueta de sesiones/_fixture_explica (sin web)")
    sub.add_parser("leer", help="→ scripts/historia.py leer")
    q = sub.add_parser("encuadre")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q = sub.add_parser("afirmaciones")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--eje")
    sub.add_parser("consolidar").add_argument("trabajo")
    sub.add_parser("ejemplos").add_argument("trabajo")
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--para", choices=["investigador", "verificador", "gancho", "guionista", "critico", "oyente"], default="guionista")
    q.add_argument("--eje")
    q = sub.add_parser("ganchos")
    q.add_argument("trabajo")
    x = q.add_mutually_exclusive_group(required=True)
    x.add_argument("--check", action="store_true")
    x.add_argument("--usar", nargs="?", const="")
    q.add_argument("--segundo")
    q = sub.add_parser("narracion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true")
    sub.add_parser("tarjetas").add_argument("trabajo")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    for nombre in ("probar", "aplicar"):
        q = sub.add_parser(nombre)
        q.add_argument("trabajo")
        q.add_argument("--cambios", required=True, help='JSON o archivo: [{"escena": N, "texto": "…"}, {"escena": N, "campo": "golpe", '
                       '"valor": "…"}, {"promesa": "…"}, {"cierre": "…"}]')
    sub.add_parser("tiempos").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida", help="otra carpeta (pruebas, maqueta o voz falsa)")
    for nombre in REENVIO:
        sub.add_parser(nombre, help="→ scripts/video.py %s" % nombre)
    a = p.parse_args()
    return {"preparar": cmd_preparar, "encuadre": cmd_encuadre, "afirmaciones": cmd_afirmaciones, "consolidar": cmd_consolidar,
            "ejemplos": cmd_ejemplos, "digesto": cmd_digesto, "ganchos": cmd_ganchos, "narracion": cmd_narracion,
            "tarjetas": cmd_tarjetas, "guion": cmd_guion, "probar": cmd_probar, "aplicar": cmd_aplicar, "tiempos": cmd_tiempos,
            "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
