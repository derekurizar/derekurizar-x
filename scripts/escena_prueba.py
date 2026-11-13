#!/usr/bin/env python3
"""Banco de pruebas de las escenas propias de /historia que se dibujan con archivos reales (vias, …).

Toma un caso de sesiones/_fixture_escenas/<tipo>.json (una escena de guion con su voz), le pasa el gate del tipo,
la arma con su constructor REAL de scripts/historia.py sobre una voz falsa (0.32 s por palabra, una pausa en cada
punto) y la graba con scripts/video_grabar.js: dos veces en 9:16 (los cuadros tienen que salir iguales: seek(t) puro),
una en 4:5, con V13 (zona segura) y A3 (nada sobre el rótulo de acto) medidos por la grabadora, y A1 (quieta entre una
entrada y la siguiente). Deja una hoja de contacto con un cuadro por entrada y el final.

Uso:
  python3 scripts/escena_prueba.py vias [--caso NOMBRE] [--paleta P] [--salida DIR]   un tipo (todos sus casos, o uno)
  python3 scripts/escena_prueba.py --todas                                           todos los tipos y casos
  python3 scripts/escena_prueba.py --lista                                           los tipos y sus casos
Salida en sesiones/_escenas/<tipo>-<caso>/ (contacto.png, contacto_4x5.png, clips). 0 ok · 1 fallo · 2 uso incorrecto
"""
import argparse
import json
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import animaciones as AN  # noqa: E402
import historia as H  # noqa: E402
import video as VD  # noqa: E402

FIXTURES = os.path.join(RAIZ, "sesiones", "_fixture_escenas")
PALABRA_S, PAUSA_S, COLA_S = 0.32, 1.1, 2.6
# tipo → gate, constructor, de dónde salen las entradas (segundo y nombre) y la caja del lienzo en 9:16 para medir A1
TIPOS = {
    "vias": {"gate": lambda g: H.revisar_vias(g), "constructor": H.t_vias,
             "entradas": lambda S: [(c["start"], c.get("lugar") or ",".join(c.get("arterias") or []) or c.get("zoom") or "capa") for c in S["M"]["capas"]],
             "caja": (0, 470, 1080, 840)},
    "lupa": {"gate": lambda g: H.revisar_lupa(g), "constructor": H.t_lupa,
             "entradas": lambda S: [(p["start"], p["etiqueta"]) for p in S["L"]["puntos"]], "caja": (0, 384, 1080, 916)},
    "deptos": {"gate": lambda g: H.revisar_deptos(g), "constructor": H.t_deptos,
               "entradas": lambda S: [(c["start"], ", ".join(c["nombres"]) or c.get("zoom") or "capa") for c in S["D"]["capas"]], "caja": (0, 470, 1080, 840)},
    # el marcador sigue a la voz mientras lee la frase: la quietud se mide desde que termina
    "pagina": {"gate": lambda g: H.revisar_pagina(g), "constructor": H.t_pagina,
               "entradas": lambda S: [(S["PG"]["t"][1], "subrayado")], "caja": (0, 384, 1080, 916)},
    "cortina": {"gate": lambda g: H.revisar_cortina(g), "constructor": H.t_cortina,
                "entradas": lambda S: [(S["T"]["ini"], "antes"), (S["CO"]["t"], "ahora")], "caja": (0, 384, 1080, 916)},
    "archivo": {"gate": lambda g: H.revisar_archivo(g), "constructor": H.t_archivo,
                "entradas": lambda S: ([(p["start"], p.get("fecha") or p.get("etiqueta") or "pieza") for p in S["A"].get("piezas") or S["A"].get("barras") or []]
                                       or [(S["A"]["t"], "conteo")]), "caja": (0, 470, 1080, 790)},
    "bandos": {"gate": lambda g: H.revisar_bandos(g), "constructor": H.t_bandos,
               "entradas": lambda S: [(p["start"], p["nombre"]) for p in S["B"]["personas"]] + ([(S["B"]["umbral"]["start"], "umbral")] if S["B"]["umbral"] else []),
               "caja": (85, 380, 791, 900)},
}


