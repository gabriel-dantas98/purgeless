import trimesh
from purgeless_sidecar.types import register
from purgeless_sidecar.segment_ai import segment_semantic
from purgeless_sidecar.ai.sam2_wrapper import MockSam2


def test_segment_semantic_with_mock_returns_assignments():
    cube = trimesh.creation.box(extents=[10, 10, 10])
    handle = register(cube)
    result = segment_semantic(handle, sam=MockSam2(num_masks=4), num_views=6, image_size=128)
    assert len(result.face_region_ids) == len(cube.faces)
    assert result.num_regions >= 1
    assert min(result.face_region_ids) >= 0
