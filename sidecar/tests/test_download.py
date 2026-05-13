import io
from pathlib import Path
from purgeless_sidecar.ai.download import download_with_progress, default_checkpoint_path


def test_default_path_under_app_support():
    p = default_checkpoint_path()
    assert "purgeless" in str(p)
    assert p.name.endswith(".pt")


def test_download_local_source(tmp_path):
    src = tmp_path / "fake_model.bin"
    src.write_bytes(b"x" * 1024)
    dst = tmp_path / "downloaded.bin"
    progress_calls = []
    download_with_progress(
        source=f"file://{src.resolve()}",
        dest=dst,
        on_progress=lambda pct: progress_calls.append(pct),
        chunk_size=128,
    )
    assert dst.exists()
    assert dst.read_bytes() == b"x" * 1024
    assert progress_calls[-1] >= 0.99
    assert any(0.0 < c < 1.0 for c in progress_calls)


def test_skip_if_present(tmp_path):
    dst = tmp_path / "already.bin"
    dst.write_bytes(b"already here")
    calls = []
    download_with_progress(
        source="file:///does/not/exist",
        dest=dst,
        on_progress=lambda pct: calls.append(pct),
    )
    assert dst.read_bytes() == b"already here"
    assert calls == [1.0]
