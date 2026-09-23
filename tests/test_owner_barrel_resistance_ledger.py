"""Fail-closed coverage tests for barrel-joint resistance ledger."""

import copy
import json
from pathlib import Path

import pytest

from scripts import owner_barrel_resistance_ledger as resistance
from scripts.owner_barrel_native_connector_inventory import build_inventory

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs/barrel-nut-resistance-ledger.json"


@pytest.fixture(scope="module")
def inventory():
    return build_inventory()


@pytest.fixture(scope="module")
def ledger():
    return json.loads(LEDGER_PATH.read_text())


def test_resistance_ledger_covers_every_duty_fastener_mode_and_case(
    ledger, inventory
):
    resistance.validate_ledger(ledger, inventory=inventory)
    assert len(ledger["stations"]) == 24
    assert len(ledger["fasteners"]) == 46
    assert set(ledger["mode_registry"]) == set(resistance.ALL_MODES)
    assert set(ledger["blocker_registry"]) == set(resistance.BLOCKERS)
    assert {
        row["category"] for row in ledger["mode_registry"].values()
    } == {"steel", "thread", "wood", "contact", "group"}
    assert ledger["summary"]["fastener_assessment_count"] == 46 * len(
        resistance.FASTENER_MODES
    )
    assert ledger["summary"]["station_assessment_count"] == 24 * len(
        resistance.STATION_MODES
    )
    assert ledger["summary"]["case_result_count"] == (
        46 * len(resistance.FASTENER_MODES)
        + 24 * len(resistance.STATION_MODES)
    ) * 6


def test_missing_controlled_inputs_never_become_pass(ledger):
    for row in ledger["fasteners"].values():
        for assessment in row["assessments"].values():
            assert assessment["applicable"] is True
            assert assessment["status"] == "UNRESOLVED"
            assert any(not value for value in assessment["evidence_state"].values())
            for result in assessment["case_results"].values():
                assert result["status"] == "UNRESOLVED"
                assert result["demand"] is None
                assert result["resistance"] is None
                assert result["utilization"] is None
                assert result["blocker_codes"]


def test_station_modes_are_unresolved_except_explicit_kicker_nonapplicability(ledger):
    kicker_applicable = set()
    for name, row in ledger["stations"].items():
        for mode, assessment in row["assessments"].items():
            if mode == "bn_kicker_backing_transfer" and row["family"] != "header_center":
                assert assessment["status"] == "NOT_APPLICABLE"
                assert all(
                    result["status"] == "NOT_APPLICABLE"
                    for result in assessment["case_results"].values()
                )
            else:
                assert assessment["status"] == "UNRESOLVED"
                assert all(
                    result["status"] == "UNRESOLVED"
                    for result in assessment["case_results"].values()
                )
            if mode == "bn_kicker_backing_transfer" and assessment["applicable"]:
                kicker_applicable.add(name)
    assert kicker_applicable == {
        "clip_split_header_center_left",
        "clip_split_header_center_right",
    }


def test_checker_rejects_pass_when_controlled_property_is_missing(ledger, inventory):
    changed = copy.deepcopy(ledger)
    assessment = next(iter(changed["fasteners"].values()))["assessments"][
        "bn_bolt_steel_interaction"
    ]
    assessment["status"] = "PASS"
    result = assessment["case_results"][resistance.CASES[0]]
    result.update(
        status="PASS",
        demand=1.0,
        demand_units="N",
        resistance=2.0,
        resistance_basis="invented",
        utilization=0.5,
        blocker_codes=[],
    )
    with pytest.raises(ValueError, match="Missing controlled properties"):
        resistance.validate_ledger(changed, inventory=inventory)


def test_checker_rejects_falsified_evidence_state(ledger, inventory):
    changed = copy.deepcopy(ledger)
    assessment = next(iter(changed["fasteners"].values()))["assessments"][
        "bn_bolt_steel_interaction"
    ]
    assessment["evidence_state"] = {
        field: True for field in assessment["evidence_state"]
    }
    with pytest.raises(ValueError, match="evidence state differs"):
        resistance.validate_ledger(changed, inventory=inventory)


def test_checker_rejects_missing_fastener_or_mode(ledger, inventory):
    changed = copy.deepcopy(ledger)
    changed["fasteners"].pop(next(iter(changed["fasteners"])))
    with pytest.raises(ValueError, match="all 46 fasteners"):
        resistance.validate_ledger(changed, inventory=inventory)

    changed = copy.deepcopy(ledger)
    first = next(iter(changed["stations"].values()))
    first["assessments"].pop("bn_contact_pressure_and_opening")
    with pytest.raises(ValueError, match="station-mode coverage"):
        resistance.validate_ledger(changed, inventory=inventory)


def test_checked_artifact_is_reproducible(ledger, inventory):
    rebuilt = resistance.build_ledger(inventory=inventory)
    assert LEDGER_PATH.read_text() == resistance.render(rebuilt)


def test_release_boundary_stays_closed(ledger):
    assert ledger["summary"]["status"] == "UNRESOLVED"
    assert ledger["summary"]["pass_count"] == 0
    assert ledger["structural_release"] is False
    assert ledger["diy_ready"] is False
