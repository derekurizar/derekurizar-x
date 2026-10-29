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
  foto TRABAJO --id ID (--commons "File:…" | --de-fuente URL | --url U --credito "Foto: …" --origen oficial|medio|empresa) --descripcion D
        [--referencia | --protagonista] [--fecha F] [--lugar L] [--retrato-de PERSONA] [--encaje contener] [--extmetadata JSON]
        (--de-fuente: la og:image de una fuente ya leída, con «Foto: <medio>» y la fecha de la nota; --protagonista: la foto
        muestra al protagonista del encuadre, H12 la exige en el gancho)
        baja la foto, comprueba lado y licencia (H7) → fotos/<id>.jpg + .json (con su sha1; un gráfico o cartel con
        texto va con --encaje contener: márgenes del color de su borde para que la foto a sangre no lo recorte)
  hechos TRABAJO --check [--eje E]   H1–H3 + H7 + H12 sobre verificacion_<eje>.json (citas en el texto guardado, fechas,
        independencia, fotos; sin --eje exige una foto del protagonista e imprime las og:image candidatas de las fuentes leídas)
  hechos TRABAJO --reclasificar [--aplicar]   los en_disputa de un solo grupo sin discrepancia en la nota → una_fuente (v3)
  encuadre TRABAJO --check     la estructura por actos del encuadre (actos, espina, hilos, personajes, periodos)
  consolidar TRABAJO           verificaciones + fotos → historia.json, base/ (hilo.json, datos.json) y la paleta del encuadre
  digesto TRABAJO --para investigador|verificador --eje E | gancho | guionista | critico | oyente | editor
        (oyente: la narración de corrido y luego la voz con lo que hay en pantalla, sin cronología ni ids; editor: re-encuadre)
  ganchos TRABAJO --check | --usar [ID] [--segundo ID]   → video.py ganchos con las familias y el visual foto de historia
  narracion TRABAJO [--check]  mide guion.narracion (palabras, segundos, conectores, «según», personajes, hilos) ANTES de
        repartirla en escenas; --check falla con H16–H19 sobre la narración sola
  tarjetas TRABAJO             las escenas con gráfico → base/tuit_N.html (materializar.py, R1–R6) y video.json.tarjetas
  guion TRABAJO --check        H4–H20 + (tarjetas) + video.py guion (V1–V5, V9, F1–F8) → locucion.json; la última línea
        RETORNO {...} es lo que el guionista devuelve al Workflow (tipos de cada escena, sin el cierre); deriva las
        secuencias de voz si el guion no las trae
  tiempos TRABAJO              video.py tiempos con los constructores de foto, cita y capitulo (y el rótulo de acto) → escenas.json
  fotos-contacto TRABAJO       fotos/contacto.png con todas las fotos (QA de contenido)
  entregar TRABAJO [--salida DIR]   → historias/<fecha>-<slug>/ (video, 4:5, caption, fuentes.md, cronologia.md, guion.json)
  voz [--pendientes [--sueltas] | --solo N,N] | voz-falsa | descargar | partir | escuchar | grabar | montar | revisar TRABAJO [...]   → video.py
        (voz: un nodo por secuencia de 2–5 escenas (la voz de corrido) más las sueltas; --pendientes: solo lo que cambió o
        falta, la secuencia entera si cambió una escena; --sueltas: solo esas escenas como nodos propios; descargar --estado
        corta cada secuencia en sus escenas; partir rehace el corte)

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import contextlib
import datetime
import glob
import hashlib
import html
import io
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
OBJETIVO_MIN_S, OBJETIVO_AVISO_S = 135, 165  # «apunta a 150 (135–165)»: el gate avisa (H5) si pasa de 165; 180 es para emergencias
VD.DURACIONES["historia"] = {"s": OBJETIVO_S, "tarjetas": (0, 6), "golpes": (0, 10), "tol": 0.2}   # V4: 120–180 s
# la narración de corrido (v3, 2026-10-27): la voz real va a ≈ 145 palabras por minuto (medido: 416 palabras en 172 s),
# así que 150 s son ≈ 360 palabras; PALABRAS orienta (aviso fuera), PALABRAS_DURO falla
PALABRAS, PALABRAS_DURO = (320, 400), (280, 430)
TIPOS_PROPIOS = ("foto", "cita", "capitulo")
CARACTERES = {"foto": (40, 280), "cita": (30, 280), "capitulo": (10, 90)}   # voz ya en palabras (≈ 15.5 car/s)
# en historia una tarjeta o un golpe pueden sostener un tramo más largo de narración que en /video
CARACTERES_VIDEO_EN_HISTORIA = {"tarjeta": (40, 260), "mapa": (40, 260), "ranking": (40, 260), "tiempo": (40, 260),
                                "explica": (40, 260), "golpe": (20, 130)}
# estructura por ACTOS (v3): tres actos fijos; los actos 2 y 3 se marcan con un rótulo sobre la primera escena del acto
# (sin detener la voz); la escena capitulo con voz propia queda como excepción (0–2, el gate avisa)
ACTOS = (("planteamiento", 1), ("nudo", 2), ("desenlace", 3))
PUNTOS_ESPINA = ("detonante", "punto_medio", "climax", "resolucion")
PERIODOS, HILOS, PERSONAJES_MAX, PRESENTACION_PALABRAS = (2, 5), (2, 6), 8, 8
CAPITULOS, ROTULOS, SEGUIDAS_MAX, GIRO_ENTRE = (0, 2), (2, 3), 3, (0.40, 0.75)
ROTULO_TIPOS = ("foto", "cita", "tarjeta", "mapa", "ranking", "tiempo", "golpe", "explica")
ROTULO_S, ROTULO_CUENTA, DESFASE_ROTULO = 2.3, (0.35, 1.45), 2.3 - VD.TRANSICION   # el rótulo dura 2.3 s; lo propio entra después
# flujo (H16): la narración se oye de corrido; cortes por minuto, conectores por acto y aperturas con atribución
CORTES_MAX_POR_MIN, CONECTORES_MIN_POR_ACTO, APERTURAS_ATRIBUIDAS_MAX = 6.5, 2, 1
# presupuesto de «según» en voz (H19): lo corroborado se narra llano con la fuente en pantalla
SEGUN_MAX_VIDEO, SEGUN_MAX_ACTO = 4, 2
SECUENCIA = (2, 5)        # escenas consecutivas del mismo acto cuya voz se graba de corrido (H20; video.py SECUENCIA_MAX)
TITULAR_PALABRAS, TITULAR_CARACTERES = 9, 60          # el titular de una escena foto
CHIP_CARACTERES, LUGAR_CARACTERES, FUENTE_CARACTERES = 14, 24, 44
CIFRA_CARACTERES, ETIQUETA_CARACTERES = 18, 30
CAP_TITULO_PALABRAS, CAP_TITULO_CARACTERES, CAP_ANIO_CARACTERES = 4, 28, 12
CITA_FRASE_CARACTERES, CREDITO_CARACTERES, ETIQUETA_GANCHO = 170, 60, 30
TRADUCCION_CARACTERES = 140                           # la traducción de una cita en otro idioma (renglón bajo la frase)
ESCENAS_MAX = 19          # + el cierre = 20 nodos: el tope de creative_run_flow_nodes (y de una llamada de estado sin Scribe)
FOTO_USOS_MAX = 2         # una misma imagen (por sha1) en ≤ 2 escenas, contando el gancho y los retratos
# H11 hilo: un demostrativo («esos 40 niños», «ese alimento») apunta a algo que ya se dijo antes en el video; si la
# cifra o la palabra no salió en ninguna escena anterior (ni antes en la misma), la escena quedó colgada (p. ej. tras
# cambiar el gancho). Las de tiempo («ese año», «esos años») y las que no son sustantivo no cuentan.
RE_DEMOSTRATIVO = re.compile(r"\b(es[oa]s|ese|esa|aquel(?:l[oa]s?)?|dich[oa]s?)\s+(?:(\d[\d.,]*)\s+)?([a-záéíóúñü]{3,})", re.I)
HILO_LIBRES = {"año", "años", "epoca", "época", "épocas", "momento", "momentos", "vez", "veces", "fecha", "fechas", "dia",
               "día", "días", "tiempo", "tiempos", "decada", "década", "décadas", "mes", "meses", "siglo", "entonces",
               "fue", "era", "eran", "son", "sería", "que", "mismo", "misma", "mismos", "mismas", "otra", "otro", "otras",
               "otros", "sola", "solo", "parte", "forma", "manera", "idea"}
# palabras vacías para notar una cita que no está en español (lleva `traduccion`)
VACIAS_EN = {"the", "and", "they", "we", "you", "is", "are", "was", "were", "to", "of", "with", "while", "what", "when",
             "want", "something", "it", "that", "this", "for", "have", "has", "our", "their", "be", "will", "would", "i"}
VACIAS_ES = {"de", "la", "que", "el", "en", "y", "los", "se", "las", "un", "una", "por", "con", "no", "su", "para", "es",
             "lo", "como", "me", "mi", "al", "del", "nos", "ya"}
# ganchos de historia (referencias/flujo-historia.md): el mecanismo que frena el scroll en una historia. Toda historia
# abre con «foto»: la foto de la historia a sangre con el titular entero desde el cuadro 0 (video/noticia.html en modo
# titular); decisión del usuario, 2026-10-26. El gancho cuenta el momento de la historia, no la respuesta que paga el video
FAMILIAS = ("resultado", "paradoja", "contraste", "misterio", "personaje", "lugar", "pregunta", "escala")
VISUALES = ("foto",)
VISUALES_DE = {fam: ("foto",) for fam in FAMILIAS}
ROTACION_FAMILIAS = 2
APERTURAS = re.compile(r"^[¿¡«\s]*(?:esta es la historia|la historia de|(?:te|les) (?:cuento|voy a contar)|hab[ií]a una vez|"
                       r"en el a[nñ]o\b|corr[ií]a el a[nñ]o|hoy (?:te|les) (?:hablo|cuento))", re.I)
PUNTAJES = ("gancho", "tension", "claridad", "flujo", "precision", "cierre")   # critica.json en modo historia (W12)
# ---- verdad ----
# una_fuente = UNA fuente seria sin nada que la contradiga: se narra llano con la fuente en pantalla; en_disputa = las
# fuentes difieren (la voz atribuye o matiza). tipo_hecho: lo que no es un acto público verificable (una acusación, una
# promesa de parte, una cifra no oficial, una opinión) se atribuye en voz aunque tenga una sola fuente (criterio BBC:
# se atribuye lo que no puede corroborarse o es de parte)
ESTADOS = ("confirmado", "una_fuente", "en_disputa", "no_confirmado")
PUBLICABLES = ("confirmado", "una_fuente", "en_disputa")
TIPOS_HECHO, ATRIBUIR_SIEMPRE = ("acto", "alegato", "estimacion", "opinion"), ("alegato", "estimacion", "opinion")
RE_SEGUN = re.compile(r"\b(?:seg[uú]n|de acuerdo con)\b", re.I)
RE_SEGUN_FUENTE = re.compile(r"\b(?:[Ss]eg[uú]n|[Dd]e acuerdo con)\s+(?:la |el |los |las |un |una )?((?:[A-ZÁÉÍÓÚÑ][\w.&-]*)(?:\s+(?:de |del |la |y )?[A-ZÁÉÍÓÚÑ][\w.&-]*)*)")
APERTURA_ATRIBUIDA = re.compile(r"^[¿¡«\s]*(?:(?:pero|y|por eso|así que|asi que|entonces)[,\s]+)?(?:seg[uú]n|de acuerdo con)\b", re.I)
# conectores causales y temporales que hacen que la narración siga de corrido (H16: ≥ 2 por acto)
CONECTORES_NARRACION = re.compile(
    r"\b(?:pero|sin embargo|aun así|en cambio|por eso|así que|asi que|entonces|hasta que|mientras tanto|porque|"
    r"(?:\d+|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|doce|quince|veinte) (?:años?|meses|semanas|d[ií]as) (?:después|antes|más tarde|mas tarde)|"
    r"(?:ese|esa) (?:mismo |misma )?(?:d[ií]a|mes|año|semana|noche|tarde|mañana)|al d[ií]a siguiente|al año siguiente|"
    r"(?:poco|meses|años|semanas|décadas|decadas) después)\b", re.I)
# hechos --reclasificar: una nota de en_disputa que describe una discrepancia real (no «solo X lo dice»)
RE_DISCREPANCIA = re.compile(r"difier|no coincid|choca|contradic|distint|otra fecha|otro (?:año|monto|n[uú]mero)|ambas|las dos|"
                             r"\b(?:1[5-9]|20)\d\d\b.*\b(?:1[5-9]|20)\d\d\b", re.I)
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
DESCARGAS = os.environ.get("HISTORIA_DESCARGAS") or os.path.join(RAIZ, "sesiones", "_descargas", "historia")   # la variable: pruebas
# el nombre del medio para el crédito de una og:image (foto --de-fuente); lo que no está aquí sale con su dominio
NOMBRES_MEDIOS = {"prensalibre.com": "Prensa Libre", "guatevision.com": "Guatevisión", "soy502.com": "Soy502", "republica.gt": "República",
                  "lahora.gt": "La Hora", "plazapublica.com.gt": "Plaza Pública", "emisorasunidas.com": "Emisoras Unidas",
                  "publinews.gt": "Publinews", "elperiodico.com.gt": "elPeriódico", "revistaeyn.com": "Estrategia & Negocios",
                  "estrategiaynegocios.net": "Estrategia & Negocios", "aprende.guatemala.com": "Guatemala.com", "nomada.gt": "Nómada",
                  "elfaro.net": "El Faro", "forbes.com.mx": "Forbes México", "forbescentroamerica.com": "Forbes Centroamérica",
                  "bloomberglinea.com": "Bloomberg Línea", "eleconomista.net": "El Economista", "chapinlandia.com": "Chapinlandia"}
