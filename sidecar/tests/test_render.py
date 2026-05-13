import numpy as np
import trimesh
from purgeless_sidecar.ai.render import render_views


def test_cube_renders_n_views():
    cube = trimesh.creation.box(extents=[1, 1, 1])
    views = render_views(cube, num_views=6, image_size=128)
    assert len(views) == 6
    for v in views:
        assert v.rgb.shape == (128, 128, 3)
        assert v.face_ids.shape == (128, 128)
        unique = set(v.face_ids.flatten().tolist())
        assert -1 in unique or len(unique) <= 13
        assert (v.face_ids >= 0).any()


def test_face_id_encoding_roundtrip():
    cube = trimesh.creation.box(extents=[1, 1, 1])
    views = render_views(cube, num_views=1, image_size=64)
    fids = views[0].face_ids
    visible = fids[fids >= 0]
    assert (visible < len(cube.faces)).all()
