#!/usr/bin/env python3
"""Copia el código común (scripts/workflow_comun.js) en cada workflow, entre «// <comun>» y «// </comun>».

El sandbox de Workflow no importa módulos: agentRol, conReparacion, avisar, la verificación mecánica
(FORMA_ITEM, cierreVer, conMecanico) y el rechequeo viven una sola vez en workflow_comun.js y este script los
replica en hilo.js, dato.js, investigacion.js, video.js, noticias.js, historia.js y explica.js. check_workflows.py (W9) falla si una copia difiere de la fuente.

Uso:
  python3 scripts/armar_workflows.py            reescribe los bloques de los workflows
  python3 scripts/armar_workflows.py --check    solo comprueba (exit 1 si alguno difiere)
Salida: 0 ok · 1 difiere o falta el marcador · 2 uso incorrecto
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(RAIZ, "scripts", "workflow_comun.js")
WORKFLOWS = ["hilo.js", "dato.js", "investigacion.js", "video.js", "noticias.js", "historia.js", "explica.js"]
INI, FIN = "// <comun>", "// </comun>"


def bloque_fuente():
    with open(FUENTE, encoding="utf-8") as fh:
        return fh.read().rstrip("\n") + "\n"


def partes(texto):
    """(antes, bloque, después) o None si faltan los marcadores."""
    import re
    ma = re.search(r"^" + re.escape(INI) + r"(?: .*)?$", texto, re.M)
    mb = re.search(r"^" + re.escape(FIN) + r"\s*$", texto, re.M)
    if not ma or not mb or mb.start() < ma.end():
        return None
    a_fin = ma.end() + 1
    return texto[:a_fin], texto[a_fin:mb.start()], texto[mb.start():]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="solo comprueba")
    a = ap.parse_args()
    src = bloque_fuente()
    fallos = 0
    for w in WORKFLOWS:
        ruta = os.path.join(RAIZ, ".claude", "workflows", w)
        with open(ruta, encoding="utf-8") as fh:
            t = fh.read()
        p = partes(t)
        if not p:
            print("FALLA %s: faltan los marcadores %s … %s" % (w, INI, FIN))
            fallos += 1
            continue
        if p[1] == src:
            print("OK     %s" % w)
            continue
        if a.check:
            print("FALLA %s: el bloque común difiere de scripts/workflow_comun.js (corre python3 scripts/armar_workflows.py)" % w)
            fallos += 1
            continue
        with open(ruta, "w", encoding="utf-8") as fh:
            fh.write(p[0] + src + p[2])
        print("ESCRITO %s" % w)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
