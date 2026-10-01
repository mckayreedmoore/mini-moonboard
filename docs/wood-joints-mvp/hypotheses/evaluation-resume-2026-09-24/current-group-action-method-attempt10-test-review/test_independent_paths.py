"""Synthetic review probes; these assertions do not establish joint capacity."""

from __future__ import annotations

import copy
from pathlib import Path
import os

import pytest

import mini_moonboard.nds_2024_group_action as method


REQUIRED_FIELDS = (
    "contract_id", "source_id", "sha256", "review_status", "classification",
    "candidate_id", "revision_id", "group_id", "baseline_scenario_id",
    "sensitivity_scenario_id", "changed_input_paths",
)
MISMATCH = "sensitivity_changed_input_paths_do_not_match_contract"
MISSING = object()


def source_bindings(tag):
    bindings = {
        role: {"source_id": f"independent-synthetic/{tag}/{role}", "sha256": str(index) * 64}
        for index, role in enumerate(method.SOURCE_ROLES, 1)
    }
    bindings["member_sections"].update(
        main_member_id="review-main", side_member_ids=["review-side"], shear_planes=1
    )
    return bindings


def record(tag="baseline", *, count=12, pitch=4.0):
    return {
        "schema": method.SCHEMA_VERSION,
        "candidate_id": "independent-synthetic-only",
        "revision_id": "test-review-v1",
        "group_id": "review-group",
        "scenario_id": tag,
        "source_bindings": source_bindings(tag),
        "group_geometry": {
            "row_axis_xyz": [1.0, 0.0, 0.0],
            "fasteners": [
                {"fastener_id": f"review-bolt-{index}", "center_in": [index * pitch, 0.0, 0.0],
                 "nominal_diameter_in": 0.5, "type": "dowel"}
                for index in range(count)
            ],
        },
        "load_case": {"case_id": "synthetic-lateral", "lateral_resultant_xyz_lbf": [1000.0, 0.0, 0.0]},
        "members": {
            "shear_planes": 1,
            "main": {"member_id": "review-main", "material": "wood", "elastic_modulus_psi": 1_400_000.0,
                     "gross_section_area_in2": 10.0, "grain_axis_xyz": [1.0, 0.0, 0.0]},
            "side_members": [
                {"member_id": "review-side", "material": "wood", "elastic_modulus_psi": 1_400_000.0,
                 "gross_section_area_in2": 5.0, "grain_axis_xyz": [1.0, 0.0, 0.0]}
            ],
        },
    }


def make_contract(paths):
    contract = {
        "contract_id": "independent-test-contract",
        "source_id": "independent-synthetic/contract",
        "sha256": "0" * 64,
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "independent-synthetic-only",
        "revision_id": "test-review-v1",
        "group_id": "review-group",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": paths,
    }
    return contract


def bind(contract):
    contract["sha256"] = method.canonical_sensitivity_contract_sha256(contract)
    return {
        "contract_id": contract["contract_id"], "source_id": contract["source_id"],
        "sha256": contract["sha256"], "review_status": "coordinator_reviewed",
    }


def boundary(result):
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"
    assert result["status"] in {"pending", "calculated_method_only", "calculated_method_sensitivity_only"}
    assert not any(key in result for key in ("accepted", "criterion_pass", "demand_capacity_ratio", "resistance"))
    if result["status"] == "pending":
        assert result["cg"] is None
        assert result["reason_codes"]
    if result["status"] == "calculated_method_only":
        assert "no resistance or demand/capacity comparison" in result["scope"]
        assert "authority_not_verified_by_method" in result["provenance_level"]
    if result["status"] == "calculated_method_sensitivity_only":
        assert "not the adopted criterion demand/capacity ratio" in result["interpretation"]


def evaluate(left, right, paths, *, contract=MISSING, binding=MISSING, **overrides):
    if contract is MISSING:
        contract = make_contract(paths)
    if binding is MISSING:
        binding = bind(contract)
    kwargs = {
        "baseline_expected_bindings": copy.deepcopy(left["source_bindings"]),
        "baseline_expected_payload_sha256": method.canonical_group_record_sha256(left),
        "sensitivity_expected_bindings": copy.deepcopy(right["source_bindings"]),
        "sensitivity_expected_payload_sha256": method.canonical_group_record_sha256(right),
        "expected_sensitivity_contract": contract,
        "expected_sensitivity_binding": binding,
    }
    kwargs.update(overrides)
    result = method.evaluate_group_factor_sensitivity(left, right, **kwargs)
    boundary(result)
    return result


