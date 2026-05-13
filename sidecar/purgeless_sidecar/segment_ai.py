"""Orchestrate render -> SAM -> back-project -> cluster."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import trimesh
from .types import get
from .ai.render import render_views
from .ai.backproject import face_vectors_from_views, cluster_face_vectors
from .ai.sam2_wrapper import Sam2Protocol


@dataclass
class SemanticSegmentResult:
    face_region_ids: list[int]
    num_regions: int
    debug_view_count: int

    def to_dict(self) -> dict:
        return {
            "face_region_ids": self.face_region_ids,
            "num_regions": self.num_regions,
            "debug_view_count": self.debug_view_count,
        }


def segment_semantic(
    handle: str,
    sam: Sam2Protocol,
    num_views: int = 12,
    image_size: int = 512,
    min_cluster_size: int | None = None,
) -> SemanticSegmentResult:
    mesh: trimesh.Trimesh = get(handle)
    views = render_views(mesh, num_views=num_views, image_size=image_size)
    face_id_buffers = [v.face_ids for v in views]
    masks_per_view = [sam.generate_masks(v.rgb) for v in views]
    vectors = face_vectors_from_views(len(mesh.faces), face_id_buffers, masks_per_view)
    mcs = min_cluster_size or max(len(mesh.faces) // 200, 5)
    labels = cluster_face_vectors(vectors, min_cluster_size=mcs)
    labels = _merge_tiny(mesh, labels, threshold_frac=0.02)
    return SemanticSegmentResult(
        face_region_ids=labels.tolist(),
        num_regions=int(len(set(labels.tolist()))),
        debug_view_count=len(views),
    )


def _merge_tiny(mesh: trimesh.Trimesh, labels: np.ndarray, threshold_frac: float) -> np.ndarray:
    """Merge regions whose face count is below threshold into largest adjacent region."""
    counts = np.bincount(labels)
    n = len(mesh.faces)
    tiny = set(int(i) for i, c in enumerate(counts) if c < threshold_frac * n)
    if not tiny:
        return _renumber_dense(labels)
    adj = mesh.face_adjacency
    for src in list(tiny):
        src_faces = np.where(labels == src)[0]
        if len(src_faces) == 0:
            continue
        src_set = set(src_faces.tolist())
        nb_counts: dict[int, int] = {}
        for a, b in adj:
            if a in src_set and b not in src_set:
                nb_counts[int(labels[b])] = nb_counts.get(int(labels[b]), 0) + 1
            elif b in src_set and a not in src_set:
                nb_counts[int(labels[a])] = nb_counts.get(int(labels[a]), 0) + 1
        if not nb_counts:
            continue
        dst = max(nb_counts, key=lambda k: nb_counts[k])
        labels[labels == src] = dst
    return _renumber_dense(labels)


def _renumber_dense(labels: np.ndarray) -> np.ndarray:
    unique = sorted(set(labels.tolist()))
    remap = {old: new for new, old in enumerate(unique)}
    return np.array([remap[int(x)] for x in labels.tolist()], dtype=np.int64)
