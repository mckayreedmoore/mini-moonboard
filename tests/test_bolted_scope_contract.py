"""Scope guard for the structural-only candidate lane."""

import csv
import json
from pathlib import Path

import pytest

from scripts.bolted_candidate_scope_contract import (
    classify,
    load_axes,
    require_same_panel_axes,
    width_contract,
)

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


def test_exported_scope_reconciles_every_axis_and_transport_member() -> None:
    panel = load("bolted-candidate-panel-contract.json")
    interfaces = load("bolted-candidate-interfaces.json")
    for width in ("official", "kerf-right"):
        rows = load_axes(width)
        result = width_contract(width, rows)
        assert panel["normalized_panel_axes_by_width"][width] == result["panel_axes"]
        assert interfaces["classified_by_width"][width] == {
            key: value for key, value in result.items() if key != "panel_axes"
        }
        assert len(result["scope_by_axis_id"]) == len({row["name"] for row in rows}) == 222
        assert set(result["scope_by_axis_id"].values()) == {"structural", "panel"}
        assert len(result["structural_stations"]) == 24
        assert len(result["retained_frame_bolts"]) == 12
        assert len(result["transport_members"]["timber"]) == 20
        assert len(result["transport_members"]["panels"]) == 6
        assert len(result["draft_separation_graph"]["panel_axis_ids"]) == 66
        assert result["move_operations"]["structural_wood_thread_removals_target"] == 0
        assert result["move_operations"]["panel_wood_thread_removals_allowed"] == 66


def test_panel_policy_rejects_changed_axis_and_unknown_scope() -> None:
    rows = load_axes("official")
    altered = list(rows)
    index = next(i for i, row in enumerate(altered) if row["shop_opening_kind"] == "hillman_panel")
    altered[index] = {**altered[index], "start_x_mm": "999"}
    with pytest.raises(ValueError, match="retained panel axes differ"):
        require_same_panel_axes(rows, tuple(altered))
    with pytest.raises(ValueError, match="unclassified attachment"):
        classify({**rows[0], "shop_opening_kind": "unknown"})


def test_scope_contract_rejects_duplicate_attachment_identity() -> None:
    rows = load_axes("official")
    with pytest.raises(ValueError, match="duplicate attachment axes"):
        width_contract("official", rows + (rows[0],))
