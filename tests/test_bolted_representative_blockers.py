"""G1 representative records name actual missing checks, not missing wood data."""

import json
from pathlib import Path

import pytest


def test_representative_blockers_bind_archived_wrench_and_keep_gate_open():
    record = json.loads(
        Path("docs/bolted-candidate-representative-blockers.json").read_text()
    )
    old = json.loads(Path("docs/floor-runner-mvp-angle-demands.json").read_text())
    assert record["status"] == "G1_open"
    assert record["wood_reference_data_available"] is True
    assert record["same_case_is_not_archived_peak_or_envelope"] is True
    assert record["drilling_released"] is False
    assert record["retained_panel_axes_unchanged"] is True
    cases = old["cases"]
    expected = {
        "narrow_opposing": "clip_horizontal_bottom_left_2",
        "center_header": "clip_split_base_center_left",
        "outer_base": "clip_angle_base_left",
    }
    assert set(record["joints"]) == set(expected)
    for family, station in expected.items():
        joint = record["joints"][family]
        assert joint["station"] == station
        case = joint["archived_same_case_wrench"]["case"]
        actual = cases[case]["angles"][station]["flanges"]["beam"]
        assert joint["archived_same_case_wrench"]["force_xyz_n"] == pytest.approx(
            actual["force_xyz_n"]
        )
        assert joint["archived_same_case_wrench"]["moment_xyz_nmm"] == pytest.approx(
            actual["moment_xyz_nmm"]
        )
        expected_status = (
            "A66_narrow_face_rejected_AB205_shifted_edge_screen_only"
            if family == "narrow_opposing"
            else "missing_joint_detail"
        )
        assert joint["status"] == expected_status
        assert joint["missing_inputs"]
        assert joint["new_candidate_demand_available"] is False
        assert joint["capacity_claim"] is False
    assert record["joints"]["center_header"]["archived_center_shift_mm"] == 10.1
