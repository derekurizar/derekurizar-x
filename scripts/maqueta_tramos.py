"""TRAMOS de la maqueta 3D: un video con varios mundos (usuario, 2026-11-15: «cuantos mundos sean necesarios»).

Un maqueta.json con `tramos` y `mundos` (en vez de un solo `mundo`) se parte en sub-maquetas de UN mundo, que el motor de
siempre sabe revisar y grabar (three.js o Blender). Cada tramo es una ventana de tiempo [desde, hasta) del video con su
mundo, su cámara, sus eventos, sus marcas y sus anotaciones (tiempos absolutos). Un mundo se puede repetir en varios
tramos (finca → mapa → puerto → mapa). La capa 2D (titulares, cifras, subtítulos, progreso, «Sígueme», cierre) es una
sola, continua, encima de todo: se graba en MODO PLACA sobre los tramos ya encadenados.

    {"version": 1, "estilo": "noche", "paleta": "cacao", "fps": 30, "duracion_s": 15,
     "mundos": {"finca": {"escala": "esquema", "receta": "campo", "piezas": […], "protagonista": "cosecha"},
                "pais":  {"escala": "pais", "set": "guatemala", "piezas": […]}},
     "tramos": [{"id": "finca", "mundo": "finca", "desde": 0, "hasta": 5, "camara": […], "eventos": […], "marcas": […]},
                {"mundo": "pais", "desde": 5, "hasta": 15, "transicion": "fundido", "fundido_s": 0.6, "camara": […]}],
     "capa": {…la de siempre…}}

- `transicion` (en el tramo que entra): `corte` (seco), `fundido` (las dos imágenes se cruzan) u `oscuro` (baja al
  oscuro y sube); `fundido_s` 0.3–0.8 s (0.5 por defecto). Para cruzar, cada tramo se graba con medio fundido de más a
  cada lado: el cruce queda centrado en el límite y el video dura exactamente `duracion_s`.
- `protagonista` por mundo (lo único en el acento EN ESE MUNDO); si un mundo no trae, vale el global si es una de sus piezas.
- `estilo` por mundo (usuario, 2026-11-16: «si hay cambios de escena deberíamos aceptar también cambios de tipo de estilo
  3D, mientras todo haga sentido»): sin él, el global. El estilo cambia solo con el mundo; la capa 2D es una sola (la
  del estilo del primer tramo).
- Los gates: M3D13 (la forma de los tramos) aquí; los M3D de siempre en cada sub-maqueta (M3D9, el gancho en el cuadro 0,
  solo en el primer tramo); M3D5 y M3D7 de la capa, una vez, sobre la capa global.

Lo usa scripts/maqueta3d.py (revisar_m, renderizar, cuadro, efectos_de) cuando el maqueta.json trae `tramos`.
"""
import copy
import json
import os
import re
import shutil
import subprocess

TRANSICIONES = {"corte": None, "fundido": "fade", "oscuro": "fadeblack"}   # → la transición de xfade de ffmpeg
FUNDIDO_DEF, FUNDIDO_MIN, FUNDIDO_MAX = 0.5, 0.3, 0.8
TRAMO_MIN = 2.5        # s: un tramo más corto no deja ver su mundo
CAMPOS_TRAMO = ("id", "mundo", "desde", "hasta", "transicion", "fundido_s", "camara", "eventos", "marcas", "anotaciones")


def es_tramos(m):
    return isinstance(m, dict) and "tramos" in m


def fundido(tr):
    return 0.0 if tr.get("transicion", "fundido") == "corte" else float(tr.get("fundido_s", FUNDIDO_DEF))


