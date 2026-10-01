#!/usr/bin/env python3
"""Reproduce the post-run ID diagnostic without editing frozen acceptance."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("frozen_free_impact_verifier", HERE / "verifier.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
expected, acceptance, reference, helpers = module.load_contract()
assert acceptance["trace_contract"]["map_pressure_law"] == 1
acceptance["trace_contract"]["map_pressure_law"] = 2
result = {
    "schema": "free_impact_law_id_diagnostic/v1",
    "original_frozen_verifier_status": "FAIL",
    "changed_in_memory_only": {"trace_contract.map_pressure_law": {"frozen": 1, "diagnostic": 2}},
    "numerical_tolerances_changed": False, "frozen_files_changed": False,
    "native_rerun": False, "joint_acceptance": False, "release": False,
}
try:
    bound = module.audit_packet_and_outputs(HERE / "output", expected, acceptance)
    cases = {case: module.audit_capture(case, bound["captures"][case], expected,
             acceptance, helpers, helpers["reference_states"]) for case in ("baseline", "trace")}
    cross = module.compare_case_results(cases["baseline"], cases["trace"], expected, acceptance)
    for case in cases.values():
        case.pop("history", None)
        case.pop("pair_resultants", None)
    result.update(status="DIAGNOSTIC_CORRECTED_ID_CHECKS_COMPLETE", cases=cases, cross_case=cross)
except Exception as exc:
    result.update(status="DIAGNOSTIC_FAIL", error=str(exc))
assert json.loads((HERE / "parent-law-id-diagnostic.json").read_text()) == result
print(json.dumps({"status": result["status"], "original_frozen_verifier_status": "FAIL"}))
