"""Reference mechanics, exact material-roll symmetry and an honest gauge chart."""

import importlib.util
from functools import lru_cache

import numpy as np
import pytest
from scipy.linalg import block_diag
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_isotropic_shaft as shaft
from scripts.thin_bolted_common_shaft import circular_properties
from scripts.thin_bolted_corotational_methods import so3_exp, so3_log
from scripts.thin_bolted_frame_mechanics import beam_stiffness


def straight_beam(length=120., basis=None):
    basis = np.eye(3) if basis is None else basis
    start = np.array([30., -20., 40.])
    return shaft.IsotropicShaftBeam(np.array([start, start + length*basis[:, 0]]), basis, 8., 200000., 76923.)


def bent_two_element():
    positions = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]])
    beams = [shaft.IsotropicShaftBeam(positions[i:i+2], np.eye(3), 8., 200000., 76923.) for i in range(2)]
    q = np.zeros((3, 6)); q[:, :3] = [[0., 0., 0.], [-1., 3., 2.], [-4., 12., 7.]]
    q[:, 3:] = [[30., 150., 100.], [80., 200., 280.], [100., 250., 400.]]
    return beams, q


def chain_response(beams, q):
    gradient, energy = np.zeros_like(q), 0.
    for i, beam in enumerate(beams):
        result = beam.response(q[i:i+2].ravel(), False)
        gradient[i:i+2] += result["gradient_n"].reshape(2, 6)
        energy += result["energy_nmm"]
    return energy, gradient


