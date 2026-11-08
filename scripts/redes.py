#!/usr/bin/env python3
"""Redes · la versión vertical de cada tarjeta de un hilo (4:5 y 9:16), en el formato de los videos.

Cada hilo se entrega con dos versiones de cada tarjeta: el PNG de X (tuit_N.png, 1080×1080) y la versión para
carrusel de Instagram, Facebook y TikTok (modo foto) en `redes/`:

  redes/4x5/tuit_N.png    1080×1350 (feed de Instagram y Facebook)
  redes/9x16/tuit_N.png   1080×1920 (TikTok modo foto, historias)
  redes/4x5/contacto.png · redes/9x16/contacto.png

La lámina es la escena de tarjeta de /video: el titular de la tarjeta arriba como golpe (Archivo condensado, en
crema: el acento es de la tarjeta), la tarjeta rearmada en Noche en modo vertical debajo (video/vertical.css: sin su
titular ni su pie) y el pie de la lámina con «Fuente: …», el handle y el contador n/N. Usa el motor de /carrusel
(templates/carrusel/lamina.html, scripts/carrusel.js con sus checks CA9–CA12); /carrusel sigue siendo el carrusel
editorial (portada, «Por qué importa», cierre) y escribe en `carrusel/`, no aquí.

Lo llama scripts/ensamblar.py al entregar un hilo (salvo --sin-redes o --sin-contacto); también se corre a mano sobre
un hilo ya entregado:

  python3 scripts/redes.py hilos/<fecha>-<slug> [--formato 4:5|9:16|ambos]

Salida: 0 ok · 1 falla (tarjeta sin DATA, CA9–CA12 o error de página) · 2 uso incorrecto.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402

HANDLE = "@derekurizargt"
FORMATOS = {"4:5": "4x5", "9:16": "9x16"}


def titular_de(html):
    """El titular de la tarjeta (DATA.titular, 1–3 líneas) en una sola línea: el golpe de la lámina."""
    m = VD.RE_DATA_VISUAL.search(open(html, encoding="utf-8").read())
    if not m:
        return None
    try:
        d = json.loads(m.group(0)[len("const DATA = "):].rstrip().rstrip(";"))
    except json.JSONDecodeError:
        return None
    t = d.get("titular")
    return " ".join(t) if isinstance(t, list) else (t or None)


def generar(hilo_dir, formatos=("4:5", "9:16")):
    """Escribe <hilo_dir>/redes/<4x5|9x16>/tuit_N.png. Devuelve (ok, mensaje)."""
    hilo_dir = os.path.abspath(hilo_dir)
    h = json.load(open(os.path.join(hilo_dir, "hilo.json"), encoding="utf-8"))
    tuits = [t for t in h["tuits"] if t.get("imagen") and os.path.exists(os.path.join(hilo_dir, "tuit_%d.html" % t["n"]))]
    if not tuits:
        return True, "sin tarjetas: no hay versión de redes"
    trabajo = tempfile.mkdtemp(prefix="redes-")
    try:
        avisos = VD.rebasar_tarjetas(hilo_dir, trabajo)   # Noche, aunque el hilo sea clásico (/investigacion)
        if avisos:
            return False, "no pude rearmar las tarjetas en Noche: " + "; ".join(avisos)
        laminas = []
        for k, t in enumerate(tuits, 1):
            golpe = titular_de(os.path.join(hilo_dir, "tuit_%d.html" % t["n"]))
            if not golpe:
                return False, "tuit_%d.html sin DATA.titular: no se arma la lámina" % t["n"]
            laminas.append({"tipo": "tarjeta", "tuit": t["n"], "golpe": golpe, "sin_acento": True, "n": k, "total": len(tuits),
                            "fuente": t.get("fuente") or ""})
        redes_dir = os.path.join(hilo_dir, "redes")
        for formato in formatos:
            json.dump({"version": 1, "formato": formato, "slug": h.get("slug"), "colores": VD.colores(h["paleta"]),
                       "handle": HANDLE, "redes": [], "laminas": laminas},
                      open(os.path.join(trabajo, "laminas.json"), "w", encoding="utf-8"), ensure_ascii=False)
            tmp = os.path.join(trabajo, "out-" + FORMATOS[formato])
            os.makedirs(tmp, exist_ok=True)
            r = subprocess.run(["node", os.path.join(RAIZ, "scripts", "carrusel.js"), "--dir", trabajo, "--out", tmp,
                                "--formato", formato, "--check"], cwd=RAIZ, capture_output=True, text=True)
            if r.returncode:
                return False, "carrusel.js %s salió con %d: %s" % (formato, r.returncode, (r.stdout + r.stderr).strip()[-800:])
            dest = os.path.join(redes_dir, FORMATOS[formato])
            shutil.rmtree(dest, ignore_errors=True)
            os.makedirs(dest)
            for l in laminas:
                shutil.move(os.path.join(tmp, "lamina_%02d.png" % l["n"]), os.path.join(dest, "tuit_%d.png" % l["tuit"]))
            r = subprocess.run(["node", os.path.join(RAIZ, "scripts", "contacto.js"), dest, "--celda", "360"],
                               cwd=RAIZ, capture_output=True, text=True)
            if r.returncode:
                return False, "contacto.js: " + (r.stderr or r.stdout).strip()[:300]
        return True, "redes/ %s · %d tarjetas" % (" + ".join(FORMATOS[f] for f in formatos), len(laminas))
    finally:
        shutil.rmtree(trabajo, ignore_errors=True)


def faltan(hilo_dir):
    """Las versiones de redes que faltan en un hilo entregado (para validate.py H4)."""
    h = json.load(open(os.path.join(hilo_dir, "hilo.json"), encoding="utf-8"))
    out = []
    for t in h.get("tuits", []):
        if t.get("imagen"):
            for sub in FORMATOS.values():
                if not os.path.exists(os.path.join(hilo_dir, "redes", sub, "tuit_%d.png" % t["n"])):
                    out.append("redes/%s/tuit_%d.png" % (sub, t["n"]))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("hilo", help="carpeta de entrega del hilo (con hilo.json)")
    p.add_argument("--formato", choices=["4:5", "9:16", "ambos"], default="ambos")
    a = p.parse_args()
    if not os.path.isfile(os.path.join(a.hilo, "hilo.json")):
        p.error("%s no tiene hilo.json" % a.hilo)
    ok, msg = generar(a.hilo, ("4:5", "9:16") if a.formato == "ambos" else (a.formato,))
    print("[redes] " + msg, file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
