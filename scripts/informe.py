#!/usr/bin/env python3
"""Informe de investigación: <dir>/informe.json -> <salida>/informe.html + informe.pdf.

Ensambla investigacion/base.html con:
  · las paletas de design/tokens.json (tarjeta + papel_tinta/papel_barra),
  · el bloque `const H` de templates/base.html (marcadores H:INICIO/H:FIN),
  · los gráficos de investigacion/graficos/*.js (+ GEOMETRIA de design/mapa_geometria.svg si hay mapa),
  · las páginas de investigacion/paginas/*.js,
  · el informe.json RESUELTO: números de página, «Figura N»/«Tabla N», referencias {fig:id} {tabla:id}
    {pag:id}, índice, capítulos de la portada y la tabla de cifras del método (desde datos.json).
Las figuras `tarjeta` con `plantilla` se arman con las plantillas de templates/graficos/ (nuevo_visual +
DATA como materializar) y se renderizan con render.js --check; las que traen `desde` copian un PNG ya
publicado. Después llama a scripts/render_informe.js (PDF Letter, checks P1–P5 con --check).

Gráficos del documento: `grafico.tipo` admite el nombre de la plantilla de tarjeta (`barras-v`) o su forma
snake (`barras_v`); los tipos válidos son los `G.<tipo>` definidos en investigacion/graficos/*.js (W7 los cruza
con el catálogo de tarjetas) y `datos` es el mismo objeto que `visual.datos` del guion (graficos.md).
Una página `tarjetas` con `desde_hilo: "<carpeta del hilo>"` se expande sola desde su hilo.json.

Gates (exit 1 si alguno falla; el informe no se escribe):
  I1 tipos de página, bloque, figura y gráfico conocidos, con sus campos obligatorios (CAMPOS_GRAFICO por
     tipo de gráfico); ids únicos; meta.numero (si va) de dos dígitos
  I2 toda cifra o serie con `id` existe en los datos.json declarados, es verificada|ajustada y su valor
     coincide; además, en todo gráfico y toda figura `tarjeta` con datos, cada número de los datos está entre
     los valores de sus cifras (`id`, `cifra_ids`, ids anidados), cotejado con ensamblar.CLAVES_DATO
     (regla de oro 1: ninguna cifra no_confirmada en el informe)
  I3 ningún texto lleva URL (http/https), emoji ni «en suma»
  I4 toda figura y tabla tiene `fuente`
  I5 toda referencia {fig:} {Fig:} {fign:} {tabla:} {Tabla:} {pag:} resuelve ({paleta} = nombre de la paleta)
  I6 la paleta existe en tokens · 1 a 160 páginas (las auditorías exhaustivas pasan de 100)
  I7 (solo AVISO) números del cuerpo (párrafos, leads, tesis, hallazgos, cierre) que no son una cifra
     verificada, un año ni un derivado declarado en un pie o nota con ÷ × − o «cálculo propio»

Uso:
  python3 scripts/informe.py <dir con informe.json> [--salida DIR] [--paleta X] [--check] [--sin-pdf] [--png DIR]
Salida: 0 ok · 1 gate o render fallido · 2 uso incorrecto
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import build_mapa  # noqa: E402  (extraer() de la geometría)
import ensamblar  # noqa: E402  (CLAVES_DATO, catalogo_plantillas: el mismo cotejo que G4)
import verificacion as VM  # noqa: E402  (sueltos: el mismo cotejo con tolerancia que G10)
import materializar  # noqa: E402  (RE_DATA, data_de)
import nuevo_visual  # noqa: E402  (ensamblar)

DIR_INV = os.path.join(RAIZ, "investigacion")
BASE = os.path.join(DIR_INV, "base.html")
BASE_TARJETA = os.path.join(RAIZ, "templates", "base.html")
TOKENS = os.path.join(RAIZ, "design", "tokens.json")
FONTS = os.path.join(RAIZ, "design", "fonts")

TIPOS_PAGINA = {
    # tipo: campos obligatorios
    "portada": ["titulo"], "indice": [], "resumen": ["tesis", "cifras"], "tablero": ["cifras"],
    "capitulo": ["numero", "titulo"], "cuerpo": ["bloques"], "apaisada": ["lateral", "figura"],
    "cronologia": ["titulo", "eventos", "fuente"], "conclusiones": ["hallazgos"], "metodo": ["cifras"],
    "glosario": ["terminos"], "anexo": ["titulo", "bloques"], "tarjetas": ["titulo", "items"],
    "contraportada": ["lema"],
}
VARIANTES_CAPITULO = {"banda", "dividida", "destacado"}
TIPOS_BLOQUE = {"titulo", "texto", "figura", "figuras", "tabla", "cita", "caja", "lectura", "notas"}
TIPOS_FIGURA = {"panel", "papel", "tarjeta"}
# Gráficos del documento: los G.<tipo> definidos en investigacion/graficos/*.js (fuente de verdad; sin lista literal).
RE_G = re.compile(r"^G\.(\w+) = ", re.M)
SOLO_DOCUMENTO = {"chispa", "cuadros", "comparacion", "columnas"}  # G.* sin plantilla de tarjeta (tablero y columnas verticales)
snake = lambda t: str(t or "").strip().replace("-", "_")  # noqa: E731
kebab = lambda t: str(t or "").strip().replace("_", "-")  # noqa: E731


def tipos_grafico():
    out = set()
    for ruta in glob.glob(os.path.join(DIR_INV, "graficos", "*.js")):
        out |= set(RE_G.findall(open(ruta, encoding="utf-8").read()))
    return out


def plantillas_sin_g():
    """Plantillas de tarjeta que aún no tienen G.<tipo> en el documento (se usan solo como figura `tarjeta`)."""
    return {snake(p) for p in ensamblar.catalogo_plantillas()} - TIPOS_GRAFICO


TIPOS_GRAFICO = tipos_grafico()
# Campos obligatorios por tipo de gráfico (mismos nombres que el contrato de la tarjeta, graficos.md).
# Casos especiales en validar(): cascada exige inicio o fin; mapa exige valores o marcados; linea/multiples con
# yDesdeCero:false y pesas con desdeCero:false exigen `nota` en la figura (como la tarjeta).
CAMPOS_GRAFICO = {
    "barras_v": ["etiquetas", "valores"], "barras_h": ["items"], "divergente": ["items"],
    "agrupadas": ["etiquetas", "series"], "columnas": ["etiquetas", "series"], "bullet": ["items"],
    "apilada": ["etiquetas", "partes"], "area_apilada": ["etiquetasX", "partes"],
    "piramide": ["grupos", "izquierda", "derecha"], "linea": ["etiquetas", "series"],
    "multiples": ["etiquetasX", "paneles"], "combinado": ["etiquetas", "barras", "linea"],
    "pendiente": ["fechas", "items"], "pesas": ["fechas", "items"], "antes_despues": ["antes", "despues"],
    "cascada": ["pasos"], "cifra": ["cifra"], "waffle": ["porcentaje", "cifra"],
    "pictograma": ["total", "destacado", "texto"], "dona": ["partes"], "treemap": ["partes"],
    "hemiciclo": ["total", "bloques"], "embudo": ["etapas", "misma_cohorte"],
    "dispersion": ["puntos", "ejeX", "ejeY"], "calor": ["filas", "columnas", "valores"],
    "linea_tiempo": ["eventos"], "mapa": [],
    "chispa": ["etiquetas", "valores"], "cuadros": ["total", "marcados"], "comparacion": ["items"],
}
# Extractor de números de los datos por tipo: el de la plantilla de tarjeta (ensamblar.CLAVES_DATO, gate G4).
CLAVES_DOC = {"columnas": "agrupadas", "chispa": "barras-v", "comparacion": "barras-h"}


def numeros_de_datos(tipo, datos):
    """Números que un gráfico afirma (los que se cotejan con las cifras), según CLAVES_DATO de su plantilla."""
    if tipo == "cuadros":
        nums = [datos.get("total"), datos.get("marcados")]
    else:
        fn = ensamblar.CLAVES_DATO.get(CLAVES_DOC.get(tipo, kebab(tipo)))
        if not fn:
            return []
        try:
            nums = fn(datos)
        except Exception:
            return []
    return [x for x in nums if isinstance(x, (int, float)) and not isinstance(x, bool)]


def valores_de_cifra(c):
    """Valores que respalda una cifra de datos.json: valor (final), serie[].v, partes[].valor. El valor_original de
    una cifra ajustada NO respalda nada: es el número que el verificador corrigió."""
    out = [c["valor"]] if isinstance(c.get("valor"), (int, float)) else []
    out += [p.get("v") for p in c.get("serie") or [] if isinstance(p, dict) and isinstance(p.get("v"), (int, float))]
    out += [p.get("valor") for p in c.get("partes") or [] if isinstance(p, dict) and isinstance(p.get("valor"), (int, float))]
    return out


def ids_de(obj):
    """Ids de cifra dentro de un `grafico` o de los `datos` de una tarjeta: `id`, `cifra_ids` y los anidados."""
    out = []
    if isinstance(obj, list):
        for v in obj:
            out += ids_de(v)
    elif isinstance(obj, dict):
        if isinstance(obj.get("id"), str):
            out.append(obj["id"])
        for i in obj.get("cifra_ids") or []:
            if isinstance(i, str):
                out.append(i)
        for k, v in obj.items():
            if k not in ("id", "cifra_ids", "marcadores", "anotaciones", "guias", "leyenda") and not k.startswith("_"):
                out += ids_de(v)  # marcadores[].id y anotaciones son presentación (departamentos, rótulos), no cifras
    return out
VEREDICTOS_OK = {"verificada", "ajustada"}
SIN_NUMERO = {"portada", "contraportada"}
RE_URL = re.compile(r"https?://", re.I)
RE_EN_SUMA = re.compile(r"\ben suma\b", re.I)  # muletilla vetada (CLAUDE.md, Estilo)
RE_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
RE_REF = re.compile(r"\{(fig|Fig|fign|tabla|Tabla|pag):([A-Za-z0-9_-]+)\}")
# {fig:id} «figura 5» · {Fig:id} «Figura 5» · {fign:id} «Fig. 5» · {tabla:id} «tabla 1» · {Tabla:id} «Tabla 1» · {pag:id} «13» (página, figura o tabla)
RE_NUM = re.compile(r"[−-]?\d[\d,]*(?:\.\d+)?")


class Gate:
    def __init__(self):
        self.fallos = []

    def __call__(self, codigo, msg):
        self.fallos.append("%s %s" % (codigo, msg))


def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- recorridos
def figuras_de_pagina(P):
    """Figuras y tablas de una página, en orden de lectura: [(kind, obj)] con kind figura|tabla."""
    out = []

    def bloques(lista):
        for B in lista or []:
            if B.get("b") == "figura":
                out.append(("figura", B))
            elif B.get("b") == "figuras":
                for f in B.get("items", []):
                    out.append(("figura", f))
            elif B.get("b") == "tabla":
                out.append(("tabla", B))
    bloques(P.get("bloques"))
    bloques(P.get("lateral"))
    if P.get("tipo") == "apaisada" and P.get("figura"):
        out.append(("figura", P["figura"]))
    return out


def textos(obj, ruta="informe"):
    """Todas las cadenas del objeto con su ruta (para I3 y para resolver referencias)."""
    if isinstance(obj, str):
        yield ruta, obj
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from textos(v, "%s[%d]" % (ruta, i))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if not k.startswith("_"):
                yield from textos(v, "%s.%s" % (ruta, k))


def reemplazar_textos(obj, fn):
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, list):
        return [reemplazar_textos(v, fn) for v in obj]
    if isinstance(obj, dict):
        return {k: (v if k.startswith("_") else reemplazar_textos(v, fn)) for k, v in obj.items()}
    return obj


def con_id(obj, etiquetas=None):
    """Objetos con clave `id` que representan cifras o series (no páginas ni figuras). Una serie anidada
    (series[], partes[], paneles[], izquierda/derecha, barras/linea) hereda las etiquetas del gráfico."""
    if isinstance(obj, list):
        for v in obj:
            yield from con_id(v, etiquetas)
    elif isinstance(obj, dict):
        et = obj.get("etiquetas") or obj.get("etiquetasX") or obj.get("grupos") or etiquetas
        if "id" in obj and ("valor" in obj or "valores" in obj or "items" in obj) and "b" not in obj and obj.get("tipo") not in TIPOS_PAGINA:
            yield dict(obj, etiquetas=et) if et and "etiquetas" not in obj else obj
        for k, v in obj.items():
            if not k.startswith("_"):
                yield from con_id(v, et)


def numeros(s):
    return [float(m.replace("−", "-").replace(",", "")) for m in RE_NUM.findall(str(s))]


def graficos_de_pagina(P):
    """[(etiqueta, tipo snake, datos, dueño)] de los gráficos de la página: figuras papel/panel (grafico),
    figuras tarjeta con plantilla+datos (tipo = la plantilla) y cifras del tablero."""
    out = []
    for kind, f in figuras_de_pagina(P):
        if kind != "figura":
            continue
        if f.get("tipo") == "tarjeta":
            if f.get("plantilla") and isinstance(f.get("datos"), dict):
                out.append(("figura %s" % (f.get("id") or f.get("plantilla")), snake(f["plantilla"]), f["datos"], f))
        elif isinstance(f.get("grafico"), dict):
            out.append(("figura %s" % (f.get("id") or f["grafico"].get("tipo")), snake(f["grafico"].get("tipo")), f["grafico"], f))
    if P.get("tipo") == "tablero":
        for c in P.get("cifras", []):
            if isinstance(c.get("grafico"), dict):
                out.append(("cifra del tablero %r" % c.get("kicker"), snake(c["grafico"].get("tipo")), c["grafico"], c))
    return out


def validar_grafico(i, grafico, figura, g):
    """I1 de un gráfico del documento: tipo conocido y campos obligatorios (CAMPOS_GRAFICO)."""
    if not isinstance(grafico, dict):
        g("I1", "página %d: figura sin `grafico`" % i)
        return
    t = snake(grafico.get("tipo"))
    if t not in TIPOS_GRAFICO:
        g("I1", "página %d: gráfico desconocido %r (hay: %s)" % (i, grafico.get("tipo"), ", ".join(sorted(TIPOS_GRAFICO))))
        return
    faltan = [c for c in CAMPOS_GRAFICO.get(t, []) if grafico.get(c) in (None, "", [], {})]
    if t == "cascada" and not (grafico.get("inicio") or grafico.get("fin")):
        faltan.append("inicio o fin")
    if t == "mapa" and not (grafico.get("valores") or grafico.get("marcados")):
        faltan.append("valores (coroplético) o marcados")
    if faltan:
        g("I1", "página %d: gráfico %s sin %s" % (i, t, ", ".join(faltan)))
    sin_cero = (t in ("linea", "multiples") and grafico.get("yDesdeCero") is False) or (t == "pesas" and grafico.get("desdeCero") is False)
    if sin_cero and not str(figura.get("nota") or "").strip():
        g("I1", "página %d: gráfico %s con eje que no parte de cero exige `nota` en la figura (como la tarjeta)" % (i, t))


def normalizar(R):
    """grafico.tipo: nombre de plantilla (kebab) → snake; etiquetas ↔ etiquetasX. Las figuras `tarjeta`
    conservan `plantilla` en kebab (la consume nuevo_visual.ensamblar)."""
    def norm_g(g):
        if not isinstance(g, dict):
            return
        if g.get("tipo"):
            g["tipo"] = snake(g["tipo"])
        if "etiquetasX" in g and "etiquetas" not in g:
            g["etiquetas"] = g["etiquetasX"]
        elif "etiquetas" in g and "etiquetasX" not in g:
            g["etiquetasX"] = g["etiquetas"]
    for P in R.get("paginas") or []:
        for kind, f in figuras_de_pagina(P):
            if kind == "figura" and f.get("tipo") != "tarjeta":
                norm_g(f.get("grafico"))
        if P.get("tipo") == "tablero":
            for c in P.get("cifras", []):
                norm_g(c.get("grafico"))
    return R


RE_DATA_JSON = re.compile(r"const DATA = (\{.*?\n\});\n", re.S)  # los tuit_N.html los escribe materializar.py con json.dumps
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MAX_TARJETAS_CON_TUIT, MAX_TARJETAS = 8, 12


def expandir_desde_hilo(P, g):
    """Página `tarjetas` con `desde_hilo`: items (desde, n, beat, titulo, alt) y `tuit` desde <carpeta>/hilo.json
    y el DATA de cada tuit_N.html. `tuits: [n…]` elige un subconjunto (para partir en dos páginas); los `items`
    escritos a mano mandan. La caja `tuit` se omite sola con más de 8 tarjetas."""
    carpeta = P.get("desde_hilo")
    ruta = os.path.join(RAIZ, carpeta, "hilo.json")
    if not os.path.exists(ruta):
        g("I1", "tarjetas: desde_hilo %r no tiene hilo.json" % carpeta)
        return
    h = cargar_json(ruta)
    tuits = [t for t in h.get("tuits", []) if t.get("imagen")]
    if P.get("tuits"):
        tuits = [t for t in tuits if t.get("n") in set(P["tuits"])]
    total = h.get("n_tuits") or len(h.get("tuits", []))
    items = []
    for t in tuits:
        html = os.path.join(RAIZ, carpeta, "tuit_%d.html" % t["n"])
        m = RE_DATA_JSON.search(open(html, encoding="utf-8").read()) if os.path.exists(html) else None
        d = {}
        if m:
            try:
                d = json.loads(m.group(1))
            except ValueError:
                d = {}
        titulo = " ".join(d.get("titular") or []) or d.get("kicker") or (t.get("alt_text") or "")[:80]
        items.append({"desde": "%s/%s" % (carpeta.rstrip("/"), t["imagen"]), "n": "%d/%d" % (t["n"], total), "beat": t.get("beat", ""), "titulo": titulo, "alt": t.get("alt_text", "")})
    if len(items) > MAX_TARJETAS:
        g("I1", "tarjetas: %d tarjetas no caben en una página (máx. %d): parte la página con `tuits: [n…]`" % (len(items), MAX_TARJETAS))
    if not P.get("items"):
        P["items"] = items
    if "tuit" not in P and len(items) <= MAX_TARJETAS_CON_TUIT:
        t1 = (h.get("tuits") or [{}])[0]
        limpio = lambda x: re.sub(r"[ \t]{2,}", " ", RE_EMOJI.sub("", x)).strip()  # noqa: E731  (el tuit puede llevar emoji; el PDF no)
        partes = [limpio(x) for x in str(t1.get("texto") or "").split("\n\n") if limpio(x)]
        fecha = str(h.get("fecha") or "")
        try:
            a, mm, dd = fecha.split("-")
            publicado = "Publicado en X por %s · %d de %s de %s" % (h.get("handle") or "@DerekUrizar", int(dd), MESES[int(mm) - 1], a)
        except ValueError:
            publicado = "Publicado en X por %s" % (h.get("handle") or "@DerekUrizar")
        if partes:
            P["tuit"] = {"gancho": partes[0], "texto": " ".join(partes[1:]), "publicado": publicado}
    P.setdefault("titulo", "Las tarjetas del hilo")
    P.pop("desde_hilo", None)


RE_DERIVADO = re.compile(r"[÷×]|c[áa]lculo propio|calculad[oa]", re.I)
RUTAS_CUERPO = re.compile(r"\.(parrafos\[\d+\]|lead|tesis|cierre|hallazgos\[\d+\]\.texto)$")


def avisos_texto(R, cifras):
    """I7 (aviso): números del cuerpo que no son cifra verificada (redondeada como se escribió, a cualquier escala),
    derivado simple de dos de ellas, año, fecha, entero ≤ 12 ni derivado declarado (un pie, nota o margen con ÷ × −
    o «cálculo propio» en la misma página). Un «45 %» ya no pasa por ser entero."""
    permitidos = set()
    for c in cifras.values():
        if c.get("veredicto") in VEREDICTOS_OK:
            permitidos |= {round(abs(float(v)), 6) for v in valores_de_cifra(c)}
    con_factor = sorted({(round(abs(float(v)), 6), VM.factor_unidad(c.get("unidad"))) for c in cifras.values()
                         if c.get("veredicto") in VEREDICTOS_OK for v in valores_de_cifra(c)})
    titulares = [c.get("valor") for c in cifras.values() if c.get("veredicto") in VEREDICTOS_OK and c.get("tipo") != "serie"][:60]
    avisos = []
    for i, P in enumerate(R.get("paginas") or [], 1):
        declarados = set()
        for ruta, s in textos(P, "p"):
            if RE_DERIVADO.search(s):
                declarados |= {round(abs(n), 6) for n in numeros(s)}
        for ruta, s in textos(P, "p"):
            if not RUTAS_CUERPO.search(ruta):
                continue
            sueltos = VM.sueltos(s, con_factor + [(x, None) for x in sorted(declarados)], titulares)  # tolerancia de redondeo y escala (verificacion.py)
            if sueltos:
                avisos.append("I7 página %d (%s): %s no es cifra verificada ni derivado declarado" % (i, ruta[2:], ", ".join(sueltos[:6])))
    return avisos


# ---------------------------------------------------------------- gates
def validar(R, tk, cifras, g):
    meta, paginas = R.get("meta") or {}, R.get("paginas") or []
    # I6
    if meta.get("paleta") not in tk["paletas"]:
        g("I6", "paleta %r no existe en design/tokens.json" % meta.get("paleta"))
    if not 1 <= len(paginas) <= 160:
        g("I6", "el informe tiene %d páginas (1 a 160)" % len(paginas))
    for campo in ("titulo", "corrido", "pie", "handle"):
        if not meta.get(campo):
            g("I1", "meta.%s es obligatorio" % campo)
    if meta.get("numero") is not None and not re.fullmatch(r"\d{2,}", str(meta.get("numero"))):
        g("I1", "meta.numero debe ser el número del informe con dos dígitos (%r)" % meta.get("numero"))
    # I1
    ids_pag, ids_fig = set(), set()
    for i, P in enumerate(paginas, 1):
        t = P.get("tipo")
        if t not in TIPOS_PAGINA:
            g("I1", "página %d: tipo desconocido %r (hay: %s)" % (i, t, ", ".join(sorted(TIPOS_PAGINA))))
            continue
        for campo in TIPOS_PAGINA[t]:
            if P.get(campo) in (None, "", []):
                g("I1", "página %d (%s): falta %s" % (i, t, campo))
        if t == "capitulo" and P.get("variante", "banda") not in VARIANTES_CAPITULO:
            g("I1", "página %d: variante de capítulo desconocida %r" % (i, P.get("variante")))
        if t == "capitulo" and P.get("variante") == "destacado" and not (P.get("dato") and P.get("fuente")):
            g("I1", "página %d: el capítulo destacado necesita dato y fuente" % i)
        if P.get("id"):
            if P["id"] in ids_pag:
                g("I1", "id de página repetido: %s" % P["id"])
            ids_pag.add(P["id"])
        for lista in (P.get("bloques"), P.get("lateral")):
            for B in lista or []:
                if B.get("b") not in TIPOS_BLOQUE:
                    g("I1", "página %d: bloque desconocido %r" % (i, B.get("b")))
        for kind, f in figuras_de_pagina(P):
            if f.get("id"):
                if f["id"] in ids_fig:
                    g("I1", "id de figura/tabla repetido: %s" % f["id"])
                ids_fig.add(f["id"])
            if kind == "tabla":
                if not f.get("columnas") or not f.get("filas"):
                    g("I1", "página %d: tabla sin columnas o filas" % i)
                for fila in f.get("filas", []):
                    if len(fila.get("c", [])) != len(f.get("columnas", [])):
                        g("I1", "página %d: fila de tabla con %d celdas para %d columnas" % (i, len(fila.get("c", [])), len(f.get("columnas", []))))
            else:
                ft = f.get("tipo", "papel")
                if ft not in TIPOS_FIGURA:
                    g("I1", "página %d: figura de tipo desconocido %r" % (i, ft))
                elif ft == "tarjeta":
                    if not (f.get("desde") or f.get("plantilla")):
                        g("I1", "página %d: figura tarjeta necesita `desde` (PNG) o `plantilla` + `datos`" % i)
                else:
                    validar_grafico(i, f.get("grafico"), f, g)
            # I4
            if not f.get("fuente"):
                g("I4", "página %d: %s %s sin fuente" % (i, kind, f.get("id") or ""))
        if t == "tablero":
            for c in P.get("cifras", []):
                if not isinstance(c.get("grafico"), dict):
                    g("I1", "página %d: cifra del tablero sin gráfico" % i)
                else:
                    validar_grafico(i, c["grafico"], c, g)
                if not c.get("fuente"):
                    g("I4", "página %d: cifra del tablero %r sin fuente" % (i, c.get("kicker")))
        if t == "resumen":
            for c in P.get("cifras", []):
                if not c.get("fuente"):
                    g("I4", "página %d: cifra del resumen %r sin fuente" % (i, c.get("kicker")))
        if t == "tarjetas":
            for it in P.get("items", []):
                if not it.get("desde") or not os.path.exists(os.path.join(RAIZ, it["desde"])):
                    g("I1", "página %d: tarjeta sin PNG `desde` existente (%r)" % (i, it.get("desde")))
    # I2
    for obj in con_id(paginas):
        cid = obj["id"]
        c = cifras.get(cid)
        if not c:
            g("I2", "la cifra %s no está en ningún datos.json de meta.datos" % cid)
            continue
        if c.get("veredicto") not in VEREDICTOS_OK:
            g("I2", "la cifra %s tiene veredicto %r: solo verificada|ajustada entra al informe" % (cid, c.get("veredicto")))
        if "items" in obj and "valores" not in obj and any(isinstance(it.get("valor"), (int, float)) for it in obj["items"] if isinstance(it, dict)):
            partes = {p.get("nombre"): p.get("valor") for p in c.get("partes") or []}
            cruces = [(it.get("nombre"), it.get("valor")) for it in obj["items"] if isinstance(it, dict) and it.get("nombre") in partes and isinstance(it.get("valor"), (int, float))]
            if not cruces:
                g("I2", "los items de %s no coinciden por nombre con ninguna parte de datos.json" % cid)
            for nom, v in cruces:
                if partes[nom] is None or abs(float(partes[nom]) - float(v)) > 1e-9:
                    g("I2", "%s: %s=%s pero datos.json dice %s" % (cid, nom, v, partes[nom]))
        elif "valores" in obj:
            serie = {str(p.get("p")): p.get("v") for p in c.get("serie") or []}
            if not serie:  # desglose por categorías: se cruza por nombre de etiqueta
                serie = {str(p.get("nombre")): p.get("valor") for p in c.get("partes") or []}
            et = [str(e) for e in (obj.get("claves") or obj.get("etiquetas", []))]  # claves: nombres en datos.json si la etiqueta es abreviada
            cruces = [(e, v) for e, v in zip(et, obj["valores"]) if e in serie and v is not None]
            if not cruces:
                g("I2", "la serie %s no comparte ningún periodo con datos.json (%s)" % (cid, ", ".join(et)))
            for e, v in cruces:
                if serie[e] is None or abs(float(serie[e]) - float(v)) > 1e-9:
                    g("I2", "la serie %s dice %s=%s pero datos.json dice %s" % (cid, e, v, serie[e]))
        elif "valor" in obj:
            vf = c.get("valor")
            if isinstance(vf, (int, float)) and not any(abs(n - float(vf)) < 1e-9 or abs(abs(n) - abs(float(vf))) < 1e-9 for n in numeros(obj["valor"])):
                g("I2", "la cifra %s se muestra como %r pero su valor final es %s" % (cid, obj["valor"], vf))
    # I2 por contrato: cada número de los datos de un gráfico (o de una figura tarjeta) está en sus cifras.
    for i, P in enumerate(paginas, 1):
        for etiqueta, tipo, datos, dueño in graficos_de_pagina(P):
            ids = []
            for x in ids_de(datos) + [x for x in (dueño.get("cifra_ids") or []) if isinstance(x, str)]:
                if x not in ids:
                    ids.append(x)
            if not ids:
                continue
            permitidos, falta = set(), False
            for cid in ids:
                c = cifras.get(cid)
                if not c:
                    g("I2", "página %d, %s: la cifra %s no está en ningún datos.json de meta.datos" % (i, etiqueta, cid)); falta = True
                elif c.get("veredicto") not in VEREDICTOS_OK:
                    g("I2", "página %d, %s: la cifra %s tiene veredicto %r" % (i, etiqueta, cid, c.get("veredicto"))); falta = True
                else:
                    permitidos |= {round(abs(float(v)), 6) for v in valores_de_cifra(c)}
            if falta:
                continue
            sueltos = sorted({round(abs(float(x)), 6) for x in numeros_de_datos(tipo, datos)} - permitidos)
            if sueltos:
                g("I2", "página %d, %s (%s): números sin respaldo en %s: %s" % (i, etiqueta, tipo, ", ".join(ids), ", ".join("%g" % x for x in sueltos[:8])))
    # I3
    for ruta, s in textos(R):
        if RE_URL.search(s):
            g("I3", "%s lleva una URL" % ruta)
        if RE_EMOJI.search(s):
            g("I3", "%s lleva un emoji (no se renderiza en el PDF)" % ruta)
        if RE_EN_SUMA.search(s):
            g("I3", "%s dice «en suma»: está vetado (la sección de cierre se titula «Conclusiones»)" % ruta)


# ---------------------------------------------------------------- resolución
# Índice largo: la lista de figuras y tablas va en hojas de continuación del índice (INDICE_FIGS_HOJA por hoja)
# cuando hay más de INDICE_CAPS capítulos o más de INDICE_FIGS entradas.
INDICE_CAPS, INDICE_FIGS, INDICE_FIGS_HOJA = 6, 24, 40


def continuar_indice(paginas):
    """Inserta tras la página `indice` las hojas de continuación de la lista de figuras (idempotente)."""
    paginas[:] = [P for P in paginas if not P.get("_indice_cont")]
    pos = next((i for i, P in enumerate(paginas) if P["tipo"] == "indice"), None)
    if pos is None:
        return
    n = sum(1 for P in paginas for _, f in figuras_de_pagina(P) if f.get("indice") is not False)
    caps = sum(1 for P in paginas if P["tipo"] == "capitulo" and P.get("indice") is not False)
    if caps <= INDICE_CAPS and n <= INDICE_FIGS:
        return
    hojas = max(1, -(-n // INDICE_FIGS_HOJA))
    por_hoja = -(-n // hojas)  # reparto parejo entre las hojas
    paginas[pos]["_hojas_figuras"] = hojas
    for k in range(hojas):
        paginas.insert(pos + 1 + k, {"tipo": "indice", "titulo": "Figuras y tablas", "_indice_cont": k + 1, "_hojas_figuras": hojas, "_por_hoja": por_hoja})


def resolver(R, cifras, g):
    paginas = R["paginas"]
    continuar_indice(paginas)
    refs = {k: {} for k in ("fig", "Fig", "fign", "tabla", "Tabla", "pag")}
    nfig = ntab = 0
    lista_figuras = []
    for i, P in enumerate(paginas, 1):
        P["_n"] = i
        P["_n_texto"] = "%02d" % i
        P["_mostrar_numero"] = P["tipo"] not in SIN_NUMERO
        if P.get("id"):
            refs["pag"][P["id"]] = "%02d" % i
        for kind, f in figuras_de_pagina(P):
            if kind == "tabla":
                if f.get("numero"):
                    f["_n"] = "Tabla " + f["numero"]
                else:
                    ntab += 1
                    f["_n"] = "Tabla %d" % ntab
                corto = f["_n"]
            else:
                nfig += 1
                f["_n"] = "Figura %d" % nfig
                corto = "Fig. %d" % nfig
            if f.get("id"):
                refs["pag"].setdefault(f["id"], "%02d" % i)  # {pag:id} también da la página de una figura o tabla
                if kind == "figura":
                    refs["fig"][f["id"]], refs["Fig"][f["id"]], refs["fign"][f["id"]] = f["_n"].lower(), f["_n"], corto
                else:
                    refs["tabla"][f["id"]], refs["Tabla"][f["id"]] = f["_n"][0].lower() + f["_n"][1:], f["_n"]
            if f.get("indice") is False:
                continue
            titulo = f.get("indice") or (" ".join(f["titular"]) if isinstance(f.get("titular"), list) else f.get("titular")) or f.get("titulo") or f.get("pie") or ""
            lista_figuras.append({"no": corto, "titulo": titulo, "pag": "%02d" % i})

    nombre_paleta = R["meta"].get("_paleta_nombre", R["meta"].get("paleta", ""))

    def sustituir(s):
        s = s.replace("{paleta}", nombre_paleta)

        def r(m):
            kind, ident = m.group(1), m.group(2)
            if ident not in refs[kind]:
                g("I5", "referencia {%s:%s} sin destino" % (kind, ident))
                return m.group(0)
            return refs[kind][ident]
        return RE_REF.sub(r, s)

    R["paginas"] = paginas = reemplazar_textos(paginas, sustituir)
    # Re-asignar los campos privados (reemplazar_textos conserva las claves _*)
    capitulos = [P for P in paginas if P["tipo"] == "capitulo"]
    for P in paginas:
        if P["tipo"] == "portada":
            P["_capitulos"] = [{"numero": c["numero"], "titulo": c.get("titulo_corto") or c["titulo"]} for c in capitulos]
        if P["tipo"] == "indice":
            entradas, anexos = [], []
            for Q in paginas:
                ind = Q.get("indice")
                if Q["tipo"] == "capitulo" and ind is not False:
                    entradas.append({"clase": "capitulo", "numero": Q["numero"], "titulo": Q.get("titulo_corto") or Q["titulo"], "desc": Q.get("descripcion", ""), "pag": Q["_n_texto"]})
                elif isinstance(ind, dict):
                    (anexos if ind.get("clase") == "anexo" else entradas).append({"clase": "simple", "titulo": ind["titulo"], "pag": Q["_n_texto"]})
            P["_entradas"], P["_anexos"], P["_figuras"] = entradas, anexos, lista_figuras
            if P.get("_hojas_figuras"):
                k = P.get("_indice_cont", 0)
                ph = P.get("_por_hoja", INDICE_FIGS_HOJA)
                P["_figuras"] = lista_figuras[(k - 1) * ph:k * ph] if k else []
                P["_figuras_en"] = next((Q["_n_texto"] for Q in paginas if Q.get("_indice_cont") == 1), "")
        if P["tipo"] == "metodo":
            filas = []
            for c in P.get("cifras", []):
                d = cifras.get(c.get("id"), {})
                filas.append({"concepto": c.get("concepto") or d.get("concepto", ""), "valor": c.get("valor", ""), "veredicto": d.get("veredicto", "—"), "aparece": c.get("aparece", "")})
            P["_cifras"] = filas
            P["_fuentes"] = R["meta"].get("fuentes", [])
    return R


# ---------------------------------------------------------------- figuras PNG
def preparar_figuras(R, salida, paleta, handle, errores):
    dfig = os.path.join(salida, "figuras")
    os.makedirs(dfig, exist_ok=True)
    tk = nuevo_visual.tokens()
    k = 0
    for P in R["paginas"]:
        for kind, f in figuras_de_pagina(P):
            if kind != "figura" or f.get("tipo") != "tarjeta":
                continue
            k += 1
            if f.get("desde"):
                origen = os.path.join(RAIZ, f["desde"])
                if not os.path.exists(origen):
                    errores.append("figura %s: no existe %s" % (f["_n"], f["desde"]))
                    continue
                destino = os.path.join(dfig, "fig_%02d.png" % k)
                shutil.copyfile(origen, destino)
                f["_src"] = "figuras/" + os.path.basename(destino)
                continue
            html = os.path.join(dfig, "fig_%02d.html" % k)
            ok, msg = nuevo_visual.ensamblar(f["plantilla"], html, paleta, tk)
            if not ok:
                errores.append("figura %s: %s" % (f["_n"], msg))
                continue
            src = open(html, encoding="utf-8").read()
            data = materializar.data_de(f, handle)
            nuevo, n = materializar.RE_DATA.subn("const DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", src, count=1)
            if n != 1:
                errores.append("figura %s: la plantilla %s no tiene un bloque DATA reconocible" % (f["_n"], f["plantilla"]))
                continue
            open(html, "w", encoding="utf-8").write(nuevo)
            r = subprocess.run(["node", os.path.join(RAIZ, "scripts", "render.js"), html, "--check"], capture_output=True, text=True)
            if r.returncode != 0:
                errores.append("figura %s (%s) no pasa el gate de tarjeta:\n%s" % (f["_n"], f["plantilla"], (r.stdout + r.stderr).strip()))
                continue
            f["_src"] = "figuras/fig_%02d.png" % k
    j = 0  # numeración común a todas las páginas tarjetas: si se reiniciara, la segunda pisaría las imágenes de la primera
    for P in R["paginas"]:
        if P["tipo"] == "tarjetas":
            for it in P["items"]:
                j += 1
                destino = os.path.join(dfig, "tarjeta_%02d.png" % j)
                shutil.copyfile(os.path.join(RAIZ, it["desde"]), destino)
                it["_src"] = "figuras/" + os.path.basename(destino)


# ---------------------------------------------------------------- ensamblado
def css_paletas(tk):
    L = []
    for k, p in tk["paletas"].items():
        h = p["ink"].lstrip("#")
        rgb = ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))
        kicker = p["a1"] if k == "obsidiana" else p["ink"]
        L.append('body[data-paleta="%s"] { --bg:%s; --ink:%s; --a1:%s; --a2:%s; --a3:%s; --ink-rgb:%s; --x-fg:%s; --rule:rgba(%s,.3); --kicker:%s; --tinta:%s; --barra:%s; }'
                 % (k, p["bg"], p["ink"], p["a1"], p["a2"], p["a3"], rgb, p["bg"], rgb, kicker, p["papel_tinta"], p["papel_barra"]))
    return "\n".join(L)


def bloque_h():
    src = open(BASE_TARJETA, encoding="utf-8").read()
    m = re.search(r"// H:INICIO[^\n]*\n(.*?)\n// H:FIN", src, re.S)
    if not m:
        raise SystemExit("ERROR: templates/base.html no tiene los marcadores // H:INICIO … // H:FIN")
    return m.group(1)


def scripts_de(carpeta):
    partes = []
    for ruta in sorted(glob.glob(os.path.join(DIR_INV, carpeta, "*.js"))):
        cuerpo = open(ruta, encoding="utf-8").read()
        if RE_URL.search(cuerpo):
            raise SystemExit("ERROR: %s contiene una URL" % os.path.relpath(ruta, RAIZ))
        partes.append("// ---- %s\n%s" % (os.path.relpath(ruta, RAIZ), cuerpo))
    return "\n".join(partes)


def centroide(d):
    """Centroide de área del anillo más grande de un path (M/L/l/H/V/z absolutos o relativos)."""
    anillos, actual, x, y = [], [], 0.0, 0.0
    for cmd, args in re.findall(r"([MmLlHhVvZz])([^MmLlHhVvZz]*)", d):
        nums = [float(t) for t in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", args)]
        if cmd in "Mm":
            if actual:
                anillos.append(actual)
            actual = []
            pares = list(zip(nums[0::2], nums[1::2]))
            for a, b in pares:
                x, y = (a, b) if cmd == "M" else (x + a, y + b)
                actual.append((x, y))
        elif cmd in "Ll":
            for a, b in zip(nums[0::2], nums[1::2]):
                x, y = (a, b) if cmd == "L" else (x + a, y + b)
                actual.append((x, y))
        elif cmd in "Hh":
            for v in nums:
                x = v if cmd == "H" else x + v
                actual.append((x, y))
        elif cmd in "Vv":
            for v in nums:
                y = v if cmd == "V" else y + v
                actual.append((x, y))
    if actual:
        anillos.append(actual)
    mejor = None
    for ring in anillos:
        area = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
            c = x0 * y1 - x1 * y0
            area += c
            cx += (x0 + x1) * c
            cy += (y0 + y1) * c
        if area and (mejor is None or abs(area) > abs(mejor[0])):
            mejor = (area, cx / (3 * area), cy / (3 * area))
    return [round(mejor[1], 1), round(mejor[2], 1)] if mejor else None


def usa_mapa(R):
    return any((f.get("grafico") or {}).get("tipo") == "mapa" for P in R["paginas"] for k, f in figuras_de_pagina(P) if k == "figura")


def ensamblar_html(R, tk):
    base = open(BASE, encoding="utf-8").read()
    for marca in ("/* I:PALETAS */", "/* I:HELPERS */", "<!-- I:GRAFICOS -->", "<!-- I:PAGINAS -->", "/*INFORME_JSON*/null"):
        if marca not in base:
            raise SystemExit("ERROR: investigacion/base.html no tiene el marcador %s" % marca)
    geo = ""
    if usa_mapa(R):
        vb, deptos = build_mapa.extraer(build_mapa.GEOMETRIA)
        centros = {k: centroide(v["d"]) for k, v in deptos.items()}
        geo = "const GEOMETRIA = " + json.dumps({"viewBox": vb, "deptos": deptos, "centros": centros}, ensure_ascii=False) + ";\n"
    html = base.replace("/* I:PALETAS */", css_paletas(tk))
    html = html.replace("/* I:HELPERS */", bloque_h())
    html = html.replace("<!-- I:GRAFICOS -->", "<script>\n" + geo + scripts_de("graficos") + "\n</script>")
    html = html.replace("<!-- I:PAGINAS -->", "<script>\n" + scripts_de("paginas") + "\n</script>")
    html = html.replace("/*INFORME_JSON*/null", json.dumps(R, ensure_ascii=False).replace("</", "<\\/"))
    return html


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dir", help="carpeta con informe.json")
    p.add_argument("--salida", help="carpeta de salida (por defecto <dir>/salida)")
    p.add_argument("--paleta", help="sustituye meta.paleta (para probar el informe en otra paleta)")
    p.add_argument("--check", action="store_true", help="render con checks P1–P5")
    p.add_argument("--sin-pdf", action="store_true", help="solo informe.html (sin render)")
    p.add_argument("--png", metavar="DIR", help="además, un PNG por página en DIR (QA visual)")
    a = p.parse_args()
    ruta = os.path.join(a.dir, "informe.json")
    if not os.path.exists(ruta):
        print("ERROR: no existe %s" % ruta, file=sys.stderr)
        return 2
    try:
        R = cargar_json(ruta)
    except json.JSONDecodeError as e:
        print("ERROR: %s no es JSON válido: %s" % (ruta, e), file=sys.stderr)
        return 1
    tk = cargar_json(TOKENS)
    if a.paleta:
        R.setdefault("meta", {})["paleta"] = a.paleta
    cifras = {}
    for rel in (R.get("meta") or {}).get("datos", []):
        rd = os.path.join(RAIZ, rel)
        if not os.path.exists(rd):
            print("FALLO I2 meta.datos: no existe %s" % rel, file=sys.stderr)
            return 1
        for c in cargar_json(rd).get("cifras", []):
            cifras.setdefault(c["id"], c)
    g = Gate()
    normalizar(R)
    for P in R.get("paginas") or []:
        if P.get("tipo") == "tarjetas" and P.get("desde_hilo"):
            expandir_desde_hilo(P, g)
    validar(R, tk, cifras, g)
    for w in avisos_texto(R, cifras):
        print("AVISO " + w, file=sys.stderr)
    if R.get("meta", {}).get("paleta") in tk["paletas"]:
        R["meta"]["_paleta_nombre"] = tk["paletas"][R["meta"]["paleta"]].get("nombre", R["meta"]["paleta"])
    if not g.fallos:
        R = resolver(R, cifras, g)
    if g.fallos:
        for f in g.fallos:
            print("FALLO " + f, file=sys.stderr)
        print("[informe] %d fallo(s) de gate: no se escribe el informe" % len(g.fallos), file=sys.stderr)
        return 1
    salida = os.path.abspath(a.salida or os.path.join(a.dir, "salida"))
    os.makedirs(salida, exist_ok=True)
    errores = []
    preparar_figuras(R, salida, R["meta"]["paleta"], R["meta"]["handle"], errores)
    if errores:
        for e in errores:
            print("FALLO " + e, file=sys.stderr)
        return 1
    dfonts = os.path.join(salida, "fonts")
    os.makedirs(dfonts, exist_ok=True)
    for f in glob.glob(os.path.join(FONTS, "*.woff2")):
        shutil.copyfile(f, os.path.join(dfonts, os.path.basename(f)))
    html = os.path.join(salida, "informe.html")
    open(html, "w", encoding="utf-8").write(ensamblar_html(R, tk))
    print("ensamblado %s · %d páginas · paleta %s" % (os.path.relpath(html, os.getcwd()), len(R["paginas"]), R["meta"]["paleta"]), flush=True)
    if a.sin_pdf:
        return 0
    cmd = ["node", os.path.join(RAIZ, "scripts", "render_informe.js"), html, "--pdf", os.path.join(salida, "informe.pdf")]
    if a.check:
        cmd.append("--check")
    if a.png:
        cmd += ["--png", a.png]
    r = subprocess.run(cmd)
    return 1 if r.returncode else 0


if __name__ == "__main__":
    sys.exit(main())
