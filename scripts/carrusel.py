#!/usr/bin/env python3
"""/carrusel: un hilo o un dato ya entregados → carrusel de 5–10 láminas 4:5 (1080×1350) para Instagram y Facebook, y
su versión 9:16 (1080×1920) para el modo foto de TikTok. Sin voz, sin créditos y sin agentes: el texto (carrusel.json)
lo escribe la sesión leyendo el digesto, como en /sabias.

Las láminas (templates/carrusel/lamina.html + carrusel.css) son cinco: `portada` (contexto, cifra grande, título y
«Desliza →»), `tarjeta` (la tarjeta N del original, rearmada en Noche, con un golpe arriba), `texto` (golpe + cuerpo),
`porque` («Por qué importa») y `cierre` (la frase final, «Guárdalo» y «Sígueme en»). Cada una lleva el contador n/N, la
fuente (menos el cierre) y el handle. Guía: referencias/flujo-carrusel.md.

Subcomandos (TRABAJO = sesiones/<slug>/carrusel):
  preparar <slug|ultimo|carpeta> [--trabajo DIR] [--fixture]
        resuelve el original (hilos/<fecha>-<slug>/ o datos/<fecha>-<slug>/; «ultimo» = el más reciente listo o
        publicado de los dos), exige estado listo|publicado (--fixture admite un borrador), copia lo que se lee a
        TRABAJO/base/, rearma las tarjetas en Noche (TRABAJO/tarjetas/) y escribe digesto.md (también lo imprime)
  digesto TRABAJO              vuelve a imprimir digesto.md
  guion TRABAJO --check        CA1–CA8 sobre TRABAJO/carrusel.json (CA8 solo avisa)
  render TRABAJO [--formato 4:5|9:16]   CA1–CA8 + scripts/carrusel.js (CA9–CA12) → TRABAJO/salida/lamina_NN.png
        (9:16: TRABAJO/salida/9x16/) y contacto.png
  entregar TRABAJO [--salida DIR]   → <carpeta del original>/carrusel/ (PNG, 9x16/, carrusel.json, caption.md, alt.md,
        contacto.png); un carrusel por original: rehacerlo lo reemplaza. Un TRABAJO de prueba (--fixture) solo se
        entrega con --salida.

Gates (en el script):
  CA1 estructura: 5–10 láminas; la 1.ª portada, la última cierre, la penúltima porque; ≥ 2 tarjeta|texto; cada
      tarjeta apunta a un tuit con imagen que no se repite; portada_forma ∈ cifra|pregunta|contraste|lista
  CA2 palabras: portada título ≤ 8 y cifra de 1 token; golpe ≤ 10; texto ≤ 30; porque ≤ 40; cierre ≤ 12
  CA3 palabra clave (1–3 palabras): en la portada, en ≥ 1 lámina más y en la 1.ª línea de los tres captions
  CA4 cada número con respaldo en datos.json (o en el `calculo` de su lámina); cifra_ids verificadas o ajustadas
  CA5 fuente en cada lámina menos el cierre
  CA6 prohibido en las láminas: «en suma», enlaces, emoji, «#», «Sígueme» fuera del cierre, frases de no_afirma
  CA7 captions sin enlaces, ≤ 5 hashtags, 1.ª línea de Instagram ≤ 125 caracteres; alt-text de 20–1000 por lámina
  CA8 (aviso) la forma de la portada repite la del carrusel anterior (memoria/carruseles.json)
Gates de página (scripts/carrusel.js): CA9 lienzo · CA10 miniatura · CA11 una cosa en acento y sin hex · CA12 pie.

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
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD  # noqa: E402
import sabias as SB  # noqa: E402  (resolver_dato, hilo_base: el dato como hilo de una tarjeta)
from ensamblar import RE_LINK, RE_EN_SUMA  # noqa: E402

TIPOS = ("portada", "tarjeta", "texto", "porque", "cierre")
FORMAS = ("cifra", "pregunta", "contraste", "lista")
LAMINAS = (5, 10)
PALABRAS = {"titulo": 8, "contexto": 10, "contra": 6, "golpe": 10, "texto": 30, "porque": 40, "cierre": 12}
CLAVE_PALABRAS = (1, 3)
HASHTAGS_MAX = 5
IG_PRIMERA_LINEA = 125
ALT = (20, 1000)
PLATAFORMAS = ("tiktok", "instagram", "facebook")
FORMATOS = {"4:5": (1080, 1350, ""), "9:16": (1080, 1920, "9x16")}
HANDLE = "@derekurizargt"      # el pie de cada lámina (Instagram y TikTok comparten el handle)
CARRUSELES = os.path.join(RAIZ, "memoria", "carruseles.json")
RE_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍⬀-⯿]")
RE_HASHTAG = re.compile(r"(?<![\w&])#\w+")
RE_SIGUEME = re.compile(r"s[ií]gue(me|nos)", re.I)


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def falla(msg):
    print("ERROR: " + msg, file=sys.stderr)
    return 1


def rel(p):
    return os.path.relpath(p, RAIZ)


def plano(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# ---------- el original ----------
def resolver(arg):
    """(tipo, carpeta) del original: un hilo (hilo.json) o un dato (dato.json). «ultimo» = el más reciente listo o
    publicado entre memoria/hilos.json y memoria/datos.json."""
    if arg == "ultimo":
        cands = []
        for reg, clave, tipo in (("hilos.json", "hilos", "hilo"), ("datos.json", "datos", "dato")):
            p = os.path.join(RAIZ, "memoria", reg)
            for r in (leer(p).get(clave) or []) if os.path.exists(p) else []:
                if r.get("estado") in ("listo", "publicado") and r.get("ruta") and os.path.isdir(os.path.join(RAIZ, r["ruta"])):
                    cands.append((r.get("fecha", ""), r.get("id", ""), tipo, os.path.join(RAIZ, r["ruta"])))
        return (sorted(cands)[-1][2], sorted(cands)[-1][3]) if cands else (None, None)
    for cand in (arg, os.path.join(RAIZ, arg)):
        if os.path.isfile(os.path.join(cand, "hilo.json")):
            return "hilo", os.path.abspath(cand)
        if os.path.isfile(os.path.join(cand, "dato.json")):
            return "dato", os.path.abspath(cand)
    h = VD.resolver_hilo(arg)
    if h:
        return "hilo", h
    d = SB.resolver_dato(arg)
    return ("dato", d) if d else (None, None)


def base_de_hilo(hilo, base):
    """TRABAJO/base/: lo que se lee del hilo (hilo.json, datos.json, tuit_N.html y sus PNG)."""
    os.makedirs(base, exist_ok=True)
    for f in ["hilo.json", "datos.json"] + [os.path.basename(x) for x in glob.glob(os.path.join(hilo, "tuit_*.*"))]:
        if f.endswith((".json", ".html", ".png")):
            shutil.copyfile(os.path.join(hilo, f), os.path.join(base, f))


def estado(trabajo):
    return leer(os.path.join(trabajo, "estado.json"))


def tuits_con_imagen(base):
    return {t["n"]: t for t in leer(os.path.join(base, "hilo.json"))["tuits"]
            if t.get("imagen") and os.path.exists(os.path.join(base, "tuit_%d.html" % t["n"]))}


def registrados(origen_ruta=None):
    regs = (leer(CARRUSELES).get("carruseles") or []) if os.path.exists(CARRUSELES) else []
    return sorted([r for r in regs if (r.get("origen") or {}).get("ruta") != origen_ruta],
                  key=lambda r: (r.get("fecha", ""), r.get("id", "")))


def cmd_preparar(a):
    tipo, orig = resolver(a.original)
    if not orig:
        return falla("no encuentro «%s» (slug de hilos/ o datos/, carpeta con hilo.json o dato.json, o «ultimo»)" % a.original)
    meta = leer(os.path.join(orig, "hilo.json" if tipo == "hilo" else "dato.json"))
    if meta.get("estado") not in ("listo", "publicado") and not a.fixture:
        return falla("el %s está «%s»: /carrusel solo convierte piezas listas o publicadas" % (tipo, meta.get("estado")))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", meta["slug"], "carrusel"))
    base = os.path.join(trabajo, "base")
    if os.path.isdir(base):
        shutil.rmtree(base)
    shutil.rmtree(os.path.join(trabajo, "tarjetas"), ignore_errors=True)
    if tipo == "hilo":
        base_de_hilo(orig, base)
    else:
        SB.hilo_base(orig, base)
        # la fuente de la tarjeta (el pie de la lámina): hilo_base no la copia
        h = leer(os.path.join(base, "hilo.json"))
        h["tuits"][0]["fuente"] = (meta.get("tuit") or {}).get("fuente") or ""
        escribir(os.path.join(base, "hilo.json"), h)
    # un hilo viejo sin cabecera de plantilla no se puede rearmar en Noche: se avisa y se bloquea
    sin_cabecera = []
    for n in sorted(tuits_con_imagen(base)):
        src = open(os.path.join(base, "tuit_%d.html" % n), encoding="utf-8").read()
        if not VD.RE_CABECERA_VISUAL.search(src) or not VD.RE_DATA_VISUAL.search(src):
            sin_cabecera.append("tuit_%d.html" % n)
    if sin_cabecera:
        return falla("%s sin cabecera «<!-- plantilla: … · paleta: … -->» o sin bloque DATA: es un %s anterior a "
                     "nuevo_visual.py y sus tarjetas no se pueden rearmar en Noche (rehazlo con /%s)"
                     % (", ".join(sin_cabecera), tipo, tipo))
    avisos = VD.rebasar_tarjetas(base, trabajo)
    if avisos:
        return falla("no pude rearmar las tarjetas en Noche: " + "; ".join(avisos))
    st = {"version": 1, "slug": meta["slug"], "origen": {"tipo": tipo, "ruta": rel(orig)}, "paleta": meta["paleta"],
          "fecha": datetime.date.today().isoformat(), "tema": meta.get("tema", ""), "fixture": bool(a.fixture)}
    escribir(os.path.join(trabajo, "estado.json"), st)
    texto = digesto(trabajo, st, meta, tipo)
    open(os.path.join(trabajo, "digesto.md"), "w", encoding="utf-8").write(texto)
    print(texto)
    if any((r.get("origen") or {}).get("ruta") == st["origen"]["ruta"] for r in registrados()):
        print("AVISO este %s ya tiene carrusel (memoria/carruseles.json): entregar lo reemplaza" % tipo)
    print("→ %s · trabajo: %s" % (rel(os.path.join(trabajo, "digesto.md")), rel(trabajo)))
    return 0


def digesto(trabajo, st, meta, tipo):
    base = os.path.join(trabajo, "base")
    valores, _tit, cifras = VD.valores_respaldo(base)
    hilo = leer(os.path.join(base, "hilo.json"))
    usadas, lineas = set(), []
    for t in hilo["tuits"]:
        ids = [i for i in t.get("cifra_ids") or [] if i]
        usadas |= set(ids)
        html = os.path.join(trabajo, "tarjetas", "tuit_%d.html" % t["n"])
        kicker, titular, _ = VD.titular_de(html) if os.path.exists(html) else ("", "", False)
        lineas += ["### T%d · %s · %s%s" % (t["n"], t.get("beat", ""), t.get("plantilla") or "sin imagen",
                                            "" if t.get("imagen") else " (no sirve como lámina `tarjeta`)")]
        if titular:
            lineas.append("- Tarjeta: %s — «%s»" % (kicker, titular))
        lineas += ["- Texto: %s" % (t.get("texto") or "—").replace("\n", " "), "- Alt: %s" % (t.get("alt_text") or "—"),
                   "- Fuente: %s" % (t.get("fuente") or "—")]
        lineas += ["- %s" % linea_cifra(i, cifras[i]) for i in ids if i in cifras]
    sobrantes = [linea_cifra(i, c) for i, c in cifras.items() if i not in usadas]
    prev = registrados(st["origen"]["ruta"])
    ultima = (prev[-1].get("portada_forma") if prev else None)
    return "\n".join([
        "# Digesto para el carrusel · %s" % st["slug"], "",
        "- Original: %s (%s) · estado %s · paleta %s" % (st["origen"]["ruta"], tipo, meta.get("estado"), st["paleta"]),
        "- Tema: %s" % meta.get("tema", ""), "- Tesis: %s" % meta.get("tesis", ""),
        "- No afirma (ninguna lámina lo dice; CA6): %s" % ("; ".join(meta.get("no_afirma") or []) or "—"),
        "- Forma de la última portada: %s%s" % (ultima or "ninguna (primer carrusel)",
                                               " (CA8: usa otra de %s)" % "|".join(f for f in FORMAS if f != ultima) if ultima else ""),
        "", "## Tuits (las láminas `tarjeta` usan los que tienen imagen)"] + lineas + [
        "", "## Cifras verificadas que no usa ninguna tarjeta (para portada, texto o porque)"] +
        (["- " + x for x in sobrantes] or ["- ninguna"]) + [
        "", "## Anatomía (CA1–CA8)",
        "- %d–%d láminas: 1.ª `portada`, última `cierre`, penúltima `porque`; en medio ≥ 2 `tarjeta` (tuit con imagen, "
        "sin repetir) o `texto`." % LAMINAS,
        "- `portada`: `contexto` (≤ %d palabras: el tema y el año), `cifra` (1 token: «0.95», «Q2,300»), `titulo` (≤ %d "
        "palabras, legible en miniatura), `fuente`; `portada_forma`: cifra (cifra + título) | pregunta (el título "
        "termina en «?») | contraste (`contra`: el antes, ≤ %d palabras) | lista (el título empieza con el número de "
        "puntos)." % (PALABRAS["contexto"], PALABRAS["titulo"], PALABRAS["contra"]),
        "- `tarjeta`: `tuit` N y `golpe` (≤ %d palabras, no repite el titular: lo dice de otra forma o añade el porqué); la "
        "fuente es la del tuit." % PALABRAS["golpe"],
        "- `texto`: `golpe` (≤ %d) + `cuerpo` (≤ %d) + `fuente`. `porque`: `cuerpo` (≤ %d, qué cambia para la gente) + "
        "`fuente`. `cierre`: `frase` (≤ %d; la consecuencia, no el dato otra vez); «Guárdalo» y «Sígueme en» los pone "
        "la plantilla." % (PALABRAS["golpe"], PALABRAS["texto"], PALABRAS["porque"], PALABRAS["cierre"]),
        "- Cada número de una lámina con respaldo en las cifras de arriba (CA4); un derivado lleva `calculo` en su "
        "lámina («sal-c11 * 100», lista si hay varios). `cifra_ids` opcional por lámina (verificadas o ajustadas).",
        "- `palabra_clave` (1–3 palabras, la que la gente busca: «canasta básica»): en la portada, en otra lámina y en la "
        "1.ª línea de los captions de tiktok, instagram y facebook (CA3).",
        "- Prohibido en las láminas: «en suma», enlaces, emoji, «#», «Sígueme» fuera del cierre (CA6).",
        "- Captions sin enlaces, ≤ %d hashtags; la 1.ª línea de Instagram ≤ %d caracteres (lo que se ve sin «más»). "
        "`alt`: un texto de %d–%d caracteres por lámina (clave = número de lámina; una `tarjeta` sin alt usa el del "
        "tuit)." % (HASHTAGS_MAX, IG_PRIMERA_LINEA, ALT[0], ALT[1]),
        "", "## Plantilla de carrusel.json", "```json",
        json.dumps({"version": 1, "origen": st["origen"], "slug": st["slug"], "paleta": st["paleta"],
                    "palabra_clave": "<1–3 palabras>", "portada_forma": "cifra", "laminas": [
                        {"tipo": "portada", "contexto": "<tema · año>", "cifra": "<1 token>", "titulo": "<≤ 8 palabras>",
                         "fuente": "<fuente>", "cifra_ids": ["<id>"]},
                        {"tipo": "tarjeta", "tuit": 1, "golpe": "<≤ 10 palabras>"},
                        {"tipo": "texto", "golpe": "<≤ 10>", "cuerpo": "<≤ 30>", "fuente": "<fuente>"},
                        {"tipo": "porque", "cuerpo": "<≤ 40>", "fuente": "<fuente>"},
                        {"tipo": "cierre", "frase": "<≤ 12>"}],
                    "caption": {"tiktok": "<palabra clave …>", "instagram": "<palabra clave … (1.ª línea ≤ 125)>",
                                "facebook": "<palabra clave …>"},
                    "alt": {"1": "<20–1000 caracteres>"}}, ensure_ascii=False, indent=1), "```", ""])


def linea_cifra(cid, c):
    serie = ", ".join("%s: %s" % (p.get("p"), p.get("v")) for p in (c.get("serie") or [])[-9:])
    partes = ", ".join("%s: %s" % (p.get("nombre", p.get("etiqueta", "")), p.get("valor")) for p in c.get("partes") or [])
    return "%s: %s = %s %s (%s)%s%s" % (cid, c.get("concepto", ""), c.get("valor"), c.get("unidad", ""),
                                       c.get("periodo") or c.get("anio", ""), " · serie: " + serie if serie else "",
                                       " · partes: " + partes if partes else "")


def cmd_digesto(a):
    print(open(os.path.join(os.path.abspath(a.trabajo), "digesto.md"), encoding="utf-8").read())
    return 0


# ---------- gate CA1–CA8 ----------
def textos_lamina(l):
    """(campo, texto) visibles de una lámina (lo que se lee en la imagen)."""
    campos = {"portada": ("contexto", "cifra", "contra", "titulo"), "tarjeta": ("golpe",), "texto": ("golpe", "cuerpo"),
              "porque": ("cuerpo",), "cierre": ("frase",)}.get(l.get("tipo"), ())
    return [(k, str(l.get(k))) for k in campos if l.get(k)]


def fuente_de(l, tuits):
    if l.get("tipo") == "tarjeta":
        return l.get("fuente") or (tuits.get(l.get("tuit")) or {}).get("fuente") or ""
    return l.get("fuente") or ""


def alt_de(c, k, l, tuits):
    alt = (c.get("alt") or {}).get(str(k))
    if not alt and l.get("tipo") == "tarjeta":
        alt = (tuits.get(l.get("tuit")) or {}).get("alt_text")
    return alt or ""


def afirmaciones_vetadas(no_afirma):
    """La afirmación de cada «No afirma que …» (normalizada, ≥ 4 palabras): ninguna lámina la puede decir."""
    out = []
    for x in no_afirma or []:
        s = re.split(r"[:;(]", re.sub(r"^\s*no\s+afirma\s+(que\s+|cu[aá]nto\s+|el\s+|la\s+)?", "", str(x), flags=re.I))[0]
        s = plano(s)
        if len(s.split()) >= 4:
            out.append(s)
    return out


def validar(trabajo):
    """CA1–CA8 → (faltas, avisos, carrusel, tuits)."""
    st = estado(trabajo)
    ruta = os.path.join(trabajo, "carrusel.json")
    if not os.path.exists(ruta):
        return ["CA1 falta %s (lo escribe la sesión con el digesto)" % rel(ruta)], [], None, {}
    try:
        c = leer(ruta)
    except json.JSONDecodeError as ex:
        return ["CA1 carrusel.json no es JSON válido: %s" % ex], [], None, {}
    base = os.path.join(trabajo, "base")
    tuits = tuits_con_imagen(base)
    meta = leer(os.path.join(base, "hilo.json"))
    f, av = [], []
    L = c.get("laminas") or []
    tipos = [l.get("tipo") for l in L]
    # CA1 estructura
    if (c.get("origen") or {}).get("ruta") != st["origen"]["ruta"]:
        f.append("CA1 origen.ruta «%s» no es el original preparado (%s)" % ((c.get("origen") or {}).get("ruta"), st["origen"]["ruta"]))
    if not LAMINAS[0] <= len(L) <= LAMINAS[1]:
        f.append("CA1 %d láminas: van %d–%d" % (len(L), *LAMINAS))
    for k, t in enumerate(tipos, 1):
        if t not in TIPOS:
            f.append("CA1 lámina %d: tipo %r (%s)" % (k, t, "|".join(TIPOS)))
    if L:
        if tipos[0] != "portada":
            f.append("CA1 la lámina 1 es la portada (llegó %s)" % tipos[0])
        if tipos[-1] != "cierre":
            f.append("CA1 la última lámina es el cierre (llegó %s)" % tipos[-1])
        if len(L) >= 2 and tipos[-2] != "porque":
            f.append("CA1 la penúltima lámina es «porque» (Por qué importa; llegó %s)" % tipos[-2])
    for t in ("portada", "porque", "cierre"):
        if tipos.count(t) > 1:
            f.append("CA1 una sola lámina %s (hay %d)" % (t, tipos.count(t)))
    if sum(t in ("tarjeta", "texto") for t in tipos) < 2:
        f.append("CA1 hacen falta ≥ 2 láminas tarjeta|texto entre la portada y el porqué")
    vistos = set()
    for k, l in enumerate(L, 1):
        if l.get("tipo") != "tarjeta":
            continue
        n = l.get("tuit")
        if n not in tuits:
            f.append("CA1 lámina %d: el tuit %r no existe o no tiene imagen (hay: %s)" % (k, n, ", ".join(map(str, sorted(tuits)))))
        elif n in vistos:
            f.append("CA1 lámina %d: el tuit %d ya salió en otra lámina" % (k, n))
        vistos.add(n)
    forma = c.get("portada_forma")
    if forma not in FORMAS:
        f.append("CA1 portada_forma %r (%s)" % (forma, "|".join(FORMAS)))
    portada = L[0] if L and tipos[0] == "portada" else {}
    if portada:
        if forma in ("cifra", "contraste") and not portada.get("cifra"):
            f.append("CA1 portada de forma %s sin `cifra`" % forma)
        if forma == "pregunta" and not str(portada.get("titulo") or "").strip().endswith("?"):
            f.append("CA1 portada de forma pregunta: el título termina en «?»")
        if forma == "contraste" and not portada.get("contra"):
            f.append("CA1 portada de forma contraste sin `contra` (el antes con el que se compara)")
        if forma == "lista" and not re.match(r"^\s*\d+\b", str(portada.get("titulo") or "")):
            f.append("CA1 portada de forma lista: el título empieza con el número de puntos («5 cosas que…»)")
        if not portada.get("titulo"):
            f.append("CA1 la portada no tiene `titulo`")
    # CA2 palabras
    for k, l in enumerate(L, 1):
        for campo, txt in textos_lamina(l):
            lim = PALABRAS["porque" if l.get("tipo") == "porque" else "cierre" if l.get("tipo") == "cierre" else
                           "texto" if campo == "cuerpo" else campo] if campo != "cifra" else 1
            n = len(txt.split())
            if n > lim:
                f.append("CA2 lámina %d (%s.%s): %d palabras, máximo %d%s" % (k, l.get("tipo"), campo, n, lim,
                                                                           " (un solo token: «0.95», «Q2,300»)" if campo == "cifra" else ""))
        if l.get("tipo") == "tarjeta" and not l.get("golpe"):
            f.append("CA2 lámina %d (tarjeta): falta `golpe` (≤ %d palabras sobre la tarjeta)" % (k, PALABRAS["golpe"]))
        if l.get("tipo") in ("texto",) and not (l.get("golpe") and l.get("cuerpo")):
            f.append("CA2 lámina %d (texto): lleva `golpe` y `cuerpo`" % k)
        if l.get("tipo") == "porque" and not l.get("cuerpo"):
            f.append("CA2 lámina %d (porque): falta `cuerpo`" % k)
        if l.get("tipo") == "cierre" and not l.get("frase"):
            f.append("CA2 lámina %d (cierre): falta `frase`" % k)
    # CA3 palabra clave
    clave = c.get("palabra_clave")
    claves = VD.palabras_clave(clave)
    if not claves:
        f.append("CA3 falta `palabra_clave` (1–3 palabras, la que la gente busca)")
    else:
        for x in claves:
            if not CLAVE_PALABRAS[0] <= len(x.split()) <= CLAVE_PALABRAS[1]:
                f.append("CA3 palabra clave «%s»: %d palabras (van %d–%d)" % (x, len(x.split()), *CLAVE_PALABRAS))
        f += VD.revisar_palabra_clave(claves, None, [t for _, t in textos_lamina(portada)], c.get("caption") or {},
                                      plataformas=PLATAFORMAS, codigo="CA3", donde="la portada")
        otras = [t for l in L[1:] for _, t in textos_lamina(l)]
        if not any(VD._busca_clave(VD._tokens_clave(t), claves) is not None for t in otras):
            f.append("CA3 la palabra clave «%s» solo está en la portada: va también en ≥ 1 lámina más" % "» / «".join(claves))
    # CA4 cifras con respaldo
    valores, _tit, cifras = VD.valores_respaldo(base)
    for k, l in enumerate(L, 1):
        extra = []
        calc = l.get("calculo")
        for expr in ([calc] if isinstance(calc, str) else calc or []):
            r, motivo = VD.resolver_calculo(expr, cifras, valores)
            if motivo:
                f.append("CA4 lámina %d: calculo «%s» %s" % (k, expr, motivo))
            else:
                extra.append(r)
        for cid in l.get("cifra_ids") or []:
            if cid not in cifras:
                f.append("CA4 lámina %d: cifra_ids %s no existe o no está verificada|ajustada" % (k, cid))
        # el alt heredado del tuit ya pasó el gate del original (G10); el propio se coteja aquí
        for campo, txt in textos_lamina(l) + [("alt", (c.get("alt") or {}).get(str(k)) or "")]:
            sin = VD.sin_respaldo(txt, valores, extra)
            if sin:
                f.append("CA4 lámina %d (%s): %s sin respaldo en datos.json (usa la cifra verificada o declara `calculo`)"
                         % (k, campo, ", ".join(sin)))
    # CA5 fuente
    for k, l in enumerate(L, 1):
        if l.get("tipo") in TIPOS and l.get("tipo") != "cierre" and not fuente_de(l, tuits).strip():
            f.append("CA5 lámina %d (%s) sin fuente" % (k, l.get("tipo")))
    # CA6 prohibido en las láminas
    vetadas = afirmaciones_vetadas(meta.get("no_afirma"))
    for k, l in enumerate(L, 1):
        for campo, txt in textos_lamina(l) + [("fuente", fuente_de(l, tuits))]:
            donde = "CA6 lámina %d (%s)" % (k, campo)
            if RE_EN_SUMA.search(txt):
                f.append("%s dice «en suma»: está vetado" % donde)
            if RE_LINK.search(txt):
                f.append("%s lleva un enlace" % donde)
            if RE_EMOJI.search(txt):
                f.append("%s lleva emoji" % donde)
            if "#" in txt:
                f.append("%s lleva «#»: los hashtags van en el caption" % donde)
            if RE_SIGUEME.search(txt):
                f.append("%s dice «Sígueme»: va solo en el cierre y lo pone la plantilla" % donde)
            p = plano(txt)
            for v in vetadas:
                if v in p:
                    f.append("%s dice lo que el original no afirma: «%s»" % (donde, v))
    # CA7 captions y alt
    cap = c.get("caption") or {}
    for p in PLATAFORMAS:
        t = str(cap.get(p) or "")
        if not t.strip():
            f.append("CA7 falta caption.%s" % p)
            continue
        if RE_LINK.search(t):
            f.append("CA7 caption.%s lleva un enlace (las plataformas no los abren en el texto)" % p)
        if len(RE_HASHTAG.findall(t)) > HASHTAGS_MAX:
            f.append("CA7 caption.%s: %d hashtags, máximo %d" % (p, len(RE_HASHTAG.findall(t)), HASHTAGS_MAX))
        if RE_EN_SUMA.search(t):
            f.append("CA7 caption.%s dice «en suma»" % p)
    l1 = next((x for x in str(cap.get("instagram") or "").splitlines() if x.strip()), "")
    if len(l1) > IG_PRIMERA_LINEA:
        f.append("CA7 caption.instagram: la 1.ª línea tiene %d caracteres, máximo %d (lo que se ve sin «más»)"
                 % (len(l1), IG_PRIMERA_LINEA))
    for k, l in enumerate(L, 1):
        n = len(alt_de(c, k, l, tuits).strip())
        if not ALT[0] <= n <= ALT[1]:
            f.append("CA7 alt de la lámina %d: %d caracteres (van %d–%d)" % (k, n, *ALT))
    # CA8 rotación de la forma (aviso)
    prev = registrados(st["origen"]["ruta"])
    if not st.get("fixture") and prev and prev[-1].get("portada_forma") == forma:
        av.append("CA8 la portada repite la forma «%s» del carrusel anterior (%s): prueba %s"
                  % (forma, prev[-1].get("slug"), "|".join(x for x in FORMAS if x != forma)))
    return f, av, c, tuits


def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    f, av, c, _ = validar(trabajo)
    for x in av:
        print("AVISO " + x)
    for x in f:
        print("FALLA " + x)
    if f:
        print("[carrusel] %d falla(s) · %d aviso(s)" % (len(f), len(av)))
        return 1
    L = c["laminas"]
    print("[carrusel] OK · %d láminas (%s) · palabra clave «%s» · portada %s"
          % (len(L), " → ".join(l["tipo"] for l in L), " / ".join(VD.palabras_clave(c["palabra_clave"])), c["portada_forma"]))
    return 0


# ---------- render ----------
def laminas_json(trabajo, c, tuits, formato):
    st = estado(trabajo)
    L = c["laminas"]
    out = []
    for k, l in enumerate(L, 1):
        x = {key: l.get(key) for key in ("tipo", "contexto", "cifra", "contra", "titulo", "tuit", "golpe", "cuerpo", "frase") if l.get(key) is not None}
        x.update(n=k, total=len(L), fuente=fuente_de(l, tuits))
        out.append(x)
    return {"version": 1, "formato": formato, "slug": st["slug"], "colores": VD.colores(c.get("paleta") or st["paleta"]),
            "handle": HANDLE, "redes": [r for r in VD.REDES if r["red"] in ("tiktok", "instagram", "facebook", "x")],
            "laminas": out}


def cmd_render(a):
    trabajo = os.path.abspath(a.trabajo)
    f, av, c, tuits = validar(trabajo)
    for x in av:
        print("AVISO " + x)
    if f:
        for x in f:
            print("FALLA " + x)
        return falla("carrusel.json no pasa CA1–CA8: corrige y repite `guion --check`")
    w, h, sub = FORMATOS[a.formato]
    sal = os.path.join(trabajo, "salida", sub) if sub else os.path.join(trabajo, "salida")
    os.makedirs(sal, exist_ok=True)
    for viejo in glob.glob(os.path.join(sal, "lamina_*.png")):
        os.remove(viejo)
    escribir(os.path.join(trabajo, "laminas.json"), laminas_json(trabajo, c, tuits, a.formato))
    rc = subprocess.run(["node", os.path.join(RAIZ, "scripts", "carrusel.js"), "--dir", trabajo, "--formato", a.formato,
                         "--out", sal, "--check"], cwd=RAIZ).returncode
    if rc:
        return falla("carrusel.js salió con %d (CA9–CA12 o error de página)" % rc)
    rc = subprocess.run(["node", os.path.join(RAIZ, "scripts", "contacto.js"), sal, "--prefijo", "lamina_",
                         "--celda", "360"], cwd=RAIZ, capture_output=True, text=True)
    if rc.returncode:
        return falla("contacto.js: " + (rc.stderr or rc.stdout).strip())
    print("→ %s (%d láminas %dx%d) · %s" % (rel(sal), len(c["laminas"]), w, h, rel(os.path.join(sal, "contacto.png"))))
    return 0


# ---------- entregar ----------
def caption_md(c, st):
    partes = ["# Caption · carrusel %s" % st["slug"], "",
              "Palabra clave: %s · %d láminas · 4:5 (Instagram y Facebook) y 9:16 (TikTok, modo foto)."
              % (" / ".join(VD.palabras_clave(c["palabra_clave"])), len(c["laminas"])),
              "Sonido: elige el sonido en la app (TikTok e Instagram sugieren los que están en tendencia; el carrusel no "
              "trae audio).", ""]
    for p, nombre in (("instagram", "Instagram"), ("facebook", "Facebook"), ("tiktok", "TikTok (modo foto: 9x16/)")):
        partes += ["## %s" % nombre, "", c["caption"][p].strip(), ""]
    return "\n".join(partes)


def alt_md(c, tuits):
    partes = ["# Texto alternativo por lámina", ""]
    for k, l in enumerate(c["laminas"], 1):
        partes.append("- **Lámina %d** (%s): %s" % (k, l["tipo"], alt_de(c, k, l, tuits).strip()))
    return "\n".join(partes) + "\n"


def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    if st.get("fixture") and not a.salida:
        return falla("TRABAJO de prueba (--fixture): solo se entrega con --salida (nunca sobre el original)")
    f, _av, c, tuits = validar(trabajo)
    if f:
        return falla("carrusel.json no pasa CA1–CA8 (%d fallas): `guion --check`" % len(f))
    sal = os.path.join(trabajo, "salida")
    pngs = sorted(glob.glob(os.path.join(sal, "lamina_*.png")))
    if len(pngs) != len(c["laminas"]):
        return falla("salida/ tiene %d láminas y carrusel.json %d: corre `render` (4:5) antes de entregar" % (len(pngs), len(c["laminas"])))
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, st["origen"]["ruta"], "carrusel"))
    if os.path.isdir(destino):
        shutil.rmtree(destino)   # un carrusel por original: rehacerlo lo reemplaza
    os.makedirs(destino)
    for p in pngs + [os.path.join(sal, "contacto.png")]:
        shutil.copyfile(p, os.path.join(destino, os.path.basename(p)))
    formatos = ["4:5"]
    v = sorted(glob.glob(os.path.join(sal, "9x16", "lamina_*.png")))
    if len(v) == len(c["laminas"]):
        os.makedirs(os.path.join(destino, "9x16"))
        for p in v:
            shutil.copyfile(p, os.path.join(destino, "9x16", os.path.basename(p)))
        formatos.append("9:16")
    elif v:
        print("AVISO salida/9x16 tiene %d láminas de %d: no se entrega el 9:16" % (len(v), len(c["laminas"])))
    ent = dict(c, tipo="carrusel", id="carrusel-%s" % st["slug"], fecha=st["fecha"], tema=st.get("tema", ""),
               n_laminas=len(c["laminas"]), formatos=formatos, fixture=bool(st.get("fixture")),
               alt={str(k): alt_de(c, k, l, tuits) for k, l in enumerate(c["laminas"], 1)})
    escribir(os.path.join(destino, "carrusel.json"), ent)
    open(os.path.join(destino, "caption.md"), "w", encoding="utf-8").write(caption_md(c, st))
    open(os.path.join(destino, "alt.md"), "w", encoding="utf-8").write(alt_md(c, tuits))
    print("→ %s (%d láminas · %s)" % (rel(destino), len(c["laminas"]), " + ".join(formatos)))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("preparar")
    q.add_argument("original", help="slug de hilos/ o datos/, carpeta con hilo.json o dato.json, o «ultimo»")
    q.add_argument("--trabajo")
    q.add_argument("--fixture", action="store_true", help="pruebas: admite un borrador; solo se entrega con --salida")
    sub.add_parser("digesto").add_argument("trabajo")
    q = sub.add_parser("guion")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true", required=True)
    q = sub.add_parser("render")
    q.add_argument("trabajo")
    q.add_argument("--formato", choices=sorted(FORMATOS), default="4:5")
    q = sub.add_parser("entregar")
    q.add_argument("trabajo")
    q.add_argument("--salida")
    a = p.parse_args()
    return {"preparar": cmd_preparar, "digesto": cmd_digesto, "guion": cmd_guion, "render": cmd_render,
            "entregar": cmd_entregar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
