"""Connected point model keeps contact and boundary assumptions explicit."""

import numpy as np

from scripts.simple_center_connected_kinematics import (
    EDGES,
    NODE_PARTS,
    constraint_rows,
    current_edges,
    matrix,
    screen,
)
from scripts.simple_center_pb02_geometry import active_geometry


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
    assert EDGES["rear_block_post"][3][1] == (140, -150.3, 202.0)
    assert EDGES["upright_rear_block"][2] == (0, -1, 0)
    assert EDGES["rear_block_post"][2] == (0, 1, 0)
    assert np.allclose(EDGES["post_block"][4], (177.65, -131.25, 166.95))
    assert np.allclose(EDGES["block_header"][4], (222.1, -131.25, 238.9))
    assert np.allclose(EDGES["header_principal_block"][4], (15.475, -110.35, 277))
    assert np.allclose(EDGES["principal_block_principal"][4], (50.95, -113.85, 310.5))
    assert np.allclose(EDGES["principal_upright_block"][4], (89.05, -144.9, 368.5))
    assert np.allclose(EDGES["upright_rear_block"][4], (133.5, -175.7, 368.5))
    assert np.allclose(EDGES["rear_block_post"][4], (133.35, -175.7, 119.45))


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


def test_contact_samples_lie_on_both_active_cad_faces():
    parts, _, _ = active_geometry()
    axes = ("x", "y", "z")
    for row in constraint_rows(closed=EDGES):
        if row["kind"] != "contact_compression":
            continue
        first, second, normal, _, _ = EDGES[row["edge"]]
        normal_index = next(index for index, value in enumerate(normal) if value)
        for node in (first, second):
            bounds = parts[NODE_PARTS[node]].BoundingBox()
            for index, (axis, coordinate) in enumerate(zip(axes, row["point_mm"])):
                low = getattr(bounds, f"{axis}min")
                high = getattr(bounds, f"{axis}max")
                assert low - 1e-6 <= coordinate <= high + 1e-6
                if index == normal_index:
                    assert min(abs(coordinate - low), abs(coordinate - high)) < 1e-6
