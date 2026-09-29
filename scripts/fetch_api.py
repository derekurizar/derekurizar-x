#!/usr/bin/env python3
"""GET a una API (JSON) con UA de navegador y caché por sha1 de la URL.

Guarda la respuesta en sesiones/_descargas/api/<sha1>.json (o --out), la registra
en sesiones/_descargas/indice.json y muestra la ruta más las primeras 40 líneas
formateadas (json.dumps indent=2) o crudas con --crudo. Si la URL ya está en el
índice y el archivo existe, no vuelve a descargar salvo --refrescar.

Uso:
  python3 scripts/fetch_api.py "https://api.worldbank.org/v2/country/GT/indicator/BX.TRF.PWKR.DT.GD.ZS?format=json" [--out ruta] [--crudo] [--refrescar] [--lineas 40]
Salida: 0 ok · 1 error de red/HTTP · 2 uso incorrecto
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import indice_descargas as idx  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
DIR_API = os.path.join(idx.DESCARGAS, "api")


def descargar(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, text/plain, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def mostrar(ruta, crudo, lineas):
    raw = open(ruta, "rb").read()
    texto = raw.decode("utf-8", errors="replace")
    if not crudo:
        try:
            texto = json.dumps(json.loads(texto), ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            print("AVISO: la respuesta no es JSON válido; se muestra cruda", file=sys.stderr)
    ls = texto.splitlines()
    for l in ls[:lineas]:
        print(l[:300])
    if len(ls) > lineas:
        print("… (%d líneas más; archivo completo en %s)" % (len(ls) - lineas, ruta))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url")
    p.add_argument("--out", help="ruta de guardado (default sesiones/_descargas/api/<sha1>.json)")
    p.add_argument("--crudo", action="store_true", help="muestra el cuerpo tal cual, sin reformatear")
    p.add_argument("--refrescar", action="store_true", help="ignora la caché y vuelve a descargar")
    p.add_argument("--lineas", type=int, default=40)
    a = p.parse_args()
    if not a.url.lower().startswith(("http://", "https://")):
        print("ERROR: la URL debe empezar por http:// o https://", file=sys.stderr)
        return 2

    sha = hashlib.sha1(a.url.encode("utf-8")).hexdigest()
    out = os.path.abspath(a.out) if a.out else os.path.join(DIR_API, sha + ".json")
    cache = None if a.refrescar else idx.buscar(a.url)
    if cache and (not a.out or os.path.abspath(cache["archivo_abs"]) == out):
        print("(caché) → %s" % cache["archivo"])
        mostrar(cache["archivo_abs"], a.crudo, a.lineas)
        return 0

    try:
        cuerpo = descargar(a.url)
    except urllib.error.HTTPError as e:
        print("ERROR HTTP %s en %s" % (e.code, a.url), file=sys.stderr)
        return 1
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print("ERROR de red: %s" % e, file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as fh:
        fh.write(cuerpo)
    try:
        json.loads(cuerpo.decode("utf-8"))
        tipo = "json"
    except (json.JSONDecodeError, UnicodeDecodeError):
        tipo = "txt"
        print("AVISO: la respuesta no es JSON; se guardó tal cual", file=sys.stderr)
    e = idx.registrar(a.url, out, tipo=tipo)
    print("descargado → %s (%s bytes)" % (e["archivo"], "{:,}".format(e["bytes"])))
    mostrar(out, a.crudo, a.lineas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
