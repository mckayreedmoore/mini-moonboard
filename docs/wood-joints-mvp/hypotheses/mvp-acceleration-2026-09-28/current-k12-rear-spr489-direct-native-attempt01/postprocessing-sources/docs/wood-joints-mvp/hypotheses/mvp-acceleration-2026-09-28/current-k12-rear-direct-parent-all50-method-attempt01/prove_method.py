#!/usr/bin/env python3
"""Prove K12 helper physical mechanics are AST-identical to the pinned helper."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
SOURCE_HELPER = SERIES / "current-springa-selected-floor-parent-response-audit-attempt01/check.py"
RESPONSE_CORE = SERIES / "current-k12-rear-spr489-direct-response-audit-attempt02/response_core.py"
TARGET_HELPER = HERE / "check.py"
OUTPUT = HERE / "method-equivalence-proof.json"
SOURCE_SHA256 = "7ff46055915e01d945cefe728cc4a4b146b05836976620c7f54100f586130b80"
SOURCE_RESPONSE_SCHEMA = "current_springa_selected_floor_physical_response_audit/v1"
TARGET_RESPONSE_SCHEMA = "current_k12_rear_spr489_direct_master_physical_response_audit/v1"
SOURCE_RESPONSE_STATUS = "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY"
TARGET_RESPONSE_STATUS = "PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY"
RESPONSE_CORE_SHA256 = "87e8624661fb30fd8d0ec23fee51ad421045bafaade0736f05439a26578ea1d8"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=True, include_attributes=False)


def function(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one function {name}")
    return matches[0]


def main_guard(tree: ast.Module) -> ast.If:
    matches = [
        node for node in tree.body if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
        and node.test.comparators and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == "__main__"
    ]
    if len(matches) != 1:
        raise ValueError("expected one __main__ guard")
    return matches[0]


def target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return None


def parsed_expression(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def increment_loop(run_node: ast.FunctionDef) -> ast.For:
    matches = [
        node for node in ast.walk(run_node)
        if isinstance(node, ast.For)
        and isinstance(node.iter, ast.Subscript)
        and isinstance(node.iter.value, ast.Name)
        and node.iter.value.id == "response"
        and isinstance(node.iter.slice, ast.Constant)
        and node.iter.slice.value == "increments"
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one `for increment in response['increments']` loop, got {len(matches)}")
    return matches[0]


def result_assignment(run_node: ast.FunctionDef) -> ast.Assign:
    matches = [
        node for node in run_node.body
        if isinstance(node, ast.Assign) and any(target_name(target) == "result" for target in node.targets)
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one final result assignment, got {len(matches)}")
    return matches[0]


def normalize_new_tree(new_tree: ast.Module, old_tree: ast.Module) -> ast.Module:
    """Erase only declared response-contract and output-routing deltas."""
    tree = copy.deepcopy(new_tree)
    old_run = function(old_tree, "run")
    old_main_guard = main_guard(old_tree)
    old_write = next(
        node for node in old_run.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "write_text"
    )

    # The dedicated path-safety adapter is new I/O-only code.
    tree.body = [node for node in tree.body if not (isinstance(node, ast.FunctionDef) and node.name == "_safe_output_path")]
    run_node = function(tree, "run")
    run_node.args.args = run_node.args.args[:-1]
    run_node.args.defaults = []
    run_node.body = [
        node for node in run_node.body
        if not (isinstance(node, ast.Assign)
                and any(target_name(target) == "output_path" for target in node.targets)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "_safe_output_path")
    ]

    schema_literals = [
        node for node in ast.walk(run_node)
        if isinstance(node, ast.Constant) and node.value == TARGET_RESPONSE_SCHEMA
    ]
    if len(schema_literals) != 1:
        raise ValueError("expected one exact K12 response schema literal")
    schema_literals[0].value = SOURCE_RESPONSE_SCHEMA

    status_literals = [
        node for node in ast.walk(run_node)
        if isinstance(node, ast.Constant) and node.value == TARGET_RESPONSE_STATUS
    ]
    if len(status_literals) != 1:
        raise ValueError("expected one exact direct-master response status literal")
    status_literals[0].value = SOURCE_RESPONSE_STATUS

    # Restore the original write target only; assert the serialized report
    # expression itself remains unchanged before replacing the path expression.
    target_write = next(
        node for node in run_node.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "write_text"
    )
    target_write_call = target_write.value
    old_write_call = old_write.value
    if dump(ast.Module(body=target_write_call.args, type_ignores=[])) != dump(ast.Module(body=old_write_call.args, type_ignores=[])):
        raise ValueError("audit JSON serialization expression changed beyond its destination")
    target_write_call.func.value = copy.deepcopy(old_write_call.func.value)

    # Remove the one additional destination field from the status print; preserve
    # the original message and all other reported status values.
    print_calls = [
        node for node in run_node.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name) and node.value.func.id == "print"
    ]
    if len(print_calls) != 1:
        raise ValueError("expected the original single completion print")
    serialized = print_calls[0].value.args[0]
    if not isinstance(serialized, ast.Call) or not isinstance(serialized.func, ast.Attribute) or serialized.func.attr != "dumps":
        raise ValueError("completion print is not the original JSON-serialized status")
    print_dict = serialized.args[0]
    if not isinstance(print_dict, ast.Dict):
        raise ValueError("completion print payload is not a dict")
    kept = [(key, value) for key, value in zip(print_dict.keys, print_dict.values, strict=True)
            if not (isinstance(key, ast.Constant) and key.value == "output_path")]
    if len(kept) != len(print_dict.keys) - 1:
        raise ValueError("expected exactly one added output_path status field")
    print_dict.keys = [key for key, _ in kept]
    print_dict.values = [value for _, value in kept]

    # The CLI adds one output flag and passes it to run; drop both for comparison.
    main_node = main_guard(tree)
    output_arg_calls = [
        node for node in ast.walk(main_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument" and node.args
        and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--output"
    ]
    if len(output_arg_calls) != 1:
        raise ValueError("expected exactly one added --output CLI option")
    main_node.body = [
        node for node in main_node.body
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and node.value is output_arg_calls[0])
    ]
    run_calls = [
        node for node in ast.walk(main_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run"
    ]
    if len(run_calls) != 1 or len(run_calls[0].args) != 3:
        raise ValueError("expected one CLI run call with exactly one added output argument")
    run_calls[0].args = run_calls[0].args[:-1]

    if dump(main_node) != dump(old_main_guard):
        raise ValueError("CLI differs from source beyond the declared output flag/argument")
    return tree


def proof() -> dict[str, Any]:
    if sha(SOURCE_HELPER) != SOURCE_SHA256:
        raise ValueError("pinned parent all-body helper SHA256 changed")
    if sha(RESPONSE_CORE) != RESPONSE_CORE_SHA256:
        raise ValueError("pinned SPR489 response core SHA256 changed")
    old_tree = ast.parse(SOURCE_HELPER.read_text(encoding="utf-8"), filename=str(SOURCE_HELPER))
    new_tree = ast.parse(TARGET_HELPER.read_text(encoding="utf-8"), filename=str(TARGET_HELPER))
    old_balance, new_balance = function(old_tree, "balance"), function(new_tree, "balance")
    old_run, new_run = function(old_tree, "run"), function(new_tree, "run")
    old_loop, new_loop = increment_loop(old_run), increment_loop(new_run)
    old_result, new_result = result_assignment(old_run), result_assignment(new_run)

    # Verify the narrow accepted new schema at the assertion site.
    new_schema_asserts = [
        node for node in ast.walk(new_run)
        if isinstance(node, ast.Assert) and TARGET_RESPONSE_SCHEMA in [
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
    ]
    if len(new_schema_asserts) != 1:
        raise ValueError("new helper does not assert only the specified direct-master response schema")
    new_status_asserts = [
        node for node in ast.walk(new_run)
        if isinstance(node, ast.Assert) and TARGET_RESPONSE_STATUS in [
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
    ]
    if len(new_status_asserts) != 1:
        raise ValueError("new helper does not assert the exact direct-master response audit status")
    core_tree = ast.parse(RESPONSE_CORE.read_text(encoding="utf-8"), filename=str(RESPONSE_CORE))
    schema_assignments = [
        node for node in core_tree.body if isinstance(node, ast.Assign)
        and any(target_name(target) == "OUTPUT_SCHEMA" for target in node.targets)
    ]
    if len(schema_assignments) != 1 or not isinstance(schema_assignments[0].value, ast.Constant) or schema_assignments[0].value.value != TARGET_RESPONSE_SCHEMA:
        raise ValueError("target schema does not match the pinned direct-master response core OUTPUT_SCHEMA")
    direct_contract = function(core_tree, "audit_record_with_direct_master_contract")
    status_assignments = [
        node for node in ast.walk(direct_contract)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name) and target.value.id == "report"
            and isinstance(target.slice, ast.Constant) and target.slice.value == "status"
            for target in node.targets
        )
    ]
    if (len(status_assignments) != 1
            or not isinstance(status_assignments[0].value, ast.Constant)
            or status_assignments[0].value.value != TARGET_RESPONSE_STATUS):
        raise ValueError("target response status does not match the pinned direct-master contract override")
    if len(new_run.args.args) != 3 or new_run.args.args[-1].arg != "output_path":
        raise ValueError("new helper API does not expose output_path")
    safe_fn = function(new_tree, "_safe_output_path")
    safe_source = dump(safe_fn)
    if "current-springa-selected-floor-parent-response-audit-attempt01" not in safe_source:
        raise ValueError("output safety adapter no longer excludes the pinned original helper directory")
    expected_safe_fn = ast.parse(
        """def _safe_output_path(output_path,model_path,response_path):
 output_path=Path(output_path).expanduser().resolve();model_path=Path(model_path).resolve();response_path=Path(response_path).resolve()
 pinned_parent_dir=(HERE.parent/'current-springa-selected-floor-parent-response-audit-attempt01').resolve()
 if output_path in (model_path,response_path) or any(parent in output_path.parents for parent in (model_path.parent,response_path.parent,pinned_parent_dir)):
  raise ValueError(f'refusing to write parent all-body audit into a pinned input/source directory: {output_path}')
 return output_path
