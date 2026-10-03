#!/usr/bin/env python3
"""Read-only replay of the authenticated a12-rear response against frozen H/D/e/W."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import scipy.sparse as sp


ROOT = Path(__file__).resolve().parents[5]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
HERE = ROOT / BASE / "current-frame-connector-compliance-attempt04-a12-response-replay-attempt01"
COMP = ROOT / BASE / "current-frame-connector-compliance-attempt04"
RUN = ROOT / BASE / "current-springa-selected-floor-a12-rear-attempt03"
OPERATOR_NATIVE = ROOT / BASE / "current-frame-pure-solid-matrix-export-native-attempt01"
SOURCE_MODEL = ROOT / BASE / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
PROJECTION = ROOT / BASE / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json"
LOAD_MAPS = ROOT / BASE / "current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json"
ASSESSMENT_PATH = HERE / "assessment.json"
OUTPUT_SCHEMA = "a12_rear_authenticated_frame_response_replay_against_H_D_e_W/v1"

# Exact evidence selected for this one read-only check. These pins prevent the
# response, reduction, physical-row map, or parser from drifting silently.
PINNED = {
    "run/response.json": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    "run/model.dat": "1f98a6737908286b86771ec4184e8ab08a4b3c1ce95b48a2d42e8284353ffd54",
    "run/model.inp": "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff",
    "run/model.json": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "run/freeze.json": "a362e551a39afcaed06ecbf0a0f1f18858fbc8677bdf2a927652b543ac67eb03",
    "run/execution.json": "6827b199681a574b744460e5b2b0e171a26fd68a51093843a897e1abb9744f00",
    "run/parent-terminal-assessment.json": "e19dd495bf6ca910a0aa6a070e38dfc00e214974d8e62fbf72624387c80ce075",
    "run/parent-all-body-response-audit.json": "3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5",
    "comp/assessment.json": "ae30902f9340875a771d60dab83621ab5e0d6dcadb58c06a35bdb1bc8ac9da6c",
    "comp/inputs.json": "3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208",
    "comp/operators.npz": "88a2f2f384edb7be7daa0e20cc87c7b8672ed13e975f8e86afd56d8aeb385b79",
    "comp/B.npz": "15470db045b2d78250cb96ec4a2a2c2d1d2f81a32c8408b08b96a8cb2ea1e220",
    "comp/row-identities.json": "768d2afe58b48fa482f118f73bb01b8c911d1f937a5891d5c420a0d821b45037",
    "operator-native/model.dof": "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    "operator-native/model.sti": "7d22d2b013fcdc9fddfeab589b456615f0671db989a034e091bac855f3a93c01",
    "operator-native/freeze.json": "614c9b466fd05c0b5ee6917aa26e108fd8151b36459b8b84999cd474f13d9ed3",
    "operator-native/execution.json": "979a3c5ad07d5569f7b805754ac3f136dbecc0865f5990c3f1f7780d4048d5d6",
    "operator-native/assessment.json": "ba41b9c75815f7daf27b3517ac01afff109d5f3e3611aa985811e92c269e69ec",
    "source_model.json": "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    "projection/projection-contract.json": "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3",
    "loads/source-load-maps.json": "9cd59d7bbafd65c740d2b0200e3dd88a6a49e6dca0bead0a38bc7826e337548c",
    "matrix-parser": "7abfeb3b02843588651b440dba4a86ae3f85106557383225a50c09b5cb080632",
    "rigid-basis": "7a887915cf84bcfef94c204baa2f47e428f81cead5c220101d9c225d2838de63",
    "native-token-parser": "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def import_source(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"source_not_importable:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def max_abs(values: np.ndarray) -> float:
    return float(np.max(np.abs(values))) if values.size else 0.0


def main() -> None:
    fixed_paths = {
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
        "operator-native/model.dof": OPERATOR_NATIVE / "model.dof",
        "operator-native/model.sti": OPERATOR_NATIVE / "model.sti",
        "operator-native/freeze.json": OPERATOR_NATIVE / "freeze.json",
        "operator-native/execution.json": OPERATOR_NATIVE / "execution.json",
        "operator-native/assessment.json": OPERATOR_NATIVE / "assessment.json",
        "source_model.json": SOURCE_MODEL,
        "projection/projection-contract.json": PROJECTION,
        "loads/source-load-maps.json": LOAD_MAPS,
        "matrix-parser": ROOT / BASE / "current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py",
        "rigid-basis": ROOT / BASE / "current-frame-free-body-condensation-preflight-attempt01/condensation.py",
        "native-token-parser": ROOT / BASE / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py",
    }
    observed_hashes = {name: sha(path) for name, path in fixed_paths.items()}
    for name, expected in PINNED.items():
        require(observed_hashes.get(name) == expected, f"pinned_sha256_mismatch:{name}")

    # Authenticate the already-run physical response and the parent’s recorded
    # all-body validation. This script never launches or retries a solver.
    response = load_json(RUN / "response.json")
    execution = load_json(RUN / "execution.json")
    freeze = load_json(RUN / "freeze.json")
    terminal = load_json(RUN / "parent-terminal-assessment.json")
    body_audit = load_json(RUN / "parent-all-body-response-audit.json")
    require(response.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY",
            "a12_response_status_not_authenticated")
    require(response.get("case_id") == "a12-rear" and len(response.get("increments", [])) == 7,
            "unexpected_response_case_or_increment_count")
    provenance = response.get("terminal_execution_provenance", {})
    require(provenance.get("freeze_sha256") == sha(RUN / "freeze.json")
            and provenance.get("execution_sha256") == sha(RUN / "execution.json")
            and provenance.get("native_output_hashes_match") is True
            and provenance.get("container_confirmed_terminal") is True
            and provenance.get("solver_error_markers_absent") is True,
            "recorded_native_execution_provenance_not_authenticated")
    require(execution.get("native_solve_executed") is True and execution.get("returncode") == 0
            and execution.get("container_confirmed_terminal") is True,
            "a12_native_execution_not_successfully_terminal")
    require(freeze.get("files_sha256", {}).get("model.inp") == PINNED["run/model.inp"]
            and freeze.get("files_sha256", {}).get("model.json") == PINNED["run/model.json"],
            "a12_freeze_does_not_bind_exact_run_inputs")
    require(execution.get("outputs_sha256", {}).get("model.dat") == PINNED["run/model.dat"],
            "a12_execution_record_does_not_bind_exact_native_DAT")
    require(terminal.get("status") == "PASS_CONDITIONAL_NUMERICAL_RESPONSE"
            and terminal.get("response_sha256") == PINNED["run/response.json"]
            and terminal.get("independent_parent_all_body_pass") is True,
            "parent_terminal_assessment_not_pass")
    require(body_audit.get("status") == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
            and body_audit.get("source_response_sha256") == PINNED["run/response.json"],
            "parent_all_body_audit_not_bound_to_response")
    require(response.get("mechanical_acceptance") is False
            and response.get("joint_demand_accepted") is False
            and response.get("qualified_for_design") is False,
            "response_claims_acceptance_outside_replay_scope")

    comp_record = load_json(COMP / "assessment.json")
    comp_inputs = load_json(COMP / "inputs.json")
    require(comp_record.get("status") == "PASS_SOURCE_BOUND_FRAME_CONNECTOR_COMPLIANCE",
            "frozen_compliance_record_not_pass")
    require(comp_record.get("input_record_sha256") == sha(COMP / "inputs.json")
            and load_json(COMP / "output-pin.json").get("assessment_sha256") == sha(COMP / "assessment.json"),
            "compliance_input_or_output_pin_mismatch")
    # Replay the existing provenance manifest without rebuilding any operator.
    changed_sources = []
    changed_snapshots = []
    for relative, expected in comp_inputs.get("source_sha256", {}).items():
        source_path = ROOT / relative
        if not source_path.is_file() or sha(source_path) != expected:
            changed_sources.append(relative)
        if source_path.suffix == ".py":
            snapshot = COMP / "sources" / relative
            if not snapshot.is_file() or sha(snapshot) != expected:
                changed_snapshots.append(relative)
    require(not changed_sources and not changed_snapshots,
            "frozen_compliance_source_lineage_changed")
    for name, expected in comp_record.get("outputs_sha256", {}).items():
        require(sha(COMP / name) == expected, f"compliance_output_hash_mismatch:{name}")

    projection_contract = load_json(PROJECTION)
    row_ids = load_json(COMP / "row-identities.json")
    projected_rows = projection_contract["rows"]
    require(len(row_ids) == len(projected_rows) == 1840
            and all(row_ids[i]["row_id"] == projected_rows[i]["row_id"] for i in range(1840)),
            "operator_row_identity_order_mismatch")
    with np.load(COMP / "operators.npz") as operators:
        H = operators["H"]
        D = operators["D"]
        e = operators["e"]
        W = operators["W"]
    B = sp.load_npz(COMP / "B.npz").tocsr()
    require(B.shape == (1840, 37647) and B.nnz == 62607
            and H.shape == (1840, 1840) and D.shape == (1840, 300)
            and e.shape == (1840, 12) and W.shape == (300, 12),
            "operator_dimensions_or_source_row_count_changed")

    matrix_parser = import_source(fixed_paths["matrix-parser"], "pinned_matrixstorage_parser_for_a12_replay")
    rigid = import_source(fixed_paths["rigid-basis"], "pinned_free_body_rigid_basis_for_a12_replay")
    dat_parser = import_source(fixed_paths["native-token-parser"], "pinned_ccx223_dat_parser_for_a12_replay")
    source = matrix_parser.load_frame_source_model(SOURCE_MODEL)
    labels = matrix_parser.parse_dof_file(OPERATOR_NATIVE / "model.dof")
    matrix_parser.require_dof_bijection(labels, source["physical_nodes"], 37647)
    owners = np.asarray([source["owner_by_node"][node] for node, _ in labels], dtype=np.int64)
    body_names = list(source["bodies"])
    require(body_names == comp_record["body_names_in_rigid_column_order"],
            "rigid_body_order_differs_from_operator_build")

    source_record = load_json(SOURCE_MODEL)
    native_record = load_json(RUN / "model.json")
    require(source_record["physical_body_nodes"] == native_record["physical_body_nodes"],
            "physical_body_node_ownership_differs_between_operator_and_response")
    for node in source["physical_nodes"]:
        require(source_record["nodes"][str(node)] == native_record["nodes"][str(node)],
                f"physical_node_coordinate_differs:{node}")

    load_record = load_json(LOAD_MAPS)
    load_cases = [case for case in load_record["cases"] if case["case_id"] == "a12-rear"]
    require(len(load_cases) == 1, "a12_rear_source_load_maps_not_unique")
    load_case = load_cases[0]
    columns = comp_record["load_columns"]
    selected_columns = {
        row["kind"]: int(row["column"])
        for row in columns if row["case_id"] == "a12-rear"
    }
    require(selected_columns == {"gravity_nodal_map": 0, "climber_nodal_map": 1},
            "a12_rear_gravity_climber_column_identity_changed")

    deck = (RUN / "model.inp").read_text(encoding="utf-8")
    require(len(re.findall(r"^\*CLOAD\s*$", deck, flags=re.MULTILINE | re.IGNORECASE)) == 1
            and not re.search(r"^\*DLOAD(?:,|\s|$)", deck, flags=re.MULTILINE | re.IGNORECASE),
            "a12_load_deck_no_longer_uses_single_proportional_cload_map")
    cload = dat_parser._parse_cload_cards(deck)
    combined = {}
    for load_name in ("gravity_nodal_map", "climber_nodal_map"):
        for node_text, vector in load_case[load_name].items():
            node = int(node_text)
            for direction, force in enumerate(vector, 1):
                key = (node, direction)
                combined[key] = combined.get(key, 0.0) + float(force)
    deck_keys = set(cload)
    source_keys = set(combined)
    max_cload_difference = max(
        (abs(cload.get(key, 0.0) - combined.get(key, 0.0)) for key in deck_keys | source_keys),
        default=0.0,
    )
    omitted_source_load_max = max((abs(combined[key]) for key in source_keys - deck_keys), default=0.0)
    require(max_cload_difference <= 1.0e-8 and omitted_source_load_max <= 1.0e-8,
            "emitted_a12_cload_map_differs_from_gravity_plus_climber_source")
    load_audit = response.get("source_load_normalization_audit", {})
    emission_audit = response.get("source_load_emission_audit", {})
    require(load_audit.get("expanded_map_matches_fresh_physical_external_loads") is True
            and load_audit.get("raw_and_expanded_wrench_transfer_passed") is True
            and emission_audit.get("source_cload_map_unchanged_from_frozen_controls") is True,
            "recorded_a12_load_normalization_or_emission_audit_not_pass")

    dat = dat_parser.parse_native_blocks((RUN / "model.dat").read_text(encoding="utf-8"))
    increments = response["increments"]
    require(set(dat) == {float(inc["time"]) for inc in increments},
            "native_DAT_and_authenticated_response_times_differ")
    native_nodes = {int(node) for node in native_record["nodes"]}
    require(all(set(block["u"]) == native_nodes and set(block["rf"]) == native_nodes
                for block in dat.values()),
            "DAT_U_RF_node_inventory_incomplete")

    body_index = {name: i for i, name in enumerate(body_names)}
    by_family = {"unilateral_springa": 0, "bilateral_spring2": 0,
                 "conditional_floor_tangent_constraint": 0}
    for row in row_ids:
        by_family[row["family"]] += 1
    require(by_family == {"unilateral_springa": 1292, "bilateral_spring2": 348,
                          "conditional_floor_tangent_constraint": 200},
            "operator_row_family_inventory_changed")

    per_increment = []
    global_max_q_reference_ratio = 0.0
    global_max_q_balance_ratio = 0.0
    global_max_wrench_ratio = 0.0
    active_floor_rows_seen = 0
    inactive_floor_rows_seen = 0
    q_reference_checks = 0
    for increment in increments:
        time = float(increment["time"])
        load_factor = float(increment["load_factor"])
        require(math.isclose(time, load_factor, rel_tol=0.0, abs_tol=5.0e-8),
                "static_load_factor_does_not_match_printed_native_time")
        state = dat[time]
        u = np.asarray([state["u"][node][direction - 1] for node, direction in labels], dtype=np.float64)
        ur = np.asarray([state["u_radius"][node][direction - 1] for node, direction in labels], dtype=np.float64)
        q = np.asarray(B @ u).reshape(-1)
        qr = np.asarray(abs(B) @ ur).reshape(-1)

        springa = {str(row["source_group"]): row for row in increment["springa_components"]}
        bilateral = {str(row["source_group"]): row for row in increment["retained_bilateral_spring2_components"]}
        floor_active = {str(row["source_row_id"]): row for row in increment["exact_floor_tangent_reactions"]}
        floor_inactive = {str(row["source_row_id"]): row for row in increment["inactive_floor_tangent_zero_actions"]}
        require(len(springa) == 1292 and len(bilateral) == 348
                and len(floor_active) == 50 and len(floor_inactive) == 150
                and set(floor_active).isdisjoint(floor_inactive),
                "response_source_force_row_coverage_changed")

        f = np.zeros(1840, dtype=np.float64)
        fr = np.zeros(1840, dtype=np.float64)
        q_reference_max_difference = 0.0
        q_reference_max_bound = 0.0
        q_reference_max_ratio = 0.0
        active_floor_max_abs_q = 0.0
        active_floor_max_radius = 0.0
        floor_active_sign_checks = 0
        for index, row in enumerate(row_ids):
            family = row["family"]
            if family == "unilateral_springa":
                record = springa[str(row["source_group"])]
                f[index] = float(record["native_endpoint_internal_force_N"])
                fr[index] = float(record["native_endpoint_internal_radius_N"])
                observed_q = float(record["q_relative_projection_mm"])
                observed_q_radius = float(record["q_relative_projection_radius_mm"])
                require(record["native_endpoint_action_reaction_passed"] is True,
                        f"SPRINGA_source_force_sign_audit_failed:{row['source_group']}")
            elif family == "bilateral_spring2":
                record = bilateral[str(row["source_group"])]
                f[index] = float(record["force_on_first_local_N"])
                fr[index] = float(record["force_rounding_radius_local_N"])
                observed_q = float(record["relative_displacement_mm"])
                observed_q_radius = float(record["relative_displacement_radius_mm"])
                require(record["rf_kdu_intervals_intersect"] is True,
                        f"bilateral_source_force_sign_audit_failed:{row['source_group']}")
            else:
                source_row_id = str(row["row_id"])
                owner = row["ownership"]
                owner_body = str(owner["first_body"])
                owner_body_index = body_index[owner_body]
                direction = np.asarray(owner["direction_global_xyz"], dtype=np.float64)
                body_translation = D[index, 6 * owner_body_index:6 * owner_body_index + 3]
                require(np.allclose(body_translation, direction, rtol=0.0, atol=2.0e-10),
                        f"floor_tangent_B_translation_sign_unexpected:{source_row_id}")
                active = floor_active.get(source_row_id)
                if active is not None:
                    physical_action = np.asarray(active["force_on_first_xyz_n"], dtype=np.float64)
                    action_radius = np.asarray(active["force_rounding_radius_xyz_n"], dtype=np.float64)
                    corrected = float(active["recovered_physical_tangent_reaction_N"])
                    corrected_from_rf = (float(active["raw_reference_rf_N"])
                                         - float(active["transferred_source_load_N"]))
                    require(abs(corrected - corrected_from_rf) <= 2.0e-12
                            and np.allclose(physical_action, corrected * direction,
                                            rtol=0.0, atol=2.0e-12),
                            f"floor_tangent_reference_Rf_correction_or_basis_changed:{source_row_id}")
                    # B's source coordinate increases along the owner basis;
                    # the physical support action is +basis*corrected, so the
                    # q-conjugate multiplier in D.T*f=W is its negative.
                    f[index] = -corrected
                    fr[index] = float(np.abs(direction) @ action_radius)
                    active_floor_max_abs_q = max(active_floor_max_abs_q, abs(float(q[index])))
                    active_floor_max_radius = max(active_floor_max_radius, float(qr[index]))
                    require(abs(float(q[index])) <= float(qr[index]) + 2.0e-12,
                            f"active_floor_stick_row_not_zero_with_DAT_interval:{source_row_id}")
                    floor_active_sign_checks += 1
                    active_floor_rows_seen += 1
                else:
                    released = floor_inactive.get(source_row_id)
                    require(released is not None
                            and released.get("native_reference_or_tangent_equation_present") is False
                            and released.get("native_tangent_spring_present") is False
                            and released.get("carryover_rf_interval_contains_zero") is True
                            and released.get("force_on_first_xyz_n") == [0.0, 0.0, 0.0],
                            f"released_floor_tangent_row_not_exactly_zero:{source_row_id}")
                    f[index] = 0.0
                    fr[index] = 0.0
                    inactive_floor_rows_seen += 1
                continue

            difference = abs(float(q[index]) - observed_q)
            bound = float(qr[index]) + observed_q_radius
            ratio = difference / max(bound, np.finfo(float).tiny)
            q_reference_max_difference = max(q_reference_max_difference, difference)
            q_reference_max_bound = max(q_reference_max_bound, bound)
            q_reference_max_ratio = max(q_reference_max_ratio, ratio)
            q_reference_checks += 1
            require(difference <= bound + 2.0e-12,
                    f"B_times_u_disagrees_with_native_source_q:{row['row_id']}")

        # The six source load columns are separate gravity/climber vectors.
        # The frozen deck has one proportional *CLOAD step, so each is scaled
        # by the exact recorded static time before composing e and W.
        gravity_col = selected_columns["gravity_nodal_map"]
        climber_col = selected_columns["climber_nodal_map"]
        e_total = load_factor * (e[:, gravity_col] + e[:, climber_col])
        W_total = load_factor * (W[:, gravity_col] + W[:, climber_col])

        a = np.zeros(300, dtype=np.float64)
        ar = np.zeros(300, dtype=np.float64)
        for body_no, body_name in enumerate(body_names):
            dofs = np.flatnonzero(owners == body_no)
            body_labels = [labels[int(index)] for index in dofs]
            _, R, _ = rigid.rigid_basis(body_labels, source["coordinates"], rotation_scale_mm=1000.0)
            # This is the same R-orthogonal gauge as the bordered KKT solve:
            # R.T*(u-R*a)=0, not Q.T*u used as a differently scaled coordinate.
            projector = np.linalg.solve(R.T @ R, R.T)
            a[6 * body_no:6 * body_no + 6] = projector @ u[dofs]
            ar[6 * body_no:6 * body_no + 6] = np.abs(projector) @ ur[dofs]

        predicted_q = D @ a + e_total - H @ f
        q_residual = q - predicted_q
        q_arithmetic_guard = 128.0 * np.finfo(float).eps * (
            np.abs(q) + np.abs(D) @ np.abs(a) + np.abs(e_total) + np.abs(H) @ np.abs(f) + 1.0
        )
        q_bound = qr + np.abs(D) @ ar + np.abs(H) @ fr + q_arithmetic_guard
        q_ratio = np.abs(q_residual) / np.maximum(q_bound, np.finfo(float).tiny)
        max_q_ratio = float(np.max(q_ratio))
        require(bool(np.all(np.abs(q_residual) <= q_bound)),
                f"q_equals_Da_plus_e_minus_Hf_interval_check_failed_at_time_{time}")

        wrench_residual = D.T @ f - W_total
        wrench_arithmetic_guard = 128.0 * np.finfo(float).eps * (
            np.abs(D.T) @ np.abs(f) + np.abs(W_total) + 1.0
        )
        wrench_bound = np.abs(D.T) @ fr + wrench_arithmetic_guard
        wrench_ratio = np.abs(wrench_residual) / np.maximum(wrench_bound, np.finfo(float).tiny)
        max_wrench_ratio = float(np.max(wrench_ratio))
        require(bool(np.all(np.abs(wrench_residual) <= wrench_bound)),
                f"D_transpose_f_equals_W_interval_check_failed_at_time_{time}")

        wrench_by_body = wrench_residual.reshape(50, 6)
        wrench_bound_by_body = wrench_bound.reshape(50, 6)
        per_increment.append({
            "time_and_load_factor": load_factor,
            "source_q_rows_compared_to_native_audit": 1640,
            "source_q_max_difference_mm": q_reference_max_difference,
            "source_q_max_combined_DAT_rounding_bound_mm": q_reference_max_bound,
            "source_q_max_difference_to_bound_ratio": q_reference_max_ratio,
            "active_floor_tangent_rows_with_zero_q_interval": floor_active_sign_checks,
            "active_floor_tangent_max_abs_q_mm": active_floor_max_abs_q,
            "active_floor_tangent_max_DAT_rounding_radius_mm": active_floor_max_radius,
            "released_floor_tangent_rows_with_exact_zero_action": 150,
            "q_minus_Da_minus_e_plus_Hf_max_abs_mm": max_abs(q_residual),
            "q_equation_DAT_only_uncertainty_bound_max_mm": float(np.max(q_bound)),
            "q_equation_max_abs_residual_to_bound_ratio": max_q_ratio,
            "D_transpose_f_minus_W_max_abs_force_N": max_abs(wrench_by_body[:, :3]),
            "D_transpose_f_minus_W_max_abs_moment_Nmm": 1000.0 * max_abs(wrench_by_body[:, 3:]),
            "D_transpose_f_minus_W_max_DAT_uncertainty_force_N": float(np.max(wrench_bound_by_body[:, :3])),
            "D_transpose_f_minus_W_max_DAT_uncertainty_moment_Nmm": 1000.0 * float(np.max(wrench_bound_by_body[:, 3:])),
            "wrench_equation_max_abs_residual_to_bound_ratio": max_wrench_ratio,
            "all_1840_rows_passed_both_reduced_equations": True,
        })
        global_max_q_reference_ratio = max(global_max_q_reference_ratio, q_reference_max_ratio)
        global_max_q_balance_ratio = max(global_max_q_balance_ratio, max_q_ratio)
        global_max_wrench_ratio = max(global_max_wrench_ratio, max_wrench_ratio)

    # Verify the recorded reduction's numerical solution diagnostics remain
    # visible. These are reported separately; they are not folded into DAT
    # token intervals or treated as a new acceptance tolerance.
    max_operator_kkt = max(float(body["max_kkt_relative_residual"]) for body in comp_record["bodies"])
    max_operator_original_residual_N = max(float(body["max_original_Ku_minus_projected_load_N"])
                                           for body in comp_record["bodies"])
    max_operator_body_force_N = max(float(body["max_original_residual_body_force_N"])
                                    for body in comp_record["bodies"])
    max_operator_body_moment_Nmm = max(float(body["max_original_residual_body_moment_N_mm"])
                                       for body in comp_record["bodies"])

    report = {
        "schema": OUTPUT_SCHEMA,
        "status": "PASS_A12_REAR_AUTHENTICATED_RESPONSE_REPLAY_AGAINST_FROZEN_REDUCTION",
        "response_case_id": "a12-rear",
        "response_sha256": PINNED["run/response.json"],
        "response_freeze_sha256": PINNED["run/freeze.json"],
        "response_execution_sha256": PINNED["run/execution.json"],
        "operator_compliance_assessment_sha256": PINNED["comp/assessment.json"],
        "operator_B_sha256": PINNED["comp/B.npz"],
        "operator_H_D_e_W_sha256": PINNED["comp/operators.npz"],
        "dimensions": {"physical_dofs": 37647, "source_rows": 1840, "rigid_coordinates": 300,
                       "rows_by_family": by_family, "separate_load_columns": 12},
        "source_force_mapping": {
            "SPRINGA": "native_endpoint_internal_force_N, signed in the existing source q coordinate; DAT RF half-last-place radii retained",
            "SPRING2": "force_on_first_local_N, checked against the native k*q interval; DAT RF half-last-place radii retained",
            "active_floor_tangent": "negative recovered_physical_tangent_reaction_N because B's q increases along the owner basis; recovered reaction is raw reference RF minus the recorded transferred source-load correction",
            "released_floor_tangent": "exact zero: no native tangent equation/spring, and the recorded carryover RF interval contains zero",
            "floor_tangent_sign_oracle": "For each T row, D's owner-body translation block equals the row owner tangent basis; source multiplier sign therefore opposes the physical support action in D.T*f=W.",
        },
        "load_composition": {
            "gravity_column": selected_columns["gravity_nodal_map"],
            "climber_column": selected_columns["climber_nodal_map"],
            "step_rule": "single proportional *CLOAD step: lambda*(gravity + climber), using the same columns in e and W",
            "max_abs_emitted_CLOAD_minus_source_sum_N": max_cload_difference,
            "max_omitted_source_CLOAD_magnitude_N": omitted_source_load_max,
        },
        "native_DAT_precision": {
            "parser": "Pinned CCX 2.23 E13.6 DAT parser; per-token half-last-place U/RF intervals propagated through B, R gauge, H, and D.T.",
            "DAT_sha256": PINNED["run/model.dat"],
            "q_reference_comparisons_across_increments": q_reference_checks,
            "active_floor_tangent_zero_q_checks": active_floor_rows_seen,
            "released_floor_tangent_zero_force_checks": inactive_floor_rows_seen,
            "printed_DAT_values_treated_as_full_precision": False,
        },
        "increment_checks": per_increment,
        "all_increments_passed": len(per_increment) == 7,
        "maximum_interval_ratios": {
            "B_u_vs_existing_native_source_q": global_max_q_reference_ratio,
            "q_equals_Da_plus_e_minus_Hf": global_max_q_balance_ratio,
            "D_transpose_f_equals_W": global_max_wrench_ratio,
        },
        "operator_numerical_diagnostics_separate_from_DAT_intervals": {
            "max_recorded_KKT_upper_force_residual_relative": max_operator_kkt,
            "max_recorded_original_Ku_minus_projected_load_N": max_operator_original_residual_N,
            "max_recorded_original_body_force_residual_N": max_operator_body_force_N,
            "max_recorded_original_body_moment_residual_Nmm": max_operator_body_moment_Nmm,
        },
        "scope_limits": [
            "This is one existing authenticated A12-rear response replay; it launched no native solve and performed no full-body factorization.",
            "The DAT interval checks use the frozen reduction values and propagate native U/RF print rounding; the elastic operator's separately recorded KKT diagnostics are not recast as physical uncertainty bounds.",
            "This validates reduced-operator applicability to this conditional response only. It does not select/qualify other floor states, prove uniqueness or recontact behavior, accept a full-frame state, qualify a joint, or authorize fabrication/climbing.",
        ],
        "native_solve_launched_by_replay": False,
        "mechanical_acceptance": False,
        "input_sha256": observed_hashes,
        "replay_script_sha256": sha(Path(__file__).resolve()),
    }
    ASSESSMENT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
                               encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "increments": len(per_increment),
                      "maximum_interval_ratios": report["maximum_interval_ratios"],
                      "native_solve_launched_by_replay": False,
                      "output": str(ASSESSMENT_PATH.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
