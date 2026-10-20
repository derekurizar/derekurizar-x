#!/usr/bin/env python3
"""/video: un hilo entregado → video vertical 1080×1920 narrado (TikTok / Reels / Facebook).

La sesión principal coordina (el guion lo orquesta el Workflow `video`); este script hace todo lo determinista y
los gates V1–V10 (referencias/flujo-video.md). La voz y Scribe salen del MCP de ElevenLabs; la música viene SOLO
del catálogo fijo design/musica/catalogo.json y los efectos SOLO de design/sfx/catalogo.json (/video nunca genera
música ni efectos).

Subcomandos (TRABAJO = sesiones/<slug>/video):
  preparar <hilo|ultimo> [--duracion corto|medio|largo] [--musica ID] [--trabajo DIR] [--permitir-borrador]
        crea TRABAJO, elige la música y escribe digesto.md para el guionista (también lo imprime); corto por defecto
  guion TRABAJO --check        gate V1–V5 + V9 (estructura de retención) sobre guion.json v2 → locucion.json
  voz TRABAJO                  imprime JSON con la voz y el texto de cada nodo TTS
  descargar TRABAJO --voz URLS.json | --palabras URLS.json   ({"<n>": "<url>"} → audio/voz_N.mp3 | palabras_N.json)
  voz-falsa TRABAJO            tono por palabra + tiempos sintéticos (fixture, 0 créditos)
  tiempos TRABAJO              atempo 1.1, alineación por palabra (V6), eventos y efectos por escena, V10 → escenas.json
  grabar TRABAJO [--fps 30] [--solo 1,3]   clips por escena (Playwright) + V7
  montar TRABAJO               voz + música con ducking + efectos + loudnorm en 2 pasadas (V8), subtitulos.srt, caption.md, portada.png
  revisar TRABAJO              revision/contacto.png (cifra completa · pico del foco · final de cada escena)
  entregar TRABAJO [--salida DIR]   copia a <hilo>/video/ (o DIR) con guion.json de entrega
  musica                       lista el catálogo fijo con cuántas veces y cuándo se usó cada pista

Exit: 0 ok · 1 gate o paso fallido · 2 uso incorrecto.
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import numeros_es as NE  # noqa: E402
import verificacion as VM  # noqa: E402

VOZ = {"voice_id": "8mBRP99B2Ng2QwsJMFQl", "nombre": "El Faraon 4", "modelo": "eleven_multilingual_v2", "idioma": "es"}
REDES = [{"red": "tiktok", "nombre": "TikTok", "handle": "@derekurizargt"},
         {"red": "instagram", "nombre": "Instagram", "handle": "@derekurizargt"},
         {"red": "x", "nombre": "X", "handle": "@DerekUrizar"}]
VELOCIDAD = 1.1      # la voz se acelera con atempo (sin cambiar el tono); los tiempos de Scribe se dividen igual
CPS = 15.5           # caracteres de voz por segundo ya acelerada (medido en la prueba del hilo de crimen)
COLA = 0.7           # aire tras la última palabra de cada escena
COLA_CIERRE = 2.8    # «Sígueme en» se queda en pantalla tras la pregunta final
PREFIJO = "En Guatemala:"
DURACION_DEFECTO = "corto"
DURACIONES = {  # objetivo en s · tarjetas y golpes (más el gancho y el cierre); «prueba» es solo para el fixture
    "corto": {"s": 60, "tarjetas": (3, 4), "golpes": (1, 2)},
    "medio": {"s": 120, "tarjetas": (6, 8), "golpes": (2, 4)},
    "largo": {"s": 240, "tarjetas": (11, 15), "golpes": (3, 6)},
    "prueba": {"s": 45, "tarjetas": (2, 3), "golpes": (0, 1)},
}
TIPOS = ("gancho", "tarjeta", "golpe")                     # escenas del guion; locucion.json añade "cierre"
FORMULAS = ("cifra", "contradiccion", "pregunta", "resultado")
ENLACES = {"pero": r"pero|sin embargo|aunque|solo que|en cambio|aun así",
           "por_eso": r"por eso|así que|entonces|el resultado|de ahí que|la consecuencia",
           "y": r"y|además|también|encima|más aún"}
RE_ENLACE = {k: re.compile(r"^[¿¡]?\s*(?:%s)\b" % v, re.I) for k, v in ENLACES.items()}
CARACTERES = {"gancho": (30, 120), "tarjeta": (40, 230), "golpe": (20, 110), "cierre": (40, 200)}  # voz ya en palabras
GOLPE_PALABRAS, GOLPE_CARACTERES = 6, 40
PANTALLA_PALABRAS, PANTALLA_CARACTERES, LINEA_PALABRAS, LINEA_CARACTERES = 4, 24, 8, 60
RITMO_MAX_S = 6.0    # V9 (estimado) y V10 (real): hueco máximo entre eventos visuales
RE_FIN_ORACION = re.compile(r"[.?!:;…](?=\s|$)")
RE_CIFRA_ID = re.compile(r"\b([a-z]{2,6}-c\d{2,3})(?:\.(serie|partes)\[(-?\d+)\])?")
CONSTANTES_CALCULO = {7, 12, 24, 30, 31, 52, 100, 365, 1000, 1000000}
PUNTAJES = ("gancho", "bucle", "ritmo", "escala_humana", "pago", "cierre")   # critica.json (W10 lo coteja con video.js)
TOLERANCIA = 0.10    # V4 (estimada) · V6 avisa con 0.15 sobre la real
MUSICA_VOLUMEN = 0.22  # antes del ducking: bajo la voz queda ≈ 0.075
VOZ_LUFS = -18.0       # la voz se nivela antes de usarla como llave del sidechain
DUCK = "threshold=0.02:ratio=2.5:attack=20:release=450:detection=rms:level_sc=1"
LUFS, LUFS_TOL, TP_MAX = -14.0, 1.5, -1.0
PROHIBIDO_CIERRE = re.compile(r"fuente|en el hilo|guate en datos|s[ií]gue(me|nos)", re.I)
MESES = r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)"
PLANTILLAS_ANIMADAS = {"antes-despues", "cifra", "barras-v", "linea", "barras-h", "waffle", "dona", "pesas",
                       "mapa", "pendiente"}
SFX_DIR = os.path.join(RAIZ, "design", "sfx")
RE_DE_CADA = re.compile(r"\b(\d+)\s+de\s+cada\s+(\d+)\b")


# ---------- utilidades ----------
def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def rel(p):
    return os.path.relpath(p, RAIZ)


def falla(msg):
    print("ERROR:", msg, file=sys.stderr)
    return 1


def ffprobe_dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def estado(trabajo):
    return leer(os.path.join(trabajo, "video.json"))


def titular_de(html):
    """Kicker, titular y si hay nota en la tarjeta, leídos de DATA en tuit_N.html."""
    s = open(html, encoding="utf-8").read()
    t = re.search(r'"titular":\s*\[(.*?)\]', s, re.S)
    k = re.search(r'"kicker":\s*("(?:[^"\\]|\\.)*")', s)
    nota = bool(re.search(r'"nota":\s*"(?:[^"\\]|\\.){3,}"', s))
    return (json.loads(k.group(1)) if k else "", " ".join(json.loads("[" + t.group(1) + "]")) if t else "", nota)


def contraste(c1, c2):
    def lum(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4  # noqa: E731
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
    a, b = sorted((lum(c1), lum(c2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def colores(paleta):
    p = leer(os.path.join(RAIZ, "design", "tokens.json"))["paletas"][paleta]
    # resaltado del subtítulo activo: a3 de fondo con a1 de texto si se lee bien; si no, ink sobre bg invertido
    if contraste(p["a3"], p["a1"]) >= 4.5:
        rbg, rink = p["a3"], p["a1"]
    else:
        rbg, rink = p["ink"], p["bg"]
    return {"bg": p["bg"], "ink": p["ink"], "a1": p["a1"], "a2": p["a2"], "a3": p["a3"],
            "resalte_bg": rbg, "resalte_ink": rink,
            "pregunta": p["a3"] if contraste(p["a3"], p["bg"]) >= 3 else p["ink"],
            "acento": p["a1"] if contraste(p["a1"], p["bg"]) >= 3 else p["ink"]}  # la cifra grande del gancho/golpe


def palabras(s):
    return len((s or "").split())


def _plano(s):
    """Texto normalizado para comparar: minúsculas, sin tildes ni signos, espacios simples."""
    s = unicodedata.normalize("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# ---------- preparar ----------
def resolver_hilo(arg):
    if arg == "ultimo":
        regs = leer(os.path.join(RAIZ, "memoria", "hilos.json"))["hilos"]
        regs = [h for h in regs if h.get("estado") in ("listo", "publicado")]
        if not regs:
            return None
        return os.path.join(RAIZ, sorted(regs, key=lambda h: (h["fecha"], h["id"]))[-1]["ruta"])
    for cand in (arg, os.path.join(RAIZ, arg), os.path.join(RAIZ, "hilos", arg)):
        if os.path.isfile(os.path.join(cand, "hilo.json")):
            return os.path.abspath(cand)
    hits = sorted(glob.glob(os.path.join(RAIZ, "hilos", "*-" + arg)))
    return hits[-1] if hits else None


def elegir_musica(paleta, forzada):
    cat = leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
    if forzada:
        p = next((x for x in cat if x["id"] == forzada), None)
        if not p:
            raise ValueError("música «%s» no está en el catálogo" % forzada)
        return p
    propias = [x for x in cat if x["paleta"] == paleta]
    if not propias:
        raise ValueError("el catálogo no tiene música para la paleta «%s»" % paleta)
    usos = {}
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    if os.path.exists(vids):
        for v in leer(vids)["videos"]:  # la usada hace más tiempo (o nunca) va primero
            usos[v.get("musica")] = max(usos.get(v.get("musica"), ""), v.get("fecha", ""))
    return sorted(propias, key=lambda x: (usos.get(x["id"], ""), x["id"]))[0]


def sugerir_tarjetas(tuits, tarjetas, dur):
    """Orden sugerido: T1, luego giro e impacto, luego contexto con plantilla animada, luego el resto (sin el cierre)."""
    beats = {t["n"]: t.get("beat") for t in tuits}
    disp = {t["n"]: t for t in tarjetas}
    orden = [1] if 1 in disp else []
    for b in ("giro", "impacto"):
        orden += [n for n in sorted(disp) if beats.get(n) == b and n not in orden]
    orden += [n for n in sorted(disp) if n not in orden and beats.get(n) != "cierre"
              and disp[n]["plantilla"] in PLANTILLAS_ANIMADAS]
    orden += [n for n in sorted(disp) if n not in orden and beats.get(n) != "cierre"]
    return sorted(orden[:dur["tarjetas"][1]])


def escala_humana(cid, c):
    """Traducciones posibles de una cifra, con su `calculo` listo para el guion (≤ 2 líneas)."""
    out = []
    partes = [p.get("valor") for p in c.get("partes") or []]
    partes = [p for p in partes if isinstance(p, (int, float)) and not isinstance(p, bool)]
    v = c.get("valor")
    if len(partes) >= 2 and partes[0]:
        out.append("×%.1f entre las dos primeras partes (calculo: %s.partes[1]/%s.partes[0]) · %+.0f %% (calculo: (%s.partes[1]/%s.partes[0]-1)*100)"
                   % (partes[1] / partes[0], cid, cid, (partes[1] / partes[0] - 1) * 100, cid, cid))
    u = str(c.get("unidad", "")).lower()
    if isinstance(v, (int, float)) and not isinstance(v, bool) and ("%" in u or "porcentaje" in u or "por ciento" in u) and 0 < v < 100:
        out.append("1 de cada %d (calculo: 100/%s)" % (round(100 / v), cid))
    serie = c.get("serie") or []
    v0 = serie[0].get("v") if serie else None
    if len(serie) >= 2 and isinstance(v0, (int, float)) and v0 and isinstance(v, (int, float)) and not isinstance(v, bool):
        out.append("×%.1f desde %s (calculo: %s/%s.serie[0]) · %+.0f %% (calculo: (%s/%s.serie[0]-1)*100)"
                   % (v / v0, serie[0].get("p"), cid, cid, (v / v0 - 1) * 100, cid, cid))
    return out[:2]


def cmd_preparar(a):
    if a.duracion not in DURACIONES:
        return falla("duración «%s»: usa corto (por defecto), medio o largo" % a.duracion)
    hilo_dir = resolver_hilo(a.hilo)
    if not hilo_dir:
        return falla("no encuentro el hilo «%s» (slug, carpeta de hilos/ o «ultimo»)" % a.hilo)
    hilo = leer(os.path.join(hilo_dir, "hilo.json"))
    datos = leer(os.path.join(hilo_dir, "datos.json"))
    if hilo.get("estado") not in ("listo", "publicado") and not a.permitir_borrador:
        return falla("el hilo está «%s»: /video solo convierte hilos listos o publicados" % hilo.get("estado"))
    try:
        musica = elegir_musica(hilo["paleta"], a.musica)
    except (ValueError, FileNotFoundError) as e:
        return falla(str(e))
    trabajo = os.path.abspath(a.trabajo or os.path.join(RAIZ, "sesiones", hilo["slug"], "video"))
    for sub in ("audio", "clips", "segs", "revision", "salida"):
        os.makedirs(os.path.join(trabajo, sub), exist_ok=True)

    cifras = {c["id"]: c for c in datos["cifras"]}
    tarjetas, lineas = [], []
    dur = DURACIONES[a.duracion]
    for t in hilo["tuits"]:
        html = os.path.join(hilo_dir, "tuit_%d.html" % t["n"])
        if not t.get("imagen") or not os.path.exists(html):
            continue
        kicker, titular, nota = titular_de(html)
        tarjetas.append({"n": t["n"], "plantilla": t.get("plantilla"), "titular": titular, "beat": t.get("beat"), "nota": nota})
        anim = "animada" if t.get("plantilla") in PLANTILLAS_ANIMADAS else "aparece entera"
        lineas.append("\n### T%d · %s · %s (%s)" % (t["n"], t.get("beat", ""), t.get("plantilla"), anim))
        lineas.append("- kicker: %s\n- titular: %s" % (kicker, titular))
        if t.get("texto"):
            lineas.append("- texto del tuit: %s" % t["texto"].replace("\n", " "))
        lineas.append("- alt-text: %s" % t.get("alt_text", ""))
        ids_num = []
        for cid in t.get("cifra_ids") or []:
            c = cifras.get(cid)
            if not c:
                continue
            serie = ", ".join("%s: %s" % (p.get("p"), p.get("v")) for p in (c.get("serie") or [])[-8:])
            partes = ", ".join("%s: %s" % (p.get("nombre", p.get("etiqueta", "")), p.get("valor")) for p in c.get("partes") or [])
            lineas.append("- cifra %s: %s = %s %s (%s)%s%s" % (
                cid, c.get("concepto", ""), c.get("valor"), c.get("unidad", ""), c.get("periodo", ""),
                " · serie (últimos): " + serie if serie else "", " · partes: " + partes if partes else ""))
            for eh in escala_humana(cid, c):
                lineas.append("  - escala humana posible: %s" % eh)
            if isinstance(c.get("valor"), (int, float)) and not isinstance(c.get("valor"), bool):
                ids_num.append((cid, c["valor"]))
        if len(ids_num) == 2 and ids_num[0][1]:
            (c1, v1), (c2, v2) = ids_num
            lineas.append("  - escala humana posible: ×%.1f entre %s y %s (calculo: %s/%s) · %+.0f %% (calculo: (%s/%s-1)*100)"
                          % (v2 / v1, c1, c2, c2, c1, (v2 / v1 - 1) * 100, c2, c1))
    if len(tarjetas) < dur["tarjetas"][0]:
        return falla("el hilo tiene %d tarjetas y «%s» pide al menos %d: usa una duración menor"
                     % (len(tarjetas), a.duracion, dur["tarjetas"][0]))
    t1 = next((x for x in tarjetas if x["n"] == 1), None)
    prefijo = bool(t1) and "guatemala" not in t1["titular"].lower()
    n_max = 1 + dur["tarjetas"][1] + dur["golpes"][1]
    caracteres = int((dur["s"] - COLA * n_max - COLA_CIERRE) * CPS)
    sugeridas = sugerir_tarjetas(hilo["tuits"], tarjetas, dur)
    st = {"hilo": rel(hilo_dir), "slug": hilo["slug"], "fecha_hilo": hilo.get("fecha"), "paleta": hilo["paleta"],
          "duracion": a.duracion, "objetivo_s": dur["s"], "musica": musica["id"], "prefijo": prefijo,
          "tarjetas": tarjetas, "sugeridas": sugeridas}
    escribir(os.path.join(trabajo, "video.json"), st)

    giros = [x["n"] for x in tarjetas if x["beat"] == "giro"]
    impactos = [x["n"] for x in tarjetas if x["beat"] == "impacto"]
    dig = ["# Digesto para el guion del video · %s" % hilo["slug"], "",
           "- Tema: %s" % hilo.get("tema", ""), "- Tesis: %s" % hilo.get("tesis", ""),
           "- Paleta: %s · modo: %s · hook_tipo: %s" % (hilo["paleta"], hilo.get("modo", "hilo"), hilo.get("hook_tipo", "")),
           "- No afirma: %s" % "; ".join(hilo.get("no_afirma") or []),
           "", "## Presupuesto",
           "- Duración: **%s** = %d s ±%d %% · gancho + %d–%d tarjetas + %d–%d golpes + cierre · voz total ≈ %d caracteres "
           "(con las cifras ya en palabras; %.1f car/s)"
           % (a.duracion, dur["s"], TOLERANCIA * 100, *dur["tarjetas"], *dur["golpes"], caracteres, CPS),
           "- Voz por escena: gancho %d–%d · tarjeta %d–%d · golpe %d–%d · cierre %d–%d caracteres."
           % (*CARACTERES["gancho"], *CARACTERES["tarjeta"], *CARACTERES["golpe"], *CARACTERES["cierre"]),
           "- Ritmo: dentro de cada escena, como mucho %.0f s (≈ %d caracteres) entre el inicio, el fin de la primera "
           "oración, cada cifra y el fin: la cifra, pronto." % (RITMO_MAX_S, RITMO_MAX_S * CPS),
           "- «En Guatemala:» al inicio de la voz del gancho: %s (lo pone el script si tu texto no dice «Guatemala»; no lo escribas)."
           % ("SÍ" if prefijo else "no"),
           "- Música: %s (%s)" % (musica["id"], musica.get("ambiente", "")),
           "", "## Estructura (la comprueba el gate V9)",
           "1. Escena 1 = **gancho**: `formula` cifra | contradiccion | pregunta | resultado; `pantalla` (una cifra o ≤ %d palabras, "
           "≤ %d caracteres) y `linea` (≤ %d palabras, ≤ %d caracteres) deben contar el gancho **en silencio**: cifra/resultado → la "
           "cifra en pantalla; pregunta → termina en «?»; contradiccion → una cifra en pantalla o línea."
           % (PANTALLA_PALABRAS, PANTALLA_CARACTERES, LINEA_PALABRAS, LINEA_CARACTERES),
           "2. Escena 2 = la **tarjeta T1**, sin enlace. Luego tarjetas y golpes en el orden del arco.",
           "3. Desde la escena 3, `enlace` pero | por_eso | y, y la voz EMPIEZA con ese conector (pero / sin embargo / aunque / "
           "solo que / en cambio / aun así · por eso / así que / entonces / el resultado / de ahí que / la consecuencia · y / además / "
           "también / encima / más aún). «y» como máximo en un tercio de los enlaces; nunca «y luego».",
           "4. Cada tarjeta lleva `golpe` (≤ %d palabras, ≤ %d caracteres): el re-gancho que va arriba, en lenguaje llano, con la "
           "cifra si cabe; nunca el titular de la tarjeta." % (GOLPE_PALABRAS, GOLPE_CARACTERES),
           "5. Las escenas `golpe` (texto a pantalla completa) llevan `pantalla` + `linea`; nunca dos seguidas ni en la escena 2; "
           "sirven para traducir la cifra anterior a escala humana, pagar la promesa o re-ganchar a mitad.",
           "6. `promesa`: {texto (10–80 caracteres, LITERAL en la voz de la escena `en` = 1 o 2), en, pago (escena del último tercio "
           "que cierra exactamente esa brecha)}.",
           "7. `calculo` (opcional en tarjetas y gancho; obligatorio en un golpe con un número nuevo): ids del digesto (%s), literales de "
           "datos.json, constantes 7/12/24/30/31/52/100/365/1000 y + − × ÷ ( ); su resultado debe aparecer escrito en la escena "
           "(«1 de cada 3», «×5», «52%%»)." % ", ".join(sorted(cifras)[:3] + [sorted(cifras)[0] + ".serie[0]", sorted(cifras)[0] + ".partes[1]"]),
           "", "## Sugerencia de tarjetas (no obligatoria)",
           "- Orden sugerido: %s (T1, luego giro e impacto, luego contexto animado). Giro: %s · impacto: %s. Marca el giro como tu "
           "«pero» mayor y un impacto como pago de la promesa."
           % (", ".join("T%d" % n for n in sugeridas), ", ".join("T%d" % n for n in giros) or "—", ", ".join("T%d" % n for n in impactos) or "—"),
           "", "## Tarjetas disponibles (la escena 2 usa T1)"] + lineas
    out = os.path.join(trabajo, "digesto.md")
    open(out, "w", encoding="utf-8").write("\n".join(dig) + "\n")
    print("\n".join(dig))
    print("\n→ %s · trabajo: %s" % (rel(out), rel(trabajo)))
    return 0


# ---------- gate del guion (V1–V5, V9) ----------
def valores_respaldo(hilo_dir):
    """Como G10 de ensamblar.py, desde el entregable: `valor` ya es el final; `valor_original` no respalda.
    Devuelve (valores (número, factor), titulares, cifras verificadas por id)."""
    datos = leer(os.path.join(RAIZ, hilo_dir, "datos.json"))
    hilo = leer(os.path.join(RAIZ, hilo_dir, "hilo.json"))
    valores, por_id, cifras = set(), {}, {}
    for c in datos["cifras"]:
        if c.get("veredicto") not in ("verificada", "ajustada"):
            continue
        nums = [c.get("valor")] + [p.get("v") for p in c.get("serie") or []] + \
               [p.get("valor") for p in c.get("partes") or []]
        f = VM.factor_unidad(c.get("unidad"))
        valores |= {(round(float(x), 6), f) for x in nums if isinstance(x, (int, float)) and not isinstance(x, bool)}
        por_id[c["id"]] = c.get("valor")
        cifras[c["id"]] = c
    titulares = [por_id[i] for t in hilo["tuits"] for i in t.get("cifra_ids") or []
                 if isinstance(por_id.get(i), (int, float))]
    return sorted(valores), titulares, cifras


def con_prefijo(texto):
    i = 1 if texto[:1] in "¿¡" else 0
    return PREFIJO + " " + texto[:i] + texto[i].lower() + texto[i + 1:]


def _coincide(x, v, tol):
    return VM.coincide(x, [(v, tol)], escalas=(1,))


def resolver_calculo(expr, cifras, valores):
    """Evalúa un `calculo` del guion: ids de cifra (pre-c01, pre-c01.serie[0], pre-c04.partes[1]) → su valor; los literales
    deben estar en el respaldo, en CONSTANTES_CALCULO o ser enteros ≤ 12. Devuelve (valor, None) o (None, motivo)."""
    expr = str(expr or "")
    if not expr.strip():
        return None, "vacío"

    def sust(m):
        cid, campo, idx = m.group(1), m.group(2), m.group(3)
        c = cifras.get(cid)
        if not c:
            raise KeyError("usa la cifra %s que no existe o no está verificada" % cid)
        if campo:
            lista = c.get(campo) or []
            try:
                p = lista[int(idx)]
            except IndexError:
                raise KeyError("%s.%s[%s] no existe" % (cid, campo, idx))
            v = p.get("v") if campo == "serie" else p.get("valor")
        else:
            v = c.get("valor")
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise KeyError("%s no tiene valor numérico" % m.group(0))
        return "(%r)" % float(v)
    try:
        sustituida = RE_CIFRA_ID.sub(sust, expr)
    except KeyError as e:
        return None, str(e)
    for m in re.finditer(NE.NUM, RE_CIFRA_ID.sub("", expr)):
        v = float(m.group().replace(",", ""))
        if v in CONSTANTES_CALCULO or (v.is_integer() and v <= 12):
            continue
        tol = 0.5 * 10 ** -VM.decimales(v)
        if any(VM.coincide(x, [(v, tol)], escalas=(f or 1.0,)) for x, f in valores):
            continue
        return None, "usa el literal %s que no está en datos.json" % m.group()
    r = VM.evaluar(sustituida)
    if r is None:
        return None, ("ilegible: ids (nar-c02, nar-c02.partes[1], nar-c02.serie[-1]), literales de datos.json, "
                      "constantes (7, 12, 24, 30, 31, 52, 100, 365, 1000) y + − × ÷ ( )")
    return r, None


def escribe_numero(r, textos):
    """True si el resultado r de un calculo aparece escrito (con su redondeo) en alguno de los textos."""
    for t in textos:
        t = VM.RE_FECHA.sub(" ", t or "")
        for m in RE_DE_CADA.finditer(t):
            a, b = float(m.group(1)), float(m.group(2))
            if a and (_coincide(r, b / a, 0.5 / a) or (b == 100 and _coincide(r, a, 0.5))):
                return True
        for m in re.finditer(NE.NUM, t):
            v = float(m.group().replace(",", ""))
            if _coincide(r, v, 0.5 * 10 ** -VM.decimales(v)):
                return True
    return False


def sin_respaldo(texto, valores, extra=()):
    """Números de un texto de pantalla (golpe, pantalla, linea) sin respaldo: como `sueltos` con max_entero=1, y
    «A de cada B» vale si B/A está respaldado (o A lo está cuando B = 100)."""
    vals = list(valores) + [(round(float(x), 6), 1.0) for x in extra]

    def de_cada(m):
        a, b = float(m.group(1)), float(m.group(2))
        if a and any(_coincide(x, b / a, 0.5 / a) or (b == 100 and _coincide(x, a, 0.5)) for x, f in vals):
            return " "
        return m.group(0)
    return VM.sueltos(RE_DE_CADA.sub(de_cada, texto or ""), vals, max_entero=1)


def es_anio_o_fecha(seg_p, siguiente):
    m = re.search(NE.NUM, seg_p)
    if not m:
        return True
    v = float(m.group().replace(",", ""))
    return (v.is_integer() and 1900 <= v <= 2100) or bool(re.match(r"de %s" % MESES, siguiente.strip().lower()))


def hueco_maximo(segs, voz):
    """Ritmo estimado de una escena: segundos entre eventos consecutivos {inicio, fin de la primera oración, fin de
    cada cifra (sin años ni fechas), fin}. Devuelve (segundos, texto antes, texto después)."""
    marcas = [0]
    m = RE_FIN_ORACION.search(voz)
    if m:
        marcas.append(m.end())
    pos = 0
    for k, s in enumerate(segs):
        pos += len(s["v"])
        if s["num"] and not es_anio_o_fecha(s["p"], "".join(x["v"] for x in segs[k + 1:k + 3])):
            marcas.append(pos)
    marcas.append(len(voz))
    marcas = sorted(set(marcas))
    a, b = max(zip(marcas, marcas[1:]), key=lambda ab: ab[1] - ab[0])
    return (b - a) / CPS, voz[max(0, a - 25):a].strip(), voz[b:b + 25].strip()


def validar_estructura(g, st, dur, tarjetas):
    """V1 (tipos y rangos) y V9 (estructura de retención) sobre guion.json v2."""
    f = []
    escenas = g.get("escenas") or []
    if isinstance(g.get("gancho"), str):
        f.append("V1 «gancho» ya no existe: la escena 1 es {\"tipo\": \"gancho\", \"formula\", \"pantalla\", \"linea\", \"texto\"} "
                 "(referencias/roles/video-guionista.md)")
    tipos = [e.get("tipo") for e in escenas]
    for i, t in enumerate(tipos, 1):
        if t not in TIPOS:
            f.append("V1 escena %d: tipo «%s» desconocido (gancho|tarjeta|golpe)" % (i, t))
    n_t, n_g = tipos.count("tarjeta"), tipos.count("golpe")
    if not dur["tarjetas"][0] <= n_t <= dur["tarjetas"][1]:
        f.append("V1 %d tarjetas; «%s» pide %d–%d" % (n_t, st["duracion"], *dur["tarjetas"]))
    if not dur["golpes"][0] <= n_g <= dur["golpes"][1]:
        f.append("V1 %d golpes; «%s» pide %d–%d" % (n_g, st["duracion"], *dur["golpes"]))
    vistos = set()
    for i, e in enumerate(escenas, 1):
        if not (e.get("texto") or "").strip():
            f.append("V1 escena %d sin texto" % i)
        if e.get("tipo") != "tarjeta":
            continue
        n = e.get("tuit")
        if n not in tarjetas:
            f.append("V1 escena %d: T%s no tiene tarjeta en el hilo" % (i, n))
        if n in vistos:
            f.append("V1 escena %d: T%s repetida" % (i, n))
        vistos.add(n)
    if not (g.get("contexto_superior") or "").strip() or len(g.get("contexto_superior", "")) > 40:
        f.append("V1 «contexto_superior» vacío o de más de 40 caracteres")
    cierre = g.get("cierre") or {}
    for k in ("texto", "pregunta"):
        if not (cierre.get(k) or "").strip():
            f.append("V1 cierre sin «%s»" % k)
    if len(cierre.get("resumen") or []) != 2:
        f.append("V1 cierre.resumen debe tener 2 líneas")
    if not escenas:
        return f

    # V9: gancho
    g1 = escenas[0]
    if g1.get("tipo") != "gancho":
        f.append("V9 la escena 1 debe ser tipo gancho")
    for i, e in enumerate(escenas[1:], 2):
        if e.get("tipo") == "gancho":
            f.append("V9 solo la escena 1 puede ser gancho (escena %d)" % i)

    def cinetico(i, e, etiqueta):
        for campo, maxp, maxc, desc in (("pantalla", PANTALLA_PALABRAS, PANTALLA_CARACTERES, "una cifra o ≤ %d palabras" % PANTALLA_PALABRAS),
                                        ("linea", LINEA_PALABRAS, LINEA_CARACTERES, "≤ %d palabras" % LINEA_PALABRAS)):
            v = (e.get(campo) or "").strip()
            if not v:
                f.append("V9 %s: falta «%s»" % (etiqueta, campo))
            elif palabras(v) > maxp or len(v) > maxc:
                f.append("V9 %s: %s «%s» de más de %d palabras o %d caracteres (%s)" % (etiqueta, campo, v, maxp, maxc, desc))
    if g1.get("tipo") == "gancho":
        if g1.get("formula") not in FORMULAS:
            f.append("V9 gancho: formula «%s» no es cifra|contradiccion|pregunta|resultado" % g1.get("formula"))
        cinetico(1, g1, "gancho")
        pant, lin = g1.get("pantalla") or "", g1.get("linea") or ""
        tiene_cifra = lambda s: bool(re.search(NE.NUM, s))  # noqa: E731
        if g1.get("formula") in ("cifra", "resultado") and not tiene_cifra(pant):
            f.append("V9 gancho (%s): la pantalla debe llevar la cifra" % g1["formula"])
        if g1.get("formula") == "pregunta" and not (pant.rstrip().endswith("?") or lin.rstrip().endswith("?")):
            f.append("V9 gancho (pregunta): pantalla o linea deben terminar en «?»")
        if g1.get("formula") == "contradiccion" and not (tiene_cifra(pant) or tiene_cifra(lin)):
            f.append("V9 gancho (contradiccion): pantalla o linea deben llevar una cifra")
    # V9: escena 2 = T1
    if len(escenas) < 2 or escenas[1].get("tipo") != "tarjeta" or escenas[1].get("tuit") != 1:
        f.append("V9 la escena 2 debe ser la tarjeta T1 (el gancho se paga con la primera tarjeta)")
    elif escenas[1].get("enlace"):
        f.append("V9 escena 2: la primera tarjeta no lleva enlace")
    # V9: enlaces, golpes y escenas golpe
    n_y, n_enl = 0, 0
    ejemplos = {"pero": "«Pero …», «Sin embargo …»", "por_eso": "«Por eso …», «Así que …»", "y": "«Y …», «Además …»"}
    for i, e in enumerate(escenas, 1):
        tipo = e.get("tipo")
        if i >= 3 and tipo in ("tarjeta", "golpe"):
            enl = e.get("enlace")
            if not enl:
                f.append("V9 escena %d: falta enlace (pero|por_eso|y)" % i)
            elif enl not in ENLACES:
                f.append("V9 escena %d: enlace «%s» no es pero|por_eso|y" % (i, enl))
            else:
                n_enl += 1
                n_y += enl == "y"
                if not RE_ENLACE[enl].match((e.get("texto") or "").strip()):
                    f.append("V9 escena %d: la voz no empieza con un conector de tipo «%s» (p. ej. %s): «%s…»"
                             % (i, enl, ejemplos[enl], (e.get("texto") or "")[:40]))
        if tipo == "tarjeta":
            golpe = (e.get("golpe") or "").strip()
            if not golpe:
                f.append("V9 escena %d: tarjeta sin «golpe»" % i)
            elif palabras(golpe) > GOLPE_PALABRAS or len(golpe) > GOLPE_CARACTERES:
                f.append("V9 escena %d: golpe «%s» de más de %d palabras o %d caracteres" % (i, golpe, GOLPE_PALABRAS, GOLPE_CARACTERES))
            else:
                tit = _plano(tarjetas.get(e.get("tuit"), {}).get("titular"))
                gp = _plano(golpe)
                if tit and len(gp) >= 8 and (gp in tit or tit in gp):
                    f.append("V9 escena %d: golpe repite el titular de T%s («%s»)" % (i, e.get("tuit"), golpe))
        if tipo == "golpe":
            cinetico(i, e, "golpe escena %d" % i)
            if i >= 2 and escenas[i - 2].get("tipo") == "golpe":
                f.append("V9 escena %d: dos golpes seguidos (un golpe remata una tarjeta)" % i)
    if n_enl and n_y > n_enl // 3:
        f.append("V9 %d enlaces «y» de %d; máximo %d (encadena con «pero» o «por eso»)" % (n_y, n_enl, n_enl // 3))
    # V9: promesa y pago
    p = g.get("promesa")
    n = len(escenas)
    if not isinstance(p, dict) or not all(k in p for k in ("texto", "en", "pago")):
        f.append("V9 promesa: falta {texto, en, pago}")
    else:
        txt = (p.get("texto") or "").strip()
        if not 10 <= len(txt) <= 80:
            f.append("V9 promesa.texto de 10–80 caracteres")
        if p.get("en") not in (1, 2):
            f.append("V9 promesa.en debe ser 1 o 2 (llegó %s)" % p.get("en"))
        elif txt and _plano(txt) not in _plano(escenas[p["en"] - 1].get("texto")):
            f.append("V9 promesa.texto no aparece literal en la voz de la escena %d" % p["en"])
        lo = math.ceil(2 * n / 3)
        if not isinstance(p.get("pago"), int) or not lo <= p["pago"] <= n or p["pago"] == p.get("en"):
            f.append("V9 promesa.pago = %s debe estar en el último tercio (escenas %d–%d) y ser distinto de «en»" % (p.get("pago"), lo, n))
    return f


def cmd_guion(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    try:
        g = leer(os.path.join(trabajo, "guion.json"))
    except (OSError, ValueError) as e:
        return falla("guion.json ilegible: %s" % e)
    dur = DURACIONES[st["duracion"]]
    tarjetas = {t["n"]: t for t in st["tarjetas"]}
    escenas = g.get("escenas") or []
    cierre = g.get("cierre") or {}
    fallas = validar_estructura(g, st, dur, tarjetas)

    # V5 reglas (antes de convertir: el prefijo cambia el texto del gancho)
    textos = [e.get("texto", "") for e in escenas] + [cierre.get("texto", "")]
    pantallas = [" ".join(filter(None, (e.get("golpe"), e.get("pantalla"), e.get("linea")))) for e in escenas]
    todo = " ".join(textos + pantallas + [" ".join(cierre.get("resumen") or []), cierre.get("pregunta", ""),
                                          json.dumps(g.get("caption") or {}, ensure_ascii=False)])
    if re.search(r"\ben suma\b", todo, re.I):
        fallas.append("V5 «en suma» está prohibido")
    if re.search(r"https?://|@\w", " ".join(textos + pantallas)):
        fallas.append("V5 la voz y la pantalla no llevan enlaces ni @handles")
    ct = (cierre.get("texto") or "").strip()
    if not ct.endswith("?"):
        fallas.append("V5 el cierre debe terminar en pregunta")
    if cierre.get("pregunta") and not ct.endswith(cierre["pregunta"].strip()):
        fallas.append("V5 cierre.texto debe terminar con cierre.pregunta")
    cierre_pantalla = " ".join([ct, " ".join(cierre.get("resumen") or []), cierre.get("pregunta", "")])
    if PROHIBIDO_CIERRE.search(cierre_pantalla):
        fallas.append("V5 el cierre no menciona fuentes, el hilo, la marca ni «sígueme» (va solo en pantalla)")
    for k in ("tiktok", "facebook"):
        if not ((g.get("caption") or {}).get(k) or "").strip():
            fallas.append("V5 falta caption.%s" % k)

    # V2, V3, V4 y ritmo por escena (escenas + cierre)
    valores, titulares, cifras = valores_respaldo(st["hilo"])
    loc = []
    for i, e in enumerate(escenas + [{"tipo": "cierre", "tuit": None, "texto": ct}], 1):
        tipo = e.get("tipo") if e.get("tipo") in TIPOS else "cierre"
        texto = e.get("texto", "")
        prefijado = False
        if i == 1 and st.get("prefijo") and "guatemala" not in texto.lower():
            texto, prefijado = con_prefijo(texto), True
        NE.AVISOS.clear()
        try:
            segs = NE.segmentos(texto)
        except ValueError as ex:
            fallas.append("V3 escena %d: %s" % (i, ex))
            continue
        pantalla = "".join(s["p"] for s in segs)
        voz = "".join(s["v"] for s in segs)
        extra, valor_calculo = [], None
        if e.get("calculo"):
            valor_calculo, motivo = resolver_calculo(e["calculo"], cifras, valores)
            if motivo:
                fallas.append("V9 escena %d: calculo «%s» %s" % (i, e["calculo"], motivo))
            elif not escribe_numero(valor_calculo, [e.get("pantalla"), e.get("linea"), e.get("golpe"), pantalla]):
                fallas.append("V9 escena %d: calculo %s da %.4g y la escena no escribe ese número (pantalla/linea/golpe/texto)"
                              % (i, e["calculo"], valor_calculo))
            else:
                extra = [valor_calculo]
        sin = VM.sueltos(pantalla, valores + [(round(float(x), 6), 1.0) for x in extra], titulares)
        if sin:
            fallas.append("V2 escena %d: números sin respaldo en datos.json: %s" % (i, ", ".join(map(str, sin))))
        for campo in ("golpe", "pantalla", "linea"):
            if e.get(campo):
                sin = sin_respaldo(e[campo], valores, extra)
                if sin:
                    fallas.append("V9 escena %d: %s «%s» tiene un número sin respaldo en datos.json ni «calculo»: %s"
                                  % (i, campo, e[campo], ", ".join(map(str, sin))))
        for av in NE.AVISOS:
            fallas.append("V3 escena %d: %s" % (i, av))
        if re.search(r"\d", voz):
            fallas.append("V3 escena %d: la voz conserva dígitos: «%s»" % (i, voz))
        largo = len(voz) - (len(PREFIJO) + 1 if prefijado else 0)
        if not CARACTERES[tipo][0] <= largo <= CARACTERES[tipo][1]:
            fallas.append("V4 escena %d (%s): %d caracteres de voz (rango %d–%d)" % (i, tipo, largo, *CARACTERES[tipo]))
        hueco, antes, despues = hueco_maximo(segs, voz) if tipo != "cierre" else (0.0, "", "")
        if hueco > RITMO_MAX_S:
            fallas.append("V9 escena %d: %.1f s sin evento entre «…%s» y «%s…» (máximo %.0f s): acorta o mueve la cifra"
                          % (i, hueco, antes, despues, RITMO_MAX_S))
        plantilla = tarjetas[e["tuit"]]["plantilla"] if tipo == "tarjeta" and e.get("tuit") in tarjetas else tipo
        loc.append({"n": i, "tipo": tipo, "tuit": e.get("tuit") if tipo == "tarjeta" else None, "plantilla": plantilla,
                    "enlace": e.get("enlace") if i >= 2 else None, "golpe": e.get("golpe") if tipo == "tarjeta" else None,
                    "cinetico": {"pantalla": e.get("pantalla"), "linea": e.get("linea")} if tipo in ("gancho", "golpe") else None,
                    "formula": e.get("formula") if tipo == "gancho" else None,
                    "calculo": e.get("calculo"), "valor_calculo": valor_calculo,
                    "pantalla": pantalla, "voz": voz, "segmentos": segs,
                    "estimado_s": round(len(voz) / CPS + (COLA_CIERRE if tipo == "cierre" else COLA), 2),
                    "hueco_max_s": round(hueco, 2)})
    for etiqueta, txt in (("resumen", " ".join(cierre.get("resumen") or [])),
                          ("caption", json.dumps(g.get("caption") or {}, ensure_ascii=False))):
        sin = VM.sueltos(txt, valores, titulares)
        if sin:
            fallas.append("V2 %s: números sin respaldo: %s" % (etiqueta, ", ".join(map(str, sin))))

    # V4 presupuesto
    chars = sum(len(x["voz"]) for x in loc)
    estimado = chars / CPS + COLA * (len(loc) - 1) + COLA_CIERRE
    lo, hi = dur["s"] * (1 - TOLERANCIA), dur["s"] * (1 + TOLERANCIA)
    if not lo <= estimado <= hi:
        fallas.append("V4 duración estimada %.0f s (%d caracteres de voz); «%s» pide %.0f–%.0f s"
                      % (estimado, chars, st["duracion"], lo, hi))
    print("escenas %d + cierre · voz %d caracteres · estimado %.0f s (objetivo %d s)"
          % (len(escenas), chars, estimado, dur["s"]))
    for x in loc:
        print("E%-2d %-7s T%-3s %-14s %5.1fs hueco %.1fs  %s" % (x["n"], x["tipo"], x["tuit"] or "-", x["plantilla"],
                                                             x["estimado_s"], x["hueco_max_s"], x["voz"]))
    if fallas:
        for f in fallas:
            print("FALLA", f)
        return 1
    escribir(os.path.join(trabajo, "locucion.json"),
             {"voz": VOZ, "caracteres": chars, "estimado_s": round(estimado, 1), "duracion": st["duracion"],
              "objetivo_s": dur["s"], "n_escenas": len(escenas), "promesa": g.get("promesa"), "escenas": loc})
    print("→ %s · V1–V5, V9 ok" % rel(os.path.join(trabajo, "locucion.json")))
    return 0


# ---------- voz ----------
def cmd_voz(a):
    loc = leer(os.path.join(a.trabajo, "locucion.json"))
    print(json.dumps({"voz": loc["voz"], "model_parameters": {"language_code": loc["voz"]["idioma"]},
                      "caracteres": loc["caracteres"],
                      "nodos": [{"n": e["n"], "prompt": e["voz"]} for e in loc["escenas"]]},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_descargar(a):
    trabajo = os.path.abspath(a.trabajo)
    origen, tipo = (a.voz, "voz") if a.voz else (a.palabras, "palabras")
    urls = leer(origen)
    for n, url in sorted(urls.items(), key=lambda kv: int(kv[0])):
        if tipo == "voz":
            dst = os.path.join(trabajo, "audio", "voz_%s.mp3" % n)
            urllib.request.urlretrieve(url, dst)
            print("voz_%s.mp3 %.2f s" % (n, ffprobe_dur(dst)))
        else:
            with urllib.request.urlopen(url) as r:
                d = json.loads(r.read().decode("utf-8"))
            ws = d["words"] if isinstance(d, dict) else d
            ws = [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in ws
                  if w.get("type", "word") == "word" and not w["text"].startswith("[")]
            escribir(os.path.join(trabajo, "audio", "palabras_%s.json" % n), ws)
            print("palabras_%s.json %d palabras" % (n, len(ws)))
    return 0


def cmd_voz_falsa(a):
    """Fixture: un tono corto por palabra (para que el ducking y los efectos se prueben) con la duración que tendría
    la voz, y palabras repartidas por longitud."""
    trabajo = os.path.abspath(a.trabajo)
    loc = leer(os.path.join(trabajo, "locucion.json"))
    cps_crudo = CPS / VELOCIDAD
    for e in loc["escenas"]:
        palabras_ = e["voz"].split()
        total = len(e["voz"]) / cps_crudo
        t, ws = 0.0, []
        for w in palabras_:
            d = (len(w) + 1) / cps_crudo
            ws.append({"text": w, "start": round(t, 3), "end": round(t + d * 0.85, 3)})
            t += d
        puerta = "+".join("between(t,%.3f,%.3f)" % (w["start"], w["end"]) for w in ws)
        ff("-f", "lavfi", "-i", "aevalsrc=exprs='0.28*sin(2*PI*165*t)*(%s)':s=44100:d=%.3f" % (puerta, total),
           "-c:a", "libmp3lame", "-b:a", "64k", os.path.join(trabajo, "audio", "voz_%d.mp3" % e["n"]))
        escribir(os.path.join(trabajo, "audio", "palabras_%d.json" % e["n"]), ws)
    print("voz falsa: %d escenas" % len(loc["escenas"]))
    return 0


# ---------- tiempos (V6) ----------
def _norm(w):
    return re.sub(r"[^\wáéíóúñü]", "", w.lower())


def alinear(e, habladas):
    """Agrupa las palabras habladas en tokens de pantalla: cada segmento con p ≠ v (cifra, unidad) es UN token
    que dura lo que se tarda en decirlo; el texto llano va palabra por palabra."""
    segs = e["segmentos"]
    voz, dueno = "", []
    for k, s in enumerate(segs):
        voz += s["v"]
        dueno += [k if (s["num"] or s["p"] != s["v"]) else None] * len(s["v"])
    palabras_ = list(re.finditer(r"\S+", voz))
    if len(palabras_) != len(habladas):
        raise ValueError("E%d: el texto tiene %d palabras y Scribe %d" % (e["n"], len(palabras_), len(habladas)))
    for m, h in zip(palabras_, habladas):
        if _norm(m.group()) != _norm(h["text"]):
            raise ValueError("E%d: «%s» en el guion, «%s» en Scribe (t=%.2f)" % (e["n"], m.group(), h["text"], h["start"]))
    toks = []
    for m, h in zip(palabras_, habladas):
        unidad = next((dueno[i] for i in range(m.start(), m.end()) if dueno[i] is not None), None)
        if unidad is not None and toks and toks[-1]["unidad"] == unidad:
            toks[-1]["end"], toks[-1]["fin_c"] = h["end"], m.end()
            continue
        toks.append({"unidad": unidad, "ini_c": m.start(), "fin_c": m.end(), "start": h["start"], "end": h["end"]})
    out = []
    for t in toks:
        if t["unidad"] is None:
            texto = voz[t["ini_c"]:t["fin_c"]]
        else:  # «dos.» → «1,596.2.»: el segmento en pantalla con la puntuación pegada
            s = segs[t["unidad"]]
            ini = sum(len(x["v"]) for x in segs[:t["unidad"]])
            texto = voz[t["ini_c"]:ini] + s["p"].strip() + voz[ini + len(s["v"]):t["fin_c"]]
        out.append({"text": texto, "start": t["start"], "end": t["end"],
                    "seg": segs[t["unidad"]] if t["unidad"] is not None else None})
    return out


def clave(v):
    return ("%f" % v).rstrip("0").rstrip(".")


def valor_de(texto):
    m = re.search(NE.NUM, texto or "")
    return float(m.group().replace(",", "")) if m else None


def repartir(palabras_, t0, t1, minimo=0.18):
    """Palabras repartidas uniformemente en [t0, t1] (≥ `minimo` s por palabra, comprimiendo hacia t1 si no caben)."""
    n = max(1, len(palabras_))
    paso = max(minimo, (t1 - t0) / n) if n > 1 else 0
    ini = min(t0, max(0.0, t1 - paso * (n - 1)))
    return [{"text": w, "start": round(ini + paso * k, 3)} for k, w in enumerate(palabras_)]


def cmd_tiempos(a):
    trabajo = os.path.abspath(a.trabajo)
    st, loc = estado(trabajo), leer(os.path.join(trabajo, "locucion.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    beats = {t["n"]: t.get("beat") for t in st["tarjetas"]}
    notas = {t["n"]: t.get("nota") for t in st["tarjetas"]}
    pago_n = (loc.get("promesa") or {}).get("pago")
    # el giro: la escena «pero» cuyo tuit tiene beat giro; si no hay, el primer «pero»
    peros = [e["n"] for e in loc["escenas"] if e.get("enlace") == "pero"]
    giro_n = next((e["n"] for e in loc["escenas"] if e.get("enlace") == "pero" and beats.get(e.get("tuit")) == "giro"),
                  peros[0] if peros else None)
    escenas, avisos = [], []
    for e in loc["escenas"]:
        n, tipo = e["n"], e.get("tipo") or ("cierre" if e["plantilla"] == "cierre" else "tarjeta")
        src, dst = [os.path.join(trabajo, "audio", x % n) for x in ("voz_%d.mp3", "voz_%d_r.mp3")]
        ff("-i", src, "-af", "atempo=%s" % VELOCIDAD, "-c:a", "libmp3lame", "-b:a", "192k", dst)
        habladas = [dict(w, start=w["start"] / VELOCIDAD, end=w["end"] / VELOCIDAD)
                    for w in leer(os.path.join(trabajo, "audio", "palabras_%d.json" % n))]
        try:
            ps = alinear(e, habladas)
        except ValueError as ex:
            return falla("V6 %s · rehaz la voz de esa escena" % ex)
        cierre = tipo == "cierre"
        fin_voz = ps[-1]["end"]
        dur = round(ffprobe_dur(dst) + (COLA_CIERRE if cierre else COLA), 3)
        pal = []
        for k, p in enumerate(ps):
            w = {"text": p["text"], "start": round(p["start"], 3), "end": round(p["end"], 3)}
            seg = p["seg"]
            if seg and seg["num"]:
                w["num"] = True
                if not es_anio_o_fecha(seg["p"], " ".join(x["text"] for x in ps[k + 1:k + 3])):
                    w["clave"] = clave(valor_de(seg["p"]))
            pal.append(w)
        S = {"n": n, "tipo": tipo, "tuit": e.get("tuit"), "plantilla": e["plantilla"], "enlace": e.get("enlace"),
             "dur": dur, "fin_voz": round(fin_voz, 3), "palabras": pal, "arriba": None}
        ev, sfx = [], []
        if cierre:
            k_preg = max([k for k, p in enumerate(ps[:-1]) if p["text"].endswith((".", "!"))] or [-1]) + 1
            mitad = ps[max(1, k_preg // 2)]["start"] if k_preg > 2 else 0.6
            S["T"] = {"r2": round(mitad, 3), "preg": round(max(0.2, ps[k_preg]["start"] - 0.1), 3),
                      "sigue": round(fin_voz + 0.1, 3)}
            ev = [(0.1, "r1"), (S["T"]["r2"], "r2"), (S["T"]["preg"], "pregunta"), (S["T"]["sigue"], "sigue")]
            sfx = [(S["T"]["preg"], "resolucion")]
        elif tipo in ("gancho", "golpe"):
            cin = e.get("cinetico") or {}
            texto_p, v = cin.get("pantalla") or "", valor_de(cin.get("pantalla"))
            dicho = next((w for w in pal if v is not None and w.get("clave") == clave(v)), None)
            pulso = None
            # la cifra cuenta desde el inicio (la pantalla debe funcionar en silencio); si la voz la dice más tarde, late
            if dicho and dicho["start"] < 1.5:
                desde, hasta = max(0.0, dicho["start"] - 0.3), dicho["end"]
            else:
                desde, hasta = 0.15, 1.1
                if dicho:
                    pulso = [dicho["start"], dicho["end"]]
            linea = repartir((cin.get("linea") or "").split(), hasta + 0.1, max(hasta + 0.4, fin_voz - 0.3))
            S["T"] = {"pant": {"texto": texto_p, "v": v, "desde": round(desde, 3), "hasta": round(hasta, 3),
                               "pulso": [round(x, 3) for x in pulso] if pulso else None},
                      "linea": linea, "fin": round(fin_voz, 3)}
            # la línea entra palabra a palabra: cuenta como evento al empezar y al terminar
            ev = [(desde, "cifra"), (hasta, "cifra_fin")] + ([(linea[0]["start"], "linea"), (linea[-1]["start"], "linea_fin")] if linea else []) + \
                 ([(pulso[0], "pulso")] if pulso else [])
            if tipo == "gancho":
                sfx = [(0.1, "impacto"), (pulso[1] if pulso else hasta, "pulso")]
            else:
                sfx = [(0.0, "grave" if e.get("enlace") == "pero" else "impacto"), (hasta, "tic")]
        else:
            valores = {}
            for k, p in enumerate(ps):
                seg = p["seg"]
                if not seg or not seg["num"] or es_anio_o_fecha(seg["p"], " ".join(x["text"] for x in ps[k + 1:k + 3])):
                    continue
                valores.setdefault(clave(valor_de(seg["p"])), [round(p["start"] - 0.5, 3), round(p["end"], 3)])
            golpe = (e.get("golpe") or "").split()
            if golpe:
                S["arriba"] = [{"text": w, "start": round(0.12 * k, 3)} for k, w in enumerate(golpe)]
            tit = 0.45 if golpe else 0.15
            ini = tit + 0.6
            fin_vals = max([w[1] for w in valores.values()] or [ini + 1.5])
            # alias escalados: la voz dice «12.8» y la barra guarda 12818 (formato.escala 1000); misma ventana
            con_alias = dict(valores)
            for k, w in valores.items():
                for esc in (1e3, 1e6):
                    con_alias.setdefault(clave(float(k) * esc), w)
            S["T"] = {"tit": round(tit, 3), "ini": round(ini, 3), "valores": con_alias,
                      "nota": round(min(fin_vals + 0.4, dur - 1.2), 3), "linea_fin": round(fin_voz - 1.0, 3), "foco": True}
            ev = ([(0.0, "golpe_arriba")] if golpe else []) + [(tit, "entra")]
            sfx = [(tit, "whoosh")]
            ultimo_tic = -9
            for desde, hasta in sorted(valores.values()):
                ev += [(desde, "foco"), (hasta, "conteo_fin")]
                if desde - tit >= 1.0:
                    sfx.append((desde, "foco"))
                if hasta - ultimo_tic >= 1.2:
                    sfx.append((hasta, "tic"))
                    ultimo_tic = hasta
            if notas.get(e.get("tuit")):
                ev.append((S["T"]["nota"], "nota"))
            if n == giro_n:
                sfx.append((0.0, "grave"))
        if n == pago_n and n != 1:
            sfx.append((-2.0, "riser"))
        ev.append((dur, "fin"))
        S["eventos"] = [{"t": round(t, 3), "tipo": k} for t, k in sorted(ev, key=lambda x: x[0])]
        S["sfx"] = [{"t": round(t, 3), "id": k} for t, k in sorted(sfx, key=lambda x: x[0])]
        escenas.append(S)
        print("E%-2d %-7s %6.2f s  eventos=%d  %s" % (n, tipo, dur, len(S["eventos"]), json.dumps(S["T"], ensure_ascii=False)[:140]))
    total = sum(s["dur"] for s in escenas)
    obj = st["objetivo_s"]
    if abs(total - obj) > obj * 0.15:
        avisos.append("V6 duración real %.1f s fuera de ±15 %% de %d s" % (total, obj))
    # V10 ritmo real: hueco máximo entre eventos consecutivos de todo el video
    linea_t, off, pago_t = [], 0.0, None
    for s in escenas:
        if s["n"] == pago_n:
            pago_t = off
        linea_t += [(off + x["t"], x["tipo"], s["n"]) for x in s["eventos"]]
        off += s["dur"]
    linea_t.sort()
    peor = max(zip(linea_t, linea_t[1:]), key=lambda ab: ab[1][0] - ab[0][0]) if len(linea_t) > 1 else None
    if peor and peor[1][0] - peor[0][0] > RITMO_MAX_S:
        avisos.append("V10 ritmo: %.1f s sin evento entre «%s» (E%d) y «%s» (E%d)"
                      % (peor[1][0] - peor[0][0], peor[0][1], peor[0][2], peor[1][1], peor[1][2]))
    e1 = loc["escenas"][0]
    escribir(os.path.join(trabajo, "escenas.json"), {
        "version": 2, "colores": colores(st["paleta"]), "contexto_superior": g["contexto_superior"], "redes": REDES,
        "gancho": {"pantalla": (e1.get("cinetico") or {}).get("pantalla"), "linea": (e1.get("cinetico") or {}).get("linea")},
        "pago": {"n": pago_n, "t": round(pago_t, 3) if pago_t is not None else None},
        "cierre": {"resumen": g["cierre"]["resumen"], "pregunta": g["cierre"]["pregunta"]},
        "total_s": round(total, 2), "escenas": escenas})
    for x in avisos:
        print("AVISO", x)
    print("total %.1f s (objetivo %d s) · hueco máximo %.1f s → %s"
          % (total, obj, (peor[1][0] - peor[0][0]) if peor else 0, rel(os.path.join(trabajo, "escenas.json"))))
    return 0


# ---------- grabar (V7) ----------
def cmd_grabar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    hilo_dir = os.path.join(RAIZ, st["hilo"])
    args = ["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", trabajo, "--hilo", hilo_dir,
            "--fps", str(a.fps)]
    if a.solo:
        args += ["--solo", a.solo]
    if subprocess.run(args, cwd=RAIZ).returncode:
        return falla("la grabación falló")
    # V7: el último cuadro de cada tarjeta animada es idéntico a su render estático
    esc = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    htmls = [os.path.join(hilo_dir, "tuit_%d.html" % e["tuit"]) for e in esc if e["tuit"]]
    if subprocess.run(["node", os.path.join(RAIZ, "scripts", "video_animar.js"), "--check", *htmls], cwd=RAIZ).returncode:
        return falla("V7 el estado final de alguna tarjeta animada no coincide con su PNG")
    return 0


# ---------- montar (V8) ----------
def musica_bucle(archivo, total, salida):
    """La pista en bucle con crossfades de 4 s hasta cubrir `total` segundos."""
    largo = ffprobe_dur(archivo)
    copias = max(1, math.ceil((total - largo) / (largo - 4)) + 1) if total > largo else 1
    entradas = sum([["-i", archivo] for _ in range(copias)], [])
    if copias == 1:
        filtro = "[0:a]atrim=0:%.3f[m]" % total
    else:
        filtro, prev = "", "[0:a]"
        for i in range(1, copias):
            out = "[x%d]" % i
            filtro += "%s[%d:a]acrossfade=d=4:c1=tri:c2=tri%s;" % (prev, i, out)
            prev = out
        filtro += "%satrim=0:%.3f[m]" % (prev, total)
    ff(*entradas, "-filter_complex", filtro, "-map", "[m]", "-ar", "48000", salida)


def medir(audio):
    """Medidas de loudnorm (input_i, input_tp, input_lra, input_thresh, target_offset) de un archivo."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af", "loudnorm=I=%s:TP=-1.5:LRA=11:print_format=json" % LUFS,
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    return {k: float(j[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def ts(s):
    h, r = divmod(s, 3600)
    m, s = divmod(r, 60)
    return ("%02d:%02d:%06.3f" % (h, m, s)).replace(".", ",")


def muestras(t):
    return "%dS" % round(t * 48000)


def cmd_montar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    segs = os.path.join(trabajo, "segs")
    clips = [os.path.join(trabajo, "clips", "e%d.mp4" % e["n"]) for e in E["escenas"]]
    offs, off = [], 0.0
    for c in clips:  # desplazamientos exactos: lo que grabó Playwright (round(dur·fps)/fps)
        offs.append(off)
        off += ffprobe_dur(c)
    D = off
    # 1. solo video
    lista = os.path.join(segs, "lista.txt")
    with open(lista, "w") as f:
        for c in clips:
            f.write("file '%s'\n" % c)
    video_solo = os.path.join(segs, "voz_video.mp4")
    ff("-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", "-an", video_solo)
    # 2. la voz en una sola pista, nivelada a VOZ_LUFS (llave determinista del ducking)
    voces = [os.path.join(trabajo, "audio", "voz_%d_r.mp3" % e["n"]) for e in E["escenas"]]
    fc = "".join("[%d:a]aresample=48000,aformat=channel_layouts=stereo,adelay=%s:all=1[v%d];" % (i, muestras(o), i)
                 for i, o in enumerate(offs))
    fc += "".join("[v%d]" % i for i in range(len(voces))) + "amix=inputs=%d:duration=longest:normalize=0,apad=whole_dur=%.3f[vz]" % (len(voces), D)
    voz = os.path.join(segs, "voz.wav")
    ff(*sum([["-i", v] for v in voces], []), "-filter_complex", fc, "-map", "[vz]", "-ar", "48000", voz)
    gv = VOZ_LUFS - medir(voz)["input_i"]
    # 3. música en bucle
    pista = next(p for p in leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
                 if p["id"] == st["musica"])
    fondo = os.path.join(segs, "musica.wav")
    musica_bucle(os.path.join(RAIZ, "design", "musica", pista["archivo"]), D, fondo)
    # 4. efectos del catálogo fijo, en su tiempo global
    cat = {x["id"]: x for x in leer(os.path.join(SFX_DIR, "catalogo.json"))["efectos"]}
    efectos = []
    for e, o in zip(E["escenas"], offs):
        for s in e.get("sfx") or []:
            t = o + s["t"]
            if t >= 0 and s["id"] in cat:
                efectos.append((t, s["id"]))
    efectos.sort()
    # 5. mezcla: voz + música con ducking (sidechain) + efectos
    entradas = ["-i", voz, "-i", fondo] + sum([["-i", os.path.join(SFX_DIR, cat[i]["archivo"])] for _, i in efectos], [])
    fc = ("[0:a]volume=%.2fdB,asplit=2[v][k];"
          "[1:a]aformat=channel_layouts=stereo,volume=%s,afade=t=in:st=0:d=1,afade=t=out:st=%.2f:d=2.5[m0];"
          "[m0][k]sidechaincompress=%s[m1];[m1]asplit=2[m][mdbg];" % (gv, MUSICA_VOLUMEN, D - 2.5, DUCK))
    for j, (t, i) in enumerate(efectos):
        fc += "[%d:a]aformat=channel_layouts=stereo,adelay=%s:all=1,volume=%ddB[f%d];" % (j + 2, muestras(t), cat[i]["ganancia_db"], j)
    fc += "[v][m]" + "".join("[f%d]" % j for j in range(len(efectos))) + "amix=inputs=%d:duration=first:normalize=0[a]" % (len(efectos) + 2)
    mezcla = os.path.join(segs, "mezcla.wav")
    ff(*entradas, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", mezcla,
       "-map", "[mdbg]", "-ar", "48000", os.path.join(segs, "musica_duck.wav"))
    # 6. loudnorm en dos pasadas (lineal: no deshace el ducking) y el video final
    m1 = medir(mezcla)
    sal = os.path.join(trabajo, "salida")
    video = os.path.join(sal, "video.mp4")
    ff("-i", video_solo, "-i", mezcla, "-filter_complex",
       "[1:a]loudnorm=I=%s:TP=-1.5:LRA=11:measured_I=%.2f:measured_TP=%.2f:measured_LRA=%.2f:measured_thresh=%.2f:offset=%.2f:linear=true[a]"
       % (LUFS, m1["input_i"], m1["input_tp"], m1["input_lra"], m1["input_thresh"], m1["target_offset"]),
       "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
       "-movflags", "+faststart", video)

    # V8
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate",
                                    "-of", "json", video], capture_output=True, text=True).stdout)["streams"]
    v = next((s for s in pr if s["codec_type"] == "video"), {})
    fallas = []
    if (v.get("width"), v.get("height")) != (1080, 1920):
        fallas.append("V8 tamaño %sx%s (se espera 1080×1920)" % (v.get("width"), v.get("height")))
    if not any(s["codec_type"] == "audio" for s in pr):
        fallas.append("V8 sin audio")
    mf = medir(video)
    lufs, tp = mf["input_i"], mf["input_tp"]
    if abs(lufs - LUFS) > LUFS_TOL or tp > TP_MAX:
        fallas.append("V8 sonoridad %.1f LUFS / %.1f dBTP (se espera %.0f ±%.1f, ≤ %.0f)" % (lufs, tp, LUFS, LUFS_TOL, TP_MAX))

    # subtítulos, caption y portada
    out, k = [], 1
    for e, off in zip(E["escenas"], offs):
        cur = []
        for p in e["palabras"] + [None]:
            if p is None or (cur and len(" ".join(x["text"] for x in cur)) + len(p["text"]) + 1 > 42):
                if cur:
                    out.append("%d\n%s --> %s\n%s\n" % (k, ts(off + cur[0]["start"]), ts(off + cur[-1]["end"] + 0.15),
                                                        " ".join(x["text"] for x in cur)))
                    k += 1
                cur = []
            if p is None:
                break
            cur.append(p)
            if p["text"][-1] in ".?:;":
                out.append("%d\n%s --> %s\n%s\n" % (k, ts(off + cur[0]["start"]), ts(off + cur[-1]["end"] + 0.15),
                                                    " ".join(x["text"] for x in cur)))
                k, cur = k + 1, []
    open(os.path.join(sal, "subtitulos.srt"), "w", encoding="utf-8").write("\n".join(out))
    redes = " · ".join("%s %s" % (r["nombre"], r["handle"]) for r in REDES)
    cap = g["caption"]
    open(os.path.join(sal, "caption.md"), "w", encoding="utf-8").write(
        "# Texto para publicar\n\n## TikTok / Reels\n%s\n\n## Facebook\n%s\n\nSígueme: %s\n"
        % (cap["tiktok"].strip(), cap["facebook"].strip(), redes))
    e1 = E["escenas"][0]
    if e1.get("tipo") in ("gancho", "golpe"):  # la portada se lee en silencio: cifra completa y línea entera
        t_port = max(e1["T"]["pant"]["hasta"], (e1["T"]["linea"] or [{"start": 0}])[-1]["start"]) + 0.35
    else:
        t_port = e1["T"]["tit"] + 1.2
    ff("-ss", "%.2f" % min(t_port, e1["dur"] - 0.1), "-i", clips[0], "-frames:v", "1", os.path.join(sal, "portada.png"))
    print("video %.1f s · %.1f LUFS · %.1f dBTP · %d subtítulos · efectos %d · música %.2f con ducking → %s"
          % (ffprobe_dur(video), lufs, tp, k - 1, len(efectos), MUSICA_VOLUMEN, rel(video)))
    for f in fallas:
        print("FALLA", f)
    return 1 if fallas else 0


