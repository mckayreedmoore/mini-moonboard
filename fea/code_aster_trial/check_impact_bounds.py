"""Apply the parent-frozen limits to both impact comparisons and refinement."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("trial", type=Path)
    a = p.parse_args()
    base = a.trial
    readiness = base / "impact-readiness.json"
    limits = json.loads(readiness.read_text())
    paths = {"coarse": base / "impact-coarse-attempt02", "fine": base / "impact-fine-attempt01"}
    reports, checks, hashes = {}, [], {}
    metrics = {"x1_error_mm": "position_abs_mm", "x2_error_mm": "position_abs_mm",
               "v1_error_mm_s": "velocity_abs_mm_s", "v2_error_mm_s": "velocity_abs_mm_s",
               "gap_error_mm": "gap_abs_mm", "normal_force_from_gap_error_N": "law_derived_force_abs_N"}
    for case, folder in paths.items():
        source = folder / "comparison.json"
        data = json.loads(source.read_text())
        reports[case] = data
        hashes[str(source.relative_to(base))] = hashlib.sha256(source.read_bytes()).hexdigest()
        execution = json.loads((folder / "execution.json").read_text())
        checks.append({"case": case, "check": "execution_and_freeze",
                       "pass": execution["returncode"] == 0 and not execution["timed_out"] and not execution["changed_frozen_inputs"]})
        checks.append({"case": case, "check": "state_count", "pass": data["state_count"] == (97 if case == "coarse" else 193)})
        for metric, key in metrics.items():
            error = data["maximum_absolute_errors"][metric]["absolute"]
            checks.append({"case": case, "check": metric, "error": error,
                           "limit": limits[case][key], "pass": 0 <= error <= limits[case][key]})
        for key, error in [("relative_total_energy_error", data["maximum_total_energy_drift_N_mm"] / 50.0),
                           ("momentum_absolute_error_tonne_mm_s", data["maximum_momentum_drift_tonne_mm_s"])]:
            checks.append({"case": case, "check": key, "error": error,
                           "limit": limits["both"][key], "pass": 0 <= error <= limits["both"][key]})
    for metric in metrics:
        coarse = reports["coarse"]["maximum_absolute_errors"][metric]["absolute"]
        fine = reports["fine"]["maximum_absolute_errors"][metric]["absolute"]
        checks.append({"case": "refinement", "check": metric, "coarse": coarse, "fine": fine,
                       "coarse_over_fine": coarse / fine if fine else None,
                       "pass": fine <= max(0.5 * coarse, 1e-9)})
    result = {"status": "PASS" if all(row["pass"] for row in checks) else "FAIL",
              "scope": "Discrete two-mass impact fixture only; not surface contact or a timber joint",
              "readiness_sha256": hashlib.sha256(readiness.read_bytes()).hexdigest(),
              "comparison_sha256": hashes, "checks": checks,
              "limits": "Contact force and penalty energy are reconstructed from the known law; native SIEF_ELGA output is not qualified."}
    (base / "impact-bounds-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
