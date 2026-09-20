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
    assert by_id["LB-04"]["depends_on"] == ["PB-02"]
    assert by_id["PB-00"]["status"] == "complete"
    assert by_id["PB-01"]["status"] in {"planned", "in_progress"}
    assert by_id["PB-02"]["status"] in {"planned", "in_progress"}
    assert by_id["LB-03A"]["status"] == "superseded_for_new_architecture"
    assert by_id["LB-03B"]["status"] == "superseded_for_new_architecture"
    assert by_id["LB-03C"]["status"] == "superseded_for_new_architecture"


def test_audit_lists_all_current_structural_stations() -> None:
    audit = json.loads((ROOT / "docs/bolted-candidate-baseline-audit.json").read_text())
    names = audit["inventory"]["structural_station_names"]
    assert audit["inventory"]["structural_stations"] == len(names) == 24
    assert len(names) == len(set(names))


def test_g1_records_exact_a66_information_gate_without_selecting_it() -> None:
    decision = json.loads((ROOT / "docs/bolted-candidate-g1-decision.json").read_text())
    request = decision["a66_manufacturer_information_gate"]
    assert decision["gate"] == "G1"
    assert decision["g1_resume_decision"]["drilling_released"] is False
    assert request["external_contact_authorized"] is False
    assert request["minimum_wood_thickness_in_question"] == 1.5
    assert request["dimensioned_bolt_hole_centers_required"] is True
    assert request["applicable_bolt_mode_resistance_required"] is True
    assert (
        request["if_unavailable"]
        == "A66 cannot advance to representative drilling or G1 selection"
    )


def test_v4_timbers_are_active_without_releasing_g1() -> None:
    owner = json.loads((ROOT / "docs/bolted-candidate-owner-inputs.json").read_text())
    decision = json.loads((ROOT / "docs/bolted-candidate-g1-decision.json").read_text())
    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    by_id = {task["id"]: task for task in ledger["tasks"]}
    assert owner["manufacturer_contact"]["authorized"] is False
    assert (
        decision["active_scope_reference"]
        == "docs/bolted-candidate-simple-joints-v4.md"
    )
    assert "PB-01" in ledger["active_focus"]
    assert "PB-02" in ledger["active_focus"]
    assert decision["g1_resume_decision"]["route"] != (
        "published_bolted_timber_HL_installation_plus_checked_unlisted_actions"
    )
    assert by_id["LB-04"]["status"] == "incomplete"
    assert by_id["LB-13"]["status"] == "blocked"
    assert decision["g1_resume_decision"]["drilling_released"] is False
    center = decision["br904_fixed_center_pose_screen"]
    assert center["half_inch_nominal_hole_play_ray_filter_cleared"] is False
    assert center["seven_sixteenths_nominal_nds_hole_range_cleared"] is False
    assert center["product_rejected"] is False


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
    assert contingency["owner_explicitly_excluded"] is True
    assert contingency["connector_selected"] is False
    assert contingency["fabrication_release"] is False


def test_owner_v4_scope_excludes_custom_steel_and_half_laps() -> None:
    owner = json.loads((ROOT / "docs/bolted-candidate-owner-inputs.json").read_text())
    decision = json.loads((ROOT / "docs/bolted-candidate-g1-decision.json").read_text())
    scope = owner["connector_scope"]
    assert scope["prefabricated_brackets_required"] is False
    assert scope["full_section_face_overlaps_allowed"] is True
    assert scope["solid_timber_corner_cleats_allowed_for_development"] is True
    assert scope["half_lap_or_housed_joinery_allowed"] is False
    assert scope["ordinary_cut_and_drilled_a36_stock_allowed"] is False
    assert scope["custom_fabricated_steel_allowed"] is False
    assert scope["routine_structural_wood_thread_removal_allowed"] is False
    assert owner["manufacturer_contact"]["authorized"] is False
    assert owner["fabrication_release"] is False
    assert (
        decision["owner_connector_scope"]["custom_cut_and_drilled_steel_allowed"]
        is False
    )
    assert "custom fabricated steel" in decision["explicitly_excluded_by_owner"]


def test_v4_ledger_dependencies_supersede_hardware_first_critical_path() -> None:
    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    by_id = {task["id"]: task for task in ledger["tasks"]}
    for stage in range(1, 7):
        assert by_id[f"PB-{stage:02d}"]["depends_on"] == [f"PB-{stage - 1:02d}"]
    assert by_id["LB-04"]["depends_on"] == ["PB-02"]
    assert by_id["LB-13"]["status"] == "blocked"
    assert all(
        by_id[stage]["status"].startswith("superseded")
        for stage in (
            "HF-00",
            "HF-01",
            "HF-02A",
            "HF-02B",
            "HF-03",
            "HF-04",
            "HF-05",
            "HF-06",
            "HF-07",
            "HF-08",
        )
    )


def test_v4_scope_preserves_selected_authority_and_panel_screw_count() -> None:
    owner = json.loads((ROOT / "docs/bolted-candidate-owner-inputs.json").read_text())
    ledger = json.loads((ROOT / "docs/bolted-candidate-task-ledger.json").read_text())
    audit = json.loads((ROOT / "docs/bolted-candidate-baseline-audit.json").read_text())
    assert ledger["baseline_commit"] == "7cdd2e37ed2d364b47879a960b9eb15b93c67048"
    assert audit["selected_authority"] == "compact-floor-flush-development"
    assert audit["inventory"]["panel_screws"] == 48
    assert audit["inventory"]["kicker_screws"] == 18
    assert audit["inventory"]["panel_and_kicker_screws"] == 66
    assert audit["scope"]["selected_candidate_promoted"] is False
    assert audit["scope"]["structural_move_wood_thread_removals_target"] == 0
    assert owner["physical_width_packet"]["option"] == "kerf-right"


def test_owner_post_only_shift_screen_remains_a_g1_prototype() -> None:
    decision = json.loads((ROOT / "docs/bolted-candidate-g1-decision.json").read_text())
    screen = json.loads(
        (ROOT / decision["owner_post_only_center_shift_screen"]["record"]).read_text()
    )
    assert screen["selected_offset_mm"] is None
    assert screen["drilling_released"] is False
    assert (
        screen["common_geometry_findings"]["top_principals_and_panel_screw_axes_moved"]
        is False
    )
    assert (
        screen["common_geometry_findings"]["kicker_edge_support_adequacy_verified"]
        is False
    )
