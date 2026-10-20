#!/usr/bin/env python3
"""Biblioteca FIJA de efectos de sonido de /video (design/sfx/). Se generó UNA sola vez con el nodo `sfx` de
ElevenLabs (eleven_text_to_sound_v2) y queda congelada: /video nunca genera efectos ni música.

  sfx.py --importar URLS.json   descarga cada efecto ({"whoosh": "<content_url>", …}), lo recorta (silencio inicial),
                                lo pasa a WAV mono 48 kHz 16-bit con pico común −3 dBFS y escribe/actualiza catalogo.json
                                (acepta también {"whoosh": {"url": …, "generation_id": …, "flow_id": …}})
  sfx.py --check                K2: catálogo completo (los 8 ids fijos), archivos presentes, duración coherente
  sfx.py                        lista el catálogo

Exit: 0 ok · 1 falla · 2 uso incorrecto.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import wave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(RAIZ, "design", "sfx")
CATALOGO = os.path.join(DIR, "catalogo.json")
PICO_DB = -3.0
# id → (uso, duración pedida, prompt, prompt_influence, ganancia relativa en la mezcla)
EFECTOS = {
    "whoosh": ("entrada de tarjeta", 0.7, "Short soft air whoosh, smooth and dry, close-mic, no tail", 0.6, -18),
    "tic": ("fin de conteo", 0.5, "Single short dry wooden tick, like a soft pencil tap on a desk, no reverb", 0.7, -14),
    "pulso": ("cifra del gancho completa", 0.6, "Single soft deep thump, muted kick-like, dry, quick decay", 0.6, -10),
    "impacto": ("escena golpe", 0.9, "Short cinematic impact with a muted low boom and a subtle tight click, dry, fast decay", 0.6, -10),
    "grave": ("giro (enlace «pero»)", 1.4, "Deep low sub-bass drop hit with a slow dark tail, cinematic, no high frequencies", 0.6, -8),
    "riser": ("2 s antes del pago", 2.0, "Two second tense filtered noise riser building steadily and cutting off cleanly at the end", 0.7, -16),
    "resolucion": ("pregunta del cierre", 1.6, "Soft warm synth pad chord swelling gently and resolving, short, calm", 0.5, -14),
    "foco": ("inicio del zoom", 0.6, "Very subtle soft airy sweep, quiet, like a slow breath, short", 0.5, -22),
}
IDS = tuple(EFECTOS)


def leer(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def duracion_wav(p):
    with wave.open(p, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def pico_db(p):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", out)
    return float(m.group(1)) if m else 0.0


def importar(ruta_urls):
    urls = leer(ruta_urls)
    os.makedirs(DIR, exist_ok=True)
    cat = leer(CATALOGO) if os.path.exists(CATALOGO) else {"version": 1, "efectos": []}
    por_id = {e["id"]: e for e in cat.get("efectos", [])}
    for sid, item in urls.items():
        if sid not in EFECTOS:
            print("ERROR: «%s» no es un efecto de la biblioteca (%s)" % (sid, ", ".join(IDS)), file=sys.stderr)
            return 1
        url = item["url"] if isinstance(item, dict) else item
        uso, dur, prompt, infl, gan = EFECTOS[sid]
        crudo = os.path.join(DIR, "_%s.crudo" % sid)
        tmp = os.path.join(DIR, "_%s.tmp.wav" % sid)
        final = os.path.join(DIR, "%s.wav" % sid)
        urllib.request.urlretrieve(url, crudo)
        # recorte del silencio inicial, 48 kHz mono, fade de salida de 50 ms
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", crudo, "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,aresample=48000,"
                        "areverse,afade=t=in:st=0:d=0.05,areverse", "-ac", "1", "-c:a", "pcm_s16le", tmp], check=True)
        ajuste = PICO_DB - pico_db(tmp)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af", "volume=%.2fdB" % ajuste,
                        "-ac", "1", "-c:a", "pcm_s16le", final], check=True)
        os.remove(crudo)
        os.remove(tmp)
        por_id[sid] = {"id": sid, "archivo": "%s.wav" % sid, "duracion_s": round(duracion_wav(final), 3), "uso": uso,
                       "ganancia_db": gan, "prompt": prompt, "prompt_influence": infl,
                       "generation_id": item.get("generation_id") if isinstance(item, dict) else None,
                       "flow_id": item.get("flow_id") if isinstance(item, dict) else None}
        print("%-11s %.2f s → %s" % (sid, por_id[sid]["duracion_s"], os.path.relpath(final, RAIZ)))
    cat = {"version": 1,
           "_comentario": "Biblioteca FIJA de efectos de /video, generada UNA vez con el nodo sfx (eleven_text_to_sound_v2) "
                          "e importada con scripts/sfx.py --importar. /video nunca genera efectos; para cambiar uno, "
                          "reimportar la url de otra variación.",
           "efectos": [por_id[i] for i in IDS if i in por_id]}
    with open(CATALOGO, "w", encoding="utf-8") as f:
        json.dump(cat, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("→ %s (%d efectos)" % (os.path.relpath(CATALOGO, RAIZ), len(cat["efectos"])))
    return 0


def fallas_k2():
    """K2: lista de fallas del catálogo de efectos (vacía si está completo y coherente)."""
    out = []
    if not os.path.exists(CATALOGO):
        return ["K2 falta design/sfx/catalogo.json (biblioteca de efectos de /video)"]
    try:
        cat = leer(CATALOGO)
    except ValueError as e:
        return ["K2 catalogo.json ilegible: %s" % e]
    vistos = {}
    for i, e in enumerate(cat.get("efectos", [])):
        sid = e.get("id")
        if sid in vistos:
            out.append("K2 efecto repetido %s" % sid)
        vistos[sid] = e
        if sid not in EFECTOS:
            out.append("K2 efectos[%d] id %r no es uno de los fijos (%s)" % (i, sid, ", ".join(IDS)))
            continue
        ruta = os.path.join(DIR, str(e.get("archivo", "")))
        if not os.path.isfile(ruta):
            out.append("K2 %s: falta design/sfx/%s" % (sid, e.get("archivo")))
            continue
        try:
            real = duracion_wav(ruta)
        except (wave.Error, EOFError) as ex:
            out.append("K2 %s: %s no es un WAV válido (%s)" % (sid, e.get("archivo"), ex))
            continue
        if not 0.2 <= real <= 4.0:
            out.append("K2 %s: dura %.2f s (se espera 0.2–4 s)" % (sid, real))
        if abs(real - float(e.get("duracion_s") or 0)) > 0.05:
            out.append("K2 %s: duracion_s %s no coincide con el archivo (%.2f s)" % (sid, e.get("duracion_s"), real))
        if not -40 <= float(e.get("ganancia_db", 1)) <= 0:
            out.append("K2 %s: ganancia_db %s fuera de −40–0" % (sid, e.get("ganancia_db")))
    for sid in IDS:
        if sid not in vistos:
            out.append("K2 falta el efecto «%s» (%s)" % (sid, EFECTOS[sid][0]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--importar", metavar="URLS.json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.importar:
        return importar(a.importar)
    if a.check:
        f = fallas_k2()
        for x in f:
            print("FALLA", x)
        print("[sfx] %d efecto(s) · %d falla(s)" % (len(IDS), len(f)))
        return 1 if f else 0
    if not os.path.exists(CATALOGO):
        print("sin catálogo: genera los efectos una vez y corre sfx.py --importar (ver referencias/flujo-video.md)")
        return 1
    for e in leer(CATALOGO)["efectos"]:
        print("%-11s %.2f s  %+3d dB · %s" % (e["id"], e["duracion_s"], e["ganancia_db"], e["uso"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
