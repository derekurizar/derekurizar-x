#!/usr/bin/env python3
"""Biblioteca de animaciones de la escena `explica` de /video (video/animaciones/): animaciones a medida que explican el
mecanismo de un fenómeno (por qué o cómo pasa), escritas por el agente video-animador para un video y guardadas para
reutilizarlas. Cada una es video/animaciones/<id>.js con ANIM.registrar('<id>', {meta, pintar, seek}) (contrato en
referencias/roles/video-animador.md); catalogo.json lo escribe SOLO este script.

Uso:
  python3 scripts/animaciones.py --lista                             las animaciones del catálogo, por mecanismo
  python3 scripts/animaciones.py --check ID [--paleta P] [--salida D] lint + node --check + meta + grabación doble a
                                                                     10 fps (iguales; ≥ 50 dB) + 4:5 + quietud V12 +
                                                                     hojas de contacto (una por paso) en D
  python3 scripts/animaciones.py --registrar ID [--video SLUG]       lo agrega al catálogo (o suma un uso)
  python3 scripts/animaciones.py --asignar TRABAJO --escena N --id ID   pone `animacion: ID` en la escena explica N de
                                                                     TRABAJO/guion.json y repasa el gate del guion
  python3 scripts/animaciones.py --validar                           K4: catálogo ↔ archivos, lint y meta

Salida: 0 ok · 1 fallo · 2 uso incorrecto.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(RAIZ, "video", "animaciones")
CATALOGO = os.path.join(DIR, "catalogo.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_BYTES = 40000
SVG_NS = "http://www.w3.org/2000/svg"   # el único «enlace» permitido: el espacio de nombres de createElementNS
# lo que una animación NO puede hacer: el estado es solo seek(t) (clips idénticos en serie y en paralelo), sin red ni
# colores fijos (la paleta del hilo llega como variables CSS, estilo Noche: var(--bg), var(--ink), var(--acento),
# var(--tinta-acento), var(--a2), var(--a3)…; cualquier var(--x) vale) ni tipos fuera de Noche
PROHIBIDO = [
    (r"Math\.random", "azar (Math.random): el cuadro debe ser función de t"),
    (r"\bDate\b|performance\.now", "reloj (Date, performance.now): el cuadro debe ser función de t"),
    (r"requestAnimationFrame|setTimeout|setInterval", "temporizadores: la grabadora llama a seek(t) cuadro a cuadro"),
    (r"\bfetch\b|XMLHttpRequest|import\s*\(|\bimportScripts\b", "red o módulos: cero dependencias externas"),
    (r"https?://", "enlace externo"),
    (r"#[0-9a-fA-F]{3,8}\b", "color fijo en hexadecimal: usa var(--ink), var(--bg), var(--acento)…"),
    (r"\brgba?\s*\(|\bhsla?\s*\(", "color fijo: usa las variables de la paleta (color-mix si hace falta transparencia)"),
    (r"Instrument\s+Serif", "Instrument Serif no va en el video (Noche): Archivo 800 en textos y Archivo 900 condensado "
                            "(font-stretch: 62.5%) en cifras, nombres y años"),
    (r"font-stretch\s*:[^;`'\"]*;[^`'\"]*?\bfont\s*:", "font-stretch antes del atajo font: (el atajo lo devuelve a normal): "
                                                     "pon font-stretch después de font:"),
]


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def escribir(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


def catalogo():
    return leer(CATALOGO) if os.path.exists(CATALOGO) else {"animaciones": []}


def ruta(aid):
    return os.path.join(DIR, aid + ".js")


def sin_comentarios(js):
    js = re.sub(r"/\*[\s\S]*?\*/", "", js)
    return re.sub(r"(^|[^:\\])//[^\n]*", r"\1", js)


def lint(aid, archivo=None):
    """Fallas estáticas del módulo (lista vacía = ok); `archivo` prueba otro camino con el mismo id (las pruebas)."""
    if not RE_ID.match(aid or ""):
        return ["id «%s» inválido (minúsculas, números y guiones)" % aid]
    p = archivo or ruta(aid)
    if not os.path.exists(p):
        return ["no existe video/animaciones/%s.js" % aid]
    js = open(p, encoding="utf-8").read()
    out = []
    if len(js.encode("utf-8")) > MAX_BYTES:
        out.append("%d bytes (máximo %d): una animación es una idea" % (len(js.encode("utf-8")), MAX_BYTES))
    if not re.search(r"ANIM\.registrar\(\s*['\"]%s['\"]" % re.escape(aid), js):
        out.append("falta ANIM.registrar('%s', {…}) con el mismo id que el archivo" % aid)
    codigo = sin_comentarios(js).replace(SVG_NS, "")
    for patron, motivo in PROHIBIDO:
        m = re.search(patron, codigo)
        if m:
            out.append("%s («%s»)" % (motivo, m.group(0)))
    return out


def meta_de(aid):
    """El `meta` que registra el módulo (lo evalúa node con un ANIM falso) → (meta, error)."""
    prog = ("const fs=require('fs');let M=null;const ANIM={registrar:(id,m)=>{M={id,meta:m.meta||null,"
            "pintar:typeof m.pintar,seek:typeof m.seek}}};new Function('ANIM',fs.readFileSync(process.argv[1],'utf8'))(ANIM);"
            "process.stdout.write(JSON.stringify(M))")
    r = subprocess.run(["node", "-e", prog, ruta(aid)], capture_output=True, text=True)
    if r.returncode:
        return None, (r.stderr.strip().splitlines() or ["node falló"])[-1]
    d = json.loads(r.stdout or "null")
    if not d:
        return None, "el módulo no llama ANIM.registrar"
    if d["pintar"] != "function" or d["seek"] != "function":
        return None, "registra {pintar, seek} como funciones"
    if d["id"] != aid:
        return None, "registra el id «%s» y el archivo es %s.js" % (d["id"], aid)
    return d["meta"], None


def fallas_meta(meta):
    import video as VID
    lo_hi = VID.EXPLICA_PASOS
    out = []
    if not isinstance(meta, dict):
        return ["falta `meta` {descripcion, mecanismo, temas, pasos: [mín, máx], ejemplo: {titulo, pasos}}"]
    if meta.get("mecanismo") not in VID.MECANISMOS_EXPLICA:
        out.append("meta.mecanismo: uno de %s (lo que la animación muestra; solo se reutiliza para ese mecanismo)"
                   % "|".join(VID.MECANISMOS_EXPLICA))
    if not 10 <= len(str(meta.get("descripcion") or "")) <= 160:
        out.append("meta.descripcion de 10–160 caracteres")
    if not isinstance(meta.get("temas"), list) or not meta["temas"]:
        out.append("meta.temas: lista de palabras para encontrarla otra vez")
    ps = meta.get("pasos")
    if not (isinstance(ps, list) and len(ps) == 2 and all(isinstance(x, int) for x in ps) and lo_hi[0] <= ps[0] <= ps[1] <= lo_hi[1]):
        out.append("meta.pasos = [mín, máx] dentro de %d–%d" % lo_hi)
        return out
    ej = meta.get("ejemplo") or {}
    eps = ej.get("pasos")
    if not (ej.get("titulo") and isinstance(eps, list) and ps[0] <= len(eps) <= ps[1]
            and all(isinstance(x, str) and 0 < len(x) <= VID.PASO_CARACTERES for x in eps)):
        out.append("meta.ejemplo = {titulo, pasos: %d–%d textos de ≤ %d caracteres} (con él se prueba)" % (ps[0], ps[1], VID.PASO_CARACTERES))
    return out


# ---------- la prueba de verdad: grabarla ----------
def escena_de_prueba(aid, meta, paleta):
    """escenas.json mínimo con una sola escena explica: voz falsa que dice cada paso del ejemplo (0.32 s por palabra)."""
    import video as VID
    ej = meta["ejemplo"]
    t, pal, pasos = 0.6, [], []
    for k, paso in enumerate(ej["pasos"]):
        pasos.append({"texto": paso, "start": round(t, 3)})
        for w in (("Luego, " if k else "Primero, ") + paso + ".").split():
            pal.append({"text": w, "start": round(t, 3), "end": round(t + 0.3, 3)})
            t += 0.32
        t += 0.6
    fin = pal[-1]["end"]
    dur = round(fin + 1.4, 3)
    S = {"n": 1, "tipo": "explica", "tuit": None, "plantilla": "explica", "enlace": None, "icono": None, "dur": dur,
         "fin_voz": fin, "palabras": pal, "arriba": [{"text": w, "start": round(0.3 + 0.12 * k, 3)} for k, w in enumerate(ej["titulo"].split())],
         "animacion": aid, "P": {"titulo": ej["titulo"], "pasos": ej["pasos"]},
         "T": {"ini": 0.6, "pasos": pasos, "fin": fin, "dur": dur}, "transicion": None, "eventos": [], "sfx": []}
    return {"version": 2, "colores": VID.colores(paleta), "contexto_superior": "Animaciones · prueba", "redes": [], "escenas": [S]}


def grabar(d, formato):
    args = ["node", os.path.join(RAIZ, "scripts", "video_grabar.js"), "--dir", d, "--hilo", d, "--fps", "10", "--paralelo", "1"]
    r = subprocess.run(args + (["--formato", "4:5"] if formato == "4:5" else []), capture_output=True, text=True)
    if r.returncode == 3:   # V13: algo de la animación sale de la zona segura (lienzo de explica.html, V.zona)
        return "V13 zona segura: " + " | ".join(ln.split(": ", 1)[-1] for ln in r.stderr.splitlines() if ln.startswith("FALLA V13"))[:600]
    return None if r.returncode == 0 else (r.stderr.strip() or r.stdout.strip())[-600:]


def framemd5(clip):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", clip, "-f", "framemd5", "-"], capture_output=True, text=True)
    return [ln.split(",")[-1].strip() for ln in r.stdout.splitlines() if ln and not ln.startswith("#")]


# Dos grabaciones de un seek(t) puro dan los mismos cuadros salvo ruido de rasterizado de Chromium (unos píxeles de
# texto o de un borde con 1–70 niveles; medido ≥ 55 dB de PSNR); un seek impuro (estado que se acumula) da mucho menos.
PSNR_MIN = 50


def peor_psnr(a, b):
    """(PSNR más bajo cuadro a cuadro entre dos clips, su cuadro); inf si todos son idénticos."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", a, "-i", b, "-lavfi", "psnr=stats_file=-", "-f", "null", "-"],
                       capture_output=True, text=True)
    peor = (float("inf"), None)
    for ln in r.stdout.splitlines():
        m = re.search(r"n:(\d+).*psnr_avg:(\S+)", ln)
        if m:
            v = float("inf") if m.group(2) == "inf" else float(m.group(2))
            if v < peor[0]:
                peor = (v, int(m.group(1)))
    return peor


