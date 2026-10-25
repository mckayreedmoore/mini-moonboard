"""Boundary checks for publication of the existing selected112 inventory."""

from __future__ import annotations

import copy
import csv
import io

import pytest

from scripts import publish_current112_hardware_plan as publisher


@pytest.fixture
def inventory():
    return {
        "stack_count": 112,
        "bolt_SKU_quantities": {
            "363": 48,
            "366": 12,
            "400": 2,
            "8092": 4,
            "8095": 14,
            "G0340956": 4,
            "G0341148": 28,
        },
        "nut_SKU_quantities": {"2571": 88, "2573": 6, "2584": 18},
        "washer_SKU_quantities_two_per_stack": {"15023": 212, "15025": 12},
        "spacers": {
            "selected_spacer_piece_count": 40,
            "catalog_SKU_counts": {"13731": 12, "13733": 20},
            "pieces_without_selected_SKU": 8,
        },
    }


@pytest.fixture
def mapping():
    return {"nominal_catalog_SKU_quantities": {"13731": 20, "13733": 20}}


def test_resolved_piece_mapping_controls_legacy_blank_ledger(inventory, mapping):
    before = copy.deepcopy(inventory)
    rows = publisher.nominal_rows(inventory, mapping)
    spacer_rows = {
        row["SKU"]: row["nominal_quantity"]
        for row in rows
        if row["category"] == "spacer"
    }
    assert spacer_rows == {"13731": 20, "13733": 20}
    assert inventory == before
    assert publisher.totals(rows) == {
        "bolt": 112,
        "nut": 112,
        "washer": 224,
        "spacer": 40,
    }
    csv_rows = list(csv.DictReader(io.StringIO(publisher.csv_bytes(rows).decode())))
    assert len(csv_rows) == 14
    assert all(row["Actual"] == row["Disposition"] == "" for row in csv_rows)
    assert not {"price", "availability", "purchase_quantity"} & set(csv_rows[0])


def test_historical_extra_bolts_and_incomplete_spacer_map_are_refused(
    inventory, mapping
):
    inventory["bolt_SKU_quantities"]["8096"] = 4
    with pytest.raises(ValueError, match="totals differ"):
        publisher.nominal_rows(inventory, mapping)
    del inventory["bolt_SKU_quantities"]["8096"]
    mapping["nominal_catalog_SKU_quantities"]["13731"] = 12
    with pytest.raises(ValueError, match="totals differ"):
        publisher.nominal_rows(inventory, mapping)


def test_source_hash_change_is_refused(tmp_path):
    source = tmp_path / "source.json"
    source.write_bytes(b"original")
    reference = {"path": source.name, "sha256": publisher.digest(b"original")}
    assert publisher.bound(tmp_path, reference) == b"original"
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Pinned source changed"):
        publisher.bound(tmp_path, reference)


def portable_fixture(tmp_path, monkeypatch, inventory, mapping):
    sources = copy.deepcopy(publisher.SOURCES)

    def save(name, record):
        raw = publisher.encode(record)
        path = tmp_path / sources[name]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        sources[name]["sha256"] = publisher.digest(raw)

    save(
        "geometry_receipt",
        {"checked_geometry": {"sha256": sources["physical_geometry"]["sha256"]}},
    )
    save(
        "response_bank",
        {
            "geometry_revision": publisher.REVISION,
            "physical_geometry": sources["geometry_receipt"],
            "all_six_cases_admitted": True,
            "cases": [{"both_independent_replays_admitted": True} for _ in range(6)],
        },
    )
    save(
        "resolved_spacers",
        {
            **mapping,
            "revision": publisher.REVISION,
            "current_spacer_pieces": 40,
            "geometry_receipt": sources["geometry_receipt"],
        },
    )
    monkeypatch.setattr(publisher, "SOURCES", sources)
    rows = publisher.nominal_rows(inventory, mapping)
    plan = publisher.make_plan(rows)
    raw = publisher.encode(plan)
    (tmp_path / publisher.PLAN).write_bytes(raw)
    (tmp_path / publisher.CSV).write_bytes(publisher.csv_bytes(rows))
    monkeypatch.setattr(publisher, "PLAN_SHA", publisher.digest(raw))
    return plan


def test_portable_check_needs_no_ignored_inventory_or_geometry(
    tmp_path, monkeypatch, inventory, mapping
):
    portable_fixture(tmp_path, monkeypatch, inventory, mapping)
    assert not (tmp_path / publisher.SOURCES["nominal_inventory"]["path"]).exists()
    assert not (tmp_path / publisher.SOURCES["physical_geometry"]["path"]).exists()
    result = publisher.check(tmp_path)
    assert result["ignored_inputs_reopened"] is False
    assert result["public_source_pins_checked"] == 3


def test_changed_release_claim_or_csv_is_refused(
    tmp_path, monkeypatch, inventory, mapping
):
    plan = portable_fixture(tmp_path, monkeypatch, inventory, mapping)
    plan["purchase_authorized"] = True
    (tmp_path / publisher.PLAN).write_bytes(publisher.encode(plan))
    with pytest.raises(ValueError, match="fingerprint differs"):
        publisher.check(tmp_path)
    monkeypatch.setattr(publisher, "PLAN_SHA", "")
    with pytest.raises(ValueError, match="counts or blank observations differ"):
        publisher.check(tmp_path)
    plan["purchase_authorized"] = False
    (tmp_path / publisher.PLAN).write_bytes(publisher.encode(plan))
    (tmp_path / publisher.CSV).write_text("different\n")
    with pytest.raises(ValueError, match="counts or blank observations differ"):
        publisher.check(tmp_path)
