"""Build and verify a source-bound inventory for the current WJ24 frame.

This is a read-only source and identity manifest producer. It consumes the
reviewed candidate records and the saved source-bound geometry/load screens;
it does not rebuild CAD, create a native model, infer a load path, or solve
mechanics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt01/current-full-frame-input-manifest.json"
)

CANDIDATE = "compact-floor-flush-wood-joints-development"
SELECTED_CANDIDATE = "compact-floor-flush-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
REVIEWED_COMMIT = "b1e8707d"
BASELINE_PROVENANCE_COMMIT = "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"

SOURCE_PATHS = {
    "candidate_authority": "wood-joints-candidate.json",
    "selected_authority": "current-candidate.json",
    "review_scene": "site/owner-wood-joints-wj24-scene.json",
    "review_report": "site/owner-wood-joints-review-report.json",
    "source_inventory": "docs/wood-joints-mvp/source-inventory.json",
    "geometry_snapshot": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json",
    "grip_screen": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json",
    "receiver_screen": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json",
    "contact_graph": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json",
    "retained_access_brep_manifest": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/brep-export/manifest.json",
    "load_cases": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json",
    "load_datums": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-datums.json",
    "material_scenarios": "docs/wood-joints-mvp/current-material-scenarios.md",
    "hardware_schedule": "docs/wood-joints-mvp/current-hardware-schedule.md",
    "panel_screw_contract": "docs/wood-joints-mvp/wj24-panel-screw-mechanics-contract.md",
    "criteria_register": "docs/wood-joints-mvp/current-criteria-coverage.md",
    "execution_plan": "docs/wood-joints-mvp/next-mvp-plan.md",
}

EXPECTED_SCENE_COUNTS = {
    "candidate_parts": 24,
    "candidate_bores": 92,
    "candidate_installed_hardware_axes": 92,
    "candidate_installed_hardware_components": 460,
    "fixed_panel_axes": 58,
    "moved_panel_axes": 8,
    "panel_screw_axes_total": 66,
    "retained_frame_bolts": 12,
    "retained_frame_bolt_installed_components": 60,
    "replaced_source_sds_axes": 144,
    "retained_legacy_sds_axes": 0,
    "retained_legacy_clips": 0,
}

EXPECTED_LOAD_CASE_IDS = {
    "a12-rear",
    "a12-forward",
    "a12-left",
    "k12-right",
    "k12-rear",
    "a1-rear",
}

EXPECTED_ROLE_IDS = {"head", "head_washer", "nut", "nut_washer", "shaft"}
FORCE_TOLERANCE_N = 1e-9
POINT_TOLERANCE_MM = 1e-9
MOMENT_TOLERANCE_N_MM = 1e-7


class ManifestError(ValueError):
    """Raised when current-source identity or count reconciliation fails."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    value = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ManifestError(f"{relative} must contain a JSON object")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _ids(rows: list[dict[str, Any]], field: str, label: str) -> set[str]:
    result = [row.get(field) for row in rows]
    _require(all(isinstance(item, str) and item for item in result), f"{label} has a missing {field}")
    _require(len(result) == len(set(result)), f"{label} has duplicate {field} values")
    return set(result)


def _set_equal(left: set[str], right: set[str], label: str) -> None:
    if left != right:
        only_left = sorted(left - right)
        only_right = sorted(right - left)
        raise ManifestError(
            f"{label} differ; only-left={only_left[:8]}, only-right={only_right[:8]}"
        )


def _vector(values: Any, label: str, dimension: int = 3) -> list[float]:
    if not isinstance(values, list) or len(values) != dimension:
        raise ManifestError(f"{label} must be a {dimension}-vector")
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ManifestError(f"{label} contains a non-finite number")
        result.append(float(value))
    return result


def _vectors_close(left: Any, right: Any, tolerance: float, label: str) -> float:
    a = _vector(left, f"{label} left")
    b = _vector(right, f"{label} right")
    error = max(abs(x - y) for x, y in zip(a, b, strict=True))
    if error > tolerance:
        raise ManifestError(f"{label} differs by {error:g}, tolerance {tolerance:g}")
    return error


def _cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _add_scaled(origin: list[float], direction: list[float], scale: float) -> list[float]:
    return [origin[i] + scale * direction[i] for i in range(3)]


def _check_hash_group(root: Path, group_id: str, expected: dict[str, str]) -> dict[str, Any]:
    rows = []
    for relative, expected_hash in sorted(expected.items()):
        path = root / relative
        if not path.is_file():
            actual_hash = None
            status = "missing"
        else:
            actual_hash = _sha256_file(path)
            status = "match" if actual_hash == expected_hash else "mismatch"
        rows.append(
            {
                "path": relative,
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
                "status": status,
            }
        )
    bad = [row for row in rows if row["status"] != "match"]
    _require(not bad, f"{group_id} has {len(bad)} missing or changed source file(s)")
    return {
        "group_id": group_id,
        "checked_count": len(rows),
        "matched_count": len(rows),
        "mismatches": [],
        "files": rows,
    }


