#!/usr/bin/env python3
"""Revisión de justificación de un informe: digesto por página para el revisor (`informe-revisor`).

El revisor comprueba que todo se justifica y se explica: cada figura dice qué muestra y de dónde sale cada
valor (en el texto, en su pie o en una tabla a la que remite), cada % derivado muestra su operación, cada
estado (cumplido, en proceso…) se apoya en un hecho con fecha y ninguna afirmación del texto queda sin cifra.
No lee informe.json entero (regla de oro 2): lee este digesto, que da por página el texto, las figuras con
sus valores y sus pies, y las tablas (las generadas por auditoria.py, en una línea: las cubre su gate J1–J5).

Avisos mecánicos (pistas para el revisor, no deciden):
  R1  valor de una figura (barra, serie, punto) cuyo nombre no aparece en el texto, los pies ni las tablas de
      su capítulo: nadie lo explica.
  R2  figura sin mención en el texto de su página ni referencia {fig:}/{Fig:}/{fign:} en el informe.
  R3  figura derivada (cálculo propio) cuyo pie no dice la operación (÷ × − «cálculo») ni remite a una tabla.
  R4  el mismo número con distinto redondeo en el texto y en una figura o tabla del mismo capítulo (V5).
  R5  un conteo de estados del texto («7 retrocesos») distinto del de la figura de estados del informe (V5).
  R6  una sigla del texto que no está en el glosario ni se desarrolla en el informe («Sicoin (Sistema …)») (V6).

Uso:
  python3 scripts/revision.py <dir con informe.json> [--informe RUTA] [--capitulo NN ...] [--max-bytes N]
  python3 scripts/revision.py <dir> --avisos          solo los avisos R1–R3 (una línea cada uno)
Salida: 0 ok · 1 informe ilegible · 2 uso incorrecto
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import informe as INF  # noqa: E402  (figuras_de_pagina, continuar_indice: la misma numeración que el PDF)
import verificacion as VM  # noqa: E402  (RE_NUM, interpretar, decimales: el mismo lector de números)

RE_REF_FIG = re.compile(r"\{(?:fig|Fig|fign):([A-Za-z0-9_-]+)\}")
RE_OPERACION = re.compile(INF.RE_DERIVADO.pattern + r"|−|\+|c[áa]lculo|\{[Tt]abla:", re.I)  # la misma idea de «derivado» que I7


def plano(obj, saltar=("grafico", "filas", "columnas", "auto", "datos", "desde")):
    """Cadenas de un objeto (sin datos de gráficos ni filas de tablas)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k not in saltar and not str(k).startswith("_"):
                out += plano(v, saltar)
    elif isinstance(obj, list):
        for v in obj:
            out += plano(v, saltar)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def valores(g):
    """[(nombre, valor)] de un gráfico (items, series, puntos, etiquetas con valores)."""
    out = []
    for it in g.get("items") or []:
        out.append((str(it.get("nombre", "")), it.get("valor")))
    for s in g.get("series") or []:
        vs = s.get("valores") or []
        out.append((str(s.get("nombre", "")), ("%s…%s (%d puntos)" % (vs[0], vs[-1], len(vs))) if vs else ""))
    for p in g.get("puntos") or []:
        if isinstance(p, dict):
            out.append((str(p.get("nombre") or p.get("etiqueta") or ""), p.get("valor", p.get("y"))))
    et, vs = g.get("etiquetas") or [], g.get("valores") or []
    if isinstance(vs, list) and vs and not isinstance(vs[0], (list, dict)):
        out += [(str(e), v) for e, v in zip(et or range(1, len(vs) + 1), vs)]
    if g.get("valor") is not None:
        out.append((str(g.get("etiqueta") or g.get("titulo") or "valor"), g.get("valor")))
    return out


def capitulo_de(P, actual):
    if P.get("tipo") == "capitulo":
        return P.get("numero") or actual
    m = re.match(r"^(\d\d) ·", str(P.get("seccion") or ""))
    return m.group(1) if m else (None if P.get("tipo") in ("conclusiones", "metodo", "glosario", "anexo", "tarjetas", "contraportada") else actual)


def recorrer(R):
    paginas = R["paginas"]
    INF.continuar_indice(paginas)
    cap, out = None, []
    for i, P in enumerate(paginas, 1):
        cap = capitulo_de(P, cap)
        out.append((i, cap, P))
    return out


