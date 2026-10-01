"""Independent every-increment oracle for the ten-step staged coupon.

Run against the parent-frozen native output directory. This file does not run
CalculiX or modify the frozen input or native output.
"""
from collections import Counter
from decimal import Decimal, ROUND_CEILING
from fractions import Fraction as F
import hashlib
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent

# (Ft start, Ft end, Fq start, Fq end, captured tangent reference). The
# concentrated Q_BODY load has the opposite sign from generalized Fq.
SCHEDULE = (
    (F(0), F(-4), F(0), F(-3), None),
    (F(-4), F(-4), F(-3), F(-2), None),
    (F(-4), F(-4), F(-2), F(-1), F(-2)),
    (F(-4), F(-4), F(-1), F(-3, 2), F(-2)),
    (F(-4), F(-4), F(-3, 2), F(-2), F(-2)),
    (F(-4), F(-4), F(-2), F(-5, 2), None),
    (F(-4), F(-2), F(-5, 2), F(-3), None),
    (F(-2), F(-2), F(-3), F(-1), None),
    (F(-2), F(-2), F(-1), F(0), F(-1)),
    (F(-2), F(-2), F(0), F(1), F(-1)),
)
U_TOL_MM = 2e-5
FORCE_TOL_N = 2e-4


def _open(ft, fq):
    return (2 * ft - fq) / 3, (-ft + 2 * fq) / 3


def _expected(stage, fraction):
    ft0, ft1, fq0, fq1, reference = SCHEDULE[stage - 1]
    ft = ft0 + (ft1 - ft0) * fraction
    fq = fq0 + (fq1 - fq0) * fraction
    if reference is None:
        t, q = _open(ft, fq)
        normal = 2 * max(q, F(0))
        tangent = F(0)
    else:
        # With K=[[2,1],[1,2]], the normal equilibrium is
        # t + 2q + 2*max(q,0) = Fq. Select the matching unilateral branch.
        delta = fq - reference
        q = delta / 4 if delta >= 0 else delta / 2
        t = reference
        normal = 2 * max(q, F(0))
        tangent = ft - (2 * t + q)
    return {"Ft": ft, "Fq": fq, "t": t, "q": q,
            "N": normal, "T": tangent, "reference": reference}


def _verify_endpoint_oracle():
    known = json.loads((HERE / "known-answer.json").read_text())
    rows = known["states"]
    if len(rows) != len(SCHEDULE):
        raise ValueError("Known-answer table must have one endpoint per scheduled step")
    for stage, row in enumerate(rows, 1):
        expected = _expected(stage, F(1))
        observed = tuple(F(row[key]) for key in (
            "Ft_N", "Fq_N", "t_mm", "q_mm", "N_N", "T_generalized_N"))
        exact = tuple(expected[key] for key in ("Ft", "Fq", "t", "q", "N", "T"))
        if observed != exact:
            raise ValueError(f"Known-answer endpoint mismatch at stage {stage}: {observed} != {exact}")
        reaction = F(row["physical_support_reaction_on_body_N"])
        if reaction != -expected["T"]:
            raise ValueError(f"Known-answer support reaction mismatch at stage {stage}")
    return len(rows)


def verify_oracle():
    """Replay exact rational step endpoints and sample each scheduled ramp."""
    endpoint_count = _verify_endpoint_oracle()
    sample_fractions = (F(0), F(1, 2), F(1))
    open_steps = {1, 2, 6, 7, 8}
    held_references = {3: F(-2), 4: F(-2), 5: F(-2), 9: F(-1), 10: F(-1)}
    for stage in range(1, 11):
        ft0, ft1, fq0, fq1, reference = SCHEDULE[stage - 1]
        if stage > 1:
            prev = SCHEDULE[stage - 2]
            if (prev[1], prev[3]) != (ft0, fq0):
                raise ValueError(f"Discontinuous applied loads at stage {stage}")
        if stage in open_steps and reference is not None:
            raise ValueError(f"Stage {stage} should have a free tangent reference")
        if stage in held_references and reference != held_references[stage]:
            raise ValueError(f"Stage {stage} has the wrong captured reference")
        for fraction in sample_fractions:
            state = _expected(stage, fraction)
            if reference is None:
                rx = 2 * state["t"] + state["q"] + state["T"] - state["Ft"]
                rq = state["t"] + 2 * state["q"] + state["N"] - state["Fq"]
                if state["T"] != 0 or state["q"] > 0 or rx or rq:
                    raise ValueError(f"Open branch/oracle balance failed at stage {stage}, f={fraction}")
            else:
                rx = 2 * state["t"] + state["q"] + state["T"] - state["Ft"]
                rq = state["t"] + 2 * state["q"] + state["N"] - state["Fq"]
                if state["q"] < 0 or state["N"] != 2 * state["q"] or rx or rq:
                    raise ValueError(f"Held branch/oracle balance failed at stage {stage}, f={fraction}")
    return {"status":"PASS_STAGED_RATIONAL_ORACLE", "stages":10,
            "samples_per_stage":len(sample_fractions),
            "known_answer_endpoints":endpoint_count}


