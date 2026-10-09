"""Targeted actual-CLI controls for the three synthetic evidence review findings."""

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())


def load(path):
    spec = importlib.util.spec_from_file_location("captured_synthetic_launcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(arguments):
    command = [sys.executable, "-B", *map(str, arguments)]
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, check=False
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def controlled(args):
    if args.kind in ("loaded_launcher", "loaded_body", "loaded_v1"):
        launcher = load(args.fixture / HERE.relative_to(ROOT) / "run.py")
        if args.kind == "loaded_launcher":
            target = Path(launcher.__file__)
            target.write_bytes(
                b"raise RuntimeError('changed executable')\n" + target.read_bytes()
            )
            launcher.load_body()
        body = launcher.load_body()
        if args.kind == "loaded_body":
            target = Path(body.__file__)
            target.write_bytes(
                b"raise RuntimeError('changed executable')\n" + target.read_bytes()
            )
            sys.argv = [str(HERE / "run.py"), "produce", "--out", str(args.out)]
            body.main()
        legacy = body.prepare()
        target = Path(legacy.__file__)
        target.write_bytes(
            b"raise RuntimeError('changed executable')\n" + target.read_bytes()
        )
        sys.argv = [str(HERE / "run.py"), "produce", "--out", str(args.out)]
        legacy.main()
    else:
        body = load(HERE / "run.py").load_body()
        legacy = body.prepare()
        encode = legacy.encoded

        def replacement(value):
            data = encode(value)
            if (
                type(value) is dict
                and value.get("schema") == "synthetic_limit_corrected_verification/v1"
            ):
                args.run.rename(args.run.with_name("preserved-original-run"))
                if args.kind == "serialized_symlink":
                    args.run.symlink_to(
                        args.replacement.resolve(), target_is_directory=True
                    )
                else:
                    args.replacement.rename(args.run)
            return data

        legacy.encoded = replacement
        sys.argv = [
            str(HERE / "run.py"),
            "verify",
            "--run",
            str(args.run),
            "--replay",
            str(args.replay),
            "--out",
            str(args.out),
        ]
        legacy.main()


def regress(output):
    output.mkdir(parents=True, exist_ok=False)
    launcher = load(HERE / "run.py")
    body = launcher.load_body()
    legacy = body.prepare()
    state = legacy.snapshot()
    commands = []
    run, replay = output / "fresh-run", output / "fresh-replay"
    for directory in (run, replay):
        record = cli([HERE / "run.py", "produce", "--out", directory])
        commands.append(record)
        body.need(record["returncode"] == 0, f"Fresh production failed: {record}")
    receipt = output / "clean-verification.json"
    record = cli(
        [HERE / "run.py", "verify", "--run", run, "--replay", replay, "--out", receipt]
    )
    commands.append(record)
    body.need(record["returncode"] == 0, f"Fresh verification failed: {record}")
    for name in ("result.json", "details.json", "run-provenance.json"):
        body.need(
            (run / name).read_bytes() == (replay / name).read_bytes(),
            "Fresh replay differs",
        )
    body.need(
        (run / "result.json").read_bytes()
        == (legacy.FROZEN / "result.json").read_bytes(),
        "Original numerical result changed",
    )
    original_details = (
        ROOT
        / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/attempt03/details.json"
    )
    original_details_sha = body.sha(original_details.read_bytes())
    body.need(
        body.sha((run / "details.json").read_bytes()) == original_details_sha,
        "Original bearing fields changed",
    )

    def copy_run(destination):
        destination.mkdir(parents=True)
        for name in ("result.json", "details.json", "run-provenance.json"):
            (destination / name).write_bytes((run / name).read_bytes())

    raw_cases = []
    for factor in (1_000_000.0, 1.001):
        label = f"coordinated-raw-factor-{factor}"
        altered = json.loads((run / "result.json").read_bytes())
        grid = altered["cases"][0]["grids"][0]
        grid["raw_LP_load_lbf"] *= factor
        grid["numerical_feasibility_scale"] /= factor
        encoded = legacy.encoded(altered)
        provenance = json.loads((run / "run-provenance.json").read_bytes())
        provenance["output_sha256"]["result.json"] = body.sha(encoded)
        bad_run, bad_replay = output / label / "run", output / label / "replay"
        for directory in (bad_run, bad_replay):
            copy_run(directory)
            (directory / "result.json").write_bytes(encoded)
            (directory / "run-provenance.json").write_bytes(legacy.encoded(provenance))
        target = output / label / "verification.json"
        record = cli(
            [
                HERE / "run.py",
                "verify",
                "--run",
                bad_run,
                "--replay",
                bad_replay,
                "--out",
                target,
            ]
        )
        commands.append(record)
        body.need(
            record["returncode"] != 0
            and "Numerical repair exceeds frozen" in record["stderr"]
            and not target.exists(),
            "Coordinated raw/scale forgery accepted",
        )
        raw_cases.append(
            {
                "factor": factor,
                "forged_raw_load_lbf": grid["raw_LP_load_lbf"],
                "preserved_scaled_load_lbf": grid["scaled_statics_load_lbf"],
            }
        )
    for kind in ("loaded_launcher", "loaded_body", "loaded_v1"):
        fixture = output / "load-fixtures" / kind
        fixture.mkdir(parents=True)
        (fixture / "current-candidate.json").write_bytes(
            (ROOT / "current-candidate.json").read_bytes()
        )
        for relative, data in state["contents"].items():
            target = fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        target = fixture / "rejected-run"
        record = cli(
            [
                HERE / "check.py",
                "controlled",
                "--kind",
                kind,
                "--fixture",
                fixture,
                "--out",
                target,
            ]
        )
        commands.append(record)
        body.need(
            record["returncode"] != 0
            and (
                "Loaded launcher source changed" in record["stderr"]
                or "Loaded executable/source changed" in record["stderr"]
            ),
            f"Loaded-source drift accepted: {record}",
        )
        body.need(
            not target.exists() or not any(target.iterdir()),
            "Loaded-source drift wrote output",
        )
    symlink_controls = []
    for kind in ("directory", "ancestor", "file"):
        place = output / "symlinks" / kind
        place.mkdir(parents=True)
        real = place / "real-run"
        copy_run(real)
        if kind == "file":
            supplied = place / "linked-run"
            supplied.mkdir()
            for name in ("result.json", "details.json", "run-provenance.json"):
                (supplied / name).symlink_to((real / name).resolve())
        elif kind == "ancestor":
            link = place / "linked-parent"
            link.symlink_to(place.resolve(), target_is_directory=True)
            supplied = link / "real-run"
        else:
            supplied = place / "linked-run"
            supplied.symlink_to(real.resolve(), target_is_directory=True)
        target = place / "verification.json"
        # Equals syntax must receive the same path checks as separated arguments.
        record = cli(
            [
                HERE / "run.py",
                "verify",
                f"--run={supplied}",
                "--replay",
                replay,
                "--out",
                target,
            ]
        )
        commands.append(record)
        body.need(
            record["returncode"] != 0
            and "Symlink evidence path:" in record["stderr"]
            and not target.exists(),
            "Symlink evidence accepted",
        )
        symlink_controls.append(kind)
    for kind in ("serialized_symlink", "serialized_directory"):
        place = output / kind
        active, other = place / "run", place / "replacement"
        copy_run(active)
        copy_run(other)
        target = place / "verification.json"
        record = cli(
            [
                HERE / "check.py",
                "controlled",
                "--kind",
                kind,
                "--run",
                active,
                "--replacement",
                other,
                "--replay",
                replay,
                "--out",
                target,
            ]
        )
        commands.append(record)
        body.need(
            record["returncode"] != 0
            and (
                "Symlink evidence path:" in record["stderr"]
                or "Lexical evidence identity changed:" in record["stderr"]
            )
            and not target.exists(),
            "Receipt-time path replacement accepted",
        )
    # Reuse the frozen v1 corruption generator to ensure previous claim checks stay active.
    spec = importlib.util.spec_from_file_location(
        "frozen_v1_regression_helpers", legacy.HERE / "check.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    previous = []
    for label in (
        "candidate_joint_capacity",
        "invented_analytic_load",
        "nonfinite_peak",
        "duplicate_case",
    ):
        altered = json.loads((run / "result.json").read_bytes())
        helper.forged_result(label, altered)
        data = (
            json.dumps(altered, sort_keys=True, indent=2, allow_nan=True) + "\n"
        ).encode()
        provenance = json.loads((run / "run-provenance.json").read_bytes())
        provenance["output_sha256"]["result.json"] = body.sha(data)
        provenance["validated_claims"] = {key: altered[key] for key in legacy.CLAIMS}
        bad_run, bad_replay = output / label / "run", output / label / "replay"
        for directory in (bad_run, bad_replay):
            copy_run(directory)
            (directory / "result.json").write_bytes(data)
            (directory / "run-provenance.json").write_bytes(legacy.encoded(provenance))
        target = output / label / "verification.json"
        record = cli(
            [
                HERE / "run.py",
                "verify",
                "--run",
                bad_run,
                "--replay",
                bad_replay,
                "--out",
                target,
            ]
        )
        commands.append(record)
        body.need(
            record["returncode"] != 0 and not target.exists(),
            "Previous compact check regressed",
        )
        previous.append(label)
    legacy.unchanged(state["pins"])
    body.need(
        body.sha(original_details.read_bytes()) == original_details_sha,
        "Original raw fields changed",
    )
    clean = json.loads(receipt.read_bytes())
    result = {
        "schema": "synthetic_limit_evidence_review_fix_regressions/v2",
        "status": "ALL_TARGETED_REGRESSIONS_PASS",
        "source_sha256": state["pins"],
        "raw_load_scale_corruptions_rejected": raw_cases,
        "loaded_source_drifts_rejected": ["launcher", "body", "v1_correction"],
        "symlink_evidence_rejected": symlink_controls,
        "receipt_time_path_replacements_rejected": [
            "symlink",
            "ordinary_directory_with_identical_bytes",
        ],
        "previous_compact_controls_rejected": previous,
        "three_file_byte_identical_fresh_replay": True,
        "result_and_fields_match_original_issued_bytes": True,
        "validated_claims": clean["validated_claims"],
        "independent_checks": clean["independent_checks"],
        "commands": commands,
    }
    legacy.new_file(output / "regressions.json", legacy.encoded(result))
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_count": len(state["pins"]),
                "negative_controls": len(commands) - 3,
            },
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("regress").add_argument("--out", type=Path, required=True)
    control = sub.add_parser("controlled")
    control.add_argument(
        "--kind",
        choices=(
            "loaded_launcher",
            "loaded_body",
            "loaded_v1",
            "serialized_symlink",
            "serialized_directory",
        ),
        required=True,
    )
    for name in ("fixture", "run", "replay", "replacement"):
        control.add_argument("--" + name, type=Path)
    control.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    controlled(args) if args.command == "controlled" else regress(args.out)


if __name__ == "__main__":
    main()
