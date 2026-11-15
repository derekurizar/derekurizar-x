#!/usr/bin/env python3
"""Poda los INTERMEDIOS de render de los trabajos de sesiones/ cuya pieza ya está ENTREGADA Y REGISTRADA.

Uso:
  python3 scripts/podar_intermedios.py                 lista lo que borraría, con su tamaño y el total (no borra nada)
  python3 scripts/podar_intermedios.py --borrar        lo borra (make podar-intermedios CONFIRMAR=1)
  python3 scripts/podar_intermedios.py --solo sesiones/historia-<slug>   un solo trabajo (o una carpeta con varios)
  python3 scripts/podar_intermedios.py --raiz DIR      otra raíz con memoria/, sesiones/ y las entregas (pruebas)

Qué es un trabajo entregado (las tres cosas; si alguna no se puede comprobar, el trabajo NO se toca y se dice por qué):
  1. su archivo de estado (video.json, youtube.json o video3d.json) casa con un registro de memoria/ por slug:
     videos.json (/video, /departamento), historias.json, explicaciones.json, sabias.json, congreso.json, videos3d.json,
     youtube.json y, para una parte de /serie, series.json + el serie.json de la serie (la parte «entregada» cuyo
     `trabajo` es esta carpeta: una copia o una versión vieja de la serie no cuenta);
  2. el registro no está «incompleto» y su carpeta de entrega existe con guion.json y el video final;
  3. el video de salida/ del trabajo es el mismo archivo que el entregado (mismo tamaño y mismos extremos): si el trabajo
     se volvió a grabar después de entregar, está en uso y no se toca.

Qué borra (solo lo que `grabar`, `montar` y `revisar` vuelven a generar):
  segs*/                        los tramos y las mezclas del montaje (segs, segs_4x5, segs_mesa, segs_16x9…)
  clips*/                       los clips por escena (clips, clips_4x5, clips_16x9, clips_tablero); NO clips_maqueta*
                                (las piezas 3D: rehacerlas es caro)
  hf/<proyecto>/render/         el render de HyperFrames, su caché (.hyperframes/) y, en un proyecto generado por
                                `proyecto` (con mesas.json), sus assets copiados
  revision/c_*.png              los cuadros sueltos de la revisión (las hojas de contacto y los .json se quedan)
  lo mismo dentro de tablero/ y variante_b/

Qué conserva SIEMPRE: audio/ (la voz grabada cuesta créditos), los guiones, plano*.json, escenas.json, locucion.json,
fotos/, base/, tarjetas/, salida/, clips_maqueta*/ y todo lo demás: con eso el video se puede volver a renderizar.
Nunca entra en carpetas que empiezan con «_» (maquetas, cachés) ni sigue enlaces simbólicos.

Exit: 0 ok · 1 no se pudo borrar algo · 2 uso incorrecto.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTADOS_OK = ("listo", "publicado", "publicable", "entregada")
# registro de memoria/ por tipo de trabajo: (archivo, clave de la carpeta de entrega)
REGISTROS = {"video": ("videos", "ruta_video"), "historia": ("historias", "ruta"), "explica": ("explicaciones", "ruta"),
             "sabias": ("sabias", "ruta"), "congreso": ("congreso", "ruta"), "video3d": ("videos3d", "ruta")}
ESTADO_DE = ("youtube.json", "video3d.json", "video.json")   # el archivo de estado de un TRABAJO (youtube.json manda: lleva además un video.json copiado)
RE_CUADRO = re.compile(r"^c_(?:[0-9a-z]+_)?\d+\.(?:png|jpg)$")
SUBTRABAJOS = ("tablero", "variante_b")       # carpetas de un TRABAJO con sus propios intermedios
PROFUNDIDAD = 3                               # sesiones/<a>/<b>/<c>: hasta dónde se buscan trabajos


def leer(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def lista_de(d):
    """Las entradas de un registro de memoria/ ({…, "<clave>": [ … ]} o una lista)."""
    if isinstance(d, list):
        return [x for x in d if isinstance(x, dict)]
    if isinstance(d, dict):
        return [x for x in next((v for v in d.values() if isinstance(v, list)), []) if isinstance(x, dict)]
    return []


def tamano(ruta):
    """Bytes de un archivo o de una carpeta entera, sin seguir enlaces simbólicos."""
    if os.path.islink(ruta) or os.path.isfile(ruta):
        return os.lstat(ruta).st_size
    total = 0
    for base, dirs, archivos in os.walk(ruta, followlinks=False):
        for n in archivos + [d for d in dirs if os.path.islink(os.path.join(base, d))]:
            try:
                total += os.lstat(os.path.join(base, n)).st_size
            except OSError:
                pass
    return total


def legible(b):
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024 or u == "GB":
            return ("%d %s" if u == "B" else "%.1f %s") % (b, u)
        b /= 1024.0


def huella(ruta):
    """Tamaño + sha1 del primer y del último MB: basta para saber si dos videos son el mismo archivo sin leerlos enteros."""
    n = os.path.getsize(ruta)
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        h.update(f.read(1 << 20))
        if n > (1 << 20):
            f.seek(max(0, n - (1 << 20)))
            h.update(f.read(1 << 20))
    return n, h.hexdigest()


def trabajos(sesiones, solo=None):
    """Las carpetas de TRABAJO (con archivo de estado) bajo sesiones/ (o bajo `solo`), sin las que empiezan con «_»."""
    raices = [solo] if solo else [os.path.join(sesiones, n) for n in sorted(os.listdir(sesiones)) if not n.startswith("_")]
    out = []

    def bajar(d, nivel):
        if not os.path.isdir(d) or os.path.islink(d) or os.path.basename(d).startswith("_"):
            return
        if any(os.path.isfile(os.path.join(d, e)) for e in ESTADO_DE):
            out.append(d)
        if nivel < PROFUNDIDAD:
            for n in sorted(os.listdir(d)):
                if n not in SUBTRABAJOS + ("nuevas", "base", "audio", "fotos", "salida", "revision", "hf") and not n.startswith(("segs", "clips", ".")):
                    bajar(os.path.join(d, n), nivel + 1)
    for r in raices:
        bajar(r, 1)
    return out


def entrega_de(trabajo, raiz):
    """(carpeta de entrega relativa, de dónde sale) si el TRABAJO está entregado y registrado; si no, (None, motivo)."""
    rel = os.path.relpath(trabajo, raiz)
    mem = lambda nombre: lista_de(leer(os.path.join(raiz, "memoria", nombre + ".json")))   # noqa: E731
    archivo = next(e for e in ESTADO_DE if os.path.isfile(os.path.join(trabajo, e)))
    st = leer(os.path.join(trabajo, archivo))
    if not isinstance(st, dict) or not st.get("slug"):
        return None, "%s ilegible o sin slug" % archivo
    if st.get("fixture"):
        return None, "es una maqueta (fixture)"
    if archivo == "youtube.json":
        reg = next((r for r in mem("youtube") if r.get("slug") == st["slug"]), None)
        if not reg:
            return None, "sin registro en memoria/youtube.json"
        ruta, origen, estado = reg.get("carpeta"), "youtube.json", reg.get("estado")
    else:
        ser = st.get("serie") if isinstance(st.get("serie"), dict) else {}
        if ser.get("parte"):
            reg = next((r for r in mem("series") if r.get("slug") == ser.get("slug")), None)
            if not reg:
                return None, "su serie no está en memoria/series.json"
            S = leer(os.path.join(raiz, reg.get("carpeta") or "", "serie.json")) or {}
            p = next((x for x in S.get("partes") or [] if x.get("n") == ser["parte"]), None)
            if not p:
                return None, "la serie entregada no tiene esa parte (%s/serie.json)" % reg.get("carpeta")
            if os.path.normpath(p.get("trabajo") or "") != os.path.normpath(rel):
                return None, "la parte %s de la serie se entregó desde %s, no desde aquí (una copia o una versión vieja)" % (ser["parte"], p.get("trabajo"))
            ruta, origen, estado = p.get("ruta"), "series.json", p.get("estado")
        elif ser:
            return None, "es la base de una serie (la investigación compartida), no una pieza"
        else:
            tipo = st.get("tipo") or "video"
            if tipo not in REGISTROS:
                return None, "tipo «%s»: este flujo no se poda" % tipo
            nombre, clave = REGISTROS[tipo]
            regs = [r for r in mem(nombre) if r.get("slug") == st["slug"]]
            if tipo == "video":   # <hilo>/video y <hilo>/video-corto se registran aparte: casa la carpeta del trabajo
                regs = [r for r in regs if os.path.basename(os.path.normpath(r.get(clave) or "")) == os.path.basename(trabajo)]
            if not regs:
                return None, "sin registro en memoria/%s.json" % nombre
            ruta, origen, estado = regs[0].get(clave), nombre + ".json", regs[0].get("estado")
    if estado not in ESTADOS_OK:
        return None, "registrado como «%s»" % estado
    if not ruta or os.path.isabs(ruta):
        return None, "el registro no dice dónde se entregó"
    dest = os.path.join(raiz, ruta)
    if not os.path.isfile(os.path.join(dest, "guion.json")):
        return None, "la entrega %s no tiene guion.json" % ruta
    ent, sal = os.path.join(dest, "video.mp4"), os.path.join(trabajo, "salida", "video.mp4")
    if not os.path.isfile(ent):
        return None, "la entrega %s no tiene video.mp4 (no se puede comprobar que esté entregado)" % ruta
    if not os.path.isfile(sal):
        return None, "el trabajo no tiene salida/video.mp4 para compararlo con el entregado"
    if huella(sal) != huella(ent):
        return None, "salida/video.mp4 no es el video entregado (se volvió a grabar después: está en uso)"
    return ruta, origen


def intermedios(trabajo, anidado=True):
    """Las rutas que se pueden borrar de un TRABAJO entregado (carpetas y archivos, sin enlaces simbólicos seguidos)."""
    out = []
    for n in sorted(os.listdir(trabajo)):
        p = os.path.join(trabajo, n)
        if not os.path.isdir(p):
            continue
        if n == "segs" or n.startswith("segs_") or n == "clips" or (n.startswith("clips_") and not n.startswith("clips_maqueta")):
            out.append(p)
        elif n == "hf" and not os.path.islink(p):
            for proy in sorted(os.listdir(p)):
                d = os.path.join(p, proy)
                if not os.path.isdir(d) or os.path.islink(d):
                    continue
                generado = os.path.isfile(os.path.join(d, "mesas.json"))
                out += [os.path.join(d, x) for x in ("render", ".hyperframes") + (("assets",) if generado else ())
                        if os.path.lexists(os.path.join(d, x))]
        elif n == "revision" and not os.path.islink(p):
            out += [os.path.join(p, x) for x in sorted(os.listdir(p)) if RE_CUADRO.match(x) and os.path.isfile(os.path.join(p, x))]
        elif n in SUBTRABAJOS and anidado and not os.path.islink(p):
            out += intermedios(p, anidado=False)
    return out


def borrar(ruta, sesiones):
    """Borra un intermedio; solo si está DENTRO de sesiones/ (un enlace simbólico se quita sin seguirlo)."""
    real = os.path.realpath(os.path.dirname(ruta))
    if os.path.commonpath([real, os.path.realpath(sesiones)]) != os.path.realpath(sesiones):
        raise OSError("%s queda fuera de %s" % (ruta, sesiones))
    if os.path.islink(ruta) or os.path.isfile(ruta):
        os.remove(ruta)
    else:
        shutil.rmtree(ruta)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--borrar", action="store_true", help="borra lo listado (sin esto, solo lista)")
    ap.add_argument("--solo", metavar="DIR", help="un trabajo o una carpeta de sesiones/ (relativa a la raíz o absoluta)")
    ap.add_argument("--raiz", default=RAIZ, help="raíz con memoria/, sesiones/ y las carpetas de entrega (por defecto, el repositorio)")
    ap.add_argument("--sin-motivos", action="store_true", help="no lista los trabajos que no se tocan")
    a = ap.parse_args()
    raiz = os.path.abspath(a.raiz)
    sesiones = os.path.join(raiz, "sesiones")
    if not os.path.isdir(sesiones) or not os.path.isdir(os.path.join(raiz, "memoria")):
        print("%s no tiene sesiones/ y memoria/" % raiz, file=sys.stderr)
        return 2
    solo = None
    if a.solo:
        solo = os.path.abspath(a.solo if os.path.isabs(a.solo) else os.path.join(raiz, a.solo))
        if not os.path.isdir(solo) or os.path.commonpath([os.path.realpath(solo), os.path.realpath(sesiones)]) != os.path.realpath(sesiones) \
                or os.path.realpath(solo) == os.path.realpath(sesiones):
            print("--solo: una carpeta dentro de %s" % os.path.relpath(sesiones, raiz), file=sys.stderr)
            return 2
    total, n_ok, sin_tocar, errores = 0, 0, [], 0
    for t in trabajos(sesiones, solo):
        rel = os.path.relpath(t, raiz)
        ruta, origen = entrega_de(t, raiz)
        if not ruta:
            sin_tocar.append((rel, origen))
            continue
        cosas = [(p, tamano(p)) for p in intermedios(t)]
        if not cosas:
            continue
        n_ok += 1
        sub = sum(b for _, b in cosas)
        total += sub
        print("%s  →  %s (memoria/%s) · %s" % (rel, ruta, origen, legible(sub)))
        for p, b in cosas:
            nombre = os.path.relpath(p, t) + ("/" if os.path.isdir(p) and not os.path.islink(p) else "")
            if a.borrar:
                try:
                    borrar(p, sesiones)
                    print("    borrado  %-34s %10s" % (nombre, legible(b)))
                except OSError as ex:
                    errores += 1
                    total -= b
                    print("    ERROR    %-34s %s" % (nombre, ex))
            else:
                print("    %-43s %10s" % (nombre, legible(b)))
    if sin_tocar and not a.sin_motivos:
        print("\nNo se tocan (%d): no consta que estén entregados y registrados" % len(sin_tocar))
        for rel, motivo in sin_tocar:
            print("    %s — %s" % (rel, motivo))
    print("\n[podar-intermedios] %d trabajo(s) entregado(s) con intermedios · %s %s%s" % (
        n_ok, legible(total), "liberados" if a.borrar else "por liberar",
        "" if a.borrar or not n_ok else " · nada se borró: make podar-intermedios CONFIRMAR=1 (o --borrar)"))
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
