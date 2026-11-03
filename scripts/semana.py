#!/usr/bin/env python3
"""/semana: «Las 5 cifras de la semana en Guatemala» → video vertical 1080×1920 de 62–90 s (TikTok / Reels / Shorts) y
su 4:5, en cuenta regresiva 5→1. Es el modo `semana` de /noticias: se publica el domingo y cuenta la semana de lunes a
domingo con las cifras de las noticias YA verificadas en los noticieros diarios (`confirmada`, con su cita guardada) y
los datos oficiales nuevos que traen dos rastreadores (`ofi`, `sem`). `en_desarrollo` nunca entra.

Escribe el MISMO trabajo que /noticias y /video (video.json, locucion.json, audio/, escenas.json, clips/, salida/): cada
cifra es una escena `noticia` (video/noticia.html con el numeral del puesto, el chip «Sección · día» y la línea a escala
humana bajo la cifra), el gancho es un `titular` y el cierre (video/cierre.html) lleva las 5 cifras en 5 líneas. La voz,
la grabación, el montaje con música y efectos y la revisión salen de scripts/video.py; leer, foto y la hoja de fotos,
de scripts/noticias.py. Guía: referencias/flujo-semana.md.

Subcomandos (TRABAJO = sesiones/semana-<domingo>/):
  preparar [--fecha YYYY-MM-DD] [--trabajo DIR] [--diarios DIR] [--memoria ARCHIVO] [--paleta P] [--musica ID] [--fixture]
        crea TRABAJO y video.json (tipo semana, ventana lunes→domingo, paleta y música fijas de marca, piso_s 61,
        palabra_clave). Sin --fecha: el domingo más reciente (hoy si es domingo); una fecha entre semana se lleva a su
        domingo. --diarios: dónde buscar sesiones/noticias-<día>/ (por defecto sesiones/); --memoria: el registro de
        semanas para SM6 (por defecto memoria/semanas.json). --fixture copia la maqueta (guion, verificación oficial),
        cosecha sus diarios y consolida
  cosechar TRABAJO             los 7 noticieros de la semana → cosecha.json: cada noticia `confirmada` con cifras, con N2
        rehecho en código (ventana de 7 días), su fuente con fecha en la ventana (SM2) y su foto copiada; lista los días
        sin noticiero y lo descartado (en desarrollo, no confirmada, sin cifras, fuera de ventana, repetida)
  candidatas TRABAJO --check [--seccion ofi|sem]   N1 sobre candidatas_<sec>.json de los rastreadores de la semana
  verificacion TRABAJO --check [--id ID]   N2 + N7 con la ventana de la semana; un dato oficial con su fuente oficial
        (*.gob.gt, Banguat, INE…) puede ir `confirmada` con esa sola fuente si cada cifra sale de ella (SM3)
  consolidar TRABAJO           cosecha.json + verificacion_*.json confirmadas → noticias.json (cifras sm-cNN)
  digesto TRABAJO --para rastreador | verificador --id ID | editor
  guion TRABAJO --check        SM1–SM11 (+ N4, V3, V5) sobre guion.json y noticias.json → locucion.json
  tiempos TRABAJO              noticias.py tiempos con el puesto, el chip y la línea humana → escenas.json; SM5 piso real
        (piso_duracion) y SM11 con los tiempos reales de la voz del gancho
  entregar TRABAJO [--salida DIR]   → semanas/<domingo>/ (9:16, 4:5, caption.md, fuentes.md, subtítulos, portadas,
        guion.json de entrega con las 5 cifras, su valor, cita y url); exige la voz de ElevenLabs salvo con --salida
  carrusel CARPETA [--trabajo DIR] [--fixture]   la semana entregada (o un TRABAJO) → TRABAJO de /carrusel con su
        carrusel.json escrito y `carrusel.py guion --check` en 0; luego `carrusel.py render` y `entregar`
  leer | foto | fotos-contacto ...   → noticias.py · voz | voz-falsa | descargar | escuchar | grabar | montar | revisar → video.py

Gates: SM1 5 cifras en orden 5→1 sin repetir y el gancho no dice ni muestra la #1 · SM2 publicada de lunes a domingo, con
su fuente guardada fechada en la ventana · SM3 noticia confirmada (o dato oficial) y su cita trae el valor · SM4 ≥ 3
secciones, ≤ 2 por sección, una cifra por noticia · SM5 62–90 s estimados; < 61 s reales es falla · SM6 ninguna cifra de
las últimas 8 semanas (memoria/semanas.json; aviso si salió en /dato o /sabias en 30 días) · SM7 fuente en pantalla de
1–44 caracteres que nombra un medio u organismo de la noticia · SM8 ≥ 3 cifras con `humana` ≤ 40 respaldada · SM9 N6 y
N7 de /noticias · SM10 cierre de 5 líneas ≤ 26 con su cifra, `final` ≤ 12 palabras y última frase, sin cebo · SM11 la
1.ª línea de los captions de TikTok y Shorts, la pantalla y la voz del gancho dicen «Guatemala» y «semana» (V19).

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import noticias as NT  # noqa: E402
import video as VD  # noqa: E402

FIXTURE = os.path.join(RAIZ, "sesiones", "_fixture_semana")
SEMANAS = os.path.join(RAIZ, "memoria", "semanas.json")
# marca fija de /semana (decisión del usuario, 2026-11-03): la misma paleta y la misma pista cada domingo, para que la
# serie se reconozca. Cielo («neutro y analítico: economía, precios») va con un resumen de cifras; cielo-2 es la pista.
# El ciclo diario de /noticias pasa por cielo uno de cada 8 días: ese domingo los dos videos comparten color (no la
# pista si el diario cae en cielo-1). Cambiable aquí o con --paleta / --musica en preparar
PALETA_SEMANA, MUSICA_SEMANA = "cielo", "cielo-2"
DIAS = 7                                  # lunes → domingo
CIFRAS = 5                                # la cuenta regresiva 5 → 1
PUESTOS = list(range(CIFRAS, 0, -1))
# los dos rastreadores de la semana (espejo en .claude/workflows/noticias.js, MODOS.semana.SECCIONES; W11)
SECCIONES = {"ofi": "datos oficiales nuevos de la semana: Banguat, INE, MSPAS, SAT, PNC, Mineduc, Conred, cualquier *.gob.gt",
             "sem": "noticias con cifra de la semana que los noticieros diarios no contaron"}
SECCIONES_MIN, POR_SECCION_MAX = 3, 2
# los puntajes del crítico en «Modo semana» (SM-C1–SM-C6; espejo en noticias.js, MODOS.semana.puntajes; W11)
PUNTAJES = ("gancho", "orden", "claridad", "escala", "tono", "cierre")
OBJETIVO_S, DURACION_MIN_S, DURACION_MAX_S, PISO_S = 75, 62, 90, 61
# voz ya en palabras, en caracteres (≈ 15.5 por segundo): gancho ≈ 3–7 s; cifra ≈ 8–13 s; cierre ≈ 3–8 s
CARACTERES = {"gancho_semana": (40, 115), "cifra_semana": (110, 205), "cierre_semana": (40, 125)}
HUMANA_CARACTERES, HUMANA_MIN = 40, 3
RESUMEN_CARACTERES, FINAL_PALABRAS = 26, 12
CLAVES = ("Guatemala", "semana")          # SM11: las dos (no son alias)
CLAVES_PLATAFORMAS = ("tiktok", "shorts")
CLAVE_S = 6.0                             # «Guatemala» y «semana» suenan en los primeros 6 s del gancho
SEMANAS_ATRAS, AVISO_DIAS = 8, 30
DIAS_CORTOS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")

leer, escribir, falla = NT.leer, NT.escribir, NT.falla


# ---------- fechas ----------
def domingo_de(fecha=None):
    """Sin fecha: el domingo más reciente (hoy si es domingo). Con fecha: el domingo de su semana (lunes→domingo)."""
    if fecha:
        d = datetime.date.fromisoformat(fecha)
        return d + datetime.timedelta(days=6 - d.weekday())
    hoy = datetime.date.today()
    return hoy - datetime.timedelta(days=(hoy.weekday() + 1) % 7)


def ventana(domingo):
    d = datetime.date.fromisoformat(domingo) if isinstance(domingo, str) else domingo
    return (d - datetime.timedelta(days=DIAS - 1)).isoformat(), d.isoformat()


def en_semana(f, st):
    lunes, domingo = st["ventana"]
    return bool(f) and lunes <= str(f)[:10] <= domingo


def rango_corto(st):
    a, b = (datetime.date.fromisoformat(x) for x in st["ventana"])
    if a.month == b.month:
        return "%d–%d %s" % (a.day, b.day, NT.MESES_CORTOS[b.month - 1])
    return "%d %s–%d %s" % (a.day, NT.MESES_CORTOS[a.month - 1], b.day, NT.MESES_CORTOS[b.month - 1])


def dia_corto(f):
    d = datetime.date.fromisoformat(f)
    return "%s %d %s" % (DIAS_CORTOS[d.weekday()], d.day, NT.MESES_CORTOS[d.month - 1])


def semana_iso(domingo):
    y, w, _ = datetime.date.fromisoformat(domingo).isocalendar()
    return "%d-W%02d" % (y, w)


def es_semana(st):
    return st.get("tipo") == "semana"


# ---------- preparar ----------
def cmd_preparar(a):
    try:
        domingo = domingo_de(a.fecha).isoformat()
    except ValueError:
        print("--fecha va como YYYY-MM-DD", file=sys.stderr)
        return 2
    if a.fecha and a.fecha != domingo:
        print("AVISO %s no es domingo: la semana es la que termina el %s" % (a.fecha, domingo))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "semana-" + domingo))
    for d in ("audio", "salida", "revision", "fotos"):
        os.makedirs(os.path.join(trabajo, d), exist_ok=True)
    paleta = a.paleta or PALETA_SEMANA
    try:
        pista = VD.elegir_musica(paleta, a.musica or (MUSICA_SEMANA if paleta == PALETA_SEMANA else None))
    except (ValueError, SystemExit) as ex:
        return falla("música: %s" % ex)
    diarios = os.path.abspath(a.diarios or (os.path.join(FIXTURE, "diarios") if a.fixture else os.path.join(RAIZ, "sesiones")))
    memoria = os.path.abspath(a.memoria or (os.path.join(FIXTURE, "semanas.json") if a.fixture else SEMANAS))
    lunes, _ = ventana(domingo)
    st = {"tipo": "semana", "fecha": domingo, "ventana": [lunes, domingo], "ventana_dias": DIAS - 1,
          "slug": "semana-" + domingo, "id": semana_iso(domingo), "hilo": None, "paleta": paleta, "musica": pista["id"],
          "duracion": "semana", "objetivo_s": OBJETIVO_S, "duracion_max_s": DURACION_MAX_S, "piso_s": PISO_S, "palabra_clave": list(CLAVES), "tarjetas": [],
          "diarios": VD.rel(diarios), "memoria": VD.rel(memoria), "fixture": bool(a.fixture)}
    escribir(os.path.join(trabajo, "video.json"), st)
    print("semana %s (%s → %s) · paleta %s · música %s" % (st["id"], lunes, domingo, paleta, pista["id"]))
    if a.fixture:
        shutil.copy(os.path.join(FIXTURE, "guion.json"), os.path.join(trabajo, "guion.json"))
        for r in glob.glob(os.path.join(FIXTURE, "oficial", "verificacion_*.json")):
            v = leer(r)
            if (v.get("foto") or {}).get("archivo"):
                foto_fixture(os.path.join(trabajo, v["foto"]["archivo"]), len(v["id"]))
            escribir(os.path.join(trabajo, os.path.basename(r)), v)
        if cosechar(trabajo) or consolidar(trabajo):
            return 1
    print(VD.rel(trabajo))
    return 0


def foto_fixture(dst, k):
    """Una foto de ejemplo (fractal de ffmpeg, sin web) para la maqueta, como noticias.fotos_fixture."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    VD.ff("-f", "lavfi", "-i", "mandelbrot=s=1600x1200:start_scale=%.2f:end_scale=0.3:start_x=%.3f:start_y=%.3f:maxiter=600" % (
        2.6 - 0.21 * (k % 7), -0.743 + 0.008 * (k % 7), 0.131 - 0.015 * (k % 7)),
        "-vf", "hue=h=%d:s=0.55,eq=brightness=-0.04:saturation=0.8,noise=alls=12:allf=t" % (37 * k % 360),
        "-frames:v", "1", "-q:v", "3", dst)


