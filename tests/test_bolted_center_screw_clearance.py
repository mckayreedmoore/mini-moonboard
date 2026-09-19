"""Physical centerline requirements for the four protected RS-2 screws."""

import cadquery as cq
import pytest

from scripts.bolted_candidate_center_screw_clearance import (
    BORE_D_MM,
    LONG_OFFSETS_MM,
    PLATE_THICKNESS_MM,
    SHORT_OFFSETS_MM,
    _distance_point_to_shape,
    _distance_segment_to_shape,
    _drilled_angle_blocks,
    screen_center_screw_clearance,
)


def test_segment_crossing_and_near_miss():
    bore = cq.Solid.makeCylinder(2, 10, cq.Vector(0, 0, 0))
    assert _distance_segment_to_shape((-5, 0, 5), (5, 0, 5), bore) == pytest.approx(0)
    assert _distance_segment_to_shape((-5, 3, 5), (5, 3, 5), bore) == pytest.approx(1)


def test_finite_segment_tip_is_not_an_infinite_line():
    bore = cq.Solid.makeCylinder(2, 10, cq.Vector(0, 0, 0))
    assert _distance_segment_to_shape((-5, 0, 5), (-3, 0, 5), bore) == pytest.approx(1)


def test_head_start_is_distinct_from_full_shaft():
    bore = cq.Solid.makeCylinder(2, 10, cq.Vector(0, 0, 0))
    assert _distance_segment_to_shape((-5, 0, 5), (5, 0, 5), bore) == 0
    assert _distance_point_to_shape((-5, 0, 5), bore) == pytest.approx(3)


@pytest.fixture(scope="module")
def record():
    return screen_center_screw_clearance()


def test_source_inventory_and_unknown_physical_envelopes(record):
    assert record["width_option"] == "kerf-right"
    assert record["retained_axis_counts"] == {"hillman_panel": 66, "bolt_clearance": 12}
    assert [s["name"] for s in record["protected_screws"]] == [
        "round_panel_lower_left_center_1",
        "round_kicker_left_center_1",
        "round_kicker_left_center_2",
        "kicker_header_left_1",
    ]
    assert all(s["purchased_centerline_length_mm"] == 63.5 for s in record["protected_screws"])
    expected_starts = [
        [-70, 20.152907, 322.07021],
        [-70, -17.74375, 60],
        [-70, -17.74375, 192],
        [-200, -17.74375, 257.95],
    ]
    expected_directions = [
        [0, -0.766044, 0.642788], [0, -1, 0], [0, -1, 0], [0, -1, 0],
    ]
    for screw, start, direction in zip(record["protected_screws"], expected_starts,
                                       expected_directions, strict=True):
        assert screw["start_mm"] == pytest.approx(start)
        assert screw["direction"] == pytest.approx(direction)
    assert record["nominal_inputs_mm"]["wood_and_steel_hole_diameter"] == 14.2875
    assert record["unknowns"] == {
        "actual_shaft_diameter_mm": None,
        "shaft_diameter_tolerance_mm": None,
        "installed_head_projection_mm": None,
        "installed_head_radius_mm": None,
    }
    assert record["drilling_released"] is False


def test_shared_deduplicates_header_and_stagger_separates(record):
    shared, stagger = record["cases"]
    assert shared["case"] == "shared"
    assert stagger["case"] == "stagger"
    assert shared["top_row_y_mm"] == -95.382052
    assert stagger["underside_row_y_mm"] == -119.666026
    assert len(shared["bores"]) == 6
    assert len(stagger["bores"]) == 8
    assert len([b for b in shared["bores"] if b["member"] == "base_header"]) == 2
    assert len([b for b in stagger["bores"] if b["member"] == "base_header"]) == 4
    for case in (shared, stagger):
        assert len(case["shaft_to_bore_pairs"]) == 4 * len(case["bores"])
        assert len(case["shaft_to_steel_pairs"]) == 4 * 4
        assert len(case["head_start_to_bore_pairs"]) == 4 * len(case["bores"])
        assert len(case["head_start_to_steel_pairs"]) == 4 * 4
        assert case["closest_pairs"]["shaft_to_bore"] == min(
            case["shaft_to_bore_pairs"], key=lambda p: p["distance_mm"]
        )
        assert case["closest_pairs"]["shaft_to_steel"] == min(
            case["shaft_to_steel_pairs"], key=lambda p: p["distance_mm"]
        )
        assert all(p["strict_raw_upper_bound_shaft_radius_mm"] == p["distance_mm"]
                   for p in case["shaft_to_bore_pairs"] + case["shaft_to_steel_pairs"])


def test_nominal_steel_holes_are_open_in_both_legs(record):
    for case in record["cases"]:
        for body in case["steel_bodies"]:
            if "horizontal" in body["id"]:
                assert (body["horizontal_holes_subtracted"],
                        body["vertical_holes_subtracted"]) == (2, 0)
            else:
                assert (body["horizontal_holes_subtracted"],
                        body["vertical_holes_subtracted"]) == (0, 2)


@pytest.mark.parametrize("above", [True, False])
def test_drilled_steel_solids_have_open_holes_at_pattern_centers(above):
    x, row_y, bend_z = 0.0, 0.0, 0.0
    horizontal, vertical = _drilled_angle_blocks(x, row_y, bend_z, above)
    horizontal_mid_z = bend_z + PLATE_THICKNESS_MM / 2 if above else bend_z - PLATE_THICKNESS_MM / 2
    vertical_mid_x = x - PLATE_THICKNESS_MM / 2
    for offset in LONG_OFFSETS_MM:
        center = (x - offset, row_y, horizontal_mid_z)
        assert _distance_point_to_shape(center, horizontal) == pytest.approx(BORE_D_MM / 2)
    for offset in SHORT_OFFSETS_MM:
        center = (vertical_mid_x, row_y, bend_z + offset if above else bend_z - offset)
        assert _distance_point_to_shape(center, vertical) == pytest.approx(BORE_D_MM / 2)
