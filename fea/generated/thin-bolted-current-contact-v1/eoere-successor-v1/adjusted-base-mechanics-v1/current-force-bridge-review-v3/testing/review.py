"""Independent preflight-only binding and safe-output review; no candidate mechanics."""
from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").exists())
MECH = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
TARGET = MECH / "current-force-bridge-v1/preflight-fix-v3"
EXPECTED = {TARGET / name: digest for name, digest in {
    "preflight.py": "a557f8ee72a211f809220f5ac25621e2c7a6c0d9fdfdadd94b95cc8d31c0254c",
    "test_preflight.py": "ff06c0b5f2b8d951f72f6f071141633950f82c50c904388ceb3f1386ecfb4334",
    "all-bindings.json": "780b589d2381fa2d469ff075f500f744142207957de1d663b1f8c4c3f801624e",
    "verification.json": "c5348a6100dfb2bae65e52499044a3d41c60a4fe5d351a4d83f46e40bb1107fd",
}.items()}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    return {"path": str(Path(path).relative_to(ROOT)), "sha256": sha(path)}


def write(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return ref(path)


def changed_args(args, **changes):
    result = list(args)
    for name, value in changes.items():
        result[result.index("--" + name.replace("_", "-")) + 1] = str(value)
    return result


def prohibited(*_args, **_kwargs):
    raise AssertionError("source-only preflight reached candidate mechanics")


def run():
    assert {p: sha(p) for p in EXPECTED} == EXPECTED
    spec = importlib.util.spec_from_file_location("independent_preflight_testing_review_v3", TARGET / "preflight.py")
    s = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s)
    w, b = s.corrected(), s.corrected().frozen()
    saved = json.loads((TARGET / "all-bindings.json").read_bytes())
    direct = {**EXPECTED, **s.FROZEN,
              **{ROOT / p: digest for p, digest in s.frozen_pins(w).items()},
              **{ROOT / r["path"]: r["sha256"] for r in saved["provided"].values()}}
    assert {p: sha(p) for p in direct} == direct
    method_path = ROOT / saved["provided"]["method_input"]["path"]
    method = json.loads(method_path.read_bytes())
    method_pins_before = b.base.verify_pins(method["source_sha256"])
    probe_root = OWN.parent / "_probes"
    probe_root.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="attempt-", dir=probe_root))
    process = subprocess.run(["uv", "run", "pytest", "-q", str(TARGET / "test_preflight.py")],
                             cwd=ROOT, check=True, capture_output=True, text=True)
    checks = [{"name": "six_issued_tests", "result": process.stdout.strip()}]
    captured = []
    original_compile = builtins.compile
    def capture(node, *args, **kwargs):
        if isinstance(node, ast.Module):
            captured.append(copy.deepcopy(node))
        return original_compile(node, *args, **kwargs)
    with w.corrected_context(b), patch.object(s, "compile", side_effect=capture, create=True):
        s.compile_preflight(w, b)
    expected = copy.deepcopy(next(n for n in ast.parse(w.FROZEN.read_bytes()).body
                                  if isinstance(n, ast.FunctionDef) and n.name == "preflight"))
    edits = []
    for node in ast.walk(expected):
        if isinstance(node, ast.Assign) and ast.unparse(node) == "data, _ = read_inputs(args.inputs, args.inputs_sha256)":
            node.targets[0].elts[1].id = "input_pins"
            edits.append("retain_returned_pins")
        if isinstance(node, ast.Call) and ast.unparse(node) == "source_pins(data['source_sha256'])":
            node.args[0] = ast.Name(id="input_pins", ctx=ast.Load())
            edits.append("forward_returned_pins")
    assert sorted(edits) == ["forward_returned_pins", "retain_returned_pins"]
    assert len(captured) == 1 and ast.dump(captured[0].body[0]) == ast.dump(ast.fix_missing_locations(expected))
    checks.append({"name": "independent_exact_compiled_AST_comparison", "substitutions": edits})
    argv = []
    for name, source in saved["provided"].items():
        flag = name.replace("_", "-")
        argv += ["--" + flag, str(ROOT / source["path"]), "--" + flag + "-sha256", source["sha256"]]
    argv += ["--mode", "preflight", "--out", str(work / "positive.json")]
    original_load = b.load
    def source_load(path, digest, name):
        module = original_load(path, digest, name)
        if Path(path).resolve() == ROOT / b.PANEL_BANK["path"]:
            module.load_panel_dependencies = prohibited
            module.prepare_panel_operators = prohibited
        return module
    findings = []
    with ExitStack() as stack:
        for item in (patch.object(b, "load", side_effect=source_load),
                     patch.object(b.factory, "prepare", side_effect=prohibited),
                     patch.object(b.frame, "ElasticAssembly", side_effect=prohibited),
                     patch.object(b, "run_case", side_effect=prohibited),
                     patch.object(b, "compile_execute", side_effect=lambda *_: prohibited)):
            stack.enter_context(item)
        assert s.main(argv) == 0
        positive = json.loads((work / "positive.json").read_bytes())
        assert not positive["missing"] and positive["provided"] == saved["provided"]
        assert not positive["production_readiness_claimed"] and not any(positive["release"].values())
        assert positive["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
        checks.append({"name": "genuine_all_six_ref_preflight_with_mechanics_traps", "passed": True})
        review = json.loads((ROOT / saved["provided"]["input_review"]["path"]).read_bytes())
        for name, data, field, value, expected_error in (
            ("review-schema", review, "schema", "foreign-review", "independent current source-input review"),
            ("method-readiness", method, "independent_readiness_pass", False, "method/readiness inputs"),
        ):
            invalid = copy.deepcopy(data)
            invalid[field] = value
            source = write(work / (name + ".json"), invalid)
            argname = "input_review" if name.startswith("review") else "method_input"
            out = work / (name + "-failure.json")
            actual = changed_args(argv, out=out, **{argname: ROOT / source["path"], argname + "_sha256": source["sha256"]})
            try:
                s.main(actual)
            except ValueError as error:
                assert expected_error in str(error), str(error)
            else:
                raise AssertionError("semantically invalid metadata passed")
            failed = json.loads(out.read_bytes())
            assert failed["status"] == "FAILED" and failed["accepted_q"] is None and failed["accepted_actions"] is None
            checks.append({"name": name + "_with_recomputed_hash", "rejected": True})
        # A byte-identical new raw input plus a matching review is valid as an
        # independent input/review pair, but the original method binds old paths.
        duplicate = work / "duplicate-input.json"
        os.link(ROOT / saved["provided"]["inputs"]["path"], duplicate)
        duplicate_ref = ref(duplicate)
        duplicate_review = copy.deepcopy(review)
        duplicate_review["input"] = duplicate_ref
        duplicate_review["source_sha256"][duplicate_ref["path"]] = duplicate_ref["sha256"]
        duplicate_review_ref = write(work / "duplicate-review.json", duplicate_review)
        mismatch_out = work / "method-mismatch.json"
        mismatch = changed_args(argv, inputs=duplicate, inputs_sha256=duplicate_ref["sha256"],
                                input_review=ROOT / duplicate_review_ref["path"],
                                input_review_sha256=duplicate_review_ref["sha256"], out=mismatch_out)
        assert method["input"] != duplicate_ref and method["input_review"] != duplicate_review_ref
        mismatch_code = s.main(mismatch)
        mismatch_result = json.loads(mismatch_out.read_bytes())
        assert mismatch_code == 0 and mismatch_result["missing"] == []
        findings.append({"priority": "P2", "title": "All-bindings preflight accepts an input/review pair different from the method's bound pair",
            "path": str((TARGET / "preflight.py").relative_to(ROOT)), "line": 85,
            "inherited_path": str(w.FROZEN.relative_to(ROOT)), "inherited_line": 509,
            "impact": "A successful complete preflight does not establish the exact input/review/method relationship required at producer entry; launching these supplied refs fails the preserved producer's line-363 method-binding check before preparation.",
            "reproduction": "Byte-identical raw-input hardlink and matching independent-review copy, with recomputed exact hashes; retain genuine original method/source/export/panel refs. Supplement exits zero with missing=[] even though method.input and method.input_review differ from provided refs.",
            "fix": "At preflight-only orchestration, require read_method(...).input/input_review to equal the supplied validated input/review refs, and add this recomputed-hash mismatch negative control. Preserve producer/admission bytes.",
            "evidence": str(mismatch_out.relative_to(ROOT))})
        checks.append({"name": "mismatched_method_binding_negative_control", "unexpected_success": True,
                       "exit_code": mismatch_code, "missing": mismatch_result["missing"]})
    after = {p: sha(p) for p in direct}
    assert after == direct
    assert b.base.verify_pins(method["source_sha256"]) == method_pins_before
    receipt = {"schema": "eoere_preflight_supplement_testing_review/v3", "status": "SUBSTANTIAL_FINDING_CONFIRMED" if findings else "CLEAN",
        "substantial_findings": findings, "checks": checks, "source_hashes_before_after_unchanged": True,
        "source_sha256": {str(p.relative_to(ROOT)): digest for p, digest in direct.items()},
        "full_method_source_pin_count": len(method_pins_before),
        "full_method_source_pin_map_sha256": b.canonical(method_pins_before),
        "review_path": str(OWN.relative_to(ROOT)), "review_sha256": sha(OWN), "probe_directory": str(work.relative_to(ROOT)),
        "candidate_preparation_K_solve_CAD_BRep_browser_or_heavy_work_performed": False,
        "release": copy.deepcopy(b.core.RELEASE),
        "retention": {"active": "review helper, receipt and owned ignored metadata fixtures; duplicate raw input is a read-only hardlink",
                      "archive_prune_staging_or_commit_performed": False}}
    receipt_path = OWN.with_name("receipt.json")
    assert not receipt_path.exists(), "preserve issued testing review"
    write(receipt_path, receipt)
    print(json.dumps({"receipt": str(receipt_path), "sha256": sha(receipt_path), "findings": len(findings)}))


if __name__ == "__main__":
    run()
