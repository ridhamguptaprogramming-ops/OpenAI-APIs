.PHONY: venv install setup run test

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
UVICORN := $(BIN)/uvicorn
PYTEST := $(BIN)/pytest

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install '.[dev]'

setup: install
	cp -n .env.example .env || true

run:
	@if [ ! -x "$(UVICORN)" ]; then \
		echo "Missing $(UVICORN). Run: make install"; \
		exit 1; \
	fi
	$(UVICORN) app.main:app --reload

test:
	@if [ ! -x "$(PYTEST)" ]; then \
		echo "Missing $(PYTEST). Run: make install"; \
		exit 1; \
	fi
	$(PYTEST) -q
