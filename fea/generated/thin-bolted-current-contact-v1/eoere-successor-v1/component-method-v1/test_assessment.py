"""Own-source projection fixtures; no synthetic candidate admission is issued."""
import copy
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("eoere_assessment_test", Path(__file__).with_name("assessment.py"))
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def capture_toy():
    end = {"end": "head", "host": "wood", "pressure_face_s_mm": -2., "support_s_mm": 0.,
           "direction_on_shaft_xyz": [-1., 0., 0.]}
    shaft = {"axis_id": "toy", "body": "shaft/toy", "point": [1., 2., 3.], "basis": np.eye(3).tolist(),
             "ends": [end], "source_axis": {"hardware_scenario": {"washer_od_mm": 14., "washer_id_mm": 10.}}}
    row = {"id": "toy/head", "axis_id": "toy", "first": "shaft/toy", "second": "wood", "end": end,
           "compression_n": 6., "point_xyz_mm": [-1., 2., 3.], "host_support_point_xyz_mm": [1., 2., 3.],
           "force_on_first_xyz_n": [-6., 0., 0.]}
    return row, shaft


def test_own_annulus_hand_average_and_unknown_couple():
    row, shaft = capture_toy()
    before = copy.deepcopy((row, shaft))
    result = method.capture_diagnostics(row, shaft)
    assert result["nominal_full_annulus_area_mm2"] == 24*math.pi
    assert result["nominal_full_annulus_average_pressure_mpa"] == 1/(4*math.pi)
    assert result["actual_pressure_couple_nmm"] is None
    assert (row, shaft) == before


@pytest.mark.parametrize("key", ["second", "host_support_point_xyz_mm", "force_on_first_xyz_n"])
def test_foreign_capture_source_or_signed_force_rejected(key):
    row, shaft = capture_toy()
    row[key] = "other" if key == "second" else [0., 0., 0.]
    with pytest.raises(ValueError):
        method.capture_diagnostics(row, shaft)


def test_own_port_force_couple_transport_hand_answer():
    fitting = {"body": "angle", "port_actions": [{"port_id": "arm-x/far-plus", "point_xyz_mm": [1., 0., 0.],
        "external_force_required_at_port_xyz_n": [0., 2., -4.],
        "external_couple_required_at_port_xyz_nmm": [0., 8., 3.]}]}
    field = {"common_shaft_steel_port_actions": [{"host": "angle", "flange": "arm-x/far-plus",
        "axis_id": "toy", "surface_index": 1, "point_xyz_mm": [1., 0., 0.],
        "force_on_steel_xyz_n": [0., 2., 0.], "moment_on_steel_at_point_xyz_nmm": [0., 0., 3.]}],
        "contact_actions": [{"id": "pressure", "kind": "flange_contact", "first": "angle",
            "flange": "arm-x/far-plus", "point_xyz_mm": [3., 0., 0.], "force_on_first_xyz_n": [0., 0., -4.]}]}
    result = method.own_port_joins(field, fitting)[0]
    assert result["own_external_force_xyz_n"] == [0., 2., -4.]
    assert result["own_external_couple_about_port_xyz_nmm"] == [0., 8., 3.]
    assert result["external_minus_elastic_required_couple_xyz_nmm"] == [0., 0., 0.]


def test_exact_new_surface_projection_and_reused_own_three_action_wrench():
    source = {"shafts": [{"axis_id": "toy", "surfaces": [{"kind": "steel", "host": "angle",
        "flange": "arm-x/far-plus", "receiver": "wood"}]}], "fitting_port_bindings": [{
        "axis_id": "toy", "angle_id": "angle", "model_port_id": "arm-x/far-plus", "entry_xyz_mm": [0., 0., 0.]}]}
    common = {"axis_id": "toy", "second": "angle", "flange": "arm-x/far-plus",
        "surface_material": "steel", "moment_on_second_at_point_xyz_nmm": [0., 0., 0.]}
    bearings = [{**common, "id": str(i), "point_xyz_mm": [float(i), 0., 0.],
                 "force_on_second_xyz_n": [0., 2., 0.]} for i in (1, 2)]
    captures = [{**common, "id": "head", "end": {"flange": "arm-x/far-plus"},
        "host_support_point_xyz_mm": [0., 0., 0.], "force_on_second_xyz_n": [3., 0., 0.]}]
    result = method.shaft_ports.aggregate_steel_ports(method.steel_surface_projection(source), bearings, captures)[0]
    assert result["force_on_steel_xyz_n"] == [3., 4., 0.]
    assert result["moment_on_steel_at_point_xyz_nmm"] == [0., 0., 6.]
    with pytest.raises(ValueError):
        method.shaft_ports.aggregate_steel_ports(method.steel_surface_projection(source), bearings[:1], captures)


