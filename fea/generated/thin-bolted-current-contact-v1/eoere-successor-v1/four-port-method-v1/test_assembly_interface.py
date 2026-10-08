"""Only the changed owned-index and loaded-collector seam, no candidate inputs."""
import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

PATH = Path(__file__).with_name("assembly_interface.py")
SPEC = importlib.util.spec_from_file_location("eoere_assembly_seam_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def element():
    model = method.four.FourPortStripModel()
    return method.FourPortAssemblyElement(model, "toy-fitting", np.arange(3, 27), 31)


def loads():
    return [{"id": "toy-own-centroid-gravity", "body": "toy-fitting", "point_xyz_mm": [18., 3., 21.],
             "force_xyz_n": [0., 0., -12.]}]


def response(el, q):
    return el.response(q, loads=loads(), declared_route=method.ROUTE)


def test_exact_indices_ports_and_eccentric_force_work():
    el = element()
    q = np.arange(31, dtype=float)*1e-5
    force, point = np.array([2., -3., 7.]), np.array([68., 28., 4.])
    port = el.point_port("arm-x/far-plus", point)
    local = el.model.port_matrix("arm-x/far-plus", point, rotation_scale=1000.)
    assert np.array_equal(port @ q, local @ q[el.indices])
    assert float(force @ (port @ q)) == pytest.approx(float((port.T @ force) @ q), abs=1e-15)
    assert port[:, :3].nnz == port[:, 27:].nnz == 0


def test_loaded_heel_matches_uncondensed_stationarity_and_affine_operator():
    el = element()
    q = np.random.default_rng(5).normal(size=24)*1e-4
    result = response(el, q)
    full = np.r_[result["loaded_heel_q_mm_rad"], q*el.scale]
    full_rhs = np.r_[result["load_projection"]["heel_wrench_n_nmm"], np.zeros(24)]
    original = el.model.full_K @ full-full_rhs
    assert np.max(abs(original[:6])) < 1e-8
    assert np.max(abs(np.asarray(result["gradient_stored_units"])-original[6:]*el.scale)) < 1e-8
    _, block = el.elastic_block()
    expected = block @ q-np.asarray(result["load_projection"]["rhs_stored_units"])
    assert np.max(abs(expected-result["gradient_stored_units"])) < 1e-8
    assert np.max(abs(np.asarray(result["external_body_resultant_about_heel_n_nmm"]))) < 1e-7


def test_source_centroid_gravity_preserves_exact_wrench_and_rigid_work():
    el = element()
    projected = el.project_loads(loads(), declared_route=method.ROUTE)
    assert np.array_equal(projected["heel_wrench_n_nmm"], [-0., 0., -12., -36., 216., 0.])
    modes = el.rigid_modes([0., 0., 0.])
    observed = modes.T @ np.asarray(projected["rhs_stored_units"])
    assert np.max(abs(observed-projected["heel_wrench_n_nmm"])) < 1e-8
    assert projected["physical_load_rows"] == loads()
    assert not projected["external_heel_support"]
    row = loads()[0]
    body_load_port = el.centroid_load_port(row["point_xyz_mm"], declared_route=method.ROUTE)
    original_rhs = np.asarray(body_load_port.T @ row["force_xyz_n"])
    assert np.max(abs(original_rhs[el.indices]-projected["rhs_stored_units"])) < 1e-10
    assert np.array_equal(original_rhs[:3], np.zeros(3))
    assert np.array_equal(original_rhs[27:], np.zeros(4))


def test_energy_gradient_and_unshifted_reciprocal_tangent():
    el = element()
    q = np.random.default_rng(9).normal(size=24)*1e-4
    observed = response(el, q)
    h = 1e-7
    fd = np.array([(response(el, q+h*v)["potential_nmm"]-response(el, q-h*v)["potential_nmm"])/(2*h)
                   for v in np.eye(24)])
    assert np.max(abs(fd-observed["gradient_stored_units"])) < 1e-6
    _, K = el.elastic_block()
    assert np.max(abs(K-K.T)) < 1e-9
    modes = el.rigid_modes([7., 2., -4.])
    assert np.max(abs(K @ modes)) < 1e-6


def test_unloaded_response_reuses_frozen_four_port_exactly():
    el = element()
    q = np.random.default_rng(15).normal(size=24)*1e-4
    actual = el.response(q, declared_route=method.ROUTE)
    old = el.model.response(q*el.scale)
    assert actual["elastic_energy_nmm"] == pytest.approx(old["energy_nmm"], abs=1e-12)
    assert np.max(abs(np.asarray(actual["gradient_stored_units"])-
                      np.asarray(old["gradient_mm_rad_units"])*el.scale)) < 1e-9


def test_rejects_old_two_port_wrong_owner_duplicate_load_and_silent_route():
    el = element()
    for indices in (np.arange(12), np.zeros(24, dtype=int)):
        with pytest.raises(ValueError):
            method.FourPortAssemblyElement(el.model, "toy-fitting", indices, 31)
    for rows, route in (([{**loads()[0], "body": "other"}], method.ROUTE),
                        (loads()+loads(), method.ROUTE), (loads(), "equal-four-way-share")):
        with pytest.raises(ValueError):
            el.project_loads(rows, declared_route=route)
    with pytest.raises(ValueError):
        el.point_port("beam", [0., 0., 0.])


def test_all_callers_and_source_inputs_preserved():
    el = element()
    q = np.arange(24, dtype=float)*1e-5
    source = loads()
    before = copy.deepcopy(source)
    q_before = q.copy()
    el.response(q, loads=source, declared_route=method.ROUTE)
    assert source == before and np.array_equal(q, q_before)
    assert len(el.model.factory_holes) == 8 and len(el.model.port_manifest) == 4


def test_loaded_condensation_proper_world_transform_and_own_descriptor():
    original = element()
    Q = Rotation.from_rotvec([.2, -.4, .3]).as_matrix()
    offset = np.array([17., -12., 25.])
    data = copy.deepcopy(original.model.inputs)
    data["heel_reference_xyz_mm"] = offset.tolist()
    data["fitting_basis_columns_xyz"] = Q.tolist()
    transformed = method.FourPortAssemblyElement(method.four.FourPortStripModel(data),
        "toy-fitting", original.indices, original.ndof)
    load = copy.deepcopy(loads()[0])
    load["point_xyz_mm"] = (Q @ np.asarray(load["point_xyz_mm"])+offset).tolist()
    load["force_xyz_n"] = (Q @ np.asarray(load["force_xyz_n"])).tolist()
    q = np.random.default_rng(19).normal(size=(4, 6))*1e-4
    rotated = np.column_stack([q[:, :3] @ Q.T, q[:, 3:] @ Q.T])
    a = response(original, q.ravel())
    b = transformed.response(rotated.ravel(), loads=[load], declared_route=method.ROUTE)
    assert abs(a["potential_nmm"]-b["potential_nmm"]) < 1e-12
    ga, gb = (np.asarray(v["gradient_stored_units"]).reshape(4, 6) for v in (a, b))
    expected = np.column_stack([ga[:, :3] @ Q.T, ga[:, 3:] @ Q.T])
    assert np.max(abs(gb-expected)) < 1e-8
    descriptor = transformed.descriptor()
    assert descriptor["dof_indices"] == original.indices.tolist()
    assert descriptor["ports"][1]["id"] == "arm-x/far-plus"
    assert descriptor["ports"][2]["id"] == "arm-z/far-minus"
    assert len(descriptor["all_factory_holes"]) == 8
    assert not descriptor["internal_heel_is_physical_owner"]


def test_source_reference_entry_nodes_transverse_signs_and_midplate_offset_work():
    Q = Rotation.from_rotvec([-.3, .1, .4]).as_matrix()
    u, v, w = Q.T
    origin = np.array([51., 32., -7.])
    model, bindings = method.model_from_reference_pose(origin, u, v, w)
    el = method.FourPortAssemblyElement(model, "toy-fitting", np.arange(24), 24)
    ports = {row["id"]: row for row in model.port_manifest}
    for row in bindings:
        along, inward = (u, -v) if row["source_flange"] == "beam" else (v, -u)
        entry = origin+65.0875*along+row["source_transverse"]*25.4*w
        own_point = np.asarray(ports[row["model_port_id"]]["point_reference_xyz_mm"])
        assert np.max(abs(own_point-entry)) < 2e-14
        midpoint = entry-inward*6.35/2
        force = np.array([3., 2., -7.])
        g = np.asarray(el.point_port(row["model_port_id"], midpoint).T @ force)
        i = ports[row["model_port_id"]]["port_index"]
        expected_couple = np.cross(midpoint-entry, force)/el.rotation_scale
        assert np.max(abs(g[6*i:6*i+3]-force)) < 1e-14
        assert np.max(abs(g[6*i+3:6*i+6]-expected_couple)) < 1e-14
    with pytest.raises(ValueError):
        method.model_from_reference_pose(origin, u, v, -w)
