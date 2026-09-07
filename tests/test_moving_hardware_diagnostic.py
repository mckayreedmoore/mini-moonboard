"""Synthetic fail-only observations; no native replay, compiler or solver."""
import copy
import io
import json

import pytest
import test_moving_hardware_replay as replay_tests

from fea import moving_hardware_diagnostic as diagnostic

inputs = replay_tests.inputs


def test_streamed_complete_grid_reuses_blocks_and_rejects_time_damage(inputs):
    _, _, _, dat, _ = inputs
    times = [(i+1)*1e-7 for i in range(200)]
    streamed = list(diagnostic.state_blocks(io.StringIO(dat), times))
    assert len(streamed) == 200
    assert streamed == diagnostic.quiet.blocks(dat, times)
    with pytest.raises(ValueError, match="Incomplete DAT grid"):
        list(diagnostic.state_blocks(io.StringIO(dat), times+[201e-7]))
    with pytest.raises(ValueError, match="out-of-order"):
        list(diagnostic.state_blocks(io.StringIO(dat), times[1:]))
    first_header = next(iter(streamed[0]))
    with pytest.raises(ValueError, match="Duplicate"):
        list(diagnostic.state_blocks(io.StringIO(dat+f"\n{first_header} 2e-5\n1 0 0 0\n"), times))


def test_full_matrix_reconstruction_ignores_unqualified_contact_energy(inputs):
    data, _, cache, dat, _ = inputs
    context = json.loads(data)
    fields = next(diagnostic.state_blocks(io.StringIO(dat), [(i+1)*1e-7 for i in range(200)]))
    # A deliberately unusable CELS field must never enter these partial observables.
    fields["total contact spring energy for time"] = ["unqualified"]
    state = diagnostic.reconstruct(context, cache, fields, 1e-7)
    for name in context["bodies"]:
        expected = replay_tests.full_reference(context, cache["operators"]["native_four_point"][name], name)
        actual = state["bodies"][name]["native"]
        assert actual["linear_momentum"] == pytest.approx(expected[0])
        assert actual["angular_momentum"] == pytest.approx(expected[1])
        assert actual["kinetic_energy"] == pytest.approx(expected[2])
    assert "CELS" not in state
    for bad in (dict(fields, unknown=[]), {k: v for k, v in fields.items() if not k.startswith("velocities")}):
        with pytest.raises(ValueError, match="diagnostic block"):
            diagnostic.reconstruct(context, cache, bad, 1e-7)
    broken = copy.deepcopy(fields)
    key = next(k for k in broken if k.startswith("velocities"))
    broken[key].pop()
    with pytest.raises(ValueError, match="ownership"):
        diagnostic.reconstruct(context, cache, broken, 1e-7)


def test_signed_pair_impulses_reference_moments_and_no_pass_verdict():
    context = {"angular_reference_mm_local": [1., 0., 0.],
               "diagnostic_reference_scales": {"P_star_tonne_mm_s": 1., "H_star_tonne_mm2_s": 1., "E_star_N_mm": 1.},
               "contact_pairs": [{"slave": "WASHER_HEAD"}, {"slave": "WASHER_BORE"}]}
    def state(time, force, impulse):
        bodies = {}
        for name, sign in (("WASHER", 1), ("BOLT_NUT", -1)):
            p = [0., sign*impulse, 0.]
            bodies[name] = {"native": {"mass": 1., "linear_momentum": p, "angular_momentum": [0., 0., sign*2*impulse],
                                       "kinetic_energy": .5*impulse**2}, "EMAS": 1., "ELKE": .5*impulse**2}
        return {"time_s": time, "source": "SYNTHETIC", "bodies": bodies,
                "pairs": {"WASHER_HEAD": {"force_N": [0., force, 0.], "origin_moment_N_mm": [0., 0., 2*force]},
                          "WASHER_BORE": {"force_N": [0., 0., 0.], "origin_moment_N_mm": [0., 0., 0.]}}}
    states = [state(0., 0., 0.), state(1., 2., 1.), state(2., -2., 1.)]
    report = diagnostic.observe(states, context)
    assert not report["qualified"] and not report["contact_energy_qualified"]
    assert "ORIGINAL AUDIT REMAINS FAILED" in report["status"]
    assert report["additional_failures"] == []  # Absence of new failures is explicitly not a pass.
    last = report["states"][-1]
    assert last["pairs"]["WASHER_HEAD"]["J"] == (0., 1., 0.)
    assert last["pairs"]["WASHER_HEAD"]["K"] == (0., 0., 1.)
    assert last["assembly_linear_drift"] == last["assembly_angular_drift"] == (0., 0., 0.)
    for body in last["bodies"].values():
        assert body["linear_residual"] == body["angular_residual"] == (0., 0., 0.)
    states[-1]["bodies"]["BOLT_NUT"]["ELKE"] = 2.
    failed = diagnostic.observe(states, context)
    assert [f["quantity"] for f in failed["additional_failures"]] == ["BOLT_NUT native KE error"]