def accepted(result, paths):
    assert result["status"] == "calculated_method_sensitivity_only", result
    assert result["changed_input_paths"] == sorted(set(paths))


def rejected(result, reason=None):
    assert result["status"] == "pending", result
    if reason:
        assert reason in result["reason_codes"], result


def pitch_paths(count):
    return [f"group_geometry.fasteners[{index}].center_in[0]" for index in range(1, count)]


def test_module_is_loaded_from_isolated_replay():
    expected = Path(os.environ["ATTEMPT10_REVIEW_REPLAY_ROOT"]) / "mini_moonboard/nds_2024_group_action.py"
    assert Path(method.__file__).resolve() == expected.resolve()


@pytest.mark.parametrize("count", [12, 21, 103])
@pytest.mark.parametrize("ordering", ["numeric", "lexical", "reverse", "duplicates"])
def test_multi_digit_positive_ordering(count, ordering):
    left, right = record(count=count), record("sensitivity", count=count, pitch=2.0)
    paths = pitch_paths(count)
    if ordering == "lexical":
        paths.sort()
    elif ordering == "reverse":
        paths.reverse()
    elif ordering == "duplicates":
        paths += [paths[0], paths[-1]]
    accepted(evaluate(left, right, paths), paths)


@pytest.mark.parametrize("error", ["omit-10", "omit-11", "extra", "leading-zero", "wrong-index", "wrong-component"])
def test_multi_digit_negative_declarations(error):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    if error.startswith("omit-"):
        paths.remove(f"group_geometry.fasteners[{error[5:]}].center_in[0]")
    elif error == "extra":
        paths.append("group_geometry.fasteners[0].center_in[0]")
    else:
        replacement = {
            "leading-zero": "group_geometry.fasteners[010].center_in[0]",
            "wrong-index": "group_geometry.fasteners[12].center_in[0]",
            "wrong-component": "group_geometry.fasteners[10].center_in[1]",
        }[error]
        paths[9] = replacement
    rejected(evaluate(left, right, paths), MISMATCH)


@pytest.mark.parametrize("start,end", [(2, 13), (10, 13), (13, 2), (13, 10)])
@pytest.mark.parametrize("declaration", ["complete", "length-only", "items-only", "omit-10", "leaf-instead", "extra"])
def test_actual_fastener_list_growth_and_removal(start, end, declaration):
    left, right = record(count=start), record("sensitivity", count=end)
    paths = ["group_geometry.fasteners.length"] + [
        f"group_geometry.fasteners[{index}]" for index in range(min(start, end), max(start, end))
    ]
    if declaration == "length-only":
        paths = paths[:1]
    elif declaration == "items-only":
        paths = paths[1:]
    elif declaration == "omit-10":
        paths.remove("group_geometry.fasteners[10]")
    elif declaration == "leaf-instead":
        paths[1] += ".center_in[0]"
    elif declaration == "extra":
        paths.append("group_geometry.fasteners[0]")
    result = evaluate(left, right, paths)
    if declaration == "complete":
        accepted(result, paths)
    else:
        rejected(result, MISMATCH)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("item", [None, [], {}, {"a.b": [1]}, [None, {"": 2}]])
def test_empty_list_growth_and_removal_whole_items(reverse, item):
    left, right = record(), record("sensitivity")
    left["extension"], right["extension"] = [], [item]
    if reverse:
        left["extension"], right["extension"] = right["extension"], left["extension"]
    paths = ["extension.length", "extension[0]"]
    accepted(evaluate(left, right, paths), paths)
    rejected(evaluate(left, right, ["extension.length"]), MISMATCH)
    rejected(evaluate(left, right, ["extension[0]"]), MISMATCH)


ESCAPED_KEYS = [
    ("a.b", r"a\.b"),
    ("a[10]", r"a\[10\]"),
    ("[", r"\["),
    ("]", r"\]"),
    ("\\", "\\\\"),
    (r"a\b", r"a\\b"),
    ("", r"\e"),
    (r"\e", r"\\e"),
    (r"\u0020", r"\\u0020"),
    (" ", r"\u0020"),
    ("\t", r"\u0009"),
    (" \n\t", r"\u0020\u000a\u0009"),
    ("\u00a0\u2003\u2028\u3000", r"\u00a0\u2003\u2028\u3000"),
    ("\x1c", r"\u001c"),
    (r"a.\[10]", r"a\.\\\[10\]"),
    (" a ", " a "),
    ("a\nb", "a\nb"),
]


