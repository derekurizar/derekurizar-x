# Hilos · @DerekUrizar — tooling
# `make help` lista los comandos.

SHELL := /bin/bash
GALERIA := templates/.galeria
PALETAS ?= cielo
ESTILO ?= noche
PALETA ?= cielo

.PHONY: help nuevo render visual catalogo validate tabla pdf ensamblar limpiar test doctor costo contacto digesto fuentes ideas calendario informe informe-ejemplo informe-catalogo informe-fixture verificacion auditoria-rehacer podar video-fixture video-fixture-4x5 noticias-fixture historia-fixture explica-fixture sabias-fixture musica whisper iconos

help:
	@echo "make nuevo T=<plantilla> OUT=<ruta.html> [PALETA=cielo]  ensambla una tarjeta (base + plantilla)"
	@echo "make render FILE=<ruta.html> [OUT=<ruta.png>]            HTML -> PNG 1080x1080 @2x, sin checks"
	@echo "make visual FILE=<ruta.html> [OUT=<ruta.png>]            GATE: render + checks R1-R6 (exit 0 = pasa)"
	@echo "make catalogo [PALETAS=cielo|todas|a,b] [ESTILO=clasico]  ensambla y renderiza TODAS las plantillas en $(GALERIA)/ (Noche; clasico = /investigacion)"
	@echo "make ensamblar SESION=sesiones/<slug> [OUT=dir] [CHECK=1] sesion -> carpeta de hilo (hilos/) o de dato (datos/) segun guion.tipo"
	@echo "make validate                                            valida memoria/*.json y la integridad de hilos/ y datos/"
	@echo "make tabla URL=<xlsx|html|csv> [OUT=ruta]                descarga y convierte a CSV (sesiones/_descargas/)"
	@echo "make pdf URL=<pdf> [OUT=ruta.pdf]                         descarga y extrae texto (pdftotext -layout)"
	@echo "make test [RAPIDO=1]                                     pruebas: validate, catalogo, fixture, fixture dato, negativos, contar_x, sintaxis de los workflows"
	@echo "make doctor                                              comprueba node/playwright/python/fuentes/agentes"
	@echo "make costo [RUN=wf_xxx]                                  tokens, herramientas y tiempo por agente de una corrida (default: la última)"
	@echo "make contacto DIR=<carpeta con tuit_N.png>               hoja de contacto contacto.png"
	@echo "make digesto SESION=sesiones/<slug> [PARA=guionista]     resumen compacto de la sesión para agentes"
	@echo "make fuentes TEMA=\"texto\"                                 catálogo de fuentes y series filtrado por tema"
	@echo "make ideas                                               banco de ideas (ideas/banco.json) y temas ya producidos"
	@echo "make calendario [DIAS=30]                                calendario editorial (ideas/calendario.json): próximas ocasiones para /fecha"
	@echo "make informe DIR=<carpeta con informe.json> [PAL=x]    informe de investigación: gates I1-I6, PDF Letter y checks P1-P5 (salida en DIR/salida)"
	@echo "make informe-ejemplo                                     construye investigacion/ejemplos/dengue-2026 (21 páginas)"
	@echo "make informe-catalogo [PAL=x]                            genera y renderiza investigacion/ejemplos/catalogo (todos los G.* en papel, panel y media página; PNG por página)"
	@echo "make informe-fixture                                     informe de prueba (8 páginas) sobre sesiones/_fixture/salida, sin agentes (requiere el fixture ensamblado)"
	@echo "make video-fixture [FPS=10]                              /video de prueba sin créditos (voz falsa) sobre sesiones/_fixture/salida → sesiones/_fixture_video/salida"
	@echo "make noticias-fixture [FPS=10]                           /noticias de prueba (maqueta: noticias de ejemplo, voz falsa, 0 créditos) → sesiones/_fixture_noticias/trabajo/salida"
	@echo "make historia-fixture [FPS=10]                           /historia de prueba (maqueta: una panadería inventada, voz falsa, 0 créditos) → sesiones/_fixture_historia/trabajo/salida"
	@echo "make explica-fixture [FPS=10]                            /explica de prueba (maqueta: el interés compuesto con fuentes de ejemplo, voz falsa, 0 créditos) → sesiones/_fixture_explica/salida"
	@echo "make sabias-fixture [FPS=10]                             /sabias de prueba (el dato de sesiones/_fixture_dato, voz falsa, 0 créditos) → sesiones/_fixture_sabias/salida"
	@echo "make musica                                              catálogo fijo de música de /video (design/musica/) y sus usos"
	@echo "make whisper                                             baja una vez el modelo ggml-small de whisper.cpp (escucha V11 de /video; antes: brew install whisper-cpp)"
	@echo "make iconos                                              biblioteca FIJA de iconos de /video (design/iconos/, Lucide; se baja UNA vez) y su check K3"
	@echo "make limpiar [SESION=sesiones/<slug>]                    borra $(GALERIA)/, salidas de _fixture y _fixture_dato y .playwright-mcp/ (o una sesión)"

