"""Current ownership guards and finite shaft gauge work at original datums."""

import copy
from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts import eoere_current_finite_preflight as preflight


def test_loaded_producer_drift_rejects_before_any_evidence_is_read(monkeypatch):
    original = preflight.current.sha
    monkeypatch.setattr(preflight.current, "sha", lambda path: "changed" if path == preflight.OWN else original(path))
    monkeypatch.setattr(preflight.intake_source, "intake", lambda: pytest.fail("intake reached after loaded producer drift"))
    with pytest.raises(ValueError, match="loaded finite preflight producer changed"):
        preflight.run()


def fixture_shaft(rotated=True):
    basis = Rotation.from_rotvec([.31, -.27, .19]).as_matrix() if rotated else np.eye(3)
    row = {"body": "shaft/own", "basis": basis.T.tolist(), "point": [101., -203., 307.],
           "stations": [-2., 17., 45., 80.], "diameter_mm": 9.525}
    nodes = np.array([[.2, -.1, .3, 0., 200., -150.],
                      [-.3, .2, -.1, 80., 210., -140.],
                      [-.4, .3, -.2, 100., 220., -130.],
                      [-.7, .5, -.3, 120., 230., -120.]])
    points = [{"id": f"own/{i}", "kind": "synthetic_port", "force": [33., -71., 53.],
               "couple": [0., 0., 0.], "point": (np.asarray(row["point"])+s*basis[:, 0]).tolist()}
              for i, s in enumerate([-2., 0., 17., 31., 45., 80.])]
    return row, nodes, points


@pytest.mark.parametrize("rotated", [False, True])
@pytest.mark.parametrize("angle", [.37, -.51, .79])
def test_multielement_energy_and_all_original_ports_have_zero_roll_work(rotated, angle):
    row, nodes, points = fixture_shaft(rotated)
    frozen = copy.deepcopy((row, nodes.tolist(), points))
    result = preflight.shaft_check(row, nodes, points, roll_rad=angle)
    assert result["declared_energy_nmm"] > 1.
    assert result["scaled_energy_roll_error"] < 1e-12
    assert abs(result["internal_roll_virtual_work_nmm_per_rad"]) < 1e-7
    assert result["sum_absolute_source_roll_work_nmm_per_rad"] < 1e-8
    assert [r["id"] for r in result["source_ports"]] == [r["id"] for r in points]
    assert (row, nodes.tolist(), points) == frozen


def test_roll_generator_matches_actual_right_roll_derivative():
    _, nodes, _ = fixture_shaft()
    h = 1e-6
    actual = (preflight.shaft.common_roll_local(nodes, h)-preflight.shaft.common_roll_local(nodes, -h))/(2*h)
    assert preflight.roll_generator(nodes) == pytest.approx(actual, rel=2e-9, abs=1e-7)
    assert np.count_nonzero(preflight.roll_generator(nodes)[:, :3]) == 0


@pytest.mark.parametrize("radial", [1e-4, .1])
def test_off_axis_load_is_rejected_without_projecting_its_point(radial):
    row, nodes, points = fixture_shaft()
    points[2]["point"] = (np.asarray(points[2]["point"])+radial*np.asarray(row["basis"])[1]).tolist()
    frozen = copy.deepcopy(points)
    with pytest.raises(ValueError, match="on-axis"):
        preflight.shaft_check(row, nodes, points)
    assert points == frozen


def test_roundoff_offset_is_retained_in_result():
    row, nodes, points = fixture_shaft()
    points[2]["point"] = (np.asarray(points[2]["point"])+2e-11*np.asarray(row["basis"])[1]).tolist()
    result = preflight.shaft_check(row, nodes, points)
    assert result["source_ports"][2]["source_radial_offset_mm"] > 1e-11


def test_declared_head_centroid_uses_original_endpoint_rigid_arm_without_projection():
    row, nodes, points = fixture_shaft()
    point = (np.asarray(row["point"])-5*np.asarray(row["basis"])[0]).tolist()
    points[0].update(kind="own_metal_gravity", point=point)
    row["metal_roles"] = [{"center_of_mass_xyz_mm": point}]
    result = preflight.shaft_check(row, nodes, points)
    assert result["source_ports"][0]["endpoint_rigid_arm_axial_extension_mm"] == pytest.approx(3.)
    assert result["source_ports"][0]["roll_point_change_mm"] < 1e-9
    assert points[0]["point"] == point


def test_unbound_gravity_point_cannot_enable_endpoint_extension():
    row, nodes, points = fixture_shaft()
    points[0]["kind"] = "own_metal_gravity"
    with pytest.raises(ValueError, match="declared metal centroid"):
        preflight.shaft_check(row, nodes, points)


