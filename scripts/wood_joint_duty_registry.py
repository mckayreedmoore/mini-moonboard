"""Build a source-bound crosswalk for the 24 former angle duties.

This registry accounts for proposed owners and source axes. It does not accept
replacement joints or run CAD geometry checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "docs/wood-joints-mvp/duty-registry.json"
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
INTERFACES = ROOT / "docs/wood-joints-mvp/interfaces.json"
WJ04_PROBE = ROOT / "docs/wood-joints-mvp/wj04-probe.json"
WJ05_RECEIVER_AUDIT = ROOT / "docs/wood-joints-mvp/wj05-receiver-audit.json"
WJ05_RECEIVER_SCRIPT = ROOT / "scripts/wood_joint_wj05_receiver_audit.py"
WJ06_RESIDUAL_SCRIPT = ROOT / "scripts/wood_joint_wj06_residual_probe.py"
WJ06_RESIDUAL_REPORT = ROOT / "docs/wood-joints-mvp/wj06-residual-probe.json"
CANDIDATE = "compact-floor-flush-wood-joints-development"
SCHEMA = "wood_joint_duty_registry/v1"


class RegistryError(ValueError):
    """Raised when source duty accounting is ambiguous or incomplete."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return _sha256(data)


def _read_json(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(parsed, dict):
        raise RegistryError(f"Expected JSON object in {path.relative_to(ROOT)}")
    return parsed, data


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _binding_matches(observed: str | None, expected: str) -> bool:
    return observed == expected


def validate_duty_assignments(
    expected_duty_ids: list[str], assignment_rows: list[dict]
) -> None:
    """Require exactly one accounting row for every source duty."""
    if any(not isinstance(duty_id, str) or not duty_id for duty_id in expected_duty_ids):
        raise RegistryError("Source duty IDs must be non-empty strings")
    assigned_ids = [row.get("legacy_duty_id") for row in assignment_rows]
    if any(not isinstance(duty_id, str) or not duty_id for duty_id in assigned_ids):
        raise RegistryError("Assigned duty IDs must be non-empty strings")
    expected_counts = Counter(expected_duty_ids)
    if duplicates := sorted(duty_id for duty_id, count in expected_counts.items() if count > 1):
        raise RegistryError(f"Duplicate source duties: {duplicates}")

    assigned_counts = Counter(assigned_ids)
    duplicates = sorted(
        str(duty_id) for duty_id, count in assigned_counts.items() if count > 1
    )
    missing = sorted(set(expected_duty_ids) - set(assigned_ids))
    unexpected = sorted(str(duty_id) for duty_id in set(assigned_ids) - set(expected_duty_ids))
    if duplicates or missing or unexpected:
        details = []
        if duplicates:
            details.append(f"duplicate assignments={duplicates}")
        if missing:
            details.append(f"missing assignments={missing}")
        if unexpected:
            details.append(f"unexpected assignments={unexpected}")
        raise RegistryError("Duty assignment accounting failed: " + "; ".join(details))


def _inventory_axis_hash(rows: list[dict]) -> str:
    return _canonical_sha256(rows)


def _wj06_script_contract(script_text: str) -> dict[str, bool]:
    """Check source markers without importing or executing the CadQuery script."""
    return {
        "wj03_duty_set_markers": all(
            marker in script_text
            for marker in (
                'f"clip_timber_header_outer_{side}"',
                'f"clip_angle_base_{side}"',
            )
        ),
        "wj04_duty_marker": 'WJ04_DUTY = "clip_horizontal_lower_right_1"' in script_text,
        "wj05_duty_set_markers": all(
            marker in script_text
            for marker in (
                'f"clip_split_header_center_{side}"',
                'f"clip_split_base_center_{side}"',
            )
        ),
        "generic_owner_marker": 'f"wj06_{duty_id}"' in script_text,
        "center_owner_marker": 'f"wj05_center_node_{duty[\'side\']}"' in script_text,
        "diagnostic_topology_marker": "one-piece solid-sawn orthogonal face cleat" in script_text,
        "four_provisional_axis_marker": all(
            marker in script_text
            for marker in (
                '("face_a", hosts[0], na, nb, wa, corner.dot(na), wb)',
                '("face_b", hosts[1], nb, na, wb, corner.dot(nb), wa)',
                "enumerate((-AXIS_EDGE_OFFSET_MM, AXIS_EDGE_OFFSET_MM), 1)",
            )
        ),
        "nine_trial_variants_marker": "WIDTHS_MM = (38.1, 63.5, 88.9)" in script_text,
        "explicit_no_acceptance_marker": '"candidate_layout_accepted": False' in script_text,
    }


def _add_assignment(
    rows: list[dict],
    *,
    duty_id: str,
    owner_id: str | None,
    evidence_kind: str,
    evidence_path: str,
    owner_status: str,
    topology: str | None,
    interface_ids: list[str] | None = None,
    unresolved: list[str] | None = None,
    legacy_duty_interface_ids: list[str] | None = None,
) -> None:
    rows.append(
        {
            "legacy_duty_id": duty_id,
            "proposed_owner_id": owner_id,
            "owner_assignment_status": owner_status,
            "evidence_kind": evidence_kind,
            "evidence_path": evidence_path,
            "proposed_topology": topology,
            "interface_ids": list(interface_ids or []),
            "legacy_duty_interface_ids": list(legacy_duty_interface_ids or []),
            "unresolved_requirements": list(unresolved or []),
        }
    )


def _build_assignments(
    inventory: dict,
    interfaces: dict,
    wj04: dict,
    receiver_audit: dict,
    wj06_text: str,
    binding: dict,
) -> list[dict]:
    duties = inventory["legacy_duties"]
    duty_ids = [row["legacy_station_id"] for row in duties]
    known_ids = set(duty_ids)
    wj06_contract = _wj06_script_contract(wj06_text)
    source_duty_markers_valid = all(
        (
            wj06_contract["wj03_duty_set_markers"],
            wj06_contract["wj04_duty_marker"],
            wj06_contract["wj05_duty_set_markers"],
        )
    )
    wj03_duty_ids = {
        duty_id
        for duty_id in duty_ids
        if duty_id.startswith(("clip_timber_header_outer_", "clip_angle_base_"))
    } if source_duty_markers_valid else set()
    wj04_duty_id = "clip_horizontal_lower_right_1" if source_duty_markers_valid else None
    wj05_duty_ids = {
        duty_id
        for duty_id in duty_ids
        if duty_id.startswith(("clip_split_header_center_", "clip_split_base_center_"))
    } if source_duty_markers_valid else set()
    expected_wj03_duty_ids = {
        *(f"clip_timber_header_outer_{side}" for side in ("left", "right")),
        *(f"clip_angle_base_{side}" for side in ("left", "right")),
    }
    expected_wj05_duty_ids = {
        *(f"clip_split_header_center_{side}" for side in ("left", "right")),
        *(f"clip_split_base_center_{side}" for side in ("left", "right")),
    }
    source_duty_sets_valid = (
        source_duty_markers_valid
        and wj03_duty_ids == expected_wj03_duty_ids
        and wj04_duty_id in known_ids
        and wj05_duty_ids == expected_wj05_duty_ids
    )
    assignments: list[dict] = []
    evidence_duty_ids: set[str] = set()

    interface_rows = {row["interface_id"]: row for row in interfaces.get("interfaces", [])}
    if len(interface_rows) != len(interfaces.get("interfaces", [])):
        raise RegistryError("Duplicate interface IDs in interfaces artifact")
    interface_owner_rows = interfaces.get("duty_owners", [])
    owner_ids = [row.get("owner_id") for row in interface_owner_rows]
    if any(not isinstance(owner_id, str) or not owner_id for owner_id in owner_ids):
        raise RegistryError("Interface owner IDs must be non-empty strings")
    if len(set(owner_ids)) != len(owner_ids):
        raise RegistryError("Duplicate owner IDs in interfaces artifact")
    owner_by_duty: dict[str, list[dict]] = {}
    for owner in interface_owner_rows:
        for duty_id in owner.get("legacy_duties", []):
            owner_by_duty.setdefault(duty_id, []).append(owner)
    unknown_interface_duties = sorted(set(owner_by_duty) - known_ids)
    if unknown_interface_duties:
        raise RegistryError(
            f"Interface owners reference unknown source duties: {unknown_interface_duties}"
        )

    for duty_id, owners in owner_by_duty.items():
        if duty_id not in known_ids:
            continue
        if len(owners) != 1:
            for owner in owners:
                _add_assignment(
                    assignments,
                    duty_id=duty_id,
                    owner_id=None,
                    evidence_kind="conflicting_interface_owner_records",
                    evidence_path="docs/wood-joints-mvp/interfaces.json",
                    owner_status="unresolved_duplicate_owner_evidence",
                    topology=None,
                    unresolved=["More than one interface owner record names this duty."],
                )
            evidence_duty_ids.add(duty_id)
            continue
        owner = owners[0]
        owner_interface_ids = owner.get("interface_ids", [])
        missing_interfaces = sorted(set(owner_interface_ids) - set(interface_rows))
        actual_duty_interfaces = sorted(
            row["interface_id"]
            for row in interface_rows.values()
            if duty_id in row.get("legacy_duties", [])
        )
        unresolved = []
        if not binding["interfaces_source_inventory_matches"]:
            unresolved.append("Interface artifact source-inventory binding is stale or absent.")
        if missing_interfaces:
            unresolved.append(f"Referenced interface rows missing: {missing_interfaces}.")
        if not actual_duty_interfaces:
            unresolved.append("No interface row directly names this legacy duty.")
        if unresolved:
            assignment_owner = None
            status = "unresolved_stale_or_inconsistent_interface_evidence"
        else:
            assignment_owner = owner["owner_id"]
            status = "proposed_layout_path_strength_incomplete"
        _add_assignment(
            assignments,
            duty_id=duty_id,
            owner_id=assignment_owner,
            evidence_kind="WJ03_interface_owner",
            evidence_path="docs/wood-joints-mvp/interfaces.json",
            owner_status=status,
            topology="WJ-03 outer-node interface path; diagnostic, not accepted",
            interface_ids=owner_interface_ids,
            legacy_duty_interface_ids=actual_duty_interfaces,
            unresolved=unresolved
            + [
                "Owner record says strength is incomplete; no duty acceptance or capacity transfers.",
                "No delivered wood or installed bolt stacks are observed by this artifact.",
            ],
        )
        evidence_duty_ids.add(duty_id)

    for duty_id in sorted(wj03_duty_ids & known_ids):
        if duty_id in evidence_duty_ids:
            continue
        _add_assignment(
            assignments,
            duty_id=duty_id,
            owner_id=None,
            evidence_kind="missing_WJ03_interface_owner_record",
            evidence_path="docs/wood-joints-mvp/interfaces.json",
            owner_status="unresolved_missing_owner_evidence",
            topology=None,
            unresolved=["WJ-06 excludes this WJ-03 duty, but no interface owner record maps it."],
        )
        evidence_duty_ids.add(duty_id)

    wj04_valid = (
        binding["wj04_source_inventory_matches"]
        and wj04.get("candidate") == CANDIDATE
        and wj04.get("status") == "diagnostic_revise"
        and wj04_duty_id in known_ids
        and wj04.get("station") == wj04_duty_id
    )
    if wj04_duty_id in known_ids:
        _add_assignment(
            assignments,
            duty_id=wj04_duty_id,
            owner_id=(f"wj04_workhorse_{wj04_duty_id}" if wj04_valid else None),
            evidence_kind="WJ04_diagnostic_probe" if wj04_valid else "stale_WJ04_probe",
            evidence_path="docs/wood-joints-mvp/wj04-probe.json",
            owner_status=("diagnostic_revise_unaccepted" if wj04_valid else "unresolved_stale_probe"),
            topology="WJ-04 revised workhorse cleat diagnostic; geometry not accepted"
            if wj04_valid
            else None,
            unresolved=(
                list(wj04.get("limits", []))
                if wj04_valid
                else ["WJ-04 probe does not bind to the current source inventory or candidate."]
            ),
        )
        evidence_duty_ids.add(wj04_duty_id)

    center_blocker_ids = [
        duty_id
        for blocker in receiver_audit.get("blocking_conditions", [])
        if blocker.get("id") == "center_structural_duties_not_implemented"
        for duty_id in blocker.get("legacy_duty_ids", [])
    ]
    unknown_center_blockers = sorted(set(center_blocker_ids) - known_ids)
    if unknown_center_blockers:
        raise RegistryError(
            f"WJ-05 blockers reference unknown source duties: {unknown_center_blockers}"
        )
    if len(center_blocker_ids) != len(set(center_blocker_ids)):
        raise RegistryError("Duplicate center-duty blocker assignments in WJ-05 audit")
    center_blockers = set(center_blocker_ids)
    wj06_center_contract_valid = (
        wj06_contract["center_owner_marker"]
        and wj06_contract["explicit_no_acceptance_marker"]
        and source_duty_sets_valid
    )
    center_ids_to_assign = sorted(wj05_duty_ids & known_ids)
    if set(center_blocker_ids) != set(center_ids_to_assign):
        for duty_id in sorted((center_blockers | set(center_ids_to_assign)) & known_ids):
            _add_assignment(
                assignments,
                duty_id=duty_id,
                owner_id=None,
                evidence_kind="conflicting_center_duty_scope",
                evidence_path="docs/wood-joints-mvp/wj05-receiver-audit.json",
                owner_status="unresolved_center_scope_mismatch",
                topology=None,
                unresolved=["WJ-05 script duties and receiver-audit blockers do not match."],
            )
            evidence_duty_ids.add(duty_id)
        center_ids_to_assign = []
    for duty_id in center_ids_to_assign:
        side = duty_id.rsplit("_", 1)[-1]
        unresolved = [
            blocker["resolution_required"]
            for blocker in receiver_audit.get("blocking_conditions", [])
            if blocker.get("id") == "center_structural_duties_not_implemented"
            and duty_id in blocker.get("legacy_duty_ids", [])
        ]
        unresolved.extend(
            [
                "Both center kicker receiver paths and inner-edge support remain unresolved.",
                "Four backer attachment bores are provisional; no complete installed bolt stacks are selected.",
            ]
        )
        if not binding["receiver_audit_source_inventory_matches"]:
            unresolved.append("WJ-05 receiver audit source-inventory binding is stale or absent.")
        _add_assignment(
            assignments,
            duty_id=duty_id,
            owner_id=f"wj05_center_node_{side}" if wj06_center_contract_valid else None,
            evidence_kind="WJ06_script_WJ05_center_dependency",
            evidence_path="scripts/wood_joint_wj06_residual_probe.py",
            owner_status=(
                "proposed_unimplemented_blocked_by_WJ05"
                if wj06_center_contract_valid
                else "unresolved_center_owner_evidence"
            ),
            topology="Integrated center node named by WJ-06; no structural interface model accepted"
            if wj06_center_contract_valid
            else None,
            unresolved=unresolved,
        )
        evidence_duty_ids.add(duty_id)

    generic_contract_valid = (
        source_duty_sets_valid
        and wj06_contract["generic_owner_marker"]
        and wj06_contract["diagnostic_topology_marker"]
        and wj06_contract["four_provisional_axis_marker"]
        and wj06_contract["explicit_no_acceptance_marker"]
        and f'CANDIDATE = "{CANDIDATE}"' in wj06_text
    )
    script_excluded_duty_ids = wj03_duty_ids | wj05_duty_ids
    if wj04_duty_id:
        script_excluded_duty_ids.add(wj04_duty_id)
    for duty_id in duty_ids:
        if source_duty_sets_valid and duty_id in script_excluded_duty_ids:
            continue
        if not generic_contract_valid and duty_id in evidence_duty_ids:
            continue
        owner_id = f"wj06_{duty_id}" if generic_contract_valid else None
        _add_assignment(
            assignments,
            duty_id=duty_id,
            owner_id=owner_id,
            evidence_kind="WJ06_residual_script_policy" if generic_contract_valid else "unresolved_owner",
            evidence_path="scripts/wood_joint_wj06_residual_probe.py",
            owner_status=(
                "proposed_unimplemented_no_generated_report"
                if generic_contract_valid
                else "unresolved_missing_owner_evidence"
            ),
            topology=(
                "One-piece solid-sawn orthogonal face-cleat diagnostic with provisional bolt axes"
                if generic_contract_valid
                else None
            ),
            unresolved=(
                [
                    "WJ-06 report is absent; no face mapping or trial result is materialized.",
                    "No replacement interface path is accepted for this duty.",
                    "Four script-declared bolt corridors per trial are provisional axes, not full stacks.",
                    "No member resistance, stiffness, complete load path, or release is established.",
                ]
                if generic_contract_valid
                else [
                    "No current source evidence safely identifies a proposed owner for this duty.",
                ]
            ),
        )

    return assignments


def build_registry() -> dict:
    inventory, inventory_bytes = _read_json(SOURCE_INVENTORY)
    interfaces, interfaces_bytes = _read_json(INTERFACES)
    wj04, wj04_bytes = _read_json(WJ04_PROBE)
    receiver_audit, receiver_bytes = _read_json(WJ05_RECEIVER_AUDIT)
    wj06_bytes = WJ06_RESIDUAL_SCRIPT.read_bytes()
    receiver_script_bytes = WJ05_RECEIVER_SCRIPT.read_bytes()
    producer_bytes = Path(__file__).read_bytes()
    optional_wj06_report = None
    optional_wj06_report_bytes = None
    if WJ06_RESIDUAL_REPORT.exists():
        optional_wj06_report, optional_wj06_report_bytes = _read_json(WJ06_RESIDUAL_REPORT)

    source_hashes = {
        _relative(SOURCE_INVENTORY): _sha256(inventory_bytes),
        _relative(INTERFACES): _sha256(interfaces_bytes),
        _relative(WJ04_PROBE): _sha256(wj04_bytes),
        _relative(WJ05_RECEIVER_AUDIT): _sha256(receiver_bytes),
        _relative(WJ05_RECEIVER_SCRIPT): _sha256(receiver_script_bytes),
        _relative(WJ06_RESIDUAL_SCRIPT): _sha256(wj06_bytes),
        _relative(Path(__file__)): _sha256(producer_bytes),
    }
    if optional_wj06_report_bytes is not None:
        source_hashes[_relative(WJ06_RESIDUAL_REPORT)] = _sha256(optional_wj06_report_bytes)

    if inventory.get("candidate") != CANDIDATE:
        raise RegistryError("Source inventory is not for the named WJ-MVP candidate")
    for label, artifact in (
        ("interfaces", interfaces),
        ("WJ-04 probe", wj04),
        ("WJ-05 receiver audit", receiver_audit),
    ):
        if artifact.get("candidate") != CANDIDATE:
            raise RegistryError(f"{label} candidate does not match source inventory")

    inventory_sha = source_hashes[_relative(SOURCE_INVENTORY)]
    interfaces_binding = interfaces.get("source_binding", {}).get("source_inventory_sha256")
    wj04_binding = wj04.get("source_inventory_sha256")
    receiver_binding = receiver_audit.get("source_fingerprints_sha256", {}).get(
        "docs/wood-joints-mvp/source-inventory.json"
    )
    binding = {
        "interfaces_source_inventory_matches": _binding_matches(
            interfaces_binding, inventory_sha
        ),
        "wj04_source_inventory_matches": _binding_matches(wj04_binding, inventory_sha),
        "receiver_audit_source_inventory_matches": _binding_matches(
            receiver_binding, inventory_sha
        ),
    }
    binding_details = {
        "source_inventory_sha256": inventory_sha,
        "interfaces_source_inventory_sha256": interfaces_binding,
        "wj04_source_inventory_sha256": wj04_binding,
        "receiver_audit_source_inventory_sha256": receiver_binding,
        "checks": binding,
        "all_consumed_artifacts_current": all(binding.values()),
    }

    duties = inventory.get("legacy_duties", [])
    expected_duty_ids = [row.get("legacy_station_id") for row in duties]
    assignments = _build_assignments(
        inventory,
        interfaces,
        wj04,
        receiver_audit,
        wj06_bytes.decode("utf-8"),
        binding,
    )
    validate_duty_assignments(expected_duty_ids, assignments)

    assignment_by_duty = {row["legacy_duty_id"]: row for row in assignments}
    legacy_axis_ids: list[str] = []
    duty_rows = []
    for source_duty in duties:
        duty_id = source_duty["legacy_station_id"]
        axes = source_duty.get("legacy_sds_axes", [])
        axis_ids = [axis.get("axis_id") for axis in axes]
        if any(not isinstance(axis_id, str) or not axis_id for axis_id in axis_ids):
            raise RegistryError(f"Duty {duty_id} has an empty or invalid legacy axis ID")
        legacy_axis_ids.extend(axis_ids)
        duty_rows.append(
            {
                "legacy_duty_id": duty_id,
                "legacy_family": source_duty.get("legacy_family"),
                "side": source_duty.get("side"),
                "legacy_host_members": source_duty.get("legacy_host_members", []),
                "legacy_sds_axis_count": len(axes),
                "legacy_sds_axis_ids": axis_ids,
                "legacy_sds_axis_identity_sha256": _inventory_axis_hash(axes),
                "axis_disposition": "source_axis_crosswalk_only_no_replacement_axis_mapping",
                **assignment_by_duty[duty_id],
                "replacement_accepted": False,
            }
        )

    fixed_screws = inventory.get("fixed_panel_kicker_screws", [])
    frame_bolts = inventory.get("starting_frame_bolts", [])
    fixed_axis_ids = [row.get("axis_id") for row in fixed_screws]
    frame_bolt_ids = [row.get("axis_id") for row in frame_bolts]
    if any(not isinstance(axis_id, str) or not axis_id for axis_id in fixed_axis_ids):
        raise RegistryError("Fixed panel/kicker axis IDs must be non-empty strings")
    if any(not isinstance(axis_id, str) or not axis_id for axis_id in frame_bolt_ids):
        raise RegistryError("Starting frame-bolt axis IDs must be non-empty strings")
    if len(set(legacy_axis_ids)) != len(legacy_axis_ids):
        raise RegistryError("Duplicate legacy SDS axis IDs in source inventory")
    if len(set(fixed_axis_ids)) != len(fixed_axis_ids):
        raise RegistryError("Duplicate fixed panel/kicker axis IDs in source inventory")
    if len(set(frame_bolt_ids)) != len(frame_bolt_ids):
        raise RegistryError("Duplicate starting frame-bolt IDs in source inventory")

    if binding["receiver_audit_source_inventory_matches"]:
        source_fixed_axes = {
            row["axis_id"]: (
                row["origin_global_xyz_mm"],
                row["axis_global_xyz"],
                row["candidate_finished_receiver_member"],
            )
            for row in fixed_screws
        }
        audited_fixed_axes = {
            row["axis_id"]: (
                row["axis_origin_global_xyz_mm"],
                row["axis_direction_global_xyz"],
                row["candidate_finished_receiver_member"],
            )
            for row in receiver_audit.get("axes", [])
        }
        if source_fixed_axes != audited_fixed_axes:
            raise RegistryError("WJ-05 audit changed fixed panel/kicker axis identities")

    if len(duties) != 24 or len(legacy_axis_ids) != 144:
        raise RegistryError(
            f"Expected 24 duties and 144 legacy SDS axes; found {len(duties)} and "
            f"{len(legacy_axis_ids)}"
        )
    if len(fixed_screws) != 66 or len(frame_bolts) != 12:
        raise RegistryError(
            "Expected 66 fixed panel/kicker axes and 12 starting frame bolts; found "
            f"{len(fixed_screws)} and {len(frame_bolts)}"
        )
    if any(len(row["legacy_sds_axis_ids"]) != 6 for row in duty_rows):
        raise RegistryError("Each legacy duty must retain exactly six source SDS axis IDs")

    owner_status_counts = Counter(row["owner_assignment_status"] for row in duty_rows)
    evidence_kind_counts = Counter(row["evidence_kind"] for row in duty_rows)
    wj06_generic_count = owner_status_counts.get("proposed_unimplemented_no_generated_report", 0)
    wj06_markers = _wj06_script_contract(wj06_bytes.decode("utf-8"))
    variants_per_duty = 9 if wj06_markers["nine_trial_variants_marker"] else None
    wj06_axis_count_declared = (
        wj06_generic_count * variants_per_duty * 4 if variants_per_duty is not None else None
    )
    wj05_bolts = receiver_audit.get("center_receiver_trial", {}).get(
        "provisional_backer_header_attachment_bolts", []
    )
    wj06_report_binding = None
    wj06_materialized_corridors = 0
    wj06_report_status = "not_materialized"
    full_stack_evidence_count = 0
    if optional_wj06_report is not None:
        # The producer itself states that candidate bolt axes are provisional and
        # that hardware stacks are not selected. Presence cannot create acceptance.
        wj06_report_binding = optional_wj06_report.get("source_binding", {}).get(
            "source_inventory_sha256"
        )
        wj06_report_current = (
            optional_wj06_report.get("candidate") == CANDIDATE
            and wj06_report_binding == inventory_sha
        )
        for duty_report in optional_wj06_report.get("duties", []):
            for variant in duty_report.get("trial_variants", []):
                wj06_materialized_corridors += len(
                    variant.get("mapping", {}).get("candidate_through_bolt_axes", [])
                )
        wj06_report_status = (
            "present_diagnostic_only_unaccepted"
            if wj06_report_current
            else "present_stale_or_candidate_mismatch"
        )
        if not wj06_report_current:
            wj06_materialized_corridors = 0

    missing_owner_duties = [
        row["legacy_duty_id"] for row in duty_rows if row["proposed_owner_id"] is None
    ]
    unresolved_duty_ids = [
        row["legacy_duty_id"] for row in duty_rows if not row["replacement_accepted"]
    ]
    return {
        "schema": SCHEMA,
        "candidate": CANDIDATE,
        "status": "accounting_complete_replacements_unaccepted",
        "claim": (
            "Source-bound duty crosswalk only. Assignment records do not qualify a joint, "
            "complete a load path, or accept a replacement."
        ),
        "producer": {
            "command": "python3 -m scripts.wood_joint_duty_registry --write",
            "script_sha256": source_hashes[_relative(Path(__file__))],
        },
        "source_snapshot_sha256": source_hashes,
        "source_binding": binding_details,
        "counts": {
            "legacy_former_angle_duties": len(duties),
            "legacy_removed_sds_axes": len(legacy_axis_ids),
            "legacy_axes_mapped_to_duty_rows": len(legacy_axis_ids),
            "unique_duty_assignments": len(duty_rows),
            "source_inventory_replacement_owner_fields_unassigned": sum(
                row.get("replacement_owner") is None for row in duties
            ),
            "duties_with_WJ03_interface_owner_evidence": evidence_kind_counts.get(
                "WJ03_interface_owner", 0
            ),
            "duties_without_materialized_interface_records": sum(
                not row["interface_ids"] for row in duty_rows
            ),
            "missing_proposed_owner_id_count": len(missing_owner_duties),
            "unresolved_or_unaccepted_duty_count": len(unresolved_duty_ids),
            "accepted_replacement_duty_count": 0,
            "fixed_panel_kicker_hillman_axes_retained": len(fixed_screws),
            "starting_frame_bolt_obligations_retained": len(frame_bolts),
        },
        "duties": duty_rows,
        "retained_obligations": {
            "fixed_panel_kicker_screws": {
                "count": len(fixed_screws),
                "policy": "66 purchased Hillman 42605 panel/kicker screws retained",
                "axis_ids": fixed_axis_ids,
                "axis_rows_sha256": _inventory_axis_hash(fixed_screws),
                "axes_moved_per_receiver_audit": (
                    receiver_audit.get("fixed_axis_identity", {}).get("axes_moved")
                    if binding["receiver_audit_source_inventory_matches"]
                    else None
                ),
                "physical_observation": None,
            },
            "starting_frame_bolts": {
                "count": len(frame_bolts),
                "axis_ids": frame_bolt_ids,
                "axis_rows_sha256": _inventory_axis_hash(frame_bolts),
                "candidate_recheck_required": True,
            },
        },
        "provisional_axes_and_hardware": {
            "wj06_residual_probe": {
                "script_contract_markers": wj06_markers,
                "report_status": wj06_report_status,
                "report_source_inventory_sha256": wj06_report_binding,
                "generic_duty_count": wj06_generic_count,
                "declared_variants_per_generic_duty": variants_per_duty,
                "declared_provisional_corridors_per_trial": 4,
                "potential_corridor_count_if_all_declared_trials_run": wj06_axis_count_declared,
                "materialized_corridor_count": wj06_materialized_corridors,
                "complete_installed_stack_count": 0,
                "interpretation": (
                    "Candidate corridors remain provisional and are not selected bolt lengths "
                    "or full installed stacks."
                ),
            },
            "wj05_center_backer_attachment": {
                "provisional_axis_count": len(wj05_bolts)
                if binding["receiver_audit_source_inventory_matches"]
                else 0,
                "reported_axis_count": len(wj05_bolts),
                "source_inventory_binding_matches": binding[
                    "receiver_audit_source_inventory_matches"
                ],
                "axis_ids": [row.get("bolt_id") for row in wj05_bolts],
                "complete_installed_stack_count": 0,
                "physical_hardware_observed": (
                    True
                    if wj05_bolts
                    and all(row.get("physical_hardware_observed") is True for row in wj05_bolts)
                    else False
                    if wj05_bolts
                    and all(row.get("physical_hardware_observed") is False for row in wj05_bolts)
                    else None
                ),
                "status": "provisional_diagnostic_geometry_unaccepted",
            },
            "replacement_complete_stack_evidence_count": full_stack_evidence_count,
            "replacement_complete_stack_basis": (
                "No consumed artifact establishes a selected, delivered, complete installed "
                "replacement stack. WJ-03 has bolt-group IDs, WJ-04 remains diagnostic, WJ-05 "
                "attachment hardware is unselected, and WJ-06 axes are provisional."
            ),
        },
        "unresolved_owner_duty_ids": missing_owner_duties,
        "unresolved_or_unaccepted_duty_ids": unresolved_duty_ids,
        "release_flags": {
            "layout_accepted": False,
            "hardware_selected": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "climbing_released": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write registry JSON artifact")
    args = parser.parse_args()
    report = build_registry()
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT_JSON.write_text(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
