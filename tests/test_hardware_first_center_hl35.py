"""Reproducible fit-rejection gates for one nominal HL35 center assembly."""

import json
from pathlib import Path

from scripts.hardware_first_center_hl35 import screen_hl35_center

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_hl35.json"


def test_installed_trial_is_rejected_by_measured_geometry() -> None:
    result = screen_hl35_center()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["all_66_panel_axes_unchanged"] is True
    assert result["prior_downward_header_failure"]["unchanged_post_overlap_mm"] == 50.8
    assert result["prior_downward_header_failure"]["screw_above_shortened_post_end_mm"] == 3.9
    assert result["header_z_mm"] == [238.9, 327.8]
    assert result["principal_min_z_mm"] == 327.8
    assert result["post_max_z_mm"] == 238.9
    assert result["original_post_material_removed_mm3"] == {"left": 0.0, "right": 0.0}
    assert result["panel_receivers_with_nominal_intersection"] == 66
    assert result["upper_kicker_receivers_with_nominal_intersection"] == 2
    assert result["full_kicker_inner_edge_support"] is False
    assert all(v > 0 for v in result["remaining_kicker_inner_edge_overhang_mm"].values())
    assert len(result["same_face_header_bore_pairs"]) == 8
    assert all(item["axis_separation_mm"] == 12.7 and
               item["overlapping_header_bore_mm3"] > 600
               for item in result["same_face_header_bore_pairs"])
    plates = result["ideal_inner_plate_envelope"]
    assert plates["flange_reach_mm"] == 82.55
    assert plates["assumed_plate_thickness_mm"] == 4.55
    assert "not delivered geometry" in plates["qualification"]
    assert plates["panel_solid_intersections_over_0_01_mm3"] == []
    assert {item["level"] for item in plates["collisions"]} == {"upper", "lower"}
    for item in plates["collisions"]:
        assert item["left_right_plate_overlap_mm3"] == 29528.135
        assert item["left_plate_opposite_timber_mm3"] == 18173.383
        assert item["right_plate_opposite_timber_mm3"] == 18173.383
    assert result["horizontal_flange_hole_x_offset"]["assumed_nominal_mm"] == 50.8
    assert "Undimensioned" in result["horizontal_flange_hole_x_offset"]["qualification"]
    assert result["screw_envelope_lengths_mm"] == {
        "frozen_occupied": 50.8,
        "purchased_overall_conditional": 63.5,
    }
    for names in result["panel_bore_clashes_by_envelope"].values():
        assert set(names) == {
            "round_kicker_left_center_2", "round_kicker_right_center_2"
        }
    assert "not required embedment" in result["receiver_check_qualification"]
    missing = [b for b in result["bores"] if b["vertical_missing_wood_mm3"] > 0.05]
    assert {b["id"] for b in missing} == {
        "left_outer_upper_1", "left_inner_upper_1",
        "right_outer_upper_1", "right_inner_upper_1",
    }
    assert result["known_projection_nonclash"]["x_axis_separation_mm"] > result[
        "known_projection_nonclash"]["sum_nominal_radii_mm"
    ]
    assert json.loads(RESULT.read_text()) == result