# ---------- cosechar ----------
def meta_fechada(f, st):
    """SM2: el .json que guardó `leer` junto al texto de la fuente trae su fecha, dentro de la ventana."""
    arch = f.get("archivo") or ""
    meta = os.path.join(RAIZ, re.sub(r"\.txt$", ".json", arch))
    if not arch.endswith(".txt") or not os.path.isfile(meta):
        return False
    return en_semana(leer(meta).get("fecha"), st)


def publicada_de(v, st):
    """La fecha de publicación de una noticia en la semana: la más reciente de sus fuentes que cae en la ventana."""
    fs = sorted(f.get("fecha") for f in v.get("fuentes") or [] if en_semana(f.get("fecha"), st))
    return fs[-1] if fs else None


def misma_cifra(a, b):
    """Dos noticias de días distintos con la misma cifra (valor y unidad) y alguna palabra del titular en común (≥ 30 %):
    la misma historia contada dos veces («Capturan a 7 policías…» y «Siete policías, ante tribunales…»)."""
    va = {(c.get("valor"), VD._plano(c.get("unidad"))) for c in a.get("cifras") or []}
    vb = {(c.get("valor"), VD._plano(c.get("unidad"))) for c in b.get("cifras") or []}
    if not va & vb:
        return False
    pa, pb = ({w for w in VD._plano(x.get("titular")).split() if len(w) > 3} for x in (a, b))
    return bool(pa and pb) and len(pa & pb) / min(len(pa), len(pb)) >= 0.3


def cosechar(trabajo):
    st = VD.estado(trabajo)
    diarios = os.path.join(RAIZ, st["diarios"])
    lunes = datetime.date.fromisoformat(st["ventana"][0])
    dias, tomadas, descartadas = [], [], []
    for k in range(DIAS):
        d = (lunes + datetime.timedelta(days=k)).isoformat()
        dirs = [os.path.join(diarios, "noticias-" + d)]
        ruta = next((os.path.join(x, "noticias.json") for x in dirs if os.path.isfile(os.path.join(x, "noticias.json"))), None)
        if not ruta:
            dias.append({"fecha": d, "noticiero": False, "noticias": 0})
            continue
        base = leer(ruta).get("noticias") or []
        dias.append({"fecha": d, "noticiero": True, "noticias": len(base), "ruta": VD.rel(os.path.dirname(ruta))})
        for v in base:
            nid = "d%02d-%s" % (int(d[8:]), v.get("id"))
            if v.get("estado") != "confirmada":
                descartadas.append({"id": nid, "motivo": "estado %s (solo entran confirmadas)" % v.get("estado")})
                continue
            if not v.get("cifras"):
                descartadas.append({"id": nid, "motivo": "sin cifras verificadas"})
                continue
            w = json.loads(json.dumps(v))
            w.update(id=nid, id_original=v.get("id"), diario=d)
            foto = w.get("foto") or {}
            if foto.get("archivo"):
                src, dst = os.path.join(os.path.dirname(ruta), foto["archivo"]), "fotos/%s.jpg" % nid
                if os.path.isfile(src):
                    shutil.copyfile(src, os.path.join(trabajo, dst))
                elif st.get("fixture"):
                    foto_fixture(os.path.join(trabajo, dst), len(tomadas) + 3)
                else:
                    w["foto"] = None
                    dst = None
                if dst:
                    w["foto"] = dict(foto, archivo=dst)
            fs, _ = NT.revisar_verificacion(w, st["fecha"], trabajo, st["ventana_dias"])
            if fs:
                descartadas.append({"id": nid, "motivo": "N2 rehecho: " + fs[0]})
                continue
            w["publicada"] = publicada_de(w, st)
            if not w["publicada"]:
                descartadas.append({"id": nid, "motivo": "fuera de ventana: ninguna fuente publicada del %s al %s" % tuple(st["ventana"])})
                continue
            if not any(meta_fechada(f, st) for f in w.get("fuentes") or []):
                descartadas.append({"id": nid, "motivo": "SM2: ninguna fuente guardada (noticias.py leer) con fecha en la ventana"})
                continue
            rep = next((t for t in tomadas if NT.repetida(w, [(t["diario"], t.get("titular") or "",
                                                               {f.get("url") for f in t.get("fuentes") or []})])
                        or misma_cifra(w, t)), None)
            if rep:
                # la misma noticia en dos diarios: queda la que tiene más fuentes (o la primera)
                if len(w.get("fuentes") or []) > len(rep.get("fuentes") or []):
                    tomadas.remove(rep)
                    descartadas.append({"id": rep["id"], "motivo": "repetida: la misma noticia que %s" % nid})
                else:
                    descartadas.append({"id": nid, "motivo": "repetida: la misma noticia que %s" % rep["id"]})
                    continue
            tomadas.append(w)
    sin = [x["fecha"] for x in dias if not x["noticiero"]]
    escribir(os.path.join(trabajo, "cosecha.json"), {"fecha": st["fecha"], "ventana": st["ventana"], "dias": dias,
                                                     "sin_noticiero": sin, "noticias": tomadas, "descartadas": descartadas})
    for x in dias:
        print("%s %-3s %s" % (x["fecha"], DIAS_CORTOS[datetime.date.fromisoformat(x["fecha"]).weekday()],
                              "%d noticias (%s)" % (x["noticias"], x["ruta"]) if x["noticiero"] else "sin noticiero"))
    for v in tomadas:
        print("  + %-12s %-12s %s · %s" % (v["id"], v.get("seccion"), v["publicada"], v.get("titular")))
    for x in descartadas:
        print("  - %-12s %s" % (x["id"], x["motivo"]))
    print("→ %s · %d cosechadas · %d descartadas · días sin noticiero: %s"
          % (VD.rel(os.path.join(trabajo, "cosecha.json")), len(tomadas), len(descartadas), ", ".join(sin) or "ninguno"))
    return 0


