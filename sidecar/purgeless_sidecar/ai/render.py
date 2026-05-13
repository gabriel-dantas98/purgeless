"""Multi-view offscreen render with face_id back-buffer.

Each face is painted with a unique RGB color encoding its face index
(R = lo byte, G = mid byte, B = hi byte). After rendering with flat
shading, pixel colors decode back to face ids.
"""
from __future__ import annotations
from dataclasses import dataclass
import os
import numpy as np
import trimesh

if os.environ.get("PURGELESS_HEADLESS"):
    os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")
import pyrender  # noqa: E402


@dataclass
class View:
    rgb: np.ndarray
    face_ids: np.ndarray
    camera_pose: np.ndarray


def _face_ids_to_colors(num_faces: int) -> np.ndarray:
    ids = np.arange(num_faces + 1, dtype=np.uint32)
    r = (ids & 0xFF).astype(np.uint8)
    g = ((ids >> 8) & 0xFF).astype(np.uint8)
    b = ((ids >> 16) & 0xFF).astype(np.uint8)
    return np.stack([r, g, b], axis=1)


def _decode_face_ids(rgb: np.ndarray) -> np.ndarray:
    r = rgb[..., 0].astype(np.uint32)
    g = rgb[..., 1].astype(np.uint32)
    b = rgb[..., 2].astype(np.uint32)
    encoded = r | (g << 8) | (b << 16)
    out = encoded.astype(np.int64) - 1
    return out


def _orbit_poses(num_views: int, radius: float) -> list[np.ndarray]:
    poses = []
    orbit_n = max(num_views - 2, 1)
    elev = np.deg2rad(15.0)
    for i in range(orbit_n):
        az = (2 * np.pi * i) / orbit_n
        eye = np.array([
            radius * np.cos(elev) * np.cos(az),
            radius * np.sin(elev),
            radius * np.cos(elev) * np.sin(az),
        ])
        poses.append(_look_at(eye, np.zeros(3), np.array([0, 1, 0])))
    if num_views >= 2:
        poses.append(_look_at(np.array([0.0, radius, 0.001]), np.zeros(3), np.array([0, 0, -1])))
        poses.append(_look_at(np.array([0.0, -radius, 0.001]), np.zeros(3), np.array([0, 0, 1])))
    return poses[:num_views]


def _look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    f = target - eye
    f = f / np.linalg.norm(f)
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[:3, 0] = s
    m[:3, 1] = u
    m[:3, 2] = -f
    m[:3, 3] = eye
    return m


def render_views(mesh: trimesh.Trimesh, num_views: int = 12, image_size: int = 512) -> list[View]:
    if len(mesh.faces) == 0:
        raise ValueError("empty mesh")
    if len(mesh.faces) > (1 << 24) - 1:
        raise ValueError(f"too many faces ({len(mesh.faces)}); 24-bit encoding overflow")

    verts = mesh.vertices[mesh.faces.flatten()]
    colors = _face_ids_to_colors(len(mesh.faces))[1:]
    per_vertex_colors = np.repeat(colors, 3, axis=0)
    faces_idx = np.arange(len(verts), dtype=np.int64).reshape(-1, 3)

    pr_mesh = trimesh.Trimesh(vertices=verts, faces=faces_idx, process=False)
    pr_mesh.visual.vertex_colors = np.hstack(
        [per_vertex_colors, np.full((len(per_vertex_colors), 1), 255, dtype=np.uint8)]
    )

    bbox = mesh.bounds
    center = (bbox[0] + bbox[1]) / 2
    extent = np.linalg.norm(bbox[1] - bbox[0])
    radius = float(extent) * 1.2

    centering = np.eye(4)
    centering[:3, 3] = -center

    scene = pyrender.Scene(ambient_light=np.ones(3) * 1.0, bg_color=np.zeros(3))
    scene.add(pyrender.Mesh.from_trimesh(pr_mesh, smooth=False), pose=centering)

    poses = _orbit_poses(num_views, radius)
    cam = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, znear=0.01, zfar=radius * 10)
    cam_node = pyrender.Node(camera=cam)
    scene.add_node(cam_node)

    renderer = pyrender.OffscreenRenderer(image_size, image_size)
    out: list[View] = []
    try:
        for pose in poses:
            scene.set_pose(cam_node, pose=pose)
            color, _depth = renderer.render(
                scene,
                flags=pyrender.RenderFlags.FLAT,
            )
            face_ids = _decode_face_ids(color)
            out.append(View(rgb=color, face_ids=face_ids, camera_pose=pose))
    finally:
        renderer.delete()
    return out
