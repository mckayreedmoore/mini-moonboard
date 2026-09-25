"""Focused tests for the standalone pre-solve current load contract."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from scripts.wood_joint_current_load_cases import (
    CASE_INPUTS,
    DYNAMIC_FACTOR,
    GRAVITY_M_PER_S2,
    PANEL_PATCH_SIZE_MM,
    POUNDS,
    POUNDS_TO_KG,
    STANDOFF_MM,
    build_current_load_contract,
    build_current_load_contract_from_datum_file,
    validate_current_load_contract,
)


@pytest.fixture
def explicit_geometry():
    return {
        "hold_face_datums_global_xyz_mm": {
            "A12": [100.0, 10.0, 500.0],
            "K12": [900.0, 10.0, 500.0],
            "A1": [100.0, 10.0, 100.0],
        },
        "panel_outward_normal_global_xyz": [0.0, 1.0, 0.0],
        "panel_midplane_applicationpoints_global_xyz_mm": {
            "A12": [100.0, 0.0, 500.0],
            "K12": [900.0, 0.0, 500.0],
            "A1": [100.0, 0.0, 100.0],
        },
    }


@pytest.fixture
def transform_source():
    return {
        "source_id": "test-fixture/explicit-current-global-transform.json",
        "sha256": hashlib.sha256(b"explicit test geometry source").hexdigest(),
        "description": "Synthetic explicit global points used only by this unit test.",
    }


def build(explicit_geometry, transform_source):
    return build_current_load_contract(
        **explicit_geometry,
        transform_source=transform_source,
    )


def _resign(contract):
    payload = dict(contract)
    payload.pop("contract_sha256", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    contract["contract_sha256"] = hashlib.sha256(encoded).hexdigest()


def test_exact_six_case_contract_has_distinct_patch_standoff_and_rebuilt_wrenches(
    explicit_geometry, transform_source
):
    contract = build(explicit_geometry, transform_source)
    cases = contract["cases"]
    assert [(case["case_id"], case["hold_id"]) for case in cases] == [
        (case_id, hold) for case_id, hold, _ in CASE_INPUTS
    ]
    assert len(cases) == 6

    vertical = -DYNAMIC_FACTOR * POUNDS * POUNDS_TO_KG * GRAVITY_M_PER_S2
    assert cases[0]["applied_force_global_xyz_n"] == pytest.approx([0.0, 300.0, vertical])
    assert cases[1]["applied_force_global_xyz_n"] == pytest.approx([0.0, -300.0, vertical])
    assert cases[2]["applied_force_global_xyz_n"] == pytest.approx([-300.0, 0.0, vertical])
    assert cases[3]["applied_force_global_xyz_n"] == pytest.approx([300.0, 0.0, vertical])

    # The panel patch remains at the caller's face datum while the force point
    # is 100 mm outward; the panel-midplane point is independently supplied.
    case = cases[0]
    assert case["panel_patch"]["size_mm"] == PANEL_PATCH_SIZE_MM == 20.0
    assert case["panel_patch"]["center_global_xyz_mm"] == [100.0, 10.0, 500.0]
    assert case["standoff"]["distance_mm"] == STANDOFF_MM == 100.0
    assert case["standoff"]["force_application_point_global_xyz_mm"] == [100.0, 110.0, 500.0]
    assert case["panel_midplane_applicationpoint_global_xyz_mm"] == [100.0, 0.0, 500.0]
    assert case["moment_about_panel_midplane_applicationpoint_global_xyz_nmm"] == pytest.approx(
        [-244652.1888393275, 0.0, 0.0]
    )
    assert case["applied_wrench"]["force_global_xyz_n"] == pytest.approx(
        case["applied_force_global_xyz_n"]
    )
    validate_current_load_contract(contract)


def test_contract_records_current_source_provenance_without_legacy_location_derivation(
    explicit_geometry, transform_source
):
    contract = build(explicit_geometry, transform_source)
    provenance = contract["source_provenance"]
    assert provenance["current_transform_source"] == transform_source
    assert provenance["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1"
    assert provenance["reviewed_repository_commit"] == "b1e8707d"
    assert provenance["files"]["scripts/clear_space_batch.py"]["sha256"]
    assert provenance["files"]["fea/current_response_model.py"]["sha256"]
    assert "not used to create current global coordinates" in provenance["source_use_note"]
    assert contract["current_geometry_inputs"]["hold_face_datums_global_xyz_mm"] == explicit_geometry[
        "hold_face_datums_global_xyz_mm"
    ]


def test_exact_case_validation_rejects_changed_case_identity_and_force(
    explicit_geometry, transform_source
):
    contract = build(explicit_geometry, transform_source)
    wrong_id = copy.deepcopy(contract)
    wrong_id["cases"][0]["case_id"] = "a12-forward"
    _resign(wrong_id)
    with pytest.raises(ValueError, match="exact six frozen case IDs"):
        validate_current_load_contract(wrong_id)

    wrong_force = copy.deepcopy(contract)
    wrong_force["cases"][0]["applied_force_global_xyz_n"][0] = 0.01
    _resign(wrong_force)
    with pytest.raises(ValueError, match="applied global force"):
        validate_current_load_contract(wrong_force)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("panel_outward_normal_global_xyz", [0.0, 2.0, 0.0], "already be a unit vector"),
        ("hold_face_datums_global_xyz_mm", {"A12": [0, 0, 0], "K12": [1, 2, 3]}, "exactly A12, K12, A1"),
        ("panel_midplane_applicationpoints_global_xyz_mm", {"A12": [0, 0, 0], "K12": [1, 2, 3]}, "exactly A12, K12, A1"),
    ],
)
def test_rejects_incomplete_or_implicit_current_geometry(
    explicit_geometry, transform_source, field, value, match
):
    inputs = copy.deepcopy(explicit_geometry)
    inputs[field] = value
    with pytest.raises(ValueError, match=match):
        build_current_load_contract(**inputs, transform_source=transform_source)


def test_requires_transform_source_sha256(explicit_geometry):
    bad_source = {
        "source_id": "live-current-transform",
        "sha256": "not-a-digest",
        "description": "Explicit global hold and panel transform source.",
    }
    with pytest.raises(ValueError, match="sha256"):
        build_current_load_contract(**explicit_geometry, transform_source=bad_source)


def test_reviewed_current_datum_file_builds_contract_and_is_hash_bound():
    contract = build_current_load_contract_from_datum_file()
    provenance = contract["source_provenance"]
    source_path = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-datums.json"
    source_binding = provenance["files"][source_path]
    assert source_binding["sha256"] == provenance["current_transform_source"]["sha256"]
    assert source_binding["role"] == "explicit current hold/panel global-datum input artifact"
    assert provenance["files"]["mini_moonboard/box_frame.py"]["sha256"]

    with open(source_path, encoding="utf-8") as source_file:
        datum_file = json.load(source_file)
    a12 = datum_file["holds"]["A12"]
    case = contract["cases"][0]
    assert case["panel_patch"]["center_global_xyz_mm"] == a12["face_datum_global_mm"]
    assert case["panel_midplane_applicationpoint_global_xyz_mm"] == a12[
        "panel_midplane_reference_global_mm"
    ]
    assert case["standoff"]["force_application_point_global_xyz_mm"] == pytest.approx(
        [
            a12["face_datum_global_mm"][i]
            + STANDOFF_MM * a12["outward_normal_global"][i]
            for i in range(3)
        ]
    )
    validate_current_load_contract(contract)