def cmd_cosechar(a):
    return cosechar(os.path.abspath(a.trabajo))


# ---------- rastreo y verificación de lo nuevo (ofi, sem) ----------
def cmd_candidatas(a):
    NT.SECCIONES = SECCIONES   # los rastreadores de la semana: ofi y sem (N1 con la ventana de 7 días)
    return NT.cmd_candidatas(a)


def revisar_semana(v, st, trabajo):
    """N2 + N7 con la ventana de la semana; SM3: un dato oficial con su fuente oficial puede ir `confirmada` con esa sola
    fuente si cada cifra sale de ella (su cita y su url son de la fuente oficial)."""
    fs, av = NT.revisar_verificacion(v, st["fecha"], trabajo, st["ventana_dias"])
    oficiales = {f.get("url") for f in v.get("fuentes") or [] if NT.clasificar(f.get("url"))[0] == "oficial"}
    if v.get("estado") == "confirmada" and oficiales and v.get("cifras") and all(c.get("url") in oficiales for c in v["cifras"]):
        quitar = [x for x in fs if "confirmada pide 2 fuentes" in x]
        if quitar:
            fs = [x for x in fs if x not in quitar]
            av.append("%s: dato oficial con su sola fuente oficial (SM3)" % v.get("id"))
    if v.get("estado") == "en_desarrollo":
        av.append("%s: en desarrollo no entra en /semana" % v.get("id"))
    if v.get("estado") == "confirmada" and not publicada_de(v, st):
        fs.append("SM2 %s: ninguna fuente publicada del %s al %s" % (v.get("id"), *st["ventana"]))
    return fs, av


def cmd_verificacion(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    rutas = [os.path.join(trabajo, "verificacion_%s.json" % a.id)] if a.id else sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json")))
    fallas, avisos = [], []
    for r in rutas:
        if not os.path.exists(r):
            fallas.append("N2 falta %s" % VD.rel(r))
            continue
        f, av = revisar_semana(leer(r), st, trabajo)
        fallas += f
        avisos += av
    for x in avisos:
        print("AVISO", x)
    for x in fallas:
        print("FALLA", x)
    if not fallas:
        print("N2 ok · %d noticia(s) de la semana" % len(rutas))
    return 1 if fallas else 0


def consolidar(trabajo):
    """cosecha.json + verificacion_*.json (confirmadas, que pasan N2 de la semana) → noticias.json; cada cifra con un id
    de la semana (sm-c01…) y su `id_original`."""
    st = VD.estado(trabajo)
    ruta_c = os.path.join(trabajo, "cosecha.json")
    if not os.path.exists(ruta_c):
        return falla("falta cosecha.json: corre semana.py cosechar")
    nts = list(leer(ruta_c)["noticias"])
    for r in sorted(glob.glob(os.path.join(trabajo, "verificacion_*.json"))):
        v = leer(r)
        f, _ = revisar_semana(v, st, trabajo)
        if v.get("estado") != "confirmada" or f or not v.get("cifras"):
            print("  - %-12s %s" % (v.get("id"), f[0] if f else "estado %s%s" % (v.get("estado"), "" if v.get("cifras") else ", sin cifras")))
            continue
        v["publicada"] = publicada_de(v, st)
        nts.append(v)
    k = 0
    for v in nts:
        for c in v.get("cifras") or []:
            k += 1
            c.setdefault("id_original", c.get("id"))
            c["id"] = "sm-c%02d" % k
    escribir(os.path.join(trabajo, "noticias.json"), {"fecha": st["fecha"], "ventana": st["ventana"], "noticias": nts})
    for v in nts:
        print("%-12s %-12s %s · %s · %s" % (v["id"], v.get("seccion"), v.get("publicada"), v.get("titular"),
                                            ", ".join("%s=%s" % (c["id"], c.get("texto")) for c in v["cifras"])))
    secs = {(v.get("seccion") or "").lower() for v in nts}
    print("→ %s · %d noticias con cifras en %d secciones" % (VD.rel(os.path.join(trabajo, "noticias.json")), len(nts), len(secs)))
    if len(nts) < CIFRAS or len(secs) < SECCIONES_MIN:
        return falla("SM4 solo %d noticias en %d secciones (van ≥ %d en ≥ %d): faltan datos oficiales o noticias de la semana"
                     % (len(nts), len(secs), CIFRAS, SECCIONES_MIN))
    return 0


def cmd_consolidar(a):
    return consolidar(os.path.abspath(a.trabajo))


# ---------- digesto ----------
def semanas_previas(st):
    """Registros de memoria/semanas.json de las últimas SEMANAS_ATRAS semanas antes de esta (SM6)."""
    ruta = os.path.join(RAIZ, st.get("memoria") or VD.rel(SEMANAS))
    if not os.path.exists(ruta):
        return []
    hoy = datetime.date.fromisoformat(st["fecha"])
    return [r for r in leer(ruta).get("semanas") or [] if 0 < (hoy - datetime.date.fromisoformat(r["fecha"])).days <= 7 * SEMANAS_ATRAS]


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    if a.para == "verificador":
        return NT.cmd_digesto(a)
    if a.para == "rastreador":
        cos = leer(os.path.join(trabajo, "cosecha.json")) if os.path.exists(os.path.join(trabajo, "cosecha.json")) else {"noticias": [], "sin_noticiero": []}
        print("\n".join(["# Rastreo de la semana · %s → %s" % tuple(st["ventana"]), "",
                         "Solo lo publicado del %s al %s. Cada candidata trae una CIFRA (un número con su cita). No en desarrollo." % tuple(st["ventana"]),
                         "", "## Secciones"] + ["- %s: %s" % kv for kv in SECCIONES.items()] +
                        ["", "## Ya cosechadas de los noticieros diarios (no las propongas)"] +
                        (["- %s · %s · %s" % (v["id"], v.get("seccion"), v.get("titular")) for v in cos["noticias"]] or ["- (ninguna)"]) +
                        ["", "## Días sin noticiero (ahí falta rastreo): %s" % (", ".join(cos.get("sin_noticiero") or []) or "ninguno"),
                         "", "## Ya contadas en las últimas %d semanas (no las repitas: SM6)" % SEMANAS_ATRAS] +
                        (["- %s · #%s %s · %s" % (r["id"], c.get("puesto"), c.get("texto"), c.get("titular")) for r in semanas_previas(st) for c in r.get("cifras") or []] or ["- (ninguna)"]) +
                        ["", "## Medios que cuentan (dominio → grupo)"] + ["- %s → %s" % kv for kv in sorted(NT.MEDIOS.items())] +
                        ["", "## Fuentes oficiales: cualquier *.gob.gt, y %s" % ", ".join(sorted(NT.OFICIALES))]))
        return 0
    base = leer(os.path.join(trabajo, "noticias.json"))
    out = ["# Cifras de la semana · %s → %s (paleta %s, música %s)" % (*st["ventana"], st["paleta"], st["musica"]), ""]
    for v in base["noticias"]:
        out += ["## %s · %s · publicada %s (%s)" % (v["id"], v.get("seccion"), v.get("publicada"), dia_corto(v["publicada"]) if v.get("publicada") else "?"),
                "Titular: %s" % v.get("titular"), "Qué pasó: %s" % (v.get("resumen") or ""),
                "Foto: %s · icono: %s · lugar: %s" % ("%s (%s)" % (v["foto"]["credito"], v["foto"]["origen"]) if v.get("foto") else "NO",
                                                     v.get("icono") or "—", v.get("depto") or "—"),
                "Fuentes: " + " · ".join("%s (%s, %s)" % (f.get("medio"), NT.clasificar(f.get("url"))[0] or "fuera de lista", f.get("fecha")) for f in v.get("fuentes") or [])]
        out += ["- cifra %s = %s %s («%s») — cita «%s»" % (c["id"], c.get("valor"), c.get("unidad"), c.get("texto"), c.get("cita")) for c in v.get("cifras") or []]
        out += ["- hecho: %s — «%s»" % (h.get("texto"), h.get("cita")) for h in v.get("hechos") or []]
        out.append("")
    prev = semanas_previas(st)
    out += ["## Ya contadas en las últimas %d semanas (SM6: no las repitas)" % SEMANAS_ATRAS] + \
        (["- %s · %s · %s" % (r["id"], c.get("texto"), c.get("titular")) for r in prev for c in r.get("cifras") or []] or ["- (ninguna)"])
    out += ["", "## Límites del guion (semana.py guion --check, SM1–SM11)",
            "- 5 cifras en `cifras[]` con `puesto` 5, 4, 3, 2, 1 (la más fuerte al final); una por noticia; ≥ %d secciones y ≤ %d por sección"
            % (SECCIONES_MIN, POR_SECCION_MAX),
            "- el gancho no dice ni muestra la #1; dice «Guatemala» y «semana» en sus primeros %.0f s, y su pantalla también" % CLAVE_S,
            "- voz en palabras: gancho %d–%d caracteres, cada cifra %d–%d, cierre %d–%d; total %d–%d s (objetivo %d; < %d s reales falla)"
            % (*CARACTERES["gancho_semana"], *CARACTERES["cifra_semana"], *CARACTERES["cierre_semana"], DURACION_MIN_S, DURACION_MAX_S, OBJETIVO_S, PISO_S),
            "- titular ≤ %d palabras y ≤ %d caracteres; fuente ≤ %d que nombra un medio u organismo de la noticia; cifra ≤ %d con etiqueta ≤ %d"
            % (NT.TITULAR_PALABRAS, NT.TITULAR_CARACTERES, NT.FUENTE_CARACTERES, NT.CIFRA_CARACTERES, NT.ETIQUETA_CARACTERES),
            "- `humana` (≤ %d caracteres) en ≥ %d cifras: la cifra a escala humana, con números de la cita o `calculo` (ids sm-cNN)"
            % (HUMANA_CARACTERES, HUMANA_MIN),
            "- cierre: 5 líneas de resumen ≤ %d caracteres, cada una con su cifra, en el orden de la cuenta; final ≤ %d palabras = última frase"
            % (RESUMEN_CARACTERES, FINAL_PALABRAS),
            "- captions tiktok, instagram, facebook y shorts (título ≤ %d con #Shorts); la 1.ª línea de tiktok y shorts dice «Guatemala» y «semana»"
            % VD.SHORTS_TITULO,
            "", "## Plantilla de guion.json", "```json",
            json.dumps({"tipo": "semana", "fecha": st["fecha"], "ventana": st["ventana"],
                        "contexto_superior": "Guatemala · semana del %s" % rango_corto(st),
                        "gancho": {"pantalla": "Las 5 cifras de la semana", "texto": "Estas son las 5 cifras de la semana en Guatemala. …"},
                        "cifras": [{"puesto": 5, "noticia": "<id>", "cifra_id": "sm-cNN", "seccion": "<sección>", "titular": "<≤ 9 palabras>",
                                    "texto": "<2–3 oraciones con la cifra en dígitos>", "cifra": {"texto": "<1,200>", "etiqueta": "<≤ 30>"},
                                    "humana": "<≤ 40, opcional>", "calculo": "<opcional>", "fuente": "<Medio · Organismo>", "publicada": "<YYYY-MM-DD>"}],
                        "cierre": {"rotulo": "La semana en Guatemala", "resumen": ["<≤ 26 con la cifra>"] * 5, "texto": "<…> <final>", "final": "<≤ 12 palabras>"},
                        "caption": {"tiktok": "<Guatemala … semana …>", "instagram": "…", "facebook": "…", "shorts": "<título con semana y Guatemala> #Shorts\n…"}},
                       ensure_ascii=False, indent=1), "```"]
    print("\n".join(out))
    return 0


# ---------- gate del guion (SM1–SM11) ----------
def respaldo_cifra(c):
    v = round(float(c["valor"]), 6)
    return [(v, NT.VM.factor_unidad(c.get("unidad"))), (v, None)]


def cifras_por_id(base):
    return {c["id"]: dict(c, noticia=v["id"]) for v in base.get("noticias") or [] for c in v.get("cifras") or []}


def valores_calculo(calc, cifras):
    """`calculo` (string o lista) con ids sm-cNN → valores (VD.resolver_calculo) y motivos de falla."""
    vals, motivos = [], []
    valores = sorted({x for c in cifras.values() if isinstance(c.get("valor"), (int, float)) for x in respaldo_cifra(c)}, key=lambda x: x[0])
    for expr in ([calc] if isinstance(calc, str) else calc or []):
        r, m = VD.resolver_calculo(expr, cifras, valores)
        if m:
            motivos.append("calculo «%s» %s" % (expr, m))
        else:
            vals.append(r)
    return vals, motivos


def nombra_fuente(fuente, nt):
    """SM7: algún trozo de la fuente en pantalla («Prensa Libre · MP») nombra un medio u organismo de la noticia (sus
    medios, sus dominios o una sigla que aparece en sus citas, hechos o titular)."""
    conocido = " ".join(VD._plano(x) for x in [f.get("medio") for f in nt.get("fuentes") or []] +
                        [NT.dominio(f.get("url")) for f in nt.get("fuentes") or []] +
                        [h.get("cita") or "" for h in (nt.get("hechos") or []) + (nt.get("cifras") or []) + (nt.get("fuentes") or [])] +
                        [nt.get("titular") or "", nt.get("resumen") or ""] if x)
    for trozo in re.split(r"[·,/|]", fuente or ""):
        t = VD._plano(trozo)
        if len(t) >= 2 and re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(t), conocido):
            return True
    return False


