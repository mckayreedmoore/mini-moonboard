"""Gross butt-face geometry for the integrated barrel-frame native adapter."""

import cadquery as cq
import pytest

from scripts import owner_barrel_native_face_contacts as contacts


@pytest.fixture(scope="module")
def report():
    return contacts.build_report()


def test_all_integrated_joint_faces_and_bolt_crossings_are_source_bound(report):
    assert report["schema"] == contacts.SCHEMA
    assert report["post_placement"] == "integrated"
    assert report["station_count"] == 24
    assert report["contact_cell_count"] == 132
    assert report["bolt_interface_count"] == 46
    assert report["trial_cut_face_count"] == 24
    assert report["trial_cut_cell_face_count"] == 24
    assert 0 < report["adjusted_contact_point_count"] < 132
    assert report["fixed_panel_kicker_screw_count"] == 66
    assert report["retained_frame_bolt_count"] == 12
    assert report["contact_law_qualified"] is False
    assert report["native_solve"] is False
    assert report["structural_released"] is False
    assert report["drilling_released"] is False


def test_actual_face_areas_and_bolt_points_are_consistent(report):
    rows = report["stations"]
    assert rows["clip_single_top_left_1"]["gross_contact_area_mm2"] == pytest.approx(
        5322.57, abs=0.01
    )
    assert rows["clip_split_header_center_left"][
        "gross_contact_area_mm2"
    ] == pytest.approx(12419.33, abs=0.01)
    assert rows["clip_split_base_center_left"][
        "gross_contact_area_mm2"
    ] == pytest.approx(5113.122, abs=0.01)
    assert rows["clip_horizontal_lower_right_2"]["trial_cut_contact_area_mm2"] == (
        pytest.approx(5234.213, abs=0.01)
    )
    assert rows["clip_split_base_center_right"]["trial_cut_contact_area_mm2"] == (
        pytest.approx(5055.451, abs=0.01)
    )
    assert rows["clip_angle_base_right"]["trial_cut_contact_area_mm2"] == (
        pytest.approx(10828.845, abs=0.01)
    )
    assert rows["clip_split_top_center_left"]["contact_cell_area_basis"] == (
        "exact_trial_cut_face"
    )
    assert all(
        0 < row["trial_cut_contact_area_mm2"] < row["gross_contact_area_mm2"]
        and row["trial_cut_face_continuous"]
        for row in rows.values()
    )
    assert all(
        len(row["contact_cells"])
        == (
            16
            if row["family"] == "base_center"
            else 10 if row["family"] == "base_outer_side" else 4
        )
        for row in rows.values()
    )
    assert all(
        sum(cell["gross_tributary_area_mm2"] for cell in row["contact_cells"])
        == pytest.approx(row["gross_contact_area_mm2"], abs=0.002)
        and sum(cell["tributary_area_mm2"] for cell in row["contact_cells"])
        == pytest.approx(row["trial_cut_contact_area_mm2"], abs=0.002)
        for row in rows.values()
    )
    assert all(
        bolt["point_on_gross_contact_face"]
        for row in rows.values()
        for bolt in row["bolt_face_crossings"]
    )
    assert len(rows["clip_split_base_center_left"]["bolt_face_crossings"]) == 1
    assert len(rows["clip_split_base_center_right"]["bolt_face_crossings"]) == 1


def test_every_contact_cell_conserves_current_trial_cut_face_area(report):
    """Native preparation must not apply gross pressure area to cut timber."""
    assert report["trial_cut_cell_face_count"] == 24
    for row in report["stations"].values():
        assert row["contact_cell_area_basis"] == "exact_trial_cut_face"
        assert all(
            isinstance(cell["point_adjusted_from_gross_center"], bool)
            for cell in row["contact_cells"]
        )
        assert sum(cell["tributary_area_mm2"] for cell in row["contact_cells"]) == (
            pytest.approx(row["trial_cut_contact_area_mm2"], abs=0.002)
        )


