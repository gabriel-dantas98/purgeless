"""SAM2 wrapper with lazy import and mock implementation for tests.

The real Sam2Wrapper does `import torch; import sam2` at *call time*,
not module load time. This keeps the sidecar startup fast and lets tests
run without torch / sam2 installed.
"""
from __future__ import annotations
from typing import Protocol
import numpy as np


class Sam2Protocol(Protocol):
    def generate_masks(self, rgb: np.ndarray) -> list[np.ndarray]: ...


class MockSam2:
    """Deterministic fake: splits image into `num_masks` vertical stripes."""

    def __init__(self, num_masks: int = 3) -> None:
        self.num_masks = num_masks

    def generate_masks(self, rgb: np.ndarray) -> list[np.ndarray]:
        h, w = rgb.shape[:2]
        masks: list[np.ndarray] = []
        stripe_w = w / self.num_masks
        for i in range(self.num_masks):
            m = np.zeros((h, w), dtype=bool)
            x0 = int(i * stripe_w)
            x1 = int((i + 1) * stripe_w) if i < self.num_masks - 1 else w
            m[:, x0:x1] = True
            masks.append(m)
        return masks


class Sam2Wrapper:
    """Real SAM2. Loads model on first call."""

    def __init__(self, checkpoint_path: str, device: str | None = None) -> None:
        self.checkpoint_path = checkpoint_path
        self.device = device
        self._generator = None

    def _load(self) -> None:
        if self._generator is not None:
            return
        import torch  # deferred
        from sam2.build_sam import build_sam2  # deferred
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator  # deferred

        device = self.device or (
            "mps" if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available()
            else "cpu"
        )
        cfg = "configs/sam2.1/sam2.1_hiera_b+.yaml"
        model = build_sam2(cfg, self.checkpoint_path, device=device)
        self._generator = SAM2AutomaticMaskGenerator(model)

    def generate_masks(self, rgb: np.ndarray) -> list[np.ndarray]:
        self._load()
        raw = self._generator.generate(rgb)
        return [r["segmentation"].astype(bool) for r in raw]
