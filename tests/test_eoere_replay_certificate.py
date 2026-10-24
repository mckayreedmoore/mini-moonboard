"""Admission of the issued plywood replay certificate without a response solve."""

import copy

import pytest

from scripts.eoere_replay_certificate import (
    bonded_plywood_dofs,
    validate_plywood_replay,
)

FIELD = {"path": "case/field.json", "sha256": "1" * 64}
MATERIAL = {"path": "material.json", "sha256": "2" * 64}
EXPECTED_DOFS = {"eoere_cleat_left": 24, "eoere_cleat_right": 24}


def certificate():
    return {
        "schema": "eoere_leg_header_plywood_raw_operator_audit/v1",
        "field": copy.deepcopy(FIELD),
        "material": copy.deepcopy(MATERIAL),
        "source": {"path": "replay.py", "sha256": "3" * 64},
        "captured_launcher": {"path": "launcher.py", "sha256": "4" * 64},
        "raw_operator_checks": [
            {"member": member, "dofs": dofs, "maximum_K_entry_error": 5.82e-11}
            for member, dofs in EXPECTED_DOFS.items()
        ],
        "all_unchanged_owner_map_checks_retained": True,
        "field_q_actions_or_operators_changed": False,
        "physical_stiffness_qualified": False,
        "production_admission_issued": False,
    }


def test_admit_issued_two_member_certificate_without_mutating_it():
    value = certificate()
    before = copy.deepcopy(value)

    assert validate_plywood_replay(
        value, field_ref=FIELD, material_ref=MATERIAL, expected_dofs=EXPECTED_DOFS
    ) is None

    assert value == before


@pytest.mark.parametrize("change", ["duplicate", "missing", "extra", "wrong_member", "wrong_dofs"])
def test_reject_incomplete_or_mismatched_bonded_operators(change):
    value = certificate()
    rows = value["raw_operator_checks"]
    if change == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif change == "missing":
        rows.pop()
    elif change == "extra":
        rows.append(copy.deepcopy(rows[0]))
    elif change == "wrong_member":
        rows[0]["member"] = "eoere_cleat_left_outer"
    else:
        rows[0]["dofs"] = 18

    with pytest.raises(ValueError):
        validate_plywood_replay(
            value, field_ref=FIELD, material_ref=MATERIAL, expected_dofs=EXPECTED_DOFS
        )


@pytest.mark.parametrize("error", [-1e-12, 1e-6, 1.1e-6, float("nan"), float("inf"), -float("inf"), True, "0"])
def test_reject_nonfinite_negative_or_excessive_operator_error(error):
    value = certificate()
    value["raw_operator_checks"][0]["maximum_K_entry_error"] = error

    with pytest.raises(ValueError, match="operator error"):
        validate_plywood_replay(
            value, field_ref=FIELD, material_ref=MATERIAL, expected_dofs=EXPECTED_DOFS
        )


@pytest.mark.parametrize("error", [0, 9.999e-7])
def test_admit_finite_error_strictly_below_the_issued_gate(error):
    value = certificate()
    value["raw_operator_checks"][0]["maximum_K_entry_error"] = error

    validate_plywood_replay(value, field_ref=FIELD, material_ref=MATERIAL, expected_dofs=EXPECTED_DOFS)


@pytest.mark.parametrize("key,value", [
    ("schema", "other-audit/v1"),
    ("field", {"path": "old/field.json", "sha256": "1" * 64}),
    ("material", {"path": "old/material.json", "sha256": "2" * 64}),
    ("all_unchanged_owner_map_checks_retained", False),
    ("all_unchanged_owner_map_checks_retained", 1),
    ("field_q_actions_or_operators_changed", True),
    ("physical_stiffness_qualified", True),
    ("physical_stiffness_qualified", 0),
    ("production_admission_issued", True),
    ("fabrication_released", True),
    ("structural_acceptance", True),
])
def test_reject_wrong_identity_changed_operators_or_qualification_claim(key, value):
    record = certificate()
    record[key] = value

    with pytest.raises(ValueError):
        validate_plywood_replay(
            record, field_ref=FIELD, material_ref=MATERIAL, expected_dofs=EXPECTED_DOFS
        )


@pytest.mark.parametrize("key", list(certificate()))
def test_reject_missing_issued_certificate_field(key):
    record = certificate()
    del record[key]

    with pytest.raises(ValueError):
        validate_plywood_replay(
            record, field_ref=FIELD, material_ref=MATERIAL, expected_dofs=EXPECTED_DOFS
        )


@pytest.mark.parametrize("key", ["field", "material", "source", "captured_launcher"])
@pytest.mark.parametrize("bad_ref", [
    {"path": "../old", "sha256": "1" * 64},
    {"path": "/outside", "sha256": "1" * 64},
    {"path": "local", "sha256": "missing"},
    {"path": "local", "sha256": "1" * 64, "extra": True},
])
def test_reject_malformed_repository_binding(key, bad_ref):
    record = certificate()
    record[key] = bad_ref
    field = bad_ref if key == "field" else FIELD
    material = bad_ref if key == "material" else MATERIAL

    with pytest.raises(ValueError):
        validate_plywood_replay(
            record, field_ref=field, material_ref=material, expected_dofs=EXPECTED_DOFS
        )


def manifest(nodes=4):
    return {
        "schema": "eoere_first_order_original_operator_bundle/v1",
        "final_ndof": 100,
        "coordinate_map": {
            "schema": "eoere_first_order_owned_coordinate_map/v1",
            "timber": {
                name: {
                    "index": [list(range(start + 6 * i, start + 6 * (i + 1))) for i in range(nodes)],
                    "source": {"name": name, "explicit_plywood_operator": {"EA_N": 100}},
                }
                for name, start in (("eoere_cleat_left", 0), ("eoere_cleat_right", 50))
            },
        },
    }


def test_derive_expected_dofs_from_captured_member_maps():
    assert bonded_plywood_dofs(manifest()) == EXPECTED_DOFS
    assert bonded_plywood_dofs(manifest(nodes=3)) == {
        "eoere_cleat_left": 18, "eoere_cleat_right": 18
    }


@pytest.mark.parametrize("change", ["wrong_schema", "missing", "extra_leaf", "aliased_index", "wrong_source"])
def test_reject_incomplete_or_aliased_captured_bonded_maps(change):
    value = manifest()
    timber = value["coordinate_map"]["timber"]
    left = timber["eoere_cleat_left"]
    if change == "wrong_schema":
        value["schema"] = "other/v1"
    elif change == "missing":
        del timber["eoere_cleat_right"]
    elif change == "extra_leaf":
        timber["eoere_cleat_left_outer"] = copy.deepcopy(left)
    elif change == "aliased_index":
        left["index"][1] = copy.deepcopy(left["index"][0])
    else:
        left["source"]["name"] = "eoere_cleat_right"

    with pytest.raises(ValueError):
        bonded_plywood_dofs(value)
