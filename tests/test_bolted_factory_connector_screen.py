import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_record(name: str) -> dict:
    return json.loads(
        (ROOT / "docs/bolted-candidate-prototypes" / name).read_text()
    )


def test_c1_screen_is_a_bounded_unresolved_factory_candidate() -> None:
    record = read_record("wurth-c1.json")

    assert record["status"] == "screened_for_joint_prototype"
    assert record["product"]["standard"] == "DIN EN 912:2011-09"
    assert record["applicability"]["softwood_wood_to_wood_listed"] is True
    assert record["applicability"]["through_bolt_and_nut_listed"] is True
    assert record["applicability"]["capacity_for_this_board"] == "unresolved; requires density, bolt grade, plate/washer stack, grain direction, edge/end distances, and combined-action check"
    assert "native solve" in " ".join(record["development_constraints"])


def test_a66_is_common_retail_and_explicitly_keeps_capacity_open() -> None:
    record = read_record("simpson-a66-retail.json")

    assert record["status"] == "common_retail_candidate_screened"
    assert record["applicability"]["specialty_purchase_required"] is False
    assert record["applicability"]["through_bolts_listed"] is True
    assert record["applicability"]["published_bolt_capacity"] is False
    assert "dashes for both allowable-load columns" in record["applicability"]["testing_and_rating_evidence"]
    assert "No dimensioned A66 factory bolt-hole layout" in record["applicability"]["testing_and_rating_evidence"]
    catalog = record["current_manufacturer_catalog_screen"]
    assert catalog["url"].endswith("C-C-2026.pdf?download=true")
    assert catalog["page"] == 314
    assert catalog["bolt_count_per_leg"] == 2
    assert catalog["f1_allowable_load_published"] is False
    assert catalog["f2_allowable_load_published"] is False
    assert catalog["bolt_hole_centers_dimensioned"] is False
    steel = record["steel_grade_transfer_screen"]
    assert steel["g90_is_coating_not_structural_grade"] is True
    assert steel["inspected_icc_table_28_lists_12_gauge_a33_and_a44_not_a66"] is True
    assert steel["a33_a44_grade33_strength_or_base_metal_thickness_transferable_to_a66"] is False
    assert steel["a66_guaranteed_fy_fu_and_base_metal_thickness_established"] is False
    drawing_search = record["current_manufacturer_drawing_search"]
    assert drawing_search["manufacturer_controlled_a66_coordinates_found"] is False
    assert drawing_search["third_party_model_usable_for_drilling"] is False
    qa = record["online_hole_measurement_lead"]
    assert qa["source_url"].startswith("https://www.lowes.com/questions/")
    assert qa["answer_author"] == "Simpson Strong-Tie"
    assert qa["stated_centers_from_edge_in"] == [2, 4, 6]
    assert qa["usable_as_bolt_drilling_layout"] is False
    assert "hole identity" in qa["limitation"]
    wall_test = record["independent_test_lead"]
    assert wall_test["source_url"].endswith("/papers/T6-11.pdf")
    assert wall_test["a66_named_in_tested_assembly"] is True
    assert wall_test["connector_only_capacity"] is False
    assert wall_test["usable_as_board_joint_rating"] is False
    assert record["product"]["lowes_url"].startswith("https://www.lowes.com/")
    assert record["product"]["home_depot_url"].startswith("https://www.homedepot.com/")


def test_initial_factory_matrix_keeps_applicability_and_action_limits_explicit() -> None:
    record = read_record("factory-bolted-alternatives.json")
    assert record["status"] == "complete_bounded_applicability_matrix"
    assert record["search_budget"]["distinct_families_screened"] == 3
    assert record["search_budget"]["catalog_exhaustion_claimed"] is False
    by_id = {item["id"]: item for item in record["alternatives"]}
    assert set(by_id) == {"existing-ml24z-through-bolt", "simpson-hl33-hl35", "simpson-ab90"}
    for item in by_id.values():
        assert item["receiver"]["thickness_mm"] == 38.1
        assert item.get("factory_hole_bolt_pattern") or item.get("models")
        assert item["orientation"]
        assert item["force_moment_coverage"]
        assert item["paired_use"]
        assert item["fabrication_implications"]
        assert item["unresolved_fields"]
    assert by_id["simpson-hl33-hl35"]["disposition"] == "rejected_for_preserved_single_2x6_receiver"
    assert by_id["simpson-ab90"]["disposition"] == "viable_for_bounded_geometry_prototype_only"


def test_hl_thickness_exclusion_applies_to_every_preserved_station() -> None:
    from mini_moonboard import compact_floor_flush_frame as baseline

    parts = {part.name: part for part in baseline.uncut_wood_parts()}
    stations = baseline.stations()
    assert len(stations) == 24
    thin = [station[0] for station in stations
            if any(min(parts[member].blank) < 88.9 for member in station[4:6])]
    assert len(thin) == 24
    record = read_record("factory-bolted-alternatives.json")
    hl = next(item for item in record["alternatives"] if item["id"] == "simpson-hl33-hl35")
    assert hl["receiver"]["preserved_stations_with_thin_member"] == len(thin)


def test_retail_hl43_does_not_rescue_thin_member_stations() -> None:
    record = read_record("simpson-hl43-retail.json")
    detail = record["bolted_detail_screen"]
    assert record["product"]["home_depot_url"].startswith("https://www.homedepot.com/")
    assert detail["catalog_minimum_wood_thickness_mm"] == 130.175
    assert detail["thickness_deficit_mm"] == 92.075
    assert detail["preserved_stations_with_at_least_one_thin_member"] == 24
    assert detail["published_values_applicable_to_preserved_stock"] is False


def test_mitek_b66_bolt_table_excludes_preserved_single_2x6() -> None:
    record = read_record("mitek-b66-retail.json")
    assert record["product"]["lowes_url"].startswith("https://www.lowes.com/")
    assert record["product"]["manufacturer_load_table_url"].startswith("https://www.mitek-us.com/")
    assert record["bolted_detail_screen"]["catalog_minimum_wood_thickness_mm"] == 76.2
    assert record["bolted_detail_screen"]["preserved_receiver_thickness_mm"] == 38.1
    assert record["bolted_detail_screen"]["published_values_applicable_to_preserved_stock"] is False
    assert record["retail_screen"]["currently_sold_on_lowes_com"] is False
    sibling = record["home_depot_sibling_ub88_screen"]
    assert sibling["home_depot_url"].startswith("https://www.homedepot.com/")
    assert sibling["catalog_minimum_wood_thickness_mm"] == 76.2
    assert sibling["preserved_receiver_thickness_mm"] == 38.1
    assert sibling["published_values_applicable_to_preserved_stock"] is False
    assert sibling["hole_centers_dimensioned_in_inspected_drawing"] is False
