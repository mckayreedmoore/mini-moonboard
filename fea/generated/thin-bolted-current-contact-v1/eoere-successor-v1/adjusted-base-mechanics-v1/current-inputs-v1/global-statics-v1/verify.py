"""Check current global statics numerically and exercise its source/output guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from decimal import Decimal, localcontext
from pathlib import Path

HERE = Path(__file__).resolve().relative_to(Path.cwd().resolve()).parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def near(actual, expected, tolerance):
    if not math.isfinite(actual) or abs(actual - expected) > tolerance:
        raise ValueError(f"independent arithmetic mismatch: {actual} != {expected}")
    return abs(actual - expected)


def hull(points):
    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    points = sorted({tuple(p[:2]) for p in points})
    lower, upper = [], []
    for chain, ordered in ((lower, points), (upper, reversed(points))):
        for point in ordered:
            while len(chain) >= 2 and cross(chain[-2], chain[-1], point) <= 0:
                chain.pop()
            chain.append(point)
    return lower[:-1] + upper[:-1]


def numerical(record):
    current_path = next(
        p
        for p in record["source_bindings"]
        if p.endswith("current-inputs-v1/attempt01/inputs.json")
    )
    data = json.loads(Path(current_path).read_bytes())
    observed = json.loads(
        Path(data["geometry"]["cached_source_export"]["path"]).read_bytes()
    )
    if {
        r["host"]: r["observed_normal_reference_points_xyz_mm"]
        for r in observed["floor_observations"]
    } != data["floor_footprints"]:
        raise ValueError("current saved-floor/input join mismatch")
    points = [
        p
        for host in sorted(data["floor_footprints"])
        for p in data["floor_footprints"][host]
    ]
    polygon = hull(points)
    if len(points) != 32 or len(polygon) != 6 or len(record["cases"]) != 7:
        raise ValueError("support/case census mismatch")
    max_force = max_moment = max_margin = max_witness = 0.0
    rows = []
    for source, case in zip(data["cases"], record["cases"], strict=True):
        if source["case_id"] != case["case_id"] or case["source_load_count"] != len(
            source["loads"]
        ):
            raise ValueError("case identity/load census mismatch")
        with localcontext() as context:
            context.prec = 45
            force = [Decimal(0)] * 3
            moment = [Decimal(0)] * 3
            for load in source["loads"]:
                p = [Decimal(str(v)) for v in load["point_xyz_mm"]]
                f = [Decimal(str(v)) for v in load["force_xyz_n"]]
                for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
                    force[i] += f[i]
                    moment[i] += p[j] * f[k] - p[k] * f[j]
        force, moment = [float(v) for v in force], [float(v) for v in moment]
        max_force = max(
            max_force,
            *(
                near(a, b, 1e-8)
                for a, b in zip(case["applied_force_xyz_n"], force, strict=True)
            ),
        )
        max_moment = max(
            max_moment,
            *(
                near(a, b, 1e-6)
                for a, b in zip(case["applied_moment_xyz_nmm"], moment, strict=True)
            ),
        )
        weight = -force[2]
        cop = [moment[1] / weight, -moment[0] / weight]
        for actual, expected in zip(
            case["required_center_of_pressure_xy_mm"], cop, strict=True
        ):
            near(actual, expected, 1e-9)
        margins = []
        for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=True):
            dx, dy = b[0] - a[0], b[1] - a[1]
            margins.append(
                (dx * (cop[1] - a[1]) - dy * (cop[0] - a[0])) / math.hypot(dx, dy)
            )
        margin = min(margins)
        max_margin = max(
            max_margin,
            near(case["minimum_support_polygon_edge_margin_mm"], margin, 1e-9),
        )
        if sorted(map(tuple, case["support_polygon_xy_mm"])) != sorted(polygon):
            raise ValueError("independent support hull mismatch")
        if case["compression_equilibrium_possible"] is not (margin >= 0):
            raise ValueError("normal feasibility claim mismatch")
        near(case["total_normal_reaction_n"], weight, 1e-8)
        near(
            case["minimum_aggregate_friction_ratio_ignoring_yaw_and_distribution"],
            math.hypot(*force[:2]) / weight,
            1e-12,
        )
        near(case["required_reaction_yaw_moment_nmm"], -moment[2], 1e-6)
        witness = case["normal_reaction_witness_n"]
        if len(witness) != len(points) or any(
            not math.isfinite(v) or v < 0 for v in witness
        ):
            raise ValueError("finite nonnegative normal witness required")
        residual = [
            math.fsum(witness) - weight,
            math.fsum(p[1] * n for p, n in zip(points, witness, strict=True))
            + moment[0],
            -math.fsum(p[0] * n for p, n in zip(points, witness, strict=True))
            + moment[1],
        ]
        max_witness = max(max_witness, abs(residual[1]), abs(residual[2]))
        for actual, tolerance in zip(residual, (1e-8, 1e-4, 1e-4), strict=True):
            near(actual, 0, tolerance)
        for actual, expected in zip(
            case["equilibrium_residual_n_and_scaled_moment_n_m"],
            (residual[0], residual[1] / 1000, residual[2] / 1000),
            strict=True,
        ):
            near(actual, expected, 1e-8)
        if case["elastic_joint_demands_or_floor_capacity_established"] is not False:
            raise ValueError(
                "global result must not claim elastic demands or floor capacity"
            )
        rows.append({"case_id": case["case_id"], "independent_margin_mm": margin})
    if (
        any(v is not False for v in record["release"].values())
        or record["input_readiness_preserved"] != data["readiness"]
    ):
        raise ValueError("release/readiness boundary mismatch")
    near(
        record["mass"]["total_kg"],
        -float(data["cases"][-1]["applied_force_xyz_n"][2])
        / data["parameters"]["gravity_m_s2"],
        1e-10,
    )
    summary = record["summary"]
    if summary["case_count"] != 7 or summary["compression_feasible_case_count"] != 7:
        raise ValueError("summary case counts mismatch")
    worst = min(rows, key=lambda r: r["independent_margin_mm"])
    if summary["minimum_edge_margin_case"] != worst["case_id"]:
        raise ValueError("summary governing case mismatch")
    near(summary["minimum_edge_margin_mm"], worst["independent_margin_mm"], 1e-9)
    return {
        "case_count": len(rows),
        "polygon_vertex_count": len(polygon),
        "rows": rows,
        "max_force_error_n": max_force,
        "max_moment_error_nmm": max_moment,
        "max_margin_error_mm": max_margin,
        "max_normal_witness_moment_residual_nmm": max_witness,
    }


GUARD_CODE = """import importlib.util
from pathlib import Path
import sys
p, target, phase = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
spec = importlib.util.spec_from_file_location("copied_statics", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
original_encoded, original_open = m.encoded, Path.open
if phase == "before":
    def encoded(value):
        with p.open("ab") as handle: handle.write(b"\\n# controlled own-source drift\\n")
        return original_encoded(value)
    m.encoded = encoded
else:
    def opened(path, *args, **kwargs):
        if path == target and args and args[0] == "xb":
            if phase == "race":
                with original_open(target, "xb") as handle: handle.write(b"other-writer\\n")
            handle = original_open(path, *args, **kwargs)
            class Proxy:
                def __enter__(self): return self
                def __exit__(self, *exc): return handle.__exit__(*exc)
                def write(self, value): return handle.write(value)
                def flush(self):
                    handle.flush()
                    with original_open(p, "ab") as stream: stream.write(b"\\n# controlled write-time drift\\n")
            return Proxy()
        return original_open(path, *args, **kwargs)
    Path.open = opened
try:
    m.run(m.CURRENT, target)
except (ValueError, FileExistsError) as error:
    if phase == "race":
        if not isinstance(error, FileExistsError) or target.read_bytes() != b"other-writer\\n": raise
    elif "source changed during calculation:" not in str(error) or target.exists(): raise
else:
    raise RuntimeError("guard failed to reject the controlled corruption")
"""


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    result_path, helper = HERE / "result.json", HERE / "check_current.py"
    record = json.loads(result_path.read_bytes())
    pins = {
        **record["source_bindings"],
        str(result_path): sha(result_path),
        str(HERE / "verify.py"): sha(HERE / "verify.py"),
    }
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError(f"frozen source changed: {path}")
    independent = numerical(record)
    checks = []

    def command(name, args, expected_exit, absent=None):
        process = subprocess.run(
            [sys.executable, "-B", *args], capture_output=True, text=True, check=False
        )
        item = {
            "name": name,
            "argv": [sys.executable, "-B", *map(str, args)],
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }
        with (output / (name + ".json")).open("x") as handle:
            json.dump(item, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
        if (process.returncode == 0) is not expected_exit or (
            absent is not None and absent.exists()
        ):
            raise ValueError(f"CLI guard failed: {name}")
        checks.append({"name": name, "passed": True})

    replay = output / "replayed.json"
    command("fresh_exact_replay", [str(helper), "--out", str(replay)], True)
    if replay.read_bytes() != result_path.read_bytes():
        raise ValueError("fresh replay differs from issued bytes")
    command("occupied_output_preserved", [str(helper), "--out", str(replay)], False)
    if replay.read_bytes() != result_path.read_bytes():
        raise ValueError("occupied output changed")
    current_path = next(
        p
        for p in record["source_bindings"]
        if p.endswith("current-inputs-v1/attempt01/inputs.json")
    )
    command("source_output_alias_rejected", [str(helper), "--out", current_path], False)
    bad = output / "bad-input.json"
    bad.write_text("{}\n")
    bad_result = output / "bad-result.json"
    command(
        "wrong_input_hash_rejected",
        [str(helper), "--inputs", str(bad), "--out", str(bad_result)],
        False,
        bad_result,
    )
    for phase in ("before", "during", "race"):
        folder = output / phase
        folder.mkdir()
        copy = folder / "copied-helper.py"
        copy.write_bytes(helper.read_bytes())
        command(
            "source_drift_or_late_output_" + phase,
            ["-c", GUARD_CODE, str(copy), str(folder / "result.json"), phase],
            True,
        )
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError(
                f"source or issued result changed during verification: {path}"
            )
    receipt = {
        "schema": "eoere_current_global_statics_verification/v1",
        "passed": True,
        "source_bindings": pins,
        "source_bindings_unchanged_after": True,
        "numerical_check": independent,
        "controls": checks,
        "controls_scope": "Four direct CLI runs plus three controlled copied-module source/output interpositions; live sources never mutated.",
        "no_frame_or_native_or_CAD_execution": True,
        "reproduce": f".venv/bin/python -B {HERE / 'verify.py'} --out NEW_EMPTY_DIRECTORY",
    }
    with (output / "receipt.json").open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(
        json.dumps(
            {
                "passed": True,
                "controls": len(checks),
                "independent_cases": independent["case_count"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
