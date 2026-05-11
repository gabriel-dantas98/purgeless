from pathlib import Path
import numpy as np
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