def contacto(clip, tiempos, out, alto):
    import video as VID
    tmp = out + "_cuadros"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    for k, t in enumerate(tiempos, 1):
        VID.ff("-ss", "%.2f" % t, "-i", clip, "-frames:v", "1", os.path.join(tmp, "c_%03d.png" % k))
    VID.ff("-framerate", "1", "-i", os.path.join(tmp, "c_%03d.png"), "-vf",
           "scale=360:%d,tile=%dx1:padding=6:color=white" % (alto, len(tiempos)), "-frames:v", "1", out)
    shutil.rmtree(tmp, ignore_errors=True)


def cmd_check(a):
    import video as VID
    aid = a.check
    fallas = lint(aid)
    if not fallas:
        r = subprocess.run(["node", "--check", ruta(aid)], capture_output=True, text=True)
        if r.returncode:
            fallas.append("node --check: %s" % (r.stderr.strip().splitlines() or ["error de sintaxis"])[-1])
    meta = None
    if not fallas:
        meta, e = meta_de(aid)
        fallas += [e] if e else fallas_meta(meta)
    if fallas:
        for x in fallas:
            print("FALLA %s: %s" % (aid, x))
        return 1
    paleta = a.paleta or list(leer(os.path.join(RAIZ, "design", "tokens.json"))["paletas"])[0]
    sal = os.path.abspath(a.salida or os.path.join(RAIZ, "sesiones", "_animaciones", aid))
    shutil.rmtree(sal, ignore_errors=True)
    os.makedirs(sal)
    escribir(os.path.join(sal, "escenas.json"), escena_de_prueba(aid, meta, paleta))
    S = leer(os.path.join(sal, "escenas.json"))["escenas"][0]
    clip = os.path.join(sal, "clips", "e1.mp4")
    err = grabar(sal, "9:16")
    if err:
        print("FALLA %s: la página no grabó: %s" % (aid, err))
        return 1
    md5a = framemd5(clip)
    shutil.move(clip, os.path.join(sal, "primera.mp4"))
    err = grabar(sal, "9:16")
    if err:
        print("FALLA %s: la segunda grabación falló: %s" % (aid, err))
        return 1
    if framemd5(clip) != md5a:
        psnr, cuadro = peor_psnr(os.path.join(sal, "primera.mp4"), clip)
        if psnr < PSNR_MIN:
            fallas.append("dos grabaciones dan cuadros distintos (cuadro %s: %.1f dB < %d): seek(t) no es puro (¿estado que "
                          "se acumula entre cuadros?)" % (cuadro, psnr, PSNR_MIN))
    os.remove(os.path.join(sal, "primera.mp4"))
    err = grabar(sal, "4:5")
    if err:
        fallas.append("el formato 4:5 no grabó: %s" % err)
    tramos = VID.ventanas_quietas(VID.movimiento_de(clip))
    fallas += ["V12 quietud: %.1f s sin movimiento desde %.1f s (añade movimiento continuo)" % (d, t0) for t0, d in tramos]
    tiempos = [min(p["start"] + 0.6, S["dur"] - 0.3) for p in S["T"]["pasos"]] + [S["dur"] - 0.3]
    contacto(clip, tiempos, os.path.join(sal, "contacto.png"), 640)
    if os.path.exists(os.path.join(sal, "clips_4x5", "e1.mp4")):
        contacto(os.path.join(sal, "clips_4x5", "e1.mp4"), tiempos, os.path.join(sal, "contacto_4x5.png"), 450)
    for x in fallas:
        print("FALLA %s: %s" % (aid, x))
    print("%s %s · %d pasos · %.1f s · paleta %s → %s/contacto.png y contacto_4x5.png (un cuadro por paso y el final)"
          % ("ok   " if not fallas else "MAL  ", aid, len(S["T"]["pasos"]), S["dur"], paleta, os.path.relpath(sal, RAIZ)))
    return 1 if fallas else 0


