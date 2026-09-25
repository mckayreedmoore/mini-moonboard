"""Authenticated signed unit cases and exact nodal wrench distributions."""

import json

import pytest

from fea.wood_joint_patch_unit_cases import (
    CASE_SIGNS,
    COMPONENTS,
    DEFAULT_MOMENT_TOLERANCE_NMM,
    EXPECTED_OWNER_PAIRS,
    MECHANICS_MANIFEST_PATH,
    ROOT,
    PatchNodeWeight,
    distribute_unit_case_to_nodes,
    distribute_wrench_to_nodes,
    distributed_unit_case_payload,
    load_wj16_unit_case_plan,
    unit_case_plan_payload,
)
from fea.wood_joint_patch_wrench import Wrench

PLAN = load_wj16_unit_case_plan()
FIRST_INTERFACE = next(iter(EXPECTED_OWNER_PAIRS))
DATUM = next(
    row.point_xyz_mm
    for row in PLAN.interface_datums
    if row.interface_id == FIRST_INTERFACE
)
PATCH = (
    PatchNodeWeight(1001, (DATUM[0] - 20.0, DATUM[1] - 15.0, DATUM[2] + 2.0), 2.0),
    PatchNodeWeight(1002, (DATUM[0] + 25.0, DATUM[1] - 15.0, DATUM[2] + 2.0), 3.0),
    PatchNodeWeight(1003, (DATUM[0] - 20.0, DATUM[1] + 30.0, DATUM[2] + 2.0), 4.0),
    PatchNodeWeight(1004, (DATUM[0] + 25.0, DATUM[1] + 30.0, DATUM[2] + 2.0), 5.0),
)


def test_authenticated_plan_defines_48_isolated_cases_and_four_datums():
    assert len(PLAN.interface_datums) == 4
    assert len(PLAN.cases) == 48
    assert len({case.case_id for case in PLAN.cases}) == 48
    assert dict(PLAN.owner_pairs) == EXPECTED_OWNER_PAIRS

    for interface_id in EXPECTED_OWNER_PAIRS:
        cases = [case for case in PLAN.cases if case.interface_id == interface_id]
        assert [(case.component, case.sign) for case in cases] == [
            (component, sign) for component in COMPONENTS for sign in CASE_SIGNS
        ]
        for case in cases:
            assert case.owner_bodies == EXPECTED_OWNER_PAIRS[interface_id]
            assert case.datum_xyz_mm == next(
                datum.point_xyz_mm
                for datum in PLAN.interface_datums
                if datum.interface_id == interface_id
            )
            expected_force = [0.0, 0.0, 0.0]
            expected_moment = [0.0, 0.0, 0.0]
            index = "XTN".index(case.component[-1])
            if case.component.startswith("F"):
                expected_force[index] = float(case.sign)
            else:
                expected_moment[index] = float(case.sign)
            assert case.host_wrench_local == Wrench(
                tuple(expected_force), tuple(expected_moment)
            )
            assert case.cleat_wrench_global == Wrench(
                tuple(-value for value in case.host_wrench_global.force_n),
                tuple(-value for value in case.host_wrench_global.moment_nmm),
            )


def test_case_payload_is_json_compatible_and_labels_its_limits():
    payload = unit_case_plan_payload(PLAN)
    assert payload["schema"] == "wood_joint_patch_unit_cases/v1"
    assert payload["status"] == "diagnostic_case_definitions_only_no_native_solve"
    assert payload["counts"] == {
        "interfaces": 4,
        "signed_cases": 48,
        "cases_per_interface": 12,
    }
    assert len(json.dumps(payload, allow_nan=False)) > 0


def test_loader_rejects_any_change_to_the_pinned_mechanics_manifest(tmp_path):
    manifest = (ROOT / MECHANICS_MANIFEST_PATH).read_bytes()
    tampered = tmp_path / "mechanics-inputs.json"
    tampered.write_bytes(manifest + b"\n")
    with pytest.raises(ValueError, match="pinned full-stock input digest"):
        load_wj16_unit_case_plan(tampered)


