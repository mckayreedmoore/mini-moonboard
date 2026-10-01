"""Carry the owner-selected Hillman prep policy onto current WJ axis records.

This is a source-pinned, static evidence inventory. It does not infer cutters
from CAD occupancy or BRep faces, replay CAD, generate a cut ticket, or release
machining. The pilot/countersink values are carried from the selected-baseline
shop checklist as policy; current WJ axis identity/coordinates come from the
reviewed attempt04 manifest and remain a separate source.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
ATTEMPT01 = BASE + "current-full-frame-machining-inventory-attempt01/"
ATTEMPT02 = BASE + "current-full-frame-machining-inventory-attempt02/"
CURRENT_MANIFEST = BASE + "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
AGENTS = "AGENTS.md"
SHOP_CHECKLIST = "docs/floor-flush-shop-checklist.md"

OUT = ROOT / ATTEMPT02 / "inventory.json"

INPUTS = {
    "current_manifest_attempt04": CURRENT_MANIFEST,
    "attempt01_inventory": ATTEMPT01 + "inventory.json",
    "attempt01_producer": "scripts/build_current_full_frame_machining_inventory_attempt01.py",
    "attempt01_readme": ATTEMPT01 + "README.md",
    "repository_agreements": AGENTS,
    "selected_baseline_shop_checklist": SHOP_CHECKLIST,
}

# File-byte pins captured from the current worktree. The manifest's own
# manifest_sha256 and the axis-list digest are also copied into the record.
EXPECTED_INPUT_SHA256 = {
    INPUTS["current_manifest_attempt04"]: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    INPUTS["attempt01_inventory"]: "6a36c53f40f552dc36f214fda0fb3b0f193b9c9918f99b04af637eb4a0adf77f",
    INPUTS["attempt01_producer"]: "10a194415df37d423b11d4a587ad1a013c2ac5ae5d1d81aa58b162dc617e188c",
    INPUTS["attempt01_readme"]: "ef536d2196446cb1469421d30bfe9b55211948738e63b4258534030328381a3c",
    INPUTS["repository_agreements"]: "672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536",
    INPUTS["selected_baseline_shop_checklist"]: "c88463f7b3d861014e6aecd7af8c087ed8fce155389d08faf67b1e11f0659599",
}

REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_MOVED_AXIS_IDS = frozenset(
    {
        "round_kicker_left_center_1",
        "round_kicker_left_center_2",
        "round_kicker_right_center_1",
        "round_kicker_right_center_2",
        "round_panel_lower_left_edge_1",
        "round_panel_lower_left_edge_2",
        "round_panel_lower_right_edge_1",
        "round_panel_lower_right_edge_2",
    }
)

PILOT_DIAMETER_IN = 0.125
PILOT_DIAMETER_MM = 3.175
COUNTERSINK_DIAMETER_IN = 0.375
COUNTERSINK_DIAMETER_MM = 9.525
EXPECTED_CURRENT_AXIS_ROWS_SHA256 = (
    "464841ff6760a78e55f98d5b655672b4d8d962c8cbf50cfe61e47a2d541db4ed"
)
PANEL_MEMBER_DIR = (
    BASE + "current-full-frame-member-solids-attempt01/bundle/members/"
)

# These are the six exact panel-member identities recorded by the pinned
# attempt01 inventory. Hashing the STEP bytes validates artifact identity only;
# it is not geometry replay or a source for tool/cutter dimensions.
PANEL_STEP_IDENTITIES = {
    "kicker_left": (
        PANEL_MEMBER_DIR + "kicker_left.step",
        "4740a18f46b8e8ecc2c01c80f7966228c498e35a09f10d7ccb32b08ea3cd8691",
    ),
    "kicker_right": (
        PANEL_MEMBER_DIR + "kicker_right.step",
        "d70c1fedf1c18304818a0f3adefdef0f64204f055a18d941ecd2b91a8dfe32b5",
    ),
    "main_lower_left": (
        PANEL_MEMBER_DIR + "main_lower_left.step",
        "78e2bd7b3a3f4cb6f70a1a2156ae3143cb936b29e5560dd6fd0cf6142aac6270",
    ),
    "main_lower_right": (
        PANEL_MEMBER_DIR + "main_lower_right.step",
        "408d8ed97edf27954fa63221096af25da56a5aab02d53f77ecccbcfafb5b5d90",
    ),
    "main_upper_left": (
        PANEL_MEMBER_DIR + "main_upper_left.step",
        "4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7",
    ),
    "main_upper_right": (
        PANEL_MEMBER_DIR + "main_upper_right.step",
        "2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f",
    ),
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded)


def read_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object: {relative}")
    return value


def index_unique(
    rows: list[dict[str, Any]], key: str, label: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row[key]
        if value in indexed:
            raise ValueError(f"Duplicate {label} identifier: {value}")
        indexed[value] = row
    return indexed


def verify_input_pins() -> dict[str, dict[str, Any]]:
    pins: dict[str, dict[str, Any]] = {}
    for label, relative in INPUTS.items():
        expected = EXPECTED_INPUT_SHA256[relative]
        raw = (ROOT / relative).read_bytes()
        actual = sha256(raw)
        if actual != expected:
            raise ValueError(
                f"Pinned source drift ({label}): {relative}: expected {expected}, got {actual}"
            )
        pins[relative] = {"sha256": actual, "size_bytes": len(raw)}
    return pins


def _check_source_contract(agents_text: str, checklist_text: str) -> None:
    required_agents = (
        "selected a lead-hole pilot plus face countersink",
        "Preserve the current",
        "66 Hillman axes (58 unchanged and eight previously owner-directed moves)",
        "retain the 66-screw count and purchased screw policy",
    )
    for phrase in required_agents:
        if phrase not in agents_text:
            raise ValueError(f"Pinned AGENTS.md no longer contains required direction: {phrase}")

    required_checklist = (
        "#### Hillman 42605 panel/kicker — 66 screws",
        "#10 insert: 1/8 in (3.175 mm) pilot and 3/8 in countersink",
        "through plywood into the 2×6 so the flat head seats flush",
        "Before production, drill/countersink/drive one offcut",
    )
    for phrase in required_checklist:
        if phrase not in checklist_text:
            raise ValueError(
                "Pinned selected-baseline checklist no longer contains the "
                f"required Hillman policy statement: {phrase}"
            )


def _validate_attempt01(prior: dict[str, Any]) -> None:
    if prior.get("attempt_id") != "current-full-frame-machining-inventory-attempt01":
        raise ValueError("Expected the immutable machining-inventory attempt01 record")
    if prior.get("geometry_revision_id") != REVISION:
        raise ValueError("Attempt01 has a different reviewed geometry revision")
    if prior.get("criterion_effect", {}).get("all_machining_represented") is not False:
        raise ValueError("Attempt01 unexpectedly claims complete machining")
    declared = prior.get("record_sha256")
    without_digest = dict(prior)
    without_digest.pop("record_sha256", None)
    if canonical_sha256(without_digest) != declared:
        raise ValueError("Attempt01 canonical record digest does not validate")


def _validate_panel_step_identities(prior: dict[str, Any]) -> dict[str, dict[str, Any]]:
    members = prior.get("members", [])
    panel_rows = {
        row.get("member_id"): row
        for row in members
        if row.get("member_kind") == "plywood_panel"
    }
    if set(panel_rows) != set(PANEL_STEP_IDENTITIES):
        raise ValueError("Attempt01 panel member identities differ from the six pinned panels")

    step_pins: dict[str, dict[str, Any]] = {}
    for member_id, (expected_path, expected_sha256) in PANEL_STEP_IDENTITIES.items():
        row = panel_rows[member_id]
        if row.get("finished_step_path") != expected_path:
            raise ValueError(f"Attempt01 STEP path drift for exact panel {member_id}")
        if row.get("finished_step_sha256") != expected_sha256:
            raise ValueError(f"Attempt01 recorded STEP digest drift for exact panel {member_id}")
        if row.get("prior_cut_inventory_coverage") != "not_covered_by_prior_cut_inventory":
            raise ValueError(f"Unexpected prior cut-inventory coverage for panel {member_id}")
        step_path = ROOT / expected_path
        raw = step_path.read_bytes()
        actual_sha256 = sha256(raw)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"Panel STEP artifact drift for {member_id}: expected {expected_sha256}, "
                f"got {actual_sha256}"
            )
        step_pins[expected_path] = {
            "sha256": actual_sha256,
            "size_bytes": len(raw),
            "member_id": member_id,
            "source_role": "finished panel BRep artifact identity only; not a cut decomposition",
        }
    return step_pins


def _axis_policy_record(axis: dict[str, Any], manifest_path: str, manifest_sha: str) -> dict[str, Any]:
    return {
        "axis_id": axis["axis_id"],
        "current_wj_coordinate_and_receiver_source": {
            "path": manifest_path,
            "file_sha256": manifest_sha,
            "record_location": "panel_kicker_screw_axes[] selected by axis_id",
            "axis_record_verbatim": copy.deepcopy(axis),
        },
        "owner_selected_hillman_prep_policy": {
            "policy_id": "hillman-42605-kobalt-80277-pilot-countersink-policy",
            "source_path": SHOP_CHECKLIST,
            "source_sha256": EXPECTED_INPUT_SHA256[SHOP_CHECKLIST],
            "source_scope": (
                "Selected-baseline shop policy. AGENTS.md requires this purchased "
                "screw policy to remain with the WJ candidate; this source does not "
                "supply a WJ-specific shop release or coordinate sheet."
            ),
            "purchased_screw": "Hillman/Fas-n-Tite 42605 #10 x 2-1/2 in (63.5 mm)",
            "pilot_diameter_in": PILOT_DIAMETER_IN,
            "pilot_diameter_mm": PILOT_DIAMETER_MM,
            "pilot_type": "owner-selected lead hole",
            "face_countersink_diameter_in": COUNTERSINK_DIAMETER_IN,
            "face_countersink_diameter_mm": COUNTERSINK_DIAMETER_MM,
            "face_seating_instruction": "head seats flush; do not overdrive through face veneer",
            "offcut_trial_required_before_production": True,
        },
        "unresolved_current_operation_fields": {
            "pilot_depth_mm": None,
            "countersink_depth_mm": None,
            "countersink_included_angle_deg": None,
            "location_tolerance_mm": None,
            "datum_and_setup_sequence": None,
            "physical_receiver_material_section_and_condition": None,
            "offcut_trial_observation": None,
            "axis_to_hold_led_cut_interaction_evidence": None,
            "net_section_or_local_section_evidence": None,
        },
        "status": "policy_dimensions_carried_forward_current_WJ_operation_unresolved",
        "not_a_cutter_inference": True,
        "not_a_machining_or_fabrication_release": True,
    }


def build() -> dict[str, Any]:
    pins = verify_input_pins()
    manifest = read_json(CURRENT_MANIFEST)
    prior = read_json(INPUTS["attempt01_inventory"])
    _validate_attempt01(prior)
    panel_step_pins = _validate_panel_step_identities(prior)
    _check_source_contract(
        (ROOT / AGENTS).read_text(encoding="utf-8"),
        (ROOT / SHOP_CHECKLIST).read_text(encoding="utf-8"),
    )

    if manifest.get("geometry_revision_id") != REVISION:
        raise ValueError("Current attempt04 manifest has a different geometry revision")
    if manifest.get("schema") != "wood_joint_current_full_frame_input_manifest/v3":
        raise ValueError("Expected current full-frame input manifest schema v3")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04":
        raise ValueError("Expected current full-frame input manifest attempt04")

    current_axes = manifest.get("panel_kicker_screw_axes", [])
    current_axis_rows_sha256 = canonical_sha256(current_axes)
    if current_axis_rows_sha256 != EXPECTED_CURRENT_AXIS_ROWS_SHA256:
        raise ValueError("Current attempt04 axis identity/coordinate digest drift")
    current_by_id = index_unique(current_axes, "axis_id", "current panel/kicker screw axis")
    prior_axes = prior.get("axis_maps", {}).get("panel_kicker_screw_axes", [])
    prior_by_id = index_unique(prior_axes, "axis_id", "attempt01 panel/kicker screw axis")
    if len(current_by_id) != 66 or len(prior_by_id) != 66:
        raise ValueError("Expected exactly 66 current and attempt01 panel/kicker screw axes")
    if set(current_by_id) != set(prior_by_id):
        raise ValueError("Current WJ axis identities differ from attempt01")

    expected_per_panel = {
        "main_lower_left": 12,
        "main_lower_right": 12,
        "main_upper_left": 12,
        "main_upper_right": 12,
        "kicker_left": 9,
        "kicker_right": 9,
    }
    current_per_panel = Counter(row["panel_member"] for row in current_axes)
    if dict(current_per_panel) != expected_per_panel:
        raise ValueError(f"Unexpected current screw-axis panel counts: {dict(current_per_panel)}")

    moved_ids = {
        row["axis_id"]
        for row in current_axes
        if row.get("current_location_status") == "moved"
    }
    retained_ids = {
        row["axis_id"]
        for row in current_axes
        if row.get("current_location_status") == "source_station_retained"
    }
    if moved_ids != EXPECTED_MOVED_AXIS_IDS or len(retained_ids) != 58:
        raise ValueError(
            "Expected the eight owner-directed moved axes plus 58 retained source stations"
        )
    if moved_ids & retained_ids or moved_ids | retained_ids != set(current_by_id):
        raise ValueError("Current screw-axis location statuses are incomplete or overlapping")

    axis_differences = []
    expanded_screw_rows = []
    for axis in current_axes:
        axis_id = axis["axis_id"]
        old = prior_by_id[axis_id]
        # Attempt01 deliberately carried only direction and membership. Require
        # these stable source facts to agree, while attempt02 binds the current
        # origin, receiver and owner-move record directly to attempt04.
        for field in ("axis_global_xyz", "panel_member", "receiver_member"):
            if axis[field] != old[field]:
                raise ValueError(
                    f"Attempt01/current manifest mismatch for {axis_id}: {field}"
                )
        if not isinstance(axis.get("origin_global_xyz_mm"), list) or len(axis["origin_global_xyz_mm"]) != 3:
            raise ValueError(f"Current axis lacks a three-component origin: {axis_id}")
        if not isinstance(axis.get("axis_global_xyz"), list) or len(axis["axis_global_xyz"]) != 3:
            raise ValueError(f"Current axis lacks a three-component direction: {axis_id}")
        expanded_screw_rows.append(
            _axis_policy_record(axis, CURRENT_MANIFEST, pins[CURRENT_MANIFEST]["sha256"])
        )
        if axis.get("current_location_status") == "moved":
            axis_differences.append(
                {
                    "axis_id": axis_id,
                    "old_start_global_xyz_mm": axis["owner_moved_axis_record"][
                        "old_start_global_xyz_mm"
                    ],
                    "new_start_global_xyz_mm": axis["origin_global_xyz_mm"],
                    "translation_global_xyz_mm": axis["translation_from_source_xyz_mm"],
                    "previous_receiver_member": axis["previous_receiver_member"],
                    "receiver_member": axis["receiver_member"],
                }
            )

    if len(axis_differences) != 8:
        raise ValueError("Expected eight axis movement records")

    record = copy.deepcopy(prior)
    record["schema"] = "wood_joint_current_full_frame_machining_gap_inventory/v2"
    record["attempt_id"] = "current-full-frame-machining-inventory-attempt02"
    record["status"] = "current_screw_axes_and_owner_policy_mapped_operation_schedule_incomplete"
    record["source_pins"] = {**pins, **panel_step_pins}
    record["source_content_digests"] = {
        **prior.get("source_content_digests", {}),
        "attempt01_record_sha256": prior["record_sha256"],
        "attempt04_manifest_declared_sha256": manifest["manifest_sha256"],
        "attempt04_current_screw_axis_rows_canonical_sha256": current_axis_rows_sha256,
        "attempt01_inventory_record_sha256": prior["record_sha256"],
    }
    record["axis_maps"]["panel_kicker_screw_axes"] = expanded_screw_rows
    record["panel_screw_policy_binding"] = {
        "policy_id": "hillman-42605-kobalt-80277-pilot-countersink-policy",
        "operation_dimensions": {
            "lead_hole_pilot_diameter_in": PILOT_DIAMETER_IN,
            "lead_hole_pilot_diameter_mm": PILOT_DIAMETER_MM,
            "face_countersink_diameter_in": COUNTERSINK_DIAMETER_IN,
            "face_countersink_diameter_mm": COUNTERSINK_DIAMETER_MM,
        },
        "policy_source": {
            "path": SHOP_CHECKLIST,
            "sha256": pins[SHOP_CHECKLIST]["sha256"],
            "rows": "Hillman 42605 panel/kicker — 66 screws; Pilot / countersink; Offcut trial",
            "applicability": (
                "Selected-baseline checklist policy source, retained for the WJ "
                "candidate by AGENTS.md. It does not define current-WJ coordinate "
                "datums, receiver sections, operation depth, tolerances, or a shop release."
            ),
        },
        "current_wj_coordinate_source": {
            "path": CURRENT_MANIFEST,
            "sha256": pins[CURRENT_MANIFEST]["sha256"],
            "manifest_id": manifest["manifest_id"],
            "axis_rows": len(current_axes),
            "axis_rows_canonical_sha256": current_axis_rows_sha256,
            "coordinate_fields": [
                "origin_global_xyz_mm",
                "axis_global_xyz",
                "translation_from_source_xyz_mm",
                "owner_moved_axis_record",
                "panel_member",
                "receiver_member",
            ],
        },
        "axis_counts": {
            "all_current_axes": 66,
            "source_station_retained": 58,
            "owner_directed_moved": 8,
            "by_panel_member": dict(sorted(current_per_panel.items())),
        },
        "owner_directed_moves": axis_differences,
        "unresolved_for_every_current_axis": {
            "pilot_depth_mm": None,
            "countersink_depth_mm": None,
            "countersink_included_angle_deg": None,
            "location_tolerance_mm": None,
            "datum_and_setup_sequence": None,
            "physical_receiver_material_section_and_condition": None,
            "offcut_trial_observation": None,
            "interaction_with_panel_holes_and_other_cuts": None,
            "local_net_section_evidence": None,
        },
        "status": "policy_dimensions_source_bound_and_carried_to_66_axes; current_WJ_operations_unresolved",
        "cutting_or_drilling_released": False,
    }
    record["criterion_effect"] = {
        "all_machining_represented": False,
        "disposition": "pending",
        "reason": (
            "Attempt02 source-binds owner-selected Hillman pilot/countersink policy "
            "dimensions to all 66 current WJ axis IDs and preserves current global "
            "coordinates. It does not establish complete panel operation decompositions, "
            "depths, countersink angle, tolerances, setups, physical receivers, or "
            "candidate-specific shop instructions. The 92 candidate and 12 retained "
            "bolt-hole operations also remain unresolved."
        ),
    }
    record["gap_register"] = [
        {
            **gap,
            **(
                {
                    "finding": (
                        "No source-bound current-WJ panel cut decomposition exists for "
                        "the six exact panel bodies. Selected-baseline stock/profile and "
                        "hold/LED records are static inputs, not a reviewed WJ cut ticket."
                    ),
                    "required_evidence": (
                        "Current-WJ panel operation schedule for each exact body, with "
                        "source-bound blank/profile/edge and hold/LED/screw operations; "
                        "explicitly mark non-applicable operations and retain unknown "
                        "tolerances or setup fields as unresolved."
                    ),
                }
                if gap["gap_id"] == "MACH-GAP-01"
                else {
                    "finding": (
                        "The selected-baseline checklist supplies owner-selected 3.175 mm "
                        "lead-hole pilot and 9.525 mm face-countersink diameters, now mapped "
                        "to all 66 current WJ axes. Pilot/countersink depths, countersink "
                        "angle, location tolerances, setups, offcut evidence, and physical "
                        "receiver conditions remain unresolved; selected-baseline coordinates "
                        "are not used for the eight moved WJ axes."
                    ),
                    "required_evidence": (
                        "A candidate-specific shop instruction or verified equivalent that "
                        "binds each current WJ axis and receiver to the retained owner policy, "
                        "defines operation depth/face/tool setup/tolerance where needed, and "
                        "records receiver/fit and offcut evidence. Do not infer from CAD occupancy."
                    ),
                }
                if gap["gap_id"] == "MACH-GAP-04"
                else {}
            ),
        }
        for gap in prior["gap_register"]
    ]
    record["limits"] = list(prior["limits"]) + [
        "The Kobalt #10 1/8 in pilot and 3/8 in face-countersink diameters are policy values sourced from the selected-baseline checklist and carried onto the 66 current WJ axis IDs; they are not verified per-axis shop operations or physical receiver evidence.",
        "Current WJ coordinates and receiver associations are copied from attempt04 manifest axis rows; they are separate from the policy source and are not selected-baseline local shop coordinates.",
        "Pilot depth, countersink depth/angle, location tolerance, setup sequence, offcut result, receiver material/section, and interactions with panel holes remain unresolved for every current axis.",
        "No panel screw preparation, panel outline, hold/LED operation, candidate-bolt hole, or retained-frame-bolt hole is released for cutting or drilling.",
    ]
    record.pop("record_sha256", None)
    record["record_sha256"] = canonical_sha256(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected = build()
    if args.write:
        if OUT.exists():
            raise SystemExit(f"Refusing to overwrite existing inventory: {OUT}")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        if not OUT.exists():
            raise SystemExit(f"Inventory is missing: {OUT}")
        actual = json.loads(OUT.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("Attempt02 inventory is stale or differs from pinned source records")
    print(
        f"{'WROTE' if args.write else 'PASS'} {OUT.relative_to(ROOT)} "
        f"sha256={expected['record_sha256']} axes=66 policy=3.175mm+9.525mm "
        "machining_complete=false release=false"
    )


if __name__ == "__main__":
    main()
