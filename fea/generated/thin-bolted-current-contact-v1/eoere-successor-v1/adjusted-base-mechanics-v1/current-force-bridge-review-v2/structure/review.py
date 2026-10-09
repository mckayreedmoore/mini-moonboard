"""Independent source/ownership/retention review; inert orchestration only."""
from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BRIDGE = OWN.parents[2] / "current-force-bridge-v1"
EXPECTED = {
    "bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab",
    "review-fix-v2/bridge.py": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643",
    "review-fix-v2/test_bridge.py": "cdaf6e63a542b738fd81b99e4c211952dd46765fb8c2082a1d43c0d977b88c90",
    "review-fix-v2/source-preflight.json": "158b2fd603cabac3d5e39ac81f726da251ce6a393b797e7e047daef3dee85fdc",
    "review-fix-v2/verification.json": "18903e345a4c7f59ecbf0036cd68946733981f8a8b9de29a3fef0a63b68a3f7a",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT))


def require(value, message):
    if not value:
        raise AssertionError(message)


def rejected(callback, error, text):
    try:
        callback()
    except error as failure:
        require(text in str(failure), "wrong rejection: " + str(failure))
    else:
        raise AssertionError("required rejection missing")


def dump(node):
    return ast.dump(node, include_attributes=False)


def function(path, name):
    nodes = [node for node in ast.parse(path.read_bytes()).body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(nodes) == 1, "one original function required")
    return copy.deepcopy(nodes[0])


