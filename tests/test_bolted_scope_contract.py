"""Scope guard for the structural-only candidate lane."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "docs" / name).read_text())


def axes(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_contract_preserves_panel_policy_and_structural_partition() -> None:
    contract = load("bolted-candidate-panel-contract.json")
    rows = axes(contract["widths"]["official"])

    assert contract["panel_policy"]["inserts"]["in_scope"] is False
    assert contract["panel_policy"]["through_bolts"]["in_scope"] is False
    assert sum(row["shop_opening_kind"] == "sds_wood" for row in rows) == 144
    assert sum(row["shop_opening_kind"] == "hillman_panel" for row in rows) == 66
    assert sum(row["shop_opening_kind"] == "bolt_clearance" for row in rows) == 12
    assert len({row["first_member"] for row in rows if row["shop_opening_kind"] == "sds_wood"}) == 24


def test_both_width_packets_preserve_the_same_scope_counts() -> None:
    contract = load("bolted-candidate-panel-contract.json")
    for path in contract["widths"].values():
        rows = axes(path)
        assert len(rows) == 222
        assert sum(row["shop_opening_kind"] == "sds_wood" for row in rows) == 144
        assert sum(row["shop_opening_kind"] == "hillman_panel" for row in rows) == 66
        assert sum(row["shop_opening_kind"] == "bolt_clearance" for row in rows) == 12
