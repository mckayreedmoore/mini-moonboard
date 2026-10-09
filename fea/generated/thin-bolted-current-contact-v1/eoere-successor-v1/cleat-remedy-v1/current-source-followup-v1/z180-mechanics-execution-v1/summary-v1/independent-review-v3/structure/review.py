"""Frozen whole-ancestry summary output review; source inspection, no writer runs."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
CORRECTION = PACKET / "review-fix-v3"
TARGETS = {
    "summarize.py": "787626079340ea3999f940cd7e057dd5c095720d42a54e44e30711ebc8f1a36e",
    "test_summarize.py": "e42c9dfbace8f59911cc76d54cea99409bd37adab12df2756f1e7f0ed7017dea",
    "verification.json": "dce19350e322c6c02b1a0a58e5a464b3f647c827514f2460ee837e5216ae0c06",
}
PREVIOUS = {
    "independent-review-v1/structure/review.py": "1305e1de8bcafab736a1fcdb3d1a64056de5821458a4b1b1d8cab34b5517f6fe",
    "independent-review-v1/structure/receipt.json": "c35e1d0b22f9869541c96fcb76ee879a2c3aa66f1ab5c7a9ec0f868a4dda0d57",
    "independent-review-v2/structure/review.py": "dd9f6a993aef841e5758eba85569418958a0b0e169b0cf99355ae80fb26bfb56",
    "independent-review-v2/structure/receipt.json": "d35e701df74f20b2b63dec98800b92dbe5fe39f19bc80f127b3077ba8dc6d9bd",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rejects(callback, text):
    try:
        callback()
    except ValueError as error:
        require(text in str(error), "unexpected rejection: " + str(error))
    else:
        raise AssertionError("expected rejection: " + text)


def review():
    pins = {str((CORRECTION / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "three frozen v3 targets differ")
    verification = read(CORRECTION / "verification.json")
    require(verification["preserved_sources_before"] == verification["preserved_sources_after"]
            and len(verification["preserved_sources_before"]) == verification["preserved_source_count"] == 20,
            "historical source binding record differs")
    for mapping in (verification["preserved_sources_before"],
                    {str((PACKET / n).relative_to(ROOT)): h for n, h in PREVIOUS.items()}):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "contradictory source/history pin")
            pins[name] = digest
    before = {n: sha(ROOT / n) for n in pins}
    require(before == pins, "bound source/history bytes differ")
    require(all((ROOT / verification[name]["path"]).stat().st_size == verification[name]["bytes"]
                for name in ("helper", "tests")), "target source byte counts differ")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")
    context_before = {n: sha(ROOT / n) for n in contexts}

    source = CORRECTION / "summarize.py"
    tree = ast.parse(source.read_bytes())
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    imports = [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    require(imports == ["import argparse", "import hashlib", "import json", "import os", "import stat",
                        "from pathlib import Path", "from types import ModuleType"], "unexpected import boundary")
    require(set(functions) == {"require", "identity", "original", "bind_output", "write_to_file", "main"},
            "wrapper added another responsibility")
    writer = functions["write_to_file"]
    calls = sorted((n for n in ast.walk(writer) if isinstance(n, ast.Call)), key=lambda n: n.lineno)
    opens = [n for n in calls if ast.unparse(n.func) == "os.open"]
    mkdirs = [n for n in calls if ast.unparse(n.func) == "os.mkdir"]
    require(len(opens) == 3 and ast.unparse(opens[0].args[0]) == "SUMMARY_ROOT"
            and ast.unparse(opens[0].args[1]) == "DIRECTORY_FLAGS"
            and all(any(k.arg == "dir_fd" and ast.unparse(k.value) == "parent_fd" for k in n.keywords) for n in opens[1:]),
            "directory/leaf opens not rooted in held ownership")
    require(len(mkdirs) == 1 and ast.unparse(mkdirs[0].args[0]) == "name"
            and any(k.arg == "dir_fd" and ast.unparse(k.value) == "parent_fd" for k in mkdirs[0].keywords),
            "path-based parent creation added")
    require(not any(ast.unparse(n.func) in ("bound.open", "bound.parent.mkdir", "Path.mkdir", "Path.open") for n in calls),
            "path output mutation bypasses ancestry ownership")
    bind = next(n for n in calls if ast.unparse(n.func) == "bind_output")
    original_call = next(n for n in calls if ast.unparse(n.func) == "original")
    require(opens[0].lineno < bind.lineno < mkdirs[0].lineno < opens[-1].lineno < original_call.lineno,
            "root authentication/creation/reservation/loading order differs")
    nested = {n.name: n for n in ast.walk(writer) if isinstance(n, ast.FunctionDef) and n is not writer}
    require(set(nested) == {"held_identity", "namespace", "write"}, "ownership helper boundaries differ")
    normal_write = ast.unparse(nested["write"])
    namespace_source, held_source = (ast.unparse(nested[n]) for n in ("namespace", "held_identity"))
    require("held_identity()" in normal_write and "if not failed:" in normal_write and "namespace()" in normal_write
            and "follow_symlinks=False" in normal_write and "os.fstat(stream.fileno())" in normal_write
            and "stat.S_ISREG" in normal_write, "write omitted anchored leaf/handle or normal namespace check")
    require("SUMMARY_ROOT.lstat()" in namespace_source and "stat.S_ISDIR" in namespace_source
            and "follow_symlinks=False" in namespace_source and "for parent_fd, name, _, expected in edges" in namespace_source
            and "os.fstat(child_fd)" in held_source, "root/ancestor namespace or held inode checks absent")
    writer_source = ast.unparse(writer)
    require("write(attempt, failed=True)" in writer_source and "status='FAILED'" in writer_source
            and "for fd in reversed(held)" in writer_source and "os.close(fd)" in writer_source
            and "with os.fdopen(leaf_fd" in writer_source, "failure policy or fd cleanup differs")
    require("os.O_EXCL" in ast.unparse(opens[-1]) and "os.O_NOFOLLOW" in ast.unparse(opens[-1])
            and "os.O_CREAT" in ast.unparse(opens[-1]), "fresh leaf reservation lost")
    original_source = ast.unparse(functions["original"])
    require("loader.original()" in original_source and "loader.write_to_file" not in original_source
            and "loader.main" not in original_source, "v2 writer invoked instead of source-only loader")
    require("(OWN, LOADED_SHA), (V2, V2_SHA)" in writer_source and "a.build(manifest, manifest_ref)" in writer_source,
            "required adapter/loader pins or unchanged build delegation omitted")

    spec = importlib.util.spec_from_file_location("z180_structure_summary_output_v3", source)
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    require(c.OWN == source and c.SUMMARY_ROOT == PACKET and c.LOADED_SHA == TARGETS["summarize.py"]
            and c.ROOT_ID == c.identity(PACKET.lstat()), "source-owned root or wrapper identity differs")
    a = c.original()
    require(a.OWN == PACKET / "summarize.py" and a.LOADED_SHA == "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d"
            and a.build.__code__.co_filename == str(a.OWN)
            and a.SELECTORS["sha256"] == "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735",
            "loader changed original build or selector owner")
    require(c.RELEASE == a.RELEASE and not any(c.RELEASE.values()), "release contract differs")
    with patch.object(c, "V2_SHA", "0" * 64):
        rejects(c.original, "output loader/v3 bytes changed")
    rejects(lambda: c.bind_output(Path("relative/../out.json")), "parent traversal")
    rejects(lambda: c.bind_output(OWN.parent / "foreign.json"), "own runs-v1")
    # API/CLI consistency uses a private callback only; never call the writer.
    ref, out = {"path": "synthetic-unread-manifest.json", "sha256": "a" * 64}, OWN.parent / "synthetic-unwritten.json"
    with patch.object(c, "write_to_file", return_value={"schema": "inert", "cases": []}) as callback, redirect_stdout(io.StringIO()):
        c.main(["--manifest", ref["path"], "--manifest-sha256", ref["sha256"], "--out", str(out)])
    callback.assert_called_once_with(ref, out)

    require(verification["checks"]["pytest_result"] == "43 passed in 0.30s"
            and verification["reuse"]["v2_writer_called"] is False
            and verification["scope"] == {"candidate_JSON_or_manifest_read": False,
                "gate_consumer_reducer_CAD_BREP_native_operator_global_or_solve_called": False,
                "genuine_summary_output_generated": False,
                "only_output_reservation_and_adapter_source_provenance_changed": True,
                "original_build_source_joins_selectors_classifiers_math_or_tolerances_changed": False},
            "inert verification or delegation scope differs")
    require(verification["interface"]["actual_roster_or_manifest"] is None
            and verification["interface"]["actual_summary_output"] is None
            and verification["unadopted_proposal"] is True and verification["complete_joint_resistance"] is None
            and verification["release"] == c.RELEASE, "output method proof implies production/strength/adoption")
    require(verification["remedy"]["reserved_leaf_itself_replaced"].startswith("Reject without touching replacement")
            and "retains STARTED" in verification["remedy"]["reserved_leaf_itself_replaced"],
            "leaf replacement retention boundary overstated")
    test_tree = ast.parse((CORRECTION / "test_summarize.py").read_bytes())
    test_names = {n.name for n in test_tree.body if isinstance(n, ast.FunctionDef)}
    require({"test_missing_parents_created_only_through_held_directory_fds",
             "test_source_owned_root_replaced_before_call_rejects_import_identity",
             "test_each_directory_replaced_immediately_before_open",
             "test_runs_ancestor_retarget_after_mkdir_cannot_redirect_following_stat",
             "test_all_held_ancestors_replaced_keep_failed_in_original_subtree",
             "test_original_parent_alias_retarget_stays_bound",
             "test_failed_callback_retained_and_retry_rejected",
             "test_same_output_two_callers_only_one_delegates"} <= test_names, "documented inert ownership controls absent")
    require({n: sha(ROOT / n) for n in pins} == before, "target/source/history drift")
    require(not any(n in ("cadquery", "OCP", "numpy", "scipy") or n.startswith("OCP.") for n in sys.modules),
            "native/scientific module imported")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT,
                          capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_summary_whole_ancestry_structure_review/v3", "findings": [],
        "review_helper_sha256": sha(OWN), "frozen_target_sha256": TARGETS,
        "reused_immutable_structure_reviews_sha256": PREVIOUS,
        "integrity": {"target_source_history_union": len(pins), "all_bound_bytes_unchanged_before_after": True,
                      "preserved_historical_source_records": 20,
                      "union_sha256": hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                      "three_new_target_bytes": sum((CORRECTION / n).stat().st_size for n in TARGETS)},
        "architecture": {"source_owned_root_identity_captured_before_loader_and_callbacks": True,
                         "held_root_and_every_relative_parent_created_opened_nofollow_and_identity_checked": True,
                         "no_path_mkdir_or_path_leaf_open_in_writer": True,
                         "normal_payload_checks_full_namespace_held_ancestry_and_reserved_leaf_inode": True,
                         "failed_record_checks_held_handles_leaf_and_stays_in_original_subtree": True,
                         "replaced_leaf_is_untouched_moved_original_STARTED_limit_explicit": True,
                         "exclusive_leaf_before_STARTED_before_source_loader_and_build": True,
                         "directory_fds_close_in_reverse_order_stream_owns_leaf_fd": True,
                         "exact_v3_v2_and_original99_manifest_pins_required": True,
                         "v2_used_only_as_verified_loader_original99_build_selectors_source_joins_unchanged": True,
                         "API_and_CLI_delegate_to_same_owned_writer": True,
                         "prior_failed_interrupted_and_reviewed_versions_preserved_without_new_PASS_label": True,
                         "old_case_results_unmodified_exceedances_null_resistance_and_snapshot_seat_limits_inherited": True,
                         "Z180_unadopted_current_Z200_authority_and_all_physical_releases_unchanged": True},
        "source_and_inert_checks": {"ownership_order_relative_open_mkdir_flags_namespace_failure_and_cleanup_AST": True,
                                     "exact_loader_chain_and_0547_selector_owner": True,
                                     "loader_hash_drift_traversal_and_foreign_output_scope_rejection": True,
                                     "CLI_exact_ref_and_destination_forwarding_only": True,
                                     "43_inert_control_source_and_saved_PASS_evidence_authenticated_not_rerun": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts},
                    "parent_owns_maintained_prose": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)),
                 "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Bounded ordinary source/AST/hash inspection and a private CLI callback only. No actual write_to_file execution or additional filesystem mutation experiment; producer's frozen 43 inert test evidence is authenticated, not rerun or reissued.",
                   "Original99 saved-case joins/selectors/math review and unchanged v2 loader proofs are reused. No genuine candidate descriptor/field/config/roster/manifest/summary data is read; no producer/gate/consumer/reducer/CAD/native/global/operator/solve work runs.",
                   "Peer review/interruption files are hash-bound retention records only. The completed actual six-case numerical packet and future production summary are outside this output-method review; source-only verification retains its original historical scope.",
                   "Only this new helper/receipt are written. Frozen targets/reviews, current/history/shared docs/site/index, Git/staging and archive/prune remain untouched; no physical/capacity/adoption or blanket acceptance gates are added."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    destination = OWN.with_name("receipt.json")
    if args.write:
        with destination.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"receipt_sha256": sha(destination), "review_helper_sha256": sha(OWN), "findings": len(receipt["findings"])}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
