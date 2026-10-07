"""Known answers for the finite mechanical adapter; no candidate assembly."""

from types import SimpleNamespace

import numpy as np
import pytest
from scipy.linalg import block_diag
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_mechanics as finite
from scripts.thin_bolted_common_shaft import reduced_shaft_matrix
from scripts.thin_bolted_corotational_methods import so3_exp, so3_log
from scripts.thin_bolted_frame_mechanics import (
    beam_stiffness,
    point_matrix,
    rectangular_torsion,
)
from scripts.thin_bolted_steel_resistance import fitting_condensed_stiffness


def fitting_fixture(model="B104ZN"):
    fitting = {"angle_id": model + "_coupon", "origin_xyz_mm": [180., 230., 140.],
               "u_xyz": [1., 0., 0.], "v_xyz": [0., 1., 0.], "w_xyz": [0., 0., 1.]}
    result = fitting_condensed_stiffness(fitting, beam_stiffness, rectangular_torsion)
    points = np.array([row["point_xyz_mm"] for row in result["ports"]])
    return finite.ObjectiveCondensedFitting(points, np.array(result["global_port_stiffness_n_mm_rad"])), result


def small_assembly():
    """One refined timber, one L fitting and one two-element circular shaft."""
    basis = Rotation.from_rotvec([.13, -.21, .17]).as_matrix()
    start, stations = np.array([30., -40., 20.]), np.array([0., 80., 160.])
    index = np.arange(18).reshape(3, 6)
    local = beam_stiffness(80., 600., 25000., 14000., 20000., 10000., 640.)
    transform = block_diag(basis.T, basis.T/1000, basis.T, basis.T/1000)
    elements = [{"start": start + basis[:, 0]*stations[i],
                 "end": start + basis[:, 0]*stations[i+1], "dofs": index[i:i+2].ravel(),
                 "local_K": local} for i in range(2)]
    member = {"start": start, "axis": basis[:, 0], "stations": stations, "index": index,
              "elements": elements, "source": {"axis": basis[:, 0], "section_u": basis[:, 1], "section_v": basis[:, 2]}}
    _, fitting_source = fitting_fixture()
    fitting = {"index": np.arange(18, 30).reshape(2, 6), "source": fitting_source,
               "points": {row["flange"]: np.array(row["point_xyz_mm"]) for row in fitting_source["ports"]}}
    shaft_basis = Rotation.from_rotvec([-.11, .23, -.19]).as_matrix()
    shaft_k, shaft_index, shaft_elements = reduced_shaft_matrix([0., 50., 100.], 8., 200000., 76923.)
    actual_index = np.where(shaft_index >= 0, shaft_index + 30, -1)
    shaft = {"point": np.array([-130., 70., 45.]), "basis": shaft_basis.T,
             "stations": np.array([0., 50., 100.]), "index": actual_index, "elements": shaft_elements}
    assembly = SimpleNamespace(ndof=47, members={"timber": member}, fittings={"fitting": fitting})
    system = SimpleNamespace(shafts={"shaft/test": shaft})
    reference_k = np.zeros((47, 47))
    for element in elements:
        idx = element["dofs"]
        reference_k[np.ix_(idx, idx)] += transform.T @ local @ transform
    scale = np.tile([1., 1., 1., .001, .001, .001], 2)
    reference_k[18:30, 18:30] += np.array(fitting_source["global_port_stiffness_n_mm_rad"])*scale[:, None]*scale[None, :]
    reference_k[30:, 30:] += shaft_k.toarray()
    return finite.FiniteMechanicsAdapter(assembly, system), reference_k, assembly, system


def node_rows(adapter):
    for member in adapter.members.values():
        for index, station in zip(member["index"], member["stations"], strict=True):
            yield index, member["start"] + station*member["axis"], np.eye(3)
    for fitting in adapter.fittings.values():
        for i, flange in enumerate(("beam", "post")):
            yield fitting["index"][i], fitting["points"][flange], np.eye(3)
    for shaft in adapter.shafts.values():
        for index, station in zip(shaft["index"], shaft["stations"], strict=True):
            yield index, shaft["point"] + station*shaft["basis"][0], shaft["storage_basis"]


def superpose(adapter, q, rotation, translation):
    result = q.copy()
    for index, position, basis in node_rows(adapter):
        own = q[index]
        result[index[:3]] = basis.T @ (rotation @ (position + basis @ own[:3]) + translation - position)
        result[index[3:]] = 1000*basis.T @ so3_log(rotation @ so3_exp(basis @ own[3:]/1000))
    return result


