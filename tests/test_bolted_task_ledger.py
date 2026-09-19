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


def test_g1_and_native_gates_remain_open_with_incomplete_physical_evidence() -> None:
    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    by_id = {task["id"]: task for task in ledger["tasks"]}
    assert by_id["LB-04"]["status"] == "incomplete"
    assert by_id["LB-04"]["gate"] == "G1"
    assert by_id["LB-05"]["status"] == "incomplete"
    assert all(by_id[f"LB-07{family}"]["status"] == "incomplete" for family in "ABCDEF")
    assert by_id["LB-12"]["status"] == "incomplete"
    assert by_id["LB-13"]["status"] == "blocked"
    assert by_id["LB-17"]["status"] == "planned"


def test_audit_lists_all_current_structural_stations() -> None:
    audit = json.loads((ROOT / "docs/bolted-candidate-baseline-audit.json").read_text())
    names = audit["inventory"]["structural_station_names"]
    assert audit["inventory"]["structural_stations"] == len(names) == 24
    assert len(names) == len(set(names))


def test_g1_records_exact_a66_information_gate_without_selecting_it() -> None:
    decision = json.loads((ROOT / "docs/bolted-candidate-g1-decision.json").read_text())
    request = decision["a66_manufacturer_information_gate"]
    assert decision["status"].endswith("G1_architecture_gate_open")
    assert request["external_contact_authorized"] is False
    assert request["minimum_wood_thickness_in_question"] == 1.5
    assert request["dimensioned_bolt_hole_centers_required"] is True
    assert request["applicable_bolt_mode_resistance_required"] is True
    assert request["if_unavailable"] == "A66 cannot advance to representative drilling or G1 selection"


def test_additional_retail_and_stock_leads_do_not_release_g1() -> None:
    decision = json.loads((ROOT / "docs/bolted-candidate-g1-decision.json").read_text())
    follow_up = json.loads((ROOT / decision["additional_retail_follow_up"]).read_text())
    contingency = json.loads(
        (ROOT / decision["ordinary_stock_scope_contingency"]["record"]).read_text()
    )
    assert {family["id"] for family in follow_up["families"]} == {
        "simpson-a88",
        "mitek-bl4-ubl4",
        "simpson-66t",
    }
    strap = next(row for row in follow_up["families"] if row["id"] == "simpson-66t")
    assert strap["uk_to_us_part_equivalence_verified"] is False
    assert strap["coplanar_mounting_face_at_each_required_station_verified"] is False
    assert follow_up["complete_joint_selected"] is False
    assert follow_up["fabrication_release"] is False
    assert contingency["owner_authorization_obtained"] is False
    assert contingency["connector_selected"] is False
    assert contingency["fabrication_release"] is False
