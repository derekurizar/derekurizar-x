#!/usr/bin/env python3
"""Digesto compacto de una sesión: lo que un agente necesita sin leer los JSON enteros.

Lee sesiones/<slug>/hallazgos_*.json, verificacion_*.json y guion.json e imprime
texto plano, una línea por cifra:

  id | concepto (≤60) | valor unidad | año | tipo(n_puntos) | fuente (≤40) | veredicto → valor_final | cita (≤80)

Series añaden «serie: primero=… último=… mín=… máx=… (n)»; desgloses «partes: top3».

--para verificador  solo el eje pedido (--eje), con url y evidencia completa por cifra
--para guionista    todas las cifras con veredicto, agrupadas por eje, más los vacíos;
                    las no_confirmada llevan «✗ NO USAR» (o se excluyen con --solo-ok)
--para productor    solo cifras usadas en guion.json (cifra_ids), con veredicto y tuit
(sin --para)        todo lo anterior en forma neutra, filtrable con --eje
--ids id1,id2       limita el digesto a esas cifras (cualquier modo)
--serie ID          (repetible) imprime SOLO los puntos completos de esa cifra, sin
                    recorte: `p,v` por línea (serie), `nombre,valor` (desglose) o
                    `anio,valor` (puntual), en crudo para pegarlos en visual.datos

Si la salida excede --max-bytes se recortan conceptos y citas antes que filas y
se avisa «(recortado)». Salida: 0 ok · 1 error · 2 uso incorrecto.

Uso: python3 scripts/digesto.py sesiones/<slug> [--eje X] [--para verificador|guionista|productor] [--max-bytes 6000] [--solo-ok]
     python3 scripts/digesto.py sesiones/<slug> --ids pre-c01,pre-c04
     python3 scripts/digesto.py sesiones/<slug> --serie pre-c01 [--serie pre-c04]
"""
import argparse
import glob
import json
import os
import re
import sys

OK = ("verificada", "ajustada")


class UsoIncorrecto(Exception):
    """Argumentos válidos en forma pero inaplicables a esta sesión (exit 2)."""


def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def fmt_num(v):
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, float) and not v.is_integer():
        s = ("%.6f" % v).rstrip("0").rstrip(".")
        ent, _, dec = s.partition(".")
        signo = "-" if ent.startswith("-") else ""
        ent = "{:,}".format(int(ent.lstrip("-")))
        return signo + ent + ("." + dec if dec else "")
    if isinstance(v, (int, float)):
        return "{:,}".format(int(v))
    return str(v)


def rec(s, n):
    """Recorta a n caracteres con «…»; n <= 0 devuelve vacío."""
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    if n <= 0:
        return ""
    return s if len(s) <= n else s[: max(1, n - 1)] + "…"


def cargar(sesion):
    ejes = {}  # eje -> {"cifras": [...], "vacios": [...]}
    for ruta in sorted(glob.glob(os.path.join(sesion, "hallazgos_*.json"))):
        h = leer(ruta)
        eje = h.get("eje") or re.sub(r"^hallazgos_|\.json$", "", os.path.basename(ruta))
        ejes[eje] = {"cifras": h.get("cifras", []), "vacios": h.get("vacios", []) or []}
    ver = {}
    for ruta in sorted(glob.glob(os.path.join(sesion, "verificacion_*.json"))):
        _v = leer(ruta)
        for it in (_v.get("items") or _v.get("cifras") or []):
            ver[it.get("id")] = it
    rg = os.path.join(sesion, "guion.json")
    guion = leer(rg) if os.path.exists(rg) else None
    return ejes, ver, guion


def stats_serie(serie):
    pts = [(p.get("p"), p.get("v")) for p in serie if isinstance(p.get("v"), (int, float))]
    if not pts:
        return ""
    mn = min(pts, key=lambda x: x[1])
    mx = max(pts, key=lambda x: x[1])
    return "serie: primero=%s:%s último=%s:%s mín=%s:%s máx=%s:%s (%d)" % (
        pts[0][0], fmt_num(pts[0][1]), pts[-1][0], fmt_num(pts[-1][1]), mn[0], fmt_num(mn[1]), mx[0], fmt_num(mx[1]), len(pts))


def top_partes(partes, k=3):
    ps = [p for p in partes if isinstance(p.get("valor"), (int, float))]
    ps.sort(key=lambda p: -p["valor"])
    return "partes: " + " · ".join("%s=%s" % (rec(p.get("nombre"), 28), fmt_num(p["valor"])) for p in ps[:k]) + (" (+%d)" % (len(ps) - k) if len(ps) > k else "")


