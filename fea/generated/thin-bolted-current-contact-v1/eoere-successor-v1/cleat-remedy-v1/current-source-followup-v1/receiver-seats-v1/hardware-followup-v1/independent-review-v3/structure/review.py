"""Bounded canonical-output review; reuse authenticated earlier scalar proofs.

Only source/JSON reads and fake callbacks/CLI fixtures run. No scalar replay,
production CLI, CAD, native methods, mechanics fields or shared-file writes.
"""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import io
import json
import runpy
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
HERE = OWN.parents[2]
TARGETS = {
    "calculate-v3.py": "352167060aa4baacfe2f460670d0a28a8638a173f312b9887e24cf5babb12f2c",
    "result-v3.json": "16962d3d5bc897336c37ac5da945e08bd0268604c1f0fc640127786dd5d97781",
}
V2_REVIEWS = {
    "correctness/receipt.json": "eaeea9fe1bee28beee95f65a39b9d952032b660ca1b9422229a9108c5134e05f",
    "correctness/review.py": "7b24ee1f6d4174f0946e6703b8b3eb7bfc11cac724d4e74b95fd3877b0c72c66",
    "structure/receipt.json": "163d942766912d876413e2f9e2290d3b992e9d73293e76cef4b48c3d42ff658e",
    "structure/review.py": "375f98b8e4016a7611c71e3a4cc0f62240723b2933fa49722ba985c753f3a23a",
    "testing/receipt.json": "0f0e0aae9c587f40121b6f8d2b42bf8996a5be678e04c24f4cbb166ffc3a0d78",
    "testing/review.py": "774882ca2b07c60fcbecd8a8866f3609e7f9c86633cc70f97c6fecfee510fccf",
}
GUARD = {
    "original_five_v1_v2_files_unchanged": True,
    "original_numerical_and_hardware_findings_exact": True,
    "requested_parent_resolved_and_validated_once": True,
    "destination_bound_to_canonical_owned_directory": True,
    "reject_existing_canonical_leaf_including_dangling_symlink": True,
    "exclusive_creation_uses_canonical_owned_destination": True,
    "requested_parent_alias_retarget_cannot_redirect_output": True,
    "capacity_or_geometry_or_hardware_adoption_changed": False,
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def relative(path):
    return path.relative_to(ROOT).as_posix()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def rejects(callback, exception, message=None):
    try:
        callback()
    except exception as error:
        assert message is None or message in str(error)
    else:
        raise AssertionError("expected rejection")


def fake_checks(subject, previous, expected):
    evaluate = subject["evaluate"]
    globals_ = evaluate.__globals__
    imported = []

    def load(path):
        imported.append(path)
        assert path == str(HERE / "calculate-v2.py")
        return {"evaluate": lambda: copy.deepcopy(previous)}

    with patch.dict(globals_, {"runpy": SimpleNamespace(run_path=load)}):
        assert evaluate() == expected
    assert imported == [str(HERE / "calculate-v2.py")]
    imported.clear()
    with patch.dict(globals_, {"runpy": SimpleNamespace(run_path=load), "PREVIOUS": {"calculate-v2.py": "0" * 64}}):
        rejects(evaluate, ValueError, "frozen v2 hardware wrapper/result changed")
    assert not imported
    changed = copy.deepcopy(previous)
    changed["status"] = "changed scalar result"
    with patch.dict(globals_, {"runpy": SimpleNamespace(run_path=lambda _: {"evaluate": lambda: changed})}):
        rejects(evaluate, ValueError, "v2 arithmetic or recorded source pins changed")
    cases = ["exact saved v2 callback", "v2 pin gate before callback import", "changed v2 callback rejected"]
    with tempfile.TemporaryDirectory(prefix="hardware-v3-structure-") as temporary:
        fixture = Path(temporary).resolve()
        owned, outside, alias = fixture / "owned", fixture / "outside", fixture / "alias"
        owned.mkdir()
        outside.mkdir()
        alias.symlink_to(owned, target_is_directory=True)
        calls = []

        def invoke(path, error=None, effect=None):
            calls.clear()

            def callback():
                calls.append("evaluate")
                if effect:
                    effect()
                return {"source_pin_count": 31}

            output = io.StringIO()
            with patch.dict(globals_, {"HERE": owned, "ROOT": fixture, "evaluate": callback}), \
                    patch.object(sys, "argv", ["calculate-v3.py", "--out", str(path)]), contextlib.redirect_stdout(output):
                if error:
                    rejects(subject["main"], error)
                else:
                    subject["main"]()
            return output.getvalue()

        def retarget():
            alias.unlink()
            alias.symlink_to(outside, target_is_directory=True)

        outsider = outside / "retarget.json"
        outsider.write_text("preserved outside bytes\n")
        stdout = invoke(alias / "retarget.json", effect=retarget)
        assert calls == ["evaluate"] and read(owned / "retarget.json") == {"source_pin_count": 31}
        assert outsider.read_text() == "preserved outside bytes\n"
        assert json.loads(stdout)["out"] == "owned/retarget.json"
        cases.append("parent alias retarget writes only canonical owned leaf")
        invoke(alias / "outside.json", ValueError)
        assert not calls and not (outside / "outside.json").exists()
        cases.append("wrong resolved parent rejected before callback")
        alias.unlink()
        alias.symlink_to(owned, target_is_directory=True)
        blocked = owned / "dangling.json"
        missing = outside / "missing.json"
        blocked.symlink_to(missing)
        invoke(alias / "dangling.json", ValueError)
        assert not calls and blocked.is_symlink() and not missing.exists()
        cases.append("existing canonical dangling leaf rejected before callback")
        late = owned / "late.json"
        invoke(alias / "late.json", FileExistsError, lambda: late.symlink_to(missing))
        assert calls == ["evaluate"] and late.is_symlink() and not missing.exists()
        cases.append("late canonical symlink rejected by exclusive creation")
    return cases


def main():
    prior_helper = HERE / "independent-review-v2/structure/review.py"
    assert sha(prior_helper) == V2_REVIEWS["structure/review.py"]
    # Importing this frozen review exposes its pin tables, without its main().
    prior_module = runpy.run_path(str(prior_helper))
    old_targets = prior_module["EXPECTED"]
    old_reviews = {f"independent-review-v1/{path}": digest for path, digest in prior_module["PRIOR_REVIEWS"].items()}
    old_reviews.update({f"independent-review-v2/{path}": digest for path, digest in V2_REVIEWS.items()})
    previous, result = read(HERE / "result-v2.json"), read(HERE / "result-v3.json")
    prior = read(HERE / "independent-review-v2/structure/receipt.json")
    pins = result["source_sha256"]
    manifest_ref = read(HERE / "inputs.json")["sources"]["frozen_receiver_packet"]
    manifest = read(ROOT / manifest_ref["path"])
    receiver_files = manifest["final_files"] + manifest["retained_development_files"]

    def unchanged():
        assert len(old_targets) == 5 and len(old_reviews) == 12 and len(receiver_files) == 10
        assert all(sha(HERE / path) == digest for path, digest in (old_targets | TARGETS).items())
        assert all(sha(HERE / path) == digest for path, digest in old_reviews.items())
        assert all(sha(ROOT / path) == digest for path, digest in pins.items())
        assert sha(ROOT / manifest_ref["path"]) == manifest_ref["sha256"]
        assert all(pins[row["path"]] == row["sha256"] and sha(ROOT / row["path"]) == row["sha256"]
                   and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in receiver_files)

    unchanged()
    assert prior["source_checks"]["saved_v2_exactly_old_result_plus_five_metadata_changes"] is True
    union = {**previous["source_sha256"], relative(HERE / "result-v2.json"): old_targets["result-v2.json"],
             relative(HERE / "calculate-v3.py"): TARGETS["calculate-v3.py"]}
    assert len(previous["source_sha256"]) == 29 and len(union) == result["source_pin_count"] == 31
    assert pins == union
    expected = copy.deepcopy(previous)
    expected.update(source_sha256=union, source_pin_count=31, output_guard_revision=GUARD,
                    reproduction_command=f"uv run python -B {relative(HERE / 'calculate-v3.py')} --out {relative(HERE)}/reproduction-v3-01.json")
    expected["execution"]["output_wrapper"] = relative(HERE / "calculate-v3.py")
    assert result == expected
    assert all(value is False for value in result["release"].values())
    assert result["current_axes_stay_Z_mm"] == 200 and result["proposed_Z_mm_unadopted"] == 180
    tree = ast.parse((HERE / "calculate-v3.py").read_bytes())
    imports = {node.module.split(".")[0] for node in tree.body if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= sys.stdlib_module_names
    cli = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    calls = [node for node in ast.walk(cli) if isinstance(node, ast.Call)]
    assert [ast.unparse(node.func.value) for node in calls if isinstance(node.func, ast.Attribute)
            and node.func.attr == "resolve"] == ["requested.parent"]
    assert any(ast.unparse(node) == "os.path.lexists(destination)" for node in calls)
    assert any(ast.unparse(node) == "destination.open('x')" for node in calls)
    destination = next(node for node in cli.body if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "destination")
    assert ast.unparse(destination.value) == "HERE / requested.name"
    assert all(node.lineno <= destination.lineno for node in ast.walk(cli) if isinstance(node, ast.Name) and node.id == "requested")
    cases = fake_checks(runpy.run_path(str(HERE / "calculate-v3.py")), previous, expected)
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    receipt = {
        "schema": "eoere_cleat_hardware_canonical_wrapper_independent_structure_review/v3",
        "status": "BOUNDED_READY_NO_SUBSTANTIAL_FINDINGS", "confirmed_findings": [],
        "target_sha256": {relative(HERE / path): digest for path, digest in (old_targets | TARGETS).items()},
        "source_checks": {"pins_verified_before_after": 31, "source_map_canonical_sha256": canonical(pins),
                          "exact_old29_plus_v2_result_and_v3_wrapper": True,
                          "saved_v3_exactly_v2_result_plus_five_metadata_changes": True,
                          "all_five_old_targets_ten_receiver_and_twelve_review_files_unchanged": True,
                          "prior_review_map_canonical_sha256": canonical(old_reviews), "stdlib_imports": sorted(imports)},
        "reused_audits": {"v2_structure_receipt": relative(HERE / "independent-review-v2/structure/receipt.json"),
                          "sha256": V2_REVIEWS["structure/receipt.json"],
                          "v1_scalar_proof_reuse": prior["reused_scalar_audit"],
                          "scalar_or_v2_arithmetic_rerun_in_this_review": False},
        "fake_callback_and_CLI_checks": cases,
        "architecture": {
            "private_wrapper": "V3 owns only canonical output and metadata. It authenticates frozen v2 wrapper/result before loading v2's existing evaluate callable, requires exact saved-result equality before augmentation, then rechecks every pin. It adds no reducer, geometry method, hardware choice or acceptance logic.",
            "source_union": "The direct scalar closure is old29 plus the frozen v2 result and v3 wrapper, with no conflicting replacement or result self-pin. Reproduction and output-wrapper identity name v3. Historical producer closure is not claimed.",
            "ownership_and_failure": "The requested parent is resolved and checked once. The canonical HERE/requested.name destination is then used for lexists, exclusive open and reporting. Retargeting the supplied parent alias during the fake callback leaves outside bytes untouched; early and late canonical symlink negatives preserve the target. This fixes the supplied alias-retarget route within the owned packet.",
            "claims": "All non-metadata v2 result fields remain exact, including current Z200 HOLD4, unadopted Z180, 4in/4.5in comparisons, catalog-versus-actual boundaries, conditional drill/tool limits and false release flags. Corrected output guard flags describe canonical destination semantics.",
            "retention": "All five frozen v1/v2 target records, twelve v1/v2 review files, ten receiver final/development witnesses and the full31-pin union remain unchanged. Earlier files stay preserved; no cache, manual, model, asset or cleanup action is added.",
        },
        "remaining": prior["remaining"],
        "CAD_native_global_current_component_fields_or_model_execution": False,
        "target_CLI_or_original_scalar_or_v2_evaluate_execution": False,
        "target_shared_docs_index_staging_commit_or_cleanup_action": False,
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN),
                             "receipt": relative(OWN.with_name("receipt.json"))},
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "pins": 31, "fake_checks": len(cases),
                      "helper_sha256": sha(OWN), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
