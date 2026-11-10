#!/usr/bin/env python3
"""Métricas reales de las piezas publicadas (/analyze-improve): registro, vínculo, alineación y diagnóstico. Solo stdlib.

La captura la hace la sesión con Claude in Chrome (referencias/analisis/captura.md) y deja un JSON por plataforma:
  {plataforma: tiktok|youtube|instagram|facebook, fecha: AAAA-MM-DD, publicaciones: [{post_id, url, titulo, fecha_pub
   (AAAA-MM-DD[THH:MM]), duracion_s, views, likes, comments, shares, saves, follows, avg_s, completion (0–1),
   viewed_pct (0–1, YouTube «se quedaron viendo»), views_3s, views_1m, distribucion (Facebook, ×), trafico {fuente: 0–1},
   curva [retención por segundo 0–1, curva[0] = 1]}]}

Subcomandos:
  importar CAPTURA… [--dry-run]   normaliza y funde en memoria/metricas.json → publicaciones[] {id (= <plataforma>-<post_id>),
                                  plataforma, post_id, url, titulo, fecha_pub, duracion_s, pieza {flujo, id, slug} | null,
                                  vinculo auto|manual|pendiente|ajena, curva (la última), snapshots[] {fecha, views, likes,
                                  comments, shares, saves, follows, avg_s, completion, viewed_pct, views_3s, views_1m,
                                  distribucion, trafico, hold {1,2,3,5,10,15,30,60}}}; la misma fecha reemplaza su snapshot.
                                  Solo este script escribe memoria/metricas.json.
  vincular [--fijar PUB FLUJO:ID] [--ajena PUB] [--dry-run]
                                  liga cada publicación a una pieza de los registros (videos, historias, noticias, sabias,
                                  explicaciones, semanas) por fecha (−1…+6 días), duración (±6 s) y palabras del título; lo
                                  anterior al primer registro queda «ajena»; lo dudoso, «pendiente» (la sesión lo fija).
  alinear PIEZA [--plataforma P] [--json]
                                  cruza la curva con las escenas (inicio = Σ(dur − transición) de escenas.json de la sesión o
                                  del guion.json entregado): retención al entrar y salir de cada escena y puntos perdidos por
                                  segundo. PIEZA = slug, id o «flujo:id».
  diagnostico [--desde F] [--mejoras SALIDA] [--json]
                                  detectores AN1–AN12 (abajo) sobre las piezas vinculadas; --mejoras escribe el borrador
                                  {flujo: analisis, pieza, mejoras[]} para memoria.py --mejoras (la sesión lo edita antes).
  rendimiento [--por familia|visual|cierre|animacion|flujo|estilo_fb] [--md]
                                  mediana del hold a 3 s y del tiempo medio (TikTok, y YouTube «visto») por categoría;
                                  video.py, historia.py y explica.py leen lineas_rendimiento() para el digesto.
  --check                         M17: el esquema de memoria/metricas.json (también lo corre validate.py).

Detectores (cada uno nombra el archivo del framework que implica):
  AN1 hold a 3 s bajo la línea base del canal (gancho)           AN7 título publicado con palabras que no están en
  AN2 más de 25 % se va en el primer segundo (cuadro 0)              caption.md ni en el guion (erratas, caption a mano)
  AN3 la escena de la promesa pierde > 1.5× la mediana           AN8 familia de gancho con hold < 0.8× la mediana
  AN4 una escena pierde > 2× la mediana del video (ritmo,        AN9 cuántos llegan al cierre y seguidores por 1,000 vistas
      animación o tarjeta)                                        AN10 tiempo medio / duración muy distinto entre plataformas
  AN5 completado bajo para su duración (largo)                   AN11 tipo de tema (historia con protagonista vs. datos)
  AN6 plataforma con < 5 % de las vistas de la mediana de la     AN12 hora de publicación (solo con ≥ 10 por franja)
  AN13 compartidos por 1,000 vistas bajo la mitad de la mediana  AN14 Shorts: «se quedaron viendo» bajo 60 %
      pieza (restricción, reclamo o subida fallida)
Las referencias de la web viven en referencias/analisis/benchmarks.md; aquí solo la línea base del propio canal.

Exit: 0 ok · 1 falla (gate o pieza sin datos) · 2 uso incorrecto.
"""
import argparse
import datetime
import difflib
import glob
import json
import os
import re
import statistics
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICAS = os.path.join(RAIZ, "memoria", "metricas.json")
VACIO = {"version": 1, "_comentario": "Métricas de las piezas publicadas; lo escribe solo scripts/metricas.py (/analyze-improve).",
         "publicaciones": []}
PLATAFORMAS = ("tiktok", "youtube", "instagram", "facebook")
VINCULOS = ("auto", "manual", "pendiente", "ajena")
CAMPOS_NUM = ("views", "likes", "comments", "shares", "saves", "follows", "avg_s", "completion", "viewed_pct",
              "views_3s", "views_1m", "distribucion")
HOLD_S = (1, 2, 3, 5, 10, 15, 30, 60)
TRANSICION = 0.3   # = video.TRANSICION (sin importar video.py: este script no depende del motor de video)
# registro → (archivo, clave de la lista, flujo, campo de la ruta)
REGISTROS = (("videos.json", "videos", "video", "ruta_video"), ("historias.json", "historias", "historia", "ruta"),
             ("noticias.json", "noticieros", "noticias", "ruta"), ("sabias.json", "sabias", "sabias", "ruta"),
             ("explicaciones.json", "explicaciones", "explica", "ruta"), ("semanas.json", "semanas", "semana", "ruta"),
             ("congreso.json", "congreso", "congreso", "ruta"))
VENTANA_DIAS = (-1, 6)       # publicada entre un día antes y seis después del registro
TOLERANCIA_DUR = 6.0         # s entre la duración publicada y la del registro
UMBRAL_AUTO, MARGEN_AUTO = 2.0, 1.0   # puntaje mínimo para vincular solo y ventaja sobre el segundo candidato
STOP = set("de del la el los las en y a o que un una al lo se es su sus por para con como mas hoy datos dato video "
           "guatemala guatemalteco guatemalteca gt shorts fue era".split())
# archivos del framework por área (lo que cada detector implica)
ARCHIVO = {"gancho": "referencias/ganchos.md", "cuadro0": "referencias/ganchos.md", "promesa": "referencias/promesas.md",
           "ritmo": "referencias/flujo-video.md", "duracion": "referencias/flujo-video.md",
           "publicacion": "referencias/analisis/publicacion.md", "caption": "referencias/flujo-video.md",
           "cierre": "referencias/cierres.md", "tema": "referencias/roles/explorador.md",
           "horario": "referencias/analisis/publicacion.md", "envios": "referencias/cierres.md"}
