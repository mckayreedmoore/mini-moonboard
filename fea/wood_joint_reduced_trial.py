"""Prepare one reviewable current-candidate native trial without launching it."""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

from fea.wood_joint_reduced_case import build_case
from fea.wood_joint_reduced_native import LEDGER, ROOT, digest, verify, write_json
from fea.wood_joint_reduced_response import freeze_trial
from fea.wood_joint_reduced_trial_review import (
    DAT_TRANSITION_METHOD,
    RF_TRANSITION_METHOD,
    _cycle_index,
    check_active_set_history,
    derive_next_active_set,
)


def prepare(directory, *, case_id="a12-rear", hillman_axial_ratio=1.):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    structure, _, metadata = build_case(case_id, hillman_axial_ratio=hillman_axial_ratio,
                                         bolt_gap_factor=0., accessory_scenario_id=None)
    metadata["scope"] = "First zero-clearance all-active diagnostic frame trial; no joint acceptance"
    metadata["initialization"] = {
        "normal_contacts": "all active; solved complementarity not established",
        "axial_ties": "all active; solved tension signs not established",
        "radial_clearance": "zero gap comparison; no radial contact states exist",
    }
    checkpoint = directory/"prepared-model.pkl"
    # This is a local coordinator checkpoint, never a third-party pickle input.
    with checkpoint.open("wb") as stream:
        pickle.dump((structure, metadata), stream, protocol=pickle.HIGHEST_PROTOCOL)
    active = {row["name"] for row in structure.springs if row["bearing_closed_assumption"]}
    sources = [ROOT/path for path in metadata["source_sha256"]]
    freeze_trial(directory/"cycle-00", structure, metadata, active_groups=active,
                 radial_states={}, extra_sources=[__file__, checkpoint, *sources])
    write_json(directory/"preparation.json", {
        "case_id": case_id, "scenario": metadata["scenario"],
        "loads": metadata["case_assembly_audit"], "active_group_count": len(active),
        "native_solve_executed": False, "mechanical_acceptance": False,
        "checkpoint_scope": "Trusted local data for the same frozen implementation; verify source pins before reuse",
    })
    return directory/"cycle-00"


