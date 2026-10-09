"""Bounded v2 CLI review; reuse frozen v1 scalar proof and keep writes in /tmp."""
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
    "inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
    "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
    "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a",
    "calculate-v2.py": "cafd8b00756e7cf5177fb8722f6139883d4c40aa28a7a08bf9d988575aa770f0",
    "result-v2.json": "2a70abd309932e497daeb0bebf152439077f776a28823d910d50c35c71c24f42",
    "independent-review-v1/testing/review.py": "0721033e0ba96c007820998333ca06ea26a9bfac8cc86eda8377ed93c74c7902",
    "independent-review-v1/testing/receipt.json": "444b375c4e9fbaf6e39ead0219c5d81b4340f41c2819b9ae26f132c7f10d3eee",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load():
    spec = importlib.util.spec_from_file_location("hardware_v2_testing", TARGET / "calculate-v2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wrapper_controls(module, original):
    observed = {}
    original_sha = module.sha

    def bad_original(path):
        return "0" * 64 if path == TARGET / "result.json" else original_sha(path)

    with patch.object(module, "sha", bad_original), patch.object(module.runpy, "run_path") as runner:
        try:
            module.evaluate()
        except ValueError as error:
            observed["changed_original_hash"] = str(error)
        else:
            raise AssertionError("original hash corruption accepted")
        assert not runner.called
    mutated = copy.deepcopy(original)
    mutated["current_axes_stay_Z_mm"] = 180.
    with patch.object(module.runpy, "run_path", return_value={"evaluate": lambda: mutated}):
        try:
            module.evaluate()
        except ValueError as error:
            observed["changed_original_result"] = str(error)
        else:
            raise AssertionError("changed numerical result accepted")
    own_calls = 0

    def changed_during_evaluation(path):
        nonlocal own_calls
        if path == module.OWN:
            own_calls += 1
            if own_calls > 1:
                return "0" * 64
        return original_sha(path)

    with patch.object(module, "sha", changed_during_evaluation):
        try:
            module.evaluate()
        except ValueError as error:
            observed["changed_pin_during_wrapper"] = str(error)
        else:
            raise AssertionError("post-calculation source change accepted")
    return observed


def actual_cli(directory, result):
    mirror = directory / "mirror"
    packet = mirror / TARGET.relative_to(ROOT)
    packet.mkdir(parents=True)
    for name in ("calculate-v2.py", "calculate.py", "inputs.json", "result.json"):
        shutil.copyfile(TARGET / name, packet / name)
    for relative, expected in result["source_sha256"].items():
        path = mirror / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(ROOT / relative)
        assert sha(path) == expected
    command = [sys.executable, "-B", str(packet / "calculate-v2.py"), "--out"]

    def run(path):
        return subprocess.run([*command, str(path)], text=True, capture_output=True, check=False, timeout=30)

    output = packet / "replay.json"
    replay = run(output)
    assert replay.returncode == 0, replay.stderr
    assert read(output) == result
    assert json.loads(replay.stdout)["sha256"] == sha(output)
    alias = mirror / "owned-parent-alias"
    alias.symlink_to(packet, target_is_directory=True)
    assert run(alias / "stable-parent.json").returncode == 0
    assert read(packet / "stable-parent.json") == result
    absent_inside, absent_outside = packet / "missing-target.json", mirror / "missing-outside.json"
    dangling, outside_link = packet / "dangling.json", packet / "outside-link.json"
    dangling.symlink_to(absent_inside)
    outside_link.symlink_to(absent_outside)
    existing_link = packet / "existing-target-link.json"
    existing_link.symlink_to(output)
    directory_leaf = packet / "directory.json"
    directory_leaf.mkdir()
    protected = {packet / name: sha(packet / name)
                 for name in ("calculate-v2.py", "calculate.py", "inputs.json", "result.json", "replay.json")}
    negatives = {}
    cases = {"occupied_regular": output, "input_alias": packet / "inputs.json",
             "dangling_leaf_inside": dangling, "dangling_leaf_outside": outside_link,
             "existing_target_leaf": existing_link, "directory_leaf": directory_leaf,
             "outside_parent": mirror / "outside.json", "wrong_suffix": packet / "wrong.txt"}
    for mode, path in cases.items():
        rejected = run(path)
        assert rejected.returncode != 0, mode
        assert all(sha(p) == digest for p, digest in protected.items())
        assert not absent_inside.exists() and not absent_outside.exists()
        negatives[mode] = "rejected; protected entries unchanged"
    contended = packet / "contended.json"
    processes = [subprocess.Popen([*command, str(contended)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                 for _ in range(2)]
    for process in processes:
        process.communicate(timeout=30)
    assert sorted(p.returncode for p in processes) == [0, 1]
    assert read(contended) == result
    return {"full_frozen_v2_JSON_reproduced": True, "stable_parent_alias_reproduced": True,
            "negative_output_controls": negatives, "two_normal_writers_returncodes": [0, 1]}


def entry_races(module, directory):
    root = directory / "injected"
    root.mkdir()
    owner, outside = root / "owned", root / "outside"
    owner.mkdir()
    outside.mkdir()
    observed = {}
    sentinel = {"source_pin_count": 29, "private_stub": True}
    for mode in ("regular_leaf", "dangling_leaf"):
        requested, missing = owner / f"{mode}.json", owner / f"{mode}-target.json"
        callbacks = []

        def inject(callbacks=callbacks, mode=mode, requested=requested, missing=missing):
            callbacks.append(True)
            if mode == "regular_leaf":
                requested.write_text("occupied sentinel")
            else:
                requested.symlink_to(missing)
            return sentinel

        with patch.object(module, "HERE", owner), patch.object(module, "ROOT", root), \
                patch.object(module, "evaluate", inject), patch.object(sys, "argv", ["review", "--out", str(requested)]):
            try:
                module.main()
            except FileExistsError:
                assert callbacks == [True]
            else:
                raise AssertionError("newly occupied leaf accepted: " + mode)
        assert not missing.exists()
        assert requested.is_symlink() if mode == "dangling_leaf" else requested.read_text() == "occupied sentinel"
        observed[mode] = "exclusive open rejected injected entry; target/bytes preserved"

    # The accepted parent alias can change after ownership validation. This is
    # a boundary control of the actual main(), with only evaluation stubbed.
    alias = root / "parent-alias"
    alias.symlink_to(owner, target_is_directory=True)
    requested = alias / "redirected.json"

    def redirect_parent():
        alias.unlink()
        alias.symlink_to(outside, target_is_directory=True)
        return sentinel

    stdout = io.StringIO()
    with patch.object(module, "HERE", owner), patch.object(module, "ROOT", root), \
            patch.object(module, "evaluate", redirect_parent), \
            patch.object(sys, "argv", ["review", "--out", str(requested)]), contextlib.redirect_stdout(stdout):
        module.main()
    assert not (owner / requested.name).exists()
    assert read(outside / requested.name) == sentinel
    assert json.loads(stdout.getvalue())["out"] == "owned/redirected.json"
    observed["parent_alias_retarget"] = {"succeeded": True, "outside_owned_packet_created": True,
                                         "reported_owned_path_does_not_exist": True}
    return observed


def main():
    original, result, inp = read(TARGET / "result.json"), read(TARGET / "result-v2.json"), read(TARGET / "inputs.json")
    frozen = read(ROOT / inp["sources"]["frozen_receiver_packet"]["path"])
    old_reviews = {str(p.relative_to(ROOT)): sha(p) for p in (TARGET / "independent-review-v1").rglob("*")
                   if p.is_file()}

    def unchanged():
        assert all(sha(TARGET / name) == digest for name, digest in EXPECTED.items())
        assert all(sha(ROOT / path) == digest for path, digest in result["source_sha256"].items())
        assert all(sha(ROOT / row["path"]) == row["sha256"]
                   for row in frozen["final_files"] + frozen["retained_development_files"])
        assert all(sha(ROOT / path) == digest for path, digest in old_reviews.items())

    unchanged()
    changes = {"source_pin_count", "source_sha256", "execution", "reproduction_command", "output_guard_revision"}
    assert {k for k in original.keys() | result.keys() if original.get(k) != result.get(k)} == changes
    assert result["source_pin_count"] == len(result["source_sha256"]) == 29
    expected_pins = dict(original["source_sha256"])
    expected_pins.update({str((TARGET / name).relative_to(ROOT)): EXPECTED[name]
                          for name in ("result.json", "calculate-v2.py")})
    assert result["source_sha256"] == expected_pins
    assert result["execution"] == {**original["execution"], "output_wrapper": str((TARGET / "calculate-v2.py").relative_to(ROOT))}
    assert result["reproduction_command"] == (f"uv run python -B {TARGET.relative_to(ROOT)}/calculate-v2.py --out "
                                                f"{TARGET.relative_to(ROOT)}/reproduction-v2-01.json")
    module = load()
    assert module.evaluate() == result
    guards = wrapper_controls(module, original)
    with tempfile.TemporaryDirectory(prefix="hardware-v2-testing-") as scratch:
        cli = actual_cli(Path(scratch), result)
        races = entry_races(module, Path(scratch))
    unchanged()
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    finding = {"priority": "P2", "path": str((TARGET / "calculate-v2.py").relative_to(ROOT)), "line": 73,
               "title": "Keep exclusive output creation inside the parent whose ownership was validated",
               "impact": "An accepted symlink parent can be retargeted after line 67 validates its resolved ownership. Line 73 then creates the fresh output outside HERE, while the success receipt reports the absent HERE/name path. The leaf-entry fix works, but this regresses canonical-parent protection from the original CLI.",
               "reproduction": "Private stdlib control invokes the frozen main() with only evaluate stubbed: parent-alias initially points at owned HERE; evaluate switches it to an outside directory; main succeeds and writes outside/redirected.json while reporting owned/redirected.json.",
               "fix": "Preserve both frozen versions. In a new wrapper, validate requested.parent, then check/open canonical HERE / requested.name exclusively, preserving the requested leaf name and rejecting occupied leaf entries. Bind a directory descriptor instead if protection against replacement of HERE itself is required. Add this parent-alias regression."}
    report = {"schema": "eoere_four_cleat_post_hardware_independent_testing_review/v2",
              "status": "LEAF_ENTRY_FIX_PASSES_PARENT_ALIAS_RACE_REVISION_REQUIRED",
              "confirmed_substantial_findings": [finding],
              "source_sha256": {str((TARGET / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()},
              "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
              "frozen_source_pin_count_before_after": 29, "receiver_final_and_development_files_unchanged": 10,
              "old_v1_review_files_unchanged": old_reviews, "evaluate_matches_recorded_v2_result": True,
              "all_v1_numerical_hardware_limits_and_release_findings_exact": True,
              "reused_v1_independent_math_proof": {"receipt_sha256": EXPECTED["independent-review-v1/testing/receipt.json"],
                                                  "decimal_box_corners": 256, "station_comparisons": 8,
                                                  "semantic_corruptions": 12, "rerun": False},
              "exact_pin_expansion_and_v2_reproduction_command": True, "wrapper_corruption_controls": guards,
              "temporary_actual_CLI_checks": cli, "injected_after_guard_controls": races,
              "release": inp["release"], "limits": inp["limits"],
              "execution": {"stdlib_source_and_stub_only": True, "CAD_native_global_field_or_bulk_execution": False,
                            "shared_documents_index_staging_or_commit_changes": False},
              "retention": "Keep this compact review active; temporary mirrors and race controls were removed. All original packets, both hardware versions and v1 reviews remain frozen. No capacity, geometry, tool or hardware adoption follows."}
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": 1}, sort_keys=True))


if __name__ == "__main__":
    main()
