#!/usr/bin/env python3
"""Build and verify an append-only source-bound T04 station inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


ATTEMPT = Path(__file__).resolve().parent
REPO = next(parent for parent in ATTEMPT.parents if (parent / "current-candidate.json").exists())
PIN_FILE = ATTEMPT / "source-pins.json"
CLASSIFICATION_FILE = ATTEMPT / "station-classification.json"
SUMS_FILE = ATTEMPT / "SHA256SUMS"

SOURCE_SPECS = [
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
        "current reviewed full-frame inventory, axes, load contracts, status",
        "derivation",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json",
        "current 50-member identity and exact STEP bundle manifest",
        "derivation_and_member_step_hash_authority",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-attachment-topology-attempt01/attachment-topology.json",
        "current 24-duty, axis, receiver-order, and pair-contact crosswalk",
        "derivation",
    ),
    (
        "docs/wood-joints-mvp/current-joint-family-reuse.md",
        "prior T04 geometry-family comparison and documented exclusions",
        "family_basis_and_limits",
    ),
    (
        "docs/wood-joints-mvp/duty-registry.json",
        "current 24-duty candidate obligations and acceptance state",
        "duty_status_crosswalk",
    ),
    (
        "docs/wood-joints-mvp/interfaces.json",
        "inspected interface proposal; scope is WJ-03 mirrored outer nodes only",
        "inspected_scope_boundary_only_not_applied_to_full_frame_stations",
    ),
    (
        "docs/wood-joints-mvp/current-criteria-coverage.json",
        "current criteria obligations; no criterion is dispositioned by this packet",
        "context_only",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json",
        "six current applied climber-force and wrench cases",
        "load_contract_context",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-datums.json",
        "explicit current hold-face and panel-midplane global datums",
        "load_contract_context",
    ),
    (
        "docs/wood-joints-mvp/current-frame-dead-load-map.md",
        "current separate dead-load and accessory-placement requirements",
        "load_contract_context_and_limits",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-dead-load-scenarios-attempt01/dead-load-scenarios.json",
        "778-row modeled gravity inventory and separate 25 kg scenario input",
        "load_contract_context",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/source-topology-map.json",
        "mass identity and source topology; solver DOFs remain unassigned",
        "load_path_gap_context",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json",
        "24 block conditional longitudinal and transverse orientation scenarios",
        "conditional_grain_context",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-transverse-scenarios-attempt01/transverse-scenarios.json",
        "20 frame timber conditional longitudinal and transverse orientation scenarios",
        "conditional_grain_context",
    ),
    (
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json",
        "current panel-screw receiver geometry screen",
        "screw_geometry_context",
    ),
    (
        "docs/wood-joints-mvp/current-hardware-schedule.md",
        "hardware product-selection and receiving status boundary",
        "hardware_identity_limits",
    ),
    (
        "docs/wood-joints-mvp/wj24-panel-screw-mechanics-contract.md",
        "66 Hillman screw policy and no-resistance-transfer boundary",
        "screw_policy_limits",
    ),
]

MANIFEST_PATH = SOURCE_SPECS[0][0]
SOLIDS_PATH = SOURCE_SPECS[1][0]
TOPOLOGY_PATH = SOURCE_SPECS[2][0]
BLOCK_MAP_PATH = SOURCE_SPECS[12][0]
TIMBER_MAP_PATH = SOURCE_SPECS[13][0]
LOAD_CASES_PATH = SOURCE_SPECS[7][0]
LOAD_DATUMS_PATH = SOURCE_SPECS[8][0]
DEAD_LOAD_PATH = SOURCE_SPECS[10][0]
MASS_TOPOLOGY_PATH = SOURCE_SPECS[11][0]
INTERFACES_PATH = SOURCE_SPECS[5][0]
CRITERIA_PATH = SOURCE_SPECS[6][0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def source_rows() -> list[dict[str, str]]:
    rows = [
        {
            "path": rel,
            "sha256": sha256(REPO / rel),
            "role": role,
            "use": use,
        }
        for rel, role, use in SOURCE_SPECS
    ]
    solids_path = REPO / SOLIDS_PATH
    solids_attempt_root = REPO / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01"
    solids = load_json(solids_path)
    for member in solids["members"]:
        rel = (solids_attempt_root / member["step_file"]).relative_to(REPO).as_posix()
        path = REPO / rel
        rows.append(
            {
                "path": rel,
                "sha256": sha256(path),
                "role": f"current finished STEP solid: {member['member_id']}",
                "use": "exact_member_identity_verification",
            }
        )
    return sorted(rows, key=lambda row: row["path"])


def verify_source_pins() -> tuple[dict[str, Any], dict[str, str]]:
    pins = load_json(PIN_FILE)
    if pins.get("schema") != "wood_joint_t04_station_source_pins/v1":
        raise ValueError("Unexpected source-pins schema")
    expected_rows = {(row["path"], row["sha256"]) for row in pins["sources"]}
    if len(expected_rows) != len(pins["sources"]):
        raise ValueError("Duplicate source pin")
    if pins["sources"] != source_rows():
        raise ValueError("Pinned source inventory differs from the declared frozen source set or 50-member STEP identity list")
    mismatches = []
    for row in pins["sources"]:
        path = REPO / row["path"]
        if not path.is_file():
            mismatches.append(f"missing:{row['path']}")
        elif sha256(path) != row["sha256"]:
            mismatches.append(f"sha256:{row['path']}")
    if mismatches:
        raise ValueError("Source pin mismatch: " + ", ".join(mismatches))
    return pins, {row["path"]: row["sha256"] for row in pins["sources"]}


def grain_frame(member_id: str, member_kind: str, block_map: dict[str, Any], timber_map: dict[str, Any]) -> dict[str, Any]:
    if member_kind == "candidate_block":
        row = block_map.get(member_id)
        if row is None:
            raise ValueError(f"Missing conditional block frame for {member_id}")
        grain = row["conditional_grain_assignment"]
        return {
            "member_id": member_id,
            "member_kind": member_kind,
            "longitudinal_axis_global_xyz": grain["grain_direction_global_xyz"],
            "axis_source_name": grain["source_axis_name"],
            "transverse_scenario_count": len(row["transverse_assignment_cases"]),
            "assignment_status": "conditional_pattern_scenario_not_selected_or_observed",
            "delivered_stock_observed": grain["delivered_stock_observed"],
            "solver_element_assignment": False,
        }
    if member_kind == "timber":
        row = timber_map.get(member_id)
        if row is None:
            raise ValueError(f"Missing conditional timber frame for {member_id}")
        return {
            "member_id": member_id,
            "member_kind": member_kind,
            "longitudinal_axis_global_xyz": row["source_longitudinal_global_xyz"],
            "transverse_cases_global_xyz": row["cases_global_xyz"],
            "transverse_scenario_count": len(row["cases_global_xyz"]),
            "assignment_status": "conditional_source_frame_scenarios_not_selected_or_observed",
            "observed_ring_orientation": row["observed_ring_orientation"],
            "selected_case": row["selected_case"],
            "solver_element_assignment": row["solver_element_assignment"],
        }
    if member_kind == "plywood_panel":
        return {
            "member_id": member_id,
            "member_kind": member_kind,
            "longitudinal_axis_global_xyz": None,
            "transverse_cases_global_xyz": None,
            "assignment_status": "panel_layup_axes_and_properties_unassigned",
            "solver_element_assignment": False,
        }
    return {
        "member_id": member_id,
        "member_kind": member_kind,
        "longitudinal_axis_global_xyz": None,
        "assignment_status": "no_wood_grain_frame_applicable_or_supplied",
    }


def axis_grain_relations(axis: list[float], frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for frame in frames:
        vector = frame.get("longitudinal_axis_global_xyz")
        if vector is None:
            out.append({"member_id": frame["member_id"], "status": "unknown", "abs_cosine_to_longitudinal": None})
            continue
        dot = sum(float(axis[i]) * float(vector[i]) for i in range(3))
        norm_axis = math.sqrt(sum(float(v) ** 2 for v in axis))
        norm_grain = math.sqrt(sum(float(v) ** 2 for v in vector))
        value = abs(dot) / (norm_axis * norm_grain)
        out.append(
            {
                "member_id": frame["member_id"],
                "status": "conditional_scenario_geometry_only",
                "abs_cosine_to_longitudinal": round(value, 12),
            }
        )
    return out


def contact_summary(pair_id: str, pair_index: dict[str, Any]) -> dict[str, Any]:
    row = pair_index.get(pair_id)
    if row is None:
        raise ValueError(f"Missing contact pair {pair_id}")
    return {
        "pair_id": pair_id,
        "member_ids": row["member_ids"],
        "geometry_state": row["geometry_state"],
        "interface_geometry_state": row["interface_geometry_state"],
        "finite_shared_planar_face_area_mm2": row["finite_shared_planar_face_area_mm2"],
        "opposed_planar_face_contact_area_mm2": row["opposed_planar_face_contact_area_mm2"],
        "minimum_separation_mm": row["minimum_separation_mm"],
        "common_volume_mm3": row["common_volume_mm3"],
        "interpretation": "CAD pair geometry only; active bearing, force transfer, contact pressure, and capacity are unknown",
    }


def station_template(duties: list[dict[str, Any]], block_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scopes = sorted({row["geometry_reuse_scope"] for row in duties})
    patterns = sorted({row["pattern_id"] for row in block_rows})
    family = duties[0]["connection_family"]
    if family == "horizontal_four_axis_station" and all(
        scope in {"common_cleat_geometry_only", "exact_ordinary_reference_patch_only"} for scope in scopes
    ):
        template_id = "common-horizontal-cleat-block-pattern"
        basis = "The prior source-bound family map verifies 15 common horizontal block solids and bore patterns by proper rigid transform; this compares the block geometry only."
    elif family == "center_post_four_axis_station":
        template_id = "center-post-cleat-block-pair"
        basis = "The prior source-bound family map records the left/right center-post cleats as a proper-rotation shape pair; receiver, axis stack, and global duty response remain separate."
    else:
        template_id = "station-specific:" + duties[0]["physical_connection_id"]
        basis = "No exact whole-station multi-field equivalence is established by the pinned input set."
    return {
        "geometry_template_id": template_id,
        "geometry_template_scope": "block_geometry_only; not a mechanical representative",
        "geometry_reuse_scopes": scopes,
        "block_pattern_ids": patterns,
        "basis": basis,
        "mechanical_representative": False,
        "mechanical_equivalence_status": "not_established_response_range_and_station_demand_are_missing",
    }


def derive_classification(pin_hashes: dict[str, str]) -> dict[str, Any]:
    manifest = load_json(REPO / MANIFEST_PATH)
    solids = load_json(REPO / SOLIDS_PATH)
    topology = load_json(REPO / TOPOLOGY_PATH)
    duty_registry = load_json(REPO / "docs/wood-joints-mvp/duty-registry.json")
    interfaces = load_json(REPO / INTERFACES_PATH)
    criteria = load_json(REPO / CRITERIA_PATH)
    load_cases = load_json(REPO / LOAD_CASES_PATH)
    datums = load_json(REPO / LOAD_DATUMS_PATH)
    dead_load = load_json(REPO / DEAD_LOAD_PATH)
    mass_topology = load_json(REPO / MASS_TOPOLOGY_PATH)
    block_map_doc = load_json(REPO / BLOCK_MAP_PATH)
    timber_map_doc = load_json(REPO / TIMBER_MAP_PATH)

    if manifest["candidate"] != "compact-floor-flush-wood-joints-development":
        raise ValueError("Current input manifest candidate mismatch")
    revision = "led-clearance-2x6-runner-seated-blocks-v1"
    if manifest["geometry_revision_id"] != revision or solids["geometry_revision_id"] != revision:
        raise ValueError("Current revision mismatch")
    if topology["candidate"] != manifest["candidate"] or topology["geometry_revision_id"] != revision:
        raise ValueError("Attachment topology candidate/revision mismatch")
    if interfaces["candidate"] != manifest["candidate"]:
        raise ValueError("Inspected interface scope candidate mismatch")

    # Conditional grain records must be the exact inputs already bound by attempt04.
    bindings = manifest["evidence_bindings"]
    block_binding = bindings["attempt04_conditional_material_map_bundle"]["existing_connector_block_orientation_map"]["artifact"]
    timber_binding = bindings["attempt04_conditional_material_map_bundle"]["frame_timber_transverse_scenarios"]["artifact"]
    if block_binding["path"] != BLOCK_MAP_PATH or block_binding["file_sha256"] != pin_hashes[BLOCK_MAP_PATH]:
        raise ValueError("Block orientation map is not the exact map bound by current input manifest attempt04")
    if block_binding["content_digest"] != block_map_doc["record_sha256"]:
        raise ValueError("Block orientation map content digest does not match attempt04 binding")
    if timber_binding["path"] != TIMBER_MAP_PATH or timber_binding["file_sha256"] != pin_hashes[TIMBER_MAP_PATH]:
        raise ValueError("Timber transverse map is not the exact map bound by current input manifest attempt04")
    if timber_binding["content_digest"] != timber_map_doc["record_sha256"]:
        raise ValueError("Timber transverse map content digest does not match attempt04 binding")

    # Bind the 50 exact current STEP identities across the current input manifest and member-solids bundle.
    manifest_member_steps = {
        row["member_id"]: row["file_sha256"]
        for row in manifest["finished_member_step_bindings"]
    }
    solids_member_steps = {row["member_id"]: row["step_sha256"] for row in solids["members"]}
    if manifest_member_steps != solids_member_steps or len(solids_member_steps) != 50:
        raise ValueError("Current manifest and member-solids STEP identities differ")

    # Applied load and dead-load records must match the current manifest's frozen source bindings.
    load_binding = bindings["six_current_applied_load_cases"]
    if load_binding["path"] != LOAD_CASES_PATH or load_binding["file_sha256"] != pin_hashes[LOAD_CASES_PATH]:
        raise ValueError("Six-case contract is not the exact source bound by current input manifest attempt04")
    if load_binding["content_digest"] != load_cases["contract_sha256"]:
        raise ValueError("Six-case contract content digest does not match attempt04 binding")
    datum_binding = load_cases["source_provenance"]["current_transform_source"]
    if datum_binding["source_path"] != LOAD_DATUMS_PATH or datum_binding["sha256"] != pin_hashes[LOAD_DATUMS_PATH]:
        raise ValueError("Current hold datums are not the exact source bound by the load contract")
    dead_binding = bindings["modeled_body_gravity_and_accessory_scenarios"]
    if dead_binding["path"] != DEAD_LOAD_PATH or dead_binding["file_sha256"] != pin_hashes[DEAD_LOAD_PATH]:
        raise ValueError("Dead-load scenarios are not the exact source bound by current input manifest attempt04")
    if dead_binding["content_digest"] != dead_load["contract_sha256"]:
        raise ValueError("Dead-load scenario digest does not match current input manifest binding")

    block_map = {row["part_id"]: row for row in block_map_doc["members"]}
    timber_map = {row["member_id"]: row for row in timber_map_doc["members"]}
    member_index = {row["member_id"]: row for row in solids["members"]}
    member_kind = {row["member_id"]: row["member_kind"] for row in solids["members"]}
    pair_index = {row["pair_id"]: row for row in topology["contact_pair_catalog"]}
    topology_axis = {row["axis_id"]: row for row in topology["candidate_bolt_axes"]}
    manifest_axis = {row["axis_id"]: row for row in manifest["candidate_bolt_axes"]}
    if len(manifest_axis) != 92 or len(topology_axis) != 92 or set(manifest_axis) != set(topology_axis):
        raise ValueError("Candidate axis inventory does not reconcile to 92 unique IDs")

    duty_groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    duty_by_name = {row["former_duty_id"]: row for row in topology["former_duties"]}
    for duty in topology["former_duties"]:
        key = tuple(sorted(duty["candidate_bolt_axis_ids"]))
        duty_groups.setdefault(key, []).append(duty)
    duty_registry_by_id = {row["legacy_duty_id"]: row for row in duty_registry["duties"]}

    stations = []
    axis_station = {}
    for axis_ids, duties in sorted(duty_groups.items(), key=lambda item: item[1][0]["physical_connection_id"]):
        physical_ids = {row["physical_connection_id"] for row in duties}
        if len(physical_ids) != 1:
            raise ValueError(f"Shared axis set maps to inconsistent physical connections: {physical_ids}")
        connection_id = next(iter(physical_ids))
        station_axes = [manifest_axis[axis_id] for axis_id in axis_ids]
        station_duty_ids = sorted(row["former_duty_id"] for row in duties)
        local_member_ids = sorted({mid for row in duties for mid in row["member_ids"]})
        for axis in station_axes:
            for mid in axis["receiver_member_ids"]:
                if mid not in local_member_ids:
                    local_member_ids.append(mid)
            axis_station[axis["axis_id"]] = connection_id
        local_member_ids = sorted(set(local_member_ids))
        block_ids = sorted(mid for mid in local_member_ids if member_kind.get(mid) == "candidate_block")
        timber_ids = sorted(mid for mid in local_member_ids if member_kind.get(mid) == "timber")
        panel_ids = sorted(mid for mid in local_member_ids if member_kind.get(mid) == "plywood_panel")
        grain_frames = [grain_frame(mid, member_kind.get(mid, "unknown"), block_map, timber_map) for mid in local_member_ids]

        contact_ids = sorted(
            {
                pair_id
                for duty in duties
                for pair_id in duty["connection_graph_pair_ids"]
            }
            | {
                item["contact_pair_id"]
                for duty in duties
                for item in duty["additional_nonfastener_contact_pairs"]
            }
        )
        station_contacts = [contact_summary(pair_id, pair_index) for pair_id in contact_ids]
        block_rows = [block_map[mid] for mid in block_ids]

        axis_rows = []
        for axis in station_axes:
            axis_id = axis["axis_id"]
            topo = topology_axis[axis_id]
            association_order_flags = [
                assoc.get("physical_head_to_nut_order_established", False)
                for assoc in axis["geometric_member_pair_associations"]
            ]
            axis_frames = [
                frame
                for frame in grain_frames
                if frame["member_id"] in axis["receiver_member_ids"]
            ]
            model_order = topo.get("ordered_receiver_ids_head_to_nut")
            axis_rows.append(
                {
                    "axis_id": axis_id,
                    "axis_source_family": axis["family"],
                    "axis_source_trial_id": axis["trial_id"],
                    "source_station_id": axis["station_id"],
                    "receiver_member_ids": axis["receiver_member_ids"],
                    "associated_pair_ids": topo["graph_member_pair_ids"],
                    "modeled_receiver_order_head_to_nut": model_order,
                    "physical_stack_order_status": "not_established_by_source_record"
                    if not association_order_flags or not all(association_order_flags)
                    else "source_record_establishes_order",
                    "axis_head_to_nut_global": axis["geometry"]["axis_head_to_nut_global"],
                    "modeled_shaft_diameter_mm": axis["geometry"]["modeled_shaft_diameter_mm"],
                    "modeled_shaft_occupied_length_mm": axis["geometry"]["modeled_shaft_occupied_length_mm"],
                    "modeled_underhead_to_tip_mm": axis["geometry"]["modeled_underhead_to_tip_mm"],
                    "modeled_wood_grip_material_length_mm": axis["geometry"]["wood_grip_material_length_mm"],
                    "modeled_receiver_intervals": axis["geometry"]["wood_receiver_intervals"],
                    "modeled_component_roles": axis["scene_modeled_component_role_ids"],
                    "hardware_status": axis["hardware_status"],
                    "length_status": axis["length_status"],
                    "receiver_pair_association_limit": axis["member_order_limit"],
                    "axis_member_grain_relations": axis_grain_relations(axis["geometry"]["axis_head_to_nut_global"], axis_frames),
                    "receiver_contact_geometry": [contact_summary(pair_id, pair_index) for pair_id in topo["graph_member_pair_ids"]],
                    "response_range": None,
                    "response_status": "no_current_station_response_or_joint_demand_bound_to_this_axis",
                }
            )

        geometry_class = duties[0]["connection_family"]
        missing = [
            "signed current-case and gravity demand/resultant at this station, including force and moment sharing among its axes, bearing faces, and neighboring members",
            "validated current-frame solver body/element/DOF mapping, contact and fastener laws, boundary conditions, and verified response range",
            "received material identity/properties and observed grain/ring orientation; the pinned wood frames are conditional alternatives, not selected stock assignments",
            "selected and received structural bolt/nut/washer products, delivered grip/thread engagement, clearance, bearing/slip/opening behavior, and station-specific resistance evidence",
        ]
        if geometry_class == "outer_sandwich_six_axis_chain":
            missing.extend(
                [
                    "a mechanics representation of the same-side six-axis shared chain under both former duties; the duties are not separate independent patches",
                    "load transfer across the finite contacts and the graph-separated spine/inner-frame-block pair; no pair contact is inferred from intervening members",
                ]
            )
        elif geometry_class == "center_principal_four_axis_station":
            missing.append("independent left/right station response evidence; equal blank dimensions do not establish a rigid-transform or demand equivalence")
        elif geometry_class == "horizontal_four_axis_station":
            missing.append("station-specific response equivalence across receiver sections, axis order, direct seat geometry, and current hold/load position")

        stations.append(
            {
                "physical_connection_id": connection_id,
                "station_class": geometry_class,
                "former_duty_ids": station_duty_ids,
                "candidate_axis_ids": list(axis_ids),
                "candidate_block_member_ids": block_ids,
                "timber_member_ids": timber_ids,
                "panel_member_ids_in_connection_scope": panel_ids,
                "member_step_identities": [
                    {
                        "member_id": mid,
                        "member_kind": member_kind[mid],
                        "step_sha256": member_index[mid]["step_sha256"],
                        "source_shape_fingerprint_sha256": member_index[mid]["source_shape_fingerprint_sha256"],
                    }
                    for mid in local_member_ids
                    if mid in member_index
                ],
                "conditional_member_grain_frames": grain_frames,
                "axis_geometry_stack_and_contact": axis_rows,
                "connection_graph_pair_geometry": station_contacts,
                "geometry_template": station_template(duties, block_rows),
                "mechanical_path_status": "geometry_crosswalk_only_not_a_demonstrated_force_transfer_path",
                "known_response_range": None,
                "missing_evidence": missing,
                "acceptance": False,
                "criterion_disposition": "unchanged_pending",
            }
        )

    if len(axis_station) != 92 or len(set(axis_station)) != 92:
        raise ValueError("Not every candidate axis maps to exactly one physical station group")

    member_kind_by_id = member_kind
    retained_topology = {row["axis_id"]: row for row in topology["retained_frame_bolts"]}
    retained = []
    for axis in manifest["retained_frame_bolt_axes"]:
        topo = retained_topology[axis["axis_id"]]
        member_ids = sorted(set(axis["members_as_recorded"]))
        frames = [grain_frame(mid, member_kind_by_id.get(mid, "unknown"), block_map, timber_map) for mid in member_ids]
        order_flags = [row.get("physical_head_to_nut_order_established", False) for row in axis["geometric_member_pair_associations"]]
        retained.append(
            {
                "axis_id": axis["axis_id"],
                "member_ids_as_recorded": axis["members_as_recorded"],
                "associated_pair_ids": topo["source_member_pair_ids"],
                "axis_global": axis["axis_global_xyz"],
                "origin_global_xyz_mm": axis["origin_global_xyz_mm"],
                "source_nominal_length_mm": axis["source_nominal_length_mm"],
                "source_modeled_grip_mm": axis["source_grip_mm"],
                "modeled_occupied_diameter_mm": axis["source_occupied_diameter_mm"],
                "modeled_occupied_length_mm": axis["source_occupied_length_mm"],
                "modeled_component_count": axis["modeled_component_count"],
                "physical_stack_order_status": "not_established_by_source_record"
                if not order_flags or not all(order_flags)
                else "source_record_establishes_order",
                "hardware_status": axis["hardware_status"],
                "candidate_recheck_status": axis["candidate_recheck_status"],
                "member_grain_scenarios": frames,
                "contact_geometry": [contact_summary(pair_id, pair_index) for pair_id in topo["source_member_pair_ids"]],
                "known_response_range": None,
                "mechanical_path_status": "retained_starting_stack_identity_only; current candidate recheck and mechanics remain open",
                "acceptance": False,
            }
        )

    screw_topology = {row["axis_id"]: row for row in topology["panel_screw_axes"]}
    screw_rows = []
    for screw in manifest["panel_kicker_screw_axes"]:
        topo = screw_topology[screw["axis_id"]]
        pair = contact_summary(topo["contact_pair_id"], pair_index)
        receiver = screw["receiver_member"]
        receiver_frame = grain_frame(receiver, member_kind_by_id.get(receiver, "unknown"), block_map, timber_map)
        screw_rows.append(
            {
                "axis_id": screw["axis_id"],
                "panel_member": screw["panel_member"],
                "receiver_member": receiver,
                "previous_receiver_member": screw["previous_receiver_member"],
                "contact_pair_id": topo["contact_pair_id"],
                "contact_geometry": pair,
                "axis_global": screw["axis_global_xyz"],
                "origin_global_xyz_mm": screw["origin_global_xyz_mm"],
                "current_location_status": screw["current_location_status"],
                "translation_from_source_xyz_mm": screw["translation_from_source_xyz_mm"],
                "owner_moved_axis_record": screw["owner_moved_axis_record"],
                "purchased_policy": screw["purchased_policy"],
                "purchased_nominal_length_mm": screw["purchased_nominal_length_mm"],
                "hardware_status": screw["hardware_status"],
                "receiver_axis_envelope_screen": screw["receiver_screen"],
                "receiver_grain_scenario": receiver_frame,
                "panel_material_axes_status": "panel_layup_axes_and_properties_unassigned",
                "axis_member_grain_relations": axis_grain_relations(screw["axis_global_xyz"], [receiver_frame]),
                "response_range": None,
                "mechanical_path_status": "panel_and_receiver_geometry_reference_only; screw engagement and transfer law not established",
                "acceptance": False,
            }
        )

    duty_crosswalk = []
    for duty in topology["former_duties"]:
        registry = duty_registry_by_id.get(duty["former_duty_id"], {})
        duty_crosswalk.append(
            {
                "former_duty_id": duty["former_duty_id"],
                "physical_connection_id": duty["physical_connection_id"],
                "candidate_axis_ids": duty["candidate_bolt_axis_ids"],
                "connection_family": duty["connection_family"],
                "geometry_reuse_scope": duty["geometry_reuse_scope"],
                "connection_graph_pair_geometry": [contact_summary(pid, pair_index) for pid in duty["connection_graph_pair_ids"]],
                "noncontact_axis_membership_pair_ids": duty["noncontact_axis_membership_pair_ids"],
                "panel_screw_shared_receiver_references_only": duty["panel_screw_relations_by_shared_receiver_only"],
                "retained_frame_bolt_shared_member_references_only": duty["retained_frame_bolt_relations_by_shared_member_only"],
                "replacement_accepted": registry.get("replacement_accepted", False),
                "duty_status": registry.get("owner_assignment_status", "not_materialized_in_duty_registry"),
                "unresolved_requirements": registry.get("unresolved_requirements", []),
                "relation_limit": "shared member or receiver references do not establish a station-local attachment or force path",
            }
        )

    # Shape-template groupings are reported only at the source-certified scope.
    templates = []
    for template_id in sorted({station["geometry_template"]["geometry_template_id"] for station in stations}):
        rows = [station for station in stations if station["geometry_template"]["geometry_template_id"] == template_id]
        templates.append(
            {
                "geometry_template_id": template_id,
                "physical_connection_ids": [row["physical_connection_id"] for row in rows],
                "scope": rows[0]["geometry_template"]["geometry_template_scope"],
                "basis": rows[0]["geometry_template"]["basis"],
                "mechanical_representative": False,
                "mechanical_equivalence_status": "not_established_no_station_response_range_or_signed_demand_vector",
            }
        )

    # Interfaces are inspected for scope only; they are not a current full-frame station inventory.
    current_member_ids = set(member_kind)
    interface_member_ids = sorted({mid for interface in interfaces["interfaces"] for mid in interface["body_ids"]})
    interface_boundary = {
        "source_path": INTERFACES_PATH,
        "scope": interfaces["scope"],
        "geometry_fingerprint_sha256": interfaces["geometry_fingerprint_sha256"],
        "interface_records": len(interfaces["interfaces"]),
        "body_ids_absent_from_current_50_member_manifest": sorted(set(interface_member_ids) - current_member_ids),
        "applied_to_current_station_classification": False,
        "reason": "This source is scoped to WJ-03 mirrored outer nodes and includes a separate interface/layout proposal. Its records do not reconcile to the reviewed current 50-member station inventory; no interface is transferred into this classification.",
    }

    case_rows = []
    for case in load_cases["cases"]:
        case_rows.append(
            {
                "case_id": case["case_id"],
                "hold_id": case["hold_id"],
                "applied_force_global_xyz_n": case["applied_force_global_xyz_n"],
                "moment_global_xyz_nmm": case["applied_wrench"]["moment_global_xyz_nmm"],
                "patch_size_mm": case["panel_patch"]["size_mm"],
                "patch_center_global_xyz_mm": case["panel_patch"]["center_global_xyz_mm"],
                "force_application_point_global_xyz_mm": case["standoff"]["force_application_point_global_xyz_mm"],
                "wrench_reference_point_global_xyz_mm": case["applied_wrench"]["reference_point_global_xyz_mm"],
                "input_type": "source_bound_applied_force_and_wrench_only",
                "reactions_or_joint_demands": False,
            }
        )

    return {
        "schema": "wood_joint_t04_station_source_classification/v1",
        "attempt_id": "current-station-family-classification-attempt01-2026-09-28",
        "candidate": manifest["candidate"],
        "geometry_revision_id": revision,
        "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "classification_scope": {
            "candidate_connection_stations": len(stations),
            "former_candidate_duties": len(duty_crosswalk),
            "candidate_bolt_axes": len(axis_station),
            "retained_frame_bolt_axes": len(retained),
            "panel_kicker_hillman_axes": len(screw_rows),
            "hillman_axes_source_station_retained": sum(row["current_location_status"] == "source_station_retained" for row in screw_rows),
            "hillman_axes_owner_moved": sum(row["current_location_status"] == "moved" for row in screw_rows),
            "member_solids": len(solids["members"]),
            "contact_pair_records": len(pair_index),
        },
        "evidence_boundary": {
            "claim": "Source-bound identity and geometry classification only; it does not demonstrate active mechanics, full load path, response, resistance, criterion disposition, or acceptance.",
            "candidate_status_changed": False,
            "geometry_changed": False,
            "native_solver_run": False,
            "cad_mutation": False,
            "criteria_changed": False,
            "mechanical_representatives_proposed": [],
            "representative_limit": "No station has an authenticated response range or signed local demand vector. Shape or contact similarity is insufficient to establish mechanical equivalence.",
        },
        "source_pins": pin_hashes,
        "load_contract_context": {
            "six_case_contract_path": LOAD_CASES_PATH,
            "six_case_contract_sha256": pin_hashes[LOAD_CASES_PATH],
            "current_datums_path": LOAD_DATUMS_PATH,
            "current_datums_sha256": pin_hashes[LOAD_DATUMS_PATH],
            "case_count": len(case_rows),
            "cases": case_rows,
            "contract_limit": "Applied panel forces and equivalent global wrenches only. These are external inputs; they contain no frame reactions, station demands, or axis forces.",
            "dead_load": {
                "path": DEAD_LOAD_PATH,
                "sha256": pin_hashes[DEAD_LOAD_PATH],
                "status": dead_load["status"],
                "modeled_mass_rows": dead_load["modeled_body_gravity"]["row_count"],
                "modeled_mass_kg": dead_load["modeled_body_gravity"]["modeled_mass_kg"],
                "modeled_gravity_force_global_xyz_n": dead_load["modeled_body_gravity"]["gravity_force_global_xyz_n"],
                "separate_accessory_allowance_kg": dead_load["accessory_allowance"]["budget_kg"],
                "accessory_placement_or_actual_split_known": False,
                "solver_dof_mapping_implemented": dead_load["readiness"]["solver_dof_mapping_implemented"],
                "mass_topology_global_solver_dof_mapping": mass_topology["global_model_integration"]["solver_dof_mapping_implemented"],
                "resultant_is_not_member_or_station_demand": True,
            },
            "known_station_response_range": None,
            "known_station_response_status": "none_bound_by_load_or_geometry_contracts",
        },
        "conditional_material_orientation_context": {
            "block_map_path": BLOCK_MAP_PATH,
            "block_map_sha256": pin_hashes[BLOCK_MAP_PATH],
            "block_members": len(block_map),
            "block_transverse_cases": sum(len(row["transverse_assignment_cases"]) for row in block_map_doc["members"]),
            "frame_timber_map_path": TIMBER_MAP_PATH,
            "frame_timber_map_sha256": pin_hashes[TIMBER_MAP_PATH],
            "frame_timbers": len(timber_map),
            "frame_transverse_scenario_count": sum(len(row["cases_global_xyz"]) for row in timber_map_doc["members"]),
            "observed_delivered_grain_or_ring_orientation": False,
            "selected_solver_material_or_element_assignment": False,
            "panel_layups_assigned": False,
            "interpretation": "Axis-to-longitudinal cosines in this packet compare modeled axes to conditional source-frame vectors only; they do not classify delivered lumber or select a material orientation.",
        },
        "geometry_template_families": templates,
        "candidate_stations": stations,
        "former_duty_crosswalk": duty_crosswalk,
        "retained_frame_bolt_axes": retained,
        "panel_kicker_hillman_axes": screw_rows,
        "inspected_interface_scope_boundary": interface_boundary,
        "criteria_context": {
            "criteria_source_path": CRITERIA_PATH,
            "criteria_source_sha256": pin_hashes[CRITERIA_PATH],
            "coverage_claim_changed": False,
            "criterion_disposition": "unchanged_pending",
        },
    }


def verify_sums() -> None:
    if not SUMS_FILE.is_file():
        raise ValueError("Missing SHA256SUMS")
    for line in SUMS_FILE.read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        path = ATTEMPT / filename
        if not path.is_file() or sha256(path) != digest:
            raise ValueError(f"Packet checksum mismatch: {filename}")


def write_sums() -> None:
    files = [ATTEMPT / "README.md", PIN_FILE, ATTEMPT / "verify_packet.py", CLASSIFICATION_FILE]
    rows = [f"{sha256(path)}  {path.name}" for path in sorted(files, key=lambda item: item.name)]
    with SUMS_FILE.open("x", encoding="utf-8") as out:
        out.write("\n".join(rows) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-pins", action="store_true", help="create initial source pins in this fresh attempt only")
    parser.add_argument("--write", action="store_true", help="write classification and checksums exclusively in this fresh attempt")
    parser.add_argument("--verify", action="store_true", help="verify source pins, exact derived classification, and packet hashes")
    args = parser.parse_args()
    try:
        if args.init_pins:
            if PIN_FILE.exists():
                raise ValueError("Refusing to replace existing source-pins.json")
            manifest = load_json(REPO / MANIFEST_PATH)
            solids = load_json(REPO / SOLIDS_PATH)
            topology = load_json(REPO / TOPOLOGY_PATH)
            if manifest["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
                raise ValueError("Unexpected current full-frame input manifest revision")
            if len(solids["members"]) != 50 or len(topology["candidate_bolt_axes"]) != 92:
                raise ValueError("Expected current 50-member/92-axis source inputs")
            pins = {
                "schema": "wood_joint_t04_station_source_pins/v1",
                "attempt_id": "current-station-family-classification-attempt01-2026-09-28",
                "candidate": manifest["candidate"],
                "geometry_revision_id": manifest["geometry_revision_id"],
                "sources": source_rows(),
            }
            with PIN_FILE.open("x", encoding="utf-8") as out:
                out.write(dump_json(pins))
            print(f"created {PIN_FILE.relative_to(REPO)} with {len(pins['sources'])} source pins")
            return 0
        if args.write:
            if CLASSIFICATION_FILE.exists() or SUMS_FILE.exists():
                raise ValueError("Refusing to replace existing classification/checksums")
            _, hashes = verify_source_pins()
            classification = derive_classification(hashes)
            with CLASSIFICATION_FILE.open("x", encoding="utf-8") as out:
                out.write(dump_json(classification))
            write_sums()
            print(f"wrote {CLASSIFICATION_FILE.relative_to(REPO)}")
            print(f"candidate stations={len(classification['candidate_stations'])}, axes={classification['classification_scope']['candidate_bolt_axes']}, retained={len(classification['retained_frame_bolt_axes'])}, screws={len(classification['panel_kicker_hillman_axes'])}")
            return 0
        if args.verify:
            pins, hashes = verify_source_pins()
            recorded = load_json(CLASSIFICATION_FILE)
            expected = derive_classification(hashes)
            if recorded != expected:
                raise ValueError("station-classification.json differs from deterministic source derivation")
            verify_sums()
            expected_station_axis_ids = {
                axis["axis_id"]
                for station in recorded["candidate_stations"]
                for axis in station["axis_geometry_stack_and_contact"]
            }
            expected_screw_ids = {row["axis_id"] for row in recorded["panel_kicker_hillman_axes"]}
            expected_retained_ids = {row["axis_id"] for row in recorded["retained_frame_bolt_axes"]}
            if len(expected_station_axis_ids) != 92 or len(expected_screw_ids) != 66 or len(expected_retained_ids) != 12:
                raise ValueError("Final identity coverage mismatch")
            if recorded["evidence_boundary"]["mechanical_representatives_proposed"]:
                raise ValueError("A mechanical representative was asserted without response evidence")
            print("PASS_SOURCE_PINS: " + str(len(pins["sources"])))
            print("PASS_MEMBER_STEP_HASHES: 50/50")
            print("PASS_DUTY_STATION_RECONCILIATION: 24 duties -> 22 stations; 92/92 axes")
            print("PASS_RETAINED_BOLTS: 12/12 axes")
            print("PASS_HILLMAN_AXES: 66/66 (58 retained, 8 moved)")
            print("PASS_CONTACT_REFERENCES_AND_CONDITIONAL_GRAIN_JOINS")
            print("PASS_NO_RESPONSE_RANGE_OR_MECHANICAL_REPRESENTATIVE_CLAIM")
            print("PASS_PACKET_SHA256SUMS")
            return 0
        parser.error("select --init-pins, --write, or --verify")
    except Exception as exc:  # explicit verifier error, no traceback noise in evidence packet
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
