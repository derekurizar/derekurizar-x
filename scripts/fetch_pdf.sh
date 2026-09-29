#!/usr/bin/env bash
# Hilos - Descarga un PDF oficial y extrae su texto con layout preservado.
# WebFetch no lee tablas de PDFs y falla con archivos >10MB; este helper si.
#
# Uso:
#   scripts/fetch_pdf.sh <URL> [salida.pdf]
#   REFRESCAR=1 scripts/fetch_pdf.sh <URL>     # ignora la caché
#   (o `make pdf URL=... [OUT=...]`)
#
# Deja el PDF y un .txt (pdftotext -layout, que conserva las columnas de las
# tablas) en sesiones/_descargas/ por defecto. Consulta y alimenta la caché
# sesiones/_descargas/indice.json via scripts/indice_descargas.py.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INDICE="python3 $RAIZ/scripts/indice_descargas.py"
URL="${1:?Uso: scripts/fetch_pdf.sh <URL> [salida.pdf]}"
OUT="${2:-$RAIZ/sesiones/_descargas/$(basename "${URL%%\?*}")}"
case "$OUT" in *.pdf) ;; *) OUT="$OUT.pdf" ;; esac
TXT="${OUT%.pdf}.txt"

command -v pdftotext >/dev/null || {
  echo "ERROR: falta pdftotext (instala poppler: brew install poppler)" >&2
  exit 1
}

rel() { python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1]))' "$1"; }

# Caché: si la URL ya está registrada y el archivo existe, se reutiliza.
if [[ "${REFRESCAR:-0}" != "1" ]]; then
  if CACHE="$($INDICE buscar "$URL" 2>/dev/null | head -1)" && [[ -n "$CACHE" ]]; then
    case "$CACHE" in /*) ;; *) CACHE="$RAIZ/$CACHE" ;; esac
    echo "(caché) → $(rel "$CACHE")"
    CTXT="${CACHE%.pdf}.txt"
    [[ -s "$CTXT" ]] || pdftotext -layout "$CACHE" "$CTXT"
    echo "OK -> $(rel "$CTXT") ($(wc -l < "$CTXT" | tr -d ' ') lineas)"
    exit 0
  fi
fi

mkdir -p "$(dirname "$OUT")"
curl -fsSL --retry 2 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" "$URL" -o "$OUT"
pdftotext -layout "$OUT" "$TXT"
$INDICE registrar "$URL" "$OUT" "$TXT" --tipo pdf >/dev/null
echo "OK -> $(rel "$OUT")"
echo "OK -> $(rel "$TXT") ($(wc -l < "$TXT" | tr -d ' ') lineas)"