ARCHIVO_ESCENA = {"tarjeta": "video/escena.html", "foto": "video/noticia.html", "cita": "video/historia.html",
                  "capitulo": "video/historia.html", "golpe": "video/golpe.html", "definicion": "video/golpe.html",
                  "adivina": "video/golpe.html", "mapa": "video/mapa.html", "ranking": "video/ranking.html",
                  "escala": "video/escala.html", "tiempo": "video/tiempo.html", "cuenta": "video/cuenta.html",
                  "noticia": "video/noticia.html", "cierre": "video/cierre.html", "gancho": "video/gancho.html"}
ENVIOS_MIN_VISTAS, ENVIOS_MIN_PIEZAS = 300, 4   # AN13: una pieza con pocas vistas no dice nada; hace falta una base
VISTO_MIN = 0.60                              # AN14
TASA_MINIMA = 0.3   # %/s: piso de la mediana de pérdida por escena (con curvas planas, la mediana ≈ 0 inflaba las razones)
FALLAS = []


def falla(m):
    FALLAS.append(m)


def leer(ruta, defecto=None):
    if not os.path.exists(ruta):
        return defecto
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def rel(p):
    return os.path.relpath(p, RAIZ)


def plano(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def palabras(t):
    return {w for w in re.findall(r"[a-z0-9ñ]+", plano(t)) if len(w) >= 3 and w not in STOP}


def fecha_de(t):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(t or ""))
    return datetime.date.fromisoformat(m.group(1)) if m else None


def hora_de(t):
    m = re.search(r"T(\d{2}):(\d{2})", str(t or ""))
    return int(m.group(1)) if m else None


def num(v):
    """«3,184» · «39K» · «1.3 mil» · «28.282» (miles con punto) · 0.079 → float o None."""
    if v is None or v == "" or v == "--":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace(" ", "").replace(" ", "")
    mult = 1.0
    for suf, m in (("mil", 1e3), ("k", 1e3), ("m", 1e6)):
        if s.endswith(suf):
            s, mult = s[:-len(suf)], m
            break
    if s.endswith("%"):
        s, mult = s[:-1], mult / 100
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    else:
        s = s.replace(",", ".")
    try:
        return float(s) * mult
    except ValueError:
        return None


def hold_de(curva):
    return {str(s): round(curva[s], 4) for s in HOLD_S if curva and s < len(curva)}


# ---------- registro ----------
def cargar():
    return leer(METRICAS) or json.loads(json.dumps(VACIO))


def normalizar(p, plataforma):
    """Una publicación de la captura → (campos fijos, snapshot)."""
    curva = [round(float(x), 4) for x in (p.get("curva") or []) if x is not None]
    snap = {k: num(p.get(k)) for k in CAMPOS_NUM if p.get(k) not in (None, "")}
    for k in ("completion", "viewed_pct"):   # aceptan 7.9 (porcentaje) o 0.079
        if snap.get(k) is not None and snap[k] > 1:
            snap[k] = round(snap[k] / 100, 4)
    if p.get("trafico"):
        snap["trafico"] = {k: (num(v) / 100 if (num(v) or 0) > 1 else num(v)) for k, v in p["trafico"].items()}
    if curva:
        snap["hold"] = hold_de(curva)
    fijos = {"plataforma": plataforma, "post_id": str(p.get("post_id") or "").strip(), "url": p.get("url") or "",
             "titulo": (p.get("titulo") or "").strip(), "fecha_pub": p.get("fecha_pub") or "",
             "duracion_s": num(p.get("duracion_s"))}
    return fijos, snap, curva


def cmd_importar(a):
    M = cargar()
    por_id = {x["id"]: x for x in M["publicaciones"]}
    n_new = n_upd = 0
    for ruta in a.capturas:
        cap = leer(ruta)
        if not isinstance(cap, dict) or cap.get("plataforma") not in PLATAFORMAS or not isinstance(cap.get("publicaciones"), list):
            print("ERROR: %s no es una captura {plataforma: %s, fecha, publicaciones[]}" % (ruta, "|".join(PLATAFORMAS)), file=sys.stderr)
            return 2
        fecha = cap.get("fecha") or datetime.date.today().isoformat()
        for p in cap["publicaciones"]:
            fijos, snap, curva = normalizar(p, cap["plataforma"])
            if not fijos["post_id"]:
                print("AVISO: publicación sin post_id en %s: %s" % (ruta, fijos["titulo"][:50]))
                continue
            pid = "%s-%s" % (cap["plataforma"], fijos["post_id"])
            snap = {"fecha": fecha, **snap}
            if pid in por_id:
                x = por_id[pid]
                for k, v in fijos.items():
                    if v not in (None, ""):
                        x[k] = v
                x["snapshots"] = [s for s in x["snapshots"] if s.get("fecha") != fecha] + [snap]
                x["snapshots"].sort(key=lambda s: s["fecha"])
                if curva:
                    x["curva"] = curva
                n_upd += 1
            else:
                x = {"id": pid, **fijos, "pieza": None, "vinculo": "pendiente", "curva": curva, "snapshots": [snap]}
                M["publicaciones"].append(x)
                por_id[pid] = x
                n_new += 1
    M["publicaciones"].sort(key=lambda x: (x["plataforma"], x.get("fecha_pub") or "", x["id"]))
    print("[importar] %d nuevas · %d actualizadas · %d en total" % (n_new, n_upd, len(M["publicaciones"])))
    if a.dry_run:
        print("[dry-run] no se escribió nada")
        return 0
    escribir(METRICAS, M)
    print("escrito %s" % rel(METRICAS))
    return 0


# ---------- piezas de los registros ----------
def piezas():
    """Todas las piezas de video registradas → [{flujo, id, slug, fecha, tema, duracion_s, ruta, frases, reg}]."""
    out = []
    for archivo, clave, flujo, campo in REGISTROS:
        d = leer(os.path.join(RAIZ, "memoria", archivo)) or {}
        for v in d.get(clave, []):
            out.append({"flujo": flujo, "id": v.get("id"), "slug": v.get("slug") or v.get("id"), "fecha": v.get("fecha"),
                        "tema": v.get("tema") or "", "duracion_s": v.get("duracion_s"), "ruta": v.get(campo),
                        "frases": v.get("frases") or {}, "reg": v})
    return out


