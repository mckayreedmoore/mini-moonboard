#!/usr/bin/env python3
"""Read-only, independent hash and arithmetic checks for the T09 review packet."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from fea.wood_joint_current_frame_adapter import (  # noqa: E402
    ATTEMPT_REL,
    _blocker_category,
    audit_current_frame,
)


ATTEMPT = ROOT / ATTEMPT_REL


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _close(a: float, b: float, *, tolerance: float = 1e-7) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tolerance, abs_tol=tolerance)


def _same_vector(a: list[float], b: list[float]) -> bool:
    return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b, strict=True))


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def main() -> int:
    terminal_path = ATTEMPT / "terminal-hashes.json"
    terminal = json.loads(terminal_path.read_text(encoding="utf-8"))
    terminal_checks = []
    for entry in terminal["artifacts"]:
        path = ROOT / entry["path"]
        observed = _sha(path)
        size = path.stat().st_size
        _check(observed == entry["sha256"], f"terminal hash mismatch: {entry['path']}")
        _check(size == entry["size_bytes"], f"terminal size mismatch: {entry['path']}")
        terminal_checks.append(
            {
                "path": entry["path"],
                "sha256": observed,
                "size_bytes": size,
                "status": "PASS",
            }
        )

    pins = json.loads((ATTEMPT / "source-pins.json").read_text(encoding="utf-8"))
    pin_checks = []
    for entry in pins["pinned_inputs"]:
        path = ROOT / entry["path"]
        observed = _sha(path)
        _check(observed == entry["sha256"], f"source pin mismatch: {entry['id']}")
        pin_checks.append(
            {
                "id": entry["id"],
                "path": entry["path"],
                "expected_sha256": entry["sha256"],
                "observed_sha256": observed,
                "status": "PASS",
            }
        )

    frozen_audit_path = ATTEMPT / "adapter-audit.json"
    frozen_contract_path = ATTEMPT / "current-frame-adapter-contract.json"
    frozen_audit = json.loads(frozen_audit_path.read_text(encoding="utf-8"))
    auth_map = frozen_audit["source_authentication"]["sha256_by_path"]
    _check(len(auth_map) == 81, "source authentication map must contain 81 paths")
    auth_checks = []
    for relative_path, expected in sorted(auth_map.items()):
        path = ROOT / relative_path
        observed = _sha(path)
        _check(observed == expected, f"authenticated source hash mismatch: {relative_path}")
        auth_checks.append(
            {"path": relative_path, "sha256": observed, "status": "PASS"}
        )

    fresh_audit, fresh_contract = audit_current_frame(ROOT, pins)
    audit_bytes_match = _canonical_json(fresh_audit) == frozen_audit_path.read_bytes()
    contract_bytes_match = (
        _canonical_json(fresh_contract) == frozen_contract_path.read_bytes()
    )
    _check(audit_bytes_match, "fresh deterministic audit differs from frozen bytes")
    _check(contract_bytes_match, "fresh deterministic contract differs from frozen bytes")

    attempt04_path = pins["pinned_inputs"][3]["path"]
    attempt04 = json.loads((ROOT / attempt04_path).read_text(encoding="utf-8"))
    bundle_path = pins["pinned_inputs"][6]["path"]
    bundle = json.loads((ROOT / bundle_path).read_text(encoding="utf-8"))
    source_bindings = {
        row["member_id"]: row for row in attempt04["finished_member_step_bindings"]
    }
    bundle_members = {row["member_id"]: row for row in bundle["members"]}
    body_ids = set(source_bindings)
    _check(len(body_ids) == len(bundle_members) == 50, "STEP member count mismatch")
    _check(body_ids == set(bundle_members), "STEP source/bundle ID sets differ")
    step_kind_counts = dict(Counter(row["member_kind"] for row in source_bindings.values()))
    _check(
        step_kind_counts == {"timber": 20, "plywood_panel": 6, "candidate_block": 24},
        "STEP body kind counts mismatch",
    )

    frozen_contract = json.loads(frozen_contract_path.read_text(encoding="utf-8"))
    _check(len(frozen_contract["body_bindings"]) == 50, "body binding count mismatch")
    _check(
        {row["source_member_id"] for row in frozen_contract["body_bindings"]}
        == body_ids,
        "adapter body IDs differ from the pinned STEP body IDs",
    )
    for row in frozen_contract["body_bindings"]:
        _check(
            all(
                row[field] is None
                for field in (
                    "solver_body_id",
                    "solver_element_ids",
                    "solver_node_ids",
                    "solver_dof_ids",
                    "solver_material_id",
                )
            ),
            f"unexpected solver or material mapping on {row['source_member_id']}",
        )

    mass_map_path = pins["pinned_inputs"][7]["path"]
    mass_map = json.loads((ROOT / mass_map_path).read_text(encoding="utf-8"))
    centroid_path = pins["pinned_inputs"][8]["path"]
    centroids = json.loads((ROOT / centroid_path).read_text(encoding="utf-8"))
    mass_rows = mass_map["physical_mass_rows"]
    centroid_by_name = {row["name"]: row for row in centroids["rows"]}
    mass_names = [row["inventory_name"] for row in mass_rows]
    entity_ids = [row["source_mass_entity"]["id"] for row in mass_rows]
    mass_kind_counts = dict(
        Counter(row["source_mass_entity"]["kind"] for row in mass_rows)
    )
    _check(len(mass_rows) == 778, "mass row count mismatch")
    _check(len(set(mass_names)) == 778, "duplicate mass inventory names")
    _check(set(mass_names) == set(centroid_by_name), "mass/centroid name sets differ")
    _check(len(set(entity_ids)) == 778, "duplicate source mass entity IDs")
    _check(
        mass_kind_counts
        == {
            "current_candidate_hardware_component": 460,
            "current_physical_tnut_component": 142,
            "current_panel_screw_axis_envelope_proxy": 66,
            "current_retained_frame_hardware_component": 60,
            "current_physical_member_solid": 50,
        },
        "mass source role counts mismatch",
    )

    total_mass = 0.0
    weighted_center = [0.0, 0.0, 0.0]
    total_force = [0.0, 0.0, 0.0]
    total_moment = [0.0, 0.0, 0.0]
    for row in mass_rows:
        entity = row["source_mass_entity"]
        graph_refs = entity.get("current_graph_member_references", [])
        _check(bool(graph_refs), f"mass role has no graph reference: {entity['id']}")
        _check(set(graph_refs) <= body_ids, f"unknown graph reference: {entity['id']}")
        name = row["inventory_name"]
        centroid = centroid_by_name[name]
        _check(row["group"] == centroid["group"], f"mass group mismatch: {name}")
        _check(_close(row["mass_kg"], centroid["mass_kg"]), f"mass mismatch: {name}")
        _check(
            _same_vector(
                row["mass_center_global_xyz_mm"],
                centroid["mass_center_global_xyz_mm"],
            ),
            f"center mismatch: {name}",
        )
        mass = float(row["mass_kg"])
        center = [float(value) for value in row["mass_center_global_xyz_mm"]]
        force = [float(value) for value in row["gravity_force_global_xyz_n"]]
        moment = [
            float(value)
            for value in row["gravity_moment_about_global_origin_nmm"]
        ]
        _check(_same_vector(force, [0.0, 0.0, -mass * 9.80665]), f"gravity mismatch: {name}")
        _check(_same_vector(moment, _cross(center, force)), f"moment mismatch: {name}")
        total_mass += mass
        for index in range(3):
            weighted_center[index] += mass * center[index]
            total_force[index] += force[index]
            total_moment[index] += moment[index]

    resultant_center = [value / total_mass for value in weighted_center]
    for source in (mass_map, centroids):
        _check(_close(total_mass, source["modeled_mass_kg"]), "aggregate mass mismatch")
        _check(
            _same_vector(resultant_center, source["modeled_mass_center_global_xyz_mm"]),
            "aggregate mass center mismatch",
        )
        _check(
            _same_vector(total_force, source["gravity_force_global_xyz_n"]),
            "aggregate gravity mismatch",
        )
        _check(
            _same_vector(total_moment, source["gravity_moment_about_global_origin_nmm"]),
            "aggregate origin moment mismatch",
        )
    equipment = mass_map["equipment_allowance"]
    _check(equipment["included_in_mass_rows"] is False, "equipment allowance included")
    _check(_close(equipment["mass_kg"], 25.0), "separate 25 kg allowance mismatch")

    mass_bindings = frozen_contract["mass_bindings"]
    _check(len(mass_bindings) == 778, "mass binding count mismatch")
    for row in mass_bindings:
        _check(
            row["mass_transfer_status"] == "not_implemented"
            and all(
                row[field] is None
                for field in (
                    "solver_body_id",
                    "solver_element_ids",
                    "solver_dof_id",
                    "solver_mass_set_id",
                )
            ),
            f"unexpected mass solver assignment: {row['source_mass_entity_id']}",
        )

    loads = json.loads((ROOT / pins["pinned_inputs"][9]["path"]).read_text(encoding="utf-8"))
    datums = json.loads((ROOT / pins["pinned_inputs"][10]["path"]).read_text(encoding="utf-8"))
    expected_case_ids = [
        "a12-rear",
        "a12-forward",
        "a12-left",
        "k12-right",
        "k12-rear",
        "a1-rear",
    ]
    _check([row["case_id"] for row in loads["cases"]] == expected_case_ids, "load case IDs mismatch")
    _check([row["case_id"] for row in frozen_contract["load_cases"]] == expected_case_ids, "adapter load case IDs mismatch")
    normal = loads["current_geometry_inputs"]["panel_outward_normal_global_xyz"]
    for source, adapted in zip(loads["cases"], frozen_contract["load_cases"], strict=True):
        datum = datums["holds"][source["hold_id"]]
        face = datum["face_datum_global_mm"]
        midplane = datum["panel_midplane_reference_global_mm"]
        _check(source["panel_patch"]["center_global_xyz_mm"] == face, "hold face/patch mismatch")
        _check(source["panel_midplane_applicationpoint_global_xyz_mm"] == midplane, "panel datum mismatch")
        _check(source["applied_wrench"]["reference_point_global_xyz_mm"] == midplane, "wrench reference mismatch")
        _check(source["standoff"]["direction_global_xyz"] == normal == datum["outward_normal_global"], "standoff normal mismatch")
        point = [face[i] + normal[i] * source["standoff"]["distance_mm"] for i in range(3)]
        _check(_same_vector(point, source["standoff"]["force_application_point_global_xyz_mm"]), "standoff point mismatch")
        force = source["applied_force_global_xyz_n"]
        expected_force = [
            *source["case_inputs"]["horizontal_force_global_xy_n"],
            loads["load_basis"]["vertical_force_global_z_n"],
        ]
        _check(_same_vector(force, expected_force), "frozen force components mismatch")
        moment = _cross([point[i] - midplane[i] for i in range(3)], force)
        _check(_same_vector(moment, source["moment_about_panel_midplane_applicationpoint_global_xyz_nmm"]), "panel midpoint moment mismatch")
        _check(_same_vector(moment, source["applied_wrench"]["moment_global_xyz_nmm"]), "wrench moment mismatch")
        _check(adapted["hold_id"] == source["hold_id"], "adapter hold binding mismatch")
        _check(adapted["panel_body_source_id"] == datum["panel_id"], "adapter panel binding mismatch")
        _check(adapted["panel_body_source_id"] in body_ids, "unknown panel body mapping")
        _check(source_bindings[adapted["panel_body_source_id"]]["member_kind"] == "plywood_panel", "load target is not a panel")
        _check(
            all(
                adapted[field] is None
                for field in (
                    "solver_load_id",
                    "solver_target_set_id",
                    "solver_patch_element_ids",
                )
            ),
            f"solver load target assigned for {source['case_id']}",
        )

    _check(all(value is None for value in frozen_contract["solver_mappings"].values()), "global solver mapping is assigned")
    _check(all(value is None for value in frozen_contract["material_assignments"].values()), "material mapping is assigned")
    _check(frozen_contract["support_mapping"]["solver_boundary_condition_ids"] is None, "support BC mapping is assigned")
    _check(frozen_contract["support_mapping"]["solver_contact_ids"] is None, "support contact mapping is assigned")

    unresolved = attempt04["readiness"]["unresolved_inputs"]
    readiness = frozen_audit["readiness"]
    _check(len(unresolved) == len(readiness["blockers"]) == 9, "blocker count mismatch")
    expected_blockers = [
        {
            "category": _blocker_category(detail),
            "source": "current-full-frame-input-manifest-attempt04",
            "detail": detail,
        }
        for detail in unresolved
    ]
    _check(readiness["blockers"] == expected_blockers, "source blockers not preserved")
    _check(readiness["inputs_ready"] is False, "inputs_ready is not false")
    _check(
        all(value is False for value in readiness.values() if isinstance(value, bool)),
        "a readiness or release flag is true",
    )
    _check(all(value is False for value in attempt04["release"].values()), "upstream release flag is true")

    report = {
        "schema": "current_frame_adapter_independent_review_verification/v1",
        "candidate_packet": ATTEMPT_REL.as_posix(),
        "terminal_manifest_sha256": _sha(terminal_path),
        "terminal_hash_checks": terminal_checks,
        "source_pin_checks": pin_checks,
        "source_authentication_checks": auth_checks,
        "deterministic_output_reproduction": {
            "audit_byte_identical": audit_bytes_match,
            "contract_byte_identical": contract_bytes_match,
        },
        "identity_joins": {
            "step_body_count": len(body_ids),
            "step_kind_counts": step_kind_counts,
            "mass_inventory_count": len(mass_rows),
            "mass_unique_entity_count": len(set(entity_ids)),
            "mass_kind_counts": mass_kind_counts,
            "mass_graph_references_all_join_to_step_bodies": True,
        },
        "mass_resultants": {
            "mass_kg": total_mass,
            "center_global_xyz_mm": resultant_center,
            "gravity_force_global_xyz_n": total_force,
            "origin_moment_global_xyz_nmm": total_moment,
            "equipment_allowance_kg_excluded": equipment["mass_kg"],
        },
        "load_datum_bindings": {
            "case_ids": expected_case_ids,
            "datum_ids": sorted(datums["holds"]),
            "standoff_and_wrench_checks": "PASS",
            "solver_targets_null": True,
        },
        "readiness": {
            "blocker_count": len(readiness["blockers"]),
            "source_blocker_details_preserved": True,
            "inputs_ready": readiness["inputs_ready"],
            "all_boolean_readiness_and_release_gates_false": True,
        },
        "result": "PASS",
    }
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
