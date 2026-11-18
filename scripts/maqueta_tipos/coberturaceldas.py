"""Pieza «coberturaceldas»: una serie anual de cobertura por celdas (p. ej. la pérdida de bosque de Hansen agregada a una
malla de celdas) dentro del contorno de un área (GeoJSON).

`datos`: un JSON {celda_grados, celdas: [{lon, lat, area_ha, bosque2000_ha, perdida_ha: {"AAAA": ha}}]} (lon, lat = el
CENTRO de la celda). `contorno`: un GeoJSON (Feature, FeatureCollection o geometría; Polygon o MultiPolygon). Las rutas
van desde la raíz del proyecto (sesiones/<slug>/geodatos/…) o absolutas: el resolver no conoce la carpeta del
maqueta.json. «_ejemplo» en los dos arma una malla y un contorno ILUSTRATIVOS (solo para la ficha del catálogo: avisa).

Resuelta (km): {celdas: [[x, y, f0, [[k, frac], …]]], anios: [AAAA…], medio: [hx, hy], anio_base, anio, anio_fin,
corre_desde, corre_hasta, tono, apagado, destello, grosor, contorno: [[x, y, s, salto]]}. f0 = bosque del año base / área;
frac = la pérdida de ese año / área (la suma nunca pasa de f0: lo que sobra se recorta y se avisa).
Publica el lugar «centro» (el centro de las celdas)."""
import json
import math
import os

TOPE_CELDAS = 30000
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _leer(ruta, que, M3, cual):
    for r in ([ruta] if os.path.isabs(ruta) else [os.path.join(RAIZ, ruta), os.path.abspath(ruta)]):
        if os.path.isfile(r):
            try:
                with open(r, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError) as e:
                raise M3.Falla("M3D2", "%s: no se pudo leer `%s` (%s): %s" % (que, cual, ruta, e))
    raise M3.Falla("M3D2", "%s: `%s` no existe: %s (ruta desde la raíz del proyecto, p. ej. sesiones/<slug>/geodatos/…)" % (que, cual, ruta))


def _h(i, k):
    v = math.sin(i * 127.1 + k * 311.7) * 43758.5453
    return v - math.floor(v)


def _ejemplo():
    """Una malla ILUSTRATIVA en Petén (no son datos): 12 × 9 celdas de 0.04°, con un frente de pérdida desde el suroeste."""
    g, celdas = 0.04, []
    for j in range(9):
        for i in range(12):
            n = j * 12 + i
            lon, lat = -90.62 + (i + 0.5) * g, 17.30 + (j + 0.5) * g
            area = 1900.0
            b0 = area * (0.55 + 0.43 * _h(n, 1))
            fr = max(0.0, 1.0 - (i * 0.11 + j * 0.13))            # el frente: más cerca del suroeste, más pérdida
            per, resto = {}, b0
            for a in range(2001, 2024):
                p = b0 * fr * 0.09 * _h(n, a) * (0.4 + (a - 2000) / 23.0)
                if p > 1 and resto > p:
                    per[str(a)] = round(p, 1); resto -= p
            celdas.append({"lon": lon, "lat": lat, "area_ha": area, "bosque2000_ha": round(b0, 1), "perdida_ha": per})
    anillo = [[-90.64, 17.29], [-90.40, 17.27], [-90.15, 17.30], [-90.13, 17.47], [-90.15, 17.67],
              [-90.38, 17.68], [-90.63, 17.65], [-90.645, 17.47], [-90.64, 17.29]]
    return {"celda_grados": g, "celdas": celdas}, {"type": "Polygon", "coordinates": [anillo]}


def _anillos(gj):
    t = (gj or {}).get("type")
    if t == "FeatureCollection":
        return [a for f in gj.get("features") or [] for a in _anillos(f)]
    if t == "Feature":
        return _anillos(gj.get("geometry"))
    if t == "Polygon":
        return [r for r in gj.get("coordinates") or []]
    if t == "MultiPolygon":
        return [r for pol in gj.get("coordinates") or [] for r in pol]
    if t == "GeometryCollection":
        return [a for g in gj.get("geometries") or [] for a in _anillos(g)]
    return []


