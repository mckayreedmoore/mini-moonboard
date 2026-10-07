"""Consume physical-shaft fields through the corrected end-dictionary gate.

All component, wrench and cut methods come from the preserved first helper.
This adapter replaces only admission/orchestration; it performs no solve/CAD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft_steel as methods

ROOT = methods.ROOT
METHOD_HELPER_SHA = "4b28f7a055c50dc127569b7df387f8e8d973f74080d2937ceb5db356a89d9952"
GATE_SHA = "26feb3bb369490729c6f8e48365d816cbda458b2fdeea89a97b8286842d1be58"
METHOD_RECEIPT = methods.PACKET / "common-shaft-steel-method-v4.json"
METHOD_RECEIPT_SHA = "2f29dea742b136f0137c8ddd3691b490e7172332c61ba4a55bdacb4755b7216c"


def require_gate(demand):
    gate_path = ROOT / "scripts/thin_bolted_common_shaft_export_audit.py"
    if GATE_SHA == "UNISSUED" or methods.sha(gate_path) != GATE_SHA:
        raise ValueError("corrected independent end-dictionary gate must be frozen")
    from scripts.thin_bolted_common_shaft_export_audit import audit_common_shaft_state

    result = audit_common_shaft_state(demand)
    if result.get("independent_common_shaft_support_load_and_equilibrium_checks_pass") is not True:
        raise ValueError("corrected independent physical common-shaft gate failed")
    return result, gate_path


def verify_component_state_labels(demand):
    expected = tuple(demand[key] for key in ("state_id", "case_id", "accessory_placement"))
    for name in ("common_shaft_steel_port_actions", "common_shaft_section_cut_actions"):
        for row in demand[name]:
            for labeled in (row, *row.get("cuts", [])):
                if tuple(labeled.get(key) for key in ("state_id", "case_id", "accessory_placement")) != expected:
                    raise ValueError("component aggregate/cut alias mixes or omits admitted state/load identity")


def component_values(demand, caller=None):
    """Reuse frozen unit methods after admission of one immutable parameter state."""
    if methods.sha(Path(methods.__file__)) != METHOD_HELPER_SHA:
        raise ValueError("preserve the reviewed common-shaft component helper")
    if methods.sha(METHOD_RECEIPT) != METHOD_RECEIPT_SHA:
        raise ValueError("preserve the reviewed common-shaft method receipt")
    for path, expected in ((methods.METHODS, methods.METHODS_SHA), (methods.HEAD, methods.HEAD_SHA)):
        if methods.sha(path) != expected:
            raise ValueError("frozen component report changed")
    unit, head = [json.loads(path.read_text()) for path in (methods.METHODS, methods.HEAD)]
    for report in (unit, head):
        for path, expected in report["source_sha256"].items():
            if methods.sha(ROOT / path) != expected:
                raise ValueError("frozen component report dependency changed")
    from scripts.thin_bolted_common_shaft import read_inputs
    from scripts.thin_bolted_steel_resistance import LAYOUT, compare_flange_actions

    ports = methods.aggregate_steel_ports(json.loads(LAYOUT.read_text()), demand["common_shaft_bearing_actions"],
                                          demand["shaft_end_capture_actions"])
    supplied = demand["common_shaft_steel_port_actions"]
    exported = {(r["axis_id"], r["angle_id"], r["flange"]): r for r in supplied}
    if len(ports) != 72 or len(supplied) != 72 or len(exported) != 72:
        raise ValueError("all unique 72 physical steel ports required")
    for port in ports:
        saved = exported[(port["axis_id"], port["angle_id"], port["flange"])]
        for key, tolerance in (("point_xyz_mm", 1e-5), ("force_on_steel_xyz_n", 1e-7),
                               ("moment_on_steel_at_point_xyz_nmm", 1e-4)):
            if np.linalg.norm(methods.vector(saved[key]) - methods.vector(port[key])) > tolerance:
                raise ValueError("producer steel wrench differs from independent own point/couple reduction")
    comparison = compare_flange_actions(methods.api_counterwrenches(ports, demand), demand["flange_contact_actions"])
    for row in comparison["flange_comparisons"]:
        row["nominal_yield_index_covers_exported_torsion"] = row["steel_torsion_complete"]
        row["torsion_omitted_from_nominal_vm_envelope"] = not row["steel_torsion_complete"]
    washers = methods.own_washer_states(unit, head, demand["shaft_end_capture_actions"])
    replay = methods.verify_shaft_cuts(demand, read_inputs())
    shafts = methods.shaft_section_references(demand["common_shaft_section_cut_actions"], caller)
    if len(washers) != 140 or len(shafts) != 70:
        raise ValueError("all 140 own washers and 70 physical shaft references required")
    return {"steel_port_wrenches": ports, "fresh_flange_component_comparison": comparison,
            "own_washer_capture_references": washers, "independent_shaft_cut_replay": replay,
            "shaft_same_section_references": shafts,
            "steel_torsion_unmodeled_flange_count": sum(not r["steel_torsion_complete"] for r in comparison["flange_comparisons"])}


def consume(path: Path, sections_path: Path | None = None) -> dict:
    payload = path.read_bytes()
    input_sha = hashlib.sha256(payload).hexdigest()
    demand = json.loads(payload)
    audit, gate_path = require_gate(demand)
    verify_component_state_labels(demand)
    caller_bytes = sections_path.read_bytes() if sections_path else None
    caller_sha = hashlib.sha256(caller_bytes).hexdigest() if caller_bytes is not None else None
    components = component_values(demand, json.loads(caller_bytes) if caller_bytes is not None else None)
    if (methods.sha(path) != input_sha or methods.sha(gate_path) != GATE_SHA
            or methods.sha(Path(methods.__file__)) != METHOD_HELPER_SHA):
        raise ValueError("state/gate changed during consumption")
    if sections_path and methods.sha(sections_path) != caller_sha:
        raise ValueError("caller section source changed during consumption")
    pins = {str(path.resolve().relative_to(ROOT)): input_sha,
            str(gate_path.relative_to(ROOT)): GATE_SHA,
            str(Path(methods.__file__).relative_to(ROOT)): METHOD_HELPER_SHA,
            str(methods.METHODS.relative_to(ROOT)): methods.METHODS_SHA,
            str(methods.HEAD.relative_to(ROOT)): methods.HEAD_SHA,
            str(METHOD_RECEIPT.relative_to(ROOT)): METHOD_RECEIPT_SHA,
            str(Path(__file__).relative_to(ROOT)): methods.sha(Path(__file__))}
    tests = ROOT / "tests/test_thin_bolted_common_shaft_steel_bound.py"
    pins[str(tests.relative_to(ROOT))] = methods.sha(tests)
    if sections_path:
        pins[str(sections_path.resolve().relative_to(ROOT))] = caller_sha
    return {"schema": "thin_bolted_common_shaft_steel/v2", "candidate": demand["candidate"],
            "state_id": demand["state_id"], "case_id": demand["case_id"],
            "accessory_placement": demand["accessory_placement"], "parameters": demand["parameters"],
            "source_sha256": pins, "producer_source_sha256": demand["source_sha256"],
            "independent_physical_common_shaft_audit": audit, **components,
            "grade5_material_reference": {"source": methods.GRADE5_SOURCE,
                "locator": "p0 inch-series SAEJ429Grade5 row, quarter-to-one-inch range",
                "minimum_tensile_yield_psi": 92000, "minimum_tensile_yield_mpa": methods.GRADE5_FY_MPA,
                "minimum_tensile_strength_psi": 120000, "proof_strength_psi_distinct_from_yield": 85000,
                "NDS_fyb_assigned": None, "actual_product_and_property_verified": False},
            "component_aggregate_and_cut_state_labels_authenticated": True,
            "method_validation": {"reused_fixture_count": 27, "new_adapter_fixture_count": 12,
                "adapter_test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_common_shaft_steel_bound.py",
                "adapter_lint_command": ".venv/bin/ruff check scripts/thin_bolted_common_shaft_steel_bound.py tests/test_thin_bolted_common_shaft_steel_bound.py"},
            "limits": ["Complete force arms/free couples retained. Flagged flange torsion remains outside its nominal VM envelope.",
                "Own washer axial capture is a model action. Actual pressure, own-end prying/moments, material and head/fillet/nut seating remain unresolved.",
                "Shaft circle/root/property inputs remain explicit unadopted scenarios. Actual product/threads/head/nut stripping and first-order physical applicability are unverified."],
            "native_or_CAD_execution": False, "unchanged_unit_methods_recomputed": False,
            "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demands", type=Path, required=True)
    parser.add_argument("--sections", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve prior common-shaft evidence")
    report = consume(args.demands, args.sections)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "state_id": report["state_id"],
                      "steel_ports": len(report["steel_port_wrenches"]), "own_washers": len(report["own_washer_capture_references"]),
                      "shafts": len(report["shaft_same_section_references"])}))


if __name__ == "__main__":
    main()
