"""Fail-closed orchestration tests for conditional barrel native cases."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import owner_barrel_six_case_run as runner

AXIAL = 1000.0
LATERAL = 500.0
CONTACT = 100.0


@pytest.fixture(autouse=True)
def stable_loaded_source_snapshot(monkeypatch):
    """Test orchestration against source bytes present when each test starts."""
    case_sources = runner.native.extra_source_hashes(runner.case_runner.PRODUCER_PATHS)
    suite_sources = runner.native.extra_source_hashes(runner.SUITE_SOURCE_PATHS)
    native_sources = runner.native.source_hashes()
    monkeypatch.setattr(runner.case_runner, "_source_inventory", lambda: case_sources)
    monkeypatch.setattr(runner, "_suite_sources", lambda: suite_sources)
    monkeypatch.setattr(runner.native, "source_hashes", lambda: native_sources)


def _write_fake_report(output, case, kwargs, *, accepted=True, termination="accepted"):
    output = Path(output)
    output.mkdir()
    model = output / "model.pkl"
    model.write_bytes(b"authenticated fake model")
    axial_names = [f"barrel-{index:02d}" for index in range(46)]
    radial_names = [f"{name}__radial_clearance" for name in axial_names]
    initial_radial = kwargs["initial_radial_clearance_states"] or {
        name: None for name in radial_names
    }
    scope = {
        "case": case,
        "candidate": runner.CANDIDATE_ID,
        "case_load": {
            "hold": runner.case_runner.CASE_LOADS[case][0],
            "horizontal_force_xy_n": list(runner.case_runner.CASE_LOADS[case][1]),
            "applied_force_xyz_n": [
                *runner.case_runner.CASE_LOADS[case][1],
                runner.EXPECTED_VERTICAL_FORCE_N,
            ],
            "pounds": 250.0,
        },
        "conditional_stiffnesses": {
            "barrel_axial_n_per_mm": kwargs["barrel_axial_n_per_mm"],
            "barrel_lateral_n_per_mm": kwargs["barrel_lateral_n_per_mm"],
            "contact_n_per_mm3": kwargs["contact_n_per_mm3"],
        },
        "contact_update_strategy": kwargs["contact_update_strategy"],
        "initial_contact_names": (
            sorted(kwargs["initial_contact_names"])
            if kwargs["initial_contact_names"] is not None
            else None
        ),
        "initial_axial_tension_names": (
            sorted(kwargs["initial_axial_tension_names"])
            if kwargs["initial_axial_tension_names"] is not None
            else None
        ),
        "initial_radial_clearance_states": initial_radial,
        "max_cycles": kwargs["max_cycles"],
        "compression_only_face_contacts": True,
        "tension_only_barrel_axial_springs": True,
        "radial_clearance_active_set": True,
        "diagnostic_only": True,
        "conditional_only": True,
        "rejected_for_acceptance": not accepted,
        "retry_checkpoint_only": not accepted,
        "joint_resistance_qualified": False,
        "qualified_for_design": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
        "structural_released": False,
    }
    scope_path = output / "diagnostic-scope.json"
    scope_path.write_text(json.dumps(scope) + "\n")
    hold, horizontal = runner.case_runner.CASE_LOADS[case]
    report = {
        "candidate": runner.CANDIDATE_ID,
        "parameters": {
            "hold": hold,
            "pounds": 250.0,
            "force_xyz_n": [*horizontal, runner.EXPECTED_VERTICAL_FORCE_N],
        },
        "source_sha256": {
            **runner.native.source_hashes(),
            **runner.case_runner._source_inventory(),
        },
        "contact_update_strategy": kwargs["contact_update_strategy"],
        "angle_stations": [],
        "axial_tension_names": axial_names,
        "radial_clearance_names": radial_names,
        "radial_clearance_states": {name: None for name in radial_names},
        "initial_radial_clearance_states": initial_radial,
        "owner_barrel_diagnostic_scope": scope,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "diy_released": False,
        "acceptance": False,
        "joint_resistance_qualified": False,
        "structural_released": False,
        "owner_barrel_wrapper_accepted": accepted,
        "retry_checkpoint_eligible": not accepted,
        "native_numerically_accepted": accepted,
        "contact_active_set_converged": accepted,
        "axial_tension_active_set_converged": accepted,
        "radial_clearance_active_set_converged": accepted,
        "closed_bearing_assumption_passed": accepted,
        "axial_tension_assumption_passed": accepted,
        "radial_clearance_assumption_passed": accepted,
        "global_equilibrium_passed": True,
        "member_equilibrium_passed": True,
        "mpc_check_passed": True,
        "numerically_accepted": accepted,
        "termination": termination,
        "contact_cycles": [],
        "bearings": [{"name": "normal-contact", "active": True}],
        "axial_tension": [
            {"name": name, "active": index == 0}
            for index, name in enumerate(axial_names)
        ],
        "physical_connection_forces": {
            name: {"force_on_first_xyz_n": [1.0, 2.0, 3.0]}
            for name in axial_names
        },
        "artifact_sha256": {
            "model.pkl": hashlib.sha256(model.read_bytes()).hexdigest(),
            "diagnostic-scope.json": hashlib.sha256(scope_path.read_bytes()).hexdigest(),
        },
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report) + "\n")
    return report


def _run(tmp_path, **changes):
    values = {
        "output": tmp_path / "suite",
        "barrel_axial_n_per_mm": AXIAL,
        "barrel_lateral_n_per_mm": LATERAL,
        "contact_n_per_mm3": CONTACT,
        "max_cycles": 4,
        "max_same_case_continuations": 1,
    }
    values.update(changes)
    return runner.run_suite(**values)


def test_exact_six_case_suite_stays_conditional_and_excludes_forces(
    tmp_path, monkeypatch
):
    calls = []

    def fake_run(case, output, **kwargs):
        calls.append((case, kwargs["contact_update_strategy"]))
        return _write_fake_report(output, case, kwargs)

    monkeypatch.setattr(runner.case_runner, "run_case", fake_run)
    summary = _run(tmp_path)

    assert calls == [(case, "all") for case in runner.CASE_ORDER]
    assert list(summary["accepted_cases"]) == list(runner.CASE_ORDER)
    assert summary["accepted_case_count"] == 6
    assert summary["status"] == "complete_authenticated_conditional_numerical_suite"
    assert summary["conditional_only"] is True
    assert summary["joint_resistance_qualified"] is False
    assert summary["qualified_for_design"] is False
    assert summary["diy_released"] is False
    assert "physical_connection_forces" not in json.dumps(summary)
    assert (tmp_path / "suite" / runner.SUMMARY_NAME).is_file()

    monkeypatch.setattr(
        runner.case_runner,
        "run_case",
        lambda *_args, **_kwargs: pytest.fail("complete resume must not rerun cases"),
    )
    assert _run(tmp_path, resume=True) == summary


def test_repeated_forward_uses_membership_seed_then_rear_fallback(
    tmp_path, monkeypatch
):
    calls = []
    outcomes = iter(
        [
            (False, "Contact active set repeated without convergence"),
            (False, "not converged"),
            (True, "accepted"),
            (True, "accepted"),
            *((True, "accepted") for _ in runner.CASE_ORDER[2:]),
        ]
    )

    def fake_run(case, output, **kwargs):
        accepted, termination = next(outcomes)
        calls.append(
            (
                case,
                kwargs["contact_update_strategy"],
                kwargs["initial_contact_names"],
                kwargs["initial_axial_tension_names"],
                kwargs["initial_radial_clearance_states"],
            )
        )
        return _write_fake_report(
            output, case, kwargs, accepted=accepted, termination=termination
        )

    monkeypatch.setattr(runner.case_runner, "run_case", fake_run)
    summary = _run(tmp_path)

    assert calls[:4] == [
        ("a12-forward", "all", None, None, None),
        (
            "a12-forward",
            "one_at_a_time",
            ["normal-contact"],
            ["barrel-00"],
            {f"barrel-{index:02d}__radial_clearance": None for index in range(46)},
        ),
        ("a12-rear", "all", None, None, None),
        ("a12-forward", "one_at_a_time", ["normal-contact"], None, None),
    ]
    assert summary["accepted_case_count"] == 6
    rejected = [row for row in summary["attempts"] if row["status"].startswith("rejected")]
    assert len(rejected) == 2
    assert all(row["forces_in_suite_state"] is False for row in rejected)


def test_radial_only_repeated_state_enters_one_at_a_time_retry(
    tmp_path, monkeypatch
):
    forward_calls = []

    def fake_run(case, output, **kwargs):
        if case == "a12-forward":
            forward_calls.append(kwargs)
            if len(forward_calls) == 1:
                report = _write_fake_report(
                    output,
                    case,
                    kwargs,
                    accepted=False,
                    termination="Contact active set repeated without convergence",
                )
                report.update(
                    contact_active_set_converged=True,
                    axial_tension_active_set_converged=True,
                    closed_bearing_assumption_passed=True,
                    axial_tension_assumption_passed=True,
                    radial_clearance_active_set_converged=False,
                    radial_clearance_assumption_passed=False,
                )
                (Path(output) / "report.json").write_text(json.dumps(report) + "\n")
                return report
        return _write_fake_report(output, case, kwargs)

    monkeypatch.setattr(runner.case_runner, "run_case", fake_run)
    summary = _run(tmp_path)

    assert len(forward_calls) == 2
    assert forward_calls[1]["contact_update_strategy"] == "one_at_a_time"
    assert forward_calls[1]["initial_radial_clearance_states"] is not None
    assert summary["accepted_case_count"] == 6


def test_resume_abandons_interrupted_attempt_without_promoting_it(
    tmp_path, monkeypatch
):
    calls = []

    def interrupted(case, output, **kwargs):
        calls.append(case)
        if len(calls) == 3:
            Path(output).mkdir()
            raise RuntimeError("simulated interruption")
        return _write_fake_report(output, case, kwargs)

    monkeypatch.setattr(runner.case_runner, "run_case", interrupted)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        _run(tmp_path)
    assert not (tmp_path / "suite" / runner.SUMMARY_NAME).exists()

    monkeypatch.setattr(
        runner.case_runner,
        "run_case",
        lambda case, output, **kwargs: _write_fake_report(output, case, kwargs),
    )
    summary = _run(tmp_path, resume=True)

    assert summary["accepted_case_count"] == 6
    assert len(summary["abandoned_attempts"]) == 1
    assert summary["abandoned_attempts"][0]["case"] == "a12-left"
    assert summary["abandoned_attempts"][0]["status"] == (
        "interrupted_without_authenticated_report"
    )


def test_resume_recovers_persisted_pending_report_exactly_once(tmp_path, monkeypatch):
    calls = []

    def interrupted_after_report(case, output, **kwargs):
        calls.append(case)
        report = _write_fake_report(output, case, kwargs)
        if len(calls) == 3:
            raise RuntimeError("simulated post-report interruption")
        return report

    monkeypatch.setattr(runner.case_runner, "run_case", interrupted_after_report)
    with pytest.raises(RuntimeError, match="post-report interruption"):
        _run(tmp_path)

    resumed_calls = []

    def resumed(case, output, **kwargs):
        resumed_calls.append(case)
        return _write_fake_report(output, case, kwargs)

    monkeypatch.setattr(runner.case_runner, "run_case", resumed)
    summary = _run(tmp_path, resume=True)

    assert "a12-left" not in resumed_calls
    assert summary["accepted_cases"]["a12-left"]["numerically_accepted"] is True
    assert summary["abandoned_attempts"] == []


def test_resume_rejects_force_payload_in_attempt_summary(tmp_path, monkeypatch):
    calls = []

    def interrupted_after_rejection(case, output, **kwargs):
        calls.append(case)
        if len(calls) == 1:
            return _write_fake_report(
                output, case, kwargs, accepted=False, termination="not converged"
            )
        Path(output).mkdir()
        raise RuntimeError("stop after persisted rejection")

    monkeypatch.setattr(runner.case_runner, "run_case", interrupted_after_rejection)
    with pytest.raises(RuntimeError, match="persisted rejection"):
        _run(tmp_path)

    state_path = tmp_path / "suite" / runner.STATE_NAME
    state = json.loads(state_path.read_text())
    state["attempts"][0]["forces_in_suite_state"] = True
    state["attempts"][0]["physical_connection_forces"] = {"forged": [1.0, 2.0, 3.0]}
    state_path.write_text(json.dumps(state) + "\n")

    with pytest.raises(ValueError, match="attempt summary changed"):
        _run(tmp_path, resume=True)
    assert not (tmp_path / "suite" / runner.SUMMARY_NAME).exists()


def test_max_cycle_continuation_carries_radial_checkpoint(tmp_path, monkeypatch):
    left_calls = []

    def fake_run(case, output, **kwargs):
        if case != "a12-left":
            return _write_fake_report(output, case, kwargs)
        left_calls.append(kwargs)
        if len(left_calls) == 1:
            return _write_fake_report(
                output, case, kwargs, accepted=False, termination="not converged"
            )
        if len(left_calls) == 2:
            report = _write_fake_report(
                output,
                case,
                kwargs,
                accepted=False,
                termination="maximum cycles exhausted",
            )
            report["contact_cycles"] = [{} for _ in range(kwargs["max_cycles"])]
            first = min(report["radial_clearance_states"])
            report["radial_clearance_states"][first] = [1.0, 0.0]
            report.update(
                contact_active_set_converged=True,
                axial_tension_active_set_converged=True,
                closed_bearing_assumption_passed=True,
                axial_tension_assumption_passed=True,
                radial_clearance_active_set_converged=False,
                radial_clearance_assumption_passed=False,
            )
            (Path(output) / "report.json").write_text(json.dumps(report) + "\n")
            return report
        return _write_fake_report(output, case, kwargs)

    monkeypatch.setattr(runner.case_runner, "run_case", fake_run)
    summary = _run(tmp_path)

    assert len(left_calls) == 3
    first = "barrel-00__radial_clearance"
    assert left_calls[2]["initial_radial_clearance_states"][first] == [1.0, 0.0]
    assert summary["accepted_cases"]["a12-left"]["attempt"].startswith("03-")


def test_resume_rejects_changed_accepted_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner.case_runner,
        "run_case",
        lambda case, output, **kwargs: _write_fake_report(output, case, kwargs),
    )
    summary = _run(tmp_path)
    first = tmp_path / "suite" / summary["accepted_cases"]["a12-forward"]["path"]
    report = json.loads((first / "report.json").read_text())
    report["qualified_for_design"] = True
    (first / "report.json").write_text(json.dumps(report) + "\n")

    with pytest.raises(ValueError, match="report changed"):
        _run(tmp_path, resume=True)


def test_first_run_never_promotes_report_that_differs_on_disk(tmp_path, monkeypatch):
    def divergent(case, output, **kwargs):
        report = _write_fake_report(output, case, kwargs)
        disk = json.loads((Path(output) / "report.json").read_text())
        disk["qualified_for_design"] = True
        (Path(output) / "report.json").write_text(json.dumps(disk) + "\n")
        return report

    monkeypatch.setattr(runner.case_runner, "run_case", divergent)
    with pytest.raises(ValueError, match="differs from persisted"):
        _run(tmp_path)

    state = json.loads((tmp_path / "suite" / runner.STATE_NAME).read_text())
    assert state["accepted_cases"] == {}
    assert state["suite_complete"] is False
    assert not (tmp_path / "suite" / runner.SUMMARY_NAME).exists()


@pytest.mark.parametrize(
    ("scope_change", "message"),
    [
        (lambda scope: scope.update(acceptance=True), "acceptance must remain false"),
        (lambda scope: scope.pop("structural_released"), "structural_released"),
    ],
)
def test_authenticated_scope_requires_exact_unreleased_flags(
    tmp_path, monkeypatch, scope_change, message
):
    def false_scope(case, output, **kwargs):
        report = _write_fake_report(output, case, kwargs)
        scope_path = Path(output) / "diagnostic-scope.json"
        scope = json.loads(scope_path.read_text())
        scope_change(scope)
        scope_path.write_text(json.dumps(scope) + "\n")
        report["owner_barrel_diagnostic_scope"] = scope
        report["artifact_sha256"]["diagnostic-scope.json"] = hashlib.sha256(
            scope_path.read_bytes()
        ).hexdigest()
        (Path(output) / "report.json").write_text(json.dumps(report) + "\n")
        return report

    monkeypatch.setattr(runner.case_runner, "run_case", false_scope)
    with pytest.raises(ValueError, match=message):
        _run(tmp_path)
    assert not (tmp_path / "suite" / runner.SUMMARY_NAME).exists()


def test_nonconverged_suite_never_writes_final_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner.case_runner,
        "run_case",
        lambda case, output, **kwargs: _write_fake_report(
            output, case, kwargs, accepted=False, termination="not converged"
        ),
    )
    with pytest.raises(RuntimeError, match="a12-rear did not converge"):
        _run(tmp_path, max_same_case_continuations=0)

    state = json.loads((tmp_path / "suite" / runner.STATE_NAME).read_text())
    assert state["suite_complete"] is False
    assert state["accepted_cases"] == {}
    assert not (tmp_path / "suite" / runner.SUMMARY_NAME).exists()


def test_resume_requires_identical_conditional_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner.case_runner,
        "run_case",
        lambda case, output, **kwargs: _write_fake_report(output, case, kwargs),
    )
    _run(tmp_path)

    with pytest.raises(ValueError, match="does not match"):
        _run(tmp_path, resume=True, barrel_axial_n_per_mm=AXIAL + 1.0)


def test_source_contract_includes_orchestrator_and_case_runner():
    names = runner.LOADED_SUITE_SOURCE_SHA256
    assert "scripts/owner_barrel_six_case_run.py" in names
    assert "scripts/owner_barrel_native_run.py" in names
    assert "scripts/owner_barrel_native_preparation.py" in names


@pytest.mark.parametrize("change", ["load", "extra", "candidate"])
def test_frozen_candidate_and_six_case_identity_fail_before_output(
    tmp_path, monkeypatch, change
):
    if change == "candidate":
        monkeypatch.setattr(
            runner.case_runner.IntegratedBarrelNative, "KEY", "changed-candidate"
        )
    else:
        loads = dict(runner.EXPECTED_LOADS)
        if change == "load":
            loads["a12-forward"] = ("A12", (1.0, -300.0))
        else:
            loads["extra-case"] = ("A1", (0.0, 0.0))
        monkeypatch.setattr(runner.case_runner, "CASE_LOADS", loads)

    with pytest.raises(ValueError, match="candidate or six-case identity"):
        _run(tmp_path)
    assert not (tmp_path / "suite").exists()