def resolver(p, X, que):
    M3, S = X.m3, X.S
    if getattr(S, "escala", "pais") != "pais":
        raise M3.Falla("M3D2", "%s: coberturaceldas es de escala pais (lon/lat sobre el relieve)" % que)
    if p["datos"] == "_ejemplo" or p["contorno"] == "_ejemplo":
        D, G = _ejemplo()
        X.avisos.append("%s: datos «_ejemplo» = malla ILUSTRATIVA del catálogo; un video usa sus datos verificados" % que)
    if p["datos"] != "_ejemplo":
        D = _leer(p["datos"], que, M3, "datos")
    if p["contorno"] != "_ejemplo":
        G = _leer(p["contorno"], que, M3, "contorno")
    g = D.get("celda_grados")
    lista = D.get("celdas")
    if not isinstance(g, (int, float)) or g <= 0 or not isinstance(lista, list) or not lista:
        raise M3.Falla("M3D2", "%s: `datos` necesita `celda_grados` (> 0) y `celdas` [{lon, lat, area_ha, bosque2000_ha, perdida_ha}]" % que)
    if len(lista) > TOPE_CELDAS:
        raise M3.Falla("M3D2", "%s: %d celdas (tope %d): agrega a celdas más grandes" % (que, len(lista), TOPE_CELDAS))
    base = int(p.get("anio_base", 2000))
    anio = int(p.get("anio", base))
    fin = p.get("anio_fin")
    cd, ch = p.get("corre_desde"), p.get("corre_hasta")
    if fin is not None:
        fin = int(fin)
        if fin <= anio:
            raise M3.Falla("M3D2", "%s: `anio_fin` (%d) tiene que ser mayor que `anio` (%d)" % (que, fin, anio))
        if cd is None or ch is None or ch <= cd:
            raise M3.Falla("M3D2", "%s: con `anio_fin`, `corre_desde` < `corre_hasta` (segundos en que el año corre)" % que)
    anios = sorted({int(a) for c in lista for a in (c.get("perdida_ha") or {}) if str(a).isdigit() and int(a) > base})
    kx = {a: k for k, a in enumerate(anios)}
    celdas, recortes, sx, sy, fuera = [], 0, 0.0, 0.0, 0
    for c in lista:
        try:
            x, y = S.xy(float(c["lon"]), float(c["lat"]))
            area = float(c["area_ha"]); b0 = float(c.get("bosque2000_ha", 0) or 0)
        except (KeyError, TypeError, ValueError):
            raise M3.Falla("M3D2", "%s: una celda sin lon, lat o area_ha: %r" % (que, c))
        if not S.dentro(x, y):
            fuera += 1
            continue
        if area <= 0:
            continue
        f0 = min(1.0, max(0.0, b0 / area)); resto, per = f0, []
        for a, ha in sorted((c.get("perdida_ha") or {}).items()):
            if not str(a).isdigit() or int(a) <= base or not ha:
                continue
            fr = float(ha) / area
            if fr > resto + 1e-6:
                recortes += 1; fr = resto
            if fr > 0:
                per.append([kx[int(a)], round(fr, 5)]); resto -= fr
        celdas.append([round(x, 3), round(y, 3), round(f0, 4), per])
        sx += x; sy += y
    if not celdas:
        raise M3.Falla("M3D2", "%s: ninguna celda cae dentro de la caja del set %s" % (que, S.id))
    if fuera:
        X.avisos.append("%s: %d celdas fuera de la caja del set (no se dibujan)" % (que, fuera))
    if recortes:
        X.avisos.append("%s: %d pérdidas pasaban del bosque que quedaba en su celda (recortadas)" % (que, recortes))
    cad, s = [], 0.0
    for an in _anillos(G):
        pts = [S.xy(float(q[0]), float(q[1])) for q in an if len(q) >= 2]
        if len(pts) < 3:
            continue
        for i, (x, y) in enumerate(pts):
            if cad and i:
                s += math.hypot(x - cad[-1][0], y - cad[-1][1])
            cad.append([x, y, s, 1 if i == len(pts) - 1 else 0])
        s += 1.0
    if not cad:
        raise M3.Falla("M3D2", "%s: `contorno` no trae ningún Polygon ni MultiPolygon" % que)
    cad = [[round(q[0], 3), round(q[1], 3), round(q[2], 3), q[3]] for q in M3.simplificar(cad, 0.12)]
    hx, hy = g * S.P["km_lon"] / 2, g * S.P["km_lat"] / 2
    n = len(celdas)
    return {"celdas": celdas, "anios": anios, "medio": [round(hx, 4), round(hy, 4)], "anio_base": base, "anio": anio,
            "anio_fin": fin, "corre_desde": cd, "corre_hasta": ch, "tono": p.get("tono", "acento"),
            "apagado": p.get("apagado", 0.15), "destello": p.get("destello", True), "grosor": p.get("contorno_grosor", 1.5),
            "contorno": cad,
            "_lugares": {"centro": {"x": round(sx / n, 3), "y": round(sy / n, 3), "nombre": "Celdas · centro", "peso": 0.6}}}


def tramos(pz):
    return [[(q[0], q[1], bool(q[3])) for q in pz["contorno"]]]


def centro(pz, G):
    c = pz["celdas"]
    return (sum(q[0] for q in c) / len(c), sum(q[1] for q in c) / len(c))
