"""Prepare, but never solve, the pinned full-load A12 fixed-episode dual QP."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re

import numpy as np
import scipy
import scipy.sparse as sp


ROOT = Path(__file__).resolve().parents[5]
BASE_REL = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
BASE = ROOT / BASE_REL
HERE = Path(__file__).resolve().parent
RUN = BASE / "current-springa-selected-floor-a12-rear-attempt03"
COMP = BASE / "current-frame-connector-compliance-attempt04"
REPLAY = BASE / "current-frame-connector-compliance-attempt04-a12-response-replay-attempt01"
REPLAY_SCRIPT = REPLAY / "replay.py"
REPLAY_ASSESSMENT = REPLAY / "assessment.json"
SOURCE_MODEL = BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
PROJECTION = BASE / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json"
LOAD_MAPS = BASE / "current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json"
SCREEN = BASE / "current-springa-selected-floor-branch-screen-attempt02/screen.json"
DUAL_METHOD = BASE / "current-floor-mask-dual-qp-fixture-attempt01"
MATRIX_PARSER = BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py"
RIGID_BASIS = BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py"
DAT_PARSER = BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"

ANSWER = HERE / "known-answer.npz"
ASSESSMENT = HERE / "assessment.json"
OUTPUT_PIN = HERE / "output-pin.json"
SCHEMA = "a12_fixed_episode_dual_qp_known_answer_preparation/v1"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def import_source(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot_import_pinned_source:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay_pins() -> dict[str, str]:
    """Read the literal PINNED map from the frozen replay without executing it."""
    tree = ast.parse(REPLAY_SCRIPT.read_text(encoding="utf-8"), filename=str(REPLAY_SCRIPT))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PINNED"
            for target in node.targets
        ):
            pins = ast.literal_eval(node.value)
            assert isinstance(pins, dict) and pins
            return pins
    raise AssertionError("frozen replay PINNED map not found")


def replay_pin_paths() -> dict[str, Path]:
    return {
        "run/response.json": RUN / "response.json",
        "run/model.dat": RUN / "model.dat",
        "run/model.inp": RUN / "model.inp",
        "run/model.json": RUN / "model.json",
        "run/freeze.json": RUN / "freeze.json",
        "run/execution.json": RUN / "execution.json",
        "run/parent-terminal-assessment.json": RUN / "parent-terminal-assessment.json",
        "run/parent-all-body-response-audit.json": RUN / "parent-all-body-response-audit.json",
        "comp/assessment.json": COMP / "assessment.json",
        "comp/inputs.json": COMP / "inputs.json",
        "comp/operators.npz": COMP / "operators.npz",
        "comp/B.npz": COMP / "B.npz",
        "comp/row-identities.json": COMP / "row-identities.json",
        "operator-native/model.dof": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof",
        "operator-native/model.sti": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.sti",
        "operator-native/freeze.json": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/freeze.json",
        "operator-native/execution.json": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/execution.json",
        "operator-native/assessment.json": BASE / "current-frame-pure-solid-matrix-export-native-attempt01/assessment.json",
        "source_model.json": SOURCE_MODEL,
        "projection/projection-contract.json": PROJECTION,
        "loads/source-load-maps.json": LOAD_MAPS,
        "matrix-parser": MATRIX_PARSER,
        "rigid-basis": RIGID_BASIS,
        "native-token-parser": DAT_PARSER,
    }


def boundary_reference_check(model: dict) -> None:
    """Confirm every selected scalar reference node is prescribed exactly zero."""
    deck_lines = (RUN / "model.inp").read_text(encoding="utf-8").splitlines()
    in_boundary = False
    boundary_rows: dict[int, tuple[int, int, float]] = {}
    for line in deck_lines:
        stripped = line.strip()
        if stripped.startswith("*"):
            in_boundary = stripped.upper() == "*BOUNDARY"
            continue
        if not in_boundary or not stripped or stripped.startswith("**"):
            continue
        fields = [field.strip() for field in stripped.split(",")]
        if len(fields) < 4:
            continue
        try:
            node = int(fields[0])
            first_dof, last_dof = int(fields[1]), int(fields[2])
            value = float(fields[3].replace("D", "E").replace("d", "e"))
        except ValueError:
            continue
        boundary_rows[node] = (first_dof, last_dof, value)
    references = {int(item["node"]) for item in model["floor_reference_nodes_and_load_map"]
                  if item["selected_floor_branch"] is True}
    assert len(references) == 50
    assert references == set(map(int, model["floor_reference_nodes"]))
    assert all(boundary_rows.get(node) == (1, 3, 0.0) for node in references)


def prepare() -> tuple[dict[str, np.ndarray], dict]:
    """Recover the authenticated full-load arrays and explicitly build QP S.

    No optimizer or native solver is invoked. The returned arrays are ready for
    a parent-owned, separately frozen solve/audit wrapper.
    """
    pins = replay_pins()
    fixed_paths = replay_pin_paths()
    assert set(pins) == set(fixed_paths), "replay PINNED path inventory changed"
    observed_source_pins = {name: sha(path) for name, path in fixed_paths.items()}
    assert observed_source_pins == pins, "frozen replay source pin mismatch"

    replay_report = read_json(REPLAY_ASSESSMENT)
    assert replay_report["status"] == "PASS_A12_REAR_AUTHENTICATED_RESPONSE_REPLAY_AGAINST_FROZEN_REDUCTION"
    assert replay_report["replay_script_sha256"] == sha(REPLAY_SCRIPT)
    response = read_json(RUN / "response.json")
    run_model = read_json(RUN / "model.json")
    response_body_audit = read_json(RUN / "parent-all-body-response-audit.json")
    assert response["status"] == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY"
    assert response["case_id"] == "a12-rear" and len(response["increments"]) == 7
    assert response["mechanical_acceptance"] is False
    assert response["joint_demand_accepted"] is False
    assert response["qualified_for_design"] is False
    assert response_body_audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
    assert response_body_audit["source_response_sha256"] == pins["run/response.json"]
    assert run_model["geometry_revision_id"] == response["geometry_revision_id"]

    branch = run_model["floor_branch_metadata"]
    assert branch["first_bearing_reference"] == "zero"
    assert branch["selected_cell_count"] == 25 and branch["inactive_cell_count"] == 75
    assert branch["selected_source_tangent_row_count"] == 50
    assert branch["inactive_source_tangent_row_count"] == 150
    # Preserve the earlier screen outcome separately from the later response
    # and all-body audits; it does not replace or invalidate their force data.
    screen = read_json(SCREEN)
    assert sha(SCREEN) == branch["screen_packet_sha256"]
    assert branch["status"] == "proposed_diagnostic_mask_only"
    assert branch["selected_branch_screen_status"] == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH"

    mask_rows = run_model["floor_selected_mask_by_original_row"]
    selected_tangent_by_cell: dict[str, list[bool]] = {}
    tangent_selected_by_row: dict[str, bool] = {}
    for item in mask_rows:
        selected_tangent_by_cell.setdefault(str(item["normal_cell"]), []).append(bool(item["selected"]))
        tangent_selected_by_row[str(item["source_row_id"])] = bool(item["selected"])
    assert len(mask_rows) == 200 and len(tangent_selected_by_row) == 200
    assert len(selected_tangent_by_cell) == 100
    assert all(len(values) == 2 and values[0] == values[1]
               for values in selected_tangent_by_cell.values())
    selected_cells = [cell for cell, values in selected_tangent_by_cell.items() if values[0]]
    assert set(selected_cells) == set(run_model["floor_selected_bearing_cells"])
    assert set(selected_cells).isdisjoint(set(run_model["floor_inactive_cells"]))
    assert len(selected_cells) == 25
    boundary_reference_check(run_model)

    projection = read_json(PROJECTION)["rows"]
    row_ids = read_json(COMP / "row-identities.json")
    assert len(projection) == len(row_ids) == 1840
    assert all(row_ids[i]["row_id"] == projection[i]["row_id"] for i in range(1840))
    families = [str(row["family"]) for row in projection]
    assert {family: families.count(family) for family in set(families)} == {
        "bilateral_spring2": 348,
        "unilateral_springa": 1292,
        "conditional_floor_tangent_constraint": 200,
    }
    tangent_rows = [i for i, row in enumerate(projection)
                    if row["family"] == "conditional_floor_tangent_constraint"]
    normal_rows_by_cell = {
        str(row["row_id"]): i for i, row in enumerate(projection)
        if row["family"] == "unilateral_springa"
        and row["ownership"].get("role") == "floor_normal"
    }
    assert len(normal_rows_by_cell) == 100
    assert set(normal_rows_by_cell) == set(selected_tangent_by_cell)
    assert all(row_ids[i]["row_id"] in tangent_selected_by_row for i in tangent_rows)
    tangent_projection_by_cell: dict[str, list[dict]] = {}
    for i in tangent_rows:
        row = projection[i]
        row_id = str(row["row_id"])
        assert "_friction/" in row_id
        cell, suffix = row_id.split("_friction/", 1)
        assert cell in normal_rows_by_cell and suffix in {"local-dof-2", "local-dof-3"}
        normal_row = projection[normal_rows_by_cell[cell]]
        assert row["ownership"]["first_body"] == normal_row["ownership"]["first_body"]
        assert row["ownership"]["second_body"] == normal_row["ownership"]["second_body"]
        assert row["ownership"]["point_mm"] == normal_row["ownership"]["point_mm"]
        expected_direction = {"local-dof-2": [0.0, 1.0, 0.0],
                              "local-dof-3": [-1.0, 0.0, 0.0]}[suffix]
        assert row["ownership"]["direction_global_xyz"] == expected_direction
        tangent_projection_by_cell.setdefault(cell, []).append(row)
    assert set(tangent_projection_by_cell) == set(normal_rows_by_cell)
    assert all(sorted(str(row["row_id"]).split("_friction/", 1)[1] for row in rows)
               == ["local-dof-2", "local-dof-3"]
               for rows in tangent_projection_by_cell.values())

    full_increment = [inc for inc in response["increments"]
                      if abs(float(inc["load_factor"]) - 1.0) <= 1e-14]
    assert len(full_increment) == 1
    increment = full_increment[0]
    assert abs(float(increment["time"]) - 1.0) <= 5e-8
    for inc in response["increments"]:
        active_ids = {str(row["source_row_id"]) for row in inc["exact_floor_tangent_reactions"]}
        inactive_ids = {str(row["source_row_id"]) for row in inc["inactive_floor_tangent_zero_actions"]}
        assert active_ids == {row_id for row_id, chosen in tangent_selected_by_row.items() if chosen}
        assert inactive_ids == {row_id for row_id, chosen in tangent_selected_by_row.items() if not chosen}
        assert len(active_ids) == 50 and len(inactive_ids) == 150
        assert inc["selected_floor_complementarity_passed"] is True
        assert inc["inactive_floor_tangent_no_restraint_or_reaction_passed"] is True

    operators_path = COMP / "operators.npz"
    with np.load(operators_path, allow_pickle=False) as op:
        H_raw = np.asarray(op["H"], dtype=np.float64)
        D = np.asarray(op["D"], dtype=np.float64)
        e_columns = np.asarray(op["e"], dtype=np.float64)
        W_columns = np.asarray(op["W"], dtype=np.float64)
    assert H_raw.shape == (1840, 1840) and D.shape == (1840, 300)
    assert e_columns.shape == (1840, 12) and W_columns.shape == (300, 12)
    replay_loads = replay_report["load_composition"]
    gravity_column = int(replay_loads["gravity_column"])
    climber_column = int(replay_loads["climber_column"])
    assert (gravity_column, climber_column) == (0, 1)
    load_factor = float(increment["load_factor"])
    # Native deck uses one proportional CLOAD: scale both sources by lambda.
    e_total = load_factor * (e_columns[:, gravity_column] + e_columns[:, climber_column])
    W_total = load_factor * (W_columns[:, gravity_column] + W_columns[:, climber_column])

    body_audit = read_json(COMP / "assessment.json")
    body_names = list(body_audit["body_names_in_rigid_column_order"])
    # The source model is JSON and is parsed by the pinned matrix helper.
    matrix_parser = import_source(MATRIX_PARSER, "a12_fixed_episode_matrix_parser")
    rigid = import_source(RIGID_BASIS, "a12_fixed_episode_rigid_basis")
    dat_parser = import_source(DAT_PARSER, "a12_fixed_episode_dat_parser")
    physical_source = matrix_parser.load_frame_source_model(SOURCE_MODEL)
    labels = matrix_parser.parse_dof_file(
        BASE / "current-frame-pure-solid-matrix-export-native-attempt01/model.dof")
    matrix_parser.require_dof_bijection(labels, physical_source["physical_nodes"], 37647)
    owners = np.asarray([physical_source["owner_by_node"][node]
                         for node, _ in labels], dtype=np.int64)
    assert body_names == list(physical_source["bodies"])
    source_native_model = read_json(RUN / "model.json")
    canonical_source_model = read_json(SOURCE_MODEL)
    assert canonical_source_model["physical_body_nodes"] == source_native_model["physical_body_nodes"]
    for node in physical_source["physical_nodes"]:
        assert canonical_source_model["nodes"][str(node)] == source_native_model["nodes"][str(node)]
    native_operator_dir = BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
    dof_path = native_operator_dir / "model.dof"
    # The response run DAT token parser is the exact source bound by the replay.
    dat = dat_parser.parse_native_blocks((RUN / "model.dat").read_text(encoding="utf-8"))
    time = float(increment["time"])
    assert time in dat
    state = dat[time]
    u = np.asarray([state["u"][node][direction - 1] for node, direction in labels], dtype=np.float64)
    u_radius = np.asarray([state["u_radius"][node][direction - 1]
                           for node, direction in labels], dtype=np.float64)
    B = sp.load_npz(COMP / "B.npz").tocsr()
    assert B.shape == (1840, 37647) and B.nnz == 62607
    q_native = np.asarray(B @ u, dtype=np.float64).reshape(-1)
    q_radius = np.asarray(abs(B) @ u_radius, dtype=np.float64).reshape(-1)

    a_native = np.zeros(300, dtype=np.float64)
    a_radius = np.zeros(300, dtype=np.float64)
    for body_no, _body_name in enumerate(body_names):
        dofs = np.flatnonzero(owners == body_no)
        body_labels = [labels[int(index)] for index in dofs]
        _, R, _ = rigid.rigid_basis(
            body_labels, physical_source["coordinates"], rotation_scale_mm=1000.0)
        projector = np.linalg.solve(R.T @ R, R.T)
        a_native[6 * body_no:6 * body_no + 6] = projector @ u[dofs]
        a_radius[6 * body_no:6 * body_no + 6] = np.abs(projector) @ u_radius[dofs]

    springa = {str(row["source_group"]): row for row in increment["springa_components"]}
    bilateral = {str(row["source_group"]): row
                 for row in increment["retained_bilateral_spring2_components"]}
    active_floor = {str(row["source_row_id"]): row
                    for row in increment["exact_floor_tangent_reactions"]}
    inactive_floor = {str(row["source_row_id"]): row
                      for row in increment["inactive_floor_tangent_zero_actions"]}
    assert len(springa) == 1292 and len(bilateral) == 348
    assert len(active_floor) == 50 and len(inactive_floor) == 150
    f_native_full = np.zeros(1840, dtype=np.float64)
    f_radius_full = np.zeros(1840, dtype=np.float64)
    k_full = np.zeros(1840, dtype=np.float64)
    for i, row in enumerate(projection):
        family = row["family"]
        source_group = str(row.get("source_group", ""))
        if family == "unilateral_springa":
            record = springa[source_group]
            f_native_full[i] = float(record["native_endpoint_internal_force_N"])
            f_radius_full[i] = float(record["native_endpoint_internal_radius_N"])
            k_full[i] = float(row["law"]["stiffness_N_per_mm"])
        elif family == "bilateral_spring2":
            record = bilateral[source_group]
            f_native_full[i] = float(record["force_on_first_local_N"])
            f_radius_full[i] = float(record["force_rounding_radius_local_N"])
            k_full[i] = float(row["law"]["stiffness_N_per_mm"])
        else:
            source_row_id = str(row["row_id"])
            # This projection inventory records floor-T cell association in
            # the scoped row ID (the normal row uses the prefix before
            # `_friction/`); ownership carries body, point, direction and
            # support class but no duplicate normal-cell field.
            assert "_friction/" in source_row_id
            cell = source_row_id.split("_friction/", 1)[0]
            assert cell in selected_tangent_by_cell
            if tangent_selected_by_row[source_row_id]:
                record = active_floor[source_row_id]
                direction = np.asarray(row["ownership"]["direction_global_xyz"], dtype=np.float64)
                action_radius = np.asarray(record["force_rounding_radius_xyz_n"], dtype=np.float64)
                f_native_full[i] = -float(record["recovered_physical_tangent_reaction_N"])
                f_radius_full[i] = float(np.abs(direction) @ action_radius)
                assert abs(float(record["raw_reference_rf_N"])
                           - float(record["transferred_source_load_N"])
                           - float(record["recovered_physical_tangent_reaction_N"])) <= 2e-12
            else:
                record = inactive_floor[source_row_id]
                assert record["native_reference_or_tangent_equation_present"] is False
                assert record["native_tangent_spring_present"] is False
                assert record["carryover_rf_interval_contains_zero"] is True
                assert record["force_on_first_xyz_n"] == [0.0, 0.0, 0.0]

    # The global projection inventory contains repeated textual row IDs for
    # some paired contact operators. Floor-normal cell IDs are unique, so use
    # those scoped identities plus array positions rather than assuming all
    # 1,840 row labels are unique.
    floor_normal_row_ids = normal_rows_by_cell
    open_normal_rows = sorted(floor_normal_row_ids[cell] for cell in selected_tangent_by_cell
                              if not selected_tangent_by_cell[cell][0])
    closed_normal_rows = sorted(floor_normal_row_ids[cell] for cell in selected_cells)
    held_tangent_rows = sorted(i for i in tangent_rows
                               if tangent_selected_by_row[str(projection[i]["row_id"])])
    released_tangent_rows = sorted(i for i in tangent_rows
                                   if not tangent_selected_by_row[str(projection[i]["row_id"])])
    assert len(open_normal_rows) == 75 and len(closed_normal_rows) == 25
    assert len(held_tangent_rows) == 50 and len(released_tangent_rows) == 150

    # Fixed-mask force variables: every non-floor unilateral row, the 25
    # closed floor normals, all 348 bilateral rows, and 50 held floor T rows.
    omitted_rows = set(open_normal_rows) | set(released_tangent_rows)
    active_rows = np.asarray([i for i in range(1840) if i not in omitted_rows], dtype=np.int64)
    assert len(active_rows) == 1615
    active_position = {int(row): position for position, row in enumerate(active_rows)}
    nonnegative_positions = np.asarray([
        active_position[i] for i, row in enumerate(projection)
        if row["family"] == "unilateral_springa" and i not in omitted_rows
    ], dtype=np.int64)
    assert len(nonnegative_positions) == 1217
    assert sum(projection[int(i)]["family"] == "bilateral_spring2" for i in active_rows) == 348
    assert sum(projection[int(i)]["family"] == "conditional_floor_tangent_constraint"
               for i in active_rows) == 50
    assert sum(projection[int(i)]["family"] == "unilateral_springa" for i in active_rows) == 1217

    Hsym = 0.5 * (H_raw + H_raw.T)
    Hsym_active = Hsym[np.ix_(active_rows, active_rows)]
    inverse_k_active = np.asarray([
        1.0 / k_full[int(i)] if projection[int(i)]["family"] != "conditional_floor_tangent_constraint"
        else 0.0
        for i in active_rows
    ], dtype=np.float64)
    assert np.isfinite(inverse_k_active).all() and np.all(inverse_k_active >= 0.0)
    S = Hsym_active + np.diag(inverse_k_active)
    held_reference_active = np.zeros(len(active_rows), dtype=np.float64)
    e_active = e_total[active_rows]
    linear = -e_active + held_reference_active
    D_active = D[active_rows, :]
    f_native_active = f_native_full[active_rows]

    # Independent native-state raw-H audit; S/Hsym are not used here.
    q_pred_raw = D @ a_native + e_total - H_raw @ f_native_full
    q_pred_sym = D @ a_native + e_total - Hsym @ f_native_full
    q_residual = q_native - q_pred_raw
    q_arithmetic_guard = 128.0 * np.finfo(float).eps * (
        np.abs(q_native) + np.abs(D) @ np.abs(a_native) + np.abs(e_total)
        + np.abs(H_raw) @ np.abs(f_native_full) + 1.0
    )
    q_bound = q_radius + np.abs(D) @ a_radius + np.abs(H_raw) @ f_radius_full + q_arithmetic_guard
    q_ratio = np.abs(q_residual) / np.maximum(q_bound, np.finfo(float).tiny)
    wrench_residual = D.T @ f_native_full - W_total
    wrench_arithmetic_guard = 128.0 * np.finfo(float).eps * (
        np.abs(D.T) @ np.abs(f_native_full) + np.abs(W_total) + 1.0
    )
    wrench_bound = np.abs(D.T) @ f_radius_full + wrench_arithmetic_guard
    wrench_ratio = np.abs(wrench_residual) / np.maximum(wrench_bound, np.finfo(float).tiny)
    assert np.all(np.abs(q_residual) <= q_bound)
    assert np.all(np.abs(wrench_residual) <= wrench_bound)

    # Raw native q/f law intervals and floor state classifications.
    spring_law_ratio = 0.0
    spring_law_max_error = 0.0
    for i, row in enumerate(projection):
        family = row["family"]
        if family == "bilateral_spring2":
            expected_force = k_full[i] * q_native[i]
        elif family == "unilateral_springa":
            expected_force = k_full[i] * max(float(q_native[i]), 0.0)
        else:
            continue
        error = abs(f_native_full[i] - expected_force)
        error_bound = f_radius_full[i] + k_full[i] * q_radius[i]
        ratio = error / max(error_bound, np.finfo(float).tiny)
        spring_law_max_error = max(spring_law_max_error, float(error))
        spring_law_ratio = max(spring_law_ratio, float(ratio))

    closed_normal_status_by_increment = []
    open_normal_status_by_increment = []
    for inc in response["increments"]:
        normal_records = {str(row["source_group"]): row for row in inc["springa_components"]}
        assert len(normal_records) == 1292
        closed_status = []
        open_status = []
        for cell, row_position in floor_normal_row_ids.items():
            row = projection[row_position]
            record = normal_records[str(row["source_group"])]
            if cell in selected_cells:
                closed_status.append(bool(record["strictly_positive_floor_normal_after_rounding"]))
            else:
                open_status.append(bool(record["strictly_separated_floor_normal_with_zero_rf_after_rounding"]))
        assert len(closed_status) == 25 and all(closed_status)
        assert len(open_status) == 75 and all(open_status)
        closed_normal_status_by_increment.append(closed_status)
        open_normal_status_by_increment.append(open_status)
    held_q_ratios = [abs(float(q_native[i])) / max(float(q_radius[i]), np.finfo(float).tiny)
                     for i in held_tangent_rows]
    assert max(held_q_ratios, default=0.0) <= 1.0 + 1e-10

    source_paths = {
        **{f"response_replay_pin:{name}": path for name, path in fixed_paths.items()},
        "response_replay_assessment": REPLAY_ASSESSMENT,
        "response_replay_script": REPLAY_SCRIPT,
        "selected_branch_screen": SCREEN,
        "dual_qp_method": DUAL_METHOD / "solve_fixture.py",
        "dual_qp_method_assessment": DUAL_METHOD / "fixed-mask-dual-qp.json",
        "this_readme": HERE / "README.md",
        "this_producer": HERE / "prepare.py",
    }
    source_hashes = {name: sha(path) for name, path in sorted(source_paths.items())}
    arrays = {
        "S": S,
        "D_active": D_active,
        "linear_objective": linear,
        "W_total": W_total,
        "e_total_full": e_total,
        "active_row_positions": active_rows,
        "nonnegative_active_positions": nonnegative_positions,
        "open_floor_normal_rows": np.asarray(open_normal_rows, dtype=np.int64),
        "closed_floor_normal_rows": np.asarray(closed_normal_rows, dtype=np.int64),
        "held_floor_tangent_rows": np.asarray(held_tangent_rows, dtype=np.int64),
        "released_floor_tangent_rows": np.asarray(released_tangent_rows, dtype=np.int64),
        "selected_cell_ids": np.asarray(sorted(selected_cells), dtype="U96"),
        "open_cell_ids": np.asarray(sorted(set(selected_tangent_by_cell) - set(selected_cells)), dtype="U96"),
        "active_row_ids": np.asarray([str(projection[int(i)]["row_id"]) for i in active_rows], dtype="U128"),
        "active_row_family": np.asarray([str(projection[int(i)]["family"]) for i in active_rows], dtype="U48"),
        "body_names_rigid_column_order": np.asarray(body_names, dtype="U64"),
        "k_active": k_full[active_rows],
        "held_reference_active_mm": held_reference_active,
        "f_native_active_N": f_native_active,
        "f_native_full_N": f_native_full,
        "f_native_rounding_radius_full_N": f_radius_full,
        "q_native_full_mm": q_native,
        "q_native_DAT_rounding_radius_full_mm": q_radius,
        "a_native_mm_and_scaled_rotation": a_native,
        "a_native_DAT_rounding_radius": a_radius,
    }
    metadata = {
        "schema": SCHEMA,
        "status": "PREPARED_A12_FIXED_EPISODE_KNOWN_ANSWER_NO_SOLVE",
        "producer_runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "openblas_num_threads_environment": os.environ.get("OPENBLAS_NUM_THREADS", "unset"),
        },
        "candidate": response["candidate"],
        "case_id": response["case_id"],
        "geometry_revision_id": response["geometry_revision_id"],
        "response_sha256": pins["run/response.json"],
        "response_replay_assessment_sha256": sha(REPLAY_ASSESSMENT),
        "response_replay_script_sha256": sha(REPLAY_SCRIPT),
        "source_sha256": source_hashes,
        "native_response_scope": {
            "response_status": response["status"],
            "parent_all_body_response_audit_status": response_body_audit["status"],
            "mechanical_acceptance": response["mechanical_acceptance"],
            "joint_demand_accepted": response["joint_demand_accepted"],
            "qualified_for_design": response["qualified_for_design"],
            "earlier_screen_status": branch["selected_branch_screen_status"],
            "branch_metadata_status": branch["status"],
            "force_source": "authenticated native response force export, not earlier rejected screen force output",
        },
        "load_case": {
            "load_factor": load_factor,
            "native_step_rule": "lambda*(gravity + climber) in the same single proportional CLOAD step",
            "gravity_column": gravity_column,
            "climber_column": climber_column,
            "used_e": "1.0*(e_gravity + e_climber)",
            "used_W": "1.0*(W_gravity + W_climber)",
            "not_a_gravity_settle_climber_ramp": True,
        },
        "fixed_episode": {
            "selected_cells": sorted(selected_cells),
            "selected_cell_count": len(selected_cells),
            "open_cell_count": len(selected_tangent_by_cell) - len(selected_cells),
            "held_tangent_rows": len(held_tangent_rows),
            "released_tangent_rows": len(released_tangent_rows),
            "first_bearing_reference": branch["first_bearing_reference"],
            "held_q_reference_mm": 0.0,
            "closed_floor_normals_strictly_positive_every_increment": all(
                all(statuses) for statuses in closed_normal_status_by_increment),
            "closed_floor_normal_row_count": len(closed_normal_rows),
            "open_floor_normal_strict_separation_every_increment": all(
                all(statuses) for statuses in open_normal_status_by_increment),
            "open_floor_normal_row_count": len(open_normal_rows),
        },
        "floor_tangent_join": {
            "cell_join": "pinned projection row_id prefix before `_friction/`; each pair checked against the normal row's first/second body and exact support point",
            "rows_per_cell": 2,
            "global_direction_by_row_suffix": {
                "local-dof-2": [0.0, 1.0, 0.0],
                "local-dof-3": [-1.0, 0.0, 0.0],
            },
            "source_force_sign": "stored f_T = -recovered physical tangent reaction; raw-reference RF minus transferred source load minus physical tangent reaction is checked",
            "held_reference_mm": 0.0,
            "closed_cells": len(selected_cells),
            "open_cells": len(selected_tangent_by_cell) - len(selected_cells),
        },
        "dual_qp": {
            "objective": "0.5*f_A.T*S*f_A + (-e_total_A + r_A).T*f_A",
            "equality": "D_A.T*f_A = W_total",
            "inequalities": "f_A >= 0 for 1,217 active unilateral spring rows; all other active variables signed",
            "S_definition": "Hsym[A,A] + diag(1/k for finite spring rows, 0 for held floor-T rows), Hsym=(Hraw+Hraw.T)/2",
            "active_variable_count": len(active_rows),
            "active_family_counts": {
                "bilateral_spring2": 348,
                "unilateral_springa": 1217,
                "held_floor_tangent": 50,
            },
            "omitted_exact_zero_force_rows": {
                "open_floor_normal": len(open_normal_rows),
                "released_floor_tangent": len(released_tangent_rows),
            },
            "qp_solve_executed": False,
        },
        "native_raw_h_audit": {
            "compatibility_definition": "q_native = D*a_native + e_total - H_raw*f_native_full",
            "max_abs_q_residual_mm": float(np.max(np.abs(q_residual), initial=0.0)),
            "max_residual_to_DAT_interval_ratio": float(np.max(q_ratio, initial=0.0)),
            "max_abs_raw_vs_symmetric_H_q_shift_mm": float(np.max(np.abs(q_pred_raw - q_pred_sym), initial=0.0)),
            "max_raw_force_balance_residual_N": float(np.max(np.abs(wrench_residual.reshape(50, 6)[:, :3]), initial=0.0)),
            "max_raw_moment_balance_residual_Nmm": float(1000.0 * np.max(np.abs(wrench_residual.reshape(50, 6)[:, 3:]), initial=0.0)),
            "max_wrench_residual_to_DAT_interval_ratio": float(np.max(wrench_ratio, initial=0.0)),
            "max_source_spring_law_residual_N": spring_law_max_error,
            "max_source_spring_law_residual_to_DAT_interval_ratio": spring_law_ratio,
            "DAT_interval_scope": "Printed U/RF half-last-place bounds plus propagated B, rigid-gauge, raw-H and D.T operations; operator KKT diagnostics stay separate.",
        },
        "parent_run_gates": [
            "Only OSQP status exactly `solved` is accepted; reject `solved inaccurate`, time/budget stops, and incomplete output.",
            "Check D.T*f=W and report body force residuals in N and moments in N mm separately; general gates 0.1 N and 2 N mm are distinct from DAT intervals.",
            "Audit q=D*a+e-H_raw*f using original unsymmetrized H over all 1,840 rows; do not use S/Hsym for this check.",
            "Check bilateral f=k*q and unilateral f=k*max(q,0), with nonnegative unilateral forces and KKT signs.",
            "Check 25 selected floor normals strictly bearing, 75 open normals f=0 and q<0, 50 held T rows q=0/reference, and 150 released T rows force=0 with q free.",
            "Compare QP outputs with exact source DAT-derived force/U intervals as a separate gate; do not widen token bounds. Record STOP if QP values exceed them even when the general residual gates pass.",
            "No uniqueness, state-selection, recontact, gravity-ramp, or frame-acceptance claim; stop on gauge, event-boundary, or unresolved nonuniqueness without adding anchors.",
        ],
        "scope": {
            "input_only": True,
            "projection_row_identity": "array positions in the pinned projection contract; textual row_id is not globally unique",
            "body_coordinates": "six rigid coordinates per body in body_names_rigid_column_order; rotation scale 1000 mm",
            "native_run": False,
            "qp_solve": False,
            "H_rebuilt": False,
            "heavy_rank_or_factor": False,
            "geometry_changed": False,
        },
    }
    return arrays, metadata


def write_inputs(arrays: dict[str, np.ndarray], metadata: dict) -> None:
    np.savez_compressed(ANSWER, **arrays)
    report = dict(metadata)
    report["known_answer_sha256"] = sha(ANSWER)
    report["producer_sha256"] = sha(HERE / "prepare.py")
    report["readme_sha256"] = sha(HERE / "README.md")
    ASSESSMENT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
                          encoding="utf-8")
    OUTPUT_PIN.write_text(json.dumps({"assessment_sha256": sha(ASSESSMENT)},
                                     indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_inputs(arrays: dict[str, np.ndarray], metadata: dict) -> None:
    report = read_json(ASSESSMENT)
    assert report["known_answer_sha256"] == sha(ANSWER)
    assert report["producer_sha256"] == sha(HERE / "prepare.py")
    assert report["readme_sha256"] == sha(HERE / "README.md")
    assert {key: value for key, value in report.items()
            if key not in {"known_answer_sha256", "producer_sha256", "readme_sha256"}} == metadata
    assert read_json(OUTPUT_PIN) == {"assessment_sha256": sha(ASSESSMENT)}
    with np.load(ANSWER, allow_pickle=False) as stored:
        assert set(stored.files) == set(arrays)
        for name, expected in arrays.items():
            assert np.array_equal(stored[name], expected), f"known-answer array changed: {name}"


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write-inputs", action="store_true")
    modes.add_argument("--verify-inputs", action="store_true")
    args = parser.parse_args()
    arrays, metadata = prepare()
    if args.write_inputs:
        write_inputs(arrays, metadata)
        print("Wrote A12 fixed-episode QP inputs; no solve was run")
    else:
        verify_inputs(arrays, metadata)
        print("PASS_A12_FIXED_EPISODE_INPUTS: source pins, native answer, and S construction")


if __name__ == "__main__":
    main()
