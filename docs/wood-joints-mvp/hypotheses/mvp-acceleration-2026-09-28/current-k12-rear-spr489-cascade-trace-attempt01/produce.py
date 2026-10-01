#!/usr/bin/env python3
"""Replay CCX 2.23 SPR489 cascade and prepare a direct-scalar coupon input only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import sys
import tarfile
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
RUN = SERIES / "current-springa-selected-floor-k12-rear-attempt03"
DIAG = SERIES / "current-springa-selected-floor-k12-rear-qghost-diagnosis-attempt01"
REL_FIXTURE = SERIES / "current-springa-relative-coordinate-fixture-attempt01"
AUDIT = SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
KERNEL = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
ARCHIVE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt02/build/context/source.tar.bz2"
MANIFEST = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/build_manifest.json"
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
CASCADE_MEMBER = "./CalculiX/ccx_2.23/src/cascade.c"

PINS = {
    "model.json": "9591669b74af719e72df2a681504cab4e283d693eaac5e42920558b30773168f",
    "model.inp": "6b630749e918189583147833e3ef94a1338dc5bb28f42171cefc05cb039695e9",
    "model.dat": "29ec3cca415ee8f1ddb6cccd07a70aade816fd4c71eca98a5944d441f6d42f7a",
    "execution.json": "805e2b43da0f612de7801eca6fa4e05c834e90d805ceb12c23a3cf03c72dae71",
    "case-context.json": "1a352178c8fe2ad64681d2f456d9fdf29e67b72d0a1cbce3aa3ed5df21259a93",
    "freeze.json": "f1d9245626d18007e68732fb79f1a0630adc292397d0ba2fd7c2ca17c48b1cfd",
    "parent-terminal-assessment.json": "c4962da39c6378cdbe9e11315017023e17d8a63a9996a4036d991fd7664aa896",
}
ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
CASCADE_SHA256 = "f90bd79ecb2b469aad0a1126e0a365ad97c3e5a50b3cfb93d359f0371e6ef534"
AUDIT_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
KERNEL_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
DIAG_SHA256 = ""  # Filled from the preserved diagnosis packet at first generation.
EXPECTED_GATE = "SPRINGA qghost displacement does not match its source projections: SPR489"
TARGET_Q = [(19800, 2), (19800, 3)]
ZERO_TOL = 1.0e-10


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def import_pinned(name: str, path: Path, expected: str):
    actual = sha(path)
    if actual != expected:
        raise RuntimeError(f"Pinned source changed: {relative(path)} SHA={actual}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import pinned source: {relative(path)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fmt_real(value: float) -> str:
    rendered = format(float(value), ".14g")
    if "." not in rendered and "e" not in rendered.lower():
        rendered += ".0"
    return rendered


def deck_equations(audit: Any, deck: str) -> list[list[list[float]]]:
    rows = audit.parse_equation_cards(deck)
    if not rows:
        raise RuntimeError("No *EQUATION rows parsed from pinned deck")
    return rows


def dependent_map(rows: list[list[list[float]]]) -> dict[tuple[int, int], int]:
    result: dict[tuple[int, int], int] = {}
    for index, row in enumerate(rows):
        key = (int(row[0][0]), int(row[0][1]))
        if key in result:
            raise RuntimeError(f"Duplicate dependent DOF {key}")
        result[key] = index
    return result


def closure_for(rows: list[list[list[float]]], targets: list[tuple[int, int]]) -> list[int]:
    by_dep = dependent_map(rows)
    found: set[int] = set()
    pending = list(targets)
    while pending:
        dof = pending.pop()
        index = by_dep.get(dof)
        if index is None or index in found:
            continue
        found.add(index)
        pending.extend((int(term[0]), int(term[1])) for term in rows[index][1:])
    return sorted(found)


def consolidate(row: list[list[float]]) -> list[list[float]]:
    """Source cascade.c duplicate-term collection, retaining first-term order."""
    result: list[list[float]] = []
    for node, dof, coefficient in row:
        key = (int(node), int(dof))
        prior = next((term for term in result if (int(term[0]), int(term[1])) == key), None)
        if prior is None:
            result.append([key[0], key[1], float(coefficient)])
        else:
            prior[2] = float(prior[2]) + float(coefficient)
    return result


def cascade_replay(rows: list[list[list[float]]], closure: list[int], prune: bool) -> dict[str, Any]:
    """Faithful relevant `cascade.c` simple-substitution loop for linear MPCs.

    The CCX routine substitutes one dependent independent term per MPC per
    sweep, consolidates duplicate DOFs, repairs a near-zero dependent only,
    then (for independent terms) drops coefficients below 1e-10.
    """
    selected = {i: [list(map(float, term)) for term in rows[i]] for i in closure}
    dep_to_row = {(int(rows[i][0][0]), int(rows[i][0][1])): i for i in closure}
    if len(dep_to_row) != len(closure):
        raise RuntimeError("Cascade closure has duplicate dependent DOFs")
    log: list[dict[str, Any]] = []
    repaired: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for sweep in range(1, 20):
        changed = False
        for i in closure:
            row = selected[i]
            replacement_index = None
            replacement_row_index = None
            for term_index, term in enumerate(row[1:], start=1):
                dependent = (int(term[0]), int(term[1]))
                if dependent in dep_to_row:
                    replacement_index = term_index
                    replacement_row_index = dep_to_row[dependent]
                    break
            if replacement_index is None:
                continue

            # cascade.c lines 185-213 consolidates before reading the term.
            row = consolidate(row)
            selected[i] = row
            replacement_index = next(
                (j for j, t in enumerate(row[1:], start=1)
                 if (int(t[0]), int(t[1])) in dep_to_row), None)
            if replacement_index is None:
                continue
            source_i = dep_to_row[(int(row[replacement_index][0]), int(row[replacement_index][1]))]
            source = selected[source_i]
            dep_coefficient = float(row[0][2])
            coefmin = min((abs(float(term[2])) for term in row if float(term[2]) != 0.0), default=1.0e30)
            if abs(dep_coefficient) < ZERO_TOL:
                repaired_value = 1.0e-5 * coefmin
                repaired.append({"equation_index_zero_based": i,
                                 "dependent_dof": row[0][:2],
                                 "original_coefficient": dep_coefficient,
                                 "replacement": repaired_value,
                                 "branch": "cascade.c:218-225 before substitution"})
                row[0][2] = repaired_value
                dep_coefficient = repaired_value
            source_dependent = float(source[0][2])
            if source_dependent == 0.0:
                raise RuntimeError(f"Zero source dependent coefficient in row {source_i}")
            source_scale = -float(row[replacement_index][2]) / source_dependent
            expanded = [[int(term[0]), int(term[1]), source_scale * float(term[2])]
                        for term in source[1:]]
            replaced = row[replacement_index]
            row = row[:replacement_index] + expanded + row[replacement_index + 1:]
            row = consolidate(row)
            if prune:
                new_row: list[list[float]] = []
                for term_index, term in enumerate(row):
                    if term_index > 0 and abs(float(term[2])) < ZERO_TOL:
                        dropped.append({
                            "equation_index_zero_based": i,
                            "dependent_dof": row[0][:2],
                            "dropped_dof": [int(term[0]), int(term[1])],
                            "dropped_coefficient": float(term[2]),
                            "source_branch": "cascade.c:325-340 independent-term deletion",
                            "sweep": sweep,
                        })
                        continue
                    if term_index == 0 and abs(float(term[2])) < ZERO_TOL:
                        coefmin2 = min((abs(float(t[2])) for t in row if float(t[2]) != 0.0), default=1.0e30)
                        repaired_value = 1.0e-5 * coefmin2
                        repaired.append({"equation_index_zero_based": i,
                                         "dependent_dof": term[:2],
                                         "original_coefficient": float(term[2]),
                                         "replacement": repaired_value,
                                         "branch": "cascade.c:325-333 dependent repair after substitution"})
                        term[2] = repaired_value
                    new_row.append(term)
                row = new_row
            selected[i] = row
            log.append({
                "sweep": sweep,
                "equation_index_zero_based": i,
                "dependent_dof": selected[i][0][:2],
                "replaced_dof": [int(replaced[0]), int(replaced[1])],
                "source_equation_index_zero_based": source_i,
                "term_count_after": len(row),
                "pruning_enabled": prune,
            })
            changed = True
        if not changed:
            return {"rows": selected, "sweeps_until_fixed_point": sweep,
                    "substitution_log": log, "dependent_repairs": repaired,
                    "independent_terms_pruned": dropped}
    raise RuntimeError("Cascade replay did not reach a fixed point")


def dat_u_tokens(data: str) -> dict[float, dict[int, list[str]]]:
    pattern = re.compile(r"^\s*displacements\s*\([^\n]*\btime\s+([0-9.EeDd+-]+)\s*\n",
                         re.MULTILINE | re.IGNORECASE)
    found: dict[float, dict[int, list[str]]] = {}
    for match in pattern.finditer(data):
        time = float(match.group(1).replace("D", "E").replace("d", "e"))
        values: dict[int, list[str]] = {}
        for line in data[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                values[int(fields[0])] = fields[1:]
            elif values:
                break
        if not values or time in found:
            raise RuntimeError(f"Malformed/duplicate DAT displacement block t={time}")
        found[time] = values
    return dict(sorted(found.items()))


def eval_equation(row: list[list[float]], tokens: dict[int, list[str]], token_radius: Any) -> tuple[float, float]:
    residual = 0.0
    radius = 0.0
    for node, dof, coefficient in row:
        raw = tokens[int(node)][int(dof) - 1]
        value = float(raw.replace("D", "E").replace("d", "e"))
        residual += float(coefficient) * value
        radius += abs(float(coefficient)) * token_radius(raw)
    return residual, radius


def cross(a: list[float], b: list[float]) -> list[float]:
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def add3(a: list[float], b: list[float]) -> list[float]:
    return [a[i] + b[i] for i in range(3)]


def scale3(a: list[float], x: float) -> list[float]:
    return [float(x) * a[i] for i in range(3)]


def equation_card(terms: list[list[float]]) -> list[str]:
    out = ["*EQUATION", str(len(terms))]
    for start in range(0, len(terms), 4):
        out.append(",".join(f"{int(n)},{int(d)},{fmt_real(float(c))}"
                             for n, d, c in terms[start:start + 4]))
    return out


def prepare_coupon(audit: Any, model: dict[str, Any], deck: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    equations = deck_equations(audit, deck)
    dep = dependent_map(equations)
    index_for = {dof: i for dof, i in dep.items()}
    source_rows = {}
    for label, dof in {
        "interpolation_A_y": (13526, 2), "interpolation_A_z": (13526, 3),
        "interpolation_B_y": (13527, 2), "interpolation_B_z": (13527, 3),
    }.items():
        index = index_for[dof]
        source_rows[label] = {"index": index, "terms": equations[index]}

    binding = next(x for x in model["unilateral_springa_bindings"] if x["source_row_id"] == "SPR489")
    owner = binding["physical_owner"]
    axis = [float(x) for x in owner["scalar_normal"]]
    weights: dict[str, list[tuple[int, float]]] = {}
    for side, label in (("A", "interpolation_A_y"), ("B", "interpolation_B_y")):
        row = source_rows[label]["terms"]
        weights[side] = [(int(n), -float(c)) for n, _d, c in row[1:]]
    for side, label in (("A", "interpolation_A_z"), ("B", "interpolation_B_z")):
        row = source_rows[label]["terms"]
        ids = [(int(n), -float(c)) for n, _d, c in row[1:]]
        if ids != weights[side]:
            raise RuntimeError(f"SPR489 y/z interpolation coefficient identity failed on side {side}")

    masters_a = [n for n, _w in weights["A"]]
    masters_b = [n for n, _w in weights["B"]]
    if set(masters_a) & set(masters_b):
        raise RuntimeError("SPR489 source interpolation master sets overlap")
    body_nodes = model["physical_body_nodes"]
    if not set(masters_a).issubset(set(map(int, body_nodes[owner["first"]]))):
        raise RuntimeError("SPR489 first interpolation master ownership mismatch")
    if not set(masters_b).issubset(set(map(int, body_nodes[owner["second"]]))):
        raise RuntimeError("SPR489 second interpolation master ownership mismatch")

    coords = {int(n): [float(v) for v in xyz] for n, xyz in model["nodes"].items()}
    point = [float(x) for x in owner["point"]]
    centroid_a = scale3([sum(w * coords[n][j] for n, w in weights["A"]) for j in range(3)],
                        1.0 / sum(w for _n, w in weights["A"]))
    centroid_b = scale3([sum(w * coords[n][j] for n, w in weights["B"]) for j in range(3)],
                        1.0 / sum(w for _n, w in weights["B"]))

    qnode, ground = 90001, 90002
    direct_terms: list[list[float]] = [[qnode, 1, 1.0]]
    for side in ("A", "B"):
        sign = 1.0 if side == "A" else -1.0
        for node, weight in weights[side]:
            direct_terms.append([node, 2, sign * axis[1] * weight])
            direct_terms.append([node, 3, sign * axis[2] * weight])
    direct_card = equation_card(direct_terms)
    # Parse back the printed real fields so the oracle uses exactly what the
    # prepared input serializes, not unformatted Python coefficient values.
    serialized_terms: list[list[float]] = []
    for line in direct_card[2:]:
        fields = line.split(",")
        if len(fields) % 3:
            raise RuntimeError("Malformed direct scalar *EQUATION serialization")
        for index in range(0, len(fields), 3):
            serialized_terms.append([int(fields[index]), int(fields[index + 1]), float(fields[index + 2])])
    if len(serialized_terms) != 81 or serialized_terms[0] != [qnode, 1, 1.0]:
        raise RuntimeError("Direct scalar row is not the expected q plus 80 source DOFs")

    serialized_axis_coeffs = {(int(n), int(d)): float(c) for n, d, c in serialized_terms[1:]}
    # Use the actual owner-source interpolation weights and normalized normal
    # to establish targets; the q coordinate itself is evaluated from the
    # rounded direct equation card below.
    states_spec = [
        {"state": "small_positive_common_mode", "pA": 4.342299e-4, "q_target": 1.6493e-6},
        {"state": "small_negative_common_mode", "pA": 4.342299e-4, "q_target": -1.6493e-6},
        {"state": "positive_control", "pA": 4.342299e-4, "q_target": 1.0e-2},
    ]
    stiffness = float(binding["stiffness_n_per_mm"])
    support_k = 100.0
    # Keep the original geometric owner action/sign convention from the
    # previously run relative-coordinate coupon: first +f*n, second -f*n.
    prepared_states: list[dict[str, Any]] = []
    source_loads: dict[str, dict[str, float]] = {}
    all_master_nodes = masters_a + masters_b
    ground_for = {node: 91000 + i for i, node in enumerate(all_master_nodes)}

    for spec in states_spec:
        pA = float(spec["pA"])
        pB = pA + float(spec["q_target"])
        displacement: dict[tuple[int, int], float] = {}
        for side, p in (("A", pA), ("B", pB)):
            for node, _weight in weights[side]:
                displacement[(node, 2)] = p * axis[1]
                displacement[(node, 3)] = p * axis[2]
        q_from_emitted = -sum(
            coefficient * displacement[(node, dof)]
            for (node, dof), coefficient in serialized_axis_coeffs.items()
        )
        native_force = stiffness * max(q_from_emitted, 0.0)
        loads: dict[str, float] = {}
        support_end_forces: dict[str, list[float]] = {}
        joint_actions: dict[str, list[float]] = {}
        for node in all_master_nodes:
            uy = displacement[(node, 2)]
            uz = displacement[(node, 3)]
            cy = serialized_axis_coeffs[(node, 2)]
            cz = serialized_axis_coeffs[(node, 3)]
            action = [0.0, native_force * cy, native_force * cz]
            support = [0.0, support_k * uy, support_k * uz]
            load = [support[1] - action[1], support[2] - action[2]]
            # The load is the manufactured external load for which the chosen
            # common-mode displacement is an exact equilibrium of the two
            # linear support springs plus the unilateral joint.
            loads[f"{node}:2"] = load[0]
            loads[f"{node}:3"] = load[1]
            support_end_forces[str(node)] = support
            joint_actions[str(node)] = action
        source_loads[str(len(prepared_states) + 1)] = loads

        action_a = [sum(joint_actions[str(n)][i] for n in masters_a) for i in range(3)]
        action_b = [sum(joint_actions[str(n)][i] for n in masters_b) for i in range(3)]
        moment_a = [0.0, 0.0, 0.0]
        moment_b = [0.0, 0.0, 0.0]
        for node in masters_a:
            moment_a = add3(moment_a, cross(coords[node], joint_actions[str(node)]))
        for node in masters_b:
            moment_b = add3(moment_b, cross(coords[node], joint_actions[str(node)]))
        ideal_a = scale3(axis, native_force)
        ideal_b = scale3(ideal_a, -1.0)
        ideal_ma = cross(point, ideal_a)
        ideal_mb = cross(point, ideal_b)
        body_a_residual = [action_a[i] - ideal_a[i] for i in range(3)]
        body_b_residual = [action_b[i] - ideal_b[i] for i in range(3)]
        moment_a_residual = [moment_a[i] - ideal_ma[i] for i in range(3)]
        moment_b_residual = [moment_b[i] - ideal_mb[i] for i in range(3)]
        per_body_balance: dict[str, float] = {}
        for side, nodes, sign in (("A", masters_a, 1.0), ("B", masters_b, -1.0)):
            # CLOAD + support-body action (-spring endpoint force) + joint
            # physical action = 0; this sign was verified by the pinned small
            # two-body relative SPRINGA fixture.
            per_body_balance[side] = 0.0
            for node in nodes:
                for dof in (2, 3):
                    c = serialized_axis_coeffs[(node, dof)]
                    u = displacement[(node, dof)]
                    action_component = native_force * c
                    load_component = loads[f"{node}:{dof}"]
                    support_component = support_k * u
                    per_body_balance[side] += load_component - support_component + action_component

        q_token = f"{q_from_emitted:.6E}"
        q_radius = audit._stable._u_token_radius(q_token)
        force_radius = stiffness * q_radius
        prepared_states.append({
            "state": spec["state"],
            "pA_target_mm": pA,
            "pB_target_mm": pB,
            "target_q_mm": float(spec["q_target"]),
            "serialized_equation_q_mm": q_from_emitted,
            "q_dat_token_example": q_token,
            "q_interval_mm_from_example_DAT_token": [q_from_emitted - q_radius, q_from_emitted + q_radius],
            "q_interval_radius_mm_from_example_DAT_token": q_radius,
            "native_force_expected_N": native_force,
            "native_force_interval_N_from_q_token_only": [native_force - force_radius, native_force + force_radius],
            "joint_internal_force_endpoint_Q_N": native_force,
            "joint_internal_force_endpoint_ground_N": -native_force,
            "physical_action_on_first_owner_N": ideal_a,
            "physical_action_on_second_owner_N": ideal_b,
            "physical_nodal_action_by_source_master_N": joint_actions,
            "support_spring_endpoint_force_by_source_master_N": support_end_forces,
            "source_CLOAD_by_source_master_dof_N": loads,
            "body_A_force_from_nodal_coefficients_N": action_a,
            "body_B_force_from_nodal_coefficients_N": action_b,
            "body_A_owner_force_residual_N": body_a_residual,
            "body_B_owner_force_residual_N": body_b_residual,
            "body_A_nodal_moment_global_origin_Nmm": moment_a,
            "body_B_nodal_moment_global_origin_Nmm": moment_b,
            "body_A_owner_moment_global_origin_Nmm": ideal_ma,
            "body_B_owner_moment_global_origin_Nmm": ideal_mb,
            "body_A_owner_moment_residual_Nmm": moment_a_residual,
            "body_B_owner_moment_residual_Nmm": moment_b_residual,
            "manufactured_source_body_balance_residual_N": per_body_balance,
        })

    # Emit all nodes and springs as a stand-alone native coupon. The same
    # source CLOAD values appearing here are recorded above and in model.json.
    fixture_nodes = {n: coords[n] for n in all_master_nodes}
    for node, ground_id in ground_for.items():
        fixture_nodes[ground_id] = coords[node][:]
    fixture_nodes[qnode] = [100.0, 0.0, 0.0]
    fixture_nodes[ground] = [0.0, 0.0, 0.0]
    lines = [
        "*HEADING",
        "SPR489 actual-interpolation direct-scalar SPRINGA coupon; input-only, not a frame",
        "*NODE,NSET=ALLNODES",
    ]
    lines.extend(f"{n},{fmt_real(x)},{fmt_real(y)},{fmt_real(z)}"
                 for n, (x, y, z) in fixture_nodes.items())
    lines.extend(["*ELEMENT,TYPE=SPRINGA,ELSET=JOINT", f"1,{qnode},{ground}"])
    element_id = 100
    support_y_ids = []
    support_z_ids = []
    for node in all_master_nodes:
        support_y_ids.append((element_id, node, ground_for[node]))
        element_id += 1
        support_z_ids.append((element_id, node, ground_for[node]))
        element_id += 1
    lines.append("*ELEMENT,TYPE=SPRING2,ELSET=SUPPORT_Y")
    lines.extend(f"{eid},{node},{g}" for eid, node, g in support_y_ids)
    lines.append("*ELEMENT,TYPE=SPRING2,ELSET=SUPPORT_Z")
    lines.extend(f"{eid},{node},{g}" for eid, node, g in support_z_ids)
    lines.extend([
        "*SPRING,ELSET=SUPPORT_Y", "2,2", fmt_real(support_k),
        "*SPRING,ELSET=SUPPORT_Z", "3,3", fmt_real(support_k),
        "*SPRING,ELSET=JOINT,NONLINEAR", "",
        "0.,-10.", "0.,0.",
        f"{fmt_real(stiffness * 10.0)},10.",
    ])
    lines.extend(direct_card)
    lines.append("*BOUNDARY")
    for node in all_master_nodes:
        lines.append(f"{node},1,1,0.")
        lines.append(f"{node},4,6,0.")
    for g in ground_for.values():
        lines.append(f"{g},1,3,0.")
    lines.extend([f"{qnode},2,3,0.", f"{ground},1,3,0."])
    for step_index, state in enumerate(prepared_states, start=1):
        lines.extend([
            f"*STEP,NLGEOM,NLGEOM=NO,INC=40",
            "*STATIC", "0.1,1.,1.e-6,0.25", "*CLOAD,OP=NEW",
        ])
        for key, value in sorted(state["source_CLOAD_by_source_master_dof_N"].items()):
            node_s, dof_s = key.split(":")
            lines.append(f"{node_s},{dof_s},{fmt_real(value)}")
        lines.extend(["*NODE PRINT,NSET=ALLNODES", "U", "RF", "*END STEP"])
    inp = "\n".join(lines) + "\n"

    # Check format round-trip, complete unique owners, exact 80 independent
    # master terms, and no source interpolation slave/ghost terms retained.
    for node in all_master_nodes:
        if (node, 1) in serialized_axis_coeffs or (node, 4) in serialized_axis_coeffs:
            raise RuntimeError("Unexpected direct scalar term outside source y/z projection DOFs")
    source_aux = {13526, 13527, 15670, 15671, 19800, 19801}
    if any(int(n) in source_aux for n, _d, _c in serialized_terms[1:]):
        raise RuntimeError("Direct scalar equation retained a source auxiliary node")
    if len(set((int(n), int(d)) for n, d, _c in serialized_terms[1:])) != 80:
        raise RuntimeError("Direct scalar equation has repeated or missing source master DOFs")

    metadata = {
        "schema": "current_spr489_direct_scalar_interpolation_coupon/v1",
        "status": "PREPARED_INPUT_ONLY_NO_NATIVE_EXECUTION",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "case_id": "k12-rear",
        "scope": "A disconnected source-bound SPR489 interpolation / scalar SPRINGA method coupon; no frame demand or joint acceptance.",
        "native_solve_executed": False,
        "qualified_for_design": False,
        "source_physical_binding": {
            "source_row_id": "SPR489",
            "source_inventory_row_index": binding["source_inventory_row_index"],
            "source_element": binding["source_element"],
            "name": binding["name"],
            "first_owner": owner["first"],
            "second_owner": owner["second"],
            "physical_owner_point_global_mm": point,
            "physical_owner_role": owner["role"],
            "preserved_scalar_normal_global": axis,
            "stiffness_N_per_mm": stiffness,
            "force_law": binding["force_law"],
            "native_table_force_vs_elongation_N_mm": binding["force_vs_elongation_table_N_mm"],
            "source_owner_fields_exactly_match_pinned_attempt03_binding": True,
            "ownership_basis_pin": relative(REL_FIXTURE / "assessment.json"),
        },
        "source_interpolation": {
            "source_rows": source_rows,
            "first_master_nodes_and_weights": [[n, w] for n, w in weights["A"]],
            "second_master_nodes_and_weights": [[n, w] for n, w in weights["B"]],
            "first_weight_sum": sum(w for _n, w in weights["A"]),
            "second_weight_sum": sum(w for _n, w in weights["B"]),
            "first_weighted_master_centroid_global_mm": centroid_a,
            "second_weighted_master_centroid_global_mm": centroid_b,
            "owner_point_global_mm": point,
            "direct_scalar_equation_terms_serialized": serialized_terms,
            "direct_scalar_equation": "u(Q,1) = n_y * sum_B(w_i*u_i,2) + n_z*sum_B(w_i*u_i,3) - n_y*sum_A(w_i*u_i,2) - n_z*sum_A(w_i*u_i,3) = p_B - p_A",
            "equation_independent_dofs": 80,
            "interpolation_and_projection_auxiliary_nodes_removed_from_coupon_equation": True,
        },
        "numerical_supports": {
            "support_spring_stiffness_N_per_mm_per_master_component": support_k,
            "support_springs_are_fixture_only": True,
            "q_node": qnode,
            "ground_node": ground,
            "spring_initial_span_mm": 100.0,
            "ground_is_numerical_only": True,
        },
        "known_answer_states": prepared_states,
        "source_CLOADs_by_step": source_loads,
        "native_expected_spring_endpoint_forces": {
            "interpretation": "Expected SPRINGA endpoint RF follows the pinned relative-coordinate coupon convention; expected SPRING2 endpoint contributions are k*u at each source master and opposite at its numerical ground. This is a method coupon output oracle, not physical support qualification.",
            "joint_endpoint_node_order": [qnode, ground],
            "physical_owner_sign": "With q=pB-pA, action on first owner is +f*n and second is -f*n, as in the pinned native relative-coordinate fixture.",
        },
        "limits": [
            "No native run, freeze, force adoption, case response audit, or joint acceptance was performed.",
            "The coupon replaces the nested interpolation/projection/qghost chain with a direct scalar equation over the same physical source interpolation masters; the deck must be reviewed before a parent-owned run.",
            "Numerical support springs are manufactured only to produce an independently prescribed known-answer state.",
            "The tiny-q state checks common-mode cancellation scale and unilateral sign; it does not reproduce or validate the full frame equilibrium.",
        ],
    }
    return metadata, inp, {"states": prepared_states, "direct_equation": serialized_terms}


def excerpt_lines(cascade_text: str) -> str:
    lines = cascade_text.splitlines()
    ranges = [(127, 140), (145, 180), (182, 228), (229, 284), (285, 347)]
    return "\n".join(f"{i:4d} {lines[i-1]}" for start, end in ranges for i in range(start, end + 1)) + "\n"


def build_outputs() -> dict[str, bytes]:
    for name, expected in PINS.items():
        path = RUN / name
        if not path.is_file() or sha(path) != expected:
            raise RuntimeError(f"Attempt03 source pin mismatch for {name}")
    audit = import_pinned("pinned_springa_response_audit", AUDIT, AUDIT_SHA256)
    if sha(KERNEL) != KERNEL_SHA256:
        raise RuntimeError("Pinned response-kernel source changed")
    model = load_json(RUN / "model.json")
    deck = (RUN / "model.inp").read_text()
    data = (RUN / "model.dat").read_text(errors="replace")
    assessment = load_json(RUN / "parent-terminal-assessment.json")
    if assessment.get("strict_response_exception") != EXPECTED_GATE:
        raise RuntimeError("K12-rear attempt03 no longer has the pinned SPR489 gate")
    diagnosis = load_json(DIAG / "diagnosis.json")
    contract = audit._validate_model(model, deck, load_json(RUN / "case-context.json"))
    equations = deck_equations(audit, deck)
    closure = closure_for(equations, TARGET_Q)
    if len(closure) != 8:
        raise RuntimeError(f"Expected eight-equation SPR489 dependency closure, got {len(closure)}")
    floor_rows = set(model["floor_selected_branch_constraint_audit"]["active_original_row_indices"])
    # Floor rows are found by their emitted reference nodes and actual dependent
    # DOFs. They are source audit rows, while this source deck stores row indices
    # directly; map the known serialized interval by matching reference DOFs.
    floor_reference_deps = {
        tuple(row["dependent_physical_pivot_dof"])
        for row in model["floor_selected_branch_constraint_audit"]["floor_reference_rows"]
    }
    closure_deps = {(int(equations[i][0][0]), int(equations[i][0][1])) for i in closure}
    floor_eq_indices = {i for i, row in enumerate(equations)
                        if (int(row[0][0]), int(row[0][1])) in floor_reference_deps}
    if set(closure) & floor_eq_indices:
        raise RuntimeError("SPR489 dependency closure unexpectedly includes a selected floor equation")

    pruned = cascade_replay(equations, closure, prune=True)
    unpruned = cascade_replay(equations, closure, prune=False)
    if pruned["dependent_repairs"] or unpruned["dependent_repairs"]:
        raise RuntimeError("SPR489 closure took cascade.c dependent-coefficient repair branch")
    state_times = [0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0]
    tokens = dat_u_tokens(data)
    if list(tokens) != state_times:
        raise RuntimeError(f"Attempt03 DAT state times changed: {list(tokens)}")
    if len(contract["bindings"]) == 0:
        raise RuntimeError("Pinned case response contract did not validate")
    rows_by_dep = {tuple(map(int, row[0][:2])): row for row in equations}
    y_key, z_key = (19800, 2), (19800, 3)
    if y_key not in rows_by_dep or z_key not in rows_by_dep:
        raise RuntimeError("SPR489 qghost axes missing from input deck")
    pruned_rows = pruned["rows"]
    unpruned_rows = unpruned["rows"]
    per_state: list[dict[str, Any]] = []
    for time in state_times:
        state_tokens = tokens[time]
        pr_y, r_pr_y = eval_equation(pruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)], state_tokens, audit._stable._u_token_radius)
        un_y, r_un_y = eval_equation(unpruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)], state_tokens, audit._stable._u_token_radius)
        pr_z, r_pr_z = eval_equation(pruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)], state_tokens, audit._stable._u_token_radius)
        un_z, r_un_z = eval_equation(unpruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)], state_tokens, audit._stable._u_token_radius)
        # qghost_pred = -sum(independent coefficients * U); equation residual is
        # qghost printed U minus that prediction. The difference of predictions
        # is the negative of the difference of equation residuals.
        delta_pred = [-(pr_y - un_y), -(pr_z - un_z)]
        qnode = state_tokens[19800]
        q_u = [float(qnode[1].replace("D", "E").replace("d", "e")),
               float(qnode[2].replace("D", "E").replace("d", "e"))]
        q_radius = [audit._stable._u_token_radius(qnode[1]), audit._stable._u_token_radius(qnode[2])]
        axis = [float(v) for v in next(b for b in model["unilateral_springa_bindings"] if b["source_row_id"] == "SPR489")["numerical_axis_global_xyz"]]
        delta_q = axis[1] * delta_pred[0] + axis[2] * delta_pred[1]
        delta_q_radius = abs(axis[1]) * (r_pr_y + r_un_y) + abs(axis[2]) * (r_pr_z + r_un_z)
        per_state.append({
            "load_factor": time,
            "qghost_y": {
                "term_count_pruned": len(pruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)]),
                "term_count_unpruned": len(unpruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)]),
                "pruned_equation_residual_mm": pr_y,
                "pruned_printed_U_token_radius_mm": r_pr_y,
                "unpruned_equation_residual_mm": un_y,
                "unpruned_printed_U_token_radius_mm": r_un_y,
                "pruning_induced_qghost_prediction_delta_mm": delta_pred[0],
                "pruned_unpruned_coefficient_delta_by_dof": coefficient_delta(
                    pruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)],
                    unpruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)]),
            },
            "qghost_z": {
                "term_count_pruned": len(pruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)]),
                "term_count_unpruned": len(unpruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)]),
                "pruned_equation_residual_mm": pr_z,
                "pruned_printed_U_token_radius_mm": r_pr_z,
                "unpruned_equation_residual_mm": un_z,
                "unpruned_printed_U_token_radius_mm": r_un_z,
                "pruning_induced_qghost_prediction_delta_mm": delta_pred[1],
                "pruned_unpruned_coefficient_delta_by_dof": coefficient_delta(
                    pruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)],
                    unpruned_rows[next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)]),
            },
            "qghost_vector_pruned_minus_unpruned_mm": delta_pred,
            "qghost_scalar_axis_projection_pruned_minus_unpruned_mm": delta_q,
            "qghost_scalar_delta_token_radius_mm": delta_q_radius,
            "printed_qghost_yz_mm": q_u,
            "printed_qghost_yz_token_radii_mm": q_radius,
            "qghost_yz_unpruned_residual_vector_mm": [un_y, un_z],
            "qghost_yz_pruned_residual_vector_mm": [pr_y, pr_z],
        })

    cascade_text = None
    with tarfile.open(ARCHIVE, "r:bz2") as archive:
        member = archive.extractfile(CASCADE_MEMBER)
        if member is None:
            raise RuntimeError("Pinned source archive does not contain cascade.c")
        cascade_text = member.read().decode("utf-8")
    manifest = load_json(MANIFEST)
    member_hash = manifest["upstream_files_sha256"].get(CASCADE_MEMBER)
    if sha(ARCHIVE) != ARCHIVE_SHA256 or member_hash != CASCADE_SHA256:
        raise RuntimeError("Pinned CCX source archive/member hash changed")
    actual_member_hash = hashlib.sha256(cascade_text.encode()).hexdigest()
    if actual_member_hash != CASCADE_SHA256:
        raise RuntimeError(f"Extracted cascade.c hash mismatch: {actual_member_hash}")
    source_excerpt = excerpt_lines(cascade_text)

    coupon_model, coupon_deck, _ = prepare_coupon(audit, model, deck)
    # A lightweight parser/audit on the written form proves the emitted card
    # has one dependent scalar, 80 independent physical master DOFs, true real
    # constants, and no solver output or forces are imported.
    if coupon_model["source_physical_binding"]["source_row_id"] != "SPR489":
        raise RuntimeError("Coupon lost exact source owner binding")
    if coupon_model["source_physical_binding"]["first_owner"] != "base_rail_service_lower_right" or coupon_model["source_physical_binding"]["second_owner"] != "wj04_lower_full_stock_cleat":
        raise RuntimeError("Coupon owner order differs from original SPR489")

    trace = {
        "schema": "current_k12_rear_spr489_cascade_trace/v1",
        "status": "SOURCE_REPLAYED_DIAGNOSTIC_ONLY_CANDIDATE_NOT_CAUSAL_PROOF",
        "case_id": "k12-rear",
        "source_gate": EXPECTED_GATE,
        "source_dependencies": [relative(RUN / n) for n in PINS],
        "cascade_source_member": CASCADE_MEMBER,
        "cascade_source_sha256": actual_member_hash,
        "cascade_archive_sha256": sha(ARCHIVE),
        "source_loop_behavior": {
            "outer_pass": "CCX cascade.c do/while; loop MPC rows in emitted order; at most one independent-dependent replacement per row per sweep.",
            "dependent_lookup": "Exact node/DOF lookup through sorted ikmpc and ilmpc; all eight rows here are regular linear *EQUATION MPCs.",
            "per_replacement": "Consolidate duplicate terms; substitute factor -coef/coefficient(dependent); consolidate again; replace dependent coefficient only if <1e-10; drop independent terms with abs(coefficient)<1e-10.",
            "source_branches": {"dependent_repair_before_substitution": "cascade.c:218-225", "independent_term_drop_after_substitution": "cascade.c:325-340"},
        },
        "target_qghost_dependent_dofs": [list(dof) for dof in TARGET_Q],
        "dependency_closure_equation_indices_zero_based": closure,
        "dependency_closure_rows_in_actual_source_order": [
            {"equation_index_zero_based": i,
             "dependent_dof": [int(equations[i][0][0]), int(equations[i][0][1])],
             "initial_term_count": len(equations[i]),
             "initial_terms": equations[i]}
            for i in closure
        ],
        "floor_rows_in_closure": sorted(set(closure) & floor_eq_indices),
        "selected_floor_reference_equation_indices_zero_based": sorted(floor_eq_indices),
        "no_floor_rows_intersect_spr489_qghost_dependency_closure": not bool(set(closure) & floor_eq_indices),
        "replay": {
            "sweeps_until_fixed_point": pruned["sweeps_until_fixed_point"],
            "substitution_count": len(pruned["substitution_log"]),
            "substitution_log": pruned["substitution_log"],
            "dependent_coefficient_repairs": pruned["dependent_repairs"],
            "independent_terms_pruned": pruned["independent_terms_pruned"],
            "per_closure_row_counts": [
                {"equation_index_zero_based": i,
                 "dependent_dof": [int(equations[i][0][0]), int(equations[i][0][1])],
                 "input_term_count": len(equations[i]),
                 "unpruned_expanded_term_count": len(unpruned["rows"][i]),
                 "pruned_expanded_term_count": len(pruned["rows"][i]),
                 "pruned_dofs": [[d["dropped_dof"], d["dropped_coefficient"]]
                                 for d in pruned["independent_terms_pruned"] if d["equation_index_zero_based"] == i]}
                for i in closure
            ],
            "qghost_rows_full_precision_unpruned": {str(list(k)): unpruned["rows"][i]
                                                    for k, i in ((y_key, next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)),
                                                                 (z_key, next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)))},
            "qghost_rows_after_ccx_small_independent_term_deletion": {str(list(k)): pruned["rows"][i]
                                                                       for k, i in ((y_key, next(i for i in closure if tuple(map(int, equations[i][0][:2])) == y_key)),
                                                                                    (z_key, next(i for i in closure if tuple(map(int, equations[i][0][:2])) == z_key)))},
            "pruned_unpruned_substitution_log_equal": pruned["substitution_log"] == unpruned["substitution_log"],
            "no_dependent_coefficient_repair_observed": len(pruned["dependent_repairs"]) == 0,
            "all_seven_DAT_states": per_state,
        },
        "diagnostic_link": {
            "diagnosis_json": relative(DIAG / "diagnosis.json"),
            "diagnosis_sha256": sha(DIAG / "diagnosis.json"),
            "strict_gate_state": 0.2,
            "strict_scalar_interval_excess_mm": 1.6343569375211753e-11,
            "diagnosis_qghost_y_row_interval_excess_mm": 2.781879000565223e-11,
            "pruning_bias_at_0_2_scalar_mm": next(s for s in per_state if s["load_factor"] == 0.2)["qghost_scalar_axis_projection_pruned_minus_unpruned_mm"],
            "interpretation": "Cascade deletion is a numerically material candidate contributor at the failing small-q common-mode state. This replay does not prove the internal native residual is caused exclusively by the cutoff; there is no solver-internal MPC residual output, and a residual remainder exists.",
        },
        "scope_limits": [
            "The replay is a source-faithful Python reconstruction of the regular linear-MPC branch on the exact reachable eight-row closure, not an instrumented CCX run.",
            "No source coefficient was repaired as a dependent term; the independent cutoff removed real small coefficients in three closure equations.",
            "No production deck, response audit, tolerance, force, acceptance state, or native run was changed or created.",
            "The direct scalar coupon is an input-only method candidate. It requires a separate parent freeze and one-run authorization before any native execution.",
        ],
    }

    pins: dict[str, Any] = {
        "schema": "current_k12_rear_spr489_cascade_trace_source_pins/v1",
        "source_files": {
            **{relative(RUN / name): sha(RUN / name) for name in PINS},
            relative(DIAG / "diagnosis.json"): sha(DIAG / "diagnosis.json"),
            relative(AUDIT): sha(AUDIT),
            relative(KERNEL): sha(KERNEL),
            relative(ARCHIVE): sha(ARCHIVE),
            relative(MANIFEST): sha(MANIFEST),
            relative(PROFILE): sha(PROFILE),
            relative(REL_FIXTURE / "model.inp"): sha(REL_FIXTURE / "model.inp"),
            relative(REL_FIXTURE / "model.json"): sha(REL_FIXTURE / "model.json"),
            relative(REL_FIXTURE / "assessment.json"): sha(REL_FIXTURE / "assessment.json"),
        },
        "pinned_source_members": {CASCADE_MEMBER: actual_member_hash},
        "output_files": {},
    }
    outputs = {
        "cascade-trace.json": (json.dumps(trace, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
        "source-pins.json": b"",  # filled after other outputs are hashed
        "cascade-source-excerpt.txt": source_excerpt.encode(),
        "direct-scalar-coupon/model.json": (json.dumps(coupon_model, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
        "direct-scalar-coupon/model.inp": coupon_deck.encode(),
        "direct-scalar-coupon/analytic-check.json": (json.dumps({
            "schema": "current_spr489_direct_scalar_interpolation_analytic_check/v1",
            "status": "INPUT_ONLY_ANALYTIC_ORACLE_PREPARED",
            "native_solve_executed": False,
            "qualified_for_design": False,
            "source_owner_binding_matches_original_spr489": True,
            "source_row_id": "SPR489",
            "preserved_axis_and_owner_point_source": "Pinned attempt03 model.json SPR489 unilateral_springa_binding.",
            "existing_relative_coordinate_sign_fixture": relative(REL_FIXTURE / "assessment.json"),
            "existing_relative_coordinate_sign_fixture_sha256": sha(REL_FIXTURE / "assessment.json"),
            "checks": [
                "Direct q equation is evaluated from actual SPR489 interpolation rows and serialized coefficients.",
                "The small positive common-mode state has pA approximately 4.342299e-4 mm and q approximately +1.6493e-6 mm; its expected endpoint force is k*q.",
                "A negative-q state verifies the open side has zero unilateral force.",
                "For q=pB-pA, physical action on original first owner is +f*n and second owner is -f*n.",
                "Nodal owner forces and first moments are explicitly summed from source interpolation weights and compared to the same preserved owner point/axis.",
                "Manufactured CLOADs include only the fixture linear support and joint force needed for the analytic prescribed displacement state; no frame/source response loads are transferred.",
            ],
            "states": coupon_model["known_answer_states"],
            "limits": coupon_model["limits"],
        }, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
        "README.md": readme_content(trace, coupon_model, pins).encode(),
    }
    for name, content in outputs.items():
        if name == "source-pins.json":
            continue
        pins["output_files"][name] = hashlib.sha256(content).hexdigest()
    outputs["source-pins.json"] = (json.dumps(pins, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    return outputs


def coefficient_delta(pruned_row: list[list[float]], unpruned_row: list[list[float]]) -> list[dict[str, Any]]:
    p = {(int(n), int(d)): float(c) for n, d, c in pruned_row}
    u = {(int(n), int(d)): float(c) for n, d, c in unpruned_row}
    return [{"dof": [n, d], "pruned_minus_unpruned": p.get((n, d), 0.0) - u.get((n, d), 0.0)}
            for n, d in sorted(set(p) | set(u)) if p.get((n, d), 0.0) != u.get((n, d), 0.0)]


def readme_content(trace: dict[str, Any], coupon: dict[str, Any], pins: dict[str, Any]) -> str:
    replay = trace["replay"]
    drops = Counter(x["equation_index_zero_based"] for x in replay["independent_terms_pruned"])
    y_i = next(x for x in trace["dependency_closure_rows_in_actual_source_order"] if x["dependent_dof"] == [19800, 2])["equation_index_zero_based"]
    z_i = next(x for x in trace["dependency_closure_rows_in_actual_source_order"] if x["dependent_dof"] == [19800, 3])["equation_index_zero_based"]
    state02 = next(x for x in replay["all_seven_DAT_states"] if x["load_factor"] == 0.2)
    y_delta = state02["qghost_y"]["pruning_induced_qghost_prediction_delta_mm"]
    z_delta = state02["qghost_z"]["pruning_induced_qghost_prediction_delta_mm"]
    scalar_delta = state02["qghost_scalar_axis_projection_pruned_minus_unpruned_mm"]
    state0 = coupon["known_answer_states"][0]
    return f"""# SPR489 cascade replay and direct-scalar coupon input

