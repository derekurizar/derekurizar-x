#!/usr/bin/env python3
"""Pruebas de los arreglos de la mesa de archivo de la ola 1 (2026-11-14). Sin render de HyperFrames y sin red; ffmpeg solo
para videos de 1 s. Exit 0 ok · 1 falla (con el detalle).

  marca       el «doble sin render» (MESA_RENDER=0) se anota por formato: un 4:5 de doble no queda limpio porque el 9:16 se
              vuelva a grabar de verdad, ni un formato queda limpio hasta que su render de verdad se MONTA; la marca
              general (la que leen los `entregar`) existe mientras algún formato siga marcado; una marca vieja se reparte
  avisos      un elenco, un respaldo o unos hechos ilegibles dan AVISO (en los avisos del gate y por stderr), no un gate
              callado; un error de programación no se atrapa; el respaldo del 16:9 ya no queda vacío
  sin_red     ningún proyecto de la mesa (vertical o 16:9) carga un <script> de fuera: GSAP sale de design/vendor/
  version     la versión de HyperFrames se define una sola vez (scripts/versiones.py)
  limite      el render tiene un límite proporcional a la duración, detiene todo su grupo de procesos y lo dice claro
  notas       mesa.notas_leidas lee también sesiones/_descargas/congreso (los .txt de `congreso.py leer`)
  pagina      mesa.pagina_png avisa si falta pdftoppm
  doctor      scripts/doctor.sh pide Node del mínimo de versiones.py, pdftoppm, swiftc y los agentes de video

Uso: python3 scripts/pruebas/ola1_mesa.py [nombre de una prueba …]
"""
import contextlib
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import types

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import versiones  # noqa: E402
import video as VD  # noqa: E402
import mesa as MS  # noqa: E402
import video_hf as VH  # noqa: E402
import youtube as YT  # noqa: E402
import youtube_hf as YH  # noqa: E402

F = []
TMP = tempfile.mkdtemp(prefix="ola1_mesa_")


def ok(cond, que):
    if not cond:
        F.append(que)


def escribir(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False))


def fuente(nombre):
    return open(os.path.join(RAIZ, "scripts", nombre), encoding="utf-8").read()