@pytest.mark.parametrize("model", ["B103ZN", "B104ZN"])
def test_condensed_fitting_reference_tangent_matches_unchanged_l_strip(model):
    fitting, source = fitting_fixture(model)
    scale = np.tile([1., 1., 1., .001, .001, .001], 2)
    expected = np.array(source["global_port_stiffness_n_mm_rad"])*scale[:, None]*scale[None, :]
    actual = fitting.response(np.zeros(12))["hessian_n_per_mm"]
    assert np.linalg.norm(actual - expected)/np.linalg.norm(expected) < 1e-9


@pytest.mark.parametrize("angle", [20., 73.])
def test_non_collinear_l_strip_common_rigid_motion_has_zero_energy_force(angle):
    fitting, _ = fitting_fixture()
    rotation = Rotation.from_rotvec(np.deg2rad(angle)*np.array([1., -2., 3.])/np.sqrt(14)).as_matrix()
    q = np.zeros((2, 6))
    q[:, :3] = fitting.reference_positions @ (rotation - np.eye(3)).T + [7., -11., 13.]
    q[:, 3:] = 1000*so3_log(rotation)
    result = fitting.response(q.ravel(), tangent=False)
    assert result["energy_nmm"] < 1e-19
    assert np.linalg.norm(result["gradient_n"]) < 1e-7


def test_deformed_fitting_energy_gradient_and_tangent_are_consistent_and_objective():
    fitting, _ = fitting_fixture()
    q = np.array([.2, -.3, .1, 40., -25., 16., -.1, .25, -.15, 32., -14., 30.])
    result = fitting.response(q)
    rotation = Rotation.from_rotvec([.19, -.24, .11]).as_matrix()
    rotated = q.reshape(2, 6).copy()
    rotated[:, :3] = (fitting.reference_positions + rotated[:, :3]) @ rotation.T + [1., 2., -3.] - fitting.reference_positions
    for i in range(2):
        rotated[i, 3:] = 1000*so3_log(rotation @ so3_exp(q.reshape(2, 6)[i, 3:]/1000))
    assert fitting.response(rotated.ravel(), False)["energy_nmm"] == pytest.approx(result["energy_nmm"], rel=1e-12)
    direction = np.random.default_rng(6).normal(size=12)
    step = 1e-4
    plus, minus = fitting.response(q + step*direction, False), fitting.response(q - step*direction, False)
    assert direction @ result["gradient_n"] == pytest.approx((plus["energy_nmm"] - minus["energy_nmm"])/(2*step), rel=1e-7)
    assert result["hessian_n_per_mm"] @ direction == pytest.approx((plus["gradient_n"] - minus["gradient_n"])/(2*step), rel=2e-7, abs=2e-5)


def test_adapter_preserves_old_indices_appends_twist_and_matches_reference_matrix():
    adapter, expected, original, system = small_assembly()
    assert original.ndof == 47 and adapter.ndof == 48
    assert system.shafts["shaft/test"]["index"][0, 3] == -1
    assert adapter.shafts["shaft/test"]["index"][0, 3] == 47
    q = adapter.prolong_state(np.zeros(47))
    result = adapter.response(q)
    assert np.linalg.norm(result["hessian_csr"][:47, :47].toarray() - expected)/np.linalg.norm(expected) < 1e-9
    assert result["energy_nmm"] == pytest.approx(0., abs=1e-20)
    assert result["physical_or_numerical_twist_constraints_added"] == 0
    assert result["finite_shaft_twist_gauge_qualified"] is False


@pytest.mark.parametrize("angle", [20., 73.])
def test_small_mechanical_assembly_rigid_energy_ports_directors(angle):
    adapter, _, _, _ = small_assembly()
    rotation = Rotation.from_rotvec(np.deg2rad(angle)*np.array([1., 2., -1.])/np.sqrt(6)).as_matrix()
    translation = np.array([7., -11., 13.])
    q = superpose(adapter, np.zeros(adapter.ndof), rotation, translation)
    result = adapter.response(q, False)
    assert result["energy_nmm"] < 1e-18
    assert np.linalg.norm(result["gradient_n"]) < 1e-7
    for body, point, flange in (("timber", [78., -15., 55.], None), ("shaft/test", [-109., 83., 67.], None),
                               ("fitting", [221., 260., 190.], "beam"), ("fitting", [215., 244., 120.], None)):
        port = adapter.port(body, point, q, flange, False)
        assert port["position_xyz_mm"] == pytest.approx(rotation @ point + translation, abs=1e-11)
    for body, flange in (("timber", None), ("shaft/test", None), ("fitting", "post")):
        director = adapter.director(body, [100., 50., 20.], q, [0., 0., 1.], flange, False)
        assert director["current_vector_xyz"] == pytest.approx(rotation[:, 2], abs=1e-12)
        assert np.linalg.norm(director["current_vector_xyz"]) == pytest.approx(1., abs=1e-12)


