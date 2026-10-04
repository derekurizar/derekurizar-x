#!/usr/bin/env python3
"""Banco de ideas para hilos (ideas/banco.json). Es el ÚNICO escritor del banco.

Cada idea: {id, creada, area, titulo, pregunta, por_que_ahora, angulo, hook_sugerido,
paleta_sugerida, datos[]{fuente, indicador, url, formato, periodo, evidencia},
puntaje{interes, datos, actualidad, total}, estado, hilo_id, actualizada, nota}.
estado: pendiente | en_curso | hecha | descartada. Toda escritura regenera ideas/README.md.

--resumen                 ideas del banco y temas de memoria/hilos.json (lo que /ideas debe evitar)
--importar <dir>          añade las ideas de <dir>/ideas_*.json (las escriben los exploradores):
                          valida campos, recalcula puntaje.total, descarta repetidas (mismo id
                          o ≥60 % de palabras clave compartidas con otra idea o con un hilo)
--siguiente               la idea pendiente de mayor puntaje (JSON compacto); exit 1 si no hay
--ver <id>                una idea en compacto (para el editor de /hilo)
--buscar "tema"           ideas pendientes o en curso que casan con un tema libre
--marcar <id> --estado E  [--hilo <hilo_id>] cambia el estado (hecha exige --hilo)
--conciliar               marca hecha toda idea enlazada (idea_id) desde un hilo listo de
                          memoria/hilos.json; lista como «posible» las que solo casan por tema

Opciones: --fecha YYYY-MM-DD (por defecto hoy) · --dry-run · --banco/--hilos (rutas, para pruebas).
Salida: 0 ok · 1 error · 2 uso incorrecto
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import fuentes as _fuentes  # noqa: E402
from ensamblar import HOOKS  # noqa: E402

BANCO = os.path.join(RAIZ, "ideas", "banco.json")
HILOS = os.path.join(RAIZ, "memoria", "hilos.json")
TOKENS = os.path.join(RAIZ, "design", "tokens.json")
ESTADOS = ["pendiente", "en_curso", "hecha", "descartada"]
AREAS = ["economia", "seguridad", "salud", "educacion", "clima-agro", "energia", "fiscal", "poblacion", "otra"]
FORMATOS = ["xlsx", "xls", "csv", "html", "pdf", "json", "api"]
UMBRAL = 0.6
COMENTARIO = ("Banco de ideas para hilos. Lo escribe SOLO scripts/ideas.py (exploradores vía --importar, "
              "memoria.py al registrar un hilo con idea_id). estado: pendiente | en_curso | hecha | descartada.")


class ErrorUso(Exception):
    pass


def hoy():
    return datetime.date.today().isoformat()


def leer(ruta, defecto=None):
    if not os.path.exists(ruta):
        if defecto is not None:
            return defecto
        raise SystemExit("ERROR: falta %s" % os.path.relpath(ruta, RAIZ))
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def cargar_banco(ruta=BANCO):
    b = leer(ruta, {"version": 1, "_comentario": COMENTARIO, "ideas": []})
    b.setdefault("ideas", [])
    return b


def paletas():
    try:
        return set(leer(TOKENS).get("paletas", {}))
    except SystemExit:
        return set()


def slug_de(texto):
    s = re.sub(r"[^a-z0-9]+", "-", _fuentes.normalizar(texto)).strip("-")
    return s[:60].rstrip("-")


def claves(*textos):
    return {k for k in _fuentes.palabras_clave(" ".join(str(t or "") for t in textos)) if not k.isdigit()}


def claves_idea(i):
    return claves(i.get("titulo"), i.get("pregunta"))


def solapa(a, b, base=None):
    """Fracción de claves compartidas sobre el conjunto menor (o sobre `base`)."""
    if not a or not b:
        return 0.0
    comun = len(a & b)
    if comun < 2:
        return 0.0
    return comun / float(len(base) if base is not None else min(len(a), len(b)))


def total(p):
    return sum(int(p.get(k) or 0) for k in ("interes", "datos", "actualidad"))


def validar_idea(i, pals):
    """Lista de problemas de una idea (vacía = válida)."""
    F = []
    for campo in ("titulo", "pregunta", "por_que_ahora", "area"):
        if not str(i.get(campo) or "").strip():
            F.append("sin %s" % campo)
    if i.get("area") and i["area"] not in AREAS:
        F.append("area %r no está en %s" % (i["area"], "|".join(AREAS)))
    if i.get("hook_sugerido") and i["hook_sugerido"] not in HOOKS:
        F.append("hook_sugerido %r desconocido" % i["hook_sugerido"])
    if pals and i.get("paleta_sugerida") and i["paleta_sugerida"] not in pals:
        F.append("paleta_sugerida %r desconocida" % i["paleta_sugerida"])
    datos = i.get("datos") or []
    if not any(str(d.get("url") or "").startswith("http") and str(d.get("evidencia") or "").strip() for d in datos):
        F.append("ningún dato con url y evidencia de que la fuente lo publica")
    for d in datos:
        if d.get("formato") and d["formato"] not in FORMATOS:
            F.append("formato %r no está en %s" % (d["formato"], "|".join(FORMATOS)))
    p = i.get("puntaje") or {}
    for k in ("interes", "datos", "actualidad"):
        if not isinstance(p.get(k), int) or not 1 <= p[k] <= 5:
            F.append("puntaje.%s debe ser entero 1–5" % k)
    if i.get("estado") and i["estado"] not in ESTADOS:
        F.append("estado %r no está en %s" % (i["estado"], "|".join(ESTADOS)))
    return F


def compacta(i):
    return {k: i.get(k) for k in ("id", "titulo", "area", "pregunta", "por_que_ahora", "angulo", "hook_sugerido",
                                  "paleta_sugerida", "datos", "puntaje", "estado", "hilo_id")}


def readme(banco, ruta_banco):
    ideas = banco.get("ideas", [])
    por = lambda e: [i for i in ideas if i.get("estado") == e]
    pend = sorted(por("pendiente"), key=lambda i: (-(i.get("puntaje") or {}).get("total", 0), i.get("creada", "")))
    L = ["# Banco de ideas", "",
         "Generado por `scripts/ideas.py`: no editar a mano. Nuevas ideas con `/ideas`; "
         "producir una con `/hilo idea:<id>` (o `/hilo` sin tema toma la primera pendiente).", "",
         "%d pendientes · %d en curso · %d hechas · %d descartadas" % (len(pend), len(por("en_curso")), len(por("hecha")), len(por("descartada"))), ""]
    celda = lambda s: str(s or "").replace("|", "/").replace("\n", " ")
    if pend:
        L += ["## Pendientes", "", "| Puntaje | id | Idea | Área | Fuentes |", "|---|---|---|---|---|"]
        for i in pend:
            p = i.get("puntaje") or {}
            fs = ", ".join(sorted({celda(d.get("fuente")) for d in i.get("datos") or [] if d.get("fuente")}))
            L.append("| %s (%s·%s·%s) | `%s` | %s | %s | %s |" % (p.get("total", "?"), p.get("interes", "?"), p.get("datos", "?"),
                                                              p.get("actualidad", "?"), i["id"], celda(i.get("titulo")), i.get("area", ""), fs))
        L.append("")
    if por("en_curso"):
        L += ["## En curso", ""] + ["- `%s` — %s%s" % (i["id"], i.get("titulo"), (" (hilo %s)" % i["hilo_id"]) if i.get("hilo_id") else "") for i in por("en_curso")] + [""]
    if por("hecha"):
        rel = os.path.relpath(os.path.join(RAIZ, "hilos"), os.path.dirname(os.path.abspath(ruta_banco)))
        L += ["## Hechas", ""] + ["- `%s` — %s → [%s](%s/%s/hilo.html)" % (i["id"], i.get("titulo"), i.get("hilo_id"), rel, i.get("hilo_id"))
                                  for i in sorted(por("hecha"), key=lambda i: i.get("actualizada", ""), reverse=True)] + [""]
    if por("descartada"):
        L += ["## Descartadas", ""] + ["- `%s` — %s%s" % (i["id"], i.get("titulo"), (": " + i["nota"]) if i.get("nota") else "") for i in por("descartada")] + [""]
    return "\n".join(L)


def guardar(banco, ruta_banco):
    escribir(ruta_banco, banco)
    with open(os.path.join(os.path.dirname(os.path.abspath(ruta_banco)), "README.md"), "w", encoding="utf-8") as fh:
        fh.write(readme(banco, ruta_banco))


def marcar_idea(idea_id, estado, hilo_id=None, fecha=None, ruta_banco=BANCO, dry_run=False):
    """Cambia el estado de una idea. Devuelve (mensaje, código de salida). Lo usa también memoria.py."""
    if estado not in ESTADOS:
        raise ErrorUso("estado %r no está en %s" % (estado, "|".join(ESTADOS)))
    if estado == "hecha" and not hilo_id:
        raise ErrorUso("--estado hecha exige --hilo <hilo_id>")
    banco = cargar_banco(ruta_banco)
    idea = next((i for i in banco["ideas"] if i.get("id") == idea_id), None)
    if not idea:
        return "ERROR: no hay idea %r en %s" % (idea_id, os.path.relpath(ruta_banco, RAIZ)), 1
    antes = idea.get("estado")
    idea["estado"] = estado
    if hilo_id:
        idea["hilo_id"] = hilo_id
    idea["actualizada"] = fecha or hoy()
    msg = "%sidea %s: %s → %s%s" % ("[dry-run] " if dry_run else "", idea_id, antes, estado, (" (hilo %s)" % hilo_id) if hilo_id else "")
    if not dry_run:
        guardar(banco, ruta_banco)
    return msg, 0


def cmd_resumen(a):
    banco = cargar_banco(a.banco)
    hilos = leer(a.hilos, {"hilos": []}).get("hilos", [])
    print("ideas en el banco: %d" % len(banco["ideas"]))
    for i in banco["ideas"]:
        print("  [%s] %s · %s" % (i.get("estado"), i.get("id"), i.get("titulo")))
    print("hilos ya producidos: %d" % len(hilos))
    for h in hilos:
        print("  %s · %s" % (h.get("id"), re.sub(r"\s+", " ", h.get("tema") or "")[:140]))
    return 0


def cmd_importar(a):
    archivos = sorted(glob.glob(os.path.join(a.importar, "ideas_*.json")))
    if not archivos:
        print("ERROR: no hay ideas_*.json en %s" % a.importar, file=sys.stderr)
        return 1
    banco = cargar_banco(a.banco)
    hilos = leer(a.hilos, {"hilos": []}).get("hilos", [])
    pals = paletas()
    fecha = a.fecha or hoy()
    existentes = [(i["id"], claves_idea(i)) for i in banco["ideas"]]
    ids = {i["id"] for i in banco["ideas"]}
    temas_hilo = [(h.get("id"), claves(h.get("tema"), h.get("tesis"))) for h in hilos]
    nuevas, n_rep, n_inv = [], 0, 0
    for ruta in archivos:
        try:
            d = leer(ruta)
        except ValueError as e:
            print("✗ %s no es JSON válido: %s" % (os.path.basename(ruta), e)); n_inv += 1
            continue
        for i in (d.get("ideas") if isinstance(d, dict) else d) or []:
            i = dict(i)
            i["id"] = slug_de(i.get("id") or i.get("titulo") or "")
            problemas = validar_idea(i, pals)
            if not i["id"]:
                problemas.append("sin id ni título")
            if problemas:
                print("✗ inválida %s (%s): %s" % (i["id"] or "?", os.path.basename(ruta), "; ".join(problemas))); n_inv += 1
                continue
            k = claves_idea(i)
            if i["id"] in ids:
                print("= repetida %s (mismo id)" % i["id"]); n_rep += 1
                continue
            parecida = next((eid for eid, ek in existentes if solapa(k, ek) >= UMBRAL), None)
            if parecida:
                print("= repetida %s (≈ idea %s)" % (i["id"], parecida)); n_rep += 1
                continue
            cubierta = next((hid for hid, hk in temas_hilo if solapa(k, hk, base=k) >= UMBRAL), None)
            if cubierta:
                print("= ya cubierta %s (≈ hilo %s)" % (i["id"], cubierta)); n_rep += 1
                continue
            p = dict(i["puntaje"]); p["total"] = total(p)
            idea = {"id": i["id"], "creada": fecha, "area": i["area"], "titulo": i["titulo"].strip(), "pregunta": i["pregunta"].strip(),
                    "por_que_ahora": i["por_que_ahora"].strip(), "angulo": (i.get("angulo") or "").strip(),
                    "hook_sugerido": i.get("hook_sugerido"), "paleta_sugerida": i.get("paleta_sugerida"),
                    "datos": [{c: dd.get(c) for c in ("fuente", "indicador", "url", "formato", "periodo", "evidencia")} for dd in i.get("datos") or []],
                    "puntaje": p, "estado": "pendiente", "hilo_id": None, "actualizada": fecha, "nota": (i.get("nota") or "").strip()}
            banco["ideas"].append(idea); nuevas.append(idea)
            ids.add(idea["id"]); existentes.append((idea["id"], k))
            print("+ %s · %s · puntaje %d · %s" % (idea["id"], idea["area"], p["total"], idea["titulo"]))
    print("%s%d nuevas · %d repetidas · %d inválidas · banco con %d ideas" % (
        "[dry-run] " if a.dry_run else "", len(nuevas), n_rep, n_inv, len(banco["ideas"])))
    if not a.dry_run and nuevas:
        guardar(banco, a.banco)
    return 0


def cmd_siguiente(a):
    pend = [i for i in cargar_banco(a.banco)["ideas"] if i.get("estado") == "pendiente"]
    if not pend:
        print("sin ideas pendientes", file=sys.stderr)
        return 1
    mejor = sorted(pend, key=lambda i: ((i.get("puntaje") or {}).get("total", 0), i.get("creada", "")), reverse=True)[0]
    print(json.dumps(compacta(mejor), ensure_ascii=False))
    return 0


def cmd_ver(a):
    idea = next((i for i in cargar_banco(a.banco)["ideas"] if i.get("id") == a.ver), None)
    if not idea:
        print("ERROR: no hay idea %r" % a.ver, file=sys.stderr)
        return 1
    print(json.dumps(compacta(idea), ensure_ascii=False, indent=1))
    return 0


def cmd_buscar(a):
    k = claves(a.buscar)
    if not k:
        print("ERROR: el tema no tiene palabras de ≥ 4 letras", file=sys.stderr)
        return 2
    res = []
    for i in cargar_banco(a.banco)["ideas"]:
        if i.get("estado") not in ("pendiente", "en_curso"):
            continue
        s = solapa(k, claves_idea(i))
        if s > 0:
            res.append((s, i))
    res.sort(key=lambda x: -x[0])
    print("tema: %s · ideas que casan: %d" % (a.buscar, len(res)))
    for s, i in res[:8]:
        print("  %s %.2f · %s · [%s] %s" % ("FUERTE" if s >= UMBRAL else "débil ", s, i["id"], i.get("estado"), i.get("titulo")))
    return 0


def cmd_marcar(a):
    if not a.estado:
        raise ErrorUso("--marcar requiere --estado")
    msg, rc = marcar_idea(a.marcar, a.estado, a.hilo, a.fecha, a.banco, a.dry_run)
    print(msg, file=sys.stderr if rc else sys.stdout)
    return rc


def cmd_conciliar(a):
    banco = cargar_banco(a.banco)
    hilos = leer(a.hilos, {"hilos": []}).get("hilos", [])
    enlazadas = {h["idea_id"]: h for h in hilos if h.get("idea_id")}
    cambios = 0
    for i in banco["ideas"]:
        h = enlazadas.get(i.get("id"))
        if not h:
            continue
        estado = "hecha" if h.get("estado") in ("listo", "publicado") else "en_curso"
        if i.get("estado") != estado or i.get("hilo_id") != h.get("id"):
            print("~ %s: %s → %s (hilo %s)" % (i["id"], i.get("estado"), estado, h.get("id")))
            i["estado"], i["hilo_id"], i["actualizada"] = estado, h.get("id"), a.fecha or hoy()
            cambios += 1
    for i in banco["ideas"]:
        if i.get("estado") != "pendiente":
            continue
        k = claves_idea(i)
        for h in hilos:
            if h.get("idea_id") != i["id"] and solapa(k, claves(h.get("tema"), h.get("tesis")), base=k) >= UMBRAL:
                print("? posible: %s ≈ hilo %s (si es la misma idea: --marcar %s --estado hecha --hilo %s)" % (i["id"], h.get("id"), i["id"], h.get("id")))
    print("%s%d idea(s) actualizada(s)" % ("[dry-run] " if a.dry_run else "", cambios))
    if cambios and not a.dry_run:
        guardar(banco, a.banco)
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--resumen", action="store_true")
    g.add_argument("--importar", metavar="DIR")
    g.add_argument("--siguiente", action="store_true")
    g.add_argument("--ver", metavar="ID")
    g.add_argument("--buscar", metavar="TEMA")
    g.add_argument("--marcar", metavar="ID")
    g.add_argument("--conciliar", action="store_true")
    p.add_argument("--estado", choices=ESTADOS)
    p.add_argument("--hilo", metavar="HILO_ID", help="id del hilo (<fecha>-<slug>) para --marcar")
    p.add_argument("--fecha", help="YYYY-MM-DD (por defecto, hoy)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--banco", default=BANCO, help=argparse.SUPPRESS)
    p.add_argument("--hilos", default=HILOS, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.fecha and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.fecha):
        p.error("--fecha debe ser YYYY-MM-DD")
    try:
        if a.resumen: return cmd_resumen(a)
        if a.importar: return cmd_importar(a)
        if a.siguiente: return cmd_siguiente(a)
        if a.ver: return cmd_ver(a)
        if a.buscar: return cmd_buscar(a)
        if a.marcar: return cmd_marcar(a)
        return cmd_conciliar(a)
    except ErrorUso as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
