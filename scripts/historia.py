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
                               (H34: falla si el encuadre nombra algo que la verificación descartó)
  premisas TRABAJO --check     solo H34 (consolida y lista lo del encuadre que la verificación tumbó; 0 = nada)
  digesto TRABAJO --para investigador|verificador --eje E | gancho | guionista | critico | oyente | editor
        (oyente: la narración de corrido y luego la voz con lo que hay en pantalla, sin cronología ni ids; editor: re-encuadre)
  ganchos TRABAJO --check | --opciones | --elegir ID | --usar [ID] [--segundo ID]   → video.py ganchos con las familias y el visual foto de historia
  cierres TRABAJO --check | --opciones | --usar ID | --propio TEXTO [--forma --mecanismo --quien --verbo]   → video.py
        cierres (5 cierres para que el usuario elija) y, al cambiar, narracion --check + guion --check
  narracion TRABAJO [--check]  mide guion.narracion (palabras, segundos, conectores, «según», personajes, hilos) ANTES de
        repartirla en escenas; --check falla con H16–H19 sobre la narración sola
  tarjetas TRABAJO             las escenas con gráfico → base/tuit_N.html (materializar.py, R1–R6) y video.json.tarjetas
  guion TRABAJO --check        H4–H20 + (tarjetas) + video.py guion (V1–V5, V9, F1–F8) → locucion.json; la última línea
        RETORNO {...} es lo que el guionista devuelve al Workflow (tipos de cada escena, sin el cierre); deriva las
        secuencias de voz si el guion no las trae
  probar TRABAJO --cambios JSON|ARCHIVO   el crítico prueba un arreglo ANTES de escribirlo: lo aplica a una copia (con el
        mismo texto en la narración, la promesa y el candidato del gancho) y corre narracion --check y guion --check;
        el TRABAJO no se toca (0 pasa · 1 el gate lo rechaza · 2 cambio mal dado)
  aplicar TRABAJO --cambios JSON|ARCHIVO   los mismos cambios que probar, en el TRABAJO real (guion.previo.json de copia);
        si el gate los rechaza restaura la copia; RETORNO {"escenas_cambiadas": [...]} (el guionista aplica así las faltas
        y mejoras del crítico que traen `cambios`, y revierte una escena desde guion.previo.json)
  tiempos TRABAJO              video.py tiempos con los constructores de foto, cita y capitulo (y el rótulo de acto), con
        V16 (la voz se aprieta donde se cortó dentro de un nombre o una cifra) → escenas.json
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
import fuentes_web as FW  # noqa: E402
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402
import video as VD  # noqa: E402

# ---- formato (decisiones del usuario, 2026-10-24) ----
OBJETIVO_S, DURACION_MAX_S = 150, 180       # «regularmente 2 o 3 minutos»; 180 s es el tope de YouTube Shorts
OBJETIVO_MIN_S, OBJETIVO_AVISO_S = 135, 165  # «apunta a 150 (135–165)»: el gate avisa (H5) si pasa de 165; 180 es para emergencias
OBJETIVO_DURO_S = 170   # H5 falla por encima (m023, m033, m052: guiones de 176 s aprobados y recortados después con un retoque)
VD.DURACIONES["historia"] = {"s": OBJETIVO_S, "tarjetas": (0, 6), "golpes": (0, 10), "tol": 0.2}   # V4: 120–180 s
# la narración de corrido (v3, 2026-10-27): la voz real va a ≈ 145 palabras por minuto (medido: 416 palabras en 172 s),
# así que 150 s son ≈ 360 palabras; PALABRAS orienta (aviso fuera), PALABRAS_DURO falla
PALABRAS, PALABRAS_DURO = (320, 400), (280, 410)
# /serie (scripts/serie.py): la investigación compartida cubre toda la serie (hasta EJES_MAX_SERIE ejes) y cada parte es
# un video de ≈ 90 s (formato «historia-serie» en video.json): aplicar_formato cambia estos valores al abrir el TRABAJO
EJES_MAX_SERIE = 5
PALABRAS_SERIE, PALABRAS_SERIE_DURO = (190, 250), (170, 265)
FORMATOS = {"historia": {"OBJETIVO_S": 150, "OBJETIVO_MIN_S": 135, "OBJETIVO_AVISO_S": 165, "OBJETIVO_DURO_S": 170,
                         "PALABRAS": (320, 400), "PALABRAS_DURO": (280, 410), "HECHOS_MIN": 6, "HILOS": (2, 6)},
            "historia-serie": {"OBJETIVO_S": 90, "OBJETIVO_MIN_S": 75, "OBJETIVO_AVISO_S": 105, "OBJETIVO_DURO_S": 110,
                               "PALABRAS": PALABRAS_SERIE, "PALABRAS_DURO": PALABRAS_SERIE_DURO, "HECHOS_MIN": 4,
                               "HILOS": (1, 4)},
            # /serie en modo caso (2026-11-06): un caso complejo por temas, partes de ≈ 130 s (115–150)
            "historia-caso": {"OBJETIVO_S": 130, "OBJETIVO_MIN_S": 115, "OBJETIVO_AVISO_S": 145, "OBJETIVO_DURO_S": 150,
                              "PALABRAS": (290, 350), "PALABRAS_DURO": (260, 365), "HECHOS_MIN": 8, "HILOS": (2, 5)}}


RESUMEN_EXTRA_S = 30   # SE14: segundos de más que puede durar la última parte de una serie por su resumen


def aplicar_formato(trabajo):
    """Los objetivos de duración y palabras del TRABAJO (video.json → formato): «historia» (150 s) o «historia-serie»
    (≈ 90 s, una parte de /serie). Rebinda los globales que leen el gate, la narración y el digesto."""
    ruta = os.path.join(trabajo or "", "video.json")
    st = leer(ruta) if trabajo and os.path.exists(ruta) else {}
    fo = dict(FORMATOS.get(st.get("formato") or "historia", FORMATOS["historia"]))
    ser = st.get("serie") if isinstance(st.get("serie"), dict) else {}
    if ser.get("de") and ser.get("parte") == ser.get("de"):
        # SE14 (decisión del usuario, 2026-11-07): la última parte de una serie lleva el resumen de toda la serie
        # (20–30 s) y puede durar esos segundos de más; el tope sigue en DURACION_MAX_S (180 s, YouTube Shorts)
        extra, pal = RESUMEN_EXTRA_S, round(RESUMEN_EXTRA_S * 145 / 60)
        fo.update({"OBJETIVO_AVISO_S": fo["OBJETIVO_AVISO_S"] + extra,
                   "OBJETIVO_DURO_S": min(DURACION_MAX_S, fo["OBJETIVO_DURO_S"] + extra),
                   "PALABRAS": (fo["PALABRAS"][0], fo["PALABRAS"][1] + pal),
                   "PALABRAS_DURO": (fo["PALABRAS_DURO"][0], fo["PALABRAS_DURO"][1] + pal)})
    globals().update(fo)
    VD.DURACIONES["historia"] = {"s": fo["OBJETIVO_S"], "tarjetas": (0, 6), "golpes": (0, 10), "tol": 0.2 if fo["OBJETIVO_S"] >= 150 else 0.22}
    return st
TIPOS_PROPIOS = ("foto", "cita", "capitulo", "red", "vias", "lupa", "deptos", "pagina", "cortina", "archivo", "bandos")   # «vias» = el mapa vial real por capas (H27, 2026-11-12); «toma» (clips de video) retirada el 2026-11-06: muchas veces sin coherencia; una cita o una foto
# «toma» queda solo para que un guion viejo con esa escena llegue al gate TM0 (y falle ahí, con su mensaje)
CARACTERES = {"foto": (40, 280), "cita": (30, 280), "capitulo": (10, 90), "toma": (20, 280), "red": (60, 320), "vias": (60, 320), "lupa": (60, 320), "deptos": (60, 320), "pagina": (60, 320), "cortina": (50, 300), "archivo": (50, 320), "bandos": (60, 320)}   # voz ya en palabras (≈ 15.5 car/s)
# en historia una tarjeta o un golpe pueden sostener un tramo más largo de narración que en /video
CARACTERES_VIDEO_EN_HISTORIA = {"tarjeta": (40, 260), "mapa": (40, 260), "ranking": (40, 260), "tiempo": (40, 260),
                                "explica": (40, 260), "golpe": (20, 130)}
# estructura por ACTOS (v3): tres actos fijos; los actos 2 y 3 se marcan con un rótulo sobre la primera escena del acto
# (sin detener la voz); la escena capitulo con voz propia queda como excepción (0–2, el gate avisa)
ACTOS = (("planteamiento", 1), ("nudo", 2), ("desenlace", 3))
PUNTOS_ESPINA = ("detonante", "punto_medio", "climax", "resolucion")
PERIODOS, HILOS, PERSONAJES_MAX, PRESENTACION_PALABRAS = (2, 5), (2, 6), 12, 8
CAPITULOS, ROTULOS, SEGUIDAS_MAX, GIRO_ENTRE = (0, 2), (2, 3), 3, (0.40, 0.75)
ESCENAS_ARCHIVO = ("vias", "lupa", "deptos", "pagina", "cortina", "archivo", "bandos")   # las escenas propias que se dibujan sobre un archivo real (cuentan como composición distinta, H26)
ROTULO_TIPOS = ("foto", "cita", "tarjeta", "mapa", "ranking", "tiempo", "golpe", "explica", "red", "vias", "lupa", "deptos", "pagina", "cortina", "archivo", "bandos")
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
RE_DEMOSTRATIVO, HILO_LIBRES = VD.RE_DEMOSTRATIVO, VD.HILO_LIBRES   # compartidas con /video (video.py)
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
PUNTAJES = ("gancho", "tension", "claridad", "flujo", "precision", "cierre", "recompensa")   # critica.json en modo historia (W12); recompensa = H-C7 (2026-11-10)
# ---- verdad ----
# una_fuente = UNA fuente seria sin nada que la contradiga: se narra llano con la fuente en pantalla; en_disputa = las
# fuentes difieren (la voz atribuye o matiza). tipo_hecho: lo que no es un acto público verificable (una acusación, una
# promesa de parte, una cifra no oficial, una opinión) se atribuye en voz aunque tenga una sola fuente (criterio BBC:
# se atribuye lo que no puede corroborarse o es de parte)
ESTADOS = ("confirmado", "una_fuente", "en_disputa", "no_confirmado")
PUBLICABLES = ("confirmado", "una_fuente", "en_disputa")
TIPOS_HECHO, ATRIBUIR_SIEMPRE = ("acto", "alegato", "estimacion", "opinion"), ("alegato", "estimacion", "opinion")
# «según», aperturas atribuidas y conectores de la narración: compartidos con /video (video.py, V18)
RE_SEGUN, RE_SEGUN_FUENTE, APERTURA_ATRIBUIDA = VD.RE_SEGUN, VD.RE_SEGUN_FUENTE, VD.APERTURA_ATRIBUIDA
CONECTORES_NARRACION = VD.CONECTORES_NARRACION   # H16: ≥ 2 por acto
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
                        r"\bversi[oó]n\b|\bcuenta(?:n)?\b|\brecuerda\w*|\basegur\w+|\bnarr\w+|"
                        r"\bcalcul\w+|\bestim\w+|\bpara (?:la|el) (?:acusaci[oó]n|fiscal\w*|MP|CICIG|defensa)\b", re.I)   # una ESTIMACIÓN se atribuye con «calculaba», «estimó»
# presunción de inocencia: sin sentencia firme no se dice que alguien cometió el delito
VETADAS = re.compile(r"\b(?:culpables?|asesin[oa]s?|delincuentes?|criminal(?:es)?|ladr[oó]n(?:es)?|corrupt[oa]s?)\b", re.I)
# fuentes que cuentan además de las de fuentes_web.py: organismos, academia, archivo y prensa internacional. Wikipedia es un
# mapa, nunca evidencia: se cita su referencia, no la página
OTROS_OFICIALES = {"cicig.org": "CICIG", "un.org": "ONU", "oas.org": "OEA", "worldbank.org": "Banco Mundial",
                   "iadb.org": "BID", "cepal.org": "CEPAL", "anacafe.org": "Anacafé", "imf.org": "FMI", "fao.org": "FAO",
                   "state.gov": "Departamento de Estado", "justice.gov": "Departamento de Justicia (EE. UU.)",
                   "treasury.gov": "Tesoro (EE. UU.)", "corteidh.or.cr": "Corte IDH",
                   # agencias científicas: la fuente primaria de sismos, volcanes, clima y relieve (m186: /video-3d,
                   # 2026-11-14: pubs.usgs.gov y earthquake.usgs.gov salían «NO CUENTA» y eran la fuente del video)
                   "usgs.gov": "Servicio Geológico de EE. UU. (USGS)", "noaa.gov": "NOAA", "nasa.gov": "NASA"}
ACADEMICAS = {"scielo.org", "jstor.org", "redalyc.org", "dialnet.unirioja.es", "persee.fr", "openedition.org",
              "flacso.edu.gt", "asies.org.gt", "icefi.org", "avancso.org.gt", "cirma.org.gt", "academia.edu",
              "britannica.com", "copernicus.org"}
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
                   "nbcnews.com": "nbc", "cbsnews.com": "cbs", "npr.org": "npr", "theworld.org": "the-world", "usatoday.com": "usa-today",
                   "time.com": "time", "elfinanciero.com.mx": "el-financiero", "expansion.mx": "expansion",
                   "eleconomista.com.mx": "el-economista-mx"}
# una nota de agencia publicada por otro diario cuenta como la agencia (su grupo, el mismo de FW.MEDIOS), no como el
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
                  "bloomberglinea.com": "Bloomberg Línea", "eleconomista.net": "El Economista", "chapinlandia.com": "Chapinlandia",
                  "theworld.org": "The World (PRI)"}
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
# una foto que no es del hecho (el lugar, la institución, la persona, el producto o la época) lleva su
# crédito, que dice «Foto de referencia: …» para que nadie la tome por la del momento; cada eje trae ≥ FOTOS_POR_EJE fotos
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
    return FW.plano_cita(s)


# ---------- registros de historias anteriores (rotación de ganchos y cierres, C11, música) ----------
PALETA_NO_REPETIR = 2   # el tinte no se repite con las últimas N piezas de video (historias, series, explicaciones, videos)


def paletas_recientes(slug_actual=None, n=PALETA_NO_REPETIR):
    """Las paletas de las últimas n piezas de video de cualquier flujo, la más reciente al final (decisión del usuario,
    2026-11-09: «otra serie y otra vez el mismo azul»)."""
    regs = []
    for archivo, clave in (("historias", "historias"), ("series", "series"), ("explicaciones", "explicaciones"), ("videos", "videos")):
        ruta = os.path.join(RAIZ, "memoria", archivo + ".json")
        if not os.path.exists(ruta):
            continue
        d = leer(ruta)
        lista = d if isinstance(d, list) else (d.get(clave) or next((v for v in d.values() if isinstance(v, list)), []))
        regs += [r for r in lista if isinstance(r, dict) and r.get("paleta") and r.get("slug") != slug_actual]
    regs.sort(key=lambda r: (r.get("fecha") or "", r.get("id") or ""))
    return [r["paleta"] for r in regs[-n:]]


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
    """R9 y F7 de una historia contra el feed entero (video.piezas_feed: todos los flujos, con las partes de /serie):
    la familia de las últimas ROTACION_FAMILIAS piezas (el visual no rota: siempre es la foto) y el cierre."""
    piezas = VD.piezas_feed(slug_actual)
    return (VD.ganchos_recientes(slug_actual, ROTACION_FAMILIAS, 0, piezas), VD.cierres_recientes(slug_actual, piezas))


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
    recientes_p = [] if a.fixture else paletas_recientes(slug)
    paleta = a.paleta or next((p for p in paletas() if p not in recientes_p), "obsidiana")
    if paleta not in paletas():
        print("--paleta: una de %s" % ", ".join(paletas()), file=sys.stderr)
        return 2
    try:
        pista = VD.elegir_musica(paleta, a.musica)
    except ValueError as ex:
        return falla(str(ex))
    # la maqueta no rota contra lo producido (sus ganchos y cierres son fijos)
    rec_g, rec_c = ({"familias": [], "visuales": []}, {"tipos": [], "formas": [], "mecanismos": []}) if a.fixture else recientes(slug)
    ruta = os.path.join(trabajo, "video.json")
    st = leer(ruta) if os.path.exists(ruta) else {}
    if not st or getattr(a, "realizacion", None):   # quién dibuja: se fija al crear el TRABAJO (uno empezado con un motor termina con él)
        st["realizacion"] = VD.realizacion_de("historia", getattr(a, "realizacion", None))
    st.update({"tipo": "historia", "slug": slug, "tema": a.tema, "fecha": datetime.date.today().isoformat(),
               "hilo": VD.rel(os.path.join(trabajo, "base")), "paleta": paleta, "musica": pista["id"],
               "musica_forzada": a.musica, "duracion": "historia", "objetivo_s": OBJETIVO_S,
               "ganchos_recientes": rec_g, "cierres_recientes": rec_c, "animaciones_recientes": [] if a.fixture else animaciones_recientes(slug),
               "promesas_recientes": [] if a.fixture else VD.promesas_recientes(slug)})
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
            2.2 - 0.3 * (k % 4), -0.743 + 0.012 * (k % 4), 0.131 - 0.018 * (k % 4)),   # k % 4: más hondo el fractal queda negro (sin detalle)
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
    if c in (None, "medio") and not (FW.dominio(url).endswith("wikipedia.org")):
        ag = agencia_de(archivo)
        if ag:
            return "medio", ag
    return c, g


def clasificar_dominio(url, propios=()):
    d = FW.dominio(url)
    if d.endswith("wikipedia.org") or d.endswith("wikimedia.org"):
        return None, d
    if any(d == x or d.endswith("." + x) for x in propios or ()):
        return "empresa", d
    c, g = FW.clasificar(url)
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
    return os.path.join(DESCARGAS, "%s-%s" % (re.sub(r"[^a-z0-9]+", "-", FW.dominio(url)), hashlib.sha1(url.encode()).hexdigest()[:10]))


