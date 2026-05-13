"""Split a mesh by face->region mapping and export each region as an STL."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import trimesh
from .types import get


def split_and_export(
    handle: str,
    face_region_ids: list[int],
    out_dir: str,
    region_ids: list[int] | None = None,
) -> list[str]:
    mesh: trimesh.Trimesh = get(handle)
    ids = np.asarray(face_region_ids, dtype=np.int64)
    if len(ids) != len(mesh.faces):
        raise ValueError("face_region_ids length must equal num_faces")
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    for stale in out_path.glob("region_*.stl"):
        stale.unlink()
    written: list[str] = []
    regions = sorted(set(ids.tolist()) if region_ids is None else region_ids)
    for region_id in regions:
        face_mask = ids == region_id
        submesh = mesh.submesh([np.where(face_mask)[0]], append=True)
        if not isinstance(submesh, trimesh.Trimesh):
            continue
        filename = out_path / f"region_{region_id:02d}.stl"
        submesh.export(filename, file_type="stl")
        written.append(str(filename))
    return written
