#!/usr/bin/env bash
# Hilos · pruebas del framework (sin agentes).
#
# Uso: bash scripts/test.sh          # completa (incluye make catalogo)
#      RAPIDO=1 bash scripts/test.sh # salta el catálogo
# Pasos: validate · catálogo · contar_x (py + js) · fixture (materializar + ensamblar --check)
#        · fixture del informe (sesiones/_fixture/informe.json sobre la salida del fixture: I1–I7 + P1–P5,
#          digesto --para redactor, memoria.py --informe en dry-run, --informes)
#        · fixture dato (una tarjeta, modo dato de ensamblar) · negativos del gate G1–G8 sobre copias
#          (incluidos los del modo investigacion: bloque, marcador [ENLACE AL INFORME], rango de tuits)
#        de los fixtures (siempre con --salida: una copia nunca escribe en hilos/ ni datos/)
#        · negativos de render.js · banco de ideas (ideas.py sobre un banco temporal)
#        · informe de investigación (ejemplo → PDF en un temporal, negativos I1–I6, P1, P2; catálogo de
#          gráficos del informe: todos los G.* en papel, panel y media página con --check)
#        · /video: numeros_es, gate V1–V5+V9 con sus negativos, K2 (efectos fijos), make video-fixture (V6–V8, V10,
#          ducking medido) · node --check de hilo.js, ideas.js, dato.js, investigacion.js y video.js · check_workflows.py (W1–W10).
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

