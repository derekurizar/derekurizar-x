#!/usr/bin/env bash
# Hilos · pruebas del framework (sin agentes).
#
# Uso: bash scripts/test.sh          # completa (incluye make catalogo)
#      RAPIDO=1 bash scripts/test.sh # salta el catálogo
# Pasos: validate · catálogo · contar_x (py + js) · fixture (materializar + ensamblar --check)
#        · fixture dato (una tarjeta, modo dato de ensamblar) · negativos del gate G1–G8 sobre copias
#        de los fixtures (siempre con --salida: una copia nunca escribe en hilos/ ni datos/)
#        · negativos de render.js · banco de ideas (ideas.py sobre un banco temporal)
#        · informe de investigación (ejemplo → PDF en un temporal, negativos I1–I6, P1, P2; catálogo de
#          gráficos del informe: todos los G.* en papel, panel y media página con --check)
#        · node --check de hilo.js, ideas.js y dato.js · check_workflows.py (constantes, modos, gráficos W7–W8).
#        Resumen «N pruebas · M fallos»; exit 1 si hay fallos.
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
[[ "${1:-}" == "RAPIDO=1" ]] && RAPIDO=1
RAPIDO="${RAPIDO:-0}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
N=0; FALLOS=0
FIX=sesiones/_fixture   # fixture que copian los negativos (se cambia a _fixture_dato más abajo)

paso() {  # paso "nombre" comando...
  N=$((N+1)); local nombre="$1"; shift
  if "$@" >"$TMP/salida.log" 2>&1; then
    printf 'OK     %s\n' "$nombre"
  else
    FALLOS=$((FALLOS+1)); printf 'FALLO  %s (exit %s)\n' "$nombre" "$?"
    sed 's/^/       /' "$TMP/salida.log" | tail -15
  fi
}

# negativo "nombre" "GATE" "código python que muta guion.json (argv[1])" ["comando shell extra con $S"]
negativo() {
  N=$((N+1)); local nombre="$1" gate="$2" mut="$3" extra="${4:-}"
  local S; S="$(mktemp -d "$TMP/neg.XXXXXX")"
  cp -R "$FIX/." "$S/"; rm -rf "$S/salida"
  if [[ -n "$mut" ]] && ! python3 -c "$mut" "$S/guion.json" 2>"$TMP/mut.log"; then
    FALLOS=$((FALLOS+1)); printf 'FALLO  %s: la mutación falló\n' "$nombre"; sed 's/^/       /' "$TMP/mut.log"; return
  fi
  [[ -n "$extra" ]] && eval "$extra"
  # Siempre con --salida: una copia con smoke:false escribiría en hilos/ o datos/ (el entregable real).
  python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" >"$TMP/neg.out" 2>"$TMP/neg.err"; local rc=$?
  if [[ $rc -eq 1 ]] && grep -q "$gate" "$TMP/neg.err"; then
    printf 'OK     %s → %s\n' "$nombre" "$gate"
  else
    FALLOS=$((FALLOS+1)); printf 'FALLO  %s: esperaba exit 1 con %s (exit %s)\n' "$nombre" "$gate" "$rc"
    sed 's/^/       /' "$TMP/neg.err" | head -8
  fi
}

MUT_PREFIJO='import json,sys; p=sys.argv[1]; g=json.load(open(p, encoding="utf-8")); T=g["tuits"]; '
MUT_SUFIJO='; json.dump(g, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)'
mut() { printf '%s%s%s' "$MUT_PREFIJO" "$1" "$MUT_SUFIJO"; }

echo "== validate / catálogo / contar_x"
paso "validate.py" python3 scripts/validate.py
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make catalogo (RAPIDO=1)"; else paso "make catalogo" make catalogo; fi
paso "contar_x.py --vectores" python3 scripts/contar_x.py --vectores
paso "contar_x.js --vectores" node scripts/contar_x.js --vectores

echo "== fixture"
paso "materializar.py sesiones/_fixture" python3 scripts/materializar.py sesiones/_fixture
paso "ensamblar.py sesiones/_fixture --check" python3 scripts/ensamblar.py sesiones/_fixture --check
comprobar_salida() {
  local d=sesiones/_fixture/salida f
  for f in hilo.html post.md datos.json hilo.json tuit_1.png tuit_2.png tuit_3.png; do
    [[ -s "$d/$f" ]] || { echo "falta $d/$f"; return 1; }
  done
  [[ "$(ls "$d"/tuit_*.png | wc -l | tr -d ' ')" -eq 3 ]] || { echo "se esperaban 3 PNG en $d"; return 1; }
  python3 -c 'import json,sys; h=json.load(open(sys.argv[1])); assert h.get("modo")=="hilo", h.get("modo")' "$d/hilo.json" || { echo "hilo.json sin modo hilo"; return 1; }
}
paso "salida del fixture (hilo.html, post.md, datos.json, hilo.json, 3 PNG)" comprobar_salida
paso "post.md marca la 2ª fuente no independiente (pre-c04)" bash -c 'grep -q "ajustada · 2ª fuente no indep." sesiones/_fixture/salida/post.md'
paso "digesto.py marca (2ª no indep.) en pre-c04" bash -c 'python3 scripts/digesto.py sesiones/_fixture --para guionista | grep "pre-c04" | grep -q "2ª no indep"'

