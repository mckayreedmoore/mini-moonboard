#!/usr/bin/env python3
"""Bound vertical reactions on the eight modeled floor faces by statics alone."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
HERE = Path(__file__).resolve().parent
GLOBAL_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/global-equilibrium.json"
ACCESSORY_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/accessory-support-resultant-attempt01/accessory-support-resultant.json"
OUTPUT_PATH = HERE / "normal-foot-reaction-bounds.json"
PINNED = {
    "AGENTS.md": (Path("AGENTS.md"), "672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536"),
    "global-equilibrium.json": (
        Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/global-equilibrium.json"),
        "4fe8652f4296827ed8bf06b376cee22194027d24eb64a73a17afa87679ffb381",
    ),
    "accessory-support-resultant.json": (
        Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/accessory-support-resultant-attempt01/accessory-support-resultant.json"),
        "adc1507a5540c54a701f95b7291b0e765819b502c39e33df164b3f805af5e76d",
    ),
}
SCALE_MM = 1000.0
WEIGHT_TOL = 1e-9
COP_TOL_MM = 1e-5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_3x3(matrix: list[list[float]], rhs: list[float]) -> list[float] | None:
    """Solve a 3x3 system, returning None for a singular basis."""
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs, strict=True)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-14:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                augmented[row][index] - factor * augmented[column][index]
                for index in range(4)
            ]
    return [augmented[row][3] for row in range(3)]


def vertices_for(footprints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vertices: list[dict[str, Any]] = []
    for footprint in footprints:
        member_id = footprint["member_id"]
        points = footprint["floor_face_vertices_xy_mm"]
        if len(points) < 3:
            raise ValueError(f"{member_id}: at least three face vertices are required")
        for index, point in enumerate(points):
            if len(point) != 2 or not all(math.isfinite(float(value)) for value in point):
                raise ValueError(f"{member_id}: invalid floor vertex")
            vertices.append({"member_id": member_id, "vertex_index": index, "xy_mm": point})
    return vertices


def statically_admissible_extremes(
    vertices: list[dict[str, Any]],
    member_ids: list[str],
    cop_xy_mm: list[float],
    normal_force_n: float,
) -> tuple[list[dict[str, Any]], int, float]:
    """Enumerate basic feasible reaction distributions over support-face vertices.

    For vertical compression-only reactions, each face's resultant may be any
    point in its polygon. The global feasible set is represented by nonnegative
    vertex weights whose sum is one and whose weighted position is the required
    CoP. A basic feasible solution has at most three nonzero weights.
    """
    if normal_force_n <= 0 or not math.isfinite(normal_force_n):
        raise ValueError("the total vertical support resultant must be positive")
    cop_x, cop_y = map(float, cop_xy_mm)
    points = [tuple(map(float, vertex["xy_mm"])) for vertex in vertices]
    member_index = {member_id: index for index, member_id in enumerate(member_ids)}
    extrema: list[dict[str, Any] | None] = [None] * len(member_ids)
    feasible_basis_count = 0
    maximum_cop_residual = 0.0

    for basis in itertools.combinations(range(len(vertices)), 3):
        matrix = [
            [1.0, 1.0, 1.0],
            [(points[index][0] - cop_x) / SCALE_MM for index in basis],
            [(points[index][1] - cop_y) / SCALE_MM for index in basis],
        ]
        weights = solve_3x3(matrix, [1.0, 0.0, 0.0])
        if weights is None or any(weight < -WEIGHT_TOL for weight in weights):
            continue
        clean = [max(0.0, weight) for weight in weights]
        total = sum(clean)
        if total <= 0:
            continue
        clean = [weight / total for weight in clean]
        residual_x = sum(weight * points[index][0] for weight, index in zip(clean, basis, strict=True)) - cop_x
        residual_y = sum(weight * points[index][1] for weight, index in zip(clean, basis, strict=True)) - cop_y
        cop_residual = max(abs(residual_x), abs(residual_y))
        if cop_residual > COP_TOL_MM:
            continue

        feasible_basis_count += 1
        maximum_cop_residual = max(maximum_cop_residual, cop_residual)
        fractions = [0.0] * len(member_ids)
        for weight, vertex_index in zip(clean, basis, strict=True):
            fractions[member_index[vertices[vertex_index]["member_id"]]] += weight
        reactions = [normal_force_n * fraction for fraction in fractions]
        witness = {
            "support_reactions_n": {
                member_id: reactions[index] for index, member_id in enumerate(member_ids)
            },
            "force_residual_n": sum(reactions) - normal_force_n,
            "cop_residual_xy_mm": [residual_x, residual_y],
            "active_vertex_weights": [
                {
                    "member_id": vertices[index]["member_id"],
                    "vertex_index": vertices[index]["vertex_index"],
                    "xy_mm": points[index],
                    "weight_fraction": weight,
                }
                for weight, index in zip(clean, basis, strict=True)
                if weight > WEIGHT_TOL
            ],
        }
        for index, member_id in enumerate(member_ids):
            current = extrema[index]
            candidate = {"fraction": fractions[index], "witness": witness}
            if current is None:
                extrema[index] = {"minimum": candidate, "maximum": candidate}
            else:
                if fractions[index] < current["minimum"]["fraction"]:
                    current["minimum"] = candidate
                if fractions[index] > current["maximum"]["fraction"]:
                    current["maximum"] = candidate

    if feasible_basis_count == 0 or any(item is None for item in extrema):
        raise ValueError("no nonnegative normal-reaction distribution satisfies global equilibrium")

    result = []
    for member_id, item in zip(member_ids, extrema, strict=True):
        assert item is not None
        low = item["minimum"]
        high = item["maximum"]
        result.append(
            {
                "member_id": member_id,
                "minimum_reaction_n": normal_force_n * low["fraction"],
                "maximum_reaction_n": normal_force_n * high["fraction"],
                "minimum_reaction_fraction": low["fraction"],
                "maximum_reaction_fraction": high["fraction"],
                "minimum_witness": low["witness"],
                "maximum_witness": high["witness"],
            }
        )
    return result, feasible_basis_count, maximum_cop_residual


def verify_embedded_sources(record: dict[str, Any], label: str) -> dict[str, str]:
    hashes = record.get("source_sha256")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError(f"{label}: missing source_sha256 map")
    verified = {}
    for name, expected in hashes.items():
        path = ROOT / name
        if not path.is_file():
            raise ValueError(f"{label}: missing pinned source {name}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"{label}: source hash changed for {name}: {actual} != {expected}")
        verified[name] = actual
    return verified


def regression_checks() -> None:
    # Four point supports at the corners of a unit square. At its center,
    # every corner can carry zero and no corner can exceed half the total.
    square = [
        {"member_id": "p00", "vertex_index": 0, "xy_mm": [0.0, 0.0]},
        {"member_id": "p10", "vertex_index": 0, "xy_mm": [1.0, 0.0]},
        {"member_id": "p11", "vertex_index": 0, "xy_mm": [1.0, 1.0]},
        {"member_id": "p01", "vertex_index": 0, "xy_mm": [0.0, 1.0]},
    ]
    corner_ranges, _, _ = statically_admissible_extremes(square, ["p00", "p10", "p11", "p01"], [0.5, 0.5], 100.0)
    for row in corner_ranges:
        if abs(row["minimum_reaction_n"]) > 1e-9 or abs(row["maximum_reaction_n"] - 50.0) > 1e-9:
            raise ValueError("unit-square center known-answer reaction range failed")
    corner_load, _, _ = statically_admissible_extremes(square, ["p00", "p10", "p11", "p01"], [0.0, 0.0], 100.0)
    expected = {"p00": 100.0, "p10": 0.0, "p11": 0.0, "p01": 0.0}
    for row in corner_load:
        if abs(row["minimum_reaction_n"] - expected[row["member_id"]]) > 1e-9 or abs(row["maximum_reaction_n"] - expected[row["member_id"]]) > 1e-9:
            raise ValueError("unit-square corner known-answer reaction range failed")


def build_result(global_data: dict[str, Any], accessory_data: dict[str, Any], source_hashes: dict[str, str]) -> dict[str, Any]:
    if global_data["geometry_revision_id"] != accessory_data["geometry_revision_id"]:
        raise ValueError("floor footprint and wrench revisions do not match")
    if accessory_data.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("unexpected candidate")
    footprints = global_data["footprints"]
    member_ids = [footprint["member_id"] for footprint in footprints]
    if len(member_ids) != 8 or len(set(member_ids)) != 8:
        raise ValueError("expected eight unique modeled floor faces")
    vertices = vertices_for(footprints)
    rows = accessory_data["scenario_case_results"]
    if len(rows) != 54:
        raise ValueError(f"expected 54 case/scenario wrenches; found {len(rows)}")
    unique = set()
    scenarios = []
    max_force_residual = 0.0
    max_cop_residual = 0.0
    max_witness_cop_residual = 0.0
    min_reaction = math.inf
    max_reaction = -math.inf
    scenario_basis_counts = []

    for row in rows:
        key = (row["case_id"], row["scenario_id"])
        if key in unique:
            raise ValueError(f"duplicate case/scenario: {key}")
        unique.add(key)
        force = list(map(float, row["total_external_force_global_xyz_n"]))
        moment = list(map(float, row["total_external_moment_about_global_origin_nmm"]))
        normal = -force[2]
        if normal <= 0:
            raise ValueError(f"{key}: nonpositive normal resultant")
        cop_xy = [moment[1] / normal, -moment[0] / normal]
        for observed, expected in zip(cop_xy, row["required_floor_normal_center_of_pressure_xy_mm"], strict=True):
            if abs(observed - float(expected)) > COP_TOL_MM:
                raise ValueError(f"{key}: reconstructed CoP mismatch")
        if not row["normal_resultant_inside_modeled_support_hull"]:
            raise ValueError(f"{key}: prior gross-hull check is not feasible")

        reactions, basis_count, cop_residual = statically_admissible_extremes(vertices, member_ids, cop_xy, normal)
        scenario_basis_counts.append(basis_count)
        max_cop_residual = max(max_cop_residual, cop_residual)
        for support in reactions:
            for bound_name in ("minimum", "maximum"):
                witness = support[f"{bound_name}_witness"]
                max_force_residual = max(max_force_residual, abs(witness["force_residual_n"]))
                residual = max(abs(value) for value in witness["cop_residual_xy_mm"])
                max_witness_cop_residual = max(max_witness_cop_residual, residual)
            min_reaction = min(min_reaction, support["minimum_reaction_n"])
            max_reaction = max(max_reaction, support["maximum_reaction_n"])
        scenarios.append(
            {
                "case_id": row["case_id"],
                "scenario_id": row["scenario_id"],
                "required_normal_resultant_n": normal,
                "required_cop_xy_mm": cop_xy,
                "gross_hull_edge_margin_mm": row["minimum_support_hull_edge_margin_mm"],
                "support_reaction_bounds": reactions,
                "feasible_basic_distribution_count": basis_count,
                "maximum_extreme_witness_cop_residual_mm": cop_residual,
            }
        )

    if max_force_residual > 1e-8 or max_witness_cop_residual > COP_TOL_MM:
        raise ValueError("extreme witness equilibrium residual exceeds tolerance")
    return {
        "schema": "normal_foot_reaction_equilibrium_bounds/v1",
        "status": "PASS_GLOBAL_NORMAL_REACTION_ENVELOPES",
        "candidate": accessory_data["candidate"],
        "geometry_revision_id": global_data["geometry_revision_id"],
        "units": {"force": "N", "length": "mm", "pressure_if_derived": "N/mm^2"},
        "source_sha256": source_hashes,
        "model": {
            "support_faces": [
                {
                    "member_id": footprint["member_id"],
                    "area_mm2": footprint["planar_area_mm2"],
                    "vertices_xy_mm": footprint["floor_face_vertices_xy_mm"],
                }
                for footprint in footprints
            ],
            "normal_reaction_assumption": "Each of the eight modeled horizontal face polygons may carry an arbitrary nonnegative vertical resultant at any point in that polygon.",
            "method": "Enumerate basic feasible solutions of the convex equilibrium polytope; each solution uses at most three of the 32 pinned face vertices.",
            "horizontal_tangent_and_yaw": "Excluded from this vertical-reaction envelope; the separate support resultant screen records their required global resultants but no capacity or distribution.",
        },
        "result_summary": {
            "case_scenario_count": len(scenarios),
            "support_face_count": len(member_ids),
            "all_scenarios_have_nonnegative_equilibrium_distribution": True,
            "minimum_possible_individual_face_reaction_n": max(0.0, min_reaction),
            "maximum_possible_individual_face_reaction_n": max_reaction,
            "maximum_force_residual_n": max_force_residual,
            "maximum_witness_cop_residual_mm": max_witness_cop_residual,
            "minimum_feasible_basic_distributions_per_scenario": min(scenario_basis_counts),
            "maximum_feasible_basic_distributions_per_scenario": max(scenario_basis_counts),
            "floor_gate_status": "BLOCKED",
            "mechanical_acceptance": False,
            "native_solve_run": False,
        },
        "interpretation": [
            "These are outer statics-only bounds on vertical support resultants, conditional on all eight pinned faces being coplanar and eligible for nonnegative normal contact.",
            "Minimum and maximum for different supports are separate optimizations; do not combine endpoint values into a simultaneous reaction vector.",
            "A witness proves only whole-assembly vertical force and roll/pitch moment balance. It does not prove that the frame's stiffness or closed internal load paths realize that distribution.",
            "Reaction resultants are not local pressure fields. Dividing by face area would give only an area-average ratio, not a peak wood-bearing stress.",
            "The result does not determine individual-foot lift under actual frame stiffness, contact gaps or floor irregularity, horizontal/yaw reaction distribution, floor resistance, internal member/joint actions, or capacity.",
            "The 54 external wrenches retain the explicit accessory-placement scenarios and modeled gravity assumptions in the pinned input record; this is not an observed accessory layout or verified floor.",
        ],
        "scenario_results": scenarios,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write after all source pins and checks pass")
    mode.add_argument("--verify", action="store_true", help="recompute and compare without writing")
    args = parser.parse_args()
    regression_checks()

    source_hashes = {}
    for name, (relative, expected) in PINNED.items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise ValueError(f"pinned input changed: {name} {actual} != {expected}")
        source_hashes[str(relative)] = actual
    global_data = json.loads(GLOBAL_PATH.read_text())
    accessory_data = json.loads(ACCESSORY_PATH.read_text())
    source_hashes.update(verify_embedded_sources(global_data, "global-equilibrium.json"))
    source_hashes.update(verify_embedded_sources(accessory_data, "accessory-support-resultant.json"))
    result = build_result(global_data, accessory_data, source_hashes)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT_PATH.write_text(rendered)
        print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}")
        return
    if not OUTPUT_PATH.is_file():
        raise SystemExit("missing result; inspect pins then run with --write")
    if OUTPUT_PATH.read_text() != rendered:
        raise SystemExit("verification failed: recomputed result differs from saved record")
    summary = result["result_summary"]
    print(
        f"PASS: {summary['case_scenario_count']} scenarios have statically admissible nonnegative "
        f"vertical support distributions; each face range is an outer equilibrium bound, not an actual reaction"
    )


if __name__ == "__main__":
    main()
