"""Validate the handoff dispatch ledger without running dependent work."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_ledger_has_unique_ids_and_resolvable_dependencies() -> None:
    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    tasks = ledger["tasks"]
    ids = [task["id"] for task in tasks]
    assert len(ids) == len(set(ids))
    known = set(ids)
    assert all(dep in known for task in tasks for dep in task["depends_on"])


def test_g1_selects_a_prototype_and_keeps_mechanics_and_solve_gates_open() -> None:
    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    by_id = {task["id"]: task for task in ledger["tasks"]}
    assert by_id["LB-04"]["status"] == "complete"
    assert by_id["LB-04"]["gate"] == "G1"
    assert by_id["LB-05"]["status"] == "complete"
    assert all(by_id[name]["status"] == "planned" for name in ("LB-13", "LB-17"))


def test_audit_lists_all_current_structural_stations() -> None:
    audit = json.loads((ROOT / "docs/bolted-candidate-baseline-audit.json").read_text())
    names = audit["inventory"]["structural_station_names"]
    assert audit["inventory"]["structural_stations"] == len(names) == 24
    assert len(names) == len(set(names))