def fila(c, v, wc, wcita, marcar_no_usar=False):
    tipo = c.get("tipo") or "?"
    if c.get("n_puntos"):
        tipo += "(%s)" % c["n_puntos"]
    if v:
        vfin = v.get("valor_final")
        vered = "%s → %s" % (v.get("veredicto"), fmt_num(vfin) if vfin is not None else "—")
    else:
        vered = "sin veredicto"
    cita = ((c.get("evidencia") or {}).get("cita") or "") if isinstance(c.get("evidencia"), dict) else ""
    partes = [c.get("id"), rec(c.get("concepto"), wc), "%s %s" % (fmt_num(c.get("valor")), c.get("unidad") or ""),
              str(c.get("anio") or ""), tipo, rec(c.get("fuente"), 40), vered]
    if cita and wcita > 0:
        partes.append("«%s»" % rec(cita, wcita))
    linea = " | ".join(partes)
    if marcar_no_usar and v and v.get("veredicto") == "no_confirmada":
        linea += "  ✗ NO USAR"
    return linea


def extras(c, para):
    L = []
    if c.get("tipo") == "serie" and c.get("serie"):
        L.append("    " + stats_serie(c["serie"]))
    if c.get("tipo") == "desglose" and c.get("partes"):
        L.append("    " + top_partes(c["partes"]))
    if para == "verificador":
        if c.get("url"):
            L.append("    url: %s" % c["url"])
        ev = c.get("evidencia")
        if isinstance(ev, dict):
            for k in ("url", "cita", "archivo_local"):
                if ev.get(k) and not (k == "url" and ev[k] == c.get("url")):
                    L.append("    evidencia.%s: %s" % (k, rec(ev[k], 300) if k == "cita" else ev[k]))
        if c.get("nota"):
            L.append("    nota: %s" % rec(c["nota"], 200))
    return L


def csv_campo(x):
    """Valor crudo para pegar: números tal cual (JSON), textos entre comillas si llevan coma."""
    if isinstance(x, bool) or x is None:
        return json.dumps(x)
    if isinstance(x, (int, float)):
        return json.dumps(x)
    t = str(x)
    return '"%s"' % t.replace('"', '""') if ("," in t or '"' in t) else t


def imprimir_serie(cid, ejes, ver):
    """Puntos completos de una cifra, sin recorte. Devuelve las líneas o None si no existe."""
    for eje, d in ejes.items():
        for c in d["cifras"]:
            if c.get("id") != cid:
                continue
            v = ver.get(cid)
            vered = ("%s → %s" % (v.get("veredicto"), json.dumps(v.get("valor_final")))) if v else "sin veredicto"
            tipo = c.get("tipo") or "?"
            L = ["## %s | %s | %s | %s | %s(%s) | eje %s | %s" % (
                cid, rec(c.get("concepto"), 120), c.get("unidad") or "", c.get("anio") or "", tipo,
                c.get("n_puntos") or (len(c.get("serie") or c.get("partes") or []) or 1), eje, vered)]
            if c.get("serie"):
                L.append("p,v")
                L += ["%s,%s" % (csv_campo(pt.get("p")), csv_campo(pt.get("v"))) for pt in c["serie"]]
            if c.get("partes"):
                L.append("nombre,valor")
                L += ["%s,%s" % (csv_campo(pt.get("nombre")), csv_campo(pt.get("valor"))) for pt in c["partes"]]
            if not c.get("serie") and not c.get("partes"):
                L.append("anio,valor")
                L.append("%s,%s" % (csv_campo(c.get("anio")), csv_campo(c.get("valor"))))
            return L
    return None


def filtrar_ids(ejes, ids):
    """Deja solo las cifras pedidas. Devuelve los ids que no existen."""
    faltan = set(ids)
    for d in ejes.values():
        d["cifras"] = [c for c in d["cifras"] if c.get("id") in ids]
        faltan -= {c.get("id") for c in d["cifras"]}
    return sorted(faltan)


