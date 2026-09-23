"""Source-bound local rigid-body rank, not a strength or whole-frame pass."""

import numpy as np
import pytest

from scripts.owner_barrel_integrated_kinematics import _point_row, _rank, build_report


@pytest.fixture(scope="module")
def report():
    return build_report()


def test_all_current_joint_faces_and_bolts_have_conditional_rank_records(report):
    assert report["station_count"] == 24
    assert report["bolt_interface_count"] == 46
    assert report["contact_cell_count"] == 132
    assert report["native_solve"] is False
    assert report["structural_released"] is False
    assert report["drilling_released"] is False
    assert report["fabrication_released"] is False
    for row in report["stations"].values():
        ranks = row["ranks"]
        assert row["rank_stable_at_tolerance_1e_9_to_1e_7"] is True
        assert (
            0
            <= ranks["bolts_lateral_only_face_open"]
            <= ranks["bolts_full_face_open"]
            <= 6
        )
        assert (
            0
            <= ranks["bolts_lateral_only_face_closed"]
            <= ranks["bolts_full_face_closed"]
            <= 6
        )
        assert ranks["bolts_full_face_open"] <= ranks["bolts_full_face_closed"]
        assert (
            ranks["bolts_lateral_only_face_open"]
            <= ranks["bolts_lateral_only_face_closed"]
        )


def test_single_bolt_center_has_a_closed_face_normal_twist_mode(report):
    for side in ("left", "right"):
        row = report["stations"][f"clip_split_base_center_{side}"]
        assert row["bolt_count"] == 1
        assert row["ranks"]["bolts_full_face_open"] == 3
        assert row["ranks"]["bolts_full_face_closed"] == 5
        assert row[
            "closed_full_free_rotation_axis_alignment_with_face_normal_abs"
        ] == pytest.approx(1.0, abs=1e-6)


def test_two_row_header_has_conditional_closed_rank_but_open_mode(report):
    for side in ("left", "right"):
        row = report["stations"][f"clip_timber_header_outer_{side}"]
        assert row["bolt_count"] == 2
        assert row["ranks"]["bolts_full_face_open"] == 5
        assert row["ranks"]["bolts_full_face_closed"] == 6
        assert row["complete_joint_capacity_or_stiffness_claimed"] is False


def test_connected_framing_sensitivity_uses_all_current_frame_links(report):
    frame = report["connected_frame"]
    assert frame["timber_count"] == 20
    assert frame["barrel_bolt_count"] == 46
    assert frame["retained_bolt_count"] == 12
    assert frame["barrel_contact_cell_count"] == 132
    assert frame["retained_contact_cell_count"] == 72
    assert frame["contact_cell_count"] == 204
    assert frame["graph_component_count"] == 1
    assert frame["relative_dof_count"] == 114
    assert frame["panel_screw_structural_credit"] is False
    assert frame["floor_support_credit"] is False
    ranks = frame["ranks"]
    assert 0 <= ranks["all_bolts_full_all_faces_open"] <= ranks[
        "all_bolts_full_all_faces_closed"
    ] <= 114
    assert 0 <= ranks["barrel_axial_off_all_faces_closed"] <= ranks[
        "all_bolts_full_all_faces_closed"
    ]
    assert ranks["both_center_faces_open"] <= ranks[
        "all_bolts_full_all_faces_closed"
    ]
    assert ranks == {
        "all_bolts_full_all_faces_open": 112,
        "all_bolts_full_all_faces_closed": 114,
        "barrel_axial_off_all_faces_closed": 114,
        "both_center_faces_open": 114,
    }
    assert frame["rank_stable_at_tolerance_1e_9_to_1e_7"] is True


def test_point_jacobian_matches_a_small_rigid_motion():
    point = np.array((25.0, -40.0, 80.0))
    origin = np.array((-10.0, 15.0, 30.0))
    direction = np.array((0.0, 0.0, 1.0))
    translation = np.array((0.3, -0.2, 0.1))
    rotation = np.array((0.002, -0.003, 0.001))
    row = _point_row(point, direction, origin, scale_mm=100.0)
    scaled_motion = np.r_[translation, rotation * 100.0]
    expected = direction @ (translation + np.cross(rotation, point - origin))
    assert row @ scaled_motion == pytest.approx(expected, abs=1e-12)


def test_synthetic_one_and_two_bolt_ranks_do_not_depend_on_reference_or_scale():
    face_points = [
        (-20.0, -20.0, 0.0),
        (-20.0, 20.0, 0.0),
        (20.0, -20.0, 0.0),
        (20.0, 20.0, 0.0),
    ]
    for origin in (np.zeros(3), np.array((200.0, -140.0, 300.0))):
        for scale in (50.0, 100.0, 200.0):
            contact = [
                _point_row(point, (0.0, 0.0, 1.0), origin, scale_mm=scale)
                for point in face_points
            ]
            single = [
                _point_row((0.0, 0.0, 0.0), axis, origin, scale_mm=scale)
                for axis in np.eye(3)
            ]
            pair = [
                _point_row(point, axis, origin, scale_mm=scale)
                for point in ((0.0, -25.0, 0.0), (0.0, 25.0, 0.0))
                for axis in np.eye(3)
            ]
            assert (_rank(single), _rank([*single, *contact])) == (3, 5)
            assert (_rank(pair), _rank([*pair, *contact])) == (5, 6)
