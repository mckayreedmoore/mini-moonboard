"""Independent circular-beam, gap, gauge and datum coupons without frame solves."""

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_common_shaft as common
from scripts import thin_bolted_frame_mechanics as frame


class RigidHostFixture:
    def __init__(self, names):
        self.names = list(names)
        self.ndof = 6 * len(self.names)
        self.K = csr_matrix((self.ndof, self.ndof))
        self.members = {}
        self.geo = {"members": [], "bodies": [{"id": n, "mass_kg": 1., "center_xyz_mm": [0., 0., 0.]} for n in names]}

    def embed(self, block, index):
        result = np.zeros((len(block), self.ndof))
        result[:, index] = block
        return csr_matrix(result)

    def port(self, body, point, flange=None):
        index = np.arange(6 * self.names.index(body), 6 * (self.names.index(body) + 1))
        return self.embed(frame.point_matrix(point, np.zeros(3)), index)

    def rigid_modes(self):
        block = np.vstack((np.hstack((np.eye(3), frame.cross_matrix(frame.REFERENCE))),
                           np.hstack((np.zeros((3, 3)), np.eye(3) * frame.ROTATION_SCALE))))
        result = np.zeros((self.ndof, 6))
        for i in range(len(self.names)):
            result[6 * i:6 * i + 6] = block
        return result


def shared_gap_fixture():
    return {"axis_id": "coupon", "body": "shaft/coupon", "point": np.zeros(3), "basis": np.eye(3),
            "diameter_mm": 10., "bore_diameter_mm": 10.2, "shaft_interval_mm": [-1., 11.],
            "surfaces": [{"host": name, "kind": "wood", "interval_mm": [0., 10.], "grain_axis_xyz": [0., 1., 0.]}
                         for name in ("a", "b")],
            "ends": [{"end": end, "host": name, "flange": None, "support_s_mm": s, "pressure_face_s_mm": s,
                      "direction_on_shaft_xyz": direction, "own_washer_thickness_mm": 0., "washer_id": end}
                     for end, name, s, direction in (("head", "a", -1., [-1., 0., 0.]), ("nut", "b", 11., [1., 0., 0.]))],
            "metal_roles": [{"id": "couponmetal", "kind": "shaft", "volume_mm3": 100.,
                             "center_of_mass_xyz_mm": [5., 0., 0.]}]}


@pytest.mark.parametrize("dof", [0, 1, 2])
def test_circular_cantilever_matches_axial_and_two_bending_shear_answers(dof):
    L, d, E, G = 1000., 12.7, 200000., 200000. / 2.6
    A, I, _ = common.circular_properties(d)
    K, index, _ = common.reduced_shaft_matrix([0., L], d, E, G)
    free = index[-1]
    force = np.eye(6)[dof]
    q = np.linalg.solve(K.toarray()[np.ix_(free, free)], force)
    expected = L / (E * A) if dof == 0 else L**3 / (3 * E * I) + L / (.9 * G * A)
    assert q[dof] == pytest.approx(expected, rel=1e-12)


def test_unequal_opposed_loads_recover_span_shear_larger_than_resultant():
    K, index, elements = common.reduced_shaft_matrix([0., 100., 200., 300.], 12.7, 200000., 200000. / 2.6)
    applied = np.zeros(K.shape[0])
    applied[index[1, 1]], applied[index[2, 1]] = 4., -3.
    q = np.zeros(K.shape[0])
    free = index[1:].ravel()
    q[free] = np.linalg.solve(K.toarray()[np.ix_(free, free)], applied[free])
    recovered = []
    for element in elements:
        value = np.zeros(12)
        selected = element["dofs"] >= 0
        value[selected] = q[element["dofs"][selected]] * element["scale"][selected]
        recovered.append(element["local_K"] @ value)
    assert recovered[0][1] == pytest.approx(-1., abs=1e-10)
    assert recovered[0][5] == pytest.approx(200., abs=1e-8)
    assert recovered[1][1] == pytest.approx(3., abs=1e-10)
    np.testing.assert_allclose(recovered[2], 0., atol=1e-8)


