"""Build per-face feature vectors from multi-view masks; cluster with HDBSCAN."""
from __future__ import annotations
import numpy as np
import hdbscan


def face_vectors_from_views(
    num_faces: int,
    face_id_buffers: list[np.ndarray],
    masks_per_view: list[list[np.ndarray]],
) -> np.ndarray:
    """For each face, build a binary vector indicating which masks cover it.

    Concatenation order: view 0 mask 0, view 0 mask 1, ..., view 1 mask 0, ...
    A face is considered "in" a mask if the majority of its rendered pixels
    fall inside that mask.
    """
    assert len(face_id_buffers) == len(masks_per_view)
    cols: list[np.ndarray] = []
    for fid_buf, masks in zip(face_id_buffers, masks_per_view):
        flat_fids = fid_buf.flatten()
        total = np.bincount(
            np.where(flat_fids >= 0, flat_fids, num_faces),
            minlength=num_faces + 1,
        )[:num_faces]
        for mask in masks:
            flat_in_mask = (mask.flatten() & (flat_fids >= 0))
            in_mask = np.bincount(
                np.where(flat_in_mask, flat_fids, num_faces),
                minlength=num_faces + 1,
            )[:num_faces]
            col = (in_mask * 2 >= total) & (total > 0)
            cols.append(col.astype(np.float64))
    if not cols:
        return np.zeros((num_faces, 0), dtype=np.float64)
    return np.stack(cols, axis=1)


def cluster_face_vectors(vectors: np.ndarray, min_cluster_size: int = 30) -> np.ndarray:
    """HDBSCAN clustering on face feature vectors.

    Returns dense label array (shape == num_faces). Noise points (-1 from
    HDBSCAN) are reassigned to the nearest cluster centroid in vector space.
    """
    if vectors.shape[1] == 0:
        return np.zeros(vectors.shape[0], dtype=np.int64)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=max(min_cluster_size, 2),
        metric="hamming",
        allow_single_cluster=True,
    )
    raw = clusterer.fit_predict(vectors)
    labels = raw.copy().astype(np.int64)
    if (labels == -1).any() and (labels >= 0).any():
        centroids = {}
        for c in set(labels.tolist()) - {-1}:
            centroids[c] = vectors[labels == c].mean(axis=0)
        for i in np.where(labels == -1)[0]:
            best = min(centroids, key=lambda c: np.linalg.norm(vectors[i] - centroids[c]))
            labels[i] = best
    if (labels == -1).all():
        labels[:] = 0
    unique = sorted(set(labels.tolist()))
    remap = {old: new for new, old in enumerate(unique)}
    return np.array([remap[l] for l in labels.tolist()], dtype=np.int64)
