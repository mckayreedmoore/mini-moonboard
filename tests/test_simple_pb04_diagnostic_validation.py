"""PB04 diagnostic identity and no-release gates are source bound."""

import copy

import pytest

from scripts import simple_pb04_diagnostic_run as runner


def _accepted_report(contract, case="a12-forward"):
    hold, horizontal = runner.EXPECTED_LOADS[case]
    inventory = contract["topology_inventory"]
    return {
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
        "angle_stations": [f"legacy-{index}" for index in range(14)],
        "axial_tension_names": inventory["tension_only_bolt_names"],
        "physical_connection_forces": {
            name: {"force_on_first_xyz_n": [1.0, 0.0, 0.0]}
            for name in inventory["required_physical_names"]
        },
        "member_section_demands": {
            name: {"member": {"name": name}} for name in inventory["block_member_names"]
        },
        "pb04_diagnostic_identity": contract["deterministic_input_fingerprint"],
        "pb04_mechanics_identity": contract["mechanics_identity"],
        "pb04_model_identity": "f" * 64,
        "source_sha256": contract["producer_source_sha256"],
        "artifact_sha256": {"model.pkl": "f" * 64},
        "qualified_for_design": False,
        "acceptance": False,
        "drilling_released": False,
        "fabrication_released": False,
    }


@pytest.fixture(scope="module")
def contract():
    return runner._preflight(runner._selected_stiffnesses(700, 1200, 2400, 10000))


def test_preflight_binds_pb04_sources_topology_and_no_release(contract):
    inventory = contract["topology_inventory"]

    assert contract["candidate"] == runner.CANDIDATE_ID
    assert contract["schema"] == "simple_pb04_eight_station_diagnostic_run/v1"
    assert contract["mechanics_identity"]["pb04_source_id"] == runner.CANDIDATE_ID
    assert inventory["pb04_tension_only_bolt_count"] == 32
    assert inventory["pb04_contact_cell_count"] == 64
    assert inventory["block_member_count"] == 8
    assert contract["qualified_for_design"] is False
    assert contract["drilling_released"] is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda report: report.update(candidate="wrong"), "candidate"),
        (lambda report: report["axial_tension_names"].pop(), "tension-only"),
        (
            lambda report: report["physical_connection_forces"].popitem(),
            "physical-force",
        ),
        (lambda report: report.update(pb04_model_identity="bad"), "model artifact"),
        (lambda report: report.update(drilling_released=True), "release"),
    ],
)
def test_validation_rejects_identity_force_and_release_drift(
    contract, mutation, message
):
    report = copy.deepcopy(_accepted_report(contract))
    mutation(report)

    with pytest.raises(ValueError, match=message):
        runner._validate_accepted_report(report, "a12-forward", contract)


def test_validation_accepts_complete_pb04_report(contract):
    report = _accepted_report(contract)
    assert runner._validate_accepted_report(report, "a12-forward", contract) is report


def test_unsolved_preparation_has_pb04_identity_and_no_release():
    structure, metadata = runner.prepare_unsolved_case(
        "a12-forward", runner._selected_stiffnesses(700, 1200, 2400, 10000)
    )

    assert metadata["pb04_candidate"] == runner.CANDIDATE_ID
    assert "pb03_candidate" not in metadata
    assert metadata["pb04_native_row_counts"]["bolt_tension_only"] == 32
    assert len(metadata["legacy_proxy_stations"]) == 14
    assert metadata["solved"] is False
    assert metadata["qualified_for_design"] is False
    assert metadata["drilling_released"] is False
    assert len(structure.members) > 8