def avisos(R):
    pags = recorrer(R)
    texto_cap, refs = {}, set()
    for i, cap, P in pags:
        t = " ".join(plano(P))
        refs.update(RE_REF_FIG.findall(t))
        for _, f in INF.figuras_de_pagina(P):
            if f.get("b") == "tabla" or "filas" in f:
                t += " " + " ".join(" ".join(str(c) for c in fila.get("c", [])) + " " + str(fila.get("detalle", "")) for fila in f.get("filas", []))
        texto_cap[cap] = texto_cap.get(cap, "") + " " + norm(t)
    A = []
    for i, cap, P in pags:
        if P.get("auto") or P.get("tipo") in ("tarjetas", "metodo", "indice"):
            continue
        t_pag = norm(" ".join(plano(P)))
        for kind, f in INF.figuras_de_pagina(P):
            if kind != "figura" or f.get("tipo") == "tarjeta":
                continue
            g = f.get("grafico") or {}
            fid = f.get("id") or "(sin id)"
            for nombre, _ in valores(g):
                if nombre and norm(nombre) not in texto_cap.get(cap, ""):
                    A.append("R1 pág. %d · %s: «%s» no aparece en el texto, los pies ni las tablas del capítulo" % (i, fid, nombre))
            titular = norm(f.get("titular"))
            if fid not in refs and not (titular and titular[:24] in t_pag.replace(titular, "", 1)):
                nombres = [norm(n) for n, _ in valores(g) if n]
                if not any(n and n in norm(" ".join(plano(P, saltar=("grafico", "filas", "columnas", "auto", "datos", "desde", "pie", "titular", "kicker")))) for n in nombres):
                    A.append("R2 pág. %d · %s: el texto de la página no la comenta ni se cita con {fig:%s}" % (i, fid, fid))
            if (f.get("derivado") or "cálculo propio" in norm(f.get("fuente"))) and not RE_OPERACION.search(str(f.get("pie") or "") + str(f.get("nota") or "")):
                A.append("R3 pág. %d · %s: figura derivada sin la operación en el pie ni remisión a una tabla" % (i, fid))
    return A + avisos_extra(R, pags)


ESTADOS_TXT = {"cumplido": "Cumplido", "en proceso": "En proceso", "anunciado": "Anunciado", "sin iniciar": "Sin iniciar",
               "incumplido": "Incumplido", "retroceso": "Retroceso", "no atribuible": "No atribuible", "no verificable": "No verificable"}
RE_CONTEO = re.compile(r"\b(\d{1,3})\s+(?:compromisos?\s+|promesas?\s+)?(?:est[áa]n?\s+|van\s+|quedan?\s+)?(?:en\s+)?(" +
                       "|".join(k.replace(" ", r"\s+") for k in ESTADOS_TXT) + r")(?:s|es)?\b", re.I)
RE_SIGLA = re.compile(r"\b[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ]{2,7}\b")
NO_SIGLA = {"III", "VIII", "XIII", "XX", "XXI", "ID", "PDF", "USD", "NOTA", "TOTAL", "FIXTURE"}


def num_textos(texto):
    """[(token, valor, decimales)] de un texto, con el lector de verificacion.py."""
    out = []
    for m in VM.RE_NUM.finditer(texto or ""):
        if m.group(2):
            continue
        it = VM.interpretar(m.group(1))
        if it:
            out.append((m.group(1), it[0][0], it[0][1]))
    return out


