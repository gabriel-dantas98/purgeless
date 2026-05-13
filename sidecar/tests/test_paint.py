import trimesh
import numpy as np
from purgeless_sidecar.types import register
from purgeless_sidecar.paint import paint_brush


def test_brush_radius_zero_paints_one_face():
    cube = trimesh.creation.box(extents=[1, 1, 1])
    handle = register(cube)
    initial = [0] * len(cube.faces)
    new_ids, touched = paint_brush(handle, initial, face_id=0, brush_radius=0, region_id=7)
    assert touched == 1
    assert new_ids[0] == 7
    assert new_ids.count(7) == 1


def test_brush_radius_one_grows():
    cube = trimesh.creation.box(extents=[1, 1, 1])
    handle = register(cube)
    initial = [0] * len(cube.faces)
    new_ids, touched = paint_brush(handle, initial, face_id=0, brush_radius=1, region_id=7)
    assert touched >= 2


def test_brush_radius_huge_paints_everything():
    cube = trimesh.creation.box(extents=[1, 1, 1])
    handle = register(cube)
    initial = [0] * len(cube.faces)
    new_ids, touched = paint_brush(handle, initial, face_id=0, brush_radius=1000, region_id=7)
    assert touched == len(cube.faces)
    assert all(r == 7 for r in new_ids)
