"""Synthetic observer protocol tests; these are not solver validation runs."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from fea.mortar_linear_law import residuals
from fea.mortar_observer_replay import PREFIX, records, replay


def fixture(*, steps=2, cutback=True, excluded=False, override=False):
    events, sta = [], []

    def call(step, inc, attempt, iteration, theta, dt, outcome):
        call_id = 1 + sum(r["kind"] == "BEGIN" for r in events)

        def emit(kind, **fields):
            events.append({"kind": kind, "call_id": call_id, **fields})

        context = {"step": step, "inc": inc, "cutback": attempt-1, "iteration": iteration,
                   "time": theta+dt, "dtime": dt, "ttime": float(step-1), "tper": 1., "theta": theta,
                   "dtheta": dt, "icntrl": 0, "nmethod": 1, "iexpl": 0, "ithermal": 0,
                   "uncoupled": 0, "mortar": 2, "iflagdualquad": 2}
        emit("BEGIN", **context)
        emit("INVENTORY", pair_count=1, slave_count=2)
        emit("PAIR", pair=0, start=0, end=2)
        raw = [[2., 4., 10.], [6., 8., 20.]]
        starts = [[1., 2., 3.], [3., 4., 5.]]
        # Nonsymmetric coupling with off-diagonal terms catches transposition
        # and the common error of multiplying only a guessed nodal area.
        matrix = [[1., .5], [2., 3.]]  # columns, then destinations
        for slot in (0, 1):
            emit("PRE_RAW", pair=0, slot=slot, node=7+slot, activity=-1 if excluded and slot else 1,
                 lambda_raw=raw[slot], lambda_start=starts[slot], ddtil_count=2)
            for destination, value in enumerate(matrix[slot]):
                emit("DDTIL", pair=0, column_slot=slot, source_slot=slot,
                     destination_slot=destination, entry=slot*2+destination, value=value)
        measured = []
        for slot in (0, 1):
            weighted = [sum(matrix[s][slot]*raw[s][i] for s in (0, 1)) for i in range(3)]
            history = [sum(matrix[s][slot]*starts[s][i] for s in (0, 1)) for i in range(3)]
            inputs = {"ln": weighted[2], "lt": weighted[:2], "lt_start": history[:2], "q": weighted[2]/10000,
                      "ut": [.01*(a-b) for a, b in zip(weighted[:2], history[:2], strict=True)],
                      "mu": .5, "normal_inverse_stiffness": .0001, "tangent_inverse_stiffness": .01,
                      "constant_n": 10000., "constant_t": 100., "activity": -1 if excluded and slot else 1,
                      "ndof": 3, "normal_mode": 1, "tangent_mode": 1}
            if override:
                inputs["q"] += .01  # Large residual survives a forced flag reset.
            result = residuals(**inputs)
            measured.append(result)
            emit("LAW", pair=0, slot=slot, node=7+slot, normal=[0., 0., 1.],
                 tangents=[1., 0., 0., 0., 1., 0.], **inputs,
                 gn=result["normal_regularization"], gt=result["tangent_regularization"],
                 b=result["algorithmic_friction_bound"], p0=0., beta=0., iwan=1,
                 rn=result["normal_residual"], rt=result["tangent_residual"])
        for slot in (0, 1):
            emit("POST_RAW_AFTER_ACTIVE_LOOP", pair=0, slot=slot, node=7+slot,
                 activity=-1 if excluded and slot else 1,
                 lambda_raw=[0., 0., 0.] if excluded and slot else raw[slot], gap=0.)
        eligible = [r for r in measured if r["eligible"]]
        emit("SUMMARY_PRE_OVERRIDE", ndiverg=14, flag=int(override), keepset=0,
             max_n=max(abs(r["normal_residual"]) for r in eligible),
             max_t=[max(abs(r["tangent_residual"][i]) for r in eligible) for i in (0, 1)],
             lm_t_av=[33., 46.], nstick=1 if excluded else 2, nslip=0, ninactive=0,
             nnogap=int(excluded), nolm=0)
        emit("SUMMARY_POST_OVERRIDE", flag=0 if iteration > 14 else int(override))
        emit("RETURN")
        emit("PRE_CHECK", **context)
        post = dict(context)
        if outcome == "accept":
            post.update(icntrl=1, cutback=0, theta=theta+dt, dtheta=dt if theta+dt < 1 else 0.)
        elif outcome == "reject":
            post.update(icntrl=1, cutback=attempt, dtheta=dt/2)
        else:
            post["iteration"] += 1
        emit("POST_CHECK", **post)
        if outcome != "continue":
            endpoint = theta if outcome == "reject" else theta+dt
            attempt_text = str(attempt) + ("U" if outcome == "reject" else "")
            sta.append(f"{step} {inc} {attempt_text} {iteration} {step-1+endpoint:.6E} {endpoint:.6E} {dt:.6E}")

    for step in range(1, steps+1):
        if cutback:
            call(step, 1, 1, 1, 0., 1., "reject")
        count = 15 if override else 2
        for inc in ((1, 2) if cutback else (1,)):
            for iteration in range(1, count+1):
                call(step, inc, 2 if cutback and inc == 1 else 1, iteration,
                     (inc-1)*.5, .5 if cutback else 1., "accept" if iteration == count else "continue")
    return events, "STEP INC ATT ITER TOTAL STEP INC_TIME\n" + "\n".join(sta)


def stream(events):
    return "ordinary solver output\n" + "\n".join(PREFIX+json.dumps(row) for row in events)


def test_multistep_cutback_accepted_state_and_matrix_reconstruction():
    events, sta = fixture()
    result = replay(stream(events), sta)
    assert result["accepted_call_ids"] == [3, 5, 8, 10]
    assert result["calls"][0]["accepted"] is False
    assert result["calls"][2]["attempt"] == 2
    assert result["calls"][2]["nodes"][0]["normal_residual"] == pytest.approx(0)
    assert result["calls"][2]["nodes"][0]["tangent_regularization"] == pytest.approx([.07, .1])
    assert "NOT VALIDATED" in result["status"]


def test_excluded_nodes_and_forced_override_are_reported_not_passed():
    events, sta = fixture(steps=1, cutback=False, excluded=True, override=True)
    result = replay(stream(events), sta)
    assert result["accepted_override_call_ids"] == [15]
    accepted = result["calls"][-1]
    assert accepted["pre_override_flag"] == 1
    assert accepted["nodes"][0]["normal_residual"] < -1
    assert not accepted["nodes"][1]["eligible"]
    assert accepted["nodes"][1]["activity"] == -1
    assert "pass" not in accepted


@pytest.mark.parametrize("kind", ["BEGIN", "INVENTORY", "PAIR", "PRE_RAW", "DDTIL", "LAW",
    "POST_RAW_AFTER_ACTIVE_LOOP", "SUMMARY_PRE_OVERRIDE", "SUMMARY_POST_OVERRIDE", "RETURN", "PRE_CHECK", "POST_CHECK"])
@pytest.mark.parametrize("mutation", ["drop", "duplicate", "reorder"])
def test_record_corruption_fails_closed(kind, mutation):
    events, sta = fixture(steps=1)
    index = next(i for i, row in enumerate(events) if row["kind"] == kind)
    if mutation == "drop":
        events.pop(index)
    elif mutation == "duplicate":
        events.insert(index, copy.deepcopy(events[index]))
    else:
        events[index], events[index+1] = events[index+1], events[index]
    with pytest.raises(ValueError):
        replay(stream(events), sta)


@pytest.mark.parametrize("kind,key,value", [
    ("BEGIN", "ithermal", 2), ("BEGIN", "uncoupled", 1), ("BEGIN", "nmethod", 4),
    ("BEGIN", "iflagdualquad", 1), ("BEGIN", "iteration", True),
    ("BEGIN", "ttime", float("nan")), ("LAW", "ln", float("inf")),
    ("LAW", "normal", [0., 0., 2.]), ("LAW", "lt_start", [0., 0.]),
    ("LAW", "rn", 1.), ("LAW", "rt", [1., 0.]), ("LAW", "normal_mode", 2),
    ("PRE_RAW", "lambda_raw", [0., 0., 0.]), ("PRE_RAW", "lambda_start", [0., 0., 0.]),
    ("DDTIL", "value", 99.), ("DDTIL", "destination_slot", 100),
    ("SUMMARY_PRE_OVERRIDE", "nstick", 99), ("SUMMARY_POST_OVERRIDE", "flag", 1),
    ("POST_CHECK", "theta", 1.),
])
def test_wrong_identity_arithmetic_scope_and_nonfinite_fail(kind, key, value):
    events, sta = fixture(steps=1)
    next(row for row in events if row["kind"] == kind)[key] = value
    with pytest.raises(ValueError):
        replay(stream(events), sta)


def test_missing_iteration_complete_pair_and_sta_corruptions():
    events, sta = fixture()
    for bad in (sta.replace("2U", "2"), sta+"\n"+sta.splitlines()[-1],
                "\n".join(sta.splitlines()[:-1]), sta.replace("1U", "2U"),
                sta.replace("5.000000E-01", "5.100000E-01")):
        if bad != sta:
            with pytest.raises(ValueError):
                replay(stream(events), bad)
    with pytest.raises(ValueError):
        replay(stream([r for r in events if r["call_id"] != 2]), sta)
    bad = [r for r in events if not (r["call_id"] == 1 and r["kind"] in ("PAIR", "PRE_RAW", "DDTIL", "LAW", "POST_RAW_AFTER_ACTIVE_LOOP"))]
    with pytest.raises(ValueError):
        replay(stream(bad), sta)


@pytest.mark.parametrize("text", [PREFIX+'{"kind":"RETURN","call_id":1,"call_id":1}',
    PREFIX+'{"kind":"UNKNOWN","call_id":1}', 'wrong '+PREFIX+'{}', PREFIX+'{truncated', ""])
def test_malformed_json_protocol(text):
    with pytest.raises(ValueError):
        records(text)


@pytest.mark.parametrize("case,call_count,accepted_count,node_count,max_normal", [
    ("mortar_0p25", 28, 8, 72, 2.6020847698760008e-9),
    ("mortar_0p125", 45, 16, 144, 2.602083881697581e-9),
])
def test_frozen_observer_cube_logs_replay_without_solver(case, call_count, accepted_count, node_count, max_normal):
    root = Path("fea/mortar_observer_build/cube-qyk279w_")
    report_bytes = (root/"report.json").read_bytes()
    assert hashlib.sha256(report_bytes).hexdigest() == "5b9a6c9345650057bf57bae0f43a8b4edd00cdacbadbe574fdc5ab076ebc7ee8"
    report = json.loads(report_bytes)
    build = root.parent/"build-rvk4q426"
    for name in ("build_result", "build_manifest"):
        assert hashlib.sha256((build/(name+".json")).read_bytes()).hexdigest() == report[name+"_sha256"]
    assert hashlib.sha256((root/"compare_cube.launch.py").read_bytes()).hexdigest() == report["launch_source_sha256"]
    item = next(r for r in report["runs"] if r["case"] == case and r["binary"] == "observer")
    assert item["exit_code"] == 0 and item["accepted_history_equal_to_archive"] is True
    directory = root/(case+"-observer")
    for name in ("cube.log", "cube.sta", "cube.inp", "original.context.json"):
        assert hashlib.sha256((directory/name).read_bytes()).hexdigest() == item["output_sha256"][name]
    assert item["deck_sha256"] == item["output_sha256"]["cube.inp"]
    result = replay((directory/"cube.log").read_text(), (directory/"cube.sta").read_text())
    assert len(result["calls"]) == call_count
    assert len(result["accepted_call_ids"]) == accepted_count
    assert result["accepted_override_call_ids"] == []
    nodes = [node for call in result["calls"] if call["accepted"] for node in call["nodes"]]
    assert len(nodes) == node_count and all(node["eligible"] for node in nodes)
    # Frozen numerical fingerprint, not a proposed contact acceptance threshold.
    assert max(abs(node["normal_residual"]) for node in nodes) == pytest.approx(max_normal, rel=1e-10, abs=1e-18)
    assert "NOT VALIDATED" in result["status"]