def test_optional_enclosed_identity_does_not_allow_present_foreign_or_none():
    field = {"state_id": "new", "case_id": "a12", "accessory_placement": "own"}
    method.identity_check(field, {}, required=False)
    for value in (None, "old"):
        with pytest.raises(ValueError):
            method.identity_check(field, {"state_id": value}, required=False)
    with pytest.raises(ValueError):
        method.identity_check(field, {})


def test_missing_panel_map_is_explicit_disposition():
    result, pins = method.panel_reductions({"source_inputs": {"panel_ids": ["toy"]}})
    assert result["status"] == "UNAVAILABLE" and not pins and result["panel_diagnostics"] == []


def test_simultaneous_generic_screw_arithmetic_keeps_product_limit():
    method.verify(method.PINS)
    result = method.panel.screw_references({"withdrawal_n": 1000., "lateral_n": 5.,
                                           "local_force_n": [1000., 3., -4.]}, method.panel.panel_method.CAT)
    thread = 1000/(2850*.5**2*.190*method.panel.panel_method.N_PER_LBF/25.4)
    assert result["generic_withdrawal_required_effective_thread_mm_CD1"] == thread
    assert result["same_axis_simultaneous_lateral_n"] == 5.
    assert result["Hillman_product_capacity_or_stiffness_established"] is False


def test_old_v1_schema_cannot_enter_fresh_reduction():
    with pytest.raises(ValueError, match="fresh converged"):
        method.reduce_field({"schema": "eoere_first_order_common_shaft_four_port_candidate/v1"}, None, None, {})


def test_panel_exact_key_projection_reuses_genuine_q_slice_api():
    basis = method.panel.panel_method.SheetBasis(100., 120., 1)
    q = np.arange(3*basis.size, dtype=float).tolist()
    field = {"response": {"q": [99.]+q}, "panel_generalized_coefficients": {"toy": {
        "global_dof_start": 1, "indices": list(range(1, 1+len(q))), "coefficients": q,
        "width_mm": 100., "height_mm": 120., "basis_order_per_direction": basis.order,
        "thickness_mm": method.panel.panel_method.CAT, "knots_normalized": basis.knots.tolist(),
        "coefficient_order": method.panel.COEFFICIENT_ORDER}}}
    before = copy.deepcopy(field)
    projection = method.panel_slice_projection(field)
    _, observed = method.panel.coefficient_slice(projection, "toy")
    assert observed.tolist() == q and field == before
    field["panel_generalized_coefficients"]["toy"]["indices"][0] = 0
    with pytest.raises(ValueError):
        method.panel_slice_projection(field)


def test_rejected_fresh_gate_precedes_any_reduction(tmp_path, monkeypatch):
    path = tmp_path/"no-field.json"
    path.write_text("{}")
    receipt = tmp_path/"no-receipt.json"
    receipt.write_text(json.dumps({"schema": method.ADMISSION_SCHEMA, method.SUCCESS: True}))
    calls = []

    def reject(*args, **kwargs):
        calls.append("gate")
        raise ValueError("synthetic rejection; no numerical admission")

    monkeypatch.setattr(method, "verify", lambda pins: None)
    monkeypatch.setattr(method, "load", lambda *args: SimpleNamespace(require_admitted_payload=reject))
    monkeypatch.setattr(method, "reduce_field", lambda *args, **kwargs: calls.append("reduction"))
    with pytest.raises(ValueError, match="synthetic rejection"):
        method.consume(path, receipt, expected_field_sha256=method.sha(path), admission_sha256="toy", steel_sha256="toy")
    assert calls == ["gate"]