# ---- fotos ----
# La foto va a sangre (estilo Noche) en la lámina de video/noticia.html: 1080×1200 arriba, la misma en 9:16 y en 4:5
# (proporción 0.9, object-fit: cover, Ken Burns hasta 1.15). Una apaisada se escala a lo alto y se recorta a los lados:
# una og:image de 1200×630 queda en ≈ 1.9× (2.2× con el Ken Burns) y la página la oscurece un poco más (brillo 0.45
# en vez de 0.55) y le pone el grano encima para que el aumento no se vea en bloques
FOTO_LADO_MIN, FOTO_LADO_AVISO = 480, 600     # material de archivo: 480 vale con aviso (a 480 px de alto, ≈ 2.9×)
# --encaje contener: el lienzo deja la imagen entera, con el margen del Ken Burns, en cualquier lámina de proporción
# 0.9 (MARCO_ANGOSTO: la de noticia.html) a 1.15 (MARCO_ANCHO); la página la muestra más clara y casi sin Ken Burns,
# para que se lea entera
ENCAJE_MARGEN, MARCO_ANCHO, MARCO_ANGOSTO = 1.18, 1.15, 0.9
PROPORCION_GRAFICO = 1.45     # más apaisada que esto y sin --encaje: aviso (¿es un gráfico o un cartel con texto?)
ORIGENES_FOTO = ("commons", "oficial", "medio", "empresa")
# una foto que no es del hecho (el lugar, la institución, la persona, el producto o la época) va como en /noticias: su
# crédito dice «Foto de referencia: …» para que nadie la tome por la del momento; cada eje trae ≥ FOTOS_POR_EJE fotos
CREDITO_FOTO, CREDITO_REFERENCIA, FOTOS_POR_EJE = "Foto: ", "Foto de referencia: ", 2
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
    return ({"familias": [x["familia"] for x in fr[-ROTACION_FAMILIAS:] if x.get("familia")], "visuales": []},
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


def ruta_fuente(url):
    """La base (sin extensión) de lo que `leer` guarda para esa url: <dominio-con-guiones>-<sha1[:10]>."""
    return os.path.join(DESCARGAS, "%s-%s" % (re.sub(r"[^a-z0-9]+", "-", NT.dominio(url)), hashlib.sha1(url.encode()).hexdigest()[:10]))


def nombre_medio(url):
    d = NT.dominio(url)
    return next((v for k, v in NOMBRES_MEDIOS.items() if d == k or d.endswith("." + k)), None) or NT.OFICIALES.get(d) or OTROS_OFICIALES.get(d) or d


def protagonistas(trabajo):
    """Los nombres del protagonista del encuadre, planos (H10, H12)."""
    return [VD._plano(x) for x in encuadre(trabajo).get("protagonista") or [] if (x or "").strip()]


def es_protagonista(rec, prot):
    """H12: la foto muestra al protagonista (foto … --protagonista) o es su retrato (--retrato-de con uno de sus nombres)."""
    return rec.get("muestra") == "protagonista" or (bool(rec.get("retrato_de")) and VD._plano(rec["retrato_de"]) in prot)


def og_candidatas(trabajo, urls=None):
    """[(meta, clase, nombra_al_protagonista)]: las fuentes leídas con og:image que valen como foto (medio, oficial o la
    empresa del encuadre); con `urls`, solo esas (las de un eje)."""
    enc, prot, out = encuadre(trabajo), protagonistas(trabajo), []
    bases = {os.path.basename(ruta_fuente(u)) for u in urls if u} if urls is not None else None
    for r in sorted(glob.glob(os.path.join(DESCARGAS, "*.json"))):
        if bases is not None and os.path.basename(r)[:-5] not in bases:
            continue
        m = leer(r)
        if not isinstance(m, dict) or not m.get("og_image") or not m.get("url"):
            continue
        clase = clasificar(m["url"], enc.get("dominios_propios") or [], m.get("archivo"))[0]
        if clase in ("medio", "oficial", "empresa"):
            out.append((m, clase, any(p in VD._plano(" ".join((m.get("titulo") or "", m["url"]))) for p in prot)))
    return out


def linea_de_fuente(trabajo, m, prot):
    """El comando listo para bajar la og:image de una fuente leída."""
    return "→ python3 scripts/historia.py foto %s --id <eje>-fNN --de-fuente %s --descripcion \"…\"%s   (og:image de %s · %s · «%s»)" % (
        VD.rel(trabajo), m["url"], " --protagonista" if prot else "", m.get("dominio"), m.get("fecha") or "s. f.", (m.get("titulo") or "")[:70])


def leer_url(url, otra_vez=False):
    """Baja la fuente (o su última copia en Wayback si ya no responde), guarda su texto y metadatos y devuelve meta."""
    os.makedirs(DESCARGAS, exist_ok=True)
    base = ruta_fuente(url)
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
    if meta.get("og_image") and meta["clase"] in ("medio", "oficial", "empresa"):
        print("FOTO: og:image %s → python3 scripts/historia.py foto <TRABAJO> --id <eje>-fNN --de-fuente %s --descripcion \"…\" "
              "[--protagonista si muestra al protagonista: el producto, el edificio, la persona]" % (meta["og_image"], a.url))
    elif meta.get("og_image") and meta["clase"] is None:
        print("FOTO: og:image %s (vale solo si el encuadre declara %s en dominios_propios: foto --de-fuente la baja como «empresa»)"
              % (meta["og_image"], meta["dominio"]))
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
           "retrato_de": (a.retrato_de or "").strip() or None, "encaje": a.encaje, "muestra": None}
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
    elif a.de_fuente:
        ruta_m = ruta_fuente(a.de_fuente) + ".json"
        if not os.path.exists(ruta_m):
            return falla("la fuente %s no está leída: python3 scripts/historia.py leer <url> primero" % a.de_fuente)
        meta = leer(ruta_m)
        if not meta.get("og_image"):
            return falla("la fuente %s no trae og:image: pasa la foto de la nota con --url o usa Commons" % meta.get("dominio"))
        clase = clasificar(a.de_fuente, encuadre(trabajo).get("dominios_propios") or [], meta.get("archivo"))[0]
        if clase not in ("medio", "oficial", "empresa"):
            return falla("H7 %s es %s: su og:image no lleva crédito de medio, oficial ni empresa (declara el dominio en dominios_propios "
                         "del encuadre o usa Commons)" % (meta.get("dominio"), clase or "una fuente que no cuenta"))
        url, origen, credito = meta["og_image"], clase, a.credito or CREDITO_FOTO + nombre_medio(a.de_fuente)
        if not credito.startswith(CREDITO_FOTO):
            print("--credito va «Foto: <medio>»", file=sys.stderr)
            return 2
        rec.update(licencia="© %s (crédito en pantalla)" % credito[len(CREDITO_FOTO):], autor=credito[len(CREDITO_FOTO):],
                   fuente=a.de_fuente, fecha=rec["fecha"] or meta.get("fecha"))
    elif a.url:
        if a.origen not in ("oficial", "medio", "empresa") or not (a.credito or "").startswith("Foto: "):
            print("--url pide --origen oficial|medio|empresa y --credito \"Foto: <institución o medio>\"", file=sys.stderr)
            return 2
        url, credito, origen = a.url, a.credito, a.origen
        rec.update(licencia="© %s (crédito en pantalla)" % a.credito[6:], autor=a.credito[6:])
    else:
        print("--commons \"File:…\", --de-fuente URL (una fuente leída) o --url U --credito C --origen O", file=sys.stderr)
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
        print("AVISO %s: %d×%d, por debajo de %d px: a sangre se verá blanda (la página la oscurece un poco más)"
              % (a.id, w, h, FOTO_LADO_AVISO))
    os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
    dst = "fotos/%s.jpg" % a.id
    VD.ff("-i", crudo, "-frames:v", "1", "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", os.path.join(trabajo, dst))
    if a.encaje == "contener":
        encajar(os.path.join(trabajo, dst))
    elif w / h > PROPORCION_GRAFICO:
        print("AVISO %s: %d×%d es muy apaisada; si es un gráfico, un cartel o un logo con texto, repite con --encaje "
              "contener (a sangre se recortan los lados: de una 16:9 se ve cerca de la mitad del ancho)" % (a.id, w, h))
    if a.referencia:
        credito = CREDITO_REFERENCIA + credito[len(CREDITO_FOTO):]
    if a.protagonista or (rec["retrato_de"] and VD._plano(rec["retrato_de"]) in protagonistas(trabajo)):
        rec["muestra"] = "protagonista"   # H12: la foto con la que abre el gancho
    rec.update(archivo=dst, credito=credito[:CREDITO_CARACTERES], origen=origen, url=url, tamano=[w, h],
               sha1=sha1_de(os.path.join(trabajo, dst)), referencia=bool(a.referencia))
    escribir(os.path.join(trabajo, "fotos", a.id + ".json"), rec)
    print("foto %s · %d×%d · %s (%s)%s → %s" % (a.id, w, h, rec["credito"], origen, " · PROTAGONISTA" if rec["muestra"] else "", dst))
    return 0


def sha1_de(ruta):
    return hashlib.sha1(open(ruta, "rb").read()).hexdigest()


def encajar(ruta):
    """--encaje contener: rellena la imagen con el color de su esquina para que quepa entera, con el margen del Ken
    Burns, en la lámina a sangre de video/noticia.html (1080×1200, proporción 0.9, en 9:16 y en 4:5) y en cualquiera de
    hasta 1.15 de proporción. Sustituye el archivo."""
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
            fallas.append("H1 %s: estado %s" % (hid, " | ".join(ESTADOS)))
            continue
        if h.get("tipo_hecho") not in (None,) + TIPOS_HECHO:
            fallas.append("H1 %s: tipo_hecho %s (acto = un acto público verificable; lo demás se atribuye en voz)" % (hid, " | ".join(TIPOS_HECHO)))
        if est == "no_confirmado":
            continue
        if not RE_FECHA.match(str(h.get("fecha") or "")) or h.get("precision") not in PRECISIONES:
            fallas.append("H1 %s: fecha YYYY[-MM[-DD]] y precision %s" % (hid, "|".join(PRECISIONES)))
        if not 10 <= len(h.get("texto") or "") <= HECHO_CARACTERES:
            fallas.append("H1 %s: texto de 10–%d caracteres (qué pasó, quién, dónde)" % (hid, HECHO_CARACTERES))
        validas, _ = revisar_fuentes(h, propios, fallas, avisos, hid)
        grupos = {g for _, g, _ in validas}
        nota = (h.get("nota") or "").strip()
        if est == "confirmado" and len(grupos) < 2:
            fallas.append("H2 %s: confirmado pide 2 fuentes independientes (grupos distintos: un documento oficial, la "
                          "empresa o la academia y otra que lo respalde); tiene %s" % (hid, ", ".join(sorted(grupos)) or "ninguna válida"))
        if est == "una_fuente":
            if not validas:
                fallas.append("H2 %s: una_fuente pide 1 fuente válida (oficial, medio de la lista, academia, archivo o la empresa)" % hid)
            elif len(grupos) >= 2:
                fallas.append("H2 %s: tiene fuentes de %d grupos (%s): es confirmado, o en_disputa si difieren"
                              % (hid, len(grupos), ", ".join(sorted(grupos))))
        if est == "en_disputa":
            if not validas or len(nota) < 10:
                fallas.append("H2 %s: en_disputa pide ≥ 1 fuente válida y una nota con la diferencia (la voz la atribuye o matiza)" % hid)
            elif len(grupos) == 1 and not RE_DISCREPANCIA.search(nota):
                avisos.append("H2 %s: en_disputa con un solo grupo y la nota no describe una discrepancia («%s»): ¿es una_fuente? "
                              "(hechos --reclasificar lo propone)" % (hid, nota[:60]))
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
            fallas.append("H1 %s: estado %s" % (cid, " | ".join(ESTADOS)))
            continue
        if c.get("tipo_hecho") not in (None,) + TIPOS_HECHO:
            fallas.append("H1 %s: tipo_hecho %s" % (cid, " | ".join(TIPOS_HECHO)))
        if est == "no_confirmado":
            continue
        if not isinstance(c.get("valor"), (int, float)) or isinstance(c.get("valor"), bool):
            fallas.append("H1 %s: valor numérico" % cid)
            continue
        validas, _ = revisar_fuentes(c, propios, fallas, avisos, cid)
        grupos, clases = {g for _, g, _ in validas}, {k for k, _, _ in validas}
        if est == "confirmado" and len(grupos) < 2 and not clases & {"oficial", "academica"}:
            fallas.append("H2 %s: una cifra confirmada pide 2 fuentes independientes o una oficial o académica" % cid)
        if est in ("una_fuente", "en_disputa") and not validas:
            fallas.append("H2 %s: %s pide ≥ 1 fuente válida" % (cid, est))
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
    if not (rec.get("credito") or "").startswith(CREDITO_REFERENCIA if rec.get("referencia") else CREDITO_FOTO):
        f.append("H7 %s: el crédito va «%s…»" % (fid, CREDITO_REFERENCIA if rec.get("referencia") else CREDITO_FOTO))
    if rec.get("origen") not in ORIGENES_FOTO:
        f.append("H7 %s: origen %s" % (fid, "|".join(ORIGENES_FOTO)))
    if rec.get("origen") == "commons" and not (LICENCIA_LIBRE.match(rec.get("licencia") or "") and not LICENCIA_NO.search(rec.get("licencia") or "")):
        f.append("H7 %s: licencia de Commons «%s» no libre" % (fid, rec.get("licencia")))
    if min(rec.get("tamano") or [0]) < FOTO_LADO_MIN:
        f.append("H7 %s: lado corto < %d px" % (fid, FOTO_LADO_MIN))
    if rec.get("muestra") not in (None, "protagonista"):
        f.append("H12 %s: «muestra» va protagonista o nada (foto … --protagonista)" % fid)
    return f


def reclasificar(trabajo, eje=None, aplicar=False):
    """hechos --reclasificar: cada hecho, cifra o cita `en_disputa` con las fuentes de UN solo grupo y una nota que no
    describe una discrepancia es en realidad `una_fuente` (así quedaron las sesiones anteriores a v3, donde «en disputa»
    significaba «una sola fuente»). Imprime los candidatos; con --aplicar los escribe (la nota se conserva)."""
    enc = encuadre(trabajo)
    propios = enc.get("dominios_propios") or []
    rutas = [os.path.join(trabajo, "verificacion_%s.json" % eje)] if eje else sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))
    n_c = 0
    for r in rutas:
        if not os.path.exists(r):
            continue
        v, cambia = leer(r), False
        for k in ("hechos", "cifras", "citas"):
            for x in v.get(k) or []:
                if x.get("estado") != "en_disputa":
                    continue
                validas, _ = revisar_fuentes(x, propios, [], [], x.get("id") or "?")
                grupos = {g for _, g, _ in validas}
                nota = (x.get("nota") or "").strip()
                if len(grupos) == 1 and not RE_DISCREPANCIA.search(nota):
                    n_c += 1
                    print("%s %-10s %s → una_fuente [%s] · nota: «%s»" % ("CAMBIA" if aplicar else "CANDIDATO", x["id"], (x.get("texto") or "")[:60],
                                                                          ", ".join(sorted(grupos)), nota[:50]))
                    if aplicar:
                        x["estado"], cambia = "una_fuente", True
        if cambia:
            escribir(r, v)
    print("%d en_disputa de un solo grupo sin discrepancia%s" % (n_c, " → una_fuente (escrito)" if aplicar else "; con --aplicar se reclasifican"))
    return 0


