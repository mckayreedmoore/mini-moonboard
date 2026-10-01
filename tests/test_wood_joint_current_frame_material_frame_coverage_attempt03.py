import copy
import math
from pathlib import Path

import pytest

from scripts.wood_joint_current_frame_material_frame_coverage_attempt02 import (
    load_pinned_sources as load_attempt02_sources,
)
from scripts.wood_joint_current_frame_material_frame_coverage_attempt03 import (
    build_coverage,
    load_pinned_sources,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_RADIAL_AXIS = {"ring_R_on_X": "X", "ring_R_on_T": "T"}
SCENARIO_TANGENTIAL_AXIS = {"ring_R_on_X": "T", "ring_R_on_T": "X"}


@pytest.fixture(scope="module")
def source_documents():
    _, documents = load_attempt02_sources(REPO_ROOT)
    return documents


def compile_sources(documents):
    return build_coverage(
        documents["manifest"],
        documents["descriptor"],
        documents["timber_map"],
        documents["block_map"],
    )


def _close_vector(actual, expected, *, tolerance=1e-8):
    assert len(actual) == len(expected) == 3
    assert all(
        math.isfinite(float(left))
        and math.isfinite(float(right))
        and abs(float(left) - float(right)) <= tolerance
        for left, right in zip(actual, expected)
    )


def _cross(left, right):
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def test_attempt03_preserves_conditional_frames_and_binds_both_block_axes(source_documents):
    coverage = compile_sources(source_documents)
    assert coverage["attempt_id"] == "current-frame-material-frame-coverage-attempt03"
    assert len(coverage["members"]) == 50
    assert sum(row["coverage_class"] == "frame_timber" for row in coverage["members"]) == 20
    assert sum(row["coverage_class"] == "candidate_block" for row in coverage["members"]) == 24
    assert sum(row["coverage_class"] == "plywood_panel_unresolved" for row in coverage["members"]) == 6

    source_blocks = {row["part_id"]: row for row in source_documents["block_map"]["members"]}
    checked_grain_members = 0
    for row in coverage["members"]:
        frame = row["conditional_material_frame_scenarios"]
        if row["coverage_class"] == "frame_timber":
            axes = frame["source_frame_axes_global_xyz"]
            components = frame["longitudinal_components_in_source_frame_xyz"]
            reconstructed = [
                sum(components[axis] * axes[axis][coordinate] for axis in ("N", "T", "X"))
                for coordinate in range(3)
            ]
            _close_vector(frame["longitudinal_direction_global_xyz"], reconstructed)
            checked_grain_members += 1
            continue

        if row["coverage_class"] != "candidate_block":
            assert row["coverage_class"] == "plywood_panel_unresolved"
            continue

        checked_grain_members += 1
        source = source_blocks[row["member_id"]]
        axes = source["source_frame_axes_global_xyz"]
        source_grain = source["conditional_grain_assignment"]["grain_direction_global_xyz"]
        _close_vector(frame["longitudinal_direction_global_xyz"], source_grain)
        assert [case["scenario_id"] for case in frame["transverse_assignments"]] == [
            "ring_R_on_X",
            "ring_R_on_T",
        ]
        for case in frame["transverse_assignments"]:
            radial_axis = SCENARIO_RADIAL_AXIS[case["scenario_id"]]
            tangential_axis = SCENARIO_TANGENTIAL_AXIS[case["scenario_id"]]
            assert case["radial_axis_local_name"] == radial_axis
            assert case["tangential_axis_local_name"] == tangential_axis
            _close_vector(case["source_radial_axis_global_xyz"], axes[radial_axis])
            _close_vector(case["source_tangential_axis_global_xyz"], axes[tangential_axis])
            _close_vector(case["material_R_global_xyz"], axes[radial_axis])
            _close_vector(case["material_T_global_xyz"], case["tangential_T_global_xyz"])
            tangent_axis = axes[tangential_axis]
            opposite_tangent_axis = [-component for component in tangent_axis]
            assert case["material_T_global_xyz"] == pytest.approx(tangent_axis) or case[
                "material_T_global_xyz"
            ] == pytest.approx(opposite_tangent_axis)
            points = case["calculix_orientation_points_global_xyz"]
            _close_vector(points[:3], case["longitudinal_L_global_xyz"])
            _close_vector(points[3:], axes[radial_axis])
            _close_vector(
                _cross(case["longitudinal_L_global_xyz"], case["material_R_global_xyz"]),
                case["material_T_global_xyz"],
            )

    assert checked_grain_members == 44
    assert all(value is False for value in coverage["readiness"].values())
    assert all(value is False for value in coverage["acceptance"].values())
    assert all(value is False for value in coverage["native_execution"].values())
    assert all(value is False for value in coverage["release"].values())
    assert all(
        all(value is None for value in member["material_assignment"].values())
        for member in coverage["members"]
    )
    assert all(
        all(value is None for value in member["solver_mapping"].values())
        for member in coverage["members"]
    )


def test_tangential_axis_label_only_mutation_fails(source_documents):
    documents = copy.deepcopy(source_documents)
    case_x = next(
        case
        for case in documents["block_map"]["members"][0]["transverse_assignment_cases"]
        if case["scenario_id"] == "ring_R_on_X"
    )
    case_x["tangential_axis_local_name"] = "X"

    with pytest.raises(ValueError, match="tangential axis label disagrees with scenario ID"):
        compile_sources(documents)


def test_swapping_valid_radial_axes_while_preserving_scenario_ids_fails(source_documents):
    documents = copy.deepcopy(source_documents)
    cases = documents["block_map"]["members"][0]["transverse_assignment_cases"]
    case_x = next(item for item in cases if item["scenario_id"] == "ring_R_on_X")
    case_t = next(item for item in cases if item["scenario_id"] == "ring_R_on_T")
    case_x["material_axes_global_xyz"], case_t["material_axes_global_xyz"] = (
        case_t["material_axes_global_xyz"],
        case_x["material_axes_global_xyz"],
    )
    case_x["calculix_orientation_points_global_xyz"], case_t[
        "calculix_orientation_points_global_xyz"
    ] = (
        case_t["calculix_orientation_points_global_xyz"],
        case_x["calculix_orientation_points_global_xyz"],
    )

    with pytest.raises(ValueError, match="radial R axis disagrees with scenario label"):
        compile_sources(documents)


def test_radial_and_tangential_labels_are_both_checked(source_documents):
    documents = copy.deepcopy(source_documents)
    cases = documents["block_map"]["members"][0]["transverse_assignment_cases"]
    cases[0]["radial_axis_local_name"] = "T"

    with pytest.raises(ValueError, match="radial axis label disagrees with scenario ID"):
        compile_sources(documents)


def test_sign_flip_cannot_break_the_right_handed_source_frame(source_documents):
    documents = copy.deepcopy(source_documents)
    case_t = next(
        case
        for case in documents["block_map"]["members"][0]["transverse_assignment_cases"]
        if case["scenario_id"] == "ring_R_on_T"
    )
    case_t["material_axes_global_xyz"]["T"] = [
        -value for value in case_t["material_axes_global_xyz"]["T"]
    ]

    with pytest.raises(ValueError, match="not right-handed"):
        compile_sources(documents)


def test_attempt03_pins_attempt02_and_complete_review_lineage():
    pins, documents = load_pinned_sources(REPO_ROOT)

    assert pins["attempt02_artifact_count"] == 7
    assert pins["inherited_source_file_count"] == 61
    assert pins["authenticated_file_count"] == 68
    assert len(pins["source_lineage_files"]) == 68
    assert pins["attempt02_review"]["sha256"] == (
        "a84586a9dbfd38cea10701fa68e158acc8675c261d436c9d8fdf45fec895d1fd"
    )
    assert pins["attempt01_review"]["sha256"] == (
        "254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405"
    )
    assert len(documents["coverage"]["members"]) == 50