def pieza_por(clave, ps=None):
    ps = ps if ps is not None else piezas()
    if ":" in clave:
        fl, i = clave.split(":", 1)
        return next((p for p in ps if p["flujo"] == fl and p["id"] == i), None)
    return next((p for p in ps if clave in (p["id"], p["slug"])), None)


def puntaje(pub, p):
    fp, fr = fecha_de(pub.get("fecha_pub")), fecha_de(p.get("fecha"))
    if not fp or not fr:
        return -1
    dias = (fp - fr).days
    if not VENTANA_DIAS[0] <= dias <= VENTANA_DIAS[1]:
        return -1
    s = 1.0 - 0.4 * abs(dias)
    if pub.get("duracion_s") and p.get("duracion_s"):
        dd = abs(pub["duracion_s"] - p["duracion_s"])
        s += 2.0 if dd <= 2.5 else 1.0 if dd <= TOLERANCIA_DUR else -2.0
    comunes = palabras(pub.get("titulo")) & (palabras(p["slug"]) | palabras(p["tema"]))
    s += 1.5 * len(comunes)
    if p["flujo"] == "noticias":   # un noticiero se publica el mismo día que su fecha (su id)
        es_noticia = bool(re.search(r"noticia", plano(pub.get("titulo"))))
        s += (3.0 if dias == 0 else -3.0) if es_noticia else -2.0
    return s


def cmd_vincular(a):
    M = cargar()
    ps = piezas()
    por_id = {x["id"]: x for x in M["publicaciones"]}
    if a.fijar:
        pub, clave = a.fijar
        p = pieza_por(clave, ps)
        if pub not in por_id or not p:
            print("ERROR: --fijar: publicación %r o pieza %r desconocida" % (pub, clave), file=sys.stderr)
            return 2
        por_id[pub].update(pieza={"flujo": p["flujo"], "id": p["id"], "slug": p["slug"]}, vinculo="manual")
        print("%s → %s:%s (manual)" % (pub, p["flujo"], p["id"]))
    elif a.ajena:
        if a.ajena not in por_id:
            print("ERROR: --ajena: publicación %r desconocida" % a.ajena, file=sys.stderr)
            return 2
        por_id[a.ajena].update(pieza=None, vinculo="ajena")
        print("%s → ajena" % a.ajena)
    else:
        primera = min((fecha_de(p["fecha"]) for p in ps if fecha_de(p["fecha"])), default=None)
        for x in M["publicaciones"]:
            if x.get("vinculo") in ("manual", "ajena"):
                continue
            fp = fecha_de(x.get("fecha_pub"))
            if primera and fp and fp < primera - datetime.timedelta(days=1):
                x.update(pieza=None, vinculo="ajena")
                continue
            orden = sorted(((puntaje(x, p), p) for p in ps), key=lambda t: -t[0])
            mejor = orden[0] if orden else (-1, None)
            seg = orden[1][0] if len(orden) > 1 else -1
            if mejor[0] >= UMBRAL_AUTO and mejor[0] - seg >= MARGEN_AUTO:
                p = mejor[1]
                x.update(pieza={"flujo": p["flujo"], "id": p["id"], "slug": p["slug"]}, vinculo="auto")
            else:
                cand = ["%s:%s (%.1f)" % (p["flujo"], p["id"], s) for s, p in orden[:3] if s >= 0]
                x.update(pieza=None, vinculo="pendiente", candidatos=cand)
    n = {v: sum(1 for x in M["publicaciones"] if x.get("vinculo") == v) for v in VINCULOS}
    for x in M["publicaciones"]:
        if x.get("vinculo") == "pendiente":
            print("PENDIENTE %s · %s · %s · %s → %s" % (x["id"], (x.get("fecha_pub") or "")[:10], x.get("duracion_s"),
                                                       x["titulo"][:50], ", ".join(x.get("candidatos") or []) or "sin candidatos"))
        else:
            x.pop("candidatos", None)
    print("[vincular] " + " · ".join("%s %d" % kv for kv in n.items()))
    if a.dry_run:
        print("[dry-run] no se escribió nada")
        return 0
    escribir(METRICAS, M)
    return 0


# ---------- alineación ----------
def escenas_de(p):
    """[{n, tipo, t0, t1, pantalla, voz, animacion, mecanismo}] de la pieza: escenas.json de la sesión si existe (tiempos
    medidos), si no el guion.json entregado (dur estimada)."""
    reg = p["reg"]
    cand = []
    if p["flujo"] == "video":
        cand.append("sesiones/%s/video/escenas.json" % p["slug"])
    elif p["flujo"] == "historia":
        cand.append("sesiones/historia-%s/escenas.json" % p["slug"])
    elif p["flujo"] == "noticias":
        cand.append("sesiones/noticias-%s/escenas.json" % p["id"])
    elif p["flujo"] == "sabias":
        cand.append("sesiones/%s/sabias/escenas.json" % p["slug"])
    elif p["flujo"] == "congreso":
        cand.append("sesiones/congreso-%s/escenas.json" % p["slug"])
    elif p["flujo"] == "explica":
        cand += ["sesiones/explica-%s/escenas.json" % p["slug"], "sesiones/mito-%s/escenas.json" % p["slug"]]
    elif p["flujo"] == "semana":
        cand.append("sesiones/semana-%s/escenas.json" % reg.get("fecha"))
    guion = leer(os.path.join(RAIZ, p["ruta"] or "", "guion.json")) or {}
    por_n = {int(e.get("n") or k): e for k, e in enumerate(guion.get("escenas") or [], 1)}
    fuente = next((c for c in cand if os.path.exists(os.path.join(RAIZ, c))), None)
    base = (leer(os.path.join(RAIZ, fuente)) or {}).get("escenas") if fuente else None
    trans = TRANSICION
    if fuente:
        trans = (leer(os.path.join(RAIZ, fuente)) or {}).get("transicion_s") or TRANSICION
    filas = base or guion.get("escenas") or []
    out, t = [], 0.0
    for k, e in enumerate(filas, 1):
        n = int(e.get("n") or k)
        g = por_n.get(n, {})
        dur = float(e.get("dur") or g.get("dur") or 0)
        out.append({"n": n, "tipo": e.get("tipo") or g.get("tipo"), "t0": round(t, 2), "t1": round(t + dur, 2),
                    "pantalla": str(g.get("pantalla") or (g.get("titular") if isinstance(g.get("titular"), str) else "") or "")[:60],
                    "voz": re.sub(r"\s+", " ", str(g.get("voz") or g.get("texto") or ""))[:90],
                    "animacion": g.get("animacion"), "mecanismo": g.get("mecanismo")})
        t += max(dur - trans, 0)
    return out, (fuente or (p["ruta"] + "/guion.json" if p["ruta"] else None)), guion