def test_deformed_mechanical_assembly_superposed_rotation_preserves_energy():
    adapter, _, _, _ = small_assembly()
    q = np.random.default_rng(51).normal(size=adapter.ndof)
    q *= .3
    rotation = Rotation.from_rotvec([.13, -.21, .17]).as_matrix()
    rotated = superpose(adapter, q, rotation, [4., -9., 6.])
    assert adapter.response(rotated, False)["energy_nmm"] == pytest.approx(adapter.response(q, False)["energy_nmm"], rel=3e-12)


def test_assembly_residual_tangent_and_world_force_moment_work():
    adapter, _, _, _ = small_assembly()
    q = np.random.default_rng(74).normal(scale=.3, size=adapter.ndof)
    for index, _, _ in node_rows(adapter):
        q[index[3:]] *= 40
    result = adapter.response(q)
    direction = np.random.default_rng(75).normal(size=adapter.ndof)
    step = 1e-4
    plus, minus = adapter.response(q + step*direction, False), adapter.response(q - step*direction, False)
    assert direction @ result["gradient_n"] == pytest.approx((plus["energy_nmm"] - minus["energy_nmm"])/(2*step), rel=1e-7)
    assert result["hessian_csr"] @ direction == pytest.approx((plus["gradient_n"] - minus["gradient_n"])/(2*step), rel=2e-7, abs=3e-5)
    total_force, total_moment = np.zeros(3), np.zeros(3)
    for index, center, basis in node_rows(adapter):
        force = basis @ result["gradient_n"][index[:3]]
        theta = basis @ q[index[3:]]/1000
        moment = 1000*finite.so3_left_jacobian_inverse(theta).T @ (basis @ result["gradient_n"][index[3:]])
        current_center = center + basis @ q[index[:3]]
        total_force += force
        total_moment += np.cross(current_center, force) + moment
    assert np.linalg.norm(total_force) < 1e-7
    assert np.linalg.norm(total_moment) < 2e-5


@pytest.mark.parametrize("body,flange", [("timber", None), ("shaft/test", None), ("fitting", "beam")])
def test_deformed_interior_port_director_and_force_dual_superposed_world_rotation(body, flange):
    adapter, _, _, _ = small_assembly()
    q = np.random.default_rng(76).normal(scale=.5, size=adapter.ndof)
    for index, _, _ in node_rows(adapter):
        q[index[3:]] *= 80
    rotation = Rotation.from_rotvec(np.deg2rad(20)*np.array([1., -2., 3.])/np.sqrt(14)).as_matrix()
    translation = np.array([4., -9., 6.])
    rotated_q = superpose(adapter, q, rotation, translation)
    transform = np.eye(adapter.ndof)
    for index, _, basis in node_rows(adapter):
        old_theta, new_theta = basis @ q[index[3:]]/1000, basis @ rotated_q[index[3:]]/1000
        transform[np.ix_(index[:3], index[:3])] = basis.T @ rotation @ basis
        transform[np.ix_(index[3:], index[3:])] = basis.T @ finite.so3_left_jacobian_inverse(new_theta) @ rotation @ finite.so3_left_jacobian(old_theta) @ basis
    if body == "timber":
        row = adapter.members[body]; point = row["start"] + 37*row["axis"] + [2., 3., -4.]
    elif body == "shaft/test":
        row = adapter.shafts[body]; point = row["point"] + 23*row["basis"][0] + [1., -2., 3.]
    else:
        point = adapter.fittings[body]["points"][flange] + [2., -3., 4.]
    initial = adapter.port(body, point, q, flange, False)
    rotated = adapter.port(body, point, rotated_q, flange, False)
    assert rotated["position_xyz_mm"] == pytest.approx(rotation @ initial["position_xyz_mm"] + translation, abs=1e-11)
    assert rotated["J_csr"] @ transform == pytest.approx(rotation @ initial["J_csr"].toarray(), abs=1e-12)
    force = np.array([170., -320., 280.])
    assert transform.T @ (rotated["J_csr"].T @ (rotation @ force)) == pytest.approx(initial["J_csr"].T @ force, abs=1e-10)
    initial = adapter.director(body, point, q, [0., 0., 1.], flange, False)
    rotated = adapter.director(body, point, rotated_q, [0., 0., 1.], flange, False)
    assert rotated["current_vector_xyz"] == pytest.approx(rotation @ initial["current_vector_xyz"], abs=1e-13)
    assert rotated["J_csr"] @ transform == pytest.approx(rotation @ initial["J_csr"].toarray(), abs=1e-13)


