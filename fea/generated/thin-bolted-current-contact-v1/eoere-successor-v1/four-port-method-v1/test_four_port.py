"""Small pure four-port known answers; no candidate/native/global mechanics."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

PATH = Path(__file__).with_name("four_port.py")
SPEC = importlib.util.spec_from_file_location("eoere_four_port_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = method
SPEC.loader.exec_module(method)


def inputs():
    return json.loads(method.INPUT.read_bytes())


def random_state(seed=14):
    q = np.random.default_rng(seed).normal(size=(4, 6))
    q[:, :3] *= 1e-4
    q[:, 3:] *= 2e-6
    return q.ravel()


def test_source_beam_exact_axial_two_bending_torsion_and_pure_moment():
    model = method.FourPortStripModel()
    L, E, G, A = model.length, model.E, model.G, model.A
    expected = {0: L/(E*A), 1: L**3/(3*E*model.Iz)+L/(model.inputs["shear_factor"]*G*A),
        2: L**3/(3*E*model.Iy)+L/(model.inputs["shear_factor"]*G*A), 3: L/(G*model.J), 5: L/(E*model.Iz)}
    for index, answer in expected.items():
        q = np.linalg.solve(model.local_K[6:, 6:], np.eye(6)[index])
        assert abs(q[index]-answer) <= 1e-13*max(1., abs(answer))
    moment = np.linalg.solve(model.local_K[6:, 6:], np.eye(6)[5])
    assert moment[1] == pytest.approx(L**2/(2*E*model.Iz), rel=1e-13)


def test_four_port_self_equilibrated_force_plus_couple_hand_answer():
    model = method.FourPortStripModel()
    result = method.known_answer(model)
    assert result["method_known_answer_pass"]
    assert np.max(abs(np.asarray(result["observed"]["condensed_heel_q_mm_rad"]))) < 1e-13
    assert np.max(abs(np.asarray(result["observed"]["internal_heel_gradient_n_nmm"]))) < 1e-9
    assert np.max(abs(np.asarray(result["observed"]["external_resultant_about_heel_n_nmm"]))) < 1e-9
    assert result["observed"]["port_actions"][0]["external_moment_on_fitting_at_port_xyz_nmm"][2] == pytest.approx(177.8)


def test_six_rigid_modes_no_heel_clamp_and_unshifted_positive_energy():
    model = method.FourPortStripModel()
    modes = np.zeros((24, 6))
    for row in model.port_manifest:
        i = row["port_index"]
        modes[6*i:6*i+6] = method.transport(np.asarray(row["point_reference_xyz_mm"]), model.origin)
    for column in range(6):
        result = model.response(modes[:, column]*1e-3)
        assert result["energy_nmm"] < 1e-20
        assert np.max(abs(np.asarray(result["gradient_mm_rad_units"]))) < 1e-7
    scaled = model.condensed_matrix(rotation_scale=1000.)
    eigenvalues = np.linalg.eigvalsh(scaled)
    budget = 256*np.finfo(float).eps*np.linalg.norm(scaled, ord=2)
    assert np.max(abs(scaled-scaled.T)) < budget
    assert np.min(eigenvalues) >= -budget
    assert np.count_nonzero(eigenvalues > budget) == 18


def test_energy_gradient_tangent_and_reciprocity():
    model = method.FourPortStripModel()
    q, p = random_state(), random_state(51)
    fields = model.response(q)
    g = np.asarray(fields["gradient_mm_rad_units"])
    h = 1e-7
    fd = np.array([(model.response(q+h*direction)["energy_nmm"]-model.response(q-h*direction)["energy_nmm"])/(2*h)
        for direction in np.eye(24)])
    assert np.max(abs(fd-g)) < 1e-7
    assert np.max(abs(model.K@q-g)) < 1e-9
    assert abs(q@model.K@p-p@model.K@q) < 1e-12
    assert abs(fields["twice_energy_vs_port_work_nmm"]) < 1e-12


def test_true_transverse_offsets_and_each_strip_and_flange_wrench_closure():
    model = method.FourPortStripModel()
    result = model.response(random_state())
    assert len(model.factory_holes) == 8 and sum(row["used_port"] for row in model.factory_holes) == 4
    assert all(abs(abs(row["hole_to_neutral_xyz_mm"][1])-3.175) < 1e-14 for row in model.port_manifest)
    for root, port in zip(result["strip_root_actions"], result["port_actions"], strict=True):
        root_w = method.wrench_at(np.asarray(root["applied_to_strip_force_xyz_n"]),
            np.asarray(root["applied_to_strip_moment_at_root_xyz_nmm"]), np.asarray(root["point_xyz_mm"]), model.origin)
        tip_w = method.wrench_at(np.asarray(port["external_force_on_fitting_xyz_n"]),
            np.asarray(port["external_moment_on_fitting_at_port_xyz_nmm"]), np.asarray(port["point_xyz_mm"]), model.origin)
        assert np.max(abs(root_w+tip_w)) < 1e-8
    assert np.max(abs(np.asarray(result["external_resultant_about_heel_n_nmm"]))) < 1e-8


def test_arbitrary_point_ports_force_moment_work_and_rotation_storage():
    model = method.FourPortStripModel()
    q = random_state()
    scale = np.tile([1.,1.,1.,1000.,1000.,1000.], 4)
    stored = scale*q
    assert .5*stored@model.condensed_matrix(rotation_scale=1000.)@stored == pytest.approx(model.response(q)["energy_nmm"], rel=1e-13)
    port = model.port_manifest[1]
    point = np.asarray(port["point_reference_xyz_mm"])+[3., -4., 5.]
    operator = model.port_matrix(port["id"], point, rotation_scale=1000.)
    force = np.array([7., -2., 4.])
    q0 = q[6:12]
    expected = q0[:3]+np.cross(q0[3:], point-np.asarray(port["point_reference_xyz_mm"]))
    assert np.max(abs(operator@stored-expected)) < 1e-15
    assert force@(operator@stored) == pytest.approx((operator.T@force)@stored, abs=1e-15)
    with pytest.raises(ValueError, match="exact own"):
        model.port_matrix("arm-x", point)


def test_proper_world_rotation_translation_covariance():
    baseline, data = method.FourPortStripModel(), inputs()
    rotation = Rotation.from_rotvec([.4, -.2, .3]).as_matrix()
    data["fitting_basis_columns_xyz"] = rotation.tolist()
    data["heel_reference_xyz_mm"] = [11., -13., 7.]
    moved = method.FourPortStripModel(data)
    q = random_state().reshape(4, 6)
    transformed = np.c_[q[:,:3]@rotation.T, q[:,3:]@rotation.T]
    first, second = baseline.response(q.ravel()), moved.response(transformed.ravel())
    assert first["energy_nmm"] == pytest.approx(second["energy_nmm"], abs=1e-12)
    expected = np.c_[np.asarray(first["gradient_mm_rad_units"]).reshape(4,6)[:,:3]@rotation.T,
        np.asarray(first["gradient_mm_rad_units"]).reshape(4,6)[:,3:]@rotation.T]
    assert np.max(abs(expected.ravel()-second["gradient_mm_rad_units"])) < 1e-8


@pytest.mark.parametrize("mutation", ["metric", "reflected", "Fy", "parallel"])
def test_incompatible_scenario_inputs_reject(mutation):
    data = copy.deepcopy(inputs())
    if mutation == "metric": data["width_mm"] = 90.
    elif mutation == "reflected": data["fitting_basis_columns_xyz"][0][0] = -1.
    elif mutation == "Fy": data["steel_fy_mpa"] = 250.
    else: data["flange_axes_local"]["arm-z"] = data["flange_axes_local"]["arm-x"]
    with pytest.raises(ValueError):
        method.FourPortStripModel(data)


def test_input_state_not_mutated_and_old_two_port_shape_rejected():
    model, q = method.FourPortStripModel(), random_state()
    before = q.copy()
    model.response(q)
    assert np.array_equal(q, before) and not model.local_K.flags.writeable
    with pytest.raises(ValueError):
        model.response(np.zeros(12))
