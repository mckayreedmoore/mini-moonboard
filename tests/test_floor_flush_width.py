"""Official 4×4 and kerf-right presentations share one selected candidate."""
from mini_moonboard.floor_flush_width import (
    KERF_RIGHT,
    KERF_RIGHT_MM,
    OFFICIAL,
    geometry_screen,
    trim_mm,
    variant,
)


def test_official_option_is_the_selected_module():
    from mini_moonboard import compact_floor_flush_frame as official
    assert variant(OFFICIAL) is official
    assert trim_mm(OFFICIAL) == 0
    assert trim_mm(KERF_RIGHT) == KERF_RIGHT_MM == 3.175


def test_kerf_right_geometry_screen_passes():
    result = geometry_screen()
    assert result['passed'], result['failures']
    assert result['left_panel_width_mm'] == 1219.2
    assert abs(result['right_panel_width_mm'] - (1219.2 - KERF_RIGHT_MM)) < 1e-4
    assert abs(result['right_rim_thickness_mm'] - 88.9) < 1e-4
    assert abs(result['right_rim_screw_edge_mm'] - 19.05) < 1e-3
    assert result['k_column_edge_mm'] > 235


def test_kerf_adapter_keeps_selected_identity_and_inventory():
    from mini_moonboard import compact_floor_flush_frame as official
    kerf = variant(KERF_RIGHT)
    assert kerf.source.KEY == official.KEY
    assert kerf.KEY == 'compact-floor-flush-kerf-right'
    assert len(kerf.connections()) == len(official.connections())
    assert len(kerf.uncut_wood_parts()) == len(official.uncut_wood_parts())
    assert {p.name for p in kerf.uncut_wood_parts()} == {p.name for p in official.uncut_wood_parts()}
