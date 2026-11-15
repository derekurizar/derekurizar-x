#!/usr/bin/env python3
"""fuentes_web.py — leer la web para los flujos de video: qué dominio es una fuente, de qué grupo, y bajar una página.

Salió de scripts/noticias.py al retirar /noticias y /semana (2026-11-14): lo usan /historia, /serie, /explica y
/congreso (`historia.py leer`, `explica.py leer`). Solo stdlib.

  dominio(url)            «https://www.prensalibre.com/x» → «prensalibre.com»
  clasificar(url)         («oficial» | «medio» | None, grupo): dos medios del mismo grupo no son independientes
  MEDIOS · OFICIALES      la lista cerrada de fuentes (historia.py la amplía con prensa internacional, museos y agencias)
  bajar(url, destino)     los bytes y el Content-Type, con el agente de un navegador
  _Texto                  HTMLParser: el texto legible de una página, sus metadatos y su JSON-LD
  fecha_de(meta, ld)      la fecha de publicación (AAAA-MM-DD) de los metadatos o del JSON-LD
  plano_cita(s)           una cita normalizada para buscarla en el texto guardado
"""
import html
import re
import unicodedata
import urllib.parse
import urllib.request
from html.parser import HTMLParser

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