def cmd_registrar(a):
    aid = a.registrar
    fallas = lint(aid)
    meta = None
    if not fallas:
        meta, e = meta_de(aid)
        fallas += [e] if e else fallas_meta(meta)
    if fallas:
        for x in fallas:
            print("FALLA %s: %s" % (aid, x))
        return 1
    cat = catalogo()
    ent = next((x for x in cat["animaciones"] if x["id"] == aid), None)
    nueva = ent is None
    if nueva:
        ent = {"id": aid, "origen": a.video or "semilla", "usos": []}
        cat["animaciones"].append(ent)
    ent.update({"descripcion": meta["descripcion"], "mecanismo": meta["mecanismo"], "temas": meta["temas"], "pasos": meta["pasos"], "ejemplo": meta["ejemplo"]})
    if a.video and a.video not in ent["usos"]:
        ent["usos"].append(a.video)
    cat["animaciones"].sort(key=lambda x: x["id"])
    escribir(CATALOGO, cat)
    print("%s %s en video/animaciones/catalogo.json · usos: %s" % ("registrada" if nueva else "actualizada", aid, ", ".join(ent["usos"]) or "—"))
    return 0


def cmd_asignar(a):
    trabajo = os.path.abspath(a.asignar)
    p = os.path.join(trabajo, "guion.json")
    if not os.path.exists(p) or a.escena is None or not a.id:
        print("uso: --asignar TRABAJO --escena N --id ID", file=sys.stderr)
        return 2
    if not any(x["id"] == a.id for x in catalogo()["animaciones"]):
        print("FALLA %s no está en el catálogo: corre --check y --registrar primero" % a.id)
        return 1
    g = leer(p)
    es = g.get("escenas") or []
    if not 1 <= a.escena <= len(es) or es[a.escena - 1].get("tipo") != "explica":
        print("FALLA la escena %s de %s no es una escena explica" % (a.escena, os.path.relpath(p, RAIZ)))
        return 1
    es[a.escena - 1]["animacion"] = a.id
    escribir(p, g)
    print("escena %d → animacion «%s»" % (a.escena, a.id))
    # el gate del guion es el del flujo del TRABAJO: /historia y /explica tienen el suyo (que llama al de /video con sus escenas)
    st = os.path.join(trabajo, "video.json")
    tipo = leer(st).get("tipo") if os.path.exists(st) else None
    script = {"historia": "historia.py", "explica": "explica.py"}.get(tipo, "video.py")
    return subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", script), "guion", trabajo, "--check"]).returncode