def main():
    targets = {relative(BRIDGE / name): digest for name, digest in EXPECTED.items()}
    before = {path: sha(ROOT / path) for path in targets}
    require(before == targets, "issued review target differs")
    spec = importlib.util.spec_from_file_location("independent_force_bridge_structure_v2", BRIDGE / "review-fix-v2/bridge.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    frozen = wrapper.frozen()  # Import only: no preparation, panel bank or solve.
    pins = wrapper.source_pins()
    checks = []

    for name, digest in frozen.REUSED.items():
        require(pins[relative(frozen.PACKET / name)] == digest, "reused source outside runtime closure")
    require(pins[relative(wrapper.OWN)] == targets[relative(wrapper.OWN)]
            and pins[relative(wrapper.FROZEN)] == wrapper.FROZEN_SHA,
            "both wrapper and genuine original must remain source-bound")
    checks.append("All five directly reused sources, the frozen bridge and wrapper are runtime-pinned.")

    originals = {name: getattr(frozen, name) for name in ("OWN", "LOADED_SHA", "source_pins", "compile_function")}
    original_ast = frozen.old_gate.ast
    with wrapper.corrected_context(frozen):
        require(frozen.OWN == wrapper.OWN and frozen.LOADED_SHA == wrapper.LOADED_SHA,
                "active wrapper provenance missing")
        rejected(lambda: wrapper.corrected_context(frozen).__enter__(), ValueError, "unnested and serialized")
    try:
        with wrapper.corrected_context(frozen):
            raise RuntimeError("inert interruption")
    except RuntimeError:
        pass
    require(all(getattr(frozen, name) is value for name, value in originals.items())
            and frozen.old_gate.ast is original_ast
            and frozen.factory.SCHEMA == frozen.ORIGINAL_SCHEMA
            and frozen.factory.read_inputs is frozen.ORIGINAL_READ
            and frozen.factory.authenticate_source_review is frozen.ORIGINAL_AUTHENTICATE,
            "serialized hooks escaped their context")
    checks.append("Nested context rejects; normal and interrupted exits restore genuine source and factory bindings.")

    captured = []
    def capture_compile(tree, *args, **kwargs):
        captured.append(copy.deepcopy(tree))
        return builtins.compile(tree, *args, **kwargs)
    with patch.object(wrapper, "compile", side_effect=capture_compile, create=True):
        result = wrapper.corrected_run_function(frozen, object())
    require(callable(result) and len(captured) == 1, "one deferred current producer required")
    expected = function(wrapper.FROZEN, "run_case")
    body = []
    replaced = inserted = 0
    for node in expected.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) \
                and node.value.func.id == "require" and len(node.value.args) == 2 \
                and isinstance(node.value.args[1], ast.Constant) \
                and node.value.args[1].value == "preserve every existing current field/operator/failure":
            body.append(ast.parse("verify_reserved_outputs(paths)").body[0])
            replaced += 1
        else:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) and node.value.func.id == "methods":
                body.append(ast.parse("preauthenticate(args, method)").body[0])
                inserted += 1
            body.append(node)
    expected.body = body
    require((replaced, inserted) == (1, 1) and dump(captured[0].body[0]) == dump(expected),
            "producer changed beyond reserved output and early-review hooks")
    checks.append("Independent AST comparison finds exactly two producer orchestration hooks; preparation, snapshot, solve and recovery statements remain identical.")

    captured.clear()
    with wrapper.corrected_context(frozen), patch.object(frozen, "compile", side_effect=capture_compile, create=True):
        compiled = frozen.admission_functions()
    require(set(compiled) == {"require_pending_field", "audit", "require_admitted_payload"}
            and len(captured) == 3, "three genuine admission functions required")
    for tree in captured:
        actual = tree.body[0]
        expected = function(frozen.old_gate.OWN, actual.name)
        if actual.name in {"audit", "require_admitted_payload"}:
            for node in ast.walk(expected):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    node.value = {"reused_raised_method_input": "current_method_input",
                                  "fixed_floor_execution": "current_execution"}.get(node.value, node.value)
        require(dump(actual) == dump(expected), "independent admission arithmetic changed")
    require(any(isinstance(n, ast.Constant) and n.value == 1e-5 for n in ast.walk(captured[0])),
            "original inclusive residual tolerance missing")
    checks.append("Independent AST comparison preserves all three admission functions except declared provenance-key replacements, including the 1e-5 tolerance.")

    compiler_pins = frozen.review_fix_compiler_sources
    require(all(sha(path) == digest for path, digest in compiler_pins.items()), "compiler source whitelist differs")
    with tempfile.TemporaryDirectory(prefix="inert-", dir=OWN.parent) as directory:
        temp = Path(directory)
        foreign = temp / "foreign.py"
        foreign.write_text("def foreign(): return 1\n")
        rejected(lambda: wrapper.compile_function(frozen, foreign, "foreign", {}), ValueError, "not a reviewed original")
        callback_count = []
        def interrupted_import():
            callback_count.append(True)
            raise RuntimeError("inert import failure")
        output = temp / "attempt.json"
        with patch.object(wrapper, "frozen", side_effect=interrupted_import):
            rejected(lambda: wrapper.main(["--out", str(output)]), RuntimeError, "inert import failure")
            failed = json.loads(output.read_bytes())
            rejected(lambda: wrapper.main(["--out", str(output)]), FileExistsError, "")
        require(len(callback_count) == 1 and failed["status"] == "FAILED"
                and failed["accepted_q"] is None and failed["accepted_actions"] is None
                and not any(failed["release"].values()), "failed attempt was reusable or accepted")
    checks.append("Compiler rejects an unreviewed source; failed import retains an exclusive, nonaccepted attempt and retry refuses before callback.")

    preflight = json.loads((BRIDGE / "review-fix-v2/source-preflight.json").read_bytes())
    manifest_ref = preflight["provided"]["source_manifest"]
    export_ref = preflight["provided"]["source_export"]
    metadata_before = {ref["path"]: sha(ROOT / ref["path"]) for ref in (manifest_ref, export_ref)}
    require(metadata_before == {ref["path"]: ref["sha256"] for ref in (manifest_ref, export_ref)},
            "descriptor/parent metadata differs")
    manifest = json.loads((ROOT / manifest_ref["path"]).read_bytes())
    exported = json.loads((ROOT / export_ref["path"]).read_bytes())
    require(manifest["readiness"]["candidate_assembly_or_solve"] is False
            and manifest["readiness"]["independent_current_field_admission"] is False
            and exported["candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed"] is False
            and not any(exported["release"].values())
            and preflight["missing"] == ["inputs", "input_review", "method_input"]
            and preflight["production_readiness_claimed"] is False
            and not any(preflight["release"].values()), "source metadata was elevated into mechanical readiness")
    checks.append("Exact descriptor metadata and descriptor-only parent authority retain missing input/review/method gates and all release claims false.")

    after = {path: sha(ROOT / path) for path in targets}
    require(after == before and wrapper.source_pins() == pins
            and {path: sha(ROOT / path) for path in metadata_before} == metadata_before,
            "review source changed")
    result = {
        "schema": "eoere_current_force_bridge_independent_structure_review/v2",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_OWNERSHIP_RETENTION_SCOPE",
        "substantial_findings": [],
        "reviewer_source": {"path": relative(OWN), "sha256": sha(OWN)},
        "target_source_sha256_before": before,
        "target_source_sha256_after": after,
        "runtime_source_sha256": pins,
        "metadata_source_sha256": metadata_before,
        "source_pins_before_after_unchanged": True,
        "checks": checks,
        "architecture": {
            "ownership": "Wrapper owns early authentication, output reservation and current provenance; frozen factory/runner/replay modules retain numerical ownership.",
            "coupling": "Scoped mutable module hooks and private AST compilation require the declared single-process serialized context. This review does not claim thread-safe concurrent execution.",
            "dataflow": "Current descriptor metadata joins feed independently reviewed raw/selected inputs; exact method readiness and a parent slot precede panel dependencies/preparation; own snapshots precede a fresh solve; separate saved-field admission follows.",
            "reuse": "Older module paths are active implementation dependencies, not inherited geometry, force, resistance or release acceptance.",
        },
        "retention": {
            "active": "Original four files, corrected four files, runtime source closure, current descriptor/authority/panel metadata and issued reviews remain active. Future operator snapshots, candidate fields, admissions and failed attempts must remain recoverable.",
            "archive_or_prune_performed": False,
            "shared_edits_staging_or_commits_performed": False,
            "retained_owned_artifacts": [relative(OWN), relative(OWN.with_name("receipt.json"))],
        },
        "limits": [
            "No actual current input construction, current panel bank/preparation, frame K, candidate q/forces, solver, CAD/BRep reader or browser was executed.",
            "Review uses exact source/JSON metadata and inert synthetic callbacks; actual numerical admission and parent readiness remain unperformed.",
            "No-slip floor support remains an unverified analytical assumption. No complete joint resistance or physical/fabrication/climbing acceptance is established.",
        ],
        "release": dict(wrapper.RELEASE),
    }
    with OWN.with_name("receipt.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
