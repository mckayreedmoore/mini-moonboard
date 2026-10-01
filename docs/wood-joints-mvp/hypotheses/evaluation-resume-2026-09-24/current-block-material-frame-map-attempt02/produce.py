#!/usr/bin/env python3
"""Bind conditional material frames to the 24 current WJ24 connector blocks.

This reads frozen source geometry records and builder declarations only. It
does not import CAD, replay geometry, mesh, run a solver, or establish material
acceptance. The common-pattern orientations use the saved proper-rigid-
transform crosswalk; other orientations follow the exact box/frame builders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "material-frame-map.json"

MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json"
)
DESIGNS_PATH = (
    "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/"
    "block-designs.json"
)
REVISION_PATH = (
    "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/"
    "revision.json"
)
MATERIAL_DOC = "docs/wood-joints-mvp/current-material-scenarios.md"
FAMILY_DOC = "docs/wood-joints-mvp/current-joint-family-reuse.md"
MATERIAL_HELPER = "fea/wood_joint_patch_materials.py"
GEOMETRY_ENTRY = "scripts/wood_joint_current_geometry.py"
SOURCE_INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
SELECTED_AUTHORITY = "current-candidate.json"
DEVELOPMENT_AUTHORITY = "wood-joints-candidate.json"
WJ04_CONFIG = "mini_moonboard/wood_joint_wj04_config.py"
COMMON_FRAME_SOURCE = "scripts/wood_joint_wj04_full_stock_mechanics_contract.py"
G7_GEOMETRY_SOURCE = "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"
CENTER_POST_GEOMETRY_SOURCE = "scripts/wood_joint_wj05_center_node_probe.py"
CENTER_PRINCIPAL_GEOMETRY_SOURCE = "scripts/wood_joint_wj24_center_header_blocks.py"
INNER_FRAME_GEOMETRY_SOURCE = "scripts/wood_joint_wj24_inner_frame_blocks.py"
SPINE_GEOMETRY_SOURCE = "scripts/wood_joint_wj24_2x6_outer_blocks.py"
BLOCK_DESIGN_SOURCE = "scripts/wood_joint_block_design_count.py"

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_SELECTED_CANDIDATE = "compact-floor-flush-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_MANIFEST_ID = "current-full-frame-input-manifest-attempt02"
EXPECTED_MANIFEST_DIGEST = "1ad6b404c8658147e9d10f54daf4ebd393116c1934654f5521421dc96667e0a0"
EXPECTED_REVIEW_COMMIT = "b1e8707d"

# Pins are copied from the reviewed input set at creation time. A changed input
# requires a new attempt instead of an implicit refresh of this record.
EXPECTED_SHA256 = {
    MANIFEST_PATH: "21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3",
    DESIGNS_PATH: "f3c7d76ecdd2d3a82d2d96ef8868bc11ddb789ecdaa6b6ff2fdeadeec45d097b",
    REVISION_PATH: "148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695",
    MATERIAL_DOC: "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4",
    FAMILY_DOC: "961f2365efc3d7d5b81a09a5ac2b7eae015f969b82189ed01276bdba20ddff58",
    MATERIAL_HELPER: "ecbbd11a8a0e99ece69aeb5cb4159e7cf17e0aa18c509c78b5c8f5a2e573ae78",
    GEOMETRY_ENTRY: "b4ba3fdc917536d016932c356431e34ed63b9f174927d88d40e4ab6faa1686f8",
    SOURCE_INVENTORY: "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    WJ04_CONFIG: "4f94f49ebc0c5f92e6dce339794983607614299f53150fc7264ca54b29e987be",
    COMMON_FRAME_SOURCE: "fd8bc1c92efa43f57cb51eff07ece9aa044ca3593892f812706a5e01adff020c",
    G7_GEOMETRY_SOURCE: "94d2b301450c942f1c7a95f89e3e7ee1ed643ce4db43576c78c1bce04f9302b9",
    CENTER_POST_GEOMETRY_SOURCE: "eafffbc95d5989bcc21a7cfed90ff25e917c778bf9758154b915cbba0ec3d173",
    CENTER_PRINCIPAL_GEOMETRY_SOURCE: "3571224219b4e5f819920bf3e4bcff307c11b4743023d656a70b3b1e954e101a",
    INNER_FRAME_GEOMETRY_SOURCE: "07c5f982e21f7a184264e414c463281f5c2925feb2add80f58e79343fa54205a",
    SPINE_GEOMETRY_SOURCE: "fb7e49e354f1ffe718c86caeeb588c129088a604498ef465028320defd13540e",
    BLOCK_DESIGN_SOURCE: "3592e70ec989c35ecab366b95b72c6909e7c21cda894946ddca0b559ce144cf7",
    SELECTED_AUTHORITY: "f4505746a0a33eac1771708fbc376686b801e2c2af3053d9447fbbc6e22491a4",
    DEVELOPMENT_AUTHORITY: "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
}

COMMON_REPRESENTATIVE = "bottom_center_left_cleat"
COMMON_MEMBERS = {
    "bottom_center_left_cleat",
    "bottom_center_right_cleat",
    "bottom_outer_left_cleat",
    "bottom_outer_right_cleat",
    "left_service_inner_lower_cleat",
    "left_service_inner_upper_cleat",
    "left_service_outer_lower_cleat",
    "left_service_outer_upper_cleat",
    "top_center_left_cleat",
    "top_center_right_cleat",
    "top_outer_left_cleat",
    "top_outer_right_cleat",
    "wj04_lower_full_stock_cleat",
    "wj06_outer_lower_right_cleat",
    "wj06_outer_upper_right_cleat",
}
AXIS_ALIGNED_GROUPS = {
    "center-post-cleat": {
        "members": {"center_post_cleat_left", "center_post_cleat_right"},
        "builder": CENTER_POST_GEOMETRY_SOURCE,
        "basis": "axis-aligned makeBox X/Y/Z in the WJ05 candidate-part builder; Y is T and Z is N",
        "grain_basis": "conditional +Z stock-length proposal in current material scenarios",
    },
    "center-principal-header-cleat": {
        "members": {
            "center_principal_cleat_left",
            "center_principal_cleat_right",
        },
        "builder": CENTER_PRINCIPAL_GEOMETRY_SOURCE,
        "basis": "current revision _block() creates global-axis makeBox solids; Y is T and Z is N",
        "grain_basis": "conditional +Z plumb-stock proposal in current material scenarios",
    },
    "outer-rim-inner-frame-block": {
        "members": {
            "knee_outer_left_inner_frame_block",
            "knee_outer_right_inner_frame_block",
        },
        "builder": INNER_FRAME_GEOMETRY_SOURCE,
        "basis": "current revision creates each blank with global-axis Solid.makeBox; Y is T and Z is N",
        "grain_basis": "conditional +Z layout proposal; current material scenarios identify this as less directly documented",
    },
    "exterior-runner-seated-spine": {
        "members": {"knee_outer_left_spine", "knee_outer_right_spine"},
        "builder": SPINE_GEOMETRY_SOURCE,
        "basis": "current revision creates each 2x6 blank with global-axis Solid.makeBox; Y is T and Z is N",
        "grain_basis": "conditional +Z stock-length/layout proposal in current material scenarios",
    },
}
G7_MEMBER = "wj04_upper_g7_crosscut_full_stock_cleat"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"pinned input is missing: {relative_path}")
    return sha256_bytes(path.read_bytes())


def read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path}: expected JSON object")
    return value


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def unit(v: list[float], context: str) -> list[float]:
    if len(v) != 3 or not all(math.isfinite(x) for x in v):
        raise ValueError(f"{context}: expected finite three-vector")
    norm = math.sqrt(dot(v, v))
    if norm <= 0:
        raise ValueError(f"{context}: zero direction")
    return [x / norm for x in v]


def determinant(matrix: list[list[float]]) -> float:
    return (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )


def apply_rotation(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [math.fsum(matrix[i][j] * vector[j] for j in range(3)) for i in range(3)]


def canonical_frame(
    axes: dict[str, list[float]], *, context: str, max_correction: float = 1e-5
) -> tuple[dict[str, list[float]], float]:
    """Remove small saved-transform roundoff while preserving the proper frame."""
    x_raw = axes["X"]
    t_raw = axes["T"]
    n_raw = axes["N"]
    x_axis = unit(x_raw, f"{context} X")
    t_residual = [t_raw[i] - dot(t_raw, x_axis) * x_axis[i] for i in range(3)]
    t_axis = unit(t_residual, f"{context} T")
    n_axis = unit(cross(x_axis, t_axis), f"{context} N")
    if dot(n_axis, n_raw) < 1.0 - 1e-5:
        raise ValueError(f"{context}: axes do not retain the recorded right-handed N direction")
    result = {"X": x_axis, "T": t_axis, "N": n_axis}
    correction = max(
        math.sqrt(math.fsum((result[name][i] - axes[name][i]) ** 2 for i in range(3)))
        for name in ("X", "T", "N")
    )
    if correction > max_correction:
        raise ValueError(f"{context}: saved frame correction {correction:.3g} is too large")
    if (
        abs(dot(x_axis, t_axis)) > 1e-8
        or abs(dot(x_axis, n_axis)) > 1e-8
        or abs(dot(t_axis, n_axis)) > 1e-8
        or dot(cross(x_axis, t_axis), n_axis) < 1.0 - 1e-8
    ):
        raise ValueError(f"{context}: frame is not orthonormal and right-handed")
    return result, correction


def matrix_for_member(group: dict[str, Any], member_id: str) -> list[list[float]]:
    if member_id == group.get("representative"):
        return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    checks = group.get("equivalence_checks")
    record = checks.get(member_id) if isinstance(checks, dict) else None
    transform = record.get("rigid_transform") if isinstance(record, dict) else None
    if not isinstance(transform, list) or len(transform) != 4:
        raise ValueError(f"{member_id}: missing source-bound proper rigid transform")
    if any(not isinstance(row, list) or len(row) != 4 for row in transform):
        raise ValueError(f"{member_id}: malformed 4x4 rigid transform")
    rotation = [[float(transform[i][j]) for j in range(3)] for i in range(3)]
    bottom = [float(x) for x in transform[3]]
    if any(not math.isfinite(value) for row in transform for value in row):
        raise ValueError(f"{member_id}: non-finite saved rigid transform")
    if max(abs(bottom[i] - [0.0, 0.0, 0.0, 1.0][i]) for i in range(4)) > 1e-10:
        raise ValueError(f"{member_id}: transform is not affine homogeneous form")
    det = determinant(rotation)
    if abs(det - 1.0) > 1e-5:
        raise ValueError(f"{member_id}: transform is not a proper rotation (det={det})")
    for i in range(3):
        for j in range(3):
            expected = 1.0 if i == j else 0.0
            if abs(math.fsum(rotation[k][i] * rotation[k][j] for k in range(3)) - expected) > 1e-5:
                raise ValueError(f"{member_id}: saved rotation is not orthogonal")
    return rotation


def build_map() -> dict[str, Any]:
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"source hash changed for {path}: expected {expected}, got {actual}")

    manifest = read_json(MANIFEST_PATH)
    designs = read_json(DESIGNS_PATH)
    revision = read_json(REVISION_PATH)
    inventory = read_json(SOURCE_INVENTORY)
    selected_authority = read_json(SELECTED_AUTHORITY)
    development_authority = read_json(DEVELOPMENT_AUTHORITY)
    if (
        manifest.get("candidate") != EXPECTED_CANDIDATE
        or manifest.get("geometry_revision_id") != EXPECTED_REVISION
        or manifest.get("manifest_id") != EXPECTED_MANIFEST_ID
        or manifest.get("manifest_sha256") != EXPECTED_MANIFEST_DIGEST
        or manifest.get("reviewed_repository_commit") != EXPECTED_REVIEW_COMMIT
    ):
        raise ValueError("attempt02 full-frame manifest identity changed")
    if revision.get("revision_id") != EXPECTED_REVISION or revision.get("joint_evaluations_run") is not False:
        raise ValueError("current revision report identity or no-evaluation claim changed")
    if selected_authority.get("candidate") != EXPECTED_SELECTED_CANDIDATE:
        raise ValueError("selected-candidate authority changed")
    if development_authority.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("development-candidate authority changed")
    authority = manifest.get("authority_and_provenance", {})
    if (
        authority.get("selected_candidate") != EXPECTED_SELECTED_CANDIDATE
        or authority.get("development_candidate") != EXPECTED_CANDIDATE
    ):
        raise ValueError("attempt02 manifest no longer preserves both candidate authorities")
    if designs.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("block design report names a different revision")
    if designs.get("method") != (
        "Finished CAD solids including holes, cuts and reliefs; translation and proper rotation allowed, reflection not allowed. Inertia candidates checked by exact solid intersection."
    ):
        raise ValueError("common-block transform method changed")

    # Load the pinned, CAD-free transformation helper only after its exact
    # implementation hash was checked above.
    sys.path.insert(0, str(ROOT))
    from fea.wood_joint_patch_materials import material_orientation_cases

    candidate_rows = manifest.get("candidate_blocks")
    if not isinstance(candidate_rows, list) or len(candidate_rows) != 24:
        raise ValueError("attempt02 manifest must name exactly 24 connector blocks")
    block_by_id = {row.get("part_id"): row for row in candidate_rows if isinstance(row, dict)}
    if len(block_by_id) != 24 or any(not isinstance(key, str) for key in block_by_id):
        raise ValueError("attempt02 candidate block IDs are malformed or duplicated")
    expected_ids = set(block_by_id)

    groups = designs.get("groups")
    if not isinstance(groups, list):
        raise ValueError("block design report has no groups")
    common_group = next(
        (row for row in groups if isinstance(row, dict) and row.get("representative") == COMMON_REPRESENTATIVE),
        None,
    )
    if not isinstance(common_group, dict) or set(common_group.get("members", ())) != COMMON_MEMBERS:
        raise ValueError("the 15-member common block group changed")
    if common_group.get("equivalence_checks", {}).get(COMMON_REPRESENTATIVE) is not None:
        raise ValueError("common representative unexpectedly has a non-identity transform")

    source_parts = inventory.get("parts")
    if not isinstance(source_parts, list):
        raise ValueError("canonical source inventory has no parts")
    source_rows = {row.get("part_id"): row for row in source_parts if isinstance(row, dict)}
    if len(source_rows) != len(source_parts):
        raise ValueError("canonical source inventory part IDs are duplicated")
    rail_frame = source_rows.get("base_rail_bottom_right", {}).get("local_axes")
    if not isinstance(rail_frame, dict) or set(rail_frame) != {"X", "T", "N"}:
        raise ValueError("source inventory lacks the common pattern's X/T/N frame")
    base_axes = {
        name: [float(value) for value in rail_frame[name]] for name in ("X", "T", "N")
    }
    base_axes, _ = canonical_frame(base_axes, context="base_rail_bottom_right source frame")
    angle = math.radians(50.0)
    expected_source_frame = {
        "X": [1.0, 0.0, 0.0],
        "T": [0.0, math.cos(angle), math.sin(angle)],
        "N": [0.0, -math.sin(angle), math.cos(angle)],
    }
    if any(
        math.sqrt(math.fsum((base_axes[name][i] - expected_source_frame[name][i]) ** 2 for i in range(3)))
        > 1e-8
        for name in ("X", "T", "N")
    ):
        raise ValueError("source-inventory frame no longer matches the pinned WJ04/material scenario basis")

    frames: dict[str, dict[str, Any]] = {}
    for member_id in sorted(COMMON_MEMBERS):
        if member_id not in expected_ids:
            raise ValueError(f"common source group member is absent from manifest: {member_id}")
        rotation = matrix_for_member(common_group, member_id)
        transformed = {name: apply_rotation(rotation, base_axes[name]) for name in ("X", "T", "N")}
        axes, correction = canonical_frame(transformed, context=f"{member_id} transformed frame")
        if abs(dot(axes["N"], base_axes["N"])) < 1.0 - 1e-7:
            raise ValueError(f"{member_id}: common source N does not retain the current pattern axis")
        frames[member_id] = {
            "pattern_id": "common-main-member",
            "axes": axes,
            "grain_axis_local_name": "N",
            "grain_basis": (
                "conditional +N_source pattern assignment; source frame starts from "
                "source-inventory base_rail_bottom_right.local_axes and is transformed "
                "by the block-design report's exact-solid proper rigid transform"
            ),
            "frame_binding": {
                "method": "source-axis frame plus saved exact-solid proper-rigid transform",
                "representative_part_id": COMMON_REPRESENTATIVE,
                "transform_matrix_4x4": (
                    [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
                    if member_id == COMMON_REPRESENTATIVE
                    else common_group["equivalence_checks"][member_id]["rigid_transform"]
                ),
                "orthonormalization_max_axis_correction": correction,
                "basis_sources": [SOURCE_INVENTORY, COMMON_FRAME_SOURCE, DESIGNS_PATH],
            },
            "grain_assignment_status": "conditional_pattern_scenario_not_observed_stock",
        }

    xyz_axes = {"X": [1.0, 0.0, 0.0], "T": [0.0, 1.0, 0.0], "N": [0.0, 0.0, 1.0]}
    for pattern_id, group in AXIS_ALIGNED_GROUPS.items():
        for member_id in group["members"]:
            if member_id not in expected_ids:
                raise ValueError(f"{pattern_id} member is absent from manifest: {member_id}")
            frames[member_id] = {
                "pattern_id": pattern_id,
                "axes": xyz_axes,
                "grain_axis_local_name": "N",
                "grain_basis": group["grain_basis"],
                "frame_binding": {
                    "method": "current geometry source builder's global-axis Solid.makeBox construction",
                    "builder_source": group["builder"],
                    "builder_basis": group["basis"],
                    "basis_sources": [group["builder"], GEOMETRY_ENTRY],
                },
                "grain_assignment_status": (
                    "conditional_analysis_choice_less_directly_documented"
                    if pattern_id == "outer-rim-inner-frame-block"
                    else "conditional_pattern_scenario_not_observed_stock"
                ),
            }

    if G7_MEMBER not in expected_ids:
        raise ValueError(f"unique G7 block is absent from manifest: {G7_MEMBER}")
    g7_frame = {name: base_axes[name] for name in ("X", "T", "N")}
    frames[G7_MEMBER] = {
        "pattern_id": "shortened-upper-G7",
        "axes": g7_frame,
        "grain_axis_local_name": "N",
        "grain_basis": (
            "conditional shortened crosscut assignment inherited from the pinned WJ04 "
            "upper-G7 source frame; not an observed board"
        ),
        "frame_binding": {
            "method": "pinned WJ04 trial frame and source-bound upper-G7 builder datum",
            "builder_source": G7_GEOMETRY_SOURCE,
            "basis_sources": [
                SOURCE_INVENTORY,
                WJ04_CONFIG,
                G7_GEOMETRY_SOURCE,
                GEOMETRY_ENTRY,
            ],
        },
        "grain_assignment_status": "conditional_pattern_scenario_not_observed_stock",
    }

    if set(frames) != expected_ids:
        missing = sorted(expected_ids - set(frames))
        extra = sorted(set(frames) - expected_ids)
        raise ValueError(f"frame coverage mismatch: missing={missing}, extra={extra}")

    material_map_members = []
    for member_id in sorted(expected_ids):
        source = frames[member_id]
        axes = source["axes"]
        grain_name = source["grain_axis_local_name"]
        grain = axes[grain_name]
        frame_input = {
            "grain_axis_local_name": grain_name,
            "grain_axis_global_xyz": grain,
            "local_axes_global_xyz": axes,
        }
        cases = material_orientation_cases(frame_input)
        if len(cases) != 2:
            raise ValueError(f"{member_id}: material helper did not produce both R/T cases")
        case_rows = []
        for case in cases:
            if not case.get("right_handed") or case.get("proposal_only") is not True:
                raise ValueError(f"{member_id}: invalid conditional material-orientation case")
            case_rows.append(case)
        manifest_row = block_by_id[member_id]
        material_map_members.append(
            {
                "part_id": member_id,
                "manifest_material_frame_status_before_map": manifest_row.get("material_frame_status"),
                "owner_report_finished_shape_sha256": manifest_row.get("owner_report_finished_shape_sha256"),
                "pattern_id": source["pattern_id"],
                "source_frame_axes_global_xyz": axes,
                "conditional_grain_assignment": {
                    "longitudinal_material_axis": "L",
                    "source_axis_name": grain_name,
                    "grain_direction_global_xyz": grain,
                    "grain_basis": source["grain_basis"],
                    "sign_equivalent": True,
                    "delivered_stock_observed": False,
                },
                "frame_binding": source["frame_binding"],
                "transverse_assignment_cases": case_rows,
                "limits": [
                    "Frame and grain assignments are proposal-only geometry/material scenarios, not measurements of this physical stock piece.",
                    "Case A/B retain unknown R/T ring orientation; actual boards may differ between blocks and within one pattern.",
                    "No elastic values, connection resistance, joint capacity, demand, or acceptance is established by this orientation map.",
                ],
            }
        )

    source_pins = {
        path: {"sha256": EXPECTED_SHA256[path]} for path in EXPECTED_SHA256
    }
    source_pins[MANIFEST_PATH]["manifest_sha256_field"] = manifest["manifest_sha256"]
    source_pins[SELECTED_AUTHORITY]["candidate"] = selected_authority["candidate"]
    source_pins[DEVELOPMENT_AUTHORITY]["candidate"] = development_authority["candidate"]
    source_pins[DESIGNS_PATH]["revision_id"] = designs["revision_id"]
    source_pins[REVISION_PATH]["revision_id"] = revision["revision_id"]
    producer_relative = Path(__file__).resolve().relative_to(ROOT).as_posix()
    source_pins[producer_relative] = {"sha256": sha256_file(producer_relative)}

    record: dict[str, Any] = {
        "schema": "wood_joint_current_connector_block_material_frame_map/v1",
        "attempt_id": "current-block-material-frame-map-attempt02",
        "status": "conditional_source_bound_candidate_block_frames_geometry_only",
        "candidate": manifest["candidate"],
        "selected_candidate_preserved": EXPECTED_SELECTED_CANDIDATE,
        "geometry_revision_id": manifest["geometry_revision_id"],
        "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "input_manifest_id": manifest["manifest_id"],
        "input_manifest_sha256": manifest["manifest_sha256"],
        "scope": {
            "mapped_connector_block_count": len(material_map_members),
            "mapped_part_ids": sorted(expected_ids),
            "pattern_counts": {
                "common-main-member": 15,
                "center-post-cleat": 2,
                "center-principal-header-cleat": 2,
                "outer-rim-inner-frame-block": 2,
                "exterior-runner-seated-spine": 2,
                "shortened-upper-G7": 1,
            },
            "transverse_assignments_per_block": 2,
            "explicitly_not_mapped": [
                "20 current source timber members",
                "six current plywood panels",
                "92 candidate bolts and their modeled hardware bodies",
                "12 retained starting frame-bolt stacks and their modeled hardware bodies",
            ],
            "complete_full_frame_material_mapping": False,
        },
        "source_pins": source_pins,
        "source_binding_method": {
            "common_pattern": "source-inventory axes plus the exact-solid proper-rotation crosswalk in block-designs.json",
            "axis_aligned_patterns": "global axes directly from the current solid-box construction calls",
            "shortened_upper_g7": "pinned WJ04 frame and upper-G7 source builder",
            "viewer_meshes_used": False,
            "cad_replayed": False,
        },
        "material_helper": {
            "path": MATERIAL_HELPER,
            "sha256": EXPECTED_SHA256[MATERIAL_HELPER],
            "function": "material_orientation_cases",
            "uses_both_transverse_assignments": True,
            "material_values_or_solver_cards_emitted": False,
        },
        "members": material_map_members,
        "readiness_effect": {
            "candidate_block_source_frames_bound_for_conditional_scenarios": True,
            "manifest_full_frame_per_member_material_mapping_ready": False,
            "full_frame_inputs_ready": False,
            "native_solve_executed": False,
        },
        "release": {
            "candidate_accepted": False,
            "engineering_mvp_complete": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "climbing_released": False,
        },
        "claim_limits": [
            "All 24 exact block IDs are sourced from full-frame input manifest attempt02; this is a block-only partial input map.",
            "The conditional timber elastic scenario combines DF-L No. 2 modulus with Douglas-fir clear-wood ratios; it is not measured or grade-specific accepted material data.",
            "The grain and transverse ring axes describe proposed analytical assignments, not the delivered grain or growth-ring orientation of any board.",
            "The inner-frame +Z grain assignment remains an explicit, less directly documented scenario choice.",
            "Common-block transforms are the saved proper rigid transforms validated by exact solid intersection in the block-design report; this attempt does not regenerate CAD or rely on viewer meshes.",
            "This record does not map source-frame member timber, plywood, steel hardware, bolt material, contact, attachments, loads, demands, resistance, or acceptance.",
        ],
    }
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
    record["record_sha256"] = sha256_bytes(payload.encode("utf-8"))
    return record


def verify() -> dict[str, Any]:
    expected = build_map()
    actual = read_json(OUTPUT.relative_to(ROOT).as_posix())
    digest = actual.pop("record_sha256", None)
    actual_payload = json.dumps(actual, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if digest != sha256_bytes(actual_payload.encode("utf-8")):
        raise ValueError("material frame map canonical digest mismatch")
    expected_digest = expected["record_sha256"]
    if digest != expected_digest:
        raise ValueError("material frame map differs from its current source-bound reconstruction")
    expected_payload = json.dumps(
        {key: value for key, value in expected.items() if key != "record_sha256"},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if actual_payload != expected_payload:
        raise ValueError("material frame map payload differs from current source reconstruction")
    # Restore for a compact verification summary.
    actual["record_sha256"] = digest
    return {
        "status": "verified",
        "candidate": actual["candidate"],
        "geometry_revision_id": actual["geometry_revision_id"],
        "mapped_block_count": actual["scope"]["mapped_connector_block_count"],
        "transverse_assignments": sum(len(row["transverse_assignment_cases"]) for row in actual["members"]),
        "full_frame_inputs_ready": actual["readiness_effect"]["full_frame_inputs_ready"],
        "record_sha256": digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.write:
        if OUTPUT.exists():
            raise FileExistsError(f"refusing to overwrite existing attempt output: {OUTPUT}")
        record = build_map()
        OUTPUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "written", "path": str(OUTPUT.relative_to(ROOT)), "record_sha256": record["record_sha256"]}, sort_keys=True))
    else:
        print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
