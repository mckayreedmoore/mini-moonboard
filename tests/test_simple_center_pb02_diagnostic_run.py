"""PB02 diagnostic orchestration accepts only authenticated native results."""

import json

import pytest

from scripts import simple_center_pb02_diagnostic_run as runner

AXIAL_STIFFNESS = 700.0
LATERAL_STIFFNESS = 1200.0
FACE_STIFFNESS = 2400.0
SOURCE_INVENTORY = {"scripts/pb02-producer.py": "a" * 64}
BOLT_NAMES = {f"pb02-bolt-{index}" for index in range(10)}
CONTACT_NAMES = {f"pb02-contact-{index}" for index in range(28)}


def _rows():
    bolts = []
    for name in sorted(BOLT_NAMES):
        bolts.extend(
            (
                {"name": f"{name}/tension", "kind": "bolt_tension"},
                {"name": f"{name}/shear_1", "kind": "bolt_shear"},
                {"name": f"{name}/shear_2", "kind": "bolt_shear"},
            )
        )
    return bolts + [
        {"name": name, "kind": "contact_compression"} for name in sorted(CONTACT_NAMES)
    ]


def _report(case, **changes):
    hold, horizontal = runner.EXPECTED_LOADS[case]
    report = {
        "candidate": runner.CANDIDATE_ID,
        "parameters": {
            "hold": hold,
            "pounds": 250.0,
            "force_xyz_n": [*horizontal, runner.EXPECTED_VERTICAL_FORCE_N],
        },
        "contact_active_set_converged": True,
        "axial_tension_active_set_converged": True,
        "closed_bearing_assumption_passed": True,
        "global_equilibrium_passed": True,
        "member_equilibrium_passed": True,
        "mpc_check_passed": True,
        "numerically_accepted": True,
        "angle_stations": [f"proxy-{index}" for index in range(22)],
        "physical_connection_forces": {
            name: {
                "force_on_first_xyz_n": [float(index + 1), 0.0, 0.0],
                **(
                    {
                        "source_rows": [
                            f"{name}/tension",
                            f"{name}/shear_1",
                            f"{name}/shear_2",
                        ]
                    }
                    if name in BOLT_NAMES
                    else {}
                ),
            }
            for index, name in enumerate(
                sorted(BOLT_NAMES | CONTACT_NAMES | runner.SHIFTED_POST_HEADER_CONTACTS)
            )
        },
        "axial_tension_names": sorted(BOLT_NAMES),
        "bearings": [{"name": name, "active": True} for name in sorted(CONTACT_NAMES)],
        "source_sha256": dict(SOURCE_INVENTORY),
        "artifact_sha256": {},
        "termination": "accepted",
    }
    report.update(changes)
    return report


@pytest.fixture
def isolated_runner(monkeypatch):
    monkeypatch.setattr(
        runner,
        "screen",
        lambda: {
            "candidate": runner.CANDIDATE_ID,
            "panel_kicker_axis_count": 66,
            "legacy_proxy_station_count": 22,
            "native_rows": {
                "bolt_shear": 20,
                "bolt_tension": 10,
                "contact_compression": 28,
            },
            "qualified_for_design": False,
            "drilling_released": False,
            "active_fingerprint": "pb02-test-geometry",
        },
    )
    monkeypatch.setattr(runner, "_source_inventory", lambda: dict(SOURCE_INVENTORY))
    monkeypatch.setattr(runner, "native_row_inventory", _rows)
    monkeypatch.setattr(
        runner,
        "_verify_model_stiffness",
        lambda path, stiffnesses: stiffnesses,
    )


def _run(tmp_path):
    return runner.run_suite(
        tmp_path / "pb02",
        bolt_axial_n_per_mm=AXIAL_STIFFNESS,
        bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
        face_normal_total_n_per_mm=FACE_STIFFNESS,
    )


def _install_fake_native_run(monkeypatch, reports, calls):
    queued = list(reports)

    def fake_run(path, **kwargs):
        case = path.name.split("-")[0] + "-" + path.name.split("-")[1]
        # Case names are the prefix preceding the numbered attempt label.
        case = next(name for name in runner.CASE_ORDER if path.name.startswith(name))
        report = queued.pop(0) if queued else _report(case)
        calls.append(
            {
                "case": case,
                "path": path,
                "strategy": kwargs["contact_update_strategy"],
                "seed": kwargs["initial_contact_names"],
                "max_cycles": kwargs["max_cycles"],
            }
        )
        path.mkdir(parents=True)
        (path / "report.json").write_text(json.dumps(report) + "\n")
        return report

    monkeypatch.setattr(runner.native, "run", fake_run)


