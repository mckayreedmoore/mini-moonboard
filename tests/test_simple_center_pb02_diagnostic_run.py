"""PB02 diagnostic orchestration accepts only authenticated native results."""

import json
import pickle

import pytest

from scripts import simple_center_pb02_diagnostic_run as runner

AXIAL_STIFFNESS = 700.0
LATERAL_STIFFNESS = 1200.0
FACE_STIFFNESS = 2400.0
SOURCE_INVENTORY = {"scripts/pb02-producer.py": "a" * 64}
NATIVE_PARTITION = runner.native_contact_partition(2)[1]
BOLT_NAMES = {f"pb02-bolt-{index}" for index in range(10)}
CONTACT_NAMES = {
    f"pb02-contact-{index}"
    for index in range(NATIVE_PARTITION["contact_row_count"])
}


def _rows(*_args, **_kwargs):
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
        "axial_tension": [
            {"name": name, "active": True} for name in sorted(BOLT_NAMES)
        ],
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
        lambda *args: {
            "candidate": runner.CANDIDATE_ID,
            "panel_kicker_axis_count": 66,
            "legacy_proxy_station_count": 22,
            "native_rows": {
                "bolt_shear": 20,
                "bolt_tension": 10,
                "contact_compression": NATIVE_PARTITION["contact_row_count"],
            },
            "canonical_contact_partition": NATIVE_PARTITION,
            "qualified_for_design": False,
            "drilling_released": False,
            "active_fingerprint": "pb02-test-geometry",
        },
    )
    monkeypatch.setattr(runner, "_source_inventory", lambda: dict(SOURCE_INVENTORY))
    monkeypatch.setattr(
        runner, "_native_source_inventory", lambda: dict(SOURCE_INVENTORY)
    )
    monkeypatch.setattr(runner, "native_row_inventory", _rows)
    monkeypatch.setattr(
        runner,
        "_verify_model_stiffness",
        lambda path, stiffnesses: stiffnesses,
    )
    monkeypatch.setattr(
        runner,
        "_model_identity",
        lambda path, case, stiffnesses: f"authenticated-model-{case}",
    )
    monkeypatch.setattr(
        runner,
        "_contact_aggregation",
        lambda report, stiffnesses: {
            "partition_fingerprint": NATIVE_PARTITION["fingerprint"],
            "grid_resolution": NATIVE_PARTITION["grid_resolution"],
            "interfaces": {edge: {} for edge in NATIVE_PARTITION["interfaces"]},
        },
    )