@pytest.mark.parametrize("station,node", [(-5., 0), (83., 3)])
def test_both_endpoint_arms_use_exact_centroids_and_independent_position_jacobian(monkeypatch, station, node):
    row, nodes, _ = fixture_shaft()
    basis = np.asarray(row["basis"]).T
    point = np.asarray(row["point"])+station*basis[:, 0]
    center = np.asarray(row["point"])+row["stations"][node]*basis[:, 0]
    actual = preflight.shaft.mechanical.interpolated_point
    calls = []

    def record(received_point, centers, state, t, received_basis):
        assert np.array_equal(received_point, point)
        result = actual(received_point, centers, state, t, received_basis)
        calls.append((state.copy(), t, result))
        return result

    monkeypatch.setattr(preflight.shaft.mechanical, "interpolated_point", record)
    rolled = preflight.shaft.common_roll_local(nodes, .37)
    result = preflight.point_check(row, nodes, rolled, preflight.roll_generator(nodes), point,
                                   [33., -71., 53.], [0., 0., 0.], axial_extension=True)
    assert len(calls) == 2 and calls[0][1] == (0. if node == 0 else 1.)
    state, _, (position, jacobian) = calls[0]
    endpoint = 0 if node == 0 else 1

    def independent_pose(q12):
        q = q12.reshape(2, 6)[endpoint]
        rotation = Rotation.from_rotvec(basis @ q[3:]/1000.).as_matrix()
        return center+basis @ q[:3]+rotation @ (point-center)

    expected = independent_pose(state)
    step = 1e-4
    expected_j = np.column_stack([(independent_pose(state+h)-independent_pose(state-h))/(2*step)
                                  for h in np.eye(12)*step])
    assert position == pytest.approx(expected, abs=1e-11)
    assert jacobian == pytest.approx(expected_j, abs=2e-9)
    assert result["endpoint_rigid_arm_axial_extension_mm"] == pytest.approx(3.)


