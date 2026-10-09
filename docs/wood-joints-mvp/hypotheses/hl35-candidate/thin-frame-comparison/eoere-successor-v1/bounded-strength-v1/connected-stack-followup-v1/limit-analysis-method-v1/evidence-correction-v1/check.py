"""Real CLI regressions for the synthetic evidence correction, using owned fixtures."""

import argparse
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
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


def drift(args):
    """Exercise the real correction main in a separate, copied-source process."""
    correction = load(
        args.fixture / HERE.relative_to(ROOT) / "correction.py", "drift_correction"
    )
    if args.kind == "serialized_input":
        encode = correction.encoded

        def changed_encoding(value):
            data = encode(value)
            if (
                type(value) is dict
                and value.get("schema") == "synthetic_limit_guarded_production/v1"
            ):
                target = correction.FROZEN / "inputs.json"
                target.write_bytes(target.read_bytes() + b"\n")
            return data

        correction.encoded = changed_encoding
    else:
        original_load = correction.load_original

        def changed_load(state, filename):
            module = original_load(state, filename)
            if filename == "analyze.py":
                run = module.run

                def changed_run(inputs):
                    target = {
                        "input": correction.FROZEN / "inputs.json",
                        "analyzer": correction.FROZEN / "analyze.py",
                        "checker": correction.FROZEN / "verify.py",
                        "correction": correction.HERE / "correction.py",
                    }[args.kind]
                    if args.kind == "input":
                        value = json.loads(target.read_bytes())
                        value["published_cases"][0]["main_bearing_lb_in"] *= 1.1
                        target.write_bytes(correction.encoded(value))
                    else:
                        target.write_bytes(
                            target.read_bytes() + b"\n# isolated drift regression\n"
                        )
                    return run(inputs)

                module.run = changed_run
            return module

        correction.load_original = changed_load
    sys.argv = [
        str(correction.HERE / "correction.py"),
        "produce",
        "--out",
        str(args.out),
    ]
    correction.main()


def forged_result(label, value):
    if label in ("candidate_inputs_used", "capacity_or_pass_claim"):
        value[label] = True
    elif label == "candidate_joint_capacity":
        value[label] = 12345.0
    elif label == "schema":
        value[label] = "physical_capacity/v1"
    elif label == "disposition":
        value[label] = "accepted_for_climbing"
    elif label == "invented_mode":
        value["cases"][0]["raw_governing_mode"] = "invented"
    elif label == "invented_analytic_load":
        value["cases"][0]["analytic_raw_yield_lbf"] = 1e99
    elif label == "invented_mode_equation":
        value["cases"][0]["analytic_all_raw_modes_lbf"]["IV"] *= 2
    elif label == "invented_published_reference":
        value["cases"][0]["published_reference_max_rounding_error_lbf"] = 1e99
    elif label == "nonfinite_peak":
        value["cases"][0]["grids"][0]["maximum_exact_moment_lb_in"] = float("nan")
    elif label == "nonfinite_summary":
        value["summary"]["maximum_scaled_LP_certificate_residual"] = float("inf")
    elif label == "duplicate_case":
        value["cases"].append(copy.deepcopy(value["cases"][0]))
    elif label == "missing_case":
        value["cases"].pop()
    elif label == "duplicate_grid":
        value["cases"][0]["grids"].append(copy.deepcopy(value["cases"][0]["grids"][0]))
    elif label == "missing_grid":
        value["cases"][0]["grids"].pop()
    elif label == "invented_summary_census":
        value["summary"]["LP_benchmark_count"] = 100
    elif label == "invented_summary_modes":
        value["summary"]["governing_modes_verified"].append("invented")
    elif label == "changed_source_closure":
        value["source_pins"].pop()
    elif label == "changed_claim_limits":
        value["claim_limits"].append("candidate strength accepted")
    elif label == "wrong_scaled_load":
        value["cases"][0]["grids"][0]["raw_LP_load_lbf"] *= 2
    elif label == "negative_certificate":
        value["cases"][0]["grids"][0]["scaled_LP_certificate"]["equality_residual"] = -1
    elif label == "unknown_compact_claim":
        value["fabrication_release"] = True
    elif label != "duplicate_JSON_key":
        raise ValueError(label)


