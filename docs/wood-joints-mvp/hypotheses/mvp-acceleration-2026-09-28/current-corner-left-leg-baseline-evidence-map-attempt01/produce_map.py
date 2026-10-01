#!/usr/bin/env python3
"""Map only the retained left LEG bolt pair to existing baseline evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[5]
SERIES = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = Path(__file__).resolve().parent
TRANSFER = SERIES / "current-corner-left-leg-onward-transfer-register-attempt01/register.json"
CORNER_A12 = SERIES / "current-corner-native-demand-export-attempt03/corner-demand-report.json"
CORNER_A1 = SERIES / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json"
AXES = Path("docs/floor-flush-construction-kerf-right/connection-axes.csv")
HARDWARE = Path("docs/floor-flush-construction-kerf-right/bolt-hardware.csv")
DATUMS = Path("docs/floor-flush-construction-kerf-right/bolt-member-datums.csv")
FRAME_REVIEW = Path("docs/wood-joints-mvp/current-frame-bolt-review.md")
BASELINE = Path("fea/results/floor-runner-mvp")
OUTPUT = HERE / "baseline-evidence-map.json"

PINNED_SOURCE_SHA256 = {
    "current-candidate.json": "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    str(AXES): "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58",
    str(HARDWARE): "a3081ca72f92271ae21967684c5b7a459619dc0cf5c00ac53e7d8cecd748afd8",
    str(DATUMS): "1ca8c4c52b88792c583222ff36cac13dad571b43df4045e7cbd96157729be2db",
    str(FRAME_REVIEW): "20067540bd318a3639e90278874bf793445a14c34bd316e18c6e508c2a518c89",
    "fea/results/floor-runner-mvp/a12-rear/checks.json": "9ed713df60c1b031984e8e99a4a7f8c0d7dd59c0a81b0f008e14797c09aa2223",
    "fea/results/floor-runner-mvp/a12-rear/geometry.json": "e62f402f10403e205f279e60fe991ef8d0b9b13ff73efb981ff33090e389e747",
    "fea/results/floor-runner-mvp/a12-rear/manifest.json": "5d721fa0b09950853b721b3dced5f0a1d0dc9f83a3af2fbb6b1797df2b02a388",
    "fea/results/floor-runner-mvp/a1-rear/checks.json": "2ffa4998eb208d031805b3eb36817001180a263677096b88d778c4eb9a60fdef",
    "fea/results/floor-runner-mvp/a1-rear/geometry.json": "e62f402f10403e205f279e60fe991ef8d0b9b13ff73efb981ff33090e389e747",
    "fea/results/floor-runner-mvp/a1-rear/manifest.json": "d65a6d63e8e62bb6af6c8b82e4800f98b066a995125b5cfe33be541d40d7b21a",
    str(TRANSFER): "b435f23d059d8b8399bcc5ab4afdbaa71171bac476b3a50953d68f8189cac8b0",
}


class MapError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MapError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected_json_object:{path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_pins() -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in PINNED_SOURCE_SHA256.items():
        path = ROOT / relative
        require(path.is_file(), f"pinned_source_exists:{relative}")
        actual = sha(path)
        require(actual == expected, f"pinned_source_sha256:{relative}")
        observed[relative] = actual
    transfer = load_json(ROOT / TRANSFER)
    for absolute_path, expected in transfer.get("source_sha256", {}).items():
        path = Path(absolute_path)
        require(path.is_file(), f"transfer_source_exists:{absolute_path}")
        require(sha(path) == expected, f"transfer_register_source_sha256:{absolute_path}")
        observed[str(path.relative_to(ROOT))] = expected
    return dict(sorted(observed.items()))


def geometry_rows() -> dict[str, Any]:
    axes = {row["name"]: row for row in read_csv(ROOT / AXES) if row.get("name") in AXIS_IDS}
    hardware = {row["name"]: row for row in read_csv(ROOT / HARDWARE) if row.get("name") in AXIS_IDS}
    datums = [row for row in read_csv(ROOT / DATUMS) if row.get("connection") in AXIS_IDS]
    require(set(axes) == set(hardware) == set(AXIS_IDS), "two_baseline_axis_and_hardware_rows")
    require(len(datums) == 4, "two_axis_rows_per_receiving_member")
    for axis_id in AXIS_IDS:
        row = axes[axis_id]
        hw = hardware[axis_id]
        require(row["kind"] == "bolt", f"{axis_id}_is_through_bolt")
        require((row["first_member"], row["second_member"]) == ("base_side_left", "lumber_leg_left"), f"{axis_id}_receiver_pair")
        require(float(row["modeled_diameter_mm"]) == 12.7 and float(row["modeled_length_mm"]) == 203.2, f"{axis_id}_nominal_dimensions")
        require(float(hw["grip_mm"]) == 177.8 and float(hw["washer_od_mm"]) == 34.925, f"{axis_id}_hardware_schedule")
        require(hw["thread_length_mm"] == "" and hw["shop_purchased_length_mm"] == "", f"{axis_id}_thread_and_purchased_length_unrecorded")
    return {
        "source_packet": str(Path("docs/floor-flush-construction-kerf-right")),
        "source_packet_role": "selected candidate's kerf-right construction/geometry option; six baseline analytical cases use the official 4x4 analytical width, so this does not create another load case",
        "axis_rows": [axes[axis_id] for axis_id in AXIS_IDS],
        "hardware_rows": [hardware[axis_id] for axis_id in AXIS_IDS],
        "member_datums": datums,
        "dimension_interpretation": {
            "nominal_bolt_diameter_mm": 12.7,
            "nominal_length_mm": 203.2,
            "wood_grip_mm": 177.8,
            "per_member_bearing_length_mm": [88.9, 88.9],
            "finished_clearance_opening_mm": [13.49375, 14.2875],
            "washer_od_mm": 34.925,
            "washer_thickness_mm": 3.175,
            "purchased_length_and_thread_dimensions": "blank in the source schedule; actual delivery is not established",
        },
    }


def archived_case(case_id: str) -> dict[str, Any]:
    folder = ROOT / BASELINE / case_id
    manifest = load_json(folder / "manifest.json")
    checks = load_json(folder / "checks.json")
    require(manifest.get("candidate") == checks.get("candidate") == "compact-floor-flush-development", f"{case_id}_selected_baseline_candidate")
    require(manifest.get("files", {}).get("checks.json") == sha(folder / "checks.json"), f"{case_id}_checks_manifest_binding")
    require(manifest.get("files", {}).get("geometry.json") == sha(folder / "geometry.json"), f"{case_id}_geometry_manifest_binding")
    require(checks.get("status") == "LISTED_FIRST_STAGE_SCREENS_MET_WITH_OPEN_LIMITS", f"{case_id}_historical_screen_status")
    require(checks.get("qualified_for_design") is False, f"{case_id}_old_check_not_qualified")
    pair_key = "base_side_left / lumber_leg_left"
    group = checks["force_directed_end_branch"]["joint_groups"][pair_key]
    require(group.get("bolt_names") == AXIS_IDS and group.get("applicable") is True, f"{case_id}_same_two_bolt_group")
    bolts: dict[str, Any] = {}
    for axis_id in AXIS_IDS:
        row = checks["bolts"][axis_id]
        bolts[axis_id] = {
            "nominal_diameter_mm": row["diameter_mm"],
            "member_bearing_lengths_mm": row["bearing_lengths_mm"],
            "historical_baseline_lateral_demand_N": row["lateral_demand_n"],
            "historical_directional_lateral_reference_N": row["lateral_reference_n"],
            "historical_lateral_ratio": row["lateral_ratio"],
            "historical_governing_yield_mode": row["dowel_reference"]["governing_mode"],
            "historical_absolute_axial_increment_N": row["hardware"]["absolute_axial_increment_n"],
            "signed_axial_action_recorded_in_this_check": False,
            "fully_threaded_root_sensitivity_ratio_nonadopted": row["fully_threaded_sensitivity"]["lateral_ratio"],
            "placement_screens_by_receiver": row["placement"],
            "nominal_diameter_condition": row["nominal_diameter_condition"],
            "bolt_result_qualified_for_design": row["qualified_for_design"],
        }
    return {
        "baseline_candidate": checks["candidate"],
        "archive_manifest_path": str((BASELINE / case_id / "manifest.json")),
        "archive_manifest_sha256": sha(folder / "manifest.json"),
        "checks_path": str((BASELINE / case_id / "checks.json")),
        "checks_sha256": sha(folder / "checks.json"),
        "geometry_path": str((BASELINE / case_id / "geometry.json")),
        "geometry_sha256": sha(folder / "geometry.json"),
        "case_check_status": checks["status"],
        "case_qualified_for_design": checks["qualified_for_design"],
        "producer_validity": checks["producer_validity"],
        "same_pair_group_record": group,
        "bolts": bolts,
        "historical_scope": "Selected-baseline case-specific demands and component screens only; source-level method/evidence map, not a transferred current corner acceptance.",
    }


def build(source_hashes: dict[str, str]) -> dict[str, Any]:
    transfer = load_json(ROOT / TRANSFER)
    require(transfer.get("schema") == "current_corner_left_leg_onward_transfer_register/v1", "parent_transfer_schema")
    require(transfer.get("retained_original_axes") == AXIS_IDS and transfer.get("new_block_axes_in_register") == [], "parent_transfer_keeps_original_axes_separate")
    require(transfer.get("case_count") == 2 and len(transfer.get("rows", [])) == 56, "parent_transfer_two_cases_all_seven_increments")

    reports = {"a12-rear": load_json(ROOT / CORNER_A12), "a1-rear": load_json(ROOT / CORNER_A1)}
    for case_id, report in reports.items():
        contract = report["source_contract"]
        require(report.get("case_id") == case_id, f"{case_id}_corner_report_identity")
        require(contract.get("retained_original_leg_runner_axis_count") == 12, f"{case_id}_original_twelve_arrangements")
        require(contract.get("new_block_axis_count") == 92, f"{case_id}_new_ninety_two_axes")
    axes = geometry_rows()
    baseline_cases = {case_id: archived_case(case_id) for case_id in ("a12-rear", "a1-rear")}
    return {
        "schema": "current_corner_left_leg_baseline_evidence_map/v1",
        "status": "TWO_CASE_CONDITIONAL_TRANSFER_LINKED_TO_UNQUALIFIED_BASELINE_CHECKS",
        "scope": {
            "cases": ["a12-rear", "a1-rear"],
            "interfaces": AXIS_IDS,
            "receiver_pair": ["base_side_left", "lumber_leg_left"],
            "source_corner": "left outer BG001/BG003/BG045 case-bound reports",
            "new_signed_action_rows_path": str(TRANSFER),
            "new_signed_action_rows_sha256": sha(ROOT / TRANSFER),
            "new_signed_action_rows_count": len(transfer["rows"]),
            "new_signed_action_source_reports": {
                "a12-rear": {"path": str(CORNER_A12), "sha256": sha(ROOT / CORNER_A12)},
                "a1-rear": {"path": str(CORNER_A1), "sha256": sha(ROOT / CORNER_A1)},
            },
            "original_twelve_and_new_ninety_two_are_separate": True,
            "new_axes_are_not_counted_as_or_substituted_for_the_original_bolt_pair": True,
        },
        "existing_selected_baseline_geometry": axes,
        "existing_selected_baseline_resistance_evidence": baseline_cases,
        "geometry_and_demand_dependency": {
            "retained_bolt_axis_identity": "The selected source schedule and current-frame review retain the two named left LEG axes, their receiver pair, station, nominal bolt diameter/length, and grip; no geometry or hardware was changed by this map.",
            "changed_receiver": "base_side_left is a shared current-corner receiver with ten new candidate bolt axes in the reviewed 92-axis layout. lumber_leg_left has no current candidate bore axis in the current-frame-bolt review. New holes in base_side_left affect the local net-section, group tear-out/splitting and remaining-section evidence for the original two-bolt pair; they do not establish a failure or imply that the old bolt axes moved.",
            "baseline_check_limits": "The selected-baseline a12-rear and a1-rear checks contain case-specific scalar lateral demands, direction-dependent single-bolt reference values, ratios and absolute axial increments. Their `qualified_for_design` values are false, and the archived checks do not provide a signed axial action in the extracted per-bolt record. The signed seven-state corner vectors remain only in the linked parent transfer register.",
            "reuse_boundary": "Existing source geometry, hardware schedule, material/method records and per-bolt component-resistance calculations are traceable for these retained arrangements. Historical demands, ratios, group results and candidate-level status are not transferred to the corner candidate. The specific affected local section dependency is the changed base_side_left bore pattern; this map makes no blanket claim that every original bolt needs requalification.",
            "criteria_or_input_not_supplied_by_legacy_map": [
                "A current signed action-to-resistance comparison for the new case-bound seven-state vectors using the actual directional grain/load basis.",
                "A mapping of the existing base_side_left net-section/group/splitting resistance evidence onto the 92-axis current receiver geometry.",
                "Delivered bolt/thread transition and purchased-length measurements remain blank in the construction schedule; no actual part conformance is inferred."
            ],
        },
        "limits": [
            "This is a read-only source/evidence map. It computes no force, resistance, capacity, utilization, acceptance, or solver result.",
            "The selected-baseline archives are historical context. The six-case baseline pass does not qualify these new corner loads or the changed receiver.",
            "The retained original 12 arrangements remain separate from the 92 new corner axes. Only the two original left LEG arrangements directly connected to base_side_left are mapped here.",
            "Full-thread-root sensitivity is reported only as non-adopted historical context; the partially threaded bolt basis and delivery checks remain applicable.",
        ],
        "source_pins_sha256": source_hashes,
        "producer": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": sha(Path(__file__).resolve()),
        },
    }


AXIS_IDS = ["lumber_leg_bolt_left_1", "lumber_leg_bolt_left_2"]


def run(write: bool) -> None:
    sources = verify_pins()
    result = build(sources)
    encoded = json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if write:
        OUTPUT.write_text(encoded, encoding="utf-8")
        print(json.dumps({
            "status": result["status"],
            "cases": list(result["existing_selected_baseline_resistance_evidence"]),
            "interfaces": result["scope"]["interfaces"],
            "new_signed_action_register_sha256": result["scope"]["new_signed_action_rows_sha256"],
            "baseline_cases_unqualified": {
                case: row["case_qualified_for_design"]
                for case, row in result["existing_selected_baseline_resistance_evidence"].items()
            },
        }, indent=2))
    else:
        require(OUTPUT.is_file(), "baseline_evidence_map_exists")
        stored = json.loads(OUTPUT.read_text(encoding="utf-8"))
        require(stored == json.loads(encoded), "baseline_evidence_map_reproduces_from_pinned_sources")
        print("verified two-case left LEG baseline evidence map and source pins")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    run(args.write)


if __name__ == "__main__":
    try:
        main()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError, AssertionError) as error:
        print(f"LEFT_LEG_BASELINE_EVIDENCE_MAP_BLOCKED: {error}", file=sys.stderr)
        raise