def _check_load_contract(
    cases: dict[str, Any], datums: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Rebuild each applied wrench from the separate datum record and case input."""
    _require(cases.get("schema") == "wood_joint_current_load_case_contract/v1", "unknown load schema")
    _require(cases.get("candidate") == CANDIDATE, "load contract names a different candidate")
    _require(cases.get("geometry_revision_id") == REVISION, "load contract revision differs")
    payload = dict(cases)
    saved_contract_hash = payload.pop("contract_sha256", None)
    _require(saved_contract_hash == _sha256_bytes(_canonical_json(payload)), "load contract content hash differs")

    geometry = cases.get("current_geometry_inputs")
    _require(isinstance(geometry, dict), "load contract has no current geometry inputs")
    geometry_hash = _sha256_bytes(_canonical_json(geometry))
    _require(
        geometry_hash == cases.get("current_geometry_input_sha256"),
        "load contract geometry-input hash differs",
    )

    holds = datums.get("holds")
    _require(isinstance(holds, dict) and set(holds) == {"A12", "K12", "A1"}, "load datum hold inventory differs")
    face_points = {key: value["face_datum_global_mm"] for key, value in holds.items()}
    midplane_points = {key: value["panel_midplane_reference_global_mm"] for key, value in holds.items()}
    normals = {key: value["outward_normal_global"] for key, value in holds.items()}
    _require(face_points == geometry.get("hold_face_datums_global_xyz_mm"), "load contract face datums differ from explicit datum artifact")
    _require(
        midplane_points == geometry.get("panel_midplane_applicationpoints_global_xyz_mm"),
        "load contract panel reference points differ from explicit datum artifact",
    )
    shared_normal = _vector(geometry.get("panel_outward_normal_global_xyz"), "panel normal")
    for hold_id, normal in normals.items():
        _vectors_close(normal, shared_normal, POINT_TOLERANCE_MM, f"{hold_id} panel normal")

    load_basis = cases.get("load_basis")
    _require(isinstance(load_basis, dict), "load contract has no load basis")
    pounds = float(load_basis["pounds"])
    dynamic_factor = float(load_basis["dynamic_factor"])
    pounds_to_kg = float(load_basis["pounds_to_kg"])
    gravity = float(load_basis["gravity_m_per_s2"])
    patch_size = float(load_basis["patch_size_mm"])
    standoff_mm = float(load_basis["standoff_mm"])
    vertical_force = -(pounds * dynamic_factor * pounds_to_kg * gravity)
    _require(abs(vertical_force - float(load_basis["vertical_force_global_z_n"])) <= FORCE_TOLERANCE_N,
             "vertical force does not reconstruct from the source-bound load basis")

    raw_cases = cases.get("cases")
    _require(isinstance(raw_cases, list) and len(raw_cases) == 6, "load contract must contain six cases")
    ids = _ids(raw_cases, "case_id", "load cases")
    _require(ids == EXPECTED_LOAD_CASE_IDS, "load case IDs differ from the reviewed six-case contract")

    output = []
    max_force_error = 0.0
    max_point_error = 0.0
    max_moment_error = 0.0
    for case in raw_cases:
        case_id = case["case_id"]
        hold_id = case.get("hold_id")
        _require(hold_id in holds, f"{case_id} references an unknown hold datum")
        inputs = case.get("case_inputs")
        _require(isinstance(inputs, dict), f"{case_id} lacks explicit case inputs")
        horizontal = _vector(
            inputs.get("horizontal_force_global_xy_n"), f"{case_id} horizontal force", dimension=2
        )
        _require(float(inputs.get("pounds")) == pounds, f"{case_id} changes the pounds basis")
        _require(float(inputs.get("dynamic_factor")) == dynamic_factor, f"{case_id} changes the dynamic factor")

        expected_force = [horizontal[0], horizontal[1], vertical_force]
        face = _vector(face_points[hold_id], f"{case_id} face datum")
        reference = _vector(midplane_points[hold_id], f"{case_id} panel reference")
        expected_point = _add_scaled(face, shared_normal, standoff_mm)
        actual_force = case.get("applied_force_global_xyz_n")
        actual_point = case.get("standoff", {}).get("force_application_point_global_xyz_mm")
        max_force_error = max(
            max_force_error,
            _vectors_close(actual_force, expected_force, FORCE_TOLERANCE_N, f"{case_id} applied force"),
            _vectors_close(case.get("applied_wrench", {}).get("force_global_xyz_n"), expected_force,
                           FORCE_TOLERANCE_N, f"{case_id} wrench force"),
        )
        max_point_error = max(
            max_point_error,
            _vectors_close(case.get("panel_patch", {}).get("center_global_xyz_mm"), face,
                           POINT_TOLERANCE_MM, f"{case_id} patch center"),
            _vectors_close(actual_point, expected_point, POINT_TOLERANCE_MM, f"{case_id} standoff point"),
            _vectors_close(case.get("panel_midplane_applicationpoint_global_xyz_mm"), reference,
                           POINT_TOLERANCE_MM, f"{case_id} panel datum"),
            _vectors_close(case.get("applied_wrench", {}).get("reference_point_global_xyz_mm"), reference,
                           POINT_TOLERANCE_MM, f"{case_id} wrench reference"),
        )
        expected_moment = _cross(
            [expected_point[i] - reference[i] for i in range(3)], expected_force
        )
        max_moment_error = max(
            max_moment_error,
            _vectors_close(
                case.get("moment_about_panel_midplane_applicationpoint_global_xyz_nmm"),
                expected_moment,
                MOMENT_TOLERANCE_N_MM,
                f"{case_id} moment",
            ),
            _vectors_close(
                case.get("applied_wrench", {}).get("moment_global_xyz_nmm"),
                expected_moment,
                MOMENT_TOLERANCE_N_MM,
                f"{case_id} wrench moment",
            ),
        )
        output.append(
            {
                "case_id": case_id,
                "hold_id": hold_id,
                "case_inputs": inputs,
                "applied_force_global_xyz_n": expected_force,
                "patch_size_mm": patch_size,
                "patch_center_global_xyz_mm": face,
                "force_application_point_global_xyz_mm": expected_point,
                "wrench_reference_point_global_xyz_mm": reference,
                "moment_global_xyz_nmm": expected_moment,
                "input_type": "source_bound_applied_force_and_wrench_only",
                "reactions_or_joint_demands": False,
            }
        )

    return output, {
        "method": "independent cross-product and force-basis reconstruction from current-load-datums.json and case_inputs",
        "case_count": len(output),
        "case_ids": sorted(ids),
        "max_force_component_residual_n": max_force_error,
        "max_point_component_residual_mm": max_point_error,
        "max_moment_component_residual_n_mm": max_moment_error,
        "tolerances": {
            "force_n": FORCE_TOLERANCE_N,
            "point_mm": POINT_TOLERANCE_MM,
            "moment_n_mm": MOMENT_TOLERANCE_N_MM,
        },
        "result": "pass_applied_input_reconstruction_only",
    }


def _axis_member_pairs(row: dict[str, Any]) -> list[dict[str, Any]]:
    return row.get("member_pair_associations", [])


def build_manifest(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    source = {key: _read_json(root, path) for key, path in SOURCE_PATHS.items()
              if path.endswith(".json")}
    candidate = source["candidate_authority"]
    selected = source["selected_authority"]
    scene = source["review_scene"]
    report = source["review_report"]
    source_inventory = source["source_inventory"]
    snapshot = source["geometry_snapshot"]
    grip = source["grip_screen"]
    receiver = source["receiver_screen"]
    graph = source["contact_graph"]
    retained_access_export = source["retained_access_brep_manifest"]
    load_cases = source["load_cases"]
    load_datums = source["load_datums"]

    current_revision = candidate.get("current_development_revision", {})
    _require(candidate.get("candidate") == CANDIDATE, "wood-joints-candidate.json names a different candidate")
    _require(selected.get("candidate") == SELECTED_CANDIDATE, "selected-candidate authority changed")
    _require(candidate.get("authority", {}).get("selected_candidate") == SELECTED_CANDIDATE,
             "development lane no longer points to the selected authority")
    _require(current_revision.get("revision_id") == REVISION, "candidate authority revision differs")
    _require(current_revision.get("reviewed_repository_commit") == REVIEWED_COMMIT,
             "reviewed repository commit differs")
    _require(current_revision.get("release") is False, "development revision must remain unreleased")
    _require(report.get("revision_id") == REVISION, "review report revision differs")
    _require(report.get("status") == "unaccepted_viewer_geometry_revision", "review report status differs")
    _require(report.get("joint_evaluations_run") is False, "review report unexpectedly claims joint evaluations")
    _require(scene.get("candidate") == CANDIDATE and scene.get("revision_id") == REVISION,
             "review scene identity differs")
    _require(snapshot.get("revision_id") == REVISION, "geometry snapshot revision differs")
    _require(grip.get("revision_id") == REVISION, "grip screen revision differs")
    _require(receiver.get("revision_id") == REVISION, "receiver screen revision differs")
    _require(graph.get("revision_id") == REVISION, "contact graph revision differs")

    # An existing exact STEP bundle covers the retained-bolt access-study
    # state only. Bind and reconcile its actual contents without treating it
    # as a full-frame geometry export.
    _require(retained_access_export.get("schema") == "wood_joint_wj24_d6_member_brep_export/v1",
             "retained-bolt access STEP export schema differs")
    _require(retained_access_export.get("status") == "exact_source_brep_bundle_for_future_d6_screen_only",
             "retained-bolt access STEP export scope differs")
    _require(retained_access_export.get("geometry_revision_id") == REVISION and
             retained_access_export.get("geometry_trial_id") == REVISION,
             "retained-bolt access STEP export revision differs")
    _require(retained_access_export.get("reviewed_repository_commit") == REVIEWED_COMMIT,
             "retained-bolt access STEP export reviewed commit differs")
    _require(retained_access_export.get("actual_product_or_tool_validation") is False,
             "retained-bolt access STEP export unexpectedly claims product/tool validation")

    scene_binding = scene.get("source_binding", {})
    scene_path = SOURCE_PATHS["review_scene"]
    report_path = SOURCE_PATHS["review_report"]
    source_inventory_path = SOURCE_PATHS["source_inventory"]
    _require(scene_binding.get("revision_report_sha256") == _sha256_file(root / report_path),
             "review scene report source hash differs")
    _require(scene_binding.get("source_inventory_sha256") == _sha256_file(root / source_inventory_path),
             "review scene source-inventory hash differs")
    snapshot_sources = snapshot.get("source_sha256", {})
    _require(isinstance(snapshot_sources, dict), "geometry snapshot source hash map is missing")
    for path, expected_hash in snapshot_sources.items():
        _require((root / path).is_file(), f"geometry snapshot source is missing: {path}")
        _require(_sha256_file(root / path) == expected_hash, f"geometry snapshot source hash differs: {path}")
    _require(grip.get("geometry_snapshot_path") == SOURCE_PATHS["geometry_snapshot"],
             "grip screen geometry snapshot path differs")
    _require(grip.get("geometry_snapshot_sha256") == _sha256_file(root / SOURCE_PATHS["geometry_snapshot"]),
             "grip screen geometry snapshot hash differs")
    _require(grip.get("scene_report_path") == report_path and
             grip.get("scene_report_sha256") == _sha256_file(root / report_path),
             "grip screen review report binding differs")

    scene_counts = scene.get("counts", {})
    snapshot_counts = snapshot.get("counts", {})
    _require(scene_counts == snapshot_counts, "scene and geometry snapshot count maps differ")
    for key, expected in EXPECTED_SCENE_COUNTS.items():
        _require(scene_counts.get(key) == expected, f"scene count {key} is not {expected}")
    _require(scene.get("release", {}) and all(value is False for value in scene["release"].values()),
             "review scene release flags must remain false")
    _require(candidate.get("release_flags", {}) and
             all(value is False for value in candidate["release_flags"].values()),
             "development candidate release flags must remain false")

    model_inventory = scene.get("model_inventory", {})
    scene_candidate_axes = model_inventory.get("candidate_axes", {})
    scene_candidate_parts = model_inventory.get("candidate_parts", {})
    fixed_panel_ids = set(model_inventory.get("fixed_panel_axes", []))
    moved_panel_rows = model_inventory.get("moved_panel_axes", [])
    moved_panel_ids = _ids(moved_panel_rows, "axis_id", "scene moved panel axes")
    scene_frame_rows = model_inventory.get("starting_frame_bolts", [])
    source_part_rows = source_inventory.get("parts", [])
    source_panel_rows = source_inventory.get("fixed_panel_kicker_screws", [])
    source_frame_rows = source_inventory.get("starting_frame_bolts", [])
    graph_inventories = graph.get("inventories", {})
    snapshot_axes = snapshot.get("axes", {})
    snapshot_members = snapshot.get("members", {})
    grip_rows = grip.get("axes", [])
    receiver_rows = receiver.get("axes", [])
    physical_member_rows = graph_inventories.get("physical_members", [])
    graph_candidate_rows = graph_inventories.get("candidate_bolt_axes", [])
    graph_panel_rows = graph_inventories.get("current_panel_screw_axes", [])
    graph_frame_rows = graph_inventories.get("retained_frame_bolts", [])

    source_part_ids = _ids(source_part_rows, "part_id", "source-inventory parts")
    candidate_part_ids = set(scene_candidate_parts)
    _require(len(candidate_part_ids) == 24, "scene candidate part ID count differs")
    graph_member_ids = _ids(physical_member_rows, "member_id", "contact graph physical members")
    _set_equal(source_part_ids | candidate_part_ids, graph_member_ids,
               "source parts + candidate blocks versus contact graph members")
    snapshot_member_ids = set(snapshot_members)
    _require(len(snapshot_member_ids) == 40, "geometry snapshot changed-body count differs")
    _set_equal(snapshot_member_ids & source_part_ids, snapshot_member_ids - candidate_part_ids,
               "snapshot shared-source body IDs versus non-candidate snapshot IDs")
    _require(snapshot_member_ids <= (source_part_ids | candidate_part_ids),
             "geometry snapshot contains an unknown member")
    _set_equal(snapshot_member_ids - source_part_ids, candidate_part_ids,
               "geometry snapshot candidate block IDs")

    candidate_axis_ids = set(scene_candidate_axes)
    _require(len(candidate_axis_ids) == 92, "scene candidate bolt-axis count differs")
    _set_equal(candidate_axis_ids, set(snapshot_axes), "scene versus geometry snapshot candidate axes")
    _set_equal(candidate_axis_ids, _ids(grip_rows, "axis_id", "grip screen axes"),
               "scene versus grip screen candidate axes")
    _set_equal(candidate_axis_ids, _ids(graph_candidate_rows, "axis_id", "contact graph candidate axes"),
               "scene versus contact graph candidate axes")
    _require(grip.get("candidate_axis_count") == 92, "grip screen candidate axis count differs")

    panel_source_ids = _ids(source_panel_rows, "axis_id", "source panel/kicker screw axes")
    panel_receiver_ids = _ids(receiver_rows, "axis_id", "current receiver panel/kicker axes")
    panel_graph_ids = _ids(graph_panel_rows, "axis_id", "contact graph panel/kicker axes")
    _set_equal(panel_source_ids, panel_receiver_ids, "source panel IDs versus current receiver screen")
    _set_equal(panel_source_ids, panel_graph_ids, "source panel IDs versus contact graph")
    _set_equal(fixed_panel_ids | moved_panel_ids, panel_source_ids,
               "scene 58 fixed + 8 moved panel axes versus source IDs")
    _require(len(fixed_panel_ids) == 58 and len(moved_panel_ids) == 8,
             "scene panel/kicker split is not 58 unchanged plus 8 moved")
    _require(not (fixed_panel_ids & moved_panel_ids), "scene fixed and moved panel IDs overlap")
    _require(receiver.get("counts", {}).get("panel_kicker_axes_total") == 66 and
             receiver.get("counts", {}).get("unchanged_source_station_axes") == 58 and
             receiver.get("counts", {}).get("moved_axes") == 8,
             "receiver screen panel axis count split differs")

    frame_scene_ids = _ids(scene_frame_rows, "axis_id", "scene starting frame bolts")
    frame_source_ids = _ids(source_frame_rows, "axis_id", "source starting frame bolts")
    frame_graph_ids = _ids(graph_frame_rows, "axis_id", "contact graph retained frame bolts")
    _set_equal(frame_scene_ids, frame_source_ids, "scene versus source-inventory retained frame bolts")
    _set_equal(frame_scene_ids, frame_graph_ids, "scene versus contact graph retained frame bolts")
    _require(len(frame_scene_ids) == 12, "retained frame-bolt count differs")

    brep_files = retained_access_export.get("files", [])
    _require(isinstance(brep_files, list), "retained-bolt access STEP file list is missing")
    brep_paths = [row.get("path") for row in brep_files]
    brep_shape_ids = _ids(brep_files, "shape_id", "retained-bolt access STEP shapes")
    _require(all(isinstance(path, str) and path.endswith(".step") for path in brep_paths),
             "retained-bolt access export has a missing or non-STEP path")
    _require(len(brep_paths) == len(set(brep_paths)), "retained-bolt access export has duplicate paths")
    brep_categories = Counter(row.get("category") for row in brep_files)
    exported_counts = retained_access_export.get("exported_counts", {})
    _require(brep_categories == Counter({"timber": 20, "retained_frame_bolt_roles": 60,
                                        "modeled_wires": 131}),
             "retained-bolt access STEP category counts differ")
    _require(exported_counts == {
        "modeled_wire_shapes": 131,
        "original_timber_member_shapes": 20,
        "retained_frame_bolt_physical_roles": 60,
        "retained_frame_bolt_stacks": 12,
        "step_files": 211,
    }, "retained-bolt access STEP exported count map differs")
    _require(len(brep_files) == exported_counts.get("step_files"),
             "retained-bolt access STEP total differs from declared file count")
    export_dir = str(Path(SOURCE_PATHS["retained_access_brep_manifest"]).parent)
    brep_hashes = {}
    for row in brep_files:
        relative_path = row["path"]
        _require(not Path(relative_path).is_absolute() and ".." not in Path(relative_path).parts,
                 f"retained-bolt access STEP path escapes its bundle: {relative_path}")
        _require(isinstance(row.get("sha256"), str) and len(row["sha256"]) == 64,
                 f"retained-bolt access STEP has an invalid hash: {relative_path}")
        _require(isinstance(row.get("bytes"), int) and row["bytes"] > 0,
                 f"retained-bolt access STEP has an invalid byte count: {relative_path}")
        brep_hashes[f"{export_dir}/{relative_path}"] = row["sha256"]
    brep_timber_ids = {row["shape_id"] for row in brep_files if row.get("category") == "timber"}
    source_timber_ids = {row["part_id"] for row in source_part_rows if row.get("kind") == "timber"}
    _set_equal(brep_timber_ids, source_timber_ids,
               "retained-bolt access STEP timber shapes versus preserved source timber IDs")
    role_ids = {row["shape_id"] for row in brep_files if row.get("category") == "retained_frame_bolt_roles"}
    role_pairs = [shape_id.rsplit("/", 1) for shape_id in role_ids]
    _require(all(len(pair) == 2 and pair[1] in EXPECTED_ROLE_IDS for pair in role_pairs),
             "retained-bolt access STEP role names differ")
    roles_by_axis: dict[str, set[str]] = {}
    for axis_id, role_id in role_pairs:
        roles_by_axis.setdefault(axis_id, set()).add(role_id)
    _require(set(roles_by_axis) == frame_scene_ids,
             "retained-bolt access STEP stack axes differ from the current 12 retained frame bolts")
    _require(all(roles == EXPECTED_ROLE_IDS for roles in roles_by_axis.values()),
             "retained-bolt access STEP role set differs for a retained frame bolt")
    omitted = retained_access_export.get("omitted_state_shapes", {})
    _require("current_candidate_connector_bodies" in omitted and
             "panels_and_66_panel_screw_axes" in omitted,
             "retained-bolt access STEP omitted-state declaration is incomplete")

    export_source_hashes = retained_access_export.get("source_sha256", {})
    _require(isinstance(export_source_hashes, dict), "retained-bolt access STEP source hashes are missing")
    for source_path, expected_hash in export_source_hashes.items():
        _require((root / source_path).is_file(), f"retained-bolt access STEP source is missing: {source_path}")
        _require(_sha256_file(root / source_path) == expected_hash,
                 f"retained-bolt access STEP source hash differs: {source_path}")
    _require(retained_access_export.get("source_inventory_sha256") ==
             _sha256_file(root / SOURCE_PATHS["source_inventory"]),
             "retained-bolt access STEP source-inventory fingerprint differs")
    _require(retained_access_export.get("source_inventory_runtime_module_sha256") ==
             source_inventory.get("source_runtime_module_hashes_sha256"),
             "retained-bolt access STEP runtime module pins differ from the source inventory")
    _require(retained_access_export.get("frozen_geometry_report_sha256_canonical_json") ==
             _sha256_bytes(_canonical_json(snapshot)),
             "retained-bolt access STEP canonical geometry-snapshot fingerprint differs")

    candidate_axis_by_id = {row["axis_id"]: row for row in grip_rows}
    graph_candidate_by_id = {row["axis_id"]: row for row in graph_candidate_rows}
    candidate_axes = []
    for axis_id in sorted(candidate_axis_ids):
        scene_row = scene_candidate_axes[axis_id]
        geometry_row = snapshot_axes[axis_id]
        grip_row = candidate_axis_by_id[axis_id]
        graph_row = graph_candidate_by_id[axis_id]
        roles = set(scene_row.get("installed_component_roles", []))
        role_ids = set(scene_row.get("installed_role_ids", []))
        _require(roles == EXPECTED_ROLE_IDS and role_ids == EXPECTED_ROLE_IDS,
                 f"candidate axis {axis_id} role inventory differs")
        receiver_ids = set(scene_row.get("receiver_ids", []))
        _require(receiver_ids == set(geometry_row.get("receiver_ids", [])),
                 f"candidate axis {axis_id} receiver IDs differ between scene and snapshot")
        _require(receiver_ids == set(grip_row.get("ordered_receiver_ids_head_to_nut", [])),
                 f"candidate axis {axis_id} receiver IDs differ in grip screen")
        candidate_axes.append(
            {
                "axis_id": axis_id,
                "station_id": scene_row.get("station_id"),
                "family": scene_row.get("family"),
                "trial_id": scene_row.get("trial_id"),
                "receiver_member_ids": sorted(receiver_ids),
                "scene_modeled_component_role_ids": sorted(role_ids),
                "geometry": {
                    "shaft_center_global_xyz_mm": geometry_row.get("shaft_center_xyz_mm"),
                    "axis_head_to_nut_global": geometry_row.get("axis_head_to_nut_global"),
                    "modeled_shaft_diameter_mm": geometry_row.get("shaft_diameter_mm"),
                    "modeled_shaft_occupied_length_mm": grip_row.get("modeled_shaft_occupied_length_mm"),
                    "modeled_underhead_to_tip_mm": grip_row.get("modeled_underhead_to_tip_mm"),
                    "wood_receiver_intervals": grip_row.get("wood_receiver_intervals"),
                    "wood_grip_material_length_mm": grip_row.get("wood_grip_material_length_mm"),
                    "modeled_shaft_covers_all_raw_receiver_intervals": grip_row.get(
                        "modeled_shaft_covers_all_raw_receiver_intervals"
                    ),
                },
                "geometric_member_pair_associations": _axis_member_pairs(graph_row),
                "member_order_limit": graph_row.get("member_order_semantics") or
                    "The geometric association does not establish physical head-to-nut stack order.",
                "hardware_status": "modeled CAD roles only; product and delivered dimensions unselected/unverified",
                "length_status": "modeled occupancy envelope; not a purchase length or delivered shank",
            }
        )

    source_panel_by_id = {row["axis_id"]: row for row in source_panel_rows}
    panel_screen_by_id = {row["axis_id"]: row for row in receiver_rows}
    panel_graph_by_id = {row["axis_id"]: row for row in graph_panel_rows}
    moved_by_id = {row["axis_id"]: row for row in moved_panel_rows}
    panel_axes = []
    for axis_id in sorted(panel_source_ids):
        row = panel_screen_by_id[axis_id]
        _require(row.get("purchased_product_policy", "").startswith("Hillman 42605"),
                 f"panel screw axis {axis_id} lost the Hillman 42605 policy")
        _require(row.get("purchased_length_mm") == 63.5,
                 f"panel screw axis {axis_id} has a different nominal purchased length")
        _require(panel_graph_by_id[axis_id].get("receiver_member") == row.get("receiver_member"),
                 f"panel screw axis {axis_id} receiver differs between current screens")
        panel_axes.append(
            {
                "axis_id": axis_id,
                "panel_member": row.get("panel_member"),
                "receiver_member": row.get("receiver_member"),
                "previous_receiver_member": row.get("previous_receiver_member"),
                "origin_global_xyz_mm": row.get("origin_global_xyz_mm"),
                "axis_global_xyz": row.get("axis_global_xyz"),
                "translation_from_source_xyz_mm": row.get("translation_from_source_xyz_mm"),
                "current_location_status": row.get("current_location_status"),
                "purchased_policy": row.get("purchased_product_policy"),
                "purchased_nominal_length_mm": row.get("purchased_length_mm"),
                "historical_source_inventory_record": {
                    "source_receiver_member": source_panel_by_id[axis_id].get("source_finished_receiver_member"),
                    "candidate_receiver_member": source_panel_by_id[axis_id].get("candidate_finished_receiver_member"),
                    "source_occupied_length_mm": source_panel_by_id[axis_id].get("source_occupied_length_mm"),
                },
                "receiver_screen": {
                    "raw_receiver_axis_envelope_intersects": row.get("raw_receiver_axis_envelope_intersects"),
                    "finished_receiver_axis_envelope_clear": row.get("finished_receiver_axis_envelope_clear"),
                },
                "owner_moved_axis_record": moved_by_id.get(axis_id),
                "hardware_status": "purchased policy retained; no receiving, installation, or screw resistance result",
            }
        )

    source_frame_by_id = {row["axis_id"]: row for row in source_frame_rows}
    graph_frame_by_id = {row["axis_id"]: row for row in graph_frame_rows}
    scene_frame_by_id = {row["axis_id"]: row for row in scene_frame_rows}
    frame_axes = []
    for axis_id in sorted(frame_scene_ids):
        a = scene_frame_by_id[axis_id]
        b = source_frame_by_id[axis_id]
        g = graph_frame_by_id[axis_id]
        _vectors_close(a.get("origin_global_xyz_mm"), b.get("origin_global_xyz_mm"), POINT_TOLERANCE_MM,
                       f"retained bolt {axis_id} scene/source origin")
        _vectors_close(a.get("axis_global_xyz"), b.get("axis_global_xyz"), POINT_TOLERANCE_MM,
                       f"retained bolt {axis_id} scene/source axis")
        frame_axes.append(
            {
                "axis_id": axis_id,
                "members_as_recorded": b.get("members"),
                "origin_global_xyz_mm": b.get("origin_global_xyz_mm"),
                "axis_global_xyz": b.get("axis_global_xyz"),
                "source_occupied_diameter_mm": b.get("source_occupied_diameter_mm"),
                "source_occupied_length_mm": b.get("source_occupied_length_mm"),
                "source_nominal_length_mm": b.get("source_nominal_length_mm"),
                "source_grip_mm": b.get("source_grip_mm"),
                "modeled_component_count": a.get("installed_component_count"),
                "candidate_recheck_status": a.get("candidate_recheck_status"),
                "geometric_member_pair_associations": _axis_member_pairs(g),
                "hardware_status": "retained starting bolt arrangement; current candidate recheck required; no product/receiving validation",
            }
        )

    source_parts_by_id = {row["part_id"]: row for row in source_part_rows}
    graph_members_by_id = {row["member_id"]: row for row in physical_member_rows}
    report_replay = report.get("candidate_part_replay", {})
    member_records = []
    for member_id in sorted(graph_member_ids):
        graph_row = graph_members_by_id[member_id]
        source_row = source_parts_by_id.get(member_id)
        snapshot_row = snapshot_members.get(member_id)
        member_records.append(
            {
                "member_id": member_id,
                "member_kind": graph_row.get("member_kind"),
                "composition_roles": graph_row.get("composition_roles", []),
                "graph_raw_geometry_summary": graph_row.get("raw"),
                "graph_finished_geometry_summary": graph_row.get("finished"),
                "source_part_provenance": None if source_row is None else {
                    "source_candidate": source_inventory.get("source_candidate"),
                    "source_commit": source_inventory.get("source_commit"),
                    "source_shape_sha256": source_row.get("source_shape_sha256"),
                    "source_shape_record_sha256": source_row.get("source_shape_record_sha256"),
                    "delivered_stock_observed": source_row.get("delivered_stock_observed"),
                    "current_finished_shape_hash_claim": False,
                },
                "reviewed_snapshot_summary": snapshot_row,
                "owner_report_finished_shape_sha256": report_replay.get(member_id, {}).get(
                    "finished_shape_sha256"
                ),
                "exact_current_finished_brep_or_step_available_in_manifest_sources": False,
            }
        )

    graph_counts = graph.get("counts", {})
    edge_states = Counter(edge.get("geometry_state") for edge in graph.get("edges", []))
    edge_pair_ids = [tuple(sorted(edge.get("member_ids", []))) for edge in graph.get("edges", [])]
    _require(len(edge_pair_ids) == len(set(edge_pair_ids)), "contact graph contains duplicate member pairs")
    _require(graph_counts.get("physical_member_nodes") == 50 and len(physical_member_rows) == 50,
             "contact graph physical member count differs")
    _require(graph_counts.get("unique_member_pairs") == 1225 and len(edge_pair_ids) == 1225,
             "contact graph member pair count differs")
    _require(edge_states == Counter({"separated": 1104, "finite_opposed_planar_touch": 115,
                                    "zero_area_touch_or_unresolved": 6}),
             "contact graph geometry state totals differ")
    _require(sum(float(edge.get("common_volume_mm3", 0.0)) > 0 for edge in graph["edges"]) == 0,
             "contact graph reports positive-volume member overlap")

    reconstructed_cases, load_audit = _check_load_contract(load_cases, load_datums)
    _require(load_datums.get("revision_id") == REVISION, "explicit load datum revision differs")

    hash_groups = []
    graph_source_hashes = graph.get("source_sha256", {}).get("geometry_source_inputs_sha256", {})
    _require(isinstance(graph_source_hashes, dict), "contact graph geometry source hash map missing")
    hash_groups.append(_check_hash_group(root, "contact_graph_geometry_source_inputs", graph_source_hashes))
    hash_groups.append(_check_hash_group(root, "source_inventory_data_sources",
                                         source_inventory.get("source_hashes_sha256", {})))
    hash_groups.append(_check_hash_group(root, "source_inventory_runtime_modules",
                                         source_inventory.get("source_runtime_module_hashes_sha256", {})))
    load_hashes = {
        path: record.get("sha256")
        for path, record in load_cases.get("source_provenance", {}).get("files", {}).items()
    }
    hash_groups.append(_check_hash_group(root, "current_load_contract_sources", load_hashes))
    datum_hashes = load_datums.get("source_sha256", {})
    _require(isinstance(datum_hashes, dict), "load datum source hash map missing")
    hash_groups.append(_check_hash_group(root, "current_load_datum_sources", datum_hashes))
    hash_groups.append(_check_hash_group(root, "retained_bolt_access_step_bundle", brep_hashes))

    _require(
        graph.get("source_sha256", {}).get("source_inventory_sha256") ==
        _sha256_file(root / source_inventory_path),
        "contact graph source inventory fingerprint differs",
    )
    _require(
        graph.get("source_sha256", {}).get("frozen_revision_report_canonical_json_sha256") ==
        scene_binding.get("revision_report_canonical_content_sha256"),
        "contact graph and scene revision-report canonical hashes differ",
    )

    direct_artifacts = []
    for key, relative in sorted(SOURCE_PATHS.items()):
        path = root / relative
        _require(path.is_file(), f"direct source artifact missing: {relative}")
        direct_artifacts.append(
            {
                "artifact_id": key,
                "path": relative,
                "sha256": _sha256_file(path),
                "role": {
                    "candidate_authority": "separate wood-joint development lane and reviewed revision authority",
                    "selected_authority": "selected candidate identity only; not imported as a mechanics result",
                    "review_scene": "owner-reviewed geometry and count authority for the current revision",
                    "review_report": "owner-reviewed geometry revision report; it says no joint evaluations were run",
                    "source_inventory": "preserved source-member/panel identity and provenance; source_commit is historical baseline provenance",
                    "geometry_snapshot": "40-body geometric summary and 92-axis inventory; not exact full-frame BRep/STEP solids",
                    "grip_screen": "92-axis nominal modeled grip/role screen",
                    "receiver_screen": "current 66-axis receiver mapping and nominal panel-screw geometry screen",
                    "contact_graph": "50-node/1225-pair geometric relationship inventory only",
                    "retained_access_brep_manifest": "hashed exact STEP export for the retained-bolt D6 access-study state; candidate blocks/connectors, panels, and 66 panel-screw axes are explicitly omitted",
                    "load_cases": "six source-bound applied-force/wrench inputs, not reactions or joint demands",
                    "load_datums": "explicit current global hold-face/panel reference datums",
                    "material_scenarios": "conditional elastic scenarios; no exact per-body material map or received stock properties",
                    "hardware_schedule": "count and open product/specification record; no complete selected/delivered BOM",
                    "panel_screw_contract": "retained 66-screw policy boundary; no inferred screw strength",
                    "criteria_register": "current unresolved criterion/obligation map",
                    "execution_plan": "MVP-E sequence and evidence requirements",
                }[key],
            }
        )

    source_part_kinds = Counter(row.get("kind") for row in source_part_rows)
    moved_axis_records = [moved_by_id[axis_id] for axis_id in sorted(moved_panel_ids)]
    current_load_case_sha = _sha256_file(root / SOURCE_PATHS["load_cases"])
    load_contract_hash = load_cases.get("contract_sha256")

    manifest: dict[str, Any] = {
        "schema": "wood_joint_current_full_frame_input_manifest/v1",
        "manifest_id": "current-full-frame-input-manifest-attempt01",
        "candidate": CANDIDATE,
        "selected_candidate_authority_preserved": SELECTED_CANDIDATE,
        "geometry_revision_id": REVISION,
        "reviewed_repository_commit": REVIEWED_COMMIT,
        "status": "entity_inventory_complete_inputs_not_ready",
        "scope": {
            "purpose": "Source-bound identity and input inventory for planning the reviewed WJ24 full-frame six-case analysis.",
            "included": [
                "current candidate/member identities and source-bound geometric summaries",
                "all 92 candidate bolt axes, 12 retained starting frame-bolt axes, and 66 panel/kicker screw axes",
                "the 50-member and 1,225-pair nominal geometric contact graph",
                "six source-bound applied load cases reconstructed from the separate explicit datum artifact",
                "current material, hardware, contact, boundary, and receiving-data status",
            ],
            "excluded": [
                "native or CAD rebuilds, mesh generation, boundary-condition implementation, or solver execution",
                "reactions, member forces, connection/fastener demands, force sharing, stiffness, resistance, utilization, or criterion disposition",
                "selection/receipt/conformance of structural hardware or inspection of wood, cuts, screws, panels, wiring, pads, or floor",
            ],
            "inventory_complete_definition": (
                "Every current physical-member ID, current axis ID, and current load-case ID in the declared scope reconciles across its independent source records and stated counts. This does not mean exact finished solids or solver inputs are ready."
            ),
        },
        "authority_and_provenance": {
            "development_authority_path": SOURCE_PATHS["candidate_authority"],
            "development_candidate": CANDIDATE,
            "reviewed_revision": REVISION,
            "reviewed_commit": REVIEWED_COMMIT,
            "selected_authority_path": SOURCE_PATHS["selected_authority"],
            "selected_candidate": SELECTED_CANDIDATE,
            "selected_candidate_role": "Authority remains selected; this development manifest does not change or requalify it.",
            "preserved_source_inventory_commit": source_inventory.get("source_commit"),
            "source_inventory_commit_role": (
                "Provenance for the selected-baseline source-member records. It is not the current WJ24 implementation commit and transfers no historical structural result."
            ),
            "scene_status": scene.get("layout_status"),
            "report_status": report.get("status"),
            "joint_evaluations_run_in_review_report": report.get("joint_evaluations_run"),
            "release_flags": {
                "development_contract": candidate.get("release_flags"),
                "review_scene": scene.get("release"),
                "geometry_snapshot": snapshot.get("release"),
            },
        },
        "coordinate_and_unit_contract": {
            "global_frame": "global XYZ",
            "geometry_units": "mm",
            "force_units": "N",
            "moment_units": "N mm",
            "preserved_source_frame": source_inventory.get("coordinate_contract"),
            "grain_note": "Source-frame T is a coordinate axis and is not automatically material tangential grain; grain and R/T orientation remain per-body analysis inputs.",
        },
        "inventory_counts": {
            "source_member_and_panel_parts": len(source_part_ids),
            "source_timber_members": source_part_kinds.get("timber", 0),
            "source_plywood_panels": source_part_kinds.get("plywood_panel", 0),
            "candidate_blocks": len(candidate_part_ids),
            "full_physical_member_nodes": len(graph_member_ids),
            "snapshot_changed_body_summaries": len(snapshot_member_ids),
            "snapshot_shared_source_members": len(snapshot_member_ids & source_part_ids),
            "snapshot_candidate_blocks": len(snapshot_member_ids - source_part_ids),
            "candidate_bolt_axes": len(candidate_axis_ids),
            "candidate_modeled_hardware_component_roles": scene_counts["candidate_installed_hardware_components"],
            "retained_starting_frame_bolt_axes": len(frame_scene_ids),
            "retained_frame_modeled_hardware_component_roles": scene_counts["retained_frame_bolt_installed_components"],
            "panel_kicker_screw_axes": len(panel_source_ids),
            "panel_axes_unchanged": len(fixed_panel_ids),
            "panel_axes_owner_moved": len(moved_panel_ids),
            "replaced_historical_SDS_axes_removed_from_candidate": scene_counts["replaced_source_sds_axes"],
            "current_applied_load_cases": len(reconstructed_cases),
            "unique_physical_member_pairs_in_graph": graph_counts["unique_member_pairs"],
        },
        "physical_members": member_records,
        "candidate_blocks": [
            {
                "part_id": part_id,
                "finished_geometry_summary": snapshot_members[part_id],
                "owner_report_finished_shape_sha256": report_replay.get(part_id, {}).get("finished_shape_sha256"),
                "exact_export_status": (
                    "one_reported_shape_fingerprint" if report_replay.get(part_id, {}).get("finished_shape_sha256")
                    else "no_per_body_finished_BRep_or_STEP_fingerprint_in_current_sources"
                ),
                "material_frame_status": "pattern-level conditional scenario only; exact member assignment is not frozen",
                "release": False,
            }
            for part_id in sorted(candidate_part_ids)
        ],
        "candidate_bolt_axes": candidate_axes,
        "retained_frame_bolt_axes": frame_axes,
        "panel_kicker_screw_axes": panel_axes,
        "target_duties": sorted(row.get("station_id") for row in model_inventory.get("target_duties", [])),
        "removed_historical_structural_axes": {
            "count": len(model_inventory.get("removed_source_axes", [])),
            "axis_ids": sorted(row.get("axis_id") for row in model_inventory.get("removed_source_axes", [])),
            "role": "Former selected-angle structural SDS axes; absent from this 92-axis candidate layout.",
        },
            "contact_graph": {
            "source_path": SOURCE_PATHS["contact_graph"],
            "physical_member_nodes": graph_counts.get("physical_member_nodes"),
            "unique_member_pairs": graph_counts.get("unique_member_pairs"),
            "aabb_broadphase_candidates": graph_counts.get("aabb_broadphase_candidates"),
            "aabb_separated_pairs_not_exactly_evaluated": graph_counts.get("aabb_separated_pairs_not_exactly_evaluated"),
            "exact_brep_pairs_evaluated": graph_counts.get("exact_brep_pairs_evaluated"),
            "geometry_state_counts": dict(sorted(edge_states.items())),
            "positive_volume_overlap_count": 0,
            "interpretation": "Geometric membership/contact classification only; it defines no active set, contact pressure, connector law, stiffness, force transfer, support route, or capacity.",
        },
        "existing_step_export_evidence": {
            "manifest_path": SOURCE_PATHS["retained_access_brep_manifest"],
            "schema": retained_access_export.get("schema"),
            "status": retained_access_export.get("status"),
            "geometry_revision_id": retained_access_export.get("geometry_revision_id"),
            "exported_counts": exported_counts,
            "category_counts": dict(sorted(brep_categories.items())),
            "source_timber_shape_ids": sorted(brep_timber_ids),
            "retained_frame_bolt_stack_ids": sorted(roles_by_axis),
            "member_binding_limit": retained_access_export.get("unchanged_source_member_binding"),
            "scope_limit": (
                "Exact STEP files exist for 20 preserved timber shapes, 60 modeled retained-frame-bolt physical roles (12 stacks), and 131 modeled wires in the future-D6 access-study state. Current candidate bolt roles/connectors, all 24 candidate blocks, plywood panels and 66 panel screw axes are omitted. The bundle is not exact full-frame current geometry and validates no actual product or tool."
            ),
        },
        "applied_load_cases": {
            "source_path": SOURCE_PATHS["load_cases"],
            "source_file_sha256": current_load_case_sha,
            "contract_sha256": load_contract_hash,
            "basis": load_cases.get("load_basis"),
            "current_geometry_input_sha256": load_cases.get("current_geometry_input_sha256"),
            "cases": reconstructed_cases,
            "independent_reconstruction_audit": load_audit,
            "load_contract_limit": load_cases.get("limits"),
        },
        "scenario_input_status": {
            "timber_and_grain": {
                "source": SOURCE_PATHS["material_scenarios"],
                "status": "conditional elastic/material-pattern proposal; not a per-body source-bound assignment",
                "exact_current_member_material_frames": "unresolved for the full 50-member inventory",
                "delivered_species_grade_moisture_grain_and_connection_zone": "not observed",
            },
            "metal_elastic": {
                "source": SOURCE_PATHS["material_scenarios"],
                "status": "generic diagnostic elastic scenario; it does not establish bolt/nut/washer identity, yield properties, strength, or delivered conformance",
            },
            "candidate_hardware": {
                "source": SOURCE_PATHS["hardware_schedule"],
                "candidate_axes": 92,
                "modeled_roles_per_axis": 5,
                "physical_bolt_nut_washer_selection": "not selected across the 92 axes",
                "thread_section_grip_engagement_and_receiving": "unresolved; nominal model length is not delivered shank/thread engagement",
            },
            "retained_frame_hardware": {
                "source": SOURCE_PATHS["hardware_schedule"],
                "starting_axes": 12,
                "current_candidate_recheck": "required; old identities/layout do not transfer structural acceptance",
                "physical_receiving": "not observed",
            },
            "panel_kicker_screws": {
                "source": SOURCE_PATHS["panel_screw_contract"],
                "count": 66,
                "purchased_policy": "Hillman 42605, 63.5 mm nominal; preserve current pilot policy and do not infer SPAX resistance, stiffness, pilots, or installation rules",
                "receipt_or_installed_engagement": "not observed",
            },
            "floor_support": {
                "status": "conditional analytical no-slip support assumption only",
                "verified_floor_or_anchor": False,
                "floor_friction_test_added": False,
            },
        },
        "source_artifacts": direct_artifacts,
        "source_dependency_hash_audits": hash_groups,
        "independent_cross_checks": {
            "physical_member_set": "26 source member/panel IDs plus 24 current candidate blocks exactly equal the 50 graph member IDs",
            "changed_body_set": "40 snapshot IDs are the 24 current blocks plus 16 shared source members; the snapshot remains summary geometry, not exact full-frame CAD solids",
            "candidate_bolt_axes": "92 axis IDs agree across owner scene, geometry snapshot, grip screen, and graph",
            "retained_frame_bolts": "12 axis IDs agree across owner scene, source inventory, and graph; source member membership does not establish physical stack order",
            "panel_kicker_screws": "66 axis IDs agree across source inventory, current receiver screen, and graph; scene split reconciles 58 unchanged plus 8 moved",
            "applied_loads": load_audit["result"],
            "embedded_source_hashes": "All listed contact-graph, source-inventory, load-contract, and datum dependencies match their recorded SHA-256 values.",
            "retained_access_step_bundle": "211 retained-bolt D6 STEP files match the export manifest; its 20 timber IDs reconcile to source-inventory timber IDs and its 12 five-role stacks reconcile to retained frame-bolt axes.",
            "all_pass": True,
        },
        "readiness": {
            "inventory_complete": True,
            "inventory_complete_scope": "Source-bound entity IDs, axis IDs, and applied case IDs/counts reconcile across the listed artifacts.",
            "inputs_ready": False,
            "exact_full_frame_finished_geometry_ready": False,
            "per_member_material_mapping_ready": False,
            "selected_structural_hardware_ready": False,
            "complete_mechanical_contact_attachment_model_ready": False,
            "current_full_frame_demands_available": False,
            "criterion_resolved": False,
            "native_solve_executed": False,
            "unresolved_inputs": [
                "No source set in this manifest supplies exact finished BRep/STEP solids for all 50 current timber/panel members. An existing retained-bolt D6 access bundle has STEP files for 20 source timber shapes, 60 retained frame-bolt component roles, and 131 modeled wires, while explicitly omitting current candidate connectors/blocks and panels/66 panel screws. The snapshot gives summaries for 40 changed bodies; the source inventory binds 26 preserved source-part shapes; the owner report only contains per-body finished-shape hashes for a subset.",
                "The current material document is a conditional pattern-level proposal; exact per-body wood/grain/R-T and modeled steel assignments for the full current frame are not bound.",
                "No selected/received bolt, nut, washer, or verified bolt thread/shank/engagement record covers all 92 candidate and 12 retained axes. The 66 Hillman screws remain a separate policy and have no transferred SPAX properties.",
                "The 50-node graph classifies geometric contacts only. Active unilateral contact, connector/bolt transfer, bolt-nut axial engagement, joint stiffness, panel attachment transfer, and all 24 replacement duties remain mechanically open.",
                "The six load cases are applied inputs only. Current full-frame boundary conditions, dead-load distribution, support reactions, joint/member demands, and stability outputs are not present.",
                "The no-slip floor boundary is an unverified analytical assumption; no floor qualification or anchor is represented.",
            ],
        },
        "claim_limits": [
            "Inventory completeness is limited to source-bound identities/counts and the six applied input records; it is not a solver-ready full-frame input freeze.",
            "The 40-body geometry snapshot and 50-node contact graph are geometric summaries, not an exact current full-frame finished-solid model. The existing retained-bolt D6 STEP bundle represents a partial access-study state and omits candidate blocks/connectors, panels, and panel screws.",
            "The 92 candidate bolts replace 144 prior selected-angle SDS axes only in this separate development lane; no structural evidence transfers from the selected candidate.",
            "The 12 original frame-bolt arrangements remain starting geometry and must be rechecked in this candidate.",
            "The six applied force/wrench records allocate no load to a member, block, interface, or bolt and state no demand or resistance.",
            "All release, acceptance, fabrication, drilling, and climbing flags remain false.",
        ],
        "release": {
            "candidate_accepted": False,
            "engineering_mvp_complete": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
            "climbing_released": False,
        },
        "producer": {
            "path": "scripts/wood_joint_current_full_frame_manifest.py",
            "sha256": _sha256_file(Path(__file__).resolve()),
        },
    }
    manifest["manifest_sha256"] = _sha256_bytes(_canonical_json(manifest))
    return manifest


def verify_manifest(root: Path = ROOT, output: Path = OUTPUT) -> dict[str, Any]:
    root = Path(root)
    output = Path(output)
    saved = _read_json(root, str(output))
    payload = dict(saved)
    saved_hash = payload.pop("manifest_sha256", None)
    _require(saved_hash == _sha256_bytes(_canonical_json(payload)), "generated manifest content hash differs")
    _require(saved.get("producer", {}).get("sha256") == _sha256_file(Path(__file__).resolve()),
             "manifest producer source hash differs")
    current = build_manifest(root)
    _require(saved == current, "saved manifest does not match current source inputs")
    _require(saved.get("readiness", {}).get("inventory_complete") is True,
             "manifest entity inventory is not complete")
    _require(saved.get("readiness", {}).get("inputs_ready") is False,
             "manifest must not claim solver inputs ready")
    _require(saved.get("independent_cross_checks", {}).get("all_pass") is True,
             "independent source/case cross-checks did not all pass")
    return {
        "status": "verified",
        "manifest_path": str(output),
        "manifest_sha256": saved_hash,
        "inventory_complete": True,
        "inputs_ready": False,
        "physical_member_count": saved["inventory_counts"]["full_physical_member_nodes"],
        "candidate_bolt_axes": saved["inventory_counts"]["candidate_bolt_axes"],
        "retained_frame_bolt_axes": saved["inventory_counts"]["retained_starting_frame_bolt_axes"],
        "panel_kicker_screw_axes": saved["inventory_counts"]["panel_kicker_screw_axes"],
        "load_case_count": saved["inventory_counts"]["current_applied_load_cases"],
        "source_dependency_hash_records": sum(group["checked_count"] for group in saved["source_dependency_hash_audits"]),
        "load_reconstruction": saved["applied_load_cases"]["independent_reconstruction_audit"]["result"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write a fresh deterministic manifest")
    mode.add_argument("--verify", action="store_true", help="verify the saved manifest against current sources")
    parser.add_argument("--output", default=str(OUTPUT), help="repository-relative manifest path")
    args = parser.parse_args()
    root = ROOT
    output = Path(args.output)
    if output.is_absolute():
        try:
            output = output.relative_to(root)
        except ValueError as error:
            raise SystemExit("--output must be inside the repository") from error
    if args.verify:
        result = verify_manifest(root, output)
    else:
        result = build_manifest(root)
        destination = root / output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                               encoding="utf-8")
        result = {
            "status": "written",
            "manifest_path": str(output),
            "manifest_sha256": result["manifest_sha256"],
            "inventory_complete": result["readiness"]["inventory_complete"],
            "inputs_ready": result["readiness"]["inputs_ready"],
            "physical_member_count": result["inventory_counts"]["full_physical_member_nodes"],
            "candidate_bolt_axes": result["inventory_counts"]["candidate_bolt_axes"],
            "retained_frame_bolt_axes": result["inventory_counts"]["retained_starting_frame_bolt_axes"],
            "panel_kicker_screw_axes": result["inventory_counts"]["panel_kicker_screw_axes"],
            "load_case_count": result["inventory_counts"]["current_applied_load_cases"],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