# ---------- revisar ----------
def cuadros_de(e):
    """Tiempos de los cuadros de revisión de una escena, según sus eventos (≤ 3)."""
    ev = e.get("eventos") or []
    primero = lambda tipo: next((x["t"] for x in ev if x["tipo"] == tipo), None)  # noqa: E731
    ultimo = lambda tipo: next((x["t"] for x in reversed(ev) if x["tipo"] == tipo), None)  # noqa: E731
    tipo = e.get("tipo")
    if tipo in ("gancho", "golpe"):
        ts_ = [(primero("cifra_fin") or 0.5) + 0.15]
    elif tipo == "cierre":
        ts_ = [(primero("pregunta") or e["dur"] * 0.5) + 0.7]
    else:
        f, c = primero("foco"), ultimo("conteo_fin")
        ts_ = ([f + 0.6] if f is not None else []) + [(c + 0.3) if c is not None else e["dur"] * 0.5]
    ts_.append(e["dur"] - 0.35)
    return [min(t, e["dur"] - 0.35) for t in ts_]


def cmd_revisar(a):
    trabajo = os.path.abspath(a.trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))["escenas"]
    rev = os.path.join(trabajo, "revision")
    for f in glob.glob(os.path.join(rev, "c_*.png")):
        os.remove(f)
    k = 0
    for e in E:
        for t in cuadros_de(e):
            k += 1
            ff("-ss", "%.2f" % t, "-i", os.path.join(trabajo, "clips", "e%d.mp4" % e["n"]),
               "-frames:v", "1", os.path.join(rev, "c_%03d.png" % k))
    cols = 3 * min(len(E), 4)
    filas = math.ceil(k / cols)
    out = os.path.join(rev, "contacto.png")
    ff("-framerate", "1", "-i", os.path.join(rev, "c_%03d.png"), "-vf",
       "scale=270:480,tile=%dx%d:padding=6:color=white" % (cols, filas), "-frames:v", "1", out)
    print("hoja de contacto (%d cuadros: cifra completa · pico del foco · final de cada escena) → %s" % (k, rel(out)))
    return 0


