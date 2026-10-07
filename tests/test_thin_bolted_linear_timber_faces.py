"""Small linear contact coupons; no candidate assembly, CAD or global solve."""

import copy

import numpy as np
import pytest
from scipy.sparse import csr_matrix, vstack

from scripts import thin_bolted_linear_timber_faces as linear
from scripts import thin_bolted_numerical_step as numerical


def coupon(divisions=2):
    proof = linear.faces.coupon_proof(divisions)
    descriptors = [row for row in linear.faces.describe_contacts(proof, 1.)
                   if row["source_descriptor"]["patch_id"] == "patch-0"]
    assembly = linear.frame.ElasticAssembly.__new__(linear.frame.ElasticAssembly)
    assembly.ndof = 24
    assembly.members = {name: {"start": np.array([-50., 0., 0.]), "axis": np.array([1., 0., 0.]),
        "stations": np.array([0., 100.]), "index": np.arange(begin, begin+12).reshape(2, 6)}
        for name, begin in ((descriptors[0]["first"], 0), (descriptors[0]["second"], 12))}
    assembly.fittings, assembly.panels, assembly.panel_offsets = {}, {}, {}
    return assembly, linear.linear_contact_rows(assembly, descriptors)


def fields(assembly, contacts, q):
    return numerical.physical_fields(csr_matrix((assembly.ndof, assembly.ndof)), np.zeros(assembly.ndof), [],
        vstack([row["B"] for row in contacts]), np.array([row["stiffness"] for row in contacts]), q, tangent=True)


def translated(z=0., x=0., y=0.):
    q = np.zeros((4, 6))
    q[:2, :3] = [x, y, z]
    return q.ravel()


@pytest.mark.parametrize("z,force,energy", [(-.02, 96., .96), (.02, 0., 0.), (0., 0., 0.)])
def test_uniform_compression_opening_and_zero_reference(z, force, energy):
    assembly, rows = coupon()
    _, actual, _, _, normals, _ = fields(assembly, rows, translated(z))
    assert normals.sum() == pytest.approx(force)
    assert actual == pytest.approx(energy)
    assert sum(row["stiffness"] for row in rows) == 4800.


def test_friction_free_slip_preserves_force_and_has_zero_tangent_work():
    assembly, rows = coupon()
    before = fields(assembly, rows, translated(-.02))
    after = fields(assembly, rows, translated(-.02, 3., -5.))
    np.testing.assert_allclose(before[0], after[0], atol=1e-12)
    assert before[1] == pytest.approx(after[1])
    for index in (0, 1, 6, 7):
        assert after[0][index] == 0.
        assert np.linalg.norm(after[2].getcol(index).toarray()) == 0.


def test_every_contact_annihilates_all_six_linear_rigid_modes():
    assembly, rows = coupon()
    C = vstack([row["B"] for row in rows])
    np.testing.assert_allclose(C @ assembly.rigid_modes(), 0., atol=1e-12)


def test_off_axis_force_dual_wrench_and_original_virtual_work():
    assembly, rows = coupon()
    # One quadrant carries one off-axis normal resultant.
    row, q = rows[-1], translated(-.02)
    gradient, energy, H, _, normals, _ = fields(assembly, [row], q)
    point, normal = np.asarray(row["point_xyz_mm"]), np.asarray(row["direction_xyz"])
    force = normals[0]*normal
    first, second = np.r_[force, np.cross(point, force)], np.r_[-force, np.cross(point, -force)]
    assert np.linalg.norm(first[3:]) > 0.
    np.testing.assert_allclose(first+second, 0., atol=1e-12)
    direction = np.random.default_rng(708).normal(size=24)
    relative = (assembly.port(row["first"], point)-assembly.port(row["second"], point)) @ direction
    assert gradient @ direction == pytest.approx(-force @ relative)
    h = 1e-6
    plus, minus = fields(assembly, [row], q+h*direction), fields(assembly, [row], q-h*direction)
    assert (plus[1]-minus[1])/(2*h) == pytest.approx(gradient @ direction, rel=1e-9)
    np.testing.assert_allclose(H @ direction, (plus[0]-minus[0])/(2*h), rtol=1e-9, atol=1e-8)
    assert energy > 0.


