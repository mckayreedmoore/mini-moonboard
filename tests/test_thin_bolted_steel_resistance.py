"""Independent arithmetic, published example and washer-equilibrium fixtures."""

import json
import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from mini_moonboard.washer_plate_response import uniform_pressure_clamped_annulus
from scripts import thin_bolted_steel_resistance as steel
from scripts.thin_bolted_frame_mechanics import beam_stiffness, rectangular_torsion


def test_same_section_axial_bending_and_centered_hole_geometry():
    result = steel.section_reference(width_mm=20., thickness_mm=2.,
        removed_center_width_mm=4., force_local_n=(320., 0., 0.),
        moment_local_nmm=(0., 64., 264.), fy_mpa=100.)
    # A=32, Zout=16*4/6, Zin=2*(20^3-4^3)/(6*20).
    assert result["nominal_normal_stress_envelope_mpa"] == pytest.approx(10+6+264/132.26666666666668)
    assert result["nominal_first_yield_index"] == pytest.approx(.17995967741935484)
    assert result["complete_joint_acceptance"] is False


def test_same_section_bolt_bending_is_not_replaced_with_t_over_a():
    d = 10.
    result = steel.bolt_section_reference(force_n=(100., 0., 0.),
        moment_nmm=(0., 1000., 0.), diameter_mm=d, fy_mpa=200.,
        material_basis="synthetic200MPa", section_basis="synthetic solid circle")
    expected = 100/(math.pi*d*d/4)+32000/(math.pi*d**3)
    assert result["same_section_nominal_stress_envelope_mpa"] == pytest.approx(expected)
    assert result["same_section_nominal_stress_envelope_mpa"] > result["direct_reference"]["interaction_equivalent_stress_mpa"]
    missing = steel.bolt_section_reference(force_n=(100., 0., 0.), moment_nmm=(0., 0., 0.),
        diameter_mm=10., fy_mpa=None, material_basis=None, section_basis=None)
    assert missing["same_section_nominal_first_yield_index"] is None


def test_all_factory_holes_limit_signed_clear_distance():
    args = {"length_mm":104.775, "width_mm":41.275, "hole_mm":14.2875,
            "used_center_mm":84.1375, "other_centers_mm":[36.5125]}
    assert steel.hole_clear_distance(**args, direction_xy=(1., 0.)) == pytest.approx(13.49375)
    assert steel.hole_clear_distance(**args, direction_xy=(-1., 0.)) == pytest.approx(33.3375)
    assert steel.hole_clear_distance(**args, direction_xy=(0., 1.)) == pytest.approx(13.49375)
    result = steel.bearing_tearout_reference(clear_distance_mm=10., bolt_diameter_mm=12.7,
                                           thickness_mm=5., fu_mpa=400.)
    assert result["nominal_strength_n"] == 24000
    assert result["asd_component_reference_n"] == 12000


def test_published_aisc_2017_block_shear_example():
    # Engineering Journal54(3),2017,p189: Agv8.12in²,Anv5.39,Ant1.02,
    # Fy50ksi,Fu65ksi,phiRn207kips. Published rounded result is independent QA.
    area = 25.4**2
    result = steel.block_shear_reference(gross_shear_area_mm2=8.12*area,
        net_shear_area_mm2=5.39*area, net_tension_area_mm2=1.02*area,
        ubs=1., fy_mpa=50000*steel.PSI_TO_MPA, fu_mpa=65000*steel.PSI_TO_MPA,
        path_basis="published synthetic QA; not a candidate path")
    assert .75*result["nominal_strength_n"]/4448.2216152605 == pytest.approx(207, abs=.5)


def test_annulus_two_sided_moment_never_credits_tension_contact():
    p = steel.annulus_pressure(axial_n=100., moment_xy_nmm=(1000., 0.),
                              inner_radius_mm=5., outer_radius_mm=10.)
    assert p["pressure_min_mpa"] < 0
    assert p["full_contact_admissible"] is False
    assert p["moment_full_contact_limit_nmm"] == pytest.approx(312.5)
    end = steel.washer_two_sided_interaction(axial_n=100., moment_xy_nmm=(1000., 0.),
        inner_radius_mm=6., outer_radius_mm=14., bearing_radius_mm=11.,
        support_opening_radius_mm=7., thickness_mm=2., fy_mpa=None)
    assert end["both_full_contact_fields_admissible"] is False
    assert end["non_axisymmetric_bending_required"] is True
    assert end["combined_t_m_metal_yield_index"] is None


def test_flange_sampling_covers_unused_holes_and_contact_beyond_attached_hole():
    fitting = {"angle_id":"B104ZN_synthetic", "origin_xyz_mm":[0., 0., 0.],
               "u_xyz":[1., 0., 0.], "v_xyz":[0., 1., 0.], "w_xyz":[0., 0., 1.]}
    load = {"point_xyz_mm":[100., 0., 0.], "force_on_steel_xyz_n":[0., -100., 0.],
            "moment_on_steel_at_point_xyz_nmm":[0., 0., 0.]}
    result = steel.flange_reference(fitting, "beam", [load])
    stations = {r["station_from_assumed_corner_mm"] for r in result["sections"]}
    assert {steel.THICKNESS, 36.5125, 84.1375, 100., 104.775} <= stations
    assert result["continuous_section_extrema_verified"] is False
    assert result["complete_joint_acceptance"] is False