def test_wrong_selected_archive_rejected_before_reconstruction(tmp_path):
    (tmp_path / "preparation.tar.gz").write_bytes(b"not selected")
    with pytest.raises(ValueError, match="Archive hash differs"):
        diagnostic.diagnose(tmp_path)


@pytest.mark.parametrize("mutation,amplitude,quantities,limit", [
    ("body_P", .004, ["WASHER linear residual", "BOLT_NUT linear residual"], .002),
    ("body_H", .006, ["WASHER angular residual", "BOLT_NUT angular residual"], .003),
    ("assembly_P", .0006, ["assembly linear drift"], .0002),
    ("assembly_H", .0009, ["assembly angular drift"], .0003),
    ("mass", 2e-5, ["WASHER native mass error"], 5e-6),
])
def test_independent_failure_gates_use_reference_scales(mutation, amplitude, quantities, limit):
    context = {"angular_reference_mm_local": [1., 0., 0.],
               "diagnostic_reference_scales": {"P_star_tonne_mm_s": 2., "H_star_tonne_mm2_s": 3., "E_star_N_mm": 5.},
               "contact_pairs": [{"slave": "WASHER_HEAD"}, {"slave": "WASHER_BORE"}]}
    initial = {"time_s": 0., "source": "SYNTHETIC",
               "bodies": {name: {"native": {"mass": 2., "linear_momentum": [0., 0., 0.],
                                             "angular_momentum": [0., 0., 0.], "kinetic_energy": 0.},
                                  "EMAS": 2., "ELKE": 0.} for name in ("WASHER", "BOLT_NUT")},
               "pairs": {name: {"force_N": [0., 0., 0.], "origin_moment_N_mm": [0., 0., 0.]}
                         for name in ("WASHER_HEAD", "WASHER_BORE")}}
    final = copy.deepcopy(initial)
    final["time_s"] = 1.
    for name, sign in (("WASHER", 1), ("BOLT_NUT", -1)):
        if name == "BOLT_NUT" and not mutation.startswith("body_"):
            continue
        body = final["bodies"][name]
        if mutation.endswith("_P"):
            body["native"]["linear_momentum"][1] = sign*amplitude
            # Shift origin H by reference x P so this changes P without changing Hc.
            body["native"]["angular_momentum"][2] = sign*amplitude
        elif mutation.endswith("_H"):
            body["native"]["angular_momentum"][2] = sign*amplitude
        else:
            body["EMAS"] *= 1+amplitude
    report = diagnostic.observe([initial, final], context)
    assert [failure["quantity"] for failure in report["additional_failures"]] == quantities
    for failure in report["additional_failures"]:
        assert failure["time_s"] == 1.
        assert failure["observed"] == pytest.approx(amplitude)
        assert failure["limit"] == pytest.approx(limit)
    assert report["qualified"] is False and report["contact_energy_qualified"] is False
    assert report["status"] == "FAIL-ONLY OBSERVATIONS; ORIGINAL AUDIT REMAINS FAILED"
