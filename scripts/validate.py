#!/usr/bin/env python3
"""Valida la memoria y la integridad de los hilos entregados. Solo stdlib.

Comprueba:
  M1 memoria/fuentes.json: schema de `fuentes` (nombre, url, categoria, rating 1-10)
     y de `series` (nombre, fuente, url, formato, unidad, frecuencia)
  M2 memoria/hilos.json: schema de cada hilo (id, fecha, slug, tema, tesis, paleta,
     n_tuits, ruta, estado) · ids únicos · paleta ∈ design/tokens.json · modo (opcional) ∈ ensamblar.MODOS["hilo"]
  M3 design/tokens.json: contraste WCAG ink/bg ≥ 4.5 (error) y a1/bg ≥ 3 (aviso)
  H1 cada hilos/*/ tiene hilo.json, post.md, datos.json, hilo.html y los PNG que
     hilo.json declara; y está registrado en memoria/hilos.json (aviso si no)
  H2 en hilo.json: T1 con texto ≤ 280 y sin enlace, ningún texto > 280, paleta única, modo conocido
  H3 el estado de hilo.json coincide con el registro: error si la entrega dice
     `borrador` o difieren en `incompleto` (ensamblar.py --solo-estado lo arregla);
     aviso en cualquier otra diferencia (`publicado` se anota a mano en memoria)
  M4 ideas/banco.json (si existe): cada idea válida (campos, área, hook, paleta, ≥1 dato
     con url y evidencia, puntajes 1–5), ids únicos, estado ∈ enum, `hecha` ⇒ hilo_id
     registrado en memoria/hilos.json; aviso si un hilo con idea_id apunta a una idea
     que no existe o que no está hecha/en curso (ideas.py --conciliar lo arregla)
  M5 memoria/datos.json (si existe; registro de /dato): schema de cada dato (id, fecha,
     slug, tema, dato, cifra_id, valor_final, unidad, fuente, plantilla, paleta, ruta,
     estado) · ids únicos · paleta, hook_tipo y modo (opcional, ∈ MODOS["dato"]) conocidos · ruta relativa y existente
  D1 cada datos/*/ tiene dato.json, dato.html, post.md, datos.json, dato.png y
     tarjeta.html; y está registrado en memoria/datos.json (aviso si no)
  D2 en dato.json: tipo "dato", sin tuits[], tuit{} con texto de 40–280 de peso X y sin
     enlace, imagen existente, alt_text 20–1000, paleta y modo conocidos
  D3 el estado de dato.json coincide con el registro (misma regla que H3)
  M6 ideas/calendario.json (si existe): cada entrada válida (id slug, fecha MM-DD|DD|YYYY-MM-DD,
     tipo, titulo, pista, formato, modo compatible, estado), ids únicos; aviso si una entrada
     `hecha` apunta a una pieza que no existe
  M7 memoria/informes.json (si existe; registro de /investigacion): schema de cada informe (id, fecha,
     slug, tema, tesis, paleta, numero, n_paginas, n_figuras, ruta_informe, ruta_hilo, hilo_id, estado,
     modo ∈ investigacion|desde) · ids y numero únicos · ruta_informe con informe.json y salida/informe.pdf ·
     ruta_hilo con hilo.json · hilo_id registrado en memoria/hilos.json
  M8 memoria/videos.json (si existe; registro de /video): schema de cada video (id, fecha, slug, hilo_id, paleta,
     duracion ∈ corto|medio|largo, duracion_s, n_escenas, musica, ruta_video, ruta_hilo, estado) · ids únicos ·
     ruta_video con guion.json (el mp4 está fuera de git: su ausencia es aviso) · musica en el catálogo
  K1 design/musica/catalogo.json: cada pista existe, ids únicos, paleta conocida y ≥ 2 pistas por paleta
  N1 cada investigacion/<YYYY-MM-DD>-*/ (entregable de /investigacion) tiene informe.json,
     salida/informe.pdf y salida/informe.html; aviso si no está en memoria/informes.json (corrida
     interrumpida: reanuda con resumeFromRunId o borra la carpeta); si no está registrada, tiene hilo/
     y aún no tiene informe.json (entre Producción y Cierre), los faltantes son aviso y no error
  N2 su informe.json: meta.datos[] y los `desde`/`desde_hilo` de figuras y tarjetas existen; meta.numero
     coincide con el registro
  N3 si tiene hilo/: mismas reglas que H1–H3, hilo.json con modo "investigacion", el cierre lleva el
     marcador [ENLACE AL INFORME] e informe_dir apunta al entregable; registrado en hilos.json con esa ruta

Uso: python3 scripts/validate.py [--quiet]   · salida 0 ok · 1 error
"""
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
from ensamblar import HOOKS, MODOS, RE_LINK, MARCADOR_INFORME  # noqa: E402  (una sola lista de ganchos y de modos para todo el framework)
from contar_x import peso_x  # noqa: E402
import ideas as _ideas  # noqa: E402
import calendario as _cal  # noqa: E402
ERRORES, AVISOS = [], []