def recientes_otros(st):
    """SM6 (aviso): valores de /dato y /sabias de los últimos 30 días → [(valor, etiqueta)]."""
    hoy, out = datetime.date.fromisoformat(st["fecha"]), []
    dat = os.path.join(RAIZ, "memoria", "datos.json")
    regs = leer(dat).get("datos") or [] if os.path.exists(dat) else []
    por_ruta = {r.get("ruta"): r for r in regs}
    for r in regs:
        if 0 <= (hoy - datetime.date.fromisoformat(r["fecha"])).days <= AVISO_DIAS and isinstance(r.get("valor_final"), (int, float)):
            out.append((float(r["valor_final"]), "/dato %s" % r.get("slug")))
    sab = os.path.join(RAIZ, "memoria", "sabias.json")
    for r in (leer(sab).get("sabias") or []) if os.path.exists(sab) else []:
        d = por_ruta.get(r.get("dato"))
        if d and 0 <= (hoy - datetime.date.fromisoformat(r["fecha"])).days <= AVISO_DIAS and isinstance(d.get("valor_final"), (int, float)):
            out.append((float(d["valor_final"]), "/sabias %s" % r.get("slug")))
    return out


def repetida_en(c, nt, base_c, prev):
    """SM6: la cifra salió en una semana anterior (mismo id original y noticia, misma url y valor, o titular ≥ 60 %)."""
    urls = {f.get("url") for f in nt.get("fuentes") or []} | ({base_c.get("url")} if base_c.get("url") else set())
    pal = {w for w in VD._plano(c.get("titular") or nt.get("titular")).split() if len(w) > 3}
    for r in prev:
        for x in r.get("cifras") or []:
            if x.get("url") in urls and isinstance(x.get("valor"), (int, float)) and abs(float(x["valor"]) - float(base_c["valor"])) < 1e-9:
                return r["id"]
            otras = {w for w in VD._plano(x.get("titular")).split() if len(w) > 3}
            if pal and otras and len(pal & otras) / min(len(pal), len(otras)) >= 0.6:
                return r["id"]
    return None


