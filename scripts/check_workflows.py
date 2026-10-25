#!/usr/bin/env python3
"""Comprueba que los workflows no se desincronicen entre sí ni con el framework. Solo stdlib.

El sandbox del Workflow no importa módulos, así que hilo.js, dato.js e ideas.js duplican constantes
(PALETAS, PLANTILLAS, HOOKS, REQ, RE_*) y la función pesoX. Este script las extrae por regex y falla si:
  W1 PALETAS difiere entre workflows o de design/tokens.json; AREAS, FORMATOS y ACCESOS de ideas.js ≠ ideas.py
  W2 PLANTILLAS difiere entre hilo.js y dato.js o del catálogo templates/graficos/*.html
  W3 HOOKS difiere entre workflows o de ensamblar.HOOKS; BEATS (hilo.js) difiere de ensamblar.BEATS
  W4 REQ, RE_LINK, RE_BAIT, RE_SUPER o pesoX difieren entre hilo.js y dato.js
  W5 las claves de MODOS de dato.js no coinciden con ensamblar.MODOS["dato"]; las de hilo.js ∪ investigacion.js
     no coinciden con ensamblar.MODOS["hilo"] o se repiten entre ambos (aviso si aún no existen)
  W6 investigacion.js: TIPOS_PAGINA igual a informe.TIPOS_PAGINA y MARCADOR_INFORME igual al de ensamblar.py
  W7 gráficos del informe: todo G.<tipo> de investigacion/graficos/*.js tiene plantilla de tarjeta (o está en
     informe.SOLO_DOCUMENTO), campos en informe.CAMPOS_GRAFICO y extractor en ensamblar.CLAVES_DATO; ningún
     G.<tipo> se define dos veces; toda plantilla de tarjeta tiene su G.* (informe.plantillas_sin_g vacío)
  W8 ningún gráfico del informe (salvo el adaptador _comun.js) usa helpers de la tarjeta que leen su DOM o sus variables CSS
     (H.color, H.rampa, H.rampaColor, H.halo, H.periodos, H.textoSobre, H.espacio, H.lienzo, H.leyenda,
     H.anotar, H.cabecera, H.verificar, document.getElementById)
  W9 el bloque común (agentRol, conReparacion, avisar, verificación mecánica, rechequeo) de hilo.js, dato.js,
     investigacion.js y video.js es copia exacta de scripts/workflow_comun.js (lo copia scripts/armar_workflows.py)
  W10 video.js: DURACIONES, TIPOS, FAMILIAS, VISUALES, MECANISMOS_EXPLICA, CIERRE_TIPOS, ENLACES y PUNTAJES son espejos literales de scripts/video.py, y el
     workflow no redefine las constantes del gate (CPS, COLA, RITMO_MAX_S, CARACTERES, DURACION_DEFECTO, VISUALES_DE,
     APERTURAS_PROHIBIDAS), que
     viven solo en video.py
  W11 noticias.js: SECCIONES es espejo literal de noticias.SECCIONES (los prefijos de los rastreadores)
  W12 historia.js: TIPOS (los de video.py más foto, cita y capitulo), FAMILIAS, VISUALES y PUNTAJES son espejos literales de
      scripts/historia.py

Uso: python3 scripts/check_workflows.py [--quiet]   · salida 0 ok · 1 diferencias
"""
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
from ensamblar import BEATS, HOOKS, MODOS, CLAVES_DATO, MARCADOR_INFORME  # noqa: E402
import informe  # noqa: E402  (TIPOS_GRAFICO, CAMPOS_GRAFICO, SOLO_DOCUMENTO, plantillas_sin_g, snake)

RE_PROHIBIDO = re.compile(r"\bH\.(color|rampa|rampaColor|halo|periodos|textoSobre|espacio|lienzo|leyenda|anotar|cabecera|verificar)\b|document\.getElementById\(")

WF = os.path.join(RAIZ, ".claude", "workflows")
ERRORES, AVISOS = [], []


def err(m): ERRORES.append(m)
def warn(m): AVISOS.append(m)


