"""PB03 diagnostic orchestration preserves the authenticated PB02 search policy."""

import json

import pytest

from scripts import simple_pb03_diagnostic_run as runner

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
        "contact_cycles": [],
        "termination": termination,
        "artifact_sha256": {},
    }


@pytest.fixture
def isolated(monkeypatch):
    monkeypatch.setattr(runner, "_preflight", lambda _: {"contract": "bound"})
    monkeypatch.setattr(runner, "_validate_accepted_report", lambda report, *_: report)
    monkeypatch.setattr(runner, "_write_accepted_scope", lambda *args: None)
    monkeypatch.setattr(
        runner,
        "_normal_contact_seed",
        lambda report: ["normal-contact"],
    )


def _run(tmp_path, **changes):
    return runner.run_suite(
        tmp_path / "pb03",
        bolt_axial_n_per_mm=AXIAL,
        bolt_lateral_n_per_mm=LATERAL,
        face_normal_total_n_per_mm=FACE,
        floor_contact_n_per_mm=FLOOR,
        **changes,
    )


def _install(monkeypatch, reports, calls):
    queued = list(reports)

    def fake_attempt(case, path, **kwargs):
        report = queued.pop(0) if queued else _report(case)
        report["contact_update_strategy"] = kwargs["strategy"]
        calls.append(
            {
                "case": case,
                "strategy": kwargs["strategy"],
                "seed": kwargs["initial_contact_names"],
                "axial_seed": kwargs["initial_axial_tension_names"],
            }
        )
        path.mkdir(parents=True)
        (path / "report.json").write_text(json.dumps(report) + "\n")
        return report

    monkeypatch.setattr(runner, "_run_attempt", fake_attempt)


def test_exact_six_case_order_and_default_output_contract(
    tmp_path, monkeypatch, isolated
):
    calls = []
    _install(monkeypatch, [_report(case) for case in runner.CASE_ORDER], calls)

    summary = _run(tmp_path)

    assert tuple(call["case"] for call in calls) == runner.CASE_ORDER
    assert list(summary["accepted_cases"]) == list(runner.CASE_ORDER)
    assert summary["rejected_attempt_forces_included"] is False
    assert summary["qualified_for_design"] is False
    assert summary["drilling_released"] is False
    assert (tmp_path / "pb03/pb03-eight-station-diagnostic.json").is_file()


def test_forward_preserves_rear_seed_fallback_without_failed_forces(
    tmp_path, monkeypatch, isolated
):
    calls = []
    failed = _report(
        "a12-forward",
        accepted=False,
        termination="Contact active set repeated without convergence",
    )
    failed["physical_connection_forces"] = {"rejected": {"force": 1e99}}
    reports = [
        failed,
        _report("a12-forward", accepted=False, termination="not converged"),
        _report("a12-rear"),
        _report("a12-forward"),
        *[_report(case) for case in runner.CASE_ORDER[2:]],
    ]
    _install(monkeypatch, reports, calls)
    monkeypatch.setattr(
        runner,
        "_same_case_repeated_seed",
        lambda *args: (["normal-contact"], ["bolt"]),
    )

    summary = _run(tmp_path)

    assert [(row["case"], row["strategy"]) for row in calls[:4]] == [
        ("a12-forward", "all"),
        ("a12-forward", "one_at_a_time"),
        ("a12-rear", "all"),
        ("a12-forward", "one_at_a_time"),
    ]
    assert calls[1]["seed"] == ["normal-contact"]
    assert calls[1]["axial_seed"] == ["bolt"]
    assert calls[3]["seed"] == ["normal-contact"]
    assert "physical_connection_forces" not in json.dumps(summary)
    assert "1e+99" not in json.dumps(summary)


def test_first_case_mode_runs_only_a12_forward(tmp_path, monkeypatch, isolated):
    calls = []
    _install(monkeypatch, [_report("a12-forward")], calls)

    summary = _run(tmp_path, cases=("a12-forward",))

    assert [row["case"] for row in calls] == ["a12-forward"]
    assert list(summary["accepted_cases"]) == ["a12-forward"]
    assert summary["accepted_case_count"] == 1