def validar_guion(trabajo):
    """SM1–SM11 (+ N4, V3, V5) → (fallas, avisos, locucion, estimado)."""
    st = VD.estado(trabajo)
    g = leer(os.path.join(trabajo, "guion.json"))
    base = leer(os.path.join(trabajo, "noticias.json"))
    por_nt = {v["id"]: v for v in base.get("noticias") or []}
    cifras = cifras_por_id(base)
    NT.CARACTERES.update(CARACTERES)
    fallas, avisos, loc = [], [], []
    cs = g.get("cifras") or []
    # SM1 la cuenta regresiva
    if len(cs) != CIFRAS:
        fallas.append("SM1 %d cifras (van %d, puestos %s)" % (len(cs), CIFRAS, "→".join(map(str, PUESTOS))))
    if [c.get("puesto") for c in cs] != PUESTOS[:len(cs)] or len(cs) != CIFRAS:
        fallas.append("SM1 los puestos van en orden %s (llegó %s)" % (", ".join(map(str, PUESTOS)), ", ".join(str(c.get("puesto")) for c in cs)))
    ids = [c.get("cifra_id") for c in cs]
    if len(set(ids)) != len(ids):
        fallas.append("SM1 una cifra va dos veces")
    # SM4 secciones y una cifra por noticia
    nts = [c.get("noticia") for c in cs]
    if len(set(nts)) != len(nts):
        fallas.append("SM4 una noticia aporta dos cifras (una por noticia)")
    secs = [VD._plano(c.get("seccion")) for c in cs]
    if len(set(secs)) < SECCIONES_MIN:
        fallas.append("SM4 %d secciones (van ≥ %d)" % (len(set(secs)), SECCIONES_MIN))
    for s_ in sorted(set(secs)):
        if secs.count(s_) > POR_SECCION_MAX:
            fallas.append("SM4 %d cifras de «%s» (máximo %d por sección)" % (secs.count(s_), s_, POR_SECCION_MAX))
    prev = semanas_previas(st)
    otros = recientes_otros(st)
    pantallas_g = [g.get("contexto_superior") or "", (g.get("gancho") or {}).get("pantalla") or ""]
    # el gancho
    ga = g.get("gancho") or {}
    uno = next((c for c in cs if c.get("puesto") == 1), None)
    dias_v = [(float((datetime.date.fromisoformat(st["ventana"][0]) + datetime.timedelta(days=k)).day), None) for k in range(DIAS)]
    vals_g = sorted({x for c in cs if c.get("puesto") != 1 and c.get("cifra_id") in cifras for x in NT.respaldo_de(por_nt.get(c.get("noticia")) or {})} | set(dias_v), key=lambda x: x[0])
    textos_g = " ".join([ga.get("pantalla") or "", ga.get("texto") or ""])
    sin = NT.sueltos(textos_g, vals_g)
    if sin:
        fallas.append("N4 gancho: números sin respaldo (o de la #1): %s" % ", ".join(map(str, sin)))
    if uno and uno.get("cifra_id") in cifras:
        c1 = cifras[uno["cifra_id"]]
        todos = NT.sueltos(textos_g, dias_v)
        if len(NT.sueltos(textos_g, dias_v + respaldo_cifra(c1))) < len(todos):
            fallas.append("SM1 el gancho dice la cifra de la #1 (%s): la cuenta la guarda para el final" % c1.get("texto"))
        pal1 = {w for w in VD._plano(uno.get("titular")).split() if len(w) > 3}
        palg = {w for w in VD._plano(textos_g).split() if len(w) > 3}
        if pal1 and len(pal1 & palg) / len(pal1) >= 0.6:
            fallas.append("SM1 el gancho cuenta la #1 («%s»)" % uno.get("titular"))
        if ga.get("noticia") and ga.get("noticia") == uno.get("noticia"):
            fallas.append("SM1 el gancho muestra la foto de la #1")
    if not (ga.get("pantalla") or "").strip() or VD.palabras(ga.get("pantalla") or "") > NT.TITULAR_PALABRAS or len(ga.get("pantalla") or "") > NT.TITULAR_CARACTERES:
        fallas.append("SM9 gancho.pantalla: 1–%d palabras y ≤ %d caracteres" % (NT.TITULAR_PALABRAS, NT.TITULAR_CARACTERES))
    escenas = [("gancho_semana", ga, None)] + [("cifra_semana", c, c) for c in cs]
    sin_humana = 0
    for n, (tipo, e, c) in enumerate(escenas, 1):
        texto = e.get("texto") or ""
        if re.search(r"\ben suma\b", texto, re.I):
            fallas.append("N4 escena %d: «en suma» está prohibido" % n)
        cv = NT.convertir(texto, n, fallas, tipo)
        for k, x in enumerate(fallas):
            if x.startswith("N5 escena %d " % n):
                fallas[k] = "SM5" + x[2:]
        if cv is None:
            continue
        nt = por_nt.get((c or {}).get("noticia")) if c else por_nt.get(ga.get("noticia") or (cs[0].get("noticia") if cs else None))
        if c:
            nid, cid = c.get("noticia"), c.get("cifra_id")
            if not nt:
                fallas.append("SM3 escena %d: la noticia %s no está en noticias.json (semana.py consolidar)" % (n, nid))
                continue
            bc = cifras.get(cid)
            # SM3 confirmada (o dato oficial) y la cita trae el valor
            if nt.get("estado") != "confirmada":
                fallas.append("SM3 escena %d: %s está «%s»: en /semana solo entran confirmadas o datos oficiales" % (n, nid, nt.get("estado")))
            if not bc or bc.get("noticia") != nid:
                fallas.append("SM3 escena %d: cifra_id %s no es una cifra de %s" % (n, cid, nid))
                continue
            if NT.sueltos(bc.get("texto") or "", [(x, None) for x in NT.numeros_cita(bc.get("cita"))]) or not isinstance(bc.get("valor"), (int, float)):
                fallas.append("SM3 escena %d: la cita de %s no trae su valor %s" % (n, cid, bc.get("valor")))
            ctx = (e.get("cifra") or {}).get("texto") or ""
            if not ctx or NT.sueltos(ctx, respaldo_cifra(bc)):
                fallas.append("SM3 escena %d: la cifra en pantalla «%s» no es el valor de %s (%s %s)" % (n, ctx, cid, bc.get("valor"), bc.get("unidad")))
            # SM2 en la semana
            pub = e.get("publicada")
            if not en_semana(pub, st):
                fallas.append("SM2 escena %d: publicada %s fuera de la semana %s → %s" % (n, pub, *st["ventana"]))
            elif pub != nt.get("publicada"):
                fallas.append("SM2 escena %d: publicada %s ≠ la de la noticia (%s)" % (n, pub, nt.get("publicada")))
            if not any(meta_fechada(f, st) for f in nt.get("fuentes") or []):
                fallas.append("SM2 escena %d: ninguna fuente de %s guardada con fecha en la semana (noticias.py leer)" % (n, nid))
            # N4 números de voz, titular y humana
            extra, motivos = valores_calculo(e.get("calculo"), cifras)
            fallas += ["SM8 escena %d: %s" % (n, m) for m in motivos]
            vals = NT.respaldo_de(nt) + [(round(x, 6), None) for x in extra] + [(float(k), None) for k in VD.CONSTANTES_CALCULO]
            for etiqueta, t in (("voz", texto), ("titular", e.get("titular") or "")):
                s_ = NT.sueltos(t, vals)
                if s_:
                    fallas.append("N4 escena %d (%s): números sin cita: %s" % (n, etiqueta, ", ".join(map(str, s_))))
            if NT.VETADAS.search(texto) and not nt.get("sentencia"):
                fallas.append("N4 escena %d: «%s» sin sentencia firme" % (n, NT.VETADAS.search(texto).group()))
            # SM8 escala humana
            hum = (e.get("humana") or "").strip()
            if hum:
                if len(hum) > HUMANA_CARACTERES:
                    fallas.append("SM8 escena %d: humana de %d caracteres (≤ %d)" % (n, len(hum), HUMANA_CARACTERES))
                s_ = NT.sueltos(hum, vals)
                if s_:
                    fallas.append("SM8 escena %d: humana con números sin cita ni calculo: %s" % (n, ", ".join(map(str, s_))))
            else:
                sin_humana += 1
            # SM6 repetida
            rep = repetida_en(e, nt, bc, prev)
            if rep:
                fallas.append("SM6 escena %d: la cifra «%s» ya salió en la semana %s" % (n, bc.get("texto"), rep))
            for v_, donde in otros:
                if abs(v_ - float(bc["valor"])) < 1e-9:
                    avisos.append("SM6 escena %d: %s ya salió en %s (últimos %d días)" % (n, bc.get("texto"), donde, AVISO_DIAS))
            # SM7 fuente
            fu = (e.get("fuente") or "").strip()
            if not 1 <= len(fu) <= NT.FUENTE_CARACTERES:
                fallas.append("SM7 escena %d: fuente en pantalla de 1–%d caracteres («%s»)" % (n, NT.FUENTE_CARACTERES, fu))
            elif not nombra_fuente(fu, nt):
                fallas.append("SM7 escena %d: la fuente «%s» no nombra un medio ni un organismo de la noticia" % (n, fu))
            # SM9 = N6 + N7
            tit = (e.get("titular") or "").strip()
            if not tit or VD.palabras(tit) > NT.TITULAR_PALABRAS or len(tit) > NT.TITULAR_CARACTERES:
                fallas.append("SM9 N6 escena %d: titular 1–%d palabras y ≤ %d caracteres («%s»)" % (n, NT.TITULAR_PALABRAS, NT.TITULAR_CARACTERES, tit))
            if not 1 <= len((e.get("seccion") or "").strip()) <= NT.SECCION_CARACTERES:
                fallas.append("SM9 N6 escena %d: seccion 1–%d caracteres" % (n, NT.SECCION_CARACTERES))
            cf = e.get("cifra") or {}
            if len(cf.get("texto") or "") > NT.CIFRA_CARACTERES or len(cf.get("etiqueta") or "") > NT.ETIQUETA_CARACTERES or not re.search(r"\d", cf.get("texto") or ""):
                fallas.append("SM9 N6 escena %d: cifra.texto con dígitos ≤ %d y etiqueta ≤ %d" % (n, NT.CIFRA_CARACTERES, NT.ETIQUETA_CARACTERES))
            foto = e.get("foto") or nt.get("foto") or {}
            if not foto.get("archivo") or not os.path.exists(os.path.join(trabajo, foto["archivo"])):
                fallas.append("SM9 N7 escena %d: cada cifra lleva la foto de su noticia en TRABAJO/fotos/" % n)
            else:
                fallas += ["SM9 N7 escena %d: %s" % (n, x) for x in NT.faltas_credito(foto)]
            if VD.valor_de(cf.get("texto") or "") is not None and not any(VD.valor_de(s["p"]) == VD.valor_de(cf["texto"]) for s in cv["segmentos"] if s["num"]):
                avisos.append("escena %d: la voz no dice la cifra %s" % (n, cf.get("texto")))
        hueco = VD.hueco_maximo(cv["segmentos"], cv["voz"])[0]
        loc.append({"n": n, "tipo": "titular" if tipo == "gancho_semana" else "noticia", "breve": False,
                    "noticia": (c or {}).get("noticia") if c else (ga.get("noticia") or (cs[0].get("noticia") if cs else None)),
                    "puesto": (c or {}).get("puesto"), "tuit": None, "plantilla": "noticia", "enlace": None,
                    "voz": cv["voz"], "prompt": cv["prompt"], "segmentos": cv["segmentos"], "pantalla": cv["pantalla"],
                    "estimado_s": round(len(cv["voz"]) / VD.CPS + VD.COLA, 2), "hueco_max_s": round(hueco, 2)})
    if len(cs) - sin_humana < HUMANA_MIN:
        fallas.append("SM8 %d cifras con `humana` (van ≥ %d)" % (len(cs) - sin_humana, HUMANA_MIN))
    # SM10 cierre
    ci = g.get("cierre") or {}
    res = ci.get("resumen") or []
    if len(res) != CIFRAS or any(len(r) > RESUMEN_CARACTERES for r in res):
        fallas.append("SM10 cierre.resumen: %d líneas ≤ %d caracteres (llegó %d)" % (CIFRAS, RESUMEN_CARACTERES, len(res)))
    for k, (r, c) in enumerate(zip(res, cs), 1):
        bc = cifras.get(c.get("cifra_id"))
        if bc and NT.sueltos((c.get("cifra") or {}).get("texto") or "", []) and NT.sueltos(r, respaldo_cifra(bc)) == NT.sueltos(r, []):
            fallas.append("SM10 cierre.resumen[%d] «%s» no lleva la cifra de la #%s (%s)" % (k, r, c.get("puesto"), bc.get("texto")))
    final = (ci.get("final") or "").strip()
    if not final or VD.palabras(final) > FINAL_PALABRAS:
        fallas.append("SM10 cierre.final: 1–%d palabras" % FINAL_PALABRAS)
    elif not VD._plano(ci.get("texto") or "").endswith(VD._plano(final)):
        fallas.append("SM10 cierre.final es la última frase de cierre.texto")
    if VD.CEBO.search(ci.get("texto") or ""):
        fallas.append("SM10 el cierre pide comentar o compartir («%s»): «Sígueme en» va solo en pantalla" % VD.CEBO.search(ci["texto"]).group())
    if VD.PROHIBIDO_CIERRE.search(ci.get("texto") or ""):
        fallas.append("SM10 la voz del cierre no dice fuentes ni «sígueme» (va en pantalla)")
    vals_c = sorted({x for v in por_nt.values() for x in NT.respaldo_de(v)}, key=lambda x: x[0])
    for etiqueta, t in [("texto", ci.get("texto") or "")] + [("resumen", r) for r in res]:
        s_ = NT.sueltos(t, vals_c)
        if s_:
            fallas.append("N4 cierre (%s): números sin cita: %s" % (etiqueta, ", ".join(map(str, s_))))
    n_c = len(escenas) + 1
    cv = NT.convertir(ci.get("texto") or "", n_c, fallas, "cierre_semana")
    for k, x in enumerate(fallas):
        if x.startswith("N5 escena %d " % n_c):
            fallas[k] = "SM5" + x[2:]
    if cv:
        loc.append({"n": n_c, "tipo": "cierre", "breve": False, "noticia": None, "puesto": None, "tuit": None, "plantilla": "cierre",
                    "enlace": None, "voz": cv["voz"], "prompt": cv["prompt"], "segmentos": cv["segmentos"], "pantalla": cv["pantalla"],
                    "estimado_s": round(len(cv["voz"]) / VD.CPS + VD.COLA_CIERRE, 2), "hueco_max_s": 0.0})
    # captions (V5) y SM11
    cap = g.get("caption") or {}
    for k, _ in VD.PLATAFORMAS:
        if not (cap.get(k) or "").strip():
            fallas.append("V5 falta caption.%s" % k)
    if cap.get("shorts") and (len(cap["shorts"].splitlines()[0]) > VD.SHORTS_TITULO or "#Shorts" not in cap["shorts"]):
        fallas.append("V5 caption.shorts: primera línea ≤ %d caracteres con #Shorts" % VD.SHORTS_TITULO)
    for k, v in cap.items():
        s_ = NT.sueltos(v or "", vals_c + dias_v)
        if s_:
            fallas.append("N4 caption.%s: números sin cita: %s" % (k, ", ".join(map(str, s_))))
    voz_g = loc[0]["voz"] if loc and loc[0]["tipo"] == "titular" else ""
    for clave in CLAVES:
        fallas += VD.revisar_palabra_clave([clave], voz_g, pantallas_g, cap, max_s=CLAVE_S, plataformas=CLAVES_PLATAFORMAS,
                                           codigo="SM11", donde="la pantalla del gancho (contexto o pantalla)")
    # SM5 duración estimada
    estimado = sum(x["estimado_s"] for x in loc) - VD.TRANSICION * (len(loc) - 1) + VD.BUCLE_S
    if not DURACION_MIN_S <= estimado <= DURACION_MAX_S:
        fallas.append("SM5 duración estimada %.0f s (van %d–%d s; objetivo %d)" % (estimado, DURACION_MIN_S, DURACION_MAX_S, OBJETIVO_S))
    return fallas, avisos, loc, estimado