@pytest.mark.parametrize("key,encoded", ESCAPED_KEYS)
@pytest.mark.parametrize("position", ["root", "object", "array"])
def test_escaped_keys_end_to_end_positive_and_wrong_declaration(key, encoded, position):
    left, right = record(), record("sensitivity")
    if position == "root":
        left[key], right[key] = 1, 2
        path, wrong = encoded, "incorrect-key"
    elif position == "object":
        left["extension"], right["extension"] = {key: 1}, {key: 2}
        path, wrong = "extension." + encoded, "extension.incorrect-key"
    else:
        left["extension"], right["extension"] = [{key: 1}], [{key: 2}]
        path, wrong = "extension[0]." + encoded, "extension[0].incorrect-key"
    accepted(evaluate(left, right, [path]), [path])
    rejected(evaluate(left, right, [wrong]), MISMATCH)


def test_literal_nested_array_and_escape_token_paths_do_not_collide():
    left, right = record(), record("sensitivity")
    left["extension"] = {
        "a.b": 1, "a": {"b": 1}, "arr[10]": 1, "arr": [0] * 11,
        "": 1, r"\e": 1, " ": 1, r"\u0020": 1, "\\": 1,
    }
    right["extension"] = {
        "a.b": 2, "a": {"b": 2}, "arr[10]": 2, "arr": [0] * 10 + [1],
        "": 2, r"\e": 2, " ": 2, r"\u0020": 2, "\\": 2,
    }
    paths = [
        r"extension.a\.b", "extension.a.b", r"extension.arr\[10\]", "extension.arr[10]",
        r"extension.\e", r"extension.\\e", r"extension.\u0020", r"extension.\\u0020", "extension.\\\\",
    ]
    assert len(paths) == len(set(paths)) == 9
    accepted(evaluate(left, right, paths), paths)
    for missing in paths:
        rejected(evaluate(left, right, [path for path in paths if path != missing]), MISMATCH)


@pytest.mark.parametrize("key", ["scenario_id", "source_bindings"])
@pytest.mark.parametrize("parent", ["", "extension"])
def test_ignored_root_keys_are_tracked_below_empty_and_normal_keys(key, parent):
    left, right = record(), record("sensitivity")
    left[parent], right[parent] = {key: 1}, {key: 2}
    path = (r"\e" if parent == "" else parent) + "." + key
    accepted(evaluate(left, right, [path]), [path])


@pytest.mark.parametrize("key", ["scenario_id", "source_bindings", "source_bindings.geometry.sha256"])
def test_ignored_root_metadata_cannot_be_declared_as_factor_change(key):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12) + [key]
    rejected(evaluate(left, right, paths), MISMATCH)


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_each_contract_omission_fails_closed(field):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    contract = make_contract(paths)
    binding = bind(contract)
    del contract[field]
    rejected(evaluate(left, right, paths, contract=contract, binding=binding), "incomplete_sensitivity_case_contract")


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_each_contract_field_mutation_under_stale_hash_fails_closed(field):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    contract = make_contract(paths)
    binding = bind(contract)
    if field == "changed_input_paths":
        contract[field] = paths[:-1]
    elif field == "sha256":
        contract[field] = "0" * 64
    else:
        contract[field] += "-mutated"
    rejected(evaluate(left, right, paths, contract=contract, binding=binding), "sensitivity_contract_content_digest_mismatch")


@pytest.mark.parametrize("field", ["contract_id", "source_id", "candidate_id", "revision_id", "group_id", "baseline_scenario_id", "sensitivity_scenario_id", "changed_input_paths"])
def test_rehashing_mutated_contract_cannot_bypass_external_binding(field):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    contract = make_contract(paths)
    binding = bind(contract)
    contract[field] = paths[:-1] if field == "changed_input_paths" else contract[field] + "-mutated"
    contract["sha256"] = method.canonical_sensitivity_contract_sha256(contract)
    rejected(evaluate(left, right, paths, contract=contract, binding=binding), "sensitivity_contract_does_not_match_independent_review_binding")