@contextlib.contextmanager
def callado():
    """Lo que el código imprime, capturado → (stdout, stderr) como StringIO."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        yield out, err


@contextlib.contextmanager
def entorno(**kw):
    antes = {k: os.environ.get(k) for k in kw}
    try:
        for k, v in kw.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@contextlib.contextmanager
def parche(obj, nombre, valor):
    antes = getattr(obj, nombre)
    setattr(obj, nombre, valor)
    try:
        yield
    finally:
        setattr(obj, nombre, antes)


# ---------- la marca del doble sin render, por formato ----------
def trabajo_montable(nombre):
    """Un TRABAJO mínimo que `video_hf.py render` y `montar` aceptan: los dos proyectos «ya armados» (1 s) y la mezcla de audio."""
    t = tempfile.mkdtemp(prefix=nombre + "_", dir=TMP)
    for Fz in VH.FORMATOS.values():
        escribir(os.path.join(t, "hf", Fz["id"], "index.html"), "<!doctype html>")
        escribir(os.path.join(t, "hf", Fz["id"], "duracion.json"), {"total_s": 1.0})
    os.makedirs(os.path.join(t, "segs_mesa"))
    VD.ff("-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-ar", "48000", os.path.join(t, "segs_mesa", "mezcla_final.wav"))
    return t


def render_de_verdad(P, args, limite, ruta_log):
    """En lugar de HyperFrames: el video del proyecto (1 s, del tamaño de su formato), como lo deja un render real."""
    Fz = next(z for z in VH.FORMATOS.values() if z["id"] == os.path.basename(P))
    VD.ff("-f", "lavfi", "-i", "color=c=0x202020:s=%dx%d:r=%d:d=1" % (Fz["w"], Fz["h"], VH.FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
          os.path.join(P, "render", "video.mp4"))
    return 0, False


def grabar(t, formato, doble):
    a = types.SimpleNamespace(trabajo=t, formato=formato, calidad="draft")
    with entorno(MESA_RENDER="0" if doble else None), parche(MS, "render_hf", render_de_verdad), callado():
        return VH.cmd_render(a)


def montar(t, formato):
    with callado() as (out, _):
        VH.cmd_montar(types.SimpleNamespace(trabajo=t, formato=formato))   # V8 falla por la sonoridad del tono: aquí no importa
    return out.getvalue()


def general(t):
    """Lo que miran los `entregar` (video.py, historia.py, explica.py, sabias.py, congreso.py)."""
    return os.path.exists(os.path.join(t, "salida", VD.MESA_SIN_RENDER))


def prueba_marca():
    # el caso del error: el 4:5 es un doble y DESPUÉS el 9:16 se graba de verdad
    t = trabajo_montable("marca")
    ok(grabar(t, "4:5", doble=True) == 0, "marca: el doble del 4:5 no se grabó")
    ok(general(t) and VH.dobles_sin_render(t) == ["4x5"], "marca: el doble del 4:5 no dejó su marca y la general (%s)" % VH.dobles_sin_render(t))
    montar(t, "4:5")
    ok(grabar(t, "9:16", doble=False) == 0, "marca: el render de verdad del 9:16 falló")
    ok(general(t), "marca: grabar el 9:16 de verdad borró la marca general con el 4:5 todavía de doble")
    sal = montar(t, "9:16")
    ok(general(t) and VH.dobles_sin_render(t) == ["4x5"], "marca: tras montar el 9:16 de verdad, el 4:5 de doble ya no está marcado (%s)" % VH.dobles_sin_render(t))
    ok("doble sin render" in sal and "4x5" in sal, "marca: `montar` no dice que el 4:5 sigue siendo un doble: %r" % sal[-200:])
    # el 4:5 se graba de verdad: hasta que no se MONTA, salida/video_4x5.mp4 sigue siendo el doble
    ok(grabar(t, "4:5", doble=False) == 0 and general(t), "marca: grabar el 4:5 de verdad sin montarlo ya dejó entregar (salida/ aún tiene el doble)")
    ok(not os.path.exists(VH.sello_doble(t, "4x5")), "marca: el render de verdad no quitó el sello de su render")
    sal = montar(t, "4:5")
    ok(not general(t) and VH.dobles_sin_render(t) == [], "marca: con los dos formatos grabados y montados de verdad la marca sigue (%s)" % VH.dobles_sin_render(t))
    ok("doble sin render" not in sal, "marca: `montar` habla de un doble cuando ya no queda ninguno")
    ok(not glob.glob(os.path.join(t, "salida", VD.MESA_SIN_RENDER + "*")), "marca: quedan marcas sueltas en salida/")
    # los dos de doble (una maqueta): la general existe y nombra los dos
    t = trabajo_montable("marca_maqueta")
    for fmt in ("9:16", "4:5"):
        grabar(t, fmt, doble=True)
        montar(t, fmt)
    ok(general(t) and VH.dobles_sin_render(t) == ["9x16", "4x5"], "marca: la maqueta con dos dobles no quedó marcada en los dos (%s)" % VH.dobles_sin_render(t))
    # una marca general de ANTES de las marcas por formato no dice de qué formato era: vale para los dos
    t = trabajo_montable("marca_vieja")
    for Fz in VH.FORMATOS.values():   # los dos renders ya hechos (dobles del código de antes: sin sello) y solo la marca general
        os.makedirs(os.path.join(t, "hf", Fz["id"], "render"))
        render_de_verdad(os.path.join(t, "hf", Fz["id"]), [], 0, "")
    escribir(os.path.join(t, "salida", VD.MESA_SIN_RENDER), "MESA_RENDER=0\n")
    grabar(t, "9:16", doble=False)
    montar(t, "9:16")
    ok(general(t) and VH.dobles_sin_render(t) == ["4x5"], "marca: una marca general vieja se borró al grabar un solo formato (%s)" % VH.dobles_sin_render(t))


# ---------- un gate sin datos avisa ----------
def pal(texto, t0=0.0, paso=0.3):
    return [{"text": w, "start": round(t0 + i * paso, 3), "end": round(t0 + i * paso + 0.25, 3)} for i, w in enumerate(texto.split())]


def trabajo_vertical(nombre, encuadre=None, datos=None, guion=None, hilo=True):
    """Un TRABAJO de la mesa vertical con dos escenas de foto; cada archivo llega como objeto (se escribe en JSON) o como texto."""
    t = tempfile.mkdtemp(prefix=nombre + "_", dir=TMP)
    escribir(os.path.join(t, "escenas.json"), {"escenas": [
        {"n": 1, "tipo": "foto", "dur": 5.0, "palabras": pal("El pleno aprobó la ley con muchos votos esa misma noche."), "eventos": [], "sfx": []},
        {"n": 2, "tipo": "foto", "dur": 5.0, "palabras": pal("Nadie esperaba ese resultado en el hemiciclo."), "eventos": [], "sfx": []}]})
    st = {"slug": nombre, "tipo": "historia", "realizacion": "mesa"}
    if hilo:
        st["hilo"] = os.path.relpath(os.path.join(t, "base"), RAIZ)
    escribir(os.path.join(t, "video.json"), st)
    escribir(os.path.join(t, "guion.json"), guion if guion is not None else {"escenas": [{"hechos": []}, {"hechos": []}]})
    escribir(os.path.join(t, "encuadre.json"), encuadre if encuadre is not None else {"protagonista": "La ley", "personajes": []})
    escribir(os.path.join(t, "base", "datos.json"), datos if datos is not None else {"cifras": [
        {"id": "c1", "veredicto": "verificada", "valor": 121, "unidad": "votos"}, {"id": "c2", "veredicto": "no_confirmada", "valor": 999, "unidad": "votos"}]})
    escribir(os.path.join(t, "base", "hilo.json"), {"tuits": [{"cifra_ids": ["c1"]}]})
    return t


PLANO = {"mesas": [{"escenas": ["e1", "e2"], "golpes": [{"tipo": "cifra", "escena": "e1", "dice": "muchos votos", "valor": "%s", "rotulo": "votos a favor"}]}]}


def plano_con(valor):
    return json.loads(json.dumps(PLANO).replace("%s", valor))


def sin_respaldo(fallas):
    return [x for x in fallas if "ni tiene respaldo en los datos" in x]


def prueba_avisos():
    # sano: sin avisos, y el respaldo trae las cifras verificadas (no la no confirmada)
    t = trabajo_vertical("sano")
    with callado() as (_, err):
        ctx = VH.contexto_v(t)
        f121, av, _ = VH.revisar_v(ctx, plano_con("121"))
        f999, _, _ = VH.revisar_v(VH.contexto_v(t), plano_con("999"))
    ok(ctx["avisos"] == [] and "sin datos" not in err.getvalue() and not any("sin datos" in x for x in av), "avisos: un TRABAJO sano avisa: %s" % ctx["avisos"])
    ok(121 in ctx["respaldo"] and 999 not in ctx["respaldo"], "avisos: el respaldo del vertical no trae las cifras verificadas: %s" % ctx["respaldo"])
    ok(not sin_respaldo(f121), "avisos: una cifra verificada que la voz no dice falla por respaldo: %s" % sin_respaldo(f121))
    ok(sin_respaldo(f999), "avisos: una cifra sin respaldo que la voz no dice pasa el gate")
    # el 16:9 no trae el respaldo resuelto: lo saca de las partes; antes quedaba SIEMPRE vacío (tuplas tomadas por números)
    ctx16 = {k: v for k, v in VH.contexto_v(t).items() if k != "respaldo"}
    with callado():
        f121, av, _ = MS.revisar(ctx16, plano_con("121"))
        f999, _, _ = MS.revisar(ctx16, plano_con("999"))
    ok(not sin_respaldo(f121) and sin_respaldo(f999), "avisos: el respaldo del 16:9 (valores_de) no respalda una cifra verificada: %s" % sin_respaldo(f121))
    ok(not any("sin datos" in x for x in av), "avisos: el 16:9 sano avisa: %s" % av)
    nums = MS.numeros_respaldo([(3.5, 1000000.0), (121.0, 1.0)])
    ok(all(x in nums for x in (3.5, 3500000.0, 121.0, 121)), "avisos: numeros_respaldo no da el valor y el valor por su factor: %s" % nums)
    # ilegibles: el elenco (encuadre.json roto) y el respaldo (datos.json roto) → AVISO con el gate y la causa, en tres sitios
    t = trabajo_vertical("roto", encuadre="{esto no es json", datos="{tampoco")
    with callado() as (out, err):
        ctx = VH.contexto_v(t)
        f, av, _ = VH.revisar_v(ctx, plano_con("121"))
    ok(ctx["elenco"] == [] and ctx["respaldo"] == [], "avisos: con los datos rotos el contexto no queda vacío de forma explícita")
    for que in ("elenco", "respaldo de las cifras"):
        en_ctx = [x for x in ctx["avisos"] if que in x]
        ok(len(en_ctx) == 1 and en_ctx[0].startswith("MV4 sin datos:") and "JSONDecodeError" in en_ctx[0],
           "avisos: %s ilegible no deja en ctx[\"avisos\"] un aviso con el gate y la causa: %s" % (que, ctx["avisos"]))
        ok(any(que in x and "sin datos" in x for x in av), "avisos: %s ilegible no sale entre los avisos del gate (plano --check): %s" % (que, av))
        ok(any(ln.startswith("AVISO MV4 sin datos:") and que in ln for ln in err.getvalue().splitlines()), "avisos: %s ilegible no sale por stderr" % que)
    ok(sin_respaldo(f), "avisos: sin respaldo legible, una cifra que la voz no dice pasó el gate")
    # el comando entero: `plano --check` imprime el AVISO (no solo la falla que no se entiende)
    escribir(os.path.join(t, "plano.json"), plano_con("121"))
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "video_hf.py"), "plano", t, "--check"], capture_output=True, text=True, cwd=RAIZ)
    ok(r.returncode == 1 and "AVISO MV4 sin datos:" in r.stdout and "elenco" in r.stdout and "respaldo de las cifras" in r.stdout,
       "avisos: `video_hf.py plano --check` no imprime los avisos de datos ilegibles (rc %s): %s" % (r.returncode, r.stdout[-400:]))
    # archivo ausente (no solo JSON roto): sin guion.json no hay hechos por escena; sin `hilo` en video.json no hay respaldo
    t = trabajo_vertical("ausente", hilo=False)
    os.remove(os.path.join(t, "guion.json"))
    with callado():
        ctx = VH.contexto_v(t)
    ok(any("guion.json" in x and "FileNotFoundError" in x for x in ctx["avisos"]), "avisos: sin guion.json no avisa de los hechos: %s" % ctx["avisos"])
    ok(any("no dice su `hilo`" in x and "KeyError" in x for x in ctx["avisos"]), "avisos: un video.json sin `hilo` no avisa del respaldo: %s" % ctx["avisos"])
    # otra forma (una lista donde iba un objeto) también es «datos ilegibles»; un error de programación NO se atrapa
    t = trabajo_vertical("forma", datos=[1, 2, 3])
    with callado():
        ctx = VH.contexto_v(t)
    ok(any("respaldo de las cifras" in x and "TypeError" in x for x in ctx["avisos"]), "avisos: un datos.json con otra forma no avisa: %s" % ctx["avisos"])
    t = trabajo_vertical("bug")

    def roto(Y):
        raise NameError("un error de programación")
    try:
        with parche(YT, "elenco_serie", roto), callado():
            VH.contexto_v(t)
        ok(False, "avisos: un error de programación (NameError) en el elenco se tragó en silencio")
    except NameError:
        pass
    # el 16:9: una parte cuyos datos no se leen queda dicha (lista para el gate, o AVISO por stderr), y revisar la vuelve aviso
    t = trabajo_vertical("roto16", datos="{no")
    Y = {"partes": [{"trabajo": os.path.relpath(t, RAIZ)}], "base": os.path.relpath(t, RAIZ)}
    malas = []
    ok(YT.valores_de(Y, malas) == [] and len(malas) == 1 and isinstance(malas[0][1], ValueError), "avisos: valores_de no devuelve la parte que no pudo leer: %s" % malas)
    with callado() as (_, err):
        YT.valores_de(Y)
    ok("AVISO" in err.getvalue() and "sin datos" in err.getvalue(), "avisos: valores_de sin lista no avisa por stderr: %r" % err.getvalue())
    with callado():
        ctx16 = {k: v for k, v in VH.contexto_v(t).items() if k not in ("respaldo", "avisos")}
        _, av, _ = MS.revisar(ctx16, plano_con("121"))
    ok(any(x.startswith("YT16 sin datos:") and "respaldo de las cifras" in x for x in av), "avisos: el 16:9 con una parte ilegible no avisa en su gate: %s" % av)
    escribir(os.path.join(t, "historia.json"), "{no")
    with callado() as (_, err):
        ok(YT.hechos_serie(Y) == {}, "avisos: hechos_serie con historia.json roto no devuelve vacío")
    ok("sin datos" in err.getvalue() and "historia.json" in err.getvalue(), "avisos: un historia.json roto no avisa: %r" % err.getvalue())
    with callado() as (_, err):
        ok(YT.hechos_serie({"base": os.path.relpath(trabajo_vertical("sin_cronologia"), RAIZ)}) == {}, "avisos: sin historia.json debe dar {}")
    ok("AVISO" not in err.getvalue(), "avisos: un flujo sin historia.json (sin cronología) no debe avisar")
    # ningún `except` desnudo ni `except Exception` vuelve a los archivos de la mesa sin que se revise aquí
    permitidos = {"mesa.py": 1, "video_hf.py": 1}   # motores_maqueta (cae al motor por defecto, más estricto) y alto_contenido (medida del marco, no un gate)
    for nombre in ("mesa.py", "video_hf.py", "youtube_hf.py", "youtube.py"):
        n = len(re.findall(r"^\s*except(\s+(Exception|BaseException))?\s*(as\s+\w+\s*)?:", fuente(nombre), re.M))
        ok(n <= permitidos.get(nombre, 0), "avisos: %s tiene %d `except` sin tipo o `except Exception` (se admiten %d): atrapa el error concreto y avisa"
           % (nombre, n, permitidos.get(nombre, 0)))


# ---------- sin red en el render ----------
def prueba_sin_red():
    P = os.path.join(TMP, "proyecto")
    etiqueta = MS.gsap_local(P)
    local = os.path.join(P, "assets", "vendor", "gsap.min.js")
    ok(os.path.exists(local) and os.path.getsize(local) == os.path.getsize(versiones.GSAP_JS), "sin_red: gsap_local no copió GSAP de design/vendor/ al proyecto")
    ok(etiqueta == '<script src="assets/vendor/gsap.min.js"></script>', "sin_red: la etiqueta de GSAP no es local: %s" % etiqueta)
    ok(os.path.exists(versiones.GSAP_JS) and os.path.isdir(versiones.THREE_DIR), "sin_red: falta lo vendorizado que fija versiones.py")
    fuera = re.compile(r"""(?:src|href)\s*=\s*["']?(?:https?:)?//|url\(\s*["']?(?:https?:)?//|@import\s+["']?(?:https?:)?//|cdn\.jsdelivr|unpkg\.com|cdnjs\.""", re.I)
    for nombre in ("mesa.py", "video_hf.py", "youtube_hf.py"):
        m = fuera.search(fuente(nombre))
        ok(not m, "sin_red: %s carga algo de fuera en lo que dibuja: «%s»" % (nombre, m.group(0) if m else ""))
    for nombre in ("video_hf.py", "youtube_hf.py"):   # los dos formatos ponen GSAP con la misma función
        ok("gsap_local(P)" in fuente(nombre), "sin_red: %s no pone GSAP con mesa.gsap_local" % nombre)
    # la plantilla del proyecto del 16:9 (el index.html que escribe youtube_hf.cmd_proyecto): su <head> ya no nombra un CDN
    src = fuente("youtube_hf.py")
    cabeza = src[src.index('<html lang="es">'):src.index("<style>", src.index('<html lang="es">'))]
    ok("http" not in cabeza and "%s" in cabeza, "sin_red: el <head> del proyecto del 16:9 no toma el <script> local: %r" % cabeza)
    ok('""" % (gsap, ' in src and "gsap = gsap_local(P)" in src, "sin_red: la plantilla del 16:9 no recibe la etiqueta de gsap_local")


