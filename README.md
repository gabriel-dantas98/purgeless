<p align="center">
  <img src="./assets/header.svg" alt="purgeless — AI meshes → printable parts, zero AMS purge" />
</p>

<h1 align="center">purgeless</h1>

<p align="center">
  Desktop app that takes AI-generated 3D meshes and prepares them for multi-color printing without purge waste.
</p>

<p align="center">
  <em>Multi-part split or AMS-optimized 3MF, your choice.</em>
</p>

<p align="center">
  <a href="./LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg"></a>
  <img alt="Platform: macOS" src="https://img.shields.io/badge/platform-macOS-lightgrey.svg">
  <img alt="Status: v0.2" src="https://img.shields.io/badge/status-v0.2-a78bfa.svg">
</p>

---

## Why

Generative AI builds meshes for looks, not for fabrication. Tools like Tripo, Meshy,
Rodin, Hunyuan3D, and Trellis hand you a gorgeous figurine that prints like garbage on a
Bambu AMS. Every color change dumps filament into purge.

`purgeless` is the step between **"AI gave me a model"** and **"I press print"**.

## What v0.1 does

- Loads `.stl`, `.3mf`, `.glb`, `.obj`, `.fbx`
- Renders the mesh in a 3D viewport (orbit / zoom)
- Geometric segmentation via connected components
- Color-codes each region in the viewport
- Exports one STL per region, ready to drop into Bambu Studio

AI semantic segmentation, manual painting, AMS-optimize mode, and procedural connectors
landed later or are still planned — see the [roadmap](./ROADMAP.md).

## What v0.2 adds

- **AI segment**: multi-view SAM2 (12 views) plus face back-projection produces semantic
  regions automatically. The first call downloads ~155 MB of SAM2 weights into
  `~/Library/Application Support/purgeless/models/`. Set `PURGELESS_MOCK_SAM=1` to skip
  the real model during dev.
- **Brush** and **Flood** paint modes on the viewport — click-drag to assign faces to the
  active region; `[` and `]` resize the brush.
- **RegionsPanel**: rename, merge, and select regions. Cmd+Z undoes the last operation
  (brush, flood, merge, rename, add).

If `pyrender` can't initialize a GL context on your machine, install the OSMesa software
backend and force it on:

```bash
cd sidecar && uv pip install 'pyrender[osmesa]'   # then run with PURGELESS_HEADLESS=1
```

### Known v0.2 limitations

- **AI segment crashes on the second call** in the same sidecar process. The Cocoa GL
  context can't be recreated on macOS, so restart the app between AI runs for now. Fix
  planned for v0.2.1 via a singleton renderer or a moderngl swap.

## Quickstart

Install the [prerequisites](./CONTRIBUTING.md#prerequisites) (Node ≥ 20, pnpm, Rust, uv),
then:

```bash
git clone https://github.com/gabriel-dantas98/purgeless.git
cd purgeless
make bootstrap   # checks prereqs, installs JS deps, syncs the Python venv
make dev         # runs the app (first build compiles Rust, ~2 min)
```

No `make`? The same two steps are `pnpm bootstrap` then `pnpm tauri dev`. Run
`make doctor` any time to check your toolchain.

Try it on the bundled fixture: `sidecar/fixtures/papa_leao.3mf`.

## Stack

| Layer | Tech |
|---|---|
| Shell | Tauri 2 (Rust) |
| Frontend | React 19 + TypeScript + Vite |
| 3D viewport | three.js + @react-three/fiber + @react-three/drei |
| Sidecar | Python 3.11 + trimesh + open3d + manifold3d + numpy |
| IPC | JSON-RPC over stdio |

## Contributing

Setup, the dev loop, architecture, and conventions live in
**[CONTRIBUTING.md](./CONTRIBUTING.md)**. The short version:

```bash
make check   # typecheck (TS) + cargo check (Rust) + pytest (Python) — run before a PR
```

Found a model that segments badly, or a printer setup we haven't covered? Open an issue.

## License

[Apache-2.0](./LICENSE).

---

<p align="center">
  made by <a href="https://gdantas.com.br">Gabriel Dantas</a>
</p>
