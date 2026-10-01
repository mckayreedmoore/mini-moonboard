import copy
from pathlib import Path

import pytest

from scripts.wood_joint_current_frame_material_frame_coverage_attempt01 import (
    build_coverage,
    load_pinned_sources,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ATTEMPT = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-material-frame-coverage-attempt01"
)


@pytest.fixture(scope="module")
def source_documents():
    _, documents = load_pinned_sources(REPO_ROOT)
    return documents


def compile_sources(documents):
    return build_coverage(
        documents["manifest"],
        documents["descriptor"],
        documents["timber_map"],
        documents["block_map"],
    )


def vector_close(left, right, *, sign_equivalent=False, tolerance=1e-8):
    direct = all(abs(a - b) <= tolerance for a, b in zip(left, right))
    if direct or not sign_equivalent:
        return direct
    return all(abs(a + b) <= tolerance for a, b in zip(left, right))


def cross(left, right):
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def test_coverage_joins_44_conditional_wood_frames_and_leaves_six_panels_open(
    source_documents,
):
    coverage = compile_sources(source_documents)

    entries = coverage["members"]
    assert len(entries) == 50
    assert len({row["member_id"] for row in entries}) == 50
    assert sum(row["coverage_class"] == "frame_timber" for row in entries) == 20
    assert sum(row["coverage_class"] == "candidate_block" for row in entries) == 24
    assert sum(row["coverage_class"] == "plywood_panel_unresolved" for row in entries) == 6
    assert coverage["source_scope"]["block_frame_method_counts"] == {
        "current geometry source builder's global-axis Solid.makeBox construction": 8,
        "pinned WJ04 trial frame and source-bound upper-G7 builder datum": 1,
        "source-axis frame plus saved exact-solid proper-rigid transform": 15,
    }
    assert coverage["readiness"] == {
        "candidate_accepted": False,
        "full_frame_material_mapping_ready": False,
        "inputs_ready": False,
        "launch_ready": False,
        "native_solve_ready": False,
    }
    assert coverage["native_execution"] == {"executed": False}
    assert all(value is False for value in coverage["acceptance"].values())
    assert all(value is False for value in coverage["release"].values())
    assert all(row["material_assignment"] == {
        "density": None,
        "elastic_properties": None,
        "grade": None,
        "material_id": None,
        "species_group": None,
    } for row in entries)
    assert all(row["solver_mapping"] == {
        "body_id": None,
        "dof_ids": None,
        "element_ids": None,
        "node_ids": None,
    } for row in entries)

    panels = [
        row for row in entries if row["coverage_class"] == "plywood_panel_unresolved"
    ]
    assert all(row["conditional_material_frame_scenarios"] is None for row in panels)
    assert all(row["orientation_status"] == "unresolved_product_and_sheet_axis" for row in panels)


def test_all_44_emitted_frames_are_right_handed_and_reconstruct_conditional_grain(
    source_documents,
):
    coverage = compile_sources(source_documents)
    wood = [
        row
        for row in coverage["members"]
        if row["coverage_class"] != "plywood_panel_unresolved"
    ]
    assert len(wood) == 44
    for row in wood:
        scenarios = row["conditional_material_frame_scenarios"]
        axes = scenarios["source_frame_axes_global_xyz"]
        assert vector_close(cross(axes["X"], axes["T"]), axes["N"])
        grain = scenarios["longitudinal_direction_global_xyz"]
        if row["coverage_class"] == "frame_timber":
            components = scenarios["longitudinal_components_in_source_frame_xyz"]
            reconstructed = tuple(
                sum(axes[axis][coordinate] * components[axis] for axis in ("X", "T", "N"))
                for coordinate in range(3)
            )
            assert vector_close(reconstructed, grain, sign_equivalent=True)
        else:
            assert scenarios["longitudinal_source_axis_name"] == "N"
            assert vector_close(axes["N"], grain, sign_equivalent=True)


def test_block_a_and_b_transverse_scenarios_are_retained_and_right_handed(source_documents):
    coverage = compile_sources(source_documents)
    blocks = [row for row in coverage["members"] if row["coverage_class"] == "candidate_block"]
    assert len(blocks) == 24
    for row in blocks:
        scenarios = row["conditional_material_frame_scenarios"]["transverse_assignments"]
        assert {scenario["scenario_id"] for scenario in scenarios} == {
            "ring_R_on_X",
            "ring_R_on_T",
        }
        grain = row["conditional_material_frame_scenarios"]["longitudinal_direction_global_xyz"]
        for scenario in scenarios:
            longitudinal = scenario["longitudinal_L_global_xyz"]
            radial = scenario["radial_R_global_xyz"]
            tangential = scenario["tangential_T_global_xyz"]
            assert vector_close(longitudinal, grain)
            assert vector_close(cross(longitudinal, radial), tangential)
            assert scenario["proposal_only"] is True


def test_changed_manifest_step_hash_fails_the_exact_export_join(source_documents):
    documents = copy.deepcopy(source_documents)
    documents["manifest"]["finished_member_step_bindings"][0]["file_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="STEP identity mismatch"):
        compile_sources(documents)


def test_missing_or_duplicate_orientation_identity_fails_closed(source_documents):
    documents = copy.deepcopy(source_documents)
    documents["timber_map"]["members"][0]["member_id"] = documents["timber_map"]["members"][1]["member_id"]

    with pytest.raises(ValueError, match="frame-timber identities"):
        compile_sources(documents)


def test_unsupported_block_frame_method_fails_closed(source_documents):
    documents = copy.deepcopy(source_documents)
    documents["block_map"]["members"][0]["frame_binding"]["method"] = "unreviewed basis"

    with pytest.raises(ValueError, match="block frame lineage is incomplete"):
        compile_sources(documents)


@pytest.mark.parametrize("map_key, member_key, axes_key", [
    ("timber_map", "member_id", "axes_global_xyz"),
    ("block_map", "part_id", "source_frame_axes_global_xyz"),
])
def test_non_orthonormal_source_frame_fails_closed(
    source_documents, map_key, member_key, axes_key
):
    documents = copy.deepcopy(source_documents)
    row = documents[map_key]["members"][0]
    axes = row["source_frame"][axes_key] if map_key == "timber_map" else row[axes_key]
    axes["N"] = [0.0, 0.0, 0.0]

    with pytest.raises(ValueError, match="orthonormal"):
        compile_sources(documents)


@pytest.mark.parametrize("map_key, axes_path", [
    ("timber_map", "axes_global_xyz"),
    ("block_map", "source_frame_axes_global_xyz"),
])
def test_left_handed_source_frame_fails_closed(source_documents, map_key, axes_path):
    documents = copy.deepcopy(source_documents)
    row = documents[map_key]["members"][0]
    axes = row["source_frame"][axes_path] if map_key == "timber_map" else row[axes_path]
    axes["N"] = [-component for component in axes["N"]]

    with pytest.raises(ValueError, match="right-handed"):
        compile_sources(documents)


def test_pinned_input_bytes_are_checked_before_parsing(tmp_path):
    manifest_path = (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    )
    target = tmp_path / manifest_path
    target.parent.mkdir(parents=True)
    target.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="pinned input hash mismatch"):
        load_pinned_sources(tmp_path)
