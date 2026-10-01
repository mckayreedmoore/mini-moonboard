#!/usr/bin/env python3
"""Verify conditional total axial-tension bounds for both upper-panel groups."""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
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
PINS = {
    str(LOADS_REL): "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    str(RECEIVER_REL): "851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991",
    str(MODEL_REL): "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    str(WRENCHES_REL): "6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f",
    str(CONTACT_REL): "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
}
PANELS = ("main_upper_left", "main_upper_right")
FORCE_TOL_N = 1e-8
VECTOR_TOL = 1e-10
CONTACT_PATCH_COUNT = 7
RESULT_PATH = HERE / "upper-panel-group-result.json"
PRODUCER_REL = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "panel-screw-group-total-withdrawal-attempt03/verify_upper_panel_groups.py"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_dot(left: list[float], right: list[float]) -> Fraction:
    """Compute the dot product exactly for serialized binary64 components."""
    return sum(
        (
            Fraction.from_float(float(a)) * Fraction.from_float(float(b))
            for a, b in zip(left, right, strict=True)
        ),
        Fraction(0),
    )


def vector_difference(left: list[float], right: list[float]) -> float:
    return max(abs(float(a) - float(b)) for a, b in zip(left, right, strict=True))


def source_pins() -> dict[str, str]:
    observed = {}
    for relative, expected in PINS.items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise ValueError(f"source hash changed for {relative}: {actual} != {expected}")
        observed[relative] = actual
    observed[str(PRODUCER_REL)] = sha256(ROOT / PRODUCER_REL)
    return observed


