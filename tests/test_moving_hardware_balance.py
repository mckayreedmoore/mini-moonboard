"""Analytic supplied-state histories, not simulated contact or physical evidence."""
import copy
import math

import pytest

from fea import moving_hardware_balance as balance

SCALES = {"P_star_tonne_mm_s": 2., "H_star_tonne_mm2_s": 2., "E_star_N_mm": 2.}
REFERENCE = (1.001, .7356, 0.)
DIRECTION = (1/3, 2/3, -2/3)
LEVER = (3., -1., 2.)


def scaled(value, vector):
    return tuple(value*x for x in vector)


def history(times=(0., 1., 2.)):
    """Two unit masses exchange P; linear contact force gives exact trapezoids.

    Each washer pair force is -.5*t*d. Thus total J=-.5*t²*d,
    core P=.5*t²*d, washer P=(2-.5*t²)*d. Reversible stored energy closes
    the exact initial total of 2. Both bodies' H0 = lever cross P.
    """
    result = []
    for time in times:
        bodies = {}
        for name, speed in (("BOLT_NUT", .5*time*time), ("WASHER", 2-.5*time*time)):
            p = scaled(speed, DIRECTION)
            ke = .5 * math.fsum(x*x for x in p)
            bodies[name] = {"native": {"mass": 1., "linear_momentum": p,
                                      "angular_momentum": balance.cross(LEVER, p), "kinetic_energy": ke},
                            "EMAS": 1., "ELKE": ke, "ELSE": 0.}
        stored = max(0., 2 - sum(body["ELKE"] for body in bodies.values()))
        force = scaled(-.5*time, DIRECTION)
        result.append({"time_s": time, "bodies": bodies, "CELS_N_mm": stored,
                       "pairs": {name: {"force_N": force, "origin_moment_N_mm": balance.cross(LEVER, force)}
                                 for name in ("WASHER_HEAD", "WASHER_BORE")}})
    return result


def test_analytic_transfer_passes_with_first_interval_and_shifted_moments():
    supplied = history()
    original = copy.deepcopy(supplied)
    report = balance.assess(supplied, SCALES, REFERENCE)
    assert supplied == original
    assert report["status"] == "NUMERICAL BALANCE GATES PASSED"
    assert report["failures"] == report["insufficient_endpoint_transfer"] == []
    assert report["full_window_qualified"] is report["refinement_qualified"] is False
    first = report["states"][1]
    final = report["states"][-1]
    for name in final["pairs"]:
        assert first["pairs"][name]["J"] == pytest.approx(scaled(-.25, DIRECTION))
        assert final["pairs"][name]["J"] == pytest.approx(scaled(-1, DIRECTION))
        assert final["pairs"][name]["K"] == pytest.approx(balance.cross(balance.difference(LEVER, REFERENCE), scaled(-1, DIRECTION)))
        assert final["pairs"][name]["cumulative_force_norm_integral"] == pytest.approx(1.)
    assert final["bodies"]["BOLT_NUT"]["delta_P"] == pytest.approx(scaled(2, DIRECTION))
    assert final["bodies"]["WASHER"]["delta_P"] == pytest.approx(scaled(-2, DIRECTION))
    assert report["peak_core_ELKE"] == pytest.approx(2.)
    for state in report["states"]:
        assert state["native_energy_residual"] == pytest.approx(0, abs=1e-15)
        for body in state["bodies"].values():
            assert body["linear_residual"] == pytest.approx((0, 0, 0), abs=1e-15)
            assert body["angular_residual"] == pytest.approx((0, 0, 0), abs=2e-15)


def test_shift_changes_reported_angular_impulse_not_balance():
    centred = balance.assess(history(), SCALES, (0, 0, 0))
    shifted = balance.assess(history(), SCALES, REFERENCE)
    assert centred["status"] == shifted["status"] == "NUMERICAL BALANCE GATES PASSED"
    for name, pair in centred["states"][-1]["pairs"].items():
        expected = balance.difference(pair["K"], balance.cross(REFERENCE, pair["J"]))
        assert shifted["states"][-1]["pairs"][name]["K"] == pytest.approx(expected)


@pytest.mark.parametrize("body,field", [("BOLT_NUT", "linear_momentum"), ("WASHER", "linear_momentum"),
                                      ("BOLT_NUT", "angular_momentum"), ("WASHER", "angular_momentum")])
def test_independent_body_or_intermediate_error_cannot_hide_at_endpoint(body, field):
    supplied = history()
    supplied[1]["bodies"][body]["native"][field] = (10, 0, 0)
    report = balance.assess(supplied, SCALES, REFERENCE)
    assert report["status"] == "NUMERICAL BALANCE GATES FAILED"
    assert any(f["time_s"] == 1 and f["quantity"].startswith(body) and "balance" in f["quantity"] for f in report["failures"])
    assert all(f["time_s"] == 1 for f in report["failures"])


def test_assembly_drift_gate_is_stricter_than_individual_balance():
    supplied = history()
    for body in supplied[1]["bodies"].values():
        body["native"]["linear_momentum"] = balance.vector_sum((body["native"]["linear_momentum"], (.00015, 0, 0)))
    report = balance.assess(supplied, SCALES, (0, 0, 0))
    assert any(f["quantity"] == "assembly linear drift norm" for f in report["failures"])
    assert not any("linear balance" in f["quantity"] for f in report["failures"])


