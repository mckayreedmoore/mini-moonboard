"""Frozen saved-summary architecture/source review; in-memory fixtures only."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "summarize.py": "99ead1194671c82e0e28f905e84c4208cf2a82dc1ed4532aaf1aeb13c0c7124d",
    "test_summarize.py": "53fb7a6a9be0678116f877de6b7659a8b9356406765b9ca9035b32059d1dcb7d",
    "source-proof.json": "94fb0a568c3d8332c30653b136c5b57e2d0fdffe4e2353a10a705d90b514be39",
    "verification.json": "d74713c46802bb959b450646175fa08f907ce403ee31cdc3dbae5deaa2b79c09",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rejects(callback, message):
    try:
        callback()
    except ValueError as error:
        require(message in str(error), "unexpected rejection: " + str(error))
    else:
        raise AssertionError("expected rejection: " + message)


def review():
    pins = {str((PACKET / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "four frozen targets differ")
    proof, verification = (read(PACKET / n) for n in ("source-proof.json", "verification.json"))
    require(proof["verified_source_pins"] == verification["verified_method_sources"], "method source records differ")
    for name, digest in proof["verified_source_pins"].items():
        require(name not in pins or pins[name] == digest, "contradictory method source pin")
        pins[name] = digest
    pattern = proof["output_guard"]["prior_pattern"]
    pins[pattern["path"]] = pattern["sha256"]
    before = {n: sha(ROOT / n) for n in pins}
    require(before == pins and len(pins) == 9, "method/retention source union differs")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")
    context_before = {n: sha(ROOT / n) for n in contexts}
    spec = importlib.util.spec_from_file_location("z180_structure_summary_only", PACKET / "summarize.py")
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    require(a.ROOT == ROOT and a.LOADED_SHA == TARGETS["summarize.py"], "summary identity differs")
    require(a.SELECTORS == proof["selected_original_definitions"]["source"]
            and a.CLOSURE_GUARD == proof["source_union_guard"]["source"]
            and a.GATE == proof["expected_future_source_bindings"]["gate"]
            and a.CONSUMER == proof["expected_future_source_bindings"]["combined_consumer"]
            and a.GEOMETRY == proof["expected_future_source_bindings"]["geometry"], "source authorities differ")
    source_tree = ast.parse((PACKET / "summarize.py").read_bytes())
    imports = [ast.unparse(n) for n in source_tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    require(imports == ["import argparse", "import ast", "import hashlib", "import json", "import math", "import os",
                        "import stat", "from pathlib import Path", "from types import SimpleNamespace"], "import boundary changed")
    selectors_raw = (ROOT / a.SELECTORS["path"]).read_bytes()
    guard_raw = (ROOT / a.CLOSURE_GUARD["path"]).read_bytes()
    original_nodes = {n.name: n for n in ast.parse(selectors_raw).body if isinstance(n, ast.FunctionDef) and n.name in a.SELECTED}
    require({n: hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
             for n, node in original_nodes.items()} == proof["selected_original_definitions"]["AST_sha256"],
            "frozen selector definitions differ")
    selected_pins = {}
    selectors = a.definitions(a.SELECTORS, a.SELECTED, selected_pins)
    require(set(vars(selectors)) == set(a.SELECTED) and selected_pins == {a.SELECTORS["path"]: a.SELECTORS["sha256"]},
            "selector loader exposed unselected source")
    with patch.object(a.ast, "parse", side_effect=AssertionError("AST before exact source authentication")):
        rejects(lambda: a.definitions({**a.SELECTORS, "sha256": "0" * 64}, a.SELECTED, {}), "exact source bytes differ")

    # Reuse the frozen synthetic fixture, replacing only its nested file-writing
    # save() with an in-memory byte store. No candidate artifacts are accessed.
    test_tree = ast.parse((PACKET / "test_summarize.py").read_bytes())
    nodes = [copy.deepcopy(n) for n in test_tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
             and n.name in ("findings", "fixture", "SimpleFixture")]
    fixture_node = next(n for n in nodes if n.name == "fixture")
    fixture_node.decorator_list = []
    replacement = ast.parse('''def save(path, data):
    raw = data if isinstance(data, bytes) else (json.dumps(data, sort_keys=True, allow_nan=False)+"\\n").encode()
    memory[str(root/path)] = raw
    return {"path": str(path), "sha256": a.sha(raw)}
''').body[0]
    fixture_node.body = [replacement if isinstance(n, ast.FunctionDef) and n.name == "save" else n for n in fixture_node.body]
    memory = {}
    namespace = {"a": a, "copy": copy, "json": json, "Path": Path, "memory": memory,
                 "SELECTOR_RAW": selectors_raw, "GUARD_RAW": guard_raw, "OWN_RAW": (PACKET / "summarize.py").read_bytes()}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(PACKET / "test_summarize.py"), "exec"), namespace)  # noqa: S102
    inert_root = OWN.parent / "never-created-inert-root"
    real_read, real_stat = Path.read_bytes, Path.stat
    def memory_read(path):
        if str(path) in memory:
            return memory[str(path)]
        require(not path.is_relative_to(inert_root), "unexpected synthetic source read")
        return real_read(path)
    def memory_stat(path, *args, **kwargs):
        if str(path) in memory:
            return SimpleNamespace(st_size=len(memory[str(path)]))
        return real_stat(path, *args, **kwargs)
    with ExitStack() as stack:
        patcher = SimpleNamespace(setattr=lambda obj, name, value: stack.enter_context(patch.object(obj, name, value)))
        stack.enter_context(patch.object(Path, "read_bytes", memory_read))
        stack.enter_context(patch.object(Path, "stat", memory_stat))
        fixture = namespace["fixture"](inert_root, patcher)
        frozen_memory = dict(memory)
        result = a.build(fixture.manifest, fixture.ref)
        require(memory == frozen_memory and not inert_root.exists(), "pure summary mutated synthetic inputs or created files")
        first = result["cases"][0]
        require([r["case_id"] for r in result["cases"]] == list(a.CASES)
                and first["coarse"]["gross_raw_members"]["fully_braced_component_normal_interaction"]["worst"]["member"] == "member21"
                and first["rich"]["shaft"]["worst"]["axis_id"] == "shaft99", "whole saved witnesses or case ordering differ")
        require(first["coarse"]["source_limits"] == ["own inert field limit"]
                and first["coarse_selector_limits_provenance"]["source"] == fixture.manifest["cases"][0]["field"],
                "coarse limits were relabelled from old contract")
        require(first["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is False
                and result["cases"][1]["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is True
                and first["outer_snapshot_caveats"]["result_pins_missing_before_snapshot"], "incomplete outer snapshot caveat lost")
        require(first["nominal_seat_geometry"]["nominal_wood_seats"] == 112
                and len(first["nominal_seat_geometry"]["new_own_nominal_seats"]) == 16
                and first["nominal_seat_geometry"]["unaffected_proof_count"] == 96
                and first["nominal_seat_geometry"]["old_actions_or_strength_transferred"] is False,
                "own/inherited nominal seat evidence merged or promoted")
        require(result["complete_joint_resistance"] is None and result["unadopted_proposal"] is True
                and result["spacer_or_4p5in_adopted"] is False and not any(result["release"].values())
                and result["execution"]["gate_consumer_reducer_CAD_operator_K_q_native_or_solve_called"] is False,
                "summary implies strength, adoption or execution")
        require(first["coarse"]["panels"]["sampled_section_exceedances_CD1"]
                and first["rich"]["steel_scenarios"][0]["summary"]["used_hole_bearing"]["exceedance_count"] == 1
                and first["rich"]["timber"]["all24_complete_joint_resistances"] is None,
                "reference exceedances or null resistance suppressed")

        # Mutate only synthetic saved bytes and rebind their immediate hashes.
        for mutation, message in (("gate_command", "corrected consumer command"), ("config_pair", "combined consumer config/pair"),
                                  ("schema", "Z180 schemas"), ("snapshot", "coverage caveat"),
                                  ("raw_pair", "raw field/admission")):
            memory.clear()
            memory.update(frozen_memory)
            binding = copy.deepcopy(fixture.manifest["cases"][0])
            if mutation == "gate_command":
                target = "process"
            elif mutation == "config_pair":
                target = "config"
            elif mutation == "schema":
                target = "result"
            elif mutation == "raw_pair":
                target = "admission"
            else:
                target = "process"
            ref = binding[target] if target == "admission" else binding["component"][target]
            record = a.decode(memory[str(inert_root / ref["path"])])
            if mutation == "gate_command":
                record["command"][2] = "foreign.py"
            elif mutation == "config_pair":
                record["field"] = binding["admission"]
            elif mutation == "schema":
                record["schema"] = "preserved_old_schema"
            elif mutation == "raw_pair":
                record["input_raw_sha256"] = "0" * 64
            else:
                record["source_pins_after"] = record["source_pins_before"]
            rebound = fixture.save(ref["path"], record)
            if target == "admission":
                binding[target] = rebound
            else:
                binding["component"][target] = rebound
            rejects(lambda binding=binding: a.case_records(binding, {}), message if mutation != "snapshot" else "exact component source snapshot")
        memory.clear()
        memory.update(frozen_memory)
        require(result["verified_source_union"]["before_after_exact"] is True, "full source union verification omitted")
        # Fresh reservation must precede every source callback; mock filesystem
        # mutation functions so this review writes only its own final records.
        out = a.OWN.parent / "runs-v1/fresh/out.json"
        with patch.object(Path, "mkdir") as mkdir, patch.object(Path, "open", side_effect=FileExistsError), \
                patch.object(a, "checked", side_effect=AssertionError("source before exclusive reservation")) as checked:
            try:
                a.write_to_file(fixture.ref, out)
            except FileExistsError:
                require(mkdir.called and not checked.called, "occupied reservation reached source callback")
            else:
                raise AssertionError("occupied reservation accepted")
        rejects(lambda: a.bind_output(out.parent / ".." / "out.json"), "parent traversal")
        rejects(lambda: a.bind_output(inert_root / "foreign.json"), "own runs-v1")
        for text in ('{"x":NaN}', '{"x":1e999}', '{"x":1,"x":2}'):
            rejects(lambda text=text: a.decode(text), "JSON")
    require(a.ROOT == ROOT and a.OWN == PACKET / "summarize.py", "synthetic source hooks did not restore")
    require(not inert_root.exists(), "in-memory fixture escaped into filesystem")

    output_node = next(n for n in source_tree.body if isinstance(n, ast.FunctionDef) and n.name == "write_to_file")
    output_source = ast.unparse(output_node)
    require('bound.open(\'x+\')' in output_source and "os.fstat" in output_source and "bound.lstat" in output_source
            and "directory.st_ino" in output_source and "opened.st_ino" in output_source
            and "status='FAILED'" in output_source and '"STARTED"' in (PACKET / "summarize.py").read_text(),
            "exclusive inode guard or retained failure contract missing")
    require(proof["actual_six_case_manifest"] is None and proof["actual_summary_output"] is None
            and verification["production_manifest_supplied"] is False and verification["production_output_ready"] is False
            and verification["candidate_field_config_pair_gate_reducer_or_summary_execution"] is False
            and verification["CAD_operator_native_global_solve"] is False and not any(verification["release"].values()),
            "source-only method proof promoted to production result")
    require({n: sha(ROOT / n) for n in pins} == before, "target/source/history bytes changed")
    require(not any(n in ("cadquery", "OCP", "numpy", "scipy") or n.startswith("OCP.") for n in sys.modules),
            "native/scientific module imported")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT,
                          capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_summary_structure_review/v1", "findings": [], "review_helper_sha256": sha(OWN),
        "frozen_target_sha256": TARGETS,
        "integrity": {"method_source_pins": 6, "target_source_pattern_union": len(pins),
                      "union_sha256": hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                      "all_bound_bytes_unchanged_before_after": True,
                      "four_target_bytes": sum((PACKET / n).stat().st_size for n in TARGETS)},
        "architecture": {"seven_exact_0547_selector_definitions_only_no_whole_old_module_import": True,
                         "existing_two_exception_source_closure_guard_reused_without_descriptor_or_gate_calls": True,
                         "actual_schemas_config_raw_pair_process_command_logs_and_source_snapshots_explicitly_bound": True,
                         "parent_future_manifest_authority_distinct_from_method_source_proof": True,
                         "pure_build_and_separate_owned_exclusive_writer": True,
                         "complete_saved_witnesses_per_case_and_separate_steel_scenarios_retained": True,
                         "first_outer_incomplete_pre_snapshot_caveat_retained_not_relabelled_complete": True,
                         "112_nominal_seats_separate_16_own_96_inherited_no_pressure_or_strength_acceptance": True,
                         "own_field_limits_provenance_exceedances_null_resistances_false_release_retained": True,
                         "canonical_parent_unresolved_leaf_inode_parent_guards_and_failed_attempt_retention_explicit": True,
                         "current_Z200_sources_and_old_results_preserved_Z180_unadopted_no_panel_remedy": True},
        "inert_checks": {"original_selector_AST_hashes_exact_and_authentication_before_compile": True,
                         "frozen_synthetic_fixture_reused_with_memory_only_save": True,
                         "positive_six_case_selection_and_complete_source_union_checks": True,
                         "old_schema_bad_config_pair_raw_pair_process_command_snapshot_rejected": True,
                         "incomplete_snapshot_seat_split_source_limits_and_reference_exceedances_preserved": True,
                         "occupied_reservation_stops_source_callbacks_traversal_and_foreign_scope_rejected": True,
                         "duplicate_nonfinite_JSON_rejected_and_synthetic_inputs_unchanged": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts},
                    "parent_owns_maintained_prose": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)),
                 "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Only nine frozen method/source/pattern files plus current instruction/prose context were read; no candidate descriptors, actual fields, configs, actual roster or production manifest/result was accessed.",
                   "In-memory standard-library fixtures reuse the frozen findings/fixture/class AST; only the fixture save callback and decorators are adapted. Filesystem writes and gates, consumers, reducers, solver/CAD/native/global work never run.",
                   "The inherited two absolute provenance exceptions remain exact source contracts; actual full candidate closure and original first outer snapshot's 42 missing entries were not independently consumed or audited here.",
                   "Producer's 26 tests and historical numerical/selector proofs are authenticated evidence, not reissued. Parent owns any future exact six-case manifest and actual saved-JSON execution; production output is still unissued.",
                   "Exclusive output source and inert occupied-path guards were checked; actual alias-retarget/inode controls are retained producer evidence, not real filesystem mutation tests in this review. Only this new helper/receipt are written; no docs/Git/archive/prune or new acceptance gates."],
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