def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    fallas, avisos, loc, estimado = validar_guion(trabajo)
    chars = sum(len(x["voz"]) for x in loc)
    print("escenas %d + cierre · voz %d caracteres · estimado %.0f s (%d–%d; objetivo %d)"
          % (max(0, len(loc) - 1), chars, estimado, DURACION_MIN_S, DURACION_MAX_S, OBJETIVO_S))
    for x in loc:
        print("E%-2d %-8s #%-2s %5.1fs  %s" % (x["n"], x["tipo"], x["puesto"] or "-", x["estimado_s"], x["voz"]))
    for x in avisos:
        print("AVISO", x)
    if fallas:
        for f in fallas:
            print("FALLA", f)
        return 1
    escribir(os.path.join(trabajo, "locucion.json"),
             {"voz": VD.VOZ, "caracteres": chars, "estimado_s": round(estimado, 1), "duracion": "semana",
              "objetivo_s": OBJETIVO_S, "n_escenas": len(loc) - 1, "promesa": None, "escenas": loc})
    print("→ %s · SM1–SM11, N4, V3, V5 ok" % VD.rel(os.path.join(trabajo, "locucion.json")))
    return 0


# ---------- tiempos ----------
def guion_adaptado(trabajo):
    """El guion de la semana en la forma que lee noticias.cmd_tiempos: cada cifra como una noticia con su chip
    («Economía», «mar 21 oct»), su puesto y su línea humana; el gancho con la ficha de la semana."""
    st = VD.estado(trabajo)
    g = leer(os.path.join(trabajo, "guion.json"))
    por_nt = {v["id"]: v for v in leer(os.path.join(trabajo, "noticias.json")).get("noticias") or []}
    nts = []
    for c in g["cifras"]:
        b = por_nt.get(c["noticia"]) or {}
        nts.append({"id": c["noticia"], "seccion": c.get("seccion"), "titular": c.get("titular"), "texto": c.get("texto"),
                    "cifra": c.get("cifra"), "fuente": c.get("fuente"), "foto": c.get("foto") or b.get("foto"),
                    "icono": c.get("icono") or b.get("icono"), "depto": c.get("depto") or b.get("depto"),
                    "chip": {"b": c.get("seccion"), "s": dia_corto(c["publicada"]) if c.get("publicada") else ""},
                    "puesto": c.get("puesto"), "humana": c.get("humana")})
    ga = dict(g.get("gancho") or {})
    ga.update(noticia=ga.get("noticia") or nts[0]["id"], ficha="Semana · %s" % rango_corto(st), conteo="%d cifras" % CIFRAS)
    return {"contexto_superior": g.get("contexto_superior"), "gancho": ga, "noticias": nts,
            "cierre": dict(g["cierre"], rotulo=g["cierre"].get("rotulo") or "La semana en Guatemala"), "caption": g.get("caption")}


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    g = guion_adaptado(trabajo)
    rc = NT.cmd_tiempos(argparse.Namespace(trabajo=trabajo), g)
    if rc:
        return rc
    ruta = os.path.join(trabajo, "escenas.json")
    E = leer(ruta)
    E["tipo"] = "semana"
    escribir(ruta, E)
    total = E["total_s"] + VD.BUCLE_S
    fallas = [x.replace("PISO", "SM5", 1) for x in VD.piso_duracion(total, st.get("piso_s") or PISO_S)]
    if total > DURACION_MAX_S:
        print("AVISO SM5 duración real %.1f s: pasa de %d s" % (total, DURACION_MAX_S))
    for clave in CLAVES:   # SM11 con los tiempos reales de la voz del gancho
        fallas += [x for x in VD.revisar_palabra_clave([clave], E["escenas"][0]["palabras"],
                                                       [g.get("contexto_superior") or "", g["gancho"].get("pantalla") or ""],
                                                       g.get("caption") or {}, max_s=CLAVE_S, plataformas=CLAVES_PLATAFORMAS,
                                                       codigo="SM11") if "voz" in x]
    for x in fallas:
        print("FALLA", x)
    print("semana %.1f s reales (piso %d, %d–%d)" % (total, st.get("piso_s") or PISO_S, DURACION_MIN_S, DURACION_MAX_S))
    return 1 if fallas else 0