echo "== fixture del informe (sesiones/_fixture/informe.json sobre la salida del fixture; sin agentes)"
pdf_hojas() {  # pdf_hojas <pdf> <n>: cuenta las hojas por /MediaBox
  python3 - "$1" "$2" <<'PY2'
import re, sys
cajas = re.findall(rb"/MediaBox\s*\[\s*0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)\s*\]", open(sys.argv[1], "rb").read())
assert len(cajas) == int(sys.argv[2]), "el PDF tiene %d páginas (se esperaban %s)" % (len(cajas), sys.argv[2])
PY2
}
paso "informe.py sesiones/_fixture --check (I1–I7 + P1–P5; tarjetas con desde_hilo)" python3 scripts/informe.py sesiones/_fixture --salida "$TMP/informe_fixture" --check
paso "PDF del fixture: 8 hojas" pdf_hojas "$TMP/informe_fixture/informe.pdf" 8
paso "informe.html del fixture: la página tarjetas se expandió desde hilo.json (item 3/3 · cierre)" grep -q '"n": "3/3", "beat": "cierre"' "$TMP/informe_fixture/informe.html"
paso "digesto.py --para redactor imprime series completas y el guion" bash -c 'python3 scripts/digesto.py sesiones/_fixture --para redactor --hilo sesiones/_fixture/salida | grep -q "serie: Ene=67" && python3 scripts/digesto.py sesiones/_fixture --para redactor | grep -q "^## guion"'
paso "digesto.py --para redactor --eje precios (sin guion ni síntesis)" bash -c '! python3 scripts/digesto.py sesiones/_fixture --para redactor --eje precios | grep -q "^## guion"'
paso "memoria.py --registrar --informe sesiones/_fixture --dry-run → memoria/informes.json (N.º 00)" bash -c 'python3 scripts/memoria.py --registrar sesiones/_fixture --ruta sesiones/_fixture/salida --informe sesiones/_fixture --dry-run 2>/dev/null | grep "informes.json" | grep -q "N.º 00"'
paso "memoria.py --solo-informe exige el hilo ya registrado (exit 1)" bash -c '! python3 scripts/memoria.py --registrar sesiones/_fixture --ruta sesiones/_fixture/salida --informe sesiones/_fixture --solo-informe --dry-run >/dev/null 2>&1'
paso "memoria.py --informes da el siguiente N.º" bash -c 'python3 scripts/memoria.py --informes | grep -q "^siguiente N.º [0-9][0-9]"'

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
negativo "modo de hilo (investigacion) en un dato" "G1 modo" "$(mut 'g["modo"]="investigacion"')"
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
# Modo investigacion (/investigacion): bloque guion.investigacion y marcador [ENLACE AL INFORME] en el cierre.
INV_BLOQUE='g["investigacion"]={"numero": "01", "informe_dir": "investigacion/2026-09-28-combustibles-2026-fixture", "capitulos": [{"n": "01", "titulo": "Del crudo al tanque", "tuits": [2]}]}'
INV_CIERRE='T[2]["texto"]=T[2]["texto"].rstrip()+" Informe completo: [ENLACE AL INFORME]"'
negativo "modo investigacion sin bloque"              "G1 modo investigacion" "$(mut 'g["modo"]="investigacion"; '"$INV_CIERRE")"
negativo "modo investigacion: cierre sin el marcador" "G8 modo investigacion" "$(mut 'g["modo"]="investigacion"; '"$INV_BLOQUE")"
negativo "modo investigacion: marcador en T1"         "G8 modo investigacion" "$(mut 'g["modo"]="investigacion"; '"$INV_BLOQUE"'; '"$INV_CIERRE"'; T[0]["texto"]=T[0]["texto"]+" [ENLACE AL INFORME]"')"
negativo "modo investigacion con 3 tuits en normal"   "G1 modo investigacion" "$(mut 'g["modo"]="investigacion"; g["smoke"]=False; '"$INV_BLOQUE"'; '"$INV_CIERRE")" 'python3 -c "import json,sys; p=sys.argv[1]; e=json.load(open(p)); e[\"smoke\"]=False; e[\"fixture\"]=False; json.dump(e, open(p,\"w\"), ensure_ascii=False, indent=2)" "$S/encuadre.json"'
positivo_hilo_investigacion() {
  local S; S="$(mktemp -d "$TMP/pos.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"; rm -rf "$S/salida" "$S/informe"
  python3 -c "$(mut 'g["modo"]="investigacion"; '"$INV_BLOQUE"'; '"$INV_CIERRE")" "$S/guion.json" || return 1
  python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" --sin-contacto >"$TMP/inv.log" 2>&1 || { tail -5 "$TMP/inv.log"; return 1; }
  python3 -c 'import json,sys; h=json.load(open(sys.argv[1])); assert h["modo"]=="investigacion" and h["investigacion"]["numero"]=="01", h.get("modo")' "$S/salida/hilo.json" || { echo "hilo.json sin modo investigacion o sin su bloque"; return 1; }
  grep -q '^## Modo investigacion' "$S/salida/post.md" || { echo "post.md sin la sección del modo"; return 1; }
  grep -q "ENLACE AL INFORME" "$S/salida/post.md" || { echo "post.md sin el marcador"; return 1; }
  python3 scripts/memoria.py --registrar "$S" --ruta sesiones/_fixture/salida --informe sesiones/_fixture --dry-run 2>/dev/null | grep -q "modo investigacion"
}
paso "modo investigacion válido (smoke, bloque y marcador): ensambla, post.md lo lleva y memoria.py --informe dice modo investigacion" positivo_hilo_investigacion

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
paso "catalogo_informe.py → informe.json + datos.json sintético (26 tipos)" bash -c 'python3 scripts/catalogo_informe.py --dir "$0" --tarjeta ninguna | grep -q "26 tipos · sin G: ninguna"' "$TMP/catalogo"
paso "informe.py catálogo --check (los 26 G.* en papel y a media página: I1–I7 + P1–P5)" python3 scripts/informe.py "$TMP/catalogo" --salida "$TMP/catalogo/salida" --check
tarjetas_partidas() {  # dos páginas tarjetas: la segunda no pisa las imágenes de la primera
  local D; D="$(mktemp -d "$TMP/tarj.XXXXXX")"
  python3 - "$INF/informe.json" "$D" <<'PY' || return 1
import json, sys
R = json.load(open(sys.argv[1], encoding="utf-8")); P = R["paginas"]
i = next(k for k, p in enumerate(P) if p["tipo"] == "tarjetas")
segunda = dict(P[i], items=P[i]["items"][4:], titulo="Las tarjetas del hilo (sigue)")
for k in ("id", "indice", "tuit", "lead"):
    segunda.pop(k, None)
P[i] = dict(P[i], items=P[i]["items"][:4]); P[i].pop("tuit", None)
P.insert(i + 1, segunda)
json.dump(R, open(sys.argv[2] + "/informe.json", "w", encoding="utf-8"), ensure_ascii=False)
open(sys.argv[2] + "/esperada.txt", "w").write(segunda["items"][0]["desde"])
PY
  python3 scripts/informe.py "$D" --salida "$D/salida" --sin-pdf >/dev/null 2>&1 || return 1
  cmp -s "$D/salida/figuras/tarjeta_05.png" "$(cat "$D/esperada.txt")"
}
paso "tarjetas partidas en dos páginas: cada imagen en su lugar" tarjetas_partidas

