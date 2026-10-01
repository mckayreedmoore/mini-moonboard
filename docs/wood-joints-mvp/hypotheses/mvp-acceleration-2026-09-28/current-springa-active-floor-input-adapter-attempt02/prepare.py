"""Prepare one proposed selected-bearing floor branch input; never run CalculiX."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
from scipy.linalg import qr

ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = ROOT / BASE / "current-springa-active-floor-input-adapter-attempt02"
CASE = HERE / "a12-rear"
CONTROL = BASE / "current-springa-frame-a12-rear-controls-attempt01"
SCREEN = BASE / "current-springa-selected-floor-branch-screen-attempt01/screen.json"
FLOOR_AUDIT = BASE / "current-floor-stick-constraint-audit-attempt01/audit.json"
FLOOR_MATRICES = BASE / "current-floor-stick-constraint-audit-attempt01/constraint-matrices.npz"
C11_MODEL = BASE / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json"
SCHEMA = "current_springa_selected_floor_input_model/v1"
BRANCH = "monotone_zero_gap_first_bearing_reference_zero"

PINS = {
    str(CONTROL / "model.json"): "b89e69abd004bd788d3619f73270375bbd8d8a195edf29313a77baee3c1a8f1e",
    str(CONTROL / "model.inp"): "bab4e4728e6a690dbff66d44cced93977a6125d5fd9fc21fe26d927d83785ca2",
    str(CONTROL / "model.dat"): "10b08e7fcfca13cc0c68916634c525b66549d4e033e3d657c83f11bddfac1f8d",
    str(CONTROL / "execution.json"): "1366a5b8c037c2c5bfa72abc9eec7fbe927544e337fe7676133ac96e826e2afb",
    str(SCREEN): "7b73531a921c3e23f5c14393be580045efa94cbdb3d94675101f0f624df84c3c",
    str(FLOOR_AUDIT): "43b5aa99468b1577cd273baddafe47955b235fa00ddd5b9d5aff91d490695c95",
    str(FLOOR_MATRICES): "4fcc630274e2f1c7166c811d2aa97a3f075d60b5724600b88be73afebe308f6e",
    str(C11_MODEL): "d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0",
    str(BASE / "current-springa-frame-response-audit-attempt01/response_audit.py"):
        "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c",
}


class InputError(RuntimeError):
    pass


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def real(value: float) -> str:
    value = float(value)
    if not math.isfinite(value):
        raise InputError("Nonfinite real in output deck")
    token = format(value, ".14g")
    if "e" in token.lower():
        mantissa, exponent = re.split("[eE]", token, maxsplit=1)
        if "." not in mantissa:
            mantissa += ".0"
        token = mantissa + "e" + exponent
    elif "." not in token:
        token += ".0"
    if len(token) > 20:
        raise InputError(f"Real token exceeds 20 columns: {token}")
    return token


def keyword(line: str) -> bool:
    return line.lstrip().startswith("*") and not line.lstrip().startswith("**")


def card_span(lines: list[str], predicate) -> tuple[int, int]:
    starts = [i for i, line in enumerate(lines) if predicate(line.strip().upper())]
    if len(starts) != 1:
        raise InputError(f"Expected one target card, found {len(starts)}")
    start = starts[0]
    end = start + 1
    while end < len(lines) and not keyword(lines[end]):
        end += 1
    return start, end


def parse_equations(lines: list[str]) -> tuple[list[list[tuple[int, int, float]]], list[tuple[int, int]]]:
    equations, spans = [], []
    cursor = 0
    while cursor < len(lines):
        if lines[cursor].strip().upper() != "*EQUATION":
            cursor += 1
            continue
        start = cursor
        cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        count = int(lines[cursor].strip())
        cursor += 1
        values = []
        while len(values) < 3 * count and cursor < len(lines):
            row = lines[cursor].strip()
            if row.startswith("*"):
                raise InputError("Truncated equation card")
            if row:
                values.extend(item.strip() for item in row.split(","))
            cursor += 1
        if len(values) != 3 * count:
            raise InputError("Equation term count does not match data")
        eq = [(int(values[i]), int(values[i + 1]), float(values[i + 2])) for i in range(0, len(values), 3)]
        equations.append(eq)
        spans.append((start, cursor))
    return equations, spans


def parse_nodes(lines: list[str]) -> dict[int, list[float]]:
    start, end = card_span(lines, lambda s: s == "*NODE")
    result = {}
    for line in lines[start + 1:end]:
        if line.strip():
            f = [x.strip() for x in line.split(",")]
            if len(f) != 4:
                raise InputError(f"Unexpected node row: {line}")
            tag = int(f[0])
            if tag in result:
                raise InputError(f"Duplicate node tag {tag}")
            result[tag] = [float(x) for x in f[1:]]
    return result


def parse_nset(lines: list[str]) -> tuple[int, int, set[int]]:
    start, end = card_span(lines, lambda s: s.startswith("*NSET,NSET=ALLN"))
    values = set()
    for line in lines[start + 1:end]:
        if line.strip():
            values.update(int(x.strip()) for x in line.split(",") if x.strip())
    return start, end, values


def parse_cload(lines: list[str]) -> dict[tuple[int, int], float]:
    start, end = card_span(lines, lambda s: s == "*CLOAD")
    values = {}
    for line in lines[start + 1:end]:
        if line.strip():
            f = [x.strip() for x in line.split(",")]
            if len(f) != 3:
                raise InputError(f"Unexpected CLOAD row: {line}")
            key = (int(f[0]), int(f[1]))
            values[key] = values.get(key, 0.0) + float(f[2])
    return values


def same_equation(a, b, tol=1e-13) -> bool:
    return len(a) == len(b) and all(
        x[:2] == y[:2] and math.isclose(x[2], y[2], rel_tol=0.0, abs_tol=tol)
        for x, y in zip(a, b, strict=True)
    )


def serialize_equation(terms: list[tuple[int, int, float]]) -> list[str]:
    vals = []
    for n, dof, c in terms:
        vals.extend([str(int(n)), str(int(dof)), real(c)])
    lines = ["*EQUATION", str(len(terms))]
    for i in range(0, len(vals), 9):
        lines.append(",".join(vals[i:i + 9]))
    return lines


def deck_protected_cards(deck: str) -> dict[str, str]:
    lines = deck.splitlines()
    material = next(i for i, s in enumerate(lines) if s.strip().upper().startswith("*MATERIAL"))
    orient = next(i for i, s in enumerate(lines) if s.strip().upper().startswith("*ORIENTATION"))
    nset = next(i for i, s in enumerate(lines) if s.strip().upper().startswith("*NSET,NSET=ALLN"))
    cs, ce = card_span(lines, lambda s: s == "*CLOAD")
    step = next(i for i, s in enumerate(lines) if s.strip().upper().startswith("*STEP"))
    return {
        "materials": "\n".join(lines[material:orient]),
        "orientation_sections": "\n".join(lines[orient:nset]),
        "cload": "\n".join(lines[cs:ce]),
        "step_output": "\n".join(lines[step:]),
    }


def protected_model_fields(model: dict[str, Any]) -> dict[str, str]:
    keys = [
        "candidate", "case_id", "geometry_revision_id", "case_input", "body_geometry",
        "body_wrench_audit_rows", "physical_body_nodes", "physical_body_elements",
        "physical_body_loads", "physical_external_loads", "physical_body_wrenches",
        "expected_physical_body_wrenches", "source_wrench_ledger", "connection_attachment_rows",
        "connection_counts", "connection_ownership", "connection_scenario",
        "contact_cell_ownership", "corner_demand_contract_audit", "material_binding",
        "source_sha256", "nodes", "fixed_nodes", "elements", "loads", "springs", "unilateral_springa_bindings",
        "raw_source_carrier_law_inventory_rows",
    ]
    return {key: digest(model[key]) for key in keys if key in model}


def build_mask(screen: dict[str, Any], audit: dict[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    if screen.get("status") != "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH":
        raise InputError("Screen is not the pinned rejected selected-bearing diagnostic")
    if screen.get("corner_demands_usable") is not False or screen.get("full_step_native_convergence") is not True:
        raise InputError("Screen scope/convergence flags changed")
    states = screen.get("states", [])
    if len(states) != 7 or screen.get("same_positive_cell_set_at_all_printed_times") is not True:
        raise InputError("Expected seven printed states and a stable positive-cell set")
    sets = []
    rows_by_state = []
    for state in states:
        rows = state.get("rows", [])
        by_cell = {str(row["cell_name"]): row for row in rows}
        positive = {cell for cell, row in by_cell.items() if row.get("strictly_positive_after_rounding") is True}
        separating = {cell for cell, row in by_cell.items() if row.get("strictly_separating_after_rounding") is True}
        if len(by_cell) != 100:
            raise InputError("Each state must classify all 100 floor cells")
        if (
            len(positive) != int(state.get("bearing_count", -1))
            or len(separating) != int(state.get("separating_count", -1))
        ):
            raise InputError("Screen state classification counts disagree with its row inventory")
        if positive & separating or positive | separating != set(by_cell):
            raise InputError("Cell classifications do not partition the floor")
        sets.append(positive)
        rows_by_state.append(by_cell)
    if any(s != sets[0] for s in sets[1:]):
        raise InputError("Positive floor-cell mask changes between printed states")
    if set(screen.get("diagnostic_positive_cells_at_final_time", [])) != sets[-1]:
        raise InputError("Final screen summary differs from final state rows")
    if set(screen.get("diagnostic_separating_cells_at_final_time", [])) != set(rows_by_state[-1]) - sets[-1]:
        raise InputError("Final separating-cell summary differs from final state rows")
    owners = audit["row_owners"]
    cell_order = list(dict.fromkeys(str(row["normal_cell"]) for row in owners))
    if len(cell_order) != 100 or set(cell_order) != set(rows_by_state[-1]):
        raise InputError("Floor audit row-owner cells differ from screen cells")
    selected = [cell for cell in cell_order if cell in sets[0]]
    inactive = [cell for cell in cell_order if cell not in sets[0]]
    mask = []
    for i, owner in enumerate(owners):
        cell, dof = str(owner["normal_cell"]), int(owner["local_dof"])
        mask.append({
            "source_row_original_index": i,
            "source_row_id": f"{cell}_friction/local-dof-{dof}",
            "normal_cell": cell,
            "local_dof": dof,
            "selected": cell in sets[0],
            "source_state": (
                "selected_proposed_positive_at_all_7_printed_states"
                if cell in sets[0]
                else "inactive_strictly_separating_at_all_7_printed_states"
            ),
        })
    if len(selected) + len(inactive) != 100:
        raise InputError("Selected/inactive mask does not cover the 100 floor cells")
    return selected, inactive, mask


def prepare() -> dict[str, Any]:
    pinned = {}
    for relative, expected in PINS.items():
        observed = sha(ROOT / relative)
        if observed != expected:
            raise InputError(f"Input pin mismatch for {relative}: {observed}")
        pinned[relative] = {"sha256": observed}

    source_model = json.loads((ROOT / (CONTROL / "model.json")).read_text())
    source_deck = (ROOT / (CONTROL / "model.inp")).read_text()
    screen = json.loads((ROOT / SCREEN).read_text())
    floor_audit = json.loads((ROOT / FLOOR_AUDIT).read_text())
    archive = np.load(ROOT / FLOOR_MATRICES)
    a = np.asarray(archive["original"], dtype=float)
    if source_model.get("schema") != "current_springa_frame_input_model/v1":
        raise InputError("Frozen controls input schema changed")
    if floor_audit.get("source_input_sha256") != PINS[str(C11_MODEL)]:
        raise InputError("Original floor matrix audit is not bound to C11 source geometry")
    if floor_audit.get("native_solve_executed") is not False or floor_audit.get("floor_bearing_verified") is not False:
        raise InputError("Original floor matrix audit changed its qualification status")

    selected_cells, inactive_cells, row_mask = build_mask(screen, floor_audit)
    row_owners = floor_audit["row_owners"]
    selected_set, inactive_set = set(selected_cells), set(inactive_cells)
    active_rows = [i for i, row in enumerate(row_owners) if str(row["normal_cell"]) in selected_set]
    inactive_rows = [i for i, row in enumerate(row_owners) if str(row["normal_cell"]) in inactive_set]
    active_count, inactive_count = len(active_rows), len(inactive_rows)
    selected_cell_count, inactive_cell_count = len(selected_cells), len(inactive_cells)
    if active_count != 2 * selected_cell_count or inactive_count != 2 * inactive_cell_count:
        raise InputError("Each selected/inactive floor cell must map to two original tangent rows")
    if active_count + inactive_count != 200 or sorted(active_rows + inactive_rows) != list(range(200)):
        raise InputError("Selected/inactive rows do not partition the 200 original tangent rows")
    active_a = a[np.asarray(active_rows, dtype=int), :]
    singular = np.linalg.svd(active_a, compute_uv=False)
    tolerance = max(active_a.shape) * np.finfo(float).eps * float(singular[0])
    rank = int(np.count_nonzero(singular > tolerance))
    if rank != active_count:
        raise InputError(
            f"Selected active floor matrix is rank deficient: rank {rank} for {active_count} proposed rows"
        )
    _, _, row_order = qr(active_a.T, pivoting=True, mode="economic")
    qr_independent_row_order = np.asarray(active_rows, dtype=int)[np.asarray(row_order[:rank], dtype=int)]
    if set(map(int, qr_independent_row_order)) != set(active_rows):
        raise InputError("QR independent-row selection does not cover every active source row")
    # Every proposed row is independent. Keep emitted equation order
    # in stable original source-row order so output reference maps remain directly indexed.
    selected_indices = np.asarray(sorted(active_rows), dtype=int)
    selected_a = a[selected_indices, :]
    _, _, column_order = qr(selected_a, pivoting=True, mode="economic")
    pivots = np.asarray(column_order[:rank], dtype=int)
    masters = [tuple(map(int, item)) for item in floor_audit["physical_master_dofs"]]
    if a.shape != (200, 800) or len(masters) != 800:
        raise InputError("Source floor master map no longer has 200x800 shape")
    s = selected_a[:, pivots]
    if np.linalg.matrix_rank(s, tol=tolerance) != rank:
        raise InputError("Selected physical pivot block is rank deficient")
    d = np.linalg.solve(s, np.eye(rank))
    h = d @ selected_a
    if not np.allclose(h[:, pivots], np.eye(rank), rtol=0.0, atol=5e-13):
        raise InputError("Selected transform has a non-identity pivot block")
    condition = float(np.linalg.cond(s))

    source_lines = source_deck.splitlines()
    model_eq = source_model["equations"]
    deck_eq, spans = parse_equations(source_lines)
    if len(model_eq) != 21998 or len(deck_eq) != len(model_eq):
        raise InputError("Frozen controls equation inventory changed")
    if any(not same_equation(parsed, [tuple(x) for x in recorded]) for parsed, recorded in zip(deck_eq, model_eq, strict=True)):
        raise InputError("Frozen controls model equations differ from deck")
    old_refs = source_model["floor_reference_nodes_and_load_map"]
    if len(old_refs) != 200:
        raise InputError("Frozen controls must have 200 all-bearing floor reference rows")
    old_ref_by_row = {int(row["source_row_original_index"]): row for row in old_refs}
    if set(old_ref_by_row) != set(range(200)):
        raise InputError("Frozen controls floor reference map is incomplete")
    if len(source_model["springs"]) != 348 or len(source_model["unilateral_springa_bindings"]) != 1292:
        raise InputError("Frozen controls spring counts changed")
    if len(source_model["physical_body_nodes"]) != 50:
        raise InputError("Frozen controls body count changed")

    old_ref_tags = {int(row["node"]) for row in old_refs}
    if len(old_ref_tags) != 200:
        raise InputError("Old floor reference tags are not unique")
    for i, owner in enumerate(row_owners):
        ref = old_ref_by_row[i]
        expected_id = f"{owner['normal_cell']}_friction/local-dof-{int(owner['local_dof'])}"
        if ref["source_row_id"] != expected_id:
            raise InputError(f"Frozen reference map row ID mismatch at {i}")
    qghost_terms = [
        [tuple(term) for term in row["terms"]]
        for binding in source_model["unilateral_springa_bindings"]
        for row in binding["qghost_equations"]
    ]
    floor_start = len(deck_eq) - 200 - len(qghost_terms)
    floor_end = floor_start + 200
    if floor_start < 0 or len(qghost_terms) != 3 * 1292:
        raise InputError("Could not locate the full-floor block between source and qghost equations")
    if any(not same_equation(actual, expected) for actual, expected in zip(deck_eq[floor_end:], qghost_terms, strict=True)):
        raise InputError("Frozen controls qghost equations do not follow the floor block as expected")
    if any(
        any(n in old_ref_tags for n, _dof, _c in eq)
        for eq in deck_eq[:floor_start] + deck_eq[floor_end:]
    ):
        raise InputError("Old floor reference is used by an equation outside the audited floor block")
    if any(
        eq[0][:2] != tuple(source_model["floor_constraint_audit"]["floor_reference_rows"][i]["dependent_physical_pivot_dof"])
        for i, eq in enumerate(deck_eq[floor_start:floor_end])
    ):
        raise InputError("Located 200 controls equations are not their audited floor constraints")

    # Rebind selected channels to the existing abstract scalar nodes in frozen controls.
    control_node_deck = parse_nodes(source_lines)
    control_node_model = {int(k): list(map(float, v)) for k, v in source_model["nodes"].items()}
    if set(control_node_deck) != set(control_node_model):
        raise InputError("Frozen controls node cards and model do not agree")
    for tag, xyz in control_node_deck.items():
        if not np.allclose(xyz, control_node_model[tag], rtol=0.0, atol=1e-10):
            raise InputError(f"Control node coordinate mismatch at {tag}")
    ref_tag = {int(row): int(old_ref_by_row[int(row)]["node"]) for row in selected_indices}
    tangent_rows = {
        str(row["group"]): row
        for row in source_model["raw_source_carrier_law_inventory_rows"]
        if row.get("role") == "assumed_no_slip_floor"
    }
    inventory_index = {
        str(row["group"]): i for i, row in enumerate(source_model["raw_source_carrier_law_inventory_rows"])
    }
    if len(tangent_rows) != 200:
        raise InputError("Frozen raw carrier inventory has no exact 200 tangent-row map")
    refs: dict[int, dict[str, Any]] = {}
    pivot_dofs = [masters[int(i)] for i in pivots]
    position_by_original = {int(orig): i for i, orig in enumerate(selected_indices)}
    for orig in selected_indices:
        orig = int(orig)
        old = old_ref_by_row[orig]
        group = str(old["source_spring_group"])
        src = tangent_rows.get(group)
        if src is None or src["name"] != old["source_spring_name"] or int(src["element"]) != int(old["source_spring_element"]):
            raise InputError(f"Source tangent inventory mismatch for {group}")
        node = ref_tag[orig]
        basis = list(map(float, old["owner_tangent_basis_global_xyz"]))
        point = list(map(float, old["owner_floorpoint_xyz_mm"]))
        if not np.isclose(np.linalg.norm(basis), 1.0, atol=1e-12, rtol=0.0):
            raise InputError(f"Non-unit source tangent basis at {old['source_row_id']}")
        force = np.asarray(basis)
        moment = np.cross(np.asarray(point), force)
        position = position_by_original[orig]
        item = copy.deepcopy(old)
        item.update({
            "node": int(node),
            "normalized_equation_index": position,
            "dependent_physical_pivot_dof": [int(pivot_dofs[position][0]), int(pivot_dofs[position][1])],
            "selected_floor_branch": True,
            "branch_id": BRANCH,
            "source_inventory_row_index": int(inventory_index[group]),
            "source_tangent_force_on_first_body_unit_N": force.tolist(),
            "source_tangent_moment_about_global_origin_on_first_body_unit_Nmm": moment.tolist(),
            "source_tangent_force_on_floor_unit_N": (-force).tolist(),
            "source_tangent_moment_about_global_origin_on_floor_unit_Nmm": (-moment).tolist(),
            "source_load_correction_N": None,
            "correction_from_full_precision_matrix_N": None,
            "correction_uses_emitted_equation_and_cload_values": False,
        })
        refs[orig] = item

    # Emit H u - D r = 0: selected rows only, with numerical zero reference values.
    pivot_set = set(map(int, pivots))
    equations: list[list[tuple[int, int, float]]] = []
    floor_equation_rows = []
    omitted_h, omitted_d = [], []
    for eq_index, orig in enumerate(selected_indices):
        orig = int(orig)
        pivot = pivot_dofs[eq_index]
        terms = [(int(pivot[0]), int(pivot[1]), 1.0)]
        for col, (node, dof) in enumerate(masters):
            if col in pivot_set:
                continue
            coef = float(h[eq_index, col])
            if abs(coef) > 1e-13:
                terms.append((int(node), int(dof), coef))
            elif coef != 0.0:
                omitted_h.append(abs(coef))
        for ref_pos, ref_orig in enumerate(selected_indices):
            coef = -float(d[eq_index, ref_pos])
            if abs(coef) > 1e-13:
                terms.append((int(refs[int(ref_orig)]["node"]), 1, coef))
            elif coef != 0.0:
                omitted_d.append(abs(coef))
        equations.append(terms)
        owner = row_owners[orig]
        floor_equation_rows.append({
            "normalized_equation_index": eq_index,
            "source_row_original_index": orig,
            "source_row_id": refs[orig]["source_row_id"],
            "normal_cell": str(owner["normal_cell"]),
            "local_dof": int(owner["local_dof"]),
            "dependent_physical_pivot_dof": [int(pivot[0]), int(pivot[1])],
            "dependent_reference_node": int(refs[orig]["node"]),
            "equation_term_count": len(terms),
            "physical_free_master_term_count": len(terms) - 1 - int(np.count_nonzero(np.abs(d[eq_index]) > 1e-13)),
        })

    # Replace only the audited all-bearing *EQUATION block. Existing scalar nodes and
    # their output set and boundaries remain inert carryovers so all other cards stay exact.
    lines = list(source_lines)
    _, eq_spans = parse_equations(lines)
    del_start, del_end = eq_spans[floor_start][0], eq_spans[floor_end - 1][1]
    new_eq_lines = [line for eq in equations for line in serialize_equation(eq)]
    lines = lines[:del_start] + new_eq_lines + lines[del_end:]

    output_deck = "\n".join(lines) + "\n"
    out_lines = output_deck.splitlines()

    emitted_nodes = parse_nodes(out_lines)
    surviving_nodes = set(control_node_model)
    if set(emitted_nodes) != surviving_nodes:
        raise InputError("Frozen controls node card changed")
    _, _, alln = parse_nset(out_lines)
    if alln != surviving_nodes:
        raise InputError("Frozen controls ALLN output set changed")
    emitted_eq, _ = parse_equations(out_lines)
    if len(emitted_eq) != len(deck_eq) - 200 + rank:
        raise InputError("Output equation count is inconsistent")
    if any(not same_equation(x, y) for x, y in zip(deck_eq[:floor_start], emitted_eq[:floor_start], strict=True)):
        raise InputError("A non-floor control equation changed")
    if any(
        not same_equation(x, y)
        for x, y in zip(deck_eq[floor_end:], emitted_eq[floor_start + rank:], strict=True)
    ):
        raise InputError("A qghost control equation changed")
    if any(not same_equation(x, y) for x, y in zip(equations, emitted_eq[floor_start:floor_start + rank], strict=True)):
        raise InputError("Emitted selected floor equations differ from prepared map")
    inactive_ref_tags = old_ref_tags - {int(ref["node"]) for ref in refs.values()}
    if any(any(n in inactive_ref_tags for n, _dof, _c in eq) for eq in emitted_eq):
        raise InputError("An inactive scalar carryover remains coupled by an equation")

    # Read the serialized equations back as physical H and reference E, then audit S H=A and S(-E)=I.
    refs_by_node = {int(item["node"]): item for item in refs.values()}
    original_to_position = {int(orig): i for i, orig in enumerate(selected_indices)}
    master_column = {key: i for i, key in enumerate(masters)}
    h_emit = np.zeros((rank, len(masters)))
    e_emit = np.zeros((rank, rank))
    term_count = 0
    for eq_index, eq in enumerate(emitted_eq[floor_start:floor_start + rank]):
        term_count += len(eq)
        for node, dof, coefficient in eq:
            key = (int(node), int(dof))
            if key in master_column:
                h_emit[eq_index, master_column[key]] += coefficient
            elif node in refs_by_node and dof == 1:
                orig = int(refs_by_node[node]["source_row_original_index"])
                e_emit[eq_index, original_to_position[orig]] += coefficient
            else:
                raise InputError(f"Unclassified term in selected floor equation: {key}")
    h_resid = s @ h_emit - selected_a
    d_resid = s @ (-e_emit) - np.eye(rank)
    if np.max(np.abs(h_resid)) > 1e-10 or np.max(np.abs(d_resid)) > 1e-10:
        raise InputError("Serialized floor equations do not reconstruct source A and S inverse")

    source_cload = parse_cload(source_lines)
    emitted_cload = parse_cload(out_lines)
    if source_cload != emitted_cload:
        raise InputError("Output changed a source CLOAD location or value")
    pivot_load = np.asarray([emitted_cload.get(key, 0.0) for key in pivot_dofs], dtype=float)
    correction_emit = -(e_emit.T @ pivot_load)
    correction_full = d.T @ pivot_load
    correction = {}
    correction_full_map = {}
    for pos, orig in enumerate(selected_indices):
        correction[int(orig)] = float(correction_emit[pos])
        correction_full_map[int(orig)] = float(correction_full[pos])
        refs[int(orig)]["source_load_correction_N"] = float(correction_emit[pos])
        refs[int(orig)]["correction_from_full_precision_matrix_N"] = float(correction_full[pos])
        refs[int(orig)]["correction_uses_emitted_equation_and_cload_values"] = True

    control_cards = deck_protected_cards(source_deck)
    output_cards = deck_protected_cards(output_deck)
    if control_cards != output_cards:
        raise InputError("A protected material/orientation/CLOAD/step-output deck region changed")

    # Construct model from frozen controls by replacing only floor references/equations and branch metadata.
    model = copy.deepcopy(source_model)
    model["nodes"] = copy.deepcopy(source_model["nodes"])
    model["fixed_nodes"] = copy.deepcopy(source_model["fixed_nodes"])
    model["equations"] = copy.deepcopy(model_eq[:floor_start]) + [
        [[int(n), int(dof), float(c)] for n, dof, c in eq] for eq in equations
    ] + copy.deepcopy(model_eq[floor_end:])
    refs_sorted = [refs[i] for i in sorted(refs)]
    for key in ("floor_reference_nodes", "floor_reference_nodes_and_load_map"):
        model[key] = [int(x["node"]) for x in refs_sorted] if key == "floor_reference_nodes" else refs_sorted
    model["exact_floor_mpc_equations"] = [
        {
            **row,
            "reference_load_correction_N": correction[int(row["source_row_original_index"])],
            "source_pivot_CLOAD_N": float(pivot_load[int(row["normalized_equation_index"])]),
            "source_load_correction_source": "serialized selected equation coefficients and emitted frozen source CLOAD",
        }
        for row in floor_equation_rows
    ]
    model["schema"] = SCHEMA
    model["native_carrier_model_schema"] = SCHEMA
    model["source_response_schema"] = SCHEMA
    model["input_adapter_status"] = "ASSEMBLED_SELECTED_FLOOR_BRANCH_INPUT_ONLY"
    model["branch_input_audit_status"] = "PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION"
    model["legacy_reduced_static_linear_response_schema_compatible"] = False
    model["input_only"] = True
    model["native_solve_executed"] = False
    model["source_response_forces_read"] = False
    model["historical_active_states_reused"] = False
    model["mechanical_acceptance"] = False
    model["qualified_for_design"] = False
    model["complete_joint_validated"] = False
    model["frame_ready_for_native_run"] = False
    model["floor_inactive_scalar_output_nodes"] = [
        {
            "node": int(old_ref_by_row[i]["node"]),
            "source_row_original_index": int(i),
            "source_row_id": str(old_ref_by_row[i]["source_row_id"]),
            "role": "isolated fixed scalar output carryover; no equation, load, or floor force map",
        }
        for i in sorted(inactive_rows)
    ]
    model["floor_selected_bearing_cells"] = selected_cells
    model["floor_inactive_cells"] = inactive_cells
    model["floor_selected_original_row_indices"] = sorted(active_rows)
    model["floor_active_original_row_indices"] = sorted(active_rows)
    model["floor_inactive_original_row_indices"] = sorted(inactive_rows)
    model["floor_selected_mask_by_original_row"] = row_mask

    floor_rows = []
    for row in floor_equation_rows:
        i = int(row["normalized_equation_index"])
        orig = int(row["source_row_original_index"])
        floor_rows.append({
            **row,
            "reference_load_correction_N": correction[orig],
            "source_pivot_CLOAD_N": float(pivot_load[i]),
            "source_load_correction_source": "serialized selected equation coefficients and emitted frozen source CLOAD",
        })
    floor_audit_out = {
        "schema": "current_selected_floor_mpc_constraint_audit/v1",
        "original_constraint_rows": 200,
        "active_original_constraint_rows": active_count,
        "inactive_original_constraint_rows": inactive_count,
        "independent_constraint_rank": rank,
        "rank_tolerance": float(tolerance),
        "singular_values_active_A": singular.tolist(),
        "active_A_min_to_max_singular_ratio": float(singular[-1] / singular[0]),
        "selected_S_condition_number": condition,
        "physical_master_dof_count": 800,
        "physical_master_dofs": [[int(n), int(dof)] for n, dof in masters],
        "active_original_row_indices": sorted(active_rows),
        "inactive_original_row_indices": sorted(inactive_rows),
        "selected_rows_original_indices": [int(i) for i in selected_indices],
        "qr_independent_row_order_original_indices": [int(i) for i in qr_independent_row_order],
        "selected_source_row_ids_in_equation_order": [str(refs[int(i)]["source_row_id"]) for i in selected_indices],
        "selected_pivot_physical_dofs": [[int(n), int(dof)] for n, dof in pivot_dofs],
        "selected_A": selected_a.tolist(),
        "selected_S": s.tolist(),
        "selected_H": h.tolist(),
        "selected_D": d.tolist(),
        "S_times_H_max_abs_residual": float(np.max(np.abs(s @ h - selected_a))),
        "H_selected_pivot_block_max_abs_identity_residual": float(np.max(np.abs(h[:, pivots] - np.eye(rank)))),
        "S_times_D_max_abs_identity_residual": float(np.max(np.abs(s @ d - np.eye(rank)))),
        "equation_term_omission_policy": "Omit H and D coefficients with absolute magnitude <=1e-13; serialize retained coefficients with .14g and a decimal point.",
        "omitted_nonzero_H_coefficient_count": int(np.count_nonzero((np.abs(h) > 0) & (np.abs(h) <= 1e-13))),
        "maximum_abs_omitted_nonzero_H_coefficient": float(max((abs(x) for x in h.ravel() if 0 < abs(x) <= 1e-13), default=0.0)),
        "omitted_nonzero_D_coefficient_count": int(np.count_nonzero((np.abs(d) > 0) & (np.abs(d) <= 1e-13))),
        "maximum_abs_omitted_nonzero_D_coefficient": float(max((abs(x) for x in d.ravel() if 0 < abs(x) <= 1e-13), default=0.0)),
        "reference_row_order": "Fresh selected equation order; active references are also listed in original source-row order.",
        "floor_reference_count": active_count,
        "floor_reference_rows": floor_rows,
        "source_load_transfer": {
            "method": "F_ref = -E_emit^T F_pivot_emit from the serialized selected MPC and emitted source CLOAD",
            "unrounded_identity": "E=-S^-1; F_ref=(S^-1)^T F_pivot",
            "pivot_CLOAD_N_in_selected_equation_order": pivot_load.tolist(),
            "reference_CLOAD_N_in_selected_equation_order": correction_emit.tolist(),
            "reference_CLOAD_N_by_original_row_index": [correction.get(i, 0.0) for i in range(200)],
            "full_precision_reference_CLOAD_N_by_original_row_index": [correction_full_map.get(i, 0.0) for i in range(200)],
            "maximum_abs_serialized_vs_full_precision_reference_CLOAD_N": float(np.max(np.abs(correction_emit - correction_full))),
            "inactive_rows_have_no_reference_and_zero_correction": True,
            "raw_reference_reaction_policy": "RF(reference_node,1) minus associated transformed source CLOAD",
            "physical_force_adoption": False,
        },
        "wrench_mapping": {
            "selected_source_row_point_wrenches_preserved": True,
            "method": "Each active original tangent row maps one-to-one through the QR row permutation to its exact original source point and force_basis.",
            "sign_convention": "Unit tangent force on physical_owner.first; floor action equal and opposite.",
        },
        "floor_condition": (
            f"Proposed monotone zero-gap first-bearing reference-zero branch only. "
            f"The {selected_cell_count}/{inactive_cell_count} mask is diagnostic, not accepted; "
            "no release/recontact method or uniqueness is claimed."
        ),
        "native_solve_executed": False,
        "floor_bearing_verified": False,
        "frame_ready_for_native_run": False,
        "complete_joint_validated": False,
    }
    model["floor_constraint_audit"] = floor_audit_out
    model["floor_selected_branch_constraint_audit"] = floor_audit_out
    model["floor_branch_metadata"] = {
        "branch_id": BRANCH,
        "status": "proposed_diagnostic_mask_only",
        "screen_packet_path": str(SCREEN),
        "screen_packet_sha256": PINS[str(SCREEN)],
        "positive_set_stable_at_all_7_printed_states": True,
        "printed_state_count": 7,
        "selected_cell_count": selected_cell_count,
        "inactive_cell_count": inactive_cell_count,
        "selected_source_tangent_row_count": active_count,
        "inactive_source_tangent_row_count": inactive_count,
        "first_bearing_reference": "zero",
        "selected_cells": selected_cells,
        "inactive_cells": inactive_cells,
        "normal_springa_carriers_changed": False,
        "displacement_preload_added": False,
        "friction_added": False,
        "anchor_added": False,
        "automatic_mask_iteration_authorized": False,
        "general_release_recontact_or_uniqueness_claimed": False,
        "selected_branch_screen_status": screen["status"],
        "selected_branch_screen_outputs_adopted": False,
        "physical_force_adoption": False,
    }
    model["source_load_emission_audit"] = {
        "source_cload_map_unchanged_from_frozen_controls": True,
        "source_cload_card_text_unchanged_from_frozen_controls": True,
        "source_cload_count": len(emitted_cload),
        "source_cload_value_map_sha256": digest([[n, d0, v] for (n, d0), v in sorted(emitted_cload.items())]),
        "floor_reference_nodes_receive_no_direct_cload": not any(n in refs_by_node for n, _ in emitted_cload),
    }
    model["serialized_selected_floor_equation_audit"] = {
        "serialized_equation_count_total": len(emitted_eq),
        "source_and_projection_equation_count_preserved": len(deck_eq) - 200,
        "serialized_selected_floor_equation_count": rank,
        "serialized_selected_floor_equation_term_count": term_count,
        "all_nonfloor_equations_unchanged": True,
        "S_times_H_emit_max_abs_reconstruction_residual": float(np.max(np.abs(h_resid))),
        "S_times_negative_E_emit_max_abs_identity_residual": float(np.max(np.abs(d_resid))),
        "correction_derived_from_emitted_E_and_CLOAD": True,
        "maximum_abs_emitted_vs_full_precision_reference_load_correction_N": float(np.max(np.abs(correction_emit - correction_full))),
        "maximum_abs_emitted_reference_load_correction_N": float(np.max(np.abs(correction_emit))),
        "selected_reference_node_tags_unique": len(refs_by_node) == active_count,
        "inactive_fixed_scalar_nodes_are_unconnected_carryovers": len(inactive_ref_tags) == inactive_count,
        "no_equation_or_reference_for_inactive_rows": True,
    }
    model["selected_floor_branch_screen_pin"] = {
        "path": str(SCREEN),
        "sha256": PINS[str(SCREEN)],
        "status": screen["status"],
        "diagnostic_only": True,
        "screen_positive_forces_or_active_states_reused_as_response": False,
    }
    model["response_route"] = {
        "whole_frame_source_audited_response_route_implemented": False,
        "selected_floor_response_auditor_required": True,
        "frame_ready_for_native_run": False,
        "mechanical_acceptance": False,
        "native_solve_authority_added": False,
    }
    model["claim_limits"] = list(source_model.get("claim_limits", [])) + [
        f"The selected {selected_cell_count}-cell mask is a proposed diagnostic branch, not an accepted floor support state.",
        f"Only {active_count} selected source tangent rows receive exact MPCs; {inactive_count} open-cell source rows receive no tangent restraint.",
        "No physical force adoption, floor/support qualification, branch uniqueness, or general release/recontact method is established.",
    ]

    protected = protected_model_fields(source_model)
    for key, expected in protected.items():
        if digest(model[key]) != expected:
            raise InputError(f"Frozen controls model field changed: {key}")
    if len(model["equations"]) != len(model_eq) - 200 + rank:
        raise InputError("Output selected floor equation count is incorrect")
    if len(refs_sorted) != active_count or len({int(x["node"]) for x in refs_sorted}) != active_count:
        raise InputError("Output must have one unique selected reference per active source row")
    if {int(x["node"]) for x in refs_sorted} - old_ref_tags:
        raise InputError("Selected active channels must bind to frozen scalar nodes")
    if {int(x["source_row_original_index"]) for x in refs_sorted} != set(active_rows):
        raise InputError("Selected refs must exactly cover active source rows")

    # One model/deck plus audit and pins. No freeze or solver process is created here.
    CASE.mkdir(parents=True, exist_ok=True)
    (CASE / "model.inp").write_text(output_deck, encoding="utf-8")
    write_json(CASE / "model.json", model)
    hashes = {"model.inp": sha(CASE / "model.inp"), "model.json": sha(CASE / "model.json")}
    write_json(HERE / "source-pins.json", {
        "schema": "current_springa_selected_floor_input_source_pins/v1",
        "pinned_inputs": pinned,
        "adapter_script_sha256": sha(HERE / "prepare.py"),
        "output_deck_sha256": hashes["model.inp"],
        "output_model_sha256": hashes["model.json"],
        "scope": f"One input-only proposed {selected_cell_count}-cell selected-bearing branch; no freeze, native solve, or response adoption.",
    })
    audit_out = {
        "schema": "current_springa_selected_floor_input_audit/v1",
        "status": "PASS_SELECTED_FLOOR_INPUT_ALGEBRA_AND_SOURCE_PRESERVATION",
        "model_schema": SCHEMA,
        "branch_id": BRANCH,
        "input_only": True,
        "native_solve_executed": False,
        "source_response_forces_read": False,
        "screen_packet": {
            "path": str(SCREEN),
            "sha256": PINS[str(SCREEN)],
            "status": screen["status"],
            "positive_set_stable_at_all_7_printed_states": True,
            "selected_cells": selected_cells,
            "inactive_cells": inactive_cells,
        },
        "selected_original_row_indices": sorted(active_rows),
        "inactive_original_row_indices": sorted(inactive_rows),
        "selected_equation_order_original_row_indices": [int(x) for x in selected_indices],
        "selected_rank": rank,
        "selected_S_condition_number": condition,
        "selected_A_S_H_D_reconstruction": {
            "A_shape": list(selected_a.shape), "S_shape": list(s.shape),
            "H_shape": list(h.shape), "D_shape": list(d.shape),
            "S_times_H_residual_max_abs": float(np.max(np.abs(s @ h - selected_a))),
            "S_times_D_identity_residual_max_abs": float(np.max(np.abs(s @ d - np.eye(rank)))),
            "serialized_S_times_H_residual_max_abs": float(np.max(np.abs(h_resid))),
            "serialized_S_times_negative_E_identity_residual_max_abs": float(np.max(np.abs(d_resid))),
            "S_condition_number": condition,
            "active_A_singular_values": singular.tolist(),
            "active_A_min_to_max_singular_ratio": float(singular[-1] / singular[0]),
        },
        "selected_source_point_wrench_preservation": {
            "status": "PASS_EXACT_SOURCE_POINT_BASIS_BINDING",
            "selected_row_count": active_count,
            "one_to_one_source_row_reference_mapping": True,
            "source_point_unit_force_and_first_moment_rows": [
                {
                    "source_row_original_index": int(x["source_row_original_index"]),
                    "source_row_id": str(x["source_row_id"]),
                    "normal_cell": str(x["normal_cell"]),
                    "source_point_xyz_mm": x["owner_floorpoint_xyz_mm"],
                    "unit_force_on_first_body_N": x["source_tangent_force_on_first_body_unit_N"],
                    "unit_moment_about_origin_on_first_body_Nmm": x["source_tangent_moment_about_global_origin_on_first_body_unit_Nmm"],
                }
                for x in refs_sorted
            ],
        },
        "source_preservation": {
            "protected_frozen_controls_value_hashes": protected,
            "source_geometry_elements_and_material_bindings_unchanged": True,
            "material_cards_unchanged": control_cards["materials"] == output_cards["materials"],
            "orientation_and_solid_section_cards_unchanged": control_cards["orientation_sections"] == output_cards["orientation_sections"],
            "source_cload_values_and_nodes_unchanged": source_cload == emitted_cload,
            "source_cload_card_text_unchanged": control_cards["cload"] == output_cards["cload"],
            "all_nonfloor_equations_unchanged": True,
            "bilateral_spring2_rows": len(model["springs"]),
            "normal_springa_rows": len(model["unilateral_springa_bindings"]),
            "physical_body_count": len(model["physical_body_nodes"]),
            "card40_controls_unchanged": output_deck.count("*STEP,NLGEOM,NLGEOM=NO,INC=40") == 1,
        },
        "serialized_floor_equation_audit": model["serialized_selected_floor_equation_audit"],
        "source_load_transfer": floor_audit_out["source_load_transfer"],
        "limits": [
            "The all-bearing diagnostic branch is rejected; its forces and active states are not adopted.",
            f"The selected {selected_cell_count}-cell mask remains a proposed hypothesis with no automatic mask iteration authority.",
            f"The {inactive_cell_count} inactive cells receive no tangent constraints; all 100 normal carriers stay unchanged.",
            "No physical force adoption, preload, friction, anchor, floor qualification, branch uniqueness, or release/recontact method is claimed.",
            "Prepared input only. No freeze, solver run, response ledger, or corner demands are included.",
        ],
        "output_sha256": hashes,
    }
    write_json(HERE / "audit.json", audit_out)
    (HERE / "README.md").write_text(
        "# Selected-bearing floor branch input adapter attempt 02\n\n"
        "This packet prepares one input-only branch from the frozen a12-rear controls model. "
        f"The proposed mask contains {selected_cell_count} diagnostic positive cells and {inactive_cell_count} separating cells, "
        "stable across seven printed states in the pinned screen. The screen rejected the "
        "all-bearing branch; its forces and active states are not reused as branch response.\n\n"
        f"Fresh exact tangential MPCs are emitted for the {active_count} selected source rows. The other "
        f"{inactive_count} source tangent rows have no active floor reference-map entry, selected equation, "
        f"or tangent restraint. The {inactive_count} old scalar tags remain isolated fixed output-only "
        "carryovers from controls and have no floor force map. All 100 normal "
        "SPRINGA carriers, 348 bilateral SPRING2 rows, source geometry/material/CLOAD data, "
        f"and INC=40 controls are preserved. The {rank}-row transform is full rank and its serialized "
        "A/S/H/D and transformed source-load maps are audited in audit.json and model.json.\n\n"
        "The branch is a monotone zero-gap first-bearing reference-zero hypothesis, not an "
        "accepted support state. No physical force adoption, floor qualification, uniqueness, "
        "or release/recontact method is claimed. This packet stops at deck/model/audit; it "
        "contains no freeze, native run, response ledger, or corner demands. Parent review is "
        "required before any execution.\n",
        encoding="utf-8",
    )
    return audit_out


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({
        "status": result["status"],
        "branch_id": result["branch_id"],
        "selected": len(result["screen_packet"]["selected_cells"]),
        "inactive": len(result["screen_packet"]["inactive_cells"]),
        "rank": result["selected_rank"],
        "outputs": result["output_sha256"],
    }, indent=2))