@lru_cache(maxsize=1)
def mechanical_fixtures():
    path = shaft.mechanical.ROOT / "tests/test_thin_bolted_finite_mechanics.py"
    spec = importlib.util.spec_from_file_location("retained_finite_mechanics_fixture", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def small_adapter():
    mechanical, _, _, common = mechanical_fixtures().small_assembly()
    mechanical.shafts["shaft/test"]["diameter_mm"] = 8.
    common.parameters = {"shaft_steel_E_mpa": 200000., "shaft_steel_nu": 200000/(2*76923.) - 1,
                         "shaft_diameter_scale": 1., "circular_shear_factor_scenario": .9}
    return shaft.IsotropicShaftAdapter(mechanical, common)


@pytest.mark.parametrize("length", [15., 50., 120.])
@pytest.mark.parametrize("rotated_basis", [False, True])
def test_exact_reference_hessian_and_numerical_tangent_recover_closed_timoshenko(length, rotated_basis):
    basis = Rotation.from_rotvec([.13, -.21, .17]).as_matrix() if rotated_basis else np.eye(3)
    beam = straight_beam(length, basis)
    area, inertia, torsion = circular_properties(beam.diameter_mm)
    local = beam_stiffness(length, area, inertia, inertia, torsion, beam.elastic_modulus_mpa, beam.shear_modulus_mpa, .9)
    transform = block_diag(basis.T, basis.T/1000, basis.T, basis.T/1000)
    expected = transform.T @ local @ transform
    assert np.linalg.norm(beam.reference_tangent() - expected)/np.linalg.norm(expected) < 1e-12
    assert np.linalg.norm(beam.tangent(np.zeros(12)) - expected)/np.linalg.norm(expected) < 1e-9


@pytest.mark.parametrize("plane", [1, 2])
def test_reference_tip_cantilever_matches_bending_plus_shear_known_answer(plane):
    beam = straight_beam(); length = beam.length_mm
    area, inertia, _ = circular_properties(beam.diameter_mm)
    force = np.zeros(6); force[plane] = .2
    tip = np.linalg.solve(beam.reference_tangent()[6:, 6:], force)
    expected = .2*(length**3/(3*beam.elastic_modulus_mpa*inertia) + length/(.9*beam.shear_modulus_mpa*area))
    assert tip[plane] == pytest.approx(expected, rel=1e-12)
    rotation_axis = 5 if plane == 1 else 4
    sign = 1 if plane == 1 else -1
    assert tip[rotation_axis]/1000 == pytest.approx(sign*.2*length**2/(2*beam.elastic_modulus_mpa*inertia), rel=1e-12)


def test_finite_axial_and_torsion_exact_known_energies():
    beam = straight_beam()
    area, _, torsion = circular_properties(beam.diameter_mm)
    q = np.zeros(12); q[6] = .4
    assert beam.energy(q) == pytest.approx(.5*beam.elastic_modulus_mpa*area/beam.length_mm*.4**2, rel=1e-12)
    q = np.zeros(12); q[9] = 120.
    assert beam.energy(q) == pytest.approx(.5*beam.shear_modulus_mpa*torsion/beam.length_mm*.12**2, rel=1e-12)


@pytest.mark.parametrize("angle", [20., 73.])
def test_exact_common_world_rotation_has_zero_energy_and_internal_force(angle):
    basis = Rotation.from_rotvec([.13, -.21, .17]).as_matrix(); beam = straight_beam(basis=basis)
    rotation = Rotation.from_rotvec(np.deg2rad(angle)*np.array([1., -2., 3.])/np.sqrt(14)).as_matrix()
    q = np.zeros((2, 6)); q[:, :3] = beam.reference_positions @ (rotation - np.eye(3)).T + [7., -11., 13.]
    q[:, 3:] = 1000*so3_log(rotation)
    result = beam.response(q.ravel(), False)
    assert result["energy_nmm"] < 1e-18
    assert np.linalg.norm(result["gradient_n"]) < 1e-7


def test_analytic_gradient_tangent_and_deformed_world_objectivity():
    basis = Rotation.from_rotvec([.13, -.21, .17]).as_matrix(); beam = straight_beam(basis=basis)
    q = np.array([.2, -.3, .1, 40., -25., 16., -.1, .25, -.15, 32., -14., 30.])
    result = beam.response(q)
    direction = np.random.default_rng(7).normal(size=12); step = 1e-4
    plus, minus = beam.response(q + step*direction, False), beam.response(q - step*direction, False)
    assert direction @ result["gradient_n"] == pytest.approx((plus["energy_nmm"] - minus["energy_nmm"])/(2*step), rel=1e-7)
    assert result["hessian_n_per_mm"] @ direction == pytest.approx((plus["gradient_n"] - minus["gradient_n"])/(2*step), rel=2e-7, abs=3e-5)
    rotation = Rotation.from_rotvec([.19, -.24, .11]).as_matrix()
    changed = q.reshape(2, 6).copy()
    changed[:, :3] = (beam.reference_positions + changed[:, :3]) @ rotation.T + [1., 2., -3.] - beam.reference_positions
    for i, own in enumerate(q.reshape(2, 6)):
        changed[i, 3:] = 1000*so3_log(rotation @ so3_exp(own[3:]/1000))
    assert beam.energy(changed.ravel()) == pytest.approx(result["energy_nmm"], rel=2e-12)


@pytest.mark.parametrize("angle", [20., 70., -35.])
def test_bent_two_element_common_right_roll_preserves_energy_gradient_and_null_work(angle):
    beams, q = bent_two_element()
    initial_energy, initial_gradient = chain_response(beams, q)
    rolled = shaft.common_roll_local(q, np.deg2rad(angle))
    changed_energy, changed_gradient = chain_response(beams, rolled)
    assert changed_energy == pytest.approx(initial_energy, rel=3e-13)
    work = 0.
    for i in range(3):
        old_theta, new_theta = q[i, 3:]/1000, rolled[i, 3:]/1000
        transform = shaft.so3_left_jacobian_inverse(new_theta) @ shaft.so3_left_jacobian(old_theta)
        assert transform.T @ changed_gradient[i, 3:] == pytest.approx(initial_gradient[i, 3:], rel=3e-12, abs=1e-8)
        assert changed_gradient[i, :3] == pytest.approx(initial_gradient[i, :3], rel=3e-12, abs=1e-8)
        generator = 1000*shaft.so3_left_jacobian_inverse(old_theta) @ so3_exp(old_theta)[:, 0]
        work += initial_gradient[i, 3:] @ generator
    assert abs(work) < 2e-7


def test_bent_beam_full_spatial_force_and_moment_close_before_gauging():
    beams, q = bent_two_element(); _, gradient = chain_response(beams, q)
    centers = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]]) + q[:, :3]
    moments = np.array([1000*shaft.so3_left_jacobian_inverse(state[3:]/1000).T @ own[3:]
                        for state, own in zip(q, gradient, strict=True)])
    assert np.linalg.norm(gradient[:, :3].sum(axis=0)) < 1e-7
    assert np.linalg.norm((np.cross(centers, gradient[:, :3]) + moments).sum(axis=0)) < 2e-6


