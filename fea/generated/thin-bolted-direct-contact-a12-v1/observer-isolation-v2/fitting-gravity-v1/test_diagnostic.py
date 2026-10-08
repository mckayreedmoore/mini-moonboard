"""Source half-port dual and saved original RHS; no current ratio execution."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("diagnostic.py")
SPEC = importlib.util.spec_from_file_location("own_fitting_gravity_coupon", PATH)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def test_genuine_port_known_force_couple_and_no_constructor(monkeypatch):
    monkeypatch.setattr(helper.frame.ElasticAssembly, "__init__", lambda *a, **k: pytest.fail("K constructor called"))
    points = {"beam": [1., 2., 3.], "post": [-4., 8., 6.]}
    rows, vector, port = helper.gravity_ports(points, [7., -3., 9.], [0., 0., -12.])
    assert rows[0]["force_on_steel_xyz_n"] == rows[1]["force_on_steel_xyz_n"] == [0., 0., -6.]
    assert rows[0]["moment_on_steel_at_point_xyz_nmm"] == [30., 36., 0.]
    assert rows[1]["moment_on_steel_at_point_xyz_nmm"] == [66., 66., 0.]
    assert np.max(abs(vector - [0., 0., -6., .030, .036, 0., 0., 0., -6., .066, .066, 0.])) < 1e-16
    total = sum((np.r_[r["force_on_steel_xyz_n"], np.cross(r["point_xyz_mm"], r["force_on_steel_xyz_n"])
                      + r["moment_on_steel_at_point_xyz_nmm"]] for r in rows), np.zeros(6))
    assert np.array_equal(total, [0., 0., -12., 36., 84., 0.])
    for q in np.eye(12):
        assert abs(float(np.array([0., 0., -12.]) @ (port @ q)) - float(vector @ q)) < 1e-15


def test_known_far_side_cut_preserves_force_arm_and_gravity_couple():
    fitting = {"angle_id": "B104ZN_known_answer", "origin_xyz_mm": [0., 0., 0.],
               "u_xyz": [1., 0., 0.], "v_xyz": [0., 1., 0.], "w_xyz": [0., 0., 1.]}
    points = {"beam": [85.725, 0., 0.], "post": [0., 69.85, 0.]}
    centroid, force = np.array([7., -3., 9.]), np.array([0., 0., -12.])
    rows, _, _ = helper.gravity_ports(points, centroid, force)
    for row in rows:
        flange = row["flange"]
        loads = [{k: row[k] for k in ("point_xyz_mm", "force_on_steel_xyz_n", "moment_on_steel_at_point_xyz_nmm")}]
        cut = helper.steel.flange_reference(fitting, flange, loads)["sections"][0]
        along = np.array(fitting["u_xyz" if flange == "beam" else "v_xyz"])
        across = np.array(fitting["w_xyz"])
        basis = np.column_stack((along, across, np.cross(along, across)))
        point = along * cut["station_from_assumed_corner_mm"]
        assert np.max(abs(np.array(cut["force_local_n"]) - basis.T @ (force / 2))) < 1e-12
        assert np.max(abs(np.array(cut["moment_local_nmm"]) - basis.T @ np.cross(centroid - point, force / 2))) < 1e-12


@pytest.fixture(scope="module")
def current():
    packet = PATH.parent.parent
    receipt = json.loads((packet / "admission.json").read_bytes())
    field, components, pins = helper.authenticate(packet / "a12-rear.json", receipt, packet / "component-reductions.json",
        expected_field_sha256=helper.FIELD_SHA, expected_component_sha256=helper.COMPONENT_SHA,
        admission_sha256=helper.GATE_SHA)
    return packet, receipt, field, components, pins


def test_current36_rhs72loads_work_wrench_and_immutable_inputs(current):
    packet, receipt, field, components, pins = current
    before = [helper.pure.references.canonical_sha(v) for v in (receipt, field, components)]
    layout = json.loads(helper.steel.LAYOUT.read_bytes())
    rows, proof = helper.project_current_gravity(field, layout)
    assert len(rows) == len({(r["angle_id"], r["flange"]) for r in rows}) == 72
    assert proof["maximum_original_RHS_coefficient_error"] == 0.
    assert proof["maximum_current_q_virtual_work_error_nmm"] < 1e-10
    assert proof["maximum_global_wrench_error_n_nmm"] < 1e-9
    assert proof["only_saved_applied_vector_read"] and not proof["material_K_loaded"]
    assert before == [helper.pure.references.canonical_sha(v) for v in (receipt, field, components)]
    helper.pure.verify_pins(pins)
    assert hashlib.sha256((packet / "a12-rear.json").read_bytes()).hexdigest() == helper.FIELD_SHA
    assert hashlib.sha256((packet / "component-reductions.json").read_bytes()).hexdigest() == helper.COMPONENT_SHA


@pytest.mark.parametrize("option", ["field", "components", "gate"])
def test_wrong_input_hash_rejected_before_vector_or_cut_dispatch(monkeypatch, option):
    monkeypatch.setattr(helper, "project_current_gravity", lambda *a: pytest.fail("vector dispatch occurred"))
    options = {"expected_field_sha256": helper.FIELD_SHA,
               "expected_component_sha256": helper.COMPONENT_SHA, "admission_sha256": helper.GATE_SHA}
    key = {"field": "expected_field_sha256", "components": "expected_component_sha256", "gate": "admission_sha256"}[option]
    options[key] = "0" * 64
    with pytest.raises(ValueError, match="reviewed exact current"):
        helper.consume("not-read.json", {}, "not-read-components.json", **options)


def test_unmodeled_free_body_couple_rejected(current):
    field = copy.deepcopy(current[2])
    row = next(r for r in field["body_applied_loads"] if r["body"].startswith("B104ZN"))
    row["moment_at_point_xyz_nmm"] = [1., 0., 0.]
    with pytest.raises(ValueError, match="force-only fitting centroid"):
        helper.project_current_gravity(field, json.loads(helper.steel.LAYOUT.read_bytes()))


def test_cli_preserves_output_created_during_explicit_stub_dispatch(tmp_path, monkeypatch):
    # Output ownership coupon only; this stub supplies no field or body proof.
    receipt, output = tmp_path / "stub-receipt.json", tmp_path / "preserve.json"
    receipt.write_text("{}")
    preserved = b"independent owner created this during dispatch\n"

    def stub(*args, **options):
        output.write_bytes(preserved)
        return {"explicit_stub_not_admitted_current_result": True}

    monkeypatch.setattr(helper, "consume", stub)
    monkeypatch.setattr(helper.sys, "argv", [str(PATH), "--field", "not-read.json", "--components", "not-read-components.json",
                                           "--admission", str(receipt), "--out", str(output)])
    with pytest.raises(FileExistsError):
        helper.main()
    assert output.read_bytes() == preserved
