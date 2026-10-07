"""Independent common-shaft loads, paired datums and geometry export fixtures."""

import copy
import json

import numpy as np
import pytest

from scripts import thin_bolted_common_shaft_audit as audit


def test_actual_metal_gravity_moves_once_and_preserves_world_wrench():
    _, cache, _, _, takeoff, integrated, _ = audit.read_sources()
    state = json.loads((audit.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json").read_text())
    bodies, loads, delta = audit.expected_common_loads(state, cache, takeoff, integrated)
    assert len(bodies) == 132 and len(loads) == 689
    assert sum(row["id"].startswith("physical-bolt-metal/") for row in loads) == 350
    assert sum(row["id"].startswith("bolt-weight/") for row in loads) == 274
    assert np.linalg.norm(delta[:3]) < 1e-8 and np.linalg.norm(delta[3:]) < 1e-5
    assert not any(row["id"].startswith("self-weight/shaft/") for row in loads)
    audit.verify_load_table(loads, loads)
    changed = copy.deepcopy(loads)
    role = next(row for row in changed if row["id"].startswith("physical-bolt-metal/"))
    role["body"] = "base_floor_left"
    with pytest.raises(ValueError, match="load owner"):
        audit.verify_load_table(changed, loads)


def test_collinear_distinct_capture_datums_close_each_body_without_added_couple():
    loads = [{"body": "shaft", "point_xyz_mm": [0., 0., 0.], "force_xyz_n": [0., 0., -10.]},
             {"body": "host", "point_xyz_mm": [0., 0., 2.], "force_xyz_n": [0., 0., 10.]}]
    actions = [{"first": "shaft", "second": "host", "point_xyz_mm": [0., 0., 0.],
                "host_support_point_xyz_mm": [0., 0., 2.], "force_on_first_xyz_n": [0., 0., 10.]}]
    residuals, applied, global_value = audit.common_balances(["shaft", "host"], loads, actions, [], [0., 750., 1100.])
    assert np.max(abs(applied)) == 0.
    assert np.max(abs(global_value)) == 0.
    assert all(np.max(abs(value)) == 0. for value in residuals.values())


def test_noncollinear_distinct_ports_require_their_actual_compensating_couple():
    row = {"first": "shaft", "second": "host", "point_xyz_mm": [0., 0., 0.],
           "host_support_point_xyz_mm": [2., 0., 0.], "force_on_first_xyz_n": [0., 0., 10.]}
    with pytest.raises(ValueError, match="do not cancel globally"):
        audit.common_balances(["shaft", "host"], [], [row], [], [0., 0., 0.])
    row["moment_on_second_at_point_xyz_nmm"] = [0., -20., 0.]
    residuals, _, global_value = audit.common_balances(["shaft", "host"], [], [row], [], [0., 0., 0.])
    assert np.max(abs(sum(residuals.values()))) == 0.
    assert np.max(abs(global_value)) == 0.


@pytest.fixture(scope="module")
def geometry_fixture():
    from scripts.thin_bolted_common_shaft import shaft_inputs

    _, cache, unit, layout, _, _, _ = audit.read_sources()
    shafts = shaft_inputs(layout, unit, cache)
    bearing, captures = [], []
    identity = {"state_id": "fixture", "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold"}
    for shaft in shafts:
        p, g = np.asarray(shaft["point"]), shaft["basis"][0]
        for index, surface in enumerate(shaft["surfaces"]):
            low, high = surface["interval_mm"]
            for quad, abscissa in enumerate((-1. / np.sqrt(3.), 1. / np.sqrt(3.))):
                point = p + g * ((low + high) / 2 + (high - low) / 2 * abscissa)
                bearing.append({**identity, "id": shaft["axis_id"] + f"/bearing-{index}-{quad}",
                                "axis_id": shaft["axis_id"], "kind": "common_shaft_bearing",
                                "first": shaft["body"], "second": surface["host"],
                                "point_xyz_mm": point.tolist(), "force_on_first_xyz_n": [0., 0., 0.],
                                "force_on_second_xyz_n": [0., 0., 0.],
                                "surface_index": index, "quad_index": quad, "host": surface["host"],
                                "surface_material": surface["kind"], "flange": surface.get("flange"),
                                "surface_interval_mm": surface["interval_mm"],
                                "axis_station_mm": float((point - p) @ g), "weight_length_mm": (high - low) / 2.})
        for end in shaft["ends"]:
            captures.append({**identity, "id": shaft["axis_id"] + "/" + end["end"] + "-capture",
                             "axis_id": shaft["axis_id"], "kind": "shaft_end_capture", "first": shaft["body"],
                             "second": end["host"], "point_xyz_mm": (p + g * end["pressure_face_s_mm"]).tolist(),
                             "host_support_point_xyz_mm": (p + g * end["support_s_mm"]).tolist(),
                             "end": end["end"], "compression_n": 0., "force_on_first_xyz_n": [0., 0., 0.],
                             "force_on_second_xyz_n": [0., 0., 0.]})
    return {**identity, "common_shaft_bearing_actions": bearing, "shaft_end_capture_actions": captures}, shafts


def test_all_actual_82_wood_72_steel_paths_and_140_captures_are_enumerated(geometry_fixture):
    state, shafts = geometry_fixture
    result = audit.verify_common_actions(state, shafts)
    assert result["radial_quadrature_actions"] == 308
    assert result["unilateral_end_capture_actions"] == 140
    assert result["wood_bearing_surfaces"] == 82 and result["steel_bearing_surfaces"] == 72


@pytest.mark.parametrize("mutation", [
    lambda d: d["common_shaft_bearing_actions"].pop(),
    lambda d: d["shaft_end_capture_actions"].pop(),
    lambda d: d["common_shaft_bearing_actions"][0].update(second="wrong-host"),
    lambda d: d["common_shaft_bearing_actions"][0].update(point_xyz_mm=[0., 0., 0.]),
    lambda d: d["common_shaft_bearing_actions"][0].update(force_on_first_xyz_n=[0., 1., 1.]),
    lambda d: d["shaft_end_capture_actions"][0].update(compression_n=-1.),
    lambda d: d["shaft_end_capture_actions"][0].update(host_support_point_xyz_mm=[0., 0., 0.]),
    lambda d: d["shaft_end_capture_actions"][0].update(state_id="old62"),
    lambda d: d["shaft_end_capture_actions"][0].update(moment_at_point_model_xyz_nmm=[0., 1., 0.]),
    lambda d: d["shaft_end_capture_actions"][0].update(moment_on_first_at_point_xyz_nmm=[0., 1., 0.]),
    lambda d: d["common_shaft_bearing_actions"][0].update(surface_material="wrong"),
    lambda d: d["common_shaft_bearing_actions"][0].update(weight_length_mm=-1.),
    lambda d: d["common_shaft_bearing_actions"][0].pop("force_on_second_xyz_n"),
])
def test_missing_foreign_or_reinterpreted_shaft_actions_rejected(geometry_fixture, mutation):
    state, shafts = geometry_fixture
    state = copy.deepcopy(state)
    mutation(state)
    with pytest.raises(ValueError):
        audit.verify_common_actions(state, shafts)


def test_old_method_cannot_be_consumed_and_source_is_frozen():
    assert audit.support.digest(audit.COMMON_PRODUCER) == audit.COMMON_PRODUCER_SHA
    with pytest.raises(ValueError, match="continuous physical-shaft method identity"):
        audit.audit_common_shaft_state({})