"""
    ).body[0]
    if dump(safe_fn) != dump(expected_safe_fn):
        raise ValueError("output-routing helper differs from its reviewed I/O-only path guard")
    if dump(new_run.args.defaults[0]) != dump(parsed_expression("HERE/'audit.json'")):
        raise ValueError("default output is not the new method folder's audit.json")

    cli_guard = main_guard(new_tree)
    cli_output_calls = [
        node for node in ast.walk(cli_guard) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
        and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--output"
    ]
    expected_cli = ast.parse("parser.add_argument('--output',type=Path,default=HERE/'audit.json')", mode="exec").body[0].value
    if len(cli_output_calls) != 1 or dump(cli_output_calls[0]) != dump(expected_cli):
        raise ValueError("CLI output option differs from reviewed configurable default")
    cli_run_calls = [node for node in ast.walk(cli_guard) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "run"]
    if len(cli_run_calls) != 1 or len(cli_run_calls[0].args) != 3 or dump(cli_run_calls[0].args[2]) != dump(parsed_expression("args.output")):
        raise ValueError("CLI does not pass the configured destination to the helper")

    normalized = normalize_new_tree(new_tree, old_tree)
    whole_module_equal_after_only_declared_io_schema_normalization = dump(normalized) == dump(old_tree)
    checks = {
        "pinned_source_helper_sha256_matches": sha(SOURCE_HELPER) == SOURCE_SHA256,
        "balance_and_all_printed_interval_tolerance_ast_identical": dump(old_balance) == dump(new_balance),
        "entire_seven_increment_body_and_global_sum_loop_ast_identical": dump(old_loop) == dump(new_loop),
        "audit_result_and_nonacceptance_payload_ast_identical": dump(old_result) == dump(new_result),
        "response_schema_literal_is_exact_target": len(new_schema_asserts) == 1,
        "response_schema_matches_pinned_direct_master_core": len(schema_assignments) == 1 and schema_assignments[0].value.value == TARGET_RESPONSE_SCHEMA,
        "response_status_literal_is_exact_target": len(new_status_asserts) == 1,
        "response_status_matches_pinned_direct_master_contract_override": len(status_assignments) == 1 and isinstance(status_assignments[0].value, ast.Constant) and status_assignments[0].value.value == TARGET_RESPONSE_STATUS,
        "configurable_output_is_separate_from_pinned_input_folders": "_safe_output_path" in [node.name for node in new_tree.body if isinstance(node, ast.FunctionDef)],
        "output_path_adapter_matches_reviewed_IO_only_guard": dump(safe_fn) == dump(expected_safe_fn),
        "CLI_passes_configurable_output_destination": len(cli_output_calls) == 1 and dump(cli_output_calls[0]) == dump(expected_cli) and len(cli_run_calls) == 1 and dump(cli_run_calls[0].args[2]) == dump(parsed_expression("args.output")),
        "whole_module_equal_after_only_declared_schema_and_output_normalization": whole_module_equal_after_only_declared_io_schema_normalization,
    }
    if not all(checks.values()):
        raise ValueError("AST compatibility proof failed: " + ", ".join(k for k, v in checks.items() if not v))
    return {
        "schema": "current_k12_rear_direct_parent_all50_method_equivalence_proof/v1",
        "status": "PASS_PHYSICAL_AUDIT_MECHANICS_AST_IDENTICAL",
        "source_helper_path": str(SOURCE_HELPER.relative_to(ROOT)),
        "source_helper_sha256": sha(SOURCE_HELPER),
        "schema_source_path": str(RESPONSE_CORE.relative_to(ROOT)),
        "schema_source_sha256": sha(RESPONSE_CORE),
        "target_helper_path": str(TARGET_HELPER.relative_to(ROOT)),
        "target_helper_sha256": sha(TARGET_HELPER),
        "accepted_response_schema": TARGET_RESPONSE_SCHEMA,
        "accepted_response_status": TARGET_RESPONSE_STATUS,
        "model_schema_unchanged": "current_springa_selected_floor_input_model/v1",
        "checks": checks,
        "schema_source_assignment": "OUTPUT_SCHEMA = " + TARGET_RESPONSE_SCHEMA,
        "status_source_assignment": 'report["status"] = "' + TARGET_RESPONSE_STATUS + '"',
        "ast_sha256": {
            "balance_function": hashlib.sha256(dump(new_balance).encode()).hexdigest(),
            "seven_increment_physical_sum_loop": hashlib.sha256(dump(new_loop).encode()).hexdigest(),
            "audit_result_assignment": hashlib.sha256(dump(new_result).encode()).hexdigest(),
            "whole_module_after_declared_normalization": hashlib.sha256(dump(normalized).encode()).hexdigest(),
        },
        "allowed_deltas_only": [
            f"response schema assertion narrowed to {TARGET_RESPONSE_SCHEMA}",
            f"response status assertion narrowed to the pinned {TARGET_RESPONSE_STATUS} direct-master override",
            "output path is configurable and resolved away from input folders and the pinned original helper directory",
            "completion print includes the chosen output path",
        ],
        "mechanics": {"printed_force_limit_n": 0.1, "printed_moment_limit_nmm": 2.0, "interval_force_limit_n": 0.1, "interval_moment_limit_nmm": 2.0, "force/moment accumulation": "unchanged from pinned source AST"},
        "response_consumed": False,
        "synthetic_forces_created": False,
        "native_solve_executed": False,
        "joint_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = proof()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")
        return
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
        raise SystemExit("method-equivalence-proof.json differs from reproducible AST proof")
    print(f"verified {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")


if __name__ == "__main__":
    main()