def leer_casos(tipo):
    ruta = os.path.join(FIXTURES, tipo + ".json")
    if not os.path.isfile(ruta):
        return None
    return json.load(open(ruta, encoding="utf-8"))


def voz_falsa(texto):
    """[{text, start, end}] a PALABRA_S por palabra, con PAUSA_S después de cada punto."""
    t, pal = 0.5, []
    for w in texto.split():
        pal.append({"text": w, "start": round(t, 3), "end": round(t + PALABRA_S - 0.02, 3)})
        t += PALABRA_S + (PAUSA_S if w.endswith((".", "?", "!")) else 0)
    return pal


def armar(tipo, escena, paleta):
    pal = voz_falsa(escena["texto"])
    fin = pal[-1]["end"]
    dur = round(fin + COLA_S, 3)
    S = {"n": 1, "tipo": tipo, "tuit": None, "plantilla": None, "enlace": None, "icono": None, "dur": dur, "fin_voz": fin,
         "palabras": pal, "acto": escena.get("acto", 1), "transicion": None, "quieta": True}
    g = {"escenas": [escena]}
    ev, sfx = TIPOS[tipo]["constructor"](S, {"voz": escena["texto"]}, pal, pal, fin, dur, g)
    S["eventos"] = [{"t": round(t, 3), "tipo": k} for t, k in ev]
    S["sfx"] = []
    return {"version": 2, "colores": VD.colores(paleta), "contexto_superior": "Escenas · prueba", "redes": [], "escenas": [S]}, S