def test_floor_is_fixed_and_has_zero_jets_without_a_twist_constraint():
    adapter, _, _, _ = small_assembly()
    q = np.zeros(adapter.ndof)
    port = adapter.port("floor", [1., 2., 3.], q)
    director = adapter.director("floor", [1., 2., 3.], q, [0., 0., 1.])
    assert port["position_xyz_mm"] == pytest.approx([1., 2., 3.])
    assert director["current_vector_xyz"] == pytest.approx([0., 0., 1.])
    assert port["J_csr"].nnz == director["J_csr"].nnz == 0
    assert all(row.nnz == 0 for row in port["H_xyz_csr"] + director["H_xyz_csr"])


@pytest.mark.parametrize("body,flange", [("timber", None), ("shaft/test", None), ("fitting", "beam"), ("fitting", None)])
def test_sparse_point_jet_fd_and_reference_linear_port(body, flange):
    adapter, _, _, _ = small_assembly()
    point = np.array([53., 24., 19.])
    q = np.random.default_rng(33).normal(size=adapter.ndof)
    q[3:6] += [18., -11., 25.]
    port = adapter.port(body, point, q, flange)
    direction = np.random.default_rng(41).normal(size=adapter.ndof)
    step = 1e-3
    plus, minus = adapter.port(body, point, q + step*direction, flange, False), adapter.port(body, point, q - step*direction, flange, False)
    assert port["J_csr"] @ direction == pytest.approx((plus["position_xyz_mm"] - minus["position_xyz_mm"])/(2*step), rel=1e-7, abs=1e-8)
    h_direction = np.vstack([row @ direction for row in port["H_xyz_csr"]])
    assert h_direction == pytest.approx((plus["J_csr"] - minus["J_csr"]).toarray()/(2*step), rel=2e-6, abs=2e-9)
    assert port["J_csr"].shape == (3, adapter.ndof)
    if body in ("timber", "shaft/test"):
        index, centers, t, basis = adapter._segment(body, point)
        center = (1 - t)*centers[0] + t*centers[1]
        linear = point_matrix(point, center) @ block_diag(basis, basis)
        expected = np.hstack(((1 - t)*linear, t*linear))
        reference = adapter.port(body, point, np.zeros(adapter.ndof), tangent=False)
        assert reference["local_J"] == pytest.approx(expected, abs=1e-14)
        assert np.array_equal(reference["support_indices"], index)


@pytest.mark.parametrize("body,flange", [("timber", None), ("shaft/test", None), ("fitting", "post")])
def test_material_director_full_jet_preserves_length_and_virtual_work(body, flange):
    adapter, _, _, _ = small_assembly()
    q = np.random.default_rng(34).normal(scale=20., size=adapter.ndof)
    point = np.array([57., 28., 21.]); direction = np.random.default_rng(42).normal(size=adapter.ndof)
    reference = np.array([1., -2., 3.])/np.sqrt(14)
    result = adapter.director(body, point, q, reference, flange)
    step = 1e-3
    plus = adapter.director(body, point, q + step*direction, reference, flange, False)
    minus = adapter.director(body, point, q - step*direction, reference, flange, False)
    assert np.linalg.norm(result["current_vector_xyz"]) == pytest.approx(1., abs=1e-12)
    assert result["J_csr"] @ direction == pytest.approx((plus["current_vector_xyz"] - minus["current_vector_xyz"])/(2*step), rel=1e-7, abs=1e-10)
    actual_h = np.vstack([row @ direction for row in result["H_xyz_csr"]])
    assert actual_h == pytest.approx((plus["J_csr"] - minus["J_csr"]).toarray()/(2*step), rel=2e-6, abs=1e-10)
    force = np.array([70., -110., 150.])
    assert direction @ (result["J_csr"].T @ force) == pytest.approx(force @ (result["J_csr"] @ direction), abs=1e-13)