def test_series_bore_gaps_add_and_each_host_has_own_compliance():
    assembly = RigidHostFixture(["a", "b"])
    diagonal = np.full(assembly.ndof, 1e9)
    diagonal[7] = 0.
    assembly.K = csr_matrix(np.diag(diagonal))
    system = common.CommonShaftSystem(assembly, [shared_gap_fixture()], wood_foundation_n_mm2=10., max_segment_mm=5.)
    applied = np.zeros(assembly.ndof)
    applied[7] = 1.
    response = frame.compatible_contact_solve(assembly.K, applied, system.bearing_groups, system.end_captures, [])
    assert response["converged"]
    # Each100N/mm host adds0.01mm elastic slip and its own0.1mm radial gap.
    assert response["q"][7] == pytest.approx(.22, abs=1e-6)
    assert system.recovery(response["q"])[0]["first_element_internal_twist_end_action_nmm"] == pytest.approx(0., abs=1e-9)


def test_common_rigid_motion_creates_no_bearing_or_capture_forces():
    assembly = RigidHostFixture(["a", "b"])
    system = common.CommonShaftSystem(assembly, [shared_gap_fixture()])
    rigid = assembly.rigid_modes()
    assert max(abs(assembly.K @ rigid).ravel()) < 1e-6
    for row in [*system.bearing_groups, *system.end_captures]:
        assert max(abs(row["B"] @ rigid).ravel()) < 1e-10
    for row in system.bearing_groups:
        # Radial bearing has no axial component, friction or shaft torque.
        assert row["ka"] == 0.
    assert next(iter(system.shafts.values()))["index"][0, 3] == -1


def test_frozen_geometry_has_actual82wood72steel_and_each_own_washer_thickness():
    shafts = common.read_inputs()
    assert len(shafts) == 70
    assert sum(r["kind"] == "wood" for s in shafts for r in s["surfaces"]) == 82
    assert sum(r["kind"] == "steel" for s in shafts for r in s["surfaces"]) == 72
    special = next(s for s in shafts if s["axis_id"] == "thin_factory_bolt_025")
    assert special["ends"][0]["own_washer_thickness_mm"] == pytest.approx(3.0734, abs=1e-6)
    assert special["ends"][1]["own_washer_thickness_mm"] == pytest.approx(3.3528, abs=1e-6)
    rear = next(s for s in shafts if s["axis_id"] == "rail_rear_bolt_left_1")
    actual = {r["host"]: r["interval_mm"] for r in rear["surfaces"]}
    np.testing.assert_allclose(actual["base_floor_left"], [0., 38.1], atol=1e-6)
    np.testing.assert_allclose(actual["lumber_leg_left"], [38.1, 88.9], atol=1e-6)


def test_real_geometry_augmentation_preserves_rigid_motion_without_short_segments():
    shafts = common.read_inputs()
    names = sorted({r["host"] for s in shafts for r in s["surfaces"]})
    assembly = RigidHostFixture(names)
    system = common.CommonShaftSystem(assembly, shafts)
    rigid = assembly.rigid_modes()
    assert len(system.bearing_groups) == 308
    assert len(system.end_captures) == 140
    assert min(np.diff(s["stations"]).min() for s in system.shafts.values()) > 1e-6
    assert max(float(abs(r["B"] @ rigid).max()) for r in [*system.bearing_groups, *system.end_captures]) < 3e-6
    assert max(float(abs(r["B"] @ rigid[:, 3:]).max()) for r in system.bearing_groups) < 3e-6


def test_own_major_diameter_gap_is_independent_of_elastic_section_scale():
    assembly = RigidHostFixture(["a", "b"])
    system = common.CommonShaftSystem(assembly, [shared_gap_fixture()], diameter_scale=.8)
    assert all(row["clearance"] == pytest.approx(.1) for row in system.bearing_groups)
    recovered = system.recovery(np.zeros(assembly.ndof))[0]
    assert recovered["elastic_section_diameter_mm"] == 8.
    assert recovered["bearing_contact_major_diameter_mm"] == 10.
    invalid = shared_gap_fixture()
    invalid["bore_diameter_mm"] = 9.
    with pytest.raises(ValueError, match="nonnegative own bore gap"):
        common.CommonShaftSystem(RigidHostFixture(["a", "b"]), [invalid])


