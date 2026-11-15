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
    una mesa puede llevar `maqueta`: un render 3D de la situación (cuando el lugar es la información); entra como un tablero
    (clips_maqueta_16x9/<mesa>.mp4, scripts/maqueta3d.py en modo pieza) con sus golpes a la derecha; gates YT20–YT24 en mesa.py

Uso (lo llama scripts/youtube.py; también directo):
  youtube_hf.py borrador TRABAJO            plano.borrador.json desde lo que ya traen las escenas
  youtube_hf.py digesto TRABAJO --capitulo N   lo que el realizador necesita para escribir plano_<N>.json
  youtube_hf.py plano TRABAJO [--check] [--hoja] [--capitulo N]   une plano_<N>.json → plano.json; gates; hoja de golpes
  youtube_hf.py maquetas TRABAJO [--fps 30] [--todo]   las mesas con maqueta 3D → clips_maqueta_16x9/<mesa>.mp4 (lo llama `youtube.py grabar`)
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
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD   # noqa: E402
import mesa as MS   # noqa: E402
from mesa import *   # noqa: E402,F401,F403  (el núcleo común: plano, gates, Mesa, mapas, documentos)

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
.maqueta{overflow:hidden}
.mq-pie{position:absolute;left:26px;right:26px;bottom:10px;font-family:'JetBrains Mono',monospace;font-size:18px;line-height:1.3;color:$gris}
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


# ---------- el plano: carga, tiempos y mesas ----------


# ---------- gates YT13–YT19 ----------


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


# ---------- documentos ----------


