#!/usr/bin/env python3
"""Arma un «set 3D»: los geodatos de un territorio para la maqueta que vuela (/video-3d).

uso:
  python3 scripts/build_set3d.py guatemala            baja (con caché) y escribe design/sets3d/guatemala/
  python3 scripts/build_set3d.py guatemala --check    revisa el set ya escrito (sin red); 0 ok · 1 falla
  python3 scripts/build_set3d.py guatemala --capa lugares   rehace solo una capa (relieve|fallas|frontera|lugares)

Capas (cada una con su fuente, licencia y fecha en fuente.json):
  relieve.png + relieve.json   malla de alturas (Mapzen Terrain Tiles, formato terrarium; R = byte alto, G = byte bajo
                               de «metros + desfase»; PNG sin perfil de color, filtro «Up»)
  fallas.json                  trazos de GEM Global Active Faults dentro de la caja (CC BY-SA 4.0)
  frontera.json                contorno del país y bordes de los vecinos dentro de la caja (Natural Earth 1:50m, design/mapas/paises-50m.json)
  lugares.json                 cabeceras, ciudades y pueblos de OpenStreetMap (Overpass, ODbL) con un peso para la luz
  fuente.json                  fuente, licencia, fecha de descarga y texto de atribución de cada capa

Las descargas quedan en sesiones/_descargas/sets3d/<set>/ (caché: no se vuelve a bajar lo que ya está). El render del
video nunca llama a la red: solo lee design/sets3d/<set>/. Python stdlib; decodifica los PNG de los mosaicos con ffmpeg.
Salida: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse, datetime, json, math, os, re, struct, subprocess, sys, time, unicodedata, urllib.parse, urllib.request, zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTE = "set3d-build/1.0 (stdlib urllib)"

SETS = {
    "guatemala": {
        "nombre": "Guatemala",
        # la caja es mucho mayor que el país: con Guatemala entera en cuadro (9:16 y 4:5) el mundo llega a los bordes
        # del lienzo (México, Belice, Honduras, El Salvador y el fondo de los dos mares), sin banda vacía
        "caja": {"lon_min": -95.0, "lon_max": -85.4, "lat_min": 11.4, "lat_max": 20.4},
        "ancho": 1440, "alto": 1350,         # celdas: 1/150 de grado ≈ 0.72 km
        "zoom": 8,                           # mosaicos terrarium: ≈ 182 px por grado
        "pais_id": "320", "pais_iso": "GT",
        # las 22 cabeceras: departamento → nombre del lugar en OpenStreetMap (y su id en el set)
        "cabeceras": {
            "Guatemala": ("Ciudad de Guatemala", "guatemala"), "El Progreso": ("Guastatoya", "guastatoya"),
            "Sacatepéquez": ("Antigua Guatemala", "antigua-guatemala"), "Chimaltenango": ("Chimaltenango", "chimaltenango"),
            "Escuintla": ("Escuintla", "escuintla"), "Santa Rosa": ("Cuilapa", "cuilapa"), "Sololá": ("Sololá", "solola"),
            "Totonicapán": ("Totonicapán", "totonicapan"), "Quetzaltenango": ("Quetzaltenango", "quetzaltenango"),
            "Suchitepéquez": ("Mazatenango", "mazatenango"), "Retalhuleu": ("Retalhuleu", "retalhuleu"),
            "San Marcos": ("San Marcos", "san-marcos"), "Huehuetenango": ("Huehuetenango", "huehuetenango"),
            "Quiché": ("Santa Cruz del Quiché", "santa-cruz-del-quiche"), "Baja Verapaz": ("Salamá", "salama"),
            "Alta Verapaz": ("Cobán", "coban"), "Petén": ("Flores", "flores"), "Izabal": ("Puerto Barrios", "puerto-barrios"),
            "Zacapa": ("Zacapa", "zacapa"), "Chiquimula": ("Chiquimula", "chiquimula"), "Jalapa": ("Jalapa", "jalapa"),
            "Jutiapa": ("Jutiapa", "jutiapa"),
        },
        # pueblos que deben existir aunque OSM los tenga como aldea (los nombra el piloto del terremoto de 1976)
        "obligatorios": ["Los Amates", "Gualán", "Quiriguá", "Puerto Barrios", "Mixco", "Tecpán Guatemala",
                         "San Martín Jilotepeque", "Chimaltenango", "Guastatoya", "Zacapa", "El Progreso", "Joyabaj",
                         "Patzicía", "San Pedro Sacatepéquez", "Antigua Guatemala"],
        "alias": {"tecpan-guatemala": "tecpan", "ciudad-de-guatemala": "guatemala"},
    },
}
DESFASE_M = 8000      # la altura se guarda como metros + DESFASE (el fondo del mar llega a −8000: la fosa se ve)
URL_RELIEVE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
URL_FALLAS = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults_harmonized.geojson"
URLS_OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def slug(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def bajar(url, destino, datos=None, intentos=3):
    """Descarga con caché: si `destino` ya existe no toca la red."""
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return destino
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, data=datos, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(req, timeout=180) as r:
                cuerpo = r.read()
            with open(destino + ".tmp", "wb") as f:
                f.write(cuerpo)
            os.replace(destino + ".tmp", destino)
            return destino
        except Exception as e:  # red: se reintenta
            ultimo = e
            time.sleep(2 + 3 * i)
    raise RuntimeError("no se pudo bajar %s: %s" % (url, ultimo))


# ---------- PNG (escritura y lectura propias: RGB de 8 bits, filtro Up) ----------
def png_escribir(ruta, ancho, alto, filas_rgb):
    """filas_rgb: lista de `alto` bytes de 3·ancho. Filtro 2 (Up) en todas las filas; sin perfil de color."""
    def trozo(tipo, datos):
        c = struct.pack(">I", len(datos)) + tipo + datos
        return c + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    crudo = bytearray()
    previa = bytes(3 * ancho)
    for fila in filas_rgb:
        crudo.append(2)
        crudo += bytes((a - b) & 255 for a, b in zip(fila, previa))
        previa = fila
    with open(ruta, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
                + trozo(b"IDAT", zlib.compress(bytes(crudo), 9)) + trozo(b"IEND", b""))


def png_leer(ruta):
    """→ (ancho, alto, filas) de un PNG escrito por png_escribir (RGB 8 bits, filtros 0 o 2)."""
    with open(ruta, "rb") as f:
        d = f.read()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", "no es PNG"
    p, idat, ancho, alto = 8, b"", 0, 0
    while p < len(d):
        n, tipo = struct.unpack(">I", d[p:p + 4])[0], d[p + 4:p + 8]
        if tipo == b"IHDR":
            ancho, alto, bits, color = struct.unpack(">IIBB", d[p + 8:p + 18])
            assert bits == 8 and color == 2, "PNG: se espera RGB de 8 bits"
        elif tipo == b"IDAT":
            idat += d[p + 8:p + 8 + n]
        p += 12 + n
    crudo = zlib.decompress(idat)
    paso = 3 * ancho + 1
    filas, previa = [], 0
    m7 = int.from_bytes(b"\x7f" * (3 * ancho), "big")
    m8 = int.from_bytes(b"\x80" * (3 * ancho), "big")
    for y in range(alto):
        filtro = crudo[y * paso]
        v = int.from_bytes(crudo[y * paso + 1:(y + 1) * paso], "big")
        if filtro == 2:   # suma byte a byte sin acarreo entre bytes
            v = ((v & m7) + (previa & m7)) ^ ((v ^ previa) & m8)
        elif filtro != 0:
            raise AssertionError("PNG: filtro %d no soportado" % filtro)
        previa = v
        filas.append(v.to_bytes(3 * ancho, "big"))
    return ancho, alto, filas


def decodificar_png_rgb(ruta):
    """Un PNG cualquiera → (ancho, alto, bytes RGB) con ffmpeg."""
    info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", ruta], capture_output=True, text=True, check=True).stdout.strip().split(",")
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, check=True).stdout
    w, h = int(info[0]), int(info[1])
    assert len(crudo) == w * h * 3, "ffmpeg devolvió %d bytes para %s" % (len(crudo), ruta)
    return w, h, crudo


# ---------- relieve ----------
def mosaico_xy(lon, lat, z):
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def capa_relieve(sid, S, cache, salida):
    c, z = S["caja"], S["zoom"]
    x0, y0 = mosaico_xy(c["lon_min"], c["lat_max"], z)
    x1, y1 = mosaico_xy(c["lon_max"], c["lat_min"], z)
    tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
    print("relieve: %d mosaicos z%d (x %d–%d, y %d–%d)" % ((tx1 - tx0 + 1) * (ty1 - ty0 + 1), z, tx0, tx1, ty0, ty1))
    mos = {}
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            ruta = bajar(URL_RELIEVE.format(z=z, x=tx, y=ty), os.path.join(cache, "terrarium", "%d_%d_%d.png" % (z, tx, ty)))
            w, h, rgb = decodificar_png_rgb(ruta)
            assert (w, h) == (256, 256)
            mos[(tx, ty)] = rgb

    def altura_px(px, py):   # píxel global (entero) → metros
        tx, ty = px >> 8, py >> 8
        tx, ty = min(max(tx, tx0), tx1), min(max(ty, ty0), ty1)
        i = (((py - (ty << 8)) & 255) * 256 + ((px - (tx << 8)) & 255)) * 3
        m = mos[(tx, ty)]
        return m[i] * 256 + m[i + 1] + m[i + 2] / 256.0 - 32768.0

    W, H = S["ancho"], S["alto"]
    filas, hmin, hmax = [], 1e9, -1e9
    alturas = []
    for j in range(H):   # fila 0 = norte; la celda (i, j) es el centro de su casilla
        lat = c["lat_max"] - (j + 0.5) / H * (c["lat_max"] - c["lat_min"])
        fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * (2 ** z) * 256 - 0.5
        py = int(math.floor(fy)); wy = fy - py
        fila = bytearray(3 * W)
        for i in range(W):
            lon = c["lon_min"] + (i + 0.5) / W * (c["lon_max"] - c["lon_min"])
            fx = (lon + 180.0) / 360.0 * (2 ** z) * 256 - 0.5
            px = int(math.floor(fx)); wx = fx - px
            a = (altura_px(px, py) * (1 - wx) + altura_px(px + 1, py) * wx) * (1 - wy) + \
                (altura_px(px, py + 1) * (1 - wx) + altura_px(px + 1, py + 1) * wx) * wy
            v = int(round(min(max(a, -DESFASE_M), 60000) + DESFASE_M))
            fila[3 * i], fila[3 * i + 1] = v >> 8, v & 255
            alturas.append(v - DESFASE_M)
            hmin, hmax = min(hmin, v - DESFASE_M), max(hmax, v - DESFASE_M)
        filas.append(bytes(fila))
    png_escribir(os.path.join(salida, "relieve.png"), W, H, filas)
    lon0, lat0 = (c["lon_min"] + c["lon_max"]) / 2, (c["lat_min"] + c["lat_max"]) / 2
    # muestras para comprobar en el navegador que la imagen se leyó sin conversión de color
    muestras = [[i, j, alturas[j * W + i]] for (i, j) in ((W // 7, H // 5), (W // 2, H // 2), (W * 3 // 4, H // 3), (W // 3, H * 4 // 5), (W - 5, 4))]
    meta = {
        "set": sid, "archivo": "relieve.png", "ancho": W, "alto": H, "caja": c, "desfase_m": DESFASE_M,
        "codificacion": "altura_m = R*256 + G - desfase_m; fila 0 = norte; la celda es el centro de su casilla",
        "min_m": hmin, "max_m": hmax,
        # proyección local de la maqueta (km): x = (lon - lon0) * km_lon (este), y = (lat - lat0) * km_lat (norte)
        "proyeccion": {"lon0": lon0, "lat0": lat0, "km_lon": round(111.320 * math.cos(math.radians(lat0)), 4), "km_lat": 110.574},
        "muestras": muestras,
    }
    with open(os.path.join(salida, "relieve.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("relieve: %d×%d celdas, de %d a %d m, %d KB" % (W, H, hmin, hmax, os.path.getsize(os.path.join(salida, "relieve.png")) // 1024))
    return {"fuente": "Mapzen Terrain Tiles (AWS Open Data), formato terrarium, zoom %d" % z,
            "url": "https://registry.opendata.aws/terrain-tiles/",
            "licencia": "Datos abiertos; atribución según la fuente de cada mosaico (SRTM, GMTED2010, ETOPO1 y otros)",
            "atribucion": "Relieve: Mapzen Terrain Tiles"}


# ---------- fallas ----------
def capa_fallas(sid, S, cache, salida):
    c = S["caja"]
    ruta = bajar(URL_FALLAS, os.path.join(os.path.dirname(cache), "_comun", "gem_active_faults_harmonized.geojson"))
    with open(ruta, encoding="utf-8") as f:
        G = json.load(f)
    dentro = lambda p: c["lon_min"] <= p[0] <= c["lon_max"] and c["lat_min"] <= p[1] <= c["lat_max"]
    trazos, sin_nombre = [], 0
    for ft in G["features"]:
        g, p = ft.get("geometry") or {}, ft.get("properties") or {}
        lineas = [g["coordinates"]] if g.get("type") == "LineString" else g.get("coordinates", []) if g.get("type") == "MultiLineString" else []
        for ln in lineas:
            # se recorta a la caja: se conservan los tramos seguidos que caen dentro
            tramo = []
            for pt in ln + [None]:
                if pt is not None and dentro(pt):
                    tramo.append([round(pt[0], 5), round(pt[1], 5)])
                else:
                    if len(tramo) >= 2:
                        nombre = (p.get("name") or "").strip()
                        if not nombre:
                            sin_nombre += 1
                        trazos.append({"nombre": nombre, "tipo": (p.get("slip_type") or "").strip(),
                                       "catalogo": p.get("catalog_name") or "", "id_gem": p.get("catalog_id") or p.get("ogc_fid"),
                                       "puntos": tramo})
                    tramo = []
    trazos.sort(key=lambda t: (t["nombre"] or "~", t["puntos"][0][0]))
    nombres = {}
    for t in trazos:
        if t["nombre"]:
            n = nombres.setdefault(t["nombre"], {"trazos": 0, "km": 0.0, "tipo": t["tipo"]})
            n["trazos"] += 1
            n["km"] += sum(dist_km(a, b) for a, b in zip(t["puntos"], t["puntos"][1:]))
    for n in nombres.values():
        n["km"] = round(n["km"], 1)
    with open(os.path.join(salida, "fallas.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "nombres": nombres, "trazos": trazos}, f, ensure_ascii=False, separators=(",", ":"))
    print("fallas: %d trazos (%d sin nombre), %d nombres: %s" % (len(trazos), sin_nombre, len(nombres), ", ".join(sorted(nombres))))
    return {"fuente": "GEM Global Active Faults Database (Styron y Pagani, 2020), capa armonizada", "url": URL_FALLAS,
            "licencia": "CC BY-SA 4.0", "atribucion": "Fallas: GEM (CC BY-SA 4.0)"}


def dist_km(a, b):
    la = math.radians((a[1] + b[1]) / 2)
    return math.hypot((b[0] - a[0]) * 111.320 * math.cos(la), (b[1] - a[1]) * 110.574)


# ---------- frontera ----------
NOMBRES_PAIS = {"484": "México", "084": "Belice", "340": "Honduras", "222": "El Salvador", "558": "Nicaragua",
                "188": "Costa Rica", "320": "Guatemala"}


def capa_vecinos(T, g_pais, caja, arco):
    """Los bordes de los países que caen en la caja, sin los del país del set (ya están en `anillos`): cada arco de
    Natural Earth una sola vez (el que comparten México y Belice no se dibuja dos veces), recortado a la caja en tramos
    seguidos. Incluye la costa de los vecinos: sin ella, un borde terrestre suelto no se entiende."""
    def idx(i):
        return i if i >= 0 else ~i

    def arcos_de(g):
        pols = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        return {idx(i) for pol in pols for r in pol for i in r}

    dentro = lambda p: caja["lon_min"] <= p[0] <= caja["lon_max"] and caja["lat_min"] <= p[1] <= caja["lat_max"]
    propios, vistos, lineas, paises = arcos_de(g_pais), set(), [], []
    for g in T["objects"]["countries"]["geometries"]:
        if g is g_pais or g.get("type") not in ("Polygon", "MultiPolygon"):
            continue
        n = 0
        for i in sorted(arcos_de(g) - propios - vistos):
            vistos.add(i)
            tramo = []
            for p in arco(i):
                if dentro(p):
                    tramo.append(p)
                else:
                    if len(tramo) >= 2:
                        lineas.append(tramo); n += 1
                    tramo = []
            if len(tramo) >= 2:
                lineas.append(tramo); n += 1
        if n:
            paises.append(NOMBRES_PAIS.get(str(g.get("id")), g.get("properties", {}).get("name")))
    return {"paises": paises, "lineas": lineas}


def capa_frontera(sid, S, cache, salida):
    with open(os.path.join(RAIZ, "design", "mapas", "paises-50m.json"), encoding="utf-8") as f:
        T = json.load(f)
    sx, sy = T["transform"]["scale"]; ox, oy = T["transform"]["translate"]

    def arco(i):
        pts, x, y = [], 0, 0
        for dx, dy in T["arcs"][i if i >= 0 else ~i]:
            x += dx; y += dy
            pts.append([round(x * sx + ox, 5), round(y * sy + oy, 5)])
        return pts if i >= 0 else pts[::-1]

    def anillo(indices):
        pts = []
        for i in indices:
            a = arco(i)
            pts += a if not pts else a[1:]
        return pts

    geos = [g for g in T["objects"]["countries"]["geometries"] if str(g.get("id")) == S["pais_id"]]
    assert geos, "país %s no está en paises-50m.json" % S["pais_id"]
    g = geos[0]
    poligonos = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
    anillos = [anillo(r) for pol in poligonos for r in pol]
    anillos.sort(key=len, reverse=True)
    vecinos = capa_vecinos(T, g, S["caja"], arco)
    with open(os.path.join(salida, "frontera.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "pais": g.get("properties", {}).get("name"), "anillos": anillos, "vecinos": vecinos},
                  f, ensure_ascii=False, separators=(",", ":"))
    print("frontera: %d anillo(s), %d puntos · vecinos: %s (%d líneas, %d puntos)"
          % (len(anillos), sum(map(len, anillos)), ", ".join(vecinos["paises"]),
             len(vecinos["lineas"]), sum(map(len, vecinos["lineas"]))))
    return {"fuente": "Natural Earth 1:50m (design/mapas/paises-50m.json)", "url": "https://www.naturalearthdata.com/",
            "licencia": "Dominio público", "atribucion": "Frontera: Natural Earth"}


# ---------- lugares ----------
def capa_lugares(sid, S, cache, salida):
    c = S["caja"]
    consulta = ('[out:json][timeout:120];area["ISO3166-1"="%s"][admin_level=2]->.a;'
                '(node(area.a)[place~"^(city|town)$"];node(area.a)[place~"^(village|suburb)$"][name~"^(%s)$"];);out body;'
                % (S["pais_iso"], "|".join(sorted(set(S["obligatorios"])))))
    destino = os.path.join(cache, "overpass_lugares.json")
    if not os.path.exists(destino):
        ultimo = None
        for url in URLS_OVERPASS:
            try:
                bajar(url, destino, datos=urllib.parse.urlencode({"data": consulta}).encode(), intentos=2)
                break
            except RuntimeError as e:
                ultimo = e
        else:
            raise ultimo
    with open(destino, encoding="utf-8") as f:
        R = json.load(f)
    orden = {"city": 0, "town": 1, "suburb": 2, "village": 3}
    nodos = []
    for e in R["elements"]:
        t = e.get("tags", {})
        nombre = t.get("name:es") or t.get("name")
        if not nombre or not (c["lon_min"] <= e["lon"] <= c["lon_max"] and c["lat_min"] <= e["lat"] <= c["lat_max"]):
            continue
        try:
            pob = int(re.sub(r"[^0-9]", "", t.get("population", "")) or 0)
        except ValueError:
            pob = 0
        nodos.append({"nombre": nombre, "lon": round(e["lon"], 5), "lat": round(e["lat"], 5), "clase": t.get("place"), "poblacion": pob,
                      "capital": t.get("capital") or "", "osm": e["id"]})
    cab = {slug(n): (dep, i) for dep, (n, i) in S["cabeceras"].items()}
    nodos.sort(key=lambda n: (orden.get(n["clase"], 9), -n["poblacion"], n["nombre"]))
    lugares, usados = {}, {}
    for n in nodos:
        s = slug(n["nombre"])
        dep = None
        if s in cab and cab[s][1] not in lugares:
            dep, s = cab[s][0], cab[s][1]
        else:
            s = S["alias"].get(s, s)
            if s in lugares:
                usados[s] = usados.get(s, 1) + 1
                s = "%s-%d" % (s, usados[s])
        # peso para la luz (0.2–1): por población si OSM la trae, si no por clase
        base = {"city": 0.62, "town": 0.36, "suburb": 0.3, "village": 0.22}.get(n["clase"], 0.2)
        if n["poblacion"] > 0:
            base = max(base, min(1.0, 0.16 + 0.14 * math.log10(max(n["poblacion"], 10)) - 0.2))
        if dep:
            base = max(base, 0.55)
        if s == "guatemala":
            base = 1.0
        lugares[s] = {"nombre": n["nombre"], "lon": n["lon"], "lat": n["lat"], "clase": n["clase"], "peso": round(base, 2)}
        if n["poblacion"]:
            lugares[s]["poblacion"] = n["poblacion"]
        if dep:
            lugares[s]["cabecera_de"] = dep
    with open(os.path.join(salida, "lugares.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "lugares": lugares}, f, ensure_ascii=False, indent=0, separators=(",", ":"))
    print("lugares: %d (%d cabeceras)" % (len(lugares), sum(1 for l in lugares.values() if l.get("cabecera_de"))))
    return {"fuente": "OpenStreetMap (Overpass API): nodos place=city|town del país y los pueblos del piloto",
            "url": "https://www.openstreetmap.org/copyright", "licencia": "ODbL 1.0",
            "atribucion": "Lugares: © OpenStreetMap"}


CAPAS = {"relieve": capa_relieve, "fallas": capa_fallas, "frontera": capa_frontera, "lugares": capa_lugares}


def construir(sid, solo=None):
    S = SETS[sid]
    cache = os.path.join(RAIZ, "sesiones", "_descargas", "sets3d", sid)
    salida = os.path.join(RAIZ, "design", "sets3d", sid)
    os.makedirs(cache, exist_ok=True); os.makedirs(salida, exist_ok=True)
    ruta_f = os.path.join(salida, "fuente.json")
    fuente = {"set": sid, "nombre": S["nombre"], "caja": S["caja"], "capas": {}}
    if os.path.exists(ruta_f):
        with open(ruta_f, encoding="utf-8") as f:
            fuente = json.load(f)
    hoy = datetime.date.today().isoformat()
    for capa, fn in CAPAS.items():
        if solo and capa != solo:
            continue
        info = fn(sid, S, cache, salida)
        info["descarga"] = hoy
        fuente["capas"][capa] = info
    orden = [k for k in ("relieve", "fallas", "frontera", "lugares") if k in fuente["capas"]]
    fuente["pie"] = " · ".join(fuente["capas"][k]["atribucion"] for k in orden)
    # lo mínimo que el pie del video debe nombrar (M3D7): una palabra clave por capa con licencia de atribución
    fuente["pie_claves"] = {"relieve": "Mapzen", "fallas": "GEM", "lugares": "OpenStreetMap"}
    with open(ruta_f, "w", encoding="utf-8") as f:
        json.dump(fuente, f, ensure_ascii=False, indent=1)
    print("fuente.json: " + fuente["pie"])


def revisar(sid):
    S = SETS[sid]
    d = os.path.join(RAIZ, "design", "sets3d", sid)
    fallas = []
    def falla(m):
        fallas.append(m); print("  FALLA " + m)
    for f in ("relieve.png", "relieve.json", "fallas.json", "frontera.json", "lugares.json", "fuente.json"):
        if not os.path.exists(os.path.join(d, f)):
            falla("falta %s (corre: python3 scripts/build_set3d.py %s)" % (f, sid))
    if fallas:
        return 1
    carga = lambda f: json.load(open(os.path.join(d, f), encoding="utf-8"))
    M = carga("relieve.json")
    w, h, filas = png_leer(os.path.join(d, "relieve.png"))
    if (w, h) != (M["ancho"], M["alto"]):
        falla("relieve.png mide %d×%d y relieve.json dice %d×%d" % (w, h, M["ancho"], M["alto"]))
    for i, j, v in M["muestras"]:
        got = filas[j][3 * i] * 256 + filas[j][3 * i + 1] - M["desfase_m"]
        if got != v:
            falla("relieve: la muestra (%d, %d) da %d y debía dar %d" % (i, j, got, v))
    peso = os.path.getsize(os.path.join(d, "relieve.png"))
    if peso > 2.6e6:
        falla("relieve.png pesa %.1f MB (tope ≈ 2.5 MB)" % (peso / 1e6))
    if not (3500 <= M["max_m"] <= 4400):
        falla("relieve: la altura máxima es %d m (el Tajumulco mide 4 220 m)" % M["max_m"])
    F = carga("fallas.json")
    for n in ("Motagua Fault", "Western Motagua Fault", "Mixco Fault", "Polochic Fault"):
        if n not in F["nombres"]:
            falla("fallas: falta «%s»" % n)
    B = carga("frontera.json")
    if not B["anillos"] or len(B["anillos"][0]) < 50:
        falla("frontera: el contorno tiene muy pocos puntos")
    L = carga("lugares.json")["lugares"]
    for dep, (n, i) in S["cabeceras"].items():
        if i not in L or L[i].get("cabecera_de") != dep:
            falla("lugares: falta la cabecera de %s (%s, id «%s»)" % (dep, n, i))
    for n in S["obligatorios"]:
        s = S["alias"].get(slug(n), slug(n))
        if s not in L and not any(slug(v["nombre"]) == slug(n) for v in L.values()):
            falla("lugares: falta «%s»" % n)
    c = S["caja"]
    for i, l in L.items():
        if not (c["lon_min"] <= l["lon"] <= c["lon_max"] and c["lat_min"] <= l["lat"] <= c["lat_max"]):
            falla("lugares: «%s» cae fuera de la caja" % i)
    Fu = carga("fuente.json")
    for k in ("relieve", "fallas", "frontera", "lugares"):
        cc = Fu["capas"].get(k) or {}
        if not all(cc.get(x) for x in ("fuente", "licencia", "descarga", "atribucion")):
            falla("fuente.json: la capa «%s» no trae fuente, licencia, descarga y atribución" % k)
    print("%s: relieve %d×%d (%d KB, %d a %d m) · %d trazos de falla · frontera %d puntos · %d lugares · %s"
          % (sid, w, h, peso // 1024, M["min_m"], M["max_m"], len(F["trazos"]), len(B["anillos"][0]), len(L), "OK" if not fallas else "%d fallas" % len(fallas)))
    return 1 if fallas else 0


def main():
    ap = argparse.ArgumentParser(description="Arma (o revisa) un set 3D de geodatos para la maqueta de /video-3d.",
                                 epilog="Sets: " + ", ".join(SETS))
    ap.add_argument("set", help="id del set (carpeta de design/sets3d/)")
    ap.add_argument("--check", action="store_true", help="solo revisa el set ya escrito (sin red)")
    ap.add_argument("--capa", choices=list(CAPAS), help="rehace solo esa capa")
    a = ap.parse_args()
    if a.set not in SETS:
        print("set desconocido: %s (hay: %s)" % (a.set, ", ".join(SETS)), file=sys.stderr)
        return 2
    if not a.check:
        try:
            construir(a.set, a.capa)
        except (RuntimeError, AssertionError, subprocess.CalledProcessError) as e:
            print("FALLA al armar el set: %s" % e, file=sys.stderr)
            return 1
    return revisar(a.set)


if __name__ == "__main__":
    sys.exit(main())
