"""Analytical vector, signed-wrench and continuous-bending method checks."""

import copy
import math

import numpy as np
import pytest

from scripts import eoere_joint_vector_tests as method


def couple_fixture():
    surfaces = [{"interval": [0., 1.], "cap": 1., "force": [1., 0.], "first_moment": [0., 0.]},
                {"interval": [1., 2.], "cap": 1., "force": [-1., 0.], "first_moment": [0., 0.]}]
    points = [{"s": 2., "force": [0., 0.], "couple": [0., 1.]}]
    caps = [{"interval": [0., 2.], "cap": 100.}]
    return surfaces, points, [0., 2.], caps


def test_signed_member_loads_and_their_couples_are_retained():
    surfaces, points, domain, caps = couple_fixture()
    result = method.solve(surfaces, points, domain, caps, cells=2)
    assert result["certified_raw_reference_index"] == pytest.approx(1.)
    assert [r["density_yz"] for r in result["cells"]] == pytest.approx(np.array([[1., 0.], [1., 0.], [-1., 0.], [-1., 0.]]))
    assert result["maximum_member_force_error_n"] < 1e-12
    assert result["maximum_member_first_moment_error_nmm"] < 1e-12
    assert result["end_moment_error_nmm"] < 1e-12
    assert result["physical_compatibility"] is False
    assert result["adjusted_capacity"] is None
    assert result["complete_joint_resistance"] is None
    assert method.verify_witness(surfaces, points, domain, caps, result)["independently_checked_cells"] == 4


def test_diagonal_load_checks_vector_norm_instead_of_component_maximum():
    surfaces, points, domain, caps = couple_fixture()
    for s in surfaces:
        s["force"][1] = s["force"][0]
    points[0]["couple"] = [-1., 1.]
    result = method.solve(surfaces, points, domain, caps, cells=2)
    assert result["certified_raw_reference_index"] == pytest.approx(math.sqrt(2.))
    assert result["raw_bearing_index"] == pytest.approx(math.sqrt(2.))
    method.verify_witness(surfaces, points, domain, caps, result)


@pytest.mark.parametrize("scale", [1e-10, 1e-8, 1e-4, 1e4])
def test_small_and_large_prescribed_actions_are_not_lost_to_absolute_solver_tolerance(scale):
    surfaces, points, domain, caps = couple_fixture()
    for surface in surfaces:
        surface["force"] = (scale*np.asarray(surface["force"])).tolist()
    points[0]["couple"] = [0., scale]
    result = method.solve(surfaces, points, domain, caps, cells=2)
    assert result["certified_raw_reference_index"] == pytest.approx(scale, rel=1e-8, abs=1e-22)
    assert result["cells"][0]["density_yz"][0] == pytest.approx(scale, rel=1e-8, abs=1e-22)
    assert result["maximum_member_force_error_n"] <= scale*1e-8
    method.verify_witness(surfaces, points, domain, caps, result)


@pytest.mark.parametrize("angle", [.1, .31, .7])
def test_inscribed_polygon_bounds_the_circular_reference(angle):
    surfaces, points, domain, caps = couple_fixture()
    direction = np.array([math.cos(angle), math.sin(angle)])
    for s in surfaces:
        s["force"] = (s["force"][0]*direction).tolist()
    points[0]["couple"] = [-direction[1], direction[0]]
    result = method.solve(surfaces, points, domain, caps, cells=2, facets=16)
    assert 1.-1e-12 <= result["certified_raw_reference_index"] <= 1./math.cos(math.pi/16.)+1e-12
    assert result["raw_bearing_index"] == pytest.approx(1.)
    method.verify_witness(surfaces, points, domain, caps, result)


def test_body_root_transition_and_both_sides_of_tip_couple_are_checked():
    surfaces, points, domain, _ = couple_fixture()
    caps = [{"interval": [0., 1.5], "cap": 100.}, {"interval": [1.5, 2.], "cap": .5}]
    result = method.solve(surfaces, points, domain, caps, cells=2)
    assert result["certified_raw_reference_index"] == pytest.approx(2.)
    assert result["continuous_raw_bending_index"] == pytest.approx(2.)
    assert any(r["low"] == 1.5 for r in result["cells"])
    method.verify_witness(surfaces, points, domain, caps, result)


