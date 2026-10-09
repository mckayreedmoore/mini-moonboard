"""Verify current placement identities, general-segment bounds and CLI guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().relative_to(Path.cwd().resolve()).parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


GUARD = """import importlib.util
from pathlib import Path
import sys
p, config, output, phase = map(Path, sys.argv[1:])
phase = str(phase)
spec = importlib.util.spec_from_file_location("copied_prepare", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
original, original_open = m.encode, Path.open
if phase in ("before", "race"):
    count = 0
    def encode(value):
        global count
        count += 1
        if phase == "before":
            with p.open("ab") as handle: handle.write(b"\\n# controlled source drift\\n")
        elif count == 1:
            with (output/"placement.json").open("xb") as handle: handle.write(b"other-writer\\n")
        return original(value)
    m.encode = encode
else:
    def opened(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        if path == output/"placement.json" and args and args[0] == "xb":
            class Proxy:
                def __enter__(self): return self
                def __exit__(self, *exc): return handle.__exit__(*exc)
                def write(self, value): return handle.write(value)
                def flush(self):
                    handle.flush()
                    with original_open(p, "ab") as stream: stream.write(b"\\n# controlled write-time drift\\n")
            return Proxy()
        return handle
    Path.open = opened
try:
    m.build(config, output)
except (ValueError, FileExistsError) as error:
    if phase == "race":
        if not isinstance(error, FileExistsError) or (output/"placement.json").read_bytes()!=b"other-writer\\n": raise
    elif "source drift:" not in str(error) or (output/"placement.json").exists(): raise
    if (output/"result.json").exists(): raise RuntimeError("failure published success")
else:
    raise RuntimeError("controlled source/output guard did not reject")
"""


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    config = json.loads((HERE / "inputs.json").read_bytes())
    result = json.loads((HERE / "result.json").read_bytes())
    placement = json.loads((HERE / "placement.json").read_bytes())
    pins = {
        **result["source_sha256"],
        **{
            str(HERE / name): sha(HERE / name)
            for name in ("placement.json", "result.json", "verify.py")
        },
    }
    for path, expected in pins.items():
        check(sha(path) == expected, "changed bound source: " + path)
    current = json.loads(Path(config["current_geometry"]).read_bytes())
    cache = json.loads(Path(config["current_cached_descriptors"]).read_bytes())
    axes = {a["id"]: a for a in current["axes"]}
    proposed = {a["id"]: a for a in placement["proposed_axes"]}
    targets = set(config["target_axis_ids"])
    check(
        set(proposed) == targets and len(proposed) == 4,
        "four explicit proposed axes required",
    )
    check(
        axes == {a["axis_id"]: a["source_axis"] for a in cache["shafts"]},
        "current 100-axis cache join",
    )
    check(
        {s["axis_id"]: s for s in current["screw_axes"]}
        == {s["id"]: s["source_screw_descriptor"] for s in cache["hillman_rows"]},
        "current 66-screw cache join",
    )
    for ident, candidate in proposed.items():
        source = axes[ident]
        point = [*source["point_xyz_mm"][:2], 180.0]
        check(
            source["point_xyz_mm"][2] == 200.0
            and {**source, "point_xyz_mm": point} == candidate,
            "only four Z coordinates may change",
        )
    review_path = next(
        p for p in config["sources"] if p.endswith("cleat-remedy-review-v1/review.py")
    )
    review = types.ModuleType("preserved_independent_segment_review")
    review.__file__ = review_path
    exec(compile(Path(review_path).read_bytes(), review_path, "exec"), review.__dict__)  # noqa: S102 -- checked pinned source.
    fixed = [a for a in current["axes"] if a["id"] not in targets]
    all_proposed = [proposed.get(a["id"], a) for a in current["axes"]]
    for key, rows in (
        ("current_fixed_96_canonical_sha256", fixed),
        ("current_66_screws_canonical_sha256", current["screw_axes"]),
        ("current_100_axes_canonical_sha256", current["axes"]),
        ("proposed_100_axes_canonical_sha256", all_proposed),
    ):
        check(
            review.canonical(rows) == placement[key],
            "placement canonical identity mismatch",
        )
    check(
        result["placement"]["sha256"] == sha(HERE / "placement.json"),
        "placement/result binding",
    )
    check(
        placement["geometry_adopted"] is False
        and all(v is False for v in result["release"].values())
        and set(result["current_drilling_holds"]) == targets,
        "unadopted HOLD4 boundary required",
    )
    screws = [
        review.primitive(
            s["axis_id"],
            role,
            s["origin_xyz_mm"],
            s["direction_xyz"],
            low,
            high,
            radius,
        )
        for s in current["screw_axes"]
        for role, low, high, radius in (
            ("screw_body", 3.0, 63.5, 2.5),
            ("screw_head_containing_cylinder", 0.0, 3.0, 4.5),
        )
    ]
    fixed_primitives = [p for a in fixed for p in review.hardware(a)]
    comparisons, maximum_error = 0, 0.0
    for index, row in enumerate(result["screens"]):
        lower = [axes[k] if index == 0 else proposed[k] for k in sorted(targets)]
        nominal = [p for a in lower for p in review.hardware(a)]
        maximum = [p for a in lower for p in review.hardware(a, maximum=True)]
        own_mask = review.np.asarray([[a[0] < b[0] for b in maximum] for a in maximum])
        for key, first, second, mask in (
            ("nominal_bore_vs_66_current_screws", nominal, screws, None),
            ("maximum_bore_vs_66_current_screws", maximum, screws, None),
            ("maximum_bore_vs_96_current_fixed_bolts", maximum, fixed_primitives, None),
            ("maximum_bore_vs_other_lower_bolts", maximum, maximum, own_mask),
        ):
            observed = row[key]
            maximum_error = max(
                maximum_error, review.summary_check(observed, first, second, mask)
            )
            _, gaps = review.matrix(first, second)
            valid = review.np.ones(gaps.shape, bool) if mask is None else mask
            check(
                int((gaps[valid] > 0).sum()) == observed["positive_bound_count"],
                "positive-count mismatch",
            )
            comparisons += observed["count"]
            for role, witness in observed["minimum_by_lower_role"].items():
                role_mask = (
                    valid & review.np.asarray([a[1] == role for a in first])[:, None]
                )
                check(
                    abs(
                        float(gaps[role_mask].min())
                        - witness["capsule_separation_lower_bound_mm"]
                    )
                    < 1e-9,
                    "independent role minimum mismatch",
                )
    checks = []

    def command(name, args, success):
        process = subprocess.run(
            [sys.executable, "-B", *args], capture_output=True, text=True, check=False
        )
        with (output / (name + ".json")).open("x") as handle:
            json.dump(
                {
                    "argv": [sys.executable, "-B", *map(str, args)],
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                },
                handle,
                indent=2,
                sort_keys=True,
            )
            handle.write("\n")
        check((process.returncode == 0) is success, "CLI guard failed: " + name)
        checks.append({"name": name, "passed": True})

    producer = HERE / "prepare.py"
    replay = output / "replayed"
    command("fresh_byte_replay", [str(producer), "--out", str(replay)], True)
    for name in ("placement.json", "result.json"):
        check(
            (replay / name).read_bytes() == (HERE / name).read_bytes(),
            "replay byte mismatch",
        )
    command("occupied_output_preserved", [str(producer), "--out", str(replay)], False)
    command(
        "source_output_alias_rejected",
        [str(producer), "--out", str(HERE / "inputs.json")],
        False,
    )
    bad = output / "bad-input.json"
    bad.write_text("{}\n")
    rejected = output / "rejected"
    command(
        "wrong_input_hash_rejected",
        [str(producer), "--inputs", str(bad), "--out", str(rejected)],
        False,
    )
    check(not any(rejected.iterdir()), "failed source hash must not publish artifacts")
    for phase in ("before", "during", "race"):
        copied = output / ("copied-" + phase + ".py")
        copied.write_bytes(producer.read_bytes())
        command(
            "source_or_late_output_" + phase,
            [
                "-c",
                GUARD,
                str(copied),
                str(HERE / "inputs.json"),
                str(output / phase),
                phase,
            ],
            True,
        )
    for name in ("placement.json", "result.json"):
        check(
            (replay / name).read_bytes() == (HERE / name).read_bytes(),
            "occupied replay changed",
        )
    for path, expected in pins.items():
        check(sha(path) == expected, "source or issued artifact changed: " + path)
    check(
        not any(k in sys.modules for k in ("cadquery", "OCP")), "unexpected CAD import"
    )
    receipt = {
        "schema": "eoere_current_Z180_identity_and_general_segment_verification/v1",
        "passed": True,
        "source_sha256": pins,
        "sources_unchanged_after": True,
        "unchanged_current_axes": 96,
        "unchanged_current_screws": 66,
        "exact_four_Z_moves": True,
        "general_segment_comparisons": comparisons,
        "maximum_minimum_bound_error_mm": maximum_error,
        "reused_independent_method": {
            "path": review_path,
            "sha256": pins[review_path],
            "functions": ["primitive", "hardware", "matrix", "summary_check"],
        },
        "runtime": {"python": sys.version.split()[0], "numpy": review.np.__version__},
        "controls": checks,
        "controls_scope": "Four direct CLI runs and three copied-module source/output interpositions; no live source is mutated.",
        "no_model_geometry_CAD_native_frame_force_or_physical_execution": True,
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
                "general_segment_comparisons": comparisons,
                "maximum_bound_error_mm": maximum_error,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