def probar(tipo, nombre, escena, paleta, salida=None, F=None):
    T = TIPOS[tipo]
    F = F or {}
    # lo que el constructor y el gate leen de la sesión: las fotos verificadas y, si hace falta, el encuadre
    H.H_ACTUAL = dict(F.get("historia") or {}, fotos=F.get("fotos") or {})
    H.TRABAJO_ACTUAL = None
    if F.get("paginas"):
        H.paginas_h = lambda _p=F["paginas"]: _p
    if F.get("encuadre"):
        H.encuadre = lambda _t, _e=F["encuadre"]: _e
        H.TRABAJO_ACTUAL = "prueba"
        H.respaldo_actual = lambda: None
    fallas = list(T["gate"]({"escenas": [escena]}))
    sal = os.path.abspath(salida or os.path.join(RAIZ, "sesiones", "_escenas", "%s-%s" % (tipo, nombre)))
    if fallas:
        for x in fallas:
            print("FALLA %s/%s: %s" % (tipo, nombre, x))
        return 1
    shutil.rmtree(sal, ignore_errors=True)
    os.makedirs(sal)
    for rec in list((F.get("fotos") or {}).values()) + list((F.get("paginas") or {}).values()):   # las fotos del caso, donde la grabadora las sirve (TRABAJO/fotos/)
        os.makedirs(os.path.join(sal, "fotos"), exist_ok=True)
        shutil.copyfile(os.path.join(FIXTURES, rec["archivo"]), os.path.join(sal, rec["archivo"]))
    todo, S = armar(tipo, escena, paleta)
    json.dump(todo, open(os.path.join(sal, "escenas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    clip = os.path.join(sal, "clips", "e1.mp4")
    err = AN.grabar(sal, "9:16")
    if err:
        print("FALLA %s/%s: la página no grabó: %s" % (tipo, nombre, err))
        return 1
    fallas += AN.GATES_GRABAR
    md5 = AN.framemd5(clip)
    shutil.move(clip, os.path.join(sal, "primera.mp4"))
    err = AN.grabar(sal, "9:16")
    if err:
        print("FALLA %s/%s: la segunda grabación falló: %s" % (tipo, nombre, err))
        return 1
    if AN.framemd5(clip) != md5:
        psnr, cuadro = AN.peor_psnr(os.path.join(sal, "primera.mp4"), clip)
        if psnr < AN.PSNR_MIN:
            fallas.append("dos grabaciones dan cuadros distintos (cuadro %s: %.1f dB): seek(t) no es puro" % (cuadro, psnr))
    os.remove(os.path.join(sal, "primera.mp4"))
    err = AN.grabar(sal, "4:5")
    fallas += list(AN.GATES_GRABAR)
    if err:
        fallas.append("el formato 4:5 no grabó: %s" % err)
    # A1: entre una entrada y la siguiente, pasado ASENTAR_S, el lienzo no se mueve
    entradas = T["entradas"](S)
    vals = VD.movimiento_de(clip, VD.QUIETUD_FPS, recorte=T["caja"])
    for k, (t0, que) in enumerate(entradas):
        a, b = t0 + AN.ASENTAR_S, (entradas[k + 1][0] if k + 1 < len(entradas) else S["dur"]) - 0.4
        mov = [(j / VD.QUIETUD_FPS, v) for j, v in enumerate(vals) if a <= j / VD.QUIETUD_FPS <= b and v >= AN.ADORNO_UMBRAL]
        if mov:
            fallas.append("A1: el lienzo se sigue moviendo %.1f s después de «%s» (desde %.1f s)" % (mov[0][0] - t0, que, mov[0][0]))
    tiempos = [min(t0 + 1.4, S["dur"] - 0.3) for t0, _ in entradas] + [S["dur"] - 0.3]
    AN.contacto(clip, tiempos, os.path.join(sal, "contacto.png"), 640)
    if os.path.exists(os.path.join(sal, "clips_4x5", "e1.mp4")):
        AN.contacto(os.path.join(sal, "clips_4x5", "e1.mp4"), tiempos, os.path.join(sal, "contacto_4x5.png"), 450)
    for x in fallas:
        print("FALLA %s/%s: %s" % (tipo, nombre, x))
    print("%s %s/%s · %d entradas · %.1f s · paleta %s → %s/contacto.png"
          % ("ok   " if not fallas else "MAL  ", tipo, nombre, len(entradas), S["dur"], paleta, os.path.relpath(sal, RAIZ)))
    return 1 if fallas else 0


def main():
    ap = argparse.ArgumentParser(description="Banco de pruebas de las escenas propias de /historia",
                                 epilog="Salida: 0 ok · 1 fallo · 2 uso incorrecto")
    ap.add_argument("tipo", nargs="?", help="tipo de escena (%s)" % ", ".join(TIPOS))
    ap.add_argument("--caso", help="un solo caso del tipo")
    ap.add_argument("--paleta", help="paleta de design/tokens.json (por defecto la del caso)")
    ap.add_argument("--salida", help="carpeta de salida (con --caso)")
    ap.add_argument("--todas", action="store_true", help="todos los tipos y casos")
    ap.add_argument("--lista", action="store_true", help="los tipos y sus casos")
    a = ap.parse_args()
    tipos = list(TIPOS) if (a.todas or a.lista) else [a.tipo] if a.tipo else []
    if not tipos or any(t not in TIPOS for t in tipos):
        ap.print_usage(sys.stderr)
        return 2
    mal = 0
    for tipo in tipos:
        F = leer_casos(tipo)
        if not F:
            print("FALLA %s: no existe sesiones/_fixture_escenas/%s.json" % (tipo, tipo))
            mal += 1
            continue
        casos = F["casos"]
        if a.lista:
            print("%s: %s" % (tipo, ", ".join(casos)))
            continue
        if a.caso and a.caso not in casos:
            print("FALLA %s: no tiene el caso «%s» (hay: %s)" % (tipo, a.caso, ", ".join(casos)))
            return 2
        for nombre, escena in casos.items():
            if a.caso and nombre != a.caso:
                continue
            mal += probar(tipo, nombre, escena, a.paleta or escena.pop("_paleta", None) or F.get("paleta") or "obsidiana", a.salida if a.caso else None, F)
    return 1 if mal else 0


if __name__ == "__main__":
    sys.exit(main())
