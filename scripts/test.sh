#!/usr/bin/env bash
# Hilos · pruebas del framework (sin agentes).
#
# Uso: bash scripts/test.sh          # completa (incluye make catalogo)
#      RAPIDO=1 bash scripts/test.sh # salta el catálogo
# Pasos: validate · catálogo · contar_x (py + js) · fixture (materializar + ensamblar --check)
#        · negativos del gate G1–G6 sobre copias del fixture · negativos de render.js
#        · node --check de hilo.js. Resumen «N pruebas · M fallos»; exit 1 si hay fallos.
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

echo "== sintaxis del workflow"
check_hilo_js() {
  { echo "(async function(){"; sed 's/^export //' .claude/workflows/hilo.js; echo "})"; } > "$TMP/hilo_check.js"
  node --check "$TMP/hilo_check.js"
}
paso "node --check hilo.js (envuelto en async function)" check_hilo_js

echo
echo "[test] $N pruebas · $FALLOS fallos"
[[ $FALLOS -eq 0 ]] || exit 1
exit 0
