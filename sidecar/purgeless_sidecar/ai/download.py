"""SAM2 weights downloader. Progress callback fires every ~5% of bytes."""
from __future__ import annotations
from pathlib import Path
from typing import Callable
import os
import sys
import urllib.request


DEFAULT_URL = (
    "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt"
)


def default_checkpoint_path() -> Path:
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return root / "purgeless" / "models" / "sam2.1_base_plus.pt"


def download_with_progress(
    source: str,
    dest: Path,
    on_progress: Callable[[float], None] | None = None,
    chunk_size: int = 1 << 20,
) -> Path:
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        if on_progress:
            on_progress(1.0)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(source) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        last_pct = -1.0
        with open(tmp, "wb") as fh:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)
                if on_progress and total > 0:
                    pct = downloaded / total
                    if pct - last_pct >= 0.05 or pct >= 1.0:
                        on_progress(pct)
                        last_pct = pct
    tmp.replace(dest)
    if on_progress:
        on_progress(1.0)
    return dest
