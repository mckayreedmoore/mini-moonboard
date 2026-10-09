"""Independent static architecture review with one owned source-drift fixture."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path.cwd()
OWN = Path(__file__).resolve().relative_to(ROOT)
PACKET = Path("fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1")
RAW = PACKET / "adjusted-base-mechanics-v1/current-force-bridge-v1"
TARGETS = {
    "bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    out = OWN.parent / "receipt.json"
    assert not out.exists(), "preserve completed review receipts"
    paths = [OWN, Path("AGENTS.md"), Path("docs/wood-joints-mvp/README.md")]
    paths += [RAW / name for name in TARGETS]
    paths += [PACKET / path for path in [
        "floor-practical-resolution-v1/runner.py", "floor-practical-resolution-v1/admission.py",
        "floor-practical-resolution-v1/support_law.py", "raised-rail-execution-v1/driver.py",
        "raised-rail-cases-v1/cases.py", "four-port-method-v1/first_order_admission.py",
        "four-port-method-v1/operator_bundle.py", "four-port-method-v1/run_first_order.py",
    ]]
    sources = {str(path): path.read_bytes() for path in paths}
    pins = {path: sha(data) for path, data in sources.items()}
    for name, expected in TARGETS.items():
        assert pins[str(RAW / name)] == expected
    preflight = json.loads(sources[str(RAW / "source-preflight.json")])
    verification = json.loads(sources[str(RAW / "verification.json")])
    gate_path = str(PACKET / "floor-practical-resolution-v1/admission.py")
    assert gate_path not in preflight["source_sha256"]
    # Import from an owned sibling working directory, with bytecode writes off.
    try:
        os.chdir(ROOT / OWN.parent)
        spec = importlib.util.spec_from_file_location("eoere_architecture_bridge_fixture", ROOT / RAW / "bridge.py")
        b = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(b)
    finally:
        os.chdir(ROOT)
    initial_pins = b.source_pins()
    assert gate_path not in initial_pins
    restored = False
    try:
        with b.factory_boundary():
            assert b.factory.SCHEMA == b.INPUT_SCHEMA
            try:
                with b.factory_boundary():
                    raise AssertionError("nested override should reject")
            except ValueError:
                pass
            raise RuntimeError("owned context cleanup fixture")
    except RuntimeError:
        restored = (b.factory.SCHEMA == b.ORIGINAL_SCHEMA
                    and b.factory.read_inputs is b.ORIGINAL_READ
                    and b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE)
    assert restored
    # Reuse only the tiny fixture function; no current descriptor/operator load.
    tree = ast.parse(sources[str(RAW / "test_bridge.py")])
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "fixture_field")
    context = {"b": b}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "owned-tiny-pending-field", "exec"), context)
    field = context["fixture_field"]()
    field["response"].update(gradient_n=[1e-3], gradient_inf_n=1e-3,
        gradient_canonical_sha256=b.canonical([1e-3]))
    original_rejected = False
    try:
        b.admission_functions()["require_pending_field"](field)
    except ValueError:
        original_rejected = True
    assert original_rejected
    original = sources[gate_path].decode()
    assert original.count("<= 1e-5") == 1
    changed = original.replace("<= 1e-5", "<= 1e-2")
    # This redirects the reread to a changed owned copy, never the genuine file.
    with tempfile.TemporaryDirectory(prefix="source-copy-", dir=ROOT / OWN.parent) as directory:
        copy_path = Path(directory) / "admission-copy.py"
        copy_path.write_text(changed)
        with patch.object(b.old_gate, "OWN", copy_path):
            b.admission_functions()["require_pending_field"](field)
            unchanged_pins_with_changed_compiled_dependency = b.source_pins() == initial_pins
    assert unchanged_pins_with_changed_compiled_dependency
    assert b.source_pins() == initial_pins
    assert not verification["candidate_CAD_panel_K_global_K_q_actions_native_solve_or_admission_performed"]
    assert not verification["production_readiness_claimed"]
    assert not any(verification["release"].values())
    receipt = {
        "schema": "eoere_current_force_bridge_architecture_review/v1",
        "status": "ONE_SUBSTANTIAL_SOURCE_INTEGRITY_FINDING",
        "source_sha256": pins,
        "findings": [{
            "id": "ARCH-SOURCE-01", "severity": "P2",
            "title": "Pin and reauthenticate the admission source before recompiling it",
            "location": {"path": str(RAW / "bridge.py"), "line": 85},
            "related_location": {"path": str(RAW / "bridge.py"), "line": 436},
            "evidence": "source_pins delegates to old_runner.source_pins and adds the bridge/method records, but not the reused floor admission.py. The issued 25-pin preflight closure omits that file. Its REUSED digest is checked only on import; admission_functions later reparses old_gate.OWN through compile_function without hashing those just-read bytes. read_method does not require that dependency in its source closure.",
            "impact": "A post-import admission-source change is outside the bridge's before/after source checks, while its changed body can be freshly compiled and used for current field admission. The frozen bridge identity and unchanged source map can therefore describe altered admission mathematics.",
            "concrete_fix": "In a separately identified revision, merge every REUSED source and expected digest into source_pins, including floor admission.py. Also authenticate the exact bytes read by compile_function against the expected frozen source digest before AST parsing. Keep this issued bridge and review frozen; revalidate only source hooks and tiny fixtures before any future genuine input/run work.",
        }],
        "owned_fixture": {
            "standalone_import_from_sibling_directory": True,
            "factory_hooks_restored_after_exception_and_nested_context_rejected": restored,
            "original_gate_rejects_1e_minus3_gradient": original_rejected,
            "owned_admission_copy_with_1e_minus2_cutoff_compiles_and_accepts_same_tiny_field": True,
            "bridge_source_pins_remain_identical_during_owned_source_copy_redirect": unchanged_pins_with_changed_compiled_dependency,
            "genuine_admission_source_changed": False,
            "interpretation": "The owned path redirect models a changed reread dependency after bridge import. It demonstrates the missing binding without modifying the genuine frozen source or creating a candidate field, operator, response or admission.",
        },
        "architecture_assessment": [
            {"source": str(RAW / "bridge.py") + ":189", "assessment":
             "The narrow factory context changes schema/read/review hooks, rejects nesting and restores originals on failure. Actual preparation remains deferred and parent-serialized."},
            {"source": str(RAW / "bridge.py") + ":231", "assessment":
             "Latest OFF geometry, parent manifest, input review, method and panel-bank identities have separate contracts. Production mode additionally requires a parent marker and exact input/method slot authorization."},
            {"source": str(RAW / "bridge.py") + ":358", "assessment":
             "Fields, operator companions and failed outputs are prechecked as a group and written exclusively. Failure receipts retain phase/events with null accepted q/actions; no evidence is pruned or relabeled."},
            {"source": str(RAW / "bridge.py") + ":473", "assessment":
             "Source preflight compiles private hooks but does not prepare candidate operators. The frozen verification explicitly reports missing genuine current inputs/review/method/export and no production readiness, demands, solve or admission."},
        ],
        "limits": [
            "This is architecture/source/retention review, not method, current-input or panel qualification. Genuine current descriptors, cases, panel/frame K, q, actions, native solves and actual field admission were never run.",
            "Only standalone import, source pin reads, context restoration and an owned tiny pending-field/source-copy fixture ran. The reported 17 tests/Ruff were inspected, not rerun.",
            "The inherited 1e-5 force tolerance and unverified fixed-rear-leg floor assumption retain their recorded domain. No production or physical approval, acceptance transfer, new demands or blanket sign-off prerequisite."
        ],
        "retention": "Original four-file bridge, old methods and current source contracts remain unchanged and active. Only this exclusive review helper/receipt were retained; the owned temporary source copy was removed.",
        "reproduction_command": [sys.executable, str(OWN)],
    }
    for path, data in sources.items():
        assert Path(path).read_bytes() == data, "reviewed source changed: " + path
    out.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"receipt": str(out), "sha256": sha(out.read_bytes()), "source_count": len(pins), "findings": 1}))


if __name__ == "__main__":
    main()