# ---------- una sola versión ----------
def prueba_version():
    v = versiones.HF_VERSION
    ok(re.fullmatch(r"\d+\.\d+\.\d+", v or ""), "version: versiones.HF_VERSION no es una versión: %r" % v)
    ok(MS.HF_VERSION is versiones.HF_VERSION and VH.HF_VERSION == v and YH.HF_VERSION == v and MS.HF == versiones.HF, "version: mesa, video_hf o youtube_hf no usan la de versiones.py")
    import maqueta3d
    ok(maqueta3d.HF == versiones.HF and maqueta3d.HF[-1] == "hyperframes@" + v, "version: maqueta3d.HF no sale de versiones.py: %s" % maqueta3d.HF)
    ok(not re.search(r"^\s*(import|from)\s+(?!os\b|sys\b|argparse\b)", fuente("versiones.py").split('"""')[2], re.M),
       "version: versiones.py importa algo del proyecto (maqueta3d cargaría de más, o se cierra un ciclo)")
    r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import maqueta3d; print(int('mesa' in sys.modules or 'video' in sys.modules))"
                        % os.path.join(RAIZ, "scripts")], capture_output=True, text=True)
    ok(r.stdout.strip() == "0", "version: importar maqueta3d carga mesa.py o video.py (por la versión): %s" % (r.stdout + r.stderr)[-200:])
    rutas = glob.glob(os.path.join(RAIZ, "scripts", "*.py")) + glob.glob(os.path.join(RAIZ, "scripts", "*.sh")) + glob.glob(os.path.join(RAIZ, "scripts", "*.js")) \
        + [os.path.join(RAIZ, "Makefile")]
    for ruta in rutas:
        if os.path.basename(ruta) == "versiones.py":
            continue
        txt = open(ruta, encoding="utf-8", errors="ignore").read()
        m = re.search(r"hyperframes@\d|HF_VERSION\s*=\s*[\"']\d|" + re.escape(v), txt)
        ok(not m, "version: %s repite la versión de HyperFrames («%s»): va solo en scripts/versiones.py" % (os.path.relpath(ruta, RAIZ), m.group(0) if m else ""))
    for nombre in ("mesa.py", "video_hf.py", "youtube_hf.py", "doctor.sh"):   # GSAP y three: en los archivos de la mesa, por versiones.py
        m = re.search(r"gsap-\d|gsap@\d|three-\d", fuente(nombre))
        ok(not m, "version: %s repite una versión vendorizada («%s»): usa versiones.GSAP_JS / THREE_DIR" % (nombre, m.group(0) if m else ""))
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "scripts", "versiones.py"), "hf"], capture_output=True, text=True)
    ok(r.returncode == 0 and r.stdout.strip() == v, "version: `versiones.py hf` (lo que lee doctor.sh) no imprime la versión: %r" % r.stdout)


