#!/usr/bin/env python3
"""Catálogo de gráficos del informe: una página por tipo G.* con la figura en papel, en panel y a media página.

Lee el `const DATA = {...}` de cada plantilla de templates/graficos/*.html (es un literal JS con comentarios:
se evalúa con UNA llamada a node), separa la cabecera (kicker, titular, nota, fuente, handle, leyenda) de los
`datos`, y escribe <dir>/informe.json + <dir>/datos.json sintético (una cifra `cat-<tipo>` verificada por
plantilla, con sus números como partes) para que cada tipo pase I1 e I2 de verdad. Solo entran las plantillas
cuyo G.<tipo> existe (informe.TIPOS_GRAFICO); las demás (informe.plantillas_sin_g) se listan al final.
Por tipo: una página en papel a toda columna (672 px) y otra a media página (papel 324 · panel compacto 284).
Las plantillas de `--tarjeta` (por defecto barras-v, mapa, dona, cascada) llevan además el panel a toda
columna (612 px) y una página que compara la tarjeta 1080 (figura `tarjeta`) con el mismo gráfico en papel.

Uso: python3 scripts/catalogo_informe.py [--dir investigacion/ejemplos/catalogo] [--paleta cielo]
                                        [--solo a,b] [--tarjeta a,b|ninguna]
Después: python3 scripts/informe.py <dir> --check [--png <dir>/salida/png]   (o make informe-catalogo)
Salida: 0 ok · 1 error · 2 uso incorrecto. Imprime «N páginas · M tipos · sin G: …».
"""
import argparse
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import ensamblar  # noqa: E402
import informe  # noqa: E402
import materializar  # noqa: E402

