"""LA ESCENA VIVA de la maqueta 3D (usuario, 2026-11-16: «cada escena debe tener bastantes detalles… se vea real… con
animaciones»): los gates que miden, SOBRE LOS DATOS (nunca sobre píxeles), si un tramo de cerca está lleno, es variado y
tiene vida. Aplica a los mundos de cerca (escala `esquema` o `ciudad`) de un video (no al modo pieza ni a los mapas).

    cosas(R, t)      lo que hay en el mundo en t: cajas con su tipo, su ficha y si se mueven
    medir(m, R)      por muestra: cuánto cuadro ocupan, cuántas cosas distintas se ven, si algo se mueve → resumen del tramo
    gates(m, R)      M3D15 cuadro lleno · M3D16 variedad · M3D17 vida · M3D18 a su distancia · M3D19 nada flota

Cada tipo del catálogo dice en su ficha (video/maqueta/<clase>/<tipo>.json) lo que hace falta para medir:
    nivel        «objeto» (una cosa suelta), «escenario» (un lugar completo: finca, beneficio, tostaduría) o «fondo» (el
                 tejido del mundo: calles, edificios genéricos, agua; no llena la escena)
    contiene     lo que muestra, en palabras («sacos», «tostadora», «gente que cata»): cuenta para la variedad
    animado      qué se mueve solo (texto), o false
    gente        true si es o incluye personas que hacen algo
    distancia_m  [mín, máx] a la que se lee
    caja_m       [largo, ancho, alto] (por defecto, sus `medidas`): cuánto cuadro ocupa

Los umbrales (UMBRAL) son la vara: se ajustan UNA vez con el video de referencia aprobado (referencias/diseno/vara3d.json).
Lo llama scripts/maqueta3d.py (gates_formato) y `maqueta3d.py escena` (la medida y la hoja de un mundo).
"""
import json
import math
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARA = os.path.join(RAIZ, "referencias", "diseno", "vara3d.json")
ESCALAS_CERCA = ("esquema", "ciudad")
UMBRAL = {
    "ocupacion": 0.35,        # M3D15: parte de la zona libre cubierta por cosas con volumen
    "muestras_ok": 0.70,      # M3D15–M3D17: parte de las muestras del tramo que cumple
    "variedad": 4,            # M3D16: cosas distintas en cuadro
    "objetos_sin_escenario": 6,
    "lejos_x": 2.0,           # M3D18: falla si lo que mira la cámara queda a más de esto × su distancia máxima
    "apoyo_m": 0.6,           # M3D19: holgura entre un actor levantado y lo que lo sostiene
}
PASO_S = 0.5                  # una muestra cada medio segundo
REJILLA = (18, 28)            # celdas de la zona libre (ancho × alto)
PLANAS = ("calles", "agua", "zona", "carretera", "trazo")   # piezas sin volumen
# `nivel: "fondo"` en la ficha = el tejido del mundo (calles, edificios genéricos, agua): no llena la escena ni cuenta como
# objeto; todo el fondo junto suma UNA cosa a la variedad. Lo que llena es lo que la historia puso ahí.


def ruta_vara():
    """Dónde vive la vara (MAQUETA_VARA la cambia: las pruebas miden con una vara propia o sin ninguna)."""
    return os.environ.get("MAQUETA_VARA") or VARA


def umbrales(base=False):
    """UMBRAL con lo que diga la vara aprobada (referencias/diseno/vara3d.json → umbral), si existe. base: sin la vara."""
    u = dict(UMBRAL)
    if base:
        return u
    try:
        with open(ruta_vara(), encoding="utf-8") as f:
            u.update({k: v for k, v in (json.load(f).get("umbral") or {}).items() if k in u})
    except (OSError, ValueError):
        pass
    return u


