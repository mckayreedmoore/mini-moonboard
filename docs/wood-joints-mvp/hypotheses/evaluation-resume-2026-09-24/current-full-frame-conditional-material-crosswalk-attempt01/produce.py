#!/usr/bin/env python3
"""Build or verify a source-bound, pre-mesh conditional material crosswalk."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


ATTEMPT_ID = "current-full-frame-conditional-material-crosswalk-attempt01"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
REL = Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24")
OUTPUT = REL / ATTEMPT_ID / "conditional-material-assignment-crosswalk.json"

MANIFEST = REL / "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
GEOMETRY = REL / "current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
TIMBER_MAP = REL / "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
TIMBER_TRANSVERSE = REL / "current-frame-timber-transverse-scenarios-attempt01/transverse-scenarios.json"
BLOCK_MAP = REL / "current-block-material-frame-map-attempt02/material-frame-map.json"
COVERAGE = REL / "current-frame-material-frame-coverage-attempt03/coverage.json"
COVERAGE_PINS = REL / "current-frame-material-frame-coverage-attempt03/source-pins.json"
DEAD_LOADS = REL / "current-frame-dead-load-scenarios-attempt01/dead-load-scenarios.json"
STEEL_MAP = REL / "current-steel-elastic-role-map-attempt01/steel-elastic-role-map.json"
MATERIAL_BRIEF = Path("docs/wood-joints-mvp/current-material-scenarios.md")
WOOD_SCENARIO_SOURCE = Path("docs/wood-joints-mvp/orthotropic-material-scenario.md")
WOOD_SCENARIO_HELPER = Path("fea/wood_joint_patch_materials.py")
REVISION_SOURCE = Path("docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json")

PINNED_SOURCE_PATHS = (
    Path("current-candidate.json"),
    Path("wood-joints-candidate.json"),
    REVISION_SOURCE,
    MATERIAL_BRIEF,
    WOOD_SCENARIO_SOURCE,
    WOOD_SCENARIO_HELPER,
    MANIFEST,
    REL / "current-full-frame-input-manifest-attempt04/produce.py",
    GEOMETRY,
    TIMBER_MAP,
    REL / "current-frame-timber-material-frame-map-attempt01/produce.py",
    TIMBER_TRANSVERSE,
    REL / "current-frame-timber-transverse-scenarios-attempt01/produce.py",
    BLOCK_MAP,
    REL / "current-block-material-frame-map-attempt02/produce.py",
    COVERAGE,
    COVERAGE_PINS,
    DEAD_LOADS,
    STEEL_MAP,
)


def repo_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "wood-joints-candidate.json").is_file():
            return candidate
    raise RuntimeError("Could not locate repository root")


ROOT = repo_root()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def record_digest(value: dict[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return sha256_bytes(canonical_bytes(payload))


def row_digest(value: dict[str, Any]) -> str:
    return sha256_bytes(canonical_bytes(value))


def read_json(relative_path: Path) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {relative_path}")
    return value


def close_vec(left: list[float], right: list[float], tolerance: float = 1e-8) -> bool:
    return len(left) == len(right) == 3 and all(
        math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tolerance)
        for a, b in zip(left, right, strict=True)
    )


def dot(left: list[float], right: list[float]) -> float:
    return math.fsum(float(a) * float(b) for a, b in zip(left, right, strict=True))


def norm(vector: list[float]) -> float:
    return math.sqrt(dot(vector, vector))


def cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def validate_axes(axes: dict[str, list[float]], context: str) -> None:
    if set(axes) != {"L", "R", "T"}:
        raise ValueError(f"{context}: expected L/R/T material axes")
    for axis_name, vector in axes.items():
        if len(vector) != 3 or not all(math.isfinite(float(value)) for value in vector):
            raise ValueError(f"{context}: invalid {axis_name} vector")
        if not math.isclose(norm(vector), 1.0, rel_tol=0.0, abs_tol=1e-8):
            raise ValueError(f"{context}: {axis_name} is not a unit vector")
    if any(abs(dot(axes[left], axes[right])) > 1e-8 for left, right in (("L", "R"), ("L", "T"), ("R", "T"))):
        raise ValueError(f"{context}: axes are not orthogonal")
    if not close_vec(cross(axes["L"], axes["R"]), axes["T"], 1e-8):
        raise ValueError(f"{context}: axes are not right handed")


def source_pins(manifest: dict[str, Any]) -> dict[str, str]:
    paths = set(PINNED_SOURCE_PATHS)
    for binding in manifest["finished_member_step_bindings"]:
        paths.add(Path(binding["path"]))
    result: dict[str, str] = {}
    for relative_path in sorted(paths, key=lambda path: path.as_posix()):
        path = ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(relative_path)
        result[relative_path.as_posix()] = sha256_file(path)
    return result


def build_crosswalk() -> dict[str, Any]:
    selected_authority = read_json(Path("current-candidate.json"))
    development_authority = read_json(Path("wood-joints-candidate.json"))
    revision = read_json(REVISION_SOURCE)
    manifest = read_json(MANIFEST)
    geometry = read_json(GEOMETRY)
    timber_map = read_json(TIMBER_MAP)
    timber_transverse = read_json(TIMBER_TRANSVERSE)
    block_map = read_json(BLOCK_MAP)
    coverage = read_json(COVERAGE)
    dead_loads = read_json(DEAD_LOADS)
    steel_map = read_json(STEEL_MAP)

    if selected_authority.get("candidate") != "compact-floor-flush-development":
        raise ValueError("Selected authority changed")
    if development_authority.get("candidate") != CANDIDATE:
        raise ValueError("Development candidate identity changed")
    if development_authority.get("current_development_revision", {}).get("revision_id") != REVISION:
        raise ValueError("Development candidate revision identity changed")
    if revision.get("revision_id") != REVISION:
        raise ValueError("Revision source identity changed")
    if (
        manifest.get("candidate") != CANDIDATE
        or manifest.get("geometry_revision_id") != REVISION
        or manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04"
    ):
        raise ValueError("Attempt04 manifest identity changed")
    if (
        coverage.get("candidate") != CANDIDATE
        or coverage.get("geometry_revision_id") != REVISION
        or coverage.get("attempt_id") != "current-frame-material-frame-coverage-attempt03"
    ):
        raise ValueError("Attempt03 coverage identity changed")
    if timber_map.get("candidate") != CANDIDATE or timber_map.get("geometry_revision_id") != REVISION:
        raise ValueError("Timber material-frame map identity changed")
    if timber_transverse.get("candidate") != CANDIDATE or timber_transverse.get("geometry_revision_id") != REVISION:
        raise ValueError("Timber transverse scenario identity changed")
    if block_map.get("candidate") != CANDIDATE or block_map.get("geometry_revision_id") != REVISION:
        raise ValueError("Connector-block material-frame map identity changed")
    if dead_loads.get("candidate") != CANDIDATE or dead_loads.get("revision_id") != REVISION:
        raise ValueError("Dead-load scenario identity changed")

    # Reconcile the sources against the explicit hashes that attempt04 froze.
    for evidence_key, relative_path, source_record, digest_field in (
        (
            "finished_member_geometry",
            GEOMETRY,
            geometry,
            "artifact_sha256",
        ),
        (
            "conditional_frame_timber_orientation",
            TIMBER_MAP,
            timber_map,
            "record_sha256",
        ),
        (
            "conditional_connector_block_orientation",
            BLOCK_MAP,
            block_map,
            "record_sha256",
        ),
    ):
        evidence = manifest["evidence_bindings"][evidence_key]
        if evidence["path"] != relative_path.as_posix():
            raise ValueError(f"Attempt04 evidence path drift for {evidence_key}")
        if sha256_file(ROOT / relative_path) != evidence["file_sha256"]:
            raise ValueError(f"Attempt04 evidence file hash mismatch for {evidence_key}")
        if source_record[digest_field] != evidence["content_digest"]:
            raise ValueError(f"Attempt04 evidence content digest mismatch for {evidence_key}")
    transverse_pin_path = (REL / "current-frame-timber-transverse-scenarios-attempt01/transverse-scenarios.json").as_posix()
    if manifest["attempt04_input_source_pins"].get(transverse_pin_path) != sha256_file(ROOT / TIMBER_TRANSVERSE):
        raise ValueError("Attempt04 source pin does not match current timber transverse scenarios")
    if coverage["source_scope"]["attempt04_manifest_path"] != MANIFEST.as_posix():
        raise ValueError("Attempt03 coverage points to a different attempt04 manifest")
    if coverage["source_scope"]["attempt04_manifest_sha256"] != sha256_file(ROOT / MANIFEST):
        raise ValueError("Attempt03 coverage attempt04 file hash mismatch")

    physical = {row["member_id"]: row for row in manifest["physical_members"]}
    step_bindings = {row["member_id"]: row for row in manifest["finished_member_step_bindings"]}
    coverage_rows = {row["member_id"]: row for row in coverage["members"]}
    timber_rows = {row["member_id"]: row for row in timber_map["members"]}
    transverse_rows = {row["member_id"]: row for row in timber_transverse["members"]}
    block_rows = {row["part_id"]: row for row in block_map["members"]}
    block_manifest_rows = {row["part_id"]: row for row in manifest["candidate_blocks"]}
    geometry_rows = {row["member_id"]: row for row in geometry["members"]}

    exact_ids = set(physical)
    if len(exact_ids) != 50 or set(step_bindings) != exact_ids or set(coverage_rows) != exact_ids:
        raise ValueError("Attempt04, STEP binding, and attempt03 coverage IDs do not reconcile")
    if set(timber_rows) != set(transverse_rows):
        raise ValueError("Timber orientation and transverse maps do not reconcile")
    if set(timber_rows) != {member_id for member_id, row in step_bindings.items() if row["member_kind"] == "timber"}:
        raise ValueError("Exact frame-timber map IDs do not reconcile")
    if set(block_rows) != {member_id for member_id, row in step_bindings.items() if row["member_kind"] == "candidate_block"}:
        raise ValueError("Exact connector-block map IDs do not reconcile")
    if set(block_manifest_rows) != set(block_rows):
        raise ValueError("Candidate-block manifest records do not reconcile")
    if set(geometry_rows) != exact_ids:
        raise ValueError("Finished STEP bundle descriptor IDs do not reconcile")

    for member_id in exact_ids:
        physical_row = physical[member_id]
        binding = step_bindings[member_id]
        old_coverage_row = coverage_rows[member_id]
        geometry_row = geometry_rows[member_id]
        if binding["member_kind"] != geometry_row["member_kind"]:
            raise ValueError(f"STEP descriptor kind mismatch for {member_id}")
        physical_binding = physical_row["current_finished_step_binding"]
        if (
            physical_binding["path"] != binding["path"]
            or physical_binding["file_sha256"] != binding["file_sha256"]
            or physical_binding["source_shape_fingerprint_sha256"] != binding["source_shape_fingerprint_sha256"]
        ):
            raise ValueError(f"Attempt04 STEP identity mismatch for {member_id}")
        if (
            Path(binding["path"]).name != Path(geometry_row["step_file"]).name
            or geometry_row["step_sha256"] != binding["file_sha256"]
            or geometry_row["step_size_bytes"] != binding["size_bytes"]
            or geometry_row["shape_summary_sha256"] != binding["shape_summary_sha256"]
            or geometry_row["source_shape_fingerprint_sha256"] != binding["source_shape_fingerprint_sha256"]
        ):
            raise ValueError(f"STEP descriptor mismatch for {member_id}")
        if old_coverage_row["current_step"]["path"] != binding["path"] or old_coverage_row["current_step"]["sha256"] != binding["file_sha256"]:
            raise ValueError(f"Attempt03 coverage STEP mismatch for {member_id}")
        actual_file = ROOT / binding["path"]
        if not actual_file.is_file() or sha256_file(actual_file) != binding["file_sha256"]:
            raise ValueError(f"Current STEP file hash mismatch for {member_id}")

    member_rows: list[dict[str, Any]] = []
    material_case_count = 0
    for member_id in sorted(exact_ids):
        physical_row = physical[member_id]
        binding = step_bindings[member_id]
        old_coverage_row = coverage_rows[member_id]
        kind = binding["member_kind"]
        row: dict[str, Any] = {
            "member_id": member_id,
            "member_kind": kind,
            "current_geometry_binding": {
                "step_path": binding["path"],
                "step_sha256": binding["file_sha256"],
                "step_size_bytes": binding["size_bytes"],
                "shape_summary_sha256": binding["shape_summary_sha256"],
                "source_shape_fingerprint_sha256": binding["source_shape_fingerprint_sha256"],
                "one_solid_valid_roundtrip": binding["one_solid_valid_roundtrip"],
                "source_bounds_and_volume_match": binding["source_bounds_and_volume_match"],
            },
            "solver_assignment": {
                "material_id": None,
                "body_id": None,
                "element_ids": None,
                "node_ids": None,
                "dof_ids": None,
                "status": "unresolved_no_solver_mesh_or_assignment",
            },
            "attempt03_coverage_join": {
                "coverage_class": old_coverage_row["coverage_class"],
                "coverage_row_sha256": row_digest(old_coverage_row),
                "step_identity_matches_attempt04": True,
                "prior_material_id": old_coverage_row["material_assignment"]["material_id"],
                "prior_solver_mapping": old_coverage_row["solver_mapping"],
            },
        }

        if kind == "timber":
            orientation_row = timber_rows[member_id]
            transverse_row = transverse_rows[member_id]
            if (
                orientation_row["current_geometry_lineage"]["step_file"] != binding["path"]
                or orientation_row["current_geometry_lineage"]["step_sha256"] != binding["file_sha256"]
                or orientation_row["current_geometry_lineage"]["source_shape_fingerprint_sha256"] != binding["source_shape_fingerprint_sha256"]
                or transverse_row["step_file"] != binding["path"]
                or transverse_row["step_sha256"] != binding["file_sha256"]
                or transverse_row["source_shape_fingerprint_sha256"] != binding["source_shape_fingerprint_sha256"]
            ):
                raise ValueError(f"Timber per-member STEP binding mismatch for {member_id}")
            grain = orientation_row["conditional_grain_assignment"]["proposed_global_xyz"]
            if transverse_row["source_longitudinal_global_xyz"] is None or abs(dot(grain, transverse_row["source_longitudinal_global_xyz"])) < 1.0 - 1e-8:
                raise ValueError(f"Timber map and transverse map grain directions differ for {member_id}")
            cases = []
            for case_name in ("A", "B"):
                axes = transverse_row["cases_global_xyz"][case_name]
                validate_axes(axes, f"{member_id} case {case_name}")
                if abs(dot(grain, axes["L"])) < 1.0 - 1e-8:
                    raise ValueError(f"Timber material L axis differs from conditional grain for {member_id}/{case_name}")
                cases.append({
                    "scenario_id": f"ring_case_{case_name}",
                    "source_scenario_id": case_name,
                    "material_axes_global_xyz": axes,
                    "frame_audit": transverse_row["frame_audits"][case_name],
                    "status": "conditional_ring_orientation_scenario_not_observed_stock",
                    "measured": False,
                    "accepted": False,
                })
            row.update({
                "conditional_material_assignment_status": "conditional_source_bound_timber_scenario_not_received_stock",
                "conditional_property_scenario_ref": "douglas_fir_orthotropic_elastic_diagnostic_2026-09-24",
                "grain_assignment": {
                    "material_axis": "L",
                    "direction_global_xyz": grain,
                    "status": orientation_row["conditional_grain_assignment"]["status"],
                    "delivered_stock_observed": False,
                    "orientation_map_row_sha256": row_digest(orientation_row),
                    "orientation_map_source_sha256": sha256_file(ROOT / TIMBER_MAP),
                },
                "transverse_ring_scenarios": cases,
                "density_assignment": {
                    "value_kg_m3": None,
                    "status": "unresolved_no_density_value_in_current_elastic_scenario",
                    "measured": False,
                    "basis": "Current body-gravity accounting is a separate mass input contract; it provides no accepted per-body density-to-mesh mapping.",
                },
                "source_map_rows": {
                    "timber_orientation_row_sha256": row_digest(orientation_row),
                    "timber_transverse_row_sha256": row_digest(transverse_row),
                    "timber_transverse_source_sha256": sha256_file(ROOT / TIMBER_TRANSVERSE),
                },
            })
            material_case_count += 2
        elif kind == "candidate_block":
            orientation_row = block_rows[member_id]
            block_manifest_row = block_manifest_rows[member_id]
            finished_binding = block_manifest_row["current_finished_step_binding"]
            if (
                finished_binding["path"] != binding["path"]
                or finished_binding["file_sha256"] != binding["file_sha256"]
                or finished_binding["source_shape_fingerprint_sha256"] != binding["source_shape_fingerprint_sha256"]
            ):
                raise ValueError(f"Connector-block manifest STEP binding mismatch for {member_id}")
            case_records = orientation_row["transverse_assignment_cases"]
            if len(case_records) != 2 or len({case["scenario_id"] for case in case_records}) != 2:
                raise ValueError(f"Expected two distinct ring scenarios for {member_id}")
            grain = orientation_row["conditional_grain_assignment"]["grain_direction_global_xyz"]
            cases = []
            for case in case_records:
                axes = case["material_axes_global_xyz"]
                validate_axes(axes, f"{member_id} {case['scenario_id']}")
                if abs(dot(grain, axes["L"])) < 1.0 - 1e-8:
                    raise ValueError(f"Block material L axis differs from conditional grain for {member_id}/{case['scenario_id']}")
                cases.append({
                    "scenario_id": case["scenario_id"],
                    "material_axes_global_xyz": axes,
                    "orientation_points_global_xyz": case["calculix_orientation_points_global_xyz"],
                    "status": "conditional_ring_orientation_scenario_not_observed_stock",
                    "measured": False,
                    "accepted": False,
                })
            row.update({
                "conditional_material_assignment_status": "conditional_source_bound_connector_block_scenario_not_received_stock",
                "conditional_property_scenario_ref": "douglas_fir_orthotropic_elastic_diagnostic_2026-09-24",
                "grain_assignment": {
                    "material_axis": "L",
                    "direction_global_xyz": grain,
                    "source_axis_name": orientation_row["conditional_grain_assignment"]["source_axis_name"],
                    "grain_basis": orientation_row["conditional_grain_assignment"]["grain_basis"],
                    "status": "conditional_pattern_grain_assignment_not_observed_stock",
                    "delivered_stock_observed": False,
                    "block_map_row_sha256": row_digest(orientation_row),
                    "block_map_source_sha256": sha256_file(ROOT / BLOCK_MAP),
                },
                "transverse_ring_scenarios": cases,
                "density_assignment": {
                    "value_kg_m3": None,
                    "status": "unresolved_no_density_value_in_current_elastic_scenario",
                    "measured": False,
                    "basis": "Current body-gravity accounting is a separate mass input contract; it provides no accepted per-body density-to-mesh mapping.",
                },
                "source_map_rows": {
                    "block_orientation_row_sha256": row_digest(orientation_row),
                    "block_map_source_sha256": sha256_file(ROOT / BLOCK_MAP),
                },
            })
            material_case_count += 2
        elif kind == "plywood_panel":
            row.update({
                "conditional_material_assignment_status": "unresolved_panel_product_layup_axes_properties_and_density",
                "conditional_property_scenario_ref": None,
                "grain_assignment": None,
                "transverse_ring_scenarios": [],
                "density_assignment": {
                    "value_kg_m3": None,
                    "status": "unresolved_panel_product_and_density",
                    "measured": False,
                },
                "source_map_rows": {},
            })
        else:
            raise ValueError(f"Unexpected full-frame member kind {kind!r} for {member_id}")
        member_rows.append(row)

    kind_counts: dict[str, int] = {}
    for row in member_rows:
        kind_counts[row["member_kind"]] = kind_counts.get(row["member_kind"], 0) + 1
    if kind_counts != {"timber": 20, "candidate_block": 24, "plywood_panel": 6}:
        raise ValueError(f"Unexpected exact body kind counts: {kind_counts}")
    if material_case_count != 88:
        raise ValueError(f"Expected 88 conditional wood transverse cases, found {material_case_count}")

    # Reuse the existing, proposal-only material helper record. The helper is
    # imported only to serialize the already documented scenario; it does not
    # load geometry, mesh, generate solver input, or execute a solver.
    sys.path.insert(0, str(ROOT))
    from fea.wood_joint_patch_materials import material_scenario

    wood_scenario = json.loads(json.dumps(material_scenario(), allow_nan=False))
    if wood_scenario["qualified_for_design"] or wood_scenario["stock_properties_measured"]:
        raise ValueError("Conditional timber scenario unexpectedly carries acceptance")
    if sha256_file(ROOT / WOOD_SCENARIO_SOURCE) != wood_scenario["source_document_sha256"]:
        raise ValueError("Orthotropic material scenario source hash changed")

    # Existing readiness remains false in the authoritative attempt04 manifest;
    # this crosswalk adds no solver IDs, panel layups, density, or connection law.
    readiness = manifest["readiness"]
    required_false = (
        "inputs_ready",
        "per_member_material_mapping_ready",
        "six_plywood_panel_layups_assigned",
        "solver_body_element_dof_material_mapping_complete",
        "native_solve_executed",
    )
    if any(readiness.get(name) is not False for name in required_false):
        raise ValueError("Attempt04 readiness flags no longer match this partial-input crosswalk scope")

    pins = source_pins(manifest)
    panel_ids = sorted(row["member_id"] for row in member_rows if row["member_kind"] == "plywood_panel")
    payload: dict[str, Any] = {
        "schema": "wood_joint_current_full_frame_conditional_material_crosswalk/v1",
        "attempt_id": ATTEMPT_ID,
        "status": "SOURCE_BOUND_PREMESH_CONDITIONAL_WOOD_INPUTS_ONLY_NOT_SOLVER_READY",
        "candidate": CANDIDATE,
        "selected_candidate_preserved": "compact-floor-flush-development",
        "geometry_revision_id": REVISION,
        "input_manifest_id": manifest["manifest_id"],
        "input_manifest_content_sha256": manifest["manifest_sha256"],
        "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "producer_sha256": sha256_file(Path(__file__).resolve()),
        "source_pins": pins,
        "counts": {
            "exact_full_frame_bodies": len(member_rows),
            "frame_timber_bodies": kind_counts["timber"],
            "connector_block_bodies": kind_counts["candidate_block"],
            "wood_bodies_with_conditional_property_scenario_ref": kind_counts["timber"] + kind_counts["candidate_block"],
            "wood_bodies_with_two_transverse_ring_scenarios": kind_counts["timber"] + kind_counts["candidate_block"],
            "conditional_transverse_ring_scenarios": material_case_count,
            "plywood_panel_bodies_unresolved": kind_counts["plywood_panel"],
            "candidate_bolt_axes_with_material_assignment": 0,
            "retained_frame_bolt_axes_with_material_assignment": 0,
        },
        "crosswalk_method": {
            "body_identity_and_step_binding": "Exact member_id and current finished STEP path/hash are joined from attempt04 physical_members and finished_member_step_bindings.",
            "frame_timber_assignments": "Join 20 body-specific longitudinal source orientation records to the 20 body-specific transverse ring scenario records; each STEP path, SHA-256, and source shape fingerprint is cross-checked.",
            "connector_block_assignments": "Join 24 body-specific source-frame/grain/two-case records to attempt04 candidate block finished STEP bindings by exact part_id and SHA-256.",
            "attempt03_coverage": "Every prior coverage row joins on exact member_id and identical STEP path/hash; its null material and solver assignments remain visible as historical pre-crosswalk state.",
            "orientation_policy": "Two source-bound transverse R/T alternatives per wood body; alternatives are conditional scenarios, not measured ring direction, selected assignments, or guaranteed bounds.",
            "property_policy": "Reuse the existing Douglas-fir orthotropic diagnostic scenario as a conditional property reference. It supplies elastic constants only; no per-body density is assigned.",
            "geometry_policy": "Existing finished STEP solids and maps only; no geometry rebuild, CAD edit, mesh generation, solver input, or solve.",
        },
        "conditional_wood_elastic_scenario": wood_scenario,
        "density_policy": {
            "wood_density_value_kg_m3": None,
            "plywood_density_value_kg_m3": None,
            "status": "unresolved_no_density_assigned",
            "measured": False,
            "note": "The source-bound body-gravity artifact carries mass accounting and load placement scenarios, not a measured density or body/mesh density map.",
            "mass_scenario_source": DEAD_LOADS.as_posix(),
        },
        "unresolved_assignments": {
            "plywood_panels": {
                "count": len(panel_ids),
                "member_ids": panel_ids,
                "product": None,
                "layup": None,
                "material_axes": None,
                "elastic_properties": None,
                "density_kg_m3": None,
                "solver_material_ids": None,
                "status": "six_panel_products_layups_axes_properties_and_density_unresolved",
            },
            "candidate_steel_and_connection_system": {
                "candidate_bolt_axes": 92,
                "candidate_component_roles": 460,
                "physical_fastener_product_assignment": None,
                "per_body_or_role_material_assignment": None,
                "solver_material_ids": None,
                "solver_body_element_node_dof_ids": None,
                "connection_laws": None,
                "generic_elastic_role_scenario_source": STEEL_MAP.as_posix(),
                "status": "conditional_generic_steel_role_scenario_not_promoted_to_exact_body_or_solver_assignment",
            },
            "retained_starting_frame_bolts": {
                "axes": 12,
                "modeled_component_roles": 60,
                "material_assignment": None,
                "solver_ids": None,
                "status": "unresolved_candidate_recheck_and_solver_mapping",
            },
        },
        "readiness": {
            "source_bound_exact_step_rows_available": True,
            "conditional_wood_elastic_scenario_referenced": True,
            "conditional_wood_orientation_screens_cover_44_of_44": True,
            "two_transverse_scenarios_per_wood_body_cover_44_of_44": True,
            "wood_density_assigned": False,
            "six_plywood_panel_layups_assigned": False,
            "steel_body_or_role_solver_material_assignments_complete": False,
            "connection_laws_assigned": False,
            "solver_body_element_dof_mapping_complete": False,
            "full_frame_per_member_material_mapping_ready": False,
            "inputs_ready": False,
            "native_solve_executed": False,
            "candidate_accepted": False,
            "fabrication_released": False,
            "climbing_released": False,
        },
        "inherited_attempt04_readiness": {name: readiness[name] for name in required_false},
        "members": member_rows,
        "limits": [
            "All wood properties and orientation records are conditional analysis scenarios, not measured, delivered, calibrated, accepted, or design-qualified properties.",
            "The source inventory DF-L No. 2 basis does not establish the delivered species group, grade, treatment, moisture, receiving condition, or grade after remanufacture.",
            "Density remains null for all wood and panel bodies; the separate gravity/mass scenario is not a per-body density or solver mass mapping.",
            "Each wood body's two R/T alternatives preserve unknown transverse ring orientation; they are not observed board rings or guaranteed response bounds.",
            "All six plywood product/layup/orientation/property assignments remain unresolved.",
            "Generic steel elastic role scenarios are not exact fastener body assignments. Physical hardware identity, steel/connection material IDs, solver IDs, and connection laws remain unresolved.",
            "No mesh, element, node, DOF, mass-carrier, load, boundary, contact, or complete joint mechanics mapping is supplied.",
            "Attempt04 readiness remains false for full-frame material mapping, inputs, and native solve; no mechanical acceptance or release is claimed.",
        ],
        "release": {
            "candidate_accepted": False,
            "climbing_released": False,
            "drilling_released": False,
            "engineering_mvp_complete": False,
            "fabrication_released": False,
            "structural_released": False,
        },
    }
    payload["record_sha256"] = record_digest(payload, "record_sha256")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="create the attempt artifact; refuses overwrite")
    mode.add_argument("--verify", action="store_true", help="read-only source and artifact verification")
    args = parser.parse_args()
    output_path = ROOT / OUTPUT
    expected = build_crosswalk()
    if args.write:
        if output_path.exists():
            raise SystemExit(f"Refusing to overwrite existing append-only artifact: {OUTPUT}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {OUTPUT}")
    else:
        if not output_path.is_file():
            raise SystemExit(f"Missing artifact: {OUTPUT}")
        actual = json.loads(output_path.read_text(encoding="utf-8"))
        if actual != expected:
            raise SystemExit("Crosswalk differs from current source-derived expected payload")
        if actual.get("record_sha256") != record_digest(actual, "record_sha256"):
            raise SystemExit("Crosswalk record digest mismatch")
        print(
            "Verified read-only: "
            f"{actual['counts']['exact_full_frame_bodies']} exact bodies, "
            f"{actual['counts']['wood_bodies_with_two_transverse_ring_scenarios']} wood bodies, "
            f"{actual['counts']['conditional_transverse_ring_scenarios']} transverse cases, "
            f"{actual['counts']['plywood_panel_bodies_unresolved']} unresolved panels; "
            "no mesh or solver execution"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