def forma(m):
    """M3D13 · la forma de los tramos. → lista de (gate, mensaje)."""
    out = []
    F = lambda msg: out.append(("M3D13", msg))
    mundos, T = m.get("mundos"), m.get("tramos")
    if "mundo" in m:
        F("con `tramos` los mundos van en `mundos` ({id: mundo}), no en `mundo`")
    if not isinstance(mundos, dict) or not mundos:
        F("`mundos` es un objeto {id: mundo} con al menos un mundo"); return out
    if not isinstance(T, list) or not T:
        F("`tramos` es una lista con al menos un tramo"); return out
    try:
        dur = float(m.get("duracion_s", 0))
    except (TypeError, ValueError):
        dur = 0.0
    usados = set()
    try:
        import maqueta3d as M3
        cat = M3.catalogo_estilos()
    except Exception:   # noqa: BLE001
        cat = {}
    for k, mu in mundos.items():
        if isinstance(mu, dict) and mu.get("estilo") is not None and cat and mu["estilo"] not in cat:
            F("el mundo «%s» pide el estilo «%s», que no está en design/sets3d/estilos.json (hay: %s)" % (k, mu["estilo"], ", ".join(cat)))
    for n, tr in enumerate(T):
        que = "tramo %d%s" % (n, " «%s»" % tr.get("id") if isinstance(tr, dict) and tr.get("id") else "")
        if not isinstance(tr, dict):
            F("%s: es un objeto {mundo, desde, hasta, camara, eventos, …}" % que); continue
        extra = [k for k in tr if k not in CAMPOS_TRAMO and not str(k).startswith("_")]
        if extra:
            F("%s: %s no %s campo de un tramo (hay: %s)" % (que, ", ".join("`%s`" % k for k in extra), "es" if len(extra) == 1 else "son", ", ".join(CAMPOS_TRAMO)))
        if tr.get("mundo") not in mundos:
            F("%s: el mundo «%s» no está en `mundos` (hay: %s)" % (que, tr.get("mundo"), ", ".join(mundos)))
        usados.add(tr.get("mundo"))
        tt = tr.get("transicion", "fundido")
        if tt not in TRANSICIONES:
            F("%s: `transicion` «%s» no existe (hay: %s)" % (que, tt, ", ".join(TRANSICIONES)))
        if tt != "corte" and not FUNDIDO_MIN <= float(tr.get("fundido_s", FUNDIDO_DEF)) <= FUNDIDO_MAX:
            F("%s: `fundido_s` va de %g a %g s" % (que, FUNDIDO_MIN, FUNDIDO_MAX))
        try:
            a, b = float(tr["desde"]), float(tr["hasta"])
        except (KeyError, TypeError, ValueError):
            F("%s: necesita `desde` y `hasta` (segundos del video)" % que); continue
        if n == 0 and abs(a) > 1e-6:
            F("%s: el primer tramo empieza en 0 (empieza en %.2f)" % (que, a))
        if n > 0 and isinstance(T[n - 1], dict) and abs(float(T[n - 1].get("hasta", -1)) - a) > 1e-3:
            F("%s: empieza en %.2f y el anterior termina en %.2f: los tramos van seguidos, sin hueco ni encime" % (que, a, float(T[n - 1].get("hasta", -1))))
        if b - a < TRAMO_MIN:
            F("%s: dura %.2f s y un tramo dura al menos %.1f s (que se vea su mundo): júntalo con el de al lado" % (que, b - a, TRAMO_MIN))
        if n == len(T) - 1 and abs(b - dur) > 1e-3:
            F("%s: el último tramo termina en %.2f y el video dura %.2f: los tramos cubren todo el video" % (que, b, dur))
        if n > 0 and fundido(tr) / 2 > min(b - a, float(T[n - 1].get("hasta", 0)) - float(T[n - 1].get("desde", 0))) / 2:
            F("%s: el fundido (%.1f s) es más largo que la mitad de uno de los dos tramos" % (que, fundido(tr)))
        # lo que vive en el tramo: dentro de su ventana
        for k in ("eventos", "marcas", "anotaciones"):
            for i, o in enumerate(tr.get(k) or []):
                t0 = float(o.get("t", -1))
                fin = t0 + float(o.get("dur", 0)) if k == "eventos" else float(o.get("hasta", t0))
                if not (a - 1e-6 <= t0 and fin <= b + 1e-6):
                    F("%s: %s %d (%s) va de %.2f a %.2f y el tramo de %.2f a %.2f: cada cosa vive dentro de su tramo"
                      % (que, k[:-1] if k != "anotaciones" else "anotación", i, o.get("tipo") or o.get("texto") or "", t0, fin, a, b))
        for i, k in enumerate(tr.get("camara") or []):
            if not a - 1e-6 <= float(k.get("t", -1)) <= b + 1e-6:
                F("%s: la clave de cámara %d (t = %.2f) cae fuera del tramo (%.2f–%.2f)" % (que, i, float(k.get("t", -1)), a, b))
        if not tr.get("camara"):
            F("%s: sin cámara (al menos una clave en `desde`)" % que)
    sobran = [k for k in mundos if k not in usados]
    if sobran:
        F("los mundos %s no se usan en ningún tramo: quítalos" % ", ".join("«%s»" % k for k in sobran))
    for k in ("camara", "eventos", "marcas", "anotaciones"):
        if m.get(k):
            F("con `tramos`, `%s` va dentro de cada tramo (no en el primer nivel)" % k)
    return out


