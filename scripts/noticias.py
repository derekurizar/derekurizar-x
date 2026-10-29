#!/usr/bin/env python3
"""/noticias: las noticias del día en Guatemala → video vertical 1080×1920 de ≤ 70 s (TikTok / Reels / Shorts) y 4:5.

Este script hace lo propio del noticiero (el estado del trabajo, el gate del guion N3–N6 y N8, los tiempos de cada
escena y las fotos de la maqueta) y escribe el MISMO trabajo que /video (video.json, locucion.json, audio/,
escenas.json, clips/, salida/): la voz, la grabación, el montaje con música y efectos y la revisión salen de
scripts/video.py sin cambios (los subcomandos de abajo marcados «→ video.py» solo los reenvían). Guía:
referencias/flujo-noticias.md.

Subcomandos (TRABAJO = sesiones/noticias-<fecha>/):
  preparar [--fecha YYYY-MM-DD] [--trabajo DIR] [--paleta P] [--musica ID] [--fixture]   crea TRABAJO y video.json
        (la paleta del día, en ciclo de 8 por fecha, y su música: las 2 pistas de la paleta se alternan); --fixture copia guion.json y noticias.json de sesiones/_fixture_noticias y dibuja sus fotos
  guion TRABAJO --check        gate N3–N6, N8 (+ V3 cifras en palabras) sobre guion.json y noticias.json → locucion.json
  tiempos TRABAJO              atempo 1.1, alineación por palabra (V6), eventos y efectos de cada escena, V10 → escenas.json
  fotos-fixture TRABAJO        fotos de ejemplo (fractales de ffmpeg, sin web) en TRABAJO/fotos/ para la maqueta
  leer URL [--buscar CITA]     baja una nota y guarda su texto y metadatos (fecha, og:image) en sesiones/_descargas/noticias/
  candidatas TRABAJO --check [--seccion pol|seg|eco]   N1 sobre candidatas_<sec>.json de los rastreadores
  verificacion TRABAJO --check [--id ID]   N2 (fuentes independientes, citas en el texto guardado, fecha) y N7 (foto)
  foto TRABAJO --id ID [--url U --credito C --origen oficial|medio|referencia]   la foto (oficial → og:image del medio → una de referencia que se pasa con --url) en fotos/<id>.jpg
  consolidar TRABAJO           verificacion_*.json → noticias.json
  digesto TRABAJO --para rastreador | verificador --id ID | editor   insumo compacto de cada agente
  fotos-contacto TRABAJO       fotos/contacto.png con todas las fotos (QA de contenido)
  entregar TRABAJO [--salida DIR]   copia a noticias/<fecha>/ el 9:16, el 4:5, caption.md, subtítulos, portadas, guion.json
        de entrega y fuentes.md (las fotos no: son de terceros); exige la voz de ElevenLabs (audio/creditos.json) salvo con --salida
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
from html.parser import HTMLParser

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402
import video as VD  # noqa: E402

FIXTURE = os.path.join(RAIZ, "sesiones", "_fixture_noticias")
# una paleta por día (decisión del usuario, 2026-10-23): el ciclo de las 8 por fecha, así dos días seguidos nunca
# repiten color; la música va con la paleta (2 pistas cada una: suena distinto cada día). Oscuras y claras alternadas
PALETAS_CICLO = ("obsidiana", "cielo", "jade", "maiz", "cacao", "atitlan", "terracota", "jacaranda")
OBJETIVO_S, DURACION_MIN_S, DURACION_MAX_S = 60, 45, 70   # el usuario: «que no dure más de 70 segundos»
NOTICIAS = (3, 4)                # noticias por video (más el gancho, que adelanta la primera)
SECCIONES_MIN = 2
# voz ya en palabras, en caracteres (≈ 15.5 por segundo a 1.1×): gancho ≤ 4 s; noticia ≈ 10–16 s; breve ≈ 5–8 s
CARACTERES = {"titular": (25, 62), "noticia": (140, 235), "breve": (60, 115), "cierre": (30, 85)}
TITULAR_PALABRAS, TITULAR_CARACTERES = 9, 60
SECCION_CARACTERES, FUENTE_CARACTERES, CREDITO_CARACTERES = 18, 44, 44
# cada noticia lleva foto (N7): la de la noticia (oficial → og:image del medio) o, si no hay, una de referencia de la
# institución, el lugar o la persona, que en pantalla dice que lo es
CREDITO_PREFIJO = {"oficial": "Foto: ", "medio": "Foto: ", "referencia": "Foto de referencia: "}
CIFRA_CARACTERES, ETIQUETA_CARACTERES = 18, 30
RESUMEN_LINEAS, RESUMEN_CARACTERES, FINAL_PALABRAS = (3, 4), 32, 10
ESTADOS_PUBLICABLES = ("confirmada", "en_desarrollo")
# presunción de inocencia: sin sentencia firme no se dice que alguien cometió el delito
VETADAS = re.compile(r"\b(?:culpables?|asesin[oa]s?|delincuentes?|criminal(?:es)?|ladr[oó]n(?:es)?|corrupt[oa]s?)\b", re.I)
SEGUN = re.compile(r"\bseg[uú]n\b|\binform[oó]\b|\bindic[oó]\b|\bconfirm[oó]\b|\breport[oó]\b", re.I)
MESES_CORTOS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
# Ken Burns de la foto, uno por noticia (zoom ≥ 1.06 para que el paneo ≤ 2 % nunca deje ver el borde)
KEN_BURNS = ({"z": [1.06, 1.14], "x": [0, -2], "y": [0, -1.2]}, {"z": [1.14, 1.06], "x": [-1.5, 1], "y": [-1, 0.5]},
             {"z": [1.07, 1.15], "x": [1.5, -0.5], "y": [0.5, -1.5]}, {"z": [1.12, 1.06], "x": [0.5, -1.5], "y": [-1.5, 0]},
             {"z": [1.06, 1.13], "x": [-1, 1.5], "y": [0, -1]})

# ---- fase 1: rastreo y verificación ----
# un rastreador por sección (prefijo del id de sus candidatas); espejo en .claude/workflows/noticias.js (W11)
SECCIONES = {"pol": "política, justicia, Congreso y gobierno", "seg": "seguridad, sociedad, migración y sucesos",
             "eco": "economía, salud, clima, educación y deportes"}
CANDIDATAS_MAX, QUE_PASO_CARACTERES, CITA_MIN = 5, 200, 20
VENTANA_DIAS = 1                 # una noticia del día cuenta si se publicó hoy o ayer
# la foto va a sangre en la lámina de video/noticia.html (1080×1200 arriba, en 9:16 y 4:5; cover, Ken Burns ≤ 1.15):
# una og:image típica de 1200×630 se recorta a los lados y se agranda ≈ 1.9× (2.2× con el Ken Burns); la página la
# oscurece un poco más cuando pasa de 2× y le pone el grano encima. Por debajo de 600 px el aumento pasa de 2.3× y se
# ve en bloques: mejor una de referencia
FOTO_LADO_MIN = 600
DESCARGAS = os.path.join(RAIZ, "sesiones", "_descargas", "noticias")
AGENTE = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
# medios que cuentan como fuente (dominio → grupo: dos medios del mismo grupo no son independientes entre sí) y
# fuentes oficiales (cualquier .gob.gt cuenta como oficial). Un dominio fuera de la lista no cuenta para confirmar
MEDIOS = {"prensalibre.com": "prensa-libre", "guatevision.com": "prensa-libre", "soy502.com": "soy502",
          "republica.gt": "republica", "lahora.gt": "la-hora", "plazapublica.com.gt": "plaza-publica",
          "emisorasunidas.com": "emisoras-unidas", "publinews.gt": "publinews", "chapintv.com": "albavision",
          "tn23.tv": "tn23", "canalantigua.tv": "canal-antigua", "ojoconmipisto.com": "ojo-con-mi-pisto",
          "prensacomunitaria.org": "prensa-comunitaria", "agenciaocote.com": "ocote", "epinvestiga.com": "ep-investiga",
          "efe.com": "efe", "swissinfo.ch": "efe", "apnews.com": "ap", "reuters.com": "reuters", "infobae.com": "infobae",
          "france24.com": "france24", "elpais.com": "el-pais", "bbc.com": "bbc", "cnn.com": "cnn", "cnnespanol.cnn.com": "cnn",
          "dw.com": "dw", "vozdeamerica.com": "voa", "vozdeamerica.org": "voa"}
OFICIALES = {"agn.gt": "AGN", "dca.gob.gt": "Diario de Centro América", "tse.org.gt": "TSE", "pdh.org.gt": "PDH",
             "fedefut.org": "Fedefut", "cdag.com.gt": "CDAG", "usac.edu.gt": "USAC"}


def leer(p):
    return VD.leer(p)


def escribir(p, obj):
    VD.escribir(p, obj)


def falla(msg):
    return VD.falla(msg)


def fecha_corta(f):
    d = datetime.date.fromisoformat(f)
    return "%d %s" % (d.day, MESES_CORTOS[d.month - 1])


def paleta_del_dia(fecha):
    return PALETAS_CICLO[datetime.date.fromisoformat(fecha).toordinal() % len(PALETAS_CICLO)]


def musica_del_dia(paleta, fecha, forzada=None):
    """Las 2 pistas de la paleta se alternan cada vez que el ciclo vuelve a ella (cada 8 días); --musica la fuerza."""
    if forzada:
        return VD.elegir_musica(paleta, forzada)
    propias = sorted((x for x in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"] if x["paleta"] == paleta),
                     key=lambda x: x["id"])
    if not propias:
        raise ValueError("el catálogo no tiene música para la paleta «%s»" % paleta)
    return propias[(datetime.date.fromisoformat(fecha).toordinal() // len(PALETAS_CICLO)) % len(propias)]


def colores(paleta):
    """Los colores de /video (estilo Noche) más `realce`, el del gancho sobre la foto oscurecida: el acento del tema."""
    c = VD.colores(paleta)
    c["realce"] = c["acento"]   # Noche: el acento del tema ya se lee sobre la foto oscurecida (≥ 5.2:1 sobre el fondo)
    return c


def depto_id(nombre):
    """«Escuintla» → «GT05» (NOMBRES de templates/base.html); None si no es un departamento."""
    if not nombre:
        return None
    if re.fullmatch(r"GT\d\d", nombre):
        return nombre
    plano = VD._plano(nombre)
    return next((k for k, v in VD.nombres_depto().items() if VD._plano(v) == plano), None)


# ---------- preparar ----------
def cmd_preparar(a):
    fecha = a.fecha or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(fecha)
    except ValueError:
        print("--fecha va como YYYY-MM-DD", file=sys.stderr)
        return 2
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "noticias-" + fecha))
    for d in ("audio", "salida", "revision"):
        os.makedirs(os.path.join(trabajo, d), exist_ok=True)
    paleta = a.paleta or paleta_del_dia(fecha)
    if paleta not in PALETAS_CICLO:
        print("--paleta: una de %s" % ", ".join(PALETAS_CICLO), file=sys.stderr)
        return 2
    try:
        pista = musica_del_dia(paleta, fecha, a.musica)
    except ValueError as ex:
        return falla(str(ex))
    escribir(os.path.join(trabajo, "video.json"), {
        "tipo": "noticias", "fecha": fecha, "slug": "noticias-" + fecha, "hilo": None, "paleta": paleta,
        "musica": pista["id"], "duracion": "noticias", "objetivo_s": OBJETIVO_S, "tarjetas": [],
        "fixture": bool(a.fixture)})
    if a.fixture:
        for f in ("guion.json", "noticias.json"):
            shutil.copy(os.path.join(FIXTURE, f), os.path.join(trabajo, f))
        rc = fotos_fixture(trabajo)
        if rc:
            return rc
    print("noticias %s · paleta del día %s · música %s" % (fecha, paleta, pista["id"]))
    print(VD.rel(trabajo))
    return 0


def fotos_fixture(trabajo):
    """Fotos de ejemplo para la maqueta: fractales de ffmpeg (sin web) con textura suficiente para que el Ken Burns
    se mida como movimiento (V12)."""
    g = leer(os.path.join(trabajo, "guion.json"))
    os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
    tonos = (0, 70, 150, 220, 300)
    for k, nt in enumerate(g["noticias"]):
        foto = nt.get("foto") or {}
        if not foto.get("archivo"):
            continue
        dst = os.path.join(trabajo, foto["archivo"])
        VD.ff("-f", "lavfi", "-i", "mandelbrot=s=1600x1200:start_scale=%.2f:end_scale=0.3:start_x=%.3f:start_y=%.3f:maxiter=600" % (
            2.4 - 0.35 * k, -0.743 + 0.01 * k, 0.131 - 0.02 * k),
            "-vf", "hue=h=%d:s=0.55,eq=brightness=-0.04:saturation=0.8,noise=alls=12:allf=t" % tonos[k % len(tonos)],
            "-frames:v", "1", "-q:v", "3", dst)
    print("fotos de ejemplo → %s" % VD.rel(os.path.join(trabajo, "fotos")))
    return 0


def cmd_fotos_fixture(a):
    return fotos_fixture(os.path.abspath(a.trabajo))


# ---------- fase 1: leer una nota, candidatas (N1), verificación (N2), foto, consolidar, digesto ----------
def dominio(url):
    d = urllib.parse.urlparse(url or "").netloc.lower().split(":")[0]
    return d[4:] if d.startswith("www.") else d


def clasificar(url):
    """(«oficial» | «medio» | None, grupo): el grupo agrupa los medios de un mismo dueño; cada oficial es su propio grupo."""
    d = dominio(url)
    if d.endswith(".gob.gt") or d in OFICIALES:
        return "oficial", d
    for m, g in MEDIOS.items():
        if d == m or d.endswith("." + m):
            return "medio", g
    return None, d


def plano_cita(s):
    """Para buscar una cita en el texto de la nota: sin tildes, comillas, signos ni espacios dobles."""
    s = unicodedata.normalize("NFKD", html.unescape(s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9%$., ]", " ", s)).strip()


class _Texto(HTMLParser):
    """El texto legible de una página (sin script, style, nav, header, footer, aside, form) y sus metadatos."""
    FUERA = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "iframe", "button"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes, self.pila, self.meta, self.titulo, self._en_titulo, self.ld = [], [], {}, "", False, []
        self._en_ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            k = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if k and a.get("content") and k not in self.meta:
                self.meta[k] = a["content"]
        if tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._en_ld = True
        if tag == "title":
            self._en_titulo = True
        if tag in self.FUERA:
            self.pila.append(tag)
        if tag in ("p", "br", "li", "h1", "h2", "h3", "div", "tr"):
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self._en_titulo = False
        if tag == "script":
            self._en_ld = False
        if self.pila and self.pila[-1] == tag:
            self.pila.pop()

    def handle_data(self, data):
        if self._en_ld:
            self.ld.append(data)
        elif self._en_titulo:
            self.titulo += data
        elif not self.pila:
            self.partes.append(data)


def fecha_de(meta, ld):
    for k in ("article:published_time", "og:article:published_time", "datepublished", "date", "dc.date", "parsely-pub-date"):
        if meta.get(k):
            m = re.search(r"\d{4}-\d{2}-\d{2}", meta[k])
            if m:
                return m.group()
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', " ".join(ld))
    return m.group(1) if m else None


def bajar(url, destino=None, limite=8_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept-Language": "es-GT,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=25) as r:
        datos = r.read(limite)
        tipo = r.headers.get("Content-Type") or ""
    if destino:
        open(destino, "wb").write(datos)
    return datos, tipo


def cmd_leer(a):
    """Baja una nota y guarda su texto (la evidencia de las citas, N2) y sus metadatos (fecha, og:image) en la caché."""
    os.makedirs(DESCARGAS, exist_ok=True)
    base = os.path.join(DESCARGAS, "%s-%s" % (re.sub(r"[^a-z0-9]+", "-", dominio(a.url)), hashlib.sha1(a.url.encode()).hexdigest()[:10]))
    if not os.path.exists(base + ".json") or a.otra_vez:
        try:
            datos, tipo = bajar(a.url)
        except Exception as ex:  # noqa: BLE001 — cualquier fallo de red se informa y la nota se descarta
            return falla("no se pudo bajar %s (%s): usa otro medio o la fuente oficial" % (a.url, ex))
        enc = (re.search(r"charset=([\w-]+)", tipo) or re.search(rb'charset="?([\w-]+)', datos[:3000]))
        enc = (enc.group(1).decode() if isinstance(enc.group(1), bytes) else enc.group(1)) if enc else "utf-8"
        p = _Texto()
        p.feed(datos.decode(enc, "replace"))
        texto = re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t\r\f\v]+", " ", "".join(p.partes))).strip()
        img = p.meta.get("og:image") or p.meta.get("twitter:image") or p.meta.get("twitter:image:src")
        meta = {"url": a.url, "dominio": dominio(a.url), "clase": clasificar(a.url)[0], "titulo": html.unescape(p.meta.get("og:title") or p.titulo).strip(),
                "fecha": fecha_de(p.meta, p.ld), "og_image": urllib.parse.urljoin(a.url, img) if img else None,
                "archivo": VD.rel(base + ".txt"), "caracteres": len(texto)}
        open(base + ".txt", "w", encoding="utf-8").write(texto + "\n")
        escribir(base + ".json", meta)
    meta = leer(base + ".json")
    if meta["caracteres"] < 400:
        print("AVISO: solo %d caracteres de texto (la página se arma con JavaScript o bloquea): usa otra fuente" % meta["caracteres"])
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    if a.buscar:
        t = plano_cita(open(os.path.join(RAIZ, meta["archivo"]), encoding="utf-8").read())
        print("cita %s en el texto" % ("SÍ está" if plano_cita(a.buscar) in t else "NO está"))
    return 0


def fecha_trabajo(trabajo):
    return VD.estado(trabajo)["fecha"]


def en_ventana(f, fecha):
    try:
        d = (datetime.date.fromisoformat(fecha) - datetime.date.fromisoformat(f)).days
    except (TypeError, ValueError):
        return False
    return 0 <= d <= VENTANA_DIAS


def cmd_candidatas(a):
    """N1: candidatas_<sec>.json de los rastreadores."""
    trabajo = os.path.abspath(a.trabajo)
    fecha = fecha_trabajo(trabajo)
    secs = [a.seccion] if a.seccion else list(SECCIONES)
    fallas, n = [], 0
    for sec in secs:
        ruta = os.path.join(trabajo, "candidatas_%s.json" % sec)
        if not os.path.exists(ruta):
            fallas.append("N1 falta %s" % VD.rel(ruta))
            continue
        cs = leer(ruta).get("candidatas") or []
        if not 1 <= len(cs) <= CANDIDATAS_MAX:
            fallas.append("N1 %s: %d candidatas (van 1–%d)" % (sec, len(cs), CANDIDATAS_MAX))
        for c in cs:
            n += 1
            cid = c.get("id") or "?"
            if not re.fullmatch(r"%s-\d{1,2}" % sec, cid):
                fallas.append("N1 %s: id «%s» (va %s-1, %s-2…)" % (sec, cid, sec, sec))
            if not c.get("titular") or not 1 <= len(c.get("que_paso") or "") <= QUE_PASO_CARACTERES:
                fallas.append("N1 %s: titular y que_paso (≤ %d caracteres)" % (cid, QUE_PASO_CARACTERES))
            urls = c.get("urls") or []
            if not any(clasificar(u.get("url"))[0] for u in urls):
                fallas.append("N1 %s: ninguna url de un medio de la lista o de una fuente oficial (MEDIOS, OFICIALES, *.gob.gt)" % cid)
            if not any(en_ventana(u.get("fecha"), fecha) for u in urls):
                fallas.append("N1 %s: ninguna url publicada el %s o el día anterior (fecha YYYY-MM-DD)" % (cid, fecha))
            pt = c.get("puntaje") or {}
            if not all(isinstance(pt.get(k), int) and 1 <= pt[k] <= 5 for k in ("impacto", "alcance", "novedad")):
                fallas.append("N1 %s: puntaje {impacto, alcance, novedad} de 1 a 5" % cid)
    for f in fallas:
        print("FALLA", f)
    if not fallas:
        print("N1 ok · %d candidatas en %s" % (n, ", ".join(secs)))
    return 1 if fallas else 0


def texto_de(archivo):
    ruta = os.path.join(RAIZ, archivo or "")
    return plano_cita(open(ruta, encoding="utf-8").read()) if archivo and os.path.isfile(ruta) else None


def revisar_verificacion(v, fecha, trabajo):
    """N2 sobre verificacion_<id>.json → (fallas, avisos)."""
    fallas, avisos, cid = [], [], v.get("id") or "?"
    est = v.get("estado")
    if est not in ("confirmada", "en_desarrollo", "no_confirmada"):
        return ["N2 %s: estado confirmada | en_desarrollo | no_confirmada" % cid], []
    if est == "no_confirmada":
        return [], []
    textos, clases = {}, []
    for f in v.get("fuentes") or []:
        clase, grupo = clasificar(f.get("url"))
        t = texto_de(f.get("archivo"))
        if t is None:
            fallas.append("N2 %s: la fuente %s no tiene archivo local (python3 scripts/noticias.py leer <url>)" % (cid, f.get("url")))
            continue
        textos[f.get("url")] = t
        if len(plano_cita(f.get("cita"))) < CITA_MIN or plano_cita(f.get("cita")) not in t:
            fallas.append("N2 %s: la cita de %s no está en su texto (cópiala tal cual, ≥ %d caracteres)" % (cid, f.get("medio") or f.get("url"), CITA_MIN))
            continue
        if clase is None:
            avisos.append("%s: %s no está en la lista de medios ni es oficial: no cuenta para confirmar" % (cid, dominio(f.get("url"))))
            continue
        if f.get("tipo") and f["tipo"] != clase:
            avisos.append("%s: %s es «%s» en la lista (dice «%s»)" % (cid, dominio(f["url"]), clase, f["tipo"]))
        clases.append((clase, grupo, en_ventana(f.get("fecha"), fecha)))
    if not any(x[2] for x in clases):
        fallas.append("N2 %s: ninguna fuente válida publicada el %s o el día anterior" % (cid, fecha))
    grupos = {g for _, g, _ in clases}
    oficial, medio = any(c == "oficial" for c, _, _ in clases), any(c == "medio" for c, _, _ in clases)
    if est == "confirmada" and not (len(grupos) >= 2 and (medio or oficial)) :
        fallas.append("N2 %s: confirmada pide 2 fuentes independientes (grupos distintos) o una oficial y un medio; tiene %s"
                      % (cid, ", ".join(sorted(grupos)) or "ninguna válida"))
    if est == "en_desarrollo" and not clases:
        fallas.append("N2 %s: en_desarrollo pide al menos una fuente válida" % cid)
    todo = " ".join(textos.values())
    if not v.get("hechos"):
        fallas.append("N2 %s: sin hechos (qué pasó, con su cita)" % cid)
    for h in (v.get("hechos") or []) + (v.get("cifras") or []):
        if plano_cita(h.get("cita")) not in todo or len(plano_cita(h.get("cita"))) < 6:
            fallas.append("N2 %s: la cita «%s» no está en el texto de sus fuentes" % (cid, (h.get("cita") or "")[:60]))
    for c in v.get("cifras") or []:
        if not isinstance(c.get("valor"), (int, float)):
            fallas.append("N2 %s: cifra %s sin valor numérico" % (cid, c.get("id")))
        elif sueltos(c.get("texto") or "", [(round(float(c["valor"]), 6), VM.factor_unidad(c.get("unidad"))), (round(float(c["valor"]), 6), None)]):
            fallas.append("N2 %s: cifra %s: «%s» no es su valor %s" % (cid, c.get("id"), c.get("texto"), c["valor"]))
        elif sueltos(c.get("texto") or "", [(x, None) for x in numeros_cita(c.get("cita"))]):
            fallas.append("N2 %s: cifra %s: la cita no trae el número «%s»" % (cid, c.get("id"), c.get("texto")))
    foto = v.get("foto")
    if foto:
        if not foto.get("archivo") or not os.path.exists(os.path.join(trabajo, foto["archivo"])):
            fallas.append("N7 %s: foto sin archivo en TRABAJO/fotos/ (python3 scripts/noticias.py foto TRABAJO --id %s)" % (cid, cid))
        fallas += ["N7 %s: %s" % (cid, x) for x in faltas_credito(foto)]
    elif est != "no_confirmada":
        fallas.append("N7 %s: cada noticia lleva foto; si no hay de la noticia, una de referencia (la institución, el lugar o "
                      "la persona): noticias.py foto TRABAJO --id %s --url U --credito \"%s<fuente>\" --origen referencia"
                      % (cid, cid, CREDITO_PREFIJO["referencia"]))
    if v.get("icono") and not os.path.exists(os.path.join(VD.ICONOS_DIR, v["icono"] + ".svg")):
        fallas.append("N7 %s: icono «%s» no está en design/iconos/" % (cid, v["icono"]))
    return fallas, avisos


def cmd_verificacion(a):
    trabajo = os.path.abspath(a.trabajo)
    fecha = fecha_trabajo(trabajo)
    rutas = [os.path.join(trabajo, "verificacion_%s.json" % a.id)] if a.id else sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))
    fallas, avisos = [], []
    for r in rutas:
        if not os.path.exists(r):
            fallas.append("N2 falta %s" % VD.rel(r))
            continue
        f, av = revisar_verificacion(leer(r), fecha, trabajo)
        fallas += f
        avisos += av
    for x in avisos:
        print("AVISO", x)
    for x in fallas:
        print("FALLA", x)
    if not fallas:
        print("N2 ok · %d noticia(s)" % len(rutas))
    return 1 if fallas else 0


def cmd_foto(a):
    """La foto de una noticia: la que se pase con --url o, si no, la og:image de su primera fuente oficial (y si no, de su
    primer medio). Baja, comprueba el tamaño (N7), la pasa a JPG ≤ 1600 px de ancho y la anota en verificacion_<id>.json."""
    trabajo = os.path.abspath(a.trabajo)
    ruta_v = os.path.join(trabajo, "verificacion_%s.json" % a.id)
    v = leer(ruta_v)
    cands = []
    if a.url:
        origen = a.origen or (clasificar(a.url)[0] or "medio")
        cands = [(a.url, a.credito or CREDITO_PREFIJO[origen] + dominio(a.url), origen)]
    else:
        fuentes = sorted(v.get("fuentes") or [], key=lambda f: clasificar(f.get("url"))[0] != "oficial")
        for f in fuentes:
            meta = os.path.join(RAIZ, re.sub(r"\.txt$", ".json", f.get("archivo") or ""))
            img = leer(meta).get("og_image") if f.get("archivo") and os.path.exists(meta) else None
            if img:
                cands.append((img, "Foto: %s" % (f.get("medio") or dominio(f["url"])), clasificar(f["url"])[0] or "medio"))
    os.makedirs(os.path.join(DESCARGAS, "fotos"), exist_ok=True)
    os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
    motivos = []
    for url, credito, origen in cands:
        crudo = os.path.join(DESCARGAS, "fotos", hashlib.sha1(url.encode()).hexdigest()[:12])
        try:
            if not os.path.exists(crudo):
                bajar(url, crudo, limite=15_000_000)
            w, h = (int(x) for x in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                                    "stream=width,height", "-of", "csv=p=0:s=x", crudo],
                                                   capture_output=True, text=True).stdout.strip().split("x")[:2])
        except Exception as ex:  # noqa: BLE001
            motivos.append("%s: %s" % (url, ex))
            continue
        if min(w, h) < FOTO_LADO_MIN:
            motivos.append("%s: %d×%d (lado corto < %d)" % (url, w, h, FOTO_LADO_MIN))
            continue
        dst = "fotos/%s.jpg" % a.id
        VD.ff("-i", crudo, "-frames:v", "1", "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", os.path.join(trabajo, dst))
        v["foto"] = {"archivo": dst, "credito": credito[:CREDITO_CARACTERES], "origen": origen, "url": url, "tamano": [w, h]}
        escribir(ruta_v, v)
        print("foto %s · %d×%d · %s (%s) → %s" % (a.id, w, h, v["foto"]["credito"], origen, dst))
        return 0
    v["foto"] = None
    escribir(ruta_v, v)
    print("SIN FOTO %s: %s → busca una de referencia (la institución, el lugar o la persona) y pásala con --url U "
          "--credito \"%s<fuente>\" --origen referencia" % (a.id, "; ".join(motivos) or "ninguna fuente trae og:image",
                                                          CREDITO_PREFIJO["referencia"]))
    return 1


def cmd_consolidar(a):
    """verificacion_*.json → noticias.json (la base del editor y del gate del guion)."""
    trabajo = os.path.abspath(a.trabajo)
    fecha = fecha_trabajo(trabajo)
    nts = [leer(r) for r in sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))]
    escribir(os.path.join(trabajo, "noticias.json"), {"fecha": fecha, "noticias": nts})
    for v in nts:
        print("%-7s %-13s %-4s %s" % (v.get("id"), v.get("estado"), "foto" if v.get("foto") else "—", v.get("titular")))
    pub = [v for v in nts if v.get("estado") in ESTADOS_PUBLICABLES]
    print("→ %s · %d publicables de %d" % (VD.rel(os.path.join(trabajo, "noticias.json")), len(pub), len(nts)))
    return 0 if len(pub) >= NOTICIAS[0] else falla("N3 solo %d noticias publicables (van ≥ %d)" % (len(pub), NOTICIAS[0]))


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    if a.para == "rastreador":
        f = st["fecha"]
        rec = noticias_recientes(f)
        print("\n".join(["# Rastreo · %s (ventana: publicadas el %s o el día anterior)" % (f, f), "",
                          "## Ya contadas en los últimos 3 días (no las propongas sin una novedad real)"] +
                         (["- %s · %s" % (d, t) for d, t, _ in rec] or ["- (ninguna)"]) +
                         ["", "## Medios que cuentan (dominio → grupo; dos del mismo grupo no son independientes)"] +
                         ["- %s → %s" % kv for kv in sorted(MEDIOS.items())] +
                         ["", "## Fuentes oficiales: cualquier *.gob.gt, y %s" % ", ".join(sorted(OFICIALES))]))
        return 0
    if a.para == "verificador":
        c = next((c for r in glob.glob(os.path.join(trabajo, "candidatas_*.json")) for c in leer(r).get("candidatas") or []
                  if c.get("id") == a.id), None)
        if not c:
            return falla("no hay candidata %s" % a.id)
        print(json.dumps(c, ensure_ascii=False, indent=1))
        return 0
    base = leer(os.path.join(trabajo, "noticias.json"))
    out = ["# Noticias verificadas · %s (paleta %s)" % (st["fecha"], st["paleta"]), ""]
    for v in base["noticias"]:
        if v.get("estado") not in ESTADOS_PUBLICABLES:
            continue
        out += ["## %s · %s · %s%s" % (v["id"], v.get("seccion"), v["estado"], " · ya salió el %s" % repetida(v, noticias_recientes(st["fecha"])) if repetida(v, noticias_recientes(st["fecha"])) else ""),
                "Titular: %s" % v.get("titular"), "Qué pasó: %s" % v.get("resumen"),
                "Lugar: %s · icono: %s · foto: %s" % (v.get("depto") or "—", v.get("icono") or "—",
                                                     "%s (%s)" % (v["foto"]["credito"], v["foto"]["origen"]) if v.get("foto") else "NO (falta)"),
                "Fuentes: " + " · ".join("%s (%s, %s)" % (f.get("medio"), clasificar(f.get("url"))[0] or "fuera de lista", f.get("fecha")) for f in v.get("fuentes") or [])]
        out += ["- hecho: %s — «%s»" % (h.get("texto"), h.get("cita")) for h in v.get("hechos") or []]
        out += ["- cifra %s: %s — «%s»" % (c.get("id"), c.get("texto"), c.get("cita")) for c in v.get("cifras") or []]
        if v.get("sentencia"):
            out.append("- hay sentencia firme")
        out.append("")
    out += ["## Límites del guion (gate noticias.py guion --check)",
            "- %d–%d noticias de ≥ %d secciones; la breve (opcional) va al final" % (*NOTICIAS, SECCIONES_MIN),
            "- voz en palabras: gancho %d–%d caracteres, noticia %d–%d, breve %d–%d, cierre %d–%d; total %d–%d s (objetivo %d)"
            % (*CARACTERES["titular"], *CARACTERES["noticia"], *CARACTERES["breve"], *CARACTERES["cierre"], DURACION_MIN_S, DURACION_MAX_S, OBJETIVO_S),
            "- titulares ≤ %d palabras y ≤ %d caracteres; fuente en pantalla ≤ %d; cifra ≤ %d con etiqueta ≤ %d"
            % (TITULAR_PALABRAS, TITULAR_CARACTERES, FUENTE_CARACTERES, CIFRA_CARACTERES, ETIQUETA_CARACTERES),
            "- cierre: %d–%d líneas de resumen ≤ %d caracteres; final ≤ %d palabras" % (*RESUMEN_LINEAS, RESUMEN_CARACTERES, FINAL_PALABRAS)]
    print("\n".join(out))
    return 0


def cmd_fotos_contacto(a):
    """Hoja con todas las fotos del trabajo (para el QA de contenido del coordinador: sin víctimas ni menores)."""
    trabajo = os.path.abspath(a.trabajo)
    fotos = sorted(glob.glob(os.path.join(trabajo, "fotos", "*.jpg")))
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
    return 0


def faltas_credito(foto):
    """N7: el crédito empieza como manda su origen («Foto: …» o «Foto de referencia: …») y cabe en pantalla."""
    credito, origen = (foto.get("credito") or "").strip(), foto.get("origen")
    if origen not in CREDITO_PREFIJO:
        return ["origen «%s» (va %s)" % (origen, " | ".join(sorted(CREDITO_PREFIJO)))]
    if not credito.startswith(CREDITO_PREFIJO[origen]) or len(credito) <= len(CREDITO_PREFIJO[origen]) or len(credito) > CREDITO_CARACTERES:
        return ["la foto %s lleva crédito «%s<fuente>» (≤ %d)" % (origen, CREDITO_PREFIJO[origen], CREDITO_CARACTERES)]
    return []


def numeros_cita(cita):
    """Los números de una cita tal como se escribieron y los escritos a la manera de la prensa («Q3 mil 400 millones»)."""
    vals = [float(m.group().replace(",", "")) for m in re.finditer(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", cita or "")]
    return vals + [VM.hablado(m.group(0))[0] for m in VM.RE_HABLADO.finditer(cita or "")]


# ---------- gate del guion (N3–N6, N8, V3) ----------
def respaldo_de(nt):
    """Los números que respaldan una noticia (N4): el valor de cada cifra verificada (en su unidad) y todo número que
    aparezca en las citas de sus hechos y cifras (tal como se escribió)."""
    vals = set()
    for c in nt.get("cifras") or []:
        if isinstance(c.get("valor"), (int, float)):
            vals.add((round(float(c["valor"]), 6), VM.factor_unidad(c.get("unidad"))))
            vals.add((round(float(c["valor"]), 6), None))
    for x in (nt.get("hechos") or []) + (nt.get("cifras") or []) + (nt.get("fuentes") or []):
        for v in numeros_cita(x.get("cita")):
            vals.add((round(v, 6), None))
    return sorted(vals, key=lambda v: v[0])


def sueltos(texto, vals):
    """VM.sueltos con las cifras de este proyecto: «Q148,500 millones» lleva coma de miles (verificacion.py la leería
    como decimal de prensa, 148.5 millones); sin la coma delante de la escala, cuenta en su unidad."""
    t = re.sub(r"(\d{1,3}(?:,\d{3})+)(?=(?:\.\d+)?\s*(?:mil\s+millones|millones|mill[oó]n|M\b))",
               lambda m: m.group(1).replace(",", ""), texto or "")
    return VM.sueltos(t, vals)


def convertir(texto, n, fallas, tipo):
    """El texto del guion → segmentos (pantalla / voz), voz en palabras y prompt de ElevenLabs (V3)."""
    for motivo in VD.pausas_mal_puestas(texto):
        fallas.append("V9 escena %d: %s" % (n, motivo))
    NE.AVISOS.clear()
    try:
        segs = NE.segmentos(texto)
    except ValueError as ex:
        fallas.append("V3 escena %d: %s" % (n, ex))
        return None
    VD.mayuscula_inicial(segs)
    prompt = VD.con_breaks("".join(s["v"] for s in segs))
    for s in segs:
        s["p"], s["v"] = VD.sin_pausas(s["p"]), VD.sin_pausas(s["v"])
    segs[0]["p"], segs[0]["v"] = segs[0]["p"].lstrip(), segs[0]["v"].lstrip()
    voz = "".join(s["v"] for s in segs)
    for av in NE.AVISOS:
        fallas.append("V3 escena %d: %s" % (n, av))
    if re.search(r"\d", voz):
        fallas.append("V3 escena %d: la voz conserva dígitos: «%s»" % (n, voz))
    lo, hi = CARACTERES[tipo]
    if not lo <= len(voz) <= hi:
        fallas.append("N5 escena %d (%s): %d caracteres de voz (rango %d–%d ≈ %.0f–%.0f s)" % (n, tipo, len(voz), lo, hi, lo / VD.CPS, hi / VD.CPS))
    return {"segmentos": segs, "voz": voz, "prompt": prompt, "pantalla": "".join(s["p"] for s in segs)}


def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    g = leer(os.path.join(trabajo, "guion.json"))
    base = leer(os.path.join(trabajo, "noticias.json"))
    verificadas = {x["id"]: x for x in base.get("noticias") or []}
    recientes = noticias_recientes(st["fecha"])
    fallas, avisos, loc = [], [], []
    nts = g.get("noticias") or []
    # N3 selección
    if not NOTICIAS[0] <= len(nts) <= NOTICIAS[1]:
        fallas.append("N3 %d noticias (van %d–%d)" % (len(nts), *NOTICIAS))
    ids = [x.get("id") for x in nts]
    if len(set(ids)) != len(ids):
        fallas.append("N3 una noticia va dos veces")
    if len({(x.get("seccion") or "").lower() for x in nts}) < SECCIONES_MIN:
        fallas.append("N3 todas las noticias son de la misma sección (≥ %d secciones)" % SECCIONES_MIN)
    for x in nts:
        b = verificadas.get(x.get("id"))
        if not b:
            fallas.append("N3 %s no está en noticias.json" % x.get("id"))
        elif b.get("estado") not in ESTADOS_PUBLICABLES:
            fallas.append("N3 %s está «%s»: solo entran %s" % (x["id"], b.get("estado"), " o ".join(ESTADOS_PUBLICABLES)))
        elif repetida(b, recientes) and not b.get("novedad"):
            fallas.append("N3 %s ya salió el %s y no trae `novedad`" % (x["id"], repetida(b, recientes)))
    breves = [k for k, x in enumerate(nts) if x.get("breve")]
    if breves and breves != [len(nts) - 1]:
        fallas.append("N5 la breve va al final y solo una")
    # el gancho adelanta la primera noticia
    ga = g.get("gancho") or {}
    if not nts or ga.get("noticia") != nts[0].get("id"):
        fallas.append("N6 gancho.noticia debe ser la primera noticia (la más fuerte)")
    pant = (ga.get("pantalla") or "").strip()
    if not pant or VD.palabras(pant) > TITULAR_PALABRAS or len(pant) > TITULAR_CARACTERES:
        fallas.append("N6 gancho.pantalla: 1–%d palabras y ≤ %d caracteres («%s»)" % (TITULAR_PALABRAS, TITULAR_CARACTERES, pant))
    escenas = [("titular", ga, nts[0] if nts else {})] + [("breve" if x.get("breve") else "noticia", x, x) for x in nts]
    for n, (tipo, e, nt) in enumerate(escenas, 1):
        texto = e.get("texto") or ""
        if VETADAS.search(texto) and not (verificadas.get(nt.get("id")) or {}).get("sentencia"):
            fallas.append("N4 escena %d: «%s» sin sentencia firme (di «señalado», «sindicado», «acusado»)" % (n, VETADAS.search(texto).group()))
        if re.search(r"\ben suma\b", texto, re.I):
            fallas.append("N4 escena %d: «en suma» está prohibido" % n)
        c = convertir(texto, n, fallas, tipo)
        if c is None:
            continue
        b = verificadas.get(nt.get("id")) or {}
        vals = respaldo_de(b)
        cifra = e.get("cifra") if tipo != "titular" else None
        textos = [("voz", texto), ("titular", e.get("titular") or e.get("pantalla") or "")] + ([("cifra", cifra.get("texto") or "")] if cifra else [])
        for etiqueta, t in textos:
            sin = sueltos(t, vals)
            if sin:
                fallas.append("N4 escena %d (%s): números sin cita en noticias.json: %s" % (n, etiqueta, ", ".join(map(str, sin))))
        if b.get("estado") == "en_desarrollo" and tipo != "titular" and not SEGUN.search(texto):
            fallas.append("N2 escena %d: la noticia está en desarrollo: la voz atribuye («según el MP», «informó Conred»)" % n)
        if tipo != "titular":
            tit = (e.get("titular") or "").strip()
            if not tit or VD.palabras(tit) > TITULAR_PALABRAS or len(tit) > TITULAR_CARACTERES:
                fallas.append("N6 escena %d: titular 1–%d palabras y ≤ %d caracteres («%s»)" % (n, TITULAR_PALABRAS, TITULAR_CARACTERES, tit))
            if not 1 <= len((e.get("seccion") or "").strip()) <= SECCION_CARACTERES:
                fallas.append("N6 escena %d: seccion 1–%d caracteres" % (n, SECCION_CARACTERES))
            if not 1 <= len((e.get("fuente") or "").strip()) <= FUENTE_CARACTERES:
                fallas.append("N6 escena %d: fuente («Prensa Libre · MP») 1–%d caracteres" % (n, FUENTE_CARACTERES))
            if cifra and (len(cifra.get("texto") or "") > CIFRA_CARACTERES or len(cifra.get("etiqueta") or "") > ETIQUETA_CARACTERES
                          or not re.search(r"\d", cifra.get("texto") or "")):
                fallas.append("N6 escena %d: cifra.texto con dígitos ≤ %d y etiqueta ≤ %d" % (n, CIFRA_CARACTERES, ETIQUETA_CARACTERES))
            if cifra and VD.valor_de(cifra["texto"]) is not None and not any(
                    VD.valor_de(s["p"]) == VD.valor_de(cifra["texto"]) for s in c["segmentos"] if s["num"]):
                avisos.append("escena %d: la voz no dice la cifra %s: la píldora entra sin latido" % (n, cifra["texto"]))
            if n >= 3 and not re.match(r"^[¿¡]?\s*(?:y|además|también|en |mientras|por otro lado|otra|por su parte)", texto.strip(), re.I):
                avisos.append("escena %d: sin conector al inicio («Además», «En economía», «Mientras tanto»)" % n)
        foto = (nt.get("foto") or {})
        if foto.get("archivo"):
            ruta = os.path.join(trabajo, foto["archivo"])
            if not re.fullmatch(r"fotos/[a-z0-9_-]+\.(?:jpg|png|webp)", foto["archivo"]) or not os.path.exists(ruta):
                fallas.append("N7 escena %d: foto «%s» no está en TRABAJO/fotos/" % (n, foto["archivo"]))
            fallas += ["N7 escena %d: %s" % (n, x) for x in faltas_credito(foto)]
        else:
            fallas.append("N7 escena %d: cada noticia lleva foto (oficial, del medio o de referencia)" % n)
        if nt.get("icono") and not os.path.exists(os.path.join(VD.ICONOS_DIR, nt["icono"] + ".svg")):
            fallas.append("N7 escena %d: icono «%s» no está en design/iconos/" % (n, nt["icono"]))
        hueco = VD.hueco_maximo(c["segmentos"], c["voz"])[0]
        loc.append({"n": n, "tipo": "titular" if tipo == "titular" else "noticia", "breve": tipo == "breve",
                    "noticia": nt.get("id"), "tuit": None, "plantilla": "noticia", "enlace": None,
                    "voz": c["voz"], "prompt": c["prompt"], "segmentos": c["segmentos"], "pantalla": c["pantalla"],
                    "estimado_s": round(len(c["voz"]) / VD.CPS + VD.COLA, 2), "hueco_max_s": round(hueco, 2)})
    # N8 cierre
    ci = g.get("cierre") or {}
    res = ci.get("resumen") or []
    if not RESUMEN_LINEAS[0] <= len(res) <= RESUMEN_LINEAS[1] or any(len(r) > RESUMEN_CARACTERES for r in res):
        fallas.append("N8 cierre.resumen: %d–%d líneas ≤ %d caracteres" % (*RESUMEN_LINEAS, RESUMEN_CARACTERES))
    final = (ci.get("final") or "").strip()
    if not final or VD.palabras(final) > FINAL_PALABRAS:
        fallas.append("N8 cierre.final: 1–%d palabras" % FINAL_PALABRAS)
    elif not VD._plano(ci.get("texto") or "").endswith(VD._plano(final)):
        fallas.append("N8 cierre.final es la última frase de cierre.texto")
    if VD.CEBO.search(ci.get("texto") or ""):
        fallas.append("N8 el cierre pide comentar o compartir («%s»): «Sígueme en» va solo en pantalla" % VD.CEBO.search(ci["texto"]).group())
    if VD.PROHIBIDO_CIERRE.search(ci.get("texto") or ""):
        fallas.append("N8 la voz del cierre no dice fuentes ni «sígueme» (va en pantalla)")
    c = convertir(ci.get("texto") or "", len(escenas) + 1, fallas, "cierre")
    if c:
        loc.append({"n": len(escenas) + 1, "tipo": "cierre", "breve": False, "noticia": None, "tuit": None, "plantilla": "cierre",
                    "enlace": None, "voz": c["voz"], "prompt": c["prompt"], "segmentos": c["segmentos"], "pantalla": c["pantalla"],
                    "estimado_s": round(len(c["voz"]) / VD.CPS + VD.COLA_CIERRE, 2), "hueco_max_s": 0.0})
    # captions (como V5)
    cap = g.get("caption") or {}
    for k, _ in VD.PLATAFORMAS:
        if not (cap.get(k) or "").strip():
            fallas.append("V5 falta caption.%s" % k)
    if cap.get("shorts") and (len(cap["shorts"].splitlines()[0]) > VD.SHORTS_TITULO or "#Shorts" not in cap["shorts"]):
        fallas.append("V5 caption.shorts: primera línea ≤ %d caracteres con #Shorts" % VD.SHORTS_TITULO)
    for k, v in cap.items():
        sin = sueltos(v or "", sorted({x for nt in nts for x in respaldo_de(verificadas.get(nt.get("id")) or {})}, key=lambda x: x[0]))
        if sin:
            fallas.append("N4 caption.%s: números sin cita: %s" % (k, ", ".join(map(str, sin))))
    # N5 duración total (las escenas se solapan TRANSICION s; el bucle final suma BUCLE_S)
    chars = sum(len(x["voz"]) for x in loc)
    estimado = sum(x["estimado_s"] for x in loc) - VD.TRANSICION * (len(loc) - 1) + VD.BUCLE_S
    if not DURACION_MIN_S <= estimado <= DURACION_MAX_S:
        fallas.append("N5 duración estimada %.0f s (van %d–%d s; objetivo %d)" % (estimado, DURACION_MIN_S, DURACION_MAX_S, OBJETIVO_S))
    print("escenas %d + cierre · voz %d caracteres · estimado %.0f s (objetivo %d s, máximo %d)"
          % (len(loc) - 1, chars, estimado, OBJETIVO_S, DURACION_MAX_S))
    for x in loc:
        print("E%-2d %-8s %-4s %5.1fs  %s" % (x["n"], x["tipo"] + ("·b" if x["breve"] else ""), x["noticia"] or "-", x["estimado_s"], x["voz"]))
    for x in avisos:
        print("AVISO", x)
    if fallas:
        for f in fallas:
            print("FALLA", f)
        return 1
    escribir(os.path.join(trabajo, "locucion.json"),
             {"voz": VD.VOZ, "caracteres": chars, "estimado_s": round(estimado, 1), "duracion": "noticias",
              "objetivo_s": OBJETIVO_S, "n_escenas": len(loc) - 1, "promesa": None, "escenas": loc})
    print("→ %s · N3–N6, N8, V3 ok" % VD.rel(os.path.join(trabajo, "locucion.json")))
    return 0


def noticias_recientes(fecha, dias=3):
    """[(fecha, titular, urls)] de lo publicado en los últimos `dias` (memoria/noticias.json): N3 no repite una
    noticia (misma url o titular casi igual) sin `novedad`."""
    ruta = os.path.join(RAIZ, "memoria", "noticias.json")
    if not os.path.exists(ruta):
        return []
    hoy = datetime.date.fromisoformat(fecha)
    out = []
    for r in leer(ruta).get("noticieros") or []:
        if 0 < (hoy - datetime.date.fromisoformat(r["fecha"])).days <= dias:
            out += [(r["fecha"], x.get("titular") or "", set(x.get("urls") or [])) for x in r.get("noticias") or []]
    return out


def repetida(nt, recientes):
    """La fecha en que ya salió esta noticia, o None: comparte una url o ≥ 60 % de las palabras del titular."""
    urls = {f.get("url") for f in nt.get("fuentes") or []}
    pal = {w for w in VD._plano(nt.get("titular")).split() if len(w) > 3}
    for f, tit, us in recientes:
        otras = {w for w in VD._plano(tit).split() if len(w) > 3}
        if urls & us or (pal and otras and len(pal & otras) / min(len(pal), len(otras)) >= 0.6):
            return f
    return None


# ---------- tiempos ----------
def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    st, loc = VD.estado(trabajo), leer(os.path.join(trabajo, "locucion.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    por_id = {x["id"]: x for x in g["noticias"]}
    total_n = len(g["noticias"])
    fecha = fecha_corta(st["fecha"])
    ruta_b = os.path.join(trabajo, "noticias.json")   # el estado de cada noticia: «En desarrollo» va en un chip
    estados = {x.get("id"): x.get("estado") for x in leer(ruta_b).get("noticias") or []} if os.path.exists(ruta_b) else {}
    escenas, avisos = [], []
    for e in loc["escenas"]:
        n, tipo = e["n"], e["tipo"]
        src, dst = [os.path.join(trabajo, "audio", x % n) for x in ("voz_%d.mp3", "voz_%d_r.mp3")]
        VD.ff("-i", src, "-af", "atempo=%s" % VD.VELOCIDAD, "-c:a", "libmp3lame", "-b:a", "192k", dst)
        habladas = [dict(w, start=w["start"] / VD.VELOCIDAD, end=w["end"] / VD.VELOCIDAD)
                    for w in VD.sin_etiquetas(leer(os.path.join(trabajo, "audio", "palabras_%d.json" % n)))]
        try:
            ps = VD.alinear(e, habladas)
        except ValueError as ex:
            return falla("V6 %s · rehaz la voz de esa escena" % ex)
        cierre = tipo == "cierre"
        fin_voz = ps[-1]["end"]
        dur = round(VD.ffprobe_dur(dst) + (VD.COLA_CIERRE if cierre else VD.COLA), 3)
        pal = []
        for k, p in enumerate(ps):
            w = {"text": p["text"], "start": round(p["start"], 3), "end": round(p["end"], 3)}
            if p["seg"] and p["seg"]["num"]:
                w["num"] = True
                if not VD.es_anio_o_fecha(p["seg"]["p"], " ".join(x["text"] for x in ps[k + 1:k + 3])):
                    w["clave"] = VD.clave(VD.valor_de(p["seg"]["p"]))
            pal.append(w)
        S = {"n": n, "tipo": tipo, "tuit": None, "plantilla": e["plantilla"], "enlace": None, "icono": None,
             "dur": dur, "fin_voz": round(fin_voz, 3), "palabras": pal, "arriba": None}
        ev, sfx = [], []
        if cierre:
            k_fin = VD.indice_frase(ps, (g.get("cierre") or {}).get("final"))
            if k_fin is None or k_fin == 0:
                k_fin = max([k for k, p in enumerate(ps[:-1]) if p["text"].endswith((".", "!"))] or [-1]) + 1
            n_r = len(g["cierre"]["resumen"])
            # conclusiones: las líneas entran rápido (son los titulares que ya se vieron); luego la frase final y «Sígueme en»
            t_fin = max(0.2, ps[k_fin]["start"] - 0.1) if k_fin < len(ps) else fin_voz
            rs = [round(0.1 + q * min(0.45, max(0.2, (t_fin - 0.6) / max(1, n_r))), 3) for q in range(n_r)]
            S["T"] = {"r": rs, "r2": rs[1] if len(rs) > 1 else rs[0], "preg": round(t_fin, 3), "sigue": round(fin_voz + 0.1, 3)}
            ev = [(x, "r%d" % (q + 1)) for q, x in enumerate(rs)] + [(S["T"]["preg"], "pregunta"), (S["T"]["sigue"], "sigue")]
            sfx = [(S["T"]["preg"], "resolucion")]
        else:
            nt = por_id[e["noticia"]]
            foto = nt.get("foto") or {}
            N = {"indice": list(por_id).index(e["noticia"]) + 1, "total": total_n, "seccion": nt.get("seccion"),
                 "foto": foto.get("archivo"), "credito": foto.get("credito"), "icono": nt.get("icono"),
                 "depto": depto_id(nt.get("depto")), "lugar": nt.get("depto") if not foto.get("archivo") else None,
                 "kb": KEN_BURNS[(n - 1) % len(KEN_BURNS)], "cifra": None, "fuente": None,
                 "estado": estados.get(e["noticia"])}
            fin_1 = VD.fin_oracion_desde(pal)
            if tipo == "titular":
                palabras_t = (g["gancho"].get("pantalla") or "").split()
                N["titular"], _ = VD.alinear_linea(palabras_t, pal, 0.0, max(0.4, fin_1))
                N.update(fecha="Hoy · " + fecha, conteo="%d noticias" % total_n)
                S["T"] = {"tit": 0.0}   # la portada (montar) se toma en T.tit + 1.2: el titular ya está entero
                ev = [(0.0, "titular")] + [(w["start"], "titular") for w in N["titular"] if w.get("dicha")]
                sfx = [(0.0, "impacto")]
            else:
                t0 = VD.TRANSICION + 0.05
                # el titular es lo primero que se lee: entra entero en ~1.2 s (atado a la voz, una palabra no dicha quedaba
                # sola en pantalla hasta el fin de la primera oración)
                N["titular"] = VD.repartir((nt.get("titular") or "").split(), t0 + 0.1, t0 + 1.2, minimo=0.08)
                ev = [(0.1, "entrada")] + [(w["start"], "titular") for w in N["titular"]]
                sfx = [(0.0, "whoosh")]
                t_ult = N["titular"][-1]["start"] if N["titular"] else t0
                if nt.get("cifra"):
                    v = VD.valor_de(nt["cifra"]["texto"])
                    w = next((x for x in pal if v is not None and x.get("clave") == VD.clave(v)), None)
                    start = max(t_ult + 0.4, w["start"] - 0.1) if w else min(t_ult + 1.2, fin_voz - 1.5)
                    N["cifra"] = {"texto": nt["cifra"]["texto"], "etiqueta": nt["cifra"].get("etiqueta") or "",
                                  "start": round(start, 3), "pulso": [round(w["start"], 3), round(w["end"] + 0.2, 3)] if w else None}
                    ev += [(start, "cifra"), (start + 0.9, "cifra_fin")]
                    sfx.append((start, "tic"))
                # la fuente entra cuando la voz atribuye («según…»); si no, pasada la mitad de la voz
                k_s = next((k for k, x in enumerate(pal) if SEGUN.fullmatch(VD._plano(x["text"]) or "")), None)
                t_f = pal[k_s]["start"] if k_s is not None else max(t_ult + 1.0, 0.55 * fin_voz)
                if N["cifra"]:
                    t_f = max(t_f, N["cifra"]["start"] + 1.2)
                t_f = min(t_f, dur - 1.0)
                N["fuente"] = {"texto": "Fuente: " + nt["fuente"], "start": round(t_f, 3)}
                ev.append((t_f, "fuente"))
                sfx.append((t_f, "pulso"))
                # cada oración nueva hace latir la foto: la escena no pasa más de RITMO_MAX_S sin un evento visual
                # (y cada número que dice la voz, si no es la cifra de la píldora)
                cifra_t = N["cifra"]["pulso"][0] if N["cifra"] and N["cifra"]["pulso"] else None
                N["oraciones"] = sorted({round(pal[k + 1]["start"], 3) for k, x in enumerate(pal[:-1]) if x["text"].endswith((".", "?", "!", ":"))}
                                        | {round(x["start"], 3) for x in pal if x.get("clave") and x["start"] != cifra_t})
                ev += [(x, "oracion") for x in N["oraciones"]]
            S["N"] = N
        S["transicion"] = None if n == 1 else VD.TRANSICIONES["cierre" if cierre else "primera" if n == 2 else "tarjeta"]
        ev.append((dur, "fin"))
        S["eventos"] = [{"t": round(t, 3), "tipo": k} for t, k in sorted(ev, key=lambda x: x[0])]
        S["sfx"] = [{"t": round(t, 3), "id": k} for t, k in sorted(sfx, key=lambda x: x[0])]
        escenas.append(S)
        print("E%-2d %-8s %6.2f s  eventos=%d" % (n, tipo, dur, len(S["eventos"])))
    total = sum(s["dur"] for s in escenas) - VD.TRANSICION * (len(escenas) - 1)
    if total + VD.BUCLE_S > DURACION_MAX_S:
        avisos.append("N5 duración real %.1f s: pasa de %d s" % (total + VD.BUCLE_S, DURACION_MAX_S))
    linea_t, off = [], 0.0
    for s in escenas:
        linea_t += [(off + x["t"], x["tipo"], s["n"]) for x in s["eventos"]]
        off += s["dur"] - VD.TRANSICION
    linea_t.sort()
    peor = max(zip(linea_t, linea_t[1:]), key=lambda ab: ab[1][0] - ab[0][0]) if len(linea_t) > 1 else None
    if peor and peor[1][0] - peor[0][0] > VD.RITMO_MAX_S:
        avisos.append("V10 ritmo: %.1f s sin evento entre «%s» (E%d) y «%s» (E%d)"
                      % (peor[1][0] - peor[0][0], peor[0][1], peor[0][2], peor[1][1], peor[1][2]))
    ci = g["cierre"]
    escribir(os.path.join(trabajo, "escenas.json"), {
        "version": 2, "tipo": "noticias", "colores": colores(st["paleta"]), "redes": VD.REDES,
        "contexto_superior": g.get("contexto_superior") or "Guatemala · %s" % fecha,
        "gancho": {"pantalla": None, "linea": None}, "pago": {"n": None, "t": None},
        "cierre": {"resumen": ci["resumen"], "final": ci["final"], "pregunta": ci["final"], "tipo": "remate",
                   "rotulo": ci.get("rotulo") or "Hoy en Guatemala"},
        "transicion_s": VD.TRANSICION, "total_s": round(total, 2), "escenas": escenas})
    for x in avisos:
        print("AVISO", x)
    print("total %.1f s + %.1f s de bucle (objetivo %d s, máximo %d) · hueco máximo %.1f s → %s"
          % (total, VD.BUCLE_S, OBJETIVO_S, DURACION_MAX_S, (peor[1][0] - peor[0][0]) if peor else 0,
             VD.rel(os.path.join(trabajo, "escenas.json"))))
    return 0


# ---------- entregar ----------
def cmd_entregar(a):
    """Copia el noticiero a noticias/<fecha>/ (o --salida) con guion.json de entrega y fuentes.md. Las fotos no se copian:
    son de terceros y quedan en sesiones/."""
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    sal = os.path.join(trabajo, "salida")
    for f in ("video.mp4", "video_4x5.mp4", "subtitulos.srt", "caption.md", "portada.png"):
        if not os.path.exists(os.path.join(sal, f)):
            return falla("falta salida/%s: graba, monta y revisa (también --formato 4:5) antes de entregar" % f)
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    if not os.path.exists(ruta_cred) and not a.salida:
        return falla("sin audio/creditos.json: la voz no salió de ElevenLabs (una maqueta o una voz falsa solo se entrega con --salida)")
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, "noticias", st["fecha"]))
    os.makedirs(destino, exist_ok=True)
    for f in glob.glob(os.path.join(destino, "portada*.png")):
        os.remove(f)
    for f in ["video.mp4", "video_4x5.mp4", "subtitulos.srt", "caption.md"] + [os.path.basename(x) for x in glob.glob(os.path.join(sal, "portada*.png"))]:
        shutil.copy2(os.path.join(sal, f), os.path.join(destino, f))
    for f in ("contacto.png", "contacto_4x5.png"):
        if os.path.exists(os.path.join(trabajo, "revision", f)):
            shutil.copy2(os.path.join(trabajo, "revision", f), os.path.join(destino, f))
    g = leer(os.path.join(trabajo, "guion.json"))
    loc = leer(os.path.join(trabajo, "locucion.json"))
    E = leer(os.path.join(trabajo, "escenas.json"))
    base = {x["id"]: x for x in leer(os.path.join(trabajo, "noticias.json")).get("noticias") or []}
    critica, rc = None, os.path.join(trabajo, "critica.json")
    if os.path.exists(rc):
        c = leer(rc)
        critica = {"veredicto": c.get("veredicto"), "vuelta": c.get("vuelta"), "puntajes": c.get("puntajes")}
    else:
        print("AVISO sin critica.json: el noticiero se entrega sin la revisión del crítico")
    noticias = []
    for x in g["noticias"]:
        b = base.get(x["id"]) or {}
        noticias.append({"id": x["id"], "seccion": x.get("seccion"), "titular": x.get("titular"), "fuente": x.get("fuente"),
                         "estado": b.get("estado"), "breve": bool(x.get("breve")), "cifra": x.get("cifra"),
                         "foto": {k: (x.get("foto") or {}).get(k) for k in ("credito", "origen")} if x.get("foto") else None,
                         "urls": [f.get("url") for f in b.get("fuentes") or [] if f.get("url")]})
    entrega = {
        "id": st["fecha"], "tipo": "noticias", "fecha": st["fecha"], "paleta": st["paleta"], "musica": st["musica"],
        "voz": loc["voz"], "velocidad": VD.VELOCIDAD,
        "creditos_voz": leer(ruta_cred)["total"] if os.path.exists(ruta_cred) else None,
        "duracion_s": round(VD.ffprobe_dur(os.path.join(destino, "video.mp4")), 1), "critica": critica,
        "contexto_superior": g.get("contexto_superior"), "gancho": g["gancho"], "noticias": noticias,
        "escenas": [{"n": e["n"], "tipo": e["tipo"], "noticia": e.get("noticia"), "pantalla": e["pantalla"], "voz": e["voz"],
                     "dur": s_["dur"]} for e, s_ in zip(loc["escenas"], E["escenas"])],
        "cierre": g["cierre"], "caption": g["caption"]}
    escribir(os.path.join(destino, "guion.json"), entrega)
    lineas = ["# Fuentes · noticias del %s" % st["fecha"], "",
              "Para el primer comentario o la descripción. Cada noticia con las fuentes que la confirman.", ""]
    for k, x in enumerate(noticias, 1):
        lineas += ["%d. **%s** (%s)" % (k, x["titular"], x["seccion"])]
        lineas += ["   - %s" % u for u in x["urls"]]
        if x["foto"]:
            lineas += ["   - %s" % x["foto"]["credito"]]
    lineas += ["", "Sígueme: %s" % " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES)]
    open(os.path.join(destino, "fuentes.md"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("entregado en %s (%.1f s) · video.mp4 (TikTok, Reels, Shorts) + video_4x5.mp4 (feed) · caption.md · fuentes.md%s"
          % (VD.rel(destino), entrega["duracion_s"], "" if entrega["creditos_voz"] is None else " · %s créditos de voz" % entrega["creditos_voz"]))
    if entrega["duracion_s"] > DURACION_MAX_S:
        print("AVISO dura %.0f s: pasa de %d s" % (entrega["duracion_s"], DURACION_MAX_S))
    return 0


# ---------- reenvío a video.py ----------
REENVIO = ("voz", "voz-falsa", "descargar", "escuchar", "grabar", "montar", "revisar")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in REENVIO:
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video.py")] + sys.argv[1:], cwd=RAIZ).returncode
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("preparar")
    q.add_argument("--fecha")
    q.add_argument("--trabajo")
    q.add_argument("--musica")
    q.add_argument("--paleta", help="fuerza una paleta (por defecto, la del día: %s en ciclo)" % ", ".join(PALETAS_CICLO))
    q.add_argument("--fixture", action="store_true")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    sub.add_parser("tiempos").add_argument("trabajo")
    sub.add_parser("fotos-fixture").add_argument("trabajo")
    q = sub.add_parser("leer")
    q.add_argument("url")
    q.add_argument("--buscar", help="dice si esta cita está en el texto guardado")
    q.add_argument("--otra-vez", action="store_true", help="vuelve a bajarla aunque esté en la caché")
    q = sub.add_parser("candidatas")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--seccion", choices=list(SECCIONES))
    q = sub.add_parser("verificacion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--id")
    q = sub.add_parser("foto")
    q.add_argument("trabajo")
    q.add_argument("--id", required=True)
    q.add_argument("--url")
    q.add_argument("--credito")
    q.add_argument("--origen", choices=sorted(CREDITO_PREFIJO))
    sub.add_parser("consolidar").add_argument("trabajo")
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--para", choices=["rastreador", "verificador", "editor"], default="editor")
    q.add_argument("--id")
    sub.add_parser("fotos-contacto").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida", help="otra carpeta (pruebas y maqueta); por defecto noticias/<fecha>/")
    for nombre in REENVIO:
        sub.add_parser(nombre, help="→ scripts/video.py %s" % nombre)
    a = p.parse_args()
    return {"preparar": cmd_preparar, "guion": cmd_guion, "tiempos": cmd_tiempos, "fotos-fixture": cmd_fotos_fixture,
            "leer": cmd_leer, "candidatas": cmd_candidatas, "verificacion": cmd_verificacion, "foto": cmd_foto,
            "consolidar": cmd_consolidar, "digesto": cmd_digesto, "fotos-contacto": cmd_fotos_contacto, "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
