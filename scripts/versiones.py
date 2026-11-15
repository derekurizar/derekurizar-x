#!/usr/bin/env python3
"""versiones.py — las versiones fijadas de lo que el render trae de fuera, en UN solo sitio.

Lo importan scripts/mesa.py (la mesa de archivo: vertical y 16:9) y scripts/maqueta3d.py (la maqueta 3D); scripts/doctor.sh
lo lee con `python3 scripts/versiones.py`. Solo `os`: no importa nada del proyecto, así nadie carga un módulo grande (ni
cierra un ciclo de imports) por una constante.

  HF_VERSION     HyperFrames, por npx (`HF` es el comando ya armado). Pide Node >= NODE_MIN.
  GSAP_JS        GSAP vendorizado en design/vendor/: los proyectos lo copian a assets/ (el render no llama a la red)
  THREE_DIR      three.js vendorizado en design/vendor/ (la maqueta 3D)

Cambiar una versión es cambiarla AQUÍ (y, para GSAP y three, traer el archivo nuevo a design/vendor/).

Uso: versiones.py [hf|gsap|three|node]   imprime una versión (sin argumento, todas)
Exit 0 ok · 2 uso incorrecto.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(RAIZ, "design", "vendor")

HF_VERSION = "0.9.28"
HF = ["npx", "--yes", "hyperframes@" + HF_VERSION]
NODE_MIN = 22            # lo que pide HyperFrames: sin él la mesa de archivo no dibuja ni renderiza

GSAP_VERSION = "3.15.0"
GSAP_JS = os.path.join(VENDOR, "gsap-%s.min.js" % GSAP_VERSION)

THREE_VERSION = "0.187.0"
THREE_DIR = os.path.join(VENDOR, "three-%s" % THREE_VERSION)

VERSIONES = {"hf": HF_VERSION, "gsap": GSAP_VERSION, "three": THREE_VERSION, "node": str(NODE_MIN)}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cual", nargs="?", choices=sorted(VERSIONES), help="la versión que se imprime (sin argumento, todas)")
    a = ap.parse_args()
    if a.cual:
        print(VERSIONES[a.cual])
    else:
        for k, v in VERSIONES.items():
            print("%s %s" % (k, v))
    sys.exit(0)
