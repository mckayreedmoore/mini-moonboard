"""Independent, synthetic API probes for the immutable attempt08 review."""

from __future__ import annotations

import itertools

import pytest

from mini_moonboard.nds_2024_group_action import (
    SCHEMA_VERSION,
    SOURCE_ROLES,
    _changed_payload_paths,
    canonical_group_record_sha256,
    canonical_sensitivity_contract_sha256,
    evaluate_group_factor_sensitivity,
)


def sources(scenario):
    records = {
        role: {
            "source_id": f"independent-test/{scenario}/{role}",
            "sha256": f"{index + 1:064x}",
        }
        for index, role in enumerate(SOURCE_ROLES)
    }
    records["member_sections"].update(
        main_member_id="main", side_member_ids=["side"], shear_planes=1
    )
    return records


def record(scenario, *, count=12, pitch=4.0):
    return {
        "schema": SCHEMA_VERSION,
        "candidate_id": "independent-synthetic-only",
        "revision_id": "review-v1",
        "group_id": "synthetic-row",
        "scenario_id": scenario,
        "source_bindings": sources(scenario),
        "group_geometry": {
            "row_axis_xyz": [1.0, 0.0, 0.0],
            "fasteners": [
                {
                    "fastener_id": f"bolt-{index}",
                    "center_in": [index * pitch, 0.0, 0.0],
                    "nominal_diameter_in": 1.0,
                    "type": "dowel",
                }
                for index in range(count)
            ],
        },
        "load_case": {
            "case_id": "synthetic-lateral-load",
            "lateral_resultant_xyz_lbf": [1000.0, 0.0, 0.0],
        },
        "members": {
            "shear_planes": 1,
            "main": {
                "member_id": "main",
                "material": "wood",
                "elastic_modulus_psi": 1_400_000.0,
                "gross_section_area_in2": 10.0,
                "grain_axis_xyz": [1.0, 0.0, 0.0],
            },
            "side_members": [
                {
                    "member_id": "side",
                    "material": "wood",
                    "elastic_modulus_psi": 1_400_000.0,
                    "gross_section_area_in2": 5.0,
                    "grain_axis_xyz": [1.0, 0.0, 0.0],
                }
            ],
        },
    }


