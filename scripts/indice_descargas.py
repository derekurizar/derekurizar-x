#!/usr/bin/env python3
"""Índice de descargas: sesiones/_descargas/indice.json (caché por URL).

Formato:
  { "<url>": {"archivo": "sesiones/_descargas/x.xlsx", "derivados": ["..._hoja1.csv"],
              "fecha": "2026-09-29T10:00:00", "bytes": 12345, "tipo": "xlsx|pdf|html|csv|json"} }

Lo consultan fetch_tabla.py, fetch_pdf.sh y fetch_api.py antes de descargar. Las rutas
se guardan relativas a la raíz del repo. También sirve como módulo:
  from indice_descargas import buscar, registrar

Uso:
  python3 scripts/indice_descargas.py registrar <url> <archivo> [derivado ...] [--tipo xlsx]
  python3 scripts/indice_descargas.py buscar <url>     # imprime la ruta; exit 1 si no está o el archivo no existe
  python3 scripts/indice_descargas.py listar
Salida: 0 ok · 1 no encontrado/error · 2 uso incorrecto
"""
import argparse
import datetime as _dt
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESCARGAS = os.path.join(RAIZ, "sesiones", "_descargas")
INDICE = os.path.join(DESCARGAS, "indice.json")
TIPOS = {".xlsx": "xlsx", ".xls": "xls", ".pdf": "pdf", ".htm": "html", ".html": "html", ".csv": "csv", ".json": "json", ".txt": "txt"}


def _rel(ruta):
    ruta = os.path.abspath(ruta)
    try:
        r = os.path.relpath(ruta, RAIZ)
        return r if not r.startswith("..") else ruta
    except ValueError:
        return ruta


def _abs(ruta):
    return ruta if os.path.isabs(ruta) else os.path.join(RAIZ, ruta)


def cargar():
    if not os.path.exists(INDICE):
        return {}
    try:
        with open(INDICE, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError:
        print("AVISO: %s corrupto; se ignora" % _rel(INDICE), file=sys.stderr)
        return {}


def guardar(idx):
    os.makedirs(DESCARGAS, exist_ok=True)
    tmp = INDICE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, INDICE)


def tipo_de(archivo):
    return TIPOS.get(os.path.splitext(archivo)[1].lower(), "otro")


def buscar(url):
    """Entrada del índice si la URL está registrada Y su archivo existe; si no, None.
    Añade 'archivo_abs' y 'derivados_abs' (solo los que existen)."""
    e = cargar().get(url)
    if not e:
        return None
    arch = _abs(e.get("archivo", ""))
    if not e.get("archivo") or not os.path.exists(arch):
        return None
    e = dict(e)
    e["archivo_abs"] = arch
    e["derivados_abs"] = [_abs(d) for d in e.get("derivados", []) if os.path.exists(_abs(d))]
    return e


def registrar(url, archivo, derivados=(), tipo=None):
    idx = cargar()
    arch = _abs(archivo)
    idx[url] = {
        "archivo": _rel(arch),
        "derivados": [_rel(d) for d in derivados],
        "fecha": _dt.datetime.now().replace(microsecond=0).isoformat(),
        "bytes": os.path.getsize(arch) if os.path.exists(arch) else 0,
        "tipo": tipo or tipo_de(arch),
    }
    guardar(idx)
    return idx[url]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("registrar", help="registra una descarga")
    r.add_argument("url")
    r.add_argument("archivo")
    r.add_argument("derivados", nargs="*")
    r.add_argument("--tipo", choices=sorted(set(TIPOS.values()) | {"otro"}))
    b = sub.add_parser("buscar", help="imprime el archivo cacheado de una URL")
    b.add_argument("url")
    sub.add_parser("listar", help="lista el índice")
    a = p.parse_args()
    if not a.cmd:
        p.print_help()
        return 2
    if a.cmd == "registrar":
        if not os.path.exists(a.archivo):
            print("ERROR: no existe %s" % a.archivo, file=sys.stderr)
            return 1
        e = registrar(a.url, a.archivo, a.derivados, a.tipo)
        print("registrado %s → %s (%s, %d bytes, %d derivado(s))" % (a.url, e["archivo"], e["tipo"], e["bytes"], len(e["derivados"])))
        return 0
    if a.cmd == "buscar":
        e = buscar(a.url)
        if not e:
            return 1
        print(e["archivo"])
        for d in e["derivados_abs"]:
            print(_rel(d))
        return 0
    idx = cargar()
    if not idx:
        print("(índice vacío: %s)" % _rel(INDICE))
        return 0
    for url, e in sorted(idx.items(), key=lambda kv: kv[1].get("fecha", ""), reverse=True):
        existe = os.path.exists(_abs(e.get("archivo", "")))
        print("%s %-5s %10s  %s\n      %s%s" % ("  " if existe else "✗ ", e.get("tipo", "?"), "{:,}".format(e.get("bytes", 0)), e.get("fecha", "")[:19], url,
                                              ("\n      → %s" % e["archivo"]) + ("".join("\n        · " + d for d in e.get("derivados", []))) if existe else "\n      → (archivo ausente) " + e.get("archivo", "")))
    print("%d entrada(s)" % len(idx))
    return 0


if __name__ == "__main__":
    sys.exit(main())
