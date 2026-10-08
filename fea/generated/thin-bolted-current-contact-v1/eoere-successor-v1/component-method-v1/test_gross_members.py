"""Small first-order own-datum/couple witnesses, never a candidate field."""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("eoere_gross_test", Path(__file__).with_name("gross_members.py"))
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def toy():
    return {"source_inputs": {"timber_rows": [{"name": "toy", "axis": [1., 0., 0.],
        "section_u": [0., 1., 0.], "section_v": [0., 0., 1.], "start": [0., 0., 0.],
        "end": [100., 0., 0.], "width_mm": 38.1, "depth_mm": 139.7}]},
        "physical_body_descriptors": [{"id": "toy", "center_xyz_mm": [50., 0., 0.]}],
        "body_applied_loads": [{"id": "self-weight/toy", "body": "toy",
            "point_xyz_mm": [50., 0., 0.], "force_xyz_n": [0., 0., 0.]}],
        "common_shaft_bearing_actions": [], "shaft_end_capture_actions": [],
        "panel_screw_actions": [], "contact_actions": [], "floor_actions": []}


def test_own_support_cut_membership_and_preserved_input():
    field = toy()
    field["shaft_end_capture_actions"] = [{"first": "shaft/toy", "second": "toy",
        "point_xyz_mm": [49., 3., 4.], "host_support_point_xyz_mm": [51., 3., 4.],
        "force_on_first_xyz_n": [6., 0., 0.]}]
    before = copy.deepcopy(field)
    actions, gravity = method.own.member_point_inputs(field)
    assert actions["toy"][0][0] == [51., 3., 4.]
    wrench = method.own.previous.member_cut_wrench([1., 0., 0.], 0., 100., [50., 0., 0.],
                                                    *gravity["toy"], actions["toy"])
    assert wrench["force_on_lower_portion_xyz_n"] == [0., 0., 0.]
    output = method.member_witnesses(field, samples=3)
    assert len(output) == 1 and output[0]["sample_count"] == 5
    assert output[0]["own_host_capture_points_and_free_couples_preserved"] is True
    assert field == before


def test_signed_own_side_free_couple_and_arm_hand_answer():
    field = toy()
    field["common_shaft_bearing_actions"] = [{"first": "shaft/toy", "second": "toy",
        "point_xyz_mm": [9., 3., 4.], "host_support_point_xyz_mm": [10., 3., 4.],
        "force_on_first_xyz_n": [0., 6., 0.], "moment_on_first_at_point_xyz_nmm": [2., 0., 1.]}]
    actions, gravity = method.own.member_point_inputs(field)
    answer = method.own.previous.member_cut_wrench([1., 0., 0.], 0., 100., [20., 0., 0.],
                                                   *gravity["toy"], actions["toy"])
    assert np.allclose(answer["force_on_lower_portion_xyz_n"], [0., 6., 0.])
    assert np.allclose(answer["moment_on_lower_portion_about_cut_xyz_nmm"], [-22., 0., -59.])


def test_affine_gravity_preserves_known_cut_force_and_arm():
    field = toy()
    field["body_applied_loads"][0].update(point_xyz_mm=[50., 3., 0.], force_xyz_n=[0., 0., -10.])
    field["physical_body_descriptors"][0]["center_xyz_mm"] = [50., 3., 0.]
    actions, gravity = method.own.member_point_inputs(field)
    answer = method.own.previous.member_cut_wrench([1., 0., 0.], 0., 100., [50., 0., 0.],
                                                   *gravity["toy"], actions["toy"])
    assert np.allclose(answer["force_on_lower_portion_xyz_n"], [0., 0., 5.])
    assert np.allclose(answer["moment_on_lower_portion_about_cut_xyz_nmm"], [15., 125., 0.])


@pytest.mark.parametrize("mutation", ["centroid", "span", "basis", "gravity_couple"])
def test_contradictory_source_views_rejected(mutation):
    field = toy()
    if mutation == "centroid":
        field["physical_body_descriptors"][0]["center_xyz_mm"][0] = 51.
    elif mutation == "span":
        field["source_inputs"]["timber_rows"][0]["end"][1] = 1.
    elif mutation == "basis":
        field["source_inputs"]["timber_rows"][0]["section_u"] = [0., -1., 0.]
    else:
        field["body_applied_loads"][0]["moment_xyz_nmm"] = [1., 0., 0.]
    with pytest.raises(ValueError):
        method.member_witnesses(field, samples=3)