def test_distinct_capture_planes_objective_closing_sign_with_moving_host_director():
    adapter, _, _, _ = small_assembly()
    shaft_point, host_point = np.array([54., 26., 21.]), np.array([57., 26., 21.])
    dref = np.array([1., 0., 0.])
    rotation = Rotation.from_rotvec([.13, -.21, .17]).as_matrix()
    q = superpose(adapter, np.zeros(adapter.ndof), rotation, [4., -9., 6.])
    shaft = adapter.port("shaft/test", shaft_point, q, tangent=False)
    host = adapter.port("timber", host_point, q, tangent=False)
    direction = adapter.director("timber", host_point, q, dref, tangent=False)
    gap = -direction["current_vector_xyz"] @ (shaft["position_xyz_mm"] - host["position_xyz_mm"]) + dref @ (shaft_point - host_point)
    assert gap == pytest.approx(0., abs=1e-12)


def test_bent_two_element_circular_proxy_does_not_have_an_exact_material_roll_gauge():
    points = np.array([[0., 0., 0.], [50., 0., 0.], [100., 0., 0.]])
    beams = [finite.CorotationalBeam.from_properties(points[i:i+2], np.eye(3), 50., 400., 400., 800., 200000., 76923., .9) for i in range(2)]
    q = np.zeros((3, 6))
    q[:, :3] = [[0., 0., 0.], [-1., 3., 2.], [-4., 12., 7.]]
    q[:, 3:] = [[30., 150., 100.], [80., 200., 280.], [100., 250., 400.]]
    initial = sum(beam.energy(q[i:i+2].ravel()) for i, beam in enumerate(beams))
    rolled = q.copy()
    for i in range(3):
        rolled[i, 3:] = 1000*so3_log(so3_exp(q[i, 3:]/1000) @ so3_exp([np.deg2rad(20.), 0., 0.]))
    changed = sum(beam.energy(rolled[i:i+2].ravel()) for i, beam in enumerate(beams))
    assert initial == pytest.approx(2068966.5174449128, rel=1e-12)
    assert (changed - initial)/initial == pytest.approx(-1.8193824865464002e-5, rel=1e-8)
    assert finite.FiniteMechanicsAdapter.finite_shaft_twist_gauge_qualified is False


def test_unsupported_interpolation_and_fitting_clamp_are_rejected():
    q = np.zeros(12); q[9] = 1000*np.deg2rad(91.)
    with pytest.raises(ValueError, match="neighboring director"):
        finite.interpolated_rotation(q, .5)
    with pytest.raises(ValueError, match="clamp"):
        finite.ObjectiveCondensedFitting(np.array([[0., 0., 0.], [1., 1., 0.]]), np.eye(12))
    adapter, _, _, _ = small_assembly()
    with pytest.raises(ValueError, match="specific fitting flange"):
        adapter.director("fitting", [1., 2., 3.], np.zeros(adapter.ndof), [0., 0., 1.])


def test_frozen_source_pins_cannot_be_overridden():
    with pytest.raises(ValueError, match="conflict"):
        finite.source_pins({"scripts/thin_bolted_common_shaft.py": "0"*64})


def test_arc_chord_axial_approximation_matches_known_geometry_and_refines():
    result = finite.chord_refinement_coupon()
    axial = []
    for row in result["records"]:
        assert row["spurious_axial_energy_nmm"] == pytest.approx(row["exact_chord_shortening_axial_energy_nmm"], rel=1e-9)
        assert row["bending_energy_nmm"] == pytest.approx(result["expected_pure_bending_energy_nmm"], rel=1e-10)
        axial.append(row["spurious_axial_energy_nmm"])
    assert axial[0]/axial[1] == pytest.approx(16., rel=1e-3)
    assert axial[1]/axial[2] == pytest.approx(16., rel=1e-3)
    assert result["candidate_refinement_established"] is False


def test_failed_finite_roll_coupon_records_nonzero_work_without_constraint():
    result = finite.circular_material_roll_coupon()
    assert result["common_material_roll_virtual_work_nmm_per_rad"] == pytest.approx(-166.64283647952834, rel=1e-10)
    assert result["finite_material_roll_gauge_established"] is False
    assert result["constraints_added"] == 0
