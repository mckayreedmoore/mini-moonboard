"""Known floor polygon and exported-port mutations, without CAD or a solve."""

import copy
import hashlib
import json

import pytest

from scripts import thin_bolted_finished_support_audit as audit


def support_fixture():
    reference, parts, proof, actions = {}, [], [], []
    for index, host in enumerate(sorted(audit.FLOOR_HOSTS)):
        x = float(index * 10)
        points = [[x, 0., 0.], [x, 3., 0.], [x + 2., 0., 0.], [x + 2., 3., 0.]]
        reference[host] = points
        source = {"id": host, "kind": "timber", "path": host + ".brep", "sha256": host + "-pin"}
        parts.append(source)
        proof.append({"member": host, "polygons_xyz_mm": [[points[i] for i in (0, 2, 3, 1)]],
                      "bearing_area_mm2": 6., "source_brep_path": source["path"], "source_brep_sha256": source["sha256"]})
        for corner, point in enumerate(points):
            compression = 1. if corner == 0 else 0.
            actions.append({"id": host + f"/floor-{corner}", "kind": "floor_normal", "first": host,
                            "second": "floor", "point_xyz_mm": point, "compression_n": compression,
                            "force_on_first_xyz_n": [0., 0., compression], "moment_at_point_model_xyz_nmm": [0., 0., 0.]})
        for component in (0, 1):
            force = [0., 0., 0.]
            force[component] = -2.
            actions.append({"id": host + f"/no-slip-{component}", "kind": "floor_tangent", "first": host,
                            "second": "floor", "point_xyz_mm": [x + 1., 1.5, 0.], "force_on_first_xyz_n": force,
                            "penalty_stiffness_n_mm": 100., "tangent_displacement_mm": .02})
    contact = {"candidate": "fixture", "layout_report_sha256": "layout", "finished_floor_footprints": reference,
               "source_sha256": {row["path"]: row["sha256"] for row in parts}}
    demand = {"candidate": "fixture", "case_id": "a12-rear", "accessory_placement": "retained-original-top-hold",
              "geometry_cache_sha256": audit.CACHE_SHA, "layout_report_sha256": "layout", "parameters": {
                  "floor_support_basis": audit.FLOOR_BASIS, "floor_contact_geometry_sha256": audit.CONTACT_SHA,
                  "floor_no_slip_xy_penalty_n_mm": 100.},
              "finished_floor_footprints": proof, "floor_actions": actions, "usable_conditional_actions": True,
              "source_sha256": {}, "response": {"nonbearing_no_slip_removed": [], "converged": True,
                                                  "gradient_inf_n": 1e-7, "generalized_residual_tolerance_n": 1e-5}}
    identity = {key: demand[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    demand["state_id"] = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]
    for row in actions:
        row.update({key: demand[key] for key in ("case_id", "accessory_placement", "state_id")})
    return demand, contact, {"parts": parts}


def test_known_rectangle_includes_boundary_and_rejects_absent_timber():
    polygon = [[0., 0., 0.], [2., 0., 0.], [2., 3., 0.], [0., 3., 0.]]
    for point in ([1., 1., 0.], [0., 2., 0.], [2., 3., 0.]):
        assert audit.inside_rectangle(point, polygon)
    assert not audit.inside_rectangle([2.01, 1., 0.], polygon)
    assert not audit.inside_rectangle([1., 1., .01], polygon)
    assert audit.inside_rectangle([1., 1., 0.], list(reversed(polygon)))


@pytest.mark.parametrize("points", [
    [[0., 0., 0.], [2., 3., 0.], [2., 0., 0.], [0., 3., 0.]],
    [[0., 0., 0.], [2., 0., 0.], [2., 3., 0.], [0., 3., .01]],
    [[0., 0., 0.], [2., 0., 0.], [2., 3., 0.], [0., 3., float("nan")]],
    [[0., 0., 0.], [2., 0., 0.], [1., 3., 0.], [0., 3., 0.]],
])
def test_crossed_nonhorizontal_nonfinite_or_nonrectangular_polygon_rejected(points):
    with pytest.raises(ValueError):
        audit.rectangle_polygon(points)


def test_all_eight_finished_faces_and_32_normal_ports_are_authenticated():
    demand, contact, cache = support_fixture()
    result = audit.verify_finished_support(demand, contact, cache)
    assert result["finished_support_geometry_checks_pass"] is True
    assert result["normal_port_count"] == 32
    assert result["tangent_port_count"] == 16


@pytest.mark.parametrize("mutation", [
    lambda d: d["parameters"].pop("floor_support_basis"),
    lambda d: d["parameters"].update(floor_contact_geometry_sha256="raw"),
    lambda d: d["finished_floor_footprints"].pop(),
    lambda d: d["finished_floor_footprints"][0].update(source_brep_sha256="other"),
    lambda d: d["finished_floor_footprints"][0].update(bearing_area_mm2=7.),
    lambda d: d["floor_actions"].pop(0),
    lambda d: d["floor_actions"][0].update(point_xyz_mm=[-38.1, 0., 0.]),
    lambda d: d["floor_actions"][0].update(first="lumber_leg_left"),
    lambda d: d["floor_actions"][0].update(compression_n=-1., force_on_first_xyz_n=[0., 0., -1.]),
    lambda d: d["floor_actions"][0].update(moment_at_point_model_xyz_nmm=[0., 0., 1.]),
    lambda d: d["floor_actions"][4].update(point_xyz_mm=[.5, 1.5, 0.]),
    lambda d: d["floor_actions"][4].update(penalty_stiffness_n_mm=50.),
    lambda d: d["floor_actions"][0].update(state_id="raw"),
])
def test_support_export_mutations_cannot_pass(mutation):
    demand, contact, cache = support_fixture()
    mutation(demand)
    with pytest.raises(ValueError):
        audit.verify_finished_support(demand, contact, cache)


def test_polygon_cannot_expand_to_include_removed_leg_material():
    demand, contact, cache = support_fixture()
    polygon = demand["finished_floor_footprints"][0]["polygons_xyz_mm"][0]
    polygon[0] = [-38.1, 0., 0.]
    polygon[3] = [-38.1, 3., 0.]
    demand["finished_floor_footprints"][0]["bearing_area_mm2"] = 40.1 * 3.
    with pytest.raises(ValueError, match="differs from exact finished timber face"):
        audit.verify_finished_support(demand, contact, cache)


def test_no_tangent_credit_on_a_nonbearing_host():
    demand, contact, cache = support_fixture()
    demand["floor_actions"][0].update(compression_n=0., force_on_first_xyz_n=[0., 0., 0.])
    with pytest.raises(ValueError, match="positive host normal bearing"):
        audit.verify_finished_support(demand, contact, cache)
    host = demand["floor_actions"][0]["first"]
    demand["floor_actions"] = [row for row in demand["floor_actions"]
                               if not (row["first"] == host and row["kind"] == "floor_tangent")]
    demand["response"]["nonbearing_no_slip_removed"] = [host]
    assert audit.verify_finished_support(demand, contact, cache)["tangent_port_count"] == 14


def test_combined_gate_reuses_frozen_arithmetic_and_preserves_its_failure(monkeypatch):
    demand, contact, cache = support_fixture()
    monkeypatch.setattr(audit, "read_authenticated_sources", lambda: (contact, cache, {}))
    called = []

    def closure(state):
        called.append(state)
        return {"independent_equilibrium_and_contact_checks_pass": False}

    monkeypatch.setattr(audit.arithmetic, "audit_state", closure)
    result = audit.audit_finished_state(demand)
    assert called == [demand]
    assert result["independent_finished_support_and_equilibrium_checks_pass"] is False


def test_source_mutation_is_rejected_before_support_or_arithmetic(monkeypatch, tmp_path):
    contact_path = tmp_path / "changed-contact.json"
    contact_path.write_text("{}")
    monkeypatch.setattr(audit, "CONTACT_PATH", contact_path)
    monkeypatch.setattr(audit, "ROOT", tmp_path)
    monkeypatch.setattr(audit, "CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(audit.arithmetic, "__file__", str(tmp_path / "frozen-audit.py"))
    with pytest.raises(ValueError, match="preserve frozen support/audit input"):
        audit.read_authenticated_sources()


def test_current_frozen_source_packet_authenticates_without_CAD():
    contact, cache, pins = audit.read_authenticated_sources()
    assert set(contact["finished_floor_footprints"]) == audit.FLOOR_HOSTS
    assert cache["candidate"] == contact["candidate"]
    assert pins[str(audit.CONTACT_PATH.relative_to(audit.ROOT))] == audit.CONTACT_SHA
    assert len(pins) >= 127


def test_proofs_are_checked_without_mutating_the_input():
    demand, contact, cache = support_fixture()
    before = copy.deepcopy(demand)
    audit.verify_finished_support(demand, contact, cache)
    assert demand == before