def _corre(lista, off, campos=("t", "hasta")):
    out = []
    for o in lista or []:
        o = copy.deepcopy(o)
        for c in campos:
            if isinstance(o.get(c), (int, float)) and not isinstance(o.get(c), bool):
                o[c] = round(float(o[c]) - off, 4)
        if isinstance(o.get("mira"), dict) and isinstance(o["mira"].get("t"), (int, float)):
            o["mira"]["t"] = round(float(o["mira"]["t"]) - off, 4)
        out.append(o)
    return out


def _ventana(lista, a, b, off):
    """Lo de la capa que se cruza con [a, b), con sus tiempos locales y recortado a la ventana (para los gates del tramo)."""
    out = []
    for o in lista or []:
        t0, t1 = float(o.get("t", 0)), float(o.get("hasta", 0))
        if t1 > a and t0 < b:
            o = dict(o, t=round(max(t0, a) - off, 4), hasta=round(min(t1, b) - off, 4))
            out.append(o)
    return out


def partir(m):
    """→ [(info, sub)]: cada tramo como una maqueta de UN mundo, con tiempos locales (0 = inicio de lo que se graba del
    tramo: `desde` menos medio fundido de entrada). info: {n, id, mundo, desde, hasta, off, pre, post, dur, transicion, fundido}."""
    T, mundos, C = m["tramos"], m["mundos"], m.get("capa") or {}
    out = []
    for n, tr in enumerate(T):
        a, b = float(tr["desde"]), float(tr["hasta"])
        pre = fundido(tr) / 2 if n > 0 else 0.0
        post = fundido(T[n + 1]) / 2 if n + 1 < len(T) else 0.0
        off, dur = a - pre, (b - a) + pre + post
        mundo = copy.deepcopy(mundos[tr["mundo"]])
        prota = mundo.pop("protagonista", None)
        estilo = mundo.pop("estilo", None) or m.get("estilo")   # ESTILO POR MUNDO (usuario, 2026-11-16): cambia solo con el mundo
        ids = {p.get("id") for p in mundo.get("piezas") or []}
        if prota is None and m.get("protagonista") in ids:
            prota = m["protagonista"]
        for p in mundo.get("piezas") or []:            # lo que se mueve por claves (actor): sus `t` también son del video
            if isinstance(p.get("claves"), list):
                p["claves"] = _corre(p["claves"], off, ("t",))
        camara = _corre(tr.get("camara"), off, ("t",))
        if camara and camara[0].get("t", 0) > 1e-6:        # el tramo se graba desde `off`: la cámara ya está en su primera clave
            camara.insert(0, dict(camara[0], t=0.0))
        if camara and camara[0].get("t", 0) < 0:
            camara[0]["t"] = 0.0
        capa = {"titulares": _ventana(C.get("titulares"), off, off + dur, off), "cifras": _ventana(C.get("cifras"), off, off + dur, off)}
        for k in ("pie", "aviso", "handle"):
            if k == "pie" and (mundo.get("escala") or "pais") == "esquema":
                continue   # el pie nombra las fuentes de los geodatos: un esquema no usa ninguno, así que su tramo no lo lleva
            if C.get(k):
                capa[k] = C[k]
        sub = {"version": m.get("version", 1), "estilo": estilo, "paleta": m.get("paleta"), "fps": m.get("fps", 30),
               "duracion_s": round(dur, 4), "mundo": mundo, "camara": camara, "eventos": _corre(tr.get("eventos"), off, ("t",)),
               "marcas": _corre(tr.get("marcas"), off), "anotaciones": _corre(tr.get("anotaciones"), off), "capa": capa,
               "_tramo": {"n": n, "de": len(T), "id": tr.get("id") or tr["mundo"], "off": round(off, 4)}}
        if m.get("video"):
            sub["video"] = True   # un video de /video-3d: sus tramos de cerca pasan los gates de la escena viva (M3D15–M3D19)
        if prota:
            sub["protagonista"] = prota
        info = {"n": n, "id": tr.get("id") or "%s-%d" % (tr["mundo"], n + 1), "mundo": tr["mundo"], "desde": a, "hasta": b, "off": off,
                "pre": pre, "post": post, "dur": dur, "transicion": tr.get("transicion", "fundido") if n > 0 else None, "fundido": fundido(tr) if n > 0 else 0.0}
        out.append((info, sub))
    return out


