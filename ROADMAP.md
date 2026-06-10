# Roadmap

purgeless sits between *"AI gave me a model"* and *"I press print"*. The path below
goes from a working geometric splitter to a full prep pipeline with two output modes:
**split** (one printable part per region, plus connectors) and **AMS-optimize** (the
whole model, color regions reorganized and the AMS swap sequence tuned to waste less
filament).

Shipped and planned milestones:

| Version | Status | Scope |
|---|---|---|
| **v0.1** | ✅ shipped | Tauri shell, 3D viewport, mesh import, geometric segmentation (connected components), split, one STL per region. Runs on `papa_leao.3mf`. |
| **v0.2** | ✅ shipped | AI segmentation (multi-view SAM2 + face back-projection), manual brush/flood paint, regions panel with merge/rename/undo. |
| **v0.2.1** | next | Fix the AI-segment second-call crash (singleton renderer or moderngl swap — see [Known limitations](./README.md#known-v02-limitations)). |
| **v0.3** | planned | Procedural connectors — pegs, magnets, dovetails — so split parts snap back together. |
| **v0.4** | planned | AMS-optimize mode + 3MF export tuned for Bambu Studio / OrcaSlicer. |
| **v0.5** | planned | Self-test corpus + per-model HTML reports. |
| **v0.6** | planned | Guided wizard and onboarding. |

## Open questions

- **AI model.** v0.2 renders multiple views and re-projects SAM2 masks onto faces.
  Worth revisiting against mesh-native approaches (Point-SAM, SAM-Mesh) once there's a
  corpus to measure against.
- **Connectors.** Split parts need a join story — peg/magnet placement, diameters, and
  tolerances that survive real prints.

Have a model that segments badly or a printer setup we haven't covered? Open an issue.
Edge cases drive this roadmap more than the version numbers do.
