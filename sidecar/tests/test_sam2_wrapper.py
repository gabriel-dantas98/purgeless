import numpy as np
from purgeless_sidecar.ai.sam2_wrapper import MockSam2, Sam2Protocol


def test_mock_returns_predictable_masks():
    sam: Sam2Protocol = MockSam2(num_masks=3)
    rgb = np.zeros((64, 64, 3), dtype=np.uint8)
    masks = sam.generate_masks(rgb)
    assert len(masks) == 3
    for m in masks:
        assert m.shape == (64, 64)
        assert m.dtype == bool


def test_mock_masks_are_disjoint_thirds():
    sam = MockSam2(num_masks=3)
    rgb = np.zeros((30, 30, 3), dtype=np.uint8)
    masks = sam.generate_masks(rgb)
    union = np.logical_or.reduce(masks)
    assert union.all(), "every pixel should be assigned to some mask"
    overlap = sum(m.astype(int) for m in masks)
    assert (overlap == 1).all()
