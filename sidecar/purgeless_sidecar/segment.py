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
    region_stats: list[dict]
    printable_region_ids: list[int]

    def to_dict(self) -> dict:
        return {
            "face_region_ids": self.face_region_ids,
            "num_regions": self.num_regions,
            "region_stats": self.region_stats,
            "printable_region_ids": self.printable_region_ids,
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
    fragment_face_threshold = max(2, int(len(mesh.faces) * 0.0001))
    area_faces = np.asarray(mesh.area_faces, dtype=np.float64)
    total_area = float(area_faces.sum())
    region_stats = []
    printable_region_ids = []
    for region_id, face_ids in enumerate(components):
        face_count = int(len(face_ids))
        area = float(area_faces[face_ids].sum())
        is_fragment = face_count < fragment_face_threshold
        region_stats.append(
            {
                "region_id": int(region_id),
                "face_count": face_count,
                "area": area,
                "area_fraction": area / total_area if total_area > 0 else 0.0,
                "is_fragment": is_fragment,
            }
        )
        if not is_fragment:
            printable_region_ids.append(int(region_id))
    if not printable_region_ids and region_stats:
        largest = max(region_stats, key=lambda item: item["face_count"])
        largest["is_fragment"] = False
        printable_region_ids.append(int(largest["region_id"]))
    return SegmentResult(
        face_region_ids=face_region.tolist(),
        num_regions=int(len(components)),
        region_stats=region_stats,
        printable_region_ids=printable_region_ids,
    )
