#!/usr/bin/env python3
"""Build and verify the source-bound T04 duty-path identity graph.

This packet records topology identities and geometry observations only.  It
does not map any identity to solver entities or assign mechanical behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-duty-path-graph-attempt01-2026-09-28"
)
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
SCHEMA = "wood_joint_t04_current_duty_path_graph/v1"

SOURCE_SPECS: list[tuple[str, str, str]] = [
    (
        "task_queue",
        "docs/wood-joints-mvp/luna-max-task-queue.json",
        "T04 queue scope and exit-gate boundary; not a geometry source",
    ),
    (
        "duty_registry",
        "docs/wood-joints-mvp/duty-registry.json",
        "current registry of 24 former duties and open requirements",
    ),
    (
        "stale_interfaces_scope_boundary",
        "docs/wood-joints-mvp/interfaces.json",
        "known stale WJ-03 scope boundary only; excluded from graph derivation",
    ),
    (
        "current_input_manifest",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json",
        "current revision member, candidate axis, retained bolt, screw, and load identities",
    ),
    (
        "current_attachment_topology",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-attachment-topology-attempt01/attachment-topology.json",
        "duty-to-axis/member/pair and shared-reference records",
    ),
    (
        "current_attachment_topology_readme",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-attachment-topology-attempt01/README.md",
        "topology artifact scope and limits",
    ),
    (
        "current_contact_graph",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "complete-contact-graph-attempt02.json",
        "current member-pair geometry observations; no mechanics law",
    ),
    (
        "receiver_screen",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "receiver-screen-attempt04.json",
        "current panel/kicker screw receiver geometry screens",
    ),
    (
        "current_load_cases",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json",
        "six current external applied panel cases; no station demands",
    ),
    (
        "current_load_datums",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-datums.json",
        "current hold/panel target identity and coordinate data",
    ),
    (
        "current_member_solids_manifest",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json",
        "50 exact current STEP identities and shape fingerprints",
    ),
    (
        "current_mass_topology_map",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-mass-topology-map-attempt03/source-topology-map.json",
        "modeled hardware-role identities and explicit absent solver DOF mappings",
    ),
    (
        "current_dead_load_scenarios",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-frame-dead-load-scenarios-attempt01/dead-load-scenarios.json",
        "current body-gravity and accessory allowance contract; no solved response",
    ),
    (
        "hillman_mechanics_contract",
        "docs/wood-joints-mvp/wj24-panel-screw-mechanics-contract.md",
        "Hillman panel/kicker screw product and mechanics boundary",
    ),
    (
        "prior_t04_readme",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-2026-09-28/README.md",
        "reviewed source-bound station-classification packet",
    ),
    (
        "prior_t04_classification",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-2026-09-28/station-classification.json",
        "reviewed 24-duty to 22-station classification and current axis inventory",
    ),
    (
        "prior_t04_source_pins",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-2026-09-28/source-pins.json",
        "source pins supporting the reviewed T04 classification",
    ),
    (
        "prior_t04_verifier",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-2026-09-28/verify_packet.py",
        "deterministic verifier for the reviewed T04 classification",
    ),
    (
        "prior_t04_checksums",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-2026-09-28/SHA256SUMS",
        "frozen checksums for the reviewed T04 classification packet",
    ),
    (
        "prior_t04_independent_review",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-independent-review-2026-09-28/review-record.json",
        "independent confirmation with explicit scope limits",
    ),
    (
        "prior_t04_independent_review_readme",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-independent-review-2026-09-28/README.md",
        "independent review summary",
    ),
    (
        "prior_t04_independent_review_checksums",
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-independent-review-2026-09-28/SHA256SUMS",
        "frozen independent-review packet checksums",
    ),
]

UNRESOLVED = {
    "behavior": "unknown; no adopted contact, timber, or fastener response law is bound to this edge",
    "face_ownership": "unknown; source pair records contain no persistent face IDs/normals or solver-side owner mapping",
    "solver_mapping": "not implemented; CAD member/axis IDs are not solver body, element, node, or DOF identities",
    "force_transfer": "unknown; geometric adjacency, receiver membership, and source cross-reference do not establish force transfer",
    "response": "not available; no signed station actions, reactions, displacements, or response range are bound",
    "required_evidence": [
        "frozen solver body/element/node/DOF map for each current member and modeled fastener role",
        "persistent contact-face ownership plus an independently checked contact/attachment law",
        "source-supported material, grain/orientation, hardware, and complete-stack assignments",
        "validated global-to-local force-transfer map and current simultaneous station actions",
        "accepted output mapping to signed station response, with separate resistance/criterion checks",
    ],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def load_json(root: Path, rel: str) -> Any:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def root_from_script() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "current-candidate.json").is_file() and (parent / ".git").is_dir():
            return parent
    raise RuntimeError("could not locate mini-moonboard repository root")


def packet_path(root: Path, name: str) -> Path:
    return root / PACKET_REL / name


def verify_nested_checksums(root: Path, sums_rel: str, packet_dir_rel: str) -> None:
    sums_path = root / sums_rel
    packet_dir = root / packet_dir_rel
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel_name = line.split(None, 1)
        rel_name = rel_name.strip().lstrip("*")
        target = packet_dir / rel_name
        if not target.is_file() or sha256_file(target) != digest:
            raise ValueError(f"nested checksum mismatch: {sums_rel}: {rel_name}")


def source_pin_records(root: Path) -> dict[str, Any]:
    specs = list(SOURCE_SPECS)
    solids_rel = next(path for key, path, _ in specs if key == "current_member_solids_manifest")
    solids = load_json(root, solids_rel)
    solids_parent = Path(solids_rel).parent.parent
    for member in solids["members"]:
        step_rel = (solids_parent / member["step_file"]).as_posix()
        specs.append(
            (
                f"current_step:{member['member_id']}",
                step_rel,
                "exact current member STEP geometry; hash must match the solids manifest",
            )
        )

    records = []
    seen: set[str] = set()
    for key, rel, use in specs:
        if rel in seen:
            raise ValueError(f"duplicate source path in pin specification: {rel}")
        seen.add(rel)
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        records.append(
            {
                "source_key": key,
                "path": rel,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "use": use,
            }
        )

    pin_by_path = {item["path"]: item for item in records}
    for member in solids["members"]:
        step_rel = (solids_parent / member["step_file"]).as_posix()
        if pin_by_path[step_rel]["sha256"] != member["step_sha256"]:
            raise ValueError(f"member STEP hash does not match descriptor: {member['member_id']}")

    prior_dir = Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-2026-09-28"
    )
    verify_nested_checksums(
        root,
        (prior_dir / "SHA256SUMS").as_posix(),
        prior_dir.as_posix(),
    )
    review_dir = Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-station-family-classification-attempt01-independent-review-2026-09-28"
    )
    verify_nested_checksums(
        root,
        (review_dir / "SHA256SUMS").as_posix(),
        review_dir.as_posix(),
    )

    return {
        "schema": "wood_joint_t04_source_pins/v1",
        "attempt_id": PACKET_REL.name,
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": REVISION,
        "source_count": len(records),
        "current_step_count": len(solids["members"]),
        "sources": sorted(records, key=lambda x: x["path"]),
        "scope_notes": [
            "interfaces.json is pinned only as the known stale WJ-03 scope boundary; no interface records are used to construct graph edges.",
            "The prior T04 classification and its independent review are pinned as source evidence; station templates remain geometry-only.",
            "All source hashes identify repository bytes; STEP hashes also match the current member-solids descriptor.",
        ],
    }


def source_hashes(pins: dict[str, Any]) -> dict[str, str]:
    return {item["path"]: item["sha256"] for item in pins["sources"]}


def add_node(nodes: dict[str, dict[str, Any]], kind: str, node_id: str, **fields: Any) -> str:
    key = f"{kind}:{node_id}"
    if key in nodes:
        raise ValueError(f"duplicate node: {key}")
    nodes[key] = {"node_id": key, "node_type": kind, **fields}
    return key


def edge(
    source: str,
    target: str,
    relation: str,
    source_path: str,
    source_record: str,
    evidence_class: str,
    semantics: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "from": source,
        "to": target,
        "relation": relation,
        "source_path": source_path,
        "source_record": source_record,
        "evidence_class": evidence_class,
        "semantics": semantics,
        "unresolved_mechanics": dict(UNRESOLVED),
        **extra,
    }


def duty_path_graph(root: Path, pins: dict[str, Any]) -> dict[str, Any]:
    source_by_key = {item["source_key"]: item for item in pins["sources"]}
    rel = {key: value["path"] for key, value in source_by_key.items() if key in {s[0] for s in SOURCE_SPECS}}
    read = lambda key: load_json(root, rel[key])

    queue = read("task_queue")
    duty_registry = read("duty_registry")
    manifest = read("current_input_manifest")
    topology = read("current_attachment_topology")
    contact = read("current_contact_graph")
    prior = read("prior_t04_classification")
    prior_review = read("prior_t04_independent_review")
    solids = read("current_member_solids_manifest")
    loads = read("current_load_cases")
    datums = read("current_load_datums")
    mass_map = read("current_mass_topology_map")
    dead = read("current_dead_load_scenarios")

    if manifest["geometry_revision_id"] != REVISION or topology["geometry_revision_id"] != REVISION:
        raise ValueError("current geometry revision mismatch")
    if prior["geometry_revision_id"] != REVISION:
        raise ValueError("prior T04 classification revision mismatch")
    if prior_review["verdict"] != "CONFIRMED_WITH_SCOPE_LIMITS":
        raise ValueError("prior T04 independent review is not the expected confirmed-with-limits review")
    prior_retained = {item["axis_id"]: item for item in prior["retained_frame_bolt_axes"]}
    t04 = next((item for item in queue["tasks"] if item["id"] == "T04"), None)
    if not t04 or t04["state"] != "active":
        raise ValueError("T04 queue record missing or not active")

    duty_rows = duty_registry["duties"]
    duty_by_id = {item["legacy_duty_id"]: item for item in duty_rows}
    topology_duties = {item["former_duty_id"]: item for item in topology["former_duties"]}
    stations = {item["physical_connection_id"]: item for item in prior["candidate_stations"]}
    if set(duty_by_id) != set(topology_duties):
        raise ValueError("duty registry/topology former-duty IDs differ")
    if len(stations) != 22 or len(duty_by_id) != 24:
        raise ValueError("reviewed T04 station/duty counts changed")

    members = {item["member_id"]: item for item in solids["members"]}
    manifest_members = {item["member_id"]: item for item in manifest["physical_members"]}
    manifest_step_bindings = {item["member_id"]: item for item in manifest["finished_member_step_bindings"]}
    if set(members) != set(manifest_members) or set(members) != set(manifest_step_bindings) or len(members) != 50:
        raise ValueError("exact current member identity join failed")
    solids_root_rel = Path(source_by_key["current_member_solids_manifest"]["path"]).parent.parent
    for member_id, record in members.items():
        step_rel = (solids_root_rel / record["step_file"]).as_posix()
        physical_binding = manifest_members[member_id]["current_finished_step_binding"]
        finished_binding = manifest_step_bindings[member_id]
        if (
            finished_binding["member_kind"] != record["member_kind"]
            or physical_binding["path"] != step_rel
            or physical_binding["file_sha256"] != record["step_sha256"]
            or physical_binding["source_shape_fingerprint_sha256"] != record["source_shape_fingerprint_sha256"]
            or finished_binding["path"] != step_rel
            or finished_binding["file_sha256"] != record["step_sha256"]
            or finished_binding["size_bytes"] != record["step_size_bytes"]
            or finished_binding["shape_summary_sha256"] != record["shape_summary_sha256"]
            or finished_binding["source_shape_fingerprint_sha256"] != record["source_shape_fingerprint_sha256"]
        ):
            raise ValueError(f"current input manifest/member STEP binding mismatch: {member_id}")
    if len(manifest["candidate_bolt_axes"]) != 92 or len(manifest["retained_frame_bolt_axes"]) != 12:
        raise ValueError("candidate or retained axis counts changed")
    if len(manifest["panel_kicker_screw_axes"]) != 66:
        raise ValueError("Hillman axis count changed")

    contact_by_id = {"pair:" + "|".join(sorted(row["member_ids"])): row for row in contact["edges"]}
    if len(contact_by_id) != len(contact["edges"]):
        raise ValueError("duplicate unordered member-pair record in current contact graph")
    topology_pair_by_id = {item["pair_id"]: item for item in topology["contact_pair_catalog"]}
    if len(topology_pair_by_id) != 100:
        raise ValueError("current attachment topology contact catalog count changed")
    for pair_id, record in topology_pair_by_id.items():
        if pair_id not in contact_by_id:
            raise ValueError(f"topology pair missing from complete current graph: {pair_id}")
        row = contact_by_id[pair_id]
        if sorted(record["member_ids"]) != sorted(row["member_ids"]):
            raise ValueError(f"contact-pair member join mismatch: {pair_id}")
        for field in (
            "geometry_state",
            "interface_geometry_state",
            "finite_shared_planar_face_area_mm2",
            "opposed_planar_face_contact_area_mm2",
            "common_volume_mm3",
            "minimum_separation_mm",
        ):
            if record[field] != row[field]:
                raise ValueError(f"contact-pair geometry field mismatch: {pair_id}/{field}")
        current_candidate_ids = {item["axis_id"] for item in row["candidate_bolt_associations"]}
        current_screw_ids = {item["axis_id"] for item in row["current_panel_screw_associations"]}
        current_retained_ids = {item["axis_id"] for item in row["retained_frame_bolt_source_membership"]}
        if (
            set(record["candidate_bolt_axis_ids"]) != current_candidate_ids
            or set(record["panel_screw_axis_ids"]) != current_screw_ids
            or set(record["retained_frame_bolt_axis_ids"]) != current_retained_ids
        ):
            raise ValueError(f"contact-pair axis association mismatch: {pair_id}")

    axes = {item["axis_id"]: item for item in manifest["candidate_bolt_axes"]}
    axis_topology = {item["axis_id"]: item for item in topology["candidate_bolt_axes"]}
    retained = {item["axis_id"]: item for item in manifest["retained_frame_bolt_axes"]}
    retained_topology = {item["axis_id"]: item for item in topology["retained_frame_bolts"]}
    screws = {item["axis_id"]: item for item in manifest["panel_kicker_screw_axes"]}
    screw_topology = {item["axis_id"]: item for item in topology["panel_screw_axes"]}
    if set(axes) != set(axis_topology) or len(axes) != 92:
        raise ValueError("candidate axis inventory join failed")
    if set(retained) != set(retained_topology) or len(retained) != 12:
        raise ValueError("retained frame-bolt inventory join failed")
    if set(retained) != set(prior_retained):
        raise ValueError("retained frame-bolt IDs differ from reviewed T04 inventory")
    if set(screws) != set(screw_topology) or len(screws) != 66:
        raise ValueError("panel/kicker screw inventory join failed")
    for axis_id, item in axes.items():
        manifest_pairs = {
            "pair:" + "|".join(sorted(association["member_pair"]))
            for association in item["geometric_member_pair_associations"]
        }
        if manifest_pairs != set(axis_topology[axis_id]["graph_member_pair_ids"]):
            raise ValueError(f"candidate axis pair association mismatch: {axis_id}")
        if set(item["receiver_member_ids"]) != set(axis_topology[axis_id]["ordered_receiver_ids_head_to_nut"]):
            raise ValueError(f"candidate axis receiver identity mismatch: {axis_id}")
    for axis_id, item in retained.items():
        current = retained_topology[axis_id]
        manifest_pairs = {
            "pair:" + "|".join(sorted(association["member_pair"]))
            for association in item["geometric_member_pair_associations"]
        }
        if set(item["members_as_recorded"]) != set(current["source_member_ids_as_recorded"]):
            raise ValueError(f"retained arrangement member identity mismatch: {axis_id}")
        if manifest_pairs != set(current["source_member_pair_ids"]):
            raise ValueError(f"retained arrangement pair identity mismatch: {axis_id}")
    for axis_id, item in screws.items():
        current = screw_topology[axis_id]
        expected_pair = "pair:" + "|".join(sorted([item["panel_member"], item["receiver_member"]]))
        if (
            current["panel_member"] != item["panel_member"]
            or current["receiver_member"] != item["receiver_member"]
            or current["contact_pair_id"] != expected_pair
        ):
            raise ValueError(f"panel/kicker screw panel-receiver-pair identity mismatch: {axis_id}")

    mass_rows = mass_map["physical_mass_rows"]
    role_entities: dict[tuple[str, str], dict[str, Any]] = {}
    screw_mass: dict[str, dict[str, Any]] = {}
    for row in mass_rows:
        entity = row["source_mass_entity"]
        axis_id = entity.get("axis_id")
        if entity.get("kind") in {"current_candidate_hardware_component", "current_retained_frame_hardware_component"}:
            key = (axis_id, entity.get("component_role"))
            if key in role_entities:
                raise ValueError(f"duplicate modeled hardware role mass row: {key}")
            role_entities[key] = entity
        elif entity.get("kind") == "current_panel_screw_axis_envelope_proxy":
            if axis_id in screw_mass:
                raise ValueError(f"duplicate panel screw proxy row: {axis_id}")
            screw_mass[axis_id] = entity
    if len(role_entities) != 520 or len(screw_mass) != 66:
        raise ValueError("modeled hardware role / screw proxy source counts changed")
    for axis_id in axes:
        if {role for aid, role in role_entities if aid == axis_id} != {"head", "head_washer", "nut", "nut_washer", "shaft"}:
            raise ValueError(f"candidate hardware role set incomplete: {axis_id}")
    for axis_id in retained:
        if {role for aid, role in role_entities if aid == axis_id} != {"head", "head_washer", "nut", "nut_washer", "shaft"}:
            raise ValueError(f"retained hardware role set incomplete: {axis_id}")

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    member_node: dict[str, str] = {}
    pair_node: dict[str, str] = {}
    duty_node: dict[str, str] = {}
    station_node: dict[str, str] = {}
    axis_node: dict[str, str] = {}
    retained_node: dict[str, str] = {}
    screw_node: dict[str, str] = {}

    hashes = source_hashes(pins)
    source_path = {key: value["path"] for key, value in source_by_key.items()}

    for member_id, record in sorted(members.items()):
        descriptor_path = record["step_file"]
        pin_path = (Path(source_path["current_member_solids_manifest"]).parent.parent / descriptor_path).as_posix()
        node = add_node(
            nodes,
            "member",
            member_id,
            member_kind=record["member_kind"],
            current_step_path=pin_path,
            current_step_sha256=record["step_sha256"],
            source_shape_fingerprint_sha256=record["source_shape_fingerprint_sha256"],
            step_size_bytes=record["step_size_bytes"],
            current_finished_step_identity_exact=True,
            delivered_stock_or_cut_observed=False,
            source_path=source_path["current_member_solids_manifest"],
            unresolved_mechanics=dict(UNRESOLVED),
        )
        member_node[member_id] = node

    # Historical-only receiver names are preserved as references, never promoted
    # to current STEP members or current graph contact surfaces.
    historical_member_node: dict[str, str] = {}

    for station_id, item in sorted(stations.items()):
        station_node[station_id] = add_node(
            nodes,
            "station",
            station_id,
            former_duty_ids=item["former_duty_ids"],
            candidate_axis_ids=item["candidate_axis_ids"],
            timber_member_ids=item["timber_member_ids"],
            candidate_block_member_ids=item["candidate_block_member_ids"],
            panel_member_ids_in_connection_scope=item["panel_member_ids_in_connection_scope"],
            station_class=item["station_class"],
            geometry_template=item["geometry_template"],
            conditional_member_grain_frames=item["conditional_member_grain_frames"],
            mechanical_path_status=item["mechanical_path_status"],
            known_response_range=item["known_response_range"],
            accepted=item["acceptance"],
            missing_evidence=item["missing_evidence"],
            source_path=source_path["prior_t04_classification"],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    for duty_id, registry in sorted(duty_by_id.items()):
        current = topology_duties[duty_id]
        duty_node[duty_id] = add_node(
            nodes,
            "former_duty",
            duty_id,
            registry_family=registry.get("legacy_family"),
            registry_host_members=registry.get("legacy_host_members", []),
            registry_legacy_axis_ids=registry.get("legacy_sds_axis_ids", []),
            registry_interface_ids=registry.get("interface_ids", []),
            owner_assignment_status=registry.get("owner_assignment_status"),
            proposed_topology=registry.get("proposed_topology"),
            replacement_accepted=registry.get("replacement_accepted", False),
            current_physical_connection_id=current["physical_connection_id"],
            current_candidate_axis_ids=current["candidate_bolt_axis_ids"],
            current_member_ids=current["member_ids"],
            current_geometry_pair_ids=current["connection_graph_pair_ids"],
            replacement_status=current["replacement_status"],
            geometry_reuse_scope=current["geometry_reuse_scope"],
            registry_unresolved_requirements=registry.get("unresolved_requirements", []),
            source_paths=[source_path["duty_registry"], source_path["current_attachment_topology"]],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    # Collect every pair referenced by the current 100-row topology catalog and
    # by any duty/axis/screw/retained record, then bind it to the full graph row.
    pair_ids = set(topology_pair_by_id)
    for duty in topology["former_duties"]:
        pair_ids.update(duty["connection_graph_pair_ids"])
        pair_ids.update(duty["candidate_axis_associated_graph_pair_ids"])
        pair_ids.update(item["contact_pair_id"] for item in duty["additional_nonfastener_contact_pairs"])
        pair_ids.update(item["contact_pair_id"] for item in duty["panel_screw_relations_by_shared_receiver_only"])
        pair_ids.update(
            pair_id
            for item in duty["retained_frame_bolt_relations_by_shared_member_only"]
            for pair_id in item["source_member_pair_ids"]
        )
    for item in topology["candidate_bolt_axes"]:
        pair_ids.update(item["graph_member_pair_ids"])
    for item in topology["panel_screw_axes"]:
        pair_ids.add(item["contact_pair_id"])
    for item in topology["retained_frame_bolts"]:
        pair_ids.update(item["source_member_pair_ids"])
    for pair_id in sorted(pair_ids):
        row = contact_by_id.get(pair_id)
        if row is None:
            raise ValueError(f"referenced pair missing from full current graph: {pair_id}")
        pair_node[pair_id] = add_node(
            nodes,
            "member_pair_geometry",
            pair_id,
            member_ids=row["member_ids"],
            geometry_state=row["geometry_state"],
            interface_geometry_state=row["interface_geometry_state"],
            finite_shared_planar_face_area_mm2=row["finite_shared_planar_face_area_mm2"],
            opposed_planar_face_contact_area_mm2=row["opposed_planar_face_contact_area_mm2"],
            cooriented_planar_face_contact_area_mm2=row["cooriented_planar_face_contact_area_mm2"],
            common_volume_mm3=row["common_volume_mm3"],
            minimum_separation_mm=row["minimum_separation_mm"],
            contact_measurement_basis=row["contact_measurement_basis"],
            candidate_bolt_axis_associations=row["candidate_bolt_associations"],
            panel_screw_axis_associations=row["current_panel_screw_associations"],
            retained_frame_bolt_membership=row["retained_frame_bolt_source_membership"],
            source_path=source_path["current_contact_graph"],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    role_node: dict[tuple[str, str], str] = {}
    for (axis_id, component_role), entity in sorted(role_entities.items()):
        role_id = entity["id"]
        role_node[(axis_id, component_role)] = add_node(
            nodes,
            "modeled_hardware_role",
            role_id,
            axis_id=axis_id,
            component_role=component_role,
            source_entity_kind=entity["kind"],
            source_geometry_kind=entity["source_geometry_kind"],
            current_graph_member_references=entity["current_graph_member_references"],
            reference_basis=entity["reference_basis"],
            solver_dof_id=entity["solver_dof_id"],
            solver_dof_mapping_status=entity["solver_dof_mapping_status"],
            source_path=source_path["current_mass_topology_map"],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    for axis_id, item in sorted(axes.items()):
        geometry = item["geometry"]
        axis_node[axis_id] = add_node(
            nodes,
            "candidate_bolt_axis",
            axis_id,
            family=item["family"],
            station_id=item["station_id"],
            trial_id=item["trial_id"],
            receiver_member_ids=item["receiver_member_ids"],
            axis_head_to_nut_global=geometry["axis_head_to_nut_global"],
            shaft_center_global_xyz_mm=geometry["shaft_center_global_xyz_mm"],
            modeled_shaft_diameter_mm=geometry["modeled_shaft_diameter_mm"],
            modeled_shaft_occupied_length_mm=geometry["modeled_shaft_occupied_length_mm"],
            wood_grip_material_length_mm=geometry["wood_grip_material_length_mm"],
            modeled_receiver_order_head_to_nut=axis_topology[axis_id]["ordered_receiver_ids_head_to_nut"],
            receiver_intervals=geometry["wood_receiver_intervals"],
            member_order_limit=item["member_order_limit"],
            hardware_status=item["hardware_status"],
            length_status=item["length_status"],
            modeled_component_role_ids=item["scene_modeled_component_role_ids"],
            physical_head_to_nut_order_established=False,
            current_mechanical_response=None,
            source_paths=[source_path["current_input_manifest"], source_path["current_attachment_topology"]],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    for axis_id, item in sorted(retained.items()):
        retained_node[axis_id] = add_node(
            nodes,
            "retained_frame_bolt_arrangement",
            axis_id,
            members_as_recorded=item["members_as_recorded"],
            associated_pair_ids=retained_topology[axis_id]["source_member_pair_ids"],
            axis_global=item["axis_global_xyz"],
            origin_global_xyz_mm=item["origin_global_xyz_mm"],
            source_grip_mm=item["source_grip_mm"],
            source_nominal_length_mm=item["source_nominal_length_mm"],
            source_occupied_diameter_mm=item["source_occupied_diameter_mm"],
            source_occupied_length_mm=item["source_occupied_length_mm"],
            physical_head_to_nut_order_established=False,
            candidate_recheck_status=item["candidate_recheck_status"],
            hardware_status=item["hardware_status"],
            known_response_range=prior_retained[axis_id]["known_response_range"],
            source_paths=[source_path["current_input_manifest"], source_path["current_attachment_topology"], source_path["prior_t04_classification"]],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    for axis_id, item in sorted(screws.items()):
        screw_node[axis_id] = add_node(
            nodes,
            "hillman_panel_kicker_axis",
            axis_id,
            panel_member=item["panel_member"],
            current_receiver_member=item["receiver_member"],
            previous_receiver_member=item["previous_receiver_member"],
            current_location_status=item["current_location_status"],
            axis_global=item["axis_global_xyz"],
            origin_global_xyz_mm=item["origin_global_xyz_mm"],
            translation_from_source_xyz_mm=item["translation_from_source_xyz_mm"],
            purchased_policy=item["purchased_policy"],
            purchased_nominal_length_mm=item["purchased_nominal_length_mm"],
            receiver_screen=item["receiver_screen"],
            owner_moved_axis_record=item["owner_moved_axis_record"],
            contact_pair_id=screw_topology[axis_id]["contact_pair_id"],
            current_screw_engagement_or_resistance=None,
            source_mass_proxy_entity_id=screw_mass[axis_id]["id"],
            source_mass_proxy_geometry_kind=screw_mass[axis_id]["source_geometry_kind"],
            source_paths=[source_path["current_input_manifest"], source_path["current_attachment_topology"], source_path["current_mass_topology_map"]],
            unresolved_mechanics=dict(UNRESOLVED),
        )

    # Graph edges: all have an explicit source basis and identical unresolved
    # mechanics fields. A relation expresses record identity, never force path.
    for station_id, item in sorted(stations.items()):
        for duty_id in item["former_duty_ids"]:
            edges.append(edge(
                station_node[station_id], duty_node[duty_id], "station_lists_former_duty",
                source_path["prior_t04_classification"], f"candidate_stations[{station_id}].former_duty_ids",
                "source_bound_reviewed_inventory_identity", "reviewed station membership only",
            ))
        for axis_id in item["candidate_axis_ids"]:
            edges.append(edge(
                station_node[station_id], axis_node[axis_id], "station_lists_candidate_axis",
                source_path["prior_t04_classification"], f"candidate_stations[{station_id}].candidate_axis_ids",
                "source_bound_reviewed_inventory_identity", "axis count/identity membership only",
            ))
        for member_id in item["timber_member_ids"] + item["candidate_block_member_ids"]:
            if member_id not in member_node:
                raise ValueError(f"station member has no current STEP identity: {member_id}")
            edges.append(edge(
                station_node[station_id], member_node[member_id], "station_lists_member",
                source_path["prior_t04_classification"], f"candidate_stations[{station_id}].timber/candidate_block_member_ids",
                "source_bound_reviewed_inventory_identity", "station scope membership only",
            ))

    for duty_id, current in sorted(topology_duties.items()):
        duty = duty_node[duty_id]
        station = station_node.get(current["physical_connection_id"])
        if station is None:
            raise ValueError(f"current duty connection missing reviewed station: {duty_id}")
        edges.append(edge(
            duty, station, "former_duty_maps_to_physical_station",
            source_path["current_attachment_topology"], f"former_duties[{duty_id}].physical_connection_id",
            "source_bound_topology_identity", "current duty-to-station crosswalk only",
        ))
        for axis_id in current["candidate_bolt_axis_ids"]:
            edges.append(edge(
                duty, axis_node[axis_id], "former_duty_lists_candidate_axis",
                source_path["current_attachment_topology"], f"former_duties[{duty_id}].candidate_bolt_axis_ids",
                "source_bound_topology_identity", "former-duty axis assignment only",
            ))
        for member_id in current["member_ids"]:
            if member_id not in member_node:
                raise ValueError(f"current duty member lacks current STEP identity: {duty_id}/{member_id}")
            edges.append(edge(
                duty, member_node[member_id], "former_duty_lists_current_member",
                source_path["current_attachment_topology"], f"former_duties[{duty_id}].member_ids",
                "source_bound_topology_identity", "current member scope only",
            ))
        for pair_id in current["connection_graph_pair_ids"]:
            edges.append(edge(
                duty, pair_node[pair_id], "former_duty_lists_geometry_pair",
                source_path["current_attachment_topology"], f"former_duties[{duty_id}].connection_graph_pair_ids",
                "source_bound_pair_reference", "member-pair geometry observation only",
            ))
        for extra_pair in current["additional_nonfastener_contact_pairs"]:
            pair_id = extra_pair["contact_pair_id"]
            edges.append(edge(
                duty, pair_node[pair_id], "former_duty_lists_additional_nonfastener_pair",
                source_path["current_attachment_topology"], f"former_duties[{duty_id}].additional_nonfastener_contact_pairs",
                "source_bound_pair_reference", "nonfastener geometry reference; active bearing not inferred",
                recorded_basis=extra_pair["source_basis"],
            ))
        for ref in current["panel_screw_relations_by_shared_receiver_only"]:
            edges.append(edge(
                duty, screw_node[ref["axis_id"]], "duty_shared_receiver_screw_reference_only",
                source_path["current_attachment_topology"], f"former_duties[{duty_id}].panel_screw_relations_by_shared_receiver_only",
                "source_bound_shared_receiver_reference", "shared receiver reference only; not station-local attachment",
                shared_contact_pair_id=ref["contact_pair_id"],
                relation_limit=ref["relation"],
            ))
        for ref in current["retained_frame_bolt_relations_by_shared_member_only"]:
            edges.append(edge(
                duty, retained_node[ref["axis_id"]], "duty_shared_member_retained_bolt_reference_only",
                source_path["current_attachment_topology"], f"former_duties[{duty_id}].retained_frame_bolt_relations_by_shared_member_only",
                "source_bound_shared_member_reference", "shared member reference only; not station-local attachment",
                shared_member_ids_only=ref["shared_member_ids_only"],
                source_member_pair_ids=ref["source_member_pair_ids"],
            ))

        registry = duty_by_id[duty_id]
        for member_id in registry.get("legacy_host_members", []):
            if member_id in member_node:
                target = member_node[member_id]
                evidence_class = "source_bound_historical_duty_member_identity"
            else:
                if member_id not in historical_member_node:
                    historical_member_node[member_id] = add_node(
                        nodes, "historical_member_reference", member_id,
                        current_step_identity_present=False,
                        source_path=source_path["duty_registry"],
                        unresolved_mechanics=dict(UNRESOLVED),
                    )
                target = historical_member_node[member_id]
                evidence_class = "source_bound_historical_duty_member_identity"
            edges.append(edge(
                duty, target, "former_duty_registry_lists_legacy_host",
                source_path["duty_registry"], f"duties[{duty_id}].legacy_host_members",
                evidence_class, "legacy host record only; not a current attachment statement",
            ))

    for axis_id, item in sorted(axes.items()):
        node = axis_node[axis_id]
        geometry = item["geometry"]
        interval_ids = {interval["receiver_id"] for interval in geometry["wood_receiver_intervals"]}
        if interval_ids != set(item["receiver_member_ids"]):
            raise ValueError(f"candidate receiver list does not match raw receiver intervals: {axis_id}")
        for member_id in item["receiver_member_ids"]:
            edges.append(edge(
                node, member_node[member_id], "candidate_axis_has_modeled_receiver_interval",
                source_path["current_input_manifest"], f"candidate_bolt_axes[{axis_id}].geometry.wood_receiver_intervals",
                "source_bound_raw_receiver_axis_geometry", "modeled shaft/receiver interval membership; physical stack and bearing unknown",
                receiver_order_head_to_nut=axis_topology[axis_id]["ordered_receiver_ids_head_to_nut"],
                physical_stack_order_established=False,
            ))
        for pair_id in axis_topology[axis_id]["graph_member_pair_ids"]:
            edges.append(edge(
                node, pair_node[pair_id], "candidate_axis_associated_member_pair",
                source_path["current_attachment_topology"], f"candidate_bolt_axes[{axis_id}].graph_member_pair_ids",
                "source_bound_axis_pair_geometry_association", "bore receiver pair association only; pair contact state is read separately",
            ))
        for role in ("head", "head_washer", "nut", "nut_washer", "shaft"):
            target = role_node[(axis_id, role)]
            edges.append(edge(
                node, target, "candidate_axis_has_modeled_hardware_role",
                source_path["current_mass_topology_map"], f"physical_mass_rows[axis_id={axis_id},role={role}].source_mass_entity",
                "source_bound_modeled_role_identity", "CAD/mass role identity only; no product, contact, or connector law",
            ))

    for axis_id, item in sorted(retained.items()):
        node = retained_node[axis_id]
        source_members = retained_topology[axis_id]["source_member_ids_as_recorded"]
        for member_id in source_members:
            edges.append(edge(
                node, member_node[member_id], "retained_bolt_record_lists_member",
                source_path["current_attachment_topology"], f"retained_frame_bolts[{axis_id}].source_member_ids_as_recorded",
                "source_bound_retained_arrangement_identity", "retained source stack member record only; current candidate recheck remains open",
                physical_head_to_nut_order_established=False,
            ))
        for pair_id in retained_topology[axis_id]["source_member_pair_ids"]:
            edges.append(edge(
                node, pair_node[pair_id], "retained_bolt_record_lists_member_pair",
                source_path["current_attachment_topology"], f"retained_frame_bolts[{axis_id}].source_member_pair_ids",
                "source_bound_retained_pair_reference", "member-pair geometry only; retained-bolt force transfer unknown",
            ))
        for role in ("head", "head_washer", "nut", "nut_washer", "shaft"):
            edges.append(edge(
                node, role_node[(axis_id, role)], "retained_bolt_has_modeled_hardware_role",
                source_path["current_mass_topology_map"], f"physical_mass_rows[axis_id={axis_id},role={role}].source_mass_entity",
                "source_bound_modeled_role_identity", "CAD/mass role identity only; no delivered product or connector law",
            ))

    for axis_id, item in sorted(screws.items()):
        node = screw_node[axis_id]
        topo_item = screw_topology[axis_id]
        for relation, member_id, basis in [
            ("panel_axis_targets_panel_member", item["panel_member"], "current panel screw map names panel member"),
            ("panel_axis_names_current_receiver_member", item["receiver_member"], "current panel screw map names receiver member"),
        ]:
            edges.append(edge(
                node, member_node[member_id], relation,
                source_path["current_input_manifest"], f"panel_kicker_screw_axes[{axis_id}].panel_member/receiver_member",
                "source_bound_panel_screw_receiver_identity", basis,
            ))
        pair_id = topo_item["contact_pair_id"]
        edges.append(edge(
            node, pair_node[pair_id], "panel_axis_associated_panel_receiver_pair",
            source_path["current_attachment_topology"], f"panel_screw_axes[{axis_id}].contact_pair_id",
            "source_bound_screw_pair_geometry_association", "current panel/receiver pair geometry only; screw engagement and transfer unknown",
        ))
        previous = item["previous_receiver_member"]
        if previous != item["receiver_member"]:
            if previous not in member_node:
                if previous not in historical_member_node:
                    historical_member_node[previous] = add_node(
                        nodes, "historical_member_reference", previous,
                        current_step_identity_present=False,
                        source_path=source_path["current_input_manifest"],
                        unresolved_mechanics=dict(UNRESOLVED),
                    )
                previous_node = historical_member_node[previous]
            else:
                previous_node = member_node[previous]
            edges.append(edge(
                node, previous_node, "panel_axis_records_previous_receiver",
                source_path["current_input_manifest"], f"panel_kicker_screw_axes[{axis_id}].previous_receiver_member",
                "source_bound_historical_receiver_reference", "previous receiver only; not part of current 50-member geometry when absent",
            ))

    for pair_id, pair_key in sorted(pair_node.items()):
        for member_id in contact_by_id[pair_id]["member_ids"]:
            edges.append(edge(
                pair_key, member_node[member_id], "member_pair_record_has_member_endpoint",
                source_path["current_contact_graph"], f"edges[member_pair={pair_id}].member_ids",
                "source_bound_current_pair_endpoint", "unordered member-pair endpoint only; face ownership and active contact unknown",
            ))

    # Current external load contract: source identity reaches the panel patch
    # target only. No edge is created to a duty or station demand.
    datum_holds = datums["holds"]
    load_nodes: dict[str, str] = {}
    for case in loads["cases"]:
        case_id = case["case_id"]
        hold_id = case["hold_id"]
        panel_id = datum_holds[hold_id]["panel_id"]
        if panel_id not in member_node:
            raise ValueError(f"load target panel has no current STEP member: {case_id}")
        load_nodes[case_id] = add_node(
            nodes,
            "external_applied_load_case",
            case_id,
            hold_id=hold_id,
            target_panel_member=panel_id,
            applied_force_global_xyz_n=case["applied_force_global_xyz_n"],
            applied_moment_global_xyz_nmm=case["applied_wrench"]["moment_global_xyz_nmm"],
            patch=case["panel_patch"],
            standoff=case["standoff"],
            source_path=source_path["current_load_cases"],
            response=None,
            unresolved_mechanics=dict(UNRESOLVED),
        )
        edges.append(edge(
            load_nodes[case_id], member_node[panel_id], "external_case_applied_at_hold_panel_patch",
            source_path["current_load_cases"], f"cases[{case_id}].panel_patch/hold_id",
            "source_bound_external_load_target", "prescribed external panel target identity only; no global-to-station transfer or response",
            target_datum_source_path=source_path["current_load_datums"],
        ))

    dead_node = add_node(
        nodes,
        "modeled_dead_load_contract",
        dead["revision_id"],
        physical_mass_row_count=mass_map["mass_inventory_row_count"],
        unique_source_mass_entity_count=mass_map["unique_source_mass_entity_count"],
        modeled_mass_kg=dead["planning_totals"]["modeled_mass_kg"],
        separate_accessory_allowance=dead["accessory_allowance"],
        solver_dof_mapping_implemented=mass_map["global_model_integration"]["solver_dof_mapping_implemented"],
        source_paths=[source_path["current_dead_load_scenarios"], source_path["current_mass_topology_map"]],
        unresolved_mechanics=dict(UNRESOLVED),
    )

    # Stable de-duplication and identifiers.
    edge_map: dict[bytes, dict[str, Any]] = {}
    for item in edges:
        key = canonical_json(item)
        edge_map[key] = item
    stable_edges = []
    for item in sorted(edge_map.values(), key=lambda x: (x["from"], x["to"], x["relation"], x["source_path"], x["source_record"])):
        edge_id = "edge:" + sha256_bytes(canonical_json(item))[:20]
        stable_edges.append({"edge_id": edge_id, **item})

    def find_edge_id(source: str, target: str, relation: str) -> str | None:
        for item in stable_edges:
            if item["from"] == source and item["to"] == target and item["relation"] == relation:
                return item["edge_id"]
        return None

    center_routes = []
    for side in ("left", "right"):
        panel = f"kicker_{side}"
        post = f"base_post_center_{side}"
        cleat = f"center_post_cleat_{side}"
        header = "base_header"
        screw_ids = sorted(
            axis_id for axis_id, item in screws.items()
            if item["panel_member"] == panel and item["receiver_member"] == post
        )
        post_axis_ids = sorted(
            axis_id for axis_id, item in axes.items()
            if set(item["receiver_member_ids"]) == {post, cleat}
        )
        header_axis_ids = sorted(
            axis_id for axis_id, item in axes.items()
            if set(item["receiver_member_ids"]) == {header, cleat}
        )
        if len(screw_ids) != 2 or len(post_axis_ids) != 2 or len(header_axis_ids) != 2:
            raise ValueError(f"center-kicker identity route coverage mismatch: {side}")
        path_edge_ids = []
        for axis_id in screw_ids:
            path_edge_ids.extend([
                find_edge_id(screw_node[axis_id], member_node[panel], "panel_axis_targets_panel_member"),
                find_edge_id(screw_node[axis_id], member_node[post], "panel_axis_names_current_receiver_member"),
                find_edge_id(screw_node[axis_id], pair_node[screw_topology[axis_id]["contact_pair_id"]], "panel_axis_associated_panel_receiver_pair"),
            ])
        for axis_id in post_axis_ids + header_axis_ids:
            path_edge_ids.extend(
                find_edge_id(axis_node[axis_id], member_node[member_id], "candidate_axis_has_modeled_receiver_interval")
                for member_id in axes[axis_id]["receiver_member_ids"]
            )
            path_edge_ids.extend(
                find_edge_id(axis_node[axis_id], pair_node[pair_id], "candidate_axis_associated_member_pair")
                for pair_id in axis_topology[axis_id]["graph_member_pair_ids"]
            )
        if any(value is None for value in path_edge_ids):
            raise ValueError(f"center-kicker route edge reference missing: {side}")
        prior_receivers = sorted({screws[axis_id]["previous_receiver_member"] for axis_id in screw_ids})
        center_routes.append(
            {
                "side": side,
                "status": "identity_chain_only_not_an_established_mechanical_path",
                "current_topology_sequence": [panel, *screw_ids, post, *post_axis_ids, cleat, *header_axis_ids, header],
                "hillman_axis_ids_currently_receiving_in_center_post": screw_ids,
                "previous_receiver_member_ids_historical_only": prior_receivers,
                "previous_receivers_have_current_step_identity": {name: name in member_node for name in prior_receivers},
                "center_post_candidate_bolt_axis_ids": post_axis_ids,
                "header_candidate_bolt_axis_ids": header_axis_ids,
                "contact_pair_ids": sorted(
                    {screw_topology[axis_id]["contact_pair_id"] for axis_id in screw_ids}
                    | {pair_id for axis_id in post_axis_ids + header_axis_ids for pair_id in axis_topology[axis_id]["graph_member_pair_ids"]}
                ),
                "supporting_edge_ids": sorted(set(path_edge_ids)),
                "interpretation_limit": "source-bound panel/receiver and candidate-axis identities are shown; face ownership, active contact, complete force transfer, solver mapping, and response remain unknown",
                "required_next_evidence": list(UNRESOLVED["required_evidence"]),
            }
        )

    contacts_state_counts: dict[str, int] = {}
    for pair_id in pair_node:
        state = contact_by_id[pair_id]["geometry_state"]
        contacts_state_counts[state] = contacts_state_counts.get(state, 0) + 1
    moved_screws = sorted(axis_id for axis_id, item in screws.items() if item["current_location_status"] != "source_station_retained")
    role_status_counts: dict[str, int] = {}
    for _, entity in role_entities.items():
        status = entity["solver_dof_mapping_status"]
        role_status_counts[status] = role_status_counts.get(status, 0) + 1

    return {
        "schema": SCHEMA,
        "attempt_id": PACKET_REL.name,
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": REVISION,
        "classification": "source-bound topology/identity graph; not a mechanical path model",
        "source_pin_file_sha256": sha256_file(packet_path(root, "source-pins.json")),
        "source_hashes_by_path": hashes,
        "source_derived_facts": {
            "queue_T04_state": t04["state"],
            "former_duty_count": len(duty_by_id),
            "reviewed_physical_station_count": len(stations),
            "candidate_bolt_axis_count": len(axes),
            "retained_frame_bolt_arrangement_count": len(retained),
            "Hillman_panel_kicker_axis_count": len(screws),
            "Hillman_axis_status_counts": {
                "source_station_retained": sum(item["current_location_status"] == "source_station_retained" for item in screws.values()),
                "owner_moved": sum(item["current_location_status"] != "source_station_retained" for item in screws.values()),
            },
            "current_member_count": len(members),
            "current_step_member_count": len(solids["members"]),
            "relevant_member_pair_count": len(pair_node),
            "relevant_pair_geometry_state_counts": dict(sorted(contacts_state_counts.items())),
            "modeled_candidate_and_retained_hardware_roles": len(role_entities),
            "hardware_role_solver_dof_mapping_status_counts": dict(sorted(role_status_counts.items())),
            "six_external_load_cases": [case["case_id"] for case in loads["cases"]],
            "modeled_dead_load_rows": mass_map["mass_inventory_row_count"],
            "modeled_dead_load_mass_kg": dead["planning_totals"]["modeled_mass_kg"],
            "separate_accessory_allowance": dead["accessory_allowance"],
            "prior_independent_review_verdict": prior_review["verdict"],
        },
        "source_derived_vs_unknown": {
            "source_derived": [
                "Current member IDs, member kinds, and exact attempt01 STEP paths/SHA-256 values joined to the attempt04 manifest.",
                "Current manifest identities for 92 modeled candidate bolt axes, 12 retained frame-bolt arrangements, and 66 Hillman panel/kicker axes.",
                "Current duty registry and attachment-topology identity crosswalk for 24 former duties and 22 reviewed physical stations.",
                "Current member-pair geometry state and geometric areas for referenced pair IDs in the full current contact graph.",
                "Current screw panel/receiver assignments, move status, prior receiver reference, and receiver-screen flags.",
                "Modeled bolt/washer/nut/shaft role names and mass-topology references; their solver DOF mappings are explicitly null/not implemented.",
                "Six prescribed external hold-panel load input identities and current body-gravity input contract metadata.",
            ],
            "unknown_or_unestablished": [
                "Physical wood, cuts, drilled holes, installed hardware, and face ownership.",
                "Selected grain/ring orientation and solver material/element axes for individual members.",
                "Active contact/bearing state, contact law, fastener engagement, preload, connector law, or force sharing.",
                "Physical head-to-nut order for candidate and retained bolt stacks.",
                "Global solver body/element/node/DOF map and global-to-station action transfer.",
                "Signed station actions, reactions, displacements, response ranges, resistances, or acceptance.",
                "Mechanical equivalence or representative response law among any stations.",
            ],
        },
        "stale_interface_scope_boundary": {
            "path": source_path["stale_interfaces_scope_boundary"],
            "sha256": hashes[source_path["stale_interfaces_scope_boundary"]],
            "use": "pinned as prior known stale WJ-03 scope boundary only; no interface records contribute to this graph",
            "prior_independent_review_boundary": prior_review["interface_scope_boundary"],
        },
        "nodes": sorted(nodes.values(), key=lambda x: x["node_id"]),
        "edges": stable_edges,
        "center_kicker_routes": center_routes,
        "coverage_and_status": {
            "former_duties_all_present": sorted(duty_node),
            "candidate_bolt_axes_all_present": sorted(axis_node),
            "retained_frame_bolt_arrangements_all_present": sorted(retained_node),
            "Hillman_panel_kicker_axes_all_present": sorted(screw_node),
            "panel_receivers_all_present": sorted({item["panel_member"] for item in screws.values()}),
            "current_receivers_all_present": sorted({item["receiver_member"] for item in screws.values()}),
            "moved_hillman_axes": moved_screws,
            "current_contact_pair_nodes": sorted(pair_node),
            "all_edges_mark_behavior_face_ownership_solver_mapping_force_transfer_response": all(
                set(UNRESOLVED).issubset(item["unresolved_mechanics"]) for item in stable_edges
            ),
        },
        "model_change_assessment": {
            "required_changes_to_current_geometry_or_axes_from_this_inventory": [],
            "changes_made": [],
            "status": "none indicated by this identity/topology-only packet",
            "before_mechanics": [
                "Parent/coordinator must freeze and assign a solver mapping for all 50 member STEP identities and modeled hardware roles.",
                "Resolve persistent face ownership, current contact/fastener behavior, hardware/material/grain assignments, and complete-stack semantics.",
                "Connect validated applied loads and dead load to the global model, then establish simultaneous signed station actions before any response or resistance comparison.",
                "Review any required geometry/model changes against the frozen candidate and owner constraints before changing it.",
            ],
        },
        "prohibited_inferences": [
            "CAD adjacency or opposed planar touch is not a contact capacity, stiffness, or force path.",
            "A bore/receiver interval or modeled component role is not physical bolt stack order, engagement, or connector response.",
            "A Hillman axis assignment is not installed screw engagement or resistance and does not inherit SPAX data.",
            "A shared member or shared receiver reference is not a station-local connection.",
            "A geometric station template is not a mechanical representative family.",
        ],
        "counts": {
            "nodes_by_type": {kind: sum(item["node_type"] == kind for item in nodes.values()) for kind in sorted({item["node_type"] for item in nodes.values()})},
            "edges": len(stable_edges),
            "center_kicker_routes": len(center_routes),
        },
    }


def checksum_payload(root: Path, names: list[str]) -> str:
    return "".join(f"{sha256_file(packet_path(root, name))}  {name}\n" for name in names)


def verify(root: Path) -> dict[str, Any]:
    pins_path = packet_path(root, "source-pins.json")
    graph_path = packet_path(root, "duty-path-graph.json")
    pins = json.loads(pins_path.read_text(encoding="utf-8"))
    freshly_built = source_pin_records(root)
    if canonical_json(pins) != canonical_json(freshly_built):
        raise ValueError("source-pins.json does not match exact current source bytes/manifest")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    expected_graph = duty_path_graph(root, pins)
    if canonical_json(graph) != canonical_json(expected_graph):
        raise ValueError("duty-path-graph.json does not match deterministic reconstruction")
    node_ids = {item["node_id"] for item in graph["nodes"]}
    if len(node_ids) != len(graph["nodes"]):
        raise ValueError("duplicate graph node IDs")
    edge_ids = {item["edge_id"] for item in graph["edges"]}
    if len(edge_ids) != len(graph["edges"]):
        raise ValueError("duplicate graph edge IDs")
    if any(item["from"] not in node_ids or item["to"] not in node_ids for item in graph["edges"]):
        raise ValueError("dangling graph edge")
    pinned_paths = {item["path"] for item in pins["sources"]}
    for item in graph["nodes"]:
        if item.get("source_path") is not None and item["source_path"] not in pinned_paths:
            raise ValueError(f"node cites an unpinned source path: {item['node_id']}")
        if any(path not in pinned_paths for path in item.get("source_paths", [])):
            raise ValueError(f"node cites an unpinned source path: {item['node_id']}")
    for item in graph["edges"]:
        if item["source_path"] not in pinned_paths:
            raise ValueError(f"edge cites an unpinned source path: {item['edge_id']}")
        if item.get("target_datum_source_path") is not None and item["target_datum_source_path"] not in pinned_paths:
            raise ValueError(f"edge cites an unpinned datum source path: {item['edge_id']}")
        if set(UNRESOLVED) != set(item["unresolved_mechanics"]):
            raise ValueError(f"edge unresolved field set changed: {item['edge_id']}")
    if any(set(UNRESOLVED) != set(item.get("unresolved_mechanics", {})) for item in graph["nodes"]):
        raise ValueError("at least one node omits a required unresolved mechanics field")
    if not graph["coverage_and_status"]["all_edges_mark_behavior_face_ownership_solver_mapping_force_transfer_response"]:
        raise ValueError("at least one edge omits a required unresolved mechanics field")
    sums_path = packet_path(root, "SHA256SUMS")
    expected_names = ["README.md", "source-pins.json", "duty-path-graph.json", "verify_packet.py"]
    expected_sums = checksum_payload(root, expected_names)
    if sums_path.read_text(encoding="utf-8") != expected_sums:
        raise ValueError("SHA256SUMS mismatch or file list changed")
    return {
        "result": "PASS",
        "source_pins": len(pins["sources"]),
        "current_step_hashes": pins["current_step_count"],
        "duties": graph["source_derived_facts"]["former_duty_count"],
        "stations": graph["source_derived_facts"]["reviewed_physical_station_count"],
        "candidate_axes": graph["source_derived_facts"]["candidate_bolt_axis_count"],
        "retained_bolts": graph["source_derived_facts"]["retained_frame_bolt_arrangement_count"],
        "hillman_axes": graph["source_derived_facts"]["Hillman_panel_kicker_axis_count"],
        "members": graph["source_derived_facts"]["current_member_count"],
        "pair_nodes": graph["source_derived_facts"]["relevant_member_pair_count"],
        "edge_count": graph["counts"]["edges"],
        "center_routes": graph["counts"]["center_kicker_routes"],
        "checksum_file_count": len(expected_names),
    }


def freeze(root: Path) -> dict[str, Any]:
    packet = root / PACKET_REL
    packet.mkdir(parents=True, exist_ok=True)
    pins = source_pin_records(root)
    (packet / "source-pins.json").write_bytes(canonical_json(pins))
    graph = duty_path_graph(root, pins)
    (packet / "duty-path-graph.json").write_bytes(canonical_json(graph))
    readme = f"""# Current duty-path topology graph — attempt 01

