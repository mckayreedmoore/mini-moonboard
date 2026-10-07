"""Independent polynomial recovery, same-state identity and force signs."""

import copy
import hashlib
import json
import math

import numpy as np
import pytest

from scripts.thin_bolted_panel_coupled import (
    COEFFICIENT_ORDER,
    FLOOR_BASIS,
    FLOOR_SHA,
    coefficient_slice,
    deformation_diagnostics,
    integrated_net_diagnostics,
    plate_fields,
    screw_references,
    validate_state,
)
from scripts.thin_bolted_panel_mechanics import CAT, SheetBasis


def polynomial_panel():
    basis = SheetBasis(120., 80., 3)
    points = np.array([(x, y) for x in np.linspace(0, 120, basis.order)
                       for y in np.linspace(0, 80, basis.order)])
    interpolation = basis.values(points)
    x, y = points.T
    values = [1. + .002 * x + .003 * y, 2. - .001 * x + .004 * y,
              3. + .01 * x - .02 * y + .0005 * x**2 + .0003 * y**2 + .0002 * x * y]
    q = np.concatenate([np.linalg.solve(interpolation, value) for value in values])
    return {"basis": basis, "thickness": CAT, "twist_scale": 1., "holes": [],
            "geometry": {"name": "known_answer", "front_height": 80.}}, q


def test_recovery_matches_independent_signed_polynomial_fields():
    panel, q = polynomial_panel()
    x, y = 47., 29.
    fields = plate_fields(panel, np.array([[x, y]]), q)
    force = 4.4482216152605
    ea_x, ea_y = 5100000 * force / 304.8, 3150000 * force / 304.8
    ei_x, ei_y = 320000 * force * 25.4**2 / 304.8, 90500 * force * 25.4**2 / 304.8
    ga = 50500 * force / 25.4
    twist = ga * CAT**2 / 12
    expected = {"u_mm": 1. + .002 * x + .003 * y,
                "v_mm": 2. - .001 * x + .004 * y,
                "outward_w_mm": 3. + .01 * x - .02 * y + .0005 * x**2 + .0003 * y**2 + .0002 * x * y,
                "slope_x": .01 + .001 * x + .0002 * y,
                "slope_upslope": -.02 + .0006 * y + .0002 * x,
                "membrane_x_n_per_mm": ea_x * .002,
                "membrane_upslope_n_per_mm": ea_y * .004,
                "membrane_xy_n_per_mm": ga * .002,
                "bending_x_nmm_per_mm": -ei_x * .001,
                "bending_upslope_nmm_per_mm": -ei_y * .0006,
                "twisting_xy_nmm_per_mm": -2 * twist * .0002,
                "rolling_x_n_per_mm": 0., "rolling_upslope_n_per_mm": 0.}
    for key, value in expected.items():
        assert fields[key][0] == pytest.approx(value, rel=1e-10, abs=1e-7)


def test_deformation_uses_actual_field_and_derivative_bounds():
    panel, q = polynomial_panel()
    row = deformation_diagnostics(panel, q, 41)
    # This quadratic reaches its maximum at the far corner: 14.36 mm.
    expected = 3 + 1.2 - 1.6 + 7.2 + 1.92 + 1.92
    assert row["maximum_sampled_abs_outward_w_mm"] == pytest.approx(expected)
    assert row["maximum_sampled_abs_w_over_panel_height"] == pytest.approx(expected / 80)
    assert row["absolute_outward_w_coefficient_convex_hull_bound_mm"] >= expected - 1e-12
    assert row["maximum_sampled_slope_norm"] == pytest.approx(math.hypot(.146, .052))
    assert row["absolute_slope_x_derivative_coefficient_bound"] == pytest.approx(.146)
    assert row["absolute_slope_upslope_derivative_coefficient_bound"] >= .052 - 1e-12
    assert row["linear_plate_applicability_established"] is False


def test_rigid_affine_motion_has_zero_warp_and_bending():
    panel, q = polynomial_panel()
    basis = panel["basis"]
    points = np.array([(x, y) for x in np.linspace(0, 120, basis.order)
                       for y in np.linspace(0, 80, basis.order)])
    q[2 * basis.size:] = np.linalg.solve(basis.values(points), 21 + .4 * points[:, 0] - .3 * points[:, 1])
    row = deformation_diagnostics(panel, q)
    assert row["maximum_sampled_affine_removed_warp_mm"] < 1e-12
    assert row["maximum_sampled_slope_norm"] == pytest.approx(.5)
    fields = plate_fields(panel, np.array([[30., 27.]]), q)
    assert fields["bending_x_nmm_per_mm"][0] == pytest.approx(0., abs=1e-7)
    assert fields["bending_upslope_nmm_per_mm"][0] == pytest.approx(0., abs=1e-7)


