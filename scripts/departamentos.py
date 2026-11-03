#!/usr/bin/env python3
"""/departamento: la serie de 22 videos (un departamento frente al país) sobre /perfil (hilo) → /video.

Lee el canon (referencias/departamentos.json: orden por población, alias y las 5–6 dimensiones con la misma fuente y
año para los 22) y la memoria (memoria/hilos.json y memoria/videos.json); nunca escribe ninguna de las dos. Los códigos
GT01–GT22 y sus nombres son los de templates/base.html (H.NOMBRES), los mismos de design/mapa_geometria.svg y de la
escena mapa (`--check` falla si divergen).

Uso:
  python3 scripts/departamentos.py --resolver <nombre|alias|GTxx>   → «GT13 Huehuetenango» (exit 1 si no lo reconoce)
  python3 scripts/departamentos.py --directiva <GTxx|nombre>        → texto del canon para el editor y el investigador
                                                                      (lo pasa /departamento como args.canon de /hilo)
  python3 scripts/departamentos.py --tablero [--memoria DIR] [--json]   → las 22 filas: hilo perfil y video, hecho o pendiente
  python3 scripts/departamentos.py --siguiente [--memoria DIR]      → el primer departamento del orden sin video
  python3 scripts/departamentos.py --check [--canon RUTA]           → canon válido (exit 1 con la lista de faltas)

Gates D (los llama scripts/video.py cuando el hilo es un perfil de departamento; `validar` en `guion --check`,
`d1_real` en `tiempos`, `d3` también en `entregar`):
  D1 el nombre (o un alias) suena en la voz del gancho en ≤ 3 s (estimado en el gate, real en tiempos; V19 con max_s 3)
  D2 el nombre se lee en la pantalla del gancho, o el visual del gancho es `lugar` con su código
  D3 la 1.ª línea de los captions de TikTok, Instagram y Facebook y el título de Shorts lo nombran; algún caption dice
     «Para alguien de <depto>» (la invitación a compartir es implícita: nunca en la voz; F4 sigue vigente); aviso si
     falta el hashtag
  D4 cada tarjeta con el valor del departamento trae también el del país, de la misma fuente y periodo (datos.json)
  D5 las dimensiones del hilo son las del canon, en su fuente y su año (un desvío sin `motivo` falla; con motivo, aviso)
  D6 el puesto que dice el video es el calculado del desglose de los 22; las tasas por habitante declaran el
     denominador INE del mismo año
  D7 hay una escena `mapa` y un `ranking` con `ventana: true`, de tarjetas distintas, con el departamento destacado
  D8 duración real ≥ 61 s (video.piso_duracion con `piso_s` en video.json)
  D9 la frase final del cierre nombra el departamento (F4 sigue prohibiendo pedir que etiqueten o compartan)

Exit: 0 ok · 1 falla · 2 uso incorrecto. Solo stdlib.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(RAIZ, "referencias", "departamentos.json")
MEMORIA = os.path.join(RAIZ, "memoria")
N_DEPTOS = 22
DIMENSIONES = (5, 6)                 # dimensiones del canon
ESTADOS = ("propuesta", "aprobada")
PISO_S = 61                          # D8 (= video.PISO_DURACION_S)
CLAVE_S = 3.0                        # D1: el nombre suena antes de este segundo
SERIE = "departamentos"
CAMPOS_DIM = ("id", "nombre", "fuente_id", "fuente", "claves_fuente", "indicador", "anio", "unidad", "per_capita",
              "denominador", "desglose_22", "estado")
RE_PAIS = re.compile(r"\b(?:nacional|pa[ií]s|rep[uú]blica|total (?:del )?pa[ií]s)\b", re.I)
RE_PER_CAPITA = re.compile(r"por (?:cada )?(?:100|1,000|1000|10,000|100,000|100000|mil)\b", re.I)
RE_PUESTO = (re.compile(r"\b(?:puesto|lugar|n[uú]mero|n\.\s?º|no\.)\s+(\d{1,2})\b", re.I),
             re.compile(r"\b(\d{1,2})\s+de\s+(?:los\s+)?%d\b" % N_DEPTOS, re.I))
_NOMBRES_BASE = None


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return re.sub(r"[^a-z0-9ñ]+", " ", "".join(ch for ch in s if unicodedata.category(ch) != "Mn")).strip()


def leer(ruta, defecto=None):
    try:
        return json.load(open(ruta, encoding="utf-8"))
    except (OSError, ValueError):
        return defecto


def nombres_base():
    """{GT01: «Guatemala», …} de templates/base.html (H.NOMBRES): la fuente única de códigos y nombres."""
    global _NOMBRES_BASE
    if _NOMBRES_BASE is None:
        try:
            base = open(os.path.join(RAIZ, "templates", "base.html"), encoding="utf-8").read()
            m = re.search(r"const NOMBRES = \{([\s\S]*?)\};", base)
            _NOMBRES_BASE = dict(re.findall(r'(GT\d\d):\s*"([^"]+)"', m.group(1))) if m else {}
        except OSError:
            _NOMBRES_BASE = {}
    return _NOMBRES_BASE


def canon(ruta=None):
    C = leer(ruta or CANON)
    if not isinstance(C, dict):
        raise SystemExit("no puedo leer el canon %s" % os.path.relpath(ruta or CANON, RAIZ))
    return C


def nombre_de(cod, C=None):
    return (C or {}).get("nombres", {}).get(cod) or nombres_base().get(cod) or cod


def resolver(x, C=None):
    """Nombre, alias, código GTxx o un prefijo único (≥ 4 letras) → código, o None."""
    C = C or canon()
    nombres = C.get("nombres") or nombres_base()
    s = str(x or "").strip()
    if re.fullmatch(r"(?i)gt\d\d", s) and s.upper() in nombres:
        return s.upper()
    n = norm(re.sub(r"(?i)^(?:el\s+)?departamento\s+de\s+", "", s)) if norm(s) != norm("departamento de Guatemala") else norm("Guatemala")
    if not n:
        return None
    for cod, nom in nombres.items():
        if norm(nom) == n:
            return cod
    for cod, als in (C.get("alias") or {}).items():
        if any(norm(a) == n for a in als):
            return cod
    if len(n) >= 4:
        cand = {cod for cod, nom in nombres.items() if norm(nom).startswith(n)}
        cand |= {cod for cod, als in (C.get("alias") or {}).items() for a in als if norm(a).startswith(n)}
        if len(cand) == 1:
            return cand.pop()
    return None


def claves(cod, C=None):
    """Palabra clave SEO del departamento: el nombre y sus alias (para V19/D1–D3 y D9)."""
    C = C or canon()
    return [nombre_de(cod, C)] + [a for a in (C.get("alias") or {}).get(cod, []) if a]


def nombra(texto, cod, C=None):
    t = " %s " % norm(texto)
    return any((" %s " % norm(k)) in t for k in claves(cod, C))


# ---------- canon ----------
def check(C):
    f = []
    base = nombres_base()
    if not isinstance(C.get("version"), int):
        f.append("version debe ser un entero")
    if len(base) != N_DEPTOS:
        f.append("templates/base.html: H.NOMBRES no trae los %d departamentos" % N_DEPTOS)
    nombres = C.get("nombres") or {}
    if nombres != base:
        dif = sorted(k for k in set(nombres) | set(base) if nombres.get(k) != base.get(k))
        f.append("nombres del canon ≠ H.NOMBRES de templates/base.html en %s" % ", ".join(dif))
    orden = C.get("orden") or []
    if sorted(orden) != sorted(base) or len(orden) != N_DEPTOS:
        f.append("orden: los %d códigos, cada uno una vez (llegaron %d)" % (N_DEPTOS, len(orden)))
    alias = C.get("alias") or {}
    vistos = {norm(v): k for k, v in base.items()}
    for cod, als in alias.items():
        if cod not in base:
            f.append("alias: código %s desconocido" % cod)
            continue
        for a in als:
            n = norm(a)
            if not n:
                f.append("alias %s: vacío" % cod)
            elif n in vistos and vistos[n] != cod:
                f.append("alias «%s» de %s choca con %s" % (a, cod, vistos[n]))
            vistos.setdefault(n, cod)
    dims = C.get("dimensiones") or []
    if not DIMENSIONES[0] <= len(dims) <= DIMENSIONES[1]:
        f.append("dimensiones: %d–%d (llegaron %d)" % (DIMENSIONES[0], DIMENSIONES[1], len(dims)))
    ids = [d.get("id") for d in dims]
    if len(set(ids)) != len(ids):
        f.append("dimensiones: ids repetidos (%s)" % ", ".join(map(str, ids)))
    for d in dims:
        did = d.get("id") or "?"
        for k in CAMPOS_DIM:
            if k not in d:
                f.append("dimensión %s: falta «%s»" % (did, k))
        if d.get("estado") not in ESTADOS:
            f.append("dimensión %s: estado %r (%s)" % (did, d.get("estado"), "|".join(ESTADOS)))
        if d.get("anio") is not None and not (isinstance(d["anio"], int) and 1990 <= d["anio"] <= 2100):
            f.append("dimensión %s: anio entero o null (llegó %r)" % (did, d.get("anio")))
        if d.get("anio") is None and not str(d.get("nota") or "").strip():
            f.append("dimensión %s: anio null necesita una nota (qué año falta confirmar)" % did)
        if d.get("per_capita") is True and not str(d.get("denominador") or "").strip():
            f.append("dimensión %s: per_capita exige el denominador (población INE del mismo año)" % did)
        if not [c for c in d.get("claves_fuente") or [] if str(c).strip()]:
            f.append("dimensión %s: claves_fuente vacía (D5 coteja con ellas la fuente de la tarjeta)" % did)
        if d.get("desglose_22") not in (True, False, None):
            f.append("dimensión %s: desglose_22 true|false|null" % did)
    if not any(d.get("desglose_22") is True for d in dims):
        f.append("ninguna dimensión publica los 22 (desglose_22): el mapa y el ranking del video no tienen de dónde salir")
    return f


def directiva(cod, C=None):
    C = C or canon()
    nom = nombre_de(cod, C)
    dims = C.get("dimensiones") or []
    L = ["CANON /departamento v%s (referencias/departamentos.json; %s) para %s (%s):" % (
        C.get("version"), "BORRADOR sin aprobar" if C.get("estado") != "aprobado" else "aprobado", nom, cod),
        "usa EXACTAMENTE estas %d dimensiones, cada una con la fuente y el año del canon (año null = el más reciente que la "
        "fuente publique para los 22; decláralo) y el valor de %s Y el del país de la MISMA fuente y periodo:" % (len(dims), nom)]
    for d in dims:
        L.append("· %s [canon: %s] — %s · %s · año %s%s%s." % (
            d["nombre"], d["id"], d["indicador"], d["fuente"], d.get("anio") if d.get("anio") is not None else "(el último con los 22)",
            " · tasa con denominador %s" % d["denominador"] if d.get("per_capita") else "",
            " · trae el desglose de los 22 departamentos" if d.get("desglose_22") else ""))
    L.append("Al menos una dimensión va como desglose de los %d (cifra tipo desglose con las %d partes y los nombres oficiales del "
             "INE) en una tarjeta `mapa` con destacar: \"%s\" (la del video y la del ranking en ventana); hacen falta 2 desgloses "
             "de 22 si se puede (el video usa uno en el mapa y otro en el ranking). En guion.json: perfil {sujeto: \"%s\", tipo: "
             "\"departamento\", codigo: \"%s\", canon_version: %s, dimensiones[]{n, nombre, anio, canon: <id del canon>, motivo? "
             "(solo si se desvía)}, omitidas?[{canon, motivo}]}; 7–8 tuits. Las tasas por habitante llevan en la cifra "
             "`denominador` (población INE del mismo año) y `calculo`." % (N_DEPTOS, N_DEPTOS, cod, nom, cod, C.get("version")))
    return " ".join(L)


# ---------- memoria: tablero y siguiente ----------
def hechos(memdir=None, C=None):
    """{cod: {"hilo": registro|None, "video": registro|None}} desde memoria/hilos.json y memoria/videos.json."""
    C = C or canon()
    memdir = memdir or MEMORIA
    out = {cod: {"hilo": None, "video": None} for cod in C["orden"]}
    for h in (leer(os.path.join(memdir, "hilos.json"), {}) or {}).get("hilos", []):
        if h.get("modo") == "perfil" and h.get("sujeto"):
            cod = resolver(h["sujeto"], C)
            if cod in out:
                out[cod]["hilo"] = h
    for v in (leer(os.path.join(memdir, "videos.json"), {}) or {}).get("videos", []):
        if v.get("serie") == SERIE:
            cod = v.get("codigo") or resolver(v.get("sujeto"), C)
            if cod in out:
                out[cod]["video"] = v
    return out


def tablero(memdir=None, C=None):
    C = C or canon()
    H = hechos(memdir, C)
    filas = []
    for k, cod in enumerate(C["orden"], 1):
        h, v = H[cod]["hilo"], H[cod]["video"]
        filas.append({"n": k, "codigo": cod, "nombre": nombre_de(cod, C),
                      "hilo": "hecho" if h else "pendiente", "hilo_ruta": (h or {}).get("ruta"),
                      "video": (v or {}).get("estado") or "hecho" if v else "pendiente", "video_ruta": (v or {}).get("ruta_video")})
    return filas


def siguiente(memdir=None, C=None):
    return next((f for f in tablero(memdir, C) if f["video"] == "pendiente"), None)


# ---------- datos: desgloses de los 22 y puestos ----------
def valores_22(x, C=None):
    """{GTxx: valor} si `x` (cifra de datos.json con partes, o DATA de una tarjeta con valores/items) trae los 22."""
    C = C or canon()
    out = {}
    if isinstance(x.get("valores"), dict):
        pares = list(x["valores"].items())
    else:
        pares = [(p.get("nombre", p.get("etiqueta")), p.get("valor")) for p in (x.get("partes") or x.get("items") or [])
                 if isinstance(p, dict)]
    for k, v in pares:
        cod = resolver(k, C) if not re.fullmatch(r"GT\d\d", str(k)) else str(k)
        if cod and isinstance(v, (int, float)) and not isinstance(v, bool):
            out[cod] = float(v)
    return out if len(out) == N_DEPTOS else None


def puesto_de(vals, cod, orden="desc"):
    """Puesto de `cod` en {cod: valor} (1 = el mayor con orden desc; empates comparten el mejor puesto)."""
    if cod not in vals:
        return None
    v = vals[cod]
    return 1 + sum(1 for x in vals.values() if (x > v if orden != "asc" else x < v))


def puestos(cifras, tarjetas, cod, C=None):
    """{cid | "T<n>": {puesto, de, orden, valor}} de cada desglose de los 22 (cifras de datos.json y tarjetas mapa)."""
    C = C or canon()
    out = {}
    for c in cifras:
        vals = valores_22(c, C) if c.get("partes") else None
        if vals and cod in vals:
            out[c["id"]] = {"puesto": puesto_de(vals, cod), "de": N_DEPTOS, "orden": "desc", "valor": vals[cod]}
    for t in tarjetas or []:
        vals = valores_22(t.get("datos") or {}, C) if t.get("datos") else None
        if vals and cod in vals:
            out["T%d" % t["n"]] = {"puesto": puesto_de(vals, cod), "de": N_DEPTOS, "orden": "desc", "valor": vals[cod]}
    return out


def departamento_de_hilo(hilo, C=None):
    """El código del departamento si el hilo entregado es un perfil de departamento (modo perfil, perfil.tipo), o None."""
    P = hilo.get("perfil") if isinstance(hilo.get("perfil"), dict) else {}
    if hilo.get("modo") != "perfil" or P.get("tipo") != "departamento":
        return None
    C = C or canon()
    return resolver(P.get("codigo"), C) or resolver(P.get("sujeto"), C)


def estado_video(hilo, datos, tarjetas, C=None):
    """Bloque `departamento` de video.json (o None): código, nombre, alias, puestos, versión del canon."""
    C = C or canon()
    cod = departamento_de_hilo(hilo, C)
    if not cod:
        return None
    return {"codigo": cod, "nombre": nombre_de(cod, C), "alias": (C.get("alias") or {}).get(cod, []),
            "puestos": puestos(datos.get("cifras") or [], tarjetas, cod, C), "canon_version": C.get("version"),
            "dimensiones": [d["id"] for d in C.get("dimensiones") or []]}


# ---------- gates D ----------
def _vd():
    import video as VD   # import tardío: video.py importa este módulo
    return VD


def d1(cod, voz, C=None):
    """D1: el nombre en la voz del gancho en ≤ 3 s. `voz` = texto (estimado) o palabras con tiempos (real)."""
    VD = _vd()
    ks = claves(cod, C)
    return VD.revisar_palabra_clave(ks, voz, [ks[0]], {}, max_s=CLAVE_S, plataformas=(), codigo="D1")


def d1_real(st, palabras_1):
    dep = st.get("departamento")
    return d1(dep["codigo"], palabras_1) if dep else []


def d3(cod, captions, C=None):
    """D3: los captions nombran el departamento en su 1.ª línea; «Para alguien de <depto>» en algún caption."""
    VD = _vd()
    ks = claves(cod, C)
    f = VD.revisar_palabra_clave(ks, None, [ks[0]], captions or {}, plataformas=("tiktok", "instagram", "facebook", "shorts"),
                                 codigo="D3")
    av = []
    txt = " ".join(str((captions or {}).get(k) or "") for k in ("tiktok", "instagram", "facebook"))
    if not any(("para alguien de " + norm(k)) in norm(txt) for k in ks):
        f.append("D3 ningún caption dice «Para alguien de %s» (la invitación a compartir va implícita en el caption, nunca en "
                 "la voz)" % ks[0])
    tag = "#" + re.sub(r"\s+", "", ks[0])
    if norm(tag) not in norm(str((captions or {}).get("tiktok") or "")):
        av.append("D3 caption.tiktok sin el hashtag %s" % tag)
    return f, av


def _cifras_de_escena(e, hilo, cifras):
    t = next((x for x in hilo.get("tuits") or [] if x.get("n") == e.get("tuit")), None)
    return t, [cifras[c] for c in (t or {}).get("cifra_ids") or [] if c in cifras]


def _lado(c, cod, C):
    """('depto', 'pais') que cubre la cifra `c`: un desglose de los 22 cubre el depto; un par [depto, país] los dos."""
    lados = set()
    if c.get("partes") and valores_22(c, C):
        return {"depto"}
    for p in c.get("partes") or []:
        nom = str(p.get("nombre", p.get("etiqueta")) or "")
        if resolver(nom, C) == cod and not RE_PAIS.search(nom):
            lados.add("depto")
        elif RE_PAIS.search(nom) or (norm(nom) == "guatemala" and cod != "GT01"):
            lados.add("pais")
    concepto = str(c.get("concepto") or "")
    if not lados:
        if nombra(concepto, cod, C) and not RE_PAIS.search(concepto):
            lados.add("depto")
        elif RE_PAIS.search(concepto) and not nombra(concepto, cod, C):
            lados.add("pais")
    return lados


def d4(g, st, hilo, cifras, C=None):
    f = []
    cod = st["departamento"]["codigo"]
    nom = nombre_de(cod, C)
    for i, e in enumerate(g.get("escenas") or [], 1):
        if e.get("tipo") not in ("tarjeta", "mapa", "ranking", "tiempo"):
            continue
        t, cs = _cifras_de_escena(e, hilo, cifras)
        dep = [c for c in cs if "depto" in _lado(c, cod, C)]
        pais = [c for c in cs if "pais" in _lado(c, cod, C)]
        if not dep:
            continue
        if not pais:
            f.append("D4 escena %d (T%s): el valor de %s va sin el del país (añade a la tarjeta la cifra nacional de la misma "
                     "fuente y periodo)" % (i, e.get("tuit"), nom))
            continue
        for a in dep:
            for b in pais:
                if a is b:
                    continue
                pa, pb = str(a.get("periodo") or a.get("anio") or ""), str(b.get("periodo") or b.get("anio") or "")
                if pa != pb:
                    f.append("D4 escena %d (T%s): %s es de %s y el país (%s) de %s: misma fuente y periodo"
                             % (i, e.get("tuit"), a["id"], pa or "?", b["id"], pb or "?"))
                fa, fb = norm(a.get("fuente")), norm(b.get("fuente"))
                if fa and fb and fa not in fb and fb not in fa:
                    f.append("D4 escena %d (T%s): %s y el país (%s) vienen de fuentes distintas («%s» / «%s»)"
                             % (i, e.get("tuit"), a["id"], b["id"], a.get("fuente"), b.get("fuente")))
    return f


def d5(hilo, C=None):
    C = C or canon()
    f, av = [], []
    P = hilo.get("perfil") or {}
    dims = {d["id"]: d for d in C.get("dimensiones") or []}
    por_nombre = {norm(d["nombre"]): d["id"] for d in dims.values()}
    tuits = {t.get("n"): t for t in hilo.get("tuits") or []}
    vistos = set()
    for q in P.get("dimensiones") or []:
        did = q.get("canon") or por_nombre.get(norm(q.get("nombre"))) or (q.get("canon") if q.get("canon") in dims else None)
        motivo = str(q.get("motivo") or "").strip()
        rep = av.append if motivo else f.append
        if did not in dims:
            rep("D5 T%s: la dimensión «%s» no está en el canon (%s)%s" % (q.get("n"), q.get("nombre"), ", ".join(dims),
                                                                       " · motivo: " + motivo if motivo else ": decláralo con «canon» o da un «motivo»"))
            continue
        vistos.add(did)
        d = dims[did]
        fuente = (tuits.get(q.get("n")) or {}).get("fuente") or ""
        if not any(norm(k) in norm(fuente) for k in d.get("claves_fuente") or []):
            rep("D5 T%s (%s): la fuente «%s» no es la del canon (%s)%s" % (q.get("n"), did, fuente, d["fuente"],
                                                                      " · motivo: " + motivo if motivo else ""))
        if isinstance(d.get("anio"), int) and q.get("anio") != d["anio"]:
            rep("D5 T%s (%s): año %s y el canon dice %s%s" % (q.get("n"), did, q.get("anio"), d["anio"],
                                                            " · motivo: " + motivo if motivo else ""))
    omit = {str(o.get("canon")): str(o.get("motivo") or "").strip() for o in P.get("omitidas") or [] if isinstance(o, dict)}
    for did in dims:
        if did in vistos:
            continue
        if omit.get(did):
            av.append("D5 la dimensión %s del canon se omite: %s" % (did, omit[did]))
        else:
            f.append("D5 falta la dimensión «%s» del canon (%s); si no hay datos, va en perfil.omitidas con su motivo"
                     % (did, dims[did]["fuente"]))
    if P.get("canon_version") not in (None, C.get("version")):
        av.append("D5 el hilo usó el canon v%s; el vigente es v%s" % (P.get("canon_version"), C.get("version")))
    return f, av


def d6(g, st, hilo, cifras, C=None):
    f = []
    dep = st["departamento"]
    P = dep.get("puestos") or {}
    todos = sorted({p["puesto"] for p in P.values()})
    for i, e in enumerate((g.get("escenas") or []) + [g.get("cierre") or {}], 1):
        textos = " ".join(str(e.get(k) or "") for k in ("texto", "golpe", "pantalla", "linea"))
        dichos = {int(m.group(1)) for rx in RE_PUESTO for m in rx.finditer(textos)}
        if not dichos:
            continue
        t, _ = _cifras_de_escena(e, hilo, cifras)
        validos = sorted({P[k]["puesto"] for k in ((t or {}).get("cifra_ids") or []) + ["T%s" % e.get("tuit")] if k in P}) or todos
        for p in sorted(dichos):
            if p not in validos:
                f.append("D6 escena %d: dice el puesto %d y el calculado del desglose de los %d es %s"
                         % (i, p, N_DEPTOS, " o ".join(map(str, validos)) or "— (no hay desglose de los 22)"))
    # tasas por habitante: denominador INE del mismo año
    usadas = {c for t in hilo.get("tuits") or [] for c in t.get("cifra_ids") or []}
    for cid in sorted(usadas):
        c = cifras.get(cid) or {}
        if not RE_PER_CAPITA.search(str(c.get("unidad") or "")):
            continue
        txt = " ".join(str(c.get(k) or "") for k in ("denominador", "calculo", "fuente"))
        anio = str(c.get("anio") or c.get("periodo") or "")
        if not re.search(r"\bINE\b", txt):
            f.append("D6 %s es una tasa por habitante (%s) sin el denominador INE declarado (denominador o fuente)" % (cid, c.get("unidad")))
        elif anio and anio[:4] not in str(c.get("denominador") or txt):
            f.append("D6 %s: la tasa es de %s y el denominador no es de ese año («%s»)" % (cid, anio, c.get("denominador") or "—"))
    return f


def ventana_de(e):
    return bool(e.get("ventana"))


def d7(g, st, tarjetas, C=None):
    f = []
    cod = st["departamento"]["codigo"]
    escenas = g.get("escenas") or []
    mapas = [e for e in escenas if e.get("tipo") == "mapa"]
    rank = [e for e in escenas if e.get("tipo") == "ranking" and ventana_de(e)]
    if not mapas:
        f.append("D7 falta la escena `mapa` (el departamento destacado entre los 22)")
    if not rank:
        f.append("D7 falta un `ranking` con `ventana: true` (los 2 primeros, «…», %s y sus vecinos)" % nombre_de(cod, C))
    for e in mapas:
        dat = (tarjetas.get(e.get("tuit")) or {}).get("datos") or {}
        if resolver(dat.get("destacar"), C) != cod:
            f.append("D7 la tarjeta del mapa (T%s) no destaca a %s (destacar: %r)" % (e.get("tuit"), nombre_de(cod, C), dat.get("destacar")))
    for e in rank:
        dat = (tarjetas.get(e.get("tuit")) or {}).get("datos") or {}
        if not valores_22(dat, C):
            f.append("D7 el ranking en ventana (T%s) necesita una tarjeta con los %d departamentos" % (e.get("tuit"), N_DEPTOS))
        if e.get("destacar") and resolver(e["destacar"], C) != cod:
            f.append("D7 el ranking en ventana destaca %s y el video es de %s" % (e["destacar"], nombre_de(cod, C)))
    if mapas and rank and {e.get("tuit") for e in mapas} & {e.get("tuit") for e in rank}:
        f.append("D7 el mapa y el ranking usan la misma tarjeta: van dos desgloses distintos")
    return f


def d9(g, cod, C=None):
    VD = _vd()
    fin = VD.final_de(g.get("cierre") or {})
    if not nombra(fin, cod, C):
        return ["D9 la frase final del cierre no nombra %s («%s»)" % (nombre_de(cod, C), fin)]
    return []


def validar(g, st, datos, hilo, voz1=None, C=None):
    """D1–D7 y D9 sobre el guion del video (D8 corre en `tiempos`) → (faltas, avisos). `voz1` = la voz de la escena 1 en
    palabras (locucion); `st` = video.json con su bloque `departamento`."""
    C = C or canon()
    dep = st.get("departamento")
    if not dep:
        return [], []
    VD = _vd()
    cod = dep["codigo"]
    cifras = {c["id"]: c for c in datos.get("cifras") or []}
    tarjetas = {t["n"]: t for t in st.get("tarjetas") or []}
    escenas = g.get("escenas") or []
    f, av = [], []
    if escenas and voz1 is not None:
        f += d1(cod, voz1, C)
    if escenas:
        e1 = escenas[0]
        en_pantalla = any(nombra(x, cod, C) for x in VD.pantalla_escena1(e1))
        lugar = e1.get("visual") == "lugar" and resolver((e1.get("visual_datos") or {}).get("depto"), C) == cod
        if not (en_pantalla or lugar):
            f.append("D2 %s no se lee en la pantalla del gancho (pantalla, línea o golpe) ni es un visual `lugar` con %s"
                     % (nombre_de(cod, C), cod))
    f3, a3 = d3(cod, g.get("caption") or {}, C)
    f += f3
    av += a3
    f += d4(g, st, hilo, cifras, C)
    f5, a5 = d5(hilo, C)
    f += f5
    av += a5
    f += d6(g, st, hilo, cifras, C)
    f += d7(g, st, tarjetas, C)
    f += d9(g, cod, C)
    return f, av


# ---------- CLI ----------
def main(argv=None):
    p = argparse.ArgumentParser(description="Serie /departamento: canon, tablero y gates D1–D9 (referencias/flujo-departamento.md).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--resolver", metavar="NOMBRE")
    g.add_argument("--directiva", metavar="DEPTO")
    g.add_argument("--tablero", action="store_true")
    g.add_argument("--siguiente", action="store_true")
    g.add_argument("--check", action="store_true")
    p.add_argument("--memoria", metavar="DIR", help="carpeta con hilos.json y videos.json (defecto: memoria/)")
    p.add_argument("--canon", metavar="RUTA", help="canon alternativo (defecto: referencias/departamentos.json)")
    p.add_argument("--json", action="store_true", help="--tablero/--siguiente en JSON")
    a = p.parse_args(argv)
    C = canon(a.canon)
    if a.check:
        f = check(C)
        for x in f:
            print("FALLA", x)
        if f:
            return 1
        dims = C["dimensiones"]
        print("canon v%s ok · %d departamentos · %d dimensiones (%s) · %d en propuesta" % (
            C["version"], len(C["orden"]), len(dims), ", ".join(d["id"] for d in dims), sum(d["estado"] == "propuesta" for d in dims)))
        return 0
    if a.resolver is not None or a.directiva is not None:
        cod = resolver(a.resolver if a.resolver is not None else a.directiva, C)
        if not cod:
            print("no reconozco el departamento «%s» (nombre, alias o GT01–GT22)" % (a.resolver or a.directiva), file=sys.stderr)
            return 1
        print("%s %s" % (cod, nombre_de(cod, C)) if a.resolver is not None else directiva(cod, C))
        return 0
    if a.tablero:
        filas = tablero(a.memoria, C)
        if a.json:
            print(json.dumps(filas, ensure_ascii=False, indent=1))
            return 0
        print("%-3s %-5s %-16s %-10s %s" % ("#", "cód", "departamento", "hilo", "video"))
        for x in filas:
            print("%-3d %-5s %-16s %-10s %s" % (x["n"], x["codigo"], x["nombre"], x["hilo"], x["video"]))
        hechos_ = sum(1 for x in filas if x["video"] != "pendiente")
        print("— %d de %d con video · %d hilos perfil" % (hechos_, len(filas), sum(1 for x in filas if x["hilo"] == "hecho")))
        return 0
    if a.siguiente:
        x = siguiente(a.memoria, C)
        if not x:
            print("la serie está completa: los %d departamentos tienen video" % N_DEPTOS)
            return 0
        print(json.dumps(x, ensure_ascii=False) if a.json else "%s %s (n.º %d del orden · hilo %s)" % (x["codigo"], x["nombre"], x["n"], x["hilo"]))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
