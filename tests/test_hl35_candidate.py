"""Known geometric controls and source-preservation guards for the new lane."""

import json
import math

import cadquery as cq
import pytest

from scripts import hl35_candidate as hl
from scripts import hl35_candidate_finalize as final
from scripts import hl35_candidate_finish as finish
from scripts import hl35_counterbore_candidate as counters
from scripts import hl35_fit_revision as fit_v3
from scripts import hl35_full_fit_candidate as full_fit
from scripts import hl35_nominal_service_candidate as service_fit
from scripts import hl35_revised_candidate as revised


def test_opposed_attachments_share_one_physical_axis():
    point, direction = cq.Vector(25, 50, 75), cq.Vector(1, 0, 0)
    expected = hl.line_key("post", point, direction)
    assert hl.line_key("post", point + direction.multiply(88.9), direction.multiply(-1)) == expected
    assert hl.line_key("post", point + cq.Vector(0, 1, 0), direction) != expected
    assert hl.line_key("other_post", point, direction) != expected


def test_ideal_angle_volume_against_closed_form():
    expected = (2 * hl.REACH * hl.PLATE * hl.BEND_LENGTH - hl.PLATE**2 * hl.BEND_LENGTH
                - 4 * math.pi * (hl.BORE / 2)**2 * hl.PLATE)
    assert hl.angle_shape().Volume() == pytest.approx(expected, abs=.001)


def test_projection_overlap_is_not_a_solid_collision():
    # Overlapping global bounding boxes alone must never be reported as a collision.
    a = cq.Solid.makeCylinder(1, 20, cq.Vector(0, 0, 0), cq.Vector(1, 1, 0))
    b = cq.Solid.makeCylinder(1, 20, cq.Vector(0, 4, 0), cq.Vector(1, 1, 0))
    assert hl.overlaps(a, b) == pytest.approx(0, abs=1e-8)
    assert hl.overlaps(a, a) == pytest.approx(a.Volume(), abs=1e-6)