def fuente(nombre, opcional=False):
    ruta = os.path.join(WF, nombre)
    if not os.path.exists(ruta):
        (warn if opcional else err)("falta %s%s" % (os.path.relpath(ruta, RAIZ), " (aún no existe: /%s no estará disponible)" % nombre[:-3] if opcional else "")); return ""
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
    hilo, dato, ideas, inv = fuente("hilo.js"), fuente("dato.js"), fuente("ideas.js"), fuente("investigacion.js", opcional=True)
    if not (hilo and dato):
        return fin(quiet)
    tokens = json.load(open(os.path.join(RAIZ, "design", "tokens.json"), encoding="utf-8"))
    paletas = list(tokens.get("paletas", {}).keys())
    catalogo = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(RAIZ, "templates", "graficos", "*.html")))

    # W1 paletas
    for nombre, src in (("hilo.js", hilo), ("dato.js", dato), ("ideas.js", ideas), ("investigacion.js", inv)):
        if not src:
            continue
        p = lista(src, "PALETAS")
        if p is None:
            err("W1 %s: no se encontró `const PALETAS = [...]`" % nombre)
        elif sorted(p) != sorted(paletas):
            err("W1 %s PALETAS %s ≠ design/tokens.json %s" % (nombre, p, paletas))
    if ideas:  # W1 también: las enumeraciones de ideas.js frente a ideas.py
        import ideas as _ideas
        for const in ("AREAS", "FORMATOS", "ACCESOS"):
            v = lista(ideas, const)
            if v is None:
                err("W1 ideas.js: no se encontró `const %s = [...]`" % const)
            elif v != getattr(_ideas, const):
                err("W1 ideas.js %s %s ≠ ideas.%s %s" % (const, v, const, getattr(_ideas, const)))
    # W2 plantillas
    for nombre, src in (("hilo.js", hilo), ("dato.js", dato), ("investigacion.js", inv)):
        if not src:
            continue
        p = lista(src, "PLANTILLAS")
        if p is None:
            err("W2 %s: no se encontró `const PLANTILLAS = [...]`" % nombre)
        elif sorted(p) != catalogo:
            err("W2 %s PLANTILLAS ≠ templates/graficos/: sobran %s, faltan %s" % (nombre, sorted(set(p) - set(catalogo)), sorted(set(catalogo) - set(p))))
    # W3 hooks y beats
    for nombre, src in (("hilo.js", hilo), ("dato.js", dato), ("ideas.js", ideas), ("investigacion.js", inv)):
        if not src:
            continue
        h = lista(src, "HOOKS")
        if h is None:
            err("W3 %s: no se encontró `const HOOKS = [...]`" % nombre)
        elif h != HOOKS:
            err("W3 %s HOOKS %s ≠ ensamblar.HOOKS %s" % (nombre, h, HOOKS))
    for nombre, src in (("hilo.js", hilo), ("investigacion.js", inv)):
        if not src:
            continue
        b = lista(src, "BEATS")
        if b is None:
            err("W3 %s: no se encontró `const BEATS = [...]`" % nombre)
        elif b != BEATS:
            err("W3 %s BEATS %s ≠ ensamblar.BEATS %s" % (nombre, b, BEATS))
    # W4 bloques que deben ser idénticos en hilo.js y dato.js
    for etiqueta, extraer in (
        ("REQ", lambda s: bloque(s, "const REQ = {")),
        ("RE_LINK", lambda s: linea(s, "const RE_LINK")),
        ("RE_BAIT", lambda s: linea(s, "const RE_BAIT")),
        ("RE_SUPER", lambda s: linea(s, "const RE_SUPER")),
        ("pesoX", lambda s: bloque(s, "function pesoX(texto) {")),
    ):
        a = extraer(hilo)
        for otro, src in (("dato.js", dato), ("investigacion.js", inv)):
            if not src:
                continue
            c = extraer(src)
            if a is None or c is None:
                err("W4 %s: no se encontró en %s" % (etiqueta, "hilo.js" if a is None else otro))
            elif norm(a) != norm(c):
                err("W4 %s difiere entre hilo.js y %s (copia el bloque de uno al otro)" % (etiqueta, otro))
    # W5 modos: dato.js solo; hilo.js ∪ investigacion.js (cada workflow declara los modos que sirve)
    k = claves_modos(dato)
    if k is None:
        warn("W5 dato.js: aún no tiene `const MODOS = {…}` (modos de ensamblar.MODOS['dato']: %s)" % MODOS["dato"])
    elif sorted(k) != sorted(MODOS["dato"]):
        err("W5 dato.js MODOS %s ≠ ensamblar.MODOS['dato'] %s" % (k, MODOS["dato"]))
    kh, ki = claves_modos(hilo), (claves_modos(inv) if inv else [])
    if kh is None:
        warn("W5 hilo.js: aún no tiene `const MODOS = {…}`")
    else:
        if inv and ki is None:
            err("W5 investigacion.js: no se encontró `const MODOS = {…}`")
        ki = ki or []
        esperado = MODOS["hilo"] if inv else [m for m in MODOS["hilo"] if m != "investigacion"]
        if set(kh) & set(ki):
            err("W5 modos repetidos entre hilo.js e investigacion.js: %s" % sorted(set(kh) & set(ki)))
        if sorted(kh + ki) != sorted(esperado):
            err("W5 hilo.js ∪ investigacion.js MODOS %s ≠ ensamblar.MODOS['hilo'] %s" % (sorted(kh + ki), sorted(esperado)))
    # W6 espejos de investigacion.js
    if inv:
        tp = lista(inv, "TIPOS_PAGINA")
        if tp is None:
            err("W6 investigacion.js: no se encontró `const TIPOS_PAGINA = [...]`")
        elif sorted(tp) != sorted(informe.TIPOS_PAGINA):
            err("W6 investigacion.js TIPOS_PAGINA %s ≠ informe.TIPOS_PAGINA %s" % (sorted(tp), sorted(informe.TIPOS_PAGINA)))
        m = re.search(r"^const MARCADOR_INFORME = '([^']*)'", inv, re.M)
        if not m:
            err("W6 investigacion.js: no se encontró `const MARCADOR_INFORME = '…'`")
        elif m.group(1) != MARCADOR_INFORME:
            err("W6 investigacion.js MARCADOR_INFORME %r ≠ ensamblar.MARCADOR_INFORME %r" % (m.group(1), MARCADOR_INFORME))
    graficos_informe(catalogo)
    video_workflow()
    noticias_workflow()
    historia_workflow()
    return fin(quiet)


