# Quick dev commands. Run from the repo root.
VENV := .venv/bin
LITE := lite

.PHONY: help install lint fmt fix sort-imports typecheck test check

help:
	@echo "make install  - install ptlite with dev deps into .venv"
	@echo "make lint     - ruff lint + format check (no changes)"
	@echo "make fmt      - ruff format + autofix lint issues"
	@echo "make typecheck - mypy strict type check"
	@echo "make test     - run pytest"
	@echo "make sort-imports - reorder imports in place (ruff I rules)"
	@echo "make check    - sort imports, lint, typecheck, then test (run before committing)"

install:
	uv pip install --python $(VENV)/python -e "$(LITE)[dev]"

lint:
	cd $(LITE) && ../$(VENV)/ruff check . && ../$(VENV)/ruff format --check .

fmt fix:
	cd $(LITE) && ../$(VENV)/ruff check --fix . && ../$(VENV)/ruff format .

sort-imports:
	cd $(LITE) && ../$(VENV)/ruff check --select I --fix --quiet .

typecheck:
	cd $(LITE) && ../$(VENV)/mypy

test:
	cd $(LITE) && ../$(VENV)/pytest -q

# Sorts imports in place first (the only step that edits files), then runs every step even if an earlier one fails, so you always see all results; exits nonzero if any failed.
check:
	@lint=0; types=0; test=0; \
	$(MAKE) --no-print-directory sort-imports; \
	echo "=== lint ==="; $(MAKE) --no-print-directory lint || lint=1; \
	echo; echo "=== typecheck ==="; $(MAKE) --no-print-directory typecheck || types=1; \
	echo; echo "=== test ==="; $(MAKE) --no-print-directory test || test=1; \
	echo; echo "=== summary ==="; \
	[ $$lint -eq 0 ] && echo "lint: ok" || echo "lint: FAILED"; \
	[ $$types -eq 0 ] && echo "typecheck: ok" || echo "typecheck: FAILED"; \
	[ $$test -eq 0 ] && echo "test: ok" || echo "test: FAILED"; \
	[ $$lint -eq 0 ] && [ $$types -eq 0 ] && [ $$test -eq 0 ]
