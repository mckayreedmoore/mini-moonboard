"""Accepted-history work and forcing-integral audits for transient pilots."""

import pytest

from fea.wood_joint_current_transient_history import _input_closure, audit_history_texts


def _freeze():
    return {
        "schema": "wood_joint_current_transient/v1",
        "amplitude_time_basis": "STEP TIME",
        "monitor_nodes": [10, 20, 30],
        "serialized_unit_load_nodes": {
            "10": {"force_xyz_n": [1.0, 0.0, 0.0]},
            "20": {"force_xyz_n": [-1.0, 0.0, 0.0]},
        },
        "rotation_nodes": [30],
        "sampled_travel_stop_mm": 3.0,
        "sampled_controller_rotation_stop_rad": 0.01,
        "sampled_loaded_node_displacement_stop_mm": 5.0,
    }


def _deck(second_force=-2.0):
    return """*AMPLITUDE,NAME=RAMP_N
0.0,0.0
0.001,0.1
0.002,0.4
0.003,0.9
0.004,1.6
0.005,2.5
*STEP,NLGEOM
*DYNAMIC,ALPHA=0
0.001,0.01,1e-6,0.0025
*CLOAD,AMPLITUDE=RAMP_N
10,1,2.0
20,1,-2.0
*NODE PRINT,NSET=PILOT_MONITOR,FREQUENCY=1
U
*END STEP
""".replace("20,1,-2.0", f"20,1,{second_force}")


def _sta():
    accepted = """SUMMARY OF JOB INFORMATION
  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME
     1          1     1     4  0.100000E-02  0.100000E-02  0.100000E-02
     1          2     1U    7  0.300000E-02  0.300000E-02  0.200000E-02
     1          2     2     5  0.250000E-02  0.250000E-02  0.150000E-02
     1          3     1     6  0.400000E-02  0.400000E-02  0.150000E-02
"""
    return accepted


def _block(time, ux10, ux20):
    return (
        f"displacements (vx,vy,vz) for set PILOT_MONITOR and time {time}\n\n"
        f"10 {ux10} 0.000000E+00 0.000000E+00\n"
        f"20 {ux20} 0.000000E+00 0.000000E+00\n"
        f"30 0.000000E+00 0.000000E+00 0.000000E+00\n\n"
    )


def _dat(*, sparse=False):
    text = _block("0.1000000E-02", "5.000000E-02", "-5.000000E-02")
    if not sparse:
        text += _block("0.2500000E-02", "2.000000E-01", "-2.000000E-01")
    text += _block("0.4000000E-02", "3.000000E-01", "-3.000000E-01")
    return text


def _log():
    return """increment 1 attempt 1
 actual total time=1.000000e-03
 initial energy (at start of step) = 0.0
 since start of the step:
 external work = 1.000000e-02
increment 2 attempt 1
 actual total time=3.000000e-03
no convergence
increment 2 attempt 2
 actual total time=2.500000e-03
 initial energy (at start of step) = 0.0
 since start of the step:
 external work = 2.350000e-01
increment 3 attempt 1
 actual total time=4.000000e-03
 initial energy (at start of step) = 0.0
 since start of the step:
 external work = 6.850000e-01
"""


def test_accepted_work_and_piecewise_impulse_ignore_rejected_attempt():
    result = audit_history_texts(
        freeze=_freeze(),
        deck_texts=[_deck()],
        sta_text=_sta(),
        dat_text=_dat(),
        log_text=_log(),
    )

    assert result["status"] == "complete"
    assert result["accepted_increment_count"] == 3
    assert result["rejected_attempt_count"] == 1
    assert result["load_scale_from_actual_cload"] == pytest.approx(2.0)
    assert result["work"]["cumulative_discrete_work_nmm"] == pytest.approx(0.685)
    assert result["work"]["native_comparison_status"] == "available"
    assert all(row["within_print_bound"] for row in result["work"]["accepted_rows"])

    impulse = result["force_impulse"]["intervals"]
    assert [
        row["piecewise_linear_pattern_impulse_ns"] for row in impulse
    ] == pytest.approx([0.0001, 0.001025, 0.003275])
    assert [
        row["whole_interval_endpoint_trapezoid_pattern_impulse_ns"] for row in impulse
    ] == pytest.approx([0.0001, 0.001125, 0.003375])
    assert impulse[1][
        "endpoint_trapezoid_minus_exact_pattern_impulse_ns"
    ] == pytest.approx(0.0001)
    assert result["force_impulse"]["interpretation"].startswith(
        "integral of the scalar force coefficient load_scale*A(t), in N*s"
    )


