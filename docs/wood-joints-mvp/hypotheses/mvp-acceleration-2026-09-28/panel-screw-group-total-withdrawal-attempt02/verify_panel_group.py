#!/usr/bin/env python3
"""Verify gravity-inclusive normal-force lower bounds for panel screw groups."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
HERE = Path(__file__).resolve().parent
LOADS_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json"
)
RECEIVER_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json"
)
MODEL_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
)
WRENCHES_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/body-external-wrenches.csv"
)
CONTACT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
)
PRODUCER_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-group-total-withdrawal-attempt02/verify_panel_group.py"
)
PINS = {
    str(LOADS_REL): "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    str(RECEIVER_REL): "851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991",
    str(MODEL_REL): "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    str(WRENCHES_REL): "6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f",
    str(CONTACT_REL): "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
}
VECTOR_TOL = 1e-10
FORCE_TOL_N = 1e-8
CONTACT_NORMAL_TOL = 1e-8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dot(a: list[float], b: list[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def max_abs_difference(a: list[float], b: list[float]) -> float:
    return max(abs(float(x) - float(y)) for x, y in zip(a, b, strict=True))


def verify_sources() -> dict[str, str]:
    observed: dict[str, str] = {}
    for rel, expected in PINS.items():
        actual = sha256(ROOT / rel)
        if actual != expected:
            raise ValueError(f"source hash changed for {rel}: {actual} != {expected}")
        observed[rel] = actual
    producer_path = ROOT / PRODUCER_REL
    observed[str(PRODUCER_REL)] = sha256(producer_path)
    return observed


def build_result(
    loads: dict[str, Any],
    receiver: dict[str, Any],
    model: dict[str, Any],
    contact_geometry: dict[str, Any],
    wrench_rows: list[dict[str, str]],
) -> dict[str, Any]:
    revision = loads["geometry_revision_id"]
    if model["revision_id"] != revision or receiver["revision_id"] != revision:
        raise ValueError("load, reduced-static, and receiver revisions differ")
    if model["contact_geometry_artifact"] != str(CONTACT_REL):
        raise ValueError("reduced-static model points to a different contact-geometry artifact")
    if contact_geometry["revision_id"] != revision:
        raise ValueError("contact geometry revision differs from the selected load revision")
    if model["source_sha256"].get(str(LOADS_REL)) != PINS[str(LOADS_REL)]:
        raise ValueError("reduced-static model no longer pins the current load contract")
    if model["mechanical_acceptance"] is not False or model["native_solve_run"] is not False:
        raise ValueError("reduced-static acceptance/run boundary changed")

    load_cases = {row["case_id"]: row for row in loads["cases"]}
    model_cases = {row["case_id"]: row for row in model["cases"]}
    if len(load_cases) != 6 or set(load_cases) != set(model_cases):
        raise ValueError("expected the same six cases in both frozen inputs")

    axes_by_panel: dict[str, list[dict[str, Any]]] = {}
    for axis in receiver["axes"]:
        axes_by_panel.setdefault(axis["panel_member"], []).append(axis)
    connections_by_panel: dict[str, list[dict[str, Any]]] = {}
    for connection in model["connections"]:
        for member in connection.get("receiver_member_ids", []):
            if member.startswith("main_") or member.startswith("kicker_"):
                connections_by_panel.setdefault(member, []).append(connection)

    wrench_by_case_member: dict[tuple[str, str], dict[str, str]] = {}
    for row in wrench_rows:
        key = (row["case_id"], row["member_id"])
        if key in wrench_by_case_member:
            raise ValueError(f"duplicate body-wrench row for {key}")
        wrench_by_case_member[key] = row

    contact_patches_by_member: dict[str, list[dict[str, Any]]] = {}
    for patch in contact_geometry["contact_patches"]:
        for member in patch["member_ids"]:
            contact_patches_by_member.setdefault(member, []).append(patch)

    results = []
    maximum_axis_alignment_error = 0.0
    maximum_body_force_reconciliation = 0.0
    members_by_id = {row["member_id"]: row for row in model["members"]}

    for case_id in sorted(load_cases):
        source = load_cases[case_id]
        model_case = model_cases[case_id]
        panel = model_case["loaded_panel"]
        outward = [float(value) for value in source["standoff"]["direction_global_xyz"]]
        if abs(norm(outward) - 1.0) > VECTOR_TOL:
            raise ValueError(f"outward panel normal is not unit length for {case_id}")

        applied_force = [float(value) for value in source["applied_force_global_xyz_n"]]
        model_applied_force = [
            float(value) for value in model_case["source_applied_load"]["applied_force_global_xyz_n"]
        ]
        applied_force_residual = max_abs_difference(applied_force, model_applied_force)
        if applied_force_residual > FORCE_TOL_N:
            raise ValueError(f"climber-force vector differs between frozen sources for {case_id}")

        body_row = wrench_by_case_member.get((case_id, panel))
        if body_row is None:
            raise ValueError(f"missing loaded-panel body wrench for {case_id} / {panel}")
        body_force = [
            float(body_row[name])
            for name in ("external_Fx_N", "external_Fy_N", "external_Fz_N")
        ]

        gravity_rows = model["assigned_gravity_by_member"].get(panel, [])
        if not gravity_rows:
            raise ValueError(f"no assigned panel/T-nut gravity rows for {panel}")
        panel_mass_rows = [row for row in gravity_rows if row["source_name"] == panel]
        if len(panel_mass_rows) != 1:
            raise ValueError(f"expected one own-weight row for panel {panel}")
        panel_volume_mm3 = float(members_by_id[panel]["graph_finished_geometry_summary"]["volume_mm3"])
        panel_density_kg_m3 = float(panel_mass_rows[0]["mass_kg"]) / (panel_volume_mm3 * 1e-9)
        if abs(panel_density_kg_m3 - 600.0) > 1e-6:
            raise ValueError(f"panel density scenario is no longer 600 kg/m^3 for {panel}")
        gravity_force = [0.0, 0.0, 0.0]
        for gravity in gravity_rows:
            if panel not in gravity.get("receiver_member_ids", []):
                raise ValueError(f"gravity row {gravity['source_name']} is not assigned to {panel}")
            for index, value in enumerate(gravity["force_xyz_n"]):
                gravity_force[index] += float(value)
        reconstructed_body_force = [
            applied_force[i] + gravity_force[i] for i in range(3)
        ]
        body_force_residual = max_abs_difference(body_force, reconstructed_body_force)
        maximum_body_force_reconciliation = max(
            maximum_body_force_reconciliation, body_force_residual
        )
        if body_force_residual > FORCE_TOL_N:
            raise ValueError(f"panel body-force row does not equal applied force plus assigned gravity for {case_id}")

        axes = axes_by_panel.get(panel, [])
        connections = connections_by_panel.get(panel, [])
        if len(axes) != 12 or len(connections) != 12:
            raise ValueError(f"expected twelve current screw axes/connections on {panel}")
        if {axis["axis_id"] for axis in axes} != {connection["axis_id"] for connection in connections}:
            raise ValueError(f"receiver axes and reduced-static panel connections differ for {panel}")
        if {connection["kind"] for connection in connections} != {"panel_screw"}:
            raise ValueError(f"unexpected modeled tensile connector kind on {panel}")
        if any(connection.get("mechanical_attachment_defined") is not False for connection in connections):
            raise ValueError(f"unexpected panel screw attachment-law status changed for {panel}")

        alignment_dots = []
        for axis in axes:
            direction = [float(value) for value in axis["axis_global_xyz"]]
            if abs(norm(direction) - 1.0) > VECTOR_TOL:
                raise ValueError(f"non-unit screw axis {axis['axis_id']}")
            alignment = dot(direction, outward)
            alignment_dots.append(alignment)
            maximum_axis_alignment_error = max(maximum_axis_alignment_error, abs(alignment + 1.0))
            if abs(alignment + 1.0) > VECTOR_TOL:
                raise ValueError(f"screw axis {axis['axis_id']} is not directed inward along panel normal")

        opposing_compression_contacts = []
        panel_contact_normal_dots = []
        for patch in contact_patches_by_member.get(panel, []):
            index = patch["member_ids"].index(panel)
            surface_normal = (
                patch["normal_on_first_xyz"] if index == 0 else patch["normal_on_second_xyz"]
            )
            alignment = dot([float(value) for value in surface_normal], outward)
            panel_contact_normal_dots.append(alignment)
            if alignment > CONTACT_NORMAL_TOL:
                opposing_compression_contacts.append({
                    "other_member": patch["member_ids"][1 - index],
                    "panel_surface_normal_dot_outward": alignment,
                    "finite_shared_area_mm2": patch["area_mm2"],
                    "patch_index": patch["patch_index"],
                })

        applied_outward = dot(applied_force, outward)
        gravity_outward = dot(gravity_force, outward)
        body_outward = dot(body_force, outward)
        if min(applied_outward, body_outward) <= 0.0:
            raise ValueError(f"loaded-panel case {case_id} lacks positive outward normal force")
        is_boundable = not opposing_compression_contacts
        results.append({
            "case_id": case_id,
            "loaded_panel": panel,
            "panel_screw_axis_count": len(axes),
            "conditional_panel_density_kg_m3": panel_density_kg_m3,
            "screw_axis_dot_outward_normal": alignment_dots,
            "applied_climber_force_global_xyz_n": applied_force,
            "applied_climber_outward_normal_component_n": applied_outward,
            "assigned_panel_and_same_panel_tnut_gravity_global_xyz_n": gravity_force,
            "assigned_panel_and_same_panel_tnut_gravity_outward_component_n": gravity_outward,
            "loaded_panel_body_external_force_global_xyz_n": body_force,
            "loaded_panel_body_external_outward_normal_component_n": body_outward,
            "conditional_minimum_total_screw_axial_tension_n": body_outward if is_boundable else None,
            "panel_contact_surface_normal_dots_to_outward": panel_contact_normal_dots,
            "opposing_normal_compression_contact_candidates": opposing_compression_contacts,
            "group_bound_disposition": (
                "CONDITIONAL_NORMAL_ONLY_TOTAL_GROUP_LOWER_BOUND"
                if is_boundable
                else "UNRESOLVED_OPPOSING_NORMAL_CONTACT"
            ),
            "applied_force_reconciliation_residual_n": applied_force_residual,
            "panel_body_force_reconciliation_residual_n": body_force_residual,
        })

    boundable = [
        row for row in results
        if row["conditional_minimum_total_screw_axial_tension_n"] is not None
    ]
    governing = max(boundable, key=lambda row: row["conditional_minimum_total_screw_axial_tension_n"])
    least = min(boundable, key=lambda row: row["conditional_minimum_total_screw_axial_tension_n"])
    return {
        "schema": "panel_screw_group_total_withdrawal_lower_bound_with_assigned_gravity/v1",
        "candidate": loads["candidate"],
        "geometry_revision_id": revision,
        "status": "PASS_SCOPED_CONDITIONAL_GROUP_TOTAL_LOWER_BOUND_WITH_ASSIGNED_GRAVITY",
        "source_sha256": {**PINS, str(PRODUCER_REL): sha256(ROOT / PRODUCER_REL)},
        "units": {"force": "N"},
        "method": {
            "result": "For each loaded panel, project its complete current body external force (climber load plus gravity assigned directly to that panel) onto the frozen outward normal. Where every finite panel-contact surface has zero or inward geometric surface-normal projection, compression-only normal contact reactions on the panel are outward or tangent. With twelve inward-parallel screw axes and no tangential contact traction or alternate restraint, summed screw axial tension must be at least the loaded-panel outward resultant.",
            "panel_gravity_assignment": "Use the current reduced-static body's source-assigned panel and same-panel T-nut gravity rows; this is conditional wrench bookkeeping, not proof of a mechanical T-nut carrier.",
            "contact_sign": "A compression reaction on the panel is opposite its outward geometric surface normal. A surface-normal dot with the panel outward normal greater than tolerance identifies a possible inward compression reaction and suppresses the lower-bound claim for that case.",
            "sharing_rule": "No per-screw action, equal share, finite upper bound, or group interaction is inferred.",
            "contact_scope": "Normal-only unilateral panel contact. Tangential friction, screw shear/bending contributions, head/panel mechanisms, and other alternate restraints are not assigned.",
        },
        "result_summary": {
            "case_count": len(results),
            "cases_with_conditional_group_bound": len(boundable),
            "cases_unresolved_by_opposing_normal_contact": len(results) - len(boundable),
            "all_loaded_panels_have_twelve_inward_aligned_screw_axes": True,
            "maximum_axis_alignment_error": maximum_axis_alignment_error,
            "maximum_applied_force_reconciliation_residual_n": max(
                row["applied_force_reconciliation_residual_n"] for row in results
            ),
            "maximum_panel_body_force_reconciliation_residual_n": maximum_body_force_reconciliation,
            "minimum_group_lower_bound_n": least["conditional_minimum_total_screw_axial_tension_n"],
            "minimum_case_id": least["case_id"],
            "maximum_group_lower_bound_n": governing["conditional_minimum_total_screw_axial_tension_n"],
            "governing_case_id": governing["case_id"],
            "governing_panel": governing["loaded_panel"],
            "conditional_panel_density_kg_m3": min(row["conditional_panel_density_kg_m3"] for row in results),
        },
        "case_results": results,
        "readiness": {
            "panel_screw_attachment_law_defined": False,
            "group_force_sharing_established": False,
            "exact_hillman_42605_resistance_available": False,
            "installed_engagement_and_head_panel_limits_verified": False,
            "receiver_to_frame_path_closed": False,
            "panel_withdrawal_gate_closed": False,
            "mechanical_acceptance": False,
            "native_solve_run": False,
        },
        "limits": [
            "This conditional necessary bound applies only to the five cases whose pinned panel-contact geometry contains no surface normal permitting inward compression reaction; `a1-rear` remains unresolved at its 113.5635 mm^2 kicker-left/main-lower-left contact.",
            "The 600 kg/m^3 panel-density scenario and same-panel T-nut weight assignments are modeled inputs, not measurements of delivered panels or a proven mechanical carrier path.",
            "Unassigned screw-axis and other hardware gravity, the separate accessory scenarios, hold/T-nut load-transfer mechanics, and forces transferred beyond the receiving panel are excluded.",
            "Normal-only contact and zero tangential traction are screening assumptions; friction or other alternate restraint could change the screw-group action.",
            "The result is only the sum of axial screw tensions. It does not give per-axis actions, a finite upper bound, equal sharing, product resistance, a safety factor, or a code-compliant group check.",
            "Exact Hillman 42605 withdrawal/load-slip properties, installed penetration, head/panel limits, defensible group distribution, and downstream receiver transfer remain unresolved.",
            "No actual stock, installation, active contact state, or physical restraint was inspected. Missing evidence is not a physical failure finding.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="reconstruct and compare without writing")
    mode.add_argument("--write", action="store_true", help="write only after source hash checks pass")
    args = parser.parse_args()

    pins = verify_sources()
    loads = json.loads((ROOT / LOADS_REL).read_text())
    receiver = json.loads((ROOT / RECEIVER_REL).read_text())
    model = json.loads((ROOT / MODEL_REL).read_text())
    contact_geometry = json.loads((ROOT / CONTACT_REL).read_text())
    with (ROOT / WRENCHES_REL).open(newline="") as stream:
        wrench_rows = list(csv.DictReader(stream))
    record = build_result(loads, receiver, model, contact_geometry, wrench_rows)
    record["source_sha256"] = pins
    path = HERE / "panel-group-with-gravity-result.json"
    rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.write:
        path.write_text(rendered)
        print(f"wrote {path.relative_to(ROOT)}")
        return
    if not path.exists():
        raise SystemExit(f"missing {path}; run with --write after inspecting source pins")
    if path.read_text() != rendered:
        raise SystemExit("verification failed: recomputed record differs from saved output")
    summary = record["result_summary"]
    print(
        f"PASS: {summary['cases_with_conditional_group_bound']}/6 cases have conditional total group lower bounds including assigned panel/T-nut gravity of "
        f"{summary['minimum_group_lower_bound_n']:.2f}–{summary['maximum_group_lower_bound_n']:.2f} N; "
        f"{summary['cases_unresolved_by_opposing_normal_contact']}/6 remain unresolved; no per-screw share, capacity, or native run claimed"
    )


if __name__ == "__main__":
    main()