echo "== estado final y memoria.py (sobre el fixture, sin escribir memoria/)"
solo_estado() {
  local d=sesiones/_fixture/salida
  python3 scripts/ensamblar.py sesiones/_fixture --solo-estado --estado incompleto >/dev/null || return 1
  python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))["estado"]=="incompleto" else 1)' "$d/hilo.json" || { echo "hilo.json no dice incompleto"; return 1; }
  grep -q '^- \*\*Estado:\*\* incompleto' "$d/post.md" || { echo "post.md no dice incompleto"; return 1; }
  grep -q '"estado": *"incompleto"' "$d/hilo.html" || { echo "hilo.html no dice incompleto"; return 1; }
  python3 scripts/ensamblar.py sesiones/_fixture --solo-estado --estado borrador >/dev/null
}
paso "ensamblar.py --solo-estado --estado incompleto (hilo.json, post.md, hilo.html)" solo_estado
paso "ensamblar.py --solo-estado sin --estado (exit 2)" bash -c '! python3 scripts/ensamblar.py sesiones/_fixture --solo-estado >/dev/null 2>&1'
paso "memoria.py rechaza --hook G1 (exit 2)" bash -c '! python3 scripts/memoria.py --registrar sesiones/_fixture --ruta sesiones/_fixture/salida --hook G1 --dry-run >/dev/null 2>&1'
memoria_dry() {
  python3 scripts/memoria.py --registrar sesiones/_fixture --ruta sesiones/_fixture/salida --hook giro_inversion --dry-run 2>/dev/null | grep -q "hook giro_inversion"
}
paso "memoria.py --dry-run acepta --hook giro_inversion" memoria_dry

echo "== fixture dato (una tarjeta: modo dato de ensamblar.py)"
paso "materializar.py sesiones/_fixture_dato" python3 scripts/materializar.py sesiones/_fixture_dato
paso "ensamblar.py sesiones/_fixture_dato --check" python3 scripts/ensamblar.py sesiones/_fixture_dato --check
comprobar_salida_dato() {
  local d=sesiones/_fixture_dato/salida f
  for f in dato.png tarjeta.html dato.html post.md datos.json dato.json; do [[ -s "$d/$f" ]] || { echo "falta $d/$f"; return 1; }; done
  [[ "$(ls "$d"/*.png | wc -l | tr -d ' ')" -eq 1 ]] || { echo "se esperaba exactamente 1 PNG en $d"; return 1; }
  [[ ! -e "$d/contacto.png" && ! -e "$d/hilo.json" && ! -e "$d/hilo.html" ]] || { echo "un dato no lleva contacto.png ni hilo.*"; return 1; }
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["tipo"]=="dato" and d.get("modo")=="dato" and "tuits" not in d and d["tuit"]["imagen"]=="dato.png" and d["dato"] and d["candidatas"]' "$d/dato.json"
}
paso "salida del dato (6 archivos, 1 PNG, sin contacto.png ni hilo.json)" comprobar_salida_dato
solo_estado_dato() {
  local d=sesiones/_fixture_dato/salida
  python3 scripts/ensamblar.py sesiones/_fixture_dato --solo-estado --estado incompleto >/dev/null || return 1
  python3 -c 'import json,sys; sys.exit(0 if json.load(open(sys.argv[1]))["estado"]=="incompleto" else 1)' "$d/dato.json" || { echo "dato.json no dice incompleto"; return 1; }
  grep -q '^- \*\*Estado:\*\* incompleto' "$d/post.md" || { echo "post.md no dice incompleto"; return 1; }
  grep -q '"estado": *"incompleto"' "$d/dato.html" || { echo "dato.html no dice incompleto"; return 1; }
  python3 scripts/ensamblar.py sesiones/_fixture_dato --solo-estado --estado borrador >/dev/null
}
paso "ensamblar.py --solo-estado sobre un dato (dato.json, dato.html, post.md)" solo_estado_dato
paso "ensamblar.py rechaza --salida hilos/ para un dato (exit 2, no crea nada)" bash -c 'python3 scripts/ensamblar.py sesiones/_fixture_dato --salida hilos/_prueba_dato >/dev/null 2>&1; rc=$?; [[ ! -e hilos/_prueba_dato ]] || { rm -rf hilos/_prueba_dato; exit 1; }; [[ $rc -eq 2 ]]'
paso "ensamblar.py rechaza --salida datos/ para un hilo (exit 2, no crea nada)" bash -c 'python3 scripts/ensamblar.py sesiones/_fixture --salida datos/_prueba_hilo >/dev/null 2>&1; rc=$?; [[ ! -e datos/_prueba_hilo ]] || { rm -rf datos/_prueba_hilo; exit 1; }; [[ $rc -eq 2 ]]'
memoria_dato_dry() {
  python3 scripts/memoria.py --registrar sesiones/_fixture_dato --ruta sesiones/_fixture_dato/salida --dry-run 2>/dev/null | grep -q "memoria/datos.json" || { echo "el dry-run no apunta a memoria/datos.json"; return 1; }
  python3 scripts/memoria.py --datos "crudo brent" >/dev/null
}
paso "memoria.py --registrar --dry-run de un dato → memoria/datos.json (y --datos)" memoria_dato_dry
paso "digesto.py --para productor con 1 tuit" bash -c 'python3 scripts/digesto.py sesiones/_fixture_dato --para productor | grep -q "tuits: 1"'

