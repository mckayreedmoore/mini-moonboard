"""Selected qualification-stack CAD corrections remain reproducible."""

import copy

import pytest

from scripts import owner_barrel_selected_geometry_probe as geometry
from scripts import owner_barrel_selected_hardware as selected


@pytest.fixture(scope="module")
def report():
    return geometry.build_report()


def test_selected_barrel_and_bore_corrections_clear_nominal_geometry(report):
    assert report["status"] == "PASS_NOMINAL_GEOMETRY_ONLY"
    assert report["nominal_geometry_clear"] is True

    barrel = report["barrel_shift"]
    assert barrel["pair_count"] == 46
    assert barrel["body_shift_mm"] == pytest.approx(2.0066)
    assert barrel["insertion_depth_range_mm"] == pytest.approx([29.058, 70.508])
    assert barrel["maximum_thread_axis_preservation_error_mm"] == pytest.approx(0.0)
    assert barrel["shifted_body_outside_receiver_volume_mm3"] == pytest.approx(0.0)
    assert barrel["bore_tail_outside_receiver_volume_mm3"] == pytest.approx(0.0)
    assert barrel["unrelated_wood_hit_count"] == 0
    assert barrel["protected_hit_count"] == 0
    assert barrel["peer_barrel_path_or_stack_hit_count"] == 0

    rail = report["six_and_half_inch_rail_correction"]
    assert rail["pair_count"] == 12
    assert rail["added_bore_depth_mm"] == pytest.approx(12.4408)
    assert rail["minimum_adverse_tip_clearance_mm"] == pytest.approx(2.0)

    top = report["five_inch_top_outer_correction"]
    assert top["pair_count"] == 4
    assert top["added_bore_depth_mm"] == pytest.approx(1.8796)
    assert top["minimum_adverse_tip_clearance_mm"] == pytest.approx(2.0)

    for correction in (rail, top):
        assert correction["outside_receiver_volume_mm3"] == pytest.approx(0.0)
        assert correction["unrelated_or_protected_hit_count"] == 0
        assert correction["peer_barrel_path_or_stack_hit_count"] == 0
        assert correction["maximum_washer_hit_count"] == 0

    assert report["structural_released"] is False
    assert report["fabrication_released"] is False
    assert report["diy_ready"] is False


def test_selected_hardware_json_is_bound_to_recomputed_geometry(report):
    expected = geometry.selection_fields(report)
    assert geometry.validate_recorded_fields(report) == expected

    changed = copy.deepcopy(selected.load_selection())
    changed["stack_screen"][
        "five_in_provisional_2mm_clearance_added_bore_depth_mm"
    ] += 0.1
    with pytest.raises(ValueError, match="Selected geometry fields drifted"):
        geometry.validate_recorded_fields(report, changed)