@pytest.mark.parametrize("component", COMPONENTS)
@pytest.mark.parametrize("sign", CASE_SIGNS)
def test_each_signed_component_distribution_closes_both_owner_wrenches(component, sign):
    case = next(
        row
        for row in PLAN.cases
        if row.interface_id == FIRST_INTERFACE
        and row.component == component
        and row.sign == sign
    )
    result = distribute_unit_case_to_nodes(
        case,
        {
            case.host_body: PATCH,
            case.cleat_body: PATCH,
        },
    )

    assert len(result.owner_distributions) == 2
    assert result.action_reaction_check.passed
    assert result.action_reaction_check.owner_bodies == case.owner_bodies
    assert result.action_reaction_check.residual_global == Wrench(
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    )
    payload = distributed_unit_case_payload(result)
    assert payload["case_id"] == case.case_id
    assert payload["action_reaction"]["passed"]
    assert len(payload["owner_distributions"]) == 2
    assert len(json.dumps(payload, allow_nan=False)) > 0
    for row in result.owner_distributions:
        serialized = next(
            item
            for item in payload["owner_distributions"]
            if item["owner_body"] == row.owner_body
        )
        assert len(serialized["nodal_loads"]) == len(PATCH)
        assert [load["tributary_area_mm2"] for load in serialized["nodal_loads"]] == [
            node.tributary_area_mm2 for node in PATCH
        ]
        assert row.reconstructed_wrench_global.force_n == pytest.approx(
            row.target_wrench_global.force_n, abs=1e-10
        )
        assert row.reconstructed_wrench_global.moment_nmm == pytest.approx(
            row.target_wrench_global.moment_nmm,
            abs=DEFAULT_MOMENT_TOLERANCE_NMM,
        )
        assert row.scaled_gram_relative_pivot > 1e-12


def test_distribution_rejects_collinear_or_duplicate_node_patches():
    wrench = Wrench((1.0, -2.0, 3.0), (4.0, 5.0, -6.0))
    collinear = (
        PatchNodeWeight(1, (0.0, 0.0, 0.0), 1.0),
        PatchNodeWeight(2, (10.0, 0.0, 0.0), 1.0),
        PatchNodeWeight(3, (30.0, 0.0, 0.0), 1.0),
    )
    with pytest.raises(ValueError, match="rank-deficient"):
        distribute_wrench_to_nodes(collinear, (0.0, 0.0, 0.0), wrench)

    duplicate_ids = (
        PATCH[0],
        PatchNodeWeight(PATCH[0].node_id, PATCH[1].point_xyz_mm, 1.0),
        PATCH[2],
    )
    with pytest.raises(ValueError, match="duplicate node id"):
        distribute_wrench_to_nodes(duplicate_ids, DATUM, wrench)


def test_tributary_areas_set_the_minimum_norm_force_weights():
    centroid = tuple(
        sum(node.tributary_area_mm2 * node.point_xyz_mm[axis] for node in PATCH)
        / sum(node.tributary_area_mm2 for node in PATCH)
        for axis in range(3)
    )
    target = Wrench((3.0, -6.0, 1.0), (0.0, 0.0, 0.0))
    result = distribute_wrench_to_nodes(
        PATCH,
        centroid,
        target,
        owner_body="synthetic_patch_owner",
    )

    total_area = sum(node.tributary_area_mm2 for node in PATCH)
    for node, load in zip(PATCH, result.nodal_forces, strict=True):
        expected_weight = node.tributary_area_mm2 / total_area
        assert load.force_xyz_n == pytest.approx(
            tuple(expected_weight * component for component in target.force_n),
            abs=1e-12,
        )
        assert load.point_xyz_mm == node.point_xyz_mm
        assert load.tributary_area_mm2 == node.tributary_area_mm2


def test_unit_case_requires_exactly_its_two_owners_and_complete_patch_records():
    case = PLAN.cases[0]
    with pytest.raises(ValueError, match="owners must match exactly"):
        distribute_unit_case_to_nodes(case, {case.host_body: PATCH})

    with pytest.raises(ValueError, match="tributary_area_mm2"):
        distribute_wrench_to_nodes(
            [
                {"node_id": 1, "point_xyz_mm": PATCH[0].point_xyz_mm},
                PATCH[1],
                PATCH[2],
            ],
            DATUM,
            Wrench((1.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        )
