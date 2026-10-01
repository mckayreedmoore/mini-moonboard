from __future__ import annotations

import hashlib
import math

import pytest

from scripts import build_current_taper_bore_clearance_preflight_attempt01 as preflight


def candidate_manifest(*, one_leg_receiver: bool = False) -> dict:
    physical = [{"member_id": f"receiver_{index}"} for index in range(92)]
    physical.extend({"member_id": leg} for leg in preflight.LEGS)
    axes = []
    for index in range(92):
        receiver = preflight.LEGS[0] if one_leg_receiver and index == 91 else f"receiver_{index}"
        axes.append(
            {
                "axis_id": f"candidate_{index:02}",
                "receiver_member_ids": [receiver],
                "geometry": {"wood_receiver_intervals": [{"receiver_id": receiver}]},
            }
        )
    return {"physical_members": physical, "candidate_bolt_axes": axes}


def test_source_pin_drift_fails_closed(tmp_path):
    source = tmp_path / "source.json"
    source.write_text("original")
    expected = hashlib.sha256(b"other").hexdigest()
    with pytest.raises(ValueError, match="source hash mismatch"):
        preflight.verify_pins(tmp_path, {"source.json": expected})


def test_duplicate_and_missing_axis_inventories_fail_closed():
    with pytest.raises(preflight.NoGoError, match="unique axis_id"):
        preflight.unique_rows([{"axis_id": "same"}, {"axis_id": "same"}], "axis_id", 2, "axis")
    with pytest.raises(preflight.NoGoError, match="unique axis_id"):
        preflight.unique_rows([{"axis_id": "one"}], "axis_id", 2, "axis")


def test_candidate_membership_audits_all_92_and_flags_a_leg_receiver():
    clear = preflight.candidate_receiver_audit(candidate_manifest())
    assert clear["candidate_axis_count"] == 92
    assert clear["receiver_membership_rows_checked"] == 92
    assert clear["leg_receiver_axis_count"] == 0
    assert clear["all_candidate_receiver_memberships_exclude_both_legs"] is True

    ambiguous = preflight.candidate_receiver_audit(candidate_manifest(one_leg_receiver=True))
    assert ambiguous["leg_receiver_axis_count"] == 1
    assert ambiguous["all_candidate_receiver_memberships_exclude_both_legs"] is False


def test_duplicate_or_incomplete_receiver_intervals_fail_closed():
    manifest = candidate_manifest()
    manifest["candidate_bolt_axes"][0]["geometry"]["wood_receiver_intervals"] = []
    with pytest.raises(preflight.NoGoError, match="receiver list/interval inventory mismatch"):
        preflight.candidate_receiver_audit(manifest)

    manifest = candidate_manifest()
    manifest["candidate_bolt_axes"][0]["receiver_member_ids"] = ["receiver_0", "receiver_0"]
    with pytest.raises(preflight.NoGoError, match="duplicate receiver membership"):
        preflight.candidate_receiver_audit(manifest)


def test_nonfinite_geometry_fails_closed():
    with pytest.raises(preflight.NoGoError, match="nonfinite"):
        preflight.finite(float("nan"), "test coordinate")
    with pytest.raises(preflight.NoGoError, match="three coordinates"):
        preflight.vector([0.0, math.inf], "test axis")


def test_axis_line_matching_uses_direction_and_perpendicular_offset():
    retained = {"origin_global_xyz_mm": [0.0, 10.0, 20.0], "axis_global_xyz": [-1.0, 0.0, 0.0]}
    on_same_line = {
        "axis_location_xyz_mm": [-15.0, 10.0, 20.0],
        "axis_direction_xyz": [1.0, 0.0, 0.0],
    }
    assert preflight.cylinder_axis_match(on_same_line, retained)[0] is True

    shifted = {**on_same_line, "axis_location_xyz_mm": [-15.0, 10.01, 20.0]}
    assert preflight.cylinder_axis_match(shifted, retained)[0] is False
    tilted = {**on_same_line, "axis_direction_xyz": [0.0, 1.0, 0.0]}
    assert preflight.cylinder_axis_match(tilted, retained)[0] is False


def test_clearance_thresholds_are_the_pinned_taper_preflight_tolerances():
    assert preflight.GEOMETRY_TOLERANCE_MM == 1e-5
    assert preflight.AXIS_TOLERANCE == 1e-10


def test_source_pinned_cad_replay_maps_eight_bores_and_keeps_criterion_pending():
    report, _ = preflight.build_report()
    assert report["cad_envelope_screen"] == "CLEAR_WITHIN_PINNED_CAD_ENVELOPES"
    assert report["candidate_receiver_audit"]["candidate_axis_count"] == 92
    assert report["candidate_receiver_audit"]["leg_receiver_axis_count"] == 0
    assert sum(row["bore_count"] for row in report["leg_bore_envelopes"].values()) == 8
    gaps = [row["minimum_bore_envelope_gap_mm"] for row in report["leg_bore_envelopes"].values()]
    assert min(gaps) == pytest.approx(50.7127715435, abs=1e-8)
    assert report["criterion_disposition"]["criterion_id"] == "taper_taper_region_unbored_torsion_applicable"
    assert report["criterion_disposition"]["status"] == "pending"
    assert report["release"] == {"candidate_accepted": False, "fabrication_released": False, "climbing_released": False}
