#!/usr/bin/env python3
"""El banco de pruebas de un módulo del vocabulario de la maqueta 3D (lo usa el agente maqueta-constructor).

Un módulo es `video/maqueta/<clase>/<tipo>.js` + su ficha `<tipo>.json` (+ `scripts/maqueta_tipos/<tipo>.py` si hace
falta); contrato en referencias/diseno/maqueta3d.md («Añadir vocabulario»). Antes de entrar al catálogo
(design/sets3d/vocabulario.json, que escribe SOLO `maqueta3d.py catalogo --registrar`) pasa por aquí:

  1. Lint del módulo: se registra en MAQ.<CLASE> con su nombre; sin red (`https?://`, fetch, import()); sin colores
     escritos (`#hex`, `0xRRGGBB`, `rgb(`, `hsl(`: llegan en ctx.COL y ctx.lin); sin azar ni reloj (`Math.random`,
     `Date.now`, `performance.now`, `new Date`, `setTimeout`, `setInterval`, `requestAnimationFrame`: seek puro, el
     azar fijo es ctx.hash). Sus reglas en Python, si las hay, compilan.
  2. La ficha: completa y su `ejemplo` pasa el validador genérico (maqueta3d.revisar_ficha / validar_campos).
  3. Una maqueta mínima armada con el `ejemplo` (sobre la maqueta base de su escala: la de prueba del motor para
     `pais`; para otra escala, un `video/maqueta/fixture/*.json` cuyo `mundo.escala` sea esa; o la que pases con
     --maqueta) → `maqueta3d.py cuadro` con el módulo inyectado en el catálogo (sin registrarlo todavía):
       · PUREZA: el mismo segundo dibujado por dos caminos (seek directo, en una página nueva; y tras recorrer otros
         segundos antes) da el mismo cuadro (PSNR ≥ 45 dB; idénticos = inf). Un módulo que acumula estado entre
         cuadros, o que usa azar, falla aquí.
       · tiempo por cuadro (aviso por encima de 3 s);
       · hoja de contacto 9:16 y 4:5 (para mirarla UNA vez).
     Un `objeto` se prueba con la primera pieza del catálogo que lo `usa` (si la pieza lleva `objeto`, dibujando ESE
     objeto); una `anotacion`, con su ejemplo en `anotaciones` (de t = 0.6 a t + lo que dure su ejemplo); un `mundo` se prueba con --maqueta (una
     maqueta que lo use); sin ella, solo lint y ficha (aviso).

Subcomandos:
  check <clase>/<tipo> [--maqueta M] [--sin-render] [--salida DIR]
        <clase>: piezas | eventos | objetos | anotaciones | mundos (o pieza, evento, objeto, anotacion, mundo). Salida por defecto:
        sesiones/_modulos/<tipo>/ (cuadros, hojas, maqueta de prueba). Última línea: RETORNO {json}.
  registrar <clase>/<tipo> [--maqueta M] [--sin-render]
        corre el check y, si pasa, `maqueta3d.py catalogo --registrar` (el único escritor del catálogo).

No edita motor.js, maqueta3d.py ni otro módulo. Exit: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse
import tempfile
import contextlib
import copy
import io
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import time
import types

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import maqueta3d as M3  # noqa: E402  (solo se importa: este script no lo edita)

SALIDA = os.path.join(RAIZ, "sesiones", "_modulos")
PSNR_MIN = 45.0          # dB: por encima, el mismo cuadro (el rasterizado de la GPU puede mover ±1 nivel algún píxel)
S_POR_CUADRO_AVISO = 3.0
SINGULAR = {v: k for k, v in M3.CLASES.items()}   # piezas → pieza
# lo que el lint añade a maqueta3d.revisar_ficha (que ya mira #hex, red, Math.random, Date.now, performance.now, new Date)
LINT = [
    (re.compile(r"\b0x[0-9a-fA-F]{6}\b"), "un color escrito a mano (0xRRGGBB): los colores llegan del estilo (ctx.COL, ctx.lin)"),
    (re.compile(r"\b(?:rgba?|hsla?)\s*\(\s*\d"), "un color escrito a mano (rgb()/hsl()): los colores llegan del estilo (ctx.COL, ctx.lin)"),
    (re.compile(r"\b(?:setTimeout|setInterval|requestAnimationFrame)\s*\("), "nada de temporizadores: el motor pide cada cuadro con su t (seek puro)"),
    (re.compile(r"\b(?:localStorage|sessionStorage|indexedDB)\b"), "nada de estado guardado en el navegador: cada cuadro es función pura de t"),
    (re.compile(r"\bdocument\.(?:createElement\s*\(\s*['\"]script|write)\b"), "el módulo no carga scripts: todo llega en ctx"),
]


def sin_comentarios(js):
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    return re.sub(r"(^|[^:\\])//[^\n]*", r"\1", js)


def partir(spec):
    """«piezas/onda» o «evento/onda» → (clase singular, carpeta, tipo) o None."""
    m = re.fullmatch(r"([a-z]+)/([a-z][a-z0-9_]*)", spec or "")
    if not m:
        return None
    c = m.group(1)
    clase = c if c in M3.CLASES else SINGULAR.get(c)
    return (clase, M3.CLASES[clase], m.group(2)) if clase else None


def sintaxis(js, nombre):
    """El módulo tiene que ser JavaScript válido: con un error de sintaxis la página no carga, la hoja sale vacía y el
    check daba «ok» (visto el 2026-11-16). Se revisa con `node --check` sobre una copia .mjs; sin node no se revisa."""
    node = shutil.which("node")
    if not node:
        return []
    with tempfile.TemporaryDirectory() as d:
        copia = os.path.join(d, "modulo.mjs")
        shutil.copyfile(js, copia)
        r = subprocess.run([node, "--check", copia], capture_output=True, text=True)
    if r.returncode == 0:
        return []
    lineas = [l for l in r.stderr.splitlines() if l.strip()]
    donde = next((l.rsplit(":", 1)[-1] for l in lineas if "modulo.mjs:" in l), "?")
    que = next((l for l in lineas if "Error" in l), "error de sintaxis")
    return ["%s: no es JavaScript válido (línea %s: %s)" % (nombre, donde, que.strip())]


def lint(clase, carpeta, tipo):
    """→ (ficha o None, fallas). Usa maqueta3d.revisar_ficha (ficha + lint base) y añade lo de LINT."""
    js, fj = os.path.join(M3.MOTOR, carpeta, tipo + ".js"), os.path.join(M3.MOTOR, carpeta, tipo + ".json")
    f = []
    if not os.path.isfile(js):
        f.append("%s/%s.js no existe (el módulo)" % (carpeta, tipo))
    if not os.path.isfile(fj):
        f.append("%s/%s.json no existe (la ficha)" % (carpeta, tipo))
    if f:
        return None, f
    try:
        fi = M3.cargar_json(fj)
    except ValueError as e:
        return None, ["%s/%s.json: no es JSON válido (%s)" % (carpeta, tipo, e)]
    f += M3.revisar_ficha(fi, clase, tipo, js)
    f += sintaxis(js, "%s/%s.js" % (carpeta, tipo))
    src = sin_comentarios(M3.cargar_texto(js))
    for rx, motivo in LINT:
        m = rx.search(src)
        if m:
            f.append("%s/%s.js: %s («%s»)" % (carpeta, tipo, motivo, m.group(0)))
    for u in (fi.get("usa") or []) if isinstance(fi, dict) else []:
        if u not in M3.vocabulario():
            f.append("%s/%s.json: `usa` «%s», que no está en el catálogo (regístralo antes)" % (carpeta, tipo, u))
    rg = os.path.join(M3.REGLAS_DIR, tipo + ".py")
    if os.path.isfile(rg):
        try:
            py_compile.compile(rg, doraise=True)
        except py_compile.PyCompileError as e:
            f.append("scripts/maqueta_tipos/%s.py no compila: %s" % (tipo, str(e).strip().splitlines()[-1]))
    return fi, f


def inyectar(fi, carpeta, tipo):
    """El módulo entra en el catálogo EN MEMORIA (sin escribir vocabulario.json) para poder dibujarlo antes de registrarlo."""
    v = dict(M3.vocabulario())
    e = dict(fi)
    e["modulo"] = "%s/%s.js" % (carpeta, tipo)
    e["reglas"] = "scripts/maqueta_tipos/%s.py" % tipo if os.path.isfile(os.path.join(M3.REGLAS_DIR, tipo + ".py")) else None
    v[tipo] = e
    import copy
    v = {k: copy.deepcopy(x) for k, x in v.items()}
    M3.expandir_objetos(list(v.values()))   # actor y flujo aceptan el objeto nuevo antes de registrarlo
    M3._VOCAB["v"] = v
    M3._REGLAS.pop(tipo, None)


def base_de(escala):
    """La maqueta base de una escala: la de prueba del motor (pais) o un fixture cuyo mundo.escala sea esa."""
    cand = [M3.FIXTURE] + sorted(os.path.join(os.path.dirname(M3.FIXTURE), n) for n in os.listdir(os.path.dirname(M3.FIXTURE))
                                 if n.endswith(".json") and os.path.join(os.path.dirname(M3.FIXTURE), n) != M3.FIXTURE)
    for ruta in cand:
        try:
            m = M3.cargar_json(ruta)
        except (OSError, ValueError):
            continue
        if ((m.get("mundo") or {}).get("escala") or "pais") == escala:
            return m, ruta
    return None, None


def maqueta_minima(clase, tipo, fi):
    """→ (maqueta, t_foco, tiempos de la hoja, nota) o (None, …, motivo). El ejemplo de la ficha sobre la base de su escala."""
    V = M3.vocabulario()
    if clase == "objeto":
        duenas = sorted(t for t, f in V.items() if f["clase"] == "pieza" and tipo in (f.get("usa") or []))
        if not duenas:
            return None, 0, [], "objeto sin pieza que lo `usa` en el catálogo: pasa --maqueta con una maqueta que lo dibuje"
        fd = copy.deepcopy(V[duenas[0]])
        if "objeto" in (fd.get("parametros") or {}):   # la pieza dibuja ESTE objeto (actor: `objeto`)
            fd["ejemplo"]["objeto"] = tipo
        return maqueta_minima("pieza", duenas[0], fd)[:3] + ("objeto probado con la pieza «%s»" % duenas[0],)
    if clase == "mundo":
        return None, 0, [], "un mundo se prueba con --maqueta (una maqueta que lo use)"
    m = None
    for esc in fi["escalas"]:
        m, ruta = base_de(esc)
        if m:
            break
    if not m:
        return None, 0, [], "no hay maqueta base de escala %s (video/maqueta/fixture/*.json con mundo.escala): pasa --maqueta" % "/".join(fi["escalas"])
    m = copy.deepcopy(m)
    ej = copy.deepcopy(fi["ejemplo"])
    piezas = []
    if clase == "pieza":
        piezas.append(ej)
        prota, t0, dur = ej.get("id"), 0.0, 4.0
    else:
        dur = float(ej.get("dur", ej.get("hasta", 2.6) - ej.get("t", 0.6)) if clase == "anotacion" else ej.get("dur", 2.0))
        t0 = 0.6
        ej["t"] = t0
        if clase == "anotacion":
            ej["hasta"] = round(t0 + dur, 2)
        for nombre, d in (fi.get("parametros") or {}).items():   # las piezas a las que apunta el evento
            if d["tipo"] == "pieza" and ej.get(nombre):
                tipos_ok = d.get("piezas") or sorted(t for t, f in V.items() if f["clase"] == "pieza")
                t_p = next((t for t in tipos_ok if t in V), None)
                if not t_p:
                    return None, 0, [], "el ejemplo apunta a una pieza de tipo %s, que no está en el catálogo" % "/".join(tipos_ok)
                p = copy.deepcopy(V[t_p]["ejemplo"]); p["id"] = ej[nombre]
                if not any(x["id"] == p["id"] for x in piezas):
                    piezas.append(p)
        prota = piezas[0]["id"] if piezas else None
    total = round(max(4.0, t0 + dur + 1.5), 2)
    m["mundo"]["piezas"] = piezas
    m["eventos"] = [ej] if clase == "evento" else []
    m["anotaciones"] = [ej] if clase == "anotacion" else []
    m["marcas"] = []
    m["camara"] = [dict(m["camara"][0], t=0.0)]          # cámara quieta: la prueba mira el módulo, no el vuelo
    if prota:
        m["protagonista"] = prota
    else:
        m.pop("protagonista", None)
    m["duracion_s"] = total
    C = m["capa"]
    C["titulares"] = [{"t": 0.0, "hasta": total, "kicker": "Prueba de módulo", "texto": "%s/%s" % (M3.CLASES[clase], tipo)}]
    C["cifras"] = []
    C["palabras"] = []
    for k in ("seguir", "cierre", "aviso"):
        C.pop(k, None)
    if "progreso" in C:
        C["progreso"] = {"actos": [0.0]}
    m["_comentario"] = "Maqueta mínima de maqueta_modulo.py para %s/%s (no es un video)." % (M3.CLASES[clase], tipo)
    foco = round(t0 + dur * 0.6, 2) if clase != "pieza" else round(total * 0.5, 2)
    hoja = sorted({0.0, round(t0 + dur * 0.25, 2), foco, round(min(total - 0.1, t0 + dur + 0.3), 2)} if clase != "pieza"
                  else {0.0, round(total * 0.25, 2), foco, round(total - 0.2, 2)})
    return m, foco, hoja, "sobre %s" % os.path.relpath(ruta, RAIZ)


def cuadros(ruta, tiempos, salida, formato, hoja):
    """maqueta3d.py cuadro en el mismo proceso (con el módulo inyectado) → (rc, segundos, {t: png}, salida de texto)."""
    a = types.SimpleNamespace(maqueta=ruta, t=[str(t) for t in tiempos], salida=salida, formato=formato, hoja=hoja,
                              pieza=False, lienzo=None, cmd="cuadro")
    buf = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(buf):
        try:
            rc = M3.cmd_cuadro(a)
        except M3.Falla as e:
            print("FALLA %s %s" % e.args); rc = 1
    seg = time.time() - t0
    pref = M3.carpeta_de(formato)
    pngs = {round(float(t), 3): os.path.join(salida, "%s_t%07.3f.png" % (pref, round(float(t), 3))) for t in tiempos}
    return rc, seg, pngs, buf.getvalue()


def psnr(a, b):
    """PSNR (dB) entre dos PNG con ffmpeg; inf si son idénticos; None si no se pudo medir."""
    p = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", a, "-i", b, "-lavfi", "psnr", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"average:(inf|[\d.]+)", p.stderr)
    return None if not m else (float("inf") if m.group(1) == "inf" else float(m.group(1)))


def check(spec, maqueta=None, sin_render=False, salida=None):
    """→ (rc, retorno dict)."""
    p = partir(spec)
    if not p:
        return 2, {"fallas": ["uso: <clase>/<tipo> con clase piezas|eventos|objetos|mundos y tipo en minúsculas (p. ej. eventos/onda)"]}
    clase, carpeta, tipo = p
    R = {"modulo": "%s/%s" % (carpeta, tipo), "clase": clase, "check": "falla", "fallas": [], "avisos": [], "pureza": None,
         "s_por_cuadro": None, "hojas": [], "maqueta": None}
    fi, f = lint(clase, carpeta, tipo)
    R["fallas"] += f
    if f or sin_render:
        if sin_render and not f:
            R["avisos"].append("--sin-render: no se probó la pureza ni se dibujó la hoja")
            R["check"] = "ok"
        return (1 if f else 0), R
    inyectar(fi, carpeta, tipo)
    dest = os.path.abspath(salida or os.path.join(SALIDA, tipo))
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    if maqueta:
        m = M3.cargar_json(maqueta)
        total = float(m.get("duracion_s", 4.0))
        foco = round(total * 0.5, 2)
        hoja = sorted({0.0, round(total * 0.25, 2), foco, round(total * 0.75, 2)})
        nota = "sobre %s" % maqueta
    else:
        m, foco, hoja, nota = maqueta_minima(clase, tipo, fi)
        if m is None:
            R["avisos"].append("sin render: %s" % nota)
            R["check"] = "ok"
            return 0, R
    ruta = os.path.join(dest, "maqueta.json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=1)
    R["maqueta"] = os.path.relpath(ruta, RAIZ)
    R["avisos"].append("maqueta mínima %s" % nota)
    # el validador genérico sobre la maqueta entera (lo que vería `maqueta3d.py check`, sin los gates de tiempos de lectura)
    try:
        for f_ in ("9:16", "4:5"):
            M3.resolver(m, f_, R["avisos"])
    except M3.Falla as e:
        R["fallas"].append("la maqueta de prueba no resuelve: %s %s" % e.args)
        return 1, R
    antes = round(max(0.0, foco - 1.1), 2)
    despues = round(min(float(m["duracion_s"]) - 0.1, foco + 0.9), 2)
    # 1) seek directo: una página nueva que solo dibuja `foco`
    rc1, s1, png1, out1 = cuadros(ruta, [foco], os.path.join(dest, "directo"), "9:16", False)
    # 2) recorrido: la misma página dibuja antes, foco y después (más los de la hoja): foco llega tras otro seek
    ts2 = sorted(set(hoja) | {antes, foco, despues})
    rc2, s2, png2, out2 = cuadros(ruta, ts2, os.path.join(dest, "9x16"), "9:16", True)
    for rc, out, que in ((rc1, out1, "seek directo"), (rc2, out2, "recorrido 9:16")):
        if rc:
            R["fallas"].append("%s: maqueta3d.py cuadro falló: %s" % (que, " | ".join(x for x in out.splitlines() if "FALLA" in x or "fuera" in x) or out.strip()[-300:]))
    if rc1 or rc2:
        return 1, R
    db = psnr(png1[foco], png2[foco])
    R["pureza"] = {"t": foco, "psnr_db": "inf" if db == float("inf") else db, "antes": antes}
    if db is None:
        R["fallas"].append("pureza: no se pudo medir (ffmpeg)")
    elif db < PSNR_MIN:
        R["fallas"].append("pureza: el segundo %.2f dibujado directo y tras recorrer %.2f no es el mismo cuadro (PSNR %.1f dB < %.0f): "
                           "el módulo acumula estado entre cuadros o usa azar; lo que se ve en t se calcula de t (ctx.hash para el azar)"
                           % (foco, antes, db, PSNR_MIN))
    por = (s2 - s1) / max(1, len(ts2) - 1)
    R["s_por_cuadro"] = round(max(por, 0.0), 2)
    if por > S_POR_CUADRO_AVISO:
        R["avisos"].append("lento: ≈ %.1f s por cuadro (aviso desde %.0f s): un video de 45 s son 1,350 cuadros" % (por, S_POR_CUADRO_AVISO))
    rc3, s3, _, out3 = cuadros(ruta, hoja, os.path.join(dest, "4x5"), "4:5", True)
    if rc3:
        R["fallas"].append("4:5: maqueta3d.py cuadro falló: %s" % (" | ".join(x for x in out3.splitlines() if "FALLA" in x) or out3.strip()[-300:]))
    for sub, fmt in (("9x16", "9x16"), ("4x5", "4x5")):
        h = os.path.join(dest, sub, "hoja_%s.jpg" % fmt)
        if os.path.isfile(h):
            R["hojas"].append(os.path.relpath(h, RAIZ))
    # LA OTRA HORA (un mundo de cerca se ve de día y de noche: la vara pide que el módulo se lea en las dos): la misma maqueta
    # con la hora contraria (estilo dia ↔ hora noche; el estilo noche ↔ el estilo dia). Un aviso si no resuelve; la hoja, en
    # hojas[] (`…/otra_hora/hoja_9x16.jpg`): se mira junto con la primera.
    escala = (m.get("mundo") or {}).get("escala") or "pais"
    if not R["fallas"] and escala in ("esquema", "ciudad") and not m.get("tramos"):
        otra = json.loads(json.dumps(m))
        horas = (M3.catalogo_estilos().get(otra.get("estilo")) or {}).get("horas")
        if horas:
            otra["mundo"]["hora"] = "dia" if (otra["mundo"].get("hora") == "noche") else "noche"
            nombre_h = otra["mundo"]["hora"]
        else:
            otra["estilo"] = next((k for k, e in M3.catalogo_estilos().items() if e.get("horas")), otra.get("estilo"))
            otra["mundo"]["hora"] = "noche" if otra.get("estilo") != m.get("estilo") and m.get("estilo") != "noche" else "dia"
            nombre_h = "%s · %s" % (otra["estilo"], otra["mundo"]["hora"])
        ruta_o = os.path.join(dest, "maqueta_otra_hora.json")
        with open(ruta_o, "w", encoding="utf-8") as fh:
            json.dump(otra, fh, ensure_ascii=False, indent=1)
        rc4, s4, _, out4 = cuadros(ruta_o, hoja, os.path.join(dest, "otra_hora"), "9:16", True)
        h = os.path.join(dest, "otra_hora", "hoja_9x16.jpg")
        if rc4 or not os.path.isfile(h):
            R["avisos"].append("la otra hora (%s) no se pudo dibujar: %s" % (nombre_h, (" | ".join(x for x in out4.splitlines() if "FALLA" in x) or out4.strip()[-200:])))
        else:
            R["hojas"].append(os.path.relpath(h, RAIZ))
            R["avisos"].append("otra hora dibujada (%s): mira las dos hojas" % nombre_h)
    if not R["fallas"]:
        R["check"] = "ok"
    return (1 if R["fallas"] else 0), R


def imprimir(rc, R):
    for x in R.get("avisos", []):
        print("AVISO", x)
    for x in R.get("fallas", []):
        print("FALLA", x)
    if R.get("pureza"):
        print("pureza t=%s · PSNR %s dB (directo vs tras %s s)" % (R["pureza"]["t"], R["pureza"]["psnr_db"] if R["pureza"]["psnr_db"] == "inf" else "%.1f" % R["pureza"]["psnr_db"], R["pureza"]["antes"]))
    if R.get("s_por_cuadro") is not None:
        print("tiempo ≈ %.2f s por cuadro" % R["s_por_cuadro"])
    for h in R.get("hojas", []):
        print("hoja:", h)
    print("RETORNO " + json.dumps(R, ensure_ascii=False))
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    for nombre in ("check", "registrar"):
        s = sub.add_parser(nombre, help="lint + ficha + pureza + hoja" + (" y, si pasa, catalogo --registrar" if nombre == "registrar" else ""))
        s.add_argument("modulo", help="<clase>/<tipo>, p. ej. eventos/onda o piezas/ruta")
        s.add_argument("--maqueta", help="una maqueta de prueba propia (en vez de la mínima armada del ejemplo)")
        s.add_argument("--sin-render", dest="sin_render", action="store_true", help="solo lint y ficha")
        s.add_argument("--salida", help="carpeta de los cuadros (por defecto sesiones/_modulos/<tipo>/)")
        s.add_argument("--motor", help=argparse.SUPPRESS)   # pruebas: una copia de video/maqueta/ con módulos rotos a propósito
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    if a.motor:
        if a.cmd == "registrar":
            print("ERROR --motor es solo para check (registrar escribe el catálogo real)", file=sys.stderr)
            return 2
        M3.MOTOR = os.path.abspath(a.motor)
    rc, R = check(a.modulo, a.maqueta, a.sin_render, a.salida)
    if rc == 2:
        print("ERROR " + R["fallas"][0], file=sys.stderr)
        return 2
    if a.cmd == "check" or rc:
        return imprimir(rc, R)
    p = subprocess.run([sys.executable, os.path.join(AQUI, "maqueta3d.py"), "catalogo", "--registrar"], capture_output=True, text=True)
    print(p.stdout.strip())
    if p.returncode:
        R["check"] = "falla"
        R["fallas"].append("catalogo --registrar: " + (p.stdout + p.stderr).strip().splitlines()[-1])
        return imprimir(1, R)
    R["registrado"] = True
    return imprimir(0, R)


if __name__ == "__main__":
    sys.exit(main())