def test_interior_bending_peak_adds_a_constraint():
    surfaces = [{"interval": [0., 10.], "cap": 1., "force": [10., 0.], "first_moment": [0., 0.]},
                {"interval": [10., 11.], "cap": 1., "force": [0., 0.], "first_moment": [0., 0.]}]
    points = [{"s": 0., "force": [-7., 0.], "couple": [0., 0.]},
              {"s": 10., "force": [-3., 0.], "couple": [0., -20.]}]
    result = method.solve(surfaces, points, [0., 11.], [{"interval": [0., 11.], "cap": 1.}], cells=2)
    assert result["cut_rounds"] >= 2
    assert result["certified_raw_reference_index"] == pytest.approx(24.5)
    worst = max(result["continuous_segments"], key=lambda s: s["raw_index"])
    assert worst["maximum_bending"]["station_mm"] == pytest.approx(7.)
    assert result["end_force_error_n"] < 1e-12
    assert result["end_moment_error_nmm"] < 1e-12
    method.verify_witness(surfaces, points, [0., 11.], [{"interval": [0., 11.], "cap": 1.}], result)


def test_omitting_an_applied_couple_cannot_pass_end_balance():
    surfaces, points, domain, caps = couple_fixture()
    points[0]["couple"] = [0., 0.]
    with pytest.raises(ValueError, match="end balance"):
        method.solve(surfaces, points, domain, caps, cells=2)


def test_continuous_facet_projection_is_checked_even_when_circular_norm_fits():
    direction = np.array([math.cos(.3), math.sin(.3)])
    surfaces = [{"interval": [a, b], "cap": 1., "force": ((b-a)*direction).tolist(), "first_moment": [0., 0.]}
                for a, b in [(0., 5.), (5., 8.), (8., 10.)]]
    surfaces.append({"interval": [10., 11.], "cap": 1., "force": [0., 0.], "first_moment": [0., 0.]})
    points = [{"s": 0., "force": (-7.*direction).tolist(), "couple": [0., 0.]},
              {"s": 10., "force": (-3.*direction).tolist(), "couple": [20.*direction[1], -20.*direction[0]]}]
    domain, caps = [0., 11.], [{"interval": [0., 11.], "cap": 1.}]
    result = method.solve(surfaces, points, domain, caps, cells=2, facets=8)
    normals = np.array([[math.cos((2*k+1)*math.pi/8), math.sin((2*k+1)*math.pi/8)] for k in range(8)])
    scale = max(normals@np.array([-direction[1], direction[0]]))/math.cos(math.pi/8)
    assert result["LP_reference_index"] == pytest.approx(24.5*scale)
    assert result["cut_rounds"] >= 2
    assert result["continuous_raw_bending_index"] == pytest.approx(24.5)
    method.verify_witness(surfaces, points, domain, caps, result)
    # This smaller index still contains the circular field but misses a facet.
    result["LP_reference_index"] = result["certified_raw_reference_index"] = 24.5
    with pytest.raises(ValueError, match="continuous polygon"):
        method.verify_witness(surfaces, points, domain, caps, result)


@pytest.mark.parametrize("change", ["overlap", "gap_in_caps", "negative_cap", "force_unbalance", "nonfinite", "facets"])
def test_invalid_own_inputs_are_rejected(change):
    surfaces, points, domain, caps = copy.deepcopy(couple_fixture())
    facets = 16
    if change == "overlap":
        surfaces[1]["interval"][0] = .5
    elif change == "gap_in_caps":
        caps[0]["interval"][0] = .1
    elif change == "negative_cap":
        surfaces[0]["cap"] = -1.
    elif change == "force_unbalance":
        surfaces[0]["force"][0] = 2.
    elif change == "nonfinite":
        surfaces[0]["first_moment"][0] = float("nan")
    elif change == "facets":
        facets = 10
    with pytest.raises(ValueError):
        method.solve(surfaces, points, domain, caps, cells=2, facets=facets)