def fallas_k4():
    """K4 (validate.py): el catálogo es JSON con {animaciones: [...]}, cada entrada tiene su archivo y pasa el lint, y
    no hay módulos sin entrada."""
    import video as VID
    out = []
    try:
        cat = catalogo()
    except ValueError as e:
        return ["video/animaciones/catalogo.json no es JSON válido: %s" % e]
    ids = []
    for x in cat.get("animaciones") or []:
        aid = x.get("id")
        ids.append(aid)
        if not RE_ID.match(aid or ""):
            out.append("id «%s» inválido" % aid)
            continue
        out += ["%s: %s" % (aid, f) for f in lint(aid)]
        ps = x.get("pasos")
        if not (isinstance(ps, list) and len(ps) == 2):
            out.append("%s: la entrada no tiene pasos [mín, máx] (corre --registrar)" % aid)
        if x.get("mecanismo") not in VID.MECANISMOS_EXPLICA:
            out.append("%s: la entrada no tiene mecanismo de %s (pon meta.mecanismo y corre --registrar)"
                       % (aid, "|".join(VID.MECANISMOS_EXPLICA)))
    if len(ids) != len(set(ids)):
        out.append("ids repetidos en el catálogo")
    sueltos = sorted(f[:-3] for f in os.listdir(DIR) if f.endswith(".js") and f[:-3] not in ids) if os.path.isdir(DIR) else []
    out += ["video/animaciones/%s.js no está en el catálogo (corre --registrar %s)" % (s, s) for s in sueltos]
    return out


