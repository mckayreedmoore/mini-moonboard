"""Synthetic full-field replay, not native dynamic or mass-operator evidence."""
import copy
import json
import math

import pytest
from test_moving_hardware_control import fixture

from fea import moving_hardware_control as control
from fea import moving_hardware_replay as replay


@pytest.fixture(scope="module")
def inputs():
    context = control.build_context(*fixture(catalog=True), direct_quiescent=True)
    context["pose_variant"] = "separated-washer-stationary-preflight"
    context["cases"] = {"moving": {**control.DIRECT_MOVING_SETTINGS,
        "initial_velocity_mm_s": {"BOLT_NUT": [0., 0., 0.], "WASHER": [-100., 100., 0.]}}}
    deck = control.deck(context, "moving").encode()
    context["deck_sha256"] = {"moving": control.digest(deck)}
    data = json.dumps(context).encode()
    operators = {}
    for operator in ("native_four_point", "physical_Gauss8"):
        operators[operator] = {}
        for name, body in context["bodies"].items():
            blocks = {}
            for element in body["elements"]:
                ids = [context["elements"][element][i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 9, 8)]
                weights = [.1]*10 if operator == "native_four_point" else [(i+1)/55 for i in range(10)]
                matrix = [[weights[i] if i == j else 0. for j in range(10)] for i in range(10)]
                coupling = -.025 if operator == "native_four_point" else .005
                matrix[0][1] = matrix[1][0] = coupling
                matrix[0][0] -= coupling
                matrix[1][1] -= coupling
                blocks[str(element)] = (ids, matrix)
            operators[operator][name] = blocks
    cache = {"context_sha256": control.digest(data), "density_tonne_mm3": context["material"]["density_tonne_mm3"],
             "operators": operators}
    tables = {}
    for name, body in context["bodies"].items():
        for label in ("displacements", "velocities"):
            factors = (.03, .01, -.02) if label == "displacements" else (.01, -.02, .03)
            tables[f"{label} (vx,vy,vz) for set {name} and time"] = [
                str(n) + " " + " ".join(format(n*f, ".17g") for f in factors) for n in body["nodes"]]
        for label, value in (("mass", 2), ("kinetic energy", 0), ("internal energy", 0)):
            tables[f"total {label} for set {name} and time"] = [str(value)]
    for label in ("relative contact displacement (slave element+face,normal,tang1,tang2)",
                  "contact stress (slave element+face,press,tang1,tang2)",
                  "contact spring energy (slave element+face,energy)"):
        tables[label + " for all contact elements and time"] = []
    for label in ("total number of contact elements", "total contact spring energy"):
        tables[label + " for time"] = ["0"]
    for pair in context["contact_pairs"]:
        tables[f"statistics for slave set {pair['slave']}, master set {pair['master']} and time"] = [
            "total surface force (fx,fy,fz) and moment about the origin (mx,my,mz)", "0 0 0 0 0 0",
            "center of gravity and mean normal", "NaN NaN NaN NaN NaN NaN",
            "moment about the center of gravity(mx,my,mz)", "NaN NaN NaN",
            "area,  normal force (+ = tension) and shear force (size)", "0 NaN NaN"]
    dat = "\n".join(name + f" {i*1e-7:.17g}\n" + "\n".join(rows)
                    for i in range(1, 201) for name, rows in tables.items())
    sta = "SUMMARY OF JOB INFORMATION\n  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME\n"
    sta += "\n".join(f"1 {i} 1 2 {i*1e-7:.17g} {i*1e-7:.17g} 1e-7" for i in range(1, 201))
    return data, deck, cache, dat, sta


def full_reference(context, blocks, body, *, initial=False):
    points = {int(n): p for n, p in context["nodes"].items()}
    p, h, ke = [0.]*3, [0.]*3, 0.
    for ids, matrix in blocks.values():
        for i, n in enumerate(ids):
            initial_v = [-100., 100., 0.] if body == "WASHER" else [0., 0., 0.]
            v = initial_v if initial else [n*.01, -n*.02, n*.03]
            x = [points[n][a] + (0 if initial else n*(.03, .01, -.02)[a]) for a in range(3)]
            for j, other in enumerate(ids):
                other_v = initial_v if initial else [other*.01, -other*.02, other*.03]
                m = matrix[i][j]
                for a in range(3):
                    p[a] += m*other_v[a]
                    h[a] += m*(x[(a+1)%3]*other_v[(a+2)%3] - x[(a+2)%3]*other_v[(a+1)%3])
                ke += .5*m*sum(v[a]*other_v[a] for a in range(3))
    return p, h, ke


def test_full_fields_and_initial_state_use_distinct_operators(inputs):
    states = replay.reconstruct(*inputs)
    assert len(states) == 201 and states[0]["time_s"] == 0
    assert states[-1]["time_s"] == pytest.approx(2e-5, rel=1e-14)
    assert "NOT PRINTED" in states[0]["source"]
    context = json.loads(inputs[0])
    for key, operator in (("native", "native_four_point"), ("physical_Gauss8", "physical_Gauss8")):
        for body in ("BOLT_NUT", "WASHER"):
            blocks = inputs[2]["operators"][operator][body]
            for state, initial in ((states[0], True), (states[1], False)):
                expected_p, expected_h, expected_ke = full_reference(context, blocks, body, initial=initial)
                actual = state["bodies"][body][key]
                assert actual["linear_momentum"] == pytest.approx(expected_p, rel=1e-12, abs=1e-12)
                assert actual["angular_momentum"] == pytest.approx(expected_h, rel=1e-12, abs=1e-12)
                assert actual["kinetic_energy"] == pytest.approx(expected_ke, rel=1e-12, abs=1e-12)
    assert states[1]["bodies"]["WASHER"]["native"]["kinetic_energy"] != states[1]["bodies"]["WASHER"]["physical_Gauss8"]["kinetic_energy"]
    assert math.hypot(*states[0]["bodies"]["WASHER"]["native"]["angular_momentum"]) > 0
    assert states[0]["bodies"]["BOLT_NUT"]["native"]["kinetic_energy"] == 0


@pytest.mark.parametrize("fault", ["cache_context", "cache_order", "deck", "short_grid", "duplicate_dat", "missing_contact", "missing_velocity"])
def test_inconsistent_or_incomplete_replay_is_rejected(inputs, fault):
    data, deck, cache, dat, sta = copy.deepcopy(inputs)
    if fault == "cache_context":
        cache["context_sha256"] = "0"*64
    elif fault == "cache_order":
        ids = next(iter(cache["operators"]["native_four_point"]["WASHER"].values()))[0]
        ids[-1], ids[-2] = ids[-2], ids[-1]
    elif fault == "deck":
        deck += b"*BOUNDARY\n1,1,3\n"
    elif fault == "short_grid":
        sta = "\n".join(sta.splitlines()[:-1])
    elif fault == "duplicate_dat":
        dat += "\n" + dat
    elif fault == "missing_contact":
        dat = dat.replace("contact stress (", "unknown contact stress (", 1)
    else:
        dat = dat.replace("velocities (vx,vy,vz) for set WASHER", "missing (vx,vy,vz) for set WASHER", 1)
    with pytest.raises(ValueError):
        replay.reconstruct(data, deck, cache, dat, sta)
