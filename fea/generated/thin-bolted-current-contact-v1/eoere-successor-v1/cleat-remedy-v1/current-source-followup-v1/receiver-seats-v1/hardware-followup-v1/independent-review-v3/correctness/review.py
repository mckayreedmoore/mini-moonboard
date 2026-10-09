"""Narrow final composition review; reuse frozen v1/v2 arithmetic reviews."""

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
    "calculate-v3.py": "352167060aa4baacfe2f460670d0a28a8638a173f312b9887e24cf5babb12f2c",
    "result-v3.json": "16962d3d5bc897336c37ac5da945e08bd0268604c1f0fc640127786dd5d97781",
    "independent-review-v2/correctness/review.py": "7b24ee1f6d4174f0946e6703b8b3eb7bfc11cac724d4e74b95fd3877b0c72c66",
    "independent-review-v2/correctness/receipt.json": "eaeea9fe1bee28beee95f65a39b9d952032b660ca1b9422229a9108c5134e05f",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def review():
    for name, digest in FROZEN.items():
        assert sha(PACKET / name) == digest, name
    prior = read(PACKET / "independent-review-v2/correctness/receipt.json")
    assert prior["findings"] == [] and prior["v1_arithmetic_proof_reused"]["corners"] == 256
    base, saved = read(PACKET / "result-v2.json"), read(PACKET / "result-v3.json")
    pins = dict(prior["source_sha256"])
    additions = dict(saved["source_sha256"])
    additions.update({str((PACKET / name).relative_to(ROOT)): digest for name, digest in FROZEN.items()})
    for path, digest in additions.items():
        assert path not in pins or pins[path] == digest
        pins[path] = digest
    before = {path: sha(ROOT / path) for path in pins}
    assert before == pins and len(pins) == 36
    expected = copy.deepcopy(base)
    for name in ("result-v2.json", "calculate-v3.py"):
        expected["source_sha256"][str((PACKET / name).relative_to(ROOT))] = sha(PACKET / name)
    expected["source_pin_count"] = 31
    expected["execution"]["output_wrapper"] = str((PACKET / "calculate-v3.py").relative_to(ROOT))
    expected["reproduction_command"] = (
        f"uv run python -B {(PACKET / 'calculate-v3.py').relative_to(ROOT)} --out "
        f"{PACKET.relative_to(ROOT)}/reproduction-v3-01.json"
    )
    expected["output_guard_revision"] = {
        "original_five_v1_v2_files_unchanged": True,
        "original_numerical_and_hardware_findings_exact": True,
        "requested_parent_resolved_and_validated_once": True,
        "destination_bound_to_canonical_owned_directory": True,
        "reject_existing_canonical_leaf_including_dangling_symlink": True,
        "exclusive_creation_uses_canonical_owned_destination": True,
        "requested_parent_alias_retarget_cannot_redirect_output": True,
        "capacity_or_geometry_or_hardware_adoption_changed": False,
    }
    assert saved == expected, "Unexpected v2-to-v3 metadata or arithmetic change"
    original = runpy.run_path
    wrapper = original(str(PACKET / "calculate-v3.py"))
    spec = read(PACKET / "inputs.json")
    allowed = {PACKET / "calculate.py", PACKET / "calculate-v2.py"} | {
        ROOT / spec["sources"][name]["path"] for name in ("hardware_method", "corner_method")
    }
    calls = []

    def forbidden(*args, **kwargs):
        raise AssertionError("Historical preparation is outside this review")

    def guarded(path, *args, **kwargs):
        assert Path(path) in allowed
        calls.append(str(Path(path).relative_to(ROOT)))
        module = original(path, *args, **kwargs)
        if Path(path).parent != PACKET:
            for name in ("prepare", "evaluate"):
                if name in module:
                    module[name] = forbidden
        return module

    runpy.run_path = guarded
    try:
        assert wrapper["evaluate"]() == saved
    finally:
        runpy.run_path = original
    assert len(calls) == 4
    # A changed previous numerical result must fail before composition.
    def changed_previous(path, *args, **kwargs):
        assert Path(path) == PACKET / "calculate-v2.py"
        changed = copy.deepcopy(base)
        changed["four_stations"][0]["matched_wood_travel_mm"] += .001
        return {"evaluate": lambda: changed}

    runpy.run_path = changed_previous
    try:
        try:
            wrapper["evaluate"]()
        except ValueError as error:
            assert "v2 arithmetic" in str(error)
        else:
            raise AssertionError("Changed previous arithmetic admitted")
    finally:
        runpy.run_path = original
    main = wrapper["main"]
    globals_ = main.__globals__
    old_here, old_evaluate, old_argv = globals_["HERE"], globals_["evaluate"], sys.argv
    tests = []
    try:
        with tempfile.TemporaryDirectory(prefix="inert-canonical-", dir=HERE) as directory:
            fixture = Path(directory)
            owned, elsewhere = fixture / "owned", fixture / "elsewhere"
            owned.mkdir()
            elsewhere.mkdir()
            alias = fixture / "alias"
            globals_["HERE"] = owned
            sentinel = {"source_pin_count": 0, "inert_review_fixture": True}
            # Retarget during evaluation; both fresh and occupied external leaves
            # must be ignored while the canonical owned destination is created.
            for label in ("retarget_to_fresh_external_leaf", "retarget_to_occupied_external_leaf"):
                if alias.is_symlink():
                    alias.unlink()
                alias.symlink_to(owned, target_is_directory=True)
                name = label + ".json"
                if "occupied" in label:
                    (elsewhere / name).write_text("preserve external fixture")

                def retarget():
                    alias.unlink()
                    alias.symlink_to(elsewhere, target_is_directory=True)
                    return sentinel

                globals_["evaluate"] = retarget
                sys.argv = ["calculate-v3.py", "--out", str(alias / name)]
                captured = io.StringIO()
                with contextlib.redirect_stdout(captured):
                    main()
                assert read(owned / name) == sentinel
                assert json.loads(captured.getvalue())["out"] == str((owned / name).relative_to(ROOT))
                if "occupied" in label:
                    assert (elsewhere / name).read_text() == "preserve external fixture"
                else:
                    assert not (elsewhere / name).exists()
                tests.append(label)
            globals_["evaluate"] = forbidden
            for label, output in (("initial_wrong_parent", elsewhere / "bad.json"),
                                  ("wrong_suffix", owned / "bad.txt")):
                sys.argv = ["calculate-v3.py", "--out", str(output)]
                try:
                    main()
                except ValueError:
                    pass
                else:
                    raise AssertionError(f"Guard admitted {label}")
                tests.append(label)
            alias.unlink()
            alias.symlink_to(owned, target_is_directory=True)
            leaf = owned / "occupied.json"
            leaf.symlink_to(owned / "missing.json")
            sys.argv = ["calculate-v3.py", "--out", str(alias / leaf.name)]
            try:
                main()
            except ValueError:
                assert os.path.lexists(leaf) and leaf.is_symlink()
            else:
                raise AssertionError("Canonical dangling symlink admitted")
            tests.append("existing_canonical_dangling_leaf")
            race = owned / "race.json"

            def occupy():
                race.symlink_to(owned / "still-missing.json")
                return sentinel

            globals_["evaluate"] = occupy
            sys.argv = ["calculate-v3.py", "--out", str(alias / race.name)]
            try:
                main()
            except FileExistsError:
                assert race.is_symlink() and not (owned / "still-missing.json").exists()
            else:
                raise AssertionError("Late canonical leaf escaped exclusive creation")
            tests.append("canonical_leaf_inserted_after_early_guard")
    finally:
        globals_["HERE"], globals_["evaluate"], sys.argv = old_here, old_evaluate, old_argv
    assert {path: sha(ROOT / path) for path in pins} == before
    return {
        "schema": "hardware_canonical_output_correctness_review/v1", "findings": [],
        "helper_sha256": sha(OWN), "source_sha256": pins,
        "sources_verified_before_after": len(pins), "sources_unchanged": True,
        "prior_v1_v2_proofs_reused": True, "v3_diff_only_declared_metadata": True,
        "exact_saved_result_replay": True, "previous_numerical_mutation_rejected": True,
        "inert_canonical_output_tests": tests, "wrapper_replay_calls": calls,
        "limits": "Stdlib scalar composition and own inert output fixtures only. No CAD/native/solver/global work, fields, adoption, shared edits, staging, commits or physical work.",
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
