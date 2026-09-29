# Hilos · @DerekUrizar — tooling
# `make help` lista los comandos.

SHELL := /bin/bash
GALERIA := templates/.galeria
PALETAS ?= cielo
PALETA ?= cielo

.PHONY: help nuevo render visual catalogo validate tabla pdf ensamblar limpiar test doctor costo contacto digesto fuentes

help:
	@echo "make nuevo T=<plantilla> OUT=<ruta.html> [PALETA=cielo]  ensambla una tarjeta (base + plantilla)"
	@echo "make render FILE=<ruta.html> [OUT=<ruta.png>]            HTML -> PNG 1080x1080 @2x, sin checks"
	@echo "make visual FILE=<ruta.html> [OUT=<ruta.png>]            GATE: render + checks R1-R6 (exit 0 = pasa)"
	@echo "make catalogo [PALETAS=cielo|todas|a,b]                  ensambla y renderiza TODAS las plantillas en $(GALERIA)/"
	@echo "make ensamblar SESION=sesiones/<slug> [OUT=dir] [CHECK=1] sesion -> carpeta de hilo (hilo.html, post.md, datos.json)"
	@echo "make validate                                            valida memoria/*.json y la integridad de hilos/"
	@echo "make tabla URL=<xlsx|html|csv> [OUT=ruta]                descarga y convierte a CSV (sesiones/_descargas/)"
	@echo "make pdf URL=<pdf> [OUT=ruta.pdf]                         descarga y extrae texto (pdftotext -layout)"
	@echo "make test [RAPIDO=1]                                     pruebas: validate, catalogo, fixture, negativos, contar_x, sintaxis de hilo.js"
	@echo "make doctor                                              comprueba node/playwright/python/fuentes/agentes"
	@echo "make costo [RUN=wf_xxx]                                  tokens, herramientas y tiempo por agente de una corrida (default: la última)"
	@echo "make contacto DIR=<carpeta con tuit_N.png>               hoja de contacto contacto.png"
	@echo "make digesto SESION=sesiones/<slug> [PARA=guionista]     resumen compacto de la sesión para agentes"
	@echo "make fuentes TEMA=\"texto\"                                 catálogo de fuentes y series filtrado por tema"
	@echo "make limpiar [SESION=sesiones/<slug>]                    borra $(GALERIA)/, salidas de _fixture y .playwright-mcp/ (o una sesión)"

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
	rm -rf $(GALERIA) sesiones/_fixture/salida .playwright-mcp
endif

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