def ret(curva, t):
    if not curva:
        return None
    if t <= 0:
        return curva[0]
    i = int(t)
    if i + 1 >= len(curva):
        return curva[-1] if t < len(curva) + 1 else None
    return curva[i] + (curva[i + 1] - curva[i]) * (t - i)


def alinear(p, curva):
    esc, fuente, guion = escenas_de(p)
    filas = []
    for e in esc:
        r0, r1 = ret(curva, e["t0"]), ret(curva, e["t1"])
        if r0 is None or r1 is None:
            break
        d = max(e["t1"] - e["t0"], 0.5)
        # tasa = % de quienes seguían viendo al entrar que se van por segundo (la curva siempre cae más al principio:
        # en puntos absolutos todas las escenas tempranas parecen malas)
        filas.append(dict(e, r0=round(r0, 3), r1=round(r1, 3), perdida=round((r0 - r1) * 100, 1),
                          tasa=round((r0 - r1) / max(r0, 0.01) * 100 / d, 2)))
    return filas, fuente, guion


def pubs_de(M, p, plataforma=None):
    return [x for x in M["publicaciones"] if (x.get("pieza") or {}).get("id") == p["id"]
            and (x.get("pieza") or {}).get("flujo") == p["flujo"] and (not plataforma or x["plataforma"] == plataforma)]


def ultimo(x):
    return (x.get("snapshots") or [{}])[-1]


def cmd_alinear(a):
    M = cargar()
    p = pieza_por(a.pieza)
    if not p:
        print("ERROR: pieza %r no está en los registros de memoria/" % a.pieza, file=sys.stderr)
        return 2
    pubs = [x for x in pubs_de(M, p, a.plataforma) if x.get("curva")]
    if not pubs:
        print("ERROR: %s:%s no tiene una publicación vinculada con curva de retención%s" % (
            p["flujo"], p["id"], " en %s" % a.plataforma if a.plataforma else ""), file=sys.stderr)
        return 1
    pub = max(pubs, key=lambda x: ultimo(x).get("views") or 0)
    filas, fuente, _ = alinear(p, pub["curva"])
    if a.json:
        print(json.dumps({"pieza": p["id"], "publicacion": pub["id"], "fuente": fuente, "escenas": filas}, ensure_ascii=False, indent=2))
        return 0
    print("%s:%s · %s · %s vistas · escenas de %s" % (p["flujo"], p["id"], pub["id"], int(ultimo(pub).get("views") or 0), fuente))
    tasas = [f["tasa"] for f in filas[1:]] or [0]
    med = statistics.median(tasas)
    for f in filas:
        marca = "  ◀ %.1f× la mediana" % (f["tasa"] / med) if med > 0 and f["n"] > 1 and f["tasa"] > 2 * med else ""
        print("%2d %-9s %6.1f–%6.1f s  %3.0f%% → %3.0f%%  −%4.1f pts (se va %4.2f%%/s)  «%s»%s" % (
            f["n"], f["tipo"], f["t0"], f["t1"], f["r0"] * 100, f["r1"] * 100, f["perdida"], f["tasa"],
            f["pantalla"] or f["voz"][:40], marca))
    return 0


