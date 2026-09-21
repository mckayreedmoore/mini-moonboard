"""PB06 diagnostic accepts only its own ten-station source and no-release state."""

import copy

import pytest

from scripts import simple_pb06_diagnostic_run as runner


@pytest.fixture(scope="module")
def contract():
    return runner._preflight(runner._selected_stiffnesses(700, 1200, 2400, 10000))


def _accepted_report(contract):
    hold, horizontal = runner.EXPECTED_LOADS["a12-forward"]
    inventory = contract["topology_inventory"]
    return {
        "candidate": runner.CANDIDATE_ID,
        "parameters": {
            "hold": hold,
            "pounds": 250.0,
            "force_xyz_n": [*horizontal, runner.EXPECTED_VERTICAL_FORCE_N],
        },
        **{
            name: True
            for name in (
                "contact_active_set_converged",
                "axial_tension_active_set_converged",
                "closed_bearing_assumption_passed",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
                "mpc_check_passed",
                "numerically_accepted",
            )
        },
        "angle_stations": [f"legacy-{index}" for index in range(12)],
        "axial_tension_names": inventory["tension_only_bolt_names"],
        "physical_connection_forces": {
            name: {"force_on_first_xyz_n": [1.0, 0.0, 0.0]}
            for name in inventory["required_physical_names"]
        },
        "member_section_demands": {
            name: {} for name in inventory["block_member_names"]
        },
        "pb06_diagnostic_identity": contract["deterministic_input_fingerprint"],
        "pb06_mechanics_identity": contract["mechanics_identity"],
        "pb06_model_identity": "f" * 64,
        "source_sha256": runner._native_source_inventory(),
        "artifact_sha256": {"model.pkl": "f" * 64},
        **{
            flag: False
            for flag in (
                "qualified_for_design",
                "acceptance",
                "drilling_released",
                "fabrication_released",
                "structural_released",
            )
        },
    }


def test_preflight_is_pb06_only(contract):
    inventory = contract["topology_inventory"]
    assert contract["candidate"] == "pb06-upper-center-native-v1"
    assert contract["schema"] == "simple_pb06_ten_station_diagnostic_run/v1"
    assert inventory["legacy_station_count"] == 12
    assert inventory["legacy_sds_axis_count"] == 72
    assert inventory["fixed_panel_kicker_axis_count"] == 66
    assert inventory["original_frame_bolt_axis_count"] == 12
    assert inventory["pb06_tension_only_bolt_count"] == 40
    assert inventory["pb06_contact_cell_count"] == 80
    assert inventory["block_member_count"] == 10
    assert contract["qualified_for_design"] is False
    assert contract["drilling_released"] is False
    assert any(
        path.name == "simple_pb06_upper_center_native.py"
        for path in runner.PRODUCER_PATHS
    )
    assert any(
        path.name == "simple_pb06_upper_center_mechanics.py"
        for path in runner.PRODUCER_PATHS
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda report: report.update(candidate="pb05-narrow-outer-native-v1"),
            "candidate",
        ),
        (lambda report: report["angle_stations"].pop(), "legacy station"),
        (lambda report: report["axial_tension_names"].pop(), "tension-only"),
        (
            lambda report: report["physical_connection_forces"].popitem(),
            "physical-force",
        ),
        (lambda report: report.update(pb06_model_identity="bad"), "model artifact"),
        (lambda report: report.update(source_sha256={}), "producer source"),
        (lambda report: report.update(drilling_released=True), "release"),
    ],
)
def test_report_rejects_mismatches(contract, mutation, message):
    report = copy.deepcopy(_accepted_report(contract))
    mutation(report)
    with pytest.raises(ValueError, match=message):
        runner._validate_accepted_report(report, "a12-forward", contract)


def test_report_requires_pb06_fingerprint(contract):
    report = _accepted_report(contract)
    assert runner._validate_accepted_report(report, "a12-forward", contract) is report
    report["pb06_mechanics_identity"] = {"pb05_source_id": "wrong"}
    with pytest.raises(ValueError, match="mechanics fingerprint"):
        runner._validate_accepted_report(report, "a12-forward", contract)


def test_attempt_binds_native_pb06_without_solving(tmp_path, monkeypatch):
    calls = []

    def fake_run(path, **kwargs):
        calls.append(kwargs)
        return {"artifact_sha256": {}, "qualified_for_design": False}

    monkeypatch.setattr(runner.native, "run", fake_run)
    monkeypatch.setattr(runner, "_model_identity", lambda *_: "f" * 64)
    report = runner._run_attempt(
        "a12-forward",
        tmp_path,
        strategy="all",
        contract={
            "deterministic_input_fingerprint": "input",
            "mechanics_identity": {},
            "stiffness_selection": {},
        },
        max_cycles=3,
    )
    assert len(calls) == 1
    assert isinstance(calls[0]["module"], runner.PB06DiagnosticNative)
    assert calls[0]["expected_candidate"] == runner.CANDIDATE_ID
    assert set(calls[0]["extra_source_paths"]) == set(runner.PRODUCER_PATHS)
    assert report["pb06_model_identity"] == "f" * 64
    assert report["structural_released"] is False


def test_run_path_is_first_case_only(tmp_path):
    with pytest.raises(ValueError, match="A12-forward only"):
        runner.run_suite(tmp_path / "unused", cases=runner.CASE_ORDER)
    assert not (tmp_path / "unused").exists()
