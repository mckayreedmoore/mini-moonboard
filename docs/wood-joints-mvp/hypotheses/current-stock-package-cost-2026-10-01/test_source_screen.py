from decimal import Decimal

import pytest
import source_screen
from source_screen import (
    parse_price_line,
    price_minimum_satisfied,
    screen_offer,
    screen_public_lumber_offers,
    screen_public_plywood_offers,
)


def valid_lumber_offer(**overrides):
    offer = {
        "seller": "Big Creek Lumber",
        "stock_class": "2x6",
        "length_ft": 10,
        "actual_section_mm": (38.1, 139.7),
        "species": "Douglas Fir-Larch",
        "grade": "#2 or Better",
        "treatment": "untreated",
        "material_condition": "dry",
        "price_line": "$880.00 mbf",
        "currency": "USD",
        "price_unit_basis": "per_mbf",
    }
    offer.update(overrides)
    return offer


def requirements():
    return {
        "stock_class": "2x6",
        "length_ft": 10,
        "section_mm": (38.1, 139.7),
        "species_allowlist": ("Douglas Fir-Larch", "DF-L"),
        "grade_rule": "no2_or_better",
        "treatment": "untreated",
        "material_condition": "dry",
    }


def test_explicit_mbf_line_is_a_known_price_rate():
    result = parse_price_line("$880.00 mbf", currency="USD", unit_basis="per_mbf")

    assert result["price_known"] is True
    assert result["price_amount"] == Decimal("880.00")
    assert result["price_unit_basis"] == "per_mbf"
    assert result["price_missing_reasons"] == ()


def test_numeric_amount_without_unit_is_not_a_known_price():
    result = parse_price_line("$49.00", currency="USD")

    assert result["price_known"] is False
    assert result["price_amount"] == Decimal("49.00")
    assert result["price_unit_basis"] is None
    assert "price_unit_basis_not_known" in result["price_missing_reasons"]


def test_foreign_currency_cannot_qualify_a_dollar_amount_in_the_usd_book():
    for currency in ("EUR", "GBP", "CAD", None):
        result = parse_price_line("$49.00", currency=currency, unit_basis="per_sheet")
        assert result["price_known"] is False
        assert result["price_currency"] is None


def test_price_line_and_declared_unit_conflict_is_rejected():
    result = parse_price_line("$880.00 mbf", currency="USD", unit_basis="per_piece")

    assert result["price_known"] is False
    assert result["price_unit_basis"] is None
    assert "price_unit_basis_conflict" in result["price_missing_reasons"]


def test_ambiguous_price_unit_suffix_is_rejected():
    result = parse_price_line("$880.00 / mbf or per piece", currency="USD")

    assert result["price_known"] is False
    assert result["price_unit_basis"] is None
    assert "price_unit_suffix_ambiguous" in result["price_missing_reasons"]


def test_malformed_digit_grouping_cannot_become_a_known_rate():
    for text in (
        "$1,,527.00 mbf",
        "$1,52.00 mbf",
        "$1,2,3 mbf",
        "$49. mbf",
        "$49.00. mbf",
    ):
        result = parse_price_line(text, currency="USD", unit_basis="per_mbf")
        assert result["price_known"] is False
    grouped = parse_price_line("$1,527.00 mbf", currency="USD", unit_basis="per_mbf")
    assert grouped["price_known"] is True
    assert grouped["price_amount"] == Decimal("1527.00")


def test_complete_matching_lumber_listing_passes_public_spec_screen():
    result = screen_offer(valid_lumber_offer(), requirements())

    assert result["price_known"] is True
    assert result["specification_eligible"] is True
    assert result["evidence_missing"] == ()


def test_incomplete_lumber_requirements_cannot_skip_specification_checks():
    rejected_offer = valid_lumber_offer(
        grade="Appearance Grade", treatment="treated", material_condition="green"
    )
    with pytest.raises(ValueError, match="incomplete lumber specification"):
        screen_offer(rejected_offer, {})
    for field in requirements():
        for missing_value in (None, "", ()):
            incomplete = {**requirements(), field: missing_value}
            with pytest.raises(ValueError, match="incomplete lumber specification"):
                screen_offer(rejected_offer, incomplete)
        incomplete = requirements()
        del incomplete[field]
        with pytest.raises(ValueError, match="incomplete lumber specification"):
            screen_offer(rejected_offer, incomplete)