def nombre_medio(url):
    d = FW.dominio(url)
    return next((v for k, v in NOMBRES_MEDIOS.items() if d == k or d.endswith("." + k)), None) or FW.OFICIALES.get(d) or OTROS_OFICIALES.get(d) or d


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
            datos, tipo = FW.bajar(intento, limite=40_000_000)
            origen = intento
            break
        except Exception as ex:  # noqa: BLE001 — cualquier fallo de red: se intenta la copia de Wayback
            error = ex
    else:
        raise RuntimeError("no se pudo bajar %s ni su copia en Wayback (%s)" % (url, error))
    meta = {"url": url, "leida_de": origen, "dominio": FW.dominio(url), "clase": clasificar(url)[0]}
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
        p = FW._Texto()
        crudo_html = datos.decode(enc, "replace")
        p.feed(crudo_html)
        texto = re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t\r\f\v]+", " ", "".join(p.partes))).strip()
        img = p.meta.get("og:image") or p.meta.get("twitter:image") or p.meta.get("twitter:image:src")
        meta.update(titulo=html.unescape(p.meta.get("og:title") or p.titulo).strip(), fecha=FW.fecha_de(p.meta, p.ld),
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
            req = urllib.request.Request(url, headers={"User-Agent": COMMONS_UA if origen == "commons" else FW.AGENTE})
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
    otra = foto_repetida(trabajo, rec)
    if otra:
        os.remove(os.path.join(trabajo, dst))
        if rec["muestra"] and not otra.get("muestra"):
            otra["muestra"] = rec["muestra"]   # la marca H12 no se pierde
            escribir(os.path.join(trabajo, "fotos", otra["id"] + ".json"), otra)
        print("foto %s: es la misma imagen que %s (ya está como fotos/%s.jpg: «%s»); usa %s en tu verificación"
              % (a.id, otra["id"], otra["id"], (otra.get("descripcion") or "")[:70], otra["id"]))
        print("RETORNO %s" % json.dumps({"id": otra["id"], "repetida_de": a.id}, ensure_ascii=False))
        return 0
    if a.referencia and not a.lugar:
        print("AVISO %s: foto de referencia sin --lugar: el chip de la escena no podrá decir dónde es (y no usará el "
              "lugar del hecho)" % a.id)
    if getattr(a, "retrato_evidencia", None):
        rec["retrato_evidencia"] = a.retrato_evidencia.strip()
    rec["focos"] = focos_de(dst, rec.get("retrato_de"))
    if getattr(a, "proceso", None):   # m122: muestra a alguien detenido, esposado o en audiencia → solo en la escena de su proceso
        rec["proceso"] = a.proceso.strip()
    escribir(os.path.join(trabajo, "fotos", a.id + ".json"), rec)
    registrar_foto(trabajo, rec)
    print("foto %s · %d×%d · %s (%s)%s → %s" % (a.id, w, h, rec["credito"], origen, " · PROTAGONISTA" if rec["muestra"] else "", dst))
    imprimir_focos(rec)
    return 0


def registrar_foto(trabajo, rec):
    """m120: una foto bajada después de consolidar (el QA de fotos de una parte, una de referencia) entra a historia.json →
    fotos, para que H7 la tenga por verificada; en una parte de serie (<TRABAJO>/parte-N) también a la investigación
    compartida (su fotos/ e historia.json), para que la vean las partes siguientes."""
    destinos = [trabajo]
    padre = os.path.dirname(trabajo)
    if re.fullmatch(r"parte-\d+", os.path.basename(trabajo)) and os.path.exists(os.path.join(padre, "historia.json")):
        destinos.append(padre)
    for d in destinos:
        ruta_h = os.path.join(d, "historia.json")
        if not os.path.exists(ruta_h):
            continue
        if d != trabajo:
            os.makedirs(os.path.join(d, "fotos"), exist_ok=True)
            for ext in (".jpg", ".json"):
                src = os.path.join(trabajo, "fotos", rec["id"] + ext)
                if os.path.exists(src):
                    shutil.copyfile(src, os.path.join(d, "fotos", rec["id"] + ext))
        H = leer(ruta_h)
        if isinstance(H.get("fotos"), dict):
            H["fotos"][rec["id"]] = rec
            escribir(ruta_h, H)
            print("foto %s registrada en %s" % (rec["id"], VD.rel(ruta_h)))


# ---------- focos: dónde están las caras de cada foto (sub-planos, recorte vertical, tarjeta de persona) ----------
BIN_CARAS = os.path.join(RAIZ, "sesiones", "_descargas", "bin", "caras")
CARA_CONF_MIN = 0.5


def detectar_caras(rutas):
    """{ruta: [{x, y, w, h, conf}]} con Vision de macOS (scripts/caras.swift, compilado una vez en BIN_CARAS); sin swift
    o sin macOS devuelve {} y las fotos quedan sin focos (la cámara usa los tercios)."""
    rutas = [r for r in rutas if r and os.path.exists(r)]
    if not rutas:
        return {}
    fuente = os.path.join(RAIZ, "scripts", "caras.swift")
    if not os.path.exists(BIN_CARAS) or os.path.getmtime(BIN_CARAS) < os.path.getmtime(fuente):
        if not shutil.which("swiftc"):
            return {}
        os.makedirs(os.path.dirname(BIN_CARAS), exist_ok=True)
        r = subprocess.run(["swiftc", "-O", fuente, "-o", BIN_CARAS], capture_output=True, text=True)
        if r.returncode:
            print("AVISO no compila scripts/caras.swift: %s" % (r.stderr.strip().splitlines() or ["?"])[-1])
            return {}
    r = subprocess.run([BIN_CARAS] + rutas, capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {}


def focos_de(ruta, retrato_de=None):
    """Las caras de una foto como focos [{x, y, w, h, que: rostro, persona?}] de izquierda a derecha (las de menos
    confianza fuera); un retrato con una sola cara la marca como de esa persona."""
    caras = [c for c in detectar_caras([ruta]).get(ruta, []) if c.get("conf", 0) >= CARA_CONF_MIN]
    focos = [{"x": round(c["x"], 4), "y": round(c["y"], 4), "w": round(c["w"], 4), "h": round(c["h"], 4), "que": "rostro"}
             for c in sorted(caras, key=lambda c: c["x"])]
    if retrato_de and len(focos) == 1:
        focos[0]["persona"] = retrato_de
    return focos


def imprimir_focos(rec):
    fs = rec.get("focos") or []
    if not fs:
        print("  focos: ninguna cara (la cámara usa los tercios; un objeto o un lugar se marca con historia.py focos --foco)")
    for k, f in enumerate(fs, 1):
        print("  cara %d · x %.2f y %.2f · %s" % (k, f["x"] + f["w"] / 2, f["y"] + f["h"] / 2, f.get("persona") or
              "¿quién? → historia.py focos TRABAJO --foto %s --cara %d --persona \"Nombre\" --evidencia \"pie o categoría\"" % (rec["id"], k)))


def cmd_focos(a):
    """Los focos de las fotos del TRABAJO: sin --foto, detecta las caras de las que no tienen focos (o todas, con
    --rehacer) y lista cada cara; con --foto y --cara, dice de quién es (--persona, con --evidencia: el pie o la
    categoría que la nombra) o la quita (--quitar); --foco x,y,w,h agrega un foco a mano (un objeto, un cartel)."""
    trabajo = os.path.abspath(a.trabajo)
    rutas = sorted(glob.glob(os.path.join(trabajo, "fotos", "*.json")))
    if a.foto:
        rutas = [r for r in rutas if os.path.basename(r)[:-5] == a.foto]
        if not rutas:
            return falla("no hay fotos/%s.json" % a.foto)
    H = leer(os.path.join(trabajo, "historia.json")) if os.path.exists(os.path.join(trabajo, "historia.json")) else None
    for ruta in rutas:
        rec = leer(ruta)
        img = os.path.join(trabajo, rec.get("archivo") or "")
        if a.rehacer or "focos" not in rec:
            rec["focos"] = focos_de(img, rec.get("retrato_de"))
        fs = rec["focos"]
        if a.foco:
            x, y, w, h = (float(v) for v in a.foco.split(","))
            fs.append({"x": x, "y": y, "w": w, "h": h, "que": a.que or "objeto"})
        if a.cara:
            if not 1 <= a.cara <= len(fs):
                return falla("%s tiene %d cara(s)" % (rec["id"], len(fs)))
            if a.quitar:
                fs.pop(a.cara - 1)
            elif a.persona:
                fs[a.cara - 1]["persona"] = a.persona.strip()
                if a.evidencia:
                    fs[a.cara - 1]["evidencia"] = a.evidencia.strip()
        escribir(ruta, rec)
        if H and rec["id"] in (H.get("fotos") or {}):
            H["fotos"][rec["id"]]["focos"] = fs
        print("foto %s · %s" % (rec["id"], (rec.get("descripcion") or "")[:70]))
        imprimir_focos(rec)
    if H:
        escribir(os.path.join(trabajo, "historia.json"), H)
    return 0


def sha1_de(ruta):
    return hashlib.sha1(open(ruta, "rb").read()).hexdigest()


def foto_repetida(trabajo, rec):
    """La foto ya bajada (otro id en fotos/*.json) con la misma imagen (sha1) o la misma url, o None."""
    for ruta in sorted(glob.glob(os.path.join(trabajo, "fotos", "*.json"))):
        otra = leer(ruta)
        if otra.get("id") != rec["id"] and ((otra.get("sha1") and otra["sha1"] == rec["sha1"]) or
                                           (otra.get("url") and otra["url"] == rec["url"])):
            return otra
    return None


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
                          % (etiqueta, f.get("medio") or FW.dominio(f.get("url")), CITA_MIN))
            continue
        clase, grupo = clasificar(f.get("url"), propios, f.get("archivo"))
        if clase is None:
            avisos.append("%s: %s no cuenta para confirmar (no es oficial, medio de la lista, academia, archivo ni la "
                          "empresa del encuadre)" % (etiqueta, FW.dominio(f.get("url"))))
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
        # m028: un hecho compuesto lleva una cita por cláusula: avisa si una cláusula no tiene ninguna palabra en las citas
        raices_citas = raices_de(citas)
        clausulas = [x for x in re.split(r";|\s+y\s+(?=[a-záéíóúñ]+\s)", h.get("texto") or "") if x.strip()]
        if len(clausulas) > 1:
            for cl in clausulas:
                r = raices_de(cl)
                if len(r) >= 2 and not r & raices_citas:
                    avisos.append("H2 %s: la cláusula «%s» no tiene respaldo en ninguna cita (un hecho compuesto lleva una cita "
                                  "por cláusula; adjunta la fuente o pártelo)" % (hid, cl.strip()[:70]))
        de_anio = [f for _, _, f in validas if anio and (anio in plano(f.get("cita")) or str(f.get("fecha") or "").startswith(anio))]
        if anio and h.get("precision") != "aprox" and not de_anio:
            fallas.append("H2 %s: el año %s no está en ninguna cita (ni es el año de publicación de la fuente): cita el "
                          "fragmento que lo dice o pon precision aprox" % (hid, anio))
        for tok, val, _ in numeros_de(h.get("texto")):
            if VM.sueltos_prensa(tok, [(round(float(m.group().replace(",", "")), 6), None) for m in RE_NUMERO.finditer(citas)]):
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
        if VM.sueltos_prensa(c.get("texto") or "", [(round(float(c["valor"]), 6), VM.factor_unidad(c.get("unidad"))), (round(float(c["valor"]), 6), None)]):
            fallas.append("H2 %s: «%s» no es su valor %s" % (cid, c.get("texto"), c["valor"]))
        elif VM.sueltos_prensa(c.get("texto") or "", nums):
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


ILUSTRACION = re.compile(r"\b(representaci[oó]n|ilustraci[oó]n|render(izado)?|infograf[ií]a|recreaci[oó]n|modelo 3d|"
                         r"illustration|rendering|artist'?s impression)\b", re.I)


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
    if ILUSTRACION.search(rec.get("descripcion") or "") and not rec.get("referencia"):
        f.append("H7 %s: «%s» es una ilustración o un render, no una foto del hecho: busca una foto o márcala de referencia (m024)"
                 % (fid, (rec.get("descripcion") or "")[:60]))
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
            d = (rec.get("descripcion") or "").strip()
            if d and VD._plano(d) != VD._plano(fotos[prev].get("descripcion") or ""):
                fotos[prev].setdefault("descripciones_alias", {})[rec["id"]] = d
                print("AVISO %s y %s describen distinto la misma imagen («%s» / «%s»): en el QA de fotos, mira cuál "
                      "dice lo que muestra" % (prev, rec["id"], (fotos[prev].get("descripcion") or "")[:50], d[:50]))
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
    # H4n/H34: los nombres vetados se calculan con TODO lo publicable, antes de que /serie guarde lo posterior a la parte
    # (un nombre de un hecho reservado no está descartado: solo se cuenta después)
    H["vetados"] = nombres_vetados(H)
    # /serie: una parte solo ve lo que pasó hasta el fin de su periodo (lo posterior lo revelan las partes siguientes)
    ser_st = VD.serie_de(st)
    hasta = str((ser_st.get("periodo") or {}).get("hasta") or "")
    reparto, reservar = set(ser_st.get("hechos") or []), set(ser_st.get("reservar") or [])
    if hasta:
        def despues(x):
            # modo caso: lo repartido a esta parte entra aunque se haya revelado después (el mecanismo de la red se
            # supo en el juicio); lo repartido a una parte siguiente no, aunque sea anterior (no se adelanta)
            if x.get("id") in reparto:
                return False
            if x.get("id") in reservar:
                return True
            fe = str(x.get("fecha") or x.get("cuando") or x.get("anio") or "")
            return bool(re.match(r"\d{4}", fe)) and fe[:len(hasta)] > hasta
        H["reservados"] = [x["id"] for k in ("hechos", "cifras", "citas") for x in H[k] if despues(x)]
        for k in ("hechos", "cifras", "citas"):
            H[k] = [x for x in H[k] if not despues(x)]
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
    cambia = False
    if paleta != st["paleta"]:
        st["paleta"] = paleta
        st["musica"] = VD.elegir_musica(paleta, st.get("musica_forzada"))["id"]
        cambia = True
    # la música va por el tema del encuadre (musica_tema), no por el color
    pt = None if st.get("musica_forzada") or not enc.get("musica_tema") else VD.elegir_musica_tema(enc["musica_tema"], st.get("slug"))
    if pt and pt["id"] != st.get("musica") and st.get("musica_tema") != enc["musica_tema"]:
        st["musica"], st["musica_tema"] = pt["id"], enc["musica_tema"]
        cambia = True
    if cambia:
        escribir(os.path.join(trabajo, "video.json"), st)
    return H


def cmd_premisas(a):
    """H34 sola: consolida (rehace historia.json con el encuadre de ahora) y lista las premisas caídas."""
    trabajo = os.path.abspath(a.trabajo)
    H = consolidar(trabajo)
    caidas = premisas_caidas(H, encuadre(trabajo))
    for c in caidas:
        print("FALLA H34 %s: «%s» nombra «%s», que la verificación descartó (%s)" % (c["donde"], c["texto"], c["nombre"], c["motivo"]))
    vet = nombres_vetados(H)
    print("nombres vetados (H4n): %s" % (", ".join("«%s»" % n for n in sorted(vet)) or "ninguno"))
    if caidas:
        return falla("H34 %d textos del encuadre nombran algo descartado: quita el nombre (o cámbialo por lo verificado) y repite" % len(caidas))
    print("H34 ok: el encuadre no da por hecho nada descartado")
    return 0


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
    # m028: un hecho publicable que se parece a uno descartado en OTRO eje: cruzar las fuentes antes de usarlo
    for h in H["hechos"]:
        rh = raices_de(h.get("texto"))
        for d in H["descartados"]:
            rd = raices_de(d.get("texto"))
            if d.get("eje") != h.get("eje") and len(rh) >= 4 and len(rh & rd) >= 0.6 * min(len(rh), len(rd)):
                print("AVISO %s se parece a un descartado del eje %s («%s»: %s): cruza las fuentes antes de usarlo"
                      % (h["id"], d.get("eje"), (d.get("texto") or "")[:60], (d.get("motivo") or "")[:60]))
                break
    for x, y in H["conflictos"]:
        print("AVISO %s y %s parecen el mismo hecho con años distintos: deja uno o márcalo en_disputa" % (x, y))
    st = VD.estado(trabajo)
    print("→ %s · base %s · paleta %s · música %s" % (VD.rel(os.path.join(trabajo, "historia.json")), st["hilo"], st["paleta"], st["musica"]))
    if len(H["hechos"]) < HECHOS_MIN:
        return falla("H1 solo %d hechos publicables (van ≥ %d para contar una historia de 2–3 min)" % (len(H["hechos"]), HECHOS_MIN))
    prot = protagonistas(trabajo)
    caidas = premisas_caidas(H, encuadre(trabajo))
    if caidas:
        for c in caidas:
            print("FALLA H34 %s: «%s» nombra «%s», que la verificación descartó (%s)" % (c["donde"], c["texto"], c["nombre"], c["motivo"]))
        return falla("H34 el encuadre da por hecho lo que la verificación tumbó: el editor lo re-encuadra (Workflow historia, paso "
                     "Premisas, o desde: encuadre): quita el nombre de la espina, los hilos, los actos, los personajes, las revelaciones y las fotos clave (la pregunta puede quedar sin él: «¿de dónde sale el nombre?»); python3 scripts/historia.py premisas %s --check"
                     % VD.rel(trabajo))
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
    aplicar_formato(trabajo)
    TRABAJO_ACTUAL, H_ACTUAL = trabajo, historia_de(trabajo)
    if ORIGINALES:
        return
    ORIGINALES.update(visual=VD.visual_del_gancho, reglas=VD.reglas_gancho, estructura=VD.validar_estructura, colores=VD.colores)
    VD.NARRACION_VIDEO = False   # la narración de /historia la revisa revisar_narracion (H15–H19), no V17–V18
    VD.TIPOS = VD.TIPOS + tuple(t for t in TIPOS_PROPIOS if t not in VD.TIPOS)
    VD.FAMILIAS = FAMILIAS   # las familias libres del gate G (con la rotación R9) son las de /historia, no las de /video
    VD.CARACTERES.update(CARACTERES)
    VD.CARACTERES.update(CARACTERES_VIDEO_EN_HISTORIA)
    VD.SIN_HUECO = VD.SIN_HUECO + TIPOS_PROPIOS
    VD.POST_CONSTRUCTORES.append(post_historia)
    VD.ICONO_TIPOS = VD.ICONO_TIPOS + ("foto",)   # la foto sin imagen va con su icono (o el mapa)
    VD.visual_del_gancho = visual_del_gancho
    VD.reglas_gancho = reglas_gancho
    VD.validar_estructura = estructura
    VD.colores = colores_con_realce
    VD.CONSTRUCTORES.update(gancho=t_gancho, foto=t_foto, cita=t_cita, capitulo=t_capitulo, red=t_red, vias=t_vias, lupa=t_lupa, deptos=t_deptos, pagina=t_pagina, cortina=t_cortina, archivo=t_archivo, bandos=t_bandos)
    VD.TRANSICION_DE.update(foto="tarjeta", cita="texto", capitulo="completa", red="completa", vias="completa", lupa="tarjeta", deptos="completa", pagina="texto", cortina="tarjeta", archivo="tarjeta", bandos="completa")


def colores_con_realce(paleta):
    c = ORIGINALES["colores"](paleta)
    c["realce"] = c["acento"]   # Noche: el acento del tema ya se lee sobre la foto oscurecida (≥ 5.2:1 sobre el fondo)
    return c


def con_alias(fotos):
    """{id: foto} con cada alias de una foto fundida (la misma imagen bajada por otro eje) apuntando a su registro: un
    guion que usa el id de un alias no falla como «no verificada»."""
    todo = dict(fotos or {})
    for rec in (fotos or {}).values():
        for al in rec.get("alias") or []:
            todo.setdefault(al, rec)
    return todo


def fotos_h():
    return con_alias((H_ACTUAL or {}).get("fotos"))


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
        f.append("R9 la familia «%s» ya abrió una de las últimas %d piezas (%s): usa otra" % (fam, ROTACION_FAMILIAS, ", ".join(rec["familias"])))
    f += VD.reglas_r14(pant, lin, texto, voz_p)   # R14 sujeto reconocible: ni «430» ni «¿Sabías que…?» en la pantalla
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


acto_de = VD.acto_de   # el gancho es del acto 1


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
    def rompe(e):   # un giro o un rótulo abren una secuencia
        return e.get("giro") or rotulo_de(e)
    return VD.secuencias_por_defecto(g, rompe=rompe)


def estructura(g, st, dur, tarjetas):
    """V1/V9 de /video sin lo que historia no hereda + H8 (actos, rótulos, variedad, giro), H20 (secuencias), las
    escenas propias y, en una parte de /serie, SE4–SE9 (scripts/serie.py)."""
    f = estructura_historia(g, st, dur, tarjetas) + revisar_tomas(g)
    if TRABAJO_ACTUAL:
        f += revisar_personas(g, encuadre(TRABAJO_ACTUAL), fotos_h())
        f += revisar_red(g, H_ACTUAL or {})
    val_, an_ = respaldo_actual(), (anios_respaldados(H_ACTUAL) if H_ACTUAL else None)
    f += revisar_vias(g, val_, an_)
    f += revisar_lupa(g, val_, an_)
    f += revisar_deptos(g, val_, an_)
    f += revisar_pagina(g, val_, an_)
    f += revisar_cortina(g, val_, an_)
    f += revisar_archivo(g, val_, an_)
    f += revisar_bandos(g, val_, an_)
    if VD.serie_de(st).get("parte"):
        import serie as SR   # noqa: E402  (serie importa historia: aquí, no arriba)
        f += SR.revisar_parte(g, st, TRABAJO_ACTUAL)
    return f


def revisar_tomas(g):
    """TM0: las tomas de video (clips de las fuentes) se retiraron el 2026-11-06; un guion que trae una falla aquí."""
    return ["TM0 escena %d: las tomas de video ya no van en /historia ni /serie: una cita (la frase literal, leída por "
            "la voz) o una foto o documento con la misma voz" % i
            for i, e in enumerate(g.get("escenas") or [], 1) if e.get("tipo") == "toma"]


# ---------- H34 y H4n (2026-11-16, Pinulito): lo que la verificación descartó no llega al video ----------
# El editor encuadró «Santa Catarina Pinula» como origen del nombre; los tres verificadores lo descartaron (la única fuente
# decía San José Pinula y no contaba), pero la premisa siguió en la espina, un hilo, un personaje y una revelación, y la voz
# la insinuó («suena a Santa Catarina Pinula»). Los nombres propios de lo descartado que ningún hecho,
# cita o cifra publicable respalda quedan vetados: en el encuadre (H34, al consolidar) y en el guion (H4n).
_MAY = r"[A-ZÁÉÍÓÚÑÜ][A-Za-zÁÉÍÓÚÑÜáéíóúñü'’\.-]*"
RE_NOMBRE_PROPIO = re.compile(r"%s(?:\s+(?:(?:de|del|la|las|los|y)\s+)*%s)+" % (_MAY, _MAY))
ARTICULOS_INICIALES = ("el", "la", "los", "las", "un", "una", "que", "en", "su", "sus", "segun")


def nombres_propios(texto):
    """Los nombres propios de dos o más palabras de un texto («Santa Catarina Pinula», «Mario Roberto Méndez»), en plano y
    sin el artículo o la palabra de inicio de oración que los antecede («El Pollo Pinulito» → «pollo pinulito»)."""
    out = []
    for m in RE_NOMBRE_PROPIO.finditer(str(texto or "")):
        ws = VD._plano(m.group()).split()
        while ws and ws[0] in ARTICULOS_INICIALES:
            ws = ws[1:]
        while ws and ws[-1] in ("de", "del", "la", "las", "los", "y"):
            ws = ws[:-1]
        if len(ws) >= 2:
            out.append(" ".join(ws))
    return out


def _contiene(plano_texto, nombre):
    return bool(re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(nombre), plano_texto))


def corpus_publicable(H):
    """Todo lo que la verificación deja decir, en plano: hechos, cifras y citas publicables con sus fuentes, autores,
    lugares y casos, más el protagonista."""
    partes = list(H.get("protagonista") or [])
    for k in ("hechos", "cifras", "citas"):
        for x in H.get(k) or []:
            partes += [str(x.get(c) or "") for c in ("texto", "concepto", "autor", "cargo", "lugar", "actores", "nota")]
            partes += [str(f.get(c) or "") for f in x.get("fuentes") or [] for c in ("medio", "titulo")]
    partes += [str(c.get(k) or "") for c in H.get("casos") or [] for k in ("persona", "estado_actual")]
    return VD._plano(" ".join(partes))


def nombres_vetados(H):
    """{nombre en plano: motivo}: los nombres propios de los descartados por la verificación que ningún hecho, cifra o
    cita publicable nombra. Si consolidar ya los guardó (H["vetados"], con lo reservado de /serie incluido), esos."""
    if isinstance(H.get("vetados"), dict):
        return H["vetados"]
    corpus = corpus_publicable(H)
    vet = {}
    fuentes = [(d.get("texto") or d.get("hecho") or "", "descartado del eje %s: %s" % (d.get("eje") or "?", (d.get("motivo") or "sin motivo")[:90]))
               for d in H.get("descartados") or []]
    # no_afirma NO: veta una afirmación sobre alguien («que Pérez Molina…»), no su nombre
    for texto, motivo in fuentes:
        for n in nombres_propios(texto):
            if not _contiene(corpus, n):
                vet.setdefault(n, motivo)
    return vet


def textos_encuadre(enc):
    """[(dónde, texto)] de lo que el encuadre le pasa como verdad al gancho, al guionista y al crítico."""
    out = [("revelaciones[%d]" % k, r) for k, r in enumerate(enc.get("revelaciones") or [], 1)]
    out += [("espina.%s" % k, (v or {}).get("frase")) for k, v in (enc.get("espina") or {}).items() if isinstance(v, dict)]
    out += [("hilo %s" % (h.get("id") or k), h.get("pregunta")) for k, h in enumerate(enc.get("hilos") or [], 1)]
    for a in enc.get("actos") or []:
        out += [("acto %s.%s" % (a.get("n"), c), a.get(c)) for c in ("titulo", "que_cuenta", "termina_en")]
    for p in enc.get("personajes") or []:
        out += [("personaje «%s»" % p.get("nombre"), "%s %s" % (p.get("nombre") or "", p.get("presentacion") or ""))]
    out += [("pregunta", enc.get("pregunta"))]
    out += [("fotos_clave[%d]" % k, f if isinstance(f, str) else json.dumps(f, ensure_ascii=False)) for k, f in enumerate(enc.get("fotos_clave") or [], 1)]
    return [(d, str(t)) for d, t in out if t]


def premisas_caidas(H, enc):
    """H34: [{donde, texto, nombre, motivo}] por cada texto del encuadre que nombra algo que la verificación descartó."""
    vet = nombres_vetados(H)
    out = []
    for donde, texto in textos_encuadre(enc):
        p = VD._plano(texto)
        for n, motivo in vet.items():
            if _contiene(p, n):
                out.append({"donde": donde, "texto": texto[:160], "nombre": n, "motivo": motivo})
    return out


def lineas_descartados(H):
    """«## Descartado por la verificación»: para el guionista y el crítico (H-C5), con los nombres que H4n veta."""
    ds = H.get("descartados") or []
    if not ds:
        return []
    vet = nombres_vetados(H)
    return ["", "## Descartado por la verificación (NO se dice, ni se insinúa: «suena a», «recuerda a», «se diría que» cuentan como afirmarlo)"] + \
        ["- %s — %s [%s]" % ((d.get("texto") or d.get("hecho") or "")[:160], (d.get("motivo") or "")[:120], d.get("eje") or "?") for d in ds] + \
        (["- Nombres vetados en voz, pantalla, fotos y lugares (H4n): %s" % ", ".join("«%s»" % n for n in sorted(vet))] if vet else [])


def revisar_vetados(g, H, fotos):
    """H4n: ninguna escena nombra (en voz, pantalla, línea, titular, rótulo o cierre) ni muestra (foto cuyo lugar o
    descripción lo nombra) algo que la verificación descartó."""
    vet = nombres_vetados(H)
    if not vet:
        return []
    f = []
    escenas = list(enumerate(g.get("escenas") or [], 1)) + [("cierre", g.get("cierre") or {})]
    for i, e in escenas:
        rot = e.get("rotulo") if isinstance(e.get("rotulo"), dict) else {}
        ids = [x for x in (e.get("foto"), (e.get("visual_datos") or {}).get("foto"), e.get("retrato")) if x]
        # el pie de una foto de Commons u oficial describe la imagen (no la historia): su lugar en el chip no cuenta
        pie_libre = VD._plano(" ".join("%s %s" % ((fotos.get(x) or {}).get("lugar") or "", (fotos.get(x) or {}).get("descripcion") or "")
                                       for x in ids if (fotos.get(x) or {}).get("origen") in ("commons", "oficial")))
        dichos = [e.get(k) for k in ("texto", "pantalla", "linea", "titular", "golpe")] + [rot.get("titulo")] + list(e.get("resumen") or [])
        chips = [x for x in (e.get("lugar"), e.get("fecha"), rot.get("lugar")) if x]
        p = VD._plano(" ".join(str(x) for x in dichos if x))
        pc = VD._plano(" ".join(str(x) for x in chips))
        for n, motivo in vet.items():
            if _contiene(p, n) or (_contiene(pc, n) and not _contiene(pie_libre, n)):
                f.append("H4n escena %s: nombra «%s», que la verificación descartó (%s). Insinuarlo («suena a…») también "
                         "cuenta: quítalo de la voz y la pantalla" % (i, n, motivo))
        for fid in ids:
            fo = fotos.get(fid) or {}
            pf = VD._plano("%s %s" % (fo.get("lugar") or "", fo.get("descripcion") or ""))
            for n, motivo in vet.items():
                if _contiene(pf, n):
                    print("AVISO H4n escena %s: la foto %s muestra «%s», que la verificación descartó (%s): en el QA de fotos, "
                          "mira si la imagen insinúa lo que la voz no puede decir" % (i, fid, n, motivo))
    return f


