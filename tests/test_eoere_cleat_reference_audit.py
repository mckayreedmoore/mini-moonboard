"""Signed loaded-edge, actual-end and bore-band reference checks."""
import copy
import math

import pytest

from scripts import eoere_cleat_reference_audit as audit


def fixture():
    profile = {"finished_YZ_polygon_mm": [[0., 0.], [100., 0.], [100., 300.], [0., 200.]],
               "basis_grain_u_v_xyz": [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
               "raw_stock_scenario_dimensions_mm": [40., 100., 300.]}
    group = [{"point_xyz_mm": [0., y, 210.], "force_xyz_n": [4., -10., 9.]}
             for y in (30., 70.)]
    return profile, group


def test_actual_slope_and_complete_bore_band_control_engagement():
    profile, group = fixture()
    result = audit.group_geometry(profile, group, 5.)
    assert result["sections"][1]["rear_y_mm"] == pytest.approx(10.)
    assert result["sections"][1]["engaged_depth_mm"] == pytest.approx(60.)
    assert result["minimum_engaged_depth_over_band_mm"] == pytest.approx(54.9999)
    assert result["nearest_actual_grain_end_mm"] == pytest.approx(20.)
    assert result["constant_full_stock_depth_over_band"] is False
    assert result["loaded_Y_sign"] == -1


def test_positive_force_selects_front_edge_and_the_farthest_bolt():
    profile, group = fixture()
    for row in group:
        row["force_xyz_n"][1] = 10.
    result = audit.group_geometry(profile, group, 5.)
    assert result["minimum_engaged_depth_over_band_mm"] == pytest.approx(70.)
    assert result["loaded_Y_sign"] == 1


def test_lower_full_rectangle_does_not_inherit_the_upper_slope():
    profile, group = fixture()
    for row in group:
        row["point_xyz_mm"][2] = 100.
    result = audit.group_geometry(profile, group, 5.)
    assert result["constant_full_stock_depth_over_band"] is True
    assert result["minimum_engaged_depth_over_band_mm"] == pytest.approx(70.)
    assert result["nearest_actual_grain_end_mm"] == pytest.approx(100.)


def test_translated_and_reflected_world_x_does_not_change_Y_plane_reference():
    profile, group = fixture()
    original = audit.group_geometry(profile, group, 5.)
    for row in group:
        row["point_xyz_mm"][0] = 1235.075
    assert audit.group_geometry(profile, group, 5.) == original


@pytest.mark.parametrize("change", ["opposing", "negligible", "wrong_grain", "split_station", "outside", "negative_radius", "nonfinite", "bowtie"])
def test_unsupported_group_or_profile_is_rejected(change):
    profile, group = fixture()
    radius = 5.
    if change == "opposing":
        group[1]["force_xyz_n"][1] = 9.
    elif change == "negligible":
        for row in group:
            row["force_xyz_n"][1] = 1e-9
    elif change == "wrong_grain":
        profile["basis_grain_u_v_xyz"][0] = [1., 0., 0.]
    elif change == "split_station":
        group[1]["point_xyz_mm"][2] += 1.
    elif change == "outside":
        group[0]["point_xyz_mm"][1] = 5.
    elif change == "negative_radius":
        radius = -1.
    elif change == "nonfinite":
        profile["finished_YZ_polygon_mm"][2][1] = math.nan
    elif change == "bowtie":
        p = profile["finished_YZ_polygon_mm"]
        p[1], p[2] = p[2], p[1]
    with pytest.raises(ValueError):
        audit.group_geometry(profile, group, radius)


def test_section_shear_uses_all_signed_Y_actions_without_a_resultant_shortcut():
    actions = [{"id": "high", "point_xyz_mm": [0., 0., 10.], "force_xyz_n": [8., -7., 3.]},
               {"id": "middle", "point_xyz_mm": [0., 0., 5.], "force_xyz_n": [9., 5., 4.]},
               {"id": "low", "point_xyz_mm": [0., 0., 0.], "force_xyz_n": [10., 2., 5.]}]
    assert audit.shear_at(actions, 6.) == {"station_mm": 6., "Y_shear_n": -7., "selected_action_ids": ["high"]}
    assert audit.shear_at(actions, 4.)["Y_shear_n"] == -2.
    assert audit.shear_at(actions, 11.)["Y_shear_n"] == 0.
    assert audit.shear_at(actions, -1.)["Y_shear_n"] == 0.


def test_material_hypothesis_reading_is_inert_and_preserves_its_declared_status(tmp_path):
    path = tmp_path/"hypothesis.py"
    path.write_text("raise RuntimeError('must never execute')\nASSUMPTIONS = "
                    "{'Ft90_mpa':0.5, 'Gc_all_modes_n_per_mm':0.1, 'property_status':'unmeasured hypothesis'}\n")
    assert audit.historical_hypothesis(path) == {"Ft90_mpa": .5, "Gc_all_modes_n_per_mm": .1,
                                                "property_status": "unmeasured hypothesis"}


def test_reference_helpers_do_not_mutate_the_frozen_input_containers():
    profile, group = fixture()
    before = copy.deepcopy((profile, group))
    audit.group_geometry(profile, group, 5.)
    assert (profile, group) == before