echo "== negativos del gate en modo dato (copias de _fixture_dato)"
FIX=sesiones/_fixture_dato
negativo "dato con 2 tuits"                    G1 "$(mut 'T.append(dict(T[0], n=2, beat="cierre"))')"
negativo "dato con beat giro"                  G1 "$(mut 'T[0]["beat"]="giro"')"
negativo "dato sin hook_tipo"                  G1 "$(mut 'g.pop("hook_tipo", None)')"
negativo "dato sin visual en T1"               G3 "$(mut 'T[0]["visual"]=None')"
negativo "dato: cifra no_confirmada dat-c02"   G3 "$(mut 'T[0]["visual"]["cifra_ids"]=["dat-c02"]')"
negativo "dato: número sin respaldo"           G4 "$(mut 'T[0]["visual"]["datos"]["cifra"]["valor"]=999')"
negativo "dato: texto repite el titular"       G2 "$(mut 'T[0]["texto"]="El crudo cerró septiembre en US$102. ¿Y ahora qué pasa con el diésel? El dato, en una tarjeta."')"
negativo "dato: texto repite 2 números"        G2 "$(mut 'T[0]["texto"]="Brent a US$102 tras US$67 en enero: ¿qué pasó con el diésel en Guatemala? El dato, en una tarjeta."')"
negativo "dato: texto de 20 caracteres"        G2 "$(mut 'T[0]["texto"]="Dato corto sin peso."')"
negativo "dato: falta visuales/tuit_1.png"     G5 "" 'rm -f "$S/visuales/tuit_1.png"'
negativo "dato: modo desconocido zzz"          "G1 modo" "$(mut 'g["modo"]="zzz"')"
negativo "dato: modo de hilo (explica)"        "G1 modo" "$(mut 'g["modo"]="explica"')"
negativo "tipo desconocido zzz"                "G1 tipo" "$(mut 'g["tipo"]="zzz"')" 'python3 -c "import json,sys; p=sys.argv[1]; e=json.load(open(p)); e[\"tipo\"]=\"zzz\"; json.dump(e, open(p,\"w\"), ensure_ascii=False, indent=2)" "$S/encuadre.json"'
negativo "modo mapa con plantilla cifra"        "G1 modo mapa" "$(mut 'g["modo"]="mapa"; g["mapa"]={"per_capita": True, "denominador": "poblacion INE 2026"}')"
negativo "modo antes con gancho giro_inversion"  "G1 modo antes" "$(mut 'g["modo"]="antes"; g["hook_tipo"]="giro_inversion"; g["antes"]={"anio_antes": 2016, "anio_despues": 2026, "nominal": False}')"
negativo "modo antes sin bloque antes"           "G1 modo antes" "$(mut 'g["modo"]="antes"')"
negativo "modo vs sin Guatemala en paises"       "G1 modo vs" "$(mut 'g["modo"]="vs"; g["vs"]={"paises": ["Honduras", "El Salvador"], "fuente_comun": "WDI", "periodo": "2024", "per_capita": True}')"
negativo "modo vs con «ganamos» en el texto"     "G1 modo vs" "$(mut 'g["modo"]="vs"; g["vs"]={"paises": ["Guatemala", "Honduras"], "fuente_comun": "WDI", "periodo": "2024", "per_capita": True}; T[0]["texto"]="Le ganamos a Honduras otra vez con el precio del crudo. El dato, en una tarjeta."')"
positivo_dato_antes() {
  local S; S="$(mktemp -d "$TMP/pos.XXXXXX")"; cp -R sesiones/_fixture_dato/. "$S/"; rm -rf "$S/salida"
  python3 -c "$(mut 'g["modo"]="antes"; g["antes"]={"anio_antes": 2016, "anio_despues": 2026, "nominal": False}')" "$S/guion.json" || return 1
  python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" >/dev/null || return 1
  python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["modo"]=="antes" and d["antes"]["anio_antes"]==2016, d.get("modo")' "$S/salida/dato.json" || { echo "dato.json sin modo antes o sin su bloque"; return 1; }
  grep -q '^- \*\*Modo:\*\* antes' "$S/salida/post.md" || { echo "post.md sin la línea de modo"; return 1; }
  grep -q '^## Modo antes' "$S/salida/post.md" || { echo "post.md sin la sección del modo"; return 1; }
  grep -q '"modo": *"antes"' "$S/salida/dato.html" || { echo "dato.html sin el modo en su JSON"; return 1; }
}
paso "modo antes válido: dato.json, post.md y dato.html llevan el modo y su bloque" positivo_dato_antes
FIX=sesiones/_fixture