def estructura_historia(g, st, dur, tarjetas):
    f = [x for x in ORIGINALES["estructura"](g, st, dur, tarjetas) if not V9_de_video(x)]
    escenas = g.get("escenas") or []
    H = H_ACTUAL or {}
    hechos = {h["id"]: h for h in H.get("hechos") or []}
    citas = {q["id"]: q for q in H.get("citas") or []}
    fotos = con_alias(H.get("fotos"))
    tipos = [e.get("tipo") for e in escenas]
    vetados = {}
    for d in H.get("descartados") or []:
        for m in RE_NUMERO.finditer(" ".join(str(d.get(k) or "") for k in ("texto", "hecho", "valor"))):
            vetados.setdefault(m.group().replace(",", ""), "descarte del eje %s («%s»)" % (d.get("eje") or "?", str(d.get("texto") or "")[:50]))
    for x in H.get("no_afirma") or []:
        for m in RE_NUMERO.finditer(str(x)):
            vetados.setdefault(m.group().replace(",", ""), "no_afirma «%s»" % str(x)[:60])
    for i, e in enumerate(escenas, 1):
        texto_e = " ".join(filter(None, (e.get("texto"), (citas.get(e.get("cita")) or {}).get("texto"))))
        for m in RE_NUMERO.finditer(texto_e):
            n = m.group().replace(",", "")
            # solo cantidades ≥ 100 y no años: un 2 o un 13 coinciden con cualquier cosa
            if n in vetados and float(n) >= 100 and not re.fullmatch(r"(1[89]|20)\d\d", n):
                print("AVISO H4 escena %d: «%s» coincide con un %s: si la atribución no basta, quítalo (m041)" % (i, m.group(), vetados[n]))
    f += revisar_vetados(g, H, fotos)
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
    f += variedad_de_imagen(escenas, encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {})   # H26
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        f += pantalla_contra_voz(i, e, hechos)   # H24 (m124)
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
                fo = fotos[fid]
                f += foto_de_proceso(i, e, fo)   # H7c (m122)
                av = foto_de_otras_personas(i, e, fo, encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {})   # m137
                if av:
                    print("AVISO " + av)
                if (fo.get("referencia") or re.search(r"referencia", e.get("fecha") or "", re.I)) and (e.get("lugar") or "").strip() \
                        and VD._plano(e["lugar"]) != VD._plano(fo.get("lugar") or "") \
                        and VD._plano(e["lugar"]) not in VD._plano(fo.get("descripcion") or ""):
                    print("AVISO H7 escena %d: foto de referencia «%s» con «%s» en el chip, pero la foto es de %s: el chip "
                          "muestra el lugar de la foto (o ninguno), no el del hecho" % (i, fid, e["lugar"], fo.get("lugar") or "un lugar sin anotar"))
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
            firma = VD._plano(q.get("autor") or "").split()
            for p in H.get("personajes") or []:
                for nombre in [p.get("nombre")] + list(p.get("alias") or []) if isinstance(p, dict) else []:
                    completo = VD._plano(nombre or "").split()
                    if firma and len(completo) > len(firma) and set(firma) <= set(completo) and firma != completo:
                        print("AVISO H6 escena %d: la cita firma «%s» y el personaje es «%s»: ¿falta un apellido? (m034)"
                              % (i, q.get("autor"), nombre))
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
    """H11: cada «esos 40 niños», «ese alimento», «esa línea» tiene su antecedente en lo que ya se oyó o se leyó antes
    (video.hilo_referencias, compartida con /video)."""
    return VD.hilo_referencias(escenas, cod="H11")


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
        for fid in dict.fromkeys([e.get("foto"), e.get("retrato"), (e.get("visual_datos") or {}).get("foto")] + fotos_de_archivo(e)):
            if fid:
                usos.setdefault(clave.get(fid, fid), []).append((i, fid))
    f = ["H7 la misma foto (%s) sale en %d escenas (%s): van ≤ %d; usa otra, un mapa, un icono o un gráfico"
         % (u[0][1], len(u), ", ".join(str(i) for i, _ in u), FOTO_USOS_MAX) for u in usos.values() if len(u) > FOTO_USOS_MAX]
    # H7b (decisión del usuario, 2026-11-09): dos escenas SEGUIDAS nunca muestran la misma imagen (el gancho y la escena 2
    # incluidos): la imagen nueva es lo que sostiene la atención
    for u in ([] if en_mesa() else usos.values()):   # en la mesa de archivo la foto de la escena es solo la semilla: MV3 vigila el plano
        for (a, fa), (b, _) in zip(u, u[1:]):
            if b == a + 1:
                f.append("H7b las escenas %d y %d seguidas muestran la misma foto (%s): cada escena, una imagen distinta de la anterior"
                         % (a, b, fa))
    return f


# H7c (m122, 2026-11-09): una foto que muestra a alguien detenido, esposado o en audiencia insinúa culpa por imagen si
# ilustra otra cosa. Solo va en la escena cuya voz nombra a esa persona (`proceso` en fotos/<id>.json, historia.py foto
# --proceso "<nombre>"); una foto así sin marcar (lo dice su descripción) es un aviso para marcarla.
RE_FOTO_PROCESO = re.compile(r"\b(esposad[oa]s?|detenid[oa]s?|capturad[oa]s?|arrestad[oa]s?|audiencias?|tribunal(?:es)?|"
                             r"juzgado|banquillo|reos?|reclus[oa]s?|celdas?|prisi[oó]n|c[aá]rcel|sindicad[oa]s?|procesad[oa]s?)\b", re.I)


def foto_de_proceso(i, e, fo):
    quien = (fo.get("proceso") or "").strip()
    voz = VD._plano(e.get("texto") or "").split()
    if quien:
        apellidos = [w for w in VD._plano(quien).split() if len(w) > 3]
        if not any(w in voz for w in apellidos):
            return ["H7c escena %d: la foto %s muestra a %s en un proceso (detenido o en audiencia): solo va en la escena cuya "
                    "voz lo nombra y cuenta ese proceso; aquí ilustra otra cosa (usa una foto del lugar o la institución)" % (i, fo.get("id"), quien)]
    elif RE_FOTO_PROCESO.search(fo.get("descripcion") or ""):
        print("AVISO H7c escena %d: la foto %s parece mostrar a alguien detenido o en audiencia («%s»): si es así, márcala con "
              "historia.py foto … --proceso \"<nombre>\" y úsala solo donde la voz lo nombra" % (i, fo.get("id"), (fo.get("descripcion") or "")[:60]))
    return []


# H24 (m124, 2026-11-09): la pantalla no dice lo que la voz ya no dice. Una cifra en pantalla (cifra.texto; en el titular o
# el golpe, la que lleva moneda, % o «mil/millones») que la voz de esa escena no dice falla: queda de una versión anterior.
# Y un alegato, una estimación o una opinión con número en pantalla lleva su atribución también en pantalla («según…»).
RE_NUM_PANTALLA = re.compile(r"(?:US\$|\$|Q\.?\s?)?\d[\d,.]*\s*(?:%|por ciento|mil(?:lones?)?\b|millones\b)?", re.I)
RE_ATRIBUYE = re.compile(r"\b(seg[uú]n|dice|dijo|cuenta|acusa|afirma|denuncia|sostiene|calcula|estima)\b", re.I)


def _digitos(x):
    return re.sub(r"\D", "", x)


# H26 (2026-11-10): con la cámara quieta, una foto fija de 15 s es un tramo sin nada nuevo (V21 lo marcaba tarde, ya
# grabado). La imagen cambia con el tema: una escena `foto` larga se reparte en dos, cada una con su imagen. Y las
# composiciones que ya existen (pantalla dividida, mini-mapa, subrayado, documento, organigrama) se usan.
FOTO_MAX_S = 12.0
FOTOS_POR_VARIANTE = 4      # aviso: por cada 4 fotos, al menos una composición distinta
RED_DESDE_PERSONAJES = 5    # aviso: con tantas personas en el encuadre, la historia pide un organigrama o un tablero


def en_mesa():
    """¿El TRABAJO que se revisa lo dibuja la mesa de archivo? Ahí la escena es unidad de voz y de respaldo, no de dibujo:
    los gates del dibujo viejo (H7b, la foto fija y las composiciones de H26) los relevan los MV del plano."""
    try:
        return bool(TRABAJO_ACTUAL) and VD.es_mesa(VD.estado(TRABAJO_ACTUAL))
    except (OSError, ValueError):
        return False


