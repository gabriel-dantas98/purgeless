from pathlib import Path
from purgeless_sidecar.loader import load_mesh


FIXTURE = Path(__file__).parent.parent / "fixtures" / "papa_leao.3mf"


def test_load_papa_leao():
    info = load_mesh(str(FIXTURE))
    assert info.num_faces > 0
    assert info.num_vertices > 0
    assert len(info.bbox_min) == 3
    assert len(info.bbox_max) == 3
    assert info.has_color in (True, False)


def test_load_returns_handle():
    info = load_mesh(str(FIXTURE))
    assert isinstance(info.handle, str) and len(info.handle) > 0