def test_exact_case_order_is_preserved_for_six_first_attempt_acceptances(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    _install_fake_native_run(
        monkeypatch, [_report(case) for case in runner.CASE_ORDER], calls
    )

    summary = _run(tmp_path)

    assert tuple(call["case"] for call in calls) == runner.CASE_ORDER
    assert list(summary["accepted_cases"]) == list(runner.CASE_ORDER)
    assert all(call["strategy"] == "all" for call in calls)
    assert all(call["seed"] is None for call in calls)
    assert summary["accepted_case_count"] == 6


def test_forward_uses_only_prescribed_fallback_and_authenticated_rear_seed(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    contact_failed = _report(
        "a12-forward",
        contact_active_set_converged=False,
        physical_connection_forces={"rejected-contact-force": 1e99},
    )
    axial_failed = _report(
        "a12-forward",
        axial_tension_active_set_converged=False,
        physical_connection_forces={"rejected-axial-force": -1e99},
    )
    reports = [
        contact_failed,
        axial_failed,
        _report("a12-rear"),
        _report("a12-forward"),
        *[_report(case) for case in runner.CASE_ORDER[2:]],
    ]
    _install_fake_native_run(monkeypatch, reports, calls)

    summary = _run(tmp_path)

    assert [
        (call["case"], call["strategy"], call["seed"] is not None) for call in calls[:4]
    ] == [
        ("a12-forward", "all", False),
        ("a12-forward", "one_at_a_time", False),
        ("a12-rear", "all", False),
        ("a12-forward", "one_at_a_time", True),
    ]
    assert calls[3]["seed"] == sorted(CONTACT_NAMES)
    assert summary["accepted_cases"]["a12-forward"]["search_seed_case"] == ("a12-rear")
    assert summary["accepted_cases"]["a12-rear"]["attempt"] == "01-all-unseeded"


def test_rear_must_authenticate_before_its_contacts_can_seed_forward(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    reports = [
        _report("a12-forward", contact_active_set_converged=False),
        _report("a12-forward", axial_tension_active_set_converged=False),
        _report("a12-rear", candidate="not-pb02"),
    ]
    _install_fake_native_run(monkeypatch, reports, calls)

    with pytest.raises(ValueError, match="candidate identity changed"):
        _run(tmp_path)

    assert [call["case"] for call in calls] == [
        "a12-forward",
        "a12-forward",
        "a12-rear",
    ]
    assert all(call["seed"] is None for call in calls)


@pytest.mark.parametrize(
    "failed_flag",
    ["contact_active_set_converged", "axial_tension_active_set_converged"],
)
def test_later_case_retries_when_either_active_set_does_not_converge(
    tmp_path, monkeypatch, isolated_runner, failed_flag
):
    calls = []
    failed = _report("a12-left")
    failed[failed_flag] = False
    reports = [
        _report("a12-forward"),
        _report("a12-rear"),
        failed,
        _report("a12-left"),
        _report("k12-right"),
        _report("k12-rear"),
        _report("a1-rear"),
    ]
    _install_fake_native_run(monkeypatch, reports, calls)

    summary = _run(tmp_path)

    left_calls = [call for call in calls if call["case"] == "a12-left"]
    assert [call["strategy"] for call in left_calls] == ["all", "one_at_a_time"]
    assert summary["accepted_cases"]["a12-left"]["attempt"] == (
        "02-one-at-a-time-unseeded"
    )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"global_equilibrium_passed": False}, "equilibrium audits failed"),
        ({"candidate": "wrong-candidate"}, "candidate identity changed"),
    ],
)
def test_converged_equilibrium_or_identity_failure_stops_without_retry(
    tmp_path, monkeypatch, isolated_runner, changes, message
):
    calls = []
    _install_fake_native_run(monkeypatch, [_report("a12-forward", **changes)], calls)

    with pytest.raises(ValueError, match=message):
        _run(tmp_path)

    assert [(call["case"], call["strategy"]) for call in calls] == [
        ("a12-forward", "all")
    ]


