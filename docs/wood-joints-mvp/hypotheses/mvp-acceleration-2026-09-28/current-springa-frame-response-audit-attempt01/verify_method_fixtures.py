"""Read-only replay of the already-passed SPRINGA and exact-floor coupons."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("response_audit", HERE / "response_audit.py")
assert spec and spec.loader
response_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(response_audit)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fixture(name: str, assessment_status: str, parent_status: str,
            parent_count_key: str, expected_count: int) -> tuple[Path, dict[str, Any], dict[float, dict[str, Any]]]:
    directory = SERIES / name
    assessment = read_json(directory / "assessment.json")
    parent_name = "parent-check.json" if name.endswith("relative-coordinate-fixture-attempt01") else "parent-all-increment-check.json"
    parent = read_json(directory / parent_name)
    execution = read_json(directory / "native/execution.json")
    dat = (directory / "native/model.dat").read_text()
    data_sha = hashlib.sha256(dat.encode("utf-8")).hexdigest()
    require(assessment.get("status") == assessment_status, f"{name}: native assessment did not pass")
    require(assessment.get("method_fixture_passed") is True, f"{name}: fixture pass flag is absent")
    require(parent.get("status") == parent_status, f"{name}: independent all-increment check did not pass")
    require(parent.get(parent_count_key) == expected_count, f"{name}: unexpected independent increment count")
    require(execution.get("returncode") == 0 and execution.get("native_solve_executed") is True,
            f"{name}: pinned native execution record is not a completed successful run")
    for filename in ("model.json", "model.inp", "model.dat"):
        recorded_sha = execution.get("outputs_sha256", {}).get(filename)
        observed_sha = hashlib.sha256((directory / "native" / filename).read_bytes()).hexdigest()
        if filename != "model.dat":
            packet_sha = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
            require(recorded_sha == observed_sha == packet_sha,
                    f"{name}: native frozen {filename} does not match its packet and execution record")
        else:
            require(recorded_sha == observed_sha,
                    f"{name}: native DAT differs from its execution record")
    require(parent.get("model_dat_sha256") == data_sha, f"{name}: parent check is not bound to its native DAT")
    if assessment.get("model_dat_sha256") is not None:
        require(assessment["model_dat_sha256"] == data_sha, f"{name}: native assessment DAT hash changed")
    blocks = response_audit.parse_native_blocks(dat)
    require(len(blocks) == expected_count, f"{name}: unexpected native U/RF state count")
    return directory, parent, blocks


def relative_springa_check() -> dict[str, Any]:
    name = "current-springa-relative-coordinate-fixture-attempt01"
    directory, parent, states = fixture(
        name,
        "PASS_NATIVE_TWO_BODY_RELATIVE_SPRINGA_MPC_FIXTURE",
        "PASS_PARENT_ALL_INCREMENT_CLOSED_FORM_AND_PHYSICAL_BALANCE",
        "increment_count",
        18,
    )
    model = read_json(directory / "model.json")
    binding = {
        "group": "relative-known-answer",
        "source_row_id": "relative-known-answer",
        "source_inventory_row_index": 0,
        "source_element": 3,
        "springa_nodes": [9, 10],
        "source_projection_nodes": [1, 2],
        "source_projection_dof": 1,
        "numerical_axis_global_xyz": [1.0, 0.0, 0.0],
        "initial_span_mm": 100.0,
        "stiffness_n_per_mm": 50.0,
        "table_domain_mm": [-10.0, 10.0],
        "physical_action_on_first_body": {
            "sign": 1,
            "unit_direction_global_xyz": [1.0, 0.0, 0.0],
        },
    }
    source = {"intended_law": "compression_only"}
    nodes = {int(node): np.asarray(point, dtype=float) for node, point in model["nodes"].items()}
    supports = model["springs"]
    maximum = {"q_mm": 0.0, "springa_force_N": 0.0, "body_balance_N": 0.0,
               "mpc_interval_distance_mm": 0.0, "known_u_mm": 0.0}
    numerical_ground_rf_max_abs_N = 0.0

    for time, state in states.items():
        mpc = response_audit._audit_all_mpcs(model["equations"], state)
        require(mpc["passed"], f"relative SPRINGA coupon MPC check failed at t={time}")
        maximum["mpc_interval_distance_mm"] = max(
            maximum["mpc_interval_distance_mm"], mpc["maximum_interval_distance_from_zero_mm"]
        )
        if time <= 1.0:
            load_a = -30.0 * time
        elif time <= 2.0:
            load_a = -30.0 + 60.0 * (time - 1.0)
        else:
            load_a = 30.0 - 60.0 * (time - 2.0)
        load_b = -load_a
        if load_a < 0.0:
            joint = -3.0 * load_a / 7.0
            expected_a = (load_a + joint) / 100.0
            expected_b = (load_b - joint) / 200.0
        elif load_a > 0.0:
            joint = 0.0
            expected_a = load_a / 100.0
            expected_b = load_b / 200.0
        else:
            joint = expected_a = expected_b = 0.0

        internal, _, nonlinear = response_audit._audit_springa(binding, source, state, nodes)
        maximum["q_mm"] = max(maximum["q_mm"], abs(nonlinear["q_relative_projection_mm"]
                                                 - (expected_b - expected_a)))
        maximum["springa_force_N"] = max(maximum["springa_force_N"], abs(internal - joint))
        maximum["known_u_mm"] = max(maximum["known_u_mm"],
                                    abs(state["u"][1][0] - expected_a),
                                    abs(state["u"][2][0] - expected_b))

        support_actions = []
        for spring in supports:
            action, _, checked = response_audit._audit_linear_spring(spring, state)
            require(checked["rf_action_reaction_passed"] and checked["rf_kdu_intervals_intersect"],
                    f"relative support law check failed at t={time}")
            support_actions.append(action)
        residual_a = load_a + support_actions[0] + internal
        residual_b = load_b + support_actions[1] - internal
        maximum["body_balance_N"] = max(maximum["body_balance_N"], abs(residual_a), abs(residual_b))
        require(abs(residual_a) < 2.0e-3 and abs(residual_b) < 2.0e-3,
                f"relative physical body balance failed at t={time}")
        numerical_ground_rf_max_abs_N = max(numerical_ground_rf_max_abs_N,
                                            abs(state["rf"][10][0]))
        require(nonlinear["numerical_ground_rf_excluded_from_physical_balance"],
                "relative ground reaction was not identified as numerical")

    require(maximum["body_balance_N"] < 2.0e-3, "relative body balance tolerance exceeded")
    require(numerical_ground_rf_max_abs_N > 1.0, "fixture did not exercise a nonzero numerical-ground RF")
    require(maximum["known_u_mm"] < 2.0e-6, "relative displacement known answer exceeded output tolerance")
    require(maximum["springa_force_N"] < 2.0e-3, "relative nonlinear force known answer exceeded output tolerance")
    return {
        "fixture": name,
        "native_dat_sha256": parent["model_dat_sha256"],
        "increment_count": len(states),
        "recovery_functions_exercised": ["_audit_springa", "_audit_linear_spring", "_audit_all_mpcs"],
        "maximum_errors": maximum,
        "numerical_ground_rf_max_abs_N_excluded": numerical_ground_rf_max_abs_N,
        "passed": True,
        "applies_to": "Scalar two-body coupling sign/law and physical action transfer only.",
    }


def interpolated_loads(model: dict[str, Any], time: float) -> dict[tuple[int, int], float]:
    previous_time = 0.0
    previous: dict[tuple[int, int], float] = {}
    for step in model["loads_by_step"]:
        current = {(int(row["node"]), int(row["dof"])): float(row["force_N"])
                   for row in step["loads"]}
        if time <= float(step["time"]):
            alpha = (time - previous_time) / (float(step["time"]) - previous_time)
            keys = set(previous) | set(current)
            return {key: previous.get(key, 0.0) + alpha * (current.get(key, 0.0) - previous.get(key, 0.0))
                    for key in keys}
        previous_time = float(step["time"])
        previous = current
    raise AssertionError(f"Native time {time} exceeds the fixture load history")


def exact_floor_mpc_check() -> dict[str, Any]:
    name = "current-exact-floor-mpc-fixture-attempt02"
    directory, parent, states = fixture(
        name,
        "PASS_NATIVE_EXACT_FLOOR_MPC_REACTION_KNOWN_ANSWER",
        "PASS_PARENT_ALL_PRINTED_INCREMENT_CHECK",
        "printed_increment_count",
        12,
    )
    model = read_json(directory / "model.json")
    equation = model["equations"][0]
    pivot = (int(equation[0][0]), int(equation[0][1]))
    reference = int(model["ground_reference_node"])
    coefficient = sum(float(term[2]) for term in equation
                      if int(term[0]) == reference and int(term[1]) == 1)
    require(abs(float(equation[0][2]) - 1.0) < 1.0e-13 and coefficient == -1.0,
            "exact-floor fixture does not encode its documented pivot/reference row")
    maximum = {"reaction_N": 0.0, "body_balance_N": 0.0, "mpc_interval_distance_mm": 0.0,
               "springa_force_N": 0.0}
    numerical_ground_rf_max_abs_N = 0.0
    nodes = {int(node): np.asarray(point, dtype=float) for node, point in model["nodes"].items()}
    normal = model["normal_law"]
    binding = {
        "group": "exact-floor-normal",
        "source_row_id": "exact-floor-normal",
        "source_inventory_row_index": 0,
        "source_element": int(normal["element"]),
        "springa_nodes": [int(normal["endpoint"]), int(normal["ground"])],
        "source_projection_nodes": [int(model["physical_node"]), int(normal["ground"])],
        "source_projection_dof": 3,
        "numerical_axis_global_xyz": [0.0, 0.0, 1.0],
        "initial_span_mm": float(normal["initial_span_mm"]),
        "stiffness_n_per_mm": 100.0,
        "table_domain_mm": [-10.0, 10.0],
        "physical_action_on_first_body": {
            "sign": 1,
            "unit_direction_global_xyz": [0.0, 0.0, 1.0],
        },
    }
    for time, state in states.items():
        mpc = response_audit._audit_all_mpcs(model["equations"], state)
        require(mpc["passed"], f"exact-floor MPC check failed at t={time}")
        maximum["mpc_interval_distance_mm"] = max(
            maximum["mpc_interval_distance_mm"], mpc["maximum_interval_distance_from_zero_mm"]
        )
        load = interpolated_loads(model, time)
        pivot_load = load.get(pivot, 0.0)
        correction = -coefficient * pivot_load
        recovered = state["rf"][reference][0] - correction
        expected = -6.5 * time if time <= 1.0 else -6.5 + 9.5 * (time - 1.0)
        maximum["reaction_N"] = max(maximum["reaction_N"], abs(recovered - expected))
        require(abs(recovered - expected) < 2.0e-3, f"exact-floor transferred reaction failed at t={time}")

        internal_normal, _, normal_check = response_audit._audit_springa(
            binding, {"intended_law": "compression_only"}, state, nodes
        )
        maximum["springa_force_N"] = max(
            maximum["springa_force_N"],
            abs(internal_normal - 10.0 * time) if time <= 1.0 else abs(internal_normal - (10.0 + 10.0 * (time - 1.0))),
        )
        xz, _, _ = response_audit._audit_linear_spring(model["springs"][0], state)
        vertical, _, _ = response_audit._audit_linear_spring(model["springs"][1], state)
        load_x, load_z = load.get((int(model["physical_node"]), 1), 0.0), load.get((int(model["physical_node"]), 3), 0.0)
        residual_x = load_x + recovered + xz
        residual_z = load_z + 0.25 * xz + vertical + internal_normal
        maximum["body_balance_N"] = max(maximum["body_balance_N"], abs(residual_x), abs(residual_z))
        require(max(abs(residual_x), abs(residual_z)) < 2.0e-3,
                f"exact-floor physical body balance failed at t={time}")
        numerical_ground_rf_max_abs_N = max(numerical_ground_rf_max_abs_N,
                                            abs(state["rf"][int(normal["ground"])][2]))
        require(normal_check["numerical_ground_rf_excluded_from_physical_balance"],
                "exact-floor numerical normal ground was counted as physical floor support")

    require(parent.get("reaction_rule") == "RF_REFERENCE_MINUS_DEPENDENT_CLOAD",
            "exact-floor fixture parent check reports another reaction convention")
    require(maximum["reaction_N"] < 2.0e-3 and maximum["body_balance_N"] < 2.0e-3,
            "exact-floor reaction or body-balance tolerance exceeded")
    return {
        "fixture": name,
        "native_dat_sha256": parent["model_dat_sha256"],
        "increment_count": len(states),
        "formula_replayed": "R_floor=RF(reference,1)-(-E_ref_coefficient)*F_pivot",
        "recovery_functions_exercised": ["_audit_springa", "_audit_linear_spring", "_audit_all_mpcs"],
        "maximum_errors": maximum,
        "numerical_normal_ground_rf_max_abs_N_excluded": numerical_ground_rf_max_abs_N,
        "passed": True,
        "applies_to": "Single transformed row, load correction, SPRINGA normal endpoint, and body closure only.",
    }


def transformed_floor_check() -> dict[str, Any]:
    name = "current-transformed-floor-reaction-fixture-attempt01"
    directory, parent, states = fixture(
        name,
        "PASS_NATIVE_TRANSFORMED_FLOOR_REACTION_KNOWN_ANSWER",
        "PASS_PARENT_ALL_PRINTED_TRANSFORMED_REACTION_INCREMENTS",
        "printed_increment_count",
        12,
    )
    model = read_json(directory / "model.json")
    transform = model["source_reaction_transform"]
    equations = model["transformed_floor_equations"]
    references = list(map(int, model["reference_nodes_by_original_source_row"]))
    pivot_nodes = [int(model["physical_nodes_by_body"][body])
                   for body in transform["pivot_physical_node_order"]]
    source_matrix = np.asarray(transform["source_matrix"], dtype=float)
    selected_rows = list(map(int, transform["selected_source_rows_zero_based"]))
    parent_by_time = {float(row["time"]): row for row in parent["records"]}
    require(selected_rows == [1, 0] and transform["pivot_physical_node_order"] == ["B", "A"],
            "transformed fixture no longer exercises a row and pivot permutation")
    maximum = {"reaction_N": 0.0, "physical_force_resultant_N": 0.0,
               "physical_moment_resultant_Nmm": 0.0, "body_balance_N": 0.0,
               "mpc_interval_distance_mm": 0.0, "springa_force_N": 0.0}
    actual_endpoint_ground_max = 0.0
    for time, state in states.items():
        mpc = response_audit._audit_all_mpcs(model["equations"], state)
        require(mpc["passed"], f"transformed floor MPC check failed at t={time}")
        maximum["mpc_interval_distance_mm"] = max(
            maximum["mpc_interval_distance_mm"], mpc["maximum_interval_distance_from_zero_mm"]
        )
        load = interpolated_loads(model, time)
        pivot_force = np.asarray([load.get((node, 1), 0.0) for node in pivot_nodes], dtype=float)
        correction_selected = np.zeros(2)
        for reference_column, original_index in enumerate(selected_rows):
            reference_node = references[original_index]
            for equation_index, terms in enumerate(equations):
                coefficient = sum(float(term[2]) for term in terms
                                  if int(term[0]) == reference_node and int(term[1]) == 1)
                correction_selected[reference_column] -= coefficient * pivot_force[equation_index]
        correction_original = np.zeros(2)
        for selected_index, original_index in enumerate(selected_rows):
            correction_original[original_index] = correction_selected[selected_index]
        raw = np.asarray([state["rf"][node][0] for node in references], dtype=float)
        source_reaction = raw - correction_original
        physical_support = source_matrix.T @ source_reaction

        # Independently reproduce the two-body linear/normal support solution
        # for this printed state and check both bodies, not only the source sum.
        applied: dict[str, dict[int, float]] = {"A": {}, "B": {}}
        for body, node in model["physical_nodes_by_body"].items():
            for dof in (1, 3):
                applied[body][dof] = load.get((int(node), dof), 0.0)
        body_residuals = []
        for index, body in enumerate(("A", "B")):
            physical_node = int(model["physical_nodes_by_body"][body])
            xz_spring, vertical_spring = [s for s in model["structural_springs"]
                                          if s["physical_body"] == body]
            xz_native = next(s for s in model["springs"] if s["name"] == xz_spring["name"])
            vertical_native = next(s for s in model["springs"] if s["name"] == vertical_spring["name"])
            xz_value, _, _ = response_audit._audit_linear_spring({
                "name": xz_spring["name"], "group": xz_spring["name"],
                "element": xz_native["element"],
                "nodes": [xz_spring["endpoint"], xz_spring["ground"]], "dof": xz_spring["dof"],
                "stiffness_n_per_mm": xz_spring["stiffness_N_per_mm"],
            }, state)
            vertical_value, _, _ = response_audit._audit_linear_spring({
                "name": vertical_spring["name"], "group": vertical_spring["name"],
                "element": vertical_native["element"],
                "nodes": [vertical_spring["endpoint"], vertical_spring["ground"]],
                "dof": vertical_spring["dof"], "stiffness_n_per_mm": vertical_spring["stiffness_N_per_mm"],
            }, state)
            normal_desc = next(item for item in model["normal_springs"] if item["physical_body"] == body)
            binding = {
                "group": normal_desc["name"], "source_row_id": normal_desc["name"],
                "source_inventory_row_index": index, "source_element": normal_desc["element"],
                "springa_nodes": [normal_desc["endpoint"], normal_desc["ground"]],
                "source_projection_nodes": [physical_node, normal_desc["ground"]],
                "source_projection_dof": 3, "numerical_axis_global_xyz": [0.0, 0.0, 1.0],
                "initial_span_mm": normal_desc["initial_span_mm"],
                "stiffness_n_per_mm": 100.0, "table_domain_mm": [-10.0, 10.0],
                "physical_action_on_first_body": {
                    "sign": 1, "unit_direction_global_xyz": [0.0, 0.0, 1.0],
                },
            }
            internal_normal, _, normal_check = response_audit._audit_springa(
                binding, {"intended_law": "compression_only"}, state,
                {int(node): np.asarray(point, dtype=float) for node, point in model["nodes"].items()},
            )
            maximum["springa_force_N"] = max(
                maximum["springa_force_N"],
                abs(internal_normal - (-100.0 * state["u"][physical_node][2])),
            )
            action_xz = np.asarray([xz_value, 0.0, 0.25 * xz_value])
            action_vertical = np.asarray([0.0, 0.0, vertical_value])
            action_normal = np.asarray([0.0, 0.0, internal_normal])
            applied_xyz = np.asarray([applied[body].get(1, 0.0), 0.0, applied[body].get(3, 0.0)])
            floor_xyz = np.asarray([physical_support[index], 0.0, 0.0])
            residual = applied_xyz + floor_xyz + action_xz + action_vertical + action_normal
            body_residuals.append(residual)
            maximum["body_balance_N"] = max(maximum["body_balance_N"], float(np.max(np.abs(residual))))
            actual_endpoint_ground_max = max(actual_endpoint_ground_max,
                                             abs(normal_check["native_ground_rf_projected_N"]))
            require(normal_check["numerical_ground_rf_excluded_from_physical_balance"],
                    "transformed floor-normal numerical ground was counted")

        source_force = float(np.sum(source_reaction))
        physical_force = float(np.sum(physical_support))
        source_moment = -25.0 * source_reaction[0] - 75.0 * source_reaction[1]
        physical_moment = -100.0 * physical_support[1]
        expected_source_reaction = np.asarray(parent_by_time[time]["source_reactions_N"], dtype=float)
        maximum["reaction_N"] = max(maximum["reaction_N"],
                                    float(np.max(np.abs(source_reaction - expected_source_reaction))))
        maximum["physical_force_resultant_N"] = max(maximum["physical_force_resultant_N"],
                                                    abs(source_force - physical_force))
        maximum["physical_moment_resultant_Nmm"] = max(maximum["physical_moment_resultant_Nmm"],
                                                       abs(source_moment - physical_moment))
        require(maximum["body_balance_N"] < 2.0e-3, f"transformed body balance failed at t={time}")

    require(actual_endpoint_ground_max > 1.0, "transformed fixture did not exercise numerical ground exclusion")
    require(maximum["reaction_N"] < 2.0e-3, "transformed source-reaction known answers differ")
    require(maximum["physical_force_resultant_N"] < 2.0e-3,
            "transformed source/physical support force resultants differ")
    require(maximum["physical_moment_resultant_Nmm"] < 2.0e-2,
            "transformed source/physical support moments differ")
    require(maximum["body_balance_N"] < 2.0e-3,
            "transformed physical body equilibrium tolerance exceeded")
    return {
        "fixture": name,
        "native_dat_sha256": parent["model_dat_sha256"],
        "increment_count": len(states),
        "formula_replayed": "R_source=RF(reference)-map((S_inverse)^T*F_pivot) in original source-row order; f_physical=A^T*R_source",
        "recovery_functions_exercised": ["_audit_springa", "_audit_linear_spring", "_audit_all_mpcs"],
        "maximum_errors": maximum,
        "nonzero_numerical_ground_rf_max_abs_N_excluded": actual_endpoint_ground_max,
        "passed": True,
        "applies_to": "Two-body nonidentity/permuted exact-floor reaction transform and source/physical wrench preservation only.",
    }


def small_endpoint_length_roundoff_check() -> dict[str, Any]:
    """Verify the arithmetic guard covers a near-zero elongation diagnostic."""
    span = 100.0
    q = 1.0e-12
    stiffness = 4_754_107.216016417
    geometric = float(np.linalg.norm(np.asarray([span + q, 0.0, 0.0])) - span)
    force_delta = abs(stiffness * max(geometric, 0.0) - stiffness * max(q, 0.0))
    geometric_roundoff_guard = 16.0 * np.finfo(float).eps * span
    force_roundoff_guard = stiffness * geometric_roundoff_guard
    require(abs(geometric - q) <= geometric_roundoff_guard,
            "endpoint-length arithmetic guard does not cover a 1e-12 mm extension")
    require(force_delta <= force_roundoff_guard,
            "k times endpoint-length arithmetic guard does not cover the near-zero law difference")
    return {
        "nominal_span_mm": span,
        "projected_q_mm": q,
        "computed_norm_dd_minus_dd0_mm": geometric,
        "projected_vs_geometric_force_difference_N": force_delta,
        "endpoint_length_arithmetic_guard_mm": geometric_roundoff_guard,
        "k_times_endpoint_length_arithmetic_guard_N": force_roundoff_guard,
        "passed": True,
    }


def main() -> None:
    results = [relative_springa_check(), exact_floor_mpc_check(), transformed_floor_check()]
    output = {
        "schema": "current_springa_method_fixture_replay/v1",
        "status": "PASS_READ_ONLY_METHOD_FIXTURE_REPLAYS",
        "native_solver_launched": False,
        "fixture_count": len(results),
        "fixtures": results,
        "near_zero_endpoint_length_roundoff_check": small_endpoint_length_roundoff_check(),
        "limits": [
            "Existing method coupons only; no current frame result, corner demand, connection acceptance, or design qualification.",
            "Replay proves the exercised scalar/matrix reaction maps and sign conventions for these fixtures, not other geometries or floor states.",
            "Frame auditing still requires parent-owned frozen model/deck and native output, then independent parent review.",
        ],
    }
    (HERE / "method_fixture_check.json").write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(output["status"], output["fixture_count"])


if __name__ == "__main__":
    main()
