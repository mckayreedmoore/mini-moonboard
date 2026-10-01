"""Build a source-bound cut/section inventory from frozen current records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "inventory.json"
BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
INPUTS = {
    "source_inventory": "docs/wood-joints-mvp/source-inventory.json",
    "current_manifest": BASE + "current-full-frame-input-manifest-attempt03/"
    + "current-full-frame-input-manifest.json",
    "member_solids": BASE + "current-full-frame-member-solids-attempt01/"
    + "bundle/current-full-frame-member-solids.json",
    "review_report": "site/owner-wood-joints-review-report.json",
    "block_designs": "docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-"
    + "blocks-2026-09-24/block-designs.json",
    "common_block_pattern": "docs/wood-joints-mvp/hypotheses/common-corner-block-"
    + "study-2026-09-24/pattern-comparison.json",
    "frame_material_map": BASE + "current-frame-timber-material-frame-map-"
    + "attempt01/current-frame-timber-material-frame-map.json",
    "block_material_map": BASE + "current-block-material-frame-map-attempt02/"
    + "material-frame-map.json",
    "attachment_topology": BASE + "current-attachment-topology-attempt01/"
    + "attachment-topology.json",
    "flush_frame_source": "mini_moonboard/compact_floor_flush_frame.py",
    "taper_frame_source": "mini_moonboard/compact_floor_taper_frame.py",
    "recess_frame_source": "mini_moonboard/compact_floor_recess_frame.py",
    "center_block_source": "scripts/wood_joint_wj05_center_node_probe.py",
    "inner_frame_block_source": "scripts/wood_joint_wj24_inner_frame_blocks.py",
    "outer_block_source": "scripts/wood_joint_wj24_2x6_outer_blocks.py",
    "g7_block_source": "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py",
}

FRAME_FEATURES: dict[str, list[dict[str, Any]]] = {
    "base_floor_left": [
        {
            "feature": "flush end profiles",
            "detail": (
                "Front end is set to the outer-post plane; rear end follows the "
                "inclined rear-leg plane. The per-member cut profile is not emitted "
                "by this inventory."
            ),
            "source_ids": ["flush_frame_source"],
        }
    ],
    "base_floor_right": [
        {
            "feature": "flush end profiles",
            "detail": (
                "Front end is set to the outer-post plane; rear end follows the "
                "inclined rear-leg plane. The per-member cut profile is not emitted "
                "by this inventory."
            ),
            "source_ids": ["flush_frame_source"],
        }
    ],
    "base_side_left": [
        {
            "feature": "flush profile trim",
            "detail": (
                "The selected flush-frame source trims this changed member at its "
                "header-back datum. Exact local section changes are not calculated."
            ),
            "source_ids": ["flush_frame_source"],
        }
    ],
    "base_side_right": [
        {
            "feature": "flush profile trim",
            "detail": (
                "The selected flush-frame source trims this changed member at its "
                "header-back datum. Exact local section changes are not calculated."
            ),
            "source_ids": ["flush_frame_source"],
        }
    ],
    "lumber_leg_left": [
        {
            "feature": "open inner-face runner recess with grain-aligned taper",
            "detail": (
                "Source geometry defines a 38.1 mm maximum-depth recess and a "
                "457.2 mm, 1:12 taper runout. The shoulder is not assigned bearing."
            ),
            "source_ids": ["recess_frame_source", "taper_frame_source"],
        }
    ],
    "lumber_leg_right": [
        {
            "feature": "open inner-face runner recess with grain-aligned taper",
            "detail": (
                "Source geometry defines a 38.1 mm maximum-depth recess and a "
                "457.2 mm, 1:12 taper runout. The shoulder is not assigned bearing."
            ),
            "source_ids": ["recess_frame_source", "taper_frame_source"],
        }
    ],
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    )


def read_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object: {relative}")
    return value


def bounds_record(bounds: list[float]) -> dict[str, Any]:
    if len(bounds) != 6:
        raise ValueError("Expected [xmin,xmax,ymin,ymax,zmin,zmax] bounds")
    pairs = {
        axis: [bounds[offset], bounds[offset + 1]]
        for axis, offset in (("X", 0), ("Y", 2), ("Z", 4))
    }
    return {
        "min_max_by_global_axis_mm": pairs,
        "axis_aligned_envelope_extents_xyz_mm": [
            pair[1] - pair[0] for pair in pairs.values()
        ],
    }


def source_records() -> dict[str, dict[str, Any]]:
    rows = {}
    for key, relative in INPUTS.items():
        raw = (ROOT / relative).read_bytes()
        rows[key] = {
            "path": relative,
            "sha256": sha256(raw),
            "size_bytes": len(raw),
        }
    producer_path = Path(__file__).resolve().relative_to(ROOT).as_posix()
    producer_raw = Path(__file__).read_bytes()
    rows["inventory_producer"] = {
        "path": producer_path,
        "sha256": sha256(producer_raw),
        "size_bytes": len(producer_raw),
    }
    return rows


def build() -> dict[str, Any]:
    source = read_json(INPUTS["source_inventory"])
    manifest = read_json(INPUTS["current_manifest"])
    solids = read_json(INPUTS["member_solids"])
    report = read_json(INPUTS["review_report"])
    block_designs = read_json(INPUTS["block_designs"])
    common_pattern = read_json(INPUTS["common_block_pattern"])
    frame_map = read_json(INPUTS["frame_material_map"])
    block_map = read_json(INPUTS["block_material_map"])
    topology = read_json(INPUTS["attachment_topology"])

    if manifest.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("Current manifest is for a different geometry revision")
    if manifest.get("schema") != "wood_joint_current_full_frame_input_manifest/v2":
        raise ValueError("Expected current full-frame manifest attempt03")
    if solids.get("geometry_revision_id") != manifest["geometry_revision_id"]:
        raise ValueError("STEP bundle revision differs from the current manifest")
    if report.get("revision_id") != manifest["geometry_revision_id"]:
        raise ValueError("Review report revision differs from the current manifest")

    inventory_parts = {
        row["part_id"]: row
        for row in source["parts"]
        if row.get("kind") == "timber"
    }
    current_members = {
        row["member_id"]: row for row in manifest["physical_members"]
    }
    solid_members = {
        row["member_id"]: row for row in solids["members"]
    }
    frame_grain = {row["member_id"]: row for row in frame_map["members"]}
    block_grain = {row["part_id"]: row for row in block_map["members"]}
    step_bindings = {
        row["member_id"]: row for row in manifest["finished_member_step_bindings"]
    }

    blocks = {row["part_id"]: row for row in manifest["candidate_blocks"]}
    design_group = {
        member_id: group
        for group in block_designs["groups"]
        for member_id in group["members"]
    }
    for check, actual, expected in (
        ("source frame members", set(inventory_parts), 20),
        ("candidate blocks", set(blocks), 24),
        ("material map frame members", set(frame_grain), 20),
        ("material map candidate blocks", set(block_grain), 24),
    ):
        if len(actual) != expected:
            raise ValueError(f"{check}: expected {expected}, got {len(actual)}")
    expected_wood = set(inventory_parts) | set(blocks)
    if {
        name
        for name, row in current_members.items()
        if row["member_kind"] in ("timber", "candidate_block")
    } != expected_wood:
        raise ValueError("20 frame timbers + 24 blocks differ from the manifest")
    if len(topology.get("candidate_bolt_axes", [])) != 92:
        raise ValueError("Attachment topology does not contain 92 candidate axes")
    if len(manifest.get("retained_frame_bolt_axes", [])) != 12:
        raise ValueError("Current manifest does not contain 12 retained frame bolts")
    if len(manifest.get("panel_kicker_screw_axes", [])) != 66:
        raise ValueError("Current manifest does not contain 66 panel screw axes")

    candidate_axis_map: dict[str, dict[str, Any]] = {}
    for row in manifest["candidate_bolt_axes"]:
        geometry = row["geometry"]
        candidate_axis_map[row["axis_id"]] = {
            "axis_id": row["axis_id"],
            "receiver_member_ids": row["receiver_member_ids"],
            "shaft_center_global_xyz_mm": geometry["shaft_center_global_xyz_mm"],
            "axis_head_to_nut_global": geometry["axis_head_to_nut_global"],
            "modeled_shaft_diameter_mm": geometry["modeled_shaft_diameter_mm"],
            "modeled_shaft_occupied_length_mm": geometry[
                "modeled_shaft_occupied_length_mm"
            ],
            "wood_receiver_intervals": geometry["wood_receiver_intervals"],
            "timber_bore_diameter_mm": None,
            "diameter_limit": (
                "Manifest records modeled bolt-shaft diameter, not the timber "
                "clearance-bore diameter."
            ),
        }

    retained_axis_map: dict[str, dict[str, Any]] = {}
    for row in manifest["retained_frame_bolt_axes"]:
        retained_axis_map[row["axis_id"]] = {
            "axis_id": row["axis_id"],
            "receiver_member_ids": row["members_as_recorded"],
            "origin_global_xyz_mm": row["origin_global_xyz_mm"],
            "axis_global_xyz": row["axis_global_xyz"],
            "source_occupied_diameter_mm": row["source_occupied_diameter_mm"],
            "source_grip_mm": row["source_grip_mm"],
            "timber_bore_diameter_mm": None,
        }

    source_screws = {row["axis_id"]: row for row in source["fixed_panel_kicker_screws"]}
    screw_axis_map: dict[str, dict[str, Any]] = {}
    for row in manifest["panel_kicker_screw_axes"]:
        historical = source_screws[row["axis_id"]]
        screw_axis_map[row["axis_id"]] = {
            "axis_id": row["axis_id"],
            "panel_member": row["panel_member"],
            "receiver_member": row["receiver_member"],
            "origin_global_xyz_mm": row["origin_global_xyz_mm"],
            "axis_global_xyz": row["axis_global_xyz"],
            "source_occupied_diameter_mm": historical[
                "source_occupied_diameter_mm"
            ],
            "source_occupied_length_mm": historical[
                "source_occupied_length_mm"
            ],
            "timber_bore_diameter_mm": None,
        }

    axis_ids_by_member: dict[str, dict[str, list[str]]] = {
        member_id: {
            "candidate_bolt_bore_axis_ids": [],
            "retained_frame_bolt_axis_ids": [],
            "panel_kicker_screw_axis_ids": [],
        }
        for member_id in expected_wood
    }
    for axis_id, row in candidate_axis_map.items():
        for member_id in row["receiver_member_ids"]:
            if member_id in axis_ids_by_member:
                axis_ids_by_member[member_id]["candidate_bolt_bore_axis_ids"].append(
                    axis_id
                )
    for axis_id, row in retained_axis_map.items():
        for member_id in row["receiver_member_ids"]:
            if member_id in axis_ids_by_member:
                axis_ids_by_member[member_id]["retained_frame_bolt_axis_ids"].append(
                    axis_id
                )
    for axis_id, row in screw_axis_map.items():
        member_id = row["receiver_member"]
        if member_id in axis_ids_by_member:
            axis_ids_by_member[member_id]["panel_kicker_screw_axis_ids"].append(axis_id)

    frame_features = FRAME_FEATURES
    block_specs: dict[str, dict[str, Any]] = {}
    common_ids = set(next(
        group["members"]
        for group in block_designs["groups"]
        if len(group["members"]) == 15
    ))
    if common_pattern.get("same_blank_count") != 15:
        raise ValueError("Common block pattern no longer covers 15 blanks")
    common_dims = common_pattern["blank_dimensions_X_T_N_mm"]
    for member_id in common_ids:
        block_specs[member_id] = {
            "constructed_blank_dimensions_mm": common_dims,
            "dimension_axes": ["X", "T", "N"],
            "basis_source_ids": ["common_block_pattern", "block_designs"],
            "known_profile_features": [],
        }
    for member_id in ("center_post_cleat_left", "center_post_cleat_right"):
        block_specs[member_id] = {
            "constructed_blank_dimensions_mm": [88.9, 88.9, 128.9],
            "dimension_axes": ["global_X", "global_Y", "global_Z"],
            "basis_source_ids": ["center_block_source"],
            "known_profile_features": [],
        }
    for member_id in ("center_principal_cleat_left", "center_principal_cleat_right"):
        change = report["block_trims"][member_id]
        block_specs[member_id] = {
            "prior_blank_dimensions_mm": change["before_dimensions_xyz_mm"],
            "constructed_blank_dimensions_mm": change["after_dimensions_xyz_mm"],
            "dimension_axes": ["global_X", "global_Y", "global_Z"],
            "basis_source_ids": ["center_block_source", "review_report"],
            "known_profile_features": [
                {
                    "feature": "5 mm outer-face and top trim",
                    "dimensions_mm": {
                        "outer_face_trim": 5.0,
                        "top_trim": 5.0,
                    },
                }
            ],
        }
    for member_id in ("knee_outer_left_inner_frame_block", "knee_outer_right_inner_frame_block"):
        raw = current_members[member_id]["graph_raw_geometry_summary"]
        block_specs[member_id] = {
            "constructed_blank_dimensions_mm": bounds_record(
                raw["bounds_xyz_mm"]
            )["axis_aligned_envelope_extents_xyz_mm"],
            "dimension_axes": ["global_X", "global_Y", "global_Z"],
            "basis_source_ids": ["inner_frame_block_source", "current_manifest"],
            "known_profile_features": [],
        }
    for member_id in ("knee_outer_left_spine", "knee_outer_right_spine"):
        change = report["exterior_block_changes"][member_id]
        block_specs[member_id] = {
            "prior_blank_dimensions_mm": change["before_dimensions_xyz_mm"],
            "constructed_blank_dimensions_mm": change["after_dimensions_xyz_mm"],
            "dimension_axes": ["global_X", "global_Y", "global_Z"],
            "basis_source_ids": ["outer_block_source", "review_report"],
            "known_profile_features": [
                {
                    "feature": "rip to 2x6 thickness and runner-seat extension",
                    "dimensions_mm": {
                        "thickness_reduction": 50.8,
                        "downward_extension": change["downward_extension_mm"],
                    },
                }
            ],
        }
    g7 = "wj04_upper_g7_crosscut_full_stock_cleat"
    block_specs[g7] = {
        "constructed_blank_dimensions_mm": [88.9, 88.9, 86.9],
        "dimension_axes": ["X", "T", "N"],
        "basis_source_ids": ["g7_block_source"],
        "known_profile_features": [
            {
                "feature": "G7 crosscut",
                "dimensions_mm": {"remaining_N": 86.9},
            }
        ],
    }
    if set(block_specs) != set(blocks):
        raise ValueError("Block blank-source map does not cover exactly 24 blocks")

    members: list[dict[str, Any]] = []
    for member_id in sorted(expected_wood):
        current = current_members[member_id]
        solid = solid_members[member_id]
        binding = step_bindings[member_id]
        step_path = binding["path"]
        step_actual_sha = sha256((ROOT / step_path).read_bytes())
        if step_actual_sha != binding["file_sha256"]:
            raise ValueError(f"STEP hash mismatch: {member_id}")
        raw_geo = current["graph_raw_geometry_summary"]
        finished_geo = current["graph_finished_geometry_summary"]
        shape_summary = solid["shape_summary"]
        common = {
            "member_id": member_id,
            "member_kind": solid["member_kind"],
            "composition_roles": current["composition_roles"],
            "raw_geometry_source": solid["geometry_source"],
            "source_shape_fingerprint_sha256": solid[
                "source_shape_fingerprint_sha256"
            ],
            "step": {
                "path": step_path,
                "sha256": binding["file_sha256"],
                "size_bytes": binding["size_bytes"],
                "roundtrip_valid_one_solid": binding["one_solid_valid_roundtrip"],
                "shape_summary_sha256": binding["shape_summary_sha256"],
                "topology_counts": {
                    key: shape_summary[key]
                    for key in (
                        "solid_count",
                        "shell_count",
                        "face_count",
                        "edge_count",
                        "vertex_count",
                    )
                },
                "surface_area_by_type_mm2": shape_summary[
                    "surface_area_by_type_mm2"
                ],
            },
            "raw_geometry_aabb": bounds_record(raw_geo["bounds_xyz_mm"]),
            "finished_geometry_aabb": bounds_record(shape_summary["bounds_xyz_mm"]),
            "raw_geometry_volume_mm3": raw_geo["volume_mm3"],
            "finished_geometry_volume_mm3": finished_geo["volume_mm3"],
            "raw_to_finished_volume_reduction_mm3": (
                raw_geo["volume_mm3"] - finished_geo["volume_mm3"]
            ),
            "named_profile_features": [],
            "cut_profile_decomposition_status": (
                "Named source/report features only; this is not a complete cut "
                "operation list. Other finished-profile geometry remains in the "
                "hashed STEP solid."
            ),
            "modeled_axis_ids": axis_ids_by_member[member_id],
            "finished_section": {
                "net_section_computed": False,
                "section_values_mm": None,
                "reason": (
                    "The pinned STEP is the exact finished solid and its global "
                    "AABB is recorded above. No section perpendicular to the "
                    "conditional grain/material axis was sliced; AABB, volume, "
                    "and cylindrical surface area do not determine a net section."
                ),
            },
        }
        if member_id in inventory_parts:
            part = inventory_parts[member_id]
            material = frame_grain[member_id]
            common.update(
                {
                    "source_blank_dimensions_mm": part[
                        "source_blank_dimensions_mm"
                    ],
                    "source_inventory_section_mm": part["actual_source_section_mm"],
                    "source_section_axes": ["X", "N"],
                    "source_geometry_status": part["source_geometry_status"],
                    "source_record_sha256": part["source_shape_record_sha256"],
                    "source_part_shape_sha256": part["source_shape_sha256"],
                    "source_local_shape_extents_mm": part[
                        "actual_shape_extents_local_mm"
                    ],
                    "delivered_stock_observed": part["delivered_stock_observed"],
                    "grain_frame_reference": {
                        "path": INPUTS["frame_material_map"],
                        "map_record_sha256": frame_map["record_sha256"],
                        "member_record_id": material["member_id"],
                        "conditional_grain_axis_global_xyz": material[
                            "conditional_grain_assignment"
                        ]["proposed_global_xyz"],
                        "source_local_X_T_N_axes": material["source_frame"][
                            "axes_global_xyz"
                        ],
                        "status": "conditional orientation scenario; not received grain",
                    },
                    "named_profile_features": FRAME_FEATURES.get(member_id, []),
                }
            )
        else:
            material = block_grain[member_id]
            common.update(
                {
                    "block_pattern_id": material["pattern_id"],
                    "constructed_blank_basis": block_specs[member_id],
                    "owner_finished_shape_sha256": blocks[member_id][
                        "owner_report_finished_shape_sha256"
                    ],
                    "grain_frame_reference": {
                        "path": INPUTS["block_material_map"],
                        "map_record_sha256": block_map["record_sha256"],
                        "member_record_id": material["part_id"],
                        "conditional_grain_axis_global_xyz": material[
                            "conditional_grain_assignment"
                        ]["grain_direction_global_xyz"],
                        "source_frame_axes_global_xyz": material[
                            "source_frame_axes_global_xyz"
                        ],
                        "status": "conditional pattern scenario; not received grain",
                    },
                    "named_profile_features": block_specs[member_id][
                        "known_profile_features"
                    ],
                }
            )
        members.append(common)

    record = {
        "schema": "wood_joint_current_timber_cut_section_inventory/v1",
        "attempt_id": "current-timber-cut-inventory-attempt01",
        "candidate": manifest["candidate"],
        "geometry_revision_id": manifest["geometry_revision_id"],
        "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "selected_candidate_preserved": manifest["selected_candidate_authority_preserved"],
        "status": "source_bound_cut_and_section_inventory_net_sections_uncomputed",
        "source_artifact_digests": {
            "current_manifest_sha256": manifest["manifest_sha256"],
            "member_solids_artifact_sha256": solids["artifact_sha256"],
            "member_step_bundle_sha256": solids["member_bundle_sha256"],
            "frame_material_map_sha256": frame_map["record_sha256"],
            "block_material_map_sha256": block_map["record_sha256"],
        },
        "sources": source_records(),
        "counts": {
            "frame_timbers": sum(
                row["member_kind"] == "timber" for row in members
            ),
            "candidate_blocks": sum(
                row["member_kind"] == "candidate_block" for row in members
            ),
            "inventoried_wood_members": len(members),
            "candidate_bolt_bore_axes": len(candidate_axis_map),
            "retained_frame_bolt_axes": len(retained_axis_map),
            "panel_kicker_screw_axes": len(screw_axis_map),
        },
        "section_and_cut_semantics": {
            "source_inventory_section": (
                "For frame timbers, this is the source inventory's recorded section "
                "in its X/N basis. It is a geometry/material scenario, not a "
                "delivered-stock measurement."
            ),
            "constructed_block_dimensions": (
                "For blocks, dimensions are from the pinned CAD pattern or builder "
                "and describe the named raw/constructed prism, not a purchased "
                "blank or a finished net section."
            ),
            "finished_brep": (
                "Each finished part is tied to its hashed STEP solid and readback "
                "summary. Global AABB extents are envelopes; they are not local "
                "cross-sections for rotated, tapered, notched, or bored members."
            ),
            "modeled_bores": (
                "The 92 candidate bolt axis records map receivers and shaft "
                "intervals. Shaft diameter is not timber bore diameter. Retained "
                "bolt and panel screw occupancy dimensions likewise are not a "
                "timber-hole diameter map."
            ),
            "cut_limit": (
                "Named profile operations are included only where a pinned source "
                "or report identifies them. This is not a complete operation-level "
                "cut ticket for all source-member inherited profiles."
            ),
            "net_section_computed": False,
        },
        "axis_maps": {
            "candidate_bolt_bore_axes": candidate_axis_map,
            "retained_frame_bolt_axes": retained_axis_map,
            "panel_kicker_screw_receiver_axes": screw_axis_map,
        },
        "known_missing_inputs": [
            "No per-member local net-section slices at critical bore, taper, or notch planes.",
            "No authoritative clearance-bore diameter for every current axis in the manifest.",
            "No delivered-board dimensions, grade, treatment, moisture, defects, or receiving observations.",
            "No cut tolerances, saw kerf, machining setup, or approved cut/drill instructions.",
        ],
        "native_solve_executed": False,
        "cutting_or_drilling_released": False,
        "candidate_accepted": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
        "members": members,
    }
    record["record_sha256"] = canonical_sha256(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    expected = build()
    if args.write:
        if OUT.exists():
            raise SystemExit(f"Refusing to overwrite existing inventory: {OUT}")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(
            json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        if not OUT.exists():
            raise SystemExit(f"Inventory is missing: {OUT}")
        actual = json.loads(OUT.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("Inventory is stale or differs from frozen source records")
    print(
        f"{'WROTE' if args.write else 'PASS'} {OUT.relative_to(ROOT)} "
        f"sha256={expected['record_sha256']} members={len(expected['members'])} "
        f"axes=92+12+66"
    )


if __name__ == "__main__":
    main()