CABECERA = ("kicker", "titular", "nota", "fuente", "handle", "leyenda")
TARJETA_DEFECTO = ["barras-v", "mapa", "dona", "cascada"]
MINI = {  # gráficos solo del tablero (sin plantilla de tarjeta)
    "chispa": {"kicker": "Serie · chispa", "valor": "12,699", "contexto": "en 2026", "grafico": {"tipo": "chispa", "etiquetas": ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"], "valores": [3826, 28810, 5213, 1885, 5364, 19754, 91767, 21252, 12699]}},
    "cuadros": {"kicker": "N de M · cuadros", "valor": "10", "contexto": "de 29 áreas", "grafico": {"tipo": "cuadros", "total": 29, "marcados": 10, "texto": "Un cuadro por área de salud"}},
    "comparacion": {"kicker": "Dos periodos · comparacion", "valor": "45", "contexto": "casos en 2026; 133 en todo 2025", "grafico": {"tipo": "comparacion", "items": [{"nombre": "2026 · SE 35", "valor": 45, "destacar": True}, {"nombre": "2025 · año", "valor": 133}]}},
}


def datos_de_plantillas(nombres):
    """{plantilla: DATA} evaluando los literales JS con node (una sola llamada)."""
    partes = []
    for n in nombres:
        src = open(os.path.join(RAIZ, "templates", "graficos", n + ".html"), encoding="utf-8").read()
        m = materializar.RE_DATA.search(src)
        if not m:
            raise SystemExit("ERROR: %s no tiene un bloque `const DATA = {...};`" % n)
        partes.append("out[%s] = (function(){ %s return DATA; })();" % (json.dumps(n), m.group(0)))
    js = "const out = {};\n" + "\n".join(partes) + "\nprocess.stdout.write(JSON.stringify(out));"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("ERROR evaluando los DATA con node:\n" + r.stderr)
    return json.loads(r.stdout)


def separar(data):
    cab = {k: data[k] for k in CABECERA if k in data}
    datos = {k: v for k, v in data.items() if k not in CABECERA}
    return cab, datos


def figura(tipo_fig, plantilla, cab, datos, cid, sufijo, alto=None, ancho_mapa=None):
    snake = informe.snake(plantilla)
    f = {"id": "%s-%s" % (snake.replace("_", "-"), sufijo), "tipo": tipo_fig, "kicker": cab.get("kicker", plantilla.upper()),
         "titular": cab.get("titular", [plantilla]), "cifra_ids": [cid], "fuente": "Catálogo · cifras de ejemplo de la plantilla %s" % plantilla,
         "pie": "%s en %s." % (plantilla, tipo_fig), "indice": "%s · %s" % (plantilla, tipo_fig)}
    if cab.get("nota"):
        f["nota"] = cab["nota"]
    if cab.get("leyenda"):
        f["leyenda"] = [{"texto": it.get("nombre", ""), "estilo": "base"} for it in cab["leyenda"] if isinstance(it, dict)]
    if tipo_fig == "tarjeta":
        f["plantilla"] = plantilla
        f["datos"] = datos
        f["alt"] = "Tarjeta %s de ejemplo." % plantilla
    else:
        f["grafico"] = dict({"tipo": snake}, **datos)
        if alto:
            f["alto"] = alto
        if snake == "mapa":  # el mapa ignora `alto`: su alto sale del ancho
            f["grafico"]["ancho"] = ancho_mapa or (300 if tipo_fig == "panel" or sufijo == "papel" else 200)
    return f


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dir", default=os.path.join("investigacion", "ejemplos", "catalogo"))
    p.add_argument("--paleta", default="cielo")
    p.add_argument("--solo", help="solo estas plantillas (separadas por comas)")
    p.add_argument("--tarjeta", default=",".join(TARJETA_DEFECTO), help="plantillas con página tarjeta frente a papel; `ninguna` para omitirlas")
    a = p.parse_args()
    catalogo = sorted(ensamblar.catalogo_plantillas())
    con_g = [n for n in catalogo if informe.snake(n) in informe.TIPOS_GRAFICO]
    if a.solo:
        pedidas = [x.strip() for x in a.solo.split(",") if x.strip()]
        malas = [x for x in pedidas if x not in catalogo]
        if malas:
            print("ERROR: plantillas desconocidas: %s" % ", ".join(malas), file=sys.stderr)
            return 2
        con_g = [n for n in pedidas if n in con_g]
    if not con_g:
        print("ERROR: ninguna de las plantillas tiene G.<tipo> en investigacion/graficos/", file=sys.stderr)
        return 1
    con_tarjeta = [] if a.tarjeta == "ninguna" else [x.strip() for x in a.tarjeta.split(",") if x.strip() in con_g]
    D = datos_de_plantillas(con_g)
    out = os.path.abspath(a.dir)
    os.makedirs(out, exist_ok=True)
    rel_datos = os.path.relpath(os.path.join(out, "datos.json"), RAIZ)

    cifras, paginas = [], []
    paginas.append({"tipo": "portada", "kicker_izq": "Catálogo · gráficos del informe", "kicker_der": "%d tipos" % len(con_g),
                    "titulo": "Los gráficos del informe", "lead": "Cada tipo G.* del documento con las cifras de ejemplo de su plantilla de tarjeta: en papel a toda columna, en panel y a media página. Mismos campos que graficos.md.",
                    "fuentes": "cifras de ejemplo de las plantillas"})
    for n in con_g:
        snake = informe.snake(n)
        cab, datos = separar(D[n])
        nums = []
        for x in informe.numeros_de_datos(snake, datos):
            if x not in nums:
                nums.append(x)
        cid = "cat-" + snake.replace("_", "-")
        cifras.append({"id": cid, "concepto": "Cifras de ejemplo de la plantilla %s" % n, "valor": nums[0] if nums else 0, "unidad": "", "anio": "", "tipo": "desglose",
                       "fuente": "catálogo", "url": "", "veredicto": "verificada", "independencia": "alta",
                       "evidencia": {"url": "", "cita": "DATA de ejemplo de templates/graficos/%s.html" % n, "archivo_local": ""},
                       "partes": [{"nombre": "v%d" % (i + 1), "valor": x} for i, x in enumerate(nums)]})
        campos = ", ".join(k for k in datos.keys() if k != "formato")
        paginas.append({"tipo": "cuerpo", "id": "cat-" + snake.replace("_", "-"), "seccion": n, "bloques": [
            {"b": "titulo", "texto": "%s · papel" % n},
            {"b": "texto", "parrafos": ["Campos: %s. Formato: %s." % (campos, json.dumps(datos.get("formato", {}), ensure_ascii=False))]},
            {"b": "figura", **figura("papel", n, cab, datos, cid, "papel")},
        ]})
        paginas.append({"tipo": "cuerpo", "seccion": n, "bloques": [
            {"b": "titulo", "texto": "%s · media página" % n},
            {"b": "texto", "parrafos": ["El mismo gráfico a media página: 324 px en papel y 284 en panel compacto (lo que ve un bloque `figuras` o el tablero)."]},
            {"b": "figuras", "items": [figura("papel", n, cab, datos, cid, "medio-papel", alto=220), figura("panel", n, cab, datos, cid, "medio-panel", alto=220)]},
        ]})
        if n in con_tarjeta:
            paginas.append({"tipo": "cuerpo", "seccion": n, "bloques": [
                {"b": "titulo", "texto": "%s · panel a toda columna" % n},
                {"b": "texto", "parrafos": ["La tarjeta hecha página: fondo de paleta y 612 px de ancho para el gráfico."]},
                {"b": "figura", **figura("panel", n, cab, datos, cid, "panel", alto=300)},
            ]})
            paginas.append({"tipo": "cuerpo", "seccion": n, "bloques": [
                {"b": "titulo", "texto": "%s · tarjeta frente a papel" % n},
                {"b": "figuras", "items": [figura("tarjeta", n, cab, datos, cid, "tarjeta"), figura("papel", n, cab, datos, cid, "vs-papel", alto=260)]},
            ]})
    # Tablero: los tres gráficos mínimos (siempre) + los de tarjeta que caben en 324 px si ya existen.
    tablero = []
    for k, c in MINI.items():
        tablero.append(dict(c, fuente="catálogo · ejemplo"))
    for n in ("bullet", "dona", "waffle"):
        if n in con_g:
            cab, datos = separar(D[n])
            tablero.append({"kicker": "%s · tablero" % n, "valor": "—", "contexto": "a 324 px", "fuente": "catálogo · ejemplo", "grafico": dict({"tipo": informe.snake(n)}, **datos)})
    paginas.append({"tipo": "tablero", "titulo": "Tablero", "subtitulo": "chispa, cuadros y comparacion son solo del tablero; el resto, si cabe a 324 px.", "cifras": tablero[:6]})
    if "combinado" in con_g:
        cab, datos = separar(D["combinado"])
        paginas.append({"tipo": "apaisada", "seccion": "apaisada", "lateral": [{"b": "titulo", "texto": "Una figura ancha"}, {"b": "texto", "parrafos": ["La hoja apaisada da 600 px al gráfico."]}],
                        "figura": figura("panel", "combinado", cab, datos, "cat-combinado", "apaisada", alto=320)})
    paginas.append({"tipo": "contraportada", "lema": "Un contrato, dos tamaños.", "ficha": [["Tipos", str(len(con_g))], ["Paleta", "{paleta}"]]})
    R = {"meta": {"titulo": "Catálogo de gráficos del informe", "corrido": "Catálogo · gráficos del informe", "corto": "Catálogo", "pie": "Catálogo · generado por scripts/catalogo_informe.py",
                  "numero_largo": "Catálogo de gráficos", "fecha": "generado", "handle": "@DerekUrizar", "paleta": a.paleta, "datos": [rel_datos],
                  "fuentes": ["Cifras de ejemplo de templates/graficos/*.html (no son datos reales)."]}, "paginas": paginas}
    json.dump(R, open(os.path.join(out, "informe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"slug": "catalogo", "cifras": cifras, "fuentes": []}, open(os.path.join(out, "datos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sin_g = sorted(informe.plantillas_sin_g())
    print("%d páginas · %d tipos · sin G: %s -> %s" % (len(paginas), len(con_g), ", ".join(sin_g) or "ninguna", os.path.relpath(out, os.getcwd())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