def build_result(
    loads: dict[str, Any],
    receiver: dict[str, Any],
    model: dict[str, Any],
    contact: dict[str, Any],
    wrench_rows: list[dict[str, str]],
    pins: dict[str, str],
) -> dict[str, Any]:
    revision = loads["geometry_revision_id"]
    if (model["candidate"], model["revision_id"]) != (
        "compact-floor-flush-wood-joints-development",
        revision,
    ):
        raise ValueError("candidate or revision differs from the frozen load contract")
    if receiver["revision_id"] != revision or contact["revision_id"] != revision:
        raise ValueError("receiver/contact inputs do not match the frozen revision")
    if model.get("contact_geometry_artifact") != str(CONTACT_REL):
        raise ValueError("model points to a different contact-geometry artifact")
    if model.get("source_sha256", {}).get(str(LOADS_REL)) != PINS[str(LOADS_REL)]:
        raise ValueError("model no longer pins the frozen six-case load contract")
    if model["mechanical_acceptance"] or model["native_solve_run"] or model["ready_for_six_case_response"]:
        raise ValueError("source readiness or run boundary changed")

    load_cases = {row["case_id"]: row for row in loads["cases"]}
    model_cases = {row["case_id"]: row for row in model["cases"]}
    if len(load_cases) != 6 or set(load_cases) != set(model_cases):
        raise ValueError("expected six matching frozen load and model cases")

    csv_by_case_member = {}
    for row in wrench_rows:
        key = (row["case_id"], row["member_id"])
        if key in csv_by_case_member:
            raise ValueError(f"duplicate body-wrench row for {key}")
        csv_by_case_member[key] = [
            float(row["external_Fx_N"]),
            float(row["external_Fy_N"]),
            float(row["external_Fz_N"]),
        ]

    axes_by_panel: dict[str, list[dict[str, Any]]] = {}
    for row in receiver["axes"]:
        if row.get("panel_member") in PANELS:
            axes_by_panel.setdefault(row["panel_member"], []).append(row)
    connections_by_panel: dict[str, list[dict[str, Any]]] = {}
    for row in model["connections"]:
        panel = row.get("source_record", {}).get("panel_member")
        if row.get("kind") == "panel_screw" and panel in PANELS:
            connections_by_panel.setdefault(panel, []).append(row)

    contacts_by_panel = {panel: [] for panel in PANELS}
    for patch in contact["contact_patches"]:
        for panel in PANELS:
            if panel in patch["member_ids"]:
                contacts_by_panel[panel].append(patch)

    members = {row["member_id"]: row for row in model["members"]}
    gravity_by_panel = model["assigned_gravity_by_member"]
    panel_axes = {}
    contact_signs = {}

    for panel in PANELS:
        axes = axes_by_panel.get(panel, [])
        connections = connections_by_panel.get(panel, [])
        if len(axes) != 12 or len(connections) != 12:
            raise ValueError(f"expected twelve receiver axes and model screws for {panel}")
        axis_ids = {row["axis_id"] for row in axes}
        if axis_ids != {row["axis_id"] for row in connections}:
            raise ValueError(f"receiver/model screw axis IDs differ for {panel}")
        if {row["mechanical_attachment_defined"] for row in connections} != {False}:
            raise ValueError(f"unexpected attachment-law status for {panel}")
        vectors = {
            tuple(float(value) for value in row["axis_global_xyz"])
            for row in axes
        }
        if len(vectors) != 1:
            raise ValueError(f"panel screw axes are not co-directed for {panel}")
        axis = list(next(iter(vectors)))
        if abs(math.sqrt(sum(value * value for value in axis)) - 1.0) > VECTOR_TOL:
            raise ValueError(f"non-unit screw axis for {panel}")
        outward = [-value for value in axis]

        contact_projections = []
        for patch in contacts_by_panel[panel]:
            panel_index = patch["member_ids"].index(panel)
            normal = [float(value) for value in patch["normal_on_first_xyz"]]
            if abs(math.sqrt(sum(value * value for value in normal)) - 1.0) > VECTOR_TOL:
                raise ValueError(f"non-unit contact normal for {panel}")
            # Compression acts opposite normal_on_first on member_ids[0],
            # and along it on member_ids[1].
            reaction = [-value for value in normal] if panel_index == 0 else normal
            projection = exact_dot(outward, reaction)
            if projection < 0:
                raise ValueError(f"recorded contact can react inward for {panel}")
            contact_projections.append(projection)
        if len(contact_projections) != CONTACT_PATCH_COUNT:
            raise ValueError(
                f"expected {CONTACT_PATCH_COUNT} recorded contacts for {panel}, "
                f"got {len(contact_projections)}"
            )

        # Bind the candidate's full model axis to its twelve connection axes.
        model_vectors = {
            tuple(float(value) for value in row["axis_xyz"])
            for row in connections
        }
        if model_vectors != {tuple(axis)}:
            raise ValueError(f"receiver and model axis vectors differ for {panel}")
        panel_axes[panel] = {
            "axis_inward_xyz": axis,
            "outward_normal_xyz": outward,
            "screw_count": len(axes),
        }
        contact_signs[panel] = {
            "patch_count": len(contact_projections),
            "positive_outward_reaction_directions": sum(p > 0 for p in contact_projections),
            "tangent_directions": sum(p == 0 for p in contact_projections),
            "negative_inward_reaction_directions": 0,
            "minimum_positive_projection": min(float(p) for p in contact_projections if p > 0),
        }

    results = []
    maximum_force_reconciliation = 0.0
    for case_id in sorted(load_cases):
        source_case = load_cases[case_id]
        model_case = model_cases[case_id]
        source_force = [float(value) for value in source_case["applied_force_global_xyz_n"]]
        model_force = [
            float(value)
            for value in model_case["source_applied_load"]["applied_force_global_xyz_n"]
        ]
        if vector_difference(source_force, model_force) > FORCE_TOL_N:
            raise ValueError(f"source/model applied force differs for {case_id}")

        panel_body_wrenches = {
            row["member_id"]: row
            for row in model_case["body_external_wrenches"]
            if row["member_id"] in PANELS
        }
        for panel in PANELS:
            if panel not in panel_body_wrenches:
                raise ValueError(f"missing body wrench for {case_id}/{panel}")
            gravity_rows = gravity_by_panel.get(panel, [])
            own_rows = [row for row in gravity_rows if row["source_name"] == panel]
            if len(own_rows) != 1:
                raise ValueError(f"expected one own-weight source row for {panel}")
            volume_mm3 = float(members[panel]["graph_finished_geometry_summary"]["volume_mm3"])
            density = float(own_rows[0]["mass_kg"]) / (volume_mm3 * 1e-9)
            if abs(density - 600.0) > 1e-6:
                raise ValueError(f"panel density scenario changed for {panel}: {density}")

            gravity_force = [0.0, 0.0, 0.0]
            for row in gravity_rows:
                if panel not in row.get("receiver_member_ids", []):
                    raise ValueError(f"gravity row {row['source_name']} not assigned to {panel}")
                for i, value in enumerate(row["force_xyz_n"]):
                    gravity_force[i] += float(value)
            panel_only_gravity = [float(value) for value in own_rows[0]["force_xyz_n"]]
            applied_to_panel = source_force if model_case["loaded_panel"] == panel else [0.0, 0.0, 0.0]
            expected_force = [gravity_force[i] + applied_to_panel[i] for i in range(3)]
            panel_only_force = [panel_only_gravity[i] + applied_to_panel[i] for i in range(3)]
            model_body = panel_body_wrenches[panel]
            body_force = [float(value) for value in model_body["assigned_external_force_xyz_n"]]
            csv_force = csv_by_case_member.get((case_id, panel))
            if csv_force is None:
                raise ValueError(f"missing CSV body-wrench row for {case_id}/{panel}")
            residual_model = vector_difference(body_force, expected_force)
            residual_csv = vector_difference(csv_force, expected_force)
            residual_export = vector_difference(body_force, csv_force)
            residual = max(residual_model, residual_csv, residual_export)
            maximum_force_reconciliation = max(maximum_force_reconciliation, residual)
            if residual > FORCE_TOL_N:
                raise ValueError(
                    f"panel body force does not reconcile to applied force plus assigned gravity "
                    f"for {case_id}/{panel}: residual={residual} N"
                )

            outward = panel_axes[panel]["outward_normal_xyz"]
            source_outward = [
                float(value) for value in load_cases[case_id]["standoff"]["direction_global_xyz"]
            ]
            if vector_difference(outward, source_outward) > VECTOR_TOL:
                raise ValueError(f"screw axis/outward normal differs from load contract for {case_id}/{panel}")
            projected = exact_dot(outward, body_force)
            if projected <= 0:
                raise ValueError(f"nonpositive outward external force for {case_id}/{panel}")
            panel_only_projected = exact_dot(outward, panel_only_force)
            if panel_only_projected <= 0:
                raise ValueError(f"nonpositive panel-only outward force for {case_id}/{panel}")
            tnut_projected = exact_dot(
                outward,
                [gravity_force[i] - panel_only_gravity[i] for i in range(3)],
            )
            if tnut_projected < 0:
                raise ValueError(f"assigned T-nut gravity is not outward for {panel}")
            results.append({
                "case_id": case_id,
                "panel_member": panel,
                "climber_loaded_panel": model_case["loaded_panel"],
                "climber_load_applied_to_this_panel": model_case["loaded_panel"] == panel,
                "body_external_force_xyz_n": body_force,
                "assigned_panel_and_same_panel_tnut_gravity_xyz_n": gravity_force,
                "panel_own_gravity_only_xyz_n": panel_only_gravity,
                "climber_plus_panel_own_weight_force_xyz_n": panel_only_force,
                "conditional_panel_density_kg_m3": density,
                "outward_normal_force_exact_sign_positive": True,
                "panel_mass_only_conditional_minimum_sum_of_12_screw_axial_tensions_n": float(panel_only_projected),
                "assigned_tnut_gravity_outward_component_n": float(tnut_projected),
                "conditional_minimum_sum_of_12_screw_axial_tensions_n": float(projected),
                "body_force_reconciliation_residual_n": residual,
                "contact_normal_projection_summary": contact_signs[panel],
            })

    panel_only_values = [
        row["panel_mass_only_conditional_minimum_sum_of_12_screw_axial_tensions_n"]
        for row in results
    ]
    values = [row["conditional_minimum_sum_of_12_screw_axial_tensions_n"] for row in results]
    governing = max(results, key=lambda row: row["conditional_minimum_sum_of_12_screw_axial_tensions_n"])
    return {
        "schema": "conditional_upper_panel_group_total_withdrawal_bounds/v1",
        "candidate": model["candidate"],
        "revision_id": revision,
        "status": "PASS_SCOPED_CONDITIONAL_UPPER_PANEL_GROUP_BOUNDS",
        "source_sha256": pins,
        "units": {"force": "N"},
        "method": {
            "result": (
                "For each of two upper panels in each of six cases, sum the assigned external body force "
                "(climber action on that panel if loaded, plus that panel's and same-panel T-nuts' assigned "
                "gravity) and project it onto the outward normal opposite the twelve parallel screw axes. "
                "Every recorded compression-only contact reaction direction has zero or nonnegative outward "
                "projection. Therefore the summed inward axial screw tension is at least the outward external "
                "force under this recorded normal-only topology."
            ),
            "scope": (
                "Necessary panel-group force-equilibrium lower bounds only. No moment closure, contact state, "
                "individual screw share, stiffness, upper bound, resistance, safety factor, or downstream "
                "receiver/member action is established."
            ),
            "panel_only_bound": (
                "A second lower bound uses only each panel's own modeled gravity and the case force applied "
                "directly to that panel. It omits same-panel T-nut weights, so it does not depend on the "
                "unverified T-nut-to-panel gravity-carrier assignment. It remains conditional on the modeled "
                "600 kg/m^3 panel density and the recorded contact/restraint topology."
            ),
            "gravity_assignment": (
                "Uses the source-assigned same-panel T-nut gravity bookkeeping at the conditional 600 kg/m^3 "
                "panel-density scenario; it does not prove a mechanical T-nut carrier."
            ),
            "contact_assumption": (
                "Only the seven finite contacts recorded for each upper panel are screened; compression-only "
                "normal reactions are outward or tangent in the recorded geometry. Tangential contact, an "
                "unrecorded restraint, and physical contact activation are not modeled."
            ),
        },
        "summary": {
            "upper_panel_case_groups": len(results),
            "upper_panels": list(PANELS),
            "cases": len(load_cases),
            "panel_mass_only_minimum_conditional_group_lower_bound_n": min(panel_only_values),
            "panel_mass_only_maximum_conditional_group_lower_bound_n": max(panel_only_values),
            "minimum_conditional_group_lower_bound_n": min(values),
            "maximum_conditional_group_lower_bound_n": max(values),
            "governing_case_id": governing["case_id"],
            "governing_panel": governing["panel_member"],
            "maximum_force_reconciliation_residual_n": maximum_force_reconciliation,
            "all_groups_have_12_inward_aligned_screws": True,
            "all_recorded_compression_contact_directions_are_outward_or_tangent": True,
        },
        "case_group_results": results,
        "not_screened": {
            "lower_panel_screw_groups": True,
            "a1_rear_loaded_lower_left_group": (
                "UNRESOLVED: the recorded kicker_left/main_lower_left contact has an inward compression "
                "reaction direction, so the outward-force projection alone gives no screw-group lower bound."
            ),
            "panel_withdrawal_gate_closed": False,
            "receiver_to_frame_path_closed": False,
            "mechanical_acceptance": False,
            "native_solve_run": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true", help="recompute and compare without writing")
    modes.add_argument("--write", action="store_true", help="write a new result after source checks")
    args = parser.parse_args()

    pins = source_pins()
    loads = json.loads((ROOT / LOADS_REL).read_text())
    receiver = json.loads((ROOT / RECEIVER_REL).read_text())
    model = json.loads((ROOT / MODEL_REL).read_text())
    contact = json.loads((ROOT / CONTACT_REL).read_text())
    with (ROOT / WRENCHES_REL).open(newline="") as stream:
        wrench_rows = list(csv.DictReader(stream))
    result = build_result(loads, receiver, model, contact, wrench_rows, pins)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"

    if args.write:
        if RESULT_PATH.exists():
            raise SystemExit(f"refusing to overwrite existing result: {RESULT_PATH}")
        RESULT_PATH.write_text(rendered)
        print(f"wrote {RESULT_PATH.relative_to(ROOT)}")
        return
    if not RESULT_PATH.exists():
        raise SystemExit(f"result is missing: {RESULT_PATH}; use --write")
    existing = json.loads(RESULT_PATH.read_text())
    if existing != json.loads(rendered):
        raise SystemExit("FAIL: recomputed upper-panel group result differs from saved result")
    print(
        "PASS: 12 upper-panel/case groups have conditional total axial-tension lower bounds "
        f"of {min(row['conditional_minimum_sum_of_12_screw_axial_tensions_n'] for row in result['case_group_results']):.3f}–"
        f"{max(row['conditional_minimum_sum_of_12_screw_axial_tensions_n'] for row in result['case_group_results']):.3f} N "
        "with assigned T-nut gravity; panel-mass-only bounds are "
        f"{min(row['panel_mass_only_conditional_minimum_sum_of_12_screw_axial_tensions_n'] for row in result['case_group_results']):.3f}–"
        f"{max(row['panel_mass_only_conditional_minimum_sum_of_12_screw_axial_tensions_n'] for row in result['case_group_results']):.3f} N; "
        "lower-panel groups and resistance remain unresolved"
    )


if __name__ == "__main__":
    main()
