"""Server-side paint operations on face_adjacency."""
from __future__ import annotations
from collections import defaultdict, deque
import numpy as np
import trimesh
from .types import get


def _adjacency_lookup(mesh: trimesh.Trimesh) -> dict[int, list[int]]:
    adj: dict[int, list[int]] = defaultdict(list)
    for a, b in mesh.face_adjacency:
        adj[int(a)].append(int(b))
        adj[int(b)].append(int(a))
    return adj


def paint_brush(
    handle: str,
    current_regions: list[int],
    face_id: int,
    brush_radius: int,
    region_id: int,
) -> tuple[list[int], int]:
    """BFS up to brush_radius hops on face_adjacency, assign region_id."""
    mesh: trimesh.Trimesh = get(handle)
    if face_id < 0 or face_id >= len(mesh.faces):
        raise ValueError(f"face_id out of range: {face_id}")
    if len(current_regions) != len(mesh.faces):
        raise ValueError("current_regions length must equal num_faces")
    adj = _adjacency_lookup(mesh)

    visited: dict[int, int] = {face_id: 0}
    queue = deque([face_id])
    while queue:
        cur = queue.popleft()
        depth = visited[cur]
        if depth >= brush_radius:
            continue
        for nb in adj.get(cur, ()):
            if nb not in visited:
                visited[nb] = depth + 1
                queue.append(nb)

    out = list(current_regions)
    for f in visited:
        out[f] = region_id
    return out, len(visited)


def paint_flood(
    handle: str,
    current_regions: list[int],
    face_id: int,
    angle_tolerance_deg: float,
    region_id: int,
) -> tuple[list[int], int]:
    """BFS that stops crossing edges with dihedral angle > tolerance."""
    mesh: trimesh.Trimesh = get(handle)
    if face_id < 0 or face_id >= len(mesh.faces):
        raise ValueError(f"face_id out of range: {face_id}")
    if len(current_regions) != len(mesh.faces):
        raise ValueError("current_regions length must equal num_faces")

    fa = mesh.face_adjacency
    angles = np.rad2deg(mesh.face_adjacency_angles)
    edge_angle: dict[tuple[int, int], float] = {}
    for (a, b), ang in zip(fa, angles):
        edge_angle[(int(a), int(b))] = float(ang)
        edge_angle[(int(b), int(a))] = float(ang)
    adj = _adjacency_lookup(mesh)

    visited = {face_id}
    queue = deque([face_id])
    while queue:
        cur = queue.popleft()
        for nb in adj.get(cur, ()):
            if nb in visited:
                continue
            ang = edge_angle.get((cur, nb), 180.0)
            if ang <= angle_tolerance_deg:
                visited.add(nb)
                queue.append(nb)

    out = list(current_regions)
    for f in visited:
        out[f] = region_id
    return out, len(visited)


def regions_merge(face_region_ids: list[int], src_id: int, dst_id: int) -> list[int]:
    """Reassign every face from src_id to dst_id; renumber to dense ids."""
    arr = np.array(face_region_ids, dtype=np.int64)
    arr[arr == src_id] = dst_id
    unique = sorted(set(arr.tolist()))
    remap = {old: new for new, old in enumerate(unique)}
    return [remap[int(x)] for x in arr.tolist()]
