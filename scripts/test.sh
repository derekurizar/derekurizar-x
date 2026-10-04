#!/usr/bin/env bash
# Hilos · pruebas del framework (sin agentes).
#
# Uso: bash scripts/test.sh          # completa (incluye make catalogo)
#      RAPIDO=1 bash scripts/test.sh # salta el catálogo
# Pasos: validate · catálogo · contar_x (py + js) · fixture (materializar + ensamblar --check)
#        · negativos del gate G1–G6 sobre copias del fixture · negativos de render.js
#        · banco de ideas (ideas.py sobre un banco temporal) · node --check de hilo.js e ideas.js. Resumen «N pruebas · M fallos»; exit 1 si hay fallos.
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
[[ "${1:-}" == "RAPIDO=1" ]] && RAPIDO=1
RAPIDO="${RAPIDO:-0}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
N=0; FALLOS=0

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
  cp -R sesiones/_fixture/. "$S/"; rm -rf "$S/salida"
  if [[ -n "$mut" ]] && ! python3 -c "$mut" "$S/guion.json" 2>"$TMP/mut.log"; then
    FALLOS=$((FALLOS+1)); printf 'FALLO  %s: la mutación falló\n' "$nombre"; sed 's/^/       /' "$TMP/mut.log"; return
  fi
  [[ -n "$extra" ]] && eval "$extra"
  python3 scripts/ensamblar.py "$S" --check >"$TMP/neg.out" 2>"$TMP/neg.err"; local rc=$?
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
}
paso "salida del fixture (hilo.html, post.md, datos.json, hilo.json, 3 PNG)" comprobar_salida

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

echo "== sintaxis de los workflows"
check_js() {
  { echo "(async function(){"; sed 's/^export //' ".claude/workflows/$1"; echo "})"; } > "$TMP/check_$1"
  node --check "$TMP/check_$1"
}
paso "node --check hilo.js (envuelto en async function)" check_js hilo.js
paso "node --check ideas.js (envuelto en async function)" check_js ideas.js

echo
echo "[test] $N pruebas · $FALLOS fallos"
[[ $FALLOS -eq 0 ]] || exit 1
exit 0
