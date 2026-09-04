import csv
from pathlib import Path

import pytest

from mini_moonboard import main_led_datums, main_tnut_datums
from mini_moonboard.export import export_panel_grid


def test_main_tnut_datums_follow_the_metric_template() -> None:
    datums = main_tnut_datums()

    assert len(datums) == 11 * 12
    assert datums["A1"] == pytest.approx((200.0, 80.0))
    assert datums["B1"] == pytest.approx((400.0, 80.0))
    assert datums["A2"] == pytest.approx((200.0, 280.0))
    assert datums["K12"] == pytest.approx((2200.0, 2280.0))


def test_led_datums_are_100_mm_below_each_tnut_row() -> None:
    datums = main_led_datums()

    assert len(datums) == 11 * 12
    assert datums["A1"] == pytest.approx((200.0, -20.0))
    assert datums["K12"] == pytest.approx((2200.0, 2180.0))


def test_exports_dual_unit_datum_table(tmp_path: Path) -> None:
    path = export_panel_grid(tmp_path)
    rows = list(csv.DictReader(path.open(newline="")))

    assert len(rows) == 264
    assert rows[0] == {
        "feature": "tnut",
        "label": "A1",
        "x_mm": "200.000",
        "y_mm": "80.000",
        "x_in": "7.8740",
        "y_in": "3.1496",
    }
    assert rows[132]["feature"] == "led"
    assert rows[132]["y_mm"] == "-20.000"
