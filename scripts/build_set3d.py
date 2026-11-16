#!/usr/bin/env python3
"""Arma un «set 3D»: los geodatos de un territorio para la maqueta que vuela (/video-3d).

uso:
  python3 scripts/build_set3d.py guatemala            baja (con caché) y escribe design/sets3d/guatemala/
  python3 scripts/build_set3d.py guatemala --check    revisa el set ya escrito (sin red); 0 ok · 1 falla
  python3 scripts/build_set3d.py guatemala --capa lugares   rehace solo una capa (relieve|fallas|frontera|lugares)
  python3 scripts/build_set3d.py capital              un set de ciudad (escala «ciudad»): design/sets3d/capital/
  python3 scripts/build_set3d.py --lista              los sets que sabe armar, con su escala

Dos tipos de set (la ESCALA del mundo que los usa, `mundo.escala` del maqueta.json; fuente.json → escala):
  pais    un territorio grande en km (relieve a zoom 8, ≈ 0.7 km por celda). Capas:
    relieve.png + relieve.json   malla de alturas (Mapzen Terrain Tiles, formato terrarium; R = byte alto, G = byte bajo
                                 de «metros + desfase»; PNG sin perfil de color, filtro «Up»)
    fallas.json                  trazos de GEM Global Active Faults dentro de la caja (CC BY-SA 4.0)
    frontera.json                contorno del país y bordes de los vecinos dentro de la caja (Natural Earth 1:50m,
                                 design/mapas/paises-50m.json)
    lugares.json                 cabeceras, ciudades y pueblos de OpenStreetMap (Overpass, ODbL) con un peso para la luz
  ciudad  una caja de pocos km en metros (relieve a zoom 14, ≈ 15 m por celda). Coordenadas en METROS locales:
          x = (lon − lon0)·m_lon (este), y = (lat − lat0)·m_lat (norte), enteros; lon0/lat0/m_lon/m_lat en relieve.json →
          proyeccion (de ahí se recupera lon/lat). Capas de OpenStreetMap (Overpass, ODbL):
    relieve.png + relieve.json   como en pais, con `base_m` (la altura más baja de la caja: el suelo de la maqueta)
    calles.json                  calles por clase (autopista, primaria, secundaria, terciaria, residencial, peatonal) y las
                                 arterias con nombre de design/vias/<vias>.fuente.json (la misma consulta y caché de
                                 scripts/build_vias.py en sesiones/_descargas/vias/, ahora en metros y no en píxeles)
    edificios.json               polígonos simplificados con su altura: `height`, o `building:levels` × 3 m; sin dato,
                                 una altura modesta por defecto (marcados: `con_altura` cuenta los que traen dato)
    agua.json                    lagos y estanques (polígonos) y ríos (líneas)
    zonas.json                   parques y áreas verdes (polígonos, con su nombre si lo tienen)
    lugares.json                 los lugares de la receta de las vías y los nodos con nombre (barrios, zonas, hitos)
  fuente.json                    fuente, licencia, fecha de descarga y atribución de cada capa; `pie` y `pie_claves` (lo
                                 que el pie del video tiene que nombrar, M3D7)

Las descargas quedan en sesiones/_descargas/sets3d/<set>/ (caché: no se vuelve a bajar lo que ya está; Overpass se
reintenta con calma en varios espejos). El render del video nunca llama a la red: solo lee design/sets3d/<set>/.
Python stdlib; decodifica los PNG de los mosaicos con ffmpeg. Salida: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse, datetime, json, math, os, re, struct, subprocess, sys, time, unicodedata, urllib.parse, urllib.request, zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTE = "set3d-build/1.0 (stdlib urllib)"

SETS = {
    "guatemala": {
        "escala": "pais",
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
    # el centro de la capital: zonas 1, 2, 3, 4, 5, 8, 9, 10, 11, 13 y El Trébol (≈ 6.5 × 7.2 km). La receta de las vías
    # (design/vias/capital.fuente.json) cubre 26 × 34 km: a escala de ciudad, con calles residenciales y edificios, esa caja
    # pesaría decenas de MB; esta guarda el repositorio por debajo de 5 MB y tiene lo que una historia de la capital nombra
    "capital": {
        "escala": "ciudad",
        "nombre": "Ciudad de Guatemala (centro)",
        "caja": {"lon_min": -90.550, "lon_max": -90.490, "lat_min": 14.585, "lat_max": 14.650},
        "celda_m": 15,                       # relieve: ≈ 15 m por celda
        "zoom": 14,                          # mosaicos terrarium: ≈ 9 m por píxel
        "vias": "capital",                   # design/vias/<vias>.fuente.json: arterias y lugares (y su caché de Overpass)
        "altura_defecto_m": 6.0,             # un edificio sin `height` ni `building:levels`: dos pisos
        "m_por_nivel": 3.0,
        "edificio_min_m2": 15,
        "lugares_obligatorios": ["capital", "el-trebol"],
    },
}
DESFASE_M = 8000      # la altura se guarda como metros + DESFASE (el fondo del mar llega a −8000: la fosa se ve)
URL_RELIEVE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
URL_FALLAS = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults_harmonized.geojson"
URLS_OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


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
    if S.get("escala") == "ciudad":   # la ciudad va en metros: x = (lon − lon0)·m_lon, y = (lat − lat0)·m_lat; el suelo es base_m
        meta["proyeccion"].update({"m_lon": round(111320.0 * math.cos(math.radians(lat0)), 2), "m_lat": 110574.0})
        meta["base_m"] = hmin
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


# ---------- sets de ciudad (escala «ciudad»): todo en metros locales ----------
OSM_CIUDAD = "© OpenStreetMap"
CLASE_CALLE = {"motorway": "autopista", "motorway_link": "autopista", "trunk": "autopista", "trunk_link": "autopista",
               "primary": "primaria", "primary_link": "primaria", "secondary": "secundaria", "secondary_link": "secundaria",
               "tertiary": "terciaria", "tertiary_link": "terciaria", "residential": "residencial", "unclassified": "residencial",
               "living_street": "residencial", "pedestrian": "peatonal"}
CLASES_CIUDAD = ("autopista", "primaria", "secundaria", "terciaria", "residencial", "peatonal")


def tamano_ciudad(S):
    """Celdas del relieve de una ciudad: la caja a ≈ celda_m metros por celda."""
    c, lat0 = S["caja"], (S["caja"]["lat_min"] + S["caja"]["lat_max"]) / 2
    ancho = int(round((c["lon_max"] - c["lon_min"]) * 111320.0 * math.cos(math.radians(lat0)) / S["celda_m"]))
    alto = int(round((c["lat_max"] - c["lat_min"]) * 110574.0 / S["celda_m"]))
    return ancho, alto


def proyector_m(S):
    """lon, lat → (x, y) en metros locales (el centro de la caja es 0, 0), la misma cuenta que relieve.json → proyeccion."""
    c = S["caja"]
    lon0, lat0 = (c["lon_min"] + c["lon_max"]) / 2, (c["lat_min"] + c["lat_max"]) / 2
    mlon, mlat = round(111320.0 * math.cos(math.radians(lat0)), 2), 110574.0
    return lambda lon, lat: ((lon - lon0) * mlon, (lat - lat0) * mlat)


def overpass(consulta, destino, espejos=None):
    """Una consulta a Overpass con caché y calma: varios espejos, reintentos con espera creciente (el servidor público
    se satura). Si `destino` ya existe no toca la red."""
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return destino
    ultimo = None
    for vuelta in range(3):
        for url in espejos or URLS_OVERPASS:
            try:
                bajar(url, destino, datos=urllib.parse.urlencode({"data": consulta}).encode(), intentos=1)
                with open(destino, encoding="utf-8") as f:
                    r = json.load(f)
                if "error" in str(r.get("remark", "")).lower():   # Overpass corta por tiempo o memoria y responde 200 a medias
                    raise RuntimeError(r["remark"])
                return destino
            except Exception as e:   # red, 429/504, o una respuesta que no es JSON
                ultimo = e
                if os.path.exists(destino):
                    os.remove(destino)
        time.sleep(20 * (vuelta + 1))
    raise RuntimeError("Overpass no respondió (%s)" % ultimo)


def osm_ciudad(sid, S, cache):
    """Los elementos de OpenStreetMap de la caja: las vías de la receta de build_vias.py (su caché) + una consulta propia
    con las calles menores, los edificios, el agua, las zonas verdes y los lugares con nombre. → lista de elementos."""
    import build_vias as BV
    c = S["caja"]
    receta = BV.leer_receta(S["vias"])
    els = {("v", e["id"]): e for e in BV.bajar(receta)}   # la misma caché: sesiones/_descargas/vias/<vias>.osm.json
    caja = "(%s,%s,%s,%s)" % (c["lat_min"], c["lon_min"], c["lat_max"], c["lon_max"])
    consulta = ('[out:json][timeout:180];('
                'way["highway"~"^(motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|'
                'residential|unclassified|living_street|pedestrian)$"]{c};'
                'way["building"]{c};'
                'way["natural"="water"]{c};relation["natural"="water"]{c};way["waterway"~"^(river|stream|canal)$"]{c};'
                'way["leisure"~"^(park|garden|pitch|stadium)$"]{c};way["landuse"~"^(grass|recreation_ground|forest|cemetery|village_green)$"]{c};'
                'node["place"~"^(suburb|neighbourhood|quarter)$"]["name"]{c};'
                'node["amenity"~"^(townhall|university|hospital|marketplace)$"]["name"]{c};node["tourism"~"^(attraction|museum)$"]["name"]{c};'
                ');out tags geom;').replace("{c}", caja)
    ruta = overpass(consulta, os.path.join(cache, "overpass_ciudad.json"))
    with open(ruta, encoding="utf-8") as f:
        for e in json.load(f)["elements"]:
            els[(e["type"][0], e["id"])] = e
    return list(els.values()), receta


def dp(pts, tol):
    """Douglas-Peucker (iterativo) sobre [(x, y), …]."""
    if len(pts) < 3:
        return list(pts)
    guarda, pila = {0, len(pts) - 1}, [(0, len(pts) - 1)]
    while pila:
        a, b = pila.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        imax, dmax = 0, 0.0
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / L
            if d > dmax:
                imax, dmax = i, d
        if dmax > tol:
            guarda.add(imax); pila += [(a, imax), (imax, b)]
    return [pts[i] for i in sorted(guarda)]


def recortes(pts, dentro):
    """Una polilínea → sus tramos seguidos dentro de la caja (al menos 2 puntos)."""
    out, tramo = [], []
    for q in pts + [None]:
        if q is not None and dentro(q):
            tramo.append(q)
        else:
            if len(tramo) >= 2:
                out.append(tramo)
            tramo = []
    return out


def area_m2(pol):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pol, pol[1:] + pol[:1]))) / 2


def entero(v):
    return int(round(v))


def altura_osm(t, S):
    """La altura de un edificio en metros y si viene de un dato (`height` o `building:levels`)."""
    for k in ("height", "building:height"):
        mo = re.match(r"\s*([0-9]+(?:[.,][0-9]+)?)", t.get(k, ""))
        if mo:
            v = float(mo.group(1).replace(",", "."))
            if 2 <= v <= 400:
                return round(v, 1), True
    mo = re.match(r"\s*([0-9]+)", t.get("building:levels", ""))
    if mo and 1 <= int(mo.group(1)) <= 120:
        return round(int(mo.group(1)) * S["m_por_nivel"], 1), True
    return S["altura_defecto_m"], False


def capas_ciudad(sid, S, cache, salida):
    """Calles, edificios, agua, zonas y lugares de la caja (metros locales enteros). → {capa: info de fuente.json}."""
    import build_vias as BV
    els, receta = osm_ciudad(sid, S, cache)
    xy = proyector_m(S)
    c = S["caja"]
    (bx0, by0), (bx1, by1) = xy(c["lon_min"], c["lat_min"]), xy(c["lon_max"], c["lat_max"])
    dentro = lambda q: bx0 <= q[0] <= bx1 and by0 <= q[1] <= by1
    geo = lambda e: [xy(p["lon"], p["lat"]) for p in e.get("geometry") or [] if p]
    hoy = datetime.date.today().isoformat()
    osm = {"fuente": "OpenStreetMap (Overpass API) y la receta de las vías design/vias/%s.fuente.json" % S["vias"], "url": "https://www.openstreetmap.org/copyright",
           "licencia": "ODbL 1.0", "atribucion": "Calles, edificios y lugares: © OpenStreetMap", "descarga": hoy}

    # calles por clase (las arterias de la receta, además, como UN trazo con nombre: el camino de una `carretera`)
    calles, vistos = [], set()
    for e in els:
        t = e.get("tags", {})
        cl = CLASE_CALLE.get(t.get("highway"))
        if e.get("type") != "way" or not cl or e["id"] in vistos:
            continue
        vistos.add(e["id"])
        for tramo in recortes(geo(e), dentro):
            pts = [[entero(x), entero(y)] for x, y in dp(tramo, 1.5)]
            if len(pts) >= 2:
                calles.append({"clase": cl, "nombre": t.get("name", ""), "puntos": pts})
    calles.sort(key=lambda k: (CLASES_CIUDAD.index(k["clase"]), k["nombre"], k["puntos"][0]))
    ancho_m, alto_m = bx1 - bx0, by1 - by0
    xy_lienzo = lambda lat, lon: (xy(lon, lat)[0] - bx0, by1 - xy(lon, lat)[1])   # el «lienzo» de build_vias.arteria, en metros
    rc = dict(receta, lienzo=[ancho_m, alto_m])
    arterias = {}
    for a in receta["arterias"]:
        try:
            r = BV.arteria(els, xy_lienzo, rc, a)
        except SystemExit:   # la arteria no pasa por esta caja
            continue
        nums = [float(v) for v in re.findall(r"-?[0-9.]+", r["d"])]
        pts = [[entero(nums[i] + bx0), entero(by1 - nums[i + 1])] for i in range(0, len(nums) - 1, 2)]
        L = sum(math.hypot(b[0] - a_[0], b[1] - a_[1]) for a_, b in zip(pts, pts[1:]))
        if L >= 400:
            arterias[a["id"]] = {"nombre": a["nombre"], "puntos": pts, "m": entero(L)}
    with open(os.path.join(salida, "calles.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "unidad": "m", "clases": list(CLASES_CIUDAD), "calles": calles, "arterias": arterias}, f, ensure_ascii=False, separators=(",", ":"))
    print("calles: %d tramos (%s) · %d arterias con nombre: %s" % (len(calles), ", ".join("%s %d" % (k, sum(1 for q in calles if q["clase"] == k)) for k in CLASES_CIUDAD),
                                                                    len(arterias), ", ".join(arterias)))

    # edificios: [altura_m, x0, y0, x1, y1, …] (anillo exterior simplificado, sin repetir el primer punto)
    edificios, nombres, con_altura = [], {}, 0
    for e in els:
        t = e.get("tags", {})
        if e.get("type") != "way" or "building" not in t:
            continue
        pol = geo(e)
        if len(pol) < 4 or not all(dentro(q) for q in pol):
            continue
        pol = dp(pol[:-1] if pol[0] == pol[-1] else pol, 0.8)
        if len(pol) < 3 or area_m2(pol) < S["edificio_min_m2"]:
            continue
        h, dato = altura_osm(t, S)
        con_altura += dato
        if t.get("name"):
            nombres[str(len(edificios))] = t["name"]
        edificios.append([h] + [entero(v) for q in pol for v in q])
    with open(os.path.join(salida, "edificios.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "unidad": "m", "formato": "[altura_m, x0, y0, x1, y1, …]: anillo exterior sin cerrar", "altura_defecto_m": S["altura_defecto_m"],
                   "con_altura": con_altura, "edificios": edificios, "nombres": nombres}, f, ensure_ascii=False, separators=(",", ":"))
    print("edificios: %d (%d con altura de OSM; el resto %.0f m)" % (len(edificios), con_altura, S["altura_defecto_m"]))

    # agua: polígonos (lagos, estanques; anillos exteriores de las relaciones) y ríos
    poligonos, rios = [], []
    for e in els:
        t = e.get("tags", {})
        if t.get("natural") == "water":
            anillos = [geo(e)] if e["type"] == "way" else [[xy(p["lon"], p["lat"]) for p in m.get("geometry") or []] for m in e.get("members", []) if m.get("role") == "outer"]
            for pol in anillos:
                if len(pol) >= 4 and sum(dentro(q) for q in pol) >= len(pol) // 2:
                    pol = [(min(max(x, bx0), bx1), min(max(y, by0), by1)) for x, y in dp(pol[:-1] if pol[0] == pol[-1] else pol, 1.5)]
                    if len(pol) >= 3 and area_m2(pol) >= 40:
                        poligonos.append({"nombre": t.get("name", ""), "puntos": [[entero(x), entero(y)] for x, y in pol]})
        elif t.get("waterway") in ("river", "stream", "canal") and e["type"] == "way":
            for tramo in recortes(geo(e), dentro):
                rios.append({"nombre": t.get("name", ""), "clase": t["waterway"], "puntos": [[entero(x), entero(y)] for x, y in dp(tramo, 2.0)]})
    with open(os.path.join(salida, "agua.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "unidad": "m", "poligonos": poligonos, "rios": rios}, f, ensure_ascii=False, separators=(",", ":"))
    print("agua: %d polígonos, %d ríos" % (len(poligonos), len(rios)))

    # zonas: parques y áreas verdes (id por su nombre: lo que `zona` puede teñir con `area`)
    zonas, ids = [], {}
    for e in els:
        t = e.get("tags", {})
        clase = t.get("leisure") if t.get("leisure") in ("park", "garden", "pitch", "stadium") else t.get("landuse") if t.get("landuse") in (
            "grass", "recreation_ground", "forest", "cemetery", "village_green") else None
        if not clase or e.get("type") != "way":
            continue
        pol = geo(e)
        if len(pol) < 4 or sum(dentro(q) for q in pol) < len(pol) // 2:
            continue
        pol = [(min(max(x, bx0), bx1), min(max(y, by0), by1)) for x, y in dp(pol[:-1] if pol[0] == pol[-1] else pol, 1.5)]
        if len(pol) < 3 or area_m2(pol) < 150:
            continue
        base = slug(t.get("name", "")) or "%s-%d" % (clase, len(zonas) + 1)
        ids[base] = ids.get(base, 0) + 1
        zid = base if ids[base] == 1 else "%s-%d" % (base, ids[base])
        zonas.append({"id": zid, "nombre": t.get("name", ""), "clase": clase, "puntos": [[entero(x), entero(y)] for x, y in pol]})
    with open(os.path.join(salida, "zonas.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "unidad": "m", "zonas": zonas}, f, ensure_ascii=False, separators=(",", ":"))
    print("zonas: %d (%d con nombre)" % (len(zonas), sum(1 for z in zonas if z["nombre"])))

    # lugares: los de la receta de las vías que caen en la caja, y los nodos con nombre (lon/lat, como en un set de país)
    lugares = {}
    for lg in receta.get("lugares", []):
        lat, lon = lg["pos"]
        if dentro(xy(lon, lat)):
            lugares[lg["id"]] = {"nombre": lg["nombre"], "lon": round(lon, 6), "lat": round(lat, 6), "clase": "receta", "peso": 1.0}
    peso = {"suburb": 0.8, "quarter": 0.7, "neighbourhood": 0.6}
    for e in sorted((e for e in els if e.get("type") == "node" and e.get("tags", {}).get("name")), key=lambda e: e["id"]):
        t = e["tags"]
        if not dentro(xy(e["lon"], e["lat"])):
            continue
        lid = slug(t["name"])
        if not lid or lid in lugares:
            continue
        clase = t.get("place") or t.get("amenity") or t.get("tourism")
        lugares[lid] = {"nombre": t["name"], "lon": round(e["lon"], 6), "lat": round(e["lat"], 6), "clase": clase, "peso": peso.get(clase, 0.5)}
    with open(os.path.join(salida, "lugares.json"), "w", encoding="utf-8") as f:
        json.dump({"set": sid, "lugares": lugares}, f, ensure_ascii=False, indent=0, separators=(",", ":"))
    print("lugares: %d" % len(lugares))
    return {"calles": dict(osm, atribucion="Calles: © OpenStreetMap"), "edificios": dict(osm, atribucion="Edificios: © OpenStreetMap"),
            "agua": dict(osm, atribucion="Agua: © OpenStreetMap"), "zonas": dict(osm, atribucion="Zonas verdes: © OpenStreetMap"),
            "lugares": dict(osm, atribucion="Lugares: © OpenStreetMap")}


def construir_ciudad(sid, S, solo=None):
    cache = os.path.join(RAIZ, "sesiones", "_descargas", "sets3d", sid)
    salida = os.path.join(RAIZ, "design", "sets3d", sid)
    os.makedirs(cache, exist_ok=True); os.makedirs(salida, exist_ok=True)
    ruta_f = os.path.join(salida, "fuente.json")
    fuente = {"set": sid, "escala": "ciudad", "nombre": S["nombre"], "caja": S["caja"], "capas": {}}
    if os.path.exists(ruta_f):
        with open(ruta_f, encoding="utf-8") as f:
            fuente = json.load(f)
    hoy = datetime.date.today().isoformat()
    if solo in (None, "relieve"):
        ancho, alto = tamano_ciudad(S)
        info = capa_relieve(sid, dict(S, ancho=ancho, alto=alto), cache, salida)
        info["fuente"] = info["fuente"].replace("zoom %d" % S["zoom"], "zoom %d (≈ %d m por celda)" % (S["zoom"], S["celda_m"]))
        info["descarga"] = hoy
        fuente["capas"]["relieve"] = info
    if solo is None or solo in ("calles", "edificios", "agua", "zonas", "lugares"):
        fuente["capas"].update(capas_ciudad(sid, S, cache, salida))
    orden = [k for k in ("relieve", "calles", "edificios", "agua", "zonas", "lugares") if k in fuente["capas"]]
    fuente["escala"] = "ciudad"
    fuente["pie"] = "Relieve: Mapzen Terrain Tiles · Calles, edificios y lugares: © OpenStreetMap (ODbL)"
    fuente["pie_claves"] = {"relieve": "Mapzen", "calles": "OpenStreetMap", "edificios": "OpenStreetMap", "agua": "OpenStreetMap",
                            "zonas": "OpenStreetMap", "lugares": "OpenStreetMap"}
    fuente["capas"] = {k: fuente["capas"][k] for k in orden}
    with open(ruta_f, "w", encoding="utf-8") as f:
        json.dump(fuente, f, ensure_ascii=False, indent=1)
    print("fuente.json: " + fuente["pie"])


def revisar_ciudad(sid):
    S = SETS[sid]
    d = os.path.join(RAIZ, "design", "sets3d", sid)
    fallas = []

    def falla(m):
        fallas.append(m); print("  FALLA " + m)
    capas = ("relieve.png", "relieve.json", "calles.json", "edificios.json", "agua.json", "zonas.json", "lugares.json", "fuente.json")
    for f in capas:
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
        if filas[j][3 * i] * 256 + filas[j][3 * i + 1] - M["desfase_m"] != v:
            falla("relieve: la muestra (%d, %d) no coincide" % (i, j))
    for k in ("m_lon", "m_lat"):
        if not M["proyeccion"].get(k):
            falla("relieve.json: la proyección de una ciudad va en metros (falta %s)" % k)
    if "base_m" not in M:
        falla("relieve.json: falta base_m (el suelo de la maqueta)")
    C, E, A, Zo, L = carga("calles.json"), carga("edificios.json"), carga("agua.json"), carga("zonas.json"), carga("lugares.json")["lugares"]
    if len(C["calles"]) < 200 or not any(q["clase"] in ("autopista", "primaria") for q in C["calles"]):
        falla("calles: muy pocas (%d) o sin autopistas ni primarias" % len(C["calles"]))
    if not C.get("arterias"):
        falla("calles: ninguna arteria con nombre de la receta de las vías")
    if len(E["edificios"]) < 500:
        falla("edificios: solo %d" % len(E["edificios"]))
    if any(len(e) < 7 or len(e) % 2 == 0 or not 2 <= e[0] <= 400 for e in E["edificios"]):
        falla("edificios: hay alguno sin [altura, x0, y0, x1, y1, x2, y2…] o con una altura imposible")
    if not Zo["zonas"]:
        falla("zonas: ninguna zona verde")
    for i in S.get("lugares_obligatorios", []):
        if i not in L:
            falla("lugares: falta «%s»" % i)
    c = S["caja"]
    for i, l in L.items():
        if not (c["lon_min"] <= l["lon"] <= c["lon_max"] and c["lat_min"] <= l["lat"] <= c["lat_max"]):
            falla("lugares: «%s» cae fuera de la caja" % i)
    Fu = carga("fuente.json")
    if Fu.get("escala") != "ciudad":
        falla("fuente.json: `escala` debe ser «ciudad»")
    for k in ("relieve", "calles", "edificios", "agua", "zonas", "lugares"):
        cc = Fu["capas"].get(k) or {}
        if not all(cc.get(x) for x in ("fuente", "licencia", "descarga", "atribucion")):
            falla("fuente.json: la capa «%s» no trae fuente, licencia, descarga y atribución" % k)
        clave = (Fu.get("pie_claves") or {}).get(k)
        if not clave or clave not in Fu.get("pie", ""):
            falla("fuente.json: el pie no nombra la fuente de la capa «%s»" % k)
    peso = sum(os.path.getsize(os.path.join(d, f)) for f in capas)
    if peso > 5e6:
        falla("el set pesa %.1f MB (tope 5 MB en el repositorio): achica la caja o simplifica más" % (peso / 1e6))
    print("%s (ciudad): relieve %d×%d (%d a %d m) · %d calles, %d arterias · %d edificios (%d con altura) · %d agua · %d zonas · %d lugares · %.2f MB · %s"
          % (sid, w, h, M["min_m"], M["max_m"], len(C["calles"]), len(C["arterias"]), len(E["edificios"]), E["con_altura"],
             len(A["poligonos"]) + len(A["rios"]), len(Zo["zonas"]), len(L), peso / 1e6, "OK" if not fallas else "%d fallas" % len(fallas)))
    return 1 if fallas else 0


def construir(sid, solo=None):
    S = SETS[sid]
    if S.get("escala") == "ciudad":
        return construir_ciudad(sid, S, solo)
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
    if S.get("escala") == "ciudad":
        return revisar_ciudad(sid)
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
    ap.add_argument("set", nargs="?", help="id del set (carpeta de design/sets3d/)")
    ap.add_argument("--check", action="store_true", help="solo revisa el set ya escrito (sin red)")
    ap.add_argument("--capa", choices=list(CAPAS) + ["calles", "edificios", "agua", "zonas"], help="rehace solo esa capa (en una ciudad, calles|edificios|agua|zonas|lugares rehacen las cinco de OSM)")
    ap.add_argument("--lista", action="store_true", help="los sets que sabe armar, con su escala")
    a = ap.parse_args()
    if a.lista:
        for k, v in SETS.items():
            print("%-10s escala %-7s %s" % (k, v.get("escala", "pais"), v["nombre"]))
        return 0
    if not a.set:
        ap.print_usage(sys.stderr)
        return 2
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
