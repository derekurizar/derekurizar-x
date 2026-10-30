#!/usr/bin/env bash
# Hilos · pruebas del framework (sin agentes).
#
# Uso: bash scripts/test.sh          # completa (incluye make catalogo)
#      RAPIDO=1 bash scripts/test.sh # salta el catálogo
# Pasos: validate (y M3 Noche sobre una copia de tokens.json) · fuentes (Archivo de ancho variable) · catálogo
#        · contar_x (py + js) · fixture (materializar + ensamblar --check)
#        · estilo: Noche en tarjetas y video, clásico en /investigacion (materializar, nuevo_visual, copiar_tarjeta del informe)
#        · fixture del informe (sesiones/_fixture/informe.json sobre la salida del fixture: I1–I7 + P1–P5,
#          digesto --para redactor, memoria.py --informe en dry-run, --informes)
#        · fixture dato (una tarjeta, modo dato de ensamblar) · negativos del gate G1–G8 sobre copias
#          (incluidos los del modo investigacion: bloque, marcador [ENLACE AL INFORME], rango de tuits)
#        de los fixtures (siempre con --salida: una copia nunca escribe en hilos/ ni datos/)
#        · negativos de render.js · banco de ideas (ideas.py sobre un banco temporal)
#        · informe de investigación (ejemplo → PDF en un temporal, negativos I1–I6, P1, P2; catálogo de
#          gráficos del informe: todos los G.* en papel, panel y media página con --check)
#        · /video: numeros_es, gate V1–V5+V9 con sus negativos, K2 (efectos fijos), make video-fixture (V6–V8, V10,
#          ducking medido) · node --check de hilo.js, ideas.js, dato.js, investigacion.js, video.js, noticias.js, historia.js y explica.js · check_workflows.py (W1–W13)
#        · /noticias: gates N1–N8 sobre la maqueta (negativos) y make noticias-fixture.
#        · /historia: gates H1–H14 sobre la maqueta (negativos: también foto repetida, retrato, chip, cita en otro idioma,
#          20 escenas), fotos fundidas y encaje, licencias de Commons, clases de fuente y agencias, M10, make
#          historia-fixture, entregar y memoria.py --historia.
#        · /explica: gates E1–E12 sobre la maqueta del interés compuesto (la calculadora, el chip «Ejemplo» y negativos de
#          E4, E5, E6, E7, E9, E10 y E11) y make explica-fixture.
#        · /sabias: gate S1–S3 sobre el dato de prueba (negativos), M13 y make sabias-fixture.
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
noche_m3() {  # M3 Noche sobre una copia de tokens.json: intacta pasa; un acento o una serie que no contrasta con el fondo, falla
  local R="$TMP/m3"; rm -rf "$R"; mkdir -p "$R/design"
  python3 - "$R" <<'PY'
import json, sys; sys.path.insert(0, "scripts"); import validate as V
R = sys.argv[1]; V.RAIZ = R
tk = json.load(open("design/tokens.json", encoding="utf-8"))
guardar = lambda: json.dump(tk, open(R + "/design/tokens.json", "w", encoding="utf-8"), ensure_ascii=False)
guardar(); V.validar_tokens(); assert not [e for e in V.ERRORES if "noche" in e], V.ERRORES
k = sorted(tk["noche"]["paletas"])[0]; q = tk["noche"]["paletas"][k]
q["acento"] = "#3A3A3A"; q["serie"][3] = "#2A2A2A"   # gris sobre un fondo casi negro: < 4.5:1 y < 3:1
guardar(); del V.ERRORES[:]; V.validar_tokens(); e = " | ".join(V.ERRORES)
for f in ("fondo", "fondo_acto2"):
    assert "tokens: noche %s acento/%s" % (k, f) in e and "tokens: noche %s serie[3]/%s" % (k, f) in e, e
del tk["noche"]["paletas"][k]; guardar(); del V.ERRORES[:]; V.validar_tokens()
assert "tokens: paleta %s sin bloque noche" % k in V.ERRORES, V.ERRORES
PY
}
paso "validate.py M3 Noche: acento y serie que no contrastan con el fondo (y el acto 2) fallan; una paleta sin bloque noche, también" noche_m3
paso "fuentes: los 5 woff2 de design/fonts (archivo-wdth.woff2 con el eje de ancho) y su @font-face con font-stretch 62% 125% en la tarjeta y el video" bash -c '
set -e; for f in archivo-var archivo-wdth instrument-serif-400 instrument-serif-400i jetbrains-mono-var; do test -s "design/fonts/$f.woff2" || { echo "falta design/fonts/$f.woff2"; exit 1; }; done
for f in templates/base.html video/comun.css; do grep -q "font-family: .Archivo.;.*font-stretch: 62% 125%; src: url(fonts/archivo-wdth.woff2)" "$f" || { echo "$f sin la Archivo de ancho variable"; exit 1; }; done'
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
estilo_investigacion() {  # Noche para todo salvo /investigacion: sus tarjetas son figuras del informe y se quedan clásicas
  local S="$TMP/estilo" f; rm -rf "$S"; mkdir -p "$S/sesion"; cp -R sesiones/_fixture/. "$S/sesion/"; rm -rf "$S/sesion/salida" "$S/sesion/informe" "$S/sesion"/visuales/tuit_*.html
  python3 scripts/materializar.py "$S/sesion" --sin-render >"$S/m1.log" 2>&1 || { tail -3 "$S/m1.log"; return 1; }
  for f in "$S/sesion"/visuales/tuit_*.html; do grep -q '<body[^>]*data-estilo="noche"' "$f" || { echo "modo hilo: $f no quedó Noche"; return 1; }; done
  python3 -c "$(mut 'g["modo"]="investigacion"')" "$S/sesion/guion.json" || return 1
  python3 scripts/materializar.py "$S/sesion" --sin-render >"$S/m2.log" 2>&1 || { tail -3 "$S/m2.log"; return 1; }
  for f in "$S/sesion"/visuales/tuit_*.html; do grep -q '<body[^>]*data-estilo="clasico"' "$f" || { echo "modo investigacion: $f no quedó clásico"; return 1; }; done
  [[ "$(ls "$S/sesion"/visuales/tuit_*.html | wc -l | tr -d ' ')" -eq 3 ]] || { echo "se esperaban 3 tuit_N.html"; return 1; }
  python3 scripts/nuevo_visual.py cifra "$S/c.html" --paleta cielo --estilo clasico >/dev/null && grep -q '<body[^>]*data-estilo="clasico"' "$S/c.html" || { echo "nuevo_visual --estilo clasico no lo marca"; return 1; }
  grep -q '· estilo: clasico ·' "$S/c.html" || { echo "la cabecera no dice el estilo"; return 1; }
  python3 scripts/nuevo_visual.py cifra "$S/n.html" --paleta cielo >/dev/null && grep -q '<body[^>]*data-estilo="noche"' "$S/n.html" || { echo "nuevo_visual sin --estilo no da Noche"; return 1; }
  python3 scripts/nuevo_visual.py cifra "$S/x.html" --estilo raro >/dev/null 2>&1; [[ $? -eq 2 && ! -e "$S/x.html" ]] || { echo "--estilo raro debería salir 2 sin escribir"; return 1; }
}
paso "estilo: materializar deja Noche en un hilo y clásico en modo investigacion (data-estilo del body); nuevo_visual --estilo clasico|noche|raro" estilo_investigacion

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

echo "== banco de ideas (banco y memoria temporales; no toca ideas/ ni memoria/)"
IB="$TMP/ideas"; mkdir -p "$IB/in"
cat > "$IB/hilos.json" <<'JSON'
{"version": 1, "hilos": [{"id": "2026-01-01-canasta", "tema": "canasta basica", "tesis": "", "estado": "listo", "idea_id": "canasta-basica-vs-salario"}]}
JSON
cat > "$IB/datos.json" <<'JSON'
{"version": 1, "datos": [{"id": "2026-01-02-sarampion-guatemala-2026", "tema": "El brote de sarampión de 2026 en Guatemala frente al resto de América", "dato": "Guatemala concentra la mayoría de casos de la región", "estado": "listo"}]}
JSON
echo '{"version": 1, "informes": []}' > "$IB/informes.json"
cat > "$IB/in/ideas_prueba.json" <<'JSON'
{"grupo": "prueba", "ideas": [
 {"id": "canasta-basica-vs-salario", "titulo": "Canasta básica frente al salario mínimo", "area": "economia", "pregunta": "¿Cuántas horas de salario mínimo cuesta la canasta básica alimentaria?", "por_que_ahora": "INE publicó septiembre", "hook_sugerido": "escala_humana", "paleta_sugerida": "maiz", "datos": [{"fuente": "INE", "indicador": "CBA", "url": "https://www.ine.gob.gt/x", "formato": "pdf", "periodo": "2016–2026", "evidencia": "Costo de la CBA a septiembre", "acceso": "confirmado"}], "puntaje": {"interes": 5, "datos": 4, "actualidad": 4}},
 {"id": "salario-minimo-canasta-basica", "titulo": "Salario mínimo y canasta básica", "area": "economia", "pregunta": "¿El salario mínimo alcanza para la canasta básica alimentaria?", "por_que_ahora": "x", "hook_sugerido": "escala_humana", "paleta_sugerida": "maiz", "datos": [{"fuente": "INE", "indicador": "CBA", "url": "https://a.gt", "evidencia": "cita de prueba"}], "puntaje": {"interes": 3, "datos": 3, "actualidad": 3}},
 {"id": "electricidad-tarifa", "titulo": "Tarifa eléctrica social", "area": "energia", "pregunta": "¿Cuánto pagan los hogares por kWh desde el subsidio?", "por_que_ahora": "ajuste trimestral de la CNEE", "hook_sugerido": "antes_despues", "paleta_sugerida": "cielo", "datos": [{"fuente": "CNEE", "indicador": "pliego tarifario", "url": "https://www.cnee.gob.gt/x", "formato": "pdf", "periodo": "2016–2026", "evidencia": "Pliego tarifario trimestral", "acceso": "serie"}], "puntaje": {"interes": 4, "datos": 4, "actualidad": 3}},
 {"id": "sarampion-region-cobertura-brote", "titulo": "Sarampión 2026: la región frente a Guatemala y el brote", "area": "salud", "pregunta": "¿Cómo se compara el brote de Guatemala con el de América?", "por_que_ahora": "informe de OPS", "hook_sugerido": "curiosity_gap", "paleta_sugerida": "terracota", "datos": [{"fuente": "OPS", "indicador": "casos", "url": "https://www.paho.org/x", "evidencia": "Situation Report 13", "acceso": "confirmado"}], "puntaje": {"interes": 4, "datos": 4, "actualidad": 4}},
 {"id": "igss-afiliados-cotizantes", "titulo": "Récord de cotizantes del IGSS", "area": "poblacion", "pregunta": "¿Qué parte de quienes trabajan cotiza al IGSS?", "por_que_ahora": "récord anunciado en octubre", "hook_sugerido": "mito_vs_dato", "paleta_sugerida": "jade", "datos": [{"fuente": "AGN", "indicador": "afiliados", "url": "https://agn.gt/x", "evidencia": "IGSS alcanza récord de 1.8 millones", "acceso": "prensa"}], "puntaje": {"interes": 4, "datos": 4, "actualidad": 5}},
 {"id": "sin-evidencia", "titulo": "Idea sin datos", "area": "economia", "pregunta": "x", "por_que_ahora": "y", "datos": [], "puntaje": {"interes": 3, "datos": 3, "actualidad": 3}}
]}
JSON
ideas_cmd() { python3 scripts/ideas.py --banco "$IB/banco.json" --hilos "$IB/hilos.json" --datos "$IB/datos.json" --informes "$IB/informes.json" "$@"; }
ideas_importar() {
  ideas_cmd --importar "$IB/in" --fecha 2026-01-01 >"$IB/imp.log" || return 1
  grep -q "3 nuevas · 2 repetidas · 1 inválidas" "$IB/imp.log" || { cat "$IB/imp.log"; return 1; }
  grep -q "ya cubierta sarampion-region-cobertura-brote (≈ dato 2026-01-02-sarampion-guatemala-2026)" "$IB/imp.log" || { echo "no rechazó la idea ya publicada como dato"; return 1; }
  [[ -s "$IB/README.md" ]] || { echo "no se generó README.md"; return 1; }
}
paso "ideas.py --importar (3 nuevas, 1 repetida por palabras clave, 1 ya cubierta por un dato, 1 sin evidencia)" ideas_importar
ideas_tope() { ideas_cmd --ver igss-afiliados-cotizantes | grep -q '"datos": 2,'; }
paso "ideas.py --importar topa puntaje.datos en 2 sin acceso confirmado ni serie" ideas_tope
ideas_excluir() { ideas_cmd --excluir | python3 -c 'import json,sys; x=json.load(sys.stdin); sys.exit(0 if any(e.startswith("[dato] El brote de sarampión") for e in x) and any(e.startswith("[idea pendiente]") for e in x) else 1)'; }
paso "ideas.py --excluir lista lo producido (con datos) y el banco, etiquetado" ideas_excluir
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
tarjeta_noche_informe() {  # informe.py copiar_tarjeta: el informe se queda clásico aunque la tarjeta del hilo sea Noche
  local D="$TMP/tarjeta_noche"; rm -rf "$D"; mkdir -p "$D"
  python3 - "$D" <<'PY'
import json, re, sys; sys.path.insert(0, "scripts")
import informe as I, materializar as M, nuevo_visual as NV
D = sys.argv[1]; tk = NV.tokens(); err = []
g = json.load(open("sesiones/_fixture/guion.json", encoding="utf-8")); v = g["tuits"][0]["visual"]; pal = g.get("paleta", "cielo")
datos = "const DATA = " + json.dumps(M.data_de(v, "@DerekUrizar"), ensure_ascii=False, indent=2) + ";\n"
def tarjeta(n, estilo, png):   # tuit_N.html como lo deja materializar (plantilla, paleta, estilo y DATA) y su PNG
    ok, msg = NV.ensamblar(v["plantilla"], "%s/tuit_%d.html" % (D, n), pal, tk, estilo); assert ok, msg
    src = open("%s/tuit_%d.html" % (D, n), encoding="utf-8").read()
    open("%s/tuit_%d.html" % (D, n), "w", encoding="utf-8").write(M.RE_DATA.sub(lambda _m: datos, src, count=1))
    open("%s/tuit_%d.png" % (D, n), "wb").write(png)
# Noche: se rearma clásica desde su HTML (misma plantilla, paleta y DATA) y el PNG Noche no llega al informe
tarjeta(1, "noche", b"png noche")
assert I.copiar_tarjeta(D + "/tuit_1.png", D + "/fig_01.png", tk, err, "tarjeta 1"), err
h = open(D + "/fig_01.html", encoding="utf-8").read()
cuerpo = lambda html: re.search(r"<body\b[^>]*>", html).group(0)   # el estilo va en el <body> (base.html nombra los dos en su CSS)
assert 'data-estilo="clasico"' in cuerpo(h), ("no se rearmó clásica", cuerpo(h))
assert M.RE_DATA.search(h).group(0) == datos, "la DATA de la tarjeta no pasó al informe"
assert open(D + "/fig_01.png", "rb").read(8) == b"\x89PNG\r\n\x1a\n", "falta el PNG clásico (render.js)"
# clásica: se copia tal cual
tarjeta(2, "clasico", b"png clasico")
assert I.copiar_tarjeta(D + "/tuit_2.png", D + "/fig_02.png", tk, err, "tarjeta 2"), err
assert open(D + "/fig_02.png", "rb").read() == b"png clasico", "una clásica se rearmó en vez de copiarse (¿data-estilo buscado fuera del <body>?)"
# Noche sin cabecera ni DATA: no se puede rearmar, falla con su motivo
open(D + "/tuit_3.html", "w").write('<body data-estilo="noche"></body>'); open(D + "/tuit_3.png", "wb").write(b"x")
assert not I.copiar_tarjeta(D + "/tuit_3.png", D + "/fig_03.png", tk, err, "tarjeta 3") and "no se puede rearmar" in err[-1], err
PY
}
paso "informe.py copiar_tarjeta: una tarjeta Noche se rearma clásica con su DATA; una clásica se copia tal cual; sin cabecera falla" tarjeta_noche_informe
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
paso "video.py anios_de (años del eje: «p» de la serie, nombre de las partes, «1997-98», sin repetir)" python3 -c '
import sys; sys.path.insert(0, "scripts"); import video
cifras = {"a": {"serie": [{"p": "2019", "v": 1}, {"p": "abr-jun 2026", "v": 2}, {"p": "2023-01", "v": 3}]},
          "b": {"partes": [{"nombre": "1997-98", "valor": 1}, {"nombre": "2019", "valor": 2}, {"nombre": "Jalapa", "valor": 3}]}}
assert video.anios_de({"cifra_ids": ["a", "b", "zz"]}, cifras) == ["2019", "2023", "1997"], video.anios_de({"cifra_ids": ["a", "b"]}, cifras)
assert video.anios_de({}, cifras) == []
'
paso "video.py «K de cada N» con el redondeo de N (70.74 % → «7 de cada 10», no «8 de cada 10»)" python3 -c '
import sys; sys.path.insert(0, "scripts"); import video as v
assert v.escribe_numero(70.74, ["7 de cada 10"]) and not v.escribe_numero(70.74, ["8 de cada 10"])
assert v.escribe_numero(56.4, ["56 de cada 100"]) and not v.escribe_numero(56.4, ["57 de cada 100"]) and v.escribe_numero(3.0, ["1 de cada 3"])
'
VT="$TMP/video"
paso "video.py preparar sobre el fixture (duración prueba)" bash -c "python3 scripts/video.py preparar sesiones/_fixture/salida --duracion prueba --trabajo '$VT' --permitir-borrador --sin-rotacion >/dev/null && cp sesiones/_fixture_video/guion.json sesiones/_fixture_video/ganchos.json sesiones/_fixture_video/seleccion.json '$VT/'"
paso "video.py ganchos --check (5 candidatos de familias distintas, R1–R10)" python3 scripts/video.py ganchos "$VT" --check
paso "video.py ganchos --usar (seleccion.json → escena 1 de guion.json; el segundo queda para la versión B)" bash -c '
python3 scripts/video.py ganchos "$1" --usar >/dev/null && python3 - "$1" <<PY
import json, sys
G = json.load(open(sys.argv[1] + "/ganchos.json", encoding="utf-8")); g = json.load(open(sys.argv[1] + "/guion.json", encoding="utf-8"))
assert G["elegido"] == "g4" and G["segundo"] == "g1", (G.get("elegido"), G.get("segundo"))
e = g["escenas"][0]
assert e["tipo"] == "gancho" and e["familia"] == "tu" and e["visual"] == "llenado" and e["texto"].startswith("Tu galón"), e
assert "promesa_sugerida" not in e and "por_que" not in e and "id" not in e, e
PY' _ "$VT"
paso "video.py guion --check (V1–V5, V9) sobre el guion v2 del fixture" python3 scripts/video.py guion "$VT" --check
paso "locucion.json v2 (tipos, cinetico, valor_calculo, hueco_max_s ≤ 6)" python3 -c '
import json, sys
L = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"]
assert [e["tipo"] for e in L] == ["gancho", "tarjeta", "tarjeta", "golpe", "ranking", "definicion", "cierre"], [e["tipo"] for e in L]
assert L[5]["cinetico"] == {"pantalla": "Precio promedio", "linea": "Lo que pagó un conductor típico en el mes, no el precio de un solo día."}, L[5]["cinetico"]
assert L[3]["cinetico"]["pantalla"] == "1.8 veces" and 1.7 < L[3]["valor_calculo"] < 1.8 and L[1]["valor_calculo"] > 50
assert all(e["hueco_max_s"] <= 6 for e in L[:-1]), [e["hueco_max_s"] for e in L]
assert L[0]["voz"].startswith("Tu galón de diésel costaba veintiséis") and L[0]["familia"] == "tu", L[0]["voz"]
assert L[0]["visual"] == {"tipo": "llenado", "capacidad": 26.0, "total": 46.1, "unidad": "quetzales"}, L[0]["visual"]
assert all(e["prompt"] == e["voz"] for e in L), "el guion del fixture no lleva pausas"
' "$VT/locucion.json"
paso "video.py narracion --check sobre el fixture: 0 fallas e imprime palabras, conectores y «según» por acto" bash -c "python3 scripts/video.py narracion '$VT' --check > '$TMP/vnarr.out' && grep -q 'acto 2 · ' '$TMP/vnarr.out' && grep -q 'conector(es) (por eso, así que)' '$TMP/vnarr.out' && grep -q 'narracion ok' '$TMP/vnarr.out'"
paso "secuencias de voz por acto: el gate las deriva (sin el gancho ni el cierre) y la locución las graba de corrido" python3 -c '
import json, sys
L = json.load(open(sys.argv[1], encoding="utf-8"))
assert L["voz_continua"] and [x["escenas"] for x in L["secuencias"]] == [[3, 4], [5, 6]], L["secuencias"]
assert [x["secuencia"] for x in L["escenas"]] == [None, None, 1, 1, 2, 2, None], [x["secuencia"] for x in L["escenas"]]
' "$VT/locucion.json"
paso "video.py oyente: la narración de corrido en orden (gancho primero, cierre al final) y voz y pantalla por escena" bash -c "python3 scripts/video.py oyente '$VT' > '$TMP/voy.out' && grep -q '^E2 · tarjeta · PANTALLA' '$TMP/voy.out' && python3 -c \"import sys; t=open(sys.argv[1]).read().split('## Escena por escena')[0]; assert t.index('Tu galón') < t.index('Por eso en la bomba') < t.index('Un conductor paga'), t\" '$TMP/voy.out'"
paso "sfx.py --check (K2: los 8 efectos fijos)" python3 scripts/sfx.py --check
paso "video.py preparar rechaza un hilo en borrador sin --permitir-borrador (exit 1)" bash -c "! python3 scripts/video.py preparar sesiones/_fixture/salida --duracion prueba --trabajo '$TMP/video_borrador' >/dev/null 2>&1"
# video_neg "<texto esperado en FALLA>" '<python que muta G (guion.json)>': el gate debe fallar con ese motivo
# rehace guion.narracion desde las voces (V17: la narración es la suma literal de las escenas) tras una mutación que
# debe seguir pasando el gate; una escena nueva sin acto toma el de la anterior
rehacer_narracion() { python3 - "$1" <<'PY'
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); voces = {1: [], 2: [], 3: []}; ac = 1
for i, e in enumerate(G["escenas"], 1):
    ac = 1 if i == 1 else e.setdefault("acto", ac); voces[ac].append(e["texto"])
