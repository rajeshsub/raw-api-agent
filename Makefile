.PHONY: bootstrap test lint dev clean

ifeq ($(OS),Windows_NT)
    VENV_BIN := .venv/Scripts
else
    VENV_BIN := .venv/bin
endif

PYTHON  := $(VENV_BIN)/python
PIP     := $(VENV_BIN)/pip
PYTEST  := $(VENV_BIN)/pytest
UVICORN := $(VENV_BIN)/uvicorn

bootstrap:
	python3.13 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	$(VENV_BIN)/pre-commit install
	cp -n .env.example .env || true
	mkdir -p workspace
	@echo ""
	@echo "Bootstrap complete. Add your API keys to .env before running."

test:
	$(PYTEST) tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

lint:
	$(VENV_BIN)/ruff check app/ tests/
	$(VENV_BIN)/black --check app/ tests/
	$(VENV_BIN)/mypy app/ --strict
	$(VENV_BIN)/bandit -r app/ -c pyproject.toml

dev:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf .venv workspace/* __pycache__ .mypy_cache .ruff_cache .coverage htmlcov