def test_minimal_director_gauge_preserves_bent_energy_and_all_axial_directors():
    beams, q = bent_two_element()
    gauged, metadata = shaft.minimal_director_gauge_local(q)
    assert abs(gauged[0, 3]) < 1e-10
    assert metadata["removed_common_right_roll_rad"] != 0
    assert chain_response(beams, gauged)[0] == pytest.approx(chain_response(beams, q)[0], rel=3e-13)
    for before, after in zip(q, gauged, strict=True):
        assert so3_exp(after[3:]/1000)[:, 0] == pytest.approx(so3_exp(before[3:]/1000)[:, 0], abs=1e-13)


def test_adapter_replaces_only_shaft_energy_without_double_count_or_source_mutation():
    adapter = small_adapter(); mechanical = adapter.mechanics
    q = np.random.default_rng(81).normal(scale=.4, size=adapter.ndof)
    own = adapter.response(q)
    result = adapter.replacement_response(q)
    wood_fitting_energy = sum(element.response(q, False)["energy_nmm"] for element in adapter.timber_elements)
    wood_fitting_energy += sum(row["model"].response(q[row["index"].ravel()], False)["energy_nmm"] for row in mechanical.fittings.values())
    assert result["energy_nmm"] == pytest.approx(own["energy_nmm"] + wood_fitting_energy, rel=1e-13)
    assert adapter.ndof == mechanical.ndof == 48
    assert len(adapter.elements) == len(adapter.timber_elements) == 2
    assert max(adapter.reference_matrix_relative_errors) < 1e-12
    original_response = mechanical.response(q, False)
    assert original_response["finite_shaft_twist_gauge_qualified"] is False
    for row in mechanical.members.values():
        assert np.linalg.norm(own["gradient_n"][row["index"].ravel()]) == 0
    assert own["physical_twist_constraints_added"] == 0


def test_full_adapter_gauge_preserves_on_axis_ports_axial_directors_and_internal_work():
    adapter = small_adapter(); q = np.zeros(adapter.ndof)
    row = adapter.mechanics.shafts["shaft/test"]
    _, bent = bent_two_element(); q[row["index"]] = bent
    gauged, _ = adapter.minimal_director_gauge(q)
    assert adapter.response(gauged, False)["energy_nmm"] == pytest.approx(adapter.response(q, False)["energy_nmm"], rel=3e-13)
    generator = adapter.material_roll_generators(q)["shaft/test"]
    assert abs(adapter.response(q, False)["gradient_n"] @ generator) < 2e-7
    for station in (0., 23., 63., 100.):
        point = row["point"] + station*row["basis"][0]
        before, after = adapter.port("shaft/test", point, q, tangent=False), adapter.port("shaft/test", point, gauged, tangent=False)
        assert after["position_xyz_mm"] == pytest.approx(before["position_xyz_mm"], abs=1e-11)
        assert np.linalg.norm(before["J_csr"] @ generator) < 1e-11
        before = adapter.director("shaft/test", point, q, row["basis"][0], tangent=False)
        after = adapter.director("shaft/test", point, gauged, row["basis"][0], tangent=False)
        assert after["current_vector_xyz"] == pytest.approx(before["current_vector_xyz"], abs=1e-13)
        assert np.linalg.norm(before["J_csr"] @ generator) < 1e-13