This packet records a source-pinned replay of the exact SPR489 qghost MPC
dependency closure in K12-rear attempt03, then prepares one source-interpolation
direct-scalar SPRINGA known-answer coupon. All artifacts here are diagnostic or
input-only. This packet contains no native run, freeze, response-force adoption,
floor-support qualification, or joint acceptance.

The closure has {len(trace['dependency_closure_equation_indices_zero_based'])} rows,
replayed in emitted equation order. The replay converges in
{replay['sweeps_until_fixed_point']} substitution sweeps; it takes
{replay['substitution_count']} replacements. No dependent coefficient is
repaired. The independent cutoff deletes
{len(replay['independent_terms_pruned'])} terms: row 9360 drops
{drops[9360]}, qghost-y row {y_i} drops {drops[y_i]}, and qghost-z row {z_i}
drops {drops[z_i]}. No selected-floor equation appears in the closure.

At the rejected 0.2 state, the source-faithful replay predicts qghost-y
{y_delta:.12g} mm and qghost-z {z_delta:.12g} mm of pruning-induced coordinate
change; the scalar axis projection changes by {scalar_delta:.12g} mm. The
recorded strict scalar interval excess is
{trace['diagnostic_link']['strict_scalar_interval_excess_mm']:.12g} mm. The
pruning change is material to the exception but does not fully explain it; this
is a candidate mechanism, not exclusive native causality. The seven-state
printed-U residuals, per-row token radii, coefficient deltas, drop records and
source-loop steps are in `cascade-trace.json`.

