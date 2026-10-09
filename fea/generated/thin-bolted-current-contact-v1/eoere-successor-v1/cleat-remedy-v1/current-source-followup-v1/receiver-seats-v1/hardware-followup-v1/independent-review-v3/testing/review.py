"""Source-only final CLI review with private alias/leaf controls; reuse v1 math."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
TARGET = OWN.parents[2]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "calculate-v3.py": "352167060aa4baacfe2f460670d0a28a8638a173f312b9887e24cf5babb12f2c",
    "result-v3.json": "16962d3d5bc897336c37ac5da945e08bd0268604c1f0fc640127786dd5d97781",
    "independent-review-v1/testing/review.py": "0721033e0ba96c007820998333ca06ea26a9bfac8cc86eda8377ed93c74c7902",
    "independent-review-v1/testing/receipt.json": "444b375c4e9fbaf6e39ead0219c5d81b4340f41c2819b9ae26f132c7f10d3eee",
    "independent-review-v2/testing/review.py": "774882ca2b07c60fcbecd8a8866f3609e7f9c86633cc70f97c6fecfee510fccf",
    "independent-review-v2/testing/receipt.json": "0f0e0aae9c587f40121b6f8d2b42bf8996a5be678e04c24f4cbb166ffc3a0d78",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load():
    spec = importlib.util.spec_from_file_location("hardware_v3_testing", TARGET / "calculate-v3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wrapper_guards(module, previous):
    failures = {}
    original_sha = module.sha
    mutated = copy.deepcopy(previous)
    mutated["current_axes_stay_Z_mm"] = 180.
    for mode in ("changed_previous_hash", "changed_previous_result", "changed_own_pin_after_evaluation"):
        calls = []

        def controlled_sha(path, mode=mode, calls=calls):
            if mode == "changed_previous_hash" and path == TARGET / "result-v2.json":
                return "0" * 64
            if mode == "changed_own_pin_after_evaluation" and path == module.OWN:
                calls.append(True)
                if len(calls) > 1:
                    return "0" * 64
            return original_sha(path)

        context = patch.object(module.runpy, "run_path", return_value={"evaluate": lambda: mutated}) \
            if mode == "changed_previous_result" else contextlib.nullcontext()
        with patch.object(module, "sha", controlled_sha), context:
            try:
                module.evaluate()
            except ValueError as error:
                failures[mode] = str(error)
            else:
                raise AssertionError("wrapper corruption accepted: " + mode)
    return failures


def actual_cli(scratch, result):
    mirror = scratch / "mirror"
    packet = mirror / TARGET.relative_to(ROOT)
    packet.mkdir(parents=True)
    for name in ("calculate.py", "inputs.json", "result.json", "calculate-v2.py", "result-v2.json", "calculate-v3.py"):
        shutil.copyfile(TARGET / name, packet / name)
    for relative, expected in result["source_sha256"].items():
        path = mirror / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(ROOT / relative)
        assert sha(path) == expected
    command = [sys.executable, "-B", str(packet / "calculate-v3.py"), "--out"]

    def run(path):
        return subprocess.run([*command, str(path)], capture_output=True, text=True, check=False, timeout=30)

    output = packet / "replay.json"
    replay = run(output)
    assert replay.returncode == 0, replay.stderr
    assert read(output) == result
    assert json.loads(replay.stdout)["sha256"] == sha(output)
    alias = mirror / "alias"
    alias.symlink_to(packet, target_is_directory=True)
    assert run(alias / "stable-alias.json").returncode == 0
    assert read(packet / "stable-alias.json") == result
    missing_inside, missing_outside = packet / "absent.json", mirror / "absent.json"
    for name, target in (("dangling-inside.json", missing_inside), ("dangling-outside.json", missing_outside),
                         ("existing-alias.json", output)):
        (packet / name).symlink_to(target)
    (packet / "directory.json").mkdir()
    protected = {p: sha(p) for p in packet.iterdir() if p.is_file()}
    rejected = []
    for name, path in {"occupied": output, "input": packet / "inputs.json",
                       "dangling_inside": alias / "dangling-inside.json", "dangling_outside": packet / "dangling-outside.json",
                       "existing_alias": alias / "existing-alias.json", "directory": packet / "directory.json",
                       "outside": mirror / "outside.json", "suffix": packet / "bad.txt"}.items():
        assert run(path).returncode != 0, name
        assert all(sha(p) == digest for p, digest in protected.items())
        assert not missing_inside.exists() and not missing_outside.exists()
        rejected.append(name)
    contended = packet / "contended.json"
    writers = [subprocess.Popen([*command, str(contended)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    for writer in writers:
        writer.communicate(timeout=30)
    assert sorted(p.returncode for p in writers) == [0, 1] and read(contended) == result
    return {"byte_identical_frozen_v3_reproduced_full_JSON": True, "stable_parent_alias_reproduced": True,
            "negative_outputs_rejected_and_preserved": rejected, "two_writers_returncodes": [0, 1]}


def alias_and_leaf_controls(module, scratch):
    observed = {}
    for mode in ("retarget_parent", "remove_parent_alias", "injected_regular_leaf", "injected_dangling_leaf", "retarget_and_inject_leaf"):
        root = scratch / mode
        owner, outside = root / "owned", root / "outside"
        owner.mkdir(parents=True)
        outside.mkdir()
        alias = root / "alias"
        alias.symlink_to(owner, target_is_directory=True)
        requested, destination = alias / "output.json", owner / "output.json"
        missing = owner / "absent.json"
        callbacks = []
        sentinel = {"source_pin_count": 31, "private_stub": True}

        def evaluate(mode=mode, alias=alias, outside=outside, destination=destination, missing=missing,
                     callbacks=callbacks, sentinel=sentinel):
            callbacks.append(True)
            if mode in {"retarget_parent", "retarget_and_inject_leaf", "remove_parent_alias"}:
                alias.unlink()
                if mode != "remove_parent_alias":
                    alias.symlink_to(outside, target_is_directory=True)
            if mode == "injected_regular_leaf":
                destination.write_text("occupied sentinel")
            elif mode in {"injected_dangling_leaf", "retarget_and_inject_leaf"}:
                destination.symlink_to(missing)
            return sentinel

        stdout = io.StringIO()
        with patch.object(module, "HERE", owner), patch.object(module, "ROOT", root), \
                patch.object(module, "evaluate", evaluate), patch.object(sys, "argv", ["review", "--out", str(requested)]), \
                contextlib.redirect_stdout(stdout):
            if mode in {"retarget_parent", "remove_parent_alias"}:
                module.main()
                assert read(destination) == sentinel
                response = json.loads(stdout.getvalue())
                assert response["out"] == "owned/output.json" and response["sha256"] == sha(destination)
                observed[mode] = "created only canonical owned output; stdout path/hash truthful"
            else:
                try:
                    module.main()
                except FileExistsError:
                    assert not stdout.getvalue()
                else:
                    raise AssertionError("injected occupied leaf accepted: " + mode)
                assert destination.is_symlink() if mode != "injected_regular_leaf" else destination.read_text() == "occupied sentinel"
                observed[mode] = "exclusive creation rejected; injected entry preserved"
        assert callbacks == [True] and not (outside / "output.json").exists() and not missing.exists()
    return observed


def main():
    original, previous, result = (read(TARGET / name) for name in ("result.json", "result-v2.json", "result-v3.json"))
    inp = read(TARGET / "inputs.json")
    frozen = read(ROOT / inp["sources"]["frozen_receiver_packet"]["path"])
    old_reviews = {str(p.relative_to(ROOT)): sha(p) for version in (1, 2)
                   for p in (TARGET / f"independent-review-v{version}").rglob("*") if p.is_file()}

    def unchanged():
        assert all(sha(TARGET / name) == digest for name, digest in EXPECTED.items())
        assert all(sha(ROOT / path) == digest for path, digest in result["source_sha256"].items())
        assert all(sha(ROOT / row["path"]) == row["sha256"]
                   for row in frozen["final_files"] + frozen["retained_development_files"])
        assert all(sha(ROOT / path) == digest for path, digest in old_reviews.items())

    unchanged()
    permitted = {"source_pin_count", "source_sha256", "execution", "reproduction_command", "output_guard_revision"}
    for earlier in (original, previous):
        assert {k for k in earlier.keys() | result.keys() if earlier.get(k) != result.get(k)} == permitted
    expected_pins = {**previous["source_sha256"], str((TARGET / "result-v2.json").relative_to(ROOT)): sha(TARGET / "result-v2.json"),
                     str((TARGET / "calculate-v3.py").relative_to(ROOT)): EXPECTED["calculate-v3.py"]}
    assert result["source_sha256"] == expected_pins and result["source_pin_count"] == len(expected_pins) == 31
    assert result["execution"] == {**previous["execution"], "output_wrapper": str((TARGET / "calculate-v3.py").relative_to(ROOT))}
    assert result["reproduction_command"] == (f"uv run python -B {TARGET.relative_to(ROOT)}/calculate-v3.py --out "
                                                f"{TARGET.relative_to(ROOT)}/reproduction-v3-01.json")
    module = load()
    assert module.evaluate() == result
    guards = wrapper_guards(module, previous)
    with tempfile.TemporaryDirectory(prefix="hardware-v3-testing-") as directory:
        cli = actual_cli(Path(directory), result)
        races = alias_and_leaf_controls(module, Path(directory))
    unchanged()
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    report = {"schema": "eoere_four_cleat_post_hardware_independent_testing_review/v3", "status": "PASS_WITHIN_SOURCE_ONLY_SCOPE",
              "confirmed_substantial_findings": [], "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
              "target_and_reused_review_sha256": {str((TARGET / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()},
              "source_pins_unchanged_before_after": 31, "receiver_final_and_development_files_unchanged": 10,
              "all_v1_v2_reviews_unchanged": old_reviews, "exact_recorded_v3_evaluation": True,
              "all_original_numerical_hardware_limits_and_release_findings_exact": True,
              "reused_frozen_v1_math_proof": {"decimal_corners": 256, "station_comparisons": 8, "semantic_corruptions": 12, "rerun": False},
              "exact_pin_expansion_and_reproduction_command": True, "wrapper_corruptions_rejected": guards,
              "actual_temporary_CLI_checks": cli, "injected_after_validation_controls": races,
              "both_prior_output_guard_findings_remediated_in_v3": True, "release": inp["release"], "limits": inp["limits"],
              "execution": {"stdlib_source_and_stub_only": True, "CAD_native_global_field_or_bulk_execution": False,
                            "shared_documents_index_staging_or_commit_changes": False},
              "retention": "Keep compact v3 review active alongside frozen v1/v2 findings. Private source-linked mirrors and controls removed; no actual fit, tool access, hardware adoption, geometry or capacity acceptance follows."}
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
