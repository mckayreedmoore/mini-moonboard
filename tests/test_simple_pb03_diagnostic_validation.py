"""PB03 diagnostic identity and solved-report gates are source bound."""

import copy

import pytest

from scripts import simple_pb03_diagnostic_run as runner
from scripts.simple_pb03_native import BLOCK_NAMES


def _physical(force=(1.0, 0.0, 0.0)):
    return {"force_on_first_xyz_n": list(force)}


def _accepted_report(contract, case="a12-forward"):
    hold, horizontal = runner.EXPECTED_LOADS[case]
    inventory = contract["topology_inventory"]
    physical = {name: _physical() for name in inventory["required_physical_names"]}
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
        "physical_connection_forces": physical,
        "member_section_demands": {
            name: {"member": {"name": name}} for name in BLOCK_NAMES.values()
        },
        "pb03_diagnostic_identity": contract["deterministic_input_fingerprint"],
        "pb03_mechanics_identity": contract["mechanics_identity"],
        "pb03_model_identity": "f" * 64,
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


def test_preflight_binds_exact_eight_station_inventory(contract):
    inventory = contract["topology_inventory"]

    assert contract["candidate"] == runner.CANDIDATE_ID
    assert contract["mechanics_identity"]["legacy_proxy_stations"] == 14
    assert inventory["pb03_tension_only_bolt_count"] == 32
    assert inventory["pb02_tension_only_bolt_count"] == 10
    assert inventory["pb03_contact_cell_count"] == 64
    assert inventory["block_member_count"] == 8
    assert contract["qualified_for_design"] is False
    assert contract["drilling_released"] is False


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda report: report.update(candidate="wrong"), "candidate"),
        (
            lambda report: report.update(angle_stations=report["angle_stations"][:-1]),
            "legacy",
        ),
        (
            lambda report: report["axial_tension_names"].pop(),
            "tension-only",
        ),
        (
            lambda report: report["physical_connection_forces"].popitem(),
            "physical-force",
        ),
        (
            lambda report: report["member_section_demands"].popitem(),
            "block",
        ),
        (lambda report: report.update(pb03_model_identity="bad"), "model artifact"),
        (lambda report: report.update(drilling_released=True), "release"),
    ],
)
def test_validation_rejects_identity_topology_force_and_release_drift(
    contract, mutation, message
):
    report = copy.deepcopy(_accepted_report(contract))
    mutation(report)

    with pytest.raises(ValueError, match=message):
        runner._validate_accepted_report(report, "a12-forward", contract)


def test_validation_accepts_complete_source_bound_report(contract):
    report = _accepted_report(contract)

    assert runner._validate_accepted_report(report, "a12-forward", contract) is report


def test_unsolved_preparation_has_combined_pb02_pb03_mechanics():
    structure, metadata = runner.prepare_unsolved_case(
        "a12-forward",
        runner._selected_stiffnesses(700, 1200, 2400, 10000),
    )

    assert metadata["pb03_candidate"] == runner.CANDIDATE_ID
    assert metadata["pb03_native_row_counts"] == {
        "existing_bolt_axes": 32,
        "bolt_tension_only": 32,
        "existing_bolt_lateral": 64,
        "contact_compression_cells": 64,
    }
    assert len(metadata["legacy_proxy_stations"]) == 14
    assert len(metadata["pb03_mechanics_identity"]["row_fingerprint_sha256"]) == 64
    assert set(BLOCK_NAMES.values()) <= set(structure.members)
    assert metadata["solved"] is False
    assert metadata["drilling_released"] is False
