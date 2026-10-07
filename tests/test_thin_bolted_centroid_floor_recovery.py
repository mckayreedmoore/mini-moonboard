"""Mixed-contact centroid recovery seam; synthetic actions, no frame solve."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts import thin_bolted_common_shaft as common
from scripts import thin_bolted_common_shaft_audit as arithmetic
from scripts import thin_bolted_finished_support_audit as support


def test_mixed_contact_recovery_preserves_centroid_release_and_physical_wrenches():
    # Reuse the existing eight-foot polygon/audit fixture, without candidate input.
    path = Path(__file__).with_name("test_thin_bolted_finished_support_audit.py")
    spec = importlib.util.spec_from_file_location("centroid_support_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    demand, proof, cache = fixture.support_fixture()
    hosts = sorted(support.FLOOR_HOSTS)
    bearing, lifted = hosts[:2]
    demand["parameters"]["floor_no_slip_xy_penalty_n_mm"] = 100000.
    normal_rows = [copy.deepcopy(r) for r in demand["floor_actions"] if r["kind"] == "floor_normal"]
    for row in normal_rows:
        row["direction_xyz"] = [0., 0., 1.]
        if row["first"] == lifted:
            row.update(compression_n=0., force_on_first_xyz_n=[0., 0., 0.])
    tangents = [{"id": host + f"/no-slip-{i}", "first": host,
                 "point_xyz_mm": np.mean(proof["finished_floor_footprints"][host], axis=0).tolist(),
                 "direction_xyz": np.eye(3)[i].tolist(), "B": csr_matrix(np.eye(2)[i:i+1]),
                 "stiffness": 100000.} for host in hosts for i in (0, 1)]
    point = tangents[0]["point_xyz_mm"]
    face = {"id": "coupon/wood-face", "kind": "timber_face_contact", "first": lifted,
            "second": bearing, "point_xyz_mm": point, "direction_xyz": [1., 0., 0.]}
    capture = {"id": "coupon/head-capture", "axis_id": "coupon", "kind": "shaft_end_capture",
               "first": "shaft/coupon", "second": bearing, "point_xyz_mm": point,
               "host_support_point_xyz_mm": (np.asarray(point)+[0., 0., 2.]).tolist(),
               "direction_xyz": [0., 0., 1.], "end": "head"}
    # Distinct hand inputs detect capture filtering or new-contact index errors.
    contacts = [normal_rows[0], capture, face, *normal_rows[1:]]
    forces = [normal_rows[0]["compression_n"], 3., 7., *[r["compression_n"] for r in normal_rows[1:]]]
    q = np.array([.002, -.003])
    panel = {"kind": "panel_screw", "axis_id": "coupon-panel", "first": "coupon/panel",
             "second": bearing, "point_xyz_mm": point, "basis": np.eye(3)}
    expected_floor = copy.deepcopy(normal_rows)
    for tangent in tangents:
        if tangent["first"] != lifted:
            scalar = -tangent["stiffness"] * float((tangent["B"] @ q)[0])
            expected_floor.append({**tangent, "kind": "floor_tangent", "second": "floor",
                                   "force_on_first_xyz_n": (scalar*np.asarray(tangent["direction_xyz"])).tolist()})
    loads = []
    for row in expected_floor:
        loads.append({"body": row["first"], "point_xyz_mm": row["point_xyz_mm"],
                      "force_xyz_n": (-np.asarray(row["force_on_first_xyz_n"])).tolist()})
    for row, scalar in ((capture, 3.), (face, 7.)):
        force = scalar*np.asarray(row["direction_xyz"])
        for body, datum, value in ((row["first"], row["point_xyz_mm"], -force),
                (row["second"], row.get("host_support_point_xyz_mm", row["point_xyz_mm"]), force)):
            loads.append({"body": body, "point_xyz_mm": datum, "force_xyz_n": value.tolist()})
    for index, load in enumerate(loads):
        load["id"] = f"coupon-load-{index}"
    applied = sum((common.frame.wrench(r["force_xyz_n"], r["point_xyz_mm"]) for r in loads), np.zeros(6))
    case = {"case_id": demand["case_id"], "accessory_placement": demand["accessory_placement"],
            "loads": loads, "applied_force_xyz_n": applied[:3],
            "applied_moment_about_global_origin_xyz_nmm": applied[3:]}
    bodies = [*hosts, "shaft/coupon", "coupon/panel"]
    system = SimpleNamespace(assembly=SimpleNamespace(members={}, geo={"members": [],
        "bodies": [{"id": name} for name in bodies]}), shafts={}, recovery=lambda _: [],
        section_cut_actions=lambda *_: [])
    recovered = common.CommonShaftSystem.compatible_actions(system, case,
        {"q": q, "connector_local_force_n": [np.zeros(3)], "normal_contact_force_n": np.array(forces),
         "nonbearing_no_slip_removed": [lifted]}, [panel], contacts, tangents)
    assert recovered["equilibrium_verification"]["all_body_and_global_checks_pass"]
    assert recovered["contact_actions"][0]["id"] == face["id"]
    assert recovered["contact_actions"][0]["compression_n"] == 7.
    assert recovered["shaft_end_capture_actions"][0]["compression_n"] == 3.
    assert len(recovered["floor_actions"]) == 32+14
    assert not any(r["first"] == lifted and r["kind"] == "floor_tangent" for r in recovered["floor_actions"])
    for row in recovered["floor_actions"]:
        expected = next(r for r in expected_floor if r["id"] == row["id"])
        np.testing.assert_allclose(row["force_on_first_xyz_n"], expected["force_on_first_xyz_n"], atol=1e-12)
    internal = [*recovered["panel_screw_actions"], *recovered["contact_actions"], *recovered["shaft_end_capture_actions"]]
    balances, _, global_value = arithmetic.common_balances(bodies, loads, internal,
        recovered["floor_actions"], common.frame.REFERENCE)
    assert max(np.linalg.norm(v) for v in balances.values()) < 1e-9
    assert np.linalg.norm(global_value) < 1e-9
    identity = {key: demand[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    demand["state_id"] = "thin-v4-"+hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]
    demand["floor_actions"] = recovered["floor_actions"]
    demand["response"]["nonbearing_no_slip_removed"] = [lifted]
    for row in demand["floor_actions"]:
        row.update({key: demand[key] for key in ("case_id", "accessory_placement", "state_id")})
    assert support.verify_finished_support(demand, proof, cache)["tangent_port_count"] == 14
    changed = copy.deepcopy(demand)
    changed["response"]["nonbearing_no_slip_removed"] = []
    with pytest.raises(ValueError, match="removed no-slip hosts"):
        support.verify_finished_support(changed, proof, cache)
