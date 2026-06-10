#!/usr/bin/env bash
# Checks that every tool purgeless needs is installed, with hints when one is missing.
# Exit 0 = good to go. Exit 1 = something's missing. Safe to run any time (read-only).
set -euo pipefail

bold=$(tput bold 2>/dev/null || true)
red=$(tput setaf 1 2>/dev/null || true)
green=$(tput setaf 2 2>/dev/null || true)
yellow=$(tput setaf 3 2>/dev/null || true)
reset=$(tput sgr0 2>/dev/null || true)

missing=0

ok()   { printf "  ${green}✓${reset} %s\n" "$1"; }
warn() { printf "  ${yellow}!${reset} %s\n" "$1"; }
bad()  { printf "  ${red}✗${reset} %s\n" "$1"; missing=1; }

# require <command> <human name> <install hint>
require() {
  local cmd="$1" name="$2" hint="$3"
  if command -v "$cmd" >/dev/null 2>&1; then
    local v
    v=$("$cmd" --version 2>/dev/null | head -1 || true)
    ok "${name}${v:+  ($v)}"
  else
    bad "${name} — not found. Install: ${hint}"
  fi
}

printf "\n${bold}purgeless preflight${reset}\n\n"

require node  "Node.js (>=20)"      "https://nodejs.org or 'brew install node'"
require pnpm  "pnpm (>=9)"          "'corepack enable' or 'npm i -g pnpm'"
require cargo "Rust toolchain"      "https://rustup.rs"
require uv    "uv (Python manager)" "'brew install uv' or https://docs.astral.sh/uv/"

# Platform-specific Tauri system dependencies.
case "$(uname -s)" in
  Darwin)
    if xcode-select -p >/dev/null 2>&1; then
      ok "Xcode Command Line Tools"
    else
      bad "Xcode Command Line Tools — run 'xcode-select --install'"
    fi
    ;;
  Linux)
    # Tauri on Linux needs webkit2gtk + friends; we only warn since package names vary by distro.
    if pkg-config --exists webkit2gtk-4.1 2>/dev/null; then
      ok "webkit2gtk (Tauri runtime deps)"
    else
      warn "webkit2gtk not detected — see https://tauri.app/start/prerequisites/ for your distro"
    fi
    ;;
esac

printf "\n"
if [ "$missing" -ne 0 ]; then
  printf "${red}${bold}Some prerequisites are missing.${reset} Install them and re-run ${bold}make doctor${reset}.\n\n"
  exit 1
fi
printf "${green}${bold}All prerequisites satisfied.${reset}\n\n"