def variedad_de_imagen(escenas, enc):
    f, av = [], []
    fotos = [(i, e) for i, e in enumerate(escenas, 1) if e.get("tipo") == "foto"]
    mesa = en_mesa()
    for i, e in ([] if mesa else fotos):
        s_ = VD.segundos_voz(e.get("texto"))
        if s_ > FOTO_MAX_S and not (e.get("dividida") or e.get("marcas") or e.get("subrayado")):
            f.append("H26 escena %d: una foto fija de %.0f s estimados (máximo %.0f): repártela en dos escenas, cada una con la "
                     "imagen de lo que cuenta (otra foto, un documento, una cita, una tarjeta)" % (i, s_, FOTO_MAX_S))
    for i, e in enumerate(escenas, 1):   # el mapa con ruta: 2–4 departamentos que existen
        if e.get("ruta") is not None:
            r = e["ruta"] if isinstance(e["ruta"], list) else []
            if not 2 <= len(r) <= 4 or any(not VD.depto_id(x) for x in r) or len({VD.depto_id(x) for x in r}) != len(r):
                f.append("H26 escena %d: `ruta` son 2–4 departamentos distintos, en el orden del recorrido (p. ej. [\"Escuintla\", "
                         "\"Guatemala\"])" % i)
            elif e.get("tipo") != "foto":
                f.append("H26 escena %d: `ruta` va en una escena foto (es el localizador con su trazo)" % i)
    variantes = sum(1 for e in escenas if e.get("dividida") or e.get("minimapa") or e.get("ruta") or e.get("depto") or e.get("marcas") or e.get("subrayado")
                    or e.get("documento") or e.get("tipo") in ("red", "tablero", "explica", "tarjeta") + ESCENAS_ARCHIVO)
    if not mesa and len(fotos) >= FOTOS_POR_VARIANTE and variantes * FOTOS_POR_VARIANTE < len(fotos):
        av.append("H26 %d escenas de foto con titular y solo %d composiciones distintas (pantalla dividida, mini-mapa, "
                  "subrayado, documento, tarjeta, animación): van ≥ 1 por cada %d fotos" % (len(fotos), variantes, FOTOS_POR_VARIANTE))
    pers = [p for p in enc.get("personajes") or [] if isinstance(p, dict) and es_persona(p)]
    if len(pers) >= RED_DESDE_PERSONAJES and not any(e.get("tipo") in ("red", "tablero") for e in escenas) and not enc.get("serie"):
        av.append("H26 %d personas en el encuadre y ninguna escena `red`: quien no las conoce se pierde; un organigrama con "
                  "las relaciones verificadas (H23)" % len(pers))
    st = VD.estado(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    if str(st.get("fecha") or VD.P6_DESDE) < VD.P6_DESDE:
        av, f = av + f, []
    for x in av:
        print("AVISO", x)
    return f


def pantalla_contra_voz(i, e, hechos):
    voz = e.get("texto") or ""
    dichos = {_digitos(m.group()) for m in re.finditer(r"\d[\d,.]*", voz)}
    fallas, en_pantalla = [], []
    c = e.get("cifra") if isinstance(e.get("cifra"), dict) else {}
    for m in re.finditer(r"\d[\d,.]*", c.get("texto") or ""):
        en_pantalla.append((m.group(), "la cifra"))
    for campo in ("titular", "golpe"):
        for m in RE_NUM_PANTALLA.finditer(e.get(campo) or ""):
            t = m.group().strip()
            if re.search(r"%|por ciento|mil|\$|Q", t, re.I):
                en_pantalla.append((re.search(r"\d[\d,.]*", t).group(), "el %s" % campo))
    for num, donde in en_pantalla:
        d = _digitos(num)
        if not d or re.fullmatch(r"(1[5-9]|20)\d\d", d) or d in dichos:
            continue
        fallas.append("H24 escena %d: %s dice «%s» y la voz de la escena no lo dice: quítalo de la pantalla o dilo" % (i, donde, num))
    if en_pantalla:
        tipos_h = {(hechos.get(h) or {}).get("tipo_hecho") for h in e.get("hechos") or []}
        if tipos_h & {"alegato", "estimacion", "opinion"}:
            atrib = " ".join(str(x or "") for x in (e.get("titular"), e.get("golpe"), c.get("etiqueta")))
            if not RE_ATRIBUYE.search(atrib):
                msg = ("H24 escena %d: la cifra en pantalla sale de un alegato, una estimación o una opinión: atribúyela también "
                       "en pantalla («según <quién>» en la etiqueta o el titular)" % i)
                if (e.get("fuente") or "").strip():   # la fuente en pantalla la ata a alguien: aviso, no falla
                    print("AVISO " + msg + "; ahora solo la sostiene la fuente «%s»" % e["fuente"])
                else:
                    fallas.append(msg)
    return fallas


RE_FOTO_CON_NOMBRES = re.compile(r"l[áa]pida|tumba|epitafio|nicho|placa (?:con|de)|memorial con|con (?:dos|tres|cuatro|\d+) nombres|"
                                 r"nombres de|retrato de", re.I)
RE_NOMBRE_PROPIO = re.compile(r"(?<![.!?¿¡]\s)(?<!^)\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})")


def foto_de_otras_personas(i, e, foto, enc):
    """m137 (aviso): la escena nombra a una persona y su foto muestra los nombres o el retrato de OTRAS (una lápida con
    dos nombres sobre la escena de Telma Pérez Alvarado). → texto del aviso o None."""
    texto = e.get("texto") or ""
    claves = [(p["nombre"], claves_personaje(p)) for p in enc.get("personajes") or []
              if isinstance(p, dict) and (p.get("nombre") or "").strip() and es_persona(p)]
    plano = VD._plano(texto)
    nombrados = [n for n, cl in claves if any(c and c in plano for c in cl)]
    nombrados += [m for m in RE_NOMBRE_PROPIO.findall(texto) if len(m.split()) >= 2 and m not in nombrados]
    if not nombrados:
        return None
    desc, ret = str(foto.get("descripcion") or ""), str(foto.get("retrato_de") or "")
    ajeno = ret and not any(VD._plano(ret) in VD._plano(n) or VD._plano(n) in VD._plano(ret) for n in nombrados)
    if not (ajeno or (RE_FOTO_CON_NOMBRES.search(desc) and not any(VD._plano(n) in VD._plano(desc) for n in nombrados))):
        return None
    return ("H7 escena %d: la voz nombra a %s y la foto «%s» muestra %s: el espectador lee esos nombres como los de la "
            "persona; usa una foto de referencia del lugar o de la época" % (i, ", ".join(nombrados[:2]), foto.get("id"),
                                                                         "el retrato de %s" % ret if ajeno else "«%s»" % desc[:70]))


def foto_de_archivo(foto):
    """m147: la foto es de archivo y su «fecha» es la de la nota que la republicó: la descripción dice «archivo» o
    «hemeroteca», o nombra un año anterior al de la foto (las ruinas de 1976 en una nota de 2026)."""
    desc = str(foto.get("descripcion") or "")
    if re.search(r"\barchivo\b|hemeroteca", desc, re.I):
        return True
    m = RE_ANIO.search(str(foto.get("fecha") or ""))
    return bool(m) and any(int(y) < int(m.group()) - 1 for y in RE_ANIO.findall(desc))


def fecha_contra_foto(i, chip, foto):
    """H7: el chip no le pone a la foto un año anterior a cuando se tomó (una foto de 2021 bajo «1978» parece de 1978):
    con una foto posterior, el chip dice su año («Foto de 2021»), «De referencia» o la época sin año."""
    m = RE_ANIO.search(str(foto.get("fecha") or ""))
    if not m or re.search(r"referencia|\bfoto\b", chip, re.I):
        return []
    previos = [y for y in RE_ANIO.findall(chip) if int(y) < int(m.group())]
    if previos and m.group() not in chip:
        if foto_de_archivo(foto):   # m147: la fecha es la de la nota que la republicó
            return ["H7 escena %d: el chip dice «%s» y la foto «%s» es de archivo publicada en %s: pon «De archivo» o la "
                    "época sin año" % (i, chip, foto.get("id"), m.group())]
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
        if cap and not e.get("resumen_serie"):   # SE14: el resumen de la serie repasa el pasado a propósito
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
        m = VETADAS.search(todo)
        if m and not (e.get("caso") and e["caso"] in casos_firmes):
            f.append("H3 escena %d: «%s» sin sentencia firme (presunción de inocencia: señalado, acusado, sindicado; con "
                     "sentencia firme, «caso»: <persona> de casos[] con sentencia_firme)" % (i, m.group()))
    cap = json.dumps(g.get("caption") or {}, ensure_ascii=False)
    for y in sorted(set(RE_ANIO.findall(cap)) - anios):
        f.append("H4 caption: el año %s no está en ningún hecho verificado" % y)
    if VETADAS.search(cap):
        f.append("H3 caption: «%s» sin sentencia firme" % VETADAS.search(cap).group())
    return f


# ---------- la narración (v3): el texto corrido que se escribe ANTES de repartirlo en escenas ----------
narracion_de, plano_voz = VD.narracion_de, VD.plano_voz   # compartidas con /video


def raices_de(texto):
    """Las raíces de 5 letras de las palabras con peso de un texto (como F3 del cierre y H14)."""
    return {w[:5] for w in VD._plano(texto).split() if len(w) >= 5 and w not in VD.STOP and w not in VD.GENERICAS and not w.isdigit()}


estimado_s = VD.estimado_guion_s


# H25 (2026-11-10, decisión del usuario): la tensión sube. La curiosidad es una escalera: se cierra una pregunta y queda
# otra abierta. Con lo que el guion ya declara (promesa, bisagra, giro, hilos que se pagan), cada tercio del video tiene
# al menos un peldaño, los hilos no se pagan todos de golpe y no pasan más de ESCALERA_HUECO_S sin ninguno.
ESCALERA_HUECO_S = 35.0


def escalera(g, enc, escenas):
    n = len(escenas)
    if n < 6:
        return []
    f, av = [], []
    pel = {}                                   # escena → qué peldaños tiene
    p, b = g.get("promesa") or {}, g.get("bisagra") or {}
    for k, en in (("promesa", p.get("en")), ("pago de la promesa", p.get("pago")), ("bisagra", b.get("en")), ("pago de la bisagra", b.get("pago"))):
        if isinstance(en, int) and 1 <= en <= n:
            pel.setdefault(en, []).append(k)
    pagos = {}
    for i, e in enumerate(escenas, 1):
        if e.get("giro"):
            pel.setdefault(i, []).append("giro")
        for hid in e.get("paga") or []:
            pel.setdefault(i, []).append("hilo " + hid)
            pagos[hid] = i
    tercios = [(1, n // 3), (n // 3 + 1, 2 * n // 3), (2 * n // 3 + 1, n)]
    for k, (a, z) in enumerate(tercios, 1):
        if not any(a <= i <= z for i in pel):
            f.append("H25 el tercio %d del video (escenas %d–%d) no abre ni paga nada (promesa, bisagra, giro o un hilo en "
                     "«paga»): la tensión sube por peldaños; mueve ahí el pago de un hilo o la bisagra" % (k, a, z))
    hilos = [h.get("id") for h in enc.get("hilos") or [] if isinstance(h, dict)]
    if len(pagos) >= 2 and len(set(pagos.values())) == 1:
        f.append("H25 todos los hilos se pagan en la escena %d: repártelos; al cerrar uno, que otro siga abierto"
                 % next(iter(pagos.values())))
    if len(hilos) >= 2 and pagos and min(pagos.values()) > 2 * n // 3 and not any(d.get("pasa_a") for d in g.get("hilos") or [] if isinstance(d, dict)):
        av.append("H25 ningún hilo se paga antes del último tercio: paga uno en el nudo (y que otro quede abierto)")
    # huecos: segundos estimados entre un peldaño y el siguiente
    t, ts = 0.0, {}
    for i, e in enumerate(escenas, 1):
        ts[i] = t
        t += VD.segundos_voz(e.get("texto"))
    marcas = sorted(ts[i] for i in pel)
    for a_, b_ in zip(marcas, marcas[1:]):
        if b_ - a_ > ESCALERA_HUECO_S:
            av.append("H25 %.0f s sin abrir ni pagar nada (entre los %.0f y los %.0f s): un peldaño en medio" % (b_ - a_, a_, b_))
    st = VD.estado(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    if str(st.get("fecha") or VD.P6_DESDE) < VD.P6_DESDE:   # un guion aprobado antes de la regla: solo aviso
        av, f = av + f, []
    for x in av:
        print("AVISO", x)
    return f


def revisar_narracion(g, H, enc):
    """H15 (la narración es la suma exacta de las voces), H16 (flujo), H17 (hilos), H18 (primera mención) y H19
    (presupuesto de «según»). Sin escenas (el guionista mide el texto antes de repartirlo: `narracion --check`), las
    unidades son los tres actos y H15 solo cuenta palabras. H15, H16 y H19 son las reglas de video.py (V17–V18 en
    /video) con los códigos y los topes de /historia."""
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    actos = [acto_de(e, i) for i, e in enumerate(escenas, 1)]
    narr = narracion_de(g)
    solo_narr = not escenas
    f = VD.revisar_reparto(g, cod="H15")
    if not narr or [a for a, _ in narr] != [1, 2, 3] or not all(t for _, t in narr):
        narr = []
    g_narr = dict(g, narracion=[{"acto": a, "texto": t} for a, t in narr])   # una narración mal formada no se mide
    if narr:
        total = sum(VD.palabras(t) for _, t in narr)
        if not PALABRAS_DURO[0] <= total <= PALABRAS_DURO[1]:
            f.append("H15 %d palabras de narración; van %d–%d (≈ %d s a 145 palabras por minuto)" % (total, *PALABRAS, OBJETIVO_S))
        elif not PALABRAS[0] <= total <= PALABRAS[1]:
            print("AVISO H15 %d palabras de narración: apunta a %d–%d (≈ %d s)" % (total, *PALABRAS, OBJETIVO_S))
    # m022: «esas 8 millones de dosis»: el determinante concuerda con «millones» (masculino), no con lo contado
    for _, t in narr:
        for m in re.finditer(r"\b(esas|estas|aquellas|las|unas|todas)\s+(\d[\d.,]*|[a-záéíóú]+)\s+millones\s+de\b", t, re.I):
            print("AVISO H16 «%s»: con «millones» va masculino («%s %s millones de»)" % (
                m.group(), {"esas": "esos", "estas": "estos", "aquellas": "aquellos", "las": "los", "unas": "unos",
                            "todas": "todos"}[m.group(1).lower()], m.group(2)))
    # H16 flujo: conectores por acto, aperturas con atribución, aperturas repetidas y cortes por minuto
    f += VD.revisar_hilo_voz(g_narr, cod="H16", conectores_min=CONECTORES_MIN_POR_ACTO)
    unidades = [VD.sin_pausas(e.get("texto") or "").strip() for e in escenas] + [VD.sin_pausas(cierre.get("texto") or "").strip()] \
        if not solo_narr else [t for _, t in narr]
    etiqueta = (lambda k: "escena %d" % (k + 1)) if not solo_narr else (lambda k: "acto %d" % (k + 1))  # noqa: E731
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
            elif d.get("pasa_a") is not None:   # /serie: el hilo sigue abierto y lo abre la parte siguiente
                ser = VD.serie_de(VD.estado(TRABAJO_ACTUAL)) if TRABAJO_ACTUAL else None
                if not ser or not ser.get("parte"):
                    f.append("H17 hilo %s: «pasa_a» es de una parte de /serie" % h["id"])
                elif d["pasa_a"] != ser["parte"] + 1 or ser["parte"] >= ser.get("de", 0):
                    f.append("H17 hilo %s: pasa_a = %s; solo pasa a la parte siguiente (%s) y la última los paga todos"
                             % (h["id"], d["pasa_a"], ser["parte"] + 1 if ser["parte"] < ser.get("de", 0) else "ninguna"))
            elif (d.get("sin_respuesta") or "").strip():
                raices = raices_de(d["sin_respuesta"])
                if raices and not any(re.search(r"\b" + re.escape(ra), narr3) for ra in raices):
                    f.append("H17 hilo %s: la narración del acto 3 (o el cierre) no dice que quedó sin respuesta («%s»)"
                             % (h["id"], d["sin_respuesta"][:60]))
            else:
                f.append("H17 hilo %s: «escena» (la que lo paga), «sin_respuesta» (la frase que lo declara) o, en /serie, «pasa_a»" % h["id"])
        ids = {h["id"] for h in hilos_enc}
        for i, e in enumerate(escenas, 1):
            for hid in e.get("paga") or []:
                if hid not in ids:
                    f.append("H17 escena %d: «paga» cita un hilo que no existe en el encuadre (%s)" % (i, hid))
    if not solo_narr:
        f += escalera(g, enc, escenas)
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
        if k == 0 and not solo_narr and len(voces_p) > 1:
            dicho += " " + voces_p[1]   # el gancho (elegido por el usuario, va literal) nombra; la escena 2 presenta
        if not any(re.search(r"\b" + re.escape(ra), dicho) for ra in raices):
            f.append("H18 %s: «%s» aparece por primera vez sin presentación («%s»): dilo en esa voz (o en la anterior) con una "
                     "aposición" % (etiqueta(k), p["nombre"], p.get("presentacion")))
    # H19 «según»: ≤ 4 por video, ≤ 2 por acto, nunca en dos escenas seguidas, nunca la misma fuente dos veces en voz
    f += VD.revisar_segun(g_narr, cod="H19", maximo=SEGUN_MAX_VIDEO, por_acto_max=SEGUN_MAX_ACTO)
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
            # H25: lo que está en juego en cada acto (qué se puede perder y a quién alcanza), y que no sea lo mismo
            if not enc.get("serie") and not (a.get("en_juego") or "").strip():
                f.append("H8 encuadre: acto %s sin «en_juego» (qué se puede perder ahí y a quién alcanza; sube de acto en acto)" % a.get("n"))
            tit = (a.get("titulo") or "").strip()
            if tit and (VD.palabras(tit) > CAP_TITULO_PALABRAS or len(tit) > CAP_TITULO_CARACTERES):
                f.append("H8 encuadre: acto %s: titulo de 1–%d palabras y ≤ %d caracteres (es el rótulo)" % (a.get("n"), CAP_TITULO_PALABRAS, CAP_TITULO_CARACTERES))
    ej = [VD._plano(a.get("en_juego") or "") for a in actos if isinstance(a, dict) and (a.get("en_juego") or "").strip()]
    if len(ej) != len(set(ej)):
        f.append("H8 encuadre: dos actos tienen el mismo «en_juego»: cada acto sube lo que está en juego")
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
        if not isinstance(h, dict) or not re.fullmatch(r"(?:p\d)?h\d+", str(h.get("id") or "")) or not (h.get("pregunta") or "").strip():
            f.append("H8 encuadre: cada hilo {id: h1, h2… (p1h1… en una parte de /serie), pregunta, eje}")
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


def revisar_paleta(enc, trabajo):
    """H8p (decisión del usuario, 2026-11-09): la paleta sale del TINTE del tema (el color de la marca o la empresa, el del
    partido o la institución, el material: café → cacao, maíz → maiz, lago → atitlan) y lo dice en `paleta_por_que`; no
    repite la de las últimas PALETA_NO_REPETIR piezas de video. La maqueta (_fixture) queda fuera."""
    r = VD.rel(trabajo)
    if "/_fixture" in r or r.startswith(("..", "/")) or (leer(os.path.join(trabajo, "video.json")).get("fixture") if os.path.exists(os.path.join(trabajo, "video.json")) else False):
        return []   # maquetas y pruebas en carpetas temporales
    f, pal = [], enc.get("paleta")
    if pal not in paletas():
        return ["H8p encuadre: «paleta» es una de %s" % ", ".join(paletas())]
    if len((enc.get("paleta_por_que") or "").split()) < 3:
        f.append("H8p encuadre: falta «paleta_por_que»: de qué tinte del tema sale %s (color de la marca, del partido o la "
                 "institución, el material o el lugar), no el azul por defecto" % pal)
    st = leer(os.path.join(trabajo, "video.json")) if os.path.exists(os.path.join(trabajo, "video.json")) else {}
    rec = paletas_recientes(st.get("slug"))
    if pal in rec:
        f.append("H8p encuadre: la paleta %s ya la usó una de las últimas %d piezas (%s): elige otra con el tinte del tema"
                 % (pal, PALETA_NO_REPETIR, ", ".join(rec)))
    mt = enc.get("musica_tema")
    if mt not in VD.MUSICA_TEMAS:
        f.append("H8m encuadre: «musica_tema» es uno de %s: la música va por el TEMA (corrupción, política, justicia…), "
                 "no por el color" % ", ".join(VD.MUSICA_TEMAS))
    elif not VD.elegir_musica_tema(mt):
        f.append("H8m encuadre: el tema de música «%s» no tiene pistas en design/musica/catalogo.json" % mt)
    return f


def cmd_encuadre(a):
    trabajo = os.path.abspath(a.trabajo)
    enc = encuadre(trabajo)
    if not enc:
        return falla("falta %s/encuadre.json" % VD.rel(trabajo))
    f = revisar_encuadre(enc) + revisar_paleta(enc, trabajo)
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
    aplicar_extension(trabajo)   # H17 en /serie («pasa_a») y el formato de la parte leen el TRABAJO actual
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
    esquema = VD.revisar_esquema(g)   # V24 (m109): claves y tipos de cada escena antes de los gates
    if esquema:
        for x in esquema:
            print("FALLA", x)
        return 1
    st = VD.estado(trabajo)
    H = historia_de(trabajo)
    # secuencias de voz (H20): si el guion no las trae, el script las deriva de los actos y las escribe (voz_continua por
    # defecto en historia: la voz se graba de corrido por secuencia)
    if g.get("voz_continua", True) and not g.get("secuencias") and g.get("escenas"):
        aplicar_extension(trabajo)
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
    loc = os.path.join(trabajo, "locucion.json")
    if rc == 0 and os.path.exists(loc) and leer(loc)["estimado_s"] > OBJETIVO_DURO_S:
        # también en aplicar y en los retoques: un lote de arreglos que alarga el video no pasa (recorta con él)
        fallas.append("H5 %.0f s estimados: pasa de %d s (objetivo %d, %d–%d); recorta una oración o una escena (la que repite)"
                      % (leer(loc)["estimado_s"], OBJETIVO_DURO_S, OBJETIVO_S, OBJETIVO_MIN_S, OBJETIVO_AVISO_S))
    for x in fallas:
        print("FALLA", x)
    todas = fallas + [l[len("FALLA "):] for l in salida.splitlines() if l.startswith("FALLA ")]
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
    """AVISO H5: el objetivo es 150 s (135–165); entre 165 y OBJETIVO_DURO_S avisa, por encima falla (guion --check)."""
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



def cmd_cierres(a):
    """cierres.json → video.py cierres (5 opciones para el usuario); con --usar o --propio pasa el cierre al guion y corre
    narracion --check y guion --check: si el gate lo rechaza, guion.json vuelve a guion.previo.json."""
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    cambia = bool(a.usar or a.propio)
    rc = VD.cmd_cierres(a)
    if rc or not cambia:
        return rc
    if correr_gates(trabajo):
        shutil.copyfile(os.path.join(trabajo, "guion.previo.json"), os.path.join(trabajo, "guion.json"))
        correr_gates(trabajo)   # locucion.json vuelve a corresponder al guion restaurado
        print("cierres: el gate rechaza ese cierre; guion.json queda como estaba")
        return 1
    print("cierres: %s en el guion · gate ok (la voz del cierre cambió: voz --pendientes)" % a.usar)
    return 0

def cmd_ganchos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    if a.check:
        a.usar = None
    return VD.cmd_ganchos(a)


# ---------- personas: el retrato de cada personaje y la tarjeta de su primera mención (H21, H22) ----------
INSTITUCION = re.compile(r"\b(ministerio|comisi[oó]n|tribunal|congreso|corte|sala|fiscal[ií]a|gobierno|juzgado|polic[ií]a|"
                         r"contralor[ií]a|superintendencia|organismo|banco|universidad|empresa|partido|ej[eé]rcito|naciones)\b", re.I)
TARJETA_S, TARJETAS_POR_ESCENA, TARJETA_SEPARA_S, CARGO_MAX = 2.2, 2, 1.2, 28


def es_persona(p):
    """Un personaje es una persona (lleva retrato y tarjeta) si el encuadre lo dice (tipo) o, sin tipo, si su nombre
    tiene al menos dos palabras con mayúscula, ninguna sigla y nada de institución."""
    if p.get("tipo"):
        return p["tipo"] == "persona"
    nom = (p.get("nombre") or "").strip()
    pal = nom.split()
    return len(pal) >= 2 and not INSTITUCION.search(nom) and not any(w.isupper() and len(w) > 1 for w in pal) \
        and sum(1 for w in pal if w[:1].isupper()) >= 2


def claves_personaje(p):
    # de una persona, un alias sin nombre propio («el presidente») no la identifica: «el presidente Bernardo Arévalo»
    # sacaba la tarjeta de Laugerud (terremoto P4). Las instituciones sí conservan los suyos («el Comité»)
    genero = (p.get("tipo") == "persona") if p.get("tipo") else es_persona(p)
    return [VD._plano(p["nombre"])] + [VD._plano(a) for a in p.get("alias") or [] if (a or "").strip()
                                       and not (genero and not any(c.isupper() for c in a))]


def retrato_de_personaje(p, fotos):
    """(archivo, foco, foto_id, evidencia) del retrato de un personaje: una cara de una foto marcada con su nombre
    (historia.py focos --persona) o una foto con su retrato_de (y su única cara); None si no hay."""
    claves = set(claves_personaje(p))
    for fid, rec in fotos.items():
        for f in rec.get("focos") or []:
            if f.get("persona") and VD._plano(f["persona"]) in claves:
                return rec.get("archivo"), f, fid, " ".join(filter(None, [f.get("evidencia"), rec.get("descripcion"), rec.get("retrato_evidencia")]))
    for fid, rec in fotos.items():
        if rec.get("retrato_de") and VD._plano(rec["retrato_de"]) in claves:
            fs = rec.get("focos") or []
            return rec.get("archivo"), (fs[0] if len(fs) == 1 else None), fid, \
                " ".join(filter(None, [rec.get("retrato_evidencia"), rec.get("descripcion")]))
    return None


def primeras_menciones(g, personajes):
    """{nombre: número de escena} de la primera vez que la voz nombra a cada personaje (como H18: un alias que es
    parte del nombre de otro personaje que también suena no cuenta)."""
    voces = [plano_voz(e.get("texto") or "") for e in g.get("escenas") or []]
    nombres = [VD._plano(p["nombre"]) for p in personajes]
    out = {}
    for p in personajes:
        nom = VD._plano(p["nombre"])
        otros = [o for o in nombres if o != nom]
        for j, v in enumerate(voces, 1):
            if any(re.search(r"\b%s\b" % re.escape(c), v) and not (c != nom and any(c in o and re.search(r"\b%s\b" % re.escape(o), v) for o in otros))
                   for c in claves_personaje(p)):
                out[p["nombre"]] = j
                break
    return out


def revisar_personas(g, enc, fotos):
    """H21: cada persona que la voz nombra tiene retrato, y su evidencia (el pie, la categoría o la descripción de la
    foto) dice su apellido. H22: lo comprueba el gate; la tarjeta la arma `tiempos` sola en la primera mención."""
    f = []
    pers = [p for p in enc.get("personajes") or [] if isinstance(p, dict) and (p.get("nombre") or "").strip() and es_persona(p)]
    prim = primeras_menciones(g, pers)
    for p in pers:
        if p["nombre"] not in prim:
            continue
        r = retrato_de_personaje(p, fotos)
        if not r and (p.get("sin_retrato") or "").strip():
            print("AVISO H22 «%s» va sin retrato (%s): su tarjeta muestra solo nombre y cargo" % (p["nombre"], p["sin_retrato"]))
            continue
        if not r:
            f.append("H22 «%s» suena en la escena %d y no tiene retrato (o, si no hay ninguna con evidencia, «sin_retrato»: motivo en el personaje): baja una foto con historia.py foto --retrato-de \"%s\" "
                     "--retrato-evidencia \"…\" o marca su cara en una foto de grupo (historia.py focos TRABAJO --foto ID --cara K "
                     "--persona \"%s\" --evidencia \"…\")" % (p["nombre"], prim[p["nombre"]], p["nombre"], p["nombre"]))
            continue
        apellido = VD._plano(p["nombre"]).split()[-1]
        if apellido not in VD._plano(r[3] or ""):
            f.append("H21 el retrato de «%s» (%s) no tiene evidencia que lo nombre: --evidencia con el pie o la categoría"
                     % (p["nombre"], r[2]))
    # `sujeto` de una escena explica: un personaje del encuadre con retrato (su cara va sobre el lienzo toda la escena)
    for i, e in enumerate(g.get("escenas") or [], 1):
        su = (e.get("sujeto") or "").strip() if e.get("tipo") == "explica" else ""
        if not su:
            continue
        p = next((x for x in enc.get("personajes") or [] if isinstance(x, dict) and VD._plano(su) in claves_personaje(x)), None)
        if not p or not retrato_de_personaje(p, fotos):
            f.append("H22 escena %d: «sujeto» «%s» es un personaje del encuadre con retrato" % (i, su))
    return f


RED_NODOS, RED_NIVELES, RED_NODO_S = (3, 8), 4, 1.1
RED_ATRIBUIR = ("alegato", "en_disputa", "estimacion", "opinion")


def relaciones_h(H):
    """[{de, a, rel, hecho, tipo_hecho, estado}] de los hechos publicables que traen `relaciones` (el investigador las
    anota y el verificador las confirma contra la cita guardada)."""
    out = []
    for h in H.get("hechos") or []:
        for r in h.get("relaciones") or []:
            if isinstance(r, dict) and r.get("de") and r.get("a"):
                out.append({"de": r["de"], "a": r["a"], "rel": r.get("rel") or "", "hecho": h["id"],
                            "tipo_hecho": h.get("tipo_hecho") or "acto", "estado": h.get("estado")})
    return out


def revisar_red(g, H):
    """H23, la escena `red` (el organigrama del caso): 3–8 nodos, cada uno un personaje del encuadre (persona con
    retrato o institución), ≤ 3 niveles con 1–2 nodos de nivel 0 (quien manda, arriba; nunca una fila de uno por nivel); cada arista con un `hecho`
    publicable cuyas `relaciones` unen esos dos extremos; si alguna arista es un alegato, una estimación, una opinión o
    está en disputa, la escena lleva `atribuida: true` (chip «Según la acusación» y arista punteada) y la voz atribuye
    («según la fiscalía…»); cada `dice` suena en la voz y en orden; ≤ 1 escena red por video; ≥ 1.1 s por nodo."""
    es = [e for e in g.get("escenas") or [] if e.get("tipo") == "red"]
    f = []
    for e in es:
        if e.get("estilo") not in (None, "red", "tablero"):
            f.append("H23 escena red: estilo «%s» (red = organigrama por niveles · tablero = cuadritos unidos con hilo)" % e.get("estilo"))
    if len(es) > 1:
        f.append("H23 %d escenas red: va 1 por video (o parte)" % len(es))
    if not es:
        return f
    enc = encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    pers = {VD._plano(c): p for p in enc.get("personajes") or [] if isinstance(p, dict) and p.get("nombre") for c in claves_personaje(p)}
    rels = relaciones_h(H)
    hechos = {h["id"]: h for h in H.get("hechos") or []}
    fotos = fotos_h()
    for e in es:
        i = (g.get("escenas") or []).index(e) + 1
        nodos, aristas = e.get("nodos") or [], e.get("aristas") or []
        if not RED_NODOS[0] <= len(nodos) <= RED_NODOS[1]:
            f.append("H23 escena %d: %d nodos; van %d–%d" % (i, len(nodos), *RED_NODOS))
        ids = {}
        for nd in nodos:
            p = pers.get(VD._plano(nd.get("personaje") or ""))
            if not p:
                f.append("H23 escena %d: el nodo «%s» no es un personaje del encuadre" % (i, nd.get("personaje")))
                continue
            if es_persona(p) and not retrato_de_personaje(p, fotos):
                f.append("H23 escena %d: «%s» no tiene retrato (H22)" % (i, p["nombre"]))
            if not isinstance(nd.get("nivel"), int) or not 0 <= nd["nivel"] < RED_NIVELES:
                f.append("H23 escena %d: «%s» sin nivel 0–%d" % (i, nd.get("personaje"), RED_NIVELES - 1))
            ids[nd.get("id")] = p
        cima = sum(1 for nd in nodos if nd.get("nivel") == 0)
        if not 1 <= cima <= 2:
            f.append("H23 escena %d: %d nodos de nivel 0: arriba va quien manda (uno, o los dos que mandan juntos)" % (i, cima))
        # (2026-11-06) una fila de una persona por nivel no es un organigrama: no se ve quién está al lado de quién
        acus = [nd for nd in nodos if (ids.get(nd.get("id")) or {}).get("bando") != "investigador"]
        por_nivel = {}
        for nd in acus:
            por_nivel.setdefault(nd.get("nivel"), []).append(nd)
        if len(por_nivel) > 3:
            f.append("H23 escena %d: %d niveles; van ≤ 3 (los que están a la misma altura del caso, lado a lado)" % (i, len(por_nivel)))
        if len(por_nivel) >= 3 and all(len(v) == 1 for v in por_nivel.values()):
            f.append("H23 escena %d: una persona por nivel es una fila, no un organigrama: pon lado a lado a los de la "
                     "misma altura (p. ej. el presidente y la vicepresidenta arriba) y suma a los investigadores (bando investigador)" % i)
        atrib = False
        for ar in aristas:
            de, a = ids.get(ar.get("de")), ids.get(ar.get("a"))
            h = hechos.get(ar.get("hecho"))
            if not (de and a):
                f.append("H23 escena %d: la arista %s→%s une nodos que no existen" % (i, ar.get("de"), ar.get("a")))
                continue
            if not h:
                f.append("H23 escena %d: la arista %s→%s no tiene un hecho publicable (`hecho`)" % (i, de["nombre"], a["nombre"]))
                continue
            cd, ca = set(claves_personaje(de)), set(claves_personaje(a))
            if not any(r["hecho"] == h["id"] and {VD._plano(r["de"]), VD._plano(r["a"])} & cd and {VD._plano(r["de"]), VD._plano(r["a"])} & ca
                       for r in rels):
                f.append("H23 escena %d: el hecho %s no registra la relación %s–%s (relaciones del hecho, verificadas)"
                         % (i, h["id"], de["nombre"], a["nombre"]))
            if (h.get("tipo_hecho") or "acto") in RED_ATRIBUIR or h.get("estado") == "en_disputa":
                atrib = True
        if atrib and not e.get("atribuida"):
            f.append("H23 escena %d: hay relaciones que son alegatos (sin sentencia): «atribuida»: true (chip «Según la "
                     "acusación», arista punteada) y la voz atribuye" % i)
        if atrib and not RE_SEGUN_FUENTE.search(e.get("texto") or "") and not re.search(r"\bseg[uú]n\b|\bacus", e.get("texto") or "", re.I):
            f.append("H23 escena %d: la voz no atribuye la estructura («según la fiscalía…», «la acusación…»)" % i)
        voz = VD._plano(e.get("texto") or "")
        pos = -1
        for nd in nodos:
            d = VD._plano(nd.get("dice") or nd.get("personaje") or "")
            k = voz.find(d, pos + 1) if d else -1
            if k < 0:
                f.append("H23 escena %d: la voz no dice «%s» (o no en el orden de los nodos)" % (i, nd.get("dice") or nd.get("personaje")))
            else:
                pos = k
    return f


def t_red(S, e, ps, pal, fin_voz, dur, g):
    """La escena red (video/red.html): cada nodo entra con su retrato o su sigla cuando la voz lo dice; la arista hacia
    él se dibuja al entrar el segundo extremo; las atribuidas, punteadas, con el chip «Según la acusación»."""
    esc = escena_guion(S, g)
    enc = encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    pers = {VD._plano(c): p for p in enc.get("personajes") or [] if isinstance(p, dict) and p.get("nombre") for c in claves_personaje(p)}
    hechos = {h["id"]: h for h in (H_ACTUAL or {}).get("hechos") or []}
    fotos = fotos_h()
    ws = [VD._plano(w["text"]) for w in pal]
    t0 = VD.TRANSICION + 0.25 + (DESFASE_ROTULO if rotulo_de(esc) else 0.0)
    nodos, ult, k0 = [], t0, 0
    for nd in esc.get("nodos") or []:
        p = pers.get(VD._plano(nd.get("personaje") or "")) or {"nombre": nd.get("personaje")}
        toks = VD._plano(nd.get("dice") or p["nombre"]).split()
        k = next((j for j in range(k0, len(ws) - len(toks) + 1) if ws[j:j + len(toks)] == toks), None)
        t = max(ult + 0.5, pal[k]["start"] - 0.1) if k is not None else ult + 0.9
        k0 = k + len(toks) if k is not None else k0
        r = retrato_de_personaje(p, fotos) if es_persona(p) else None
        cargo = (p.get("cargo") or p.get("presentacion") or "").strip()
        nodos.append({"id": nd.get("id"), "nombre": p["nombre"], "corto": nd.get("corto") or (p.get("alias") or [p["nombre"]])[0],
                      "cargo": cargo[:CARGO_MAX], "nivel": nd.get("nivel", 1), "bando": p.get("bando") or nd.get("bando") or "acusado",
                      "foto": r[0] if r else None, "foco": r[1] if r else None, "sigla": None if r else (p.get("nombre") or "")[:8],
                      "start": round(min(t, dur - 1.0), 3)})
        ult = t
    por = {n["id"]: n for n in nodos}
    aristas = []
    for ar in esc.get("aristas") or []:
        a, b = por.get(ar.get("de")), por.get(ar.get("a"))
        if not (a and b):
            continue
        h = hechos.get(ar.get("hecho")) or {}
        atr = (h.get("tipo_hecho") or "acto") in RED_ATRIBUIR or h.get("estado") == "en_disputa"
        aristas.append({"de": a["id"], "a": b["id"], "rel": ar.get("rel") or "", "atribuida": atr,
                        "start": round(max(a["start"], b["start"]) + 0.15, 3)})
    # estilo "tablero": los mismos datos y el mismo gate H23, dibujados como tablero de investigación (cuadritos e hilos,
    # sin tachas: video/tablero.html) en vez del organigrama por niveles
    S["pagina"] = "tablero" if esc.get("estilo") == "tablero" else "red"
    S["G"] = {"titulo": esc.get("titulo") or "", "nodos": nodos, "aristas": aristas, "atribuida": bool(esc.get("atribuida")),
              "fuente": ("Fuente: " + esc["fuente"]) if esc.get("fuente") else None}
    if esc.get("atribuida"):
        S["chip"] = {"texto": "Según la acusación", "tono": "ink", "desde": round(t0, 3), "pos": "arriba"}
    S["T"] = {"ini": round(t0, 3)}
    ev = [(0.1, "entrada")] + [(n["start"], "nodo") for n in nodos] + [(x["start"], "arista") for x in aristas]
    sfx = entrada_sfx(S, e, esc) + [(n["start"], "voto") for n in nodos[::2]]
    R = rotulo_de(esc)
    if R:
        S["R"] = armar_rotulo(S, esc, ps, g, R)
        ev_r, sfx_r = eventos_rotulo(S)
        ev += ev_r
        sfx += sfx_r
    return ev, sfx


# ---------- escena vias: el mapa vial real de una ciudad, animado por capas (H27, 2026-11-12) ----------
VIAS_DIR = os.path.join(RAIZ, "design", "vias")
VIAS_CAPAS, VIAS_POR_VIDEO, VIAS_CAPA_S, VIAS_BURBUJA_R = (2, 6), 2, 1.6, 150.0
VIAS_TITULO, VIAS_ETIQUETA, VIAS_ROTULO, VIAS_ACERCA = 30, 24, 40, (1.4, 4.0)
VIAS_PRIMERA = 0.35   # la primera capa suena en el primer 35 % de la voz (si no, el mapa queda quieto demasiado)
VIAS_CLAVES = {"dice", "arterias", "sentido", "nivel", "lugar", "etiqueta", "cifra", "rotulo", "zoom", "acerca", "burbuja", "riel", "carrera"}
VIAS_VECES = (1.2, 10)   # carrera: cuántas veces más tarda el viaje de hoy que el mismo viaje sin tráfico


def vias_de(rid):
    """La red vial design/vias/<id>.json (la arma scripts/build_vias.py desde OpenStreetMap), o None."""
    if not rid or not re.fullmatch(r"[a-z0-9-]+", str(rid)):
        return None
    ruta = os.path.join(VIAS_DIR, "%s.json" % rid)
    return leer(ruta) if os.path.isfile(ruta) else None


def redes_viales():
    if not os.path.isdir(VIAS_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(VIAS_DIR) if f.endswith(".json") and not f.endswith(".fuente.json"))


def respaldo_actual():
    """Los valores con respaldo del trabajo en curso (cifras y números de los hechos), o None fuera de un trabajo."""
    if not TRABAJO_ACTUAL:
        return None
    try:
        return VD.valores_respaldo(VD.estado(TRABAJO_ACTUAL)["hilo"])[0]
    except Exception:   # un trabajo a medio armar (pruebas del gate): sin valores no se revisan los números
        return None


def lineas_vias():
    """Para el digesto del guionista: la forma de la escena vias y las redes que hay, con sus arterias y lugares."""
    out = ["- vias (el mapa vial REAL de la ciudad, de OpenStreetMap, animado por capas; H27): red_vial (id), titulo ≤ %d, capas %d–%d "
           "[{dice (la palabra o el nombre que la voz dice al entrar la capa, sin cifras; en el orden de la voz), arterias? [ids] (su "
           "trazo crece del centro hacia afuera; sentido: «entra» = hacia el centro; nivel 0–1 = hasta dónde), lugar? id (aro y rótulo) "
           "con etiqueta? ≤ %d, cifra? ≤ %d con rotulo? ≤ %d (el dato de arriba), zoom? id de lugar o «todo» (la cámara solo se mueve "
           "aquí; acerca? %.1f–%.1f), burbuja? {lugar, valor} (área ∝ valor; el mismo lugar en dos capas crece), riel? true, carrera? "
           "{arteria, veces} (dos puntos hacen el mismo viaje hacia el centro: uno sin tráfico y el de hoy, que tarda `veces` más; "
           "`veces` con respaldo)}], fuente "
           "(obligatoria si hay cifra, etiqueta o burbuja). Una capa por frase: ≥ %.1f s de voz por capa; la primera capa suena en la primera frase; ≤ %d por video. Cada número "
           "en pantalla con respaldo, como en una foto"
           % (VIAS_TITULO, *VIAS_CAPAS, VIAS_ETIQUETA, CIFRA_CARACTERES, VIAS_ROTULO, *VIAS_ACERCA, VIAS_CAPA_S, VIAS_POR_VIDEO)]
    for rid in redes_viales():
        red = vias_de(rid)
        out.append("  · red_vial «%s» (%s): arterias %s; lugares %s%s"
                   % (rid, red.get("nombre"), ", ".join("%s (%s)" % (k, v["nombre"]) for k, v in red["arterias"].items()),
                      ", ".join("%s (%s)" % (k, v["nombre"]) for k, v in red["lugares"].items()), "; con vía de tren (riel)" if red.get("riel") else ""))
    if len(out) == 1:
        out.append("  · no hay redes viales en design/vias/: una nueva se arma con python3 scripts/build_vias.py <id> (receta <id>.fuente.json)")
    return out


def revisar_vias(g, valores=None, anios=None):
    """H27, la escena `vias` (el mapa vial real por capas): la red existe en design/vias/; título en un renglón; 2–6
    capas, cada una con su `dice` (sin cifras) que suena en la voz y en orden, y con algo que mostrar; arterias, lugares
    y zoom son ids de la red; cada número en pantalla (cifra, rótulo, etiqueta, título, valor de una burbuja) con
    respaldo; con un dato en pantalla, `fuente`; ≥ 1.6 s de voz por capa; ≤ 2 escenas vias por video."""
    es = [(i, e) for i, e in enumerate(g.get("escenas") or [], 1) if e.get("tipo") == "vias"]
    f = []
    if len(es) > VIAS_POR_VIDEO:
        f.append("H27 %d escenas vias: van ≤ %d por video (o parte)" % (len(es), VIAS_POR_VIDEO))

    def numeros(i, que, txt):
        if valores is None or not txt:
            return
        resto = str(txt)
        if anios is not None:
            for y in set(RE_ANIO.findall(resto)):
                if y not in anios:
                    f.append("H27 escena %d: el año %s de %s no está en ningún hecho, cita o cifra verificada" % (i, y, que))
            resto = RE_ANIO.sub(" ", resto)
        sin = VD.sin_respaldo(resto, valores)
        if sin:
            f.append("H27 escena %d: %s «%s» con un número sin respaldo: %s" % (i, que, txt, ", ".join(map(str, sin))))

    for i, e in es:
        red = vias_de(e.get("red_vial"))
        if not red:
            f.append("H27 escena %d: red_vial «%s» no existe en design/vias/ (hay: %s; una nueva se arma con scripts/build_vias.py)"
                     % (i, e.get("red_vial"), ", ".join(redes_viales()) or "ninguna"))
            continue
        tit = (e.get("titulo") or "").strip()
        if not tit or len(tit) > VIAS_TITULO:
            f.append("H27 escena %d: titulo de 1–%d caracteres (un renglón sobre el mapa); llegó «%s»" % (i, VIAS_TITULO, tit))
        numeros(i, "el título", tit)
        capas = e.get("capas") if isinstance(e.get("capas"), list) else []
        if not VIAS_CAPAS[0] <= len(capas) <= VIAS_CAPAS[1]:
            f.append("H27 escena %d: %d capas; van %d–%d (una por frase de la voz)" % (i, len(capas), *VIAS_CAPAS))
        voz, pos, con_dato = VD._plano(e.get("texto") or ""), -1, False
        for k, c in enumerate(capas, 1):
            if not isinstance(c, dict):
                f.append("H27 escena %d capa %d: cada capa es un objeto {dice, …}" % (i, k))
                continue
            if set(c) - VIAS_CLAVES:
                f.append("H27 escena %d capa %d: clave desconocida %s (van: %s)" % (i, k, ", ".join(sorted(set(c) - VIAS_CLAVES)), ", ".join(sorted(VIAS_CLAVES))))
            d = VD._plano(c.get("dice") or "")
            if not d or re.search(r"\d", str(c.get("dice") or "")):
                f.append("H27 escena %d capa %d: `dice` es la palabra o el nombre que la voz dice al entrar la capa, sin cifras "
                         "(«Mixco», «El Trébol», «carriles»)" % (i, k))
            else:
                j = voz.find(d, pos + 1)
                if j < 0:
                    f.append("H27 escena %d capa %d: la voz no dice «%s» (o no en el orden de las capas)" % (i, k, c.get("dice")))
                else:
                    if k == 1 and j > VIAS_PRIMERA * max(1, len(voz)):
                        f.append("H27 escena %d: la primera capa entra con «%s», pasado el %d %% de la voz: el mapa se queda quieto "
                                 "mientras tanto (V21); que la primera frase ya encienda algo" % (i, c.get("dice"), VIAS_PRIMERA * 100))
                    pos = j
            if not any(c.get(x) for x in ("arterias", "lugar", "zoom", "burbuja", "riel", "cifra", "carrera")):
                f.append("H27 escena %d capa %d: la capa no muestra nada (arterias, lugar, zoom, burbuja, riel, carrera o cifra)" % (i, k))
            ca = c.get("carrera")
            if ca is not None:
                if not (isinstance(ca, dict) and ca.get("arteria") in red["arterias"] and isinstance(ca.get("veces"), (int, float))
                        and not isinstance(ca.get("veces"), bool) and VIAS_VECES[0] <= ca["veces"] <= VIAS_VECES[1]):
                    f.append("H27 escena %d capa %d: carrera {arteria (de la red), veces (%.1f–%d: cuántas veces más tarda el viaje de hoy "
                             "que el mismo viaje sin tráfico)}" % (i, k, *VIAS_VECES))
                else:
                    numeros(i, "las veces de la carrera de la capa %d" % k, "%g" % ca["veces"])
            arts = c.get("arterias")
            if arts is not None and (not isinstance(arts, list) or any(a not in red["arterias"] for a in arts)):
                f.append("H27 escena %d capa %d: arterias %s; en «%s» hay: %s" % (i, k, arts, e.get("red_vial"), ", ".join(red["arterias"])))
            if c.get("sentido") not in (None, "sale", "entra"):
                f.append("H27 escena %d capa %d: sentido «%s» (sale = del centro hacia afuera · entra = hacia el centro)" % (i, k, c.get("sentido")))
            nv = c.get("nivel")
            if nv is not None and not (isinstance(nv, (int, float)) and not isinstance(nv, bool) and 0 < nv <= 1):
                f.append("H27 escena %d capa %d: nivel %s; va entre 0 y 1 (la parte de la arteria que se enciende)" % (i, k, nv))
            if c.get("lugar") is not None and c.get("lugar") not in red["lugares"]:
                f.append("H27 escena %d capa %d: lugar «%s»; en «%s» hay: %s" % (i, k, c.get("lugar"), e.get("red_vial"), ", ".join(red["lugares"])))
            if c.get("zoom") is not None and c.get("zoom") != "todo" and c.get("zoom") not in red["lugares"]:
                f.append("H27 escena %d capa %d: zoom «%s»; va un lugar de la red o «todo»" % (i, k, c.get("zoom")))
            ac = c.get("acerca")
            if ac is not None and not (isinstance(ac, (int, float)) and not isinstance(ac, bool) and VIAS_ACERCA[0] <= ac <= VIAS_ACERCA[1]):
                f.append("H27 escena %d capa %d: acerca %s; va de %.1f a %.1f" % (i, k, ac, *VIAS_ACERCA))
            if c.get("etiqueta") and not c.get("lugar"):
                f.append("H27 escena %d capa %d: la etiqueta va en el rótulo de un `lugar`" % (i, k))
            if c.get("rotulo") and not c.get("cifra"):
                f.append("H27 escena %d capa %d: `rotulo` acompaña a una `cifra`" % (i, k))
            b = c.get("burbuja")
            if b is not None:
                if not (isinstance(b, dict) and b.get("lugar") in red["lugares"] and isinstance(b.get("valor"), (int, float))
                        and not isinstance(b.get("valor"), bool) and b["valor"] > 0):
                    f.append("H27 escena %d capa %d: burbuja {lugar (de la red), valor > 0}" % (i, k))
                else:
                    numeros(i, "el valor de la burbuja de la capa %d" % k, "%g" % b["valor"])
            if c.get("riel") and not red.get("riel"):
                f.append("H27 escena %d capa %d: la red «%s» no tiene vía de tren" % (i, k, e.get("red_vial")))
            for que, txt, tope in (("la cifra", c.get("cifra"), CIFRA_CARACTERES), ("el rótulo", c.get("rotulo"), VIAS_ROTULO),
                                   ("la etiqueta", c.get("etiqueta"), VIAS_ETIQUETA)):
                if txt is None:
                    continue
                if not isinstance(txt, str) or not txt.strip() or len(txt) > tope:
                    f.append("H27 escena %d capa %d: %s va de 1 a %d caracteres; llegó «%s»" % (i, k, que, tope, txt))
                else:
                    numeros(i, "%s de la capa %d" % (que, k), txt)
            con_dato = con_dato or bool(c.get("cifra") or c.get("etiqueta") or b)
        fu = (e.get("fuente") or "").strip()
        if con_dato and not fu:
            f.append("H27 escena %d: con una cifra, una etiqueta o una burbuja en pantalla, la escena lleva `fuente`" % i)
        if len(fu) > FUENTE_CARACTERES:
            f.append("H27 escena %d: fuente de %d caracteres (máximo %d)" % (i, len(fu), FUENTE_CARACTERES))
        s_ = VD.segundos_voz(e.get("texto"))
        if capas and s_ < VIAS_CAPA_S * len(capas):
            f.append("H27 escena %d: %d capas en %.1f s de voz estimados: van ≥ %.1f s por capa (quita capas o alarga la voz)"
                     % (i, len(capas), s_, VIAS_CAPA_S))
    return f


def t_vias(S, e, ps, pal, fin_voz, dur, g):
    """La escena vias (video/vias.html): cada capa entra cuando la voz dice su `dice` (después del rótulo de acto, si lo
    hay); el radio de cada burbuja sale de su valor frente al mayor de la escena (área ∝ valor)."""
    esc = escena_guion(S, g)
    ws = [VD._plano(w["text"]) for w in pal]
    R = rotulo_de(esc)
    t0 = VD.TRANSICION + 0.25 + (DESFASE_ROTULO if R else 0.0)
    brutas = [c for c in esc.get("capas") or [] if isinstance(c, dict)]
    vmax = max([c["burbuja"]["valor"] for c in brutas if isinstance(c.get("burbuja"), dict) and c["burbuja"].get("valor")] or [1])
    capas, ult, k0 = [], t0 - 0.5, 0
    for c in brutas:
        toks = VD._plano(c.get("dice") or "").split()
        k = next((j for j in range(k0, len(ws) - len(toks) + 1) if ws[j:j + len(toks)] == toks), None) if toks else None
        t = max(ult + 0.5, pal[k]["start"] - 0.1) if k is not None else ult + 0.9
        k0 = k + len(toks) if k is not None else k0
        t = min(t, dur - 1.0)
        capa = {"start": round(t, 3)}
        for campo in ("arterias", "sentido", "nivel", "lugar", "etiqueta", "cifra", "rotulo", "zoom", "acerca"):
            if c.get(campo) is not None:
                capa[campo] = c[campo]
        if c.get("riel"):
            capa["riel"] = True
        if isinstance(c.get("carrera"), dict):
            capa["carrera"] = {"arteria": c["carrera"].get("arteria"), "veces": c["carrera"].get("veces")}
        b = c.get("burbuja")
        if isinstance(b, dict) and b.get("valor"):
            capa["burbuja"] = {"lugar": b.get("lugar"), "r": round(VIAS_BURBUJA_R * (b["valor"] / vmax) ** 0.5, 1)}
        capas.append(capa)
        ult = t
    S["pagina"] = "vias"
    S["M"] = {"red": esc.get("red_vial"), "titulo": esc.get("titulo") or "", "capas": capas,
              "fuente": ("Fuente: " + esc["fuente"]) if esc.get("fuente") else None}
    S["T"] = {"ini": round(t0, 3)}
    ev = [(0.1, "entrada")] + [(c["start"], "nodo") for c in capas]
    sfx = entrada_sfx(S, e, esc)
    if R:
        S["R"] = armar_rotulo(S, esc, ps, g, R)
        ev_r, sfx_r = eventos_rotulo(S)
        ev += ev_r
        sfx += sfx_r
    return ev, sfx


# ---------- escenas con archivos reales (2026-11-12): ayudantes comunes de lupa, deptos, pagina, cortina, archivo y bandos ----------
def entradas_dice(items, pal, t0, dur):
    """Cuándo entra cada elemento con `dice`: en la palabra de la voz que lo dice (en orden), nunca antes de t0 ni a
    menos de 0.5 s del anterior; si la voz no lo dice, 0.9 s después del anterior."""
    ws = [VD._plano(w["text"]) for w in pal]
    out, ult, k0 = [], t0 - 0.5, 0
    for c in items:
        toks = VD._plano((c or {}).get("dice") or "").split()
        k = next((j for j in range(k0, len(ws) - len(toks) + 1) if ws[j:j + len(toks)] == toks), None) if toks else None
        t = max(ult + 0.5, pal[k]["start"] - 0.1) if k is not None else ult + 0.9
        k0 = k + len(toks) if k is not None else k0
        t = min(t, dur - 1.0)
        out.append(round(t, 3))
        ult = t
    return out


def revisar_dice(f, gate, i, items, texto, que, primera=True):
    """Cada elemento es un objeto con su `dice` (sin cifras) que suena en la voz y en orden; el primero, en el primer
    35 % de la voz (si no, la pantalla queda quieta: V21)."""
    voz, pos = VD._plano(texto or ""), -1
    for k, c in enumerate(items, 1):
        if not isinstance(c, dict):
            f.append("%s escena %d %s %d: es un objeto {dice, …}" % (gate, i, que, k))
            continue
        d = VD._plano(c.get("dice") or "")
        if not d or re.search(r"\d", str(c.get("dice") or "")):
            f.append("%s escena %d %s %d: `dice` es la palabra o el nombre que la voz dice al entrar, sin cifras" % (gate, i, que, k))
            continue
        j = voz.find(d, pos + 1)
        if j < 0:
            f.append("%s escena %d %s %d: la voz no dice «%s» (o no en ese orden)" % (gate, i, que, k, c.get("dice")))
            continue
        if k == 1 and primera and j > VIAS_PRIMERA * max(1, len(voz)):
            f.append("%s escena %d: lo primero entra con «%s», pasado el %d %% de la voz: la pantalla se queda quieta mientras "
                     "tanto (V21); que la primera frase ya muestre algo" % (gate, i, c.get("dice"), VIAS_PRIMERA * 100))
        pos = j


def numeros_pantalla(f, gate, i, que, txt, valores, anios):
    """Los números de un texto de pantalla con respaldo (y sus años en un hecho); sin `valores` no se revisa."""
    if valores is None or not txt:
        return
    resto = str(txt)
    if anios is not None:
        for y in sorted(set(RE_ANIO.findall(resto))):
            if y not in anios:
                f.append("%s escena %d: el año %s de %s no está en ningún hecho, cita o cifra verificada" % (gate, i, y, que))
        resto = RE_ANIO.sub(" ", resto)
    sin = VD.sin_respaldo(resto, valores)
    if sin:
        f.append("%s escena %d: %s «%s» con un número sin respaldo: %s" % (gate, i, que, txt, ", ".join(map(str, sin))))


def foto_de(gate, i, fid, f, que="foto"):
    """El registro de una foto verificada (historia.json → fotos) o None; sin historia cargada no se revisa."""
    rec = fotos_h().get(fid)
    if rec and rec.get("archivo"):
        return rec
    if H_ACTUAL is not None:
        f.append("%s escena %d: %s «%s» no es una foto verificada (historia.json → fotos)" % (gate, i, que, fid))
    return None


def titulo_corto(f, gate, i, e, valores, anios, obligatorio=True):
    tit = (e.get("titulo") or "").strip()
    if (obligatorio and not tit) or len(tit) > VIAS_TITULO:
        f.append("%s escena %d: titulo de 1–%d caracteres (un renglón); llegó «%s»" % (gate, i, VIAS_TITULO, tit))
    numeros_pantalla(f, gate, i, "el título", tit, valores, anios)
    fu = (e.get("fuente") or "").strip()
    if len(fu) > FUENTE_CARACTERES:
        f.append("%s escena %d: fuente de %d caracteres (máximo %d)" % (gate, i, len(fu), FUENTE_CARACTERES))
    return fu


def cerrar_escena(S, e, esc, ps, g, ev):
    """El efecto de entrada y, si la escena abre un acto, su rótulo → (eventos, efectos)."""
    sfx = entrada_sfx(S, e, esc)
    R = rotulo_de(esc)
    if R:
        S["R"] = armar_rotulo(S, esc, ps, g, R)
        ev_r, sfx_r = eventos_rotulo(S)
        ev, sfx = ev + ev_r, sfx + sfx_r
    return ev, sfx


def t0_propio(esc):
    return VD.TRANSICION + 0.25 + (DESFASE_ROTULO if rotulo_de(esc) else 0.0)


def escenas_de(g, tipo):
    return [(i, e) for i, e in enumerate(g.get("escenas") or [], 1) if e.get("tipo") == tipo]


# ---------- escena lupa: una foto real que se interroga punto por punto (H28) ----------
LUPA_PUNTOS, LUPA_ETIQUETA, LUPA_PUNTO_S = (2, 5), 28, 1.8


def revisar_lupa(g, valores=None, anios=None):
    """H28, la escena `lupa`: una foto verificada; título de un renglón; estilo puntos (cámara y velo) o pistas (se
    quedan); 2–5 puntos con x, y entre 0 y 1 (dónde está en la foto), etiqueta corta y su `dice` en la voz y en orden;
    números con respaldo; ≥ 1.8 s de voz por punto."""
    f = []
    for i, e in escenas_de(g, "lupa"):
        foto_de("H28", i, e.get("foto"), f)
        titulo_corto(f, "H28", i, e, valores, anios)
        if e.get("estilo") not in (None, "puntos", "pistas"):
            f.append("H28 escena %d: estilo «%s» (puntos = la cámara se acerca a cada punto · pistas = las etiquetas se quedan)" % (i, e.get("estilo")))
        ps = e.get("puntos") if isinstance(e.get("puntos"), list) else []
        if not LUPA_PUNTOS[0] <= len(ps) <= LUPA_PUNTOS[1]:
            f.append("H28 escena %d: %d puntos; van %d–%d (uno por frase de la voz)" % (i, len(ps), *LUPA_PUNTOS))
        revisar_dice(f, "H28", i, ps, e.get("texto"), "punto")
        for k, p in enumerate(ps, 1):
            if not isinstance(p, dict):
                continue
            if set(p) - {"dice", "x", "y", "etiqueta"}:
                f.append("H28 escena %d punto %d: clave desconocida %s (van dice, x, y, etiqueta)" % (i, k, ", ".join(sorted(set(p) - {"dice", "x", "y", "etiqueta"}))))
            if not all(isinstance(p.get(c), (int, float)) and not isinstance(p.get(c), bool) and 0 <= p[c] <= 1 for c in ("x", "y")):
                f.append("H28 escena %d punto %d: x e y entre 0 y 1 (dónde está el punto en la foto: 0,0 arriba a la izquierda); "
                         "mira la foto antes de escribirlos" % (i, k))
            et = p.get("etiqueta")
            if not isinstance(et, str) or not et.strip() or len(et) > LUPA_ETIQUETA:
                f.append("H28 escena %d punto %d: etiqueta de 1–%d caracteres; llegó «%s»" % (i, k, LUPA_ETIQUETA, et))
            else:
                numeros_pantalla(f, "H28", i, "la etiqueta del punto %d" % k, et, valores, anios)
        s_ = VD.segundos_voz(e.get("texto"))
        if ps and s_ < LUPA_PUNTO_S * len(ps):
            f.append("H28 escena %d: %d puntos en %.1f s de voz estimados: van ≥ %.1f s por punto" % (i, len(ps), s_, LUPA_PUNTO_S))
    return f


def t_lupa(S, e, ps, pal, fin_voz, dur, g):
    """La escena lupa (video/lupa.html): cada punto entra cuando la voz dice su `dice`."""
    esc = escena_guion(S, g)
    fo = fotos_h().get(esc.get("foto")) or {}
    t0 = t0_propio(esc)
    brutos = [p for p in esc.get("puntos") or [] if isinstance(p, dict)]
    puntos = [{"start": t, "x": p.get("x"), "y": p.get("y"), "etiqueta": p.get("etiqueta") or ""}
              for p, t in zip(brutos, entradas_dice(brutos, pal, t0, dur))]
    S["pagina"] = "lupa"
    S["L"] = {"foto": fo.get("archivo"), "credito": fo.get("credito"), "titulo": esc.get("titulo") or "", "estilo": esc.get("estilo") or "puntos",
              "puntos": puntos, "fuente": ("Fuente: " + esc["fuente"]) if esc.get("fuente") else None}
    S["T"] = {"ini": round(t0, 3)}
    return cerrar_escena(S, e, esc, ps, g, [(0.1, "entrada")] + [(p["start"], "nodo") for p in puntos])


# ---------- escena deptos: el mapa de los 22 departamentos animado por capas (H29) ----------
DEPTOS_CAPAS, DEPTOS_POR_CAPA, DEPTOS_POR_VIDEO = (2, 6), 6, 2
DEPTOS_CLAVES = {"dice", "deptos", "etiqueta", "cifra", "rotulo", "arco", "onda", "zoom"}


def revisar_deptos(g, valores=None, anios=None):
    """H29, la escena `deptos` (el mapa de departamentos por capas): título de un renglón; 2–6 capas con su `dice` en la
    voz y en orden; `deptos` son departamentos que existen (1–6 por capa, sin repetir en la capa); `arco` pide una capa
    anterior con departamentos; `onda` y `arco` piden departamentos en su capa; `zoom` es un departamento o «todo»;
    números con respaldo; con un dato en pantalla, `fuente`; ≥ 1.6 s de voz por capa; ≤ 2 por video."""
    es = escenas_de(g, "deptos")
    f = []
    if len(es) > DEPTOS_POR_VIDEO:
        f.append("H29 %d escenas deptos: van ≤ %d por video (o parte)" % (len(es), DEPTOS_POR_VIDEO))
    for i, e in es:
        fu = titulo_corto(f, "H29", i, e, valores, anios)
        capas = e.get("capas") if isinstance(e.get("capas"), list) else []
        if not DEPTOS_CAPAS[0] <= len(capas) <= DEPTOS_CAPAS[1]:
            f.append("H29 escena %d: %d capas; van %d–%d (una por frase de la voz)" % (i, len(capas), *DEPTOS_CAPAS))
        revisar_dice(f, "H29", i, capas, e.get("texto"), "capa")
        con_dato, hubo = False, False
        for k, c in enumerate(capas, 1):
            if not isinstance(c, dict):
                continue
            if set(c) - DEPTOS_CLAVES:
                f.append("H29 escena %d capa %d: clave desconocida %s (van: %s)" % (i, k, ", ".join(sorted(set(c) - DEPTOS_CLAVES)), ", ".join(sorted(DEPTOS_CLAVES))))
            ds = c.get("deptos")
            if ds is not None:
                ids = [VD.depto_id(x) for x in ds] if isinstance(ds, list) else [None]
                if not ds or len(ids) > DEPTOS_POR_CAPA or any(not x for x in ids) or len(set(ids)) != len(ids):
                    f.append("H29 escena %d capa %d: `deptos` son 1–%d departamentos que existen, sin repetir (p. ej. [\"Retalhuleu\"]); "
                             "llegó %s" % (i, k, DEPTOS_POR_CAPA, ds))
            if not (ds or c.get("zoom") or c.get("cifra")):
                f.append("H29 escena %d capa %d: la capa no muestra nada (deptos, zoom o cifra)" % (i, k))
            if c.get("arco") and not (ds and hubo):
                f.append("H29 escena %d capa %d: `arco` une el departamento de una capa anterior con el de esta: las dos llevan `deptos`" % (i, k))
            if c.get("onda") and not ds:
                f.append("H29 escena %d capa %d: `onda` sale del primer departamento de la capa: lleva `deptos`" % (i, k))
            if c.get("zoom") is not None and c.get("zoom") != "todo" and not VD.depto_id(c.get("zoom")):
                f.append("H29 escena %d capa %d: zoom «%s»; va un departamento o «todo»" % (i, k, c.get("zoom")))
            if c.get("etiqueta") and not ds:
                f.append("H29 escena %d capa %d: la etiqueta va en el rótulo del primer departamento de la capa" % (i, k))
            if c.get("rotulo") and not c.get("cifra"):
                f.append("H29 escena %d capa %d: `rotulo` acompaña a una `cifra`" % (i, k))
            for que, txt, tope in (("la cifra", c.get("cifra"), CIFRA_CARACTERES), ("el rótulo", c.get("rotulo"), VIAS_ROTULO),
                                   ("la etiqueta", c.get("etiqueta"), VIAS_ETIQUETA)):
                if txt is None:
                    continue
                if not isinstance(txt, str) or not txt.strip() or len(txt) > tope:
                    f.append("H29 escena %d capa %d: %s va de 1 a %d caracteres; llegó «%s»" % (i, k, que, tope, txt))
                else:
                    numeros_pantalla(f, "H29", i, "%s de la capa %d" % (que, k), txt, valores, anios)
            con_dato = con_dato or bool(c.get("cifra") or c.get("etiqueta"))
            hubo = hubo or bool(ds)
        if con_dato and not fu:
            f.append("H29 escena %d: con una cifra o una etiqueta en pantalla, la escena lleva `fuente`" % i)
        s_ = VD.segundos_voz(e.get("texto"))
        if capas and s_ < VIAS_CAPA_S * len(capas):
            f.append("H29 escena %d: %d capas en %.1f s de voz estimados: van ≥ %.1f s por capa" % (i, len(capas), s_, VIAS_CAPA_S))
    return f


def t_deptos(S, e, ps, pal, fin_voz, dur, g):
    """La escena deptos (video/deptos.html): cada capa entra cuando la voz dice su `dice`."""
    esc = escena_guion(S, g)
    t0 = t0_propio(esc)
    nombres = VD.nombres_depto()
    brutas = [c for c in esc.get("capas") or [] if isinstance(c, dict)]
    capas = []
    for c, t in zip(brutas, entradas_dice(brutas, pal, t0, dur)):
        ids = [x for x in (VD.depto_id(d) for d in c.get("deptos") or []) if x]
        capa = {"start": t, "ids": ids, "nombres": [nombres.get(x, x) for x in ids], "arco": bool(c.get("arco")), "onda": bool(c.get("onda")),
                "zoom": "todo" if c.get("zoom") == "todo" else VD.depto_id(c.get("zoom"))}
        for campo in ("etiqueta", "cifra", "rotulo"):
            if c.get(campo):
                capa[campo] = c[campo]
        capas.append(capa)
    S["pagina"] = "deptos"
    S["D"] = {"titulo": esc.get("titulo") or "", "capas": capas, "fuente": ("Fuente: " + esc["fuente"]) if esc.get("fuente") else None}
    S["T"] = {"ini": round(t0, 3)}
    return cerrar_escena(S, e, esc, ps, g, [(0.1, "entrada")] + [(c["start"], "nodo") for c in capas])


# ---------- escena pagina: la página real de un documento con la frase subrayada en su sitio (H30) ----------
PAGINA_FRASE, PAGINA_RENGLONES, PAGINAS_POR_VIDEO = (20, 240), 5, 2


def paginas_h():
    """Las páginas de documento del trabajo en curso (TRABAJO/paginas.json, las escribe `historia.py pagina`)."""
    ruta = os.path.join(TRABAJO_ACTUAL, "paginas.json") if TRABAJO_ACTUAL else None
    return leer(ruta) if ruta and os.path.isfile(ruta) else {}


def frase_en_pdf(pdf, frase):
    """(página, cajas [x, y, ancho, alto] en 0–1 de cada renglón, la frase como está en el PDF) de la primera página del
    PDF que trae la frase palabra por palabra (sin distinguir mayúsculas, tildes ni puntuación); None si no está."""
    toks = VD._plano(frase).split()
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    for p in range(1, (int(m.group(1)) if m else 0) + 1):
        x = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), pdf, "-"], capture_output=True, text=True).stdout
        pg = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', x)
        if not pg:
            continue
        pw, ph = float(pg.group(1)), float(pg.group(2))
        ws = [(float(a), float(b), float(c), float(d), html.unescape(t))
              for a, b, c, d, t in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', x)]
        plano = [(k, tk) for k, w in enumerate(ws) for tk in VD._plano(w[4]).split()]
        sec = [tk for _, tk in plano]
        j = next((j for j in range(len(sec) - len(toks) + 1) if sec[j:j + len(toks)] == toks), None)
        if j is None:
            continue
        usadas = [ws[k] for k in sorted({plano[q][0] for q in range(j, j + len(toks))})]
        renglones = []
        for w in usadas:   # un renglón = las palabras seguidas con (casi) la misma altura
            if renglones and abs(renglones[-1][-1][1] - w[1]) < 0.6 * (w[3] - w[1]):
                renglones[-1].append(w)
            else:
                renglones.append([w])
        cajas = [[round(min(w[0] for w in r) / pw, 4), round(min(w[1] for w in r) / ph, 4),
                  round((max(w[2] for w in r) - min(w[0] for w in r)) / pw, 4), round((max(w[3] for w in r) - min(w[1] for w in r)) / ph, 4)]
                 for r in renglones]
        return p, cajas, " ".join(w[4] for w in usadas)
    return None


def cmd_pagina(a):
    """La página de un PDF ya leído donde está una frase: la imagen de la página (TRABAJO/fotos/<id>.jpg) y la caja de
    cada renglón de la frase (TRABAJO/paginas.json), para la escena `pagina`. Necesita poppler (pdftotext, pdftoppm)."""
    trabajo = os.path.abspath(a.trabajo)
    if not re.fullmatch(r"[a-z0-9_-]+", a.id):
        return falla("--id en minúsculas, cifras y guiones (será fotos/<id>.jpg)")
    if not all(shutil.which(x) for x in ("pdfinfo", "pdftotext", "pdftoppm")):
        return falla("faltan pdfinfo, pdftotext y pdftoppm (brew install poppler)")
    pdf = a.pdf or (ruta_fuente(a.url) + ".pdf" if a.url else None)
    if not pdf or not os.path.isfile(pdf):
        return falla("no hay PDF: pasa --url de una fuente PDF ya leída con `leer` (o --pdf con su ruta)")
    r = frase_en_pdf(pdf, a.frase)
    if not r:
        return falla("el PDF no trae esa frase palabra por palabra: cópiala de la cita guardada (un trozo de 1–%d renglones)" % PAGINA_RENGLONES)
    pag, cajas, literal = r
    if len(cajas) > PAGINA_RENGLONES or not PAGINA_FRASE[0] <= len(literal) <= PAGINA_FRASE[1]:
        return falla("la frase ocupa %d renglones y %d caracteres: va un trozo de ≤ %d renglones y %d–%d caracteres"
                     % (len(cajas), len(literal), PAGINA_RENGLONES, *PAGINA_FRASE))
    os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
    base = os.path.join(trabajo, "fotos", "_pagina_" + a.id)
    subprocess.run(["pdftoppm", "-f", str(pag), "-l", str(pag), "-r", "120", "-jpeg", "-jpegopt", "quality=80", pdf, base], check=True)
    hechas = glob.glob(base + "*.jpg")
    if not hechas:
        return falla("pdftoppm no escribió la página %d" % pag)
    os.replace(hechas[0], os.path.join(trabajo, "fotos", a.id + ".jpg"))
    ruta = os.path.join(trabajo, "paginas.json")
    todo = leer(ruta) if os.path.isfile(ruta) else {}
    todo[a.id] = {"archivo": "fotos/%s.jpg" % a.id, "pagina": pag, "lineas": cajas, "frase": literal,
                  "fuente": a.fuente or (nombre_medio(a.url) if a.url else None), "url": a.url}
    escribir(ruta, todo)
    print("pagina %s · pág. %d · %d renglones · «%s» → %s" % (a.id, pag, len(cajas), literal, VD.rel(os.path.join(trabajo, "fotos", a.id + ".jpg"))))
    return 0


def revisar_pagina(g, valores=None, anios=None):
    """H30, la escena `pagina`: la página existe (historia.py pagina) con 1–5 renglones; título de un renglón; `fuente`
    (de quién es el documento); la voz lee la frase subrayada tal como está en el documento; ≤ 2 por video."""
    es = escenas_de(g, "pagina")
    f = []
    if len(es) > PAGINAS_POR_VIDEO:
        f.append("H30 %d escenas pagina: van ≤ %d por video (o parte)" % (len(es), PAGINAS_POR_VIDEO))
    pags = paginas_h()
    for i, e in es:
        fu = titulo_corto(f, "H30", i, e, valores, anios)
        if not fu:
            f.append("H30 escena %d: `fuente` dice de quién es el documento («CEUR, Universidad de San Carlos»)" % i)
        pg = pags.get(e.get("pagina"))
        if not pg:
            if TRABAJO_ACTUAL:
                f.append("H30 escena %d: pagina «%s» no existe: se arma con python3 scripts/historia.py pagina <TRABAJO> --id <id> "
                         "--url <fuente PDF ya leída> --frase «…»" % (i, e.get("pagina")))
            continue
        if not pg.get("lineas") or len(pg["lineas"]) > PAGINA_RENGLONES:
            f.append("H30 escena %d: la página «%s» tiene %d renglones subrayados; van 1–%d" % (i, e.get("pagina"), len(pg.get("lineas") or []), PAGINA_RENGLONES))
        if VD._plano(pg.get("frase") or "") not in VD._plano(e.get("texto") or ""):
            f.append("H30 escena %d: la voz no lee la frase subrayada tal como está en el documento: «%s»" % (i, pg.get("frase")))
    return f


def t_pagina(S, e, ps, pal, fin_voz, dur, g):
    """La escena pagina (video/pagina.html): el marcador recorre la frase mientras la voz la lee."""
    esc = escena_guion(S, g)
    pg = paginas_h().get(esc.get("pagina")) or {}
    t0 = t0_propio(esc)
    ws = [VD._plano(w["text"]) for w in pal]
    toks = VD._plano(pg.get("frase") or "").split()

    def buscar(trozo, desde=0):
        return next((j for j in range(desde, len(ws) - len(trozo) + 1) if ws[j:j + len(trozo)] == trozo), None) if trozo else None
    k1 = buscar(toks[:3])
    k2 = buscar(toks[-3:], k1 or 0)
    t_ini = max(t0 + 1.2, pal[k1]["start"]) if k1 is not None else max(t0 + 1.2, 0.35 * fin_voz)
    t_fin = pal[k2 + len(toks[-3:]) - 1]["end"] if k2 is not None else min(fin_voz, t_ini + 5.0)
    t_fin = min(max(t_fin, t_ini + 0.8), dur - 0.6)
    S["pagina"] = "pagina"
    fuente = "Documento: %s" % esc["fuente"] if esc.get("fuente") else "Documento"
    S["PG"] = {"foto": pg.get("archivo"), "lineas": pg.get("lineas") or [], "titulo": esc.get("titulo") or "",
               "fuente": fuente + (", pág. %s" % pg["pagina"] if pg.get("pagina") else ""), "t": [round(t_ini, 3), round(t_fin, 3)]}
    S["T"] = {"ini": round(t0, 3)}
    ev = [(0.1, "entrada"), (max(t0, t_ini - 1.1), "plano"), (t_ini, "nodo"), (t_fin, "nodo")]
    ev_, sfx = cerrar_escena(S, e, esc, ps, g, ev)
    return ev_, sfx + [(t_ini, "marcador")]


# ---------- escena cortina: antes y ahora con dos fotos reales (H31) ----------
CORTINA_ETIQUETA, CORTINA_DESDE = 14, 0.2


def revisar_cortina(g, valores=None, anios=None):
    """H31, la escena `cortina` (antes y ahora): dos fotos verificadas y distintas; dos etiquetas cortas (la de antes y
    la de ahora) con sus años en un hecho; título de un renglón; el `dice` (sin cifras) suena en la voz pasado el 20 %
    (la foto de antes se ve primero); ≤ 1 por video."""
    es = escenas_de(g, "cortina")
    f = []
    if len(es) > 1:
        f.append("H31 %d escenas cortina: va 1 por video (o parte)" % len(es))
    for i, e in es:
        titulo_corto(f, "H31", i, e, valores, anios)
        a, b = foto_de("H31", i, e.get("antes"), f, "antes"), foto_de("H31", i, e.get("ahora"), f, "ahora")
        if e.get("antes") == e.get("ahora") or (a and b and a.get("archivo") == b.get("archivo")):
            f.append("H31 escena %d: `antes` y `ahora` son dos fotos distintas del mismo lugar o de la misma cosa" % i)
        ets = e.get("etiquetas")
        if not (isinstance(ets, list) and len(ets) == 2 and all(isinstance(x, str) and 0 < len(x.strip()) <= CORTINA_ETIQUETA for x in ets)):
            f.append("H31 escena %d: `etiquetas` son dos textos de 1–%d caracteres: la de antes y la de ahora ([\"1976\", \"2021\"])" % (i, CORTINA_ETIQUETA))
        else:
            for x in ets:
                numeros_pantalla(f, "H31", i, "la etiqueta", x, valores, anios)
        voz, d = VD._plano(e.get("texto") or ""), VD._plano(e.get("dice") or "")
        if not d or re.search(r"\d", str(e.get("dice") or "")):
            f.append("H31 escena %d: `dice` es la palabra de la voz con la que cruza la cortina, sin cifras («después», «hoy»)" % i)
        elif voz.find(d) < 0:
            f.append("H31 escena %d: la voz no dice «%s»" % (i, e.get("dice")))
        elif voz.find(d) < CORTINA_DESDE * len(voz):
            f.append("H31 escena %d: la cortina cruza con «%s», antes del %d %% de la voz: primero se ve la foto de antes mientras la voz "
                     "la cuenta" % (i, e.get("dice"), CORTINA_DESDE * 100))
    return f


def t_cortina(S, e, ps, pal, fin_voz, dur, g):
    """La escena cortina (video/cortina.html): la cortina cruza cuando la voz dice el `dice`."""
    esc = escena_guion(S, g)
    a, b = fotos_h().get(esc.get("antes")) or {}, fotos_h().get(esc.get("ahora")) or {}
    t0 = t0_propio(esc)
    t = max(entradas_dice([esc], pal, t0, dur)[0], t0 + 1.2)
    creditos = " · ".join(dict.fromkeys(x for x in (a.get("credito"), b.get("credito")) if x))
    S["pagina"] = "cortina"
    S["CO"] = {"antes": a.get("archivo"), "ahora": b.get("archivo"), "etiquetas": list(esc.get("etiquetas") or ["", ""])[:2], "t": round(t, 3),
               "titulo": esc.get("titulo") or "", "pie": " · ".join(x for x in (creditos, ("Fuente: " + esc["fuente"]) if esc.get("fuente") else None) if x)}
    S["T"] = {"ini": round(t0, 3)}
    ev, sfx = cerrar_escena(S, e, esc, ps, g, [(0.1, "entrada"), (t, "plano")])
    return ev, sfx + [(t, "whip")]


# ---------- escena archivo: varias piezas reales en pantalla, una por frase (H32) ----------
ARCHIVO_ESTILOS = {"tira": (2, 5), "capas": (2, 5), "mesa": (3, 4)}   # estilo → cuántas piezas
ARCHIVO_FECHA, ARCHIVO_PIEZA_S, ARCHIVO_CUENTA, ARCHIVO_BARRAS, ARCHIVO_POR_VIDEO = 14, 2.2, (2, 24), (2, 6), 2
ARCHIVO_CONTEO_S = 1.5   # lo que tarda el conteo en llenar la rejilla


def revisar_archivo(g, valores=None, anios=None):
    """H32, la escena `archivo`: estilo tira | capas | mesa (piezas: cada una su foto verificada, distinta, con su `dice`
    en la voz y en orden; fecha y rótulo cortos), conteo (una foto, `cuenta` con respaldo, `unidad`, `dice`) o barras
    (una foto y 2–6 barras con valor con respaldo; `fuente`); números con respaldo; ≤ 2 por video."""
    es = escenas_de(g, "archivo")
    f = []
    if len(es) > ARCHIVO_POR_VIDEO:
        f.append("H32 %d escenas archivo: van ≤ %d por video (o parte)" % (len(es), ARCHIVO_POR_VIDEO))
    for i, e in es:
        est = e.get("estilo")
        fu = titulo_corto(f, "H32", i, e, valores, anios)
        if est in ARCHIVO_ESTILOS:
            ps = e.get("piezas") if isinstance(e.get("piezas"), list) else []
            if not ARCHIVO_ESTILOS[est][0] <= len(ps) <= ARCHIVO_ESTILOS[est][1]:
                f.append("H32 escena %d: %d piezas; en «%s» van %d–%d" % (i, len(ps), est, *ARCHIVO_ESTILOS[est]))
            revisar_dice(f, "H32", i, ps, e.get("texto"), "pieza")
            vistos = set()
            for k, p in enumerate(ps, 1):
                if not isinstance(p, dict):
                    continue
                if set(p) - {"dice", "foto", "fecha", "rotulo"}:
                    f.append("H32 escena %d pieza %d: clave desconocida %s (van dice, foto, fecha, rotulo)" % (i, k, ", ".join(sorted(set(p) - {"dice", "foto", "fecha", "rotulo"}))))
                rec = foto_de("H32", i, p.get("foto"), f, "la foto de la pieza %d" % k)
                if p.get("foto") in vistos or (rec and rec.get("archivo") in vistos):
                    f.append("H32 escena %d pieza %d: la foto «%s» ya salió en esta escena" % (i, k, p.get("foto")))
                vistos |= {p.get("foto"), (rec or {}).get("archivo")}
                for que, txt, tope in (("la fecha", p.get("fecha"), ARCHIVO_FECHA), ("el rótulo", p.get("rotulo"), VIAS_ROTULO)):
                    if txt is None:
                        continue
                    if not isinstance(txt, str) or not txt.strip() or len(txt) > tope:
                        f.append("H32 escena %d pieza %d: %s va de 1 a %d caracteres; llegó «%s»" % (i, k, que, tope, txt))
                    else:
                        numeros_pantalla(f, "H32", i, "%s de la pieza %d" % (que, k), txt, valores, anios)
            s_ = VD.segundos_voz(e.get("texto"))
            if ps and s_ < ARCHIVO_PIEZA_S * len(ps):
                f.append("H32 escena %d: %d piezas en %.1f s de voz estimados: van ≥ %.1f s por pieza" % (i, len(ps), s_, ARCHIVO_PIEZA_S))
        elif est == "conteo":
            foto_de("H32", i, e.get("foto"), f)
            c = e.get("cuenta")
            if not (isinstance(c, int) and not isinstance(c, bool) and ARCHIVO_CUENTA[0] <= c <= ARCHIVO_CUENTA[1]):
                f.append("H32 escena %d: `cuenta` es un entero de %d a %d (cuántas veces se repite la foto); llegó %s" % (i, *ARCHIVO_CUENTA, c))
            else:
                numeros_pantalla(f, "H32", i, "la cuenta", str(c), valores, anios)
            un = e.get("unidad")
            if not isinstance(un, str) or not un.strip() or len(un) > VIAS_ROTULO:
                f.append("H32 escena %d: `unidad` dice qué se cuenta, en 1–%d caracteres («pasos a desnivel en diez años»)" % (i, VIAS_ROTULO))
            else:
                numeros_pantalla(f, "H32", i, "la unidad", un, valores, anios)
            revisar_dice(f, "H32", i, [e], e.get("texto"), "el conteo", primera=False)
        elif est == "barras":
            foto_de("H32", i, e.get("foto"), f)
            bs = e.get("barras") if isinstance(e.get("barras"), list) else []
            if not ARCHIVO_BARRAS[0] <= len(bs) <= ARCHIVO_BARRAS[1]:
                f.append("H32 escena %d: %d barras; van %d–%d" % (i, len(bs), *ARCHIVO_BARRAS))
            revisar_dice(f, "H32", i, bs, e.get("texto"), "barra")
            for k, b in enumerate(bs, 1):
                if not isinstance(b, dict):
                    continue
                v = b.get("valor")
                if not (isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0):
                    f.append("H32 escena %d barra %d: `valor` es un número > 0" % (i, k))
                else:
                    numeros_pantalla(f, "H32", i, "el valor de la barra %d" % k, "%g" % v, valores, anios)
                et = b.get("etiqueta")
                if not isinstance(et, str) or not et.strip() or len(et) > 10:
                    f.append("H32 escena %d barra %d: etiqueta de 1–10 caracteres (el año o la categoría); llegó «%s»" % (i, k, et))
                if b.get("texto") is not None:
                    if not isinstance(b["texto"], str) or not 0 < len(b["texto"]) <= 12:
                        f.append("H32 escena %d barra %d: `texto` (cómo se escribe el valor) de 1–12 caracteres" % (i, k))
                    else:
                        numeros_pantalla(f, "H32", i, "el texto de la barra %d" % k, b["texto"], valores, anios)
            if not fu:
                f.append("H32 escena %d: unas barras llevan `fuente`" % i)
        else:
            f.append("H32 escena %d: estilo «%s» (tira = línea de tiempo con fotos · capas = recortes que caen uno sobre otro · mesa = las "
                     "pruebas sobre una mesa · conteo = una foto por cada cosa que se cuenta · barras = una serie sobre la foto)" % (i, est))
    return f


def con_miles(v):
    return "{:,}".format(int(v)) if float(v).is_integer() else "%g" % v


def t_archivo(S, e, ps, pal, fin_voz, dur, g):
    """La escena archivo (video/archivo.html): cada pieza, la cuenta o cada barra entra cuando la voz dice su `dice`."""
    esc = escena_guion(S, g)
    est = esc.get("estilo")
    t0 = t0_propio(esc)
    fotos = fotos_h()
    A = {"estilo": est, "titulo": esc.get("titulo") or ""}
    creditos, ev = [], [(0.1, "entrada")]
    if est in ARCHIVO_ESTILOS:
        brutas = [p for p in esc.get("piezas") or [] if isinstance(p, dict)]
        A["piezas"] = []
        for p, t in zip(brutas, entradas_dice(brutas, pal, t0, dur)):
            rec = fotos.get(p.get("foto")) or {}
            creditos.append(rec.get("credito"))
            A["piezas"].append({"start": t, "foto": rec.get("archivo"), "fecha": p.get("fecha") or "", "rotulo": p.get("rotulo") or ""})
        ev += [(p["start"], "plano") for p in A["piezas"]]
    elif est == "conteo":
        rec = fotos.get(esc.get("foto")) or {}
        creditos.append(rec.get("credito"))
        t = entradas_dice([esc], pal, t0, dur)[0]
        A.update(foto=rec.get("archivo"), n=esc.get("cuenta") or 0, t=t, dura=ARCHIVO_CONTEO_S, unidad=esc.get("unidad") or "")
        ev += [(t, "cifra"), (t + ARCHIVO_CONTEO_S, "cifra_fin")]
    else:
        rec = fotos.get(esc.get("foto")) or {}
        creditos.append(rec.get("credito"))
        brutas = [b for b in esc.get("barras") or [] if isinstance(b, dict)]
        vmax = max([b.get("valor") or 0 for b in brutas] or [1]) or 1
        A["foto"] = rec.get("archivo")
        A["barras"] = [{"start": t, "etiqueta": b.get("etiqueta") or "", "texto": b.get("texto") or con_miles(b.get("valor") or 0),
                        "alto": round((b.get("valor") or 0) / vmax, 4)} for b, t in zip(brutas, entradas_dice(brutas, pal, t0, dur))]
        ev += [(b["start"], "nodo") for b in A["barras"]]
    A["pie"] = " · ".join(list(dict.fromkeys(c for c in creditos if c)) + (["Fuente: " + esc["fuente"]] if esc.get("fuente") else []))
    S["pagina"], S["A"], S["T"] = "archivo", A, {"ini": round(t0, 3)}
    return cerrar_escena(S, e, esc, ps, g, ev)


# ---------- escena bandos: las personas toman partido en dos columnas (H33) ----------
BANDOS_PERSONAS, BANDOS_POR_LADO, BANDOS_NOMBRE, BANDOS_CIFRA, BANDOS_TEXTO, BANDOS_PERSONA_S = (2, 6), 3, 16, 8, 30, 1.6


def revisar_bandos(g, valores=None, anios=None):
    """H33, la escena `bandos`: dos lados con nombre corto (y cifra con respaldo); 2–6 personas, cada una un personaje
    del encuadre con retrato, en su lado (0 o 1; ≤ 3 por lado y al menos una en cada uno), con su `dice` en la voz y en
    orden; `umbral` opcional {dice, texto, marca, lleno, total} con sus números con respaldo; ≤ 1 por video."""
    es = escenas_de(g, "bandos")
    f = []
    if len(es) > 1:
        f.append("H33 %d escenas bandos: va 1 por video (o parte)" % len(es))
    enc = encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    pers = {VD._plano(c): p for p in enc.get("personajes") or [] if isinstance(p, dict) and p.get("nombre") for c in claves_personaje(p)}
    fotos = fotos_h()
    for i, e in es:
        titulo_corto(f, "H33", i, e, valores, anios)
        lados = e.get("lados") if isinstance(e.get("lados"), list) else []
        if len(lados) != 2 or not all(isinstance(x, dict) and isinstance(x.get("nombre"), str) and 0 < len(x["nombre"].strip()) <= BANDOS_NOMBRE for x in lados):
            f.append("H33 escena %d: `lados` son dos {nombre ≤ %d, cifra?} («A favor» y «En contra»)" % (i, BANDOS_NOMBRE))
        for x in lados:
            if isinstance(x, dict) and x.get("cifra") is not None:
                if not isinstance(x["cifra"], str) or not 0 < len(x["cifra"]) <= BANDOS_CIFRA:
                    f.append("H33 escena %d: la cifra de un lado va de 1 a %d caracteres" % (i, BANDOS_CIFRA))
                else:
                    numeros_pantalla(f, "H33", i, "la cifra de «%s»" % x.get("nombre"), x["cifra"], valores, anios)
        ps = e.get("personas") if isinstance(e.get("personas"), list) else []
        if not BANDOS_PERSONAS[0] <= len(ps) <= BANDOS_PERSONAS[1]:
            f.append("H33 escena %d: %d personas; van %d–%d" % (i, len(ps), *BANDOS_PERSONAS))
        revisar_dice(f, "H33", i, ps, e.get("texto"), "persona")
        por_lado = [0, 0]
        for k, p in enumerate(ps, 1):
            if not isinstance(p, dict):
                continue
            if p.get("lado") not in (0, 1) or isinstance(p.get("lado"), bool):
                f.append("H33 escena %d persona %d: `lado` es 0 o 1 (el primero o el segundo de `lados`)" % (i, k))
            else:
                por_lado[p["lado"]] += 1
            if enc:
                q = pers.get(VD._plano(p.get("personaje") or ""))
                if not q:
                    f.append("H33 escena %d: «%s» no es un personaje del encuadre" % (i, p.get("personaje")))
                elif not (es_persona(q) and retrato_de_personaje(q, fotos)):
                    f.append("H33 escena %d: «%s» no tiene retrato (H22): sin cara no entra a los bandos" % (i, q["nombre"]))
        if ps and (min(por_lado) < 1 or max(por_lado) > BANDOS_POR_LADO):
            f.append("H33 escena %d: %d y %d personas por lado: va al menos una en cada lado y ≤ %d por lado" % (i, *por_lado, BANDOS_POR_LADO))
        u = e.get("umbral")
        if u is not None:
            nums = [u.get(c) for c in ("marca", "lleno", "total")] if isinstance(u, dict) else []
            if not (isinstance(u, dict) and all(isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0 for x in nums)
                    and nums[0] <= nums[2] and nums[1] <= nums[2] and isinstance(u.get("texto"), str) and 0 < len(u["texto"]) <= BANDOS_TEXTO):
                f.append("H33 escena %d: umbral {dice, texto ≤ %d, marca (lo que hacía falta), lleno (lo alcanzado), total}" % (i, BANDOS_TEXTO))
            else:
                revisar_dice(f, "H33", i, [u], e.get("texto"), "el umbral", primera=False)
                for x in nums:
                    numeros_pantalla(f, "H33", i, "el umbral", "%g" % x, valores, anios)
                numeros_pantalla(f, "H33", i, "el texto del umbral", u["texto"], valores, anios)
        s_ = VD.segundos_voz(e.get("texto"))
        if ps and s_ < BANDOS_PERSONA_S * len(ps):
            f.append("H33 escena %d: %d personas en %.1f s de voz estimados: van ≥ %.1f s por persona" % (i, len(ps), s_, BANDOS_PERSONA_S))
    return f


def t_bandos(S, e, ps, pal, fin_voz, dur, g):
    """La escena bandos (video/bandos.html): cada persona entra a su columna cuando la voz la nombra."""
    esc = escena_guion(S, g)
    enc = encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    pers = {VD._plano(c): p for p in enc.get("personajes") or [] if isinstance(p, dict) and p.get("nombre") for c in claves_personaje(p)}
    fotos = fotos_h()
    t0 = t0_propio(esc)
    brutas = [p for p in esc.get("personas") or [] if isinstance(p, dict)]
    personas, creditos = [], []
    for p, t in zip(brutas, entradas_dice(brutas, pal, t0, dur)):
        q = pers.get(VD._plano(p.get("personaje") or "")) or {"nombre": p.get("personaje")}
        r = retrato_de_personaje(q, fotos) if es_persona(q) else None
        if r:
            creditos.append((fotos.get(r[2]) or {}).get("credito"))
        cargo = (q.get("cargo") or q.get("presentacion") or "").strip()
        personas.append({"start": t, "nombre": q["nombre"], "corto": p.get("corto") or (q.get("alias") or [q["nombre"]])[0], "cargo": cargo[:CARGO_MAX],
                         "lado": 1 if p.get("lado") == 1 else 0, "foto": r[0] if r else None, "foco": r[1] if r else None})
    lados = [{"nombre": (x or {}).get("nombre") or "", "cifra": (x or {}).get("cifra") or ""} for x in (list(esc.get("lados") or []) + [{}, {}])[:2]]
    B = {"titulo": esc.get("titulo") or "", "lados": lados, "personas": personas, "umbral": None,
         "pie": " · ".join(list(dict.fromkeys(c for c in creditos if c)) + (["Fuente: " + esc["fuente"]] if esc.get("fuente") else []))}
    ev = [(0.1, "entrada")] + [(p["start"], "persona") for p in personas]
    u = esc.get("umbral")
    if isinstance(u, dict):
        t_u = max(entradas_dice([u], pal, t0, dur)[0], (personas[-1]["start"] + 0.8) if personas else t0)
        B["umbral"] = {"start": round(min(t_u, dur - 1.0), 3), "texto": u.get("texto") or "", "marca": u.get("marca"), "lleno": u.get("lleno"), "total": u.get("total")}
        ev.append((B["umbral"]["start"], "cifra"))
    S["pagina"], S["B"], S["T"] = "bandos", B, {"ini": round(t0, 3)}
    return cerrar_escena(S, e, esc, ps, g, ev)


def lineas_archivo():
    """Para el digesto del guionista: las escenas que se dibujan sobre un archivo real (además de vias)."""
    return ["- lupa (UNA foto real que se interroga punto por punto; H28): foto (id verificado), titulo ≤ %d, estilo? puntos (la cámara "
            "se acerca y un velo apaga el resto: leer una foto de archivo) | pistas (las etiquetas se quedan: la anatomía de un objeto), "
            "puntos %d–%d [{dice, x, y (0–1: dónde está en la foto; MIRA la foto con Read antes de escribirlos), etiqueta ≤ %d}]; ≥ %.1f s "
            "de voz por punto. La etiqueta dice lo que SE VE; lo que no se ve en la foto va en la voz con su hecho"
            % (VIAS_TITULO, *LUPA_PUNTOS, LUPA_ETIQUETA, LUPA_PUNTO_S),
            "- deptos (el mapa de los 22 departamentos por capas; H29): titulo ≤ %d, capas %d–%d [{dice, deptos? [nombres] (se encienden; el "
            "primero lleva su rótulo, con etiqueta? ≤ %d), arco? true (un arco desde el departamento de la capa anterior: el viaje de algo), "
            "onda? true (un anillo sale del primer departamento y va encendiendo a los demás: un sismo, una noticia), cifra? ≤ %d con "
            "rotulo? ≤ %d, zoom? departamento | «todo»}], fuente (si hay cifra o etiqueta); ≥ %.1f s de voz por capa; ≤ %d por video. Para "
            "un solo lugar basta `depto` en una foto; para un recorrido corto, `ruta`"
            % (VIAS_TITULO, *DEPTOS_CAPAS, VIAS_ETIQUETA, CIFRA_CARACTERES, VIAS_ROTULO, VIAS_CAPA_S, DEPTOS_POR_VIDEO),
            "- pagina (la página REAL de un documento con la frase subrayada en su sitio; H30): pagina (id), titulo ≤ %d, fuente (de quién "
            "es el documento). Antes de escribirla, arma la página: python3 scripts/historia.py pagina <TRABAJO> --id <id> --url <la fuente "
            "PDF ya leída> --frase «el trozo literal, 1–%d renglones». La voz dice de quién es el documento y LEE la frase tal como está "
            "(como una cita); la cámara baja a ella y el marcador la recorre al paso de la voz. ≤ %d por video. Si la fuente no es un PDF, "
            "usa `cita` con `documento`" % (VIAS_TITULO, PAGINA_RENGLONES, PAGINAS_POR_VIDEO),
            "- cortina (ANTES Y AHORA con dos fotos reales del mismo lugar o de la misma cosa; H31): antes (id de foto), ahora (id de foto), "
            "etiquetas [«1976», «2021»] ≤ %d cada una, dice (la palabra de la voz con la que cruza la cortina, sin cifras, pasado el %d %% de "
            "la voz), titulo ≤ %d. Primero la voz cuenta la foto de antes; la cortina descubre la de ahora. 1 por video"
            % (CORTINA_ETIQUETA, CORTINA_DESDE * 100, VIAS_TITULO),
            "- archivo (varias piezas REALES en pantalla, una por frase; H32): estilo + titulo ≤ %d. tira | capas | mesa: piezas [{dice, foto "
            "(id; cada una distinta), fecha? ≤ %d, rotulo? ≤ %d}] (tira 2–5: una línea de tiempo con fotos, la tira corre a la que suena; "
            "capas 2–5: recortes o fotos que caen uno sobre otro; mesa 3–4: las pruebas del caso sobre una mesa, la cámara va de una a "
            "otra); ≥ %.1f s de voz por pieza. conteo: foto, cuenta (%d–%d, con respaldo), unidad ≤ %d («pasos a desnivel en diez años»), "
            "dice: la foto se repite una vez por cada cosa contada y el contador sube. barras: foto, barras %d–%d [{dice, etiqueta ≤ 10 "
            "(el año), valor (con respaldo), texto? («11,785»)}], fuente: la foto se apaga y suben las barras. ≤ %d por video"
            % (VIAS_TITULO, ARCHIVO_FECHA, VIAS_ROTULO, ARCHIVO_PIEZA_S, *ARCHIVO_CUENTA, VIAS_ROTULO, *ARCHIVO_BARRAS, ARCHIVO_POR_VIDEO),
            "- bandos (las personas TOMAN PARTIDO en dos columnas: quién votó a favor y quién en contra, quién firmó y quién no; H33): "
            "titulo ≤ %d, lados [{nombre ≤ %d, cifra? ≤ %d}, {…}], personas %d–%d [{personaje (del encuadre, con retrato), lado: 0|1, dice}] "
            "(≤ %d por lado, al menos una en cada uno), umbral? {dice, texto ≤ %d, marca, lleno, total} (la barra de lo alcanzado frente a "
            "lo que hacía falta), fuente. Cada quien en su lado por un HECHO verificado (su voto, su firma), nunca por una opinión. 1 por video"
            % (VIAS_TITULO, BANDOS_NOMBRE, BANDOS_CIFRA, *BANDOS_PERSONAS, BANDOS_POR_LADO, BANDOS_TEXTO)]


def tarjetas_de_escena(S, esc, pal, dur, g):
    """S.P de una escena: la tarjeta de cada persona que la voz nombra aquí por primera vez en el video (≤ 2, separadas
    TARJETA_SEPARA_S; en el gancho desde 1.0 s). Si la escena ya muestra a esa persona (una cara de su foto con su
    nombre), solo la franja del nombre y el sub-plano se acerca a su cara en ese instante."""
    enc = encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    pers = [p for p in enc.get("personajes") or [] if isinstance(p, dict) and (p.get("nombre") or "").strip() and es_persona(p)]
    if not pers:
        return []
    prim = primeras_menciones(g, pers)
    fotos = fotos_h()
    fo = fotos.get(esc.get("foto")) or {}
    ws = [VD._plano(w["text"]) for w in pal]
    out = []
    for p in pers:
        if prim.get(p["nombre"]) != S["n"] or len(out) >= TARJETAS_POR_ESCENA:
            continue
        k = None
        for c in claves_personaje(p):
            toks = c.split()
            k = next((j for j in range(len(ws) - len(toks) + 1) if ws[j:j + len(toks)] == toks), None)
            if k is not None:
                break
        if k is None:
            continue
        t = max(pal[k]["start"] - 0.12, 1.0 if S["n"] == 1 else 0.3)
        if out and t - out[-1]["start"] < TARJETA_SEPARA_S:
            t = out[-1]["start"] + TARJETA_SEPARA_S
        if t + 1.0 > dur:
            continue
        r = retrato_de_personaje(p, fotos)
        en_foto = next((i for i, f in enumerate(fo.get("focos") or []) if f.get("persona") and VD._plano(f["persona"]) in claves_personaje(p)), None)
        cargo = (p.get("cargo") or p.get("presentacion") or "").strip()
        out.append({"nombre": p["nombre"], "cargo": cargo[:CARGO_MAX + 12] if len(cargo) <= CARGO_MAX + 12 else cargo[:CARGO_MAX].rsplit(" ", 1)[0],
                    "foto": r[0] if r else None, "foco": r[1] if r else None, "solo": en_foto is not None or not r,
                    "start": round(t, 3), "fin": round(min(t + TARJETA_S, dur - 0.2), 3), "foco_en_escena": en_foto})
    return out


def sujeto_explica(nombre):
    """{nombre, cargo, foto, foco} del personaje que una escena explica pone sobre su lienzo (`sujeto`), o None si no es
    un personaje del encuadre con retrato."""
    enc = encuadre(TRABAJO_ACTUAL) if TRABAJO_ACTUAL else {}
    p = next((x for x in enc.get("personajes") or [] if isinstance(x, dict)
              and VD._plano(nombre) in claves_personaje(x)), None)
    r = retrato_de_personaje(p, fotos_h()) if p else None
    if not r or not r[0]:
        return None
    cargo = (p.get("cargo") or p.get("presentacion") or "").strip()
    return {"nombre": p["nombre"], "cargo": cargo if len(cargo) <= CARGO_MAX + 12 else cargo[:CARGO_MAX].rsplit(" ", 1)[0],
            "foto": r[0], "foco": r[1]}


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
              "conteo": vis.get("etiqueta") or "", "titular": linea, "kb": VD.KEN_BURNS[0], "depto": None, "icono": None,
              "encaje": fo.get("encaje"), "familia": e.get("familia")}   # «contener»: la página la muestra entera (más clara y casi sin Ken Burns); familia: resultado|escala con cifra → cifra héroe (m039)
    S["T"] = {"pant": {"texto": cin.get("pantalla"), "v": None, "desde": 0.0, "hasta": 0.4, "pulso": None}, "linea": linea,
              "fin": round(fin_voz, 3)}
    ev = [(0.0, "titular"), (0.4, "cifra_fin")] + [(w["start"], "linea_dicha") for w in linea if w.get("dicha")]
    if vis.get("foto") and fo.get("encaje") != "contener":   # el gancho: amplio y, a los ~3 s, cerca a la cara
        cortes = [round(pal[k + 1]["start"], 3) for k, x in enumerate(pal[:-1]) if x["text"].endswith((".", "?", "!", ":"))]
        S["N"]["planos"], S["N"]["focos"] = VD.planos_foto(fo.get("focos"), dur, cortes, [0.4])
        ev += [(x["t"], "plano") for x in S["N"]["planos"][1:]]
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
    lugar_chip = esc.get("lugar") or ""
    if fo.get("referencia") or re.search(r"referencia", esc.get("fecha") or "", re.I):
        lugar_chip = fo.get("lugar") or ""   # una foto de referencia: el lugar es el de la foto, no el del hecho
    N = {"modo": "noticia", "chip": {"b": esc.get("fecha") or "", "s": lugar_chip}, "foto": fo.get("archivo"),
         "credito": fo.get("credito"), "icono": esc.get("icono"), "depto": VD.depto_id(esc.get("depto")),
         "lugar": esc.get("lugar") if not fo.get("archivo") else None, "kb": VD.KEN_BURNS[(S["n"] - 1) % len(VD.KEN_BURNS)],
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
    # el subrayado: la palabra del titular con un año o una cifra, cuando la voz la dice (señalar lo importante)
    N["marcas"] = []
    for k_t, w_t in enumerate(N["titular"]):
        v_t = VD.valor_de(w_t["text"]) if re.search(r"\d", w_t["text"]) else None
        w_v = next((x for x in pal if v_t is not None and x.get("clave") == VD.clave(v_t)), None)
        if w_v and w_v["start"] > (N["titular"][-1]["start"] if N["titular"] else 0) + 0.3 \
                and abs(w_v["start"] - ((N["cifra"] or {}).get("start") or -9)) > 0.6:
            N["marcas"].append({"k": k_t, "t": round(w_v["start"], 3)})
            ev.append((w_v["start"], "marca"))
            sfx.append((w_v["start"], "marcador"))
            break
    # el mapa con ruta (2026-11-10): `ruta` = 2–4 departamentos por los que pasa lo que cuenta la escena (el puerto → la
    # aduana → la capital). El localizador se queda más y un trazo los une en orden. Cada uno, un lugar de un hecho de la
    # escena: lo comprueba el gate (H26).
    ruta = [VD.depto_id(x) for x in esc.get("ruta") or []]
    ruta = [x for x in ruta if x]
    if N["foto"] and len(ruta) >= 2 and not N.get("encaje"):
        largo = 1.4 + 0.9 * (len(ruta) - 1)
        # tras el titular si cabe; en una escena corta entra antes (nunca antes de que la foto esté puesta)
        d0 = round(max(t0 + 0.6, min((N["titular"][-1]["start"] if N["titular"] else t0) + 0.4, dur - largo - 0.5)), 3)
        if d0 + largo + 0.3 < dur:
            N["minimapa"] = {"depto": ruta[-1], "ruta": ruta, "desde": d0, "hasta": round(d0 + largo, 3)}
            ev += [(d0, "entrada")] + [(round(d0 + 0.5 + 0.9 * k, 3), "ruta") for k in range(1, len(ruta))]
    elif N["foto"] and N["depto"] and not N.get("encaje"):   # el localizador: dónde queda, 1.7 s tras entrar
        d0 = round(max(t0 + 0.9, (N["titular"][-1]["start"] if N["titular"] else t0) + 0.4), 3)
        if d0 + 2.0 < dur:
            N["minimapa"] = {"depto": N["depto"], "desde": d0, "hasta": round(d0 + 1.7, 3)}
            ev.append((d0, "entrada"))
    div = [fotos_h().get(x) or {} for x in (esc.get("dividida") or [])[:2]]
    if len(div) == 2 and all(d.get("archivo") for d in div):   # dos personas frente a frente: una foto por mitad
        N["dividida"] = [{"foto": d["archivo"], "focos": d.get("focos") or []} for d in div]
        N["foto"] = div[0]["archivo"]
        N["credito"] = " · ".join(dict.fromkeys(d.get("credito") or "" for d in div if d.get("credito")))
        evitar = [x for x in (cifra_t, (N["cifra"] or {}).get("start"), t0 + 0.1) if x is not None]
        N["planos"], _ = VD.planos_foto([{"x": 0.25, "y": 0.4, "w": 0.1, "h": 0.1}, {"x": 0.75, "y": 0.4, "w": 0.1, "h": 0.1}],
                                        dur, N["oraciones"], evitar)
        ev += [(x["t"], "plano") for x in N["planos"][1:]]
    elif N["foto"] and N.get("encaje") != "contener":   # sub-planos sobre las caras (V21), lejos de la cifra y del titular (V22)
        evitar = [x for x in (cifra_t, (N["cifra"] or {}).get("start"), t0 + 0.1) if x is not None]
        N["planos"], N["focos"] = VD.planos_foto(fo.get("focos"), dur, N["oraciones"], evitar)
        ev += [(x["t"], "plano") for x in N["planos"][1:]]
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
    if S["H"]["documento"]:
        # el documento entra como una hoja que se desliza sobre el escritorio («papel») y, al terminar la frase, el
        # sello con su fecha y su fuente («sello»): señala que lo leído está en un papel con fecha (H2: la cita guardada)
        sfx = [(t, k) for t, k in sfx if not (t <= VD.TRANSICION + 0.1 and k in ("whoosh", "impacto"))] + [(0.1, "papel")]
        fin_q = max([w["start"] + 0.45 for w in texto if w.get("dicha")] or [fin_voz - 0.6])
        t_s = round(min(max(fin_q + 0.2, 1.8), dur - 1.0), 3)
        sello = " · ".join(x for x in ((q.get("cuando") or ""), (esc.get("fuente") or q.get("autor") or "")) if x)
        if sello:
            if len(sello) > 26:   # un sello largo parte en dos renglones y pisa el membrete o la zona segura (V13): solo la fecha
                sello = q.get("cuando") or sello[:26]
            S["H"]["sello"] = {"texto": sello, "t": t_s}
            ev.append((t_s, "sello"))
            sfx.append((t_s, "sello"))
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
    ser = VD.serie_de(VD.estado(TRABAJO_ACTUAL)) if TRABAJO_ACTUAL else {}
    if tipo == "gancho" and ser.get("parte") and not S.get("chip"):   # /serie: «Parte N de M» desde el cuadro 0 (SE8)
        S["chip"] = {"texto": "Parte %d de %d" % (ser["parte"], ser.get("de") or ser["parte"]), "tono": "acento", "pos": "arriba", "desde": 0}
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
    if tipo == "explica" and (esc.get("sujeto") or "").strip():   # sobre quién actúa el mecanismo: su retrato toda la escena
        su = sujeto_explica(esc["sujeto"])
        if su:
            S["sujeto"] = su
    if tipo != "cierre":   # H22: la tarjeta de persona en la primera mención (y el sub-plano a su cara, un solo evento)
        P = tarjetas_de_escena(S, esc, pal, dur, g)
        if S.get("sujeto"):   # el retrato del sujeto ya nombra a esa persona: sin otra tarjeta encima
            P = [x for x in P if x["nombre"] != S["sujeto"]["nombre"]]
            # su tarjeta queda fija toda la escena (en una `continua` ya estaba: visible desde el cuadro 0)
            t0 = -1.0 if S.get("continua") else (S.get("T") or {}).get("ini", 0.3)
            P = [dict(S["sujeto"], solo=False, sujeto=True, start=round(t0, 3), fin=round(dur + 5, 3), foco_en_escena=None)] + P
        if P:
            S["personas"] = P
            ev += [(x["start"], "persona") for x in P if x["start"] > 0]
            N = S.get("N") or {}
            fijos = [(x["start"], x["foco_en_escena"]) for x in P if x["foco_en_escena"] is not None]
            if fijos and N.get("planos") and N.get("focos") and not N.get("dividida"):
                evitar = [x for x in ((N.get("cifra") or {}).get("start"),) if x is not None]
                N["planos"], N["focos"] = VD.planos_foto(N["focos"], dur, N.get("oraciones") or [], evitar, personas=fijos)
                ev = [(t, k) for t, k in ev if k != "plano"] + [(x["t"], "plano") for x in N["planos"][1:]]
    if S.get("transicion") and tipo != "cierre":
        if esc.get("giro"):
            S["transicion"] = VD.TRANSICIONES["giro"]
        elif S.get("seguida") and not rotulo_de(esc):
            S["transicion"] = VD.TRANSICIONES["seguida"]
        # (cámara quieta, 2026-11-06: ni whip ni empujes laterales por el año; queda la transición del tipo)
    return ev, sfx


leer_cambios = VD.leer_cambios


def aplicar_cambios(g, gan, cambios, trabajo=None):
    """VD.aplicar_cambios + m121: una escena cuya foto cambió (campo foto o cambio de tipo) rehace su chip con la foto
    nueva, salvo que el mismo arreglo dé la fecha: «De referencia» si la foto es de referencia; si el chip decía un año y la
    foto es de otro, «Foto de <año de la foto>». Así el chip de la foto anterior no miente sobre la nueva."""
    rc, msg, escenas = VD.aplicar_cambios(g, gan, cambios)
    if rc or not trabajo:
        return rc, msg, escenas
    for c in cambios:
        n = c.get("escena")
        if not isinstance(n, int) or not 1 <= n <= len(g.get("escenas") or []):
            continue
        cambia_foto = c.get("campo") == "foto" or ("tipo" in c and "foto" in c and "campo" not in c)
        da_fecha = c.get("campo") == "fecha" or "fecha" in c or any(x.get("escena") == n and x.get("campo") == "fecha" for x in cambios)
        e = g["escenas"][n - 1]
        if not cambia_foto or da_fecha or not e.get("foto"):
            continue
        ruta = os.path.join(trabajo, "fotos", "%s.json" % e["foto"])
        fo = leer(ruta) if os.path.exists(ruta) else {}
        chip, anio = (e.get("fecha") or "").strip(), str(fo.get("fecha") or "")[:4]
        nuevo = chip
        if fo.get("referencia"):
            nuevo = "De referencia"
        elif foto_de_archivo(fo) and (re.search(r"referencia", chip, re.I) or re.search(r"\b(1[5-9]|20)\d\d\b", chip)):
            # m147: una foto de archivo republicada lleva la fecha de la nota (2026), no la del hecho: «De archivo»
            nuevo = "De archivo"
        elif re.search(r"referencia", chip, re.I) and re.fullmatch(r"\d{4}", anio):   # la nueva sí es del hecho
            nuevo = "Foto de %s" % anio
        elif re.search(r"\b(1[5-9]|20)\d\d\b", chip) and re.fullmatch(r"\d{4}", anio) and anio not in chip:
            nuevo = "Foto de %s" % anio
        if nuevo != chip:
            e["fecha"] = nuevo
            print("aplicar: escena %d con la foto %s: el chip «%s» pasa a «%s» (m121)" % (n, e["foto"], chip, nuevo))
    return rc, msg, escenas


def correr_gates(trabajo):
    """narracion --check y guion --check sobre un TRABAJO: imprime sus FALLA y AVISO → 0 pasa · 1 alguno falla."""
    rc = 0
    for cmd in ("narracion", "guion"):
        r = subprocess.run([sys.executable, os.path.abspath(__file__), cmd, trabajo, "--check"], capture_output=True, text=True, cwd=RAIZ)
        for linea in (r.stdout + r.stderr).splitlines():
            if linea.startswith(("FALLA", "AVISO")):
                print("%s · %s" % (cmd, linea))
        rc = rc or (1 if r.returncode else 0)
    return rc


def cmd_probar(a):
    """El crítico prueba un arreglo ANTES de escribirlo: aplica los cambios a una copia del TRABAJO (sin audio ni video),
    con el mismo texto en la narración de corrido, la promesa y el candidato del gancho, y corre narracion --check y
    guion --check. El TRABAJO real no se toca. → 0 pasa · 1 el gate lo rechaza (imprime las fallas) · 2 cambio mal dado."""
    trabajo = os.path.abspath(a.trabajo)
    try:
        cambios = leer_cambios(a.cambios)
    except (OSError, ValueError) as ex:
        print("FALLA --cambios ilegible: %s" % ex)
        return 2
    tmp = os.path.join(os.path.dirname(trabajo), "_probar-%s-%d" % (os.path.basename(trabajo), os.getpid()))   # junto al TRABAJO: una parte de serie se mide contra sus hermanas (SE13, SE15, SE19)
    shutil.copytree(trabajo, tmp, ignore=shutil.ignore_patterns("audio", "salida", "revision", "clips*", "segs*", "hf", "tablero"))
    try:
        g = leer(os.path.join(tmp, "guion.json"))
        ruta_g = os.path.join(tmp, "ganchos.json")
        gan = leer(ruta_g) if os.path.exists(ruta_g) else None
        rc, msg, _ = aplicar_cambios(g, gan, cambios, tmp)
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
    """Aplica en el TRABAJO real un arreglo ya probado (los mismos cambios que probar): copia guion.json a
    guion.previo.json (y ganchos.json a ganchos.previo.json), aplica, corre narracion --check y guion --check (que reescribe
    locucion.json) y, si el gate lo rechaza, restaura las copias y vuelve a correr el gate. Lo usa el guionista para las
    faltas y mejoras del crítico que traen `cambios`, y para revertir una escena desde guion.previo.json.
    → 0 aplicado (última línea RETORNO {"escenas_cambiadas": [...]}) · 1 el gate lo rechaza (TRABAJO como estaba) · 2 cambio mal dado."""
    trabajo = os.path.abspath(a.trabajo)
    try:
        cambios = leer_cambios(a.cambios)
    except (OSError, ValueError) as ex:
        print("FALLA --cambios ilegible: %s" % ex)
        return 2
    ruta = os.path.join(trabajo, "guion.json")
    ruta_g = os.path.join(trabajo, "ganchos.json")
    g = leer(ruta)
    gan = leer(ruta_g) if os.path.exists(ruta_g) else None
    rc, msg, escenas = aplicar_cambios(g, gan, cambios, trabajo)
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
        correr_gates(trabajo)   # locucion.json vuelve a corresponder al guion restaurado
        print("aplicar: el gate lo rechaza; guion.json queda como estaba")
        return 1
    VD.renumerar_audio(trabajo, [c["insertar"] for c in cambios if "insertar" in c])   # m108: las voces siguen a su escena
    print("aplicar: %d cambio(s) en el TRABAJO · gate ok" % len(cambios))
    print("RETORNO %s" % json.dumps({"escenas_cambiadas": sorted(escenas)}, ensure_ascii=False))
    return 0


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
        fs = " · ".join("%s" % (f.get("medio") or FW.dominio(f.get("url"))) for f in h.get("fuentes") or [])
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
              ["- No afirma: %s" % "; ".join(H.get("no_afirma") or [])] + \
              (["", "## Premisas que la verificación tumbó (H34: quita el nombre de donde aparezca; la pregunta puede quedar sin él)"] +
               ["- %s: «%s» → «%s» (%s)" % (c["donde"], c["texto"], c["nombre"], c["motivo"]) for c in premisas_caidas(H, enc)]
               if premisas_caidas(H, enc) else []) + lineas_descartados(H) + \
              ["", "## Cronología verificada (id · fecha · estado — hecho [fuentes])"] + lineas_hechos(H) + \
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
        out += ["", "## Clases de fuente que cuentan", "- oficial: *.gob.gt, %s, %s" % (", ".join(sorted(FW.OFICIALES)), ", ".join(sorted(OTROS_OFICIALES))),
                "- medio (dominio → grupo): %s" % ", ".join("%s→%s" % kv for kv in sorted({**FW.MEDIOS, **INTERNACIONALES}.items())),
                "- academica: *.edu, %s · archivo: %s (Wayback cuenta como su original)" % (", ".join(sorted(ACADEMICAS)), ", ".join(sorted(ARCHIVOS))),
                "- Wikipedia NO cuenta: úsala para llegar a sus referencias."]
        print("\n".join(out))
        return 0
    H = historia_de(trabajo)
    if a.para == "oyente":
        return digesto_oyente(trabajo, H)
    rec_g = st.get("ganchos_recientes") or {}
    prot = protagonistas(trabajo)
    vet_d = nombres_vetados(H)
    base = ["# Historia · %s (paleta %s, música %s)" % (st.get("tema"), st["paleta"], st["musica"]), "",
            "- Pregunta: %s · arco: %s" % (H.get("pregunta"), H.get("arco")),
            "- Protagonista: %s" % (" / ".join(H.get("protagonista") or encuadre(trabajo).get("protagonista") or []) or "FALTA en el encuadre")] + \
        lineas_encuadre(H, enc) + \
        ["- Revelaciones (lo que el video PAGA: el gancho no las adelanta —H13 veta sus números—, la promesa paga una "
         "(promesa.revela: 1, 2…) y la escena del pago la cuenta con sus palabras (H14)):"] + \
        (["  R%d. %s" % (k, r) for k, r in enumerate(H.get("revelaciones") or encuadre(trabajo).get("revelaciones") or [], 1)]
         or ["  (el encuadre no trae revelaciones: H13 y H14 no corren)"]) + \
        ["- No afirma: %s" % "; ".join(H.get("no_afirma") or [])] + lineas_descartados(H) + \
        ["", "## Cronología verificada (id · fecha · estado — hecho [fuentes])"] + \
        lineas_hechos(H) + (["", "## Conflictos de fecha"] + ["- %s y %s" % tuple(x) for x in H["conflictos"]] if H.get("conflictos") else []) + \
        ["", "## Cifras (id · texto · valor)"] + ["- %s · %s · %s %s (%s)" % (c["id"], c.get("texto"), c["valor"], c.get("unidad", ""), c.get("anio") or "")
                                                for c in H.get("cifras") or []] + \
        ["", "## Citas literales (id · quién · cuándo — frase)"] + ["- %s · %s%s · %s%s — «%s»" % (q["id"], q.get("autor"), ", " + q["cargo"] if q.get("cargo") else "",
                                                                    q.get("cuando"), " · documento" if q.get("documento") else "", q.get("texto"))
                                                                    for q in H.get("citas") or []] + \
        ["", "## Fotos verificadas (id · qué muestra · crédito · origen; PROTAGONISTA = la que puede abrir el gancho, H12)"] + \
        ["- %s · %s · %s (%s)%s%s" % (k, f.get("descripcion"), f.get("credito"), f.get("origen"),
                                      " · %s %s" % (f.get("fecha") or "", f.get("lugar") or "") if f.get("fecha") or f.get("lugar") else "",
                                      " · PROTAGONISTA" if es_protagonista(f, prot) else "") +
         ("".join(" · ⚠ nombra un descartado («%s»)" % n for n in vet_d if _contiene(VD._plano("%s %s" % (f.get("lugar") or "", f.get("descripcion") or "")), n)))
         for k, f in sorted((H.get("fotos") or {}).items())] + \
        (["", "## Casos (estado a la fecha de consulta)"] + ["- %s: %s (consultado %s)%s" % (x.get("persona"), x.get("estado_actual"), x.get("fecha_consulta"),
                                                            " · sentencia firme" if x.get("sentencia_firme") else "") for x in H.get("casos") or []]
         if H.get("casos") else [])
    ser_d = VD.serie_de(st)
    if (ser_d.get("parte") or 0) > 1:   # SE15–SE16: lo que ya contaron las partes anteriores de la serie
        import serie as SR   # noqa: E402  (serie importa historia: aquí, no arriba)
        ya = SR.ya_contado(trabajo, ser_d["parte"])["ids"]
        base = [re.sub(r"^- ([a-z]{2,4}-[hcq]\d+) · ", lambda m: "- %s · [YA CONTADO EN P%d] " % (m.group(1), ya[m.group(1)])
                       if m.group(1) in ya else m.group(0), x) for x in base]
        base += SR.lineas_ya_contado(trabajo, ser_d["parte"])
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
                      "- La voz no abre con «Esta es la historia de…», «Te cuento…», «En el año…» ni con contexto: abre con el momento más fuerte.",
                      "", "## Rendimiento real (TikTok, YouTube; /analyze-improve)"] + VD.lineas_rendimiento_real()
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
                  *lineas_vias(),
                  *lineas_archivo(),
                  *VD.lineas_animaciones(st.get("animaciones_recientes") or []),
                  "- Cierre: rotulo («Lo que dejó»…), resumen %d–%d líneas ≤ %d, texto, tipo remate, forma LEGADO (lo normal): lo que la gente hace "
                  "HOY con lo que la historia dejó («Hoy, sus hijos y sus nietos siguen tomando Incaparina»); consecuencia {quien (gente: nietos, "
                  "clientes, trabajadores…), verbo (en presente)}, ≤ 1 cifra, sin «según» (H9). Forma consecuencia (con mecanismo) si la historia "
                  "termina mal. NEUTRO = nadie hace nada («la marca sigue», «la receta cambió», un resumen): bloquea en H-C6. La emoción la pone "
                  "el hecho, no los adjetivos"
                  % (*VD.RESUMEN_LINEAS, VD.RESUMEN_CARACTERES), "", "## Promesas recientes (P3)"] + VD.lineas_promesas(st["promesas_recientes"] if "promesas_recientes" in st else VD.promesas_recientes(st["slug"])) + \
                  ["", "## Frases ya usadas (C11)"] + VD.frases_usadas(st["slug"]) + frases_historias(st["slug"])
    print("\n".join(out))
    return 0


