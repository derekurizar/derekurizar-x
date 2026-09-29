#!/usr/bin/env python3
"""Ensambla una tarjeta: templates/base.html + templates/graficos/<plantilla>.html.

Las plantillas son FRAGMENTOS (un <style> opcional + un <script> con `DATA` y
`render()`); la base aporta anatomía, fuentes, paletas y helpers. El resultado
es un HTML autocontenido (salvo las fuentes, que scripts/render.js sirve desde
design/fonts/). El visualista solo edita el objeto DATA del archivo ensamblado.

Uso:
  python3 scripts/nuevo_visual.py <plantilla> <destino.html> [--paleta cielo]
  python3 scripts/nuevo_visual.py --listar
  python3 scripts/nuevo_visual.py --galeria templates/.galeria [--paletas cielo,jade|todas]
Salida: 0 ok · 1 error · 2 uso incorrecto
"""
import argparse
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(RAIZ, "templates", "base.html")
DIR_PLANTILLAS = os.path.join(RAIZ, "templates", "graficos")
DIR_PRUEBAS = os.path.join(RAIZ, "templates", ".pruebas")
TOKENS = os.path.join(RAIZ, "design", "tokens.json")
MARCADOR = "<!-- T:PLANTILLA -->"


def tokens():
    with open(TOKENS, encoding="utf-8") as fh:
        return json.load(fh)


def plantillas(incluir_pruebas=False):
    rutas = sorted(glob.glob(os.path.join(DIR_PLANTILLAS, "*.html")))
    if incluir_pruebas:
        rutas += sorted(glob.glob(os.path.join(DIR_PRUEBAS, "*.html")))
    return rutas


def ruta_plantilla(nombre):
    for d in (DIR_PLANTILLAS, DIR_PRUEBAS):
        r = os.path.join(d, nombre + ".html")
        if os.path.exists(r):
            return r
    return None


def _sustituir_paleta(html, paleta):
    cierre = html.lower().find("</head>")
    desde = cierre + len("</head>") if cierre != -1 else 0
    m = re.search(r"<body\b([^>]*)>", html[desde:], re.I)
    if not m:
        raise ValueError("base.html sin <body>")
    attrs = m.group(1)
    if re.search(r'\bdata-paleta\s*=\s*"[^"]*"', attrs):
        attrs = re.sub(r'(\bdata-paleta\s*=\s*)"[^"]*"', r'\1"%s"' % paleta, attrs)
    else:
        attrs = attrs.rstrip() + ' data-paleta="%s"' % paleta
    ini, fin = desde + m.start(), desde + m.end()
    return html[:ini] + "<body" + attrs + ">" + html[fin:]


def ensamblar(nombre, destino, paleta, tk):
    fuente = ruta_plantilla(nombre)
    if not fuente:
        return False, "no existe la plantilla %r (hay: %s)" % (
            nombre, ", ".join(os.path.splitext(os.path.basename(p))[0] for p in plantillas()))
    if paleta not in tk["paletas"]:
        return False, "paleta %r no existe en design/tokens.json (hay: %s)" % (paleta, ", ".join(tk["paletas"]))
    with open(BASE, encoding="utf-8") as fh:
        base = fh.read()
    with open(fuente, encoding="utf-8") as fh:
        frag = fh.read()
    if MARCADOR not in base:
        return False, "base.html no tiene el marcador " + MARCADOR
    if "const DATA" not in frag or "function render" not in frag:
        return False, "%s debe definir `const DATA = {...}` y `function render(D)`" % os.path.relpath(fuente, RAIZ)
    if re.search(r"https?://", frag):
        return False, "%s contiene una URL: las tarjetas no admiten recursos externos" % os.path.relpath(fuente, RAIZ)
    cabecera = "<!-- plantilla: %s · paleta: %s · ensamblado por scripts/nuevo_visual.py -->\n" % (nombre, paleta)
    html = base.replace(MARCADOR, cabecera + frag.strip() + "\n")
    html = _sustituir_paleta(html, paleta)
    os.makedirs(os.path.dirname(os.path.abspath(destino)) or ".", exist_ok=True)
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(html)
    return True, "%s (%s) -> %s" % (nombre, paleta, os.path.relpath(destino, os.getcwd()))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("plantilla", nargs="?")
    p.add_argument("destino", nargs="?")
    p.add_argument("--paleta", default="cielo")
    p.add_argument("--listar", action="store_true")
    p.add_argument("--galeria", metavar="DIR", help="ensambla todas las plantillas (y .pruebas/) en DIR")
    p.add_argument("--paletas", default="cielo", help="para --galeria: lista separada por comas o 'todas'")
    a = p.parse_args()
    tk = tokens()

    if a.listar:
        for r in plantillas(incluir_pruebas=True):
            with open(r, encoding="utf-8") as fh:
                primera = fh.readline().strip()
            print("  %-16s %s" % (os.path.splitext(os.path.basename(r))[0], primera[:90]))
        return 0

    if a.galeria:
        pals = list(tk["paletas"]) if a.paletas == "todas" else [s.strip() for s in a.paletas.split(",") if s.strip()]
        fallos, n = 0, 0
        for r in plantillas(incluir_pruebas=True):
            nombre = os.path.splitext(os.path.basename(r))[0]
            for pal in pals:
                destino = os.path.join(a.galeria, "%s%s.html" % (nombre, "" if len(pals) == 1 else "-" + pal))
                png = os.path.splitext(destino)[0] + ".png"
                if os.path.exists(png):
                    os.remove(png)
                ok, msg = ensamblar(nombre, destino, pal, tk)
                n += ok
                if not ok:
                    fallos += 1
                    print("ERROR: " + msg, file=sys.stderr)
        print("[galeria] %d ensamblado(s) · %d error(es)" % (n, fallos))
        return 1 if fallos else 0

    if not a.plantilla or not a.destino:
        p.error("hacen falta <plantilla> y <destino.html> (o --listar / --galeria DIR)")
    ok, msg = ensamblar(a.plantilla, a.destino, a.paleta, tk)
    print(("OK   " if ok else "ERROR: ") + msg, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
