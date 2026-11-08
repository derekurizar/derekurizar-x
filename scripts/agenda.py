#!/usr/bin/env python3
"""/agenda: el content manager de la semana — qué se publica cada día, en qué plataforma y a qué hora, y qué hay que
producir para que ningún espacio quede vacío. Solo stdlib.

Decisiones del usuario (2026-11-03): como máximo 2 videos al día. El espacio A es una pieza fuerte (historia, explica,
parte de serie, /video de un hilo) y el B una pieza corta (¿Sabías que…?, mito, departamento). El carrusel va aparte (no es
video, ≤ 1 al día). **No se publican noticieros**: /noticias y /semana no se programan. Planifica producción y publicación;
sin tope de créditos (el plan muestra la estimación). Corrido a mitad de semana, planifica el resto: lo producido, publicado
o con tema elegido se conserva.

Espacios: A · pieza fuerte 09:00 · B · pieza corta 19:30 · C · carrusel 13:00 (opcional). Cada video va a TikTok,
Instagram Reels, Facebook Reels y YouTube Shorts en 9:16 y el 4:5 al feed de Instagram y Facebook. **Facebook**: cada video
lleva un estilo de descripción que rota (historia, pregunta, dato, lista: ESTILOS_FB); la sesión la escribe con
`facebook SLOT --texto` y `metricas.py rendimiento --por estilo_fb` compara cuál funciona.

Cómo se llenan los espacios (en orden):
1. Lo listo sin publicar (registros de memoria/ cruzados con memoria/metricas.json; aviso si se parece a algo publicado
   hace < 30 días): lo corto al B, lo demás al A.
2. Partes de /serie que ya se pueden publicar (A).
3. Fechas del calendario (≤ 2): un dato → /dato + /sabias en el B; un hilo → /hilo + /video en el A. Nunca antes de su
   fecha.
4. El siguiente /departamento (≤ 1 por semana, B).
5. La mezcla: el A con ≥ 3 historias y 1 explica; el B alterna «¿Sabías que…?» y mito. Nunca el mismo formato dos días
   seguidos en el mismo espacio, salvo historia.

Lo que no tiene pieza es una orden de producción (comando, día para producirla, minutos y créditos estimados); el tema lo
propone la sesión y lo elige el usuario (`tema`).

Subcomandos (DIR = agenda/<AAAA-Wnn>/ de la semana; --dir otro):
  plan [--desde AAAA-MM-DD] [--memoria DIR] [--dir DIR]   arma (o rehace: lo producido, publicado o con tema elegido se
                                                          conserva) los espacios de hoy al domingo → agenda.json + agenda.md +
                                                          agenda.html (para abrir: órdenes en orden, días, archivos, captions)
  tema SLOT "<tema>" [--formato F] [--dir DIR]            el tema que eligió el usuario (AG4: no repite lo producido)
  producido SLOT --ruta DIR_ENTREGA [--dir DIR]           liga la pieza entregada al espacio
  publicado SLOT [--plataforma P|todas] [--dir DIR]       marca la publicación (la hora real; /analyze-improve la mide)
  facebook SLOT --texto "…" [--estilo E] [--dir DIR]     la descripción de Facebook del espacio en su estilo (F4: sin cebo)
  omitir PIEZA [--motivo M] [--dir DIR]                  una pieza lista que el usuario no quiere publicar: sale de la agenda
  hoy [--fecha F] [--dir DIR]                             la lista del día: qué producir ahora y qué publicar, con el archivo
                                                          de cada plataforma y el bloque de caption.md
  --check [--dir DIR]                                     AG1–AG9 sobre agenda.json (también lo corre validate.py como M18)

Gates: AG1 ≤ 2 videos por día · AG2 el A lleva una pieza fuerte y el B una corta; ningún noticiero ni /semana · AG3 sin
el mismo formato en días seguidos en el mismo espacio, salvo historia · AG4 sin repetir un tema producido en los últimos 60 días ni
otro de la agenda · AG5 una parte de serie solo cuando la siguiente tiene guion aprobado · AG6 cada orden de producción
vence antes de su espacio · AG7 una pieza ya publicada no se vuelve a programar · AG8 cada video a las 4 plataformas, con su estilo de Facebook ·
AG9 ≤ 1 carrusel por día.

Exit: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))

PLATAFORMAS_VIDEO = ("tiktok", "instagram", "facebook", "youtube")
PLATAFORMAS_CARRUSEL = ("instagram", "facebook", "tiktok")
HORA = {"A": "09:00", "B": "19:30", "C": "13:00"}
VIDEOS_POR_DIA = 2
CARRUSELES_POR_DIA = 1
# formato → (comando, días antes para producir, minutos, créditos de voz estimados; CLAUDE.md)
FORMATOS = {
    "historia": ("/historia <tema>", 1, 45, 2200),
    "explica": ("/explica <tema>", 1, 35, 1700),
    "mito": ("/mito <creencia>", 1, 30, 1000),
    "departamento": ("/departamento siguiente", 1, 60, 1000),
    "serie": ("/serie <tema> (parte N)", 1, 30, 1250),
    "sabias": ("/sabias <pista>", 0, 25, 400),
    "congreso": ("/congreso <iniciativa>", 1, 25, 800),
    "video": ("/video <slug>", 1, 30, 1700),
    "noticias": ("/noticias", 0, 30, 850),
    "semana": ("/semana", 0, 30, 1200),
    "carrusel": ("/carrusel <slug>", 0, 10, 0),
}
FUERTES = ("historia", "explica", "serie", "video")               # espacio A
CORTAS = ("sabias", "mito", "departamento", "congreso")            # espacio B (20–90 s)
ROTACION_CORTAS = ("sabias", "mito")                               # lo que alterna el espacio B
SIN_AGENDA = ("noticias", "semana")   # el usuario no publica noticieros (2026-11-03): /noticias y /semana no se programan
# estilos de la descripción de Facebook (rotan; /analyze-improve compara cuál funciona). Ninguno pide comentar, compartir ni
# etiquetar (F4: Meta lo penaliza)
ESTILOS_FB = {"pregunta": "Abre con la pregunta que el video responde (una sola, concreta, sin cebo) y una línea de contexto.",
              "lista": "Una línea de gancho y 3–5 viñetas «▸» con las cifras del video, cada una con su referente; al final la fuente.",
              "historia": "Un párrafo narrado como relato (quién, dónde, qué pasó), sin cifras en la primera línea; la cifra llega en la segunda.",
              "dato": "Abre con la cifra más fuerte y su referente en la primera línea; luego por qué importa en una oración."}
ESTILOS_FB_ORDEN = ("historia", "pregunta", "dato", "lista")
REPITEN = ("historia",)                 # AG3: el único formato fuerte que puede ir dos días seguidos
MEZCLA_MIN = {"historia": 3, "explica": 1}
DIAS_REPETIDO, DIAS_PARECIDO = 60, 30
ESTADOS = ("propuesto", "tema", "producido", "publicado")
MIN_OPCIONES, MAX_OPCIONES = 2, 3   # opciones de tema por espacio (la primera queda como tema: la semana queda lista)
FLUJO_DE_FORMATO = {"historia": "historia", "explica": "explica", "mito": "explica", "sabias": "sabias", "congreso": "congreso", "video": "video",
                    "departamento": "video", "noticias": "noticias", "semana": "semana", "serie": "serie", "carrusel": "carrusel"}
REGISTROS = (("videos.json", "videos", "video", "ruta_video"), ("historias.json", "historias", "historia", "ruta"),
             ("noticias.json", "noticieros", "noticias", "ruta"), ("sabias.json", "sabias", "sabias", "ruta"),
             ("congreso.json", "congreso", "congreso", "ruta"),
             ("explicaciones.json", "explicaciones", "explica", "ruta"), ("semanas.json", "semanas", "semana", "ruta"),
             ("carruseles.json", "carruseles", "carrusel", "ruta"))
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
STOP = set("de del la el los las en y a o que un una al lo se por para con como su sus es guatemala historia maqueta publica "
           "publicacion anterior mensual frente pais datos".split())
CALENDARIO_MAX = 2      # fechas del calendario por semana (las publicaciones mensuales pueden caer juntas)


def leer(p, defecto=None):
    if not os.path.exists(p):
        return defecto
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def rel(p):
    return os.path.relpath(p, RAIZ)


def plano(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def claves(*textos):
    return {w[:6] for t in textos for w in re.findall(r"[a-zñ]+", plano(t)) if len(w) >= 4 and w not in STOP}


def parecido(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def fecha(t):
    return datetime.date.fromisoformat(str(t)[:10])


def semana_iso(d):
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


def dir_semana(d, otro=None):
    return os.path.abspath(otro) if otro else os.path.join(RAIZ, "agenda", semana_iso(d))


# ---------- inventario ----------
def inventario(memdir):
    """Las piezas de los registros con sus plataformas publicadas (memoria/metricas.json) → [{flujo, id, slug, tema, fecha,
    ruta, publicadas[], claves}]."""
    pubs = (leer(os.path.join(memdir, "metricas.json"), {}) or {}).get("publicaciones", [])
    plats, fechas_pub = {}, {}
    for p in pubs:
        pz = p.get("pieza")
        if pz:
            k = (pz["flujo"], pz["id"])
            plats.setdefault(k, set()).add(p["plataforma"])
            f = str(p.get("fecha_pub") or "")[:10]
            if f and (k not in fechas_pub or f < fechas_pub[k]):
                fechas_pub[k] = f
    out = []
    for archivo, clave, flujo, campo in REGISTROS:
        for v in (leer(os.path.join(memdir, archivo), {}) or {}).get(clave, []):
            k = (flujo, v.get("id"))
            out.append({"flujo": flujo, "id": v.get("id"), "slug": v.get("slug") or v.get("id"), "tema": v.get("tema") or "",
                        "fecha": v.get("fecha"), "ruta": v.get(campo), "estado": v.get("estado"),
                        "publicadas": sorted(plats.get(k, [])), "fecha_pub": fechas_pub.get(k) or (v.get("fecha") if v.get("estado") == "publicado" else None),
                        "claves": sorted(claves(v.get("tema"), v.get("slug") or v.get("id"), v.get("creencia")))})
    return out


def formato_de_pieza(x):
    if x["flujo"] == "explica":
        return "mito" if "mito" in (x.get("slug") or "") else "explica"
    return x["flujo"]


def listas(inv):
    """Lo listo sin publicar en ninguna plataforma (programable), con aviso si se parece a algo publicado hace poco."""
    publicadas = [x for x in inv if x["publicadas"]]
    out = []
    for x in inv:
        if x["publicadas"] or x.get("estado") not in ("listo", "publicado") or x["flujo"] in ("noticias", "semana"):
            continue
        aviso = None
        for y in publicadas:
            if y is x or not y.get("fecha_pub"):
                continue
            if parecido(set(x["claves"]), set(y["claves"])) >= 0.5:
                aviso = "se parece a «%s», publicada el %s: publícala solo si el ángulo es otro" % (y["slug"], y["fecha_pub"])
                break
        out.append(dict(x, aviso=aviso))
    return out


def incompletas(inv):
    """Piezas publicadas en algunas plataformas y no en todas (se listan aparte para completarlas, no ocupan espacio)."""
    return [x for x in inv if x["publicadas"] and x["flujo"] != "carrusel" and set(x["publicadas"]) != set(PLATAFORMAS_VIDEO)]


# ---------- fuentes de espacios ----------
def calendario_en(desde, hasta):
    try:
        import calendario as CAL
    except Exception:  # noqa: BLE001
        return []
    out = []
    for e in CAL.cargar()["entradas"]:
        for s in CAL.specs_de(e):
            o = CAL.proxima(s, desde)
            if o and o <= hasta and CAL.vigente(e, s, o):
                out.append({"fecha": o.isoformat(), "id": e.get("id"), "titulo": e.get("titulo"), "formato": e.get("formato") or "dato",
                            "modo": e.get("modo"), "pista": e.get("pista")})
    return sorted(out, key=lambda x: x["fecha"])


def series_publicables(memdir=None):
    """Las partes de /serie que ya se pueden publicar. Con otra carpeta de registros (la maqueta), solo las series que
    ella registra en series.json: las series reales en series/ no entran en una semana de prueba."""
    out = []
    propia = os.path.abspath(os.path.join(RAIZ, "memoria"))
    permitidas = None
    if memdir and os.path.abspath(memdir) != propia:
        reg = leer(os.path.join(memdir, "series.json")) if os.path.exists(os.path.join(memdir, "series.json")) else {}
        permitidas = {x.get("slug") for x in (reg.get("series") if isinstance(reg, dict) else reg) or [] if isinstance(x, dict)}
    for sj in sorted(__import__("glob").glob(os.path.join(RAIZ, "series", "*", "serie.json"))):
        try:
            import serie as SR
            S = leer(sj)
            if permitidas is not None and S.get("slug") not in permitidas:
                continue
            for p in S.get("partes") or []:
                if SR.publicable(S, p) and not p.get("publicada"):
                    out.append({"serie": S["slug"], "n": p["n"], "de": len(S["partes"]), "titulo": p["titulo"], "ruta": p.get("ruta"),
                                "carpeta": S["carpeta"]})
        except Exception:  # noqa: BLE001
            continue
    return out


def departamento_siguiente():
    try:
        import departamentos as DP
        f = DP.siguiente()
        return f and {"codigo": f.get("codigo"), "nombre": f.get("nombre"), "canon": DP.canon().get("estado")}
    except Exception:  # noqa: BLE001
        return None


def mezcla(n, rendimiento):
    """Los formatos de los n espacios A sin pieza: historia en todos menos uno, que es explica (con ≥ 4 espacios); el orden
    deja la explica a mitad de semana. La historia es lo que más retiene en esta cuenta (metricas.py rendimiento)."""
    if n <= 0:
        return []
    out = ["historia"] * n
    if n >= MEZCLA_MIN["historia"] + MEZCLA_MIN["explica"]:
        out[n // 2] = "explica"
    return out


def rendimiento_formatos(memdir):
    try:
        import metricas as MT
        MT.METRICAS = os.path.join(memdir, "metricas.json")
        r = MT.rendimiento("flujo")
        return {"historia": (r.get("historia") or {}).get("hold3"), "explica": (r.get("explica") or {}).get("hold3"),
                "mito": (r.get("explica") or {}).get("hold3"), "sabias": (r.get("sabias") or {}).get("hold3"),
                "video": (r.get("video") or {}).get("hold3")}
    except Exception:  # noqa: BLE001
        return {}


# ---------- plan ----------
def espacio(d, slot, formato, **kw):
    hora = HORA[slot]
    com, antes, minutos, cred = FORMATOS[formato]
    plataformas = PLATAFORMAS_CARRUSEL if formato == "carrusel" else PLATAFORMAS_VIDEO
    s = {"id": "%s-%s" % (d.isoformat(), slot), "fecha": d.isoformat(), "dia": DIAS[d.weekday()], "slot": slot, "hora": hora,
         "formato": formato, "pieza": None, "tema": None, "comando": com, "producir_el": (d - datetime.timedelta(days=antes)).isoformat(),
         "minutos": minutos, "creditos": cred, "plataformas": list(plataformas), "estado": "propuesto", "avisos": [], "publicado": {}}
    s.update(kw)
    return s


def con_pieza(s, x):
    s.update(pieza={"flujo": x["flujo"], "id": x["id"], "ruta": x["ruta"]}, tema=x.get("tema") or x.get("slug"), estado="producido",
             comando=None, producir_el=None, minutos=0, creditos=0)
    if x.get("aviso"):
        s["avisos"].append(x["aviso"])
    return s


def ya_paso(d, slot, ahora):
    """¿El espacio de hoy ya pasó su hora? (no se planifica lo que ya no se puede publicar)."""
    if not ahora or d != ahora.date():
        return False
    return ahora.strftime("%H:%M") > HORA[slot]


def armar(desde, memdir, previo=None, ahora=None):
    hasta = desde + datetime.timedelta(days=6 - desde.weekday())
    dias = [desde + datetime.timedelta(days=k) for k in range((hasta - desde).days + 1)]
    inv = inventario(memdir)
    omitidas = list((previo or {}).get("omitidas") or [])
    previos = {s["id"]: s for s in (previo or {}).get("espacios", [])
               if not (s.get("pieza") and s["pieza"].get("id") in {o["id"] for o in omitidas} and s.get("estado") != "publicado")
               and s.get("formato") not in SIN_AGENDA}
    # lo de antes de `desde` y lo que ya avanzó (tema elegido, producido, publicado) se conserva tal cual
    conservar = {k: s for k, s in previos.items() if s["fecha"] < desde.isoformat() or s.get("estado") in ("tema", "producido", "publicado")}
    # lo de hoy que ya pasó su hora sin publicarse vuelve al inventario; un espacio del calendario repetido se queda una vez
    vistos = set()
    for k, s in sorted(conservar.items()):
        pasado = s["fecha"] >= desde.isoformat() and s.get("estado") != "publicado" and ya_paso(fecha(s["fecha"]), s["slot"], ahora)
        repetido = s.get("calendario") and s["calendario"] in vistos
        # un espacio de otra versión de la agenda que no cabe en su tipo (una pieza corta en el A) y no está producido se
        # vuelve a colocar (el calendario y el departamento lo ponen en su espacio)
        fuera = s["fecha"] >= desde.isoformat() and s.get("estado") == "tema" and (
            (s["slot"] == "A" and s["formato"] not in FUERTES) or (s["slot"] == "B" and s["formato"] not in CORTAS))
        if pasado or repetido or fuera:
            del conservar[k]
        elif s.get("calendario"):
            vistos.add(s["calendario"])
    for s in conservar.values():
        if s.get("estado") != "publicado" and s["fecha"] >= desde.isoformat():
            s["hora"] = HORA[s["slot"]]
    usados = {(s["pieza"]["flujo"], s["pieza"]["id"]) for s in conservar.values() if s.get("pieza")}
    listos = [x for x in listas(inv) if (x["flujo"], x["id"]) not in usados and x["id"] not in {o["id"] for o in omitidas}]
    espacios = [s for s in conservar.values() if s["fecha"] < desde.isoformat()]
    libres = {"A": [], "B": []}
    for d in dias:
        for slot in ("A", "B", "C"):
            k = "%s-%s" % (d.isoformat(), slot)
            if k in conservar:
                espacios.append(conservar[k])
            elif slot in libres and not ya_paso(d, slot, ahora):
                libres[slot].append(d)
    asignados = {"A": {}, "B": {}}

    def fijo(slot, d):
        return asignados[slot].get(d) or next((s for s in espacios if s["slot"] == slot and s["fecha"] == d.isoformat()), None)

    def vecino(slot, d, fmt):
        return any((fijo(slot, d + datetime.timedelta(days=k)) or {}).get("formato") == fmt for k in (-1, 1))

    def poner(slot, d, s):
        libres[slot].remove(d)
        asignados[slot][d] = s
    # 1) lo listo sin publicar: lo corto al espacio B, lo demás al A
    videos_listos = [x for x in listos if x["flujo"] != "carrusel"]
    carr_listos = [x for x in listos if x["flujo"] == "carrusel"]
    for x in sorted(videos_listos, key=lambda x: (x.get("aviso") is not None, x.get("fecha") or "")):
        fmt = formato_de_pieza(x)
        slot = "B" if fmt in CORTAS else "A"
        d = next((dd for dd in libres[slot] if not vecino(slot, dd, fmt)), None)
        if d:
            poner(slot, d, con_pieza(espacio(d, slot, fmt), x))
    # 2) partes de /serie (espacio A)
    for sp in series_publicables(memdir):
        if not libres["A"]:
            break
        d = libres["A"][0]
        poner("A", d, espacio(d, "A", "serie", tema="%s · Parte %d de %d: %s" % (sp["serie"], sp["n"], sp["de"], sp["titulo"]),
                              estado="producido" if sp.get("ruta") else "tema",
                              pieza={"flujo": "serie", "id": "%s-parte-%d" % (sp["serie"], sp["n"]), "ruta": sp.get("ruta")}))
    # 3) el calendario: un dato → «¿Sabías que…?» en el espacio B; un hilo → /video en el A (respetando la reserva de historias)
    hist = sum(1 for s in list(asignados["A"].values()) + espacios if s["slot"] == "A" and s["formato"] == "historia")
    cupo_a = max(0, len(libres["A"]) - min(len(libres["A"]), max(0, MEZCLA_MIN["historia"] - hist)))
    pospuestas = []
    ya = {s.get("calendario") for s in espacios + list(asignados["A"].values()) + list(asignados["B"].values()) if s.get("calendario")}
    for c in [x for x in calendario_en(dias[0], dias[-1]) if x["id"] not in ya][:max(0, CALENDARIO_MAX - len(ya))]:
        es_dato = c["formato"].startswith("dato")
        slot, fmt = ("B", "sabias") if es_dato else ("A", "video")
        d0 = fecha(c["fecha"])
        # nunca antes de su fecha (el dato todavía no existe); si no cabe esta semana, pasa a la siguiente
        cands = sorted((x for x in libres[slot] if x >= d0), key=lambda x: (x - d0).days)
        d = next((x for x in cands if not vecino(slot, x, fmt)), None)
        if not d or (slot == "A" and cupo_a <= 0):
            pospuestas.append(c)
            continue
        if slot == "A":
            cupo_a -= 1
        poner(slot, d, espacio(d, slot, fmt, tema=c["titulo"], estado="tema", calendario=c["id"],
                               comando=("/fecha %s (→ /dato%s y /sabias)" % (c["id"], " " + c["modo"] if c.get("modo") else "")) if es_dato
                               else "/fecha %s (→ /hilo y /video)" % c["id"]))
    # 4) el siguiente /departamento (≤ 1 por semana, espacio B)
    dep = departamento_siguiente()
    todos = espacios + list(asignados["A"].values()) + list(asignados["B"].values())
    if dep and libres["B"] and not any(s["formato"] == "departamento" for s in todos):
        d = next((x for x in libres["B"][len(libres["B"]) // 2:] + libres["B"] if not vecino("B", x, "departamento")), None)
        if d:
            poner("B", d, espacio(d, "B", "departamento", tema="%s frente al país" % dep["nombre"], estado="tema",
                                  comando="/departamento %s" % dep["nombre"]))
            if dep.get("canon") == "propuesta":
                asignados["B"][d]["avisos"].append("el canon de /departamento sigue en propuesta: apruébalo (referencias/departamentos.json) antes de producir")
    # 5) la mezcla: A con ≥ 3 historias y ≥ 1 explica; B alterna «¿Sabías que…?» y mito sin repetir en días seguidos
    rend = rendimiento_formatos(memdir)
    for d, f in zip(sorted(libres["A"]), mezcla(len(libres["A"]), rend)):
        asignados["A"][d] = espacio(d, "A", f)
    libres["A"] = []
    for d in sorted(libres["B"]):
        f = next((x for x in ROTACION_CORTAS if not vecino("B", d, x)), ROTACION_CORTAS[0])
        asignados["B"][d] = espacio(d, "B", f)
    libres["B"] = []
    espacios += list(asignados["A"].values()) + list(asignados["B"].values())
    # C · un carrusel listo, el primer día libre
    for x in carr_listos:
        d = next((dd for dd in dias if not ya_paso(dd, "C", ahora)
                  and not any(s["fecha"] == dd.isoformat() and s["slot"] == "C" for s in espacios)), None)
        if d:
            espacios.append(con_pieza(espacio(d, "C", "carrusel"), x))
    if ahora and not any(s["fecha"] == desde.isoformat() for s in espacios):
        desde = desde + datetime.timedelta(days=1)   # hoy ya no queda nada que publicar: la agenda empieza mañana
    hoy = desde.isoformat()
    for s in espacios:
        if s.get("producir_el") and s["producir_el"] < hoy and s["estado"] in ("propuesto", "tema") and s["fecha"] >= hoy:
            s["avisos"].append("va tarde: producir HOY (%s)" % hoy)
            s["producir_el"] = hoy
    espacios.sort(key=lambda s: (s["fecha"], {"A": 0, "C": 1, "B": 2}[s["slot"]]))
    _desempatar(espacios)
    asignar_estilos_facebook(espacios)
    return {"version": 2, "semana": semana_iso(desde), "desde": desde.isoformat(), "hasta": hasta.isoformat(),
            "generado": datetime.date.today().isoformat(), "espacios": espacios, "omitidas": omitidas,
            "pospuestas": [{"id": c["id"], "fecha": c["fecha"], "titulo": c["titulo"]} for c in pospuestas],
            "incompletas": [{"flujo": x["flujo"], "id": x["id"], "ruta": x["ruta"], "faltan": [p for p in PLATAFORMAS_VIDEO if p not in x["publicadas"]]}
                            for x in incompletas(inv)]}


def asignar_estilos_facebook(espacios):
    """Cada video va a Facebook con un estilo de descripción que rota en la semana (lo que se conservó guarda el suyo), para
    que /analyze-improve compare cuál funciona (metricas.py rendimiento --por estilo_fb)."""
    videos = [s for s in espacios if s["formato"] != "carrusel"]
    usados = [s["facebook"]["estilo"] for s in videos if (s.get("facebook") or {}).get("estilo")]
    k = len(usados)
    for s in videos:
        if not (s.get("facebook") or {}).get("estilo"):
            s["facebook"] = {"estilo": ESTILOS_FB_ORDEN[k % len(ESTILOS_FB_ORDEN)], "texto": None}
            k += 1


def _desempatar(espacios):
    for slot in ("A", "B"):
        _desempatar_slot([s for s in espacios if s["slot"] == slot])


def _desempatar_slot(fuertes):
    for _ in range(len(fuertes)):
        cambio = False
        for a, b in zip(fuertes, fuertes[1:]):
            if a["formato"] == b["formato"] and a["formato"] not in REPITEN and b["estado"] == "propuesto":
                otro = next((c for c in fuertes if c["estado"] == "propuesto" and c["formato"] != b["formato"]
                             and c is not b and c is not a), None)
                if otro:
                    b["formato"], otro["formato"] = otro["formato"], b["formato"]
                    for s in (b, otro):
                        s["comando"], antes, s["minutos"], s["creditos"] = FORMATOS[s["formato"]][0], FORMATOS[s["formato"]][1], FORMATOS[s["formato"]][2], FORMATOS[s["formato"]][3]
                        s["producir_el"] = (fecha(s["fecha"]) - datetime.timedelta(days=antes)).isoformat()
                    cambio = True
        if not cambio:
            return


# ---------- gates ----------
def revisar(A, memdir, listo=False):
    """AG1–AG9 (y con listo, AG10: cada espacio por producir tiene tema, el del usuario o la opción recomendada)."""
    f = []
    if listo:
        for s in A.get("espacios") or []:
            if s["fecha"] >= A.get("desde", s["fecha"]) and s["estado"] in ("propuesto", "tema") and s["formato"] != "carrusel":
                if not s.get("tema"):
                    f.append("AG10 %s: sin tema (escribe sus opciones: agenda.py opciones %s --opcion «…|…» --opcion «…|…»)" % (s["id"], s["id"]))
    esp = A.get("espacios") or []
    por_dia = {}
    for s in esp:
        por_dia.setdefault(s["fecha"], []).append(s)
    inv = {(x["flujo"], x["id"]): x for x in inventario(memdir)}
    for d, ss in sorted(por_dia.items()):
        videos = [s for s in ss if s["formato"] != "carrusel"]
        if len(videos) > VIDEOS_POR_DIA:
            f.append("AG1 %s: %d videos (van ≤ %d; el carrusel no cuenta)" % (d, len(videos), VIDEOS_POR_DIA))
        for s in ss:
            if s["formato"] in SIN_AGENDA:
                f.append("AG2 %s: %s en la agenda (el usuario no publica noticieros: el espacio B es una pieza corta)" % (s["id"], s["formato"]))
            elif s["slot"] == "B" and s["formato"] not in CORTAS:
                f.append("AG2 %s: el espacio B lleva una pieza corta (%s), no %s" % (s["id"], "|".join(CORTAS), s["formato"]))
            elif s["slot"] == "A" and s["formato"] not in FUERTES:
                f.append("AG2 %s: el espacio A lleva una pieza fuerte (%s), no %s" % (s["id"], "|".join(FUERTES), s["formato"]))
        if sum(1 for s in ss if s["formato"] == "carrusel") > CARRUSELES_POR_DIA:
            f.append("AG9 %s: más de %d carrusel" % (d, CARRUSELES_POR_DIA))
    for slot in ("A", "B"):
        serie_slot = sorted([s for s in esp if s["slot"] == slot], key=lambda s: s["fecha"])
        for a, b in zip(serie_slot, serie_slot[1:]):
            if a["formato"] == b["formato"] and a["formato"] not in REPITEN and (fecha(b["fecha"]) - fecha(a["fecha"])).days == 1:
                f.append("AG3 %s y %s: dos «%s» seguidos (solo historia puede repetir)" % (a["id"], b["id"], a["formato"]))
    for s in esp:
        est = (s.get("facebook") or {}).get("estilo")
        if s["formato"] != "carrusel" and est not in ESTILOS_FB:
            f.append("AG8 %s: el estilo de Facebook «%s» no es uno de %s" % (s["id"], est, "|".join(ESTILOS_FB)))
    hoy = fecha(A.get("desde") or datetime.date.today().isoformat())
    producidos = [x for x in inv.values() if x.get("fecha") and (hoy - fecha(x["fecha"])).days <= DIAS_REPETIDO]
    temas = []
    for s in esp:
        if s["formato"] in ("noticias", "semana") or not s.get("tema") or s.get("pieza"):
            continue
        ks = claves(s["tema"])
        for x in producidos:
            if parecido(ks, set(x["claves"])) >= 0.6:
                f.append("AG4 %s: «%s» repite «%s» (producido el %s)" % (s["id"], s["tema"][:50], x["slug"], x["fecha"]))
                break
        for t_id, t in temas:
            if parecido(ks, t) >= 0.6:
                f.append("AG4 %s: «%s» repite el tema de %s en esta agenda" % (s["id"], s["tema"][:50], t_id))
        temas.append((s["id"], ks))
    for s in esp:
        if s["formato"] == "serie" and s.get("pieza") and s["estado"] != "publicado":
            m = re.match(r"^(.*)-parte-(\d+)$", s["pieza"]["id"])
            if m:
                try:
                    import serie as SR
                    ruta, S = SR.cargar_serie(m.group(1))
                    p = next((x for x in S["partes"] if x["n"] == int(m.group(2))), None)
                    if p and not SR.publicable(S, p):
                        f.append("AG5 %s: la parte %s se publica cuando la %d tenga el guion aprobado" % (s["id"], m.group(2), int(m.group(2)) + 1))
                except SystemExit:
                    f.append("AG5 %s: no encuentro la serie %s" % (s["id"], m.group(1)))
        if s["estado"] in ("propuesto", "tema") and s.get("producir_el") and s["producir_el"] > s["fecha"]:
            f.append("AG6 %s: se produce el %s, después de su espacio" % (s["id"], s["producir_el"]))
        if s.get("pieza") and s["estado"] != "publicado":
            x = inv.get((s["pieza"]["flujo"], s["pieza"]["id"]))
            if x and x["publicadas"] and not s.get("publicado"):
                f.append("AG7 %s: %s ya está publicada en %s" % (s["id"], s["pieza"]["id"], ", ".join(x["publicadas"])))
        if s["formato"] != "carrusel" and set(s.get("plataformas") or []) != set(PLATAFORMAS_VIDEO):
            f.append("AG8 %s: un video va a %s (llegó %s)" % (s["id"], ", ".join(PLATAFORMAS_VIDEO), ", ".join(s.get("plataformas") or [])))
        if s.get("estado") not in ESTADOS:
            f.append("M18 %s: estado %r" % (s["id"], s.get("estado")))
    return f


# ---------- salidas ----------
def escribir_md(ruta, A):
    L = ["# Agenda %s (%s → %s)" % (A["semana"], A["desde"], A["hasta"]), "",
         "2 videos al día como máximo: una pieza fuerte (09:00) y una corta (19:30); el carrusel va aparte. Cada video va a TikTok, "
         "Instagram Reels, Facebook Reels y YouTube Shorts (9:16) y su 4:5 al feed. Copia el texto de `caption.md`; en Facebook, "
         "la descripción en el estilo que le toca (columna Facebook).",
         "", "| Día | Hora | Espacio | Formato | Pieza o tema | Estado | Producir | Créditos | Facebook | Avisos |", "|---|---|---|---|---|---|---|---|---|---|"]
    total = 0
    for s in A["espacios"]:
        if s["fecha"] < A["desde"]:
            continue
        total += s.get("creditos") or 0
        pieza = s["pieza"]["ruta"] if s.get("pieza") and s["pieza"].get("ruta") else (s.get("tema") or "**tema por elegir** · " + (s.get("comando") or ""))
        L.append("| %s %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            s["dia"], s["fecha"][5:], s["hora"], s["slot"], s["formato"], pieza, s["estado"],
            "—" if not s.get("producir_el") else "%s · ~%d min" % (s["producir_el"][5:], s.get("minutos") or 0),
            s.get("creditos") or "—", (s.get("facebook") or {}).get("estilo") or "—", "; ".join(s.get("avisos") or []) or ""))
    L += ["", "Créditos de voz estimados para lo que falta producir: ≈ %s." % "{:,}".format(total)]
    if A.get("pospuestas"):
        L += ["", "## Fechas del calendario que pasan a la semana siguiente", ""]
        L += ["- %s · %s (`%s`)" % (c["fecha"], c["titulo"], c["id"]) for c in A["pospuestas"]]
    if A.get("incompletas"):
        L += ["", "## Publicadas en algunas plataformas (completar si conviene)", ""]
        L += ["- `%s` · falta %s" % (x["ruta"] or x["id"], ", ".join(x["faltan"])) for x in A["incompletas"]]
    open(ruta, "w", encoding="utf-8").write("\n".join(L) + "\n")


def guardar(d, A):
    escribir(os.path.join(d, "agenda.json"), A)
    escribir_md(os.path.join(d, "agenda.md"), A)
    escribir_html(os.path.join(d, "agenda.html"), A)


NOMBRE_PLAT = {"tiktok": "TikTok", "instagram": "Instagram", "facebook": "Facebook", "youtube": "YouTube"}
ETIQUETA_SLOT = {"A": "Pieza fuerte", "B": "Noticias", "C": "Carrusel"}
ETIQUETA_ESTADO = {"propuesto": "sin tema", "tema": "por producir", "producido": "listo para publicar", "publicado": "publicado"}


def ordenes(A):
    """Las órdenes de trabajo en orden: [(día, hora orden, texto, comando, slot)] — producir (el día que toca, lo que va
    antes primero), y publicar en cada espacio con lo que se corre después."""
    out = []
    for s in A["espacios"]:
        if s["fecha"] < A["desde"]:
            continue
        if s["estado"] in ("propuesto", "tema") and s.get("producir_el"):
            com = s["comando"] if s.get("tema") else "elige el tema: /agenda (o agenda.py tema %s \"<tema>\")" % s["id"]
            # producir va antes que publicar ese día; primero lo que sale antes; «al terminar» justo después de su orden
            clave = (0, s["fecha"], s["hora"])
            out.append((s["producir_el"], clave + (0,), "Producir · %s · %s" % (s["formato"], s.get("tema") or "tema por elegir"), com, s))
            if s.get("tema"):
                out.append((s["producir_el"], clave + (1,), "Al terminar de producir", "python3 scripts/agenda.py producido %s --ruta <carpeta de entrega>" % s["id"], s))
        if s["estado"] != "publicado":
            out.append((s["fecha"], (1, s["fecha"], s["hora"], 0), "Publicar · %s · %s" % (s["formato"], s.get("tema") or (s.get("pieza") or {}).get("ruta") or ""),
                        "python3 scripts/agenda.py publicado %s" % s["id"], s))
    return sorted(out, key=lambda x: (x[0], x[1]))


def escribir_html(ruta, A):
    """agenda.html: la semana para abrir en el navegador (sin dependencias externas): las órdenes en orden, los días con sus
    espacios, los archivos por plataforma y los captions con botón de copiar."""
    e = html.escape
    hoy = datetime.date.today().isoformat()
    total = sum(s.get("creditos") or 0 for s in A["espacios"] if s["fecha"] >= A["desde"])

    def bloque_caption(ruta_pieza, fb=None):
        caps = caption_de(ruta_pieza)
        fb = fb or {}
        if fb.get("texto"):
            caps["facebook"] = fb["texto"]
        if not caps:
            return ""
        out = ['<div class="caps">']
        for p, t in caps.items():
            out.append('<div class="cap"><div class="caph"><b>%s</b><button onclick="copiar(this)">Copiar</button></div><pre>%s</pre></div>'
                       % (e(NOMBRE_PLAT.get(p, p)), e(t)))
        return "".join(out) + "</div>"

    def opciones_html(s):
        ops = s.get("opciones") or []
        if not ops:
            return ""
        out = ["<div class='ops'><b>Opciones</b>"]
        for k, o in enumerate(ops, 1):
            elegida = o["tema"] == s.get("tema")
            out.append("<div class='op%s'><span>%d. %s%s</span><small>%s</small>%s</div>" % (
                " sel" if elegida else "", k, e(o["tema"]), " · %s" % e(o["formato"]) if o.get("formato") and o["formato"] != s["formato"] else "",
                e(o.get("por_que") or ""),
                "" if elegida else "<code>python3 scripts/agenda.py tema %s --opcion %d</code><button onclick=\"copiar(this)\">Copiar</button>" % (e(s["id"]), k)))
        return "".join(out) + "</div>"

    def fbnota(s):
        fb = s.get("facebook") or {}
        if not fb.get("estilo"):
            return ""
        return "<p class='fb'>Facebook · estilo <b>%s</b>: %s%s</p>" % (e(fb["estilo"]), e(ESTILOS_FB[fb["estilo"]]),
                                                                    "" if fb.get("texto") else " <i>(por escribir)</i>")

    filas_ord = []
    dia_prev = None
    for dia, _, texto, com, s in ordenes(A):
        if dia != dia_prev:
            filas_ord.append('<h3 class="%s">%s %s%s</h3>' % ("hoy" if dia == hoy else "", DIAS[fecha(dia).weekday()].capitalize(), dia[8:] + "/" + dia[5:7],
                                                          " · hoy" if dia == hoy else ""))
            dia_prev = dia
        filas_ord.append('<div class="ord"><span class="t">%s</span><span class="x">%s</span><code>%s</code><button onclick="copiar(this)">Copiar</button></div>'
                         % (e(s["hora"] if texto.startswith("Publicar") else "antes"), e(texto), e(com)))
    dias_html = []
    por_dia = {}
    for s in A["espacios"]:
        if s["fecha"] >= A["desde"]:
            por_dia.setdefault(s["fecha"], []).append(s)
    for dia in sorted(por_dia):
        tarjetas = []
        for s in sorted(por_dia[dia], key=lambda x: x["hora"]):
            ruta_p = (s.get("pieza") or {}).get("ruta")
            arch = ""
            if ruta_p:
                if s["formato"] == "carrusel":
                    arch = "<p class='f'>Láminas: <code>%s/*.png</code> (4:5) · <code>%s/9x16/*.png</code> (TikTok, modo foto)</p>" % (e(ruta_p), e(ruta_p))
                else:
                    arch = ("<p class='f'>9:16 → TikTok, Reels, Facebook Reels, Shorts: <code>%s/video.mp4</code><br>4:5 → feed de Instagram y "
                            "Facebook: <code>%s/video_4x5.mp4</code><br>YouTube Studio → Audiencia: «No, no está hecho para niños»</p>" % (e(ruta_p), e(ruta_p)))
            avisos = "".join("<p class='av'>⚠ %s</p>" % e(a) for a in s.get("avisos") or [])
            prod = "" if not s.get("producir_el") or s["estado"] not in ("propuesto", "tema") else                 "<p class='pr'>Producir el %s · ~%d min · ≈ %s créditos<br><code>%s</code></p>" % (
                    e(s["producir_el"][8:] + "/" + s["producir_el"][5:7]), s.get("minutos") or 0, "{:,}".format(s.get("creditos") or 0), e(s.get("comando") or ""))
            tarjetas.append('<article class="slot %s %s"><header><span class="h">%s</span><span class="k">%s · %s</span><span class="st">%s</span></header>'
                            '<h4>%s</h4><p class="pl">%s</p>%s%s%s%s</article>' % (
                                s["slot"], s["estado"], e(s["hora"]), e(ETIQUETA_SLOT.get(s["slot"], s["slot"])), e(s["formato"]),
                                e("por producir" if s["estado"] == "propuesto" and s.get("tema") else ETIQUETA_ESTADO.get(s["estado"], s["estado"])), e(s.get("tema") or ruta_p or "Tema por elegir"),
                                " · ".join(NOMBRE_PLAT.get(p, p) for p in s.get("plataformas") or []), prod, arch, bloque_caption(ruta_p, s.get("facebook")) if ruta_p else "", opciones_html(s) + fbnota(s) + avisos))
        dias_html.append('<section class="dia %s"><h2>%s <small>%s</small></h2>%s</section>' % (
            "hoy" if dia == hoy else "", DIAS[fecha(dia).weekday()].capitalize(), dia[8:] + "/" + dia[5:7], "".join(tarjetas)))
    extra = []
    if A.get("omitidas"):
        extra.append("<h3>Omitidas</h3><ul>%s</ul>" % "".join("<li><code>%s</code> %s</li>" % (e(o["id"]), e(o.get("motivo") or "")) for o in A["omitidas"]))
    if A.get("pospuestas"):
        extra.append("<h3>Pasan a la semana siguiente</h3><ul>%s</ul>" % "".join("<li>%s · %s</li>" % (e(c["fecha"]), e(c["titulo"])) for c in A["pospuestas"]))
    if A.get("incompletas"):
        extra.append("<h3>Publicadas en algunas plataformas</h3><ul>%s</ul>" % "".join(
            "<li><code>%s</code> · falta %s</li>" % (e(x.get("ruta") or x["id"]), e(", ".join(NOMBRE_PLAT.get(p, p) for p in x["faltan"]))) for x in A["incompletas"]))
    doc = """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agenda %(semana)s</title><style>