INF_DENGUE="$INF"; INF="$TMP/catalogo"   # negativos sobre el catálogo: campos obligatorios de los tipos nuevos (CAMPOS_GRAFICO) e I2 por contrato
pag_cat() { echo 'pg=next(p for p in P if p.get("seccion")=="'"$1"'" and p["bloques"][0]["texto"].endswith("papel")); f=pg["bloques"][2]; g=f["grafico"]; '; }
neg_informe "catálogo: apilada sin partes"              "I1 página" "$(pag_cat apilada)g.pop(\"partes\")"
neg_informe "catálogo: embudo sin misma_cohorte"        "I1 página" "$(pag_cat embudo)g.pop(\"misma_cohorte\")"
neg_informe "catálogo: dispersion sin ejeX"             "I1 página" "$(pag_cat dispersion)g.pop(\"ejeX\")"
neg_informe "catálogo: cascada sin inicio ni fin"       "I1 página" "$(pag_cat cascada)g.pop(\"inicio\"); g.pop(\"fin\")"
neg_informe "catálogo: pesas sin cero y sin nota"       "I1 página" "$(pag_cat pesas)g[\"desdeCero\"]=False; f.pop(\"nota\",None)"
neg_informe "catálogo: cascada con un paso sin respaldo" "I2 página" "$(pag_cat cascada)g[\"pasos\"][0][\"valor\"]+=1"
neg_informe "catálogo: dona con una parte sin respaldo"  "I2 página" "$(pag_cat dona)g[\"partes\"][0][\"valor\"]+=1"
INF="$INF_DENGUE"
neg_texto_pequeno() {  # P1: el render rechaza texto por debajo de 12 px
  sed 's#</style>#.p { font-size: 10px !important; }</style>#' "$TMP/informe/informe.html" > "$TMP/informe/p1.html"
  node scripts/render_informe.js "$TMP/informe/p1.html" --check >"$TMP/p1.log" 2>&1 && return 1
  grep -q "P1 " "$TMP/p1.log"
}
paso "render_informe.js rechaza texto de 10 px (P1)" neg_texto_pequeno
INF_DENGUE="$INF"; INF=sesiones/_fixture   # negativos sobre el fixture del informe (cifras del fixture de hilo)
neg_informe "fixture: cifra no_confirmada (pre-c05) en el resumen"  I2 'P[1]["cifras"][0]["id"]="pre-c05"'
neg_informe "fixture: punto de la serie del Brent cambiado"          I2 'P[3]["bloques"][2]["grafico"]["series"][0]["valores"][3]=118'
neg_informe "fixture: figura sin fuente"                             I4 'P[3]["bloques"][2].pop("fuente")'
neg_informe "fixture: referencia {fign:} sin destino"                I5 'P[5]["hallazgos"][0]["ref"]="{fign:nada}"'
neg_informe "fixture: desde_hilo sin hilo.json"                      I1 'P[7]["desde_hilo"]="sesiones/no-existe"'
neg_informe "fixture: página que desborda"                           P2 'P[3]["bloques"][1]["parrafos"]*=14' render
INF="$INF_DENGUE"