# ---------- entregar ----------
def cmd_entregar(a):
    trabajo = os.path.abspath(a.trabajo)
    st = estado(trabajo)
    E = leer(os.path.join(trabajo, "escenas.json"))
    loc = leer(os.path.join(trabajo, "locucion.json"))
    g = leer(os.path.join(trabajo, "guion.json"))
    destino = os.path.abspath(a.salida or os.path.join(RAIZ, st["hilo"], "video"))
    os.makedirs(destino, exist_ok=True)
    for f in ("video.mp4", "subtitulos.srt", "caption.md", "portada.png"):
        shutil.copy2(os.path.join(trabajo, "salida", f), os.path.join(destino, f))
    shutil.copy2(os.path.join(trabajo, "revision", "contacto.png"), os.path.join(destino, "contacto.png"))
    hilo = leer(os.path.join(RAIZ, st["hilo"], "hilo.json"))
    critica, rc = None, os.path.join(trabajo, "critica.json")
    if os.path.exists(rc):
        c = leer(rc)
        critica = {"veredicto": c.get("veredicto"), "vuelta": c.get("vuelta"),
                   "puntajes": {k: (c.get("puntajes") or {}).get(k) for k in PUNTAJES}}
    else:
        print("AVISO sin critica.json: el video se entrega sin la revisión del crítico")
    g1 = g["escenas"][0]
    entrega = {
        "id": "%s-%s" % (hilo.get("fecha"), st["slug"]), "slug": st["slug"], "hilo": st["hilo"],
        "paleta": st["paleta"], "duracion": st["duracion"], "duracion_s": round(ffprobe_dur(os.path.join(destino, "video.mp4")), 1),
        "n_escenas": len(loc["escenas"]) - 1, "musica": st["musica"], "voz": loc["voz"], "velocidad": VELOCIDAD,
        "creditos_voz": loc["caracteres"], "contexto_superior": g["contexto_superior"],
        "gancho": {"formula": g1.get("formula"), "pantalla": g1.get("pantalla"), "linea": g1.get("linea")},
        "promesa": g.get("promesa"), "critica": critica,
        "escenas": [{"n": e["n"], "tipo": e.get("tipo"), "tuit": e["tuit"], "plantilla": e["plantilla"], "enlace": e.get("enlace"),
                     "golpe": e.get("golpe"), "cinetico": e.get("cinetico"), "pantalla": e["pantalla"], "voz": e["voz"],
                     "dur": s["dur"]} for e, s in zip(loc["escenas"], E["escenas"])],
        "cierre": g["cierre"], "caption": g["caption"],
    }
    escribir(os.path.join(destino, "guion.json"), entrega)
    print("entregado en %s (%.1f s)" % (rel(destino), entrega["duracion_s"]))
    return 0


