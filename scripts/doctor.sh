#!/usr/bin/env bash
# Hilos · doctor: comprueba el entorno y reporta OK / AVISO / ERROR.
#
# Uso: bash scripts/doctor.sh
# Salida: 0 si no hay ERROR (los AVISO no fallan) · 1 con algún ERROR
set -u
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
ERRORES=0; AVISOS=0
ok()    { printf 'OK     %s\n' "$*"; }
aviso() { printf 'AVISO  %s\n' "$*"; AVISOS=$((AVISOS+1)); }
error() { printf 'ERROR  %s\n' "$*"; ERRORES=$((ERRORES+1)); }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# node ≥ 20
if command -v node >/dev/null; then
  NV="$(node --version | sed 's/^v//')"; NMAJ="${NV%%.*}"
  if [[ "$NMAJ" -ge 20 ]]; then ok "node $NV (≥ 20)"; else error "node $NV: se necesita ≥ 20"; fi
else
  error "node no está instalado"
fi

# playwright
if node -e "require('playwright')" >/dev/null 2>&1; then
  PV="$(node -e "console.log(require('playwright/package.json').version)" 2>/dev/null || echo '?')"
  ok "playwright $PV disponible (node -e \"require('playwright')\")"
else
  error "playwright no se puede cargar: corre npm install (y npx playwright install chromium)"
fi

# python3 ≥ 3.9
if command -v python3 >/dev/null; then
  PYV="$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then ok "python3 $PYV (≥ 3.9)"; else error "python3 $PYV: se necesita ≥ 3.9"; fi
else
  error "python3 no está instalado"
fi

# tipografías
FALTAN=""
for f in archivo-var.woff2 instrument-serif-400.woff2 instrument-serif-400i.woff2 jetbrains-mono-var.woff2; do
  [[ -s "design/fonts/$f" ]] || FALTAN="$FALTAN $f"
done
if [[ -z "$FALTAN" ]]; then ok "design/fonts/: los 4 woff2 presentes"; else error "design/fonts/: faltan$FALTAN"; fi

# render de prueba (plantilla cifra + checks R1–R6)
if [[ $ERRORES -eq 0 ]]; then
  if python3 scripts/nuevo_visual.py cifra "$TMP/t.html" >"$TMP/render.log" 2>&1 && node scripts/render.js "$TMP/t.html" --check >>"$TMP/render.log" 2>&1; then
    ok "render de prueba (cifra → PNG + checks R1–R6)"
  else
    error "render de prueba falló:"; sed 's/^/       /' "$TMP/render.log" | tail -8
  fi
else
  aviso "render de prueba omitido (hay errores previos)"
fi

# pdftotext
if command -v pdftotext >/dev/null; then ok "pdftotext ($(pdftotext -v 2>&1 | head -1))"; else aviso "falta pdftotext (brew install poppler): make pdf no funcionará"; fi

# agentes y workflow
NAG="$(ls .claude/agents/hilo-*.md 2>/dev/null | wc -l | tr -d ' ')"
if [[ "$NAG" -eq 6 ]]; then ok ".claude/agents/: 6 archivos hilo-*.md"; else error ".claude/agents/: hay $NAG hilo-*.md (deben ser 6: editor, investigador, verificador, guionista, visualista, productor)"; fi
if [[ -s .claude/workflows/hilo.js ]]; then ok ".claude/workflows/hilo.js presente"; else error "falta .claude/workflows/hilo.js"; fi
if [[ -f .claude/commands/hilo.md ]]; then ok ".claude/commands/hilo.md presente"; else aviso "falta .claude/commands/hilo.md (/hilo no estará disponible)"; fi

# memoria y tokens
for f in memoria/fuentes.json memoria/hilos.json design/tokens.json; do
  if python3 -c "import json,sys; json.load(open('$f', encoding='utf-8'))" 2>/dev/null; then ok "$f es JSON válido"; else error "$f falta o no es JSON válido"; fi
done

# residuos
if [[ -d .playwright-mcp ]]; then aviso ".playwright-mcp/ presente (capturas del MCP de Playwright): bórralo, no forma parte del repo"; fi
NAJ="$(ls sesiones/*/visuales/*.ajuste.json 2>/dev/null | wc -l | tr -d ' ')"
[[ "$NAJ" -gt 0 ]] && aviso "$NAJ ajuste(s) sin consolidar en sesiones/*/visuales/ (materializar.py --consolidar)"

echo
echo "Recuerda: si acabas de crear o editar agentes en .claude/agents/, reinicia Claude Code para que los registre."
echo "[doctor] $ERRORES error(es) · $AVISOS aviso(s)"
[[ $ERRORES -eq 0 ]] || exit 1
exit 0
