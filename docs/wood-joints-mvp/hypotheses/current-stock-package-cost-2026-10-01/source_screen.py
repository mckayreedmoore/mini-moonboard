"""Pure source offer parser and eligibility screen for the 2026-10-01 stock packet.

This module records public listing observations only. It does not calculate a
candidate package cost or imply purchase, stock availability, or material
acceptance.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

EXPECTED_SECTIONS_MM: dict[str, tuple[float, float]] = {
    "2x6": (38.1, 139.7),
    "4x4": (88.9, 88.9),
    "4x6": (88.9, 139.7),
}

# Independent nominal line requests keyed to the recorded seller identities.
# These are comparison asks, not product qualification or purchase selection.
PUBLIC_LUMBER_REQUESTS = {
    **{
        ("Big Creek Lumber", f"13210206{length:02d}"): ("2x6", length)
        for length in (8, 10, 12)
    },
    **{
        ("Big Creek Lumber", f"13210404{length:02d}"): ("4x4", length)
        for length in (8, 10, 12, 16)
    },
    **{
        ("Big Creek Lumber", f"13210406{length:02d}"): ("4x6", length)
        for length in (8, 10, 12, 16)
    },
}

_PRICE_RE = re.compile(
    r"^\s*\$?\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,2})?)"
)
_UNIT_ALIASES = {
    "mbf": "per_mbf",
    "per mbf": "per_mbf",
    "per_mbf": "per_mbf",
    "$/mbf": "per_mbf",
    "thousand board feet": "per_mbf",
    "piece": "per_piece",
    "each": "per_piece",
    "per piece": "per_piece",
    "per_piece": "per_piece",
    "sheet": "per_sheet",
    "per sheet": "per_sheet",
    "per_sheet": "per_sheet",
    "pack": "per_pack",
    "per pack": "per_pack",
    "per_pack": "per_pack",
}


PUBLIC_LUMBER_OFFERS: tuple[dict[str, Any], ...] = (
    {
        "seller": "Big Creek Lumber",
        "country": "United States",
        "currency": "USD",
        "stock_class": "2x6",
        "length_ft": 8,
        "observed_on": "2026-10-01",
        "listing_quantity_unit": "piece",
        "sku": "1321020608",
        "description": "Douglas Fir #2 or Better S4S",
        "source_quote": "2x6x8; Douglas Fir #2 or Better S4S; $880.00 / MBF; quantity unit piece",
        "species": "Douglas Fir",
        "grade": "#2 or Better",
        "price_line": "$880.00 mbf",
        "price_unit_basis": "per_mbf",
        "source_url": "https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=59&pid=18426&pl1=1",
    },
    {
        "seller": "Big Creek Lumber",
        "country": "United States",
        "currency": "USD",
        "stock_class": "2x6",
        "length_ft": 10,
        "observed_on": "2026-10-01",
        "listing_quantity_unit": "piece",
        "sku": "1321020610",
        "description": "Douglas Fir #2 or Better S4S",
        "source_quote": "2x6x10; Douglas Fir #2 or Better S4S; $880.00 / MBF; quantity unit piece",
        "species": "Douglas Fir",
        "grade": "#2 or Better",
        "price_line": "$880.00 mbf",
        "price_unit_basis": "per_mbf",
        "source_url": "https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=59&pid=18427&pl1=1",
    },
    {
        "seller": "Big Creek Lumber",
        "country": "United States",
        "currency": "USD",
        "stock_class": "2x6",
        "length_ft": 12,
        "observed_on": "2026-10-01",
        "listing_quantity_unit": "piece",
        "sku": "1321020612",
        "description": "Douglas Fir #2 or Better S4S",
        "source_quote": "2x6x12; Douglas Fir #2 or Better S4S; $880.00 / MBF; quantity unit piece",
        "species": "Douglas Fir",
        "grade": "#2 or Better",
        "price_line": "$880.00 mbf",
        "price_unit_basis": "per_mbf",
        "source_url": "https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=59&pid=18428&pl1=1",
    },
    *(
        {
            "seller": "Big Creek Lumber",
            "country": "United States",
            "currency": "USD",
            "stock_class": "4x4",
            "length_ft": length_ft,
            "observed_on": "2026-10-01",
            "listing_quantity_unit": "piece",
            "sku": f"13210404{length_ft:02d}",
            "description": "Doug Fir Std or Btr S4S",
            "source_quote": f"4x4x{length_ft}; Doug Fir Std or Btr S4S; $1,484.00 / MBF; quantity unit piece",
            "species": "Douglas Fir",
            "grade": "Std or Btr",
            "price_line": "$1,484.00 mbf",
            "price_unit_basis": "per_mbf",
            "source_url": f"https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid={pid}&pl1=1",
        }
        for length_ft, pid in ((8, 18472), (10, 18473), (12, 18474), (16, 18476))
    ),
    *(
        {
            "seller": "Big Creek Lumber",
            "country": "United States",
            "currency": "USD",
            "stock_class": "4x6",
            "length_ft": length_ft,
            "observed_on": "2026-10-01",
            "listing_quantity_unit": "piece",
            "sku": f"13210406{length_ft:02d}",
            "description": "Douglas Fir #2 or Better S4S",
            "source_quote": f"4x6x{length_ft}; Douglas Fir #2 or Better S4S; $1,527.00 / MBF; quantity unit piece",
            "species": "Douglas Fir",
            "grade": "#2 or Better",
            "price_line": "$1,527.00 mbf",
            "price_unit_basis": "per_mbf",
            "source_url": f"https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid={pid}&pl1=1",
        }
        for length_ft, pid in ((8, 18500), (10, 18501), (12, 18502), (16, 18504))
    ),
)

PUBLIC_PLYWOOD_OFFERS: tuple[dict[str, Any], ...] = (
    {
        "seller": "The Home Depot",
        "country": "United States",
        "currency": "USD",
        "observed_on": "2026-10-01",
        "listing_quantity_unit": "sheet",
        "sku": "Internet #100003769 / Model #605189 / Store SKU #724084",
        "description": "Plytanium 23/32 in. x 4 ft. x 8 ft. Southern Pine T&G plywood sheathing",
        "source_quote": "Model #605189; 23/32 in. x 4 ft. x 8 ft. Southern Pine Tongue and Groove Plywood Sheathing; $49.00; Buy 48 or more $44.10",
        "price_line": "$49.00",
        "price_unit_basis": "per_sheet",
        "quantity_minimum": None,
        "comparison_role": "comparable_sheet_offer_only",
        "source_url": "https://www.homedepot.com/p/100003769",
        "price_source_url": "https://www.homedepot.com/b/Lumber-Composites-Plywood-Sheathing-Plywood/Plytanium/23-32/4/N-5yc1vZc7q5Z4ajZ1z0mcphZ1z0mcq1",
    },
    {
        "seller": "The Home Depot",
        "country": "United States",
        "currency": "USD",
        "observed_on": "2026-10-01",
        "listing_quantity_unit": "sheet",
        "sku": "Internet #100003769 / Model #605189 / Store SKU #724084",
        "description": "Plytanium 23/32 in. x 4 ft. x 8 ft. Southern Pine T&G plywood sheathing",
        "source_quote": "Model #605189; Buy 48 or more $44.10 per sheet",
        "price_line": "$44.10",
        "price_unit_basis": "per_sheet",
        "quantity_minimum": 48,
        "comparison_role": "comparable_sheet_offer_only",
        "source_url": "https://www.homedepot.com/p/100003769",
        "price_source_url": "https://www.homedepot.com/b/Lumber-Composites-Plywood-Sheathing-Plywood/Plytanium/23-32/4/N-5yc1vZc7q5Z4ajZ1z0mcphZ1z0mcq1",
    },
    {
        "seller": "Sutherlands",
        "country": "United States",
        "currency": "USD",
        "observed_on": "2026-10-01",
        "listing_quantity_unit": "sheet",
        "sku": "2552586",
        "description": "4 ft. x 4 ft. x 23/32 in. APA CDX Yellow Pine plywood",
        "source_quote": "SKU #2552586; 4 x 4-foot x 23/32-inch APA CDX Plywood; no numeric price shown",
        "price_line": None,
        "price_unit_basis": "per_sheet",
        "quantity_minimum": None,
        "comparison_role": "candidate_item_not_crosswalked",
        "source_url": "https://sutherlands.com/products/item/2552586/sutherlands-4-x-4-foot-x-23-32-inch-apa-cdx-yellow-pine-plywood",
    },
)


def _unit_from_text(value: str | None) -> str | None:
    if not value:
        return None
    key = " ".join(value.strip().lower().replace("$", "").split())
    key = key.strip(" /:=")
    key = key.removeprefix("per ") if key in {"mbf", "piece", "sheet", "pack"} else key
    return _UNIT_ALIASES.get(key)


def _raw_price_suffix(raw_price: str) -> str:
    match = _PRICE_RE.match(raw_price)
    return raw_price[match.end() :].strip() if match else ""


def parse_price_line(
    raw_price: str | None,
    *,
    currency: str | None,
    unit_basis: str | None = None,
) -> dict[str, Any]:
    """Parse one visible amount for this USD source book, requiring unit basis.

    A numeric display without a unit is retained as a number but is not a known
    usable price. Quantity tiers are represented as separate offer records.
    """

    missing: list[str] = []
    match = _PRICE_RE.match(raw_price or "")
    amount: Decimal | None = None
    if match:
        try:
            amount = Decimal(match.group(1).replace(",", ""))
        except InvalidOperation:
            amount = None
    if amount is None:
        missing.append("numeric_price_not_displayed")

    suffix = _raw_price_suffix(raw_price or "")
    suffix_unit = _unit_from_text(suffix)
    declared_unit = _unit_from_text(unit_basis)
    unit_conflict = bool(declared_unit and suffix_unit and declared_unit != suffix_unit)
    suffix_ambiguous = bool(suffix and suffix_unit is None)
    declared_unit_unknown = bool(unit_basis and declared_unit is None)
    canonical_unit = (
        None
        if unit_conflict or suffix_ambiguous or declared_unit_unknown
        else declared_unit or suffix_unit
    )
    if unit_conflict:
        missing.append("price_unit_basis_conflict")
    elif suffix_ambiguous:
        missing.append("price_unit_suffix_ambiguous")
    elif declared_unit_unknown:
        missing.append("declared_price_unit_basis_unknown")
    elif canonical_unit is None:
        missing.append("price_unit_basis_not_known")

    currency_code = currency.strip().upper() if currency else None
    if currency_code != "USD":
        missing.append("currency_code_unsupported_for_usd_source_book")

    return {
        "price_known": not missing,
        "price_amount": amount,
        "price_currency": currency_code if currency_code == "USD" else None,
        "price_unit_basis": canonical_unit,
        "price_missing_reasons": tuple(missing),
    }


def price_minimum_satisfied(
    quantity_minimum: int | None, quantity: int | None
) -> bool | None:
    """Return whether a row's stated quantity minimum is met, if knowable.

    This does not choose an exclusive tier or select the price to pay."""

    if quantity_minimum is None:
        return True
    if quantity is None:
        return None
    return quantity >= quantity_minimum


def _grade_is_no2_or_better(grade: str | None) -> bool:
    if not grade:
        return False
    text = " ".join(grade.lower().replace("number", "no.").split())
    return bool(
        re.fullmatch(r"(?:#|no\.?\s*)\s*2(?:\s*(?:or|&)\s*(?:better|btr))?", text)
    )


def screen_offer(
    offer: Mapping[str, Any],
    requirements: Mapping[str, Any],
    *,
    required_quantity: int | None = None,
) -> dict[str, Any]:
    """Screen a complete lumber comparison, separating price and spec gaps."""

    required_fields = (
        "stock_class",
        "length_ft",
        "section_mm",
        "species_allowlist",
        "grade_rule",
        "treatment",
        "material_condition",
    )
    omitted = [field for field in required_fields if not requirements.get(field)]
    if omitted:
        raise ValueError(f"incomplete lumber specification: {', '.join(omitted)}")

    price = parse_price_line(
        offer.get("price_line"),
        currency=offer.get("currency"),
        unit_basis=offer.get("price_unit_basis"),
    )
    evidence_missing: list[str] = []
    specification_conflicts: list[str] = []

    for field in ("stock_class", "length_ft"):
        expected = requirements.get(field)
        if expected is None:
            continue
        observed = offer.get(field)
        if observed is None:
            evidence_missing.append(f"{field}_not_published")
        elif observed != expected:
            specification_conflicts.append(f"{field}_mismatch")

    expected_section = requirements.get("section_mm")
    if expected_section is not None:
        observed_section = offer.get("actual_section_mm")
        if observed_section is None:
            evidence_missing.append("actual_section_not_published")
        elif tuple(observed_section) != tuple(expected_section):
            specification_conflicts.append("actual_section_mismatch")

    species_allowlist = requirements.get("species_allowlist")
    if species_allowlist:
        species = offer.get("species")
        if not species:
            evidence_missing.append("species_not_published")
        elif species.casefold() not in {item.casefold() for item in species_allowlist}:
            normalized_species = " ".join(
                str(species).casefold().replace("-", " ").split()
            )
            if normalized_species in {"douglas fir", "df"}:
                evidence_missing.append("required_species_group_not_demonstrated")
            else:
                specification_conflicts.append("species_mismatch")

    grade_rule = requirements.get("grade_rule")
    if grade_rule is not None and grade_rule != "no2_or_better":
        raise ValueError(f"unsupported structural grade rule: {grade_rule}")
    if grade_rule == "no2_or_better":
        if not offer.get("grade"):
            evidence_missing.append("structural_grade_not_published")
        elif not _grade_is_no2_or_better(str(offer["grade"])):
            evidence_missing.append("no2_structural_grade_not_demonstrated")

    expected_treatment = requirements.get("treatment")
    if expected_treatment is not None:
        observed_treatment = offer.get("treatment")
        if observed_treatment is None:
            evidence_missing.append("treatment_status_not_published")
        elif observed_treatment.casefold() != expected_treatment.casefold():
            specification_conflicts.append("treatment_mismatch")

    expected_condition = requirements.get("material_condition")
    if expected_condition is not None:
        observed_condition = offer.get("material_condition")
        if observed_condition is None:
            evidence_missing.append("material_condition_not_published")
        elif observed_condition.casefold() != expected_condition.casefold():
            specification_conflicts.append("material_condition_mismatch")

    for field, expected in requirements.get("exact_fields", {}).items():
        observed = offer.get(field)
        if observed is None:
            evidence_missing.append(f"{field}_not_published")
        elif observed != expected:
            specification_conflicts.append(f"{field}_mismatch")

    return {
        **price,
        "specification_eligible": not evidence_missing and not specification_conflicts,
        "evidence_missing": tuple(evidence_missing),
        "specification_conflicts": tuple(specification_conflicts),
        "price_minimum_satisfied": price_minimum_satisfied(
            offer.get("quantity_minimum"), required_quantity
        ),
    }


def lumber_requirements(stock_class: str, length_ft: int) -> dict[str, Any]:
    """Build the frozen public-line comparison for an original full-section stick."""

    return {
        "stock_class": stock_class,
        "length_ft": length_ft,
        "section_mm": EXPECTED_SECTIONS_MM[stock_class],
        "species_allowlist": ("Douglas Fir-Larch", "DF-L"),
        "grade_rule": "no2_or_better",
        "treatment": "untreated",
        "material_condition": "dry",
    }


def screen_public_lumber_offers() -> tuple[dict[str, Any], ...]:
    """Screen recorded public lumber lines against their nominal stock asks."""

    screened = []
    for offer in PUBLIC_LUMBER_OFFERS:
        identity = (offer.get("seller"), offer.get("sku"))
        if identity not in PUBLIC_LUMBER_REQUESTS:
            raise ValueError(f"unrecognized public lumber line identity: {identity}")
        stock_class, length_ft = PUBLIC_LUMBER_REQUESTS[identity]
        result = screen_offer(
            offer,
            lumber_requirements(stock_class, length_ft),
        )
        screened.append({**offer, **result})
    return tuple(screened)


def screen_public_plywood_offers(
    *, required_quantity: int | None = None
) -> tuple[dict[str, Any], ...]:
    """Keep sheet price and candidate crosswalk status separate."""

    screened = []
    for offer in PUBLIC_PLYWOOD_OFFERS:
        price = parse_price_line(
            offer.get("price_line"),
            currency=offer.get("currency"),
            unit_basis=offer.get("price_unit_basis"),
        )
        evidence_missing = (
            "current_wood_lane_panel_item_crosswalk_missing",
            "plywood_layup_unverified",
            "source_sheet_layout_and_quantity_unresolved",
        )
        screened.append(
            {
                **offer,
                **price,
                "specification_eligible": False,
                "evidence_missing": evidence_missing,
                "specification_conflicts": (),
                "price_minimum_satisfied": price_minimum_satisfied(
                    offer.get("quantity_minimum"), required_quantity
                ),
            }
        )
    return tuple(screened)
