"""Independent frozen-consumer review; saved metadata and inert tests only.

No genuine field, reducer, admission, CAD, operator preparation, K or solve is
executed. The source-only current contract and synthetic controls are rerun.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
MECH = OWN.parents[2]
TARGET = MECH / "current-component-bridge-v1/consumer-v1"
FROZEN = {
    "consume.py": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9",
    "test_consume.py": "e289bf15565d6fd19d4ee59ff8cc9b11b7db3ac807e5584abe2cc353b254cab5",
    "verification.json": "13d897fdb5271aafe1af3c2c1741ff592ae8cee3fba5a995cd8fdd4ddc8a4bc4",
}
INSPECTED = (
    "component-method-v1/assessment.py",
    "component-method-v1/gross_members.py",
    "raised-rail-components-v1/comparisons.py",
    "steel-shaft-comparison-v1/comparison.py",
    "floor-practical-resolution-v1/runner.py",
    "adjusted-base-mechanics-v1/current-force-bridge-v1/bridge.py",
    "adjusted-base-mechanics-v1/current-force-bridge-v1/review-fix-v2/bridge.py",
)
SCRIPTS = (
    "scripts/thin_bolted_panel_coupled.py",
    "scripts/thin_bolted_panel_mechanics.py",
    "scripts/thin_bolted_timber_common_shaft_checks.py",
)
EXTRA_INSPECTED = {
    "floor-practical-resolution-v1/runner.py": "02b35eb6eb148e1b178fcca069b761065eaec8f0641ec5adc91f211b3e9eceb4",
    "adjusted-base-mechanics-v1/current-force-bridge-v1/bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    "scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0",
    "scripts/thin_bolted_panel_mechanics.py": "472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa",
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relative(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def function(path, name):
    tree = ast.parse(Path(path).read_bytes())
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def calls(node):
    return [ast.unparse(item.func) for item in ast.walk(node) if isinstance(item, ast.Call)]


def source_checks():
    consumer = TARGET / "consume.py"
    consume = function(consumer, "consume")
    body = [ast.unparse(item) for item in consume.body]
    positions = {term: next(i for i, item in enumerate(body) if term in item)
                 for term in ("authenticate(", "_current_contract(", "_reduce(")}
    require(positions["authenticate("] < positions["_current_contract("] < positions["_reduce("],
            "authentic current gate must precede contract and reduction")
    intake = function(consumer, "authenticate")
    require("_reduce" not in calls(intake) and "method" not in calls(intake),
            "intake must not invoke reductions")
    reservation = function(consumer, "consume_to_file")
    opened = next(node for node in ast.walk(reservation) if isinstance(node, ast.With))
    require(ast.unparse(opened.items[0].context_expr) == "Path(out).open('x')",
            "reservation must be exclusive")
    require(any("consume(" in ast.unparse(item) for item in opened.body),
            "producer must remain under the exclusive output reservation")
    base = MECH.parent / "component-method-v1/assessment.py"
    panel_calls = calls(function(base, "panel_reductions"))
    require("panel.prepared_datums" in panel_calls
            and "panel.panel_method.resolved_section_references" in panel_calls
            and "panel.deformation_diagnostics" in panel_calls
            and "panel.panel_method.edge_transfer_diagnostics" not in panel_calls,
            "selected diagnostics must not depend on historical support footprints")
    for file, name in (("scripts/thin_bolted_panel_mechanics.py", "resolved_section_references"),
                       ("scripts/thin_bolted_panel_coupled.py", "deformation_diagnostics")):
        require("support_bounds" not in ast.unparse(function(ROOT / file, name)),
                "cleared historical support footprints must not enter selected diagnostics")
    reduction_calls = calls(function(base, "reduce_field"))
    require(all(name in reduction_calls for name in (
        "steel.fitting_strip_comparisons", "steel.shaft_circle_comparisons",
        "gross.member_witnesses", "panel.screw_references", "panel_reductions")),
        "frozen coarse reducer bindings differ")
    return {"gate_before_contract_before_reducer": True,
            "exclusive_reservation_encloses_producer": True,
            "unchanged_selected_frozen_function_bindings": True,
            "selected_panel_diagnostics_do_not_use_cleared_old_support_footprints": True}


def main():
    pins = {relative(TARGET / name): digest for name, digest in FROZEN.items()}
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "review target changed: " + path)
    static = source_checks()
    spec = importlib.util.spec_from_file_location("independent_current_component_correctness_subject", TARGET / "consume.py")
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)
    # This plan imports only stdlib and reads saved JSON/source bytes.
    plan = consumer._load_plan()
    exported = json.loads(plan.checked_bytes(plan.ARTIFACTS["descriptors"]))
    raw_timber = {row["name"] for row in exported["raw_gross_timber_rows"]}
    source = {key: exported[value] for key, value in consumer.DESCRIPTOR_KEYS.items()}
    source["parameters"] = exported["parameters"]
    source["panel_ids"] = [row["id"] for row in exported["finished_body_observations"] if row["id"] not in raw_timber]
    contract, axes = consumer._current_contract({"source_inputs": source}, plan)
    require(len(axes) == 100 and len(source["hillman_rows"]) == 66
            and len(source["current_panel_machining_descriptors"]["features"]) == 340,
            "exact current metadata census differs")
    require(contract["complete_joint_resistance"] is None,
            "metadata contract must preserve unknown complete resistance")
    plan.merge(pins, contract["source_sha256"])
    plan.merge(pins, {relative(consumer.PLAN): consumer.PLAN_SHA, relative(OWN): sha(OWN)})
    plan.merge(pins, {relative(ROOT / path if path.startswith("scripts/") else MECH.parent / path): digest
                      for path, digest in EXTRA_INSPECTED.items()})
    for path in INSPECTED:
        actual = MECH.parent / path
        require(relative(actual) in pins, "inspected frozen source lacks contract pin: " + path)
    for path in SCRIPTS:
        require(path in pins, "inspected script lacks contract pin: " + path)
    consumer.verify(pins)
    # Reuse the already checked contract to isolate all exact saved-row joins.
    cached = {row["path"]: plan.checked_bytes(row) for row in plan.ARTIFACTS.values()
              if row is plan.ARTIFACTS["descriptors"] or row is plan.ARTIFACTS["geometry"]}
    inert_plan = SimpleNamespace(component_plan=lambda: contract, ARTIFACTS=plan.ARTIFACTS,
                                 checked_bytes=lambda row: cached[row["path"]], indexed=plan.indexed)
    rejected = []
    for key in (*consumer.DESCRIPTOR_KEYS, "parameters", "panel_ids"):
        altered = {**source, key: copy.copy(source[key])}
        value = altered[key]
        if isinstance(value, list):
            value.pop()
        else:
            value.pop(next(iter(value)))
        try:
            consumer._current_contract({"source_inputs": altered}, inert_plan)
        except ValueError:
            rejected.append(key)
        else:
            raise AssertionError("altered current source row accepted: " + key)
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               str(TARGET / "test_consume.py")]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
    require(result.returncode == 0 and "23 passed" in result.stdout, result.stdout + result.stderr)
    consumer.verify(pins)
    require(not any(name in sys.modules for name in ("cadquery", "OCP", "scripts.thin_bolted_panel_coupled",
                "eoere_current_coarse_assessment", "eoere_current_coarse_gross", "eoere_current_coarse_centroidal_comparison")),
            "review must not import CAD or genuine reducers")
    receipt = {
        "schema": "eoere_extended_cleat_component_consumer_independent_correctness_review/v1",
        "status": "CLEAN_SOURCE_SAVED_METADATA_AND_SYNTHETIC_CONTROLS_GENUINE_PAIR_PENDING",
        "findings": [], "target": {relative(TARGET / name): digest for name, digest in FROZEN.items()},
        "checks": {**static, "positive_actual_saved_metadata_contract": True,
                   "current_axes": len(axes), "current_Hillman_screws": len(source["hillman_rows"]),
                   "current_panel_apertures": len(source["current_panel_machining_descriptors"]["features"]),
                   "frozen_contract_source_pins": len(contract["source_sha256"]),
                   "altered_source_joins_rejected": rejected,
                   "supplied_tests_passed": 23,
                   "same_payload_null_resistance_and_all_six_false_release_controls": True,
                   "failure_and_abrupt_exit_reservations_retained": True,
                   "source_pins_before_after_unchanged": True},
        "command": [relative(OWN)], "test_command": command,
        "test_result": result.stdout.strip(), "python": sys.version,
        "source_sha256": dict(sorted(pins.items())),
        "execution": {"saved_JSON_source_AST_and_synthetic_controls_only": True,
                      "genuine_field_or_admission_consumed": False, "genuine_reducer_imported_or_called": False,
                      "CAD_import_query_or_rebuild": False, "panel_bank_K_or_preparation": False,
                      "frame_K_q_native_solve_or_browser": False},
        "limits": ["No genuine current admitted field exists in this review. Production compatibility and numerical component findings remain unexercised.",
                   "The current metadata source plan, frozen reducer interfaces, and inert controls are method evidence; no old response, capacity, release or current force admission is transferred.",
                   "Frozen equations and tolerances are unchanged; exceedances and null complete resistance remain permitted. No panel or screw remedy is proposed."],
        "release": dict(consumer.RELEASE),
    }
    output = OWN.with_name("receipt.json")
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"receipt": relative(output), "sha256": sha(output),
                      "review_helper_sha256": sha(OWN), "status": receipt["status"],
                      "tests_passed": 23, "review_source_pins": len(pins)}, sort_keys=True))


if __name__ == "__main__":
    main()
