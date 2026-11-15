#!/usr/bin/env python3
"""Pruebas de lo medido que se guarda y de la agenda que lo usa (m214, m063; sin red, sin créditos, pocos segundos).

Todo corre sobre una raíz temporal: los módulos se cargan con su RAIZ y sus rutas de registro apuntando ahí, así que no
se lee ni se escribe memoria/ ni agenda/ reales (la única prueba que lanza los scripts de verdad usa --dry-run y
comprueba que memoria/costos.json quedó como estaba).

  costo-resumen     costo.py: una corrida fabricada → la entrada de costos.json (tokens, por rol, por modelo, minutos)
  costo-slug        costo.py: la carpeta de un worktree (.claude/worktrees/x) se encuentra
  costo-entrega     costo.py: el reloj hasta la entrega (y una entrega vieja no mide nada)
  costo-cli         costo.py --registrar --dry-run por la línea de comandos: no escribe; sin --pieza o con otro flujo, exit 2
  memoria-costo     memoria.py --costo: resuelve la pieza por slug, la misma corrida reemplaza, --dry-run no escribe
  m22               validate.py M22: el registro bueno pasa; run repetido, flujo desconocido y minutos negativos fallan
  medianas          agenda.medidas: mediana con ≥ 3 mediciones, estimado con menos; video ≠ departamento; partes de serie
  plan              agenda.armar: cada orden lleva la mediana o el estimado y dice de dónde sale; agenda.md lo muestra
  ligar             memoria.py marca la agenda al registrar: uno casa → producido (y AG4 deja de fallar); dos casan → no
                    marca y avisa; ninguno → nada; otro formato → no marca; --dry-run y maqueta → nunca; parte de serie
  maqueta           la memoria congelada de `make agenda-fixture` (solo lectura): sus medianas y su costos.json, que pasa M22

Uso: python3 scripts/pruebas/resto_costos.py [prueba …] [--lista] [-v]. Exit 0 ok · 1 falla · 2 uso.
"""
import contextlib
import copy
import datetime
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import agenda as AG  # noqa: E402
import costo as CO  # noqa: E402
import memoria as MM  # noqa: E402
import validate as VL  # noqa: E402

F = []
TMP = tempfile.mkdtemp(prefix="resto_costos_")
REGISTROS_MM = {"HILOS": "hilos.json", "DATOS": "datos.json", "INFORMES": "informes.json", "VIDEOS": "videos.json",
                "HISTORIAS": "historias.json", "EXPLICACIONES": "explicaciones.json", "VIDEOS3D": "videos3d.json",
                "SABIAS": "sabias.json", "CONGRESO": "congreso.json", "CARRUSELES": "carruseles.json", "MEJORAS": "mejoras.json",
                "SERIES": "series.json", "YOUTUBE": "youtube.json", "COSTOS": "costos.json", "FUENTES": "fuentes.json"}


def ok(cond, que):
    if not cond:
        F.append(que)
    return bool(cond)


def poner(raiz, ruta, datos):
    p = os.path.join(raiz, ruta)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False)
    return p


def leer(raiz, ruta):
    with open(os.path.join(raiz, ruta), encoding="utf-8") as fh:
        return json.load(fh)


def callado(fn, *args, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        r = fn(*args, **kw)
    return r, buf.getvalue()


def raiz_nueva(nombre):
    """Una raíz vacía; memoria.py, agenda.py y validate.py pasan a trabajar ahí (nunca en el repositorio)."""
    raiz = os.path.join(TMP, nombre)
    os.makedirs(os.path.join(raiz, "memoria"))
    MM.RAIZ = AG.RAIZ = VL.RAIZ = raiz
    for const, archivo in REGISTROS_MM.items():
        setattr(MM, const, os.path.join(raiz, "memoria", archivo))
    VL.ERRORES[:], VL.AVISOS[:] = [], []
    return raiz


# ---------- una corrida de Workflow fabricada (lo que costo.py lee de ~/.claude/projects/…) ----------
def corrida(base, run="wf_prueba-001", inicio="2026-11-10T15:00:00Z", minutos=30):
    ses = os.path.join(base, "sesion-1")
    d = os.path.join(ses, "subagents", "workflows", run)
    os.makedirs(d)
    t0 = datetime.datetime.fromisoformat(inicio.replace("Z", "+00:00"))

    def hora(m):
        return (t0 + datetime.timedelta(minutes=m)).isoformat().replace("+00:00", "Z")

    def agente(aid, tipo, label, fase, modelo, m0, m1, usos):
        poner(d, "agent-%s.meta.json" % aid, {"agentType": tipo, "description": label, "workflowPhase": fase})
        with open(os.path.join(d, "agent-%s.jsonl" % aid), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "user", "timestamp": hora(m0)}) + "\n")
            for k, u in enumerate(usos):
                # un mensaje ocupa dos líneas (una por bloque) y el uso crece: se toma el máximo, no la suma
                bloques = [({"type": "text", "text": "voy"}, dict(u, output_tokens=1)),
                           ({"type": "tool_use", "name": "Bash"} if k == 0 else {"type": "text", "text": "listo"}, u)]
                for bloque, uso in bloques:
                    msg = {"id": "msg_%s_%d" % (aid, k), "model": modelo, "usage": uso, "content": [bloque]}
                    fh.write(json.dumps({"type": "assistant", "timestamp": hora(m0 + (m1 - m0) * (k + 1) / len(usos)), "message": msg}) + "\n")
    agente("a1", "historia-guionista", "guionista", "Guion", "claude-opus-5-5", 0, 20,
           [{"input_tokens": 100, "output_tokens": 2000, "cache_read_input_tokens": 50000, "cache_creation_input_tokens": 10000},
            {"input_tokens": 50, "output_tokens": 1000, "cache_read_input_tokens": 60000, "cache_creation_input_tokens": 0}])
    agente("a2", "general-purpose", "plano-2", "Plano", "claude-sonnet-5-5", 20, minutos,
           [{"input_tokens": 10, "output_tokens": 500, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 200}])
    with open(os.path.join(d, "journal.jsonl"), "w", encoding="utf-8") as fh:
        for x in ({"type": "launched"}, {"type": "failed", "agentId": ""},
                  {"type": "started", "agentId": "a1", "label": "guionista", "phase": "Guion"}, {"type": "result", "agentId": "a1"},
                  {"type": "started", "agentId": "a2", "label": "plano-2", "phase": "Plano"}, {"type": "result", "agentId": "a2"}):
            fh.write(json.dumps(x) + "\n")
    poner(ses, "workflows/%s.json" % run, {"status": "completed", "durationMs": minutos * 60000, "workflowName": "historia", "totalTokens": 1})
    return d


