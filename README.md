# purgeless

Desktop app that takes AI-generated 3D meshes and prepares them for multi-color printing without purge waste.

See full design: `gdantas-control-plane/docs/superpowers/specs/2026-05-11-purgeless-design.md`.

## v0.1 quickstart

```bash
pnpm install
cd sidecar && uv sync && cd ..
pnpm tauri dev
```

## Stack

Tauri 2 + React + three.js + Python sidecar (trimesh + open3d).