@pytest.mark.parametrize("change", ["density", "interval", "cap", "surface", "couple", "root", "claim", "index"])
def test_independent_dimensional_checker_rejects_changed_witness_or_demand(change):
    surfaces, points, domain, caps = couple_fixture()
    result = method.solve(surfaces, points, domain, caps, cells=2)
    if change == "density":
        result["cells"][0]["density_yz"][0] += .01
    elif change == "interval":
        result["cells"][0]["high"] -= .01
    elif change == "cap":
        result["cells"][0]["cap"] *= 2.
    elif change == "surface":
        result["cells"][0]["surface"] = 1
    elif change == "couple":
        points[0]["couple"][1] = 0.
    elif change == "root":
        caps[0]["cap"] = .01
    elif change == "claim":
        result["complete_joint_resistance"] = 1.
    elif change == "index":
        result["certified_raw_reference_index"] /= 2.
    with pytest.raises(ValueError):
        method.verify_witness(surfaces, points, domain, caps, result)


def adapter_fixture():
    shaft = {"axis_id": "fixture", "basis": [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]],
             "point": [10., 20., 30.], "shaft_interval_mm": [0., 3.],
             "surfaces": [{"host": str(i), "kind": "wood", "interval_mm": [float(i), float(i+1)]} for i in range(3)]}
    trials = []
    for i, s in enumerate(shaft["surfaces"]):
        # Own host field q_x=2+3*(s-mid) gives F_x=2, M_y=3/12.
        trials.append({"axis_id": "fixture", "surface_index": i, "host": s["host"], "kind": s["kind"],
                       "interval_from_axis_point_mm": s["interval_mm"],
                       "lateral_force_on_host_xyz_n": [2., 0., 0.],
                       "moment_on_host_about_interval_center_xyz_nmm": [0., .25, 0.],
                       "affine_endpoint_line_density_vectors_n_mm": [[.5, 0., 0.], [3.5, 0., 0.]]})
    reference = {"axis_id": "fixture", "raw_bearing_trials": [
        {"surface_index": i, "host": str(i), "kind": "wood", "raw_bearing_reference_n_mm": 5.} for i in range(3)],
        "continuous_bending_segments": [{"interval_mm": [0., 3.], "raw_plastic_moment_reference_nmm": 10.}]}
    loads = [{"id": "metal", "point_xyz_mm": [12., 23., 31.], "force_xyz_n": [4., 5., 6.],
              "moment_xyz_nmm": [7., 8., 9.]}]
    return shaft, trials, loads, reference


def test_current_adapter_preserves_host_sign_centered_couple_and_off_axis_gravity():
    source = adapter_fixture()
    result = method.current_stack_inputs(*source)
    assert result["surfaces"][0]["force"] == [-2., 0.]
    assert result["surfaces"][0]["first_moment"] == [-.25, 0.]
    assert result["points"] == [{"s": 1., "force": [4., 5.], "couple": [25., -4.]}]
    assert result["separate_axial_gravity_and_torque"] == [{"id": "metal", "axial_force_n": 6., "axial_torque_nmm": 7.}]
    assert source == adapter_fixture()


@pytest.mark.parametrize("change", ["basis", "member", "interval", "affine_couple", "reference"])
def test_current_adapter_rejects_bad_own_joins(change):
    shaft, trials, loads, reference = adapter_fixture()
    if change == "basis":
        shaft["basis"][2][1] = -1.
    elif change == "member":
        trials[0]["host"] = "other"
    elif change == "interval":
        trials[0]["interval_from_axis_point_mm"] = [0., 2.]
    elif change == "affine_couple":
        trials[0]["moment_on_host_about_interval_center_xyz_nmm"][1] = 0.
    elif change == "reference":
        reference["raw_bearing_trials"][0]["host"] = "other"
    with pytest.raises(ValueError):
        method.current_stack_inputs(shaft, trials, loads, reference)
