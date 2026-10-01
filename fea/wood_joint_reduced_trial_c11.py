"""Parent-side exact preparation for the single bounded c11 diagnostic."""
from __future__ import annotations

import json
import pickle
from pathlib import Path

from fea.wood_joint_reduced_native import LEDGER, ROOT, digest, verify, write_json
from fea.wood_joint_reduced_response import freeze_trial
from fea.wood_joint_reduced_trial_review import (
    DAT_TRANSITION_METHOD,
    check_active_set_history,
    derive_next_active_set,
    review_transition,
)

ATTEMPT = ROOT / (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "reduced-static-a12-rear-ratio1-gap0-attempt02"
)
C10 = ATTEMPT / "cycle-10-sign-closure-r2"
C10_AUDIT = ATTEMPT / (
    "cycle-10-sign-closure-r2-postrun-review/independent-postrun-review.json"
)
C11 = ATTEMPT / "cycle-11-sign-closure-r1"
C10_AUDIT_SHA256 = "ee520a5eafc737a54530e13c1348fd2abacadb9a724e91ff7e4b92094ea69566"
C10_FREEZE_SHA256 = "bbaa8929b5c28c853a35e65ce12a91c82faaf1ad2129c9424c9ff385633ab226"
C10_RUN_ID = "reduced-a12-ratio1-gap0-attempt02-cycle10-sign-closure-r2"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_c10_postrun_audit(*, evidence_root: Path = ROOT) -> dict:
    """Verify the exact peer audit and every live artifact it binds."""
    root = Path(evidence_root).resolve()
    audit_path = root / C10_AUDIT.relative_to(ROOT)
    _require(digest(audit_path) == C10_AUDIT_SHA256,
             "The c10 independent post-run audit hash changed")
    audit = json.loads(audit_path.read_text())
    scope = audit.get("scope", {})
    _require(audit.get("schema") == "wood_joint_c10_independent_postrun_review/v1"
             and audit.get("audit_outcome") == "PASS"
             and scope.get("cycle") == "c10"
             and scope.get("packet_path") == str(C10.relative_to(ROOT))
             and scope.get("run_id") == C10_RUN_ID
             and scope.get("freeze_sha256") == C10_FREEZE_SHA256
             and scope.get("native_solver_invoked_by_reviewer") is False
             and scope.get("c10_inputs_or_parent_review_audit_modified") is False,
             "The c10 independent audit scope or verdict changed")
    _require(audit.get("check_counts") == {"failed": 0, "passed": 18, "total": 18}
             and len(audit.get("checks", [])) == 18
             and all(row.get("passed") is True for row in audit["checks"]),
             "The c10 independent audit no longer passes all 18 checks")
    response = audit.get("response_recalculation", {})
    _require(response.get("exact_field_matches") == 21
             and response.get("mismatched_fields") == []
             and response.get("mechanical_acceptance") is False
             and response.get("numerical_checks_passed") is False,
             "The independently reproduced c10 response changed")
    mechanics = audit.get("mechanics", {})
    _require(mechanics.get("all_raw_equilibrium_passed") is True
             and mechanics.get("all_interval_equilibrium_passed") is True
             and mechanics.get("mpc", {}).get("passed") is True
             and mechanics.get("axial_ties", {}).get("passed") is True
             and mechanics.get("force_recovery", {}).get("status")
                 == "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS"
             and mechanics.get("contact_complementarity", {}).get("exception_count") == 3
             and mechanics.get("all_complementarity_passed") is False
             and mechanics.get("numerical_checks_passed") is False
             and mechanics.get("mechanical_acceptance") is False,
             "The c10 mechanical findings changed or were promoted")
    transition = audit.get("transition_recheck", {})
    _require(transition.get("applicable_check_count") == 9
             and transition.get("applicable_checks_passed") == 9
             and transition.get("ready_for_scoped_native_run") is True,
             "The c09-to-c10 predecessor transition audit is no longer valid")

    bindings = audit.get("bindings", {})
    for binding in bindings.values():
        if isinstance(binding, dict) and binding.get("path") and binding.get("sha256"):
            _require(digest(root / binding["path"]) == binding["sha256"],
                     "A c10 post-run audit binding changed: " + binding["path"])
    ledger_binding = bindings.get("ledger", {})
    ledger = json.loads((root / ledger_binding["path"]).read_text())
    ledger_rows = [row for row in ledger.get("runs", [])
                   if row.get("run_id") == C10_RUN_ID]
    _require(len(ledger_rows) == 1
             and ledger_rows[0] == ledger_binding.get("record")
             and ledger_rows[0].get("state") == "consumed_terminal"
             and ledger_rows[0].get("launches_consumed") == 1,
             "The c10 ledger row is no longer uniquely terminal")
    return audit