# ---------- diagnóstico ----------
def mediana(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def caption_de(p):
    ruta = os.path.join(RAIZ, p["ruta"] or "", "caption.md")
    return open(ruta, encoding="utf-8").read() if p["ruta"] and os.path.exists(ruta) else ""


def textos_guion(guion):
    return " ".join(str(e.get(k) or "") for e in (guion.get("escenas") or []) for k in ("voz", "texto", "pantalla", "linea"))


def resumen_piezas(M, desde=None):
    """{(flujo, id): {p, pubs {plataforma: pub}, tk (snapshot TikTok), ...}} de las piezas vinculadas."""
    out = {}
    ps = {(p["flujo"], p["id"]): p for p in piezas()}
    for x in M["publicaciones"]:
        pz = x.get("pieza")
        if not pz or (pz["flujo"], pz["id"]) not in ps:
            continue
        if desde and (x.get("fecha_pub") or "") < desde:
            continue
        r = out.setdefault((pz["flujo"], pz["id"]), {"p": ps[(pz["flujo"], pz["id"])], "pubs": {}})
        prev = r["pubs"].get(x["plataforma"])
        if not prev or (ultimo(x).get("views") or 0) > (ultimo(prev).get("views") or 0):
            r["pubs"][x["plataforma"]] = x
    return out


def hallazgo(codigo, area, pieza, evidencia, archivo=None, propuesta=""):
    return {"codigo": codigo, "area": area, "pieza": pieza, "evidencia": evidencia,
            "archivo": archivo or ARCHIVO.get(area, "referencias/analisis/publicacion.md"), "propuesta": propuesta}


def diagnosticar(M, desde=None):
    R = resumen_piezas(M, desde)
    H = []
    tk = {k: r["pubs"]["tiktok"] for k, r in R.items() if "tiktok" in r["pubs"]}
    holds = {k: (ultimo(x).get("hold") or {}) for k, x in tk.items()}
    base3 = mediana([h.get("3") for h in holds.values()])
    base1 = mediana([h.get("1") for h in holds.values()])
    n_plat = {pl: sum(1 for r in R.values() if pl in r["pubs"]) for pl in PLATAFORMAS}
    med_plat = {pl: mediana([ultimo(r["pubs"][pl]).get("views") for r in R.values() if pl in r["pubs"]]) for pl in PLATAFORMAS}
    for k, r in sorted(R.items(), key=lambda kv: kv[1]["p"].get("fecha") or ""):
        p, pid = r["p"], "%s:%s" % k
        x = r["pubs"].get("tiktok")
        h = holds.get(k) or {}
        s = ultimo(x) if x else {}
        gan = (p["frases"].get("gancho") or "")[:70]
        # AN1 gancho
        if base3 and h.get("3") is not None and h["3"] < min(0.6, base3):
            H.append(hallazgo("AN1", "gancho", pid, "hold 3 s %.0f%% (mediana del canal %.0f%%) · gancho «%s» · familia %s" % (
                h["3"] * 100, base3 * 100, gan, p["frases"].get("familia") or "—"),
                propuesta="Gancho con sujeto reconocible + vacío de curiosidad; nunca solo la cifra ni una fórmula genérica (R14)."))
        # AN2 cuadro 0
        if h.get("1") is not None and h["1"] < 0.75:
            H.append(hallazgo("AN2", "cuadro0", pid, "se va el %.0f%% en el primer segundo (mediana del canal %.0f%%)" % (
                (1 - h["1"]) * 100, (1 - (base1 or 0)) * 100),
                propuesta="Cuadro 0 con imagen reconocible (foto u objeto) y movimiento; la cifra sola sobre fondo oscuro no frena."))
        filas, fuente, guion = alinear(p, x["curva"]) if x and x.get("curva") else ([], None, {})
        if len(filas) >= 3:
            tasas = [f["tasa"] for f in filas[1:] if f["r0"] >= 0.05]   # el final plano (casi nadie) no cuenta
            med = max(statistics.median(tasas) if tasas else 0, TASA_MINIMA)
            prom_n = ((guion.get("promesa") or {}).get("en"))
            prom_n = prom_n if isinstance(prom_n, int) else 2
            for f in filas[1:]:
                if f["n"] == prom_n and f["tasa"] > 1.5 * med and f["perdida"] >= 5:
                    H.append(hallazgo("AN3", "promesa", pid, "la escena %d (promesa, %s) pierde %.1f pts en %.1f s: se va el %.1f%%/s de quien seguía (%.1f× la mediana)" % (
                        f["n"], f["tipo"], f["perdida"], f["t1"] - f["t0"], f["tasa"], f["tasa"] / med),
                        propuesta="Pagar una micro-respuesta antes de 8 s; la promesa no puede ser una escena quieta."))
                elif f["n"] > 2 and f["tasa"] > 2 * med and f["perdida"] >= 2 and f["r0"] >= 0.03:
                    arch = ("video/animaciones/%s.js" % f["animacion"]) if f.get("animacion") else ARCHIVO_ESCENA.get(f["tipo"], ARCHIVO["ritmo"])
                    if f["tipo"] == "cierre":
                        arch = ARCHIVO["cierre"]
                    H.append(hallazgo("AN4", "cierre" if f["tipo"] == "cierre" else "ritmo", pid, "escena %d (%s%s) %.1f–%.1f s: se va el %.2f%%/s de quien seguía (%.1f× la mediana) · «%s»" % (
                        f["n"], f["tipo"], ", " + f["animacion"] if f.get("animacion") else "", f["t0"], f["t1"], f["tasa"],
                        f["tasa"] / med, f["pantalla"] or f["voz"][:50]), archivo=arch,
                        propuesta=("El cierre se nota: la gente se va al reconocer el final. Que la última escena abra o pague "
                                   "algo (no resuma) y vuelva al gancho en bucle." if f["tipo"] == "cierre" else
                                   "Revisar la escena: duración, movimiento, si repite lo anterior o si su texto se lee.")))
            # AN9 cierre
            cie = next((f for f in filas if f["tipo"] == "cierre"), None)
            if cie and s.get("views"):
                H.append(hallazgo("AN9", "cierre", pid, "llega al cierre el %.0f%% · %.1f seguidores por 1,000 vistas" % (
                    cie["r0"] * 100, 1000 * (s.get("follows") or 0) / s["views"]), propuesta=""))
        # AN5 completado
        dur = (x or {}).get("duracion_s") or p.get("duracion_s")
        if s.get("completion") is not None and dur and dur > 90 and s["completion"] < 0.1:
            H.append(hallazgo("AN5", "duracion", pid, "completado %.1f%% en %.0f s (tiempo medio %.0f s)" % (
                s["completion"] * 100, dur, s.get("avg_s") or 0),
                propuesta="Probar un corte de 60–90 s para TikTok/Facebook/Reels y dejar el largo en YouTube."))
        # AN6 restricción: la pieza casi no se vio en una plataforma donde las demás piezas sí se ven
        for pl, pb in r["pubs"].items():
            v = ultimo(pb).get("views")
            med_pl = med_plat.get(pl)
            edad = (datetime.date.today() - (fecha_de(pb.get("fecha_pub")) or datetime.date.today())).days
            otras = mediana([ultimo(o).get("views") for q, o in r["pubs"].items() if q != pl])
            # con pocas piezas la mediana de la plataforma engaña: además, la pieza sí se vio en sus otras plataformas
            if (v is not None and med_pl and med_pl >= 100 and v < 0.05 * med_pl and edad >= 2
                    and (n_plat.get(pl, 0) >= 5 or (otras and v < 0.05 * otras))):
                H.append(hallazgo("AN6", "publicacion", pid, "%s: %d vistas frente a una mediana de %d de las piezas en %s" % (
                    pl, v, med_pl, pl), propuesta="Revisar en %s si está restringido (edad, alcohol, reclamo de música), si falta "
                                                   "una pregunta obligatoria (YouTube: «hecho para niños») o si la subida falló." % pl))
        # AN7 caption: ¿se usó caption.md? ¿hay erratas?
        cap = caption_de(p)
        if cap:
            g_ = guion or (leer(os.path.join(RAIZ, p["ruta"], "guion.json")) or {})
            conocido = palabras(cap) | palabras(textos_guion(g_)) | palabras(p["tema"]) | palabras(p["slug"])
            lineas_cap = [plano(l) for l in cap.splitlines() if len(l.strip()) > 20]
            a_mano, erratas = [], []
            for pl, pb in sorted(r["pubs"].items()):
                tit = re.sub(r"#\S+", " ", pb.get("titulo") or "").strip()
                if not tit:
                    continue
                if max((difflib.SequenceMatcher(None, plano(tit), l).ratio() for l in lineas_cap), default=0) < 0.6:
                    a_mano.append(pl)
                for w in sorted(palabras(tit) - conocido):
                    cerca = difflib.get_close_matches(w, conocido, n=1, cutoff=0.88)
                    if cerca and not w.isdigit():
                        erratas.append("%s «%s» (¿«%s»?)" % (pl, w, cerca[0]))
            # una palabra que cambia entre plataformas en el mismo lugar del título (el autocorrector de una app)
            tits = {pl: [w for w in re.findall(r"[a-z0-9ñ]+", plano(re.sub(r"#\S+", " ", pb.get("titulo") or "")))]
                    for pl, pb in r["pubs"].items()}
            for pl, ws in sorted(tits.items()):
                for otro, ws2 in tits.items():
                    f1, f2 = fecha_de(r["pubs"][pl].get("fecha_pub")), fecha_de(r["pubs"][otro].get("fecha_pub"))
                    if otro == pl or (f1 and f2 and abs((f1 - f2).days) > 2):   # otra subida de la misma pieza, otro título
                        continue
                    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ws, ws2).get_opcodes():
                        if op == "replace" and i2 - i1 == 1 and j2 - j1 in (1, 2) and ws[i1] not in conocido and ws2[j2 - 1] in conocido:
                            erratas.append("%s «%s» (en %s: «%s»)" % (pl, ws[i1], otro, " ".join(ws2[j1:j2])))
            erratas = sorted(set(erratas))
            if erratas:
                H.append(hallazgo("AN7", "caption", pid, "posibles erratas en el título publicado: " + ", ".join(erratas),
                                  archivo=(p["ruta"] + "/caption.md"),
                                  propuesta="Corregir el título en la plataforma (el autocorrector cambió una palabra)."))
            if a_mano:
                H.append(hallazgo("AN7", "caption", pid, "título escrito a mano, no el de caption.md, en: %s" % ", ".join(a_mano),
                                  archivo=(p["ruta"] + "/caption.md"),
                                  propuesta="Publicar con el caption de caption.md (lleva las palabras que la gente busca y la "
                                            "pregunta que abre el video)."))
        # AN10 tiempo medio por plataforma
        rel_ = {}
        for pl, pb in r["pubs"].items():
            sp = ultimo(pb)
            d_ = pb.get("duracion_s") or p.get("duracion_s")
            if sp.get("avg_s") and d_:
                rel_[pl] = sp["avg_s"] / d_
        if len(rel_) >= 2 and min(rel_.values()) > 0 and max(rel_.values()) / min(rel_.values()) >= 2.5:
            H.append(hallazgo("AN10", "duracion", pid, "tiempo medio / duración: " + ", ".join("%s %.0f%%" % (k, v * 100) for k, v in sorted(rel_.items())),
                              propuesta="El mismo corte no sirve en todas: duración por plataforma."))
    # AN13 nadie lo envía: compartidos por 1,000 vistas frente a la mediana del canal en esa plataforma (Instagram dice
    # que los envíos por alcance son una de sus tres señales de Reels; referencias/analisis/investigacion.md §4)
    for pl in ("instagram", "tiktok", "facebook"):
        tasas = {}
        for k, r in R.items():
            sp = ultimo(r["pubs"][pl]) if pl in r["pubs"] else {}
            if sp.get("views") and sp["views"] >= ENVIOS_MIN_VISTAS and sp.get("shares") is not None:
                tasas[k] = 1000.0 * sp["shares"] / sp["views"]
        if len(tasas) >= ENVIOS_MIN_PIEZAS:
            med = mediana(list(tasas.values()))
            for k, v in sorted(tasas.items()):
                if med and v < 0.5 * med:
                    H.append(hallazgo("AN13", "envios", "%s:%s" % k, "%s: %.1f compartidos por 1,000 vistas (mediana del canal %.1f, n=%d)"
                                      % (pl, v, med, len(tasas)),
                                      propuesta="Un cierre que uno le mandaría a alguien concreto (la consecuencia para una persona, no "
                                                "el dato); sin pedir que lo envíen (F4)."))
    # AN14 lo deslizan en el primer cuadro (Shorts): «se quedaron viendo» bajo 60 % casi nunca despega (Galloway 2023,
    # preliminar; nivel C)
    for k, r in sorted(R.items()):
        sp = ultimo(r["pubs"]["youtube"]) if "youtube" in r["pubs"] else {}
        if sp.get("viewed_pct") is not None and sp["viewed_pct"] < VISTO_MIN and (sp.get("views") or 0) >= ENVIOS_MIN_VISTAS:
            H.append(hallazgo("AN14", "cuadro0", "%s:%s" % k, "YouTube Shorts: se quedó viendo el %.0f%% (los demás deslizaron); bajo %.0f%% "
                              "casi ninguno despega" % (sp["viewed_pct"] * 100, VISTO_MIN * 100),
                              propuesta="El primer cuadro es la miniatura: sujeto reconocible y texto que se lee sin sonido desde "
                                        "el cuadro 0 (R12, R14)."))
    # AN8 familias
    fams = {}
    for k, h in holds.items():
        f = R[k]["p"]["frases"].get("familia") or ("noticia" if k[0] == "noticias" else None)
        if f and h.get("3") is not None:
            fams.setdefault(f, []).append(h["3"])
    for f, xs in sorted(fams.items()):
        if len(xs) >= 2 and base3 and mediana(xs) < 0.8 * base3:
            H.append(hallazgo("AN8", "gancho", "familia:%s" % f, "familia «%s»: hold 3 s mediano %.0f%% (n=%d) frente a %.0f%% del canal" % (
                f, mediana(xs) * 100, len(xs), base3 * 100), propuesta="Bajar la prioridad de la familia o exigir un sujeto reconocible."))
    # AN11 tipo de pieza
    por_flujo = {}
    for k, h in holds.items():
        if h.get("3") is not None:
            por_flujo.setdefault(k[0], []).append((h["3"], ultimo(tk[k]).get("views") or 0))
    if len(por_flujo) >= 2:
        H.append(hallazgo("AN11", "tema", "canal", "TikTok por flujo: " + " · ".join(
            "%s hold3 %.0f%% vistas med. %d (n=%d)" % (f, mediana([a for a, _ in xs]) * 100, mediana([b for _, b in xs]), len(xs))
            for f, xs in sorted(por_flujo.items())), propuesta=""))
    # AN12 horario
    franjas = {}
    for k, x in tk.items():
        hh = hora_de(x.get("fecha_pub"))
        if hh is not None:
            franjas.setdefault("mañana" if hh < 12 else "tarde" if hh < 18 else "noche", []).append(ultimo(x).get("views") or 0)
    if franjas and min(len(v) for v in franjas.values()) >= 10:
        H.append(hallazgo("AN12", "horario", "canal", "vistas medianas por franja: " + ", ".join(
            "%s %d (n=%d)" % (f, mediana(v), len(v)) for f, v in franjas.items())))
    return H, {"hold3": base3, "hold1": base1, "piezas": len(R)}