def t_costo_resumen():
    d = corrida(os.path.join(TMP, "proy-resumen"))
    r = CO.analizar_run(d)
    c = CO.resumen_costo(r, "la-prueba", "historia")
    ok(c["run"] == "wf_prueba-001" and c["workflow"] == "historia" and c["pieza"] == "la-prueba" and c["flujo"] == "historia",
       "resumen: run, workflow, pieza y flujo: %s" % {k: c[k] for k in ("run", "workflow", "pieza", "flujo")})
    ok(c["minutos"] == 30.0 and c["agentes"] == 2 and c["completados"] == 2 and c["fallbacks"] == 1, "resumen: minutos, agentes y fallbacks: %s" % c)
    ok(c["tokens"] == {"input": 160, "output": 3500, "cache_read": 111000, "cache_create": 10200, "total": 124860},
       "resumen: los tokens (un mensaje en dos líneas cuenta una vez) y su total: %s" % c["tokens"])
    ok(set(c["por_rol"]) == {"historia-guionista", "plano"} and c["por_rol"]["historia-guionista"] == {"agentes": 1, "tokens": 123150, "salida": 3000, "minutos": 20.0}
       and c["por_rol"]["plano"]["minutos"] == 10.0, "resumen: por rol (el genérico plano-2 → plano): %s" % c["por_rol"])
    ok(c["por_modelo"] == {"claude-opus-5-5": {"agentes": 1, "tokens": 123150, "salida": 3000}, "claude-sonnet-5-5": {"agentes": 1, "tokens": 1710, "salida": 500}},
       "resumen: por modelo: %s" % c["por_modelo"])
    ok(c["fecha"] in ("2026-11-10", "2026-11-11") and c["herramientas"] == 2 and "creditos_voz" not in c, "resumen: fecha, herramientas y sin créditos de voz: %s" % c)
    # la salida normal sigue igual de forma: la tabla por agente con su TOTAL
    _, salida = callado(CO.imprimir, r)
    ok("run wf_prueba-001 · 2 agentes (2 completados) · 1 fallback(s) · 30.0 min" in salida and "TOTAL" in salida and "guionista" in salida,
       "la tabla normal de costo.py cambió:\n%s" % salida)


def t_costo_slug():
    ok(CO.slug_proyecto("/Users/x/Desktop/repo/.claude/worktrees/mejoras-video") == "-Users-x-Desktop-repo--claude-worktrees-mejoras-video",
       "slug de un worktree: %s" % CO.slug_proyecto("/Users/x/Desktop/repo/.claude/worktrees/mejoras-video"))
    ok(CO.slug_proyecto("/Users/x/Desktop/derekurizar-x") == "-Users-x-Desktop-derekurizar-x", "slug del repositorio principal cambió")
    ok(len(CO.raices_proyecto("/Users/x/a.b/c")) == 2 and len(CO.raices_proyecto("/Users/x/ab/c")) == 1, "raices_proyecto: el slug de hoy y el de antes, sin repetir")


def t_costo_entrega():
    d = corrida(os.path.join(TMP, "proy-entrega"), inicio="2026-11-10T15:00:00Z")
    c = CO.resumen_costo(CO.analizar_run(d), "p", "historia")
    ent = os.path.join(TMP, "entrega-a")
    g = poner(ent, "guion.json", {})
    t0 = datetime.datetime(2026, 11, 10, 15, 0, tzinfo=datetime.timezone.utc).timestamp()
    os.utime(g, (t0 + 74 * 60, t0 + 74 * 60))
    ok(CO.minutos_hasta_entrega([c], ent) == 74.0, "reloj hasta la entrega: %s (va 74.0)" % CO.minutos_hasta_entrega([c], ent))
    os.utime(g, (t0 + 3 * 86400, t0 + 3 * 86400))
    ok(CO.minutos_hasta_entrega([c], ent) is None, "una entrega de tres días después no mide el reloj de la pieza")
    os.utime(g, (t0 - 600, t0 - 600))
    ok(CO.minutos_hasta_entrega([c], ent) is None, "una entrega anterior a la corrida no mide nada")
    ok(CO.minutos_hasta_entrega([c], os.path.join(TMP, "no-existe")) is None, "sin guion.json no hay reloj")


