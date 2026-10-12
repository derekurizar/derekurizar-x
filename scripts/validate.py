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

Uso: python3 scripts/validate.py [--quiet]   · salida 0 ok · 1 error
"""
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
from ensamblar import HOOKS, MODOS, RE_LINK  # noqa: E402  (una sola lista de ganchos y de modos para todo el framework)
from contar_x import peso_x  # noqa: E402
import ideas as _ideas  # noqa: E402
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

    for carpeta in sorted(glob.glob(os.path.join(RAIZ, "hilos", "*"))):
        if not os.path.isdir(carpeta):
            continue
        rel = os.path.relpath(carpeta, RAIZ)
        for archivo in ("hilo.json", "post.md", "datos.json", "hilo.html"):
            if not os.path.exists(os.path.join(carpeta, archivo)):
                err("%s: falta %s" % (rel, archivo))
        if rel not in registrados:
            warn("%s no está registrado en memoria/hilos.json" % rel)
        hj = os.path.join(carpeta, "hilo.json")
        if not os.path.exists(hj):
            continue
        try:
            h = json.load(open(hj, encoding="utf-8"))
        except json.JSONDecodeError as e:
            err("%s/hilo.json inválido: %s" % (rel, e)); continue
        reg = registrados.get(rel)
        if reg and reg.get("estado") != h.get("estado"):
            e_reg, e_hilo = reg.get("estado"), h.get("estado")
            if e_hilo == "borrador" or "incompleto" in (e_reg, e_hilo):
                err("%s: hilo.json dice estado %r y memoria/hilos.json %r (corre ensamblar.py <sesion> --solo-estado --estado %s)" % (rel, e_hilo, e_reg, e_reg))
            else:
                warn("%s: hilo.json dice estado %r y memoria/hilos.json %r" % (rel, e_hilo, e_reg))
        tuits = h.get("tuits", [])
        if not tuits:
            err("%s/hilo.json sin tuits" % rel); continue
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
    estado = {idea.get("id"): idea.get("estado") for idea in d.get("ideas", [])}
    for h in hilos:
        if h.get("idea_id") and estado.get(h["idea_id"]) not in ("hecha", "en_curso"):
            warn("hilo %s apunta a la idea %s (%s): corre python3 scripts/ideas.py --conciliar" % (
                h.get("id"), h["idea_id"], estado.get(h["idea_id"], "no existe")))


def main():
    quiet = "--quiet" in sys.argv
    paletas = validar_tokens()
    validar_fuentes()
    validar_hilos(paletas)
    validar_datos(paletas)
    validar_ideas(paletas)
    for a in AVISOS:
        print("AVISO  " + a)
    for e in ERRORES:
        print("ERROR  " + e, file=sys.stderr)
    if not quiet or ERRORES:
        print("[validate] %d error(es) · %d aviso(s)" % (len(ERRORES), len(AVISOS)))
    return 1 if ERRORES else 0


if __name__ == "__main__":
    sys.exit(main())