def prepare_c11(directory: Path = C11) -> Path:
    """Freeze and internally review one fresh c10-derived active-set branch."""
    target = Path(directory).resolve()
    _require(target.is_relative_to(ROOT) and target.parent == C10.parent,
             "c11 must remain beside its c00-c10 history inside the repository")
    _require(target.name == "cycle-11-sign-closure-r1" and not target.exists(),
             "Refusing to overwrite or rename the single c11 diagnostic packet")

    packet = verify(C10, check_live=False)
    audit = verify_c10_postrun_audit()
    _require(digest(C10 / "freeze.json") == C10_FREEZE_SHA256,
             "The c10 input freeze changed")
    model = json.loads((C10 / "model.json").read_text())
    response = json.loads((C10 / "response.json").read_text())
    execution_path = C10 / "execution.json"
    execution = json.loads(execution_path.read_text())
    review_path = C10 / "review.json"
    review = json.loads(review_path.read_text())
    authorization_path = C10 / "authorization.json"
    authorization = json.loads(authorization_path.read_text())
    ledger = json.loads(LEDGER.read_text())
    ledger_matches = [row for row in ledger["runs"] if row.get("run_id") == C10_RUN_ID]
    _require(execution.get("run_id") == C10_RUN_ID
             and execution.get("returncode") == 0
             and execution.get("container_confirmed_terminal") is True
             and execution.get("native_solve_executed") is True
             and review.get("input_freeze_sha256") == C10_FREEZE_SHA256
             and review.get("ready_for_scoped_native_run") is True
             and authorization.get("input_freeze_sha256") == C10_FREEZE_SHA256
             and authorization.get("native_execution_authorized") is True
             and len(ledger_matches) == 1
             and ledger_matches[0].get("state") == "consumed_terminal"
             and ledger_matches[0].get("execution_record_sha256") == digest(execution_path),
             "The c10 execution chain is not eligible as a transition predecessor")
    _require(response.get("input_freeze_sha256") == C10_FREEZE_SHA256
             and response.get("native_execution_verified") is True
             and response.get("all_raw_equilibrium_passed") is True
             and response.get("all_interval_equilibrium_passed") is True
             and response.get("mpc_check_passed") is True
             and response.get("native_warnings") == []
             and response.get("force_output_recovery_audit", {}).get("status")
                 == "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS"
             and response.get("mechanical_acceptance") is False,
             "The c10 response no longer meets predecessor force/equilibrium screens")
    for name, expected in execution.get("outputs_sha256", {}).items():
        _require(digest(C10 / name) == expected, "A c10 native output changed: " + name)

    checkpoint = C10.parent / "prepared-model.pkl"
    checkpoint_key = str(checkpoint.relative_to(ROOT))
    _require(packet.get("source_sha256", {}).get(checkpoint_key) == digest(checkpoint),
             "The trusted prepared-model checkpoint changed since c10 was frozen")
    with checkpoint.open("rb") as stream:
        structure, metadata = pickle.load(stream)
    active, transition = derive_next_active_set(model, response, (C10 / "model.dat").read_text())
    old_active = set(model["trial_active_groups"])
    added = active - old_active
    removed = old_active - active
    expected_added = {"contact_85_2"}
    expected_removed = {
        "floor_base_floor_left_7", "floor_base_floor_left_7_friction",
        "floor_base_floor_left_9", "floor_base_floor_left_9_friction",
    }
    _require(added == expected_added and removed == expected_removed
             and len(active) == 511
             and transition.get("normal_active_next") == 317
             and transition.get("tension_active_next") == 166
             and transition.get("paired_floor_tangent_groups_next") == 28
             and transition.get("ambiguous_state_changes_suppressed") == 0
             and transition.get("threshold_rounding_ambiguous_normal_count") == 0
             and transition.get("threshold_rounding_ambiguous_tension_count") == 0,
             "The frozen c10 response no longer yields the reviewed c11 branch")
    history = check_active_set_history(C10, active)
    _require(history.get("status") == "PASS_NO_REPEATED_ACTIVE_SET"
             and history.get("prior_consumed_branch_count") == 11,
             "The proposed c11 branch repeats or differs from the reviewed history")

    initialization = metadata.pop("initialization", None)
    if initialization is None:
        initialization = model.get("original_initialization")
    metadata.update({
        "scope": "Zero-clearance diagnostic active-set cycle 11; no joint acceptance",
        "active_set_transition_method": DAT_TRANSITION_METHOD,
        "active_set_transition": transition,
        "original_initialization": initialization,
        "current_branch": {
            "active_group_count": len(active),
            "origin": "Single bounded update from cycle10 checked response; no c12 retry budget",
        },
        "cycle_index": 11,
        "previous_trial_freeze_sha256": digest(C10 / "freeze.json"),
        "previous_response_sha256": digest(C10 / "response.json"),
        "previous_execution_sha256": digest(execution_path),
        "previous_postrun_review_sha256": digest(C10_AUDIT),
        "previous_trial_run_id": C10_RUN_ID,
    })
    source_paths = [ROOT / path for path in metadata["source_sha256"]]
    freeze_trial(
        target, structure, metadata, active_groups=active, radial_states={},
        extra_sources=[
            __file__, checkpoint, C10 / "freeze.json", C10 / "model.json",
            review_path, authorization_path, execution_path, C10 / "response.json",
            C10 / "review-audit.json", C10_AUDIT,
            ROOT / authorization["independent_review"],
            ROOT / "fea/wood_joint_reduced_trial.py",
            ROOT / "fea/wood_joint_reduced_trial_review.py",
            *source_paths,
        ],
    )
    write_json(target / "preparation.json", {
        "case_id": model["case_id"], "cycle_index": 11,
        "previous_trial_run_id": C10_RUN_ID,
        "previous_trial_freeze_sha256": C10_FREEZE_SHA256,
        "previous_response_sha256": digest(C10 / "response.json"),
        "previous_postrun_review_path": str(C10_AUDIT.relative_to(ROOT)),
        "previous_postrun_review_sha256": C10_AUDIT_SHA256,
        "active_group_count": len(active), "active_groups": sorted(active),
        "active_set_transition_method": DAT_TRANSITION_METHOD,
        "active_set_transition": transition,
        "active_set_history_check": history,
        "changed_groups": {"added": sorted(added), "removed": sorted(removed)},
        "native_solve_executed": False, "mechanical_acceptance": False,
        "stage_budget": "One c11 diagnostic maximum; stop on any failed gate; no automatic c12",
        "c10_audit_outcome": audit["audit_outcome"],
    })
    review_transition(C10, target, write=True)
    verify(target, check_live=True)
    return target


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=C11)
    args = parser.parse_args()
    print(prepare_c11(args.directory))