def huella(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


def t_costo_cli():
    d = corrida(os.path.join(TMP, "proy-cli"))
    real = os.path.join(RAIZ, "memoria", "costos.json")
    antes = huella(real)
    base = [sys.executable, os.path.join(RAIZ, "scripts", "costo.py")]
    r = subprocess.run(base + ["--registrar", "--pieza", "prueba-que-no-existe", "--flujo", "historia", "--run", d, "--dry-run"],
                       capture_output=True, text=True, cwd=RAIZ)
    ok(r.returncode == 0 and "[dry-run] no se escribió nada" in r.stdout and "costo wf_prueba-001 · /historia prueba-que-no-existe · 30.0 min · 2 agentes" in r.stdout
       and "no está en el registro de /historia" in r.stdout, "costo.py --registrar --dry-run: exit %d\n%s%s" % (r.returncode, r.stdout, r.stderr))
    ok(huella(real) == antes, "costo.py --registrar --dry-run tocó memoria/costos.json")
    r = subprocess.run(base + ["--registrar", "--run", d, "--dry-run"], capture_output=True, text=True, cwd=RAIZ)
    ok(r.returncode == 2 and "--pieza" in r.stderr, "--registrar sin --pieza ni --flujo: exit %d (va 2)" % r.returncode)
    r = subprocess.run(base + ["--registrar", "--pieza", "x", "--flujo", "podcast", "--run", d, "--dry-run"], capture_output=True, text=True, cwd=RAIZ)
    ok(r.returncode == 2 and "flujo 'podcast'" in r.stderr, "--registrar con un flujo desconocido: exit %d (va 2)\n%s" % (r.returncode, r.stderr))
    r = subprocess.run(base + ["--pieza", "x", "--run", d], capture_output=True, text=True, cwd=RAIZ)
    ok(r.returncode == 2, "--pieza sin --registrar: exit %d (va 2)" % r.returncode)
    r = subprocess.run(base + ["--run", d, "--json"], capture_output=True, text=True, cwd=RAIZ)
    ok(r.returncode == 0 and json.loads(r.stdout)["run"] == "wf_prueba-001" and json.loads(r.stdout)["agentes"][0]["modelo"] == "claude-opus-5-5",
       "costo.py --run DIR --json (la salida normal): exit %d" % r.returncode)
    ok(huella(real) == antes, "las pruebas de la línea de comandos tocaron memoria/costos.json")


def entrada(run, pieza, flujo="historia", minutos=30.0, **kw):
    return dict({"pieza": pieza, "flujo": flujo, "run": run, "workflow": flujo, "fecha": "2026-11-10", "inicio": "2026-11-10T15:00:00+00:00",
                 "fin": "2026-11-10T15:30:00+00:00", "minutos": minutos, "agentes": 2, "completados": 2, "fallbacks": 0,
                 "tokens": {"input": 1, "output": 2, "cache_read": 3, "cache_create": 4, "total": 10}, "herramientas": 5, "pico_alto": 0,
                 "por_rol": {}, "por_modelo": {}}, **kw)


def t_memoria_costo():
    raiz = raiz_nueva("memoria-costo")
    poner(raiz, "memoria/historias.json", {"historias": [{"id": "2026-11-09-el-puente", "slug": "el-puente", "fecha": "2026-11-09"}]})
    poner(raiz, "memoria/sabias.json", {"sabias": [{"id": "sabias-motos", "slug": "motos", "fecha": "2026-11-09"}]})
    poner(raiz, "memoria/series.json", {"series": [{"id": "2026-11-06-la-red", "slug": "la-red", "fecha": "2026-11-06", "partes": [{"n": 1}, {"n": 2}]}]})
    a = poner(raiz, "entrada/uno.json", entrada("wf_1", "el-puente"))
    rc, salida = callado(MM.registrar_costo, a)
    C = leer(raiz, "memoria/costos.json")
    ok(rc == 0 and [c["pieza"] for c in C["costos"]] == ["2026-11-09-el-puente"] and C["costos"][0]["registrado"] and C["version"] == 1,
       "--costo: el slug se resuelve al id del registro: %s\n%s" % (C["costos"], salida))
    # la misma corrida reemplaza; otra corrida de la misma pieza se suma; un lote con varias
    poner(raiz, "entrada/uno.json", entrada("wf_1", "2026-11-09-el-puente", minutos=31.5))
    poner(raiz, "entrada/lote.json", {"costos": [entrada("wf_2", "el-puente", minutos=12.0), entrada("wf_3", "motos", flujo="sabias"),
                                                entrada("wf_4", "la-red-parte-2", flujo="serie"), entrada("wf_5", "la-red", flujo="serie")]})
    rc1, s1 = callado(MM.registrar_costo, a)
    rc2, _ = callado(MM.registrar_costo, os.path.join(raiz, "entrada/lote.json"))
    C = leer(raiz, "memoria/costos.json")["costos"]
    por = {c["run"]: c for c in C}
    ok(rc1 == 0 and rc2 == 0 and len(C) == 5 and por["wf_1"]["minutos"] == 31.5 and "reemplaza" in s1, "--costo: la misma corrida reemplaza y las demás se suman: %s" % [c["run"] for c in C])
    ok(por["wf_3"]["pieza"] == "sabias-motos" and por["wf_4"]["pieza"] == "2026-11-06-la-red-parte-2" and por["wf_5"]["pieza"] == "2026-11-06-la-red",
       "--costo: ids resueltos (sabías por slug, la parte de una serie, la serie): %s" % [(c["run"], c["pieza"]) for c in C])
    # una pieza sin registrar se guarda con aviso; --dry-run no escribe; lo inválido sale con 2 sin escribir
    antes = huella(os.path.join(raiz, "memoria/costos.json"))
    rc, salida = callado(MM.registrar_costo, poner(raiz, "entrada/seco.json", entrada("wf_9", "no-existe")), True)
    ok(rc == 0 and "no está en el registro de /historia" in salida and "[dry-run]" in salida and huella(os.path.join(raiz, "memoria/costos.json")) == antes,
       "--costo --dry-run escribió o no avisó:\n%s" % salida)
    for nombre, mala in (("flujo", entrada("wf_8", "el-puente", flujo="podcast")), ("minutos", entrada("wf_8", "el-puente", minutos=-1)),
                         ("sin run", entrada("", "el-puente")), ("tokens", dict(entrada("wf_8", "el-puente"), tokens={}))):
        rc, _ = callado(MM.registrar_costo, poner(raiz, "entrada/mala.json", mala))
        ok(rc == 2 and huella(os.path.join(raiz, "memoria/costos.json")) == antes, "--costo aceptó una entrada inválida (%s): exit %s" % (nombre, rc))
    rc, _ = callado(MM.registrar_costo, poner(raiz, "entrada/lista.json", [1, 2]))
    ok(rc == 2, "--costo aceptó un archivo que no es una entrada")


def t_m22():
    raiz = raiz_nueva("m22")
    poner(raiz, "memoria/historias.json", {"historias": [{"id": "2026-11-09-el-puente", "slug": "el-puente", "fecha": "2026-11-09"}]})
    buenas = [entrada("wf_1", "2026-11-09-el-puente"), entrada("wf_2", "2026-11-09-el-puente", minutos_pieza=70.0, entrega="historias/2026-11-09-el-puente")]

    def m22(costos):
        poner(raiz, "memoria/costos.json", {"version": 1, "costos": costos})
        VL.ERRORES[:], VL.AVISOS[:] = [], []
        VL.validar_costos()
        return list(VL.ERRORES), list(VL.AVISOS)
    e, a = m22(buenas)
    ok(e == [] and a == [], "M22 rechaza un registro bueno: %s %s" % (e, a))
    for que, mutar in (("run repetido", lambda c: c.append(dict(c[0]))), ("flujo 'podcast'", lambda c: c[0].update(flujo="podcast")),
                       ("minutos (≥ 0)", lambda c: c[0].update(minutos=-3)), ("sin pieza", lambda c: c[0].update(pieza="")),
                       ("fecha", lambda c: c[1].update(fecha="10/11/2026")), ("minutos_pieza", lambda c: c[1].update(minutos_pieza=0)),
                       ("relativa a la raíz", lambda c: c[1].update(entrega="/tmp/x")), ("tokens.total", lambda c: c[0].update(tokens={"total": "mucho"}))):
        c = copy.deepcopy(buenas)
        mutar(c)
        e, _ = m22(c)
        ok(any(x.startswith("M22 ") and que in x for x in e), "M22 no muerde «%s»: %s" % (que, e))
    e, a = m22([entrada("wf_1", "pieza-fantasma")])
    ok(e == [] and any("pieza-fantasma no está en el registro" in x for x in a), "M22: una pieza sin registrar es aviso, no error: %s %s" % (e, a))
    os.remove(os.path.join(raiz, "memoria/costos.json"))
    VL.ERRORES[:], VL.AVISOS[:] = [], []
    VL.validar_costos()
    ok(VL.ERRORES == [], "M22: sin costos.json no hay error")


def memoria_medida(raiz):
    """Registros de juguete: 3 historias (mediana 2500), 2 sabías, 4 videos (3 de hilo + 1 departamento + 1 corte), una serie."""
    m = os.path.join(raiz, "memoria")
    poner(m, "historias.json", {"historias": [
        {"id": "2026-11-01-a", "slug": "a", "tema": "El puente de Belice", "fecha": "2026-11-01", "ruta": "historias/2026-11-01-a", "estado": "listo", "creditos_voz": 2400.0},
        {"id": "2026-11-02-b", "slug": "b", "tema": "La cervecería del siglo", "fecha": "2026-11-02", "ruta": "historias/2026-11-02-b", "estado": "listo", "creditos_voz": 2500},
        {"id": "2026-11-03-c", "slug": "c", "tema": "El ferrocarril verde", "fecha": "2026-11-03", "ruta": "historias/2026-11-03-c", "estado": "listo", "creditos_voz": 9000.0},
        {"id": "2026-11-03-d", "slug": "d", "tema": "Voz falsa", "fecha": "2026-11-03", "ruta": "historias/2026-11-03-d", "estado": "incompleto", "creditos_voz": None}]})
    poner(m, "sabias.json", {"sabias": [{"id": "sabias-x", "slug": "x", "fecha": "2026-11-01", "ruta": "datos/x/video", "estado": "listo", "creditos_voz": 300},
                                        {"id": "sabias-y", "slug": "y", "fecha": "2026-11-02", "ruta": "datos/y/video", "estado": "listo", "creditos_voz": 500}]})
    poner(m, "videos.json", {"videos": [
        {"id": "v1", "slug": "v1", "fecha": "2026-10-01", "ruta_video": "hilos/v1/video", "estado": "listo", "creditos_voz": 1000},
        {"id": "v2", "slug": "v2", "fecha": "2026-10-02", "ruta_video": "hilos/v2/video", "estado": "listo", "creditos_voz": 2000},
        {"id": "v3", "slug": "v3", "fecha": "2026-10-03", "ruta_video": "hilos/v3/video", "estado": "listo", "creditos_voz": 3000},
        {"id": "v3-corto", "slug": "v3", "variante": "corto", "fecha": "2026-10-03", "ruta_video": "hilos/v3/video-corto", "estado": "listo", "creditos_voz": 50},
        {"id": "v4", "slug": "v4", "serie": "departamentos", "fecha": "2026-10-04", "ruta_video": "hilos/v4/video", "estado": "listo", "creditos_voz": 900}]})
    poner(m, "series.json", {"series": [{"id": "2026-11-06-la-red", "slug": "la-red", "fecha": "2026-11-06", "partes": [
        {"n": 1, "estado": "entregada", "ruta": "series/2026-11-06-la-red/parte-1", "creditos_voz": 2100},
        {"n": 2, "estado": "entregada", "ruta": "series/2026-11-06-la-red/parte-2"},          # registrada antes: lo dice su guion.json
        {"n": 3, "estado": "entregada", "ruta": "series/2026-11-06-la-red/parte-3", "creditos_voz": 2300},
        {"n": 4, "estado": "guion"}]}]})
    poner(raiz, "series/2026-11-06-la-red/parte-2/guion.json", {"creditos_voz": 2200.5})
    poner(m, "costos.json", {"costos": [
        entrada("wf_a1", "2026-11-01-a", minutos=10.0), entrada("wf_a2", "2026-11-01-a", minutos=20.0),            # 30 (suma de corridas)
        entrada("wf_b1", "2026-11-02-b", minutos=12.0, minutos_pieza=50.0), entrada("wf_b2", "2026-11-02-b", minutos=8.0, minutos_pieza=41.0),   # 50 (el reloj)
        entrada("wf_c1", "2026-11-03-c", minutos=40.0),                                                                # 40
        entrada("wf_s1", "2026-11-06-la-red", flujo="serie", minutos=90.0),                                            # la investigación compartida no cuenta
        entrada("wf_s2", "2026-11-06-la-red-parte-1", flujo="serie", minutos=25.0), entrada("wf_s3", "2026-11-06-la-red-parte-2", flujo="serie", minutos=35.0),
        entrada("wf_h1", "un-hilo", flujo="hilo", minutos=23.0), entrada("wf_x1", "sabias-x", flujo="sabias", minutos=5.0),
        entrada("wf_k1", "congreso-1", flujo="congreso", minutos=9.0, minutos_pieza=20.0), entrada("wf_k2", "congreso-2", flujo="congreso", minutos=9.0, minutos_pieza=40.0),
        entrada("wf_k3", "congreso-3", flujo="congreso", minutos=9.0, minutos_pieza=30.0)]})   # las tres con el reloj hasta la entrega
    return m


def t_medianas():
    raiz = raiz_nueva("medianas")
    m = memoria_medida(raiz)
    M = AG.medidas(m)
    ok(M["historia"]["creditos"] == (2500, "mediana de 3") and M["historia"]["n"] == {"minutos": 3, "creditos": 3},
       "historia: la mediana de 3 créditos (un atípico de 9,000 no la mueve; sin número no cuenta): %s" % M["historia"])
    ok(M["historia"]["minutos"] == (40, "mediana de 3, 2 solo agentes"), "historia: minutos = mediana de [30 suma, 50 reloj, 40 suma]: %s" % (M["historia"]["minutos"],))
    ok(M["congreso"]["minutos"] == (30, "mediana de 3") and M["congreso"]["creditos"][1] == "estimado", "congreso: tres piezas con el reloj hasta la entrega: %s" % M["congreso"])
    ok(M["sabias"]["creditos"] == (AG.FORMATOS["sabias"][3], "estimado") and M["sabias"]["minutos"] == (AG.FORMATOS["sabias"][2], "estimado")
       and M["sabias"]["n"] == {"minutos": 1, "creditos": 2}, "sabías: con 2 mediciones manda el estimado fijo: %s" % M["sabias"])
    ok(M["video"]["creditos"] == (2000, "mediana de 3") and M["departamento"]["creditos"] == (AG.FORMATOS["departamento"][3], "estimado")
       and M["departamento"]["n"]["creditos"] == 1, "video y departamento van aparte y el corte A/B no cuenta: %s · %s" % (M["video"], M["departamento"]))
    ok(M["serie"]["creditos"] == (2200, "mediana de 3") and M["serie"]["minutos"] == (AG.FORMATOS["serie"][2], "estimado") and M["serie"]["n"]["minutos"] == 2,
       "serie: créditos de las partes (registro o guion.json) y minutos solo de las partes: %s" % M["serie"])
    ok(M["explica"]["creditos"] == (AG.FORMATOS["explica"][3], "estimado") and M["explica"]["n"] == {"minutos": 0, "creditos": 0}, "explica sin registro: estimado: %s" % M["explica"])
    # la tercera parte medida completa la mediana de minutos de la serie
    C = leer(raiz, "memoria/costos.json")
    C["costos"].append(entrada("wf_s4", "2026-11-06-la-red-parte-3", flujo="serie", minutos=45.0))
    poner(raiz, "memoria/costos.json", C)
    ok(AG.medidas(m)["serie"]["minutos"] == (35, "mediana de 3, solo agentes"), "serie con 3 partes medidas: %s" % (AG.medidas(m)["serie"]["minutos"],))
    rc, salida = callado(AG.cmd_medidas, type("A", (), {"memoria": m})())
    ok(rc == 0 and "2,500 (mediana de 3; fijo 2,200)" in salida and "400 (estimado; 2 de 3)" in salida, "agenda.py medidas:\n%s" % salida)


def t_plan():
    raiz = raiz_nueva("plan")
    m = memoria_medida(raiz)
    for archivo, clave, listo in (("historias.json", "historias", "2026-11-01-a"), ("sabias.json", "sabias", "sabias-x"), ("videos.json", "videos", None)):
        R = leer(m, archivo)   # una historia y un «¿Sabías que…?» quedan listos para publicar; lo demás cuenta para la mediana y no se programa
        for v in R[clave]:
            v["estado"] = "listo" if v["id"] == listo else "incompleto"
        poner(m, archivo, R)
    cal, dep = AG.calendario_en, AG.departamento_siguiente
    AG.calendario_en, AG.departamento_siguiente = (lambda *a: []), (lambda: None)   # la semana, sin el calendario ni la serie de los 22
    try:
        A = AG.armar(datetime.date(2026, 11, 16), m)
    finally:
        AG.calendario_en, AG.departamento_siguiente = cal, dep
    ordenes = [s for s in A["espacios"] if AG.es_orden(s)]
    H = [s for s in ordenes if s["formato"] == "historia"]
    S = [s for s in ordenes if s["formato"] == "sabias"]
    ok(H and all(s["creditos"] == 2500 and s["minutos"] == 40 and s["origen"] == {"minutos": "mediana de 3, 2 solo agentes", "creditos": "mediana de 3"} for s in H),
       "las órdenes de historia no llevan la mediana medida: %s" % [(s["id"], s["minutos"], s["creditos"], s.get("origen")) for s in H])
    ok(S and all(s["creditos"] == AG.FORMATOS["sabias"][3] and s["origen"] == {"minutos": "estimado", "creditos": "estimado"} for s in S),
       "las órdenes de sabías no llevan el estimado: %s" % [(s["id"], s["creditos"], s.get("origen")) for s in S])
    P = [s for s in A["espacios"] if not AG.es_orden(s)]
    ok(P and all("origen" not in s and s["creditos"] == 0 for s in P), "lo ya producido no lleva estimado: %s" % [(s["id"], s.get("origen")) for s in P])
    ok(AG.revisar(A, m) == [], "el plan con medianas no pasa AG1–AG9: %s" % AG.revisar(A, m))
    d = os.path.join(raiz, "agenda", A["semana"])
    AG.guardar(d, A)
    md = open(os.path.join(d, "agenda.md"), encoding="utf-8").read()
    total = sum(s["creditos"] for s in ordenes)
    ok("~40 min (mediana de 3, 2 solo agentes)" in md and "2,500 (mediana de 3)" in md and "%s (estimado)" % AG.FORMATOS["sabias"][3] in md
       and "≈ %s (%d de %d órdenes con la mediana medida" % ("{:,}".format(total), sum(s["origen"]["creditos"] != "estimado" for s in ordenes), len(ordenes)) in md,
       "agenda.md no dice de dónde sale cada número:\n%s" % md)
    ok("(mediana de 3)" in open(os.path.join(d, "agenda.html"), encoding="utf-8").read(), "agenda.html no muestra el origen")
    # cambiar el formato de un espacio cambia sus números por los del formato nuevo
    s = copy.deepcopy(next(x for x in ordenes if x["formato"] == "sabias"))
    AG.fijar_tema(s, "Una ley del Congreso", "congreso", AG.medidas(m))
    ok(s["creditos"] == AG.FORMATOS["congreso"][3] and s["minutos"] == 30 and s["origen"] == {"minutos": "mediana de 3", "creditos": "estimado"}, "fijar_tema con otro formato: %s" % s)
    s = copy.deepcopy(H[0])
    AG.fijar_tema(s, "Un tema de video", "video", AG.medidas(m))
    ok(s["creditos"] == 2000 and s["origen"] == {"minutos": "estimado", "creditos": "mediana de 3"}, "fijar_tema a video: la mediana de video: %s" % s)
    # una agenda de antes (sin `origen`) se sigue escribiendo
    for x in A["espacios"]:
        x.pop("origen", None)
    AG.guardar(d, A)
    ok("(estimado)" in open(os.path.join(d, "agenda.md"), encoding="utf-8").read(), "una agenda sin `origen` no se escribe")


# ---------- m063: memoria.py marca la agenda al registrar ----------
HOY = datetime.date.today()


def agenda_de_prueba(raiz, temas, hasta=None):
    """Una agenda sin terminar con un espacio por tema: [(slot, formato, tema)] en días seguidos desde hoy."""
    esp = []
    for k, (slot, formato, tema) in enumerate(temas):
        s = AG.espacio(HOY + datetime.timedelta(days=k), slot, formato)
        AG.fijar_tema(s, tema)
        esp.append(s)
    AG.asignar_estilos_facebook(esp)
    A = {"version": 2, "semana": AG.semana_iso(HOY), "desde": HOY.isoformat(), "hasta": (hasta or HOY + datetime.timedelta(days=6)).isoformat(),
         "generado": HOY.isoformat(), "espacios": esp, "omitidas": [], "pospuestas": [], "incompletas": []}
    d = os.path.join(raiz, "agenda", A["semana"])
    AG.guardar(d, A)
    return d


def entrega_historia(raiz, slug, tema, carpeta=None, **extra):
    ruta = carpeta or "historias/%s-%s" % (HOY.isoformat(), slug)
    poner(raiz, ruta + "/guion.json", dict({"tipo": "historia", "id": "%s-%s" % (HOY.isoformat(), slug), "slug": slug, "tema": tema, "fecha": HOY.isoformat(),
                                             "paleta": "tierra", "musica": "tierra-1", "duracion_s": 150.0, "creditos_voz": 2500.0,
                                             "escenas": [{"voz": "Una ciudad salió de la selva."}], "cierre": {"final": "Y sigue ahí."}}, **extra))
    return ruta


def espacios(d):
    return {s["id"]: s for s in leer(d, "agenda.json")["espacios"]}


def t_ligar():
    # 1) un espacio casa: queda producido con su ruta y AG4 deja de fallar
    raiz = raiz_nueva("ligar-uno")
    d = agenda_de_prueba(raiz, [("A", "historia", "Tikal: cómo la ciudad maya salió de la selva"), ("B", "sabias", "El precio del maíz en octubre"),
                                ("A", "historia", "El zoológico La Aurora")])
    ruta = entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva")
    sid = "%s-A" % HOY.isoformat()
    # el control: registrada la pieza y sin marcar el espacio, AG4 falla (es lo que m063 arregla)
    real_marcar, MM.marcar_agenda = MM.marcar_agenda, lambda *a, **k: None
    try:
        rc, _ = callado(MM.registrar_historia, ruta, "listo")
    finally:
        MM.marcar_agenda = real_marcar
    A = leer(d, "agenda.json")
    ok(rc == 0 and any(x.startswith("AG4 %s" % sid) for x in AG.revisar(A, os.path.join(raiz, "memoria"))),
       "control: sin marcar la agenda, AG4 debería fallar por el tema repetido: %s" % AG.revisar(A, os.path.join(raiz, "memoria")))
    rc, salida = callado(MM.registrar_historia, ruta, "listo")
    E = espacios(d)
    ok(rc == 0 and E[sid]["estado"] == "producido" and E[sid]["pieza"] == {"flujo": "historia", "id": "%s-tikal-la-ciudad-maya" % HOY.isoformat(), "ruta": ruta}
       and "agenda %s: %s queda producido" % (AG.semana_iso(HOY), sid) in salida, "registrar la historia no marcó su espacio: %s\n%s" % (E[sid], salida))
    ok(sum(s["estado"] == "producido" for s in E.values()) == 1, "se marcó más de un espacio: %s" % [(k, s["estado"]) for k, s in E.items()])
    ok(AG.revisar(leer(d, "agenda.json"), os.path.join(raiz, "memoria")) == [], "tras marcar, la agenda no pasa: %s" % AG.revisar(leer(d, "agenda.json"), os.path.join(raiz, "memoria")))
    ok("producido" in open(os.path.join(d, "agenda.md"), encoding="utf-8").read(), "agenda.md no se rehízo al marcar")
    # volver a registrar la misma pieza no toca nada más
    antes = huella(os.path.join(d, "agenda.json"))
    rc, salida = callado(MM.registrar_historia, ruta, "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes and "agenda" not in salida.replace("memoria/", ""), "registrar otra vez volvió a tocar la agenda:\n%s" % salida)

    # 2) --dry-run y las maquetas nunca tocan la agenda (ni el registro, en dry-run)
    raiz = raiz_nueva("ligar-seco")
    d = agenda_de_prueba(raiz, [("A", "historia", "Tikal: cómo la ciudad maya salió de la selva")])
    antes = huella(os.path.join(d, "agenda.json"))
    ruta = entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva")
    rc, _ = callado(MM.registrar_historia, ruta, "listo", True)
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes and not os.path.exists(os.path.join(raiz, "memoria/historias.json")), "--dry-run tocó la agenda o el registro")
    maqueta = entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva", carpeta="sesiones/_fixture_historia/salida")
    rc, salida = callado(MM.registrar_historia, maqueta, "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes, "una entrega de maqueta (sesiones/…) marcó la agenda:\n%s" % salida)
    marcada = entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva", fixture=True)
    rc, salida = callado(MM.registrar_historia, marcada, "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes, "una entrega con «fixture» en su guion marcó la agenda:\n%s" % salida)

    # 3) dos espacios casan: no marca ninguno y avisa
    raiz = raiz_nueva("ligar-dos")
    d = agenda_de_prueba(raiz, [("A", "historia", "Tikal: cómo la ciudad maya salió de la selva"), ("A", "historia", "La ciudad maya de Tikal y su selva")])
    antes = huella(os.path.join(d, "agenda.json"))
    rc, salida = callado(MM.registrar_historia, entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva"), "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes and "AVISO agenda: 2 espacios casan" in salida and "agenda.py producido SLOT --ruta" in salida,
       "con dos espacios que casan debía avisar sin marcar:\n%s" % salida)

    # 4) ninguno casa: nada; otro formato: no marca y avisa; una agenda ya terminada o de maqueta no se toca
    raiz = raiz_nueva("ligar-nada")
    d = agenda_de_prueba(raiz, [("A", "historia", "El zoológico La Aurora"), ("A", "explica", "Tikal: cómo la ciudad maya salió de la selva")])
    antes = huella(os.path.join(d, "agenda.json"))
    rc, salida = callado(MM.registrar_historia, entrega_historia(raiz, "el-ferrocarril-verde", "El ferrocarril verde de Los Altos"), "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes and "agenda" not in salida.replace("memoria/", ""), "sin espacio que case debía callar:\n%s" % salida)
    rc, salida = callado(MM.registrar_historia, entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva"), "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes and "casa por tema pero su formato no es de /historia" in salida,
       "un espacio de otro formato no debía marcarse:\n%s" % salida)
    raiz = raiz_nueva("ligar-vieja")
    d = agenda_de_prueba(raiz, [("A", "historia", "Tikal: cómo la ciudad maya salió de la selva")], hasta=HOY - datetime.timedelta(days=1))
    antes = huella(os.path.join(d, "agenda.json"))
    ruta = entrega_historia(raiz, "tikal-la-ciudad-maya", "Tikal, la ciudad maya que salió de la selva")
    rc, _ = callado(MM.registrar_historia, ruta, "listo")
    ok(rc == 0 and huella(os.path.join(d, "agenda.json")) == antes, "una agenda que ya terminó no se toca")
    A = leer(d, "agenda.json")
    A.update(hasta=(HOY + datetime.timedelta(days=3)).isoformat(), memoria="sesiones/_fixture_agenda/memoria")
    poner(d, "agenda.json", A)
    antes = huella(os.path.join(d, "agenda.json"))
    r = AG.ligar_pieza("historia", "%s-tikal-la-ciudad-maya" % HOY.isoformat(), ruta, tema="Tikal, la ciudad maya que salió de la selva", slug="tikal-la-ciudad-maya")
    ok(r["estado"] == "nada" and huella(os.path.join(d, "agenda.json")) == antes, "una agenda armada sobre otros registros (maqueta) no se toca: %s" % r)

    # 5) sabías y la parte de una serie (por el id del espacio; «Parte N» solo casa con esa parte)
    raiz = raiz_nueva("ligar-otros")
    d = agenda_de_prueba(raiz, [("B", "sabias", "Las remesas de julio fueron el mes más alto"), ("A", "serie", "La red de aduanas · Parte 3"),
                                ("A", "historia", "El zoológico La Aurora")])
    poner(raiz, "datos/2026-11-10-remesas-julio-record/video/guion.json", {
        "tipo": "sabias", "id": "sabias-remesas-julio-record", "slug": "remesas-julio-record", "tema": "Remesas de julio: el mes más alto", "fecha": HOY.isoformat(),
        "paleta": "tierra", "musica": "tierra-1", "duracion_s": 27.0, "creditos_voz": 410, "escenas": [{"voz": "¿Sabías que…?"}]})
    rc, salida = callado(MM.registrar_sabias, "datos/2026-11-10-remesas-julio-record/video", "listo")
    E = espacios(d)
    ok(rc == 0 and E["%s-B" % HOY.isoformat()]["estado"] == "producido" and E["%s-B" % HOY.isoformat()]["pieza"]["flujo"] == "sabias",
       "registrar un «¿Sabías que…?» no marcó su espacio:\n%s" % salida)
    serie = "series/2026-11-06-la-red-de-aduanas"
    S = {"slug": "la-red-de-aduanas", "tema": "La red de aduanas", "motor": "historia", "fecha": "2026-11-06", "estado": "en curso", "partes": [
        {"n": 1, "titulo": "Las escuchas", "estado": "entregada", "ruta": serie + "/parte-1", "duracion_s": 140.0},
        {"n": 2, "titulo": "La caída", "estado": "entregada", "ruta": serie + "/parte-2", "duracion_s": 141.0},
        {"n": 3, "titulo": "El juicio", "estado": "guion"}]}
    for k in (1, 2):
        poner(raiz, "%s/parte-%d/guion.json" % (serie, k), {"musica": "tierra-1", "creditos_voz": 2000 + k, "escenas": [{"voz": "Parte."}]})
    poner(raiz, serie + "/serie.json", S)
    sid = "%s-A" % (HOY + datetime.timedelta(days=1)).isoformat()
    rc, salida = callado(MM.registrar_serie, serie)
    reg = leer(raiz, "memoria/series.json")["series"][0]
    ok(rc == 0 and espacios(d)[sid]["estado"] == "tema" and [p.get("creditos_voz") for p in reg["partes"]] == [2001, 2002, None],
       "las partes 1 y 2 no casan con el espacio «Parte 3» (y el registro guarda sus créditos): %s\n%s" % (espacios(d)[sid]["estado"], salida))
    S["partes"][2].update(estado="entregada", ruta=serie + "/parte-3", duracion_s=150.0)
    poner(raiz, serie + "/parte-3/guion.json", {"musica": "tierra-1", "creditos_voz": 2003, "escenas": [{"voz": "Parte."}]})
    poner(raiz, serie + "/serie.json", S)
    rc, salida = callado(MM.registrar_serie, serie)
    E = espacios(d)
    ok(rc == 0 and E[sid]["estado"] == "producido" and E[sid]["pieza"] == {"flujo": "serie", "id": "la-red-de-aduanas-parte-3", "ruta": serie + "/parte-3"}
       and salida.count("queda producido") == 1, "la parte 3 recién entregada no marcó su espacio (o lo marcó otra): %s\n%s" % (E[sid], salida))
    # un espacio que ya lleva la parte por id (el que arma `plan`) casa sin mirar el tema
    A = leer(d, "agenda.json")
    x = next(s for s in A["espacios"] if s["formato"] == "historia")
    x.update(formato="serie", tema="otra cosa", pieza={"flujo": "serie", "id": "la-red-de-aduanas-parte-9", "ruta": None})
    poner(d, "agenda.json", A)
    r = AG.ligar_pieza("serie", "la-red-de-aduanas-parte-9", serie + "/parte-9", tema="La red de aduanas", slug="la-red-de-aduanas", parte=9)
    ok(r["estado"] == "marcado" and espacios(d)[x["id"]]["pieza"]["ruta"] == serie + "/parte-9", "un espacio con la pieza por id no se ligó: %s" % r)
    ok(AG.ligar_pieza("serie", "la-red-de-aduanas-parte-9", serie + "/parte-9", parte=9)["estado"] == "ya", "ligar dos veces la misma pieza debe decir «ya»")


def t_maqueta():
    """La memoria congelada de `make agenda-fixture` trae los costos de las corridas reales de sus historias y videos."""
    m = os.path.join(RAIZ, "sesiones", "_fixture_agenda", "memoria")
    M = AG.medidas(m)
    ok(M["historia"]["minutos"] == (65, "mediana de 11, solo agentes") and M["historia"]["creditos"] == (2567, "mediana de 11"),
       "la maqueta de /agenda: historia: %s" % M["historia"])
    ok(M["video"]["minutos"] == (21, "mediana de 6, solo agentes") and M["video"]["creditos"] == (1838, "mediana de 6"), "la maqueta de /agenda: video: %s" % M["video"])
    ok(M["sabias"]["creditos"][1] == "estimado" and M["explica"]["minutos"][1] == "estimado", "la maqueta de /agenda: sabías y explica van con el estimado")
    raiz = raiz_nueva("maqueta")   # su costos.json tiene la forma del real: pasa M22 con sus registros
    for f in ("costos.json", "historias.json", "videos.json"):
        shutil.copy(os.path.join(m, f), os.path.join(raiz, "memoria", f))
    VL.validar_costos()
    ok(VL.ERRORES == [] and VL.AVISOS == [], "el costos.json de la maqueta no pasa M22: %s %s" % (VL.ERRORES, VL.AVISOS))


PRUEBAS = {"costo-resumen": t_costo_resumen, "costo-slug": t_costo_slug, "costo-entrega": t_costo_entrega, "costo-cli": t_costo_cli,
           "memoria-costo": t_memoria_costo, "m22": t_m22, "medianas": t_medianas, "plan": t_plan, "ligar": t_ligar, "maqueta": t_maqueta}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--lista" in sys.argv:
        print("\n".join(PRUEBAS))
        return 0
    desconocidas = [a for a in args if a not in PRUEBAS]
    if desconocidas or any(a not in ("--lista", "-v") for a in sys.argv[1:] if a.startswith("-")):
        print("uso: resto_costos.py [%s] [--lista] [-v]" % " | ".join(PRUEBAS), file=sys.stderr)
        return 2
    try:
        for nombre in args or list(PRUEBAS):
            n = len(F)
            try:
                PRUEBAS[nombre]()
            except Exception as e:  # noqa: BLE001  (una prueba que revienta es una falla, no un traceback suelto)
                F.append("%s reventó: %s: %s" % (nombre, type(e).__name__, e))
            if "-v" in sys.argv:
                print("%-14s %s" % (nombre, "ok" if len(F) == n else "%d falla(s)" % (len(F) - n)))
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    for x in F:
        print("FALLA", x)
    print("[resto · costos y agenda] %s" % ("ok" if not F else "%d fallas" % len(F)))
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