echo "== revisión de justificación (digesto del revisor)"
revision_ok() { python3 scripts/revision.py "$1" | grep -q "^# revisión" && python3 scripts/revision.py "$1" --avisos >/dev/null; }
paso "revision.py da el digesto y los avisos R1–R3 del informe de ejemplo" revision_ok investigacion/ejemplos/dengue-2026
paso "revision.py da el digesto y los avisos R1–R3 del fixture" revision_ok sesiones/_fixture
revision_r3() {  # una figura derivada sin la operación en el pie salta R3
  python3 - "$TMP/rev_r3" <<'PY'
import json, os, sys
d = sys.argv[1]; os.makedirs(d, exist_ok=True)
R = {"meta": {}, "paginas": [{"tipo": "cuerpo", "seccion": "01 · Prueba", "bloques": [
    {"b": "texto", "parrafos": ["Texto que no nombra la barra."]},
    {"b": "figura", "id": "f1", "tipo": "papel", "derivado": True, "fuente": "Cálculo propio", "pie": "Sin operación.",
     "grafico": {"tipo": "barras_h", "items": [{"nombre": "Barra muda", "valor": 3}]}}]}]}
json.dump(R, open(os.path.join(d, "informe.json"), "w"))
PY
  python3 scripts/revision.py "$TMP/rev_r3" --avisos | grep -q "^R3" && python3 scripts/revision.py "$TMP/rev_r3" --avisos | grep -q "^R1"
}
paso "revision.py marca R1 (barra sin explicar) y R3 (derivada sin operación)" revision_r3
revision_r456() {  # mismo número con otro redondeo (R4), conteo de estados distinto (R5), sigla sin glosario (R6)
  python3 - "$TMP/rev_r4" <<'PY'
import json, os, sys
d = sys.argv[1]; os.makedirs(d, exist_ok=True)
R = {"meta": {}, "paginas": [{"tipo": "cuerpo", "seccion": "01 · Prueba", "bloques": [
    {"b": "texto", "parrafos": ["Covial programó 6,347.84 km; hay 3 retrocesos según el MSPAS."]},
    {"b": "figura", "id": "km", "tipo": "papel", "fuente": "Covial", "pie": "Kilómetros.",
     "grafico": {"tipo": "barras_h", "items": [{"nombre": "Covial programó", "valor": 6348}]}},
    {"b": "figura", "id": "estados", "tipo": "papel", "fuente": "Cálculo propio ÷", "pie": "Estados.",
     "grafico": {"tipo": "barras_h", "items": [{"nombre": "Cumplido", "valor": 2}, {"nombre": "En proceso", "valor": 3},
                                               {"nombre": "Retroceso", "valor": 1}, {"nombre": "Sin iniciar", "valor": 4}]}}]}]}
json.dump(R, open(os.path.join(d, "informe.json"), "w"))
PY
  local A; A="$(python3 scripts/revision.py "$TMP/rev_r4" --avisos)"
  grep -q "^R4" <<<"$A" && grep -q "^R5" <<<"$A" && grep -q "^R6 .*MSPAS" <<<"$A" || { echo "$A"; return 1; }
}
paso "revision.py marca R4 (otro redondeo), R5 (conteo de estados) y R6 (sigla sin glosario)" revision_r456

