"""Reject parent components before using the unchanged frozen v2 entrypoint."""

import argparse
import hashlib
import json
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
V2_MAP_SHA256 = "1d214a9a31f37cdaf358a58daba2d143baf79e22787677516e8b6251933f83ce"
SOURCE_AT_LOAD = Path(__file__).read_bytes()
INPUT_AT_LOAD = (HERE / "inputs.json").read_bytes()


def reject_parent_components(*paths):
    for path in paths:
        if ".." in Path(path).parts:
            raise ValueError(
                "Parent component '..' is unsupported in run/replay/out paths"
            )


def _engine():
    # Capture this supplement before importing anything it guards.
    bound = {
        HERE / "run.py": hashlib.sha256(SOURCE_AT_LOAD).hexdigest(),
        HERE / "inputs.json": hashlib.sha256(INPUT_AT_LOAD).hexdigest(),
        HERE / "check.py": hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest(),
    }
    metadata = json.loads(INPUT_AT_LOAD)
    if (
        metadata["schema"] != "synthetic_limit_parent_path_boundary_inputs/v3"
        or metadata["candidate_inputs_used"] is not False
        or metadata["capacity_or_pass_claim"] is not False
    ):
        raise ValueError("Wrong synthetic path-boundary inputs")
    files = metadata["frozen_v2_files"]
    canonical = (
        json.dumps(files, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    if hashlib.sha256(canonical).hexdigest() != V2_MAP_SHA256:
        raise ValueError("Unrecognized frozen v2 six-file map")
    captured = {}
    for relative, pin in files.items():
        path = ROOT / relative
        data = path.read_bytes()
        if (
            path != V2 / path.name
            or hashlib.sha256(data).hexdigest() != pin["sha256"]
            or len(data) != pin["bytes"]
        ):
            raise ValueError("Changed frozen v2 file")
        bound[path], captured[relative] = pin["sha256"], data
    for pin in metadata["review_receipts"]:
        bound[ROOT / pin["path"]] = pin["sha256"]

    def sources_unchanged():
        for path, expected in bound.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Loaded supplement/source changed: {path}")

    sources_unchanged()
    launcher = types.ModuleType("captured_frozen_v2_launcher")
    launcher.__file__ = str(V2 / "run.py")
    # Execute the exact v2 launcher bytes authenticated above.
    exec(  # noqa: S102
        compile(
            captured[str((V2 / "run.py").relative_to(ROOT))], launcher.__file__, "exec"
        ),
        launcher.__dict__,
    )
    engine = launcher.load_body().prepare()
    sources_unchanged()
    previous_snapshot, previous_unchanged = engine.snapshot, engine.unchanged
    previous_produce, previous_verify = engine.produce, engine.verify

    def unchanged(pins):
        sources_unchanged()
        previous_unchanged(pins)

    def snapshot():
        sources_unchanged()
        state = previous_snapshot()
        for path, expected in bound.items():
            relative = str(path.relative_to(ROOT))
            if relative in state["pins"] and state["pins"][relative] != expected:
                raise ValueError("Supplement source snapshot mismatch")
            state["pins"][relative] = expected
            state["contents"][relative] = path.read_bytes()
        unchanged(state["pins"])
        return state

    def produce(output):
        reject_parent_components(output)
        return previous_produce(output)

    def verify(run, replay, output):
        reject_parent_components(run, replay, output)
        return previous_verify(run, replay, output)

    engine.unchanged, engine.snapshot = unchanged, snapshot
    engine.produce, engine.verify = produce, verify
    return engine


def produce(output):
    reject_parent_components(output)
    return _engine().produce(output)


def verify(run, replay, output):
    reject_parent_components(run, replay, output)
    return _engine().verify(run, replay, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("produce").add_argument("--out", type=Path, required=True)
    validation = sub.add_parser("verify")
    for name in ("run", "replay", "out"):
        validation.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = (
            produce(args.out)
            if args.command == "produce"
            else verify(args.run, args.replay, args.out)
        )
    except (OSError, ValueError, TypeError, KeyError, StopIteration) as error:
        parser.exit(1, f"Evidence rejected: {error}\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "validated_claims": result["validated_claims"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
