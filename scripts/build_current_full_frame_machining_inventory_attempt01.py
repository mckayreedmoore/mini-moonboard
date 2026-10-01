"""Reconcile current 50-member geometry against the available cut inventory.

This is a static provenance/gap report. It does not derive cutter dimensions,
replay CAD, generate shop instructions, or change any source geometry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    / "current-full-frame-machining-inventory-attempt01/inventory.json"
)
BASE = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
)
INPUTS = {
    "current_manifest": BASE
    + "current-full-frame-input-manifest-attempt04/"
    + "current-full-frame-input-manifest.json",
    "member_solids_bundle": BASE
    + "current-full-frame-member-solids-attempt01/bundle/"
    + "current-full-frame-member-solids.json",
    "prior_timber_cut_inventory": BASE
    + "current-timber-cut-inventory-attempt01/inventory.json",
    "prior_timber_cut_inventory_readme": BASE
    + "current-timber-cut-inventory-attempt01/README.md",
}
EXPECTED_INPUT_SHA256 = {
    INPUTS["current_manifest"]: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    INPUTS["member_solids_bundle"]: "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    INPUTS["prior_timber_cut_inventory"]: "bacc2c669923c34164e12dc227d414a96dcac1d0861d43fa785f0d3712a25af4",
    INPUTS["prior_timber_cut_inventory_readme"]: "75c146d185233647b11a5d4d6523bb35db45cb6484f6fbc225ce6bd0a3734af5",
}
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    )


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


def require_unique(values: list[str], label: str) -> None:
    if len(set(values)) != len(values):
        raise ValueError(f"Duplicate {label} identifier")


def verify_input_pins() -> dict[str, dict[str, Any]]:
    pins: dict[str, dict[str, Any]] = {}
    for relative, expected in EXPECTED_INPUT_SHA256.items():
        raw = (ROOT / relative).read_bytes()
        actual = sha256(raw)
        if actual != expected:
            raise ValueError(
                f"Pinned source drift: {relative}: expected {expected}, got {actual}"
            )
        pins[relative] = {
            "sha256": actual,
            "size_bytes": len(raw),
        }
    return pins


def build() -> dict[str, Any]:
    pins = verify_input_pins()
    manifest = read_json(INPUTS["current_manifest"])
    solids = read_json(INPUTS["member_solids_bundle"])
    prior = read_json(INPUTS["prior_timber_cut_inventory"])

    if manifest.get("geometry_revision_id") != REVISION:
        raise ValueError("Current manifest has a different reviewed geometry revision")
    if manifest.get("schema") != "wood_joint_current_full_frame_input_manifest/v3":
        raise ValueError("Expected full-frame input manifest schema v3")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04":
        raise ValueError("Expected current full-frame input manifest attempt04")
    if solids.get("geometry_revision_id") != REVISION:
        raise ValueError("STEP bundle has a different geometry revision")
    if prior.get("geometry_revision_id") != REVISION:
        raise ValueError("Prior cut inventory has a different geometry revision")

    manifest_members = index_unique(
        manifest["physical_members"], "member_id", "manifest member"
    )
    bindings = index_unique(
        manifest["finished_member_step_bindings"], "member_id", "STEP binding"
    )
    solid_members = index_unique(solids["members"], "member_id", "STEP bundle member")
    prior_members = index_unique(prior["members"], "member_id", "prior cut-inventory member")
    expected_ids = set(manifest_members)
    if len(expected_ids) != 50 or set(bindings) != expected_ids:
        raise ValueError("Current manifest must bind exactly 50 unique member STEP files")
    if set(solid_members) != expected_ids:
        raise ValueError("STEP bundle membership differs from the current manifest")
    if set(prior_members) - expected_ids:
        raise ValueError("Prior timber inventory contains members absent from current geometry")
    if len(prior_members) != 44:
        raise ValueError(f"Expected 44 prior wood-member records, got {len(prior_members)}")

    kind_counts: dict[str, int] = {}
    for row in solid_members.values():
        kind_counts[row["member_kind"]] = kind_counts.get(row["member_kind"], 0) + 1
    if kind_counts != {"timber": 20, "candidate_block": 24, "plywood_panel": 6}:
        raise ValueError(f"Unexpected full-frame member kinds: {kind_counts}")
    manifest_kind_counts: dict[str, int] = {}
    for row in manifest_members.values():
        manifest_kind_counts[row["member_kind"]] = (
            manifest_kind_counts.get(row["member_kind"], 0) + 1
        )
    if manifest_kind_counts != {"timber": 44, "panel": 6}:
        raise ValueError(f"Unexpected manifest member kinds: {manifest_kind_counts}")
    prior_kind_counts: dict[str, int] = {}
    for row in prior_members.values():
        prior_kind_counts[row["member_kind"]] = (
            prior_kind_counts.get(row["member_kind"], 0) + 1
        )
    if prior_kind_counts != {"timber": 20, "candidate_block": 24}:
        raise ValueError(f"Unexpected prior inventory member kinds: {prior_kind_counts}")

    candidate_axes = manifest.get("candidate_bolt_axes", [])
    retained_axes = manifest.get("retained_frame_bolt_axes", [])
    screw_axes = manifest.get("panel_kicker_screw_axes", [])
    if (len(candidate_axes), len(retained_axes), len(screw_axes)) != (92, 12, 66):
        raise ValueError("Current axis counts must remain 92 candidate, 12 retained, 66 screws")
    require_unique([row["axis_id"] for row in candidate_axes], "candidate-bolt axis")
    require_unique([row["axis_id"] for row in retained_axes], "retained-frame-bolt axis")
    require_unique([row["axis_id"] for row in screw_axes], "panel/kicker screw axis")

    axis_members: dict[str, dict[str, list[str]]] = {
        member_id: {"candidate_bolt": [], "retained_frame_bolt": [], "panel_kicker_screw": []}
        for member_id in expected_ids
    }
    candidate_rows = []
    for row in candidate_axes:
        receivers = row["receiver_member_ids"]
        if not receivers or not set(receivers) <= expected_ids:
            raise ValueError(f"Unknown candidate-axis receiver: {row.get('axis_id')}")
        for member_id in receivers:
            axis_members[member_id]["candidate_bolt"].append(row["axis_id"])
        candidate_rows.append(
            {
                "axis_id": row["axis_id"],
                "receiver_member_ids": receivers,
                "modeled_shaft_diameter_mm": row["geometry"][
                    "modeled_shaft_diameter_mm"
                ],
                "clearance_bore_diameter_mm": None,
                "cut_geometry_status": (
                    "No source-authoritative timber bore diameter or operation is "
                    "bound here; modeled shaft occupancy is not cutter geometry."
                ),
            }
        )

    retained_rows = []
    for row in retained_axes:
        members = row["members_as_recorded"]
        if not members or not set(members) <= expected_ids:
            raise ValueError(f"Unknown retained-bolt receiver: {row.get('axis_id')}")
        for member_id in members:
            axis_members[member_id]["retained_frame_bolt"].append(row["axis_id"])
        retained_rows.append(
            {
                "axis_id": row["axis_id"],
                "receiver_member_ids_as_recorded": members,
                "source_occupied_diameter_mm": row["source_occupied_diameter_mm"],
                "clearance_bore_diameter_mm": None,
                "cut_geometry_status": (
                    "Retained bolt occupancy does not specify a timber bore or "
                    "machining operation."
                ),
            }
        )

    screw_rows = []
    for row in screw_axes:
        members = [row["panel_member"], row["receiver_member"]]
        if not set(members) <= expected_ids:
            raise ValueError(f"Unknown screw-axis member: {row.get('axis_id')}")
        for member_id in set(members):
            axis_members[member_id]["panel_kicker_screw"].append(row["axis_id"])
        screw_rows.append(
            {
                "axis_id": row["axis_id"],
                "panel_member": row["panel_member"],
                "receiver_member": row["receiver_member"],
                "axis_global_xyz": row["axis_global_xyz"],
                "hardware_status": row["hardware_status"],
                "purchased_policy": row["purchased_policy"],
                "preparatory_hole_geometry_status": (
                    "Axis/member association only; no operation dimensions or "
                    "cut ticket are inferred here."
                ),
            }
        )

    members = []
    for member_id in sorted(expected_ids):
        physical = manifest_members[member_id]
        binding = bindings[member_id]
        solid = solid_members[member_id]
        step_path = binding["path"]
        step_hash = sha256((ROOT / step_path).read_bytes())
        if step_hash != binding["file_sha256"]:
            raise ValueError(f"Finished STEP hash mismatch for {member_id}")
        bundle_step_path = (
            (ROOT / INPUTS["member_solids_bundle"]).parent.parent
            / solid["step_file"]
        ).resolve()
        if (
            bundle_step_path != (ROOT / step_path).resolve()
            or solid["step_sha256"] != binding["file_sha256"]
            or solid["source_shape_fingerprint_sha256"]
            != physical["current_finished_step_binding"][
                "source_shape_fingerprint_sha256"
            ]
        ):
            raise ValueError(f"Manifest/STEP bundle identity mismatch for {member_id}")
        old_row = prior_members.get(member_id)
        if old_row is not None:
            if (
                old_row["step"]["path"] != step_path
                or old_row["step"]["sha256"] != binding["file_sha256"]
                or old_row["source_shape_fingerprint_sha256"]
                != solid["source_shape_fingerprint_sha256"]
            ):
                raise ValueError(f"Prior cut-inventory crosswalk mismatch for {member_id}")
            cut_status = old_row["cut_profile_decomposition_status"]
            named_features = old_row["named_profile_features"]
            net_section = old_row["finished_section"]["net_section_computed"]
            coverage = "prior_44_member_cut_inventory_row"
        else:
            cut_status = (
                "No row in the prior 44-member timber/block cut inventory; "
                "operation decomposition is absent from this evidence."
            )
            named_features = []
            net_section = False
            coverage = "not_covered_by_prior_cut_inventory"
        members.append(
            {
                "member_id": member_id,
                "member_kind": solid["member_kind"],
                "manifest_member_kind": physical["member_kind"],
                "finished_step_path": step_path,
                "finished_step_sha256": binding["file_sha256"],
                "source_shape_fingerprint_sha256": solid[
                    "source_shape_fingerprint_sha256"
                ],
                "prior_cut_inventory_coverage": coverage,
                "cut_profile_decomposition_status": cut_status,
                "named_profile_features_from_prior_inventory": named_features,
                "net_section_computed_in_prior_inventory": net_section,
                "associated_axes": axis_members[member_id],
            }
        )

    uncovered = [
        row["member_id"]
        for row in members
        if row["prior_cut_inventory_coverage"]
        == "not_covered_by_prior_cut_inventory"
    ]
    if len(uncovered) != 6 or any(
        solid_members[member_id]["member_kind"] != "plywood_panel"
        for member_id in uncovered
    ):
        raise ValueError("Expected exactly the six plywood panels to be uncovered")

    record: dict[str, Any] = {
        "schema": "wood_joint_current_full_frame_machining_gap_inventory/v1",
        "attempt_id": "current-full-frame-machining-inventory-attempt01",
        "candidate": manifest["candidate"],
        "geometry_revision_id": REVISION,
        "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "selected_candidate_preserved": manifest["selected_candidate_authority_preserved"],
        "status": "identity_reconciled_operation_schedule_incomplete",
        "criterion_effect": {
            "all_machining_represented": False,
            "disposition": "pending",
            "reason": (
                "This packet reconciles member identities and enumerates known "
                "coverage gaps. It does not provide a complete source-authoritative "
                "operation schedule or cut ticket."
            ),
        },
        "source_pins": pins,
        "source_content_digests": {
            "current_manifest_declared_sha256": manifest["manifest_sha256"],
            "member_solids_bundle_declared_sha256": solids["artifact_sha256"],
            "member_step_bundle_sha256": solids["member_bundle_sha256"],
            "prior_cut_inventory_record_sha256": prior["record_sha256"],
        },
        "counts": {
            "current_members": len(members),
            "current_timbers": kind_counts["timber"],
            "current_candidate_blocks": kind_counts["candidate_block"],
            "current_plywood_panels": kind_counts["plywood_panel"],
            "members_reconciled_to_prior_cut_inventory": len(prior_members),
            "members_without_prior_cut_inventory_row": len(uncovered),
            "candidate_bolt_axes": len(candidate_rows),
            "retained_frame_bolt_axes": len(retained_rows),
            "panel_kicker_screw_axes": len(screw_rows),
        },
        "limits": [
            "A finished STEP body identifies nominal geometry; it is not by itself a cut-operation schedule or a source-authoritative shop instruction.",
            "Modeled shaft/occupied diameters and axis receiver associations are analysis geometry, not timber clearance-bore or preparatory-hole dimensions.",
            "No net-section slices, machining tolerances, setups, tool selections, or approved cut tickets are produced.",
            "No physical stock, panels, axes, holes, or installation were inspected; no cutting, drilling, fabrication, structural, or climbing release is made.",
        ],
        "gap_register": [
            {
                "gap_id": "MACH-GAP-01",
                "scope": "six current plywood panel members",
                "finding": "No member rows for plywood panels exist in the prior cut inventory.",
                "required_evidence": "Source-bound panel blank, edge, bevel, recess, insert, and other applicable operation schedule for each exact current panel body; omit non-applicable operations explicitly.",
                "status": "open",
            },
            {
                "gap_id": "MACH-GAP-02",
                "scope": "44 timber and candidate-block members",
                "finding": "The prior inventory contains named features and finished STEP bindings, but expressly lacks a complete per-member operation decomposition.",
                "required_evidence": "Source-linked operation decomposition for every member, including dimensions and datum/tolerance basis where available; retain unknown values as unresolved.",
                "status": "open",
            },
            {
                "gap_id": "MACH-GAP-03",
                "scope": "92 candidate bolt axes and 12 retained frame-bolt axes",
                "finding": "Receiver memberships and modeled occupancy are mapped, but no authoritative timber clearance-bore diameter or operation schedule is bound.",
                "required_evidence": "Owner/product/source-backed drilling basis for each applicable receiver, with member, datum, direction, diameter, depth, and tolerance only where specified.",
                "status": "open",
            },
            {
                "gap_id": "MACH-GAP-04",
                "scope": "66 panel/kicker screw axes",
                "finding": "The current axis/member and retained Hillman policy are mapped; this packet supplies no actual preparatory-hole or countersink operation dimensions.",
                "required_evidence": "Current candidate shop instruction tied to the purchased screw policy and current receiver, distinguishing required pilot/countersink operations from axis occupancy.",
                "status": "open",
            },
            {
                "gap_id": "MACH-GAP-05",
                "scope": "critical timber sections and all shop operations",
                "finding": "No operation-plane net sections, complete cut tolerances, setup sequence, or cut-ticket schedule are provided.",
                "required_evidence": "Reviewed operation/section schedule and any required local section evidence, source-bound to the same frozen geometry revision.",
                "status": "open",
            },
        ],
        "members": members,
        "axis_maps": {
            "candidate_bolt_axes": candidate_rows,
            "retained_frame_bolt_axes": retained_rows,
            "panel_kicker_screw_axes": screw_rows,
        },
        "native_solve_executed": False,
        "cutting_or_drilling_released": False,
        "candidate_accepted": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
    }
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
            raise SystemExit("Inventory is stale or differs from pinned source records")
    print(
        f"{'WROTE' if args.write else 'PASS'} {OUT.relative_to(ROOT)} "
        f"sha256={expected['record_sha256']} members={len(expected['members'])} "
        f"axes=92+12+66; machining_complete=false"
    )


if __name__ == "__main__":
    main()
