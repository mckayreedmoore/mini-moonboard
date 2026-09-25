"""Pure-JSON classifier for frozen WJ24 tool-operation probe output.

The probe retains 36 nominal frame-bolt tool/withdrawal envelopes in its raw
obstacle map. Those shapes describe possible operations on retained bolts, not
installed material. This postprocessor preserves every raw hit, partitions
those temporary-envelope overlaps from other retained-geometry-envelope hits,
and adds diagnostic-only flags. It never re-runs CAD or upgrades access,
removal, installation, or acceptance.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROBE_SCHEMA = "wood_joint_wj24_tool_operation_probe/v1"
CLASSIFIER_SCHEMA = "wood_joint_wj24_tool_operation_hit_classification/v1"
LAYOUT_ID = "wj24-twenty-four-duty-integrated-static-v1"
TRIAL_ID = "wj24-wj18-plus-top-center-bottom-pairs-v1"
TEMPORAL_FAMILY = "retained_12_frame_bolt_tools_withdrawals"
TEMPORAL_PREFIX = f"protected/{TEMPORAL_FAMILY}/"
RETAINED_CATEGORY = "retained_geometry_envelope_hits"
TEMPORAL_CATEGORY = "temporal_operation_envelope_overlaps"
KNOWN_PROTECTED_FAMILIES = frozenset(
    {
        "fixed_66_hillman_axes_63p5mm",
        "retained_12_frame_bolt_components",
        TEMPORAL_FAMILY,
        "tnuts",
        "hold_hole_and_provisional_projection",
        "lights",
        "wires",
        "retained_legacy_clips",
        "retained_legacy_sds_axes",
    }
)


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _is_collision_report(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and isinstance(value.get("external_envelope_hits_mm3"), Mapping)
        and "external_envelope_clear" in value
    )


def _hit_count(value: Mapping[str, Any]) -> int:
    count = 0
    for obstacle_hits in value.values():
        if not isinstance(obstacle_hits, Mapping):
            raise TypeError("collision hit rows must be obstacle-to-volume mappings")
        count += len(obstacle_hits)
    return count


def _protected_family(obstacle_id: str) -> str | None:
    parts = obstacle_id.split("/")
    if len(parts) >= 3 and parts[0] == "protected":
        return parts[1]
    return None


def _classify_collision_report(report: dict[str, Any]) -> dict[str, Any]:
    if "hit_classification" in report:
        raise ValueError("raw collision report already contains hit_classification")
    raw_hits = report["external_envelope_hits_mm3"]
    if not isinstance(raw_hits, Mapping):
        raise TypeError("external_envelope_hits_mm3 must be a mapping")

    retained: dict[str, dict[str, Any]] = {}
    temporal: dict[str, dict[str, Any]] = {}
    unknown_families: set[str] = set()
    for candidate_id, obstacle_hits in raw_hits.items():
        if not isinstance(candidate_id, str) or not isinstance(obstacle_hits, Mapping):
            raise TypeError(
                "collision candidate rows must map IDs to obstacle mappings"
            )
        for obstacle_id in obstacle_hits:
            if not isinstance(obstacle_id, str):
                raise TypeError("collision obstacle IDs must be strings")
            family = _protected_family(obstacle_id)
            if family is not None and family not in KNOWN_PROTECTED_FAMILIES:
                # Future protected families stay in the retained-geometry bucket
                # until a source-backed rule says they are temporal operations.
                unknown_families.add(family)
            target = (
                temporal
                if obstacle_id.startswith(TEMPORAL_PREFIX)
                or obstacle_id == TEMPORAL_PREFIX.rstrip("/")
                else retained
            )
            target.setdefault(candidate_id, {})[obstacle_id] = obstacle_hits[
                obstacle_id
            ]

    raw_count = _hit_count(raw_hits)
    retained_count = _hit_count(retained)
    temporal_count = _hit_count(temporal)
    dropped_count = raw_count - retained_count - temporal_count
    if dropped_count != 0:
        raise RuntimeError("hit classification failed to preserve every raw collision")

    classification = {
        "schema": CLASSIFIER_SCHEMA,
        "raw_external_envelope_hits_map_sha256": _canonical_sha256(raw_hits),
        RETAINED_CATEGORY: retained,
        TEMPORAL_CATEGORY: temporal,
        "raw_hit_count": raw_count,
        "retained_geometry_envelope_hit_count": retained_count,
        "temporal_operation_envelope_overlap_count": temporal_count,
        "dropped_hit_count": dropped_count,
        "unclassified_hit_count": 0,
        "unknown_protected_families_retained": sorted(unknown_families),
        "raw_external_envelope_clear": report["external_envelope_clear"],
        "retained_geometry_envelope_clear": not retained,
        "temporal_operation_envelope_overlap_present": bool(temporal),
        "raw_clear_includes_temporal_operation_proxies": True,
        "physical_access_established": False,
        "operation_route_established": False,
    }
    report["hit_classification"] = classification
    return classification


def _walk_collision_reports(value: Any):
    if _is_collision_report(value):
        yield value
        return
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_collision_reports(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_collision_reports(child)


def _operation_summary(
    operation: Mapping[str, Any], classifications: list[Mapping[str, Any]]
) -> dict[str, Any]:
    if not classifications:
        return {
            "status": (
                "scope_not_modeled"
                if operation.get("status") == "scope_not_modeled"
                else "no_collision_report"
            ),
            "collision_report_count": 0,
            "retained_geometry_envelope_clear": None,
            "retained_geometry_envelope_hit_count": 0,
            "temporal_operation_envelope_overlap_present": False,
            "temporal_operation_envelope_overlap_count": 0,
            "dropped_hit_count": 0,
            "physical_access_or_removal_established": False,
        }
    return {
        "status": "diagnostic_classified",
        "collision_report_count": len(classifications),
        "retained_geometry_envelope_clear": all(
            row["retained_geometry_envelope_clear"] for row in classifications
        ),
        "retained_geometry_envelope_hit_count": sum(
            int(row["retained_geometry_envelope_hit_count"]) for row in classifications
        ),
        "temporal_operation_envelope_overlap_present": any(
            row["temporal_operation_envelope_overlap_present"]
            for row in classifications
        ),
        "temporal_operation_envelope_overlap_count": sum(
            int(row["temporal_operation_envelope_overlap_count"])
            for row in classifications
        ),
        "dropped_hit_count": sum(
            int(row["dropped_hit_count"]) for row in classifications
        ),
        "raw_external_envelope_clear_for_all_reports": all(
            row["raw_external_envelope_clear"] for row in classifications
        ),
        "physical_access_or_removal_established": False,
    }


def _effective_method_summary(axes: list[Mapping[str, Any]]) -> dict[str, Any]:
    withdrawal_methods: dict[str, int] = {}
    withdrawal_statuses: dict[str, int] = {}
    shaft_methods: dict[str, int] = {}
    head_washer_methods: dict[str, int] = {}
    terminal_margins: dict[str, int] = {}
    for axis in axes:
        operations = axis.get("operations", {})
        if not isinstance(operations, Mapping):
            continue
        withdrawal = operations.get("shaft_withdrawal", {})
        if not isinstance(withdrawal, Mapping):
            continue
        method = withdrawal.get("method")
        if isinstance(method, str):
            withdrawal_methods[method] = withdrawal_methods.get(method, 0) + 1
        status = withdrawal.get("status")
        if isinstance(status, str):
            withdrawal_statuses[status] = withdrawal_statuses.get(status, 0) + 1
        shaft_method = withdrawal.get("shaft_sweep_method")
        if isinstance(shaft_method, str):
            shaft_methods[shaft_method] = shaft_methods.get(shaft_method, 0) + 1
        head_washer_method = withdrawal.get("head_and_washer_sweep_method")
        if isinstance(head_washer_method, str):
            head_washer_methods[head_washer_method] = (
                head_washer_methods.get(head_washer_method, 0) + 1
            )
        margin = withdrawal.get("terminal_clearance_margin_mm")
        if isinstance(margin, (int, float)) and not isinstance(margin, bool):
            key = str(margin)
            terminal_margins[key] = terminal_margins.get(key, 0) + 1
    return {
        "withdrawal_method_counts": dict(sorted(withdrawal_methods.items())),
        "withdrawal_status_counts": dict(sorted(withdrawal_statuses.items())),
        "shaft_sweep_method_counts": dict(sorted(shaft_methods.items())),
        "head_and_washer_sweep_method_counts": dict(
            sorted(head_washer_methods.items())
        ),
        "terminal_clearance_margin_mm_counts": dict(sorted(terminal_margins.items())),
        "exact_coaxial_cylinder_shaft_sweep_count": shaft_methods.get(
            "exact_coaxial_cylinder_translation_sweep", 0
        ),
        "conservative_oriented_box_head_and_washer_sweep_count": head_washer_methods.get(
            "separate conservative oriented-box translation enclosures", 0
        ),
        "per_axis_method_fields_are_authoritative": True,
    }


def classify_wj24_tool_operation_report(
    raw_report: Mapping[str, Any], *, raw_report_sha256: str | None = None
) -> dict[str, Any]:
    """Return a copy with diagnostic-only hit classifications appended.

    The original raw hit maps, raw clearance booleans, artifact hashes, and
    provenance are retained byte-for-value in the returned JSON tree.
    """
    if not isinstance(raw_report, Mapping):
        raise TypeError("WJ24 raw tool-operation report must be a mapping")
    if raw_report.get("schema") != PROBE_SCHEMA:
        raise ValueError(f"raw report schema must be {PROBE_SCHEMA}")
    if (
        raw_report.get("layout_id") != LAYOUT_ID
        or raw_report.get("trial_id") != TRIAL_ID
    ):
        raise ValueError("raw report must identify the frozen WJ24 layout and trial")
    axes = raw_report.get("axes")
    if not isinstance(axes, list) or any(not isinstance(row, Mapping) for row in axes):
        raise TypeError("raw report axes must be a list of axis mappings")
    if "classification_inventory" in raw_report:
        raise ValueError("raw report already contains classification_inventory")

    result = copy.deepcopy(dict(raw_report))
    raw_sha = raw_report_sha256 or _canonical_sha256(raw_report)
    if len(raw_sha) != 64 or any(
        character not in "0123456789abcdef" for character in raw_sha
    ):
        raise ValueError("raw_report_sha256 must be a lowercase SHA-256 digest")

    all_classifications: list[Mapping[str, Any]] = []
    unknown_families: set[str] = set()
    for axis in result["axes"]:
        axis_id = axis.get("axis_id")
        operations = axis.get("operations")
        if not isinstance(axis_id, str) or not isinstance(operations, Mapping):
            raise TypeError("each raw axis must identify an operations mapping")
        if not isinstance(operations, dict):
            raise TypeError("raw report operations must be mutable JSON objects")
        for operation_name, operation in operations.items():
            if not isinstance(operation_name, str) or not isinstance(operation, dict):
                raise TypeError("operation rows must be named JSON objects")
            if "hit_classification_summary" in operation:
                raise ValueError(
                    "operation already contains hit_classification_summary"
                )
            found = []
            for collision_report in _walk_collision_reports(operation):
                classification = _classify_collision_report(collision_report)
                found.append(classification)
                all_classifications.append(classification)
                unknown_families.update(
                    classification["unknown_protected_families_retained"]
                )
            operation["hit_classification_summary"] = _operation_summary(
                operation, found
            )

    raw_hit_count = sum(int(row["raw_hit_count"]) for row in all_classifications)
    retained_hit_count = sum(
        int(row["retained_geometry_envelope_hit_count"]) for row in all_classifications
    )
    temporal_hit_count = sum(
        int(row["temporal_operation_envelope_overlap_count"])
        for row in all_classifications
    )
    dropped_hit_count = sum(
        int(row["dropped_hit_count"]) for row in all_classifications
    )
    result["classification_inventory"] = {
        "schema": CLASSIFIER_SCHEMA,
        "classifier": "pure JSON postprocessor; no CAD geometry recomputed",
        "raw_report_sha256": raw_sha,
        "raw_collision_report_count": len(all_classifications),
        "raw_hit_count": raw_hit_count,
        "retained_geometry_envelope_hit_count": retained_hit_count,
        "temporal_operation_envelope_overlap_count": temporal_hit_count,
        "dropped_hit_count": dropped_hit_count,
        "unclassified_hit_count": 0,
        "raw_collision_hit_maps_preserved": True,
        "original_raw_clearance_flags_preserved": True,
        "temporal_operation_family": TEMPORAL_FAMILY,
        "temporal_operation_obstacle_prefix": TEMPORAL_PREFIX,
        "retained_geometry_category": RETAINED_CATEGORY,
        "unknown_protected_family_policy": (
            "retain conservatively in retained_geometry_envelope_hits until a "
            "source-backed temporal rule is added"
        ),
        "unknown_protected_families_retained": sorted(unknown_families),
        "axis_rows_present": len(result["axes"]),
        "expected_axis_rows": 104,
        "all_104_axis_rows_present": len(result["axes"]) == 104,
        "classification_changes_acceptance_or_access": False,
        "physical_access_established": False,
        "operation_route_established": False,
    }
    result["classification_provenance"] = {
        "raw_report_sha256": raw_sha,
        "classifier_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    raw_method_contract = raw_report.get("method_contract", {})
    raw_shaft_method_text = (
        raw_method_contract.get("shaft_withdrawal")
        if isinstance(raw_method_contract, Mapping)
        else None
    )
    result["method_refinement"] = {
        "schema": CLASSIFIER_SCHEMA,
        "raw_method_contract_preserved_verbatim": True,
        "raw_top_level_shaft_method_text": raw_shaft_method_text,
        "per_axis_method_summary": _effective_method_summary(result["axes"]),
        "interpretation": (
            "The preserved top-level raw summary describes all moving roles "
            "with a conservative oriented bounding sweep. Per-axis operation "
            "fields summarize the executed checks: separate conservative "
            "oriented-box enclosures for head/head-washer, and an exact "
            "coaxial-cylinder shaft sweep when primitive reconstruction "
            "validates. These method details remain geometric diagnostics and "
            "do not establish physical access or removal."
        ),
        "classification_changes_acceptance_or_access": False,
    }
    return result


def classify_file(input_path: Path, output_path: Path) -> dict[str, Any]:
    raw_bytes = input_path.read_bytes()
    raw_report = json.loads(raw_bytes)
    if not isinstance(raw_report, Mapping):
        raise TypeError("WJ24 raw tool-operation JSON must contain an object")
    classified = classify_wj24_tool_operation_report(
        raw_report, raw_report_sha256=hashlib.sha256(raw_bytes).hexdigest()
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(classified, indent=2) + "\n")
    return classified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, required=True, help="Frozen raw probe JSON"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Classified report JSON"
    )
    args = parser.parse_args()
    report = classify_file(args.input, args.output)
    summary = report["classification_inventory"]
    print(
        json.dumps(
            {
                "output": str(args.output),
                "raw_report_sha256": summary["raw_report_sha256"],
                "raw_collision_report_count": summary["raw_collision_report_count"],
                "raw_hit_count": summary["raw_hit_count"],
                "retained_geometry_envelope_hit_count": summary[
                    "retained_geometry_envelope_hit_count"
                ],
                "temporal_operation_envelope_overlap_count": summary[
                    "temporal_operation_envelope_overlap_count"
                ],
                "dropped_hit_count": summary["dropped_hit_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