This append-only T04 packet records source-bound member, contact-pair, and fastener-axis identities for `{REVISION}`. It is a topology inventory, not a qualified mechanical path model. The T04 queue remains active and its path/equivalence exit gate remains open.

The deterministic graph covers **24 former duties, 22 reviewed physical stations, 92 candidate bolt axes, 12 retained frame-bolt arrangements, 66 Hillman panel/kicker axes, 50 current member STEP identities, {len(graph['nodes'])} graph nodes, {len(graph['edges'])} graph edges, and both center-kicker routes**. It includes `{len(graph['source_hashes_by_path'])}` source pins, including all 50 current STEP files. See `source-pins.json` for the exact paths, byte counts, and hashes; `duty-path-graph.json` contains the complete machine-readable crosswalk.

## What the sources establish

- The current duty registry and attachment topology identify all 24 former duties and connect them to 22 source-reviewed physical station identities. The two outer-side chains each serve two former duties; that shared topology remains one chain and is not represented as two independent patches.
- The current manifest and topology identify the 92 candidate bolt axes, their modeled raw-wood receiver intervals, the 12 retained bolt arrangements and their recorded members, and the 66 Hillman axes with current panel/receiver assignments. The source inventory records 58 retained Hillman axes and 8 owner-moved axes.
- The current STEP bundle supplies exact identities for 50 members. Referenced pair records are joined to the complete current member-pair geometry graph. Finite opposed planar touch, separated geometry, and reported areas remain CAD geometry observations only.
- The two center-kicker records show the current Hillman axes at `kicker_left/right` to `base_post_center_left/right`, followed by candidate center-post bolt identities to the center-post cleat and candidate header bolt identities to `base_header`. The two previous inner-kicker backer receiver member names (used by four axes) are historical references absent from the current 50-member STEP set.
- Six external load cases identify their hold-panel targets. The dead-load contract and current mass topology map provide modeled input identities. Neither source supplies a current station response or a solver DOF assignment.

