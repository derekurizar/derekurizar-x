#!/usr/bin/env python3
"""
Hilos - Descarga y tabula fuentes oficiales que WebFetch no puede leer
===============================================================================
Complementa a fetch_pdf.sh: cubre Excel (.xlsx) y tablas HTML (.htm/.html) —
formatos tipicos de Banguat, INE y SAT. Solo stdlib (sin pandas/openpyxl).

Convierte a CSV en sesiones/_descargas/ para que el agente lo lea directo:
  .xlsx       -> un CSV por hoja (zipfile + XML; celdas y sharedStrings)
  .htm/.html  -> un CSV por <table> encontrada
  .csv        -> se guarda tal cual
  .xls        -> solo descarga (binario legado; convertir a mano) y avisa
  .pdf        -> avisa: usar `make pdf URL=...`

Caché: antes de descargar consulta sesiones/_descargas/indice.json (helper
scripts/indice_descargas.py). Si la URL ya está y el archivo existe, lo reutiliza
e imprime «(caché) → archivo», salvo --refrescar. Cada descarga queda registrada.

Uso:
  python3 scripts/fetch_tabla.py <URL-o-ruta-local> [--out sesiones/_descargas/nombre] [--refrescar]
  python3 scripts/fetch_tabla.py --enlaces '\\.xlsx$' <URL de la pagina>   # lista enlaces que casan, sin descargarlos
  (o `make tabla URL=...`)
Salida: 0 ok · 1 error · 2 uso incorrecto · 3 formato no convertible (descargado igual)
"""
import argparse
import csv
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indice_descargas as idx  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
SESION = idx.DESCARGAS


def es_url(s):
    return s.lower().startswith(("http://", "https://"))


