#!/usr/bin/env python3
"""Read-only verifier for the current-frame mesh/source audit packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[4]
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
BASE = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(path: str) -> Path:
    return ROOT / path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> None:
    pins = read_json(PACKET / "source-pins.json")
    audit = read_json(PACKET / "mesh-source-audit.json")
    require(pins["schema"] == "wood_joint_source_pins/v1", "source pin schema")
    require(audit["schema"] == "wood_joint_current_frame_mesh_source_audit/v1", "audit schema")
    require(audit["geometry_revision_id"] == REVISION_ID, "audit revision")
    require(not audit["source_pins_include_live_task_queue"], "queue must remain excluded")
    records = pins["sources"]
    require(len(records) == audit["source_pin_count"], "source pin record count")
    require(all("luna-max-task-queue" not in x["path"] for x in records), "queue path is not a source pin")
    for row in records:
        path = source(row["path"])
        require(path.is_file(), f"missing pinned source: {row['path']}")
        require(path.stat().st_size == row["size_bytes"], f"size mismatch: {row['path']}")
        require(sha256(path) == row["sha256"], f"SHA-256 mismatch: {row['path']}")

    rev = read_json(source("docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json"))
    m03 = read_json(source(str(BASE / "current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json")))
    m04 = read_json(source(str(BASE / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json")))
    bundle_path = BASE / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
    bundle = read_json(source(str(bundle_path)))
    inv = read_json(source(str(BASE / "ordinary-patch-inputs-attempt01/inventory.json")))
    mesh_path = BASE / "ordinary-port-motion-attempt09-common-map/mesh.json"
    mesh = read_json(source(str(mesh_path)))
    contract = read_json(source(str(BASE / "current-frame-adapter-attempt01/current-frame-adapter-contract.json")))
    mass = read_json(source(str(BASE / "current-mass-topology-map-attempt03/source-topology-map.json")))
    loads = read_json(source(str(BASE / "current-load-cases.json")))
    datums = read_json(source(str(BASE / "current-load-datums.json")))
    require(rev.get("revision_id") == REVISION_ID, "reviewed revision identity")
    require(all(x.get("geometry_revision_id") == REVISION_ID for x in (m03, m04, bundle, loads)), "full-frame/load revision joins")
    require(inv["candidate"]["revision_id"] == REVISION_ID, "patch input revision")
    require(mesh["current_candidate_binding"]["revision_id"] == REVISION_ID, "patch mesh revision")
    require(contract["geometry_revision_id"] == REVISION_ID, "adapter revision")
    require(mass["revision_id"] == REVISION_ID and datums["revision_id"] == REVISION_ID, "mass/datum revisions")
    require(len(loads["cases"]) == 6, "six current load cases")
    require(mass["mass_inventory_row_count"] == 778, "current mass/topology row count")

    rows04 = {x["member_id"]: x for x in m04["finished_member_step_bindings"]}
    rowsb = {x["member_id"]: x for x in bundle["members"]}
    require(len(rows04) == len(rowsb) == 50 and set(rows04) == set(rowsb), "50 full-frame member identities")
    audit_rows = {x["member_id"]: x for x in audit["identity_audit"]["current_full_frame_members"]}
    require(set(audit_rows) == set(rows04), "audit contains exact 50-member identity set")
    bundle_root = BASE / "current-full-frame-member-solids-attempt01"
    for member_id, row in rows04.items():
        other = rowsb[member_id]
        step = source(row["path"])
        replay_rel = bundle_root / other["step_file"]
        replay = source(str(replay_rel))
        require(Path(row["path"]) == replay_rel, f"STEP path join: {member_id}")
        require(row["member_kind"] == other["member_kind"], f"kind join: {member_id}")
        require(row["file_sha256"] == other["step_sha256"] == sha256(step) == sha256(replay), f"STEP digest join: {member_id}")
        require(row["size_bytes"] == step.stat().st_size == replay.stat().st_size, f"STEP size join: {member_id}")
        require(row["shape_summary_sha256"] == other["shape_summary_sha256"], f"shape summary join: {member_id}")
        require(row["source_shape_fingerprint_sha256"] == other["source_shape_fingerprint_sha256"], f"source shape join: {member_id}")
        recorded = audit_rows[member_id]
        require(recorded["path"] == row["path"] and recorded["sha256"] == row["file_sha256"], f"audit member record: {member_id}")

    require(mesh["input_bundle_inventory_sha256"] == sha256(source(str(BASE / "ordinary-patch-inputs-attempt01/inventory.json"))), "patch mesh inventory binding")
    require(len(inv["step_artifacts"]) == 27, "patch inventory source STEP count")
    for key, item in inv["step_artifacts"].items():
        step = source(str(BASE / "ordinary-patch-inputs-attempt01" / f"{key}.step"))
        require(step.is_file() and sha256(step) == item["file_sha256"], f"patch source STEP: {key}")

    bodies = mesh["bodies"]
    require(len(bodies) == 19 and mesh["body_count"] == 19, "patch mesh body count")
    all_elements: set[int] = set()
    all_nodes: set[int] = set()
    for body_id, row in bodies.items():
        elements, nodes = row["elements"], row["nodes"]
        require(len(elements) == row["element_count"], f"element IDs/count: {body_id}")
        require(len(nodes) == row["node_count"], f"node IDs/count: {body_id}")
        require(not all_elements.intersection(elements), f"duplicate global element ID: {body_id}")
        require(not all_nodes.intersection(nodes), f"duplicate global node ID: {body_id}")
        all_elements.update(elements)
        all_nodes.update(nodes)
    require(len(all_elements) == mesh["element_count"] == 57643, "global patch element total")
    require(len(all_nodes) == mesh["node_count"] == 116162, "global patch node total")
    require(sum(1 for x in bodies.values() if x["owner_kind"] == "wood_member") == 3, "patch wood body count")
    require(sum(1 for x in bodies.values() if x["owner_kind"] == "physical_metal") == 16, "patch metal body count")

    full_fingerprints = {mid: row["source_shape_fingerprint_sha256"] for mid, row in rows04.items()}
    matched = set()
    for wb in mesh["input_geometry_context"]["wood_bodies"]:
        mid, fingerprint = wb["part_id"], wb["finished_geometry"]["cad_shape_sha256"]
        require(full_fingerprints.get(mid) == fingerprint, f"patch wood shape identity: {mid}")
        matched.add(mid)
    missing = sorted(set(rows04) - matched)
    require(len(matched) == 3 and len(missing) == 47, "3 matched and 47 uncovered current members")
    require(missing == audit["identity_audit"]["full_frame_member_ids_missing_from_patch_mesh"], "missing member list")

    require(all(value is None for value in contract["solver_mappings"].values()), "full-frame solver mappings remain null")
    require(len(contract["body_bindings"]) == 50, "adapter body binding count")
    require(all(value is None for row in contract["body_bindings"] for key, value in row.items() if key.startswith("solver_")), "per-body solver mappings remain null")
    require(mesh["status"] == "VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER", "patch-only mesh provenance status")
    require(mesh["accepted"] is False and mesh["solved"] is False and mesh["native_solve_run"] is False, "patch mesh acceptance/solve flags")
    require(all(value is False for value in audit["gates"].values()), "audit gates remain false")
    old = read_json(source("fea/results/current-frame-response.json"))
    require(old.get("candidate") == "no-shoes-development" and old.get("workspace_geometry_sources_match") is False, "historical response is not this candidate")
    print(json.dumps({"status":"PASS","source_pins_verified":len(records),"current_frame_members_joined":len(rows04),"patch_input_steps_verified":len(inv["step_artifacts"]),"patch_mesh_bodies":len(bodies),"patch_mesh_elements":len(all_elements),"patch_mesh_nodes":len(all_nodes),"patch_member_matches":len(matched),"current_members_uncovered":len(missing),"full_frame_solver_mappings":"null","readiness_gates":"false"},sort_keys=True))


if __name__ == "__main__":
    main()