def test_signed_impulse_cancellation_is_not_replaced_with_force_norm():
    supplied = history((0., 1., 2., 3.))
    for index, state in enumerate(supplied):
        force = (0, 1, -1, 0)[index]
        for pair in state["pairs"].values():
            pair["force_N"] = (force, 0, 0)
            pair["origin_moment_N_mm"] = (0, 0, 0)
    report = balance.assess(supplied, SCALES, (0, 0, 0))
    pair = report["states"][-1]["pairs"]["WASHER_HEAD"]
    assert pair["J"] == (0, 0, 0)
    assert pair["cumulative_force_norm_integral"] == 2
    assert any("endpoint net impulse" in f["quantity"] for f in report["insufficient_endpoint_transfer"])
    assert report["status"] == "NUMERICAL BALANCE GATES FAILED"  # Failure takes priority over insufficient transfer.


def test_quiet_or_underexcited_history_is_inconclusive():
    initial = history()[0]
    supplied = [initial, {**copy.deepcopy(initial), "time_s": 1}]
    report = balance.assess(supplied, SCALES, REFERENCE)
    assert report["status"] == "NUMERICAL BALANCE INCONCLUSIVE"
    assert report["failures"] == [] and len(report["insufficient_endpoint_transfer"]) == 3


def test_balanced_transient_transfer_cannot_replace_endpoint_requirements():
    supplied = []
    for time, amplitude, transferred in ((0, 0, 0), (1, -.5, .5), (2, .5, .5), (3, 0, 0)):
        state = history()[0]
        state["time_s"] = time
        for name, speed in (("BOLT_NUT", transferred), ("WASHER", 2-transferred)):
            p = scaled(speed, DIRECTION)
            ke = .5 * math.fsum(v*v for v in p)
            state["bodies"][name]["native"].update(linear_momentum=p, angular_momentum=balance.cross(LEVER, p), kinetic_energy=ke)
            state["bodies"][name]["ELKE"] = ke
        state["CELS_N_mm"] = 2 - sum(b["ELKE"] for b in state["bodies"].values())
        for pair in state["pairs"].values():
            pair["force_N"] = scaled(amplitude, DIRECTION)
            pair["origin_moment_N_mm"] = balance.cross(LEVER, pair["force_N"])
        supplied.append(state)
    report = balance.assess(supplied, SCALES, REFERENCE)
    assert report["status"] == "NUMERICAL BALANCE INCONCLUSIVE" and report["failures"] == []
    assert len(report["insufficient_endpoint_transfer"]) == 3
    assert report["peak_core_ELKE"] == pytest.approx(.125)
    assert report["states"][-1]["pairs"]["WASHER_HEAD"]["cumulative_force_norm_integral"] == pytest.approx(1.)


@pytest.mark.parametrize("fault", ["mass", "ke", "stored_energy"])
def test_native_mass_ke_and_total_energy_gates(fault):
    supplied = history()
    if fault == "mass":
        supplied[1]["bodies"]["WASHER"]["EMAS"] = 1.001
    elif fault == "ke":
        supplied[1]["bodies"]["WASHER"]["ELKE"] += .001
    else:
        supplied[1]["bodies"]["WASHER"]["ELSE"] += .1
    report = balance.assess(supplied, SCALES, REFERENCE)
    expected = {"mass": "native mass relative error", "ke": "native kinetic-energy error", "stored_energy": "total native energy residual"}[fault]
    assert report["status"] == "NUMERICAL BALANCE GATES FAILED"
    assert any(expected in f["quantity"] for f in report["failures"])


def test_ke_floor_is_reported_and_not_claimed_as_relative_accuracy():
    initial = history()[0]
    supplied = [initial, {**copy.deepcopy(initial), "time_s": 1}]
    supplied[1]["bodies"]["BOLT_NUT"]["ELKE"] = 5e-14
    report = balance.assess(supplied, SCALES, REFERENCE)
    core = report["states"][1]["bodies"]["BOLT_NUT"]
    assert core["native_KE_floor_controls"] is True
    assert core["native_KE_comparison_scale"] == 2e-8
    assert report["failures"] == []
    supplied[1]["bodies"]["BOLT_NUT"]["ELKE"] = 2e-13
    report = balance.assess(supplied, SCALES, REFERENCE)
    assert any("native kinetic-energy error" in f["quantity"] for f in report["failures"])


@pytest.mark.parametrize("fault", ["initial_time", "initial_force", "initial_moment", "duplicate_time", "missing_body", "missing_pair", "nan", "negative_energy"])
def test_invalid_supplied_states_are_rejected(fault):
    supplied = history()
    if fault == "initial_time":
        supplied = supplied[1:]
    elif fault in ("initial_force", "initial_moment"):
        supplied[0]["pairs"]["WASHER_BORE"]["force_N" if fault == "initial_force" else "origin_moment_N_mm"] = (1, 0, 0)
    elif fault == "duplicate_time":
        supplied[1]["time_s"] = 0
    elif fault == "missing_body":
        del supplied[1]["bodies"]["BOLT_NUT"]
    elif fault == "missing_pair":
        del supplied[1]["pairs"]["WASHER_HEAD"]
    elif fault == "nan":
        supplied[1]["bodies"]["WASHER"]["native"]["linear_momentum"] = (0, float("nan"), 0)
    else:
        supplied[1]["CELS_N_mm"] = -1
    with pytest.raises(ValueError):
        balance.assess(supplied, SCALES, REFERENCE)


def test_physical_operator_values_are_not_substituted_into_native_gates():
    supplied = history()
    for state in supplied:
        for body in state["bodies"].values():
            body["physical_Gauss8"] = {"mass": 1e8, "linear_momentum": (1e8, 0, 0)}
    assert balance.assess(supplied, SCALES, REFERENCE)["status"] == "NUMERICAL BALANCE GATES PASSED"