def test_area_and_partly_open_rocking_match_rectangle_quadrature():
    q = np.zeros((4, 6)); q[:2, 4] = 30.  # theta_y=.03 radians.
    q[:2, 2] = -.03*np.array([-50., 50.])
    errors = []
    exact = .5*60.*.03**2*40.**3/3.
    for divisions in (2, 4, 8):
        assembly, rows = coupon(divisions)
        _, energy, _, _, normals, _ = fields(assembly, rows, q.ravel())
        assert np.count_nonzero(normals) == len(rows)//2
        assert energy/exact == pytest.approx(1.-1./divisions**2)
        errors.append(abs(energy-exact))
    assert errors == sorted(errors, reverse=True)


def test_coordinate_map_exports_original_order_and_does_not_mutate_members():
    assembly, _ = coupon()
    before = copy.deepcopy(assembly.members)
    mapping = linear.timber_coordinate_map(assembly)
    assert mapping["schema"] == linear.MAP_SCHEMA and mapping["ndof"] == 24 and mapping["rotation_scale"] == 1000.
    assert [row["member"] for row in mapping["members"]] == list(assembly.members)
    for row, original in zip(mapping["members"], before.values(), strict=True):
        np.testing.assert_array_equal(row["node_dof_indices"], original["index"])
        np.testing.assert_array_equal(row["node_reference_centers_xyz_mm"], [[-50., 0., 0.], [50., 0., 0.]])
        np.testing.assert_array_equal(assembly.members[row["member"]]["index"], original["index"])


def recovered_fixture():
    assembly, rows = coupon()
    q = translated()
    recovered = {"contact_actions": [{"id": row["id"], "kind": row["kind"], "first": row["first"], "second": row["second"],
        "point_xyz_mm": row["point_xyz_mm"], "compression_n": 0., "force_on_first_xyz_n": [0., 0., 0.],
        "case_id": "coupon", "accessory_placement": "coupon", "state_id": "coupon"} for row in rows]}
    prepared = {"contacts": rows, "coordinate_map": linear.timber_coordinate_map(assembly),
                "source_sha256": linear.source_pins()}
    return recovered, prepared, q


def test_recovery_preserves_zero_rows_source_metadata_and_input_ownership():
    recovered, prepared, q = recovered_fixture()
    before = copy.deepcopy(recovered)
    result = linear.stamp_recovered_actions(recovered, prepared, q)
    assert recovered == before
    assert len(result["timber_face_contact_actions"]) == 4
    assert result["linear_timber_coordinate_map"] == prepared["coordinate_map"]
    for row in result["timber_face_contact_actions"]:
        assert row["force_on_second_xyz_n"] == row["moment_on_first_at_point_xyz_nmm"] == [0., 0., 0.]
        assert row["compression_n"] == row["relative_closure_mm"] == 0.
        assert row["source_descriptor"]["cell_area_mm2"] == row["cell_area_mm2"]
        assert row["state_id"] == "coupon" and row["physical_pressure_or_current_overlap_resolved"] is False


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "host", "point", "force", "compression", "couple", "dual", "q"])
def test_recovery_rejects_missing_or_contradictory_fields(mutation):
    recovered, prepared, q = recovered_fixture()
    if mutation == "missing":
        recovered["contact_actions"].pop()
    elif mutation == "duplicate":
        recovered["contact_actions"][1] = recovered["contact_actions"][0]
    elif mutation == "host":
        recovered["contact_actions"][0]["first"] = "foreign"
    elif mutation == "point":
        recovered["contact_actions"][0]["point_xyz_mm"] = [9., 8., 7.]
    elif mutation == "force":
        recovered["contact_actions"][0]["force_on_first_xyz_n"] = [1., 0., 0.]
    elif mutation == "compression":
        recovered["contact_actions"][0]["compression_n"] = 1.
    elif mutation == "couple":
        recovered["contact_actions"][0]["moment_at_point_model_xyz_nmm"] = [0., 1., 0.]
    elif mutation == "dual":
        recovered["contact_actions"][0]["force_on_second_xyz_n"] = [1., 0., 0.]
    else:
        q[0] = np.nan
    with pytest.raises(ValueError):
        linear.stamp_recovered_actions(recovered, prepared, q)


def test_source_pins_reject_a_changed_frozen_producer():
    with pytest.raises(ValueError, match="contradictory"):
        linear.source_pins({"scripts/thin_bolted_frame_mechanics.py": "0"*64})
