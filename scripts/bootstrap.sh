#!/usr/bin/env bash
# One command from a fresh clone to a runnable app:
#   checks prerequisites -> installs JS deps -> syncs the Python sidecar venv.
# Idempotent: safe to run again any time deps change.
set -euo pipefail

bold=$(tput bold 2>/dev/null || true)
green=$(tput setaf 2 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)

cd "$(dirname "$0")/.."

step() { printf "\n${bold}» %s${reset}\n" "$1"; }

step "Checking prerequisites"
bash scripts/preflight.sh

step "Installing JS dependencies (pnpm)"
pnpm install

step "Syncing Python sidecar (uv)"
( cd sidecar && uv sync )

printf "\n${green}${bold}Ready.${reset} Start the app with:\n\n  ${bold}make dev${reset}    (or: pnpm tauri dev)\n\n"
printf "Try it on the bundled fixture: ${bold}sidecar/fixtures/papa_leao.3mf${reset}\n"
printf "First run builds Rust (~2 min) and downloads SAM2 weights on first AI segment.\n\n"
