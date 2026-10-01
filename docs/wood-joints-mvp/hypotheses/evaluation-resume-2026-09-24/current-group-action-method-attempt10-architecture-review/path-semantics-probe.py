"""Independent path/contract probes for the hash-pinned attempt10 replay.

Usage: <pytest-environment-python> path-semantics-probe.py <isolated-replay-root>
This writes no source files and runs no solver.
"""
from __future__ import annotations

import copy
import json
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
replay = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(replay))
from mini_moonboard.nds_2024_group_action import (  # noqa: E402
    _changed_payload_paths,
    canonical_group_record_sha256,
    evaluate_group_factor_sensitivity,
)

fixture = runpy.run_path(str(replay / "tests/test_nds_2024_group_action.py"))
payload = fixture["payload"]
bindings = fixture["bindings"]
bind_contract = fixture["bind_sensitivity_contract"]


def public_result(left_extension, right_extension, paths):
    left = payload(count=3)
    right = payload(count=3)
    left.update(left_extension)
    right.update(right_extension)
    right["scenario_id"] = "sensitivity"
    right["source_bindings"] = bindings("sensitivity")
    contract = {
        "contract_id": "architecture-path-probe",
        "source_id": "synthetic-fixture/architecture-path-probe",
        "sha256": "pending-digest",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": paths,
    }
    independent_binding = bind_contract(contract)
    return evaluate_group_factor_sensitivity(
        left,
        right,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(left),
        sensitivity_expected_bindings=bindings("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(right),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=independent_binding,
    )


cases = {
    "literal_dot": ({"a.b": 1}, {"a.b": 2}, [r"a\.b"]),
    "nested_dot": ({"a": {"b": 1}}, {"a": {"b": 2}}, ["a.b"]),
    "literal_index": ({"a[0]": 1}, {"a[0]": 2}, [r"a\[0\]"]),
    "array_index": ({"a": [1]}, {"a": [2]}, ["a[0]"]),
    "empty_key": ({"": 1}, {"": 2}, [r"\e"]),
    "literal_empty_escape": ({r"\e": 1}, {r"\e": 2}, [r"\\e"]),
    "whitespace_key": ({" ": 1}, {" ": 2}, [r"\u0020"]),
    "literal_whitespace_escape": ({r"\u0020": 1}, {r"\u0020": 2}, [r"\\u0020"]),
    "multiple_whitespace": ({" \t": 1}, {" \t": 2}, [r"\u0020\u0009"]),
    "nested_empty_keys": ({"": {"": 1}}, {"": {"": 2}}, [r"\e.\e"]),
    "growth_with_nested_whole_item": ({"a": []}, {"a": [{"x": [1, 2]}]}, ["a.length", "a[0]"]),
    "shrink_with_nested_whole_item": ({"a": [{"x": [1, 2]}]}, {"a": []}, ["a.length", "a[0]"]),
    "middle_removal_is_positional": ({"a": ["first", "middle", "last"]}, {"a": ["first", "last"]}, ["a.length", "a[1]", "a[2]"]),
    "type_replacement_is_parent": ({"a": [1]}, {"a": {"length": 1}}, ["a"]),
    "list_length": ({"a": []}, {"a": [1]}, ["a.length", "a[0]"]),
    "literal_object_length": ({"a": {"length": 0}}, {"a": {"length": 1}}, ["a.length"]),
}
observed = {}
for name, (left, right, expected) in cases.items():
    paths = sorted(_changed_payload_paths(left, right))
    result = public_result(left, right, expected)
    assert paths == expected, (name, paths, expected)
    assert result["status"] == "calculated_method_sensitivity_only", (name, result)
    assert result["capacity"] is None and result["criterion_disposition"] == "pending"
    observed[name] = {"paths": paths, "status": result["status"]}

wrong_whitespace = public_result({" ": 1}, {" ": 2}, [r"\\u0020"])
assert wrong_whitespace["status"] == "pending"
assert "sensitivity_changed_input_paths_do_not_match_contract" in wrong_whitespace["reason_codes"]

leaf_expansion = public_result({"a": []}, {"a": [{"x": [1, 2]}]}, ["a.length", "a[0].x[0]", "a[0].x[1]"])
assert leaf_expansion["status"] == "pending"
assert "sensitivity_changed_input_paths_do_not_match_contract" in leaf_expansion["reason_codes"]

# Exercise every distinct key in a single tree: no location aliases can hide
# behind set() when the whole dictionary changes.
keys = ["", " ", "\t", " \t", "\u2003", ".", "[", "]", "\\", "a.b", "a[0]", "a\\b", r"\e", r"\u0020", "length", "a\nb", "e\u0301", "\u00e9"]
all_keys_paths = _changed_payload_paths(dict.fromkeys(keys, 1), dict.fromkeys(keys, 2))
assert len(all_keys_paths) == len(keys) == len(set(all_keys_paths))

print(json.dumps({
    "positive_cases": observed,
    "distinct_key_count": len(keys),
    "distinct_key_paths": all_keys_paths,
    "negative_cases": {
        "double_backslash_whitespace_contract_rejected": wrong_whitespace,
        "leaf_expansion_instead_of_added_whole_item": leaf_expansion,
    },
    "python_version": sys.version,
    "all_assertions_pass": True,
}, indent=2, ensure_ascii=False))