echo "== verificación mecánica (verificacion.py V-A–V-E, G9, G10)"
paso "verificacion.py: el fixture de hilo pasa sin fallas" python3 scripts/verificacion.py sesiones/_fixture
paso "verificacion.py: el fixture de dato pasa sin fallas" python3 scripts/verificacion.py sesiones/_fixture_dato
ver_neg() {  # ver_neg REGLA "mutación python sobre (h, v) = (hallazgos, verificación) del fixture"
  local S; S="$(mktemp -d "$TMP/ver.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"; rm -rf "$S/salida"
  python3 - "$S" "$2" <<'PY' || return 1
import json, sys
s, code = sys.argv[1], sys.argv[2]
hp, vp = s + "/hallazgos_precios.json", s + "/verificacion_precios.json"
h, v = json.load(open(hp)), json.load(open(vp))
C = {c["id"]: c for c in h["cifras"]}; V = {i["id"]: i for i in v["items"]}
exec(code)
json.dump(h, open(hp, "w"), ensure_ascii=False); json.dump(v, open(vp, "w"), ensure_ascii=False)
PY
  python3 scripts/verificacion.py "$S" >"$TMP/ver.out" 2>&1; local rc=$?
  [[ $rc -eq 1 ]] && grep -q "FALLA $1" "$TMP/ver.out" || { cat "$TMP/ver.out"; return 1; }
  [[ -z "${3:-}" ]] || { python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" >/dev/null 2>"$TMP/ver.err"; grep -q "$3" "$TMP/ver.err" || { cat "$TMP/ver.err"; return 1; }; }
}
paso "V-A: la cita dice 46.0 y el valor es 46.1 → falla (y G9 en ensamblar)" ver_neg V-A 'C["pre-c03"]["evidencia"]["cita"] = "Diésel, septiembre 2026: Q46.0 por galón"' "G9 T2 cifra pre-c03"
paso "V-A: un derivado con calculo que no da el valor → falla" ver_neg V-A 'C["pre-c03"]["evidencia"]["cita"] = "sin el número"; C["pre-c03"]["calculo"] = "26/0.5"'
paso "V-B: ajustada que deja el valor viejo en partes[] → falla" ver_neg V-B 'V["pre-c04"]["valor_final"] = 6.1; C["pre-c04"]["evidencia"]["cita"] += " 6.1"'
paso "V-C: independencia alta con url_2 del mismo dominio → falla" ver_neg V-C 'V["pre-c02"]["independencia"] = "alta"; V["pre-c02"]["url_2"] = "https://www.mem.gob.gt/otra"'
paso "V-C: independencia ausente → falla" ver_neg V-C 'V["pre-c02"].pop("independencia")'
ver_calculo() {  # un derivado bien declarado pasa: calculo evaluado
  local S; S="$(mktemp -d "$TMP/ver.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"
  python3 - "$S" <<'PY'
import json, sys
p = sys.argv[1] + "/hallazgos_precios.json"; h = json.load(open(p))
for c in h["cifras"]:
    if c["id"] == "pre-c03":
        c["evidencia"]["cita"] = "el diésel subió de Q26 a Q46.10"; c["calculo"] = "26 + 20.1"
json.dump(h, open(p, "w"), ensure_ascii=False)
PY
  python3 scripts/verificacion.py "$S"
}
paso "V-A: un derivado con calculo correcto pasa" ver_calculo
paso "verificacion.py lee números de prensa (mil 734, 16 mil 537 millones, Q18.615,5 millones)" python3 -c '
import sys; sys.path.insert(0, "scripts"); import verificacion as V
casos = [("mil 734 kilómetros", 1734), ("Q16 mil 537 millones 678 mil", 16537.678), ("Q18.615,5 millones", 18615.5), ("un millón 625 mil 849", 1625849), ("cinco personas", 5)]
assert all(V.coincide(v, V.numeros(t)) for t, v in casos), [t for t, v in casos if not V.coincide(v, V.numeros(t))]
assert not V.coincide(17.3, V.numeros("17.4%")) and V.sueltos("15.4 mil casos", [15454]) == ["15.4 mil"]'
g10() {  # un número del texto que no es ninguna cifra → aviso G10
  local S; S="$(mktemp -d "$TMP/g10.XXXXXX")"; cp -R sesiones/_fixture/. "$S/"; rm -rf "$S/salida"
  python3 -c "$(mut 'T[1]["texto"]="El diésel llegó a Q47.3 el galón."')" "$S/guion.json"
  python3 scripts/ensamblar.py "$S" --check --salida "$S/salida" 2>&1 | grep -q "G10 T2.*47.3"
}
paso "G10: número del texto sin respaldo en las cifras → aviso" g10

echo "== auditoría (fixture: retroceso por poco, igual = sin iniciar, no atribuible, sin dato)"
AUDF=sesiones/_fixture_auditoria
aud_pos() {
  local S; S="$(mktemp -d "$TMP/aud.XXXXXX")"; cp -R "$AUDF/." "$S/"
  for e in aaa bbb; do python3 scripts/auditoria.py "$S" --validar $e --verificacion >/dev/null || return 1; done
  python3 scripts/auditoria.py "$S" --calcular >"$TMP/aud.json" || return 1
  python3 - "$TMP/aud.json" "$S/auditoria.json" <<'PY' || return 1
import json, sys
r = json.load(open(sys.argv[1])); a = json.load(open(sys.argv[2]))
est = {c["id"]: c["estado"] for c in a["compromisos"]}
assert r["global"] == 30.0, r["global"]
esperado = {"S1-01": "en_proceso", "S1-02": "cumplido", "S1-03": "cumplido", "S1-04": "no_atribuible",
            "S2-01": "retroceso", "S2-02": "no_iniciado", "S2-03": "no_atribuible", "S2-04": "no_verificable"}
assert est == esperado, {k: (est.get(k), v) for k, v in esperado.items() if est.get(k) != v}
PY
  python3 scripts/auditoria.py "$S" --insertar "$S/informe.json" >/dev/null || return 1
  python3 scripts/auditoria.py "$S" --justificar "$S/informe.json" >/dev/null || return 1
  python3 scripts/auditoria.py "$S" --resumen | grep -q "16.65" || { echo "--resumen no da 16.65 con sus dos decimales"; return 1; }
}
paso "auditoria.py: validar → calcular (global 30.0, 8 estados) → insertar → justificar J1–J5" aud_pos
aud_neg() {  # aud_neg "texto esperado en la falla" eje "mutación python sobre ev (evaluación) y vr (verificación)"
  local S; S="$(mktemp -d "$TMP/aud.XXXXXX")"; cp -R "$AUDF/." "$S/"
  python3 - "$S" "$2" "$3" <<'PY' || return 1
import json, sys
s, eje, code = sys.argv[1], sys.argv[2], sys.argv[3]
ep, vp = "%s/evaluacion_%s.json" % (s, eje), "%s/verificacion_%s.json" % (s, eje)
ev, vr = json.load(open(ep)), json.load(open(vp))
E = {i["id"]: i for i in ev["items"]}; R = {i["id"]: i for i in vr["compromisos"]}
exec(code)
json.dump(ev, open(ep, "w"), ensure_ascii=False); json.dump(vr, open(vp, "w"), ensure_ascii=False)
PY
  python3 scripts/auditoria.py "$S" --validar "$2" --verificacion >"$TMP/audn.out" 2>&1; local rc=$?
  [[ $rc -eq 1 ]] && grep -q "$1" "$TMP/audn.out" || { cat "$TMP/audn.out"; return 1; }
}
paso "auditoría: observado que no es el valor de su cifra → falla" aud_neg "observado 401 no es un valor" aaa 'E["S1-01"]["observado"] = 401'
paso "auditoría: no_atribuible con existe_desde del mandato → falla" aud_neg "existe_desde anterior al mandato" aaa 'R["S1-04"]["existe_desde"] = "2025"'
paso "auditoría: no_atribuible sin existe_desde → falla" aud_neg "existe_desde anterior al mandato" aaa 'R["S1-04"].pop("existe_desde")'
paso "auditoría: hito con hecho anterior al mandato → sugiere no_atribuible" aud_neg "estado no_atribuible con existe_desde" aaa 'E["S1-03"]["fecha_dato"] = "2023-05"'

echo "== video (/video)"
paso "numeros_es.py --prueba (cifras → palabras, ida y vuelta)" python3 scripts/numeros_es.py --prueba
VT="$TMP/video"
paso "video.py preparar sobre el fixture (duración prueba)" bash -c "python3 scripts/video.py preparar sesiones/_fixture/salida --duracion prueba --trabajo '$VT' --permitir-borrador >/dev/null && cp sesiones/_fixture_video/guion.json '$VT/'"
paso "video.py guion --check (V1–V5, V9) sobre el guion v2 del fixture" python3 scripts/video.py guion "$VT" --check
paso "locucion.json v2 (tipos, cinetico, valor_calculo, hueco_max_s ≤ 6)" python3 -c '
import json, sys
L = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"]
assert [e["tipo"] for e in L] == ["gancho", "tarjeta", "tarjeta", "golpe", "tarjeta", "cierre"], [e["tipo"] for e in L]
assert L[3]["cinetico"]["pantalla"] == "1.8 veces" and 1.7 < L[3]["valor_calculo"] < 1.8 and L[1]["valor_calculo"] > 50
assert all(e["hueco_max_s"] <= 6 for e in L[:-1]), [e["hueco_max_s"] for e in L]
assert L[0]["voz"].startswith("En Guatemala:") and "Guatemala" not in L[0]["cinetico"]["pantalla"]
' "$VT/locucion.json"
paso "sfx.py --check (K2: los 8 efectos fijos)" python3 scripts/sfx.py --check
paso "video.py preparar rechaza un hilo en borrador sin --permitir-borrador (exit 1)" bash -c "! python3 scripts/video.py preparar sesiones/_fixture/salida --duracion prueba --trabajo '$TMP/video_borrador' >/dev/null 2>&1"
# video_neg "<texto esperado en FALLA>" '<python que muta G (guion.json)>': el gate debe fallar con ese motivo
video_neg() {
  local esperado="$1" mut="$2" d="$TMP/video_neg"
  rm -rf "$d"; cp -R "$VT" "$d"
  python3 - "$d/guion.json" "$mut" <<'PY' || return 1
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8"))
exec(sys.argv[2])
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
  local out; out="$(python3 scripts/video.py guion "$d" --check 2>&1)" && return 1
  grep -q "$esperado" <<<"$out"
}
# índices del guion v2 del fixture: [0] gancho · [1] T1 · [2] T2 · [3] golpe · [4] T3
paso "video gate: número sin respaldo → V2" video_neg "V2 escena 3" 'G["escenas"][2]["texto"] = G["escenas"][2]["texto"].replace("46.1", "47.3")'
paso "video gate: cifra de género ambiguo sin marca → V3" video_neg "V3 escena 5" 'G["escenas"][4]["texto"] += " Fueron 200 en total."'
paso "video gate: cierre sin pregunta → V5" video_neg "V5 el cierre debe terminar en pregunta" 'G["cierre"]["texto"] = "El barril subió y la bomba lo sintió."'
paso "video gate: cierre que menciona fuentes → V5" video_neg "V5 el cierre no menciona" 'G["cierre"]["texto"] = "Las fuentes están en el hilo. " + G["cierre"]["texto"]'
paso "video gate: tarjeta repetida → V1" video_neg "V1 escena 5: T2 repetida" 'G["escenas"][4]["tuit"] = 2'
paso "video gate: demasiado largo → V4" video_neg "V4 duración estimada" 'G["escenas"][4]["texto"] += " Guatemala sale bajo en el promedio del año porque incluye los meses de subsidio, cuando el Congreso aprobó un techo al precio."'
paso "video gate: «gancho» de la v1 → migración" video_neg "V1 «gancho» ya no existe" 'G["gancho"] = "¿Cuánto pesa el crudo?"'
paso "video gate: escena 1 que no es gancho → V9" video_neg "V9 la escena 1 debe ser tipo gancho" 'G["escenas"][0]["tipo"] = "golpe"'
paso "video gate: fórmula desconocida → V9" video_neg "V9 gancho: formula «susto»" 'G["escenas"][0]["formula"] = "susto"'
paso "video gate: pantalla del gancho demasiado larga → V9" video_neg "V9 gancho: pantalla" 'G["escenas"][0]["pantalla"] = "El barril de petróleo subió mucho este año"'
paso "video gate: gancho cifra sin cifra en pantalla → V9" video_neg "V9 gancho (cifra): la pantalla debe llevar la cifra" 'G["escenas"][0]["pantalla"] = "El barril"'
paso "video gate: voz del gancho demasiado larga → V4" video_neg "V4 escena 1 (gancho)" 'G["escenas"][0]["texto"] += " Y el transporte público subió en todo el país, departamento por departamento, sin excepción alguna."'
paso "video gate: escena 2 que no es T1 → V9" video_neg "V9 la escena 2 debe ser la tarjeta T1" 'G["escenas"][1], G["escenas"][2] = G["escenas"][2], G["escenas"][1]'
paso "video gate: enlace ausente → V9" video_neg "V9 escena 3: falta enlace" 'del G["escenas"][2]["enlace"]'
paso "video gate: enlace desconocido → V9" video_neg "V9 escena 4: enlace «luego»" 'G["escenas"][3]["enlace"] = "luego"'
paso "video gate: voz sin conector → V9" video_neg "V9 escena 3: la voz no empieza con un conector" 'G["escenas"][2]["texto"] = G["escenas"][2]["texto"].replace("Por eso en", "En")'
paso "video gate: exceso de enlaces «y» → V9" video_neg "enlaces «y»" 'exec("for e in G[\"escenas\"][2:]:\n e[\"enlace\"] = \"y\"; e[\"texto\"] = \"Y \" + e[\"texto\"][0].lower() + e[\"texto\"][1:]")'
paso "video gate: golpe demasiado largo → V9" video_neg "V9 escena 3: golpe «" 'G["escenas"][2]["golpe"] = "El galón de diésel pasó de veintiséis a cuarenta y seis"'
paso "video gate: golpe que repite el titular → V9" video_neg "V9 escena 2: golpe repite el titular de T1" 'G["escenas"][1]["golpe"] = "cerró septiembre en US$102"'
paso "video gate: dos golpes seguidos → V9" video_neg "dos golpes seguidos" 'G["escenas"].insert(4, dict(G["escenas"][3]))'
paso "video gate: golpes fuera de rango → V1" video_neg "V1 2 golpes; «prueba» pide 0–1" 'G["escenas"].append({"tipo": "golpe", "enlace": "y", "pantalla": "102 dólares", "linea": "el barril", "texto": "Y el barril sigue en 102 dólares."})'
paso "video gate: promesa que no es literal → V9" video_neg "V9 promesa.texto no aparece literal" 'G["promesa"]["texto"] = "Y esto no termina aquí."'
paso "video gate: pago fuera del último tercio → V9" video_neg "V9 promesa.pago = 2" 'G["promesa"]["pago"] = 2'
paso "video gate: calculo que no da la pantalla → V9" video_neg "V9 escena 4: calculo pre-c03/pre-c02\*2 da" 'G["escenas"][3]["calculo"] = "pre-c03/pre-c02*2"'
paso "video gate: pantalla sin respaldo ni calculo → V9" video_neg "sin respaldo en datos.json ni «calculo»" 'G["escenas"][3]["pantalla"] = "2.5 veces"; del G["escenas"][3]["calculo"]'
paso "video gate: literal del calculo sin respaldo → V9" video_neg "usa el literal 181" 'G["escenas"][3]["calculo"] = "pre-c03/181"'
paso "video gate: cifra inexistente en el calculo → V9" video_neg "usa la cifra pre-c09" 'G["escenas"][3]["calculo"] = "pre-c09/pre-c02"'
paso "video gate: hueco de más de 6 s sin cifra → V9 ritmo" video_neg "sin evento entre" 'G["escenas"][1]["texto"] += " Y eso sin contar lo que subieron el transporte, la comida y todo lo que se mueve en camión por el país entero."'
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make video-fixture (RAPIDO=1)"; else
  paso "make video-fixture (voz falsa, V6–V8, V10, 10 fps)" make video-fixture
  paso "fixture de video: 1080×1920 con audio y guion de entrega" bash -c 'ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_video/salida/video.mp4 | grep -q "video,1080,1920" && test -s sesiones/_fixture_video/salida/guion.json && test -s sesiones/_fixture_video/salida/subtitulos.srt'
  paso "escenas.json v2 (tipos, eventos, efectos del catálogo, hueco real ≤ 6 s)" python3 -c '
import json
E = json.load(open("sesiones/_fixture_video/trabajo/escenas.json", encoding="utf-8"))
cat = {x["id"] for x in json.load(open("design/sfx/catalogo.json", encoding="utf-8"))["efectos"]}
assert E["version"] == 2 and E["escenas"][0]["tipo"] == "gancho" and E["gancho"]["pantalla"] == "102 dólares"
assert all(e.get("eventos") for e in E["escenas"]) and all(s["id"] in cat for e in E["escenas"] for s in e["sfx"])
ts, off = [], 0.0
for e in E["escenas"]:
    ts += [off + x["t"] for x in e["eventos"]]; off += e["dur"]
ts.sort(); hueco = max(b - a for a, b in zip(ts, ts[1:]))
assert hueco <= 6, "hueco real %.1f s" % hueco
assert sum(len(e["sfx"]) for e in E["escenas"]) >= 6 and any(s["id"] == "riser" for e in E["escenas"] for s in e["sfx"])
'
  paso "ducking: la música baja ≥ 6 dB bajo la voz" bash -c '
rms() { ffmpeg -hide_banner -i "$1" -af "atrim=$2:$3,astats=measure_overall=RMS_level:measure_perchannel=none" -f null - 2>&1 | grep "RMS level dB" | tail -1 | grep -o "[-0-9.]*$"; }
A=$(python3 -c "import json; E=json.load(open(\"sesiones/_fixture_video/trabajo/escenas.json\")); e=E[\"escenas\"][1]; print(\"%.2f %.2f\" % (E[\"escenas\"][0][\"dur\"] + e[\"palabras\"][1][\"start\"], E[\"escenas\"][0][\"dur\"] + e[\"palabras\"][6][\"end\"]))")
set -- $A
D=$(rms sesiones/_fixture_video/trabajo/segs/musica_duck.wav $1 $2); M=$(rms sesiones/_fixture_video/trabajo/segs/musica.wav $1 $2)
python3 -c "import math,sys; d=float(sys.argv[1]); m=float(sys.argv[2]) + 20*math.log10(0.22); print(\"ducking %.1f dB (duck %.1f · musica %.1f)\" % (m-d, d, m)); sys.exit(0 if m - d >= 6 else 1)" "$D" "$M"'
fi

echo "== sintaxis de los workflows"
check_js() {
  { echo "(async function(){"; sed 's/^export //' ".claude/workflows/$1"; echo "})"; } > "$TMP/check_$1"
  node --check "$TMP/check_$1"
}
paso "node --check hilo.js (envuelto en async function)" check_js hilo.js
paso "node --check ideas.js (envuelto en async function)" check_js ideas.js
paso "node --check dato.js (envuelto en async function)" check_js dato.js
paso "node --check investigacion.js (envuelto en async function)" check_js investigacion.js
paso "node --check video.js (envuelto en async function)" check_js video.js
paso "check_workflows.py (PALETAS, PLANTILLAS, HOOKS, BEATS, REQ, pesoX, MODOS, gráficos del informe W7–W8, bloque común W9 y espejos de video.js W10)" python3 scripts/check_workflows.py

echo
echo "[test] $N pruebas · $FALLOS fallos"
[[ $FALLOS -eq 0 ]] || exit 1
exit 0
