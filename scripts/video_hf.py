#!/usr/bin/env python3
"""video_hf.py — el video vertical (9:16 y 4:5) como «mesa de archivo», dibujado y renderizado con HyperFrames.

Es el mismo lenguaje del 16:9 de /youtube-long (scripts/youtube_hf.py, núcleo en scripts/mesa.py) llevado al cuadro
vertical (usuario, 2026-11-14): con cada oración de la voz ENTRA en pantalla lo que la voz nombra y, una vez puesto, se
queda quieto. La cámara no se mueve ni se escala nada para aparentar ritmo.

Lo propio del vertical:
  · el cuadro: golpe de arriba y barra de progreso, mesa dentro de la zona segura de TikTok, Reels y Shorts, subtítulos
    palabra por palabra debajo, «Sígueme» a mitad, cierre en dos pantallas con «Sígueme en», logos y usuarios;
  · el repliegue: en 1080×1920 caben pocas piezas; cuando la siguiente no cabe, las de al frente pasan DE UN CORTE a su
    versión compacta arriba (nunca se anima la escala, nunca para dar ritmo: solo cuando entra otra pieza);
  · el tiempo de lectura (MV8): un texto queda al frente ≥ 0.5 s + 0.3 s por palabra antes de replegarse o barrerse; la
    cita y el documento que la voz lee no cuentan (se entintan o se subrayan con la voz).

El guion visual es TRABAJO/plano.json, con el mismo esquema del 16:9 (mesas → golpes con `dice`), sin `x` ni `y`: el
motor coloca por regla. Gates MV1–MV14 sobre los datos (nunca sobre píxeles): `plano --check`.

Uso:
  video_hf.py piloto ORIGEN --trabajo DESTINO        copia un TRABAJO ya producido (misma voz) para rehacerlo en mesa
  video_hf.py importar-plano TRABAJO --de SESION_YT --parte N   trae del plano del 16:9 los golpes de esa parte
  video_hf.py borrador TRABAJO                        plano.borrador.json desde lo que ya traen las escenas
  video_hf.py plano TRABAJO [--check] [--hoja] [--borrador]
  video_hf.py tableros TRABAJO [--fps 30]             las escenas que son tablero, grabadas limpias con el motor propio (y las maquetas)
  video_hf.py maquetas TRABAJO [--fps 30] [--todo]    las mesas con maqueta 3D → clips_maqueta/<mesa>.mp4 (maqueta3d.py en modo pieza)
  video_hf.py proyecto TRABAJO [--formato 9:16|4:5]   TRABAJO/hf/<9x16|4x5>/ (un proyecto de HyperFrames)
  video_hf.py revisar TRABAJO [--formato F]           hyperframes check + hoja de contacto por mesa
  video_hf.py audio TRABAJO                           voz + música + efectos del plano a −14 LUFS; .srt
  video_hf.py render TRABAJO [--formato F] [--calidad looks]    SIEMPRE --workers 1
  video_hf.py montar TRABAJO [--formato F]            salida/video.mp4 (9:16) o salida/video_4x5.mp4

Exit 0 ok · 1 falla · 2 uso.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import video as VD   # noqa: E402
import mesa as MS    # noqa: E402
from mesa import (LEAD, FPS, HF_VERSION, leer, escribir, rel, falla, esc, cuadro, fichas, buscar, segmentos, eventos_de, lectura,   # noqa: E402
                  retrato_de, renglones, tam_nombre, atlas, doc_de, Mesa, dibujar, colores, enlazar, hf, resumen_golpe, VD_mmss, numeros)

# ---------- el cuadro ----------
# arriba = y de la cabecera · x0–x1 = columna de la mesa (x1b bajo yb: ahí empiezan los iconos de la app) · y1 = fin de la mesa
FORMATOS = {
    "9:16": {"id": "9x16", "w": 1080, "h": 1920, "arriba": 226, "x0": 85, "x1": 1023, "x1b": 876, "yb": 1070, "y1": 1370, "subs": 1400, "subs_cierre": 1500,
             "salida": "video.mp4", "segs": "segs_mesa"},
    "4:5": {"id": "4x5", "w": 1080, "h": 1350, "arriba": 70, "x0": 85, "x1": 995, "x1b": 995, "yb": 10 ** 6, "y1": 1090, "subs": 1120, "subs_cierre": 1150,
            "salida": "video_4x5.mp4", "segs": "segs_mesa_4x5", "escala": 0.87},   # la mesa del 4:5 es más baja: todo a escala, mismo reparto
}
TABLEROS_V = ("explica", "tarjeta", "cuenta", "hemiciclo", "vias", "deptos", "ranking", "mapa", "escala", "tiempo", "lupa", "cortina", "adivina")
TABLERO_FUERA_V = ("arriba", "chip", "ejemplo")         # lo que la mesa vertical pone por su cuenta (además de youtube.TABLERO_FUERA)
TABLERO_RECORTE_V = "crop=950:1040:65:60"   # la columna segura de la página 4:5 (x 85–995, hasta donde irían los subtítulos)
TABLERO_LADOS = (950, 1040)
# las reglas de los gates que cambian frente al 16:9 (mesa.regla)
PIEZAS_V = ("red", "barra")   # las piezas compuestas propias del vertical (dibujar_red, dibujar_barra); las demás las dibuja mesa.dibujar
BARRAS_MIN, BARRAS_MAX = 2, 5   # la pieza `barra`: la comparación de 2 a 5 valores (la cifra con su medida)
BARRA_FILA = 128
REGLAS = {"MESA_S": (3.0, 24.0), "MESA_PIEZAS": 6, "HUECO_MAX_S": 4.0, "ENTRE_GOLPES_S": 0.4, "FOTO_USOS_MAX": 1, "FOTO_SEPARACION_S": 0,
          "PROPIAS": ("cierre",), "TABLERO": TABLEROS_V, "TIPOS": MS.TIPOS + PIEZAS_V, "ARCHIVO": MS.ARCHIVO + ("red",),
          "TABLERO_SOLO": True, "HUECO_TABLERO_S": 6.0,
          # la maqueta 3D (mesa.py): un clip del lienzo del tablero para los dos formatos; en un vertical caben pocas
          "MAQUETA_LIENZO": TABLERO_LADOS, "MAQUETA_CARPETA": "clips_maqueta", "MAQUETAS_MAX": 2, "MAQUETAS_CAP_MAX": None,
          # los pasos propios de cada tablero del vertical (los eventos que `tiempos` escribe en la escena)
          "EVENTOS_TABLERO": MS.EVENTOS_TABLERO + ("renglon", "resultado", "resalta", "item", "ventana", "punto", "pildora", "figuras", "destacadas", "anio",
                                                    "conteo_fin", "llenar", "umbral", "barras", "plano", "capa", "arista", "persona", "valor", "linea")}   # el tablero conserva el ritmo con que se aprobó su animación (V10: ≤ 6 s)
ATRIBUYE = re.compile(r"\b(segun|para la acusacion|para la fiscalia|dijo|dijeron|afirmo|afirmaron|senalo|senalaron|acuso|acusaron|sostuvo|sostuvieron|a juicio de)\b")
RED_NIVELES, RED_POR_NIVEL, RED_ACUSADORES = 3, 2, 2
RED_CARTA, RED_ALTO, RED_PASO = 380, 164, 226   # una carta de la jerarquía: ancho, alto y paso entre niveles
CODIGOS = {"YT13": "MV1", "YT14": "MV2", "YT15": "MV3", "YT16": "MV4", "YT17": "MV5", "YT18": "MV6", "YT19": "MV7",
           "YT20": "MV15", "YT21": "MV16", "YT22": "MV17", "YT23": "MV18", "YT24": "MV19"}   # la maqueta 3D (mesa.revisar_maqueta)
MAQUETA_MARGEN = 26        # px del marco de la maqueta a la pieza que cae encima (a la escala del formato)
MAQUETA_PIE_PX = 22        # el pie del marco (la atribución de los geodatos y el `aviso` si lo hay): letra de crédito
MAQUETA_GOLPE_ALTO = 0.35  # una pieza sobre la maqueta no tapa más de esta fracción de su alto
LECT_BASE, LECT_PALABRA, LECT_MIN = 0.5, 0.3, 1.0   # MV8: segundos al frente = 0.5 + 0.3 × palabras que la voz no dice (nunca menos de 1 s)
PILA_LEGIBLES, PILA_COMPACTAS = 3, 2   # MV9 (no es un gate): 3 piezas en fila al frente, más una chica al lado de la tercera (4), y 2 compactas arriba
ESCALA_MIN = 0.72                      # MV11: una pieza no se dibuja a menos de esto de su tamaño
COMPACTA_ANCHO = 388                   # dos compactas caben lado a lado en la columna
ANCHO_PIEZA = 791                      # el ancho de la columna segura completa (x 85–876)
SEGUIR_S = 3.4
GIROS_V = [-1.5, 2, -1, 1.5, -2, 1]   # en vertical las hojas van casi derechas: un giro mayor pisa el texto de la vecina
BUCLE_S = VD.BUCLE_S   # el cierre en bucle: el cuadro 0 del gancho vuelve al final (TikTok repite el video)
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
DOC_V = {"pagina": 938, "portada": 600, "portada_h": 620, "tab": (48, 640)}

CSS = """
@font-face{font-family:'Archivo';font-weight:100 900;font-stretch:62% 125%;src:url('assets/fonts/archivo-wdth.woff2') format('woff2')}
@font-face{font-family:'JetBrains Mono';font-weight:100 800;src:url('assets/fonts/jetbrains-mono-var.woff2') format('woff2')}
#root{position:absolute;inset:0;font-family:'Archivo',sans-serif;color:$tinta}
.pz{position:absolute}
.mov{position:relative}
.pila{position:relative;box-shadow:0 30px 60px rgba(0,0,0,.6),0 5px 12px rgba(0,0,0,.45)}
.velo{position:absolute;inset:0;background:$sombra;opacity:0;pointer-events:none}
.cond{font-family:'Archivo',sans-serif;font-stretch:62%;font-weight:800;text-transform:uppercase;line-height:.94;letter-spacing:.005em}
.mono{font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.1em}
.foto{background:$papel;padding:14px 14px 0}
.foto .im{position:relative;overflow:hidden}
.foto .im img{display:block;position:absolute;object-fit:cover}
.foto .pie{padding:12px 6px 14px}
.foto .pie b{display:block;font-weight:650;font-size:36px;line-height:1.12}
.foto .pie span{display:block;margin-top:6px;font-family:'JetBrains Mono',monospace;font-size:22px;color:$sepia;white-space:nowrap;overflow:hidden}
.ficha{background:$papel;padding:26px 32px 28px;border-top:12px solid $cafe}
.ficha.per{display:flex;gap:26px;align-items:flex-start}
.ficha .ret{flex:none;width:210px;height:250px;position:relative;overflow:hidden;background:$papel2}
.ficha .ret img{position:absolute;display:block}
.ficha .k{font-size:28px;line-height:1.2;color:$sepia;font-weight:600}
.ficha .n{margin-top:10px}
.ficha .r{margin-top:12px;font-size:42px;font-weight:500;line-height:1.18;color:$sepia2}
.ficha .f,.cifra .f,.recorte .f,.cita .f{margin-top:14px;font-family:'JetBrains Mono',monospace;font-size:22px;color:$sepia}
.fecha{background:$papel;padding:10px}
.fecha .in{border:5px solid $tinta;padding:14px 26px 8px;text-align:center}
.fecha .s{font-size:28px;font-weight:700}
.fecha .b{font-size:170px;white-space:nowrap}
.cal{background:$papel;text-align:center}
.cal .top{background:$cafe;color:$papel;font-size:44px;padding:10px 0 8px}
.cal .mes{font-size:160px;padding:18px 0 0}
.cal .sub{font-size:28px;font-weight:700;padding:0 0 18px;color:$sepia2}
.cifra{background:$mesa2;border:1px solid $filo;padding:22px 34px 26px;color:$papel}
.cifra .v{color:$acento;white-space:nowrap}
.cifra .l{font-size:56px;margin-top:2px}
.cifra .f{color:$gris}
.cifra.cr .v{color:$papel}
.cifra.cr .cuad i{background:$papel}
.recorte{background:$papel2;padding:26px 30px 28px}
.recorte .cab{display:flex;justify-content:space-between;align-items:baseline;border-bottom:4px solid $tinta;padding-bottom:10px}
.recorte .cab .m{font-size:46px}
.recorte .cab .d{font-family:'JetBrains Mono',monospace;font-size:22px;color:$sepia2}
.recorte .t{font-size:60px;margin-top:18px;text-transform:none;line-height:1}
.recorte .x{font-size:44px;line-height:1.25;margin-top:16px;font-weight:450;color:$sepia2}
.doc-txt .cab{display:block}
.doc-txt .cab .d{margin-top:6px}
.hl{background-image:linear-gradient($acento,$acento);background-repeat:no-repeat;background-size:0% 100%;-webkit-box-decoration-break:clone;box-decoration-break:clone;padding:2px 0}
.nota{background:$acento;padding:22px 30px 20px}
.nota .cond{font-size:96px}
.nota.cr{background:$papel}
.cita{background:$papel;padding:34px 40px 34px;border-left:14px solid $cafe}
.cita .q{font-size:56px;line-height:1.22;font-weight:600;color:#a89a80}
.cita .a{margin-top:22px;font-size:50px}
.cita .c{margin-top:6px;font-size:34px;color:$sepia2;font-weight:500}
.doc{background:$hoja;position:relative;overflow:hidden}
.doc img{display:block;position:absolute}
.doc .marca{position:absolute;background:$acento;mix-blend-mode:multiply;opacity:.85}
.tab{position:absolute;background:$tinta;color:$papel;padding:12px 22px 10px;max-width:700px}
.tab .cond{font-size:48px}
.tab .mono{font-size:22px;color:$acento;margin-bottom:4px}
.barras{background:$mesa2;border:1px solid $filo;padding:24px 34px 22px;color:$papel}
.barras .h{font-size:44px;margin-bottom:14px}
.barras .fi{height:114px;position:relative}
.barras .et{font-size:44px;display:flex;justify-content:space-between;align-items:baseline;gap:20px}
.barras .et .v{font-size:52px;white-space:nowrap}
.barras .pi{position:relative;height:30px;margin-top:10px;background:$filo}
.barras .pi b{position:absolute;left:0;top:0;bottom:0;background:$papel;transform-origin:0 50%}
.barras .ac .pi b{background:$acento}.barras .ac .v{color:$acento}
.barras .f{margin-top:12px;font-family:'JetBrains Mono',monospace;font-size:22px;color:$gris}
.mapa{background:$papel2;padding:16px}
.mapa svg{display:block;background:$mar}
.mapa .tierra{fill:$tierra;stroke:$costa;stroke-width:.8}
.mapa .gt{fill:$cafe;stroke:$tinta;stroke-width:1.2}
.mapa text{font-family:'Archivo',sans-serif;font-stretch:62%;font-weight:800;fill:$tinta;text-transform:uppercase}
.pizarra{background:$mesa2;border:3px solid $filo2;overflow:hidden}
.maqueta{overflow:hidden}
.mq-pie{position:absolute;font-family:'JetBrains Mono',monospace;font-size:22px;line-height:1.3;color:$gris}
.chip{display:inline-block;background:$papel;padding:16px 26px 12px;box-shadow:0 18px 36px rgba(0,0,0,.55);white-space:nowrap}
.chip .cond{font-size:52px}
.chip.ac{background:$acento}
.cuad{display:grid;grid-template-columns:repeat(6,40px);gap:9px;margin-top:14px}
.cuad i{display:block;width:40px;height:40px;background:$acento;opacity:0}
.cm{background:$papel;padding:14px 18px 12px;border-top:8px solid $cafe}
.cm .k{font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.08em;font-size:20px;color:$sepia;font-weight:600;white-space:nowrap;overflow:hidden}
.cm .n{font-size:50px;margin-top:4px}
.cm.osc{background:$mesa2;border:1px solid $filo;color:$papel}
.cm.osc .n{color:$acento;font-size:96px;white-space:nowrap}
.cm.osc.cr .n{color:$papel}
.cm.osc .l{font-size:34px}
.cm.ac{background:$acento;border-top:0;padding-top:16px}
.cmf{background:$papel;padding:10px 10px 0}
.cmf .im{position:relative;overflow:hidden}
.cmf .im img{position:absolute;display:block}
.cmf b{display:block;font-weight:650;font-size:28px;line-height:1.1;padding:10px 4px 10px;max-height:82px;overflow:hidden}
.nd{position:relative;background:$papel;padding:12px 14px 12px 12px;border-top:8px solid $cafe;display:flex;gap:14px;align-items:flex-start;height:164px;overflow:hidden}
.nd.inv{border-top-color:$gris}
.nd .rt{flex:none;width:118px;height:140px;position:relative;overflow:hidden;background:$papel2}
.nd .rt img{position:absolute;display:block}
.nd .nm{font-size:40px}
.nd .cg{font-size:28px;line-height:1.12;margin-top:6px;color:$sepia2;font-weight:500}
.nd .cl{position:absolute;left:0;right:0;top:0;bottom:0;background:$tinta;color:$acento;display:flex;align-items:center;justify-content:center;font-size:84px}
.etq{display:inline-block;background:$acento;padding:10px 18px 6px;font-size:38px;white-space:nowrap}
.est{display:inline-block;border:3px solid $papel;color:$papel;padding:8px 16px 4px;font-size:30px;white-space:nowrap}
.qa{color:$gris;font-size:28px;white-space:nowrap}
.rel{position:absolute;background:$mesa;color:$papel;font-size:28px;padding:3px 10px 1px;white-space:nowrap}
.cie{position:absolute;color:$papel}
.cie .li{font-size:74px;text-transform:none;line-height:1}
.cie .fin{font-size:58px;line-height:1.14;font-weight:700}
.cie .sg{font-size:120px;color:$acento}
.cie .p1{font-size:28px;font-weight:600;color:$acento;white-space:nowrap}
.cie .rd{display:flex;align-items:center;gap:26px;font-size:58px;font-weight:700;white-space:nowrap}
.cie .rd svg{flex:none;box-sizing:content-box;width:50px;height:50px;padding:16px;background:$papel;fill:$tinta;stroke:$tinta}
"""


def mezcla(c1, c2, k):
    """Un color entre dos hex (k = 0 → c1, 1 → c2)."""
    a = [int(c1.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(c2.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(int(round(x + (y - x) * k)) for x, y in zip(a, b))


def colores_v(E):
    """Los colores de la mesa: los del 16:9 más los tonos derivados (ningún hex suelto en el dibujo)."""
    C = colores(E)
    C.update(sepia=mezcla(C["tinta"], C["papel"], 0.36), sepia2=mezcla(C["tinta"], C["papel"], 0.14), sombra=mezcla(C["mesa2"], "#000000", 0.3),
             hoja=mezcla(C["papel"], "#ffffff", 0.5), mar=mezcla(C["papel2"], C["cafe"], 0.1), tierra=mezcla(C["papel2"], C["cafe"], 0.34),
             costa=mezcla(C["papel2"], C["tinta"], 0.5), luz=mezcla(C["mesa"], "#ffffff", 0.055), fondo=mezcla(C["mesa"], "#000000", 0.4),
             filo="rgba(%d,%d,%d,.22)" % tuple(int(C["papel"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)),
             filo2="rgba(%d,%d,%d,.85)" % tuple(int(C["papel"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)))
    return C


def codigo(x):
    """Un mensaje de los gates del núcleo (YT13–YT19) con el código del vertical (MV1–MV7)."""
    x = re.sub(r"\bYT(1[3-9]|2[0-4])\b", lambda m: CODIGOS[m.group(0)], x)
    return x.replace("capítulo 1:", "el video:").replace("en el 16:9 la cámara", "en la mesa la cámara")


# ---------- contexto ----------
def contexto_v(trabajo):
    import youtube as YT
    E = leer(os.path.join(trabajo, "escenas.json"))
    es = E["escenas"]
    for S in es:
        S["clave"] = "e%d" % S["n"]
    TR = E.get("transicion_s", VD.TRANSICION)
    offs, off = [], 0.0
    for k, S in enumerate(es):
        offs.append(cuadro(off))
        off += S["dur"] - (TR if k < len(es) - 1 else 0.0)
    total = cuadro(off)
    st = leer(os.path.join(trabajo, "video.json")) if os.path.exists(os.path.join(trabajo, "video.json")) else {}
    Y = {"partes": [{"trabajo": rel(trabajo)}], "base": rel(trabajo), "slug": st.get("slug") or os.path.basename(trabajo), "musica": st.get("musica"),
         "paleta": st.get("paleta"), "fixture": bool(st.get("fixture")) or "/_fixture" in "/" + rel(trabajo)}   # una maqueta: los gates avisan
    # Lo que un gate necesita y no se pudo leer NO se calla (MS.aviso_datos): queda en ctx["avisos"], `revisar` lo suma a los
    # suyos (sale en `plano --check`) y sale por stderr. Solo se atrapa lo que pasa al leer datos (MS.DATOS_ILEGIBLES).
    avisos, hechos_de = [], {}
    try:
        for k, e in enumerate(leer(os.path.join(trabajo, "guion.json")).get("escenas") or []):
            hechos_de["e%d" % (k + 1)] = e.get("hechos") or []
    except MS.DATOS_ILEGIBLES as ex:
        hechos_de = {}
        MS.aviso_datos(avisos, "MV4", "no se pudo leer %s, que dice qué hechos verificados cuenta cada escena; un número o un nombre en "
                                      "pantalla solo pasa si la voz lo dice" % rel(os.path.join(trabajo, "guion.json")), ex)
    try:
        elenco = YT.elenco_serie(Y)
    except MS.DATOS_ILEGIBLES as ex:
        elenco = []
        MS.aviso_datos(avisos, "MV4", "no se pudo leer el elenco (los `personajes` de %s y sus retratos); las fichas de persona salen sin "
                                      "retrato y a cada una se le pide `cargo` y el nombre como lo dice la voz, como a alguien de fuera del elenco"
                       % rel(os.path.join(trabajo, "encuadre.json")), ex)
    prot = None
    try:
        pr = leer(os.path.join(trabajo, "encuadre.json")).get("protagonista")
        prot = pr if isinstance(pr, str) else (pr[0] if isinstance(pr, list) and pr and isinstance(pr[0], str) else (pr[0].get("nombre") if isinstance(pr, list) and pr else None))
    except (OSError, ValueError, AttributeError):
        pass
    ctx = {"trabajo": trabajo, "E": E, "es": es, "offs": offs, "total": total, "Y": Y, "st": st, "por_clave": {S["clave"]: i for i, S in enumerate(es)},
           "caps": [{"numero": 1, "idx": list(range(len(es))), "titulo": "", "ini": 0.0, "fin": total}],
           "reglas": REGLAS, "hechos_de": hechos_de, "elenco": elenco, "doc": DOC_V, "protagonista": prot}
    try:   # el respaldo de los números en pantalla: las cifras de los datos del video, también como las redondea una tarjeta
        ctx["respaldo"] = MS.numeros_respaldo(VD.valores_respaldo(st["hilo"])[0])   # [(valor, factor de la unidad)] → números sueltos
    except MS.DATOS_ILEGIBLES as ex:
        ctx["respaldo"] = []
        donde = "datos.json e hilo.json de %s" % st["hilo"] if st.get("hilo") else "video.json no dice su `hilo`"
        MS.aviso_datos(avisos, "MV4", "no se pudo leer el respaldo de las cifras (%s); un número en pantalla solo pasa si la voz lo dice o "
                                      "está en los hechos de la mesa" % donde, ex)
    ctx["avisos"] = avisos
    ctx["seguir"] = seguir_de(ctx)
    return ctx


def seguir_de(ctx):
    """El «Sígueme» de la mitad del video (V25): el que trae la escena o, si no, hacia el 50 % (videos de ≥ 45 s). → segundo global o None."""
    for i, S in enumerate(ctx["es"]):
        if isinstance(S.get("seguir"), dict) and S["tipo"] != "cierre":
            return round(ctx["offs"][i] + float(S["seguir"].get("desde", 1.0)), 3)
    if ctx["total"] < 45:
        return None
    mitad = ctx["total"] * 0.5
    cand = [(abs(o + 1.0 - mitad), o + 1.0) for o, S in zip(ctx["offs"], ctx["es"]) if S["tipo"] not in TABLEROS_V + ("cierre",) and 0.4 <= (o + 1.0) / ctx["total"] <= 0.65]
    return round(min(cand)[1], 3) if cand else None


def resolver_v(ctx, P):
    """El plano resuelto (mesa.resolver) más lo que el vertical pone solo: el rótulo de acto de una escena abre su mesa como ficha."""
    mesas, f = MS.resolver(ctx, P)
    es, offs = ctx["es"], ctx["offs"]
    for M in mesas:
        i0 = M["idx"][0]
        R = es[i0].get("R") if isinstance(es[i0].get("R"), dict) else None
        if not R or M["clase"] not in ("mesa", "maqueta"):
            continue
        tit = " ".join(w["text"] for w in R.get("titulo") or [] if isinstance(w, dict))
        if not tit:
            continue
        cuando = str(R.get("hasta") or R.get("desde") or "")
        # nunca «Acto N de M» en pantalla (usuario, 2026-11-15): la ficha lleva solo el título, el lugar y la fecha
        o = offs[i0]
        M["golpes"] = [{"tipo": "institucion", "nombre": tit, "kicker": R.get("lugar") or "", "rol": cuando,
                        "_t": round(o + 0.05, 3), "_fin": round(o + 1.0, 3), "_i": i0, "_acto": True}] + [g for g in M["golpes"] if not g.get("_acto")]
        M["ini"] = cuadro(o)
    for k, M in enumerate(mesas):
        M["fin"] = mesas[k + 1]["ini"] if k + 1 < len(mesas) else ctx["total"]
    previo = ""
    for M in mesas:   # el golpe de arriba que sigue en pantalla cuando una mesa no trae el suyo
        if M["clase"] == "cierre":
            continue
        M.pop("_hereda", None)
        propio = titulos_de(ctx, M)
        if propio:
            previo = propio[-1][1]
        else:
            M["_hereda"] = previo
    # el «Sígueme» de la mitad: entero dentro de una mesa de piezas (si cae al final de una, pasa al inicio de la siguiente)
    ctx["seguir_en"] = None
    sg = ctx.get("seguir")
    if sg is not None:
        cand = [M for M in mesas if M["clase"] == "mesa" and M["fin"] - M["ini"] >= SEGUIR_S + 1.2]
        dentro = [M for M in cand if M["ini"] + 0.4 <= sg <= M["fin"] - SEGUIR_S - 0.6]
        M = dentro[0] if dentro else min(cand, key=lambda M: abs(M["ini"] + 0.6 - sg), default=None)
        if M is not None:
            ctx["seguir_en"] = (M["id"], round(sg if dentro else M["ini"] + 0.6, 3))
    return mesas, [codigo(x) for x in f]


# ---------- la cabecera: barra, golpe de arriba ----------
def titulos_de(ctx, M):
    """Los golpes de arriba de una mesa: [(segundo global, texto)]. El del plano (`titulo`) o el que la escena ya trae."""
    es, E = ctx["es"], ctx["E"]
    S = es[M["idx"][0]]
    if M["clase"] == "cierre":
        ci, T = E.get("cierre") or {}, S.get("T") or {}
        sig = (E.get("serie") or {}).get("siguiente") or {}
        out = [(M["ini"], ci.get("rotulo") or "Lo que dejó")]
        if sig.get("titulo"):
            out.append((round(M["ini"] + float(T.get("preg", 5.5)) - 0.15, 3), "Parte %s · %s" % (sig.get("n"), sig["titulo"])))
        return out
    t = (M.get("titulo") or "").strip()
    if not t:
        N, T, P_ = S.get("N") or {}, S.get("T") or {}, S.get("P") or {}
        if S["tipo"] == "gancho" and (T.get("pant") or {}).get("texto"):
            t = T["pant"]["texto"]
        elif S.get("arriba"):
            t = " ".join(w["text"] for w in S["arriba"] if isinstance(w, dict))
        elif N.get("titular"):
            t = " ".join(w["text"] for w in N["titular"] if isinstance(w, dict))
        elif (T.get("pant") or {}).get("texto") and S["tipo"] not in ("golpe", "definicion"):   # el golpe y la definición la ponen como pieza
            t = T["pant"]["texto"]
        elif P_.get("titulo"):
            t = P_["titulo"]
        else:   # las escenas con archivo propio (vias, lupa, deptos, cortina, red, archivo, bandos, pagina) traen su título
            t = next((str(S[k]["titulo"]) for k in ("M", "L", "D", "CO", "G", "A", "B", "PG") if isinstance(S.get(k), dict) and isinstance(S[k].get("titulo"), str) and S[k]["titulo"].strip()), "")
        t = " ".join(str(t).split()[:8]) or M.get("_hereda") or ""
    return [(M["ini"], t)] if t else []


def seguir_sitio(ctx, Fz, M, tits):
    """El «Sígueme» de la mitad en la mesa M: (píxeles que baja la mesa, y del botón) o (0, None) si no cae en ella. Si el
    golpe de arriba es corto, el botón va a su derecha y la mesa no pierde nada."""
    se = ctx.get("seguir_en")
    if not se or se[0] != M["id"]:
        return 0, None
    cabs = [cabeza(ctx, Fz, t) for _, t in tits] or [cabeza(ctx, Fz, "")]
    cab = max(cabs, key=lambda c: c["y0"])
    ancho = max([len(r) * c["px"] * 0.445 for c in cabs for r in c["renglones"]] or [0])
    if ancho <= (Fz["x1b"] - Fz["x0"]) - 310 and cab["lineas"] <= 1:
        return 0, cab["titulo"] - 2
    return 104, cab["y0"]


def cabeza(ctx, Fz, texto):
    """La geometría de la cabecera con un golpe de arriba dado: {kicker, barra, titulo, px, renglones, y0} (y0 = donde empieza
    la mesa). El golpe va en uno o dos renglones que NO se parten solos (el ancho de la condensada se estima; si un renglón
    sale algo más largo, sigue dentro de la zona segura: a esa altura llega hasta x 1023)."""
    serie = 36 if ctx["E"].get("serie") else 0
    barra = Fz["arriba"] + serie
    col = Fz["x1b"] - Fz["x0"]
    texto = " ".join((texto or "").split())
    rs = [texto] if texto else []
    if len(texto) > 21:   # dos renglones parejos
        pal = texto.split()
        k = min(range(1, len(pal)), key=lambda i: abs(len(" ".join(pal[:i])) - len(" ".join(pal[i:])))) if len(pal) > 1 else 1
        rs = [" ".join(pal[:k]), " ".join(pal[k:])] if len(pal) > 1 else [texto]
    largo = max([len(r) for r in rs] or [1])
    px = max(56, min(92, int(col / (largo * 0.445))))
    alto = int(px * 0.94)
    return {"kicker": Fz["arriba"] - 4, "barra": barra, "titulo": barra + 7 + 20, "px": px, "renglones": rs, "lineas": len(rs),
            "y0": barra + 7 + 20 + len(rs) * alto + (30 if rs else 4)}


# ---------- tamaños ----------
def texto_lectura(g):
    """El texto que una pieza pide LEER (MV8). La cita y el documento que la voz lee no cuentan: la voz los subraya."""
    t = g.get("tipo")
    if t == "cita" or (t == "documento" and g.get("lee")):
        return ""
    if t == "foto":
        txt = g.get("pie")
    elif t == "recorte":
        txt = "%s %s" % (g.get("titular") or "", (g.get("extracto") or "").replace(g.get("resalta") or "\0", " ") if g.get("resalta_dice") else g.get("extracto") or "")
    elif t in ("persona", "institucion"):
        txt = " ".join(str(g.get(c) or "") for c in ("kicker", "persona", "nombre", "cargo", "rol"))
    elif t == "cifra":
        txt = "%s %s" % (g.get("valor") or "", g.get("rotulo") or "")
    elif t == "termino":
        txt = "%s %s" % (g.get("texto") or "", g.get("definicion") or "")
    elif t == "fecha":
        txt = "%s %s" % (g.get("chico") or "", g.get("grande") or "")
    elif t == "lugar":
        txt = g.get("rotulo") or " ".join(p.get("nombre", "") for p in g.get("puntos") or [] if isinstance(p, dict))
    elif t == "lista":
        txt = " ".join((it or {}).get("texto") or "" for it in g.get("items") or [])
    elif t == "documento":
        txt = "%s %s" % (g.get("titulo") or "", g.get("subtitulo") or "")
    elif t == "barra":
        txt = "%s %s" % (g.get("titulo") or "", " ".join("%s %s" % (b.get("etiqueta") or "", b.get("texto") or b.get("valor") or "") for b in g.get("barras") or [] if isinstance(b, dict)))
    elif t == "red":
        txt = " ".join(str(x.get(c) or "") for grupo in ("nodos", "acusadores") for x in g.get(grupo) or [] if isinstance(x, dict) for c in ("nombre", "cargo"))
        txt = "%s %s %s" % (g.get("etiqueta") or "", txt, g.get("estado") or "")
    else:
        txt = ""
    return (txt or "").strip()


def palabras_de(g):
    return len(texto_lectura(g).split())


def lectura_de(ctx, g, desde, hasta):
    """Los segundos que una pieza pide al frente (MV8) y las palabras que hay que leer: las que la voz dice mientras la pieza
    está en pantalla se oyen a la vez que se ven y no cuentan (como la cita que la voz lee). → (segundos, palabras)."""
    toks = VD._plano(texto_lectura(g)).split()
    if not toks:
        return 0.0, 0
    dichas = set()
    for S, o in zip(ctx["es"], ctx["offs"]):
        if o > hasta or o + S["dur"] < desde - 0.8:
            continue
        for w in S.get("palabras") or []:
            if desde - 0.8 <= o + w["start"] <= hasta:
                for t in VD._plano(w["text"]).split():
                    dichas.add(t)
                    dichas.add(MS.EN_PALABRAS.get(t, t))
    n = sum(1 for t in toks if t not in dichas)
    return max(LECT_MIN, LECT_BASE + LECT_PALABRA * n), n


def medida_v(ctx, g, F, ancho_max, elenco):
    """(ancho, alto, extras) de una pieza en el cuadro vertical; extras["f"] = escala propia de la pieza (zoom)."""
    t = g["tipo"]
    W = min(ancho_max, int(g["w"])) if g.get("w") else ancho_max
    if t == "foto":
        r = F.get(g.get("foto")) or {}
        tw, th = (r.get("tamano") or [1600, 1000])[:2]
        rc = g.get("recorte") if isinstance(g.get("recorte"), list) and len(g["recorte"]) == 4 else [0, 0, 1, 1]
        a = (tw * rc[2]) / max(1.0, th * rc[3])
        w = min(W, 791 if a >= 1.25 else 640 if a >= 0.9 else 500)
        hi = int(min((w - 28) / a, 470 if a >= 0.9 else 560))
        hi = max(hi, int((w - 28) / 2.4))
        return w, hi + 74 + 40 * renglones(g.get("pie"), 36, w - 40, False), {"hi": hi, "a": a, "rc": rc}
    if t == "recorte":
        w = min(W, 791)
        h = 26 + 62 + (18 + 60 * renglones(g.get("titular"), 60, w - 60) if g.get("titular") else 0) + \
            (16 + 55 * renglones("«%s»" % g.get("extracto"), 44, w - 60, False) if g.get("extracto") else 0) + 28
        return w, h, {}
    if t in ("persona", "institucion") or (t == "termino" and g.get("definicion")):
        nombre = g.get("persona") or g.get("nombre") or g.get("texto") or ""
        ret = retrato_de(elenco, g) if t == "persona" else None
        w = min(W, 791 if (len(nombre) > 14 or ret) else 640)
        dentro = w - 64 - (236 if ret else 0)
        px = tam_nombre(nombre, dentro, 110, 60)
        rol = g.get("cargo") if t == "persona" else g.get("rol") if t == "institucion" else g.get("definicion")
        kicker = g.get("kicker") or ("Para entender" if t == "termino" else "")
        h = 12 + 26 + (34 * max(1, -(-len(kicker) // max(8, dentro // 20))) + 10 if kicker else 0) + int(px * 0.94) * renglones(nombre, px, dentro) + \
            (12 + 50 * renglones(rol, 42, dentro, False) if rol else 0) + (42 if g.get("fuente") else 0) + 28
        return w, max(h, 316 if ret else 0), {"px": px, "ret": ret}
    if t == "lugar":
        if g.get("mapa") == "guatemala":
            return 432, 450 + 60 + 32, {"f": 1.3}
        A = atlas(g.get("puntos") or [], min(W - 32, 759))
        return A["w"] + 32, A["h"] + 32, {"A": A}
    if t == "fecha":
        if g.get("estilo") == "calendario":
            return 380, 360, {}
        w = max(400, int(len(str(g.get("grande") or "")) * 170 * 0.43) + 92)
        return min(w, W), 280, {}
    if t == "cifra":
        v = str(g.get("valor") or "")
        px = 300 if len(v) <= 3 else 240 if len(v) <= 5 else 180 if len(v) <= 8 else 140 if len(v) <= 11 else 110
        w = min(W, max(440, int(len(v) * px * 0.44) + 72))
        cu = int(g.get("cuadros") or 0)
        h = 22 + int(px * 0.94) + 4 + 53 * renglones(g.get("rotulo"), 56, w - 70) + (14 + 49 * -(-cu // 6) if cu else 0) + (42 if g.get("fuente") else 0) + 26
        return w, h, {"px": px}
    if t == "termino":
        w = min(W, max(360, int(len(g.get("texto") or "") * 96 * 0.47) + 64))
        return w, 42 + 91 * renglones(g.get("texto"), 96, w - 60), {}
    if t == "cita":
        w = min(W, 791)
        return w, 68 + 69 * renglones("«%s»" % g.get("texto"), 56, w - 94, False) + 22 + 50 + (40 if g.get("cargo") else 0), {}
    if t == "documento":
        D = doc_de(ctx, g)
        w = min(W, D["w"])
        return w, int(D["h"] * w / D["w"]), {"D": D, "k": w / D["w"]}
    if t == "red":
        niveles = sorted({int(n.get("nivel") or 0) for n in g.get("nodos") or [] if isinstance(n, dict)})
        h = (64 if g.get("etiqueta") else 0) + max(1, len(niveles)) * RED_PASO - (RED_PASO - RED_ALTO) + (44 + RED_ALTO if g.get("acusadores") else 0) + \
            (62 if g.get("estado") else 0)
        return 791, h, {"niveles": niveles}
    if t == "barra":
        bs = [b for b in g.get("barras") or [] if isinstance(b, dict)]
        return 791, 24 + (62 if g.get("titulo") else 0) + BARRA_FILA * max(1, len(bs)) + (40 if g.get("fuente") else 0) + 10, {}
    if t == "lista":
        largo = max([len((it or {}).get("texto") or "") for it in g.get("items") or []] or [6])
        ficha_w = int(largo * 52 * 0.455) + 56
        corr = max(0, min(160, W - ficha_w - 40))
        return min(W, ficha_w + corr + 40), 104 * len(g.get("items") or []) + (70 if g.get("lazo") else 20), {"ficha_w": ficha_w, "corr": corr}
    return 400, 200, {}


def compacta(ctx, g, F, elenco):
    """La versión compacta de una pieza (lo que queda arriba tras el repliegue): (ancho, alto, HTML, activos) o None si no deja nada."""
    t = g.get("tipo")
    if t == "lista" or g.get("_acto"):
        return None
    if t == "foto":
        r = F.get(g.get("foto")) or {}
        if not r.get("archivo"):
            return None
        tw, th = (r.get("tamano") or [1600, 1000])[:2]
        rc = g.get("recorte") if isinstance(g.get("recorte"), list) and len(g["recorte"]) == 4 else [0, 0, 1, 1]
        wi, hi = 280, 170
        pie = " ".join((g.get("pie") or "").split()[:5])
        cw, ch = tw * rc[2], th * rc[3]
        s = max(wi / cw, hi / ch)
        fx, fy = (g.get("pos") or [0.5, 0.4])[:2]
        ix = -(rc[0] * tw * s) - max(0, cw * s - wi) * fx
        iy = -(rc[1] * th * s) - max(0, ch * s - hi) * fy
        return 300, 10 + hi + 12 + 31 * min(2, renglones(pie, 28, 270, False)) + 10, ('<div class="cmf"><div class="im" style="width:%dpx;height:%dpx"><img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx" alt=""></div>'
                                   '<b>%s</b></div>' % (wi, hi, r["archivo"], ix, iy, tw * s, th * s, esc(pie))), [r["archivo"]]
    if t == "barra":
        bs = [b for b in g.get("barras") or [] if isinstance(b, dict)]
        b = next((b for b in bs if b.get("acento")), bs[-1] if bs else None)
        if not b:
            return None
        g = {"tipo": "cifra", "valor": b.get("texto") or b.get("valor"), "rotulo": b.get("etiqueta") or "", "crema": g.get("crema")}
        t = "cifra"
    if t == "cifra":
        v = str(g.get("valor") or "")
        w = min(COMPACTA_ANCHO, max(240, int(len(v) * 96 * 0.44) + 40))
        rot = " ".join((g.get("rotulo") or "").split()[:5])
        return w, 14 + 92 + 34 * renglones(rot, 34, w - 38) + 16, ('<div class="cm osc%s"><div class="n cond">%s</div><div class="l cond">%s</div></div>'
                                                                 % (" cr" if g.get("crema") else "", esc(v), esc(rot))), []
    if t == "termino" and not g.get("definicion"):
        txt = g.get("texto") or ""
        w = min(COMPACTA_ANCHO, max(200, int(len(txt) * 50 * 0.47) + 40))
        return w, 30 + 48 * renglones(txt, 50, w - 36), '<div class="cm%s"><div class="n cond" style="margin-top:0">%s</div></div>' % ("" if g.get("crema") else " ac", esc(txt)), []
    if t == "persona":
        n = g.get("persona") or ""
    elif t == "institucion":
        n = g.get("nombre") or ""
    elif t == "termino":
        n = g.get("texto") or ""
    elif t == "recorte":
        n = g.get("medio") or "Prensa"
    elif t == "documento":
        n = g.get("titulo") or "Documento"
    elif t == "cita":
        n = g.get("autor") or ""
    elif t == "lugar":
        n = g.get("rotulo") or g.get("depto") or next((p.get("nombre") for p in reversed(g.get("puntos") or []) if isinstance(p, dict)), "")
    elif t == "fecha":
        n = " ".join(str(x) for x in (g.get("grande"), g.get("arriba")) if x)
    else:
        return None
    if not n:
        return None
    px = 50 if len(n) <= 22 else 42
    w = min(COMPACTA_ANCHO, max(200, int(len(n) * px * 0.5) + 60))   # holgada: si el nombre se parte, la compacta pisa lo de abajo
    return w, 8 + 16 + int(px * 0.96) * renglones(n, px, w - 36) + 14, '<div class="cm"><div class="n cond" style="font-size:%dpx;margin-top:0">%s</div></div>' % (px, esc(n)), []


# ---------- la mesa vertical: colocación por regla, con repliegue ----------
def componer(ctx, M, fmt, F, elenco):
    """Dónde va cada pieza de una mesa en un formato y cuándo se repliega → {cab, piezas, compactas, fallas}.
    Las piezas bajan en fila (una a la izquierda, la siguiente a la derecha); cuando la que entra no cabe debajo, o ya hay
    PILA_LEGIBLES al frente, las de al frente pasan de un corte a su versión compacta, arriba, y la mesa sigue debajo."""
    if M["clase"] == "maqueta":
        return componer_maqueta(ctx, M, fmt, F, elenco)
    Fz = FORMATOS[fmt]
    tits = titulos_de(ctx, M)
    cab = max((cabeza(ctx, Fz, t) for _, t in tits), key=lambda c: c["y0"]) if tits else cabeza(ctx, Fz, "")
    y0, Y1, x0 = cab["y0"], Fz["y1"], Fz["x0"]
    y0 += seguir_sitio(ctx, Fz, M, tits)[0]   # la esquina del «Sígueme», si el golpe de arriba no le deja sitio a su lado
    nom = "%s E%s" % (M["id"], "–".join(str(ctx["es"][i]["n"]) for i in dict.fromkeys((M["idx"][0], M["idx"][-1]))))
    out, comp, fallas = [], [], []
    frente, tira, base, cur = [], [], y0, y0
    fila = None   # la última pieza chica puesta: otra chica cabe a su lado
    grandes = 0
    fin_mesa = M["fin"] - (0.46 if M.get("_barre", True) else 0.0)

    def lim(yb):
        return Fz["x1"] if yb <= Fz["yb"] else Fz["x1b"]

    def replegar(t_rep):
        nonlocal frente, tira, base, cur, fila
        for c in tira:
            c["hasta"] = t_rep
        nuevas = []
        for p in frente:
            p["hasta"] = t_rep
            c = compacta(ctx, p["g"], F, elenco)
            if c:
                e_ = Fz.get("escala", 1.0)
                nuevas.append({"g": p["g"], "w": int(c[0] * e_), "h": int(c[1] * e_), "desde": t_rep, "hasta": None, "activos": c[3],
                               "html": c[2] if e_ == 1 else '<div style="zoom:%.3f;width:%dpx">%s</div>' % (e_, c[0], c[2])})
        tira = nuevas[-PILA_COMPACTAS:]
        x, alto = x0, 0
        for j, c in enumerate(tira):
            if j and x + c["w"] > Fz["x1b"]:
                c["x"], c["y"] = Fz["x1b"] - c["w"], y0 + 26
            else:
                c["x"], c["y"] = x, y0
            x = c["x"] + c["w"] + 14
            alto = max(alto, c["y"] - y0 + c["h"])
            c["giro"] = (-1.5, 1.2)[j % 2]
        comp.extend(tira)
        base = y0 + alto + (18 if tira else 0)
        cur, frente, fila = base, [], None

    for k, g in enumerate(M["golpes"]):
        t = g["_t"]
        g.setdefault("giro", GIROS_V[k % len(GIROS_V)])
        ancho = (Fz["x1"] if fmt == "4:5" else Fz["x1b"]) - x0
        w, h, ex = medida_v(ctx, g, F, min(ancho, 860), elenco)
        f = float(ex.get("f", 1.0)) * Fz.get("escala", 1.0)
        wv, hv = int(w * f), int(h * f)
        if g["tipo"] == "documento" and g.get("pagina") and not g.get("w"):
            # la página de un documento usa todo el ancho que la zona deja sobre los iconos: su letra es la más chica de la mesa
            w2, h2, ex2 = medida_v(ctx, g, F, Fz["x1"] - x0, elenco)
            if (cur if (not frente or cur + int(h2 * f) <= Y1) else y0) + int(h2 * f) <= Fz["yb"]:
                w, h, ex = w2, h2, ex2
                wv, hv = int(w * f), int(h * f)
        junto = None
        if fila and wv <= 470 and len(frente) < PILA_LEGIBLES + 1:
            yj = fila["y"] + 22
            if fila["x_fin"] + 14 + wv <= lim(max(yj + hv, fila["y"] + fila["h"])) and yj + hv <= Y1:
                junto = (lim(max(yj + hv, fila["y"] + fila["h"])) - wv, yj)
        if junto:
            p = {"g": g, "x": junto[0], "y": junto[1], "w": w, "h": h, "ex": ex, "f": round(f, 3), "wv": wv, "hv": hv, "t": t, "hasta": None, "k": k}
            frente.append(p)
            out.append(p)
            cur = max(cur, junto[1] + hv + 14)
            fila = None
            continue
        if frente and g.get("limpia"):   # el plano pide el corte aquí: lo anterior se repliega antes de que entre esta pieza
            replegar(round(t - LEAD, 3))
        if frente and (cur + hv > Y1 or len(frente) >= PILA_LEGIBLES):
            # antes de replegar a una pieza que aún se está leyendo: si la nueva cabe algo más chica, entra chica
            pend = [p for p in frente if not p["g"].get("_ya") and (t - LEAD) - p["t"] < lectura_de(ctx, p["g"], p["t"], t - LEAD)[0] - 0.05]
            f2 = (Y1 - cur) / float(hv) if hv else 1.0
            if pend and len(frente) < PILA_LEGIBLES and f2 >= 0.8:
                f *= f2
                wv, hv = int(w * f), int(h * f)
            else:
                replegar(round(t - LEAD, 3))
        if cur + hv > Y1:   # sola en la mesa y aún no cabe: a escala
            f *= max(0.4, (Y1 - cur) / float(hv))
            wv, hv = int(w * f), int(h * f)
        tope = lim(cur + hv) - x0
        if wv > tope:
            f *= tope / float(wv)
            wv, hv = int(w * f), int(h * f)
        tope = lim(cur + hv) - x0
        if wv >= tope - 50:
            x = x0 + (tope - wv) // 2
        elif wv > 470:   # las hojas grandes alternan de lado
            x = x0 if grandes % 2 == 0 else x0 + tope - wv
            grandes += 1
        else:            # una chica va a la izquierda tras una grande (otra chica cabe a su lado); dos chicas seguidas alternan
            x = x0 if (not frente or frente[-1]["wv"] > 470 or frente[-1]["x"] > x0 + 20) else x0 + tope - wv
        p = {"g": g, "x": x, "y": cur, "w": w, "h": h, "ex": ex, "f": round(f, 3), "wv": wv, "hv": hv, "t": t, "hasta": None, "k": k}
        frente.append(p)
        out.append(p)
        fila = {"y": cur, "x_fin": x + wv, "h": hv} if wv <= 470 and x == x0 else None
        cur += hv + 14
        if f < ESCALA_MIN - 0.001:
            fallas.append("MV11 %s golpe %d (%s, %s): no cabe en la mesa (se dibujaría al %d %%): acorta su texto, o parte la mesa"
                          % (nom, k + 1, g["tipo"], fmt, round(100 * f)))
        if p["y"] + hv > Y1 + 4 or x < x0 - 2 or x + wv > lim(p["y"] + hv) + 2:
            fallas.append("MV10 %s golpe %d (%s, %s): sale de la zona segura" % (nom, k + 1, g["tipo"], fmt))
    # MV8: cada texto, su tiempo al frente
    for p in out:
        if p["g"].get("_ya") or not palabras_de(p["g"]):
            continue
        hasta = p["hasta"] if p["hasta"] is not None else fin_mesa
        pide, n = lectura_de(ctx, p["g"], p["t"], hasta)
        if hasta - p["t"] < pide - 0.05:
            fallas.append("MV8 %s golpe %d (%s «%s»): queda %.1f s al frente y pide %.1f s (%d palabras que la voz no dice): acorta el texto, quita la "
                          "pieza que la desplaza, o parte la mesa" % (nom, p["k"] + 1, p["g"]["tipo"], resumen_golpe(p["g"])[:40], hasta - p["t"], pide, n))
    # MV13: un solo acento al frente a la vez (la que ya se replegó va atenuada, arriba, y no cuenta). Falla si un dato (cifra,
    # barra) comparte el acento con otro dato o con un bloque; lo demás se avisa (MS.acento_compite dice por qué)
    avisos = []
    for b, antes in MS.acentos_a_la_vez(out, fin_mesa):
        cuales = lambda ps: " y ".join("%s (golpe %d)" % (MS.en_acento(a_["g"]), a_["k"] + 1) for a_ in ps)
        graves = [a_ for a_ in antes if MS.acento_compite(a_["g"], b["g"])]
        leves = [a_ for a_ in antes if a_ not in graves]
        cabeza_ = "MV13 %s golpe %d (%s, %s): %s entra a los %.1f s y " % (nom, b["k"] + 1, b["g"]["tipo"], fmt, MS.en_acento(b["g"]), b["t"])
        if graves:
            fallas.append(cabeza_ + "%s sigue%s al frente en acento: un solo acento a la vez, y con una cifra en pantalla el acento es solo suyo. Pon "
                          "`\"crema\": true` en la que no es el dato que la voz está diciendo (cifra, nota o barra), `\"limpia\": true` en la que entra (repliega lo "
                          "anterior), quita el `acento` de la lista, o llévala a otra mesa" % (cuales(graves), "n" if len(graves) > 1 else ""))
        if leves:
            avisos.append(cabeza_ + "%s sigue%s al frente en acento: dos acentos a la vez. Si compiten, deja uno: `\"crema\": true` (cifra, nota o barra), "
                          "`\"limpia\": true` en la que entra, o quita el subrayado o el lazo que sobra" % (cuales(leves), "n" if len(leves) > 1 else ""))
    return {"cab": cab, "tits": tits, "piezas": out, "compactas": comp, "fallas": fallas, "avisos": avisos, "y0": y0}


def marco_clip(ctx, M, fmt):
    """El marco del clip de la maqueta de una mesa: como el de un tablero (centrado en la columna segura, con la proporción
    del lienzo y hasta donde deja la cabecera) → {x, y, w, h, cab, tits}."""
    Fz = FORMATOS[fmt]
    tits = titulos_de(ctx, M)
    cab = max((cabeza(ctx, Fz, t) for _, t in tits), key=lambda c: c["y0"]) if tits else cabeza(ctx, Fz, "")
    ancho = Fz["x1b"] - Fz["x0"]
    alto = int(ancho * TABLERO_LADOS[1] / float(TABLERO_LADOS[0]))
    if cab["y0"] + alto > Fz["y1"]:
        alto = Fz["y1"] - cab["y0"]
        ancho = int(alto * TABLERO_LADOS[0] / float(TABLERO_LADOS[1]))
    margen = int(MAQUETA_MARGEN * ancho / float(TABLERO_LADOS[0]))
    return {"x": Fz["x0"] + (Fz["x1b"] - Fz["x0"] - ancho) // 2, "y": cab["y0"] + max(0, (Fz["y1"] - cab["y0"] - alto) // 3), "w": ancho, "h": alto,
            "cab": cab, "tits": tits, "margen": margen, "pie": MS.credito_maqueta_alto(M["maqueta"], ancho - 2 * margen, MAQUETA_PIE_PX)[1]}


def componer_maqueta(ctx, M, fmt, F, elenco):
    """Las piezas que caen SOBRE la maqueta de una mesa: una a la vez, abajo a la izquierda del marco (donde la maqueta suelta
    pone su cifra), sin taparle más de MAQUETA_GOLPE_ALTO; cada una se va de un corte cuando entra la siguiente (o se barre con
    la mesa). No hay repliegue: la maqueta es lo que se mira. → lo mismo que `componer`."""
    Fz = FORMATOS[fmt]
    K = marco_clip(ctx, M, fmt)
    margen, pie = K["margen"], K["pie"] + 22   # la pieza (girada) no tapa el pie del marco
    nom = "%s E%s" % (M["id"], "–".join(str(ctx["es"][i]["n"]) for i in dict.fromkeys((M["idx"][0], M["idx"][-1]))))
    out, fallas = [], []
    fin_mesa = M["fin"] - (0.46 if M.get("_barre", True) else 0.0)
    gs = M["golpes"]
    for k, g in enumerate(gs):
        g.setdefault("giro", GIROS_V[k % len(GIROS_V)])
        w, h, ex = medida_v(ctx, g, F, min(K["w"] - 2 * margen, 860), elenco)
        f = float(ex.get("f", 1.0)) * Fz.get("escala", 1.0)
        f = min(f, K["h"] * MAQUETA_GOLPE_ALTO / float(max(1, h)), (K["w"] - 2 * margen) / float(max(1, w)))
        wv, hv = int(w * f), int(h * f)
        p = {"g": g, "x": K["x"] + margen, "y": K["y"] + K["h"] - pie - hv, "w": w, "h": h, "ex": ex, "f": round(f, 3), "wv": wv, "hv": hv, "t": g["_t"],
             "hasta": round(gs[k + 1]["_t"] - LEAD, 3) if k + 1 < len(gs) else None, "k": k}
        out.append(p)
        if f < ESCALA_MIN * Fz.get("escala", 1.0) - 0.001:
            fallas.append("MV11 %s golpe %d (%s, %s): sobre la maqueta se dibujaría al %d %% (no puede taparle más del %d %% del alto): ahí va una cifra, una fecha "
                          "o una nota corta; lo demás, en otra mesa" % (nom, k + 1, g["tipo"], fmt, round(100 * f / Fz.get("escala", 1.0)), round(100 * MAQUETA_GOLPE_ALTO)))
    for p in out:   # MV8: cada texto, su tiempo al frente
        if p["g"].get("_ya") or not palabras_de(p["g"]):
            continue
        hasta = p["hasta"] if p["hasta"] is not None else fin_mesa
        pide, n = lectura_de(ctx, p["g"], p["t"], hasta)
        if hasta - p["t"] < pide - 0.05:
            fallas.append("MV8 %s golpe %d (%s «%s»): queda %.1f s sobre la maqueta y pide %.1f s (%d palabras que la voz no dice): acorta el texto, o quita la "
                          "pieza que la reemplaza" % (nom, p["k"] + 1, p["g"]["tipo"], resumen_golpe(p["g"])[:40], hasta - p["t"], pide, n))
    return {"cab": K["cab"], "tits": K["tits"], "piezas": out, "compactas": [], "fallas": fallas, "y0": K["cab"]["y0"], "marco": K}


def retrato_nodo(ctx, n, F):
    """El retrato de un nodo de la jerarquía: (archivo, ancho, alto, foco) o None. Sale de su `foto` (id o ruta, con `foco`) o del elenco (`persona`)."""
    arch, foco = None, n.get("foco") if isinstance(n.get("foco"), dict) else None
    if n.get("foto"):
        r = F.get(n["foto"]) or next((r for r in F.values() if r.get("archivo") == n["foto"]), None)
        arch = (r or {}).get("archivo")
    if not arch and (n.get("persona") or n.get("nombre")):
        p = retrato_de(ctx["elenco"], {"persona": n.get("persona") or n.get("nombre")})
        if p:
            arch, foco = p["foto"], foco or p.get("foco")
    if not arch:
        return None
    r = next((r for r in F.values() if r.get("archivo") == arch), {})
    tw, th = (r.get("tamano") or [800, 800])[:2]
    return arch, tw, th, foco if foco and "x" in foco else None


def dibujar_red(ctx, m, g, x, y, w, h, ex, k, F, usados):
    """La jerarquía de personas: cartas por nivel (retrato, nombre, cargo), hilos entre ellas (sólido = hecho; punteado =
    alegato, con la etiqueta «Según…» arriba, que entra ANTES que las caras), quien acusa aparte y sin hilos, y el estado del
    caso abajo. Cada carta entra cuando la voz la nombra; una carta con `clave` entra como clave («El Uno») y se voltea a la
    cara cuando la voz dice el nombre."""
    C, T, f = ctx["C"], g["_t"], m.f
    S, o = ctx["es"][g["_i"]], ctx["offs"][g["_i"]]

    def t_de(frase, por):
        r = buscar(S, frase or "", 0) if frase else None
        return round(o + S["palabras"][r[1]]["start"], 3) if r else por
    nodos = [n for n in g.get("nodos") or [] if isinstance(n, dict)]
    acus = [n for n in g.get("acusadores") or [] if isinstance(n, dict)][:RED_ACUSADORES]
    niveles = ex.get("niveles") or [0]
    y0 = 64 if g.get("etiqueta") else 0
    if g.get("etiqueta"):
        m.pieza(T, x, y, 10, -1.5, '<div class="etq cond">%s</div>' % esc(g["etiqueta"]), sfx="papel", sombra=True)
    pos, ult = {}, T + 0.3

    def carta(n, cx, cy, clase, j):
        nonlocal ult
        nid = "%s-n%d" % (m.id, m.k + 1)
        rt = retrato_nodo(ctx, n, F)
        img = ""
        if rt:
            arch, tw, th, fo = rt
            usados.add(arch)
            if fo:
                s = 118 / max(1.0, fo["w"] * tw * 1.9)
                ix, iy = 59 - (fo["x"] + fo["w"] / 2) * tw * s, 62 - (fo["y"] + fo["h"] / 2) * th * s
            else:
                s = max(118 / tw, 140 / th)
                ix, iy = (118 - tw * s) / 2, (140 - th * s) / 2
            img = '<div class="rt"><img src="assets/%s" style="left:%.0fpx;top:%.0fpx;width:%.0fpx" alt=""></div>' % (arch, ix, iy, tw * s)
        tn = max(T + 0.35 + 0.12 * j, t_de(n.get("dice"), ult + 0.5))
        tc = t_de(n.get("clave_dice"), None) if n.get("clave") else None
        entra = max(T + 0.35 + 0.12 * j, min(tn, tc)) if tc is not None else tn
        ult = max(ult, entra)
        dentro = ('<div class="nd%s">%s<div><div class="nm cond">%s</div>%s</div>%s</div>'
                  % (clase, img, esc(n.get("nombre")), '<div class="cg">%s</div>' % esc(n["cargo"]) if n.get("cargo") else "",
                     '<div id="%s-cl" class="cl cond">%s</div>' % (nid, esc(n["clave"])) if tc is not None and tc < tn - 0.2 else ""))
        m.pieza(entra, x + int(cx * f), y + int(cy * f), RED_CARTA, (-1.2, 1.2, -0.8, 1)[j % 4], dentro, sfx="papel" if j % 2 == 0 else None)
        if tc is not None and tc < tn - 0.2:   # la clave se voltea a la cara
            m.tl.append('tl.fromTo("#%s-cl",{scaleX:1,opacity:1},{scaleX:0,opacity:1,duration:.16,ease:"power2.in"},%.3f);' % (nid, m.loc(tn - 0.16)))
            m.tl.append('tl.set("#%s-cl",{opacity:0},%.3f);' % (nid, m.loc(tn)))
            m.sfx.append((tn, "impacto"))
            ult = max(ult, tn)
        if n.get("id"):
            pos[n["id"]] = (cx, cy, max(entra, tn))

    j = 0
    for li, niv in enumerate(niveles):
        fila = [n for n in nodos if int(n.get("nivel") or 0) == niv][:RED_POR_NIVEL]
        for q, n in enumerate(fila):
            cx = (791 - RED_CARTA) // 2 if len(fila) == 1 else (0 if q == 0 else 791 - RED_CARTA)
            carta(n, cx, y0 + li * RED_PASO, "", j)
            j += 1
    # los hilos: de la carta de abajo a la de arriba; punteado = alegato
    lineas, anim = "", []
    for q, a in enumerate(g.get("aristas") or []):
        if not isinstance(a, dict) or a.get("de") not in pos or a.get("a") not in pos:
            continue
        (x1, y1, t1), (x2, y2, t2) = pos[a["de"]], pos[a["a"]]
        if y1 < y2:
            (x1, y1), (x2, y2) = (x2, y2), (x1, y1)
        ax, ay, bx, by = (x1 + RED_CARTA / 2) * f, (y1 + 4) * f, (x2 + RED_CARTA / 2) * f, (y2 + RED_ALTO + 4) * f
        ta = max(t1, t2) + 0.25
        ta = max(ta, t_de(a.get("dice"), ta))
        lid = "%s-h%d-%d" % (m.id, m.k, q)
        lineas += ('<clipPath id="%s-c"><rect id="%s-r" x="0" y="%.0f" width="%d" height="0"/></clipPath><line clip-path="url(#%s-c)" x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
                   'stroke="%s" stroke-width="%d" stroke-linecap="round"%s/>' % (lid, lid, ay, int(w * f) + 40, lid, ax, ay, bx, by, C["papel"], 8 if a.get("atribuida") else 10,
                                                                             ' stroke-dasharray="4 20"' if a.get("atribuida") else ""))
        anim.append('tl.fromTo("#%s-r",{attr:{y:%.0f,height:0}},{attr:{y:%.0f,height:%.0f},duration:.5,ease:"power1.inOut"},%.3f);' % (lid, ay, by, max(1.0, ay - by), m.loc(ta)))
        m.sfx.append((ta, "marcador"))
        ult = max(ult, ta)
    if lineas:
        sid = "%s-hs%d" % (m.id, m.k)
        m.html.append('<svg id="%s" class="pz" style="left:%dpx;top:%dpx;z-index:8" width="%d" height="%d" data-layout-ignore>%s</svg>' % (sid, x, y, int(w * f) + 40, int(h * f) + 20, lineas))
        m.tl += anim
        m.extra.append("#" + sid)
    ya = y0 + len(niveles) * RED_PASO - (RED_PASO - RED_ALTO)
    if acus:
        ta0 = max(T + 0.5, min([t_de(n.get("dice"), 10 ** 6) for n in acus] + [ult + 0.6]) - 0.3)
        m.pieza(ta0, x, y + int((ya + 8) * f), 10, 0, '<div class="qa mono">%s</div>' % esc(g.get("acusa") or "Quién acusa"), sfx=None, sombra=False)
        for q, n in enumerate(acus):
            carta(n, 0 if q == 0 else 791 - RED_CARTA, ya + 44, " inv", j)
            j += 1
        ya += 44 + RED_ALTO
    if g.get("estado"):
        m.pieza(max(ult + 0.4, t_de(g.get("estado_dice"), ult + 0.6)), x, y + int((ya + 14) * f), 10, 0, '<div class="est mono">%s</div>' % esc(g["estado"]), sfx="sello", sombra=False)


def valor_num(v):
    """«Q45,259», «1.8 veces», 46.1 → 45259.0, 1.8, 46.1 (None si no hay número)."""
    if isinstance(v, (int, float)):
        return float(v)
    m_ = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(v or ""))
    return float(m_.group(0).replace(",", "")) if m_ else None


def dibujar_barra(ctx, m, g, x, y, w, h, ex, k, F, usados):
    """La cifra con su medida: 2–5 barras (etiqueta, valor) a la misma escala. La pieza entra con su rótulo y cada barra
    crece cuando la voz dice su valor (o su `dice`); la que lleva `acento` (o la última) va en el color de acento."""
    C, T = ctx["C"], g["_t"]
    S, o = ctx["es"][g["_i"]], ctx["offs"][g["_i"]]
    bs = [b for b in g.get("barras") or [] if isinstance(b, dict)][:BARRAS_MAX]
    vals = [valor_num(b.get("valor")) or 0.0 for b in bs]
    tope = max(vals + [1e-9])
    ac = -1 if g.get("crema") else next((j for j, b in enumerate(bs) if b.get("acento")), len(bs) - 1)   # en crema ninguna destaca (MV13)
    pid = "%s-b%d" % (m.id, m.k + 1)
    filas = "".join('<div class="fi%s"><div class="et cond"><span>%s</span><span class="v">%s</span></div><div class="pi"><b id="%s-%d" style="width:%.1f%%"></b></div></div>'
                    % (" ac" if j == ac else "", esc(b.get("etiqueta")), esc(str(b.get("texto") or (num_txt(b["valor"]) if valor_num(b.get("valor")) is not None else ""))), pid, j, 100.0 * max(0.0, v) / tope)
                    for j, (b, v) in enumerate(zip(bs, vals)))
    dentro = '<div class="barras">%s%s%s</div>' % ('<div class="h cond">%s</div>' % esc(g["titulo"]) if g.get("titulo") else "", filas,
                                                  '<div class="f">%s</div>' % esc(g["fuente"]) if g.get("fuente") else "")
    m.pieza(T, x, y, w, max(-1.5, min(1.5, GIROS_V[k % len(GIROS_V)])), dentro, sfx="papel", ya=g.get("_ya", False))

    def t_de(frase, por):
        r = buscar(S, frase or "", 0) if frase else None
        return round(o + S["palabras"][r[1]]["start"], 3) if r else por
    t_prev = T + 0.15
    for j, b in enumerate(bs):
        td = t_de(b.get("dice"), None)
        if T > o + S["dur"] or (td is not None and td < T - 0.5):   # la vuelta del bucle (el cuadro 0 otra vez): las barras ya están llenas
            m.tl.append('tl.set("#%s-%d",{scaleX:1},0);' % (pid, j))
            continue
        tj = max(t_prev, td if td is not None else t_prev + (0.35 if j else 0.15))
        m.tl.append('tl.fromTo("#%s-%d",{scaleX:0},{scaleX:1,duration:.55,ease:"power3.out"},%.3f);' % (pid, j, m.loc(tj)))
        m.sfx.append((tj + 0.1, "impacto" if j == ac else "tic"))
        t_prev = tj + 0.2


class MesaV(Mesa):
    """Una mesa del cuadro vertical: piezas que pueden terminar antes del barrido (repliegue) y compactas sin entrada."""

    def __init__(self, mid, ini, fin, barrer, css, Fz):
        super().__init__(mid, ini, fin, barrer, css, ancho=Fz["w"], alto=Fz["h"], centro=(400, 680), medio_y=(Fz["y1"] + 420) // 2, barrido=-1500)
        self.hasta = None

    def pieza(self, g, x, y, w, giro, dentro, sfx="papel", ya=False, sombra=True, velo=True):
        pid = super().pieza(g, x, y, w, giro, dentro, sfx=sfx, ya=ya, sombra=sombra, velo=False)
        if self.hasta is not None:
            p = self.piezas[-1]
            p["fin"] = self.loc(self.hasta)
            self.html[-1] = re.sub(r'data-duration="[\d.]+"', 'data-duration="%.3f"' % max(0.1, round(p["fin"] - p["t0"], 3)), self.html[-1], count=1)
        return pid

    def estatica(self, x, y, w, giro, dentro, desde, hasta=None):
        self.k += 1
        pid = "%s-c%d" % (self.id, self.k)
        t0 = self.loc(desde)
        fin = self.loc(hasta) if hasta is not None else round(self.fin - self.ini, 3)
        self.html.append('<div id="%s" class="clip pz" data-start="%.3f" data-duration="%.3f" data-track-index="%d" data-layout-allow-overlap '
                         'data-layout-allow-occlusion style="left:%dpx;top:%dpx;width:%dpx;z-index:%d"><div id="%s-mov" class="mov"><div class="pila">%s'
                         '<i class="velo" style="opacity:.5"></i></div></div></div>' % (pid, t0, max(0.1, round(fin - t0, 3)), 1 + self.k % 6, x, y, w, 4 + self.k % 4, pid, dentro))
        self.tl.append('tl.fromTo("#%s-mov",{rotation:%s,opacity:0},{rotation:%s,opacity:1,duration:.14,ease:"none"},%.3f);' % (pid, giro, giro, t0))
        self.piezas.append(dict({"id": pid, "t0": t0, "giro": giro, "velo": False}, **({"fin": fin} if hasta is not None else {})))
        return pid

    def cerrar(self):
        todas = self.piezas
        self.piezas = [p for p in todas if "fin" not in p]   # el barrido se lleva solo lo que sigue en la mesa
        try:
            return super().cerrar()
        finally:
            self.piezas = todas


def iconos_redes():
    """Los logos de las redes del cierre (los de video/cierre.html: una sola fuente)."""
    if not hasattr(iconos_redes, "c"):
        s = open(os.path.join(RAIZ, "video", "cierre.html"), encoding="utf-8").read()
        blo = s[s.index("const ICONOS = {"):]
        blo = blo[:blo.index("};")]
        iconos_redes.c = {m.group(1): m.group(2) for m in re.finditer(r"^\s*(\w+):\s*'(.*)',\s*$", blo, re.M)}
    return iconos_redes.c


def mesa_html_v(ctx, M, F, elenco, usados, fmt, primera=False, ultima=False):
    """Una mesa del video vertical → (HTML de su composición, efectos [(t, id)], lo compuesto)."""
    es, C = ctx["es"], ctx["C"]
    Fz = FORMATOS[fmt]
    m = MesaV(M["id"], M["ini"], M["fin"], barrer=not ultima, css=ctx["css"], Fz=Fz)
    S = es[M["idx"][0]]
    d = M["fin"] - M["ini"]
    M["_barre"] = not ultima
    if M["clase"] == "cierre":
        E = ctx["E"]
        ci, T = E.get("cierre") or {}, S.get("T") or {}
        tits = titulos_de(ctx, M)
        cab = max((cabeza(ctx, Fz, t) for _, t in tits), key=lambda c: c["y0"])
        y0, x0, col = cab["y0"] + 16, Fz["x0"], Fz["x1b"] - Fz["x0"]
        rs = (ci.get("resumen") or [])[:3]
        ts = list(T.get("r") or [0.1, 1.6, 3.5])[:len(rs)]
        t_b = float(T.get("preg", 5.5))
        t_s = float(T.get("sigue", t_b + 4.0))
        y = y0 + 40
        for j, r in enumerate(rs):
            m.html.append('<div id="%s-r%d" class="cie clip" data-start="0" data-duration="%.3f" data-track-index="%d" style="left:%dpx;top:%dpx;width:%dpx">'
                          '<div id="%s-r%d-in" class="li cond"%s>%s</div></div>' % (m.id, j, max(0.3, t_b - 0.05), 1 + j, x0, y, col, m.id, j,
                                                                                   ' style="color:%s"' % C["acento"] if j == len(rs) - 1 else "", esc(r)))
            y += 74 * renglones(r, 74, col) + 96
            m.tl.append('tl.fromTo("#%s-r%d-in",{x:-60,opacity:0},{x:0,opacity:1,duration:.45,ease:"power3.out"},%.3f);' % (m.id, j, max(0.0, ts[j] - 0.1)))
            m.tl.append('tl.fromTo("#%s-r%d-in",{x:0,opacity:1},{x:-1500,opacity:1,duration:.4,ease:"power2.in",immediateRender:false},%.3f);' % (m.id, j, max(0.2, t_b - 0.5)))
            m.sfx.append((M["ini"] + ts[j], "papel"))
        m.sfx.append((M["ini"] + t_b - 0.45, "whoosh"))
        fin_txt = ci.get("final") or ""
        redes = [r for r in E.get("redes") or [] if r.get("red") in iconos_redes()]
        parte = int((E.get("serie") or {}).get("parte") or 0)
        if parte >= 2:   # una parte suelta de la serie: por dónde empezar (flujo-serie.md)
            m.html.append('<div id="%s-p1" class="cie clip" data-start="%.3f" data-duration="%.3f" data-track-index="6" style="left:%dpx;top:%dpx;width:%dpx">'
                          '<div id="%s-p1-in" class="p1 mono">Empieza por la Parte 1 · fijada en mi perfil</div></div>' % (m.id, t_b, d - t_b, x0, y0, col, m.id))
            m.tl.append('tl.fromTo("#%s-p1-in",{opacity:0},{opacity:1,duration:.4,ease:"none"},%.3f);' % (m.id, t_b))
            y0 += 52
        h_fin = 66 * renglones(fin_txt, 58, col, False)
        y_sg = y0 + h_fin + 34
        dos = fmt == "4:5"
        filas = -(-len(redes) // 2) if dos else len(redes)
        paso = int(min(108, max(88, (Fz["y1"] - (y_sg + 136)) / float(max(1, filas)))))
        m.html.append('<div id="%s-fin" class="cie clip" data-start="%.3f" data-duration="%.3f" data-track-index="4" style="left:%dpx;top:%dpx;width:%dpx">'
                      '<div id="%s-fin-in" class="fin">%s</div></div>' % (m.id, t_b, d - t_b, x0, y0, col, m.id, esc(fin_txt)))
        m.tl.append('tl.fromTo("#%s-fin-in",{y:30,opacity:0},{y:0,opacity:1,duration:.5,ease:"power3.out"},%.3f);' % (m.id, t_b))
        m.html.append('<div id="%s-sg" class="cie clip" data-start="%.3f" data-duration="%.3f" data-track-index="5" style="left:%dpx;top:%dpx;width:%dpx">'
                      '<div id="%s-sg-in" class="sg cond">Sígueme en</div></div>' % (m.id, t_s, d - t_s, x0, y_sg, col, m.id))
        m.tl.append('tl.fromTo("#%s-sg-in",{y:30,opacity:0},{y:0,opacity:1,duration:.4,ease:"power3.out"},%.3f);' % (m.id, t_s))
        m.sfx.append((M["ini"] + t_s + 0.1, "impacto"))
        for j, r in enumerate(redes):
            cx = x0 + (col // 2 if dos and j % 2 else 0)
            cy = y_sg + 136 + paso * (j // 2 if dos else j)
            tj = t_s + 0.3 + 0.12 * j
            m.html.append('<div id="%s-rd%d" class="cie clip" data-start="%.3f" data-duration="%.3f" data-track-index="%d" style="left:%dpx;top:%dpx">'
                          '<div id="%s-rd%d-in" class="rd"%s><svg viewBox="0 0 24 24">%s</svg><span>%s</span></div></div>'
                          % (m.id, j, tj, max(0.2, d - tj), 1 + j % 3, cx, cy, m.id, j, ' style="font-size:44px"' if dos else "", iconos_redes()[r["red"]], esc(r.get("handle"))))
            m.tl.append('tl.fromTo("#%s-rd%d-in",{x:-40,opacity:0},{x:0,opacity:1,duration:.35,ease:"power3.out"},%.3f);' % (m.id, j, tj))
        m.barrer = False
        return m.cerrar(), m.sfx, {"cab": cab, "tits": tits, "piezas": [], "compactas": [], "fallas": []}
    tablero = M["clase"] == "tablero"
    if tablero:
        tits = titulos_de(ctx, M)
        cab = cabeza(ctx, Fz, tits[0][1] if tits else "")
        clip = "clips/e%d.mp4" % S["n"]
        usados.add(clip)
        ancho = Fz["x1b"] - Fz["x0"]
        alto = int(ancho * TABLERO_LADOS[1] / float(TABLERO_LADOS[0]))
        if cab["y0"] + alto > Fz["y1"]:
            alto = Fz["y1"] - cab["y0"]
            ancho = int(alto * TABLERO_LADOS[0] / float(TABLERO_LADOS[1]))
        # el marco llega hasta donde llega lo dibujado (tableros → *.alto.json): una tarjeta corta no deja medio marco vacío
        fa = os.path.join(ctx["trabajo"], "clips_tablero", "e%d.alto.json" % S["n"])
        marco = alto
        try:
            h_ = leer(fa)["alto"] if os.path.exists(fa) else None
            if h_:
                marco = min(alto, int((h_ + 36) * alto / float(TABLERO_LADOS[1])))
        except (OSError, ValueError, KeyError, TypeError):
            pass
        x = Fz["x0"] + (Fz["x1b"] - Fz["x0"] - ancho) // 2
        y = cab["y0"] + max(0, (Fz["y1"] - cab["y0"] - marco) // 3)
        m.html.append('<div id="%s-marco" class="pz pizarra" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;z-index:5" data-layout-allow-overlap>'
                      '<video id="%s-anim" class="clip" data-start="0" data-duration="%.3f" data-track-index="0" muted playsinline src="assets/%s" '
                      'style="position:absolute;left:0;top:0;width:%dpx;height:%dpx;object-fit:cover"></video></div>' % (m.id, x, y, ancho, marco, m.id, d, clip, ancho, alto))
        m.tl.append('tl.fromTo("#%s-marco",{y:60,opacity:0},{y:0,opacity:1,duration:.4,ease:"power3.out"},0);' % m.id)
        m.sfx.append((M["ini"] + 0.2, "whoosh"))
        if not M["golpes"]:
            m.extra.append("#%s-marco" % m.id)
            return m.cerrar(), m.sfx, {"cab": cab, "tits": tits, "piezas": [], "compactas": [], "fallas": []}
        corte = m.loc(M["golpes"][0]["_t"] - LEAD)
        m.html[-1] = m.html[-1].replace('data-duration="%.3f"' % d, 'data-duration="%.3f"' % max(0.2, corte), 1)
        m.tl.append('tl.set("#%s-marco",{opacity:0},%.3f);' % (m.id, corte))
    if M["clase"] == "maqueta":   # la maqueta 3D: su clip (clips_maqueta/<mesa>.mp4) ocupa el marco toda la mesa; los golpes caen encima
        K = marco_clip(ctx, M, fmt)
        clip = "maquetas/%s.mp4" % M["id"]
        usados.add(clip)
        m.html.append('<div id="%s-marco" class="pz maqueta" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;z-index:5" data-layout-allow-overlap>'
                      '<video id="%s-anim" class="clip" data-start="0" data-duration="%.3f" data-track-index="0" muted playsinline src="assets/%s" '
                      'style="position:absolute;left:0;top:0;width:%dpx;height:%dpx;object-fit:cover"></video>'
                      '<div class="mq-pie" data-layout-ignore style="left:%dpx;right:%dpx;bottom:10px">%s</div></div>'
                      % (m.id, K["x"], K["y"], K["w"], K["h"], m.id, d, clip, K["w"], K["h"], K["margen"], K["margen"], esc(MS.credito_maqueta(M["maqueta"]))))
        m.tl.append('tl.fromTo("#%s-marco",{y:60,opacity:0},{y:0,opacity:1,duration:.4,ease:"power3.out"},0);' % m.id)
        m.sfx.append((M["ini"] + 0.2, "whoosh"))
        m.sfx += MS.efectos_maqueta(ctx, M)
        m.extra.append("#%s-marco" % m.id)
    for k, g in enumerate(M["golpes"]):
        if primera and g["_t"] - LEAD <= M["ini"] + 0.05:
            g["_ya"] = True
    L = componer(ctx, M, fmt, F, elenco)
    for p in L["piezas"]:
        m.f, m.hasta = p["f"], p["hasta"]
        n0 = len(m.extra)
        {"red": dibujar_red, "barra": dibujar_barra}.get(p["g"]["tipo"], dibujar)(ctx, m, p["g"], p["x"], p["y"], p["w"], p["h"], p["ex"], p["k"], F, usados)
        if p["hasta"] is not None:
            for sel in m.extra[n0:]:   # el lazo de una lista se va con ella
                m.tl.append('tl.set("%s",{opacity:0},%.3f);' % (sel, m.loc(p["hasta"])))
            del m.extra[n0:]
    m.f, m.hasta = 1.0, None
    for c in L["compactas"]:
        if (c["hasta"] if c["hasta"] is not None else M["fin"]) - c["desde"] < 0.6:
            continue
        m.estatica(c["x"], c["y"], c["w"], c["giro"], c["html"], c["desde"], c["hasta"])
        usados.update(c["activos"])
    return m.cerrar(), m.sfx, L


# ---------- subtítulos ----------
VACIAS = set("a al con de del e el en es la las lo los o para por que se su sus u un una y".split())


def trocear(ps):
    """Los subtítulos en trozos de ≤ 26 caracteres (como video/comun.js): corta tras puntuación fuerte y no deja una palabra vacía al final."""
    out, cur = [], []
    for p in ps:
        largo = len(" ".join(x["text"] for x in cur)) + len(p["text"]) + 1
        if cur and largo > 26:
            lleva = [cur.pop()] if len(cur) > 1 and VD._plano(cur[-1]["text"]) in VACIAS else []
            out.append(cur)
            cur = lleva
        cur.append(p)
        if re.search(r"[.?:;…]$", p["text"]):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def subtitulos(ctx, mesas, Fz, C):
    """Los subtítulos del video: un clip por trozo, la palabra activa en caja de acento y las que faltan al 38 %. Callan
    mientras la voz lee una cita que ya está en pantalla (sin subtítulo doble). → (HTML, tweens)."""
    es, offs = ctx["es"], ctx["offs"]
    calla = []
    for M in mesas:
        for g in M["golpes"]:
            if g.get("tipo") == "cita":
                a, b = lectura(ctx, g)
                if a is not None:
                    calla.append((a - 0.05, b + 0.05))
    trozos = []
    for i, S in enumerate(es):
        y = Fz["subs_cierre"] if S["tipo"] == "cierre" else Fz["subs"]
        for tr in trocear([w for w in S.get("palabras") or [] if (w.get("text") or "").strip()]):
            ts = [offs[i] + w["start"] for w in tr]
            if sum(1 for t in ts if any(a <= t <= b for a, b in calla)) >= 0.6 * len(tr):
                continue
            trozos.append({"y": y, "pal": tr, "ts": ts, "fin": offs[i] + tr[-1].get("end", tr[-1]["start"] + 0.3)})
    html, tl = [], []
    for k, tz in enumerate(trozos):
        ini = max(0.0, tz["ts"][0] - 0.05)
        sig = trozos[k + 1]["ts"][0] - 0.05 if k + 1 < len(trozos) else ctx["total"]
        fin = sig if sig - tz["fin"] < 0.7 else tz["fin"] + 0.4
        fin = min(fin, ctx["total"])
        if fin - ini < 0.12:
            continue
        html.append('      <div id="sb%d" class="clip sbt" data-start="%.3f" data-duration="%.3f" data-track-index="9" data-layout-ignore style="top:%dpx">%s</div>'
                    % (k, ini, fin - ini, tz["y"], " ".join('<span id="sb%d-%d">%s</span>' % (k, j, esc(w["text"])) for j, w in enumerate(tz["pal"]))))
        for j, t in enumerate(tz["ts"]):
            tl.append('tl.set("#sb%d-%d",{opacity:1,backgroundColor:"%s",color:"%s"},%.3f);' % (k, j, C["acento"], C["tinta"], max(ini, t)))
            if j + 1 < len(tz["ts"]):
                tl.append('tl.set("#sb%d-%d",{backgroundColor:"rgba(0,0,0,0)",color:"%s"},%.3f);' % (k, j, C["papel"], max(ini, tz["ts"][j + 1])))
    return "\n".join(html), "\n".join("      " + x for x in tl)


# ---------- proyecto ----------
def tramos_barra(ctx):
    """Los tramos de la barra de progreso: uno por acto (y el cierre) → [(ini, fin)]."""
    es, offs, out = ctx["es"], ctx["offs"], []
    act = object()
    for i, S in enumerate(es):
        k = ("cierre",) if S["tipo"] == "cierre" else S.get("acto")
        if k != act or k is None:
            out.append([offs[i], None])
            act = k
    for k, t in enumerate(out):
        t[1] = out[k + 1][0] if k + 1 < len(out) else ctx["total"]
    return [(a, b) for a, b in out if b - a > 0.05]


def cmd_proyecto(a):
    return armar(os.path.abspath(a.trabajo), a.formato)


def armar(trabajo, fmt, portada=False):
    """El proyecto de HyperFrames de un formato (TRABAJO/hf/<9x16|4x5>/). Con `portada`, uno mínimo (hf/portada): solo la
    primera mesa con su golpe de arriba, sin subtítulos ni barra, para sacar la portada limpia."""
    ctx = contexto_v(trabajo)
    fp = os.path.join(trabajo, "plano.json")
    if not os.path.exists(fp):
        return falla("falta plano.json: video_hf.py plano %s" % rel(trabajo))
    Fz = FORMATOS[fmt]
    mesas, f0 = resolver_v(ctx, leer(fp))
    if portada:
        mesas = mesas[:1]
        ctx["seguir_en"] = None
        ctx["total"] = mesas[0]["fin"]
    C = ctx["C"] = colores_v(ctx["E"])
    css = CSS
    for k, v in sorted(C.items(), key=lambda kv: -len(kv[0])):
        css = css.replace("$" + k, v)
    ctx["css"] = css
    F, elenco = fichas(trabajo), ctx["elenco"]
    P = os.path.join(trabajo, "hf", "portada" if portada else Fz["id"])
    for d_ in ("compositions", "assets"):
        shutil.rmtree(os.path.join(P, d_), ignore_errors=True)
    os.makedirs(os.path.join(P, "compositions"))
    usados, hosts, efectos, titulos, info = set(), [], [], [], []
    W, H, D = Fz["w"], Fz["h"], ctx["total"]
    bucle = 0.0 if portada else BUCLE_S
    if bucle and mesas[0]["clase"] == "mesa" and any(g.get("_ya") or not (g.get("dice") or "").strip() for g in mesas[0]["golpes"]):
        # el cierre en bucle: el cuadro 0 del gancho (sus piezas ya puestas) vuelve al final, con la barra en cero
        mesas = mesas + [dict(mesas[0], id="mb", ini=D, fin=D + bucle, _bucle=True,
                              golpes=[dict(g, _t=D, _fin=D + 0.3, _ya=True) for g in mesas[0]["golpes"] if g.get("_ya") or not (g.get("dice") or "").strip()])]
    else:
        bucle = 0.0
    for k, M in enumerate(mesas):
        html, sfx, L = mesa_html_v(ctx, M, F, elenco, usados, fmt, primera=(k == 0 or M.get("_bucle")), ultima=(k == len(mesas) - 1 or bool(bucle) and k == len(mesas) - 2))
        if M.get("_bucle"):
            sfx = []
        efectos += sfx
        open(os.path.join(P, "compositions", M["id"] + ".html"), "w", encoding="utf-8").write(html)
        hosts.append('      <div id="%s" data-composition-id="%s" data-composition-src="compositions/%s.html" data-start="%.4f" data-duration="%.4f" '
                     'data-track-index="%d" data-track-kind="graphics" data-width="%d" data-height="%d"></div>'
                     % (M["id"], M["id"], M["id"], M["ini"], M["fin"] - M["ini"], 1 + k % 2, W, H))
        for t, txt in L["tits"]:
            titulos.append([t, txt, cabeza(ctx, Fz, txt)])
        info.append({"id": M["id"], "ini": round(M["ini"], 3), "fin": round(M["fin"], 3), "clase": M["clase"], "piezas": len(L["piezas"]),
                     "repliegues": sorted({round(c["desde"], 3) for c in L["compactas"]}), "fallas": L["fallas"]})
    for u in sorted(usados):
        src = os.path.join(trabajo, "clips_tablero", os.path.basename(u)) if u.startswith("clips/") else \
            os.path.join(trabajo, REGLAS["MAQUETA_CARPETA"], os.path.basename(u)) if u.startswith("maquetas/") else os.path.join(trabajo, u)
        if os.path.exists(src):
            enlazar(src, os.path.join(P, "assets", u))
        else:
            print("AVISO falta %s%s" % (rel(src), " (video_hf.py tableros)" if u.startswith("clips/") else " (video_hf.py maquetas)" if u.startswith("maquetas/") else ""))
    for M in mesas:
        if M["clase"] == "maqueta" and not M.get("_bucle") and not MS.clip_maqueta(ctx, M)[1]:
            print("AVISO la maqueta de %s cambió desde su render (o no se ha renderizado): video_hf.py maquetas %s" % (M["id"], rel(trabajo)))
    for fnt in ("archivo-wdth.woff2", "jetbrains-mono-var.woff2"):
        enlazar(os.path.join(RAIZ, "design", "fonts", fnt), os.path.join(P, "assets", "fonts", fnt))
    enlazar(os.path.join(RAIZ, "design", "grano-mesa.png"), os.path.join(P, "assets", "grano.png"))
    MS.gsap_local(P)   # GSAP del repositorio (scripts/versiones.py): assets/vendor/gsap.min.js; el render no llama a la red
    # la cabecera: la barra por actos, el kicker de la serie y el golpe de arriba (cambia de un corte con su mesa)
    x0, col = Fz["x0"], Fz["x1b"] - Fz["x0"]
    cab0 = cabeza(ctx, Fz, "")
    sobre, tl = [], []
    DT = D + bucle   # la duración del video: con el bucle del final
    tr = [] if portada else tramos_barra(ctx)
    if tr:
        sobre.append('      <div id="barra" class="clip" data-start="0" data-duration="%.4f" data-track-index="5" data-layout-ignore style="left:%dpx;top:%dpx;width:%dpx">%s</div>'
                     % (DT, x0, cab0["barra"], col, "".join('<i style="flex:%.2f"><b id="bp%d"></b></i>' % (b - a_, j) for j, (a_, b) in enumerate(tr))))
    for j, (a_, b) in enumerate(tr):
        tl.append('tl.fromTo("#bp%d",{scaleX:0,transformOrigin:"0%% 50%%"},{scaleX:1,duration:%.3f,ease:"none"},%.3f);' % (j, b - a_, a_))
        if bucle:
            tl.append('tl.set("#bp%d",{scaleX:0},%.3f);' % (j, D))
    if bucle:
        tl.append('tl.fromTo("#mb",{opacity:0},{opacity:1,duration:%.2f,ease:"none"},%.3f);' % (VD.BUCLE_FUNDIDO, D))
    serie = ctx["E"].get("serie") or {}
    if serie.get("parte"):
        sobre.append('      <div id="kick" class="clip mono" data-start="0" data-duration="%.4f" data-track-index="6" data-layout-ignore style="left:%dpx;top:%dpx;width:%dpx">'
                     'Parte %s de %s%s</div>' % (DT, x0, cab0["kicker"], col, serie["parte"], serie.get("de"), " · " + esc(serie["titulo"]) if serie.get("titulo") else ""))
    # el chip «Ejemplo» (/explica: números ilustrativos que calculó el script, E3–E4): arriba a la derecha, en la línea del
    # kicker, mientras está la mesa de una escena con `ejemplo` (en un tablero también: su clip se graba sin chip)
    tramos = []
    for M in mesas:
        if M["clase"] != "cierre" and not M.get("_bucle") and any(ctx["es"][i].get("ejemplo") for i in M["idx"]):
            if tramos and abs(tramos[-1][1] - M["ini"]) < 0.05:
                tramos[-1][1] = M["fin"]
            else:
                tramos.append([M["ini"], M["fin"]])
    for j, (a_, b) in enumerate(tramos):
        sobre.append('      <div id="ejm%d" class="clip mono ejm" data-start="%.3f" data-duration="%.3f" data-track-index="9" data-layout-ignore style="right:%dpx;top:%dpx">Ejemplo</div>'
                     % (j, a_, b - a_, W - (Fz["x1b"] if fmt == "9:16" else Fz["x1"]), cab0["kicker"] - 10))
    titulos.sort(key=lambda x: x[0])
    runs = []
    for t, txt, cab in titulos:
        if runs and runs[-1][1] == txt:
            continue
        runs.append([t, txt, cab])
    for k, (t, txt, cab) in enumerate(runs):
        fin = runs[k + 1][0] if k + 1 < len(runs) else DT
        sobre.append('      <div id="tit%d" class="clip tit" data-start="%.3f" data-duration="%.3f" data-track-index="7" data-layout-ignore style="left:%dpx;top:%dpx;width:%dpx">'
                     '<div id="tit%d-in" class="cond" style="font-size:%dpx;white-space:nowrap">%s</div></div>' % (k, t, max(0.2, fin - t), x0, cab["titulo"], col, k, cab["px"],
                        "<br>".join(esc(r) for r in cabeza(ctx, Fz, txt)["renglones"])))
        if t > 0.05:
            tl.append('tl.fromTo("#tit%d-in",{y:16,opacity:0},{y:0,opacity:1,duration:.3,ease:"power3.out"},%.3f);' % (k, t))
    # «Sígueme» a mitad del video (V25): arriba a la derecha, sin cuenta, sin cortar la escena
    if ctx.get("seguir_en"):
        M = next(M for M in mesas if M["id"] == ctx["seguir_en"][0])
        t = ctx["seguir_en"][1]
        y = seguir_sitio(ctx, Fz, M, titulos_de(ctx, M))[1]
        sobre.append('      <div id="seguir" class="clip" data-start="%.3f" data-duration="%.3f" data-track-index="8" data-layout-allow-overlap data-layout-allow-occlusion '
                     'style="right:%dpx;top:%dpx"><div id="seguir-in"><span>Sígueme</span><svg id="seguir-c" viewBox="0 0 24 24" width="44" height="44"><path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7 2.5 7h-17S6 15 6 9Z'
                     'M10 20a2 2 0 0 0 4 0" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div>'
                     % (t, SEGUIR_S, W - Fz["x1b"] if fmt == "9:16" else W - Fz["x1"], y))
        tl += ['tl.fromTo("#seguir-in",{y:-40,opacity:0},{y:0,opacity:1,duration:.35,ease:"power3.out"},%.3f);' % t,
               'tl.fromTo("#seguir-in",{scale:1},{scale:.92,duration:.09,yoyo:true,repeat:1,ease:"power1.inOut",immediateRender:false},%.3f);' % (t + 1.2),
               'tl.fromTo("#seguir-c",{rotation:0,transformOrigin:"50%% 10%%"},{rotation:16,duration:.09,yoyo:true,repeat:5,ease:"sine.inOut"},%.3f);' % (t + 1.5),
               'tl.fromTo("#seguir-in",{y:0,opacity:1},{y:-40,opacity:0,duration:.3,ease:"power2.in",immediateRender:false},%.3f);' % (t + SEGUIR_S - 0.32)]
        efectos.append((round(t + 1.2, 3), "tic"))
    sub_html, sub_tl = ("", "") if portada else subtitulos(ctx, mesas, Fz, C)
    audio = ""
    mezcla_f = os.path.join(trabajo, "segs_mesa", "mezcla_final.wav")
    if os.path.exists(mezcla_f) and not portada and abs(VD.ffprobe_dur(mezcla_f) - DT) < 0.2:   # la guía de la vista previa
        enlazar(mezcla_f, os.path.join(P, "assets", "audio.wav"))
        audio = '      <audio id="guia" class="clip" data-start="0" data-duration="%.4f" data-track-index="10" data-volume="1" src="assets/audio.wav"></audio>\n' % DT
    open(os.path.join(P, "index.html"), "w", encoding="utf-8").write("""<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=%(W)d, height=%(H)d" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: %(W)dpx; height: %(H)dpx; overflow: hidden; background: %(mesa2)s; }
      #root { position: relative; width: %(W)dpx; height: %(H)dpx; }
      #mesa { position: absolute; inset: 0; background: radial-gradient(900px 1200px at 46%% 38%%, %(luz)s 0%%, %(mesa)s 55%%, %(fondo)s 100%%); }
      #grano { position: absolute; inset: 0; background: url('assets/grano.png'); background-size: 480px 270px; opacity: .16; mix-blend-mode: overlay; }
      @font-face { font-family: 'Archivo'; font-weight: 100 900; font-stretch: 62%% 125%%; src: url('assets/fonts/archivo-wdth.woff2') format('woff2'); }
      @font-face { font-family: 'JetBrains Mono'; font-weight: 100 800; src: url('assets/fonts/jetbrains-mono-var.woff2') format('woff2'); }
      .cond { font-family: 'Archivo', sans-serif; font-stretch: 62%%; font-weight: 800; text-transform: uppercase; line-height: .94; letter-spacing: .005em; }
      .mono { font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: .1em; }
      #barra { position: absolute; z-index: 800; display: flex; gap: 10px; height: 7px; }
      #barra i { position: relative; display: block; height: 7px; border-radius: 4px; background: %(filo)s; overflow: hidden; }
      #barra b { position: absolute; inset: 0; display: block; background: %(papel)s; }
      #kick { position: absolute; z-index: 800; font-size: 22px; font-weight: 600; color: %(acento)s; white-space: nowrap; overflow: hidden; }
      .tit { position: absolute; z-index: 800; color: %(papel)s; }
      .ejm { position: absolute; z-index: 820; background: %(papel)s; color: %(tinta)s; font-size: 24px; font-weight: 700; padding: 8px 14px 6px; white-space: nowrap; }
      .sbt { position: absolute; z-index: 850; left: %(x0)dpx; width: %(col)dpx; text-align: center; font: 800 60px/1.24 'Archivo', sans-serif; color: %(papel)s; }
      .sbt span { opacity: .38; border-radius: 12px; padding: 0 .14em; }
      #seguir { position: absolute; z-index: 900; }
      #seguir-in { display: flex; align-items: center; gap: 14px; background: %(acento)s; color: %(tinta)s; padding: 16px 26px 12px 30px; font: 800 56px/1 'Archivo', sans-serif;
        font-stretch: 62%%; text-transform: uppercase; box-shadow: 0 18px 40px rgba(0,0,0,.55); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="%(D).4f" data-width="%(W)d" data-height="%(H)d">
      <div id="mesa" data-layout-ignore></div>
      <div id="grano" data-layout-ignore></div>
%(hosts)s
%(sobre)s
%(subs)s
%(audio)s    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
%(tl)s
%(subtl)s
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""" % dict(C, W=W, H=H, D=DT, x0=x0, col=col, hosts="\n".join(hosts), sobre="\n".join(sobre), subs=sub_html, audio=audio,
           tl="\n".join("      " + x for x in tl), subtl=sub_tl))
    escribir(os.path.join(P, "hyperframes.json"), {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                                                    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
                                                    "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
                                                    "media": {"autoProxy": True}, "authoringSkill": "hyperframes"})
    escribir(os.path.join(P, "meta.json"), {"id": "%s-%s" % (ctx["Y"]["slug"], Fz["id"]), "name": "%s (%s)" % (ctx["Y"]["slug"], fmt)})
    escribir(os.path.join(P, "mesas.json"), info)
    if portada:
        return 0
    escribir(os.path.join(P, "duracion.json"), {"plano_s": D, "bucle_s": bucle, "total_s": round(DT, 4)})
    if fmt == "9:16":
        escribir(os.path.join(trabajo, "hf", "efectos.json"), sorted([round(t, 3), i] for t, i in efectos if 0 <= t < D - 0.2))
    print("proyecto %s: %d mesas · %d piezas · %d repliegues · %s → %s" % (fmt, len(mesas), sum(x["piezas"] for x in info), sum(len(x["repliegues"]) for x in info), VD_mmss(D), rel(P)))
    for x in f0:
        print("AVISO", x)
    return 0


# ---------- gates ----------
def revisar_v(ctx, P, mesas=None, f0=None):
    """MV1–MV14 sobre el plano → (fallas, avisos, medidas). MV1–MV7 son los del núcleo con las reglas del vertical; MV8–MV11
    y MV13 salen de componer la mesa en los dos formatos (geometría y tiempos calculados, nunca píxeles): MV13 = dos piezas
    que el plano manda dibujar en el color de acento (mesa.en_acento) no coinciden al frente; falla si una es un dato (cifra o
    barra) y la otra otro dato o un bloque, y lo demás se avisa (mesa.acento_compite)."""
    if mesas is None:
        mesas, f0 = resolver_v(ctx, P)
    f, av, med = MS.revisar(ctx, P, mesas, f0)
    f, av = [codigo(x) for x in f], [codigo(x) for x in av]
    F, elenco = fichas(ctx["trabajo"]), ctx["elenco"]
    vistos = set()
    for k, M in enumerate(mesas):
        if M["clase"] == "tablero" and M["golpes"]:
            i = M["idx"][0]
            pasos = [ctx["offs"][i] + x["t"] for x in ctx["es"][i].get("eventos") or [] if x.get("tipo") in MS.EVENTOS_TABLERO]
            if pasos and M["golpes"][0]["_t"] - LEAD < max(pasos) + 1.0:
                f.append("MV6 %s: el primer golpe de un tablero entra a los %.1f s y la animación da su último paso a los %.1f s: la pieza la retira; "
                         "va al menos 1 s después" % (M["id"], M["golpes"][0]["_t"], max(pasos)))
        if M["clase"] not in ("mesa", "tablero", "maqueta") or not M["golpes"]:
            continue
        M["_barre"] = k < len(mesas) - 1
        if k == 0:
            for g in M["golpes"]:
                if g["_t"] - LEAD <= M["ini"] + 0.05:
                    g["_ya"] = True
        for fmt in FORMATOS:
            try:
                L = componer(ctx, M, fmt, F, elenco)
                fallas_fmt, avisos_fmt = L["fallas"], L.get("avisos") or []
            except (OSError, KeyError) as e:
                # un documento cuya página no está en paginas.json: mesa.revisar ya dio su MV4; aquí no se puede medir la
                # mesa, y antes el gate reventaba con FileNotFoundError / KeyError en vez de decirlo
                fallas_fmt, avisos_fmt = ["MV4 %s: no se puede componer la mesa (%s: %s): revisa las páginas de sus documentos (historia.py pagina)"
                                          % (M["id"], type(e).__name__, e)], []
            for lista, destino in ((fallas_fmt, f), (avisos_fmt, av)):
                for x in lista:
                    clave = re.sub(r", (9:16|4:5)\)", ")", x)
                    if clave not in vistos:
                        vistos.add(clave)
                        destino.append(x)
    # MV4 y MV12: la jerarquía de personas (red)
    voz_video = " ".join(VD._plano(w["text"]) for S in ctx["es"] for w in S.get("palabras") or [])
    for M in mesas:
        voz_mesa = " ".join(VD._plano(w["text"]) for i in M["idx"] for w in ctx["es"][i].get("palabras") or [])
        for j, g in enumerate(M["golpes"]):
            if g.get("crema") and g.get("tipo") not in MS.CREMA_TIPOS:   # MV13: `crema` solo donde el motor sabe dibujarla sin acento
                f.append("MV13 %s golpe %d (%s): `crema` solo vale en %s (la pieza se dibuja sin acento); en esta no cambia nada: quítalo"
                         % (M["id"], j + 1, g.get("tipo"), ", ".join(MS.CREMA_TIPOS)))
            if g.get("tipo") == "barra":   # MV4: la comparación, a la misma escala y con algo que medir
                q = "%s golpe %d (barra)" % (M["id"], j + 1)
                bs = [b for b in g.get("barras") or [] if isinstance(b, dict)]
                if not BARRAS_MIN <= len(bs) <= BARRAS_MAX:
                    f.append("MV4 %s: de %d a %d barras {etiqueta, valor, texto?, dice?, acento?}" % (q, BARRAS_MIN, BARRAS_MAX))
                for b in bs:
                    if not (b.get("etiqueta") or "").strip() or valor_num(b.get("valor")) is None or valor_num(b.get("valor")) < 0:
                        f.append("MV4 %s: la barra «%s» lleva `etiqueta` y un `valor` numérico ≥ 0" % (q, b.get("etiqueta")))
                    elif b.get("texto") and valor_num(b["texto"]) is not None and abs(valor_num(b["texto"]) - valor_num(b["valor"])) > 0.01 * max(1.0, abs(valor_num(b["valor"]))) \
                            and not re.search(r"\b(mil|millones?|%)", b["texto"], re.I):
                        f.append("MV4 %s: la barra «%s» dice «%s» y mide %s: el largo no corresponde a lo escrito" % (q, b.get("etiqueta"), b["texto"], b["valor"]))
                continue
            if g.get("tipo") != "red":
                continue
            q = "%s golpe %d (red)" % (M["id"], j + 1)
            nodos = [n for n in g.get("nodos") or [] if isinstance(n, dict)]
            acus = [n for n in g.get("acusadores") or [] if isinstance(n, dict)]
            ids = {n.get("id") for n in nodos}
            niveles = {}
            for n in nodos:
                niveles.setdefault(int(n.get("nivel") or 0), []).append(n)
            if not 2 <= len(nodos) or len(niveles) > RED_NIVELES or any(len(v) > RED_POR_NIVEL for v in niveles.values()) or len(acus) > RED_ACUSADORES:
                f.append("MV4 %s: de 2 nodos en adelante, ≤ %d niveles, ≤ %d por nivel y ≤ %d acusadores (lo demás, en otra mesa)" % (q, RED_NIVELES, RED_POR_NIVEL, RED_ACUSADORES))
            for n in nodos + acus:
                nom = VD._plano(n.get("persona") or n.get("nombre") or "")
                if not nom or not (n.get("dice") and buscar(ctx["es"][g["_i"]], n["dice"], 0)):
                    f.append("MV2 %s: el nodo «%s» lleva `dice` con palabras de la voz de su escena" % (q, n.get("nombre")))
                if nom and not any(t in voz_video for t in nom.split() if len(t) > 3) and not (n.get("clave") and VD._plano(n["clave"]) in voz_video):
                    f.append("MV4 %s: la voz del video nunca nombra a «%s»" % (q, n.get("nombre")))
            ar = [a_ for a_ in g.get("aristas") or [] if isinstance(a_, dict)]
            for a_ in ar:
                if a_.get("de") not in ids or a_.get("a") not in ids:
                    f.append("MV12 %s: un hilo une dos nodos de la jerarquía (quien acusa va aparte, sin hilos): %s → %s" % (q, a_.get("de"), a_.get("a")))
            if any(a_.get("atribuida") for a_ in ar) or g.get("atribuida"):
                if not (g.get("etiqueta") or "").strip():
                    f.append("MV12 %s: sus hilos son un alegato: lleva `etiqueta` («Según la acusación», «Según la fiscalía»…), que entra antes que las caras" % q)
                if not ATRIBUYE.search(voz_mesa):
                    f.append("MV12 %s: la voz de la mesa no atribuye el alegato (según…, para la acusación…, dijo…)" % q)
    # MV14: el primer cuadro ya tiene sujeto
    if mesas and mesas[0]["clase"] == "maqueta":
        f.append("MV14 %s: el gancho no lleva maqueta: el cuadro 0 abre con el sujeto (≥ 2 piezas ya puestas: su foto y su nombre) y vuelve en el bucle; "
                 "la maqueta va en una mesa de más adelante" % mesas[0]["id"])
    if mesas and mesas[0]["clase"] == "mesa":
        ya = [g for g in mesas[0]["golpes"] if g.get("_ya")]
        if len(ya) < 2:
            f.append("MV14 el cuadro 0 tiene %d pieza(s): el gancho abre con al menos 2 ya puestas (golpes sin `dice` al inicio de la primera mesa: "
                     "la foto del protagonista y su nombre)" % len(ya))
    return f, av, med


def fecha_legible(f):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(f or ""))
    return "%d de %s de %s" % (int(m.group(3)), MESES[int(m.group(2)) - 1], m.group(1)) if m and 1 <= int(m.group(2)) <= 12 else str(f or "")


def num_txt(v):
    """46.1 → «46.1»; 45259.26 → «45,259»; 17449.4 → «17,449»; 109 → «109» (como lo escriben las tarjetas)."""
    v = float(v)
    if abs(v) >= 1000 or abs(v - round(v)) < 1e-9:
        return "{:,}".format(int(round(v)))
    return ("%.1f" % v).rstrip("0").rstrip(".")


def texto_pantalla(S, i, frase, F):
    """Las piezas de una escena de texto cinético del motor propio (gancho, golpe, definición: /video, /sabias, /explica,
    /departamento, /congreso) en la mesa: la línea de pantalla como nota o cifra, la definición como ficha y, en el gancho,
    su visual (pareja → barra, llenado o figuras → cifra, lugar → mapa, el hemiciclo → la barra de votos frente al umbral).
    El gancho abre con dos piezas ya puestas (MV14). → lista de golpes."""
    T, V, tipo = S.get("T") or {}, S.get("V") or {}, S["tipo"]
    pal = S.get("palabras") or []
    pant = ((T.get("pant") or {}).get("texto") or T.get("pantalla") or "").strip()
    linea = " ".join(w.get("text", "") for w in T.get("linea") or [] if isinstance(w, dict)).strip()

    def dice_de(txt, por=None):
        """La palabra de la voz que lleva el primer número de `txt` (o la frase `txt` si la voz la dice)."""
        ns = numeros(txt or "")
        for k, w in enumerate(pal):
            if ns & numeros(w["text"]):
                return w["text"]
        r = buscar(S, " ".join((txt or "").split()[:2]), 0) if txt else None
        return " ".join(w["text"] for w in pal[r[1]:r[1] + 2]) if r else por
    gs = []
    if tipo == "definicion" and pant:
        return [{"tipo": "termino", "dice": frase(0), "texto": " ".join(pant.split()[:6]), "definicion": linea}]
    if tipo == "golpe" and pant:   # sin golpe de arriba propio (titulos_de): sigue el de la mesa anterior; la línea es la pieza
        if (T.get("pant") or {}).get("v") is not None:
            return [{"tipo": "cifra", "dice": dice_de(pant, frase(0)), "valor": pant, "rotulo": " ".join(linea.split()[:6])}]
        gs.append({"tipo": "termino", "dice": frase(0), "texto": " ".join(pant.split()[:6])})
        if linea and len(linea.split()) <= 6 and VD._plano(linea) != VD._plano(pant):
            r = buscar(S, " ".join(linea.split()[:2]), 0)
            if r and r[1] > 2:
                # la línea bajo el golpe va en crema: el acento es del golpe (MV13: un solo acento al frente)
                gs.append({"tipo": "termino", "dice": " ".join(w["text"] for w in pal[r[1]:r[1] + 2]), "texto": linea, "crema": True})
        return gs
    if tipo != "gancho":
        return gs
    # el gancho: la línea de pantalla y su visual, ya puestos en el cuadro 0. Con una línea corta, la pantalla es el golpe de
    # arriba y la línea una nota; con una larga, la línea es el golpe de arriba y la pantalla la nota (nunca las dos lo mismo)
    corta = linea and len(linea.split()) <= 6 and VD._plano(linea) != VD._plano(pant)
    S["_titulo_v"] = pant if (corta or not linea) else " ".join(linea.split()[:8])
    if pant and not corta and linea:
        gs.append({"tipo": "termino", "texto": " ".join(pant.split()[:6])})
    vt = V.get("tipo")
    if T.get("modo") == "gancho" and isinstance(T.get("cuentas"), dict) and (T.get("umbral") or {}).get("n"):   # /congreso: el mini-hemiciclo
        c = T["cuentas"]
        gs.append({"tipo": "barra", "barras": [{"etiqueta": "A favor", "valor": c.get("favor", 0), "texto": str(c.get("favor", 0)), "dice": dice_de(str(c.get("favor")))},
                                                {"etiqueta": "Hacían falta", "valor": T["umbral"]["n"], "texto": str(T["umbral"]["n"]), "dice": dice_de(str(T["umbral"]["n"]))},
                                                {"etiqueta": "En contra", "valor": c.get("contra", 0), "texto": str(c.get("contra", 0)), "dice": dice_de(str(c.get("contra")))}],
                   "titulo": T.get("etiqueta") or ""})
        gs[-1]["barras"][0]["acento"] = True
        fid = os.path.basename(T.get("foto") or "")[:-4] if T.get("foto") else None
        if fid and fid in F:
            gs.insert(0, {"tipo": "foto", "foto": fid, "pie": " ".join((T.get("etiqueta") or F[fid].get("descripcion") or "").split()[:6])})
    elif vt == "pareja" and isinstance(V.get("a"), dict) and isinstance(V.get("b"), dict):
        bs = []
        for lado in ("a", "b"):
            x = V[lado]
            if valor_num(x.get("valor")) is None:
                continue
            txt = num_txt(x["valor"])
            bs.append({"etiqueta": x.get("etiqueta") or lado.upper(), "valor": x["valor"], "texto": txt, "dice": dice_de(txt)})
        if len(bs) == 2:
            bs[-1]["acento"] = True
            gs.append({"tipo": "barra", "barras": bs})
    elif vt in ("llenado", "figuras") and valor_num(V.get("total")) is not None:
        v = num_txt(V["total"])
        gs.append({"tipo": "cifra", "dice": dice_de(v, frase(0)), "valor": v, "rotulo": " ".join((V.get("unidad") or linea).split()[:5]) or "en total"})
    elif vt == "lugar" and (V.get("nombre") or V.get("depto")):
        gs.append({"tipo": "lugar", "dice": dice_de(V.get("nombre"), frase(0)), "mapa": "guatemala", "depto": V.get("nombre") or V.get("depto"),
                   "rotulo": V.get("etiqueta") or V.get("nombre")})
    elif vt == "cifra" or (T.get("pant") or {}).get("v") is not None:
        n = next((w["text"].strip(" ,.;:") for w in pal if numeros(w["text"])), None)
        if n and not (pant and numeros(pant) & numeros(n)):
            gs.append({"tipo": "cifra", "dice": n, "valor": n, "rotulo": " ".join(linea.split()[:5]) or "cifra"})
    # el cuadro 0 lleva dos piezas (MV14): la línea corta como nota; si no hay, el visual ya puesto
    if corta:
        gs.insert(0, {"tipo": "termino", "texto": linea})
    if sum(1 for g in gs if not g.get("dice")) < 2:
        for g in gs:
            if g.get("dice"):
                g.pop("dice")
                break
    if any(g["tipo"] in ("cifra", "barra") for g in gs):   # MV13: el acento es del dato (la cifra, la barra); la nota que lo acompaña, en crema
        for g in gs:
            if g["tipo"] == "termino":
                g["crema"] = True
    return gs


def borrador_v(ctx):
    """El plano de partida del vertical: una mesa por escena, con lo que la escena ya trae y lo ya verificado de sus hechos.
    El realizador lo mejora; la maqueta lo usa tal cual. Sobre el borrador del 16:9 (foto, cita, término, años y cifras
    dichas, personas nombradas) añade lo propio del cuadro vertical: los tableros solos, la red como jerarquía, la página de
    documento, el rótulo de capítulo, un recorte con el titular real de la nota del hecho, y el cuadro 0 del gancho."""
    import youtube as YT
    import youtube_hf as YH
    trabajo, es = ctx["trabajo"], ctx["es"]
    por = {}
    for m in YH.borrador(dict(ctx))["mesas"]:
        for g in m["golpes"]:
            por.setdefault(g.pop("escena", None) or m["escenas"][0], []).append(g)
    F, notas, H = fichas(trabajo), MS.notas_leidas(), YT.hechos_serie(ctx["Y"])
    try:
        G = leer(os.path.join(trabajo, "guion.json")).get("escenas") or []
    except (OSError, ValueError):
        G = []
    fpg = os.path.join(trabajo, "paginas.json")
    PG = leer(fpg) if os.path.exists(fpg) else {}
    nombres = {VD._plano(c) for p in ctx["elenco"] for c in p["claves"]}
    mesas, notas_usadas = [], set()
    for i, S in enumerate(es):
        cl, tipo, pal = S["clave"], S["tipo"], S.get("palabras") or []
        if tipo == "cierre":
            continue
        if tipo in TABLEROS_V:
            mesas.append({"escenas": [cl], "golpes": []})
            continue
        if tipo == "red" and isinstance(S.get("G"), dict):
            r = red_de(S)
            r.pop("escena", None)
            mesas.append({"escenas": [cl], "golpes": [r]})
            continue

        def frase(k0, n=2):
            return " ".join(w["text"] for w in pal[k0:k0 + n]).strip(" ,.;:")
        voz = VD._plano(" ".join(w["text"] for w in pal))
        gs = []
        cinetico = (tipo in ("golpe", "definicion") or tipo == "gancho" and not (S.get("N") or {}).get("foto")) and isinstance(S.get("T"), dict) and ((S["T"].get("pant") or {}).get("texto") or S["T"].get("pantalla"))
        if cinetico:   # el texto cinético del motor propio: lo traduce texto_pantalla (y no las cifras sueltas del borrador del 16:9)
            gs = texto_pantalla(S, i, frase, F)
            por[cl] = [g for g in por.get(cl, []) if g["tipo"] in ("foto", "persona", "cita")]
        for g in por.get(cl, []):
            if g["tipo"] == "foto":
                r = F.get(g.get("foto")) or {}
                if (MS.JUDICIAL.search(r.get("descripcion") or "") or r.get("retrato_de")) and not any(n and n in voz for n in nombres):
                    continue   # personas en un proceso, sobre una voz que no nombra a nadie: fuera
                pie = (g.get("pie") or "").split()[:5]
                while len(pie) > 1 and VD._plano(pie[-1]) in VACIAS:   # un pie no termina en «el», «de», «tras»…
                    pie.pop()
                g["pie"] = " ".join(pie).rstrip(",;:")
            if g["tipo"] == "persona" and g.get("cargo"):
                g["cargo"] = " ".join(g["cargo"].split()[:5])
            gs.append(g)
        e = G[i] if i < len(G) and isinstance(G[i], dict) else {}
        if tipo == "pagina" and e.get("pagina") in PG and pal:
            fr = (PG[e["pagina"]].get("frase") or "").split()
            gs.insert(0, {"tipo": "documento", "dice": frase(0), "pagina": e["pagina"], "titulo": ((S.get("PG") or {}).get("titulo") or PG[e["pagina"]].get("fuente") or "")[:40],
                          "lee": " ".join(fr[:3]), "lee_hasta": " ".join(fr[-3:])})
        if tipo == "capitulo" and pal:
            Hh = S.get("H") or {}
            tit = " ".join(w["text"] for w in Hh.get("titulo") or [] if isinstance(w, dict))
            gs = [{"tipo": "institucion", "dice": frase(0), "kicker": "Capítulo %s de %s" % (Hh.get("numero"), Hh.get("total")), "nombre": tit or "Capítulo %s" % Hh.get("numero"),
                   "rol": " – ".join(str(x) for x in dict.fromkeys(x for x in (Hh.get("desde"), Hh.get("hasta")) if x))}]
        segs = [sg for sg in segmentos(S) if (sg.get("texto") or "").strip()]
        if len(segs) >= 2 and not any(g["tipo"] in ("recorte", "documento", "cita") for g in gs):   # el titular real de la nota de un hecho de la escena
            for hid in ctx["hechos_de"].get(cl) or []:
                fu = next((fu for fu in (H.get(hid) or {}).get("fuentes") or [] if fu.get("url") not in notas_usadas and (notas.get(fu.get("url")) or {}).get("titulo")
                           and 3 <= len(notas[fu["url"]]["titulo"].split()) <= 12 and not re.search(r"\b(the|of|and|how|what)\b", notas[fu["url"]]["titulo"], re.I)), None)
                if fu:
                    n = notas[fu["url"]]
                    notas_usadas.add(fu["url"])
                    gs.append({"tipo": "recorte", "dice": frase(next((k for k, w in enumerate(pal) if w["start"] >= segs[1]["t"]), 0)), "medio": fu.get("medio") or n.get("medio") or "", "fecha": fecha_legible(fu.get("fecha") or n.get("fecha")),
                               "url": fu["url"], "titular": n["titulo"]})
                    break
        gs.sort(key=lambda g: (buscar(S, g.get("dice") or "", 0) or (-1,))[0])
        if i == 0 and cinetico:   # el gancho de texto cinético: sus piezas sin `dice` ya están en el cuadro 0
            gs = [g for g in gs if not g.get("dice")] + [g for g in gs if g.get("dice")]
        elif i == 0:   # el cuadro 0: el sujeto ya puesto (MV14)
            if ctx.get("protagonista") and not any(g["tipo"] == "termino" for g in gs[:2]):
                gs.insert(1 if gs and gs[0]["tipo"] in ("foto", "recorte") else 0, {"tipo": "termino", "texto": ctx["protagonista"]})
            for g in gs[:2]:
                g.pop("dice", None)
        mesas.append(dict({"escenas": [cl], "golpes": gs[:REGLAS["MESA_PIEZAS"]]}, **({"titulo": S.pop("_titulo_v")} if S.get("_titulo_v") else {})))
    return {"version": 1, "mesas": mesas}


def cmd_borrador(a):
    trabajo = os.path.abspath(a.trabajo)
    B = borrador_v(contexto_v(trabajo))
    escribir(os.path.join(trabajo, "plano.borrador.json"), B)
    print("borrador: %d mesas · %d golpes → %s" % (len(B["mesas"]), sum(len(m["golpes"]) for m in B["mesas"]), rel(os.path.join(trabajo, "plano.borrador.json"))))
    return 0


def cmd_digesto(a):
    """Lo que hace falta para escribir el plano de un video vertical: las oraciones con su segundo, lo que el borrador ya
    propone, los hechos de cada escena con sus fuentes (el titular real de cada nota leída), las fotos, las páginas y el elenco."""
    import youtube as YT
    import youtube_hf as YH
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto_v(trabajo)
    es, offs = ctx["es"], ctx["offs"]
    F, elenco = fichas(trabajo), ctx["elenco"]
    H = YT.hechos_serie(ctx["Y"])
    bor = {m["escenas"][0]: m["golpes"] for m in borrador_v(ctx)["mesas"]}
    usados = {}
    fp = os.path.join(trabajo, "plano.json")
    if os.path.exists(fp):
        for m in leer(fp).get("mesas") or []:
            for g in m.get("golpes") or []:
                if g.get("tipo") == "foto":
                    usados[g.get("foto")] = usados.get(g.get("foto"), 0) + 1
    print("# Plano vertical de %s · %s · escribe %s" % (ctx["Y"]["slug"], VD_mmss(ctx["total"]), rel(fp)))
    print("\nReglas: una pieza por oración; texto corto (lo que la voz ya dice no hace falta repetirlo); cada texto queda al frente 0.5 s + 0.3 s por "
          "palabra que la voz no dice; ≤ %d piezas por mesa; una foto, una sola vez; mesas de una o dos escenas con `titulo` de ≤ 6 palabras; un solo acento "
          "al frente (cifra, nota, barra, subrayado: a la que no es el dato, `\"crema\": true`)." % REGLAS["MESA_PIEZAS"])
    print("\n## Escenas (clave · tipo · segundo). Cada «·» es una oración: ahí tiene que entrar algo.")
    notas = MS.notas_leidas()
    for i, S in enumerate(es):
        if S["tipo"] == "cierre":
            print("\n%s  %s · cierre (lo arma el script; no va en el plano)" % (VD_mmss(offs[i]), S["clave"]))
            continue
        tab = S["tipo"] in TABLEROS_V
        print("\n%s  %s · %s%s · %.1f s%s" % (VD_mmss(offs[i]), S["clave"], S["tipo"], " (TABLERO: va sola; un golpe tuyo entra ≥ 1 s después de su último paso y la retira)" if tab else "",
                                               S["dur"], " · abre el acto: el motor pone su rótulo como ficha" if isinstance(S.get("R"), dict) else ""))
        pasos = sorted(offs[i] + x["t"] for x in S.get("eventos") or [] if x.get("tipo") in MS.EVENTOS_TABLERO) if tab else []
        for sg in segmentos(S):
            if (sg.get("texto") or "").strip():
                sin = tab and not any(offs[i] + sg["t"] - 0.6 <= t_ < offs[i] + sg["hasta"] for t_ in pasos)
                print("   · %5.1f s  %s%s" % (offs[i] + sg["t"], sg["texto"], "   ← sin paso de la animación: necesita un golpe" if sin else ""))
        N = S.get("N") or {}
        if N.get("foto"):
            print("   foto de la escena: %s" % YT.foto_id(N["foto"]))
        for g in bor.get(S["clave"]) or []:
            print("   borrador: %s" % json.dumps({k: v for k, v in g.items() if k != "escena"}, ensure_ascii=False)[:1400 if g.get("tipo") == "red" else 230])
        for hid in ctx["hechos_de"].get(S["clave"]) or []:
            h = H.get(hid) or {}
            print("   hecho %s (%s%s): %s" % (hid, h.get("fecha"), ", " + h.get("estado") if h.get("estado") else "", (h.get("texto") or "")[:170]))
            for fu in (h.get("fuentes") or [])[:3]:
                n = notas.get(fu.get("url")) or {}
                print("      fuente: %s · %s · titular: «%s»%s\n        url: %s\n        cita: «%s»" % (
                    fu.get("medio"), fu.get("fecha") or n.get("fecha"), (n.get("titulo") or "(nota sin leer: historia.py leer)")[:100],
                    " · PDF (historia.py pagina)" if MS.pdf_de(fu.get("url")) else "", fu.get("url"), (fu.get("cita") or "")[:260]))
    print("\n## Personas (pieza `persona`; el retrato entra solo si lo hay)")
    for p in elenco:
        print("  %s · %s · %s · la voz la nombra como: %s" % (p["nombre"], p["cargo"], "con retrato" if p.get("foto") else "SIN retrato", " / ".join(p["claves"][:4])))
    print("\n## Fotos (id · tamaño · usos · crédito · qué se ve)")
    for fid, r in sorted(F.items()):
        if fid.startswith("_") or not r.get("archivo"):
            continue
        print("  %s · %s · %d usos · %s · %s%s" % (fid, "×".join(str(x) for x in r.get("tamano") or []), usados.get(fid, 0), r.get("credito"), (r.get("descripcion") or "")[:110],
                                                 " · PERSONAS EN PROCESO O RETRATO: solo donde la voz las nombra" if MS.JUDICIAL.search(r.get("descripcion") or "") or r.get("retrato_de") else ""))
    pg = os.path.join(trabajo, "paginas.json")
    if os.path.exists(pg):
        print("\n## Páginas de documento (pieza `documento` con `pagina`)")
        for k, v in leer(pg).items():
            print("  %s · pág. %s · «%s» · %s" % (k, v.get("pagina"), (v.get("frase") or "")[:90], v.get("fuente")))
    print("\n## Lugares con coordenadas (mapa «mundo»): %s" % ", ".join(sorted(MS.LUGARES)))
    for ln in MS.digesto_maqueta(ctx):
        print(ln)
    return 0


def red_de(S):
    """La pieza `red` que una escena `red` ya trae en `S.G` (nodos con nivel, hilos, alegato): quien investiga o acusa va aparte."""
    G = S.get("G") or {}
    pal = S.get("palabras") or []

    def dice_en(t):
        k = min(range(len(pal)), key=lambda i: abs(pal[i]["start"] - t)) if pal else 0
        return " ".join(w["text"] for w in pal[k:k + 2]).strip(" ,.;:")
    nodos, acus = [], []
    for n in G.get("nodos") or []:
        d = {"id": n.get("id"), "nombre": n.get("corto") or n.get("nombre"), "persona": n.get("nombre"), "cargo": n.get("cargo") or "", "dice": dice_en(n.get("start") or 0)}
        if n.get("foto"):
            d["foto"] = n["foto"]
            if isinstance(n.get("foco"), dict):
                d["foco"] = {k: n["foco"][k] for k in ("x", "y", "w", "h") if k in n["foco"]}
        if (n.get("bando") or "") in ("investigador", "acusador", "fiscal"):
            acus.append(d)
        else:
            nodos.append(dict(d, nivel=int(n.get("nivel") or 0)))
    ids = {n["id"] for n in nodos}
    ar = [{"de": a_["de"], "a": a_["a"], "rel": a_.get("rel") or "", "atribuida": bool(a_.get("atribuida") or G.get("atribuida")), "dice": dice_en(a_.get("start") or 0)}
          for a_ in G.get("aristas") or [] if a_.get("de") in ids and a_.get("a") in ids]
    out = {"tipo": "red", "escena": S["clave"], "dice": dice_en(min([n.get("start") or 0 for n in G.get("nodos") or []] or [0]) - 1.0), "nodos": nodos, "aristas": ar, "acusadores": acus[:RED_ACUSADORES]}
    if G.get("atribuida") or any(a_["atribuida"] for a_ in ar):
        out["etiqueta"] = "Según la acusación"
    if G.get("fuente"):
        out["fuente"] = G["fuente"]
    return out


def hoja_v(ctx, mesas):
    es, offs = ctx["es"], ctx["offs"]
    L = ["# Hoja de golpes\n", "Cada fila es una oración de la voz y lo que entra en pantalla con ella.\n",
         "| Tiempo | Arriba | La voz dice | Entra en pantalla |", "|---|---|---|---|"]
    for M in mesas:
        tit = "; ".join(t for _, t in titulos_de(ctx, M))
        if M["clase"] == "cierre":
            L.append("| %s | %s | (cierre) | Conclusiones, frase final y «Sígueme en» |" % (VD_mmss(M["ini"]), tit))
            continue
        ev = eventos_de(ctx, M)
        for i in M["idx"]:
            for sg in segmentos(es[i]):
                if not (sg.get("texto") or "").strip():
                    continue
                a_, b = offs[i] + sg["t"], offs[i] + sg["hasta"]
                gs = [g for g in M["golpes"] if a_ - 0.6 <= g["_t"] < b]
                txt = "; ".join("**%s**: %s" % (g["tipo"], resumen_golpe(g)) for g in gs)
                if not txt:
                    dentro = [e for e in ev if a_ - 0.6 <= e[0] < b]
                    txt = "un paso de la animación ya hecha (%s)" % es[i]["tipo"] if any(e[1] == "tablero" for e in dentro) else \
                        "" if any(e[1] == "maqueta" for e in dentro) else "sigue el subrayado o la lista de la pieza anterior" if dentro else ""
                txt = "; ".join(x for x in (txt, MS.resumen_maqueta(ctx, M, a_ - 0.6, b)) if x) or "—"
                L.append("| %s | %s | %s | %s |" % (VD_mmss(a_), tit, sg["texto"].replace("|", "/"), txt))
                tit = ""
    return "\n".join(L) + "\n"


def cmd_plano(a):
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto_v(trabajo)
    fp = os.path.join(trabajo, "plano.json")
    if getattr(a, "auto", False) and (a.borrador or not os.path.exists(fp)):   # el borrador de partida, siempre al día
        escribir(os.path.join(trabajo, "plano.borrador.json"), borrador_v(ctx))
        if not a.borrador and not ctx["Y"].get("fixture"):
            return falla("falta la fase Plano: %s no tiene plano.json. Lanza el Workflow «plano» (video-realizador) o escríbelo desde el borrador "
                         "(%s; `video.py plano %s --digesto`): el borrador solo no se publica" % (rel(trabajo), rel(os.path.join(trabajo, "plano.borrador.json")), rel(trabajo)))
    if a.borrador or (getattr(a, "auto", False) and not os.path.exists(fp)):
        shutil.copy(os.path.join(trabajo, "plano.borrador.json"), fp)
    if not os.path.exists(fp):
        return falla("no hay plano.json en %s (video_hf.py borrador, o importar-plano)" % rel(trabajo))
    P = leer(fp)
    if getattr(a, "con", None):   # las mesas de un archivo reemplazan a las del plano que cubren sus escenas (la maqueta de prueba: una mesa con maqueta 3D)
        nuevas = leer(a.con)
        nuevas = nuevas.get("mesas") or [nuevas] if isinstance(nuevas, dict) else nuevas
        claves = {c for m in nuevas for c in m.get("escenas") or []}
        P["mesas"] = [m for m in P.get("mesas") or [] if not claves & set(m.get("escenas") or [])] + nuevas
        P["mesas"].sort(key=lambda m: min([ctx["por_clave"].get(c, 10 ** 6) for c in m.get("escenas") or []] or [10 ** 6]))
        escribir(fp, P)
    mesas, f0 = resolver_v(ctx, P)
    f, av, med = revisar_v(ctx, P, mesas, f0)
    if a.hoja:
        open(os.path.join(trabajo, "plano.md"), "w", encoding="utf-8").write(hoja_v(ctx, mesas))
        print("hoja de golpes → %s" % rel(os.path.join(trabajo, "plano.md")))
    n = sum(len(M["golpes"]) for M in mesas)
    m = (med["capitulos"] or {}).get(1) or {"piezas": 0, "archivo_real": 0, "tipos": []}
    print("plano: %d mesas · %d piezas en %s (una cada %.1f s) · %d de %d oraciones con pieza nueva · %d de archivo real (%.0f %%) · %s" % (
        len(mesas), n, VD_mmss(ctx["total"]), ctx["total"] / max(1, n), med["con_pieza_nueva"], med["oraciones"], m["archivo_real"],
        100 * m["archivo_real"] / max(1, m["piezas"]), ", ".join(m["tipos"])))
    if med.get("maquetas"):
        print("  maquetas 3D: %s" % ", ".join("%s (%s, %.1f s)" % (M["id"], M["maqueta"].get("estilo"), M["fin"] - M["ini"]) for M in mesas if M["clase"] == "maqueta"))
    for x in av:
        print("AVISO", x)
    fix = bool(ctx["Y"].get("fixture"))
    for x in f:
        print("AVISO (maqueta)" if fix else "FALLA", x)
    ok = not f or fix
    print("RETORNO " + json.dumps({"archivo": rel(fp), "gate": "ok" if ok else "falla", "fallas": f[:40], "piezas": n, "archivo_real": m["archivo_real"]}, ensure_ascii=False))
    return 0 if ok or not a.check else 1


# ---------- piloto: rehacer en mesa una pieza ya producida, con su misma voz ----------
def cmd_piloto(a):
    src, dst = os.path.abspath(a.origen), os.path.abspath(a.trabajo)
    if not os.path.exists(os.path.join(src, "escenas.json")):
        return falla("%s no es un TRABAJO con escenas.json" % rel(src))
    prohibidas = [os.path.join(RAIZ, d) for d in ("series", "historias", "hilos", "datos", "explicaciones", "congreso", "noticias", "semanas")]
    if dst == src or any(dst.startswith(p + os.sep) for p in prohibidas) or dst.startswith(src + os.sep):
        return falla("el piloto va en una carpeta aparte de sesiones/ (nunca sobre el original ni dentro de un entregable)")
    os.makedirs(dst, exist_ok=True)
    for f in ("escenas.json", "guion.json", "locucion.json", "encuadre.json", "historia.json", "video.json", "paginas.json"):
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    for d_ in ("fotos", "base"):
        if os.path.isdir(os.path.join(src, d_)):
            shutil.copytree(os.path.join(src, d_), os.path.join(dst, d_), dirs_exist_ok=True)
    os.makedirs(os.path.join(dst, "audio"), exist_ok=True)
    for f in glob.glob(os.path.join(src, "audio", "voz_*_r.mp3")):
        enlazar(f, os.path.join(dst, "audio", os.path.basename(f)))
    st = leer(os.path.join(dst, "video.json"))
    st.update(realizacion="mesa", piloto_de=rel(src), hilo=rel(os.path.join(dst, "base")))
    if a.fixture:
        st["fixture"] = True   # la maqueta: los gates avisan en vez de fallar (su plano es el borrador)
    escribir(os.path.join(dst, "video.json"), st)
    print("piloto: %s → %s (misma voz; el original no se toca)" % (rel(src), rel(dst)))
    return 0


def cmd_importar(a):
    """Trae del plano del 16:9 (sesión de /youtube-long) los golpes de una parte: «Pk.eN» → «eN», sin `x`, `y` ni `w`;
    las fotos y las páginas que esos golpes usan se copian al TRABAJO."""
    trabajo, yt = os.path.abspath(a.trabajo), os.path.abspath(a.de)
    ctx = contexto_v(trabajo)
    P = leer(os.path.join(yt, "plano.json"))
    pre = "P%d." % a.parte
    PGy = leer(os.path.join(yt, "paginas.json")) if os.path.exists(os.path.join(yt, "paginas.json")) else {}
    fpg = os.path.join(trabajo, "paginas.json")
    PG = leer(fpg) if os.path.exists(fpg) else {}
    mesas, fotos = [], 0
    for M in P.get("mesas") or []:
        claves = [c[len(pre):] for c in M.get("escenas") or [] if c.startswith(pre)]
        claves = [c for c in claves if c in ctx["por_clave"]]
        if not claves:
            continue
        if any(ctx["es"][ctx["por_clave"][c]]["tipo"] in TABLEROS_V for c in claves):
            mesas += [{"escenas": [c], "golpes": []} for c in claves if ctx["es"][ctx["por_clave"][c]]["tipo"] in TABLEROS_V]
            continue
        gs = []
        for g in M.get("golpes") or []:
            esc_ = g.get("escena") or (M["escenas"][0] if M.get("escenas") else "")
            if not esc_.startswith(pre) or esc_[len(pre):] not in claves:
                continue
            g = {k: v for k, v in g.items() if k not in ("x", "y", "w", "giro")}
            g["escena"] = esc_[len(pre):]
            if g.get("foto"):
                for ext in (".json", ".jpg", ".png", ".jpeg", ".webp"):
                    s = os.path.join(yt, "fotos", g["foto"] + ext)
                    if os.path.exists(s) and not os.path.exists(os.path.join(trabajo, "fotos", g["foto"] + ext)):
                        shutil.copy2(s, os.path.join(trabajo, "fotos", g["foto"] + ext))
                        fotos += ext != ".json"
            if g.get("pagina") and g["pagina"] in PGy and g["pagina"] not in PG:
                PG[g["pagina"]] = PGy[g["pagina"]]
                arch = PGy[g["pagina"]].get("archivo")
                if arch and os.path.exists(os.path.join(yt, arch)):
                    os.makedirs(os.path.dirname(os.path.join(trabajo, arch)), exist_ok=True)
                    shutil.copy2(os.path.join(yt, arch), os.path.join(trabajo, arch))
            gs.append(g)
        mesa = {"escenas": claves, "golpes": gs}
        if isinstance(M.get("maqueta"), dict) and len(claves) == len(M.get("escenas") or []):   # la maqueta 3D de la mesa viaja entera (el clip se rehace en el lienzo vertical)
            mesa["maqueta"] = json.loads(json.dumps(M["maqueta"]))
            for grupo in ("camara", "eventos", "marcas"):
                for x in mesa["maqueta"].get(grupo) or []:
                    if isinstance(x, dict) and str(x.get("escena") or "").startswith(pre):
                        x["escena"] = x["escena"][len(pre):]
        mesas.append(mesa)
    if PG:
        escribir(fpg, PG)
    escribir(os.path.join(trabajo, "plano.json"), {"version": 1, "mesas": mesas})
    print("importar-plano: %d mesas · %d golpes · %d fotos copiadas → %s" % (len(mesas), sum(len(m["golpes"]) for m in mesas), fotos, rel(os.path.join(trabajo, "plano.json"))))
    return 0


# ---------- tableros, revisión, audio, render, montaje ----------
def alto_contenido(clip):
    """Hasta dónde llega lo dibujado en un clip de tablero (px de su alto, 1040): la última fila que se aparta del fondo en
    tres cuadros (30 %, 60 % y el final). Sirve para el marco, no es un gate: una tarjeta corta no deja medio marco vacío."""
    W, H = 190, 208
    try:
        dur = VD.ffprobe_dur(clip)
    except Exception:
        return None
    hasta = 0
    for f in (0.3, 0.6, 0.97):
        b = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "%.2f" % (dur * f), "-i", clip, "-frames:v", "1", "-vf", "scale=%d:%d,format=gray" % (W, H),
                            "-f", "rawvideo", "-"], capture_output=True).stdout
        if len(b) < W * H:
            continue
        fondo = sorted(b)[len(b) // 2]
        filas = [r for r in range(H) if sum(1 for c in range(W) if abs(b[r * W + c] - fondo) > 22) > 3]
        if filas:
            hasta = max(hasta, filas[-1] + 1)
    return int(round(hasta * TABLERO_LADOS[1] / float(H))) if hasta else None


def cmd_tableros(a):
    import youtube as YT
    trabajo = os.path.abspath(a.trabajo)
    st = VD.estado(trabajo)
    ns = argparse.Namespace(trabajo=trabajo, fps=a.fps, paralelo=None, solo=None, todo=a.todo, fuera=TABLERO_FUERA_V, tipos=TABLEROS_V, recorte=TABLERO_RECORTE_V,
                            formato_grabar=("tablero", "clips_limpios"), hilo_dir=VD.tarjetas_dir(trabajo, st) or os.path.join(trabajo, "base"), huella="v2|" + TABLERO_RECORTE_V + "|")
    rc = YT.cmd_grabar(ns)
    if rc:
        return rc
    for c in sorted(glob.glob(os.path.join(trabajo, "clips_tablero", "e*.mp4"))):
        fa = c[:-4] + ".alto.json"
        if not os.path.exists(fa) or os.path.getmtime(fa) < os.path.getmtime(c):
            h = alto_contenido(c)
            if h:
                escribir(fa, {"alto": h, "de": TABLERO_LADOS[1]})
    # y los otros clips que la mesa aloja: las maquetas 3D (`tableros --todo` rehace los tableros, no las maquetas: `maquetas --todo`)
    return cmd_maquetas(argparse.Namespace(trabajo=trabajo, fps=a.fps, todo=False))


def cmd_maquetas(a):
    """Las mesas con maqueta 3D del plano → clips_maqueta/<mesa>.mp4 (950×1040, un clip para 9:16 y 4:5), con caché por huella.
    MESA_RENDER=0: dobles sin render."""
    trabajo = os.path.abspath(a.trabajo)
    fp = os.path.join(trabajo, "plano.json")
    if not os.path.exists(fp):
        return 0   # sin plano no hay maquetas (el paso «plano» ya avisa)
    ctx = contexto_v(trabajo)
    mesas, _ = resolver_v(ctx, leer(fp))
    return MS.grabar_maquetas(ctx, mesas, fps=a.fps, todo=getattr(a, "todo", False))


def total_de(trabajo, fmt):
    """La duración del video de un formato ya proyectado (el plano más el bucle del final), o None."""
    f = os.path.join(trabajo, "hf", FORMATOS[fmt]["id"], "duracion.json")
    return leer(f)["total_s"] if os.path.exists(f) else None


def cmd_revisar(a):
    """hyperframes check y una hoja de contacto: cada mesa justo antes de cada repliegue y antes de barrerse (cuando más tiene)."""
    trabajo = os.path.abspath(a.trabajo)
    Fz = FORMATOS[a.formato]
    P = os.path.join(trabajo, "hf", Fz["id"])
    if not os.path.exists(os.path.join(P, "index.html")):
        return falla("falta el proyecto: video_hf.py proyecto %s --formato %s" % (rel(trabajo), a.formato))
    r = hf(P, "check", "--json")
    try:
        d = json.loads(r.stdout[r.stdout.index("{"):])
    except ValueError:
        return falla("hyperframes check no respondió: %s" % (r.stderr or r.stdout)[-300:])
    err = [x for k in ("lint", "runtime", "layout", "motion", "contrast", "craft", "audio") for x in (d.get(k) or {}).get("findings") or [] if x.get("severity") == "error"]
    adv = [x for k in ("lint", "runtime", "layout", "motion", "contrast", "craft") for x in (d.get(k) or {}).get("findings") or [] if x.get("severity") == "warning"]
    for x in err:
        print("FALLA %s %s" % (x.get("code"), (x.get("message") or "")[:200]))
    cuenta = {}
    for x in adv:
        cuenta[x.get("code")] = cuenta.get(x.get("code"), 0) + 1
    ts = []
    for m in leer(os.path.join(P, "mesas.json")):
        ts += [t - 0.12 for t in m["repliegues"] if t - 0.12 > m["ini"] + 0.3] + [max(m["ini"] + 0.2, m["fin"] - 0.6)]
    ts = sorted(set(round(t, 2) for t in ts))
    os.makedirs(os.path.join(trabajo, "revision"), exist_ok=True)
    hojas = []
    for k in range(0, len(ts), 18):
        s = hf(P, "snapshot", "--at", ",".join("%.2f" % t for t in ts[k:k + 18]))
        for h in re.findall(r"(\S+contact-sheet[^\s]*\.jpg)", s.stdout):
            dst = os.path.join(trabajo, "revision", "mesa_%s_%d.jpg" % (Fz["id"], len(hojas) + 1))
            shutil.copy(h, dst)
            hojas.append(dst)
    print("revisar %s: check %s · avisos %s · %d cuadros en %d hoja(s): %s" % (a.formato, "ok" if d.get("ok") and not err else "CON ERRORES", cuenta or "ninguno",
                                                                             len(ts), len(hojas), ", ".join(rel(h) for h in hojas)))
    return 1 if err or not d.get("ok") else 0


def cmd_portada(a):
    """La portada limpia (salida/portada.png): el cuadro del gancho con su golpe de arriba, sin subtítulos ni barra, justo
    antes del primer repliegue (cuando la primera mesa tiene más piezas)."""
    trabajo = os.path.abspath(a.trabajo)
    if armar(trabajo, "9:16", portada=True):
        return 1
    P = os.path.join(trabajo, "hf", "portada")
    m = leer(os.path.join(P, "mesas.json"))[0]
    t = round(min([x - 0.15 for x in m["repliegues"] if x - 0.15 > 0.3] + [m["fin"] - 0.6]), 2)
    tmp = os.path.join(P, "cuadros")
    shutil.rmtree(tmp, ignore_errors=True)
    r = hf(P, "snapshot", "--at", "%.2f" % t, "--no-end", "--keep", "-o", "cuadros")
    pngs = sorted(glob.glob(os.path.join(tmp, "*.png")))
    if not pngs:
        return falla("la portada no se dibujó: %s" % (r.stderr or r.stdout)[-300:])
    os.makedirs(os.path.join(trabajo, "salida"), exist_ok=True)
    shutil.copy(pngs[0], os.path.join(trabajo, "salida", "portada.png"))
    print("portada: el cuadro del gancho a los %.2f s → %s" % (t, rel(os.path.join(trabajo, "salida", "portada.png"))))
    return 0


def cmd_contacto(a):
    """La hoja de contacto del video ya montado (revision/contacto[_4x5].png): cada mesa cuando más piezas tiene."""
    trabajo = os.path.abspath(a.trabajo)
    Fz = FORMATOS[a.formato]
    video = os.path.join(trabajo, "salida", Fz["salida"])
    fm = os.path.join(trabajo, "hf", Fz["id"], "mesas.json")
    if not os.path.exists(video) or not os.path.exists(fm):
        return falla("falta %s o su proyecto: graba y monta --formato %s primero" % (rel(video), a.formato))
    ts = []
    for m in leer(fm):
        if m["id"] != "mb":
            ts += [t - 0.12 for t in m["repliegues"] if t - 0.12 > m["ini"] + 0.3] + [max(m["ini"] + 0.2, m["fin"] - 0.6)]
    ts = sorted(set(round(t, 2) for t in ts))
    paso = max(1, -(-len(ts) // 30))
    ts = ts[::paso]
    rev = os.path.join(trabajo, "revision")
    tmp = os.path.join(rev, "_contacto")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    alto = 480 if a.formato == "9:16" else 338
    for k, t in enumerate(ts):
        VD.ff("-ss", "%.2f" % t, "-i", video, "-frames:v", "1", "-vf", "scale=-2:%d" % alto, os.path.join(tmp, "%03d.png" % k))
    cols = 6
    out = os.path.join(rev, "contacto%s.png" % ("" if a.formato == "9:16" else "_4x5"))
    VD.ff("-framerate", "1", "-i", os.path.join(tmp, "%03d.png"), "-vf", "tile=%dx%d:margin=6:padding=6" % (cols, -(-len(ts) // cols)), "-frames:v", "1", out)
    shutil.rmtree(tmp, ignore_errors=True)
    print("contacto %s: %d cuadros → %s" % (a.formato, len(ts), rel(out)))
    return 0


def cmd_audio(a):
    import youtube as YT
    trabajo = os.path.abspath(a.trabajo)
    ctx = contexto_v(trabajo)
    fe = os.path.join(trabajo, "hf", "efectos.json")
    if not os.path.exists(fe):
        return falla("falta hf/efectos.json: video_hf.py proyecto primero")
    E, offs = ctx["E"], ctx["offs"]
    D = total_de(trabajo, "9:16") or ctx["total"]   # con el bucle del final
    segs = os.path.join(trabajo, "segs_mesa")
    os.makedirs(segs, exist_ok=True)
    os.makedirs(os.path.join(trabajo, "salida"), exist_ok=True)
    voz = YT.mezclar_voz(trabajo, E, offs, D, segs)
    fondo, pistas = YT.musica_por_capitulo(ctx["Y"], [{"t": 0.0}], D, segs)
    final, mf, n = YT.pista_final(voz, fondo, leer(fe), D, segs)
    YT.srt(E, offs, os.path.join(trabajo, "salida", "subtitulos.srt"))
    print("audio %s · %.1f LUFS · %.1f dBTP · %d efectos · música %s → %s" % (VD_mmss(D), mf["input_i"], mf["input_tp"], n, pistas[0], rel(final)))
    return 0


# ---------- el doble sin render (MESA_RENDER=0), por formato ----------
# Una maqueta no renderiza con HyperFrames: su «render» es un doble en negro de la duración exacta. Eso se anota POR FORMATO
# (un 4:5 de doble no queda limpio porque el 9:16 se haya vuelto a grabar de verdad):
#   hf/<formato>/render/.doble           el sello viaja con el render: lo pone el doble y lo quita un render de verdad
#   salida/.maqueta_sin_render.<formato> el video montado de ese formato viene de un doble: la pone el doble y la pone o la
#                                        quita `montar`, según el sello del render que monta
#   salida/.maqueta_sin_render           la general (VD.MESA_SIN_RENDER), la que leen los `entregar`: existe mientras
#                                        ALGÚN formato esté marcado
def sello_doble(trabajo, fid):
    return os.path.join(trabajo, "hf", fid, "render", ".doble")


def marca_doble(trabajo, fid=None):
    """La marca de salida/: la de un formato («9x16», «4x5») o, sin `fid`, la general que leen los `entregar`."""
    return os.path.join(trabajo, "salida", VD.MESA_SIN_RENDER + ("." + fid if fid else ""))


def dobles_sin_render(trabajo):
    """Los formatos cuyo video montado viene de un doble → ["9x16", "4x5"] (vacío: se puede entregar)."""
    return [Fz["id"] for Fz in FORMATOS.values() if os.path.exists(marca_doble(trabajo, Fz["id"]))]


def repartir_marca_vieja(trabajo):
    """Una marca general sin marcas por formato es de antes de que existieran y no dice de qué formato era: vale para todo
    formato que ya tenga render o video montado (cada uno queda con su sello y su marca hasta que se grabe de verdad)."""
    if dobles_sin_render(trabajo) or not os.path.exists(marca_doble(trabajo)):
        return
    for Fz in FORMATOS.values():
        r = os.path.join(trabajo, "hf", Fz["id"], "render")
        if os.path.exists(os.path.join(r, "video.mp4")) or os.path.exists(os.path.join(trabajo, "salida", Fz["salida"])):
            if os.path.isdir(r):
                open(sello_doble(trabajo, Fz["id"]), "w").write("MESA_RENDER=0 (marca general anterior a las marcas por formato)\n")
            open(marca_doble(trabajo, Fz["id"]), "w").write("MESA_RENDER=0 (marca general anterior a las marcas por formato)\n")


def marcar_doble(trabajo, fid, doble):
    """Anota si el video del formato `fid` viene de un doble (o ya no) y deja al día la marca general, que existe mientras
    algún formato siga marcado. → los formatos marcados."""
    os.makedirs(os.path.join(trabajo, "salida"), exist_ok=True)
    repartir_marca_vieja(trabajo)
    m = marca_doble(trabajo, fid)
    if doble:
        open(m, "w").write("MESA_RENDER=0\n")
    elif os.path.exists(m):
        os.remove(m)
    quedan, general = dobles_sin_render(trabajo), marca_doble(trabajo)
    if quedan:
        open(general, "w").write("MESA_RENDER=0\n%s\n" % " ".join(quedan))
    elif os.path.exists(general):
        os.remove(general)
    return quedan


def cmd_render(a):
    trabajo = os.path.abspath(a.trabajo)
    Fz = FORMATOS[a.formato]
    P = os.path.join(trabajo, "hf", Fz["id"])
    if not os.path.exists(os.path.join(P, "index.html")):
        return falla("falta el proyecto: video_hf.py proyecto %s --formato %s" % (rel(trabajo), a.formato))
    os.makedirs(os.path.join(P, "render"), exist_ok=True)
    out = os.path.join(P, "render", "video.mp4")
    D = total_de(trabajo, a.formato) or contexto_v(trabajo)["total"]
    sello = sello_doble(trabajo, Fz["id"])
    if os.environ.get("MESA_RENDER") == "0":   # las maquetas: un doble de la duración exacta, sin HyperFrames (el proyecto ya pasó su check)
        VD.ff("-f", "lavfi", "-i", "color=c=0x14100d:s=%dx%d:r=%d:d=%.4f" % (Fz["w"], Fz["h"], FPS, D), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out)
        open(sello, "w").write("MESA_RENDER=0\n")
        marcar_doble(trabajo, Fz["id"], True)
        print("render %s: doble sin render de %.2f s (MESA_RENDER=0; no se puede entregar) → %s" % (a.formato, D, rel(out)))
        return 0
    registro = os.path.join(P, "render", "render.log")
    limite = MS.limite_render(D)   # SIEMPRE un proceso (con varios el video tiembla) y con un límite proporcional a la duración
    rc, vencido = MS.render_hf(P, ["--quality", a.calidad, "--workers", "1", "-o", "render/video.mp4"], limite, registro)
    if vencido:
        return falla(MS.texto_limite("el render %s" % a.formato, limite, D, registro))
    if rc or not os.path.exists(out):
        return falla("el render falló (hyperframes %s; %s)" % (HF_VERSION, rel(registro)))
    repartir_marca_vieja(trabajo)   # una marca general de antes de las marcas por formato: se reparte ANTES de quitar el sello de este
    if os.path.exists(sello):
        os.remove(sello)             # este render ya es de verdad; la marca de salida/ la quita `montar` cuando lo monte
    d = VD.ffprobe_dur(out)
    print("render %s: %s (%.2f s; el plano dice %.2f s) → %s" % (a.formato, VD_mmss(d), d, D, rel(out)))
    if abs(d - D) > 2.0 / FPS + 0.05:
        return falla("la duración del video (%.2f s) no es la del plano (%.2f s)" % (d, D))
    return 0


def cmd_montar(a):
    trabajo = os.path.abspath(a.trabajo)
    Fz = FORMATOS[a.formato]
    video_solo = os.path.join(trabajo, "hf", Fz["id"], "render", "video.mp4")
    final = os.path.join(trabajo, "segs_mesa", "mezcla_final.wav")
    for f, como in ((video_solo, "render"), (final, "audio")):
        if not os.path.exists(f):
            return falla("falta %s: video_hf.py %s" % (rel(f), como))
    dv, da = VD.ffprobe_dur(video_solo), VD.ffprobe_dur(final)
    if abs(dv - da) > 0.35:
        return falla("el video dura %.2f s y el audio %.2f s: vuelve a correr proyecto, render y audio sobre el mismo plano" % (dv, da))
    os.makedirs(os.path.join(trabajo, "salida"), exist_ok=True)
    video = os.path.join(trabajo, "salida", Fz["salida"])
    VD.ff("-i", video_solo, "-i", final, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", video)
    mf = VD.medir(video)
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "json", video], capture_output=True, text=True).stdout)["streams"]
    v = next((s_ for s_ in pr if s_["codec_type"] == "video"), {})
    fallas = []
    if (v.get("width"), v.get("height")) != (Fz["w"], Fz["h"]):
        fallas.append("V8 tamaño %sx%s (se espera %d×%d)" % (v.get("width"), v.get("height"), Fz["w"], Fz["h"]))
    if abs(mf["input_i"] - VD.LUFS) > VD.LUFS_TOL or mf["input_tp"] > VD.TP_MAX:
        fallas.append("V8 sonoridad %.1f LUFS / %.1f dBTP (se espera %.0f ±%.1f, ≤ %.0f)" % (mf["input_i"], mf["input_tp"], VD.LUFS, VD.LUFS_TOL, VD.TP_MAX))
    print("video %s %s · %.1f LUFS · %.1f dBTP → %s" % (a.formato, VD_mmss(VD.ffprobe_dur(video)), mf["input_i"], mf["input_tp"], rel(video)))
    # el video montado es de verdad solo si su render lo es: la marca del formato sigue al sello del render (la general, a todas)
    dobles = marcar_doble(trabajo, Fz["id"], os.path.exists(sello_doble(trabajo, Fz["id"])))
    if dobles:
        print("  doble sin render (MESA_RENDER=0) en %s: no se puede entregar hasta grabar y montar de verdad %s"
              % (", ".join(dobles), "ese formato" if len(dobles) == 1 else "esos formatos"))
    for x in fallas:
        print("FALLA", x)
    return 1 if fallas else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    q = sub.add_parser("piloto")
    q.add_argument("origen")
    q.add_argument("--trabajo", required=True)
    q.add_argument("--fixture", action="store_true", help="marca la copia como maqueta")
    q.set_defaults(fn=cmd_piloto)
    q = sub.add_parser("importar-plano")
    q.add_argument("trabajo")
    q.add_argument("--de", required=True, help="la sesión de /youtube-long con plano.json")
    q.add_argument("--parte", type=int, required=True)
    q.set_defaults(fn=cmd_importar)
    q = sub.add_parser("borrador")
    q.add_argument("trabajo")
    q.set_defaults(fn=cmd_borrador)
    q = sub.add_parser("plano")
    q.add_argument("trabajo")
    q.add_argument("--check", action="store_true")
    q.add_argument("--hoja", action="store_true")
    q.add_argument("--borrador", action="store_true", help="usa plano.borrador.json tal cual (la maqueta)")
    q.add_argument("--auto", action="store_true", help="arma el borrador; en una maqueta lo usa si falta plano.json, y en un trabajo real se detiene")
    q.add_argument("--con", metavar="MESAS.json", help="reemplaza en plano.json las mesas de esas escenas por las del archivo (las maquetas de prueba)")
    q.set_defaults(fn=cmd_plano)
    for nombre, fn in (("tableros", cmd_tableros), ("maquetas", cmd_maquetas)):
        q = sub.add_parser(nombre)
        q.add_argument("trabajo")
        q.add_argument("--fps", type=int, default=30)
        q.add_argument("--todo", action="store_true")
        q.set_defaults(fn=fn)
    q = sub.add_parser("portada")
    q.add_argument("trabajo")
    q.set_defaults(fn=cmd_portada)
    for nombre, fn in (("proyecto", cmd_proyecto), ("revisar", cmd_revisar), ("render", cmd_render), ("montar", cmd_montar), ("contacto", cmd_contacto)):
        q = sub.add_parser(nombre)
        q.add_argument("trabajo")
        q.add_argument("--formato", default="9:16", choices=tuple(FORMATOS))
        if nombre == "render":
            q.add_argument("--calidad", default=os.environ.get("MESA_CALIDAD", "looks"), choices=("draft", "looks", "delivery"))
        q.set_defaults(fn=fn)
    q = sub.add_parser("audio")
    q.add_argument("trabajo")
    q.set_defaults(fn=cmd_audio)
    q = sub.add_parser("digesto")
    q.add_argument("trabajo")
    q.set_defaults(fn=cmd_digesto)
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return 2
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