:root{--bg:#f6f3ee;--card:#fff;--ink:#1d1b18;--mut:#6b655c;--line:#e4ddd2;--a:#b4532a;--ok:#2f7d4f;--warn:#a46a00;--code:#f1ece4}
@media (prefers-color-scheme: dark){:root{--bg:#141210;--card:#1d1a17;--ink:#f1ebe2;--mut:#a59d92;--line:#2e2924;--a:#e8875a;--ok:#6fc28f;--warn:#e0b04a;--code:#26221e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 60px}h1{margin:0 0 4px;font-size:26px}.sub{color:var(--mut);margin:0 0 20px}
.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.6fr);gap:24px}@media (max-width:860px){.grid{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}h2{font-size:18px;margin:0 0 10px}h2 small{color:var(--mut);font-weight:400}
h3{font-size:14px;margin:16px 0 6px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}h3.hoy{color:var(--a)}
.ord{display:grid;grid-template-columns:52px 1fr auto;gap:4px 8px;align-items:center;padding:8px 0;border-top:1px solid var(--line)}
.ord .t{color:var(--mut);font-variant-numeric:tabular-nums}.ord code{grid-column:2/3;font-size:12.5px}.ord button{grid-row:1/3;grid-column:3}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);border-radius:6px;padding:2px 6px;word-break:break-word;white-space:pre-wrap}
pre{padding:8px;margin:6px 0 0;font-size:12.5px}button{font:inherit;font-size:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:6px;padding:4px 8px;cursor:pointer}
button.ok{color:var(--ok);border-color:var(--ok)}.dia{margin-bottom:22px}.dia.hoy h2{color:var(--a)}
.slot{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:10px;padding:12px 14px;margin:8px 0}
.slot.A{border-left-color:var(--a)}.slot.B{border-left-color:var(--mut)}.slot.C{border-left-color:var(--warn)}
.slot header{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.slot .h{font-weight:700;font-variant-numeric:tabular-nums}.slot .k{color:var(--mut)}
.slot .st{margin-left:auto;font-size:12px;padding:2px 8px;border-radius:99px;border:1px solid var(--line)}
.slot.producido .st{color:var(--ok);border-color:var(--ok)}.slot.publicado{opacity:.6}.slot.propuesto .st{color:var(--warn);border-color:var(--warn)}
.slot h4{margin:6px 0 2px;font-size:16px}.pl,.f{color:var(--mut);margin:4px 0;font-size:13px}.pr{margin:6px 0;font-size:13px}.av{color:var(--warn);margin:6px 0 0;font-size:13px}
.ops{margin:8px 0;font-size:13px;display:grid;gap:4px}.op{display:grid;grid-template-columns:1fr auto;gap:2px 8px;padding:6px 8px;border:1px solid var(--line);border-radius:6px}
.op span{font-weight:600}.op small{grid-column:1/2;color:var(--mut)}.op code{grid-column:1/2;font-size:12px}.op button{grid-row:1/4;grid-column:2}.op.sel{border-color:var(--ok)}.op.sel span::after{content:" · elegida";color:var(--ok);font-weight:400}
.fb{font-size:13px;margin:6px 0 0;padding:6px 8px;border-radius:6px;background:var(--code)}.caps{display:grid;gap:6px;margin-top:8px}.caph{display:flex;justify-content:space-between;align-items:center}
.tot{color:var(--mut);margin-top:12px;font-size:13px}ul{padding-left:18px}
</style></head><body><main>
<h1>Agenda %(semana)s</h1><p class="sub">%(desde)s → %(hasta)s · como máximo 2 videos al día (una pieza fuerte a las 09:00 y una corta a las 19:30), el carrusel aparte; en Facebook, el estilo de descripción que toca · cada video a TikTok, Instagram, Facebook y YouTube · generado %(gen)s</p>
<div class="grid"><div class="panel"><h2>Órdenes de trabajo, en orden</h2>%(ordenes)s<p class="tot">Créditos de voz estimados para lo que falta producir: ≈ %(total)s</p>%(extra)s</div>
<div>%(dias)s</div></div></main>
<script>function copiar(b){var c=b.closest('.ord,.cap');var t=(c.querySelector('code,pre')||{}).innerText||'';
navigator.clipboard.writeText(t).then(function(){b.textContent='Copiado';b.classList.add('ok');setTimeout(function(){b.textContent='Copiar';b.classList.remove('ok')},1500)})}</script>
</body></html>""" % {"semana": e(A["semana"]), "desde": e(A["desde"]), "hasta": e(A["hasta"]), "gen": e(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
                     "ordenes": "".join(filas_ord) or "<p>Nada pendiente.</p>", "total": "{:,}".format(total), "extra": "".join(extra), "dias": "".join(dias_html)}
    open(ruta, "w", encoding="utf-8").write(doc)


def cmd_plan(a):
    desde = fecha(a.desde) if a.desde else datetime.date.today()
    d = dir_semana(desde, a.dir)
    memdir = os.path.abspath(a.memoria or os.path.join(RAIZ, "memoria"))
    previo = leer(os.path.join(d, "agenda.json"))
    A = armar(desde, memdir, previo, None if a.desde else datetime.datetime.now())
    if a.memoria:
        A["memoria"] = rel(memdir)
    f = revisar(A, memdir)
    guardar(d, A)
    for s in A["espacios"]:
        if s["fecha"] >= A["desde"]:
            print("%s %-9s %s %s · %-12s · %-10s · %s%s" % (s["fecha"], s["dia"], s["hora"], s["slot"], s["formato"], s["estado"],
                  (s["pieza"] or {}).get("ruta") or s.get("tema") or "tema por elegir: " + (s.get("comando") or ""),
                  "  ⚠ " + "; ".join(s["avisos"]) if s.get("avisos") else ""))
    for x in f:
        print("FALLA", x)
    print("[agenda] %s · %d espacios · %d sin tema · %s" % (A["semana"], sum(1 for s in A["espacios"] if s["fecha"] >= A["desde"]),
          sum(1 for s in A["espacios"] if s["fecha"] >= A["desde"] and not s.get("tema")), rel(os.path.join(d, "agenda.md"))))
    return 1 if f else 0


def cargar(a, desde=None):
    d = dir_semana(desde or datetime.date.today(), a.dir)
    A = leer(os.path.join(d, "agenda.json"))
    if not A:
        raise SystemExit(print("ERROR: no hay agenda en %s (corre agenda.py plan)" % rel(d), file=sys.stderr) or 1)
    return d, A


def espacio_de(A, sid):
    s = next((x for x in A["espacios"] if x["id"] == sid), None)
    if not s:
        raise SystemExit(print("ERROR: no hay espacio %s (%s)" % (sid, ", ".join(x["id"] for x in A["espacios"])), file=sys.stderr) or 2)
    return s


def fijar_tema(s, tema, formato=None):
    if formato:
        s["formato"] = formato
        com, antes, minutos, cred = FORMATOS[formato]
        s.update(minutos=minutos, creditos=cred, producir_el=(fecha(s["fecha"]) - datetime.timedelta(days=antes)).isoformat())
    s["tema"] = tema.strip()
    s["comando"] = FORMATOS[s["formato"]][0].replace("<tema>", s["tema"]).replace("<creencia>", s["tema"]).replace("<pista>", s["tema"])
    s["estado"] = "tema"


def formatos_de_slot(slot):
    return FUERTES if slot == "A" else CORTAS


def cmd_tema(a):
    d, A = cargar(a, fecha(a.slot[:10]))
    s = espacio_de(A, a.slot)
    if a.formato and a.formato not in formatos_de_slot(s["slot"]):
        print("--formato del espacio %s: %s" % (s["slot"], "|".join(formatos_de_slot(s["slot"]))), file=sys.stderr)
        return 2
    if a.opcion:
        ops = s.get("opciones") or []
        if not 1 <= a.opcion <= len(ops):
            print("--opcion: 1–%d (las opciones de %s)" % (len(ops), s["id"]), file=sys.stderr)
            return 2
        o = ops[a.opcion - 1]
        fijar_tema(s, o["tema"], a.formato or o.get("formato"))
    elif a.tema:
        fijar_tema(s, a.tema, a.formato)
    else:
        print("el tema: \"<tema>\" o --opcion N", file=sys.stderr)
        return 2
    s["tema_auto"] = False
    memdir = os.path.join(RAIZ, A.get("memoria") or "memoria")
    f = [x for x in revisar(A, memdir) if x.startswith("AG4 %s" % s["id"])]
    for x in f:
        print("FALLA", x)
    if f:
        return 1
    guardar(d, A)
    print("%s · %s · «%s» · producir el %s → %s" % (s["id"], s["formato"], s["tema"], s.get("producir_el"), s["comando"]))
    return 0


def cmd_opciones(a):
    """Las 2–3 opciones de tema de un espacio (las investiga la sesión: actualidad, fechas y datos importantes), cada una con su
    porqué; la primera queda como tema (recomendada) salvo que el usuario ya haya elegido uno. Así toda la semana queda lista
    para producir; `tema SLOT --opcion N` cambia a otra."""
    d, A = cargar(a, fecha(a.slot[:10]))
    s = espacio_de(A, a.slot)
    ops = []
    for k, t in enumerate(a.opcion or []):
        tema, _, por_que = t.partition("|")
        fmt = None
        if "::" in tema:
            fmt, tema = tema.split("::", 1)
            fmt = fmt.strip()
            if fmt not in formatos_de_slot(s["slot"]):
                print("opción %d: formato «%s» no va en el espacio %s (%s)" % (k + 1, fmt, s["slot"], "|".join(formatos_de_slot(s["slot"]))), file=sys.stderr)
                return 2
        ops.append({"tema": tema.strip(), "por_que": por_que.strip(), "formato": fmt or s["formato"]})
    if not MIN_OPCIONES <= len(ops) <= MAX_OPCIONES or any(not o["tema"] or not o["por_que"] for o in ops):
        print("--opcion «<tema>|<por qué ahora>» de %d a %d veces (formato opcional: «mito::<creencia>|…»)" % (MIN_OPCIONES, MAX_OPCIONES), file=sys.stderr)
        return 2
    memdir = os.path.join(RAIZ, A.get("memoria") or "memoria")
    otros = [x for x in A["espacios"] if x is not s and x.get("tema") and x["formato"] not in SIN_AGENDA]
    f = []
    producidos = [x for x in inventario(memdir) if x.get("fecha") and (fecha(A["desde"]) - fecha(x["fecha"])).days <= DIAS_REPETIDO]
    for k, o in enumerate(ops, 1):
        ks = claves(o["tema"])
        x = next((x for x in producidos if parecido(ks, set(x["claves"])) >= 0.6), None)
        if x:
            f.append("AG4 opción %d «%s» repite «%s» (producido el %s)" % (k, o["tema"][:50], x["slug"], x["fecha"]))
        y = next((y for y in otros if parecido(ks, claves(y["tema"])) >= 0.6), None)
        if y:
            f.append("AG4 opción %d «%s» repite el tema de %s" % (k, o["tema"][:50], y["id"]))
    for x in f:
        print("FALLA", x)
    if f:
        return 1
    s["opciones"] = ops
    if s["estado"] == "propuesto" or s.get("tema_auto") or not s.get("tema"):
        fijar_tema(s, ops[0]["tema"], ops[0]["formato"] if ops[0]["formato"] != s["formato"] else None)
        s["tema_auto"] = True
    guardar(d, A)
    print("%s · %d opciones · tema: «%s»%s" % (s["id"], len(ops), s["tema"], " (recomendada)" if s.get("tema_auto") else " (la elegida por el usuario)"))
    return 0


def cmd_producido(a):
    d, A = cargar(a, fecha(a.slot[:10]))
    s = espacio_de(A, a.slot)
    ruta = os.path.abspath(a.ruta)
    if not os.path.isfile(os.path.join(ruta, "guion.json")) and not os.path.isfile(os.path.join(ruta, "carrusel.json")):
        return print("ERROR: %s no es una entrega (sin guion.json ni carrusel.json)" % rel(ruta), file=sys.stderr) or 1
    g = leer(os.path.join(ruta, "guion.json")) or leer(os.path.join(ruta, "carrusel.json")) or {}
    s.update(pieza={"flujo": FLUJO_DE_FORMATO.get(s["formato"], s["formato"]), "id": g.get("id") or os.path.basename(ruta), "ruta": rel(ruta)},
             estado="producido")
    guardar(d, A)
    print("%s producido → %s" % (s["id"], rel(ruta)))
    return 0


def cmd_publicado(a):
    d, A = cargar(a, fecha(a.slot[:10]))
    s = espacio_de(A, a.slot)
    plats = s["plataformas"] if a.plataforma in (None, "todas") else [a.plataforma]
    ahora = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
    for p in plats:
        s.setdefault("publicado", {})[p] = ahora
    if set(s["publicado"]) >= set(s["plataformas"]):
        s["estado"] = "publicado"
    guardar(d, A)
    print("%s publicado en %s (%s)" % (s["id"], ", ".join(plats), ahora))
    return 0


def caption_de(ruta):
    """Los bloques de caption.md por plataforma (el texto entre ``` de cada sección)."""
    p = os.path.join(RAIZ, ruta or "", "caption.md")
    if not ruta or not os.path.exists(p):
        return {}
    out, sec = {}, None
    texto = open(p, encoding="utf-8").read()
    for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", texto, re.S | re.M):
        nombre, cuerpo = plano(m.group(1)), m.group(2)
        k = next((x for x in ("tiktok", "instagram", "facebook", "youtube") if x in nombre), None)
        if k:
            b = re.search(r"```\n(.*?)\n```", cuerpo, re.S)
            lineas = [l for l in (b.group(1) if b else cuerpo).strip().splitlines()
                      if l.strip() and not re.match(r"^(Título \(|\*\*Este video)", l.strip())]   # caption.md viejo, sin bloques
            out[k] = "\n".join(lineas)
    return out


def cmd_facebook(a):
    """La descripción de Facebook de un espacio, escrita en el estilo que le tocó (la escribe la sesión con caption.md y el
    guion de la pieza); hoy y agenda.html la muestran en lugar del bloque de Facebook de caption.md."""
    d, A = cargar(a, fecha(a.slot[:10]))
    s = espacio_de(A, a.slot)
    fb = s.setdefault("facebook", {"estilo": ESTILOS_FB_ORDEN[0], "texto": None})
    if a.estilo:
        fb["estilo"] = a.estilo
    texto = (a.texto or "").strip()
    try:
        import video as VD
        m = VD.CEBO.search(texto)
    except Exception:  # noqa: BLE001
        m = None
    if m:
        print("FALLA F4 «%s» es cebo de interacción (Meta lo penaliza): quítalo" % m.group())
        return 1
    if not texto:
        print("--texto: la descripción en estilo %s: %s" % (fb["estilo"], ESTILOS_FB[fb["estilo"]]), file=sys.stderr)
        return 2
    fb["texto"] = texto
    guardar(d, A)
    print("%s · Facebook en estilo «%s» (%d caracteres)" % (s["id"], fb["estilo"], len(texto)))
    return 0


def cmd_omitir(a):
    """Una pieza lista que el usuario no quiere publicar: sale de la agenda y su espacio vuelve a la mezcla (plan)."""
    d, A = cargar(a)
    if any(o["id"] == a.pieza for o in A.get("omitidas") or []):
        print("%s ya estaba omitida" % a.pieza)
        return 0
    A.setdefault("omitidas", []).append({"id": a.pieza, "motivo": a.motivo or "", "fecha": datetime.date.today().isoformat()})
    guardar(d, A)
    print("%s omitida: corre agenda.py plan para rehacer los espacios" % a.pieza)
    return 0


def cmd_hoy(a):
    dia = fecha(a.fecha) if a.fecha else datetime.date.today()
    d, A = cargar(a, dia)
    hoy = dia.isoformat()
    print("# Hoy, %s %s" % (DIAS[dia.weekday()], hoy))
    prod = [s for s in A["espacios"] if s.get("producir_el") and s["producir_el"] <= hoy <= s["fecha"] and s["estado"] in ("propuesto", "tema")]
    print("\n## Producir")
    for s in prod or []:
        print("- %s (%s %s) · %s · %s" % (s["comando"] if s.get("tema") else "elige el tema primero: /agenda (tema) · " + (s.get("comando") or ""),
                                         s["dia"], s["hora"], s["formato"], s.get("tema") or "—"))
    if not prod:
        print("- nada pendiente")
    print("\n## Publicar")
    for s in [x for x in A["espacios"] if x["fecha"] == hoy]:
        print("- %s · %s · %s · %s · %s" % (s["hora"], s["slot"], s["formato"], s["estado"], (s.get("pieza") or {}).get("ruta") or s.get("tema") or "—"))
        ruta = (s.get("pieza") or {}).get("ruta")
        if ruta:
            if s["formato"] == "carrusel":
                print("    archivos: %s/*.png (4:5) y %s/9x16/*.png" % (ruta, ruta))
            else:
                print("    9:16 → TikTok, Instagram Reels, Facebook Reels, YouTube Shorts: %s/video.mp4 · 4:5 → feed: %s/video_4x5.mp4" % (ruta, ruta))
                print("    YouTube Studio → Audiencia: «No, no está hecho para niños»")
            fb = s.get("facebook") or {}
            for p, t in caption_de(ruta).items():
                if p == "facebook" and fb.get("texto"):
                    t = fb["texto"]
                print("    caption %s: %s" % (p, t.splitlines()[0][:110]))
            if fb.get("estilo"):
                print("    Facebook · estilo «%s»%s: %s" % (fb["estilo"], "" if fb.get("texto") else " (sin escribir: agenda.py facebook %s --texto …)" % s["id"],
                                                         ESTILOS_FB[fb["estilo"]]))
            print("    después: python3 scripts/agenda.py publicado %s" % s["id"])
    return 0


def cmd_check(a):
    d, A = cargar(a, fecha(a.desde) if a.desde else None)
    memdir = os.path.join(RAIZ, A.get("memoria") or "memoria")
    f = revisar(A, memdir, listo=a.listo)
    for x in f:
        print("FALLA", x)
    print("[agenda] %s · %s" % (A["semana"], "ok" if not f else "%d fallas" % len(f)))
    return 1 if f else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="AG1–AG9 sobre agenda.json")
    ap.add_argument("--dir", help="otra carpeta de agenda (pruebas)")
    ap.add_argument("--desde", help="con --check: un día de la semana a revisar")
    ap.add_argument("--listo", action="store_true", help="con --check: además AG10 (todo espacio con tema y ≥ 2 opciones)")
    sub = ap.add_subparsers(dest="cmd")
    q = sub.add_parser("plan")
    q.add_argument("--desde")
    q.add_argument("--memoria", help="otra carpeta de registros (la maqueta)")
    q.add_argument("--dir")
    q = sub.add_parser("tema")
    q.add_argument("slot")
    q.add_argument("tema", nargs="?")
    q.add_argument("--opcion", type=int, help="elige la opción N de las que escribió la sesión")
    q.add_argument("--formato")
    q.add_argument("--dir")
    q = sub.add_parser("opciones", help="2–3 opciones de tema para un espacio; la primera queda como tema")
    q.add_argument("slot")
    q.add_argument("--opcion", action="append", help="«<tema>|<por qué ahora>» (formato opcional: «mito::<creencia>|…»)")
    q.add_argument("--dir")
    q = sub.add_parser("producido")
    q.add_argument("slot")
    q.add_argument("--ruta", required=True)
    q.add_argument("--dir")
    q = sub.add_parser("publicado")
    q.add_argument("slot")
    q.add_argument("--plataforma", choices=PLATAFORMAS_VIDEO + ("todas",))
    q.add_argument("--dir")
    q = sub.add_parser("facebook", help="la descripción de Facebook del espacio, en su estilo")
    q.add_argument("slot")
    q.add_argument("--texto", required=True)
    q.add_argument("--estilo", choices=tuple(ESTILOS_FB))
    q.add_argument("--dir")
    q = sub.add_parser("omitir", help="una pieza lista que no se publica (sale de la agenda)")
    q.add_argument("pieza", help="el id de la pieza (el de memoria/, p. ej. 2026-11-01-la-erupcion-del-volcan-de-fuego-de-2018)")
    q.add_argument("--motivo")
    q.add_argument("--dir")
    q = sub.add_parser("hoy")
    q.add_argument("--fecha")
    q.add_argument("--dir")
    a = ap.parse_args()
    if a.check:
        return cmd_check(a)
    fn = {"plan": cmd_plan, "tema": cmd_tema, "producido": cmd_producido, "publicado": cmd_publicado, "hoy": cmd_hoy, "omitir": cmd_omitir,
          "facebook": cmd_facebook, "opciones": cmd_opciones}.get(a.cmd)
    if not fn:
        ap.print_help()
        return 2
    return fn(a)


if __name__ == "__main__":
    sys.exit(main())
