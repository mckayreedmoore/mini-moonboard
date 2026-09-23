"""Governing combined-cut artifact stays nominal and fail closed."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import owner_barrel_combined_cut_sections as combined

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/barrel-nut-combined-cut-sections.json"


@pytest.fixture(scope="module")
def report():
    return json.loads(ARTIFACT.read_text())


@pytest.fixture(scope="module")
def live_report():
    return combined.build_report()


def test_generated_artifact_exactly_matches_live_transitive_sources(report, live_report):
    assert report == live_report


def test_curved_cutter_projection_uses_surface_extrema_not_only_vertices():
    cutter = cq.Solid.makeCylinder(
        5,
        20,
        cq.Vector(3, 4, 7),
        cq.Vector(1, 0, 0),
    )
    low, high = combined._projected_interval(cutter, cq.Vector(1, 0, 0))
    assert low == pytest.approx(3)
    assert high == pytest.approx(23)

    sloped = cq.Solid.makeCylinder(
        5,
        20,
        cq.Vector(0, 0, 0),
        cq.Vector(1, 0, 0),
    )
    low, high = combined._projected_interval(
        sloped,
        combined._grain("base_side_left"),
    )
    assert low == pytest.approx(-5)
    assert high == pytest.approx(5)


def test_artifact_is_bound_to_current_sources(report):
    assert report["schema"] == combined.SCHEMA
    assert report["source"]["historical_two_row_preliminary_used"] is False
    assert set(report["source"]["source_sha256"]) == set(combined.SOURCE_PATHS)
    for name, expected in report["source"]["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


def test_scope_is_exact_current_governing_layout(report):
    scope = report["scope"]
    assert scope["station_count"] == 8
    assert scope["barrel_pair_count"] == 14
    assert scope["member_count"] == 11
    assert set(scope["stations"]) == set(combined.GOVERNING_STATIONS)
    assert set(scope["members"]) == combined.SCOPED_MEMBERS
    for station in combined.PRINCIPAL_STATIONS:
        assert len(scope["stations"][station]["bolt_names"]) == 1
    for station in combined.OUTER_RAIL_STATIONS:
        assert len(scope["stations"][station]["bolt_names"]) == 2


def test_nominal_full_frame_machining_inventory_is_complete_but_unqualified(report):
    inventory = report["nominal_full_frame_machining_inventory"]
    assert inventory == {
        "member_count": 20,
        "all_members_one_valid_connected_solid": True,
        "host_cutter_count": 268,
        "all_host_cutters_intersect_raw_wood": True,
        "all_host_cutters_removed_from_cut_solids": True,
        "service_cut_count": 32,
        "additional_cut_count": 2,
        "fixed_panel_kicker_cut_count": 66,
        "retained_frame_cut_count": 24,
        "outer_header_trial_cut_count": 16,
        "center_trial_cut_count": 20,
        "remaining_barrel_trial_cut_count": 108,
        "excluded_legacy_sds_axis_count": 144,
        "tolerance_or_resistance_credit": False,
    }


def test_combined_solids_keep_every_scoped_cutter_and_one_valid_solid(report):
    solids = report["combined_cut_solids"]
    inventory = report["cutter_inventory"]
    assert set(solids) == combined.SCOPED_MEMBERS
    assert inventory["host_cutter_count"] == sum(
        row["cutter_count"] for row in solids.values()
    )
    assert inventory["all_scoped_member_cutters_retained"] is True
    assert inventory["all_cutters_have_host_coverage"] is True
    assert len(inventory["rows"]) == inventory["host_cutter_count"]
    assert all(row["host_covered"] for row in inventory["rows"])
    assert solids["base_header"]["cutter_count"] == 30
    for side in ("left", "right"):
        assert solids[f"base_principal_center_{side}"]["cutter_count"] == 21
    for row in solids.values():
        assert row["combined_cut_is_valid"] is True
        assert row["combined_cut_solid_count"] == 1
        assert 0 < row["combined_cut_volume_mm3"] < row["uncut_volume_mm3"]
        assert row["removed_volume_mm3"] > 0


def test_principal_header_pocket_ligament_and_twist_stay_unresolved(report):
    rows = report["critical_principal_header"]
    assert set(rows) == set(combined.PRINCIPAL_STATIONS)
    for row in rows.values():
        assert row["head_pocket_minimum_nominal_header_edge_stock_mm"] == (
            pytest.approx(2.092152)
        )
        assert row["barrel_nominal_radial_x_edge_ligament_mm"] == pytest.approx(
            14.0462
        )
        assert row["isolated_closed_face_rank"] == 5
        assert row["isolated_relative_dof"] == 6
        assert row["free_mode_alignment_with_face_normal_abs"] == pytest.approx(1)
        assert row["face_normal_twist_mode_unresolved"] is True
        assert row["geometry_survival_or_strength_claimed"] is False
    expected = {
        "clip_split_base_center_left": (259.757014, 4612.443118),
        "clip_split_base_center_right": (219.757014, 4310.664868),
    }
    for station, (critical, net) in expected.items():
        section = rows[station]["local_full_section_screen"]
        assert section["sample_pitch_mm"] == 0.25
        assert section["critical_grain_station_mm"] == pytest.approx(critical)
        assert section["gross_area_at_critical_station_mm2"] == pytest.approx(
            5322.57
        )
        assert section["minimum_sampled_full_gross_net_area_mm2"] == (
            pytest.approx(net)
        )
        assert section["net_area_at_principal_barrel_axis_mm2"] == pytest.approx(
            4749.118586
        )
        assert "not a continuous or tolerance-case minimum" in section[
            "coverage_boundary"
        ]
        assert section["strength_or_capacity_claimed"] is False


def test_all_twelve_six_inch_stack_diagnostics_remain_unqualified(report):
    stacks = report["six_inch_outer_rail_stacks"]
    assert stacks["row_count"] == len(stacks["rows"]) == 12
    assert stacks["nominal_tip_past_assumed_axis_mm"] == pytest.approx(1.849)
    assert stacks["nominal_maximum_body_overlap_if_fully_threaded_mm"] == (
        pytest.approx(6.8528)
    )
    assert stacks["nominal_barrel_bore_diametral_fit_allowance_mm"] == 0
    for row in stacks["rows"]:
        assert row["shaft_length_mm"] == pytest.approx(152.4)
        assert row["tip_past_assumed_axis_mm"] == pytest.approx(1.849)
        assert row["maximum_body_overlap_with_fully_threaded_shaft_mm"] == (
            pytest.approx(6.8528)
        )
        assert row["modeled_barrel_diametral_clearance_mm"] == 0
        assert row["thread_engagement"] == "UNKNOWN"
        assert row["fit_qualified"] is False
        assert row["thread_engagement_qualified"] is False


def test_nominal_section_refinement_has_explicit_coverage_boundary(report):
    for row in report["combined_cut_solids"].values():
        sections = row["nominal_grain_normal_sections"]
        assert [item["local_pitch_mm"] for item in sections["refinement"]] == [
            1.0,
            0.5,
            0.25,
        ]
        sampled_areas = [
            item["minimum_sampled_net_area_mm2"]
            for item in sections["refinement"]
        ]
        assert sampled_areas == sorted(sampled_areas, reverse=True)
        assert sections["minimum_sampled_net_area_mm2"] == sampled_areas[-1]
        assert sections["minimum_sampled_net_area_mm2"] > 0
        assert sections["gross_area_at_critical_station_mm2"] + sections[
            "area_comparison_tolerance_mm2"
        ] >= sections["minimum_sampled_net_area_mm2"]
        assert sections["area_comparison_tolerance_mm2"] == (
            combined.SECTION_AREA_COMPARISON_TOLERANCE_MM2
        )
        assert sections["sample_set_stability_threshold_mm2"] == (
            combined.SECTION_SAMPLE_SET_STABILITY_THRESHOLD_MM2
        )
        assert sections["sample_set_minimum_stable"] is True
        assert sections["strength_or_capacity_claimed"] is False
        assert "does not prove a continuous global minimum" in sections[
            "coverage_boundary"
        ]
    coverage = report["section_coverage"]
    assert coverage["unstable_sample_set_members"] == []
    assert coverage["all_member_sample_set_minima_stable"] is True
    assert coverage["continuous_global_coverage_complete"] is False
    assert coverage["tolerance_case_coverage_complete"] is False
    assert coverage["geometry_survival_established"] is False


def test_missing_tolerances_force_evidence_blocked_without_release(report):
    assert report["controlled_tolerance_cases"] == []
    assert report["net_section_resistance_evaluated"] is False
    assert "No tolerance-minimum section" in report[
        "net_section_resistance_not_evaluated_reason"
    ]
    assert len(report["missing_controlled_inputs"]) >= 6
    assert report["disposition"] == "EVIDENCE_BLOCKED"
    assert all(value is False for value in report["flags"].values())
    assert "No GO or NO_GO" in report["disposition_basis"]


def test_scope_validator_rejects_one_bolt_principal_source_drift(report):
    bolt_station = {}
    barrel_station = {}
    bolts = {}
    for station, row in report["scope"]["stations"].items():
        for name in row["bolt_names"]:
            bolt_station[name] = station
            bolts[name] = SimpleNamespace(members=tuple(row["members"]))
        for name in row["barrel_names"]:
            barrel_station[name] = station
    assembly = {
        "bolt_station": bolt_station,
        "barrel_station": barrel_station,
        "bolts": bolts,
    }
    assert combined._scope(assembly)["clip_split_base_center_left"]
    added = "source_drift_extra_bolt"
    assembly["bolt_station"][added] = "clip_split_base_center_left"
    assembly["bolts"][added] = SimpleNamespace(
        members=("base_header", "base_principal_center_left")
    )
    with pytest.raises(ValueError, match="scope changed"):
        combined._scope(assembly)
