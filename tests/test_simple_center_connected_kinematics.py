"""Connected point model keeps contact and boundary assumptions explicit."""

import numpy as np

from scripts.simple_center_connected_kinematics import EDGES, matrix, screen
from scripts.simple_center_post_header_two_bolt_probe import VARIANTS
from scripts.simple_center_second_bolt_tolerance_probe import POSE


def test_current_trial_axes_are_used():
    _, y, z_pair, x_pair = VARIANTS["shorter_8in_trial"]
    assert EDGES["post_block"][3] == [(177.65, y, z) for z in z_pair]
    assert EDGES["block_header"][3] == [(x, -130, 238.9) for x in x_pair]
    assert EDGES["header_principal_block"][3] == [(15.475, POSE.vertical_y, 277)]
    assert EDGES["principal_block_principal"][3] == [(50.95, -95, POSE.cross_z)]


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
