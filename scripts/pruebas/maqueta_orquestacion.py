#!/usr/bin/env python3
"""Pruebas de la orquestación de la maqueta 3D (fases 4 y 5): el constructor de módulos y quién lo usa. Solo stdlib.

Rápidas (sin render, < 5 s):
  1. maqueta_modulo.py check --sin-render pasa con módulos del catálogo (eventos/onda, piezas/ruta) y MUERDE con un
     módulo roto a propósito en una copia de video/maqueta/ (color hex, 0xRRGGBB, Math.random, Date.now, setTimeout,
     red, sin registrarse, ficha cuyo ejemplo no pasa, nombre con guion).
  2. Nadie lista tipos a mano: video3d.js, plano.js, las guías del director, del constructor, del realizador, del crítico 3D
     y del explica-editor no traen una lista de tipos del catálogo (un arreglo JS con ≥ 2 tipos, o una lista de ≥ 3 tipos
     con tilde invertida en una misma línea): todos leen `maqueta3d.py catalogo`.
  3. video3d.js: para en elegir_gancho, devuelve cierres, usa agentRol/conReparacion/guia, lee el catálogo, ≤ 3
     constructores a la vez; plano.js: la fase del constructor es opcional y acotada (una vez).
  4. Los dos agentes nuevos existen con su modelo y herramientas, y sus guías también.
Con --render: además la pureza muerde (un módulo que acumula estado entre cuadros) y pasa en eventos/onda (≈ 30 s).

Uso: python3 scripts/pruebas/maqueta_orquestacion.py [--render]   · exit 0 ok · 1 falla
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import maqueta3d as M3  # noqa: E402

MOD = os.path.join(RAIZ, "scripts", "maqueta_modulo.py")
FALLAS = []


def ok(cond, msg):
    if not cond:
        FALLAS.append(msg)
    return cond


def correr(*args):
    p = subprocess.run([sys.executable, MOD] + list(args), capture_output=True, text=True, cwd=RAIZ)
    return p.returncode, p.stdout + p.stderr


def leer(r):
    with open(os.path.join(RAIZ, r), encoding="utf-8") as fh:
        return fh.read()


def lint_rapido():
    for spec in ("eventos/onda", "piezas/ruta"):
        rc, out = correr("check", spec, "--sin-render")
        ok(rc == 0, "check --sin-render %s debería pasar: %s" % (spec, out.strip()[-400:]))
    tmp = tempfile.mkdtemp(prefix="maqmod_")
    try:
        motor = os.path.join(tmp, "maqueta")
        shutil.copytree(M3.MOTOR, motor)
        onda_js = open(os.path.join(motor, "eventos", "onda.js"), encoding="utf-8").read()
        onda_json = json.load(open(os.path.join(motor, "eventos", "onda.json"), encoding="utf-8"))
        casos = {
            "hex": (onda_js.replace("orden: 60,", "orden: 60, color: '#ff8800',"), None, "color escrito"),
            "hex0x": (onda_js.replace("orden: 60,", "orden: 60, color: 0xff8800,"), None, "0xRRGGBB"),
            "azar": (onda_js.replace("const u = (t - e.t) / e.dur;", "const u = (t - e.t) / e.dur * Math.random();"), None, "azar"),
            "reloj": (onda_js.replace("const u = (t - e.t) / e.dur;", "const u = (t - e.t) / e.dur + Date.now() * 0;"), None, "azar ni reloj"),
            "timer": (onda_js.replace("orden: 60,", "orden: 60, armar() { setTimeout(() => 0, 10); },"), None, "temporizadores"),
            "red": (onda_js.replace("orden: 60,", "orden: 60, url: 'https://ejemplo.org/x.json',"), None, "red"),
            "sinreg": (onda_js.replace("MAQ.EVENTOS.onda =", "MAQ.EVENTOS.otra ="), None, "no se registra"),
            "ejemplo": (onda_js, dict(onda_json, ejemplo=dict(onda_json["ejemplo"], radio_km=99999)), "radio_km"),
        }
        for nombre, (js, ficha, espera) in casos.items():
            tipo = "zz" + nombre
            with open(os.path.join(motor, "eventos", tipo + ".js"), "w", encoding="utf-8") as fh:
                fh.write(js.replace("MAQ.EVENTOS.onda", "MAQ.EVENTOS." + tipo) if nombre != "sinreg" else js)
            f = dict(ficha or onda_json, tipo=tipo)
            f["ejemplo"] = dict(f["ejemplo"], tipo=tipo)
            with open(os.path.join(motor, "eventos", tipo + ".json"), "w", encoding="utf-8") as fh:
                json.dump(f, fh, ensure_ascii=False)
            rc, out = correr("check", "eventos/" + tipo, "--sin-render", "--motor", motor)
            ok(rc == 1 and espera in out, "el lint debería morder «%s» (espera «%s»): rc %d · %s" % (nombre, espera, rc, out.strip()[-300:]))
        rc, out = correr("check", "eventos/con-guion", "--sin-render")
        ok(rc == 2, "un nombre con guion es uso incorrecto (exit 2): rc %d" % rc)
        rc, out = correr("registrar", "eventos/onda", "--motor", motor)
        ok(rc == 2, "registrar no acepta --motor (escribiría el catálogo real): rc %d" % rc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pureza_render():
    rc, out = correr("check", "eventos/onda")
    ok(rc == 0 and "psnr_db" in out, "check eventos/onda con render debería pasar: %s" % out.strip()[-400:])
    tmp = tempfile.mkdtemp(prefix="maqmod_")
    try:
        motor = os.path.join(tmp, "maqueta")
        shutil.copytree(M3.MOTOR, motor)
        js = open(os.path.join(motor, "eventos", "onda.js"), encoding="utf-8").read()
        # impuro: el radio crece con cada cuadro dibujado (estado acumulado en el módulo), no con t
        js = js.replace("MAQ.EVENTOS.onda = {", "let cuenta = 0;\n  MAQ.EVENTOS.zzimpuro = {").replace(
            "const u = (t - e.t) / e.dur;", "cuenta += 1; const u = Math.min(1, cuenta / 3);")
        f = json.load(open(os.path.join(motor, "eventos", "onda.json"), encoding="utf-8"))
        f["tipo"] = "zzimpuro"; f["ejemplo"] = dict(f["ejemplo"], tipo="zzimpuro")
        open(os.path.join(motor, "eventos", "zzimpuro.js"), "w", encoding="utf-8").write(js)
        json.dump(f, open(os.path.join(motor, "eventos", "zzimpuro.json"), "w", encoding="utf-8"))
        rc, out = correr("check", "eventos/zzimpuro", "--motor", motor, "--salida", os.path.join(tmp, "salida"))
        ok(rc == 1 and "no es el mismo cuadro" in out, "la pureza debería morder un módulo que acumula estado: rc %d · %s" % (rc, out.strip()[-400:]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def sin_tipos_a_mano():
    tipos = set(M3.vocabulario())
    ok(len(tipos) >= 5, "el catálogo está vacío o casi: corre maqueta3d.py catalogo --registrar")
    archivos = [".claude/workflows/video3d.js", ".claude/workflows/plano.js", ".claude/agents/video3d-director.md",
                ".claude/agents/maqueta-constructor.md", "referencias/roles/video3d-director.md", "referencias/roles/maqueta-constructor.md",
                "referencias/roles/video-realizador.md", "referencias/roles/video-critico/3d.md", "referencias/roles/explica-editor.md"]
    for r in archivos:
        if not ok(os.path.isfile(os.path.join(RAIZ, r)), "falta %s" % r):
            continue
        src = leer(r)
        for m in re.finditer(r"\[([^\[\]]*)\]", src):
            dentro = set(re.findall(r"['\"]([a-z_]+)['\"]", m.group(1)))
            ok(len(dentro & tipos) < 2, "%s lista tipos del catálogo a mano: [%s]" % (r, m.group(1)[:80]))
        for n, ln in enumerate(src.splitlines(), 1):
            con_tilde = set(re.findall(r"`([a-z_]+)`", ln)) & tipos
            ok(len(con_tilde) < 3, "%s:%d lista tipos del catálogo a mano (%s): que lea `maqueta3d.py catalogo`" % (r, n, ", ".join(sorted(con_tilde))))
        if r.endswith((".js", "director.md", "constructor.md", "realizador.md")):
            ok("catalogo" in src, "%s no manda a leer el catálogo (maqueta3d.py catalogo)" % r)


def workflows():
    v = leer(".claude/workflows/video3d.js")
    for txt, que in (("export const meta", "meta"), ("name: 'video3d'", "name"), ("whenToUse:", "whenToUse"), ("phases:", "phases"),
                     ("'elegir_gancho'", "para en elegir_gancho"), ("cierres", "devuelve cierres"), ("agentRol(", "agentRol"),
                     ("conReparacion(", "conReparacion"), ("guia(", "guia()"), ("maqueta-constructor", "constructor"),
                     ("video3d-director", "director"), ("'elegir_estilo'", "para si la confianza del estilo es baja"),
                     ("// <comun>", "bloque común"), ("storyboard", "storyboard")):
        ok(txt in v, "video3d.js: falta %s («%s»)" % (que, txt))
    m = re.search(r"\bCONSTRUCTORES_MAX = (\d+)", v)
    ok(m and int(m.group(1)) <= 3, "video3d.js: CONSTRUCTORES_MAX ≤ 3")
    p = leer(".claude/workflows/plano.js")
    ok("maqueta-constructor" in p and "briefs" in p, "plano.js: la fase opcional del constructor (briefs del realizador)")
    ok(re.search(r"^const BRIEFS_MAX = [12]\b", p, re.M), "plano.js: BRIEFS_MAX (1–2) acota la fase del constructor")
    import armar_workflows as AW
    ok("video3d.js" in AW.WORKFLOWS, "armar_workflows.WORKFLOWS no incluye video3d.js")


def agentes():
    for nombre, tools in (("video3d-director", "Read, Write, Edit, Bash"), ("maqueta-constructor", "Read, Write, Edit, Bash")):
        r = ".claude/agents/%s.md" % nombre
        if not ok(os.path.isfile(os.path.join(RAIZ, r)), "falta %s" % r):
            continue
        src = leer(r)
        ok(re.search(r"^name: %s$" % nombre, src, re.M), "%s: name" % r)
        ok(re.search(r"^model: opus$", src, re.M), "%s: model opus" % r)
        ok(re.search(r"^tools: %s$" % re.escape(tools), src, re.M), "%s: tools %s (sin web)" % (r, tools))
        ok(os.path.isfile(os.path.join(RAIZ, "referencias", "roles", nombre + ".md")), "falta referencias/roles/%s.md" % nombre)
    ok("motor.js" in leer("referencias/roles/maqueta-constructor.md"), "la guía del constructor dice que nunca edita motor.js")


def main():
    lint_rapido()
    sin_tipos_a_mano()
    workflows()
    agentes()
    if "--render" in sys.argv:
        pureza_render()
    for f in FALLAS:
        print("FALLA", f)
    print("maqueta_orquestacion: %s" % ("ok" if not FALLAS else "%d falla(s)" % len(FALLAS)))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
