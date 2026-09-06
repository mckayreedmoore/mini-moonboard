"""Strict arithmetic/accepted-state replay of the pinned mortar observer stream.

This checks observed multiplier transformations and law arithmetic, not full
kinematics, a converged weak law, or physical resistance. No solver is launched.
"""
import argparse
import json
import math
from pathlib import Path

from fea.mortar_linear_law import residuals

PREFIX = "MORTAR_OBSERVER "
CONTEXT = "step inc cutback iteration time dtime ttime tper theta dtheta icntrl nmethod iexpl ithermal uncoupled mortar iflagdualquad"
SCHEMA = {
    **{kind: CONTEXT for kind in ("BEGIN", "PRE_CHECK", "POST_CHECK")},
    "INVENTORY": "pair_count slave_count",
    "PAIR": "pair start end",
    "PRE_RAW": "pair slot node activity lambda_raw lambda_start ddtil_count",
    "DDTIL": "pair column_slot source_slot destination_slot entry value",
    "LAW": "pair slot node activity ndof normal tangents ln lt lt_start q ut gn gt b constant_n constant_t mu normal_mode tangent_mode normal_inverse_stiffness tangent_inverse_stiffness p0 beta iwan rn rt",
    "POST_RAW_AFTER_ACTIVE_LOOP": "pair slot node activity lambda_raw gap",
    "SUMMARY_PRE_OVERRIDE": "ndiverg flag keepset max_n max_t lm_t_av nstick nslip ninactive nnogap nolm",
    "SUMMARY_POST_OVERRIDE": "flag",
    "RETURN": "",
}
INTEGERS = {"call_id", "step", "inc", "cutback", "iteration", "icntrl", "nmethod", "iexpl", "ithermal",
            "uncoupled", "mortar", "iflagdualquad", "pair_count", "slave_count", "pair", "start", "end",
            "slot", "node", "activity", "ddtil_count", "column_slot", "source_slot", "destination_slot",
            "entry", "ndof", "normal_mode", "tangent_mode", "iwan", "ndiverg", "flag", "keepset",
            "nstick", "nslip", "ninactive", "nnogap", "nolm"}
ARRAYS = {"lambda_raw": 3, "lambda_start": 3, "normal": 3, "tangents": 6,
          **{key: 2 for key in ("lt", "lt_start", "ut", "gt", "rt", "max_t", "lm_t_av")}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, name):
    """Arithmetic serialization/replay tolerance only; never a law tolerance."""
    require(math.isfinite(actual) and math.isfinite(expected) and
            math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12), "Arithmetic mismatch: " + name)


def _object(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "Duplicate JSON key")
    return result


def records(text):
    result = []
    for line in text.splitlines():
        if PREFIX.strip() not in line:
            continue
        require(line.startswith(PREFIX), "Malformed observer prefix")
        row = json.loads(line[len(PREFIX):], object_pairs_hook=_object)
        require(isinstance(row, dict) and type(row.get("kind")) is str and row["kind"] in SCHEMA, "Unknown observer record")
        require(set(row) == {"kind", "call_id", *SCHEMA[row["kind"]].split()}, "Observer schema differs")
        for key, value in row.items():
            if key == "kind":
                continue
            if key in INTEGERS:
                require(type(value) is int, "Integer required: " + key)
            else:
                values = value if key in ARRAYS else [value]
                require(isinstance(values, list) and len(values) == ARRAYS.get(key, 1), "Array length: " + key)
                require(all(type(v) in (int, float) and math.isfinite(v) for v in values), "Nonfinite scalar: " + key)
        result.append(row)
    require(bool(result), "Missing observer stream")
    return result


def _scope(context):
    require(context["nmethod"] == 1 and context["iexpl"] in (0, 1) and
            context["ithermal"] in (0, 1) and context["uncoupled"] == 0 and
            context["mortar"] == 2 and context["iflagdualquad"] == 2,
            "Only uncoupled-free static mechanical MORTAR is supported")
    require(context["step"] >= 1 and context["inc"] >= 1 and context["iteration"] >= 1 and
            context["cutback"] >= 0 and context["tper"] > 0, "Invalid increment identity")