def test_every_contact_partition_preserves_cut_face_centroid_and_first_moments(
    report,
):
    for station, row in report["stations"].items():
        cells = row["contact_cells"]
        area = row["trial_cut_contact_area_mm2"]
        expected_centroid = row["trial_cut_contact_centroid_xyz_mm"]
        actual_moment = [
            sum(
                cell["tributary_area_mm2"] * cell["point_xyz_mm"][axis]
                for cell in cells
            )
            for axis in range(3)
        ]
        expected_moment = [area * value for value in expected_centroid]
        assert actual_moment == pytest.approx(expected_moment, abs=0.05), station
        assert [value / area for value in actual_moment] == pytest.approx(
            expected_centroid, abs=1e-5
        ), station

    for station in ("clip_angle_base_left", "clip_angle_base_right"):
        row = report["stations"][station]
        area = row["trial_cut_contact_area_mm2"]
        centroid = [
            sum(
                cell["tributary_area_mm2"] * cell["point_xyz_mm"][axis]
                for cell in row["contact_cells"]
            )
            / area
            for axis in range(3)
        ]
        assert centroid == pytest.approx(
            row["trial_cut_contact_centroid_xyz_mm"], abs=1e-5
        )


def test_partition_fails_closed_for_disconnected_cut_face():
    patch = cq.Face.makeFromWires(
        cq.Wire.makePolygon(
            [
                cq.Vector(0, 0, 0),
                cq.Vector(10, 0, 0),
                cq.Vector(10, 10, 0),
                cq.Vector(0, 10, 0),
            ],
            close=True,
        )
    )
    halves = [
        cq.Face.makeFromWires(
            cq.Wire.makePolygon(
                [
                    cq.Vector(x0, 0, 0),
                    cq.Vector(x1, 0, 0),
                    cq.Vector(x1, 10, 0),
                    cq.Vector(x0, 10, 0),
                ],
                close=True,
            )
        )
        for x0, x1 in ((0, 4), (6, 10))
    ]
    cut_patch = cq.Compound.makeCompound(halves)
    with pytest.raises(ValueError, match="must be one connected face"):
        contacts._contact_cells(
            patch, cut_patch, cq.Vector(0, 0, 1), "disconnected"
        )


def test_center_single_bolt_has_numerically_resolved_rear_contact_strip(report):
    for station in ("clip_split_base_center_left", "clip_split_base_center_right"):
        row = report["stations"][station]
        bolt_y = row["bolt_face_crossings"][0]["point_xyz_mm"][1]
        cell_y = [cell["point_xyz_mm"][1] for cell in row["contact_cells"]]
        assert min(cell_y) < bolt_y < max(cell_y)
        rear_area = sum(
            cell["tributary_area_mm2"]
            for cell in row["contact_cells"]
            if cell["point_xyz_mm"][1] < bolt_y
        )
        assert rear_area == pytest.approx(605.959553, abs=0.01)
        assert row["contact_cell_area_basis"] == "exact_trial_cut_face"
        assert row["gross_face_y_edge_margins_from_bolt_mm"]["rear"] == pytest.approx(
            16.194623, abs=0.0002
        )
        assert row["gross_face_y_edge_margins_from_bolt_mm"]["front"] == pytest.approx(
            118.007, abs=0.002
        )
        margin = row["gross_face_y_edge_margins_from_bolt_mm"]
        assert margin["trial_cut_rear_strip_area_mm2"] == pytest.approx(
            588.179572, abs=0.001
        )
        assert (
            margin["trial_cut_rear_strip_area_mm2"]
            < row["trial_cut_contact_area_mm2"] / 2
        )
        assert margin["trial_cut_rear_strip_area_mm2"] + margin[
            "trial_cut_front_area_mm2"
        ] == pytest.approx(row["trial_cut_contact_area_mm2"], abs=0.001)
