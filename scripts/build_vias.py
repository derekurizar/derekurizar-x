#!/usr/bin/env python3
"""Red vial real de una ciudad (OpenStreetMap) → design/vias/<id>.json, para la escena `vias` de /video y /historia.

Lee la receta design/vias/<id>.fuente.json (recuadro, lienzo, arterias con los nombres o `ref` de sus tramos, lugares
con su latitud y longitud), baja UNA vez los caminos del recuadro por la API Overpass (caché en
sesiones/_descargas/vias/<id>.osm.json) y escribe design/vias/<id>.json:

    { id, nombre, viewBox, lienzo, bbox, atribucion, generado,
      capas:    [{clase, ancho, opacidad, d}]          la red entera, simplificada, por clase de camino
      arterias: {<id>: {nombre, d, largo, km, ini, fin}}  UN trazo por arteria, del centro hacia afuera (para colas,
                                                          rastros y puntos que la recorren)
      riel:     d                                       las vías de tren del recuadro (o "")
      lugares:  {<id>: {nombre, x, y}} }

Las tarjetas y los videos NO llaman a OpenStreetMap (regla 4, cero dependencias externas): dibujan este archivo. La
licencia es ODbL: toda escena que lo use lleva «© colaboradores de OpenStreetMap» en su pie (`atribucion`).

Cada arteria se saca con el camino más corto dentro de los tramos que llevan su nombre o su `ref`, desde el punto más
cercano a `ini` (o al centro) hasta el más cercano a `fin` (o el más lejano del centro); los cabos sueltos a menos de
90 m (puentes y pasos a desnivel sin nombre) se unen.

Uso:
  python3 scripts/build_vias.py capital                 descarga (o usa la caché) y escribe design/vias/capital.json
  python3 scripts/build_vias.py capital --refrescar     vuelve a bajar de Overpass
  python3 scripts/build_vias.py capital --osm RUTA      usa un JSON de Overpass ya bajado (lo copia a la caché)
  python3 scripts/build_vias.py capital --check         no escribe: el archivo existe, coincide con la receta y cada
                                                        arteria y lugar cae dentro del lienzo
  python3 scripts/build_vias.py --lista                 las redes que hay en design/vias/
Salida: 0 ok · 1 fallo · 2 uso incorrecto
"""
import argparse
import datetime
import heapq
import json
import math
import os
import shutil
import sys
import urllib.parse
import urllib.request
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIAS = os.path.join(RAIZ, "design", "vias")
CACHE = os.path.join(RAIZ, "sesiones", "_descargas", "vias")
OVERPASS = "https://overpass-api.de/api/interpreter"
ATRIBUCION = "© colaboradores de OpenStreetMap"
# clase de camino → (ancho del trazo, opacidad) en un lienzo de 1080 de ancho; de la más fina a la más gruesa
CLASES = [("tertiary", 1.0, 0.2), ("secondary", 1.6, 0.3), ("primary", 2.4, 0.42), ("trunk", 3.4, 0.5), ("motorway", 3.4, 0.5)]
CABO_M = 90        # dos tramos de la misma arteria separados por menos de esto se unen
TOL_RED = 0.5      # tolerancia de simplificación (px del lienzo) de la red
TOL_ARTERIA = 1.0  # y de las arterias


def fallo(msg, code=1):
    print("FALLA " + msg, file=sys.stderr)
    sys.exit(code)


def leer_receta(vid):
    ruta = os.path.join(VIAS, vid + ".fuente.json")
    if not os.path.isfile(ruta):
        fallo("no existe la receta %s" % os.path.relpath(ruta, RAIZ), 2)
    r = json.load(open(ruta, encoding="utf-8"))
    for k in ("id", "nombre", "bbox", "lienzo", "centro", "arterias"):
        if k not in r:
            fallo("a la receta le falta `%s`" % k, 2)
    if r["id"] != vid:
        fallo("la receta dice id «%s», no «%s»" % (r["id"], vid), 2)
    return r


