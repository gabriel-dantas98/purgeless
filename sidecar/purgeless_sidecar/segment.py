"""Geometric segmentation: connected components on face adjacency.

v0.1 uses ONLY connected components. Curvature-based split comes in v0.2.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import trimesh
from .types import get


@dataclass
class SegmentResult:
    face_region_ids: list[int]
    num_regions: int

    def to_dict(self) -> dict:
        return {
            "face_region_ids": self.face_region_ids,
            "num_regions": self.num_regions,
        }


def segment_geometric(handle: str) -> SegmentResult:
    mesh: trimesh.Trimesh = get(handle)
    components = trimesh.graph.connected_components(
        edges=mesh.face_adjacency,
        nodes=np.arange(len(mesh.faces)),
        engine="scipy",
    )
    face_region = np.full(len(mesh.faces), -1, dtype=np.int64)
    for region_id, face_ids in enumerate(components):
        face_region[face_ids] = region_id
    assert (face_region >= 0).all(), "every face should be assigned"
    return SegmentResult(
        face_region_ids=face_region.tolist(),
        num_regions=int(len(components)),
    )
