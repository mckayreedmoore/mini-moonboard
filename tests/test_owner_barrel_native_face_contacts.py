"""Gross butt-face geometry for the integrated barrel-frame native adapter."""

import pytest

from scripts import owner_barrel_native_face_contacts as contacts


@pytest.fixture(scope="module")
def report():
    return contacts.build_report()


def test_all_integrated_joint_faces_and_bolt_crossings_are_source_bound(report):
    assert report["schema"] == contacts.SCHEMA
    assert report["post_placement"] == "integrated"
    assert report["station_count"] == 24
    assert report["contact_cell_count"] == 96
    assert report["bolt_interface_count"] == 46
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
    assert all(len(row["contact_cells"]) == 4 for row in rows.values())
    assert all(
        sum(cell["tributary_area_mm2"] for cell in row["contact_cells"])
        == pytest.approx(row["gross_contact_area_mm2"], abs=0.002)
        for row in rows.values()
    )
    assert all(
        bolt["point_on_gross_contact_face"]
        for row in rows.values()
        for bolt in row["bolt_face_crossings"]
    )
    assert len(rows["clip_split_base_center_left"]["bolt_face_crossings"]) == 1
    assert len(rows["clip_split_base_center_right"]["bolt_face_crossings"]) == 1
