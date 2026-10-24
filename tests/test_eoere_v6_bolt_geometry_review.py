"""Exercise the actual current-review seam with independent wrench controls."""

import copy

import numpy as np
import pytest

from scripts import eoere_bolt_outer_geometry as outer
from scripts.eoere_v6_bolt_geometry_review import lateral_endpoints, occurrence


def coupon(force, moment=(0., 0., 0.)):
    profile = outer.outer_profile({
        "member": "coupon", "datum_xyz_mm": [0., 0., 0.],
        "basis_grain_u_v_xyz": np.eye(3).tolist(),
        "raw_profile_vertices_luv_mm": [[l, u, v] for l in (0., 200.) for u in (0., 40.) for v in (0., 120.)],
    })
    surface = {"kind": "wood", "host": "coupon", "interval_mm": [0., 40.]}
    shaft = {"axis_id": "own", "point": [100., 0., 30.],
             "basis": [[0., 1., 0.]], "diameter_mm": 10., "surfaces": [surface]}
    action = {"axis_id": "own", "host": "coupon", "surface_interval_mm": [0., 40.],
              "surface_index": 0, "point_xyz_mm": [100., 20., 30.],
              "force_on_host_xyz_n": list(force), "moment_on_host_at_point_xyz_nmm": list(moment)}
    return profile, shaft, surface, action


def test_actual_review_seam_does_not_call_oblique_short_edge_a_classified_failure():
    args = coupon([100., 37., -100.])
    result = occurrence(*args, None)
    assert result["placement"]["minimum_outer_edge_distance_mm"] == 30.
    assert result["placement"]["full_4D_outer_edge_marker_pass"] is False
    assert result["load_classification"]["direction"] == "oblique"
    assert result["edge_rule"]["status"] == "unresolved"
    assert result["component_status"] == "UNRESOLVED"
    assert result["complete_Cdelta"] is None
    assert result["complete_joint_qualified"] is False
    assert result["wrench"]["axial_force_N"] == 37.


def test_principal_perpendicular_short_loaded_edge_still_fails_the_same_review():
    result = occurrence(*coupon([0., 37., -100.]), None)
    assert result["load_classification"]["direction"] == "perpendicular"
    assert result["edge_rule"]["required_mm"] == [40., 15.]
    assert result["edge_rule"]["status"] == "fail"
    assert result["component_status"] == "FAIL"
    assert result["complete_Cdelta"] is None


def test_pure_bore_couple_is_retained_and_cannot_be_classified_as_an_unloaded_pass():
    result = occurrence(*coupon([0., 0., 0.], [1200., 0., 0.]), None)
    assert result["load_classification"]["reversal"] is True
    assert result["component_status"] == "UNRESOLVED"
    assert result["wrench"]["own_free_couple_xyz_Nmm"] == [1200., 0., 0.]
    assert result["wrench"]["force_reconstruction_error_N"] < 1e-7
    assert result["wrench"]["moment_reconstruction_error_Nmm"] < 1e-5


def test_affine_force_and_first_moment_have_independent_known_integrals():
    _, shaft, surface, action = coupon([80., 19., 40.], [400., 0., -200.])
    first, last, result = lateral_endpoints(shaft, surface, action)
    length = 40.
    np.testing.assert_allclose((first + last) * length / 2, [80., 0., 40.], atol=1e-12)
    observed = np.cross([0., 1., 0.], (last - first) * length**2 / 12)
    np.testing.assert_allclose(observed, [400., 0., -200.], atol=1e-12)
    assert result["axial_force_N"] == 19.


@pytest.mark.parametrize("mismatch", ["axis", "host", "interval", "point", "nonfinite"])
def test_foreign_or_invalid_wrench_cannot_reach_the_geometry_rule(mismatch):
    _, shaft, surface, action = copy.deepcopy(coupon([80., 19., 40.]))
    if mismatch == "axis":
        action["axis_id"] = "other"
    elif mismatch == "host":
        action["host"] = "other"
    elif mismatch == "interval":
        action["surface_interval_mm"] = [0., 30.]
    elif mismatch == "point":
        action["point_xyz_mm"][1] += 1.
    else:
        action["force_on_host_xyz_n"][2] = float("nan")
    with pytest.raises(ValueError):
        lateral_endpoints(shaft, surface, action)
