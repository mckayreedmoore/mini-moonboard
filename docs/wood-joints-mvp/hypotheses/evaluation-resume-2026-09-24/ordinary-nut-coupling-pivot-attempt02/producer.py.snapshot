"""Equivalent sparse dependency ordering for the frozen six-DOF nut fit.

Keep each nut's six rigid controls independent and eliminate six shaft DOFs
instead. The equality row space is unchanged; this avoids substituting the
full shaft fit into every rigid carrier node during native MPC cascading.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.linalg import qr


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_equations(text):
    lines = text.splitlines()
    equations = []
    index = 0
    while index < len(lines):
        if lines[index].upper() != "*EQUATION":
            index += 1
            continue
        count = int(lines[index + 1])
        index += 2
        terms = []
        while len(terms) < count:
            cells = lines[index].split(",")
            if len(cells) % 3 or len(cells) > 12:
                raise ValueError("invalid equation card")
            for offset in range(0, len(cells), 3):
                if len(cells[offset + 2]) > 20:
                    raise ValueError("coefficient overflows native f20.0 field")
                terms.append(
                    (
                        int(cells[offset]),
                        int(cells[offset + 1]),
                        float(cells[offset + 2]),
                    )
                )
            index += 1
        if len(terms) != count:
            raise ValueError("incorrect equation term count")
        equations.append(terms)
    return equations


def pivot_fit(matrix):
    """Return exact row operations for c=A*x with six stable physical pivots."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape[0] != 6 or matrix.shape[1] < 6 or not np.isfinite(matrix).all():
        raise ValueError("expected finite six-row fit")
    scale = np.array((1, 1, 1, 3.175, 3.175, 3.175))
    scaled = scale[:, None] * matrix
    _, _, permutation = qr(scaled, pivoting=True, mode="economic")
    pivots = permutation[:6]
    if np.linalg.matrix_rank(scaled[:, pivots]) != 6:
        raise ValueError("six physical pivot DOFs do not span the fit")
    condition = float(np.linalg.cond(scaled[:, pivots]))
    if not np.isfinite(condition) or condition > 1e4:
        raise ValueError("poor physical pivot conditioning")
    inverse = np.linalg.solve(matrix[:, pivots], np.eye(6))
    # Original E=[-A I]. New E=[inv(AP) A -inv(AP)] = -inv(AP) E.
    transformed = np.column_stack((inverse @ matrix, -inverse))
    transformed[:, pivots] = np.eye(6)
    original = np.column_stack((-matrix, np.eye(6)))
    error = float(np.max(np.abs(transformed + inverse @ original)))
    if error > 1e-10:
        raise ValueError("equation row-space equivalence failed")
    return pivots, transformed, inverse, condition, error


