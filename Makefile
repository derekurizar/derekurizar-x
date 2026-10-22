# Hilos · @DerekUrizar — tooling
# `make help` lista los comandos.

SHELL := /bin/bash
GALERIA := templates/.galeria
PALETAS ?= cielo
PALETA ?= cielo

.PHONY: help nuevo render visual catalogo validate tabla pdf ensamblar limpiar test doctor costo contacto digesto fuentes ideas calendario informe informe-ejemplo informe-catalogo informe-fixture verificacion auditoria-rehacer podar video-fixture video-fixture-4x5 musica whisper iconos

help:
	@echo "make nuevo T=<plantilla> OUT=<ruta.html> [PALETA=cielo]  ensambla una tarjeta (base + plantilla)"
	@echo "make render FILE=<ruta.html> [OUT=<ruta.png>]            HTML -> PNG 1080x1080 @2x, sin checks"
	@echo "make visual FILE=<ruta.html> [OUT=<ruta.png>]            GATE: render + checks R1-R6 (exit 0 = pasa)"
	@echo "make catalogo [PALETAS=cielo|todas|a,b]                  ensambla y renderiza TODAS las plantillas en $(GALERIA)/"
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
	python3 scripts/nuevo_visual.py --galeria $(GALERIA) --paletas $(PALETAS)
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
	python3 scripts/video.py preparar sesiones/_fixture/salida --duracion prueba --trabajo $(VF)/trabajo --permitir-borrador > /dev/null
	cp $(VF)/guion.json $(VF)/trabajo/guion.json
	python3 scripts/video.py guion $(VF)/trabajo --check
	python3 scripts/video.py voz-falsa $(VF)/trabajo
	python3 scripts/video.py tiempos $(VF)/trabajo
	python3 scripts/video.py grabar $(VF)/trabajo --fps $(FPS)
	python3 scripts/video.py montar $(VF)/trabajo
	python3 scripts/video.py revisar $(VF)/trabajo
	python3 scripts/video.py entregar $(VF)/trabajo --salida $(VF)/salida

whisper:   # V11: whisper.cpp local; el binario viene de Homebrew (brew install whisper-cpp), el modelo se baja aquí
	python3 scripts/video.py whisper

iconos:   # K3: biblioteca fija de iconos (Lucide, tag fijado en scripts/iconos.py); importar solo si falta el catálogo
	@test -s design/iconos/catalogo.json || python3 scripts/iconos.py --importar
	python3 scripts/iconos.py --check

video-fixture-4x5:   # sobre el trabajo que dejó video-fixture: la versión 1080×1350 para el feed
	python3 scripts/video.py grabar $(VF)/trabajo --fps $(FPS) --formato 4:5
	python3 scripts/video.py montar $(VF)/trabajo --formato 4:5
	python3 scripts/video.py revisar $(VF)/trabajo --formato 4:5
	python3 scripts/video.py entregar $(VF)/trabajo --salida $(VF)/salida

musica:
	@python3 scripts/video.py musica

informe-catalogo:
	python3 scripts/catalogo_informe.py $(if $(PAL),--paleta $(PAL),)
	python3 scripts/informe.py investigacion/ejemplos/catalogo --check --png investigacion/ejemplos/catalogo/salida/png
