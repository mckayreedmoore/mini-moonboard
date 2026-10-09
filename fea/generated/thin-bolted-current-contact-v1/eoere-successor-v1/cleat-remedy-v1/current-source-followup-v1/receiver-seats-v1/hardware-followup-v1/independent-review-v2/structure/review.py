"""Review the frozen output wrapper, reusing the authenticated v1 scalar audit.

Read sources and JSON; fake the old scalar callback and CLI in temporary fixtures.
Do not rerun arithmetic, target CLI, CAD, native methods or mechanics fields.
"""
from __future__ import annotations

import ast
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
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
HERE = OWN.parents[2]
EXPECTED = {
    "inputs.json": "6cba1fb87b9cfa337f2c5418afe6c0f7fa6def8d6ae463e9f355701df3d75e33",
    "calculate.py": "ed7a16cbdb97bf15ddc74e2af49bb3b512dc57c7541358392db55ea25d8dfc0e",
    "result.json": "fbe6983488fc5c3017810654f43df0e0ef2188657387cc6a3b92b4e02fbb4c0a",
    "calculate-v2.py": "cafd8b00756e7cf5177fb8722f6139883d4c40aa28a7a08bf9d988575aa770f0",
    "result-v2.json": "2a70abd309932e497daeb0bebf152439077f776a28823d910d50c35c71c24f42",
}
PRIOR_REVIEWS = {
    "correctness/receipt.json": "33b5a465b5ec7e5c3e113995f6762e719f8a5fbc27225bf4ea71f1078b6ca652",
    "correctness/review.py": "de63a82747c218c372a5f1d1f6cd969148331cac7d8e929bcc5692f92819dd2c",
    "structure/receipt.json": "0b6e1ac25e8e9a59b7eb8682e10c0812b6ef8121ceda7c43a0ec2d58eadb14e6",
    "structure/review.py": "8fca4986fadcd090321fa3b103032342183232839adf6d5c815681d1939bd9c2",
    "testing/receipt.json": "444b375c4e9fbaf6e39ead0219c5d81b4340f41c2819b9ae26f132c7f10d3eee",
    "testing/review.py": "0721033e0ba96c007820998333ca06ea26a9bfac8cc86eda8377ed93c74c7902",
}
GUARD = {
    "original_three_files_unchanged": True,
    "original_numerical_and_hardware_findings_exact": True,
    "reject_existing_requested_entry_including_dangling_symlink": True,
    "exclusive_creation_uses_original_requested_path": True,
    "path_resolution_used_only_for_parent_ownership_test": True,
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


def fake_checks(subject, original, expected):
    evaluate = subject["evaluate"]
    globals_ = evaluate.__globals__
    imports = []

    def load(path):
        imports.append(path)
        assert path == str(HERE / "calculate.py")
        return {"evaluate": lambda: copy.deepcopy(original)}

    with patch.dict(globals_, {"runpy": SimpleNamespace(run_path=load)}):
        assert evaluate() == expected
    assert imports == [str(HERE / "calculate.py")]
    changed = copy.deepcopy(original)
    changed["status"] = "changed scalar result"
    with patch.dict(globals_, {"runpy": SimpleNamespace(run_path=lambda _: {"evaluate": lambda: changed})}):
        rejects(evaluate, ValueError, "original arithmetic or recorded source pins changed")
    imports.clear()
    with patch.dict(globals_, {"runpy": SimpleNamespace(run_path=load), "ORIGINAL": {"calculate.py": "0" * 64}}):
        rejects(evaluate, ValueError, "frozen original hardware packet changed")
    assert not imports
    cases = ["exact frozen scalar callback", "changed scalar callback rejected", "original pin gate before callback import"]
    main = subject["main"]
    with tempfile.TemporaryDirectory(prefix="hardware-v2-structure-") as temporary:
        fixture = Path(temporary).resolve()
        owned = fixture / "owned"
        owned.mkdir()
        calls = []

        def invoke(path, error=None, occupy=None):
            calls.clear()

            def fake_evaluate():
                calls.append("evaluate")
                if occupy:
                    occupy()
                return {"source_pin_count": 29}

            output = io.StringIO()
            with patch.dict(globals_, {"HERE": owned, "ROOT": fixture, "evaluate": fake_evaluate}), \
                    patch.object(sys, "argv", ["calculate-v2.py", "--out", str(path)]), contextlib.redirect_stdout(output):
                if error:
                    rejects(main, error)
                else:
                    main()
            return output.getvalue()

        fresh = owned / "fresh.json"
        stdout = invoke(fresh)
        assert calls == ["evaluate"] and read(fresh) == {"source_pin_count": 29}
        assert json.loads(stdout)["out"] == "owned/fresh.json"
        cases.append("fresh requested entry written exclusively")
        existing = owned / "existing.json"
        existing.write_text("prior bytes\n")
        invoke(existing, ValueError)
        assert not calls and existing.read_text() == "prior bytes\n"
        cases.append("existing regular entry rejected before callback")
        dangling = owned / "dangling.json"
        missing = fixture / "missing.json"
        dangling.symlink_to(missing)
        invoke(dangling, ValueError)
        assert not calls and dangling.is_symlink() and not missing.exists()
        cases.append("dangling requested entry rejected before callback")
        for path in (fixture / "outside.json", owned / "wrong.txt"):
            invoke(path, ValueError)
            assert not calls and not os.path.lexists(path)
        cases.append("wrong parent and suffix rejected before callback")
        late = owned / "late.json"
        missing_late = fixture / "missing-late.json"
        invoke(late, FileExistsError, lambda: late.symlink_to(missing_late))
        assert calls == ["evaluate"] and late.is_symlink() and not missing_late.exists()
        cases.append("late requested-entry symlink rejected by exclusive open")
    return cases


def main():
    original, result = read(HERE / "result.json"), read(HERE / "result-v2.json")
    pins = result["source_sha256"]
    prior = read(HERE / "independent-review-v1/structure/receipt.json")
    manifest_ref = read(HERE / "inputs.json")["sources"]["frozen_receiver_packet"]
    manifest = read(ROOT / manifest_ref["path"])
    old_receiver = manifest["final_files"] + manifest["retained_development_files"]

    def unchanged():
        assert all(sha(HERE / path) == digest for path, digest in EXPECTED.items())
        assert all(sha(HERE / "independent-review-v1" / path) == digest for path, digest in PRIOR_REVIEWS.items())
        assert all(sha(ROOT / path) == digest for path, digest in pins.items())
        assert sha(ROOT / manifest_ref["path"]) == manifest_ref["sha256"]
        assert len(old_receiver) == 10
        assert all(pins[row["path"]] == row["sha256"] and sha(ROOT / row["path"]) == row["sha256"]
                   and (ROOT / row["path"]).stat().st_size == row["bytes"] for row in old_receiver)

    unchanged()
    assert prior["confirmed_findings"] == []
    assert prior["source_checks"]["scalar_evaluate_canonical_result_matches_frozen"] is True
    assert prior["target_sha256"] == {relative(HERE / name): EXPECTED[name] for name in ("inputs.json", "calculate.py", "result.json")}
    union = {**original["source_sha256"], relative(HERE / "result.json"): EXPECTED["result.json"],
             relative(HERE / "calculate-v2.py"): EXPECTED["calculate-v2.py"]}
    assert len(original["source_sha256"]) == 27 and len(union) == result["source_pin_count"] == 29
    assert pins == union
    expected = copy.deepcopy(original)
    expected.update(source_sha256=union, source_pin_count=29, output_guard_revision=GUARD,
                    reproduction_command=f"uv run python -B {relative(HERE / 'calculate-v2.py')} --out {relative(HERE)}/reproduction-v2-01.json")
    expected["execution"]["output_wrapper"] = relative(HERE / "calculate-v2.py")
    assert result == expected
    assert all(value is False for value in result["release"].values())
    assert result["current_axes_stay_Z_mm"] == 200 and result["proposed_Z_mm_unadopted"] == 180
    tree = ast.parse((HERE / "calculate-v2.py").read_bytes())
    imports = {node.module.split(".")[0] for node in tree.body if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= sys.stdlib_module_names
    cli = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    calls = [node for node in ast.walk(cli) if isinstance(node, ast.Call)]
    resolves = [ast.unparse(node.func.value) for node in calls if isinstance(node.func, ast.Attribute) and node.func.attr == "resolve"]
    assert resolves == ["requested.parent"]
    assert any(ast.unparse(node) == "os.path.lexists(requested)" for node in calls)
    assert any(ast.unparse(node) == "requested.open('x')" for node in calls)
    cases = fake_checks(runpy.run_path(str(HERE / "calculate-v2.py")), original, expected)
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    unchanged()
    receipt = {
        "schema": "eoere_cleat_hardware_wrapper_independent_structure_review/v2",
        "status": "BOUNDED_READY_NO_SUBSTANTIAL_FINDINGS",
        "confirmed_findings": [],
        "target_sha256": {relative(HERE / path): digest for path, digest in EXPECTED.items()},
        "source_checks": {"pins_verified_before_after": 29, "source_map_canonical_sha256": canonical(pins),
                          "exact_old27_plus_old_result_and_new_wrapper": True,
                          "saved_v2_exactly_old_result_plus_five_metadata_changes": True,
                          "all_ten_receiver_files_and_six_prior_review_files_unchanged": True,
                          "prior_frozen_manifest": manifest_ref, "stdlib_imports": sorted(imports)},
        "reused_scalar_audit": {"receipt": relative(HERE / "independent-review-v1/structure/receipt.json"),
                                "sha256": PRIOR_REVIEWS["structure/receipt.json"],
                                "scalar_arithmetic_rerun_in_this_review": False},
        "fake_callback_and_CLI_checks": cases,
        "architecture": {
            "ownership": "The wrapper owns output guarding and provenance metadata. It checks the original three frozen files before loading the existing scalar evaluate callable and requires exact equality with its saved result before augmentation. Original reducers, scalar helpers and literal TOOL ownership are unchanged.",
            "source_union": "The 29 current pins retain every old scalar/reference and receiver witness and add the original result plus this wrapper. The result does not self-pin. Reproduction names the v2 wrapper; post-calculation verification covers the full union. This remains a bounded direct scalar closure, not a historical producer closure.",
            "output_and_failure": "Only the parent is resolved for ownership; lexists rejects occupied requested entries before the callback. Exclusive open uses the original requested path and rejects a newly occupied final entry, including a dangling symlink. These fake checks establish the output fix, not production arithmetic or physical execution.",
            "claim_boundary": "Exact saved-result comparison preserves current Z200 HOLD4, unadopted Z180 and 4in/4.5in comparisons, false release flags, catalog-versus-actual distinctions and conditional drill/tool limits. No capacity, geometry or hardware adoption changes.",
            "retention": "Original three files, all six v1 review files and all ten receiver final/development witnesses remain unchanged. The small wrapper and corrected result reuse those witnesses; this compact review adds no cache, manual, asset, model or cleanup action.",
        },
        "remaining": prior["remaining"],
        "CAD_native_global_current_component_fields_or_model_execution": False,
        "target_CLI_or_original_scalar_execution": False,
        "target_shared_docs_index_staging_commit_or_cleanup_action": False,
        "review_artifacts": {"helper": relative(OWN), "helper_sha256": sha(OWN),
                             "receipt": relative(OWN.with_name("receipt.json"))},
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "pins": 29, "fake_checks": len(cases),
                      "helper_sha256": sha(OWN), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
