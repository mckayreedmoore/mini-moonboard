#!/usr/bin/env python3
"""Build or verify a source-only attachment topology index; no CAD is used."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")

SOURCES = {
    "geometry_snapshot": BASE / "geometry-snapshot.json",
    "contact_graph": BASE / "complete-contact-graph-attempt02.json",
    "grip_screen": BASE / "grip-screen-attempt02.json",
    "receiver_screen": BASE / "receiver-screen-attempt04.json",
    "member_solids": BASE / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json",
    "full_frame_manifest": BASE / "current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json",
    "duty_registry": Path("docs/wood-joints-mvp/duty-registry.json"),
    "family_reuse_map": Path("docs/wood-joints-mvp/current-joint-family-reuse.md"),
    "plan": Path("docs/wood-joints-mvp/next-mvp-plan.md"),
}
FAMILY_REUSE_MAP_SHA256 = "961f2365efc3d7d5b81a09a5ac2b7eae015f969b82189ed01276bdba20ddff58"

HORIZONTAL_DUTIES = [
    "clip_single_top_left_1",
    "clip_single_top_right_2",
    "clip_split_top_center_left",
    "clip_split_top_center_right",
    "clip_horizontal_bottom_left_1",
    "clip_horizontal_bottom_right_2",
    "clip_horizontal_bottom_left_2",
    "clip_horizontal_bottom_right_1",
    "clip_horizontal_lower_left_1",
    "clip_horizontal_lower_right_2",
    "clip_horizontal_lower_left_2",
    "clip_horizontal_lower_right_1",
    "clip_horizontal_upper_left_1",
    "clip_horizontal_upper_right_2",
    "clip_horizontal_upper_left_2",
    "clip_horizontal_upper_right_1",
]

SPECIAL_HORIZONTAL_AXES = {
    "clip_horizontal_lower_right_2": [
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_rail_1",
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_rail_2",
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_side_1",
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_side_2",
    ],
    "clip_horizontal_lower_right_1": [
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/lower_rail_1",
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/lower_rail_2",
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/lower_principal_1",
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/lower_principal_2",
    ],
    "clip_horizontal_upper_right_2": [
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_rail_1",
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_rail_2",
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_side_1",
        "wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_side_2",
    ],
    "clip_horizontal_upper_right_1": [
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1",
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_2",
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_principal_1",
        "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_principal_2",
    ],
}

CENTER_DUTIES = {
    "clip_split_header_center_left": [
        "center_post_left_1",
        "center_post_left_2",
        "center_post_header_left_1",
        "center_post_header_left_2",
    ],
    "clip_split_header_center_right": [
        "center_post_right_1",
        "center_post_right_2",
        "center_post_header_right_1",
        "center_post_header_right_2",
    ],
    "clip_split_base_center_left": [
        "center_principal_left_1",
        "center_principal_left_2",
        "center_principal_header_left_1",
        "center_principal_header_left_2",
    ],
    "clip_split_base_center_right": [
        "center_principal_right_1",
        "center_principal_right_2",
        "center_principal_header_right_1",
        "center_principal_header_right_2",
    ],
}

OUTER_DUTIES = {
    "clip_timber_header_outer_left": [
        "knee_outer_left_post_1",
        "knee_outer_left_post_2",
        "knee_outer_left_side_1",
        "knee_outer_left_side_2",
        "knee_outer_left_inner_header_1",
        "knee_outer_left_inner_header_2",
    ],
    "clip_angle_base_left": [
        "knee_outer_left_post_1",
        "knee_outer_left_post_2",
        "knee_outer_left_side_1",
        "knee_outer_left_side_2",
        "knee_outer_left_inner_header_1",
        "knee_outer_left_inner_header_2",
    ],
    "clip_timber_header_outer_right": [
        "knee_outer_right_post_1",
        "knee_outer_right_post_2",
        "knee_outer_right_side_1",
        "knee_outer_right_side_2",
        "knee_outer_right_inner_header_1",
        "knee_outer_right_inner_header_2",
    ],
    "clip_angle_base_right": [
        "knee_outer_right_post_1",
        "knee_outer_right_post_2",
        "knee_outer_right_side_1",
        "knee_outer_right_side_2",
        "knee_outer_right_inner_header_1",
        "knee_outer_right_inner_header_2",
    ],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pair_id(member_ids: list[str]) -> str:
    first, second = sorted(member_ids)
    return f"pair:{first}|{second}"


def build_index() -> dict[str, Any]:
    source_hashes = {
        name: sha256_bytes((ROOT / path).read_bytes())
        for name, path in SOURCES.items()
    }
    if source_hashes["family_reuse_map"] != FAMILY_REUSE_MAP_SHA256:
        raise ValueError("family mapping source changed; review and update the explicit crosswalk")
    source = {
        name: read_json(path)
        for name, path in SOURCES.items()
        if path.suffix == ".json"
    }

    snapshot = source["geometry_snapshot"]
    graph = source["contact_graph"]
    grip = source["grip_screen"]
    receiver = source["receiver_screen"]
    solids = source["member_solids"]
    manifest = source["full_frame_manifest"]
    duty_registry = source["duty_registry"]

    revision = snapshot["revision_id"]
    reviewed_commit = snapshot["reviewed_repository_commit"]
    if not all(
        value == revision
        for value in (
            graph["revision_id"],
            grip["revision_id"],
            receiver["revision_id"],
            solids["geometry_revision_id"],
            manifest["geometry_revision_id"],
        )
    ):
        raise ValueError("source records do not share one geometry revision")
    if grip["reviewed_repository_commit"] != reviewed_commit:
        raise ValueError("grip screen and geometry snapshot checkpoints differ")

    members = {member["member_id"]: member for member in solids["members"]}
    physical_member_ids = {
        item["member_id"] for item in graph["inventories"]["physical_members"]
    }
    if len(members) != 50 or physical_member_ids != set(members):
        raise ValueError("contact graph nodes do not match the 50 STEP members")
    if solids["member_scope"]["total"] != 50:
        raise ValueError("member-solids bundle has an unexpected member count")

    graph_edges = {
        pair_id(edge["member_ids"]): edge for edge in graph["edges"]
    }
    if len(graph_edges) != graph["counts"]["unique_member_pairs"]:
        raise ValueError("contact graph contains duplicate or missing pair keys")
    candidate_inventory = {
        item["axis_id"]: item
        for item in graph["inventories"]["candidate_bolt_axes"]
    }
    candidate_snapshot = snapshot["axes"]
    grip_axes = {item["axis_id"]: item for item in grip["axes"]}
    if not (
        set(candidate_inventory) == set(candidate_snapshot) == set(grip_axes)
    ):
        raise ValueError("candidate bolt-axis sources do not reconcile")
    if len(candidate_inventory) != 92:
        raise ValueError("unexpected candidate bolt-axis count")

    panel_inventory = {
        item["axis_id"]: item
        for item in graph["inventories"]["current_panel_screw_axes"]
    }
    panel_screen = {item["axis_id"]: item for item in receiver["axes"]}
    if set(panel_inventory) != set(panel_screen) or len(panel_screen) != 66:
        raise ValueError("panel screw-axis sources do not reconcile")

    retained_inventory = {
        item["axis_id"]: item
        for item in graph["inventories"]["retained_frame_bolts"]
    }
    if len(retained_inventory) != 12:
        raise ValueError("unexpected retained frame-bolt count")

    registry_duties = {
        item["legacy_duty_id"]: item for item in duty_registry["duties"]
    }
    duty_ids = set(registry_duties)
    if len(duty_ids) != 24:
        raise ValueError("duty registry does not contain 24 unique duties")
    if set(HORIZONTAL_DUTIES) | set(CENTER_DUTIES) | set(OUTER_DUTIES) != duty_ids:
        raise ValueError("family-map duty crosswalk differs from the duty registry")

    block_ids = {
        member_id
        for member_id, member in members.items()
        if member["member_kind"] == "candidate_block"
    }
    panel_screws = []
    panel_pair_ids: set[str] = set()
    for axis_id in sorted(panel_screen):
        row = panel_screen[axis_id]
        pair = pair_id([row["panel_member"], row["receiver_member"]])
        if pair not in graph_edges:
            raise ValueError(f"panel screw pair is absent from contact graph: {axis_id}")
        panel_pair_ids.add(pair)
        panel_screws.append(
            {
                "axis_id": axis_id,
                "panel_member": row["panel_member"],
                "receiver_member": row["receiver_member"],
                "previous_receiver_member": row["previous_receiver_member"],
                "current_location_status": row["current_location_status"],
                "origin_global_xyz_mm": row["origin_global_xyz_mm"],
                "axis_global_xyz": row["axis_global_xyz"],
                "contact_pair_id": pair,
            }
        )

    retained_bolts = []
    retained_pair_ids: set[str] = set()
    for axis_id, row in sorted(retained_inventory.items()):
        pairs = sorted(
            pair_id(association["member_pair"])
            for association in row["member_pair_associations"]
        )
        retained_pair_ids.update(pairs)
        retained_bolts.append(
            {
                "axis_id": axis_id,
                "source_member_ids_as_recorded": row["source_member_ids_as_recorded"],
                "source_member_pair_ids": pairs,
                "origin_global_xyz_mm": row["origin_global_xyz_mm"],
                "axis_global_xyz": row["axis_global_xyz"],
                "head_to_nut_order": "not_established_by_source_record",
            }
        )

    explicit_axis_ids: dict[str, list[str]] = {}
    for duty_id in HORIZONTAL_DUTIES:
        explicit_axis_ids[duty_id] = sorted(
            SPECIAL_HORIZONTAL_AXES[duty_id]
            if duty_id in SPECIAL_HORIZONTAL_AXES
            else [
                axis_id
                for axis_id in candidate_snapshot
                if f"/{duty_id}/" in axis_id
            ]
        )
        if len(explicit_axis_ids[duty_id]) != 4:
            raise ValueError(f"expected four horizontal axes for {duty_id}")
    explicit_axis_ids.update(CENTER_DUTIES)
    explicit_axis_ids.update(OUTER_DUTIES)

    physical_chain_for_duty: dict[str, str] = {}
    family_for_duty: dict[str, str] = {}
    reuse_scope_for_duty: dict[str, str] = {}
    for duty_id in HORIZONTAL_DUTIES:
        physical_chain_for_duty[duty_id] = f"horizontal_station:{duty_id}"
        family_for_duty[duty_id] = "horizontal_four_axis_station"
        if duty_id == "clip_horizontal_bottom_right_1":
            reuse_scope_for_duty[duty_id] = "exact_ordinary_reference_patch_only"
        elif duty_id == "clip_horizontal_upper_right_1":
            reuse_scope_for_duty[duty_id] = "unique_shortened_g7_geometry"
        else:
            reuse_scope_for_duty[duty_id] = "common_cleat_geometry_only"
    for side in ("left", "right"):
        post_duty = f"clip_split_header_center_{side}"
        principal_duty = f"clip_split_base_center_{side}"
        physical_chain_for_duty[post_duty] = f"center_post_station:{side}"
        family_for_duty[post_duty] = "center_post_four_axis_station"
        reuse_scope_for_duty[post_duty] = "center_post_geometry_pair; separate station patch"
        physical_chain_for_duty[principal_duty] = f"center_principal_station:{side}"
        family_for_duty[principal_duty] = "center_principal_four_axis_station"
        reuse_scope_for_duty[principal_duty] = "distinct_center_principal_geometry"
        for duty_id in (f"clip_timber_header_outer_{side}", f"clip_angle_base_{side}"):
            physical_chain_for_duty[duty_id] = f"outer_sandwich_chain:{side}"
            family_for_duty[duty_id] = "outer_sandwich_six_axis_chain"
            reuse_scope_for_duty[duty_id] = "same_side_shared_chain; not two independent patches"

    extra_seats: dict[str, list[tuple[list[str], str]]] = {
        "clip_split_base_center_left": [
            (["base_rail_bottom_left", "base_principal_center_left"], "current-joint-family-reuse.md")
        ],
        "clip_split_base_center_right": [
            (["base_rail_bottom_right", "base_principal_center_right"], "current-joint-family-reuse.md")
        ],
    }
    runner_seats = [
        row
        for row in receiver["bolt_declared_and_runner_contact_graph"]["interfaces"]
        if row["interface_basis"] == "reported exterior block seat on floor runner"
    ]

    candidate_axis_records = {}
    for axis_id in sorted(candidate_inventory):
        axis_snapshot = candidate_snapshot[axis_id]
        axis_grip = grip_axes[axis_id]
        graph_axis = candidate_inventory[axis_id]
        if set(axis_snapshot["receiver_ids"]) != set(
            axis_grip["ordered_receiver_ids_head_to_nut"]
        ):
            raise ValueError(f"receiver order mismatch for {axis_id}")
        graph_pair_ids = sorted(
            {
                pair_id(association["member_pair"])
                for association in graph_axis["member_pair_associations"]
            }
        )
        if not set(graph_pair_ids).issubset(graph_edges):
            raise ValueError(f"candidate-axis pair is absent: {axis_id}")
        candidate_axis_records[axis_id] = {
            "axis_id": axis_id,
            "ordered_receiver_ids_head_to_nut": axis_grip[
                "ordered_receiver_ids_head_to_nut"
            ],
            "graph_member_pair_ids": graph_pair_ids,
        }

    duties = []
    pair_ids_referenced: set[str] = set()
    candidate_axis_reference_count = 0
    for duty_id in sorted(duty_ids):
        axis_ids = explicit_axis_ids[duty_id]
        candidate_axis_reference_count += len(axis_ids)
        duty_member_ids: set[str] = set()
        axis_association_pair_ids: set[str] = set()
        for axis_id in axis_ids:
            axis_snapshot = candidate_snapshot[axis_id]
            duty_member_ids.update(axis_snapshot["receiver_ids"])
            axis_association_pair_ids.update(
                candidate_axis_records[axis_id]["graph_member_pair_ids"]
            )

        direct_seat_records: list[dict[str, str]] = []
        if duty_id in HORIZONTAL_DUTIES or duty_id in CENTER_DUTIES:
            receiver_groups = {
                tuple(sorted(candidate_snapshot[axis_id]["receiver_ids"]))
                for axis_id in axis_ids
            }
            host_ids = {
                member_id
                for group in receiver_groups
                for member_id in group
                if member_id not in block_ids
            }
            if len(host_ids) != 2:
                raise ValueError(f"cannot identify documented host seat for {duty_id}")
            direct_seat_records.append(
                {
                    "contact_pair_id": pair_id(list(host_ids)),
                    "source_basis": (
                        "current-joint-family-reuse.md: finite horizontal host-to-host seat"
                        if duty_id in HORIZONTAL_DUTIES
                        else "current-joint-family-reuse.md: direct center host seat"
                    ),
                }
            )
        for members_for_seat, source_basis in extra_seats.get(duty_id, []):
            direct_seat_records.append(
                {
                    "contact_pair_id": pair_id(members_for_seat),
                    "source_basis": source_basis,
                }
            )
        if duty_id in OUTER_DUTIES:
            side = "left" if duty_id.endswith("left") else "right"
            spine_id = f"knee_outer_{side}_spine"
            for row in runner_seats:
                if spine_id in row["members"]:
                    direct_seat_records.append(
                        {
                            "contact_pair_id": pair_id(row["members"]),
                            "source_basis": "receiver-screen-attempt04: exterior block-to-runner seat",
                        }
                    )
                    duty_member_ids.update(row["members"])
        for seat in direct_seat_records:
            seat_pair_id = seat["contact_pair_id"]
            if seat_pair_id not in graph_edges:
                raise ValueError(f"documented seat is absent from graph: {duty_id}")
            if graph_edges[seat_pair_id]["finite_shared_planar_face_area_mm2"] <= 0:
                raise ValueError(f"documented seat has no finite graph contact: {duty_id}")
            duty_member_ids.update(graph_edges[seat_pair_id]["member_ids"])

        unknown_members = duty_member_ids - set(members)
        if unknown_members:
            raise ValueError(f"duty references missing STEP members: {sorted(unknown_members)}")

        relevant_retained = []
        for retained in retained_bolts:
            shared_members = sorted(
                set(retained["source_member_ids_as_recorded"]) & duty_member_ids
            )
            if shared_members:
                relevant_retained.append(
                    {
                        "axis_id": retained["axis_id"],
                        "source_member_pair_ids": retained["source_member_pair_ids"],
                        "shared_member_ids_only": shared_members,
                    }
                )

        relevant_panel_screws = []
        relevant_panel_pair_ids: set[str] = set()
        for screw in panel_screws:
            if screw["receiver_member"] in duty_member_ids:
                relevant_panel_screws.append(
                    {
                        "axis_id": screw["axis_id"],
                        "panel_member": screw["panel_member"],
                        "receiver_member": screw["receiver_member"],
                        "contact_pair_id": screw["contact_pair_id"],
                        "relation": "shared_receiver_member_only_not_station_local",
                    }
                )
                relevant_panel_pair_ids.add(screw["contact_pair_id"])

        connection_pair_ids = axis_association_pair_ids | {
            seat["contact_pair_id"] for seat in direct_seat_records
        }
        all_pair_ids = connection_pair_ids | relevant_panel_pair_ids
        pair_ids_referenced.update(all_pair_ids)
        duty_members = [member_ref(member_id, members) for member_id in sorted(duty_member_ids)]
        contact_pair_ids = sorted(
            graph_pair_id
            for graph_pair_id in connection_pair_ids
            if graph_edges[graph_pair_id]["finite_shared_planar_face_area_mm2"] > 0
        )
        noncontact_association_pair_ids = sorted(
            graph_pair_id
            for graph_pair_id in axis_association_pair_ids
            if graph_edges[graph_pair_id]["finite_shared_planar_face_area_mm2"] == 0
        )
        duties.append(
            {
                "former_duty_id": duty_id,
                "physical_connection_id": physical_chain_for_duty[duty_id],
                "connection_family": family_for_duty[duty_id],
                "geometry_reuse_scope": reuse_scope_for_duty[duty_id],
                "replacement_status": "geometry_crosswalk_only_not_accepted",
                "member_ids": sorted(duty_member_ids),
                "members": duty_members,
                "candidate_bolt_axis_ids": axis_ids,
                "candidate_axis_associated_graph_pair_ids": sorted(
                    axis_association_pair_ids
                ),
                "connection_graph_pair_ids": sorted(connection_pair_ids),
                "finite_contact_pair_ids": contact_pair_ids,
                "noncontact_axis_membership_pair_ids": noncontact_association_pair_ids,
                "additional_nonfastener_contact_pairs": sorted(
                    direct_seat_records,
                    key=lambda row: row["contact_pair_id"],
                ),
                "retained_frame_bolt_relations_by_shared_member_only": relevant_retained,
                "panel_screw_relations_by_shared_receiver_only": relevant_panel_screws,
            }
        )

    for row in graph["inventories"]["candidate_bolt_axes"]:
        for association in row["member_pair_associations"]:
            pair_ids_referenced.add(pair_id(association["member_pair"]))
    pair_ids_referenced.update(retained_pair_ids)
    pair_ids_referenced.update(panel_pair_ids)
    for row in direct_seat_records:
        pair_ids_referenced.add(row["contact_pair_id"])

    pair_catalog = []
    for graph_pair_id in sorted(pair_ids_referenced):
        edge = graph_edges[graph_pair_id]
        pair_catalog.append(
            {
                "pair_id": graph_pair_id,
                "member_ids": edge["member_ids"],
                "geometry_state": edge["geometry_state"],
                "interface_geometry_state": edge["interface_geometry_state"],
                "finite_shared_planar_face_area_mm2": edge[
                    "finite_shared_planar_face_area_mm2"
                ],
                "opposed_planar_face_contact_area_mm2": edge[
                    "opposed_planar_face_contact_area_mm2"
                ],
                "common_volume_mm3": edge["common_volume_mm3"],
                "minimum_separation_mm": edge["minimum_separation_mm"],
                "candidate_bolt_axis_ids": sorted(
                    {
                        association["axis_id"]
                        for association in edge["candidate_bolt_associations"]
                    }
                ),
                "retained_frame_bolt_axis_ids": sorted(
                    {
                        association["axis_id"]
                        for association in edge["retained_frame_bolt_source_membership"]
                    }
                ),
                "panel_screw_axis_ids": sorted(
                    {
                        association["axis_id"]
                        for association in edge["current_panel_screw_associations"]
                    }
                ),
            }
        )

    member_catalog = [member_ref(member_id, members) for member_id in sorted(members)]
    unique_duty_axes = {
        axis_id for duty in duties for axis_id in duty["candidate_bolt_axis_ids"]
    }
    if unique_duty_axes != set(candidate_inventory):
        raise ValueError("former-duty crosswalk does not cover all 92 candidate axes")
    unique_chains = {duty["physical_connection_id"] for duty in duties}

    payload = {
        "schema": "wood_joint_current_attachment_topology/v1",
        "attempt_id": "current-attachment-topology-attempt01",
        "candidate": solids["candidate"],
        "geometry_revision_id": revision,
        "reviewed_source_commit": reviewed_commit,
        "selected_candidate_preserved": solids["selected_candidate_preserved"],
        "scope": "source-bound geometry and membership crosswalk; no mechanics result",
        "pair_id_definition": (
            "Derived join key: pair:<lexicographically-first-member-id>|<second-member-id>. "
            "The source graph has member-pair rows but no native pair ID."
        ),
        "source_sha256": source_hashes,
        "source_artifact_identities": {
            "contact_graph_file_sha256": source_hashes["contact_graph"],
            "member_solids_artifact_sha256": solids["artifact_sha256"],
            "member_step_set_sha256": solids["member_bundle_sha256"],
            "joint_family_reuse_map_file_sha256": source_hashes["family_reuse_map"],
            "current_plan_file_sha256": source_hashes["plan"],
        },
        "counts": {
            "physical_member_nodes": len(members),
            "timber_member_solids": solids["member_scope"]["timber"],
            "panel_member_solids": solids["member_scope"]["plywood_panel"],
            "candidate_block_solids": solids["member_scope"]["candidate_block"],
            "contact_graph_member_pairs": graph["counts"]["unique_member_pairs"],
            "contact_graph_exact_brep_pairs_evaluated": graph["counts"][
                "exact_brep_pairs_evaluated"
            ],
            "contact_graph_aabb_separated_pairs_not_exactly_evaluated": graph[
                "counts"
            ]["aabb_separated_pairs_not_exactly_evaluated"],
            "contact_graph_finite_contacts": sum(
                edge["geometry_state"] == "finite_opposed_planar_touch"
                for edge in graph["edges"]
            ),
            "contact_graph_zero_area_or_unresolved_tangencies": sum(
                edge["geometry_state"] == "zero_area_touch_or_unresolved"
                for edge in graph["edges"]
            ),
            "contact_graph_separated_pairs": sum(
                edge["geometry_state"] == "separated" for edge in graph["edges"]
            ),
            "contact_graph_positive_volume_overlaps": sum(
                edge["common_volume_mm3"] > 0 for edge in graph["edges"]
            ),
            "former_duties": len(duties),
            "unique_candidate_bolt_axes_crosswalked": len(unique_duty_axes),
            "candidate_axis_references_across_duty_rows": candidate_axis_reference_count,
            "unique_physical_connection_ids": len(unique_chains),
            "retained_frame_bolt_axes": len(retained_bolts),
            "retained_frame_bolt_member_pairs": len(retained_pair_ids),
            "panel_screw_axes": len(panel_screws),
            "panel_screw_panel_receiver_pairs": len(panel_pair_ids),
            "referenced_contact_graph_pairs": len(pair_catalog),
        },
        "contact_graph_scope_and_limits": graph["scope"],
        "member_step_solids": member_catalog,
        "candidate_bolt_axes": list(candidate_axis_records.values()),
        "contact_pair_catalog": pair_catalog,
        "retained_frame_bolts": retained_bolts,
        "panel_screw_axes": panel_screws,
        "former_duties": duties,
        "readiness": {
            "source_geometry_and_member_identity_reconciled": True,
            "pair_level_topology_crosswalk_ready": True,
            "solver_surface_map_ready": False,
            "active_contact_and_attachment_law_ready": False,
            "mechanics_method_applicability_demonstrated": False,
            "current_demands_available": False,
            "replacement_duties_accepted": 0,
            "step3_complete": False,
        },
        "claim_limits": [
            "This artifact crosswalks existing source records and exact member STEP identities only.",
            "Contact pair IDs are derived member-pair keys, not native graph identifiers.",
            "The contact graph is pair-level and is not a solver surface map; it has no face IDs, normals, or patch coordinates.",
            "Pair membership and finite face area do not establish active contact, load transfer, load sharing, stiffness, resistance, or capacity.",
            "Retained-bolt and panel-screw links on a former-duty row are shared-member associations only, not station-local paths or demands.",
            "The index supplies no contact law, material law, fastener engagement, solver mapping, fresh demand, or duty acceptance.",
            "Step 3 remains open pending family-specific mechanics representations and applicability evidence.",
        ],
    }
    artifact_digest = sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return {**payload, "artifact_sha256": artifact_digest}


def member_ref(member_id: str, members: dict[str, dict[str, Any]]) -> dict[str, Any]:
    member = members[member_id]
    return {
        "member_id": member_id,
        "member_kind": member["member_kind"],
        "step_file": member["step_file"],
        "step_sha256": member["step_sha256"],
        "source_shape_fingerprint_sha256": member["source_shape_fingerprint_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the deterministic index")
    mode.add_argument("--verify", action="store_true", help="verify the index against sources")
    args = parser.parse_args()
    destination = HERE / "attachment-topology.json"
    expected = build_index()
    encoded = json.dumps(expected, indent=2, sort_keys=True) + "\n"
    if args.write:
        destination.write_text(encoded, encoding="utf-8")
        print(f"wrote {destination.relative_to(ROOT)}")
        print(f"artifact_sha256={expected['artifact_sha256']}")
        return 0
    if not destination.exists():
        print(f"missing artifact: {destination}", file=sys.stderr)
        return 1
    actual = read_json(destination)
    if actual != expected:
        print("attachment topology artifact differs from pinned source records", file=sys.stderr)
        return 1
    print(
        "verified "
        f"{expected['counts']['former_duties']} duties, "
        f"{expected['counts']['unique_candidate_bolt_axes_crosswalked']} unique candidate axes, "
        f"{expected['counts']['retained_frame_bolt_axes']} retained bolts, "
        f"{expected['counts']['panel_screw_axes']} panel screws, "
        f"{expected['counts']['referenced_contact_graph_pairs']} referenced contact pairs"
    )
    print(f"artifact_sha256={expected['artifact_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
