from pathlib import Path
import numpy as np
import trimesh
from purgeless_sidecar.loader import load_mesh
from purgeless_sidecar.segment import segment_geometric


FIXTURE = Path(__file__).parent.parent / "fixtures" / "papa_leao.3mf"


def test_segment_returns_one_region_per_face():
    info = load_mesh(str(FIXTURE))
    result = segment_geometric(info.handle)
    assert len(result.face_region_ids) == info.num_faces
    assert result.num_regions >= 1


def test_segment_region_ids_are_zero_based_dense():
    info = load_mesh(str(FIXTURE))
    result = segment_geometric(info.handle)
    ids = np.array(result.face_region_ids)
    unique = sorted(set(ids.tolist()))
    assert unique[0] == 0
    assert unique == list(range(len(unique)))


def test_segment_merges_stl_duplicate_vertices(tmp_path):
    mesh = trimesh.Trimesh(
        vertices=np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
            ]
        ),
        faces=np.array([[0, 1, 2], [3, 4, 5]]),
        process=False,
    )
    path = tmp_path / "duplicate_vertices.stl"
    mesh.export(path)

    info = load_mesh(str(path))
    result = segment_geometric(info.handle)

    assert result.num_regions == 1
    assert result.face_region_ids == [0, 0]


def test_segment_marks_tiny_components_as_fragments(tmp_path):
    mesh = trimesh.Trimesh(
        vertices=np.array(
            [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 0.0, 0.0],
                [1.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
                [10.0, 10.0, 10.0],
                [10.1, 10.0, 10.0],
                [10.0, 10.1, 10.0],
            ]
        ),
        faces=np.array([[0, 1, 2], [3, 4, 5], [6, 7, 8]]),
        process=False,
    )
    path = tmp_path / "fragment.stl"
    mesh.export(path)

    info = load_mesh(str(path))
    result = segment_geometric(info.handle)

    assert result.num_regions == 2
    assert result.printable_region_ids == [0]
    assert result.region_stats[0]["face_count"] == 2
    assert result.region_stats[0]["is_fragment"] is False
    assert result.region_stats[1]["face_count"] == 1
    assert result.region_stats[1]["is_fragment"] is True
