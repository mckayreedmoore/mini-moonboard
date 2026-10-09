"""Fail-closed replay entrypoint for the frozen v3 producer and its inputs.

Default verifies existing evidence only. --run-out explicitly invokes the
unchanged, source-authenticated producer, then verifies its input bindings.
This gate was not part of the original v3 CAD execution.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DOC = Path(
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
)
PARENT = DOC / "occupied-aligned-wire-v1.json"
PARENT_SHA = "2b31d82a41cd6eb1c80e3ed84b2d0cae428fdc575b1c8c6fa27d7c3e6f0276c5"
REPORTS = {
    DOC
    / "occupied-adjusted-base-v3.json": "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7",
    DOC
    / "occupied-2026-adjustments-v3.json": "5dfa03b785715c92717725400e73bf41b00a58160595ddf6b61b61c3b31f6134",
}
INPUTS = (
    DOC / "occupied-bottom-rail-v1.json",
    DOC.parent / "native-geometry-v4.json",
    Path("site/eoere-bottom-rail-scene.json.gz"),
)
PRODUCER = Path("scripts/eoere_2026_adjustments.py")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def authenticated(path, expected, reader):
    data = reader(path)
    if digest(data) != expected:
        raise ValueError(f"canonical source differs: {path}")
    return data


def join_pins(*maps):
    joined = {}
    for mapping in maps:
        for name, expected in mapping.items():
            path = str(Path(name).resolve())
            if path in joined and joined[path] != expected:
                raise ValueError(f"conflicting source bindings: {path}")
            joined[path] = expected
    return joined


def contract(reader=Path.read_bytes):
    parent = json.loads(authenticated(PARENT, PARENT_SHA, reader))
    canonical = {str(PARENT): PARENT_SHA}
    for path in INPUTS:
        expected = parent["source_sha256"][str(path)]
        canonical[str(path)] = expected
    source_maps = []
    report_pins = {}
    for path, expected in REPORTS.items():
        report = json.loads(authenticated(path, expected, reader))
        source_maps.append(report["source_sha256"])
        report_pins[str(path)] = expected
    frozen = join_pins(*source_maps)
    if len(frozen) != 570 or str(PRODUCER.resolve()) not in frozen:
        raise ValueError("complete 570-source frozen producer contract required")
    joined = join_pins(canonical, frozen, report_pins)
    return frozen, joined


def verify(reader=Path.read_bytes):
    frozen, pins = contract(reader)
    for name, expected in pins.items():
        authenticated(Path(name), expected, reader)
    return frozen, pins


def verify_replay_bindings(report, frozen, output, reader=Path.read_bytes):
    actual = join_pins(report["source_sha256"])
    for name, expected in frozen.items():
        if actual.get(name) != expected:
            raise ValueError(f"replayed frozen source differs or is missing: {name}")
    for name, expected in actual.items():
        path = Path(name)
        if name not in frozen and not path.is_relative_to(output.resolve()):
            raise ValueError(f"unexpected nongenerated replay source: {path}")
        authenticated(path, expected, reader)
    return actual


def controls():
    rejected = []
    frozen, _ = verify()
    helper = Path("scripts/thin_bolted_occupied.py")
    cache = Path(next(name for name in frozen if name.endswith(".brep")))
    # Readers simulate changed/missing inputs without altering evidence bytes.
    for target in (PARENT, *INPUTS, PRODUCER, *REPORTS, helper, cache):
        for mode in ("changed", "missing"):

            def reader(path, target=target, mode=mode):
                if path.resolve() == target.resolve():
                    if mode == "missing":
                        raise FileNotFoundError(str(path))
                    return path.read_bytes() + b"changed-input"
                return path.read_bytes()

            try:
                verify(reader)
            except (ValueError, FileNotFoundError):
                rejected.append({"path": str(target), "mode": mode})
            else:
                raise AssertionError(f"accepted {mode} source: {target}")
    try:
        join_pins({str(helper): "a" * 64}, {str(helper.resolve()): "b" * 64})
    except ValueError:
        rejected.append({"mode": "conflicting_relative_absolute_alias"})
    else:
        raise AssertionError("accepted conflicting alias hashes")
    output = Path("fea/generated/replay-gate-synthetic-control").resolve()
    generated = output / "new-output.brep"
    payload = b"synthetic-generated-output"

    def reader(path):
        return payload if path == generated else path.read_bytes()

    example = {"source_sha256": {**frozen, str(generated): digest(payload)}}
    verify_replay_bindings(example, frozen, output, reader)
    for target in (PRODUCER, helper, cache):
        for mode in ("missing_replay_binding", "changed_replay_binding"):
            bindings = dict(example["source_sha256"])
            name = str(target.resolve())
            if mode.startswith("missing"):
                bindings.pop(name)
            else:
                bindings[name] = "0" * 64
            try:
                verify_replay_bindings(
                    {"source_sha256": bindings}, frozen, output, reader
                )
            except ValueError:
                rejected.append({"path": name, "mode": mode})
            else:
                raise AssertionError(f"accepted {mode}: {name}")
    bindings = {
        **example["source_sha256"],
        str(Path("unfrozen-helper.py").resolve()): "0" * 64,
    }
    try:
        verify_replay_bindings({"source_sha256": bindings}, frozen, output, reader)
    except ValueError:
        rejected.append({"mode": "unexpected_nongenerated_replay_binding"})
    else:
        raise AssertionError("accepted unexpected nongenerated replay source")
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", required=True, type=Path, help="fresh replay-gate receipt"
    )
    parser.add_argument(
        "--run-out",
        type=Path,
        help="explicit fresh CAD replay output; omitted by default",
    )
    args = parser.parse_args()
    if args.out.exists() or (args.run_out is not None and args.run_out.exists()):
        raise ValueError("fresh receipt and replay output paths required")
    frozen, pins = verify()
    rejected = controls()
    if args.run_out is not None:
        subprocess.run(
            [sys.executable, "-B", str(PRODUCER), "--out", str(args.run_out)],
            check=True,
        )
        if verify() != (frozen, pins):
            raise ValueError("canonical replay inputs changed during execution")
        for path in (
            args.run_out / "base/geometry.json",
            args.run_out / "geometry.json",
        ):
            report = json.loads(path.read_bytes())
            verify_replay_bindings(report, frozen, args.run_out)
            pins[str(path)] = digest(path.read_bytes())
    pins[str(Path(__file__).relative_to(Path.cwd()))] = digest(
        Path(__file__).read_bytes()
    )
    result = {
        "schema": "eoere_2026_replay_source_gate/v2",
        "passed": True,
        "mode": "VERIFIED_REPLAY"
        if args.run_out is not None
        else "VERIFY_EXISTING_FROZEN_V3_INPUTS_ONLY",
        "original_v3_execution_used_this_gate": False,
        "geometry_or_assets_reissued": False,
        "cad_execution_this_check": args.run_out is not None,
        "native_solver": False,
        "canonical_input_count": len(INPUTS),
        "complete_frozen_source_count": len(frozen),
        "new_generated_output_binding_control_passed": True,
        "rejected_controls": rejected,
        "source_sha256": pins,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {"passed": True, "mode": result["mode"], "rejected_controls": len(rejected)}
        )
    )


if __name__ == "__main__":
    main()