def test_cedar_offer_is_rejected_as_cross_species():
    result = screen_offer(
        valid_lumber_offer(species="Western Red Cedar"), requirements()
    )

    assert result["price_known"] is True
    assert result["specification_eligible"] is False
    assert "species_mismatch" in result["specification_conflicts"]


def test_generic_douglas_fir_label_does_not_establish_df_larch_group():
    result = screen_offer(valid_lumber_offer(species="Douglas Fir"), requirements())

    assert result["specification_eligible"] is False
    assert "required_species_group_not_demonstrated" in result["evidence_missing"]


def test_wrong_actual_section_is_rejected_even_with_matching_nominal_label():
    result = screen_offer(
        valid_lumber_offer(actual_section_mm=(39.7, 143.0)), requirements()
    )

    assert result["specification_eligible"] is False
    assert "actual_section_mismatch" in result["specification_conflicts"]


def test_wrong_stock_length_is_rejected_without_price_transfer():
    result = screen_offer(valid_lumber_offer(length_ft=12), requirements())

    assert result["price_known"] is True
    assert result["specification_eligible"] is False
    assert "length_ft_mismatch" in result["specification_conflicts"]


def test_appearance_or_unmapped_grade_does_not_pass_as_no2():
    result = screen_offer(valid_lumber_offer(grade="Appearance Grade"), requirements())

    assert result["specification_eligible"] is False
    assert "no2_structural_grade_not_demonstrated" in result["evidence_missing"]


def test_mixed_or_qualified_grade_phrase_cannot_pass_by_containing_no2():
    for grade in ("#2 or lower", "No. 2 Utility", "mixed #2/#3"):
        result = screen_offer(valid_lumber_offer(grade=grade), requirements())
        assert result["specification_eligible"] is False
        assert "no2_structural_grade_not_demonstrated" in result["evidence_missing"]


def test_unrecognized_grade_rule_cannot_skip_a_required_grade_check():
    required = {**requirements(), "grade_rule": "no2_structural"}
    with pytest.raises(ValueError, match="unsupported structural grade rule"):
        screen_offer(valid_lumber_offer(grade=None), required)


def test_antistain_treated_lumber_does_not_match_untreated_requirement():
    result = screen_offer(
        valid_lumber_offer(treatment="anti-stain treated"), requirements()
    )

    assert result["specification_eligible"] is False
    assert "treatment_mismatch" in result["specification_conflicts"]


def test_green_stock_does_not_match_dry_service_input():
    result = screen_offer(
        valid_lumber_offer(material_condition="green"), requirements()
    )

    assert result["specification_eligible"] is False
    assert "material_condition_mismatch" in result["specification_conflicts"]


def test_missing_condition_and_actual_section_remain_evidence_gaps():
    result = screen_offer(
        valid_lumber_offer(actual_section_mm=None, material_condition=None),
        requirements(),
    )

    assert result["specification_eligible"] is False
    assert "actual_section_not_published" in result["evidence_missing"]
    assert "material_condition_not_published" in result["evidence_missing"]


def test_quantity_tier_does_not_apply_below_its_minimum():
    assert price_minimum_satisfied(48, 6) is False
    assert price_minimum_satisfied(48, 48) is True
    assert price_minimum_satisfied(48, None) is None


def test_public_lumber_rates_remain_price_known_but_specification_ineligible():
    screened = screen_public_lumber_offers()

    assert len(screened) == 11
    assert all(row["price_known"] for row in screened)
    assert all(row["price_unit_basis"] == "per_mbf" for row in screened)
    assert all(row["listing_quantity_unit"] == "piece" for row in screened)
    assert all(not row["specification_eligible"] for row in screened)
    four_by_four = [row for row in screened if row["stock_class"] == "4x4"]
    assert all(
        "no2_structural_grade_not_demonstrated" in row["evidence_missing"]
        for row in four_by_four
    )
    four_by_six = [row for row in screened if row["stock_class"] == "4x6"]
    assert all(
        "required_species_group_not_demonstrated" in row["evidence_missing"]
        for row in four_by_six
    )
    assert all(
        "actual_section_not_published" in row["evidence_missing"] for row in screened
    )
    assert all(
        "treatment_status_not_published" in row["evidence_missing"] for row in screened
    )
    assert all(
        "material_condition_not_published" in row["evidence_missing"]
        for row in screened
    )
    assert not any(
        row["stock_class"] == "2x6" and row["length_ft"] == 16 for row in screened
    )