def prepare(source_directory, output_directory):
    source, output = Path(source_directory), Path(output_directory)
    raw = (source / "nut-coupling.inp").read_text()
    report = json.loads((source / "nut-coupling.json").read_text())
    hashes = {
        name: digest(source / name)
        for name in ("nut-coupling.inp", "nut-coupling.json")
    }
    if hashes["nut-coupling.inp"] != report["include_file_sha256"]:
        raise ValueError("source nut fit is not authenticated")
    equations = parse_equations(raw)
    if len(equations) != 24:
        raise ValueError("expected four sets of six source equations")
    prefix = raw[: raw.index("*EQUATION")]
    cards = [
        prefix.rstrip(),
        "** Equivalent physical-pivot dependency order; original fit unchanged.",
    ]
    audits, summaries = [], []
    new_dependents = set()
    for nut_index, row in enumerate(report["per_nut"]):
        original = equations[6 * nut_index : 6 * nut_index + 6]
        control_pairs = [terms[0][:2] for terms in original]
        ref, rot = report["nsets"][row["control_node_sets"]["rigid_control_nset"]]
        if control_pairs != [(node, dof) for node in (ref, rot) for dof in (1, 2, 3)]:
            raise ValueError("source fit control order changed")
        physical = sorted({term[:2] for terms in original for term in terms[1:]})
        indices = {key: index for index, key in enumerate(physical)}
        matrix = np.zeros((6, len(physical)))
        for index, terms in enumerate(original):
            if terms[0][2] != 1.0:
                raise ValueError("source control coefficient must equal one")
            for node, dof, coefficient in terms[1:]:
                matrix[index, indices[(node, dof)]] = -coefficient
        pivots, transformed, inverse, condition, error = pivot_fit(matrix)
        all_pairs = physical + control_pairs
        rendered = np.zeros_like(transformed)
        for index, pivot in enumerate(pivots):
            dependent = physical[pivot]
            if dependent in new_dependents:
                raise ValueError("duplicate physical dependent DOF")
            new_dependents.add(dependent)
            ordering = [int(pivot)] + [
                i
                for i in range(len(all_pairs))
                if i != pivot and transformed[index, i] != 0
            ]
            terms = []
            for column in ordering:
                field = f"{transformed[index, column]:.13e}"
                if len(field) > 20:
                    raise ValueError("transformed coefficient exceeds f20.0 width")
                rendered[index, column] = float(field)
                node, dof = all_pairs[column]
                terms.append(f"{node},{dof},{field}")
            cards.extend(("*EQUATION", str(len(terms))))
            cards.extend(
                ",".join(terms[start : start + 4]) for start in range(0, len(terms), 4)
            )
            summaries.append(
                {
                    "physical_bolt_id": row["physical_bolt_id"],
                    "dependent_node_id": dependent[0],
                    "dependent_dof": dependent[1],
                    "term_count": len(terms),
                }
            )
        expected = -inverse @ np.column_stack((-matrix, np.eye(6)))
        relative = float(np.max(np.abs(rendered - expected)) / np.max(np.abs(expected)))
        if relative > 1e-12:
            raise ValueError("serialized equation row space changed")
        # Independent non-rigid states exercise the entire linear relation,
        # rather than only rigid motions which the fit was designed to match.
        trial = np.random.default_rng(472 + nut_index).normal(size=(len(physical), 12))
        state = np.vstack((trial, matrix @ trial))
        residual = float(np.max(np.abs(rendered @ state)))
        if residual > 1e-10:
            raise ValueError("serialized equations reject an original admissible state")
        audits.append(
            {
                "bolt_id": row["physical_bolt_id"],
                "dependent_shaft_dofs": [list(physical[i]) for i in pivots],
                "scaled_pivot_condition_number": condition,
                "unserialized_equivalence_max_abs_error": error,
                "serialized_row_space_relative_error": relative,
                "serialized_admissible_state_max_abs_residual": residual,
            }
        )
    result = "\n".join(cards) + "\n"
    report["status"] = "EQUIVALENT_PHYSICAL_PIVOT_NUT_COUPLING_INPUT_ONLY"
    report["equation_cards"] = summaries
    report["include_file_sha256"] = hashlib.sha256(result.encode()).hexdigest()
    report["artifacts"] = {"nut-coupling.inp": report["include_file_sha256"]}
    report["fresh_control_node_allocation"]["all_dependent_control_dofs_unique"] = False
    report["fresh_control_node_allocation"]["controls_are_independent_in_equations"] = (
        True
    )
    report["equivalent_dependency_reparameterization"] = {
        "source_directory": str(source),
        "source_sha256": hashes,
        "producer_sha256": digest(Path(__file__)),
        "per_nut": audits,
        "original_fit_and_equality_row_space_preserved": True,
        "only_dependency_order_changed": True,
        "physical_model_changed": False,
        "reason": "Avoid cascading dense shaft-fit coefficients into every rigid seat carrier node.",
    }
    if hashes != {name: digest(source / name) for name in hashes}:
        raise ValueError("source changed during reparameterization")
    output.mkdir(parents=True, exist_ok=False)
    (output / "nut-coupling.inp").write_text(result)
    (output / "nut-coupling.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return audits