def cmd_hechos(a):
    trabajo = os.path.abspath(a.trabajo)
    if getattr(a, "reclasificar", False):
        rc = reclasificar(trabajo, a.eje, a.aplicar)
        if not a.aplicar or rc:
            return rc
        a.check = True
    if not a.check:
        return falla("hechos: --check o --reclasificar")
    enc = encuadre(trabajo)
    propios = enc.get("dominios_propios") or []
    rutas = [os.path.join(trabajo, "verificacion_%s.json" % a.eje)] if a.eje else sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))
    fallas, avisos, n, casos, vs = [], [], 0, 0, []
    for r in rutas:
        if not os.path.exists(r):
            fallas.append("H1 falta %s" % VD.rel(r))
            continue
        v = leer(r)
        vs.append(v)
        f, av = revisar_eje(v, trabajo, propios)
        fallas += f
        avisos += av
        casos += len(v.get("casos") or [])
        n += sum(1 for h in v.get("hechos") or [] if h.get("estado") in PUBLICABLES)
        if len(set(v.get("fotos") or [])) < FOTOS_POR_EJE:
            fallas.append("H7 eje %s: %d foto(s); cada eje trae ≥ %d (la del hecho o, si no hay, una de referencia del lugar, "
                          "la institución, la persona, el producto o la época: historia.py foto … --referencia)"
                          % (v.get("eje") or os.path.basename(r)[13:-5], len(set(v.get("fotos") or [])), FOTOS_POR_EJE))
        for fid in v.get("fotos") or []:
            ruta_f = os.path.join(trabajo, "fotos", "%s.json" % fid)
            if not os.path.exists(ruta_f):
                fallas.append("H7 %s: falta fotos/%s.json (python3 scripts/historia.py foto …)" % (fid, fid))
            else:
                fallas += revisar_foto(leer(ruta_f), trabajo)
    if not a.eje and (enc.get("sensibles") or {}).get("justicia") and not casos:
        fallas.append("H3 historia de justicia: cada persona señalada lleva su estado del caso a la fecha de la consulta (casos[] "
                      "en la verificación de su eje)")
    # H12: una foto del protagonista (la del gancho). Sin --eje falla; con --eje falla solo si la tiene a mano (la og:image de
    # una fuente que ya leyó y lo nombra: 0 búsquedas), si no avisa
    prot, sugerencias = protagonistas(trabajo), []
    recs = [leer(r) for r in sorted(glob.glob(os.path.join(trabajo, "fotos", "*.json")))]
    con_prot = [r["id"] for r in recs if es_protagonista(r, prot)]
    if prot and not con_prot:
        urls = {f.get("url") for v in vs for k in ("hechos", "cifras", "citas") for x in v.get(k) or [] for f in x.get("fuentes") or []} if a.eje else None
        a_mano = [c for c in og_candidatas(trabajo, urls) if c[2]]
        if not a.eje or a_mano:
            fallas.append("H12 ninguna foto muestra al protagonista (%s): el gancho abre con ella (foto … --protagonista)%s"
                          % (" / ".join(enc.get("protagonista")), "; abajo, las og:image de fuentes ya leídas que lo nombran (sin buscar)" if a_mano
                             else "; busca en Commons «%s», la prensa de la empresa o la og:image de una nota" % enc["protagonista"][0]))
            sugerencias = [linea_de_fuente(trabajo, m, True) for m, _, _ in a_mano]
        else:
            avisos.append("H12 todavía ninguna foto muestra al protagonista (%s): si tu eje lo cubre, baja una con --protagonista"
                          % " / ".join(enc.get("protagonista")))
    for x in avisos:
        print("AVISO", x)
    for x in fallas:
        print("FALLA", x)
    for x in sugerencias:
        print(x)
    if not fallas:
        print("H1–H3 ok · %d hecho(s) publicables en %d eje(s)%s" % (n, len(rutas), " · H12 foto(s) del protagonista: %s" % ", ".join(con_prot)
                                                                     if con_prot and not a.eje else ""))
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
            if rec.get("muestra") == "protagonista":
                fotos[prev]["muestra"] = "protagonista"   # la marca H12 no se pierde al fundir
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
    periodos = enc.get("periodos") or enc.get("capitulos") or []   # «capitulos» es el nombre viejo (v2): solo reparten ejes
    H = {"tema": st.get("tema"), "slug": st["slug"], "pregunta": enc.get("pregunta"), "arco": enc.get("arco"),
         "actos": enc.get("actos") or [], "espina": enc.get("espina") or {}, "hilos": enc.get("hilos") or [],
         "personajes": enc.get("personajes") or [], "periodos": periodos, "capitulos": periodos,
         "no_afirma": enc.get("no_afirma") or [],
         "protagonista": enc.get("protagonista") or [], "revelaciones": enc.get("revelaciones") or [],
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
    f = revisar_encuadre(encuadre(trabajo))
    if f:
        for x in f:
            print("FALLA", x)
        return falla("el encuadre no tiene la estructura por actos (v3): el editor lo re-encuadra (Workflow historia con desde: "
                     "encuadre) y historia.py encuadre %s --check lo comprueba" % VD.rel(trabajo))
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
    prot = protagonistas(trabajo)
    if prot and not any(es_protagonista(r, prot) for r in H["fotos"].values()):
        return falla("H12 ninguna foto muestra al protagonista: python3 scripts/historia.py hechos %s --check imprime las candidatas "
                     "(og:image de fuentes leídas) y el comando foto --de-fuente … --protagonista" % VD.rel(trabajo))
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
    VD.CARACTERES.update(CARACTERES_VIDEO_EN_HISTORIA)
    VD.SIN_HUECO = VD.SIN_HUECO + TIPOS_PROPIOS
    VD.POST_CONSTRUCTORES.append(post_historia)
    VD.ICONO_TIPOS = VD.ICONO_TIPOS + ("foto",)   # la foto sin imagen va con su icono (o el mapa)
    VD.visual_del_gancho = visual_del_gancho
    VD.reglas_gancho = reglas_gancho
    VD.validar_estructura = estructura
    VD.colores = colores_con_realce
    VD.CONSTRUCTORES.update(gancho=t_gancho, foto=t_foto, cita=t_cita, capitulo=t_capitulo)
    VD.TRANSICION_DE.update(foto="tarjeta", cita="texto", capitulo="completa")


def colores_con_realce(paleta):
    c = ORIGINALES["colores"](paleta)
    c["realce"] = c["acento"]   # Noche: el acento del tema ya se lee sobre la foto oscurecida (≥ 5.2:1 sobre el fondo)
    return c


def fotos_h():
    return (H_ACTUAL or {}).get("fotos") or {}


def visual_del_gancho(e, cifras, valores):
    if (e.get("visual") or "cifra") != "foto":
        return ORIGINALES["visual"](e, cifras, valores)
    d = e.get("visual_datos") or {}
    fo, f = fotos_h().get(d.get("foto")), []
    prot = protagonistas(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else []
    if not fo:
        f.append("visual foto: «foto» «%s» no es una foto verificada (historia.json → fotos)" % d.get("foto"))
    elif prot and not es_protagonista(fo, prot):
        con = [k for k, r in fotos_h().items() if es_protagonista(r, prot)]
        f.append("H12 la foto del gancho «%s» no muestra al protagonista (%s): la primera imagen dice de qué va la historia; usa %s"
                 % (d.get("foto"), " / ".join(encuadre(TRABAJO_ACTUAL).get("protagonista")),
                    ", ".join(con) if con else "una foto bajada con --protagonista (hechos --check imprime las candidatas)"))
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
    if vis != "foto":
        f.append("H7 el gancho de una historia abre con una foto a sangre (visual «foto» con una foto verificada), "
                 "no con «%s»" % vis)
    if e.get("icono") and vis != "cifra":
        f.append("el icono va solo con el visual cifra")
    silencio = " ".join((pant, lin))
    if vis == "cifra" and VD.numeros_sin_anios(silencio) and len(set(VD.numeros_sin_anios(silencio))) < 2 and not (
            VD.RE_DE_CADA.search(silencio) or re.search(r"×\s?\d|\d\s*veces\b|\bde\s+\d[\d,]*\b|\bpor\s+(?:cada\s+)?\w+", silencio, re.I)):
        f.append("R2 la cifra va sola en pantalla («%s»): dale un referente o usa la foto" % silencio.strip())
    prot = [x for x in (encuadre(TRABAJO_ACTUAL).get("protagonista") or []) if (x or "").strip()] if TRABAJO_ACTUAL else []
    if not prot:
        f.append("H10 el encuadre no trae «protagonista» (los nombres de quien protagoniza la historia: la marca, la "
                 "persona, la empresa…): el editor lo añade")
    elif not any(VD._plano(x) in VD._plano(" ".join((pant, lin, texto))) for x in prot):
        f.append("H10 el gancho no nombra al protagonista de la historia (%s): dilo en la pantalla, la línea o la voz"
                 % " / ".join(prot))
    # H13 reserva: lo que el video revela (encuadre.revelaciones) no se adelanta en el gancho. Lo mecánico son sus números:
    # ningún dígito escrito en una revelación aparece en la pantalla, la línea ni la voz. Sin números, lo juzga el crítico
    revs = (encuadre(TRABAJO_ACTUAL).get("revelaciones") or []) if TRABAJO_ACTUAL else []
    for k, rev in enumerate(revs, 1):
        tok = next((t for t in RE_NUMERO.findall(rev) if VD.escribe_numero(float(t.replace(",", "")), [pant, lin, texto])), None)
        if tok:
            f.append("H13 el gancho adelanta la revelación R%d («%s»): escribe «%s», que el video paga después; cuenta el momento, "
                     "no la respuesta" % (k, rev[:60], tok))
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
    return f, av


def rotulo_de(e):
    """El rótulo de acto de una escena: su campo `rotulo` {anio, titulo, lugar?, numero?} dibujado sobre la escena sin
    detener la voz o, en una escena capitulo (la excepción, v2), sus propios anio y titulo. None si no marca un acto."""
    if e.get("tipo") == "capitulo":
        return {"anio": str(e.get("anio") or "").strip(), "titulo": (e.get("titulo") or "").strip(), "lugar": e.get("lugar") or "",
                "numero": e.get("numero"), "capitulo": True}
    r = e.get("rotulo")
    if not isinstance(r, dict):
        return None
    return {"anio": str(r.get("anio") or "").strip(), "titulo": (r.get("titulo") or "").strip(), "lugar": r.get("lugar") or "",
            "numero": r.get("numero"), "capitulo": False}


def acto_de(e, i):
    """El acto de la escena i: el gancho (escena 1) es el acto 1 (ganchos --usar lo reescribe sin el campo)."""
    return 1 if i == 1 else e.get("acto")


def V9_de_video(x):
    """Las líneas V9 de /video que historia no hereda: la voz ya no tiene que EMPEZAR con «pero / por eso» (la causalidad
    vive en la narración, H16) y «y» no se cuenta (el enlace solo decide el efecto de sonido)."""
    if x.startswith(("V9 la escena 2 debe ser la tarjeta T1", "V9 escena 2: la primera tarjeta")):
        return True
    if x.startswith("V9 escena ") and ("falta enlace" in x or "no empieza con un conector" in x):
        return True
    return x.startswith("V9 ") and "enlaces «y» de" in x


def secuencias_por_defecto(g):
    """Las secuencias de voz (H20) cuando el guion no las trae: tramos de escenas consecutivas del mismo acto, de 2 a
    SECUENCIA[1], que se cortan antes de un giro o de un rótulo (abren una secuencia); el gancho y el cierre van solos."""
    es = g.get("escenas") or []
    tramos, actual = [], []
    for i, e in enumerate(es, 1):
        if i == 1:
            continue
        rompe = not actual or acto_de(e, i) != acto_de(es[actual[-1] - 1], actual[-1]) or e.get("giro") or rotulo_de(e)
        if rompe and actual:
            tramos.append(actual)
            actual = []
        actual.append(i)
    if actual:
        tramos.append(actual)
    out = []
    for t in tramos:
        while len(t) > SECUENCIA[1]:
            corte = SECUENCIA[1] if len(t) - SECUENCIA[1] != 1 else SECUENCIA[1] - 1
            out.append(t[:corte])
            t = t[corte:]
        if len(t) >= SECUENCIA[0]:
            out.append(t)
    return out


def estructura(g, st, dur, tarjetas):
    """V1/V9 de /video sin lo que historia no hereda + H8 (actos, rótulos, variedad, giro), H20 (secuencias) y las
    escenas propias."""
    f = [x for x in ORIGINALES["estructura"](g, st, dur, tarjetas) if not V9_de_video(x)]
    escenas = g.get("escenas") or []
    H = H_ACTUAL or {}
    hechos = {h["id"]: h for h in H.get("hechos") or []}
    citas = {q["id"]: q for q in H.get("citas") or []}
    fotos = H.get("fotos") or {}
    tipos = [e.get("tipo") for e in escenas]
    if len(escenas) > ESCENAS_MAX:
        f.append("H8 %d escenas: van ≤ %d (más el cierre son los 20 nodos que ElevenLabs genera de una vez)" % (len(escenas), ESCENAS_MAX))
    for i, e in enumerate(escenas, 1):
        if e.get("enlace") not in (None, "") and e.get("enlace") not in VD.ENLACES:
            f.append("H8 escena %d: enlace «%s» no es pero|por_eso|y (es opcional: solo decide el efecto de sonido)" % (i, e.get("enlace")))
    # H8 actos: cada escena (menos el gancho) declara su acto 1–3, en orden y los tres presentes
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    for i, ac in enumerate(actos, 1):
        if i > 1 and ac not in (1, 2, 3):
            f.append("H8 escena %d: «acto» 1, 2 o 3 (planteamiento, nudo, desenlace)" % i)
    validos = [a for a in actos if a in (1, 2, 3)]
    if validos != sorted(validos):
        f.append("H8 los actos van en orden (1 → 2 → 3): una escena vuelve a un acto anterior")
    if validos and set(validos) != {1, 2, 3}:
        f.append("H8 faltan actos: %s (van los tres)" % ", ".join(str(a) for a in (1, 2, 3) if a not in validos))
    primeras = {}
    for i, ac in enumerate(actos, 1):
        if ac in (1, 2, 3) and ac not in primeras:
            primeras[ac] = i
    # H8 rótulos: los actos 2 y 3 abren con un rótulo sobre su primera escena (o con una escena capitulo, la excepción)
    rotulos, caps = [], []
    for i, e in enumerate(escenas, 1):
        r = rotulo_de(e)
        if r is None:
            continue
        (caps if r["capitulo"] else rotulos).append(i)
        ac = actos[i - 1]
        if not r["capitulo"] and e.get("tipo") not in ROTULO_TIPOS:
            f.append("H8 escena %d: el rótulo va sobre una escena %s, no en %s" % (i, "|".join(ROTULO_TIPOS), e.get("tipo")))
        if r["capitulo"] and isinstance(e.get("rotulo"), dict):
            f.append("H8 escena %d: una escena capitulo no lleva además «rotulo»" % i)
        if ac in (2, 3) and primeras.get(ac) != i:
            f.append("H8 escena %d: el rótulo marca la PRIMERA escena de su acto (el acto %d empieza en la escena %s)" % (i, ac, primeras.get(ac)))
        elif ac == 1 and i != 2:
            f.append("H8 escena %d: en el acto 1 el rótulo solo cabe en la escena 2 (el gancho abre el acto)" % i)
        if not r["anio"] or len(r["anio"]) > CAP_ANIO_CARACTERES:
            f.append("H8 escena %d: rótulo «anio» (el año o la época, ≤ %d caracteres)" % (i, CAP_ANIO_CARACTERES))
        if not r["titulo"] or VD.palabras(r["titulo"]) > CAP_TITULO_PALABRAS or len(r["titulo"]) > CAP_TITULO_CARACTERES:
            f.append("H8 escena %d: rótulo «titulo» de 1–%d palabras y ≤ %d caracteres" % (i, CAP_TITULO_PALABRAS, CAP_TITULO_CARACTERES))
        if len(r["lugar"] or "") > LUGAR_CARACTERES:
            f.append("H8 escena %d: «lugar» de ≤ %d caracteres" % (i, LUGAR_CARACTERES))
    for ac in (2, 3):
        i = primeras.get(ac)
        if i and i not in rotulos and i not in caps:
            f.append("H8 el acto %d empieza en la escena %d sin rótulo: rotulo {anio, titulo, lugar?} en esa escena (año y ≤ %d "
                     "palabras sobre la imagen, la voz sigue)" % (ac, i, CAP_TITULO_PALABRAS))
    if len(caps) > CAPITULOS[1]:
        f.append("H8 %d escenas capitulo; van ≤ %d (una tarjeta con voz propia detiene la narración: prefiere rotulo)" % (len(caps), CAPITULOS[1]))
    elif caps:
        print("AVISO H8 %d escena(s) capitulo detienen la voz (escena%s %s): prefiere rotulo sobre la primera escena del acto"
              % (len(caps), "s" if len(caps) > 1 else "", ", ".join(map(str, caps))))
    for j, k in enumerate(caps, 1):
        e = escenas[k - 1]
        if e.get("numero") != j:
            f.append("H8 escena %d: capitulo numero %s (van 1, 2, 3… en orden)" % (k, e.get("numero")))
        if k >= len(escenas) or tipos[k] == "capitulo":
            f.append("H8 escena %d: un capítulo lleva al menos una escena después" % k)
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
    elif validos and actos[giros[0]] != 2:
        f.append("H8 el giro (escena %d) va en el acto 2, el nudo (está en el acto %s)" % (giros[0] + 1, actos[giros[0]]))
    if not any(t in ("foto", "cita") for t in tipos):
        f.append("H8 una historia lleva al menos una escena foto o cita")
    # H20 secuencias de voz: forma en video.py (V9); aquí lo semántico
    secs = g.get("secuencias") or []
    if g.get("voz_continua") and not secs:
        f.append("H20 voz_continua exige «secuencias» (grupos de %d–%d escenas consecutivas del mismo acto)" % SECUENCIA)
    en_sec = set()
    for k, grupo in enumerate(secs if isinstance(secs, list) else [], 1):
        if not (isinstance(grupo, list) and all(isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= len(escenas) for n in grupo)):
            continue   # V9 (video.py) lo señala
        en_sec |= set(grupo)
        if len({actos[n - 1] for n in grupo}) > 1:
            f.append("H20 secuencia %d (escenas %s): cruza actos; una secuencia vive dentro de un acto" % (k, ", ".join(map(str, grupo))))
        for n in grupo[1:]:
            if escenas[n - 1].get("giro") or rotulo_de(escenas[n - 1]):
                f.append("H20 secuencia %d: la escena %d (giro o rótulo) solo puede ABRIR una secuencia" % (k, n))
    for i in range(2, len(escenas)):
        if i not in en_sec and i - 1 in en_sec and i + 1 in en_sec and actos[i - 2] == actos[i - 1] == actos[i]:
            print("AVISO H20 la escena %d queda fuera de toda secuencia entre dos del mismo acto: su voz se graba aparte" % i)
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        for hid in e.get("hechos") or []:
            if hid not in hechos:
                f.append("H4 escena %d: el hecho «%s» no está entre los publicables de historia.json" % (i, hid))
        if tipo == "foto":
            fid = e.get("foto")
            if fid is not None and fid not in fotos:
                f.append("H7 escena %d: la foto «%s» no está verificada (fotos/<id>.json)" % (i, fid))
            if fid is None or e.get("icono") or e.get("depto"):
                f.append("H7 escena %d: la escena foto lleva una foto verificada, nunca un icono ni un mapa: si no hay "
                         "del hecho, una de referencia (el lugar, la institución, la persona, el producto o la época: "
                         "historia.py foto … --referencia); si no hay ninguna, cuéntala con otra escena" % i)
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
    f += hilo_referencias(escenas)
    f += pago_revelacion(g, escenas)
    final = ((g.get("cierre") or {}).get("final") or "").strip()
    if re.search(r"\bseg[uú]n\b", final, re.I):
        f.append("H9 el final del cierre no lleva «según»: es lo último que se oye y tiene que doler o conmover; apóyalo en un "
                 "hecho confirmado (lo que la historia le hizo a una persona o a un grupo concreto) y deja la atribución "
                 "en el resumen o en una escena anterior")
    avisar_flashbacks(escenas)
    return f


def hilo_referencias(escenas):
    """H11: cada «esos 40 niños», «ese alimento», «esa línea» tiene su antecedente en lo que ya se oyó o se leyó antes:
    la cifra y la palabra salen en una escena anterior (voz, pantalla, línea, titular) o antes en la misma voz."""
    f, dicho = [], ""
    llano = lambda t: VD._plano(re.sub(r"\{([\d.,]+):\w+\}", r"\1", t or ""))  # noqa: E731
    for i, e in enumerate(escenas, 1):
        voz = e.get("texto") or ""
        for m in RE_DEMOSTRATIVO.finditer(voz):
            num, pal = m.group(2), m.group(3).lower()
            if pal in HILO_LIBRES or VD._plano(pal) in HILO_LIBRES:
                continue
            antes = dicho + " " + llano(voz[:m.start()])
            raiz = VD._plano(pal[:-1] if pal.endswith("s") and len(pal) > 4 else pal)
            falta = [x for x, ok in ((num, not num or re.search(r"\b%s\b" % re.escape(llano(num)), antes)),
                                     (pal, re.search(r"\b%s" % re.escape(raiz), antes))) if x and not ok]
            if falta:
                f.append("H11 escena %d: «%s» apunta a algo que no se dijo antes (%s no sale en ninguna escena "
                         "anterior): di qué es aquí o cámbialo; si cambiaste el gancho u otra escena, relee el hilo "
                         "entero" % (i, m.group(0), " ni ".join("«%s»" % x for x in falta)))
        dicho += " " + llano(" ".join(str(e.get(k) or "") for k in ("pantalla", "linea", "titular", "golpe", "titulo", "texto")))
    return f


def pago_revelacion(g, escenas):
    """H14: la promesa declara qué revelación del encuadre paga (`promesa.revela`, R1, R2…) y la escena `promesa.pago` la
    cuenta: una raíz de 5 letras de la revelación (sin vacías) está en su voz o en su pantalla (como F3 del cierre)."""
    revs = (encuadre(TRABAJO_ACTUAL).get("revelaciones") or []) if TRABAJO_ACTUAL else []
    p = g.get("promesa") or {}
    if not revs:
        return []
    k = p.get("revela")
    if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= len(revs):
        return ["H14 promesa.revela: el número (1–%d) de la revelación del encuadre que la promesa paga (el digesto las lista R1, R2…)" % len(revs)]
    pago = p.get("pago")
    if not isinstance(pago, int) or not 1 <= pago <= len(escenas):
        return []   # V9 ya lo señala
    e = escenas[pago - 1]
    dicho = VD._plano(" ".join(str(e.get(c) or "") for c in ("texto", "pantalla", "linea", "titular", "golpe", "titulo")))
    raices = {w[:5] for w in VD._plano(revs[k - 1]).split() if len(w) >= 5 and w not in VD.STOP and w not in VD.GENERICAS and not w.isdigit()}
    if raices and not any(re.search(r"\b" + re.escape(r), dicho) for r in raices):
        return ["H14 la escena %d (promesa.pago) no cuenta la revelación R%d («%s»): la promesa se paga ahí, con sus palabras, "
                "o mueve el pago a la escena que la cuenta" % (pago, k, revs[k - 1][:70])]
    return []


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
    """Aviso: un año anterior al del acto en que va la escena (el museo de 2019 dentro de «2021»); el año del acto es el
    del rótulo (o del capitulo) que lo abre."""
    cap = None
    for i, e in enumerate(escenas, 1):
        r = rotulo_de(e)
        if r:
            m = RE_ANIO.search(r["anio"])
            cap = int(m.group()) if m else None
            if r["capitulo"]:
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


def medio_de(h):
    """El nombre de la primera fuente de un hecho (sin el paréntesis «(maqueta)»), para cotejarlo con la pantalla."""
    fs = h.get("fuentes") or []
    if not fs:
        return ""
    m = (fs[0].get("medio") or "").split("(")[0].strip()
    return m or nombre_medio(fs[0].get("url") or "")


def fuente_en_pantalla(e):
    """Lo que la escena escribe como fuente: «fuente» (foto, cita) o grafico.fuente (tarjetas), plano."""
    gr = e.get("grafico") if isinstance(e.get("grafico"), dict) else {}
    return VD._plano(" ".join(filter(None, (e.get("fuente"), gr.get("fuente")))))


def revisar_verdad(g, H, valores):
    """H3 y H4: años y números con respaldo; presunción de inocencia; ATRIBUCIÓN (v3): la voz atribuye o matiza solo lo
    `en_disputa` y lo de parte (`tipo_hecho` alegato | estimacion | opinion) y dice quién habla antes de leer una cita;
    lo `una_fuente` se narra llano con la fuente en pantalla (o ya nombrada en el mismo acto)."""
    f = []
    anios = anios_respaldados(H)
    hechos = {h["id"]: h for h in H.get("hechos") or []}
    citas = {q["id"]: q for q in H.get("citas") or []}
    casos_firmes = {x.get("persona") for x in H.get("casos") or [] if x.get("sentencia_firme")}
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    nombradas, voz_previa = {}, ""
    for i, e in enumerate(escenas + [dict(cierre, tipo="cierre")], 1):
        textos = [e.get(k) or "" for k in ("texto", "pantalla", "linea", "golpe", "titular", "titulo", "fecha", "lugar", "fuente")]
        textos += [str(e.get("anio") or "")] + [(e.get("cifra") or {}).get(k) or "" for k in ("texto", "etiqueta")]
        textos += [" ".join(map(str, e.get("pasos") or [])), " ".join(e.get("resumen") or [])]
        r = rotulo_de(e)
        if r:
            textos += [r["anio"], r["titulo"], r["lugar"]]
        todo = " ".join(textos)
        voz = VD.sin_pausas(e.get("texto") or "")
        ac = acto_de(e, i) if i <= len(escenas) else 3
        vistos = nombradas.setdefault(ac, set())
        hs = [hechos[h] for h in e.get("hechos") or [] if h in hechos]
        de_parte = [h for h in hs if h.get("estado") == "en_disputa" or h.get("tipo_hecho") in ATRIBUIR_SIEMPRE]
        if de_parte and not ATRIBUCION.search(voz):
            f.append("H4 escena %d: cuenta un hecho en disputa o de parte (%s) y la voz no atribuye ni matiza («según…», «dijo», "
                     "«acusó», «a inicios de…»)" % (i, ", ".join("%s %s" % (h["id"], h.get("tipo_hecho") or h["estado"]) for h in de_parte)))
        en_pantalla = fuente_en_pantalla(e)
        for h in [h for h in hs if h.get("estado") == "una_fuente"]:
            mp = VD._plano(medio_de(h))
            if not mp:
                continue
            if mp in en_pantalla or mp in VD._plano(voz) or any(mp in v or v in mp for v in vistos):
                vistos.add(mp)
            else:
                f.append("H4 escena %d: cuenta un hecho de una sola fuente (%s: %s) y la fuente no está en pantalla ni se nombró "
                         "antes en este acto: ponla en «fuente» (o grafico.fuente) o nómbrala una vez; la voz no necesita «según»"
                         % (i, h["id"], medio_de(h)))
        vistos |= {VD._plano(x) for x in re.split(r"[·,/]", (e.get("fuente") or "") + "·" + ((e.get("grafico") or {}).get("fuente") or "")) if x.strip()}
        if e.get("tipo") == "cita" and citas.get(e.get("cita")):
            q = citas[e["cita"]]
            pv, pq = VD._plano(voz), VD._plano(q.get("texto"))
            pos = pv.find(pq)
            antes = (VD._plano(voz_previa) + " " + (pv[:pos] if pos >= 0 else pv)).strip()
            raices = {w[:5] for w in VD._plano(q.get("autor") or "").split() if len(w) >= 4 and w not in VD.STOP}
            if raices and not any(ra in antes for ra in raices):
                f.append("H4 escena %d: la voz no dice quién lo dijo (%s) antes de leer la cita; preséntalo en esta voz o en la "
                         "anterior" % (i, q.get("autor")))
        voz_previa = voz
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


# ---------- la narración (v3): el texto corrido que se escribe ANTES de repartirlo en escenas ----------
def narracion_de(g):
    """[(acto, texto)] de guion.narracion (3 entradas {acto, texto}); [] si no viene."""
    return [(x.get("acto"), (x.get("texto") or "").strip()) for x in g.get("narracion") or [] if isinstance(x, dict)]


def plano_voz(t):
    return VD._plano(VD.sin_pausas(t or ""))


def raices_de(texto):
    """Las raíces de 5 letras de las palabras con peso de un texto (como F3 del cierre y H14)."""
    return {w[:5] for w in VD._plano(texto).split() if len(w) >= 5 and w not in VD.STOP and w not in VD.GENERICAS and not w.isdigit()}


def estimado_s(g):
    """Segundos estimados del guion sin locución (dígitos sin convertir): lo bastante para contar cortes por minuto."""
    es = g.get("escenas") or []
    return sum(len(VD.sin_pausas(e.get("texto") or "")) for e in es + [g.get("cierre") or {}]) / VD.CPS + VD.COLA * len(es) + VD.COLA_CIERRE


def revisar_narracion(g, H, enc):
    """H15 (la narración es la suma exacta de las voces), H16 (flujo), H17 (hilos), H18 (primera mención) y H19
    (presupuesto de «según»). Sin escenas (el guionista mide el texto antes de repartirlo: `narracion --check`), las
    unidades son los tres actos y H15 solo cuenta palabras."""
    f = []
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    narr = narracion_de(g)
    solo_narr = not escenas
    if not narr or [a for a, _ in narr] != [1, 2, 3] or not all(t for _, t in narr):
        f.append("H15 «narracion»: 3 entradas {acto: 1|2|3, texto} con el texto corrido de cada acto (se escribe ANTES de "
                 "repartirlo en escenas; cada escena toma un tramo sin cambiar una palabra)")
        narr = []
    for ac, texto in narr:
        if solo_narr:
            break
        voces = [e.get("texto") or "" for e, a in zip(escenas, actos) if a == ac]
        if ac == 3:
            voces.append(cierre.get("texto") or "")
        esperado, dado = plano_voz(" ".join(voces)), plano_voz(texto)
        if esperado != dado:
            k = next((j for j, (x, y) in enumerate(zip(esperado, dado)) if x != y), min(len(esperado), len(dado)))
            f.append("H15 acto %d: la narración no es la suma de las voces de sus escenas%s; difieren desde «…%s» (narración) frente a "
                     "«…%s» (voces): reparte el texto tal cual o corrige la narración" % (ac, " y el cierre" if ac == 3 else "",
                                                                                        dado[max(0, k - 20):k + 25], esperado[max(0, k - 20):k + 25]))
    if narr:
        total = sum(VD.palabras(t) for _, t in narr)
        if not PALABRAS_DURO[0] <= total <= PALABRAS_DURO[1]:
            f.append("H15 %d palabras de narración; van %d–%d (≈ %d s a 145 palabras por minuto)" % (total, *PALABRAS, OBJETIVO_S))
        elif not PALABRAS[0] <= total <= PALABRAS[1]:
            print("AVISO H15 %d palabras de narración: apunta a %d–%d (≈ %d s)" % (total, *PALABRAS, OBJETIVO_S))
    # H16 flujo: conectores por acto, aperturas con atribución, aperturas repetidas y cortes por minuto
    for ac, texto in narr:
        n_c = len(CONECTORES_NARRACION.findall(VD.sin_pausas(texto)))
        if n_c < CONECTORES_MIN_POR_ACTO:
            f.append("H16 acto %d: %d conector(es) causal o temporal («pero», «por eso», «entonces», «dos años después», «mientras "
                     "tanto»…); van ≥ %d: cada oración sigue de la anterior, nunca «y luego»" % (ac, n_c, CONECTORES_MIN_POR_ACTO))
    unidades = [VD.sin_pausas(e.get("texto") or "").strip() for e in escenas] + [VD.sin_pausas(cierre.get("texto") or "").strip()] \
        if not solo_narr else [t for _, t in narr]
    etiqueta = (lambda k: "escena %d" % (k + 1)) if not solo_narr else (lambda k: "acto %d" % (k + 1))  # noqa: E731
    if not solo_narr:
        ap = [i for i, u in enumerate(unidades[:-1], 1) if i >= 2 and APERTURA_ATRIBUIDA.match(u)]
        if len(ap) > APERTURAS_ATRIBUIDAS_MAX:
            f.append("H16 %d escenas abren con una atribución («Según…», «Pero, según…»: escenas %s); va ≤ %d: la fuente en pantalla "
                     "y la voz narra" % (len(ap), ", ".join(map(str, ap)), APERTURAS_ATRIBUIDAS_MAX))
        dos = [" ".join(plano_voz(u).split()[:2]) for u in unidades[:-1]]
        for i in range(1, len(dos)):
            if dos[i] and dos[i] == dos[i - 1]:
                f.append("H16 escenas %d y %d abren con las mismas palabras («%s»): varía la apertura" % (i, i + 1, dos[i]))
        primeras = {}
        for u in unidades[1:-1]:
            w = (plano_voz(u).split() or [""])[0]
            primeras[w] = primeras.get(w, 0) + 1
        for w, n in primeras.items():
            if n > 3 and w:
                print("AVISO H16 %d escenas abren con «%s»: varía la apertura" % (n, w))
        est = estimado_s(g)
        cpm = (len(escenas) + 1) / max(1.0, est / 60)
        if cpm > CORTES_MAX_POR_MIN:
            f.append("H16 %.1f cortes por minuto (%d escenas más el cierre en %.0f s); van ≤ %.1f: una escena puede sostener un tramo "
                     "más largo de narración" % (cpm, len(escenas), est, CORTES_MAX_POR_MIN))
    # H17 hilos: lo que la historia abre se paga en una escena o se declara sin respuesta en la narración del acto 3
    hilos_enc = [h for h in enc.get("hilos") or [] if isinstance(h, dict) and (h.get("id") or "").strip()]
    if hilos_enc:
        decl = {h.get("id"): h for h in g.get("hilos") or [] if isinstance(h, dict)}
        narr3 = plano_voz(" ".join([t for a, t in narr if a == 3] + [cierre.get("texto") or ""]))
        for h in hilos_enc:
            d = decl.get(h["id"])
            if not d:
                f.append("H17 el hilo %s («%s») no está en guion.hilos: {id, escena: N (la que lo paga, con paga: [id])} o "
                         "{id, sin_respuesta: «nunca se supo…»}" % (h["id"], (h.get("pregunta") or "")[:60]))
            elif d.get("escena") is not None:
                n = d["escena"]
                if solo_narr:
                    continue
                if not isinstance(n, int) or isinstance(n, bool) or not 3 <= n <= len(escenas):
                    f.append("H17 hilo %s: escena %s no existe (3–%d)" % (h["id"], n, len(escenas)))
                elif h["id"] not in (escenas[n - 1].get("paga") or []):
                    f.append("H17 hilo %s: la escena %d no lo declara en «paga»: [\"%s\"]" % (h["id"], n, h["id"]))
            elif (d.get("sin_respuesta") or "").strip():
                raices = raices_de(d["sin_respuesta"])
                if raices and not any(re.search(r"\b" + re.escape(ra), narr3) for ra in raices):
                    f.append("H17 hilo %s: la narración del acto 3 (o el cierre) no dice que quedó sin respuesta («%s»)"
                             % (h["id"], d["sin_respuesta"][:60]))
            else:
                f.append("H17 hilo %s: «escena» (la que lo paga) o «sin_respuesta» (la frase que lo declara)" % h["id"])
        ids = {h["id"] for h in hilos_enc}
        for i, e in enumerate(escenas, 1):
            for hid in e.get("paga") or []:
                if hid not in ids:
                    f.append("H17 escena %d: «paga» cita un hilo que no existe en el encuadre (%s)" % (i, hid))
    # H18 primera mención: cada personaje llega presentado la primera vez que la voz lo nombra
    prot = [VD._plano(x) for x in enc.get("protagonista") or [] if (x or "").strip()]
    personajes = [p for p in enc.get("personajes") or [] if isinstance(p, dict) and (p.get("nombre") or "").strip()]
    citas = {q["id"]: q for q in H.get("citas") or []}
    pantallas = [VD._plano(pantalla_de(e, citas)) for e in escenas] if not solo_narr else [""] * 3
    voces_p = [plano_voz(u) for u in unidades]
    nombres = {VD._plano(p["nombre"]): p for p in personajes}
    for p in personajes:
        nom = VD._plano(p["nombre"])
        if nom in prot:
            continue
        claves = [nom] + [VD._plano(a) for a in p.get("alias") or [] if (a or "").strip()]
        otros = [o for o in nombres if o != nom]
        k = None
        for j, v in enumerate(voces_p):
            for c in claves:
                if re.search(r"\b%s\b" % re.escape(c), v) and not (c != nom and any(c in o and re.search(r"\b%s\b" % re.escape(o), v) for o in otros)):
                    k = j
                    break
            if k is not None:
                break
        if k is None:
            continue
        raices = raices_de(p.get("presentacion") or "")
        if not raices or VD.palabras(p.get("presentacion") or "") > PRESENTACION_PALABRAS:
            f.append("H18 personaje %s: «presentacion» de 1–%d palabras que diga quién es («hermano de la vicepresidenta»)" % (p["nombre"], PRESENTACION_PALABRAS))
            continue
        dicho = " ".join(filter(None, [voces_p[k], pantallas[k] if k < len(pantallas) else "", voces_p[k - 1] if k > 0 else ""]))
        if not any(re.search(r"\b" + re.escape(ra), dicho) for ra in raices):
            f.append("H18 %s: «%s» aparece por primera vez sin presentación («%s»): dilo en esa voz (o en la anterior) con una "
                     "aposición" % (etiqueta(k), p["nombre"], p.get("presentacion")))
    # H19 «según»: ≤ 4 por video, ≤ 2 por acto, nunca en dos escenas seguidas, nunca la misma fuente dos veces en voz
    segs = [len(RE_SEGUN.findall(u)) for u in unidades]
    if sum(segs) > SEGUN_MAX_VIDEO:
        f.append("H19 %d «según» en la voz; van ≤ %d: lo corroborado se narra llano con la fuente en pantalla; varía con una "
                 "aposición («AMSA, la autoridad del lago, …») o el verbo de la fuente («el tribunal calificó…»)" % (sum(segs), SEGUN_MAX_VIDEO))
    por_acto = {}
    for k, n in enumerate(segs):
        ac = (k + 1) if solo_narr else (actos[k] if k < len(actos) else 3)
        por_acto[ac] = por_acto.get(ac, 0) + n
    for ac, n in sorted(por_acto.items(), key=lambda kv: str(kv[0])):
        if n > SEGUN_MAX_ACTO:
            f.append("H19 acto %s: %d «según»; van ≤ %d por acto" % (ac, n, SEGUN_MAX_ACTO))
    if not solo_narr:
        for i in range(1, len(segs)):
            if segs[i - 1] and segs[i]:
                f.append("H19 escenas %d y %d: «según» en dos escenas seguidas; la segunda fuente va solo en pantalla" % (i, i + 1))
    fuentes_voz = {}
    for k, u in enumerate(unidades):
        for m in RE_SEGUN_FUENTE.finditer(u):
            fuentes_voz.setdefault(VD._plano(m.group(1)), []).append(etiqueta(k))
    for fu, ns in fuentes_voz.items():
        if len(ns) > 1:
            f.append("H19 «según %s» %d veces en voz (%s): la segunda vez va solo en pantalla" % (fu, len(ns), ", ".join(ns)))
    return f


def revisar_encuadre(enc):
    """La estructura v3 del encuadre: 3 actos, la espina (4 puntos en su acto), 2–6 hilos, ≤ 8 personajes presentados y
    2–5 periodos (el reparto de los ejes). → fallas H8."""
    f = []
    actos = enc.get("actos") if isinstance(enc.get("actos"), list) else []
    if [(a.get("nombre"), a.get("n")) for a in actos if isinstance(a, dict)] != list(ACTOS) or len(actos) != 3:
        f.append("H8 encuadre: «actos» son exactamente 3 en orden: %s (n 1–3), cada uno con titulo (≤ %d palabras), periodo, "
                 "que_cuenta y termina_en" % (", ".join("%s (%d)" % x for x in ACTOS), CAP_TITULO_PALABRAS))
    else:
        for a in actos:
            for k in ("titulo", "periodo", "que_cuenta", "termina_en"):
                if not (a.get(k) or "").strip():
                    f.append("H8 encuadre: acto %s sin «%s»" % (a.get("n"), k))
            tit = (a.get("titulo") or "").strip()
            if tit and (VD.palabras(tit) > CAP_TITULO_PALABRAS or len(tit) > CAP_TITULO_CARACTERES):
                f.append("H8 encuadre: acto %s: titulo de 1–%d palabras y ≤ %d caracteres (es el rótulo)" % (a.get("n"), CAP_TITULO_PALABRAS, CAP_TITULO_CARACTERES))
    ejes = {x.get("id") for x in enc.get("ejes") or [] if isinstance(x, dict)}
    esp = enc.get("espina") if isinstance(enc.get("espina"), dict) else {}
    for k, en in zip(PUNTOS_ESPINA, ((1,), (2,), (2, 3), (3,))):
        p = esp.get(k)
        if not isinstance(p, dict) or not (p.get("frase") or "").strip():
            f.append("H8 encuadre: espina.%s {frase, acto, ejes} (los cuatro puntos: detonante, punto_medio, climax, resolucion)" % k)
            continue
        if p.get("acto") not in en:
            f.append("H8 encuadre: espina.%s va en el acto %s" % (k, " o ".join(map(str, en))))
        if any(x not in ejes for x in p.get("ejes") or []):
            f.append("H8 encuadre: espina.%s cita un eje que no existe (%s)" % (k, ", ".join(sorted(ejes))))
    hilos = enc.get("hilos") if isinstance(enc.get("hilos"), list) else []
    if not HILOS[0] <= len(hilos) <= HILOS[1]:
        f.append("H8 encuadre: %d hilos; van %d–%d (las preguntas que la historia abre y debe pagar o declarar sin respuesta)" % (len(hilos), *HILOS))
    ids = []
    for h in hilos:
        if not isinstance(h, dict) or not re.fullmatch(r"h\d+", str(h.get("id") or "")) or not (h.get("pregunta") or "").strip():
            f.append("H8 encuadre: cada hilo {id: h1, h2…, pregunta, eje}")
            continue
        ids.append(h["id"])
        if h.get("eje") and h["eje"] not in ejes:
            f.append("H8 encuadre: hilo %s cita el eje «%s», que no existe" % (h["id"], h["eje"]))
    if len(ids) != len(set(ids)):
        f.append("H8 encuadre: ids de hilo repetidos")
    prot = {VD._plano(x) for x in enc.get("protagonista") or []}
    pers = enc.get("personajes") if isinstance(enc.get("personajes"), list) else []
    if len(pers) > PERSONAJES_MAX:
        f.append("H8 encuadre: %d personajes; van ≤ %d" % (len(pers), PERSONAJES_MAX))
    for p in pers:
        if not isinstance(p, dict) or not (p.get("nombre") or "").strip():
            f.append("H8 encuadre: cada personaje {nombre, alias[], presentacion}")
            continue
        pr = (p.get("presentacion") or "").strip()
        if not pr or VD.palabras(pr) > PRESENTACION_PALABRAS:
            f.append("H8 encuadre: personaje %s: presentacion de 1–%d palabras (quién es: «hermano de la vicepresidenta»)" % (p["nombre"], PRESENTACION_PALABRAS))
        if VD._plano(p["nombre"]) in prot:
            f.append("H8 encuadre: %s es el protagonista: no va en personajes (lo presenta el gancho)" % p["nombre"])
    periodos = enc.get("periodos") if isinstance(enc.get("periodos"), list) else (enc.get("capitulos") if isinstance(enc.get("capitulos"), list) else [])
    if not PERIODOS[0] <= len(periodos) <= PERIODOS[1]:
        f.append("H8 encuadre: %d periodos; van %d–%d (el reparto de los ejes entre investigadores: {n, titulo, periodo, pregunta})" % (len(periodos), *PERIODOS))
    return f


def cmd_encuadre(a):
    trabajo = os.path.abspath(a.trabajo)
    enc = encuadre(trabajo)
    if not enc:
        return falla("falta %s/encuadre.json" % VD.rel(trabajo))
    f = revisar_encuadre(enc)
    for x in f:
        print("FALLA", x)
    if not f:
        print("encuadre ok · actos %s · espina %s · %d hilos · %d personajes · %d periodos"
              % (" / ".join(a_.get("titulo") or "" for a_ in enc["actos"]), ", ".join("%s (acto %s)" % (k, enc["espina"][k].get("acto")) for k in PUNTOS_ESPINA),
                 len(enc.get("hilos") or []), len(enc.get("personajes") or []), len(enc.get("periodos") or enc.get("capitulos") or [])))
    return 1 if f else 0


def cmd_narracion(a):
    """La herramienta del guionista para escribir el texto corrido ANTES de repartirlo: por acto, palabras, segundos a 145 ppm,
    conectores, «según» (y a qué fuente), la primera mención de cada personaje y los hilos; --check falla con H16–H19
    (sobre la narración sola) y con la cuenta de palabras."""
    trabajo = os.path.abspath(a.trabajo)
    g = leer(os.path.join(trabajo, "guion.json"))
    H, enc = historia_de(trabajo), encuadre(trabajo)
    narr = narracion_de(g)
    if not narr:
        return falla("guion.json sin «narracion»: [{acto: 1, texto}, {acto: 2, texto}, {acto: 3, texto}]")
    total = 0
    for ac, texto in narr:
        n_p = VD.palabras(texto)
        total += n_p
        NE.AVISOS.clear()
        try:
            car = len(NE.convertir(VD.sin_pausas(texto))[1])
        except ValueError:
            car = len(texto)
        NE.AVISOS.clear()
        con = CONECTORES_NARRACION.findall(VD.sin_pausas(texto))
        seg = [m.group(1) for m in RE_SEGUN_FUENTE.finditer(texto)]
        print("acto %d · %d palabras · ≈ %.0f s de voz · conectores %d (%s) · «según» %d%s" % (
            ac, n_p, car / VD.CPS, len(con), ", ".join(con[:6]) or "ninguno", len(RE_SEGUN.findall(texto)), " (" + ", ".join(seg) + ")" if seg else ""))
    colas = VD.COLA * max(0, len(g.get("escenas") or []) or 12) + VD.COLA_CIERRE
    print("total %d palabras (objetivo %d–%d) · ≈ %.0f s con las colas de %d escenas (objetivo %d s)"
          % (total, *PALABRAS, total / 145 * 60 + colas, len(g.get("escenas") or []) or 12, OBJETIVO_S))
    texto_todo = plano_voz(" ".join(t for _, t in narr))
    for p in enc.get("personajes") or []:
        nom = VD._plano(p.get("nombre") or "")
        if nom and re.search(r"\b%s\b" % re.escape(nom), texto_todo):
            ok = any(re.search(r"\b" + re.escape(ra), texto_todo) for ra in raices_de(p.get("presentacion") or ""))
            print("personaje %s: nombrado%s" % (p["nombre"], " y presentado" if ok else " SIN presentación («%s»)" % p.get("presentacion")))
    decl = {h.get("id"): h for h in g.get("hilos") or [] if isinstance(h, dict)}
    for h in enc.get("hilos") or []:
        d = decl.get(h.get("id")) or {}
        print("hilo %s («%s»): %s" % (h.get("id"), (h.get("pregunta") or "")[:50], "paga la escena %s" % d["escena"] if d.get("escena") is not None
                                      else "sin respuesta: «%s»" % d["sin_respuesta"][:50] if d.get("sin_respuesta") else "SIN declarar en guion.hilos"))
    if not getattr(a, "check", False):
        return 0
    f = revisar_narracion({"narracion": g.get("narracion"), "hilos": g.get("hilos"), "cierre": g.get("cierre")}, H, enc)
    for x in f:
        print("FALLA", x)
    print("narracion %s" % ("ok" if not f else "con %d falla(s)" % len(f)))
    return 1 if f else 0


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
    # secuencias de voz (H20): si el guion no las trae, el script las deriva de los actos y las escribe (voz_continua por
    # defecto en historia: la voz se graba de corrido por secuencia)
    if g.get("voz_continua", True) and not g.get("secuencias") and g.get("escenas"):
        g["secuencias"], g["voz_continua"] = secuencias_por_defecto(g), True
        escribir(os.path.join(trabajo, "guion.json"), g)
        print("secuencias por defecto (voz de corrido): %s" % " · ".join("–".join(map(str, (s[0], s[-1]))) for s in g["secuencias"]))
    elif g.get("secuencias") and "voz_continua" not in g:
        g["voz_continua"] = True
        escribir(os.path.join(trabajo, "guion.json"), g)
    fallas = construir_tarjetas(trabajo, g, st)
    aplicar_extension(trabajo)
    valores, _, _ = VD.valores_respaldo(VD.estado(trabajo)["hilo"])
    fallas += revisar_verdad(g, H, valores)
    fallas += revisar_narracion(g, H, encuadre(trabajo))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):   # las FALLA de video.py (V1–V5, V9, F1–F8, H8–H14) van también al RETORNO
        rc = VD.cmd_guion(argparse.Namespace(trabajo=trabajo, check=True))
    salida = buf.getvalue()
    print(salida, end="")
    for x in fallas:
        print("FALLA", x)
    todas = fallas + [l[len("FALLA "):] for l in salida.splitlines() if l.startswith("FALLA ")]
    loc = os.path.join(trabajo, "locucion.json")
    if fallas and rc == 0 and os.path.exists(loc):
        os.remove(loc)   # una locución que no pasó H3–H14 no se graba
    ok = rc == 0 and not fallas
    if ok:
        marcar_citas_sin_escucha(loc, g, H)
        print("H3–H14 ok")
        av = aviso_duracion(leer(loc)["estimado_s"])
        if av:
            print(av)
    print("RETORNO " + json.dumps(retorno_guion(trabajo, g, ok, todas), ensure_ascii=False))
    return 0 if ok else 1


def aviso_duracion(estimado_s):
    """AVISO H5 (no gate): el objetivo es 150 s (135–165); el tope de 180 queda para emergencias."""
    if estimado_s <= OBJETIVO_AVISO_S:
        return None
    return ("AVISO H5 %.0f s estimados: apunta a %d s (%d–%d); el tope de %d s es para emergencias. Recorta una escena o una "
            "oración por escena antes de la crítica" % (estimado_s, OBJETIVO_S, OBJETIVO_MIN_S, OBJETIVO_AVISO_S, DURACION_MAX_S))


def retorno_guion(trabajo, g, ok, fallas):
    """La última línea de `guion --check`: lo que el guionista devuelve TAL CUAL al Workflow (S.guion). `tipos` trae el tipo
    de cada escena en orden, sin el cierre (que no está en TIPOS)."""
    es = g.get("escenas") or []
    loc = os.path.join(trabajo, "locucion.json")
    est = leer(loc)["estimado_s"] if ok and os.path.exists(loc) else round(estimado_s(g), 1)
    hilos_g = [h for h in g.get("hilos") or [] if isinstance(h, dict)]
    return {"archivo": VD.rel(os.path.join(trabajo, "guion.json")), "gate": "ok" if ok else "falla", "fallas": fallas,
            "escenas": len(es), "tipos": [e.get("tipo") for e in es], "capitulos": sum(e.get("tipo") == "capitulo" for e in es),
            "actos": len({acto_de(e, i) for i, e in enumerate(es, 1)} & {1, 2, 3}),
            "rotulos": sum(1 for e in es if rotulo_de(e) and not rotulo_de(e)["capitulo"]),
            "palabras": sum(VD.palabras(t) for _, t in narracion_de(g)),
            "segun": sum(len(RE_SEGUN.findall(VD.sin_pausas(e.get("texto") or ""))) for e in es + [g.get("cierre") or {}]),
            "hilos_pagados": sum(1 for h in hilos_g if h.get("escena") is not None),
            "hilos_sin_respuesta": sum(1 for h in hilos_g if (h.get("sin_respuesta") or "").strip()),
            "secuencias": len(g.get("secuencias") or []),
            "estimado_s": est, "explica_sin_animacion": [i for i, e in enumerate(es, 1) if e.get("tipo") == "explica" and not e.get("animacion")]}


def marcar_citas_sin_escucha(ruta_loc, g, H):
    """V11: la frase de una cita en otro idioma no se coteja con whisper (corre con -l es): locucion.json →
    escenas[].escucha_omitir, que video.py escuchar deja fuera de la comparación."""
    loc = leer(ruta_loc)
    citas, cambio = {q["id"]: q for q in H.get("citas") or []}, False
    for e, le in zip(g.get("escenas") or [], loc["escenas"]):   # mismo orden; el cierre queda fuera del zip
        q = citas.get(e.get("cita")) if e.get("tipo") == "cita" else None
        if q and otro_idioma(q.get("texto")):
            le["escucha_omitir"], cambio = q["texto"], True
    if cambio:
        escribir(ruta_loc, loc)


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
    fo = next((r for r in fotos_h().values() if vis.get("foto") and r.get("archivo") == vis.get("foto")), {})
    S["N"] = {"modo": "titular", "foto": vis.get("foto"), "credito": vis.get("credito"), "fecha": cin.get("pantalla") or "",
              "conteo": vis.get("etiqueta") or "", "titular": linea, "kb": NT.KEN_BURNS[0], "depto": None, "icono": None,
              "encaje": fo.get("encaje")}   # «contener»: la página la muestra entera (más clara y casi sin Ken Burns)
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


def entrada_sfx(S, e, esc):
    """El efecto de entrada de una escena de historia (presupuesto v3): un «pero» en la voz o el giro llevan «grave»; la
    primera escena de una secuencia, una sin secuencia o una con rótulo, «whoosh»; dentro de una secuencia (la voz sigue
    de corrido) no hay efecto de entrada."""
    if VD.RE_ENLACE["pero"].match(VD.sin_pausas(e.get("voz") or "").strip()) or esc.get("giro"):
        return [(0.0, "grave")]
    if S.get("seguida") and not rotulo_de(esc):
        return []
    return [(0.0, "whoosh")]


def t_fuente(esc, pal, t_ult, fin_voz, dur):
    """Cuándo entra el chip «Fuente: …»: en la primera palabra de la voz que nombre esa fuente; si la voz no la nombra, a
    mitad de la escena. Ya no depende de que la voz diga «según» (la fuente en pantalla es la norma, H4)."""
    ws = [VD._plano(w["text"]) for w in pal]
    k = None
    for medio in re.split(r"[·,/]", esc.get("fuente") or ""):
        toks = VD._plano(medio).split()
        for j in range(len(ws) - len(toks) + 1) if toks else []:
            if ws[j:j + len(toks)] == toks:
                k = j if k is None else min(k, j)
                break
    t_f = pal[k]["start"] if k is not None else max(t_ult + 1.0, 0.45 * fin_voz)
    return min(t_f, dur - 1.0)


def armar_rotulo(S, esc, ps, g, R):
    """El rótulo de acto sobre la primera escena del acto (S.R, lo dibuja V.pintarActo): el año cuenta desde el del
    rótulo anterior (si la voz dice el año antes de 2 s, termina ahí), el título entra palabra a palabra y todo se
    desvanece en ROTULO_S; la voz sigue narrando debajo."""
    es = g.get("escenas") or []
    previos = [rotulo_de(x) for i, x in enumerate(es, 1) if i < S["n"] and rotulo_de(x)]
    t0 = ROTULO_CUENTA[0]
    k = next((j for j, p in enumerate(ps) if p.get("seg") and p["seg"].get("num") and R["anio"] and R["anio"] in (p["seg"].get("p") or "")
              and p["end"] <= 2.0), None)
    t1 = max(t0 + 0.9, ps[k]["end"]) if k is not None else ROTULO_CUENTA[1]
    titulo = VD.repartir(R["titulo"].split(), t1, t1 + 0.5, minimo=0.1)
    return {"numero": R.get("numero") or acto_de(esc, S["n"]) or len(previos) + 1, "total": len(ACTOS),
            "desde": previos[-1]["anio"] if previos else None, "hasta": R["anio"], "titulo": titulo,
            "lugar": R.get("lugar") or None, "cuenta": [round(t0, 3), round(t1, 3)], "fin": ROTULO_S}


def eventos_rotulo(S):
    r = S["R"]
    return [(0.1, "acto"), (r["cuenta"][1], "acto_cuenta_fin"), (r["fin"], "acto_fin")], [(r["cuenta"][1], "resolucion")]


def t_foto(S, e, ps, pal, fin_voz, dur, g):
    """La escena foto: video/noticia.html en modo noticia (chip con la fecha y el lugar, la foto a sangre con Ken Burns
    y, en la columna, el titular, la cifra si la hay, la fuente y el crédito de la foto). Con rótulo de acto, lo propio entra cuando el rótulo se va;
    dentro de una secuencia, el titular entra con la primera oración de la voz."""
    esc = escena_guion(S, g)
    fo = fotos_h().get(esc.get("foto")) or {}
    R = rotulo_de(esc)
    t0 = VD.TRANSICION + 0.05 + (DESFASE_ROTULO if R else 0.0)
    if S.get("seguida") and not R:
        t0 = 0.05
    N = {"modo": "noticia", "chip": {"b": esc.get("fecha") or "", "s": esc.get("lugar") or ""}, "foto": fo.get("archivo"),
         "credito": fo.get("credito"), "icono": esc.get("icono"), "depto": NT.depto_id(esc.get("depto")),
         "lugar": esc.get("lugar") if not fo.get("archivo") else None, "kb": NT.KEN_BURNS[(S["n"] - 1) % len(NT.KEN_BURNS)],
         "encaje": fo.get("encaje"), "cifra": None, "fuente": None}
    tit_ws = (esc.get("titular") or "").split()
    if S.get("seguida") and not R:
        fin_1 = VD.fin_oracion_desde(pal, 0)
        N["titular"], _ = VD.alinear_linea(tit_ws, pal, t0 + 0.05, max(t0 + 0.9, min(fin_1, fin_voz - 0.3)))
        if not any(w.get("dicha") for w in N["titular"]):
            N["titular"] = VD.repartir(tit_ws, t0 + 0.1, t0 + 0.9, minimo=0.08)
    else:
        N["titular"] = VD.repartir(tit_ws, t0 + 0.1, t0 + 1.2, minimo=0.08)
    ev = [(0.1 + (DESFASE_ROTULO if R else 0.0), "entrada")] + [(w["start"], "titular") for w in N["titular"]]
    sfx = entrada_sfx(S, e, esc)
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
        t_f = t_fuente(esc, pal, t_ult, fin_voz, dur)
        if N["cifra"]:
            t_f = min(max(t_f, N["cifra"]["start"] + 1.2), dur - 1.0)
        N["fuente"] = {"texto": "Fuente: " + esc["fuente"], "start": round(t_f, 3)}
        ev.append((t_f, "fuente"))
    cifra_t = N["cifra"]["pulso"][0] if N["cifra"] and N["cifra"]["pulso"] else None
    latidos = {round(pal[k + 1]["start"], 3) for k, x in enumerate(pal[:-1]) if x["text"].endswith((".", "?", "!", ":"))} | \
        {round(x["start"], 3) for x in pal if x.get("clave") and x["start"] != cifra_t}
    rellenar_huecos(latidos, ev, pal, dur)
    N["oraciones"] = sorted(latidos)
    ev += [(x, "oracion") for x in N["oraciones"]]
    S["pagina"], S["N"], S["T"] = "noticia", N, {"tit": round(t0, 3)}
    if R:
        S["R"] = armar_rotulo(S, esc, ps, g, R)
        ev_r, sfx_r = eventos_rotulo(S)
        ev += ev_r
        sfx += sfx_r
    return ev, sfx


def t_cita(S, e, ps, pal, fin_voz, dur, g):
    """La escena cita: video/historia.html (la frase entera apagada que se enciende con la voz, sin subtítulo mientras
    la lee; quién y cuándo; la parte clave se subraya en el acento cuando la voz la dice)."""
    esc = escena_guion(S, g)
    q = next((x for x in (H_ACTUAL or {}).get("citas") or [] if x["id"] == esc.get("cita")), {})
    ws = (q.get("texto") or "").split()
    R = rotulo_de(esc)
    t0 = VD.TRANSICION + 0.1 + (DESFASE_ROTULO if R else 0.0)
    if S.get("seguida") and not R:
        t0 = 0.1
    texto, _ = VD.alinear_linea(ws, pal, t0, max(t0 + 0.4, fin_voz - 0.3))
    resalte, resalte_t = None, None
    rw = [VD._norm(w) for w in (esc.get("resalte") or "").split()]
    qn = [VD._norm(w) for w in ws]
    for k in range(len(qn) - len(rw) + 1) if rw else []:
        if qn[k:k + len(rw)] == rw:
            resalte, resalte_t = [k, k + len(rw) - 1], round(texto[k]["start"], 3)
            break
    ret = fotos_h().get(esc.get("retrato")) or {}
    entra = round(t0 + 0.25, 3) if (S.get("seguida") and not R) else round(0.6 + (DESFASE_ROTULO if R else 0.0), 3)
    fuente = {"texto": "Fuente: " + esc["fuente"], "start": round(max(t_fuente(esc, pal, t0, fin_voz, dur), min(2.0, dur - 1.0)), 3)} if esc.get("fuente") else None
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
    ev = [(0.1 + (DESFASE_ROTULO if R else 0.0), "entrada"), (entra, "firma")] + [(w["start"], "palabra") for w in texto if w.get("dicha")]
    sfx = entrada_sfx(S, e, esc)
    if R:
        S["R"] = armar_rotulo(S, esc, ps, g, R)
        ev_r, sfx_r = eventos_rotulo(S)
        ev += ev_r
        sfx += sfx_r
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


ENTRADAS_ROTULO = ("entra", "golpe_arriba", "cifra", "cifra_fin", "linea", "linea_fin", "linea_dicha", "lienzo", "paso", "foco",
                   "conteo_fin", "nota", "anio", "anio_fin", "item", "punto", "figuras", "destacadas", "etiqueta", "pildora")


def post_historia(S, e, ps, pal, fin_voz, dur, g, ev, sfx):
    """Tras el constructor de cualquier escena (VD.POST_CONSTRUCTORES): el rótulo de acto sobre las escenas de video.py
    (tarjeta, golpe, explica…: lo propio espera a que el rótulo se vaya), el presupuesto de efectos dentro de una
    secuencia, y la transición de entrada (fundido dentro de una secuencia; la del giro manda)."""
    esc = escena_guion(S, g)
    tipo = S.get("tipo")
    if tipo not in TIPOS_PROPIOS + ("gancho", "cierre"):
        R = rotulo_de(esc)
        if R:
            for w in S.get("arriba") or []:
                w["start"] = round(w["start"] + DESFASE_ROTULO, 3)
            T = S.get("T") or {}
            for k in ("tit", "ini"):
                if isinstance(T.get(k), (int, float)):
                    T[k] = round(T[k] + DESFASE_ROTULO, 3)
            if isinstance(T.get("pant"), dict):
                for k in ("desde", "hasta"):
                    if isinstance(T["pant"].get(k), (int, float)):
                        T["pant"][k] = round(T["pant"][k] + DESFASE_ROTULO, 3)
            for lista in (T.get("linea") or [], T.get("pasos") or [], T.get("items") or [], T.get("puntos") or []):
                for w in lista:
                    w["start"] = round(max(w["start"], ROTULO_S), 3)
            for v in (T.get("valores") or {}).values():
                v[0] = round(max(v[0], ROTULO_S), 3)
            for k in ("nota", "figuras", "destacadas", "etiqueta_t"):
                if isinstance(T.get(k), (int, float)):
                    T[k] = round(max(T[k], ROTULO_S + (1.0 if k == "nota" else 0.0)), 3)
            ev = [(max(t, ROTULO_S) if k in ENTRADAS_ROTULO else t, k) for t, k in ev]
            S["R"] = armar_rotulo(S, esc, ps, g, R)
            ev_r, sfx_r = eventos_rotulo(S)
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
    E["tipo"] = "historia"
    E["cierre"]["rotulo"] = (g.get("cierre") or {}).get("rotulo") or "Lo que dejó"
    escribir(ruta, E)
    if E["total_s"] + VD.BUCLE_S > DURACION_MAX_S:
        print("AVISO H5 duración real %.1f s: pasa de %d s (el tope de YouTube Shorts)" % (E["total_s"] + VD.BUCLE_S, DURACION_MAX_S))
    return 0


# ---------- digestos ----------
def lineas_hechos(H, con_citas=True):
    """Un hecho por línea: `una_fuente [medio]` se narra llano con la fuente en pantalla; `en_disputa (nota)` y
    `· ALEGATO|ESTIMACIÓN|OPINIÓN` se atribuyen en voz (H4)."""
    out = []
    for h in H.get("hechos") or []:
        fs = " · ".join("%s" % (f.get("medio") or NT.dominio(f.get("url"))) for f in h.get("fuentes") or [])
        th = h.get("tipo_hecho")
        out.append("- %s · %s (%s) · %s%s%s — %s [%s]" % (h["id"], h.get("fecha"), h.get("precision"), h["estado"],
                   " (" + h["nota"] + ")" if h["estado"] == "en_disputa" and h.get("nota") else "",
                   " · %s" % {"alegato": "ALEGATO", "estimacion": "ESTIMACIÓN", "opinion": "OPINIÓN"}[th] if th in ATRIBUIR_SIEMPRE else "",
                   h.get("texto"), fs))
    return out


def lineas_encuadre(H, enc):
    """Actos, espina, hilos y personajes del encuadre (v3), para el gancho, el guionista y el crítico."""
    actos = H.get("actos") or enc.get("actos") or []
    esp = H.get("espina") or enc.get("espina") or {}
    out = ["- Actos (tres; los actos 2 y 3 abren con un rótulo sobre su primera escena, la voz sigue):"]
    out += ["  %s. %s · «%s» (%s) — %s; termina en: %s" % (a.get("n"), a.get("nombre"), a.get("titulo"), a.get("periodo"), a.get("que_cuenta"), a.get("termina_en"))
            for a in actos] or ["  (el encuadre no trae actos: historia.py encuadre --check)"]
    out += ["- Espina (en este orden; el guionista cuelga las escenas de aquí):"]
    out += ["  %s (acto %s%s): %s" % (k, (esp.get(k) or {}).get("acto"), " · " + ", ".join((esp.get(k) or {}).get("ejes") or []) if (esp.get(k) or {}).get("ejes") else "",
                                       (esp.get(k) or {}).get("frase")) for k in PUNTOS_ESPINA if esp.get(k)]
    hilos = H.get("hilos") or enc.get("hilos") or []
    out += ["- Hilos (lo que la historia abre: cada uno se paga en una escena (paga: [id]) o se declara sin respuesta en la narración "
            "del acto 3; H17):"] + ["  %s · %s%s" % (h.get("id"), h.get("pregunta"), " (eje %s)" % h["eje"] if h.get("eje") else "") for h in hilos]
    pers = H.get("personajes") or enc.get("personajes") or []
    if pers:
        out += ["- Personajes (la primera vez que la voz los nombra van presentados con ≤ %d palabras; H18):" % PRESENTACION_PALABRAS]
        out += ["  %s%s — %s" % (p.get("nombre"), " (%s)" % ", ".join(p.get("alias") or []) if p.get("alias") else "", p.get("presentacion")) for p in pers]
    return out


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    enc = encuadre(trabajo)
    if a.para == "editor":
        H = historia_de(trabajo)
        out = ["# Re-encuadre · %s (la cronología ya está verificada: añade actos, espina, hilos y personajes; conserva lo demás)" % st.get("tema"), "",
               "- Pregunta: %s · arco: %s" % (H.get("pregunta"), H.get("arco")),
               "- Protagonista: %s" % " / ".join(H.get("protagonista") or []),
               "- Revelaciones:"] + ["  R%d. %s" % (k, r) for k, r in enumerate(H.get("revelaciones") or [], 1)] + \
              ["- No afirma: %s" % "; ".join(H.get("no_afirma") or []), "", "## Cronología verificada (id · fecha · estado — hecho [fuentes])"] + lineas_hechos(H) + \
              ["", "## Citas literales"] + ["- %s · %s · %s — «%s»" % (q["id"], q.get("autor"), q.get("cuando"), q.get("texto")) for q in H.get("citas") or []] + \
              (["", "## Casos"] + ["- %s: %s" % (x.get("persona"), x.get("estado_actual")) for x in H.get("casos") or []] if H.get("casos") else []) + \
              ["", "## Encuadre actual (encuadre.json)", "```json", json.dumps(enc, ensure_ascii=False, indent=1), "```"]
        print("\n".join(out))
        return 0
    if a.para in ("investigador", "verificador"):
        eje = next((x for x in enc.get("ejes") or [] if x.get("id") == a.eje), None)
        if not eje:
            return falla("el encuadre no tiene el eje «%s»" % a.eje)
        periodos = enc.get("periodos") or enc.get("capitulos") or []
        de_eje = eje.get("periodos") or eje.get("capitulos") or []
        hilos_eje = [h for h in enc.get("hilos") or [] if not h.get("eje") or h.get("eje") == a.eje]
        out = ["# %s · eje %s (%s)" % (st.get("tema"), eje["id"], eje.get("nombre")), "",
               "- Pregunta de la historia: %s" % enc.get("pregunta"), "- Arco: %s" % enc.get("arco"),
               "- Periodos del eje: %s" % ", ".join("%s (%s)" % (c.get("titulo"), c.get("periodo")) for c in periodos if c.get("n") in de_eje),
               "- Hilos de tu eje (busca su respuesta; si no existe, dilo en huecos): %s" % ("; ".join("%s %s" % (h.get("id"), h.get("pregunta")) for h in hilos_eje) or "—"),
               "- Personajes (trae el cargo y la relación con que se presentan): %s" % ("; ".join("%s — %s" % (p.get("nombre"), p.get("presentacion")) for p in enc.get("personajes") or []) or "—"),
               "- Estados: confirmado (2 grupos) · una_fuente (1 fuente seria sin contradicción: se narra llano con la fuente en pantalla) · "
               "en_disputa (las fuentes difieren: nota con las dos versiones) · no_confirmado. tipo_hecho: acto | alegato | estimacion | opinion "
               "(lo que no es acto se atribuye en voz)",
               "- Qué buscar: %s" % "; ".join(eje.get("preguntas") or []),
               "- Fuentes sugeridas: %s" % "; ".join(eje.get("fuentes") or []),
               "- Dominios de la empresa o institución protagonista (cuentan como fuente propia): %s" % ", ".join(enc.get("dominios_propios") or []) or "—",
               "- Protagonista: %s" % (" / ".join(enc.get("protagonista") or []) or "FALTA en el encuadre"),
               "- Fotos que hacen falta (encuadre.fotos_clave; la PRIMERA es la del protagonista y es obligatoria, H12): %s"
               % ("; ".join(enc.get("fotos_clave") or []) or "la imagen del protagonista (%s)" % " / ".join(enc.get("protagonista") or [])),
               "- Candidatas de foto: la og:image de las notas que leas (leer la imprime con el comando foto --de-fuente listo), Commons por el "
               "nombre del protagonista, la prensa de la empresa; nunca un icono en lugar de una foto",
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
            out += ["- foto candidata %s · %s · %s%s" % (x.get("id"), x.get("descripcion"), x.get("commons") or x.get("url"),
                                                     " · PROTAGONISTA" if x.get("protagonista") else "") for x in hz.get("fotos") or []]
            urls = {ev.get("url") for k in ("hechos", "cifras", "citas") for x in hz.get(k) or [] for ev in x.get("evidencia") or x.get("fuentes") or []}
            cands = og_candidatas(trabajo, urls)
            if cands:
                out += ["", "## og:image de las fuentes leídas en este eje (* = nombra al protagonista: bájala con --protagonista, H12)"]
                for m, clase, pr in cands:
                    out += ["- %s%s · %s · «%s» · %s" % ("* " if pr else "", m["dominio"], m.get("fecha") or "s. f.", (m.get("titulo") or "")[:80], m["og_image"]),
                            "  " + linea_de_fuente(trabajo, m, pr)]
        out += ["", "## Clases de fuente que cuentan", "- oficial: *.gob.gt, %s, %s" % (", ".join(sorted(NT.OFICIALES)), ", ".join(sorted(OTROS_OFICIALES))),
                "- medio (dominio → grupo): %s" % ", ".join("%s→%s" % kv for kv in sorted({**NT.MEDIOS, **INTERNACIONALES}.items())),
                "- academica: *.edu, %s · archivo: %s (Wayback cuenta como su original)" % (", ".join(sorted(ACADEMICAS)), ", ".join(sorted(ARCHIVOS))),
                "- Wikipedia NO cuenta: úsala para llegar a sus referencias."]
        print("\n".join(out))
        return 0
    H = historia_de(trabajo)
    if a.para == "oyente":
        return digesto_oyente(trabajo, H)
    rec_g = st.get("ganchos_recientes") or {}
    prot = protagonistas(trabajo)
    base = ["# Historia · %s (paleta %s, música %s)" % (st.get("tema"), st["paleta"], st["musica"]), "",
            "- Pregunta: %s · arco: %s" % (H.get("pregunta"), H.get("arco")),
            "- Protagonista: %s" % (" / ".join(H.get("protagonista") or encuadre(trabajo).get("protagonista") or []) or "FALTA en el encuadre")] + \
        lineas_encuadre(H, enc) + \
        ["- Revelaciones (lo que el video PAGA: el gancho no las adelanta —H13 veta sus números—, la promesa paga una "
         "(promesa.revela: 1, 2…) y la escena del pago la cuenta con sus palabras (H14)):"] + \
        (["  R%d. %s" % (k, r) for k, r in enumerate(H.get("revelaciones") or encuadre(trabajo).get("revelaciones") or [], 1)]
         or ["  (el encuadre no trae revelaciones: H13 y H14 no corren)"]) + \
        ["- No afirma: %s" % "; ".join(H.get("no_afirma") or []), "", "## Cronología verificada (id · fecha · estado — hecho [fuentes])"] + \
        lineas_hechos(H) + (["", "## Conflictos de fecha"] + ["- %s y %s" % tuple(x) for x in H["conflictos"]] if H.get("conflictos") else []) + \
        ["", "## Cifras (id · texto · valor)"] + ["- %s · %s · %s %s (%s)" % (c["id"], c.get("texto"), c["valor"], c.get("unidad", ""), c.get("anio") or "")
                                                for c in H.get("cifras") or []] + \
        ["", "## Citas literales (id · quién · cuándo — frase)"] + ["- %s · %s%s · %s%s — «%s»" % (q["id"], q.get("autor"), ", " + q["cargo"] if q.get("cargo") else "",
                                                                    q.get("cuando"), " · documento" if q.get("documento") else "", q.get("texto"))
                                                                    for q in H.get("citas") or []] + \
        ["", "## Fotos verificadas (id · qué muestra · crédito · origen; PROTAGONISTA = la que puede abrir el gancho, H12)"] + \
        ["- %s · %s · %s (%s)%s%s" % (k, f.get("descripcion"), f.get("credito"), f.get("origen"),
                                      " · %s %s" % (f.get("fecha") or "", f.get("lugar") or "") if f.get("fecha") or f.get("lugar") else "",
                                      " · PROTAGONISTA" if es_protagonista(f, prot) else "")
         for k, f in sorted((H.get("fotos") or {}).items())] + \
        (["", "## Casos (estado a la fecha de consulta)"] + ["- %s: %s (consultado %s)%s" % (x.get("persona"), x.get("estado_actual"), x.get("fecha_consulta"),
                                                            " · sentencia firme" if x.get("sentencia_firme") else "") for x in H.get("casos") or []]
         if H.get("casos") else [])
    if a.para == "gancho":
        out = base + ["", "## Ganchos de historia (4–5 candidatos de familias distintas, todos con la foto a sangre)",
                      "- Familias: %s" % ", ".join(FAMILIAS),
                      "- Visual: SIEMPRE foto. `visual_datos: {\"foto\": \"<id de foto>\", \"etiqueta\": \"<lugar · año>\" (≤ %d)}`: la foto a sangre "
                      "cubre toda la pantalla, `pantalla` en el chip y `linea` entera desde el cuadro 0, que se enciende cuando la voz la dice. "
                      "La foto del gancho MUESTRA AL PROTAGONISTA (H12; las marcadas PROTAGONISTA arriba: %s). Entre ellas, la más fuerte "
                      "(el producto, la persona, el lugar)." % (ETIQUETA_GANCHO, ", ".join(k for k, f in sorted((H.get("fotos") or {}).items())
                                                                                       if es_protagonista(f, prot)) or "NINGUNA: hechos --check H12"),
                      "- Qué cuenta: el momento de la historia (el problema que la hizo nacer, la persona, la decisión, lo que estaba en juego). "
                      "NUNCA una revelación de la lista de arriba ni su número: H13 falla si el gancho escribe un número que está en una "
                      "revelación; el crítico puntúa «reserva» y un candidato que regala una revelación no gana.",
                      "- El gancho nombra al protagonista en la pantalla, la línea o la voz (H10).",
                      "- Bloqueadas por rotación: familias %s" % (", ".join(rec_g.get("familias") or []) or "ninguna"),
                      "- Sin cifra obligatoria (una historia abre con el hecho), pero cada número dicho tiene respaldo. Cada año dicho está en un hecho.",
                      "- La voz no abre con «Esta es la historia de…», «Te cuento…», «En el año…» ni con contexto: abre con el momento más fuerte."]
        print("\n".join(out))
        return 0
    if a.para == "critico":
        base += lineas_narracion(trabajo, g_actual(trabajo))
    out = base + ["", "## Límites del guion (historia.py guion --check: H3–H20 + V1–V5, V9, F1–F8 de video.py; devuelve TAL CUAL su línea RETORNO)",
                  "- PRIMERO la narración: guion.narracion = [{acto: 1, texto}, {acto: 2, texto}, {acto: 3, texto}], el texto corrido de cada acto "
                  "como lo diría una sola voz (%d–%d palabras en total ≈ %d s a 145 por minuto; con dígitos). Mídela con python3 scripts/historia.py "
                  "narracion <TRABAJO> --check (conectores, «según», personajes presentados, hilos). DESPUÉS repártela en escenas SIN cambiar una "
                  "palabra: la suma de las voces de cada acto (más el cierre en el 3) es la narración (H15)" % (*PALABRAS, OBJETIVO_S),
                  "- Flujo (H16): ≥ %d conectores causales o temporales por acto («pero», «por eso», «entonces», «dos años después», «mientras "
                  "tanto»); ≤ %d escena abre con «Según…»; dos escenas seguidas no abren igual; ≤ %.1f cortes por minuto (una escena puede "
                  "sostener un tramo largo). La voz NO tiene que empezar con «pero / por eso» (enlace es opcional: solo decide el efecto de sonido)"
                  % (CONECTORES_MIN_POR_ACTO, APERTURAS_ATRIBUIDAS_MAX, CORTES_MAX_POR_MIN),
                  "- Atribución (H4, H19): la voz atribuye o matiza SOLO lo en_disputa, los ALEGATO/ESTIMACIÓN/OPINIÓN y las citas (dice quién "
                  "habla antes de leerla); lo una_fuente se narra llano con la fuente en pantalla («fuente» en foto/cita, grafico.fuente en "
                  "tarjetas) o ya nombrada antes en el mismo acto. ≤ %d «según» por video, ≤ %d por acto, nunca en dos escenas seguidas, nunca la "
                  "misma fuente dos veces en voz. Varía: aposición («AMSA, la autoridad del lago, …»), verbo de la fuente («el tribunal calificó…»)"
                  % (SEGUN_MAX_VIDEO, SEGUN_MAX_ACTO),
                  "- Duración: apunta a %d s (%d–%d); el tope de %d s es para emergencias (V4 acepta 120–180; el gate avisa si pasas de %d). "
                  "Voz por escena: gancho %d–%d · foto %d–%d · cita %d–%d · capitulo %d–%d · "
                  "tarjeta %d–%d · golpe %d–%d · explica %d–%d · cierre %d–%d caracteres (ya en palabras; %.1f car/s)"
                  % (OBJETIVO_S, OBJETIVO_MIN_S, OBJETIVO_AVISO_S, DURACION_MAX_S, OBJETIVO_AVISO_S, *VD.CARACTERES["gancho"], *CARACTERES["foto"],
                     *CARACTERES["cita"], *CARACTERES["capitulo"], *CARACTERES_VIDEO_EN_HISTORIA["tarjeta"], *CARACTERES_VIDEO_EN_HISTORIA["golpe"],
                     *CARACTERES_VIDEO_EN_HISTORIA["explica"], *VD.CARACTERES["cierre"], VD.CPS),
                  "- promesa {texto (10–80, literal en la voz de la escena en), en: 2, pago, revela}: revela es el número R de la revelación que la "
                  "escena pago cuenta con sus palabras (H14)",
                  "- Tres actos (H8): «acto»: 1|2|3 en cada escena (el gancho es el 1); la primera escena de los actos 2 y 3 lleva rotulo {anio ≤ %d, "
                  "titulo ≤ %d palabras, lugar?} dibujado sobre la imagen mientras la voz sigue (en foto, cita, tarjeta, golpe o explica; opcional "
                  "en la escena 2 para el acto 1); una escena capitulo con voz propia es la excepción (≤ %d, el gate avisa). El giro (giro: true) "
                  "va en el acto 2, entre el %d y el %d %%. Nunca %d escenas del mismo tipo seguidas; ≤ %d escenas"
                  % (CAP_ANIO_CARACTERES, CAP_TITULO_PALABRAS, CAPITULOS[1], GIRO_ENTRE[0] * 100, GIRO_ENTRE[1] * 100, SEGUIDAS_MAX + 1, ESCENAS_MAX),
                  "- Hilos (H17): guion.hilos = [{id, escena: N} (la escena que lo paga lleva paga: [id]) | {id, sin_respuesta: «nunca se supo…»} "
                  "(la frase va en la narración del acto 3 o el cierre)]. Personajes (H18): la primera voz que los nombra los presenta",
                  "- Secuencias (H20): «secuencias»: [[2,3],[4,5,6],…] grupos de %d–%d escenas consecutivas del mismo acto (sin el gancho ni el "
                  "cierre; un giro o un rótulo solo abren una secuencia): su voz se graba de corrido. Si no las escribes, el gate las deriva"
                  % SECUENCIA,
                  "- foto: foto (id de una foto verificada; nunca null, icono ni mapa: si no hay del hecho, una de referencia), fecha (chip ≤ %d; «De referencia» si la foto no es del hecho), lugar ≤ %d, titular ≤ %d palabras, hechos [ids], cifra? {texto, etiqueta}, fuente ≤ %d (obligatoria si cita un hecho una_fuente o en_disputa cuya fuente no se mostró ni se nombró antes en el acto)"
                  % (CHIP_CARACTERES, LUGAR_CARACTERES, TITULAR_PALABRAS, FUENTE_CARACTERES),
                  "- cita: cita (id), la voz dice quién habla y la lee literal; resalte? (trozo literal), retrato? (id de foto), fuente?",
                  "- tarjeta/mapa/ranking/tiempo: tuit (1, 2…), golpe ≤ %d palabras, grafico {plantilla de templates/graficos/, kicker, titular, nota, fuente, datos}; foco: false si el zoom a la cifra estorba"
                  % VD.GOLPE_PALABRAS,
                  *VD.lineas_animaciones(st.get("animaciones_recientes") or []),
                  "- Cierre: rotulo («Lo que dejó»…), resumen %d–%d líneas ≤ %d, texto, tipo remate, forma LEGADO (lo normal): lo que la gente hace "
                  "HOY con lo que la historia dejó («Hoy, sus hijos y sus nietos siguen tomando Incaparina»); consecuencia {quien (gente: nietos, "
                  "clientes, trabajadores…), verbo (en presente)}, ≤ 1 cifra, sin «según» (H9). Forma consecuencia (con mecanismo) si la historia "
                  "termina mal. NEUTRO = nadie hace nada («la marca sigue», «la receta cambió», un resumen): bloquea en H-C6. La emoción la pone "
                  "el hecho, no los adjetivos"
                  % (*VD.RESUMEN_LINEAS, VD.RESUMEN_CARACTERES), "", "## Frases ya usadas (C11)"] + VD.frases_usadas(st["slug"]) + frases_historias(st["slug"])
    print("\n".join(out))
    return 0


def g_actual(trabajo):
    ruta = os.path.join(trabajo, "guion.json")
    return leer(ruta) if os.path.exists(ruta) else {}


def narracion_corrida(trabajo, g):
    """La voz de corrido por acto, en palabras (locucion.json) si ya pasó el gate; si no, guion.narracion."""
    ruta = os.path.join(trabajo, "locucion.json")
    es = g.get("escenas") or []
    if os.path.exists(ruta) and es:
        loc = leer(ruta)
        por_acto = {}
        for L in loc["escenas"]:
            ac = acto_de(es[L["n"] - 1], L["n"]) if L["n"] - 1 < len(es) else 3
            por_acto.setdefault(ac, []).append(L["voz"])
        return [(ac, " ".join(por_acto[ac])) for ac in sorted(por_acto, key=str)]
    return narracion_de(g)


def lineas_narracion(trabajo, g):
    """«## Narración (de corrido)» + la duración y el presupuesto, para el crítico."""
    narr = narracion_corrida(trabajo, g)
    if not narr:
        return []
    ruta = os.path.join(trabajo, "locucion.json")
    est = leer(ruta)["estimado_s"] if os.path.exists(ruta) else estimado_s(g)
    es = g.get("escenas") or []
    segun = sum(len(RE_SEGUN.findall(VD.sin_pausas(e.get("texto") or ""))) for e in es + [g.get("cierre") or {}])
    return ["", "## Narración (de corrido): léela como un texto, como quien oye un documental con los ojos cerrados (H-C4 flujo)"] + \
        ["- Acto %s: %s" % (ac, t) for ac, t in narr] + \
        ["- Duración objetivo %d s (%d–%d) · estimado %.0f s · %d palabras · %d «según» en voz (≤ %d)"
         % (OBJETIVO_S, OBJETIVO_MIN_S, OBJETIVO_AVISO_S, est, sum(VD.palabras(t) for _, t in narracion_de(g)) or sum(VD.palabras(t) for _, t in narr), segun, SEGUN_MAX_VIDEO)]


def digesto_oyente(trabajo, H):
    """Solo lo que un espectador oye y lee, en orden: primero la narración de corrido (para oírla como un documental) y
    luego la voz en palabras (locucion.json) con lo que hay en pantalla por escena. Sin cronología, sin encuadre, sin
    fuentes ni ids: el oyente ingenuo no sabe nada más."""
    ruta = os.path.join(trabajo, "locucion.json")
    if not os.path.exists(ruta):
        return falla("falta locucion.json: corre python3 scripts/historia.py guion %s --check" % VD.rel(trabajo))
    loc, g = leer(ruta), leer(os.path.join(trabajo, "guion.json"))
    es, citas = g.get("escenas") or [], {q["id"]: q for q in H.get("citas") or []}
    out = ["# Lo que se oye y se lee, en orden (%d escenas + cierre, ≈ %.0f s)" % (len(es), loc["estimado_s"]), "",
           "## La narración de corrido (óyela primero, de principio a fin, sin pantalla)", ""]
    out += ["%s" % t for _, t in narracion_corrida(trabajo, g)]
    out += ["", "## Escena por escena (lo que se lee en pantalla y lo que dice la voz)", ""]
    for L in loc["escenas"]:
        e = es[L["n"] - 1] if L["n"] - 1 < len(es) else dict(g.get("cierre") or {}, tipo="cierre")
        pant = pantalla_de(e, citas)
        out += ["E%d · %s%s" % (L["n"], L["tipo"], " · PANTALLA: %s" % pant if pant else ""), "   VOZ: %s" % L["voz"]]
    print("\n".join(out))
    return 0


def pantalla_de(e, citas):
    """Lo que se LEE en una escena (sin ids ni fuentes)."""
    t = e.get("tipo")
    r = rotulo_de(e)
    # el rótulo de acto en pantalla: año grande, título y lugar (sin «Acto N de M»: decisión del usuario, 2026-10-27)
    rot = ["%s · %s · %s" % (r["anio"], r["titulo"], r["lugar"])] if r and not r["capitulo"] else []
    if t == "gancho":
        partes = [e.get("pantalla"), e.get("linea"), (e.get("visual_datos") or {}).get("etiqueta")]
    elif t == "foto":
        c = e.get("cifra") or {}
        partes = [e.get("fecha"), e.get("lugar"), e.get("titular"), c.get("texto"), c.get("etiqueta")]
    elif t == "cita":
        q = citas.get(e.get("cita")) or {}
        partes = ["«%s»" % q.get("texto", ""), q.get("autor"), q.get("cargo"), e.get("traduccion")]
    elif t == "capitulo":
        partes = ["Capítulo %s" % e.get("numero"), e.get("anio"), e.get("titulo"), e.get("lugar")]
    elif t in VD.CON_TUIT or t == "escala":
        gr = e.get("grafico") or {}
        tit = gr.get("titular")
        partes = [e.get("golpe"), gr.get("kicker"), " ".join(tit) if isinstance(tit, list) else tit, e.get("etiqueta")]
    elif t == "explica":
        partes = [e.get("titulo")] + [str(p) for p in e.get("pasos") or []]
    elif t == "cierre":
        partes = [e.get("rotulo")] + list(e.get("resumen") or []) + [e.get("final")]
    else:   # golpe, definicion, adivina
        partes = [e.get("pantalla"), e.get("linea"), e.get("termino"), e.get("definicion"), e.get("pregunta")] + list(e.get("opciones") or [])
    return " · ".join(str(x).strip() for x in rot + partes if x and str(x).strip())


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
        "actos": [{"numero": rotulo_de(e).get("numero") or acto_de(e, i), "anio": rotulo_de(e)["anio"], "titulo": rotulo_de(e)["titulo"],
                   "escena": i} for i, e in enumerate(escenas_g, 1) if rotulo_de(e)],
        "capitulos": [{"numero": e.get("numero"), "anio": e.get("anio"), "titulo": e.get("titulo")} for e in escenas_g if e.get("tipo") == "capitulo"],
        "narracion": g.get("narracion"), "hilos": g.get("hilos"), "secuencias": g.get("secuencias"),
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


def etiqueta_estado(x):
    if x.get("estado") == "confirmado":
        return ""
    if x.get("estado") == "una_fuente":
        return " *(una fuente: %s)*" % (medio_de(x) or "?")
    return " *(en disputa)*"


def usados(escenas, H):
    """Los hechos y las citas que cuenta el guion, por acto: [(rótulo del acto, [hechos y citas])]."""
    hechos = {x["id"]: x for x in (H.get("hechos") or []) + (H.get("citas") or [])}
    nombres = {a.get("n"): a for a in H.get("actos") or [] if isinstance(a, dict)}
    bloques, vistos, acto_abierto = [("Gancho y promesa", [])], set(), None
    for i, e in enumerate(escenas, 1):
        r, ac = rotulo_de(e), acto_de(e, i)
        if r:
            bloques.append(("%s %s · %s · %s" % ("Capítulo" if r["capitulo"] else "Acto", r.get("numero") or ac or "", r["anio"], r["titulo"]), []))
            acto_abierto = ac
        elif ac and ac != acto_abierto and i > 1:
            a = nombres.get(ac) or {}
            bloques.append(("Acto %s · %s" % (ac, a.get("titulo") or a.get("nombre") or ""), []))
            acto_abierto = ac
        for hid in (e.get("hechos") or []) + ([e["cita"]] if e.get("cita") else []):
            if hid in hechos and hid not in vistos:
                vistos.add(hid)
                bloques[-1][1].append(hechos[hid])
    return [b for b in bloques if b[1]]


def fuentes_md(st, escenas, H):
    L = ["# Fuentes · %s" % st.get("tema"), "",
         "Para la descripción o el primer comentario. Cada hecho que cuenta el video con las fuentes que lo respaldan; "
         "lo de una sola fuente se narra con esa fuente en pantalla; lo que está «en disputa» la voz lo atribuye.", ""]
    for rotulo, xs in usados(escenas, H):
        L += ["## %s" % rotulo, ""]
        for x in xs:
            L.append("- %s%s" % (x.get("texto"), etiqueta_estado(x)))
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
        for x in ids:   # el crédito de Commons ya trae la licencia («Foto: autor · CC BY-SA 4.0»): no se repite
            cred, lic = fotos[x].get("credito") or "", fotos[x].get("licencia") or ""
            L.append("- %s · %s" % (cred if lic in cred else "%s · %s" % (cred, lic), fotos[x].get("pagina") or fotos[x].get("url")))
        L.append("")
    L.append("Sígueme: %s" % " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES))
    return "\n".join(L) + "\n"


def cronologia_md(st, escenas, H):
    xs = sorted([x for _, b in usados(escenas, H) for x in b], key=lambda x: (str(x.get("fecha") or x.get("cuando") or ""), x["id"]))
    L = ["# Cronología verificada · %s" % st.get("tema"), "", "La línea de tiempo de lo que cuenta el video (%s)." % st["fecha"], ""]
    for x in xs:
        medios = ", ".join(dict.fromkeys(f.get("medio") or NT.dominio(f.get("url")) for f in x.get("fuentes") or []))
        quien = "%s: «%s»" % (x.get("autor"), x.get("texto")) if x.get("autor") else x.get("texto")
        estado = "confirmado" if x.get("estado") == "confirmado" else "una fuente (%s)" % (medio_de(x) or "?") if x.get("estado") == "una_fuente" \
            else "en disputa%s" % (" — %s" % x["nota"] if x.get("nota") else "")
        L.append("- **%s** · %s · %s · %s" % (x.get("fecha") or x.get("cuando") or "s. f.", quien, estado, medios))
    if H.get("conflictos"):
        L += ["", "## Fechas en conflicto", ""] + ["- %s y %s: el mismo hecho con años distintos" % tuple(c) for c in H["conflictos"]]
    return "\n".join(L) + "\n"


REENVIO = ("voz", "voz-falsa", "descargar", "partir", "escuchar", "grabar", "montar", "revisar")


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
    q.add_argument("--de-fuente", metavar="URL", help="la og:image de una fuente ya leída: crédito «Foto: <medio>», origen por su clase, fecha de la nota")
    q.add_argument("--credito")
    q.add_argument("--origen", choices=["oficial", "medio", "empresa"])
    q.add_argument("--descripcion")
    q.add_argument("--fecha")
    q.add_argument("--lugar")
    q.add_argument("--retrato-de", help="si es el retrato de una persona, su nombre (el de la cita); un objeto o un lugar no lo lleva")
    q.add_argument("--encaje", choices=["contener"], help="gráfico, cartel o logo con texto: márgenes para que la foto a sangre no lo recorte")
    x = q.add_mutually_exclusive_group()
    x.add_argument("--referencia", action="store_true", help="la foto no es del hecho sino de referencia (el lugar, la institución, la persona, "
                   "el producto o la época): el crédito dice «Foto de referencia: …»")
    x.add_argument("--protagonista", action="store_true", help="la foto muestra al protagonista del encuadre (el producto, el edificio, la persona): "
                   "H12 la exige en el gancho")
    q.add_argument("--extmetadata", help="pruebas: extmetadata de Commons guardado (solo comprueba la licencia, sin red)")
    q = sub.add_parser("hechos")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true")
    q.add_argument("--reclasificar", action="store_true", help="propone una_fuente para cada en_disputa de un solo grupo sin discrepancia en la nota")
    q.add_argument("--aplicar", action="store_true", help="con --reclasificar: escribe los cambios y repite el check")
    q.add_argument("--eje")
    sub.add_parser("consolidar").add_argument("trabajo")
    q = sub.add_parser("encuadre", help="la estructura v3 del encuadre: actos, espina, hilos, personajes, periodos")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q = sub.add_parser("narracion", help="mide la narración de corrido (guion.narracion) antes de repartirla en escenas")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", help="falla con H16–H19 sobre la narración sola")
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--para", choices=["investigador", "verificador", "gancho", "guionista", "critico", "oyente", "editor"], default="guionista")
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
            "consolidar": cmd_consolidar, "encuadre": cmd_encuadre, "narracion": cmd_narracion, "digesto": cmd_digesto,
            "ganchos": cmd_ganchos, "tarjetas": cmd_tarjetas, "guion": cmd_guion, "tiempos": cmd_tiempos,
            "fotos-contacto": cmd_fotos_contacto, "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
