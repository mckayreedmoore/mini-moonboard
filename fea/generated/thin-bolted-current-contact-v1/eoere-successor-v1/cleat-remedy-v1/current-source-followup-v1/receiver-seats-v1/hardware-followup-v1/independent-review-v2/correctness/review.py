"""Review only hardware wrapper composition; reuse frozen v1 arithmetic proof."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import runpy
import sys
import tempfile
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
PACKET = HERE.parents[1]
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
FROZEN = {
    "inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
    "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
    "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a",
    "calculate-v2.py": "cafd8b00756e7cf5177fb8722f6139883d4c40aa28a7a08bf9d988575aa770f0",
    "result-v2.json": "2a70abd309932e497daeb0bebf152439077f776a28823d910d50c35c71c24f42",
    "independent-review-v1/correctness/review.py": "de63a82747c218c372a5f1d1f6cd969148331cac7d8e929bcc5692f92819dd2c",
    "independent-review-v1/correctness/receipt.json": "33b5a465b5ec7e5c3e113995f6762e719f8a5fbc27225bf4ea71f1078b6ca652",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def review():
    for name, digest in FROZEN.items():
        assert sha(PACKET / name) == digest, name
    base, saved = read(PACKET / "result.json"), read(PACKET / "result-v2.json")
    proof = read(PACKET / "independent-review-v1/correctness/receipt.json")
    assert proof["findings"] == [] and proof["box_corner_total"] == 256
    pins = dict(saved["source_sha256"])
    for name, digest in FROZEN.items():
        path = str((PACKET / name).relative_to(ROOT))
        assert path not in pins or pins[path] == digest
        pins[path] = digest
    before = {path: sha(ROOT / path) for path in pins}
    assert before == pins and len(pins) == 32
    expected = copy.deepcopy(base)
    for name in ("result.json", "calculate-v2.py"):
        expected["source_sha256"][str((PACKET / name).relative_to(ROOT))] = FROZEN[name]
    expected["source_pin_count"] = 29
    expected["execution"]["output_wrapper"] = str((PACKET / "calculate-v2.py").relative_to(ROOT))
    expected["reproduction_command"] = (
        f"uv run python -B {(PACKET / 'calculate-v2.py').relative_to(ROOT)} --out "
        f"{PACKET.relative_to(ROOT)}/reproduction-v2-01.json"
    )
    expected["output_guard_revision"] = {
        "original_three_files_unchanged": True,
        "original_numerical_and_hardware_findings_exact": True,
        "reject_existing_requested_entry_including_dangling_symlink": True,
        "exclusive_creation_uses_original_requested_path": True,
        "path_resolution_used_only_for_parent_ownership_test": True,
        "capacity_or_geometry_or_hardware_adoption_changed": False,
    }
    assert saved == expected, "Unexpected v1-to-v2 composition difference"
    original = runpy.run_path
    wrapper = original(str(PACKET / "calculate-v2.py"))
    spec = read(PACKET / "inputs.json")
    allowed = {PACKET / "calculate.py"} | {
        ROOT / spec["sources"][name]["path"] for name in ("hardware_method", "corner_method")
    }
    calls = []

    def forbidden(*args, **kwargs):
        raise AssertionError("Historical preparation is outside this review")

    def guarded(path, *args, **kwargs):
        assert Path(path) in allowed
        calls.append(str(Path(path).relative_to(ROOT)))
        module = original(path, *args, **kwargs)
        if Path(path) != PACKET / "calculate.py":
            for name in ("prepare", "evaluate"):
                if name in module:
                    module[name] = forbidden
        return module

    runpy.run_path = guarded
    try:
        assert wrapper["evaluate"]() == saved, "Guarded stdlib replay differs"
    finally:
        runpy.run_path = original
    assert len(calls) == 3
    # Inject an inert changed numerical result; exact v1 equality must reject it.
    def changed_original(path, *args, **kwargs):
        assert Path(path) == PACKET / "calculate.py"
        changed = copy.deepcopy(base)
        changed["four_stations"][0]["matched_wood_travel_mm"] += .001
        return {"evaluate": lambda: changed}

    runpy.run_path = changed_original
    try:
        try:
            wrapper["evaluate"]()
        except ValueError as error:
            assert "original arithmetic" in str(error)
        else:
            raise AssertionError("Changed v1 numerical result admitted")
    finally:
        runpy.run_path = original
    main = wrapper["main"]
    globals_ = main.__globals__
    saved_here, saved_evaluate, saved_argv = globals_["HERE"], globals_["evaluate"], sys.argv
    tests, eval_calls = [], []
    try:
        with tempfile.TemporaryDirectory(prefix="inert-guards-", dir=HERE) as directory:
            fixture = Path(directory)
            owned = fixture / "owned"
            owned.mkdir()
            globals_["HERE"] = owned

            def inert_evaluate():
                eval_calls.append(True)
                return {"source_pin_count": 0, "inert_review_fixture": True}

            globals_["evaluate"] = inert_evaluate
            occupied = owned / "occupied.json"
            occupied.write_text("preserve")
            occupied_dir = owned / "directory.json"
            occupied_dir.mkdir()
            dangling = owned / "dangling.json"
            dangling.symlink_to(owned / "missing-target.json")
            link = owned / "link.json"
            link.symlink_to(occupied)
            for label, output in (
                ("existing_file", occupied), ("existing_directory", occupied_dir),
                ("existing_symlink", link), ("dangling_symlink", dangling),
                ("wrong_parent", fixture / "outside.json"), ("wrong_suffix", owned / "bad.txt"),
            ):
                sys.argv = ["calculate-v2.py", "--out", str(output)]
                try:
                    main()
                except ValueError:
                    assert not eval_calls
                else:
                    raise AssertionError(f"Guard admitted {label}")
                tests.append(label)
            assert occupied.read_text() == "preserve" and dangling.is_symlink()
            # Creation uses the supplied entry; parent aliases remain legitimate.
            alias = fixture / "parent-alias"
            alias.symlink_to(owned, target_is_directory=True)
            for label, output in (("fresh_direct", owned / "direct.json"),
                                  ("fresh_parent_alias", alias / "aliased.json")):
                sys.argv = ["calculate-v2.py", "--out", str(output)]
                with contextlib.redirect_stdout(io.StringIO()):
                    main()
                assert read(output) == {"source_pin_count": 0, "inert_review_fixture": True}
                tests.append(label)
            # An entry occupied during evaluation must still lose to mode x.
            race = owned / "race.json"

            def occupy_during_evaluate():
                race.symlink_to(owned / "still-missing.json")
                return {"source_pin_count": 0}

            globals_["evaluate"] = occupy_during_evaluate
            sys.argv = ["calculate-v2.py", "--out", str(race)]
            try:
                main()
            except FileExistsError:
                assert os.path.lexists(race) and race.is_symlink()
                assert not (owned / "still-missing.json").exists()
            else:
                raise AssertionError("Exclusive creation followed a newly inserted symlink")
            tests.append("symlink_inserted_after_early_guard")
    finally:
        globals_["HERE"], globals_["evaluate"], sys.argv = saved_here, saved_evaluate, saved_argv
    assert {path: sha(ROOT / path) for path in pins} == before
    return {
        "schema": "hardware_wrapper_composition_correctness_review/v1", "findings": [],
        "helper_sha256": sha(OWN), "source_sha256": pins,
        "sources_verified_before_after": len(pins), "sources_unchanged": True,
        "v1_arithmetic_proof_reused": {"path": str((PACKET / "independent-review-v1/correctness/receipt.json").relative_to(ROOT)),
                                       "sha256": FROZEN["independent-review-v1/correctness/receipt.json"], "corners": 256},
        "v2_diff_only_declared_metadata": True, "exact_saved_result_replay": True,
        "original_numerical_mutation_rejected": True, "inert_CLI_guard_tests": tests,
        "wrapper_replay_calls": calls,
        "limits": "Stdlib scalar composition and inert output fixtures only. No CAD/native/solver/global work, fields, shared edits, staging, commits or physical work.",
        "reproduction_command": f"uv run python -B {OWN.relative_to(ROOT)}",
    }


if __name__ == "__main__":
    receipt = review()
    output = HERE / "receipt.json"
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "sha256": sha(output),
                      "sources": receipt["sources_verified_before_after"], "findings": receipt["findings"]}))