def _read_blocks(path):
    raw = path.read_text()
    blocks = {}
    header = re.compile(
        r"^[ \t]*(displacements|forces) [^\n]*?\btime[ \t]+([\d.Ee+-]+)[ \t]*\r?\n", re.M)
    for match in header.finditer(raw):
        rows = {}
        for line in raw[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                rows[int(fields[0])] = tuple(map(float, fields[1:]))
            elif rows:
                break
        if not rows:
            continue
        key = (match.group(1), Decimal(match.group(2)))
        if key in blocks:
            raise ValueError(f"Duplicate native output block: {key}")
        blocks[key] = rows
    return raw, blocks


def check(directory):
    directory = Path(directory)
    known_answer_count = _verify_endpoint_oracle()
    raw, blocks = _read_blocks(directory / "model.dat")
    records, failures = [], []
    for kind, time in sorted(blocks):
        if kind != "displacements":
            continue
        force_key = ("forces", time)
        if force_key not in blocks:
            raise ValueError(f"Missing RF block at total time {time}")
        u, rf = blocks[(kind, time)], blocks[force_key]
        if set(u) != set(rf) or set(u) != set(range(1, 8)):
            raise ValueError(f"Incomplete seven-node output inventory at total time {time}")

        stage = int(time.to_integral_value(rounding=ROUND_CEILING))
        if not 1 <= stage <= len(SCHEDULE):
            raise ValueError(f"Native increment outside ten-step schedule: {time}")
        fraction = F(time) - F(stage - 1)
        if not F(0) < fraction <= F(1):
            raise ValueError(f"Unexpected local step time {fraction} at total time {time}")
        expected = _expected(stage, fraction)
        ft, fq = float(expected["Ft"]), float(expected["Fq"])
        t, q = float(expected["t"]), float(expected["q"])
        normal, tangent = float(expected["N"]), float(expected["T"])

        observed_t = u[1][0]
        observed_q = -u[2][1]
        observed_tangent = ft - rf[7][0]
        observed_normal = rf[6][1]
        displacement_error = max(
            abs(observed_t - t), abs(observed_q - q),
            abs(u[7][0] - t), abs(u[5][1] + q))
        ground_spring_errors = (rf[3][0] + observed_t, rf[4][1] - observed_q)
        force_error = max(
            abs(observed_tangent - tangent), abs(observed_normal - normal),
            *map(abs, ground_spring_errors))
        balance = (
            2 * observed_t + observed_q + observed_tangent - ft,
            observed_t + 2 * observed_q + observed_normal - fq)
        normal_law_error = abs(observed_normal - 2 * max(observed_q, 0.0))
        if expected["reference"] is None:
            branch_error = max(0.0, observed_q)
            open_tangent_error = abs(observed_tangent)
        else:
            branch_error = max(0.0, -observed_q)
            open_tangent_error = 0.0
        passed = (
            displacement_error < U_TOL_MM
            and force_error < FORCE_TOL_N
            and max(map(abs, balance)) < FORCE_TOL_N
            and normal_law_error < FORCE_TOL_N
            and branch_error < U_TOL_MM
            and open_tangent_error < FORCE_TOL_N)
        if not passed:
            failures.append(str(time))
        records.append({
            "time":str(time), "stage":stage, "local_fraction":str(fraction),
            "expected_Ft_Fq_t_q_N_T":[ft,fq,t,q,normal,tangent],
            "observed_t_q_N_T":[observed_t,observed_q,observed_normal,observed_tangent],
            "max_displacement_error_mm":displacement_error,
            "max_force_error_N":force_error,
            "ground_spring_reaction_errors_N":list(ground_spring_errors),
            "body_balance_residual_N":list(balance),
            "normal_law_error_N":normal_law_error,
            "contact_branch_error_mm":branch_error,
            "pass":passed,
        })

    counts = Counter(row["stage"] for row in records)
    times = {Decimal(row["time"]) for row in records}
    stage_coverage = all(counts[stage] > 0 for stage in range(1, 11))
    endpoint_coverage = all(Decimal(stage) in times for stage in range(1, 11))
    mode_stdout = (directory / "native.stdout").read_text()
    mode_pass = (
        "Newton-Raphson iterative procedure is active" in mode_stdout
        and "effects are turned off" in mode_stdout
        and "Nonlinear geometric effects are taken into account" not in mode_stdout)
    capture_first_increment_pass = True
    for stage, reference in ((3, -2.0), (9, -1.0)):
        first = next((row for row in records if row["stage"] == stage), None)
        if first is None:
            capture_first_increment_pass = False
            continue
        # Per-increment displacement checks above cover every print. These
        # first-record checks make entry-time capture an explicit result.
        capture_first_increment_pass &= abs(first["observed_t_q_N_T"][0] - reference) < U_TOL_MM

    passed = (stage_coverage and endpoint_coverage and mode_pass
              and capture_first_increment_pass and not failures)
    return {
        "status":"PASS_PARENT_STAGED_COUPON_ALL_INCREMENTS" if passed
                 else "REJECT_PARENT_STAGED_COUPON_CHECK",
        "model_dat_sha256":hashlib.sha256(raw.encode()).hexdigest(),
        "known_answer_endpoint_count":known_answer_count,
        "increment_count":len(records),
        "increment_counts_by_stage":{str(stage):counts[stage] for stage in range(1, 11)},
        "stage_coverage_pass":stage_coverage,
        "endpoint_coverage_pass":endpoint_coverage,
        "native_mode_pass":mode_pass,
        "capture_first_increment_pass":capture_first_increment_pass,
        "failed_times":failures,
        "reaction_rule_generalized_T":"Ft-RF(T_REFERENCE,1)",
        "normal_force_rule":"RF(NORMAL_GROUND,2)=2*max(q,0)",
        "open_steps_require_zero_tangent":[1,2,6,7,8],
        "frame_ready":False,
        "joint_accepted":False,
        "records":records,
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["--verify-oracle"]:
        print(json.dumps(verify_oracle(), indent=2))
        raise SystemExit(0)
    if len(sys.argv) != 2:
        raise SystemExit("usage: parent_staged_check.py NATIVE_OUTPUT_DIRECTORY | --verify-oracle")
    result = check(sys.argv[1])
    print(json.dumps(result, indent=2, allow_nan=False))
    sys.exit(0 if result["status"].startswith("PASS") else 1)
