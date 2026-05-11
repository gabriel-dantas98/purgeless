"""Load a mesh from disk into the registry."""
from __future__ import annotations
import trimesh
from .types import MeshInfo, register


def load_mesh(path: str) -> MeshInfo:
    scene_or_mesh = trimesh.load(path, force="mesh", process=False)
    if not isinstance(scene_or_mesh, trimesh.Trimesh):
        # Fallback: flatten a Scene to a single Trimesh by concatenating geometries.
        if isinstance(scene_or_mesh, trimesh.Scene):
            geoms = list(scene_or_mesh.dump())
            if not geoms:
                raise ValueError("Scene contains no geometry")
            mesh = trimesh.util.concatenate(geoms)
        else:
            raise ValueError(f"Unsupported mesh type: {type(scene_or_mesh)}")
    else:
        mesh = scene_or_mesh
    handle = register(mesh)
    bbox = mesh.bounds  # shape (2, 3): [min, max]
    has_color = (
        mesh.visual is not None
        and getattr(mesh.visual, "vertex_colors", None) is not None
        and len(mesh.visual.vertex_colors) == len(mesh.vertices)
    )
    return MeshInfo(
        handle=handle,
        num_faces=int(len(mesh.faces)),
        num_vertices=int(len(mesh.vertices)),
        bbox_min=[float(x) for x in bbox[0]],
        bbox_max=[float(x) for x in bbox[1]],
        has_color=bool(has_color),
    )