def test_condensed_angle_known_answer_in_plane_tip_force():
    # Two-leg L-frame, fixed post end, F along post axis at beam end. Castigliano:
    # F*[Lb³/(3EI)+Lb²Lp/(EI)+Lb/(kGA)+Lp/(EA)]. The straight-beam legs carry
    # respectively shear/bending and axial/constant-moment actions.
    fitting = {"angle_id":"B104ZN_synthetic", "origin_xyz_mm":[0., 0., 0.],
               "u_xyz":[1., 0., 0.], "v_xyz":[0., 1., 0.], "w_xyz":[0., 0., 1.]}
    result = steel.fitting_condensed_stiffness(fitting, beam_stiffness, rectangular_torsion)
    matrix = np.asarray(result["global_port_stiffness_n_mm_rad"])
    displacement = np.linalg.solve(matrix[:6, :6], [0., 100., 0., 0., 0., 0.])
    lb, lp = [r["centroid_length_mm"] for r in result["legs"]]
    section = result["section"]
    e, g = section["elastic_modulus_mpa"], section["elastic_modulus_mpa"]/(2*(1+section["nu"]))
    i, area = section["inertia_y_mm4"], section["area_mm2"]
    expected = 100*(lb**3/(3*e*i)+lb**2*lp/(e*i)+lb/((5/6)*g*area)+lp/(e*area))
    assert displacement[1] == pytest.approx(expected, rel=2e-12)
    assert result["actual_product_stiffness_verified"] is False


def test_condensed_angle_has_six_rigid_motions_and_net_sensitivity_softens():
    fitting = {"angle_id":"B103ZN_synthetic", "origin_xyz_mm":[5., 4., 3.],
               "u_xyz":[1., 0., 0.], "v_xyz":[0., 1., 0.], "w_xyz":[0., 0., 1.]}
    gross = steel.fitting_condensed_stiffness(fitting, beam_stiffness, rectangular_torsion)
    net = steel.fitting_condensed_stiffness(fitting, beam_stiffness, rectangular_torsion,
                                         section_scenario="net_section_full_leg")
    matrix = np.asarray(gross["global_port_stiffness_n_mm_rad"])
    for component in np.eye(3):
        translation = np.r_[component, np.zeros(3), component, np.zeros(3)]
        rotation = np.concatenate([np.r_[np.cross(component, p["point_xyz_mm"]), component]
                                   for p in gross["ports"]])
        for motion in (translation, rotation):
            assert np.linalg.norm(matrix @ motion)/(np.linalg.norm(matrix)*np.linalg.norm(motion)) < 2e-15
    # Scale rotations by representative L to assess numerical rigid rank.
    scaling = np.diag([1., 1., 1., .01, .01, .01]*2)
    eigen = np.linalg.eigvalsh(scaling @ matrix @ scaling)
    assert np.count_nonzero(eigen > np.max(eigen)*1e-8) == 6
    difference = scaling @ (matrix-np.asarray(net["global_port_stiffness_n_mm_rad"])) @ scaling
    assert min(np.linalg.eigvalsh(difference)) > -1e-6


def test_plate_basis_matches_existing_independent_clamped_annulus_helper():
    a, b, p, nu = 1., 10., 1., .3
    matrix = np.vstack((steel._plate_basis(a, nu)[:2], steel._plate_basis(b, nu)[:2]))
    rhs = -np.r_[steel._plate_particular(a, p, nu)[:2], steel._plate_particular(b, p, nu)[:2]]
    coefficients = np.linalg.solve(matrix, rhs)
    w = (steel._plate_basis(5., nu) @ coefficients + steel._plate_particular(5., p, nu))[0]
    known = uniform_pressure_clamped_annulus(inner_radius=a, outer_radius=b,
        flexural_rigidity=1., pressure=p, radius=5.)
    assert w == pytest.approx(known.deflection, rel=1e-12)


