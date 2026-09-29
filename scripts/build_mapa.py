#!/usr/bin/env python3
"""Inyecta la geometría de los 22 departamentos en templates/graficos/mapa.html.

Lee design/mapa_geometria.svg (22 <path> con id GT01–GT22, name y d) y (re)escribe
en la plantilla el bloque entre los marcadores

    // MAPA:GEOMETRIA:INICIO
    // MAPA:GEOMETRIA:FIN

con `const GEOMETRIA = { viewBox: "…", deptos: { GT01: { n: "Guatemala", d: "M…" }, … } };`.

Por qué así:
  - La plantilla es un FRAGMENTO: la base crea el ÚNICO <svg> por JS (R4). La
    geometría viaja como texto JS y el fragmento no lleva ningún «<svg» literal
    (dos <svg> = el bug del 300×150).
  - El bloque va DESPUÉS de `const DATA` porque scripts/materializar.py sustituye
    el PRIMER `const DATA = {...};` (regex hasta el primer «\\n};\\n»).
  - Los nombres del svg pueden venir abreviados («Chimal.», «Quezaltenango»); la
    tabla NOMBRES de la plantilla lleva los 22 oficiales y aquí se verifica que
    cada id del svg corresponde a ese nombre.

Uso:
  python3 scripts/build_mapa.py [--geometria design/mapa_geometria.svg] [--destino ruta.html …]
  python3 scripts/build_mapa.py --check    # no escribe: 22 ids, nombres, bloque al día, DATA antes, cero <svg>
Sin --destino inyecta en templates/graficos/mapa.html y en templates/.pruebas/estres-mapa.html
(la prueba de estrés lleva el mismo render() con otro DATA).
Salida: 0 ok · 1 error · 2 uso incorrecto
"""
import argparse
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEOMETRIA = os.path.join(RAIZ, "design", "mapa_geometria.svg")
DESTINOS = [os.path.join(RAIZ, "templates", "graficos", "mapa.html"),
            os.path.join(RAIZ, "templates", ".pruebas", "estres-mapa.html")]
INICIO = "// MAPA:GEOMETRIA:INICIO"
FIN = "// MAPA:GEOMETRIA:FIN"

# Nombres oficiales (INE). Misma tabla que `const NOMBRES` en la plantilla.
NOMBRES = {
    "GT01": "Guatemala", "GT02": "El Progreso", "GT03": "Sacatepéquez", "GT04": "Chimaltenango",
    "GT05": "Escuintla", "GT06": "Santa Rosa", "GT07": "Sololá", "GT08": "Totonicapán",
    "GT09": "Quetzaltenango", "GT10": "Suchitepéquez", "GT11": "Retalhuleu", "GT12": "San Marcos",
    "GT13": "Huehuetenango", "GT14": "Quiché", "GT15": "Baja Verapaz", "GT16": "Alta Verapaz",
    "GT17": "Petén", "GT18": "Izabal", "GT19": "Zacapa", "GT20": "Chiquimula",
    "GT21": "Jalapa", "GT22": "Jutiapa",
}
# Grafías alternativas que aparecen en fuentes cartográficas → nombre oficial normalizado.
ALIAS = {"quezaltenango": "quetzaltenango", "chimal": "chimaltenango", "elquiche": "quiche", "peten": "peten"}


def normalizar(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]", "", s.lower())


def nombre_coincide(nombre_svg, oficial):
    a, b = normalizar(nombre_svg.rstrip(". ")), normalizar(oficial)
    a = ALIAS.get(a, a)
    return a == b or (len(a) >= 4 and b.startswith(a))


def extraer(ruta):
    """Devuelve (viewBox, {id: {"n": nombre_svg, "d": d}}) o lanza ValueError."""
    with open(ruta, encoding="utf-8") as fh:
        crudo = fh.read()
    limpio = re.sub(r"<!--.*?-->", "", crudo, flags=re.S)
    if len(re.findall(r"<svg\b", limpio, re.I)) != 1:
        raise ValueError("%s: debe tener exactamente una apertura <svg>" % ruta)
    m = re.search(r'viewBox="([^"]+)"', limpio)
    if not m:
        raise ValueError("%s: sin viewBox" % ruta)
    view_box = m.group(1).strip()
    deptos = {}
    for tag in re.findall(r"<path\b[^>]*>", limpio, re.I | re.S):
        attrs = dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag))
        pid, nombre, d = attrs.get("id", ""), attrs.get("name", ""), attrs.get("d", "").strip()
        if not re.fullmatch(r"GT\d\d", pid):
            raise ValueError("%s: <path> sin id GTnn (%r)" % (ruta, pid))
        if pid in deptos:
            raise ValueError("%s: id repetido %s" % (ruta, pid))
        if not d or '"' in d or "\\" in d or "\n" in d:
            raise ValueError("%s: %s tiene un atributo d vacío o con caracteres no admitidos" % (ruta, pid))
        deptos[pid] = {"n": nombre, "d": d}
    faltan = sorted(set(NOMBRES) - set(deptos))
    sobran = sorted(set(deptos) - set(NOMBRES))
    if faltan or sobran:
        raise ValueError("%s: ids faltantes %s · ids desconocidos %s" % (ruta, faltan or "—", sobran or "—"))
    for pid, dep in deptos.items():
        if not nombre_coincide(dep["n"], NOMBRES[pid]):
            raise ValueError("%s: %s se llama %r en el svg pero la tabla oficial dice %r" % (ruta, pid, dep["n"], NOMBRES[pid]))
    return view_box, deptos