def cmd_diagnostico(a):
    M = cargar()
    H, base = diagnosticar(M, a.desde)
    if a.json:
        print(json.dumps({"base": base, "hallazgos": H}, ensure_ascii=False, indent=2))
    else:
        print("[diagnóstico] %d piezas vinculadas · hold 3 s mediano %s · hold 1 s %s" % (
            base["piezas"], "%.0f%%" % (base["hold3"] * 100) if base["hold3"] else "—", "%.0f%%" % (base["hold1"] * 100) if base["hold1"] else "—"))
        for h in H:
            print("%-4s %-11s %-48s %s" % (h["codigo"], h["area"], h["pieza"][:48], h["evidencia"]))
    if a.mejoras:
        agrupar = {}
        for h in H:
            if not h["propuesta"]:
                continue
            clave = (h["codigo"], h["archivo"]) if h["codigo"] not in ("AN6", "AN7") else (h["codigo"], h["pieza"], h["archivo"])
            agrupar.setdefault(clave, []).append(h)
        mejoras = [{"area": hs[0]["area"], "archivo": hs[0]["archivo"],
                    "problema": "%s (%d): %s" % (hs[0]["codigo"], len(hs), " | ".join("%s: %s" % (x["pieza"], x["evidencia"]) for x in hs[:4]))[:900],
                    "propuesta": hs[0]["propuesta"]} for hs in agrupar.values()]
        escribir(os.path.abspath(a.mejoras), {"flujo": "analisis", "pieza": "analisis-%s" % datetime.date.today().isoformat(), "mejoras": mejoras})
        print("borrador de %d mejoras → %s (edítalo y regístralo con memoria.py --mejoras)" % (len(mejoras), rel(os.path.abspath(a.mejoras))),
              file=sys.stderr if a.json else sys.stdout)
    return 0


