# LeashMap — top-level orchestration.
# One command to test the whole system, or run the end-to-end demo.
#
# Prereqs on PATH: uv (server/simulator), flutter (app), make + a C compiler
# (firmware). See ARCHITECTURE.md.

MODE ?= exit_zone

.PHONY: test test-server test-simulator test-firmware test-app demo clean help

help:
	@echo "make test            run every test suite (server, simulator, firmware, app)"
	@echo "make test-server     server pytest (FastAPI + SQLite)"
	@echo "make test-simulator  simulator pytest"
	@echo "make test-firmware   firmware host tests (make -C firmware test)"
	@echo "make test-app        flutter analyze + test"
	@echo "make demo [MODE=...] end-to-end demo (exit_zone|low_battery|offline|drift|lost|normal)"
	@echo "make clean           remove build artifacts and the local sqlite db"

test: test-server test-simulator test-firmware test-app
	@echo "\nAll suites passed."

test-server:
	@echo "== server =="
	cd server && uv sync --quiet && uv run pytest -q

test-simulator:
	@echo "== simulator =="
	cd simulator && uv sync --quiet && uv run pytest -q

test-firmware:
	@echo "== firmware =="
	$(MAKE) -C firmware test

test-app:
	@echo "== app =="
	cd app && flutter pub get && flutter analyze && flutter test

demo:
	bash scripts/demo.sh $(MODE)

clean:
	$(MAKE) -C firmware clean
	rm -f server/leashmap.db