# ---------- una mesa → HTML + línea de tiempo ----------


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
    maqueta = M["clase"] == "maqueta"   # la maqueta 3D entra como un tablero: su clip a la izquierda, los golpes de la mesa a la derecha
    tablero = M["clase"] == "tablero" or maqueta
    if tablero:
        d = M["fin"] - M["ini"]
        clip = "maquetas/%s.mp4" % M["id"] if maqueta else "clips/e%d.mp4" % S["n"]
        usados.add(clip)
        m.html.append('<div id="%s-marco" class="pz %s" style="left:110px;top:54px;width:1008px;height:972px;z-index:5" data-layout-allow-overlap>'
                      '<video id="%s-anim" class="clip" data-start="0" data-duration="%.3f" data-track-index="0" muted playsinline src="assets/%s" '
                      'style="position:absolute;left:0;top:0;width:1008px;height:972px;object-fit:cover"></video>%s</div>'
                      % (m.id, "maqueta" if maqueta else "pizarra", m.id, d, clip,
                         '<div class="mq-pie" data-layout-ignore>%s</div>' % esc(credito_maqueta(M["maqueta"])) if maqueta else ""))
        if maqueta:
            m.sfx += efectos_maqueta(ctx, M)
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
            src = os.path.join(trabajo, "clips_tablero", os.path.basename(u)) if u.startswith("clips/") else \
                os.path.join(trabajo, regla(ctx, "MAQUETA_CARPETA"), os.path.basename(u)) if u.startswith("maquetas/") else os.path.join(trabajo, u)
            if os.path.exists(src):
                enlazar(src, os.path.join(P, "assets", u))
            else:
                print("AVISO falta %s (youtube.py grabar)" % rel(src))
        for M in ms:
            if M["clase"] == "maqueta" and not clip_maqueta(ctx, M)[1]:
                print("AVISO la maqueta de %s cambió desde su render (o no se ha renderizado): youtube.py grabar %s" % (M["id"], rel(trabajo)))
        for fnt in ("archivo-wdth.woff2", "jetbrains-mono-var.woff2"):
            enlazar(os.path.join(RAIZ, "design", "fonts", fnt), os.path.join(P, "assets", "fonts", fnt))
        enlazar(os.path.join(RAIZ, "design", "grano-mesa.png"), os.path.join(P, "assets", "grano.png"))
        gsap = gsap_local(P)   # GSAP del repositorio (scripts/versiones.py), como el vertical: el render no llama a la red
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
    %s
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
""" % (gsap, C["mesa2"], C["mesa"], C["acento"], C["tinta"], C["mesa2"], C["acento"], C["papel"], C["acento"], dur, "\n".join(hosts), sobre, audio, sobre_tl))
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
    ctx = contexto(trabajo)
    dur_de = {c["numero"]: c["fin"] - c["ini"] for c in ctx["caps"]}
    procs, cola, malas = [], list(Ps), 0
    try:
        while cola or procs:
            while cola and len(procs) < a.paralelo:
                P = cola.pop(0)
                os.makedirs(os.path.join(P, "render"), exist_ok=True)
                log = open(os.path.join(P, "render", "render.log"), "w")
                # el límite de tiempo, proporcional a lo que dura el capítulo; con varios a la vez HyperFrames los pone en fila,
                # así que también cuenta lo que este tiene delante
                dur = dur_de.get(int(P.rsplit("-", 1)[1]), ctx["total"])
                limite = limite_render(dur + sum(x[5] for x in procs))
                pr = lanzar_render(P, ["--quality", a.calidad, "--workers", "1", "-o", "render/capitulo.mp4"], log)
                procs.append((P, pr, log, time.monotonic() + limite, limite, dur))
            for item in list(procs):
                P, pr, log, vence, limite, dur = item
                vencido = pr.poll() is None and time.monotonic() > vence
                if vencido:
                    detener_render(pr)
                if pr.poll() is not None:
                    log.close()
                    procs.remove(item)
                    ok = not vencido and pr.returncode == 0 and os.path.exists(os.path.join(P, "render", "capitulo.mp4"))
                    if vencido:
                        print("render %s: FALLÓ: %s" % (os.path.basename(P), texto_limite("el render del capítulo", limite, dur, os.path.join(P, "render", "render.log"))))
                    else:
                        print("render %s: %s" % (os.path.basename(P), "ok" if ok else "FALLÓ (render/render.log)"))
                    malas += not ok
            if procs:
                try:   # hasta que termine el primero, o hasta el límite más cercano (para verlo vencer a tiempo)
                    procs[0][1].wait(timeout=max(0.2, min(5.0, min(x[3] for x in procs) - time.monotonic())))
                except subprocess.TimeoutExpired:
                    pass
    finally:
        for item in procs:   # una interrupción a mano: ningún render queda huérfano sosteniendo el candado de HyperFrames
            detener_render(item[1])
            item[2].close()
    if malas:
        return 1
    if a.capitulo:
        return 0
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


def cmd_maquetas(a):
    """Las mesas con maqueta 3D del plano → clips_maqueta_16x9/<mesa>.mp4 (1120×1080, el lienzo del tablero), con caché por
    huella. MESA_RENDER=0: dobles sin render."""
    trabajo = os.path.abspath(a.trabajo)
    fp = os.path.join(trabajo, "plano.json")
    if not os.path.exists(fp):
        return 0   # sin plano no hay maquetas
    ctx = contexto(trabajo)
    mesas, _ = resolver(ctx, leer(fp))
    return grabar_maquetas(ctx, mesas, fps=getattr(a, "fps", FPS) or FPS, todo=getattr(a, "todo", False))


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
        av = [x for x in av if ("capítulo %d:" % a.capitulo) in x or " sin datos: " in x]   # un gate sin datos (aviso_datos) vale para todo capítulo
    if a.hoja:
        hoja = hoja_de(ctx, mesas)
        open(os.path.join(trabajo, "plano.md"), "w", encoding="utf-8").write(hoja)
        print("hoja de golpes → %s" % rel(os.path.join(trabajo, "plano.md")))
    n = sum(len(M["golpes"]) for M in mesas)
    print("plano: %d mesas · %d piezas en %s (una cada %.1f s) · %d de %d oraciones con pieza nueva" % (
        len(mesas), n, VD_mmss(ctx["total"]), ctx["total"] / max(1, n), med["con_pieza_nueva"], med["oraciones"]))
    for cap, m in sorted(med["capitulos"].items()):
        print("  capítulo %d: %d piezas · %d de archivo real (%.0f %%) · %s" % (cap, m["piezas"], m["archivo_real"], 100 * m["archivo_real"] / max(1, m["piezas"]), ", ".join(m["tipos"])))
    if med.get("maquetas"):
        print("  maquetas 3D: %s" % ", ".join("%s (capítulo %d, %s, %.1f s)" % (M["id"], M["cap"], M["maqueta"].get("estilo"), M["fin"] - M["ini"]) for M in mesas if M["clase"] == "maqueta"))
    for x in av:
        print("AVISO", x)
    fix = bool(ctx["Y"].get("fixture"))
    for x in f:
        print("AVISO (maqueta)" if fix else "FALLA", x)
    ok = not f or fix
    print("RETORNO " + json.dumps({"archivo": rel(fp), "gate": "ok" if ok else "falla", "fallas": f[:40], "piezas": n,
                                   "archivo_real": sum(m["archivo_real"] for m in med["capitulos"].values())}, ensure_ascii=False))
    return 0 if ok or not a.check else 1


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
    for ln in digesto_maqueta(dict(ctx, es=[es[i] for i in c["idx"]], offs=[offs[i] for i in c["idx"]])):
        print(ln)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    for nombre, fn in (("borrador", cmd_borrador), ("proyecto", cmd_proyecto), ("revisar", cmd_revisar)):
        q = sub.add_parser(nombre)
        q.add_argument("trabajo")
        q.add_argument("--capitulo", type=int)
        q.set_defaults(fn=fn)
    q = sub.add_parser("maquetas")
    q.add_argument("trabajo")
    q.add_argument("--fps", type=int, default=FPS)
    q.add_argument("--todo", action="store_true")
    q.set_defaults(fn=cmd_maquetas)
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