nuevo:
	@test -n "$(T)" -a -n "$(OUT)" || { echo "Uso: make nuevo T=<plantilla> OUT=<ruta.html> [PALETA=cielo]"; exit 2; }
	python3 scripts/nuevo_visual.py $(T) $(OUT) --paleta $(PALETA)

render:
	@test -n "$(FILE)" || { echo "Uso: make render FILE=<ruta.html> [OUT=<ruta.png>]"; exit 2; }
	node scripts/render.js $(FILE) $(if $(OUT),--out $(OUT),)

visual:
	@test -n "$(FILE)" || { echo "Uso: make visual FILE=<ruta.html> [OUT=<ruta.png>]"; exit 2; }
	node scripts/render.js $(FILE) --check $(if $(OUT),--out $(OUT),)

catalogo:
	rm -rf $(GALERIA) && mkdir -p $(GALERIA)
	python3 scripts/nuevo_visual.py --galeria $(GALERIA) --paletas $(PALETAS) --estilo $(ESTILO)
	node scripts/render.js $(GALERIA)/*.html --check

ensamblar:
	@test -n "$(SESION)" || { echo "Uso: make ensamblar SESION=sesiones/<slug> [OUT=dir] [CHECK=1]"; exit 2; }
	python3 scripts/ensamblar.py $(SESION) $(if $(OUT),--salida $(OUT),) $(if $(CHECK),--check,)

validate:
	python3 scripts/validate.py

tabla:
	@test -n "$(URL)" || { echo "Uso: make tabla URL=<xlsx|html|csv> [OUT=ruta]"; exit 2; }
	python3 scripts/fetch_tabla.py "$(URL)" $(if $(OUT),--out $(OUT),)

pdf:
	@test -n "$(URL)" || { echo "Uso: make pdf URL=<pdf> [OUT=ruta.pdf]"; exit 2; }
	bash scripts/fetch_pdf.sh "$(URL)" $(OUT)

limpiar:
ifdef SESION
	@case "$(SESION)" in sesiones/_fixture*|sesiones/_descargas*|sesiones/|sesiones) echo "no se borra $(SESION)"; exit 2;; sesiones/*) rm -rf "$(SESION)" && echo "borrada $(SESION)";; *) echo "SESION debe empezar por sesiones/"; exit 2;; esac
else
	rm -rf $(GALERIA) sesiones/_fixture/salida sesiones/_fixture/informe sesiones/_fixture_dato/salida sesiones/_fixture_auditoria/informe sesiones/_fixture_video/trabajo sesiones/_fixture_video/salida .playwright-mcp
	rm -rf sesiones/fixture-[0-9]*
endif

# Sesiones que ningún registro de memoria/ menciona (huérfanas: corridas abandonadas o de prueba).
# Sin BORRAR=1 solo las lista; con BORRAR=1 las borra.
podar:
	@python3 scripts/validate.py --huerfanas $(if $(BORRAR),--borrar,)

test:
	RAPIDO=$(RAPIDO) bash scripts/test.sh

doctor:
	bash scripts/doctor.sh

costo:
	python3 scripts/costo.py $(if $(RUN),--run $(RUN),--ultimo)

contacto:
	@test -n "$(DIR)" || { echo "Uso: make contacto DIR=<carpeta>"; exit 2; }
	node scripts/contacto.js $(DIR)

digesto:
	@test -n "$(SESION)" || { echo "Uso: make digesto SESION=sesiones/<slug> [PARA=guionista|verificador|productor] [EJE=x]"; exit 2; }
	python3 scripts/digesto.py $(SESION) $(if $(PARA),--para $(PARA),) $(if $(EJE),--eje $(EJE),)

fuentes:
	@test -n "$(TEMA)" || { echo "Uso: make fuentes TEMA=\"texto\""; exit 2; }
	python3 scripts/fuentes.py --tema "$(TEMA)" --series

ideas:
	python3 scripts/ideas.py --resumen

calendario:
	python3 scripts/calendario.py --proximas $(if $(DIAS),$(DIAS),30)

informe:
	@test -n "$(DIR)" || { echo "Uso: make informe DIR=<carpeta con informe.json> [PAL=paleta]"; exit 2; }
	python3 scripts/informe.py $(DIR) --check $(if $(PAL),--paleta $(PAL),)

verificacion:
	@test -n "$(SESION)" || { echo "Uso: make verificacion SESION=sesiones/<slug> [EJE=prefijo]"; exit 2; }
	python3 scripts/verificacion.py $(SESION) $(if $(EJE),--eje $(EJE),)

# Rehace una auditoría sobre su sesión tras corregir evaluaciones o verificaciones a mano (sin agentes):
# validar cada eje → puntaje → fichas en el informe → informe.py --check → J1–J5 → avisos R1–R6.
auditoria-rehacer:
	@test -n "$(SESION)" || { echo "Uso: make auditoria-rehacer SESION=sesiones/<slug> [DIR=investigacion/<fecha>-<slug>]"; exit 2; }
	@for f in $(SESION)/evaluacion_*.json; do e=$$(basename $$f .json); e=$${e#evaluacion_}; out=$$(python3 scripts/auditoria.py $(SESION) --validar $$e --verificacion) || { echo "$$out"; exit 1; }; echo "$$out" | tail -1; done
	python3 scripts/auditoria.py $(SESION) --calcular
	python3 scripts/auditoria.py $(SESION) --insertar $(SESION)/informe.json
	python3 scripts/informe.py $(SESION) --check --salida $(SESION)/informe --png $(SESION)/informe/png
	python3 scripts/auditoria.py $(SESION) --justificar $(SESION)/informe.json
	python3 scripts/revision.py $(SESION) --avisos
	@if [ -n "$(DIR)" ]; then cp $(SESION)/informe.json $(DIR)/informe.json && python3 scripts/informe.py $(DIR) --check; fi

informe-ejemplo:
	python3 scripts/informe.py investigacion/ejemplos/dengue-2026 --check

informe-fixture:
	python3 scripts/informe.py sesiones/_fixture --check --salida sesiones/_fixture/informe --png sesiones/_fixture/informe/png

# /video de prueba: hilo del fixture, guion v2 (gancho, golpe con calculo, enlaces, promesa), duración «prueba» (45 s), voz
# falsa (tono por palabra, 0 créditos), todos los gates V1–V10.
FPS ?= 10
VF := sesiones/_fixture_video
video-fixture:
	@test -s sesiones/_fixture/salida/hilo.json || { echo "Primero: python3 scripts/materializar.py sesiones/_fixture && python3 scripts/ensamblar.py sesiones/_fixture --check"; exit 2; }
	rm -rf $(VF)/trabajo $(VF)/salida
	python3 scripts/video.py preparar sesiones/_fixture/salida --duracion prueba --trabajo $(VF)/trabajo --permitir-borrador --sin-rotacion > /dev/null
	cp $(VF)/guion.json $(VF)/ganchos.json $(VF)/seleccion.json $(VF)/trabajo/
	python3 scripts/video.py ganchos $(VF)/trabajo --check
	python3 scripts/video.py ganchos $(VF)/trabajo --usar
	python3 scripts/video.py guion $(VF)/trabajo --check
	python3 scripts/video.py voz-falsa $(VF)/trabajo
	python3 scripts/video.py tiempos $(VF)/trabajo
	python3 scripts/video.py grabar $(VF)/trabajo --fps $(FPS)
	python3 scripts/video.py montar $(VF)/trabajo
	python3 scripts/video.py revisar $(VF)/trabajo
	python3 scripts/video.py grabar $(VF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/video.py montar $(VF)/trabajo --formato 4:5
	python3 scripts/video.py revisar $(VF)/trabajo --formato 4:5
	python3 scripts/video.py entregar $(VF)/trabajo --salida $(VF)/salida

whisper:   # V11: whisper.cpp local; el binario viene de Homebrew (brew install whisper-cpp), el modelo se baja aquí
	python3 scripts/video.py whisper

iconos:   # K3: biblioteca fija de iconos (Lucide, tag fijado en scripts/iconos.py); importar solo si falta el catálogo
	@test -s design/iconos/catalogo.json || python3 scripts/iconos.py --importar
	python3 scripts/iconos.py --check

video-fixture-4x5:   # sobre el trabajo que dejó video-fixture: vuelve a grabar solo la versión 1080×1350 del feed
	python3 scripts/video.py grabar $(VF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/video.py montar $(VF)/trabajo --formato 4:5
	python3 scripts/video.py revisar $(VF)/trabajo --formato 4:5
	python3 scripts/video.py entregar $(VF)/trabajo --salida $(VF)/salida

NF := sesiones/_fixture_noticias
noticias-fixture:   # maqueta de /noticias: noticias de ejemplo con fotos generadas, voz falsa, 9:16 y 4:5
	rm -rf $(NF)/trabajo
	python3 scripts/noticias.py preparar --fecha 2026-10-23 --trabajo $(NF)/trabajo --fixture
	python3 scripts/noticias.py guion $(NF)/trabajo --check
	python3 scripts/noticias.py voz-falsa $(NF)/trabajo
	python3 scripts/noticias.py tiempos $(NF)/trabajo
	python3 scripts/noticias.py grabar $(NF)/trabajo --fps $(FPS)
	python3 scripts/noticias.py montar $(NF)/trabajo
	python3 scripts/noticias.py revisar $(NF)/trabajo
	python3 scripts/noticias.py grabar $(NF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/noticias.py montar $(NF)/trabajo --formato 4:5
	python3 scripts/noticias.py revisar $(NF)/trabajo --formato 4:5

HF := sesiones/_fixture_historia
historia-fixture:   # maqueta de /historia: hechos verificados de ejemplo, fotos generadas, voz falsa, 9:16 y 4:5
	rm -rf $(HF)/trabajo
	python3 scripts/historia.py preparar "La panadería La Espiga de Xela (historia de ejemplo)" --slug la-espiga-maqueta --trabajo $(HF)/trabajo --fixture
	python3 scripts/historia.py hechos $(HF)/trabajo --check
	python3 scripts/historia.py consolidar $(HF)/trabajo
	python3 scripts/historia.py ganchos $(HF)/trabajo --check
	python3 scripts/historia.py ganchos $(HF)/trabajo --usar
	python3 scripts/historia.py guion $(HF)/trabajo --check
	python3 scripts/historia.py voz-falsa $(HF)/trabajo
	python3 scripts/historia.py tiempos $(HF)/trabajo
	python3 scripts/historia.py grabar $(HF)/trabajo --fps $(FPS)
	python3 scripts/historia.py montar $(HF)/trabajo
	python3 scripts/historia.py revisar $(HF)/trabajo
	python3 scripts/historia.py grabar $(HF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/historia.py montar $(HF)/trabajo --formato 4:5
	python3 scripts/historia.py revisar $(HF)/trabajo --formato 4:5

EF := sesiones/_fixture_explica
explica-fixture:   # maqueta de /explica: el interés compuesto con fuentes de ejemplo, ejemplos calculados, voz falsa, 9:16 y 4:5
	rm -rf $(EF)/trabajo $(EF)/salida
	python3 scripts/explica.py preparar "Interés compuesto (maqueta)" --slug interes-compuesto-maqueta --trabajo $(EF)/trabajo --fixture
	python3 scripts/explica.py encuadre $(EF)/trabajo --check
	python3 scripts/explica.py afirmaciones $(EF)/trabajo --check
	python3 scripts/explica.py consolidar $(EF)/trabajo
	python3 scripts/explica.py ganchos $(EF)/trabajo --check
	python3 scripts/explica.py ganchos $(EF)/trabajo --usar
	python3 scripts/explica.py narracion $(EF)/trabajo --check
	python3 scripts/explica.py guion $(EF)/trabajo --check
	python3 scripts/explica.py voz-falsa $(EF)/trabajo
	python3 scripts/explica.py tiempos $(EF)/trabajo
	python3 scripts/explica.py grabar $(EF)/trabajo --fps $(FPS)
	python3 scripts/explica.py montar $(EF)/trabajo
	python3 scripts/explica.py revisar $(EF)/trabajo
	python3 scripts/explica.py grabar $(EF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/explica.py montar $(EF)/trabajo --formato 4:5
	python3 scripts/explica.py revisar $(EF)/trabajo --formato 4:5
	python3 scripts/explica.py entregar $(EF)/trabajo --salida $(EF)/salida

SF := sesiones/_fixture_sabias
sabias-fixture:   # maqueta de /sabias: el dato de prueba de /dato, guion fijo, voz falsa, 9:16 y 4:5
	rm -rf $(SF)/trabajo $(SF)/salida
	python3 scripts/materializar.py sesiones/_fixture_dato > /dev/null
	python3 scripts/ensamblar.py sesiones/_fixture_dato --check > /dev/null
	python3 scripts/sabias.py preparar sesiones/_fixture_dato/salida --trabajo $(SF)/trabajo --fixture > /dev/null
	cp $(SF)/guion.json $(SF)/trabajo/
	python3 scripts/sabias.py guion $(SF)/trabajo --check
	python3 scripts/sabias.py voz-falsa $(SF)/trabajo
	python3 scripts/sabias.py tiempos $(SF)/trabajo
	python3 scripts/sabias.py grabar $(SF)/trabajo --fps $(FPS)
	python3 scripts/sabias.py montar $(SF)/trabajo
	python3 scripts/sabias.py revisar $(SF)/trabajo
	python3 scripts/sabias.py grabar $(SF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/sabias.py montar $(SF)/trabajo --formato 4:5
	python3 scripts/sabias.py revisar $(SF)/trabajo --formato 4:5
	python3 scripts/sabias.py entregar $(SF)/trabajo --salida $(SF)/salida

musica:
	@python3 scripts/video.py musica

informe-catalogo:
	python3 scripts/catalogo_informe.py $(if $(PAL),--paleta $(PAL),)
	python3 scripts/informe.py investigacion/ejemplos/catalogo --check --png investigacion/ejemplos/catalogo/salida/png