## What remains unknown

Every graph edge carries explicit unknowns for behavior, face ownership, solver mapping, force transfer, and response. The graph does not establish active contact, face normals/ownership, connection stiffness/capacity, bolt or screw engagement, physical head-to-nut order, selected grain orientation, station demands, reactions, response ranges, or mechanical equivalence. Modeled hardware role rows have no solver DOF mapping; no graph edge means force can pass between its endpoints.

`interfaces.json` is pinned only as the known stale WJ-03 scope boundary from the prior T04 packet. Its interface records were excluded from graph derivation. The prior station-family classification and independent review are pinned; their geometry-only groupings are not elevated into representative mechanical families here.

## Model changes and next executable action

This inventory identifies **no required geometry or axis change**, and makes none. Before mechanics work, the coordinator must map the frozen 50 member STEP identities and modeled hardware roles into the chosen solver, assign persistent contact/face ownership and material/grain/hardware behavior, and validate how the six load contracts and dead load reach signed station actions. Any changed model is a separate reviewed input and requires a fresh pin set; no solver run is performed by this packet.

Run from this directory:

```sh
python3 verify_packet.py --verify
sha256sum -c SHA256SUMS
```

The verifier reconstructs the graph from its pinned sources and rejects changed inputs, missing axes/pairs, dangling edges, or checksum drift. Packet verification checks bytes and identity joins; it does not validate a mechanical model.
"""
    (packet / "README.md").write_text(readme, encoding="utf-8")
    names = ["README.md", "source-pins.json", "duty-path-graph.json", "verify_packet.py"]
    (packet / "SHA256SUMS").write_text(checksum_payload(root, names), encoding="utf-8")
    return verify(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true", help="write this new append-only packet")
    mode.add_argument("--verify", action="store_true", help="verify pins, deterministic graph, and checksums")
    args = parser.parse_args()
    root = root_from_script()
    try:
        result = freeze(root) if args.freeze else verify(root)
    except Exception as exc:  # report one concise fail-closed diagnostic
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
