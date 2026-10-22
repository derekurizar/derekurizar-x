#!/usr/bin/env python3
"""Biblioteca FIJA de iconos de /video (design/iconos/): una lista curada de iconos Lucide (licencia ISC; los heredados
de Feather, MIT) que el gancho, los golpes y la definición pueden llevar como acento (`icono: "<id>"` en el guion).

Uso:
  python3 scripts/iconos.py --importar [--version 0.547.0]   baja los SVG del tag fijado a design/iconos/ (UNA vez),
                                                             escribe catalogo.json y LICENSE.txt
  python3 scripts/iconos.py --check                          K3: cada icono del catálogo existe y es un SVG 24×24
  python3 scripts/iconos.py --lista                          los ids con sus palabras clave (para el digesto)

Los SVG se guardan tal cual (24×24, stroke currentColor): la página los pinta con la tinta de la paleta.
Salida: 0 ok · 1 fallo · 2 uso incorrecto.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(RAIZ, "design", "iconos")
VERSION = "0.547.0"
URL = "https://raw.githubusercontent.com/lucide-icons/lucide/%s/icons/%s.svg"
URL_LICENCIA = "https://raw.githubusercontent.com/lucide-icons/lucide/%s/LICENSE"

# id de Lucide → palabras clave (lo que la cifra nombra); el guionista elige por ellas
ICONOS = {
    "cloud-rain": "lluvia, precipitación, temporal", "cloud-sun": "clima, canícula, sequía", "sun": "sol, calor, sequía",
    "droplets": "agua, gotas, lluvia", "thermometer": "temperatura, calor, El Niño", "wind": "viento, huracán, tormenta",
    "waves": "mar, océano, inundación", "mountain": "volcán, montaña, altiplano", "flame": "incendio, fuego",
    "wheat": "maíz, cosecha, grano, frijol", "sprout": "siembra, agricultura, campo", "tractor": "agro, finca, producción",
    "utensils": "comida, alimentación, canasta básica", "baby": "niñez, nacimientos, primera infancia",
    "user": "persona, habitante", "users": "población, familias, hogares", "heart-pulse": "salud, mortalidad, hospital",
    "hospital": "hospital, centro de salud", "stethoscope": "médicos, consulta, salud", "syringe": "vacuna, vacunación",
    "graduation-cap": "educación, graduados, escuela", "school": "escuela, aulas, matrícula", "book-open": "lectura, estudio",
    "banknote": "dinero, salario, quetzales", "coins": "precio, costo, inflación", "wallet": "gasto, ingreso, bolsillo",
    "trending-up": "sube, aumento, récord", "trending-down": "baja, caída, descenso", "percent": "porcentaje, tasa",
    "scale": "justicia, ley, balanza", "shield": "seguridad, protección, policía", "siren": "emergencia, alerta, homicidios",
    "gavel": "justicia, sentencias, tribunales", "zap": "electricidad, energía, luz", "fuel": "combustible, gasolina, diésel",
    "car": "vehículos, tránsito", "bus": "transporte, pasajeros", "plane": "migración, vuelos, deportados",
    "map-pin": "lugar, municipio, departamento", "map": "territorio, país, mapa", "house": "vivienda, hogar, casa",
    "building-2": "ciudad, edificio, empresa", "factory": "industria, fábrica, exportación", "calendar": "fecha, año, plazo",
    "clock": "tiempo, horas, espera", "hourglass": "demora, plazo vencido", "globe": "mundo, países, comparación",
    "flag": "nación, Guatemala, bandera", "landmark": "Estado, Congreso, gobierno", "vote": "elecciones, voto",
}


def bajar(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def importar(version):
    os.makedirs(DIR, exist_ok=True)
    fallos, iconos = [], []
    for id_, claves in ICONOS.items():
        try:
            svg = bajar(URL % (version, id_))
        except urllib.error.HTTPError as e:
            fallos.append("%s (HTTP %d)" % (id_, e.code))
            continue
        if not svg.lstrip().startswith(b"<svg"):
            fallos.append("%s (no es SVG)" % id_)
            continue
        with open(os.path.join(DIR, id_ + ".svg"), "wb") as f:
            f.write(svg)
        iconos.append({"id": id_, "archivo": id_ + ".svg", "claves": claves})
        print("  %-16s %s" % (id_, claves))
    if fallos:
        print("ERROR: no se bajaron: %s" % ", ".join(fallos))
        return 1
    with open(os.path.join(DIR, "LICENSE.txt"), "wb") as f:
        f.write(bajar(URL_LICENCIA % version))
    cat = {"fuente": "Lucide", "version": version, "licencia": "ISC (los iconos heredados de Feather, MIT); ver LICENSE.txt",
           "fecha": datetime.date.today().isoformat(), "uso": "acento opcional en gancho, golpe y definición de /video (icono: <id>); ≤ 1 por escena",
           "iconos": iconos}
    with open(os.path.join(DIR, "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
    print("catalogo.json: %d iconos de Lucide %s → %s" % (len(iconos), version, os.path.relpath(DIR, RAIZ)))
    return 0


def catalogo():
    ruta = os.path.join(DIR, "catalogo.json")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def fallas_k3():
    """K3: los iconos del catálogo existen, son SVG con viewBox 0 0 24 24, y no hay SVG fuera del catálogo."""
    cat = catalogo()
    if not cat:
        return ["no hay design/iconos/catalogo.json (corre make iconos)"]
    fallos = []
    ids = set()
    for ic in cat["iconos"]:
        ids.add(ic["id"])
        ruta = os.path.join(DIR, ic["archivo"])
        if not os.path.exists(ruta):
            fallos.append("falta %s" % ic["archivo"])
            continue
        with open(ruta, encoding="utf-8") as f:
            svg = f.read()
        if not svg.lstrip().startswith("<svg") or 'viewBox="0 0 24 24"' not in svg:
            fallos.append("%s no es un SVG 24×24" % ic["archivo"])
    sueltos = sorted(f for f in os.listdir(DIR) if f.endswith(".svg") and f[:-4] not in ids)
    if sueltos:
        fallos.append("SVG fuera del catálogo: %s" % ", ".join(sueltos))
    if not os.path.exists(os.path.join(DIR, "LICENSE.txt")):
        fallos.append("falta LICENSE.txt")
    return fallos


def check():
    fallos = fallas_k3()
    for x in fallos:
        print("K3 FALLA: %s" % x)
    if not fallos:
        cat = catalogo()
        print("K3 ok: %d iconos (Lucide %s)" % (len(cat["iconos"]), cat["version"]))
    return 1 if fallos else 0


def lista():
    cat = catalogo()
    if not cat:
        print("sin catálogo (make iconos)")
        return 1
    for ic in cat["iconos"]:
        print("%-16s %s" % (ic["id"], ic["claves"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--importar", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--lista", action="store_true")
    ap.add_argument("--version", default=VERSION, help="tag de Lucide (por defecto %s)" % VERSION)
    a = ap.parse_args()
    if a.importar:
        return importar(a.version)
    if a.check:
        return check()
    return lista()


if __name__ == "__main__":
    sys.exit(main())
