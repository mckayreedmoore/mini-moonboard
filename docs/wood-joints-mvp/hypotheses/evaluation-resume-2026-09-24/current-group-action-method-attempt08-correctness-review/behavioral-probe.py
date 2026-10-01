"""Independent synthetic probes; run from the repository root with PYTHONPATH=."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
import runpy

from mini_moonboard.nds_2024_group_action import (
    canonical_group_record_sha256,
    canonical_sensitivity_contract_sha256,
    evaluate_group_action_factor,
    evaluate_group_factor_sensitivity,
)


source_path = Path(inspect.getfile(evaluate_group_factor_sensitivity))
fixture_path = Path("tests/test_nds_2024_group_action.py")
source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
fixture_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
fixtures = runpy.run_path(str(fixture_path))
payload = fixtures["payload"]
bindings = fixtures["bindings"]
observations = []


def scenario_pair(*, baseline_count=3, variant_count=3, variant_pitch=4.0):
    baseline = payload(count=baseline_count)
    variant = payload(count=variant_count, pitch=variant_pitch)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")
    return baseline, variant


def compare(name, baseline, variant, paths, expected_reason=None, mutate=None):
    contract = {
        "contract_id": f"independent-{name}",
        "source_id": f"independent-review/{name}",
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
    contract["sha256"] = canonical_sensitivity_contract_sha256(contract)
    binding = {
        key: contract[key]
        for key in ("contract_id", "source_id", "sha256", "review_status")
    }
    if mutate is not None:
        mutate(contract, binding)
    result = evaluate_group_factor_sensitivity(
        baseline,
        variant,
        baseline_expected_bindings=baseline["source_bindings"],
        baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
        sensitivity_expected_bindings=variant["source_bindings"],
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=binding,
    )
    assert result["capacity"] is None, (name, result)
    assert result["criterion_disposition"] == "pending", (name, result)
    if expected_reason is None:
        assert result["status"] == "calculated_method_sensitivity_only", (name, result)
        assert result["changed_input_paths"] == sorted(set(paths)), (name, result)
    else:
        assert result["status"] == "pending", (name, result)
        assert expected_reason in result["reason_codes"], (name, result)
    observations.append({"name": name, "declared_paths": paths, "result": result})


path_mismatch = "sensitivity_changed_input_paths_do_not_match_contract"
base, variant = scenario_pair(baseline_count=12, variant_count=12, variant_pitch=2.0)
pitch_paths = [
    f"group_geometry.fasteners[{index}].center_in[0]"
    for index in range(1, 12)
]
compare("twelve-index-reversed-contract", base, variant, list(reversed(pitch_paths)))
compare("twelve-index-duplicate-contract", base, variant, pitch_paths + pitch_paths[:1])
compare("twelve-index-omitted-item", base, variant, pitch_paths[:-1], path_mismatch)
compare("twelve-index-extra-item", base, variant, pitch_paths + ["members.main"], path_mismatch)

tail_paths = ["group_geometry.fasteners.length"] + [
    f"group_geometry.fasteners[{index}]" for index in range(2, 12)
]
for name, counts in (("grow", (2, 12)), ("shrink", (12, 2))):
    base, variant = scenario_pair(baseline_count=counts[0], variant_count=counts[1])
    compare(f"{name}-complete-items", base, variant, list(reversed(tail_paths)))
    compare(f"{name}-length-only", base, variant, tail_paths[:1], path_mismatch)
    compare(f"{name}-omitted-item", base, variant, tail_paths[:-1], path_mismatch)
    compare(f"{name}-omitted-length", base, variant, tail_paths[1:], path_mismatch)

base, variant = scenario_pair()
base["producer_extension"] = [[], [{"a": 1}]]
variant["producer_extension"] = [[], [{"a": 1}, {"b": 2}], [99]]
compare(
    "nested-array-growth",
    base,
    variant,
    [
        "producer_extension.length",
        "producer_extension[1].length",
        "producer_extension[1][1]",
        "producer_extension[2]",
    ],
)

base, variant = scenario_pair()
base["producer_extension"] = {
    "a.b": 1,
    "a": {"b": 1},
    "arr[0]": 1,
    "arr": [1],
    "back\\slash": 1,
    "": 1,
    "\\e": 1,
    "\\": 1,
    ".": 1,
    "[": 1,
    "]": 1,
    "length": 1,
}
variant["producer_extension"] = {
    **{key: 2 for key in base["producer_extension"]},
    "a": {"b": 2},
    "arr": [2],
}
escaped_paths = [
    r"producer_extension.a\.b",
    "producer_extension.a.b",
    r"producer_extension.arr\[0\]",
    "producer_extension.arr[0]",
    r"producer_extension.back\\slash",
    r"producer_extension.\e",
    r"producer_extension.\\e",
    r"producer_extension.\\",
    r"producer_extension.\.",
    r"producer_extension.\[",
    r"producer_extension.\]",
    "producer_extension.length",
]
compare("escaped-key-combinations", base, variant, escaped_paths)
compare("escaped-literal-dot-omission", base, variant, escaped_paths[1:], path_mismatch)

base, variant = scenario_pair()
base[""] = 1
variant[""] = 2
compare("root-empty-key", base, variant, [r"\e"])

base, variant = scenario_pair()
base["producer_extension"] = {"length": 1, "arr": [1]}
variant["producer_extension"] = {"length": 2, "arr": [1, 2]}
compare(
    "object-length-and-array-length",
    base,
    variant,
    [
        "producer_extension.length",
        "producer_extension.arr.length",
        "producer_extension.arr[1]",
    ],
)

base, variant = scenario_pair()
base["producer_extension"] = [1]
variant["producer_extension"] = {"0": 1}
compare("whole-value-type-change", base, variant, ["producer_extension"])
compare("type-change-child-is-insufficient", base, variant, ["producer_extension[0]"], path_mismatch)

base, variant = scenario_pair(variant_pitch=2.0)
paths = [
    "group_geometry.fasteners[1].center_in[0]",
    "group_geometry.fasteners[2].center_in[0]",
]


def stale_digest(contract, binding):
    contract["changed_input_paths"] = paths[:1]


def rebound(field, value):
    def mutate(contract, binding):
        contract[field] = value
        contract["sha256"] = canonical_sensitivity_contract_sha256(contract)
        binding["sha256"] = contract["sha256"]
    return mutate


compare("stale-contract-content-digest", base, variant, paths, "sensitivity_contract_content_digest_mismatch", stale_digest)
compare("wrong-independent-binding", base, variant, paths, "sensitivity_contract_does_not_match_independent_review_binding", lambda c, b: b.update(sha256="f" * 64))
compare("unreviewed-contract", base, variant, paths, "sensitivity_case_contract_not_coordinator_reviewed", rebound("review_status", "draft"))
compare("non-composite-contract", base, variant, paths, "sensitivity_scenarios_must_be_classified_as_composite", rebound("classification", "single_variable"))
compare("wrong-group-identity", base, variant, paths, "sensitivity_contract_identity_mismatch", rebound("group_id", "other-group"))
compare("wrong-baseline-scenario", base, variant, paths, "baseline_scenario_id_mismatch", rebound("baseline_scenario_id", "other-baseline"))
compare("wrong-sensitivity-scenario", base, variant, paths, "sensitivity_scenario_id_mismatch", rebound("sensitivity_scenario_id", "other-sensitivity"))
variant["load_case"]["case_id"] = "other-case"
compare("different-load-case", base, variant, paths + ["load_case.case_id"], "sensitivity_case_load_case_mismatch")

base, variant = scenario_pair()
base[" "] = 1
variant[" "] = 2
for record in (base, variant):
    factor = evaluate_group_action_factor(
        record,
        expected_bindings=record["source_bindings"],
        expected_payload_sha256=canonical_group_record_sha256(record),
    )
    assert factor["status"] == "calculated_method_only", factor
compare("whitespace-root-key-false-pending", base, variant, [" "], "invalid_sensitivity_changed_input_paths")

report = {
    "schema": "wood_joint_group_action_attempt08_independent_behavioral_probes/v1",
    "source_sha256": source_sha256,
    "fixture_sha256": fixture_sha256,
    "expected_behavior_checks": len(observations) - 1,
    "reproduced_low_priority_limitations": 1,
    "method_only_boundary_preserved_for_every_probe": True,
    "observations": observations,
}
assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_sha256
assert hashlib.sha256(fixture_path.read_bytes()).hexdigest() == fixture_sha256
Path(__file__).with_name("behavioral-probe-results.json").write_text(
    json.dumps(report, indent=2) + "\n"
)
print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))
