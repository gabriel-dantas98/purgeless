import numpy as np
from purgeless_sidecar.ai.backproject import face_vectors_from_views, cluster_face_vectors


def test_face_vectors_shape():
    num_faces = 5
    face_id_buffers = [
        np.array([[0, 0, 1, 1, 2, 2, 3, 3, 4, 4]]),
        np.array([[0, 0, 1, 1, 2, 2, 3, 3, 4, 4]]),
        np.array([[0, 0, 1, 1, 2, 2, 3, 3, 4, 4]]),
    ]
    masks_per_view = [
        [np.array([[True, True, True, True, False, False, False, False, False, False]]),
         np.array([[False, False, False, False, True, True, True, True, True, True]])],
        [np.array([[True, True, True, True, False, False, False, False, False, False]]),
         np.array([[False, False, False, False, True, True, True, True, True, True]])],
        [np.array([[True, True, False, False, False, False, False, False, False, False]]),
         np.array([[False, False, True, True, True, True, True, True, True, True]])],
    ]
    vecs = face_vectors_from_views(num_faces, face_id_buffers, masks_per_view)
    assert vecs.shape == (5, 6)
    np.testing.assert_array_equal(vecs[0], [1, 0, 1, 0, 1, 0])
    np.testing.assert_array_equal(vecs[4], [0, 1, 0, 1, 0, 1])


def test_cluster_three_groups():
    vecs = np.array([
        [1, 0, 0], [1, 0, 0], [1, 0, 0],
        [0, 1, 0], [0, 1, 0], [0, 1, 0],
        [0, 0, 1], [0, 0, 1], [0, 0, 1],
    ], dtype=np.float64)
    labels = cluster_face_vectors(vecs, min_cluster_size=2)
    assert labels.shape == (9,)
    unique = set(labels.tolist())
    assert len(unique) == 3
    for u in unique:
        assert (labels == u).sum() == 3