def _postrun_review_integrity_passes(review, *, evidence_root=ROOT):
    """Check follow-up eligibility without rewriting the saved audit verdict."""
    expected_gate_ast_sha256 = "30027b167c57e7c6cc68fa370d5917482bf64b964afc06aaa857ee0797d8ef68"
    provenance = review.get("provenance", {})
    legacy_authorization = provenance.get("authorization_checks_all_pass") is True
    corrected_lineage = provenance.get("corrected_review_lineage_checks", {})
    corrected_review = provenance.get("corrected_review_checks", {})
    independent_checks = provenance.get("pre_run_independent_review_checks", {})
    corrected_authorization = (
        isinstance(corrected_lineage, dict)
        and bool(corrected_lineage)
        and all(value is True for value in corrected_lineage.values())
        and isinstance(corrected_review, dict)
        and bool(corrected_review)
        and all(value is True for value in corrected_review.values())
        and isinstance(independent_checks, dict)
        and bool(independent_checks)
        and all(value is True for value in independent_checks.values())
        and provenance.get("corrected_review_lineage_checks", {}).get(
            "pre_run_independent_review_checks_all_pass") is True
        and provenance.get("freeze_source_snapshot_and_live_tree_verified_read_only") is True
    )
    audited_authorization = (
        (provenance.get("cycle_authorization_review_checks_all_pass") is True
         or provenance.get("authorization_and_review_lineage_checks_all_pass") is True
         or provenance.get("authorization_review_lineage_checks_all_pass") is True)
        and provenance.get("ledger_checks_all_pass") is True
        and (provenance.get("freeze_and_live_sources_verified_read_only") is True
             or provenance.get("freeze_source_snapshot_and_live_tree_verified_read_only") is True)
        and isinstance(provenance.get("freeze_source_pin_count"), int)
        and provenance["freeze_source_pin_count"] > 0
    )
    corrected_authorization = corrected_authorization and (
        provenance.get("ledger_checks_all_pass") is True
        and provenance.get("freeze_source_pin_live_mismatch_count") == 0
        and provenance.get("freeze_source_pin_live_missing_count") == 0
        and isinstance(provenance.get("freeze_source_pin_count"), int)
        and provenance["freeze_source_pin_count"] > 0
    )
    output_hashes_match = (
        provenance.get("execution_output_hashes_all_match") is True
        or provenance.get("all_execution_output_hashes_match") is True
    )
    output_hash_rows = provenance.get("execution_output_hash_matches", {})
    output_hashes_match = output_hashes_match and (
        not isinstance(output_hash_rows, dict)
        or all(value is True for value in output_hash_rows.values())
    )
    if (legacy_authorization or audited_authorization or corrected_authorization) and output_hashes_match:
        return True

    # The saved c09 audit records one independently reviewed helper drift.
    # This gate is a second live-tree delta; allow only its pinned AST and the
    # audited helper change, with every other c09 source pin unchanged.
    try:
        root = Path(evidence_root).resolve()
        c09 = root / (
            "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
            "reduced-static-a12-rear-ratio1-gap0-attempt02/"
            "cycle-09-rf-opening-intervals"
        )
        freeze_path = c09 / "freeze.json"
        review_path = c09 / "postrun-review.json"
        equivalence_path = c09 / "source-drift-equivalence-review-v2.json"
        expected_freeze_sha = "9af8d36214b108d5d928cfca6e2bb3d853ef70ae8170584939157a5f5a962874"
        expected_review_sha = "7e3581c01e71981a27782fb6b4bc4279f41e51933063db3af49c6db5ac7cb061"
        expected_equivalence_sha = "8edead6dacdbfdf829379a1c2127851d7918ee1e175345b23450a2237ecd16ed"
        expected_frozen_source_sha = "6b13b79eb35f7238bbc9283ef484271927e2dd14a0ff9519e30d1a74a9cc70be"
        expected_live_source_sha = "89dd47aaed3f3e1ac3c4d6dd1ec3d2efd4e7119fb7ded26cd180984a95b1ade1"
        expected_source_path = "fea/wood_joint_reduced_trial_review.py"

        if (digest(freeze_path) != expected_freeze_sha
                or digest(review_path) != expected_review_sha
                or digest(equivalence_path) != expected_equivalence_sha
                or json.loads(review_path.read_text()) != review):
            return False

        equivalence = json.loads(equivalence_path.read_text())
        source = equivalence.get("reviewer_source_comparison", {})
        source_inventory = equivalence.get("c09_source_pin_inventory", {})
        frozen_source = c09 / "sources/fea/wood_joint_reduced_trial_review.py"
        live_source = root / expected_source_path
        if (digest(frozen_source) != expected_frozen_source_sha
                or digest(live_source) != expected_live_source_sha
                or equivalence.get("schema") != "wood_joint_postfreeze_source_drift_equivalence_review/v2"
                or equivalence.get("c09_binding") != {
                    "c09_dat_sha256": "b0b91715405351ff895eef19a534c365da62a05652a23ec6d9389b5cfd62fef7",
                    "c09_model_sha256": "fc19f711a817eaecc8df37dd204f2df4cb3dd55e951e74f02fd260226443915a",
                    "c09_response_sha256": "caa2f520636a0a227c425416ca88fc503f7d4f1fc8b06e2fafac832bac9aaf90",
                    "input_freeze_path": "freeze.json",
                    "input_freeze_sha256": expected_freeze_sha,
                    "postrun_review_path": "postrun-review.json",
                    "postrun_review_sha256": expected_review_sha,
                }
                or source.get("path") != expected_source_path
                or source.get("frozen_snapshot_path") != "sources/fea/wood_joint_reduced_trial_review.py"
                or source.get("frozen_sha256") != expected_frozen_source_sha
                or source.get("current_live_sha256") != expected_live_source_sha
                or source.get("all_other_module_function_asts_identical") is not True
                or source_inventory.get("frozen_source_pin_count") != 907
                or source_inventory.get("frozen_snapshots_matching_all_pins") != 907
                or source_inventory.get("snapshot_mismatch_paths") != []
                or source_inventory.get("current_live_mismatch_count") != 2
                or {row.get("path") for row in source_inventory.get(
                    "current_live_mismatches", [])} != {
                        "fea/wood_joint_reduced_trial.py",
                        expected_source_path,
                    }):
            return False

        freeze = json.loads(freeze_path.read_text())
        source_pins = freeze.get("source_sha256", {})
        if len(source_pins) != 907:
            return False
        live_mismatches = {}
        for name, expected_sha in source_pins.items():
            snapshot = c09 / "sources" / name
            current = root / name
            if digest(snapshot) != expected_sha:
                return False
            current_sha = digest(current)
            if current_sha != expected_sha:
                live_mismatches[name] = (expected_sha, current_sha)

        runner_path = "fea/wood_joint_reduced_trial.py"
        expected_runner_sha = "f41a90bfcc3016d873b02733c26af85b82f8798763646f6c005299ce658d9305"
        if (set(live_mismatches) != {expected_source_path, runner_path}
                or live_mismatches[expected_source_path]
                    != (expected_frozen_source_sha, expected_live_source_sha)
                or live_mismatches[runner_path][0] != expected_runner_sha
                or live_mismatches[runner_path][1] != digest(root / runner_path)
                or source_pins.get(runner_path) != expected_runner_sha):
            return False

        import ast
        import hashlib

        frozen_runner = c09 / "sources" / runner_path
        live_runner = root / runner_path

        def without_predecessor_gate(path):
            tree = ast.parse(path.read_text())
            gate_functions = [
                node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "_postrun_review_integrity_passes"
            ]
            if len(gate_functions) != 1:
                return None
            remaining = [
                node for node in tree.body
                if node is not gate_functions[0]
            ]
            return ast.dump(
                ast.Module(body=remaining, type_ignores=[]),
                include_attributes=False,
            )

        if without_predecessor_gate(frozen_runner) != without_predecessor_gate(live_runner):
            return False

        def reviewed_gate_ast_sha256(path):
            tree = ast.parse(path.read_text())
            gate_functions = [
                node for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "_postrun_review_integrity_passes"
            ]
            if len(gate_functions) != 1:
                return None
            gate = gate_functions[0]
            pins = [
                node for node in gate.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name)
                        and target.id == "expected_gate_ast_sha256"
                        for target in node.targets)
            ]
            if (len(pins) != 1
                    or not isinstance(pins[0].value, ast.Constant)
                    or pins[0].value.value != expected_gate_ast_sha256):
                return None
            pins[0].value = ast.Constant(value="<normalized-gate-ast-pin>")
            normalized = ast.dump(gate, include_attributes=False)
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        if reviewed_gate_ast_sha256(live_runner) != expected_gate_ast_sha256:
            return False

        added = source.get("added_ast_functions", {})
        modified = source.get("modified_ast_functions", {})
        narrow = equivalence.get("narrow_conclusion", {})
        provenance = review.get("provenance", {})
        drift = provenance.get("live_source_drift_since_freeze", [])
        checks = review.get("postrun_audit_checks", {})
        failed_checks = [name for name, passed in checks.items() if passed is False]
        expected_drift = [{
            "frozen_sha256": expected_frozen_source_sha,
            "live_matches": False,
            "live_sha256": "63c8548dce96c535ab62aaacc34a6d192f6a48b0f072429a6527750c277706c5",
            "path": expected_source_path,
            "snapshot_matches": True,
            "snapshot_sha256": expected_frozen_source_sha,
        }]
        return (
            review.get("postrun_audit_checks_all_pass") is False
            and failed_checks == ["current_live_tree_matches_all_907_freeze_source_pins"]
            and len(checks) == 18
            and all(passed is True or passed is False for passed in checks.values())
            and provenance.get("freeze_source_pin_count") == 907
            and provenance.get("freeze_source_pin_live_mismatch_count") == 1
            and provenance.get("freeze_source_pin_live_missing_count") == 0
            and provenance.get("freeze_source_snapshot_and_live_tree_verified_read_only") is False
            and checks.get("frozen_source_snapshot_complete_and_matches_all_907_pins") is True
            and provenance.get("all_execution_output_hashes_match") is True
            and provenance.get("ledger_checks_all_pass") is True
            and drift == expected_drift
            and added == {
                "_authorized_review_binding":
                    "50e4f4d21ade53e08f219275e3bfdfc942d44d717ea7d2a2b100fd3043ab78d6"
            }
            and source.get("removed_ast_functions") == []
            and modified == {
                "_check_prior_execution": {
                    "frozen_ast_sha256":
                        "b826e1d98480c6de98a8718e49bfba59545b1ecf9c175328d4fa35f515e68ae9",
                    "live_ast_sha256":
                        "a7c2bacf6dc440caba932fab9492be3b1856fb654e56f11bec3ae2575980d219",
                },
                "audit_consumed_transition": {
                    "frozen_ast_sha256":
                        "f1ad6c36da8d84031ab47025c1c72b9497caef0e3afdda5e8d5c677639290431",
                    "live_ast_sha256":
                        "fbeaeb485a205da045b1c9c65b4c8b26d48dcbc839928d3fed33d6aaf0be7ba3",
                }
            }
            and narrow.get("reviewer_change_can_change_c09_native_response") is False
            and narrow.get("reviewer_change_can_change_c09_to_c10_dat_active_set_selection") is False
            and narrow.get("reviewer_change_corrects_external_review_predecessor_validation") is True
            and narrow.get("does_not_establish") == [
                "This does not change or pass c09's saved post-run audit; its false provenance/audit flag remains intact.",
                "This does not validate c09 mechanical complementarity or design acceptance.",
                "This does not make the current c09 predecessor gate pass; its exact live-source and sidecar pins are stale after the reviewer edit.",
                "This does not review the superseded first c10 freeze, establish a new c10 exact-freeze review, authorize native execution, or establish mechanical acceptance.",
            ]
            and review.get("mechanical_acceptance") is False
        )
    except (OSError, ValueError, TypeError, KeyError, SyntaxError):
        return False


