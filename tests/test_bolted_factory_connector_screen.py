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