def capa_global(m):
    """La maqueta de la capa: el mundo del primer tramo, quieto (una clave), sin eventos ni marcas, con la capa entera y la
    duración del video. Sirve para los gates de la capa (M3D5, M3D7) y para grabar la capa en MODO PLACA."""
    info, sub = partir(m)[0]
    cam = [dict(sub["camara"][0], t=0.0)] if sub["camara"] else []
    g = {"version": m.get("version", 1), "estilo": sub["estilo"], "paleta": m.get("paleta"), "fps": m.get("fps", 30),
         "duracion_s": m.get("duracion_s"), "mundo": sub["mundo"], "camara": cam, "eventos": [], "marcas": [], "anotaciones": [],
         "capa": copy.deepcopy(m.get("capa") or {}), "_capa_global": True}
    # el aviso «Esquema · no es un lugar real» solo mientras se ve un mundo esquema (no sobre el mapa real)
    g["capa"]["aviso_ventanas"] = [[tr["desde"], tr["hasta"]] for tr in m["tramos"] if (m["mundos"][tr["mundo"]] or {}).get("escala") == "esquema"]
    # y el pie (las fuentes de los geodatos) solo mientras se ve un mapa: un esquema no usa ninguno
    g["capa"]["pie_ventanas"] = [[tr["desde"], tr["hasta"]] for tr in m["tramos"] if ((m["mundos"][tr["mundo"]] or {}).get("escala") or "pais") != "esquema"]
    if sub.get("protagonista"):
        g["protagonista"] = sub["protagonista"]
    return g


def revisar_m(m, formatos, M3):
    """→ (fallas, avisos), como maqueta3d.revisar_m: M3D13, los gates de cada tramo y los de la capa global."""
    fallas = ["%s %s" % x for x in forma(m)]
    if fallas:
        return fallas, []
    avisos = []
    for info, sub in partir(m):
        f, a = M3.revisar_m(sub, formatos)
        pre = "[tramo %d «%s», %.1f–%.1f s del video; tiempos del tramo +%.2f] " % (info["n"] + 1, info["id"], info["desde"], info["hasta"], info["off"])
        fallas += [x.split(" ", 1)[0] + " " + pre + x.split(" ", 1)[1] if " " in x else x for x in f]
        avisos += [pre + x for x in a if not x.startswith("M3D10 pide") and not (info["n"] > 0 and "portada" in x)]
    f, a = M3.revisar_m(capa_global(m), formatos)
    fallas += [x.split(" ", 1)[0] + " [capa] " + x.split(" ", 1)[1] if " " in x else x for x in f]
    avisos += ["[capa] " + x for x in a if "sin `protagonista`" not in x]
    return fallas, list(dict.fromkeys(avisos))


def efectos(m):
    """[[t, sfx], …] de todos los tramos (tiempos del video) y de la capa."""
    C = m.get("capa") or {}
    lista = []
    for tr in m.get("tramos") or []:
        lista += [[e["t"], e["sfx"]] for e in tr.get("eventos") or [] if e.get("sfx")]
        lista += [[o["t"], o["sfx"]] for k in ("marcas", "anotaciones") for o in tr.get(k) or [] if o.get("sfx")]
    lista += [[o["t"], o["sfx"]] for k in ("titulares", "cifras") for o in C.get(k) or [] if o.get("sfx")]
    lista += [[C[k]["t"], C[k]["sfx"]] for k in ("seguir", "cierre") if (C.get(k) or {}).get("sfx")]
    return sorted([round(float(t), 3), s] for t, s in lista)


def _cuadros(ruta):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", ruta],
                       capture_output=True, text=True)
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        return -1


