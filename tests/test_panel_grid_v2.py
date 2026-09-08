"""Independent explicit template coordinates; no expensive CAD construction."""

import pytest

from mini_moonboard import panel_grid as historical
from mini_moonboard import panel_grid_v2 as grid


@pytest.mark.parametrize("height,tnut_rows,led_rows", [
    (1220.0,
     (100, 300, 500, 700, 900, 1100, 1320, 1520, 1720, 1920, 2120, 2320),
     (20, 200, 400, 600, 800, 1000, 1200, 1420, 1620, 1820, 2020, 2220)),
    (1219.2,
     (99.2, 299.2, 499.2, 699.2, 899.2, 1099.2, 1319.2, 1519.2, 1719.2,
      1919.2, 2119.2, 2319.2),
     (19.2, 199.2, 399.2, 599.2, 799.2, 999.2, 1199.2, 1419.2, 1619.2,
      1819.2, 2019.2, 2219.2)),
])
def test_explicit_panel_edge_coordinates(height, tnut_rows, led_rows):
    nuts, leds = grid.main_tnut_datums(height), grid.main_led_datums(height)
    assert len(nuts) == len(leds) == 132
    assert nuts.keys() == leds.keys()
    for column_index, column in enumerate("ABCDEFGHIJK", 1):
        for row in range(1, 13):
            assert nuts[f"{column}{row}"] == pytest.approx((column_index * 200, tnut_rows[row-1]))
            assert leds[f"{column}{row}"] == pytest.approx((column_index * 200, led_rows[row-1]))
    assert len(set(nuts.values())) == len(set(leds.values())) == 132
    assert set(nuts.values()).isdisjoint(leds.values())
    assert all(0 < s < 2 * height and 0 < x < 2 * height for x, s in (*nuts.values(), *leds.values()))
    assert nuts["A7"][1] - nuts["A6"][1] == pytest.approx(220)
    assert nuts["A1"][1] - leds["A1"][1] == pytest.approx(80)
    assert nuts["A7"][1] - leds["A7"][1] == pytest.approx(120)
    assert all(nuts[f"A{r}"][1] - leds[f"A{r}"][1] == pytest.approx(100)
               for r in range(2, 13) if r != 7)
    assert height - leds["A7"][1] == pytest.approx(20)
    assert sum(s < height for _, s in leds.values()) == 77
    assert sum(s > height for _, s in leds.values()) == 55


def test_default_is_actual_stock_and_historical_grid_is_unchanged():
    assert grid.main_tnut_datums() == grid.main_tnut_datums(1219.2)
    assert grid.main_led_datums() == grid.main_led_datums(1219.2)
    assert historical.main_tnut_datums()["A1"] == (200., 80.)
    assert historical.main_led_datums()["A1"] == (200., -20.)
    assert grid.kicker_foothold_datums() == historical.kicker_foothold_datums()


@pytest.mark.parametrize("height", [0, -1, 1200, 1220.7875, float("nan"), float("inf")])
def test_rejects_unresearched_panel_sizes(height):
    with pytest.raises(ValueError):
        grid.main_tnut_datums(height)
    with pytest.raises(ValueError):
        grid.main_led_datums(height)
