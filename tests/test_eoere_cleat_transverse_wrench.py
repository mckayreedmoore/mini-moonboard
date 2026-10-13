from copy import deepcopy

import numpy as np
import pytest

from scripts import eoere_cleat_transverse_wrench as method

NORMAL_SOURCE = {
    "path": "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-split-closure.py",
    "sha256": "e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e",
}
normal = method.component.load(NORMAL_SOURCE, "test_current_cleat_normal").normal_bound


@pytest.mark.parametrize(("q", "tension", "peak"), [
    ([10., 0., 0., 0., 0., 0.], 10., 1.25),
    ([-10., 0., 0., 0., 0., 0.], 0., 0.),
    ([0., 7., -3., 11., 12., 0.], 6., 4.5),
    ([0., 7., -3., 11., 0., -8.], 2., 1.5),
    ([0., 7., -3., 11., 12., -8.], 6., 6.),
])
def test_normal_force_and_both_couples_with_independent_answers(q, tension, peak):
    row = method.normal_components(q, 2., 4., normal)
    assert row["normal_hull"]["minimum_tensile_normal_resultant_n"] == pytest.approx(tension)
    assert row["affine_normal_equilibrium_field"]["maximum_tension_mpa"] == pytest.approx(peak)
    assert row["normal_hull"]["unresolved_shear_shear_torque_n_n_nmm"] == q[1:4]
    assert row["perpendicular_tensile_allowable_mpa"] is row["fracture_or_complete_resistance_n"] is None


def action(point, force, couple=(0., 0., 0.), identity="toy"):
    return {"id": identity, "point_xyz_mm": list(point), "force_xyz_n": list(force), "free_couple_xyz_nmm": list(couple)}


def test_wrench_includes_transport_and_free_couple_and_is_translation_invariant():
    rows = [action([2., 1., 3.], [4., 5., 6.], [7., 8., 9.])]
    force, moment, ids = method.action_wrench(rows, [0., 0., 0.], 0., False)
    assert force.tolist() == [4., 5., 6.]
    assert moment.tolist() == [-2., 8., 15.]
    assert ids == ["toy"]
    shift = np.asarray([20., -30., 40.])
    moved = deepcopy(rows)
    moved[0]["point_xyz_mm"] = (np.asarray(rows[0]["point_xyz_mm"])+shift).tolist()
    observed = method.action_wrench(moved, shift, shift[1], False)
    assert np.allclose(observed[0], force) and np.allclose(observed[1], moment)


def test_point_trace_ownership_keeps_both_limits():
    rows = [action([0., -1., 0.], [1., 0., 0.], identity="low"),
            action([0., 0., 0.], [2., 0., 0.], identity="boundary"),
            action([0., 1., 0.], [4., 0., 0.], identity="high")]
    low = method.action_wrench(rows, [0., 0., 0.], 0., False)
    high = method.action_wrench(rows, [0., 0., 0.], 0., True)
    assert low[0].tolist() == [4., 0., 0.] and high[0].tolist() == [6., 0., 0.]
    assert low[2] == ["high"] and high[2] == ["boundary", "high"]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1., 0.])
def test_invalid_rectangle_rejected(bad):
    with pytest.raises(ValueError):
        method.normal_components([1., 0., 0., 0., 0., 0.], bad, 4., normal)


def test_invalid_point_action_rejected():
    with pytest.raises(ValueError):
        method.action_wrench([action([0., 1., 0.], [0., float("nan"), 0.])], [0., 0., 0.], 0., False)


def test_finished_section_and_mass_first_moments_are_exact():
    import cadquery as cq

    solid = cq.Solid.makeBox(2., 4., 6., cq.Vector(10., 20., 30.))
    g = method.section_geometry(solid, cq, 21.)
    assert g["area_mm2"] == pytest.approx(12.)
    assert g["width_x_mm"] == pytest.approx(2.) and g["height_z_mm"] == pytest.approx(6.)
    assert g["origin_xyz_mm"] == pytest.approx([11., 21., 33.])
    assert g["portions"]["high"]["volume_mm3"] == pytest.approx(36.)
    assert g["portions"]["high"]["center_xyz_mm"] == pytest.approx([11., 22.5, 33.])
    assert g["portions"]["low"]["volume_mm3"] == pytest.approx(12.)


def test_cut_hole_and_outside_cut_are_rejected():
    import cadquery as cq

    solid = cq.Solid.makeBox(20., 40., 60.)
    bored = solid.cut(cq.Solid.makeCylinder(2., 40., cq.Vector(10., 0., 30.), cq.Vector(0., 1., 0.)))
    with pytest.raises(ValueError, match="rectangular"):
        method.section_geometry(bored, cq, 21.)
    with pytest.raises(ValueError, match="interior"):
        method.section_geometry(solid, cq, 50.)


def case_fixture(monkeypatch, imbalance=False):
    y = method.CUT_Y_MM
    actions = [action([0., y-1., 0.], [-3., -10., 2.], [0., 0., 3.], "low"),
               action([0., y+1., 0.], [0., 10., 2.], identity="high"),
               action([0., y, 0.], [3., 0., 0.], identity="boundary")]
    if imbalance:
        actions[0]["force_xyz_n"][0] += 1.
    gravity = np.asarray([0., 0., -4.])
    monkeypatch.setattr(method, "member_actions", lambda *args: (actions, gravity))
    geometry = {"origin_xyz_mm": [0., y, 0.], "whole_center_xyz_mm": [0., y, 0.],
                "width_x_mm": 2., "height_z_mm": 4., "whole_volume_mm3": 32.,
                "portions": {"high": {"volume_mm3": 16., "center_xyz_mm": [0., y+1., 0.]}}}
    return {"case_id": "toy", "state_id": "toy-state", "field": {"path": "toy"}}, geometry


def test_case_uses_partial_finished_gravity_and_keeps_tangential_trace_difference(monkeypatch):
    binding, geometry = case_fixture(monkeypatch)
    row = method.case_result(binding, {}, {}, "toy", geometry, normal)
    assert row["whole_body_force_residual_n"] == pytest.approx([0., 0., 0.])
    assert row["whole_body_moment_residual_nmm"] == pytest.approx([0., 0., 0.])
    assert row["finished_high_portion_gravity_xyz_n"] == pytest.approx([0., 0., -2.])
    a, b = row["traces"]
    assert a["required_cut_on_low_portion_n_nmm"] == pytest.approx([10., 0., 0., 0., 0., 0.])
    assert b["required_cut_on_low_portion_n_nmm"] == pytest.approx([10., 0., 3., 0., 0., 0.])
    assert a["normal_hull"]["minimum_tensile_normal_resultant_n"] == b["normal_hull"]["minimum_tensile_normal_resultant_n"] == 10.


def test_unbalanced_case_fails_original_gate(monkeypatch):
    binding, geometry = case_fixture(monkeypatch, imbalance=True)
    with pytest.raises(ValueError, match="balance"):
        method.case_result(binding, {}, {}, "toy", geometry, normal)
