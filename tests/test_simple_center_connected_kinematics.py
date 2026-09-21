"""Connected point model keeps contact and boundary assumptions explicit."""

import numpy as np

from scripts.simple_center_connected_kinematics import (
    EDGES,
    current_edges,
    matrix,
    screen,
)


def test_current_trial_axes_are_used():
    assert EDGES == current_edges()
    assert EDGES["post_block"][3] == [
        (177.65, -145, 145),
        (177.65, -145, 176),
    ]
    assert EDGES["block_header"][3] == [
        (208.35, -130.5, 186),
        (236.0, -117.5, 186),
    ]
    assert EDGES["header_principal_block"][3] == [(15.475, -139, 291.45)]
    assert EDGES["principal_block_principal"][3] == [(34.525, -95, 312.5)]
    assert np.allclose(EDGES["principal_upright_block"][3], [(114.45, -144.5, 356)])
    assert np.allclose(EDGES["upright_rear_block"][3], [(133.5, -163.95, 370)])
    assert EDGES["rear_block_post"][3][1] == (140, -150.3, 190)
    assert EDGES["upright_rear_block"][2] == (0, -1, 0)
    assert EDGES["rear_block_post"][2] == (0, 1, 0)


def test_connected_rank_depends_on_return_path_and_contacts():
    result = screen()
    anchored = result["post_anchored"]
    assert anchored["all_faces_closed_axial_on"]["relative_dof"] == 0
    assert anchored["all_faces_closed_axial_off"]["relative_dof"] == 0
    assert anchored["serial_only_closed_axial_on"]["relative_dof"] == 2
    assert anchored["principal_faces_open_axial_on"]["relative_dof"] == 2
    assert anchored["main_faces_closed_return_faces_open_axial_on"]["relative_dof"] == 3
    assert (
        anchored["main_faces_closed_return_faces_open_axial_off"]["relative_dof"] == 7
    )
    assert {
        row["relative_dof"] for row in anchored["one_face_open_axial_on"].values()
    } == {0}
    assert {
        row["relative_dof"] for row in anchored["one_face_open_axial_off"].values()
    } == {1}
    assert anchored["all_faces_open_axial_on"]["relative_dof"] == 9
    assert anchored["all_faces_open_axial_off"]["relative_dof"] == 19
    assert result["free_assembly_all_faces_closed_axial_on"]["relative_dof"] == 6
    assert result["strength_or_frame_verdict"] is False


def test_whole_body_translation_is_free_without_post_anchor():
    closed = matrix(closed=EDGES, anchor_post=False)
    translation = np.zeros(closed.shape[1])
    translation[::6] = 1.0
    assert np.linalg.norm(closed @ translation) < 1e-10