def test_real_metal_gravity_remap_preserves_every_role_without_duplicate_host_mass():
    import json

    report = json.loads((frame.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json").read_text())
    original = {"loads": report["body_applied_loads"]}
    shafts = common.read_inputs()
    names = sorted({r["host"] for s in shafts for r in s["surfaces"]})
    assembly = RigidHostFixture(names)
    system = common.CommonShaftSystem(assembly, shafts)
    migrated = system.remap_bolt_gravity(original)
    physical = [r for r in migrated["loads"] if r["id"].startswith("physical-bolt-metal/")]
    assert len(physical) == 350
    assert len({r["id"] for r in physical}) == 350
    assert len({r["body"] for r in physical}) == 70
    retained = [r for r in migrated["loads"] if r["id"].startswith("bolt-weight/")]
    assert len(retained) == 274
    original_bodies = {r["body"] for r in report["body_equilibrium_residuals"]}
    assert all(r["body"] in original_bodies for r in retained)
    assert max(abs(v) for v in migrated["shaft_metal_gravity_remap_residual_n_nmm"]) < 1e-5


def test_physical_recovery_keeps_distinct_capture_points_and_steel_bearing_moment():
    assembly = RigidHostFixture(["a", "b", "f", "panel"])
    shaft = shared_gap_fixture()
    shaft["surfaces"].append({"host": "f", "kind": "steel", "interval_mm": [-.5, 0.],
                               "flange": "beam", "receiver": "a", "entry_xyz_mm": [0., 0., 0.]})
    shaft["ends"][0].update(host="f", flange="beam", support_s_mm=-.5)
    system = common.CommonShaftSystem(assembly, [shaft])
    panel = {"id": "paneltest", "axis_id": "paneltest", "kind": "panel_screw", "first": "panel", "second": "b",
             "point_xyz_mm": [0., 0., 0.], "basis": np.eye(3)}
    groups = [panel, *system.bearing_groups]
    forces = [np.zeros(3)] + [np.zeros(3) for _ in system.bearing_groups]
    steel_groups = [i for i, g in enumerate(groups) if g.get("surface", {}).get("kind") == "steel"]
    forces[steel_groups[0]], forces[steel_groups[1]] = np.array([0., 1., 0.]), np.array([0., 2., 0.])
    response = {"q": np.zeros(assembly.ndof), "connector_local_force_n": forces,
                "normal_contact_force_n": np.array([3., 4.]), "nonbearing_no_slip_removed": []}
    case = {"case_id": "coupon", "accessory_placement": "coupon", "loads": [],
            "applied_force_xyz_n": [0., 0., 0.], "applied_moment_about_global_origin_xyz_nmm": [0., 0., 0.]}
    result = system.compatible_actions(case, response, groups, system.end_captures, [])
    assert len(result["common_shaft_bearing_actions"]) == 6
    assert result["shaft_end_capture_actions"][0]["point_xyz_mm"] != result["shaft_end_capture_actions"][0]["host_support_point_xyz_mm"]
    port = result["common_shaft_steel_port_actions"][0]
    np.testing.assert_allclose(port["force_on_steel_xyz_n"], [3., 3., 0.])
    expected_moment = sum(np.cross(np.array(groups[i]["point_xyz_mm"]), forces[i]) for i in steel_groups)
    np.testing.assert_allclose(port["moment_on_steel_at_point_xyz_nmm"], expected_moment)
    assert port["moment_on_steel_at_point_xyz_nmm"][2] != 0.
    totals = np.sum([np.r_[r["force_xyz_n"], r["moment_about_reference_xyz_nmm"]]
                     for r in result["body_equilibrium_residuals"]], axis=0)
    np.testing.assert_allclose(totals, 0., atol=1e-12)
    assert result["equilibrium_verification"]["all_bodies"] == 5
    assert not result["equilibrium_verification"]["all_body_and_global_checks_pass"]
    cut = next(c for c in result["common_shaft_section_cut_actions"][0]["cuts"]
               if abs(c["station_from_axis_point_mm"]) < 1e-10)
    np.testing.assert_allclose(cut["local_N_V1_V2_T_M1_M2_n_nmm"],
                               np.r_[[3., 3., 0.], expected_moment])


@pytest.mark.parametrize("parameter,value", [("steel_E_mpa", np.nan), ("diameter_scale", np.inf),
                                            ("wood_foundation_n_mm2", np.nan), ("plate_foundation_n_mm2", np.inf),
                                            ("end_capture_n_mm", np.nan), ("max_segment_mm", np.inf)])
def test_scenario_properties_reject_nonfinite_inputs(parameter, value):
    with pytest.raises(ValueError, match="finite"):
        common.CommonShaftSystem(RigidHostFixture(["a", "b"]), [shared_gap_fixture()], **{parameter: value})
