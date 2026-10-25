#!/usr/bin/env python3
"""/historia: un evento o una historia de Guatemala contada de principio a fin → video vertical 1080×1920 de 2–3 min
(TikTok / Reels / Shorts) y 4:5.

Este script hace lo propio de la historia: el estado del trabajo, el texto guardado de cada fuente (también PDF y
Wayback), las fotos con licencia (Wikimedia Commons, oficiales, del medio), el gate de los hechos (H1–H3), la
cronología, la base que respalda la voz y el gate del guion (H4–H8). Escribe el MISMO trabajo que /video: arma en
TRABAJO/base/ un «hilo base» (hilo.json, datos.json con las cifras y los números de los hechos verificados, y las
tarjetas tuit_N.html materializadas de las plantillas de templates/graficos/), así que el gate del guion (V1–V5, V9,
F1–F8), los ganchos (R1–R12), los tiempos, la voz, la grabación, el montaje y la revisión salen de scripts/video.py con
sus escenas propias (foto, cita, capitulo) enchufadas por sus extensiones (CONSTRUCTORES, TRANSICION_DE, SIN_HUECO).
Guía: referencias/flujo-historia.md.

Subcomandos (TRABAJO = sesiones/historia-<slug>/):
  preparar <tema> [--slug S] [--trabajo DIR] [--paleta P] [--musica ID] [--fixture]   crea TRABAJO y video.json
        (--fixture copia la maqueta de sesiones/_fixture_historia y dibuja sus fotos)
  leer URL [--buscar CITA] [--otra-vez]   guarda el texto de una fuente (HTML, PDF o su copia en Wayback) en sesiones/_descargas/historia/
  commons BUSQUEDA                lista fotos de Wikimedia Commons con su licencia (✓ libre / ✗ no se usa)
  foto TRABAJO --id ID (--commons "File:…" | --url U --credito "Foto: …" --origen oficial|medio|empresa) --descripcion D
        [--fecha F] [--lugar L] [--retrato-de PERSONA] [--encaje contener] [--extmetadata JSON]
        baja la foto, comprueba lado y licencia (H7) → fotos/<id>.jpg + .json (con su sha1; un gráfico o cartel con
        texto va con --encaje contener: márgenes del color de su borde para que el marco no lo recorte)
  hechos TRABAJO --check [--eje E]   H1–H3 sobre verificacion_<eje>.json (citas en el texto guardado, fechas, independencia)
  consolidar TRABAJO           verificaciones + fotos → historia.json, base/ (hilo.json, datos.json) y la paleta del encuadre
  digesto TRABAJO --para investigador|verificador --eje E | gancho | guionista | critico
  ganchos TRABAJO --check | --usar [ID] [--segundo ID]   → video.py ganchos con las familias y el visual foto de historia
  tarjetas TRABAJO             las escenas con gráfico → base/tuit_N.html (materializar.py, R1–R6) y video.json.tarjetas
  guion TRABAJO --check        H4–H8 + (tarjetas) + video.py guion (V1–V5, V9, F1–F8) → locucion.json
  tiempos TRABAJO              video.py tiempos con los constructores de foto, cita y capitulo → escenas.json
  fotos-contacto TRABAJO       fotos/contacto.png con todas las fotos (QA de contenido)
  entregar TRABAJO [--salida DIR]   → historias/<fecha>-<slug>/ (video, 4:5, caption, fuentes.md, cronologia.md, guion.json)
  voz | voz-falsa | descargar | escuchar | grabar | montar | revisar TRABAJO [...]   → video.py (mismos argumentos)

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import datetime
import glob
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import numeros_es as NE  # noqa: E402
import noticias as NT  # noqa: E402
import verificacion as VM  # noqa: E402
import video as VD  # noqa: E402

# ---- formato (decisiones del usuario, 2026-10-24) ----
OBJETIVO_S, DURACION_MAX_S = 150, 180       # «regularmente 2 o 3 minutos»; 180 s es el tope de YouTube Shorts
VD.DURACIONES["historia"] = {"s": OBJETIVO_S, "tarjetas": (0, 6), "golpes": (0, 10), "tol": 0.2}   # V4: 120–180 s
TIPOS_PROPIOS = ("foto", "cita", "capitulo")
CARACTERES = {"foto": (40, 210), "cita": (30, 220), "capitulo": (10, 90)}   # voz ya en palabras (≈ 15.5 car/s)
CAPITULOS, SEGUIDAS_MAX, GIRO_ENTRE = (3, 5), 2, (0.40, 0.75)
TITULAR_PALABRAS, TITULAR_CARACTERES = 9, 60          # el titular de una escena foto
CHIP_CARACTERES, LUGAR_CARACTERES, FUENTE_CARACTERES = 14, 24, 44
CIFRA_CARACTERES, ETIQUETA_CARACTERES = 18, 30
CAP_TITULO_PALABRAS, CAP_TITULO_CARACTERES, CAP_ANIO_CARACTERES = 4, 28, 12
CITA_FRASE_CARACTERES, CREDITO_CARACTERES, ETIQUETA_GANCHO = 170, 60, 30
TRADUCCION_CARACTERES = 140                           # la traducción de una cita en otro idioma (renglón bajo la frase)
ESCENAS_MAX = 19          # + el cierre = 20 nodos: el tope de creative_run_flow_nodes (y de una llamada de estado sin Scribe)
FOTO_USOS_MAX = 2         # una misma imagen (por sha1) en ≤ 2 escenas, contando el gancho y los retratos
# palabras vacías para notar una cita que no está en español (lleva `traduccion`)
VACIAS_EN = {"the", "and", "they", "we", "you", "is", "are", "was", "were", "to", "of", "with", "while", "what", "when",
             "want", "something", "it", "that", "this", "for", "have", "has", "our", "their", "be", "will", "would", "i"}
VACIAS_ES = {"de", "la", "que", "el", "en", "y", "los", "se", "las", "un", "una", "por", "con", "no", "su", "para", "es",
             "lo", "como", "me", "mi", "al", "del", "nos", "ya"}
# ganchos de historia (referencias/flujo-historia.md): el mecanismo que frena el scroll en una historia; «foto» es la foto
# de la historia a sangre con el titular entero desde el cuadro 0 (video/noticia.html en modo titular)
FAMILIAS = ("resultado", "paradoja", "contraste", "misterio", "personaje", "lugar", "pregunta", "escala")
VISUALES = ("foto",) + VD.VISUALES
VISUALES_DE = {"resultado": ("foto", "cifra", "pareja"), "paradoja": ("foto", "pareja", "cifra"),
               "contraste": ("pareja", "foto", "llenado", "cifra"), "misterio": ("foto", "cifra"),
               "personaje": ("foto", "cifra"), "lugar": ("lugar", "foto"), "pregunta": ("foto", "cifra", "pareja"),
               "escala": ("figuras", "llenado", "pareja")}
ROTACION_FAMILIAS, ROTACION_VISUALES = 2, 1
APERTURAS = re.compile(r"^[¿¡«\s]*(?:esta es la historia|la historia de|(?:te|les) (?:cuento|voy a contar)|hab[ií]a una vez|"
                       r"en el a[nñ]o\b|corr[ií]a el a[nñ]o|hoy (?:te|les) (?:hablo|cuento))", re.I)
PUNTAJES = ("gancho", "tension", "claridad", "ritmo", "precision", "cierre")   # critica.json en modo historia (W12)
# ---- verdad ----
ESTADOS = ("confirmado", "en_disputa", "no_confirmado")
PUBLICABLES = ("confirmado", "en_disputa")
PRECISIONES = ("dia", "mes", "anio", "aprox")
CITA_MIN, HECHO_CARACTERES, HECHOS_MIN = 20, 240, 6
RE_FECHA = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
RE_ANIO = re.compile(r"(?<!\d)(?<!\d[,.])(1[5-9]\d\d|20\d\d)(?!\d|[,.]\d)")   # «en 1977,» sí; «4,1977» y «1977.5» no
RE_NUMERO = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
# en disputa = la voz atribuye o matiza
ATRIBUCION = re.compile(r"\bseg[uú]n\b|\bde acuerdo con\b|\bafirm\w+|\bdijo\b|\bdice\b|\bsostien\w+|\bhabr[ií]a\w*|"
                        r"\bcerca de\b|\balrededor de\b|\ba (?:inicios|principios|mediados|finales) de\b|\baproximadamente\b|"
                        r"\bversi[oó]n\b|\bcuenta(?:n)?\b|\brecuerda\w*|\basegur\w+|\bnarr\w+", re.I)
# fuentes que cuentan además de las de /noticias: organismos, academia, archivo y prensa internacional. Wikipedia es un
# mapa, nunca evidencia: se cita su referencia, no la página
OTROS_OFICIALES = {"cicig.org": "CICIG", "un.org": "ONU", "oas.org": "OEA", "worldbank.org": "Banco Mundial",
                   "iadb.org": "BID", "cepal.org": "CEPAL", "anacafe.org": "Anacafé", "imf.org": "FMI", "fao.org": "FAO",
                   "state.gov": "Departamento de Estado", "justice.gov": "Departamento de Justicia (EE. UU.)",
                   "treasury.gov": "Tesoro (EE. UU.)", "corteidh.or.cr": "Corte IDH"}
ACADEMICAS = {"scielo.org", "jstor.org", "redalyc.org", "dialnet.unirioja.es", "persee.fr", "openedition.org",
              "flacso.edu.gt", "asies.org.gt", "icefi.org", "avancso.org.gt", "cirma.org.gt", "academia.edu",
              "britannica.com"}
# archivos, hemerotecas y museos (instituciones, no sitios de aficionados)
ARCHIVOS = {"archive.org", "hemeroteca.prensalibre.com", "elpais.com/hemeroteca", "newspapers.com", "loc.gov",
            "archivohistoricopn.org", "nsarchive.gwu.edu", "nsarchive2.gwu.edu", "thehenryford.org", "si.edu",
            "smithsonianmag.com"}
INTERNACIONALES = {"nytimes.com": "nyt", "washingtonpost.com": "wapo", "latimes.com": "latimes", "theguardian.com": "guardian",
                   "elmundo.es": "el-mundo", "abc.es": "abc", "eluniversal.com.mx": "el-universal", "insightcrime.org": "insight-crime",
                   "elfaro.net": "el-faro", "nomada.gt": "nomada", "elperiodico.com.gt": "el-periodico", "chapinlandia.com": "chapinlandia",
                   "aprende.guatemala.com": "guatemala-com", "forbescentroamerica.com": "forbes-ca", "estrategiaynegocios.net": "eyn",
                   "eleconomista.net": "el-economista", "bloomberg.com": "bloomberg", "ft.com": "ft", "wsj.com": "wsj",
                   "revistaeyn.com": "eyn", "bloomberglinea.com": "bloomberg", "forbes.com": "forbes",
                   "forbes.com.mx": "forbes", "axios.com": "axios", "chicagotribune.com": "chicago-tribune",
                   "nbcnews.com": "nbc", "cbsnews.com": "cbs", "npr.org": "npr", "usatoday.com": "usa-today",
                   "time.com": "time", "elfinanciero.com.mx": "el-financiero", "expansion.mx": "expansion",
                   "eleconomista.com.mx": "el-economista-mx"}
# una nota de agencia publicada por otro diario cuenta como la agencia (su grupo, el mismo de NT.MEDIOS), no como el
# diario: dos diarios con el mismo cable no son independientes y un diario fuera de la lista con el cable sí cuenta
# (solo firmas: «(AP)» o «Por/By Associated Press»; el crédito de una foto, «Fulano, Associated Press», no cuenta)
FIRMA = r"\b(?:By|Por)\s+(?i:the\s+|la\s+agencia\s+|la\s+)?"
AGENCIAS = (("ap", r"\(AP\)|" + FIRMA + r"(?:Associated Press|AP)\b"), ("efe", r"\(EFE\)|" + FIRMA + r"EFE\b"),
            ("reuters", r"\(Reuters\)|" + FIRMA + r"Reuters\b"),
            ("afp", r"\(AFP\)|" + FIRMA + r"(?:AFP|Agence France-Presse)\b"))
AGENCIA_CARACTERES = 2500   # la firma de la agencia va arriba (byline o entradilla)
DESCARGAS = os.path.join(RAIZ, "sesiones", "_descargas", "historia")
# ---- fotos ----
FOTO_LADO_MIN, FOTO_LADO_AVISO = 480, 600     # material de archivo: 480 vale con aviso
# --encaje contener: el marco de noticia.html (object-fit: cover) mide ≈ 1.11 de ancho por alto en 9:16 y ≈ 0.93 en
# 4:5, y el Ken Burns acerca hasta 1.15: el lienzo deja la imagen entera dentro de los dos con ese margen
ENCAJE_MARGEN, MARCO_ANCHO, MARCO_ANGOSTO = 1.18, 1.15, 0.9
PROPORCION_GRAFICO = 1.45     # más apaisada que esto y sin --encaje: aviso (¿es un gráfico o un cartel con texto?)
ORIGENES_FOTO = ("commons", "oficial", "medio", "empresa")
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_UA = "HilosDerekUrizar/1.0 (https://x.com/DerekUrizar; datos de Guatemala) python-urllib"
LICENCIA_LIBRE = re.compile(r"^(?:public domain|dominio p[uú]blico|pd(?:[- ][\w.-]+)?|cc0(?: 1\.0)?|cc[ -]by(?:[ -]sa)?(?:[ -]\d(?:\.\d)?)?"
                            r"(?:[ -][a-z]{2})?|attribution|no restrictions|copyrighted free use)$", re.I)
LICENCIA_NO = re.compile(r"\bnc\b|\bnd\b|non-?commercial|noderiv|no deriv|fair use|non-?free", re.I)

FIXTURE = os.path.join(RAIZ, "sesiones", "_fixture_historia")
TRABAJO_ACTUAL, H_ACTUAL, ORIGINALES = None, None, {}


def leer(p):
    return VD.leer(p)


def escribir(p, obj):
    VD.escribir(p, obj)


def falla(msg):
    return VD.falla(msg)


def slug_de(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")[:60]


def plano(s):
    return NT.plano_cita(s)


# ---------- registros de historias anteriores (rotación de ganchos y cierres, C11, música) ----------
def historias_registradas(slug_actual=None):
    ruta = os.path.join(RAIZ, "memoria", "historias.json")
    regs = leer(ruta).get("historias") or [] if os.path.exists(ruta) else []
    return sorted([h for h in regs if h.get("slug") != slug_actual], key=lambda h: (h.get("fecha", ""), h.get("id", "")))


def frases_historias(slug_actual, n=VD.FRASES_USADAS_VIDEOS):
    """C11: las frases de voz de las últimas n historias (memoria/historias.json → frases), con el formato de
    video.frases_usadas (que solo lee los videos de hilos)."""
    regs = [h for h in historias_registradas(slug_actual) if h.get("frases")][-n:]
    if not regs:
        return ["- (ninguna historia anterior registrada)"]
    out = []
    for h in reversed(regs):
        fr = h["frases"]
        out.append("- historia **%s** · promesa: «%s» · gancho: «%s» · cierre (%s · %s): «%s» · aperturas: %s"
                   % (h["slug"], fr.get("promesa", ""), fr.get("gancho", ""), fr.get("cierre_tipo") or "remate",
                      fr.get("cierre_forma") or "", fr.get("cierre") or "", " / ".join("«%s…»" % x for x in fr.get("aperturas", []))))
    return out


def animaciones_recientes(slug_actual):
    """Rotación de la escena explica: las de los últimos videos (video.animaciones_recientes) y las de las últimas
    historias (memoria/historias.json → frases.animaciones)."""
    out = list(VD.animaciones_recientes(slug_actual))
    for h in historias_registradas(slug_actual)[-VD.ROTACION_ANIMACIONES:]:
        out += [x for x in (h.get("frases") or {}).get("animaciones") or [] if x and x not in out]
    return out


def recientes(slug_actual):
    fr = [h.get("frases") or {} for h in historias_registradas(slug_actual)]
    return ({"familias": [x["familia"] for x in fr[-ROTACION_FAMILIAS:] if x.get("familia")],
             "visuales": [x.get("visual") or "cifra" for x in fr[-ROTACION_VISUALES:]]},
            {"tipos": [x.get("cierre_tipo") or "remate" for x in fr[-1:]],
             "formas": [x.get("cierre_forma") for x in fr[-VD.ROTACION_CIERRES:] if x.get("cierre_forma")],
             "mecanismos": [x["cierre_mecanismo"] for x in fr[-1:] if x.get("cierre_mecanismo")]})


def elegir_musica(paleta, forzada=None):
    """La pista de la paleta usada hace más tiempo (o nunca) entre los videos y las historias registradas."""
    if forzada:
        return VD.elegir_musica(paleta, forzada)
    cat = [x for x in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"] if x["paleta"] == paleta]
    if not cat:
        raise ValueError("el catálogo no tiene música para la paleta «%s»" % paleta)
    usos = {}
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    regs = (leer(vids).get("videos") or [] if os.path.exists(vids) else []) + historias_registradas()
    for v in regs:
        usos[v.get("musica")] = max(usos.get(v.get("musica"), ""), v.get("fecha", ""))
    return sorted(cat, key=lambda x: (usos.get(x["id"], ""), x["id"]))[0]


def paletas():
    return list(leer(os.path.join(RAIZ, "design", "tokens.json"))["paletas"])


# ---------- preparar ----------
def cmd_preparar(a):
    slug = slug_de(a.slug or a.tema)
    if not slug:
        print("el tema no da un slug (letras o números)", file=sys.stderr)
        return 2
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "historia-" + slug))
    for d in ("audio", "salida", "revision", "fotos", "base"):
        os.makedirs(os.path.join(trabajo, d), exist_ok=True)
    previas = historias_registradas(slug)
    paleta = a.paleta or next((p for p in paletas() if not previas or p != previas[-1].get("paleta")), "obsidiana")
    if paleta not in paletas():
        print("--paleta: una de %s" % ", ".join(paletas()), file=sys.stderr)
        return 2
    try:
        pista = elegir_musica(paleta, a.musica)
    except ValueError as ex:
        return falla(str(ex))
    # la maqueta no rota contra lo producido (sus ganchos y cierres son fijos)
    rec_g, rec_c = ({"familias": [], "visuales": []}, {"tipos": [], "formas": [], "mecanismos": []}) if a.fixture else recientes(slug)
    ruta = os.path.join(trabajo, "video.json")
    st = leer(ruta) if os.path.exists(ruta) else {}
    st.update({"tipo": "historia", "slug": slug, "tema": a.tema, "fecha": datetime.date.today().isoformat(),
               "hilo": VD.rel(os.path.join(trabajo, "base")), "paleta": paleta, "musica": pista["id"],
               "musica_forzada": a.musica, "duracion": "historia", "objetivo_s": OBJETIVO_S,
               "ganchos_recientes": rec_g, "cierres_recientes": rec_c, "animaciones_recientes": [] if a.fixture else animaciones_recientes(slug)})
    st.setdefault("tarjetas", [])
    escribir(ruta, st)
    if a.fixture:
        rc = copiar_fixture(trabajo)
        if rc:
            return rc
    if any(VD._plano(h.get("tema")) == VD._plano(a.tema) or h.get("slug") == slug for h in previas):
        print("AVISO esta historia ya se contó (memoria/historias.json): cuéntala solo con un ángulo nuevo")
    print("historia «%s» · paleta provisional %s (el editor elige la del tema) · música %s" % (a.tema, paleta, pista["id"]))
    print(VD.rel(trabajo))
    return 0


def copiar_fixture(trabajo):
    """La maqueta: encuadre, verificaciones, ganchos, selección y guion de sesiones/_fixture_historia (sus fuentes de
    ejemplo ya guardadas en fuentes/) y sus fotos dibujadas con ffmpeg (fractales, sin web)."""
    for f in ["encuadre.json", "ganchos.json", "seleccion.json", "guion.json"] + [os.path.basename(x) for x in glob.glob(os.path.join(FIXTURE, "verificacion_*.json"))]:
        shutil.copy(os.path.join(FIXTURE, f), os.path.join(trabajo, f))
    tonos = (20, 90, 160, 230, 300)
    for k, rec in enumerate(leer(os.path.join(FIXTURE, "fotos.json"))["fotos"]):
        rec = dict(rec, archivo="fotos/%s.jpg" % rec["id"], url=None)
        VD.ff("-f", "lavfi", "-i", "mandelbrot=s=1600x1200:start_scale=%.2f:end_scale=0.3:start_x=%.3f:start_y=%.3f:maxiter=600" % (
            2.2 - 0.3 * k, -0.743 + 0.012 * k, 0.131 - 0.018 * k),
            "-vf", "hue=h=%d:s=0.5,eq=brightness=-0.05:saturation=0.75,noise=alls=12:allf=t" % tonos[k % len(tonos)],
            "-frames:v", "1", "-q:v", "3", os.path.join(trabajo, rec["archivo"]))
        escribir(os.path.join(trabajo, "fotos", rec["id"] + ".json"), rec)
    print("maqueta: fuentes de ejemplo y fotos dibujadas → %s" % VD.rel(trabajo))
    return 0


# ---------- leer una fuente (HTML, PDF o Wayback) ----------
def agencia_de(archivo):
    """La agencia que firma el texto guardado («(AP)», «Associated Press», «(EFE)», «(Reuters)», «(AFP)») en sus primeros
    caracteres, o None."""
    ruta = os.path.join(RAIZ, archivo or "")
    if not archivo or not os.path.isfile(ruta):
        return None
    cabeza = open(ruta, encoding="utf-8", errors="replace").read(AGENCIA_CARACTERES)
    return next((g for g, rx in AGENCIAS if re.search(rx, cabeza)), None)


def clasificar(url, propios=(), archivo=None):
    """(clase, grupo): oficial | medio | academica | archivo | empresa, o (None, dominio) si no cuenta. Una copia de
    Wayback cuenta como su original; Wikipedia nunca cuenta. Con el texto guardado (`archivo`), una nota firmada por una
    agencia cuenta como la agencia (medio, grupo de la agencia) aunque la publique un diario fuera de la lista."""
    m = re.match(r"https?://web\.archive\.org/web/[^/]+/(.+)$", url or "")
    if m:
        return clasificar(m.group(1), propios, archivo)
    c, g = clasificar_dominio(url, propios)
    if c in (None, "medio") and not (NT.dominio(url).endswith("wikipedia.org")):
        ag = agencia_de(archivo)
        if ag:
            return "medio", ag
    return c, g


def clasificar_dominio(url, propios=()):
    d = NT.dominio(url)
    if d.endswith("wikipedia.org") or d.endswith("wikimedia.org"):
        return None, d
    if any(d == x or d.endswith("." + x) for x in propios or ()):
        return "empresa", d
    c, g = NT.clasificar(url)
    if c:
        return c, g
    for tabla, clase in ((OTROS_OFICIALES, "oficial"), (INTERNACIONALES, "medio")):
        for k, v in tabla.items():
            if d == k or d.endswith("." + k):
                return clase, (v if clase == "medio" else k)
    if d.endswith(".edu") or ".edu." in d or any(d == k or d.endswith("." + k) for k in ACADEMICAS):
        return "academica", d
    if any(d == k.split("/")[0] or d.endswith("." + k.split("/")[0]) for k in ARCHIVOS):
        return "archivo", d
    return None, d


def leer_url(url, otra_vez=False):
    """Baja la fuente (o su última copia en Wayback si ya no responde), guarda su texto y metadatos y devuelve meta."""
    os.makedirs(DESCARGAS, exist_ok=True)
    base = os.path.join(DESCARGAS, "%s-%s" % (re.sub(r"[^a-z0-9]+", "-", NT.dominio(url)), hashlib.sha1(url.encode()).hexdigest()[:10]))
    if os.path.exists(base + ".json") and not otra_vez:
        return leer(base + ".json")
    origen, error = url, None
    for intento in (url, "https://web.archive.org/web/2026/" + url):
        try:
            datos, tipo = NT.bajar(intento, limite=40_000_000)
            origen = intento
            break
        except Exception as ex:  # noqa: BLE001 — cualquier fallo de red: se intenta la copia de Wayback
            error = ex
    else:
        raise RuntimeError("no se pudo bajar %s ni su copia en Wayback (%s)" % (url, error))
    meta = {"url": url, "leida_de": origen, "dominio": NT.dominio(url), "clase": clasificar(url)[0]}
    if datos[:5] == b"%PDF-" or "pdf" in (tipo or "").lower():
        open(base + ".pdf", "wb").write(datos)
        r = subprocess.run(["pdftotext", "-layout", base + ".pdf", base + ".txt"], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError("pdftotext falló con %s: %s" % (url, r.stderr.strip()[:200]))
        texto = open(base + ".txt", encoding="utf-8", errors="replace").read()
        meta.update(titulo=os.path.basename(urllib.parse.urlparse(url).path), fecha=None, og_image=None, formato="pdf")
    else:
        enc = re.search(r"charset=([\w-]+)", tipo or "") or re.search(rb'charset="?([\w-]+)', datos[:3000])
        enc = (enc.group(1).decode() if isinstance(enc.group(1), bytes) else enc.group(1)) if enc else "utf-8"
        p = NT._Texto()
        p.feed(datos.decode(enc, "replace"))
        texto = re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t\r\f\v]+", " ", "".join(p.partes))).strip()
        img = p.meta.get("og:image") or p.meta.get("twitter:image") or p.meta.get("twitter:image:src")
        meta.update(titulo=html.unescape(p.meta.get("og:title") or p.titulo).strip(), fecha=NT.fecha_de(p.meta, p.ld),
                    og_image=urllib.parse.urljoin(url, img) if img else None, formato="html")
        open(base + ".txt", "w", encoding="utf-8").write(texto + "\n")
    meta.update(archivo=VD.rel(base + ".txt"), caracteres=len(texto), agencia=agencia_de(VD.rel(base + ".txt")))
    meta["clase"] = clasificar(url, (), meta["archivo"])[0]
    escribir(base + ".json", meta)
    return meta


def cmd_leer(a):
    try:
        meta = leer_url(a.url, a.otra_vez)
    except RuntimeError as ex:
        return falla("%s: usa otra fuente" % ex)
    if meta["caracteres"] < 400:
        print("AVISO: solo %d caracteres de texto (la página se arma con JavaScript o bloquea): usa otra fuente o su PDF" % meta["caracteres"])
    if meta["clase"] is None:
        print("NO CUENTA: %s no es oficial, medio de la lista, agencia, academia, archivo ni museo%s. Sirve como mapa: "
              "busca y guarda la fuente que cita (o la empresa, si el encuadre la declara en dominios_propios)"
              % (meta["dominio"], "; Wikipedia: lee y cita sus referencias" if "wikipedia" in meta["dominio"] else ""))
    elif meta.get("agencia"):
        print("cuenta como la agencia «%s» (firma en el texto), no como %s" % (meta["agencia"], meta["dominio"]))
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    if a.buscar:
        t = plano(open(os.path.join(RAIZ, meta["archivo"]), encoding="utf-8", errors="replace").read())
        print("cita %s en el texto" % ("SÍ está" if plano(a.buscar) in t else "NO está"))
    return 0


# ---------- fotos: Wikimedia Commons (con licencia), oficiales, del medio o de la empresa ----------
def commons(params):
    q = dict(params, action="query", format="json", prop="imageinfo", iiprop="url|size|extmetadata|mime", iiurlwidth=1600)
    req = urllib.request.Request(COMMONS_API + "?" + urllib.parse.urlencode(q), headers={"User-Agent": COMMONS_UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def sin_html(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def licencia(ext):
    """extmetadata de Commons → (libre, licencia, autor, motivo). Libre = dominio público, CC0, CC BY o CC BY-SA (nunca
    NC ni ND, ni una obra no libre)."""
    val = lambda k: sin_html((ext.get(k) or {}).get("value"))  # noqa: E731
    lic, autor = val("LicenseShortName") or val("License"), val("Artist") or val("Credit")
    if val("NonFree").lower() in ("true", "1"):
        return False, lic, autor, "Commons la marca como obra no libre"
    if not lic:
        return False, lic, autor, "sin licencia declarada"
    if LICENCIA_NO.search(lic):
        return False, lic, autor, "licencia %s (no comercial o sin derivadas: no se usa)" % lic
    if not LICENCIA_LIBRE.match(lic.strip()):
        return False, lic, autor, "licencia %s fuera de la lista (dominio público, CC0, CC BY, CC BY-SA)" % lic
    if not autor and not re.match(r"public domain|pd|cc0", lic, re.I):
        return False, lic, autor, "CC BY pide el autor y Commons no lo declara"
    return True, lic, autor or "dominio público", ""


def credito_commons(autor, lic):
    autor = re.sub(r"\s*\(.*?\)\s*", " ", autor or "").strip() or "Wikimedia Commons"
    c = "Foto: %s · %s" % (autor, lic)
    return c if len(c) <= CREDITO_CARACTERES else "Foto: %s · %s" % (autor[:max(8, CREDITO_CARACTERES - len(lic) - 10)].rstrip() + "…", lic)


def cmd_commons(a):
    try:
        r = commons({"generator": "search", "gsrsearch": a.busqueda, "gsrnamespace": 6, "gsrlimit": 12})
    except Exception as ex:  # noqa: BLE001
        return falla("Commons no responde: %s" % ex)
    pags = sorted((r.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    if not pags:
        print("sin resultados en Commons para «%s»" % a.busqueda)
        return 0
    for p in pags:
        ii = (p.get("imageinfo") or [{}])[0]
        ext = ii.get("extmetadata") or {}
        ok, lic, autor, motivo = licencia(ext)
        print("%s %s · %s×%s · %s · %s · %s\n    %s" % ("✓" if ok and min(ii.get("width", 0), ii.get("height", 0)) >= FOTO_LADO_MIN else "✗",
              p.get("title"), ii.get("width"), ii.get("height"), lic or "sin licencia", (autor or "—")[:40],
              sin_html((ext.get("DateTimeOriginal") or {}).get("value"))[:20] or "sin fecha",
              (sin_html((ext.get("ImageDescription") or {}).get("value"))[:150] or "—") + ("" if ok else "  [%s]" % motivo)))
    print("→ foto TRABAJO --id <eje>-fNN --commons \"File:…\" --descripcion \"…\" (solo las ✓)")
    return 0


def cmd_foto(a):
    trabajo = os.path.abspath(a.trabajo)
    if not re.fullmatch(r"[a-z]{2,6}-f\d{2}", a.id or ""):
        print("--id va como <eje>-fNN (ori-f01)", file=sys.stderr)
        return 2
    rec = {"id": a.id, "descripcion": (a.descripcion or "").strip(), "fecha": a.fecha, "lugar": a.lugar,
           "retrato_de": (a.retrato_de or "").strip() or None, "encaje": a.encaje}
    if not rec["descripcion"]:
        print("--descripcion: qué muestra la foto (para el QA y para que el guionista la elija)", file=sys.stderr)
        return 2
    if a.commons:
        titulo = a.commons if a.commons.startswith("File:") else "File:" + a.commons
        try:
            ext_local = leer(a.extmetadata) if a.extmetadata else None
            if ext_local is None:
                r = commons({"titles": titulo})
                pag = next(iter((r.get("query") or {}).get("pages", {}).values()), {})
                ii = (pag.get("imageinfo") or [None])[0]
                if not ii:
                    return falla("Commons no tiene «%s»" % titulo)
            else:
                ii = {"extmetadata": ext_local, "thumburl": None, "url": None, "descriptionurl": None}
        except Exception as ex:  # noqa: BLE001
            return falla("Commons no responde: %s" % ex)
        ok, lic, autor, motivo = licencia(ii.get("extmetadata") or {})
        if not ok:
            return falla("H7 %s: %s → busca otra o deja la escena con la tarjeta tipográfica" % (titulo, motivo))
        if ext_local is not None:
            print("licencia ok: %s · %s (extmetadata local, sin descarga)" % (lic, autor))
            return 0
        url, credito, origen = ii.get("thumburl") or ii.get("url"), credito_commons(autor, lic), "commons"
        rec.update(licencia=lic, autor=autor, pagina=ii.get("descriptionurl"))
        if not rec["fecha"]:   # la fecha de la toma, si Commons la trae («2004-07-24 12:00» → «2004-07-24»)
            m = re.search(r"\b(1[89]\d\d|20\d\d)(?:[-:](\d\d)(?:[-:](\d\d))?)?", sin_html(((ii.get("extmetadata") or {}).get("DateTimeOriginal") or {}).get("value")))
            rec["fecha"] = "-".join(x for x in m.groups() if x) if m else None
    elif a.url:
        if a.origen not in ("oficial", "medio", "empresa") or not (a.credito or "").startswith("Foto: "):
            print("--url pide --origen oficial|medio|empresa y --credito \"Foto: <institución o medio>\"", file=sys.stderr)
            return 2
        url, credito, origen = a.url, a.credito, a.origen
        rec.update(licencia="© %s (crédito en pantalla)" % a.credito[6:], autor=a.credito[6:])
    else:
        print("--commons \"File:…\" o --url U --credito C --origen O", file=sys.stderr)
        return 2
    os.makedirs(os.path.join(DESCARGAS, "fotos"), exist_ok=True)
    crudo = os.path.join(DESCARGAS, "fotos", hashlib.sha1(url.encode()).hexdigest()[:12])
    try:
        if not os.path.exists(crudo):
            req = urllib.request.Request(url, headers={"User-Agent": COMMONS_UA if origen == "commons" else NT.AGENTE})
            with urllib.request.urlopen(req, timeout=40) as r:
                open(crudo, "wb").write(r.read(25_000_000))
        w, h = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                                "stream=width,height", "-of", "csv=p=0:s=x", crudo],
                                               capture_output=True, text=True).stdout.strip().split("x")[:2])
    except Exception as ex:  # noqa: BLE001
        return falla("no se pudo bajar o leer la foto %s (%s)" % (url, ex))
    if min(w, h) < FOTO_LADO_MIN:
        return falla("H7 %s: %d×%d (lado corto < %d px): busca otra" % (url, w, h, FOTO_LADO_MIN))
    if min(w, h) < FOTO_LADO_AVISO:
        print("AVISO %s: %d×%d, por debajo de %d px: se verá blanda en el marco" % (a.id, w, h, FOTO_LADO_AVISO))
    os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
    dst = "fotos/%s.jpg" % a.id
    VD.ff("-i", crudo, "-frames:v", "1", "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", os.path.join(trabajo, dst))
    if a.encaje == "contener":
        encajar(os.path.join(trabajo, dst))
    elif w / h > PROPORCION_GRAFICO:
        print("AVISO %s: %d×%d es muy apaisada; si es un gráfico, un cartel o un logo con texto, repite con --encaje "
              "contener (el marco recortaría los lados)" % (a.id, w, h))
    rec.update(archivo=dst, credito=credito[:CREDITO_CARACTERES], origen=origen, url=url, tamano=[w, h],
               sha1=sha1_de(os.path.join(trabajo, dst)))
    escribir(os.path.join(trabajo, "fotos", a.id + ".json"), rec)
    print("foto %s · %d×%d · %s (%s) → %s" % (a.id, w, h, rec["credito"], origen, dst))
    return 0


def sha1_de(ruta):
    return hashlib.sha1(open(ruta, "rb").read()).hexdigest()


def encajar(ruta):
    """--encaje contener: rellena la imagen con el color de su esquina para que quepa entera, con el margen del Ken
    Burns, en el marco de 9:16 (≈ 1.11 de proporción) y en el de 4:5 (≈ 0.93). Sustituye el archivo."""
    w, h = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                            "stream=width,height", "-of", "csv=p=0:s=x", ruta],
                                           capture_output=True, text=True).stdout.strip().split("x")[:2])
    px = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-vf", "crop=2:2:0:0,scale=1:1", "-frames:v", "1", "-f",
                         "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout[:3]
    color = "0x%02x%02x%02x" % tuple(px) if len(px) == 3 else "white"
    ancho = 2 * round(ENCAJE_MARGEN * max(w, MARCO_ANCHO * h) / 2)
    alto = 2 * round(max(ancho / MARCO_ANGOSTO, ENCAJE_MARGEN * h) / 2)
    tmp = ruta + ".tmp.jpg"
    VD.ff("-i", ruta, "-vf", "pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=%s" % (ancho, alto, color), "-q:v", "3", tmp)
    os.replace(tmp, ruta)
    return ancho, alto


# ---------- H1–H3: hechos, cifras, citas, fotos y casos de un eje ----------
def texto_de(archivo):
    ruta = os.path.join(RAIZ, archivo or "")
    return plano(open(ruta, encoding="utf-8", errors="replace").read()) if archivo and os.path.isfile(ruta) else None


def encuadre(trabajo):
    ruta = os.path.join(trabajo, "encuadre.json")
    return leer(ruta) if os.path.exists(ruta) else {}


def revisar_fuentes(item, propios, fallas, avisos, etiqueta):
    """Cada fuente con su texto guardado y la cita literal dentro → [(clase, grupo, fecha)] de las que cuentan y el
    texto de todas."""
    validas, textos = [], []
    for f in item.get("fuentes") or []:
        t = texto_de(f.get("archivo"))
        if t is None:
            fallas.append("H2 %s: la fuente %s no tiene archivo local (python3 scripts/historia.py leer <url>)" % (etiqueta, f.get("url")))
            continue
        textos.append(t)
        c = plano(f.get("cita"))
        if len(c) < CITA_MIN or c not in t:
            fallas.append("H2 %s: la cita de %s no está en su texto guardado (cópiala tal cual, ≥ %d caracteres)"
                          % (etiqueta, f.get("medio") or NT.dominio(f.get("url")), CITA_MIN))
            continue
        clase, grupo = clasificar(f.get("url"), propios, f.get("archivo"))
        if clase is None:
            avisos.append("%s: %s no cuenta para confirmar (no es oficial, medio de la lista, academia, archivo ni la "
                          "empresa del encuadre)" % (etiqueta, NT.dominio(f.get("url"))))
            continue
        validas.append((clase, grupo, f))
    return validas, " ".join(textos)


def numeros_de(texto):
    """Los números de un texto que no son años ni enteros ≤ 12 (los que la voz o la pantalla deben respaldar)."""
    out = []
    for m in RE_NUMERO.finditer(texto or ""):
        v = float(m.group().replace(",", ""))
        if (v.is_integer() and (1500 <= v <= 2100 or v <= 12)):
            continue
        out.append((m.group(), v, texto[m.end():m.end() + 16]))
    return out


def revisar_eje(v, trabajo, propios):
    """H1–H3 sobre verificacion_<eje>.json → (fallas, avisos)."""
    fallas, avisos = [], []
    eje = v.get("eje") or "?"
    hechos = v.get("hechos") or []
    if not hechos:
        fallas.append("H1 %s: sin hechos" % eje)
    for h in hechos:
        hid, est = h.get("id") or "?", h.get("estado")
        if not re.fullmatch(r"%s-h\d{2}" % re.escape(eje), hid):
            fallas.append("H1 %s: id «%s» (va %s-h01, %s-h02…)" % (eje, hid, eje, eje))
        if est not in ESTADOS:
            fallas.append("H1 %s: estado confirmado | en_disputa | no_confirmado" % hid)
            continue
        if est == "no_confirmado":
            continue
        if not RE_FECHA.match(str(h.get("fecha") or "")) or h.get("precision") not in PRECISIONES:
            fallas.append("H1 %s: fecha YYYY[-MM[-DD]] y precision %s" % (hid, "|".join(PRECISIONES)))
        if not 10 <= len(h.get("texto") or "") <= HECHO_CARACTERES:
            fallas.append("H1 %s: texto de 10–%d caracteres (qué pasó, quién, dónde)" % (hid, HECHO_CARACTERES))
        validas, _ = revisar_fuentes(h, propios, fallas, avisos, hid)
        grupos = {g for _, g, _ in validas}
        if est == "confirmado" and len(grupos) < 2:
            fallas.append("H2 %s: confirmado pide 2 fuentes independientes (grupos distintos: un documento oficial, la "
                          "empresa o la academia y otra que lo respalde); tiene %s" % (hid, ", ".join(sorted(grupos)) or "ninguna válida"))
        if est == "en_disputa" and (not validas or len((h.get("nota") or "").strip()) < 10):
            fallas.append("H2 %s: en_disputa pide ≥ 1 fuente válida y una nota con la diferencia (la voz la atribuye o matiza)" % hid)
        anio = str(h.get("fecha") or "")[:4]
        citas = " ".join(plano(f.get("cita")) for _, _, f in validas)
        de_anio = [f for _, _, f in validas if anio and (anio in plano(f.get("cita")) or str(f.get("fecha") or "").startswith(anio))]
        if anio and h.get("precision") != "aprox" and not de_anio:
            fallas.append("H2 %s: el año %s no está en ninguna cita (ni es el año de publicación de la fuente): cita el "
                          "fragmento que lo dice o pon precision aprox" % (hid, anio))
        for tok, val, _ in numeros_de(h.get("texto")):
            if NT.sueltos(tok, [(round(float(m.group().replace(",", "")), 6), None) for m in RE_NUMERO.finditer(citas)]):
                fallas.append("H2 %s: el número «%s» del texto no está en sus citas" % (hid, tok))
    for c in v.get("cifras") or []:
        cid, est = c.get("id") or "?", c.get("estado")
        if not re.fullmatch(r"%s-c\d{2}" % re.escape(eje), cid):
            fallas.append("H1 %s: id «%s» (va %s-c01…)" % (eje, cid, eje))
        if est not in ESTADOS:
            fallas.append("H1 %s: estado confirmado | en_disputa | no_confirmado" % cid)
            continue
        if est == "no_confirmado":
            continue
        if not isinstance(c.get("valor"), (int, float)) or isinstance(c.get("valor"), bool):
            fallas.append("H1 %s: valor numérico" % cid)
            continue
        validas, _ = revisar_fuentes(c, propios, fallas, avisos, cid)
        grupos, clases = {g for _, g, _ in validas}, {k for k, _, _ in validas}
        if est == "confirmado" and len(grupos) < 2 and not clases & {"oficial", "academica"}:
            fallas.append("H2 %s: una cifra confirmada pide 2 fuentes independientes o una oficial o académica" % cid)
        if est == "en_disputa" and not validas:
            fallas.append("H2 %s: en_disputa pide ≥ 1 fuente válida" % cid)
        nums = [(round(float(m.group().replace(",", "")), 6), None) for _, _, f in validas for m in RE_NUMERO.finditer(f.get("cita") or "")]
        if NT.sueltos(c.get("texto") or "", [(round(float(c["valor"]), 6), VM.factor_unidad(c.get("unidad"))), (round(float(c["valor"]), 6), None)]):
            fallas.append("H2 %s: «%s» no es su valor %s" % (cid, c.get("texto"), c["valor"]))
        elif NT.sueltos(c.get("texto") or "", nums):
            fallas.append("H2 %s: ninguna cita trae el número «%s»" % (cid, c.get("texto")))
    for q in v.get("citas") or []:
        qid, est = q.get("id") or "?", q.get("estado")
        if not re.fullmatch(r"%s-q\d{2}" % re.escape(eje), qid):
            fallas.append("H1 %s: id «%s» (va %s-q01…)" % (eje, qid, eje))
        if est not in ESTADOS or est == "no_confirmado":
            continue
        frase = plano(q.get("texto"))
        if not (q.get("autor") or "").strip() or not (q.get("cuando") or "").strip():
            fallas.append("H1 %s: la cita lleva autor (persona o documento) y cuando" % qid)
        if not 10 <= len(q.get("texto") or "") <= CITA_FRASE_CARACTERES:
            fallas.append("H1 %s: la frase de 10–%d caracteres (literal: es lo que se lee en pantalla)" % (qid, CITA_FRASE_CARACTERES))
        if not any(frase and frase in (texto_de(f.get("archivo")) or "") for f in q.get("fuentes") or []):
            fallas.append("H2 %s: la frase no está literal en el texto guardado de ninguna de sus fuentes" % qid)
    for x in v.get("casos") or []:
        if not (x.get("persona") or "").strip() or not (x.get("estado_actual") or "").strip() or not RE_FECHA.match(str(x.get("fecha_consulta") or "")):
            fallas.append("H3 caso %s: persona, estado_actual (condenado, absuelto, proceso abierto, prófugo…) y fecha_consulta" % (x.get("persona") or "?"))
            continue
        f = x.get("fuente") or {}
        t = texto_de(f.get("archivo"))
        if t is None or len(plano(f.get("cita"))) < CITA_MIN or plano(f.get("cita")) not in t:
            fallas.append("H3 caso %s: el estado actual con su fuente guardada y la cita literal" % x["persona"])
    return fallas, avisos


def revisar_foto(rec, trabajo):
    f = []
    fid = rec.get("id") or "?"
    if not rec.get("archivo") or not os.path.exists(os.path.join(trabajo, rec["archivo"])):
        f.append("H7 %s: sin archivo en fotos/ (python3 scripts/historia.py foto …)" % fid)
    if not (rec.get("credito") or "").startswith("Foto: "):
        f.append("H7 %s: el crédito va «Foto: …»" % fid)
    if rec.get("origen") not in ORIGENES_FOTO:
        f.append("H7 %s: origen %s" % (fid, "|".join(ORIGENES_FOTO)))
    if rec.get("origen") == "commons" and not (LICENCIA_LIBRE.match(rec.get("licencia") or "") and not LICENCIA_NO.search(rec.get("licencia") or "")):
        f.append("H7 %s: licencia de Commons «%s» no libre" % (fid, rec.get("licencia")))
    if min(rec.get("tamano") or [0]) < FOTO_LADO_MIN:
        f.append("H7 %s: lado corto < %d px" % (fid, FOTO_LADO_MIN))
    return f


def cmd_hechos(a):
    trabajo = os.path.abspath(a.trabajo)
    enc = encuadre(trabajo)
    propios = enc.get("dominios_propios") or []
    rutas = [os.path.join(trabajo, "verificacion_%s.json" % a.eje)] if a.eje else sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))
    fallas, avisos, n, casos = [], [], 0, 0
    for r in rutas:
        if not os.path.exists(r):
            fallas.append("H1 falta %s" % VD.rel(r))
            continue
        v = leer(r)
        f, av = revisar_eje(v, trabajo, propios)
        fallas += f
        avisos += av
        casos += len(v.get("casos") or [])
        n += sum(1 for h in v.get("hechos") or [] if h.get("estado") in PUBLICABLES)
        for fid in v.get("fotos") or []:
            ruta_f = os.path.join(trabajo, "fotos", "%s.json" % fid)
            if not os.path.exists(ruta_f):
                fallas.append("H7 %s: falta fotos/%s.json (python3 scripts/historia.py foto …)" % (fid, fid))
            else:
                fallas += revisar_foto(leer(ruta_f), trabajo)
    if not a.eje and (enc.get("sensibles") or {}).get("justicia") and not casos:
        fallas.append("H3 historia de justicia: cada persona señalada lleva su estado del caso a la fecha de la consulta (casos[] "
                      "en la verificación de su eje)")
    for x in avisos:
        print("AVISO", x)
    for x in fallas:
        print("FALLA", x)
    if not fallas:
        print("H1–H3 ok · %d hecho(s) publicables en %d eje(s)" % (n, len(rutas)))
    return 1 if fallas else 0


# ---------- consolidar: historia.json, cronología y la base que respalda la voz ----------
def unidad_de(despues):
    d = (despues or "").strip().lower()
    return "miles de millones" if d.startswith("mil millones") else "millones" if re.match(r"mill[oó]n", d) else \
        "miles" if re.match(r"mil\b", d) else ""


def fundir_fotos(trabajo, recs):
    """{id: foto} sin repetidas: dos ids con la misma imagen (sha1 del jpg o misma url, p. ej. bajada por dos ejes) quedan
    en el primero, que anota los otros en `alias`."""
    fotos, vistos = {}, {}
    for rec in recs:
        ruta = os.path.join(trabajo, rec.get("archivo") or "")
        clave = rec.get("sha1") or (sha1_de(ruta) if rec.get("archivo") and os.path.isfile(ruta) else None)
        prev = vistos.get(clave) or vistos.get(rec.get("url"))
        if prev:
            fotos[prev].setdefault("alias", []).append(rec["id"])
            print("AVISO %s es la misma imagen que %s: queda %s" % (rec["id"], prev, prev))
            continue
        fotos[rec["id"]] = dict(rec, sha1=clave)
        for k in (clave, rec.get("url")):
            if k:
                vistos[k] = rec["id"]
    return fotos


def consolidar(trabajo):
    st = VD.estado(trabajo)
    enc = encuadre(trabajo)
    ejes = [leer(r) for r in sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))]
    fotos = fundir_fotos(trabajo, [leer(r) for r in sorted(glob.glob(os.path.join(trabajo, "fotos", "*.json")))])
    H = {"tema": st.get("tema"), "slug": st["slug"], "pregunta": enc.get("pregunta"), "arco": enc.get("arco"),
         "capitulos": enc.get("capitulos") or [], "no_afirma": enc.get("no_afirma") or [],
         "hechos": [], "cifras": [], "citas": [], "casos": [], "descartados": [], "fotos": fotos}
    for v in ejes:
        for k in ("hechos", "cifras", "citas"):
            for x in v.get(k) or []:
                (H[k] if x.get("estado") in PUBLICABLES else H["descartados"]).append(dict(x, eje=v.get("eje"), clase=k))
        H["casos"] += v.get("casos") or []
        H["descartados"] += [dict(x, eje=v.get("eje")) for x in v.get("descartados") or []]
    H["hechos"].sort(key=lambda h: (str(h.get("fecha")), h.get("id")))
    # conflictos de fecha: el mismo evento con fechas distintas en dos ejes (texto casi igual)
    conflictos = []
    for i, x in enumerate(H["hechos"]):
        for y in H["hechos"][i + 1:]:
            px, py = set(VD._plano(x.get("texto")).split()), set(VD._plano(y.get("texto")).split())
            if px and py and len(px & py) / min(len(px), len(py)) >= 0.7 and str(x.get("fecha"))[:4] != str(y.get("fecha"))[:4]:
                conflictos.append([x["id"], y["id"]])
    H["conflictos"] = conflictos
    escribir(os.path.join(trabajo, "historia.json"), H)
    # la base (hilo.json + datos.json) que leen el gate del guion, los ganchos y el cierre de video.py
    cifras = []
    for c in H["cifras"]:
        cifras.append({"id": c["id"], "concepto": c.get("concepto") or c.get("texto"), "valor": c["valor"], "unidad": c.get("unidad") or "",
                       "periodo": str(c.get("anio") or ""), "veredicto": "verificada", "url": ((c.get("fuentes") or [{}])[0]).get("url")})
    for x in H["hechos"] + H["citas"]:
        for k, (tok, val, despues) in enumerate(numeros_de(x.get("texto")), 1):
            cifras.append({"id": "%s-n%d" % (x["id"], k), "concepto": x.get("texto"), "valor": val, "unidad": unidad_de(despues),
                           "periodo": str(x.get("fecha") or x.get("cuando") or "")[:4], "veredicto": "verificada"})
    base = os.path.join(trabajo, "base")
    os.makedirs(base, exist_ok=True)
    paleta = enc.get("paleta") if enc.get("paleta") in paletas() else st["paleta"]
    hilo_b = leer(os.path.join(base, "hilo.json")) if os.path.exists(os.path.join(base, "hilo.json")) else {}
    hilo_b.update({"slug": st["slug"], "fecha": st.get("fecha"), "tema": st.get("tema") or enc.get("tema", ""),
                   "tesis": enc.get("resumen") or enc.get("pregunta") or "", "paleta": paleta, "estado": "listo",
                   "modo": "historia", "no_afirma": H["no_afirma"]})
    hilo_b.setdefault("tuits", [])
    escribir(os.path.join(base, "hilo.json"), hilo_b)
    escribir(os.path.join(base, "datos.json"), {"slug": st["slug"], "fecha": st.get("fecha"), "cifras": cifras})
    if paleta != st["paleta"]:
        st["paleta"] = paleta
        st["musica"] = elegir_musica(paleta, st.get("musica_forzada"))["id"]
        escribir(os.path.join(trabajo, "video.json"), st)
    return H


def cmd_consolidar(a):
    trabajo = os.path.abspath(a.trabajo)
    H = consolidar(trabajo)
    for h in H["hechos"]:
        print("%-9s %-11s %-10s %s" % (h["id"], h["estado"], h.get("fecha"), h.get("texto")))
    print("cifras %d · citas %d · fotos %d · casos %d · descartados %d" % (len(H["cifras"]), len(H["citas"]), len(H["fotos"]),
                                                                          len(H["casos"]), len(H["descartados"])))
    for x, y in H["conflictos"]:
        print("AVISO %s y %s parecen el mismo hecho con años distintos: deja uno o márcalo en_disputa" % (x, y))
    st = VD.estado(trabajo)
    print("→ %s · base %s · paleta %s · música %s" % (VD.rel(os.path.join(trabajo, "historia.json")), st["hilo"], st["paleta"], st["musica"]))
    if len(H["hechos"]) < HECHOS_MIN:
        return falla("H1 solo %d hechos publicables (van ≥ %d para contar una historia de 2–3 min)" % (len(H["hechos"]), HECHOS_MIN))
    return 0


def historia_de(trabajo):
    ruta = os.path.join(trabajo, "historia.json")
    if not os.path.exists(ruta):
        raise SystemExit(falla("falta historia.json: corre python3 scripts/historia.py consolidar %s" % VD.rel(trabajo)))
    return leer(ruta)


# ---------- extensión de video.py: escenas foto, cita y capitulo; gancho con foto; estructura de historia ----------
def aplicar_extension(trabajo):
    """Enchufa en video.py lo propio de /historia (una vez por proceso): los tipos de escena, su voz, sus tiempos y su
    transición; el gancho con visual foto y sus reglas; la estructura H8 en lugar de la de /video."""
    global TRABAJO_ACTUAL, H_ACTUAL
    TRABAJO_ACTUAL, H_ACTUAL = trabajo, historia_de(trabajo)
    if ORIGINALES:
        return
    ORIGINALES.update(visual=VD.visual_del_gancho, reglas=VD.reglas_gancho, estructura=VD.validar_estructura, colores=VD.colores)
    VD.TIPOS = VD.TIPOS + tuple(t for t in TIPOS_PROPIOS if t not in VD.TIPOS)
    VD.CARACTERES.update(CARACTERES)
    VD.SIN_HUECO = VD.SIN_HUECO + TIPOS_PROPIOS
    VD.ICONO_TIPOS = VD.ICONO_TIPOS + ("foto",)   # la foto sin imagen va con su icono (o el mapa)
    VD.visual_del_gancho = visual_del_gancho
    VD.reglas_gancho = reglas_gancho
    VD.validar_estructura = estructura
    VD.colores = colores_con_realce
    VD.CONSTRUCTORES.update(gancho=t_gancho, foto=t_foto, cita=t_cita, capitulo=t_capitulo)
    VD.TRANSICION_DE.update(foto="tarjeta", cita="texto", capitulo="completa")


def colores_con_realce(paleta):
    c = ORIGINALES["colores"](paleta)
    p = leer(os.path.join(RAIZ, "design", "tokens.json"))["paletas"][paleta]
    c["realce"] = next((p[k] for k in ("a1", "bg", "a3", "a2")
                        if VD.contraste(p[k], "#141414") >= 4.5 and VD.contraste(p[k], "#FFFFFF") >= 1.5), "#F6F2E8")
    return c


def fotos_h():
    return (H_ACTUAL or {}).get("fotos") or {}


def visual_del_gancho(e, cifras, valores):
    if (e.get("visual") or "cifra") != "foto":
        return ORIGINALES["visual"](e, cifras, valores)
    d = e.get("visual_datos") or {}
    fo, f = fotos_h().get(d.get("foto")), []
    if not fo:
        f.append("visual foto: «foto» «%s» no es una foto verificada (historia.json → fotos)" % d.get("foto"))
    et = (d.get("etiqueta") or "").strip()
    if len(et) > ETIQUETA_GANCHO:
        f.append("visual foto: «etiqueta» de ≤ %d caracteres (la época y el lugar: «Amatitlán · 2015»)" % ETIQUETA_GANCHO)
    return {"tipo": "foto", "foto": fo and fo.get("archivo"), "credito": fo and fo.get("credito"), "etiqueta": et, "numeros": []}, f


def reglas_gancho(e, voz_p, ctx):
    """R2–R9 de un gancho de historia (las familias de historia, el visual foto, sin R10: una historia puede abrir sin
    cifra) → (fallas, avisos)."""
    f, av = [], []
    fam, vis = e.get("familia"), e.get("visual") or "cifra"
    pant, lin, texto = e.get("pantalla") or "", e.get("linea") or "", VD.sin_pausas(e.get("texto") or "").strip()
    V_ = ctx.get("visual") or {}
    if fam not in FAMILIAS:
        return ["familia «%s» no es una familia de historia (%s)" % (fam, "|".join(FAMILIAS))], av
    if vis not in VISUALES_DE[fam]:
        f.append("el visual «%s» no va con la familia %s (admite %s)" % (vis, fam, ", ".join(VISUALES_DE[fam])))
    if e.get("icono") and vis != "cifra":
        f.append("el icono va solo con el visual cifra")
    silencio = " ".join((pant, lin))
    if vis == "cifra" and VD.numeros_sin_anios(silencio) and len(set(VD.numeros_sin_anios(silencio))) < 2 and not (
            VD.RE_DE_CADA.search(silencio) or re.search(r"×\s?\d|\d\s*veces\b|\bde\s+\d[\d,]*\b|\bpor\s+(?:cada\s+)?\w+", silencio, re.I)):
        f.append("R2 la cifra va sola en pantalla («%s»): dale un referente o usa la foto" % silencio.strip())
    if VD.APERTURAS_PROHIBIDAS.match(texto) or APERTURAS.match(texto):
        f.append("R3 la voz abre con contexto o con el anuncio de la historia («%s…»): abre con el momento más fuerte"
                 % " ".join(texto.split()[:4]))
    dichos = [pant, lin, voz_p]
    if vis in ("llenado", "pareja"):
        for v in [x for x in V_.get("numeros", []) if x is not None]:
            if not VD.escribe_numero(v, dichos):
                f.append("R4 el visual %s muestra %s y ni la voz ni la pantalla lo dicen" % (vis, VD.clave(v)))
    elif vis == "lugar" and V_.get("nombre") and VD._plano(V_["nombre"]) not in VD._plano(" ".join(dichos)):
        f.append("R4 el visual lugar señala %s y ni la voz ni la pantalla nombran el lugar" % V_["nombre"])
    if not VD.RE_GUATEMALA.search(" ".join((texto, pant, lin, V_.get("etiqueta") or ""))):
        e2 = ctx.get("e2")
        if e2 is None:
            av.append("R6 el gancho no dice «Guatemala»: dilo en la primera oración de la escena 2")
        elif not VD.RE_GUATEMALA.search(re.split(r"(?<=[.?!…])\s+", VD.sin_pausas(e2).strip())[0]):
            f.append("R6 «Guatemala» no se dice ni se lee en los primeros 6 s (gancho o primera oración de la escena 2)")
    m = VD.RE_AHORA.search(" ".join((texto, pant, lin)))
    if m:
        f.append("R7 «%s» en el gancho de una historia: di el año («en 2015…»), no «%s»" % (m.group(), m.group()))
    if fam == "pregunta":
        if not (pant.rstrip().endswith("?") or lin.rstrip().endswith("?")):
            f.append("R8 familia pregunta: pantalla o línea terminan en «?»")
        q = voz_p.rfind("?")
        if q < 0 or len(voz_p[q + 1:].strip()) < 12:
            f.append("R8 la pregunta se contesta en el mismo gancho (una oración después del «?»)")
    rec = ctx.get("recientes") or {}
    if fam in (rec.get("familias") or []):
        f.append("R9 la familia «%s» ya abrió una de las últimas %d historias (%s): usa otra" % (fam, ROTACION_FAMILIAS, ", ".join(rec["familias"])))
    if vis in (rec.get("visuales") or []):
        f.append("R9 el visual «%s» abrió la historia anterior: usa otro" % vis)
    return f, av


def estructura(g, st, dur, tarjetas):
    """V1/V9 de /video sin «la escena 2 es T1» + H8 (capítulos, variedad, giro) y las escenas propias."""
    f = [x for x in ORIGINALES["estructura"](g, st, dur, tarjetas)
         if not x.startswith(("V9 la escena 2 debe ser la tarjeta T1", "V9 escena 2: la primera tarjeta"))]
    escenas = g.get("escenas") or []
    H = H_ACTUAL or {}
    hechos = {h["id"]: h for h in H.get("hechos") or []}
    citas = {q["id"]: q for q in H.get("citas") or []}
    fotos = H.get("fotos") or {}
    tipos = [e.get("tipo") for e in escenas]
    if len(escenas) > ESCENAS_MAX:
        f.append("H8 %d escenas: van ≤ %d (más el cierre son los 20 nodos que ElevenLabs genera de una vez)" % (len(escenas), ESCENAS_MAX))
    caps = [k for k, t in enumerate(tipos) if t == "capitulo"]
    if not CAPITULOS[0] <= len(caps) <= CAPITULOS[1]:
        f.append("H8 %d capítulos; van %d–%d (cada uno abre con una escena capitulo)" % (len(caps), *CAPITULOS))
    if caps and caps[0] not in (1, 2):
        f.append("H8 el primer capítulo empieza en la escena 2 o 3 (tras el gancho y, si va, la promesa)")
    for j, k in enumerate(caps, 1):
        e = escenas[k]
        if e.get("numero") != j:
            f.append("H8 escena %d: capitulo numero %s (van 1, 2, 3… en orden)" % (k + 1, e.get("numero")))
        if k + 1 >= len(escenas) or tipos[k + 1] == "capitulo":
            f.append("H8 escena %d: un capítulo lleva al menos una escena después" % (k + 1))
        anio, tit = str(e.get("anio") or "").strip(), (e.get("titulo") or "").strip()
        if not anio or len(anio) > CAP_ANIO_CARACTERES:
            f.append("H8 escena %d: capitulo «anio» (el año o la época, ≤ %d caracteres)" % (k + 1, CAP_ANIO_CARACTERES))
        if not tit or VD.palabras(tit) > CAP_TITULO_PALABRAS or len(tit) > CAP_TITULO_CARACTERES:
            f.append("H8 escena %d: capitulo «titulo» de 1–%d palabras y ≤ %d caracteres" % (k + 1, CAP_TITULO_PALABRAS, CAP_TITULO_CARACTERES))
        if len(e.get("lugar") or "") > LUGAR_CARACTERES:
            f.append("H8 escena %d: «lugar» de ≤ %d caracteres" % (k + 1, LUGAR_CARACTERES))
    for k in range(SEGUIDAS_MAX, len(tipos)):
        if len(set(tipos[k - SEGUIDAS_MAX:k + 1])) == 1:
            f.append("H8 escenas %d–%d: %d escenas %s seguidas (máximo %d): alterna foto, cita, gráfico, golpe y explica"
                     % (k - SEGUIDAS_MAX + 1, k + 1, SEGUIDAS_MAX + 1, tipos[k], SEGUIDAS_MAX))
    giros = [k for k, e in enumerate(escenas) if e.get("giro")]
    if len(giros) != 1:
        f.append("H8 una escena con «giro»: true (el momento en que la historia cambia); llegaron %d" % len(giros))
    elif not GIRO_ENTRE[0] <= giros[0] / max(1, len(escenas) - 1) <= GIRO_ENTRE[1] or tipos[giros[0]] == "capitulo":
        f.append("H8 el giro (escena %d) va entre el %d y el %d %% del video y no en un capítulo"
                 % (giros[0] + 1, GIRO_ENTRE[0] * 100, GIRO_ENTRE[1] * 100))
    if not any(t in ("foto", "cita") for t in tipos):
        f.append("H8 una historia lleva al menos una escena foto o cita")
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        for hid in e.get("hechos") or []:
            if hid not in hechos:
                f.append("H4 escena %d: el hecho «%s» no está entre los publicables de historia.json" % (i, hid))
        if tipo == "foto":
            fid = e.get("foto")
            if fid is not None and fid not in fotos:
                f.append("H7 escena %d: la foto «%s» no está verificada (fotos/<id>.json)" % (i, fid))
            if fid is None and not (e.get("icono") or NT.depto_id(e.get("depto"))):
                f.append("H7 escena %d: sin foto, pon depto o icono para la tarjeta tipográfica" % i)
            if fid in fotos:
                f += fecha_contra_foto(i, e.get("fecha") or "", fotos[fid])
            tit = (e.get("titular") or "").strip()
            if not tit or VD.palabras(tit) > TITULAR_PALABRAS or len(tit) > TITULAR_CARACTERES:
                f.append("H6 escena %d: «titular» de 1–%d palabras y ≤ %d caracteres" % (i, TITULAR_PALABRAS, TITULAR_CARACTERES))
            if not (e.get("fecha") or "").strip() or len(e.get("fecha")) > CHIP_CARACTERES:
                f.append("H6 escena %d: «fecha» (la del chip: «Feb 2015», «1971») de 1–%d caracteres" % (i, CHIP_CARACTERES))
            if len(e.get("lugar") or "") > LUGAR_CARACTERES or len(e.get("fuente") or "") > FUENTE_CARACTERES:
                f.append("H6 escena %d: «lugar» ≤ %d y «fuente» ≤ %d caracteres" % (i, LUGAR_CARACTERES, FUENTE_CARACTERES))
            c = e.get("cifra")
            if c and (not re.search(r"\d", c.get("texto") or "") or len(c.get("texto") or "") > CIFRA_CARACTERES or len(c.get("etiqueta") or "") > ETIQUETA_CARACTERES):
                f.append("H6 escena %d: cifra {texto ≤ %d con dígitos, etiqueta ≤ %d}" % (i, CIFRA_CARACTERES, ETIQUETA_CARACTERES))
            if not e.get("hechos"):
                f.append("H4 escena %d: la foto cuenta un hecho: «hechos»: [ids]" % i)
        elif tipo == "cita":
            q = citas.get(e.get("cita"))
            if not q:
                f.append("H4 escena %d: la cita «%s» no está entre las verificadas" % (i, e.get("cita")))
                continue
            if VD._plano(q["texto"]) not in VD._plano(e.get("texto")):
                f.append("H4 escena %d: la voz lee la cita literal («%s»)" % (i, q["texto"][:60]))
            r = (e.get("resalte") or "").strip()
            if r and VD._plano(r) not in VD._plano(q["texto"]):
                f.append("H6 escena %d: «resalte» es un trozo literal de la cita" % i)
            if e.get("retrato") and e["retrato"] not in fotos:
                f.append("H7 escena %d: el retrato «%s» no está verificado" % (i, e["retrato"]))
            elif e.get("retrato") and VD._plano(fotos[e["retrato"]].get("retrato_de") or "") != VD._plano(q.get("autor") or ""):
                f.append("H7 escena %d: el retrato «%s» no es de %s (retrato_de: %s): un objeto o un lugar no va como "
                         "retrato; quítalo o usa una foto de esa persona" % (i, e["retrato"], q.get("autor"),
                                                                           fotos[e["retrato"]].get("retrato_de") or "ninguno"))
            if otro_idioma(q.get("texto")):
                tr = (e.get("traduccion") or "").strip()
                if not tr or len(tr) > TRADUCCION_CARACTERES:
                    f.append("H6 escena %d: la cita no está en español: «traduccion» (≤ %d caracteres) va en pantalla bajo "
                             "la frase y la voz la dice" % (i, TRADUCCION_CARACTERES))
                elif VD._plano(tr) not in VD._plano(e.get("texto")):
                    f.append("H6 escena %d: la voz dice la traducción tal cual («%s»)" % (i, tr[:50]))
            if len(e.get("fuente") or "") > FUENTE_CARACTERES:
                f.append("H6 escena %d: «fuente» ≤ %d caracteres" % (i, FUENTE_CARACTERES))
        elif tipo in VD.CON_TUIT:
            gr = e.get("grafico") or {}
            if not os.path.exists(os.path.join(RAIZ, "templates", "graficos", "%s.html" % gr.get("plantilla"))):
                f.append("H6 escena %d: «grafico.plantilla» «%s» no es una de templates/graficos/" % (i, gr.get("plantilla")))
            if not isinstance(gr.get("datos"), dict):
                f.append("H6 escena %d: «grafico.datos» (el contrato DATA de la plantilla: referencias/diseno/graficos.md)" % i)
    f += usos_de_fotos(escenas, fotos)
    avisar_flashbacks(escenas)
    return f


def usos_de_fotos(escenas, fotos):
    """H7: una misma imagen (por sha1, o alias de otra) en ≤ FOTO_USOS_MAX escenas, contando el gancho y los retratos."""
    clave = {}
    for fid, rec in fotos.items():
        for k in [fid] + (rec.get("alias") or []):
            clave[k] = rec.get("sha1") or fid
    usos = {}
    for i, e in enumerate(escenas, 1):
        for fid in (e.get("foto"), e.get("retrato"), (e.get("visual_datos") or {}).get("foto")):
            if fid:
                usos.setdefault(clave.get(fid, fid), []).append((i, fid))
    return ["H7 la misma foto (%s) sale en %d escenas (%s): van ≤ %d; usa otra, un mapa, un icono o un gráfico"
            % (u[0][1], len(u), ", ".join(str(i) for i, _ in u), FOTO_USOS_MAX) for u in usos.values() if len(u) > FOTO_USOS_MAX]


def fecha_contra_foto(i, chip, foto):
    """H7: el chip no le pone a la foto un año anterior a cuando se tomó (una foto de 2021 bajo «1978» parece de 1978):
    con una foto posterior, el chip dice su año («Foto de 2021»), «De referencia» o la época sin año."""
    m = RE_ANIO.search(str(foto.get("fecha") or ""))
    if not m or re.search(r"referencia|\bfoto\b", chip, re.I):
        return []
    previos = [y for y in RE_ANIO.findall(chip) if int(y) < int(m.group())]
    if previos and m.group() not in chip:
        return ["H7 escena %d: el chip dice «%s» pero la foto «%s» es de %s: pon «Foto de %s», «De referencia» o la "
                "época sin año" % (i, chip, foto.get("id"), m.group(), m.group())]
    return []


def avisar_flashbacks(escenas):
    """Aviso: un año anterior al del capítulo en que va la escena (el museo de 2019 dentro de «2021»)."""
    cap = None
    for i, e in enumerate(escenas, 1):
        if e.get("tipo") == "capitulo":
            m = RE_ANIO.search(str(e.get("anio") or ""))
            cap = int(m.group()) if m else None
            continue
        if cap:
            antes = sorted({y for y in RE_ANIO.findall(" ".join(str(e.get(k) or "") for k in ("texto", "fecha"))) if int(y) < cap})
            if antes:
                print("AVISO escena %d: %s es anterior al capítulo de %d (flashback): atribúyelo, dilo como recuerdo o "
                      "muévelo al capítulo que le toca" % (i, ", ".join(antes), cap))


def otro_idioma(texto):
    """Una cita que no está en español: más palabras vacías en inglés que en español (y al menos dos)."""
    ws = re.findall(r"[a-záéíóúñü']+", (texto or "").lower())
    en, es = sum(w in VACIAS_EN for w in ws), sum(w in VACIAS_ES for w in ws)
    return en >= 2 and en > es


# ---------- H4: años, atribución y presunción de inocencia en todo lo que se dice o se lee ----------
def anios_respaldados(H):
    out = {str(VD.ANIO)}
    for x in (H.get("hechos") or []) + (H.get("citas") or []):
        out |= set(RE_ANIO.findall(str(x.get("fecha") or x.get("cuando") or "")))
        out |= set(RE_ANIO.findall(x.get("texto") or ""))
        for f in x.get("fuentes") or []:
            out |= set(RE_ANIO.findall(f.get("cita") or ""))
    for c in H.get("cifras") or []:
        out |= set(RE_ANIO.findall(str(c.get("anio") or "")))
    for x in H.get("casos") or []:
        out |= set(RE_ANIO.findall(" ".join((x.get("estado_actual") or "", str(x.get("fecha_consulta") or "")))))
    return out


def revisar_verdad(g, H, valores):
    f = []
    anios = anios_respaldados(H)
    hechos = {h["id"]: h for h in H.get("hechos") or []}
    casos_firmes = {x.get("persona") for x in H.get("casos") or [] if x.get("sentencia_firme")}
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    for i, e in enumerate(escenas + [dict(cierre, tipo="cierre")], 1):
        textos = [e.get(k) or "" for k in ("texto", "pantalla", "linea", "golpe", "titular", "titulo", "fecha", "lugar", "fuente")]
        textos += [str(e.get("anio") or "")] + [(e.get("cifra") or {}).get(k) or "" for k in ("texto", "etiqueta")]
        textos += [" ".join(map(str, e.get("pasos") or [])), " ".join(e.get("resumen") or [])]
        todo = " ".join(textos)
        for y in sorted(set(RE_ANIO.findall(todo)) - anios):
            f.append("H4 escena %d: el año %s no está en ningún hecho, cita o cifra verificada" % (i, y))
        for campo in ("titular", "fecha", "lugar"):
            sin = VD.sin_respaldo(e.get(campo) or "", valores)
            if sin:
                f.append("H4 escena %d: %s «%s» con un número sin respaldo: %s" % (i, campo, e.get(campo), ", ".join(map(str, sin))))
        if e.get("cifra"):
            sin = VD.sin_respaldo(e["cifra"].get("texto") or "", valores)
            if sin:
                f.append("H4 escena %d: la cifra «%s» no tiene respaldo en las cifras ni en los hechos" % (i, e["cifra"].get("texto")))
        if any((hechos.get(h) or {}).get("estado") == "en_disputa" for h in e.get("hechos") or []) and not ATRIBUCION.search(e.get("texto") or ""):
            f.append("H4 escena %d: cuenta un hecho en disputa y la voz no atribuye ni matiza («según…», «a inicios de…»)" % i)
        m = NT.VETADAS.search(todo)
        if m and not (e.get("caso") and e["caso"] in casos_firmes):
            f.append("H3 escena %d: «%s» sin sentencia firme (presunción de inocencia: señalado, acusado, sindicado; con "
                     "sentencia firme, «caso»: <persona> de casos[] con sentencia_firme)" % (i, m.group()))
    cap = json.dumps(g.get("caption") or {}, ensure_ascii=False)
    for y in sorted(set(RE_ANIO.findall(cap)) - anios):
        f.append("H4 caption: el año %s no está en ningún hecho verificado" % y)
    if NT.VETADAS.search(cap):
        f.append("H3 caption: «%s» sin sentencia firme" % NT.VETADAS.search(cap).group())
    return f


# ---------- tarjetas: las escenas con gráfico → base/tuit_N.html ----------
def anios_grafico(datos):
    ets = [str(x) for x in (datos or {}).get("etiquetasX") or []]
    for k in ("antes", "despues"):
        if isinstance((datos or {}).get(k), dict):
            ets.append(str(datos[k].get("etiqueta", "")))
    return [m.group() for m in (VD.RE_ANIO.match(e.strip()) for e in ets) if m]


def construir_tarjetas(trabajo, g, st):
    """Materializa las escenas con `grafico` (tarjeta, mapa, ranking, tiempo, escala con tuit) en base/ y anota
    video.json.tarjetas; solo vuelve a renderizar si cambió algún gráfico. → lista de fallas."""
    base = os.path.join(trabajo, "base")
    tuits, vistos, f = [], set(), []
    for i, e in enumerate(g.get("escenas") or [], 1):
        if e.get("tipo") not in VD.CON_TUIT + ("escala",) or not isinstance(e.get("grafico"), dict):
            continue
        n = e.get("tuit")
        if not isinstance(n, int) or n < 1 or n in vistos:
            f.append("H6 escena %d: «tuit» entero ≥ 1 y único (el número de la tarjeta)" % i)
            continue
        vistos.add(n)
        tuits.append({"n": n, "visual": dict(e["grafico"], titular=e["grafico"].get("titular") or [e.get("golpe") or ""])})
    hilo_b = leer(os.path.join(base, "hilo.json"))
    nuevo = {"slug": st["slug"], "paleta": st["paleta"], "handle": "@DerekUrizar", "tuits": tuits}
    ruta_g = os.path.join(base, "guion.json")
    previo = leer(ruta_g) if os.path.exists(ruta_g) else None
    if tuits and (previo != nuevo or any(not os.path.exists(os.path.join(base, "tuit_%d.html" % t["n"])) for t in tuits)):
        escribir(ruta_g, nuevo)
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "materializar.py"), base], capture_output=True, text=True)
        if r.returncode:
            return f + ["H6 las tarjetas no pasan materializar.py (R1–R6): %s" % (r.stdout + r.stderr).strip()[-600:]]
        for t in tuits:
            for ext in ("html", "png"):
                shutil.copy2(os.path.join(base, "visuales", "tuit_%d.%s" % (t["n"], ext)), os.path.join(base, "tuit_%d.%s" % (t["n"], ext)))
    elif not tuits:
        escribir(ruta_g, nuevo)
    tarjetas = []
    for t in tuits:
        html_ = os.path.join(base, "tuit_%d.html" % t["n"])
        kicker, titular, nota = VD.titular_de(html_)
        datos = VD.datos_tarjeta(open(html_, encoding="utf-8").read())
        tarjetas.append({"n": t["n"], "plantilla": t["visual"].get("plantilla"), "titular": titular, "beat": None, "nota": nota,
                         "anios": anios_grafico(datos), "datos": datos})
    hilo_b["tuits"] = [{"n": t["n"], "imagen": "tuit_%d.png" % t["n"], "plantilla": t["visual"].get("plantilla"),
                        "cifra_ids": t["visual"].get("cifra_ids") or []} for t in tuits]
    escribir(os.path.join(base, "hilo.json"), hilo_b)
    st["tarjetas"] = tarjetas
    escribir(os.path.join(trabajo, "video.json"), st)
    return f


def cmd_tarjetas(a):
    trabajo = os.path.abspath(a.trabajo)
    f = construir_tarjetas(trabajo, leer(os.path.join(trabajo, "guion.json")), VD.estado(trabajo))
    for x in f:
        print("FALLA", x)
    st = VD.estado(trabajo)
    print("%d tarjeta(s) en %s" % (len(st["tarjetas"]), st["hilo"]))
    return 1 if f else 0


# ---------- gate del guion ----------
def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    try:
        g = leer(os.path.join(trabajo, "guion.json"))
    except (OSError, ValueError) as ex:
        return falla("guion.json ilegible: %s" % ex)
    st = VD.estado(trabajo)
    H = historia_de(trabajo)
    fallas = construir_tarjetas(trabajo, g, st)
    aplicar_extension(trabajo)
    valores, _, _ = VD.valores_respaldo(VD.estado(trabajo)["hilo"])
    fallas += revisar_verdad(g, H, valores)
    rc = VD.cmd_guion(argparse.Namespace(trabajo=trabajo, check=True))
    for x in fallas:
        print("FALLA", x)
    if fallas:
        loc = os.path.join(trabajo, "locucion.json")
        if rc == 0 and os.path.exists(loc):
            os.remove(loc)   # una locución que no pasó H3–H8 no se graba
        return 1
    if rc == 0:
        print("H3–H8 ok")
    return rc


def cmd_ganchos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    if a.check:
        a.usar = None
    return VD.cmd_ganchos(a)


# ---------- tiempos: los constructores de las escenas propias ----------
def escena_guion(S, g):
    es = g.get("escenas") or []
    return es[S["n"] - 1] if S["n"] - 1 < len(es) else {}


def t_gancho(S, e, ps, pal, fin_voz, dur, g):
    """El gancho con visual foto: video/noticia.html en modo titular (la foto a sangre, la pantalla en el chip, la línea
    entera desde el cuadro 0 encendiéndose con la voz). Otro visual sigue en video.py."""
    vis = e.get("visual") or {}
    if vis.get("tipo") != "foto":
        return None
    cin = e.get("cinetico") or {}
    fin_1 = VD.fin_oracion_desde(pal, 0)
    linea, _ = VD.alinear_linea((cin.get("linea") or "").split(), pal, 0.0, max(0.4, fin_1))
    S["pagina"] = "noticia"
    S["N"] = {"modo": "titular", "foto": vis.get("foto"), "credito": vis.get("credito"), "fecha": cin.get("pantalla") or "",
              "conteo": vis.get("etiqueta") or "", "titular": linea, "kb": NT.KEN_BURNS[0], "depto": None, "icono": None}
    S["T"] = {"pant": {"texto": cin.get("pantalla"), "v": None, "desde": 0.0, "hasta": 0.4, "pulso": None}, "linea": linea,
              "fin": round(fin_voz, 3)}
    ev = [(0.0, "titular"), (0.4, "cifra_fin")] + [(w["start"], "linea_dicha") for w in linea if w.get("dicha")]
    return ev, [(0.1, "impacto")]


def rellenar_huecos(latidos, ev, pal, dur, maximo=4.5):
    """Una oración larga deja la foto quieta: mientras quede un tramo de más de `maximo` s sin evento, la foto late
    también en una palabra de en medio (la que sigue a una coma, si hay)."""
    tras_coma = {round(pal[k + 1]["start"], 3) for k, x in enumerate(pal[:-1]) if x["text"].endswith((",", ";"))}
    for _ in range(12):
        ts = sorted(latidos | {t for t, _ in ev} | {dur})
        a, b = max(zip(ts, ts[1:]), key=lambda ab: ab[1] - ab[0])
        cands = [round(w["start"], 3) for w in pal if a + 1.0 < w["start"] < b - 1.0]
        if b - a <= maximo or not cands:
            return
        latidos.add(min(cands, key=lambda t: (t not in tras_coma, abs(t - (a + b) / 2))))


def t_foto(S, e, ps, pal, fin_voz, dur, g):
    """La escena foto: video/noticia.html en modo noticia (chip con la fecha y el lugar, la foto con Ken Burns y su
    crédito, el titular, la cifra si la hay y la fuente)."""
    esc = escena_guion(S, g)
    fo = fotos_h().get(esc.get("foto")) or {}
    t0 = VD.TRANSICION + 0.05
    N = {"modo": "noticia", "chip": {"b": esc.get("fecha") or "", "s": esc.get("lugar") or ""}, "foto": fo.get("archivo"),
         "credito": fo.get("credito"), "icono": esc.get("icono"), "depto": NT.depto_id(esc.get("depto")),
         "lugar": esc.get("lugar") if not fo.get("archivo") else None, "kb": NT.KEN_BURNS[(S["n"] - 1) % len(NT.KEN_BURNS)],
         "cifra": None, "fuente": None}
    N["titular"] = VD.repartir((esc.get("titular") or "").split(), t0 + 0.1, t0 + 1.2, minimo=0.08)
    ev = [(0.1, "entrada")] + [(w["start"], "titular") for w in N["titular"]]
    sfx = [(0.0, "grave" if S.get("enlace") == "pero" else "whoosh")]
    t_ult = N["titular"][-1]["start"] if N["titular"] else t0
    c = esc.get("cifra")
    if c:
        v = VD.valor_de(c.get("texto"))
        w = next((x for x in pal if v is not None and x.get("clave") == VD.clave(v)), None)
        start = max(t_ult + 0.4, w["start"] - 0.1) if w else min(t_ult + 1.2, fin_voz - 1.5)
        N["cifra"] = {"texto": c["texto"], "etiqueta": c.get("etiqueta") or "", "start": round(start, 3),
                      "pulso": [round(w["start"], 3), round(w["end"] + 0.2, 3)] if w else None}
        ev += [(start, "cifra"), (start + 0.9, "cifra_fin")]
        sfx.append((start, "tic"))
    if esc.get("fuente"):
        k_s = next((k for k, x in enumerate(pal) if NT.SEGUN.fullmatch(VD._plano(x["text"]) or "")), None)
        t_f = pal[k_s]["start"] if k_s is not None else max(t_ult + 1.0, 0.55 * fin_voz)
        if N["cifra"]:
            t_f = max(t_f, N["cifra"]["start"] + 1.2)
        t_f = min(t_f, dur - 1.0)
        N["fuente"] = {"texto": "Fuente: " + esc["fuente"], "start": round(t_f, 3)}
        ev.append((t_f, "fuente"))
        sfx.append((t_f, "pulso"))
    cifra_t = N["cifra"]["pulso"][0] if N["cifra"] and N["cifra"]["pulso"] else None
    latidos = {round(pal[k + 1]["start"], 3) for k, x in enumerate(pal[:-1]) if x["text"].endswith((".", "?", "!", ":"))} | \
        {round(x["start"], 3) for x in pal if x.get("clave") and x["start"] != cifra_t}
    rellenar_huecos(latidos, ev, pal, dur)
    N["oraciones"] = sorted(latidos)
    ev += [(x, "oracion") for x in N["oraciones"]]
    S["pagina"], S["N"], S["T"] = "noticia", N, {"tit": round(t0, 3)}
    return ev, sfx


def t_cita(S, e, ps, pal, fin_voz, dur, g):
    """La escena cita: video/historia.html (la frase entera apagada que se enciende con la voz; quién y cuándo; en un
    documento, el resaltador barre la parte clave)."""
    esc = escena_guion(S, g)
    q = next((x for x in (H_ACTUAL or {}).get("citas") or [] if x["id"] == esc.get("cita")), {})
    ws = (q.get("texto") or "").split()
    t0 = VD.TRANSICION + 0.1
    texto, _ = VD.alinear_linea(ws, pal, t0, max(t0 + 0.4, fin_voz - 0.3))
    resalte, resalte_t = None, None
    rw = [VD._norm(w) for w in (esc.get("resalte") or "").split()]
    qn = [VD._norm(w) for w in ws]
    for k in range(len(qn) - len(rw) + 1) if rw else []:
        if qn[k:k + len(rw)] == rw:
            resalte, resalte_t = [k, k + len(rw) - 1], round(texto[k]["start"], 3)
            break
    ret = fotos_h().get(esc.get("retrato")) or {}
    entra = 0.6
    fuente = {"texto": "Fuente: " + esc["fuente"], "start": round(min(max(2.0, 0.6 * fin_voz), dur - 1.0), 3)} if esc.get("fuente") else None
    S["pagina"] = "historia"
    S["H"] = {"texto": texto, "autor": q.get("autor"), "cargo": q.get("cargo"), "cuando": q.get("cuando"),
              "retrato": ret.get("archivo"), "credito": ret.get("credito"), "documento": bool(q.get("documento")),
              "membrete": q.get("membrete") or q.get("autor"), "resalte": resalte, "resalte_t": resalte_t,
              "fuente": fuente, "entra": entra, "traduccion": None}
    if (esc.get("traduccion") or "").strip() and texto:   # entra cuando la voz termina la frase original
        fin_q = texto[-1]["start"]
        t_tr = next((w["start"] for w in pal if w["start"] > fin_q + 0.05), max(fin_q + 0.4, fin_voz - 1.2))
        S["H"]["traduccion"] = {"texto": esc["traduccion"].strip(), "start": round(t_tr, 3)}
    S["T"] = {"ini": round(t0, 3)}
    ev = [(0.1, "entrada"), (entra, "firma")] + [(w["start"], "palabra") for w in texto if w.get("dicha")]
    sfx = [(0.0, "grave" if S.get("enlace") == "pero" else "whoosh")]
    if resalte_t is not None:
        ev += [(resalte_t, "resalte"), (resalte_t + 0.8, "resalte_fin")]
        sfx.append((resalte_t, "pulso"))
    if fuente:
        ev.append((fuente["start"], "fuente"))
    if S["H"]["traduccion"]:
        ev.append((S["H"]["traduccion"]["start"], "traduccion"))
    # mientras la voz narra antes de leer la cita, las comillas (o la hoja) laten al empezar cada oración
    latidos = {round(pal[k + 1]["start"], 3) for k, x in enumerate(pal[:-1]) if x["text"].endswith((".", "?", "!", ":"))}
    rellenar_huecos(latidos, ev, pal, dur)
    S["H"]["latidos"] = sorted(latidos)
    ev += [(x, "oracion") for x in latidos]
    return ev, sfx


def t_capitulo(S, e, ps, pal, fin_voz, dur, g):
    """El separador de capítulo: video/historia.html (el año cuenta desde el del capítulo anterior; el título entra con la
    voz; la línea de capítulos)."""
    es = g.get("escenas") or []
    esc = escena_guion(S, g)
    caps = [x for x in es if x.get("tipo") == "capitulo"]
    previos = [x for x in es[:S["n"] - 1] if x.get("tipo") == "capitulo"]
    hasta = str(esc.get("anio") or "").strip()
    desde = str(previos[-1].get("anio") or "").strip() if previos else None
    t0 = VD.TRANSICION + 0.1
    k = next((j for j, p in enumerate(ps) if p.get("seg") and p["seg"].get("num") and hasta and hasta in (p["seg"].get("p") or "")), None)
    t1 = min(max(t0 + 0.9, ps[k]["end"]), t0 + 2.2) if k is not None else t0 + 1.1
    titulo, _ = VD.alinear_linea((esc.get("titulo") or "").split(), pal, t1 + 0.1, max(t1 + 0.5, fin_voz - 0.2))
    S["pagina"] = "historia"
    S["H"] = {"numero": esc.get("numero"), "total": len(caps), "desde": desde, "hasta": hasta, "cuenta": [round(t0, 3), round(t1, 3)],
              "titulo": titulo, "lugar": esc.get("lugar") or ""}
    S["T"] = {"cuenta": [round(t0, 3), round(t1, 3)]}
    ev = [(t0, "cuenta"), (t1, "cuenta_fin")] + [(w["start"], "titulo") for w in titulo]
    if esc.get("lugar") and titulo:
        ev.append((titulo[-1]["start"] + 0.2, "lugar"))
    return ev, [(0.0, "whoosh"), (t1, "resolucion")]


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    rc = VD.cmd_tiempos(argparse.Namespace(trabajo=trabajo))
    if rc:
        return rc
    ruta = os.path.join(trabajo, "escenas.json")
    E = leer(ruta)
    g = leer(os.path.join(trabajo, "guion.json"))
    E["tipo"] = "historia"
    E["cierre"]["rotulo"] = (g.get("cierre") or {}).get("rotulo") or "Lo que dejó"
    escribir(ruta, E)
    if E["total_s"] + VD.BUCLE_S > DURACION_MAX_S:
        print("AVISO H5 duración real %.1f s: pasa de %d s (el tope de YouTube Shorts)" % (E["total_s"] + VD.BUCLE_S, DURACION_MAX_S))
    return 0


# ---------- digestos ----------
def lineas_hechos(H, con_citas=True):
    out = []
    for h in H.get("hechos") or []:
        fs = " · ".join("%s" % (f.get("medio") or NT.dominio(f.get("url"))) for f in h.get("fuentes") or [])
        out.append("- %s · %s (%s) · %s%s — %s [%s]" % (h["id"], h.get("fecha"), h.get("precision"), h["estado"],
                   " (" + h["nota"] + ")" if h["estado"] == "en_disputa" and h.get("nota") else "", h.get("texto"), fs))
    return out


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    enc = encuadre(trabajo)
    if a.para in ("investigador", "verificador"):
        eje = next((x for x in enc.get("ejes") or [] if x.get("id") == a.eje), None)
        if not eje:
            return falla("el encuadre no tiene el eje «%s»" % a.eje)
        out = ["# %s · eje %s (%s)" % (st.get("tema"), eje["id"], eje.get("nombre")), "",
               "- Pregunta de la historia: %s" % enc.get("pregunta"), "- Arco: %s" % enc.get("arco"),
               "- Capítulos del eje: %s" % ", ".join("%s (%s)" % (c.get("titulo"), c.get("periodo")) for c in enc.get("capitulos") or []
                                                    if c.get("n") in (eje.get("capitulos") or [])),
               "- Qué buscar: %s" % "; ".join(eje.get("preguntas") or []),
               "- Fuentes sugeridas: %s" % "; ".join(eje.get("fuentes") or []),
               "- Dominios de la empresa o institución protagonista (cuentan como fuente propia): %s" % ", ".join(enc.get("dominios_propios") or []) or "—",
               "- No afirma: %s" % "; ".join(enc.get("no_afirma") or []),
               "- Sensible: %s" % json.dumps(enc.get("sensibles") or {}, ensure_ascii=False), ""]
        if a.para == "verificador":
            ruta = os.path.join(trabajo, "hallazgos_%s.json" % a.eje)
            if not os.path.exists(ruta):
                return falla("falta %s" % VD.rel(ruta))
            hz = leer(ruta)
            out += ["## Hallazgos del investigador (verifícalos uno por uno)"]
            for k in ("hechos", "cifras", "citas"):
                for x in hz.get(k) or []:
                    out.append("- %s · %s · %s — %s" % (x.get("id"), x.get("fecha") or x.get("cuando") or x.get("anio") or "", (x.get("texto") or "")[:200],
                               " | ".join("%s «%s»" % (ev.get("url"), (ev.get("cita") or "")[:140]) for ev in x.get("evidencia") or x.get("fuentes") or [])))
            out += ["- foto candidata %s · %s · %s" % (x.get("id"), x.get("descripcion"), x.get("commons") or x.get("url")) for x in hz.get("fotos") or []]
        out += ["", "## Clases de fuente que cuentan", "- oficial: *.gob.gt, %s, %s" % (", ".join(sorted(NT.OFICIALES)), ", ".join(sorted(OTROS_OFICIALES))),
                "- medio (dominio → grupo): %s" % ", ".join("%s→%s" % kv for kv in sorted({**NT.MEDIOS, **INTERNACIONALES}.items())),
                "- academica: *.edu, %s · archivo: %s (Wayback cuenta como su original)" % (", ".join(sorted(ACADEMICAS)), ", ".join(sorted(ARCHIVOS))),
                "- Wikipedia NO cuenta: úsala para llegar a sus referencias."]
        print("\n".join(out))
        return 0
    H = historia_de(trabajo)
    rec_g = st.get("ganchos_recientes") or {}
    base = ["# Historia · %s (paleta %s, música %s)" % (st.get("tema"), st["paleta"], st["musica"]), "",
            "- Pregunta: %s · arco: %s" % (H.get("pregunta"), H.get("arco")),
            "- Capítulos del encuadre: %s" % " · ".join("%s. %s (%s)" % (c.get("n"), c.get("titulo"), c.get("periodo")) for c in H.get("capitulos") or []),
            "- No afirma: %s" % "; ".join(H.get("no_afirma") or []), "", "## Cronología verificada (id · fecha · estado — hecho [fuentes])"] + \
        lineas_hechos(H) + (["", "## Conflictos de fecha"] + ["- %s y %s" % tuple(x) for x in H["conflictos"]] if H.get("conflictos") else []) + \
        ["", "## Cifras (id · texto · valor)"] + ["- %s · %s · %s %s (%s)" % (c["id"], c.get("texto"), c["valor"], c.get("unidad", ""), c.get("anio") or "")
                                                for c in H.get("cifras") or []] + \
        ["", "## Citas literales (id · quién · cuándo — frase)"] + ["- %s · %s%s · %s%s — «%s»" % (q["id"], q.get("autor"), ", " + q["cargo"] if q.get("cargo") else "",
                                                                    q.get("cuando"), " · documento" if q.get("documento") else "", q.get("texto"))
                                                                    for q in H.get("citas") or []] + \
        ["", "## Fotos verificadas (id · qué muestra · crédito · origen)"] + ["- %s · %s · %s (%s)%s" % (k, f.get("descripcion"), f.get("credito"), f.get("origen"),
                                                                              " · %s %s" % (f.get("fecha") or "", f.get("lugar") or "") if f.get("fecha") or f.get("lugar") else "")
                                                                              for k, f in sorted((H.get("fotos") or {}).items())] + \
        (["", "## Casos (estado a la fecha de consulta)"] + ["- %s: %s (consultado %s)%s" % (x.get("persona"), x.get("estado_actual"), x.get("fecha_consulta"),
                                                            " · sentencia firme" if x.get("sentencia_firme") else "") for x in H.get("casos") or []]
         if H.get("casos") else [])
    if a.para == "gancho":
        out = base + ["", "## Ganchos de historia (4–5 candidatos de familias distintas; ≥ 2 con visual que no sea la cifra)",
                      "- Familias: %s" % ", ".join(FAMILIAS),
                      "- Visuales por familia: %s" % " · ".join("%s → %s" % (k, "|".join(v)) for k, v in VISUALES_DE.items()),
                      "- Visual foto: `visual_datos: {\"foto\": \"<id de foto>\", \"etiqueta\": \"<lugar · año>\" (≤ %d)}`: la foto a sangre, "
                      "`pantalla` en el chip y `linea` entera desde el cuadro 0, que se enciende cuando la voz la dice." % ETIQUETA_GANCHO,
                      "- Bloqueadas por rotación: familias %s · visual %s" % (", ".join(rec_g.get("familias") or []) or "ninguna",
                                                                        ", ".join(rec_g.get("visuales") or []) or "ninguno"),
                      "- Sin cifra obligatoria (una historia puede abrir con el hecho), pero cada número dicho tiene respaldo. Cada año dicho está en un hecho.",
                      "- La voz no abre con «Esta es la historia de…», «Te cuento…», «En el año…» ni con contexto: abre con el momento más fuerte."]
        print("\n".join(out))
        return 0
    out = base + ["", "## Límites del guion (historia.py guion --check: H3–H8 + V1–V5, V9, F1–F8 de video.py)",
                  "- Duración %d s ±20 %% (máximo %d s, el tope de Shorts); voz por escena: gancho %d–%d · foto %d–%d · cita %d–%d · capitulo %d–%d · "
                  "tarjeta %d–%d · golpe %d–%d · explica %d–%d · cierre %d–%d caracteres (ya en palabras; %.1f car/s)"
                  % (OBJETIVO_S, DURACION_MAX_S, *VD.CARACTERES["gancho"], *CARACTERES["foto"], *CARACTERES["cita"], *CARACTERES["capitulo"],
                     *VD.CARACTERES["tarjeta"], *VD.CARACTERES["golpe"], *VD.CARACTERES["explica"], *VD.CARACTERES["cierre"], VD.CPS),
                  "- %d–%d capítulos (escena capitulo: numero, anio ≤ %d, titulo ≤ %d palabras, lugar); el primero en la escena 2 o 3"
                  % (*CAPITULOS, CAP_ANIO_CARACTERES, CAP_TITULO_PALABRAS),
                  "- Nunca %d escenas del mismo tipo seguidas; una escena con giro: true entre el %d y el %d %%"
                  % (SEGUIDAS_MAX + 1, GIRO_ENTRE[0] * 100, GIRO_ENTRE[1] * 100),
                  "- foto: foto (id) o null con depto/icono, fecha (chip ≤ %d), lugar ≤ %d, titular ≤ %d palabras, hechos [ids], cifra? {texto, etiqueta}, fuente? ≤ %d"
                  % (CHIP_CARACTERES, LUGAR_CARACTERES, TITULAR_PALABRAS, FUENTE_CARACTERES),
                  "- cita: cita (id), la voz la lee literal; resalte? (trozo literal), retrato? (id de foto), fuente?",
                  "- tarjeta/mapa/ranking/tiempo: tuit (1, 2…), golpe ≤ %d palabras, grafico {plantilla de templates/graficos/, kicker, titular, nota, fuente, datos}"
                  % VD.GOLPE_PALABRAS,
                  *VD.lineas_animaciones(st.get("animaciones_recientes") or []),
                  "- Cierre: rotulo («Lo que dejó»…), resumen %d–%d líneas ≤ %d, texto, tipo, forma, final, consecuencia (F1–F8)"
                  % (*VD.RESUMEN_LINEAS, VD.RESUMEN_CARACTERES), "", "## Frases ya usadas (C11)"] + VD.frases_usadas(st["slug"]) + frases_historias(st["slug"])
    print("\n".join(out))
    return 0


# ---------- fotos-contacto y reenvío ----------
def cmd_fotos_contacto(a):
    return NT.cmd_fotos_contacto(a)


# ---------- entrega: historias/<fecha>-<slug>/ ----------
SALIDA_ENTREGA = ("video.mp4", "video_4x5.mp4", "subtitulos.srt", "caption.md", "portada.png")


def fotos_de_escena(e):
    return [x for x in (e.get("foto"), e.get("retrato"), (e.get("visual_datos") or {}).get("foto")) if x]


def cmd_entregar(a):
    """Copia la historia a historias/<fecha>-<slug>/ (o --salida) con guion.json de entrega, fuentes.md y cronologia.md.
    Las fotos no se copian (son de terceros y quedan en sesiones/). No vuelve a correr los gates: entrega lo grabado."""
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    sal = os.path.join(trabajo, "salida")
    for f in SALIDA_ENTREGA:
        if not os.path.exists(os.path.join(sal, f)):
            return falla("falta salida/%s: graba, monta y revisa (también --formato 4:5) antes de entregar" % f)
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    if not os.path.exists(ruta_cred) and not a.salida:
        return falla("sin audio/creditos.json: la voz no salió de ElevenLabs (una maqueta o una voz falsa solo se entrega con --salida)")
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, "historias", "%s-%s" % (st["fecha"], st["slug"])))
    os.makedirs(destino, exist_ok=True)
    for f in glob.glob(os.path.join(destino, "portada*.png")):
        os.remove(f)
    for f in list(SALIDA_ENTREGA) + [os.path.basename(x) for x in glob.glob(os.path.join(sal, "portada_*.png"))]:
        shutil.copy2(os.path.join(sal, f), os.path.join(destino, f))
    for f in ("contacto.png", "contacto_4x5.png"):
        if os.path.exists(os.path.join(trabajo, "revision", f)):
            shutil.copy2(os.path.join(trabajo, "revision", f), os.path.join(destino, f))
    g, H = leer(os.path.join(trabajo, "guion.json")), historia_de(trabajo)
    loc, E = leer(os.path.join(trabajo, "locucion.json")), leer(os.path.join(trabajo, "escenas.json"))
    escenas_g, fotos = g.get("escenas") or [], H.get("fotos") or {}
    critica, rc = None, os.path.join(trabajo, "critica.json")
    if os.path.exists(rc):
        c = leer(rc)
        critica = {"veredicto": c.get("veredicto"), "vuelta": c.get("vuelta"), "puntajes": c.get("puntajes")}
    else:
        print("AVISO sin critica.json: la historia se entrega sin la revisión del crítico")
    credito = lambda fid: {k: (fotos.get(fid) or {}).get(k) for k in ("credito", "origen", "licencia")} if fid in fotos else None  # noqa: E731
    escenas = []
    for e, s_ in zip(loc["escenas"], E["escenas"]):
        eg = escenas_g[e["n"] - 1] if e["n"] - 1 < len(escenas_g) else {}
        escenas.append({"n": e["n"], "tipo": e["tipo"], "pantalla": e.get("pantalla"), "voz": e.get("voz"), "dur": s_["dur"],
                        "hechos": eg.get("hechos") or [], "fotos": [credito(x) for x in fotos_de_escena(eg) if credito(x)],
                        "animacion": eg.get("animacion"), "mecanismo": eg.get("mecanismo")})
    e1 = escenas_g[0] if escenas_g else {}
    entrega = {
        "id": "%s-%s" % (st["fecha"], st["slug"]), "tipo": "historia", "slug": st["slug"], "tema": st.get("tema"),
        "fecha": st["fecha"], "pregunta": H.get("pregunta"), "arco": H.get("arco"),
        "capitulos": [{"numero": e.get("numero"), "anio": e.get("anio"), "titulo": e.get("titulo")} for e in escenas_g if e.get("tipo") == "capitulo"],
        "paleta": st["paleta"], "musica": st["musica"], "voz": loc["voz"], "velocidad": VD.VELOCIDAD,
        "creditos_voz": leer(ruta_cred)["total"] if os.path.exists(ruta_cred) else None,
        "duracion_s": round(VD.ffprobe_dur(os.path.join(destino, "video.mp4")), 1), "critica": critica,
        "gancho": {k: e1.get(k) for k in ("familia", "visual", "pantalla", "linea")}, "promesa": g.get("promesa"),
        "escenas": escenas, "cierre": g.get("cierre"), "caption": g.get("caption")}
    escribir(os.path.join(destino, "guion.json"), entrega)
    open(os.path.join(destino, "fuentes.md"), "w", encoding="utf-8").write(fuentes_md(st, escenas_g, H))
    open(os.path.join(destino, "cronologia.md"), "w", encoding="utf-8").write(cronologia_md(st, escenas_g, H))
    print("entregado en %s (%.1f s) · video.mp4 (TikTok, Reels, Shorts) + video_4x5.mp4 (feed) · caption.md · fuentes.md · "
          "cronologia.md%s" % (VD.rel(destino), entrega["duracion_s"],
                               "" if entrega["creditos_voz"] is None else " · %s créditos de voz" % entrega["creditos_voz"]))
    if entrega["duracion_s"] > DURACION_MAX_S:
        print("AVISO dura %.0f s: pasa de %d s (YouTube lo publica como video normal, no como Short)" % (entrega["duracion_s"], DURACION_MAX_S))
    return 0


def usados(escenas, H):
    """Los hechos y las citas que cuenta el guion, por capítulo: [(rótulo del capítulo, [hechos y citas])]."""
    hechos = {x["id"]: x for x in (H.get("hechos") or []) + (H.get("citas") or [])}
    bloques, vistos = [("Gancho y promesa", [])], set()
    for e in escenas:
        if e.get("tipo") == "capitulo":
            bloques.append(("Capítulo %s · %s · %s" % (e.get("numero"), e.get("anio"), e.get("titulo")), []))
        for hid in (e.get("hechos") or []) + ([e["cita"]] if e.get("cita") else []):
            if hid in hechos and hid not in vistos:
                vistos.add(hid)
                bloques[-1][1].append(hechos[hid])
    return [b for b in bloques if b[1]]


def fuentes_md(st, escenas, H):
    L = ["# Fuentes · %s" % st.get("tema"), "",
         "Para la descripción o el primer comentario. Cada hecho que cuenta el video con las fuentes que lo respaldan; "
         "lo que está «en disputa» la voz lo atribuye.", ""]
    for rotulo, xs in usados(escenas, H):
        L += ["## %s" % rotulo, ""]
        for x in xs:
            L.append("- %s%s" % (x.get("texto"), "" if x.get("estado") == "confirmado" else " *(en disputa)*"))
            urls = dict.fromkeys(f["url"] for f in x.get("fuentes") or [] if f.get("url"))
            medio = {f["url"]: f.get("medio") or NT.dominio(f["url"]) for f in x.get("fuentes") or [] if f.get("url")}
            L += ["  - %s: %s" % (medio[u], u) for u in urls]
        L.append("")
    fotos = H.get("fotos") or {}
    ids = []
    for e in escenas:
        ids += [x for x in fotos_de_escena(e) if x in fotos and x not in ids]
    if ids:
        L += ["## Fotos", ""]
        L += ["- %s · %s · %s" % (fotos[x].get("credito"), fotos[x].get("licencia"), fotos[x].get("pagina") or fotos[x].get("url")) for x in ids]
        L.append("")
    L.append("Sígueme: %s" % " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES))
    return "\n".join(L) + "\n"


def cronologia_md(st, escenas, H):
    xs = sorted([x for _, b in usados(escenas, H) for x in b], key=lambda x: (str(x.get("fecha") or x.get("cuando") or ""), x["id"]))
    L = ["# Cronología verificada · %s" % st.get("tema"), "", "La línea de tiempo de lo que cuenta el video (%s)." % st["fecha"], ""]
    for x in xs:
        medios = ", ".join(dict.fromkeys(f.get("medio") or NT.dominio(f.get("url")) for f in x.get("fuentes") or []))
        quien = "%s: «%s»" % (x.get("autor"), x.get("texto")) if x.get("autor") else x.get("texto")
        estado = "confirmado" if x.get("estado") == "confirmado" else "en disputa%s" % (" — %s" % x["nota"] if x.get("nota") else "")
        L.append("- **%s** · %s · %s · %s" % (x.get("fecha") or x.get("cuando") or "s. f.", quien, estado, medios))
    if H.get("conflictos"):
        L += ["", "## Fechas en conflicto", ""] + ["- %s y %s: el mismo hecho con años distintos" % tuple(c) for c in H["conflictos"]]
    return "\n".join(L) + "\n"


REENVIO = ("voz", "voz-falsa", "descargar", "escuchar", "grabar", "montar", "revisar")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in REENVIO:
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video.py")] + sys.argv[1:], cwd=RAIZ).returncode
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("preparar")
    q.add_argument("tema")
    q.add_argument("--slug")
    q.add_argument("--trabajo")
    q.add_argument("--paleta")
    q.add_argument("--musica")
    q.add_argument("--fixture", action="store_true", help="la maqueta de sesiones/_fixture_historia (sin web)")
    q = sub.add_parser("leer")
    q.add_argument("url")
    q.add_argument("--buscar")
    q.add_argument("--otra-vez", action="store_true")
    sub.add_parser("commons").add_argument("busqueda")
    q = sub.add_parser("foto")
    q.add_argument("trabajo")
    q.add_argument("--id", required=True)
    q.add_argument("--commons")
    q.add_argument("--url")
    q.add_argument("--credito")
    q.add_argument("--origen", choices=["oficial", "medio", "empresa"])
    q.add_argument("--descripcion")
    q.add_argument("--fecha")
    q.add_argument("--lugar")
    q.add_argument("--retrato-de", help="si es el retrato de una persona, su nombre (el de la cita); un objeto o un lugar no lo lleva")
    q.add_argument("--encaje", choices=["contener"], help="gráfico, cartel o logo con texto: márgenes para que el marco no lo recorte")
    q.add_argument("--extmetadata", help="pruebas: extmetadata de Commons guardado (solo comprueba la licencia, sin red)")
    q = sub.add_parser("hechos")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--eje")
    sub.add_parser("consolidar").add_argument("trabajo")
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--para", choices=["investigador", "verificador", "gancho", "guionista", "critico"], default="guionista")
    q.add_argument("--eje")
    q = sub.add_parser("ganchos")
    q.add_argument("trabajo")
    x = q.add_mutually_exclusive_group(required=True)
    x.add_argument("--check", action="store_true")
    x.add_argument("--usar", nargs="?", const="")
    q.add_argument("--segundo")
    sub.add_parser("tarjetas").add_argument("trabajo")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    sub.add_parser("tiempos").add_argument("trabajo")
    sub.add_parser("fotos-contacto").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida", help="otra carpeta (pruebas, maqueta o voz falsa)")
    for nombre in REENVIO:
        sub.add_parser(nombre, help="→ scripts/video.py %s" % nombre)
    a = p.parse_args()
    return {"preparar": cmd_preparar, "leer": cmd_leer, "commons": cmd_commons, "foto": cmd_foto, "hechos": cmd_hechos,
            "consolidar": cmd_consolidar, "digesto": cmd_digesto, "ganchos": cmd_ganchos, "tarjetas": cmd_tarjetas,
            "guion": cmd_guion, "tiempos": cmd_tiempos, "fotos-contacto": cmd_fotos_contacto, "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