def construir(ejes, ver, guion, a, wc, wcita):
    """Devuelve (cabecera[], bloques[]) donde cada bloque es una lista de líneas (una cifra)."""
    todas = [(e, c) for e, d in ejes.items() for c in d["cifras"]]
    n_ok = sum(1 for _, c in todas if (ver.get(c.get("id")) or {}).get("veredicto") in OK)
    n_no = sum(1 for _, c in todas if (ver.get(c.get("id")) or {}).get("veredicto") == "no_confirmada")
    n_sin = sum(1 for _, c in todas if c.get("id") not in ver)
    n_ser = sum(1 for _, c in todas if c.get("tipo") == "serie")
    cab = ["digesto %s · %d cifras · %d ok · %d no_confirmadas · %d sin veredicto · %d series · ejes: %s%s" % (
        os.path.basename(os.path.normpath(a.sesion)), len(todas), n_ok, n_no, n_sin, n_ser, ", ".join(ejes) or "—",
        (" · para " + a.para) if a.para else "")]
    cab.append("id | concepto | valor unidad | año | tipo(n) | fuente | veredicto → valor_final | cita")

    ejes_sel = {e: d for e, d in ejes.items() if not a.eje or e == a.eje}
    bloques = []
    if a.para == "productor":
        if not guion:
            raise UsoIncorrecto("--para productor necesita guion.json en la sesión")
        uso = {}
        for t in guion.get("tuits", []):
            for cid in ((t.get("visual") or {}).get("cifra_ids") or []):
                if a.ids and cid not in a.ids:
                    continue
                uso.setdefault(cid, []).append("T%s" % t.get("n"))
        indice = {c.get("id"): (e, c) for e, c in todas}
        cab.append("cifras en guion.json: %d · tuits: %d" % (len(uso), len(guion.get("tuits", []))))
        for cid, tuits in uso.items():
            if cid not in indice:
                bloques.append(["%s | (NO EXISTE en hallazgos) | usada en %s  ✗" % (cid, ", ".join(tuits))])
                continue
            e, c = indice[cid]
            v = ver.get(cid)
            L = [fila(c, v, wc, wcita, marcar_no_usar=True) + " | en %s" % ", ".join(tuits)]
            if not v or v.get("veredicto") not in OK:
                L[0] += "  ✗ NO USAR"
            L += extras(c, a.para)
            bloques.append(L)
        return cab, bloques

    if a.para == "verificador":
        if not a.eje:
            if len(ejes) == 1:
                a.eje = next(iter(ejes))
                ejes_sel = ejes
            else:
                raise UsoIncorrecto("--para verificador exige --eje (hay: %s)" % ", ".join(ejes))
        if a.eje not in ejes:
            raise UsoIncorrecto("no existe hallazgos_%s.json (hay: %s)" % (a.eje, ", ".join(ejes) or "ninguno"))

    for e, d in ejes_sel.items():
        bloques.append(["## eje %s (%d cifras)" % (e, len(d["cifras"]))])
        for c in d["cifras"]:
            v = ver.get(c.get("id"))
            if a.para == "guionista" and a.solo_ok and (not v or v.get("veredicto") not in OK):
                continue
            L = [fila(c, v, wc, wcita, marcar_no_usar=(a.para in ("guionista", None)))]
            L += extras(c, a.para)
            bloques.append(L)
        if a.para in ("guionista", None) and d["vacios"]:
            bloques.append(["  vacíos %s:" % e] + ["   - " + rec(x, 200) for x in d["vacios"]])
    return cab, bloques


def render(cab, bloques):
    return "\n".join(cab + [l for b in bloques for l in b]) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sesion", help="carpeta sesiones/<slug>")
    p.add_argument("--eje", help="solo ese eje (obligatorio con --para verificador si hay varios)")
    p.add_argument("--para", choices=["verificador", "guionista", "productor"])
    p.add_argument("--max-bytes", type=int, default=6000)
    p.add_argument("--solo-ok", action="store_true", help="con --para guionista: excluye las no_confirmada / sin veredicto")
    p.add_argument("--ids", help="limita el digesto a esas cifras (ids separados por coma)")
    p.add_argument("--serie", action="append", default=[], metavar="ID",
                   help="imprime solo los puntos completos de esa cifra (repetible); p,v · nombre,valor · anio,valor")
    a = p.parse_args()
    a.ids = {x.strip() for x in a.ids.split(",") if x.strip()} if a.ids else None
    if not os.path.isdir(a.sesion):
        print("ERROR: no existe la carpeta %s" % a.sesion, file=sys.stderr)
        return 2
    ejes, ver, guion = cargar(a.sesion)
    if not ejes and a.para != "productor":
        print("ERROR: %s no tiene hallazgos_*.json" % a.sesion, file=sys.stderr)
        return 1
    if a.serie:
        fallos = 0
        for cid in a.serie:
            L = imprimir_serie(cid, ejes, ver)
            if L is None:
                print("ERROR: no existe la cifra %s en hallazgos_*.json" % cid, file=sys.stderr)
                fallos += 1
                continue
            sys.stdout.write("\n".join(L) + "\n")
        return 1 if fallos else 0
    if a.ids:
        faltan = filtrar_ids(ejes, a.ids)
        if faltan:
            print("ERROR: --ids: no existen %s" % ", ".join(faltan), file=sys.stderr)
            return 1

    recortado = False
    salida = None
    try:
        construir(ejes, ver, guion, a, 60, 80)
    except UsoIncorrecto as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    # Primero se estrechan conceptos y citas; solo después se quitan filas.
    for wc, wcita in ((60, 80), (45, 40), (30, 0), (22, 0)):
        cab, bloques = construir(ejes, ver, guion, a, wc, wcita)
        salida = render(cab, bloques)
        if len(salida.encode("utf-8")) <= a.max_bytes:
            break
        recortado = True
    if len(salida.encode("utf-8")) > a.max_bytes:
        # Quitar sublíneas (series/partes/url) y luego filas del final.
        bloques = [[b[0]] for b in bloques]
        while bloques and len(render(cab, bloques).encode("utf-8")) > a.max_bytes:
            bloques.pop()
        salida = render(cab, bloques)
    if recortado:
        salida += "(recortado)\n"
    sys.stdout.write(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