# ---------- el límite de tiempo del render ----------
def vivo(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def prueba_limite():
    with entorno(MESA_RENDER_LIMITE_S=None):
        ok(MS.limite_render(600) > MS.limite_render(60) > MS.limite_render(0) > 0, "limite: el límite no crece con la duración del video")
        ok(MS.limite_render(90) >= 10 * 1.6 * 90, "limite: el límite de un video de 90 s no deja ni 10 veces lo que tarda un render normal (≈ 1.6×)")
    with entorno(MESA_RENDER_LIMITE_S="7"):
        ok(MS.limite_render(600) == 7.0, "limite: MESA_RENDER_LIMITE_S no fija el límite")
    for nombre, llamada in (("video_hf.py", "MS.render_hf("), ("youtube_hf.py", "lanzar_render(")):
        src = fuente(nombre)
        ok(llamada in src and "limite_render(" in src and "texto_limite(" in src, "limite: %s no renderiza con límite y mensaje" % nombre)
        ok(not re.search(r"subprocess\.(run|Popen)\(\s*\[\s*[\"']npx", src), "limite: %s lanza npx por su cuenta (sin límite ni grupo de procesos)" % nombre)
    # un «render» que se cuelga, con un hijo: vence, se detienen los dos y el mensaje dice qué pasó y qué hacer
    P = tempfile.mkdtemp(prefix="colgado_", dir=TMP)
    pidf = os.path.join(P, "hijo.pid")
    colgado = [sys.executable, "-c", "import subprocess, sys, time\nh = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
               "open(%r, 'w').write(str(h.pid))\ntime.sleep(60)" % pidf]
    t0 = time.time()
    with parche(MS, "HF", colgado):
        rc, vencido = MS.render_hf(P, ["--workers", "1"], 1.5, os.path.join(P, "render.log"))
    ok(vencido and rc is None, "limite: un render colgado no vence (rc %s, vencido %s)" % (rc, vencido))
    ok(time.time() - t0 < 30, "limite: detener un render colgado tardó %.0f s" % (time.time() - t0))
    hijo = int(open(pidf).read()) if os.path.exists(pidf) else None
    for _ in range(20):
        if hijo and not vivo(hijo):
            break
        time.sleep(0.1)
    ok(hijo and not vivo(hijo), "limite: el proceso que lanzó el render (Chrome, ffmpeg) sigue vivo tras vencer: pid %s" % hijo)
    m = MS.texto_limite("el render 9:16", 2400.0, 90.0, os.path.join(P, "render.log"))
    ok("límite" in m and "MESA_RENDER_LIMITE_S" in m and "render.log" in m and "40:00" in m, "limite: el mensaje no dice el límite, el registro y cómo subirlo: %s" % m)
    with parche(MS, "HF", [sys.executable, "-c", "import sys; sys.exit(3)"]):
        ok(MS.render_hf(P, [], 20, os.path.join(P, "render.log")) == (3, False), "limite: un render que termina (con error) no devuelve su código")
    # el comando: `video_hf.py render` que vence sale con 1 y el mensaje, sin tocar las marcas
    t = trabajo_montable("vence")
    with parche(MS, "HF", colgado), entorno(MESA_RENDER=None, MESA_RENDER_LIMITE_S="1"), callado() as (_, err):
        rc = VH.cmd_render(types.SimpleNamespace(trabajo=t, formato="9:16", calidad="draft"))
    ok(rc == 1 and "límite" in err.getvalue() and "MESA_RENDER_LIMITE_S" in err.getvalue(), "limite: `render` vencido no falla con su mensaje (rc %s): %r" % (rc, err.getvalue()))
    # y el del 16:9 (un proceso por capítulo, en su bucle): el capítulo colgado vence, se detiene y el comando falla diciéndolo
    t = tempfile.mkdtemp(prefix="vence16_", dir=TMP)
    escribir(os.path.join(t, "escenas.json"), {"escenas": [{"n": 1, "tipo": "foto", "dur": 4.0, "origen": "P1.e1", "palabras": pal("Una sola escena.")}]})
    escribir(os.path.join(t, "youtube.json"), {"slug": "vence16", "partes": []})
    os.makedirs(os.path.join(t, "hf", "cap-1"))
    t0 = time.time()
    with parche(MS, "HF", colgado), entorno(MESA_RENDER_LIMITE_S="1"), callado() as (out, _):
        rc = YH.cmd_render(types.SimpleNamespace(trabajo=t, capitulo=None, paralelo=1, calidad="draft"))
    ok(rc == 1 and "render cap-1: FALLÓ" in out.getvalue() and "límite" in out.getvalue(), "limite: el render del 16:9 colgado no vence con su mensaje (rc %s): %r" % (rc, out.getvalue()))
    ok(time.time() - t0 < 30, "limite: el render del 16:9 tardó %.0f s en darse por vencido" % (time.time() - t0))


# ---------- las notas de /congreso ----------
def carpetas_de_notas():
    hist, cong = os.path.join(TMP, "desc", "historia"), os.path.join(TMP, "desc", "congreso")
    escribir(os.path.join(hist, "aaa.json"), {"url": "https://medio.example/nota-1", "titulo": "El titular de la nota", "medio": "Medio", "fecha": "2026-04-01"})
    escribir(os.path.join(hist, "aaa.txt"), "El cuerpo de la nota del medio.")
    escribir(os.path.join(hist, "suelto.txt"), "un texto que no es una nota\nsin url en la primera línea\n")
    escribir(os.path.join(cong, "bbb.txt"), "https://www.congreso.example/noticias/17397\nNORMATIVA PREVIENE LOS DELITOS DIGITALES\n\nEl Congreso aprobó con 121 votos el decreto.\n")
    escribir(os.path.join(cong, "ccc.txt"), "https://www.congreso.example/iniciativa/6347.pdf\n\nINICIATIVA 6347. Exposición de motivos…\n")
    escribir(os.path.join(cong, "ccc.pdf"), "%PDF-1.4 de mentira")
    return hist, cong


def prueba_notas():
    ok(any(os.path.normpath(c).endswith(os.path.join("sesiones", "_descargas", "congreso")) for c in MS.CARPETAS_NOTAS)
       and any(os.path.normpath(c).endswith(os.path.join("sesiones", "_descargas", "historia")) for c in MS.CARPETAS_NOTAS),
       "notas: notas_leidas no mira sesiones/_descargas/historia y sesiones/_descargas/congreso: %s" % (MS.CARPETAS_NOTAS,))
    hist, cong = carpetas_de_notas()
    N = MS.notas_leidas([hist, cong])
    ok(set(N) == {"https://medio.example/nota-1", "https://www.congreso.example/noticias/17397", "https://www.congreso.example/iniciativa/6347.pdf"},
       "notas: no salen las tres notas (una de historia, dos de congreso): %s" % sorted(N))
    n = N.get("https://www.congreso.example/noticias/17397") or {}
    ok(n.get("titulo") == "NORMATIVA PREVIENE LOS DELITOS DIGITALES", "notas: la nota de congreso no trae su titular: %r" % n.get("titulo"))
    ok("121 votos" in MS.texto_nota(n) if n else False, "notas: texto_nota no lee el texto de una nota de congreso")
    ok("cuerpo de la nota" in MS.texto_nota(N["https://medio.example/nota-1"]), "notas: texto_nota dejó de leer el .txt de una ficha de historia")
    ok(MS.notas_leidas([hist]).keys() == {"https://medio.example/nota-1"}, "notas: un .txt sin url en su primera línea se tomó por nota")
    with parche(MS, "CARPETAS_NOTAS", (hist, cong)):   # lo que usan los gates: la caché por defecto
        MS.notas_leidas.__dict__.pop("c", None)
        try:
            ok(MS.pdf_de("https://www.congreso.example/iniciativa/6347.pdf") == os.path.join(cong, "ccc.pdf"), "notas: pdf_de no encuentra el PDF de una iniciativa de congreso")
            ok(MS.pdf_de("https://www.congreso.example/noticias/17397") is None, "notas: pdf_de inventa un PDF para una nota sin él")
        finally:
            MS.notas_leidas.__dict__.pop("c", None)


# ---------- pagina_png avisa ----------
def prueba_pagina():
    hist, cong = carpetas_de_notas()
    t = os.path.join(TMP, "pagina")
    os.makedirs(os.path.join(t, "fotos"), exist_ok=True)
    url = "https://www.congreso.example/iniciativa/6347.pdf"
    with parche(MS, "CARPETAS_NOTAS", (hist, cong)):
        MS.notas_leidas.__dict__.pop("c", None)
        try:
            with parche(MS.shutil, "which", lambda x: None), callado() as (_, err):
                r = MS.pagina_png(t, url, 1)
            ok(r is None and "AVISO" in err.getvalue() and "pdftoppm" in err.getvalue() and "poppler" in err.getvalue(),
               "pagina: sin pdftoppm, pagina_png devuelve None sin avisar: %r" % err.getvalue())
            if shutil.which("pdftoppm"):   # con pdftoppm y un PDF que no lo es: avisa de que no sacó la página
                with callado() as (_, err):
                    r = MS.pagina_png(t, url, 2)
                ok(r is None and "AVISO" in err.getvalue() and "no sacó la página 2" in err.getvalue(), "pagina: un PDF ilegible no avisa: %r" % err.getvalue())
            with callado() as (_, err):
                ok(MS.pagina_png(t, "https://medio.example/nota-1", 1) is None and "AVISO" not in err.getvalue(), "pagina: una nota que no es PDF no debe avisar")
        finally:
            MS.notas_leidas.__dict__.pop("c", None)


# ---------- doctor.sh ----------
def prueba_doctor():
    d = fuente("doctor.sh")
    ok(subprocess.run(["bash", "-n", os.path.join(RAIZ, "scripts", "doctor.sh")]).returncode == 0, "doctor: doctor.sh no pasa `bash -n`")
    ok("versiones.py node" in d and '-ge "$NODE_MIN"' in d and versiones.NODE_MIN >= 22, "doctor: no pide el Node mínimo de versiones.py (≥ 22)")
    ok(not re.search(r"-ge 20\b", d), "doctor: sigue aceptando Node 20")
    ok("versiones.py hf" in d and "scripts/mesa.py: HF_VERSION" not in d, "doctor: no lee la versión de HyperFrames de versiones.py")
    ok(not re.search(r"hyperframes [^\n]*\(el 16:9 de /youtube-long\)", d), "doctor: sigue diciendo que HyperFrames es solo el 16:9 de /youtube-long")
    for x in ("pdftoppm", "swiftc"):
        ok(re.search(r"command -v %s\b" % x, d), "doctor: no comprueba %s" % x)
    agentes = ("video-critico video-gancho video-guionista video-animador video-realizador historia-editor historia-investigador historia-verificador "
               "historia-guionista historia-oyente explica-editor explica-investigador explica-verificador explica-guionista youtube-editor youtube-realizador").split()
    m = re.search(r'^AGV="([^"]+)"', d, re.M)
    ok(m and m.group(1).split() == agentes, "doctor: no comprueba los 16 agentes de video (video-*, historia-*, explica-*, youtube-*)")
    for a in agentes:   # lo mismo que hace doctor.sh: el archivo y su `name:`
        f = os.path.join(RAIZ, ".claude", "agents", a + ".md")
        ok(os.path.exists(f) and re.search(r"^name: %s$" % re.escape(a), "".join(open(f, encoding="utf-8").readlines()[:12]), re.M),
           "doctor: el agente %s falta en .claude/agents/ o su `name:` no es su nombre" % a)
    usa = [os.path.basename(p) for p in glob.glob(os.path.join(RAIZ, "scripts", "*.py")) if re.search(r"[\"']yt-dlp[\"']", open(p, encoding="utf-8", errors="ignore").read())]
    ok(("yt-dlp" in d) == bool(usa), "doctor: yt-dlp %s y %s" % ("se comprueba" if "yt-dlp" in d else "no se comprueba", "lo llaman %s" % usa if usa else "ningún script lo llama"))
    ok("tomas de /historia" not in d, "doctor: sigue hablando de las tomas de video (retiradas)")


PRUEBAS = {"marca": prueba_marca, "avisos": prueba_avisos, "sin_red": prueba_sin_red, "version": prueba_version, "limite": prueba_limite,
           "notas": prueba_notas, "pagina": prueba_pagina, "doctor": prueba_doctor}

if __name__ == "__main__":
    pedidas = sys.argv[1:] or list(PRUEBAS)
    if any(p not in PRUEBAS for p in pedidas):
        print("uso: ola1_mesa.py [%s]" % " ".join(PRUEBAS), file=sys.stderr)
        sys.exit(2)
    t0 = time.time()
    try:
        for p in pedidas:
            n0 = len(F)
            try:
                PRUEBAS[p]()
            except Exception as ex:   # una prueba que revienta es una falla con su causa, y las demás siguen
                import traceback
                F.append("%s: reventó: %s: %s\n%s" % (p, type(ex).__name__, ex, traceback.format_exc(limit=4)))
            print("%-8s %s" % (p, "ok" if len(F) == n0 else "%d falla(s)" % (len(F) - n0)))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    for x in F:
        print("FALLA", x)
    print("[ola 1 · mesa] %s (%.1f s)" % ("ok" if not F else "%d fallas" % len(F), time.time() - t0))
    sys.exit(1 if F else 0)