def test_two_face_washer_matches_independent_equilibrium_shooting():
    # Different method: integrate radial moment/slope directly using the
    # pressure integral for Q, instead of solving deflection-basis constants.
    a, s, c, b, thickness, nu, force = 6., 7., 11., 14., 2., .3, 100.
    result = steel.washer_axisymmetric_bending(axial_n=force, inner_radius_mm=a,
        outer_radius_mm=b, bearing_radius_mm=c, support_opening_radius_mm=s,
        thickness_mm=thickness, nu=nu)
    head = force/(math.pi*(c*c-a*a))
    support = force/(math.pi*(b*b-s*s))

    def ode(r, state):
        theta, mr = state
        # Applied positive head pressure and opposite support pressure.
        integral = head*(min(r, c)**2-a*a)/2 - support*max(0., r*r-s*s)/2
        qr = -integral/r
        return (-mr-nu*theta/r, (nu-1)*mr/r-(1-nu*nu)*theta/r**2+qr)

    def integrate(initial):
        return solve_ivp(ode, (a, b), (initial, 0.), rtol=1e-12, atol=1e-13,
                         max_step=.003, dense_output=True)

    zero, one = integrate(0.), integrate(1.)
    initial = -zero.y[1, -1]/(one.y[1, -1]-zero.y[1, -1])
    independent = integrate(initial)
    witness = result["sampled_bending_peak"]
    theta, mr = independent.sol(witness["radius_mm"])
    hoop = nu*mr-(1-nu*nu)*theta/witness["radius_mm"]
    radial_stress, hoop_stress = -6*mr/thickness**2, -6*hoop/thickness**2
    equivalent = math.sqrt(radial_stress**2-radial_stress*hoop_stress+hoop_stress**2)
    assert witness["von_mises_mpa"] == pytest.approx(equivalent, rel=2e-7)
    assert result["matrix_residual"] < 1e-10
    assert abs(result["outer_free_shear_residual_n_per_mm"]) < 1e-10


def test_identical_two_face_pressure_has_zero_bending_and_force_scaling():
    args = {"inner_radius_mm":6., "outer_radius_mm":14., "bearing_radius_mm":14.,
            "support_opening_radius_mm":6., "thickness_mm":2.}
    zero = steel.washer_axisymmetric_bending(axial_n=100., **args)
    assert zero["required_fy_mpa_at_sampled_bending_first_yield"] == pytest.approx(0., abs=1e-12)
    args["bearing_radius_mm"] = 11.
    one = steel.washer_axisymmetric_bending(axial_n=100., **args)
    doubled = steel.washer_axisymmetric_bending(axial_n=200., **args)
    assert doubled["required_fy_mpa_at_sampled_bending_first_yield"] == pytest.approx(2*one["required_fy_mpa_at_sampled_bending_first_yield"])


def test_frozen_census_small_minimum_thickness_and_unknown_strengths():
    report = steel.evaluate()
    assert report["counts"] == {"fittings":36, "flange_ports":72, "new_physical_shafts":58,
        "starting_physical_shafts":12, "shared_new_shafts":14, "washer_ends":140, "small_washer_ends":14}
    small = [w for w in report["washer_reference_inputs"] if w["small_washer_product"]]
    assert len(small) == 14
    assert all(w["minimum_published_thickness_mm"] == pytest.approx(1.8796) for w in small)
    assert all(len(report["washer_bending_profiles"][w["unit_axial_two_face_bending_profile_id"]]["small_washer_tolerance_corner_comparisons"]) == 4 for w in small)
    assert all(w["numeric_washer_fy_mpa"] is None for w in report["washer_reference_inputs"])
    assert all(r["bearing_tearout"]["nominal_strength_n"] is None for r in report["nominal_fitting_component_geometry"])
    assert report["complete_joint_acceptance"] is False


def test_fresh_flange_api_preserves_contacts_and_missing_ports():
    source = json.loads(steel.LAYOUT.read_text())
    axis = next(a for a in source["installed_axes"] if a["attachments"])
    port = axis["attachments"][0]
    action = {"case_id":"synthetic-fixture", "axis_id":axis["id"],
        "angle_id":port["angle_id"], "flange":port["flange"],
        "point_xyz_mm":port["entry_xyz_mm"], "force_on_receiver_xyz_n":[0., 100., 0.],
        "moment_on_receiver_at_point_xyz_nmm":[0., 0., 0.]}
    contact = action | {"force_on_receiver_xyz_n":[0., -25., 0.]}
    report = steel.compare_flange_actions([action], [contact])
    row = report["flange_comparisons"][0]
    assert len(row["external_point_actions_on_steel"]) == 2
    assert row["external_point_actions_on_steel"][0]["force_on_steel_xyz_n"] == [0., -100., 0.]
    assert len(report["cases"][0]["missing_flange_actions"]) == 71
    assert report["bolt_end_moment_and_prying_zero_inferred"] is False
    placements = steel.compare_flange_actions(
        [action | {"accessory_placement":"first"}, action | {"accessory_placement":"second"}], [])
    assert {r["accessory_placement"] for r in placements["cases"]} == {"first", "second"}
    with pytest.raises(ValueError, match="frozen flange hole"):
        steel.compare_flange_actions([action | {"point_xyz_mm":[0., 0., 0.]}], [])
    with pytest.raises(ValueError, match="duplicate"):
        steel.compare_flange_actions([action, action], [])


@pytest.mark.parametrize("field,value", [("thickness_mm", 0.), ("axial_n", -1.),
    ("nu", .5), ("bearing_radius_mm", 5.), ("outer_radius_mm", math.nan)])
def test_invalid_washer_inputs_stop(field, value):
    args = {"axial_n":100., "inner_radius_mm":6., "outer_radius_mm":14.,
            "bearing_radius_mm":11., "support_opening_radius_mm":7., "thickness_mm":2.}
    with pytest.raises(ValueError):
        steel.washer_axisymmetric_bending(**(args | {field: value}))