def avisos_extra(R, pags):
    """R4–R6 sobre el informe entero (pistas para el revisor)."""
    A = []
    # R4: en la MISMA página, un número del texto y uno de sus figuras o tablas que son el mismo con otro
    # redondeo (≥ 3 cifras significativas en los dos: «6,347.84» frente a «6,348»; 102.1 frente a 102.13)
    def sig(v, d):
        return len(str(int(abs(v)))) + d if abs(v) >= 1 else d

    for i, cap, P in pags:
        if P.get("auto") or P.get("tipo") in ("tarjetas", "indice", "metodo", "anexo"):
            continue
        figs = []
        for _, f in INF.figuras_de_pagina(P):
            for nombre, v in valores(f.get("grafico") or {}):
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    figs.append((f.get("id") or "(figura)", float(v), VM.decimales(float(v)), "%g" % v))
            for fila in f.get("filas") or []:
                for c in fila.get("c", []):
                    for tok, v, d in num_textos(str(c)):
                        figs.append((f.get("id") or "(tabla)", v, d, tok))
        vistos = set()
        for t in plano(P, saltar=("grafico", "filas", "columnas", "auto", "datos", "desde", "pie", "fuente")):
            for tok, tv, d in num_textos(t):
                if tv.is_integer() and 1900 <= tv <= 2100:
                    continue
                for fid, v, dv, ftok in figs:
                    if dv == d or sig(tv, d) < 3 or sig(v, dv) < 3:
                        continue
                    lo = min(d, dv)
                    if round(v, lo) == round(tv, lo) and abs(v - tv) > 1e-9 and (tok, fid) not in vistos:
                        vistos.add((tok, fid))
                        A.append("R4 pág. %d · el texto dice %s y %s lo da como %s: mismo número, otro redondeo" % (i, tok, fid, ftok))
    # R5: conteos de estados del texto frente a la figura de estados (la que tiene ≥ 4 items con nombre de estado)
    figura_estados = None
    for i, cap, P in pags:
        for _, f in INF.figuras_de_pagina(P):
            items = {str(it.get("nombre", "")): it.get("valor") for it in (f.get("grafico") or {}).get("items") or []}
            if sum(1 for k in items if k in ESTADOS_TXT.values()) >= 4:
                figura_estados = (i, f.get("id"), items)
                break
        if figura_estados:
            break
    if figura_estados:
        pf, fid, items = figura_estados
        for i, cap, P in pags:
            if P.get("auto") or P.get("tipo") in ("tarjetas",):
                continue
            for t in plano(P):
                for m in RE_CONTEO.finditer(t):
                    n, est = int(m.group(1)), re.sub(r"\s+", " ", m.group(2).lower())
                    real = items.get(ESTADOS_TXT[est])
                    if isinstance(real, (int, float)) and n != real and not re.search(r"\bde\s+(?:los\s+)?" + re.escape(m.group(0)), t):
                        A.append("R5 pág. %d · el texto dice «%s» y la figura %s (pág. %d) cuenta %s %s" % (i, m.group(0), fid, pf, fmt_n(real), ESTADOS_TXT[est].lower()))
    # R6: siglas sin glosario ni desarrollo
    glos, todo = set(), []
    for i, cap, P in pags:
        if P.get("tipo") == "glosario":
            for t in P.get("terminos") or []:
                glos |= set(RE_SIGLA.findall(str(t.get("t", "")) + " " + str(t.get("d", ""))[:80]))
        todo.append((i, " ".join(plano(P))))
    junto = " ".join(t for _, t in todo)
    desarrolladas = set(re.findall(r"\(([A-ZÁÉÍÓÚÑ]{3,8})\)", junto)) | set(re.findall(r"\b([A-ZÁÉÍÓÚÑ]{3,8})\s*\(", junto))
    ya = set()
    for i, _ in todo:
        P = next(P for j, _c, P in pags if j == i)
        # solo frases en caja mixta (los kickers en mayúsculas no traen siglas) y sin marcadores [ENLACE AL HILO]
        t = " ".join(x for x in plano(P, saltar=("grafico", "filas", "columnas", "auto", "datos", "desde", "kicker", "kicker_izq", "kicker_der"))
                     if sum(ch.islower() for ch in x) > sum(ch.isupper() for ch in x))
        t = re.sub(r"\[[A-ZÁÉÍÓÚÑ ]+\]", " ", t)
        for sg in RE_SIGLA.findall(t):
            if sg in ya or sg in glos or sg in desarrolladas or sg in NO_SIGLA or re.fullmatch(r"[IVXLC]+", sg) or desarrollada(sg, junto):
                continue
            ya.add(sg)
            A.append("R6 pág. %d · sigla %s sin glosario ni desarrollo en el informe" % (i, sg))
    return A


VACIAS = r"(?:\s+(?:de|del|la|las|los|el|y|e|para|en|sobre|a)\b)*"


def desarrollada(sigla, texto):
    """True si el texto trae la sigla desarrollada: palabras cuyas iniciales son sus letras (Instituto Guatemalteco
    de Seguridad Social → IGSS), con artículos y preposiciones entre ellas."""
    letras = [l for l in sigla if l.isalpha()]
    if len(letras) < 3:
        return False
    pat = r"\b" + (VACIAS + r"\s+").join(re.escape(l) + r"[\wáéíóúñ]+" for l in letras) + r"\b"
    return re.search(pat, texto, re.I) is not None and re.search(pat, texto) is not None


def fmt_n(v):
    return ("%d" % v) if float(v).is_integer() else ("%g" % v)