def encadenar(partes, fps, destino):
    """partes: [(mp4, info)] en orden → `destino` (H.264 casi sin pérdida, yuv420p): corte = uno tras otro; fundido u
    oscuro = xfade centrado en el límite (cada tramo trae medio fundido de más a cada lado)."""
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p, _ in partes:
        cmd += ["-i", p]
    # todas las entradas a la misma base de tiempo (AVTB): concat la cambia a 1/1000000 y xfade exige que sus dos
    # entradas coincidan, así que un corte seguido de un fundido fallaba con «Invalid argument» (-22)
    fc = ["[%d:v]settb=AVTB[s%d]" % (i, i) for i in range(len(partes))] if len(partes) > 1 else []
    cur, largo = "[s0]", partes[0][1]["dur"]
    for i in range(1, len(partes)):
        info = partes[i][1]
        sal = "[v%d]" % i
        tr = TRANSICIONES.get(info["transicion"])
        if tr:
            d = info["fundido"]
            fc.append("%s[s%d]xfade=transition=%s:duration=%.4f:offset=%.4f%s" % (cur, i, tr, d, largo - d, sal))
            largo += info["dur"] - d
        else:
            fc.append("%s[s%d]concat=n=2:v=1:a=0%s" % (cur, i, sal))
            largo += info["dur"]
        cur = sal
    if fc:
        cmd += ["-filter_complex", ";".join(fc) + ";%sfps=%s,format=yuv420p[out]" % (cur, fps), "-map", "[out]"]
    else:
        cmd += ["-vf", "fps=%s,format=yuv420p" % fps]
    cmd += ["-an", "-c:v", "libx264", "-preset", "medium", "-crf", "8", "-g", "10", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart", destino]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, " ".join(r.stderr.split())[-300:]


def renderizar(m, f, proy, final, registro, M3):
    """Un formato (o lienzo de pieza) de una maqueta con tramos: cada tramo con su motor → la placa encadenada → la capa
    2D en MODO PLACA encima → `final`. → 0 ok · 1 falla."""
    os.makedirs(proy, exist_ok=True)
    fps = int(m.get("fps", 30))
    partes = []
    for info, sub in partir(m):
        d = os.path.join(proy, "tramo-%02d-%s" % (info["n"] + 1, info["id"]))
        os.makedirs(d, exist_ok=True)
        mp4 = os.path.join(d, "video.mp4")
        print("tramo %d/%d «%s» (%s, %.1f s)…" % (info["n"] + 1, len(m["tramos"]), info["id"], info["mundo"], info["dur"]))
        if M3.renderizar(sub, f, os.path.join(d, "proyecto"), mp4, os.path.join(d, "render.log")):
            return 1
        partes.append((mp4, info))
    placa = os.path.join(proy, "placa.mp4")
    rc, err = encadenar(partes, fps, placa)
    espera = int(round(float(m["duracion_s"]) * fps))
    n = _cuadros(placa) if rc == 0 else -1
    if rc or abs(n - espera) > 1:
        print("FALLA tramos (%s): la placa encadenada tiene %d cuadros y se esperaban %d (ffmpeg %d: %s)" % (f, n, espera, rc, err)); return 1
    print("placa %s: %d tramos encadenados · %d cuadros" % (f, len(partes), n))
    return M3.renderizar(capa_global(m), f, os.path.join(proy, "capa"), final, registro, placa=placa)


def tramo_en(m, t):
    """(info, sub) del tramo que se ve en el segundo t del video (el último incluye el final)."""
    partes = partir(m)
    for info, sub in partes:
        if info["desde"] - 1e-6 <= t < info["hasta"]:
            return info, sub
    return partes[-1]


def cruce_en(partes, t):
    """Si en el segundo t se cruzan dos tramos (fundido u oscuro) → (transición, avance 0–1, tramo que sale, tramo que entra);
    si no, None. El cruce va centrado en el límite, como en `encadenar`."""
    for k in range(1, len(partes)):
        info = partes[k][0]
        d = info["fundido"]
        if TRANSICIONES.get(info["transicion"]) and d > 0 and abs(t - info["desde"]) < d / 2 - 1e-6:
            return info["transicion"], (t - (info["desde"] - d / 2)) / d, partes[k - 1], partes[k]
    return None


def mezclar(trans, p, a, b, destino):
    """El cuadro de un cruce, como lo deja xfade: fundido = mezcla de los dos; oscuro = el que sale se apaga y el que entra
    se enciende. → código de ffmpeg."""
    if trans == "oscuro":
        k, src = (1 - 2 * p, a) if p < 0.5 else (2 * p - 1, b)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "format=rgb24,lutrgb=r='val*%.4f':g='val*%.4f':b='val*%.4f'" % (k, k, k), destino]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", a, "-i", b, "-filter_complex",
               "[0]format=rgb24[a];[1]format=rgb24[b];[a][b]blend=all_expr='A*%.4f+B*%.4f'" % (1 - p, p), "-frames:v", "1", destino]
    return subprocess.run(cmd, capture_output=True, text=True).returncode


