#!/usr/bin/env python3
"""Comprueba que los workflows no se desincronicen entre sí ni con el framework. Solo stdlib.

El sandbox del Workflow no importa módulos, así que hilo.js, dato.js e ideas.js duplican constantes
(PALETAS, PLANTILLAS, HOOKS, REQ, RE_*) y la función pesoX. Este script las extrae por regex y falla si:
  W1 PALETAS difiere entre workflows o de design/tokens.json
  W2 PLANTILLAS difiere entre hilo.js y dato.js o del catálogo templates/graficos/*.html
  W3 HOOKS difiere entre workflows o de ensamblar.HOOKS; BEATS (hilo.js) difiere de ensamblar.BEATS
  W4 REQ, RE_LINK, RE_BAIT, RE_SUPER o pesoX difieren entre hilo.js y dato.js
  W5 las claves de MODOS de hilo.js y dato.js no coinciden con ensamblar.MODOS (aviso si aún no existen)
  W7 gráficos del informe: todo G.<tipo> de investigacion/graficos/*.js tiene plantilla de tarjeta (o está en
     informe.SOLO_DOCUMENTO), campos en informe.CAMPOS_GRAFICO y extractor en ensamblar.CLAVES_DATO; ningún
     G.<tipo> se define dos veces; las plantillas sin G.* se avisan (informe.plantillas_sin_g)
  W8 ningún gráfico del informe (salvo el adaptador _comun.js) usa helpers de la tarjeta que leen su DOM o sus variables CSS
     (H.color, H.rampa, H.rampaColor, H.halo, H.periodos, H.textoSobre, H.espacio, H.lienzo, H.leyenda,
     H.anotar, H.cabecera, H.verificar, document.getElementById)

Uso: python3 scripts/check_workflows.py [--quiet]   · salida 0 ok · 1 diferencias
"""
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
from ensamblar import BEATS, HOOKS, MODOS, CLAVES_DATO  # noqa: E402
import informe  # noqa: E402  (TIPOS_GRAFICO, CAMPOS_GRAFICO, SOLO_DOCUMENTO, plantillas_sin_g, snake)

RE_PROHIBIDO = re.compile(r"\bH\.(color|rampa|rampaColor|halo|periodos|textoSobre|espacio|lienzo|leyenda|anotar|cabecera|verificar)\b|document\.getElementById\(")

WF = os.path.join(RAIZ, ".claude", "workflows")
ERRORES, AVISOS = [], []


def err(m): ERRORES.append(m)
def warn(m): AVISOS.append(m)


def fuente(nombre):
    ruta = os.path.join(WF, nombre)
    if not os.path.exists(ruta):
        err("falta %s" % os.path.relpath(ruta, RAIZ)); return ""
    return open(ruta, encoding="utf-8").read()


def lista(src, nombre):
    """const NOMBRE = ['a', 'b'] → ['a', 'b'] (None si no está)."""
    m = re.search(r"^const %s = \[(.*?)\]\s*(//.*)?$" % nombre, src, re.M)
    return re.findall(r"'([^']*)'", m.group(1)) if m else None


def bloque(src, inicio, fin=r"^\}"):
    """Texto desde la línea que empieza por `inicio` hasta la primera línea que casa con `fin` (ambas incluidas)."""
    m = re.search(r"^%s.*$" % re.escape(inicio), src, re.M)
    if not m:
        return None
    resto = src[m.start():]
    f = re.search(fin, resto[m.end() - m.start():], re.M)
    if not f:
        return resto
    return resto[: (m.end() - m.start()) + f.end()]


def linea(src, inicio):
    m = re.search(r"^%s.*$" % re.escape(inicio), src, re.M)
    return m.group(0) if m else None


def norm(t):
    return re.sub(r"[ \t]+", " ", t or "").strip()


def claves_modos(src):
    b = bloque(src, "const MODOS = {")
    if not b:
        return None
    return re.findall(r"^\s+(\w+):\s*\{", b, re.M)


