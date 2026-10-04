#!/usr/bin/env python3
"""Ensambla la carpeta de entrega de un hilo desde su sesión y aplica el gate mecánico.

Entrada:  sesiones/<slug>/  con guion.json (obligatorio), encuadre.json,
          hallazgos_<eje>.json, verificacion_<eje>.json y visuales/tuit_N.{html,png}
Salida:   hilos/<fecha>-<slug>/ (o --salida DIR; en smoke/fixture <sesion>/salida/) con
          hilo.json · datos.json · post.md · hilo.html · contacto.png · tuit_N.html · tuit_N.png

--check aplica el GATE MECÁNICO antes de escribir (si falla, no escribe y sale 1):
  G1 estructura: 3–21 tuits numerados 1..n; T1 gancho, Tn cierre, un solo giro;
     en modo normal con ≥5 tuits, un beat impacto
  G2 textos (peso X: URL=23, emoji=2): T1 40–280, primera línea ≤ 90, sin enlace;
     todos ≤ 280; T2..T(n−1) con imagen ≤ 200; sin engagement bait; alt_text 20–1000;
     dato héroe: el texto no repite una línea del titular ni ≥2 números de su tarjeta
  G3 visuales: obligatorios en T2..T(n−1); plantilla del catálogo; kicker ≤ 45;
     titular 1–3 líneas de ≤ 26; nota ≤ 150; fuente 1–70 sin «Fuente:»; sin URLs;
     cifra_ids no vacío y ⊆ cifras verificadas|ajustadas
  G4 C3 mecánico: todo número de visual.datos (según la plantilla) existe en las
     cifras referenciadas (valor_final, puntos de serie o partes del desglose)
  G5 archivos: tuit_N.html y .png existen, sin ajustes sin consolidar; el HTML
     contiene el kicker y la fuente
  G6 paleta: ∈ design/tokens.json y == encuadre.paleta
  G7 superlativos («récord», «histórico»…) solo con una serie ≥ 10 puntos en las
     cifras del tuit cuyo máximo sea el valor
  G8 el cierre nombra la fuente corta de cada tarjeta

--estado borrador|listo|incompleto  estado que se escribe en hilo.json, hilo.html y post.md (default borrador).
--solo-estado  no ensambla ni renderiza: solo reescribe el estado (exige --estado) en la
               carpeta de entrega ya existente. Lo corre el productor tras el gate C1–C8.

Uso: python3 scripts/ensamblar.py sesiones/<slug> [--salida DIR] [--check] [--fecha YYYY-MM-DD] [--forzar] [--sin-contacto]
     python3 scripts/ensamblar.py sesiones/<slug> --solo-estado --estado listo|incompleto
Salida: 0 ok · 1 gate fallido o error · 2 uso incorrecto
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
try:
    from contar_x import peso_x  # noqa: E402
except Exception:  # pragma: no cover - antes de que exista contar_x.py
    def peso_x(t):
        return len(t or "")

BEATS = ["gancho", "contexto", "giro", "impacto", "cierre"]
HOOKS = ["giro_inversion", "escala_humana", "brecha_territorial", "pregunta_directa", "curiosity_gap", "mito_vs_dato", "antes_despues", "titular_clasico"]
RE_LINK = re.compile(r"https?://|www\.|\.com\b|\.gt\b", re.I)
RE_BAIT = re.compile(r"(dale|da|dame|dejen?)\s+(rt|like|me gusta)|s[ií]gue(me|nos)|retuitea|comparte si|like si|guarda este|no te lo pierdas", re.I)
RE_SUPER = re.compile(r"r[ée]cord|hist[óo]ric[oa]|m[áa]s alt[oa] de la historia|nunca antes", re.I)
# Claves de visual.datos que son DATOS (se cotejan contra las cifras); el resto es presentación.
CLAVES_DATO = {
    "linea": lambda d: [v for s in d.get("series", []) for v in s.get("valores", []) if v is not None],
    "barras-v": lambda d: list(d.get("valores", [])) + ([d["referencia"]["valor"]] if d.get("referencia") else []),
    "barras-h": lambda d: [it.get("valor") for it in d.get("items", [])],
    "antes-despues": lambda d: [d.get("antes", {}).get("valor"), d.get("despues", {}).get("valor")],
    "dona": lambda d: [p.get("valor") for p in d.get("partes", [])] + ([d["centro"]["valor"]] if isinstance(d.get("centro", {}).get("valor"), (int, float)) else []),
    "pendiente": lambda d: [v for it in d.get("items", []) for v in (it.get("a"), it.get("b"))],
    "pesas": lambda d: [v for it in d.get("items", []) for v in (it.get("a"), it.get("b"))],
    "waffle": lambda d: [d.get("porcentaje"), d.get("cifra", {}).get("valor")],
    "cifra": lambda d: [d.get("cifra", {}).get("valor")] + ([d["comparacion"]["valor"]] if d.get("comparacion") else []),
    "mapa": lambda d: [v for v in (d.get("valores") or {}).values() if v is not None],
    "calor": lambda d: [v for fila in (d.get("valores") or []) for v in fila if v is not None],
    # bullet: una meta de 100 (el total, p. ej. 100 % del presupuesto) es definición, no cifra; las demás se cotejan.
    "bullet": lambda d: [it.get("valor") for it in d.get("items", [])] + [m for m in [it.get("meta") for it in d.get("items", [])] + [d.get("meta")] if isinstance(m, (int, float)) and m != 100],
    "embudo": lambda d: [e.get("valor") for e in d.get("etapas", [])],
    "divergente": lambda d: [it.get("valor") for it in d.get("items", [])],
    "apilada": lambda d: [v for p in d.get("partes", []) for v in p.get("valores", [])],
    "piramide": lambda d: list((d.get("izquierda") or {}).get("valores", [])) + list((d.get("derecha") or {}).get("valores", [])),
    "treemap": lambda d: [p.get("valor") for p in d.get("partes", [])],
    "dispersion": lambda d: [v for p in d.get("puntos", []) for v in (p.get("x"), p.get("y"))] + [(d.get("guias") or {}).get(k) for k in ("x", "y")],
}
CLAVES_PRESENTACION = {"decimales", "escala", "destacar", "clases", "decimales_pildora", "i", "fila", "col", "miles", "cortes", "maximo", "minimo_rotulo", "desde", "hasta"}


def leer(ruta, obligatorio=False):
    if not os.path.exists(ruta):
        if obligatorio:
            raise SystemExit("ERROR: falta %s" % ruta)
        return None
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def catalogo_plantillas():
    return {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(RAIZ, "templates", "graficos", "*.html"))}


def cargar_sesion(sesion):
    guion = leer(os.path.join(sesion, "guion.json"), obligatorio=True)
    encuadre = leer(os.path.join(sesion, "encuadre.json"))
    cifras, veredictos, fuentes = {}, {}, {}
    for ruta in sorted(glob.glob(os.path.join(sesion, "hallazgos_*.json"))):
        h = leer(ruta)
        for c in h.get("cifras", []):
            if c["id"] in cifras:
                raise SystemExit("ERROR: id de cifra duplicado entre ejes: %s (en %s)" % (c["id"], os.path.basename(ruta)))
            cifras[c["id"]] = c
        for f in h.get("fuentes", []):
            fuentes[f.get("nombre")] = f
    for ruta in sorted(glob.glob(os.path.join(sesion, "verificacion_*.json"))):
        v = leer(ruta)
        for it in (v.get("items") or v.get("cifras") or []):
            veredictos[it["id"]] = it
    return guion, encuadre, cifras, veredictos, fuentes


def valores_de(cifra, veredicto):
    """Conjunto de números que una cifra 'contiene' (valor final, serie, partes)."""
    vals = set()
    vf = veredicto.get("valor_final") if veredicto else None
    for v in (vf, cifra.get("valor")):
        if isinstance(v, (int, float)):
            vals.add(round(float(v), 6))
    for p in cifra.get("serie", []) or []:
        if isinstance(p.get("v"), (int, float)):
            vals.add(round(float(p["v"]), 6))
    for p in cifra.get("partes", []) or []:
        if isinstance(p.get("valor"), (int, float)):
            vals.add(round(float(p["valor"]), 6))
    return vals


def numeros_de(d):
    """Todos los números 'de dato' de visual.datos (excluye claves de presentación)."""
    out = []

    def rec(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            out.append(x)
        elif isinstance(x, list):
            for y in x:
                rec(y)
        elif isinstance(x, dict):
            for k, y in x.items():
                if k not in CLAVES_PRESENTACION:
                    rec(y)
    rec(d)
    return out


def fmt_num(v):
    if isinstance(v, float) and not v.is_integer():
        return ("%.6f" % v).rstrip("0").rstrip(".")
    return "{:,}".format(int(v)) if isinstance(v, (int, float)) else str(v)


def formas(v):
    """Formas en que un número puede aparecer escrito en un tuit."""
    a = abs(float(v))
    out = {fmt_num(v), str(v), ("%.2f" % a).rstrip("0").rstrip("."), ("%.1f" % a)}
    if a.is_integer():
        out |= {str(int(a)), "{:,}".format(int(a))}
    return {x for x in out if x and x not in ("0", "0.0")}


def aparece_en_texto(v, texto):
    return any(re.search(r"(?<![\d.,])" + re.escape(x) + r"(?!\d|[.,]\d)", texto) for x in formas(v))


def fuente_corta(fuente):
    return re.split(r"\s+[·—–]\s+|,|\s+/\s+|\(", fuente or "", maxsplit=1)[0].strip()


MAX_TUITS = 21  # igual que hilo.js


def gate(guion, encuadre, cifras, veredictos, sesion, plantillas, paletas):
    F, W = [], []
    tuits = guion.get("tuits", [])
    n = len(tuits)
    smoke = bool(guion.get("smoke") or (encuadre or {}).get("smoke") or (encuadre or {}).get("fixture"))
    ok_ids = {i for i, v in veredictos.items() if v.get("veredicto") in ("verificada", "ajustada")}
    # G1
    if not (3 if smoke else 4) <= n <= MAX_TUITS:
        F.append("G1 el hilo tiene %d tuits (deben ser %s–%d)" % (n, 3 if smoke else 4, MAX_TUITS))
    if [t.get("n") for t in tuits] != list(range(1, n + 1)):
        F.append("G1 los tuits no están numerados 1..%d" % n)
    if n and tuits[0].get("beat") != "gancho":
        F.append("G1 T1 debe ser beat 'gancho'")
    if n and tuits[-1].get("beat") != "cierre":
        F.append("G1 T%d debe ser beat 'cierre'" % n)
    giros = [t for t in tuits if t.get("beat") == "giro"]
    if len(giros) != 1:
        F.append("G1 debe haber exactamente un beat 'giro' (hay %d)" % len(giros))
    if not smoke and n >= 5 and not any(t.get("beat") == "impacto" for t in tuits):
        F.append("G1 en modo normal con ≥5 tuits debe haber un beat 'impacto' (escala humana)")
    for t in tuits:
        if t.get("beat") not in BEATS:
            F.append("G1 T%s beat %r no está en %s" % (t.get("n"), t.get("beat"), BEATS))
    if guion.get("hook_tipo") and guion["hook_tipo"] not in HOOKS:
        F.append("G1 hook_tipo %r no está en %s" % (guion["hook_tipo"], HOOKS))
    if len((guion.get("sintesis") or {}).get("no_afirma", [])) > 5:
        W.append("no_afirma tiene más de 5 ítems: deja solo lo que un lector inferiría del hilo")
    # G6
    pal = guion.get("paleta")
    if pal not in paletas:
        F.append("G6 paleta %r no existe en design/tokens.json" % pal)
    if encuadre and encuadre.get("paleta") != pal:
        F.append("G6 paleta del guion (%s) ≠ encuadre (%s)" % (pal, encuadre.get("paleta")))
    # G2 + G3 + G4 + G5 + G7
    fuentes_tarjetas = []
    todas_ids = [c for t in tuits if t.get("visual") for c in t["visual"].get("cifra_ids", [])]
    for i, t in enumerate(tuits):
        k = t.get("n", i + 1)
        texto = t.get("texto") or ""
        peso = peso_x(texto)
        if i == 0:
            if not 40 <= peso <= 280:
                F.append("G2 T1 debe pesar entre 40 y 280 en X (pesa %d)" % peso)
            if len(texto.split("\n")[0]) > 90:
                F.append("G2 T1 primera línea > 90 caracteres")
            if RE_LINK.search(texto):
                F.append("G2 T1 lleva un enlace o dominio")
        elif peso > 280:
            F.append("G2 T%d pesa %d en X (>280)" % (k, peso))
        if RE_BAIT.search(texto):
            F.append("G2 T%d contiene engagement bait" % k)
        v = t.get("visual")
        if v is None:
            if 0 < i < n - 1:
                F.append("G3 T%d no lleva visual (obligatorio en T2..T%d)" % (k, n - 1))
            continue
        if 0 < i < n - 1 and peso > 200:
            F.append("G2 T%d con imagen pesa %d (>200): que la tarjeta hable" % (k, peso))
        alt = (t.get("alt_text") or "").strip()
        if not 20 <= len(alt) <= 1000:
            F.append("G2 T%d alt_text debe tener 20–1000 caracteres (%d)" % (k, len(alt)))
        pl = v.get("plantilla_final") or v.get("plantilla")
        if pl not in plantillas:
            F.append("G3 T%d plantilla %r no está en el catálogo %s" % (k, pl, sorted(plantillas)))
        if not v.get("kicker") or len(v["kicker"]) > 45:
            F.append("G3 T%d kicker vacío o > 45" % k)
        tit = v.get("titular") or []
        if not 1 <= len(tit) <= 3 or any((not l.strip()) or len(l) > 26 for l in tit):
            F.append("G3 T%d titular: 1–3 líneas de ≤ 26 caracteres (%s)" % (k, tit))
        if len(v.get("nota") or "") > 150:
            F.append("G3 T%d nota > 150" % k)
        fu = v.get("fuente") or ""
        if not 1 <= len(fu) <= 70 or fu.lower().startswith("fuente:"):
            F.append("G3 T%d fuente vacía, > 70 o con prefijo «Fuente:»" % k)
        else:
            fuentes_tarjetas.append((k, fuente_corta(fu)))
        if re.search(r"https?://", json.dumps(v, ensure_ascii=False)):
            F.append("G3 T%d el visual contiene una URL" % k)
        ids = v.get("cifra_ids") or []
        if not ids:
            F.append("G3 T%d cifra_ids vacío" % k)
        malos = [c for c in ids if c not in ok_ids]
        if malos:
            F.append("G3 T%d cifra_ids no verificadas o desconocidas: %s" % (k, malos))
        # G2 dato héroe: el texto no repite el titular (entero, o ≥2 de sus líneas)
        if texto.strip():
            tx = re.sub(r"\s+", " ", texto.lower())
            titular_junto = re.sub(r"\s+", " ", " ".join(l.strip() for l in tit).lower())
            lineas_rep = [l.strip() for l in tit if len(l.strip()) >= 8 and l.strip().lower() in tx]
            if (titular_junto and titular_junto in tx) or len(lineas_rep) >= 2:
                F.append("G2 T%d el texto repite el titular de su tarjeta: «%s»" % (k, " / ".join(lineas_rep) or titular_junto))
            repetidos = {x for x in numeros_de(v.get("datos") or {}) if aparece_en_texto(x, texto)}
            if len(repetidos) >= 2:
                msg = "G2 T%d el texto repite %d números de su tarjeta (dato héroe): %s" % (k, len(repetidos), sorted(repetidos))
                (F if i == 0 else W).append(msg)
        # G4
        permitidos = set()
        for c in ids:
            if c in cifras:
                permitidos |= valores_de(cifras[c], veredictos.get(c))
        extractor = CLAVES_DATO.get(pl)
        if extractor:
            nums = [x for x in extractor(v.get("datos") or {}) if isinstance(x, (int, float)) and not isinstance(x, bool)]
            fuera = sorted({round(float(x), 6) for x in nums} - permitidos)
            if fuera:
                F.append("G4 T%d números del visual sin respaldo en sus cifras %s: %s" % (k, ids, fuera))
            if not nums:
                F.append("G4 T%d visual.datos no trae números para la plantilla %s" % (k, pl))
        # G7 superlativos: en la tarjeta exigen respaldo en sus propias cifras (fallo);
        # en el texto, respaldo en alguna cifra del hilo (aviso si no)
        def respalda(cids):
            for c in cids:
                cf = cifras.get(c) or {}
                serie = [p.get("v") for p in (cf.get("serie") or []) if isinstance(p.get("v"), (int, float))]
                vf = (veredictos.get(c) or {}).get("valor_final", cf.get("valor"))
                if len(serie) >= 10 and isinstance(vf, (int, float)) and abs(max(serie) - vf) < 1e-9:
                    return True
            return False
        if RE_SUPER.search(" ".join(tit)) and not respalda(ids):
            F.append("G7 T%d la tarjeta dice «récord/histórico» sin una serie ≥10 puntos en sus cifras cuyo máximo sea el valor" % k)
        elif RE_SUPER.search(texto) and not respalda(ids) and not respalda(todas_ids):
            W.append("G7 T%d el texto dice «récord/histórico» sin una serie ≥10 puntos que lo respalde en el hilo" % k)
        # G5
        if os.path.exists(os.path.join(sesion, "visuales", "tuit_%d.ajuste.json" % k)):
            F.append("G5 T%d tiene un ajuste sin consolidar (corre scripts/materializar.py --consolidar)" % k)
        html = os.path.join(sesion, "visuales", "tuit_%d.html" % k)
        png = os.path.join(sesion, "visuales", "tuit_%d.png" % k)
        if not os.path.exists(html) or not os.path.exists(png):
            F.append("G5 T%d faltan visuales/tuit_%d.html o .png (corre scripts/materializar.py)" % (k, k))
        else:
            src = open(html, encoding="utf-8").read()
            if v.get("kicker") and v["kicker"] not in src:
                F.append("G5 T%d el HTML no contiene el kicker del guion (desincronizado)" % k)
            if fu and fu not in src:
                F.append("G5 T%d el HTML no contiene la fuente del guion (desincronizado)" % k)
    # G8 fuentes en el cierre
    if n:
        cierre = (tuits[-1].get("texto") or "").lower()
        faltan = sorted({fc for _, fc in fuentes_tarjetas if fc and fc.lower() not in cierre})
        if fuentes_tarjetas and not cierre.strip():
            F.append("G8 el cierre no tiene texto: debe nombrar las fuentes de las tarjetas")
        elif faltan:
            F.append("G8 el cierre no nombra las fuentes de las tarjetas: %s" % ", ".join(faltan))
    return F, W


ESTADOS = ["borrador", "listo", "incompleto"]


def escribir_hilo_html(hilo, salida):
    plantilla = open(os.path.join(RAIZ, "templates", "hilo.html"), encoding="utf-8").read()
    html = plantilla.replace("/*HILO_JSON*/null", json.dumps(hilo, ensure_ascii=False).replace("</", "<\\/"))
    open(os.path.join(salida, "hilo.html"), "w", encoding="utf-8").write(html)


def cambiar_estado(salida, estado):
    """--solo-estado: reescribe `estado` en hilo.json, hilo.html y post.md sin renderizar nada."""
    hj = os.path.join(salida, "hilo.json")
    if not os.path.exists(hj):
        print("ERROR: falta %s (ensambla primero)" % os.path.relpath(hj, RAIZ), file=sys.stderr)
        return 1
    hilo = json.load(open(hj, encoding="utf-8"))
    hilo["estado"] = estado
    json.dump(hilo, open(hj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    escribir_hilo_html(hilo, salida)
    pm = os.path.join(salida, "post.md")
    if os.path.exists(pm):
        s = open(pm, encoding="utf-8").read()
        s2, k = re.subn(r"^- \*\*Estado:\*\* \S+", "- **Estado:** %s" % estado, s, count=1, flags=re.M)
        if not k:
            print("AVISO: post.md no tiene línea «- **Estado:** …»", file=sys.stderr)
        open(pm, "w", encoding="utf-8").write(s2)
    print("[ensamblar] estado %s -> %s (hilo.json, hilo.html, post.md)" % (estado, os.path.relpath(salida, RAIZ)))
    return 0


def escribir(guion, encuadre, cifras, veredictos, fuentes, sesion, salida, fallos_gate, con_contacto=True, estado="borrador"):
    os.makedirs(salida, exist_ok=True)
    tuits = guion["tuits"]
    n = len(tuits)
    slug = guion.get("slug") or (encuadre or {}).get("slug") or os.path.basename(os.path.normpath(sesion))
    fecha = guion.get("fecha") or (encuadre or {}).get("fecha") or ""
    tema = (encuadre or {}).get("tema") or guion.get("tema") or slug
    sin = guion.get("sintesis", {})
    tesis = sin.get("tesis") or guion.get("tesis") or ""
    ok_ids = {i for i, v in veredictos.items() if v.get("veredicto") in ("verificada", "ajustada")}
    usadas = {c for t in tuits if t.get("visual") for c in t["visual"].get("cifra_ids", [])}

    for t in tuits:
        if t.get("visual"):
            for ext in ("html", "png"):
                src = os.path.join(sesion, "visuales", "tuit_%d.%s" % (t["n"], ext))
                if os.path.exists(src):
                    shutil.copyfile(src, os.path.join(salida, "tuit_%d.%s" % (t["n"], ext)))

    # aparece_en
    aparece = {c: [] for c in cifras}
    for t in tuits:
        v = t.get("visual")
        if v:
            for c in v.get("cifra_ids", []):
                if c in aparece:
                    aparece[c].append("tuit_%d.png" % t["n"])
        texto = t.get("texto") or ""
        for c, cf in cifras.items():
            vf = (veredictos.get(c) or {}).get("valor_final", cf.get("valor"))
            if isinstance(vf, (int, float)) and texto and aparece_en_texto(vf, texto):
                aparece[c].append("T%d" % t["n"])

    fuentes_tarjetas = []
    for t in tuits:
        if t.get("visual") and t["visual"].get("fuente") and t["visual"]["fuente"] not in fuentes_tarjetas:
            fuentes_tarjetas.append(t["visual"]["fuente"])
    fuentes_usadas = sorted({(cifras[c].get("fuente") or "") for c in usadas if c in cifras} - {""})

    hilo = {
        "slug": slug, "fecha": fecha, "tema": tema, "tesis": tesis, "paleta": guion.get("paleta"),
        "hook_tipo": guion.get("hook_tipo"), "pregunta": sin.get("pregunta", ""), "n_tuits": n,
        "estado": estado,
        "tuits": [{
            "n": t["n"], "beat": t.get("beat"), "texto": t.get("texto") or "", "caracteres": peso_x(t.get("texto") or ""),
            "alt_text": t.get("alt_text") or "", "imagen": ("tuit_%d.png" % t["n"]) if t.get("visual") else None,
            "plantilla": (t.get("visual") or {}).get("plantilla_final") or (t.get("visual") or {}).get("plantilla"),
            "fuente": (t.get("visual") or {}).get("fuente"), "cifra_ids": (t.get("visual") or {}).get("cifra_ids", []),
        } for t in tuits],
        "no_afirma": sin.get("no_afirma", []), "incertidumbre": sin.get("incertidumbre", []),
        "fuentes": fuentes_tarjetas, "fuentes_cifras": fuentes_usadas,
        "gate_mecanico": "ok" if not fallos_gate else "falla",
        "contacto": None,
    }

    datos = {
        "slug": slug, "fecha": fecha, "tesis": tesis, "ancla_id": sin.get("ancla_id"), "paleta": guion.get("paleta"),
        "hook_tipo": guion.get("hook_tipo"),
        "cifras": [], "fuentes": list(fuentes.values()),
        "no_afirma": sin.get("no_afirma", []), "incertidumbre": sin.get("incertidumbre", []),
        "descartadas": sin.get("descartadas", []) or [{"id": i, "por": v.get("veredicto"), "nota": v.get("nota", "")} for i, v in veredictos.items() if v.get("veredicto") == "no_confirmada"],
    }
    for c, cf in cifras.items():
        if c not in ok_ids:
            continue
        v = veredictos.get(c, {})
        entrada = {k: cf.get(k) for k in ("id", "concepto", "unidad", "anio", "tipo", "fuente", "url", "periodo", "n_puntos") if cf.get(k) is not None}
        entrada["valor"] = v.get("valor_final", cf.get("valor"))
        if v.get("veredicto") == "ajustada" and cf.get("valor") != v.get("valor_final"):
            entrada["valor_original"] = cf.get("valor")
        entrada["veredicto"] = v.get("veredicto")
        if v.get("fuente_2"):
            entrada["fuente_2"] = v["fuente_2"]
        if cf.get("evidencia"):
            entrada["evidencia"] = cf["evidencia"]
        if cf.get("serie"):
            entrada["serie"] = cf["serie"]
        if cf.get("partes"):
            entrada["partes"] = cf["partes"]
        entrada["usada"] = c in usadas
        entrada["aparece_en"] = aparece.get(c, [])
        datos["cifras"].append(entrada)

    # post.md
    L = ["# %s" % tema, "", "- **Fecha:** %s" % fecha, "- **Slug:** %s" % slug, "- **Paleta:** %s" % guion.get("paleta"),
         "- **Gancho:** %s" % (guion.get("hook_tipo") or "—"), "- **Tesis:** %s" % tesis,
         "- **Tuits:** %d · **Imágenes:** %d" % (n, sum(1 for t in tuits if t.get("visual"))),
         "- **Gate mecánico:** %s" % hilo["gate_mecanico"], "- **Estado:** %s (la publicación en X es manual)" % hilo["estado"], ""]
    for t in tuits:
        texto = t.get("texto") or ""
        L.append("## Tuit %d/%d — %s (%d de peso X)" % (t["n"], n, t.get("beat", ""), peso_x(texto)))
        L.append("")
        L.append(texto if texto.strip() else "_(sin texto: la imagen lo dice)_")
        if t.get("visual"):
            L.append("")
            L.append("[📸 tuit_%d.png — %s]" % (t["n"], t.get("alt_text", "")))
        L.append("")
    usadas_l = [c for c in datos["cifras"] if c["usada"]]
    no_usadas_l = [c for c in datos["cifras"] if not c["usada"]]
    L += ["## Datos clave (cifras usadas en el hilo)", "", "| id | Concepto | Valor | Unidad | Año | Veredicto | Fuente | Aparece en |", "|---|---|---|---|---|---|---|---|"]
    for c in usadas_l:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (c["id"], c.get("concepto", ""), fmt_num(c["valor"]), c.get("unidad", ""), c.get("anio", ""), c.get("veredicto", ""), c.get("fuente", ""), ", ".join(c["aparece_en"]) or "—"))
    if no_usadas_l:
        L += ["", "<details><summary>Cifras verificadas no usadas (%d)</summary>" % len(no_usadas_l), "", "| id | Concepto | Valor | Unidad | Año | Fuente |", "|---|---|---|---|---|---|"]
        for c in no_usadas_l:
            L.append("| %s | %s | %s | %s | %s | %s |" % (c["id"], c.get("concepto", ""), fmt_num(c["valor"]), c.get("unidad", ""), c.get("anio", ""), c.get("fuente", "")))
        L += ["", "</details>"]
    L += ["", "## Lo que este hilo NO afirma", ""] + (["- " + x for x in hilo["no_afirma"]] or ["- (nada declarado)"])
    L += ["", "## Incertidumbre declarada", ""] + (["- " + x for x in hilo["incertidumbre"]] or ["- (nada declarado)"])
    if datos["descartadas"]:
        L += ["", "## Cifras no confirmadas (excluidas del hilo)", ""] + ["- %s — %s %s" % (d.get("id"), d.get("por", ""), d.get("nota", "")) for d in datos["descartadas"]]
    L += ["", "## Fuentes", "", "**En el pie de cada tarjeta:**", ""] + ["- " + f for f in fuentes_tarjetas]
    L += ["", "**De las cifras usadas:**", ""] + ["- " + f for f in fuentes_usadas]
    otras = [f for f in fuentes.values() if f.get("nombre") and f["nombre"] not in fuentes_usadas]
    if otras:
        L += ["", "**Otras consultadas:**", ""] + ["- %s%s" % (f.get("nombre"), (" — " + f["url"]) if f.get("url") else "") for f in otras]
    if fallos_gate:
        L += ["", "## Gate mecánico — FALLOS", ""] + ["- " + f for f in fallos_gate]
    L.append("")
    open(os.path.join(salida, "post.md"), "w", encoding="utf-8").write("\n".join(L))

    # contacto.png (hoja de contacto con todas las tarjetas)
    if con_contacto and any(t.get("visual") for t in tuits):
        contacto = os.path.join(RAIZ, "scripts", "contacto.js")
        if os.path.exists(contacto):
            r = subprocess.run(["node", contacto, salida, "--out", os.path.join(salida, "contacto.png")], capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(os.path.join(salida, "contacto.png")):
                hilo["contacto"] = "contacto.png"
            else:
                print("AVISO: no se generó contacto.png: %s" % (r.stderr or r.stdout).strip()[:300], file=sys.stderr)

    json.dump(hilo, open(os.path.join(salida, "hilo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(datos, open(os.path.join(salida, "datos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    escribir_hilo_html(hilo, salida)
    return hilo


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sesion")
    p.add_argument("--salida", help="carpeta de salida (default hilos/<fecha>-<slug>/; smoke/fixture → <sesion>/salida)")
    p.add_argument("--check", action="store_true", help="aplica el gate mecánico; si falla no escribe y sale 1")
    p.add_argument("--fecha", help="YYYY-MM-DD para la carpeta si el guion no la trae")
    p.add_argument("--forzar", action="store_true", help="escribe aunque el gate falle (los fallos quedan en post.md)")
    p.add_argument("--sin-contacto", action="store_true", help="no genera contacto.png")
    p.add_argument("--estado", choices=ESTADOS, help="estado escrito en hilo.json, hilo.html y post.md (default borrador)")
    p.add_argument("--solo-estado", action="store_true", help="solo reescribe el estado en la carpeta de entrega existente (exige --estado)")
    a = p.parse_args()
    if a.solo_estado and not a.estado:
        p.error("--solo-estado exige --estado listo|incompleto|borrador")
    sesion = os.path.abspath(a.sesion)
    guion, encuadre, cifras, veredictos, fuentes = cargar_sesion(sesion)
    tokens = leer(os.path.join(RAIZ, "design", "tokens.json"), obligatorio=True)
    plantillas = catalogo_plantillas()

    fecha = guion.get("fecha") or (encuadre or {}).get("fecha") or a.fecha
    if fecha and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        print("ERROR: fecha %r no es YYYY-MM-DD" % fecha, file=sys.stderr); return 2
    slug = guion.get("slug") or (encuadre or {}).get("slug") or os.path.basename(os.path.normpath(sesion))
    smoke = bool(guion.get("smoke") or (encuadre or {}).get("smoke") or (encuadre or {}).get("fixture"))
    salida = a.salida or (os.path.join(sesion, "salida") if smoke else os.path.join(RAIZ, "hilos", "%s-%s" % (fecha or "sin-fecha", slug)))
    if a.solo_estado:
        return cambiar_estado(salida, a.estado)

    fallos, avisos = gate(guion, encuadre, cifras, veredictos, sesion, plantillas, set(tokens["paletas"])) if a.check else ([], [])
    for w in avisos:
        print("AVISO " + w)
    for f in fallos:
        print("FALLO " + f, file=sys.stderr)
    if fallos and not a.forzar:
        print("[ensamblar] gate mecánico: %d fallo(s); no se escribe la carpeta (usa --forzar para escribir igual)" % len(fallos), file=sys.stderr)
        return 1
    hilo = escribir(guion, encuadre, cifras, veredictos, fuentes, sesion, salida, fallos, con_contacto=not a.sin_contacto, estado=a.estado or "borrador")
    rel = os.path.relpath(salida, RAIZ)
    print("[ensamblar] %s · %d tuits · %d imágenes · gate %s%s -> %s" % (
        slug, hilo["n_tuits"], sum(1 for t in hilo["tuits"] if t["imagen"]), hilo["gate_mecanico"],
        " · contacto.png" if hilo.get("contacto") else "", rel))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
