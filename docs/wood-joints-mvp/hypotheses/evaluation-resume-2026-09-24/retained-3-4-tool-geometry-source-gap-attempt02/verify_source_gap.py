#!/usr/bin/env python3
"""Verify the read-only attempt02 source-gap packet and frozen T07/T08 scope."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
TARGET_AXES = {
    "lumber_leg_bolt_left_1",
    "lumber_leg_bolt_left_2",
    "lumber_leg_bolt_right_1",
    "lumber_leg_bolt_right_2",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    packet = load(HERE / "source-gap.json")
    pins = load(HERE / "source-pins.json")
    terminal = load(HERE / "terminal-hashes.json")
    terminal_checked = 0
    for row in terminal["artifacts"]:
        path = HERE / row["path"]
        require(path.is_file(), f"missing packet artifact: {row['path']}")
        require(digest(path) == row["sha256"], f"packet artifact hash mismatch: {row['path']}")
        terminal_checked += 1

    require(packet["decision"] == "NO_COMPLETE_PROFILE_FOUND_IN_CHECKED_PUBLIC_WERA_ROUTES", "unexpected source decision")
    require(packet["screen_status"] == "NOT_RUN_SOURCE_GAP", "a tool screen must not be claimed")
    require(packet["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1", "geometry revision changed")
    require(packet["external_geometry_artifact_found"] is False, "geometry artifact must remain absent")

    checked = 0
    for row in pins["repository_inputs"]:
        path = ROOT / row["path"]
        require(path.is_file(), f"missing pinned input: {row['path']}")
        require(digest(path) == row["sha256"], f"pinned input changed: {row['path']}")
        checked += 1

    base = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
    t07 = load(ROOT / base / "current-fit-transport-closeout-attempt02/evidence-register.json")
    t07_review = load(ROOT / base / "current-fit-transport-closeout-attempt02/parent-review.json")
    cross = load(ROOT / base / "current-fit-transport-option-crosswalk-attempt01/option-crosswalk.json")
    cross_review = load(ROOT / base / "current-fit-transport-option-crosswalk-attempt01/parent-review.json")
    t08 = load(ROOT / base / "current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json")
    t08_review = load(ROOT / base / "current-hardware-material-cost-closeout-attempt01/parent-review.json")
    critical = load(ROOT / base / "current-fit-transport-critical-envelopes-attempt01/critical-envelopes.json")
    critical_review = load(ROOT / base / "current-fit-transport-critical-envelopes-attempt01/parent-review.json")
    operations = load(ROOT / base / "step6-operation-coverage-attempt01/operation-coverage.json")

    require(t07_review["status"] == "PASS_IDENTITY_REGISTER_ONLY_OPERATION_GATES_OPEN", "unexpected T07 parent status")
    require(cross_review["status"] == "PASS_SOURCE_BOUND_OPTION_CROSSWALK_ONLY_ALL_PHYSICAL_GATES_OPEN", "unexpected crosswalk parent status")
    require(t08_review["status"] == "PASS_SOURCE_BOUND_REGISTER_ONLY_WITH_PENDING_PRODUCT_MATERIAL_PRICE_GATES", "unexpected T08 parent status")
    require(critical_review["status"] == "PASS_SOURCE_BOUND_NOMINAL_ENVELOPES_ONLY_ALL_PHYSICAL_GATES_OPEN", "unexpected critical-envelope parent status")
    require(t07["geometry_revision_id"] == cross["geometry_revision_id"] == t08["geometry_revision_id"] == packet["geometry_revision_id"], "T07/T08 geometry revision mismatch")

    retained = t08["retained_axis_rows"]
    retained_ids = {row["axis_id"] for row in retained}
    require(len(retained) == 12 and retained_ids == set(packet["scope"]["retained_bolt_axis_ids"]), "retained 12-axis inventory changed")
    require({row["axis_id"] for row in retained if row["catalog_reference"]["bolt_bolt_depot_product"] == "407"} == TARGET_AXES, "#407 target set changed")
    require(all(row["catalog_reference"]["bolt_bolt_depot_product"] in {"367", "368"} for row in retained if row["axis_id"] not in TARGET_AXES), "non-target retained references changed")

    critical_rows = critical["retained_wire_component_hit_matrix"]
    require(len(critical_rows) == 12, "retained source-CAD component report count changed")
    for axis in TARGET_AXES:
        rows = [row for row in critical_rows if row["axis_id"] == axis]
        require(len(rows) == 3, f"expected three existing component rows for {axis}")
        require(all(row["T07_applied_proxy_profile_id"] == "facom_34_7_16" for row in rows), f"unexpected proxy at {axis}")
        require(all(row["T07_proxy_head_size_mismatch_to_3_4_in_reference"] is True for row in rows), f"size mismatch not recorded at {axis}")
        require(all(row["correct_size_profile_comparator_id"] == "wera_6000_05073287001" for row in rows), f"Wera comparator pointer changed at {axis}")
        require(all(row["correct_size_profile_fit_screened"] is False for row in rows), f"matching-size profile appears screened at {axis}")

    operation_rows = {row["entity_id"]: row for row in operations["axis_records"]}
    require(len(operations["axis_records"]) == 170, "exact-operation register coverage changed")
    for axis in TARGET_AXES:
        row = operation_rows[axis]
        require(row["fit_and_use_limits"]["real_tool_fit_established"] is False, f"real tool fit was cleared at {axis}")
        require(row["fit_and_use_limits"]["physical_fit_established"] is False, f"physical fit was cleared at {axis}")
        require(row["operation_statuses"]["counterhold"]["status"] == "not_established", f"counterhold status changed at {axis}")

    route_rows = packet["source_review"]["checked_manufacturer_routes"]
    require(route_rows and all(row["full_profile_geometry_found"] is False for row in route_rows), "source conclusion claims a full profile")
    require(any(row["route_id"] == "wera_product_family_page" for row in route_rows), "official Wera product page not recorded")
    require(any(row["route_id"] == "wera_datasheet_linked_from_family_page" for row in route_rows), "linked datasheet route not recorded")

    axis_results = {row["axis_id"]: row["status"] for row in packet["axis_dispositions"]}
    require(set(axis_results) == retained_ids, "source-gap disposition must cover exactly 12 retained axes")
    require({axis for axis, status in axis_results.items() if status == "NOT_RUN_SOURCE_GAP"} == TARGET_AXES, "matching-size target set changed")
    require(all(status == "NOT_TARGETED_DIFFERENT_SIZE_REFERENCE" for axis, status in axis_results.items() if axis not in TARGET_AXES), "non-target disposition changed")

    invariants = packet["disposition_invariants"]
    required_false = {
        "geometry_changed",
        "retained_bolt_arrangements_changed",
        "selected_product_or_tool",
        "tool_motion_screen_performed",
        "fit_or_access_screen_performed",
        "native_or_docker_execution",
        "physical_fit_or_access_cleared",
        "cable_service_or_transport_cleared",
        "candidate_criteria_changed",
    }
    require(all(invariants[key] is False for key in required_false), "a prohibited geometry, selection, screen, or gate disposition is recorded")
    require(invariants["all_candidate_criteria_remain_pending"] is True, "candidate criteria cannot be cleared")
    require(invariants["all_existing_physical_operation_statuses_remain_open"] is True, "physical operation gates cannot be cleared")
    print(f"attempt02 source-gap packet verified: {checked} repository pins, {terminal_checked} artifact hashes; 12 retained axes; 4 matching-size targets not screened")


if __name__ == "__main__":
    main()
