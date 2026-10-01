#!/usr/bin/env python3
"""Cross-check floor-normal resultants for frozen loads and accessory scenarios."""

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
ACCESSORY_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-dead-load-scenarios-attempt01/dead-load-scenarios.json"
)
HULL_REL = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/global-equilibrium.json")
EXPECTED_PINS = {
    str(LOADS_REL): "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    str(ACCESSORY_REL): "37df743291b49d0a2b68274cd18337051c75dc927d72e49a903162d10f982e83",
    str(HULL_REL): "4fe8652f4296827ed8bf06b376cee22194027d24eb64a73a17afa87679ffb381",
}
FORCE_TOLERANCE_N = 1e-7
MOMENT_TOLERANCE_NMM = 1e-5
HULL_TOLERANCE_MM = 1e-6


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add(a: list[float], b: list[float]) -> list[float]:
    return [float(x) + float(y) for x, y in zip(a, b, strict=True)]


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def max_abs_difference(a: list[float], b: list[float]) -> float:
    return max(abs(float(x) - float(y)) for x, y in zip(a, b, strict=True))


def polygon_signed_area(points: list[list[float]]) -> float:
    return 0.5 * sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )


def edge_margins(points: list[list[float]], xy: list[float]) -> list[float]:
    area = polygon_signed_area(points)
    if abs(area) < 1e-9:
        raise ValueError("support hull has zero area")
    orientation = 1.0 if area > 0 else -1.0
    margins = []
    for i, start in enumerate(points):
        end = points[(i + 1) % len(points)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length <= 0:
            raise ValueError("support hull has a zero-length edge")
        signed_distance = orientation * (dx * (xy[1] - start[1]) - dy * (xy[0] - start[0])) / length
        margins.append(signed_distance)
    return margins


def check_pins() -> dict[str, str]:
    observed = {}
    for rel, expected in EXPECTED_PINS.items():
        actual = sha256(ROOT / rel)
        if actual != expected:
            raise ValueError(f"source hash changed for {rel}: {actual} != {expected}")
        observed[rel] = actual
    return observed


def build_record(loads: dict[str, Any], dead: dict[str, Any], hull_data: dict[str, Any], pins: dict[str, str]) -> dict[str, Any]:
    revision = loads["geometry_revision_id"]
    if revision != dead["revision_id"] or revision != hull_data["geometry_revision_id"]:
        raise ValueError("the applied-load, accessory, and support-hull revisions differ")
    if loads["candidate"] != dead["candidate"]:
        raise ValueError("the applied-load and accessory candidates differ")

    scenarios = dead["accessory_allowance"]["scenarios"]
    if len(scenarios) != 9:
        raise ValueError(f"expected nine recorded accessory placements, found {len(scenarios)}")
    scenarios_by_id = {row["scenario_id"]: row for row in scenarios}
    if len(scenarios_by_id) != len(scenarios):
        raise ValueError("accessory scenario IDs are not unique")
    cases_by_id = {row["case_id"]: row for row in loads["cases"]}
    if len(cases_by_id) != len(loads["cases"]):
        raise ValueError("applied load case IDs are not unique")
    if set(row["case_id"] for row in hull_data["cases"]) != set(cases_by_id):
        raise ValueError("support-hull screen case IDs differ from applied-load contract")

    hull = [[float(x), float(y)] for x, y in hull_data["support_hull_xy_mm"]]
    if len(hull) < 3:
        raise ValueError("support hull needs at least three vertices")
    if abs(polygon_signed_area(hull)) <= 1e-9:
        raise ValueError("support hull is degenerate")

    base_gravity = dead["modeled_body_gravity"]
    base_force = [float(v) for v in base_gravity["gravity_force_global_xyz_n"]]
    base_moment = [float(v) for v in base_gravity["gravity_moment_about_global_origin_nmm"]]
    resultants = dead["gravity_and_six_case_resultants"]["scenario_case_resultants"]
    if len(resultants) != len(scenarios) * len(cases_by_id):
        raise ValueError("the stored scenario/case resultant count is incomplete")

    output_rows = []
    max_force_closure = 0.0
    max_moment_closure = 0.0
    for source_row in resultants:
        scenario_id = source_row["scenario_id"]
        case_id = source_row["case_id"]
        if scenario_id not in scenarios_by_id or case_id not in cases_by_id:
            raise ValueError(f"unknown scenario/case pair: {scenario_id} / {case_id}")
        accessory = scenarios_by_id[scenario_id]
        case = cases_by_id[case_id]

        applied = case["applied_wrench"]
        applied_force = [float(v) for v in applied["force_global_xyz_n"]]
        applied_moment_origin = add(
            [float(v) for v in applied["moment_global_xyz_nmm"]],
            cross([float(v) for v in applied["reference_point_global_xyz_mm"]], applied_force),
        )
        accessory_force = [float(v) for v in accessory["accessory_gravity_force_global_xyz_n"]]
        accessory_moment = [float(v) for v in accessory["accessory_gravity_moment_about_global_origin_nmm"]]
        expected_dead_force = add(base_force, accessory_force)
        expected_dead_moment = add(base_moment, accessory_moment)
        expected_total_force = add(expected_dead_force, applied_force)
        expected_total_moment = add(expected_dead_moment, applied_moment_origin)

        force_residual = max_abs_difference(
            expected_total_force, source_row["combined_external_force_global_xyz_n"]
        )
        moment_residual = max_abs_difference(
            expected_total_moment, source_row["combined_external_moment_about_global_origin_nmm"]
        )
        dead_force_residual = max_abs_difference(
            expected_dead_force, source_row["dead_load_resultant_force_global_xyz_n"]
        )
        dead_moment_residual = max_abs_difference(
            expected_dead_moment, source_row["dead_load_resultant_moment_about_global_origin_nmm"]
        )
        max_force_closure = max(max_force_closure, force_residual, dead_force_residual)
        max_moment_closure = max(max_moment_closure, moment_residual, dead_moment_residual)
        if force_residual > FORCE_TOLERANCE_N or dead_force_residual > FORCE_TOLERANCE_N:
            raise ValueError(f"wrench force reconstruction failed for {scenario_id} / {case_id}")
        if moment_residual > MOMENT_TOLERANCE_NMM or dead_moment_residual > MOMENT_TOLERANCE_NMM:
            raise ValueError(f"wrench moment reconstruction failed for {scenario_id} / {case_id}")

        force = expected_total_force
        moment = expected_total_moment
        normal = -force[2]
        if normal <= 0:
            raise ValueError(f"nonpositive required floor-normal resultant for {scenario_id} / {case_id}")
        cop_xy = [moment[1] / normal, -moment[0] / normal]
        margins = edge_margins(hull, cop_xy)
        minimum_margin = min(margins)
        output_rows.append({
            "scenario_id": scenario_id,
            "case_id": case_id,
            "total_external_force_global_xyz_n": force,
            "total_external_moment_about_global_origin_nmm": moment,
            "required_floor_normal_resultant_n": normal,
            "required_floor_tangent_resultant_global_xy_n": [-force[0], -force[1]],
            "required_floor_yaw_reaction_nmm": -moment[2],
            "required_floor_normal_center_of_pressure_xy_mm": cop_xy,
            "support_hull_edge_margins_mm": margins,
            "minimum_support_hull_edge_margin_mm": minimum_margin,
            "normal_resultant_inside_modeled_support_hull": minimum_margin >= -HULL_TOLERANCE_MM,
            "force_reconstruction_residual_n": force_residual,
            "moment_reconstruction_residual_nmm": moment_residual,
        })

    expected_pairs = {
        (scenario_id, case_id)
        for scenario_id in scenarios_by_id
        for case_id in cases_by_id
    }
    actual_pairs = {(row["scenario_id"], row["case_id"]) for row in output_rows}
    if actual_pairs != expected_pairs:
        raise ValueError("scenario/case combinations contain a duplicate or omission")
    output_rows.sort(key=lambda row: (row["scenario_id"], row["case_id"]))
    if not all(row["normal_resultant_inside_modeled_support_hull"] for row in output_rows):
        raise ValueError("at least one recorded global normal resultant lies outside the support hull")

    worst = min(output_rows, key=lambda row: row["minimum_support_hull_edge_margin_mm"])
    best = max(output_rows, key=lambda row: row["minimum_support_hull_edge_margin_mm"])
    by_case = {}
    for case_id in sorted(cases_by_id):
        rows = [row for row in output_rows if row["case_id"] == case_id]
        case_worst = min(rows, key=lambda row: row["minimum_support_hull_edge_margin_mm"])
        by_case[case_id] = {
            "scenario_count": len(rows),
            "minimum_support_hull_edge_margin_mm": case_worst["minimum_support_hull_edge_margin_mm"],
            "governing_scenario_id": case_worst["scenario_id"],
            "governing_cop_xy_mm": case_worst["required_floor_normal_center_of_pressure_xy_mm"],
            "required_normal_resultant_n": case_worst["required_floor_normal_resultant_n"],
            "required_tangent_resultant_global_xy_n": case_worst["required_floor_tangent_resultant_global_xy_n"],
            "required_yaw_reaction_nmm": case_worst["required_floor_yaw_reaction_nmm"],
        }

    return {
        "schema": "wood_joint_accessory_global_support_resultant/v1",
        "candidate": loads["candidate"],
        "geometry_revision_id": revision,
        "status": "PASS_RECORDED_GLOBAL_NORMAL_RESULTANTS_WITHIN_HULL_ONLY",
        "source_sha256": pins,
        "units": {"force": "N", "moment": "N*mm", "center": "mm"},
        "inputs": {
            "modeled_mass_rows": base_gravity["row_count"],
            "modeled_mass_kg": base_gravity["modeled_mass_kg"],
            "additional_accessory_budget_kg": dead["accessory_allowance"]["budget_kg"],
            "accessory_scenario_count": len(scenarios),
            "applied_case_count": len(cases_by_id),
            "support_hull_vertices_xy_mm": hull,
            "support_hull_area_mm2": abs(polygon_signed_area(hull)),
            "accessory_scenario_interpretation": "source-defined analytical placement scenarios, not observed mass splits or installation"
        },
        "result_summary": {
            "scenario_case_count": len(output_rows),
            "all_required_normal_resultants_inside_hull": True,
            "minimum_edge_margin_mm": worst["minimum_support_hull_edge_margin_mm"],
            "governing_scenario_id": worst["scenario_id"],
            "governing_case_id": worst["case_id"],
            "governing_cop_xy_mm": worst["required_floor_normal_center_of_pressure_xy_mm"],
            "maximum_edge_margin_mm": best["minimum_support_hull_edge_margin_mm"],
            "maximum_margin_scenario_id": best["scenario_id"],
            "maximum_margin_case_id": best["case_id"],
            "maximum_force_reconstruction_residual_n": max_force_closure,
            "maximum_moment_reconstruction_residual_nmm": max_moment_closure,
            "by_case": by_case,
        },
        "scenario_case_results": output_rows,
        "readiness": {
            "mechanical_acceptance": False,
            "floor_support_gate_closed": False,
            "member_or_joint_demand_accepted": False,
            "native_solve_run": False,
        },
        "limits": [
            "This is a necessary whole-assembly static normal-resultant/support-hull check, not a solved frame response.",
            "The floor hull comes from the source-bound eight-member STEP floor-face screen; intact internal load transfer is assumed, not demonstrated.",
            "The 224.4208 kg modeled mass uses source CAD and conditional density assumptions; the additional 25 kg is represented only by the nine pinned scenarios.",
            "All accessory placements use the source scenario's zero outward hold-CG offset; these are not measured masses or a guaranteed installation envelope.",
            "Center of pressure inside the hull does not establish compatible individual support reactions, local uplift, bearing pressure, sliding resistance, friction coefficient, yaw capacity, floor quality, or anchorage.",
            "Required tangential resultants and yaw reactions are reported as equilibrium demands only; no resistance is assigned.",
            "The record supplies no member or joint actions, code/product check, design acceptance, or release."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="reconstruct and compare without writing")
    mode.add_argument("--write", action="store_true", help="write after all frozen source checks pass")
    args = parser.parse_args()

    pins = check_pins()
    loads = json.loads((ROOT / LOADS_REL).read_text())
    dead = json.loads((ROOT / ACCESSORY_REL).read_text())
    hull_data = json.loads((ROOT / HULL_REL).read_text())
    record = build_record(loads, dead, hull_data, pins)
    path = HERE / "accessory-support-resultant.json"
    rendered = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.write:
        path.write_text(rendered)
        print(f"wrote {path.relative_to(ROOT)}")
        return
    if not path.exists():
        raise SystemExit(f"missing {path}; rerun with --write after checking source pins")
    if path.read_text() != rendered:
        raise SystemExit("verification failed: reconstructed record differs from saved output")
    result = record["result_summary"]
    print(
        "PASS: 54 frozen load/accessory resultants reconstruct; all normal CoPs are in the modeled hull; "
        f"minimum margin={result['minimum_edge_margin_mm']:.6f} mm"
    )


if __name__ == "__main__":
    main()