def test_partial_receiver_is_not_minimum_thickness():
    bore = cq.Solid.makeCylinder(hl.BORE / 2, hl.WOOD_MIN, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    thin = cq.Solid.makeBox(100, 100, 38.1, cq.Vector(-50, -50, 0))
    full = cq.Solid.makeBox(100, 100, 88.9, cq.Vector(-50, -50, 0))
    assert hl.overlaps(bore, thin) / bore.Volume() == pytest.approx(3 / 7, abs=1e-8)
    assert hl.overlaps(bore, full) / bore.Volume() == pytest.approx(1, abs=1e-8)


def test_frozen_candidate_has_complete_census_and_no_inherited_pass():
    snapshot, inventory, _ = hl.load_sources()
    report = json.loads((hl.PACKET / "fit-assessment.json").read_text())
    counts = report["counts"]
    assert counts["duties"] == len(report["duties"]) == 24
    assert counts["flange_hole_attachments"] == len(report["flange_attachments"]) == 192
    assert counts["new_physical_bolt_axes"] == len(report["physical_bolt_axes"]) == 140
    attachments = {f'{row["angle_id"]}:{row["flange"]}:{row["hole_index"]}' for row in report["flange_attachments"]}
    bound = [name for row in report["physical_bolt_axes"] for name in row["attachment_ids"]]
    assert len(bound) == len(set(bound)) == len(attachments)
    assert set(bound) == attachments
    originals = {row["axis_id"]: row for row in inventory["fixed_panel_kicker_screws"]}
    moves = {row["axis_id"]: row for row in snapshot["panel_screws"]}
    assert len(originals) == len(report["panel_screw_axes"]) == 66
    for row in report["panel_screw_axes"]:
        original, move = originals[row["axis_id"]], moves.get(row["axis_id"])
        expected = move["new_start_global_xyz_mm"] if move else original["origin_global_xyz_mm"]
        assert row["origin_global_xyz_mm"] == pytest.approx(expected, abs=1e-8)
        assert row["axis_global_xyz"] == pytest.approx(original["axis_global_xyz"], abs=1e-8)
        assert row["new_candidate_axis_moved"] is False
    assert all(value is False for value in report["release"].values())
    assert all(row["catalog_resistance_utilization"] is None for row in report["duties"])
    assert report["load_basis"]["inherited_joint_passes"] is False
    assert report["mechanics_gates"]["native_solve_ready"] is False


def test_evidence_bytes_and_old_authorities_are_unchanged():
    manifest = json.loads((hl.PACKET / "manifest.json").read_text())
    for path, expected in {**manifest["source_sha256"], **manifest["outputs"]}.items():
        assert hl.sha(hl.ROOT / path) == expected, path
    contract = json.loads((hl.ROOT / "hl35-candidate.json").read_text())
    assert contract["authority"]["replaces_selected_authority"] is False
    assert contract["candidate"] != json.loads((hl.ROOT / "current-candidate.json").read_text())["candidate"]
    assert all(value is False for value in contract["release"].values())


def test_bolt_grip_is_local_to_its_path_through_a_shaped_header():
    # The top rises/falls along Y. A whole-member height would float the washer
    # above the actual exit. The known line at Y20 crosses Z0 and Z80 exactly.
    wedge = revised.yz_prism(0, 100, [(0, 0), (100, 0), (0, 100)])
    point, direction = cq.Vector(50, 20, -10), cq.Vector(0, 0, 1)
    assert full_fit.line_span(wedge, point, direction) == pytest.approx((10, 90), abs=1e-7)
    assert hl.projected_extent(wedge, direction) == pytest.approx((0, 100))
    assert full_fit.line_span(wedge, point + direction.multiply(150), direction) == pytest.approx((-140, -60), abs=1e-7)


def test_auxiliary_washer_change_against_circle_overlap_control():
    def axis(x):
        return {"id": "test", "axis_kind": "auxiliary_through_tie", "attachments": [],
                "diameter_mm": 7.9375, "grip_mm": 250, "point": cq.Vector(x, 0, 0),
                "direction": cq.Vector(0, 0, 1)}
    pitch, radius = 31.75, 19.05
    old = dict(fit_v3.metal(axis(0)))["head_washer"]
    shifted = old.translate(cq.Vector(pitch, 0, 0))
    area = 2 * radius**2 * math.acos(pitch / (2 * radius)) - pitch / 2 * math.sqrt(4 * radius**2 - pitch**2)
    assert hl.overlaps(old, shifted) == pytest.approx(area * 3, abs=1e-5)
    new = dict(finish.local_metal(axis(0)))["head_washer"]
    assert hl.overlaps(new, new.translate(cq.Vector(pitch, 0, 0))) == pytest.approx(0, abs=1e-7)


def test_service_revision_retains_complete_inputs_without_acceptance():
    snapshot, inventory, _ = hl.load_sources()
    report = json.loads((service_fit.PACKET / "fit-assessment.json").read_text())
    counts = report["counts"]
    assert counts["hl35_angles"] == 30
    assert counts["flange_hole_attachments"] == len(report["flange_attachments"]) == 120
    assert counts["new_physical_bolt_axes"] == len(report["physical_bolt_axes"]) == 98
    assert counts["total_proposed_structural_bolt_axes"] == len(report["installed_axes"]) == 112
    assert len({a["id"] for a in report["installed_axes"]}) == 112
    assert len(report["panel_screw_axes"]) == len(inventory["fixed_panel_kicker_screws"]) == 66
    original = {r["axis_id"]: r for r in inventory["fixed_panel_kicker_screws"]}
    old_moves = {r["axis_id"]: r for r in snapshot["panel_screws"]}
    new_moves = {r["axis_id"]: r for r in report["proposed_screw_moves"]}
    assert len(new_moves) == 8
    for row in report["panel_screw_axes"]:
        name = row["axis_id"]
        prior = old_moves[name]["new_start_global_xyz_mm"] if name in old_moves else original[name]["origin_global_xyz_mm"]
        expected = new_moves[name]["new_point_xyz_mm"] if name in new_moves else prior
        assert row["origin_global_xyz_mm"] == pytest.approx(expected, abs=1e-8)
        assert row["axis_global_xyz"] == pytest.approx(original[name]["axis_global_xyz"], abs=1e-8)
        assert row["new_candidate_axis_moved"] == (name in new_moves)
        if name in new_moves:
            assert new_moves[name]["old_point_xyz_mm"] == pytest.approx(prior, abs=1e-8)
    assert len(report["service_clearance"]["source_authentication"]) == 405
    assert len(report["proposed_wire_routes"]) == 3
    assert all(r["endpoints_retained"] for r in report["proposed_wire_routes"])
    assert all(r["within_approximate_budget"] for r in report["proposed_wire_routes"])
    assert all(r["unused_slack_accommodation_modeled"] is False for r in report["proposed_wire_routes"])
    assert all(value is False for value in report["release"].values())
    assert report["mechanics_gates"]["native_solve_ready"] is False
    assert report["load_basis"]["inherited_joint_passes"] is False
    assert all(row["catalog_resistance_utilization"] is None for row in report["duties"])


def test_all_distinct_failed_inputs_and_latest_evidence_remain_bound():
    packets = [hl.PACKET, revised.PACKET, fit_v3.PACKET, full_fit.PACKET, finish.PACKET, service_fit.PACKET, final.PACKET, counters.PACKET]
    for packet in packets:
        manifest = json.loads((packet / "manifest.json").read_text())
        for path, expected in {**manifest["source_sha256"], **manifest["outputs"]}.items():
            assert hl.sha(hl.ROOT / path) == expected, f"{packet.name}: {path}"
        for supplement in ("rendering", "hardware_closure"):
            if supplement in manifest:
                for path, expected in {**manifest[supplement]["source_sha256"], **manifest[supplement]["outputs"]}.items():
                    assert hl.sha(hl.ROOT / path) == expected, path
    latest = json.loads((service_fit.PACKET / "fit-assessment.json").read_text())
    prior = json.loads((finish.PACKET / "fit-assessment.json").read_text())
    assert latest["installed_axes"] == prior["installed_axes"]
    assert hl.sha(hl.ROOT / latest["reused_v5_negative_hardware_checks"]["path"]) == latest["reused_v5_negative_hardware_checks"]["sha256"]


def test_final_nominal_fit_cannot_promote_the_candidate_to_structural_acceptance():
    report = json.loads((final.PACKET / "fit-assessment.json").read_text())
    contract = json.loads((hl.ROOT / "hl35-candidate.json").read_text())
    original = json.loads((hl.PACKET / "fit-assessment.json").read_text())
    mapping = contract["source_duty_to_new_joint"]
    assert set(mapping) == {r["duty_id"] for r in original["duties"]}
    assert set(mapping.values()) == {r["duty_id"] for r in report["duties"]}
    assert len(mapping) == 24 and len(set(mapping.values())) == 22
    assert report["mechanics_gates"]["conditional_occupied_geometry"] is True
    assert report["mechanics_gates"]["geometry_fit"] is False
    assert report["mechanics_gates"]["direction_and_pair_installation_applicable"] is False
    assert report["mechanics_gates"]["native_solve_ready"] is False
    assert contract["revision"] == counters.REVISION
    assert contract["status"] == report["status"] == "REVISE"
    assert all(value is False for value in report["release"].values())
    assert all(value is False for value in contract["release"].values())
    assert all(r["catalog_resistance_utilization"] is None and r["status"] == "UNQUALIFIED" for r in report["duties"])
    assert len(report["joint_architecture"]["paired_angle_duties"]) == 8
    assert len(report["joint_architecture"]["single_angle_and_compression_duties"]) == 14
    prior = json.loads((finish.PACKET / "fit-assessment.json").read_text())
    assert report["installed_axes"] == prior["installed_axes"]
    assert all(report["counts"][name] == 0 for name in (
        "attachments_missing_minimum_receiving_wood", "flanges_without_full_nominal_bearing",
        "planning_hardware_pair_intersections", "planning_hardware_screw_intersections",
        "planning_nonshaft_hardware_timber_intersections", "retained_service_metal_intersections",
        "retained_service_timber_intersections"))
    closure = json.loads((final.PACKET / "hardware-closure.json").read_text())
    assert closure["conditional_coverage_passed"] is False
    assert closure["counts"]["metal_angle_intersections"] == 8
    assert closure["counts"]["shaft_unrelated_raw_timber_intersections"] == 4


def test_deeper_recess_clearance_does_not_hide_failed_receiving_wood():
    report = json.loads((counters.PACKET / "fit-assessment.json").read_text())
    contract = json.loads((hl.ROOT / "hl35-candidate.json").read_text())
    assert report["counts"]["attachments_missing_minimum_receiving_wood"] == 8
    assert report["counts"]["flanges_without_full_nominal_bearing"] == 8
    assert {r["duty_id"] for r in report["duties"] if r["status"] == "REVISE"} == {
        "principal_header_outer_left", "principal_header_outer_right",
        "kicker_header_outer_left", "kicker_header_outer_right"}
    assert all(report["counts"][name] == 0 for name in (
        "planning_hardware_pair_intersections", "planning_hardware_angle_intersections",
        "shaft_unrelated_raw_timber_intersections", "planning_hardware_screw_intersections",
        "planning_nonshaft_hardware_timber_intersections", "retained_service_metal_intersections",
        "retained_service_timber_intersections"))
    assert report["mechanics_gates"]["conditional_occupied_geometry"] is False
    assert contract["assessment"]["conditional_occupied_geometry_passed"] is False
    assert all(value is False for value in report["release"].values())
    assert all(r["catalog_resistance_utilization"] is None for r in report["duties"])
