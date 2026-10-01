"""Independent every-increment oracle for the two-step nonzero-release coupon.

Reads the frozen native output; never rewrites a producer or native artifact.
The second step requires immediate release at unchanged external load.
"""
import hashlib
import json
import re
import sys
from pathlib import Path


def check(directory):
    directory = Path(directory)
    raw = (directory / "model.dat").read_text()
    blocks = {}
    for match in re.finditer(r"^\s*(displacements|forces) [^\n]*time\s+([\d.E+-]+)\n", raw, re.M):
        rows = {}
        for line in raw[match.end():].splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[0].isdigit():
                rows[int(fields[0])] = tuple(map(float, fields[1:]))
            elif rows:
                break
        key = (match[1], float(match[2]))
        if key in blocks:
            raise ValueError("Duplicate output block")
        blocks[key] = rows
    records, errors = [], []
    for kind, time in sorted(blocks):
        if kind != "displacements":
            continue
        u, rf = blocks[(kind, time)], blocks[("forces", time)]
        if set(u) != set(rf) or set(u) != set(range(1, 8)):
            raise ValueError("Incomplete coupon node inventory")
        if time <= 1.0:
            ft, fq = -3*time, -2*time
            t, q = -2.0, (2-2*time)/4
            normal = 2*q
        else:
            ft, fq = -3.0, -2.0
            t, q, normal = -4/3, -1/3, 0.0
        tangent = ft-(2*t+q)
        observed_t, observed_q = u[1][0], -u[2][1]
        observed_normal = rf[6][1]
        observed_tangent = ft-rf[7][0]
        displacement_error = max(abs(observed_t-t), abs(observed_q-q),
                                 abs(u[7][0]-t), abs(u[5][1]+q))
        force_error = max(abs(observed_normal-normal), abs(observed_tangent-tangent),
                          abs(rf[3][0]+t), abs(rf[4][1]-q))
        balance = [2*observed_t+observed_q+observed_tangent-ft,
                   observed_t+2*observed_q+observed_normal-fq]
        constitutive_error = abs(observed_normal-2*max(observed_q, 0))
        passed = (displacement_error < 2e-5 and force_error < 2e-4
                  and max(map(abs, balance)) < 2e-4 and constitutive_error < 2e-4)
        if not passed:
            errors.append(time)
        records.append({"time":time, "expected_t_q_N_T":[t,q,normal,tangent],
                        "observed_t_q_N_T":[observed_t,observed_q,observed_normal,observed_tangent],
                        "max_displacement_error_mm":displacement_error,
                        "max_force_error_N":force_error, "balance_N":balance,
                        "normal_law_error_N":constitutive_error, "pass":passed})
    times = [r["time"] for r in records]
    coverage = bool(times) and any(t < 1 for t in times) and any(1 < t < 2 for t in times)
    coverage = coverage and 1.0 in times and 2.0 in times
    stdout = (directory / "native.stdout").read_text()
    mode = ("Newton-Raphson iterative procedure is active" in stdout
            and "effects are turned off" in stdout
            and "Nonlinear geometric effects are taken into account" not in stdout)
    return {"status":"PASS_PARENT_NONZERO_RELEASE_ALL_INCREMENTS" if coverage and mode and not errors else "REJECT_PARENT_NONZERO_RELEASE_CHECK",
            "model_dat_sha256":hashlib.sha256(raw.encode()).hexdigest(),
            "coverage_pass":coverage, "native_mode_pass":mode,
            "failed_times":errors, "increment_count":len(records),
            "reaction_rule_generalized_T":"Ft-RF(T_REFERENCE,1)",
            "frame_ready":False, "joint_accepted":False, "records":records}


if __name__ == "__main__":
    result = check(sys.argv[1])
    print(json.dumps(result, indent=2, allow_nan=False))
    sys.exit(0 if result["status"].startswith("PASS") else 1)