def main():
    ap = argparse.ArgumentParser(description="Biblioteca de animaciones de la escena explica de /video.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("Uso:")[1])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--lista", action="store_true", help="las animaciones del catálogo")
    g.add_argument("--check", metavar="ID", help="prueba una animación (lint, sintaxis, meta, grabación doble, 4:5, quietud)")
    g.add_argument("--registrar", metavar="ID", help="la agrega al catálogo o suma un uso")
    g.add_argument("--asignar", metavar="TRABAJO", help="pone la animación en la escena explica del guion")
    g.add_argument("--validar", action="store_true", help="K4: catálogo ↔ archivos y lint")
    ap.add_argument("--paleta", help="paleta de design/tokens.json para --check (por defecto la primera)")
    ap.add_argument("--salida", help="carpeta de --check (por defecto sesiones/_animaciones/<id>)")
    ap.add_argument("--video", help="slug del hilo cuyo video la usa (--registrar)")
    ap.add_argument("--escena", type=int, help="número de la escena explica (--asignar)")
    ap.add_argument("--id", help="id de la animación (--asignar)")
    a = ap.parse_args()
    if a.lista:   # por mecanismo: una animación se reutiliza solo para el mismo (video.py MECANISMOS_EXPLICA)
        import video as VID
        cat = catalogo()["animaciones"]
        for m, que in VID.MECANISMOS_EXPLICA.items():
            print("%s — %s" % (m, que))
            for x in [x for x in cat if x.get("mecanismo") == m] or [None]:
                print("  %s" % ("(ninguna aún: el animador escribe la primera)" if x is None else "%-22s %d–%d pasos · %s · usos: %s" % (
                    x["id"], *x.get("pasos", [0, 0]), x.get("descripcion", ""), ", ".join(x.get("usos") or []) or "—")))
        for x in [x for x in cat if x.get("mecanismo") not in VID.MECANISMOS_EXPLICA]:
            print("SIN MECANISMO %s (corre --registrar %s)" % (x["id"], x["id"]))
        return 0
    if a.check:
        return cmd_check(a)
    if a.registrar:
        return cmd_registrar(a)
    if a.asignar:
        return cmd_asignar(a)
    fs = fallas_k4()
    for x in fs:
        print("FALLA K4 %s" % x)
    print("K4 %s · %d animación(es)" % ("ok" if not fs else "con fallas", len(catalogo()["animaciones"])))
    return 1 if fs else 0


if __name__ == "__main__":
    sys.exit(main())
