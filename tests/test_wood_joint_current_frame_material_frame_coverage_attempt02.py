import copy
from pathlib import Path

import pytest

from scripts.wood_joint_current_frame_material_frame_coverage_attempt01 import (
    load_pinned_sources as load_attempt01_sources,
)
from scripts.wood_joint_current_frame_material_frame_coverage_attempt02 import (
    build_coverage,
    load_pinned_sources,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def source_documents():
    _, documents = load_attempt01_sources(REPO_ROOT)
    return documents


def compile_sources(documents):
    return build_coverage(
        documents["manifest"],
        documents["descriptor"],
        documents["timber_map"],
        documents["block_map"],
    )


def test_attempt02_preserves_axis_bound_cases_and_attempt01_scope(source_documents):
    coverage = compile_sources(source_documents)
    assert coverage["attempt_id"] == "current-frame-material-frame-coverage-attempt02"
    assert len(coverage["members"]) == 50
    assert sum(row["coverage_class"] == "frame_timber" for row in coverage["members"]) == 20
    assert sum(row["coverage_class"] == "candidate_block" for row in coverage["members"]) == 24
    assert sum(row["coverage_class"] == "plywood_panel_unresolved" for row in coverage["members"]) == 6

    blocks = [row for row in coverage["members"] if row["coverage_class"] == "candidate_block"]
    source_blocks = {
        row["part_id"]: row for row in source_documents["block_map"]["members"]
    }
    for row in blocks:
        scenarios = row["conditional_material_frame_scenarios"]["transverse_assignments"]
        assert [item["scenario_id"] for item in scenarios] == [
            "ring_R_on_X",
            "ring_R_on_T",
        ]
        assert {item["scenario_id"] for item in scenarios} == {"ring_R_on_X", "ring_R_on_T"}
        source_axes = source_blocks[row["member_id"]]["source_frame_axes_global_xyz"]
        for item in scenarios:
            expected_axis = "X" if item["scenario_id"] == "ring_R_on_X" else "T"
            assert item["radial_axis_local_name"] == expected_axis
            assert item["source_radial_axis_global_xyz"] == source_axes[expected_axis]
            assert item["material_R_global_xyz"] == source_axes[expected_axis]
            assert item["material_R_global_xyz"] == item["calculix_orientation_points_global_xyz"][3:]

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


def test_radial_axis_label_must_match_scenario_id(source_documents):
    documents = copy.deepcopy(source_documents)
    case_x = documents["block_map"]["members"][0]["transverse_assignment_cases"][0]
    case_x["radial_axis_local_name"] = "T"

    with pytest.raises(ValueError, match="radial axis label disagrees with scenario ID"):
        compile_sources(documents)


def test_calculix_radial_orientation_point_must_match_source_axis(source_documents):
    documents = copy.deepcopy(source_documents)
    case_x = next(
        item
        for item in documents["block_map"]["members"][0]["transverse_assignment_cases"]
        if item["scenario_id"] == "ring_R_on_X"
    )
    source_t = documents["block_map"]["members"][0]["source_frame_axes_global_xyz"]["T"]
    case_x["calculix_orientation_points_global_xyz"][3:] = source_t

    with pytest.raises(ValueError, match="CalculiX radial point disagrees with source axis"):
        compile_sources(documents)


def test_attempt02_pins_attempt01_review_packet_and_all_original_sources():
    pins, documents = load_pinned_sources(REPO_ROOT)

    assert pins["attempt01_artifact_count"] == 7
    assert pins["original_source_file_count"] == 54
    assert pins["authenticated_file_count"] == 61
    assert pins["attempt01_independent_review"]["sha256"] == (
        "254aeb9a09447d10c461e187b8c92210f05dd793582f621d28cee2e821b0e405"
    )
    assert len(documents["coverage"]["members"]) == 50
