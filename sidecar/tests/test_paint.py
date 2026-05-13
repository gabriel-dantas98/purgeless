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


def test_flood_cube_face_strict_tolerance():
    """On a cube, two coplanar triangles share an edge with dihedral ~0.
    Adjacent cube faces share edges with dihedral 90 deg.
    Tolerance 30 deg should pick up only the same cube face (2 tris)."""
    import trimesh
    from purgeless_sidecar.paint import paint_flood
    from purgeless_sidecar.types import register

    cube = trimesh.creation.box(extents=[1, 1, 1])
    handle = register(cube)
    initial = [0] * len(cube.faces)
    new_ids, touched = paint_flood(handle, initial, face_id=0, angle_tolerance_deg=30.0, region_id=9)
    assert touched == 2, f"expected 2 coplanar tris, got {touched}"
    assert new_ids.count(9) == 2


def test_flood_loose_tolerance_paints_everything():
    import trimesh
    from purgeless_sidecar.paint import paint_flood
    from purgeless_sidecar.types import register

    cube = trimesh.creation.box(extents=[1, 1, 1])
    handle = register(cube)
    initial = [0] * len(cube.faces)
    new_ids, touched = paint_flood(handle, initial, face_id=0, angle_tolerance_deg=180.0, region_id=9)
    assert touched == len(cube.faces)


def test_merge_renumbers_densely():
    from purgeless_sidecar.paint import regions_merge

    initial = [0, 0, 2, 3, 4, 1]
    out = regions_merge(initial, src_id=2, dst_id=0)
    assert sorted(set(out)) == [0, 1, 2, 3]
    assert out[2] == out[0]


def test_merge_no_op_when_src_absent():
    from purgeless_sidecar.paint import regions_merge

    initial = [0, 0, 1, 1, 2, 2]
    out = regions_merge(initial, src_id=99, dst_id=0)
    assert out == [0, 0, 1, 1, 2, 2]