# ---------- entregar ----------
def cifras_entrega(trabajo):
    """Las 5 cifras del guion con lo que respalda cada una (valor, unidad, cita, url, urls de la noticia)."""
    g = leer(os.path.join(trabajo, "guion.json"))
    base = leer(os.path.join(trabajo, "noticias.json"))
    por_nt, cifras = {v["id"]: v for v in base["noticias"]}, cifras_por_id(base)
    out = []
    for c in g["cifras"]:
        bc, nt = cifras.get(c["cifra_id"]) or {}, por_nt.get(c["noticia"]) or {}
        foto = c.get("foto") or nt.get("foto")
        out.append({"puesto": c["puesto"], "cifra_id": c["cifra_id"], "id_original": bc.get("id_original"), "noticia": c["noticia"],
                    "noticia_original": nt.get("id_original") or nt.get("id"), "diario": nt.get("diario"),
                    "seccion": c.get("seccion"), "titular": c.get("titular"), "texto": (c.get("cifra") or {}).get("texto"),
                    "etiqueta": (c.get("cifra") or {}).get("etiqueta"), "humana": c.get("humana"), "calculo": c.get("calculo"),
                    "fuente": c.get("fuente"), "publicada": c.get("publicada"), "valor": bc.get("valor"), "unidad": bc.get("unidad"),
                    "cita": bc.get("cita"), "url": bc.get("url"), "urls": [f.get("url") for f in nt.get("fuentes") or [] if f.get("url")],
                    # los números de las citas de su noticia (respaldan la línea humana fuera de sesiones/: /carrusel)
                    "respaldo": sorted({x for x, _ in NT.respaldo_de(nt)}),
                    "foto": {k: foto.get(k) for k in ("credito", "origen")} if foto else None})
    return out