def test_quotient_world_rigid_generator_preserves_external_force_moment_work():
    adapter = small_adapter(); q = np.zeros(adapter.ndof)
    body = "shaft/test"; row = adapter.mechanics.shafts[body]
    _, bent = bent_two_element(); q[row["index"]] = bent
    gauged, _ = adapter.minimal_director_gauge(q)
    reference = np.array([17., -31., 22.])
    fields = adapter.quotient_world_rigid_generators(gauged, reference)[body]
    assert np.linalg.norm(fields["first_local_theta_x_increment_after_correction"]) < 1e-10
    assert np.linalg.norm(fields["compensating_common_right_roll_per_world_rigid_component"]) > .01
    dual, wrench = np.zeros(adapter.ndof), np.zeros(6)
    for station, force in ((11., [70., -110., 90.]), (67., [-60., 140., 50.]), (93., [25., -75., -150.])):
        point = row["point"] + station*row["basis"][0]
        port = adapter.port(body, point, gauged, tangent=False); force = np.array(force)
        dual += port["J_csr"].T @ force
        wrench += np.r_[force, np.cross(port["position_xyz_mm"] - reference, force)]
    assert fields["full_world_rigid_G_csr"].T @ dual == pytest.approx(wrench, abs=1e-9)
    assert fields["quotient_world_rigid_G_csr"].T @ dual == pytest.approx(wrench, abs=1e-9)
    assert np.linalg.norm(fields["quotient_world_rigid_G_csr"].T @ adapter.response(gauged, False)["gradient_n"]) < 3e-6


def test_real_off_axis_ports_and_radial_material_vectors_are_not_projected_or_called_invariant():
    adapter = small_adapter(); q = np.zeros(adapter.ndof); body = "shaft/test"; row = adapter.mechanics.shafts[body]
    _, bent = bent_two_element(); q[row["index"]] = bent
    gauged, _ = adapter.minimal_director_gauge(q)
    point = row["point"] + 23*row["basis"][0] + 5*row["basis"][1]
    initial, changed = adapter.port(body, point, q, tangent=False), adapter.port(body, point, gauged, tangent=False)
    assert np.linalg.norm(changed["position_xyz_mm"] - initial["position_xyz_mm"]) > .1
    initial = adapter.director(body, point, q, row["basis"][1], tangent=False)
    changed = adapter.director(body, point, gauged, row["basis"][1], tangent=False)
    assert np.linalg.norm(changed["current_vector_xyz"] - initial["current_vector_xyz"]) > .01


def test_all350_original_source_centroids_keep_precision_offsets_and_gauge_invariance():
    result = shaft.source_axis_gauge_audit()
    assert result["physical_shafts"] == 70 and result["original_metal_load_centroids"] == 350
    assert result["centroids_projected_to_axis"] == 0
    assert result["maximum_original_centroid_radial_offset_mm"] == pytest.approx(4.3715613161697907e-10, rel=1e-10)
    assert result["maximum_unprojected_centroid_gauge_position_change_mm"] < 2e-10
    assert result["maximum_axial_director_gauge_change"] < 1e-14
    assert result["sum_absolute_gravity_work_change_nmm"] < 1e-8


def test_declared_finite_extension_arc_chord_error_remains_and_refines():
    result = shaft.chord_refinement_coupon(); axial = []
    for row in result["records"]:
        assert row["bending_energy_nmm"] == pytest.approx(result["expected_bending_energy_nmm"], rel=1e-11)
        assert row["shear_energy_nmm"] < 1e-20
        axial.append(row["spurious_chord_axial_energy_nmm"])
    assert axial[0]/axial[1] == pytest.approx(16., rel=1e-3)
    assert axial[1]/axial[2] == pytest.approx(16., rel=1e-3)
    assert result["candidate_local_curvature_refinement_established"] is False


def test_unsupported_local_turn_antiparallel_gauge_and_property_mismatch_are_rejected():
    beam = straight_beam(); q = np.zeros(12); q[11] = 1000*np.deg2rad(91.)
    with pytest.raises(ValueError, match="local shaft turn"):
        beam.energy(q)
    nodes = np.zeros((2, 6)); nodes[0, 4] = 1000*(np.pi - 2e-6)
    with pytest.raises(ValueError, match="antiparallel"):
        shaft.minimal_director_gauge_local(nodes)
    adapter = small_adapter(); q = np.zeros(adapter.ndof); q[adapter.mechanics.shafts["shaft/test"]["appended_first_twist_dof"]] = 1.
    with pytest.raises(ValueError, match="requires minimal"):
        adapter.quotient_world_rigid_generators(q)


def test_frozen_mechanical_adapter_pin_cannot_be_replaced():
    with pytest.raises(ValueError, match="conflict"):
        shaft.source_pins({"scripts/thin_bolted_finite_mechanics.py": "0"*64})