echo "== negativos del gate mecánico (copias del fixture)"
negativo "titular de 30 caracteres"         G3 "$(mut 'T[1]["visual"]["titular"]=["x"*30]')"
negativo "fuente con URL"                   G3 "$(mut 'T[1]["visual"]["fuente"]="https://x"')"
negativo "cifra_ids desconocida pre-c99"    G3 "$(mut 'T[1]["visual"]["cifra_ids"]=["pre-c99"]')"
negativo "número sin respaldo (items[1])"   G4 "$(mut 'T[2]["visual"]["datos"]["items"][1]["valor"]=123456')"
negativo "engagement bait en T2"            G2 "$(mut 'T[1]["texto"]="dale RT si te gustó"')"
negativo "T1 de 300 caracteres"             G2 "$(mut 'T[0]["texto"]="a"*300')"
negativo "dos beats giro"                   G1 "$(mut 'T[2]["beat"]="giro"')"
negativo "falta visuales/tuit_2.png"        G5 "" 'rm -f "$S/visuales/tuit_2.png"'
negativo "ajuste sin consolidar"            G5 "" 'echo "{\"nota\":\"x\"}" > "$S/visuales/tuit_2.ajuste.json"'
negativo "T2 con imagen de 201 caracteres"  G2 "$(mut 'T[1]["texto"]="x"*201')"
negativo "T1 repite el titular de su tarjeta" G2 "$(mut 'T[0]["texto"]="El crudo cerró septiembre en US$102. ¿Y ahora qué pasa con el diésel? Hilo con datos."')"
negativo "T1 repite 2 números de su tarjeta" G2 "$(mut 'T[0]["texto"]="Brent a US$102 tras US$67 en enero: ¿qué pasó con el diésel en Guatemala? Hilo con datos."')"
negativo "tarjeta dice récord sin serie"     G7 "$(mut 'T[1]["visual"]["titular"]=["Llenar el tanque","récord de 2026"]')"
negativo "cierre sin nombrar las fuentes"    G8 "$(mut 'T[2]["texto"]="Eso es todo por hoy. Gracias por leer hasta aquí."')"
negativo "hook_tipo desconocido"             G1 "$(mut 'g["hook_tipo"]="clickbait"')"
negativo "modo desconocido zzz"              "G1 modo" "$(mut 'g["modo"]="zzz"')"
negativo "modo de dato (mapa) en un hilo"    "G1 modo" "$(mut 'g["modo"]="mapa"')"
negativo "modo explica dejando el giro"      "G1 modo explica" "$(mut 'g["modo"]="explica"; g["explica"]={"pregunta": "¿Cómo cerró el crudo?", "pasos": [{"n": 2, "titulo": "De enero a septiembre"}]}')"
negativo "modo explica sin bloque explica"   "G1 modo explica" "$(mut 'g["modo"]="explica"; T[1]["beat"]="paso"')"
negativo "modo perfil con 3 tuits"           "G1 modo perfil" "$(mut 'g["modo"]="perfil"; g["smoke"]=False; T[1]["beat"]="dimension"; g["perfil"]={"sujeto": "El crudo", "tipo": "grupo", "dimensiones": [{"n": 2, "nombre": "precio", "anio": 2026}]}')" 'python3 -c "import json,sys; p=sys.argv[1]; e=json.load(open(p)); e[\"smoke\"]=False; e[\"fixture\"]=False; json.dump(e, open(p,\"w\"), ensure_ascii=False, indent=2)" "$S/encuadre.json"'
positivo_hilo_explica() {
  local S; S="$(mktemp -d "$TMP/pos.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"; rm -rf "$S/salida"
  python3 -c "$(mut 'g["modo"]="explica"; T[1]["beat"]="paso"; g["explica"]={"pregunta": "¿Cómo cerró el crudo?", "pasos": [{"n": 2, "titulo": "De enero a septiembre"}]}')" "$S/guion.json" || return 1
  python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" --sin-contacto >/dev/null || return 1
  python3 -c 'import json,sys; h=json.load(open(sys.argv[1])); assert h["modo"]=="explica" and h["explica"]["pasos"][0]["n"]==2, h.get("modo")' "$S/salida/hilo.json" || { echo "hilo.json sin modo explica o sin su bloque"; return 1; }
  grep -q '^## Modo explica' "$S/salida/post.md" || { echo "post.md sin la sección del modo"; return 1; }
  grep -q '"modo": *"explica"' "$S/salida/hilo.html"
}
paso "modo explica válido (3 tuits, sin giro, beat paso): hilo.json, post.md y hilo.html llevan el modo" positivo_hilo_explica
positivo_hilo_perfil() {
  local S; S="$(mktemp -d "$TMP/pos.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"; rm -rf "$S/salida"
  # 5 tuits: T1 gancho · T2–T4 dimension (copias de la tarjeta de T2, rotuladas «Guatemala») · T5 cierre (la antigua T3).
  cp "$S/visuales/tuit_3.html" "$S/visuales/tuit_5.html"; cp "$S/visuales/tuit_3.png" "$S/visuales/tuit_5.png"
  cp "$S/visuales/tuit_2.html" "$S/visuales/tuit_3.html"; cp "$S/visuales/tuit_2.png" "$S/visuales/tuit_3.png"
  cp "$S/visuales/tuit_2.html" "$S/visuales/tuit_4.html"; cp "$S/visuales/tuit_2.png" "$S/visuales/tuit_4.png"
  python3 - "$S/guion.json" <<'EOF' || return 1
import copy, json, sys
p = sys.argv[1]; g = json.load(open(p, encoding="utf-8")); T = g["tuits"]
dim = T[1]; dim["beat"] = "dimension"; dim["visual"]["datos"]["antes"]["sub"] = "promedio nacional de Guatemala"
cierre = T[2]; cierre["n"] = 5
g["tuits"] = [T[0], dim, dict(copy.deepcopy(dim), n=3), dict(copy.deepcopy(dim), n=4), cierre]
g["modo"] = "perfil"
g["perfil"] = {"sujeto": "El crudo", "tipo": "grupo", "dimensiones": [{"n": 2, "nombre": "enero", "anio": 2026}, {"n": 3, "nombre": "abril", "anio": 2026}, {"n": 4, "nombre": "septiembre", "anio": 2026}]}
json.dump(g, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
EOF
  python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" --sin-contacto >"$TMP/perfil.log" 2>&1 || { tail -5 "$TMP/perfil.log"; return 1; }
  python3 -c 'import json,sys; h=json.load(open(sys.argv[1])); assert h["modo"]=="perfil" and h["n_tuits"]==5 and len(h["perfil"]["dimensiones"])==3' "$S/salida/hilo.json" || { echo "hilo.json sin modo perfil, 5 tuits y 3 dimensiones"; return 1; }
  python3 scripts/memoria.py --registrar "$S" --ruta sesiones/_fixture/salida --dry-run 2>/dev/null | grep -q "modo perfil"
}
paso "modo perfil válido (5 tuits, beat dimension, bloque perfil): ensambla y memoria.py --dry-run dice modo perfil" positivo_hilo_perfil
negativo "modo normal con 3 tuits"           G1 "$(mut 'g["smoke"]=False')" 'python3 -c "import json,sys; p=sys.argv[1]; e=json.load(open(p)); e[\"smoke\"]=False; e[\"fixture\"]=False; json.dump(e, open(p,\"w\"), ensure_ascii=False, indent=2)" "$S/encuadre.json"'

echo "== negativos de render.js"
render_neg_url() {
  python3 scripts/nuevo_visual.py cifra "$TMP/neg_url.html" >/dev/null || return 1
  python3 - "$TMP/neg_url.html" <<'EOF' || return 1
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s2, k = re.subn(r'(const DATA = \{.*?\bfuente:\s*)"[^"]*"', r'\1"https://eia.gov"', s, count=1, flags=re.S)
assert k == 1, "no se encontró fuente en DATA"
open(p, "w", encoding="utf-8").write(s2)
EOF
  if node scripts/render.js "$TMP/neg_url.html" --check >"$TMP/r.log" 2>&1; then echo "render.js aceptó una fuente con URL"; cat "$TMP/r.log"; return 1; fi
  return 0
}
paso "render.js rechaza fuente https://eia.gov (exit 1)" render_neg_url
render_neg_r1() {
  python3 scripts/nuevo_visual.py cifra "$TMP/neg_r1.html" >/dev/null || return 1
  python3 - "$TMP/neg_r1.html" <<'EOF' || return 1
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
assert "</body>" in s
open(p, "w", encoding="utf-8").write(s.replace("</body>", '<div style="font-size:12px">x</div></body>', 1))
EOF
  if node scripts/render.js "$TMP/neg_r1.html" --check >"$TMP/r.log" 2>&1; then echo "render.js aceptó texto de 12px"; return 1; fi
  grep -q "R1" "$TMP/r.log" || { echo "exit 1 pero sin R1 en la salida:"; cat "$TMP/r.log"; return 1; }
  return 0
}
paso "render.js rechaza texto de 12px con R1" render_neg_r1
# render_neg_datos <plantilla> <js que rompe DATA>: el render() de la plantilla debe rechazarlo (exit 1, «DATA:»).
render_neg_datos() {
  local f="$TMP/neg_$1.html"
  python3 scripts/nuevo_visual.py "$1" "$f" >/dev/null || return 1
  python3 - "$f" "$2" <<'EOF' || return 1
import sys
p, js = sys.argv[1], sys.argv[2]; s = open(p, encoding="utf-8").read()
assert "\nfunction render(D)" in s, "sin function render(D)"
open(p, "w", encoding="utf-8").write(s.replace("\nfunction render(D)", "\n" + js + "\nfunction render(D)", 1))
EOF
  if node scripts/render.js "$f" --check >"$TMP/r.log" 2>&1; then echo "render.js aceptó: $2"; return 1; fi
  grep -q "DATA:" "$TMP/r.log" || { echo "exit 1 pero sin «DATA:»:"; tail -5 "$TMP/r.log"; return 1; }
}
paso "bullet rechaza 8 items"                 render_neg_datos bullet 'DATA.items = DATA.items.concat(DATA.items);'
paso "embudo rechaza etapas que crecen"       render_neg_datos embudo 'DATA.etapas.reverse();'
paso "embudo exige misma_cohorte"             render_neg_datos embudo 'delete DATA.misma_cohorte;'
paso "divergente rechaza 16 items"            render_neg_datos divergente 'DATA.items = DATA.items.concat(DATA.items);'
paso "apilada rechaza valores desparejos"     render_neg_datos apilada 'DATA.partes[0].valores.pop();'
paso "piramide rechaza 3 grupos"              render_neg_datos piramide 'DATA.grupos = DATA.grupos.slice(0, 3);'
paso "treemap rechaza 2 partes"               render_neg_datos treemap 'DATA.partes = DATA.partes.slice(0, 2);'
paso "dispersion rechaza 5 puntos"            render_neg_datos dispersion 'DATA.puntos = DATA.puntos.slice(0, 5);'
paso "barras-v rechaza periodo invertido"     render_neg_datos barras-v 'DATA.periodos = [{ desde: 3, hasta: 1, nombre: "x" }];'
paso "hemiciclo rechaza bloques que no suman" render_neg_datos hemiciclo 'DATA.bloques[0].curules += 5;'
paso "multiples rechaza 3 paneles"            render_neg_datos multiples 'DATA.paneles = DATA.paneles.slice(0, 3);'
paso "combinado rechaza linea desparejada"    render_neg_datos combinado 'DATA.linea.valores.pop();'
paso "linea-tiempo rechaza 2 eventos"         render_neg_datos linea-tiempo 'DATA.eventos = DATA.eventos.slice(0, 2);'
paso "agrupadas rechaza más de 3 series"      render_neg_datos agrupadas 'DATA.series = DATA.series.concat(DATA.series);'
paso "pictograma rechaza destacado > total"   render_neg_datos pictograma 'DATA.destacado = DATA.total + 1;'
paso "area-apilada rechaza valores desparejos" render_neg_datos area-apilada 'DATA.partes[0].valores.pop();'
paso "cascada rechaza fin que no cuadra"      render_neg_datos cascada 'DATA.fin.valor += 1000;'
paso "cascada rechaza efecto desconocido"     render_neg_datos cascada 'DATA.pasos[0].efecto = "quita";'

echo "== banco de ideas (banco y hilos temporales; no toca ideas/ ni memoria/)"
IB="$TMP/ideas"; mkdir -p "$IB/in"
cat > "$IB/hilos.json" <<'JSON'
{"version": 1, "hilos": [{"id": "2026-01-01-canasta", "tema": "canasta basica", "tesis": "", "estado": "listo", "idea_id": "canasta-basica-vs-salario"}]}
JSON
cat > "$IB/in/ideas_prueba.json" <<'JSON'
{"grupo": "prueba", "ideas": [
 {"id": "canasta-basica-vs-salario", "titulo": "Canasta básica frente al salario mínimo", "area": "economia", "pregunta": "¿Cuántas horas de salario mínimo cuesta la canasta básica alimentaria?", "por_que_ahora": "INE publicó septiembre", "hook_sugerido": "escala_humana", "paleta_sugerida": "maiz", "datos": [{"fuente": "INE", "indicador": "CBA", "url": "https://www.ine.gob.gt/x", "formato": "pdf", "periodo": "2016–2026", "evidencia": "Costo de la CBA a septiembre"}], "puntaje": {"interes": 5, "datos": 4, "actualidad": 4}},
 {"id": "salario-minimo-canasta-basica", "titulo": "Salario mínimo y canasta básica", "area": "economia", "pregunta": "¿El salario mínimo alcanza para la canasta básica alimentaria?", "por_que_ahora": "x", "hook_sugerido": "escala_humana", "paleta_sugerida": "maiz", "datos": [{"fuente": "INE", "indicador": "CBA", "url": "https://a.gt", "evidencia": "cita de prueba"}], "puntaje": {"interes": 3, "datos": 3, "actualidad": 3}},
 {"id": "electricidad-tarifa", "titulo": "Tarifa eléctrica social", "area": "energia", "pregunta": "¿Cuánto pagan los hogares por kWh desde el subsidio?", "por_que_ahora": "ajuste trimestral de la CNEE", "hook_sugerido": "antes_despues", "paleta_sugerida": "cielo", "datos": [{"fuente": "CNEE", "indicador": "pliego tarifario", "url": "https://www.cnee.gob.gt/x", "formato": "pdf", "periodo": "2016–2026", "evidencia": "Pliego tarifario trimestral"}], "puntaje": {"interes": 4, "datos": 4, "actualidad": 3}},
 {"id": "sin-evidencia", "titulo": "Idea sin datos", "area": "economia", "pregunta": "x", "por_que_ahora": "y", "datos": [], "puntaje": {"interes": 3, "datos": 3, "actualidad": 3}}
]}
JSON
ideas_cmd() { python3 scripts/ideas.py --banco "$IB/banco.json" --hilos "$IB/hilos.json" "$@"; }
ideas_importar() {
  ideas_cmd --importar "$IB/in" --fecha 2026-01-01 >"$IB/imp.log" || return 1
  grep -q "2 nuevas · 1 repetidas · 1 inválidas" "$IB/imp.log" || { cat "$IB/imp.log"; return 1; }
  [[ -s "$IB/README.md" ]] || { echo "no se generó README.md"; return 1; }
}
paso "ideas.py --importar (2 nuevas, 1 repetida por palabras clave, 1 sin evidencia)" ideas_importar
ideas_siguiente() { ideas_cmd --siguiente | grep -q '"id": "canasta-basica-vs-salario"'; }
paso "ideas.py --siguiente devuelve la de mayor puntaje" ideas_siguiente
ideas_hecha_sin_hilo() { ideas_cmd --marcar electricidad-tarifa --estado hecha >/dev/null 2>&1; [[ $? -eq 2 ]]; }
paso "ideas.py --marcar hecha sin --hilo (exit 2)" ideas_hecha_sin_hilo
ideas_conciliar() {
  ideas_cmd --conciliar >/dev/null || return 1
  ideas_cmd --ver canasta-basica-vs-salario | grep -q '"estado": "hecha"' || { echo "la idea enlazada no quedó hecha"; return 1; }
  grep -q "2026-01-01-canasta" "$IB/README.md" || { echo "README.md sin el hilo de la idea hecha"; return 1; }
}
paso "ideas.py --conciliar marca hecha la idea enlazada desde hilos.json" ideas_conciliar
memoria_idea_smoke() {
  local S; S="$(mktemp -d "$TMP/idea.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"
  python3 -c 'import json,sys; p=sys.argv[1]; e=json.load(open(p)); e["idea_id"]="x-y"; json.dump(e, open(p,"w"))' "$S/encuadre.json"
  python3 scripts/memoria.py --registrar "$S" --ruta sesiones/_fixture/salida --dry-run 2>/dev/null | grep -q "banco de ideas no se toca"
}
paso "memoria.py no marca ideas en sesiones smoke/fixture" memoria_idea_smoke

echo "== calendario editorial (calendario temporal; no toca ideas/)"
CAL="$TMP/cal"; mkdir -p "$CAL/in"
cat > "$CAL/calendario.json" <<'JSON'
{"version": 1, "entradas": [
 {"id": "dia-de-la-nina", "fecha": "10-11", "tipo": "dia_internacional", "titulo": "Día de la Niña", "pista": "niñas madres", "formato": "dato", "modo": null, "estado": "pendiente"},
 {"id": "remesas-mensual", "fecha": "07", "tipo": "publicacion", "titulo": "Banguat publica remesas", "pista": "remesas del mes", "formato": "dato", "modo": null, "estado": "pendiente"},
 {"id": "terremoto-1976", "fecha": "02-04", "tipo": "efemeride", "titulo": "Terremoto de 1976", "pista": "hace N años", "formato": "dato", "modo": "antes", "anio_origen": 1976, "estado": "hecha", "ultimo_uso": "2026-02-04"},
 {"id": "elecciones-2027", "fecha": "2027-06-20", "tipo": "evento", "titulo": "Elecciones 2027", "pista": "padrón", "formato": "hilo", "modo": null, "estado": "pendiente"},
 {"id": "pliegos-cnee", "fecha": ["01-31", "10-31"], "tipo": "publicacion", "titulo": "Pliegos CNEE", "pista": "tarifa del trimestre", "formato": "dato", "modo": null, "estado": "pendiente"}
]}
JSON
cat > "$CAL/in/calendario_prueba.json" <<'JSON'
{"entradas": [
 {"id": "dia-de-la-nina", "fecha": "10-11", "tipo": "dia_internacional", "titulo": "Día de la Niña", "pista": "x", "formato": "dato"},
 {"id": "dia-mundial-agua", "fecha": "03-22", "tipo": "dia_internacional", "titulo": "Día Mundial del Agua", "pista": "cobertura de agua por departamento", "formato": "dato", "modo": "mapa"},
 {"id": "mal-modo", "fecha": "03-23", "tipo": "evento", "titulo": "Entrada con modo de hilo en un dato", "pista": "x", "formato": "dato", "modo": "explica"}
]}
JSON
cal_cmd() { python3 scripts/calendario.py --calendario "$CAL/calendario.json" "$@"; }
cal_proximas() {
  cal_cmd --proximas 30 --fecha 2026-10-11 >"$CAL/p.log" || return 1
  grep -q "2026-10-11 (hoy) · dia-de-la-nina" "$CAL/p.log" || { cat "$CAL/p.log"; return 1; }
  grep -q "2026-11-07 (en 27 días) · remesas-mensual" "$CAL/p.log" || { cat "$CAL/p.log"; return 1; }
  grep -q "2026-10-31 (en 20 días) · pliegos-cnee" "$CAL/p.log" || { cat "$CAL/p.log"; return 1; }
  ! grep -q "terremoto-1976\|elecciones-2027" "$CAL/p.log" || { echo "salió una entrada fuera de ventana"; cat "$CAL/p.log"; return 1; }
  cal_cmd --proximas 200 --fecha 2026-10-11 | grep -q "2027-02-04 (en 116 días) · terremoto-1976 .* hace 51 años" || { echo "la efeméride hecha en 2026 no vuelve en 2027"; return 1; }
}
paso "calendario.py --proximas (hoy, mensual, lista de fechas, hecha vuelve al año siguiente)" cal_proximas
paso "calendario.py --dia 10-11 encuentra el Día de la Niña" bash -c 'python3 scripts/calendario.py --calendario "'"$CAL"'/calendario.json" --dia 10-11 --fecha 2026-10-11 | grep -q dia-de-la-nina'
paso "calendario.py --dia 2027-06-20 encuentra la puntual" bash -c 'python3 scripts/calendario.py --calendario "'"$CAL"'/calendario.json" --dia 2027-06-20 | grep -q elecciones-2027'
paso "calendario.py --buscar \"remesas\" (FUERTE)" bash -c 'python3 scripts/calendario.py --calendario "'"$CAL"'/calendario.json" --buscar "remesas del mes" | grep -q "FUERTE.*remesas-mensual"'
cal_importar() {
  cal_cmd --importar "$CAL/in" --fecha 2026-10-11 >"$CAL/imp.log" || return 1
  grep -q "1 nuevas · 1 repetidas · 1 inválidas" "$CAL/imp.log" || { cat "$CAL/imp.log"; return 1; }
  cal_cmd --ver dia-mundial-agua | grep -q '"modo": "mapa"'
}
paso "calendario.py --importar (1 nueva, 1 repetida por id, 1 inválida por modo)" cal_importar
cal_marcar() {
  cal_cmd --marcar dia-mundial-agua --estado hecha --pieza datos/2026-03-22-agua --fecha 2026-03-22 >/dev/null || return 1
  cal_cmd --ver dia-mundial-agua | grep -q '"ultimo_uso": "2026-03-22"' || return 1
  cal_cmd --marcar no-existe --estado hecha >/dev/null 2>&1; [[ $? -eq 1 ]]
}
paso "calendario.py --marcar hecha anota ultimo_uso y pieza; id inexistente → exit 1" cal_marcar
paso "calendario.py --proximas sobre la semilla real" python3 scripts/calendario.py --proximas 30

echo "== informe de investigación (investigacion/; salida en un temporal, no toca el ejemplo)"
INF=investigacion/ejemplos/dengue-2026
paso "informe.py $INF --check (gates I1–I6 + render P1–P5 + PDF)" python3 scripts/informe.py "$INF" --salida "$TMP/informe" --check
pdf_paginas() {  # 21 hojas Letter; la 8 apaisada
  python3 - "$TMP/informe/informe.pdf" <<'PY'
import re, sys
cajas = re.findall(rb"/MediaBox\s*\[\s*0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)\s*\]", open(sys.argv[1], "rb").read())
dims = [(round(float(w)), round(float(h))) for w, h in cajas]
assert len(dims) == 21, "el PDF tiene %d páginas" % len(dims)
assert dims[7] == (792, 612), "la página 8 no es apaisada: %s" % (dims[7],)
assert all(d == (612, 792) for i, d in enumerate(dims) if i != 7), "hojas que no son Letter vertical"
PY
}
paso "PDF: 21 hojas Letter, la 8 apaisada" pdf_paginas

# neg_informe "nombre" "GATE" "python que muta R (informe.json) y puede escribir archivos en D (carpeta temporal)" [render]
neg_informe() {
  N=$((N+1)); local nombre="$1" gate="$2" mut="$3" render="${4:-}"
  local D; D="$(mktemp -d "$TMP/inf.XXXXXX")"
  cp "$INF/informe.json" "$D/"
  if ! python3 -c 'import json,sys; D=sys.argv[1]; p=D+"/informe.json"; R=json.load(open(p,encoding="utf-8")); P=R["paginas"]
'"$mut"'
json.dump(R, open(p,"w",encoding="utf-8"), ensure_ascii=False)' "$D" 2>"$TMP/mut.log"; then
    FALLOS=$((FALLOS+1)); printf 'FALLO  %s: la mutación falló\n' "$nombre"; sed 's/^/       /' "$TMP/mut.log"; return
  fi
  python3 scripts/informe.py "$D" --salida "$D/salida" $([[ -n "$render" ]] && echo --check || echo --sin-pdf) >"$TMP/neg.out" 2>"$TMP/neg.err"; local rc=$?
  if [[ $rc -eq 1 ]] && grep -q "$gate" "$TMP/neg.err"; then printf 'OK     %s → %s\n' "$nombre" "$gate"
  else FALLOS=$((FALLOS+1)); printf 'FALLO  %s: esperaba exit 1 con %s (exit %s)\n' "$nombre" "$gate" "$rc"; sed 's/^/       /' "$TMP/neg.err" | head -8; fi
}
neg_informe "página de tipo desconocido"         I1 'P[2]["tipo"]="zzz"'
neg_informe "cifra del resumen con otro valor"    I2 'P[2]["cifras"][0]["valor"]="12,700"'
neg_informe "serie del tablero con otro valor"    I2 'P[3]["cifras"][0]["grafico"]["valores"][0]=9999'
neg_informe "cifra no_confirmada en datos.json"   I2 'd=json.load(open(R["meta"]["datos"][0],encoding="utf-8")); [c.update(veredicto="no_confirmada") for c in d["cifras"] if c["id"]=="ser-c01"]; json.dump(d,open(D+"/datos.json","w",encoding="utf-8")); R["meta"]["datos"]=[D+"/datos.json"]'
neg_informe "URL en la tesis"                     I3 'P[2]["tesis"]+=" https://x.org"'
neg_informe "figura sin fuente"                   I4 'P[5]["bloques"][2].pop("fuente")'
neg_informe "referencia {fig:} sin destino"       I5 'P[5]["bloques"][1]["parrafos"][0]+=" Ver {fig:nada}."'
neg_informe "paleta desconocida"                  I6 'R["meta"]["paleta"]="zzz"'
neg_informe "página que desborda la hoja"         P2 'P[5]["bloques"][1]["parrafos"]*=12' render
neg_informe "gráfico con nombre desconocido"       I1 'P[5]["bloques"][2]["grafico"]["tipo"]="barras-x"'
neg_informe "linea sin cero y sin nota"            I1 'P[9]["bloques"][2]["grafico"]["yDesdeCero"]=False; P[9]["bloques"][2].pop("nota",None)'
neg_informe "tarjeta con un número sin respaldo"   I2 'f=P[6]["bloques"][2]["items"][0]; f["cifra_ids"]=["ser-c08"]; f["datos"]["valores"][0]=24'
neg_informe "gráfico con cifra_ids y número ajeno"  I2 'P[5]["bloques"][2]["grafico"]["valores"][2]=5214'
pos_informe() {  # el nombre de la plantilla (kebab) vale como grafico.tipo; una tarjeta con cifra_ids y datos exactos pasa I2
  local D; D="$(mktemp -d "$TMP/inf.XXXXXX")"; cp "$INF/informe.json" "$D/"
  python3 -c 'import json,sys; D=sys.argv[1]; p=D+"/informe.json"; R=json.load(open(p,encoding="utf-8")); P=R["paginas"]
P[5]["bloques"][2]["grafico"]["tipo"]="barras-v"; f=P[6]["bloques"][2]["items"][0]; f["cifra_ids"]=["ser-c08"]
json.dump(R, open(p,"w",encoding="utf-8"), ensure_ascii=False)' "$D" || return 1
  python3 scripts/informe.py "$D" --salida "$D/salida" --sin-pdf >/dev/null 2>"$TMP/pos.err" || { cat "$TMP/pos.err"; return 1; }
}
paso "informe.py admite grafico.tipo en kebab y coteja una tarjeta con cifra_ids (I2 por contrato)" pos_informe
paso "catalogo_informe.py → informe.json + datos.json sintético" python3 scripts/catalogo_informe.py --dir "$TMP/catalogo" --tarjeta ninguna
paso "informe.py catálogo --check (todos los G.* en papel, panel y media página: I1–I7 + P1–P5)" python3 scripts/informe.py "$TMP/catalogo" --salida "$TMP/catalogo/salida" --check
neg_texto_pequeno() {  # P1: el render rechaza texto por debajo de 12 px
  sed 's#</style>#.p { font-size: 10px !important; }</style>#' "$TMP/informe/informe.html" > "$TMP/informe/p1.html"
  node scripts/render_informe.js "$TMP/informe/p1.html" --check >"$TMP/p1.log" 2>&1 && return 1
  grep -q "P1 " "$TMP/p1.log"
}
paso "render_informe.js rechaza texto de 10 px (P1)" neg_texto_pequeno

echo "== sintaxis de los workflows"
check_js() {
  { echo "(async function(){"; sed 's/^export //' ".claude/workflows/$1"; echo "})"; } > "$TMP/check_$1"
  node --check "$TMP/check_$1"
}
paso "node --check hilo.js (envuelto en async function)" check_js hilo.js
paso "node --check ideas.js (envuelto en async function)" check_js ideas.js
paso "node --check dato.js (envuelto en async function)" check_js dato.js
paso "check_workflows.py (PALETAS, PLANTILLAS, HOOKS, BEATS, REQ, pesoX, MODOS y gráficos del informe W7–W8)" python3 scripts/check_workflows.py

echo
echo "[test] $N pruebas · $FALLOS fallos"
[[ $FALLOS -eq 0 ]] || exit 1
exit 0