@pytest.mark.parametrize("couple", [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
def test_any_point_couple_needs_its_own_load_law(couple):
    row, nodes, points = fixture_shaft()
    points[0]["couple"] = couple
    with pytest.raises(ValueError, match="separately qualified"):
        preflight.shaft_check(row, nodes, points)


@pytest.mark.parametrize("problem", ["outside", "repeated_station", "duplicate_port", "nan_nodes", "improper_basis"])
def test_invalid_current_source_or_state_is_rejected(problem):
    row, nodes, points = fixture_shaft()
    if problem == "outside":
        points[0]["point"] = (np.asarray(row["point"])-3*np.asarray(row["basis"])[0]).tolist()
    elif problem == "repeated_station":
        row["stations"][2] = row["stations"][1]
    elif problem == "duplicate_port":
        points[1]["id"] = points[0]["id"]
    elif problem == "nan_nodes":
        nodes[0, 0] = np.nan
    elif problem == "improper_basis":
        row["basis"][0] = (-np.asarray(row["basis"])[0]).tolist()
    with pytest.raises(ValueError):
        preflight.shaft_check(row, nodes, points)


def partition_fixture():
    sources = [{"body": f"shaft/{i:03d}", "axis_id": str(i), "basis": np.eye(3).tolist(),
                "diameter_mm": 9.525, "point": [i, 0., 0.], "surfaces": [], "ends": []}
               for i in range(100)]
    chart = {"shafts": {s["body"]: {k: v for k, v in s.items() if k != "body"} for s in sources},
             "four_port_fittings": {f"fitting/{i}": {} for i in range(22)}}
    loads = [{"body": f"fitting/{i}", "id": f"gravity/{i}"} for i in range(22)]
    called = []

    def partition(received_chart, received_loads, order, *, expected_counts):
        assert received_chart is chart and received_loads is loads
        assert order == [s["body"] for s in sources]
        assert expected_counts == {"timber": 22, "fitting": 22, "shaft": 100, "panel": 6}
        called.append(order)
        return {"first_order_ndof": 9350, "prospective_quotient_ndof": 9350,
                "prospective_full_ndof": 9450,
                "load_ids_by_family": {family: list(range(count)) for family, count in preflight.LOAD_COUNTS.items()}}

    return SimpleNamespace(ownership_partition=partition), chart, loads, sources, called


def test_current_partition_reuses_frozen_operation_with_actual_source_order():
    method, chart, loads, sources, called = partition_fixture()
    sources.reverse()  # JSON alphabetical map order deliberately differs.
    result = preflight.current_partition(method, chart, loads, sources)
    assert result["prospective_full_ndof"] == 9450 and len(called) == 1


@pytest.mark.parametrize("field,value", [("first_order_ndof", 9272), ("prospective_full_ndof", 9372),
                                         ("prospective_quotient_ndof", 9450)])
def test_old_or_constrained_partition_cannot_transfer(field, value):
    method, chart, loads, sources, _ = partition_fixture()
    original = method.ownership_partition
    method.ownership_partition = lambda *a, **kw: {**original(*a, **kw), field: value}
    with pytest.raises(ValueError, match="older map"):
        preflight.current_partition(method, chart, loads, sources)


@pytest.mark.parametrize("problem", ["old500metal", "foreign_source", "duplicate_fitting_gravity"])
def test_partition_rejects_wrong_current_hardware_or_gravity(problem):
    method, chart, loads, sources, _ = partition_fixture()
    if problem == "old500metal":
        original = method.ownership_partition
        def changed(*a, **kw):
            result = original(*a, **kw)
            result["load_ids_by_family"]["shaft"] = list(range(500))
            return result
        method.ownership_partition = changed
    elif problem == "foreign_source":
        sources[0] = {**sources[0], "diameter_mm": 8.}
    else:
        loads[-1]["body"] = loads[0]["body"]
    with pytest.raises(ValueError):
        preflight.current_partition(method, chart, loads, sources)


def contact_fixture():
    descriptors = []
    for kind, count in preflight.CONTACT_COUNTS.items():
        for i in range(count):
            descriptors.append({"id": f"{kind}/{i}", "kind": kind})
    tangents = [r for r in descriptors if r["kind"] == "floor_tangent"]
    enabled = []
    for i, r in enumerate(tangents[:4]):
        r.update(first="lumber_leg_left" if i < 2 else "lumber_leg_right",
                 direction_xyz=[1., 0., 0.] if i % 2 == 0 else [0., 1., 0.])
        enabled.append({"id": r["id"], "first": r["first"], "kind": "floor_tangent", "interaction_enabled": True})
    bundle = {"partitions": {"groups": [{"descriptor": r} for r in descriptors], "contacts": [], "tangents": []}}
    return bundle, {"reference_interaction_descriptors": copy.deepcopy(descriptors), "floor_actions": enabled}


def test_current_contact_census_keeps_only_two_rear_centroid_xy_groups():
    bundle, field = contact_fixture()
    result = preflight.current_contacts(bundle, field)
    assert result["enabled_centroid_XY_groups"] == 2
    assert result["all_source_interaction_counts"]["timber_face_contact"] == 332
    assert result["all_source_interaction_counts"]["panel_contact"] == 922


@pytest.mark.parametrize("problem", ["old_panel_count", "missing_current_row", "duplicate_id", "all_floor_enabled", "wrong_host"])
def test_old_or_changed_contact_or_floor_sources_fail(problem):
    bundle, field = contact_fixture()
    if problem in {"old_panel_count", "missing_current_row"}:
        bundle["partitions"]["groups"].pop()
    elif problem == "duplicate_id":
        bundle["partitions"]["groups"][0]["descriptor"]["id"] = bundle["partitions"]["groups"][1]["descriptor"]["id"]
    elif problem == "all_floor_enabled":
        field["floor_actions"] += [dict(r, id=r["id"]+"/extra") for r in field["floor_actions"]]
    else:
        field["floor_actions"][0]["first"] = "base_post_outer_left"
    with pytest.raises(ValueError):
        preflight.current_contacts(bundle, field)


def point_inventory():
    field = {"source_inputs": {"shafts": [{"body": f"shaft/{i}"} for i in range(100)]},
             "body_applied_loads": [], "common_shaft_bearing_actions": [], "shaft_end_capture_actions": []}
    for i in range(100):
        for j in range(5+(i < 8)):
            field["body_applied_loads"].append({"body": f"shaft/{i}", "id": f"metal/{i}/{j}",
                "point_xyz_mm": [0., 0., 0.], "force_xyz_n": [0., 0., -1.]})
        for kind, count, key in [("common_shaft_bearing", 4+(i < 16), "common_shaft_bearing_actions"),
                                 ("shaft_end_capture", 2, "shaft_end_capture_actions")]:
            for j in range(count):
                field[key].append({"first": f"shaft/{i}", "axis_id": str(i), "id": f"{kind}/{i}/{j}",
                    "kind": kind, "point_xyz_mm": [0., 0., 0.], "force_on_first_xyz_n": [0., 0., -1.],
                    "moment_on_first_at_point_xyz_nmm": [0., 0., 0.]})
    return field


def test_all_1124_current_shaft_sources_include_eight_spacers_once():
    rows = preflight.owned_shaft_points(point_inventory())
    assert len(rows) == 100 and sum(map(len, rows.values())) == 1124
    assert Counter(p["kind"] for points in rows.values() for p in points)["own_metal_gravity"] == 508


@pytest.mark.parametrize("problem", ["missing_spacer", "wrong_bearing_axis", "wrong_capture_owner"])
def test_incomplete_or_foreign_current_shaft_sources_are_rejected(problem):
    field = point_inventory()
    if problem == "missing_spacer":
        field["body_applied_loads"].pop()
    elif problem == "wrong_bearing_axis":
        field["common_shaft_bearing_actions"][0]["axis_id"] = "99"
    else:
        field["shaft_end_capture_actions"][0]["first"] = "timber/foreign"
    with pytest.raises(ValueError):
        preflight.owned_shaft_points(field)


def test_six_case_orchestration_restores_every_own_noncontiguous_saved_pose(monkeypatch):
    """The wrapper must not replace distinct admitted poses with zero states."""
    cases, bundles, pins, expected = [], {}, {}, {}
    source_order = [f"shaft/{i:03d}" for i in reversed(range(100))]
    chart = {"shafts": {}}
    for i, body in enumerate(source_order):
        indices = (3*np.arange(11)+37*i+7).astype(int)
        # Maps deliberately have gaps and an omitted first spin. The frozen
        # partition's independent coverage contract is tested in its own suite;
        # this test isolates the current wrapper's restoration and routing.
        indices = np.insert(indices, 3, -1).reshape(2, 6)
        chart["shafts"][body] = {"index": indices.tolist()}
    for i, case_id in enumerate(preflight.SEQUENCE):
        q = np.arange(9350, dtype=float)*.001+(i+1)*.19
        ref = {"path": f"synthetic/operator-{i}.json", "sha256": f"manifest-sha-{i}"}
        pins[ref["path"]] = ref["sha256"]
        bundles[ref["path"]] = {"coordinate_map": chart,
            "original_operator_fingerprint_sha256": f"own-operator-{i}", "case": {"loads": [{"id": case_id}]}}
        field = {"operator_bundle": {"manifest": ref}, "body_applied_loads": [{"id": case_id}],
            "original_operator_fingerprint_sha256": f"own-operator-{i}",
            "response": {"q": q.tolist(), "q_canonical_sha256": preflight.canonical_sha(q.tolist())},
            "source_inputs": {"shafts": [{"body": body, "metal_roles": []} for body in source_order]}}
        binding = {"case_id": case_id, "state_id": f"own-state-{i}", "field": {"path": f"own-field-{i}"}}
        cases.append((binding, field, {}))
        for body in source_order:
            indices = np.asarray(chart["shafts"][body]["index"])
            own = np.zeros((2, 6))
            own[indices >= 0] = q[indices[indices >= 0]]
            expected[i, body] = own
    monkeypatch.setattr(preflight.intake_source, "intake", lambda: (cases, pins))
    monkeypatch.setattr(preflight.component, "load", lambda *_: SimpleNamespace(source_pins=dict))
    monkeypatch.setattr(preflight.shaft, "source_pins", dict)
    monkeypatch.setattr(preflight.current, "verify", lambda pins: pins)
    monkeypatch.setattr(preflight.current, "read", lambda ref: bundles[ref["path"]])
    monkeypatch.setattr(preflight.current, "manifest", lambda: {"release": {"candidate_accepted": False}})
    monkeypatch.setattr(preflight, "current_partition", lambda *_: {"prospective_full_ndof": 9450})
    monkeypatch.setattr(preflight, "current_contacts", lambda *_: {"enabled_centroid_XY_groups": 2})
    points = {body: [{"id": "own-port/"+body}] for body in source_order}
    monkeypatch.setattr(preflight, "owned_shaft_points", lambda _: points)
    calls = []

    def check(row, nodes, own_points):
        case_i = len(calls)//100
        assert row["body"] == source_order[len(calls) % 100]
        assert np.array_equal(nodes, expected[case_i, row["body"]])
        assert nodes[0, 3] == 0. and np.count_nonzero(nodes) == 11
        assert own_points is points[row["body"]]
        calls.append((case_i, row["body"]))
        return {"body": row["body"]}

    monkeypatch.setattr(preflight, "shaft_check", check)
    result = preflight.run()
    assert len(calls) == 600 and len(set(calls)) == 600
    assert [(r["case_id"], r["state_id"]) for r in result["cases"]] == [
        (case_id, f"own-state-{i}") for i, case_id in enumerate(preflight.SEQUENCE)]
    assert result["finite_frame_potential_or_equilibrium_or_native_solver_run"] is False
    assert result["source_points_projected_or_physical_torque_constraints_added"] == 0
