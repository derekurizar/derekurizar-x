#!/usr/bin/env python3
"""check_docs.py — la documentación que guía a los agentes no se rompe ni engorda (D0–D7).

CLAUDE.md lo carga cada agente de cada corrida: se mantiene corto (reglas, decisiones, una línea por flujo) y el
detalle vive en referencias/ y en .claude/. Este script comprueba que al moverlo no se perdió nada y que lo que se
cita existe.

  D0  ningún identificador del CLAUDE.md largo (congelado en scripts/pruebas/claude_md_identificadores.txt) se perdió:
      cada uno está en CLAUDE.md, referencias/ o .claude/ (o en scripts/pruebas/claude_md_retirados.txt, con su motivo)
  D1  CLAUDE.md ≤ 3,300 palabras
  D2  toda ruta citada en CLAUDE.md existe
  D3  toda sección citada («Sección» en `archivo.md`) existe, en CLAUDE.md, los comandos y los agentes
  D4  anclas: las reglas y decisiones que deben poder encontrarse con grep donde les toca (ANCLAS)
  D5  todo comando, agente, workflow y script aparece en referencias/mapa.md
  D6  ninguna guía describe un flujo retirado (/noticias, /semana) salvo para decir que se retiró
  D7  guías por modo: cada referencias/roles/<rol>/<modo>.md está citado en el núcleo del rol y cada archivo que citan
      el núcleo o los workflows (guia('rol', 'modo')) existe

Uso:
  python3 scripts/check_docs.py                      corre D0–D7 (exit 1 con fallas)
  python3 scripts/check_docs.py --congelar ARCHIVO   escribe la lista de identificadores de ARCHIVO (el CLAUDE.md largo)
  python3 scripts/check_docs.py --faltan             lista los identificadores de D0 que no están en ninguna parte
  python3 scripts/check_docs.py --raiz DIR           otra raíz (pruebas)
"""
import argparse
import glob
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALABRAS_MAX = 3300
CONGELADOS = "scripts/pruebas/claude_md_identificadores.txt"
RETIRADOS = "scripts/pruebas/claude_md_retirados.txt"
FLUJOS_RETIRADOS = ("noticias", "semana")
GATE = re.compile(r"\b(?:[A-Z]{1,2}3?[A-Z]?-?C?\d{1,2}[a-z]?)\b")
# (expresión regular, archivo donde tiene que estar): lo que un agente busca con grep cuando duda de una regla
ANCLAS = [
    (r"en suma", "CLAUDE.md"),
    (r"no_confirmada", "CLAUDE.md"),
    (r"elige el gancho y el cierre", "CLAUDE.md"),
    (r"nunca anuncia", "referencias/promesas.md"),
    (r"\bP6\b", "referencias/promesas.md"),
    (r"bisagra", "referencias/promesas.md"),
    (r"\bR14\b", "referencias/ganchos.md"),
    (r"\bR5\b.*6 s", "referencias/ganchos.md"),
    (r"\bF9\b", "referencias/cierres.md"),
    (r"El Faraon 4", "referencias/flujo-video.md"),
    (r"\bV13\b", "referencias/flujo-video.md"),
    (r"\bV16\b", "referencias/flujo-video.md"),
    (r"\bV25\b", "referencias/flujo-video.md"),
    (r"\bV26\b", "referencias/flujo-video.md"),
    (r"CAMARA_QUIETA", "referencias/flujo-video.md"),
    (r"\bH12\b", "referencias/flujo-historia.md"),
    (r"\bH25\b", "referencias/flujo-historia.md"),
    (r"\bH26\b", "referencias/flujo-historia.md"),
    (r"\bH7b\b", "referencias/flujo-historia.md"),
    (r"\bH8m\b", "referencias/flujo-historia.md"),
    (r"legado", "referencias/flujo-historia.md"),
    (r"`vias`", "referencias/flujo-historia.md"),
    (r"\bSE9\b", "referencias/flujo-serie.md"),
    (r"\bSE14\b", "referencias/flujo-serie.md"),
    (r"\bSE15\b", "referencias/flujo-serie.md"),
    (r"\bSE17\b", "referencias/flujo-serie.md"),
    (r"fijada en mi perfil", "referencias/flujo-serie.md"),
    (r"\bE3\b", "referencias/flujo-explica.md"),
    (r"«Ejemplo»", "referencias/flujo-explica.md"),
    (r"\bS1\b", "referencias/flujo-sabias.md"),
    (r"\bD1\b", "referencias/flujo-departamento.md"),
    (r"\bCG1\b", "referencias/flujo-congreso.md"),
    (r"\bCA1\b", "referencias/flujo-carrusel.md"),
    (r"\bAN1\b", "referencias/flujo-analisis.md"),
    (r"\bAG1\b", "referencias/flujo-agenda.md"),
    (r"19:30", "referencias/flujo-agenda.md"),
    (r"\bMV8\b", "referencias/flujo-mesa.md"),
    (r"\bMV1\b", "referencias/flujo-mesa.md"),
    (r"--workers 1", "referencias/flujo-mesa.md"),
    (r"[Rr]epliegue", "referencias/flujo-mesa.md"),
    (r"\bYT13\b", "referencias/flujo-youtube.md"),
    (r"montaje\.json", "referencias/flujo-youtube.md"),
    (r"\bC3D1\b", "referencias/flujo-video3d.md"),
    (r"[Uu]n solo estilo", "referencias/flujo-video3d.md"),
    (r"\bM3D1\b", "referencias/diseno/maqueta3d.md"),
    (r"Noche", "referencias/diseno/sistema.md"),
    (r"generations_count", "referencias/fragmentos/voz-mcp.md"),
    (r"--nodos", "referencias/fragmentos/voz-mcp.md"),
    (r"\bI1\b", "referencias/flujo-investigacion.md"),
]