def corto(s, n):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def digesto(R, caps):
    L = []
    for i, cap, P in recorrer(R):
        if caps and cap not in caps:
            continue
        tipo = P.get("tipo")
        if P.get("_indice_cont") or tipo in ("indice", "contraportada"):
            continue
        if P.get("auto"):
            n = sum(len(f.get("filas", [])) for _, f in INF.figuras_de_pagina(P))
            L.append("\n## p. %d · %s · [%s: %d filas generadas por auditoria.py; las cubre el gate J1–J5]" % (i, tipo, P["auto"], n))
            continue
        L.append("\n## p. %d · %s%s%s" % (i, tipo, (" · cap. " + cap) if cap else "", (" · " + P["titulo"]) if P.get("titulo") else ""))
        if P.get("lead"):
            L.append("LEAD: " + corto(P["lead"], 600))
        for B in P.get("bloques") or []:
            b = B.get("b")
            if b == "titulo":
                L.append("TÍTULO: " + B.get("texto", ""))
            elif b == "texto":
                for p in B.get("parrafos") or [B.get("texto")]:
                    L.append("TXT: " + corto(p, 900))
                for m in B.get("margen") or []:
                    L.append("MARGEN: %s — %s" % (m.get("termino", ""), corto(m.get("texto"), 200)))
        for kind, f in INF.figuras_de_pagina(P):
            if kind == "tabla":
                filas = f.get("filas", [])
                L.append("TABLA %s · %s · %d filas · cols: %s" % (f.get("id", "—"), corto(f.get("indice") or f.get("titulo") or "", 60), len(filas),
                                                                 " | ".join(c.get("t", "") for c in f.get("columnas", []))))
                for fila in filas[:4]:
                    L.append("   · " + corto(" | ".join(str(c) for c in fila.get("c", [])), 160))
                if len(filas) > 4:
                    L.append("   · … %d filas más" % (len(filas) - 4))
                L.append("   pie: %s · fuente: %s" % (corto(f.get("pie"), 300), corto(f.get("fuente"), 120)))
                continue
            g = f.get("grafico") or {}
            if f.get("tipo") == "tarjeta":
                L.append("FIG %s · tarjeta del hilo · %s · pie: %s · fuente: %s" % (f.get("id", "—"), corto(f.get("indice"), 60), corto(f.get("pie"), 200), corto(f.get("fuente"), 100)))
                continue
            vals = valores(g)
            L.append("FIG %s · %s · %s · «%s»%s" % (f.get("id", "—"), g.get("tipo", f.get("tipo")), corto(f.get("kicker"), 60), corto(f.get("titular"), 90),
                                                 " · DERIVADA" if f.get("derivado") else ""))
            if vals:
                L.append("   valores: " + "; ".join("%s = %s" % (corto(n, 40), v) for n, v in vals[:40]) + (" …" if len(vals) > 40 else ""))
            L.append("   pie: %s · fuente: %s" % (corto(f.get("pie"), 400), corto(f.get("fuente"), 120)))
        for k in ("tesis", "hallazgos", "cierre", "no_afirma", "limites", "cifras"):
            v = P.get(k)
            if isinstance(v, str):
                L.append("%s: %s" % (k.upper(), corto(v, 600)))
            elif isinstance(v, list):
                for x in v[:16]:
                    L.append("%s: %s" % (k.upper(), corto(json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else x, 300)))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", help="carpeta con informe.json (sesión o entregable)")
    ap.add_argument("--informe", help="ruta del informe.json (por defecto <dir>/informe.json)")
    ap.add_argument("--capitulo", action="append", default=[], metavar="NN", help="solo ese capítulo (repetible)")
    ap.add_argument("--avisos", action="store_true", help="solo los avisos R1–R6")
    ap.add_argument("--max-bytes", type=int, default=90000)
    a = ap.parse_args()
    ruta = a.informe or os.path.join(a.dir, "informe.json")
    if not os.path.exists(ruta):
        print("ERROR: no existe %s" % ruta, file=sys.stderr)
        return 2
    try:
        with open(ruta, encoding="utf-8") as fh:
            R = json.load(fh)
    except (OSError, ValueError) as e:
        print("ERROR: %s ilegible: %s" % (ruta, e), file=sys.stderr)
        return 1
    A = avisos(json.loads(json.dumps(R)))
    if a.avisos:
        print("\n".join(A) if A else "sin avisos R1–R6")
        return 0
    caps = {c.zfill(2) for c in a.capitulo}
    cuerpo = digesto(R, caps)
    cab = "# revisión · %s · %d páginas · %d aviso(s) R1–R6 (pistas; tú decides)\n" % (ruta, len(R["paginas"]), len(A))
    cab += "\n".join(A[:80]) + ("\n… %d avisos más (--avisos)" % (len(A) - 80) if len(A) > 80 else "") + "\n"
    out = cab + cuerpo
    if len(out.encode("utf-8")) > a.max_bytes:
        out = out.encode("utf-8")[: a.max_bytes].decode("utf-8", "ignore") + "\n… recortado a %d bytes: pide --capitulo NN" % a.max_bytes
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
