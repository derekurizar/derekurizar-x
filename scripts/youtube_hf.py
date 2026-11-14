#!/usr/bin/env python3
"""youtube_hf.py — el 16:9 de /youtube-long como «mesa de archivo», dibujado y renderizado con HyperFrames.

Por qué existe (usuario, 2026-11-13): el 16:9 del motor propio era una foto por escena; el «arreglo» movía la cámara para
cumplir un gate de píxeles («pésimo»). Dinamismo es que ENTRE en pantalla lo que la voz nombra: fotos, recortes de
prensa, documentos, retratos, lugares en un mapa, fechas, cifras con su rótulo. Aquí cada pieza cae sobre una mesa
cuando la voz la dice y, una vez puesta, se queda quieta. La cámara no se mueve.

El guion visual es TRABAJO/plano.json (lo escribe el agente youtube-realizador, un capítulo cada uno, sobre el borrador
que arma este script) y lo valida `plano --check` (YT13–YT19, sobre los datos: nunca sobre píxeles).

  plano.json = {"mesas": [{"escenas": ["P1.e1", "promesa"], "golpes": [{"tipo", "escena", "dice", …}]}]}
    mesa   = un tema (6–45 s): sus piezas se apilan; al cambiar de mesa, todo se barre
    golpe  = una pieza que entra cuando la voz dice `dice` (palabras literales de la voz de `escena`, en orden)
    tipos  = foto · recorte · documento · persona · institucion · lugar · fecha · cifra · termino · cita · lista
    una escena `explica` o `tarjeta` es un TABLERO: su animación ya hecha va entera y quieta a la izquierda (clip del
    motor propio) y sus golpes caen a la derecha; va sola en su mesa
    los rótulos de capítulo y el cierre los arma este script (no van en el plano)

Uso (lo llama scripts/youtube.py; también directo):
  youtube_hf.py borrador TRABAJO            plano.borrador.json desde lo que ya traen las escenas
  youtube_hf.py digesto TRABAJO --capitulo N   lo que el realizador necesita para escribir plano_<N>.json
  youtube_hf.py plano TRABAJO [--check] [--hoja] [--capitulo N]   une plano_<N>.json → plano.json; gates; hoja de golpes
  youtube_hf.py proyecto TRABAJO [--capitulo N]   TRABAJO/hf/cap-N/ (un proyecto HyperFrames por capítulo) + hf/efectos.json
  youtube_hf.py revisar TRABAJO [--capitulo N]    hyperframes check + hoja de contacto (revision/hf_cap-N.jpg)
  youtube_hf.py render TRABAJO [--capitulo N] [--calidad looks]   render por capítulo (--workers 1) → segs_16x9/video_solo.mp4

Render SIEMPRE con --workers 1: con varios procesos de Chrome el video tiembla (medido 2026-11-13).
Exit 0 ok · 1 falla · 2 uso.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD   # noqa: E402

FPS = 30
HF_VERSION = "0.9.28"
LEAD = 0.30            # la pieza empieza a caer 0.3 s antes de su palabra y aterriza en ella
ENTRA = 0.5
VISIBLES = 3           # YT18: con 3 piezas nuevas encima, la de abajo se atenúa
MESA_S = (4.0, 45.0)   # YT18: lo que dura una mesa
MESA_PIEZAS = 12       # YT18
HUECO_MAX_S = 6.0      # YT14: ningún tramo de voz de más de esto sin un golpe
ENTRE_GOLPES_S = 0.3   # YT18: dos piezas no entran a menos de esto
PIEZA_NUEVA_MIN = 0.5  # YT17: fracción de oraciones con pieza nueva
ARCHIVO_MIN = 0.35     # YT17: fracción de piezas que son archivo real (aviso bajo 0.5)
TIPOS_MIN = 4          # YT17: tipos distintos por capítulo
TEXTO_SEGUIDOS = 2     # YT17: rótulos de solo texto seguidos
FOTO_USOS_MAX = 2      # YT15
FOTO_SEPARACION_S = 180
TIPOS = ("foto", "recorte", "documento", "persona", "institucion", "lugar", "fecha", "cifra", "termino", "cita", "lista")
ARCHIVO = ("foto", "recorte", "documento", "lugar")   # archivo real (más la persona con retrato y los tableros)
SOLO_TEXTO = ("termino", "lista")
TABLERO = ("explica", "tarjeta")
PROPIAS = ("capitulo", "cierre")
EVENTOS_TABLERO = ("paso", "foco", "cifra", "nodo", "entra", "golpe_arriba", "acto", "nota", "lienzo")
INSTITUCION = re.compile(r"\b(banco|junta|superintendencia|ministerio|fondo|tribunal|juzgado|corte|sala|congreso|fiscalia|comision|grupo|bolsa|sociedad|empresa)\b")
JUDICIAL = re.compile(r"\b(audiencia|capturad|detenid|procesad|ligad[oa]s? a proceso|esposad|primera declaraci[oó]n|sindicad|acusad|imputad)", re.I)
EN_PALABRAS = dict({w: str(i) for i, w in enumerate("cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete "
                                                     "dieciocho diecinueve veinte".split())},
                   un="1", una="1", treinta="30", cuarenta="40", cincuenta="50", sesenta="60", setenta="70", ochenta="80", noventa="90", cien="100", mil="1000",
                   primer="1", primero="1", primera="1", segundo="2", segunda="2", tercer="3", tercero="3", tercera="3", cuarto="4", cuarta="4", quinto="5",
                   quinta="5", sexto="6", septimo="7", octavo="8", noveno="9", decimo="10", doble="2", triple="3", mitad="2")
LUGARES = {   # (lon, lat) de los lugares que suelen salir; otro lugar lleva lon y lat en el golpe
    "guatemala": (-90.52, 14.63), "ciudad de guatemala": (-90.52, 14.63), "barbados": (-59.62, 13.10), "bridgetown": (-59.62, 13.10),
    "nueva york": (-74.00, 40.71), "panama": (-79.52, 8.98), "ciudad de panama": (-79.52, 8.98), "gran caiman": (-81.38, 19.29),
    "islas caiman": (-81.38, 19.29), "miami": (-80.19, 25.76), "washington": (-77.04, 38.90), "mexico": (-99.13, 19.43),
    "el salvador": (-89.19, 13.69), "san salvador": (-89.19, 13.69), "honduras": (-87.20, 14.07), "tegucigalpa": (-87.20, 14.07),
    "costa rica": (-84.09, 9.93), "nicaragua": (-86.25, 12.13), "belice": (-88.77, 17.25), "bahamas": (-77.35, 25.05),
    "madrid": (-3.70, 40.42), "espana": (-3.70, 40.42), "houston": (-95.37, 29.76), "los angeles": (-118.24, 34.05),
    "colombia": (-74.07, 4.71), "bogota": (-74.07, 4.71), "suiza": (8.54, 47.37), "londres": (-0.13, 51.51)}

CSS = """
@font-face{font-family:'Archivo';font-weight:100 900;font-stretch:62% 125%;src:url('assets/fonts/archivo-wdth.woff2') format('woff2')}
@font-face{font-family:'JetBrains Mono';font-weight:100 800;src:url('assets/fonts/jetbrains-mono-var.woff2') format('woff2')}
#root{position:absolute;inset:0;font-family:'Archivo',sans-serif;color:$tinta}
.pz{position:absolute}
.mov{position:relative}
.pila{position:relative;box-shadow:0 34px 70px rgba(0,0,0,.6),0 5px 12px rgba(0,0,0,.45)}
.velo{position:absolute;inset:0;background:#0b0705;opacity:0;pointer-events:none}
.cond{font-family:'Archivo',sans-serif;font-stretch:62%;font-weight:800;text-transform:uppercase;line-height:.94;letter-spacing:.005em}
.mono{font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.1em}
.foto{background:$papel;padding:14px 14px 0}
.foto .im{position:relative;overflow:hidden}
.foto .im img{display:block;position:absolute;object-fit:cover}
.foto .pie{padding:12px 6px 14px}
.foto .pie b{display:block;font-weight:650;font-size:28px;line-height:1.12}
.foto .pie span{display:block;margin-top:5px;font-family:'JetBrains Mono',monospace;font-size:17px;color:#6b5a45;white-space:nowrap;overflow:hidden}
.ficha{background:$papel;padding:30px 36px 30px;border-top:12px solid $cafe}
.ficha.per{display:flex;gap:28px;align-items:flex-start}
.ficha .ret{flex:none;width:210px;height:250px;position:relative;overflow:hidden;background:$papel2}
.ficha .ret img{position:absolute;display:block}
.ficha .k{font-size:28px;color:#6b5a45;font-weight:600}
.ficha .n{margin-top:12px}
.ficha .r{margin-top:14px;font-size:32px;font-weight:500;line-height:1.18;color:#3a2c1f}
.ficha .f,.cifra .f,.recorte .f,.cita .f{margin-top:16px;font-family:'JetBrains Mono',monospace;font-size:18px;color:#7a6850}
.fecha{background:$papel;padding:10px}
.fecha .in{border:5px solid $tinta;padding:14px 26px 8px;text-align:center}
.fecha .s{font-size:29px;font-weight:700}
.fecha .b{font-size:168px;white-space:nowrap}
.cal{background:$papel;text-align:center}
.cal .top{background:$cafe;color:$papel;font-size:40px;padding:10px 0 8px}
.cal .mes{font-size:150px;padding:18px 0 0}
.cal .sub{font-size:29px;font-weight:700;padding:0 0 18px;color:#3a2c1f}
.cifra{background:$mesa2;border:1px solid rgba(246,242,232,.22);padding:22px 36px 26px;color:$papel}
.cifra .v{color:$acento;white-space:nowrap}
.cifra .l{font-size:44px;margin-top:2px}
.cifra .f{color:$gris}
.recorte{background:$papel2;padding:26px 32px 28px}
.recorte .cab{display:flex;justify-content:space-between;align-items:baseline;border-bottom:4px solid $tinta;padding-bottom:10px}
.recorte .cab .m{font-size:40px}
.recorte .cab .d{font-family:'JetBrains Mono',monospace;font-size:20px;color:#4e3f2f}
.recorte .t{font-size:56px;margin-top:18px;text-transform:none;line-height:1}
.recorte .x{font-size:38px;line-height:1.3;margin-top:16px;font-weight:450;color:#2b2016}
.doc-txt .cab{display:block}
.doc-txt .cab .d{margin-top:6px}
.hl{background-image:linear-gradient($acento,$acento);background-repeat:no-repeat;background-size:0% 100%;-webkit-box-decoration-break:clone;box-decoration-break:clone;padding:2px 0}
.nota{background:$acento;padding:26px 34px 24px}
.nota .cond{font-size:66px}
.cita{background:$papel;padding:34px 44px 34px;border-left:14px solid $cafe}
.cita .q{font-size:44px;line-height:1.24;font-weight:500;color:#a89a80}
.cita .a{margin-top:20px;font-size:40px}
.cita .c{margin-top:6px;font-size:28px;color:#4e3f2f;font-weight:500}
.doc{background:#FBF9F3;position:relative;overflow:hidden}
.doc img{display:block;position:absolute}
.doc .marca{position:absolute;background:$acento;mix-blend-mode:multiply;opacity:.85}
.tab{position:absolute;background:$tinta;color:$papel;padding:12px 22px 10px;max-width:760px}
.tab .cond{font-size:44px}
.tab .mono{font-size:19px;color:$acento;margin-bottom:4px}
.mapa{background:$papel2;padding:16px}
.mapa svg{display:block;background:#DCD2BC}
.mapa .tierra{fill:#C3B391;stroke:#8d7b5c;stroke-width:.8}
.mapa .gt{fill:$cafe;stroke:$tinta;stroke-width:1.2}
.mapa text{font-family:'Archivo',sans-serif;font-stretch:62%;font-weight:800;fill:$tinta;text-transform:uppercase}
.pizarra{background:#231c18;border:3px solid rgba(246,242,232,.85);overflow:hidden}
.chip{display:inline-block;background:$papel;padding:16px 26px 12px;box-shadow:0 18px 36px rgba(0,0,0,.55);white-space:nowrap}
.chip .cond{font-size:52px}
.chip.ac{background:$acento}
.cuad{display:grid;grid-template-columns:repeat(6,34px);gap:8px;margin-top:14px}
.cuad i{display:block;width:34px;height:34px;background:$acento;opacity:0}
.rot{position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;padding:0 150px;color:$papel}
.rot .k{font-size:34px;color:$acento}
.rot .t{font-size:190px;margin-top:18px;line-height:.9}
.rot .a{font-size:74px;margin-top:26px;color:$gris}
.cie{position:absolute;left:110px;top:90px;width:900px;color:$papel}
.cie .k{font-size:30px;color:$acento}
.cie .li{font-size:64px;margin-top:22px;text-transform:none;line-height:1}
.cie .fin{font-size:46px;line-height:1.2;font-weight:500;margin-top:44px;color:$papel}
.cie .sus{margin-top:50px;display:inline-block;background:$acento;color:$tinta;padding:18px 34px 14px}
.cie .sus .cond{font-size:60px}
.cie .han{margin-top:18px;font-size:30px;color:$gris}
"""


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, obj):
    """Escritura atómica: varios realizadores corren `plano --check` a la vez sobre el mismo plano.json."""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = "%s.%d.tmp" % (p, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, p)


def rel(p):
    return os.path.relpath(p, RAIZ)


def falla(m):
    print("ERROR: " + m, file=sys.stderr)
    return 1


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cuadro(t):
    return round(round(t * FPS) / FPS, 4)


# ---------- contexto: escenas, tiempos, capítulos ----------
def contexto(trabajo):
    import youtube as YT
    E = leer(os.path.join(trabajo, "escenas.json"))
    es = YT.claves_visuales(E["escenas"])
    TR = E.get("transicion_s", VD.TRANSICION)
    offs, off = [], 0.0
    for k, S in enumerate(es):
        offs.append(cuadro(off))
        off += S["dur"] - (TR if k < len(es) - 1 else 0.0)
    total = cuadro(off)
    caps, act = [], None
    for i, S in enumerate(es):
        if S["tipo"] == "capitulo" or act is None:
            num = (S.get("H") or {}).get("numero") if S["tipo"] == "capitulo" else 1
            act = {"numero": num or len(caps) + 1, "idx": [], "titulo": " ".join(w["text"] for w in (S.get("H") or {}).get("titulo") or [])}
            caps.append(act)
        act["idx"].append(i)
    for k, c in enumerate(caps):
        c["ini"] = offs[c["idx"][0]]
        c["fin"] = offs[caps[k + 1]["idx"][0]] if k + 1 < len(caps) else total
    return {"trabajo": trabajo, "E": E, "es": es, "offs": offs, "total": total, "caps": caps, "Y": YT.estado_y(trabajo),
            "por_clave": {S["clave"]: i for i, S in enumerate(es)}}


def cap_de(ctx, i):
    return next(c["numero"] for c in ctx["caps"] if i in c["idx"])


def fichas(trabajo):
    out = {}
    for f in glob.glob(os.path.join(trabajo, "fotos", "*.json")):
        try:
            d = leer(f)
            out[d.get("id") or os.path.basename(f)[:-5]] = d
        except (OSError, ValueError):
            pass
    return out


def toks_de(S):
    """Las palabras de la voz en fichas normalizadas: [(ficha, índice de palabra)] («US$256» son dos fichas de una palabra)."""
    out = []
    for i, w in enumerate(S.get("palabras") or []):
        for t in VD._plano(w["text"]).split():
            out.append((t, i))
    return out


def buscar(S, dice, desde=0):
    """Dónde dice la voz de la escena la frase `dice`, desde la ficha `desde` → (ficha inicial, palabra inicial, palabra final) o None."""
    T = toks_de(S)
    q = VD._plano(dice).split()
    if not q:
        return None
    ws = [t for t, _ in T]
    for j in range(desde, len(ws) - len(q) + 1):
        if ws[j:j + len(q)] == q:
            return j, T[j][1], T[j + len(q) - 1][1]
    return None


def segmentos(S):
    import youtube as YT
    return YT.segmentos(S)


# ---------- el plano: carga, tiempos y mesas ----------
def resolver(ctx, P):
    """Pone a cada golpe su segundo global (`_t`), el fin de su frase (`_fin`) y su escena (`_i`); arma las mesas del video en
    orden (las del plano, más los rótulos de capítulo, el cierre y lo que falte). → (mesas, fallas)."""
    es, offs, fallas = ctx["es"], ctx["offs"], []
    cubiertas, mesas = {}, []
    for k, M in enumerate((P or {}).get("mesas") or []):
        claves = [c for c in M.get("escenas") or [] if isinstance(c, str)]
        idx = [ctx["por_clave"].get(c) for c in claves]
        nom = "mesa %d (%s)" % (k + 1, ", ".join(claves)[:60])
        if not idx or any(i is None for i in idx):
            fallas.append("YT16 %s: escena que no existe en el montaje: %s" % (nom, [c for c, i in zip(claves, idx) if i is None]))
            continue
        if idx != list(range(idx[0], idx[0] + len(idx))):
            fallas.append("YT18 %s: sus escenas van seguidas y en orden" % nom)
            continue
        if any(i in cubiertas for i in idx):
            fallas.append("YT18 %s: una escena no va en dos mesas" % nom)
            continue
        tipos = {es[i]["tipo"] for i in idx}
        if tipos & set(PROPIAS):
            fallas.append("YT18 %s: los rótulos de capítulo y el cierre los arma el script: quítalos del plano" % nom)
            continue
        if tipos & set(TABLERO) and len(idx) > 1:
            fallas.append("YT18 %s: una escena %s (tablero) va sola en su mesa" % (nom, "/".join(sorted(tipos & set(TABLERO)))))
            continue
        cursor, golpes = {}, []
        for j, g in enumerate(M.get("golpes") or []):
            if not isinstance(g, dict):
                continue
            g = dict(g)
            cl = g.get("escena") or claves[0]
            if cl not in claves:
                fallas.append("YT16 %s golpe %d: su escena «%s» no es de esta mesa" % (nom, j + 1, cl))
                continue
            i = ctx["por_clave"][cl]
            S = es[i]
            dice = (g.get("dice") or "").strip()
            if not dice:
                if i == 0 and all(x.get("_ya") for x in golpes) and len(golpes) < 3:   # el primer cuadro del video no espera a la voz
                    g.update(_t=0.0, _fin=0.6, _i=i, _ya=True)
                    golpes.append(g)
                    continue
                fallas.append("YT14 %s golpe %d (%s): falta `dice` (las palabras de la voz que lo hacen entrar)" % (nom, j + 1, g.get("tipo")))
                continue
            r = buscar(S, dice, cursor.get(i, 0))
            if not r:
                antes = buscar(S, dice, 0)
                fallas.append("YT14 %s golpe %d: la voz de %s no dice «%s»%s" % (nom, j + 1, cl, dice, " después del golpe anterior (van en orden)" if antes else ""))
                continue
            cursor[i] = r[0]
            pal = S["palabras"]
            g.update(_t=round(offs[i] + pal[r[1]]["start"], 3), _fin=round(offs[i] + pal[r[2]]["end"], 3), _i=i)
            golpes.append(g)
        golpes.sort(key=lambda x: x["_t"])
        for i in idx:
            cubiertas[i] = True
        mesas.append({"idx": idx, "golpes": golpes, "clase": "tablero" if tipos & set(TABLERO) else "mesa", "titulo": M.get("titulo") or ""})
    for i, S in enumerate(es):
        if i in cubiertas:
            continue
        if S["tipo"] in PROPIAS:
            mesas.append({"idx": [i], "golpes": [], "clase": S["tipo"]})
        elif S["tipo"] in TABLERO:
            mesas.append({"idx": [i], "golpes": [], "clase": "tablero"})
        else:
            fallas.append("YT14 E%d (%s, %s): ninguna mesa del plano la cubre" % (S["n"], S["clave"], S["tipo"]))
            mesas.append({"idx": [i], "golpes": [], "clase": "mesa", "vacia": True})
    mesas.sort(key=lambda m: m["idx"][0])
    for k, M in enumerate(mesas):
        o = offs[M["idx"][0]]
        g1 = M["golpes"][0]["_t"] if M["golpes"] else o
        # la mesa anterior se queda hasta que la primera pieza de esta va a caer (sin mesa vacía entre las dos)
        M["ini"] = cuadro(o if (k == 0 or M["clase"] != "mesa" or mesas[k - 1]["clase"] in PROPIAS) else max(o, g1 - LEAD - 0.15))
        M["cap"] = cap_de(ctx, M["idx"][0])
    for k, M in enumerate(mesas):
        M["fin"] = mesas[k + 1]["ini"] if k + 1 < len(mesas) else ctx["total"]
        M["id"] = "m%d" % (k + 1)
    return mesas, fallas


def eventos_de(ctx, M):
    """Los segundos en que ENTRA algo en una mesa: [(t, 'pieza'|'marca'|'tablero', tipo)]."""
    ev = []
    for g in M["golpes"]:
        ev.append((g["_t"], "pieza", g.get("tipo")))
        for sub in subgolpes(ctx, g):
            ev.append((sub, "marca", g.get("tipo")))
    if M["clase"] == "tablero":
        i = M["idx"][0]
        for x in ctx["es"][i].get("eventos") or []:
            if x.get("tipo") in EVENTOS_TABLERO:
                ev.append((round(ctx["offs"][i] + x["t"], 3), "tablero", x["tipo"]))
    return sorted(ev)


def subgolpes(ctx, g):
    """Los segundos de lo que una pieza hace después de entrar (un subrayado, cada elemento de una lista, el lazo)."""
    S = ctx["es"][g["_i"]]
    o, out = ctx["offs"][g["_i"]], []

    def t_de(frase):
        r = buscar(S, frase or "", 0)
        return round(o + S["palabras"][r[1]]["start"], 3) if r else None
    if g.get("tipo") in ("documento", "cita"):
        a_, b_ = lectura(ctx, g)
        t = a_
        while a_ is not None and t < b_:
            if t > g["_t"] + 0.2:
                out.append(round(t, 3))
            t += 2.6
    if g.get("resalta_dice") and g.get("tipo") == "recorte":
        t = t_de(g["resalta_dice"])
        if t is not None and t > g["_t"] + 0.2:
            out.append(t)
    for it in (g.get("items") or [])[1:]:
        t = t_de(it.get("dice")) if isinstance(it, dict) else None
        if t is not None:
            out.append(t)
    if isinstance(g.get("lazo"), dict):
        t = t_de(g["lazo"].get("dice"))
        if t is not None:
            out.append(t)
    return out


def lectura(ctx, g):
    """De cuándo a cuándo la voz LEE un documento (`lee` … `lee_hasta`) o una cita (su texto): (t0, t1) o (None, None)."""
    S = ctx["es"][g["_i"]]
    o = ctx["offs"][g["_i"]]
    if g.get("tipo") == "documento":
        ini, fin = g.get("lee"), g.get("lee_hasta") or g.get("lee")
    else:
        pal = (g.get("texto") or "").split()
        ini, fin = " ".join(pal[:3]), " ".join(pal[-3:])
    a = buscar(S, ini or "", 0)
    if not a:
        return None, None
    b = buscar(S, fin or "", a[0]) or a
    return round(o + S["palabras"][a[1]]["start"], 3), round(o + S["palabras"][b[2]]["end"], 3)


# ---------- gates YT13–YT19 ----------
def numeros(txt):
    return {re.sub(r"[.,]", "", x) for x in re.findall(r"\d[\d.,]*\d|\d", txt or "")}


def textos_de(g):
    """Todo el texto que una pieza pone en pantalla (para YT13 y para el respaldo de sus números)."""
    partes = [g.get(c) for c in ("valor", "rotulo", "grande", "chico", "arriba", "texto", "definicion", "pie", "nombre", "kicker", "rol", "titulo",
                                 "subtitulo", "extracto", "titular", "persona", "cargo", "autor")]
    partes += [it.get("texto") for it in g.get("items") or [] if isinstance(it, dict)]
    partes += [p.get("nombre") for p in g.get("puntos") or [] if isinstance(p, dict)]
    return " ".join(str(x) for x in partes if x)


def notas_leidas():
    """Las notas guardadas por `historia.py leer`: {url: ficha}."""
    if not hasattr(notas_leidas, "c"):
        out = {}
        for f in glob.glob(os.path.join(RAIZ, "sesiones", "_descargas", "historia", "*.json")):
            try:
                d = leer(f)
            except (OSError, ValueError):
                continue
            if isinstance(d, dict) and d.get("url"):
                d["_json"] = f
                out[d["url"]] = d
        notas_leidas.c = out
    return notas_leidas.c


def texto_nota(n):
    for p in (n.get("archivo"), n["_json"][:-5] + ".txt"):
        if p and os.path.exists(p if os.path.isabs(p) else os.path.join(RAIZ, p)):
            return open(p if os.path.isabs(p) else os.path.join(RAIZ, p), encoding="utf-8", errors="ignore").read()
    return ""


def revisar(ctx, P, mesas=None, f0=None):
    """YT13–YT19 sobre el plano → (fallas, avisos, medidas)."""
    import youtube as YT
    es, offs = ctx["es"], ctx["offs"]
    if mesas is None:
        mesas, f0 = resolver(ctx, P)
    f, av = list(f0 or []), []
    F = fichas(ctx["trabajo"])
    elenco = YT.elenco_serie(ctx["Y"])
    nombres = {VD._plano(c) for p in elenco for c in p["claves"]} | {VD._plano(p["nombre"]) for p in elenco}
    try:
        respaldo = {re.sub(r"\.0+$", "", ("%f" % v).rstrip("0").rstrip(".")) for v in YT.valores_de(ctx["Y"]) if isinstance(v, (int, float))}
    except Exception:
        respaldo = set()
    PG = leer(os.path.join(ctx["trabajo"], "paginas.json")) if os.path.exists(os.path.join(ctx["trabajo"], "paginas.json")) else {}
    # lo que respalda un número o un nombre además de la voz de la mesa: todo lo que la voz dice en el video y los hechos
    # verificados de las escenas de la mesa (su texto, su fecha, sus citas, sus actores)
    todo_dicho = {x for S in es for w in S.get("palabras") or [] for x in numeros(w["text"])} | {EN_PALABRAS[t] for S in es for t, _ in toks_de(S) if t in EN_PALABRAS}
    try:
        H = YT.hechos_serie(ctx["Y"])
        hechos_de = {e.get("id"): e.get("hechos") or [] for e in leer(os.path.join(ctx["trabajo"], "indice.json")).get("escenas") or []}
    except (OSError, ValueError, KeyError):
        H, hechos_de = {}, {}

    def hechos_mesa(M):
        return [H[h] for i in M["idx"] for h in hechos_de.get(es[i]["clave"]) or [] if h in H]

    def personas_de(hs):
        out = set()
        for h in hs:
            for a_ in h.get("actores") or []:
                k = VD._plano(a_)
                if 2 <= len(k.split()) <= 6 and not INSTITUCION.search(k):
                    out |= {t for t in k.split() if len(t) > 3}
        return out
    voz_video = " ".join(VD._plano(w["text"]) for S in es for w in S.get("palabras") or [])
    usos, por_cap = {}, {}
    n_seg = n_nueva = 0
    for M in mesas:
        if M["clase"] in PROPIAS:
            continue
        nom = "%s E%s" % (M["id"], "–".join(str(es[i]["n"]) for i in (M["idx"][0], M["idx"][-1])) if len(M["idx"]) > 1 else es[M["idx"][0]]["n"])
        d = M["fin"] - M["ini"]
        if M["clase"] == "mesa" and not MESA_S[0] <= d <= MESA_S[1] and not M.get("vacia"):
            f.append("YT18 %s: la mesa dura %.1f s; va de %.0f a %.0f s (parte la mesa por tema, o únela a la vecina)" % (nom, d, *MESA_S))
        if len(M["golpes"]) > MESA_PIEZAS:
            f.append("YT18 %s: %d piezas en una mesa (máximo %d): parte la mesa" % (nom, len(M["golpes"]), MESA_PIEZAS))
        ev = eventos_de(ctx, M)
        voz_mesa = " ".join(VD._plano(w["text"]) for i in M["idx"] for w in es[i]["palabras"])
        dichos = {x for i in M["idx"] for w in es[i]["palabras"] for x in numeros(w["text"])}
        dichos |= {EN_PALABRAS[t] for i in M["idx"] for t, _ in toks_de(es[i]) if t in EN_PALABRAS}
        hs = hechos_mesa(M)
        de_hechos = numeros(" ".join(" ".join(str(x) for x in (h.get("texto"), h.get("fecha"))) + " " + " ".join(fu.get("cita") or "" for fu in h.get("fuentes") or []) for h in hs))
        apellidos = personas_de(hs)
        # YT14: cada oración trae un golpe; ningún hueco largo
        for i in M["idx"]:
            S = es[i]
            for sg in segmentos(S):
                if not (sg.get("texto") or "").strip():
                    continue
                a, b = offs[i] + sg["t"], offs[i] + sg["hasta"]
                dentro = [e for e in ev if a - 0.6 <= e[0] < b]
                n_seg += 1
                n_nueva += any(e[1] in ("pieza", "tablero") for e in dentro)
                if not dentro:
                    f.append("YT14 %s %s %.1f s: ninguna pieza entra con «%s»" % (nom, S["clave"], a, sg["texto"][:70]))
        ts = [M["ini"]] + [e[0] for e in ev] + [min(M["fin"], offs[M["idx"][-1]] + es[M["idx"][-1]].get("fin_voz", es[M["idx"][-1]]["dur"]))]
        for a, b in zip(ts, ts[1:]):
            if b - a > HUECO_MAX_S:
                f.append("YT14 %s: %.1f s sin que entre nada (de %.1f a %.1f s; máximo %.0f s)" % (nom, b - a, a, b, HUECO_MAX_S))
        ent = [g["_t"] for g in M["golpes"]]
        for a, b in zip(ent, ent[1:]):
            if b - a < ENTRE_GOLPES_S and b > 0.01:
                f.append("YT18 %s: dos piezas entran con %.2f s de diferencia en %.1f s (mínimo %.1f s): una lista, o separa los `dice`" % (nom, b - a, a, ENTRE_GOLPES_S))
        # YT13: cada cifra o año dicho se ve cuando se dice
        if M["clase"] == "mesa":
            for i in M["idx"]:
                for w in es[i]["palabras"]:
                    if not w.get("num"):
                        continue
                    t = offs[i] + w["start"]
                    ns = numeros(w["text"])
                    if not any(ns & numeros(textos_de(g)) and g["_t"] <= t + 1.0 for g in M["golpes"]):
                        f.append("YT13 %s %s %.1f s: la voz dice «%s» y ninguna pieza lo muestra" % (nom, es[i]["clave"], t, w["text"]))
        seguidos = 0
        for j, g in enumerate(M["golpes"]):
            t = g.get("tipo")
            q = "%s golpe %d (%s, %.1f s)" % (nom, j + 1, t, g["_t"])
            if t not in TIPOS:
                f.append("YT16 %s: tipo desconocido; van %s" % (q, " · ".join(TIPOS)))
                continue
            por_cap.setdefault(M["cap"], []).append(g)
            seguidos = seguidos + 1 if t in SOLO_TEXTO else 0
            if seguidos > TEXTO_SEGUIDOS:
                f.append("YT17 %s: %d rótulos de solo texto seguidos (máximo %d): pon un archivo real entre ellos" % (q, seguidos, TEXTO_SEGUIDOS))
            # los números que una pieza pone en pantalla: dichos por la voz de la mesa o con respaldo
            if t not in ("recorte", "documento", "cita"):
                propios = numeros(" ".join(str(g.get(c) or "") for c in ("valor", "grande", "chico", "arriba", "rotulo", "texto", "definicion", "rol")))
                sin = sorted(x for x in propios if x not in dichos and x not in respaldo and x not in todo_dicho and x not in de_hechos
                             and not (t == "fecha" and len(x) <= 2))
                if sin:
                    f.append("YT16 %s: «%s» no lo dice la voz, no está en los hechos de la mesa ni tiene respaldo en los datos" % (q, ", ".join(sin)))
            if t == "foto":
                r = F.get(g.get("foto"))
                if not r or not r.get("credito") or not os.path.exists(os.path.join(ctx["trabajo"], r.get("archivo") or "x")):
                    f.append("YT16 %s: la foto «%s» no tiene ficha, crédito o archivo (historia.py foto)" % (q, g.get("foto")))
                    continue
                usos.setdefault(g["foto"], []).append(g["_t"])
                if not (g.get("pie") or "").strip() or len(g["pie"].split()) > 9:
                    f.append("YT16 %s: `pie` de 1 a 9 palabras que diga qué se ve" % q)
                oracion = VD._plano(" ".join(w["text"] for w in es[g["_i"]]["palabras"]))
                if (JUDICIAL.search(r.get("descripcion") or "") or r.get("retrato_de")) and not any(n and n in oracion for n in nombres) \
                        and not (apellidos & set(oracion.split())):
                    f.append("YT16 %s: «%s» muestra a personas en un proceso o es un retrato, y la voz de %s no nombra a nadie: ahí da a entender "
                             "que son los acusados; usa un edificio, un documento o un recorte" % (q, g["foto"], es[g["_i"]]["clave"]))
            elif t == "recorte":
                n = notas_leidas().get(g.get("url"))
                if not n:
                    f.append("YT16 %s: `url` de una nota ya leída con historia.py leer" % q)
                    continue
                cuerpo = VD._plano(texto_nota(n))
                if g.get("titular") and VD._plano(g["titular"]) != VD._plano(n.get("titulo") or ""):
                    f.append("YT16 %s: el titular no es el de la nota («%s»)" % (q, (n.get("titulo") or "")[:80]))
                if g.get("extracto") and VD._plano(g["extracto"]) not in cuerpo:
                    f.append("YT16 %s: el extracto no está literal en la nota guardada" % q)
                if g.get("resalta") and g["resalta"] not in (g.get("extracto") or ""):
                    f.append("YT16 %s: `resalta` es un trozo literal del extracto" % q)
                if not (g.get("medio") and g.get("fecha") and (g.get("titular") or g.get("extracto"))):
                    f.append("YT16 %s: lleva medio, fecha y titular o extracto" % q)
            elif t == "documento":
                if g.get("pagina"):
                    if g["pagina"] not in PG:
                        f.append("YT16 %s: la página «%s» no está en paginas.json (historia.py pagina)" % (q, g["pagina"]))
                elif not (isinstance(g.get("portada"), dict) and notas_leidas().get(g["portada"].get("url")) and g.get("titulo")):
                    f.append("YT16 %s: lleva `pagina` (historia.py pagina) o `portada` {url de un PDF ya leído, pagina} con `titulo`" % q)
            elif t == "persona":
                p = next((p for p in elenco if VD._plano(g.get("persona") or "") in [VD._plano(p["nombre"])] + [VD._plano(c) for c in p["claves"]]), None)
                # alguien que no es del elenco: su nombre lo dice la voz (en esta mesa o antes, con nombre y apellido)
                if not p and not (g.get("cargo") and (VD._plano(g.get("persona") or "") in voz_mesa or VD._plano(g.get("persona") or "") in voz_video)):
                    f.append("YT16 %s: «%s» no es del elenco: lleva el nombre como lo dice la voz y su `cargo`" % (q, g.get("persona")))
            elif t == "institucion":
                if not (g.get("nombre") and (g.get("kicker") or g.get("rol"))):
                    f.append("YT16 %s: lleva nombre y kicker o rol (qué es)" % q)
            elif t == "lugar":
                if g.get("mapa") == "guatemala":
                    if not g.get("depto"):
                        f.append("YT16 %s: el mapa de Guatemala lleva `depto`" % q)
                elif g.get("mapa") == "mundo":
                    for p in g.get("puntos") or []:
                        if not (isinstance(p, dict) and p.get("nombre") and (VD._plano(p["nombre"]) in LUGARES or ("lon" in p and "lat" in p))):
                            f.append("YT16 %s: el punto «%s» no está en la lista de lugares: ponle lon y lat" % (q, (p or {}).get("nombre")))
                    if not g.get("puntos"):
                        f.append("YT16 %s: el mapa del mundo lleva `puntos`" % q)
                else:
                    f.append("YT16 %s: `mapa` es «guatemala» o «mundo»" % q)
            elif t == "fecha" and not g.get("grande"):
                f.append("YT16 %s: lleva `grande` (el año o el día)" % q)
            elif t == "cifra" and not (g.get("valor") and g.get("rotulo")):
                f.append("YT16 %s: lleva `valor` y `rotulo` (de qué es la cifra)" % q)
            elif t == "termino" and (not g.get("texto") or len(g["texto"].split()) > 6):
                f.append("YT16 %s: `texto` de 1 a 6 palabras" % q)
            elif t == "cita" and not (g.get("texto") and g.get("autor")):
                f.append("YT16 %s: lleva `texto` literal y `autor`" % q)
            elif t == "lista" and not (isinstance(g.get("items"), list) and 2 <= len(g["items"]) <= 6):
                f.append("YT16 %s: `items` son 2 a 6 {texto, dice}" % q)
    # YT15: una foto, pocas veces y lejos
    for fid, ts in sorted(usos.items()):
        if len(ts) > FOTO_USOS_MAX:
            f.append("YT15 la foto %s sale %d veces (máximo %d): %s" % (fid, len(ts), FOTO_USOS_MAX, ", ".join(VD.mmss(t) if hasattr(VD, "mmss") else "%.0f s" % t for t in ts)))
        for a, b in zip(ts, ts[1:]):
            if b - a < FOTO_SEPARACION_S:
                f.append("YT15 la foto %s vuelve a los %.0f s (mínimo %d s entre una y otra): %.0f s y %.0f s" % (fid, b - a, FOTO_SEPARACION_S, a, b))
    # YT17: que no sea relleno
    medidas = {"oraciones": n_seg, "con_pieza_nueva": n_nueva, "capitulos": {}}
    if n_seg and n_nueva / n_seg < PIEZA_NUEVA_MIN:
        f.append("YT17 solo %d de %d oraciones traen una pieza nueva (mínimo %.0f %%)" % (n_nueva, n_seg, 100 * PIEZA_NUEVA_MIN))
    tab = {}
    for M in mesas:
        if M["clase"] == "tablero":
            tab[M["cap"]] = tab.get(M["cap"], 0) + 1
    for cap, gs in sorted(por_cap.items()):
        tipos = sorted({g["tipo"] for g in gs})
        real = sum(1 for g in gs if g["tipo"] in ARCHIVO or (g["tipo"] == "persona" and retrato_de(elenco, g))) + tab.get(cap, 0)
        n = len(gs) + tab.get(cap, 0)
        medidas["capitulos"][cap] = {"piezas": n, "archivo_real": real, "tipos": tipos}
        if len(tipos) < TIPOS_MIN:
            f.append("YT17 capítulo %d: %d tipos de pieza (%s); van al menos %d distintos" % (cap, len(tipos), ", ".join(tipos), TIPOS_MIN))
        if n and real / n < ARCHIVO_MIN:
            f.append("YT17 capítulo %d: %d de %d piezas son archivo real (%.0f %%; mínimo %.0f %%): más fotos, recortes, documentos y mapas"
                     % (cap, real, n, 100 * real / n, 100 * ARCHIVO_MIN))
        elif n and real / n < 0.5:
            av.append("YT17 capítulo %d: %.0f %% de archivo real (%d de %d); la meta es 50 %%" % (cap, 100 * real / n, real, n))
    # YT19: nada de cámara para aparentar ritmo
    for S in es:
        if S.get("saltos"):
            f.append("YT19 E%d lleva saltos de cámara: en el 16:9 la cámara no se mueve" % S["n"])
    return f, av, medidas


def retrato_de(elenco, g):
    k = VD._plano(g.get("persona") or "")
    p = next((p for p in elenco if k in [VD._plano(p["nombre"])] + [VD._plano(c) for c in p["claves"]]), None)
    return p if p and p.get("foto") else None


# ---------- borrador: lo que las escenas ya traen ----------
def borrador(ctx):
    """Un plano de partida con lo que cada escena ya trae (su foto, su cifra, los años y las cifras que dice la voz, las personas
    que nombra, la cita, la definición). El realizador lo mejora; la maqueta lo usa tal cual."""
    import youtube as YT
    es = ctx["es"]
    elenco = YT.elenco_serie(ctx["Y"])
    F = fichas(ctx["trabajo"])
    mesas, act, dur = [], None, 0.0
    for i, S in enumerate(es):
        if S["tipo"] in PROPIAS:
            act = None
            continue
        gs = []
        pal = S.get("palabras") or []

        def frase(k0, n=2):
            return " ".join(w["text"] for w in pal[k0:k0 + n])
        N, H, T = S.get("N") or {}, S.get("H") or {}, S.get("T") or {}
        fid = YT.foto_id(N.get("foto")) if N.get("foto") else None
        if fid and fid in F and pal:
            tit = " ".join(w["text"] for w in N.get("titular") or [] if isinstance(w, dict))
            gs.append((0, {"tipo": "foto", "escena": S["clave"], "dice": frase(0), "foto": fid, "pie": " ".join((tit or F[fid].get("descripcion") or "").split()[:8])}))
        if S["tipo"] == "cita" and H.get("texto"):
            txt = " ".join(w["text"] for w in H["texto"])
            r = buscar(S, " ".join(txt.split()[:3]), 0)
            gs.append((r[1] if r else 0, {"tipo": "cita", "escena": S["clave"], "dice": frase(r[1] if r else 0, 3), "texto": txt, "autor": H.get("autor") or "",
                                          "cargo": H.get("cargo") or ""}))
        if S["tipo"] in ("definicion", "golpe") and (T.get("pant") or {}).get("texto"):
            linea = " ".join(w["text"] for w in T.get("linea") or [])
            gs.append((0, {"tipo": "termino", "escena": S["clave"], "dice": frase(0), "texto": T["pant"]["texto"], "definicion": linea if S["tipo"] == "definicion" else ""}))
        if S["tipo"] not in TABLERO:
            for k, w in enumerate(pal):
                if not w.get("num"):
                    continue
                txt = w["text"].strip(" ,.;:")
                if re.fullmatch(r"(1[89]|20)\d\d", txt):
                    gs.append((k, {"tipo": "fecha", "escena": S["clave"], "dice": w["text"], "grande": txt, "chico": pal[k - 1]["text"] if k and pal[k - 1]["text"].lower() in ("en", "desde", "hasta") else "año"}))
                else:
                    cif = N.get("cifra") or {}
                    rot = cif.get("etiqueta") if cif and numeros(cif.get("texto")) & numeros(txt) else " ".join(x["text"] for x in pal[k + 1:k + 3]).strip(" ,.;:")
                    gs.append((k, {"tipo": "cifra", "escena": S["clave"], "dice": w["text"], "valor": (cif.get("texto") if cif and numeros(cif.get("texto")) & numeros(txt) else txt),
                                   "rotulo": rot or "cifra"}))
            for j, ts in YT.nombradas(S, elenco).items():
                k = next((k for k, w in enumerate(pal) if abs(w["start"] - ts[0]) < 0.01), 0)
                gs.append((k, {"tipo": "persona", "escena": S["clave"], "dice": frase(k, 2), "persona": elenco[j]["nombre"], "cargo": elenco[j]["cargo"]}))
        gs = [g for _, g in sorted(gs, key=lambda x: x[0])]
        nueva = (act is None or S["tipo"] in TABLERO or act.get("_tab") or dur + S["dur"] > 26 or len(act["escenas"]) >= 3)
        if nueva:
            act = {"escenas": [], "golpes": [], "_tab": S["tipo"] in TABLERO}
            mesas.append(act)
            dur = 0.0
        act["escenas"].append(S["clave"])
        act["golpes"] += gs
        dur += S["dur"]
    for m in mesas:
        m.pop("_tab", None)
    return {"version": 1, "mesas": mesas}


# ---------- tamaños y colocación ----------
def renglones(txt, px, ancho, cond=True):
    """Cuántos renglones ocupa un texto (estimado: la condensada mide ≈ 0.40 em por carácter; la normal, 0.52)."""
    por = max(4, int(ancho / (px * (0.455 if cond else 0.52))))
    n, linea = 1, 0
    for p in (txt or "").split():
        if linea and linea + 1 + len(p) > por:
            n, linea = n + 1, len(p)
        else:
            linea += (1 if linea else 0) + len(p)
    return n


def tam_nombre(txt, ancho, maximo=104, minimo=64):
    """El cuerpo de un nombre: en un renglón si cabe a ≥ 72 px; si no, el mayor que quepa en dos."""
    for px in range(maximo, 71, -6):
        if renglones(txt, px, ancho) == 1:
            return px
    for px in range(maximo, minimo - 1, -6):
        if renglones(txt, px, ancho) <= 2:
            return px
    return minimo


def medida(ctx, g, F, ancho_max, elenco):
    """(ancho, alto, extras) de una pieza. `ancho_max` es lo que deja la mesa (con un tablero, la columna derecha)."""
    t = g["tipo"]
    if g.get("w"):
        ancho_max = min(ancho_max, int(g["w"]))
    if t == "foto":
        r = F.get(g.get("foto")) or {}
        tw, th = (r.get("tamano") or [1600, 1000])[:2]
        rc = g.get("recorte") if isinstance(g.get("recorte"), list) and len(g["recorte"]) == 4 else [0, 0, 1, 1]
        a = (tw * rc[2]) / max(1.0, th * rc[3])
        w = min(ancho_max, int(g.get("w") or (840 if a >= 1.25 else 620 if a >= 0.9 else 460)))
        hi = int(min((w - 28) / a, 540 if a >= 0.9 else 600))
        hi = max(hi, int((w - 28) / 2.4))
        return w, hi + 14 + 46 + 34 * renglones(g.get("pie"), 28, w - 40, False), {"hi": hi, "a": a, "rc": rc}
    if t == "recorte":
        w = min(ancho_max, 900)
        h = 26 + 62 + (18 + 58 * renglones(g.get("titular"), 56, w - 64) if g.get("titular") else 0) + \
            (16 + 50 * renglones("«%s»" % g.get("extracto"), 38, w - 64, False) if g.get("extracto") else 0) + 30
        return w, h, {}
    if t in ("persona", "institucion"):
        nombre = g.get("persona") or g.get("nombre") or ""
        ret = retrato_de(elenco, g) if t == "persona" else None
        w = min(ancho_max, 1100 if len(nombre) > 22 else 780)
        dentro = w - 72 - (238 if ret else 0)
        px = tam_nombre(nombre, dentro)
        rol = g.get("cargo") if t == "persona" else g.get("rol")
        h = 12 + 30 + 34 + 12 + int(px * 0.94) * renglones(nombre, px, dentro) + (14 + 38 * renglones(rol, 32, dentro, False) if rol else 0) + \
            (34 if g.get("fuente") else 0) + 30
        return w, max(h, 322 if ret else 0), {"px": px, "ret": ret}
    if t == "lugar":
        if g.get("mapa") == "guatemala":
            return 432, 450 + 60 + 32, {}
        A = atlas(g.get("puntos") or [], min(ancho_max - 32, 1150))
        return A["w"] + 32, A["h"] + 32, {"A": A}
    if t == "fecha":
        if g.get("estilo") == "calendario":
            return 360, 340, {}
        w = max(400, int(len(str(g.get("grande") or "")) * 168 * 0.43) + 92)
        return min(w, ancho_max), 276, {}
    if t == "cifra":
        v = str(g.get("valor") or "")
        px = 236 if len(v) <= 4 else 170 if len(v) <= 7 else 124 if len(v) <= 11 else 96
        w = min(ancho_max, max(400, int(len(v) * px * 0.44) + 76))
        cu = int(g.get("cuadros") or 0)
        h = 22 + int(px * 0.94) + 4 + 44 * renglones(g.get("rotulo"), 44, w - 72) + (14 + 42 * math.ceil(cu / 6) if cu else 0) + (34 if g.get("fuente") else 0) + 26
        return w, h, {"px": px}
    if t == "termino":
        if g.get("definicion"):
            w = min(ancho_max, 860)
            px = tam_nombre(g["texto"], w - 72, 96)
            return w, 12 + 30 + 34 + 12 + int(px * 0.94) * renglones(g["texto"], px, w - 72) + 14 + 38 * renglones(g["definicion"], 32, w - 72, False) + 30, {"px": px}
        w = min(ancho_max, max(380, int(len(g.get("texto") or "") * 66 * 0.47) + 84))
        return w, 50 + 62 * renglones(g.get("texto"), 66, w - 68), {}
    if t == "cita":
        w = min(ancho_max, 1020)
        return w, 68 + 55 * renglones("«%s»" % g.get("texto"), 44, w - 102, False) + 20 + 40 + (34 if g.get("cargo") else 0), {}
    if t == "documento":
        D = doc_de(ctx, g)
        if ancho_max < 900 and D.get("frase"):
            w = ancho_max
            return w, 34 + 30 + 52 * renglones(g.get("titulo") or D["tab"][0], 50, w - 76) + 16 + 46 * renglones("«%s»" % D["frase"], 34, w - 76, False) + 34, {"D": D, "texto": True}
        w = min(ancho_max, D["w"])
        return w, int(D["h"] * w / D["w"]), {"D": D, "k": w / D["w"]}
    if t == "lista":
        largo = max([len((it or {}).get("texto") or "") for it in g.get("items") or []] or [6])
        ficha_w = int(largo * 52 * 0.455) + 56
        corr = max(0, min(200, ancho_max - ficha_w - 40))
        return min(ancho_max, ficha_w + corr + 40), 104 * len(g.get("items") or []) + (70 if g.get("lazo") else 20), {"ficha_w": ficha_w, "corr": corr}
    return 400, 200, {}


def colocar(piezas, tablero=False):
    """Coloca las piezas de una mesa en el orden en que entran: cada una busca el sitio que menos tapa a las tres últimas y
    queda cerca de la anterior (la vista no salta). → [(x, y)]. Un golpe con `x`,`y` se respeta."""
    X0, X1, Y0, Y1 = (1160 if tablero else 100), 1824, 58, 1012
    puestos, out = [], []
    for k, (w, h, g) in enumerate(piezas):
        if g.get("x") is not None and g.get("y") is not None:   # a mano, pero nunca fuera del cuadro
            pos = (max(40, min(int(g["x"]), 1880 - w)), max(30, min(int(g["y"]), 1050 - h)))
        else:
            mejor, pos = None, (X0, Y0)
            for y in range(Y0, max(Y0, Y1 - h) + 1, 24):
                for x in range(X0, max(X0, X1 - w) + 1, 24):
                    s = 0.0
                    for edad, (px, py, pw, ph) in enumerate(reversed(puestos)):
                        ox = max(0, min(x + w, px + pw) - max(x, px))
                        oy = max(0, min(y + h, py + ph) - max(y, py))
                        tapa = ox * oy / float(pw * ph)
                        # tapar a una de las tres últimas es lo peor; tapar a una vieja (ya atenuada) también cuesta: primero la mesa vacía
                        s += tapa * (16.0 if edad == 0 else 10.0 if edad == 1 else 5.0 if edad == 2 else 1.6) * 1000
                    if puestos:
                        px, py, pw, ph = puestos[-1]
                        d = math.hypot((x + w / 2) - (px + pw / 2), (y + h / 2) - (py + ph / 2))
                        s += max(0.0, d - 1000) * 0.25
                    else:
                        s += (x - X0) * 0.4 + (y - Y0) * 0.6
                    s += (y - Y0) * 0.05 + (x - X0) * 0.01
                    if mejor is None or s < mejor:
                        mejor, pos = s, (x, y)
        puestos.append((pos[0], pos[1], w, h))
        out.append(pos)
    if puestos and not any(g.get("x") is not None for _, _, g in piezas):   # el conjunto, centrado en su zona (no arrinconado arriba a la izquierda)
        dx = int(((X0 + X1) - (min(p[0] for p in puestos) + max(p[0] + p[2] for p in puestos))) / 2)
        dy = int(((Y0 + Y1) - (min(p[1] for p in puestos) + max(p[1] + p[3] for p in puestos))) / 2)
        out = [(x + max(0, dx), y + max(0, dy)) for x, y in out]
    return out


# ---------- mapas ----------
def atlas(puntos, ancho=1150):
    """Un mapa del mundo (Natural Earth 50 m, dominio público: design/mapas/paises-50m.json) encuadrado en sus puntos."""
    pts = []
    for p in puntos:
        if not isinstance(p, dict):
            continue
        lo, la = (p["lon"], p["lat"]) if "lon" in p and "lat" in p else LUGARES.get(VD._plano(p.get("nombre") or ""), (None, None))
        if lo is not None:
            pts.append((p.get("nombre") or "", float(lo), float(la)))
    if not pts:
        pts = [("Guatemala", -90.52, 14.63)]
    lons, lats = [p[1] for p in pts], [p[2] for p in pts]
    L0, L1, B0, B1 = min(lons) - 5, max(lons) + 5, min(lats) - 5.5, max(lats) + 5.5
    phi = math.radians((B0 + B1) / 2)
    if (L1 - L0) * math.cos(phi) / (B1 - B0) < 1.9:   # proporción ≈ 2:1 (una tira de atlas)
        extra = (1.9 * (B1 - B0) / math.cos(phi) - (L1 - L0)) / 2
        L0, L1 = L0 - extra, L1 + extra
    else:
        extra = ((L1 - L0) * math.cos(phi) / 1.9 - (B1 - B0)) / 2
        B0, B1 = B0 - extra, B1 + extra
    k = ancho / ((L1 - L0) * math.cos(phi))
    alto = int((B1 - B0) * k)

    def P(lon, lat):
        return ((lon - L0) * math.cos(phi) * k, (B1 - lat) * k)
    if not hasattr(atlas, "T"):
        T = leer(os.path.join(RAIZ, "design", "mapas", "paises-50m.json"))
        sx, sy = T["transform"]["scale"]
        tx, ty = T["transform"]["translate"]
        arcs = []
        for a in T["arcs"]:
            x = y = 0
            ps = []
            for dx, dy in a:
                x += dx
                y += dy
                ps.append((x * sx + tx, y * sy + ty))
            arcs.append(ps)
        atlas.T = (T, arcs)
    T, arcs = atlas.T
    tierra, gt = [], []
    for geo in T["objects"]["countries"]["geometries"]:
        polys = [geo["arcs"]] if geo["type"] == "Polygon" else geo["arcs"] if geo["type"] == "MultiPolygon" else []
        for poly in polys:
            for ring in poly:
                ps = []
                for i in ring:
                    a = arcs[i] if i >= 0 else arcs[~i][::-1]
                    ps += a if not ps else a[1:]
                if not any(L0 - 4 < lo < L1 + 4 and B0 - 4 < la < B1 + 4 for lo, la in ps):
                    continue
                paso = max(1, len(ps) // 900)
                d = "M" + "L".join("%.1f %.1f" % P(lo, la) for lo, la in ps[::paso]) + "Z"
                (gt if geo.get("id") == "320" else tierra).append(d)
    return {"w": int(ancho), "h": alto, "tierra": "".join(tierra), "gt": "".join(gt), "pts": [(n, *P(lo, la)) for n, lo, la in pts]}


def deptos():
    """Los 22 departamentos (design/mapa_geometria.svg): [(d, id, nombre, (cx, cy))]."""
    if not hasattr(deptos, "c"):
        s = open(os.path.join(RAIZ, "design", "mapa_geometria.svg"), encoding="utf-8").read()
        out = []
        for m in re.finditer(r"<path\b([^>]*)>", s):
            at = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
            if not re.fullmatch(r"GT\d\d", at.get("id") or ""):
                continue
            x = y = 0.0
            pts, cmd, buf = [], None, []
            for t in re.findall(r"[MmLlZz]|-?\d+\.?\d*", at["d"]):
                if t in "MmLlZz":
                    cmd, buf = t, []
                    continue
                buf.append(float(t))
                if len(buf) == 2:
                    x, y = (buf[0], buf[1]) if cmd in "ML" else (x + buf[0], y + buf[1])
                    pts.append((x, y))
                    buf = []
                    cmd = "L" if cmd == "M" else "l" if cmd == "m" else cmd
            out.append((at["d"], at["id"], at.get("name") or "", (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))))
        deptos.c = out
    return deptos.c


# ---------- documentos ----------
def pdf_de(url):
    n = notas_leidas().get(url)
    if not n:
        return None
    p = n["_json"][:-5] + ".pdf"
    return p if os.path.exists(p) else None


def pagina_png(trabajo, url, pagina, dpi=200):
    """La página de un PDF ya leído como imagen (fotos/_doc-<hash>-p<N>.jpg, con poppler). → (ruta relativa al TRABAJO, ancho, alto) o None."""
    pdf = pdf_de(url)
    if not pdf or not shutil.which("pdftoppm"):
        return None
    base = "_doc-%s-p%d" % (hashlib.sha1(url.encode()).hexdigest()[:8], pagina)
    dst = os.path.join(trabajo, "fotos", base + ".jpg")
    if not os.path.exists(dst):
        tmp = os.path.join(trabajo, "fotos", base)
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(pagina), "-l", str(pagina), "-jpeg", "-jpegopt", "quality=88", "-singlefile", pdf, tmp], check=False)
    if not os.path.exists(dst):
        return None
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout.strip().split(",")
    return "fotos/" + base + ".jpg", int(r[0]), int(r[1])


def doc_de(ctx, g):
    """Lo que hace falta para dibujar un documento: la imagen de la página, el recorte que se ve y los renglones a subrayar."""
    trabajo = ctx["trabajo"]
    if g.get("pagina"):
        PG = leer(os.path.join(trabajo, "paginas.json"))[g["pagina"]]
        img = pagina_png(trabajo, PG.get("url") or "", int(PG.get("pagina") or 1)) if PG.get("url") else None
        if not img:
            arch = os.path.join(trabajo, PG["archivo"])
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", arch], capture_output=True, text=True).stdout.strip().split(",")
            img = (PG["archivo"], int(r[0]), int(r[1]))
        L = PG.get("lineas") or []
        y0 = max(0.0, min(l[1] for l in L) - 0.12) if L else 0.1
        y1 = min(1.0, max(l[1] + l[3] for l in L) + 0.08) if L else 0.45
        x0, x1 = 0.08, 0.92
        w = 1040
        k = w / ((x1 - x0) * img[1])
        tit = g.get("titulo") or ""
        tab_h = 40 + 44 * renglones(tit, 44, 700) + 16   # la pestaña va abajo: la página se alarga para que no tape lo subrayado
        return {"img": img[0], "w": w, "h": int((y1 - y0) * img[2] * k) + tab_h, "k": k, "x0": x0, "y0": y0, "pw": img[1], "ph": img[2], "lineas": L,
                "tab": ((PG.get("fuente") or "")[:60], tit), "frase": PG.get("frase") or ""}
    po = g.get("portada") or {}
    img = pagina_png(trabajo, po.get("url") or "", int(po.get("pagina") or 1))
    if not img:
        return {"img": None, "w": 640, "h": 600, "k": 1, "x0": 0, "y0": 0, "pw": 640, "ph": 600, "lineas": [], "tab": (g.get("kicker") or "", g.get("titulo") or ""), "sub": g.get("subtitulo") or ""}
    x0, x1, y0 = 0.09, 0.91, 0.045
    w = 640
    k = w / ((x1 - x0) * img[1])
    return {"img": img[0], "w": w, "h": 600, "k": k, "x0": x0, "y0": y0, "pw": img[1], "ph": img[2], "lineas": [], "tab": (g.get("kicker") or "", g.get("titulo") or ""),
            "sub": g.get("subtitulo") or "", "abajo": True}


# ---------- una mesa → HTML + línea de tiempo ----------
class Mesa:
    def __init__(self, mid, ini, fin, barrer, css):
        self.id, self.ini, self.fin, self.barrer, self.css = mid, ini, fin, barrer, css
        self.html, self.tl, self.piezas, self.sfx, self.k, self.extra, self.f = [], [], [], [], 0, [], 1.0

    def loc(self, g):
        return round(max(0.0, g - self.ini), 3)

    def pieza(self, g, x, y, w, giro, dentro, sfx="papel", ya=False, sombra=True, velo=True):
        if self.f != 1:   # la mesa va llena: todo a escala (zoom de Chrome: el texto se vuelve a dibujar nítido)
            dentro = '<div style="zoom:%.3f;width:%dpx">%s</div>' % (self.f, w, dentro)
            w = int(w * self.f)
        self.k += 1
        pid = "%s-p%d" % (self.id, self.k)
        t0 = 0.0 if ya else self.loc(g - LEAD)
        dx = -130 if x + w / 2 < 760 else 130 if x + w / 2 > 1160 else 0
        dy = 100 if y > 520 else -90
        self.html.append(
            '<div id="%s" class="clip pz" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-layout-allow-overlap '
            'data-layout-allow-occlusion style="left:%dpx;top:%dpx;width:%dpx;z-index:%d"><div id="%s-mov" class="mov">'
            '<div id="%s-pila" class="pila"%s>%s%s</div></div></div>'
            % (pid, t0, max(0.1, round(self.fin - self.ini - t0, 3)), 1 + self.k % 6, x, y, w, 10 + self.k, pid, pid,
               "" if sombra else ' style="box-shadow:none"', dentro, '<i id="%s-velo" class="velo"></i>' % pid if velo else ""))
        if ya:
            self.tl.append('tl.set("#%s-mov",{rotation:%s},0);' % (pid, giro))
        else:
            self.tl.append('tl.fromTo("#%s-mov",{x:%d,y:%d,rotation:%s,scale:1.1,opacity:0},{x:0,y:0,rotation:%s,scale:1,opacity:1,duration:%.2f,'
                           'ease:"power3.out"},%.3f);' % (pid, dx, dy, giro + (5 if giro >= 0 else -5), giro, ENTRA, t0))
            if sfx:
                self.sfx.append((round(self.ini + t0 + ENTRA * 0.55, 3), sfx))
        self.piezas.append({"id": pid, "t0": t0, "giro": giro, "velo": velo})
        return pid

    def cerrar(self):
        P = self.piezas
        for i, p in enumerate(P):
            if p["velo"] and i + VISIBLES < len(P):
                self.tl.append('tl.fromTo("#%s-velo",{opacity:0},{opacity:.5,duration:.45,ease:"power1.out"},%.3f);' % (p["id"], P[i + VISIBLES]["t0"] + 0.1))
        if self.barrer:
            t = round(self.fin - self.ini - 0.46, 3)
            if t > 0.2:
                for i, p in enumerate(P):
                    self.tl.append('tl.fromTo("#%s-mov",{x:0,y:0,rotation:%s},{x:-2400,y:%d,rotation:%s,duration:.42,ease:"power2.in",immediateRender:false},%.3f);'
                                   % (p["id"], p["giro"], 30 + 12 * (i % 3), p["giro"] - 9, t + 0.012 * i))
                for sel in self.extra:
                    self.tl.append('tl.fromTo("%s",{x:0},{x:-2400,duration:.42,ease:"power2.in",immediateRender:false},%.3f);' % (sel, t))
                self.sfx.append((round(self.fin - 0.34, 3), "whoosh"))
        return ('<template>\n<style>%s</style>\n<div id="root" data-composition-id="%s" data-width="1920" data-height="1080">\n%s\n</div>\n'
                '<script>\n(function(){\nconst tl = gsap.timeline({paused:true});\n%s\nwindow.__timelines["%s"] = tl;\n})();\n</script>\n</template>\n'
                % (self.css, self.id, "\n".join(self.html), "\n".join(self.tl), self.id))


GIROS = [-2, 3, -1.5, 2, -3, 1.5, -2.5, 2.5, -1, 3.5, -3.5, 1]


def dibujar(ctx, m, g, x, y, w, h, ex, k, F, usados):
    """Una pieza del plano → su HTML dentro de la mesa `m` (y sus animaciones propias)."""
    t, T = g["tipo"], g["_t"]
    C = ctx["C"]
    giro = g.get("giro", GIROS[k % len(GIROS)])
    ya = bool(g.get("_ya"))
    pid = "%s-p%d" % (m.id, m.k + 1)
    S = ctx["es"][g["_i"]]
    o = ctx["offs"][g["_i"]]

    def t_de(frase, por=None):
        r = buscar(S, frase or "", 0)
        return round(o + S["palabras"][r[1]]["start"], 3) if r else por

    def fin_de(frase, por=None):
        r = buscar(S, frase or "", 0)
        return round(o + S["palabras"][r[2]]["end"], 3) if r else por
    if t == "foto":
        r = F[g["foto"]]
        usados.add(r["archivo"])
        rc, hi, wi = ex["rc"], ex["hi"], w - 28
        tw, th = (r.get("tamano") or [1600, 1000])[:2]
        cw, ch = tw * rc[2], th * rc[3]
        s = max(wi / cw, hi / ch)
        fx, fy = (g.get("pos") or [0.5, 0.4])[:2]
        ix = -(rc[0] * tw * s) - max(0, cw * s - wi) * fx
        iy = -(rc[1] * th * s) - max(0, ch * s - hi) * fy
        cred = (r.get("credito") or "") + (" · %s" % str(r["fecha"])[:4] if r.get("fecha") and str(r["fecha"])[:4] not in (g.get("pie") or "") else "")
        dentro = ('<div class="foto"><div class="im" style="width:%dpx;height:%dpx"><img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx" alt=""></div>'
                  '<div class="pie"><b>%s</b><span data-layout-ignore>%s</span></div></div>' % (wi, hi, r["archivo"], ix, iy, tw * s, th * s, esc(g.get("pie")), esc(cred)))
        m.pieza(T, x, y, w, giro, dentro, ya=ya)
    elif t == "recorte":
        ext = g.get("extracto") or ""
        if g.get("resalta") and g["resalta"] in ext:
            a, b = ext.split(g["resalta"], 1)
            cuerpo = "«%s<span id=\"%s-hl\" class=\"hl\">%s</span>%s»" % (esc(a), pid, esc(g["resalta"]), esc(b))
        else:
            cuerpo = "«%s»" % esc(ext)
        dentro = ('<div class="recorte"><div class="cab"><div class="m cond">%s</div><div class="d" data-layout-ignore>%s</div></div>%s%s</div>'
                  % (esc(g.get("medio")), esc(g.get("fecha")), '<div class="t cond">%s</div>' % esc(g["titular"]) if g.get("titular") else "",
                     '<div class="x">%s</div>' % cuerpo if ext else ""))
        m.pieza(T, x, y, w, giro, dentro, ya=ya)
        if g.get("resalta") and g["resalta"] in ext:
            t0 = max(T + 0.35, t_de(g.get("resalta_dice"), T + 0.5))
            t1 = max(t0 + 0.8, fin_de(g.get("resalta_dice"), t0 + 1.4))
            m.tl.append('tl.fromTo("#%s-hl",{backgroundSize:"0%% 100%%"},{backgroundSize:"100%% 100%%",duration:%.2f,ease:"none"},%.3f);' % (pid, min(t1 - t0, 2.4), m.loc(t0)))
            m.sfx.append((t0, "marcador"))
    elif t in ("persona", "institucion") or (t == "termino" and g.get("definicion")):
        if t == "persona":
            kicker, nombre, rol = g.get("kicker") or "", g.get("persona") or "", g.get("cargo") or ""
            ret = ex.get("ret")
            if ret and not kicker:
                kicker = ""
        elif t == "institucion":
            kicker, nombre, rol, ret = g.get("kicker") or "", g.get("nombre") or "", g.get("rol") or "", None
        else:
            kicker, nombre, rol, ret = g.get("kicker") or "Para entender", g.get("texto") or "", g.get("definicion") or "", None
        cuerpo = ('%s<div class="n cond" style="font-size:%dpx">%s</div>%s%s' % (
            '<div class="k mono">%s</div>' % esc(kicker) if kicker else "", ex.get("px", 78), esc(nombre), '<div class="r">%s</div>' % esc(rol) if rol else "",
            '<div class="f" data-layout-ignore>%s</div>' % esc(g["fuente"]) if g.get("fuente") else ""))
        if ret:
            usados.add(ret["foto"])
            fo = ret.get("foco") or {}
            rr = next((r for r in F.values() if r.get("archivo") == ret["foto"]), {})
            tw, th = (rr.get("tamano") or [800, 800])[:2]
            if fo and "x" in fo:
                s = 210 / max(1.0, fo["w"] * tw * 1.9)
                ix, iy = 105 - (fo["x"] + fo["w"] / 2) * tw * s, 110 - (fo["y"] + fo["h"] / 2) * th * s
            else:
                s = max(210 / tw, 250 / th)
                ix, iy = (210 - tw * s) / 2, (250 - th * s) / 2
            dentro = ('<div class="ficha per"><div class="ret"><img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx" alt=""></div><div>%s</div></div>'
                      % (ret["foto"], ix, iy, tw * s, cuerpo))
        else:
            dentro = '<div class="ficha">%s</div>' % cuerpo
        m.pieza(T, x, y, w, giro, dentro, ya=ya)
    elif t == "lugar":
        if g.get("mapa") == "guatemala":
            D = deptos()
            k_ = VD._plano(g.get("depto") or "")
            sel = next((d for d in D if VD._plano(d[2]) == k_), None) or next((d for d in D if VD._plano(d[2]) == "guatemala"), D[0])
            cx, cy = sel[3]
            dentro = ('<div class="mapa"><svg viewBox="40 40 860 900" width="400" height="418">%s<g id="%s-pin"><circle cx="%.0f" cy="%.0f" r="34" fill="none" stroke="%s" '
                      'stroke-width="9"/><circle cx="%.0f" cy="%.0f" r="13" fill="%s"/></g></svg><div class="cond" style="font-size:40px;padding:12px 4px 2px">%s</div></div>'
                      % ("".join('<path class="%s" d="%s"/>' % ("gt" if d is sel else "tierra", d[0]) for d in D), pid, cx, cy, C["tinta"], cx, cy, C["tinta"],
                         esc(g.get("rotulo") or sel[2])))
            m.pieza(T, x, y, w, giro if abs(giro) <= 3 else 3, dentro, ya=ya)
            m.tl.append('tl.fromTo("#%s-pin",{opacity:0,scale:2.2,transformOrigin:"%.0fpx %.0fpx"},{opacity:1,scale:1,duration:.3,ease:"power3.out"},%.3f);' % (pid, cx, cy, m.loc(T + 0.05)))
        else:
            A = ex["A"]
            pts = A["pts"]
            marcas, anim = "", []
            fs = int(max(30, min(50, 50 * A["w"] / 1150.0)))
            cajas = []
            for j, (nombre, px_, py_) in enumerate(pts):
                der = px_ > A["w"] * 0.55
                ancho_t = len(nombre) * fs * 0.5
                tx = px_ + (-22 if der else 22)
                ops = [py_ + fs * 1.35, py_ - fs * 0.6, py_ + fs * 2.3, py_ - fs * 1.5]
                ty = next((y_ for y_ in ops if fs < y_ < A["h"] - 8 and not any(abs(y_ - cy_) < fs and min(tx, tx - ancho_t if der else tx + ancho_t) < cx1 and
                                                                                 max(tx, tx - ancho_t if der else tx + ancho_t) > cx0 for cx0, cx1, cy_ in cajas)), ops[0])
                cajas.append((min(tx, tx - ancho_t if der else tx + ancho_t), max(tx, tx - ancho_t if der else tx + ancho_t), ty))
                marcas += ('<g id="%s-pt%d"><circle cx="%.1f" cy="%.1f" r="13" fill="%s" stroke="%s" stroke-width="5"/><text x="%.0f" y="%.0f" font-size="%d" text-anchor="%s">%s</text></g>'
                           % (pid, j, px_, py_, C["acento"], C["tinta"], tx, ty, fs, "end" if der else "start", esc(nombre)))
                tj = t_de(nombre, T + 0.25 + 0.5 * j) if j else T
                anim.append((j, max(T + 0.1, tj)))
            ruta = ""
            if g.get("ruta") and len(pts) >= 2:
                d = "M%.1f %.1f" % (pts[0][1], pts[0][2])
                for a, b in zip(pts, pts[1:]):
                    d += " Q%.1f %.1f %.1f %.1f" % ((a[1] + b[1]) / 2, min(a[2], b[2]) - abs(b[1] - a[1]) * 0.22, b[1], b[2])
                ruta = ('<path id="%s-ruta" d="%s" fill="none" stroke="%s" stroke-width="6" stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="110"/>'
                        % (pid, d, C["tinta"]))
            dentro = ('<div class="mapa"><svg viewBox="0 0 %d %d" width="%d" height="%d"><path class="tierra" d="%s"/><path class="gt" d="%s"/>%s%s</svg></div>'
                      % (A["w"], A["h"], A["w"], A["h"], A["tierra"], A["gt"], ruta, marcas))
            m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
            ult = max(t_ for _, t_ in anim)
            if ruta:
                t0 = anim[1][1] - 0.6 if len(anim) > 1 else T + 0.2
                m.tl.append('tl.fromTo("#%s-ruta",{strokeDashoffset:110},{strokeDashoffset:0,duration:%.2f,ease:"power1.inOut"},%.3f);' % (pid, max(0.6, ult - t0), m.loc(max(T, t0))))
                m.sfx.append((max(T, t0), "marcador"))
            for j, tj in anim[1:]:
                m.tl.append('tl.fromTo("#%s-pt%d",{opacity:0,scale:.6,transformOrigin:"%.0fpx %.0fpx"},{opacity:1,scale:1,duration:.3,ease:"back.out(2)"},%.3f);'
                            % (pid, j, pts[j][1], pts[j][2], m.loc(tj)))
    elif t == "fecha":
        if g.get("estilo") == "calendario":
            dentro = '<div class="cal"><div class="top cond">%s</div><div class="mes cond">%s</div><div class="sub mono">%s</div></div>' % (esc(g.get("arriba")), esc(g.get("grande")), esc(g.get("chico")))
        else:
            dentro = '<div class="fecha"><div class="in"><div class="s mono">%s</div><div class="b cond">%s</div></div></div>' % (esc(g.get("chico") or "año"), esc(str(g.get("grande"))))
        m.pieza(T, x, y, w, -5 if k % 2 else 4, dentro, sfx="sello", ya=ya)
    elif t == "cifra":
        v = str(g.get("valor"))
        cu = int(g.get("cuadros") or 0)
        dentro = ('<div class="cifra"><div id="%s-v" class="v cond" style="font-size:%dpx">%s</div><div class="l cond">%s</div>%s%s</div>'
                  % (pid, ex["px"], esc(v), esc(g.get("rotulo")), '<div class="cuad">%s</div>' % "".join('<i id="%s-c%d"></i>' % (pid, i) for i in range(cu)) if cu else "",
                     '<div class="f" data-layout-ignore>%s</div>' % esc(g["fuente"]) if g.get("fuente") else ""))
        mm = re.match(r"^(\D*)(\d[\d,]*)(.*)$", v)
        cuenta = g.get("cuenta") if isinstance(g.get("cuenta"), int) and g.get("cuenta") > 3 and mm else None
        m.pieza(T, x, y, w, giro, dentro, sfx=None if cuenta else "impacto", ya=ya)
        if cuenta:
            t1 = max(T + 0.7, min(g["_fin"], T + 1.5))
            m.tl.append('(function(){const o={v:0},el=document.querySelector("#%s-v");tl.fromTo(o,{v:0},{v:%d,duration:%.2f,ease:"power2.out",onUpdate:function(){'
                        'el.textContent=%s+Math.round(o.v).toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g,",")+%s;}},%.3f);})();'
                        % (pid, cuenta, t1 - T, json.dumps(mm.group(1)), json.dumps(mm.group(3)), m.loc(T)))
            m.sfx.append((t1, "tic"))
        for i in range(cu):
            m.tl.append('tl.fromTo("#%s-c%d",{opacity:0},{opacity:1,duration:.08},%.3f);' % (pid, i, m.loc(T + i * 0.05)))
    elif t == "termino":
        m.pieza(T, x, y, w, giro, '<div class="nota"><div class="cond">%s</div></div>' % esc(g.get("texto")), sfx="papel", ya=ya)
    elif t == "cita":
        # la cita entra atenuada y cada palabra se entinta cuando la voz la lee (la voz dice quién habla y luego la lee)
        pal = (g.get("texto") or "").split()
        cuerpo = "«" + " ".join('<span id="%s-w%d" class="w">%s</span>' % (pid, j, esc(w)) for j, w in enumerate(pal)) + "»"
        dentro = ('<div class="cita"><div class="q">%s</div><div class="a cond">%s</div>%s</div>'
                  % (cuerpo, esc(g.get("autor")), '<div class="c">%s</div>' % esc(g["cargo"]) if g.get("cargo") else ""))
        m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
        t0, t1 = lectura(ctx, g)
        if t0 is None:
            t0, t1 = T + 0.4, T + 0.4 + 0.28 * len(pal)
        T_ = toks_de(S)
        cur = (buscar(S, " ".join(pal[:3]), 0) or (0, 0, 0))[0]
        for j, w in enumerate(pal):
            q = VD._plano(w).split()
            tj = None
            if q:
                for c in range(cur, min(len(T_), cur + 8)):
                    if T_[c][0] == q[0]:
                        tj, cur = o + S["palabras"][T_[c][1]]["start"], c + len(q)
                        break
            if tj is None:
                tj = t0 + (t1 - t0) * j / max(1, len(pal))
            m.tl.append('tl.fromTo("#%s-w%d",{color:"%s"},{color:"%s",duration:.18,ease:"none"},%.3f);' % (pid, j, "#a89a80", "#1f160d", m.loc(max(tj, T + 0.3))))
        m.sfx.append((max(t0, T + 0.3), "marcador"))
    elif t == "documento" and ex.get("texto"):
        D = ex["D"]
        dentro = ('<div class="recorte doc-txt"><div class="cab"><div class="m cond" style="font-size:30px">Documento</div><div class="d" data-layout-ignore>%s</div></div>'
                  '<div class="t cond" style="font-size:50px">%s</div><div class="x" style="font-size:34px">«<span id="%s-hl" class="hl">%s</span>»</div></div>'
                  % (esc(D["tab"][0])[:44], esc(g.get("titulo") or D["tab"][0]), pid, esc(D["frase"])))
        m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
        t0 = max(T + 0.4, t_de(g.get("lee"), T + 0.6))
        m.tl.append('tl.fromTo("#%s-hl",{backgroundSize:"0%% 100%%"},{backgroundSize:"100%% 100%%",duration:1.6,ease:"none"},%.3f);' % (pid, m.loc(t0)))
        m.sfx.append((t0, "marcador"))
    elif t == "documento":
        D, kk = ex["D"], ex["k"]
        e = D["k"] * kk
        marcas = ""
        for j, (lx, ly, lw, lh) in enumerate(D["lineas"]):
            marcas += ('<div id="%s-l%d" class="marca" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx"></div>'
                       % (pid, j, (lx - D["x0"]) * D["pw"] * e - 4, (ly - D["y0"]) * D["ph"] * e - 3, lw * D["pw"] * e + 8, lh * D["ph"] * e + 6))
        if D.get("img"):
            usados.add(D["img"])
        tab = ('<div class="tab" style="%s"><div class="mono" data-layout-ignore>%s</div><div class="cond">%s</div>%s</div>'
               % ("bottom:0;left:0;right:0" if D.get("abajo") else "bottom:0;right:0", esc(D["tab"][0]), esc(D["tab"][1]),
                  '<div class="cond" style="font-size:30px;color:%s;margin-top:4px">%s</div>' % (C["papel2"], esc(D["sub"])) if D.get("sub") else "")
               if D["tab"][0] or D["tab"][1] else "")
        img = ('<img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx" alt="">' % (D["img"], -D["x0"] * D["pw"] * e, -D["y0"] * D["ph"] * e, D["pw"] * e)) if D.get("img") else ""
        dentro = '<div class="doc" style="width:%dpx;height:%dpx">%s%s%s</div>' % (w, h, img, marcas, tab)
        m.pieza(T, x, y, w, max(-1.5, min(1.5, giro)), dentro, ya=ya)
        if D["lineas"]:
            t0 = max(T + 0.4, t_de(g.get("lee"), T + 0.6))
            t1 = max(t0 + 1.0, fin_de(g.get("lee_hasta") or g.get("lee"), t0 + 2.2 * len(D["lineas"])))
            largo = [l[2] for l in D["lineas"]]
            acum = 0.0
            for j, lw in enumerate(largo):
                d = (t1 - t0) * lw / sum(largo)
                m.tl.append('tl.fromTo("#%s-l%d",{scaleX:0,transformOrigin:"0%% 50%%"},{scaleX:1,duration:%.2f,ease:"none"},%.3f);' % (pid, j, d, m.loc(t0 + acum)))
                m.sfx.append((t0 + acum, "marcador"))
                acum += d
    elif t == "lista":
        items = [it for it in g.get("items") or [] if isinstance(it, dict)]
        ult = T
        for j, it in enumerate(items):
            tj = T if j == 0 else max(ult + 0.22, t_de(it.get("dice"), ult + 0.5))
            ult = tj
            cx = x + int((20 if j % 2 == 0 else 20 + ex.get("corr", 200)) * m.f)
            m.pieza(tj, cx, y + int((20 + j * 100) * m.f), ex.get("ficha_w", 260), [-3, 4, 2, -3, 3, -2][j % 6],
                    '<div class="chip%s"><div class="cond">%s</div></div>' % (" ac" if g.get("acento") == j else "", esc(it.get("texto"))), sombra=False,
                    sfx="papel" if j == 0 else None, velo=False, ya=ya and j == 0)
        if isinstance(g.get("lazo"), dict):
            tl_ = max(ult + 0.3, t_de(g["lazo"].get("dice"), ult + 0.6))
            hh = 100 * len(items) + 60
            sid = "%s-lz%d" % (m.id, m.k)
            m.html.append('<svg id="%s" class="pz" style="left:%dpx;top:%dpx;z-index:60" width="%d" height="%d" viewBox="0 0 560 %d" preserveAspectRatio="none" data-layout-ignore>'
                          '<path id="%s-p" d="M70 30 C210 -12 480 6 530 %d C585 %d 525 %d 335 %d C150 %d 22 %d 22 %d C22 %d 36 60 70 30" fill="none" stroke="%s" '
                          'stroke-width="7" stroke-linecap="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="110"/></svg>'
                          % (sid, x - int(30 * m.f), y - int(26 * m.f), int((w + 60) * m.f), int((hh + 20) * m.f), hh + 20, sid, int(hh * .28), int(hh * .6), int(hh * .94), hh, hh + 8, int(hh * .88), int(hh * .52), int(hh * .3), C["acento"]))
            m.tl.append('tl.fromTo("#%s-p",{strokeDashoffset:110},{strokeDashoffset:0,duration:.8,ease:"power1.inOut"},%.3f);' % (sid, m.loc(tl_)))
            m.sfx.append((tl_, "marcador"))
            m.extra.append("#" + sid)


def mesa_html(ctx, M, F, elenco, usados, primera=False, ultima=False):
    """Una mesa del video → (HTML de su composición, efectos [(t, id)])."""
    es, offs, C = ctx["es"], ctx["offs"], ctx["C"]
    m = Mesa(M["id"], M["ini"], M["fin"], barrer=not ultima, css=ctx["css"])
    i0 = M["idx"][0]
    S = es[i0]
    if M["clase"] == "capitulo":
        H = S.get("H") or {}
        tit = " ".join(w["text"] for w in H.get("titulo") or [])
        anios = " – ".join(str(x) for x in (H.get("desde"), H.get("hasta")) if x) if H.get("desde") != H.get("hasta") else str(H.get("desde") or "")
        m.html.append('<div id="%s-rot" class="rot clip" data-start="0" data-duration="%.3f" data-track-index="1"><div id="%s-in"><div class="k mono">Capítulo %s de %s</div>'
                      '<div class="t cond" style="font-size:%dpx">%s</div><div class="a cond">%s</div></div></div>'
                      % (m.id, M["fin"] - M["ini"], m.id, H.get("numero"), H.get("total"), 190 if len(tit) <= 22 else 150 if len(tit) <= 32 else 120, esc(tit), esc(anios)))
        m.tl.append('tl.fromTo("#%s-in",{y:60,opacity:0},{y:0,opacity:1,duration:.5,ease:"power3.out"},0.1);' % m.id)
        m.tl.append('tl.fromTo("#%s-in",{x:0},{x:-2400,duration:.42,ease:"power2.in",immediateRender:false},%.3f);' % (m.id, max(0.7, M["fin"] - M["ini"] - 0.46)))
        m.sfx += [(M["ini"] + 0.25, "impacto"), (M["fin"] - 0.34, "whoosh")]
        m.barrer = False
        return m.cerrar(), m.sfx
    if M["clase"] == "cierre":
        ci, T = ctx["E"].get("cierre") or {}, S.get("T") or {}
        rs = (ci.get("resumen") or [])[:3]
        ts = (T.get("r") or [0.1, 1.6, 3.5]) + [T.get("preg", 5.5), T.get("sigue", 9.7)]
        yt = next((r["handle"] for r in ctx["E"].get("redes") or [] if r.get("red") == "youtube"), "")
        cuerpo = '<div class="k mono">%s</div>' % esc(ci.get("rotulo") or "Lo que dejó")
        for j, r in enumerate(rs):
            cuerpo += '<div id="%s-r%d" class="li cond">%s</div>' % (m.id, j, esc(r))
        cuerpo += '<div id="%s-fin" class="fin">%s</div>' % (m.id, esc(ci.get("final") or ""))
        cuerpo += '<div id="%s-sus"><div class="sus"><div class="cond">Suscríbete</div></div><div class="han mono">%s</div></div>' % (m.id, esc(yt))
        m.html.append('<div id="%s-cie" class="cie clip" data-start="0" data-duration="%.3f" data-track-index="1">%s</div>' % (m.id, M["fin"] - M["ini"], cuerpo))
        for j in range(len(rs)):
            m.tl.append('tl.fromTo("#%s-r%d",{x:-60,opacity:0},{x:0,opacity:1,duration:.45,ease:"power3.out"},%.3f);' % (m.id, j, max(0.0, ts[j] - 0.1)))
            m.sfx.append((M["ini"] + ts[j], "papel"))
        m.tl.append('tl.fromTo("#%s-fin",{y:30,opacity:0},{y:0,opacity:1,duration:.5,ease:"power3.out"},%.3f);' % (m.id, ts[-2]))
        m.tl.append('tl.fromTo("#%s-sus",{y:30,opacity:0},{y:0,opacity:1,duration:.5,ease:"power3.out"},%.3f);' % (m.id, ts[-1]))
        m.barrer = False
        return m.cerrar(), m.sfx
    tablero = M["clase"] == "tablero"
    if tablero:
        d = M["fin"] - M["ini"]
        clip = "clips/e%d.mp4" % S["n"]
        usados.add(clip)
        m.html.append('<div id="%s-marco" class="pz pizarra" style="left:110px;top:54px;width:1008px;height:972px;z-index:5" data-layout-allow-overlap>'
                      '<video id="%s-anim" class="clip" data-start="0" data-duration="%.3f" data-track-index="0" muted playsinline src="assets/%s" '
                      'style="position:absolute;left:0;top:0;width:1008px;height:972px;object-fit:cover"></video></div>' % (m.id, m.id, d, clip))
        # el rótulo de acto de la escena (año, título, lugar) abre la mesa como ficha; el tablero entra cuando el rótulo acabaría
        R = S.get("R") if isinstance(S.get("R"), dict) else None
        t_marco = max(0.0, float(R.get("fin") or 2.3) - 0.4) if R else 0.0
        m.tl.append('tl.fromTo("#%s-marco",{x:-80,opacity:0},{x:0,opacity:1,duration:.4,ease:"power3.out"},%.3f);' % (m.id, t_marco))
        m.extra.append("#%s-marco" % m.id)
        m.sfx.append((M["ini"] + t_marco + 0.2, "whoosh"))
        if R:
            tit = " ".join(w["text"] for w in R.get("titulo") or [] if isinstance(w, dict))
            cuando = " – ".join(str(x) for x in dict.fromkeys(x for x in (R.get("desde"), R.get("hasta")) if x))
            if tit:
                M["golpes"] = [{"tipo": "institucion", "nombre": tit, "kicker": R.get("lugar") or "", "rol": cuando, "_t": round(M["ini"] + 0.35, 3),
                                "_fin": round(M["ini"] + 1.2, 3), "_i": i0}] + [g for g in M["golpes"] if not g.get("_acto")]
                M["golpes"][0]["_acto"] = True
    gs = M["golpes"]
    med = [medida(ctx, g, F, 660 if tablero else 1150, elenco) for g in gs]
    # la mesa a escala: se achica hasta que ninguna pieza tape más del 15 % de una de las tres anteriores, pero no bajo 0.8
    # (más chica, la mesa se ve vacía mientras se llena y la letra de los documentos no se lee: mejor que la vieja quede debajo)
    pos = []
    for f_ in ((1.0,) if any(g.get("x") is not None for g in gs) else (1.0, 0.93, 0.86, 0.8)):
        m.f = f_
        dims = [(int(w * f_), int(h * f_)) for w, h, _ in med]
        pos = colocar([(w, h, g) for (w, h), g in zip(dims, gs)], tablero)
        peor = 0.0
        for k in range(len(pos)):
            for j in range(max(0, k - 3), k):
                ox = max(0, min(pos[k][0] + dims[k][0], pos[j][0] + dims[j][0]) - max(pos[k][0], pos[j][0]))
                oy = max(0, min(pos[k][1] + dims[k][1], pos[j][1] + dims[j][1]) - max(pos[k][1], pos[j][1]))
                peor = max(peor, ox * oy / float(max(1, dims[j][0] * dims[j][1])))
        if peor <= 0.15:
            break
    for k, (g, (w, h, ex), (x, y)) in enumerate(zip(gs, med, pos)):
        if primera and k == 0 and g["_t"] - LEAD <= M["ini"] + 0.05:
            g["_ya"] = True
        dibujar(ctx, m, g, x, y, w, h, ex, k, F, usados)
    return m.cerrar(), m.sfx


def colores(E):
    c = E.get("colores") or {}
    return {"mesa": c.get("bg") or "#1E130E", "mesa2": c.get("fondo_acto2") or "#0F0A07", "papel": c.get("ink") or "#F6F2E8", "papel2": "#E9E1CF",
            "tinta": c.get("tinta_acento") or "#1A1208", "acento": c.get("a1") or "#D9A66B", "gris": c.get("a2") or "#958E86", "cafe": c.get("a3") or "#856441"}


def enlazar(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def cmd_proyecto(a):
    import youtube as YT
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto(trabajo)
    fp = os.path.join(trabajo, "plano.json")
    if not os.path.exists(fp):
        return falla("falta plano.json: youtube.py plano %s (o --borrador en la maqueta)" % rel(trabajo))
    mesas, f0 = resolver(ctx, leer(fp))
    ctx["C"] = colores(ctx["E"])
    css = CSS
    for k, v in sorted(ctx["C"].items(), key=lambda kv: -len(kv[0])):   # «$papel2» antes que «$papel»
        css = css.replace("$" + k, v)
    ctx["css"] = css
    F = fichas(trabajo)
    elenco = YT.elenco_serie(ctx["Y"])
    efectos = []
    mezcla = os.path.join(trabajo, "segs_16x9", "mezcla_final.wav")
    for c in ctx["caps"]:
        if a.capitulo and c["numero"] != a.capitulo:
            continue
        P = os.path.join(trabajo, "hf", "cap-%d" % c["numero"])
        shutil.rmtree(os.path.join(P, "compositions"), ignore_errors=True)
        shutil.rmtree(os.path.join(P, "assets"), ignore_errors=True)
        os.makedirs(os.path.join(P, "compositions"))
        usados, hosts = set(), []
        ms = [M for M in mesas if M["cap"] == c["numero"]]
        for k, M in enumerate(ms):
            html, sfx = mesa_html(ctx, M, F, elenco, usados, primera=(M is mesas[0]), ultima=(M is mesas[-1]))
            efectos += sfx
            open(os.path.join(P, "compositions", M["id"] + ".html"), "w", encoding="utf-8").write(html)
            hosts.append('      <div id="%s" data-composition-id="%s" data-composition-src="compositions/%s.html" data-start="%.4f" data-duration="%.4f" '
                         'data-track-index="%d" data-track-kind="graphics" data-width="1920" data-height="1080"></div>'
                         % (M["id"], M["id"], M["id"], M["ini"] - c["ini"], M["fin"] - M["ini"], 1 + k % 2))
        for u in sorted(usados):
            src = os.path.join(trabajo, "clips_tablero", os.path.basename(u)) if u.startswith("clips/") else os.path.join(trabajo, u)
            if os.path.exists(src):
                enlazar(src, os.path.join(P, "assets", u))
            else:
                print("AVISO falta %s (youtube.py grabar)" % rel(src))
        for fnt in ("archivo-wdth.woff2", "jetbrains-mono-var.woff2"):
            enlazar(os.path.join(RAIZ, "design", "fonts", fnt), os.path.join(P, "assets", "fonts", fnt))
        enlazar(os.path.join(RAIZ, "design", "grano-mesa.png"), os.path.join(P, "assets", "grano.png"))
        dur = c["fin"] - c["ini"]
        # lo que va encima de la mesa sin ser pieza: el «Suscríbete» de la mitad del video (V25) y la pregunta en su pago (P6)
        sobre, sobre_tl = "", ""
        for i in c["idx"]:
            S = ctx["es"][i]
            if isinstance(S.get("seguir"), dict) and S["tipo"] not in PROPIAS:
                t = round(max(0.5, min(ctx["offs"][i] + S["seguir"].get("desde", 1.0) - c["ini"], c["fin"] - c["ini"] - 3.8)), 3)   # entero dentro del capítulo
                sobre += ('      <div id="seguir" class="clip" data-start="%.3f" data-duration="3.600" data-track-index="8" data-layout-allow-overlap data-layout-allow-occlusion>'
                          '<div id="seguir-in"><span id="seguir-t">Suscríbete</span><svg id="seguir-c" viewBox="0 0 24 24" width="40" height="40"><path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7 2.5 7h-17S6 15 6 9Z'
                          'M10 20a2 2 0 0 0 4 0" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div>\n' % t)
                sobre_tl += ('      tl.fromTo("#seguir-in",{y:-50,opacity:0},{y:0,opacity:1,duration:.35,ease:"power3.out"},%.3f);\n'
                             '      tl.fromTo("#seguir-in",{scale:1},{scale:.92,duration:.09,yoyo:true,repeat:1,ease:"power1.inOut",immediateRender:false},%.3f);\n'
                             '      tl.fromTo("#seguir-c",{rotation:0,transformOrigin:"50%% 10%%"},{rotation:16,duration:.09,yoyo:true,repeat:5,ease:"sine.inOut"},%.3f);\n'
                             '      tl.fromTo("#seguir-in",{y:0,opacity:1},{y:-50,opacity:0,duration:.3,ease:"power2.in",immediateRender:false},%.3f);\n' % (t, t + 1.2, t + 1.5, t + 3.2))
                efectos.append((round(ctx["offs"][i] + S["seguir"].get("desde", 1.0) + 1.2, 3), "tic"))
            q = S.get("pregunta")
            if isinstance(q, dict) and (q.get("texto") or "").strip() and S["tipo"] not in PROPIAS:
                t = round(ctx["offs"][i] + q.get("desde", 0.9) - c["ini"], 3)
                d = max(2.5, float(q.get("dur") or 4.0))
                sobre += ('      <div id="pregunta" class="clip" data-start="%.3f" data-duration="%.3f" data-track-index="8" data-layout-allow-overlap data-layout-allow-occlusion>'
                          '<div id="pregunta-in"><i>La pregunta</i><b>%s</b><svg viewBox="0 0 24 24" width="46" height="46"><path id="pregunta-ok" d="M4 12.5l5 5L20 6.5" fill="none" stroke="%s" '
                          'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="110"/></svg></div></div>\n'
                          % (t, d, esc(q["texto"].strip()), ctx["C"]["acento"]))
                sobre_tl += ('      tl.fromTo("#pregunta-in",{y:-50,opacity:0},{y:0,opacity:1,duration:.4,ease:"power3.out"},%.3f);\n'
                             '      tl.fromTo("#pregunta-ok",{strokeDashoffset:110},{strokeDashoffset:0,duration:.45,ease:"power1.inOut"},%.3f);\n'
                             '      tl.fromTo("#pregunta-in",{y:0,opacity:1},{y:-50,opacity:0,duration:.3,ease:"power2.in",immediateRender:false},%.3f);\n' % (t, t + 0.9, t + d - 0.35))
        audio = ""
        if os.path.exists(mezcla):   # la guía de la vista previa: el tramo del capítulo de la mezcla ya hecha (youtube.py audio)
            VD.ff("-ss", "%.4f" % c["ini"], "-t", "%.4f" % dur, "-i", mezcla, "-ar", "48000", os.path.join(P, "assets", "audio.wav"))
            audio = '      <audio id="guia" class="clip" data-start="0" data-duration="%.4f" data-track-index="9" data-volume="1" src="assets/audio.wav"></audio>\n' % dur
        C = ctx["C"]
        open(os.path.join(P, "index.html"), "w", encoding="utf-8").write("""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: %s; }
      #root { position: relative; width: 1920px; height: 1080px; }
      #mesa { position: absolute; inset: 0; background: radial-gradient(1500px 900px at 46%% 40%%, #2a1b13 0%%, %s 55%%, #120b08 100%%); }
      #grano { position: absolute; inset: 0; background: url('assets/grano.png'); background-size: 480px 270px; opacity: .16; mix-blend-mode: overlay; }
      @font-face { font-family: 'Archivo'; font-weight: 100 900; font-stretch: 62%% 125%%; src: url('assets/fonts/archivo-wdth.woff2') format('woff2'); }
      @font-face { font-family: 'JetBrains Mono'; font-weight: 100 800; src: url('assets/fonts/jetbrains-mono-var.woff2') format('woff2'); }
      #seguir, #pregunta { position: absolute; z-index: 900; }
      #seguir { right: 96px; top: 64px; }
      #seguir-in { display: flex; align-items: center; gap: 14px; background: %s; color: %s; padding: 14px 26px 12px 30px; font: 800 46px/1 'Archivo', sans-serif; font-stretch: 62%%;
        text-transform: uppercase; box-shadow: 0 18px 40px rgba(0,0,0,.55); }
      #pregunta { left: 96px; top: 56px; max-width: 1180px; }
      #pregunta-in { display: grid; grid-template-columns: 1fr auto; column-gap: 22px; align-items: center; background: %s; border-left: 10px solid %s; padding: 16px 26px 16px 24px;
        box-shadow: 0 18px 40px rgba(0,0,0,.55); color: %s; }
      #pregunta-in i { grid-column: 1 / 3; font: 600 22px/1 'JetBrains Mono', monospace; letter-spacing: .1em; text-transform: uppercase; color: %s; font-style: normal; margin-bottom: 8px; }
      #pregunta-in b { font: 700 40px/1.12 'Archivo', sans-serif; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="%.4f" data-width="1920" data-height="1080">
      <div id="mesa" data-layout-ignore></div>
      <div id="grano" data-layout-ignore></div>
%s
%s%s    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
%s      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""" % (C["mesa2"], C["mesa"], C["acento"], C["tinta"], C["mesa2"], C["acento"], C["papel"], C["acento"], dur, "\n".join(hosts), sobre, audio, sobre_tl))
        escribir(os.path.join(P, "hyperframes.json"), {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                                                        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                                                        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                                                        "media": {"autoProxy": True}, "authoringSkill": "hyperframes"})
        escribir(os.path.join(P, "meta.json"), {"id": "%s-cap-%d" % (ctx["Y"].get("slug") or "youtube", c["numero"]), "name": "Capítulo %d" % c["numero"]})
        escribir(os.path.join(P, "mesas.json"), [{"id": M["id"], "ini": round(M["ini"] - c["ini"], 3), "fin": round(M["fin"] - c["ini"], 3), "clase": M["clase"],
                                                  "piezas": len(M["golpes"])} for M in ms])
        print("proyecto: capítulo %d · %d mesas · %d piezas · %s → %s" % (c["numero"], len(ms), sum(len(M["golpes"]) for M in ms), VD_mmss(dur), rel(P)))
    if not a.capitulo:
        escribir(os.path.join(trabajo, "hf", "efectos.json"), sorted([t, i] for t, i in efectos if 0 <= t < ctx["total"] - 0.2))
    for x in f0:
        print("AVISO", x)
    return 0


def VD_mmss(t):
    return "%d:%02d" % (int(t) // 60, int(t) % 60)


def hf(P, *args, timeout=3600):
    return subprocess.run(["npx", "--yes", "hyperframes@" + HF_VERSION] + list(args), cwd=P, capture_output=True, text=True, timeout=timeout)


def cmd_revisar(a):
    """hyperframes check por capítulo y una hoja de contacto: cada mesa justo antes de barrerse (cuando tiene todas sus piezas)."""
    trabajo = os.path.abspath(a.trabajo)
    malas = 0
    for P in sorted(glob.glob(os.path.join(trabajo, "hf", "cap-*"))):
        n = int(P.rsplit("-", 1)[1])
        if a.capitulo and n != a.capitulo:
            continue
        r = hf(P, "check", "--json")
        try:
            d = json.loads(r.stdout[r.stdout.index("{"):])
        except ValueError:
            print("FALLA capítulo %d: hyperframes check no respondió: %s" % (n, (r.stderr or r.stdout)[-300:]))
            malas += 1
            continue
        err = [x for k in ("lint", "runtime", "layout", "motion", "contrast", "craft", "audio") for x in (d.get(k) or {}).get("findings") or [] if x.get("severity") == "error"]
        adv = [x for k in ("lint", "runtime", "layout", "motion", "contrast", "craft") for x in (d.get(k) or {}).get("findings") or [] if x.get("severity") == "warning"]
        for x in err:
            print("FALLA capítulo %d: %s %s" % (n, x.get("code"), (x.get("message") or "")[:160]))
        cuenta = {}
        for x in adv:
            cuenta[x.get("code")] = cuenta.get(x.get("code"), 0) + 1
        ms = leer(os.path.join(P, "mesas.json"))
        ts = ",".join("%.2f" % max(m["ini"] + 0.2, m["fin"] - 0.6) for m in ms)
        s = hf(P, "snapshot", "--at", ts)
        hojas = re.findall(r"(\S+contact-sheet[^\s]*\.jpg)", s.stdout)
        os.makedirs(os.path.join(trabajo, "revision"), exist_ok=True)
        for j, h in enumerate(hojas):
            shutil.copy(h, os.path.join(trabajo, "revision", "hf_cap-%d%s.jpg" % (n, "" if len(hojas) == 1 else "_%d" % (j + 1))))
        print("capítulo %d: check %s · avisos %s · %d hoja(s) en revision/hf_cap-%d*.jpg" % (n, "ok" if d.get("ok") and not err else "CON ERRORES", cuenta or "ninguno", len(hojas), n))
        malas += bool(err) or not d.get("ok")
    return 1 if malas else 0


def cmd_render(a):
    """Render por capítulo, cada uno con UN proceso (--workers 1: con varios el video tiembla); une los capítulos sin
    recodificar → segs_16x9/video_solo.mp4. HyperFrames renderiza de uno en uno (candado global ~/.cache/hyperframes/locks):
    lanzar varios a la vez solo los pone en fila (medido: 2:15 de video en 3 min 40 s)."""
    trabajo = os.path.abspath(a.trabajo)
    Ps = sorted(glob.glob(os.path.join(trabajo, "hf", "cap-*")), key=lambda p: int(p.rsplit("-", 1)[1]))
    if a.capitulo:
        Ps = [p for p in Ps if int(p.rsplit("-", 1)[1]) == a.capitulo]
    if not Ps:
        return falla("no hay proyectos en hf/: youtube.py proyecto")
    procs, cola, malas = [], list(Ps), 0
    while cola or procs:
        while cola and len(procs) < a.paralelo:
            P = cola.pop(0)
            os.makedirs(os.path.join(P, "render"), exist_ok=True)
            log = open(os.path.join(P, "render", "render.log"), "w")
            procs.append((P, subprocess.Popen(["npx", "--yes", "hyperframes@" + HF_VERSION, "render", "--quality", a.calidad, "--workers", "1", "-o", "render/capitulo.mp4"],
                                              cwd=P, stdout=log, stderr=subprocess.STDOUT), log))
        for item in list(procs):
            P, pr, log = item
            if pr.poll() is not None:
                log.close()
                procs.remove(item)
                ok = pr.returncode == 0 and os.path.exists(os.path.join(P, "render", "capitulo.mp4"))
                print("render %s: %s" % (os.path.basename(P), "ok" if ok else "FALLÓ (render/render.log)"))
                malas += not ok
        if procs:
            try:
                procs[0][1].wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    if malas:
        return 1
    if a.capitulo:
        return 0
    ctx = contexto(trabajo)
    segs = os.path.join(trabajo, "segs_16x9")
    os.makedirs(segs, exist_ok=True)
    lista = os.path.join(segs, "capitulos.txt")
    open(lista, "w").write("".join("file '%s'\n" % os.path.join(P, "render", "capitulo.mp4") for P in Ps))
    out = os.path.join(segs, "video_solo.mp4")
    VD.ff("-f", "concat", "-safe", "0", "-i", lista, "-map", "0:v", "-c:v", "copy", "-an", "-movflags", "+faststart", out)
    d = VD.ffprobe_dur(out)
    print("video: %s (%s; el plano dice %s) → %s" % (VD_mmss(d), "%.2f s" % d, "%.2f s" % ctx["total"], rel(out)))
    if abs(d - ctx["total"]) > 2.0 / FPS * len(Ps) + 0.05:
        return falla("la duración del video (%.2f s) no es la del plano (%.2f s)" % (d, ctx["total"]))
    return 0


# ---------- plano: unir, gates, hoja, digesto ----------
def cmd_borrador(a):
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto(trabajo)
    B = borrador(ctx)
    escribir(os.path.join(trabajo, "plano.borrador.json"), B)
    print("borrador: %d mesas · %d golpes → %s" % (len(B["mesas"]), sum(len(m["golpes"]) for m in B["mesas"]), rel(os.path.join(trabajo, "plano.borrador.json"))))
    return 0


def cmd_plano(a):
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto(trabajo)
    fp = os.path.join(trabajo, "plano.json")
    partes = sorted(glob.glob(os.path.join(trabajo, "plano_*.json")), key=lambda p: int(re.findall(r"plano_(\d+)\.json", p)[0]))
    if a.borrador:
        shutil.copy(os.path.join(trabajo, "plano.borrador.json"), fp)
    elif partes:
        mesas = []
        for p in partes:
            try:
                d = leer(p)
            except ValueError as ex:
                return falla("%s no es JSON: %s" % (rel(p), ex))
            mesas += [m for m in d.get("mesas") or [] if isinstance(m, dict)]
        mesas.sort(key=lambda m: min([ctx["por_clave"].get(c, 10 ** 6) for c in m.get("escenas") or []] or [10 ** 6]))
        escribir(fp, {"version": 1, "mesas": mesas})
    if not os.path.exists(fp):
        return falla("no hay plano_<N>.json ni plano.json en %s" % rel(trabajo))
    P = leer(fp)
    mesas, f0 = resolver(ctx, P)
    f, av, med = revisar(ctx, P, mesas, f0)
    if a.capitulo:
        claves = {ctx["es"][i]["clave"] for c in ctx["caps"] if c["numero"] == a.capitulo for i in c["idx"]}
        ids = {M["id"] for M in mesas if M["cap"] == a.capitulo}
        f = [x for x in f if any((" %s " % k) in x or (" %s:" % k) in x or ("(%s" % k) in x for k in claves) or any(x.split(" ")[1] == i for i in ids)
             or ("capítulo %d:" % a.capitulo) in x]
        av = [x for x in av if ("capítulo %d:" % a.capitulo) in x]
    if a.hoja:
        hoja = hoja_de(ctx, mesas)
        open(os.path.join(trabajo, "plano.md"), "w", encoding="utf-8").write(hoja)
        print("hoja de golpes → %s" % rel(os.path.join(trabajo, "plano.md")))
    n = sum(len(M["golpes"]) for M in mesas)
    print("plano: %d mesas · %d piezas en %s (una cada %.1f s) · %d de %d oraciones con pieza nueva" % (
        len(mesas), n, VD_mmss(ctx["total"]), ctx["total"] / max(1, n), med["con_pieza_nueva"], med["oraciones"]))
    for cap, m in sorted(med["capitulos"].items()):
        print("  capítulo %d: %d piezas · %d de archivo real (%.0f %%) · %s" % (cap, m["piezas"], m["archivo_real"], 100 * m["archivo_real"] / max(1, m["piezas"]), ", ".join(m["tipos"])))
    for x in av:
        print("AVISO", x)
    fix = bool(ctx["Y"].get("fixture"))
    for x in f:
        print("AVISO (maqueta)" if fix else "FALLA", x)
    ok = not f or fix
    print("RETORNO " + json.dumps({"archivo": rel(fp), "gate": "ok" if ok else "falla", "fallas": f[:40], "piezas": n,
                                   "archivo_real": sum(m["archivo_real"] for m in med["capitulos"].values())}, ensure_ascii=False))
    return 0 if ok or not a.check else 1


def hoja_de(ctx, mesas):
    es, offs = ctx["es"], ctx["offs"]
    L = ["# Hoja de golpes\n", "Cada fila es una oración de la voz y lo que entra en pantalla con ella.\n"]
    cap = None
    for M in mesas:
        if M["cap"] != cap:
            cap = M["cap"]
            c = next(c for c in ctx["caps"] if c["numero"] == cap)
            L.append("\n## Capítulo %d%s\n\n| Tiempo | La voz dice | Entra en pantalla |\n|---|---|---|" % (cap, " · " + c["titulo"] if c["titulo"] else ""))
        if M["clase"] in PROPIAS:
            L.append("| %s | (sin voz) | %s |" % (VD_mmss(M["ini"]), "Rótulo del capítulo" if M["clase"] == "capitulo" else "Cierre y «Suscríbete»"))
            continue
        ev = eventos_de(ctx, M)
        for i in M["idx"]:
            for sg in segmentos(es[i]):
                if not (sg.get("texto") or "").strip():
                    continue
                a, b = offs[i] + sg["t"], offs[i] + sg["hasta"]
                gs = [g for g in M["golpes"] if a - 0.6 <= g["_t"] < b]
                txt = "; ".join("**%s**: %s" % (g["tipo"], resumen_golpe(g)) for g in gs)
                if not txt:
                    dentro = [e for e in ev if a - 0.6 <= e[0] < b]
                    if any(e[1] == "tablero" for e in dentro):
                        txt = "un paso de la animación ya hecha (%s)" % es[i]["tipo"]
                    elif dentro:
                        txt = "sigue el subrayado o la lista de la pieza anterior"
                L.append("| %s | %s | %s |" % (VD_mmss(a), sg["texto"].replace("|", "/"), txt or "—"))
    return "\n".join(L) + "\n"


def resumen_golpe(g):
    t = g["tipo"]
    if t == "foto":
        return "%s («%s»)" % (g.get("foto"), g.get("pie"))
    if t == "recorte":
        return "%s, %s: %s" % (g.get("medio"), g.get("fecha"), (g.get("titular") or g.get("extracto") or "")[:70])
    if t == "documento":
        return g.get("titulo") or g.get("pagina") or ""
    if t == "persona":
        return "%s (%s)" % (g.get("persona"), g.get("cargo") or "")
    if t == "institucion":
        return g.get("nombre") or ""
    if t == "lugar":
        return g.get("rotulo") or g.get("depto") or " → ".join(p.get("nombre", "") for p in g.get("puntos") or [])
    if t == "fecha":
        return " ".join(str(x) for x in (g.get("chico"), g.get("grande")) if x)
    if t == "cifra":
        return "%s %s" % (g.get("valor"), g.get("rotulo"))
    if t == "lista":
        return ", ".join(it.get("texto", "") for it in g.get("items") or [])
    return (g.get("texto") or "")[:70]


def cmd_digesto(a):
    """Lo que el realizador de un capítulo necesita: las oraciones con su segundo, lo que el código ya detecta, las fuentes de
    cada hecho, las fotos y los documentos que hay, y el borrador de partida."""
    import youtube as YT
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto(trabajo)
    es, offs = ctx["es"], ctx["offs"]
    c = next((c for c in ctx["caps"] if c["numero"] == a.capitulo), None)
    if not c:
        return falla("no hay capítulo %s (hay %s)" % (a.capitulo, [x["numero"] for x in ctx["caps"]]))
    F = fichas(trabajo)
    elenco = YT.elenco_serie(ctx["Y"])
    H = YT.hechos_serie(ctx["Y"])
    idx = leer(os.path.join(trabajo, "indice.json")) if os.path.exists(os.path.join(trabajo, "indice.json")) else {"escenas": []}
    hechos_de = {e.get("id"): e.get("hechos") or [] for e in idx.get("escenas") or []}
    B = borrador(ctx)
    bor = {cl: [g for g in m["golpes"] if (g.get("escena") or m["escenas"][0]) == cl] for m in B["mesas"] for cl in m["escenas"]}
    usados = {}
    fp = os.path.join(trabajo, "plano.json")
    if os.path.exists(fp):
        for m in leer(fp).get("mesas") or []:
            for g in m.get("golpes") or []:
                if g.get("tipo") == "foto":
                    usados[g.get("foto")] = usados.get(g.get("foto"), 0) + 1
    print("# Capítulo %d%s · %s a %s · escribe sesiones/…/plano_%d.json" % (c["numero"], " · " + c["titulo"] if c["titulo"] else "", VD_mmss(c["ini"]), VD_mmss(c["fin"]), c["numero"]))
    print("\n## Escenas (clave · tipo · segundo del video). Cada «·» es una oración: ahí tiene que entrar algo.")
    notas, vistos = notas_leidas(), set()
    for i in c["idx"]:
        S = es[i]
        if S["tipo"] in PROPIAS:
            print("\n%s  E%d %s (lo arma el script; no va en el plano)" % (VD_mmss(offs[i]), S["n"], S["tipo"]))
            continue
        print("\n%s  %s · %s%s · %.1f s" % (VD_mmss(offs[i]), S["clave"], S["tipo"], " (TABLERO: va sola en su mesa; su animación ya trae sus pasos)" if S["tipo"] in TABLERO else "", S["dur"]))
        for sg in segmentos(S):
            if (sg.get("texto") or "").strip():
                print("   · %5.1f s  %s" % (offs[i] + sg["t"], sg["texto"]))
        N = S.get("N") or {}
        if S["tipo"] in TABLERO:
            Pp, Tt = S.get("P") or {}, S.get("T") or {}
            ya = [" ".join(w["text"] for w in S.get("arriba") or []), Pp.get("titulo")] + [x.get("texto") for x in Tt.get("pasos") or []] + \
                 [k for k in (Tt.get("valores") or {}) if len(k) <= 8] + [(S.get("R") or {}).get("hasta"), (S.get("R") or {}).get("lugar")]
            print("   el tablero ya muestra: %s" % " · ".join(dict.fromkeys(str(x) for x in ya if x)))
            pasos = sorted(offs[i] + x["t"] for x in S.get("eventos") or [] if x.get("tipo") in EVENTOS_TABLERO)
            for sg in segmentos(S):
                if (sg.get("texto") or "").strip() and not any(offs[i] + sg["t"] - 0.6 <= t_ < offs[i] + sg["hasta"] for t_ in pasos):
                    print("   sin paso propio (necesita un golpe tuyo): «%s»" % sg["texto"][:80])
        if N.get("foto"):
            print("   foto de la escena: %s" % YT.foto_id(N["foto"]))
        for g in bor.get(S["clave"]) or []:
            print("   borrador: %s" % json.dumps({k: v for k, v in g.items() if k != "escena"}, ensure_ascii=False)[:230])
        for hid in hechos_de.get(S["clave"]) or []:
            h = H.get(hid) or {}
            print("   hecho %s (%s, %s%s): %s" % (hid, h.get("fecha"), h.get("lugar") or "sin lugar", ", " + h.get("estado") if h.get("estado") else "", (h.get("texto") or "")[:170]))
            for fu in (h.get("fuentes") or [])[:3]:
                n = notas.get(fu.get("url")) or {}
                pdf = bool(pdf_de(fu.get("url")))
                print("      fuente: %s · %s · «%s»%s%s\n        url: %s\n        cita: «%s»" % (
                    fu.get("medio"), fu.get("fecha") or n.get("fecha"), (n.get("titulo") or "")[:90], " · PDF" if pdf else "", " · con og:image" if n.get("og_image") else "",
                    fu.get("url"), (fu.get("cita") or "")[:260]))
                vistos.add(fu.get("url"))
    print("\n## Personas (ficha `persona`; el retrato entra solo si lo hay)")
    for p in elenco:
        print("  %s · %s · %s · la voz la nombra como: %s" % (p["nombre"], p["cargo"], "con retrato" if p.get("foto") else "SIN retrato", " / ".join(p["claves"][:4])))
    import historia as HI
    try:
        pj = leer(os.path.join(RAIZ, ctx["Y"]["base"], "historia.json")).get("personajes") or []
    except (OSError, ValueError, KeyError):
        pj = []
    inst = [p for p in pj if isinstance(p, dict) and not HI.es_persona(p)]
    if inst:
        print("\n## Instituciones (ficha `institucion`)")
        for p in inst:
            print("  %s · %s" % (p.get("nombre"), p.get("cargo") or p.get("presentacion") or ""))
    print("\n## Fotos que ya hay (id · tamaño · usos en el plano · crédito · qué se ve). Una foto ≤ %d veces y a ≥ %d s." % (FOTO_USOS_MAX, FOTO_SEPARACION_S))
    for fid, r in sorted(F.items()):
        if fid.startswith("_") or not r.get("archivo"):
            continue
        print("  %s · %s · %d usos · %s · %s%s" % (fid, "×".join(str(x) for x in r.get("tamano") or []), usados.get(fid, 0), r.get("credito"), (r.get("descripcion") or "")[:110],
                                                 " · PERSONAS EN PROCESO: solo donde la voz las nombra" if JUDICIAL.search(r.get("descripcion") or "") else ""))
    pg = os.path.join(trabajo, "paginas.json")
    if os.path.exists(pg):
        print("\n## Páginas de documento ya sacadas (documento con `pagina`)")
        for k, v in leer(pg).items():
            print("  %s · pág. %s · «%s» · %s · %s" % (k, v.get("pagina"), (v.get("frase") or "")[:90], v.get("fuente"), v.get("url") or ""))
    print("\n## Lugares con coordenadas (mapa «mundo»): %s" % ", ".join(sorted(LUGARES)))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    for nombre, fn in (("borrador", cmd_borrador), ("proyecto", cmd_proyecto), ("revisar", cmd_revisar)):
        q = sub.add_parser(nombre)
        q.add_argument("trabajo")
        q.add_argument("--capitulo", type=int)
        q.set_defaults(fn=fn)
    q = sub.add_parser("plano")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true")
    q.add_argument("--hoja", action="store_true")
    q.add_argument("--borrador", action="store_true", help="usa plano.borrador.json tal cual (la maqueta)")
    q.add_argument("--capitulo", type=int)
    q.set_defaults(fn=cmd_plano)
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.add_argument("--capitulo", type=int, required=True)
    q.set_defaults(fn=cmd_digesto)
    q = sub.add_parser("render")
    q.add_argument("trabajo")
    q.add_argument("--capitulo", type=int)
    q.add_argument("--calidad", default="looks", choices=("draft", "looks", "delivery"))
    q.add_argument("--paralelo", type=int, default=1, help=argparse.SUPPRESS)
    q.set_defaults(fn=cmd_render)
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
