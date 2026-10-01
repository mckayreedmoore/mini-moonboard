#!/usr/bin/env python3
"""Reproduce the bounded SPR489 qghost and floor-normal diagnosis."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
RUN = SERIES / "current-springa-selected-floor-k12-rear-attempt03"
HERE = Path(__file__).resolve().parent
AUDIT = SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
AUDIT_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
KERNEL = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
KERNEL_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
EXPECTED_RUN_HASHES = {
    "model.json": "9591669b74af719e72df2a681504cab4e283d693eaac5e42920558b30773168f",
    "model.inp": "6b630749e918189583147833e3ef94a1338dc5bb28f42171cefc05cb039695e9",
    "model.dat": "29ec3cca415ee8f1ddb6cccd07a70aade816fd4c71eca98a5944d441f6d42f7a",
    "execution.json": "805e2b43da0f612de7801eca6fa4e05c834e90d805ceb12c23a3cf03c72dae71",
    "case-context.json": "1a352178c8fe2ad64681d2f456d9fdf29e67b72d0a1cbce3aa3ed5df21259a93",
    "freeze.json": "f1d9245626d18007e68732fb79f1a0630adc292397d0ba2fd7c2ca17c48b1cfd",
    "parent-terminal-assessment.json": "c4962da39c6378cdbe9e11315017023e17d8a63a9996a4036d991fd7664aa896",
}
EXPECTED_GATE = "SPRINGA qghost displacement does not match its source projections: SPR489"
SCHEMA = "current_springa_selected_floor_qghost_diagnosis/v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def import_pinned(name: str, path: Path, expected: str):
    actual = sha(path)
    if actual != expected:
        raise RuntimeError(f"Pinned method source changed: {rel(path)} ({actual})")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import pinned method: {rel(path)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dat_u_tokens(data: str) -> dict[float, dict[int, list[str]]]:
    pattern = re.compile(
        r"^\s*displacements\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n",
        re.MULTILINE | re.IGNORECASE,
    )
    result: dict[float, dict[int, list[str]]] = {}
    for match in pattern.finditer(data):
        time = float(match.group(1).replace("D", "E").replace("d", "e"))
        rows: dict[int, list[str]] = {}
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                node = int(fields[0])
                if node in rows:
                    raise RuntimeError(f"Duplicate U token row at t={time}, node={node}")
                rows[node] = fields[1:]
            elif rows:
                break
        if not rows or time in result:
            raise RuntimeError(f"Malformed or duplicate DAT displacement block at t={time}")
        result[time] = rows
    return dict(sorted(result.items()))


def equation_row(equations: list[Any], dependent: tuple[int, int]) -> tuple[int, list[list[float]]]:
    rows = [(index, equation) for index, equation in enumerate(equations)
            if (int(equation[0][0]), int(equation[0][1])) == dependent]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one emitted equation with dependent DOF {dependent}, got {len(rows)}")
    return rows[0]


def equation_interval(audit: Any, equation: list[list[float]], state: dict[str, Any]) -> dict[str, Any]:
    residual = sum(float(coef) * state["u"][int(node)][int(dof) - 1]
                   for node, dof, coef in equation)
    radius = sum(abs(float(coef)) * state["u_radius"][int(node)][int(dof) - 1]
                 for node, dof, coef in equation)
    guard = 32.0 * sys.float_info.epsilon * max(1.0, abs(residual))
    return {
        "residual_mm": residual,
        "rounding_interval_radius_mm": radius,
        "arithmetic_guard_mm": guard,
        "interval_intersects_zero": abs(residual) <= radius + guard,
        "strict_interval_excess_mm": max(0.0, abs(residual) - radius - guard),
        "generic_mpc_distance_from_zero_mm": max(0.0, abs(residual) - radius),
        "generic_mpc_tolerance_pass": max(0.0, abs(residual) - radius) <= audit._stable.MPC_INTERVAL_TOL_MM,
    }


def main() -> None:
    for name, expected in EXPECTED_RUN_HASHES.items():
        path = RUN / name
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"Pinned attempt03 input changed: {name}")
    if (HERE / "diagnosis.json").exists() or (HERE / "source-pins.json").exists():
        raise RuntimeError("Refusing to overwrite an existing diagnostic packet")

    audit = import_pinned("pinned_springa_response_audit", AUDIT, AUDIT_SHA256)
    if sha(KERNEL) != KERNEL_SHA256:
        raise RuntimeError("Pinned stable response kernel changed")

    model = read_json(RUN / "model.json")
    deck = (RUN / "model.inp").read_text()
    data = (RUN / "model.dat").read_text(errors="replace")
    context = read_json(RUN / "case-context.json")
    assessment = read_json(RUN / "parent-terminal-assessment.json")
    if (assessment.get("status") != "REJECTED_PROPOSED_SELECTED_BEARING_RESPONSE_COMPATIBILITY"
            or assessment.get("strict_response_exception") != EXPECTED_GATE
            or assessment.get("native_returncode") != 0
            or assessment.get("container_confirmed_terminal") is not True):
        raise RuntimeError("Attempt03 parent terminal assessment does not match the assigned gate")

    contract = audit._validate_model(model, deck, context)
    states = audit.parse_native_blocks(data)
    tokens = dat_u_tokens(data)
    expected_times = [0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0]
    if list(states) != expected_times or list(tokens) != expected_times:
        raise RuntimeError("Attempt03 does not contain the pinned seven-state load history")
    expected_nodes = set(map(int, model["nodes"]))
    for time, state in states.items():
        if set(state["u"]) != expected_nodes or set(state["rf"]) != expected_nodes:
            raise RuntimeError(f"Incomplete U/RF node inventory at t={time}")
        if set(tokens[time]) != expected_nodes:
            raise RuntimeError(f"Incomplete raw U token inventory at t={time}")

    try:
        audit.audit_record(model, data, deck, context)
    except ValueError as exc:
        strict_replay = {"status": "REPRODUCED_REJECTION", "exception": str(exc)}
        if str(exc) != EXPECTED_GATE:
            raise RuntimeError(f"Pinned strict gate changed: {exc}") from exc
    else:
        raise RuntimeError("Pinned strict audit unexpectedly accepted attempt03")

    binding = next(row for row in contract["bindings"] if row["group"] == "SPR489")
    source = contract["source_by_group"]["SPR489"]
    if (binding["name"] != "contact_70_0"
            or binding["source_projection_nodes"] != [15670, 15671]
            or binding["springa_nodes"] != [19800, 19801]
            or source["physical_owner"]["first"] != "base_rail_service_lower_right"
            or source["physical_owner"]["second"] != "wj04_lower_full_stock_cleat"):
        raise RuntimeError("SPR489 ownership or node binding differs from the reported exception")

    equations = audit.parse_equation_cards(deck)
    equation_specs = {
        "source_projection_first": (15670, 1),
        "source_projection_second": (15671, 1),
        "qghost_fixed_x": (19800, 1),
        "qghost_y": (19800, 2),
        "qghost_z": (19800, 3),
    }
    mapped_equations = {key: equation_row(equations, dof) for key, dof in equation_specs.items()}
    axis = [float(value) for value in binding["numerical_axis_global_xyz"]]
    # The emitted *EQUATION coefficients are the numerical coefficients the
    # solver saw; compare them directly with the source-bound unit axis.
    emitted_y = -float(mapped_equations["qghost_y"][1][1][2])
    emitted_z = -float(mapped_equations["qghost_z"][1][1][2])
    coefficient_delta = [emitted_y - axis[1], emitted_z - axis[2]]

    qghost_states: list[dict[str, Any]] = []
    for time, state in states.items():
        p1, p2 = map(int, binding["source_projection_nodes"])
        dof = int(binding["source_projection_dof"]) - 1
        qnode, ground = map(int, binding["springa_nodes"])
        source_q = state["u"][p2][dof] - state["u"][p1][dof]
        source_radius = state["u_radius"][p2][dof] + state["u_radius"][p1][dof]
        q_vector = [state["u"][qnode][i] - state["u"][ground][i] for i in range(3)]
        q_vector_radius = [state["u_radius"][qnode][i] + state["u_radius"][ground][i]
                           for i in range(3)]
        qghost = sum(axis[i] * q_vector[i] for i in range(3))
        qghost_from_emitted_coefficients = emitted_y * q_vector[1] + emitted_z * q_vector[2]
        qghost_radius = sum(abs(axis[i]) * q_vector_radius[i] for i in range(3))
        gap = qghost - source_q
        gap_radius = qghost_radius + source_radius
        guard = 32.0 * sys.float_info.epsilon * max(1.0, abs(qghost), abs(source_q))
        equations_at_time = {}
        for key, (index, equation) in mapped_equations.items():
            equations_at_time[key] = {
                "equation_index_zero_based": index,
                "dependent_dof": list(equation_specs[key]),
                "emitted_terms": equation,
                **equation_interval(audit, equation, state),
            }
        residual_abs = abs(gap)
        q_tokens = {
            str(node): tokens[time][node]
            for node in (p1, p2, qnode, ground)
        }
        q_token_radii = {
            str(node): [audit._stable._u_token_radius(token) for token in tokens[time][node]]
            for node in (p1, p2, qnode, ground)
        }
        qghost_states.append({
            "load_factor": time,
            "raw_u_tokens_by_node": q_tokens,
            "u_token_radii_mm_by_node": q_token_radii,
            "source_q_mm": source_q,
            "source_q_radius_mm": source_radius,
            "qghost_relative_vector_mm": q_vector,
            "qghost_relative_vector_radius_mm": q_vector_radius,
            "qghost_projected_mm": qghost,
            "qghost_projected_with_emitted_deck_coefficients_mm": qghost_from_emitted_coefficients,
            "emitted_coefficient_projection_minus_source_q_mm": qghost_from_emitted_coefficients - source_q,
            "qghost_projected_radius_mm": qghost_radius,
            "qghost_minus_source_q_mm": gap,
            "combined_output_interval_radius_mm": gap_radius,
            "arithmetic_guard_mm": guard,
            "strict_qghost_interval_pass": residual_abs <= gap_radius + guard,
            "interval_excess_mm": max(0.0, residual_abs - gap_radius - guard),
            "emitted_equation_checks": equations_at_time,
            "generic_all_mpc_audit": audit.audit_all_mpcs(equations, state),
        })

    # The existing known branch classifier is applied independently to each
    # of the 100 source floor-normal laws at all seven recorded increments.
    # Numerical force checks are consumed only to classify the law; no force
    # values or balances are retained in this diagnostic.
    selected = set(map(str, model["floor_selected_bearing_cells"]))
    floor_bindings = [row for row in contract["bindings"]
                      if contract["source_by_group"][str(row["group"])].get("role") == "floor_normal"]
    if len(floor_bindings) != 100 or len(selected) != 23:
        raise RuntimeError("Attempt03 is not the pinned 23-selected/100-normal proposal")
    floor_states = []
    stable_positive_sets = []
    for time, state in states.items():
        rows = []
        for floor in floor_bindings:
            floor_source = contract["source_by_group"][str(floor["group"])]
            _force, _force_radius, check = audit.audit_springa(
                floor, floor_source, state, contract["emitted_nodes"]
            )
            selected_cell = str(floor["name"]) in selected
            try:
                branch_check = audit._strict_normal_branch_check(floor, check, state, contract, selected_cell)
                classification = "STRICTLY_POSITIVE" if selected_cell else "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"
                reason = "pinned selected/inactive normal-law interval test passed"
            except audit.ResponseAuditError as exc:
                branch_check = None
                classification = "INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"
                reason = str(exc)
            elongation = float(check["geometric_spring_elongation_mm"])
            q = float(check["q_relative_projection_mm"])
            q_radius = float(check["q_relative_projection_radius_mm"])
            if branch_check is not None:
                geometric_interval = branch_check["geometric_elongation_interval_mm"]
                projected_q = float(branch_check["projected_q_mm"])
                q_radius = float(branch_check["projected_q_rounding_radius_mm"])
            else:
                geometric_interval = [None, None]
                projected_q = q
            rows.append({
                "cell_name": str(floor["name"]),
                "source_group": str(floor["group"]),
                "source_row_id": str(floor["source_row_id"]),
                "selected_in_attempt03_input": selected_cell,
                "classification": classification,
                "classification_reason": reason,
                "projected_q_interval_mm": [projected_q - q_radius, projected_q + q_radius],
                "geometric_elongation_interval_mm": geometric_interval,
            })
        if len(rows) != 100 or len({row["cell_name"] for row in rows}) != 100:
            raise RuntimeError(f"Floor-normal inventory is incomplete at t={time}")
        counts = Counter(row["classification"] for row in rows)
        positive = sorted(row["cell_name"] for row in rows if row["classification"] == "STRICTLY_POSITIVE")
        separated = sorted(row["cell_name"] for row in rows
                           if row["classification"] == "STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF")
        stable_positive_sets.append(positive)
        floor_states.append({
            "load_factor": time,
            "normal_count": len(rows),
            "strictly_positive_count": counts["STRICTLY_POSITIVE"],
            "strictly_separated_count": counts["STRICTLY_SEPARATED_WITH_ZERO_ENDPOINT_RF"],
            "ambiguous_or_noncomplementary_count": counts["INTERVAL_AMBIGUOUS_OR_NOT_COMPLEMENTARY"],
            "positive_cell_names_diagnostic_only": positive,
            "separated_cell_names_diagnostic_only": separated,
            "rows": rows,
        })

    if any(positive != sorted(selected) for positive in stable_positive_sets):
        raise RuntimeError("Attempt03 observed strict-positive floor set differs from its proposed 23-cell mask")
    if any(row["interval_excess_mm"] > 0.0 and row["load_factor"] != 0.2
           for row in qghost_states):
        raise RuntimeError("The qghost aggregate gate now fails at an unexpected state")
    failing = next(row for row in qghost_states if row["load_factor"] == 0.2)
    if failing["strict_qghost_interval_pass"] or failing["interval_excess_mm"] <= 0.0:
        raise RuntimeError("SPR489 qghost interval failure did not reproduce at t=0.2")

    coefficient_record = {
        "source_axis_yz": axis[1:],
        "emitted_axis_yz_from_qghost_equation_coefficients": [emitted_y, emitted_z],
        "emitted_minus_source_coefficient_deltas": coefficient_delta,
        "maximum_absolute_coefficient_delta": max(map(abs, coefficient_delta)),
        "interpretation": "14-significant-digit deck formatting only; the emitted source-projection and qghost equations share these coefficients.",
    }
    diagnosis = {
        "schema": SCHEMA,
        "status": "DIAGNOSTIC_ONLY_QGHOST_PRINTED_INTERVAL_EXCEPTION",
        "case_id": "k12-rear",
        "attempt_id": "springa-selected-k12-rear-attempt03",
        "native_force_adoption": False,
        "corner_demands_usable": False,
        "support_qualification": False,
        "physical_failure_inferred": False,
        "qghost_gate_replay": strict_replay,
        "spr489_binding": {
            "source_row_id": binding["source_row_id"],
            "source_inventory_row_index": binding["source_inventory_row_index"],
            "source_element": binding["source_element"],
            "name": binding["name"],
            "first_owner": source["physical_owner"]["first"],
            "second_owner": source["physical_owner"]["second"],
            "normal_axis_xyz": axis,
            "source_projection_nodes_dof": [[15670, 1], [15671, 1]],
            "qghost_nodes": [19800, 19801],
            "q_definition": "u(15671,1) - u(15670,1)",
        },
        "emitted_coefficient_audit": coefficient_record,
        "qghost_state_reconstruction": qghost_states,
        "floor_normal_classification": {
            "method": "Pinned attempt03 response audit SPRINGA law check and _strict_normal_branch_check; no force values retained.",
            "proposed_selected_cell_count": len(selected),
            "source_normal_cell_count": len(floor_bindings),
            "states": floor_states,
            "stable_positive_set_through_all_recorded_states": stable_positive_sets[0],
            "stable_mask_matches_proposed_input": True,
            "response_gate_implication": "Floor normals are strictly classified 23 positive and 77 separated at all seven output states, but this does not cure or waive the independent SPR489 qghost gate.",
        },
        "engineering_interpretation": {
            "finding": "A small native-output qghost MPC residual at SPR489 DOF2 lies outside its DAT token-rounding interval at t=0.2; the source-projection equation rows pass, so this is not a demonstrated source-geometry mismatch.",
            "basis": "At t=0.2, the qghost-to-source scalar gap exceeds the combined pinned token intervals plus arithmetic guard by only the recorded interval_excess_mm. Both source-projection equations intersect zero at every recorded state; the qghost z equation passes at t=0.2, and all MPCs satisfy the pinned 1e-5 mm generic residual criterion. Emitted axis coefficients differ from the source axis only by .14g formatting.",
            "limitation": "The output proves that the rounding-only intervals do not intersect at t=0.2. The response files do not expose a solver-internal MPC residual, so they cannot attribute the remaining difference more narrowly than a small native-output residual versus the rounding-only interval gate. Do not call this a token-decoding bug or a structural incompatibility.",
            "method_action": "No interval relaxation, response-force adoption, branch iteration, or native rerun is authorized by this diagnosis.",
        },
    }

    method_hashes = {
        rel(AUDIT): sha(AUDIT),
        rel(KERNEL): sha(KERNEL),
        rel(Path(__file__)): sha(Path(__file__)),
    }
    source_files = {name: sha(RUN / name) for name in EXPECTED_RUN_HASHES}
    source_files.update({
        "native.stdout": sha(RUN / "native.stdout"),
        "native.stderr": sha(RUN / "native.stderr"),
        "parent-serialized-input-audit.json": sha(RUN / "parent-serialized-input-audit.json"),
        "parent-case-context-check.json": sha(RUN / "parent-case-context-check.json"),
        "parent-readiness-review.json": sha(RUN / "parent-readiness-review.json"),
    })
    pins = {
        "schema": "current_springa_selected_floor_qghost_diagnosis_source_pins/v1",
        "run_packet_path": rel(RUN),
        "run_source_sha256": source_files,
        "pinned_response_methods_sha256": method_hashes,
        "response_method_claims": {
            "strict_gate": EXPECTED_GATE,
            "token_policy": "Pinned CalculiX 2.23 E13.6 token radii; canonical exact zero U fields have zero radius under the prior bounded zero-U fixture.",
            "generic_mpc_tolerance_mm": audit._stable.MPC_INTERVAL_TOL_MM,
        },
        "source_case_context": {
            "case_id": context.get("case_id"),
            "candidate": context.get("candidate"),
            "geometry_revision_id": context.get("geometry_revision_id"),
            "source_controls_model_json_path": context.get("source_controls_model_json_path"),
            "source_controls_model_json_sha256": context.get("source_controls_model_json_sha256"),
            "source_controls_deck_path": context.get("source_controls_deck_path"),
            "source_controls_deck_sha256": context.get("source_controls_deck_sha256"),
            "diagnostic_floor_screen_path": context.get("diagnostic_floor_screen_path"),
            "diagnostic_floor_screen_sha256": context.get("diagnostic_floor_screen_sha256"),
            "selected_floor_branch_id": context.get("selected_floor_branch_id"),
            "selected_floor_mask_count": len(selected),
        },
    }
    (HERE / "source-pins.json").write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n")
    (HERE / "diagnosis.json").write_text(json.dumps(diagnosis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": diagnosis["status"],
        "diagnosis_sha256": sha(HERE / "diagnosis.json"),
        "source_pins_sha256": sha(HERE / "source-pins.json"),
        "failing_load_factor": 0.2,
        "qghost_interval_excess_mm": failing["interval_excess_mm"],
        "floor_normal_counts_by_state": [
            [row["load_factor"], row["strictly_positive_count"], row["strictly_separated_count"],
             row["ambiguous_or_noncomplementary_count"]]
            for row in floor_states
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
