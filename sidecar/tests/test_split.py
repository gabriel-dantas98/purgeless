from pathlib import Path
from purgeless_sidecar.loader import load_mesh
from purgeless_sidecar.segment import segment_geometric
from purgeless_sidecar.split import split_and_export


FIXTURE = Path(__file__).parent.parent / "fixtures" / "papa_leao.3mf"


def test_split_writes_one_stl_per_region(tmp_path):
    info = load_mesh(str(FIXTURE))
    seg = segment_geometric(info.handle)
    files = split_and_export(info.handle, seg.face_region_ids, str(tmp_path))
    assert len(files) == seg.num_regions
    for f in files:
        p = Path(f)
        assert p.exists()
        assert p.suffix == ".stl"
        assert p.stat().st_size > 0


def test_split_can_export_selected_regions(tmp_path):
    info = load_mesh(str(FIXTURE))
    seg = segment_geometric(info.handle)
    files = split_and_export(
        info.handle,
        seg.face_region_ids,
        str(tmp_path),
        region_ids=[seg.printable_region_ids[0]],
    )

    assert len(files) == 1
    assert Path(files[0]).name == f"region_{seg.printable_region_ids[0]:02d}.stl"


def test_split_removes_stale_region_files(tmp_path):
    stale = tmp_path / "region_99.stl"
    stale.write_text("old")

    info = load_mesh(str(FIXTURE))
    seg = segment_geometric(info.handle)
    split_and_export(
        info.handle,
        seg.face_region_ids,
        str(tmp_path),
        region_ids=[seg.printable_region_ids[0]],
    )

    assert not stale.exists()
