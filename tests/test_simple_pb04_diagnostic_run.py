"""PB04 delegates only the proven PB03 active-set orchestration policy."""

import json

import pytest

from scripts import simple_pb04_diagnostic_run as runner

AXIAL = 700.0
LATERAL = 1200.0
FACE = 2400.0
FLOOR = 10000.0


def _report(case, *, accepted=True, termination="accepted"):
    hold, horizontal = runner.EXPECTED_LOADS[case]
    return {
        "candidate": runner.CANDIDATE_ID,
        "parameters": {
            "hold": hold,
            "pounds": 250.0,
            "force_xyz_n": [*horizontal, runner.EXPECTED_VERTICAL_FORCE_N],
        },
        "contact_active_set_converged": accepted,
        "axial_tension_active_set_converged": accepted,
        "closed_bearing_assumption_passed": accepted,
        "global_equilibrium_passed": accepted,
        "member_equilibrium_passed": accepted,
        "mpc_check_passed": accepted,
        "numerically_accepted": accepted,
        "bearings": [{"name": "normal-contact", "active": True}],
        "axial_tension": [{"name": "bolt", "active": True}],
        "axial_tension_names": ["bolt"],
        "termination": termination,
        "artifact_sha256": {},
    }


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr(runner, "_preflight", lambda _: {"contract": "pb04"})
    monkeypatch.setattr(runner, "_validate_accepted_report", lambda report, *_: report)
    monkeypatch.setattr(runner, "_write_accepted_scope", lambda *args: None)
    monkeypatch.setattr(
        runner.orchestration, "_normal_contact_seed", lambda _: ["normal-contact"]
    )


def _install(monkeypatch, reports, calls):
    queued = list(reports)

    def fake_attempt(case, path, **kwargs):
        report = queued.pop(0) if queued else _report(case)
        calls.append((case, kwargs["strategy"]))
        path.mkdir(parents=True)
        (path / "report.json").write_text(json.dumps(report) + "\n")
        return report

    monkeypatch.setattr(runner, "_run_attempt", fake_attempt)


def _run(tmp_path, **changes):
    return runner.run_suite(
        tmp_path / "pb04",
        bolt_axial_n_per_mm=AXIAL,
        bolt_lateral_n_per_mm=LATERAL,
        face_normal_total_n_per_mm=FACE,
        floor_contact_n_per_mm=FLOOR,
        **changes,
    )


def test_exact_six_case_order_and_pb04_summary_name(tmp_path, monkeypatch, isolated):
    calls = []
    _install(monkeypatch, [_report(case) for case in runner.CASE_ORDER], calls)

    summary = _run(tmp_path)

    assert tuple(case for case, _ in calls) == runner.CASE_ORDER
    assert list(summary["accepted_cases"]) == list(runner.CASE_ORDER)
    assert summary["qualified_for_design"] is False
    assert summary["drilling_released"] is False
    assert (tmp_path / "pb04" / runner.SUMMARY_NAME).is_file()
    assert not (tmp_path / "pb04/pb03-eight-station-diagnostic.json").exists()


def test_first_case_mode_and_retry_policy_are_unchanged(
    tmp_path, monkeypatch, isolated
):
    calls = []
    failed = _report(
        "a12-forward",
        accepted=False,
        termination="Contact active set repeated without convergence",
    )
    _install(monkeypatch, [failed, _report("a12-forward")], calls)
    monkeypatch.setattr(
        runner,
        "_same_case_repeated_seed",
        lambda *args: (["normal-contact"], ["bolt"]),
    )

    summary = _run(tmp_path, cases=("a12-forward",))

    assert calls == [("a12-forward", "all"), ("a12-forward", "one_at_a_time")]
    assert list(summary["accepted_cases"]) == ["a12-forward"]
    assert summary["rejected_attempt_forces_included"] is False
