"""Product-specific nominal head input must not become physical clearance approval."""

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_hillman_42605_record_keeps_dimensions_and_panel_axes_in_scope() -> None:
    record = json.loads(
        (ROOT / "docs/bolted-candidate-hillman-42605-dimensions.json").read_text()
    )
    with (ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv").open(
        newline=""
    ) as handle:
        panel_axes = [
            row for row in csv.DictReader(handle)
            if row["shop_opening_kind"] == "hillman_panel"
        ]
    assert len(panel_axes) == record["preserved_panel_and_kicker_axes"] == 66
    assert all(
        float(row["shop_purchased_length_mm"]) == record["purchased_length_mm"]
        for row in panel_axes
    )
    assert record["retailer_listed_nominal_head_diameter_mm"] == pytest.approx(
        record["retailer_listed_nominal_head_diameter_in"] * 25.4
    )
    assert record["retailer_listed_nominal_head_radius_mm"] == pytest.approx(
        record["retailer_listed_nominal_head_diameter_mm"] / 2
    )
    assert record["shaft_external_major_diameter_mm"] is None
    assert record["head_diameter_tolerance_mm"] is None
    assert record["installed_head_projection_mm"] is None
    assert record["physical_clearance_accepted"] is False
    assert record["panel_policy_changed"] is False
    assert record["drilling_released"] is False
