#!/usr/bin/env python3
"""Costo de una corrida de Workflow (/hilo, /historia, /video, plano…): tokens, herramientas y duración por agente.

Localiza ~/.claude/projects/<slug del cwd>/<sesión>/subagents/workflows/<run>/ (el
slug es la ruta absoluta del proyecto con todo lo que no es letra ni dígito → «-»:
un worktree en .claude/worktrees/ también se encuentra; se buscan todas las sesiones)
y lee:
  journal.jsonl   líneas started (agentId, label, phase), failed (fallback) y result
  agent-*.jsonl   mensajes assistant con message.usage (input, output, cache_read,
                  cache_creation), bloques tool_use y timestamps
  *.meta.json     descripción/fase del agente
  ../../../workflows/<run>.json   resumen del runner (status, durationMs, totalTokens…)

Un mensaje del modelo ocupa varias líneas (una por bloque); el uso se toma como el
máximo por message.id, así output_tokens no se cuenta dos veces ni se queda corto.

Imprime tabla por agente (label, turnos, tool_use por nombre abreviado, tokens,
duración) y totales; señala failed (fallbacks) y agentes con contexto pico > 150 K.
--json vuelca el mismo resumen (con varios --run, una lista).

--registrar: lo medido se guarda (m214). Arma el resumen de cada corrida y se lo pasa a
`scripts/memoria.py --costo ARCHIVO` (el único que escribe memoria/costos.json; este script no
escribe en memoria/). Va al cerrar cada pieza, después de registrarla con memoria.py:

  python3 scripts/costo.py --registrar --pieza <id o slug> --flujo <flujo> [--run wf_a wf_b … | --ultimo]
                           [--entrega <carpeta de entrega>] [--dry-run]

  --pieza    el id o el slug de la pieza (memoria.py lo resuelve contra el registro de su flujo); la parte de una
             serie es <serie>-parte-N y la investigación compartida de la serie, el id de la serie
  --flujo    hilo | dato | investigacion | ideas | video | departamento | historia | explica | sabias | congreso |
             video3d | serie | youtube | carrusel (memoria.FLUJOS_COSTO)
  --run      una o varias corridas de la pieza (el Workflow del guion, sus reanudaciones, el «Plano»…); sin --run, la última
  --entrega  la carpeta entregada: con su guion.json mide `minutos_pieza`, el reloj desde que arrancó la primera
             corrida hasta la entrega (incluye voz, render y esperas; se omite si no cae entre 0 y 24 h). Pásala
             siempre: sin ella la agenda solo sabe cuánto tardaron los agentes («solo agentes» en sus órdenes)
  --dry-run  imprime lo que guardaría y no escribe nada

Cada corrida es una entrada de memoria/costos.json → costos[] (registrar la misma corrida reemplaza):
  {pieza, flujo, run, workflow, fecha, inicio, fin, minutos (reloj de la corrida), agentes, completados, fallbacks,
   tokens {input, output, cache_read, cache_create, total}, herramientas, pico_alto,
   por_rol {<rol>: {agentes, tokens, salida, minutos}}, por_modelo {<modelo>: {agentes, tokens, salida}},
   entrega?, minutos_pieza?, registrado}
(rol = el tipo de agente; en un agente genérico, su etiqueta sin el número: plano-3 → plano). Los créditos de voz NO
van aquí: ya están en el registro de cada pieza como `creditos_voz`. `scripts/agenda.py` lee las dos cosas para que
cada orden de producción lleve la mediana medida de su flujo (con ≥ 3 mediciones) y no el estimado fijo.

Uso: python3 scripts/costo.py [--run wf_xxx … | --ultimo] [--json] [--proyecto DIR] [--listar]
     python3 scripts/costo.py --registrar --pieza P --flujo F [--run wf_xxx … | --ultimo] [--entrega DIR] [--dry-run]
Salida: 0 ok · 1 no se encontró el run · 2 uso incorrecto (con --registrar, el código de memoria.py --costo: 2 si
        rechaza la entrada)
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICO_AVISO = 150_000
ABREV = {"Bash": "bash", "Read": "read", "Write": "write", "Edit": "edit", "WebSearch": "search", "WebFetch": "fetch",
         "ToolSearch": "tsearch", "StructuredOutput": "out", "Agent": "agent", "Glob": "glob", "Grep": "grep"}


def slug_proyecto(ruta):
    """El nombre de la carpeta de un proyecto en ~/.claude/projects/: su ruta absoluta con todo lo que no es letra ni
    dígito cambiado por «-» (un worktree en .claude/worktrees/x queda …--claude-worktrees-x)."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(ruta))