The coupon uses the same SPR489 owner order, contact point, unit normal,
stiffness, and actual two 20-node interpolation coefficient sets. It replaces
only the nested interpolation/projection/qghost representation with one direct
scalar equation over the original 80 independent master DOFs. Its first state
has common first-point translation {state0['pA_target_mm']:.10g} mm and serialized
equation q {state0['serialized_equation_q_mm']:.12g} mm, with expected endpoint
force {state0['native_force_expected_N']:.12g} N. It also includes a negative-q
open state and a +0.01 mm closed control. The direct row retains all 80 source
DOFs; no qghost, projection slave, or interpolated slave node appears in that
row. The manufactured loads, expected nodal actions, force and moment
resultants, and DAT-token q/force intervals are in
`direct-scalar-coupon/model.json` and `analytic-check.json`.

`cascade-source-excerpt.txt` contains the exact relevant source lines from the
hash-pinned CCX 2.23 `cascade.c`. The producer verifies the archive/member
hashes, source input hashes, owner binding, and the equation closure before
writing. Reproduce or check without running CalculiX:

```bash
.venv/bin/python {relative(HERE / 'produce.py')} --write
.venv/bin/python {relative(HERE / 'produce.py')} --check
```

The native relative-coordinate sign convention is cross-referenced to the
already run bounded method coupon at
`{relative(REL_FIXTURE)}`; this packet does not rerun it. Parent owns any later
freeze and native execution.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="write the deterministic input-only packet")
    group.add_argument("--check", action="store_true", help="verify packet outputs without native execution")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.write:
        for relative_name, content in outputs.items():
            path = HERE / relative_name
            if path.exists():
                raise RuntimeError(f"Refusing to overwrite existing packet output: {relative(path)}")
        for relative_name, content in outputs.items():
            path = HERE / relative_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print("Wrote source-pinned cascade trace and direct-scalar coupon inputs only; no native run or freeze.")
        return
    for relative_name, content in outputs.items():
        path = HERE / relative_name
        if not path.is_file() or path.read_bytes() != content:
            raise RuntimeError(f"Prepared output mismatch: {relative(path)}")
    print("PASS: deterministic source-pinned trace and coupon input artifacts match; no native run.")


if __name__ == "__main__":
    main()
