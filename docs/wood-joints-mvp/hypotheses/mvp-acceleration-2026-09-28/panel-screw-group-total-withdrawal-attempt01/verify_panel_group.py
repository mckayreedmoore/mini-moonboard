#!/usr/bin/env python3
"""Reconstruct climber-load-only lower bounds on panel screw-group tension."""

from __future__ import annotations

import argparse
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
CONTACT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json"
)
PINS = {
    str(LOADS_REL): "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    str(RECEIVER_REL): "851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991",
    str(MODEL_REL): "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
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
    observed = {}
    for rel, expected in PINS.items():
        actual = sha256(ROOT / rel)
        if actual != expected:
            raise ValueError(f"source hash changed for {rel}: {actual} != {expected}")
        observed[rel] = actual
    return observed


def build_result(
    loads: dict[str, Any],
    receiver: dict[str, Any],
    model: dict[str, Any],
    contact_geometry: dict[str, Any],
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

    interfaces = receiver["panel_to_receiver_interfaces"]["interfaces"]
    interface_by_pair = {(row["panel_member"], row["receiver_member"]): row for row in interfaces}
    contact_patches_by_member: dict[str, list[dict[str, Any]]] = {}
    for patch in contact_geometry["contact_patches"]:
        for member in patch["member_ids"]:
            contact_patches_by_member.setdefault(member, []).append(patch)
    results = []
    maximum_alignment_error = 0.0
    maximum_force_reconciliation = 0.0

    for case_id in sorted(load_cases):
        source = load_cases[case_id]
        model_case = model_cases[case_id]
        panel = model_case["loaded_panel"]
        force = [float(value) for value in source["applied_force_global_xyz_n"]]
        model_force = [float(value) for value in model_case["source_applied_load"]["applied_force_global_xyz_n"]]
        force_residual = max_abs_difference(force, model_force)
        maximum_force_reconciliation = max(maximum_force_reconciliation, force_residual)
        if force_residual > FORCE_TOL_N:
            raise ValueError(f"load vector differs between frozen sources for {case_id}")

        outward = [float(value) for value in source["standoff"]["direction_global_xyz"]]
        if abs(norm(outward) - 1.0) > VECTOR_TOL:
            raise ValueError(f"outward panel normal is not unit length for {case_id}")
        axes = axes_by_panel.get(panel, [])
        connections = connections_by_panel.get(panel, [])
        if len(axes) != 12 or len(connections) != 12:
            raise ValueError(f"expected twelve current screw axes/connections on {panel}")
        if {axis["axis_id"] for axis in axes} != {connection["axis_id"] for connection in connections}:
            raise ValueError(f"receiver axes and reduced-static panel connections differ for {panel}")
        if {connection["kind"] for connection in connections} != {"panel_screw"}:
            raise ValueError(f"unexpected modeled tensile connector kind on {panel}")
        if any(connection.get("mechanical_attachment_defined") is not False for connection in connections):
            raise ValueError(f"unexpected attachment-law status changed for {panel}")

        alignment_dots = []
        attached_receivers = set()
        for axis in axes:
            direction = [float(value) for value in axis["axis_global_xyz"]]
            if abs(norm(direction) - 1.0) > VECTOR_TOL:
                raise ValueError(f"non-unit screw axis {axis['axis_id']}")
            alignment = dot(direction, outward)
            alignment_dots.append(alignment)
            maximum_alignment_error = max(maximum_alignment_error, abs(alignment + 1.0))
            if abs(alignment + 1.0) > VECTOR_TOL:
                raise ValueError(f"screw axis {axis['axis_id']} is not directed inward along the panel normal")
            attached_receivers.add(axis["receiver_member"])

        if not attached_receivers:
            raise ValueError(f"no receiver interfaces found for {panel}")
        for receiver_member in attached_receivers:
            interface = interface_by_pair.get((panel, receiver_member))
            if interface is None or interface["geometry_state"] != "finite_planar_face_contact":
                raise ValueError(f"missing finite rear-face geometry for {panel} / {receiver_member}")

        outward_force = dot(force, outward)
        if outward_force <= 0:
            raise ValueError(f"load case {case_id} has no positive outward panel-normal force")
        application_moment = [float(value) for value in source["applied_wrench"]["moment_global_xyz_nmm"]]
        opposing_compression_contacts = []
        contact_normal_dots = []
        for patch in contact_patches_by_member.get(panel, []):
            index = patch["member_ids"].index(panel)
            surface_normal = patch["normal_on_first_xyz"] if index == 0 else patch["normal_on_second_xyz"]
            alignment = dot([float(value) for value in surface_normal], outward)
            contact_normal_dots.append(alignment)
            if alignment > CONTACT_NORMAL_TOL:
                opposing_compression_contacts.append({
                    "other_member": patch["member_ids"][1 - index],
                    "panel_face_normal_dot_outward": alignment,
                    "finite_shared_area_mm2": patch["area_mm2"],
                    "patch_index": patch["patch_index"],
                })
        group_bound = None if opposing_compression_contacts else outward_force
        results.append({
            "case_id": case_id,
            "loaded_panel": panel,
            "panel_screw_axis_count": len(axes),
            "panel_screw_receiver_members": sorted(attached_receivers),
            "axis_dot_outward_normal": alignment_dots,
            "climber_load_force_global_xyz_n": force,
            "climber_load_outward_normal_component_n": outward_force,
            "conditional_minimum_group_axial_tension_n": group_bound,
            "panel_contact_face_normal_dots_to_outward": contact_normal_dots,
            "opposing_compression_contact_candidates": opposing_compression_contacts,
            "group_bound_disposition": (
                "UNRESOLVED_OPPOSING_NORMAL_CONTACT"
                if opposing_compression_contacts
                else "CONDITIONAL_BOUND_UNDER_NORMAL_ONLY_CONTACT"
            ),
            "climber_load_moment_global_xyz_nmm": application_moment,
            "force_reconciliation_residual_n": force_residual,
            "interpretation": "necessary total group axial tension under compression-only rear support and no alternate out-of-plane tensile restraint; before gravity",
        })

    boundable = [row for row in results if row["conditional_minimum_group_axial_tension_n"] is not None]
    if not boundable:
        raise ValueError("no case has a support boundary sufficient for a group-total bound")
    governing = max(boundable, key=lambda row: row["conditional_minimum_group_axial_tension_n"])
    least = min(boundable, key=lambda row: row["conditional_minimum_group_axial_tension_n"])
    return {
        "schema": "panel_screw_group_total_withdrawal_lower_bound/v1",
        "candidate": loads["candidate"],
        "geometry_revision_id": revision,
        "status": "PASS_SCOPED_CONDITIONAL_GROUP_TOTAL_LOWER_BOUND",
        "source_sha256": PINS,
        "units": {"force": "N", "moment": "N*mm"},
        "method": {
            "equilibrium_axis": "current load contract's outward panel normal",
            "group_resultant_rule": "For outward external normal force Fout, compression-only rear contacts push outward. If every finite panel contact face has zero or negative panel-outward normal projection, and the modeled support law is normal-only, then with all screw axes parallel to the inward normal the summed axial screw tension must be at least Fout. Any contact face whose panel normal points outward can push inward in compression and prevents this bound unless its state/law is separately resolved.",
            "sharing_rule": "No per-screw split or equal sharing is inferred.",
            "contact_scope": "Normal-only unilateral face contact; tangential friction or other restraint is unassigned and receives no credit.",
        },
        "result_summary": {
            "case_count": len(results),
            "cases_with_conditional_group_bound": len(boundable),
            "cases_unresolved_by_opposing_normal_contact": len(results) - len(boundable),
            "all_loaded_panels_have_twelve_aligned_screw_axes": True,
            "maximum_axis_alignment_error": maximum_alignment_error,
            "maximum_force_reconciliation_residual_n": maximum_force_reconciliation,
            "minimum_group_lower_bound_n": least["conditional_minimum_group_axial_tension_n"],
            "minimum_case_id": least["case_id"],
            "maximum_group_lower_bound_n": governing["conditional_minimum_group_axial_tension_n"],
            "governing_case_id": governing["case_id"],
            "governing_panel": governing["loaded_panel"],
        },
        "case_results": results,
        "readiness": {
            "panel_screw_attachment_law_defined": False,
            "group_force_sharing_established": False,
            "screw_capacity_check_available": False,
            "panel_withdrawal_gate_closed": False,
            "mechanical_acceptance": False,
            "native_solve_run": False,
        },
        "limits": [
            "This is a climber-load-only conditional lower bound on the sum of axial tensions over the loaded panel's twelve screws only for cases whose pinned contact-face normals do not reveal an opposing compression path, under normal-only unilateral contact.",
            "It excludes panel, T-nut, hold, and accessory gravity; applying the eccentric moments still creates unknown concentration and redistribution among axes.",
            "The `a1-rear` / `main_lower_left` case is left unbounded because the pinned geometry includes a 113.5635 mm^2 `kicker_left` contact face whose normal permits an inward compression reaction; its active state and force transfer are unknown.",
            "Zero tangential contact traction is an explicit screening condition, not a demonstrated physical law; edge friction or another out-of-plane restraint could alter group action.",
            "The source-defined load is applied directly to the panel; hold/T-nut mechanics are bypassed.",
            "The group lower bound is not a per-screw demand, equal-share estimate, load-slip law, resistance, safety factor, or code check.",
            "Exact Hillman 42605 withdrawal/stiffness, installed penetration, head/panel resistance, defensible group distribution, and receiver-to-frame transfer remain unresolved.",
            "No actual stock, installation, bearing contact, or alternate physical restraint was inspected; the result does not close the panel-withdrawal or receiver-path gate.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="reconstruct and compare without writing")
    mode.add_argument("--write", action="store_true", help="write only after frozen-source checks pass")
    args = parser.parse_args()

    pins = verify_sources()
    loads = json.loads((ROOT / LOADS_REL).read_text())
    receiver = json.loads((ROOT / RECEIVER_REL).read_text())
    model = json.loads((ROOT / MODEL_REL).read_text())
    contact_geometry = json.loads((ROOT / CONTACT_REL).read_text())
    record = build_result(loads, receiver, model, contact_geometry)
    record["source_sha256"] = pins
    path = HERE / "panel-group-result.json"
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
        f"PASS: all six panel/group mappings reconcile; {summary['cases_with_conditional_group_bound']}/6 cases have conditional total screw-group axial-tension lower bounds of "
        f"{summary['minimum_group_lower_bound_n']:.2f}–{summary['maximum_group_lower_bound_n']:.2f} N; "
        f"{summary['cases_unresolved_by_opposing_normal_contact']}/6 remain unbounded by opposing-normal contact; no per-screw split or capacity check is claimed"
    )


if __name__ == "__main__":
    main()
