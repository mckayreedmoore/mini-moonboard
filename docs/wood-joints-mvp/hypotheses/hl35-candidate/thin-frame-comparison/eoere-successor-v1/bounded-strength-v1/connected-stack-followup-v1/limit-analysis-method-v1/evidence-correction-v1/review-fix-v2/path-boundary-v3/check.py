"""Actual-CLI parent-path and serialization-retarget controls; no new mechanics."""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())


def load():
    spec = importlib.util.spec_from_file_location(
        "synthetic_path_boundary", HERE / "run.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(arguments):
    command = [sys.executable, "-B", *map(str, arguments)]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def retarget(args):
    wrapper = load()
    make_engine = wrapper._engine

    def instrumented_engine():
        (args.case / "engine-entered").write_text("engine loaded\n")
        engine = make_engine()
        encode = engine.encoded

        def instrumented_encode(value):
            data = encode(value)
            if (
                type(value) is dict
                and value.get("schema") == "synthetic_limit_corrected_verification/v1"
            ):
                (args.case / "serialization-hook-entered").write_text(
                    "retarget attempted\n"
                )
                if args.kind == "parent":
                    link = args.case / "lexical/link"
                    link.unlink()
                    link.symlink_to(
                        (args.case / "altered/nested").resolve(),
                        target_is_directory=True,
                    )
                else:
                    active = args.case / "run"
                    active.rename(args.case / "preserved-run")
                    active.symlink_to(
                        (args.case / "replacement").resolve(), target_is_directory=True
                    )
            return data

        engine.encoded = instrumented_encode
        return engine

    wrapper._engine = instrumented_engine
    supplied = (
        args.case / "lexical/link/../run"
        if args.kind == "parent"
        else args.case / "run"
    )
    sys.argv = [
        str(HERE / "run.py"),
        "verify",
        f"--run={supplied}",
        "--replay",
        str(args.replay),
        "--out",
        str(args.case / "verification.json"),
    ]
    wrapper.main()


def regress(output):
    output.mkdir(parents=True, exist_ok=False)
    wrapper = load()
    engine = wrapper._engine()
    state = engine.snapshot()
    commands = []
    run, replay = output / "fresh-run", output / "fresh-replay"
    for directory in (run, replay):
        record = cli([HERE / "run.py", "produce", f"--out={directory}"])
        commands.append(record)
        engine.need(record["returncode"] == 0, f"Fresh production failed: {record}")
    clean = output / "clean-verification.json"
    supplied = str(run) if run.is_absolute() else "./" + str(run)
    record = cli(
        [
            HERE / "run.py",
            "verify",
            f"--run={supplied}",
            "--replay",
            replay,
            "--out",
            clean,
        ]
    )
    commands.append(record)
    engine.need(
        record["returncode"] == 0, f"Ordinary relative verification failed: {record}"
    )
    for name in ("result.json", "details.json", "run-provenance.json"):
        engine.need(
            (run / name).read_bytes() == (replay / name).read_bytes(),
            "Fresh replay differs",
        )
    engine.need(
        (run / "result.json").read_bytes()
        == (engine.FROZEN / "result.json").read_bytes(),
        "Numerical result changed",
    )
    original = (
        ROOT
        / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/attempt03/details.json"
    )
    original_sha = engine.digest(original.read_bytes())
    engine.need(
        engine.digest((run / "details.json").read_bytes()) == original_sha,
        "Original fields changed",
    )

    def copy_run(path):
        path.mkdir(parents=True, exist_ok=True)
        for name in ("result.json", "details.json", "run-provenance.json"):
            (path / name).write_bytes((run / name).read_bytes())

    static = []
    for kind in ("produce_out", "verify_run", "verify_replay", "verify_out"):
        place = output / kind
        (place / "child").mkdir(parents=True)
        copy_run(place / "run")
        parent_run = place / "child/../run"
        target = place / "verification.json"
        if kind == "produce_out":
            arguments = [
                HERE / "run.py",
                "produce",
                f"--out={place / 'child/../produced'}",
            ]
        else:
            supplied_run = parent_run if kind == "verify_run" else run
            supplied_replay = parent_run if kind == "verify_replay" else replay
            supplied_out = (
                place / "child/../verification.json" if kind == "verify_out" else target
            )
            arguments = [
                HERE / "run.py",
                "verify",
                f"--run={supplied_run}",
                f"--replay={supplied_replay}",
                f"--out={supplied_out}",
            ]
        record = cli(arguments)
        commands.append(record)
        engine.need(
            record["returncode"] != 0
            and "Parent component '..'" in record["stderr"]
            and not target.exists()
            and not (place / "produced").exists(),
            "Parent path accepted",
        )
        static.append(kind)
    race = output / "parent-retarget"
    for path in (race / "lexical/run", race / "actual/run", race / "altered/run"):
        copy_run(path)
    for path in (race / "actual/nested", race / "altered/nested"):
        path.mkdir()
    (race / "lexical/link").symlink_to(
        (race / "actual/nested").resolve(), target_is_directory=True
    )
    altered = json.loads((race / "altered/run/result.json").read_bytes())
    altered["candidate_joint_capacity"] = 12345.0
    (race / "altered/run/result.json").write_bytes(engine.encoded(altered))
    record = cli(
        [
            HERE / "run.py",
            "verify",
            f"--run={race / 'lexical/link/../run'}",
            "--replay",
            replay,
            "--out",
            race / "static-receipt.json",
        ]
    )
    commands.append(record)
    engine.need(
        record["returncode"] != 0
        and "Parent component '..'" in record["stderr"]
        and not (race / "static-receipt.json").exists(),
        "Symlink/parent path accepted",
    )
    record = cli(
        [
            HERE / "check.py",
            "retarget",
            "--kind",
            "parent",
            "--case",
            race,
            "--replay",
            replay,
        ]
    )
    commands.append(record)
    engine.need(
        record["returncode"] != 0
        and "Parent component '..'" in record["stderr"]
        and not (race / "verification.json").exists()
        and not (race / "engine-entered").exists()
        and not (race / "serialization-hook-entered").exists(),
        "Parent path reached engine/retarget serialization",
    )
    ordinary = output / "ordinary-retarget"
    copy_run(ordinary / "run")
    copy_run(ordinary / "replacement")
    record = cli(
        [
            HERE / "check.py",
            "retarget",
            "--kind",
            "ordinary",
            "--case",
            ordinary,
            "--replay",
            replay,
        ]
    )
    commands.append(record)
    engine.need(
        record["returncode"] != 0
        and (
            "Symlink evidence path:" in record["stderr"]
            or "Lexical evidence identity changed:" in record["stderr"]
        )
        and (ordinary / "serialization-hook-entered").exists()
        and not (ordinary / "verification.json").exists(),
        "Existing serialization guard regressed",
    )
    api = []
    for operation, paths in (
        (wrapper.produce, (output / "child/../api-out",)),
        (wrapper.verify, (output / "child/../run", replay, output / "api.json")),
        (engine.produce, (output / "child/../backend-out",)),
        (engine.verify, (run, output / "child/../replay", output / "backend.json")),
    ):
        try:
            operation(*paths)
        except ValueError as error:
            engine.need(
                "Parent component '..'" in str(error), "Wrong API parent rejection"
            )
            api.append(operation.__name__)
        else:
            raise ValueError("Public/backend API accepted parent component")
    engine.unchanged(state["pins"])
    engine.need(
        engine.digest(original.read_bytes()) == original_sha,
        "Original raw fields changed",
    )
    verified = json.loads(clean.read_bytes())
    result = {
        "schema": "synthetic_limit_parent_path_boundary_regressions/v3",
        "status": "ALL_PARENT_PATH_CONTROLS_PASS",
        "source_sha256": state["pins"],
        "static_parent_path_controls_rejected": static,
        "symlink_parent_static_rejected": True,
        "parent_serialization_retarget_rejected_before_engine_loading": True,
        "ordinary_serialization_retarget_still_rejected": True,
        "API_parent_path_controls_rejected": api,
        "fresh_three_file_replay_byte_identical": True,
        "numeric_result_and_fields_match_original": True,
        "validated_claims": verified["validated_claims"],
        "independent_checks": verified["independent_checks"],
        "commands": commands,
    }
    engine.new_file(output / "regressions.json", engine.encoded(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_count": len(state["pins"]),
                "negative_CLI_controls": len(commands) - 3,
            },
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("regress").add_argument("--out", type=Path, required=True)
    retargeting = sub.add_parser("retarget")
    retargeting.add_argument("--kind", choices=("parent", "ordinary"), required=True)
    retargeting.add_argument("--case", type=Path, required=True)
    retargeting.add_argument("--replay", type=Path, required=True)
    args = parser.parse_args()
    retarget(args) if args.command == "retarget" else regress(args.out)


if __name__ == "__main__":
    main()