def leer(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def identificadores(texto):
    """Lo que un agente buscaría con grep: los tramos entre comillas invertidas de una sola palabra y los códigos de gate."""
    ids = set()
    for t in re.findall(r"`([^`\n]+)`", texto):
        t = t.strip()
        if t and " " not in t and len(t) >= 3:
            ids.add(t)
    ids.update(GATE.findall(texto))
    return ids


def docs(raiz):
    """Todo el texto donde un identificador puede vivir: CLAUDE.md, referencias/ y .claude/ (comandos, agentes, workflows)."""
    rutas = [os.path.join(raiz, "CLAUDE.md")]
    for base in ("referencias", os.path.join(".claude", "commands"), os.path.join(".claude", "agents"), os.path.join(".claude", "workflows")):
        for d, _, fs in os.walk(os.path.join(raiz, base)):
            rutas += [os.path.join(d, f) for f in fs if f.endswith((".md", ".js", ".json"))]
    return {os.path.relpath(r, raiz): leer(r) for r in sorted(rutas)}


def retirados(raiz):
    """identificador → motivo (una línea `identificador<TAB>motivo`; # comenta)."""
    r = {}
    for l in leer(os.path.join(raiz, RETIRADOS)).split("\n"):
        if l.strip() and not l.startswith("#"):
            k, _, v = l.partition("\t")
            r[k.strip()] = v.strip()
    return r


def d0(raiz, D):
    lista = [l.strip() for l in leer(os.path.join(raiz, CONGELADOS)).split("\n") if l.strip() and not l.startswith("#")]
    if not lista:
        return ["D0 falta %s (python3 scripts/check_docs.py --congelar <CLAUDE.md largo>)" % CONGELADOS], []
    todo = "\n".join(D.values())
    fuera = retirados(raiz)
    faltan = [i for i in lista if i not in todo and i not in fuera]
    sin_motivo = [i for i, m in fuera.items() if not m]
    f = []
    if faltan:
        f.append("D0 %d identificador(es) del CLAUDE.md anterior no están en CLAUDE.md, referencias/ ni .claude/: %s%s"
                 % (len(faltan), ", ".join(faltan[:12]), " …" if len(faltan) > 12 else ""))
    if sin_motivo:
        f.append("D0 %s: identificador(es) sin motivo: %s" % (RETIRADOS, ", ".join(sin_motivo[:8])))
    return f, faltan


def d1(D):
    n = len(D.get("CLAUDE.md", "").split())
    return ["D1 CLAUDE.md tiene %d palabras (máximo %d): lo nuevo va a la guía de su flujo o a referencias/mapa.md" % (n, PALABRAS_MAX)] if n > PALABRAS_MAX else []


def existe(raiz, t):
    bases = ("", "referencias", "scripts", os.path.join(".claude", "commands"), os.path.join(".claude", "workflows"), os.path.join(".claude", "agents"))
    return any(os.path.exists(os.path.join(raiz, b, t)) for b in bases)


def d2(raiz, D):
    f = []
    for t in sorted(set(re.findall(r"`([^`\n]+)`", D.get("CLAUDE.md", "")))):
        t = t.strip().replace("\\|", "|")
        if " " in t or re.search(r"[<>*{}…|$]|N\b", t) or t.startswith(("/", "--", "http")):
            continue
        ruta = t.rstrip("/")
        con_barra = "/" in ruta
        es_archivo = re.search(r"\.(md|py|js|sh|json|html|css)$", ruta)
        if not con_barra and not (es_archivo and (ruta.startswith("flujo-") or ruta.endswith((".py", ".sh")))):
            continue
        if con_barra and not (es_archivo or t.endswith("/")):
            continue
        if not existe(raiz, ruta):
            f.append("D2 CLAUDE.md cita `%s`, que no existe" % t)
    return f


def d3(raiz, D):
    f = []
    for nombre, texto in D.items():
        if not (nombre == "CLAUDE.md" or nombre.startswith((os.path.join(".claude", "commands"), os.path.join(".claude", "agents")))):
            continue
        for sec, arch in re.findall(r"«([^»\n]{3,60})» (?:en|de|del) `([^`\n]+\.md)`", texto):
            arch = arch.strip()
            ruta = next((os.path.join(raiz, b, arch) for b in ("", "referencias", os.path.join("referencias", "roles")) if os.path.isfile(os.path.join(raiz, b, arch))), None)
            if not ruta:
                continue   # un archivo de sesión (caption.md, plano.md): no es una guía
            cuerpo = leer(ruta)
            titulos = [l for l in cuerpo.split("\n") if l.startswith("#") or l.lstrip("-> ").startswith("**")]
            if not any(sec.lower() in l.lower() for l in titulos):
                f.append("D3 %s cita «%s» en `%s`, y esa sección no existe" % (nombre, sec, arch))
    return f


def d4(raiz):
    f = []
    for patron, arch in ANCLAS:
        if not re.search(patron, leer(os.path.join(raiz, arch))):
            f.append("D4 falta el ancla /%s/ en %s" % (patron, arch))
    return f


def d5(raiz):
    mapa = leer(os.path.join(raiz, "referencias", "mapa.md"))
    if not mapa:
        return ["D5 falta referencias/mapa.md"]
    f = []
    grupos = (("comando", os.path.join(".claude", "commands", "*.md")), ("agente", os.path.join(".claude", "agents", "*.md")),
              ("workflow", os.path.join(".claude", "workflows", "*.js")), ("script", os.path.join("scripts", "*.py")),
              ("script", os.path.join("scripts", "*.js")), ("script", os.path.join("scripts", "*.sh")))
    for tipo, patron in grupos:
        for r in sorted(glob.glob(os.path.join(raiz, patron))):
            base = os.path.basename(r)
            nombre = base if tipo in ("script", "workflow") else base[:-3]
            # los agentes se listan también agrupados: `hilo-*.md`, `noticias-{a,b}.md`
            grupo = tipo == "agente" and re.search(r"%s-(\*|\{[^}]*%s[^}]*\})" % (re.escape(nombre.split("-")[0]), re.escape(nombre.split("-", 1)[-1])), mapa)
            if nombre not in mapa and not grupo:
                f.append("D5 %s %s no aparece en referencias/mapa.md" % (tipo, base))
    return f


def d6(D):
    f = []
    patron = re.compile(r"(?<![\w.])/(%s)\b(?![./\w-])" % "|".join(FLUJOS_RETIRADOS))
    for nombre, texto in D.items():
        for n, l in enumerate(texto.split("\n"), 1):
            if patron.search(l) and not re.search(r"retir|histórico", l, re.I):
                f.append("D6 %s:%d describe un flujo retirado (/%s)" % (nombre, n, patron.search(l).group(1)))
    return f


def d7(raiz, D):
    f = []
    roles = os.path.join(raiz, "referencias", "roles")
    for d in sorted(glob.glob(os.path.join(roles, "*", ""))):
        rol = os.path.basename(d.rstrip(os.sep))
        nucleo = leer(os.path.join(roles, rol + ".md"))
        if not nucleo:
            f.append("D7 referencias/roles/%s/ no tiene su núcleo referencias/roles/%s.md" % (rol, rol))
            continue
        for m in sorted(glob.glob(os.path.join(d, "*.md"))):
            if os.path.basename(m) not in nucleo:
                f.append("D7 referencias/roles/%s/%s no está citado en el núcleo del rol" % (rol, os.path.basename(m)))
        for cita in set(re.findall(r"`(?:referencias/roles/%s/)?([a-z0-9-]+\.md)`" % re.escape(rol), nucleo)):
            if cita != rol + ".md" and re.search(r"roles/%s/`|`referencias/roles/%s/%s`" % (re.escape(rol), re.escape(rol), re.escape(cita)), nucleo) \
                    and not os.path.isfile(os.path.join(d, cita)) and not existe(raiz, cita):
                f.append("D7 el núcleo de %s cita %s, que no existe en referencias/roles/%s/" % (rol, cita, rol))
    for nombre, texto in D.items():
        if not nombre.endswith(".js"):
            continue
        for rol, modos in re.findall(r"guia\('([a-z-]+)'((?:,\s*'[a-z0-9-]+')+)\)", texto):
            for modo in re.findall(r"'([a-z0-9-]+)'", modos):
                if not os.path.isfile(os.path.join(roles, rol, modo + ".md")):
                    f.append("D7 %s pide guia('%s', '%s') y referencias/roles/%s/%s.md no existe" % (nombre, rol, modo, rol, modo))
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--congelar", metavar="ARCHIVO", help="escribe la lista de identificadores de ese CLAUDE.md")
    ap.add_argument("--faltan", action="store_true", help="lista los identificadores de D0 que faltan, uno por línea")
    ap.add_argument("--raiz", default=RAIZ)
    a = ap.parse_args()
    raiz = os.path.abspath(a.raiz)
    if a.congelar:
        ids = sorted(identificadores(leer(a.congelar)))
        if not ids:
            print("FALLA  %s no trae identificadores" % a.congelar)
            return 2
        destino = os.path.join(raiz, CONGELADOS)
        with open(destino, "w", encoding="utf-8") as f:
            f.write("# Identificadores del CLAUDE.md largo (2026-11-14), congelados para D0 de scripts/check_docs.py.\n")
            f.write("\n".join(ids) + "\n")
        print("escrito %s (%d identificadores)" % (CONGELADOS, len(ids)))
        return 0
    D = docs(raiz)
    f0, faltan = d0(raiz, D)
    if a.faltan:
        print("\n".join(faltan))
        return 1 if faltan else 0
    fallas = f0 + d1(D) + d2(raiz, D) + d3(raiz, D) + d4(raiz) + d5(raiz) + d6(D) + d7(raiz, D)
    for x in fallas:
        print("FALLA  " + x)
    print("[check_docs] %d falla(s) · CLAUDE.md %d palabras" % (len(fallas), len(D.get("CLAUDE.md", "").split())))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
