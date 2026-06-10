# purgeless — developer entrypoints.
# Run `make` with no target for the menu.
.DEFAULT_GOAL := help
.PHONY: help bootstrap doctor dev build test typecheck check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "} {printf "  \033[1m%-12s\033[0m %s\n", $$1, $$2}'

bootstrap: ## Fresh clone -> runnable: check prereqs, install JS + Python deps
	@bash scripts/bootstrap.sh

doctor: ## Check that all prerequisites are installed
	@bash scripts/preflight.sh

dev: ## Run the desktop app (Tauri + Vite + Python sidecar)
	pnpm tauri dev

build: ## Build a production app bundle
	pnpm tauri build

test: ## Run the Python sidecar test suite
	cd sidecar && uv run pytest -v

typecheck: ## TypeScript type-check (no emit)
	pnpm exec tsc --noEmit

check: typecheck ## Typecheck (TS) + cargo check (Rust) + pytest (Python)
	cd src-tauri && cargo check
	cd sidecar && uv run pytest -q

clean: ## Remove build artifacts and dependency caches
	rm -rf dist node_modules src-tauri/target sidecar/.venv sidecar/.pytest_cache
