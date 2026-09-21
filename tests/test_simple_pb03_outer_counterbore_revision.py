"""Isolated PB03 outer-upright counterbore geometry prototype."""

import pytest

from scripts import simple_pb03_outer_counterbore_revision as revision


@pytest.fixture(scope="module")
def result():
    return revision.screen()


def test_counterbore_is_bound_to_the_six_outer_upright_stations(result):
    assert result["schema"] == "simple_pb03_outer_counterbore_revision/v1"
    assert result["pb03_source_id"] == revision.PB03_SOURCE_ID
    assert result["target_stations"] == list(revision.TARGET_STATIONS)
    assert result["inventory"] == {
        "stations": 6,
        "upright_bolts": 12,
        "counterbores": 12,
        "unchanged_rail_stacks": 12,
        "fixed_panel_kicker_axes": 66,
    }
    assert result["source_geometry_preserved"] is True
    assert result["quarter_inch_shafts_preserved"] is True
    assert result["rail_stacks_preserved"] is True
    assert result["fixed_axes_unchanged"] is True


def test_depth_follows_the_complete_eight_inch_stack(result):
    stack = result["stack_basis"]
    assert stack["bolt_product"] == "Everbilt 800696"
    assert stack["bolt_nominal_length_mm"] == pytest.approx(203.2)
    assert stack["bolt_listed_thread_length_mm"] == pytest.approx(152.4)
    assert stack["original_wood_grip_mm"] == pytest.approx(228.6)
    assert stack["washer_each_side_mm"] == pytest.approx(1.651)
    assert stack["washer_outside_diameter_mm"] == pytest.approx(18.6436)
    assert stack["nut_height_mm"] == pytest.approx(5.7404)
    assert stack["nut_max_across_corners_mm"] == pytest.approx(12.827)
    assert stack["two_thread_projection_mm"] == pytest.approx(2.54)
    assert stack["required_counterbore_depth_mm"] == pytest.approx(36.9824)
    assert stack["revised_wood_grip_mm"] == pytest.approx(191.6176)
    assert stack["stack_length_mm"] == pytest.approx(203.2)
    assert stack["thread_beyond_wood_mm"] == pytest.approx(9.9314)
    assert stack["required_thread_beyond_wood_mm"] == pytest.approx(9.9314)
    assert stack["listed_thread_length_pass"] is True
    assert stack["forstner_diameter_mm"] == pytest.approx(25.4)


def test_pockets_and_access_clear_every_preserved_feature(result):
    assert result["pocket_unintended_bore_hits_mm3"] == {}
    assert result["pocket_preserved_stack_hits_mm3"] == {}
    assert result["pocket_unrelated_timber_hits_mm3"] == {}
    assert result["pocket_panel_hits_mm3"] == {}
    assert result["pocket_fixed_axis_hits_mm3"] == {}
    assert result["pocket_to_pocket_hits_mm3"] == {}
    assert result["counterbore_tool_obstruction_hits_mm3"] == {}
    assert result["socket_outside_pocket_mm3"] == {}
    assert result["all_counterbores_inside_blocks"] is True
    assert result["all_intended_bores_open_into_pockets"] is True
    assert result["all_geometry_checks_pass"] is True


def test_remaining_ligaments_are_reported_without_strength_claim(result):
    ligaments = result["governing_ligaments_mm"]
    assert ligaments["axial_wood_beyond_pocket"] == pytest.approx(102.7176)
    assert ligaments["pocket_to_block_edge"] == pytest.approx(15.875)
    assert ligaments["between_counterbores"] == pytest.approx(19.6)
    assert ligaments["pocket_to_unintended_bore"] > 0
    assert ligaments["pocket_to_preserved_stack"] > 0
    assert result["decision"] == "PASS_ISOLATED_GEOMETRY_ONLY"
    assert result["strength_checked"] is False
    assert result["active_design_integrated"] is False
    assert result["qualified_for_design"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False


def test_invalid_forstner_size_fails_closed():
    with pytest.raises(ValueError, match="Forstner"):
        revision.screen(forstner_diameter_mm=18.0)


def test_reusable_builder_returns_the_exact_twelve_pockets():
    module = revision.PB03Native()
    pockets, blocks = revision.build_counterbored_blocks(module.pb03_geometries())

    assert len(pockets) == 12
    assert set(blocks) == set(revision.TARGET_STATIONS)
    for station in revision.TARGET_STATIONS:
        original = module.pb03_geometries()[station].block
        revised = blocks[station]
        assert original.BoundingBox().xlen == pytest.approx(revised.BoundingBox().xlen)
        assert original.BoundingBox().ylen == pytest.approx(revised.BoundingBox().ylen)
        assert original.BoundingBox().zlen == pytest.approx(revised.BoundingBox().zlen)
        assert original.Volume() - revised.Volume() > 0
