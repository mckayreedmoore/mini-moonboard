"""The PB05 short-stock proposal retains all eight geometry duties."""

import math
from types import SimpleNamespace

import pytest

from scripts import simple_pb05_short_block_screen as short


def test_outer_washer_openings_follow_bolt_interface():
    geometry = SimpleNamespace(
        station=short.pb05.OUTER_STATIONS[0],
        upright_name="upright",
        rail_name="rail",
        block_length_mm=152.4,
        report={"rail_bore_n_offset_mm": 80.159},
        bolts=(
            SimpleNamespace(name="trial_upright_1", members=("upright", "block")),
            SimpleNamespace(name="trial_rail_1", members=("rail", "block")),
        ),
    )
    openings = short._openings(geometry)
    upright_n = short.lower.UPRIGHT_N_OFFSETS_MM[0]
    assert openings["trial_upright_1/washer"]["near_net_mm"] == pytest.approx(
        upright_n - short.narrow.hardware.WASHER_OUTSIDE_DIAMETER_MM / 2
    )
    assert openings["trial_rail_1/washer"]["near_net_mm"] == pytest.approx(
        80.159 - short.lower.WASHER_DIAMETER_MM / 2
    )


@pytest.fixture(scope="module")
def result():
    return short.screen()


def test_common_six_inch_rebuild_keeps_fixed_inventory(result):
    assert result["source_id"] == "pb05-six-narrow-no-pocket-outer-v1"
    assert result["common_length_mm"] == 152.4
    assert set(result["stations"]) == set(short.STATIONS)
    assert result["inventory"] == {
        "stations": 8,
        "outer_blocks": 6,
        "center_blocks": 2,
        "panel_kicker_axes": 66,
        "frame_bolt_axes": 12,
        "new_bolt_axes": 32,
        "counterbores": 0,
    }
    for name, row in result["stations"].items():
        width = 95.25 if name in short.pb05.OUTER_STATIONS else 139.7
        assert row["block_dimensions_mm"] == pytest.approx([width, 57.15, 152.4])
        assert len(row["end_openings_mm"]) == 8
        assert len(row["rail_tool_x_edge_reserves_mm"]) == 2
        expected_area = math.pi * (short.lower.BOLT_DIAMETER_MM / 2) ** 2
        lengths = row["installed_shaft_volumes_mm3"]
        assert len(lengths) == 4
        assert all(
            volume
            == pytest.approx(expected_area * (203.2 if "_upright_" in bolt else 127.0))
            for bolt, volume in lengths.items()
        )


def test_all_eight_simultaneous_gates_and_no_release(result):
    assert result["decision"] == "PASS_GEOMETRY_ONLY"
    assert result["station_pairs"]["total"] == 28
    assert (
        result["station_pairs"]["exact"]
        + result["station_pairs"]["separated_by_envelope"]
        == 28
    )
    assert result["simultaneous_pair_hits_mm3"] == {}
    assert all(all(row["gates"].values()) for row in result["stations"].values())
    assert result["provisional_minimum_end_length_mm"] == pytest.approx(125.559)
    assert result["force_transfer"] is False
    assert result["strength_checked"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False


def test_invalid_common_length_rejected():
    with pytest.raises(ValueError, match="positive and finite"):
        short.screen(0)
