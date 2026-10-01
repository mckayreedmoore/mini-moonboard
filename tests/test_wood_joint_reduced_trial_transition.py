import json
import shutil
from pathlib import Path

import pytest

from fea.wood_joint_reduced_trial import _postrun_review_integrity_passes
from fea.wood_joint_reduced_trial_review import (
    TOLERANCE_MM,
    _check_prior_execution,
    _authorized_review_binding,
    _rf_active_normal_opening_interval,
    check_active_set_history,
    derive_next_active_set,
)
from fea.wood_joint_reduced_native import digest
from fea.wood_joint_reduced_trial_c11 import verify_c10_postrun_audit

ROOT = Path(__file__).resolve().parents[1]
C08 = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-08-rounding-aware"
)
RF_FIXTURE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    / "rf-opening-known-answer-attempt02"
)
C09 = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    / "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-09-rf-opening-intervals"
)
def _cycle08_inputs():
    model = json.loads((C08 / "model.json").read_text())
    response = json.loads((C08 / "response.json").read_text())
    dat_text = (C08 / "model.dat").read_text()
    return model, response, dat_text


def test_cycle08_corrected_lineage_audit_passes_followup_integrity_gate():
    audit = json.loads((C08 / "postrun-review.json").read_text())

    assert _postrun_review_integrity_passes(audit) is True


def test_cycle09_exact_review_helper_drift_is_eligible_without_rewriting_failed_audit():
    audit = json.loads((C09 / "postrun-review.json").read_text())

    assert audit["postrun_audit_checks_all_pass"] is False
    failed = [
        name for name, passed in audit["postrun_audit_checks"].items()
        if passed is False
    ]
    assert failed == ["current_live_tree_matches_all_907_freeze_source_pins"]
    assert _postrun_review_integrity_passes(audit) is True
    assert audit["postrun_audit_checks_all_pass"] is False


def test_c10_independent_postrun_audit_binds_terminal_outputs_and_failed_mechanics():
    audit = verify_c10_postrun_audit()

    assert audit["audit_outcome"] == "PASS"
    assert audit["check_counts"] == {"failed": 0, "passed": 18, "total": 18}
    assert audit["mechanics"]["contact_complementarity"]["exception_count"] == 3
    assert audit["mechanics"]["mechanical_acceptance"] is False


def _copy_cycle09_integrity_evidence(root):
    freeze = json.loads((C09 / "freeze.json").read_text())
    for relative in freeze["source_sha256"]:
        relative = Path(relative)
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source.resolve())
        snapshot = C09 / "sources" / relative
        snapshot_target = root / C09.relative_to(ROOT) / "sources" / relative
        snapshot_target.parent.mkdir(parents=True, exist_ok=True)
        snapshot_target.symlink_to(snapshot.resolve())

    copies = (
        C09.relative_to(ROOT) / "freeze.json",
        C09.relative_to(ROOT) / "postrun-review.json",
        C09.relative_to(ROOT) / "source-drift-equivalence-review-v2.json",
        Path("fea/wood_joint_reduced_trial.py"),
        Path("fea/wood_joint_reduced_trial_review.py"),
    )
    for relative in copies:
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        shutil.copyfile(source, target)


