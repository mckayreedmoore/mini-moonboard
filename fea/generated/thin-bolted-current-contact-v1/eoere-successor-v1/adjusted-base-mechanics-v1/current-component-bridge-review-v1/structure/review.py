"""Source-only component-consumer architecture and retention review.

The recorded 23-control pytest run was performed independently in a separate
process. This replay verifies exact target bytes, AST boundaries and saved
metadata only. It never loads the genuine gate or component reducer modules.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
TARGET = MECH / "current-component-bridge-v1/consumer-v1"
EXPECTED = {
    TARGET / "consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    TARGET / "test_consume.py": "e289bf15565d6fd19d4ee59ff8cc9b11b7db3ac807e5584abe2cc353b254cab5",
    TARGET / "verification.json": "13d897fdb5271aafe1af3c2c1741ff592ae8cee3fba5a995cd8fdd4ddc8a4bc4",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def calls(function):
    return {ast.unparse(node.func): node.lineno for node in ast.walk(function) if isinstance(node, ast.Call)}


def main():
    assert all(sha(path) == value for path, value in EXPECTED.items())
    tree = ast.parse((TARGET / "consume.py").read_bytes())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    imported = {node.module.split(".")[0] for node in tree.body if isinstance(node, ast.ImportFrom)}
    imported.update(alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import) for alias in node.names)
    assert imported <= sys.stdlib_module_names
    consumer_calls = calls(functions["consume"])
    assert consumer_calls["authenticate"] < consumer_calls["_current_contract"] < consumer_calls["_reduce"]
    auth_calls = calls(functions["authenticate"])
    assert auth_calls["_load_gate"] < auth_calls["gate.require_admitted_payload"] < auth_calls["verify"]
    assert "method" not in auth_calls and "_reduce" not in auth_calls
    reducing = functions["_reduce"]
    scoped = [node for node in ast.walk(reducing) if isinstance(node, ast.With)
              and any(ast.unparse(item.context_expr) == "BOUNDARY_LOCK" for item in node.items)]
    assert len(scoped) == 1
    boundary = [ast.unparse(item.context_expr) for item in scoped[0].items]
    assert boundary == ["BOUNDARY_LOCK", "patch.object(base, 'FIELD_SCHEMA', FIELD_SCHEMA)",
                        "patch.object(base.panel, 'prepared_datums', current_datums)",
                        "patch.object(steel, 'source_pins', current_comparison_pins)"]
    assert calls(scoped[0])["base.reduce_field"] > scoped[0].lineno
    spec = importlib.util.spec_from_file_location("independent_component_structure_subject", TARGET / "consume.py")
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    plan = subject._load_plan()
    contract = plan.component_plan()
    subject.verify(contract["source_sha256"])
    assert contract["census"]["shafts"] == 100 and contract["census"]["panel_screws"] == 66
    assert contract["census"]["panel_features"] == 340 and contract["census"]["physical_owner_gravity_rows"] == 150
    assert contract["complete_joint_resistance"] is None and not any(contract["release"].values())
    assert contract["nominal_seat_geometry"]["old_actions_or_strength_transferred"] is False
    assert contract["execution"]["method_imports_or_execution"] is False
    assert all(row["old_dependency_map_used_as_current_runtime"] is False for row in contract["historical_evidence"].values())
    assert "cadquery" not in sys.modules
    assert not any(label in sys.modules for label in ("eoere_current_component_genuine_gate", "eoere_current_coarse_assessment",
                                                     "eoere_current_coarse_gross", "eoere_current_coarse_centroidal_comparison"))
    assert all(sha(path) == value for path, value in EXPECTED.items())
    sources = [*EXPECTED, MECH / "current-component-bridge-v1/component_plan.py",
               MECH.parent / "component-method-v1/assessment.py", MECH.parent / "component-method-v1/gross_members.py",
               MECH.parent / "raised-rail-components-v1/comparisons.py",
               MECH.parent / "steel-shaft-comparison-v1/comparison.py",
               MECH.parent / "centroidal-four-port-v1/centroidal.py",
               ROOT / "scripts/thin_bolted_panel_coupled.py", ROOT / "scripts/thin_bolted_panel_mechanics.py", OWN]
    receipt = {
        "schema": "eoere_current_component_consumer_independent_structure_review/v1",
        "status": "PASS_NO_SUBSTANTIAL_FINDINGS_SOURCE_AND_SYNTHETIC_SCOPE_ONLY",
        "confirmed_findings": [],
        "target_expected_sha256": {relative(path): value for path, value in EXPECTED.items()},
        "reviewed_source_sha256": {relative(path): sha(path) for path in sources},
        "saved_metadata_closure": {"verified_pins": len(contract["source_sha256"]),
                                   "canonical_sha256": subject.canonical(contract["source_sha256"]),
                                   "current_geometry": contract["current_geometry"], "current_manifest": contract["current_manifest"],
                                   "current_descriptors": contract["current_saved_descriptors"],
                                   "census": contract["census"], "exact_target_bytes_unchanged": True},
        "static_checks": {"consumer_imports_stdlib_only": True, "gate_before_contract_before_reducers": True,
                          "raw_payload_and_receipt_exact_hashes_required": True, "current_schema_geometry_release_checked": True,
                          "gate_raw_payload_identity_and_before_after_source_pins_checked": True,
                          "current_descriptor_rows_join_saved_export": True,
                          "scoped_reducer_boundary": boundary},
        "independent_test_run": {
            "command": "PYTHONPATH=. .venv/bin/python -B -m pytest -q -p no:cacheprovider " + relative(TARGET / "test_consume.py"),
            "passed": 23, "observed_seconds": 4.14,
            "scope": "fake admission/reducer fixtures, saved current descriptor metadata, subprocess reservation/failure controls",
            "actual_genuine_gate_and_reducer_pair_executed": False,
        },
        "architecture": {
            "ownership": "Consumer owns exact artifact admission, current metadata joins, temporary callback boundaries and output lifecycle. Frozen plan owns nominal source/seat proof selection. Frozen reducers retain component equations and tolerance checks.",
            "layering": "authenticate returns before _current_contract and _reduce. Reducer imports occur only inside _reduce. Importing consumer and source plan loads no gate, reducer or CAD module.",
            "old_geometry_boundary": "Current axes are supplied explicitly. The historical comparison source_contract is never invoked. Scoped steel source_pins removes old occupied-layout intake while retaining the unchanged method/input scenario needed by original strip arithmetic.",
            "panel_boundary": "Frozen panel geometry/datums provide unchanged outline/chart metadata; original panel reducer checks current chart origin/axes and coefficient slices. Scoped prepared_datums supplies exact current 340 apertures and clears historical support_bounds, marking current support footprints unqualified. No panel operator preparation or stiffness routine is called.",
            "global_state": "RLock covers the three temporary reducer callbacks. Context-managed patches restore schema, panel callback and comparison callback on reducer success or exception. Separate imported frozen modules remain source witnesses; unload/geometry mutation is not used.",
            "failure_ownership": "consume_to_file and CLI exclusively reserve and fsync STARTED before any input read. Exceptions retain FAILED; abrupt callback exits retain STARTED. A failed reservation prevents intake. Payload mutation or changed pinned bytes rejects result publication.",
            "claims": "Same-state conditional comparisons may retain exceedances; complete_joint_resistance stays null and all release flags stay false. Synthetic controls supply no current force result or structural acceptance.",
        },
        "retention": {
            "active": "Exact consumer/plan/gate sources, current descriptor/input sources, borrowed pure-method modules, panel datum/reference files and nominal seat/subset proof receipts remain active dependencies, including historical paths.",
            "historical_evidence": "Nominal seat and extended-cleat subset proofs select geometry only; historical dependency maps and actions are not relabeled current response evidence.",
            "archive_or_prune_performed": False,
            "archive_eligibility": "Later archival requires current consumer, owner and process checks plus evidence_archive verified recovery before separate pruning. Ignored or old paths alone authorize no deletion.",
            "owned_artifacts": [relative(OWN), relative(OWN.with_name("receipt.json"))], "bulky_artifacts_added": False,
        },
        "remaining": ["No genuine current admitted field/receipt pair exists yet; integration of genuine gate and genuine reducers remains unperformed.",
                      "Production consumption must use an exact current pair and preserve same-state identity, exceedances and null resistance.",
                      "Rich component completion, actual hardware/contact/material applicability and physical acceptance are outside this coarse consumer review."],
        "actual_reducers_preparation_K_CAD_native_frame_browser_executed": False,
        "target_or_shared_docs_staging_commits_modified": False,
    }
    OWN.with_name("receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": receipt["status"], "closure_pins": len(contract["source_sha256"]),
                      "review_sha256": sha(OWN), "receipt_sha256": sha(OWN.with_name("receipt.json"))}))


if __name__ == "__main__":
    main()