def test_public_line_class_and_length_use_an_independent_sku_request(monkeypatch):
    offer = valid_lumber_offer(sku="1321020610", stock_class="4x6", length_ft=12)
    monkeypatch.setattr(source_screen, "PUBLIC_LUMBER_OFFERS", (offer,))
    result = screen_public_lumber_offers()[0]
    assert result["specification_eligible"] is False
    assert "stock_class_mismatch" in result["specification_conflicts"]
    assert "length_ft_mismatch" in result["specification_conflicts"]
    monkeypatch.setattr(
        source_screen, "PUBLIC_LUMBER_OFFERS", (valid_lumber_offer(sku="unrecognized"),)
    )
    with pytest.raises(ValueError, match="unrecognized public lumber line"):
        screen_public_lumber_offers()


def test_other_seller_cannot_inherit_a_recorded_big_creek_sku_request(monkeypatch):
    offer = valid_lumber_offer(seller="Another seller", sku="1321020610")
    monkeypatch.setattr(source_screen, "PUBLIC_LUMBER_OFFERS", (offer,))
    with pytest.raises(ValueError, match="unrecognized public lumber line"):
        screen_public_lumber_offers()


def test_public_book_wrapper_does_not_accept_caller_supplied_observations():
    fabricated_offer = valid_lumber_offer(sku="1321020610", price_line="$1.00 each")
    with pytest.raises(TypeError):
        screen_public_lumber_offers([fabricated_offer])


def test_recorded_lumber_prices_and_source_identities_match_the_dated_table():
    expected = {
        "1321020608": ("880.00", "59", "18426"),
        "1321020610": ("880.00", "59", "18427"),
        "1321020612": ("880.00", "59", "18428"),
        "1321040408": ("1484.00", "14", "18472"),
        "1321040410": ("1484.00", "14", "18473"),
        "1321040412": ("1484.00", "14", "18474"),
        "1321040416": ("1484.00", "14", "18476"),
        "1321040608": ("1527.00", "14", "18500"),
        "1321040610": ("1527.00", "14", "18501"),
        "1321040612": ("1527.00", "14", "18502"),
        "1321040616": ("1527.00", "14", "18504"),
    }
    actual = {row["sku"]: row for row in screen_public_lumber_offers()}
    assert set(actual) == set(expected)
    for sku, (amount, page, product) in expected.items():
        row = actual[sku]
        assert row["seller"] == "Big Creek Lumber"
        assert row["observed_on"] == "2026-10-01"
        assert row["price_amount"] == Decimal(amount)
        assert row["price_currency"] == "USD"
        assert row.get("quantity_minimum") is None
        assert row["source_url"] == (
            "https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx"
            f"?pg={page}&pid={product}&pl1=1"
        )


def test_plywood_tier_and_specification_gaps_stay_separate():
    below_tier = screen_public_plywood_offers(required_quantity=47)
    at_tier = screen_public_plywood_offers(required_quantity=48)

    hd_below = [row for row in below_tier if row["seller"] == "The Home Depot"]
    hd_at = [row for row in at_tier if row["seller"] == "The Home Depot"]
    assert len(hd_below) == 2
    assert all(row["price_known"] for row in hd_below)
    assert all(not row["specification_eligible"] for row in hd_below)
    assert hd_below[0]["price_minimum_satisfied"] is True
    assert hd_below[1]["price_minimum_satisfied"] is False
    assert hd_at[0]["price_minimum_satisfied"] is True
    assert hd_at[1]["price_minimum_satisfied"] is True
    assert [(row["price_amount"], row["quantity_minimum"]) for row in hd_at] == [
        (Decimal("49.00"), None),
        (Decimal("44.10"), 48),
    ]
    for row in hd_at:
        assert row["observed_on"] == "2026-10-01"
        assert row["price_currency"] == "USD"
        assert row["price_unit_basis"] == "per_sheet"
        assert row["sku"] == "Internet #100003769 / Model #605189 / Store SKU #724084"
        assert row["source_url"] == "https://www.homedepot.com/p/100003769"
    sutherlands = next(row for row in below_tier if row["seller"] == "Sutherlands")
    assert sutherlands["price_known"] is False
    assert sutherlands["price_currency"] == "USD"
    assert sutherlands["price_amount"] is None
    assert sutherlands["sku"] == "2552586"
    assert sutherlands["observed_on"] == "2026-10-01"
    assert sutherlands["price_unit_basis"] == "per_sheet"