# ---------- rendimiento (lo leen los digestos) ----------
def categoria(p, por):
    fr = p["frases"]
    if por == "familia":
        return [fr.get("familia") or ("noticia" if p["flujo"] == "noticias" else None)]
    if por == "visual":
        return [fr.get("visual")]
    if por == "cierre":
        return [fr.get("cierre_forma")]
    if por == "animacion":
        return fr.get("animaciones") or []
    return [p["flujo"]]


def rendimiento(por="familia", M=None):
    M = M if M is not None else cargar()
    R = resumen_piezas(M)
    tabla = {}
    for k, r in R.items():
        tk, yt = r["pubs"].get("tiktok"), r["pubs"].get("youtube")
        h3 = (ultimo(tk).get("hold") or {}).get("3") if tk else None
        avg = ultimo(tk).get("avg_s") if tk else None
        vis = ultimo(tk).get("views") if tk else None
        vy = ultimo(yt).get("viewed_pct") if yt else None
        for c in categoria(r["p"], por):
            if c:
                tabla.setdefault(c, []).append({"h3": h3, "avg": avg, "views": vis, "yt": vy, "pieza": r["p"]["slug"]})
    return {c: {"n": len(xs), "hold3": mediana([x["h3"] for x in xs]), "avg_s": mediana([x["avg"] for x in xs]),
                "views": mediana([x["views"] for x in xs]), "yt_visto": mediana([x["yt"] for x in xs]),
                "piezas": [x["pieza"] for x in xs]} for c, xs in tabla.items()}


def estilos_facebook():
    """{(flujo, id): estilo} del estilo de descripción de Facebook con que /agenda programó cada pieza (agenda/*/agenda.json)."""
    out = {}
    for p in sorted(glob.glob(os.path.join(RAIZ, "agenda", "*", "agenda.json"))):
        try:
            A = leer(p) or {}
        except (OSError, ValueError):
            continue
        for s in A.get("espacios") or []:
            pz, est = s.get("pieza") or {}, (s.get("facebook") or {}).get("estilo")
            if pz.get("id") and est:
                out[(pz.get("flujo"), pz["id"])] = est
    return out


def rendimiento_facebook(M=None):
    """Por estilo de descripción: vistas, tiempo medio y distribución medianos en Facebook (lo que /agenda prueba)."""
    M = M if M is not None else cargar()
    est = estilos_facebook()
    tabla = {}
    for k, r in resumen_piezas(M).items():
        fb = r["pubs"].get("facebook")
        e = est.get(k) or est.get((FLUJO_AGENDA.get(k[0], k[0]), k[1]))
        if fb and e:
            sn = ultimo(fb)
            tabla.setdefault(e, []).append({"views": sn.get("views"), "avg": sn.get("avg_s"), "dist": sn.get("distribucion"), "pieza": r["p"]["slug"]})
    return {e: {"n": len(xs), "views": mediana([x["views"] for x in xs]), "avg_s": mediana([x["avg"] for x in xs]),
                "distribucion": mediana([x["dist"] for x in xs]), "piezas": [x["pieza"] for x in xs]} for e, xs in tabla.items()}


FLUJO_AGENDA = {"explica": "explica", "historia": "historia", "video": "video", "sabias": "sabias", "congreso": "congreso"}


def pct(v):
    return "%.0f%%" % (v * 100) if v is not None else "—"


def lineas_rendimiento(pors=("familia", "visual")):
    """Sección «Rendimiento real» para los digestos de gancho y guion; vacía si aún no hay métricas."""
    if not os.path.exists(METRICAS):
        return ["- (sin métricas: corre /analyze-improve)"]
    M = cargar()
    out = []
    for por in pors:
        t = rendimiento(por, M)
        if not t:
            continue
        base = mediana([v["hold3"] for v in t.values()])
        filas = sorted(t.items(), key=lambda kv: -(kv[1]["hold3"] or 0))
        out.append("- Por %s (TikTok: retención a 3 s · tiempo medio · vistas medianas; YouTube: «visto»): %s" % (por, " · ".join(
            "%s %s · %.0f s · %s · YT %s (n=%d)%s" % (c, pct(v["hold3"]), v["avg_s"] or 0, int(v["views"] or 0), pct(v["yt_visto"]), v["n"],
                                                    " ▼" if base and v["hold3"] is not None and v["hold3"] < 0.8 * base and v["n"] >= 2 else "")
            for c, v in filas)))
    if out:
        out.append("- ▼ = por debajo de 0.8× la mediana con n ≥ 2: si eliges esa categoría, el `por_que` explica qué la hace distinta "
                   "esta vez. Lo que más retiene en esta cuenta: un sujeto que se reconoce (marca, persona, lugar, objeto) y "
                   "un vacío que abre una pregunta (R14).")
    return out or ["- (métricas sin piezas vinculadas todavía)"]