def test_saved_basis_and_global_slice_reject_mixed_coefficients():
    panel, q = polynomial_panel()
    basis = panel["basis"]
    state = {"parameters": {"panel_intervals": 3}, "response": {"q": [9., *q.tolist()]},
             "panel_generalized_coefficients": {"known": {
                 "width_mm": 120., "height_mm": 80., "basis_order_per_direction": basis.order,
                 "knots_normalized": basis.knots.tolist(), "coefficient_order": COEFFICIENT_ORDER,
                 "global_dof_start": 1, "coefficients_mm": q.tolist()}}}
    assert coefficient_slice(state, "known")[1] == pytest.approx(q)
    mixed = copy.deepcopy(state)
    mixed["panel_generalized_coefficients"]["known"]["coefficients_mm"][5] += .001
    with pytest.raises(ValueError, match="global field slice"):
        coefficient_slice(mixed, "known")
    mixed = copy.deepcopy(state)
    mixed["panel_generalized_coefficients"]["known"]["coefficient_order"] = "w,v,u"
    with pytest.raises(ValueError, match="ordering"):
        coefficient_slice(mixed, "known")


def test_finished_state_identity_and_simultaneous_actions_are_required():
    state = {"case_id": "a12-rear", "accessory_placement": "retained-original-top-hold",
             "geometry_cache_sha256": "geometry", "parameters": {
                 "floor_support_basis": FLOOR_BASIS, "floor_contact_geometry_sha256": FLOOR_SHA},
             "response": {"converged": True}, "usable_conditional_actions": True,
             "equilibrium_verification": {"all_body_and_global_checks_pass": True},
             "release": {"climbing_released": False}, "panel_screw_actions": [], "contact_actions": []}
    identity = {key: state[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    state["state_id"] = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True,
                                                             separators=(",", ":")).encode()).hexdigest()[:24]
    validate_state(state)
    mixed = copy.deepcopy(state)
    mixed["panel_screw_actions"] = [{"state_id": "another", "case_id": "a12-rear",
                                    "accessory_placement": state["accessory_placement"]}]
    with pytest.raises(ValueError, match="mixed"):
        validate_state(mixed)
    state["parameters"].pop("floor_support_basis")
    with pytest.raises(ValueError, match="raw-floor"):
        validate_state(state)


def test_same_axis_generic_head_and_thread_references_do_not_combine_peaks():
    row = {"withdrawal_n": 600., "lateral_n": 50., "local_force_n": [600., 30., -40.]}
    reference = screw_references(row, CAT)
    force = 4.4482216152605
    assert reference["same_axis_simultaneous_lateral_n"] == 50.
    assert reference["generic_withdrawal_required_effective_thread_mm_CD1"] == pytest.approx(
        600 / (2850 * .5**2 * .190 * force / 25.4))
    assert reference["projected_annulus_mean_pressure_mpa"] == pytest.approx(600 / (math.pi * 14))
    assert reference["generic_head_reference_n_CD1"] == pytest.approx(580.2924076360686)
    assert reference["Hillman_product_capacity_or_stiffness_established"] is False
    with pytest.raises(ValueError, match="simultaneous"):
        screw_references({**row, "lateral_n": 51.}, CAT)


def test_net_integrals_preserve_signed_coupled_polynomial_actions():
    panel, q = polynomial_panel()
    result = integrated_net_diagnostics(panel, q, 4)
    witness = result["simultaneous_signed_cut_witnesses"]["mean_net_bending_ratio_CD1"]
    force = 4.4482216152605
    dx = 320000 * force * 25.4**2 / 304.8
    dy = 90500 * force * 25.4**2 / 304.8
    expected = -dx * .001 * 80 if witness["cut_axis"] == "x" else -dy * .0006 * 120
    assert witness["signed_bending_nmm"] == pytest.approx(expected, rel=1e-10)
    assert witness["signed_rolling_shear_n"] == pytest.approx(0., abs=1e-6)
    assert result["local_hole_seat_edge_or_hold_capacity_accepted"] is False