# Espejos de scripts/video.py en video.js y constantes que el workflow NO debe duplicar.
W10_LISTAS = ("DURACIONES", "TIPOS", "FAMILIAS", "VISUALES", "MECANISMOS_EXPLICA", "CIERRE_TIPOS", "ENLACES", "PUNTAJES")
W10_PROHIBIDAS = ("CPS", "COLA", "RITMO_MAX_S", "CARACTERES", "DURACION_DEFECTO", "VISUALES_DE", "APERTURAS_PROHIBIDAS")


def video_workflow():
    """W10: video.js refleja las listas de scripts/video.py y no redefine las constantes del gate."""
    vid = fuente("video.js", opcional=True)
    if not vid:
        return
    try:
        import video as VID
    except Exception as ex:  # video.py importa numeros_es y verificacion; si está a medias, se avisa como error
        err("W10 no se pudo importar scripts/video.py: %s" % ex)
        return
    for nombre in W10_LISTAS:
        js = lista(vid, nombre)
        if js is None:
            err("W10 video.js: no se encontró `const %s = [...]`" % nombre)
            continue
        if not hasattr(VID, nombre):
            err("W10 scripts/video.py no define %s (video.js lo espera)" % nombre)
            continue
        py = list(getattr(VID, nombre))
        if js != py:
            err("W10 video.js %s %s ≠ video.%s %s" % (nombre, js, nombre, py))
    for nombre in W10_PROHIBIDAS:
        if re.search(r"^const %s\b" % nombre, vid, re.M):
            err("W10 video.js define `const %s`: las constantes del gate viven solo en scripts/video.py" % nombre)


def noticias_workflow():
    """W11: noticias.js refleja las secciones de scripts/noticias.py."""
    src = fuente("noticias.js", opcional=True)
    if not src:
        return
    try:
        import noticias as NOT
    except Exception as ex:  # noqa: BLE001
        err("W11 no se pudo importar scripts/noticias.py: %s" % ex)
        return
    js = lista(src, "SECCIONES")
    if js is None:
        err("W11 noticias.js: no se encontró `const SECCIONES = [...]`")
    elif js != list(NOT.SECCIONES):
        err("W11 noticias.js SECCIONES %s ≠ noticias.SECCIONES %s" % (js, list(NOT.SECCIONES)))


def historia_workflow():
    """W12: historia.js refleja las listas de scripts/historia.py."""
    src = fuente("historia.js", opcional=True)
    if not src:
        return
    try:
        import historia as HI
    except Exception as ex:  # noqa: BLE001
        err("W12 no se pudo importar scripts/historia.py: %s" % ex)
        return
    esperado = {"TIPOS": list(HI.VD.TIPOS) + [t for t in HI.TIPOS_PROPIOS if t not in HI.VD.TIPOS],
                "FAMILIAS": list(HI.FAMILIAS), "VISUALES": list(HI.VISUALES), "PUNTAJES": list(HI.PUNTAJES)}
    for nombre, py in esperado.items():
        js = lista(src, nombre)
        if js is None:
            err("W12 historia.js: no se encontró `const %s = [...]`" % nombre)
        elif js != py:
            err("W12 historia.js %s %s ≠ historia.py %s" % (nombre, js, py))


def graficos_informe(catalogo):
    """W7 y W8: el motor de gráficos del informe frente al catálogo de tarjetas."""
    tipos, cat = informe.TIPOS_GRAFICO, {informe.snake(c) for c in catalogo}
    sobran = sorted(tipos - cat - informe.SOLO_DOCUMENTO)
    if sobran:
        err("W7 G.* sin plantilla de tarjeta ni en informe.SOLO_DOCUMENTO: %s" % ", ".join(sobran))
    faltan = sorted(informe.plantillas_sin_g())
    if faltan:
        err("W7 plantillas de tarjeta sin G.* en investigacion/graficos/ (el informe debe poder dibujar todo el catálogo): %s" % ", ".join(faltan))
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

    # W9 el bloque común de hilo.js, dato.js e investigacion.js es copia exacta de scripts/workflow_comun.js
    import armar_workflows as AW
    src = AW.bloque_fuente()
    for w in AW.WORKFLOWS:
        with open(os.path.join(RAIZ, ".claude", "workflows", w), encoding="utf-8") as fh:
            p = AW.partes(fh.read())
        if not p:
            err("W9 %s: faltan los marcadores del bloque común (%s … %s)" % (w, AW.INI, AW.FIN))
        elif p[1] != src:
            err("W9 %s: el bloque común difiere de scripts/workflow_comun.js (edita ese archivo y corre python3 scripts/armar_workflows.py)" % w)


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