def compare(baseline, sensitivity, paths):
    contract = {
        "contract_id": "independent-synthetic-path-contract",
        "source_id": "independent-test/path-contract",
        "sha256": "unbound",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "independent-synthetic-only",
        "revision_id": "review-v1",
        "group_id": "synthetic-row",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": paths,
    }
    contract["sha256"] = canonical_sensitivity_contract_sha256(contract)
    binding = {
        key: contract[key]
        for key in ("contract_id", "source_id", "sha256", "review_status")
    }
    result = evaluate_group_factor_sensitivity(
        baseline,
        sensitivity,
        baseline_expected_bindings=sources("baseline"),
        baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
        sensitivity_expected_bindings=sources("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(sensitivity),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=binding,
    )
    # Every positive and negative public-API probe retains the method boundary.
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"
    return result


def assert_calculated(result, paths):
    assert result["status"] == "calculated_method_sensitivity_only"
    assert result["reason_codes"] == []
    assert result["changed_input_paths"] == sorted(set(paths))
    assert result["sensitivity_classification"] == "composite_scenario"
    assert "not the adopted criterion demand/capacity ratio" in result["interpretation"]


def assert_mismatch(result):
    assert result["status"] == "pending"
    assert result["reason_codes"] == [
        "sensitivity_changed_input_paths_do_not_match_contract"
    ]
    assert result["cg"] is None


TWELVE_PATHS_NUMERIC = [
    f"group_geometry.fasteners[{index}].center_in[0]" for index in range(1, 12)
]
TWELVE_PATHS_LEXICAL = [
    f"group_geometry.fasteners[{index}].center_in[0]"
    for index in (10, 11, 1, 2, 3, 4, 5, 6, 7, 8, 9)
]


@pytest.mark.parametrize(
    "paths",
    [
        TWELVE_PATHS_NUMERIC,
        TWELVE_PATHS_LEXICAL,
        list(reversed(TWELVE_PATHS_NUMERIC)),
        TWELVE_PATHS_NUMERIC + [TWELVE_PATHS_NUMERIC[0]],
    ],
    ids=["numeric-order", "lexical-order", "reversed-order", "duplicate-normalized"],
)
def test_twelve_fasteners_normalize_to_lexical_order(paths):
    baseline = record("baseline", pitch=4.0)
    sensitivity = record("sensitivity", pitch=2.0)
    result = compare(baseline, sensitivity, paths)
    assert_calculated(result, TWELVE_PATHS_LEXICAL)
    assert result["changed_input_paths"] == TWELVE_PATHS_LEXICAL


@pytest.mark.parametrize("mutation", ["omit-10", "extra-0", "omit-11", "wrong-axis"])
def test_twelve_fasteners_reject_inexact_path_contracts(mutation):
    paths = list(TWELVE_PATHS_NUMERIC)
    if mutation == "omit-10":
        paths.remove("group_geometry.fasteners[10].center_in[0]")
    elif mutation == "omit-11":
        paths.remove("group_geometry.fasteners[11].center_in[0]")
    elif mutation == "extra-0":
        paths.append("group_geometry.fasteners[0].center_in[0]")
    else:
        paths[-1] = "group_geometry.fasteners[11].center_in[1]"
    assert_mismatch(compare(record("baseline"), record("sensitivity", pitch=2.0), paths))


@pytest.mark.parametrize("counts", [(10, 12), (12, 10)], ids=["growth", "shrinkage"])
def test_multiple_added_or_removed_fasteners_require_length_and_every_whole_item(counts):
    baseline = record("baseline", count=counts[0])
    sensitivity = record("sensitivity", count=counts[1])
    complete = [
        "group_geometry.fasteners.length",
        "group_geometry.fasteners[10]",
        "group_geometry.fasteners[11]",
    ]
    assert_calculated(compare(baseline, sensitivity, complete), complete)
    for omitted in complete:
        assert_mismatch(compare(baseline, sensitivity, [p for p in complete if p != omitted]))
    assert_mismatch(compare(baseline, sensitivity, complete[:1]))
    assert_mismatch(
        compare(
            baseline,
            sensitivity,
            [complete[0], complete[1] + ".center_in[0]", complete[2]],
        )
    )


@pytest.mark.parametrize("reverse", [False, True], ids=["empty-growth", "to-empty"])
def test_empty_list_additions_and_removals_use_whole_item_paths(reverse):
    baseline = record("baseline")
    sensitivity = record("sensitivity")
    values = [[], [{"nested": [1, 2]}, "second"]]
    if reverse:
        values.reverse()
    baseline["producer_extension"] = values[0]
    sensitivity["producer_extension"] = values[1]
    complete = [
        "producer_extension.length",
        "producer_extension[0]",
        "producer_extension[1]",
    ]
    assert_calculated(compare(baseline, sensitivity, complete), complete)
    assert_mismatch(compare(baseline, sensitivity, complete[:1]))
    assert_mismatch(compare(baseline, sensitivity, complete[1:]))


ESCAPED_KEYS = [
    ("a.b", r"a\.b", "a.b"),
    ("a[0]", r"a\[0\]", "a[0]"),
    ("[", r"\[", "["),
    ("]", r"\]", "]"),
    ("a\\b", r"a\\b", "a\\b"),
    ("a\\.b", r"a\\\.b", r"a\.b"),
    ("", r"\e", r"\\e"),
    ("\\e", r"\\e", r"\e"),
]


@pytest.mark.parametrize("key,escaped,wrong", ESCAPED_KEYS)
def test_special_object_keys_match_only_their_exact_escaped_paths(key, escaped, wrong):
    baseline = record("baseline")
    sensitivity = record("sensitivity")
    baseline["producer_extension"] = {key: 1}
    sensitivity["producer_extension"] = {key: 2}
    path = f"producer_extension.{escaped}"
    assert_calculated(compare(baseline, sensitivity, [path]), [path])
    assert_mismatch(compare(baseline, sensitivity, [f"producer_extension.{wrong}"]))


@pytest.mark.parametrize("operation", ["add", "remove"])
def test_empty_and_literal_backslash_e_keys_remain_distinct_on_addition_or_removal(operation):
    baseline = record("baseline")
    sensitivity = record("sensitivity")
    extensions = [{}, {"": 1, "\\e": 2}]
    if operation == "remove":
        extensions.reverse()
    baseline["producer_extension"] = extensions[0]
    sensitivity["producer_extension"] = extensions[1]
    complete = [r"producer_extension.\e", r"producer_extension.\\e"]
    assert_calculated(compare(baseline, sensitivity, complete), complete)
    for omitted in complete:
        assert_mismatch(compare(baseline, sensitivity, [p for p in complete if p != omitted]))


def test_literal_dot_brackets_backslash_and_nested_paths_do_not_collapse_together():
    baseline = record("baseline")
    sensitivity = record("sensitivity")
    baseline["producer_extension"] = {
        "a.b": 1,
        "a": {"b": 1},
        "x[0]": 1,
        "x": [1],
        "\\e": 1,
        "": 1,
        "a\\b": 1,
    }
    sensitivity["producer_extension"] = {
        "a.b": 2,
        "a": {"b": 2},
        "x[0]": 2,
        "x": [2],
        "\\e": 2,
        "": 2,
        "a\\b": 2,
    }
    complete = [
        r"producer_extension.a\.b",
        "producer_extension.a.b",
        r"producer_extension.x\[0\]",
        "producer_extension.x[0]",
        r"producer_extension.\\e",
        r"producer_extension.\e",
        r"producer_extension.a\\b",
    ]
    assert len(set(complete)) == 7
    assert_calculated(compare(baseline, sensitivity, complete), complete)
    for omitted in complete:
        assert_mismatch(compare(baseline, sensitivity, [p for p in complete if p != omitted]))


def test_bounded_key_encoding_injectivity_and_nested_separation():
    # This is a bounded encoding probe, not a proof for arbitrary JSON trees.
    alphabet = ("a", ".", "[", "]", "\\", "e")
    keys = [
        "".join(chars)
        for size in range(4)
        for chars in itertools.product(alphabet, repeat=size)
    ]
    encoded = {}
    for key in keys:
        paths = _changed_payload_paths({key: 0}, {key: 1})
        assert len(paths) == 1
        assert paths[0] not in encoded, (key, encoded.get(paths[0]))
        encoded[paths[0]] = key
    assert len(encoded) == 259

    # Enumerate two-segment paths independently, including empty keys.
    seen = set(encoded)
    short_keys = ["", "a", ".", "[", "]", "\\", "e", "a.b", "a[0]", "\\e"]
    for outer, inner in itertools.product(short_keys, repeat=2):
        [path] = _changed_payload_paths({outer: {inner: 0}}, {outer: {inner: 1}})
        assert path not in seen
        seen.add(path)
    assert len(seen) == 359


def test_only_root_scenario_and_source_bindings_are_ignored():
    baseline = record("baseline")
    sensitivity = record("sensitivity")
    baseline["producer_extension"] = {"scenario_id": "before", "source_bindings": 1}
    sensitivity["producer_extension"] = {"scenario_id": "after", "source_bindings": 2}
    complete = ["producer_extension.scenario_id", "producer_extension.source_bindings"]
    assert_calculated(compare(baseline, sensitivity, complete), complete)
    assert_mismatch(compare(baseline, sensitivity, complete[:1]))
