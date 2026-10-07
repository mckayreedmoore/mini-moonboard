"""Composition/current-action coupons without preparing or solving a frame."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_frame as finite
from scripts import thin_bolted_finite_panel_adapter as panels


def fixture_file(name):
    path = Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def descriptor(id_, kind, first, second, point, direction, owner, axial=0., lateral=0., gap=0., sign=1., second_point=None):
    second_point = point if second_point is None else second_point
    return {"id": id_, "kind": kind, "first": first, "second": second,
        "reference_first_point_xyz_mm": list(point), "reference_second_point_xyz_mm": list(second_point),
        "reference_director_xyz": list(direction), "director_owner": owner, "first_port_kind": "point",
        "axial_stiffness_n_mm": axial, "lateral_stiffness_n_mm": lateral, "radial_gap_mm": gap,
        "axial_sign": sign, "reference_axial_projection_mm": sign * float(np.array(direction) @ (np.array(point) - second_point)),
        "axial_tension_only": True, "source_descriptor": {}}


def small_potential(with_panel=False, with_load=False):
    m = fixture_file("test_thin_bolted_finite_mechanics.py")
    mechanical, _, assembly, _ = m.small_assembly()
    point = np.array([51., 22., 31.])
    direction = np.array([1., 2., -3.]) / np.sqrt(14)
    interactions = [descriptor("bearing", "common_shaft_bearing", "shaft/test", "timber", point, direction, "timber", lateral=31., gap=.1),
                    descriptor("capture", "shaft_end_capture", "shaft/test", "timber", point + 4 * direction, direction, "timber", axial=17., sign=-1., second_point=point)]
    panel_map, loads = {}, {}
    if with_panel:
        p = fixture_file("test_thin_bolted_finite_panel_adapter.py")
        raw = p.panel(False); raw["screws"] = [p.screw(raw)]
        offset = mechanical.ndof; mechanical.ndof += 3 * raw["basis"].size
        panel = panels.FinitePanelAdapter(raw, np.arange(offset, mechanical.ndof), mechanical.ndof)
        panel_map["kicker_left"] = panel
        zero = np.zeros(panel.local_size)
        load = SimpleNamespace(loads=[], point_loads=[], retained_rigid_correction_n=zero.copy(), reference_port_alignment_correction_n=zero.copy())

        def external(q, tangent, reference):
            return {"energy_nmm": 0., "gradient_n": np.zeros(mechanical.ndof), "hessian_csr": csr_matrix((mechanical.ndof, mechanical.ndof)) if tangent else None,
                    "retained_rigid_correction_wrench_n_nmm": np.zeros(6), "reference_port_alignment_wrench_n_nmm": np.zeros(6)}

        load.external = external; loads["kicker_left"] = load
        screw = raw["screws"][0]
        midpoint = panel.origin + panel.axes[:, :2] @ [120., 140.]
        value = descriptor("screw", "panel_screw", "kicker_left", "timber", midpoint, panel.axes[:, 2], "kicker_left", axial=29., lateral=41.)
        value["first_port_kind"] = "projected_ring"; value["source_descriptor"]["axis_id"] = screw["axis_id"]
        interactions.append(value)
        back = panel.origin + panel.axes @ [180., 230., -9.128125]
        interactions.append(descriptor("panel-contact", "panel_contact", "kicker_left", "timber", back, panel.axes[:, 2], "kicker_left", axial=51., sign=-1.))
    dead = [{"id": "fitting-gravity", "body": "fitting", "point_xyz_mm": [230., 251., 200.], "force_xyz_n": [0., 0., -10.]}] if with_load else []
    potential = finite.FiniteFramePotential(mechanical, panel_map, loads, interactions, dead,
        case={"state_id": "method-coupon", "case_id": "coupon", "accessory_placement": "coupon"})
    return potential, assembly, m


def test_current_connection_actions_and_director_couples_close_pair_moments():
    p, _, _ = small_potential()
    q = np.random.default_rng(75).normal(scale=.2, size=p.ndof)
    q[3:6] *= 100.
    result = p.response(q, False, recover_actions=True)
    assert result["hessian_csr"] is None
    assert len(result["finite_interaction_actions"]) == 2
    for action in result["finite_interaction_actions"]:
        F = np.array(action["force_on_first_xyz_n"])
        p1, p2 = np.array(action["point_on_first_xyz_mm"]), np.array(action["point_on_second_xyz_mm"])
        moment = np.cross(p1 - p2, F) + action["moment_on_first_at_current_point_xyz_nmm"] + np.array(action["moment_on_second_at_current_point_xyz_nmm"])
        np.testing.assert_allclose(moment, 0., atol=1e-9)
        np.testing.assert_allclose(action["force_on_second_xyz_n"], -F, atol=1e-12)
        assert action["state_id"] == "method-coupon"


def test_composed_full_tangent_and_gradient_only_paths_share_actual_residual():
    p, _, _ = small_potential(True, True)
    q = np.random.default_rng(27).normal(scale=.1, size=p.ndof)
    q[3:6] *= 80.
    full, compact = p.response(q), p.response(q, False)
    np.testing.assert_allclose(full["gradient_n"], compact["gradient_n"], atol=2e-8)
    assert full["energy_nmm"] == pytest.approx(compact["energy_nmm"], abs=1e-8)
    direction = np.random.default_rng(28).normal(size=p.ndof); direction /= np.linalg.norm(direction)
    h = 1e-4
    plus, minus = p.response(q + h * direction, False), p.response(q - h * direction, False)
    assert direction @ full["gradient_n"] == pytest.approx((plus["energy_nmm"] - minus["energy_nmm"]) / (2 * h), rel=2e-7, abs=2e-7)
    np.testing.assert_allclose(full["hessian_csr"] @ direction, (plus["gradient_n"] - minus["gradient_n"]) / (2 * h), rtol=3e-6, atol=3e-5)
    assert not compact["zero_jet_h_placeholders_are_a_physical_tangent"]


def test_current_pose_replay_requires_no_stiffness_or_response():
    p, _, _ = small_potential(True)
    q = np.random.default_rng(80).normal(scale=.2, size=p.ndof)
    q[3:6] *= 100.
    for body, point, flange in (("timber", [57., 18., 66.], None), ("shaft/test", [-115., 80., 61.], None),
                                ("fitting", [220., 245., 190.], "beam"), ("fitting", [221., 246., 191.], None),
                                ("floor", [1., 2., 0.], None)):
        actual = p.mechanics.port(body, point, q, flange, False)
        replay = finite.current_pose_from_map(p.map, body, point, q, flange=flange)
        np.testing.assert_allclose(replay["position_xyz_mm"], actual["position_xyz_mm"], atol=1e-10)
    panel = p.panels["kicker_left"]
    for projected in (False, True):
        point = panel.origin + panel.axes @ [120., 140., 9.128125]
        actual = panel.screw_port(q, panel.panel["screws"][0], False) if projected else panel.point_port(q, point, False)
        replay = finite.current_pose_from_map(p.map, "kicker_left", point, q, projected_ring=projected)
        np.testing.assert_allclose(replay["position_xyz_mm"], actual["position_xyz_mm"], atol=1e-10)
        np.testing.assert_allclose(replay["current_vector_xyz"], actual["normal_xyz"], atol=1e-12)


def test_reference_and_finite_common_rigid_motion_are_objective_without_loads():
    p, _, fixture = small_potential(True)
    q = np.zeros(p.ndof)
    rotation = Rotation.from_rotvec([.21, -.19, .17]).as_matrix(); translation = np.array([3., -5., 7.])
    q = fixture.superpose(p.mechanics, q, rotation, translation)
    panel_fixture = fixture_file("test_thin_bolted_finite_panel_adapter.py")
    panel = p.panels["kicker_left"]
    q[panel.indices] = panel_fixture.rigid_q(panel, rotation, translation)
    response = p.response(q, False, recover_actions=True)
    assert response["energy_nmm"] < 1e-15
    assert np.linalg.norm(response["gradient_n"]) < 1e-6
    assert response["panel_generalized_load_corrections"][0]["physical_point_forces_or_pressure_representation"] is False


def test_affine2point_gravity_preserves_member_mass_centroid_and_source_ids():
    _p, assembly, _ = small_potential()
    member = assembly.members["timber"]
    member["axis"] = member["source"]["axis"]
    center = member["start"] + 93. * member["axis"] + np.array([1., 2., -1.])
    load = {"id": "self-weight/timber", "body": "timber", "point_xyz_mm": center.tolist(), "force_xyz_n": [0., 0., -100.]}
    rows = finite.mechanical_load_ports(assembly, {"loads": [load]}, [])
    assert len(rows) == 4
    assert len({row["id"] for row in rows}) == 4
    assert sum(row["source_fraction"] for row in rows) == pytest.approx(1., abs=1e-14)
    mean = sum((row["source_fraction"] * np.array(row["point_xyz_mm"]) for row in rows), np.zeros(3))
    np.testing.assert_allclose(mean, center, atol=1e-12)
    np.testing.assert_allclose(np.sum([row["force_xyz_n"] for row in rows], axis=0), [0., 0., -100.], atol=1e-12)


def test_corner_xy_pairs_remain_zero_rows_when_their_contact_is_disabled():
    p, _, _ = small_potential()
    tangents = [{"id": "t" + str(i), "first": "virtual-corner", "physical_first": "timber", "floor_support_id": "timber/floor-0",
                 "normal_contact_id": "timber/floor-0", "point_xyz_mm": [0., 0., 0.], "direction_xyz": np.eye(3)[i].tolist(), "stiffness": 25.} for i in (0, 1)]
    p.interactions = finite.describe_interactions([], [], tangents)
    q = np.zeros(p.ndof); q[0] = .1
    enabled = p.response(q, False, recover_actions=True)
    disabled = p.response(q, False, recover_actions=True, disabled_floor_support_ids=["timber/floor-0"])
    action = disabled["finite_interaction_actions"][0]
    assert action["first"] == "timber"
    assert not action["interaction_enabled"]
    np.testing.assert_allclose(action["force_on_first_xyz_n"], 0.)
    assert enabled["component_potential_energies_nmm"]["connections"] > 0.
    assert disabled["component_potential_energies_nmm"]["connections"] == 0.


def test_floor_activation_access_reports_own_corner_normal_and_fixed_pattern():
    p, _, _ = small_potential()
    support = "timber/floor-0"
    normal = {"id": support, "kind": "floor_normal", "first": "timber", "second": "floor",
              "point_xyz_mm": [0., 0., 0.], "direction_xyz": [0., 0., 1.], "stiffness": 25.}
    tangents = [{"id": support + "/xy-" + str(i), "first": "timber", "floor_support_id": support,
                 "normal_contact_id": support, "point_xyz_mm": [0., 0., 0.],
                 "direction_xyz": np.eye(3)[i].tolist(), "stiffness": 25.} for i in (0, 1)]
    p.interactions = finite.describe_interactions([], [normal], tangents)
    q = np.zeros(p.ndof)
    indices = p.mechanics.members["timber"]["index"]
    q[indices[:, 0]], q[indices[:, 2]] = .2, -.1
    bearing = p.response(q, False, recover_actions=True)
    assert bearing["floor_normal_reactions_n"] == {support: pytest.approx(2.5)}
    assert bearing["floor_xy_enabled_support_ids"] == [support]
    assert bearing["disabled_floor_support_ids"] == []
    q[indices[:, 2]] = .1
    open_corner = p.response(q, False, recover_actions=True, disabled_floor_support_ids=[support])
    assert open_corner["floor_normal_reactions_n"] == {support: 0.}
    assert open_corner["floor_xy_enabled_support_ids"] == []
    assert open_corner["disabled_floor_support_ids"] == [support]
    assert len(open_corner["finite_interaction_actions"]) == 2
    assert not open_corner["floor_no_slip_or_contact_stability_qualified"]


def test_frozen_isotropic_replacement_is_used_once_without_legacy_shaft_energy(monkeypatch):
    replacement = fixture_file("test_thin_bolted_isotropic_shaft.py").small_adapter()
    p = finite.FiniteFramePotential(replacement.mechanics, {}, {}, [], [], shaft_replacement=replacement)
    q = np.random.default_rng(53).normal(scale=.07, size=p.ndof)
    q[3:6] *= 80.
    expected = replacement.replacement_response(q)
    original = replacement.replacement_response
    calls = []

    def counted(q, tangent):
        calls.append(tangent)
        return original(q, tangent)

    def legacy_response_is_forbidden(*args, **kwargs):
        raise AssertionError("legacy finite shaft energy would be duplicated")

    monkeypatch.setattr(replacement, "replacement_response", counted)
    monkeypatch.setattr(replacement.mechanics, "response", legacy_response_is_forbidden)
    actual = p.response(q)
    assert calls == [True]
    assert actual["shaft_elasticity_replaced_without_double_count"]
    assert actual["energy_nmm"] == pytest.approx(expected["energy_nmm"], abs=1e-12)
    np.testing.assert_allclose(actual["gradient_n"], expected["gradient_n"], atol=1e-12)
    np.testing.assert_allclose(actual["hessian_csr"].toarray(), expected["hessian_csr"].toarray(), atol=1e-12)


def test_old_independent_bolt_ports_are_rejected():
    with pytest.raises(ValueError, match="excludes old independent"):
        finite.describe_interactions([{"kind": "fitting_bolt"}], [], [])


def test_current_recovery_needs_one_complete_identity():
    p, _, _ = small_potential()
    p.case["state_id"] = None
    with pytest.raises(ValueError, match="explicit state"):
        p.response(np.zeros(p.ndof), False, recover_actions=True)