def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    sal = os.path.join(trabajo, "salida")
    for f in ("video.mp4", "video_4x5.mp4", "subtitulos.srt", "caption.md", "portada.png"):
        if not os.path.exists(os.path.join(sal, f)):
            return falla("falta salida/%s: graba, monta y revisa (también --formato 4:5) antes de entregar" % f)
    ruta_cred = os.path.join(trabajo, "audio", "creditos.json")
    if not os.path.exists(ruta_cred) and not a.salida:
        return falla("sin audio/creditos.json: la voz no salió de ElevenLabs (una voz falsa solo se entrega con --salida)")
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, "semanas", st["fecha"]))
    os.makedirs(destino, exist_ok=True)
    for f in glob.glob(os.path.join(destino, "portada*.png")):
        os.remove(f)
    for f in ["video.mp4", "video_4x5.mp4", "subtitulos.srt", "caption.md"] + [os.path.basename(x) for x in glob.glob(os.path.join(sal, "portada*.png"))]:
        shutil.copy2(os.path.join(sal, f), os.path.join(destino, f))
    for f in ("contacto.png", "contacto_4x5.png"):
        if os.path.exists(os.path.join(trabajo, "revision", f)):
            shutil.copy2(os.path.join(trabajo, "revision", f), os.path.join(destino, f))
    g, loc, E = (leer(os.path.join(trabajo, x)) for x in ("guion.json", "locucion.json", "escenas.json"))
    critica = None
    if os.path.exists(os.path.join(trabajo, "critica.json")):
        c = leer(os.path.join(trabajo, "critica.json"))
        critica = {"veredicto": c.get("veredicto"), "vuelta": c.get("vuelta"), "puntajes": c.get("puntajes")}
    else:
        print("AVISO sin critica.json: la semana se entrega sin la revisión del crítico")
    cos = leer(os.path.join(trabajo, "cosecha.json")) if os.path.exists(os.path.join(trabajo, "cosecha.json")) else {}
    cifras = cifras_entrega(trabajo)
    entrega = {"id": st.get("id") or semana_iso(st["fecha"]), "tipo": "semana", "fecha": st["fecha"], "ventana": st["ventana"],
               "paleta": st["paleta"], "musica": st["musica"], "voz": loc["voz"], "velocidad": VD.VELOCIDAD,
               "creditos_voz": leer(ruta_cred)["total"] if os.path.exists(ruta_cred) else None,
               "duracion_s": round(VD.ffprobe_dur(os.path.join(destino, "video.mp4")), 1), "critica": critica,
               "fixture": bool(st.get("fixture")), "sin_noticiero": cos.get("sin_noticiero") or [],
               "contexto_superior": g.get("contexto_superior"), "gancho": g["gancho"], "cifras": cifras,
               "escenas": [{"n": e["n"], "tipo": e["tipo"], "puesto": e.get("puesto"), "pantalla": e["pantalla"], "voz": e["voz"],
                            "dur": s_["dur"]} for e, s_ in zip(loc["escenas"], E["escenas"])],
               "cierre": g["cierre"], "caption": g["caption"]}
    escribir(os.path.join(destino, "guion.json"), entrega)
    lineas = ["# Fuentes · las 5 cifras de la semana %s → %s" % tuple(st["ventana"]), "",
              "Para el primer comentario o la descripción. Cada cifra con la cita que la trae y las fuentes de su noticia.", ""]
    for c in cifras:
        lineas += ["%d. **#%d · %s** (%s, %s): %s" % (6 - c["puesto"], c["puesto"], c["titular"], c["seccion"], c["publicada"], c["texto"]),
                   "   - «%s»" % c["cita"]] + ["   - %s" % u for u in c["urls"]]
        if c["foto"]:
            lineas.append("   - %s" % c["foto"]["credito"])
    lineas += ["", "Sígueme: %s" % " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES)]
    open(os.path.join(destino, "fuentes.md"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("entregado en %s (%.1f s) · video.mp4 + video_4x5.mp4 · caption.md · fuentes.md%s"
          % (VD.rel(destino), entrega["duracion_s"], "" if entrega["creditos_voz"] is None else " · %s créditos de voz" % entrega["creditos_voz"]))
    if entrega["duracion_s"] < PISO_S:
        print("AVISO SM5 dura %.0f s: debajo de %d s" % (entrega["duracion_s"], PISO_S))
    return 0


# ---------- carrusel (la interfaz con /carrusel) ----------
def entrega_de(carpeta):
    """(guion de entrega con cifras completas, ruta) de una semana entregada (semanas/<fecha>/) o de un TRABAJO."""
    d = os.path.abspath(carpeta if os.path.isabs(carpeta) else os.path.join(RAIZ, carpeta))
    g = leer(os.path.join(d, "guion.json"))
    if g.get("tipo") != "semana":
        raise ValueError("%s/guion.json no es de /semana" % VD.rel(d))
    if not all(isinstance(c.get("valor"), (int, float)) for c in g.get("cifras") or []):
        if not os.path.exists(os.path.join(d, "noticias.json")):
            raise ValueError("%s: las cifras no traen su valor (ni hay noticias.json para buscarlo)" % VD.rel(d))
        g = dict(g, cifras=cifras_entrega(d), id=VD.estado(d).get("id"), fixture=bool(VD.estado(d).get("fixture")))
    return g, d


def base_carrusel(carpeta, base):
    """TRABAJO/base/ de /carrusel desde una semana: hilo.json sin imágenes (las láminas son `texto`) y datos.json con las
    5 cifras verificadas (veredicto verificada, su valor y su cita). Lo llama carrusel.py preparar (origen semana)."""
    g, _ = entrega_de(carpeta)
    os.makedirs(base, exist_ok=True)
    # los puestos de la cuenta (1–5) y las constantes que usa una línea humana con `calculo` («por cada Q1,000») no son
    # cifras de una fuente: van aparte, con su concepto, para que CA4 no los tome por números sin respaldo
    usadas = sorted({k for c in g["cifras"] if c.get("calculo") for k in VD.CONSTANTES_CALCULO
                     if NT.sueltos(c.get("humana") or "", [(float(k), None)]) != NT.sueltos(c.get("humana") or "", [])})
    escribir(os.path.join(base, "datos.json"), {"cifras": [
        {"id": c["cifra_id"], "concepto": c["titular"], "valor": c["valor"], "unidad": c.get("unidad"), "periodo": c.get("publicada"),
         "veredicto": "verificada", "valor_final": c["valor"], "evidencia": {"url": c.get("url"), "cita": c.get("cita")},
         "partes": [{"nombre": "cita", "valor": x} for x in c.get("respaldo") or []]}
        for c in g["cifras"]] + [
        {"id": "sm-c00", "concepto": "puestos de la cuenta regresiva (5 → 1) y constantes de los cálculos", "valor": CIFRAS,
         "unidad": "puesto", "veredicto": "verificada", "valor_final": CIFRAS,
         "partes": [{"nombre": "puesto", "valor": k} for k in PUESTOS] + [{"nombre": "constante", "valor": k} for k in usadas]}]})
    escribir(os.path.join(base, "hilo.json"), {
        "slug": "semana-" + g["fecha"], "fecha": g["fecha"], "tema": "Las 5 cifras de la semana en Guatemala (%s → %s)" % tuple(g["ventana"]),
        "tesis": "", "paleta": g.get("paleta") or PALETA_SEMANA, "estado": "listo" if not g.get("fixture") else "borrador",
        "modo": "semana", "no_afirma": [],
        "tuits": [{"n": k, "imagen": None, "plantilla": None, "cifra_ids": [c["cifra_id"]], "beat": "impacto",
                   "texto": c["titular"], "alt_text": "", "fuente": c.get("fuente")} for k, c in enumerate(g["cifras"], 1)]})
    return g


def carrusel_json(g, origen):
    """Un carrusel de 8 láminas desde las 5 cifras: portada (la #1 en grande), una lámina `texto` por cifra en el orden
    de la cuenta, «Por qué importa» y el cierre. Pasa CA1–CA8 tal cual; la sesión puede pulir el texto."""
    cs = sorted(g["cifras"], key=lambda c: -c["puesto"])
    uno = cs[-1]
    rango = "%s–%s" % (dia_corto(g["ventana"][0]), dia_corto(g["ventana"][1]))
    laminas = [{"tipo": "portada", "contexto": "Guatemala · semana %s" % rango_corto({"ventana": g["ventana"]}),
                "cifra": uno["texto"].replace(" ", ""), "titulo": "Las 5 cifras de la semana", "fuente": uno["fuente"],
                "cifra_ids": [uno["cifra_id"]]}]
    def millones(t):   # «Q6,200 millones» → «Q6.2 mil millones» (la coma de miles ante «millones» se lee como decimal de prensa)
        return re.sub(r"(\d{1,3}),(\d{3})\s+millones", lambda m: "%s mil millones" % ("%g" % (float(m.group(1) + m.group(2)) / 1000)), t or "")
    resumen = g["cierre"].get("resumen") or []
    for k, c in enumerate(cs):
        # el golpe es la línea del cierre (lleva la cifra: es lo que se enciende); el cuerpo, el titular y la escala humana
        golpe = resumen[k] if k < len(resumen) else c["titular"]
        cuerpo = " ".join(x for x in ["%s." % c["titular"].rstrip("."), millones(c.get("humana"))] if x).strip()
        laminas.append({"tipo": "texto", "golpe": "%d. %s" % (c["puesto"], golpe), "cuerpo": cuerpo, "fuente": c["fuente"],
                        "cifra_ids": [c["cifra_id"]], **({"calculo": c["calculo"]} if c.get("calculo") else {})})
    laminas.append({"tipo": "porque", "cuerpo": "Cinco números verificados de la semana en Guatemala, de cinco temas distintos: lo que pasó, contado con su fuente.",
                    "fuente": " · ".join(sorted({c["fuente"].split("·")[0].strip() for c in cs}))[:60]})
    laminas.append({"tipo": "cierre", "frase": (g["cierre"].get("final") or "La semana en cinco números.")})
    alt = {"1": "Portada: las 5 cifras de la semana en Guatemala, del %s. La número 1: %s, %s." % (rango, uno["texto"], uno["titular"])}
    for k, c in enumerate(cs, 2):
        alt[str(k)] = "Puesto %d de la semana: %s. %s. Fuente: %s." % (c["puesto"], c["titular"], c["texto"], c["fuente"])
    alt[str(len(laminas) - 1)] = "Por qué importa: cinco números verificados de la semana en Guatemala, cada uno con su fuente."
    alt[str(len(laminas))] = "Cierre: %s Guárdalo y sígueme para la próxima semana." % (g["cierre"].get("final") or "")
    lista = ", ".join("%s (%s)" % (c["texto"], c["seccion"].lower()) for c in cs)
    return {"version": 1, "origen": origen, "slug": "semana-" + g["fecha"], "paleta": g.get("paleta") or PALETA_SEMANA,
            "palabra_clave": "semana", "portada_forma": "cifra", "laminas": laminas,
            "caption": {"tiktok": "Las 5 cifras de la semana en Guatemala, del %s. %s. #Guatemala #Semana" % (rango, lista),
                        "instagram": "Las 5 cifras de la semana en Guatemala (%s)\nDesliza: %s. Guárdalo. #Guatemala" % (rango, lista),
                        "facebook": "Las 5 cifras de la semana en Guatemala, del %s, con su fuente: %s." % (rango, lista)},
            "alt": alt}


def cmd_carrusel(a):
    """La semana → un TRABAJO de /carrusel (carrusel.py preparar con el origen semana) con su carrusel.json escrito y
    pasado por `carrusel.py guion --check`."""
    try:
        g, d = entrega_de(a.carpeta)
    except (ValueError, FileNotFoundError) as ex:
        return falla(str(ex))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "semana-" + g["fecha"], "carrusel"))
    cmd = [sys.executable, os.path.join(RAIZ, "scripts", "carrusel.py"), "preparar", VD.rel(d), "--trabajo", trabajo]
    if a.fixture or g.get("fixture"):
        cmd.append("--fixture")
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True)
    if r.returncode:
        return falla("carrusel.py preparar: %s" % (r.stderr or r.stdout).strip()[-400:])
    st = leer(os.path.join(trabajo, "estado.json"))
    escribir(os.path.join(trabajo, "carrusel.json"), carrusel_json(g, st["origen"]))
    rc = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "carrusel.py"), "guion", trabajo, "--check"], cwd=RAIZ).returncode
    if rc:
        return falla("el carrusel.json de la semana no pasa CA1–CA8: corrígelo en %s" % VD.rel(trabajo))
    print("→ %s · siguiente: python3 scripts/carrusel.py render %s (y --formato 9:16), luego entregar"
          % (VD.rel(os.path.join(trabajo, "carrusel.json")), VD.rel(trabajo)))
    return 0


# ---------- main ----------
A_NOTICIAS = ("leer", "foto", "fotos-contacto")
A_VIDEO = ("voz", "voz-falsa", "descargar", "escuchar", "grabar", "montar", "revisar")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in A_NOTICIAS + A_VIDEO:
        script = "noticias.py" if sys.argv[1] in A_NOTICIAS else "video.py"
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", script)] + sys.argv[1:], cwd=RAIZ).returncode
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("preparar")
    q.add_argument("--fecha")
    q.add_argument("--trabajo")
    q.add_argument("--diarios", help="carpeta con noticias-<día>/ (por defecto sesiones/)")
    q.add_argument("--memoria", help="registro de semanas para SM6 (por defecto memoria/semanas.json)")
    q.add_argument("--paleta")
    q.add_argument("--musica")
    q.add_argument("--fixture", action="store_true")
    sub.add_parser("cosechar").add_argument("trabajo")
    q = sub.add_parser("candidatas")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--seccion", choices=list(SECCIONES))
    q = sub.add_parser("verificacion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q.add_argument("--id")
    sub.add_parser("consolidar").add_argument("trabajo")
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--para", choices=["rastreador", "verificador", "editor"], default="editor")
    q.add_argument("--id")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    sub.add_parser("tiempos").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida")
    q = sub.add_parser("carrusel")
    q.add_argument("carpeta", help="semanas/<domingo>/ (entregada) o un TRABAJO de /semana")
    q.add_argument("--trabajo")
    q.add_argument("--fixture", action="store_true")
    for nombre in A_NOTICIAS + A_VIDEO:
        sub.add_parser(nombre, help="→ scripts/%s %s" % ("noticias.py" if nombre in A_NOTICIAS else "video.py", nombre))
    a = p.parse_args()
    return {"preparar": cmd_preparar, "cosechar": cmd_cosechar, "candidatas": cmd_candidatas, "verificacion": cmd_verificacion,
            "consolidar": cmd_consolidar, "digesto": cmd_digesto, "guion": cmd_guion, "tiempos": cmd_tiempos,
            "entregar": cmd_entregar, "carrusel": cmd_carrusel}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