def regression(output):
    output.mkdir(parents=True, exist_ok=False)
    correction = load(HERE / "correction.py", "corrected_synthetic_evidence")
    state = correction.snapshot()
    commands = []
    run, replay = output / "fresh-run", output / "fresh-replay"
    for directory in (run, replay):
        result = cli([HERE / "correction.py", "produce", "--out", directory])
        commands.append(result)
        correction.need(result["returncode"] == 0, f"Fresh production failed: {result}")
    valid = cli(
        [
            HERE / "correction.py",
            "verify",
            "--run",
            run,
            "--replay",
            replay,
            "--out",
            output / "clean-verification.json",
        ]
    )
    commands.append(valid)
    correction.need(valid["returncode"] == 0, f"Clean verification failed: {valid}")
    for name in ("result.json", "details.json", "run-provenance.json"):
        correction.need(
            (run / name).read_bytes() == (replay / name).read_bytes(),
            "Fresh replay differs",
        )
    original_result = state["contents"][
        str((correction.FROZEN / "result.json").relative_to(ROOT))
    ]
    original_raw = (
        ROOT
        / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1/attempt03/details.json"
    )
    original_raw_sha = correction.digest(original_raw.read_bytes())
    correction.need(
        (run / "result.json").read_bytes() == original_result,
        "Numerical result changed",
    )
    correction.need(
        correction.digest((run / "details.json").read_bytes()) == original_raw_sha,
        "Numerical fields changed",
    )
    guard_file = output / "existing-file"
    guard_file.write_bytes(b"preserved output fixture\n")
    guard_link = output / "dangling-output"
    guard_link.symlink_to(output / "absent-target")
    guard_directory_link = output / "directory-output-link"
    guard_directory_link.symlink_to(run.resolve(), target_is_directory=True)
    for path in (run, guard_file, guard_link, guard_directory_link):
        rejected = cli([HERE / "correction.py", "produce", "--out", path])
        commands.append(rejected)
        correction.need(rejected["returncode"] != 0, "Existing output accepted")
    rejected = cli(
        [
            HERE / "correction.py",
            "verify",
            "--run",
            run,
            "--replay",
            replay,
            "--out",
            output / "clean-verification.json",
        ]
    )
    commands.append(rejected)
    correction.need(rejected["returncode"] != 0, "Existing verification overwritten")
    correction.need(
        guard_file.read_bytes() == b"preserved output fixture\n"
        and guard_link.is_symlink()
        and not (output / "absent-target").exists(),
        "Guard changed a fixture",
    )
    base_result = json.loads((run / "result.json").read_bytes())
    base_provenance = json.loads((run / "run-provenance.json").read_bytes())
    corruptions = [
        "candidate_inputs_used",
        "capacity_or_pass_claim",
        "candidate_joint_capacity",
        "schema",
        "disposition",
        "invented_mode",
        "invented_analytic_load",
        "invented_mode_equation",
        "invented_published_reference",
        "nonfinite_peak",
        "nonfinite_summary",
        "duplicate_case",
        "missing_case",
        "duplicate_grid",
        "missing_grid",
        "invented_summary_census",
        "invented_summary_modes",
        "changed_source_closure",
        "changed_claim_limits",
        "wrong_scaled_load",
        "negative_certificate",
        "unknown_compact_claim",
        "duplicate_JSON_key",
    ]
    for label in corruptions:
        value = copy.deepcopy(base_result)
        forged_result(label, value)
        data = (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=True) + "\n"
        ).encode()
        if label == "duplicate_JSON_key":
            data = b'{"candidate_inputs_used":true,' + data[1:]
        provenance = copy.deepcopy(base_provenance)
        provenance["output_sha256"]["result.json"] = correction.digest(data)
        provenance["validated_claims"] = {key: value[key] for key in correction.CLAIMS}
        bad_run, bad_replay = output / label / "run", output / label / "replay"
        for directory in (bad_run, bad_replay):
            directory.mkdir(parents=True)
            (directory / "result.json").write_bytes(data)
            (directory / "details.json").write_bytes(
                (run / "details.json").read_bytes()
            )
            (directory / "run-provenance.json").write_bytes(
                correction.encoded(provenance)
            )
        receipt = output / label / "verification.json"
        rejected = cli(
            [
                HERE / "correction.py",
                "verify",
                "--run",
                bad_run,
                "--replay",
                bad_replay,
                "--out",
                receipt,
            ]
        )
        commands.append(rejected)
        correction.need(
            rejected["returncode"] != 0 and not receipt.exists(),
            f"Forged evidence accepted: {label}",
        )
    drift_types = ("input", "analyzer", "checker", "correction", "serialized_input")
    for kind in drift_types:
        fixture = output / "drift-fixtures" / kind
        fixture.mkdir(parents=True)
        (fixture / "current-candidate.json").write_bytes(
            (ROOT / "current-candidate.json").read_bytes()
        )
        for relative, data in state["contents"].items():
            destination = fixture / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        destination = fixture / "rejected-run"
        rejected = cli(
            [
                HERE / "check.py",
                "drift",
                "--fixture",
                fixture,
                "--kind",
                kind,
                "--out",
                destination,
            ]
        )
        commands.append(rejected)
        correction.need(
            rejected["returncode"] != 0
            and "Source/evidence drift:" in rejected["stderr"],
            f"Drift not detected: {kind}: {rejected}",
        )
        correction.need(
            destination.is_dir() and not any(destination.iterdir()),
            "Drift published output",
        )
    # Real verification must also reject evidence changed after consuming it.
    encoded = correction.encoded
    evidence_fixture = output / "evidence-drift"
    for label, directory in (("run", run), ("replay", replay)):
        target = evidence_fixture / label
        target.mkdir(parents=True)
        for name in ("result.json", "details.json", "run-provenance.json"):
            (target / name).write_bytes((directory / name).read_bytes())

    def changing_receipt(value):
        data = encoded(value)
        if (
            type(value) is dict
            and value.get("schema") == "synthetic_limit_corrected_verification/v1"
        ):
            path = evidence_fixture / "run/result.json"
            path.write_bytes(path.read_bytes() + b"\n")
        return data

    correction.encoded = changing_receipt
    try:
        correction.verify(
            evidence_fixture / "run",
            evidence_fixture / "replay",
            evidence_fixture / "verification.json",
        )
    except ValueError as error:
        correction.need(
            "Run/replay evidence drift" in str(error), "Wrong evidence drift rejection"
        )
    else:
        raise ValueError("Changed evidence accepted")
    finally:
        correction.encoded = encoded
    correction.need(
        not (evidence_fixture / "verification.json").exists(),
        "Evidence drift published receipt",
    )
    correction.unchanged(state["pins"])
    correction.need(
        correction.digest(original_raw.read_bytes()) == original_raw_sha,
        "Original raw evidence changed",
    )
    receipt = {
        "schema": "synthetic_limit_evidence_correction_regressions/v1",
        "status": "ALL_BOUNDED_REGRESSIONS_PASS",
        "source_sha256": state["pins"],
        "real_CLI_corruptions_rejected": corruptions,
        "real_CLI_source_drift_rejected_before_any_output": list(drift_types),
        "post_serialization_evidence_drift_rejected": True,
        "fresh_result_details_match_issued_bytes": True,
        "fresh_three_file_replay_byte_identical": True,
        "output_guard_cases": [
            "directory",
            "file",
            "dangling_symlink",
            "directory_symlink",
            "existing_verification",
        ],
        "clean_verification_sha256": correction.digest(
            (output / "clean-verification.json").read_bytes()
        ),
        "commands": commands,
        "validated_claims": json.loads(
            (output / "clean-verification.json").read_bytes()
        )["validated_claims"],
        "candidate_actions_or_geometry_used": False,
    }
    correction.new_file(output / "regressions.json", correction.encoded(receipt))
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "corruptions": len(corruptions),
                "source_drifts": len(drift_types),
            },
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("regress").add_argument("--out", type=Path, required=True)
    controlled = sub.add_parser("drift")
    controlled.add_argument("--fixture", type=Path, required=True)
    controlled.add_argument(
        "--kind",
        choices=("input", "analyzer", "checker", "correction", "serialized_input"),
        required=True,
    )
    controlled.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    drift(args) if args.command == "drift" else regression(args.out)


if __name__ == "__main__":
    main()