def descargar(url, out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(out, "wb") as f:
        f.write(r.read())
    print(f"descargado -> {os.path.relpath(out)}")
    return out


def fetch(src, out, refrescar=False):
    """Devuelve (ruta_local, entrada_cache_o_None)."""
    if os.path.exists(src):
        return src, None
    if not es_url(src):
        raise SystemExit(f"ERROR: {src!r} no es una URL ni una ruta existente")
    cache = None if refrescar else idx.buscar(src)
    if cache:
        print(f"(caché) → {cache['archivo']}")
        return cache["archivo_abs"], cache
    try:
        return descargar(src, out), None
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ERROR HTTP {e.code} al descargar {src}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SystemExit(f"ERROR de red al descargar {src}: {e}")


# ---------- .xlsx (zip de XML, stdlib puro) ----------

def _col_to_idx(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def xlsx_to_csvs(path):
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    outs = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
        sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        for sheet in sheets:
            root = ET.fromstring(z.read(sheet))
            rows = []
            for row in root.iter(f"{{{ns['m']}}}row"):
                cells = {}
                for c in row.findall("m:c", ns):
                    v = c.find("m:v", ns)
                    if v is None or v.text is None:
                        continue
                    val = shared[int(v.text)] if c.get("t") == "s" else v.text
                    cells[_col_to_idx(c.get("r", "A1"))] = val
                if cells:
                    width = max(cells) + 1
                    rows.append([cells.get(i, "") for i in range(width)])
            if not rows:
                continue
            num = re.search(r"sheet(\d+)", sheet).group(1)
            out = f"{os.path.splitext(path)[0]}_hoja{num}.csv"
            with open(out, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            outs.append((out, len(rows)))
    return outs


# ---------- tablas HTML ----------

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._row, self._cell, self._depth = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self.tables.append([])
        elif self._depth and tag == "tr":
            self._row = []
        elif self._depth and tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "table" and self._depth:
            self._depth -= 1
        elif self._depth and tag == "tr" and self._row is not None:
            if self._row:
                self.tables[-1].append(self._row)
            self._row = None
        elif self._depth and tag in ("td", "th") and self._cell is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            if self._row is not None:
                self._row.append(text)
            self._cell = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def decodificar(raw):
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def html_to_csvs(path):
    text = decodificar(open(path, "rb").read())
    p = TableParser()
    p.feed(text)
    outs = []
    for i, table in enumerate(t for t in p.tables if t):
        out = f"{os.path.splitext(path)[0]}_tabla{i + 1}.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(table)
        outs.append((out, len(table)))
    return outs


# ---------- --enlaces ----------

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag in ("a", "area", "link", "iframe", "embed", "source"):
            for k, v in attrs:
                if k in ("href", "src") and v:
                    self.hrefs.append(v)


def listar_enlaces(patron, url):
    try:
        rx = re.compile(patron, re.I)
    except re.error as e:
        raise SystemExit(f"ERROR: patron {patron!r} invalido: {e}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            html = decodificar(r.read())
            base = r.geturl()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ERROR HTTP {e.code} al leer {url}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SystemExit(f"ERROR de red al leer {url}: {e}")
    p = LinkParser()
    p.feed(html)
    vistos, out = set(), []
    for h in p.hrefs:
        absu = urllib.parse.urljoin(base, h.strip())
        if absu in vistos or not rx.search(absu):
            continue
        vistos.add(absu)
        out.append(absu)
    return out


def main():
    ap = argparse.ArgumentParser(description="Descarga Excel/HTML oficial y lo convierte a CSV legible (con caché en sesiones/_descargas/indice.json)")
    ap.add_argument("src", nargs="?", help="URL o ruta local del archivo (o la pagina, con --enlaces)")
    ap.add_argument("--out", help="ruta de descarga (default: sesiones/_descargas/<nombre>)")
    ap.add_argument("--refrescar", action="store_true", help="ignora la caché y vuelve a descargar")
    ap.add_argument("--enlaces", metavar="PATRON", help="lista los enlaces de la pagina que casan con el regex (p. ej. '\\.xlsx$'), sin descargarlos")
    args = ap.parse_args()
    if not args.src:
        ap.error("hace falta <URL-o-ruta>")

    if args.enlaces:
        if not es_url(args.src):
            ap.error("--enlaces requiere una URL")
        enlaces = listar_enlaces(args.enlaces, args.src)
        for e in enlaces:
            print(e)
        print(f"# {len(enlaces)} enlace(s) que casan con {args.enlaces!r}", file=sys.stderr)
        return 0 if enlaces else 1

    name = os.path.basename(urllib.parse.urlparse(args.src).path if es_url(args.src) else args.src) or "descarga"
    out = os.path.abspath(args.out) if args.out else os.path.join(SESION, name)
    path, cache = fetch(args.src, out, args.refrescar)
    ext = os.path.splitext(path)[1].lower()

    if cache and cache["derivados_abs"] and len(cache["derivados_abs"]) == len(cache.get("derivados", [])):
        for d in cache["derivados_abs"]:
            filas = sum(1 for _ in open(d, encoding="utf-8", errors="replace"))
            print(f"(caché) OK -> {os.path.relpath(d)} ({filas} filas)")
        return 0

    if ext == ".xlsx":
        results = xlsx_to_csvs(path)
    elif ext in (".htm", ".html"):
        results = html_to_csvs(path)
    elif ext == ".csv":
        results = [(path, sum(1 for _ in open(path, encoding="utf-8", errors="replace")))]
    elif ext == ".xls":
        print(f"AVISO: {path} es .xls binario legado; stdlib no lo convierte. "
              "Abrelo con Numbers/Excel y exporta a CSV, o busca la version .xlsx de la fuente.")
        if es_url(args.src):
            idx.registrar(args.src, path)
        return 3
    elif ext == ".pdf":
        print("AVISO: para PDFs usa `make pdf URL=...` (pdftotext -layout).")
        if es_url(args.src):
            idx.registrar(args.src, path)
        return 3
    else:
        print(f"AVISO: extension {ext!r} no soportada; archivo descargado en {path}.")
        if es_url(args.src):
            idx.registrar(args.src, path)
        return 3

    if es_url(args.src):
        idx.registrar(args.src, path, [r[0] for r in results if r[0] != path])
    if not results:
        print("Sin tablas encontradas en el archivo.")
        return 1
    for out_path, rows in results:
        print(f"OK -> {os.path.relpath(out_path)} ({rows} filas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