def _run(tmp_path, **changes):
    return runner.run_suite(
        tmp_path / "pb02",
        bolt_axial_n_per_mm=AXIAL_STIFFNESS,
        bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
        face_normal_total_n_per_mm=FACE_STIFFNESS,
        **changes,
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
                "axial_seed": kwargs["initial_axial_tension_names"],
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
    assert calls[3]["axial_seed"] is None
    assert summary["accepted_cases"]["a12-forward"]["search_seed_case"] == ("a12-rear")
    assert summary["accepted_cases"]["a12-rear"]["attempt"] == "01-all-unseeded"


def _exhausted(case, max_cycles, *, normal_names=None, axial_names=None, **changes):
    normal_names = CONTACT_NAMES if normal_names is None else set(normal_names)
    axial_names = BOLT_NAMES if axial_names is None else set(axial_names)
    report = _report(
        case,
        contact_active_set_converged=False,
        axial_tension_active_set_converged=False,
        numerically_accepted=False,
        termination="Maximum active-set cycles exhausted without convergence",
        contact_update_strategy="one_at_a_time",
        contact_cycles=[{"cycle": index} for index in range(max_cycles)],
        bearings=[
            {"name": name, "active": name in normal_names}
            for name in sorted(CONTACT_NAMES)
        ],
        axial_tension=[
            {"name": name, "active": name in axial_names} for name in sorted(BOLT_NAMES)
        ],
    )
    report.update(changes)
    return report


def test_same_case_continuation_reuses_only_unilateral_memberships(
    tmp_path, monkeypatch, isolated_runner
):
    max_cycles = 2
    calls = []
    active_normals = {"pb02-contact-1", "pb02-contact-7"}
    active_axials = {"pb02-bolt-2"}
    rejected = _exhausted(
        "a12-forward",
        max_cycles,
        normal_names=active_normals,
        axial_names=active_axials,
        physical_connection_forces={"ALTERED_REJECTED_FORCE": 9.9e99},
    )
    reports = [
        _report("a12-forward", contact_active_set_converged=False),
        rejected,
        _report("a12-forward"),
        *map(_report, runner.CASE_ORDER[1:]),
    ]
    _install_fake_native_run(monkeypatch, reports, calls)

    summary = _run(tmp_path, max_cycles=max_cycles, max_same_case_continuations=1)

    continuation = calls[2]
    assert continuation["case"] == "a12-forward"
    assert continuation["seed"] == sorted(active_normals)
    assert continuation["axial_seed"] == sorted(active_axials)
    assert continuation["path"].name.endswith("same-case-continuation-01")
    assert "ALTERED_REJECTED_FORCE" not in json.dumps(summary)
    assert summary["attempts"][2]["same_case_continuation_from_attempt"] == (
        "02-one-at-a-time-unseeded"
    )


def test_same_case_continuation_never_reuses_a_different_case_checkpoint(
    tmp_path, monkeypatch, isolated_runner
):
    max_cycles = 2
    calls = []
    wrong_case = _exhausted("a12-rear", max_cycles)
    reports = [
        _report("a12-forward", contact_active_set_converged=False),
        wrong_case,
    ]
    _install_fake_native_run(monkeypatch, reports, calls)

    with pytest.raises(ValueError, match="checkpoint load identity changed"):
        _run(tmp_path, max_cycles=max_cycles, max_same_case_continuations=1)

    assert len(calls) == 2


def test_same_case_continuations_have_a_strict_configured_bound(
    tmp_path, monkeypatch, isolated_runner
):
    max_cycles = 2
    calls = []
    reports = [
        _report("a12-forward", contact_active_set_converged=False),
        _exhausted("a12-forward", max_cycles),
        _exhausted("a12-forward", max_cycles),
        _report("a12-rear"),
        _report("a12-forward"),
        *map(_report, runner.CASE_ORDER[2:]),
    ]
    _install_fake_native_run(monkeypatch, reports, calls)

    summary = _run(tmp_path, max_cycles=max_cycles, max_same_case_continuations=1)

    forward_calls = [call for call in calls if call["case"] == "a12-forward"]
    assert len(forward_calls) == 4
    assert (
        sum("same-case-continuation" in call["path"].name for call in forward_calls)
        == 1
    )
    assert summary["max_same_case_continuations"] == 1


@pytest.mark.parametrize("value", [-1, 1.5, True])
def test_same_case_continuation_bound_must_be_a_nonnegative_integer(
    tmp_path, isolated_runner, value
):
    with pytest.raises(ValueError, match="nonnegative integer"):
        _run(tmp_path, max_same_case_continuations=value)


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
    assert result["contact_model"]["partition_fingerprint"] == (
        NATIVE_PARTITION["fingerprint"]
    )
    assert (
        result["contact_model"]["contact_row_count"]
        == (NATIVE_PARTITION["contact_row_count"])
    )
    assert result["contact_model"]["canonical_per_area_n_per_mm3"] > 0


def test_stiffness_selection_exposes_four_by_four_native_partition():
    result = runner._selected_stiffnesses(
        AXIAL_STIFFNESS,
        LATERAL_STIFFNESS,
        FACE_STIFFNESS,
        contact_grid_resolution=4,
    )

    assert result["contact_model"]["grid_resolution"] == [4, 4]
    assert result["contact_model"]["partition_fingerprint"] != (
        NATIVE_PARTITION["fingerprint"]
    )
    assert result["contact_model"]["contact_row_count"] > (
        NATIVE_PARTITION["contact_row_count"]
    )


def test_model_stiffness_verifier_authenticates_generated_contact_partition(tmp_path):
    stiffnesses = runner._selected_stiffnesses(
        AXIAL_STIFFNESS, LATERAL_STIFFNESS, FACE_STIFFNESS
    )
    model = runner.prepare_case(
        "a12-forward",
        bolt_axial_n_per_mm=AXIAL_STIFFNESS,
        bolt_lateral_n_per_mm=LATERAL_STIFFNESS,
        face_normal_total_n_per_mm=FACE_STIFFNESS,
    )
    path = tmp_path / "model"
    path.mkdir()
    with (path / "model.pkl").open("wb") as target:
        pickle.dump({"model": model}, target)

    assert runner._verify_model_stiffness(path, stiffnesses) == stiffnesses

    model[1]["pb02_contact_stiffness"]["partition_fingerprint"] = "changed"
    with (path / "model.pkl").open("wb") as target:
        pickle.dump({"model": model}, target)
    with pytest.raises(ValueError, match="area-derived contact metadata"):
        runner._verify_model_stiffness(path, stiffnesses)


def test_contact_aggregation_records_refinement_comparison_fields():
    stiffnesses = runner._selected_stiffnesses(
        AXIAL_STIFFNESS, LATERAL_STIFFNESS, FACE_STIFFNESS
    )
    rows = [
        row
        for row in runner.native_row_inventory()
        if row["kind"] == "contact_compression"
    ]
    active = {rows[0]["name"], rows[-1]["name"]}
    report = {
        "bearings": [
            {"name": row["name"], "active": row["name"] in active} for row in rows
        ],
        "physical_connection_forces": {
            row["name"]: {
                "first": row["first_part"],
                "second": row["second_part"],
                "scalar_normal": [-value for value in row["direction"]],
                "contact_partition_fingerprint": NATIVE_PARTITION["fingerprint"],
                "contact_grid_resolution": NATIVE_PARTITION["grid_resolution"],
                "force_on_first_xyz_n": (
                    [-value for value in row["direction"]]
                    if row["name"] in active
                    else [0.0] * 3
                ),
            }
            for row in rows
        },
    }

    result = runner._contact_aggregation(report, stiffnesses)

    assert result["partition_fingerprint"] == NATIVE_PARTITION["fingerprint"]
    assert set(result["interfaces"]) == set(NATIVE_PARTITION["interfaces"])
    assert sum(
        row["active_tributary_area_mm2"] for row in result["interfaces"].values()
    ) == pytest.approx(
        sum(row["tributary_area_mm2"] for row in rows if row["name"] in active)
    )
    assert all(
        {
            "force_resultant_n",
            "moment_resultant_about_net_centroid_nmm",
            "active_tributary_area_mm2",
            "peak_average_cell_pressure_n_per_mm2",
        }
        <= set(row)
        for row in result["interfaces"].values()
    )

    missing = {
        **report,
        "physical_connection_forces": dict(report["physical_connection_forces"]),
    }
    missing["physical_connection_forces"].pop(rows[0]["name"])
    with pytest.raises(ValueError, match="missing canonical physical-force"):
        runner._contact_aggregation(missing, stiffnesses)

    reversed_report = {
        **report,
        "physical_connection_forces": {
            name: dict(force)
            for name, force in report["physical_connection_forces"].items()
        },
    }
    reversed_report["physical_connection_forces"][rows[0]["name"]][
        "force_on_first_xyz_n"
    ] = list(rows[0]["direction"])
    with pytest.raises(ValueError, match="force reversed"):
        runner._contact_aggregation(reversed_report, stiffnesses)


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
