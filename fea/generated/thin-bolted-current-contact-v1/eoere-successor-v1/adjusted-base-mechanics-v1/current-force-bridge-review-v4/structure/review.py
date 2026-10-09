"""Independent architecture/source/retention review; metadata and inert flows."""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
TARGET = MECH / "current-force-bridge-v1/preflight-fix-v4"
EXPECTED = {
    "preflight.py": "244f441114f3215d82e45d55403da5cfb2417d9b996779bcb5291188c2cd7ad2",
    "test_preflight.py": "ffb459d39cc7855ca4fb3f597bc025ab2f7553486666008e374c691cdf1ecbae",
    "all-bindings.json": "3f80b1185b88812d18219b1cea2ed2c1dee3cb8b323f2dafc72558f3e554f8d4",
    "verification.json": "afc71138a185b23eba2fa2d4d8947691446226814ea0c5f6223d1f08b735ab59",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    helper_path = MECH / "current-force-bridge-review-v2/structure/review.py"
    h = load(helper_path, "inert_force_structure_helpers_v4")
    before = {h.relative(TARGET / name): h.sha(TARGET / name) for name in EXPECTED}
    h.require(before == {h.relative(TARGET / name): digest for name, digest in EXPECTED.items()}, "issued v4 source differs")
    supplement = load(TARGET / "preflight.py", "independent_method_binding_structure_v4")
    previous = supplement.previous()
    wrapper = previous.corrected()  # These three modules import stdlib only.
    inherited = {**previous.frozen_pins(wrapper), **supplement.frozen_pins()}
    verification = json.loads((TARGET / "verification.json").read_bytes())
    preserved = dict(verification["frozen_original_corrected_v3_and_review_sources"])
    v3_verification = json.loads(supplement.V3.with_name("verification.json").read_bytes())
    preserved.update(v3_verification["preserved_source_sha256"])
    h.require(all(h.sha(ROOT / path) == digest for path, digest in preserved.items()), "issued or failed evidence changed")
    checks = ["Exact v4 files, frozen v3 and original/corrected source files, prior reviews, and original failed preflight/process/log hashes match."]

    tree = ast.parse((TARGET / "preflight.py").read_bytes())
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    h.require(names == {"frozen_pins", "previous", "method_reference_bindings", "preflight", "main"}
              and not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                          and node.func.id in {"exec", "compile", "patch"} for node in ast.walk(tree)),
              "v4 takes over compiler or numerical ownership")
    h.require(supplement.REFERENCE_KEYS == ("inputs", "input_review", "source_manifest", "panel_bank", "source_export"),
              "five-reference contract differs")
    checks.append("V4 is an equality adapter with no AST compiler, numerical functions or authentication-policy replacement; v3 and491653 retain their existing responsibilities.")

    with tempfile.TemporaryDirectory(prefix="inert-", dir=OWN.parent) as directory:
        temp = Path(directory)
        refs = {key: {"path": h.relative(temp / key), "sha256": "a"*64} for key in supplement.REFERENCE_KEYS}
        geometry = {"report": {"path": "synthetic_geometry", "sha256": "b"*64},
                    "source_manifest": refs["source_manifest"], "cached_source_export": refs["source_export"]}
        method_ref = {"path": h.relative(temp / "method"), "sha256": "c"*64}
        method = {"input": refs["inputs"], "input_review": refs["input_review"], "geometry": geometry["report"],
                  "source_manifest": refs["source_manifest"], "panel_bank": refs["panel_bank"], "input_record": method_ref}
        args = SimpleNamespace(mode="preflight", run=False, method_input=ROOT / method_ref["path"],
            method_input_sha256=method_ref["sha256"], **{key: ROOT / ref["path"] for key, ref in refs.items()},
            **{key + "_sha256": ref["sha256"] for key, ref in refs.items()})
        events = []
        def read_method(path, digest):
            h.require(path == args.method_input and digest == args.method_input_sha256, "wrong synthetic method")
            events.append("read_method")
            return method
        b = SimpleNamespace(bundle=SimpleNamespace(artifact_path=h.relative), require=wrapper.require,
                            read_method=read_method, read_ref=lambda ref: {"geometry": geometry},
                            source_pins=lambda extra=None: dict(extra or {}))
        def preserved_preflight(actual, actual_wrapper, actual_bridge):
            h.require(actual is args and actual_wrapper is wrapper and actual_bridge is b, "delegation differs")
            events.append("preserved_v3_preflight")
            return {"source_sha256": {}, "missing": [], "production_readiness_claimed": False,
                    "release": dict(wrapper.RELEASE)}
        s = SimpleNamespace(preflight=preserved_preflight)
        full = supplement.preflight(args, s, wrapper, b)
        h.require(events == ["read_method", "preserved_v3_preflight"]
                  and full["method_reference_bindings"]["checked"] == refs
                  and full["method_reference_bindings"]["complete"] is True, "binding gate does not precede v3")
        negative_count = 0
        for key in supplement.REFERENCE_KEYS:
            for change in ("path", "sha256"):
                altered = copy.deepcopy(args)
                if change == "path":
                    setattr(altered, key, temp / (key + "-different-path"))
                else:
                    setattr(altered, key + "_sha256", "d"*64)
                events.clear()
                h.rejected(lambda altered=altered: supplement.preflight(altered, s, wrapper, b), ValueError,
                           "supplied " + key + " reference differs from method binding")
                h.require(events == ["read_method"], "reference mismatch reached v3")
                negative_count += 1
        checks.append("Ten synthetic path/hash mismatches across all five references reject before preserved v3; the exact synthetic flow delegates after the method gate.")

        no_method = copy.deepcopy(args)
        no_method.method_input_sha256 = None
        partial = supplement.method_reference_bindings(no_method, b)
        h.require(partial["method_provided"] is False and partial["complete"] is False
                  and partial["checked"] == {} and partial["unchecked"] == list(supplement.REFERENCE_KEYS),
                  "incomplete method reference overstated")
        one_missing = copy.deepcopy(args)
        one_missing.inputs_sha256 = None
        partial = supplement.method_reference_bindings(one_missing, b)
        h.require(partial["method_provided"] is True and partial["complete"] is False
                  and partial["unchecked"] == ["inputs"] and "inputs" not in partial["checked"],
                  "incomplete supplied reference overstated")
        checks.append("Partial method/hash references remain unchecked with complete=false; only complete supplied references enter the checked set.")

        output = temp / "failed.json"
        attempts = []
        def interrupted_import():
            attempts.append(True)
            raise RuntimeError("inert frozen import failure")
        with patch.object(wrapper, "frozen", side_effect=interrupted_import):
            h.rejected(lambda: supplement.main(["--out", str(output)]), RuntimeError, "inert frozen import failure")
            failure = json.loads(output.read_bytes())
            h.rejected(lambda: supplement.main(["--out", str(output)]), FileExistsError, "")
            dangling = temp / "dangling.json"
            dangling.symlink_to(temp / "absent.json")
            h.rejected(lambda: supplement.main(["--out", str(dangling)]), FileExistsError, "")
        h.require(len(attempts) == 1 and failure["status"] == "FAILED" and failure["accepted_q"] is None
                  and failure["accepted_actions"] is None and not any(failure["release"].values()) and dangling.is_symlink(),
                  "exclusive output or failed retention differs")
        checks.append("The genuine491653 reservation retains a failed import, refuses repeat/dangling outputs before frozen work, and leaves accepted q/actions null.")

    saved = json.loads((TARGET / "all-bindings.json").read_bytes())
    current = saved["provided"]
    h.require(all(saved["source_sha256"].get(path) == digest for path, digest in inherited.items())
              and all(saved["source_sha256"].get(ref["path"]) == ref["sha256"]
                      and h.sha(ROOT / ref["path"]) == ref["sha256"] for ref in current.values()),
              "saved direct source closure omits inherited or supplied references")
    method = json.loads((ROOT / current["method_input"]["path"]).read_bytes())
    inputs = json.loads((ROOT / current["inputs"]["path"]).read_bytes())
    bound = {"inputs": method["input"], "input_review": method["input_review"],
             "source_manifest": method["source_manifest"], "panel_bank": method["panel_bank"],
             "source_export": inputs["geometry"]["cached_source_export"]}
    h.require(saved["method_reference_bindings"] == {"method_provided": True, "method": current["method_input"],
                  "checked": bound, "unchecked": [], "complete": True}
              and bound == {key: current[key] for key in supplement.REFERENCE_KEYS}
              and inputs["geometry"]["report"] == method["geometry"]
              and inputs["geometry"]["source_manifest"] == method["source_manifest"]
              and saved["missing"] == [] and saved["production_readiness_claimed"] is False
              and saved["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
              and not any(saved["release"].values()), "saved reference equality or claim boundary differs")
    checks.append("Saved six supplied bindings match the exact method and input geometry references; transitive source records remain pinned while production/release claims remain false.")

    after = {h.relative(TARGET / name): h.sha(TARGET / name) for name in EXPECTED}
    h.require(before == after and all(h.sha(ROOT / path) == digest for path, digest in preserved.items())
              and inherited == {**previous.frozen_pins(wrapper), **supplement.frozen_pins()}, "frozen bytes changed")
    receipt = {
        "schema": "eoere_method_binding_preflight_independent_structure_review/v4",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_OWNERSHIP_RETENTION_SCOPE", "substantial_findings": [],
        "reviewer_source": {"path": h.relative(OWN), "sha256": h.sha(OWN)},
        "reused_review_helper": {"path": h.relative(helper_path), "sha256": h.sha(helper_path)},
        "target_source_sha256_before": before, "target_source_sha256_after": after,
        "preserved_evidence_sha256": preserved, "source_pins_before_after_unchanged": True,
        "checks": checks, "synthetic_reference_mismatch_count": negative_count,
        "architecture": "V4 adds method-reference equality before the existing v3 source preflight; v3 retains raw-pin propagation, and frozen491653 retains source authentication, output ownership and producer/admission mechanics. No alias mapping or capacity inference is introduced.",
        "retention": {"active": "Original/corrected bridge, v3, prior issued reviews/failures, exact current source/input/review/method/panel bindings, and the v4 supplement remain active.",
                      "archive_or_prune_performed": False, "shared_edits_staging_or_commits_performed": False},
        "limits": ["Only source/JSON metadata and synthetic callbacks were used; genuine source preflight and genuine field consumers were not rerun.",
                   "No current K, preparation, q/actions, solve, native/CAD/BRep work, browser or serialized-slot edits occurred.",
                   "Existing fresh cases and remaining serialized runs are outside this review. Root owns final validation; this source review supplies no mechanics admission, complete joint resistance or physical release."],
        "release": dict(wrapper.RELEASE),
    }
    with OWN.with_name("receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "checks": len(checks), "receipt_sha256": h.sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
