"""Shared dataclasses + an in-process mesh registry."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import uuid


@dataclass
class MeshInfo:
    handle: str
    num_faces: int
    num_vertices: int
    bbox_min: list[float]
    bbox_max: list[float]
    has_color: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Process-local registry: handle -> trimesh.Trimesh
# The sidecar is single-process so a plain dict is fine.
_MESHES: dict[str, Any] = {}


def register(mesh) -> str:
    handle = uuid.uuid4().hex
    _MESHES[handle] = mesh
    return handle


def get(handle: str):
    mesh = _MESHES.get(handle)
    if mesh is None:
        raise KeyError(f"Unknown mesh handle: {handle}")
    return mesh


def drop(handle: str) -> None:
    _MESHES.pop(handle, None)
