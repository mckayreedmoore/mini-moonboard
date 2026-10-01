from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts import build_current_timber_cut_yield_scenario_attempt01 as cut_yield


def test_current_revision_24_ids_classes_and_ripped_grade_gate_are_bound() -> None:
    report = cut_yield.build_report()

    assert report["candidate"] == "compact-floor-flush-wood-joints-development"
    assert report["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1"
    assert report["selected_candidate_authority_preserved"] == "compact-floor-flush-development"
    assert report["inventory_reconciliation"]["count"] == 24
    assert report["inventory_reconciliation"]["by_stock_class"] == {
        "4x4": 18,
        "4x6": 4,
        "2x6": 2,
    }
    assert report["inventory_reconciliation"]["exact_ids_match_attempt04_manifest"] is True
    assert report["inventory_reconciliation"]["ripped_4x6_part_ids"] == sorted(
        cut_yield.RIPPED_4X6_IDS
    )
    assert all(not blank["grade_assigned"] for row in report["scenarios"] for blank in row["proposed_blanks"])
    ripped = {
        blank["part_id"]: blank["post_rip_grade_status"]
        for row in report["scenarios"]
        for blank in row["proposed_blanks"]
        if blank["part_id"] in cut_yield.RIPPED_4X6_IDS
    }
    assert set(ripped) == cut_yield.RIPPED_4X6_IDS
    assert set(ripped.values()) == {"unresolved_after_cross_section_remanufacture"}


def test_length_scenarios_preserve_source_condition_and_section_boundaries() -> None:
    report = cut_yield.build_report()

    assert report["scenario_result_count"] == 30
    assert report["packing_policy"]["cross_section_mixing"] is False
    assert report["packing_policy"]["shared_unsawn_4x6_stock_before_ripping"] is False
    assert report["packing_policy"]["optimization_claim"] is False
    two_by_six = [
        row for row in report["scenarios"] if row["stock_class"] == "2x6"
    ]
    assert {
        (row["published_stock_length_ft"], row["stock_source_descriptor"])
        for row in two_by_six
    } == {
        (8.0, "2x6x8 #2 Prime Douglas Fir, kiln-dried; actual 1.5 x 5.5 in"),
        (16.0, "2x6x16 #2 Better Douglas Fir, green; actual 1.562 x 5.625 in"),
    }
    for row in report["scenarios"]:
        for arithmetic_bin in row["packing"]["bins"]:
            assert arithmetic_bin["stock_classes"] == [row["stock_class"]]
            assert arithmetic_bin["blank_sections_mm"] == [row["proposed_blank_cross_section_mm"]]
            assert set(arithmetic_bin["part_ids"]).issubset(
                {blank["part_id"] for blank in row["proposed_blanks"]}
            )


def test_eight_foot_four_by_four_scenario_reproduces_explicit_cut_arithmetic() -> None:
    report = cut_yield.build_report()
    row = next(
        scenario
        for scenario in report["scenarios"]
        if scenario["stock_class"] == "4x4"
        and scenario["published_stock_length_ft"] == 8
        and scenario["kerf_mm"] == 3.2
        and scenario["end_trim_per_arithmetic_bin_mm"] == 25.4
    )

    assert row["blank_count"] == 18
    assert row["proposed_blank_length_total_mm"] == pytest.approx(2140.2)
    assert row["packing"]["arithmetic_bin_count"] == 1
    arithmetic_bin = row["packing"]["bins"][0]
    assert arithmetic_bin["used_cut_length_mm"] == pytest.approx(2197.8)
    assert arithmetic_bin["end_trim_mm"] == pytest.approx(25.4)
    assert arithmetic_bin["remaining_length_mm"] == pytest.approx(215.2)
    assert row["packing"]["not_a_purchase_quantity"] is True


def test_first_fit_decreasing_respects_kerf_trim_and_rejects_an_oversized_blank() -> None:
    blanks = [
        {"part_id": "a", "pattern_group": "p", "proposed_blank_length_mm": 40.0,
         "stock_class": "4x4", "proposed_blank_cross_section_mm": [88.9, 88.9]},
        {"part_id": "b", "pattern_group": "p", "proposed_blank_length_mm": 40.0,
         "stock_class": "4x4", "proposed_blank_cross_section_mm": [88.9, 88.9]},
    ]
    packed = cut_yield.pack_arithmetic_group(blanks, 99.0, 5.0, 10.0)
    assert packed["arithmetic_bin_count"] == 2
    assert all(row["remaining_length_mm"] == pytest.approx(44.0) for row in packed["bins"])

    too_short = cut_yield.pack_arithmetic_group(blanks[:1], 44.0, 5.0, 0.0)
    assert too_short["status"] == "arithmetic_infeasible_for_length"
    assert too_short["unfitted_part_ids"] == ["a"]
    assert too_short["arithmetic_bin_count"] == 0


def test_source_hash_drift_fails_closed(tmp_path: Path) -> None:
    root = tmp_path
    packet = root / cut_yield.PACKET_REL
    packet.mkdir(parents=True)
    shutil.copy2(cut_yield.ROOT / cut_yield.PACKET_REL / "source-pins.json", packet)
    shutil.copy2(cut_yield.ROOT / cut_yield.PACKET_REL / "scenario-inputs.json", packet)
    pins = json.loads((packet / "source-pins.json").read_text())
    for source in pins["sources"]:
        destination = root / source["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cut_yield.ROOT / source["path"], destination)
    drifted = root / pins["sources"][0]["path"]
    drifted.write_bytes(drifted.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="source hash drift"):
        cut_yield.build_report(root)


def test_claim_boundary_keeps_cost_fit_receiving_and_release_false() -> None:
    boundary = cut_yield.build_report()["claim_boundary"]
    assert boundary["arithmetic_scenarios_only"] is True
    assert boundary["purchase_quantity_established"] is False
    assert boundary["product_selected"] is False
    assert boundary["price_or_cost_established"] is False
    assert boundary["material_identity_or_grade_accepted"] is False
    assert boundary["physical_fit_established"] is False
    assert boundary["physical_cutting_authorized"] is False
    assert boundary["candidate_or_climbing_release"] is False