def test_missing_accepted_displacement_makes_work_unavailable_without_bridging():
    result = audit_history_texts(
        freeze=_freeze(),
        deck_texts=[_deck()],
        sta_text=_sta(),
        dat_text=_dat(sparse=True),
        log_text=_log(),
    )
    assert result["status"] == "work_unavailable"
    assert result["work"]["status"] == "unavailable_missing_accepted_displacements"
    assert result["work"]["cumulative_discrete_work_nmm"] is None
    assert result["work"]["accepted_rows"] == []
    assert result["monitor_coverage"][
        "missing_accepted_times_seconds"
    ] == pytest.approx([0.0025])
    # Load-factor integration can be evaluated from accepted status times,
    # but the missing U block must not be bridged into a work interval.
    assert result["force_impulse"]["status"] == "available"


def test_nonproportional_actual_cload_rejected():
    with pytest.raises(ValueError, match="not proportional"):
        audit_history_texts(
            freeze=_freeze(),
            deck_texts=[_deck(second_force=-1.9)],
            sta_text=_sta(),
            dat_text=_dat(),
            log_text=_log(),
        )


def test_amplitude_time_basis_must_match_step_time_coordinate():
    with pytest.raises(ValueError, match="STEP TIME"):
        audit_history_texts(
            freeze=_freeze(),
            deck_texts=[
                _deck().replace(
                    "*AMPLITUDE,NAME=RAMP_N", "*AMPLITUDE,NAME=RAMP_N,TIME=TOTAL TIME"
                )
            ],
            sta_text=_sta(),
            dat_text=_dat(),
            log_text=_log(),
        )


def test_impulse_uses_matched_dat_times_and_propagates_time_print_resolution():
    dat = _dat().replace("time 0.2500000E-02", "time 0.2500002E-02")
    result = audit_history_texts(
        freeze=_freeze(),
        deck_texts=[_deck()],
        sta_text=_sta(),
        dat_text=dat,
        log_text=_log(),
    )
    second_interval = result["force_impulse"]["intervals"][1]
    assert second_interval["end_time_seconds"] == pytest.approx(0.002500002)
    assert second_interval["end_time_source"] == "complete_dat_monitor_header"
    assert second_interval["end_time_print_bound_seconds"] == pytest.approx(5.0e-10)
    assert second_interval["piecewise_linear_impulse_time_print_bound_ns"] > 0.0
    assert result["work"]["accepted_rows"][1]["time_seconds"] == pytest.approx(
        0.002500002
    )


def test_nonfinite_monitor_values_rejected():
    bad_dat = _dat().replace("5.000000E-02", "NaN")
    with pytest.raises(ValueError):
        audit_history_texts(
            freeze=_freeze(),
            deck_texts=[_deck()],
            sta_text=_sta(),
            dat_text=bad_dat,
            log_text=_log(),
        )


def test_input_closure_preserves_filename_case_and_rejects_unpinned_include(tmp_path):
    (tmp_path / "pilot.inp").write_text("*INCLUDE,INPUT=mesh.inp\n")
    (tmp_path / "mesh.inp").write_text("*NODE\n10,0,0,0\n")
    assert len(_input_closure(tmp_path, "pilot.inp", {"pilot.inp", "mesh.inp"})) == 2
    with pytest.raises(ValueError, match="not pinned"):
        _input_closure(tmp_path, "pilot.inp", {"pilot.inp"})