voces[3].append(G["cierre"]["texto"])
G["narracion"] = [{"acto": a, "texto": " ".join(voces[a])} for a in (1, 2, 3)]
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
}
export -f rehacer_narracion
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
paso "video gate: cierre.texto que no termina con la frase final → V5" video_neg "V5 cierre.texto debe terminar con cierre.final" 'G["cierre"]["texto"] = "El barril subió y la bomba lo sintió."'
paso "video gate: cierre sin tipo ni forma → V1" video_neg "V1 cierre sin «tipo»" 'del G["cierre"]["tipo"]; del G["cierre"]["forma"]'
paso "video gate: pregunta final que no nombra el tema (analogía de otro ámbito) → F3" video_neg "F3 «¿Cuántas personas duermen en tu casa por cada cuarto?» no nombra nada del tema" 'G["cierre"].update(tipo="pregunta", forma="experiencia", final="¿Cuántas personas duermen en tu casa por cada cuarto?"); G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: cebo de interacción en el cierre → F4" video_neg "F4 «Comenta» es cebo" 'G["cierre"]["final"] = "Comenta si tu galón pasó de 26 a 46.1 quetzales."; G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: remate que vuelve a la cifra del gancho → F6" video_neg "F6 el remate repite la cifra del gancho" 'G["cierre"]["final"] = "Un conductor paga 46.1 quetzales por el galón de diésel."; G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: consecuencia sin gente (una tasa) → F6" video_neg "no es gente" 'G["cierre"]["consecuencia"]["quien"] = "El diésel"; G["cierre"]["final"] = "El diésel pesa casi el doble en cada bomba."; G["cierre"]["consecuencia"]["verbo"] = "pesa"; G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: remate fatalista → F8" video_neg "F8 «no hay nada que" 'G["cierre"]["final"] = "Un conductor paga el doble y no hay nada que hacer."; G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: remate que proyecta una pérdida al futuro → F8" video_neg "F8 «pagarán» proyecta al futuro" 'G["cierre"]["consecuencia"].update(quien="Los conductores", verbo="pagarán"); G["cierre"]["final"] = "Los conductores pagarán el doble por el galón de diésel."; G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: remate con «?» → F2" video_neg "F2 un remate no es una pregunta" 'G["cierre"]["final"] = "¿Tu galón pasó de 26 a 46.1 quetzales?"; G["cierre"]["texto"] = "El barril subió y la bomba lo sintió en todo el país. " + G["cierre"]["final"]'
paso "video gate: «no tenían 2 años» para una edad → V5" video_neg "V5 «no tenían 2 años» no se entiende" 'G["escenas"][2]["texto"] += " Los conductores no tenían 2 años."'
paso "video gate: forma de cierre desconocida → F1" video_neg "F1 cierre.forma «moraleja»" 'G["cierre"]["forma"] = "moraleja"'
paso "video cierre: F5 (tema sensible: sin experiencia ni «tu casa»), F7 (pregunta tras pregunta, forma y mecanismo repetidos) y F1/F6 (el bucle de dato ya no es remate) en reglas_cierre" python3 -c '
import sys; sys.path.insert(0, "scripts"); import video as v
hilo = {"tema": "Hacinamiento en las cárceles", "tesis": "Las cárceles tienen 3.42 presos por espacio"}
tarj = [{"titular": "Pavón: 4,464 presos en un penal para 960"}]
st = {"cierres_recientes": {"tipos": ["pregunta"], "formas": ["experiencia", "elegir"]}}
f = v.reglas_cierre({"tipo": "pregunta", "forma": "experiencia", "final": "¿Cuántos presos caben en tu casa?", "texto": "x"}, st, hilo, tarj, [960.0])
assert any(x.startswith("F5 tema sensible: la pregunta no pide") for x in f) and any("«tu casa»" in x for x in f), f
assert any(x.startswith("F7 el video anterior cerró con una pregunta") for x in f) and any(x.startswith("F7 la forma «experiencia»") for x in f), f
ok = v.reglas_cierre({"tipo": "remate", "forma": "consecuencia", "final": "Esta noche, 4,464 presos duermen en Pavón.", "texto": "x",
                      "consecuencia": {"mecanismo": "quien", "quien": "4,464 presos", "verbo": "duermen"}}, st, hilo, tarj, [960.0])
assert ok == [], ok
st["cierres_recientes"]["mecanismos"] = ["quien"]
f = v.reglas_cierre({"tipo": "remate", "forma": "consecuencia", "final": "Esta noche, 4,464 presos duermen en Pavón.", "texto": "x",
                     "consecuencia": {"mecanismo": "quien", "quien": "4,464 presos", "verbo": "duermen"}}, st, hilo, tarj, [960.0])
assert any(x.startswith("F7 el mecanismo «quien»") for x in f), f
f = v.reglas_cierre({"tipo": "remate", "forma": "bucle", "final": "En Pavón caben 960. En 2025 había 4,464.", "texto": "x"}, st, hilo, tarj, [960.0, 4464.0])
assert any(x.startswith("F1 cierre.forma «bucle»") for x in f) and any(x.startswith("F6 el remate") for x in f), f
'
paso "video cierre: cierres_recientes y frases de memoria con tipo y forma (videos viejos = pregunta · experiencia)" python3 -c '
import sys; sys.path.insert(0, "scripts"); import video as v, memoria as m
r = v.cierres_recientes("__ninguno__")
assert set(r) == {"tipos", "formas", "mecanismos"} and len(r["tipos"]) <= 1 and len(r["formas"]) <= 2 and len(r["mecanismos"]) <= 1, r
fr = m.frases_video({"cierre": {"tipo": "remate", "forma": "consecuencia", "final": "Esta noche, 4,464 presos duermen en Pavón.",
                                "consecuencia": {"mecanismo": "quien"}}, "escenas": []})
