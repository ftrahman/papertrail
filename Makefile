# Quick dev commands. Run from the repo root.
VENV := .venv/bin
LITE := lite

.PHONY: help install lint fmt fix test check

help:
	@echo "make install  - install ptlite with dev deps into .venv"
	@echo "make lint     - ruff lint + format check (no changes)"
	@echo "make fmt      - ruff format + autofix lint issues"
	@echo "make test     - run pytest"
	@echo "make check    - lint then test (run before committing)"

install:
	$(VENV)/python -m pip install -e "$(LITE)[dev]"

lint:
	cd $(LITE) && ../$(VENV)/ruff check . && ../$(VENV)/ruff format --check .

fmt fix:
	cd $(LITE) && ../$(VENV)/ruff check --fix . && ../$(VENV)/ruff format .

test:
	cd $(LITE) && ../$(VENV)/pytest -q

# Runs lint and tests even if lint fails, so you always see both; exits nonzero if either failed.
check:
	@lint=0; test=0; \
	echo "=== lint ==="; $(MAKE) --no-print-directory lint || lint=1; \
	echo; echo "=== test ==="; $(MAKE) --no-print-directory test || test=1; \
	echo; echo "=== summary ==="; \
	[ $$lint -eq 0 ] && echo "lint: ok" || echo "lint: FAILED"; \
	[ $$test -eq 0 ] && echo "test: ok" || echo "test: FAILED"; \
	[ $$lint -eq 0 ] && [ $$test -eq 0 ]