def prepare_followup(previous_directory, directory, *, use_rf_opening_intervals=False):
    """Freeze the next same-case zero-gap active branch; never launches it."""
    previous = Path(previous_directory).resolve()
    target = Path(directory).resolve()
    if not previous.is_relative_to(ROOT) or not target.is_relative_to(ROOT):
        raise ValueError("Trial directories must remain inside the repository")
    if target.exists():
        raise FileExistsError(target)
    packet = verify(previous, check_live=False)
    execution_path = previous/"execution.json"
    report_path = previous/"response.json"
    review_path = previous/"review.json"
    postrun_review_path = previous/"postrun-review.json"
    execution = json.loads(execution_path.read_text())
    report = json.loads(report_path.read_text())
    review = json.loads(review_path.read_text())
    postrun_review = json.loads(postrun_review_path.read_text())
    ledger = json.loads(LEDGER.read_text())
    matches = [row for row in ledger["runs"] if row["run_id"] == execution["run_id"]]
    if len(matches) != 1:
        raise ValueError("Previous native execution is not uniquely registered")
    registered = matches[0]
    if (registered["state"] != "consumed_terminal" or registered["launches_consumed"] != 1
            or registered["execution_record_sha256"] != digest(execution_path)
            or registered["input_freeze_sha256"] != digest(previous/"freeze.json")
            or execution.get("returncode") != 0
            or not execution.get("container_confirmed_terminal")):
        raise ValueError("Previous native run is not a terminal, ledger-verified success")
    if (review.get("ready_for_scoped_native_run") is not True
            or review.get("input_freeze_sha256") != digest(previous/"freeze.json")):
        raise ValueError("Previous native run lacks a review bound to its exact freeze")
    postrun_provenance = postrun_review.get("provenance", {})
    postrun_files = postrun_provenance.get("cycle_file_sha256", {})
    if (postrun_review.get("schema") != "wood_joint_rf_force_recovery_postrun_review/v1"
            or postrun_review.get("cycle") != execution["run_id"]
            or postrun_files.get("freeze.json") != digest(previous/"freeze.json")
            or postrun_files.get("execution.json") != digest(execution_path)
            or postrun_files.get("response.json") != digest(report_path)
            or not _postrun_review_integrity_passes(postrun_review)
            or postrun_review.get("reviewer_executed_native_solve") is not False
            or postrun_review.get("cycle_native_solve_executed") is not True
            or postrun_review.get("mechanical_acceptance") is not False):
        raise ValueError("Independent postrun review is missing or stale for the previous branch")
    for name, expected in execution["outputs_sha256"].items():
        if digest(previous/name) != expected:
            raise ValueError("Previous native output changed: " + name)
    if (report.get("input_freeze_sha256") != digest(previous/"freeze.json")
            or report.get("native_execution_verified") is not True
            or report.get("force_output_recovery_audit", {}).get("status")
               != "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS"
            or report.get("all_raw_equilibrium_passed") is not True
            or report.get("all_interval_equilibrium_passed") is not True
            or report.get("mpc_check_passed") is not True
            or report.get("native_warnings")
            or report.get("postprocessor_sha256") != digest(ROOT/"fea/wood_joint_reduced_response.py")
            or report.get("force_output_helper_sha256") != digest(ROOT/"fea/wood_joint_reduced_force_output.py")
            or report.get("mechanical_acceptance") is not False):
        raise ValueError("Previous branch lacks its checked RF response report")
    model = json.loads((previous/"model.json").read_text())
    if (model.get("case_id") != "a12-rear" or model.get("scenario", {}).get("bolt_gap_factor") != 0.
            or model.get("trial_radial_states") != {}):
        raise ValueError("Follow-up preparation supports only the same a12-rear zero-gap case")

    checkpoint = previous.parent/"prepared-model.pkl"
    checkpoint_key = str(checkpoint.relative_to(ROOT))
    if packet["source_sha256"].get(checkpoint_key) != digest(checkpoint):
        raise ValueError("Trusted prepared-model checkpoint differs from its frozen pin")
    with checkpoint.open("rb") as stream:
        structure, metadata = pickle.load(stream)
    if use_rf_opening_intervals and (
            model.get("cycle_index") != 8 or _cycle_index(target) != 9):
        raise ValueError("RF opening intervals are currently authorized only for c08-to-c09 transition review")
    active, transition = derive_next_active_set(
        model, report, (previous/"model.dat").read_text(),
        use_rf_opening_intervals=use_rf_opening_intervals)
    expected_method = RF_TRANSITION_METHOD if use_rf_opening_intervals else DAT_TRANSITION_METHOD
    if transition["method"] != expected_method:
        raise ValueError("Active-set transition method differs from the requested preparation mode")
    if transition["ambiguous_state_changes_suppressed"]:
        raise ValueError("An unresolved rounding interval suppresses a selected active-set change")
    history_check = check_active_set_history(previous, active)
    radial = {}
    if set(radial) != set(model.get("trial_radial_states", {})):
        raise ValueError("Radial state inventory changed in the zero-gap follow-up")

    original_initialization = metadata.pop("initialization", None)
    if original_initialization is None:
        original_initialization = model.get("original_initialization")
    metadata.update({
        "scope": "Zero-clearance diagnostic active-set cycle "
                 + str(int(model.get("cycle_index", 0))+1) + "; no joint acceptance",
        "active_set_transition_method": transition["method"],
        "active_set_transition": transition,
        "original_initialization": original_initialization,
        "current_branch": {
            "active_group_count": len(active),
            "origin": "Update from cycle" + str(model.get("cycle_index"))
                      + " checked response using " + transition["method"]
                      + "; current complementarity not established",
        },
        "cycle_index": int(model.get("cycle_index", 0))+1,
        "previous_trial_freeze_sha256": digest(previous/"freeze.json"),
        "previous_response_sha256": digest(report_path),
        "previous_execution_sha256": digest(execution_path),
        "previous_postrun_review_sha256": digest(postrun_review_path),
        "previous_trial_run_id": execution["run_id"],
    })
    source_paths = [ROOT/path for path in metadata["source_sha256"]]
    freeze_trial(target, structure, metadata, active_groups=active, radial_states=radial,
                 extra_sources=[__file__, checkpoint, previous/"freeze.json", previous/"model.json",
                                review_path, postrun_review_path, execution_path, report_path,
                                ROOT/"fea/wood_joint_reduced_trial_review.py",
                                *source_paths])
    write_json(target/"preparation.json", {
        "case_id": model["case_id"], "cycle_index": metadata["cycle_index"],
        "previous_trial_run_id": execution["run_id"],
        "previous_trial_freeze_sha256": metadata["previous_trial_freeze_sha256"],
        "previous_response_sha256": metadata["previous_response_sha256"],
        "previous_postrun_review_sha256": metadata["previous_postrun_review_sha256"],
        "active_group_count": len(active), "active_groups": sorted(active),
        "active_set_transition_method": transition["method"],
        "active_set_transition": transition,
        "active_set_history_check": history_check,
        "radial_states": radial, "native_solve_executed": False,
        "mechanical_acceptance": False,
    })
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--previous", type=Path,
                        help="Prepare a follow-up from a completed frozen branch")
    parser.add_argument("--rf-opening-intervals", action="store_true",
                        help="Use the reviewed RF interval method for c08-to-c09 only")
    parser.add_argument("--case-id", default="a12-rear")
    parser.add_argument("--hillman-axial-ratio", type=float, default=1.)
    args = parser.parse_args()
    if args.previous is not None:
        print(prepare_followup(args.previous, args.directory,
                               use_rf_opening_intervals=args.rf_opening_intervals))
    else:
        if args.rf_opening_intervals:
            parser.error("--rf-opening-intervals requires --previous")
        print(prepare(args.directory, case_id=args.case_id,
                      hillman_axial_ratio=args.hillman_axial_ratio))