def rendimiento_por_parte():
    """El paso de una parte a la siguiente en cada serie: vistas de N+1 entre vistas de N, por plataforma. Es la única
    medida de si el puente y la promesa de la serie funcionan (referencias/analisis/investigacion.md §2)."""
    M = cargar()
    por = {}
    for x in M.get("publicaciones") or []:
        pz = x.get("pieza") or {}
        m = re.match(r"^(.*)-parte-(\d+)$", str(pz.get("slug") or pz.get("id") or ""))
        if not m or x.get("vinculo") not in ("auto", "manual"):
            continue
        v = ultimo(x).get("views")
        if v:
            d = por.setdefault(m.group(1), {}).setdefault(x["plataforma"], {})
            d[int(m.group(2))] = max(d.get(int(m.group(2)), 0), v)
    if not por:
        print("(ninguna parte de serie publicada y medida todavía: vincula las publicaciones con metricas.py vincular)")
        return 0
    for serie, pls in sorted(por.items()):
        print(serie)
        for pl, d in sorted(pls.items()):
            ns = sorted(d)
            pasos = ["P%d %d" % (ns[0], d[ns[0]])] + ["→ P%d %d (%.0f%%)" % (b, d[b], 100.0 * d[b] / d[a_]) for a_, b in zip(ns, ns[1:])]
            print("  %-10s %s" % (pl, " ".join(pasos)))
    return 0


def cmd_rendimiento(a):
    if a.por == "estilo_fb":
        t = rendimiento_facebook()
        if not t:
            print("(sin piezas de /agenda con estilo de Facebook publicadas y medidas todavía)")
        for e, v in sorted(t.items(), key=lambda kv: -(kv[1]["views"] or 0)):
            print("%-10s n=%-2d vistas FB %6d  tiempo medio %5.1f s  distribución %s  %s" % (
                e, v["n"], int(v["views"] or 0), v["avg_s"] or 0, "%+.1f×" % v["distribucion"] if v["distribucion"] is not None else "—",
                ", ".join(v["piezas"])[:80]))
        return 0
    if a.por == "parte":
        return rendimiento_por_parte()
    if a.md:
        print("\n".join(lineas_rendimiento((a.por,))))
        return 0
    t = rendimiento(a.por)
    for c, v in sorted(t.items(), key=lambda kv: -(kv[1]["hold3"] or 0)):
        print("%-14s n=%-2d hold3 %-5s avg %5.1f s  vistas %7d  YT visto %-5s  %s" % (
            c, v["n"], pct(v["hold3"]), v["avg_s"] or 0, int(v["views"] or 0), pct(v["yt_visto"]), ", ".join(v["piezas"])[:80]))
    return 0


# ---------- M17 ----------
def revisar(M):
    """M17: esquema de memoria/metricas.json → lista de fallas."""
    f = []
    if not isinstance(M, dict) or not isinstance(M.get("publicaciones"), list):
        return ["M17 metricas.json sin publicaciones[]"]
    ids = set()
    claves = {(p["flujo"], p["id"]) for p in piezas()}
    for i, x in enumerate(M["publicaciones"]):
        for campo in ("id", "plataforma", "post_id", "titulo", "vinculo", "snapshots"):
            if campo not in x:
                f.append("M17 publicaciones[%d] sin %s" % (i, campo))
        if x.get("id") in ids:
            f.append("M17 publicaciones: id repetido %s" % x.get("id"))
        ids.add(x.get("id"))
        if x.get("plataforma") not in PLATAFORMAS:
            f.append("M17 publicaciones[%d] plataforma %r" % (i, x.get("plataforma")))
        if x.get("id") != "%s-%s" % (x.get("plataforma"), x.get("post_id")):
            f.append("M17 publicaciones[%d] id %r ≠ <plataforma>-<post_id>" % (i, x.get("id")))
        if x.get("vinculo") not in VINCULOS:
            f.append("M17 publicaciones[%d] vinculo %r" % (i, x.get("vinculo")))
        pz = x.get("pieza")
        if x.get("vinculo") in ("auto", "manual") and (not pz or (pz.get("flujo"), pz.get("id")) not in claves):
            f.append("M17 publicaciones[%d] vinculada a una pieza que no está en los registros: %r" % (i, pz))
        c = x.get("curva") or []
        if c and (any(not isinstance(v, (int, float)) or v < 0 or v > 1.5 for v in c)):
            f.append("M17 publicaciones[%d] curva con valores fuera de 0–1.5" % i)
        for s in x.get("snapshots") or []:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(s.get("fecha"))):
                f.append("M17 publicaciones[%d] snapshot sin fecha AAAA-MM-DD" % i)
            for k in ("completion", "viewed_pct"):
                if s.get(k) is not None and not 0 <= s[k] <= 1:
                    f.append("M17 publicaciones[%d] %s=%r fuera de 0–1" % (i, k, s[k]))
    return f


def cmd_check(_a):
    if not os.path.exists(METRICAS):
        print("[M17] memoria/metricas.json no existe (ok: /analyze-improve lo crea)")
        return 0
    f = revisar(leer(METRICAS))
    for x in f:
        print("FALLA", x)
    print("[M17] %s" % ("ok" if not f else "%d fallas" % len(f)))
    return 1 if f else 0


def main():
    global METRICAS
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--check", action="store_true", help="M17: esquema de memoria/metricas.json")
    ap.add_argument("--metricas", help="otro metricas.json (pruebas y fixture); por defecto memoria/metricas.json")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("importar")
    s.add_argument("capturas", nargs="+")
    s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("vincular")
    s.add_argument("--fijar", nargs=2, metavar=("PUB", "FLUJO:ID"))
    s.add_argument("--ajena", metavar="PUB")
    s.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("alinear")
    s.add_argument("pieza")
    s.add_argument("--plataforma", choices=PLATAFORMAS, default="tiktok")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("diagnostico")
    s.add_argument("--desde")
    s.add_argument("--mejoras", metavar="SALIDA")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("rendimiento")
    s.add_argument("--por", choices=("familia", "visual", "cierre", "animacion", "flujo", "estilo_fb", "parte"), default="familia")
    s.add_argument("--md", action="store_true")
    a = ap.parse_args()
    if a.metricas:
        METRICAS = os.path.abspath(a.metricas)
    if a.check:
        return cmd_check(a)
    fn = {"importar": cmd_importar, "vincular": cmd_vincular, "alinear": cmd_alinear, "diagnostico": cmd_diagnostico,
          "rendimiento": cmd_rendimiento}.get(a.cmd)
    if not fn:
        ap.print_help()
        return 2
    return fn(a)


if __name__ == "__main__":
    sys.exit(main())
