"""Candidate authority stays separate, source-bound, dirty-aware, and unreleased."""

import copy
import json
from pathlib import Path

import pytest

from scripts import owner_barrel_candidate_contract as contract_source

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "barrel-nut-candidate.json"


@pytest.fixture(scope="module")
def contract():
    return json.loads(CONTRACT.read_text())


def test_contract_binds_candidate_geometry_station_register_and_sources(contract):
    contract_source.validate_contract(contract)
    checks = contract_source.check_contract(contract)
    assert checks["valid"]
    assert checks["worktree_currently_dirty"]
    assert contract["station_register"]["counts"] == contract_source.EXPECTED_COUNTS
    assert contract["station_register"]["units"] == contract_source.EXPECTED_UNITS
    assert contract["counts"] == contract["station_register"]["counts"]
    assert contract["units"] == contract["station_register"]["units"]
    assert len(contract["geometry"]["fingerprint_sha256"]) == 64


def test_contract_does_not_replace_selected_candidate_or_claim_release(contract):
    assert contract["candidate"] == "compact-floor-flush-bolted-development"
    assert contract["authority"]["selected_candidate"] == (
        "compact-floor-flush-development"
    )
    assert contract["authority"]["replaces_selected_authority"] is False
    assert contract["release"] is False
    assert not any(contract["release_flags"].values())


def test_contract_reports_uncommitted_repository_state(contract):
    state = contract["repository_state"]
    assert state["worktree_clean_at_generation"] is False
    assert state["uncommitted_changes_present_at_generation"] is True
    assert state["porcelain_entries_at_generation"]
    assert len(state["dirty_snapshot_sha256"]) == 64
    assert "does not claim a clean or frozen" in state["status_policy"]


def test_contract_rejects_count_or_release_drift(contract):
    changed = copy.deepcopy(contract)
    changed["station_register"]["counts"]["barrel_pairs"] = 45
    with pytest.raises(ValueError, match="counts changed"):
        contract_source.validate_contract(changed)

    changed = copy.deepcopy(contract)
    changed["station_register"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source/data binding changed"):
        contract_source.validate_contract(changed)

    changed = copy.deepcopy(contract)
    changed["units"]["force"] = "lbf"
    with pytest.raises(ValueError, match="units changed"):
        contract_source.validate_contract(changed)

    changed = copy.deepcopy(contract)
    changed["release_flags"]["diy_ready"] = True
    with pytest.raises(ValueError, match="remain unreleased"):
        contract_source.validate_contract(changed)