def bloque(view_box, deptos, origen):
    L = [INICIO + " · generado por scripts/build_mapa.py desde %s · NO EDITAR A MANO" % origen,
         "const GEOMETRIA = {",
         "  viewBox: %s," % json.dumps(view_box),
         "  deptos: {"]
    ids = sorted(deptos)
    for i, pid in enumerate(ids):
        L.append("    %s: { n: %s, d: %s }%s" % (pid, json.dumps(deptos[pid]["n"], ensure_ascii=False),
                                                json.dumps(deptos[pid]["d"]), "," if i < len(ids) - 1 else ""))
    L += ["  }", "};", FIN]
    return "\n".join(L)


def partes(html):
    """(antes, bloque_actual, despues) según los marcadores; ValueError si faltan o se repiten."""
    ini = [m.start() for m in re.finditer(re.escape(INICIO), html)]
    fin = [m.start() for m in re.finditer(re.escape(FIN), html)]
    if len(ini) != 1 or len(fin) != 1:
        raise ValueError("la plantilla debe tener exactamente un %s y un %s (hay %d y %d)" % (INICIO, FIN, len(ini), len(fin)))
    if fin[0] < ini[0]:
        raise ValueError("%s aparece antes que %s" % (FIN, INICIO))
    f = fin[0] + len(FIN)
    return html[:ini[0]], html[ini[0]:f], html[f:]


def verificar(html, esperado):
    """Lista de problemas del HTML ya inyectado (vacía = ok)."""
    fallos = []
    try:
        antes, actual, _ = partes(html)
    except ValueError as e:
        return [str(e)]
    if actual != esperado:
        fallos.append("el bloque GEOMETRIA está desactualizado: corre python3 scripts/build_mapa.py")
    if len(re.findall(r"GT\d\d: \{ n:", actual)) != 22:
        fallos.append("el bloque GEOMETRIA no tiene 22 departamentos")
    m = re.search(r"const DATA = \{", antes)
    if not m:
        fallos.append("`const DATA = {` debe ir ANTES del bloque GEOMETRIA (materializar.py sustituye el primero)")
    elif "\n};\n" not in antes[m.end():]:
        fallos.append("el bloque `const DATA = {...};` no cierra con «};» en su propia línea antes de la geometría")
    if re.search(r"<svg\b", html, re.I):
        fallos.append("la plantilla contiene «<svg» literal: el único <svg> lo crea la base por JS (R4)")
    if "const NOMBRES" in html:
        mn = re.search(r"const NOMBRES = \{(.*?)\};", html, re.S)
        tabla = dict(re.findall(r'(GT\d\d):\s*"([^"]+)"', mn.group(1))) if mn else {}
        if tabla != NOMBRES:
            dif = [k for k in sorted(set(tabla) | set(NOMBRES)) if tabla.get(k) != NOMBRES.get(k)]
            fallos.append("la tabla NOMBRES de la plantilla no coincide con la oficial en: " + ", ".join(dif))
    else:
        fallos.append("la plantilla no define `const NOMBRES = {...}`")
    if re.search(r"https?://", html):
        fallos.append("la plantilla contiene una URL")
    return fallos


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--geometria", default=GEOMETRIA)
    p.add_argument("--destino", action="append", help="HTML con los marcadores (repetible; por defecto la plantilla y su prueba de estrés)")
    p.add_argument("--check", action="store_true", help="no escribe: solo verifica")
    a = p.parse_args()
    destinos = a.destino or DESTINOS
    for ruta in [a.geometria] + destinos:
        if not os.path.exists(ruta):
            print("ERROR: no existe %s" % ruta, file=sys.stderr)
            return 2
    try:
        view_box, deptos = extraer(a.geometria)
    except ValueError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    origen = os.path.relpath(a.geometria, RAIZ)
    nuevo = bloque(view_box, deptos, origen)
    errores = 0
    for destino in destinos:
        with open(destino, encoding="utf-8") as fh:
            html = fh.read()
        rel = os.path.relpath(destino, RAIZ)
        if a.check:
            fallos = verificar(html, nuevo)
            for f in fallos:
                print("FALLO %s: %s" % (rel, f), file=sys.stderr)
            if not fallos:
                print("OK (--check): %s · 22 departamentos · viewBox %s · sin <svg> literal" % (rel, view_box))
            errores += bool(fallos)
            continue
        try:
            antes, actual, despues = partes(html)
        except ValueError as e:
            print("ERROR %s: %s" % (rel, e), file=sys.stderr)
            errores += 1
            continue
        salida = antes + nuevo + despues
        fallos = verificar(salida, nuevo)
        if fallos:
            for f in fallos:
                print("FALLO %s: %s" % (rel, f), file=sys.stderr)
            errores += 1
            continue
        if salida != html:
            with open(destino, "w", encoding="utf-8") as fh:
                fh.write(salida)
            print("OK -> %s (geometría de %s, %d bytes, %s)" % (rel, origen, len(nuevo), "actualizado" if actual.strip() != INICIO else "inyectado"))
        else:
            print("OK (sin cambios): %s ya tiene la geometría al día" % rel)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
