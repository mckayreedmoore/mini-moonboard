"""Focused geometry-only contract for the remaining eight owner duties."""

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_outer_top_layout as layout


def test_eight_duties_use_one_provisional_part_basis_without_release():
    result = layout.screen()
    assert len(result["stations"]) == 8
    assert result["source_axes"] == {"panel": 66, "frame_bolt": 12}
    assert result["provisional_hardware"]["axis_offset_mm"] == 8.001
    assert result["provisional_hardware"]["axis_offset_sensitivity_mm"] == [
        6.0,
        8.001,
        10.0,
    ]
    assert result["direct_count"] >= 2
    assert result["direct_count"] + result["exception_count"] == 8
    for station in result["stations"].values():
        assert station["source_members"]
        assert station["grain"]
        if station["mode"] == "direct":
            assert station["machine_bore_meets_barrel_bore"]
            assert station["source_wood_bore_coverage"] >= 0.999
        else:
            assert station["blocker"]
            assert not station["complete_replacement"]
    assert result["no_legacy_angle_placeholder"]
    assert not result["fit_qualified"]
    assert not result["strength_qualified"]
    assert not result["drilling_released"]


def test_viewer_adapter_has_real_hardware_and_paths_for_eight_duties():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    built = layout.build_layout(wood)
    assert len(built["stations"]) == 8
    assert built["diagnostics"]["disposition"] == "REVISE"
    for row in built["stations"].values():
        assert row["mode"] == "direct"
        assert row["compact_alternate_block"] is None
        assert row["axis_offset_mm"] == 8.001
        assert row["disposition"] == "REVISE"
        assert len(row["bolts"]) == len(row["barrels"]) == 2
        assert set(row["stacks"]) == set(row["bolts"])
        assert len(row["drilling_paths"]) == len(row["access_paths"]) == 4
        assert all(shape.Volume() > 0 for shape in row["barrels"].values())
