#!/usr/bin/env python3
"""Materializa los visuales de un hilo DESDE guion.json (fuente de verdad única).

Para cada tuit con `visual`, ensambla la plantilla (scripts/nuevo_visual.py),
sustituye el bloque `const DATA = {...};` por el JSON del guion
(cabecera + `visual.datos`) y renderiza con `scripts/render.js --check`.
Así el visualista no edita HTML a mano: corrige el guion y vuelve a correr.

Ajustes sin pisarse entre visualistas en paralelo: cada visualista escribe SOLO
<sesion>/visuales/tuit_N.ajuste.json (un objeto parcial del `visual`: kicker,
titular, nota, fuente, leyenda, datos, plantilla). materializar lo fusiona sobre
el guion al ensamblar. Nadie toca guion.json hasta que el productor corre
`--consolidar`, que funde los ajustes en guion.json y los borra.

Uso:
  python3 scripts/materializar.py sesiones/<slug> [--tuit N] [--sin-render] [--forzar-plantilla X] [--consolidar]
Salida: 0 todos los visuales pasan el gate · 1 alguno falla · 2 uso incorrecto
Escribe <sesion>/visuales/tuit_N.html y tuit_N.png.
"""
import argparse
import json
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RE_DATA = re.compile(r"const DATA = \{.*?\n\};\n", re.S)
CABECERA = ("kicker", "titular", "nota", "fuente", "handle", "leyenda")


def data_de(visual, handle):
    d = {}
    for k in CABECERA:
        if k in visual and visual[k] not in (None, ""):
            d[k] = visual[k]
    d.setdefault("nota", "")
    d.setdefault("handle", handle)
    datos = visual.get("datos") or {}
    for k, v in datos.items():
        d[k] = v
    d.setdefault("formato", {"prefijo": "", "sufijo": "", "decimales": 0, "miles": True, "escala": 1})
    return d


def ruta_ajuste(sesion, n):
    return os.path.join(sesion, "visuales", "tuit_%d.ajuste.json" % n)


def fusionar(base, ajuste):
    """Fusiona un ajuste sobre un visual: claves de primer nivel se sustituyen,
    salvo `datos`, que se fusiona por claves (un ajuste con solo `formato` no
    borra el resto de los datos)."""
    v = dict(base)
    for k, val in ajuste.items():
        if k == "datos" and isinstance(val, dict) and isinstance(v.get("datos"), dict):
            d = dict(v["datos"])
            d.update(val)
            v["datos"] = d
        else:
            v[k] = val
    return v


def con_ajuste(sesion, tuit):
    """Devuelve el visual del tuit con su ajuste (si existe) fusionado encima."""
    v = dict(tuit["visual"])
    ra = ruta_ajuste(sesion, tuit["n"])
    if os.path.exists(ra):
        with open(ra, encoding="utf-8") as fh:
            aj = json.load(fh)
        v = fusionar(v, aj)
        v["_ajustado"] = True
    return v


def materializar_uno(sesion, guion, tuit, render=True, plantilla_forzada=None):
    v = con_ajuste(sesion, tuit)
    n = tuit["n"]
    plantilla = plantilla_forzada or v.get("plantilla_final") or v["plantilla"]
    paleta = guion.get("paleta", "cielo")
    vis_dir = os.path.join(sesion, "visuales")
    os.makedirs(vis_dir, exist_ok=True)
    html = os.path.join(vis_dir, "tuit_%d.html" % n)
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "nuevo_visual.py"), plantilla, html, "--paleta", paleta],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return False, "T%d: %s" % (n, (r.stderr or r.stdout).strip())
    with open(html, encoding="utf-8") as fh:
        src = fh.read()
    data = data_de(v, guion.get("handle", "@DerekUrizar"))
    bloque = "const DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    nuevo, k = RE_DATA.subn(bloque, src, count=1)
    if k != 1:
        return False, "T%d: la plantilla %s no tiene un bloque `const DATA = {...};` reconocible" % (n, plantilla)
    with open(html, "w", encoding="utf-8") as fh:
        fh.write(nuevo)
    if plantilla_forzada:
        # Queda anotado como ajuste para que --consolidar lo lleve al guion.
        ra = ruta_ajuste(sesion, n)
        aj = json.load(open(ra, encoding="utf-8")) if os.path.exists(ra) else {}
        aj["plantilla_final"] = plantilla_forzada
        json.dump(aj, open(ra, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    png = os.path.relpath(html[:-5] + ".png", RAIZ)
    if not render:
        return True, "T%d: %s ensamblado (sin render)" % (n, plantilla)
    r = subprocess.run(["node", os.path.join(RAIZ, "scripts", "render.js"), html, "--check"], capture_output=True, text=True)
    salida = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        return False, "T%d (%s) NO pasa el gate:\n%s" % (n, plantilla, salida)
    return True, "T%d (%s%s) OK -> %s" % (n, plantilla, " · con ajuste" if v.get("_ajustado") else "", png)


def consolidar(sesion, guion):
    """Funde los tuit_N.ajuste.json en guion.json y los borra. Devuelve cuántos."""
    k = 0
    for t in guion.get("tuits", []):
        if not t.get("visual"):
            continue
        ra = ruta_ajuste(sesion, t["n"])
        if not os.path.exists(ra):
            continue
        aj = json.load(open(ra, encoding="utf-8"))
        t["visual"] = fusionar(t["visual"], aj)
        os.remove(ra)
        k += 1
    if k:
        with open(os.path.join(sesion, "guion.json"), "w", encoding="utf-8") as fh:
            json.dump(guion, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return k


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sesion")
    p.add_argument("--tuit", type=int, help="solo ese número de tuit")
    p.add_argument("--sin-render", action="store_true")
    p.add_argument("--forzar-plantilla", help="usa otra plantilla (solo con --tuit); queda anotada como plantilla_final en el ajuste")
    p.add_argument("--consolidar", action="store_true", help="funde los tuit_N.ajuste.json en guion.json (solo el productor) y re-renderiza")
    a = p.parse_args()
    sesion = os.path.abspath(a.sesion)
    ruta_guion = os.path.join(sesion, "guion.json")
    if not os.path.exists(ruta_guion):
        print("ERROR: no existe " + ruta_guion, file=sys.stderr); return 2
    with open(ruta_guion, encoding="utf-8") as fh:
        guion = json.load(fh)
    if a.forzar_plantilla and not a.tuit:
        p.error("--forzar-plantilla requiere --tuit")
    if a.consolidar:
        print("[materializar] %d ajuste(s) consolidado(s) en guion.json" % consolidar(sesion, guion))
    fallos = 0
    for t in guion.get("tuits", []):
        if a.tuit and t.get("n") != a.tuit:
            continue
        if not t.get("visual"):
            continue
        ok, msg = materializar_uno(sesion, guion, t, render=not a.sin_render, plantilla_forzada=a.forzar_plantilla)
        print(("OK   " if ok else "FALLO ") + msg, file=sys.stdout if ok else sys.stderr)
        fallos += (not ok)
    print("[materializar] %d fallo(s)" % fallos)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