def cmd_musica(a):
    cat = leer(os.path.join(RAIZ, "design", "musica", "catalogo.json"))["pistas"]
    vids = os.path.join(RAIZ, "memoria", "videos.json")
    usos = {}
    for v in (leer(vids)["videos"] if os.path.exists(vids) else []):
        n, f = usos.get(v.get("musica"), (0, ""))
        usos[v.get("musica")] = (n + 1, max(f, v.get("fecha", "")))
    for p in cat:
        n, f = usos.get(p["id"], (0, ""))
        print("%-13s %-10s %5.0f s · %d uso(s)%s · %s" % (p["id"], p["paleta"], p["duracion_s"], n,
                                                      " (último %s)" % f if f else "", p["ambiente"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("preparar")
    p.add_argument("hilo")
    p.add_argument("--duracion", default=DURACION_DEFECTO)
    p.add_argument("--musica")
    p.add_argument("--trabajo")
    p.add_argument("--permitir-borrador", action="store_true", help="solo para el fixture")
    p = sub.add_parser("guion")
    p.add_argument("trabajo")
    p.add_argument("--check", action="store_true", required=True)
    for nombre in ("voz", "voz-falsa", "tiempos", "montar", "revisar"):
        sub.add_parser(nombre).add_argument("trabajo")
    p = sub.add_parser("descargar")
    p.add_argument("trabajo")
    x = p.add_mutually_exclusive_group(required=True)
    x.add_argument("--voz")
    x.add_argument("--palabras")
    p = sub.add_parser("grabar")
    p.add_argument("trabajo")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--solo")
    sub.add_parser("musica")
    p = sub.add_parser("entregar")
    p.add_argument("trabajo")
    p.add_argument("--salida")
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"preparar": cmd_preparar, "guion": cmd_guion, "voz": cmd_voz, "descargar": cmd_descargar,
            "voz-falsa": cmd_voz_falsa, "tiempos": cmd_tiempos, "grabar": cmd_grabar, "montar": cmd_montar,
            "revisar": cmd_revisar, "entregar": cmd_entregar, "musica": cmd_musica}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