def aplica(m, R):
    """¿Este maqueta (resuelto) es un tramo de cerca de un video? (los mapas, el modo pieza y la capa global no)."""
    return R["mundo"]["escala"] in ESCALAS_CERCA and not R["pieza"] and not m.get("_capa_global")


def _ficha(M3, tipo, clase=None):
    return M3.ficha(tipo, clase) or {}


def _caja_de(fi, tam=1.0):
    c = fi.get("caja_m")
    if not c:
        md = fi.get("medidas") or {}
        c = [md.get("largo_m", 2.0), md.get("ancho_m", 2.0), md.get("alto_m", 2.0)]
    return [float(c[0]) * tam, float(c[1]) * tam, float(c[2]) * tam]


def cosas(M3, R, t):
    """Lo que hay en el mundo en t → [{clave, tipo, clase, x, y, lev, l, a, h, dx, dy, mueve, gente, nivel, contiene,
    animado, dist}] en unidades de la escena (l, a, h y lev también). Las piezas planas van con h = 0 (no ocupan)."""
    um = 1.0 / R["mundo"]["unidad_m"]
    mov, out = R.get("_moviles") or {}, []

    def cosa(clave, fi, x, y, l, a, h, dx=1.0, dy=0.0, lev=0.0, mueve=False):
        out.append({"clave": clave, "tipo": fi.get("tipo", clave), "clase": fi.get("clase"), "x": x, "y": y, "lev": lev, "l": l, "a": a, "h": h,
                    "dx": dx, "dy": dy, "mueve": bool(mueve or fi.get("animado")), "gente": bool(fi.get("gente")), "nivel": fi.get("nivel") or "objeto",
                    "contiene": list(fi.get("contiene") or []), "animado": bool(fi.get("animado")), "dist": fi.get("distancia_m")})

    for pz in R["piezas"]:
        tipo, fi = pz["tipo"], _ficha(M3, pz["tipo"], "pieza")
        if tipo == "actor":
            M = mov.get(pz["id"])
            if not M:
                continue
            x, y, dx, dy, v, vis = M.en(t, 0)
            if not vis:
                continue
            fo = _ficha(M3, pz["objeto"], "objeto")
            l, a, h = (c * um for c in _caja_de(fo, float(pz.get("tamano", 1))))
            cosa(pz["objeto"], fo, x, y, l, a, h, dx, dy, float(pz.get("lev", 0)) * um, abs(v) * R["mundo"]["unidad_m"] > 0.05)
        elif tipo == "flujo":
            M = mov.get(pz["id"])
            if not M:
                continue
            for n in range(len(M)):
                x, y, dx, dy, v, vis = M.en(t, n)
                if not vis:
                    continue
                obj = pz["tipos"][pz["vehiculos"][n][1]]
                fo = _ficha(M3, obj, "objeto")
                l, a, h = (c * um for c in _caja_de(fo, float(pz.get("tamano", 1))))
                cosa(obj, fo, x, y, l, a, h, dx, dy, 0.0, abs(v) * R["mundo"]["unidad_m"] > 0.05)
        elif tipo == "edificios":
            for e in pz.get("edificios") or []:
                xs, ys = e[1::2], e[2::2]
                cosa("edificios", fi, (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys), float(e[0]) * um)
        elif pz.get("poligono"):     # una pieza sobre un polígono (el cafetal): su caja y la altura de su ficha
            xs, ys = pz["poligono"][0::2], pz["poligono"][1::2]
            if xs and isinstance(xs[0], (list, tuple)):
                xs, ys = [q[0] for q in pz["poligono"]], [q[1] for q in pz["poligono"]]
            alto = _caja_de(fi)[2] * um + float(pz.get("pendiente_m", 0)) * um
            cosa(tipo, fi, (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(xs) - min(xs), max(ys) - min(ys), alto)
        elif "x" in pz and "y" in pz and tipo not in PLANAS:   # una pieza puesta en un lugar (beneficio, tostaduría)
            l, a, h = (c * um for c in _caja_de(fi, float(pz.get("tamano", 1))))
            r = math.radians(float(pz.get("rumbo", 0)))
            cosa(tipo, fi, pz["x"], pz["y"], l, a, h, math.cos(r), math.sin(r))
        elif tipo in PLANAS:
            cosa(tipo, fi, 0.0, 0.0, 0.0, 0.0, 0.0)
    return out


def _rect(c, pr, alt):
    """El rectángulo en pantalla (x0, y0, x1, y1) de la caja de una cosa: el que encierra los puntos de su caja que caen
    delante de la cámara (una rejilla de 3 × 3 × 2: con la cámara dentro o pegada a un escenario, las esquinas de atrás no
    se proyectan y las demás sí). None si ninguno se ve."""
    hx, hy = c["l"] / 2, c["a"] / 2
    z0 = alt(c["x"], c["y"]) + c["lev"]
    pts = []
    for sx in (-1, 0, 1):
        for sy in (-1, 0, 1):
            x = c["x"] + c["dx"] * hx * sx - c["dy"] * hy * sy
            y = c["y"] + c["dy"] * hx * sx + c["dx"] * hy * sy
            for z in (z0, z0 + c["h"]):
                p = pr(x, y, z)
                if p is not None:
                    pts.append(p)
    if len(pts) < 3:
        return None
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def zona_libre(Z):
    """(x0, y0, x1, y1) de la zona del cuadro donde vive el mundo: entre el titular y la banda de abajo."""
    return Z["corte"], Z["tit_y"] + 60, Z["W"] - Z["corte"], Z["fin_marcas"]


def muestra(M3, R, t, pr=None):
    """Una muestra en t → {ocupacion, claves (cosas distintas en cuadro), escenarios, objetos, gente, mueve, mira_dist}."""
    Z, S = R["zona"], R["_set"]
    cam = M3.camara_en(R["camara"], t)
    pr = pr or M3.proyector(cam, Z["W"], Z["H"], Z["H"] / 2 - Z["centro_y"])
    x0, y0, x1, y1 = zona_libre(Z)
    nx, ny = REJILLA
    cw, ch = (x1 - x0) / nx, (y1 - y0) / ny
    celdas = [[False] * nx for _ in range(ny)]
    claves, escenarios, objetos, gente, mueve = set(), 0, 0, 0, False
    for c in cosas(M3, R, t):
        if c["nivel"] == "fondo" or c["h"] <= 0:   # el tejido del mundo: todo junto, una cosa
            claves.add("(fondo)")
            continue
        r = _rect(c, pr, S.suelo)
        if not r or r[2] < x0 or r[0] > x1 or r[3] < y0 or r[1] > y1:
            continue
        if (min(r[2], x1) - max(r[0], x0)) * (min(r[3], y1) - max(r[1], y0)) < 24 * 24:   # un punto en el horizonte no cuenta
            continue
        claves.add(c["clave"]); claves.update(c["contiene"])
        escenarios += c["nivel"] == "escenario"
        objetos += 1
        gente += c["gente"]
        mueve = mueve or c["mueve"]
        for j in range(max(0, int((r[1] - y0) // ch)), min(ny, int((r[3] - y0) // ch) + 1)):
            fila = celdas[j]
            for i in range(max(0, int((r[0] - x0) // cw)), min(nx, int((r[2] - x0) // cw) + 1)):
                fila[i] = True
    if not mueve:   # un evento en curso también es vida (una ruptura, un resaltar, un trazo que se dibuja)
        mueve = any(e["t"] <= t <= e["t"] + e["dur"] for e in R["eventos"])
    return {"t": t, "ocupacion": sum(map(sum, celdas)) / float(nx * ny), "claves": sorted(claves), "escenarios": escenarios, "objetos": objetos,
            "gente": gente, "mueve": mueve, "dist_m": cam["dist"] * R["mundo"]["unidad_m"], "mira": (cam["x"], cam["y"])}


def medir(M3, m, R, U=None):
    """El tramo entero → {muestras, ocupacion (mediana), lleno, variedad (mediana), variado, vida, gente_max}."""
    U, dur = U or umbrales(), R["dur"]
    ts = [min(dur, PASO_S * k) for k in range(int(dur / PASO_S) + 1)] or [0.0]
    M = [muestra(M3, R, t) for t in ts]
    return _medida(M, U)


def _medida(M, U):
    n = float(len(M))
    med = lambda v: sorted(v)[len(v) // 2]
    return {"muestras": M, "n": len(M),
            "ocupacion": round(med([x["ocupacion"] for x in M]), 3),
            "lleno": round(sum(x["ocupacion"] >= U["ocupacion"] for x in M) / n, 3),
            "variedad": med([len(x["claves"]) for x in M]),
            "variado": round(sum(len(x["claves"]) >= U["variedad"] and (x["escenarios"] >= 1 or x["objetos"] >= U["objetos_sin_escenario"]) for x in M) / n, 3),
            "vida": round(sum(x["mueve"] for x in M) / n, 3),
            "gente_max": max(x["gente"] for x in M)}


def gates(M3, m, R):
    """M3D15–M3D19 de un tramo de cerca → [(gate, mensaje)]."""
    if not aplica(m, R):
        return []
    U, out = umbrales(), []
    F = lambda g, msg: out.append((g, msg))
    r = medir(M3, m, R)
    if r["lleno"] < U["muestras_ok"]:
        F("M3D15", "la escena se ve vacía: las cosas con volumen cubren ≥ %d %% del cuadro solo en %d %% del tramo (mínimo %d %%; mediana %d %%): "
          "acerca la cámara a lo que pasa o llena el lugar (un escenario completo, gente, objetos del oficio, el entorno)"
          % (round(100 * U["ocupacion"]), round(100 * r["lleno"]), round(100 * U["muestras_ok"]), round(100 * r["ocupacion"])))
    if r["variado"] < U["muestras_ok"]:
        F("M3D16", "poca variedad: solo en %d %% del tramo se ven ≥ %d cosas distintas con un escenario (o ≥ %d objetos) en cuadro (mínimo %d %%; "
          "mediana %d cosas): un lugar de cerca nunca es una sola cosa sobre el suelo"
          % (round(100 * r["variado"]), U["variedad"], U["objetos_sin_escenario"], round(100 * U["muestras_ok"]), r["variedad"]))
    if r["vida"] < U["muestras_ok"]:
        F("M3D17", "poca vida: algo se mueve en cuadro solo en %d %% del tramo (mínimo %d %%): gente que hace algo, un vehículo que pasa, una "
          "máquina que gira (tipos `animado` del catálogo) o un evento" % (round(100 * r["vida"]), round(100 * U["muestras_ok"])))
    # M3D18 · lo que la cámara mira, a la distancia a la que se lee (la cosa con volumen más cercana al punto que mira)
    lejos, cerca, tot = {}, {}, 0
    for x in r["muestras"]:
        cs = [c for c in cosas(M3, R, x["t"]) if c["h"] > 0 and c["dist"]]
        if not cs:
            continue
        c = min(cs, key=lambda c: math.hypot(c["x"] - x["mira"][0], c["y"] - x["mira"][1]) - max(c["l"], c["a"]) / 2)
        if math.hypot(c["x"] - x["mira"][0], c["y"] - x["mira"][1]) > max(c["l"], c["a"]):
            continue
        tot += 1
        if x["dist_m"] > c["dist"][1] * U["lejos_x"]:
            lejos[c["clave"]] = lejos.get(c["clave"], 0) + 1
        elif x["dist_m"] > c["dist"][1] or x["dist_m"] < c["dist"][0]:
            cerca[c["clave"]] = cerca.get(c["clave"], 0) + 1
    for k, n in lejos.items():
        if n / float(max(1, tot)) > 0.5:
            d = (_ficha(M3, k).get("distancia_m") or [0, 0])
            F("M3D18", "la cámara mira «%s» desde demasiado lejos más de la mitad del tramo: se lee a %g–%g m (acerca la cámara)" % (k, d[0], d[1]))
    R.setdefault("_avisos_escena", []).extend("M3D18 «%s» queda fuera de su distancia de lectura en %d muestra(s)" % kv for kv in cerca.items())
    # M3D19 · nada flota: un actor levantado del suelo tiene algo debajo que lo sostiene
    todas = cosas(M3, R, 0.0)
    for c in todas:
        if c["clase"] != "objeto" or c["lev"] * R["mundo"]["unidad_m"] <= U["apoyo_m"]:
            continue
        apoyo = False
        for o in todas:
            if o is c or o["h"] <= 0:
                continue
            ux, uy = c["x"] - o["x"], c["y"] - o["y"]
            lx, ly = ux * o["dx"] + uy * o["dy"], -ux * o["dy"] + uy * o["dx"]
            if abs(lx) <= o["l"] / 2 + 0.5 and abs(ly) <= o["a"] / 2 + 0.5 and c["lev"] <= o["lev"] + o["h"] + U["apoyo_m"] / R["mundo"]["unidad_m"]:
                apoyo = True
                break
        if not apoyo:
            F("M3D19", "«%s» está a %.1f m del suelo sin nada debajo que lo sostenga: ponlo sobre algo (una mesa, una tarima, otra pieza) o bájalo"
              % (c["clave"], c["lev"] * R["mundo"]["unidad_m"]))
    return out


def vara_de(medidas):
    """Los umbrales que fija un video de referencia aprobado. medidas: lo que devolvió `medir` para cada tramo de cerca (en
    cada formato). La regla, sobre el tramo MÁS FLOJO de la referencia: ocupación = 70 % de su mediana; variedad = la suya
    menos 1; y, ya con esos dos, la parte del tramo que tiene que cumplir = la suya menos 5 puntos (entre 70 y 90 %). Si con
    esa ocupación algún tramo de la referencia no llegara a cumplir con 5 puntos de holgura, la ocupación baja de punto en
    punto hasta que sí: la referencia SIEMPRE pasa su vara. Nunca por debajo de los umbrales de partida: la vara sube, no baja."""
    u = umbrales(base=True)
    if not medidas:
        return u
    piso, holgura = u["ocupacion"], 0.05
    peor = lambda: min(min(r["lleno"], r["variado"], r["vida"]) for r in (_medida(r["muestras"], u) for r in medidas))
    u["variedad"] = max(u["variedad"], min(r["variedad"] for r in medidas) - 1)
    if peor() < u["muestras_ok"] + holgura:      # ni la variedad de partida le da holgura: se queda la de partida
        u["variedad"] = umbrales(base=True)["variedad"]
    u["ocupacion"] = max(piso, math.floor(70 * min(r["ocupacion"] for r in medidas)) / 100.0)
    while u["ocupacion"] > piso and peor() < u["muestras_ok"] + holgura:
        u["ocupacion"] = max(piso, round(u["ocupacion"] - 0.01, 2))
    u["muestras_ok"] = min(0.9, max(u["muestras_ok"], math.floor(round(100 * (peor() - holgura), 6)) / 100.0))
    return u


def resumen(M3, m, R):
    """Una línea legible de la medida de un tramo (para `maqueta3d.py escena` y la vara)."""
    r = medir(M3, m, R)
    return ("ocupación %d %% (lleno %d %% del tramo) · variedad %d (variado %d %%) · vida %d %% · gente %d"
            % (round(100 * r["ocupacion"]), round(100 * r["lleno"]), r["variedad"], round(100 * r["variado"]), round(100 * r["vida"]), r["gente_max"])), r
