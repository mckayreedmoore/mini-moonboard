"""Independently integrate recorded synthetic fields; never rerun CAD or FEA."""

import argparse
import copy
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = next(p for p in PACKET.parents if (p / "uv.lock").exists())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(result, details, inputs):
    if result["analyze_sha256"] != sha(PACKET / "analyze.py") or result[
        "inputs_sha256"
    ] != sha(PACKET / "inputs.json"):
        raise ValueError("Result source/input hash mismatch")
    expected = {
        f"{case['id']}/{n}": case
        for case in inputs["published_cases"] + inputs["synthetic_cases"]
        for n in inputs["cells_per_member"]
    }
    if details.keys() != expected.keys():
        raise ValueError("Missing or extra synthetic fields")
    maxima = {
        "member_force_residual_lbf": 0.0,
        "shaft_force_residual_lbf": 0.0,
        "shaft_end_moment_lb_in": 0.0,
        "moment_bound_ratio": 0.0,
        "bearing_bound_ratio": 0.0,
    }
    for key, field in details.items():
        case = expected[key]
        cells = int(key.rsplit("/", 1)[1])
        arrays = [
            field[k]
            for k in ("a_in", "b_in", "bearing_density_lb_in", "bearing_bounds_lb_in")
        ]
        if not all(len(array) == 2 * cells for array in arrays):
            raise ValueError("Bad recorded field dimension")
        a, b, density, caps = arrays
        segments = list(zip(a, b, density))
        if not all(math.isfinite(v) for array in arrays for v in array):
            raise ValueError("Nonfinite recorded field")
        ls, lm, gap = (case[k] for k in ("side_length_in", "main_length_in", "gap_in"))
        for i, (lo, hi, _) in enumerate(segments):
            local = i % cells
            offset, span = (0.0, ls) if i < cells else (ls + gap, lm)
            if (
                abs(lo - (offset + span * local / cells)) > 1e-12
                or abs(hi - (offset + span * (local + 1) / cells)) > 1e-12
            ):
                raise ValueError("Recorded interval differs from frozen coupon")
            expected_cap = (
                case["side_bearing_lb_in"] if i < cells else case["main_bearing_lb_in"]
            )
            if caps[i] != expected_cap:
                raise ValueError("Changed synthetic material bound")
        if field["moment_bound_lb_in"] != case["yield_moment_lb_in"]:
            raise ValueError("Changed synthetic moment bound")
        load = field["statics_load_lbf"]
        if not math.isfinite(load) or load <= 0:
            raise ValueError("Invalid synthetic load")
        side = math.fsum(q * (hi - lo) for lo, hi, q in segments[:cells])
        main = math.fsum(q * (hi - lo) for lo, hi, q in segments[cells:])
        force_error = max(abs(side - load), abs(main + load))

        # Direct dimensional primitives, independent of normalized LP assembly
        # and the producer's recursive prefix integration.
        def moment(x, segments=segments):
            return math.fsum(
                q * (max(x - lo, 0) ** 2 - max(x - hi, 0) ** 2) / 2
                for lo, hi, q in segments
            )

        points = list(a) + list(b)
        for lo, hi, q in segments:
            shear = math.fsum(
                v * (max(lo - aa, 0) - max(lo - bb, 0)) for aa, bb, v in segments
            )
            if q != 0 and lo < lo - shear / q < hi:
                points.append(lo - shear / q)
        maximum = max(abs(moment(x)) for x in points)
        end_moment = abs(moment(ls + gap + lm))
        bearing_ratio = max(abs(q) / cap for q, cap in zip(density, caps))
        moment_ratio = maximum / case["yield_moment_lb_in"]
        if (
            force_error > 1e-8
            or end_moment > 1e-8
            or bearing_ratio > 1 + 1e-10
            or moment_ratio > 1 + 1e-9
        ):
            raise ValueError(f"Recorded field fails exact polynomial statics: {key}")
        row = next(row for row in result["cases"] if row["id"] == case["id"])
        grid = next(grid for grid in row["grids"] if grid["cells_per_member"] == cells)
        if (
            load != grid["scaled_statics_load_lbf"]
            or abs(maximum - grid["maximum_exact_moment_lb_in"]) > 1e-8
        ):
            raise ValueError("Recorded field disagrees with compact result")
        maxima = {
            key: max(maxima[key], value)
            for key, value in {
                "member_force_residual_lbf": force_error,
                "shaft_force_residual_lbf": abs(side + main),
                "shaft_end_moment_lb_in": end_moment,
                "moment_bound_ratio": moment_ratio,
                "bearing_bound_ratio": bearing_ratio,
            }.items()
        }
    return {"independently_integrated_fields": len(details), **maxima}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        parser.error("Verification output must be new")
    inputs = json.loads((PACKET / "inputs.json").read_text())
    result = json.loads((args.run / "result.json").read_text())
    details = json.loads((args.run / "details.json").read_text())
    for pin in inputs["references"]:
        if sha(ROOT / pin["path"]) != pin["sha256"]:
            raise ValueError(f"Changed source: {pin['path']}")
    independent = check(result, details, inputs)
    replay = {
        name: sha(args.run / name) == sha(args.replay / name)
        for name in ("result.json", "details.json")
    }
    if not all(replay.values()):
        raise ValueError("Replay is not byte identical")
    rejected = []
    first = next(iter(details))
    for corruption in (
        "bearing_impulse",
        "missing_field",
        "moment_bound",
        "input_hash",
    ):
        bad_result, bad_details = copy.deepcopy(result), copy.deepcopy(details)
        if corruption == "bearing_impulse":
            bad_details[first]["bearing_density_lb_in"][0] += 1000
        elif corruption == "missing_field":
            del bad_details[first]
        elif corruption == "moment_bound":
            bad_details[first]["moment_bound_lb_in"] *= 2
        else:
            bad_result["inputs_sha256"] = "0" * 64
        try:
            check(bad_result, bad_details, inputs)
        except ValueError:
            rejected.append(corruption)
        else:
            raise ValueError(f"Corrupt evidence accepted: {corruption}")
    before = {name: sha(args.run / name) for name in ("result.json", "details.json")}
    existing = subprocess.run(
        [sys.executable, str(PACKET / "analyze.py"), "--out", str(args.run)],
        capture_output=True,
        text=True,
        check=False,
    )
    if existing.returncode != 2 or "must be a new directory" not in existing.stderr:
        raise ValueError("Existing-output CLI rejection failed")
    if before != {name: sha(args.run / name) for name in before}:
        raise ValueError("Guard test changed issued bytes")
    verification = {
        "schema": "synthetic_dowel_bearing_moment_limit_verification/v1",
        "verify_sha256": sha(__file__),
        "independent_checks": independent,
        "byte_identical_replay": replay,
        "rejected_corrupt_evidence": rejected,
        "existing_output_rejected_before_write": True,
        "source_pins_matched": len(inputs["references"]),
        "run_files": {
            name: {"path": str(args.run / name), "sha256": digest}
            for name, digest in before.items()
        },
        "source_files": {
            name: sha(PACKET / name) for name in ("analyze.py", "inputs.json")
        },
        "candidate_inputs_used": False,
        "capacity_or_pass_claim": False,
    }
    with args.out.open("x") as stream:
        json.dump(verification, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(independent, sort_keys=True))


if __name__ == "__main__":
    main()
