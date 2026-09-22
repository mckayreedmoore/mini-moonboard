"""Current integrated post/header and kicker transfer remains conditional."""

import pytest

from scripts.owner_barrel_post_header_preliminary import report


@pytest.fixture(scope="module")
def result():
    return report()


def test_two_sides_bind_current_source_inventory(result):
    assert result["geometry_source"].endswith("build_integrated_viewer_assembly()")
    assert result["material_source"] == "docs/bolted-candidate-material-basis.json"
    assert result["inventory"] == {
        "barrel_pairs": 46,
        "former_angle_stations": 24,
        "fixed_panel_kicker_screws": 66,
        "retained_frame_bolts": 12,
        "post_header_bolts": 4,
        "fixed_center_kicker_screws": 4,
        "separate_backers": 0,
    }
    assert set(result["posts"]) == {
        "base_post_center_left",
        "base_post_center_right",
    }
    for side in ("left", "right"):
        post = result["posts"][f"base_post_center_{side}"]
        assert post["station"] == f"clip_split_header_center_{side}"
        assert len(post["bolt_rows"]) == 2
        assert len(post["kicker_screws"]) == 2
        assert all(
            row["name"].startswith(f"round_kicker_{side}_center_")
            for row in post["kicker_screws"]
        )


def test_modeled_geometry_and_component_scales(result):
    for side in ("left", "right"):
        post = result["posts"][f"base_post_center_{side}"]
        assert post["row_spacing_mm"] == pytest.approx(35.0)
        assert post["unit_y_screw_force_sensitivity"][
            "equal_two_screw_total_1n_axial_row_couple_n"
        ] == pytest.approx(3.2257)
        assert post["face"]["gross_area_mm2"] == pytest.approx(12419.33)
        assert post["face"]["trial_cut_area_mm2"] == pytest.approx(12330.973, abs=0.002)
        assert post["isolated_post_section"][
            "two_full_slot_parallel_tension_reference_n"
        ] == pytest.approx(42182.041, abs=0.01)
        for row in post["bolt_rows"]:
            assert row["nominal_bolt_length_mm"] == pytest.approx(88.9)
            assert row["shaft_diameter_mm"] == pytest.approx(6.35)
            assert row["head_diameter_mm"] == pytest.approx(11.0)
            assert row["head_height_mm"] == pytest.approx(4.0)
            assert row["washer_outer_diameter_mm"] == pytest.approx(25.4)
            assert row["washer_thickness_mm"] == pytest.approx(1.651)
            assert row["machine_bore_diameter_mm"] == pytest.approx(7.5)
            assert row["barrel_body_diameter_mm"] == pytest.approx(10.0076)
            assert row["barrel_cross_bore_depth_mm"] == pytest.approx(68.501)
            assert row["tip_past_barrel_far_wall_mm"] == pytest.approx(5.2452)
            assert row["ideal_full_contact_washer_fc_perp_n"] == pytest.approx(
                1993.14, abs=0.01
            )
            assert row["steel_only_ea_over_length_root_n_per_mm"] == pytest.approx(
                47177.023, abs=0.01
            )
            assert (
                row["steel_only_ea_over_length_nominal_n_per_mm"]
                > row["steel_only_ea_over_length_root_n_per_mm"]
            )
        for screw in post["kicker_screws"]:
            assert screw["purchased_length_mm"] == pytest.approx(63.5)
            assert screw["wood_embed_length_mm"] == pytest.approx(45.2438)
            assert screw["axis_to_nearest_x_edge_mm"] == pytest.approx(
                20.4875 if side == "left" else 17.3125
            )
            assert screw["axis_to_nearest_z_end_mm"] in (46.9, 60.0)
            assert screw["remaining_y_stock_beyond_tip_mm"] == pytest.approx(94.4562)


def test_no_demand_capacity_or_release(result):
    assert result["native_solve"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert result["signed_demand_n"] is None
    assert result["complete_joint_capacity_n"] is None
    for post in result["posts"].values():
        assert post["post_header_joint_resistance_n"] is None
        assert post["screw_withdrawal_resistance_n"] is None
        assert post["barrel_resistance_n"] is None
        assert post["complete_backing_load_path_verified"] is False