def test_rejected_attempt_forces_never_enter_suite_summary(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    sentinel = "FORCE_FROM_REJECTED_NATIVE_ATTEMPT"
    rejected = _report(
        "a12-forward",
        contact_active_set_converged=False,
        physical_connection_forces={sentinel: {"signed_force_n": 9.9e88}},
        bearings=[{"name": sentinel, "active": True}],
    )
    reports = [rejected, _report("a12-forward"), *map(_report, runner.CASE_ORDER[1:])]
    _install_fake_native_run(monkeypatch, reports, calls)

    summary = _run(tmp_path)
    serialized = json.dumps(summary)

    assert sentinel not in serialized
    assert "9.9e+88" not in serialized
    assert summary["rejected_attempt_forces_included"] is False
    assert summary["attempts"][0]["forces_in_suite_summary"] is False
    assert "physical_connection_forces" not in summary["attempts"][0]


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan"), True])
def test_stiffness_selection_rejects_nonpositive_nonfinite_or_boolean(value):
    with pytest.raises(ValueError, match="positive and finite"):
        runner._selected_stiffnesses(value, LATERAL_STIFFNESS, FACE_STIFFNESS)


def test_stiffness_selection_records_exact_explicit_values_and_unqualified_status():
    result = runner._selected_stiffnesses(
        AXIAL_STIFFNESS, LATERAL_STIFFNESS, FACE_STIFFNESS
    )

    assert result["exact_selected_values"] == {
        "bolt_axial_n_per_mm": AXIAL_STIFFNESS,
        "bolt_lateral_n_per_mm": LATERAL_STIFFNESS,
        "face_normal_total_per_interface_n_per_mm": FACE_STIFFNESS,
    }
    assert result["complete_joint_stiffness_qualified"] is False
    assert "developmental" in result["selection_status"]


def test_changed_source_inventory_is_rejected_before_any_native_solve(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    monkeypatch.setattr(
        runner,
        "_source_inventory",
        lambda: (_ for _ in ()).throw(ValueError("changed after import")),
    )
    _install_fake_native_run(monkeypatch, [], calls)

    with pytest.raises(ValueError, match="changed after import"):
        _run(tmp_path)

    assert calls == []


def test_changed_six_case_load_inventory_is_rejected_before_native_solve(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    changed = dict(runner.CASES)
    changed["a12-forward"] = ("A12", (1.0, -300.0))
    monkeypatch.setattr(runner, "CASES", changed)
    _install_fake_native_run(monkeypatch, [], calls)

    with pytest.raises(ValueError, match="six-case load inventory changed"):
        _run(tmp_path)

    assert calls == []


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        (
            {
                "parameters": {
                    "hold": "A12",
                    "pounds": 250.0,
                    "force_xyz_n": [0.0, 300.0, -1112.055],
                }
            },
            "load inventory changed",
        ),
        ({"source_sha256": {}}, "source inventory is unauthenticated"),
    ],
)
def test_converged_load_or_source_failure_stops_without_retry(
    tmp_path, monkeypatch, isolated_runner, changes, message
):
    calls = []
    _install_fake_native_run(monkeypatch, [_report("a12-forward", **changes)], calls)

    with pytest.raises(ValueError, match=message):
        _run(tmp_path)

    assert len(calls) == 1


def test_summary_and_case_scope_preserve_developmental_claim_boundaries(
    tmp_path, monkeypatch, isolated_runner
):
    calls = []
    _install_fake_native_run(
        monkeypatch, [_report(case) for case in runner.CASE_ORDER], calls
    )

    summary = _run(tmp_path)
    false_claims = (
        "qualified_for_design",
        "actual_joint_demands_qualified",
        "resistance_checked",
        "acceptance",
        "drilling_released",
        "fabrication_released",
    )

    assert summary["developmental_only"] is True
    assert all(summary[key] is False for key in false_claims)
    assert summary["validation"] == {
        "geometry_inventory": True,
        "topology_inventory": True,
        "candidate_identity": True,
        "stiffness_inventory": True,
        "producer_source_inventory": True,
        "six_case_load_inventory": True,
        "all_accepted_case_equilibrium_audits": True,
    }
    for case, record in summary["accepted_cases"].items():
        report = json.loads(
            (tmp_path / "pb02" / record["path"] / "report.json").read_text()
        )
        scope = report["diagnostic_scope"]
        assert scope["case"] == case
        assert scope["developmental_only"] is True
        assert all(scope[key] is False for key in false_claims)
        assert report["qualified_for_design"] is False
        assert report["drilling_released"] is False
        assert report["fabrication_released"] is False