def bajar(receta, refrescar=False, osm=None):
    os.makedirs(CACHE, exist_ok=True)
    cache = os.path.join(CACHE, receta["id"] + ".osm.json")
    if osm:
        shutil.copyfile(osm, cache)
    if refrescar or not os.path.isfile(cache):
        s, w, n, e = receta["bbox"]
        caja = "(%s,%s,%s,%s)" % (s, w, n, e)
        q = ('[out:json][timeout:120];(way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]%s;'
             'way["railway"~"^(rail|disused|abandoned|light_rail)$"]%s;);out tags geom;') % (caja, caja)
        req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(),
                                     headers={"User-Agent": "mapa-estatico/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                cuerpo = resp.read()
        except Exception as ex:  # red caída, límite de Overpass
            fallo("no se pudo bajar de Overpass: %s" % ex)
        open(cache, "wb").write(cuerpo)
    try:
        return json.load(open(cache, encoding="utf-8"))["elements"]
    except Exception as ex:
        fallo("la caché %s no es un JSON de Overpass: %s" % (os.path.relpath(cache, RAIZ), ex))


def proyector(receta):
    s, w, n, e = receta["bbox"]
    ancho, alto = receta["lienzo"]
    return lambda lat, lon: ((lon - w) / (e - w) * ancho, (n - lat) / (n - s) * alto)


def simplificar(pts, tol):
    """Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    largo = math.hypot(dx, dy) or 1e-9
    imax, dmax = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / largo
        if d > dmax:
            imax, dmax = i, d
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return simplificar(pts[: imax + 1], tol)[:-1] + simplificar(pts[imax:], tol)


def trazo(pts):
    return "M" + " L".join("%g %g" % (round(x, 1), round(y, 1)) for x, y in pts)


def metros(a, b):
    return math.hypot((a[0] - b[0]) * 111000, (a[1] - b[1]) * 111000 * math.cos(math.radians(a[0])))


def arteria(els, xy, receta, a):
    """El camino más corto por los tramos con el nombre o el ref de la arteria, del centro hacia afuera."""
    ancho, alto = receta["lienzo"]
    nombres, refs = set(a.get("nombres") or [a["nombre"]]), set(a.get("refs") or [])
    centro = tuple(receta["centro"])
    g = defaultdict(dict)
    for e in els:
        t = e.get("tags", {})
        if "highway" not in t or not e.get("geometry"):
            continue
        if t.get("name") not in nombres and t.get("ref") not in refs:
            continue
        ps = [(round(p["lat"], 6), round(p["lon"], 6)) for p in e["geometry"]]
        for p, q in zip(ps, ps[1:]):
            # fuera del lienzo no hay arteria (un margen de 1 %)
            if not all(0.01 * ancho <= xy(*r)[0] <= 0.99 * ancho and 0.02 * alto <= xy(*r)[1] <= 0.97 * alto for r in (p, q)):
                continue
            g[p][q] = g[q][p] = metros(p, q)
    if not g:
        fallo("la arteria «%s» no tiene tramos en el recuadro (nombres %s, refs %s)" % (a["id"], sorted(nombres), sorted(refs)))
    nodos = list(g)
    for p in [n for n in nodos if len(g[n]) == 1]:
        for q in nodos:
            if p != q and q not in g[p]:
                d = metros(p, q)
                if d < CABO_M:
                    g[p][q] = g[q][p] = d * 3
    origen = min(nodos, key=lambda n: metros(n, tuple(a.get("ini") or centro)))
    dist, prev, cola = {origen: 0.0}, {}, [(0.0, origen)]
    while cola:
        d, u = heapq.heappop(cola)
        if d > dist.get(u, 1e18):
            continue
        for v, w in g[u].items():
            if d + w < dist.get(v, 1e18):
                dist[v], prev[v] = d + w, u
                heapq.heappush(cola, (d + w, v))
    if a.get("fin"):
        meta = min(dist, key=lambda n: metros(n, tuple(a["fin"])))
    else:
        meta = max(dist, key=lambda n: metros(n, centro))
    camino = [meta]
    while camino[-1] != origen:
        camino.append(prev[camino[-1]])
    camino.reverse()
    pts = simplificar([xy(*p) for p in camino], TOL_ARTERIA)
    largo = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:]))
    return {"nombre": a["nombre"], "d": trazo(pts), "largo": round(largo, 1), "km": round(dist[meta] / 1000, 1),
            "ini": [round(v, 1) for v in pts[0]], "fin": [round(v, 1) for v in pts[-1]]}


def construir(receta, els):
    xy = proyector(receta)
    ancho, alto = receta["lienzo"]
    k = ancho / 1080.0
    por_clase = defaultdict(list)
    rieles = []
    for e in els:
        t = e.get("tags", {})
        if not e.get("geometry"):
            continue
        pts = [xy(p["lat"], p["lon"]) for p in e["geometry"]]
        if t.get("highway") in {c for c, _, _ in CLASES}:
            por_clase[t["highway"]].append(trazo(simplificar(pts, TOL_RED)))
        elif "railway" in t:
            rieles.append(trazo(simplificar(pts, TOL_RED)))
    capas = [{"clase": c, "ancho": round(a * k, 2), "opacidad": o, "d": " ".join(por_clase[c])}
             for c, a, o in CLASES if por_clase.get(c)]
    lugares = {}
    for lg in receta.get("lugares", []):
        x, y = xy(*lg["pos"])
        lugares[lg["id"]] = {"nombre": lg["nombre"], "x": round(x, 1), "y": round(y, 1)}
    return {
        "id": receta["id"], "nombre": receta["nombre"], "viewBox": "0 0 %d %d" % (ancho, alto), "lienzo": [ancho, alto],
        "bbox": receta["bbox"], "atribucion": ATRIBUCION,
        "capas": capas,
        "arterias": {a["id"]: arteria(els, xy, receta, a) for a in receta["arterias"]},
        "riel": " ".join(rieles),
        "lugares": lugares,
    }


def revisar(receta, datos):
    """Fallas de un design/vias/<id>.json ya escrito frente a su receta."""
    fallas = []
    ancho, alto = receta["lienzo"]
    if datos.get("lienzo") != receta["lienzo"] or datos.get("bbox") != receta["bbox"]:
        fallas.append("el lienzo o el recuadro no coinciden con la receta: vuelve a construir")
    if datos.get("atribucion") != ATRIBUCION:
        fallas.append("falta la atribución «%s»" % ATRIBUCION)
    if not datos.get("capas"):
        fallas.append("la red no tiene capas")
    for a in receta["arterias"]:
        art = (datos.get("arterias") or {}).get(a["id"])
        if not art or not art.get("d") or art.get("largo", 0) < 20:
            fallas.append("falta la arteria «%s» (o su trazo mide menos de 20 px)" % a["id"])
            continue
        for punta in ("ini", "fin"):
            x, y = art[punta]
            if not (0 <= x <= ancho and 0 <= y <= alto):
                fallas.append("la arteria «%s» se sale del lienzo en su %s (%s, %s)" % (a["id"], punta, x, y))
    for lg in receta.get("lugares", []):
        p = (datos.get("lugares") or {}).get(lg["id"])
        if not p or not (0 <= p["x"] <= ancho and 0 <= p["y"] <= alto):
            fallas.append("el lugar «%s» falta o cae fuera del lienzo" % lg["id"])
    if "http" in json.dumps({k: v for k, v in datos.items() if k != "atribucion"}):
        fallas.append("el archivo lleva una URL: la escena no puede depender de la red")
    return fallas


def main():
    ap = argparse.ArgumentParser(description="Red vial real (OpenStreetMap) → design/vias/<id>.json", add_help=True,
                                 epilog="Salida: 0 ok · 1 fallo · 2 uso incorrecto")
    ap.add_argument("id", nargs="?", help="id de la red (design/vias/<id>.fuente.json)")
    ap.add_argument("--refrescar", action="store_true", help="vuelve a bajar de Overpass aunque haya caché")
    ap.add_argument("--osm", help="JSON de Overpass ya bajado (se copia a la caché)")
    ap.add_argument("--check", action="store_true", help="no escribe: revisa design/vias/<id>.json frente a su receta")
    ap.add_argument("--lista", action="store_true", help="las redes de design/vias/")
    args = ap.parse_args()
    if args.lista:
        for f in sorted(os.listdir(VIAS)) if os.path.isdir(VIAS) else []:
            if f.endswith(".json") and not f.endswith(".fuente.json"):
                d = json.load(open(os.path.join(VIAS, f), encoding="utf-8"))
                print("%s · %s · arterias: %s · lugares: %s" % (d["id"], d["nombre"], ", ".join(d["arterias"]), ", ".join(d["lugares"])))
        return 0
    if not args.id:
        ap.print_usage(sys.stderr)
        return 2
    receta = leer_receta(args.id)
    destino = os.path.join(VIAS, args.id + ".json")
    if args.check:
        if not os.path.isfile(destino):
            fallo("no existe %s: corre python3 scripts/build_vias.py %s" % (os.path.relpath(destino, RAIZ), args.id))
        fallas = revisar(receta, json.load(open(destino, encoding="utf-8")))
        for f in fallas:
            print("FALLA " + f, file=sys.stderr)
        if not fallas:
            print("ok %s" % os.path.relpath(destino, RAIZ))
        return 1 if fallas else 0
    datos = construir(receta, bajar(receta, args.refrescar, args.osm))
    datos["generado"] = datetime.date.today().isoformat()
    fallas = revisar(receta, datos)
    for f in fallas:
        print("FALLA " + f, file=sys.stderr)
    if fallas:
        return 1
    json.dump(datos, open(destino, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("%s · %d KB" % (os.path.relpath(destino, RAIZ), os.path.getsize(destino) // 1024))
    for aid, a in datos["arterias"].items():
        print("  %-16s %5.1f km · %4.0f px · de %s a %s" % (aid, a["km"], a["largo"], a["ini"], a["fin"]))
    for lid, lg in datos["lugares"].items():
        print("  lugar %-12s %s (%s, %s)" % (lid, lg["nombre"], lg["x"], lg["y"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