@pytest.mark.parametrize("field", ["candidate_id", "revision_id", "group_id", "baseline_scenario_id", "sensitivity_scenario_id", "review_status", "classification"])
def test_rebound_invalid_contract_still_fails_semantic_checks(field):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    contract = make_contract(paths)
    contract[field] += "-mutated"
    rejected(evaluate(left, right, paths, contract=contract))


@pytest.mark.parametrize("paths", [None, [], "group_geometry", [None], [1], [True], [""], [" "], ["\t\n"], {}])
def test_rebound_invalid_path_containers_fail_closed(paths):
    left, right = record(), record("sensitivity", pitch=2.0)
    rejected(evaluate(left, right, paths), "invalid_sensitivity_changed_input_paths")


@pytest.mark.parametrize("field", ["contract_id", "source_id", "sha256", "review_status"])
@pytest.mark.parametrize("change", ["omit", "mutate"])
def test_independent_binding_omissions_and_mutations(field, change):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    contract = make_contract(paths)
    binding = bind(contract)
    if change == "omit":
        del binding[field]
    else:
        binding[field] = "0" * 64 if field == "sha256" else binding[field] + "-mutated"
    rejected(evaluate(left, right, paths, contract=contract, binding=binding))


@pytest.mark.parametrize("missing", ["contract", "binding", "both"])
def test_missing_contract_or_binding_fails_closed(missing):
    left, right = record(), record("sensitivity", pitch=2.0)
    paths = pitch_paths(12)
    contract = make_contract(paths)
    binding = bind(contract)
    if missing in ("contract", "both"):
        contract = None
    if missing in ("binding", "both"):
        binding = None
    rejected(evaluate(left, right, paths, contract=contract, binding=binding), "sensitivity_case_contract_and_independent_binding_required")


@pytest.mark.parametrize("side", ["baseline", "sensitivity"])
@pytest.mark.parametrize("damage", ["missing-binding", "wrong-binding", "missing-digest", "wrong-digest"])
def test_independent_payload_evidence_failures_are_pending(side, damage):
    left, right = record(), record("sensitivity", pitch=2.0)
    overrides = {}
    if damage == "missing-binding":
        overrides[f"{side}_expected_bindings"] = None
    elif damage == "wrong-binding":
        overrides[f"{side}_expected_bindings"] = source_bindings("wrong-source")
    elif damage == "missing-digest":
        overrides[f"{side}_expected_payload_sha256"] = None
    else:
        overrides[f"{side}_expected_payload_sha256"] = "0" * 64
    rejected(evaluate(left, right, pitch_paths(12), **overrides), "baseline_or_sensitivity_case_not_calculated")


@pytest.mark.parametrize("reverse", [False, True])
def test_ratio_on_either_side_of_one_never_means_capacity_or_criterion_acceptance(reverse):
    left = record(pitch=2.0 if reverse else 4.0)
    right = record("sensitivity", pitch=4.0 if reverse else 2.0)
    # Producer attempts to include adoption/capacity claims are hashed input only.
    for case in (left, right):
        case.update(capacity=1000000, criterion_disposition="accepted", criterion_pass=True)
    result = evaluate(left, right, pitch_paths(12))
    accepted(result, pitch_paths(12))
    assert (result["sensitivity_over_baseline_cg"] < 1.0) is reverse
    for case in (left, right):
        factor = method.evaluate_group_action_factor(
            case, expected_bindings=copy.deepcopy(case["source_bindings"]),
            expected_payload_sha256=method.canonical_group_record_sha256(case),
        )
        boundary(factor)
        assert factor["status"] == "calculated_method_only"


@pytest.mark.parametrize("left,right,expected", [
    ({"a.b": 1}, {"a.b": 1.0}, [r"a\.b"]),
    ({"": -0.0}, {"": 0.0}, [r"\e"]),
    ({"a[0]": 1}, {"a[0]": True}, [r"a\[0\]"]),
    ({"extension": {"": 1}}, {"extension": {}}, [r"extension.\e"]),
    ({"extension": {}}, {"extension": {"": 1}}, [r"extension.\e"]),
    ({"extension": [1]}, {"extension": {"0": 1}}, ["extension"]),
    ({"extension": [1, 2]}, {"extension": [2, 1]}, ["extension[0]", "extension[1]"]),
])
def test_exact_scalar_and_structural_changes(left, right, expected):
    assert sorted(method._changed_payload_paths(left, right)) == sorted(expected)
