"""Source-bound rigid-body branch/rank screen; no native solve or FE kernel."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
ADAPTER = BASE / "current-springa-frame-input-adapter-attempt01"
MODEL = ADAPTER / "a12-rear/model.json"
DECK = ADAPTER / "a12-rear/model.inp"
FLOOR_AUDIT = BASE / "current-floor-stick-constraint-audit-attempt01/audit.json"
FLOOR_MATRIX = BASE / "current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz"

RELATIVE_CUTOFFS = (1e-8, 1e-10, 1e-12, 1e-14)
ROTATION_LENGTH_MM = 1000.0
EXPANSION_PRUNE = 1e-13

# These source pins include the method context as well as the exact input data
# used by this bounded mechanism screen. A change requires an intentional audit
# update rather than silently inheriting a newer model.
PINNED_SHA256 = {
    str(ADAPTER / "source-pins.json"): "3242284af13f7e7d4f5fbe3ca68d22bd76533f2428a8080053f27569278ce228",
    str(ADAPTER / "prepare.py"): "b3fd2371fe36eceb4fe7111241130e565eacf4ce94dbfef4eeb2ed7104a80c4a",
    str(MODEL): "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    str(DECK): "11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c",
    str(ADAPTER / "a12-rear/audit.json"): "1570e9680ae09e1437baa225667806c4e1c7380eac2ddddbd633f342c15a778f",
    str(FLOOR_AUDIT): "43b5aa99468b1577cd273baddafe47955b235fa00ddd5b9d5aff91d490695c95",
    str(FLOOR_MATRIX): "4fcc630274e2f1c7166c811d2aa97a3f075d60b5724600b88be73afebe308f6e",
    str(BASE / "current-floor-stick-constraint-audit-attempt01/produce.py"): "0970076aacea039a89c3afdd8448eb75e82dcd7c9b7a91629d048abdc0f0d5e6",
    str(BASE / "current-gravity-settle-climber-ramp-scenario-attempt01/scenario-contract.json"): "f0eb875f53aeee99f98f567ba0ff8260771860254176cc0b9aa56fbbd05bb9ca",
    str(BASE / "current-gravity-settle-climber-ramp-scenario-attempt01/decomposition.json"): "39d1530ee888bb824c2bd1624072890385c19a1448f4d146567a041aff5d14dc",
    str(BASE / "current-gravity-settle-climber-ramp-scenario-attempt01/README.md"): "8e9deda6c758a1bbcb9ee045ed33ac6019bf9ea646f1423d166bdff7e91628ce",
    str(BASE / "current-global-floor-wrench-screen-attempt01/floor-wrench-screen.json"): "0e04b1f129462077e3ff9bdd369f77caba2f3eb5ca61147f922dc4bbe4ca9d9f",
    str(BASE / "current-global-floor-wrench-screen-attempt01/README.md"): "e2cfb188aa6dfe950d284dee85af24ee7405743788e63161827c7f13da98ef8e",
    str(BASE / "current-floor-staged-reference-native-attempt01/parent-staged-assessment.json"): "5d8aafe1097850057e0f18ede01fa8a61f2ace52dc73c3a9743c5a785ea6e783",
    str(BASE / "current-floor-staged-reference-native-attempt01/README.md"): "61002716b00c9d83713cc993561784476d01432e35a64a176032420956dc7346",
}


class AuditError(ValueError):
    """Raised when a pinned source or rigid-body mapping is inconsistent."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_pins() -> dict[str, dict[str, str]]:
    observed: dict[str, dict[str, str]] = {}
    for relative, expected in PINNED_SHA256.items():
        path = ROOT / relative
        if not path.is_file():
            raise AuditError(f"Missing pinned input: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise AuditError(f"Pinned input changed: {relative}: {actual} != {expected}")
        observed[relative] = {"sha256": actual}
    return observed


def independent_rank(matrix: np.ndarray, relative_cutoff: float = 1e-10) -> dict[str, Any]:
    """Rank after explicit row and column equilibration; report zero rows/columns."""
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2:
        raise AuditError("Rank input is not a matrix")
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        return {
            "rows": int(matrix.shape[0]),
            "columns": int(matrix.shape[1]),
            "zero_rows": int(matrix.shape[0]),
            "zero_columns": int(matrix.shape[1]),
            "rank": 0,
            "nullity": int(matrix.shape[1]),
            "relative_cutoff": relative_cutoff,
            "largest_scaled_singular_value": 0.0,
            "smallest_scaled_singular_value": 0.0,
        }

    row_norms = np.linalg.norm(matrix, axis=1)
    kept_rows = row_norms > 1e-14
    row_scaled = matrix[kept_rows] / row_norms[kept_rows, None]
    if row_scaled.shape[0] == 0:
        return {
            "rows": int(matrix.shape[0]),
            "columns": int(matrix.shape[1]),
            "zero_rows": int(matrix.shape[0]),
            "zero_columns": int(matrix.shape[1]),
            "rank": 0,
            "nullity": int(matrix.shape[1]),
            "relative_cutoff": relative_cutoff,
            "largest_scaled_singular_value": 0.0,
            "smallest_scaled_singular_value": 0.0,
        }

    column_norms = np.linalg.norm(row_scaled, axis=0)
    kept_columns = column_norms > 1e-14
    column_scaled = np.zeros_like(row_scaled)
    column_scaled[:, kept_columns] = row_scaled[:, kept_columns] / column_norms[kept_columns]
    singular = np.linalg.svd(column_scaled, compute_uv=False)
    largest = float(singular[0]) if len(singular) else 0.0
    rank = int(np.count_nonzero(singular > largest * relative_cutoff)) if largest else 0
    return {
        "rows": int(matrix.shape[0]),
        "columns": int(matrix.shape[1]),
        "zero_rows": int((~kept_rows).sum()),
        "zero_columns": int((~kept_columns).sum()),
        "rank": rank,
        "nullity": int(matrix.shape[1] - rank),
        "relative_cutoff": relative_cutoff,
        "largest_scaled_singular_value": largest,
        "smallest_scaled_singular_value": float(singular[-1]) if len(singular) else 0.0,
    }


def rank_sensitivity(matrix: np.ndarray) -> dict[str, Any]:
    reports = [independent_rank(matrix, cutoff) for cutoff in RELATIVE_CUTOFFS]
    return {
        "method": "Dense SVD after unit-row and unit-column equilibration; no stiffness weighting.",
        "relative_cutoffs": [format(value, ".0e") for value in RELATIVE_CUTOFFS],
        "rank_by_relative_cutoff": {
            format(value, ".0e"): report["rank"]
            for value, report in zip(RELATIVE_CUTOFFS, reports, strict=True)
        },
        "nullity_by_relative_cutoff": {
            format(value, ".0e"): report["nullity"]
            for value, report in zip(RELATIVE_CUTOFFS, reports, strict=True)
        },
        "rows": reports[0]["rows"],
        "columns": reports[0]["columns"],
        "zero_rows": reports[0]["zero_rows"],
        "zero_columns": reports[0]["zero_columns"],
        "smallest_scaled_singular_value": reports[0]["smallest_scaled_singular_value"],
    }


def rigid_row_from_nodal_terms(
    terms: dict[tuple[int, int], float],
    *,
    nodes: dict[int, np.ndarray],
    body_of: dict[int, str],
    datums: dict[str, np.ndarray],
    body_index: dict[str, int],
    rotation_length_mm: float = ROTATION_LENGTH_MM,
) -> np.ndarray:
    """Map a scalar nodal displacement row to six rigid coordinates per body."""
    output = np.zeros(6 * len(body_index), dtype=float)
    for (node, dof), coefficient in terms.items():
        body = body_of.get(int(node))
        if body is None:
            raise AuditError(f"Unowned physical master DOF in row: node={node}, dof={dof}")
        if dof not in (1, 2, 3):
            raise AuditError(f"Nontranslational source DOF in row: node={node}, dof={dof}")
        relative = (nodes[int(node)] - datums[body]) / rotation_length_mm
        start = 6 * body_index[body]
        output[start + dof - 1] += coefficient
        if dof == 1:
            output[start + 4] += coefficient * relative[2]
            output[start + 5] -= coefficient * relative[1]
        elif dof == 2:
            output[start + 3] -= coefficient * relative[2]
            output[start + 5] += coefficient * relative[0]
        else:
            output[start + 3] += coefficient * relative[1]
            output[start + 4] -= coefficient * relative[0]
    return output


def run_rank_oracles() -> dict[str, Any]:
    """Check six free-body modes and a two-body relative spin mechanism first."""
    free = np.zeros((0, 6), dtype=float)
    free_rank = independent_rank(free)
    if (free_rank["rank"], free_rank["nullity"]) != (0, 6):
        raise AuditError("Free-body rank oracle failed")

    fixture_nodes = {
        1: np.array([0.0, 0.0, 0.0]),
        2: np.array([0.0, 0.0, 0.0]),
        3: np.array([1.0, 0.0, 0.0]),
        4: np.array([1.0, 0.0, 0.0]),
    }
    fixture_bodies = ["A", "B"]
    fixture_index = {name: i for i, name in enumerate(fixture_bodies)}
    fixture_body_of = {1: "A", 3: "A", 2: "B", 4: "B"}
    fixture_datums = {"A": np.zeros(3), "B": np.zeros(3)}
    fixture_rows = []
    for dof in (1, 2, 3):
        fixture_rows.append(
            rigid_row_from_nodal_terms(
                {(1, dof): -1.0, (2, dof): 1.0},
                nodes=fixture_nodes,
                body_of=fixture_body_of,
                datums=fixture_datums,
                body_index=fixture_index,
                rotation_length_mm=1.0,
            )
        )
    for dof in (2, 3):
        fixture_rows.append(
            rigid_row_from_nodal_terms(
                {(3, dof): -1.0, (4, dof): 1.0},
                nodes=fixture_nodes,
                body_of=fixture_body_of,
                datums=fixture_datums,
                body_index=fixture_index,
                rotation_length_mm=1.0,
            )
        )
    mechanism = independent_rank(np.asarray(fixture_rows))
    if (mechanism["rank"], mechanism["nullity"]) != (5, 7):
        raise AuditError("Two-body one-extra-mechanism rank oracle failed")
    return {
        "free_single_body": {
            "body_rigid_dofs": 6,
            "constraint_rows": 0,
            "rank": free_rank["rank"],
            "nullity": free_rank["nullity"],
            "expected": {"rank": 0, "nullity": 6},
            "passed": True,
        },
        "two_bodies_with_five_relative_ties": {
            "body_rigid_dofs": 12,
            "constraint_rows": 5,
            "ties": [
                "three relative translations at a shared point",
                "two relative translations at a second point on the x axis",
            ],
            "remaining_mechanism": "relative spin about the x axis",
            "rank": mechanism["rank"],
            "nullity": mechanism["nullity"],
            "expected": {"rank": 5, "nullity": 7},
            "passed": True,
        },
    }


def build_model_rows(model: dict[str, Any]) -> dict[str, Any]:
    nodes = {int(tag): np.asarray(xyz, dtype=float) for tag, xyz in model["nodes"].items()}
    bodies = sorted(model["physical_body_nodes"])
    body_index = {name: index for index, name in enumerate(bodies)}
    body_of: dict[int, str] = {}
    for body, tags in model["physical_body_nodes"].items():
        for tag in tags:
            node = int(tag)
            if node in body_of:
                raise AuditError(f"Physical node belongs to multiple bodies: {node}")
            body_of[node] = body
    if len(body_of) != sum(len(tags) for tags in model["physical_body_nodes"].values()):
        raise AuditError("Physical body node partition is not unique")
    datums = {
        body: np.mean([nodes[int(tag)] for tag in model["physical_body_nodes"][body]], axis=0)
        for body in bodies
    }

    fixed_nodes = set(map(int, model["fixed_nodes"]))
    fixed_dofs = {(node, dof) for node in fixed_nodes for dof in (1, 2, 3)}
    floor_support_nodes = set(map(int, model["floor_support_nodes"]))
    conditional_floor_keys = {
        tuple(map(int, row["dependent_physical_pivot_dof"]))
        for row in model["exact_floor_mpc_equations"]
    }
    equations: dict[tuple[int, int], list[list[float]]] = {}
    for terms in model["equations"]:
        key = (int(terms[0][0]), int(terms[0][1]))
        if key in equations:
            raise AuditError(f"Duplicate equation pivot in model: {key}")
        equations[key] = terms
    if not conditional_floor_keys.issubset(equations):
        raise AuditError("Conditional floor pivot set is not present in serialized equations")
    if fixed_dofs.intersection(equations):
        raise AuditError("An SPC DOF is also an equation-dependent DOF")
    permanent_equations = {
        key: terms for key, terms in equations.items() if key not in conditional_floor_keys
    }

    cache: dict[tuple[int, int], dict[tuple[int, int], float]] = {}
    visiting: set[tuple[int, int]] = set()

    def expand(key: tuple[int, int]) -> dict[tuple[int, int], float]:
        if key in cache:
            return cache[key]
        if key in visiting:
            raise AuditError(f"Circular permanent MPC at {key}")
        visiting.add(key)
        if key in fixed_dofs:
            result: dict[tuple[int, int], float] = {}
        elif key not in permanent_equations:
            result = {key: 1.0}
        else:
            terms = permanent_equations[key]
            denominator = float(terms[0][2])
            if denominator == 0.0:
                raise AuditError(f"Zero equation pivot coefficient at {key}")
            result = {}
            for node, dof, coefficient in terms[1:]:
                for master, weight in expand((int(node), int(dof))).items():
                    result[master] = result.get(master, 0.0) - float(coefficient) * weight / denominator
            result = {master: weight for master, weight in result.items() if abs(weight) > EXPANSION_PRUNE}
        visiting.remove(key)
        cache[key] = result
        return result

    def difference(first: int, second: int, dof: int) -> dict[tuple[int, int], float]:
        result = expand((int(second), int(dof))).copy()
        for key, value in expand((int(first), int(dof))).items():
            result[key] = result.get(key, 0.0) - value
        return {key: value for key, value in result.items() if abs(value) > EXPANSION_PRUNE}

    def fixed_floor_master_nodes(key: tuple[int, int]) -> set[int]:
        """Trace an MPC projection to its fixed floor endpoint node, if any."""
        active: set[tuple[int, int]] = set()

        def visit(current: tuple[int, int]) -> set[int]:
            if current in fixed_dofs:
                return {current[0]} if current[0] in floor_support_nodes else set()
            if current not in permanent_equations:
                return set()
            if current in active:
                raise AuditError(f"Circular permanent MPC while tracing floor endpoint at {current}")
            active.add(current)
            found: set[int] = set()
            for node, dof, coefficient in permanent_equations[current][1:]:
                if abs(float(coefficient)) > EXPANSION_PRUNE:
                    found.update(visit((int(node), int(dof))))
            active.remove(current)
            return found

        return visit(key)

    bilateral_rows: list[np.ndarray] = []
    bilateral_names: set[str] = set()
    for spring in model["springs"]:
        if spring["group"] in bilateral_names:
            raise AuditError(f"Duplicate permanent spring group: {spring['group']}")
        bilateral_names.add(spring["group"])
        if float(spring["stiffness_n_per_mm"]) <= 0.0:
            raise AuditError(f"Nonpositive bilateral spring stiffness: {spring['name']}")
        terms = difference(int(spring["nodes"][0]), int(spring["nodes"][1]), int(spring["dof"]))
        bilateral_rows.append(
            rigid_row_from_nodal_terms(
                terms,
                nodes=nodes,
                body_of=body_of,
                datums=datums,
                body_index=body_index,
            )
        )

    source_rows = model["raw_source_carrier_law_inventory_rows"]
    law_counts = Counter(str(row["intended_law"]) for row in source_rows)
    unilateral_rows: list[np.ndarray] = []
    q_map_max_error = 0.0
    q_length_max_error = 0.0
    right_slope_max_error = 0.0
    left_force_max_abs = 0.0
    zero_force_max_abs = 0.0
    unilateral_names: set[str] = set()
    ground_nodes: set[int] = set()
    floor_normal_projection_count = 0
    floor_normal_endpoint_nodes: set[int] = set()
    element_map = model["elements"]
    for binding in model["unilateral_springa_bindings"]:
        name = str(binding["name"])
        if name in unilateral_names:
            raise AuditError(f"Duplicate unilateral source row: {name}")
        unilateral_names.add(name)
        inventory_index = int(binding["source_inventory_row_index"])
        source = source_rows[inventory_index]
        if (
            source["name"] != name
            or list(map(int, source["nodes"])) != list(map(int, binding["source_projection_nodes"]))
            or int(source["dof"]) != int(binding["source_projection_dof"])
        ):
            raise AuditError(f"Unilateral projection row does not rejoin source inventory: {name}")
        first, ground = map(int, binding["springa_nodes"])
        if (ground, 1) not in fixed_dofs or ground in body_of:
            raise AuditError(f"SPRINGA ground endpoint is not a fixed numerical node: {name}")
        ground_nodes.add(ground)
        element = element_map[str(int(binding["source_element"]))]
        if element[0] != "SPRINGA" or list(map(int, element[1])) != [first, ground]:
            raise AuditError(f"SPRINGA node mapping changed: {name}")
        if not bool(binding["ground_endpoint_is_numerical_only"]):
            raise AuditError(f"SPRINGA endpoint is not marked numerical-only: {name}")

        source_terms = difference(
            int(binding["source_projection_nodes"][0]),
            int(binding["source_projection_nodes"][1]),
            int(binding["source_projection_dof"]),
        )
        if source.get("physical_owner", {}).get("role") == "floor_normal":
            # The source floor endpoint is an SPC-fixed independent master of
            # the attachment projection. Its effect must survive as a
            # body-to-fixed-floor displacement in this one-sided support row.
            first_projection = (
                int(binding["source_projection_nodes"][0]),
                int(binding["source_projection_dof"]),
            )
            second_projection = (
                int(binding["source_projection_nodes"][1]),
                int(binding["source_projection_dof"]),
            )
            first_expansion = expand(first_projection)
            if not first_expansion or any(node not in body_of for node, _ in first_expansion):
                raise AuditError(f"Floor normal body-side projection did not expand to physical-body DOFs: {name}")
            if expand(second_projection):
                raise AuditError(f"Fixed floor normal endpoint did not eliminate to zero: {name}")
            endpoint_nodes = fixed_floor_master_nodes(second_projection)
            if len(endpoint_nodes) != 1 or not endpoint_nodes.issubset(floor_support_nodes):
                raise AuditError(f"Floor normal projection did not reach one fixed floor endpoint: {name}")
            if floor_normal_endpoint_nodes.intersection(endpoint_nodes):
                raise AuditError(f"Multiple floor normal rows unexpectedly share one floor endpoint: {name}")
            floor_normal_endpoint_nodes.update(endpoint_nodes)
            if any(node not in body_of for node, _ in source_terms):
                raise AuditError(f"Expanded floor normal row has a nonphysical master: {name}")
            floor_normal_projection_count += 1
        spring_axis = nodes[ground] - nodes[first]
        initial_length = float(np.linalg.norm(spring_axis))
        if initial_length == 0.0:
            raise AuditError(f"Zero initial SPRINGA length: {name}")
        spring_axis /= initial_length
        native_terms: dict[tuple[int, int], float] = {}
        for dof in (1, 2, 3):
            for master, weight in expand((first, dof)).items():
                native_terms[master] = native_terms.get(master, 0.0) - float(spring_axis[dof - 1]) * weight
        all_keys = set(source_terms) | set(native_terms)
        mapping_error = max(
            (abs(source_terms.get(key, 0.0) - native_terms.get(key, 0.0)) for key in all_keys),
            default=0.0,
        )
        q_map_max_error = max(q_map_max_error, mapping_error)
        q_length_max_error = max(q_length_max_error, abs(initial_length - float(binding["initial_span_mm"])))
        if mapping_error > 1e-8:
            raise AuditError(f"SPRINGA projected extension does not match source row: {name}")
        if abs(initial_length - float(binding["initial_span_mm"])) > 1e-8:
            raise AuditError(f"SPRINGA initial span changed: {name}")

        table = binding["force_vs_elongation_table_N_mm"]
        if len(table) != 3 or list(map(float, table[1])) != [0.0, 0.0]:
            raise AuditError(f"Expected a zero-force SPRINGA breakpoint at q=0: {name}")
        left_force, left_q = map(float, table[0])
        right_force, right_q = map(float, table[2])
        if left_q >= 0.0 or right_q <= 0.0:
            raise AuditError(f"SPRINGA table does not bracket q=0: {name}")
        left_force_max_abs = max(left_force_max_abs, abs(left_force))
        zero_force_max_abs = max(zero_force_max_abs, abs(float(table[1][0])))
        slope_error = abs(right_force / right_q - float(binding["stiffness_n_per_mm"]))
        right_slope_max_error = max(right_slope_max_error, slope_error)
        if abs(left_force) > 1e-12 or abs(float(table[1][0])) > 1e-12 or slope_error > 1e-8:
            raise AuditError(f"Unexpected unilateral table branch at q=0: {name}")

        unilateral_rows.append(
            rigid_row_from_nodal_terms(
                source_terms,
                nodes=nodes,
                body_of=body_of,
                datums=datums,
                body_index=body_index,
            )
        )

    if len(bilateral_rows) != 348 or len(unilateral_rows) != 1292:
        raise AuditError("Source spring law row totals changed")
    if floor_normal_projection_count != 100:
        raise AuditError("Expected exactly 100 floor-normal rows to retain fixed-endpoint projection effects")
    if len(floor_normal_endpoint_nodes) != 100 or floor_normal_endpoint_nodes != floor_support_nodes:
        raise AuditError("The 100 floor-normal rows no longer map one-to-one to the 100 fixed floor endpoints")
    if dict(law_counts) != {
        "bilateral": 348,
        "compression_only": 1122,
        "floor_tangent_all_bearing_hypothesis": 200,
        "tension_only": 170,
    }:
        raise AuditError(f"Source carrier-law counts changed: {dict(law_counts)}")

    physical_nodes = set(body_of)
    numerical_ground_nodes = {int(row["node"]) for row in model["numerical_spring_ground_nodes"]}
    floor_reference_nodes = {int(row["node"]) for row in model["floor_reference_nodes"]}
    if ground_nodes != numerical_ground_nodes or len(ground_nodes) != 1292:
        raise AuditError("SPRINGA numerical-ground endpoint set changed")
    if len(floor_reference_nodes) != 200 or len(floor_support_nodes) != 100:
        raise AuditError("Conditional floor-reference/support node counts changed")
    if ground_nodes & floor_reference_nodes or ground_nodes & floor_support_nodes or floor_reference_nodes & floor_support_nodes:
        raise AuditError("Fixed numerical node classes overlap")
    if fixed_nodes != ground_nodes | floor_reference_nodes | floor_support_nodes:
        raise AuditError("Fixed-node/SPC inventory has an unclassified or missing node")
    if fixed_nodes & physical_nodes:
        raise AuditError("A physical body node is fixed by the serialized SPC set")
    if not floor_reference_nodes.issubset(fixed_nodes) or not floor_support_nodes.issubset(fixed_nodes):
        raise AuditError("Conditional floor or support bookkeeping nodes lost their SPCs")

    element_nodes = {
        int(node)
        for _, connectivity, _ in model["elements"].values()
        for node in connectivity
    }
    equation_nodes = {
        int(term[0])
        for equation in model["equations"]
        for term in equation
    }
    floor_support_term_count_by_node = Counter(
        int(term[0])
        for equation in model["equations"]
        for term in equation[1:]
        if int(term[0]) in floor_support_nodes
    )
    floor_support_term_count_by_dof = Counter(
        int(term[1])
        for equation in model["equations"]
        for term in equation[1:]
        if int(term[0]) in floor_support_nodes
    )
    floor_support_equation_rows = [
        equation
        for equation in model["equations"]
        if any(int(term[0]) in floor_support_nodes for term in equation[1:])
    ]
    if floor_support_nodes & element_nodes:
        raise AuditError("A fixed floor endpoint was inserted into a physical element")
    if set(floor_support_term_count_by_node) != floor_support_nodes or any(
        count != 3 for count in floor_support_term_count_by_node.values()
    ):
        raise AuditError("Fixed floor endpoints are not each represented by three source projection terms")
    if floor_support_term_count_by_dof != Counter({1: 100, 2: 100, 3: 100}):
        raise AuditError("Fixed floor endpoint terms no longer cover one occurrence per DOF")
    if any(
        int(equation[0][0]) in floor_support_nodes
        or tuple(map(int, equation[0][:2])) in conditional_floor_keys
        for equation in floor_support_equation_rows
    ):
        raise AuditError("A fixed floor endpoint became an equation pivot or conditional floor row")
    for node in floor_reference_nodes:
        if node not in equation_nodes:
            raise AuditError("A floor reference node is absent from conditional floor equations")
    for equation in model["equations"]:
        if any(int(term[0]) in floor_reference_nodes for term in equation) and tuple(
            map(int, equation[0][:2])
        ) not in conditional_floor_keys:
            raise AuditError("A fixed captured-reference node escaped into a permanent projection row")

    # Check the spring rows directly against the source body partition.
    for row in [*bilateral_rows, *unilateral_rows]:
        if row.shape != (6 * len(bodies),):
            raise AuditError("Rigid-body spring row has the wrong width")
    if len(physical_nodes) != 12549 or len(bodies) != 50:
        raise AuditError("Current source physical-body inventory changed")

    return {
        "nodes": nodes,
        "bodies": bodies,
        "body_index": body_index,
        "body_of": body_of,
        "datums": datums,
        "bilateral_rows": np.asarray(bilateral_rows, dtype=float),
        "unilateral_rows": np.asarray(unilateral_rows, dtype=float),
        "floor_reference_nodes": floor_reference_nodes,
        "floor_support_nodes": floor_support_nodes,
        "floor_support_term_count_by_node": floor_support_term_count_by_node,
        "floor_support_term_count_by_dof": floor_support_term_count_by_dof,
        "floor_support_equation_row_count": len(floor_support_equation_rows),
        "floor_normal_projection_count": floor_normal_projection_count,
        "floor_normal_unique_fixed_endpoint_count": len(floor_normal_endpoint_nodes),
        "numerical_ground_nodes": numerical_ground_nodes,
        "conditional_floor_keys": conditional_floor_keys,
        "permanent_equation_count": len(permanent_equations),
        "equation_count": len(equations),
        "source_law_counts": dict(sorted(law_counts.items())),
        "springa_map_max_abs_coefficient_residual": q_map_max_error,
        "springa_initial_span_max_abs_residual_mm": q_length_max_error,
        "springa_positive_branch_max_slope_residual_N_per_mm": right_slope_max_error,
        "springa_negative_branch_max_abs_force_N": left_force_max_abs,
        "springa_zero_force_max_abs_N": zero_force_max_abs,
        "fixed_nodes": fixed_nodes,
        "fixed_dofs": fixed_dofs,
        "physical_nodes": physical_nodes,
        "element_nodes": element_nodes,
        "equation_nodes": equation_nodes,
        "expansion_prune_abs": EXPANSION_PRUNE,
    }


def common_rigid_modes(
    bodies: list[str], body_index: dict[str, int], datums: dict[str, np.ndarray]
) -> np.ndarray:
    modes = np.zeros((6 * len(bodies), 6), dtype=float)
    for axis in range(3):
        modes[axis::6, axis] = 1.0
    for axis in range(3):
        omega = np.eye(3)[axis]
        vector = modes[:, axis + 3]
        for body in bodies:
            offset = 6 * body_index[body]
            vector[offset : offset + 3] = np.cross(omega, datums[body])
            vector[offset + 3 : offset + 6] = ROTATION_LENGTH_MM * omega
    norms = np.linalg.norm(modes, axis=0)
    return modes / norms


def residuals_for_modes(matrix: np.ndarray, modes: np.ndarray) -> list[float]:
    row_norms = np.linalg.norm(matrix, axis=1)
    kept = row_norms > 1e-14
    scaled = matrix[kept] / row_norms[kept, None]
    return [float(np.max(np.abs(scaled @ modes[:, index]))) if scaled.size else 0.0 for index in range(modes.shape[1])]


def build_floor_rigid_rows(
    model: dict[str, Any],
    model_rows: dict[str, Any],
    floor_audit: dict[str, Any],
    floor_matrix_path: Path,
) -> tuple[np.ndarray, dict[str, Any]]:
    archive = np.load(floor_matrix_path, allow_pickle=False)
    floor_matrix = np.asarray(archive["original"], dtype=float)
    masters = [tuple(map(int, pair)) for pair in floor_audit["physical_master_dofs"]]
    if floor_matrix.shape != (200, 800) or len(masters) != 800:
        raise AuditError("Pinned floor-stick matrix is not the expected 200x800 source matrix")
    if len(set(masters)) != 800 or any(node not in model_rows["body_of"] for node, _ in masters):
        raise AuditError("Floor-stick matrix masters no longer map one-to-one to physical-body DOFs")
    pivot_master_count = len(set(masters) & model_rows["conditional_floor_keys"])
    if pivot_master_count != 200:
        raise AuditError("Expected all 200 conditional floor pivots among the physical floor-matrix masters")
    if int(floor_audit["independent_constraint_rank"]) != 200:
        raise AuditError("Pinned floor-stick source constraint rank changed")
    if floor_audit.get("source_input_sha256") != model["source_model_pin"]["c11_input_model_sha256"]:
        raise AuditError("Floor-stick source input no longer matches the current frame source")
    g = np.asarray(
        [
            rigid_row_from_nodal_terms(
                {(node, dof): 1.0},
                nodes=model_rows["nodes"],
                body_of=model_rows["body_of"],
                datums=model_rows["datums"],
                body_index=model_rows["body_index"],
            )
            for node, dof in masters
        ],
        dtype=float,
    )
    floor_rows = floor_matrix @ g
    return floor_rows, {
        "source_floor_constraint_rows": int(floor_matrix.shape[0]),
        "source_floor_physical_master_dofs": int(floor_matrix.shape[1]),
        "unique_physical_body_master_dofs": len(set(masters)),
        "conditional_physical_pivots_in_matrix_masters": pivot_master_count,
        "all_source_masters_map_to_reviewed_physical_bodies": True,
        "projected_floor_row_count": int(floor_rows.shape[0]),
        "projected_zero_row_count": int(np.count_nonzero(np.linalg.norm(floor_rows, axis=1) <= 1e-14)),
        "conditional_reference_nodes_are_fixed_for_this_increment_screen": len(model_rows["floor_reference_nodes"]) == 200,
        "condition": "All 100 floor normals bearing; each of the 200 captured no-slip reference increments held fixed.",
    }


def build_audit() -> dict[str, Any]:
    pins = check_pins()
    model = read_json(ROOT / MODEL)
    floor_audit = read_json(ROOT / FLOOR_AUDIT)
    staged_assessment = read_json(ROOT / (BASE / "current-floor-staged-reference-native-attempt01/parent-staged-assessment.json"))
    gravity_contract = read_json(ROOT / (BASE / "current-gravity-settle-climber-ramp-scenario-attempt01/scenario-contract.json"))
    global_floor = read_json(ROOT / (BASE / "current-global-floor-wrench-screen-attempt01/floor-wrench-screen.json"))

    if (
        model.get("schema") != "current_springa_frame_input_model/v1"
        or model.get("candidate") != "compact-floor-flush-wood-joints-development"
        or model.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1"
        or model.get("case_id") != "a12-rear"
    ):
        raise AuditError("Current frame input identity changed")
    if model.get("native_solve_executed") is not False or model.get("geometry_audit", {}).get("native_solve_executed") is not False:
        raise AuditError("Source model does not remain an input-only adapter")
    if len(model["elements"]) != 3543:
        raise AuditError("Current frame element inventory changed")
    if model["adapted_element_kind_counts"] != {"C3D20": 1903, "SPRING2": 348, "SPRINGA": 1292}:
        raise AuditError("Current frame element kinds/counts changed")

    oracles = run_rank_oracles()
    rows = build_model_rows(model)
    bilateral = rows["bilateral_rows"]
    unilateral = rows["unilateral_rows"]
    free_open = bilateral
    active_normal = np.vstack((bilateral, unilateral))

    floor_rigid_rows, floor_projection_audit = build_floor_rigid_rows(
        model, rows, floor_audit, ROOT / FLOOR_MATRIX
    )
    floor_stick_only = np.vstack((bilateral, floor_rigid_rows))
    active_stick = np.vstack((active_normal, floor_rigid_rows))

    free_modes = common_rigid_modes(rows["bodies"], rows["body_index"], rows["datums"])
    free_residuals = residuals_for_modes(free_open, free_modes)
    if max(free_residuals) > 1e-8:
        raise AuditError("Permanent bilateral rows do not preserve all six common rigid modes")
    active_candidate_modes = free_modes[:, [0, 1, 5]]
    active_candidate_residuals = residuals_for_modes(active_normal, active_candidate_modes)
    if max(active_candidate_residuals) > 1e-8:
        raise AuditError("All-active normal-only envelope does not preserve x/y slide and z yaw")
    floor_stick_common_residuals = residuals_for_modes(floor_stick_only, free_modes)
    floor_stick_preserved_common_modes = [
        mode
        for mode, residual in zip(
            ["Tx", "Ty", "Tz", "Rx", "Ry", "Rz"],
            floor_stick_common_residuals,
            strict=True,
        )
        if residual <= 1e-8
    ]
    floor_stick_removed_common_modes = [
        mode
        for mode, residual in zip(
            ["Tx", "Ty", "Tz", "Rx", "Ry", "Rz"],
            floor_stick_common_residuals,
            strict=True,
        )
        if residual > 1e-8
    ]

    branch_results = {
        "all_unilateral_open_bilateral_only": {
            "included": ["348 positive bilateral SPRING2 rows", "permanent source projection/interpolation MPCs"],
            "excluded": ["1,292 unilateral SPRINGA tangents", "all 200 conditional floor-stick rows"],
            "floor_reference_handling": "The 200 fixed scalar captured-reference nodes occur only in the 200 conditional floor-stick rows removed from this all-open screen; they add no body constraint here. The separate 100 fixed numerical floor endpoints remain in the source projection MPCs and their ground effect is retained in the expanded floor-normal rows whenever those unilateral rows are included.",
            "screen": rank_sensitivity(free_open),
            "common_global_rigid_modes": {
                "count": 6,
                "basis": ["Tx", "Ty", "Tz", "Rx", "Ry", "Rz"],
                "normalized_row_residuals_max_abs": free_residuals,
                "verified": True,
            },
            "additional_body_rigid_nullity_at_1e-10": rank_sensitivity(free_open)["nullity_by_relative_cutoff"]["1e-10"] - 6,
            "interpretation": "At the selected 1e-10 cutoff, 80 body-rigid kinematic null directions split into six common free-body modes and 74 additional relative-body mechanisms. The rank varies at tighter numerical cutoffs, so this is a mechanism screen, not a full stiffness rank.",
            "state_status": "A declared all-open branch at q=0, not an asserted gravity-load direction or accepted contact state.",
        },
        "all_unilateral_active_normal_only_envelope": {
            "included": ["348 positive bilateral SPRING2 rows", "all 1,292 unilateral SPRINGA projected rows, including 100 floor-normal rows"],
            "excluded": ["all 200 conditional floor-stick rows"],
            "screen": rank_sensitivity(active_normal),
            "verified_remaining_rigid_modes": {
                "basis": ["global Tx", "global Ty", "global Rz"],
                "normalized_row_residuals_max_abs": active_candidate_residuals,
                "independent_modes": 3,
                "rank_at_1e-10": rank_sensitivity(active_normal)["rank_by_relative_cutoff"]["1e-10"],
                "nullity_at_1e-10": rank_sensitivity(active_normal)["nullity_by_relative_cutoff"]["1e-10"],
                "these_modes_span_the_screen_nullspace_at_1e-10": rank_sensitivity(active_normal)["nullity_by_relative_cutoff"]["1e-10"] == 3,
            },
            "interpretation": "The optimistic all-active normal-only envelope leaves planar floor slide and yaw. It does not identify a compatible or simultaneously active state.",
            "state_status": "An all-positive one-sided tangent envelope, not the initial zero-load tangent or a solved state.",
        },
        "all_unilateral_open_with_conditional_all_bearing_floor_stick": {
            "included": ["348 positive bilateral SPRING2 rows", "all 200 exact floor-stick rows with fixed captured-reference increments"],
            "excluded": ["all 1,292 unilateral SPRINGA tangents"],
            "floor_row_projection": floor_projection_audit,
            "screen": rank_sensitivity(floor_stick_only),
            "common_global_rigid_modes": {
                "normalized_row_residuals_max_abs": floor_stick_common_residuals,
                "preserved": floor_stick_preserved_common_modes,
                "removed_by_conditional_floor_rows": floor_stick_removed_common_modes,
                "rank_increase_vs_open_bilateral_only_at_1e-10": (
                    rank_sensitivity(floor_stick_only)["rank_by_relative_cutoff"]["1e-10"]
                    - rank_sensitivity(free_open)["rank_by_relative_cutoff"]["1e-10"]
                ),
                "nullity_reduction_vs_open_bilateral_only_at_1e-10": (
                    rank_sensitivity(free_open)["nullity_by_relative_cutoff"]["1e-10"]
                    - rank_sensitivity(floor_stick_only)["nullity_by_relative_cutoff"]["1e-10"]
                ),
            },
            "interpretation": "At the 1e-10 cutoff, the captured no-slip rows remove the three verified common in-plane modes Tx, Ty, and Rz plus twelve additional directions from the bilateral-only screen nullspace; 65 screen-null directions remain. The common modes Tz, Rx, and Ry remain. This separates removal of common floor motion from curing all body-rigid mechanisms. The row set is only a conditional algebraic screen and is not physically admissible unless all required floor normals bear.",
            "state_status": "Conditional counterfactual only: it combines fixed captured no-slip reference increments with all unilateral normal tangents open, so it is not an asserted contact state.",
        },
        "all_unilateral_active_with_conditional_all_bearing_floor_stick": {
            "included": ["348 positive bilateral SPRING2 rows", "all 1,292 unilateral SPRINGA projected rows", "all 200 exact floor-stick rows with fixed captured-reference increments"],
            "excluded": [],
            "floor_row_projection": floor_projection_audit,
            "screen": rank_sensitivity(active_stick),
            "interpretation": "This separately declared all-bearing/no-slip increment screen has no body-rigid null mode at the tested cutoffs. The floor rows are conditional episode constraints, not a zero-load support or gauge.",
            "state_status": "Conditional optimistic envelope only: all 1,292 unilateral rows are assumed on their positive tangent; all 100 floor normal forces must be positive; and the no-slip reference episode must already have been captured.",
        },
    }

    fixed_classes = {
        "SPRINGA_numerical_ground_nodes": len(rows["numerical_ground_nodes"]),
        "conditional_floor_reference_scalar_nodes": len(rows["floor_reference_nodes"]),
        "fixed_floor_endpoint_nodes": len(rows["floor_support_nodes"]),
        "fixed_nodes_total": len(rows["fixed_nodes"]),
        "fixed_translation_dofs_total": len(rows["fixed_dofs"]),
        "fixed_physical_body_nodes": len(rows["fixed_nodes"] & rows["physical_nodes"]),
        "fixed_floor_endpoint_nodes_are_nonphysical": not bool(
            rows["floor_support_nodes"] & rows["physical_nodes"]
        ),
        "fixed_floor_endpoint_nodes_are_not_element_nodes": not bool(
            rows["floor_support_nodes"] & rows["element_nodes"]
        ),
        "fixed_floor_endpoint_projection_equations": {
            "master_term_count": sum(rows["floor_support_term_count_by_node"].values()),
            "equation_row_count": rows["floor_support_equation_row_count"],
            "terms_by_dof": {
                str(dof): count
                for dof, count in sorted(rows["floor_support_term_count_by_dof"].items())
            },
            "each_node_has_three_master_terms": all(
                count == 3 for count in rows["floor_support_term_count_by_node"].values()
            ),
            "none_are_pivots_or_conditional_floor_rows": True,
            "expanded_effect_in_100_floor_normal_rows": rows["floor_normal_projection_count"],
            "one_to_one_floor_normal_to_fixed_endpoint_mapping": (
                rows["floor_normal_unique_fixed_endpoint_count"] == 100
            ),
            "interpretation": "Fixed numerical endpoints in the assumed floor reaction path, not physical body nodes, physical anchors, or a verified floor condition.",
        },
        "classes_partition_fixed_nodes": len(rows["fixed_nodes"]) == 1292 + 200 + 100,
    }

    return {
        "schema": "current_frame_gravity_rigid_body_rank_readiness/v1",
        "status": "PASS_SOURCE_BOUND_RIGID_BODY_BRANCH_SCREEN_INITIAL_GRAVITY_GAUGE_OPEN",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "case_id": model["case_id"],
        "native_solve_executed": False,
        "geometry_changed": False,
        "full_physical_tangent_rank_claimed": False,
        "pinned_inputs": pins,
        "prior_packet_context": {
            "staged_coupon": {
                "source": str(BASE / "current-floor-staged-reference-native-attempt01/README.md"),
                "native_method_scope": "The staged coupon passed its 60-increment parent oracle and does not test the frame zero-reaction gauge or rank.",
                "assessment_status": staged_assessment.get("status", "status field absent"),
            },
            "gravity_loading_contract": {
                "source": str(BASE / "current-gravity-settle-climber-ramp-scenario-attempt01/README.md"),
                "initial_state_gate": "The source contract requires a tangent-rank check and removal only of demonstrated reaction-free null modes.",
                "scenario_contract_schema": gravity_contract.get("schema"),
            },
            "global_floor_screen": {
                "source": str(BASE / "current-global-floor-wrench-screen-attempt01/README.md"),
                "scope": "Aggregate equilibrium witnesses only; not a compatible all-bearing deformation or stiffness response.",
                "schema": global_floor.get("schema"),
            },
        },
        "rank_oracles_run_before_frame_screen": oracles,
        "model_constraint_inventory": {
            "physical_body_count": len(rows["bodies"]),
            "physical_body_nodes": len(rows["physical_nodes"]),
            "serialized_nodes": len(model["nodes"]),
            "serialized_equations_total": rows["equation_count"],
            "permanent_projection_and_interpolation_equations": rows["permanent_equation_count"],
            "conditional_floor_stick_equations_excluded_from_open_branch": len(rows["conditional_floor_keys"]),
            "bilateral_spring2_rows": len(rows["bilateral_rows"]),
            "unilateral_springa_rows": len(rows["unilateral_rows"]),
            "source_law_counts": rows["source_law_counts"],
            "fixed_node_classes": fixed_classes,
            "rigid_coordinate_scaling": {
                "translation_coordinates": "mm",
                "rotation_coordinates": "1000 mm * radians",
                "body_datum": "Arithmetic mean of the source physical-body node coordinates",
                "expansion_coefficient_prune_absolute": rows["expansion_prune_abs"],
            },
            "springa_mapping_check": {
                "method": "Expand each serialized SPRINGA first endpoint through permanent MPCs; project its displacement on the actual fixed-endpoint line axis; compare with the source physical projection row.",
                "maximum_absolute_coefficient_residual": rows["springa_map_max_abs_coefficient_residual"],
                "initial_span_max_abs_residual_mm": rows["springa_initial_span_max_abs_residual_mm"],
                "positive_q_branch_max_slope_residual_N_per_mm": rows["springa_positive_branch_max_slope_residual_N_per_mm"],
                "negative_q_branch_max_abs_force_N": rows["springa_negative_branch_max_abs_force_N"],
                "zero_q_force_max_abs_N": rows["springa_zero_force_max_abs_N"],
                "q_zero_tangent": "One-sided: zero slope on the negative-q side, positive k slope on the positive-q side. No single two-sided tangent is specified at q=0.",
            },
        },
        "rigid_body_branch_screens": branch_results,
        "readiness_gate": {
            "initial_gravity_gauge_ready": False,
            "reason": "The all-open bilateral branch has 74 additional body-rigid kinematic mechanisms beyond the six common modes at the selected 1e-10 cutoff; the unilateral rows are nonsmooth at q=0, so neither the all-open branch nor the optimistic all-active envelope selects the gravity-start tangent.",
            "full_operator_missing": "No assembled reduced C3D20 physical tangent operator is pinned. The deck supplies 1,903 C3D20 solids, 348 bilateral springs, engineering-constant materials/orientations and 21,998 equations, but the current packet does not assemble an orientation-aware solid tangent and combine it with a state-consistent unilateral active set.",
            "next_gate": "A parent-reviewed initial gravity continuation must establish its directional unilateral state, demonstrate its actual branch null modes, and remove only verified common null modes with a reaction-free gauge. Do not assume the gauge has six modes after floor normals become active: the declared all-open branch has six common modes, the optimistic all-normal-active envelope has three planar common modes, and an actual active subset may differ. Do not transfer the conditional all-bearing floor-stick result to the zero-load start.",
            "no_support_or_geometry_edit_introduced": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = build_audit()
    output = HERE / "audit.json"
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        output.write_text(rendered, encoding="utf-8")
        print(json.dumps({"status": result["status"], "output": str(output.relative_to(ROOT))}, sort_keys=True))
        return
    if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
        raise SystemExit("Stored audit.json does not match the source-bound recomputation")
    print(json.dumps({"status": result["status"], "verified": True}, sort_keys=True))


if __name__ == "__main__":
    main()
