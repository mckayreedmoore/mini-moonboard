"""Reconcile the archived representative WJ04 steel mesh with WJ24 wood.

This is a read-only JSON/hash comparison. It does not import CAD, regenerate
geometry, mesh, assign contact, or run a solver. The output is a bounded
identity bridge for eight representative bolts only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj24-representative-hardware-identity"
OUTPUT_PATH = OUTPUT_DIR / "identity.json"
INDEX_PATH = OUTPUT_DIR / "sha256.json"

PATCH_DIR = ROOT / "fea/results/diagnostics/wj04-full-stock-patch-geometry-v1"
MECHANICS_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj16-full-stock-mechanics-inputs"
HARDWARE_DIR = ROOT / "fea/results/diagnostics/wj04-mechanics-hardware-v1"
MESH_EVIDENCE_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj04-hardware-patch-mesh/attempt-01"
WJ24_STATIC_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj24-integrated-static"
WJ24_HARDWARE_DIR = ROOT / "docs/wood-joints-mvp/hypotheses/wj24-hardware-inventory"
WJ24_WOOD_DIR = ROOT / "fea/results/diagnostics/wj24-baseline-patch-geometry-v1"

STACK_IDS = (
    "lower_rail_1",
    "lower_rail_2",
    "lower_principal_1",
    "lower_principal_2",
    "upper_rail_1",
    "upper_rail_2",
    "upper_principal_1",
    "upper_principal_2",
)
FAMILY_ID = "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis"
PHYSICAL_ROLES = ("bolt", "head_washer", "nut_washer", "nut")
CAD_ROLES = ("head", "head_washer", "nut", "nut_washer", "shaft")
WOOD_BODY_IDS = (
    "base_rail_service_lower_right",
    "base_rail_service_upper_right",
    "base_principal_center_right",
    "wj04_lower_full_stock_cleat",
    "wj04_upper_g7_crosscut_full_stock_cleat",
)
SCENARIO_ID = "body_to_far_wood_face"
WOOD_GRIP_MM = 127.0
HEAD_WASHER_THICKNESS_MM = 2.032
GEOMETRY_TOLERANCE_MM = 1e-3
VOLUME_TOLERANCE_MM3 = 1e-6


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256(path.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def _close_vector(first: Any, second: Any, tolerance: float, context: str) -> None:
    if not isinstance(first, list) or not isinstance(second, list) or len(first) != len(second):
        raise ValueError(f"{context}: expected vectors of equal length")
    values = [abs(float(a) - float(b)) for a, b in zip(first, second, strict=True)]
    if not all(math.isfinite(value) for value in values) or max(values, default=0.0) > tolerance:
        raise ValueError(f"{context}: vector difference exceeds {tolerance:g}")


def _close_number(first: Any, second: Any, tolerance: float, context: str) -> None:
    a, b = float(first), float(second)
    if not math.isfinite(a) or not math.isfinite(b) or abs(a - b) > tolerance:
        raise ValueError(f"{context}: difference exceeds {tolerance:g}")


def _verify_indexed_files(directory: Path, index_name: str, relative_paths: list[str]) -> tuple[dict[str, str], str]:
    index_path = directory / index_name
    index = _read_json(index_path)
    verified: dict[str, str] = {}
    for relative in relative_paths:
        expected = index.get(relative)
        path = directory / relative
        if not isinstance(expected, str) or len(expected) != 64 or not path.is_file():
            raise ValueError(f"{index_path.relative_to(ROOT)}: missing indexed file {relative}")
        actual = _sha256_file(path)
        if actual != expected:
            raise ValueError(f"{path.relative_to(ROOT)}: SHA-256 differs from {index_name}")
        verified[relative] = actual
    return verified, _sha256_file(index_path)


def _delta_bounds_overlap(first: list[float], second: list[float]) -> bool:
    # Inclusive comparison is conservative: touching boxes are treated as overlap.
    return all(
        float(first[2 * axis]) <= float(second[2 * axis + 1])
        and float(second[2 * axis]) <= float(first[2 * axis + 1])
        for axis in range(3)
    )


def _union_bounds(bounds: list[list[float]]) -> list[float]:
    return [
        min(float(row[0]) for row in bounds),
        max(float(row[1]) for row in bounds),
        min(float(row[2]) for row in bounds),
        max(float(row[3]) for row in bounds),
        min(float(row[4]) for row in bounds),
        max(float(row[5]) for row in bounds),
    ]


def _dot(vector_a: list[float], vector_b: list[float]) -> float:
    return math.fsum(float(a) * float(b) for a, b in zip(vector_a, vector_b, strict=True))


def _add_scaled(origin: list[float], axis: list[float], station: float) -> list[float]:
    return [float(point) + station * float(direction) for point, direction in zip(origin, axis, strict=True)]


def _verify_old_mesh_archive() -> tuple[dict[str, Any], dict[str, str]]:
    contents_path = MESH_EVIDENCE_DIR / "bundle-contents.json"
    archive_path = MESH_EVIDENCE_DIR / "complete-mesh-evidence.tar.gz"
    outer_index_path = MESH_EVIDENCE_DIR / "sha256.json"
    contents = _read_json(contents_path)
    outer_index = _read_json(outer_index_path)
    for relative in ("bundle-contents.json", "complete-mesh-evidence.tar.gz"):
        path = MESH_EVIDENCE_DIR / relative
        if _sha256_file(path) != outer_index.get(relative):
            raise ValueError(f"{path.relative_to(ROOT)}: outer archive index mismatch")
    mesh_member = contents.get("mesh.json")
    inp_member = contents.get("mesh.inp")
    if not isinstance(mesh_member, dict) or not isinstance(inp_member, dict):
        raise TypeError("archived WJ04 metal mesh contents index is incomplete")
    with tarfile.open(archive_path, "r:gz") as archive:
        mesh_file = archive.extractfile("mesh.json")
        inp_file = archive.extractfile("mesh.inp")
        if mesh_file is None or inp_file is None:
            raise ValueError("archived WJ04 metal mesh report/deck is missing")
        mesh_bytes, inp_bytes = mesh_file.read(), inp_file.read()
    if len(mesh_bytes) != mesh_member.get("bytes") or _sha256(mesh_bytes) != mesh_member.get("sha256"):
        raise ValueError("archived WJ04 metal mesh report differs from contents index")
    if len(inp_bytes) != inp_member.get("bytes") or _sha256(inp_bytes) != inp_member.get("sha256"):
        raise ValueError("archived WJ04 metal mesh deck differs from contents index")
    report = json.loads(mesh_bytes)
    return report, {
        "archive_sha256": _sha256_file(archive_path),
        "contents_index_sha256": _sha256_file(contents_path),
        "outer_hash_index_sha256": _sha256_file(outer_index_path),
        "mesh_report_sha256": _sha256(mesh_bytes),
        "mesh_deck_sha256": _sha256(inp_bytes),
    }


def build_identity_report() -> dict[str, Any]:
    patch_path = PATCH_DIR / "inventory.json"
    mechanics_path = MECHANICS_DIR / "mechanics-inputs.json"
    hardware_path = HARDWARE_DIR / "inventory.json"
    composition_path = WJ24_STATIC_DIR / "composition.json"
    wj24_hardware_path = WJ24_HARDWARE_DIR / "inventory.json"
    wj24_reconciliation_path = WJ24_WOOD_DIR / "reconciliation.json"

    patch_hashes, patch_index_sha = _verify_indexed_files(
        PATCH_DIR,
        "sha256.json",
        ["inventory.json", *(f"wood/{body_id}.step" for body_id in WOOD_BODY_IDS)],
    )
    mechanics_hashes, mechanics_index_sha = _verify_indexed_files(
        MECHANICS_DIR, "sha256.json", ["mechanics-inputs.json"]
    )
    hardware_inventory = _read_json(hardware_path)
    hardware_manifest_paths = ["inventory.json", "references/nbs-unified-thread-table2-excerpt.json"]
    hardware_manifest_paths.extend(sorted(hardware_inventory.get("step_artifacts", {})))
    hardware_hashes, hardware_index_sha = _verify_indexed_files(
        HARDWARE_DIR, "sha256.json", hardware_manifest_paths
    )
    wj24_static_hashes, wj24_static_index_sha = _verify_indexed_files(
        WJ24_STATIC_DIR, "sha256.json", ["composition.json"]
    )
    wj24_hardware_hashes, wj24_hardware_index_sha = _verify_indexed_files(
        WJ24_HARDWARE_DIR, "sha256.json", ["inventory.json"]
    )
    wj24_wood_hashes, wj24_wood_index_sha = _verify_indexed_files(
        WJ24_WOOD_DIR,
        "sha256.json",
        ["reconciliation.json", *(f"wood/{body_id}.step" for body_id in WOOD_BODY_IDS)],
    )

    patch = _read_json(patch_path)
    mechanics = _read_json(mechanics_path)
    composition = _read_json(composition_path)
    wj24_hardware = _read_json(wj24_hardware_path)
    reconciliation = _read_json(wj24_reconciliation_path)
    mesh_report, mesh_hashes = _verify_old_mesh_archive()

    if patch.get("schema") != "wood_joint_wj04_patch_geometry/v1":
        raise ValueError("legacy WJ16 patch inventory schema changed")
    if hardware_inventory.get("schema") != "wood_joint_wj04_mechanics_hardware/v1":
        raise ValueError("representative steel source inventory schema changed")
    if wj24_hardware.get("schema") != "wood_joint_wj24_hardware_inventory/v1":
        raise ValueError("current WJ24 hardware inventory schema changed")
    if reconciliation.get("status") != "source_bound_representative_WJ16_to_WJ24_geometry_comparison_only":
        raise ValueError("WJ16-to-WJ24 finished-wood reconciliation status changed")
    if mesh_report.get("scenario_id") != SCENARIO_ID or mesh_report.get("body_count") != 32:
        raise ValueError("archived representative metal mesh is not the 32-body selected profile")
    if mesh_report.get("physical_mesh_scope", {}).get("physical_bolts") != 8:
        raise ValueError("archived metal mesh bolt count is not eight")
    if mesh_report.get("physical_mesh_scope", {}).get("physical_solids") != 32:
        raise ValueError("archived metal mesh physical solid count is not 32")
    if mesh_report.get("legacy_collision_roles_meshed") != 0:
        raise ValueError("legacy collision envelopes must remain unmeshed metadata")
    if mesh_report.get("solved") is not False or mesh_report.get("accepted") is not False:
        raise ValueError("archived mesh claims exceed geometry preparation")
    if mesh_report.get("input_bundle_inventory_sha256") != hardware_hashes["inventory.json"]:
        raise ValueError("archived steel mesh no longer binds its original hardware inventory")
    if mesh_report.get("wood_mesh_bundle_sha256") != patch_hashes["inventory.json"]:
        raise ValueError("archived steel mesh no longer retains its original WJ16 wood fingerprint")
    if mesh_report.get("input_bundle_hash_index_sha256") != hardware_index_sha:
        raise ValueError("archived steel mesh no longer binds its original hardware hash index")
    if mesh_report.get("active_contact_or_tie_set_assignment") is not False:
        raise ValueError("archived steel mesh unexpectedly assigns active contacts or ties")
    if mesh_report.get("material_contact_tie_preload_load_or_solver_cards") is not False:
        raise ValueError("archived steel mesh exceeds geometry-only scope")
    mesh_contents = _read_json(MESH_EVIDENCE_DIR / "bundle-contents.json")
    if mesh_report.get("mesh_input_sha256") != mesh_contents.get("mesh.inp", {}).get("sha256"):
        raise ValueError("archived steel mesh report/deck binding differs")
    if hardware_inventory.get("source_inputs", {}).get("sha256", {}).get("patch_inventory.json") != patch_hashes["inventory.json"]:
        raise ValueError("physical steel source inventory no longer binds the WJ16 wood source")
    if hardware_inventory.get("source_inputs", {}).get("sha256", {}).get("mechanics_inputs.json") != mechanics_hashes["mechanics-inputs.json"]:
        raise ValueError("physical steel source inventory no longer binds WJ16 axis mechanics")
    hardware_scope = hardware_inventory.get("scope", {})
    if any(
        hardware_scope.get(key) != value
        for key, value in (
            ("unique_physical_bolts", 8),
            ("physical_solids_per_scenario", 32),
            ("grip_each_bolt_mm", WOOD_GRIP_MM),
            ("native_solver_run", False),
            ("capacity_or_release_claim", False),
        )
    ):
        raise ValueError("physical steel source inventory changed count or claim boundary")
    if hardware_inventory.get("status") != "conditional_response_hardware_geometry_only":
        raise ValueError("physical steel source inventory status exceeds its conditional geometry scope")
    if reconciliation.get("source_composition", {}).get("WJ24", {}).get("report_sha256") != wj24_static_hashes["composition.json"]:
        raise ValueError("WJ24 geometry reconciliation is not bound to the current integrated composition")
    if reconciliation.get("source_composition", {}).get("WJ16", {}).get("report_sha256") != patch.get("composition", {}).get("wj16_composition_report_sha256"):
        raise ValueError("WJ24 geometry reconciliation is not bound to the preserved WJ16 composition")
    if reconciliation.get("source_composition", {}).get("shared_source_object") is not True:
        raise ValueError("WJ16 and WJ24 geometry comparison does not share its source object")
    if reconciliation.get("old_WJ16_patch_bundle", {}).get("inventory_sha256") != patch_hashes["inventory.json"]:
        raise ValueError("WJ24 geometry reconciliation is not bound to the preserved WJ16 patch")
    composition_checks = wj24_hardware.get("source_provenance", {}).get("composition_identity_checks", {})
    if composition_checks.get("canonical_inventory_hash_and_source_binding_match") is not True:
        raise ValueError("WJ24 hardware inventory no longer binds the canonical geometry source")
    if composition_checks.get("all_104_candidate_axes_and_520_roles_preserved") is not True:
        raise ValueError("WJ24 hardware inventory no longer accounts for the integrated axis/role set")
    if composition_checks.get("zero_retained_legacy_clips_or_sds_axes") is not True:
        raise ValueError("WJ24 candidate composition retained a legacy clip or SDS axis")

    old_rows = {row.get("stack_spec_id"): row for row in patch.get("physical_bolts", [])}
    mechanics_rows = {row.get("stack_spec_id"): row for row in mechanics.get("physical_bolts", [])}
    selected_scenario = next(
        (row for row in hardware_inventory.get("scenarios", []) if row.get("scenario_id") == SCENARIO_ID),
        None,
    )
    if selected_scenario is None or selected_scenario.get("physical_bolt_count") != 8:
        raise ValueError("representative body-to-far-face steel profile is missing or changed")
    if selected_scenario.get("physical_solid_count") != 32 or selected_scenario.get("physical_profile_claim") is not False:
        raise ValueError("representative body-to-far-face profile count or claim boundary changed")
    physical_rows = {row.get("stack_spec_id"): row for row in selected_scenario.get("stacks", [])}
    current_axes = composition.get("candidate_axes", {})
    schedule = {row.get("axis_id"): row for row in wj24_hardware.get("candidate_hardware_axis_schedule", [])}
    mesh_bodies = mesh_report.get("bodies", {})
    body_comparisons = {row.get("body_id"): row for row in reconciliation.get("body_comparisons", [])}

    if set(old_rows) != set(STACK_IDS) or set(mechanics_rows) != set(STACK_IDS):
        raise ValueError("WJ16 source/mechanics reports do not contain exactly the eight named axes")
    if set(physical_rows) != set(STACK_IDS):
        raise ValueError("physical steel geometry inventory does not contain exactly the eight named axes")
    if set(body_comparisons) != set(WOOD_BODY_IDS):
        raise ValueError("WJ24 reconciliation body set differs from the five-body identity contract")

    # The original profile fingerprint is kept verbatim. WJ24 receives a
    # separate bridge; it never overwrites or impersonates this WJ16 value.
    legacy_wood_mesh_sha = mesh_report.get("wood_mesh_bundle_sha256")
    report_rows: list[dict[str, Any]] = []
    role_counts = {role: 0 for role in PHYSICAL_ROLES}
    selected_geometry = hardware_inventory.get("selected_hardware_geometry", {})
    for stack_id in STACK_IDS:
        axis_id = f"{FAMILY_ID}/{stack_id}"
        old = old_rows[stack_id]
        mech = mechanics_rows[stack_id]
        metal = physical_rows[stack_id]
        wj24_axis = current_axes.get(axis_id)
        current_schedule = schedule.get(axis_id)
        if not isinstance(wj24_axis, dict) or not isinstance(current_schedule, dict):
            raise TypeError(f"WJ24 source is missing representative candidate axis {axis_id}")

        old_receivers = [row["member_id"] for row in old.get("receivers_head_to_nut", [])]
        expected_receivers = old_receivers
        if len(expected_receivers) != 2 or any(body not in WOOD_BODY_IDS for body in expected_receivers):
            raise ValueError(f"{axis_id}: participant list is not a known two-body WJ16 interface")
        current_receivers = wj24_axis.get("receiver_ids")
        if current_receivers != expected_receivers:
            raise ValueError(f"{axis_id}: WJ24 receiver order/identity differs from WJ16")
        mechanics_receivers = [row["member_id"] for row in mech.get("receivers_head_to_nut", [])]
        physical_receivers = [row["member_id"] for row in metal.get("receivers_head_to_nut", [])]
        if mechanics_receivers != expected_receivers or physical_receivers != expected_receivers:
            raise ValueError(f"{axis_id}: WJ16 mechanics/physical-profile participant order differs")
        if current_schedule.get("ordered_receiver_ids_from_candidate_bore") != expected_receivers:
            raise ValueError(f"{axis_id}: current WJ24 inventory receiver order differs")
        stack_class = current_schedule.get("stack_class", {})
        if stack_class.get("hardware_model_class") != "six_in_model_127_mm_grip" or stack_class.get("modeled_nominal_length_mm") != 152.4 or stack_class.get("nominal_wood_grip_mm") != WOOD_GRIP_MM:
            raise ValueError(f"{axis_id}: current WJ24 candidate hardware class or modeled grip differs")
        if set(wj24_axis.get("installed_role_ids", [])) != set(CAD_ROLES):
            raise ValueError(f"{axis_id}: current WJ24 CAD role set changed")
        if set(current_schedule.get("installed_cad_role_ids", [])) != set(CAD_ROLES):
            raise ValueError(f"{axis_id}: current inventory CAD role set changed")

        old_bore = old.get("composed_occupancy_bore", {})
        current_bore = wj24_axis.get("bore_shape", {})
        if old_bore.get("cad_shape_sha256") != current_bore.get("shape_sha256"):
            raise ValueError(f"{axis_id}: WJ24 candidate bore shape fingerprint differs")
        _close_vector(old_bore.get("bounds_xyz_mm"), current_bore.get("bounds_xyz_mm"), GEOMETRY_TOLERANCE_MM, f"{axis_id} bore bounds")
        _close_number(old_bore.get("volume_mm3"), current_bore.get("volume_mm3"), VOLUME_TOLERANCE_MM3, f"{axis_id} bore volume")

        axis = [float(value) for value in metal["world_axis_direction_head_to_nut"]]
        origin = [float(value) for value in metal["underhead_origin_global_xyz_mm"]]
        head_face = [float(value) for value in metal["wood_head_face_center_global_xyz_mm"]]
        far_face = [float(value) for value in metal["wood_far_face_center_global_xyz_mm"]]
        if len(axis) != 3 or len(origin) != 3 or len(head_face) != 3 or len(far_face) != 3:
            raise ValueError(f"{axis_id}: axis/seat coordinates must be 3D")
        _close_vector(axis, mech.get("world_axis_direction_head_to_nut"), 1e-10, f"{axis_id} source axis direction")
        _close_vector(head_face, mech.get("world_axis_origin_xyz_mm"), GEOMETRY_TOLERANCE_MM, f"{axis_id} first wood-face datum")
        _close_vector([float(x) for x in old["world_axis_direction_head_to_nut"]], axis, 1e-10, f"{axis_id} patch axis direction")
        if float(metal.get("wood_grip_mm", math.nan)) != WOOD_GRIP_MM:
            raise ValueError(f"{axis_id}: representative modeled wood grip changed")
        if not math.isclose(math.sqrt(_dot(axis, axis)), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"{axis_id}: direction is not a unit vector")

        # First and far wood seats are the head and nut washer bearing planes.
        expected_head_face = _add_scaled(origin, axis, HEAD_WASHER_THICKNESS_MM)
        expected_far_face = _add_scaled(origin, axis, HEAD_WASHER_THICKNESS_MM + WOOD_GRIP_MM)
        _close_vector(head_face, expected_head_face, GEOMETRY_TOLERANCE_MM, f"{axis_id} head washer wood seat")
        _close_vector(far_face, expected_far_face, GEOMETRY_TOLERANCE_MM, f"{axis_id} nut washer wood seat")
        _close_number(metal.get("nut_washer_start_station_from_underhead_mm"), HEAD_WASHER_THICKNESS_MM + WOOD_GRIP_MM, VOLUME_TOLERANCE_MM3, f"{axis_id} far-face profile station")
        _close_number(metal.get("smooth_body_transition_station_from_underhead_mm"), HEAD_WASHER_THICKNESS_MM + WOOD_GRIP_MM, VOLUME_TOLERANCE_MM3, f"{axis_id} profile transition station")
        _close_number(sum(float(row["wood_thickness_mm"]) for row in old["receivers_head_to_nut"]), WOOD_GRIP_MM, GEOMETRY_TOLERANCE_MM, f"{axis_id} participant grip sum")

        stack_mesh_rows: dict[str, Any] = {}
        for role in PHYSICAL_ROLES:
            role_counts[role] += 1
            body_id = f"{stack_id}__{role}"
            mesh_body = mesh_bodies.get(body_id)
            if not isinstance(mesh_body, dict) or mesh_body.get("component_role") != role:
                raise ValueError(f"{axis_id}: archived mesh body {body_id} is missing or misclassified")
            solid_identity = mesh_body.get("solid_identity", {})
            expected_rel = f"hardware/{SCENARIO_ID}/{stack_id}/{role}.step"
            if solid_identity.get("inventory_sha256") != hardware_hashes["inventory.json"]:
                raise ValueError(f"{axis_id}/{role}: old mesh body no longer binds its hardware inventory")
            if solid_identity.get("step_sha256") != hardware_hashes.get(expected_rel):
                raise ValueError(f"{axis_id}/{role}: old mesh source STEP identity differs")
            source_solid = metal.get("component_solids", {}).get(role, {})
            if solid_identity.get("source_shape_sha256") != source_solid.get("cad_shape_sha256"):
                raise ValueError(f"{axis_id}/{role}: old mesh source-shape identity differs")
            if solid_identity.get("expected_solid_count") != 1 or solid_identity.get("imported_solid_count") != 1:
                raise ValueError(f"{axis_id}/{role}: old mesh body is not one physical solid")
            if mesh_body.get("stack_spec_id") != stack_id or mesh_body.get("physical_bolt_id") != axis_id:
                raise ValueError(f"{axis_id}/{role}: old mesh body axis identity differs")
            datum = mesh_body.get("axis_datum", {})
            _close_vector(datum.get("origin_global_xyz_mm"), origin, GEOMETRY_TOLERANCE_MM, f"{axis_id}/{role} mesh underhead origin")
            _close_vector(datum.get("direction_head_to_nut_global"), axis, 1e-10, f"{axis_id}/{role} mesh direction")
            imported_bounds = mesh_body.get("imported_cad", {}).get("bounds_xyz_mm")
            _close_vector(imported_bounds, source_solid.get("bounds_xyz_mm"), GEOMETRY_TOLERANCE_MM, f"{axis_id}/{role} mesh/source bounds")
            stack_mesh_rows[role] = {
                "mesh_body_id": body_id,
                "source_step_sha256": solid_identity["step_sha256"],
                "imported_solid_count": 1,
                "bounds_xyz_mm": imported_bounds,
                "surface_classification_status": mesh_body.get("surface_classification", {}).get("status"),
            }

        # The physical mesh body roles use `bolt` as the continuous head/shank;
        # wood-seat labels are classified on each separate washer body.
        head_washer_labels = {
            candidate
            for surface in mesh_bodies[f"{stack_id}__head_washer"].get("surfaces", {}).values()
            for candidate in surface.get("datum_classification", {}).get("role_candidates", [])
        }
        nut_washer_labels = {
            candidate
            for surface in mesh_bodies[f"{stack_id}__nut_washer"].get("surfaces", {}).values()
            for candidate in surface.get("datum_classification", {}).get("role_candidates", [])
        }
        if "head_washer_wood_seat_face" not in head_washer_labels or "nut_washer_wood_seat_face" not in nut_washer_labels:
            raise ValueError(f"{axis_id}: the two washer wood-seat descriptors are missing")

        component_bounds = [solid["bounds_xyz_mm"] for solid in metal["component_solids"].values()]
        envelope_bounds = _union_bounds(component_bounds)
        participants = []
        for body_id in expected_receivers:
            comparison = body_comparisons[body_id]
            unchanged = comparison.get("same_geometry_within_tolerance") is True
            delta_rows = comparison.get("delta_solids", []) or []
            if unchanged:
                if comparison.get("WJ16", {}).get("cad_shape_sha256") != comparison.get("WJ24", {}).get("cad_shape_sha256"):
                    raise ValueError(f"{axis_id}/{body_id}: unchanged-body source fingerprints differ")
                local_check = "whole_finished_solid_identical"
                overlap_count = 0
            else:
                if body_id != "base_principal_center_right" or not delta_rows:
                    raise ValueError(f"{axis_id}/{body_id}: changed participant lacks a bounded principal delta report")
                overlap_count = sum(
                    _delta_bounds_overlap(envelope_bounds, delta["bounds_xyz_mm"])
                    for delta in delta_rows
                )
                if overlap_count:
                    raise ValueError(f"{axis_id}/{body_id}: WJ24 wood delta touches the physical stack envelope")
                local_check = "all_exact_delta_solids_bbox_disjoint_from_complete_stack_envelope"
            participants.append(
                {
                    "body_id": body_id,
                    "WJ16_shape_sha256": comparison.get("WJ16", {}).get("cad_shape_sha256"),
                    "WJ24_shape_sha256": comparison.get("WJ24", {}).get("cad_shape_sha256"),
                    "whole_body_same_geometry": unchanged,
                    "local_identity_basis": local_check,
                    "reported_delta_solid_count": len(delta_rows),
                    "delta_bbox_overlaps_stack_envelope": overlap_count,
                }
            )

        report_rows.append(
            {
                "physical_bolt_id": axis_id,
                "stack_spec_id": stack_id,
                "interface_id": metal.get("interface_id"),
                "axis": {
                    "direction_head_to_nut_global": axis,
                    "underhead_origin_global_xyz_mm": origin,
                    "underhead_origin_basis": metal.get("underhead_origin_basis"),
                    "first_wood_face_axis_point_global_xyz_mm": head_face,
                    "far_wood_face_axis_point_global_xyz_mm": far_face,
                    "head_to_nut_direction_and_origin_source": "frozen WJ16 mechanics and WJ04 physical-profile inventory; exact WJ24 candidate-bore CAD fingerprint match",
                    "WJ16_occupancy_bore_shape_sha256": old_bore.get("cad_shape_sha256"),
                    "WJ24_candidate_bore_shape_sha256": current_bore.get("shape_sha256"),
                    "bore_bounds_difference_max_mm": max(
                        abs(float(a) - float(b))
                        for a, b in zip(old_bore["bounds_xyz_mm"], current_bore["bounds_xyz_mm"], strict=True)
                    ),
                    "bore_volume_difference_mm3": abs(float(old_bore["volume_mm3"]) - float(current_bore["volume_mm3"])),
                },
                "wood_stack": {
                    "ordered_receivers_head_to_nut": expected_receivers,
                    "receiver_thicknesses_mm": [float(row["wood_thickness_mm"]) for row in old["receivers_head_to_nut"]],
                    "wood_grip_mm": float(metal["wood_grip_mm"]),
                    "head_washer_wood_seat_center_global_xyz_mm": head_face,
                    "head_washer_wood_seat_station_from_underhead_mm": HEAD_WASHER_THICKNESS_MM,
                    "nut_washer_wood_seat_center_global_xyz_mm": far_face,
                    "nut_washer_wood_seat_station_from_underhead_mm": HEAD_WASHER_THICKNESS_MM + WOOD_GRIP_MM,
                    "wood_seat_role_assignment": "geometry descriptors only; no active contact or tie is assigned",
                },
                "profiles_and_body_roles": {
                    "scenario_id": SCENARIO_ID,
                    "scenario_interpretation": next(row["interpretation"] for row in hardware_inventory["scenarios"] if row["scenario_id"] == SCENARIO_ID),
                    "profile_transition_station_from_underhead_mm": float(metal["smooth_body_transition_station_from_underhead_mm"]),
                    "nut_interval_from_underhead_mm": [float(metal["nut_start_station_from_underhead_mm"]), float(metal["nut_end_station_from_underhead_mm"])],
                    "physical_mesh_role_count_per_stack": 4,
                    "physical_mesh_roles": stack_mesh_rows,
                    "WJ24_installed_CAD_roles": CAD_ROLES,
                    "physical_to_CAD_role_mapping": {
                        "bolt": ["head", "shaft"],
                        "head_washer": ["head_washer"],
                        "nut_washer": ["nut_washer"],
                        "nut": ["nut"],
                    },
                    "head_and_nut_washer_seat_surface_descriptors_present": True,
                    "material_or_contact_law": False,
                },
                "WJ24_participant_geometry": participants,
                "complete_stack_envelope_bounds_xyz_mm": envelope_bounds,
            }
        )

    if any(role_counts[role] != 8 for role in PHYSICAL_ROLES):
        raise ValueError("physical steel role count must be 8 bolts + 8 of each washer/nut role")
    if len(mesh_bodies) != 32:
        raise ValueError("archived representative steel mesh body count is not 32")

    wj24_step_solid_checks = {}
    for body_id in WOOD_BODY_IDS:
        artifact = reconciliation.get("step_artifacts", {}).get(body_id)
        if not isinstance(artifact, dict):
            raise TypeError(f"WJ24 reconciliation has no source-bound STEP artifact for {body_id}")
        identity = artifact.get("identity_checks", {})
        difference = identity.get("symmetric_difference", {})
        if any(identity.get(name) is not True for name in ("solid_count", "volume", "centroid", "bounds")):
            raise ValueError(f"WJ24 {body_id} STEP identity checks are incomplete")
        if difference.get("passed") is not True or difference.get("source_only_volume_mm3") != 0.0 or difference.get("step_only_volume_mm3") != 0.0:
            raise ValueError(f"WJ24 {body_id} STEP source/readback identity failed")
        rel = f"wood/{body_id}.step"
        if artifact.get("file_sha256") != wj24_wood_hashes.get(rel):
            raise ValueError(f"WJ24 {body_id} STEP artifact differs across indexes")
        wj24_step_solid_checks[body_id] = {
            "file_sha256": artifact["file_sha256"],
            "source_solid_sha256": artifact["source_solid"]["cad_shape_sha256"],
            "source_to_STEP_identity_checks_passed": True,
            "WJ16_to_WJ24_whole_body_same_geometry": body_comparisons[body_id].get("same_geometry_within_tolerance"),
        }

    input_hashes = {
        "identity_comparison_helper_py": _sha256_file(Path(__file__)),
        "WJ16_patch_inventory_json": patch_hashes["inventory.json"],
        "WJ16_patch_hash_index_json": patch_index_sha,
        "WJ16_mechanics_inputs_json": mechanics_hashes["mechanics-inputs.json"],
        "WJ16_mechanics_hash_index_json": mechanics_index_sha,
        "WJ04_physical_hardware_inventory_json": hardware_hashes["inventory.json"],
        "WJ04_physical_hardware_hash_index_json": hardware_index_sha,
        "WJ24_static_composition_json": wj24_static_hashes["composition.json"],
        "WJ24_static_hash_index_json": wj24_static_index_sha,
        "WJ24_hardware_inventory_json": wj24_hardware_hashes["inventory.json"],
        "WJ24_hardware_hash_index_json": wj24_hardware_index_sha,
        "WJ24_wood_reconciliation_json": wj24_wood_hashes["reconciliation.json"],
        "WJ24_wood_hash_index_json": wj24_wood_index_sha,
        **{f"WJ24_STEP_{key.replace('/', '_')}": value for key, value in wj24_wood_hashes.items() if key.startswith("wood/")},
        "WJ04_archived_steel_mesh_report_archive": mesh_hashes["archive_sha256"],
        "WJ04_archived_steel_mesh_contents_index": mesh_hashes["contents_index_sha256"],
        "WJ04_archived_steel_mesh_json_member": mesh_hashes["mesh_report_sha256"],
        "WJ04_archived_steel_mesh_inp_member": mesh_hashes["mesh_deck_sha256"],
    }

    return {
        "schema": "wood_joint_wj24_representative_hardware_identity/v1",
        "status": "representative_metal_to_WJ24_wood_identity_only",
        "inspection_date": "2026-09-24",
        "outcome": "all_eight_old_physical_stack_axes_and_ordered_participants_match_current_WJ24; wood_changes_are_outside_each_stack_envelope",
        "scope": {
            "physical_bolts": 8,
            "physical_washers": 16,
            "physical_nuts": 8,
            "physical_metal_solids": 32,
            "representative_interfaces": 4,
            "selected_profile_scenario": SCENARIO_ID,
            "wood_bodies": list(WOOD_BODY_IDS),
        },
        "claim_boundary": {
            "accepted": False,
            "current_WJ24_wood_mesh_rebuilt_or_reused_here": False,
            "material_assigned": False,
            "contact_or_tie_assigned": False,
            "native_solve_run": False,
            "capacity_established": False,
            "delivered_hardware_fit_or_inspection_established": False,
            "fabrication_or_drilling_released": False,
            "interpretation": "Geometry/source identity only; no joint response, acceptance, or release follows.",
        },
        "preserved_legacy_binding": {
            "old_steel_mesh_schema": mesh_report.get("schema"),
            "old_steel_mesh_scenario_id": mesh_report.get("scenario_id"),
            "old_input_hardware_inventory_sha256": mesh_report.get("input_bundle_inventory_sha256"),
            "old_WJ16_wood_mesh_bundle_sha256": legacy_wood_mesh_sha,
            "old_steel_mesh_archive_sha256": mesh_hashes["archive_sha256"],
            "old_steel_mesh_json_member_sha256": mesh_hashes["mesh_report_sha256"],
            "old_wood_fingerprint_was_modified": False,
        },
        "current_WJ24_binding": {
            "composition_sha256": wj24_static_hashes["composition.json"],
            "hardware_inventory_sha256": wj24_hardware_hashes["inventory.json"],
            "finished_wood_reconciliation_sha256": wj24_wood_hashes["reconciliation.json"],
            "finished_wood_STEP_identity_checks": wj24_step_solid_checks,
            "bridge_rule": "Keep the legacy WJ16 mesh fingerprint intact and add this source-derived identity record as a separate WJ24 binding.",
        },
        "identity_rules": {
            "axis_identity": "Exact OCC source-shape SHA-256 for each current WJ24 candidate bore equals the corresponding WJ16 occupancy-bore SHA-256; ordered receiver IDs also match. Coordinates and direction are separately recorded from the frozen WJ16 mechanics/profile datum.",
            "seat_identity": "WJ16 and WJ24 use the same candidate-bore solid identity; unchanged participant solids remain exact, while changed principal delta solids have bounding boxes disjoint from the full metal-stack envelope.",
            "principal_locality_test": "Conservative inclusive AABB disjointness against every exact added/removed delta solid reported by the source-bound WJ16-to-WJ24 OCC comparison.",
            "component_role_mapping": "One continuous bolt (head plus shaft), one head washer, one nut washer, and one nut per axis; legacy collision-role envelopes are metadata only.",
        },
        "counts_by_physical_role": role_counts,
        "modeled_hardware_profile": {
            "source_status": selected_geometry.get("status"),
            "dimension_choice": selected_geometry.get("dimension_choice"),
            "bolt": {
                key: selected_geometry.get("bolt", {}).get(key)
                for key in ("sku", "thread_designation", "nominal_length_mm", "smooth_body_diameter_mm", "body_diameter_range_mm", "head_height_mm", "head_across_corners_mm", "Lb_mm", "Lg_mm")
            },
            "washer": {
                key: selected_geometry.get("each_of_two_washers_per_bolt", {}).get(key)
                for key in ("inside_diameter_mm", "outside_diameter_mm", "thickness_mm", "candidate")
            },
            "nut": {
                key: selected_geometry.get("nut", {}).get(key)
                for key in ("sku", "thread_designation", "modeled_thickness_mm", "across_corners_mm", "smooth_basic_reference_bore_mm")
            },
            "sku_or_delivered_part_selected": False,
        },
        "source_sha256": input_hashes,
        "axes": report_rows,
    }


def write_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    identity_bytes = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    OUTPUT_PATH.write_bytes(identity_bytes)
    snapshot_path = OUTPUT_DIR / "producer.py.snapshot"
    snapshot_path.write_bytes(Path(__file__).read_bytes())
    index = {
        "README.md": _sha256_file(OUTPUT_DIR / "README.md"),
        "identity.json": _sha256(identity_bytes),
        "producer.py.snapshot": _sha256_file(snapshot_path),
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the new WJ24 identity report and hash index")
    args = parser.parse_args()
    report = build_identity_report()
    if args.write:
        write_report(report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "outcome": report["outcome"],
                "axis_count": len(report["axes"]),
                "physical_role_counts": report["counts_by_physical_role"],
                "legacy_WJ16_wood_fingerprint_preserved": report["preserved_legacy_binding"]["old_wood_fingerprint_was_modified"] is False,
                "report_path": str(OUTPUT_PATH.relative_to(ROOT)) if args.write else None,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
