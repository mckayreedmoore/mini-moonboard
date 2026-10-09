"""Narrow frozen snapshot-shape adapter review; source and inert callbacks only."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
CORRECTION = PACKET / "review-fix-v4"
TARGETS = {
    "summarize.py": "e4ba76473e84aa7afdae3599a2c196b894a7d0311a407de9bb0daece647196d9",
    "test_summarize.py": "66eb2383a37b0f91abf7b8191cb78189ff0504ac6801b26fc352ffa168c31fe2",
    "verification.json": "69b6cb1d4f3776b2bb4830b6be69539843e913fc703f7812a2d45a3060f5b654",
}
REUSED = {
    "summarize.py": "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d",
    "review-fix-v2/summarize.py": "15dd2c60a1b6db3eeae6e98b0267268a4460c9a6efc86cb711aa8376fb82046f",
    "review-fix-v3/summarize.py": "787626079340ea3999f940cd7e057dd5c095720d42a54e44e30711ebc8f1a36e",
    "review-fix-v3/verification.json": "dce19350e322c6c02b1a0a58e5a464b3f647c827514f2460ee837e5216ae0c06",
    "independent-review-v1/structure/review.py": "1305e1de8bcafab736a1fcdb3d1a64056de5821458a4b1b1d8cab34b5517f6fe",
    "independent-review-v1/structure/receipt.json": "c35e1d0b22f9869541c96fcb76ee879a2c3aa66f1ab5c7a9ec0f868a4dda0d57",
    "independent-review-v3/structure/review.py": "fb87d4b552fcc79bbfc67487c131fa2b9dd89fbc69033f7e945a12f0a44c4089",
    "independent-review-v3/structure/receipt.json": "5fe91d73d327ec05b59efada74c4e29d863525afdedd9fe5a4305c97874a2164",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rejects(callback, text):
    try:
        callback()
    except ValueError as error:
        require(text in str(error), "unexpected rejection: " + str(error))
    else:
        raise AssertionError("expected rejection: " + text)


def review():
    pins = {str((CORRECTION / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    pins.update({str((PACKET / n).relative_to(ROOT)): h for n, h in REUSED.items()})
    before = {n: sha(ROOT / n) for n in pins}
    require(before == pins, "frozen targets or reused sources differ")
    verification = json.loads((CORRECTION / "verification.json").read_bytes())
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")
    context_before = {n: sha(ROOT / n) for n in contexts}
    spec = importlib.util.spec_from_file_location("z180_structure_snapshot_shape_v4", CORRECTION / "summarize.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    require(c.LOADED_SHA == TARGETS["summarize.py"] and c._writer.__file__ == str(c.V3)
            and c._writer.write_to_file.__code__.co_filename == str(c.V3)
            and c._writer.original is c.output_original
            and c._original_loader.__globals__ is vars(c._writer), "private exact writer/loader boundary differs")
    guard_code = c._writer.write_to_file.__code__
    # Capture the compiled adapted AST; original module loading remains source-only.
    captured = []
    builtin_compile = compile
    def capture_compile(source, filename, mode, *args, **kwargs):
        if isinstance(source, ast.Module):
            captured.append(copy.deepcopy(source))
        return builtin_compile(source, filename, mode, *args, **kwargs)
    with patch.object(c, "compile", side_effect=capture_compile, create=True):
        a = c.original()
    require(len(captured) == 1 and [n.name for n in captured[0].body] == ["case_records", "build"],
            "adapter compiled unselected implementation")
    original = ast.parse((PACKET / "summarize.py").read_bytes())
    original_selected = ast.Module(body=[n for n in original.body if isinstance(n, ast.FunctionDef)
                                       and n.name in ("case_records", "build")], type_ignores=[])
    adapted = captured[0]
    schemas = [n for n in ast.walk(adapted) if isinstance(n, ast.Constant) and n.value == c.SNAPSHOT_SCHEMA]
    require(len(schemas) == 2, "unexpected schema substitutions")
    # Normalize exactly the two authenticated schema constants and the one
    # optional observation back to the original AST; every other node is strict.
    schema_nodes = sorted(schemas, key=lambda n: (n.lineno, n.col_offset))
    for node, expected in zip(schema_nodes, c.OLD_SCHEMAS, strict=True):
        node.value = expected
    history = ast.parse(c.HISTORY_ACCESS, mode="eval").body
    class RestoreHistory(ast.NodeTransformer):
        count = 0
        def visit_Call(self, node):
            if (isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                    and ast.dump(node.func.value, include_attributes=False) == ast.dump(history.value, include_attributes=False)
                    and len(node.args) == 2 and ast.dump(node.args[0], include_attributes=False) == ast.dump(history.slice, include_attributes=False)
                    and isinstance(node.args[1], ast.List) and not node.args[1].elts and not node.keywords):
                self.count += 1
                return copy.deepcopy(history)
            return self.generic_visit(node)
    restore = RestoreHistory()
    adapted = restore.visit(adapted)
    require(restore.count == 1 and ast.dump(adapted, include_attributes=False) == ast.dump(original_selected, include_attributes=False),
            "adapter changes original joins/state/census/coverage/selectors beyond three seams")
    require(a.OWN == PACKET / "summarize.py" and a.LOADED_SHA == REUSED["summarize.py"]
            and a.build.__code__.co_filename == str(c.OWN) and a.case_records.__code__.co_filename == str(c.OWN)
            and a.SELECTORS["sha256"] == "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735",
            "adaptation relabelled original engineering authority")
    require(a is not c.original(), "adapted original module shared mutable state across loads")
    source_pins = {}
    a.verify(source_pins)  # Source-only union with adapter/closure-guard code, no data.
    require(source_pins[str(c.OWN.relative_to(ROOT))] == c.LOADED_SHA,
            "adapter provenance omitted from existing verified union")
    require(c._writer.write_to_file.__code__ is guard_code, "data adaptation changed writer code")

    token, manifest, manifest_ref = object(), {"source_sha256": {}}, {"path": "synthetic-unread.json", "sha256": "a" * 64}
    rejected_build = Mock(return_value=token)
    stub = type("PrivateInertOriginal", (), {})()
    stub.ROOT, stub.build = ROOT, rejected_build
    with patch.object(c, "original", return_value=stub):
        output_module = c.output_original()
        rejects(lambda: output_module.build(manifest, manifest_ref), "exact v4 adapter manifest pin")
        require(not rejected_build.called, "missing adapter pin reached inert build")
    # Fresh callback module for success preserves the supplied raw manifest/ref.
    build_callback = Mock(return_value=token)
    stub = type("PrivateInertOriginal", (), {})()
    stub.ROOT, stub.build = ROOT, build_callback
    manifest["source_sha256"][str(c.OWN.relative_to(ROOT))] = c.LOADED_SHA
    with patch.object(c, "original", return_value=stub):
        require(c.output_original().build(manifest, manifest_ref) is token, "output adapter did not delegate exact result")
    build_callback.assert_called_once_with(manifest, manifest_ref)
    direct_build = Mock(return_value=token)
    with patch.object(c, "original", return_value=type("PrivateReplay", (), {"build": staticmethod(direct_build)})()):
        require(c.build(manifest, manifest_ref) is token, "pure in-memory API did not delegate")
    direct_build.assert_called_once_with(manifest, manifest_ref)
    out = OWN.parent / "synthetic-unwritten.json"
    with patch.object(c._writer, "write_to_file", return_value=token) as writer:
        require(c.write_to_file(manifest_ref, out) is token, "wrapper bypassed retained writer")
    writer.assert_called_once_with(manifest_ref, out)
    with patch.object(c, "write_to_file", return_value={"schema": "inert", "cases": []}) as callback, redirect_stdout(io.StringIO()):
        c.main(["--manifest", manifest_ref["path"], "--manifest-sha256", manifest_ref["sha256"], "--out", str(out)])
    callback.assert_called_once_with(manifest_ref, out)
    with patch.object(c, "LOADED_SHA", "0" * 64), patch.object(c.ast, "parse", side_effect=AssertionError("AST after source drift")):
        rejects(c.original, "v4 adapter source changed")
    contract = verification["bounded_correction"]
    require(contract["exact_AST_substitution_count"] == 3
            and contract["engineering_method_equations_classifiers_tolerances_source_identity_state_census_or_coverage_checks_changed"] is False
            and contract["saved_snapshot_records_relabelled_or_rewritten"] is False
            and contract["output_guard"]["writer_code_changes"] is False
            and verification["checks"]["pytest_result"] == "13 passed in 0.58s", "recorded narrow adapter scope differs")
    require(verification["complete_joint_resistance"] is None and verification["unadopted_proposal"] is True
            and not any(verification["release"].values())
            and verification["scope"]["gate_consumer_reducer_CAD_BREP_native_operator_global_K_or_solve_called"] is False
            and verification["scope"]["genuine_summary_output_written"] is False, "saved replay proof promoted to mechanics/acceptance")
    require({n: sha(ROOT / n) for n in pins} == before, "target/reused source/history drift")
    require(not any(n in ("cadquery", "OCP", "numpy", "scipy") or n.startswith("OCP.") for n in sys.modules),
            "native/scientific module imported")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT,
                          capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_summary_saved_shape_structure_review/v4", "findings": [],
        "review_helper_sha256": sha(OWN), "frozen_target_sha256": TARGETS, "reused_source_and_review_sha256": REUSED,
        "integrity": {"target_source_review_union": len(pins), "all_bound_bytes_unchanged_before_after": True,
                      "union_sha256": hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                      "three_new_target_bytes": sum((CORRECTION / n).stat().st_size for n in TARGETS)},
        "architecture": {"exactly_two_schema_literals_and_one_optional_history_lookup_changed": True,
                         "all_other_original_case_and_build_AST_nodes_identical": True,
                         "no_saved_snapshot_rewrite_or_authority_state_hash_census_coverage_relaxation": True,
                         "own_adapter_pin_joins_existing_before_after_source_verification": True,
                         "output_manifest_requires_adapter_pin_and_preserves_exact_supplied_manifest_ref": True,
                         "pure_saved_replay_retains_raw_manifest_adds_execution_provenance": True,
                         "private_verified_v3_writer_code_and_captured_root_identity_reused": True,
                         "fresh_original_module_per_load_no_shared_engineering_namespace_override": True,
                         "unchanged_original99_math_selectors_source_joins_and_v3_guard_proofs_reused": True,
                         "old_failed_and_reviewed_packets_retained_at_original_scopes": True,
                         "incomplete_first_pre_snapshot_caveat_and_separate_16_own_96_old_seats_inherited": True,
                         "exceeded_references_null_complete_resistance_unadopted_Z180_false_releases_unchanged": True},
        "source_and_inert_checks": {"captured_compiled_AST_normalizes_exactly_to_original_except_three_seams": True,
                                     "fresh_module_loader_code_owner_and_writer_callback_isolation": True,
                                     "adapter_source_union_verification_source_only": True,
                                     "missing_adapter_manifest_pin_stops_build_source_drift_stops_AST": True,
                                     "pure_build_writer_and_CLI_exact_argument_and_result_delegation": True,
                                     "producer_13_inert_tests_and_1306_pin_saved_replay_evidence_not_rerun": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts},
                    "parent_owns_maintained_prose": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)),
                 "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Narrow data-adapter source/AST/hash inspection and private inert callbacks only. No output writer execution, filesystem mutation experiments, actual candidate descriptor/field/config/roster/manifest/summary reads, or gate/consumer/reducer/CAD/native/global work.",
                   "Original99 math/join/selector and exact v3 ownership reviews are reused rather than repeated. The source union probe verifies only adapter and existing closure-guard code; full actual 1306-pin saved-data replay remains producer evidence, not an independent reissue.",
                   "Preservation and actual replay references inside frozen verification remain opaque records; failed attempt01 and actual saved files are not opened or modified. Prior frozen proofs retain their original scope.",
                   "Only this new helper/receipt are written. No targets, prior reviews, shared docs/site/index, Git/staging or archive/prune changes and no new physical/capacity/adoption or blanket acceptance gates."],
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
