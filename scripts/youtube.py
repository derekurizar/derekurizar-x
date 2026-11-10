#!/usr/bin/env python3
"""/youtube-long: una serie ya entregada convertida en UN video largo 16:9 para YouTube. Solo stdlib.

El video largo no es un guion nuevo: es un MONTAJE (montaje.json), una lista ordenada de referencias a las escenas ya
verificadas y grabadas de cada parte (Pk.eN), con cortes y unas pocas piezas de voz nueva. Cortar no gasta créditos;
solo las uniones (puentes), la promesa global y, como último recurso, alguna escena reescrita (revozar).

Por qué hace falta: cada parte de /serie se hizo para entenderse SOLA, así que pegadas se repiten (ganchos y cierres de
cada parte, el mismo hecho contado dos o tres veces, la misma persona presentada en cada parte, saltos atrás en el
tiempo). referencias/flujo-youtube.md lo cuenta con el caso La Línea.

TRABAJO = sesiones/youtube-<slug>/:
  youtube.json            estado: serie, partes (TRABAJO y entrega de cada una), paleta, música, rangos
  indice.json             cada escena de cada parte: id Pk.eN, tipo, duración, hechos, frases (Pk.eN.fM) con tiempos
  repeticiones.json       lo que se repite al pegar las partes (hechos, frases, presentaciones, glosas, saltos)
  montaje.borrador.json   el montaje con las marcas del formato corto ya quitadas (lo completa el editor)
  montaje.json            el montaje del editor (YT1–YT8)
  nuevas/                 un TRABAJO de /historia con SOLO las piezas de voz nueva (puentes, promesa, revozadas)
  escenas.json, audio/, fotos/, base/, tomas/, clips_16x9/ …   el TRABAJO unido que se graba y se monta

Montaje (montaje.json):
  {version, titulo,
   promesa: {texto, forma, foto, pago: "Pk.eN", hechos: [ids]},
   capitulos: [{parte, titulo,
                puente: null | {texto, foto, hechos: [ids]},
                escenas: [{ref: "Pk.eN", op: usar|quitar|revozar, quitar: ["texto literal"…], sin_hechos: [ids],
                           reprise: bool, ancla: "…", texto: "… (revozar)", razon: "…"}]}]}

Subcomandos:
  preparar SERIE [--trabajo DIR] [--fixture]    indice, repeticiones y borrador; imprime el TRABAJO (última línea)
  digesto TRABAJO --para editor|oyente|critico  el insumo de cada agente (el oyente: solo lo que se oye y se lee)
  montaje TRABAJO --check                       YT1–YT8 sobre montaje.json; RETORNO json en la última línea
  probar TRABAJO --cambios ARCHIVO              aplica los cambios a una copia del montaje y corre el gate (no escribe)
  aplicar TRABAJO --cambios ARCHIVO             los aplica a montaje.json si el gate pasa (si no, lo deja como estaba)
  resumen TRABAJO                               el montaje para que el usuario lo apruebe (duración, cortes, uniones)
  voz TRABAJO [--falsa]                         arma nuevas/ (guion y locucion de las piezas nuevas) e imprime los nodos
  tiempos TRABAJO                               los tiempos de las piezas nuevas (nuevas/escenas.json; V16)
  armar TRABAJO                                 el TRABAJO unido: escenas.json, audio recortado, recursos, música
  grabar TRABAJO [--fps 30] [--paralelo N]      las escenas en 16:9 (video_grabar.js --formato 16:9)
  montar TRABAJO                                video 1920×1080 por tramos + voz, música por capítulo y efectos (−14 LUFS)
  miniatura TRABAJO --texto "…" [--foto ID] [--cifra "…"]   miniatura 1280×720 (YT10)
  entregar TRABAJO [--salida DIR]               series/<fecha>-<slug>/youtube/ (video, miniatura, caption con capítulos…)
  --revisar SERIE                               lo que preparar comprueba, sin escribir

Gates:
  YT1 referencias: cada escena de cada parte aparece una vez, en orden, en el capítulo de su parte; un capítulo por parte
  YT2 formato corto: ni «Sígueme», ni «parte» con ordinal, ni «capítulo», ni anuncios en la voz que queda
  YT3 uniones: 1–2 oraciones de ≤ 160 caracteres, sin anunciar, con hechos `confirmado|una_fuente` y números con respaldo
  YT4 repetición: cada hecho una vez (reprise ≤ 3, con razón); sin frases de ≥ 8 palabras repetidas; una presentación
      completa por persona y una glosa por sigla (un recordatorio corto vale tras ≥ 5 min)
  YT5 referencias colgadas: lo que sigue a un corte no abre con «Eso», «Ese», «Su»… sin `ancla` (aviso)
  YT6 cortes de audio: en un silencio de ≥ 80 ms, sin partir un nombre; ≤ 3 revozar
  YT7 duración: 8–20 min; cada capítulo ≥ 60 s
  YT8 adelanto opcional (un momento alto ya grabado, 3–9 s, antes del gancho) y promesa global: forma del catálogo, sin anuncio, antes del segundo 15, con su `pregunta` para la pantalla, y se
      paga en el último 40 %
  YT9–YT11 render, miniatura y entrega (grabar, montar, miniatura, entregar)
  YT12 ocupación del 16:9 (en grabar): ninguna escena de más de 4 s con más de 70 % de fondo liso

Exit: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse
import copy
import datetime
import glob
import json
import os
import re
import shutil
import tempfile
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402
import numeros_es as NE  # noqa: E402

# ---------- constantes (espejo en .claude/workflows/youtube.js: W14) ----------
PUENTE_ORACIONES, PUENTE_CARACTERES = 2, 160      # YT3
PROMESA_CARACTERES = 160
REPRISE_MAX = 3                                   # YT4
RECORDATORIO_S = 300                              # YT4: tras 5 min, un recordatorio corto de quién es vale
FRASE_REPETIDA_PALABRAS = 8                       # YT4 (como SE13)
FUNDIDO_CORTE_S = 0.004                           # el fundido a cada lado de un corte de voz
SILENCIO_CORTE_S = 0.08                           # YT6
REVOZAR_MAX = 3                                   # YT6
DURACION_S = (480, 1200)                          # YT7: 8–20 min
CAPITULO_MIN_S = 60                               # YT7 (YouTube pide ≥ 10 s)
PROMESA_ANTES_S = 15                              # YT8: la promesa global se oye antes de este segundo
PAGO_DESDE = 0.60                                 # YT8: la promesa se paga en el último 40 %
CAPITULO_S = 2.8                                  # el rótulo de capítulo: sin voz
FINAL_EXTRA_S = 12.0                              # la pantalla final: aire para los elementos finales de YouTube
TRAMO_ESCENAS = 14                                # montar: escenas por tramo de video (sin filtergraph de 120 entradas)
OPS = ("usar", "quitar", "revozar")
PUNTAJES = ("repeticion", "continuidad", "uniones", "ritmo", "promesa", "claridad", "escalada")   # crítico en Modo largo (Y-C1–Y-C7)
RE_ANUNCIO = re.compile(
    r"\bs[ií]gue(?:me|nos)\b|\bsuscr[ií]bete\b|\ben\s+(?:la|esta)\s+(?:primera|segunda|tercera|cuarta|quinta|sexta|s[eé]ptima|octava|"
    r"siguiente|pr[oó]xima|[uú]ltima)\s+parte\b|\bparte\s+(?:uno|dos|tres|cuatro|cinco|seis|siete|ocho|\d)\b|\bcap[ií]tulo\b|"
    r"\ba\s+continuaci[oó]n\b|\bahora\s+(?:vamos|veremos|te\s+cuento|toca)\b|\blo\s+que\s+viene\b|\bte\s+(?:cuento|voy\s+a\s+contar)\b|"
    r"\bvas\s+a\s+ver\b|\bm[aá]s\s+adelante\b|\ben\s+este\s+video\b|\bal\s+final\s+del\s+video\b|\bqu[eé]date\b", re.I)
RE_ANAFORA = re.compile(r"^(?:eso|esa|ese|esos|esas|esto|esta|este|estos|estas|as[ií]|su|sus|ah[ií]|all[ií]|ello|aquel|aquella|"
                        r"tambi[eé]n|tampoco|otro|otra)\b", re.I)
RE_GLOSA = re.compile(r"\b(?:la|el|del|al)\s+(%s)\s*,\s*(?:la|el|una|un|comisi[oó]n|oficina)\s+[^,.:;?]{4,70}[,.:;]" % "|".join(
    sorted({re.escape(v[1]) for v in NE.SIGLAS.values() if v[0] == "palabra"} | {"eme pe", "MP", "Onu", "Cicig", "Sat", "Feci", "Cacif"},
           key=len, reverse=True)), re.I)
FORMATO_GRABAR = "16:9"


def leer(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(p, obj):
    os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def rel(p):
    return os.path.relpath(os.path.abspath(p), RAIZ)


def falla(m):
    print("ERROR:", m, file=sys.stderr)
    return 1


def plano(s):
    return VD._plano(s or "")


# ---------- las partes ----------
def ruta_serie(arg):
    """serie.json desde la carpeta, el slug o «ultima» (la serie completa más reciente de memoria/series.json)."""
    import serie as SE  # noqa: E402
    if arg == "ultima":
        try:
            ss = [x for x in leer(os.path.join(RAIZ, "memoria", "series.json")).get("series") or []
                  if all(p.get("estado") == "entregada" for p in x.get("partes") or [{}])]
        except (OSError, ValueError):
            ss = []
        ss.sort(key=lambda x: (x.get("fecha") or "", x.get("id") or ""))
        return os.path.join(RAIZ, ss[-1]["carpeta"], "serie.json") if ss else None
    return SE.ruta_serie(arg)


def dirs_parte(base):
    """Las carpetas parte-N de un TRABAJO de serie (filtra las de nombre raro: «parte-4 » con espacio)."""
    out = {}
    for d in glob.glob(os.path.join(base, "parte-*")):
        m = re.fullmatch(r"parte-(\d+)", os.path.basename(d))
        if m and os.path.isdir(d):
            out[int(m.group(1))] = d
    return out


def cargar_parte(k, trabajo):
    """Lo de una parte que el montaje usa: guion (texto, hechos por escena), escenas.json (tiempos reales) y locucion."""
    g = leer(os.path.join(trabajo, "guion.json"))
    E = leer(os.path.join(trabajo, "escenas.json"))
    loc = leer(os.path.join(trabajo, "locucion.json"))
    return {"n": k, "trabajo": trabajo, "guion": g, "E": E, "loc": loc}


def tokens_voz(S):
    """Las palabras dichas de una escena (sin las de una toma con su audio original)."""
    return [w for w in S.get("palabras") or [] if not w.get("toma")]


def frases_de(toks):
    """Oraciones de una escena: [(i0, i1)] índices de tokens; corta tras «.», «?», «!» o «…»."""
    out, i0 = [], 0
    for i, w in enumerate(toks):
        if w["text"].rstrip("»”\")").endswith((".", "?", "!", "…")):
            out.append((i0, i))
            i0 = i + 1
    if i0 < len(toks):
        out.append((i0, len(toks) - 1))
    return out


def texto_toks(toks):
    return " ".join(w["text"] for w in toks)


def escena_guion(P, n):
    es = P["guion"].get("escenas") or []
    if n <= len(es):
        return es[n - 1]
    return dict(P["guion"].get("cierre") or {}, tipo="cierre")


def construir_indice(partes):
    """[{id, parte, n, tipo, dur, fin_voz, acto, hechos, cita, resumen, texto, frases[{id, texto, t0, t1}], marca}]"""
    idx = []
    M = len(partes)
    for P in partes:
        for S in P["E"]["escenas"]:
            n, tipo = S["n"], S.get("tipo")
            eg = escena_guion(P, n)
            toks = tokens_voz(S)
            frs = [{"id": "P%d.e%d.f%d" % (P["n"], n, j), "texto": texto_toks(toks[a:b + 1]),
                    "t0": toks[a]["start"], "t1": toks[b]["end"]} for j, (a, b) in enumerate(frases_de(toks), 1)]
            marca = None
            if tipo == "gancho" and P["n"] > 1:
                marca = "gancho de la parte %d: el video largo abre una sola vez" % P["n"]
            elif tipo == "cierre" and P["n"] < M:
                marca = "cierre de la parte %d (pregunta-puente e invitación): el capítulo siguiente sigue de corrido" % P["n"]
            elif eg.get("resumen_serie"):
                marca = "resumen de la serie (SE14): repasa lo que el espectador acaba de ver"
            idx.append({"id": "P%d.e%d" % (P["n"], n), "parte": P["n"], "n": n, "tipo": tipo, "dur": S["dur"],
                        "fin_voz": S.get("fin_voz"), "acto": S.get("acto"), "hechos": eg.get("hechos") or [],
                        "cita": eg.get("cita"), "foto": eg.get("foto"), "resumen": bool(eg.get("resumen_serie")),
                        "texto": texto_toks(toks), "frases": frs, "marca": marca, "toma": bool(S.get("toma"))})
    return idx


# ---------- repeticiones ----------
def frases_largas(texto):
    out = set()
    for fr in re.split(r"(?<=[.:?!;])\s+", texto or ""):
        w = re.sub(r"[^\wáéíóúüñ ]", "", fr.lower()).split()
        if len(w) >= FRASE_REPETIDA_PALABRAS:
            out.add(" ".join(w))
    return out


def personajes_de(base):
    try:
        enc = leer(os.path.join(base, "encuadre.json"))
    except (OSError, ValueError):
        return []
    return [p for p in enc.get("personajes") or [] if isinstance(p, dict) and (p.get("nombre") or "").strip()]


def raices(s):
    return {w[:6] for w in plano(s).split() if len(w) >= 5 and w not in VD.STOP}


def claves_de(p):
    return [plano(p["nombre"])] + [plano(a) for a in p.get("alias") or [] if (a or "").strip() and not plano(a).startswith("la ")
                                   and not plano(a).startswith("el ")]


def menciones(items, pers):
    """{nombre: [(i, t, presentado)]}: en qué escenas (en orden) suena cada persona y si va con su presentación
    (≥ 2 raíces de su `presentacion` en la misma escena)."""
    out = {}
    nombres = [plano(p["nombre"]) for p in pers]
    for p in pers:
        cl, rp, nom = claves_de(p), raices(p.get("presentacion") or ""), plano(p["nombre"])
        otros = [o for o in nombres if o != nom]
        for i, it in enumerate(items):
            v = plano(it["texto"])
            if not any(re.search(r"\b%s\b" % re.escape(c), v) and not (c != nom and any(c in o and re.search(r"\b%s\b" % re.escape(o), v) for o in otros))
                       for c in cl):
                continue
            pres = len(rp & raices(it["texto"])) >= min(2, len(rp))
            out.setdefault(p["nombre"], []).append((i, it.get("t", 0.0), pres))
    return out


def glosas(items):
    """[(sigla, i, t, texto)] cada vez que la voz explica una sigla («la Cicig, la comisión de la ONU…»)."""
    out = []
    for i, it in enumerate(items):
        for m in RE_GLOSA.finditer(it["texto"]):
            out.append((plano(m.group(1)), i, it.get("t", 0.0), m.group(0).strip()))
    return out


def informe_repeticiones(idx, pers):
    """Lo que se repite al pegar las partes tal cual (antes del montaje)."""
    items, t = [], 0.0
    for x in idx:
        items.append(dict(x, t=t))
        t += x["dur"] - VD.TRANSICION
    hechos = {}
    for x in idx:
        if x["resumen"] or x["marca"]:
            continue
        for h in x["hechos"]:
            hechos.setdefault(h, []).append(x["id"])
    rep_h = {h: v for h, v in hechos.items() if len({r.split(".")[0] for r in v}) > 1}   # dentro de una parte ya pasó SE
    frases = {}
    for x in idx:
        if x["resumen"]:
            continue
        for fr in frases_largas(x["texto"]):
            frases.setdefault(fr, []).append(x["id"])
    rep_f = {f: v for f, v in frases.items() if len(v) > 1}
    men = menciones(items, pers)
    rep_p = {n: [items[i]["id"] for i, _, pres in v if pres] for n, v in men.items()}
    rep_p = {n: v for n, v in rep_p.items() if len(v) > 1}
    gl = {}
    for s, i, _, txt in glosas(items):
        gl.setdefault(s, []).append({"id": items[i]["id"], "texto": txt})
    rep_g = {s: v for s, v in gl.items() if len(v) > 1}
    marcas = [{"id": x["id"], "por": x["marca"]} for x in idx if x["marca"]]
    muletillas = {}
    for x in idx:
        for m in re.finditer(r"ninguna fuente explica la diferencia|seg[uú]n la prensa", x["texto"], re.I):
            muletillas.setdefault(m.group(0).lower(), []).append(x["id"])
    return {"duracion_s": round(t, 1), "escenas": len(idx), "marcas": marcas, "hechos": rep_h, "frases": rep_f,
            "presentaciones": rep_p, "glosas": rep_g, "muletillas": {k: v for k, v in muletillas.items() if len(v) > 1}}


def lineas_repeticiones(R):
    L = ["## Lo que se repite al pegar las partes (%d escenas, %.1f min tal cual)" % (R["escenas"], R["duracion_s"] / 60), "",
         "### Marcas del formato corto (el script ya las quita: op quitar fija)"]
    L += ["- %s · %s" % (m["id"], m["por"]) for m in R["marcas"]] or ["- ninguna"]
    L += ["", "### Hechos contados más de una vez (id: escenas)"]
    L += ["- %s: %s" % (h, ", ".join(v)) for h, v in sorted(R["hechos"].items(), key=lambda kv: (-len(kv[1]), kv[0]))] or ["- ninguno"]
    L += ["", "### Frases de ≥ %d palabras repetidas" % FRASE_REPETIDA_PALABRAS]
    L += ["- «%s…»: %s" % (f[:70], ", ".join(v)) for f, v in R["frases"].items()] or ["- ninguna"]
    L += ["", "### Personas presentadas más de una vez (escenas con nombre + presentación)"]
    L += ["- %s: %s" % (n, ", ".join(v)) for n, v in R["presentaciones"].items()] or ["- ninguna"]
    L += ["", "### Siglas explicadas más de una vez"]
    L += ["- %s: %s" % (s, " · ".join("%s («%s»)" % (x["id"], x["texto"][:60]) for x in v)) for s, v in R["glosas"].items()] or ["- ninguna"]
    if R["muletillas"]:
        L += ["", "### Muletillas"] + ["- «%s»: %s" % (k, ", ".join(v)) for k, v in R["muletillas"].items()]
    return L


# ---------- preparar ----------
def estado_y(trabajo):
    return leer(os.path.join(trabajo, "youtube.json"))


def partes_de(Y):
    return [cargar_parte(p["n"], os.path.join(RAIZ, p["trabajo"])) for p in Y["partes"]]


def revisar_serie(S, base):
    """Lo que preparar exige: todas las partes entregadas, con su TRABAJO y la voz final de cada escena."""
    f = []
    dp = dirs_parte(base) if base else {}
    for p in S.get("partes") or []:
        if p.get("estado") != "entregada":
            f.append("la parte %d está en «%s»: el video largo se arma con la serie completa y entregada" % (p["n"], p.get("estado")))
            continue
        t = os.path.join(RAIZ, p["trabajo"]) if p.get("trabajo") else dp.get(p["n"])
        if not t or not os.path.isdir(t):
            f.append("la parte %d no tiene TRABAJO (%s)" % (p["n"], p.get("trabajo")))
            continue
        for req in ("guion.json", "escenas.json", "locucion.json"):
            if not os.path.exists(os.path.join(t, req)):
                f.append("la parte %d no tiene %s" % (p["n"], req))
        if os.path.exists(os.path.join(t, "escenas.json")):
            for S_ in leer(os.path.join(t, "escenas.json"))["escenas"]:
                if not os.path.exists(os.path.join(t, "audio", "voz_%d_r.mp3" % S_["n"])):
                    f.append("la parte %d no tiene la voz final de la escena %d (audio/voz_%d_r.mp3)" % (p["n"], S_["n"], S_["n"]))
    if len(S.get("partes") or []) < 2:
        f.append("una serie de una parte no se convierte en video largo")
    return f


def borrador(idx, S):
    caps = []
    for p in S["partes"]:
        es = []
        for x in [x for x in idx if x["parte"] == p["n"]]:
            e = {"ref": x["id"], "op": "quitar" if x["marca"] else "usar"}
            if x["marca"]:
                e["razon"] = x["marca"]
                e["fija"] = True
            es.append(e)
        caps.append({"parte": p["n"], "titulo": p.get("titulo") or "Parte %d" % p["n"], "puente": None, "escenas": es})
    return {"version": 1, "titulo": S.get("tema"), "promesa": None, "capitulos": caps}


def cmd_preparar(a):
    sj = ruta_serie(a.serie)
    if not sj:
        return falla("no encuentro serie.json para «%s»" % a.serie)
    S = leer(sj)
    base = os.path.join(RAIZ, S["trabajo"]) if S.get("trabajo") else None
    f = revisar_serie(S, base)
    if f:
        for x in f:
            print("FALLA", x)
        return 1
    if a.revisar:
        print("serie lista para el video largo: %d partes" % len(S["partes"]))
        return 0
    slug = S["slug"]
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", "youtube-" + slug))
    os.makedirs(trabajo, exist_ok=True)
    Y = {"version": 1, "slug": slug, "tema": S.get("tema"), "serie": rel(sj), "carpeta": rel(os.path.dirname(sj)),
         "base": S.get("trabajo"), "paleta": S.get("paleta"), "musica": S.get("musica"), "fecha": datetime.date.today().isoformat(),
         "fixture": bool(a.fixture or S.get("fixture")),
         "duracion_s": list(DURACION_S) if not (a.fixture or S.get("fixture")) else [30, 1200],
         "capitulo_min_s": CAPITULO_MIN_S if not (a.fixture or S.get("fixture")) else 10,
         "silencio_corte_s": SILENCIO_CORTE_S if not (a.fixture or S.get("fixture")) else 0.05,
         "partes": [{"n": p["n"], "titulo": p.get("titulo"), "trabajo": p.get("trabajo"), "ruta": p.get("ruta"),
                     "periodo": p.get("periodo"), "pregunta": p.get("pregunta")} for p in S["partes"]]}
    escribir(os.path.join(trabajo, "youtube.json"), Y)
    partes = partes_de(Y)
    idx = construir_indice(partes)
    escribir(os.path.join(trabajo, "indice.json"), {"escenas": idx})
    R = informe_repeticiones(idx, personajes_de(os.path.join(RAIZ, S["trabajo"])))
    escribir(os.path.join(trabajo, "repeticiones.json"), R)
    escribir(os.path.join(trabajo, "montaje.borrador.json"), borrador(idx, S))
    print("\n".join(lineas_repeticiones(R)))
    print("")
    print("partes %d · escenas %d · %.1f min tal cual · hechos repetidos %d · personas presentadas de nuevo %d · glosas repetidas %d"
          % (len(partes), len(idx), R["duracion_s"] / 60, len(R["hechos"]), len(R["presentaciones"]), len(R["glosas"])))
    print(rel(trabajo))
    return 0


# ---------- el montaje ----------
def cargar_contexto(trabajo):
    """(Y, partes, {id: escena del índice}, {(parte, n): S de escenas.json})"""
    Y = estado_y(trabajo)
    partes = partes_de(Y)
    idx = leer(os.path.join(trabajo, "indice.json"))["escenas"]
    S_de = {(P["n"], S["n"]): S for P in partes for S in P["E"]["escenas"]}
    return Y, partes, {x["id"]: x for x in idx}, S_de


def norm_w(w):
    return re.sub(r"[^\wáéíóúüñ]", "", (w or "").lower())


def tramo_de(toks, texto):
    """Índices (i0, i1) de los tokens que dicen `texto` (comparación sin mayúsculas ni puntuación); None si no está o
    está más de una vez."""
    ws = [norm_w(w) for w in texto.split() if norm_w(w)]
    tk = [norm_w(w["text"]) for w in toks]
    if not ws:
        return None, "vacío"
    hits = [i for i in range(len(tk) - len(ws) + 1) if tk[i:i + len(ws)] == ws]
    if not hits:
        return None, "no está en la voz de la escena (cópialo literal del digesto)"
    if len(hits) > 1:
        return None, "está %d veces en la escena: alarga el texto para que sea uno solo" % len(hits)
    return (hits[0], hits[0] + len(ws) - 1), None


def es_nombre(w):
    t = w["text"].strip("«»“”\"(")
    return bool(t) and t[0].isupper()


def intervalo_corte(toks, i0, i1):
    """[c0, c1) en segundos de la escena: del medio del silencio antes del tramo al medio del silencio después."""
    c0 = (toks[i0 - 1]["end"] + toks[i0]["start"]) / 2 if i0 > 0 else max(0.0, toks[i0]["start"] - 0.05)
    c1 = (toks[i1]["end"] + toks[i1 + 1]["start"]) / 2 if i1 + 1 < len(toks) else toks[i1]["end"] + 0.05
    return round(c0, 3), round(c1, 3)


def revisar_corte(toks, i0, i1, sil=SILENCIO_CORTE_S):
    """YT6 de un tramo: silencio a los dos lados, sin partir un nombre."""
    f = []
    if i0 > 0:
        gap = toks[i0]["start"] - toks[i0 - 1]["end"]
        if gap < sil:
            f.append("antes de «%s» hay %.0f ms de silencio (van ≥ %.0f): el corte se oiría; corta desde otra palabra o usa revozar"
                     % (toks[i0]["text"], gap * 1000, sil * 1000))
        if es_nombre(toks[i0 - 1]) and es_nombre(toks[i0]) and not re.search(r"[,.:;?!»]$", toks[i0 - 1]["text"]):
            f.append("el corte parte un nombre («%s %s»)" % (toks[i0 - 1]["text"], toks[i0]["text"]))
    if i1 + 1 < len(toks):
        gap = toks[i1 + 1]["start"] - toks[i1]["end"]
        if gap < sil:
            f.append("después de «%s» hay %.0f ms de silencio (van ≥ %.0f): el corte se oiría; corta hasta otra palabra o usa revozar"
                     % (toks[i1]["text"], gap * 1000, sil * 1000))
        if es_nombre(toks[i1]) and es_nombre(toks[i1 + 1]) and not re.search(r"[,.:;?!»]$", toks[i1]["text"]):
            f.append("el corte parte un nombre («%s %s»)" % (toks[i1]["text"], toks[i1 + 1]["text"]))
    return f


def limpiar_texto(s):
    s = re.sub(r"\s+([,.:;?!])", r"\1", s)
    s = re.sub(r",\s*([.:;?!])", r"\1", s)
    s = re.sub(r"([,:;])\s*,", r"\1", s)
    s = re.sub(r"^[,;:\s]+", "", s.strip())
    return s[:1].upper() + s[1:] if s else s


def aplicar_cortes(S, quitar, sil=SILENCIO_CORTE_S):
    """→ (toks que quedan, [(c0, c1)], fallas) de una escena con sus `quitar`."""
    toks = tokens_voz(S)
    tramos, f = [], []
    for q in quitar or []:
        r, err = tramo_de(toks, q)
        if err:
            f.append("«%s» %s" % (q, err))
            continue
        tramos.append(r)
    tramos.sort()
    for (a0, a1), (b0, b1) in zip(tramos, tramos[1:]):
        if b0 <= a1 + 1:
            f.append("dos cortes se tocan o se pisan: júntalos en un solo texto")
    for i0, i1 in tramos:
        f += revisar_corte(toks, i0, i1, sil)
    if tramos and sum(i1 - i0 + 1 for i0, i1 in tramos) >= len(toks):
        f.append("los cortes se llevan toda la voz: usa op quitar")
    quedan = [w for j, w in enumerate(toks) if not any(i0 <= j <= i1 for i0, i1 in tramos)]
    return quedan, [intervalo_corte(toks, i0, i1) for i0, i1 in tramos], f


def cola_de(S):
    return S.get("cola") if isinstance(S.get("cola"), (int, float)) else VD.COLA


def voz_nueva(texto):
    """(pantalla, voz en palabras, segmentos) de un texto nuevo, como video.py guion (cifras en palabras)."""
    NE.AVISOS.clear()
    segs = NE.segmentos(VD.sin_pausas(texto))
    VD.mayuscula_inicial(segs)
    avisos = list(NE.AVISOS)
    NE.AVISOS.clear()
    for s_ in segs:
        s_["p"], s_["v"] = VD.sin_pausas(s_["p"]), VD.sin_pausas(s_["v"])
    segs[0]["p"], segs[0]["v"] = segs[0]["p"].lstrip(), segs[0]["v"].lstrip()
    return "".join(x["p"] for x in segs), "".join(x["v"] for x in segs), segs, avisos


def estimado_nuevo(texto):
    return round(len(voz_nueva(texto)[1]) / VD.CPS + VD.COLA, 2)


ADELANTO_S = (3.0, 9.0)   # el adelanto: un momento alto ya grabado, antes del gancho


def adelanto_de(M, por_id, S_de, items):
    """montaje.adelanto = {ref: "Pk.eN", texto: "las palabras literales que se oyen"}: los primeros segundos del video son
    un momento alto que ya está grabado (una cita, una cifra), cortado de su escena; después entra el gancho. Cuida la
    intro de 30 s que YouTube mide. No es voz nueva (0 créditos) y la escena completa sigue en su sitio. → (item, fallas)."""
    a = M.get("adelanto")
    if not a:
        return None, []
    ref, texto = a.get("ref"), (a.get("texto") or "").strip()
    x = por_id.get(ref)
    if not x or not texto:
        return None, ["YT8 adelanto {ref, texto}: una escena del video y las palabras literales que se oyen de ella"]
    if x["tipo"] in ("gancho", "cierre") or not any(it["k"] == "escena" and it.get("ref") == ref for it in items):
        return None, ["YT8 adelanto.ref %s: una escena que queda en el video (no el gancho ni el cierre)" % ref]
    S = S_de[(x["parte"], x["n"])]
    pal = S.get("palabras") or []
    ws, toks = [VD._plano(w["text"]) for w in pal], VD._plano(texto).split()
    j = next((k for k in range(len(ws) - len(toks) + 1) if ws[k:k + len(toks)] == toks), None)
    if j is None:
        return None, ["YT8 adelanto.texto no está literal en la voz de %s (las palabras como las dice la voz: las cifras van "
                      "en palabras, «cinco millones», no «5,000,000»)" % ref]
    t0, t1 = pal[j]["start"], pal[j + len(toks) - 1]["end"]
    # se oye SOLO la frase: fuera lo de antes (desde 0: es la primera escena, sin transición de entrada) y lo de después,
    # cortando antes de que empiece la palabra siguiente
    sig = pal[j + len(toks)]["start"] if j + len(toks) < len(pal) else S["dur"]
    fin = round(min(t1 + 0.35, max(t1 + 0.05, sig - 0.04)), 3)
    cortes = ([(0.0, round(max(0.0, t0 - 0.1), 3))] if t0 - 0.1 > 0.1 else []) + ([(fin, round(S["dur"], 3))] if S["dur"] - fin > 0.1 else [])
    dur = round(S["dur"] - sum(c1 - c0 for c0, c1 in cortes), 3)
    f = []
    if not ADELANTO_S[0] <= dur <= ADELANTO_S[1]:
        f.append("YT8 el adelanto dura %.1f s (van %d–%d): una frase, no la escena" % (dur, *ADELANTO_S))
    return {"k": "adelanto", "ref": ref, "parte": x["parte"], "n": x["n"], "tipo": x["tipo"], "op": "usar", "hechos": [],
            "reprise": False, "texto": texto, "cortes": cortes, "dur": dur, "recortado": False}, f


def secuencia(M, Y, por_id, S_de):
    """El video en orden: [{k: escena|promesa|capitulo|puente, …, dur, texto}] (lo quitado no entra; queda en `quitado`
    del siguiente para YT5) y las fallas de resolución (YT1, YT6)."""
    items, f = [], []
    caps = M.get("capitulos") or []
    pr = M.get("promesa")
    total_caps = len(caps)
    for ci, c in enumerate(caps):
        cap_item = {"k": "capitulo", "parte": c.get("parte"), "numero": ci + 1, "total": total_caps, "titulo": c.get("titulo") or "",
                    "dur": CAPITULO_S, "texto": ""}
        es = c.get("escenas") or []
        pendiente_quitado = []
        def emitir_escena(e):
            ref = e.get("ref")
            x = por_id.get(ref)
            if not x:
                f.append("YT1 %s no existe" % ref)
                return
            op = e.get("op") or "usar"
            if op == "quitar":
                pendiente_quitado.append(ref)
                return
            S = S_de[(x["parte"], x["n"])]
            it = {"k": "escena", "ref": ref, "parte": x["parte"], "n": x["n"], "tipo": x["tipo"], "op": op,
                  "hechos": [h for h in x["hechos"] if h not in (e.get("sin_hechos") or [])], "reprise": bool(e.get("reprise")),
                  "ancla": e.get("ancla"), "quitado_antes": list(pendiente_quitado)}
            pendiente_quitado.clear()
            if op == "revozar":
                txt = (e.get("texto") or "").strip()
                it.update(texto=txt, dur=estimado_nuevo(txt) if txt else 0.0, cortes=[])
            else:
                quedan, cortes, fc = aplicar_cortes(S, e.get("quitar"), silencio_de(Y))
                f.extend("YT6 %s: %s" % (ref, x_) for x_ in fc)
                it.update(texto=limpiar_texto(texto_toks(quedan)), cortes=cortes,
                          dur=round(S["dur"] - sum(c1 - c0 for c0, c1 in cortes), 3), recortado=bool(e.get("quitar")))
            items.append(it)
        if ci == 0:
            if es:
                emitir_escena(es[0])
            if pr:
                items.append({"k": "promesa", "texto": (pr.get("texto") or "").strip(), "foto": pr.get("foto"), "titular": pr.get("titular"),
                              "hechos": pr.get("hechos") or [], "dur": estimado_nuevo(pr.get("texto") or "x")})
            # el capítulo 1 empieza en 0:00: su rótulo, mudo, a los 0:11 cortaba la intro que YouTube mide (los primeros
            # 30 s). No se dibuja; el capítulo sigue en la descripción (capitulos_de lo toma de `cap1`)
            if items:
                items[0]["cap1"] = cap_item
            resto = es[1:]
        else:
            items.append(cap_item)
            resto = es
        pu = c.get("puente")
        if pu:
            items.append({"k": "puente", "parte": c.get("parte"), "texto": (pu.get("texto") or "").strip(), "foto": pu.get("foto"),
                          "titular": pu.get("titular"),
                          "hechos": pu.get("hechos") or [], "dur": estimado_nuevo(pu.get("texto") or "x")})
        for e in resto:
            emitir_escena(e)
    ad, f_ad = adelanto_de(M, por_id, S_de, items)
    f.extend(f_ad)
    if ad:
        items.insert(0, ad)
    t = 0.0
    for it in items:
        it["t"] = round(t, 2)
        t += it["dur"] - VD.TRANSICION
    return items, f, round(t + VD.TRANSICION + FINAL_EXTRA_S, 1)


def silencio_de(Y):
    """El silencio mínimo para cortar (YT6): 80 ms con la voz real; la maqueta (voz falsa, pausas uniformes) baja a 50."""
    return Y.get("silencio_corte_s") or SILENCIO_CORTE_S


def hechos_serie(Y):
    """{id: hecho} de la cronología verificada de la serie (historia.json del TRABAJO base)."""
    try:
        H = leer(os.path.join(RAIZ, Y["base"], "historia.json"))
    except (OSError, ValueError, TypeError):
        return {}
    return {h["id"]: h for h in H.get("hechos") or []}


def fotos_serie(Y):
    out = {}
    for p in Y["partes"]:
        for j in glob.glob(os.path.join(RAIZ, p["trabajo"], "fotos", "*.json")):
            try:
                r = leer(j)
            except (OSError, ValueError):
                continue
            if r.get("archivo"):
                out.setdefault(r.get("id") or os.path.basename(j)[:-5], dict(r, _trabajo=p["trabajo"]))
    return out


def valores_de(Y):
    vals = []
    for p in Y["partes"]:
        try:
            st = leer(os.path.join(RAIZ, p["trabajo"], "video.json"))
            v, _, _ = VD.valores_respaldo(st["hilo"])
            vals += v
        except (OSError, ValueError, KeyError):
            continue
    return vals


def oraciones(t):
    return [o for o in re.split(r"(?<=[.?!…])\s+", (t or "").strip()) if o]


def revisar_montaje(M, Y, idx, S_de, partes):
    """YT1–YT8 → (fallas, avisos, items, total_s)."""
    f, av = [], []
    por_id = {x["id"]: x for x in idx}
    caps = M.get("capitulos") or []
    # YT1
    if [c.get("parte") for c in caps] != [p["n"] for p in Y["partes"]]:
        f.append("YT1 un capítulo por parte, en orden (%s); llegó %s" % ([p["n"] for p in Y["partes"]], [c.get("parte") for c in caps]))
    for c in caps:
        k = c.get("parte")
        esperadas = [x["id"] for x in idx if x["parte"] == k]
        dadas = [e.get("ref") for e in c.get("escenas") or []]
        if dadas != esperadas:
            faltan = [r for r in esperadas if r not in dadas]
            sobran = [r for r in dadas if r not in esperadas]
            f.append("YT1 capítulo %s: van todas sus escenas una vez y en orden (op quitar para sacarlas)%s%s%s" % (
                k, "; faltan " + ", ".join(faltan) if faltan else "", "; sobran " + ", ".join(map(str, sobran)) if sobran else "",
                "; el orden cambió" if not faltan and not sobran else ""))
        if not (c.get("titulo") or "").strip() or len(c.get("titulo") or "") > 60:
            f.append("YT1 capítulo %s: título de 1–60 caracteres" % k)
        for e in c.get("escenas") or []:
            x = por_id.get(e.get("ref"))
            op = e.get("op") or "usar"
            if op not in OPS:
                f.append("YT1 %s: op «%s» (usar|quitar|revozar)" % (e.get("ref"), op))
            if x and x["marca"] and op != "quitar":
                f.append("YT2 %s se quita siempre: %s" % (x["id"], x["marca"]))
            if op != "usar" and not (e.get("razon") or "").strip():
                f.append("YT1 %s: op %s lleva `razon`" % (e.get("ref"), op))
            if e.get("quitar") and op != "usar":
                f.append("YT1 %s: `quitar` va con op usar" % e.get("ref"))
            if x and x["tipo"] == "cita" and e.get("quitar"):
                f.append("YT6 %s es una cita: no se recorta (la cita se dice entera o se quita la escena)" % x["id"])
            if x and x["tipo"] == "gancho" and x["parte"] == 1 and op != "usar":
                f.append("YT1 el gancho de la parte 1 abre el video largo (op usar)")
    items, fr, total = secuencia(M, Y, por_id, S_de)
    f += fr
    voz_items = [it for it in items if it["k"] != "capitulo"]
    # YT2: nada del formato corto en la voz que queda
    for it in voz_items:
        nuevo = it["k"] in ("puente", "promesa") or it.get("op") == "revozar"   # lo grabado ya pasó P2 en su parte
        m = RE_ANUNCIO.search(it["texto"]) or (VD.META_PROMESA.search(it["texto"]) if nuevo else None)
        if m:
            f.append("YT2 %s dice «%s»: el video largo no anuncia lo que viene ni pide seguir la cuenta" % (etiqueta(it), m.group(0)))
    # YT3: uniones (puentes), y lo mismo para la promesa y las escenas revozadas en lo que aplica
    H = hechos_serie(Y)
    vals = valores_de(Y)
    fotos = fotos_serie(Y)
    n_puentes = 0
    for it in voz_items:
        if it["k"] not in ("puente", "promesa") and it.get("op") != "revozar":
            continue
        n_puentes += it["k"] == "puente"
        txt = it["texto"]
        os_ = oraciones(txt)
        if not txt:
            f.append("YT3 %s sin texto" % etiqueta(it))
            continue
        tope = PROMESA_CARACTERES if it["k"] == "promesa" else PUENTE_CARACTERES
        if it["k"] == "puente" and not 1 <= len(os_) <= PUENTE_ORACIONES:
            f.append("YT3 %s: 1–%d oraciones (llegaron %d)" % (etiqueta(it), PUENTE_ORACIONES, len(os_)))
        if it["k"] == "promesa" and len(os_) != 1:
            f.append("YT8 la promesa global es una oración")
        for o in os_:
            if len(o) > tope and it.get("op") != "revozar":
                f.append("YT3 %s: «%s…» pasa de %d caracteres" % (etiqueta(it), o[:50], tope))
        if it["k"] in ("puente", "promesa"):
            if not it.get("hechos"):
                f.append("YT3 %s: `hechos` con los ids que sostienen la frase (confirmado o una_fuente)" % etiqueta(it))
            for h in it.get("hechos") or []:
                if H and h not in H:
                    f.append("YT3 %s: el hecho %s no está en la cronología" % (etiqueta(it), h))
                elif H and H[h].get("estado") not in ("confirmado", "una_fuente"):
                    f.append("YT3 %s: el hecho %s está %s (van confirmado o una_fuente)" % (etiqueta(it), h, H[h].get("estado")))
            tit = (it.get("titular") or "").split()
            if not 1 <= len(tit) <= 7:
                f.append("YT3 %s: `titular` de 1–7 palabras (la línea de arriba de la foto)" % etiqueta(it))
            if not it.get("foto") or it["foto"] not in fotos:
                f.append("YT3 %s: `foto` con el id de una foto de la serie (digesto: Fotos)" % etiqueta(it))
        sin = VD.sin_respaldo(txt, vals) if vals else []
        if sin:
            f.append("YT3 %s: números sin respaldo en los datos de la serie: %s" % (etiqueta(it), ", ".join(map(str, sin))))
        _, voz, _, avs = voz_nueva(txt)
        f.extend("YT3 %s: %s" % (etiqueta(it), x_) for x_ in avs)
    revs = [it for it in voz_items if it.get("op") == "revozar"]
    if len(revs) > REVOZAR_MAX:
        f.append("YT6 %d escenas revozadas (máximo %d): recorta en lugar de reescribir" % (len(revs), REVOZAR_MAX))
    # YT4: repetición en lo que queda
    vistos = {}
    reprises = 0
    for it in voz_items:
        if it["k"] != "escena":
            continue
        for h in it.get("hechos") or []:
            if h in vistos and it.get("parte") != vistos[h][1]:
                if it.get("reprise"):
                    continue
                f.append("YT4 %s cuenta otra vez %s (ya en %s): quita la escena, recorta la frase (y declara `sin_hechos`) o "
                         "márcala `reprise` con razón si la referencia atrás ayuda" % (etiqueta(it), h, vistos[h][0]))
            vistos.setdefault(h, (etiqueta(it), it.get("parte")))
        reprises += bool(it.get("reprise"))
    if reprises > REPRISE_MAX:
        f.append("YT4 %d escenas `reprise` (máximo %d)" % (reprises, REPRISE_MAX))
    for it in voz_items:
        if it.get("reprise") and not (por_id_razon(M, it.get("ref"))):
            f.append("YT4 %s: `reprise` lleva `razon`" % etiqueta(it))
    vistas_f = {}
    for it in voz_items:
        if it.get("reprise"):   # una referencia atrás declarada repite a propósito
            continue
        for fr_ in frases_largas(it["texto"]):
            if fr_ in vistas_f:
                f.append("YT4 %s repite una frase de %s («%s…»)" % (etiqueta(it), vistas_f[fr_], fr_[:60]))
            vistas_f.setdefault(fr_, etiqueta(it))
    pers = personajes_de(os.path.join(RAIZ, Y["base"])) if Y.get("base") else []
    for nombre, ms in menciones(voz_items, pers).items():
        ult_pres, ult_t = None, None
        for i, t, pres in ms:
            if pres and ult_pres is not None and t - ult_t < RECORDATORIO_S:
                f.append("YT4 %s presenta otra vez a %s (ya presentado %.0f s antes, en %s): quita el inciso con `quitar`"
                         % (etiqueta(voz_items[i]), nombre, t - ult_t, etiqueta(voz_items[ult_pres])))
            elif pres and ult_pres is not None:
                av.append("YT4 %s vuelve a presentar a %s tras %.0f s: vale si es corto («el comisionado Velásquez»)"
                          % (etiqueta(voz_items[i]), nombre, t - ult_t))
            if pres:
                ult_pres = i
            ult_t = t
    gl_ult = {}
    for s_, i, t, txt in glosas(voz_items):
        if s_ in gl_ult and t - gl_ult[s_][1] < RECORDATORIO_S:
            f.append("YT4 %s vuelve a explicar la sigla (%s «%s»; ya en %s): quítalo con `quitar`"
                     % (etiqueta(voz_items[i]), s_.upper(), txt[:50], etiqueta(voz_items[gl_ult[s_][0]])))
        gl_ult[s_] = (i, t)
    # YT5: lo que sigue a un corte
    for it in voz_items:
        if it["k"] == "escena" and it.get("quitado_antes") and not it.get("ancla") and RE_ANAFORA.match(it["texto"] or ""):
            av.append("YT5 %s abre con «%s» justo después de quitar %s: ¿a qué se refiere? declara `ancla` o recorta"
                      % (etiqueta(it), (it["texto"] or "").split()[0], ", ".join(it["quitado_antes"])))
    # YT7
    lo, hi = Y.get("duracion_s") or DURACION_S
    if not lo <= total <= hi:
        f.append("YT7 %.1f min estimados (van %.0f–%.0f min)" % (total / 60, lo / 60, hi / 60))
    cap_min = Y.get("capitulo_min_s") or CAPITULO_MIN_S
    for c_ in capitulos_de(items, total):
        if c_["dur"] < cap_min:
            f.append("YT7 el capítulo %d («%s») dura %.0f s (mínimo %d)" % (c_["numero"], c_["titulo"], c_["dur"], cap_min))
    # YT11 (lo que el montaje ya trae para la entrega): título y descripción de YouTube
    yt = M.get("youtube") or {}
    if not (yt.get("titulo") or "").strip() or len(yt.get("titulo") or "") > 100:
        f.append("YT11 youtube.titulo de 1–100 caracteres, con el sujeto reconocible")
    if not (yt.get("descripcion") or "").strip():
        f.append("YT11 youtube.descripcion: 2–4 oraciones de qué trata, sin anunciar el final")
    elif VD.META_PROMESA.search(yt["descripcion"]) or RE_ANUNCIO.search(yt["descripcion"]):
        f.append("YT11 youtube.descripcion anuncia el video o pide seguir la cuenta: la intriga sale del tema")
    # YT8
    pr = M.get("promesa")
    if not pr:
        f.append("YT8 falta la promesa global (una oración tras el gancho que abre la pregunta del video entero)")
    else:
        if pr.get("forma") not in VD.PROMESA_FORMAS:
            f.append("YT8 promesa.forma «%s» (%s)" % (pr.get("forma"), "|".join(VD.PROMESA_FORMAS)))
        pago = next((it for it in voz_items if it["k"] == "escena" and it["ref"] == pr.get("pago")), None)
        if not pago:
            f.append("YT8 promesa.pago «%s» no es una escena que quede en el video" % pr.get("pago"))
        elif pago["t"] < PAGO_DESDE * total:
            f.append("YT8 la promesa se paga en %s (%.0f %% del video): va en el último %d %%"
                     % (pr.get("pago"), 100 * pago["t"] / total, round(100 * (1 - PAGO_DESDE))))
    # imagen (avisos): una foto que sale 3 veces o más, o una foto fija de más de 12 s, se notan en 12 minutos
    usos = {}
    for it in voz_items:
        x = por_id.get(it.get("ref")) if it["k"] == "escena" else None
        if x and x.get("tipo") == "foto" and x.get("foto"):
            usos.setdefault(x["foto"], []).append(it["ref"])
            if (x.get("dur") or 0) > VD.NOVEDAD_FALLA_S + 7 and not it.get("cortes"):
                av.append("imagen: %s es una foto fija de %.0f s: recorta su contexto o parte la escena en la serie" % (it["ref"], x["dur"]))
    for fo_, refs in usos.items():
        if len(refs) >= 3:
            av.append("imagen: la foto %s sale %d veces (%s): quita la escena que menos aporta" % (fo_, len(refs), ", ".join(refs)))
    if pr:
        # la recompensa clara (P6): la promesa se oye antes del segundo 15 y lleva su pregunta para la pantalla
        prom = next((it for it in voz_items if it["k"] == "promesa"), None)
        if prom and prom.get("t", 0) > PROMESA_ANTES_S:
            f.append("YT8 la promesa empieza a los %.0f s: va antes del segundo %d (tras el gancho, antes del contexto)"
                     % (prom["t"], PROMESA_ANTES_S))
        q = (pr.get("pregunta") or "").strip()
        nuevo = str(Y.get("fecha") or VD.P6_DESDE) >= VD.P6_DESDE
        if not q:
            (f if nuevo else av).append("YT8 falta promesa.pregunta: la pregunta que el video entero responde (≤ %d palabras), "
                                        "para la pantalla" % VD.PREGUNTA_PALABRAS)
        elif not (q.startswith("¿") and q.endswith("?")) or len(q.split()) > VD.PREGUNTA_PALABRAS or VD.META_PROMESA.search(q):
            f.append("YT8 promesa.pregunta: una pregunta («¿…?») de ≤ %d palabras que no anuncia el video" % VD.PREGUNTA_PALABRAS)
    return f, av, items, total


def por_id_razon(M, ref):
    for c in M.get("capitulos") or []:
        for e in c.get("escenas") or []:
            if e.get("ref") == ref:
                return (e.get("razon") or "").strip()
    return ""


def etiqueta(it):
    return {"escena": it.get("ref"), "promesa": "la promesa", "puente": "el puente del capítulo %s" % it.get("parte"),
            "capitulo": "el rótulo %s" % it.get("numero")}.get(it["k"], it["k"])


def capitulos_de(items, total):
    """[{numero, titulo, t, dur}]: el capítulo 1 empieza en 0:00 (abre con el gancho y la promesa)."""
    caps = [it for it in items if it["k"] == "capitulo"]
    c1 = next((it["cap1"] for it in items if it.get("cap1")), None)
    if c1 and not any(c.get("numero") == 1 for c in caps):
        caps = [dict(c1, t=0.0)] + caps
    out = []
    for j, c in enumerate(caps):
        t0 = 0.0 if j == 0 else c["t"]
        t1 = caps[j + 1]["t"] if j + 1 < len(caps) else total
        out.append({"numero": c["numero"], "titulo": c["titulo"], "parte": c["parte"], "t": round(t0, 2), "dur": round(t1 - t0, 1)})
    return out


def mmss(t):
    t = int(round(t))
    return "%d:%02d:%02d" % (t // 3600, t % 3600 // 60, t % 60) if t >= 3600 else "%d:%02d" % (t // 60, t % 60)


def retorno(trabajo, ok, f, items, total):
    q = [it for it in items if it["k"] == "escena"]
    return {"archivo": rel(os.path.join(trabajo, "montaje.json")), "gate": "ok" if ok else "falla", "fallas": f,
            "duracion_min": round(total / 60, 1), "escenas": len(q), "recortadas": sum(1 for it in q if it.get("recortado")),
            "revozadas": sum(1 for it in q if it.get("op") == "revozar"),
            "puentes": sum(1 for it in items if it["k"] == "puente"), "promesa": any(it["k"] == "promesa" for it in items)}


def correr_check(trabajo, M):
    Y, partes, por_id, S_de = cargar_contexto(trabajo)
    idx = list(por_id.values())
    return revisar_montaje(M, Y, idx, S_de, partes)


def cmd_montaje(a):
    trabajo = os.path.abspath(a.trabajo)
    try:
        M = leer(os.path.join(trabajo, "montaje.json"))
    except (OSError, ValueError) as ex:
        return falla("montaje.json ilegible: %s" % ex)
    f, av, items, total = correr_check(trabajo, M)
    for it in items:
        print("%7s  %-9s %-10s %5.1f s  %s" % (mmss(it["t"]), it["k"], it.get("ref") or it.get("titulo") or "", it["dur"],
                                               (it.get("texto") or "")[:90]))
    print("total ≈ %s (%.1f min) · %d piezas" % (mmss(total), total / 60, len(items)))
    for x in av:
        print("AVISO", x)
    for x in f:
        print("FALLA", x)
    ok = not f
    if ok:
        print("YT1–YT8 ok")
        escribir(os.path.join(trabajo, "secuencia.json"), {"total_s": total, "items": items})
    print("RETORNO " + json.dumps(retorno(trabajo, ok, f, items, total), ensure_ascii=False))
    return 0 if ok else 1


def aplicar_cambios(M, cambios):
    """Cambios: [{op: escena, ref, set: {...}} | {op: puente, parte, valor} | {op: promesa, valor} | {op: titulo, parte, valor}]."""
    M = copy.deepcopy(M)
    for c in cambios:
        if c.get("op") == "escena":
            for cap in M["capitulos"]:
                for e in cap["escenas"]:
                    if e["ref"] == c.get("ref"):
                        for k, v in (c.get("set") or {}).items():
                            if v is None:
                                e.pop(k, None)
                            else:
                                e[k] = v
        elif c.get("op") == "puente":
            for cap in M["capitulos"]:
                if cap["parte"] == c.get("parte"):
                    cap["puente"] = c.get("valor")
        elif c.get("op") == "titulo":
            for cap in M["capitulos"]:
                if cap["parte"] == c.get("parte"):
                    cap["titulo"] = c.get("valor")
        elif c.get("op") == "promesa":
            M["promesa"] = c.get("valor")
        else:
            raise ValueError("cambio desconocido: %s" % json.dumps(c, ensure_ascii=False))
    return M


def cmd_probar(a, escribir_si_pasa=False):
    trabajo = os.path.abspath(a.trabajo)
    M = leer(os.path.join(trabajo, "montaje.json"))
    try:
        cambios = json.loads(a.cambios) if a.cambios.strip()[:1] in "[{" else leer(a.cambios)   # JSON en línea o archivo
        M2 = aplicar_cambios(M, cambios if isinstance(cambios, list) else cambios.get("cambios") or [])
    except (OSError, ValueError) as ex:
        return falla("cambios: %s" % ex)
    f, av, items, total = correr_check(trabajo, M2)
    antes, _, _, t_antes = correr_check(trabajo, M)
    nuevas = [x for x in f if x not in antes]
    for x in av:
        print("AVISO", x)
    for x in f:
        print("FALLA", x)
    print("con los cambios: %.1f min (antes %.1f) · fallas %d (nuevas %d)" % (total / 60, t_antes / 60, len(f), len(nuevas)))
    if escribir_si_pasa:
        if f:
            print("no se aplicó: el montaje con los cambios no pasa YT1–YT8")
            return 1
        shutil.copy(os.path.join(trabajo, "montaje.json"), os.path.join(trabajo, "montaje.previo.json"))
        escribir(os.path.join(trabajo, "montaje.json"), M2)
        escribir(os.path.join(trabajo, "secuencia.json"), {"total_s": total, "items": items})
        print("aplicado → %s" % rel(os.path.join(trabajo, "montaje.json")))
        return 0
    return 1 if nuevas else 0


def cmd_aplicar(a):
    return cmd_probar(a, escribir_si_pasa=True)


def cmd_resumen(a):
    trabajo = os.path.abspath(a.trabajo)
    M = leer(os.path.join(trabajo, "montaje.json"))
    f, av, items, total = correr_check(trabajo, M)
    q = [it for it in items if it["k"] == "escena"]
    quit = sum(1 for c in M["capitulos"] for e in c["escenas"] if (e.get("op") or "usar") == "quitar")
    L = ["# Montaje · %s" % (M.get("titulo") or ""), "",
         "Duración ≈ **%s** (%.1f min) · %d escenas · %d quitadas · %d recortadas · %d revozadas · %d uniones" % (
             mmss(total), total / 60, len(q), quit, sum(1 for it in q if it.get("recortado")),
             sum(1 for it in q if it.get("op") == "revozar"), sum(1 for it in items if it["k"] == "puente")), ""]
    pr = M.get("promesa") or {}
    L += ["**Promesa** (%s, se paga en %s): «%s»" % (pr.get("forma"), pr.get("pago"), pr.get("texto")), "", "## Capítulos"]
    for c_ in capitulos_de(items, total):
        L.append("- %s %s" % (mmss(c_["t"]), c_["titulo"]))
    L += ["", "## Uniones (voz nueva)"]
    L += ["- Cap. %s: «%s»" % (it.get("parte"), it["texto"]) for it in items if it["k"] == "puente"] or ["- ninguna"]
    L += ["", "## Escenas reescritas (voz nueva)"]
    L += ["- %s: «%s»" % (it["ref"], it["texto"]) for it in q if it.get("op") == "revozar"] or ["- ninguna"]
    L += ["", "## Cortes"]
    for c in M["capitulos"]:
        for e in c["escenas"]:
            if (e.get("op") or "usar") == "quitar" and not e.get("fija"):
                L.append("- %s fuera: %s" % (e["ref"], e.get("razon")))
            elif e.get("quitar"):
                L.append("- %s sin «%s»" % (e["ref"], "», «".join(e["quitar"])))
    nuevos = sum(len(voz_nueva(it["texto"])[1]) for it in items if it["k"] in ("puente", "promesa") or it.get("op") == "revozar")
    L += ["", "Voz nueva: %d caracteres (≈ %d créditos)." % (nuevos, nuevos)]
    if f:
        L += ["", "## Falta arreglar"] + ["- " + x for x in f]
    if av:
        L += ["", "## Avisos"] + ["- " + x for x in av]
    print("\n".join(L))
    return 0


# ---------- digestos ----------
def lineas_escena_editor(x, S, sil=SILENCIO_CORTE_S):
    L = ["### %s · %s · %.1f s%s%s" % (x["id"], x["tipo"], x["dur"], " · hechos " + ", ".join(x["hechos"]) if x["hechos"] else "",
                                         " · FIJA: " + x["marca"] if x["marca"] else "")]
    for fr in x["frases"]:
        L.append("  %s  %s" % (fr["id"].split(".")[-1], fr["texto"]))
    toks = tokens_voz(S)
    cortes = [toks[i]["text"] for i in range(1, len(toks)) if toks[i]["start"] - toks[i - 1]["end"] >= sil]
    if cortes:
        L.append("  silencios ≥ %.0f ms antes de: %s" % (sil * 1000, " · ".join(cortes)))
    return L


def cmd_digesto(a):
    trabajo = os.path.abspath(a.trabajo)
    Y, partes, por_id, S_de = cargar_contexto(trabajo)
    idx = list(por_id.values())
    if a.para == "editor":
        R = leer(os.path.join(trabajo, "repeticiones.json"))
        H = hechos_serie(Y)
        L = ["# Montaje del video largo · %s" % Y.get("tema"), "",
             "Serie de %d partes, %.1f min tal cual. Objetivo: %.0f–%.0f min. Lee referencias/roles/youtube-editor.md." % (
                 len(partes), R["duracion_s"] / 60, Y["duracion_s"][0] / 60, Y["duracion_s"][1] / 60), ""]
        L += ["## Partes"] + ["- P%d · %s · %s · periodo %s–%s" % (p["n"], p.get("titulo"), p.get("pregunta"),
                                                                  (p.get("periodo") or {}).get("desde"), (p.get("periodo") or {}).get("hasta"))
                               for p in Y["partes"]]
        L += [""] + lineas_repeticiones(R)
        pers = personajes_de(os.path.join(RAIZ, Y["base"])) if Y.get("base") else []
        if pers:
            L += ["", "## Personas (la presentación completa va una sola vez en todo el video)"]
            L += ["- %s — %s" % (p["nombre"], p.get("presentacion")) for p in pers]
        L += ["", "## Escenas (frases f1…; para recortar copia el texto literal de una frase o de un inciso)"]
        for x in idx:
            L += lineas_escena_editor(x, S_de[(x["parte"], x["n"])], silencio_de(Y))
        L += ["", "## Hechos verificados (para los `hechos` de los puentes y de la promesa)"]
        L += ["- %s · %s · %s — %s" % (h, v.get("fecha"), v.get("estado"), v.get("texto")) for h, v in H.items()
              if v.get("estado") in ("confirmado", "una_fuente")]
        L += ["", "## Fotos de la serie (para la `foto` de los puentes y de la promesa)"]
        L += ["- %s · %s · %s" % (k, r.get("descripcion") or "", r.get("credito") or "") for k, r in sorted(fotos_serie(Y).items())]
        L += ["", "Escribe %s (parte de %s) y corre: python3 scripts/youtube.py montaje %s --check" % (
            rel(os.path.join(trabajo, "montaje.json")), rel(os.path.join(trabajo, "montaje.borrador.json")), rel(trabajo))]
        print("\n".join(L))
        return 0
    M = leer(os.path.join(trabajo, "montaje.json"))
    items, _, total = secuencia(M, Y, por_id, S_de)
    if a.para == "oyente":
        L = ["# Lo que se oye y se lee, en orden (un video de YouTube de %.0f min, horizontal)" % (total / 60), "",
             "Escenas numeradas E1…EN. Un rótulo de capítulo no tiene voz: solo su título en pantalla.", ""]
        for j, it in enumerate(items, 1):
            if it["k"] == "capitulo":
                L.append("E%d · rótulo · PANTALLA: «Capítulo %d · %s»" % (j, it["numero"], it["titulo"]))
                continue
            L.append("E%d · %s · VOZ: %s" % (j, it.get("tipo") or it["k"], it["texto"]))
        print("\n".join(L))
        return 0
    # crítico: el montaje con sus referencias, el informe de repeticiones y lo que queda
    L = ["# Crítica del montaje · %s (%.1f min)" % (Y.get("tema"), total / 60), ""]
    pr = M.get("promesa") or {}
    L += ["Promesa (%s, paga %s): «%s»" % (pr.get("forma"), pr.get("pago"), pr.get("texto")), ""]
    for j, it in enumerate(items, 1):
        if it["k"] == "capitulo":
            L.append("E%d · %s · CAPÍTULO %d «%s»" % (j, mmss(it["t"]), it["numero"], it["titulo"]))
        else:
            L.append("E%d · %s · %s%s%s · %s" % (j, mmss(it["t"]), it.get("ref") or it["k"],
                                                " (recortada)" if it.get("recortado") else "", " (REVOZADA)" if it.get("op") == "revozar" else "",
                                                it["texto"]))
    R = leer(os.path.join(trabajo, "repeticiones.json"))
    L += [""] + lineas_repeticiones(R)
    print("\n".join(L))
    return 0


# ---------- voz nueva (nuevas/) ----------
def enlazar(src, dst):
    if os.path.exists(dst):
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def fuente_de_hechos(H, ids):
    for h in ids or []:
        for f_ in (H.get(h) or {}).get("fuentes") or []:
            if f_.get("medio"):
                return f_["medio"]
    return None


def fecha_de_hechos(H, ids):
    for h in ids or []:
        fe = str((H.get(h) or {}).get("fecha") or "")
        m = re.match(r"(\d{4})(?:-(\d{2}))?", fe)
        if m:
            meses = ("", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
                     "Noviembre", "Diciembre")
            return ("%s %s" % (meses[int(m.group(2))], m.group(1))) if m.group(2) else m.group(1)
    return ""


def piezas_nuevas(items):
    """Las piezas con voz nueva, en orden: [(item, n en nuevas/)]."""
    out = []
    for it in items:
        if it["k"] in ("puente", "promesa") or it.get("op") == "revozar":
            out.append((it, len(out) + 1))
    return out


def cmd_voz(a):
    """Arma nuevas/ (un TRABAJO de /historia con solo las piezas de voz nueva) e imprime los nodos para el MCP
    (o, con --falsa, graba la voz falsa)."""
    trabajo = os.path.abspath(a.trabajo)
    Y, partes, por_id, S_de = cargar_contexto(trabajo)
    M = leer(os.path.join(trabajo, "montaje.json"))
    f, _, items, _ = revisar_montaje(M, Y, list(por_id.values()), S_de, partes)
    if f and not getattr(a, "sin_gate", False):
        for x in f:
            print("FALLA", x)
        return falla("el montaje no pasa YT1–YT8: corre youtube.py montaje --check")
    nv = os.path.join(trabajo, "nuevas")
    P1 = os.path.join(RAIZ, Y["partes"][0]["trabajo"])
    os.makedirs(os.path.join(nv, "audio"), exist_ok=True)
    for nombre in ("video.json", "encuadre.json", "historia.json"):
        if os.path.exists(os.path.join(P1, nombre)):
            shutil.copy2(os.path.join(P1, nombre), os.path.join(nv, nombre))
    st = leer(os.path.join(nv, "video.json"))
    st["serie"] = None
    st["piezas_sueltas"] = True   # m115: piezas de voz sueltas, no un video: sin el aviso de duración V6
    for k in ("piso_s", "palabra_clave", "departamento"):   # gates de un video corto: no aplican a las piezas sueltas
        st.pop(k, None)
    st["hilo"] = rel(os.path.join(P1, "base")) if os.path.isdir(os.path.join(P1, "base")) else st.get("hilo")
    escribir(os.path.join(nv, "video.json"), st)
    for fid, r in fotos_serie(Y).items():
        for ext in ("", ".json"):
            src = os.path.join(RAIZ, r["_trabajo"], r["archivo"] if not ext else os.path.join("fotos", fid + ".json"))
            dst = os.path.join(nv, r["archivo"] if not ext else os.path.join("fotos", fid + ".json"))
            if os.path.exists(src):
                enlazar(src, dst)
    H = hechos_serie(Y)
    g1 = partes[0]["guion"]
    escenas, loc = [], []
    for it, n in piezas_nuevas(items):
        if it.get("op") == "revozar":
            eg = copy.deepcopy(escena_guion(next(P for P in partes if P["n"] == it["parte"]), it["n"]))
            eg.pop("acto", None)
            eg["texto"] = it["texto"]
        else:
            ids = it.get("hechos") or []
            fuente = fuente_de_hechos(H, ids)
            eg = {"tipo": "foto", "foto": it.get("foto"), "fecha": fecha_de_hechos(H, ids), "lugar": "",
                  "titular": (it.get("titular") or "").strip(), "hechos": ids, "texto": it["texto"]}
            if fuente:
                eg["fuente"] = fuente
        escenas.append(eg)
        pantalla, voz, segs, _ = voz_nueva(eg["texto"])
        prompt = VD.sin_comillas(VD.con_breaks("".join(s_["v"] for s_ in segs)))
        loc.append({"n": n, "tipo": "foto", "tuit": None, "plantilla": "foto", "acto": None, "secuencia": None, "cola": VD.COLA,
                    "pantalla": pantalla, "voz": voz, "prompt": prompt, "segmentos": segs, "pieza": etiqueta(it),
                    "estimado_s": round(len(voz) / VD.CPS + VD.COLA, 2)})
    if not loc:
        print("el montaje no tiene voz nueva")
        return 0
    escribir(os.path.join(nv, "guion.json"), {"tipo": g1.get("tipo"), "contexto_superior": sin_kicker_serie(g1.get("contexto_superior")),
                                               "promesa": None, "secuencias": [], "voz_continua": False, "escenas": escenas,
                                               "cierre": {"resumen": [], "texto": "", "final": "", "tipo": "remate"}, "caption": {}})
    lv = leer(os.path.join(P1, "locucion.json"))
    car = sum(len(x["voz"]) for x in loc)
    escribir(os.path.join(nv, "locucion.json"), {"voz": lv["voz"], "caracteres": car, "estimado_s": sum(x["estimado_s"] for x in loc),
                                                  "duracion": "youtube", "objetivo_s": int(sum(x["estimado_s"] for x in loc)) or 1,
                                                  "n_escenas": len(loc), "promesa": None, "voz_continua": False, "secuencias": [],
                                                  "escenas": loc})
    for x in loc:
        print("N%-2d %-28s %3d car · %s" % (x["n"], x["pieza"], len(x["voz"]), x["voz"]), file=sys.stderr)
    if a.falsa:
        return VD.cmd_voz_falsa(argparse.Namespace(trabajo=nv))
    return VD.cmd_voz(argparse.Namespace(trabajo=nv, pendientes=False, sueltas=True, solo=None))


def cmd_tiempos(a):
    """Los tiempos de las piezas nuevas (historia.py tiempos sobre nuevas/: V16, foto, tarjeta de persona)."""
    trabajo = os.path.abspath(a.trabajo)
    nv = os.path.join(trabajo, "nuevas")
    if not os.path.exists(os.path.join(nv, "locucion.json")):
        print("sin voz nueva")
        return 0
    return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "historia.py"), "tiempos", nv], cwd=RAIZ).returncode


# ---------- armar ----------
TIEMPO_ESCALAR = {"t", "start", "end", "fin", "fin_voz", "ini", "tit", "linea_fin", "nota", "desde", "hasta", "preg", "sigue",
                  "fin_final", "r2", "campana", "clic", "entra", "resalte_t"}
TIEMPO_LISTA = {"oraciones", "pulso", "cuenta", "latidos", "resalte", "r", "saltos", "dicho", "marcador"}
SIN_TIEMPO = {"focos", "foco", "kb", "dividida", "colores", "toma"}


def mover(t, cortes):
    """Un tiempo de la escena original → el de la escena recortada."""
    d = 0.0
    for c0, c1 in cortes:
        if t >= c1:
            d += c1 - c0
        elif t > c0:
            return round(c0 - d, 3)
    return round(t - d, 3)


def correr_tiempos(o, cortes, clave=None):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k in SIN_TIEMPO:
                continue
            if k == "valores" and isinstance(v, dict):
                o[k] = {kk: [mover(x, cortes) for x in vv] if isinstance(vv, list) else vv for kk, vv in v.items()}
            elif isinstance(v, (int, float)) and not isinstance(v, bool) and k in TIEMPO_ESCALAR:
                o[k] = mover(v, cortes)
            elif isinstance(v, list) and k in TIEMPO_LISTA:
                o[k] = [mover(x, cortes) if isinstance(x, (int, float)) and not isinstance(x, bool) else correr_tiempos(x, cortes) for x in v]
            else:
                correr_tiempos(v, cortes, k)
    elif isinstance(o, list):
        for x in o:
            correr_tiempos(x, cortes, clave)
    return o


def recortar_escena(S, cortes):
    """La escena con sus tiempos corridos: sin las palabras del tramo cortado; lo demás se corre o se pega al corte."""
    S = copy.deepcopy(S)
    quitado = sum(c1 - c0 for c0, c1 in cortes)
    pal = []
    for w in S.get("palabras") or []:
        if any(c0 <= (w["start"] + w["end"]) / 2 < c1 for c0, c1 in cortes):
            continue
        pal.append(w)
    S["palabras"] = pal
    dur = S["dur"]
    for k in ("palabras",):
        S[k] = correr_tiempos(S[k], cortes)
    for k, v in list(S.items()):
        if k in ("palabras", "n", "dur", "cola", "acto", "secuencia", "tuit") or k in SIN_TIEMPO:
            continue
        if k in TIEMPO_ESCALAR and isinstance(v, (int, float)) and not isinstance(v, bool):
            S[k] = mover(v, cortes)
        elif isinstance(v, (dict, list)):
            S[k] = correr_tiempos(v, cortes, k)
    S["dur"] = round(dur - quitado, 3)
    if S.get("T", {}).get("dur") is not None:
        S["T"]["dur"] = S["dur"]
    S["eventos"] = [x for x in S.get("eventos") or [] if x["t"] <= S["dur"]]
    if not S["eventos"] or S["eventos"][-1]["tipo"] != "fin":
        S["eventos"].append({"t": S["dur"], "tipo": "fin"})
    else:
        S["eventos"][-1]["t"] = S["dur"]
    S["sfx"] = [x for x in S.get("sfx") or [] if x["t"] < S["dur"] - 0.2]
    return S


def recortar_audio(src, dst, cortes):
    """El mp3 sin los tramos [c0, c1): atrim de lo que queda, fundidos de 4 ms (con 12 y 25 ms la escucha YT6 dejaba de reconocer una escena recortada) y concat (como partir_secuencia)."""
    if not cortes:
        enlazar(src, dst)
        return
    largo = VD.ffprobe_dur(src)
    trozos, t = [], 0.0
    for c0, c1 in cortes:
        if c0 > t:
            trozos.append((t, c0))
        t = c1
    if t < largo:
        trozos.append((t, largo))
    fc = ""
    for i, (a0, a1) in enumerate(trozos):
        d = min(FUNDIDO_CORTE_S, max(0.004, (a1 - a0) / 4))
        fc += "[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=%.3f,afade=t=out:st=%.3f:d=%.3f[t%d];" % (
            a0, a1, d, max(0, a1 - a0 - d), d, i)
    fc += "".join("[t%d]" % i for i in range(len(trozos))) + "concat=n=%d:v=0:a=1[a]" % len(trozos)
    VD.ff("-i", src, "-filter_complex", fc, "-map", "[a]", "-ar", "44100", "-b:a", "192k", dst)


def silencio(dst, dur):
    VD.ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "%.3f" % dur, "-b:a", "128k", dst)


def escena_capitulo(it, n, anios):
    """El rótulo de capítulo (video/historia.html en modo capitulo): sin voz, el año cuenta y el título entra."""
    t0 = VD.TRANSICION + 0.1
    t1 = t0 + 0.9
    ws = (it["titulo"] or "").split()
    titulo = [{"text": w, "start": round(t1 + 0.1 + 0.12 * k, 3)} for k, w in enumerate(ws)]
    desde, hasta = anios
    ev = [(0.0, "entrada"), (t0, "cuenta"), (t1, "cuenta_fin")] + [(w["start"], "titulo") for w in titulo] + [(CAPITULO_S, "fin")]
    return {"n": n, "tipo": "capitulo", "pagina": "historia", "tuit": None, "plantilla": "capitulo", "enlace": None, "icono": None,
            "chip": None, "dur": CAPITULO_S, "fin_voz": 0.0, "palabras": [], "arriba": None, "acto": None, "secuencia": None,
            "cola": 0.0, "apretado": [], "seguida": False, "sigue": False,
            "H": {"numero": it["numero"], "total": it["total"], "desde": desde, "hasta": hasta, "cuenta": [round(t0, 3), round(t1, 3)],
                  "titulo": titulo, "lugar": ""},
            "T": {"cuenta": [round(t0, 3), round(t1, 3)]}, "transicion": VD.TRANSICIONES["completa"], "quieta": True,
            "eventos": [{"t": round(t, 3), "tipo": k} for t, k in ev], "sfx": [{"t": 0.0, "id": "whoosh"}, {"t": round(t1, 3), "id": "resolucion"}]}


# ---------- el expediente en pantalla (16:9): margen y tablero ----------
MARGEN_TIPOS = ("cita", "golpe", "tarjeta", "explica")   # las escenas que en 16:9 dejaban media pantalla vacía
MARGEN_LLENO = 3                                          # con menos personas, el margen va sobre la última foto borrosa
MARGEN_MIN = 1                                            # personas ya nombradas para que haya margen
MARGEN_CUADROS = 9                                        # cuadritos en el margen (3 × 3)
TABLERO_CUADROS = 12                                      # cuadritos en el rótulo de capítulo (4 × 3)
CAPITULO_TABLERO_S = 3.8                                  # el rótulo con tablero dura un poco más: entran sus personas


def elenco_serie(Y):
    """Las personas de la serie (los `personajes` del encuadre de cada parte que son persona), una vez cada una, con su
    retrato y el foco de su cara: [{nombre, corto, cargo, claves, foto, foco}]."""
    import historia as HI
    fotos = fotos_serie(Y)
    out, vistos = [], set()
    for p_ in Y["partes"]:
        f = os.path.join(RAIZ, p_["trabajo"], "encuadre.json") if p_.get("trabajo") else None
        if not f or not os.path.exists(f):
            continue
        for p in leer(f).get("personajes") or []:
            if not isinstance(p, dict) or not (p.get("nombre") or "").strip() or not HI.es_persona(p):
                continue
            k = VD._plano(p["nombre"])
            if k in vistos:
                continue
            vistos.add(k)
            r = HI.retrato_de_personaje(p, fotos)
            alias = [a for a in p.get("alias") or [] if (a or "").strip() and a[:1].isupper()]
            pal = p["nombre"].split()
            corto = alias[0] if alias else (" ".join(pal[1:]) if len(pal) >= 3 else pal[-1])
            out.append({"nombre": p["nombre"], "corto": corto, "cargo": (p.get("cargo") or p.get("presentacion") or "").strip()[:60],
                        "claves": sorted(set(HI.claves_personaje(p)), key=len, reverse=True),
                        "foto": r[0] if r else None, "foco": r[1] if r else None})
    return out


def nombradas(S, elenco):
    """{índice de la persona: [segundos]}: cuándo la voz de la escena nombra a cada una (nombre o alias)."""
    pal = S.get("palabras") or []
    ws = [VD._plano(w["text"]) for w in pal]
    out, tomadas = {}, set()
    for i, p in enumerate(elenco):
        for c in p["claves"]:
            toks = c.split()
            for j in range(len(ws) - len(toks) + 1):
                if ws[j:j + len(toks)] == toks and not tomadas & set(range(j, j + len(toks))):
                    tomadas |= set(range(j, j + len(toks)))
                    out.setdefault(i, []).append(round(pal[j]["start"], 3))
    return {i: sorted(v) for i, v in out.items()}


def margenes(escenas, Y, caps_n):
    """El expediente del 16:9. A cada escena de MARGEN_TIPOS le pone `margen` (capítulo, los cuadritos de las personas ya
    nombradas en el video, con las que la voz nombra aquí iluminadas a su segundo) y le quita la tarjeta de persona (el
    margen ya dice quién es). A cada rótulo de capítulo, `H.tablero`: los ya vistos atenuados y los que aparecen en ese
    capítulo entrando, unidos por los hilos de las escenas `red` (aristas de hechos verificados, H23). Nada se marca ni
    se tacha: solo se ilumina."""
    elenco = elenco_serie(Y)
    if not elenco:
        return 0
    cuadro = lambda i, **kw: dict({k: elenco[i][k] for k in ("nombre", "corto", "cargo", "foto", "foco")}, **kw)
    # capítulo de cada escena y las menciones por escena
    cap, cap_de, M = 0, [], []
    for S in escenas:
        if S.get("tipo") == "capitulo":
            cap = S["H"]["numero"]
        cap_de.append(max(cap, 1))
        M.append(nombradas(S, elenco))
    primera = {}                       # persona → índice de la escena de su primera mención
    for j, m in enumerate(M):
        for i in m:
            primera.setdefault(i, j)
    idx_nombre = {VD._plano(p["nombre"]): i for i, p in enumerate(elenco)}
    hilos_vistos, vistos, puestos, ult_foto = [], [], 0, None
    for j, S in enumerate(escenas):
        tipo = S.get("tipo")
        if tipo == "capitulo":
            k = S["H"]["numero"]
            nuevos = [i for i in sorted(primera, key=primera.get) if cap_de[primera[i]] == k and i not in vistos]
            orden = (vistos + nuevos)[-TABLERO_CUADROS:]
            t1 = S["H"]["cuenta"][1]
            pers = [cuadro(i, nuevo=i in nuevos, start=round(t1 + 0.25 + 0.22 * nuevos.index(i), 3) if i in nuevos else 0) for i in orden]
            hilos = [[orden.index(a_), orden.index(b_), 0.3] for a_, b_ in hilos_vistos if a_ in orden and b_ in orden]
            if pers:
                S["H"]["tablero"] = {"personas": pers, "hilos": hilos}
                S["dur"] = CAPITULO_TABLERO_S
                S["eventos"] = [x for x in S["eventos"] if x["tipo"] != "fin"] + \
                    [{"t": x["start"], "tipo": "persona"} for x in pers if x["start"]] + [{"t": S["dur"], "tipo": "fin"}]
                S["eventos"].sort(key=lambda x: x["t"])
        if tipo == "red":               # sus aristas valen para los tableros que vienen
            nodos = {n_["id"]: idx_nombre.get(VD._plano(n_.get("nombre") or "")) for n_ in (S.get("G") or {}).get("nodos") or []}
            for ar in (S.get("G") or {}).get("aristas") or []:
                a_, b_ = nodos.get(ar.get("de")), nodos.get(ar.get("a"))
                if a_ is not None and b_ is not None and a_ != b_ and (a_, b_) not in hilos_vistos and (b_, a_) not in hilos_vistos:
                    hilos_vistos.append((a_, b_))
        antes = list(vistos)
        for i in sorted(M[j], key=lambda i: M[j][i][0]):
            if i not in vistos:
                vistos.append(i)
        if tipo == "red" and S.get("pagina") == "red":   # en 16:9 el organigrama dejaba 77 % de fondo liso: el tablero
            S["pagina"] = "tablero"
        if tipo in MARGEN_TIPOS and len(vistos) < MARGEN_LLENO and ult_foto:   # pocas personas aún: la última foto, de fondo
            S["fondo"] = ult_foto
        if S.get("pagina") == "noticia" and (S.get("N") or {}).get("foto"):
            ult_foto = S["N"]["foto"]
        if tipo in MARGEN_TIPOS and len(vistos) >= MARGEN_MIN:   # con menos, el margen quedaría vacío: la escena va centrada
            orden = vistos[-MARGEN_CUADROS:]
            c = next((x for x in caps_n if x["numero"] == cap_de[j]), {})
            S["margen"] = {"capitulo": {"numero": cap_de[j], "total": len(caps_n), "titulo": c.get("titulo") or ""},
                           "personas": [cuadro(i, start=(M[j][i][0] if i not in antes else 0), activo=M[j].get(i, [])) for i in orden]}
            S["eventos"] = sorted((S.get("eventos") or []) + [{"t": t, "tipo": "persona"} for i in M[j] for t in M[j][i][:1]],
                                  key=lambda x: x["t"])
            S["personas"] = []
            puestos += 1
    return puestos


SFX_LARGO_POR_MIN = 6.0                            # el video largo no suena como un Short: ≤ 6 efectos por minuto
SFX_ENTRADA = ("whoosh", "impacto", "grave")       # los de la entrada de una escena
SFX_TIC_CADA_S = 8.0                               # un `tic` cada 8 s como mucho


def ralear_sfx_largo(escenas, total):
    """Los efectos del formato corto, pegados, saturan (138 en 12 min; el mismo whoosh en 34 escenas). En el largo: sin
    efecto de entrada entre dos escenas de la misma parte (solo al cambiar de capítulo o tras una unión), un `tic` cada
    SFX_TIC_CADA_S y, si aún pasa de SFX_LARGO_POR_MIN, fuera los `tic` y `foco` que queden. El «Sígueme» conserva los
    suyos. → (antes, después)."""
    antes = sum(len(S.get("sfx") or []) for S in escenas)
    t, ult_tic = 0.0, -99.0
    for prev, S in zip([None] + escenas, escenas):
        misma = prev is not None and prev.get("tipo") != "capitulo" and S.get("tipo") not in ("capitulo", "cierre") \
            and str(prev.get("origen")).split(".")[0] == str(S.get("origen")).split(".")[0]
        out = []
        for x in S.get("sfx") or []:
            if x.get("seguir"):
                out.append(x)
            elif misma and x["id"] in SFX_ENTRADA and x["t"] <= VD.TRANSICION + 0.5 and not S.get("giro"):
                continue
            elif x["id"] == "tic":
                if t + x["t"] - ult_tic >= SFX_TIC_CADA_S:
                    ult_tic = t + x["t"]
                    out.append(x)
            else:
                out.append(x)
        S["sfx"] = out
        t += S["dur"] - VD.TRANSICION
    tope = int(SFX_LARGO_POR_MIN * total / 60)
    for quitar in ("tic", "foco"):
        for S in escenas:
            if sum(len(S_.get("sfx") or []) for S_ in escenas) <= tope:
                break
            S["sfx"] = [x for x in S["sfx"] if x["id"] != quitar or x.get("seguir")]
    return antes, sum(len(S.get("sfx") or []) for S in escenas)


def huellas_escenas(escenas):
    """{n: huella} de lo que se dibuja en cada escena (su entrada de escenas.json entera): si no cambia, su clip sirve."""
    import hashlib
    fuera = ("transicion", "sfx", "n")   # la transición y los efectos son del montaje; el número cambia si entra o sale una escena
    return {S["n"]: hashlib.sha1(json.dumps({k: v for k, v in S.items() if k not in fuera}, sort_keys=True,
                                            ensure_ascii=False).encode("utf-8")).hexdigest()[:16] for S in escenas}


def transiciones_con_sentido(escenas, por_id, hechos):
    """En vez del fundido genérico entre escenas pegadas, la transición dice algo de la historia (nunca va por reloj):
    un documento entra como una hoja que se pone encima (coverup); si el año de los hechos avanza, la escena empuja
    hacia la izquierda, y si retrocede, hacia la derecha. Lo demás conserva su transición. Devuelve cuántas cambió."""
    def anio(S):
        ids = (por_id.get(S.get("origen")) or {}).get("hechos") or []
        ys = [int(m.group(0)) for h in ids for m in [re.match(r"\d{4}", str((hechos.get(h) or {}).get("fecha") or ""))] if m]
        return max(ys) if ys else None
    ult, n = (anio(escenas[0]) if escenas else None), 0
    for prev, S in zip(escenas, escenas[1:]):
        a = anio(S)
        generica = S.get("transicion") == VD.TRANSICIONES["seguida"] and S.get("tipo") not in ("cierre", "capitulo") \
            and prev.get("tipo") != "capitulo"
        if generica and (S.get("H") or {}).get("documento"):
            S["transicion"], n = "coverup", n + 1
        elif generica and a and ult and a != ult:
            S["transicion"], n = VD.TRANSICIONES["avanza" if a > ult else "retrocede"], n + 1
        ult = a or ult
    return n


def anio_de(p):
    s = str(p or "")
    m = re.search(r"(1[89]\d\d|20\d\d)", s)
    return m.group(1) if m else None


RE_KICKER_SERIE = re.compile(r"^\s*serie\b", re.I)


def sin_kicker_serie(ctx):
    """m116 (YT2): el kicker «Serie · <tema>» es marca del formato corto; en el video largo no va (golpe, cierre, escenario)."""
    return "" if RE_KICKER_SERIE.match(ctx or "") else (ctx or "")


def cmd_armar(a):
    trabajo = os.path.abspath(a.trabajo)
    Y, partes, por_id, S_de = cargar_contexto(trabajo)
    M = leer(os.path.join(trabajo, "montaje.json"))
    f, _, items, _ = revisar_montaje(M, Y, list(por_id.values()), S_de, partes)
    if f and not getattr(a, "sin_gate", False):
        for x in f:
            print("FALLA", x)
        return falla("el montaje no pasa YT1–YT8")
    nv = os.path.join(trabajo, "nuevas")
    nuevas = piezas_nuevas(items)
    E_nv = {}
    if nuevas:
        if not os.path.exists(os.path.join(nv, "escenas.json")):
            return falla("faltan los tiempos de la voz nueva: youtube.py voz y youtube.py tiempos")
        E_nv = {S["n"]: S for S in leer(os.path.join(nv, "escenas.json"))["escenas"]}
        loc_nv = leer(os.path.join(nv, "locucion.json"))
        textos = [x["voz"] for x in loc_nv["escenas"]]
        esperados = [voz_nueva(it["texto"])[1] for it, _ in nuevas]
        if textos != esperados:
            return falla("la voz nueva no corresponde al montaje (cambió después de youtube.py voz): vuelve a correr voz y tiempos")
    candado = os.path.join(trabajo, ".grabando")
    if os.path.exists(candado):   # armar borra los clips: nunca mientras se graba
        try:
            os.kill(int(open(candado).read().strip()), 0)
            return falla("hay una grabación en curso en este TRABAJO (%s): espera a que termine o detenla" % rel(candado))
        except (OSError, ValueError):
            os.remove(candado)
    # un retoque ya no obliga a regrabar todo (60–120 min): los clips se conservan y, al final, se borra solo el de cada
    # escena cuyo contenido cambió (huellas_escenas); `armar --todo` los borra todos (cambió una página de video/)
    f_esc = os.path.join(trabajo, "escenas.json")
    huellas_antes = huellas_escenas(leer(f_esc)["escenas"]) if os.path.exists(f_esc) and not getattr(a, "todo", False) else {}
    for d in ("audio", "base", "segs_16x9") + (() if huellas_antes else ("clips_16x9",)):
        shutil.rmtree(os.path.join(trabajo, d), ignore_errors=True)
    os.makedirs(os.path.join(trabajo, "audio"), exist_ok=True)
    os.makedirs(os.path.join(trabajo, "base"), exist_ok=True)
    for fid, r in fotos_serie(Y).items():
        enlazar(os.path.join(RAIZ, r["_trabajo"], r["archivo"]), os.path.join(trabajo, r["archivo"]))
        js = os.path.join(RAIZ, r["_trabajo"], "fotos", fid + ".json")
        if os.path.exists(js):
            enlazar(js, os.path.join(trabajo, "fotos", fid + ".json"))
    por_parte = {P["n"]: P for P in partes}
    k_nueva = {id(it): n for it, n in nuevas}
    escenas, n, ult_carta = [], 0, {}
    cap_anio = {}
    for p in Y["partes"]:
        per = p.get("periodo") or {}
        cap_anio[p["n"]] = (anio_de(per.get("desde")), anio_de(per.get("hasta")))
    t_global = 0.0
    for it in items:
        n += 1
        if it["k"] == "capitulo":
            S = escena_capitulo(it, n, cap_anio.get(it["parte"], (None, None)))
            silencio(os.path.join(trabajo, "audio", "voz_%d_r.mp3" % n), 0.2)
        elif it["k"] in ("puente", "promesa") or it.get("op") == "revozar":
            j = k_nueva[id(it)]
            S = copy.deepcopy(E_nv[j])
            S["acto"] = None
            S.pop("R", None)
            enlazar(os.path.join(nv, "audio", "voz_%d_r.mp3" % j), os.path.join(trabajo, "audio", "voz_%d_r.mp3" % n))
        else:
            P = por_parte[it["parte"]]
            S0 = S_de[(it["parte"], it["n"])]
            S = recortar_escena(S0, it.get("cortes") or [])
            recortar_audio(os.path.join(P["trabajo"], "audio", "voz_%d_r.mp3" % it["n"]),
                           os.path.join(trabajo, "audio", "voz_%d_r.mp3" % n), it.get("cortes") or [])
            if S.get("tuit"):
                nuevo = it["parte"] * 100 + S["tuit"]
                for ext in (".html", ".png"):
                    src = os.path.join(P["trabajo"], "base", "tuit_%d%s" % (S["tuit"], ext))
                    if os.path.exists(src):
                        enlazar(src, os.path.join(trabajo, "base", "tuit_%d%s" % (nuevo, ext)))
                S["tuit"] = nuevo
            if S.get("toma"):
                tid = S["toma"].get("id")
                src = os.path.join(P["trabajo"], "tomas")
                for nombre in (tid, tid + ".wav", tid + ".json"):
                    s_ = os.path.join(src, nombre)
                    d_ = os.path.join(trabajo, "tomas", nombre)
                    if os.path.isdir(s_) and not os.path.exists(d_):
                        shutil.copytree(s_, d_, copy_function=os.link)
                    elif os.path.isfile(s_):
                        enlazar(s_, d_)
            if S.get("tipo") == "gancho":
                S["chip"] = None
            if S.get("tipo") == "cierre":   # el cierre de la última parte: la pantalla final de YouTube
                S["dur"] = round(S["dur"] + FINAL_EXTRA_S, 3)
                S["eventos"] = [x for x in S["eventos"] if x["tipo"] != "fin"] + [{"t": S["dur"], "tipo": "fin"}]
        # la tarjeta de persona: una vez, y otra solo si pasaron ≥ 5 min (recordar quién es). Las dibuja comun.js desde
        # S.personas (S.P son los pasos de una escena explica)
        if isinstance(S.get("personas"), list):
            quedan = []
            for c in S["personas"]:
                if c["nombre"] in ult_carta and t_global - ult_carta[c["nombre"]] < RECORDATORIO_S:
                    continue
                ult_carta[c["nombre"]] = t_global
                quedan.append(c)
            S["personas"] = quedan
        S["n"] = n
        S["origen"] = "adelanto" if it["k"] == "adelanto" else it.get("ref") or it["k"]
        if it["k"] == "adelanto":   # un corte seco de entrada, sin rótulo de acto ni chip: es un destello antes del gancho
            S.pop("R", None)
            S["chip"] = None
            S["acto"] = None
        if n == 1:
            S["transicion"] = None
        elif not S.get("transicion"):
            S["transicion"] = VD.TRANSICIONES["seguida"]
        escenas.append(S)
        t_global += S["dur"] - VD.TRANSICION
    # la seguida/sigue de las secuencias solo vale entre escenas vecinas de la misma parte que siguen pegadas
    for a_, b_ in zip(escenas, escenas[1:]):
        if a_["origen"].split(".")[0] != b_["origen"].split(".")[0] or not a_.get("sigue") or not b_.get("seguida"):
            a_["sigue"] = False
            b_["seguida"] = False
    E1 = partes[0]["E"]
    Eu = partes[-1]["E"]
    # P6: la pregunta en pantalla es la del video entero (la promesa global), no la de cada parte
    prm = M.get("promesa") or {}
    for S in escenas:
        S.pop("pregunta", None)
        S["eventos"] = [x for x in S.get("eventos") or [] if x.get("tipo") != "pregunta"]
        q_en = {"promesa": ("promesa", 0.6), prm.get("pago"): ("pago", 0.9)}.get(S.get("origen"))
        if (prm.get("pregunta") or "").strip() and q_en and S.get("tipo") != "cierre":
            S["pregunta"] = {"texto": prm["pregunta"].strip(), "desde": q_en[1], "pagada": q_en[0] == "pago",
                             "dur": round(min(VD.PREGUNTA_S[q_en[0]], S["dur"] - VD.TRANSICION - 0.3 - q_en[1]), 3)}
    n_tr = transiciones_con_sentido(escenas, por_id, hechos_serie(Y))
    print("transiciones: %d con sentido (cambio de año o documento) en vez del fundido" % n_tr)
    caps_n = [{"numero": it["numero"], "titulo": it["titulo"]} for it in [x.get("cap1") for x in items if x.get("cap1")] + items
              if it and it["k"] == "capitulo"]
    n_marg = margenes(escenas, Y, caps_n)
    if n_marg:
        print("expediente: %d escenas con margen · tablero en %d rótulos de capítulo"
              % (n_marg, sum(1 for S in escenas if (S.get("H") or {}).get("tablero"))))
    total = round(sum(S["dur"] for S in escenas) - VD.TRANSICION * (len(escenas) - 1), 2)
    # el «Sígueme» de la mitad es del video largo, no el que traía cada parte (V25)
    for x in VD.marcar_seguir(escenas, total - FINAL_EXTRA_S):
        print("AVISO", x)
    print("efectos: %d → %d (formato largo)" % ralear_sfx_largo(escenas, total))
    escribir(os.path.join(trabajo, "escenas.json"), {
        "version": 2, "formato": FORMATO_GRABAR, "colores": E1.get("colores"), "contexto_superior": sin_kicker_serie(E1.get("contexto_superior")),
        "redes": E1.get("redes"), "serie": None, "gancho": E1.get("gancho"), "pago": {"n": None, "t": None},
        "cierre": dict(Eu.get("cierre") or {}, invitacion=None), "transicion_s": VD.TRANSICION, "total_s": total,
        "tipo": "historia", "escenas": escenas})
    if huellas_antes:
        # cada clip se reusa por su contenido, aunque la escena haya cambiado de número (entró o salió otra antes)
        ahora, cambian = huellas_escenas(escenas), []
        cd = os.path.join(trabajo, "clips_16x9")
        por_huella = {}
        for n_viejo, h in huellas_antes.items():
            if os.path.exists(os.path.join(cd, "e%d.mp4" % n_viejo)):
                por_huella.setdefault(h, n_viejo)
        tmp = os.path.join(cd, ".reuso")
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        for S in escenas:
            n_viejo = por_huella.pop(ahora[S["n"]], None)
            if n_viejo is not None:
                os.replace(os.path.join(cd, "e%d.mp4" % n_viejo), os.path.join(tmp, "e%d.mp4" % S["n"]))
            else:
                cambian.append(S["n"])
        for f in glob.glob(os.path.join(cd, "e*.mp4")):   # lo que no se reusó ya no corresponde a ninguna escena
            os.remove(f)
        for f in glob.glob(os.path.join(tmp, "e*.mp4")):
            os.replace(f, os.path.join(cd, os.path.basename(f)))
        os.rmdir(tmp)
        print("clips: %d escenas cambiaron y se vuelven a grabar (%s); las demás se conservan"
              % (len(cambian), ", ".join(map(str, cambian))[:200] or "ninguna"))
    st = leer(os.path.join(P1_de(Y), "video.json"))
    st.update({"hilo": rel(os.path.join(trabajo, "base")), "serie": None, "formato": "youtube", "objetivo_s": int(total),
               "musica": Y.get("musica") or st.get("musica"), "paleta": Y.get("paleta") or st.get("paleta")})
    escribir(os.path.join(trabajo, "video.json"), st)
    caps = capitulos_de([dict(it, t=t_de(escenas, j)) for j, it in enumerate(items)], total + FINAL_EXTRA_S * 0)
    escribir(os.path.join(trabajo, "capitulos.json"), {"total_s": total, "capitulos": caps})
    # la maqueta va con voz falsa (tonos): whisper no oye palabras y YT6 fallaría siempre
    f_es, av_es = ([], ["YT6 maqueta con voz falsa: sin escucha de los recortes"]) if Y.get("fixture") else \
        escuchar_recortes(trabajo, [(j + 1, it["texto"], it["ref"]) for j, it in enumerate(items) if it.get("recortado")])
    for x in av_es:
        print("AVISO", x)
    print("armado: %d escenas · %s (%.1f min) · %d capítulos → %s" % (len(escenas), mmss(total), total / 60, len(caps),
                                                                     rel(os.path.join(trabajo, "escenas.json"))))
    for c_ in caps:
        print("  %s %s" % (mmss(c_["t"]), c_["titulo"]))
    for x in f_es:
        print("FALLA", x)
    return 1 if f_es else 0


def escuchar_recortes(trabajo, pares):
    """YT6 con whisper.cpp (si está): cada escena recortada se oye entera y se compara con el texto que queda; un corte
    que se come una palabra baja la coincidencia. → (fallas, avisos)."""
    import difflib
    modelo = VD.modelo_whisper()
    if not pares or not shutil.which("whisper-cli") or not os.path.exists(modelo):
        return [], (["YT6 sin whisper-cli o sin modelo (make whisper): oye a mano las escenas recortadas"] if pares else [])
    f, av = [], []
    for n, texto, ref in pares:
        wav = os.path.join(trabajo, "segs_16x9", "escucha_%d.wav" % n)
        os.makedirs(os.path.dirname(wav), exist_ok=True)
        VD.ff("-i", os.path.join(trabajo, "audio", "voz_%d_r.mp3" % n), "-ar", "16000", "-ac", "1", wav)
        oido = subprocess.run(["whisper-cli", "-m", modelo, "-l", "es", "-nt", "-f", wav], capture_output=True, text=True).stdout
        a = [norm_w(w) for w in plano(texto).split() if norm_w(w)]
        b = [norm_w(w) for w in plano(oido).split() if norm_w(w)]
        r = difflib.SequenceMatcher(None, a, b).ratio()
        if r < 0.8:
            f.append("YT6 %s (E%d) recortada: whisper oye «%s» (coincide %.0f %%): el corte se come algo; corta en otro silencio o usa revozar"
                     % (ref, n, oido.strip()[:90], 100 * r))
        elif r < 0.9:
            av.append("YT6 %s (E%d) recortada coincide %.0f %% con lo que oye whisper: óyela" % (ref, n, 100 * r))
    return f, av


def P1_de(Y):
    return os.path.join(RAIZ, Y["partes"][0]["trabajo"])


def t_de(escenas, j):
    return sum(S["dur"] - VD.TRANSICION for S in escenas[:j])


# ---------- grabar y montar (YT9) ----------
# YT12 ocupación (2026-11-10): con el panel lateral, las escenas de más de 70 % de fondo liso bajaron de 22 a 3 de 69 en
# La Línea. Una escena de más de 4 s (no el rótulo ni el cierre, cuya mitad derecha es de la pantalla final de YouTube)
# no pasa de ese 70 %. Se mide en el cuadro al 60 % de la escena: celdas de 8×6 px (de 96×54) casi sin variación y del
# tono del fondo.
OCUPACION_MAX = 0.70
OCUPACION_DESDE = "2026-11-10"   # un largo empezado antes recibe aviso


def vacio_de(clip, t, W=96, H=54):
    """Fracción del cuadro que es fondo liso, en el segundo t del clip (o None si no se pudo leer)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.2f" % t, "-i", clip, "-frames:v", "1", "-vf",
                        "scale=%d:%d,format=gray" % (W, H), "-f", "rawvideo", "-"], capture_output=True)
    px = list(r.stdout)
    if len(px) != W * H:
        return None
    fondo = sorted(px)[len(px) // 2]
    lisas = tot = 0
    for cy in range(0, H, 6):
        for cx in range(0, W, 8):
            c = [px[y * W + x] for y in range(cy, min(H, cy + 6)) for x in range(cx, min(W, cx + 8))]
            tot += 1
            lisas += max(c) - min(c) <= 10 and abs(sum(c) / len(c) - fondo) <= 10
    return lisas / tot


def revisar_ocupacion(trabajo, Y):
    """YT12 sobre los clips grabados → (fallas, avisos); escribe revision/ocupacion_16x9.json."""
    E = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    out, malas = [], []
    for S in E:
        clip = os.path.join(trabajo, "clips_16x9", "e%d.mp4" % S["n"])
        if S.get("tipo") in ("capitulo", "cierre") or S["dur"] <= 4 or not os.path.exists(clip):
            continue
        v = vacio_de(clip, S["dur"] * 0.6)
        if v is None:
            continue
        out.append({"n": S["n"], "tipo": S.get("tipo"), "origen": S.get("origen"), "vacio": round(v, 2), "margen": bool(S.get("margen"))})
        if v > OCUPACION_MAX:
            malas.append("YT12 E%d (%s, %s): %.0f %% del cuadro es fondo liso (máximo %.0f %%): que la escena llene el 16:9 "
                         "(margen, foto de fondo, el tablero en vez del organigrama)" % (S["n"], S.get("tipo"), S.get("origen"),
                                                                                         100 * v, 100 * OCUPACION_MAX))
    os.makedirs(os.path.join(trabajo, "revision"), exist_ok=True)
    escribir(os.path.join(trabajo, "revision", "ocupacion_16x9.json"), {"maximo": OCUPACION_MAX, "escenas": out})
    if out:
        print("YT12 ocupación: mediana de fondo liso %.0f %% · %d de %d escenas pasan de %.0f %%" % (
            100 * sorted(x["vacio"] for x in out)[len(out) // 2], len(malas), len(out), 100 * OCUPACION_MAX))
    nuevo = str(Y.get("fecha") or OCUPACION_DESDE) >= OCUPACION_DESDE
    return (malas, []) if nuevo else ([], malas)


def cmd_grabar(a):
    trabajo = os.path.abspath(a.trabajo)
    args = ["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, "--hilo", os.path.join(trabajo, "base"),
            "--fps", str(a.fps), "--formato", FORMATO_GRABAR]
    solo = a.solo
    if not solo:   # sin --solo: solo las escenas que no tienen clip (las que `armar` marcó como cambiadas)
        ns = [S["n"] for S in leer(os.path.join(trabajo, "escenas.json"))["escenas"]]
        faltan = [n for n in ns if not os.path.exists(os.path.join(trabajo, "clips_16x9", "e%d.mp4" % n))]
        if not faltan:
            print("grabar: los %d clips ya están al día" % len(ns))
            return 0
        if len(faltan) < len(ns):
            solo = ",".join(map(str, faltan))
            print("grabar: %d de %d escenas (las demás conservan su clip)" % (len(faltan), len(ns)))
    if solo:
        args += ["--solo", solo]
    if a.paralelo:
        args += ["--paralelo", str(a.paralelo)]
    candado = os.path.join(trabajo, ".grabando")
    open(candado, "w").write(str(os.getpid()))
    try:
        rc = subprocess.run(args, cwd=RAIZ).returncode
    finally:
        os.remove(candado) if os.path.exists(candado) else None
    if rc == 3:
        return falla("YT9 algo visible sale de los márgenes del 16:9 (revision/zona_16x9.json): corrige la página y vuelve a grabar")
    if rc:
        return falla("la grabación falló")
    f12, av12 = revisar_ocupacion(trabajo, estado_y(trabajo))
    for x in av12:
        print("AVISO", x)
    for x in f12:
        print("FALLA", x)
    return 1 if f12 else 0


def pistas_paleta(Y):
    cat = leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
    base = Y.get("musica")
    # la música va por TEMA (H8m): con `musica_tema`, todas las pistas de ese tema (la de la serie primero) alternan por
    # capítulo; dos pistas de la paleta repetidas siete veces cansan en 12 minutos
    if Y.get("musica_tema"):
        fam = [p for p in cat if Y["musica_tema"] in (p.get("temas") or [])]
        fam.sort(key=lambda p: (p["id"] != base, p["id"]))
        if len(fam) > 1:
            return fam
    pal = next((p["paleta"] for p in cat if p["id"] == base), Y.get("paleta"))
    ids = [base] + [p["id"] for p in cat if p.get("paleta") == pal and p["id"] != base]
    return [next(p for p in cat if p["id"] == i) for i in ids if any(p["id"] == i for p in cat)]


def musica_por_capitulo(Y, caps, total, segs):
    """La música del video: una pista por capítulo, alternando las de la paleta, fundidas 2 s en cada rótulo."""
    pistas = pistas_paleta(Y)
    trozos = []
    for j, c in enumerate(caps):
        t0 = c["t"]
        t1 = caps[j + 1]["t"] if j + 1 < len(caps) else total
        p = pistas[j % len(pistas)]
        out = os.path.join(segs, "musica_%d.wav" % (j + 1))
        VD.musica_bucle(os.path.join(RAIZ, "design", "musica", p["archivo"]), (t1 - t0) + 2.0, out)
        trozos.append(out)
    fondo = os.path.join(segs, "musica.wav")
    if len(trozos) == 1:
        shutil.copy(trozos[0], fondo)
        return fondo, [pistas[0]["id"]]
    fc, prev = "", "[0:a]"
    for i in range(1, len(trozos)):
        out = "[m%d]" % i
        fc += "%s[%d:a]acrossfade=d=2:c1=tri:c2=tri%s;" % (prev, i, out)
        prev = out
    fc += "%satrim=0:%.3f[m]" % (prev, total)
    VD.ff(*sum([["-i", x] for x in trozos], []), "-filter_complex", fc, "-map", "[m]", "-ar", "48000", fondo)
    return fondo, [pistas[j % len(pistas)]["id"] for j in range(len(caps))]


def video_por_tramos(E, clips, durs, offs, segs):
    """Las escenas encadenadas con su transición (xfade), por tramos de TRAMO_ESCENAS escenas que luego se unen con la
    transición de la primera escena de cada tramo: el mismo resultado que una sola cadena, sin un filtergraph de 120
    entradas."""
    TR = E.get("transicion_s", VD.TRANSICION)
    n = len(clips)
    cortes = list(range(0, n, TRAMO_ESCENAS))
    tramos = []
    for k, i0 in enumerate(cortes):
        i1 = min(n, i0 + TRAMO_ESCENAS)
        out = os.path.join(segs, "tramo_%02d.mp4" % (k + 1))
        if i1 - i0 == 1:
            shutil.copy(clips[i0], out)
        else:
            fc, prev = "", "[0:v]"
            for j in range(1, i1 - i0):
                tr = E["escenas"][i0 + j].get("transicion") or VD.TRANSICIONES["tarjeta"]
                fc += "%s[%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d];" % (prev, j, tr, TR, offs[i0 + j] - offs[i0], j)
                prev = "[x%d]" % j
            VD.ff(*sum([["-i", c] for c in clips[i0:i1]], []), "-filter_complex", fc.rstrip(";"), "-map", prev, "-an",
                  "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium", out)
        tramos.append((out, i0))
    video_solo = os.path.join(segs, "voz_video.mp4")
    if len(tramos) == 1:
        shutil.copy(tramos[0][0], video_solo)
        return video_solo
    fc, prev = "", "[0:v]"
    for j in range(1, len(tramos)):
        i0 = tramos[j][1]
        tr = E["escenas"][i0].get("transicion") or VD.TRANSICIONES["tarjeta"]
        fc += "%s[%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f[t%d];" % (prev, j, tr, TR, offs[i0], j)
        prev = "[t%d]" % j
    VD.ff(*sum([["-i", x] for x, _ in tramos], []), "-filter_complex", fc.rstrip(";"), "-map", prev, "-an",
          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium", video_solo)
    return video_solo


def mezclar_voz(trabajo, E, offs, D, segs):
    """Todas las voces (y el audio original de una toma) en una pista, por lotes de 40 entradas."""
    voces = [(os.path.join(trabajo, "audio", "voz_%d_r.mp3" % e["n"]), o) for e, o in zip(E["escenas"], offs)]
    for e, o in zip(E["escenas"], offs):
        if (e.get("toma") or {}).get("wav"):
            voces.append((os.path.join(trabajo, e["toma"]["wav"]), o + e["toma"]["t"]))
    lotes = []
    for k in range(0, len(voces), 40):
        grupo = voces[k:k + 40]
        fc = "".join("[%d:a]aresample=48000,aformat=channel_layouts=stereo,adelay=%s:all=1[v%d];" % (i, VD.muestras(o), i)
                     for i, (_, o) in enumerate(grupo))
        fc += "".join("[v%d]" % i for i in range(len(grupo))) + "amix=inputs=%d:duration=longest:normalize=0,apad=whole_dur=%.3f[vz]" % (len(grupo), D)
        out = os.path.join(segs, "voz_%d.wav" % (k // 40 + 1))
        VD.ff(*sum([["-i", v] for v, _ in grupo], []), "-filter_complex", fc, "-map", "[vz]", "-ar", "48000", out)
        lotes.append(out)
    voz = os.path.join(segs, "voz.wav")
    if len(lotes) == 1:
        shutil.copy(lotes[0], voz)
    else:
        VD.ff(*sum([["-i", x] for x in lotes], []), "-filter_complex",
              "".join("[%d:a]" % i for i in range(len(lotes))) + "amix=inputs=%d:duration=longest:normalize=0,atrim=0:%.3f[vz]" % (len(lotes), D),
              "-map", "[vz]", "-ar", "48000", voz)
    return voz


def srt(E, offs, salida):
    open(salida, "w", encoding="utf-8").write(VD.texto_srt(E["escenas"], offs))


def cmd_montar(a):
    trabajo = os.path.abspath(a.trabajo)
    Y = estado_y(trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))
    segs = os.path.join(trabajo, "segs_16x9")
    os.makedirs(segs, exist_ok=True)
    sal = os.path.join(trabajo, "salida")
    os.makedirs(sal, exist_ok=True)
    clips = [os.path.join(trabajo, "clips_16x9", "e%d.mp4" % e["n"]) for e in E["escenas"]]
    falta = [c for c in clips if not os.path.exists(c)]
    if falta:
        return falla("faltan clips (youtube.py grabar): %s" % ", ".join(rel(x) for x in falta[:5]))
    durs = [VD.ffprobe_dur(c) for c in clips]
    TR = E.get("transicion_s", VD.TRANSICION)
    offs, off = [], 0.0
    for k, d in enumerate(durs):
        offs.append(off)
        off += d - (TR if k < len(durs) - 1 else 0.0)
    D = off
    video_solo = video_por_tramos(E, clips, durs, offs, segs)
    D = VD.ffprobe_dur(video_solo)
    voz = mezclar_voz(trabajo, E, offs, D, segs)
    gv = VD.VOZ_LUFS - VD.medir(voz)["input_i"]
    caps_t = [{"t": offs[i]} for i, e in enumerate(E["escenas"]) if e["tipo"] == "capitulo"]
    primero = next((e for e in E["escenas"] if e["tipo"] == "capitulo"), None)
    if not caps_t or (primero["H"].get("numero") or 1) != 1:   # sin rótulo del capítulo 1: empieza en 0:00
        caps_t.insert(0, {"t": 0.0})
    caps_t[0]["t"] = 0.0
    fondo, pistas = musica_por_capitulo(Y, caps_t or [{"t": 0.0}], D, segs)
    cat = {x["id"]: x for x in leer(os.path.join(VD.SFX_DIR, "catalogo.json"))["efectos"]}
    efectos = sorted((o + s["t"], s["id"]) for e, o in zip(E["escenas"], offs) for s in e.get("sfx") or [] if o + s["t"] >= 0 and s["id"] in cat)
    # la voz y la música con ducking; los efectos, en lotes (cada uno con su retraso) sumados aparte
    fx = os.path.join(segs, "efectos.wav")
    if efectos:
        lotes = []
        for k in range(0, len(efectos), 40):
            grupo = efectos[k:k + 40]
            fc = "".join("[%d:a]aformat=channel_layouts=stereo,aresample=48000,adelay=%s:all=1,volume=%ddB[f%d];" % (
                j, VD.muestras(t), cat[i]["ganancia_db"], j) for j, (t, i) in enumerate(grupo))
            fc += "".join("[f%d]" % j for j in range(len(grupo))) + "amix=inputs=%d:duration=longest:normalize=0,apad=whole_dur=%.3f[a]" % (len(grupo), D)
            out = os.path.join(segs, "efectos_%d.wav" % (k // 40 + 1))
            VD.ff(*sum([["-i", os.path.join(VD.SFX_DIR, cat[i]["archivo"])] for _, i in grupo], []), "-filter_complex", fc, "-map", "[a]",
                  "-ar", "48000", out)
            lotes.append(out)
        VD.ff(*sum([["-i", x] for x in lotes], []), "-filter_complex",
              "".join("[%d:a]" % i for i in range(len(lotes))) + "amix=inputs=%d:duration=longest:normalize=0,atrim=0:%.3f[a]" % (len(lotes), D),
              "-map", "[a]", "-ar", "48000", fx)
    else:
        VD.ff("-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "%.3f" % D, fx)
    fc = ("[0:a]volume=%.2fdB,asplit=2[v][k];"
          "[1:a]aformat=channel_layouts=stereo,volume=%s,afade=t=in:st=0:d=1,afade=t=out:st=%.2f:d=4[m0];"
          "[m0][k]sidechaincompress=%s[m];[v][m][2:a]amix=inputs=3:duration=first:normalize=0[a]" % (gv, VD.MUSICA_VOLUMEN, D - 4, VD.DUCK))
    mezcla = os.path.join(segs, "mezcla.wav")
    VD.ff("-i", voz, "-i", fondo, "-i", fx, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", mezcla)
    m1 = VD.medir(mezcla)
    video = os.path.join(sal, "video.mp4")
    filtro = ("[1:a]loudnorm=I=%s:TP=-1.5:LRA=11:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:measured_thresh=%.2f:offset=%.2f:linear=true%s[a]")
    datos = (VD.LUFS, m1["input_i"], m1["input_tp"], m1["input_lra"], m1["input_thresh"], m1["target_offset"])
    VD.ff("-i", video_solo, "-i", mezcla, "-filter_complex", filtro % (datos + ("",)), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", video)
    mf = VD.medir(video)
    if mf["input_tp"] > VD.TP_MAX:
        print("AVISO YT9 pico %.1f dBTP: se rehace la pista con limitador" % mf["input_tp"])
        VD.ff("-i", video_solo, "-i", mezcla, "-filter_complex", filtro % (datos + (",alimiter=limit=0.79:level=false",)), "-map", "0:v",
              "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", video)
        mf = VD.medir(video)
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", video],
                                   capture_output=True, text=True).stdout)["streams"]
    v = next((s_ for s_ in pr if s_["codec_type"] == "video"), {})
    fallas = []
    if (v.get("width"), v.get("height")) != (1920, 1080):
        fallas.append("YT9 tamaño %sx%s (se espera 1920×1080)" % (v.get("width"), v.get("height")))
    if not any(s_["codec_type"] == "audio" for s_ in pr):
        fallas.append("YT9 sin audio")
    if abs(mf["input_i"] - VD.LUFS) > VD.LUFS_TOL or mf["input_tp"] > VD.TP_MAX:
        fallas.append("YT9 sonoridad %.1f LUFS / %.1f dBTP (se espera %.0f ±%.1f, ≤ %.0f)" % (mf["input_i"], mf["input_tp"], VD.LUFS, VD.LUFS_TOL, VD.TP_MAX))
    srt(E, offs, os.path.join(sal, "subtitulos.srt"))
    # los capítulos reales (desplazamientos de los clips grabados) para la descripción de YouTube
    caps = leer(os.path.join(trabajo, "capitulos.json"))
    reales = {e["H"].get("numero"): o for e, o in zip(E["escenas"], offs) if e["tipo"] == "capitulo"}
    for c_ in caps["capitulos"]:
        c_["t"] = 0.0 if c_["numero"] == 1 else round(reales.get(c_["numero"], c_["t"]), 2)
    caps["total_s"] = round(D, 2)
    caps["musica"] = pistas
    escribir(os.path.join(trabajo, "capitulos.json"), caps)
    print("video 16:9 %s (%.1f min) · %.1f LUFS · %.1f dBTP · música %s → %s" % (mmss(D), D / 60, mf["input_i"], mf["input_tp"],
                                                                              " / ".join(sorted(set(pistas))), rel(video)))
    for x in fallas:
        print("FALLA", x)
    return 1 if fallas else 0


# ---------- miniatura (YT10) y entrega (YT11) ----------
TITULO_YT = 100           # YouTube: ≤ 100 caracteres
DESCRIPCION_YT = 5000     # YouTube: ≤ 5000 caracteres


def cmd_miniatura(a):
    trabajo = os.path.abspath(a.trabajo)
    ruta = os.path.join(trabajo, "escenas.json")
    E = leer(ruta)
    Y = estado_y(trabajo)
    fotos = fotos_serie(Y)
    if a.foto and a.foto not in fotos:
        return falla("la foto %s no es de la serie" % a.foto)
    if len((a.texto or "").split()) > 5:
        return falla("YT10 la miniatura lleva ≤ 5 palabras")
    if a.cifra:
        vals = valores_de(Y)
        sin = VD.sin_respaldo(a.cifra, vals) if vals else []
        if sin:
            return falla("YT10 la cifra de la miniatura no tiene respaldo en los datos de la serie: %s" % ", ".join(map(str, sin)))
    fo = fotos.get(a.foto) or {}
    E["miniatura"] = {"texto": a.texto.strip(), "cifra": (a.cifra or "").strip() or None, "chip": (a.chip or "").strip() or None,
                      "foto": fo.get("archivo"), "focos": [f for f in fo.get("focos") or [] if f.get("que") == "rostro"]}
    escribir(ruta, E)
    sal = os.path.join(trabajo, "salida")
    os.makedirs(sal, exist_ok=True)
    nombre = "miniatura%s" % ("_" + a.nombre if a.nombre else "")
    grande = os.path.join(trabajo, "segs_16x9", nombre + "_1920.png")
    os.makedirs(os.path.dirname(grande), exist_ok=True)
    lista = os.path.join(trabajo, "segs_16x9", "miniatura.json")
    escribir(lista, [{"nombre": nombre, "pagina": "miniatura", "archivo": grande}])
    rc = subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, "--hilo", os.path.join(trabajo, "base"),
                         "--formato", FORMATO_GRABAR, "--portadas", lista], cwd=RAIZ).returncode
    if rc:
        return falla("YT10 la miniatura no se pudo dibujar (ver el error de la página)")
    final = os.path.join(sal, nombre + ".png")
    VD.ff("-i", grande, "-vf", "scale=1280:720:flags=lanczos", final)
    chica = os.path.join(trabajo, "segs_16x9", nombre + "_320.png")
    VD.ff("-i", grande, "-vf", "scale=320:180:flags=lanczos", chica)
    print("miniatura 1280×720 → %s (y a 320×180 para revisar: %s)" % (rel(final), rel(chica)))
    # YT10 variantes: para «Probar y comparar» tienen que ser distintas de verdad (otra foto) y el texto no repite el título
    reg_f = os.path.join(trabajo, "miniaturas.json")
    reg = leer(reg_f) if os.path.exists(reg_f) else {}
    reg[nombre] = {"foto": a.foto, "texto": a.texto.strip(), "cifra": (a.cifra or "").strip() or None}
    escribir(reg_f, reg)
    if len(reg) >= 2 and len({v.get("foto") for v in reg.values()}) < 2:
        print("AVISO YT10 las %d miniaturas usan la misma foto (%s): una prueba A/B compara fotos distintas (otra cara, otro "
              "momento)" % (len(reg), a.foto))
    mj = os.path.join(trabajo, "montaje.json")
    titulo = ((leer(mj).get("youtube") or {}).get("titulo") or "") if os.path.exists(mj) else ""
    propias = lambda t: {w for w in VD._plano(t).split() if len(w) > 3}
    if propias(a.texto) and propias(a.texto) <= propias(titulo):
        print("AVISO YT10 el texto de la miniatura («%s») repite el título: que diga lo que el título no dice" % a.texto.strip())
    return 0


TEASER_S = (12.0, 26.0)   # lo que se toma de la Parte 1 (hasta el final de una escena)
TEASER_FINAL_S = 3.5      # la pantalla «Video completo»


def cmd_teaser(a):
    """El teaser vertical del largo (9:16): el arranque de la Parte 1 ya entregada (gancho y lo que le sigue, hasta el
    final de una escena, 12–26 s) y una pantalla final «Video completo · En YouTube». Lleva de los cortos al largo: hoy
    nada lo hace. Sin voz nueva (0 créditos). → salida/teaser.mp4 y teaser.md."""
    trabajo = os.path.abspath(a.trabajo)
    Y = estado_y(trabajo)
    M = leer(os.path.join(trabajo, "montaje.json"))
    p1 = next((p for p in Y["partes"] if p["n"] == 1), None)
    v1 = os.path.join(RAIZ, p1["ruta"], "video.mp4") if p1 and p1.get("ruta") else None
    if not v1 or not os.path.exists(v1):
        v1 = os.path.join(RAIZ, p1["trabajo"], "salida", "video.mp4") if p1 else None
    if not v1 or not os.path.exists(v1):
        return falla("el teaser sale del video 9:16 de la Parte 1 y no está (ni en su entrega ni en su TRABAJO)")
    E1 = leer(os.path.join(RAIZ, p1["trabajo"], "escenas.json"))["escenas"]
    t, corte = 0.0, None
    for S in E1:
        t += S["dur"] - VD.TRANSICION
        if (S.get("tipo") or "") == "cierre":
            break
        if TEASER_S[0] <= t <= TEASER_S[1]:
            corte = t          # el último final de escena que cabe
    if corte is None:
        corte = min(TEASER_S[1], VD.ffprobe_dur(v1) - 1)
    titulo = ((M.get("youtube") or {}).get("titulo") or Y.get("tema") or "").strip()
    yt = next((r["handle"] for r in VD.REDES if r["red"] == "youtube"), "")
    largo = os.path.join(trabajo, "salida", "video.mp4")
    minutos = int(round(VD.ffprobe_dur(largo) / 60)) if os.path.exists(largo) else None
    f_esc = os.path.join(trabajo, "escenas.json")
    E = leer(f_esc)
    E["teaser"] = {"titulo": titulo, "handle": yt, "minutos": minutos}
    escribir(f_esc, E)
    segs, sal = os.path.join(trabajo, "segs_16x9"), os.path.join(trabajo, "salida")
    os.makedirs(segs, exist_ok=True)
    os.makedirs(sal, exist_ok=True)
    png, lista = os.path.join(segs, "teaser_final.png"), os.path.join(segs, "teaser.json")
    escribir(lista, [{"nombre": "teaser", "pagina": "teaser", "archivo": png}])
    rc = subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, "--hilo", os.path.join(trabajo, "base"),
                         "--formato", "9:16", "--portadas", lista], cwd=RAIZ).returncode
    if rc:
        return falla("la pantalla final del teaser no se pudo dibujar")
    out = os.path.join(sal, "teaser.mp4")
    fo = 0.5
    VD.ff("-t", "%.3f" % corte, "-i", v1, "-loop", "1", "-t", "%.2f" % TEASER_FINAL_S, "-i", png,
          "-f", "lavfi", "-t", "%.2f" % TEASER_FINAL_S, "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex",
          "[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[v0];[1:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[v1];"
          "[v0][v1]xfade=transition=fade:duration=%.2f:offset=%.3f[v];"
          "[0:a]aresample=48000,afade=t=out:st=%.3f:d=%.2f[a0];[a0][2:a]acrossfade=d=%.2f[a]" % (fo, corte - fo, corte - fo, fo, fo),
          "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
          "-movflags", "+faststart", out)
    open(os.path.join(sal, "teaser.md"), "w", encoding="utf-8").write("\n".join([
        "# Teaser del video largo", "",
        "`teaser.mp4` (9:16, %.0f s): el arranque de la Parte 1 y la pantalla «Video completo». Súbelo como Short, Reel y "
        "TikTok el día que publiques el largo; en YouTube Studio ponle el video largo como «Video relacionado»." % VD.ffprobe_dur(out), "",
        "```", "%s\nEl documental completo%s está en YouTube: %s" % (titulo, " (%d min)" % minutos if minutos else "", yt),
        "#Guatemala #documental", "```", ""]))
    print("teaser %.1f s (%.1f s de la Parte 1 + %.1f s de pantalla final) → %s" % (VD.ffprobe_dur(out), corte, TEASER_FINAL_S, rel(out)))
    return 0


def contacto(video, salida, n=24, escenas=None, offs=None):
    """Hoja de contacto. Con las escenas, un cuadro por escena en su estado final (0.4 s antes de que termine: un
    cuadro a intervalos fijos cae a mitad de una animación y engaña); sin ellas, n cuadros repartidos."""
    d = VD.ffprobe_dur(video)
    if not escenas:
        VD.ff("-i", video, "-vf", "fps=%.5f,scale=320:-1,tile=6x4:padding=6:color=black" % (n / d), "-frames:v", "1", salida)
        return
    tmp = tempfile.mkdtemp(prefix="contacto_")
    try:
        for i, (S, off) in enumerate(zip(escenas, offs)):
            t = min(d - 0.1, off + max(0.2, S["dur"] - VD.TRANSICION - 0.4))
            VD.ff("-ss", "%.3f" % t, "-i", video, "-frames:v", "1", "-vf", "scale=320:-1", os.path.join(tmp, "%04d.png" % i))
        cols = 8
        filas = -(-len(escenas) // cols)
        VD.ff("-framerate", "1", "-i", os.path.join(tmp, "%04d.png"), "-vf", "tile=%dx%d:padding=6:color=black" % (cols, filas),
              "-frames:v", "1", salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fuentes_unidas(Y, caps):
    L = ["# Fuentes · %s" % Y.get("tema"), "", "Cada hecho del video con las fuentes que lo respaldan, por capítulo.", ""]
    for c_ in caps:
        p = next((x for x in Y["partes"] if x["n"] == c_["parte"]), None)
        f = os.path.join(RAIZ, p["ruta"], "fuentes.md") if p and p.get("ruta") else None
        L += ["## Capítulo %d · %s (%s)" % (c_["numero"], c_["titulo"], mmss(c_["t"])), ""]
        if f and os.path.exists(f):
            for linea in open(f, encoding="utf-8").read().splitlines():
                if linea.startswith("# ") or linea.startswith("Para la descripción"):
                    continue
                L.append(linea.replace("## ", "### ", 1) if linea.startswith("## ") else linea)
        L.append("")
    return "\n".join(L).rstrip() + "\n"


COMENTARIO_MAX = 9500   # un comentario de YouTube admite ≈ 10,000 caracteres


def fuentes_del_video(Y, caps, escenas, por_id):
    """(fuentes.md, comentario.txt) SOLO de lo que quedó en el video: por capítulo, los hechos de sus escenas (no los de
    las que el montaje quitó) con sus fuentes sin URL repetidas. El comentario lista cada fuente una vez, bajo el minuto
    de su capítulo, y cabe en un comentario fijado (antes: 62,000 caracteres con 290 URL, 92 distintas)."""
    H = hechos_serie(Y)
    cap, por_cap = 0, {}
    for S in escenas:
        if S.get("tipo") == "capitulo":
            cap = S["H"]["numero"]
        for h in (por_id.get(S.get("origen")) or {}).get("hechos") or []:
            if h in H and h not in por_cap.setdefault(max(cap, 1), []):
                por_cap[max(cap, 1)].append(h)
    md = ["# Fuentes · %s" % Y.get("tema"), "", "Cada hecho que quedó en el video, con las fuentes que lo respaldan, por capítulo.", ""]
    com, vistas = ["Fuentes, por capítulo:", ""], set()
    for c_ in caps:
        md += ["## Capítulo %d · %s (%s)" % (c_["numero"], c_["titulo"], mmss(c_["t"])), ""]
        lineas = []
        for h in por_cap.get(c_["numero"], []):
            x, urls = H[h], []
            md.append("- %s%s" % (x.get("texto"), " *(una fuente)*" if x.get("estado") == "una_fuente" else ""))
            for f_ in x.get("fuentes") or []:
                u = (f_.get("url") or "").strip()
                if u and u not in urls:
                    urls.append(u)
                    md.append("  - %s: %s" % (f_.get("medio") or "fuente", u))
                    if u not in vistas:
                        vistas.add(u)
                        lineas.append("%s: %s" % (f_.get("medio") or "Fuente", u))
        md.append("")
        if lineas:
            com += ["%s %s" % (mmss(c_["t"]), c_["titulo"])] + lineas + [""]
    texto = "\n".join(com).rstrip() + "\n"
    if len(texto) > COMENTARIO_MAX:   # no cabe: se corta en una línea entera y remite a la lista completa
        corte = texto[:COMENTARIO_MAX - 80].rsplit("\n", 1)[0]
        texto = corte + "\n\n(Lista completa de fuentes: en la descripción del canal o a pedido.)\n"
    return "\n".join(md).rstrip() + "\n", texto


def revisar_capitulos(caps, total, minimo=3):
    f = []
    if len(caps) < minimo:
        f.append("YT11 YouTube muestra capítulos con ≥ 3 (hay %d)" % len(caps))
    if caps and caps[0]["t"] != 0:
        f.append("YT11 el primer capítulo empieza en 0:00")
    for j, c_ in enumerate(caps):
        t1 = caps[j + 1]["t"] if j + 1 < len(caps) else total
        if t1 - c_["t"] < 10:
            f.append("YT11 el capítulo %d dura %.0f s (YouTube pide ≥ 10 s)" % (c_["numero"], t1 - c_["t"]))
    return f


def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    Y = estado_y(trabajo)
    M = leer(os.path.join(trabajo, "montaje.json"))
    sal = os.path.join(trabajo, "salida")
    video = os.path.join(sal, "video.mp4")
    mini = os.path.join(sal, "miniatura.png")
    for req in (video, mini, os.path.join(sal, "subtitulos.srt"), os.path.join(trabajo, "capitulos.json")):
        if not os.path.exists(req):
            return falla("falta %s (montar y miniatura)" % rel(req))
    C = leer(os.path.join(trabajo, "capitulos.json"))
    caps, total = C["capitulos"], VD.ffprobe_dur(video)
    f = revisar_capitulos(caps, total, 2 if Y.get("fixture") else 3)   # la maqueta tiene 2 partes
    yt = M.get("youtube") or {}
    titulo = (yt.get("titulo") or "").strip()
    desc = (yt.get("descripcion") or "").strip()
    if not titulo or len(titulo) > TITULO_YT:
        f.append("YT11 montaje.youtube.titulo de 1–%d caracteres" % TITULO_YT)
    if not desc:
        f.append("YT11 montaje.youtube.descripcion (2–4 oraciones: de qué trata, sin anunciar el final)")
    if desc and VD.META_PROMESA.search(desc):
        f.append("YT11 la descripción anuncia el video («%s»)" % VD.META_PROMESA.search(desc).group(0))
    redes = " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in VD.REDES)
    bloque = "\n".join("%s %s" % (mmss(c_["t"]), c_["titulo"]) for c_ in caps)
    tags = " ".join(yt.get("hashtags") or [])
    texto = "\n\n".join(x for x in (desc, "Capítulos\n" + bloque, "Fuentes de cada hecho, por capítulo: en el primer comentario.",
                                     "Sígueme en " + redes, tags) if x)
    if len(texto) > DESCRIPCION_YT:
        f.append("YT11 la descripción pasa de %d caracteres" % DESCRIPCION_YT)
    for x in f:
        print("FALLA", x)
    if f:
        return 1
    dest = os.path.abspath(a.salida or os.path.join(RAIZ, Y["carpeta"], "youtube"))
    os.makedirs(dest, exist_ok=True)
    for nombre in ("video.mp4", "subtitulos.srt"):
        shutil.copy2(os.path.join(sal, nombre), os.path.join(dest, nombre))
    for x in glob.glob(os.path.join(sal, "miniatura*.png")):
        shutil.copy2(x, os.path.join(dest, os.path.basename(x)))
    for nombre in ("teaser.mp4", "teaser.md"):   # el teaser vertical, si se hizo (youtube.py teaser)
        if os.path.exists(os.path.join(sal, nombre)):
            shutil.copy2(os.path.join(sal, nombre), os.path.join(dest, nombre))
    shutil.copy2(os.path.join(trabajo, "montaje.json"), os.path.join(dest, "montaje.json"))
    escribir(os.path.join(dest, "capitulos.json"), C)
    Es = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    offs_c, t_c = [], 0.0
    for S in Es:
        offs_c.append(t_c)
        t_c += S["dur"] - VD.TRANSICION
    contacto(video, os.path.join(dest, "contacto.png"), escenas=Es, offs=offs_c)
    por_id_e = cargar_contexto(trabajo)[2]
    f_md, f_com = fuentes_del_video(Y, caps, Es, por_id_e)
    if f_md.count("\n- ") < 3:   # sin hechos por escena (una maqueta): las fuentes de cada parte, como antes
        f_md, f_com = fuentes_unidas(Y, caps), None
    open(os.path.join(dest, "fuentes.md"), "w", encoding="utf-8").write(f_md)
    if f_com:
        open(os.path.join(dest, "comentario.txt"), "w", encoding="utf-8").write(f_com)
    partes_md = ["%d. %s — %s" % (p_["n"], p_.get("titulo") or "", p_.get("ruta") or "") for p_ in Y["partes"]]
    minis = sorted(os.path.basename(x) for x in glob.glob(os.path.join(sal, "miniatura_*.png")))
    caption = ["# YouTube · %s" % Y.get("tema"), "",
               "Súbelo como video normal (16:9, %s): miniatura `miniatura.png`, subtítulos `subtitulos.srt` (español), "
               "el primer comentario con `fuentes.md` y, al final, la pantalla final con un video de la serie y el botón de "
               "suscribirse en la mitad derecha (los últimos %.0f s)." % (mmss(total), FINAL_EXTRA_S), "",
               "## Título", "", "```", titulo, "```", "", "## Descripción", "", "```", texto, "```", ""] + [
               "## Primer comentario (fíjalo)", "", "Copia `comentario.txt` tal cual: las fuentes una vez cada una, bajo el minuto de su "
               "capítulo (cabe en un comentario). La lista completa por hecho está en `fuentes.md`.", "",
               "## Al publicar", "",
               "- Audiencia: «No, no está hecho para niños».",
               "- Lista de reproducción: una con el nombre de la serie; añade ahí también los Shorts de las partes.",
               "- Etiquetas: %s" % ", ".join(dict.fromkeys([Y.get("tema") or ""] + [h.lstrip("#") for h in yt.get("hashtags") or []] + ["Guatemala", "documental"])),
               "- Miniatura: sube %s a «Probar y comparar» si hay más de una." % (", ".join(minis) or "`miniatura.png`"),
               "- En cada Short de la serie (YouTube Studio → Video relacionado), enlaza este video largo:", ""] + partes_md + [""]
    open(os.path.join(dest, "caption.md"), "w", encoding="utf-8").write("\n".join(caption))
    nuevas = os.path.join(trabajo, "nuevas", "audio", "creditos.json")
    creditos = leer(nuevas).get("total") if os.path.exists(nuevas) else 0
    escribir(os.path.join(dest, "guion.json"), {
        "tipo": "youtube", "id": "youtube-" + Y["slug"], "slug": Y["slug"], "tema": Y.get("tema"), "serie": Y["serie"],
        "fecha": datetime.date.today().isoformat(), "duracion_s": round(total, 1), "titulo": titulo, "descripcion": desc,
        "capitulos": caps, "paleta": Y.get("paleta"), "musica": C.get("musica") or [Y.get("musica")], "creditos_voz": creditos,
        "promesa": M.get("promesa"), "partes": [p["n"] for p in Y["partes"]], "fixture": bool(Y.get("fixture"))})
    print("entregado → %s (%s, %d capítulos)" % (rel(dest), mmss(total), len(caps)))
    print(rel(dest))
    return 0


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    q = sub.add_parser("preparar")
    q.add_argument("serie")
    q.add_argument("--trabajo")
    q.add_argument("--fixture", action="store_true")
    q.add_argument("--revisar", action="store_true")
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--para", choices=("editor", "oyente", "critico"), required=True)
    q = sub.add_parser("montaje")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true")
    for nombre in ("probar", "aplicar"):
        q = sub.add_parser(nombre)
        q.add_argument("trabajo")
        q.add_argument("--cambios", required=True)
    sub.add_parser("resumen").add_argument("trabajo")
    q = sub.add_parser("voz")
    q.add_argument("trabajo")
    q.add_argument("--falsa", action="store_true")
    q.add_argument("--sin-gate", action="store_true", help=argparse.SUPPRESS)   # solo pruebas de desarrollo
    sub.add_parser("tiempos").add_argument("trabajo")
    sub.add_parser("teaser", help="el teaser vertical 9:16 del largo: arranque de la Parte 1 + «Video completo»").add_argument("trabajo")
    q = sub.add_parser("armar")
    q.add_argument("--todo", action="store_true", help="borra todos los clips (cambió una página de video/): se regraba entero")
    q.add_argument("trabajo")
    q.add_argument("--sin-gate", action="store_true", help=argparse.SUPPRESS)
    q = sub.add_parser("grabar")
    q.add_argument("trabajo")
    q.add_argument("--fps", type=int, default=30)
    q.add_argument("--solo")
    q.add_argument("--paralelo", type=int)
    sub.add_parser("montar").add_argument("trabajo")
    q = sub.add_parser("miniatura")
    q.add_argument("trabajo")
    q.add_argument("--texto", required=True)
    q.add_argument("--foto")
    q.add_argument("--cifra")
    q.add_argument("--chip")
    q.add_argument("--nombre", help="variante (miniatura_<nombre>.png); sin él, miniatura.png")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"preparar": cmd_preparar, "digesto": cmd_digesto, "montaje": cmd_montaje, "probar": cmd_probar,
            "aplicar": cmd_aplicar, "resumen": cmd_resumen, "voz": cmd_voz, "tiempos": cmd_tiempos, "armar": cmd_armar,
            "grabar": cmd_grabar, "montar": cmd_montar, "miniatura": cmd_miniatura, "teaser": cmd_teaser,
            "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