def _sta(text):
    rows = []
    for line in text.splitlines():
        cells = line.split()
        if not cells or not cells[0].isdigit():
            continue
        require(len(cells) == 7, "Malformed STA row")
        rejected = cells[2].endswith("U")
        identity = tuple(int(v) for v in (cells[0], cells[1], cells[2].removesuffix("U"), cells[3]))
        values = [float(v) for v in cells[4:]]
        require(all(math.isfinite(v) for v in values), "Nonfinite STA row")
        require(all(v > 0 for v in identity), "Invalid STA identity")
        rows.append((identity, rejected, values, cells[4:]))
    require(bool(rows), "Missing STA history")
    return rows


def replay(text, sta_text):
    events, cursor = records(text), 0
    calls, terminal, previous, inventory = [], [], None, None

    def take(kind, call_id):
        nonlocal cursor
        require(cursor < len(events), "Truncated observer sequence: " + kind)
        row = events[cursor]
        require(row["kind"] == kind and row["call_id"] == call_id, "Missing/reordered record: " + kind)
        cursor += 1
        return row

    while cursor < len(events):
        call_id = len(calls) + 1
        begin = take("BEGIN", call_id)
        _scope(begin)
        require(begin["icntrl"] == 0 and begin["dtime"] > 0 and begin["dtheta"] > 0, "Invalid attempt start")
        same(begin["dtime"], begin["dtheta"] * begin["tper"], "attempt duration")
        same(begin["time"], (begin["theta"] + begin["dtheta"]) * begin["tper"], "attempt endpoint")
        if previous is None:
            require((begin["step"], begin["inc"], begin["cutback"], begin["iteration"]) == (1, 1, 0, 1), "Missing initial call")
            same(begin["theta"], 0, "initial theta")
            same(begin["ttime"], 0, "initial total time")
        else:
            pre, post, accepted = previous
            if begin["step"] == post["step"]:
                expected_inc = post["inc"] + int(accepted)
                expected_iteration = 1 if post["icntrl"] else post["iteration"]
                require((begin["inc"], begin["cutback"], begin["iteration"]) ==
                        (expected_inc, post["cutback"], expected_iteration), "Dropped/reordered iteration or retry")
                for field in ("theta", "dtheta", "ttime", "tper"):
                    same(begin[field], post[field], "next " + field)
            else:
                require(accepted and begin["step"] == post["step"] + 1 and post["theta"] >= 1-1e-6 and
                        (begin["inc"], begin["cutback"], begin["iteration"]) == (1, 0, 1), "Invalid step transition")
                same(begin["theta"], 0, "next step theta")
                same(begin["ttime"], post["ttime"] + post["tper"], "next step total time")
        counts = take("INVENTORY", call_id)
        require(counts["pair_count"] > 0 and counts["slave_count"] > 0, "Empty contact inventory")
        raw, entries, pairs = {}, [], []
        for _ in range(counts["pair_count"]):
            pair = take("PAIR", call_id)
            require(pair["pair"] >= 0 and pair["end"] > pair["start"] >= 0 and
                    (not pairs or pair["pair"] > pairs[-1][0]), "Invalid pair order/range")
            pairs.append((pair["pair"], pair["start"], pair["end"]))
            for slot in range(pair["start"], pair["end"]):
                row = take("PRE_RAW", call_id)
                require(row["slot"] == slot and row["pair"] == pair["pair"] and slot not in raw and
                        row["node"] > 0 and row["ddtil_count"] >= 0, "Incomplete/duplicate slave inventory")
                raw[slot] = row
                column_entries = []
                for _ in range(row["ddtil_count"]):
                    entry = take("DDTIL", call_id)
                    require(entry["pair"] == pair["pair"] and entry["column_slot"] == slot and entry["entry"] >= 0 and
                            (not column_entries or entry["entry"] == column_entries[-1] + 1), "Sparse column differs")
                    column_entries.append(entry["entry"])
                    entries.append(entry)
        require(len(raw) == counts["slave_count"] and len({r["node"] for r in raw.values()}) == len(raw),
                "Missing/repeated physical slave nodes; overlapping ties unsupported")
        current_inventory = (pairs, [(slot, row["pair"], row["node"]) for slot, row in raw.items()])
        if inventory is None:
            inventory = current_inventory
        require(current_inventory == inventory, "Contact inventory changed")
        require(len({r["entry"] for r in entries}) == len(entries), "Duplicate sparse entry")
        weighted = {slot: [[0., 0., 0.], [0., 0., 0.]] for slot in raw}
        for entry in entries:
            require(entry["destination_slot"] in raw and entry["source_slot"] in raw, "Uncovered sparse source/destination")
            for phase, field in enumerate(("lambda_raw", "lambda_start")):
                for axis, value in enumerate(raw[entry["source_slot"]][field]):
                    weighted[entry["destination_slot"]][phase][axis] += entry["value"] * value
        laws, results = {}, {}
        for slot, row in raw.items():
            law = take("LAW", call_id)
            require(all(law[k] == row[k] for k in ("pair", "slot", "node", "activity")), "Law/raw identity differs")
            bases = [law["normal"], law["tangents"][:3], law["tangents"][3:]]
            if law["activity"] >= 0 and law["ndof"] > 0:
                for i, a in enumerate(bases):
                    for j, b in enumerate(bases):
                        same(sum(x*y for x, y in zip(a, b, strict=True)), float(i == j), "orthonormal frozen basis")
            projections = [[sum(a*b for a, b in zip(vector, basis, strict=True)) for basis in bases]
                           for vector in weighted[slot]]
            for actual, expected in zip([law["ln"], *law["lt"], *law["lt_start"]],
                                        [*projections[0], *projections[1][1:]], strict=True):
                same(actual, expected, "DDTIL multiplier projection")
            fields = ("ln", "lt", "lt_start", "q", "ut", "mu", "normal_inverse_stiffness",
                      "tangent_inverse_stiffness", "constant_n", "constant_t", "activity", "ndof",
                      "normal_mode", "tangent_mode")
            result = residuals(**{field: law[field] for field in fields})
            for field, value in (("gn", result["normal_regularization"]), ("b", result["algorithmic_friction_bound"]),
                                 ("rn", result["normal_residual"])):
                same(law[field], value, "signed source " + field)
            for field, values in (("gt", result["tangent_regularization"]), ("rt", result["tangent_residual"])):
                for a, b in zip(law[field], values, strict=True):
                    same(a, b, "signed source " + field)
            laws[slot], results[slot] = law, result
        post_nodes = {}
        for slot, row in raw.items():
            post = take("POST_RAW_AFTER_ACTIVE_LOOP", call_id)
            require(all(post[k] == row[k] for k in ("pair", "slot", "node")) and
                    post["activity"] in (-3, -2, -1, 0, 1, 2), "Post-update node coverage differs")
            post_nodes[slot] = post
        summary = take("SUMMARY_PRE_OVERRIDE", call_id)
        require(summary["flag"] in (0, 1) and summary["keepset"] == 0 and summary["ndiverg"] >= 14,
                "Unsupported observer summary")
        for field, activity in (("nstick", 1), ("nslip", 2), ("ninactive", 0), ("nnogap", -1)):
            require(summary[field] == sum(r["activity"] == activity for r in post_nodes.values()), "Summary count differs: " + field)
        require(summary["nolm"] == sum(r["activity"] == -2 or (r["activity"] == -3 and laws[s]["mu"] <= 1e-10)
                                       for s, r in post_nodes.items()), "Excluded summary count differs")
        eligible = [r for r in results.values() if r["eligible"]]
        same(summary["max_n"], max((abs(r["normal_residual"]) for r in eligible), default=-1.), "max_n")
        for i in range(2):
            same(summary["max_t"][i], max((abs(r["tangent_residual"][i]) for r in eligible), default=-1.), "max_t")
        after = take("SUMMARY_POST_OVERRIDE", call_id)
        override = begin["iteration"] > summary["ndiverg"]
        require(after["flag"] == (0 if override else summary["flag"]), "Forced override differs")
        take("RETURN", call_id)
        pre, post = take("PRE_CHECK", call_id), take("POST_CHECK", call_id)
        require({k: pre[k] for k in CONTEXT.split()} == {k: begin[k] for k in CONTEXT.split()}, "Call/check context differs")
        _scope(post)
        require(0 <= post["theta"] <= 1+1e-12 and post["dtheta"] >= 0, "Invalid post-check time bounds")
        for field in set(CONTEXT.split()) - {"iteration", "cutback", "theta", "dtheta", "icntrl"}:
            require(post[field] == pre[field], "Unexpected check mutation: " + field)
        require(post["icntrl"] in (0, 1), "Unknown convergence decision")
        accepted = post["icntrl"] == 1 and post["cutback"] == 0
        if accepted:
            require(pre["iteration"] > 1 and post["iteration"] == pre["iteration"] and after["flag"] == 0,
                    "Invalid accepted mechanical iteration")
            same(post["theta"], pre["theta"] + pre["dtheta"], "accepted theta")
        else:
            same(post["theta"], pre["theta"], "unaccepted theta")
            require(post["cutback"] == pre["cutback"] + post["icntrl"] and
                    post["iteration"] == pre["iteration"] + 1-post["icntrl"], "Invalid continuation/cutback")
            if post["icntrl"]:
                require(0 < post["dtheta"] < pre["dtheta"], "Cutback did not reduce attempted duration")
            else:
                same(post["dtheta"], pre["dtheta"], "continuing iteration duration")
        if post["icntrl"]:
            terminal.append((pre, accepted))
        previous = pre, post, accepted
        calls.append({"call_id": call_id, "step": pre["step"], "inc": pre["inc"], "attempt": pre["cutback"]+1,
                      "iteration": pre["iteration"], "accepted": accepted, "forced_flag_override": override,
                      "pre_override_flag": summary["flag"],
                      "nodes": [{"pair": laws[s]["pair"], "node": laws[s]["node"], "activity": laws[s]["activity"],
                                 "post_activity": post_nodes[s]["activity"], **r} for s, r in results.items()]})
    require(previous[2] and previous[1]["theta"] >= 1-1e-6, "Incomplete final accepted step")
    sta = _sta(sta_text)
    require(len(sta) == len(terminal), "STA/observer terminal coverage differs")
    for (identity, rejected, values, printed), (pre, accepted) in zip(sta, terminal, strict=True):
        require(identity == (pre["step"], pre["inc"], pre["cutback"]+1, pre["iteration"]) and rejected != accepted,
                "STA decision identity differs")
        time = pre["time"] if accepted else pre["time"]-pre["dtime"]
        for actual, expected, token in zip(values, (pre["ttime"]+time, time, pre["dtime"]), printed, strict=True):
            exponent = int(token.lower().split("e")[1]) if "e" in token.lower() else 0
            digits = len(token.lower().split("e")[0].split(".")[-1]) if "." in token else 0
            require(abs(actual-expected) <= .500001*10**(exponent-digits) + abs(expected)*1e-14, "STA printed time differs")
    return {"status": "OBSERVER ARITHMETIC/COVERAGE REPLAY ONLY; WEAK LAW AND PHYSICAL CAPACITY NOT VALIDATED",
            "limitations": "Inputs require separately bound solver/build/deck provenance. DDTIL and frozen-basis multiplier transforms are replayed; gap, displacement kinematics, segmentation and complete coupling forces are not independently reconstructed. Arithmetic comparison thresholds are not law acceptance tolerances.",
            "calls": calls, "accepted_call_ids": [c["call_id"] for c in calls if c["accepted"]],
            "accepted_override_call_ids": [c["call_id"] for c in calls if c["accepted"] and c["forced_flag_override"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("sta", type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.log.read_text(), args.sta.read_text()), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