assert fr["cierre"] == "Esta noche, 4,464 presos duermen en Pavón." and fr["cierre_tipo"] == "remate" and fr["cierre_forma"] == "consecuencia" and fr["cierre_mecanismo"] == "quien", fr
'
paso "video gate: icono desconocido → V1" video_neg "V1 escena 1: icono «no-existe»" 'G["escenas"][0]["icono"] = "no-existe"'
paso "video gate: primera oración del gancho de más de 4 s → V9" video_neg "V9 gancho: la primera oración dura" 'G["escenas"][0]["texto"] = "Tu galón de diésel, el que llenas en la bomba de cada esquina de Guatemala, costaba 26 quetzales. En septiembre, 46.1."'
paso "video gate: promesa de más de 3 s en la escena 1 → V9 (en: 2)" video_neg "V9 gancho: la promesa dura" 'G["promesa"] = {"texto": "Quédate hasta el final y sabrás cuál de nuestros vecinos paga todavía más por cada galón.", "en": 1, "pago": 5}; G["escenas"][0]["texto"] += " " + G["promesa"]["texto"]'
paso "video gate: promesa con «al final te digo» → V9" video_neg "V9 promesa.texto usa «al final te digo»" 'G["escenas"][1]["texto"] = G["escenas"][1]["texto"].replace("Quédate: hay un vecino que paga todavía más.", "Al final te digo qué vecino paga más."); G["promesa"]["texto"] = "Al final te digo qué vecino paga más."'
paso "video gate: promesa que empieza con un conector suelto → V9" video_neg "V9 promesa.texto empieza con un conector suelto" 'G["escenas"][1]["texto"] = G["escenas"][1]["texto"].replace("Quédate: hay un vecino que paga todavía más.", "Pero un vecino paga más."); G["promesa"]["texto"] = "Pero un vecino paga más."'
paso "video gate: caption con «te lo digo al final» → V5" video_neg "V5 caption.tiktok usa" 'G["caption"]["tiktok"] += " ¿Quién paga más? Te lo digo al final."'
paso "video gate: ranking sobre una tarjeta cifra → V1" video_neg "V1 escena 2: la escena ranking necesita una tarjeta barras-h o mapa" 'G["escenas"][1]["tipo"] = "ranking"'
paso "video gate: ranking con top 7 → V1" video_neg "V1 escena 5: top 7 fuera de 3–6" 'G["escenas"][4]["top"] = 7'
paso "video gate: ranking cuya voz no dice el primer valor → V9" video_neg "V9 escena 5: la voz no dice el valor del primer puesto" 'G["escenas"][4]["texto"] = "Pero no somos los que más pagan: en Guatemala el galón promedia 4.85 dólares."'
paso "video gate: tiempo sobre una barras-h → V1" video_neg "V1 escena 5: la escena tiempo necesita una tarjeta antes-despues o linea" 'G["escenas"][4]["tipo"] = "tiempo"'
paso "video gate: dos escenas completas de la misma tarjeta → V1" video_neg "V1 escena 5: T2 repetida" 'G["escenas"][4]["tipo"] = "tiempo"; G["escenas"][4]["tuit"] = 2'
paso "video gate: escala con K ≥ N → V1" video_neg "V1 escena 4: de_cada \\[5, 3\\] fuera de rango" 'G["escenas"][3] = {"tipo": "escala", "enlace": "por_eso", "de_cada": [5, 3], "etiqueta": "x", "calculo": "(pre-c03/pre-c02-1)*100", "texto": "Así que pagas 5 de cada 3."}'
paso "video gate: escala cuya voz no dice «K de cada N» → V9" video_neg "V9 escena 4: la voz no dice «77 de cada 100»" 'G["escenas"][3] = {"tipo": "escala", "enlace": "por_eso", "de_cada": [77, 100], "etiqueta": "x", "calculo": "(pre-c03/pre-c02-1)*100", "texto": "Así que pagas un 77% más que en enero."}'
paso "video gate: icono en una tarjeta → V1" video_neg "V1 escena 2: \`icono\` solo va en gancho" 'G["escenas"][1]["icono"] = "droplets"'
paso "iconos.py --check (K3: la biblioteca fija de iconos está completa)" python3 scripts/iconos.py --check
paso "video gate: cierre que menciona fuentes → V5" video_neg "V5 el cierre no menciona" 'G["cierre"]["texto"] = "Las fuentes están en el hilo. " + G["cierre"]["texto"]'
paso "video gate: tarjeta repetida → V1" video_neg "V1 escena 5: T2 repetida" 'G["escenas"][4]["tuit"] = 2'
paso "video gate: demasiado largo → V4" video_neg "V4 duración estimada" 'G["escenas"][4]["texto"] += " Guatemala sale bajo en el promedio del año porque incluye los meses de subsidio, cuando el Congreso aprobó un techo al precio."'
paso "video gate: «gancho» de la v1 → migración" video_neg "V1 «gancho» ya no existe" 'G["gancho"] = "¿Cuánto pesa el crudo?"'
paso "video gate: escena 1 que no es gancho → V9" video_neg "V9 la escena 1 debe ser tipo gancho" 'G["escenas"][0]["tipo"] = "golpe"'
paso "video gate: familia desconocida → V9" video_neg "V9 gancho: familia «susto»" 'G["escenas"][0]["familia"] = "susto"'
paso "video gate: pantalla del gancho demasiado larga → V9" video_neg "V9 gancho: pantalla" 'G["escenas"][0]["pantalla"] = "El barril de petróleo subió mucho este año"'
paso "video gate: la cifra va sola en pantalla → R2" video_neg "R2 la cifra va sola" 'G["escenas"][0].update(familia="resultado", visual="cifra", pantalla="46.1 quetzales", linea="el galón de diésel en septiembre"); G["escenas"][0].pop("visual_datos")'
paso "video gate: voz del gancho demasiado larga → V4" video_neg "V4 escena 1 (gancho)" 'G["escenas"][0]["texto"] += " Y el transporte público subió en todo el país, departamento por departamento, sin excepción alguna."'
paso "video gate: escena 2 que no es T1 → V9" video_neg "V9 la escena 2 debe ser la tarjeta T1" 'G["escenas"][1], G["escenas"][2] = G["escenas"][2], G["escenas"][1]'
paso "video gate: sin narración de corrido → V17" video_neg "V17 «narracion»: 3 entradas" 'del G["narracion"]'
paso "video gate: enlace desconocido → V9" video_neg "V9 escena 4: enlace «luego»" 'G["escenas"][3]["enlace"] = "luego"'
paso "video gate: una voz que no está en la narración → V17" video_neg "V17 acto 2: la narración no es la suma de las voces" 'G["escenas"][2]["texto"] = G["escenas"][2]["texto"].replace("Por eso en", "En")'
paso "video gate: un acto sin conectores en la narración → V18" video_neg "V18 acto 2: 0 conector" 'exec("for e in G[\"escenas\"][2:4]:\n e[\"texto\"] = e[\"texto\"].replace(\"Por eso en\", \"En\").replace(\"Así que llenar\", \"Llenar\")\nG[\"narracion\"][1][\"texto\"] = \" \".join(e[\"texto\"] for e in G[\"escenas\"][2:4])")'
paso "video gate: una referencia sin antecedente → V18" video_neg "V18 escena 3: «esos 7 tanques» apunta a algo que no se dijo antes" 'exec("t = G[\"escenas\"][2][\"texto\"]; n = t.replace(\"Por eso en la bomba\", \"Por eso en esos 7 tanques\")\nG[\"escenas\"][2][\"texto\"] = n; G[\"narracion\"][1][\"texto\"] = G[\"narracion\"][1][\"texto\"].replace(t, n)")'
paso "video gate: el enlace es opcional (solo elige el efecto de sonido)" bash -c 'd="$1/video_sin_enlace"; rm -rf "$d"; cp -R "$2" "$d"; python3 -c "import json,sys; p=sys.argv[1]; G=json.load(open(p)); [e.pop(\"enlace\", None) for e in G[\"escenas\"]]; json.dump(G, open(p,\"w\"), ensure_ascii=False)" "$d/guion.json" && python3 scripts/video.py guion "$d" --check >/dev/null' _ "$TMP" "$VT"
paso "video gate: golpe demasiado largo → V9" video_neg "V9 escena 3: golpe «" 'G["escenas"][2]["golpe"] = "El galón de diésel pasó de veintiséis a cuarenta y seis"'
paso "video gate: golpe que repite el titular → V9" video_neg "V9 escena 2: golpe repite el titular de T1" 'G["escenas"][1]["golpe"] = "cerró septiembre en US$102"'
paso "video gate: dos golpes seguidos → V9" video_neg "dos golpes seguidos" 'G["escenas"].insert(4, dict(G["escenas"][3]))'
paso "video gate: escenas de texto fuera de rango → V1" video_neg "escenas de texto (golpes, definición, adivina, explica); «prueba» pide 0–2" 'G["escenas"].append({"tipo": "golpe", "enlace": "y", "pantalla": "102 dólares", "linea": "el barril", "texto": "Y el barril sigue en 102 dólares."})'
paso "video gate: promesa que no es literal → V9" video_neg "V9 promesa.texto no aparece literal" 'G["promesa"]["texto"] = "Y esto no termina aquí."'
paso "video gate: pago fuera del último tercio → V9" video_neg "V9 promesa.pago = 2" 'G["promesa"]["pago"] = 2'
paso "video gate: calculo que no da la pantalla → V9" video_neg "V9 escena 4: calculo pre-c03/pre-c02\*2 da" 'G["escenas"][3]["calculo"] = "pre-c03/pre-c02*2"'
paso "video gate: pantalla sin respaldo ni calculo → V9" video_neg "sin respaldo en datos.json ni «calculo»" 'G["escenas"][3]["pantalla"] = "2.5 veces"; del G["escenas"][3]["calculo"]'
paso "video gate: literal del calculo sin respaldo → V9" video_neg "usa el literal 181" 'G["escenas"][3]["calculo"] = "pre-c03/181"'
paso "video gate: cifra inexistente en el calculo → V9" video_neg "usa la cifra pre-c09" 'G["escenas"][3]["calculo"] = "pre-c09/pre-c02"'
paso "video gate: hueco de más de 6 s sin cifra → V9 ritmo" video_neg "sin evento entre" 'G["escenas"][1]["texto"] += " Y eso sin contar lo que subieron el transporte, la comida y todo lo que se mueve en camión por el país entero."'
paso "video gate: la voz del gancho no dice lo que está en pantalla → V9" video_neg "la voz no dice «diesel»" 'G["escenas"][0]["texto"] = G["escenas"][0]["texto"].replace("galón de diésel", "galón")'
paso "video gate: gancho sin «verbo» → V9" video_neg "V9 escena 1 (gancho): falta «verbo»" 'del G["escenas"][0]["verbo"]'
paso "video gate: voz del gancho que lee el titular sin verbo → V9" video_neg "no lleva el verbo «costaba»" 'G["escenas"][0]["texto"] = G["escenas"][0]["texto"].replace("Tu galón de diésel costaba 26 quetzales.", "Tu galón de diésel, 26 quetzales.")'
paso "video gate: la voz del gancho abre con contexto → R3" video_neg "R3 la voz abre con contexto" 'G["escenas"][0]["texto"] = "En Guatemala, tu galón de diésel costaba 26 quetzales. En septiembre, 46.1."'
paso "video gate: «hoy» con un dato sin periodo del año → R7" video_neg "R7 «Hoy»" 'G["escenas"][0]["texto"] = G["escenas"][0]["texto"].replace("En septiembre,", "Hoy,")'
paso "video gate: «Guatemala» ni en el gancho ni en la primera oración de T1 → R6" video_neg "R6 «Guatemala» no se dice" 'G["escenas"][0]["texto"] = "Tu galón de diésel costaba 26 quetzales. En septiembre pagaste 46.1."'
paso "video gate: el visual muestra un número que nadie dice → R4" video_neg "R4 el visual llenado muestra 102" 'G["escenas"][0]["visual_datos"]["total"] = "pre-c01"'
paso "video gate: visual con un número sin respaldo → V2" video_neg "visual llenado: total «47» no tiene respaldo" 'G["escenas"][0]["visual_datos"]["total"] = 47'
paso "video gate: visual que no va con la familia → V9" video_neg "el visual «lugar» no va con la familia tu" 'G["escenas"][0]["visual"] = "lugar"'
paso "video gate: escena 1 distinta del gancho elegido (ganchos.json) → V9" video_neg "no es el gancho elegido «g4»" 'G["escenas"][0]["linea"] = "quetzales de tu galón de diésel"'
paso "video gate: familia repetida de los últimos videos → R9" bash -c '
d="$1/video_r9"; rm -rf "$d"; cp -R "$2" "$d"
python3 -c "import json,sys; p=sys.argv[1]; v=json.load(open(p)); v[\"ganchos_recientes\"]={\"familias\": [\"tu\", \"lugar\"], \"visuales\": [\"llenado\"]}; json.dump(v, open(p, \"w\"))" "$d/video.json"
out="$(python3 scripts/video.py guion "$d" --check 2>&1)" && exit 1
grep -q "R9 la familia «tu»" <<<"$out" && grep -q "R9 el visual «llenado»" <<<"$out"' _ "$TMP" "$VT"
# ganchos_neg "<texto esperado en FALLA>" '<python que muta G (ganchos.json)>': ganchos --check debe fallar con ese motivo
ganchos_neg() {
  local esperado="$1" mut="$2" d="$TMP/ganchos_neg"
  rm -rf "$d"; cp -R "$VT" "$d"
  python3 - "$d/ganchos.json" "$mut" <<'PY' || return 1
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); C = {c["id"]: c for c in G["candidatos"]}
exec(sys.argv[2])
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
  local out; out="$(python3 scripts/video.py ganchos "$d" --check 2>&1)" && return 1
  grep -q "$esperado" <<<"$out"
}
paso "ganchos: familias repetidas → G" ganchos_neg "G familias repetidas" 'C["g2"]["familia"] = "tu"'
paso "ganchos: tres candidatos → G" ganchos_neg "G 3 candidatos" 'G["candidatos"] = G["candidatos"][:3]'
paso "ganchos: menos de 2 con visual → G" ganchos_neg "G al menos 2 candidatos con un visual" 'for k in ("g1", "g4", "g5"): C[k]["visual"] = "cifra"; C[k].pop("visual_datos")'
paso "ganchos: pregunta sin respuesta en el gancho → R8" ganchos_neg "g3: R8 la pregunta se contesta" 'C["g3"]["texto"] = "¿Cuánto subió el diésel en Guatemala desde enero? Te va a sorprender."'
paso "ganchos: figuras cuyo calculo no da «K de cada N» → visual" ganchos_neg "no respalda «3 de cada 4»" 'C["g2"].update(familia="escala", visual="figuras", visual_datos={"de_cada": [3, 4], "etiqueta": "x", "calculo": "pre-c02/pre-c03*100"})'
paso "ganchos: lugar fuera de los 22 departamentos → visual" ganchos_neg "no es uno de los 22 departamentos" 'C["g2"].update(familia="lugar", visual="lugar", visual_datos={"depto": "Narnia", "etiqueta": "x"})'
paso "ganchos: --usar rechaza ids que no existen" bash -c '! python3 scripts/video.py ganchos "$1" --usar g9 --segundo g1 >/dev/null 2>&1' _ "$VT"
paso "video.py variante: la versión B (el segundo, g1) pasa el gate e imprime solo el nodo de la escena 1" bash -c '
d="$1/video_b"; rm -rf "$d"; cp -R "$2" "$d"
out="$(python3 scripts/video.py variante "$d")" || exit 1
python3 - "$d" <<PY
import json, sys
L = json.load(open(sys.argv[1] + "/variante_b/locucion.json", encoding="utf-8"))["escenas"]
assert L[0]["familia"] == "contraste" and L[0]["visual"]["tipo"] == "pareja" and L[0]["voz"].startswith("En enero, el diésel"), L[0]
PY
grep -q "\"n\": 1" <<<"$out" && ! grep -q "\"n\": 2" <<<"$out"' _ "$TMP" "$VT"
paso "video gate: pausa que no va tras puntuación ni antes de «pero» → V9" video_neg "va tras puntuación fuerte" 'G["escenas"][1]["texto"] = G["escenas"][1]["texto"].replace("El barril costaba", "El barril [pausa] costaba")'
paso "video gate: dos pausas en una escena → V9" video_neg "2 pausas en una escena" 'G["escenas"][1]["texto"] = G["escenas"][1]["texto"].replace("más. Un", "más. [pausa] Un") + " [pausa]"'
paso "video gate: pausa justo antes de «pero» vale" bash -c '
d="$1/video_pausa"; rm -rf "$d"; cp -R "$2" "$d"
python3 - "$d/guion.json" <<PY
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8"))
G["escenas"][4]["texto"] = G["escenas"][4]["texto"].replace("5.9 dólares; en Guatemala", "5.9 dólares [pausa larga] aunque en Guatemala")
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$d/guion.json"; python3 scripts/video.py guion "$d" --check >/dev/null && python3 -c "import json,sys; L=json.load(open(sys.argv[1]))[\"escenas\"]; assert \"dólares <break time=\\\"1.2s\\\" /> aunque\" in L[4][\"prompt\"] and \"dólares aunque en Guatemala\" in L[4][\"voz\"], L[4][\"prompt\"]" "$d/locucion.json"' _ "$TMP" "$VT"
paso "video gate: definición cuya voz no dice el término → V9" video_neg "la voz no dice el término" 'G["escenas"][5]["texto"] = "Y es lo que pagó un conductor típico en el mes, no el precio de un solo día."'
paso "video gate: término de más de 3 palabras → V9" video_neg "«termino» de 1–3 palabras" 'G["escenas"][5]["termino"] = "Precio promedio mensual del galón"'
paso "video gate: escena mapa sobre una tarjeta que no es mapa → V1" video_neg "la escena mapa necesita una tarjeta mapa" 'G["escenas"][4] = {"tipo": "mapa", "tuit": 3, "enlace": "pero", "golpe": "El mapa lo dice solo", "texto": "Pero el mapa lo dice solo: el norte concentra la pobreza."}'
paso "video gate: dos definiciones → V1" video_neg "V1 2 definiciones; máximo 1" 'G["escenas"].insert(3, dict(G["escenas"][5], enlace="por_eso", texto="Por eso " + G["escenas"][5]["texto"][2:]))'
paso "video gate: definición cuya voz no anuncia el concepto antes del término → V9" video_neg "la voz debe anunciar el concepto antes de decir «Precio promedio»" 'G["escenas"][5]["texto"] = "Y precio promedio quiere decir lo que pagó un conductor típico en el mes. No el precio de un solo día."'
# la adivina: el golpe del fixture (índice 3) se vuelve una pregunta con tres opciones y revelado
ADIVINA='{"tipo": "adivina", "enlace": "por_eso", "pregunta": "¿A cuánto llegó el barril?", "opciones": ["67 dólares", "90 dólares", "102 dólares"], "correcta": 2, "texto": "Así que adivina: ¿a cuánto llegó el barril? ¿67, 90 o 102? Pausa y piénsalo. Llegó a 102 dólares."}'
paso "video gate: adivina válida → locución con opciones, correcta y pausa antes de la respuesta" bash -c '
d="$1/video_adivina"; rm -rf "$d"; cp -R "$2" "$d"
python3 - "$d/guion.json" "$3" <<PY
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); G["escenas"][3] = json.loads(sys.argv[2])
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$d/guion.json"; python3 scripts/video.py guion "$d" --check >/dev/null && python3 - "$d/locucion.json" <<PY
import json, sys
L = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"]
e = L[3]
assert e["tipo"] == "adivina" and e["adivina"]["correcta"] == 2 and e["adivina"]["opciones"][2] == "102 dólares", e["adivina"]
assert "<break time=\"2.0s\" /> Llegó a ciento dos" in e["prompt"] and "[pausa" not in e["voz"] and "<" not in e["voz"], e["prompt"]
assert e["cinetico"]["pantalla"].endswith("?") and " · " in e["cinetico"]["linea"], e["cinetico"]
PY' _ "$TMP" "$VT" "$ADIVINA"
paso "video gate: adivina con la opción correcta sin respaldo → V9" video_neg "la opción correcta «90 dólares» no tiene respaldo" "import json; G[\"escenas\"][3] = json.loads('$ADIVINA'); G[\"escenas\"][3][\"correcta\"] = 1; G[\"escenas\"][3][\"texto\"] = G[\"escenas\"][3][\"texto\"].replace(\"Llegó a 102\", \"Llegó a 90\")"
paso "video gate: adivina cuya última cifra no es la correcta → V9" video_neg "la última cifra de la voz debe ser la opción correcta" "import json; G[\"escenas\"][3] = json.loads('$ADIVINA'); G[\"escenas\"][3][\"texto\"] = G[\"escenas\"][3][\"texto\"].replace(\"Llegó a 102\", \"Llegó a 67\")"
paso "video gate: adivina que no nombra una opción → V9" video_neg "la voz nombra las 3 opciones; falta" "import json; G[\"escenas\"][3] = json.loads('$ADIVINA'); G[\"escenas\"][3][\"texto\"] = G[\"escenas\"][3][\"texto\"].replace(\"¿67, 90 o 102? \", \"\")"
paso "video gate: adivina sin pedir que pausen para responder → V9" video_neg "una oración pide pausar para responder" "import json; G[\"escenas\"][3] = json.loads('$ADIVINA'); G[\"escenas\"][3][\"texto\"] = G[\"escenas\"][3][\"texto\"].replace(\"Pausa y piénsalo. \", \"\")"
paso "video gate: cierre con menos de 3 s de voz antes de la frase final → V9" video_neg "V9 cierre: .* s de voz antes de la frase final" 'G["cierre"]["texto"] = "Subió. " + G["cierre"]["final"]'
paso "video gate: cierre con 4 líneas de conclusiones → V1" video_neg "V1 cierre.resumen: 2–3 líneas" 'G["cierre"]["resumen"] = ["Uno.", "Dos.", "Tres.", "Cuatro."]'
paso "video gate: cierre con 3 líneas de conclusiones vale y tiempos las reparte antes de la frase final" bash -c '
set -e; d="$1/video_cierre3"; rm -rf "$d"; cp -R "$2" "$d"
python3 - "$d/guion.json" <<PY
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); G["cierre"]["resumen"] = ["El barril, arriba.", "El galón, casi el doble.", "Y no somos los que más pagan."]
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$d/guion.json"; python3 scripts/video.py guion "$d" --check >/dev/null && python3 scripts/video.py voz-falsa "$d" >/dev/null && python3 scripts/video.py tiempos "$d" >/dev/null
python3 - "$d/escenas.json" <<PY
import json, sys
e = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"][-1]
T = e["T"]
assert e["tipo"] == "cierre" and len(T["r"]) == 3 and T["r"][0] < T["r"][1] < T["r"][2] < T["preg"] < T["sigue"], T
PY' _ "$TMP" "$VT"
paso "video gate: adivina cuya pregunta en pantalla tiene palabras que la voz no dice → V9" video_neg "y la voz no: se escribe al ritmo de la voz" "import json; G[\"escenas\"][3] = json.loads('$ADIVINA'); G[\"escenas\"][3][\"pregunta\"] = \"¿A cuánto llegó el barril de la gente en septiembre?\""
paso "video tiempos: la línea de pantalla se alinea con la voz sin anclar un «de» suelto de otra oración" python3 - <<'PY'
import sys; sys.path.insert(0, "scripts")
import video as v
voz = "Y adivina: ¿qué parte de Alta Verapaz está en Fase tres o más? ¿El siete, el quince o el veintiocho por ciento? Más de una de cada cuatro: el veintiocho por ciento."
pal = [{"text": t, "start": i * 0.5} for i, t in enumerate(voz.split())]
out, k = v.alinear_linea("¿Qué parte de la gente de Alta Verapaz está en Fase 3+?".split(), pal, 0.5, 6.0)
assert out[-1]["start"] < 6.0 and [w["text"] for w in out if w.get("dicha")][-1] == "Fase", out
assert all(b["start"] > a["start"] for a, b in zip(out, out[1:])), out
PY
# la explica: el golpe del fixture (índice 3) se vuelve una animación de la biblioteca (la semilla cadena)
EXPLICA='{"tipo": "explica", "enlace": "por_eso", "mecanismo": "cadena", "animacion": "cadena", "brief": "Cadena lineal: el barril sube, el diésel sube detrás y la bomba cobra más; cada caja se llena al decirla.", "titulo": "Del barril a la bomba", "pasos": ["Sube el barril", "Sube el diésel", "Pagas más"], "texto": "Así que la cadena es corta: sube el barril, sube el diésel y pagas más."}'
paso "video gate: explica válida → locución con animación, título y pasos; transición a pantalla completa" bash -c '
d="$1/video_explica"; rm -rf "$d"; cp -R "$2" "$d"
python3 - "$d/guion.json" "$3" <<PY
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); G["escenas"][3] = json.loads(sys.argv[2])
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$d/guion.json"; python3 scripts/video.py guion "$d" --check >/dev/null && python3 - "$d/locucion.json" <<PY
import json, sys
e = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"][3]
assert e["tipo"] == "explica" and e["explica"]["animacion"] == "cadena" and len(e["explica"]["pasos"]) == 3, e["explica"]
PY' _ "$TMP" "$VT" "$EXPLICA"
paso "video gate: explica con animación que no está en la biblioteca y sin brief → V9" video_neg "no está en video/animaciones/catalogo.json" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); G[\"escenas\"][3][\"animacion\"] = \"no-existe\""
paso "video gate: explica nueva (animacion null) sin brief → V9" video_neg "«brief» de 40–400" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); G[\"escenas\"][3][\"animacion\"] = None; G[\"escenas\"][3][\"brief\"] = \"\""
paso "video gate: explica que reutiliza sin brief → V9" video_neg "«brief» de 40–400" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); del G[\"escenas\"][3][\"brief\"]"
paso "video gate: explica sin mecanismo → V9" video_neg "«mecanismo» es uno de" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); del G[\"escenas\"][3][\"mecanismo\"]"
paso "video gate: explica con una animación de otro mecanismo (cadena para una onda) → V9" video_neg "muestra «cadena», no «onda»" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); G[\"escenas\"][3][\"mecanismo\"] = \"onda\""
paso "video gate: explica con la animación del video anterior → V9 (rotación)" video_neg "salió en uno de los últimos" "import json, os; G[\"escenas\"][3] = json.loads('$EXPLICA'); p = os.path.join(os.path.dirname(sys.argv[1]), \"video.json\"); st = json.load(open(p)); st[\"animaciones_recientes\"] = [\"cadena\"]; json.dump(st, open(p, \"w\"))"
paso "video gate: explica con un paso que la voz no dice → V9" video_neg "la voz no dice el paso «Cierran gasolineras»" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); G[\"escenas\"][3][\"pasos\"][2] = \"Cierran gasolineras\""
paso "video gate: explica con un solo paso → V9" video_neg "«pasos»: 2–6 cadenas" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); G[\"escenas\"][3][\"pasos\"] = [\"Sube el barril\"]"
paso "video gate: dos explica seguidas → V1" video_neg "V1 dos escenas explica seguidas" "import json; G[\"escenas\"][3] = json.loads('$EXPLICA'); G[\"escenas\"].insert(4, dict(json.loads('$EXPLICA'), enlace=\"y\", texto=\"Y la cadena sigue: sube el barril, sube el diésel y pagas más.\"))"
paso "animaciones: el lint rechaza azar, reloj, colores fijos, Instrument Serif y font-stretch antes de font:; las de la biblioteca pasan; K4 avisa de un módulo fuera del catálogo" bash -c '
set -e; d="$1/anim_neg"; rm -rf "$d"; mkdir -p "$d"
cp video/animaciones/cadena.js "$d/cadena.js"
cat >> "$d/cadena.js" <<JS
const r = Math.random() + Date.now(); const c = "#ff0000";
const tipo = "font-stretch:62.5%;text-transform:uppercase;font:900 40px/1 Archivo,sans-serif"; const vieja = "Instrument Serif";
JS
python3 - "$d" <<PY
import os, shutil, sys
sys.path.insert(0, "scripts")
import animaciones as A
f = A.lint("cadena", os.path.join(sys.argv[1], "cadena.js"))
assert any("Math.random" in x for x in f) and any("Date" in x for x in f) and any("hexadecimal" in x for x in f), f
assert any("Instrument Serif" in x for x in f) and any("font-stretch antes" in x for x in f), f
assert all(A.lint(x["id"]) == [] for x in A.catalogo()["animaciones"]), {x["id"]: A.lint(x["id"]) for x in A.catalogo()["animaciones"]}
lib = os.path.join(sys.argv[1], "lib"); os.makedirs(lib)
shutil.copy(A.CATALOGO, lib); shutil.copy(A.ruta("cadena"), lib); open(os.path.join(lib, "suelta.js"), "w").write("// sin registrar\n")
A.DIR, A.CATALOGO = lib, os.path.join(lib, "catalogo.json")
k4 = A.fallas_k4()
assert any("suelta.js no está en el catálogo" in x for x in k4), k4
PY' _ "$TMP"
paso "video gate: pausa al inicio de la escena → V9" video_neg "al inicio de la escena no sirve" 'G["escenas"][4]["texto"] = "[pausa] " + G["escenas"][4]["texto"]'
paso "video gate: golpe sin «verbo» → V9" video_neg "V9 escena 4 (golpe): falta «verbo»" 'del G["escenas"][3]["verbo"]'
paso "video gate: una escena abre con las palabras que cerraron la anterior → V9" video_neg "V9 escena 5: empieza con «enero»" 'G["escenas"][4]["texto"] = "Pero lo de enero no es lo peor: en México el galón de diésel promedia 5.9 dólares; en Guatemala, 4.85."'
paso "módulo común de video: cada página de escena enlaza comun.css y comun.js (la portada solo el CSS), no redefine fuentes, trocear, clamp ni eo, y el grabador los sirve" bash -c '
set -e
for f in video/*.html; do
  grep -q "href=.comun.css" "$f" || { echo "$f no enlaza comun.css"; exit 1; }
  [[ "$f" == video/portada.html ]] || grep -q "src=.comun.js" "$f" || { echo "$f no carga comun.js"; exit 1; }
  if grep -nE "@font-face|const (trocear|clamp|eo|prog) =" "$f"; then echo "$f redefine lo que vive en comun.css/comun.js"; exit 1; fi
done
grep -q "\"comun.js\", \"comun.css\"" scripts/video_grabar.js || { echo "video_grabar.js no sirve comun.js y comun.css"; exit 1; }
node -e "global.location = { search: \"?n=3&f=45\" }; const c = new Set(); global.document = { documentElement: { classList: { add: (x) => c.add(x) } } };
eval(require(\"fs\").readFileSync(\"video/comun.js\", \"utf8\") + \";global.V = V\");
const t = V.trocear([{ text: \"Hola\" }, { text: \"mundo.\" }, { text: \"otra\" }]);
if (V.n !== 3 || !V.F45 || !c.has(\"f45\") || t.length !== 2 || V.esc(\"a<b\") !== \"a&lt;b\" || V.esc(null) !== \"\" || V.prog(2, 0, 1) !== 1) process.exit(1);"'
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make video-fixture (RAPIDO=1)"; else
  paso "make video-fixture (voz falsa, V6–V8, V10, 10 fps)" make video-fixture
  paso "fixture de video: 1080×1920 con audio y guion de entrega" bash -c 'ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_video/salida/video.mp4 | grep -q "video,1080,1920" && test -s sesiones/_fixture_video/salida/guion.json && test -s sesiones/_fixture_video/salida/subtitulos.srt'
  paso "cierre en bucle (dura total + 0.35 s y el último cuadro es el primero del gancho) y portadas pregunta/giro" bash -c '
set -e; V=sesiones/_fixture_video/salida/video.mp4; D="$1"
T=$(python3 - "$V" <<PY
import json, subprocess, sys
V = sys.argv[1]
E = json.load(open("sesiones/_fixture_video/trabajo/escenas.json", encoding="utf-8"))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", V], capture_output=True, text=True).stdout)
assert abs(dur - (E["total_s"] + 0.35)) <= 0.35, (dur, E["total_s"])
print("%.2f" % (dur - 0.15))  # dentro del último cuadro (el bucle puro dura 0.35 s)
PY
)
ffmpeg -loglevel error -y -i "$V" -frames:v 1 "$D/primero.png"
ffmpeg -loglevel error -y -ss "$T" -i "$V" -frames:v 1 -update 1 "$D/ultimo.png"
S=$(ffmpeg -i "$D/primero.png" -i "$D/ultimo.png" -lavfi ssim -f null - 2>&1 | grep -o "All:[0-9.]*" | cut -d: -f2)
python3 -c "import sys; s=float(sys.argv[1]); assert s >= 0.97, (\"ssim\", s)" "$S"
test -s sesiones/_fixture_video/salida/portada_cierre.png && test -s sesiones/_fixture_video/salida/portada_giro.png' _ "$TMP"
  paso "escenas.json v2 (tipos, eventos, efectos del catálogo, hueco real ≤ 6 s)" python3 -c '
import json
E = json.load(open("sesiones/_fixture_video/trabajo/escenas.json", encoding="utf-8"))
G = json.load(open("sesiones/_fixture_video/guion.json", encoding="utf-8"))
cat = {x["id"] for x in json.load(open("design/sfx/catalogo.json", encoding="utf-8"))["efectos"]}
assert E["version"] == 2 and E["escenas"][0]["tipo"] == "gancho" and E["gancho"]["pantalla"] == G["escenas"][0]["pantalla"], E["gancho"]
assert E["transicion_s"] == 0.3 and E["escenas"][0]["transicion"] is None and E["escenas"][1]["transicion"] == "smoothleft"
import os; assert os.path.exists("sesiones/_fixture_video/trabajo/revision/linea_tiempo.png")
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
  paso "descargar --estado: voz por prompt (la más reciente), palabras por id de generación, créditos por generación" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; D="$1/video_estado"; rm -rf "$D"; cp -R "$T" "$D"; rm -f "$D"/audio/voz_*.mp3 "$D"/audio/palabras_*.json "$D"/audio/creditos.json
python3 - "$T" "$D" <<PY
import json, os, sys
T, D = os.path.abspath(sys.argv[1]), sys.argv[2]
L = json.load(open(os.path.join(T, "locucion.json"), encoding="utf-8"))["escenas"]
def gen(n, gid, cr, t):
    return {"id": gid, "status": "completed", "modality": "audio", "prompt": L[n - 1].get("prompt") or L[n - 1]["voz"], "created_at_unix_ms": t,
            "price": {"credits": cr}, "content_url": "file://%s/audio/voz_%d.mp3" % (T, n)}
def tr(n, gid):
    ws = json.load(open(os.path.join(T, "audio", "palabras_%d.json" % n), encoding="utf-8"))
    pw = os.path.join(D, "audio", "palabras_src_%d.json" % n)
    ws = [dict(w, type="word") for w in ws]
    if n == 1:   # Scribe devuelve la etiqueta <break> como tres «palabras» de duración cero: descargar las quita
        t = ws[2]["start"]
        ws[2:2] = [{"text": x, "start": t, "end": t, "type": "word"} for x in ("<break", "time=" + chr(34) + "0.6s" + chr(34), "/>")]
    json.dump({"words": ws}, open(pw, "w", encoding="utf-8"))
    return {"generation_id": "tr_" + gid, "text": "", "source": {"url": "https://x/content_generation/ses/%s/content.mp3?x=1" % gid},
            "words_download_url": "file://" + os.path.abspath(pw)}
gens = [gen(e["n"], "gen%d" % e["n"], 10 * e["n"], e["n"]) for e in L]
gens.insert(0, gen(1, "gen1_vieja", 5, 0))   # la escena 1 dos veces: se baja y se cobra la más reciente
# el MCP recorta generations[].prompt a 200 caracteres; media[].prompt viene entero y manda
media = [{"generation_id": "gen2", "prompt": gens[2]["prompt"]}]; gens[2]["prompt"] = gens[2]["prompt"][:40]
json.dump({"generations": gens, "media": media, "transcripts": [tr(e["n"], "gen%d" % e["n"]) for e in L]}, open(os.path.join(D, "estado.json"), "w", encoding="utf-8"))
json.dump({"generations": [gen(1, "gen1_retoma", 7, 99)], "transcripts": [tr(1, "gen1_retoma")]}, open(os.path.join(D, "retoma.json"), "w", encoding="utf-8"))
PY
python3 scripts/video.py descargar "$D" --estado "$D/estado.json" >/dev/null
shopt -s nullglob; for f in "$T"/audio/voz_[0-9].mp3 "$T"/audio/voz_[0-9][0-9].mp3 "$T"/audio/palabras_[0-9]*.json; do cmp -s "$f" "$D/audio/$(basename "$f")" || { echo "difiere $f"; exit 1; }; done
chk() { python3 -c "import json,sys; c=json.load(open(sys.argv[1])); assert (c[\"total\"], len(c[\"generaciones\"])) == (float(sys.argv[2]), int(sys.argv[3])), (sys.argv[4], c)" "$D/audio/creditos.json" "$1" "$2" "$3"; }
N=$(python3 -c "import json; print(len(json.load(open(\"$T/locucion.json\"))[\"escenas\"]))")
S=$((10 * N * (N + 1) / 2))
chk $S $N "la generación vieja no se cobra"
python3 scripts/video.py descargar "$D" --estado "$D/retoma.json" >/dev/null; chk $((S + 7)) $((N + 1)) "la retoma suma"
python3 scripts/video.py descargar "$D" --estado "$D/retoma.json" >/dev/null; chk $((S + 7)) $((N + 1)) "repetir el mismo estado no suma"
rm -f "$D"/audio/voz_2.mp3; ! python3 scripts/video.py descargar "$D" --estado "$D/retoma.json" >/dev/null 2>&1' _ "$TMP"
  paso "descargar --estado: un prompt recortado a 200 caracteres sin media casa por prefijo" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; D="$1/video_estado_prefijo"; rm -rf "$D"; mkdir -p "$D/audio"
python3 - "$T" "$D" <<PY
import json, os, sys
T, D = os.path.abspath(sys.argv[1]), sys.argv[2]
voz = "Una locución larga de prueba que pasa de doscientos caracteres para que el recorte del MCP deje solo el principio " * 2 + "y termina con la cifra final de la escena."
assert len(voz) > 200
json.dump({"escenas": [{"n": 1, "tipo": "gancho", "voz": voz}]}, open(os.path.join(D, "locucion.json"), "w", encoding="utf-8"))
pw = os.path.join(D, "audio", "palabras_src.json"); json.dump({"words": [{"text": "una", "start": 0, "end": 0.2, "type": "word"}]}, open(pw, "w"))
json.dump({"generations": [{"id": "g1", "status": "completed", "modality": "audio", "prompt": voz[:200], "created_at_unix_ms": 1, "price": {"credits": 3},
                             "content_url": "file://%s/audio/voz_1.mp3" % T}],
           "transcripts": [{"generation_id": "t1", "text": "", "source": {"url": "https://x/content_generation/s/g1/content.mp3"}, "words_download_url": "file://" + pw}]},
          open(os.path.join(D, "estado.json"), "w", encoding="utf-8"))
PY
python3 scripts/video.py descargar "$D" --estado "$D/estado.json" >/dev/null
test -s "$D/audio/voz_1.mp3" && test -s "$D/audio/palabras_1.json"
python3 -c "import json,sys; c=json.load(open(sys.argv[1])); assert c[\"total\"] == 3.0, c" "$D/audio/creditos.json"' _ "$TMP"
  paso "V11 escucha: dígitos, coma decimal y género no cuentan; una cifra distinta es falta, una palabra distinta aviso" python3 -c '
import sys; sys.path.insert(0, "scripts"); import video as V
S = [{"v": "casi ", "num": False}, {"v": "una", "num": True}, {"v": " de cada ", "num": False}, {"v": "tres", "num": True}, {"v": " gotas: el ", "num": False},
     {"v": "noventa y nueve punto noventa y seis por ciento", "num": True}, {"v": " y ", "num": False}, {"v": "cuatro punto seis", "num": True}, {"v": " millones en ", "num": False}, {"v": "dos mil veintidós", "num": True}]
f, a, p = V.comparar_escucha(S, "casi 1 de cada 3 gotas: el 99,96% y 4.6 millones en 2022"); assert (f, a, p) == ([], [], 0.0), (f, a, p)
f, a, p = V.comparar_escucha(S, "casi una de cada tres gotas: el 99,96% y 4,7 millones en 2022"); assert len(f) == 1 and "siete" in f[0] and not a, (f, a)
f, a, p = V.comparar_escucha(S, "casi 1 de cada 3 lágrimas: el 99,96% y 4.6 millones en 2022"); assert not f and len(a) == 1 and "lagrimas" in a[0], (f, a)
print("ok")'
  paso "V11 escucha: homófonos, palabras juntas y siglos en romanos no avisan; otra pronunciación sí" python3 -c '
import sys; sys.path.insert(0, "scripts"); import video as V
S = [{"v": "los Castillo Córdova abrieron la Cervecería Centro Americana a fines del siglo diecinueve; Brahva peleó el mercado a la Gallo y Monge habló", "num": False}]
f, a, p = V.comparar_escucha(S, "los castillo cordoba abrieron la cervecería centroamericana a fines del siglo XIX; brava peleó el mercado al agallo y monje habló"); assert (f, a, p) == ([], [], 0.0), (f, a, p)
f, a, p = V.comparar_escucha([{"v": "la etiqueta decía Lager Bier", "num": False}], "la etiqueta decía lagerbjerg"); assert len(a) == 1 and "lagerbjerg" in a[0], a
print("ok")'
  paso "escuchar con un whisper falso: igual → ok · cifra cambiada → FALLA V11 en E2 · palabra cambiada → aviso" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; B="$1/whisper_falso"; rm -rf "$B"; mkdir -p "$B/bin"
cat > "$B/bin/whisper-cli" <<SH
#!/bin/bash
# whisper-cli falso: escribe <of>.json con el texto que dicta la tabla FAKE_WHISPER ({nombre del wav: texto})
of=""; f=""
while [[ \$# -gt 0 ]]; do case "\$1" in -of) of="\$2"; shift;; -f) f="\$2"; shift;; esac; shift; done
python3 - "\$of" "\$f" "\$FAKE_WHISPER" <<PY
import json, os, sys
of, f, tabla = sys.argv[1:4]
texto = json.load(open(tabla)).get(os.path.basename(f))
if texto is None: sys.exit(3)
json.dump({"transcription": [{"text": texto}]}, open(of + ".json", "w"))
PY
SH
chmod +x "$B/bin/whisper-cli"; : > "$B/modelo.bin"
python3 - "$T" "$B" <<PY
import json, sys
T, B = sys.argv[1:3]
L = json.load(open(T + "/locucion.json", encoding="utf-8"))["escenas"]
igual = {"escucha_%d.wav" % e["n"]: e["voz"] for e in L}
e2 = L[1]; segs = e2["segmentos"]; k = next(i for i, s in enumerate(segs) if s["num"])
cifra = dict(igual); cifra["escucha_2.wav"] = "".join(("cero" if i == k else s["v"]) for i, s in enumerate(segs))
palabra = dict(igual); palabra["escucha_1.wav"] = L[0]["voz"].replace("Guatemala", "Honduras", 1)
for nombre, t in (("igual", igual), ("cifra", cifra), ("palabra", palabra)):
    json.dump(t, open("%s/%s.json" % (B, nombre), "w", encoding="utf-8"))
PY
export PATH="$B/bin:$PATH"
FAKE_WHISPER="$B/igual.json" python3 scripts/video.py escuchar "$T" --modelo "$B/modelo.bin" > "$B/igual.out"; grep -q "^E1  ok" "$B/igual.out"
! FAKE_WHISPER="$B/cifra.json" python3 scripts/video.py escuchar "$T" --modelo "$B/modelo.bin" > "$B/cifra.out" 2>&1; grep -q "^E2  FALLA V11" "$B/cifra.out"; grep -q "rehaz la voz de E2" "$B/cifra.out"
FAKE_WHISPER="$B/palabra.json" python3 scripts/video.py escuchar "$T" --modelo "$B/modelo.bin" --solo 1 > "$B/palabra.out"; grep -q "^E1  ok .*aviso: esperaba «guatemala», oyó «honduras»" "$B/palabra.out"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d[\"escenas\"][\"1\"][\"avisos\"] and not d[\"escenas\"][\"1\"][\"faltas\"]" "$T/audio/escucha.json"
rm -f "$T"/audio/escucha*' _ "$TMP"
  paso "escuchar sin whisper-cli: avisa y sale 0" bash -c 'PATH="/usr/bin:/bin" python3 scripts/video.py escuchar sesiones/_fixture_video/trabajo --modelo /no/existe.bin | grep -q "^AVISO V11"'
  paso "V12 quietud: un clip fijo de 3 s (la portada con su grano, en x264 crf 16 como grabar) da un tramo quieto; los clips del fixture, ninguno (revision/quietud.json)" bash -c '
set -e; Q="$1/quietud"; rm -rf "$Q"; mkdir -p "$Q"
# crf 16 y no -qp 0: con el grano fijo de Noche x264 retoca unos píxeles en ±1 entre cuadros iguales (signalstats daba
# YAVG de 1.5–7.7 en esos cuadros y V12 no veía la pantalla congelada)
ffmpeg -y -v error -loop 1 -framerate 30 -i sesiones/_fixture_video/salida/portada.png -t 3 -r 30 -c:v libx264 -pix_fmt yuv420p -crf 16 -preset medium "$Q/fijo.mp4"
python3 - "$Q/fijo.mp4" <<PY
import sys, json, glob; sys.path.insert(0, "scripts"); import video as V
m = V.movimiento_de(sys.argv[1]); assert len(m) >= 10 and max(m) < V.QUIETUD_UMBRAL, m
t = V.ventanas_quietas(m); assert t and t[0][1] >= 2.0, t
assert V.ventanas_quietas([0.0] * 20) == [(0.25, 4.75)] and V.ventanas_quietas([0.0, 0.0, 1.0] * 10) == []
q = json.load(open("sesiones/_fixture_video/trabajo/revision/quietud.json"))
assert q["umbral"] == V.QUIETUD_UMBRAL and all(not e["quieto"] for e in q["escenas"].values()), {n: e["quieto"] for n, e in q["escenas"].items() if e["quieto"]}
assert all(len(e["movimiento"]) > 4 for e in q["escenas"].values())
PY' _ "$TMP"
  paso "V15 primer cuadro: un fondo vacío con el grano de la portada da 0 % dibujado (9:16 y 4:5); el gancho del fixture pasa el mínimo" bash -c '
set -e; Q="$1/v15"; rm -rf "$Q"; mkdir -p "$Q"
# la franja sin subtítulos de la portada (y 1385–1475) repetida hasta llenar el cuadro: solo fondo y grano
ffmpeg -y -v error -i sesiones/_fixture_video/salida/portada.png -vf "crop=1080:90:0:1385,loop=loop=21:size=1:start=0,tile=1x22,crop=1080:1920:0:0" -frames:v 1 "$Q/vacio.png"
for f in "1080:1920 vacio" "1080:1350 vacio_4x5"; do set -- $f
  ffmpeg -y -v error -loop 1 -framerate 10 -i "$Q/vacio.png" -t 1 -vf "crop=$1:0:0" -c:v libx264 -pix_fmt yuv420p -crf 16 -preset medium "$Q/$2.mp4"; done
python3 - "$Q" <<PY
import sys; sys.path.insert(0, "scripts"); import video as V
Q = sys.argv[1]
assert V.llenado_primer_cuadro(Q + "/vacio.mp4") == 0 and V.llenado_primer_cuadro(Q + "/vacio_4x5.mp4", f45=True) == 0, "el grano cuenta como dibujo"
assert V.llenado_primer_cuadro("sesiones/_fixture_video/trabajo/clips/e1.mp4") >= V.PRIMER_CUADRO_MIN
PY' _ "$TMP"
  paso "grabar --paralelo 1 da los mismos cuadros que la grabación en paralelo del fixture (framemd5 de e1 y e2)" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; P="$1/paralelo"; rm -rf "$P"; cp -R "$T" "$P"; rm -f "$P"/clips/*.mp4
python3 scripts/video.py grabar "$P" --fps 10 --solo 1,2 --paralelo 1 > /dev/null
for n in 1 2; do a=$(ffmpeg -v error -i "$T/clips/e$n.mp4" -f framemd5 - | grep -v "^#"); b=$(ffmpeg -v error -i "$P/clips/e$n.mp4" -f framemd5 - | grep -v "^#"); [[ -n "$a" && "$a" == "$b" ]] || { echo "e$n difiere entre serie y paralelo"; exit 1; }; done' _ "$TMP"
  paso "portadas limpias: sin subtítulos ni barra (franja lisa en y 1385–1475 tras desenfocar: el grano no cuenta), portada_texto.png de 1080×1920 y las alternativas" bash -c '
set -e; S=sesiones/_fixture_video/salida
for f in portada.png portada_texto.png portada_cierre.png portada_giro.png; do test -s "$S/$f" || { echo "falta $f"; exit 1; }; done
[[ "$(ffprobe -v error -show_entries stream=width,height -of csv=p=0 "$S/portada_texto.png")" == "1080,1920" ]]
# el grano fijo de Noche da 17–20 niveles de luma en la franja vacía; tras boxblur=12, 1–2; un subtítulo, 70 o más
for f in portada.png portada_cierre.png; do
  r=$(ffmpeg -v error -i "$S/$f" -vf "crop=1080:90:0:1385,boxblur=12:1,signalstats,metadata=print:file=-" -f null - 2>/dev/null | grep -o "YM[AI][XN]=[0-9.]*" | tr "\n" " ")
  python3 -c "import re,sys; d=dict(x.split(\"=\") for x in sys.argv[1].split()); assert float(d[\"YMAX\"]) - float(d[\"YMIN\"]) < 6, (sys.argv[2], d)" "$r" "$f"
done'
  paso "transiciones: el fixture usa el catálogo (smoothleft en E2, fade dentro de una secuencia de voz y en el cierre); cada una encadena dos clips; una ajena → V8" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; X="$1/xfade"; rm -rf "$X"; mkdir -p "$X"
python3 - "$T" "$X" <<PY
import json, os, subprocess, sys
sys.path.insert(0, "scripts"); import video as V
T, X = sys.argv[1:3]
E = json.load(open(T + "/escenas.json"))["escenas"]
tr = {e["n"]: e.get("transicion") for e in E}
assert tr[1] is None and tr[2] == "smoothleft", tr
assert tr[next(e["n"] for e in E if e.get("tipo") == "definicion")] == "fade", tr   # va de corrido tras el ranking (secuencia)
assert tr[E[-1]["n"]] == "fade", tr
assert all(t in V.TRANSICIONES.values() for n, t in tr.items() if n != 1), tr
for t in sorted(set(V.TRANSICIONES.values())):
    out = os.path.join(X, t + ".mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", T + "/clips/e1.mp4", "-i", T + "/clips/e2.mp4", "-filter_complex",
                    "[0:v][1:v]xfade=transition=%s:duration=0.3:offset=1.0" % t, "-frames:v", "20", out], check=True)
    assert os.path.getsize(out) > 0, t
PY
cp -R "$T" "$X/trabajo"; python3 -c "
import json, sys; p=sys.argv[1]; E=json.load(open(p)); E[\"escenas\"][1][\"transicion\"]=\"nada\"; json.dump(E, open(p, \"w\"))" "$X/trabajo/escenas.json"
! python3 scripts/video.py montar "$X/trabajo" --sin-bucle > "$X/montar.out" 2>&1; grep -q "V8 E2: transición «nada»" "$X/montar.out"' _ "$TMP"
  paso "icono (una copia: el golpe lleva «droplets»): escenas.json lo lleva solo ahí y el cuadro de E4 a 1.5 s lo dibuja sobre la cifra (franja desenfocada: el grano no cuenta)" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; C="$1/video_icono"; rm -rf "$C"; cp -R "$T" "$C"; rm -f "$C"/clips/*.mp4
python3 -c "
import json, sys; p = sys.argv[1]; g = json.load(open(p))
assert g[\"escenas\"][3][\"tipo\"] == \"golpe\" and not g[\"escenas\"][0].get(\"icono\"), g[\"escenas\"][3][\"tipo\"]
g[\"escenas\"][3][\"icono\"] = \"droplets\"
json.dump(g, open(p, \"w\"), ensure_ascii=False)" "$C/guion.json"
rehacer_narracion "$C/guion.json"; python3 scripts/video.py guion "$C" --check > /dev/null; python3 scripts/video.py voz-falsa "$C" > /dev/null; python3 scripts/video.py tiempos "$C" > /dev/null
python3 -c "import json,sys; E=json.load(open(sys.argv[1]))[\"escenas\"]; assert [e.get(\"icono\") for e in E] == [None, None, None, \"droplets\", None, None, None], [e.get(\"icono\") for e in E]" "$C/escenas.json"
python3 scripts/video.py grabar "$C" --solo 4 --fps 10 > /dev/null
ffmpeg -y -v error -ss 1.5 -i "$C/clips/e4.mp4" -frames:v 1 "$C/e4.png"
# el icono va arriba de la cifra (x 85–285, y 560–710); a su derecha (x 600–800) queda fondo con grano. Tras boxblur=2 el
# grano da ~3 niveles de luma y el trazo crema del icono ~170
rango() { ffmpeg -v error -i "$C/e4.png" -vf "crop=200:150:$1:560,boxblur=2:1,signalstats,metadata=print:file=-" -f null - 2>/dev/null | grep -o "YM[AI][XN]=[0-9.]*" | tr "\n" " "; }
python3 -c "
import sys; r = lambda s: (lambda d: float(d[\"YMAX\"]) - float(d[\"YMIN\"]))(dict(x.split(\"=\") for x in s.split()))
assert r(sys.argv[1]) > 40, (\"icono\", sys.argv[1]); assert r(sys.argv[2]) < 10, (\"fondo\", sys.argv[2])" "$(rango 85)" "$(rango 600)"' _ "$TMP"
  paso "ranking del fixture (T3 barras-h, top 4): los puestos dichos entran al decirlos, los demás antes y en orden; sfx resolucion en el primero" bash -c '
python3 - <<PY
import json
E = json.load(open("sesiones/_fixture_video/trabajo/escenas.json"))["escenas"]
e = next(x for x in E if x["tipo"] == "ranking")
it = e["T"]["items"]; assert [x["puesto"] for x in it] == [1, 2, 3, 4] and it[0]["nombre"] == "México" and it[0]["hi"], it
dichos = [x for x in it if x["dicho"]]; assert len(dichos) == 2 and all(abs(x["start"] - (x["dicho"][0] - 0.1)) < 0.01 for x in dichos), it
sin = sorted((x for x in it if not x["dicho"]), key=lambda x: -x["puesto"]); assert sin[0]["start"] < sin[1]["start"] < min(x["start"] for x in dichos), it
assert e["transicion"] in ("circleopen", "slideup") and sum(1 for x in e["eventos"] if x["tipo"] == "item") == 4
assert any(x["id"] == "resolucion" and abs(x["t"] - it[0]["start"]) < 0.01 for x in e["sfx"]), e["sfx"]
PY'
  paso "escena tiempo (T2 antes-despues en una copia): dos puntos con sus tiempos, marcador, píldora ×1.77 y grabación" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; C="$1/video_tiempo"; rm -rf "$C"; cp -R "$T" "$C"; rm -f "$C"/clips/*.mp4
python3 -c "
import json, sys; p = sys.argv[1]; g = json.load(open(p)); e = g[\"escenas\"][2]; assert e[\"tuit\"] == 2; e[\"tipo\"] = \"tiempo\"; json.dump(g, open(p, \"w\"), ensure_ascii=False)" "$C/guion.json"
rehacer_narracion "$C/guion.json"; python3 scripts/video.py guion "$C" --check > /dev/null; python3 scripts/video.py voz-falsa "$C" > /dev/null; python3 scripts/video.py tiempos "$C" > /dev/null
python3 - "$C" <<PY
import json, sys
e = json.load(open(sys.argv[1] + "/escenas.json"))["escenas"][2]; T = e["T"]
assert e["tipo"] == "tiempo" and [p["etiqueta"] for p in T["puntos"]] == ["Enero", "Septiembre"] and T["puntos"][1]["hi"], T
assert T["puntos"][0]["start"] < T["puntos"][1]["start"] < T["pildora"]["start"] and T["pildora"]["texto"] == "×1.77", T
assert T["marcador"][0] < T["marcador"][1] and e["transicion"] in ("circleopen", "slideup"), T
PY
python3 scripts/video.py grabar "$C" --solo 3 --fps 10 > /dev/null; test -s "$C/clips/e3.mp4"' _ "$TMP"
  paso "escena escala (una copia: el golpe pasa a «77 de cada 100» con calculo): V2 exime K y N, tiempos (figuras, destacadas, etiqueta) y grabación" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; C="$1/video_escala"; rm -rf "$C"; cp -R "$T" "$C"; rm -f "$C"/clips/*.mp4
python3 -c "
import json, sys; p = sys.argv[1]; g = json.load(open(p))
g[\"escenas\"][3] = {\"tipo\": \"escala\", \"enlace\": \"por_eso\", \"de_cada\": [77, 100], \"etiqueta\": \"quetzales más por cada 100 de enero\", \"calculo\": \"(pre-c03/pre-c02-1)*100\", \"golpe\": \"77 de cada 100\", \"texto\": \"Así que el salto es brutal: pagas 77 de cada 100 más que en enero.\"}
json.dump(g, open(p, \"w\"), ensure_ascii=False)" "$C/guion.json"
rehacer_narracion "$C/guion.json"; python3 scripts/video.py guion "$C" --check > /dev/null; python3 scripts/video.py voz-falsa "$C" > /dev/null; python3 scripts/video.py tiempos "$C" > /dev/null
python3 - "$C" <<PY
import json, sys
e = json.load(open(sys.argv[1] + "/escenas.json"))["escenas"][3]; T = e["T"]
assert e["tipo"] == "escala" and (T["k"], T["n"]) == (77, 100) and T["figuras"] < T["destacadas"] < T["etiqueta_t"], T
assert [x["tipo"] for x in e["eventos"] if x["tipo"] in ("figuras", "destacadas", "etiqueta")] == ["figuras", "destacadas", "etiqueta"]
assert sum(1 for x in e["sfx"] if x["id"] == "tic") >= 10 and any(x["id"] == "resolucion" for x in e["sfx"]), e["sfx"]
PY
python3 scripts/video.py grabar "$C" --solo 4 --fps 10 > /dev/null; test -s "$C/clips/e4.mp4"' _ "$TMP"
  paso "gancho en 3 s: cifra desde 0.15, línea en sincronía con la voz (palabras dichas ancladas, o al entrar la línea si la voz ya las dijo; el resto como frase, antes del fin de la 1.ª oración), evento promesa en su escena" bash -c '
python3 - <<PY
import json
E = json.load(open("sesiones/_fixture_video/trabajo/escenas.json"))["escenas"]; e = E[0]; T = e["T"]
assert T["pant"]["desde"] == 0.15 and T["pant"]["pulso"], T["pant"]
norm = lambda s: s.lower().strip(".,;:?¿!¡")
voz = [(norm(w["text"]), w["start"]) for w in e["palabras"]]
dichas = [w for w in T["linea"] if w.get("dicha")]; assert dichas, T["linea"]
# cada palabra dicha entra 0.05 s antes de que la voz la diga, nunca antes de que entre la línea (1.2 s); si la voz ya la
# dijo antes, se ancla ahí y solo el espacio mínimo de 0.12 s entre palabras la corre (alinear_linea)
L = T["linea"]
for i, w in enumerate(L):
    if not w.get("dicha"): continue
    prev = L[i - 1]["start"] + 0.12 if i else 0
    assert any(txt == norm(w["text"]) and (abs(w["start"] - max(1.2, t - 0.05)) < 0.02 or (w["start"] > max(1.2, t - 0.05) and abs(w["start"] - prev) < 0.02)) for txt, t in voz), (w, voz)
fin1 = next(w["end"] for w in e["palabras"] if w["text"].endswith((".", "?", "!")))
assert all(w["start"] <= max(fin1, max(x["start"] for x in dichas)) + 0.12 * len(T["linea"]) for w in T["linea"]), (T["linea"], fin1)
starts = [w["start"] for w in T["linea"]]; assert starts == sorted(starts) and all(b - a >= 0.119 for a, b in zip(starts, starts[1:])), starts
ev = [x["tipo"] for x in e["eventos"]]; assert "linea_fin" in ev, ev
# la promesa va en la escena que dice el guion (promesa.en): evento y «tic» en su primera palabra
G = json.load(open("sesiones/_fixture_video/guion.json")); P = G["promesa"]; ep = E[P["en"] - 1]
vp = [(norm(w["text"]), w["start"]) for w in ep["palabras"]]
tp = next(x["t"] for x in ep["eventos"] if x["tipo"] == "promesa"); assert any(txt == norm(P["texto"].split()[0]) and abs(tp - t) < 0.01 for txt, t in vp), (tp, vp)
assert any(x["id"] == "tic" and abs(x["t"] - tp) < 0.01 for x in ep["sfx"]), ep["sfx"]
g = E[3]; assert g["T"]["linea"][-1]["start"] <= g["fin_voz"], g["T"]["linea"]
PY'
  paso "subtítulos del gancho (tu · llenado): ocultos antes de la cifra (0.3 s) y mientras repiten la pantalla («26 quetzales»); visibles en «En septiembre, Guatemala pagó» (franja desenfocada: el grano no cuenta)" bash -c '
set -e; T=sesiones/_fixture_video/trabajo
dicha() { python3 -c "import json,sys; e=json.load(open(sys.argv[1]))[\"escenas\"][0]; print(next(w[\"start\"] for w in e[\"palabras\"] if w[\"text\"].strip(\".,\")==sys.argv[2]) + 0.25)" "$T/escenas.json" "$1"; }
trep=$(dicha 26); tvis=$(dicha septiembre)
# el grano fijo de Noche da 17–20 niveles de luma en la franja vacía; tras boxblur=12, 1–2; un subtítulo, 70 o más
franja() { ffmpeg -v error -ss "$1" -i "$T/clips/e1.mp4" -frames:v 1 -vf "crop=1080:90:0:1385,boxblur=12:1,signalstats,metadata=print:file=-" -f null - 2>/dev/null | grep -o "YM[AI][XN]=[0-9.]*" | tr "\n" " "; }
lisa() { python3 -c "import sys; d=dict(x.split(\"=\") for x in sys.argv[1].split()); r=float(d[\"YMAX\"]) - float(d[\"YMIN\"]); assert (r < 6) == (sys.argv[2] == \"si\"), (sys.argv[3], d)" "$1" "$2" "$3"; }
lisa "$(franja 0.3)" si "subtítulo antes de que aterrice la cifra"
lisa "$(franja $trep)" si "subtítulo que repite la pantalla (26 quetzales)"
lisa "$(franja $tvis)" no "falta el subtítulo de «En septiembre, Guatemala pagó»"' _ "$TMP"
  paso "animadores de las 16 plantillas restantes (divergente … treemap y area-apilada … piramide): V7 y cuadro intermedio distinto del final" bash -c '
  set -e; test -d templates/.galeria || { echo "sin templates/.galeria: corre make catalogo"; exit 1; }; M="$1/medio"; rm -rf "$M"; mkdir -p "$M"
  N=(); for t in divergente apilada embudo bullet agrupadas treemap area-apilada calor cascada combinado dispersion hemiciclo linea-tiempo multiples pictograma piramide; do if [ -f "templates/.galeria/estres-$t.html" ]; then N+=("estres-$t"); else N+=("$t"); fi; done
  F=(); for n in "${N[@]}"; do F+=("templates/.galeria/$n.html"); done
  node scripts/video_animar.js --check "${F[@]}" --medio "$M" >/dev/null
  for n in "${N[@]}"; do t="$n"
    S=$(ffmpeg -i "$M/.galeria-$t.medio.png" -i "$M/.galeria-$t.final.png" -lavfi ssim -f null - 2>&1 | grep -o "All:[0-9.]*" | cut -d: -f2)
    python3 -c "import sys; s=float(sys.argv[1]); assert s < 0.995, (sys.argv[2], \"no anima\", s)" "$S" "$t"
  done' _ "$TMP"
  paso "adivina: tiempos (pregunta, opciones, revelado tras la última cifra) y grabación de la escena" bash -c '
set -e; d="$1/video_adivina_t"; rm -rf "$d"; cp -R sesiones/_fixture_video/trabajo "$d"; rm -rf "$d/clips" "$d/salida"
python3 - "$d/guion.json" "$2" <<PY
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); G["escenas"][3] = json.loads(sys.argv[2])
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$d/guion.json"; python3 scripts/video.py guion "$d" --check >/dev/null && python3 scripts/video.py voz-falsa "$d" >/dev/null && python3 scripts/video.py tiempos "$d" >/dev/null
python3 - "$d/escenas.json" <<PY
import json, sys
e = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"][3]
T, tipos = e["T"], [x["tipo"] for x in e["eventos"]]
assert e["tipo"] == "adivina" and len(T["opciones"]) == 3 and T["revelado"] > T["opciones"][-1]["start"] + 0.5 and T["revelado"] < e["dur"], T
assert tipos.count("opcion") == 3 and "revelado" in tipos and "pregunta" in tipos, tipos
assert any(s["id"] == "resolucion" for s in e["sfx"]), e["sfx"]
assert T["pausa"] is not None and T["opciones"][-1]["start"] < T["pausa"] < T["revelado"] and "pausa" in tipos, T
PY
python3 scripts/video.py grabar "$d" --fps 10 --solo 4 >/dev/null
test -s "$d/clips/e4.mp4"' _ "$TMP" "$ADIVINA"
  paso "explica: tiempos (cada paso al decirlo, en orden), circleopen y grabación de la animación de la biblioteca" bash -c '
set -e; d="$1/video_explica_t"; rm -rf "$d"; cp -R sesiones/_fixture_video/trabajo "$d"; rm -rf "$d/clips" "$d/salida"
python3 - "$d/guion.json" "$2" <<PY
import json, sys
G = json.load(open(sys.argv[1], encoding="utf-8")); G["escenas"][3] = json.loads(sys.argv[2])
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$d/guion.json"; python3 scripts/video.py guion "$d" --check >/dev/null && python3 scripts/video.py voz-falsa "$d" >/dev/null && python3 scripts/video.py tiempos "$d" >/dev/null
python3 - "$d/escenas.json" <<PY
import json, sys
e = json.load(open(sys.argv[1], encoding="utf-8"))["escenas"][3]
ps = [p["start"] for p in e["T"]["pasos"]]
assert e["tipo"] == "explica" and e["animacion"] == "cadena" and e["transicion"] == "circleopen", (e["animacion"], e["transicion"])
assert len(ps) == 3 and e["T"]["ini"] < ps[0] < ps[1] < ps[2] < e["dur"], e["T"]
assert [x["tipo"] for x in e["eventos"]].count("paso") == 3 and e["arriba"], e["eventos"]
PY
python3 scripts/video.py grabar "$d" --fps 10 --solo 4 >/dev/null
test -s "$d/clips/e4.mp4"' _ "$TMP" "$EXPLICA"
  paso "animaciones.py --check cadena: lint, meta, dos grabaciones iguales, 4:5, sin quietud y hojas de contacto" bash -c '
python3 scripts/animaciones.py --check cadena --salida "$1/anim_cadena" >/dev/null && test -s "$1/anim_cadena/contacto.png" && test -s "$1/anim_cadena/contacto_4x5.png"' _ "$TMP"
  paso "make video-fixture-4x5 (formato 1080×1350 para el feed: clips_4x5, video_4x5.mp4, contacto_4x5.png, entrega)" bash -c 'make video-fixture-4x5 >/dev/null && ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_video/salida/video_4x5.mp4 | grep -q "video,1080,1350" && test -s sesiones/_fixture_video/salida/contacto_4x5.png && test -s sesiones/_fixture_video/trabajo/revision/linea_tiempo_4x5.png'
  paso "V13 zona segura: el fixture (9:16 y 4:5), una escala de 100 figuras con etiqueta de dos líneas y un ranking de 6 caben; con el fin de zona en y 850 el gate falla (exit 3) y escribe zona.json" bash -c '
set -e; W="$1/zona"; rm -rf "$W"; mkdir -p "$W"; cp sesiones/_fixture_video/trabajo/escenas.json "$W/"
python3 - "$W/escenas.json" <<PY
import json, sys, copy
p = sys.argv[1]; d = json.load(open(p)); E = d["escenas"]
base = next(e for e in E if e.get("tipo") == "golpe")
esc = copy.deepcopy(base); esc.update({"n": 90, "tipo": "escala", "tuit": None, "plantilla": "escala",
  "T": {"k": 63, "n": 100, "etiqueta": "muertos en tránsito iban en moto (2026)", "ini": 0.6, "figuras": 1.0, "destacadas": 2.0, "etiqueta_t": 3.0}})
rk = copy.deepcopy(next(e for e in E if e.get("tipo") == "ranking")); rk["n"] = 91
items = rk["T"]["items"]
while len(items) < 6:
    x = copy.deepcopy(items[-1]); x["puesto"] = len(items) + 1; x["hi"] = False; items.append(x)
d["escenas"] = [esc, rk]; json.dump(d, open(p, "w"), ensure_ascii=False)
PY
H=sesiones/_fixture/salida
node scripts/video_grabar.js --dir "$W" --hilo "$H" --zona >/dev/null
node scripts/video_grabar.js --dir "$W" --hilo "$H" --zona --formato 4:5 >/dev/null
node scripts/video_grabar.js --dir sesiones/_fixture_video/trabajo --hilo "$H" --zona >/dev/null
set +e; node scripts/video_grabar.js --dir "$W" --hilo "$H" --zona --zona-fin 850 2>"$W/err"; rc=$?; set -e
test "$rc" = 3 && grep -q "FALLA V13 e90 (escala" "$W/err" && grep -q "baja de y 850" "$W/err" && test -s "$W/revision/zona.json"' _ "$TMP"
  paso "entrega para cuatro plataformas: caption.md con TikTok, Instagram, Facebook y Shorts; sin video_4x5.mp4, entregar falla" bash -c '
set -e; C=sesiones/_fixture_video/salida/caption.md
for x in "## TikTok" "## Instagram Reels" "## Facebook Reels" "## YouTube Shorts" "#Shorts"; do grep -q "$x" "$C"; done
W="$1/sin45"; rm -rf "$W"; cp -R sesiones/_fixture_video/trabajo "$W"; rm -f "$W/salida/video_4x5.mp4"
! python3 scripts/video.py entregar "$W" --salida "$1/sin45_salida" 2>/dev/null' _ "$TMP"
  paso "video gate: faltan captions de Instagram y Shorts → V5" video_neg "V5 falta caption.instagram" 'del G["caption"]["instagram"]'
  paso "video gate: título de Shorts de más de 100 caracteres → V5" video_neg "V5 caption.shorts: la primera línea" 'G["caption"]["shorts"] = "x" * 120 + "\\n#Shorts"'
  paso "escena mapa: tarjeta de mapa a pantalla completa (gate, tiempos, grabación con h.js y geometria.js)" bash -c '
set -e; H="$1/hilo_mapa"; W="$1/video_mapa"; rm -rf "$H" "$W"; cp -R sesiones/_fixture/salida "$H"; cp templates/.galeria/mapa.html "$H/tuit_9.html"
python3 - "$H/hilo.json" <<PY
import json, sys
h = json.load(open(sys.argv[1], encoding="utf-8"))
h["tuits"].append({"n": 9, "beat": "impacto", "texto": "", "caracteres": 0, "alt_text": "Mapa de prueba", "imagen": "tuit_9.png", "plantilla": "mapa", "fuente": "Prueba", "cifra_ids": []})
json.dump(h, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
python3 scripts/video.py preparar "$H" --duracion prueba --trabajo "$W" --permitir-borrador >/dev/null
python3 - "$W/guion.json" <<PY
import json, sys
G = json.load(open("sesiones/_fixture_video/guion.json", encoding="utf-8"))
G["escenas"][4] = {"tipo": "mapa", "tuit": 9, "acto": 3, "enlace": "pero", "golpe": "El mapa lo dice solo", "texto": "Pero el mapa lo dice solo: el norte y el altiplano concentran la pobreza."}
json.dump(G, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
PY
rehacer_narracion "$W/guion.json"; python3 scripts/video.py guion "$W" --check >/dev/null && python3 scripts/video.py voz-falsa "$W" >/dev/null && python3 scripts/video.py tiempos "$W" >/dev/null
python3 -c "import json,sys; e=json.load(open(sys.argv[1]))[\"escenas\"][4]; assert e[\"tipo\"] == \"mapa\" and e[\"tuit\"] == 9 and e[\"arriba\"] and any(x[\"tipo\"] == \"entra\" for x in e[\"eventos\"]), e" "$W/escenas.json"
python3 scripts/video.py grabar "$W" --fps 10 --solo 5 >/dev/null
test -s "$W/clips/e5.mp4"
ffmpeg -loglevel error -y -ss 0.4 -i "$W/clips/e5.mp4" -frames:v 1 -update 1 "$W/a.png"; ffmpeg -loglevel error -y -ss 4.0 -i "$W/clips/e5.mp4" -frames:v 1 -update 1 "$W/b.png"
S=$(ffmpeg -i "$W/a.png" -i "$W/b.png" -lavfi ssim -f null - 2>&1 | grep -o "All:[0-9.]*" | cut -d: -f2)
python3 -c "import sys; s=float(sys.argv[1]); assert s < 0.95, (\"el mapa no se dibujó\", s)" "$S"' _ "$TMP"
  paso "tiempos: un año dicho que la tarjeta tiene en su eje late (evento anio); uno ajeno a la tarjeta, no" bash -c '
set -e; T=sesiones/_fixture_video/trabajo; D="$1/video_anio"; rm -rf "$D"; cp -R "$T" "$D"
anios() { python3 - "$D" "$1" <<PY
import json, sys, os
D, a = sys.argv[1], json.loads(sys.argv[2])
V = json.load(open(os.path.join(D, "video.json"), encoding="utf-8"))
for t in V["tarjetas"]: t["anios"] = a if t["n"] == 1 else []
json.dump(V, open(os.path.join(D, "video.json"), "w", encoding="utf-8"), ensure_ascii=False)
PY
}
python3 - "$D" <<PY
import json, sys, os
D = sys.argv[1]
G = json.load(open(os.path.join(D, "guion.json"), encoding="utf-8"))
G["escenas"][1]["texto"] = G["escenas"][1]["texto"].replace("dólares en enero", "dólares en enero de 2026")
json.dump(G, open(os.path.join(D, "guion.json"), "w", encoding="utf-8"), ensure_ascii=False)
PY
anios "[\"2026\"]"
rehacer_narracion "$D/guion.json"; python3 scripts/video.py guion "$D" --check >/dev/null && python3 scripts/video.py voz-falsa "$D" >/dev/null && python3 scripts/video.py tiempos "$D" >/dev/null
python3 -c "import json,sys; E=json.load(open(sys.argv[1]))[\"escenas\"]; e=E[1]; assert e[\"T\"][\"anios\"].get(\"2026\") and any(x[\"tipo\"] == \"anio\" for x in e[\"eventos\"]), e[\"T\"]; assert not any(x[\"tipo\"] == \"anio\" for x in E[2][\"eventos\"])" "$D/escenas.json"
anios "[]"
python3 scripts/video.py tiempos "$D" >/dev/null
python3 -c "import json,sys; E=json.load(open(sys.argv[1]))[\"escenas\"]; assert not E[1][\"T\"][\"anios\"] and not any(x[\"tipo\"] == \"anio\" for x in E[1][\"eventos\"])" "$D/escenas.json"' _ "$TMP"
fi

echo "== /noticias (gates N1–N8 sobre la maqueta; sin web ni créditos)"
NT="$TMP/noticias"
paso "noticias.py preparar --fixture + guion --check (maqueta)" bash -c "python3 scripts/noticias.py preparar --fecha 2026-10-23 --trabajo '$NT' --fixture >/dev/null && python3 scripts/noticias.py guion '$NT' --check >/dev/null"
paso "paleta del día: dos días seguidos nunca repiten" python3 -c 'import sys; sys.path.insert(0,"scripts"); import noticias as N, datetime as D; d=D.date(2026,1,1); ps=[N.paleta_del_dia((d+D.timedelta(k)).isoformat()) for k in range(30)]; assert all(a!=b for a,b in zip(ps,ps[1:])) and set(ps)==set(N.PALETAS_CICLO), ps'
# neg_noticias "nombre" "GATE" "python que muta g (guion.json) o b (noticias.json)"
neg_noticias() {
  N=$((N+1)); local nombre="$1" gate="$2" mut="$3" S; S="$(mktemp -d "$TMP/negn.XXXXXX")"
  cp -R "$NT/." "$S/"
  python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+"/guion.json")); b=json.load(open(d+"/noticias.json")); exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False); json.dump(b, open(d+"/noticias.json","w"), ensure_ascii=False)' "$S" "$mut"
  python3 scripts/noticias.py guion "$S" --check >"$TMP/negn.out" 2>&1; local rc=$?
  if [[ $rc -eq 1 ]] && grep -q "$gate" "$TMP/negn.out"; then printf 'OK     %s → %s\n' "$nombre" "$gate"
  else FALLOS=$((FALLOS+1)); printf 'FALLO  %s: esperaba exit 1 con %s (exit %s)\n' "$nombre" "$gate" "$rc"; sed 's/^/       /' "$TMP/negn.out" | tail -6; fi
}
neg_noticias "cifra en la voz sin cita" "N4" 'g["noticias"][1]["texto"] = g["noticias"][1]["texto"].replace("Q6,200 millones", "Q9,900 millones")'
neg_noticias "«culpable» sin sentencia" "N4" 'g["noticias"][0]["texto"] = g["noticias"][0]["texto"].replace("según Conred", "y el alcalde es culpable, según Conred")'
neg_noticias "guion de más de 70 s" "N5" 'g["noticias"].insert(3, dict(g["noticias"][1], id="n3")); g["noticias"][3]["breve"] = False; g["noticias"] = g["noticias"][:4]; [x.update(texto=g["noticias"][1]["texto"]) for x in g["noticias"][:3]]'
neg_noticias "cierre sin frase final" "N8" 'g["cierre"]["final"] = ""'
neg_noticias "noticia sin foto" "N7" 'g["noticias"][2]["foto"] = None'
neg_noticias "foto de referencia con crédito «Foto:»" "N7" 'g["noticias"][2]["foto"]["credito"] = "Foto: ejemplo"'
neg_noticias "noticia no confirmada" "N3" 'b["noticias"][2]["estado"] = "no_confirmada"'
neg_noticias "en desarrollo sin atribuir" "N2" 'b["noticias"][2]["estado"] = "en_desarrollo"; g["noticias"][2]["texto"] = g["noticias"][2]["texto"].replace(", informó el Ministerio de Salud", " en todo el país")'
neg_noticias "una sola sección" "N3" '[x.update(seccion="Clima") for x in g["noticias"]]'
verificacion_negativa() {
  local S="$TMP/vneg"; rm -rf "$S"; cp -R "$NT" "$S"
  printf 'El Ministerio de Salud informó que los casos de dengue bajan 35 por ciento frente a 2025 en todo el país, según su boletín semanal.\n' > "$S/nota.txt"
  python3 - "$S" <<'EOF2'
import json, sys
S = sys.argv[1]
base = {"id": "eco-1", "seccion": "Salud", "titular": "Dengue baja", "resumen": "x", "depto": "Guatemala", "icono": "heart-pulse",
        "hechos": [{"texto": "baja", "cita": "los casos de dengue bajan 35 por ciento", "url": "https://www.mspas.gob.gt/a"}], "cifras": [], "foto": {"archivo": "fotos/eco-1.jpg", "credito": "Foto: Soy502", "origen": "medio"}}
una = dict(base, estado="confirmada", fuentes=[{"medio": "Soy502", "tipo": "medio", "url": "https://www.soy502.com/a", "fecha": "2026-10-23", "archivo": S + "/nota.txt", "cita": "los casos de dengue bajan 35 por ciento frente a 2025"}])
json.dump(una, open(S + "/verificacion_eco-1.json", "w"))
EOF2
  mkdir -p "$S/fotos" && : > "$S/fotos/eco-1.jpg"
  python3 scripts/noticias.py verificacion "$S" --check --id eco-1 | grep -q "N2 eco-1: confirmada pide 2 fuentes" || return 1
  # con una oficial además del medio, pasa
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_eco-1.json")); v["fuentes"].append(dict(v["fuentes"][0], medio="MSPAS", tipo="oficial", url="https://www.mspas.gob.gt/a")); json.dump(v, open(S+"/verificacion_eco-1.json","w"))' "$S"
  python3 scripts/noticias.py verificacion "$S" --check --id eco-1 >/dev/null || return 1
  # una cita que no está en el texto guardado falla
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_eco-1.json")); v["hechos"][0]["cita"]="los casos de dengue suben"; json.dump(v, open(S+"/verificacion_eco-1.json","w"))' "$S"
  python3 scripts/noticias.py verificacion "$S" --check --id eco-1 | grep -q "no está en el texto" || return 1
  # una noticia publicable sin foto falla: va una de referencia
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_eco-1.json")); v["foto"]=None; json.dump(v, open(S+"/verificacion_eco-1.json","w"))' "$S"
  python3 scripts/noticias.py verificacion "$S" --check --id eco-1 | grep -q "N7 eco-1: cada noticia lleva foto" || return 1
}
paso "noticias.py verificacion --check: una sola fuente no confirma; medio + oficial sí; cita fuera del texto falla (N2); sin foto falla (N7)" verificacion_negativa
paso "música del día: las 2 pistas de la paleta se alternan cada vez que vuelve el ciclo" python3 -c 'import sys; sys.path.insert(0,"scripts"); import noticias as N, datetime as D; d=D.date(2026,10,23); a=N.musica_del_dia(N.paleta_del_dia(d.isoformat()), d.isoformat())["id"]; e=d+D.timedelta(8); b=N.musica_del_dia(N.paleta_del_dia(e.isoformat()), e.isoformat())["id"]; assert N.paleta_del_dia(d.isoformat())==N.paleta_del_dia(e.isoformat()) and a!=b, (a,b)'
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make noticias-fixture y entregar (RAPIDO=1)"; else
  paso "make noticias-fixture (maqueta 9:16 y 4:5, V13, V8)" bash -c 'make noticias-fixture >/dev/null && ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_noticias/trabajo/salida/video_4x5.mp4 | grep -q "video,1080,1350"'
  entregar_noticias() {
    local T=sesiones/_fixture_noticias/trabajo D="$TMP/entrega_noticias"
    python3 scripts/noticias.py entregar "$T" 2>&1 | grep -q "creditos.json" || { echo "entregar sin voz real debía negarse"; return 1; }
    python3 scripts/noticias.py entregar "$T" --salida "$D" >/dev/null || return 1
    for f in video.mp4 video_4x5.mp4 caption.md subtitulos.srt guion.json fuentes.md portada.png contacto.png; do [[ -s "$D/$f" ]] || { echo "falta $f"; return 1; }; done
    [[ ! -d "$D/fotos" ]] || { echo "las fotos de terceros no se entregan"; return 1; }
    grep -q "https://conred.gob.gt/ejemplo" "$D/fuentes.md" || { echo "fuentes.md sin las urls"; return 1; }
    python3 scripts/memoria.py --noticias "$D" --dry-run | grep -q "4 noticias"
  }
  paso "noticias.py entregar (sin voz real se niega; --salida: 9:16, 4:5, caption, fuentes.md, sin fotos) + memoria.py --noticias --dry-run" entregar_noticias
fi

echo "== /historia (gates H1–H8 sobre la maqueta; sin web ni créditos)"
HT="$TMP/historia"
paso "historia.py preparar --fixture + hechos --check + consolidar + ganchos --usar + guion --check (maqueta)" bash -c "python3 scripts/historia.py preparar 'La Espiga (maqueta)' --slug la-espiga-maqueta --trabajo '$HT' --fixture >/dev/null && python3 scripts/historia.py hechos '$HT' --check >/dev/null && python3 scripts/historia.py consolidar '$HT' >/dev/null && python3 scripts/historia.py ganchos '$HT' --usar >/dev/null && python3 scripts/historia.py guion '$HT' --check >/dev/null"
# neg_historia "nombre" "GATE" "python que muta g (guion.json)"
neg_historia() {
  local nombre="$1" gate="$2" mut="$3" S="$TMP/hneg"
  rm -rf "$S"; cp -R "$HT" "$S"; rm -f "$S/locucion.json"
  python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+"/guion.json")); e=g["escenas"]; exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False)' "$S" "$mut"
  python3 scripts/historia.py guion "$S" --check >"$TMP/negh.out" 2>&1; local rc=$?
  paso "historia.py guion --check rechaza: $nombre ($gate)" bash -c "[[ $rc -ne 0 ]] && grep -q 'FALLA $gate' '$TMP/negh.out' && [[ ! -s '$S/locucion.json' ]]"
}
# RN: rehace guion.narracion desde las voces (H15) en una mutación que debe seguir pasando el gate
RN='narr=[]
for a in (1,2,3):
    vs=[x["texto"] for i,x in enumerate(e,1) if (1 if i==1 else x.get("acto"))==a]
    if a==3: vs.append(g["cierre"]["texto"])
    narr.append({"acto":a,"texto":" ".join(vs)})
g["narracion"]=narr'
neg_historia "un año que no está en la cronología" "H4" 'e[3]["texto"] = e[3]["texto"].replace("1977", "1979")'
neg_historia "un número sin respaldo" "V2" 'e[4]["texto"] = e[4]["texto"].replace("4,500", "4,800")'
neg_historia "un hecho de parte (alegato en disputa) sin atribuir" "H4 escena 9: cuenta un hecho en disputa o de parte" 'e[8]["texto"] = e[8]["texto"].replace("su familia dice que fue en 2011", "fue en 2011")'
neg_historia "un hecho de una sola fuente sin la fuente en pantalla" "H4 escena 9: cuenta un hecho de una sola fuente" 'e[8].pop("fuente")'
neg_historia "una cita sin decir quién habla" "H4 escena 3: la voz no dice quién lo dijo" 'e[2]["texto"] = e[2]["texto"].replace("Marta Pérez, la fundadora, encendió ese horno en 1952 y abrió La Espiga. Años después, ya famosa en Xela, lo resumió así:", "Alguien lo resumió así:")'
neg_historia "«culpable» sin sentencia firme" "H3" 'e[6]["texto"] = e[6]["texto"].replace("la multa:", "la multa y el dueño fue culpable:")'
neg_historia "cuatro escenas seguidas del mismo tipo" "H8 escenas 4–7: 4 escenas foto seguidas" 'e[4:4] = [dict(e[3], giro=False) for _ in range(3)]'
neg_historia "actos fuera de orden" "H8 los actos van en orden" 'e[4]["acto"] = 3'
neg_historia "el acto 3 sin rótulo" "H8 el acto 3 empieza en la escena 8 sin rótulo" 'e[7].pop("rotulo")'
neg_historia "un rótulo en el gancho" "H8 escena 1: el rótulo va sobre una escena" 'e[0]["rotulo"] = {"anio": "1976", "titulo": "La carpa"}'
neg_historia "sin giro" "H8" 'e[5].pop("giro")'
neg_historia "el giro fuera del nudo (acto 2)" "H8 el giro (escena 5) va en el acto 2" 'e[5].pop("giro"); e[4]["giro"] = True'
neg_historia "más de 180 s" "V4" '[x.update(texto=x["texto"] + " " + x["texto"]) for x in e[1:] if x["tipo"] == "foto"]; [x.update(texto=x["texto"] + " Marta Pérez lo dijo así.") for x in e if x["tipo"] == "cita"]'
neg_historia "una cita que la voz no lee literal" "H4" 'e[2]["texto"] = e[2]["texto"].replace("Cada pan sale", "Todo pan sale")'
neg_historia "la misma foto en 3 escenas (gancho, 4 y 9)" "H7 la misma foto" 'e[8]["foto"] = "ori-f02"'
neg_historia "un retrato que no es de quien habla" "H7 escena 3: el retrato" 'e[2]["retrato"] = "ori-f01"'
neg_historia "el chip con un año anterior a la foto" "H7 escena 4: el chip" 'e[3]["fecha"] = "1952"'
neg_historia "20 escenas (más el cierre pasan de 20 nodos)" "H8 20 escenas" 'e[8:8] = [dict(e[7], giro=False) for _ in range(11)]'
neg_historia "una escena foto con icono en lugar de foto" "H7 escena 9: la escena foto lleva una foto" 'e[8].update(foto=None, icono="landmark")'
neg_historia "una escena que apunta a algo que no se dijo (esos 900 hornos)" "H11 escena 4" 'e[3]["texto"] = "Esos 900 hornos no volvieron. " + e[3]["texto"]'
neg_historia "«según» en el final del cierre" "H9" 'g["cierre"]["final"] = "Según la prensa, sus trabajadores aún encienden los dos hornos."; g["cierre"]["texto"] = g["cierre"]["texto"].rsplit(".", 2)[0] + ". " + g["cierre"]["final"]'
neg_historia "la promesa no dice qué revelación paga" "H14 promesa.revela" 'g["promesa"].pop("revela")'
neg_historia "la escena del pago no cuenta la revelación prometida" "H14 la escena 9" 'g["promesa"]["revela"] = 1'
neg_historia "un legado con el verbo en pasado" "F6 legado" 'g["cierre"].update(final="En Xela, sus trabajadores encendieron los dos hornos.", consecuencia={"quien": "trabajadores", "verbo": "encendieron"}); g["cierre"]["texto"] = g["cierre"]["texto"].rsplit(".", 2)[0] + ". " + g["cierre"]["final"]'
neg_historia "un legado sin gente (la marca como sujeto)" "F6 cierre.consecuencia.quien" 'g["cierre"].update(final="En Xela, La Espiga aún enciende los dos hornos.", consecuencia={"quien": "La Espiga", "verbo": "enciende"}); g["cierre"]["texto"] = g["cierre"]["texto"].rsplit(".", 2)[0] + ". " + g["cierre"]["final"]'
neg_historia "la narración no es la suma de las voces" "H15 acto 2" 'g["narracion"][1]["texto"] = g["narracion"][1]["texto"].replace("harina", "arina", 1)'
neg_historia "sin narración" "H15 «narracion»" 'g.pop("narracion")'
neg_historia "tres escenas que abren con «Según»" "H16 3 escenas abren con una atribución" '[x.update(texto="Según la prensa, " + x["texto"][0].lower() + x["texto"][1:]) for x in (e[3], e[4], e[6])]'
neg_historia "dos escenas seguidas con la misma apertura" "H16 escenas 3 y 4 abren con las mismas palabras" 'e[3]["texto"] = "Marta Pérez " + e[3]["texto"]'
neg_historia "un acto sin conectores en la narración" "H16 acto 2" 'g["narracion"][1]["texto"] = g["narracion"][1]["texto"].replace("Entonces, en", "En").replace("Pero lo", "Lo")'
neg_historia "un hilo del encuadre sin pagar ni declarar" "H17 el hilo h1" 'g["hilos"] = g["hilos"][1:]'
neg_historia "un hilo pagado por una escena que no lo declara" "H17 hilo h1: la escena 8 no lo declara" 'e[7].pop("paga")'
neg_historia "un personaje sin presentación en su primera mención" "H18 escena 6" 'e[5]["texto"] = e[5]["texto"].replace(", la autoridad sanitaria,", "")'
neg_historia "cinco «según» en la voz" "H19" '[x.update(texto="Según Soy502, " + x["texto"][0].lower() + x["texto"][1:]) for x in e[1:6]]'
neg_historia "la misma fuente dos veces en voz" "H19 «según soy502» 2 veces" 'e[1]["texto"] = "Según Soy502, " + e[1]["texto"][0].lower() + e[1]["texto"][1:]; e[8]["texto"] = e[8]["texto"].replace("su familia dice", "según Soy502, su familia dice")'
neg_historia "una secuencia que cruza actos con el giro en medio" "H20 secuencia 1" 'g["secuencias"] = [[4, 5, 6]]'
neg_historia "secuencias solapadas" "V9 secuencia 2: escenas repetidas" 'g["secuencias"] = [[2, 3], [3, 4]]'
neg_historia "una secuencia con el gancho" "V9 secuencia 1: escenas entre 2 y" 'g["secuencias"] = [[1, 2]]'
capitulo_compat() {
  local S="$TMP/hcap"; rm -rf "$S"; cp -R "$HT" "$S"; rm -f "$S/locucion.json"
  python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+"/guion.json")); e=g["escenas"]; r=e[5].pop("rotulo")
e[5:5]=[{"tipo":"capitulo","acto":2,"numero":1,"anio":r["anio"],"titulo":r["titulo"],"lugar":r["lugar"],"texto":"Llega una inspección."}]
g["promesa"]["pago"]=10; g["hilos"][0]["escena"]=9; g.pop("secuencias")
exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False)' "$S" "$RN"
  python3 scripts/historia.py guion "$S" --check > "$TMP/hcap.out" 2>&1 || { cat "$TMP/hcap.out"; return 1; }
  grep -q "AVISO H8 1 escena(s) capitulo detienen la voz" "$TMP/hcap.out" || { echo "sin aviso de capitulo"; return 1; }
  tail -1 "$TMP/hcap.out" | python3 -c 'import json,sys; r=json.loads(sys.stdin.read()[8:]); assert r["capitulos"]==1 and r["rotulos"]==1 and r["actos"]==3 and r["secuencias"]>=3, r'
}
paso "historia.py guion --check: una escena capitulo (la excepción) pasa con aviso; el gate deriva las secuencias" capitulo_compat
aplicar_arreglo() {
  local S="$TMP/hapl"; rm -rf "$S"; cp -R "$HT" "$S"
  local bueno malo antes
  bueno=$(python3 -c 'import json,sys; t=json.load(open(sys.argv[1]+"/guion.json"))["escenas"][3]["texto"]; print(json.dumps([{"escena": 4, "texto": t.replace("destruyó", "derribó")}], ensure_ascii=False))' "$S")
  python3 scripts/historia.py aplicar "$S" --cambios "$bueno" > "$TMP/hapl.out" 2>&1 || { cat "$TMP/hapl.out"; return 1; }
  tail -1 "$TMP/hapl.out" | grep -q 'RETORNO {"escenas_cambiadas": \[4\]}' || { echo "sin RETORNO de escenas_cambiadas"; return 1; }
  grep -q "derribó" "$S/guion.json" && grep -q "derribó" "$S/locucion.json" && test -s "$S/guion.previo.json" || { echo "el cambio no llegó a guion.json y locucion.json"; return 1; }
  antes=$(shasum "$S/guion.json" | cut -d" " -f1)
  malo='[{"escena": 4, "texto": "Según unos, según otros, según la familia, según el diario y según todos, el local cayó."}]'
  ! python3 scripts/historia.py aplicar "$S" --cambios "$malo" > "$TMP/hapl2.out" 2>&1 || { echo "un arreglo que el gate rechaza se aplicó"; return 1; }
  [[ "$(shasum "$S/guion.json" | cut -d" " -f1)" == "$antes" ]] || { echo "guion.json cambió tras un arreglo rechazado"; return 1; }
}
paso "historia.py aplicar: un arreglo probado llega a guion.json y locucion.json; uno que el gate rechaza deja el guion como estaba" aplicar_arreglo
gancho_sin_foto() {
  local S="$TMP/hgsf"; rm -rf "$S"; cp -R "$HT" "$S"
  python3 -c 'import json,sys; d=sys.argv[1]; k=json.load(open(d+"/ganchos.json")); c=k["candidatos"][1]; c.update(visual="pareja", visual_datos={"a": {"valor": "ori-c01", "etiqueta": "panes al día, 1968"}, "b": {"valor": "cas-c01", "etiqueta": "quetzales de multa, 2004"}}); json.dump(k, open(d+"/ganchos.json","w"), ensure_ascii=False)' "$S"
  python3 scripts/historia.py ganchos "$S" --check | grep -q "FALLA g2: H7 el gancho de una historia abre con una foto a sangre" || { echo "un gancho sin foto pasó"; return 1; }
  python3 -c 'import json,sys; d=sys.argv[1]; v=json.load(open(d+"/verificacion_cas.json")); v["fotos"]=v["fotos"][:1]; json.dump(v, open(d+"/verificacion_cas.json","w"), ensure_ascii=False)' "$S"
  python3 scripts/historia.py hechos "$S" --check | grep -q "H7 eje cas: 1 foto" || { echo "un eje con una foto pasó"; return 1; }
}
paso "historia.py: el gancho abre con foto a sangre y cada eje trae ≥ 2 fotos (H7)" gancho_sin_foto
gancho_sin_protagonista() {
  local S="$TMP/hgsp"; rm -rf "$S"; cp -R "$HT" "$S"
  python3 -c 'import json,sys; d=sys.argv[1]; k=json.load(open(d+"/ganchos.json")); c=k["candidatos"][0]; c.update(linea="Una panadería reabrió tras el terremoto", texto="Una panadería reabrió bajo una carpa. Fue en Guatemala, tras el terremoto de 1976."); json.dump(k, open(d+"/ganchos.json","w"), ensure_ascii=False)' "$S"
  python3 scripts/historia.py ganchos "$S" --check | grep -q "FALLA g1: H10 el gancho no nombra al protagonista" || { echo "un gancho sin protagonista pasó"; return 1; }
}
paso "historia.py ganchos --check: el gancho nombra al protagonista del encuadre (H10)" gancho_sin_protagonista
gancho_regala_revelacion() {
  local S="$TMP/hgrr"; rm -rf "$S"; cp -R "$HT" "$S"
  python3 -c 'import json,sys; d=sys.argv[1]; e=json.load(open(d+"/encuadre.json")); e["revelaciones"].append("La Espiga llegó a 25 locales y los cerró"); json.dump(e, open(d+"/encuadre.json","w"), ensure_ascii=False)' "$S"
  python3 scripts/historia.py ganchos "$S" --check | grep -q "FALLA g4: H13 el gancho adelanta la revelación R4" || { echo "un gancho que regala la revelación pasó"; return 1; }
}
paso "historia.py ganchos --check: el gancho no escribe un número de una revelación (H13)" gancho_regala_revelacion
foto_protagonista() {
  local S="$TMP/hprot" D="$TMP/hprot_descargas" URL="https://www.soy502.com/espiga-local-25"; rm -rf "$S" "$D"; cp -R "$HT" "$S"; mkdir -p "$D"
  python3 -c 'import json,sys; d=sys.argv[1]; k=json.load(open(d+"/ganchos.json")); k["candidatos"][0]["visual_datos"]["foto"]="cas-f02"; json.dump(k, open(d+"/ganchos.json","w"), ensure_ascii=False)' "$S"
  python3 scripts/historia.py ganchos "$S" --check | grep -q "FALLA g1: H12 la foto del gancho" || { echo "un gancho con una foto de referencia pasó"; return 1; }
  for f in "$S"/fotos/*.json; do python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); r.pop("muestra", None); json.dump(r, open(sys.argv[1],"w"), ensure_ascii=False)' "$f"; done
  ffmpeg -v error -y -f lavfi -i color=c=gray:s=1200x800 -frames:v 1 "$D/og.jpg"
  local base; base=$(HISTORIA_DESCARGAS="$D" python3 -c 'import sys; sys.path.insert(0,"scripts"); import historia as H; print(H.ruta_fuente(sys.argv[1]))' "$URL")
  python3 -c 'import json,sys; json.dump({"url": sys.argv[1], "dominio": "soy502.com", "clase": "medio", "titulo": "La Espiga abre su local 25", "fecha": "2004-03-01", "og_image": "file://"+sys.argv[2], "archivo": None, "caracteres": 900}, open(sys.argv[3]+".json","w"))' "$URL" "$D/og.jpg" "$base"
  HISTORIA_DESCARGAS="$D" python3 scripts/historia.py hechos "$S" --check > "$TMP/hprot.out" 2>&1
  grep -q "FALLA H12 ninguna foto muestra al protagonista" "$TMP/hprot.out" || { echo "sin foto del protagonista pasó"; cat "$TMP/hprot.out"; return 1; }
  grep -q -- "--de-fuente $URL .*--protagonista" "$TMP/hprot.out" || { echo "no sugirió la og:image de la fuente leída"; cat "$TMP/hprot.out"; return 1; }
  ! HISTORIA_DESCARGAS="$D" python3 scripts/historia.py consolidar "$S" >/dev/null 2>&1 || { echo "consolidar sin foto del protagonista pasó"; return 1; }
  ! python3 scripts/historia.py foto "$S" --id cas-f03 --url x --protagonista --referencia >/dev/null 2>&1 || { echo "--protagonista con --referencia pasó"; return 1; }
  HISTORIA_DESCARGAS="$D" python3 scripts/historia.py foto "$S" --id cas-f03 --de-fuente "$URL" --descripcion "El local 25" --protagonista >/dev/null || { echo "foto --de-fuente falló"; return 1; }
  python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["origen"]=="medio" and r["credito"]=="Foto: Soy502" and r["muestra"]=="protagonista" and r["fecha"]=="2004-03-01" and r["fuente"]==sys.argv[2], r' "$S/fotos/cas-f03.json" "$URL"
  python3 -c 'import json,sys; d=sys.argv[1]; v=json.load(open(d+"/verificacion_cas.json")); v["fotos"].append("cas-f03"); json.dump(v, open(d+"/verificacion_cas.json","w"), ensure_ascii=False)' "$S"
  HISTORIA_DESCARGAS="$D" python3 scripts/historia.py hechos "$S" --check | grep -q "H12 foto(s) del protagonista: cas-f03" || { echo "hechos --check no vio la foto nueva"; return 1; }
}
paso "historia.py: la foto del protagonista es obligatoria (H12 en gancho, hechos --check y consolidar) y foto --de-fuente baja la og:image de una fuente leída" foto_protagonista
voz_pendientes() {
  local S="$TMP/hvoz"; rm -rf "$S"; cp -R "$HT" "$S"
  python3 scripts/historia.py voz-falsa "$S" >/dev/null || return 1
  [[ -s "$S/audio/secuencias.json" && -s "$S/audio/voz_sec_1.mp3" && -s "$S/audio/voz_3.mp3" ]] || { echo "la voz falsa no se generó por secuencia ni se cortó"; return 1; }
  python3 scripts/historia.py voz "$S" --pendientes 2>/dev/null | python3 -c 'import json,sys; r=json.load(sys.stdin); assert r["nodos"]==[] and r["caracteres"]==0, r'
  python3 scripts/historia.py voz "$S" 2>/dev/null | python3 -c 'import json,sys; r=json.load(sys.stdin); ids=[n["n"] for n in r["nodos"]]; assert ids==[1,"s1","s2","s3","s4",10], ids; assert r["nodos"][1]["escenas"]==[2,3] and r["nodos"][1]["prompt"].count(".")>=2, r["nodos"][1]'
  python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+"/guion.json")); e=g["escenas"]; e[2]["texto"]=e[2]["texto"].replace("Xela", "Quetzaltenango"); exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False)' "$S" "$RN"
  python3 scripts/historia.py guion "$S" --check >/dev/null || { echo "el gate falló tras el cambio"; return 1; }
  rm "$S/audio/voz_7.mp3"
  python3 scripts/historia.py voz "$S" --pendientes 2>"$TMP/hvoz.err" | python3 -c 'import json,sys; r=json.load(sys.stdin); assert [n["n"] for n in r["nodos"]]==["s1","s3"], r'
  grep -q "2 por generar en 2 nodo(s)" "$TMP/hvoz.err" || { cat "$TMP/hvoz.err"; return 1; }
  grep -q "secuencia s1 (E2–E3)" "$TMP/hvoz.err" || { cat "$TMP/hvoz.err"; return 1; }
  python3 scripts/historia.py voz "$S" --pendientes --sueltas 2>/dev/null | python3 -c 'import json,sys; r=json.load(sys.stdin); assert [n["n"] for n in r["nodos"]]==[3,7], r'
  python3 scripts/historia.py voz "$S" --solo 2,5 2>/dev/null | python3 -c 'import json,sys; r=json.load(sys.stdin); assert [n["n"] for n in r["nodos"]]==[2,5], r'
}
paso "historia.py voz: un nodo por secuencia (voz de corrido), --pendientes regraba la secuencia entera, --sueltas solo las escenas, --solo" voz_pendientes
partir_sintetico() {
  local S="$TMP/hpartir"; rm -rf "$S"; mkdir -p "$S/audio"
  python3 -c 'import json,sys; d=sys.argv[1]
json.dump({"voz": {}, "caracteres": 0, "estimado_s": 0, "secuencias": [{"k": 1, "escenas": [2, 3], "prompt": "Hola mundo. Adiós mundo cruel.", "caracteres": 29}],
  "escenas": [{"n": 2, "voz": "Hola mundo."}, {"n": 3, "voz": "Adiós mundo cruel."}]}, open(d+"/locucion.json","w"))
json.dump([{"text": "Hola", "start": 0.1, "end": 0.4}, {"text": "mundo.Adiós", "start": 0.5, "end": 1.3}, {"text": "mun", "start": 1.4, "end": 1.6}, {"text": "do", "start": 1.6, "end": 1.7}, {"text": "cruel.", "start": 1.8, "end": 2.2}], open(d+"/audio/palabras_sec_1.json","w"))' "$S"
  ffmpeg -v error -y -f lavfi -i "sine=frequency=220:duration=2.5" -c:a libmp3lame -b:a 64k "$S/audio/voz_sec_1.mp3"
  python3 scripts/video.py partir "$S" > "$TMP/hpartir.out" 2>&1 || { cat "$TMP/hpartir.out"; return 1; }
  python3 -c 'import json,sys,subprocess; d=sys.argv[1]
p2=json.load(open(d+"/audio/palabras_2.json")); p3=json.load(open(d+"/audio/palabras_3.json"))
assert [w["text"] for w in p2]==["Hola","mundo."] and [w["text"] for w in p3]==["Adiós","mundo","cruel."], (p2,p3)
assert p2[0]["start"]<0.5 and p3[0]["start"]<0.5 and p3[1]["end"]>p3[1]["start"], (p2,p3)
dur=lambda f: float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
c=json.load(open(d+"/audio/secuencias.json"))["1"]["cortes_s"]; assert abs(dur(d+"/audio/voz_2.mp3")-c[1])<0.12 and abs(dur(d+"/audio/voz_3.mp3")-(c[2]-c[1]))<0.12, (c, dur(d+"/audio/voz_2.mp3"), dur(d+"/audio/voz_3.mp3"))' "$S"
  python3 -c 'import json,sys; d=sys.argv[1]; ws=json.load(open(d+"/audio/palabras_sec_1.json")); ws[0]["text"]="Hello"; json.dump(ws, open(d+"/audio/palabras_sec_1.json","w"))' "$S"
  ! python3 scripts/video.py partir "$S" >/dev/null 2>"$TMP/hpartir.err" || { echo "un desajuste de Scribe pasó"; return 1; }
  grep -q "V6 secuencia s1" "$TMP/hpartir.err" || { cat "$TMP/hpartir.err"; return 1; }
}
paso "video.py partir: corta una secuencia en sus escenas con los tiempos de Scribe (repara un token fundido y uno partido; V6 si no casa)" partir_sintetico
paso "video.py comparar_escucha: una cita en otro idioma (omitir) no cuenta como distinta; un número mal oído sigue siendo falta" python3 -c 'import sys; sys.path.insert(0,"scripts"); import video as V
seg=[{"v":"Lo dijo así:","num":False},{"v":"Every loaf comes out of the same oven","num":False},{"v":"y vendía cuarenta panes","num":True}]
f,a,p=V.comparar_escucha(seg,"Lo dijo así: y vendía cuarenta panes",omitir="Every loaf comes out of the same oven"); assert not f and p<10,(f,a,p)
f,a,p=V.comparar_escucha(seg,"Lo dijo así: y vendía catorce panes",omitir="Every loaf comes out of the same oven"); assert f,(f,a,p)
f,a,p=V.comparar_escucha(seg,"Lo dijo así: y vendía cuarenta panes"); assert p>30,(f,a,p)'
paso "historia.py guion --check imprime RETORNO (tipos, actos, rótulos, palabras, según, secuencias, hilos; gate ok)" bash -c "python3 scripts/historia.py guion '$HT' --check | tail -1 | python3 -c 'import json,sys; l=sys.stdin.read(); assert l.startswith(\"RETORNO \"), l; r=json.loads(l[8:]); assert r[\"gate\"]==\"ok\" and r[\"escenas\"]==9 and len(r[\"tipos\"])==9 and \"cierre\" not in r[\"tipos\"] and r[\"tipos\"][0]==\"gancho\" and r[\"capitulos\"]==0 and r[\"actos\"]==3 and r[\"rotulos\"]==2 and r[\"segun\"]==0 and r[\"secuencias\"]==4 and r[\"hilos_pagados\"]==1 and r[\"hilos_sin_respuesta\"]==1 and 280<=r[\"palabras\"]<=430, r'"
paso "historia.py guion --check: el RETORNO con gate falla trae las FALLA de video.py" bash -c "S='$TMP/hret'; rm -rf \"\$S\"; cp -R '$HT' \"\$S\"; python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+\"/guion.json\")); g[\"promesa\"][\"pago\"]=3; json.dump(g, open(d+\"/guion.json\",\"w\"), ensure_ascii=False)' \"\$S\"; python3 scripts/historia.py guion \"\$S\" --check | tail -1 | grep -q '\"gate\": \"falla\".*promesa'"
paso "historia.py aviso_duracion: avisa sobre 165 s y calla en 150" python3 -c 'import sys; sys.path.insert(0,"scripts"); import historia as H; assert "AVISO H5" in H.aviso_duracion(170) and H.aviso_duracion(150) is None'
paso "digesto --para gancho y --para guionista listan las revelaciones, la espina, los hilos, los personajes y ALEGATO" bash -c "python3 scripts/historia.py digesto '$HT' --para gancho | grep -q 'R2. Cerró la última sucursal' && python3 scripts/historia.py digesto '$HT' --para guionista > '$TMP/dg.txt' && grep -q 'h1 · ¿Por qué cerró?' '$TMP/dg.txt' && grep -q 'detonante (acto 1' '$TMP/dg.txt' && grep -q 'Marta Pérez (Marta) — la fundadora' '$TMP/dg.txt' && grep -q 'cas-h04.*ALEGATO' '$TMP/dg.txt' && grep -q 'una_fuente' '$TMP/dg.txt' && ! grep -q 'Narración (de corrido)' '$TMP/dg.txt'"
paso "digesto --para critico trae la narración de corrido, la duración y el presupuesto de «según»; --para editor el re-encuadre" bash -c "python3 scripts/historia.py digesto '$HT' --para critico > '$TMP/dc.txt' && grep -q '## Narración (de corrido)' '$TMP/dc.txt' && grep -q '^- Acto 2: ' '$TMP/dc.txt' && grep -q 'Duración objetivo 150 s' '$TMP/dc.txt' && python3 scripts/historia.py digesto '$HT' --para editor | grep -q '## Encuadre actual'"
paso "digesto --para oyente: solo voz y pantalla, en orden, sin cronología ni ids" bash -c "python3 scripts/historia.py digesto '$HT' --para oyente > '$TMP/oy.txt' && grep -q '## La narración de corrido' '$TMP/oy.txt' && grep -q '^E6 · cita · PANTALLA: 2004 · La inspección' '$TMP/oy.txt' && grep -q '^E9 · foto · PANTALLA: 2010' '$TMP/oy.txt' && grep -q '^E10 · cierre' '$TMP/oy.txt' && ! grep -q 'Cronología\|ori-h0' '$TMP/oy.txt'"
cita_en_ingles() {
  local S="$TMP/hingles"; rm -rf "$S"; cp -R "$HT" "$S"
  python3 -c 'import json,sys; d=sys.argv[1]; h=json.load(open(d+"/historia.json")); q=next(x for x in h["citas"] if x["id"]=="ori-q01"); q["texto"]="Every loaf comes out of the same oven that we lit on the first day"; json.dump(h, open(d+"/historia.json","w"), ensure_ascii=False)
g=json.load(open(d+"/guion.json")); e=g["escenas"]; e[2]["texto"]="Marta Pérez, la fundadora, lo dijo así: Every loaf comes out of the same oven that we lit on the first day"; exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False)' "$S" "$RN"
  python3 scripts/historia.py guion "$S" --check | grep -q "H6 escena 3: la cita no está en español" || { echo "cita en inglés sin traducción no falló"; return 1; }
  python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+"/guion.json")); e=g["escenas"]; e[2]["traduccion"]="Cada pan sale del mismo horno que encendimos el primer día"; e[2]["texto"]+=". Cada pan sale del mismo horno que encendimos el primer día."; exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False)' "$S" "$RN"
  ! python3 scripts/historia.py guion "$S" --check | grep -q "H6 escena 3: la cita no está en español" || { echo "con traducción siguió fallando"; return 1; }
  python3 -c 'import json,sys; l=json.load(open(sys.argv[1]+"/locucion.json")); assert l["escenas"][2]["escucha_omitir"].startswith("Every loaf"), l["escenas"][2]' "$S" || { echo "la cita en inglés no quedó marcada para la escucha (escucha_omitir)"; return 1; }
}
paso "historia.py guion --check: cita en otro idioma pide traduccion en pantalla y en la voz (H6)" cita_en_ingles
fotos_repetidas() {
  local S="$TMP/hdup"; rm -rf "$S"; cp -R "$HT" "$S"
  cp "$S/fotos/ori-f01.jpg" "$S/fotos/rec-f09.jpg"
  python3 -c 'import json,sys; d=sys.argv[1]; r=json.load(open(d+"/fotos/ori-f01.json")); r.update(id="rec-f09", archivo="fotos/rec-f09.jpg", url="https://otra.url/x.jpg"); r.pop("sha1", None); json.dump(r, open(d+"/fotos/rec-f09.json","w"))' "$S"
  python3 scripts/historia.py consolidar "$S" | grep -q "rec-f09 es la misma imagen que ori-f01" || { echo "no fundió la foto repetida"; return 1; }
  python3 -c 'import json,sys; h=json.load(open(sys.argv[1]+"/historia.json")); assert "rec-f09" not in h["fotos"] and "rec-f09" in h["fotos"]["ori-f01"]["alias"]' "$S"
}
paso "historia.py consolidar: la misma imagen con dos ids queda en uno (alias)" fotos_repetidas
paso "historia.py encajar: un gráfico apaisado queda entero en el marco de 9:16 y de 4:5" bash -c "ffmpeg -v error -y -f lavfi -i color=c=white:s=1600x1018 -frames:v 1 '$TMP/graf.jpg' && python3 -c 'import sys; sys.path.insert(0,\"scripts\"); import historia as H; w,h=H.encajar(sys.argv[1]); assert w>=1.18*1600 and w/h<=0.95 and w/1.11>=1.18*1018, (w,h)' '$TMP/graf.jpg'"
hechos_negativos() {
  local S="$TMP/hhech"; rm -rf "$S"; cp -R "$HT" "$S"
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_ori.json")); v["hechos"][0]["fuentes"][0]["cita"]="Marta Pérez fundó una pizzería en 1952"; json.dump(v, open(S+"/verificacion_ori.json","w"))' "$S"
  python3 scripts/historia.py hechos "$S" --check --eje ori | grep -q "H2 ori-h01: la cita de" || { echo "cita fuera del texto no falló"; return 1; }
  cp "$HT/verificacion_ori.json" "$S/"
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_ori.json")); v["hechos"][1]["fuentes"]=v["hechos"][1]["fuentes"][:1]; json.dump(v, open(S+"/verificacion_ori.json","w"))' "$S"
  python3 scripts/historia.py hechos "$S" --check --eje ori | grep -q "H2 ori-h02: confirmado pide 2 fuentes" || { echo "una fuente confirmó"; return 1; }
  cp "$HT/verificacion_ori.json" "$S/"
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_ori.json")); v["hechos"][0]["fecha"]="1953"; json.dump(v, open(S+"/verificacion_ori.json","w"))' "$S"
  python3 scripts/historia.py hechos "$S" --check --eje ori | grep -q "el año 1953 no está" || { echo "año fuera de la cita no falló"; return 1; }
  cp "$HT/verificacion_ori.json" "$S/"
  python3 -c 'import json,sys; S=sys.argv[1]; e=json.load(open(S+"/encuadre.json")); e["sensibles"]["justicia"]=True; json.dump(e, open(S+"/encuadre.json","w"))' "$S"
  python3 scripts/historia.py hechos "$S" --check | grep -q "H3 historia de justicia" || { echo "justicia sin casos no falló"; return 1; }
  cp "$HT/encuadre.json" "$S/"
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_ori.json")); v["hechos"][0]["estado"]="una_fuente"; json.dump(v, open(S+"/verificacion_ori.json","w"))' "$S"
  python3 scripts/historia.py hechos "$S" --check --eje ori | grep -q "H2 ori-h01: tiene fuentes de 2 grupos" || { echo "una_fuente con dos grupos pasó"; return 1; }
  cp "$HT/verificacion_ori.json" "$S/"
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_cas.json")); h=next(x for x in v["hechos"] if x["id"]=="cas-h03"); h["estado"]="en_disputa"; h["nota"]="solo Soy502 lo reporta"; json.dump(v, open(S+"/verificacion_cas.json","w"))' "$S"
  python3 scripts/historia.py hechos "$S" --check --eje cas | grep -q "AVISO H2 cas-h03: en_disputa con un solo grupo" || { echo "sin aviso de reclasificación"; return 1; }
  python3 scripts/historia.py hechos "$S" --reclasificar | grep -q "CANDIDATO cas-h03" || { echo "--reclasificar no propuso cas-h03"; return 1; }
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_cas.json")); assert next(x for x in v["hechos"] if x["id"]=="cas-h03")["estado"]=="en_disputa"' "$S"
  python3 scripts/historia.py hechos "$S" --reclasificar --aplicar | grep -q "CAMBIA cas-h03" || { echo "--aplicar no cambió cas-h03"; return 1; }
  python3 -c 'import json,sys; S=sys.argv[1]; v=json.load(open(S+"/verificacion_cas.json")); assert next(x for x in v["hechos"] if x["id"]=="cas-h03")["estado"]=="una_fuente"' "$S"
}
paso "historia.py hechos --check: cita fuera del texto, una sola fuente, año fuera de la cita, justicia sin casos, una_fuente con dos grupos (H2, H3); --reclasificar propone y --aplicar escribe" hechos_negativos
paso "historia.py encuadre --check: sin espina, hilos fuera de rango o el protagonista como personaje falla" bash -c "S='$TMP/henc'; rm -rf \"\$S\"; cp -R '$HT' \"\$S\"; python3 -c 'import json,sys; d=sys.argv[1]; e=json.load(open(d+\"/encuadre.json\")); e[\"espina\"].pop(\"climax\"); e[\"hilos\"]=e[\"hilos\"][:1]; e[\"personajes\"].append({\"nombre\": \"La Espiga\", \"presentacion\": \"la panadería\"}); json.dump(e, open(d+\"/encuadre.json\",\"w\"), ensure_ascii=False)' \"\$S\"; python3 scripts/historia.py encuadre \"\$S\" --check > '$TMP/henc.out' 2>&1; grep -q 'espina.climax' '$TMP/henc.out' && grep -q '1 hilos' '$TMP/henc.out' && grep -q 'es el protagonista' '$TMP/henc.out' && ! python3 scripts/historia.py consolidar \"\$S\" >/dev/null 2>&1"
paso "historia.py narracion --check sobre la maqueta: 0 fallas e imprime palabras, conectores, personajes e hilos" bash -c "python3 scripts/historia.py narracion '$HT' --check > '$TMP/narr.out' && grep -q 'acto 1 · ' '$TMP/narr.out' && grep -q 'personaje Marta Pérez: nombrado y presentado' '$TMP/narr.out' && grep -q 'hilo h2 .*sin respuesta' '$TMP/narr.out' && grep -q 'narracion ok' '$TMP/narr.out'"
paso "licencias de Commons: CC BY-SA y dominio público sí; NC, ND y no libre no (H7)" python3 -c 'import sys; sys.path.insert(0,"scripts"); import historia as H
m=lambda l, a="Autor": {"LicenseShortName": {"value": l}, "Artist": {"value": a}}
assert H.licencia(m("CC BY-SA 4.0"))[0] and H.licencia(m("Public domain", ""))[0] and H.licencia(m("CC0"))[0] and H.licencia(m("CC BY 2.0"))[0]
assert not H.licencia(m("CC BY-NC-SA 4.0"))[0] and not H.licencia(m("CC BY-ND 3.0"))[0] and not H.licencia(m(""))[0]
assert not H.licencia(dict(m("CC BY-SA 4.0"), NonFree={"value": "true"}))[0]'
paso "clasificar: Wikipedia no cuenta; Wayback cuenta como su original; academia y organismos sí" python3 -c 'import sys; sys.path.insert(0,"scripts"); import historia as H
assert H.clasificar("https://es.wikipedia.org/wiki/Guatemala")[0] is None
assert H.clasificar("https://web.archive.org/web/2015/https://www.prensalibre.com/x") == ("medio", "prensa-libre")
assert H.clasificar("https://www.cicig.org/x")[0] == "oficial" and H.clasificar("https://www.scielo.org/x")[0] == "academica"'
paso "clasificar: Forbes México, E&N, Bloomberg Línea y museos cuentan; Mental Floss no; una nota firmada por AP en otro diario cuenta como ap" bash -c "printf 'Happy Meals\nBy Associated Press\nKANSAS CITY (AP) texto' > '$TMP/ap.txt'; printf 'Foto: Fulano, Associated Press\ntexto local' > '$TMP/foto_ap.txt'; python3 -c 'import sys; sys.path.insert(0,\"scripts\"); import historia as H
assert H.clasificar(\"https://www.forbes.com.mx/x\") == (\"medio\", \"forbes\") and H.clasificar(\"https://www.revistaeyn.com/x\") == (\"medio\", \"eyn\")
assert H.clasificar(\"https://www.bloomberglinea.com/x\")[0] == \"medio\" and H.clasificar(\"https://www.thehenryford.org/x\")[0] == \"archivo\"
assert H.clasificar(\"https://www.mentalfloss.com/x\")[0] is None and H.clasificar(\"https://www.deseret.com/x\")[0] is None
assert H.clasificar(\"https://www.deseret.com/x\", (), sys.argv[1]) == (\"medio\", \"ap\")
assert H.clasificar(\"https://www.deseret.com/x\", (), sys.argv[2])[0] is None' '$TMP/ap.txt' '$TMP/foto_ap.txt'"
paso "validate.py M10: un registro de historia sin campos, con slug repetido y sin su entrega falla" bash -c "R='$TMP/m10'; rm -rf \"\$R\"; mkdir -p \"\$R/memoria\" \"\$R/design/musica\"; cp design/musica/catalogo.json \"\$R/design/musica/\"; printf '{\"historias\": [{\"id\": \"a\", \"slug\": \"x\", \"fecha\": \"2026-01-01\", \"ruta\": \"historias/no-existe\", \"paleta\": \"maiz\", \"musica\": \"maiz-1\", \"duracion_s\": 150, \"estado\": \"listo\", \"frases\": {}}, {\"id\": \"b\", \"slug\": \"x\", \"estado\": \"raro\"}]}' > \"\$R/memoria/historias.json\"; python3 -c 'import sys; sys.path.insert(0,\"scripts\"); import validate as V; V.RAIZ=sys.argv[1]; V.validar_historias({\"maiz\"}); e=\" | \".join(V.ERRORES); assert \"M10 historias[1] sin ruta\" in e and \"slug repetido x\" in e and \"sin guion.json\" in e and \"estado\" in e, e' \"\$R\""
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make historia-fixture (RAPIDO=1)"; else
  paso "make historia-fixture (maqueta 9:16 y 4:5, V7, V13, V8)" bash -c 'make historia-fixture >/dev/null && ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_historia/trabajo/salida/video_4x5.mp4 | grep -q "video,1080,1350"'
  paso "historia.py entregar --salida + memoria.py --historia --dry-run (maqueta: fuentes.md, cronologia.md, guion.json tipo historia)" bash -c "rm -rf '$TMP/hentrega' && python3 scripts/historia.py entregar sesiones/_fixture_historia/trabajo --salida '$TMP/hentrega' >/dev/null && test -s '$TMP/hentrega/fuentes.md' && test -s '$TMP/hentrega/cronologia.md' && test -s '$TMP/hentrega/video_4x5.mp4' && python3 -c 'import json,sys; g=json.load(open(sys.argv[1]+\"/guion.json\")); assert g[\"tipo\"]==\"historia\" and g[\"gancho\"][\"familia\"] and g[\"escenas\"]' '$TMP/hentrega' && python3 scripts/memoria.py --historia '$TMP/hentrega' --dry-run | grep -q 'gancho resultado/foto · cierre legado'"
  paso "historia.py entregar sin créditos de voz y sin --salida no entrega (voz falsa)" bash -c "! python3 scripts/historia.py entregar sesiones/_fixture_historia/trabajo >/dev/null 2>&1"
fi

echo "== /sabias (gate S1–S3 sobre el dato de prueba; sin web ni créditos)"
ST="$TMP/sabias"
paso "sabias.py preparar sobre sesiones/_fixture_dato/salida (base/, video.json tipo sabias, tarjeta en Noche)" bash -c "python3 scripts/sabias.py preparar sesiones/_fixture_dato/salida --trabajo '$ST' --fixture >/dev/null && test -s '$ST/base/hilo.json' && grep -q 'data-estilo=\"noche\"' '$ST/tarjetas/tuit_1.html' && python3 -c 'import json,sys; st=json.load(open(sys.argv[1])); assert st[\"tipo\"]==\"sabias\" and st[\"duracion\"]==\"sabias\"' '$ST/video.json'"
paso "sabias.py guion --check pasa con el guion fijo de la maqueta" bash -c "cp sesiones/_fixture_sabias/guion.json '$ST/' && python3 scripts/sabias.py guion '$ST' --check >/dev/null"
sabias_neg() {  # sabias_neg "código python sobre g" "texto esperado en las FALLA"
  python3 -c 'import json,sys; g=json.load(open("sesiones/_fixture_sabias/guion.json")); exec(sys.argv[1]); json.dump(g, open(sys.argv[2]+"/guion.json","w"), ensure_ascii=False)' "$1" "$ST" || return 1
  local out; out="$(python3 scripts/sabias.py guion "$ST" --check 2>&1)" && return 1
  grep -qF "$2" <<<"$out"
}
paso "S2 rechaza un gancho que no abre con «¿Sabías que…»" sabias_neg 'g["escenas"][0]["texto"]="El barril que compra Guatemala pasó de 67 a 102 dólares."' "S2 la voz abre con"
paso "S2 rechaza otra pantalla en el gancho" sabias_neg 'g["escenas"][0]["pantalla"]="102 dólares"' "S2 la pantalla del gancho"
paso "S1 rechaza conclusiones en el cierre (una sola pantalla)" sabias_neg 'g["cierre"]["resumen"]=["El barril, arriba."]' "S1 cierre.resumen"
paso "S1 rechaza una escena 2 que no es el dato" sabias_neg 'g["escenas"][1]={"tipo":"golpe","pantalla":"102","linea":"dólares el barril","verbo":"es","texto":"Es el promedio: 102 dólares el barril."}' "S1 la escena 2 es el dato"
paso "S1 rechaza una promesa" sabias_neg 'g["promesa"]={"texto":"Quédate y sabrás cuánto.","en":2,"pago":3}' "S1 sin \`promesa\`"
paso "validate.py M13: un registro de /sabias sin campos y sin su entrega falla" bash -c "R='$TMP/m13'; rm -rf \"\$R\"; mkdir -p \"\$R/memoria\" \"\$R/design/musica\"; cp design/musica/catalogo.json \"\$R/design/musica/\"; printf '{\"sabias\": [{\"id\": \"a\", \"slug\": \"x\", \"fecha\": \"2026-01-01\", \"ruta\": \"datos/no-existe/video\", \"dato\": \"datos/no-existe\", \"paleta\": \"maiz\", \"musica\": \"maiz-1\", \"duracion_s\": 22, \"estado\": \"listo\", \"frases\": {}}, {\"id\": \"b\", \"slug\": \"x\", \"estado\": \"raro\"}]}' > \"\$R/memoria/sabias.json\"; python3 -c 'import sys; sys.path.insert(0,\"scripts\"); import validate as V; V.RAIZ=sys.argv[1]; V.validar_sabias({\"maiz\"}); e=\" | \".join(V.ERRORES); assert \"M13 sabias[1] sin ruta\" in e and \"slug repetido x\" in e and \"sin guion.json\" in e and \"estado\" in e, e' \"\$R\""
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make sabias-fixture (RAPIDO=1)"; else
  paso "make sabias-fixture (9:16 y 4:5 de 20–30 s, V7, V13, V8)" bash -c 'make sabias-fixture >/dev/null && ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_sabias/salida/video_4x5.mp4 | grep -q "video,1080,1350" && python3 -c "import json; g=json.load(open(\"sesiones/_fixture_sabias/salida/guion.json\")); assert g[\"tipo\"]==\"sabias\" and 20 <= g[\"duracion_s\"] <= 30, g[\"duracion_s\"]"'
  paso "memoria.py --sabias --dry-run sobre la entrega de la maqueta" bash -c "python3 scripts/memoria.py --sabias sesiones/_fixture_sabias/salida --dry-run | grep -q 'gancho pareja · apoyo golpe · cierre consecuencia'"
  paso "sabias.py entregar sin créditos de voz y sin --salida no entrega (voz falsa)" bash -c "! python3 scripts/sabias.py entregar sesiones/_fixture_sabias/trabajo >/dev/null 2>&1"
fi

echo "== /explica (gates E1–E12 sobre la maqueta del interés compuesto; sin web ni créditos)"
XT="$TMP/explica"
paso "explica.py preparar --fixture + encuadre + afirmaciones + consolidar + ganchos --usar + narracion + guion --check (maqueta)" bash -c "python3 scripts/explica.py preparar 'Interés compuesto (maqueta)' --slug interes-compuesto-maqueta --trabajo '$XT' --fixture >/dev/null && python3 scripts/explica.py encuadre '$XT' --check >/dev/null && python3 scripts/explica.py afirmaciones '$XT' --check >/dev/null && python3 scripts/explica.py consolidar '$XT' >/dev/null && python3 scripts/explica.py ganchos '$XT' --usar >/dev/null && python3 scripts/explica.py narracion '$XT' --check >/dev/null && python3 scripts/explica.py guion '$XT' --check >/dev/null"
paso "explica.py: la calculadora da Q17,449.40 (Q1,000 al 10 % por 30 años), 77.1 % de interés sobre interés y 72 ÷ 36 = 2" python3 -c '
import json, sys
X = json.load(open(sys.argv[1] + "/explicacion.json"))
s = {(x["id"], y["salida"]): y for x in X["ejemplos"] for y in x["salidas"]}
assert s["luis", "final"]["valor"] == 17449.4 and s["luis", "pct_interes_sobre_interes"]["valor"] == 77.1, s["luis", "final"]
assert s["r72_tarjeta", "anios"]["valor"] == 2.0 and not [x for x in X["ejemplos"] if x["id"] == "r72_tarjeta"][0]["ilustrativo"]
L = json.load(open(sys.argv[1] + "/locucion.json"))
assert [e["n"] for e in L["escenas"] if e.get("ejemplo")] == [1, 3, 4, 5, 8, 9], [e["n"] for e in L["escenas"] if e.get("ejemplo")]' "$XT"
# neg_explica "nombre" "GATE" "python que muta g (guion.json)"
neg_explica() {
  local nombre="$1" gate="$2" mut="$3" S="$TMP/xneg"
  rm -rf "$S"; cp -R "$XT" "$S"; rm -f "$S/locucion.json"
  python3 -c 'import json,sys; d=sys.argv[1]; g=json.load(open(d+"/guion.json")); e=g["escenas"]; exec(sys.argv[2]); json.dump(g, open(d+"/guion.json","w"), ensure_ascii=False)' "$S" "$mut"
  python3 scripts/explica.py guion "$S" --check >"$TMP/negx.out" 2>&1; local rc=$?
  paso "explica.py guion --check rechaza: $nombre ($gate)" bash -c "[[ $rc -ne 0 ]] && grep -q 'FALLA $gate' '$TMP/negx.out' && [[ ! -s '$S/locucion.json' ]]"
}
# XN: rehace guion.narracion desde las voces (E9) para que la mutación solo toque el gate que se prueba
XN='narr=[]
for a in (1,2,3):
    vs=[x["texto"] for i,x in enumerate(e,1) if (1 if i==1 else x.get("acto"))==a]
    if a==3: vs.append(g["cierre"]["texto"])
    narr.append({"acto":a,"texto":" ".join(vs)})
g["narracion"]=narr'
neg_explica "números de ejemplo sin decirlos como ejemplo" "E4 escena 5" 'e[4]["texto"] = e[4]["texto"].replace("Hagamos la cuenta de Ana año por año.", "Ana va año por año.")
'"$XN"
neg_explica "un número de ejemplo como dato de Guatemala" "E4 escena 8" 'e[7]["texto"] = e[7]["texto"].replace("Luis, que empezó diez años después, junta", "En Guatemala, Luis junta")
'"$XN"
neg_explica "una tarjeta de ejemplo con una institución como fuente" "E4 escena 9" 'e[8]["grafico"]["fuente"] = "Banguat"'
neg_explica "un consejo («te recomiendo»)" "E10 escena 13" 'e[12]["texto"] = "Te recomiendo ahorrar: " + e[12]["texto"][0].lower() + e[12]["texto"][1:]
'"$XN"
neg_explica "una cuenta mal sumada en la pizarra" "E11 escena 5: renglón 2" 'e[4]["renglones"][1]["r"] = "1,220"'
neg_explica "dos resaltados en una pizarra" "E11 escena 5: un solo renglón" 'e[4]["renglones"][0].update(resalta="r", etiqueta="el primer año")'
neg_explica "la narración no es la suma de las voces" "E9 acto 2" 'g["narracion"][1]["texto"] = g["narracion"][1]["texto"].replace("porque", "pues", 1)'
neg_explica "sin la escena de la idea equivocada" "E5 una escena del acto 1" 'e[2].pop("intuicion")'
neg_explica "sin la escena que la corrige" "E5 una escena del acto 2" 'e[4].pop("corrige")'
neg_explica "el acto 3 sin rótulo" "E5 el acto 3 empieza" 'e[10].pop("rotulo")'
neg_explica "un acento que no es de la leyenda" "E7 escena 7" 'e[6]["acento"] = "capital"'
neg_explica "un personaje del gancho que no vuelve" "E6 Luis" 'e[7]["texto"] = e[7]["texto"].replace("Luis, que empezó diez años después, junta", "Quien empezó diez años después junta")
'"$XN"
neg_explica "el giro fuera del acto 2" "E5" 'e[9].pop("giro"); e[11]["giro"] = True'
if [[ "$RAPIDO" == "1" ]]; then echo "SKIP   make explica-fixture (RAPIDO=1)"; else
  paso "make explica-fixture (maqueta 9:16 y 4:5, pizarra y chip «Ejemplo», V7, V13, V8, entrega)" bash -c 'make explica-fixture FPS=6 >/dev/null && ffprobe -v error -show_entries stream=codec_type,width,height -of csv=p=0 sesiones/_fixture_explica/salida/video_4x5.mp4 | grep -q "video,1080,1350" && test -s sesiones/_fixture_explica/salida/ejemplos.md && python3 scripts/memoria.py --explica sesiones/_fixture_explica/salida --dry-run >/dev/null'
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
paso "node --check noticias.js (envuelto en async function)" check_js noticias.js
paso "node --check historia.js (envuelto en async function)" check_js historia.js
paso "node --check explica.js (envuelto en async function)" check_js explica.js
paso "check_workflows.py (PALETAS, PLANTILLAS, HOOKS, BEATS, REQ, pesoX, MODOS, gráficos del informe W7–W8, bloque común W9, espejos de video.js W10, de noticias.js W11 y de historia.js W12)" python3 scripts/check_workflows.py

echo
echo "[test] $N pruebas · $FALLOS fallos"
[[ $FALLOS -eq 0 ]] || exit 1
exit 0