def cuadro(m, tiempos, formatos, salida, hoja, M3):
    """Cuadros sueltos de una maqueta con tramos: para cada t, el cuadro del mundo de su tramo (con sus marcas) y la capa
    global encima. → 0 ok · 1 falla."""
    import argparse
    fps = int(m.get("fps", 30))
    os.makedirs(salida, exist_ok=True)
    tmp = os.path.join(salida, "_tramos")
    partes = partir(m)
    for f in formatos:
        carpeta = M3.carpeta_de(f)
        por_tramo, cruces = {}, {}
        for t in tiempos:
            x = cruce_en(partes, t)        # en un fundido se ven los DOS mundos: se dibuja el cuadro de cada uno y se mezclan
            if x:
                cruces[t] = (x[0], x[1], x[2][0]["n"], x[3][0]["n"])
            for info, sub in ([x[2], x[3]] if x else [tramo_en(m, t)]):
                por_tramo.setdefault(info["n"], (info, sub, []))[2].append(t)
        fotos, de_tramo = {}, {}
        for n, (info, sub, ts) in sorted(por_tramo.items()):
            d = os.path.join(tmp, "tramo-%02d" % (n + 1))
            os.makedirs(d, exist_ok=True)
            ruta = os.path.join(d, "maqueta.json")
            with open(ruta, "w", encoding="utf-8") as fh:
                json.dump(sub, fh, ensure_ascii=False)
            locales = [round(t - info["off"], 3) for t in ts]
            ns = argparse.Namespace(maqueta=ruta, t=locales, salida=d, formato=f if f in M3.ZONAS else "9:16", hoja=False,
                                    pieza=not f in M3.ZONAS, lienzo=None if f in M3.ZONAS else f.replace(":", "x"), cmd="cuadro")
            if M3.cmd_cuadro(ns):
                return 1
            for t, tl in zip(ts, locales):
                de_tramo[(n, t)] = os.path.join(d, "%s_t%07.3f.png" % (carpeta, tl))
                if t not in cruces:
                    fotos[int(round(t * fps))] = de_tramo[(n, t)]
        for t, (trans, avance, na, nb) in cruces.items():
            mez = os.path.join(tmp, "cruce_%s_t%07.3f.png" % (carpeta, t))
            if mezclar(trans, avance, de_tramo[(na, t)], de_tramo[(nb, t)], mez):
                print("FALLA cuadro %s (tramos): no se pudo mezclar el cruce de %.2f s" % (f, t)); return 1
            fotos[int(round(t * fps))] = mez
        # la capa global en MODO PLACA, con cada cuadro del mundo como foto de la placa
        proy = os.path.join(tmp, "capa", carpeta)
        os.makedirs(proy, exist_ok=True)
        M3.escribir_proyecto(capa_global(m), f, proy, sorted(fotos), placa_externa=True)
        for nq, png in fotos.items():
            shutil.copyfile(png, os.path.join(proy, "assets", "placa", "c_%05d.png" % nq))
        snap = os.path.abspath(os.path.join(proy, "_cuadros"))
        shutil.rmtree(snap, ignore_errors=True)
        p, seg = M3.correr(M3.HF + ["snapshot", "--at", ",".join("%g" % t for t in tiempos), "--no-end", "--keep", "--browser-gpu", "--timeout", "120000", "-o", snap],
                           proy, os.path.join(proy, "cuadro.log"))
        pngs = sorted((x for x in os.listdir(snap) if x.endswith(".png")), key=lambda x: float(re.sub(r"[^0-9.]", "", x.rsplit("s.", 1)[0]) or 0)) if os.path.isdir(snap) else []
        if p.returncode != 0 or len(pngs) != len(tiempos):
            print("FALLA cuadro %s (tramos): hyperframes snapshot devolvió %d y %d de %d cuadros (ver %s)" % (f, p.returncode, len(pngs), len(tiempos), os.path.join(proy, "cuadro.log")))
            return 1
        salidas = []
        for t, png in zip(sorted(tiempos), pngs):
            dst = os.path.join(salida, "%s_t%07.3f.png" % (carpeta, t))
            shutil.move(os.path.join(snap, png), dst); salidas.append(dst)
        print("cuadros %s (tramos, %.1f s): %s" % (f, seg, " ".join(salidas)))
        if hoja:
            h = os.path.join(salida, "hoja_%s.jpg" % carpeta)
            M3.hoja_de(salidas, h, 360 if len(salidas) > 3 else 540)
            print("hoja %s: %s  (en orden: %s s)" % (f, h, ", ".join("%g" % t for t in sorted(tiempos))))
    return 0