@pytest.mark.parametrize(
    "tamper",
    [
        "equivalence_sidecar",
        "live_review_source",
        "other_live_source",
        "predecessor_runner_outside_gate",
        "predecessor_gate_body",
    ],
)
def test_cycle09_drift_exception_rejects_changed_evidence(tmp_path, tamper):
    audit = json.loads((C09 / "postrun-review.json").read_text())
    evidence_root = tmp_path / "evidence"
    _copy_cycle09_integrity_evidence(evidence_root)
    assert _postrun_review_integrity_passes(audit, evidence_root=evidence_root) is True

    if tamper == "equivalence_sidecar":
        sidecar = evidence_root / (
            C09.relative_to(ROOT) / "source-drift-equivalence-review-v2.json"
        )
        data = json.loads(sidecar.read_text())
        data["narrow_conclusion"]["source_delta_can_change_c09_native_response"] = True
        sidecar.write_text(json.dumps(data))
    elif tamper == "live_review_source":
        source = evidence_root / "fea/wood_joint_reduced_trial_review.py"
        source.write_text(source.read_text() + "\n")
    elif tamper == "other_live_source":
        source = evidence_root / "fea/wood_joint_reduced_connections.py"
        source.unlink()
        source.write_text((ROOT / "fea/wood_joint_reduced_connections.py").read_text() + "\n")
    elif tamper == "predecessor_runner_outside_gate":
        source = evidence_root / "fea/wood_joint_reduced_trial.py"
        source.write_text(source.read_text().replace('return directory/"cycle-00"',
                                                      'return directory/"changed"'))
    else:
        source = evidence_root / "fea/wood_joint_reduced_trial.py"
        source.write_text(source.read_text().replace(
            "    # The saved c09 audit records one independently reviewed helper drift.",
            "    return True\n\n"
            "    # The saved c09 audit records one independently reviewed helper drift.",
        ))

    assert _postrun_review_integrity_passes(audit, evidence_root=evidence_root) is False
    assert _postrun_review_integrity_passes(
        {**audit, "postrun_audit_checks_all_pass": True}
    ) is False


def test_authorized_review_binding_accepts_and_hash_checks_external_freeze_audit():
    authorization = json.loads((C09 / "authorization.json").read_text())
    freeze_sha = __import__("fea.wood_joint_reduced_native", fromlist=["digest"]).digest(
        C09 / "freeze.json"
    )

    review_path, review_sha = _authorized_review_binding(C09, authorization, freeze_sha)

    assert review_path == C09 / "independent-review.json"
    assert review_sha == authorization["independent_review_sha256"]
    with pytest.raises(ValueError, match="review artifact hash differs"):
        _authorized_review_binding(
            C09,
            {**authorization, "independent_review_sha256": "0" * 64},
            freeze_sha,
        )


def test_prior_execution_accepts_parent_authorized_external_pre_run_review():
    previous_packet = json.loads((C09 / "freeze.json").read_text())
    previous_model = json.loads((C09 / "model.json").read_text())
    paths = (
        C09 / "freeze.json",
        C09 / "model.json",
        C09 / "review.json",
        C09 / "execution.json",
        C09 / "response.json",
        C09.parent / "prepared-model.pkl",
        ROOT / "fea/wood_joint_reduced_response.py",
        ROOT / "fea/wood_joint_reduced_force_output.py",
    )
    current_packet = {
        "source_sha256": {
            str(path.resolve().relative_to(ROOT)): digest(path)
            for path in paths
        }
    }

    lineage = _check_prior_execution(
        C09, previous_packet, previous_model, current_packet
    )

    assert lineage["previous_run_id"] == (
        "reduced-a12-ratio1-gap0-attempt02-cycle09-rf-opening-intervals"
    )
    assert lineage["launch_bound_review_path"] == str(
        (C09 / "independent-review.json").relative_to(ROOT)
    )
    assert lineage["launch_bound_review_sha256"] == digest(
        C09 / "independent-review.json"
    )