def err(m): ERRORES.append(m)
def warn(m): AVISOS.append(m)


def cargar(rel):
    ruta = os.path.join(RAIZ, rel)
    if not os.path.exists(ruta):
        err("falta %s" % rel); return None
    try:
        with open(ruta, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        err("%s no es JSON válido: %s" % (rel, e)); return None


def luminancia(hexv):
    h = hexv.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contraste(a, b):
    la, lb = sorted([luminancia(a), luminancia(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def validar_tokens():
    tk = cargar("design/tokens.json")
    if not tk:
        return set()
    a1_bajas = []
    for k, p in tk.get("paletas", {}).items():
        for campo in ("bg", "ink", "a1", "a2", "a3"):
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", p.get(campo, "")):
                err("tokens: paleta %s sin %s válido" % (k, campo))
        try:
            c = contraste(p["bg"], p["ink"])
            if c < 4.5:
                err("tokens: paleta %s ink/bg %.2f:1 < 4.5" % (k, c))
            c1 = contraste(p["bg"], p["a1"])
            if c1 < 3:
                a1_bajas.append("%s %.2f" % (k, c1))
        except (KeyError, ValueError):
            pass
    papel = (tk.get("documento") or {}).get("papel")
    if papel:  # informes (investigacion/): la tinta del acento va en texto sobre papel
        for k, p in tk.get("paletas", {}).items():
            for campo in ("papel_tinta", "papel_barra"):
                if not re.fullmatch(r"#[0-9A-Fa-f]{6}", p.get(campo, "")):
                    err("tokens: paleta %s sin %s válido (documento)" % (k, campo))
            try:
                c = contraste(papel, p["papel_tinta"])
                if c < 4.5:
                    err("tokens: paleta %s papel_tinta/papel %.2f:1 < 4.5" % (k, c))
            except (KeyError, ValueError):
                pass
    if a1_bajas:  # esperado y documentado en referencias/diseno/sistema.md: a1 nunca va en texto pequeño
        warn("tokens: a1/bg < 3:1 en %d paleta(s) (%s): a1 solo en cifras grandes y marcas (sistema.md)" % (len(a1_bajas), ", ".join(a1_bajas)))
    return set(tk.get("paletas", {}))


def validar_fuentes():
    d = cargar("memoria/fuentes.json")
    if not d:
        return
    for i, f in enumerate(d.get("fuentes", [])):
        for campo in ("nombre", "url", "categoria", "rating"):
            if campo not in f:
                err("fuentes[%d] sin %s" % (i, campo))
        if not isinstance(f.get("rating"), int) or not 1 <= f.get("rating", 0) <= 10:
            err("fuentes[%d] rating fuera de 1-10" % i)
    formatos = {"xlsx", "csv", "html", "pdf", "json", "api", "xls"}
    for i, s in enumerate(d.get("series", [])):
        for campo in ("nombre", "fuente", "url", "formato", "unidad", "frecuencia"):
            if campo not in s:
                err("series[%d] sin %s" % (i, campo))
        if s.get("formato") not in formatos:
            err("series[%d] formato %r no está en %s" % (i, s.get("formato"), sorted(formatos)))


def validar_hilos(paletas):
    d = cargar("memoria/hilos.json")
    registrados = {}
    if d:
        ids = set()
        estados = {"borrador", "listo", "publicado", "incompleto"}
        hooks = set(HOOKS)
        for i, h in enumerate(d.get("hilos", [])):
            for campo in ("id", "fecha", "slug", "tema", "tesis", "paleta", "n_tuits", "ruta", "estado"):
                if campo not in h:
                    err("hilos[%d] sin %s" % (i, campo))
            if h.get("id") in ids:
                err("hilos: id repetido %s" % h.get("id"))
            ids.add(h.get("id"))
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(h.get("fecha", ""))):
                err("hilos[%d] fecha no es YYYY-MM-DD" % i)
            if paletas and h.get("paleta") not in paletas:
                err("hilos[%d] paleta %r desconocida" % (i, h.get("paleta")))
            if h.get("estado") not in estados:
                err("hilos[%d] estado %r no está en %s" % (i, h.get("estado"), sorted(estados)))
            if h.get("hook_tipo") and h["hook_tipo"] not in hooks:
                err("hilos[%d] hook_tipo %r desconocido" % (i, h.get("hook_tipo")))
            if h.get("modo") and h["modo"] not in MODOS["hilo"]:
                err("hilos[%d] modo %r no está en %s" % (i, h.get("modo"), MODOS["hilo"]))
            if os.path.isabs(str(h.get("ruta", ""))):
                err("hilos[%d] ruta debe ser relativa a la raíz del repo (%s)" % (i, h.get("ruta")))
            registrados[os.path.normpath(str(h.get("ruta", "")))] = h
        sin_modo = [h.get("id") for h in d.get("hilos", []) if not h.get("modo")]
        if sin_modo:
            warn("hilos: %d registro(s) sin modo (corre python3 scripts/memoria.py --conciliar-modos): %s" % (len(sin_modo), ", ".join(map(str, sin_modo[:4])) + (" …" if len(sin_modo) > 4 else "")))

    for carpeta in sorted(glob.glob(os.path.join(RAIZ, "hilos", "*"))):
        if os.path.isdir(carpeta):
            validar_carpeta_hilo(carpeta, os.path.relpath(carpeta, RAIZ), registrados, paletas)
    return registrados


def validar_carpeta_hilo(carpeta, rel, registrados, paletas):
    """H1–H3 de una carpeta de hilo (hilos/* o investigacion/*/hilo). Devuelve hilo.json o None."""
    if True:
        for archivo in ("hilo.json", "post.md", "datos.json", "hilo.html"):
            if not os.path.exists(os.path.join(carpeta, archivo)):
                err("%s: falta %s" % (rel, archivo))
        if rel not in registrados:
            warn("%s no está registrado en memoria/hilos.json" % rel)
        hj = os.path.join(carpeta, "hilo.json")
        if not os.path.exists(hj):
            return None
        try:
            h = json.load(open(hj, encoding="utf-8"))
        except json.JSONDecodeError as e:
            err("%s/hilo.json inválido: %s" % (rel, e)); return None
        reg = registrados.get(rel)
        if reg and reg.get("estado") != h.get("estado"):
            e_reg, e_hilo = reg.get("estado"), h.get("estado")
            if e_hilo == "borrador" or "incompleto" in (e_reg, e_hilo):
                err("%s: hilo.json dice estado %r y memoria/hilos.json %r (corre ensamblar.py <sesion> --solo-estado --estado %s)" % (rel, e_hilo, e_reg, e_reg))
            else:
                warn("%s: hilo.json dice estado %r y memoria/hilos.json %r" % (rel, e_hilo, e_reg))
        tuits = h.get("tuits", [])
        if not tuits:
            err("%s/hilo.json sin tuits" % rel); return h
        t1 = tuits[0].get("texto", "")
        if not t1.strip():
            err("%s: T1 sin texto" % rel)
        if re.search(r"https?://|www\.", t1):
            err("%s: T1 lleva enlace" % rel)
        for t in tuits:
            if len(t.get("texto", "")) > 280:
                err("%s: T%s supera 280 caracteres (%d)" % (rel, t.get("n"), len(t["texto"])))
            img = t.get("imagen")
            if img and not os.path.exists(os.path.join(carpeta, img)):
                err("%s: falta la imagen %s de T%s" % (rel, img, t.get("n")))
        if paletas and h.get("paleta") not in paletas:
            err("%s: paleta %r desconocida" % (rel, h.get("paleta")))
        if h.get("modo") and h["modo"] not in MODOS["hilo"]:
            err("%s: hilo.json modo %r no está en %s" % (rel, h.get("modo"), MODOS["hilo"]))
        return h


RE_ENTREGABLE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$")


def validar_informes(paletas, hilos_registrados):
    """M7 + N1–N3: memoria/informes.json y las carpetas investigacion/<fecha>-<slug>/ (entregables de /investigacion)."""
    registrados = {}
    rel_mem = "memoria/informes.json"
    hids = {h.get("id") for h in hilos_registrados.values()}
    if os.path.exists(os.path.join(RAIZ, rel_mem)):  # ausente = ok: memoria.py lo crea con el primer informe
        d = cargar(rel_mem)
        if d:
            ids, numeros = set(), {}
            estados = {"borrador", "listo", "publicado", "incompleto"}
            for i, h in enumerate(d.get("informes", [])):
                for campo in ("id", "fecha", "slug", "tema", "tesis", "paleta", "numero", "n_paginas", "n_figuras", "ruta_informe", "ruta_hilo", "hilo_id", "estado", "modo"):
                    if campo not in h:
                        err("informes[%d] sin %s" % (i, campo))
                if h.get("id") in ids:
                    err("informes: id repetido %s" % h.get("id"))
                ids.add(h.get("id"))
                num = str(h.get("numero") or "")
                if not re.fullmatch(r"\d{2,}", num):
                    err("informes[%d] numero %r debe tener dos dígitos" % (i, h.get("numero")))
                elif num in numeros:
                    err("informes: N.º %s repetido (%s y %s)" % (num, numeros[num], h.get("id")))
                numeros[num] = h.get("id")
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(h.get("fecha", ""))):
                    err("informes[%d] fecha no es YYYY-MM-DD" % i)
                if paletas and h.get("paleta") not in paletas:
                    err("informes[%d] paleta %r desconocida" % (i, h.get("paleta")))
                if h.get("estado") not in estados:
                    err("informes[%d] estado %r no está en %s" % (i, h.get("estado"), sorted(estados)))
                if h.get("modo") not in ("investigacion", "desde"):
                    err("informes[%d] modo %r no es investigacion|desde" % (i, h.get("modo")))
                ri, rh = str(h.get("ruta_informe", "")), str(h.get("ruta_hilo", ""))
                if os.path.isabs(ri) or os.path.isabs(rh):
                    err("informes[%d] rutas deben ser relativas a la raíz (%s · %s)" % (i, ri, rh))
                else:
                    if not os.path.exists(os.path.join(RAIZ, ri, "informe.json")):
                        err("informes[%d] ruta_informe %s sin informe.json" % (i, ri))
                    elif not os.path.exists(os.path.join(RAIZ, ri, "salida", "informe.pdf")):
                        err("informes[%d] %s/salida/informe.pdf no existe" % (i, ri))
                    if not os.path.exists(os.path.join(RAIZ, rh, "hilo.json")):
                        err("informes[%d] ruta_hilo %s sin hilo.json" % (i, rh))
                if h.get("hilo_id") not in hids:
                    err("informes[%d] hilo_id %r no está en memoria/hilos.json" % (i, h.get("hilo_id")))
                registrados[os.path.normpath(ri)] = h

    for carpeta in sorted(glob.glob(os.path.join(RAIZ, "investigacion", "*"))):
        if not os.path.isdir(carpeta) or not RE_ENTREGABLE.match(os.path.basename(carpeta)):
            continue
        rel = os.path.relpath(carpeta, RAIZ)
        # N1 (entre Producción y Cierre de /investigacion la carpeta solo tiene hilo/ y aún no está
        # registrada: los archivos del informe faltan por diseño → aviso; registrada, son error)
        reg = registrados.get(rel)
        en_curso = not reg and os.path.isdir(os.path.join(carpeta, "hilo")) and not os.path.exists(os.path.join(carpeta, "informe.json"))
        for archivo in ("informe.json", os.path.join("salida", "informe.pdf"), os.path.join("salida", "informe.html")):
            if not os.path.exists(os.path.join(carpeta, archivo)):
                (warn if en_curso else err)("%s: falta %s%s" % (rel, archivo, " (informe pendiente: lo escribe el Cierre)" if en_curso else ""))
        if not reg:
            warn("%s no está registrado en memoria/informes.json (corrida interrumpida: reanuda con resumeFromRunId o borra la carpeta)" % rel)
        rj = os.path.join(carpeta, "informe.json")
        if os.path.exists(rj):
            try:
                R = json.load(open(rj, encoding="utf-8"))
            except json.JSONDecodeError as e:
                err("%s/informe.json inválido: %s" % (rel, e)); R = None
            if R:  # N2
                meta = R.get("meta") or {}
                for rel_d in meta.get("datos") or []:
                    if not os.path.exists(os.path.join(RAIZ, rel_d)):
                        err("%s: meta.datos %s no existe" % (rel, rel_d))
                if not meta.get("numero"):
                    warn("%s: informe.json sin meta.numero" % rel)
                elif reg and str(reg.get("numero")) != str(meta.get("numero")):
                    err("%s: meta.numero %r ≠ registro %r" % (rel, meta.get("numero"), reg.get("numero")))
                for P in R.get("paginas") or []:
                    if P.get("desde_hilo") and not os.path.exists(os.path.join(RAIZ, P["desde_hilo"], "hilo.json")):
                        err("%s: tarjetas desde_hilo %s sin hilo.json" % (rel, P["desde_hilo"]))
                    for it in P.get("items") or []:
                        if isinstance(it, dict) and it.get("desde") and not os.path.exists(os.path.join(RAIZ, it["desde"])):
                            err("%s: tarjeta desde %s no existe" % (rel, it["desde"]))
                    for B in (P.get("bloques") or []) + (P.get("lateral") or []):
                        figs = B.get("items", []) if B.get("b") == "figuras" else ([B] if B.get("b") == "figura" else [])
                        for f in figs:
                            if isinstance(f, dict) and f.get("desde") and not os.path.exists(os.path.join(RAIZ, f["desde"])):
                                err("%s: figura desde %s no existe" % (rel, f["desde"]))
        # N3
        ch = os.path.join(carpeta, "hilo")
        if os.path.isdir(ch):
            relh = os.path.relpath(ch, RAIZ)
            h = validar_carpeta_hilo(ch, relh, hilos_registrados, paletas)
            if h:
                if h.get("modo") != "investigacion":
                    err("%s: hilo.json debe llevar modo \"investigacion\" (es %r)" % (relh, h.get("modo")))
                tuits = h.get("tuits") or []
                if tuits and MARCADOR_INFORME not in (tuits[-1].get("texto") or ""):
                    err("%s: el cierre no lleva el marcador %s" % (relh, MARCADOR_INFORME))
                inv = h.get("investigacion") if isinstance(h.get("investigacion"), dict) else {}
                if inv and os.path.normpath(str(inv.get("informe_dir") or "")) != os.path.normpath(rel):
                    err("%s: investigacion.informe_dir %r ≠ %s" % (relh, inv.get("informe_dir"), rel))
        elif reg and os.path.normpath(str(reg.get("ruta_hilo") or "")) == os.path.normpath(os.path.join(rel, "hilo")):
            err("%s: el registro apunta a %s/hilo pero no existe" % (rel, rel))


def validar_datos(paletas):
    """M5 + D1–D3: registro memoria/datos.json y carpetas datos/*/ (entregables de /dato)."""
    registrados = {}
    rel_mem = "memoria/datos.json"
    if os.path.exists(os.path.join(RAIZ, rel_mem)):  # ausente = ok: memoria.py lo crea al registrar el primer dato
        d = cargar(rel_mem)
        if d:
            ids = set()
            estados = {"borrador", "listo", "publicado", "incompleto"}
            for i, h in enumerate(d.get("datos", [])):
                for campo in ("id", "fecha", "slug", "tema", "dato", "cifra_id", "valor_final", "unidad", "fuente", "plantilla", "paleta", "ruta", "estado"):
                    if campo not in h:
                        err("datos[%d] sin %s" % (i, campo))
                if h.get("id") in ids:
                    err("datos: id repetido %s" % h.get("id"))
                ids.add(h.get("id"))
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(h.get("fecha", ""))):
                    err("datos[%d] fecha no es YYYY-MM-DD" % i)
                if paletas and h.get("paleta") not in paletas:
                    err("datos[%d] paleta %r desconocida" % (i, h.get("paleta")))
                if h.get("estado") not in estados:
                    err("datos[%d] estado %r no está en %s" % (i, h.get("estado"), sorted(estados)))
                if h.get("hook_tipo") and h["hook_tipo"] not in HOOKS:
                    err("datos[%d] hook_tipo %r desconocido" % (i, h.get("hook_tipo")))
                if h.get("modo") and h["modo"] not in MODOS["dato"]:
                    err("datos[%d] modo %r no está en %s" % (i, h.get("modo"), MODOS["dato"]))
                ruta = str(h.get("ruta", ""))
                if os.path.isabs(ruta):
                    err("datos[%d] ruta debe ser relativa a la raíz del repo (%s)" % (i, ruta))
                elif not os.path.isdir(os.path.join(RAIZ, ruta)):
                    err("datos[%d] ruta %s no existe" % (i, ruta))
                registrados[os.path.normpath(ruta)] = h

    for carpeta in sorted(glob.glob(os.path.join(RAIZ, "datos", "*"))):
        if not os.path.isdir(carpeta):
            continue
        rel = os.path.relpath(carpeta, RAIZ)
        for archivo in ("dato.json", "dato.html", "post.md", "datos.json", "dato.png", "tarjeta.html"):
            if not os.path.exists(os.path.join(carpeta, archivo)):
                err("%s: falta %s" % (rel, archivo))
        if rel not in registrados:
            warn("%s no está registrado en memoria/datos.json" % rel)
        dj = os.path.join(carpeta, "dato.json")
        if not os.path.exists(dj):
            continue
        try:
            dd = json.load(open(dj, encoding="utf-8"))
        except json.JSONDecodeError as e:
            err("%s/dato.json inválido: %s" % (rel, e)); continue
        reg = registrados.get(rel)
        if reg and reg.get("estado") != dd.get("estado"):
            e_reg, e_d = reg.get("estado"), dd.get("estado")
            if e_d == "borrador" or "incompleto" in (e_reg, e_d):
                err("%s: dato.json dice estado %r y memoria/datos.json %r (corre ensamblar.py <sesion> --solo-estado --estado %s)" % (rel, e_d, e_reg, e_reg))
            else:
                warn("%s: dato.json dice estado %r y memoria/datos.json %r" % (rel, e_d, e_reg))
        if dd.get("tipo") != "dato":
            err("%s: dato.json debe llevar tipo \"dato\"" % rel)
        if "tuits" in dd:
            err("%s: dato.json no lleva tuits[] (es un dato, no un hilo)" % rel)
        t = dd.get("tuit")
        if not isinstance(t, dict):
            err("%s: dato.json sin tuit{}" % rel); continue
        texto = t.get("texto") or ""
        peso = peso_x(texto)
        if not 40 <= peso <= 280:
            err("%s: el texto pesa %d en X (debe ser 40–280)" % (rel, peso))
        if RE_LINK.search(texto):
            err("%s: el texto lleva enlace o dominio" % rel)
        img = t.get("imagen") or "dato.png"
        if not os.path.exists(os.path.join(carpeta, img)):
            err("%s: falta la imagen %s" % (rel, img))
        alt = (t.get("alt_text") or "").strip()
        if not 20 <= len(alt) <= 1000:
            err("%s: alt_text debe tener 20–1000 caracteres (%d)" % (rel, len(alt)))
        if paletas and dd.get("paleta") not in paletas:
            err("%s: paleta %r desconocida" % (rel, dd.get("paleta")))
        if dd.get("modo") and dd["modo"] not in MODOS["dato"]:
            err("%s: dato.json modo %r no está en %s" % (rel, dd.get("modo"), MODOS["dato"]))


def validar_ideas(paletas):
    if not os.path.exists(_ideas.BANCO):
        return
    d = cargar(os.path.relpath(_ideas.BANCO, RAIZ))
    if not d:
        return
    hilos = (cargar("memoria/hilos.json") or {}).get("hilos", [])
    hids = {h.get("id") for h in hilos}
    ids = set()
    for i, idea in enumerate(d.get("ideas", [])):
        iid = idea.get("id") or "ideas[%d]" % i
        if not re.fullmatch(r"[a-z0-9-]+", str(idea.get("id") or "")):
            err("ideas[%d] id %r no es un slug" % (i, idea.get("id")))
        if iid in ids:
            err("ideas: id repetido %s" % iid)
        ids.add(iid)
        for p in _ideas.validar_idea(idea, paletas):
            err("ideas %s: %s" % (iid, p))
        if idea.get("estado") not in _ideas.ESTADOS:
            err("ideas %s: estado %r no está en %s" % (iid, idea.get("estado"), _ideas.ESTADOS))
        if idea.get("estado") == "hecha" and idea.get("hilo_id") not in hids:
            err("ideas %s: hecha con hilo_id %r que no está en memoria/hilos.json" % (iid, idea.get("hilo_id")))
    if d.get("ideas") and not any(i.get("estado") == "pendiente" for i in d["ideas"]):
        warn("ideas: el banco no tiene ninguna idea pendiente (/hilo sin tema no tendrá de dónde elegir): corre /ideas")
    estado = {idea.get("id"): idea.get("estado") for idea in d.get("ideas", [])}
    for h in hilos:
        if h.get("idea_id") and estado.get(h["idea_id"]) not in ("hecha", "en_curso"):
            warn("hilo %s apunta a la idea %s (%s): corre python3 scripts/ideas.py --conciliar" % (
                h.get("id"), h["idea_id"], estado.get(h["idea_id"], "no existe")))


def _hoy():
    import datetime as _dt
    return _dt.date.today().isoformat()


def huerfanas(borrar=False):
    """Sesiones (sin _ al inicio) que ningún registro de memoria/ menciona por slug o ruta."""
    import shutil
    textos = " ".join(json.dumps(cargar(r) or {}, ensure_ascii=False) for r in ("memoria/hilos.json", "memoria/datos.json", "memoria/informes.json"))
    out = []
    for d in sorted(glob.glob(os.path.join(RAIZ, "sesiones", "*"))):
        n = os.path.basename(d)
        if not os.path.isdir(d) or n.startswith("_"):
            continue
        if ('"%s"' % n) in textos or ("-%s\"" % n) in textos or ("-%s/" % n) in textos:
            continue
        out.append(n)
    for n in out:
        if borrar:
            shutil.rmtree(os.path.join(RAIZ, "sesiones", n))
        print("%s sesiones/%s" % ("borrada" if borrar else "huérfana", n))
    print("[podar] %d sesión(es) huérfana(s)%s" % (len(out), "" if borrar or not out else " · make podar BORRAR=1 para borrarlas"))
    return 0


def validar_calendario():
    if not os.path.exists(_cal.CALENDARIO):
        return
    d = cargar(os.path.relpath(_cal.CALENDARIO, RAIZ))
    if not d:
        return
    ids = set()
    for i, e in enumerate(d.get("entradas", [])):
        eid = e.get("id") or "entradas[%d]" % i
        if eid in ids:
            err("calendario: id repetido %s" % eid)
        ids.add(eid)
        for p in _cal.validar_entrada(e):
            err("calendario %s: %s" % (eid, p))
        if e.get("estado") == "hecha" and e.get("pieza") and not os.path.isdir(os.path.join(RAIZ, str(e["pieza"]))):
            warn("calendario %s: hecha con pieza %s que no existe" % (eid, e["pieza"]))
        if e.get("estado") == "pendiente" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("fecha", ""))) and str(e["fecha"]) < _hoy():
            warn("calendario %s: fecha puntual %s ya pasó y sigue pendiente (márcala hecha o descartada con calendario.py --marcar)" % (eid, e["fecha"]))