def main():
    quiet = "--quiet" in sys.argv
    hilo, dato, ideas = fuente("hilo.js"), fuente("dato.js"), fuente("ideas.js")
    if not (hilo and dato):
        return fin(quiet)
    tokens = json.load(open(os.path.join(RAIZ, "design", "tokens.json"), encoding="utf-8"))
    paletas = list(tokens.get("paletas", {}).keys())
    catalogo = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(RAIZ, "templates", "graficos", "*.html")))

    # W1 paletas
    for nombre, src in (("hilo.js", hilo), ("dato.js", dato), ("ideas.js", ideas)):
        if not src:
            continue
        p = lista(src, "PALETAS")
        if p is None:
            err("W1 %s: no se encontró `const PALETAS = [...]`" % nombre)
        elif sorted(p) != sorted(paletas):
            err("W1 %s PALETAS %s ≠ design/tokens.json %s" % (nombre, p, paletas))
    # W2 plantillas
    for nombre, src in (("hilo.js", hilo), ("dato.js", dato)):
        p = lista(src, "PLANTILLAS")
        if p is None:
            err("W2 %s: no se encontró `const PLANTILLAS = [...]`" % nombre)
        elif sorted(p) != catalogo:
            err("W2 %s PLANTILLAS ≠ templates/graficos/: sobran %s, faltan %s" % (nombre, sorted(set(p) - set(catalogo)), sorted(set(catalogo) - set(p))))
    # W3 hooks y beats
    for nombre, src in (("hilo.js", hilo), ("dato.js", dato), ("ideas.js", ideas)):
        if not src:
            continue
        h = lista(src, "HOOKS")
        if h is None:
            err("W3 %s: no se encontró `const HOOKS = [...]`" % nombre)
        elif h != HOOKS:
            err("W3 %s HOOKS %s ≠ ensamblar.HOOKS %s" % (nombre, h, HOOKS))
    b = lista(hilo, "BEATS")
    if b is None:
        err("W3 hilo.js: no se encontró `const BEATS = [...]`")
    elif b != BEATS:
        err("W3 hilo.js BEATS %s ≠ ensamblar.BEATS %s" % (b, BEATS))
    # W4 bloques que deben ser idénticos en hilo.js y dato.js
    for etiqueta, extraer in (
        ("REQ", lambda s: bloque(s, "const REQ = {")),
        ("RE_LINK", lambda s: linea(s, "const RE_LINK")),
        ("RE_BAIT", lambda s: linea(s, "const RE_BAIT")),
        ("RE_SUPER", lambda s: linea(s, "const RE_SUPER")),
        ("pesoX", lambda s: bloque(s, "function pesoX(texto) {")),
    ):
        a, c = extraer(hilo), extraer(dato)
        if a is None or c is None:
            err("W4 %s: no se encontró en %s" % (etiqueta, "hilo.js" if a is None else "dato.js"))
        elif norm(a) != norm(c):
            err("W4 %s difiere entre hilo.js y dato.js (copia el bloque de uno al otro)" % etiqueta)
    # W5 modos
    for nombre, src, tipo in (("hilo.js", hilo, "hilo"), ("dato.js", dato, "dato")):
        k = claves_modos(src)
        if k is None:
            warn("W5 %s: aún no tiene `const MODOS = {…}` (modos de ensamblar.MODOS[%r]: %s)" % (nombre, tipo, MODOS[tipo]))
        elif sorted(k) != sorted(MODOS[tipo]):
            err("W5 %s MODOS %s ≠ ensamblar.MODOS[%r] %s" % (nombre, k, tipo, MODOS[tipo]))
    graficos_informe(catalogo)
    return fin(quiet)


def graficos_informe(catalogo):
    """W7 y W8: el motor de gráficos del informe frente al catálogo de tarjetas."""
    tipos, cat = informe.TIPOS_GRAFICO, {informe.snake(c) for c in catalogo}
    sobran = sorted(tipos - cat - informe.SOLO_DOCUMENTO)
    if sobran:
        err("W7 G.* sin plantilla de tarjeta ni en informe.SOLO_DOCUMENTO: %s" % ", ".join(sobran))
    faltan = sorted(informe.plantillas_sin_g())
    if faltan:
        warn("W7 plantillas de tarjeta sin G.* en investigacion/graficos/ (solo valen como figura tarjeta): %s" % ", ".join(faltan))
    sin_campos = sorted(tipos - set(informe.CAMPOS_GRAFICO))
    if sin_campos:
        err("W7 G.* sin entrada en informe.CAMPOS_GRAFICO: %s" % ", ".join(sin_campos))
    sin_claves = sorted(t for t in tipos - informe.SOLO_DOCUMENTO if informe.kebab(t) not in CLAVES_DATO)
    if sin_claves:
        err("W7 G.* sin extractor en ensamblar.CLAVES_DATO: %s" % ", ".join(sin_claves))
    vistos = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "investigacion", "graficos", "*.js"))):
        src = open(ruta, encoding="utf-8").read()
        for t in informe.RE_G.findall(src):
            if t in vistos:
                err("W7 G.%s definido dos veces: %s y %s" % (t, vistos[t], os.path.basename(ruta)))
            vistos[t] = os.path.basename(ruta)
        if os.path.basename(ruta) == "_comun.js":
            continue  # GX es el adaptador: envuelve H.rampa (solo en panel) y H.* puros; los G.* solo usan GX.*
        for k, linea_src in enumerate(src.split("\n"), 1):
            m = RE_PROHIBIDO.search(linea_src)
            if m and not linea_src.lstrip().startswith("//"):
                err("W8 %s:%d usa %s (helper de la tarjeta; en el informe se pinta con col.* y GX.*)" % (os.path.relpath(ruta, RAIZ), k, m.group(0)))


def fin(quiet):
    for a in AVISOS:
        print("AVISO  " + a)
    for e in ERRORES:
        print("ERROR  " + e, file=sys.stderr)
    if not quiet or ERRORES:
        print("[check_workflows] %d error(es) · %d aviso(s)" % (len(ERRORES), len(AVISOS)))
    return 1 if ERRORES else 0


if __name__ == "__main__":
    sys.exit(main())
