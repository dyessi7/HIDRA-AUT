.PHONY: setup test run lint db-schema db-seed clean help

VENV := .venv

CASO ?= AV-2026-0001
ZONA ?= Porvenir Norte
TIPO ?= baja_tension
PRIORIDAD ?= normal

ifeq ($(OS),Windows_NT)
	PYTHON := python
	PY := $(VENV)/Scripts/python.exe
else
	PYTHON := python3
	PY := $(VENV)/bin/python
endif


help:
	@echo "Comandos disponibles:"
	@echo "  make setup                Crea .venv e instala dependencias"
	@echo "  make test                 Ejecuta pytest sobre tests/"
	@echo "  make run                  Ejecuta un caso completo"
	@echo "  make lint                 Ejecuta Ruff + mypy"
	@echo "  make db-schema            Muestra instrucciones para cargar schema.sql"
	@echo "  make db-seed              Muestra instrucciones para cargar seed.sql"
	@echo "  make clean                Limpia caches del proyecto"


setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	@echo "Setup completo."


test:
	$(PY) -m pytest tests/ -v


run:
	$(PY) -m graph.workflow \
		--caso "$(CASO)" \
		--zona "$(ZONA)" \
		--tipo "$(TIPO)" \
		--prioridad "$(PRIORIDAD)"


lint:
	$(PY) -m ruff check .
	$(PY) -m mypy agents tools graph models


db-schema:
	@echo "Abre Supabase SQL Editor y ejecuta el contenido de db/schema.sql"


db-seed:
	@echo "Abre Supabase SQL Editor y ejecuta el contenido de db/seed.sql"


clean:
	$(PY) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', '.mypy_cache', '.ruff_cache']]"