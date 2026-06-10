# Contributing to purgeless

Thanks for taking a look. purgeless is a desktop app that turns AI-generated 3D meshes
into parts you can actually print on a Bambu AMS without bleeding filament into purge.
This guide gets you from a fresh clone to a running dev build, and covers the
conventions and the sharp edges worth knowing before you send a PR.

## Prerequisites

Install these once. `make doctor` checks all of them and tells you what's missing.

| Tool | Version | Why | Install |
|---|---|---|---|
| **Node.js** | ≥ 20 | Vite + frontend tooling | [nodejs.org](https://nodejs.org) |
| **pnpm** | ≥ 9 | JS package manager | `corepack enable` |
| **Rust** | stable | Tauri shell | [rustup.rs](https://rustup.rs) |
| **uv** | latest | Python sidecar venv | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |

Platform system deps for Tauri:

- **macOS** — Xcode Command Line Tools (`xcode-select --install`). This is the primary
  development target.
- **Linux** — `webkit2gtk` and the GTK build deps; see the
  [Tauri prerequisites](https://tauri.app/start/prerequisites/) for your distro.

## Setup

```bash
git clone https://github.com/gabriel-dantas98/purgeless.git
cd purgeless
make bootstrap   # checks prereqs, installs JS deps, syncs the Python venv
make dev         # runs the app (first build compiles Rust, ~2 min)
```

`make bootstrap` is idempotent — run it again whenever dependencies change. If you'd
rather not use `make`, the same steps are `pnpm bootstrap` then `pnpm tauri dev`.

Open the bundled fixture `sidecar/fixtures/papa_leao.3mf` to see the full flow:
import → segment → split → export.

## Dev loop

| Command | What it does |
|---|---|
| `make dev` | Run the app (Tauri shell + Vite HMR + Python sidecar) |
| `make test` | Python sidecar test suite (`pytest`) |
| `make typecheck` | TypeScript type-check, no emit |
| `make check` | Typecheck + `cargo check` + `pytest` — run this before a PR |
| `make build` | Production app bundle |
| `make clean` | Remove build artifacts and dep caches |

The frontend hot-reloads. Changes to the Rust shell or the Python sidecar need a
restart of `make dev`.

## How it fits together

```
┌─────────────────────────┐     JSON-RPC over stdio     ┌──────────────────────────┐
│  Tauri shell (Rust)      │ ─────────────────────────►  │  Python sidecar          │
│  src-tauri/              │                             │  sidecar/purgeless_      │
│   lib.rs   — commands    │  ◄───  notifications  ───   │   sidecar/               │
│   sidecar.rs — subprocess│     (progress events)       │   server.py — RPC router │
└───────────┬─────────────┘                             │   loader / segment /     │
            │ Tauri events                               │   segment_ai / paint /   │
            ▼                                            │   split / types          │
┌─────────────────────────┐                             └──────────────────────────┘
│  React + three.js (src/) │     The sidecar owns all geometry: loading, segmentation,
│   Viewport, RegionsPanel │     painting, and export. The shell spawns it with
│   ipc/sidecar.ts wrappers│     `uv run python -m purgeless_sidecar.server` and pipes
└─────────────────────────┘     typed requests through `src/ipc/sidecar.ts`.
```

Adding a feature that touches geometry usually means three coordinated edits:

1. A new method in `sidecar/purgeless_sidecar/server.py` (register it in `METHODS`).
2. A typed wrapper in `src/ipc/sidecar.ts`.
3. UI in `src/components/` that calls the wrapper.

## Conventions

- **Branches** — `feat/…`, `fix/…`, `docs/…`, `chore/…` off `main`.
- **Commits** — [Conventional Commits](https://www.conventionalcommits.org/) with a
  scope, matching the existing history: `feat(viewport): …`, `fix(actionbar): …`,
  `test(sidecar): …`.
- **PRs** — keep them focused, run `make check` first, and describe what you verified
  (which fixture, which mode).

## Sharp edges

- **AI segment crashes on the second call** in the same session on macOS. The Cocoa GL
  context can't be recreated, so restart the app between AI runs for now. A fix is planned
  for v0.2.1.
- **SAM2 weights** (~155 MB) download to `~/Library/Application Support/purgeless/models/`
  on the first AI segment. Set `PURGELESS_MOCK_SAM=1` to skip the real model during dev.
- **No GL context?** If `pyrender` can't initialize one, install the software backend
  (`cd sidecar && uv pip install 'pyrender[osmesa]'`) and run with `PURGELESS_HEADLESS=1`.

See the [roadmap](./ROADMAP.md) for where things are headed.
