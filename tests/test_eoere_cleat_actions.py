"""Independent action/exterior-wrench controls for the frozen cleat reducer."""

from copy import deepcopy

import numpy as np
import pytest

from scripts import eoere_cleat_transverse_wrench as method

NORMAL_SOURCE = {
    "path": "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-split-closure.py",
    "sha256": "e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e",
}
normal = method.component.load(NORMAL_SOURCE, "test_cleat_actions_normal").normal_bound


def extraction_fixture():
    member, y = "eoere_cleat_left", method.CUT_Y_MM
    rows, shafts = [], []
    for i, offset in enumerate((-4., -2., 2., 4.)):
        identity, point = f"bore-{i}", [0., y+offset, 0.]
        shafts.append({"axis_id": identity, "basis": [[1., 0., 0.]], "bore_diameter_mm": .5})
        actions = [{"point_xyz_mm": [-1., point[1], 0.],
                    "signed_components": {"force_on_receiver_xyz_n": [0., 2., 3.]},
                    "own_free_moment_nmm": [4., 5., 6.]},
                   {"point_xyz_mm": [1., point[1], 0.],
                    "signed_components": {"force_on_receiver_xyz_n": [0., -1., -2.]},
                    "own_free_moment_nmm": [-1., -2., -3.]},
                   {"point_xyz_mm": point,
                    "signed_components": {"force_on_receiver_xyz_n": [7., 0., 0.]},
                    "own_free_moment_nmm": [0., 0., 0.]}]
        # Hand sum: force=(7,1,1); transported moments=(0,5,-3),
        # free couples=(3,3,3), giving complete moment=(3,8,0).
        rows.append({"axis_id": identity, "receiver": member,
                     "own_aggregate_point_xyz_mm": point, "own_point_actions": actions,
                     "own_force_xyz_n": [7., 1., 1.],
                     "own_moment_at_aggregate_xyz_nmm": [3., 8., 0.]})
    field = {
        "source_inputs": {"shafts": shafts},
        "contact_actions": [
            {"id": "member-first", "first": member, "second": "neighbor-a",
             "point_xyz_mm": [2., y+1., 3.], "force_on_first_xyz_n": [4., 5., 6.],
             "moment_at_point_model_xyz_nmm": [7., 8., 9.]},
            {"id": "member-second", "first": "neighbor-b", "second": member,
             "point_xyz_mm": [1., y-1., 2.], "force_on_first_xyz_n": [-2., -3., -4.],
             "moment_at_point_model_xyz_nmm": [-5., -6., -7.]},
            {"id": "unrelated", "first": "neighbor-a", "second": "neighbor-b"}],
        "panel_screw_actions": [{"first": "panel", "second": "neighbor-a"}],
        "body_applied_loads": [{"id": "self-weight/"+member, "body": member,
                                "point_xyz_mm": [0., y, 0.], "force_xyz_n": [0., 0., -4.]}],
    }
    data = {"findings": {"timber": {"wood_surfaces": rows}}}
    geometry = {"whole_center_xyz_mm": [0., y, 0.]}
    return member, field, data, geometry


def test_complete_bore_wrenches_both_contact_signs_and_gravity_are_extracted():
    member, field, data, geometry = extraction_fixture()
    actions, gravity = method.member_actions(field, data, member, geometry)
    expected = [{"id": f"bore-{i}/complete-wood-wrench", "point_xyz_mm": [0., method.CUT_Y_MM+offset, 0.],
                 "force_xyz_n": [7., 1., 1.], "free_couple_xyz_nmm": [3., 8., 0.]}
                for i, offset in enumerate((-4., -2., 2., 4.))]
    expected.extend([
        {"id": "member-first", "point_xyz_mm": [2., method.CUT_Y_MM+1., 3.],
         "force_xyz_n": [4., 5., 6.], "free_couple_xyz_nmm": [7., 8., 9.]},
        {"id": "member-second", "point_xyz_mm": [1., method.CUT_Y_MM-1., 2.],
         "force_xyz_n": [2., 3., 4.], "free_couple_xyz_nmm": [5., 6., 7.]},
    ])
    assert actions == expected
    assert gravity.tolist() == [0., 0., -4.]