def raices_proyecto(proyecto):
    """Las carpetas donde pueden estar las corridas de un proyecto: el slug de hoy y el de antes (solo «/» → «-»)."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    out = []
    for slug in (slug_proyecto(proyecto), os.path.abspath(proyecto).replace("/", "-")):
        p = os.path.join(base, slug)
        if p not in out:
            out.append(p)
    return out


def raiz_proyecto(proyecto):
    cands = raices_proyecto(proyecto)
    return next((p for p in cands if os.path.isdir(p)), cands[0])


def runs_disponibles(proyecto):
    out = []
    for base in raices_proyecto(proyecto):
        for d in glob.glob(os.path.join(base, "*", "subagents", "workflows", "wf_*")):
            if os.path.isdir(d) and d not in [x[1] for x in out]:
                out.append((os.path.getmtime(d), d))
    out.sort(reverse=True)
    return out


def abreviar(nombre):
    if nombre in ABREV:
        return ABREV[nombre]
    m = re.match(r"mcp__(?:plugin_)?([a-z0-9]+)_.*__([a-z_]+)$", nombre)
    if m:
        return "%s:%s" % (m.group(1)[:6], m.group(2).replace("browser_", "")[:10])
    return nombre[:10].lower()


def ts(s):
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def leer_jsonl(ruta):
    with open(ruta, encoding="utf-8") as fh:
        for l in fh:
            l = l.strip()
            if not l:
                continue
            try:
                yield json.loads(l)
            except json.JSONDecodeError:
                continue


def analizar_agente(ruta):
    por_msg = {}  # message.id -> usage máximo por campo
    tools = {}
    modelos = {}  # message.model -> mensajes
    primero = ultimo = None
    pico = 0
    for d in leer_jsonl(ruta):
        t = ts(d.get("timestamp"))
        if t:
            primero = primero or t
            ultimo = t
        if d.get("type") != "assistant":
            continue
        m = d.get("message") or {}
        mid = m.get("id") or d.get("uuid")
        u = m.get("usage") or {}
        if mid not in por_msg and m.get("model"):
            modelos[m["model"]] = modelos.get(m["model"], 0) + 1
        acc = por_msg.setdefault(mid, {})
        for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
            acc[k] = max(acc.get(k, 0), u.get(k) or 0)
        ctx = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        pico = max(pico, ctx)
        for b in m.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                tools[b.get("name", "?")] = tools.get(b.get("name", "?"), 0) + 1
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    for u in por_msg.values():
        tot["input"] += u.get("input_tokens", 0)
        tot["output"] += u.get("output_tokens", 0)
        tot["cache_read"] += u.get("cache_read_input_tokens", 0)
        tot["cache_create"] += u.get("cache_creation_input_tokens", 0)
    return {"turnos": len(por_msg), "tools": tools, "tokens": tot, "pico": pico,
            "modelo": max(modelos, key=modelos.get) if modelos else None,
            "inicio": primero.isoformat() if primero else None, "fin": ultimo.isoformat() if ultimo else None,
            "segundos": (ultimo - primero).total_seconds() if primero and ultimo else 0}


def analizar_run(run_dir):
    journal = os.path.join(run_dir, "journal.jsonl")
    agentes = {}  # agentId -> info
    fallidos = 0
    orden = []
    if os.path.exists(journal):
        for d in leer_jsonl(journal):
            t = d.get("type")
            if t == "started" and d.get("agentId"):
                agentes.setdefault(d["agentId"], {"label": d.get("label"), "phase": d.get("phase"), "estado": "iniciado"})
                orden.append(d["agentId"])
            elif t == "result" and d.get("agentId") in agentes:
                agentes[d["agentId"]]["estado"] = "completado"
            elif t == "failed":
                fallidos += 1
    for ruta in sorted(glob.glob(os.path.join(run_dir, "agent-*.jsonl"))):
        aid = re.sub(r"^agent-|\.jsonl$", "", os.path.basename(ruta))
        info = agentes.setdefault(aid, {"label": None, "phase": None, "estado": "sin journal"})
        meta = ruta[:-6] + ".meta.json"
        if os.path.exists(meta):
            try:
                mj = json.load(open(meta, encoding="utf-8"))
                info["label"] = info.get("label") or mj.get("description")
                info["phase"] = info.get("phase") or mj.get("workflowPhase")
                info["agentType"] = mj.get("agentType")
            except json.JSONDecodeError:
                pass
        info.update(analizar_agente(ruta))
        if aid not in orden:
            orden.append(aid)
    # Resumen del runner (si existe): <sesión>/workflows/<run>.json
    run_id = os.path.basename(run_dir)
    sesion_dir = os.path.dirname(os.path.dirname(os.path.dirname(run_dir)))
    runner = {}
    rj = os.path.join(sesion_dir, "workflows", run_id + ".json")
    if os.path.exists(rj):
        try:
            d = json.load(open(rj, encoding="utf-8"))
            runner = {k: d.get(k) for k in ("status", "durationMs", "agentCount", "totalTokens", "totalToolCalls", "defaultModel", "workflowName") if k in d}
        except json.JSONDecodeError:
            pass
    lista = [dict(id=aid, **agentes[aid]) for aid in orden if "tokens" in agentes[aid]]
    tot = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    tools_tot = {}
    inicio = fin = None
    for a in lista:
        for k in tot:
            tot[k] += a["tokens"][k]
        for n, c in a["tools"].items():
            tools_tot[n] = tools_tot.get(n, 0) + c
        ti, tf = ts(a["inicio"]), ts(a["fin"])
        if ti and (inicio is None or ti < inicio):
            inicio = ti
        if tf and (fin is None or tf > fin):
            fin = tf
    return {
        "run": run_id, "ruta": run_dir, "runner": runner,
        "agentes": lista, "n_agentes": len(lista),
        "n_completados": sum(1 for a in lista if a.get("estado") == "completado"),
        "fallbacks": fallidos, "tokens": tot, "tools": tools_tot,
        "inicio": inicio.isoformat() if inicio else None, "fin": fin.isoformat() if fin else None,
        "minutos": round((fin - inicio).total_seconds() / 60, 1) if inicio and fin else 0,
        "pico_alto": [a["label"] or a["id"] for a in lista if a["pico"] > PICO_AVISO],
    }


def rol_de(a):
    """El rol de un agente: su tipo (.claude/agents/); en un agente genérico, su etiqueta sin el número (plano-3 → plano)."""
    tipo = a.get("agentType")
    if tipo and tipo != "general-purpose":
        return tipo
    return re.sub(r"[-_ ]?\d+$", "", str(a.get("label") or tipo or a.get("id") or "agente")) or "agente"


def resumen_costo(r, pieza, flujo):
    """El resumen de una corrida (lo que devuelve analizar_run) como entrada de memoria/costos.json."""
    t = dict(r["tokens"])
    t["total"] = sum(r["tokens"].values())
    por_rol, por_modelo = {}, {}
    for a in r["agentes"]:
        tot = sum(a["tokens"].values())
        x = por_rol.setdefault(rol_de(a), {"agentes": 0, "tokens": 0, "salida": 0, "minutos": 0.0})
        x["agentes"] += 1
        x["tokens"] += tot
        x["salida"] += a["tokens"]["output"]
        x["minutos"] = round(x["minutos"] + a["segundos"] / 60, 1)
        y = por_modelo.setdefault(a.get("modelo") or "?", {"agentes": 0, "tokens": 0, "salida": 0})
        y["agentes"] += 1
        y["tokens"] += tot
        y["salida"] += a["tokens"]["output"]
    ini = ts(r["inicio"])
    return {"pieza": pieza, "flujo": flujo, "run": r["run"], "workflow": (r.get("runner") or {}).get("workflowName"),
            "fecha": ini.astimezone().date().isoformat() if ini else None, "inicio": r["inicio"], "fin": r["fin"],
            "minutos": r["minutos"], "agentes": r["n_agentes"], "completados": r["n_completados"], "fallbacks": r["fallbacks"],
            "tokens": t, "herramientas": sum(r["tools"].values()), "pico_alto": len(r["pico_alto"]),
            "por_rol": por_rol, "por_modelo": por_modelo}


def minutos_hasta_entrega(regs, entrega):
    """El reloj de la pieza: de la primera corrida al guion.json (o carrusel.json) de la entrega. None si no se puede
    medir o no cae entre 0 y 24 h (una entrega vieja o una copia del repositorio no miden nada)."""
    marca = next((os.path.join(entrega, f) for f in ("guion.json", "carrusel.json") if os.path.isfile(os.path.join(entrega, f))), None)
    inicios = [ts(x["inicio"]) for x in regs if ts(x.get("inicio"))]
    if not marca or not inicios:
        return None
    fin = _dt.datetime.fromtimestamp(os.path.getmtime(marca), _dt.timezone.utc)
    m = (fin - min(inicios)).total_seconds() / 60
    return round(m, 1) if 0 < m <= 24 * 60 else None


def registrar(runs_dir, pieza, flujo, entrega=None, dry_run=False, memoria_py=None):
    """--registrar: el resumen de cada corrida → un JSON temporal → memoria.py --costo (que escribe memoria/costos.json)."""
    regs = []
    for run_dir in runs_dir:
        r = analizar_run(run_dir)
        if not r["agentes"]:
            print("ERROR: %s no tiene agent-*.jsonl" % run_dir, file=sys.stderr)
            return 1
        regs.append(resumen_costo(r, pieza, flujo))
    if entrega:
        ent = os.path.abspath(entrega)
        m = minutos_hasta_entrega(regs, ent)
        rel_ent = os.path.relpath(ent, RAIZ)
        for x in regs:
            if not rel_ent.startswith(".."):
                x["entrega"] = rel_ent
            if m is not None:
                x["minutos_pieza"] = m
        if m is None:
            print("AVISO: no mido el reloj hasta la entrega (%s sin guion.json, o la entrega no cae en las 24 h siguientes a la corrida)" % entrega)
    sys.stdout.flush()   # lo que sigue lo imprime memoria.py: que los avisos de aquí salgan antes
    fd, tmp = tempfile.mkstemp(prefix="costo_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"costos": regs}, fh, ensure_ascii=False)
        cmd = [sys.executable, memoria_py or os.path.join(RAIZ, "scripts", "memoria.py"), "--costo", tmp] + (["--dry-run"] if dry_run else [])
        return subprocess.run(cmd).returncode
    finally:
        os.unlink(tmp)


def k(n):
    """1234567 → 1.23M · 45678 → 45.7K · 321 → 321"""
    if n >= 1_000_000:
        return "%.2fM" % (n / 1e6)
    if n >= 1000:
        return "%.1fK" % (n / 1e3)
    return str(n)


def dur(seg):
    seg = int(seg)
    return "%d:%02d" % (seg // 60, seg % 60)


def imprimir(r):
    print("run %s · %d agentes (%d completados) · %d fallback(s) · %s min · %s → %s" % (
        r["run"], r["n_agentes"], r["n_completados"], r["fallbacks"], r["minutos"], (r["inicio"] or "")[11:19], (r["fin"] or "")[11:19]))
    if r["runner"]:
        rn = r["runner"]
        print("runner: status=%s · %s · %s tokens · %s tool calls · %s" % (
            rn.get("status"), ("%.1f min" % (rn["durationMs"] / 60000)) if rn.get("durationMs") else "?", k(rn.get("totalTokens") or 0), rn.get("totalToolCalls"), rn.get("defaultModel")))
    cab = "%-18s %-13s %3s  %-34s %7s %9s %9s %8s %7s %6s" % ("label", "fase", "trn", "tool_use", "input", "cache_rd", "cache_cr", "output", "pico", "dur")
    print(cab)
    print("-" * len(cab))
    for a in r["agentes"]:
        tl = " ".join("%s:%d" % (abreviar(n), c) for n, c in sorted(a["tools"].items(), key=lambda x: -x[1]))
        marca = ""
        if a["pico"] > PICO_AVISO:
            marca += " ▲ctx"
        if a.get("estado") != "completado":
            marca += " ✗%s" % a.get("estado")
        print("%-18s %-13s %3d  %-34s %7s %9s %9s %8s %7s %6s%s" % (
            (a["label"] or a["id"])[:18], (a.get("phase") or "")[:13], a["turnos"], tl[:34], k(a["tokens"]["input"]), k(a["tokens"]["cache_read"]),
            k(a["tokens"]["cache_create"]), k(a["tokens"]["output"]), k(a["pico"]), dur(a["segundos"]), marca))
    print("-" * len(cab))
    t = r["tokens"]
    print("%-18s %-13s %3d  %-34s %7s %9s %9s %8s" % ("TOTAL", "", sum(a["turnos"] for a in r["agentes"]), "%d tool_use" % sum(r["tools"].values()),
                                                      k(t["input"]), k(t["cache_read"]), k(t["cache_create"]), k(t["output"])))
    print("tool_use: " + ", ".join("%s %d" % (abreviar(n), c) for n, c in sorted(r["tools"].items(), key=lambda x: -x[1])))
    if r["fallbacks"]:
        print("AVISO: %d intento(s) 'failed' en el journal (fallbacks de tipo de agente: reinicia Claude Code para registrar .claude/agents/)." % r["fallbacks"])
    if r["pico_alto"]:
        print("AVISO: contexto pico > %s en: %s" % (k(PICO_AVISO), ", ".join(r["pico_alto"])))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", nargs="+", help="id del run (wf_xxx) o ruta a su carpeta; varios con --registrar o para verlos seguidos")
    p.add_argument("--ultimo", action="store_true", help="el run con mtime más reciente")
    p.add_argument("--json", action="store_true")
    p.add_argument("--proyecto", default=os.getcwd(), help="directorio del proyecto (default cwd)")
    p.add_argument("--listar", action="store_true", help="lista los runs disponibles")
    p.add_argument("--registrar", action="store_true", help="guarda lo medido en memoria/costos.json (vía memoria.py --costo); exige --pieza y --flujo")
    p.add_argument("--pieza", help="con --registrar: id o slug de la pieza")
    p.add_argument("--flujo", help="con --registrar: el flujo de la pieza (historia, explica, video, sabias…)")
    p.add_argument("--entrega", help="con --registrar: la carpeta entregada (mide el reloj hasta la entrega)")
    p.add_argument("--dry-run", action="store_true", help="con --registrar: imprime y no escribe")
    a = p.parse_args()
    if a.registrar and not (a.pieza and a.flujo):
        p.error("--registrar exige --pieza <id o slug> y --flujo <flujo>")
    if not a.registrar and (a.pieza or a.flujo or a.entrega or a.dry_run):
        p.error("--pieza, --flujo, --entrega y --dry-run van con --registrar")

    runs = runs_disponibles(a.proyecto)
    if a.listar:
        if not runs:
            print("sin runs en %s" % raiz_proyecto(a.proyecto))
            return 1
        for mt, d in runs:
            print("%s  %s" % (_dt.datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M"), os.path.basename(d)))
        return 0
    dirs = []
    for nombre in a.run or []:
        if os.path.isdir(nombre):
            dirs.append(os.path.abspath(nombre))
            continue
        cand = [d for _, d in runs if os.path.basename(d) == nombre or os.path.basename(d).startswith(nombre)]
        if not cand:
            print("ERROR: no se encontró el run %s en %s (usa --listar)" % (nombre, raiz_proyecto(a.proyecto)), file=sys.stderr)
            return 1
        dirs.append(cand[0])
    if not dirs:
        if not (a.ultimo or runs):
            p.error("indica --run wf_xxx o --ultimo")
        if not runs:
            print("ERROR: no hay runs en %s" % raiz_proyecto(a.proyecto), file=sys.stderr)
            return 1
        dirs.append(runs[0][1])
    if a.registrar:
        return registrar(dirs, a.pieza, a.flujo, a.entrega, a.dry_run)
    rs = []
    for run_dir in dirs:
        r = analizar_run(run_dir)
        if not r["agentes"]:
            print("ERROR: %s no tiene agent-*.jsonl" % run_dir, file=sys.stderr)
            return 1
        rs.append(r)
    if a.json:
        json.dump(rs[0] if len(rs) == 1 else rs, sys.stdout, ensure_ascii=False, indent=1)
        print()
    else:
        for i, r in enumerate(rs):
            if i:
                print()
            imprimir(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
