#!/usr/bin/env python3
"""Costo de una corrida del Workflow /hilo: tokens, herramientas y duración por agente.

Localiza ~/.claude/projects/<slug del cwd>/<sesión>/subagents/workflows/<run>/ (el
slug es la ruta absoluta del proyecto con «/» → «-»; se buscan todas las sesiones)
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
--json vuelca el mismo resumen.

Uso: python3 scripts/costo.py [--run wf_xxx | --ultimo] [--json] [--proyecto DIR] [--listar]
Salida: 0 ok · 1 no se encontró el run · 2 uso incorrecto
"""
import argparse
import datetime as _dt
import glob
import json
import os
import re
import sys

PICO_AVISO = 150_000
ABREV = {"Bash": "bash", "Read": "read", "Write": "write", "Edit": "edit", "WebSearch": "search", "WebFetch": "fetch",
         "ToolSearch": "tsearch", "StructuredOutput": "out", "Agent": "agent", "Glob": "glob", "Grep": "grep"}


def slug_proyecto(ruta):
    return os.path.abspath(ruta).replace("/", "-")


def raiz_proyecto(proyecto):
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", slug_proyecto(proyecto))


def runs_disponibles(proyecto):
    base = raiz_proyecto(proyecto)
    out = []
    for d in glob.glob(os.path.join(base, "*", "subagents", "workflows", "wf_*")):
        if os.path.isdir(d):
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
    p.add_argument("--run", help="id del run (wf_xxx) o ruta a su carpeta")
    p.add_argument("--ultimo", action="store_true", help="el run con mtime más reciente")
    p.add_argument("--json", action="store_true")
    p.add_argument("--proyecto", default=os.getcwd(), help="directorio del proyecto (default cwd)")
    p.add_argument("--listar", action="store_true", help="lista los runs disponibles")
    a = p.parse_args()

    runs = runs_disponibles(a.proyecto)
    if a.listar:
        if not runs:
            print("sin runs en %s" % raiz_proyecto(a.proyecto))
            return 1
        for mt, d in runs:
            print("%s  %s" % (_dt.datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M"), os.path.basename(d)))
        return 0
    if a.run and os.path.isdir(a.run):
        run_dir = os.path.abspath(a.run)
    elif a.run:
        cand = [d for _, d in runs if os.path.basename(d) == a.run or os.path.basename(d).startswith(a.run)]
        if not cand:
            print("ERROR: no se encontró el run %s en %s (usa --listar)" % (a.run, raiz_proyecto(a.proyecto)), file=sys.stderr)
            return 1
        run_dir = cand[0]
    elif a.ultimo or runs:
        if not runs:
            print("ERROR: no hay runs en %s" % raiz_proyecto(a.proyecto), file=sys.stderr)
            return 1
        run_dir = runs[0][1]
    else:
        p.error("indica --run wf_xxx o --ultimo")
    r = analizar_run(run_dir)
    if not r["agentes"]:
        print("ERROR: %s no tiene agent-*.jsonl" % run_dir, file=sys.stderr)
        return 1
    if a.json:
        json.dump(r, sys.stdout, ensure_ascii=False, indent=1)
        print()
    else:
        imprimir(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
