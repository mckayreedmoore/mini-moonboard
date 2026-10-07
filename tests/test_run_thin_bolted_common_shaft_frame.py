"""Avoid duplicate gravity and accidental reuse of removed frame bolt ports."""

import json
import sys
from types import SimpleNamespace

import pytest

from scripts import run_thin_bolted_common_shaft_frame as driver
from scripts.run_thin_bolted_common_shaft_frame import (
    bind_common_metadata,
    case_with_shaft_gravity,
)
from scripts.run_thin_bolted_finished_floor import bind_finished_state


def test_physical_gravity_replaces_the_case_once_for_load_and_recovery():
    system = SimpleNamespace(remap_bolt_gravity=lambda case: {
        **case, "loads": [{"body": "shaft/a"}], "shaft_metal_gravity_remap_residual_n_nmm": [0.] * 6})
    case = {"case_id": "a12-rear", "loads": [{"body": "timber"}]}
    assert case_with_shaft_gravity(case, system) is case
    assert case["loads"] == [{"body": "shaft/a"}]
    with pytest.raises(ValueError, match="already remapped"):
        case_with_shaft_gravity(case, system)


def test_common_actions_receive_the_final_floor_bound_identity():
    bearing = {"force_on_first_xyz_n": [1., 2., 0.]}
    report = {"state_id": "before", "case_id": "a12-rear", "accessory_placement": "original",
              "parameters": {"bolt_axial_lateral_stiffness_n_mm": 1000., "relative_bolt_radial_clearance_mm": 1.5875},
              "geometry_cache_sha256": "geo", "source_sha256": {},
              "counts": {"bolt_interfaces": 84}, "attachment_actions": [], "retained_bolt_actions": [],
              "limits": ["Fourteen shared shafts use two independent attachment spring ports."],
              "common_shaft_bearing_actions": [bearing],
              "common_shaft_section_cut_actions": [{"cuts": [{"local_N_V1_V2_T_M1_M2_n_nmm": [1.] * 6}]}]}
    system = SimpleNamespace(parameters={"end_capture_stiffness_n_mm": 1000.}, bearing_groups=[1],
                             end_captures=[1, 2], shafts={"shaft/a": {}})
    bound = bind_common_metadata(report, system, {}, ["command"])
    bound = bind_finished_state(bound, [], {}, "driver")
    assert bearing["state_id"] == bound["state_id"]
    assert bound["common_shaft_section_cut_actions"][0]["cuts"][0]["state_id"] == bound["state_id"]
    assert bound["counts"]["independent_lumped_frame_bolt_ports"] == 0
    assert "bolt_interfaces" not in bound["counts"]
    assert "relative_bolt_radial_clearance_mm" not in bound["parameters"]
    assert bound["inactive_legacy_bolt_port_parameters"]["relative_bolt_radial_clearance_mm"] == 1.5875
    assert not any(limit.startswith("Fourteen shared shafts") for limit in bound["limits"])


def test_old_independent_bolt_forces_cannot_be_labeled_as_continuous_shaft_result():
    with pytest.raises(ValueError, match="old independent"):
        bind_common_metadata({"attachment_actions": [{"force": 12.}]}, None, {}, [])


def test_unsolved_response_is_retained_without_manufactured_coefficients(tmp_path, monkeypatch):
    output = tmp_path / "failed.json"
    report = {"state_id": "before", "case_id": "a12-rear", "accessory_placement": "original",
              "parameters": {}, "geometry_cache_sha256": "geometry", "source_sha256": {},
              "limits": [], "usable_conditional_actions": False,
              "response": {"converged": False, "termination": "Newton iteration limit", "gradient_inf_n": 21.8}}

    def fail():
        raise driver.UnsolvedCommonState(report)

    monkeypatch.setattr(driver.shafts, "read_inputs", dict)
    monkeypatch.setattr(driver.shafts, "source_pins", dict)
    monkeypatch.setattr(driver.finished, "main", fail)
    monkeypatch.setattr(driver.finished, "read_finished_footprints", lambda: ({}, [], {}))
    argv = ["driver", "--cases", "a12-rear", "--out", str(output)]
    monkeypatch.setattr(sys, "argv", argv)
    driver.main()
    retained = json.loads(output.read_text())
    assert retained["response"] == report["response"]
    assert retained["failed_response_without_recovered_actions"] is True
    assert retained["usable_conditional_actions"] is False
    assert "q" not in retained["response"]
    assert "panel_generalized_coefficients" not in retained
    assert "common_shaft_bearing_actions" not in retained
    assert sys.argv == argv
