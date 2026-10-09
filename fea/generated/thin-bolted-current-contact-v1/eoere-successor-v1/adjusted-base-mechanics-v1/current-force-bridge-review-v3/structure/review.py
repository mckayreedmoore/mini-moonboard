"""Independent source/retention review of the source-only preflight seam."""
from __future__ import annotations

import ast
import builtins
import contextlib
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
MECH = OWN.parents[2]
ROOT = OWN.parents[7]
TARGET = MECH / "current-force-bridge-v1/preflight-fix-v3"
EXPECTED = {
    "preflight.py": "a557f8ee72a211f809220f5ac25621e2c7a6c0d9fdfdadd94b95cc8d31c0254c",
    "test_preflight.py": "ff06c0b5f2b8d951f72f6f071141633950f82c50c904388ceb3f1386ecfb4334",
    "all-bindings.json": "780b589d2381fa2d469ff075f500f744142207957de1d663b1f8c4c3f801624e",
    "verification.json": "c5348a6100dfb2bae65e52499044a3d41c60a4fe5d351a4d83f46e40bb1107fd",
}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    helper_path = MECH / "current-force-bridge-review-v2/structure/review.py"
    h = load(helper_path, "inert_force_structure_helpers_v2")
    before = {h.relative(TARGET / name): h.sha(TARGET / name) for name in EXPECTED}
    h.require(before == {h.relative(TARGET / name): digest for name, digest in EXPECTED.items()}, "issued supplement changed")
    supplement = load(TARGET / "preflight.py", "independent_preflight_structure_v3")
    wrapper = supplement.corrected()  # The wrapper imports standard library only.
    frozen_pins = supplement.frozen_pins(wrapper)
    verification = json.loads((TARGET / "verification.json").read_bytes())
    preserved = verification["preserved_source_sha256"]
    h.require(all(h.sha(ROOT / path) == digest for path, digest in preserved.items()), "preserved evidence differs")
    checks = ["Exact supplement, original/corrected sources, prior issued reviews and original failed preflight/process/log hashes match."]

    captured = []
    def capture(tree, *args, **kwargs):
        captured.append(copy.deepcopy(tree))
        return builtins.compile(tree, *args, **kwargs)
    with patch.object(supplement, "compile", side_effect=capture, create=True):
        supplement.compile_preflight(wrapper, SimpleNamespace())
    h.require(len(captured) == 1, "one source-only function required")
    expected = h.function(wrapper.FROZEN, "preflight")
    counts = [0, 0]
    for node in ast.walk(expected):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple) \
                and [getattr(part, "id", None) for part in node.targets[0].elts] == ["data", "_"]:
            node.targets[0].elts[1].id = "input_pins"
            counts[0] += 1
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "source_pins" \
                and len(node.args) == 1 and isinstance(node.args[0], ast.Subscript) \
                and isinstance(node.args[0].value, ast.Name) and node.args[0].value.id == "data" \
                and isinstance(node.args[0].slice, ast.Constant) and node.args[0].slice.value == "source_sha256":
            node.args[0] = ast.Name(id="input_pins", ctx=ast.Load())
            counts[1] += 1
    h.require(counts == [1, 1] and h.dump(captured[0].body[0]) == h.dump(expected), "change exceeds the two source-pin substitutions")
    checks.append("Independent AST comparison finds exactly two pin-dataflow substitutions; authentication calls, source policy, bank metadata checks and result semantics are otherwise identical.")

    with tempfile.TemporaryDirectory(prefix="inert-", dir=OWN.parent) as directory:
        temp = Path(directory)
        files = {}
        for name in ("inputs", "input_review", "method_input", "source_export", "source_manifest", "panel_bank"):
            path = temp / (name + ".json")
            path.write_text(json.dumps({"synthetic": name}))
            files[name] = {"path": h.relative(path), "sha256": h.sha(path)}
        args = SimpleNamespace(mode="preflight", run=False)
        for name, ref in files.items():
            setattr(args, name, ROOT / ref["path"])
            setattr(args, name + "_sha256", ref["sha256"])
        geometry = {"synthetic": "latest"}
        data = {"source_sha256": {"synthetic_descriptor": "d"*64}}
        returned_pins = {**data["source_sha256"], files["inputs"]["path"]: files["inputs"]["sha256"],
                         "synthetic_extra_validated_dependency": "e"*64}
        seen = []
        def authenticate(ref, actual, pins):
            h.require(ref == files["input_review"] and actual is data and pins == returned_pins,
                      "validated full raw-input closure lost at authentication")
            seen.append("unchanged_authenticator_received_full_returned_pins")
        def read_ref(ref):
            if ref == files["source_manifest"]:
                return {"geometry": geometry, "readiness": {"candidate_assembly_or_solve": False}}
            if ref == files["source_export"]:
                return {"schema": "eoere_extended_cleat_cached_source_export/v1", "geometry": geometry,
                        "manifest": files["source_manifest"]}
            raise AssertionError("unexpected synthetic reference")
        bank = SimpleNamespace(source_inputs=lambda: {"geometry": geometry, "optional_2026_extra": False},
                               verify_panel_source_inputs=lambda actual: h.require(actual is data, "wrong source view"))
        b = SimpleNamespace(
            source_pins=lambda extra=None: dict(extra or {}), compile_execute=lambda _callback: None,
            admission_functions=dict, bundle=SimpleNamespace(artifact_path=h.relative), require=h.require,
            ROOT=ROOT, frame=SimpleNamespace(sha=h.sha), SOURCE_MANIFEST=files["source_manifest"],
            PANEL_BANK=files["panel_bank"], GEOMETRY=geometry, read_ref=read_ref, load=lambda *_args: bank,
            factory_boundary=contextlib.nullcontext, read_inputs=lambda *_args: (data, returned_pins),
            authenticate_review=authenticate, read_method=lambda *_args: {}, methods=lambda _record: (None, bank),
            INPUT_SCHEMA="synthetic_inputs", REVIEW_SCHEMA="synthetic_review", METHOD_SCHEMA="synthetic_method",
            FIELD_SCHEMA="synthetic_field", ADMISSION_SCHEMA="synthetic_admission",
            law=SimpleNamespace(contract=lambda: {"unverified_floor": True}), core=SimpleNamespace(RELEASE=wrapper.RELEASE))
        result = supplement.compile_preflight(wrapper, b)(args)
        h.require(seen == ["unchanged_authenticator_received_full_returned_pins"] and result["missing"] == []
                  and result["production_readiness_claimed"] is False and not any(result["release"].values()),
                  "synthetic source-only flow differs")
        h.require(files["inputs"]["path"] not in data["source_sha256"], "raw source self-reference was synthesized")
        checks.append("Synthetic six-binding flow passes the complete read_inputs return, including an extra validated dependency, to authentication without adding a self-reference to input data.")

        output = temp / "failed.json"
        events = []
        def interrupted_frozen():
            events.append(True)
            raise RuntimeError("inert frozen import failure")
        with patch.object(wrapper, "frozen", side_effect=interrupted_frozen):
            h.rejected(lambda: supplement.main(["--out", str(output)]), RuntimeError, "inert frozen import failure")
            failure = json.loads(output.read_bytes())
            h.rejected(lambda: supplement.main(["--out", str(output)]), FileExistsError, "")
        h.require(len(events) == 1 and failure["status"] == "FAILED" and failure["accepted_q"] is None
                  and failure["accepted_actions"] is None and not any(failure["release"].values()),
                  "output ownership or failed-attempt retention differs")
        h.rejected(lambda: supplement.preflight(SimpleNamespace(mode="build-inputs", run=False), wrapper, b),
                   ValueError, "source-preflight-only")
        checks.append("The genuine exclusive-output wrapper retains a failed import attempt and refuses its retry before frozen work; the supplement rejects non-preflight modes.")

    saved = json.loads((TARGET / "all-bindings.json").read_bytes())
    refs = saved["provided"]
    h.require(set(refs) == {"inputs", "input_review", "method_input", "source_export", "source_manifest", "panel_bank"}
              and all(saved["source_sha256"].get(ref["path"]) == ref["sha256"]
                      and h.sha(ROOT / ref["path"]) == ref["sha256"] for ref in refs.values())
              and all(saved["source_sha256"].get(path) == digest for path, digest in frozen_pins.items()),
              "saved result omits a current provided or frozen pin")
    method = json.loads((ROOT / refs["method_input"]["path"]).read_bytes())
    h.require(method["input"] == refs["inputs"] and method["input_review"] == refs["input_review"]
              and method["source_manifest"] == refs["source_manifest"] and method["panel_bank"] == refs["panel_bank"]
              and saved["missing"] == [] and saved["production_readiness_claimed"] is False
              and saved["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
              and saved["historical_q_forces_or_acceptance_transferred"] is False and not any(saved["release"].values()),
              "saved source pass elevated authority or changed method bindings")
    checks.append("Saved output contains all six exact current bindings plus frozen source pins; method input/review/panel/manifest identities agree and source success retains production/release claims false.")

    after = {h.relative(TARGET / name): h.sha(TARGET / name) for name in EXPECTED}
    h.require(after == before and all(h.sha(ROOT / path) == digest for path, digest in preserved.items())
              and supplement.frozen_pins(wrapper) == frozen_pins, "sources changed during review")
    receipt = {
        "schema": "eoere_preflight_only_supplement_independent_structure_review/v3",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_OWNERSHIP_RETENTION_SCOPE",
        "substantial_findings": [], "reviewer_source": {"path": h.relative(OWN), "sha256": h.sha(OWN)},
        "reused_review_helper": {"path": h.relative(helper_path), "sha256": h.sha(helper_path)},
        "target_source_sha256_before": before, "target_source_sha256_after": after,
        "preserved_evidence_sha256": preserved, "source_pins_before_after_unchanged": True,
        "checks": checks,
        "architecture": "A source-only adapter changes pin flow in one frozen preflight function. The frozen491653 producer/admission remains the mechanical owner; its reservation owns attempts. Full validated read_inputs pins reach the existing authenticator without source aliases or synthesized raw-input identity.",
        "retention": {"active": "Original/corrected bridge, issued reviews, failed original preflight/process/log, current source/input/review/method/panel bindings and all supplement files remain active.",
                      "archive_or_prune_performed": False, "shared_edits_staging_or_commits_performed": False},
        "limits": ["Only source/JSON metadata and synthetic source callbacks were inspected or executed; no genuine preflight was repeated.",
                   "No current preparation, panel/frame K, q/forces, solve, CAD/BRep reader, browser or force slot was run/opened.",
                   "The saved source preflight passes within its declared scope; this review supplies no parent run authorization, numerical field admission, complete joint resistance or physical release."],
        "release": dict(wrapper.RELEASE),
    }
    with OWN.with_name("receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "checks": len(checks), "receipt_sha256": h.sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