@pytest.mark.parametrize("omission", ["free-couple", "capture"])
def test_incomplete_saved_bore_wrench_is_rejected(omission):
    member, field, data, geometry = extraction_fixture()
    actions = data["findings"]["timber"]["wood_surfaces"][0]["own_point_actions"]
    if omission == "free-couple":
        actions[0]["own_free_moment_nmm"] = [0., 0., 0.]
    else:
        actions.pop()
    with pytest.raises(ValueError, match="complete bolt/wood wrench"):
        method.member_actions(field, data, member, geometry)


def exterior_case(monkeypatch, moment_error=0.):
    y = method.CUT_Y_MM
    actions = [
        {"id": "high", "point_xyz_mm": [1., y+1., 2.],
         "force_xyz_n": [4., 5., 6.], "free_couple_xyz_nmm": [7., 8., 9.]},
        {"id": "low", "point_xyz_mm": [0., y-1., 0.],
         "force_xyz_n": [-7., -5., -2.], "free_couple_xyz_nmm": [-5.+moment_error, -10., -3.]},
        {"id": "boundary", "point_xyz_mm": [0., y, 0.],
         "force_xyz_n": [3., 0., 0.], "free_couple_xyz_nmm": [0., 0., 0.]},
    ]
    monkeypatch.setattr(method, "member_actions", lambda *args: (deepcopy(actions), np.asarray([0., 0., -4.])))
    geometry = {"origin_xyz_mm": [0., y, 0.], "whole_center_xyz_mm": [0., y, 0.],
                "width_x_mm": 2., "height_z_mm": 4., "whole_volume_mm3": 32.,
                "portions": {"high": {"volume_mm3": 24., "center_xyz_mm": [0., y+.5, 0.]}}}
    binding = {"case_id": "coupled-toy", "state_id": "coupled-toy-state", "field": {"path": "toy"}}
    return binding, geometry


def test_complete_case_preserves_nonzero_normal_moments_and_torque(monkeypatch):
    binding, geometry = exterior_case(monkeypatch)
    row = method.case_result(binding, {}, {}, "toy", geometry, normal)
    assert row["whole_body_force_residual_n"] == pytest.approx([0., 0., 0.])
    assert row["whole_body_moment_residual_nmm"] == pytest.approx([0., 0., 0.])
    assert row["finished_high_portion_gravity_xyz_n"] == pytest.approx([0., 0., -3.])
    a, b = row["traces"]
    # High point's transported moment=(3,10,10), minus gravity moment
    # (1.5,0,0), then reorder xyz to the right-handed normalY/pZ/qX chart.
    assert a["required_cut_on_low_portion_n_nmm"] == pytest.approx([5., 3., 4., 10., 10., 1.5])
    assert b["required_cut_on_low_portion_n_nmm"] == pytest.approx([5., 3., 7., 10., 10., 1.5])
    for trace in (a, b):
        assert trace["normal_hull"]["minimum_tensile_normal_resultant_n"] == pytest.approx(7.5)
        affine = trace["affine_normal_equilibrium_field"]
        assert affine["maximum_tension_mpa"] == pytest.approx(4.65625)
        assert affine["maximum_compression_mpa"] == pytest.approx(3.40625)
        # Signed corner values independently fix both moment directions;
        # extrema alone would also pass after a reflected stress field.
        corners = {(r["p_z_mm"], r["q_x_mm"]): r["normal_stress_mpa"] for r in affine["corners"]}
        assert corners == pytest.approx({(-2., -1.): -2.84375, (-2., 1.): 4.65625,
                                         (2., -1.): -3.40625, (2., 1.): 4.09375})


def test_force_balanced_but_moment_unbalanced_case_is_rejected(monkeypatch):
    binding, geometry = exterior_case(monkeypatch, moment_error=.5)
    with pytest.raises(ValueError, match="whole-cleat force or moment balance"):
        method.case_result(binding, {}, {}, "toy", geometry, normal)