def validar_videos(paletas):
    """K1 (catálogo fijo de música de /video) y M8 (memoria/videos.json)."""
    ids_musica = set()
    rel_cat = "design/musica/catalogo.json"
    if not os.path.exists(os.path.join(RAIZ, rel_cat)):
        err("K1 falta %s (biblioteca de música de /video)" % rel_cat)
    else:
        cat = cargar(rel_cat) or {}
        por_paleta = {}
        for i, p in enumerate(cat.get("pistas", [])):
            if p.get("id") in ids_musica:
                err("K1 pista repetida %s" % p.get("id"))
            ids_musica.add(p.get("id"))
            if paletas and p.get("paleta") not in paletas:
                err("K1 pistas[%d] paleta %r desconocida" % (i, p.get("paleta")))
            if not os.path.exists(os.path.join(RAIZ, "design", "musica", str(p.get("archivo", "")))):
                err("K1 pistas[%d] falta design/musica/%s" % (i, p.get("archivo")))
            por_paleta[p.get("paleta")] = por_paleta.get(p.get("paleta"), 0) + 1
        for pal in paletas or []:
            if por_paleta.get(pal, 0) < 2:
                err("K1 la paleta %s tiene %d pista(s) de música; se piden ≥ 2" % (pal, por_paleta.get(pal, 0)))
    # K2: biblioteca fija de efectos de /video (design/sfx/), comprobada por scripts/sfx.py
    try:
        import sfx as _sfx  # noqa: E402
        for x in _sfx.fallas_k2():
            err(x)
    except Exception as e:  # noqa: BLE001
        err("K2 scripts/sfx.py: %s" % e)
    # K3: biblioteca fija de iconos de /video (design/iconos/), solo si está importada (scripts/iconos.py)
    if os.path.exists(os.path.join(RAIZ, "design", "iconos", "catalogo.json")):
        try:
            import iconos as _iconos  # noqa: E402
            for x in _iconos.fallas_k3():
                err("K3 " + x)
        except Exception as e:  # noqa: BLE001
            err("K3 scripts/iconos.py: %s" % e)
    # K4: biblioteca de animaciones de la escena explica (video/animaciones/, scripts/animaciones.py)
    if os.path.isdir(os.path.join(RAIZ, "video", "animaciones")):
        try:
            import animaciones as _anim  # noqa: E402
            for x in _anim.fallas_k4():
                err("K4 " + x)
        except Exception as e:  # noqa: BLE001
            err("K4 scripts/animaciones.py: %s" % e)
    rel_mem = "memoria/videos.json"
    if not os.path.exists(os.path.join(RAIZ, rel_mem)):  # ausente = ok: memoria.py lo crea con el primer video
        return
    d = cargar(rel_mem) or {}
    ids = set()
    for i, v in enumerate(d.get("videos", [])):
        for campo in ("id", "fecha", "slug", "hilo_id", "paleta", "duracion", "duracion_s", "n_escenas", "musica",
                      "ruta_video", "ruta_hilo", "estado"):
            if campo not in v:
                err("M8 videos[%d] sin %s" % (i, campo))
        if v.get("id") in ids:
            err("M8 videos: id repetido %s" % v.get("id"))
        ids.add(v.get("id"))
        if v.get("duracion") not in ("corto", "medio", "largo"):
            err("M8 videos[%d] duracion %r no es corto|medio|largo" % (i, v.get("duracion")))
        if v.get("estado") not in ("listo", "publicado", "incompleto"):
            err("M8 videos[%d] estado %r" % (i, v.get("estado")))
        if paletas and v.get("paleta") not in paletas:
            err("M8 videos[%d] paleta %r desconocida" % (i, v.get("paleta")))
        if ids_musica and v.get("musica") not in ids_musica:
            err("M8 videos[%d] música %r no está en el catálogo" % (i, v.get("musica")))
        rv, rh = str(v.get("ruta_video", "")), str(v.get("ruta_hilo", ""))
        if os.path.isabs(rv) or os.path.isabs(rh):
            err("M8 videos[%d] rutas deben ser relativas a la raíz" % i)
            continue
        if not os.path.exists(os.path.join(RAIZ, rv, "guion.json")):
            err("M8 videos[%d] %s sin guion.json" % (i, rv))
        elif not os.path.exists(os.path.join(RAIZ, rv, "video.mp4")):
            warn("M8 videos[%d] %s/video.mp4 no está (fuera de git: se regenera con /video)" % (i, rv))
        if not os.path.exists(os.path.join(RAIZ, rh, "hilo.json")):
            err("M8 videos[%d] ruta_hilo %s sin hilo.json" % (i, rh))


def main():
    if "--huerfanas" in sys.argv:
        return huerfanas("--borrar" in sys.argv)
    quiet = "--quiet" in sys.argv
    paletas = validar_tokens()
    validar_fuentes()
    hilos_registrados = validar_hilos(paletas)
    validar_informes(paletas, hilos_registrados)
    validar_datos(paletas)
    validar_ideas(paletas)
    validar_calendario()
    validar_videos(paletas)
    for a in AVISOS:
        print("AVISO  " + a)
    for e in ERRORES:
        print("ERROR  " + e, file=sys.stderr)
    if not quiet or ERRORES:
        print("[validate] %d error(es) · %d aviso(s)" % (len(ERRORES), len(AVISOS)))
    return 1 if ERRORES else 0


if __name__ == "__main__":
    sys.exit(main())
