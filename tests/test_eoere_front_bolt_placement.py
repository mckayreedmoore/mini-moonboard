from copy import deepcopy

import numpy as np
import pytest

from scripts import eoere_front_bolt_placement as method
from scripts.thin_bolted_timber_resistance import end_geometry_factor


def coupon():
    profile = {"basis_grain_u_v_xyz": np.eye(3).tolist(), "datum_xyz_mm": [0., 0., 0.],
               "raw_profile_vertices_luv_mm": [[l, u, v] for l in (0., 300.) for u in (0., 40.) for v in (0., 140.)],
               "end_cut_planes": [{"outward_normal_luv": [-1., 0., 0.], "offset_from_datum_mm": 0.},
                                  {"outward_normal_luv": [1., 0., 0.], "offset_from_datum_mm": 300.}]}
    shaft = {"axis_id": "toy", "basis": [[0., 1., 0.]], "point": [100., 0., 70.], "diameter_mm": 10.}
    surface = {"host": "toy_member", "interval_mm": [0., 40.]}
    return profile, shaft, surface


def test_full_value_placement_does_not_adopt_group_factor():
    row = method.placement(*coupon(), end_geometry_factor)
    assert [e["minimum_axis_to_end_along_grain_mm"] for e in row["grain_end_distances"]] == [100., 200.]
    assert row["outer_edge_distances_mm"] == [70., 70.]
    assert row["full_value_end_and_outer_edge_screen_pass"] is True
    assert row["complete_Cdelta"] is row["Cg"] is row["complete_joint_resistance"] is None


def test_reduced_end_factor_and_below_minimum_are_distinct():
    profile, shaft, surface = coupon()
    shaft["point"][0] = 60.
    row = method.placement(profile, shaft, surface, end_geometry_factor)
    assert row["conservative_end_component"]["end_factor_only"] == pytest.approx(6/7)
    assert not row["full_value_end_and_outer_edge_screen_pass"]
    shaft["point"][0] = 34.
    row = method.placement(profile, shaft, surface, end_geometry_factor)
    assert row["conservative_end_component"]["status"] == "below_minimum"
    assert row["conservative_end_component"]["end_factor_only"] is None


def test_reversed_load_cannot_hide_an_inadequate_outer_edge():
    profile, shaft, surface = coupon()
    shaft["point"][2] = 39.
    row = method.placement(profile, shaft, surface, end_geometry_factor)
    assert row["minimum_outer_edge_4D_margin_mm"] == -1.
    assert not row["full_value_end_and_outer_edge_screen_pass"]


def test_rotated_translated_reversed_shaft_is_invariant():
    profile, shaft, surface = coupon()
    expected = method.placement(profile, shaft, surface, end_geometry_factor)
    rotation = np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]])
    shift = np.array([123., -456., 789.])
    profile["basis_grain_u_v_xyz"] = rotation.T.tolist()
    profile["datum_xyz_mm"] = shift.tolist()
    shaft["point"] = (rotation @ np.array([100., 40., 70.])+shift).tolist()
    shaft["basis"] = [(rotation @ np.array([0., -1., 0.])).tolist()]
    observed = method.placement(profile, shaft, surface, end_geometry_factor)
    assert observed["grain_end_distances"] == expected["grain_end_distances"]
    assert observed["outer_edge_distances_mm"] == expected["outer_edge_distances_mm"]


def test_oblique_end_is_intersected_along_grain():
    profile, shaft, surface = coupon()
    normal = np.array([1., 0., -.5])/np.sqrt(1.25)
    profile["end_cut_planes"][1] = {"outward_normal_luv": normal.tolist(), "offset_from_datum_mm": 300./np.sqrt(1.25)}
    row = method.placement(profile, shaft, surface, end_geometry_factor)
    assert row["grain_end_distances"][1]["minimum_axis_to_end_along_grain_mm"] == pytest.approx(235.)


@pytest.mark.parametrize("corrupt", ["parallel_shaft", "outside_interval", "nonfinite_profile", "wrong_end_normal"])
def test_incompatible_geometry_is_rejected(corrupt):
    profile, shaft, surface = deepcopy(coupon())
    if corrupt == "parallel_shaft":
        shaft["basis"][0] = [1., 0., 0.]
    elif corrupt == "outside_interval":
        surface["interval_mm"] = [-1., 40.]
    elif corrupt == "nonfinite_profile":
        profile["datum_xyz_mm"][0] = float("nan")
    else:
        profile["end_cut_planes"][0]["outward_normal_luv"] = [1., 0., 0.]
    with pytest.raises(ValueError):
        method.placement(profile, shaft, surface, end_geometry_factor)


def test_finished_boundary_census_rejects_added_external_notch():
    import cadquery as cq

    profile, _, _ = coupon()
    shape = cq.Workplane("XY").box(300., 40., 140., centered=(False, False, False)).val()
    for x in (90., 120., 180., 210.):
        shape = shape.cut(cq.Solid.makeCylinder(2., 40., cq.Vector(x, 0., 70.), cq.Vector(0., 1., 0.)))
    assert method.confirm_outer_faces(shape, method.outer_planes(profile))["all_six_exterior_planes_match"]
    notched = shape.cut(cq.Solid.makeBox(10., 40., 10., cq.Vector(50., 0., 130.)))
    with pytest.raises(ValueError, match="exterior plane"):
        method.confirm_outer_faces(notched, method.outer_planes(profile))