def test_rf_opening_inversion_reproduces_both_independent_fixture_answers():
    fixture_model = json.loads((RF_FIXTURE / "native/model.json").read_text())
    fixture_check = json.loads((RF_FIXTURE / "postrun-check.json").read_text())
    fixture_model["scenario"] = {"bolt_gap_factor": 0.0}
    fixture_model["trial_radial_states"] = {}

    assert fixture_check["status"] == "PASS_RF_OPENING_INTERVALS_CLASSIFY_BOTH_THRESHOLD_SIDES"
    for branch in fixture_check["branches"]:
        name = "contact_" + branch["branch"]
        spring = next(row for row in fixture_model["springs"] if row["name"] == name)
        owner = fixture_model["connection_ownership"][name]
        scalar_force = branch["rf_contact_force_on_first_n"]
        scalar_radius = branch["rf_contact_force_rounding_radius_n"]
        # The native fixture's independent checker records the audited scalar
        # RF and its printed-value radius.  Its unit normal is global +Z, so
        # these are the corresponding physical force-vector inputs.
        report = {
            "force_output_recovery_audit": {
                "status": "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS",
                "all_spring_rf_action_reaction_passed": True,
                "all_active_spring_rf_matches_kdu_print_intervals": True,
                "components": [{
                    "spring_name": name,
                    "active": True,
                    "spring_element": spring["element"],
                    "nodes_first_second": spring["nodes"],
                    "dof": 1,
                    "rf_action_reaction_passed": True,
                    "rf_matches_kdu_print_intervals": True,
                    "rf_force_on_first_n": scalar_force,
                    "rf_force_rounding_radius_n": scalar_radius,
                }],
            },
            "physical_connection_forces": {
                name: {
                    "first": owner["first"],
                    "second": owner["second"],
                    "scalar_normal": owner["scalar_normal"],
                    "force_on_first_xyz_n": [0.0, 0.0, scalar_force],
                    "force_rounding_radius_xyz_n": [0.0, 0.0, scalar_radius],
                }
            },
        }

        _, _, interval = _rf_active_normal_opening_interval(
            fixture_model, report, name, spring
        )

        assert interval["interval_lower_mm"] == pytest.approx(
            branch["inferred_opening_interval_mm"][0], rel=1e-10, abs=1e-20
        )
        assert interval["interval_upper_mm"] == pytest.approx(
            branch["inferred_opening_interval_mm"][1], rel=1e-10, abs=1e-20
        )
        assert interval["interval_lower_mm"] <= branch["known_opening_mm"]
        assert branch["known_opening_mm"] <= interval["interval_upper_mm"]
        if branch["branch"] == "below":
            assert interval["interval_upper_mm"] <= TOLERANCE_MM
        else:
            assert interval["interval_lower_mm"] > TOLERANCE_MM


def test_rf_precision_resolves_the_two_cycle08_contact_switch_ambiguities():
    model, response, dat_text = _cycle08_inputs()

    active, transition = derive_next_active_set(
        model, response, dat_text, use_rf_opening_intervals=True
    )

    assert len(active) == 521
    assert "contact_83_13" not in active
    assert "contact_52_21" in active
    assert transition["dat_threshold_rounding_ambiguous_normal_count"] == 2
    assert transition["rf_opening_resolved_normal_count"] == 2
    assert transition["threshold_rounding_ambiguous_normal_count"] == 0
    assert transition["ambiguous_state_changes_suppressed"] == 0
    history = check_active_set_history(C08, active)
    assert history["prior_consumed_branch_count"] == 9
    assert history["status"] == "PASS_NO_REPEATED_ACTIVE_SET"


def test_dat_only_transition_keeps_its_previous_rounding_aware_result():
    model, response, dat_text = _cycle08_inputs()

    active, transition = derive_next_active_set(model, response, dat_text)

    assert len(active) == 522
    assert "contact_83_13" in active
    assert transition["dat_threshold_rounding_ambiguous_normal_count"] == 2
    assert transition["rf_opening_resolved_normal_count"] == 0
    assert transition["threshold_rounding_ambiguous_normal_count"] == 2
    assert transition["ambiguous_state_changes_suppressed"] == 1


def test_rf_transition_fails_closed_when_ambiguous_contact_force_is_missing():
    model, response, dat_text = _cycle08_inputs()
    del response["physical_connection_forces"]["contact_83_13"]

    with pytest.raises(ValueError, match="lacks source-owned RF force recovery"):
        derive_next_active_set(model, response, dat_text, use_rf_opening_intervals=True)


def test_active_set_history_rejects_a_previously_consumed_branch():
    model, _, _ = _cycle08_inputs()

    with pytest.raises(ValueError, match="repeats consumed branch"):
        check_active_set_history(C08, set(model["trial_active_groups"]))
