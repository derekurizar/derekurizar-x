#!/usr/bin/env python3
"""/congreso: una ley del Congreso de Guatemala en un video vertical de menos de un minuto (TikTok / Reels / Shorts) y
su 4:5: qué buscaba, cuántos votos tuvo a favor y en contra frente al umbral, y algunos diputados de cada lado.

Los votos salen del registro nominal oficial (congreso.gob.gt, capturado con Claude in Chrome: referencias/congreso/
captura.md) y viven en una base local (sesiones/_congreso/base/{votaciones,votos}.csv, la misma de la investigación
«Cómo vota el Congreso»). El guion lo escribe la sesión con el digesto; el gate (CG1–CG10 + V1–V5, V9, F1–F8, R) y el
resto (voz, tiempos, grabar, montar, revisar) son los de scripts/video.py con la escena propia `hemiciclo`
(video/hemiciclo.html) y las escenas `foto` y `cita` de /historia enchufadas. Guía: referencias/flujo-congreso.md.

Subcomandos (TRABAJO = sesiones/congreso-<slug>):
  importar CAPTURA.json [--dry-run]   la captura de Chrome → base (CG1: 160 filas, sin duplicados, cada nombre en el
        padrón, cada voto conocido; una votación que ya está en la base se coteja voto por voto)
  padron CAPTURA.json                 referencias/congreso/diputados.json (id, nombre, nombres/apellidos, bancada, foto)
  proponer [--dias 21] [--n 6]        las leyes votadas en los últimos días, con su votación decisiva y su margen
  preparar <iniciativa> [--slug S] [--trabajo DIR] [--paleta P] [--musica ID] [--fixture] [--semilla DIR]
        TRABAJO + votación decisiva (votacion.json, base/datos.json con las cifras cg-cNN) + digesto.md
  ley TRABAJO --check                 CG2: ley.json (qué buscaba, estado, citas) con cada cita literal en su texto guardado
  leer TRABAJO CAPTURA.json           textos y fotos capturados en Chrome (CG.textos, CG.pdfs) → sesiones/_descargas/congreso/
        (el archivo de ley.json) y TRABAJO/fotos/ley-fNN.jpg con «Foto: Congreso de la República»
  fotos TRABAJO [--captura CAPTURA.json] [--diputados "Nombre" …]   retratos oficiales → TRABAJO/fotos/dip-<id>.jpg
  digesto TRABAJO                     vuelve a escribir e imprimir digesto.md (con ley.json y las fotos)
  guion TRABAJO --check               CG3–CG10 + video.py guion (V1–V5, V9, F1–F8) → locucion.json
  tiempos TRABAJO                     video.py tiempos con la escena hemiciclo → escenas.json (CG7: ≤ 59.5 s reales)
  entregar TRABAJO [--salida DIR]     → congreso/<fecha>-<slug>/ (video, 4:5, caption, fuentes.md, votos.csv)
  voz | voz-falsa | descargar | escuchar | grabar | montar | revisar TRABAJO [...]   → video.py

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import base64
import collections
import contextlib
import csv
import datetime
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402

BASE = os.path.join(RAIZ, "sesiones", "_congreso", "base")
CAPTURAS = os.path.join(RAIZ, "sesiones", "_congreso", "capturas")
PADRON = os.path.join(RAIZ, "referencias", "congreso", "diputados.json")
RETRATOS = os.path.join(RAIZ, "design", "diputados")          # caché de retratos oficiales (crece con el uso)
DESCARGAS = os.path.join(RAIZ, "sesiones", "_descargas", "congreso")
REGISTRO = os.path.join(RAIZ, "memoria", "congreso.json")
ORIGEN = "https://www.congreso.gob.gt"
CREDITO_RETRATO = "Foto: Congreso de la República"

TOTAL = 160
MAYORIA = 81            # mayoría absoluta del total (Ley Orgánica, art. 99)
CALIFICADA = 107        # dos tercios: urgencia nacional, dispensa, rechazo de veto, leyes constitucionales
VOTOS = ("favor", "contra", "ausente", "licencia")
# el umbral es ley, no un dato de la votación: su respaldo es la Ley Orgánica (texto guardado por la investigación N.º 03)
LEY_ORGANICA = {"url": "https://www.oas.org/es/sla/dlc/mesicic/docs/mesicic5_gtm_anexo2.pdf",
                "archivo": "sesiones/como-vota-el-congreso/base/contexto/fuentes/ley-organica-63-94-oea.txt"}

# ---- formato (decisión del usuario, 2026-11-04): menos de un minuto ----
OBJETIVO_S, TOL = 50, 0.14            # V4: 43–57 s estimados
TECHO_S = 59.5                        # CG7: duración real (con el bucle) por debajo del minuto
VD.DURACIONES["congreso"] = {"s": OBJETIVO_S, "tarjetas": (0, 0), "golpes": (0, 3), "tol": TOL}
ESCENAS = (4, 8)                      # gancho … (más el cierre)
TIPOS_PROPIOS = ("hemiciclo", "foto", "cita")
CARACTERES = {"hemiciclo": (40, 260), "foto": (30, 210), "cita": (30, 210)}
NOMBRES_POR_LADO = 3                  # CG4 (usuario, 2026-11-04): hasta 3 por lado, cada uno de un partido distinto
PESO_HOLGURA = 1                      # CG4: el partido del nombrado está entre los N + 1 que más votos dieron a ese lado
PALETAS = ("obsidiana", "cielo", "jade", "terracota", "cacao", "jacaranda", "atitlan", "maiz")
FASES = ("llenar", "umbral", "foco", "barras")
# CG5: el registro dice quién votó qué; el video no califica a nadie
PROHIBIDAS = re.compile(r"\b(traidor\w*|vendid[oa]s|corrupt[oa]s?|ladr[oó]n\w*|rata\w*|sinverg[uü]enza\w*|"
                        r"de siempre|los mismos de siempre|pacto de corruptos|bodoque\w*|vergonzos\w*|descarad\w*|"
                        r"cínic\w*|cinic\w*|mafia\w*|se vendieron|les pagaron|a escondidas|madrugonazo\w*)\b", re.I)
VERBOS_LEY = re.compile(r"\b(busca\w*|pretend\w*|propon\w*|propuso|obliga\w*|prohib\w*|permit\w*|crea\w*|establec\w*|"
                        r"reform\w*|aument\w*|reduc\w*|quita\w*|elimin\w*|autoriz\w*)\b", re.I)
RE_INICIATIVA = re.compile(r"INICIATIVA(?:\s+DE\s+LEY)?(?:\s+N[ÚU]MERO)?\s+(\d{3,5})|URGENCIA NACIONAL\s+(\d{3,5})", re.I)
DECISIVAS = (("redaccion final", "REDACCIÓN FINAL"), ("unico debate", "ÚNICO DEBATE"), ("tercer debate", "TERCER DEBATE"))
ORIGINALES = {}
TRABAJO_ACTUAL = None
VOT = None        # votacion.json del TRABAJO en curso (lo leen los constructores)
LEY = None


# ---------- utilidades ----------
def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def falla(msg):
    print("ERROR: " + msg, file=sys.stderr)
    return 1


def plano(s):
    s = unicodedata.normalize("NFD", str(s or "")).lower()
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ ]+", " ", s.replace("ñ", "n")).split()


def clave_nombre(s):
    return " ".join(sorted(plano(s)))


def slug_de(s):
    return "-".join(plano(s))[:60].strip("-")


def leer_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def votaciones_base():
    return leer_csv(os.path.join(BASE, "votaciones.csv"))


def votos_de(ids):
    ids = {str(i) for i in ids}
    out = collections.defaultdict(list)
    with open(os.path.join(BASE, "votos.csv"), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["id_votacion"] in ids:
                out[r["id_votacion"]].append(r)
    return out


def bancadas_actuales():
    """{clave_nombre: {nombre, bloque, distrito}} con la bancada de la votación más reciente de cada diputado."""
    fecha = {r["id_votacion"]: r["fecha_votacion"] for r in votaciones_base()}
    out = {}
    with open(os.path.join(BASE, "votos.csv"), encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k, fv = clave_nombre(r["diputado"]), fecha.get(r["id_votacion"], "")
            if k not in out or fv > out[k]["_f"]:
                out[k] = {"nombre": r["diputado"], "bloque": r["bloque"], "distrito": r["distrito"], "_f": fv}
    return out


def padron():
    return leer(PADRON)["diputados"] if os.path.exists(PADRON) else []


def partir_nombre(base_nombre, sitio_nombre):
    """«Nombres Apellidos» (base) y «Apellidos Nombres» (sitio) → (nombres, apellidos) como listas de palabras."""
    b, s = base_nombre.split(), sitio_nombre.split()
    for k in range(1, len(b)):
        if [plano(x) for x in s[:len(b) - k]] == [plano(x) for x in b[k:]]:
            return b[:k], b[k:]
    return b[:max(1, len(b) // 2)], b[max(1, len(b) // 2):]


def nombre_corto(d):
    """«Luis Aguirre»: primer nombre + primer apellido («de León», «De La Rosa» se conservan enteros)."""
    nom, ape = d.get("nombres") or d["nombre"].split()[:1], d.get("apellidos") or d["nombre"].split()[1:]
    primero, ap = nom[0], []
    for w in ape:
        ap.append(w)
        if plano(w) and plano(w)[0] not in ("de", "del", "la", "las", "los", "y"):
            break
    return " ".join([primero] + ap)


def bancada_legible(b):
    """«INDP - SEMILLA» → «Semilla (independientes)»; «VAMOS» → «Vamos»; «WINAQ - URNG» → «Winaq-URNG»."""
    b = (b or "").strip()
    m = re.match(r"INDP\s*-\s*(.+)", b, re.I)
    if m:
        return "independientes ex %s" % bancada_legible(m.group(1)) if plano(m.group(1)) != ["semilla"] else "Semilla (independientes)"
    siglas = {"UNE", "URNG", "VOS", "CREO", "PU"}
    return "-".join(" ".join(w if w.upper() in siglas else w.capitalize() for w in p.split()) for p in re.split(r"\s*-\s*", b))


def partido(b):
    """La familia de partido de una bancada: «INDP - UNE» (los que dejaron la UNE) cuenta como UNE, para que dos nombres
    «de distintos partidos» no sean la UNE y sus ex."""
    b = (b or "").strip()
    m = re.match(r"INDP\s*-\s*(.+)", b, re.I)
    return (m.group(1) if m else b).strip().upper()


def partidos_lado(D, lado):
    """[(partido, votos, [diputados])] de un lado de la votación, de más a menos votos (CG4: los que más pesaron)."""
    g = collections.OrderedDict()
    for d in D["diputados"]:
        if d["voto"] == lado:
            g.setdefault(partido(d["bancada"]), []).append(d)
    return sorted(((p, len(ds), ds) for p, ds in g.items()), key=lambda x: (-x[1], x[0]))


def nombres_requeridos(D, lado):
    """CG4: cuántos nombres van de ese lado: 3, o menos si votaron menos partidos; 0 del lado en contra si nadie votó en contra."""
    return min(NOMBRES_POR_LADO, len(partidos_lado(D, lado)))


def partidos_de_peso(D, lado):
    """Los partidos «importantes en la votación» de ese lado: los N + 1 con más votos (con empates)."""
    ps = partidos_lado(D, lado)
    k = min(len(ps), nombres_requeridos(D, lado) + PESO_HOLGURA)
    corte = ps[k - 1][1] if k else 0
    return [p for p, n, _ in ps if n >= corte]


# ---------- importar y padrón ----------
def indice_nombres(pad=None):
    """{clave: {nombre, bloque, distrito, id?}}: la base manda (nombre canónico y bancada actual); el padrón completa."""
    idx = {k: dict(v) for k, v in bancadas_actuales().items()}
    for d in pad if pad is not None else padron():
        for k in {clave_nombre(d.get("nombre_sitio") or ""), clave_nombre(d.get("nombre") or "")} - {""}:
            if k in idx:
                idx[k]["id"] = d.get("id")
            else:
                idx[k] = {"nombre": d.get("nombre"), "bloque": d.get("bancada") or d.get("bloque_sitio") or "", "distrito": d.get("distrito", ""), "id": d.get("id")}
    return idx


def cmd_padron(a):
    caps = [leer(x) for x in a.captura]
    cap = next((c for c in caps if c.get("padron")), {})
    cap = dict(cap, sesiones=[s for c in caps for s in c.get("sesiones") or []])
    filas = cap.get("padron") or []
    if len(filas) != TOTAL:
        print("AVISO el padrón trae %d diputados (se esperaban %d)" % (len(filas), TOTAL))
    base = bancadas_actuales()
    previo = {d["id"]: d for d in padron()}
    # el listado nominal escribe «Apellidos Nombres»: con él se parte el nombre (para decir «Luis Aguirre»)
    invertidos = {clave_nombre(f["nombre"]): f["nombre"] for s in cap.get("sesiones") or [] for v in s.get("votaciones") or []
                  for f in v.get("filas") or []}
    out, sin = [], []
    tomados = {clave_nombre(p["nombre"]) for p in filas if clave_nombre(p["nombre"]) in base}
    for p in filas:
        b = base.get(clave_nombre(p["nombre"]))
        if not b:   # un apodo en la portada («Willy Ralda»): el de la base del mismo distrito con sus apellidos
            toks = set(plano(p["nombre"])[1:])
            cand = [v for k, v in base.items() if k not in tomados and toks and toks <= set(plano(v["nombre"]))
                    and plano(v["distrito"]) == plano(p.get("distrito"))]
            b = cand[0] if len(cand) == 1 else None
        nombre = b["nombre"] if b else p["nombre"]
        if not b:
            sin.append(p["nombre"])
        inv = invertidos.get(clave_nombre(p["nombre"])) or (previo.get(p["id"]) or {}).get("nombre_listado")
        nom, ape = partir_nombre(nombre, inv) if inv else ((previo.get(p["id"]) or {}).get("nombres"), (previo.get(p["id"]) or {}).get("apellidos"))
        d = {"id": p["id"], "nombre": nombre, "nombres": nom, "apellidos": ape, "nombre_listado": inv,
             "bancada": b["bloque"] if b else p["bloque"], "bloque_sitio": p["bloque"],
             "distrito": p.get("distrito") or (b or {}).get("distrito", ""), "miniatura": p.get("miniatura", ""), "url": p.get("url", ""),
             "notoriedad": (previo.get(p["id"]) or {}).get("notoriedad", "")}
        out.append(d)
    escribir(PADRON, {"corte": cap.get("capturado", "")[:10], "fuente": ORIGEN + "/ (tarjetas de diputados)",
                      "_comentario": "Lo escribe scripts/congreso.py padron. «bancada» es la de la votación más reciente en la "
                                     "base (la del sistema de votación); «bloque_sitio» la de la portada del Congreso. "
                                     "«notoriedad» la llena la sesión (cargo, por qué se le conoce) y ayuda a elegir a quién nombrar.",
                      "diputados": out})
    print("padrón: %d diputados → %s%s" % (len(out), VD.rel(PADRON), (" · sin votos en la base: " + ", ".join(sin)) if sin else ""))
    return 0


def nombres_sitio(cap):
    """{clave del nombre del sitio («Apellidos Nombres»): diputado del padrón}."""
    out = {}
    for d in padron():
        out[clave_nombre(d["nombre"])] = d
    return out


def cmd_importar(a):
    cap = leer(a.captura)
    idx = indice_nombres()
    vot = votaciones_base()
    por_fecha = {(r["fecha_votacion"], str(int(r["no_votacion"]))): r for r in vot}
    nuevas_v, nuevos_votos, fallas, cotejadas = [], [], [], 0
    urls = leer(os.path.join(BASE, "indice.json")) if os.path.exists(os.path.join(BASE, "indice.json")) else {"capturas": [], "urls": {}}
    for s in cap.get("sesiones") or []:
        for v in s.get("votaciones") or []:
            et = "sesión %s · votación %s (%s)" % (s.get("no_sesion"), v.get("no_votacion"), v.get("fecha_votacion"))
            filas = v.get("filas") or []
            # CG1: el listado nominal completo y sin sorpresas
            if len(filas) != TOTAL:
                fallas.append("CG1 %s: %d filas (van %d)" % (et, len(filas), TOTAL))
            dup = [k for k, n in collections.Counter(clave_nombre(f["nombre"]) for f in filas).items() if n > 1]
            if dup:
                fallas.append("CG1 %s: nombres repetidos: %s" % (et, ", ".join(dup)))
            raros = sorted({f["voto"] for f in filas} - set(VOTOS))
            if raros:
                fallas.append("CG1 %s: votos desconocidos: %s" % (et, ", ".join(raros)))
            filas_ok = []
            for f in filas:
                d = idx.get(clave_nombre(f["nombre"]))
                if not d:
                    fallas.append("CG1 %s: «%s» no está en la base ni en el padrón (corre `padron` con una captura nueva)" % (et, f["nombre"]))
                    continue
                filas_ok.append({"diputado": d["nombre"], "bloque": d["bloque"], "distrito": d["distrito"], "voto": f["voto"]})
            cuenta = collections.Counter(f["voto"] for f in filas)
            clave_v = (v.get("fecha_votacion", ""), str(int(v.get("no_votacion") or 0)))
            urls["urls"][str(v["id_votacion"])] = {"url": v.get("url"), "pdf": v.get("pdf"), "pregunta": v.get("pregunta")}
            previa = por_fecha.get(clave_v)
            if previa:   # ya está en la base: se coteja (la captura reproduce el xlsx oficial)
                cotejadas += 1
                for k in VOTOS:
                    if int(previa[k]) != cuenta.get(k, 0):
                        fallas.append("CG1 %s: la base dice %s %s y el sitio %d" % (et, previa[k], k, cuenta.get(k, 0)))
                continue
            nuevas_v.append({"id_sesion": s["id_sesion"], "tipo_sesion": s.get("tipo_sesion", ""), "no_sesion": s.get("no_sesion", ""),
                             "fecha_sesion": s.get("fecha_sesion", ""), "id_votacion": v["id_votacion"], "no_votacion": v.get("no_votacion", ""),
                             "fecha_votacion": v.get("fecha_votacion", ""), "pregunta": v.get("pregunta", ""), "pregunta_xlsx": v.get("pregunta", ""),
                             "n_diputados": len(filas), **{k: cuenta.get(k, 0) for k in VOTOS}, "archivo": "web:" + (v.get("url") or "")})
            nuevos_votos += [dict(id_votacion=v["id_votacion"], **f) for f in filas_ok]
    for x in fallas:
        print("FALLA", x)
    print("captura %s: %d votaciones nuevas, %d cotejadas con la base" % (os.path.basename(a.captura), len(nuevas_v), cotejadas))
    if fallas:
        return 1
    if a.dry_run or not nuevas_v:
        return 0
    ruta_v, ruta_d = os.path.join(BASE, "votaciones.csv"), os.path.join(BASE, "votos.csv")
    cab_v = list(leer_csv(ruta_v)[0].keys())
    with open(ruta_v, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=cab_v).writerows(nuevas_v)
    with open(ruta_d, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=["id_votacion", "bloque", "distrito", "diputado", "voto"]).writerows(nuevos_votos)
    urls["capturas"].append({"archivo": VD.rel(os.path.abspath(a.captura)), "fecha": cap.get("capturado", ""), "votaciones": len(nuevas_v)})
    escribir(os.path.join(BASE, "indice.json"), urls)
    print("→ %s (+%d) · %s (+%d)" % (VD.rel(ruta_v), len(nuevas_v), VD.rel(ruta_d), len(nuevos_votos)))
    return 0


# ---------- leyes y votación decisiva ----------
def iniciativa_de(pregunta):
    m = RE_INICIATIVA.search(pregunta or "")
    return (m.group(1) or m.group(2)) if m else None


def clase_votacion(pregunta):
    p = " ".join(plano(pregunta))
    if "urgencia nacional" in p and "mocion" in p:
        return "urgencia"
    if re.search(r"\b(articulo|enmienda|preambulo|titulo|capitulo|considerando)\b", p) and "redaccion final" not in p:
        return "parcial"
    for clave, _ in DECISIVAS:
        if clave in p:
            return clave
    return "otra"


def leyes(vot=None):
    """{iniciativa: [votaciones en orden]} de las preguntas que nombran una iniciativa."""
    out = collections.defaultdict(list)
    for r in vot if vot is not None else votaciones_base():
        ini = iniciativa_de(r["pregunta"])
        if ini:
            out[ini].append(r)
    for v in out.values():
        v.sort(key=lambda r: (r["fecha_votacion"], int(r["no_votacion"] or 0)))
    return out


def decisiva_de(vs):
    """La votación que aprueba (o rechaza) la ley: redacción final > único debate > tercer debate (la última de su clase)."""
    for clave, _ in DECISIVAS:
        xs = [r for r in vs if clase_votacion(r["pregunta"]) == clave]
        if xs:
            return xs[-1], clave
    return None, None


def umbral_de(clase):
    return CALIFICADA if clase == "urgencia" else MAYORIA


def resumen_votacion(r, clase=None):
    clase = clase or clase_votacion(r["pregunta"])
    u, fav = umbral_de(clase), int(r["favor"])
    return "%s · %s a favor, %s en contra, %s ausentes, %s con licencia · umbral %d → %s (%+d)" % (
        r["fecha_votacion"][:16], r["favor"], r["contra"], r["ausente"], r["licencia"], u,
        "aprobada" if fav >= u else "no alcanzó", fav - u)


def cmd_proponer(a):
    vot = votaciones_base()
    hasta = max(r["fecha_votacion"] for r in vot)[:10]
    desde = (datetime.date.fromisoformat(hasta) - datetime.timedelta(days=a.dias)).isoformat()
    cands = []
    for ini, vs in leyes(vot).items():
        dec, clase = decisiva_de(vs)
        if not dec or dec["fecha_votacion"][:10] < desde:
            continue
        fav, con, aus = int(dec["favor"]), int(dec["contra"]), int(dec["ausente"])
        urg = next((r for r in vs if clase_votacion(r["pregunta"]) == "urgencia"), None)
        u = MAYORIA
        cerca = max(0, 30 - abs(fav - u)) / 30            # cerca del umbral: más tensión
        division = min(fav, con) / max(1, fav + con)        # votación dividida
        recencia = 1 - (datetime.date.fromisoformat(hasta) - datetime.date.fromisoformat(dec["fecha_votacion"][:10])).days / max(1, a.dias)
        puntaje = round(2 * division + cerca + recencia + (0.5 if urg else 0) + (0.3 if aus >= 40 else 0), 2)
        cands.append((puntaje, ini, dec, clase, urg, len(vs)))
    cands.sort(key=lambda x: -x[0])
    print("Leyes votadas del %s al %s (base hasta %s; ¿falta algo? captura con referencias/congreso/captura.md)" % (desde, hasta, hasta))
    for p, ini, dec, clase, urg, nv in cands[:a.n]:
        print("\n%.2f · iniciativa %s · %s · %d votaciones" % (p, ini, dict(DECISIVAS)[clase], nv))
        print("   decisiva: %s" % resumen_votacion(dec, clase))
        if urg:
            print("   urgencia nacional: %s" % resumen_votacion(urg, "urgencia"))
        print("   «%s»" % dec["pregunta"][:150])
    if not cands:
        print("(ninguna ley con votación decisiva en esos días)")
    return 0


def cifra(cid, concepto, valor, unidad, periodo, url, cita, archivo, partes=None):
    c = {"id": cid, "concepto": concepto, "valor": valor, "unidad": unidad, "periodo": periodo, "veredicto": "verificada",
         "valor_final": valor, "evidencia": {"url": url, "cita": cita, "archivo_local": archivo}}
    if partes:
        c["partes"] = partes
    return c


def armar_votacion(trabajo, ini, fixture=False):
    """votacion.json + base/datos.json (cifras cg-cNN) + votos_ley.csv de la iniciativa `ini`."""
    vs = leyes().get(str(ini))
    if not vs:
        raise SystemExit(falla("la iniciativa %s no tiene votaciones en la base (¿falta capturar la sesión? `proponer` lista las recientes)" % ini))
    dec, clase = decisiva_de(vs)
    if not dec:
        raise SystemExit(falla("la iniciativa %s no tiene votación de tercer debate, único debate ni redacción final" % ini))
    urg = next((r for r in vs if clase_votacion(r["pregunta"]) == "urgencia"), None)
    indice = leer(os.path.join(BASE, "indice.json")) if os.path.exists(os.path.join(BASE, "indice.json")) else {"urls": {}}
    pad = {clave_nombre(d["nombre"]): d for d in padron()}
    filas = votos_de([dec["id_votacion"]] + ([urg["id_votacion"]] if urg else []))
    os.makedirs(trabajo, exist_ok=True)

    def info(r, clase_r):
        url = (indice["urls"].get(str(r["id_votacion"])) or {}).get("url") or ""
        diputados = []
        for x in sorted(filas[r["id_votacion"]], key=lambda x: x["diputado"]):
            d = pad.get(clave_nombre(x["diputado"])) or {}
            diputados.append({"nombre": x["diputado"], "corto": nombre_corto(d) if d.get("nombres") else nombre_corto({"nombre": x["diputado"]}),
                              "bancada": x["bloque"], "bancada_legible": bancada_legible(x["bloque"]), "distrito": x["distrito"],
                              "voto": x["voto"], "id": d.get("id")})
        por_b = collections.defaultdict(collections.Counter)
        for d in diputados:
            por_b[d["bancada"]][d["voto"]] += 1
        return {"id_votacion": r["id_votacion"], "clase": clase_r, "pregunta": r["pregunta"], "fecha": r["fecha_votacion"],
                "sesion": "%s %s" % (r["tipo_sesion"], r["no_sesion"]), "url": url or ("archivo oficial: " + r["archivo"]),
                "umbral": umbral_de(clase_r), **{k: int(r[k]) for k in VOTOS},
                "bancadas": {b: dict(c) for b, c in sorted(por_b.items(), key=lambda kv: -sum(kv[1].values()))},
                "diputados": diputados}
    V = {"iniciativa": str(ini), "decisiva": info(dec, clase), "urgencia": info(urg, "urgencia") if urg else None,
         "votaciones": [{"id": r["id_votacion"], "fecha": r["fecha_votacion"], "pregunta": r["pregunta"], "favor": int(r["favor"]),
                         "contra": int(r["contra"]), "clase": clase_votacion(r["pregunta"])} for r in vs]}
    escribir(os.path.join(trabajo, "votacion.json"), V)
    # el listado nominal de la decisiva: el archivo local que citan las cifras
    ruta_csv = os.path.join(trabajo, "votos_ley.csv")
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["votacion", "diputado", "bancada", "distrito", "voto"])
        for k in ("decisiva", "urgencia"):
            for d in (V[k] or {}).get("diputados") or []:
                w.writerow([k, d["nombre"], d["bancada"], d["distrito"], d["voto"]])
    rel_csv = VD.rel(ruta_csv)
    cifras, n = [], 0

    def nueva(*args, **kw):
        nonlocal n
        n += 1
        cifras.append(cifra("cg-c%02d" % n, *args, **kw))
        return "cg-c%02d" % n
    D = V["decisiva"]
    per = D["fecha"][:10]
    nombre_v = "votación de %s (%s)" % (dict(DECISIVAS).get(clase, clase).lower(), per)
    ids = {}
    for k, txt in (("favor", "votos a favor"), ("contra", "votos en contra"), ("ausente", "diputados ausentes"), ("licencia", "diputados con licencia o excusa")):
        ids[k] = nueva("%s en la %s de la iniciativa %s" % (txt.capitalize(), nombre_v, ini), D[k], "diputados", per, D["url"],
                       "%d filas con voto «%s» en el listado nominal de la %s" % (D[k], k, nombre_v), rel_csv)
    ids["total"] = nueva("Diputados del Congreso", TOTAL, "diputados", per, D["url"], "%d filas en el listado nominal" % TOTAL, rel_csv)
    ids["umbral"] = nueva("Votos para aprobar: mayoría absoluta del total (Ley Orgánica, art. 99)", MAYORIA, "votos", "vigente",
                          LEY_ORGANICA["url"], "mayoría absoluta del total de diputados que integran el Congreso", LEY_ORGANICA["archivo"])
    for lado in ("favor", "contra"):
        partes = [{"nombre": bancada_legible(b), "valor": c.get(lado, 0)} for b, c in D["bancadas"].items() if c.get(lado)]
        if partes:
            ids["bancadas_" + lado] = nueva("Votos %s por bancada en la %s" % ("a favor" if lado == "favor" else "en contra", nombre_v),
                                            sum(p["valor"] for p in partes), "diputados", per, D["url"],
                                            "conteo por bancada del listado nominal", rel_csv, partes=partes)
    if V["urgencia"]:
        U = V["urgencia"]
        ids["urg_favor"] = nueva("Votos a favor de declarar la iniciativa %s de urgencia nacional (%s)" % (ini, U["fecha"][:10]), U["favor"],
                                 "diputados", U["fecha"][:10], U["url"], "%d filas con voto «favor» en la moción de urgencia" % U["favor"], rel_csv)
        ids["urg_contra"] = nueva("Votos en contra de la urgencia nacional (%s)" % U["fecha"][:10], U["contra"], "diputados",
                                  U["fecha"][:10], U["url"], "%d filas con voto «contra» en la moción de urgencia" % U["contra"], rel_csv)
        ids["urg_umbral"] = nueva("Votos para declarar urgencia nacional: dos tercios del total", CALIFICADA, "votos", "vigente",
                                  LEY_ORGANICA["url"], "las dos terceras partes del total de diputados", LEY_ORGANICA["archivo"])
    V["cifras"] = ids
    escribir(os.path.join(trabajo, "votacion.json"), V)
    return V, cifras


def recientes():
    regs = leer(REGISTRO).get("congreso", []) if os.path.exists(REGISTRO) else []
    regs = sorted(regs, key=lambda r: (r.get("fecha", ""), r.get("id", "")))
    fr = [r.get("frases") or {} for r in regs]
    return regs, ({"familias": [x.get("familia") for x in fr[-2:] if x.get("familia")], "visuales": []},
                  {"tipos": [x.get("cierre_tipo") for x in fr[-1:] if x.get("cierre_tipo")],
                   "formas": [x.get("cierre_forma") for x in fr[-VD.ROTACION_CIERRES:] if x.get("cierre_forma")],
                   "mecanismos": [x["cierre_mecanismo"] for x in fr[-1:] if x.get("cierre_mecanismo")]})


SEMILLA = ("votacion.json", "votos_ley.csv", "ley.json", "fotos", "fuentes")


def cmd_preparar(a):
    ini = re.sub(r"\D", "", a.iniciativa or "")
    if a.semilla:   # la maqueta: la votación, la ley, las fotos y sus textos ya armados (sin la base, que vive fuera de git)
        ini = ini or leer(os.path.join(a.semilla, "votacion.json"))["iniciativa"]
    if not ini:
        return falla("dime el número de la iniciativa («6347»); `congreso.py proponer` lista las leyes votadas en los últimos días")
    slug = slug_de(a.slug) if a.slug else "iniciativa-%s" % ini
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "congreso-" + slug))
    if a.semilla:
        os.makedirs(trabajo, exist_ok=True)
        for x in SEMILLA:
            src = os.path.join(a.semilla, x)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(trabajo, x), dirs_exist_ok=True)
            elif os.path.exists(src):
                shutil.copyfile(src, os.path.join(trabajo, x))
        V = leer(os.path.join(trabajo, "votacion.json"))
        cifras = leer(os.path.join(a.semilla, "datos.json"))["cifras"]
    else:
        V, cifras = armar_votacion(trabajo, ini, a.fixture)
    regs, (rec_g, rec_c) = recientes()
    usadas = [r.get("paleta") for r in regs]
    paleta = a.paleta or min(PALETAS, key=lambda p: (usadas[::-1].index(p) * -1 if p in usadas else -999, PALETAS.index(p)))
    if a.paleta is None and usadas:
        paleta = next((p for p in PALETAS if p not in usadas[-3:]), PALETAS[0])
    base = os.path.join(trabajo, "base")
    os.makedirs(base, exist_ok=True)
    fecha = V["decisiva"]["fecha"][:10]
    escribir(os.path.join(base, "datos.json"), {"slug": slug, "cifras": cifras})
    escribir(os.path.join(base, "hilo.json"), {"slug": slug, "fecha": fecha, "tema": "Iniciativa %s · Congreso de Guatemala" % ini,
                                               "tesis": "", "paleta": paleta, "estado": "listo", "modo": "congreso", "hook_tipo": None,
                                               "no_afirma": [], "tuits": []})
    with contextlib.redirect_stdout(io.StringIO()):
        rc = VD.cmd_preparar(argparse.Namespace(hilo=base, duracion="congreso", musica=a.musica, trabajo=trabajo,
                                                permitir_borrador=True, sin_rotacion=a.fixture))
    if rc:
        return rc
    st = VD.estado(trabajo)
    st.update({"tipo": "congreso", "iniciativa": ini, "fecha": datetime.date.today().isoformat(), "fecha_votacion": fecha,
               "ganchos_recientes": {"familias": [], "visuales": []} if a.fixture else rec_g,
               "cierres_recientes": {"tipos": [], "formas": [], "mecanismos": []} if a.fixture else rec_c,
               "fixture": bool(a.fixture)})
    escribir(os.path.join(trabajo, "video.json"), st)
    texto = digesto(trabajo)
    print(texto)
    print("→ %s · trabajo: %s" % (VD.rel(os.path.join(trabajo, "digesto.md")), VD.rel(trabajo)))
    if not os.path.exists(os.path.join(trabajo, "ley.json")):
        print("SIGUIENTE ley.json (qué buscaba, estado, citas) con sus textos guardados y `congreso.py ley %s --check`" % VD.rel(trabajo))
    return 0


# ---------- ley.json (CG2) ----------
def texto_guardado(archivo):
    ruta = os.path.join(RAIZ, archivo or "")
    if not archivo or not os.path.exists(ruta):
        return None
    return open(ruta, encoding="utf-8", errors="replace").read()


def contiene(texto, cita):
    norm = lambda s: " ".join(plano(s))   # noqa: E731
    return bool(cita) and norm(cita) in norm(texto)


def revisar_ley(trabajo):
    """CG2 → (fallas, ley)."""
    ruta = os.path.join(trabajo, "ley.json")
    if not os.path.exists(ruta):
        return ["CG2 falta ley.json (qué buscaba la ley con su cita; referencias/flujo-congreso.md)"], None
    L, f = leer(ruta), []
    if not (L.get("titulo") or "").strip():
        f.append("CG2 ley.json sin «titulo» (el nombre de la ley o del decreto)")
    if not (L.get("nombre_corto") or "").strip() or len(L.get("nombre_corto") or "") > 34:
        f.append("CG2 «nombre_corto» de 1–34 caracteres (va en el contexto de arriba: «Ley de …»)")
    qb = L.get("que_busca") or []
    if not 1 <= len(qb) <= 5:
        f.append("CG2 «que_busca»: 1–5 afirmaciones (qué cambia y para quién)")
    docs = [("que_busca[%d]" % k, x) for k, x in enumerate(qb)] + ([("estado", L["estado"])] if L.get("estado") else []) + \
           [("citas[%s]" % x.get("id"), x) for x in L.get("citas") or []]
    for et, x in docs:
        if not (x.get("texto") or "").strip():
            f.append("CG2 %s sin «texto»" % et)
        if not (x.get("url") or "").startswith("http"):
            f.append("CG2 %s sin «url»" % et)
        t = texto_guardado(x.get("archivo"))
        cita = x.get("cita") if et != "citas[%s]" % x.get("id") else (x.get("cita") or x.get("texto"))
        if t is None:
            f.append("CG2 %s: «archivo» %s no existe (guarda el texto con historia.py leer o congreso.py leer)" % (et, x.get("archivo")))
        elif not contiene(t, cita):
            f.append("CG2 %s: la cita «%s» no está literal en %s" % (et, (cita or "")[:70], x.get("archivo")))
    for x in L.get("citas") or []:
        if not re.fullmatch(r"ley-q\d{2}", x.get("id") or ""):
            f.append("CG2 cita id «%s»: va como ley-qNN" % x.get("id"))
    # cifras de la ley (penas, plazos, montos): cada número escrito en su cita literal
    for k, c in enumerate(L.get("cifras") or [], 1):
        if not re.fullmatch(r"ley-c\d{2}", c.get("id") or ""):
            f.append("CG2 cifras[%d]: id «%s» va como ley-cNN" % (k, c.get("id")))
        t = texto_guardado(c.get("archivo"))
        if t is None or not contiene(t, c.get("cita")):
            f.append("CG2 cifra %s: la cita no está literal en %s" % (c.get("id"), c.get("archivo")))
        elif not isinstance(c.get("valor"), (int, float)) or not VD.escribe_numero(c["valor"], [c.get("cita")]):
            f.append("CG2 cifra %s: su cita no escribe el valor %s" % (c.get("id"), c.get("valor")))
    return f, L


def sincronizar_cifras(trabajo, L):
    """Las cifras de ley.json (ley-cNN) entran a base/datos.json junto a las de la votación (cg-cNN): respaldan la voz (V2)."""
    ruta = os.path.join(trabajo, "base", "datos.json")
    D = leer(ruta)
    D["cifras"] = [c for c in D["cifras"] if not c["id"].startswith("ley-")] + [
        cifra(c["id"], c.get("concepto", ""), c["valor"], c.get("unidad", ""), c.get("periodo", ""), c.get("url", ""), c["cita"], c["archivo"])
        for c in L.get("cifras") or []]
    escribir(ruta, D)
    # el tema del «hilo base» (F3: la frase final nombra algo del tema): el título y lo que busca la ley
    ruta_h = os.path.join(trabajo, "base", "hilo.json")
    H = leer(ruta_h)
    H["tema"] = "%s · Congreso de Guatemala" % (L.get("titulo") or H.get("tema", ""))
    H["tesis"] = ". ".join(x["texto"] for x in (L.get("que_busca") or []) + ([L["estado"]] if L.get("estado") else []))
    escribir(ruta_h, H)


def cmd_ley(a):
    trabajo = os.path.abspath(a.trabajo)
    f, L = revisar_ley(trabajo)
    for x in f:
        print("FALLA", x)
    if not f:
        sincronizar_cifras(trabajo, L)
        digesto(trabajo)
        print("ley.json ok · %d afirmaciones · estado: %s · %d citas · %d cifras → base/datos.json · digesto.md al día"
              % (len(L.get("que_busca") or []), "sí" if L.get("estado") else "no", len(L.get("citas") or []), len(L.get("cifras") or [])))
    return 1 if f else 0


def cmd_leer(a):
    """Una captura de Chrome de congreso.gob.gt (que bloquea las descargas fuera del navegador) → textos guardados para
    ley.json y fotos con crédito en TRABAJO/fotos: {"textos": {url: {titulo, texto, foto: {url, data}}}} (CG.textos) o
    {"pdfs": {url: dataURL}} (CG.pdfs: la iniciativa; pdftotext saca el texto)."""
    trabajo = os.path.abspath(a.trabajo)
    cap = leer(a.captura)
    os.makedirs(DESCARGAS, exist_ok=True)
    os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
    nf = len(glob.glob(os.path.join(trabajo, "fotos", "ley-f*.json")))
    for url, x in (cap.get("textos") or {}).items():
        h = hashlib.sha1(url.encode()).hexdigest()[:12]
        txt = os.path.join(DESCARGAS, h + ".txt")
        open(txt, "w", encoding="utf-8").write("%s\n%s\n\n%s\n" % (url, x.get("titulo", ""), x.get("texto", "")))
        print("texto · %s · %d caracteres → %s" % (x.get("titulo", "")[:70], len(x.get("texto", "")), VD.rel(txt)))
        fo = x.get("foto") or {}
        if fo.get("data"):
            ya = [r for r in VD.fotos_trabajo(trabajo).values() if r.get("url") == fo.get("url")]
            if ya:
                print("foto ya en el TRABAJO: %s" % ya[0]["id"])
                continue
            nf += 1
            fid = "ley-f%02d" % nf
            tmp = os.path.join(trabajo, "fotos", fid + ".orig")
            open(tmp, "wb").write(base64.b64decode(fo["data"].split(",", 1)[1]))
            VD.ff("-i", tmp, "-frames:v", "1", "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", os.path.join(trabajo, "fotos", fid + ".jpg"))
            os.remove(tmp)
            w, hh = (int(v) for v in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                                      "-of", "csv=p=0:s=x", os.path.join(trabajo, "fotos", fid + ".jpg")],
                                                     capture_output=True, text=True).stdout.strip().split("x")[:2])
            escribir(os.path.join(trabajo, "fotos", fid + ".json"),
                     {"id": fid, "archivo": "fotos/%s.jpg" % fid, "credito": "Foto: Congreso de la República", "origen": "oficial",
                      "descripcion": "Foto de la nota «%s»" % x.get("titulo", ""), "url": fo["url"], "fuente": url, "tamano": [w, hh],
                      "encaje": None, "referencia": False, "fecha": None})
            print("foto %s · %d×%d · Foto: Congreso de la República" % (fid, w, hh))
    for url, data in (cap.get("pdfs") or {}).items():
        h = hashlib.sha1(url.encode()).hexdigest()[:12]
        pdf, txt = os.path.join(DESCARGAS, h + ".pdf"), os.path.join(DESCARGAS, h + ".txt")
        open(pdf, "wb").write(base64.b64decode(data.split(",", 1)[1]))
        r = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True)
        if r.returncode or len(r.stdout.strip()) < 200:
            print("AVISO pdftotext no sacó texto de %s (¿un escaneo?): usa la nota oficial o la prensa" % url)
            continue
        open(txt, "w", encoding="utf-8").write(url + "\n\n" + r.stdout)
        print("pdf · %d caracteres → %s" % (len(r.stdout), VD.rel(txt)))
    return 0


# ---------- fotos de los diputados ----------
def cmd_fotos(a):
    trabajo = os.path.abspath(a.trabajo)
    pad = {d["id"]: d for d in padron()}
    por_nombre = {clave_nombre(d["nombre"]): d for d in pad.values()}
    os.makedirs(RETRATOS, exist_ok=True)
    if a.captura:
        for pid, x in (leer(a.captura).get("fotos") or {}).items():
            if not x or not x.get("data"):
                print("AVISO perfil %s sin foto" % pid)
                continue
            crudo = base64.b64decode(x["data"].split(",", 1)[1])
            tmp = os.path.join(RETRATOS, "%s.orig" % pid)
            open(tmp, "wb").write(crudo)
            VD.ff("-i", tmp, "-frames:v", "1", "-vf", "scale='min(900,iw)':-2", "-q:v", "3", os.path.join(RETRATOS, "%s.jpg" % pid))
            os.remove(tmp)
            meta = {"id": pid, "nombre": (pad.get(pid) or {}).get("nombre"), "url": x.get("url"), "credito": CREDITO_RETRATO,
                    "capturado": datetime.date.today().isoformat()}
            escribir(os.path.join(RETRATOS, "%s.json" % pid), meta)
            print("retrato %s · %s" % (pid, meta["nombre"]))
    faltan = []
    for nombre in a.diputados or []:
        d = por_nombre.get(clave_nombre(nombre))
        if not d:
            print("FALLA «%s» no está en el padrón" % nombre)
            return 1
        src = os.path.join(RETRATOS, "%s.jpg" % d["id"])
        if not os.path.exists(src):
            faltan.append(d["id"])
            continue
        os.makedirs(os.path.join(trabajo, "fotos"), exist_ok=True)
        fid = "dip-%s" % d["id"]
        shutil.copyfile(src, os.path.join(trabajo, "fotos", fid + ".jpg"))
        escribir(os.path.join(trabajo, "fotos", fid + ".json"),
                 {"id": fid, "archivo": "fotos/%s.jpg" % fid, "credito": CREDITO_RETRATO, "descripcion": "Retrato oficial de %s" % d["nombre"],
                  "retrato_de": d["nombre"], "origen": "oficial", "url": (leer(os.path.join(RETRATOS, "%s.json" % d["id"])) or {}).get("url"),
                  "encaje": None, "referencia": False})
        print("foto %s · %s" % (fid, d["nombre"]))
    if faltan:
        print("FALTAN retratos: captúralos en Chrome con CG.correr({fotos: %s}) y corre fotos --captura" % json.dumps(faltan))
        return 1
    return 0


# ---------- digesto ----------
def cruzados(D):
    """Los que votaron distinto de la mayoría de su bancada (entre los que votaron a favor o en contra; bancadas de ≥ 3)."""
    out = []
    for b, c in D["bancadas"].items():
        emit = {k: c.get(k, 0) for k in ("favor", "contra")}
        if sum(emit.values()) < 3 or min(emit.values()) == 0:
            continue
        mayor = max(emit, key=emit.get)
        out += [d for d in D["diputados"] if d["bancada"] == b and d["voto"] in ("favor", "contra") and d["voto"] != mayor]
    return out


def digesto(trabajo):
    st, V = VD.estado(trabajo), leer(os.path.join(trabajo, "votacion.json"))
    D, U = V["decisiva"], V.get("urgencia")
    datos = {c["id"]: c for c in leer(os.path.join(trabajo, "base", "datos.json"))["cifras"]}
    pad = {d["nombre"]: d for d in padron()}
    fotos = VD.fotos_trabajo(trabajo)
    L = leer(os.path.join(trabajo, "ley.json")) if os.path.exists(os.path.join(trabajo, "ley.json")) else None
    lineas = ["# Digesto para /congreso · iniciativa %s" % V["iniciativa"], "",
              "- Ley: %s" % ((L or {}).get("titulo") or "(falta ley.json: el título, qué buscaba y su estado)"),
              "- Paleta: %s · música: %s" % (st["paleta"], st["musica"]), "",
              "## La votación decisiva (%s)" % dict(DECISIVAS).get(D["clase"], D["clase"]),
              "- %s · %s" % (D["sesion"], resumen_votacion({k: D[k] for k in VOTOS} | {"fecha_votacion": D["fecha"]}, D["clase"])),
              "- Pregunta: «%s»" % D["pregunta"], "- Listado nominal: %s" % D["url"]]
    if U:
        lineas += ["", "## La urgencia nacional (dos tercios: %d)" % CALIFICADA,
                   "- %s" % resumen_votacion({k: U[k] for k in VOTOS} | {"fecha_votacion": U["fecha"]}, "urgencia")]
    lineas += ["", "## Cifras (las únicas que la voz y la pantalla pueden decir; V2)"]
    for cid, c in datos.items():
        partes = ", ".join("%s: %s" % (p["nombre"], p["valor"]) for p in c.get("partes") or [])
        lineas.append("- %s: %s = %s%s" % (cid, c["concepto"], c["valor"], " · " + partes if partes else ""))
    lineas += ["", "## Bancadas (bancada actual del sistema de votación)"]
    for b, c in D["bancadas"].items():
        lineas.append("- %s: %s" % (bancada_legible(b), ", ".join("%d %s" % (c[k], k) for k in VOTOS if c.get(k))))
    cz = cruzados(D)
    lineas += ["", "## A quién nombrar (CG3–CG4)",
               "- Hasta %d por lado, **cada uno de un partido distinto** (los independientes ex UNE cuentan como UNE) y de los "
               "partidos que más votos dieron a ese lado; menos solo si votaron menos partidos. Un nombre con `notoriedad` "
               "(el presidente del Congreso, un jefe de bancada) vale aunque su partido sea chico, pero sigue sin repetir partido." % NOMBRES_POR_LADO,
               "- Cruzados (votaron distinto de su bancada): %s" % ("; ".join("%s (%s, %s)" % (d["nombre"], bancada_legible(d["bancada"]), d["voto"]) for d in cz) or "ninguno")]
    for lado in ("favor", "contra"):
        ps = partidos_lado(D, lado)
        if not ps:
            lineas.append("- %s: nadie (no se nombra a nadie de este lado)" % lado)
            continue
        peso = partidos_de_peso(D, lado)
        lineas.append("- **%s** (%d votos): van %d nombres de partidos distintos; partidos de peso: %s"
                      % (lado, sum(n for _, n, _ in ps), nombres_requeridos(D, lado), ", ".join(peso)))
        for p, n, ds in ps:
            conocidos = [d for d in ds if (pad.get(d["nombre"]) or {}).get("notoriedad")]
            if p not in peso and not conocidos:
                continue
            cz_p = [d for d in ds if d in cz]
            lineas.append("  - %s · %d%s%s: %s" % (p, n, " · conocidos: " + "; ".join("%s (%s)" % (d["nombre"], pad[d["nombre"]]["notoriedad"]) for d in conocidos) if conocidos else "",
                                                 " · cruzados: " + "; ".join(d["nombre"] for d in cz_p) if cz_p else "",
                                                 "; ".join("%s (%s)" % (d["nombre"], bancada_legible(d["bancada"])) for d in ds[:30])))
    lineas.append("- (llena «notoriedad» en referencias/congreso/diputados.json para que un nombre conocido salga arriba)")
    lineas += ["", "## Fotos en el TRABAJO (gancho con `visual: foto`; avatares en `focos` del hemiciclo)"]
    lineas += ["- %s · %s · %s" % (k, r.get("descripcion", ""), r.get("credito", "")) for k, r in fotos.items()] or ["- (ninguna)"]
    if L:
        lineas += ["", "## Qué buscaba (ley.json: `afirma` en la escena que lo dice)"]
        lineas += ["- [%d] %s" % (k, x["texto"]) for k, x in enumerate(L.get("que_busca") or [])]
        if L.get("estado"):
            lineas.append("- estado: %s (escena con `estado: true`)" % L["estado"]["texto"])
        lineas += ["- cita %s: «%s» (%s)" % (x["id"], x["texto"], x.get("autor") or x.get("membrete") or "") for x in L.get("citas") or []]
    car = int((OBJETIVO_S - VD.COLA * 6 - VD.COLA_CIERRE) * VD.CPS)
    lineas += ["", "## Presupuesto",
               "- %d s ±%d %% (%.0f–%.0f s estimados) y ≤ %.1f s reales con el bucle (CG7) · voz ≈ %d caracteres ya en palabras"
               % (OBJETIVO_S, TOL * 100, OBJETIVO_S * (1 - TOL), OBJETIVO_S * (1 + TOL), TECHO_S, car),
               "- Voz por escena: gancho %d–%d · hemiciclo %d–%d · foto/cita %d–%d · golpe %d–%d · cierre %d–%d."
               % (*VD.CARACTERES["gancho"], *CARACTERES["hemiciclo"], *CARACTERES["foto"], *VD.CARACTERES["golpe"], *VD.CARACTERES["cierre"]),
               "", "## Estructura (CG3–CG10 + V1–V5, V9, F1–F8)",
               "1. **Gancho** (`tipo: gancho`): la consecuencia o la paradoja de la ley, con «Congreso» o «diputados» y "
               "«Guatemala» en ≤ 6 s; `visual: foto` (una foto del pleno o del tema, con crédito) y `mini: \"decisiva\"` "
               "(el hemiciclo de la votación dentro de un círculo que, al final, se abre hacia la escena siguiente: el portal).",
               "2. **La votación** (`tipo: hemiciclo`, `votacion: decisiva|urgencia`, `fases: [\"llenar\", \"umbral\"]`): la voz "
               "dice el umbral («hacían falta 81») y los votos a favor; los asientos se llenan con su contador y el pop de cada "
               "tanda; si hubo votos en contra, se dicen.",
               "3. **Qué buscaba** (`golpe`, `foto` o `cita` de la iniciativa) con `afirma: [k]` (índices de ley.que_busca): a "
               "quién le toca y qué cambia, en lenguaje llano.",
               "4. **Quiénes** (`tipo: hemiciclo`, `fases: [\"foco\"]` y opcional `\"barras\"`; `focos`: [{\"diputado\": "
               "\"Nombre completo\"} | {\"bancada\": \"VAMOS\", \"voto\": \"favor\"}]): las bancadas de cada lado y hasta 3 nombres "
               "por lado, de partidos distintos y de los que más pesaron (CG4), cada uno con su avatar sobre su asiento cuando "
               "la voz lo nombra; con 3 y 3 conviene partirlo en dos escenas foco (en contra, «pero» a favor). Declara en `diputados` "
               "[{nombre, voto}] a cada diputado que la voz nombra (CG3).",
               "5. **Por eso** (`golpe` o `foto`, `estado: true`): qué pasa ahora (sanción, veto, vigencia), con ley.estado.",
               "6. **Cierre** de una sola pantalla (`resumen: []`, `texto` = `final`): la consecuencia para quien vive la ley; "
               "sin «sígueme» en la voz.",
               "- Frases cortas, encadenadas con «pero» y «por eso» (≥ 2 enlaces en el video, CG8). Neutral: nadie es "
               "«traidor», «vendido» ni «corrupto» (CG5); quién votó qué se dice tal cual.",
               "- `contexto_superior` (≤ 40): «<nombre corto> · Congreso». `caption`: tiktok, instagram, facebook y shorts.",
               "", "## Rotación",
               "- Ganchos recientes: %s · cierres: %s" % (", ".join(st["ganchos_recientes"].get("familias") or []) or "—",
                                                        ", ".join(st["cierres_recientes"].get("formas") or []) or "—"),
               "", "## Plantilla de guion.json", "```json",
               json.dumps({"contexto_superior": "<Ley …> · Congreso", "escenas": [
                   {"tipo": "gancho", "familia": "paradoja", "visual": "foto", "visual_datos": {"foto": "<id>"}, "mini": "decisiva",
                    "pantalla": "<≤ 4 palabras>", "linea": "<≤ 8 palabras>", "verbo": "<verbo>", "texto": "<la paradoja con «Congreso»>"},
                   {"tipo": "hemiciclo", "votacion": "decisiva", "fases": ["llenar", "umbral"], "golpe": "<≤ 6 palabras>",
                    "texto": "Para aprobarla hacían falta 81 votos. Tuvo …"},
                   {"tipo": "golpe", "afirma": [0], "pantalla": "<…>", "linea": "<…>", "verbo": "<…>", "texto": "<qué buscaba>"},
                   {"tipo": "hemiciclo", "votacion": "decisiva", "fases": ["foco", "barras"], "golpe": "<…>",
                    "focos": [{"bancada": "VAMOS", "voto": "favor"}, {"diputado": "<Nombre>"}],
                    "diputados": [{"nombre": "<Nombre>", "voto": "favor"}], "texto": "<quiénes>"},
                   {"tipo": "golpe", "estado": True, "enlace": "por_eso", "pantalla": "<…>", "linea": "<…>", "verbo": "<…>", "texto": "<qué pasa ahora>"}],
                   "cierre": {"texto": "<frase final>", "final": "<frase final>", "resumen": [], "tipo": "remate", "forma": "consecuencia",
                              "consecuencia": {"mecanismo": "quien", "quien": "<gente>", "verbo": "<verbo>"}},
                   "caption": {"tiktok": "…", "instagram": "…", "facebook": "…", "shorts": "<título>\n… #Shorts"}}, ensure_ascii=False, indent=1),
               "```", ""]
    texto = "\n".join(lineas)
    open(os.path.join(trabajo, "digesto.md"), "w", encoding="utf-8").write(texto)
    return texto


def cmd_digesto(a):
    print(digesto(os.path.abspath(a.trabajo)))
    return 0


# ---------- extensión de video.py ----------
def aplicar_extension(trabajo):
    """Enchufa en video.py lo propio de /congreso (una vez por proceso): los tipos hemiciclo, foto y cita, sus voces,
    sus tiempos y su transición; el gancho con el hemiciclo en un círculo; la estructura CG en lugar de la de /video."""
    global TRABAJO_ACTUAL, VOT, LEY
    import historia as HI   # noqa: E402  (historia importa video: aquí, no arriba)
    TRABAJO_ACTUAL = trabajo
    VOT = leer(os.path.join(trabajo, "votacion.json"))
    LEY = leer(os.path.join(trabajo, "ley.json")) if os.path.exists(os.path.join(trabajo, "ley.json")) else {}
    HI.TRABAJO_ACTUAL = trabajo
    HI.H_ACTUAL = {"fotos": VD.fotos_trabajo(trabajo), "citas": LEY.get("citas") or [], "hechos": [], "cifras": {}}
    if ORIGINALES:
        return
    ORIGINALES.update(estructura=VD.validar_estructura, reglas=VD.reglas_gancho)
    VD.NARRACION_VIDEO = False
    VD.CIERRE_ANTES_S = 0.0
    VD.TIPOS = VD.TIPOS + tuple(t for t in TIPOS_PROPIOS if t not in VD.TIPOS)
    VD.CARACTERES.update(CARACTERES)
    VD.SIN_HUECO = VD.SIN_HUECO + TIPOS_PROPIOS
    VD.TRANSICIONES["portal"] = "fade"
    VD.CONSTRUCTORES.update(gancho=t_gancho, hemiciclo=t_hemiciclo, foto=HI.t_foto, cita=HI.t_cita)
    VD.TRANSICION_DE.update(hemiciclo="portal", foto="tarjeta", cita="texto")
    VD.validar_estructura = estructura
    VD.reglas_gancho = reglas_gancho


def de_video_que_no_aplica(x):
    return x.startswith(("V9 promesa", "P1 ", "P2 ", "P3 ", "P4 ", "P5 ", "V1 cierre.resumen", "V9 la escena 2 debe ser la tarjeta T1",
                         "V9 escena 2: la primera tarjeta"))


def diputado_por_nombre(nombre, D):
    k = clave_nombre(nombre)
    return next((d for d in D["diputados"] if clave_nombre(d["nombre"]) == k), None)


def nombrados_en(texto, D):
    """Los diputados de la votación que la voz nombra («Luis Aguirre» o el nombre completo)."""
    t = " " + " ".join(plano(texto)) + " "
    return [d for d in D["diputados"] if " %s " % " ".join(plano(d["corto"])) in t or " %s " % " ".join(plano(d["nombre"])) in t]


def estructura(g, st, dur, tarjetas):
    f = [x for x in ORIGINALES["estructura"](g, st, dur, tarjetas) if not de_video_que_no_aplica(x)]
    escenas, cierre = g.get("escenas") or [], g.get("cierre") or {}
    tipos = [e.get("tipo") for e in escenas]
    if not ESCENAS[0] <= len(escenas) <= ESCENAS[1]:
        f.append("CG9 %d escenas: van %d–%d más el cierre" % (len(escenas), *ESCENAS))
    if cierre.get("resumen"):
        f.append("CG9 cierre.resumen va vacío ([]): el cierre es una sola pantalla")
    if (cierre.get("texto") or "").strip() != (cierre.get("final") or "").strip():
        f.append("CG9 cierre.texto = cierre.final: la voz del cierre es solo la frase final")
    fotos = VD.fotos_trabajo(TRABAJO_ACTUAL)
    citas = {x["id"]: x for x in (LEY or {}).get("citas") or []}
    qb = (LEY or {}).get("que_busca") or []
    # CG10: la votación en el hemiciclo, pronto
    hems = [(i, e) for i, e in enumerate(escenas, 1) if e.get("tipo") == "hemiciclo"]
    llena = [i for i, e in hems if "llenar" in (e.get("fases") or [])]
    if not llena:
        f.append("CG10 ninguna escena hemiciclo llena la votación (`fases` con «llenar»)")
    elif llena[0] > 3:
        f.append("CG10 la votación (hemiciclo con «llenar») entra en la escena %d: va en la 2 o la 3" % llena[0])
    for i, e in hems:
        fs = e.get("fases") or []
        if not fs or any(x not in FASES for x in fs):
            f.append("CG10 escena %d (hemiciclo): `fases` de %s" % (i, "|".join(FASES)))
        cual = e.get("votacion") or "decisiva"
        if cual not in ("decisiva", "urgencia") or not VOT.get(cual):
            f.append("CG10 escena %d: `votacion` «%s» no existe (decisiva%s)" % (i, cual, "|urgencia" if VOT.get("urgencia") else ""))
            continue
        D = VOT[cual]
        if "llenar" in fs:
            if not VD.escribe_numero(D["favor"], [e.get("texto")]):
                f.append("CG10 escena %d: la voz no dice los %d votos a favor" % (i, D["favor"]))
            if not VD.escribe_numero(D["umbral"], [e.get("texto")]):
                f.append("CG10 escena %d: la voz no dice el umbral (%d): sin él, la cifra no se entiende" % (i, D["umbral"]))
        for k, fo in enumerate(e.get("focos") or []):
            if fo.get("diputado"):
                d = diputado_por_nombre(fo["diputado"], D)
                if not d:
                    f.append("CG3 escena %d foco %d: «%s» no está en el listado de la votación" % (i, k + 1, fo["diputado"]))
                elif "dip-%s" % d.get("id") not in fotos:
                    f.append("CG3 escena %d foco %d: falta el retrato de %s (congreso.py fotos TRABAJO --diputados \"%s\")" % (i, k + 1, d["nombre"], d["nombre"]))
            elif fo.get("bancada"):
                c = D["bancadas"].get(fo["bancada"]) or {}
                if not c.get(fo.get("voto") or "favor"):
                    f.append("CG3 escena %d foco %d: la bancada %s no tiene votos «%s»" % (i, k + 1, fo["bancada"], fo.get("voto") or "favor"))
            else:
                f.append("CG3 escena %d foco %d: {diputado} o {bancada, voto}" % (i, k + 1))
        if "foco" in fs and not e.get("focos"):
            f.append("CG10 escena %d: la fase «foco» necesita `focos`" % i)
    # CG3–CG4: los nombres que dice la voz, declarados y con su voto; los dos lados
    D = VOT["decisiva"]
    declarados, lados = {}, collections.Counter()
    for i, e in enumerate(escenas, 1):
        D_e = VOT.get(e.get("votacion") or "decisiva") or D
        for x in e.get("diputados") or []:
            d = diputado_por_nombre(x.get("nombre"), D_e)
            if not d:
                f.append("CG3 escena %d: «%s» no está en el listado de la votación" % (i, x.get("nombre")))
            elif x.get("voto") != d["voto"]:
                f.append("CG3 escena %d: %s votó «%s», no «%s»" % (i, d["nombre"], d["voto"], x.get("voto")))
            else:
                declarados[d["nombre"]] = d
                lados[d["voto"]] += 1
        for d in nombrados_en(e.get("texto") or "", D_e):
            if not any(clave_nombre(x.get("nombre")) == clave_nombre(d["nombre"]) for x in e.get("diputados") or []):
                f.append("CG3 escena %d: la voz nombra a %s y la escena no lo declara en `diputados` (con su voto: %s)" % (i, d["nombre"], d["voto"]))
    # CG4 (usuario, 2026-11-04): hasta 3 por lado, de partidos distintos y de los que más votos dieron a ese lado
    por_lado = collections.defaultdict(list)
    for d in declarados.values():
        por_lado[d["voto"]].append(d)
    if D["contra"] > 0 and (not lados["favor"] or not lados["contra"]):
        f.append("CG4 nombras solo a un lado (%s): si hubo votos en contra, al menos un nombre de cada lado"
                 % (", ".join("%d %s" % (n, k) for k, n in lados.items()) or "nadie"))
    pad = {x["nombre"]: x for x in padron()}
    for lado in ("favor", "contra"):
        ds, req = por_lado.get(lado, []), nombres_requeridos(D, lado)
        if len(ds) > NOMBRES_POR_LADO:
            f.append("CG4 %d nombres del lado «%s» (máximo %d)" % (len(ds), lado, NOMBRES_POR_LADO))
        vistos = collections.defaultdict(list)
        for d in ds:
            vistos[partido(d["bancada"])].append(d["nombre"])
        for p, ns in vistos.items():
            if len(ns) > 1:
                f.append("CG4 del lado «%s» nombras a %d de %s (%s): uno por partido" % (lado, len(ns), p, ", ".join(ns)))
        if ds and len(vistos) < req:
            f.append("CG4 del lado «%s» nombras %d partido(s); votaron %d partidos: van %d nombres de partidos distintos (de peso: %s)"
                     % (lado, len(vistos), len(partidos_lado(D, lado)), req, ", ".join(partidos_de_peso(D, lado))))
        peso = partidos_de_peso(D, lado)
        for d in ds:
            if partido(d["bancada"]) not in peso and not (pad.get(d["nombre"]) or {}).get("notoriedad"):
                f.append("CG4 %s es de %s, que pesó poco del lado «%s»: nombra a alguien de %s (o llena su «notoriedad» si es conocido)"
                         % (d["nombre"], partido(d["bancada"]), lado, ", ".join(peso)))
    # CG5: neutralidad
    todo = " ".join([e.get("texto") or "" for e in escenas] + [cierre.get("texto") or ""] +
                    [" ".join(filter(None, (e.get("pantalla"), e.get("linea"), e.get("golpe"), e.get("titular")))) for e in escenas] +
                    [json.dumps(g.get("caption") or {}, ensure_ascii=False)])
    for m in PROHIBIDAS.finditer(todo):
        f.append("CG5 «%s»: el video no califica a nadie; quién votó qué se dice tal cual" % m.group())
    # CG6: qué buscaba, con respaldo
    afirma = [(i, e) for i, e in enumerate(escenas, 1) if e.get("afirma")]
    if not afirma:
        f.append("CG6 ninguna escena dice qué buscaba la ley (`afirma: [k]` con los índices de ley.que_busca)")
    for i, e in afirma:
        if any(not isinstance(k, int) or not 0 <= k < len(qb) for k in e["afirma"]):
            f.append("CG6 escena %d: `afirma` %s fuera de ley.que_busca (0–%d)" % (i, e["afirma"], len(qb) - 1))
    for i, e in enumerate(escenas, 1):
        if i > 1 and e.get("tipo") != "hemiciclo" and VERBOS_LEY.search(e.get("texto") or "") and not e.get("afirma") and not e.get("estado"):
            print("AVISO escena %d: la voz describe la ley («%s») sin `afirma`: si lo dice la iniciativa, decláralo"
                  % (i, VERBOS_LEY.search(e["texto"]).group()))
        if e.get("estado") and not (LEY or {}).get("estado"):
            f.append("CG6 escena %d: `estado: true` sin ley.estado (con su cita)" % i)
        if e.get("tipo") == "foto" and e.get("foto") not in fotos:
            f.append("CG6 escena %d (foto): «%s» no está en TRABAJO/fotos" % (i, e.get("foto")))
        if e.get("tipo") == "cita" and e.get("cita") not in citas:
            f.append("CG6 escena %d (cita): «%s» no está en ley.citas" % (i, e.get("cita")))
    # CG8: el hilo de la narración: «pero» y «por eso»
    enlaces = sum(1 for e in escenas[1:] if VD.RE_ENLACE["pero"].search(VD.sin_pausas(e.get("texto") or "")) or
                  re.search(r"\b(pero|por eso|así que|entonces)\b", e.get("texto") or "", re.I))
    if enlaces < 2:
        f.append("CG8 %d escenas con «pero / por eso / así que»: van ≥ 2 (la narración se encadena, no se enumera)" % enlaces)
    g1 = escenas[0] if escenas else {}
    if not re.search(r"\b(congreso|diputad\w*|pleno)\b", " ".join(filter(None, (g1.get("texto"), g1.get("pantalla"), g1.get("linea")))), re.I):
        f.append("CG8 el gancho no dice «Congreso», «diputados» ni «pleno»: el sujeto se reconoce en ≤ 6 s")
    if g1.get("mini") and g1.get("mini") not in ("decisiva", "urgencia"):
        f.append("CG10 gancho: `mini` decisiva|urgencia")
    return f


def reglas_gancho(e, voz_p, ctx):
    f, av = ORIGINALES["reglas"](e, voz_p, ctx)
    return [x for x in f if not x.startswith("R9 el visual")], av   # el visual foto del gancho se repite a propósito (formato)


# ---------- constructores de tiempos ----------
def escena_guion(S, g):
    es = g.get("escenas") or []
    return es[S["n"] - 1] if S["n"] - 1 < len(es) else {}


def orden_asientos(D):
    """Los 160 asientos de izquierda a derecha: a favor (por bancada, la mayor primero), ausentes, licencia, en contra (la
    bancada mayor al extremo derecho). → lista de {v, b, nombre} y {nombre: índice}."""
    bancadas = list(D["bancadas"].keys())

    def grupo(voto, invertir=False):
        bs = sorted(bancadas, key=lambda b: -(D["bancadas"][b].get(voto) or 0))
        if invertir:
            bs = bs[::-1]
        out = []
        for b in bs:
            out += [d for d in D["diputados"] if d["voto"] == voto and d["bancada"] == b]
        return out
    lista = grupo("favor") + grupo("ausente") + grupo("licencia") + grupo("contra", invertir=True)
    asientos = [{"v": d["voto"][0], "b": bancadas.index(d["bancada"]), "nombre": d["nombre"]} for d in lista]
    return asientos, {a["nombre"]: k for k, a in enumerate(asientos)}, [bancada_legible(b) for b in bancadas]


def momento(pal, valor, despues=0.0):
    """La palabra de la voz que dice `valor` (clave) desde `despues`, o None."""
    return next((w for w in pal if w.get("clave") == VD.clave(valor) and w["start"] >= despues), None)


def momento_nombre(pal, texto, despues=0.0):
    toks = plano(texto)
    ws = [" ".join(plano(w["text"])) for w in pal]
    for j in range(len(ws)):
        if pal[j]["start"] < despues:
            continue
        for k in range(len(toks)):
            if toks[k:k + 1] and ws[j] == toks[k] and (len(toks[k]) >= 4):
                return pal[j]
    return None


def pops(desde, hasta, n_max=12):
    """Los pops de una tanda de asientos: uno cada ~0.22 s, ≤ n_max (montar abre una entrada por efecto)."""
    if hasta - desde < 0.15:
        return [(desde, "voto")]
    k = max(1, min(n_max, int((hasta - desde) / 0.22)))
    return [(desde + (hasta - desde) * j / k, "voto") for j in range(k)]


def t_hemiciclo(S, e, ps, pal, fin_voz, dur, g):
    esc = escena_guion(S, g)
    cual = esc.get("votacion") or "decisiva"
    D = VOT[cual]
    fases = esc.get("fases") or ["llenar", "umbral"]
    asientos, idx, bancadas = orden_asientos(D)
    t0 = 0.05 if S.get("seguida") else VD.TRANSICION + 0.1
    ev, sfx = [(t0, "entra")], []
    T = {"modo": "escena", "votacion": cual, "asientos": [{"v": a["v"], "b": a["b"]} for a in asientos], "bancadas": bancadas,
         "umbral": {"n": D["umbral"], "etiqueta": "%d para aprobar" % D["umbral"] if cual == "decisiva" else "%d para la urgencia" % D["umbral"]},
         "cuentas": {k: D[k] for k in VOTOS}, "lleno": "llenar" not in fases, "fin": round(fin_voz, 3)}
    golpe = (esc.get("golpe") or "").split()
    if golpe:
        S["arriba"] = [{"text": w, "start": round(t0 + 0.12 * k, 3)} for k, w in enumerate(golpe)]
        ev.append((0.0, "golpe_arriba"))
    cursor = t0 + 0.3
    if "llenar" in fases:
        # cada lado se llena hasta que la voz dice su número (la tanda dura 0.8–3.2 s); si no lo dice, va seguido
        w_u = momento(pal, D["umbral"])
        w_f = momento(pal, D["favor"])
        fin_f = (w_f["start"] + 0.15) if w_f else min(cursor + 2.2, fin_voz - 1.0)
        ini_f = max(cursor, fin_f - 3.2)
        w_c = momento(pal, D["contra"], fin_f) if D["contra"] else None
        fin_c = (w_c["start"] + 0.15) if w_c else fin_f + 1.6
        ini_c = max(fin_f + 0.2, fin_c - 2.4)
        ini_a, fin_a = fin_f + 0.1, fin_f + 1.0
        T["llenar"] = {"favor": [round(ini_f, 3), round(fin_f, 3)], "contra": [round(ini_c, 3), round(fin_c, 3)],
                       "ausente": [round(ini_a, 3), round(fin_a, 3)]}
        t_um = (w_u["start"] - 0.05) if w_u else ini_f
        T["umbral"]["start"] = round(max(t0, t_um), 3)
        ev += [(ini_f, "llenar"), (fin_f, "lleno_favor"), (ini_c, "llenar_contra"), (fin_c, "lleno_contra"), (T["umbral"]["start"], "umbral")]
        sfx += pops(ini_f, fin_f) + (pops(ini_c, fin_c, 8) if D["contra"] else [])
        cruza = D["favor"] >= D["umbral"]
        t_res = max(fin_f, T["umbral"]["start"]) + 0.25
        T["resultado"] = {"start": round(t_res, 3), "aprobada": cruza}
        ev.append((t_res, "resultado"))
        sfx.append((t_res, "mazo"))
        cursor = fin_c + 0.4
    else:
        T["umbral"]["start"] = round(t0, 3)
    if "foco" in fases:
        focos, desde = [], cursor if "llenar" in fases else t0 + 0.4
        for k, fo in enumerate(esc.get("focos") or []):
            if fo.get("diputado"):
                d = diputado_por_nombre(fo["diputado"], D)
                w = momento_nombre(pal, d["corto"].split()[-1], desde) or momento_nombre(pal, d["corto"], desde)
                fot = "fotos/dip-%s.jpg" % d.get("id")
                item = {"tipo": "diputado", "asientos": [idx[d["nombre"]]], "nombre": d["corto"], "bancada": bancada_legible(d["bancada"]),
                        "voto": d["voto"], "foto": fot}
            else:
                b, voto = fo["bancada"], fo.get("voto") or "favor"
                w = momento_nombre(pal, bancada_legible(b), desde)
                item = {"tipo": "bancada", "asientos": [k2 for k2, a in enumerate(asientos) if bancadas[a["b"]] == bancada_legible(b) and a["v"] == voto[0]],
                        "nombre": bancada_legible(b), "voto": voto, "n": D["bancadas"][b].get(voto, 0)}
            item["start"] = round((w["start"] - 0.1) if w else desde + 0.3 + 1.6 * k, 3)
            desde = item["start"] + 0.6
            focos.append(item)
        for k, it in enumerate(focos):
            it["fin"] = round(focos[k + 1]["start"] - 0.05 if k + 1 < len(focos) else dur + 0.5, 3)   # el último se queda hasta el corte
            ev += [(it["start"], "foco"), (it["start"] + 0.5, "foco_nombre")]
            sfx.append((it["start"], "tic"))
        T["focos"] = focos
        cursor = (focos[-1]["start"] + 1.2) if focos else cursor
    if "barras" in fases:
        palabra = esc.get("barras_en")
        w = momento_nombre(pal, palabra, cursor) if palabra else None
        t_b = (w["start"] - 0.1) if w else min(max(cursor, fin_voz - 2.6), dur - 1.8)
        if T.get("focos"):   # las barras entran cuando termina el último foco (la ficha no se cruza con las columnas)
            t_b = max(t_b, T["focos"][-1]["start"] + 1.4)
            T["focos"][-1]["fin"] = round(min(T["focos"][-1]["fin"], t_b), 3)
        T["barras"] = {"start": round(t_b, 3)}
        ev += [(t_b, "barras"), (t_b + 1.0, "barras_fin")]
        sfx.append((t_b, "whoosh"))
    S["pagina"], S["T"] = "hemiciclo", T
    if not S.get("seguida"):
        sfx.insert(0, (0.0, "grave" if VD.RE_ENLACE["pero"].match(VD.sin_pausas(e.get("voz") or "").strip()) else "whoosh"))
    return ev, sfx


def t_gancho(S, e, ps, pal, fin_voz, dur, g):
    """El gancho con `mini`: la foto a sangre y el hemiciclo de la votación en un círculo que se llena con la voz y, al
    final, se abre hacia la escena siguiente (el portal). Sin `mini`: el gancho con foto de video.py."""
    esc = escena_guion(S, g)
    vis = e.get("visual") or {}
    if not esc.get("mini") or vis.get("tipo") != "foto":
        return VD.t_gancho_foto(S, e, ps, pal, fin_voz, dur, g)
    D = VOT[esc["mini"]]
    asientos, _, bancadas = orden_asientos(D)
    cin = e.get("cinetico") or {}
    fin_1 = VD.fin_oracion_desde(pal, 0)
    linea, _ = VD.alinear_linea((cin.get("linea") or "").split(), pal, 0.0, max(0.4, fin_1))
    w_f = momento(pal, D["favor"])
    fin_f = (w_f["start"] + 0.1) if w_f else min(2.2, fin_voz - 0.5)
    es = g.get("escenas") or []
    sigue_hem = len(es) > 1 and es[1].get("tipo") == "hemiciclo"
    S["pagina"] = "hemiciclo"
    S["T"] = {"modo": "gancho", "votacion": esc["mini"], "asientos": [{"v": a["v"], "b": a["b"]} for a in asientos], "bancadas": bancadas,
              "umbral": {"n": D["umbral"], "start": 0.0}, "cuentas": {k: D[k] for k in VOTOS},
              "llenar": {"favor": [0.25, round(max(0.9, fin_f), 3)], "contra": [round(max(0.9, fin_f) + 0.1, 3), round(max(0.9, fin_f) + 0.7, 3)],
                         "ausente": [round(max(0.9, fin_f), 3), round(max(0.9, fin_f) + 0.5, 3)]},
              "foto": vis.get("foto"), "credito": vis.get("credito"), "encaje": vis.get("encaje"),
              "pantalla": cin.get("pantalla") or "", "linea": linea, "etiqueta": vis.get("etiqueta") or "",
              # «pant» como en el gancho de video.py: montar elige la portada cuando el hemiciclo del círculo está lleno
              "pant": {"texto": cin.get("pantalla") or "", "v": None, "desde": 0.0, "hasta": round(max(0.9, fin_f) + 0.6, 3), "pulso": None},
              "portal": [round(max(fin_voz, dur - 0.55), 3), round(dur, 3)] if sigue_hem else None, "fin": round(fin_voz, 3)}
    ev = [(0.0, "titular"), (0.25, "llenar"), (max(0.9, fin_f), "lleno_favor")] + [(w["start"], "linea_dicha") for w in linea if w.get("dicha")]
    sfx = [(0.1, "impacto")] + pops(0.25, max(0.9, fin_f), 6)
    if S["T"]["portal"]:
        ev.append((S["T"]["portal"][0], "portal"))
    return ev, sfx


# ---------- guion, tiempos y entrega ----------
def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    f, _ = revisar_ley(trabajo)
    for x in f:
        print("FALLA", x)
    aplicar_extension(trabajo)
    rc = VD.cmd_guion(argparse.Namespace(trabajo=trabajo, check=True))
    return 1 if f else rc


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    aplicar_extension(trabajo)
    rc = VD.cmd_tiempos(argparse.Namespace(trabajo=trabajo))
    ruta = os.path.join(trabajo, "escenas.json")
    if not os.path.exists(ruta):
        return rc or 1
    E = leer(ruta)
    E["tipo"] = "congreso"
    escribir(ruta, E)
    total = E["total_s"] + VD.BUCLE_S
    if total > TECHO_S:
        print("FALLA CG7 %.1f s reales con el bucle: /congreso va por debajo del minuto (≤ %.1f s); acorta la voz" % (total, TECHO_S))
        return 1
    return rc


def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    if not os.path.exists(os.path.join(trabajo, "audio", "creditos.json")) and not a.salida:
        return falla("sin audio/creditos.json: la voz no salió de ElevenLabs (una voz falsa solo se entrega con --salida)")
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, "congreso", "%s-%s" % (st["fecha"], st["slug"])))
    rc = VD.cmd_entregar(argparse.Namespace(trabajo=trabajo, salida=destino))
    if rc:
        return rc
    V = leer(os.path.join(trabajo, "votacion.json"))
    L = leer(os.path.join(trabajo, "ley.json")) if os.path.exists(os.path.join(trabajo, "ley.json")) else {}
    ruta = os.path.join(destino, "guion.json")
    ent, g = leer(ruta), leer(os.path.join(trabajo, "guion.json"))
    nombrados = [{"nombre": x["nombre"], "voto": x["voto"]} for e in g.get("escenas") or [] for x in e.get("diputados") or []]
    ent.update({"id": "congreso-%s" % st["slug"], "tipo": "congreso", "fecha": st["fecha"], "iniciativa": V["iniciativa"],
                "ley": L.get("titulo"), "votacion": {k: V["decisiva"][k] for k in ("fecha", "clase", "umbral", *VOTOS)},
                "nombrados": nombrados})
    escribir(ruta, ent)
    shutil.copyfile(os.path.join(trabajo, "votos_ley.csv"), os.path.join(destino, "votos.csv"))
    D = V["decisiva"]
    fu = ["# Fuentes · %s" % (L.get("titulo") or "iniciativa %s" % V["iniciativa"]), "",
          "## Votación (registro nominal oficial)", "- %s · %s" % (D["pregunta"], D["url"])]
    if V.get("urgencia"):
        fu.append("- %s · %s" % (V["urgencia"]["pregunta"], V["urgencia"]["url"]))
    fu += ["- Umbral: Ley Orgánica del Organismo Legislativo (Decreto 63-94), art. 99 · %s" % LEY_ORGANICA["url"], "", "## Qué buscaba y estado"]
    fu += ["- %s · %s" % (x["texto"], x["url"]) for x in (L.get("que_busca") or []) + ([L["estado"]] if L.get("estado") else [])]
    fu += ["", "## Fotos"] + ["- %s · %s" % (r.get("descripcion", ""), r.get("credito", "")) for r in VD.fotos_trabajo(trabajo).values()]
    open(os.path.join(destino, "fuentes.md"), "w", encoding="utf-8").write("\n".join(fu) + "\n")
    print("→ %s (%s s)" % (VD.rel(destino), ent.get("duracion_s")))
    return 0


REENVIO = ("voz", "voz-falsa", "descargar", "escuchar", "grabar", "montar", "revisar")


def main():
    if len(sys.argv) > 1 and sys.argv[1] in REENVIO:
        return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video.py")] + sys.argv[1:], cwd=RAIZ).returncode
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("importar")
    q.add_argument("captura")
    q.add_argument("--dry-run", action="store_true")
    sub.add_parser("padron").add_argument("captura", nargs="+", help="captura con el padrón (y otras con listados nominales)")
    q = sub.add_parser("proponer")
    q.add_argument("--dias", type=int, default=21)
    q.add_argument("--n", type=int, default=6)
    q = sub.add_parser("preparar")
    q.add_argument("iniciativa")
    q.add_argument("--slug")
    q.add_argument("--trabajo")
    q.add_argument("--paleta", choices=PALETAS)
    q.add_argument("--musica")
    q.add_argument("--fixture", action="store_true", help="pruebas: sin rotación")
    q.add_argument("--semilla", help="carpeta con votacion.json, datos.json, ley.json, fotos/ y fuentes/ (la maqueta)")
    q = sub.add_parser("ley")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q = sub.add_parser("leer")
    q.add_argument("trabajo")
    q.add_argument("captura")
    q = sub.add_parser("fotos")
    q.add_argument("trabajo")
    q.add_argument("--captura")
    q.add_argument("--diputados", nargs="*")
    sub.add_parser("digesto").add_argument("trabajo")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    sub.add_parser("tiempos").add_argument("trabajo")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida")
    a = p.parse_args()
    return {"importar": cmd_importar, "padron": cmd_padron, "proponer": cmd_proponer, "preparar": cmd_preparar, "ley": cmd_ley,
            "leer": cmd_leer, "fotos": cmd_fotos, "digesto": cmd_digesto, "guion": cmd_guion, "tiempos": cmd_tiempos,
            "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