def g_actual(trabajo):
    ruta = os.path.join(trabajo, "guion.json")
    return leer(ruta) if os.path.exists(ruta) else {}


def narracion_corrida(trabajo, g):
    """La voz de corrido por acto, en palabras (locucion.json) si ya pasó el gate; si no, guion.narracion."""
    ruta = os.path.join(trabajo, "locucion.json")
    return VD.narracion_corrida(g, leer(ruta) if os.path.exists(ruta) else None)


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
    fuentes ni ids: el oyente ingenuo no sabe nada más (video.lineas_oyente, el mismo digesto de /video)."""
    ruta = os.path.join(trabajo, "locucion.json")
    if not os.path.exists(ruta):
        return falla("falta locucion.json: corre python3 scripts/historia.py guion %s --check" % VD.rel(trabajo))
    citas = {q["id"]: q for q in H.get("citas") or []}
    aplicar_extension(trabajo)
    print("\n".join(VD.lineas_oyente(leer(os.path.join(trabajo, "guion.json")), leer(ruta), lambda e: pantalla_de(e, citas))))
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
    elif t == "red":
        partes = [e.get("titulo"), "Según la acusación" if e.get("atribuida") else None] + \
                 ["%s (nivel %s)" % (nd.get("personaje"), nd.get("nivel")) for nd in e.get("nodos") or []] + \
                 ["%s %s %s" % (ar.get("de"), ar.get("rel") or "→", ar.get("a")) for ar in e.get("aristas") or []]
    elif t == "deptos":
        partes = [e.get("titulo")] + [" ".join(str(x) for x in (", ".join(c.get("deptos") or []), c.get("etiqueta"), c.get("cifra"), c.get("rotulo")) if x)
                                      for c in e.get("capas") or [] if isinstance(c, dict)]
    elif t == "pagina":
        partes = [e.get("titulo"), "Documento: %s" % (e.get("fuente") or ""), "«%s» (subrayado)" % ((paginas_h().get(e.get("pagina")) or {}).get("frase") or "")]
    elif t == "cortina":
        partes = [e.get("titulo")] + [str(x) for x in e.get("etiquetas") or []]
    elif t == "archivo":
        partes = [e.get("titulo"), e.get("unidad"), str(e["cuenta"]) if e.get("cuenta") else None] + \
                 [" ".join(str(x) for x in (p.get("fecha"), p.get("rotulo"), p.get("etiqueta"), p.get("texto") or p.get("valor")) if x)
                  for p in (e.get("piezas") or []) + (e.get("barras") or []) if isinstance(p, dict)]
    elif t == "bandos":
        partes = [e.get("titulo")] + [" ".join(str(x) for x in (l.get("cifra"), l.get("nombre")) if x) for l in e.get("lados") or [] if isinstance(l, dict)] + \
                 ["%s → lado %s" % (p.get("personaje"), p.get("lado")) for p in e.get("personas") or [] if isinstance(p, dict)] + [(e.get("umbral") or {}).get("texto")]
    elif t == "lupa":
        partes = [e.get("titulo")] + [p.get("etiqueta") for p in e.get("puntos") or [] if isinstance(p, dict)]
    elif t == "vias":
        lugares = (vias_de(e.get("red_vial")) or {}).get("lugares") or {}
        partes = [e.get("titulo")] + [" ".join(str(x) for x in ((lugares.get(c.get("lugar")) or {}).get("nombre"), c.get("etiqueta"), c.get("cifra"),
                                                                 c.get("rotulo")) if x) for c in e.get("capas") or [] if isinstance(c, dict)]
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
def cmd_fotos_contacto(a, sin_repetidas=True):
    """Hoja con todas las fotos del trabajo (para el QA de contenido del coordinador: sin víctimas ni menores).
    sin_repetidas: una imagen bajada con dos ids (mismo contenido) sale una sola vez."""
    trabajo = os.path.abspath(a.trabajo)
    fotos = sorted(glob.glob(os.path.join(trabajo, "fotos", "*.jpg")))
    if sin_repetidas:
        vistos, unicas = set(), []
        for f in fotos:
            h = hashlib.sha1(open(f, "rb").read()).hexdigest()
            if h not in vistos:
                vistos.add(h)
                unicas.append(f)
        if len(unicas) < len(fotos):
            print("AVISO %d foto(s) repetida(s) (la misma imagen con otro id): salen una vez" % (len(fotos) - len(unicas)))
        fotos = unicas
    if not fotos:
        print("sin fotos")
        return 0
    cols = min(3, len(fotos))
    entradas = sum([["-i", f] for f in fotos], [])
    fc = "".join("[%d:v]scale=480:300:force_original_aspect_ratio=decrease,pad=480:300:(ow-iw)/2:(oh-ih)/2:color=white,"
                 "drawbox=x=0:y=0:w=480:h=300:color=black@0:t=1[f%d];" % (k, k) for k in range(len(fotos)))
    while len(fotos) % cols:
        fc += "color=white:s=480x300:d=1[f%d];" % len(fotos)
        fotos.append(None)
    filas = len(fotos) // cols
    fc += "".join("[f%d]" % k for k in range(len(fotos))) + "xstack=inputs=%d:layout=%s[o]" % (
        len(fotos), "|".join("%d_%d" % (480 * (k % cols), 300 * (k // cols)) for k in range(len(fotos))))
    out = os.path.join(trabajo, "fotos", "contacto.png")
    if len(fotos) == 1:
        VD.ff(*entradas, "-vf", "scale=480:-2", "-frames:v", "1", out)
    else:
        VD.ff(*entradas, "-filter_complex", fc, "-map", "[o]", "-frames:v", "1", out)
    print("hoja de fotos (%d, en orden: %s) → %s" % (len([f for f in fotos if f]), ", ".join(os.path.basename(f)[:-4] for f in fotos if f), VD.rel(out)))
    # m029: lo que dice cada foto, en el orden de la hoja, para cotejar la descripción y el chip con lo que se ve
    for k, f in enumerate(fotos):
        if not f:
            continue
        meta = f[:-4] + ".json"
        d = json.load(open(meta, encoding="utf-8")) if os.path.exists(meta) else {}
        chip = " · ".join(x for x in (d.get("lugar"), str(d.get("fecha") or "")[:4]) if x)
        print("  fila %d col %d · %-9s · %s%s · %s" % (k // cols + 1, k % cols + 1, os.path.basename(f)[:-4],
              (d.get("descripcion") or "sin descripción")[:80], " · chip «%s»" % chip if chip else "", d.get("credito") or ""))
    return 0


# ---------- entrega: historias/<fecha>-<slug>/ ----------
SALIDA_ENTREGA = ("video.mp4", "video_4x5.mp4", "subtitulos.srt", "caption.md", "portada.png")


def fotos_de_archivo(e):
    """Las fotos que usa una escena con archivos reales fuera de su `foto`: las dos de una cortina y las piezas de un archivo."""
    return [x for x in (e.get("antes"), e.get("ahora")) if x] + [p.get("foto") for p in e.get("piezas") or [] if isinstance(p, dict) and p.get("foto")]


def fotos_de_escena(e):
    return [x for x in (e.get("foto"), e.get("retrato"), (e.get("visual_datos") or {}).get("foto")) if x] + list(e.get("dividida") or []) + \
        fotos_de_archivo(e)


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
    if os.path.exists(os.path.join(sal, VD.MESA_SIN_RENDER)) and not a.salida:
        return falla("este video es un doble sin render (MESA_RENDER=0, de maqueta): vuelve a grabar sin esa variable antes de entregar")
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
    escenas_g, fotos = g.get("escenas") or [], con_alias(H.get("fotos"))
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
        "gancho": {k: e1.get(k) for k in ("familia", "visual", "pantalla", "linea")}, "promesa": g.get("promesa"), "bisagra": g.get("bisagra"),
        "escenas": escenas, "cierre": g.get("cierre"), "caption": g.get("caption")}
    VD.con_eleccion(entrega, trabajo, g)   # quién eligió el gancho y el cierre, y qué recomendaba el crítico
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
            medio = {f["url"]: f.get("medio") or FW.dominio(f["url"]) for f in x.get("fuentes") or [] if f.get("url")}
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
        medios = ", ".join(dict.fromkeys(f.get("medio") or FW.dominio(f.get("url")) for f in x.get("fuentes") or []))
        quien = "%s: «%s»" % (x.get("autor"), x.get("texto")) if x.get("autor") else x.get("texto")
        estado = "confirmado" if x.get("estado") == "confirmado" else "una fuente (%s)" % (medio_de(x) or "?") if x.get("estado") == "una_fuente" \
            else "en disputa%s" % (" — %s" % x["nota"] if x.get("nota") else "")
        L.append("- **%s** · %s · %s · %s" % (x.get("fecha") or x.get("cuando") or "s. f.", quien, estado, medios))
    if H.get("conflictos"):
        L += ["", "## Fechas en conflicto", ""] + ["- %s y %s: el mismo hecho con años distintos" % tuple(c) for c in H["conflictos"]]
    return "\n".join(L) + "\n"


REENVIO = ("voz", "voz-falsa", "descargar", "partir", "escuchar", "grabar", "montar", "revisar", "plano")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "voz" and not any(x in sys.argv for x in ("-h", "--help")):
        import serie as SR   # noqa: E402  SE17: una parte de serie no se graba antes de revisar la serie completa
        bloqueo = SR.voz_permitida(os.path.abspath(sys.argv[2]))
        if bloqueo:
            return falla(bloqueo)
    if len(sys.argv) > 1 and sys.argv[1] == "producir":   # la cadena de producción común y reanudable (scripts/producir.py)
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "producir.py")] + sys.argv[2:], cwd=RAIZ).returncode
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
    q.add_argument("--realizacion", choices=VD.REALIZACIONES, help="quién dibuja el video: mesa (la mesa de archivo en HyperFrames; por defecto) o propio")
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
    q.add_argument("--retrato-evidencia", help="con --retrato-de: el pie, la categoría de Commons o el título que nombra a la persona (H21)")
    q.add_argument("--proceso", help="m122: la foto muestra a una persona detenida, esposada o en audiencia: su nombre. Solo podrá ir en "
                   "una escena cuya voz la nombre (H7c)")
    x = q.add_mutually_exclusive_group()
    x.add_argument("--referencia", action="store_true", help="la foto no es del hecho sino de referencia (el lugar, la institución, la persona, "
                   "el producto o la época): el crédito dice «Foto de referencia: …»")
    x.add_argument("--protagonista", action="store_true", help="la foto muestra al protagonista del encuadre (el producto, el edificio, la persona): "
                   "H12 la exige en el gancho")
    q.add_argument("--extmetadata", help="pruebas: extmetadata de Commons guardado (solo comprueba la licencia, sin red)")
    q = sub.add_parser("focos", help="las caras de cada foto (Vision de macOS) y de quién es cada una: sub-planos, recorte y tarjeta de persona")
    q.add_argument("trabajo")
    q.add_argument("--foto", help="una sola foto (<eje>-fNN)")
    q.add_argument("--cara", type=int, help="con --foto: la cara N (de izquierda a derecha)")
    q.add_argument("--persona", help="con --cara: de quién es (el nombre del personaje del encuadre)")
    q.add_argument("--evidencia", help="con --persona: el pie o la categoría que la nombra")
    q.add_argument("--quitar", action="store_true", help="con --cara: no es una cara (o no sirve)")
    q.add_argument("--foco", help="x,y,w,h (0–1): un foco a mano (un objeto, un cartel)")
    q.add_argument("--que", choices=["rostro", "objeto", "texto"], help="con --foco")
    q.add_argument("--rehacer", action="store_true", help="vuelve a detectar las caras aunque ya tenga focos")
    q = sub.add_parser("hechos")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true")
    q.add_argument("--reclasificar", action="store_true", help="propone una_fuente para cada en_disputa de un solo grupo sin discrepancia en la nota")
    q.add_argument("--aplicar", action="store_true", help="con --reclasificar: escribe los cambios y repite el check")
    q.add_argument("--eje")
    sub.add_parser("consolidar").add_argument("trabajo")
    q = sub.add_parser("premisas", help="H34: lo que el encuadre da por hecho y la verificación descartó")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
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
    x.add_argument("--opciones", action="store_true")
    x.add_argument("--elegir")
    q.add_argument("--segundo")
    q.add_argument("--por", choices=VD.ELEGIDO_POR, help="quién eligió el gancho (video.py ganchos --help)")
    q = sub.add_parser("cierres")
    q.add_argument("trabajo")
    VD.agregar_args_cierres(q)
    sub.add_parser("tarjetas").add_argument("trabajo")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q = sub.add_parser("probar", help="el crítico prueba un arreglo contra el gate en una copia, sin tocar el TRABAJO")
    q.add_argument("trabajo")
    q.add_argument("--cambios", required=True, help='JSON o archivo: [{"escena": N, "texto": "…"}, {"escena": N, "campo": "fecha", '
                   '"valor": "…"}, {"promesa": "…", "forma"?}, {"bisagra": "…", "forma"?, "en"?, "pago"?}, {"cierre": "…"}]')
    q = sub.add_parser("aplicar", help="aplica en el TRABAJO un arreglo ya probado (los mismos cambios que probar) y corre el gate")
    q.add_argument("trabajo")
    q.add_argument("--cambios", required=True, help="los mismos cambios que probar (JSON o archivo)")
    sub.add_parser("tiempos").add_argument("trabajo")
    sub.add_parser("fotos-contacto").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida", help="otra carpeta (pruebas, maqueta o voz falsa)")
    q = sub.add_parser("pagina", help="la página de un PDF ya leído donde está una frase (imagen + caja de cada renglón) para la escena pagina")
    q.add_argument("trabajo")
    q.add_argument("--id", required=True, help="id de la página (será fotos/<id>.jpg)")
    q.add_argument("--url", help="la fuente PDF ya leída con `leer`")
    q.add_argument("--pdf", help="o la ruta del PDF")
    q.add_argument("--frase", required=True, help="el trozo literal que se subraya (1–5 renglones)")
    q.add_argument("--fuente", help="de quién es el documento (por defecto, el medio de la url)")
    for nombre in REENVIO:
        sub.add_parser(nombre, help="→ scripts/video.py %s" % nombre)
    a = p.parse_args()
    if getattr(a, "trabajo", None) and a.cmd != "preparar":
        aplicar_formato(os.path.abspath(a.trabajo))
    return {"preparar": cmd_preparar, "leer": cmd_leer, "commons": cmd_commons, "foto": cmd_foto, "hechos": cmd_hechos,
            "consolidar": cmd_consolidar, "premisas": cmd_premisas, "encuadre": cmd_encuadre, "narracion": cmd_narracion, "digesto": cmd_digesto,
            "ganchos": cmd_ganchos, "cierres": cmd_cierres, "tarjetas": cmd_tarjetas, "guion": cmd_guion, "probar": cmd_probar, "aplicar": cmd_aplicar, "tiempos": cmd_tiempos,
            "fotos-contacto": cmd_fotos_contacto, "entregar": cmd_entregar, "focos": cmd_focos, "pagina": cmd_pagina}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
