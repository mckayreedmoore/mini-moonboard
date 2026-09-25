"""Frozen pre-solve force and wrench contract for the current WJ24 geometry.

This module deliberately does not load CAD, import a frame model, or estimate
joint response. The caller must supply current global hold-face datums, the
outward panel normal, and the corresponding panel-midplane moment reference
points. The result records applied force and wrench only; it contains no
reactions, load distribution, stiffness, resistance, or acceptance claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA = "wood_joint_current_load_case_contract/v1"
GEOMETRY_REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
REVIEWED_REPOSITORY_COMMIT = "b1e8707d"
CANDIDATE_ID = "compact-floor-flush-wood-joints-development"

POUNDS = 250.0
DYNAMIC_FACTOR = 2.0
POUNDS_TO_KG = 0.45359237
GRAVITY_M_PER_S2 = 9.80665
PANEL_PATCH_SIZE_MM = 20.0
STANDOFF_MM = 100.0

CASE_INPUTS = (
    ("a12-rear", "A12", (0.0, 300.0)),
    ("a12-forward", "A12", (0.0, -300.0)),
    ("a12-left", "A12", (-300.0, 0.0)),
    ("k12-right", "K12", (300.0, 0.0)),
    ("k12-rear", "K12", (0.0, 300.0)),
    ("a1-rear", "A1", (0.0, 300.0)),
)
REQUIRED_HOLDS = ("A12", "K12", "A1")

GEOMETRY_SNAPSHOT_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json"
)
CURRENT_LOAD_DATUMS_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-datums.json"
)
CURRENT_SCENE_PATH = Path("site/owner-wood-joints-wj24-scene.json")

# These files are opened only to hash/read the frozen provenance basis. In
# particular, panel_grid_v2.py is retained as historical hold-label context;
# its local T-nut coordinates are not used to generate current hold datums.
SOURCE_ROLES = {
    "scripts/clear_space_batch.py": "frozen six case IDs, horizontal inputs, 250 lb and 20 mm override",
    "scripts/wood_joint_current_load_cases.py": "independent frozen current force/wrench contract producer",
    "fea/current_response_run.py": "historical current-frame producer/loader provenance; never invoked",
    "fea/current_response_model.py": "historical force scaling and standoff-wrench convention; never imported",
    "fea/horizontal_panel_frame.py": "historical patch/wrench distribution convention; never imported",
    "mini_moonboard/panel_grid_v2.py": "historical hold labels only; local datums are not current coordinates",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VECTOR_TOLERANCE = 1e-9
_WRENCH_TOLERANCE = 1e-8


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _digest_without_contract_hash(contract: Mapping[str, Any]) -> str:
    payload = dict(contract)
    payload.pop("contract_sha256", None)
    return _sha256_bytes(_canonical_json_bytes(payload))


def _vector(value: Any, name: str) -> list[float]:
    if isinstance(value, (str, bytes, bytearray, Mapping)):
        raise TypeError(f"{name} must be a finite three-component vector")
    try:
        parts = list(value)
    except TypeError as error:
        raise ValueError(f"{name} must be a finite three-component vector") from error
    if len(parts) != 3:
        raise ValueError(f"{name} must be a finite three-component vector")
    result = []
    for part in parts:
        if isinstance(part, bool):
            raise TypeError(f"{name} must be a finite three-component vector")
        try:
            number = float(part)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"{name} must be a finite three-component vector") from error
        if not math.isfinite(number):
            raise ValueError(f"{name} must be a finite three-component vector")
        result.append(number)
    return result


def _exact_mapping_keys(value: Any, required: tuple[str, ...], name: str) -> None:
    if not isinstance(value, Mapping) or set(value) != set(required):
        raise ValueError(f"{name} must contain exactly {', '.join(required)}")


def _cross(first: list[float], second: list[float]) -> list[float]:
    return [
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    ]


def _add_scaled(point: list[float], direction: list[float], scale: float) -> list[float]:
    return [point[i] + direction[i] * scale for i in range(3)]


def _close_vector(first: Any, second: list[float], *, tolerance: float) -> bool:
    try:
        a = _vector(first, "contract vector")
    except ValueError:
        return False
    return all(math.isclose(x, y, rel_tol=0.0, abs_tol=tolerance) for x, y in zip(a, second, strict=True))


def _validate_transform_source(transform_source: Mapping[str, Any]) -> dict[str, Any]:
    required = ("source_id", "sha256", "description")
    optional = ("source_path", "source_sha256")
    if not isinstance(transform_source, Mapping) or not set(required) <= set(transform_source) or set(
        transform_source
    ) - set(required + optional):
        raise ValueError("transform_source must contain source_id, sha256, description and optional source bindings")
    cleaned: dict[str, Any] = {}
    for key in required:
        item = transform_source[key]
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"transform_source.{key} must be a non-empty string")
        cleaned[key] = item.strip()
    cleaned["sha256"] = cleaned["sha256"].lower()
    if not _SHA256_RE.fullmatch(cleaned["sha256"]):
        raise ValueError("transform_source.sha256 must be a lowercase or uppercase SHA-256 hex digest")
    if "source_path" in transform_source:
        source_path = transform_source["source_path"]
        if not isinstance(source_path, str) or not source_path.strip():
            raise ValueError("transform_source.source_path must be a non-empty repository-relative path")
        cleaned["source_path"] = source_path.strip()
    if "source_sha256" in transform_source:
        dependencies = transform_source["source_sha256"]
        if not isinstance(dependencies, Mapping):
            raise TypeError("transform_source.source_sha256 must be a path-to-hash mapping")
        normalized_dependencies = {}
        for relative, digest in dependencies.items():
            if not isinstance(relative, str) or not isinstance(digest, str):
                raise TypeError("transform source dependency bindings must be path-to-hash strings")
            normalized_digest = digest.lower()
            if not _SHA256_RE.fullmatch(normalized_digest):
                raise ValueError(f"transform source dependency has an invalid SHA-256: {relative}")
            normalized_dependencies[relative] = normalized_digest
        cleaned["source_sha256"] = dict(sorted(normalized_dependencies.items()))
    return cleaned


def _repository_provenance(
    repository_root: Path,
    transform_source: Mapping[str, Any],
) -> dict[str, Any]:
    root = repository_root.resolve()
    snapshot_path = root / GEOMETRY_SNAPSHOT_PATH
    if not snapshot_path.is_file():
        raise ValueError(f"Required current geometry snapshot is missing: {GEOMETRY_SNAPSHOT_PATH}")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if snapshot.get("revision_id") != GEOMETRY_REVISION_ID:
        raise ValueError("Geometry snapshot revision does not match the requested WJ24 revision")
    if snapshot.get("reviewed_repository_commit") != REVIEWED_REPOSITORY_COMMIT:
        raise ValueError("Geometry snapshot is not bound to the reviewed repository commit")

    bound_sources = snapshot.get("source_sha256")
    if not isinstance(bound_sources, Mapping) or not bound_sources:
        raise ValueError("Geometry snapshot is missing its source SHA-256 binding")
    source_rows: dict[str, dict[str, str]] = {}
    for relative, expected_sha in bound_sources.items():
        if not isinstance(relative, str) or not isinstance(expected_sha, str):
            raise TypeError("Geometry snapshot source bindings must be path-to-hash strings")
        path = root / relative
        if not path.is_file():
            raise ValueError(f"Geometry snapshot source is missing: {relative}")
        actual_sha = _sha256_file(path)
        if actual_sha != expected_sha:
            raise ValueError(f"Geometry snapshot source hash mismatch: {relative}")
        source_rows[relative] = {"sha256": actual_sha, "role": "source bound by the reviewed geometry snapshot"}

    transform_source_path = transform_source.get("source_path")
    if transform_source_path is not None:
        path = root / transform_source_path
        if not path.is_file() or _sha256_file(path) != transform_source["sha256"]:
            raise ValueError("Current transform source path/hash does not match its explicit source binding")
        source_rows[transform_source_path] = {
            "sha256": transform_source["sha256"],
            "role": "explicit current hold/panel global-datum input artifact",
        }
    for relative, expected_sha in transform_source.get("source_sha256", {}).items():
        path = root / relative
        if not path.is_file() or _sha256_file(path) != expected_sha:
            raise ValueError(f"Current transform dependency hash mismatch: {relative}")
        source_rows[relative] = {
            "sha256": expected_sha,
            "role": "source bound by the explicit current datum artifact",
        }

    scene_path = root / CURRENT_SCENE_PATH
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    if scene.get("candidate") != CANDIDATE_ID or scene.get("revision_id") != GEOMETRY_REVISION_ID:
        raise ValueError("Current scene candidate/revision does not match the geometry snapshot")
    report_name = scene.get("revision_report_path")
    report_sha = scene.get("revision_report_sha256")
    if not isinstance(report_name, str) or not isinstance(report_sha, str):
        raise TypeError("Current scene review-report source binding must contain strings")
    report_relative = str(CURRENT_SCENE_PATH.parent / report_name)
    report_path = root / report_relative
    if not report_path.is_file() or _sha256_file(report_path) != report_sha:
        raise ValueError("Current scene review-report hash does not match the saved report")
    if source_rows.get(report_relative, {}).get("sha256") != report_sha:
        raise ValueError("Geometry snapshot does not bind the current scene review report")

    snapshot_relative = str(GEOMETRY_SNAPSHOT_PATH)
    source_rows[snapshot_relative] = {
        "sha256": _sha256_file(snapshot_path),
        "role": "reviewed current geometry snapshot and revision identity",
    }
    for relative, role in SOURCE_ROLES.items():
        path = root / relative
        if not path.is_file():
            raise ValueError(f"Required historical load source is missing: {relative}")
        source_rows[relative] = {"sha256": _sha256_file(path), "role": role}

    return {
        "geometry_revision_id": GEOMETRY_REVISION_ID,
        "reviewed_repository_commit": REVIEWED_REPOSITORY_COMMIT,
        "geometry_snapshot": snapshot_relative,
        "snapshot_bound_source_sha256": {
            key: value["sha256"]
            for key, value in sorted(source_rows.items())
            if key in bound_sources
        },
        "files": {key: source_rows[key] for key in sorted(source_rows)},
        "current_transform_source": dict(transform_source),
        "source_use_note": (
            "Repository files are read only for source identity. The historical local hold/T-nut datum "
            "table is not used to create current global coordinates."
        ),
    }


def _normalize_geometry(
    hold_face_datums_global_xyz_mm: Mapping[str, Any],
    panel_midplane_applicationpoints_global_xyz_mm: Mapping[str, Any],
    panel_outward_normal_global_xyz: Any,
) -> dict[str, Any]:
    _exact_mapping_keys(hold_face_datums_global_xyz_mm, REQUIRED_HOLDS, "hold_face_datums_global_xyz_mm")
    _exact_mapping_keys(
        panel_midplane_applicationpoints_global_xyz_mm,
        REQUIRED_HOLDS,
        "panel_midplane_applicationpoints_global_xyz_mm",
    )
    normal = _vector(panel_outward_normal_global_xyz, "panel_outward_normal_global_xyz")
    norm = math.sqrt(sum(component * component for component in normal))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=_VECTOR_TOLERANCE):
        raise ValueError("panel_outward_normal_global_xyz must already be a unit vector")
    face_points = {
        hold: _vector(hold_face_datums_global_xyz_mm[hold], f"{hold} hold face datum")
        for hold in REQUIRED_HOLDS
    }
    midplane_points = {
        hold: _vector(
            panel_midplane_applicationpoints_global_xyz_mm[hold],
            f"{hold} panel-midplane application point",
        )
        for hold in REQUIRED_HOLDS
    }
    return {
        "coordinate_frame": "global_xyz_mm_and_global_xyz_n",
        "panel_outward_normal_global_xyz": normal,
        "hold_face_datums_global_xyz_mm": face_points,
        "panel_midplane_applicationpoints_global_xyz_mm": midplane_points,
    }


def build_current_load_contract(
    *,
    hold_face_datums_global_xyz_mm: Mapping[str, Any],
    panel_outward_normal_global_xyz: Any,
    panel_midplane_applicationpoints_global_xyz_mm: Mapping[str, Any],
    transform_source: Mapping[str, Any],
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the exact six-case applied-force contract from explicit geometry.

    ``hold_face_datums_global_xyz_mm`` gives current global panel-face centers
    for exactly A12, K12, and A1. ``panel_midplane_applicationpoints...`` gives
    their explicit global moment-reference points on the panel midplane. The
    outward normal must be a caller-supplied global unit vector. No point is
    inferred from a T-nut center, hold label, nominal board transform, or panel
    thickness.

    The force location is each face datum plus 100 mm along the explicit normal.
    The 20 mm panel patch remains centered at the face datum and is a separate
    input-location convention. Moment is reconstructed about the explicitly
    supplied panel-midplane point. This is an applied wrench, not a joint
    reaction or demand allocation.
    """
    geometry = _normalize_geometry(
        hold_face_datums_global_xyz_mm,
        panel_midplane_applicationpoints_global_xyz_mm,
        panel_outward_normal_global_xyz,
    )
    clean_transform_source = _validate_transform_source(transform_source)
    root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[1]
    provenance = _repository_provenance(root, clean_transform_source)
    input_geometry_sha256 = _sha256_bytes(_canonical_json_bytes(geometry))
    vertical_force_n = -DYNAMIC_FACTOR * POUNDS * POUNDS_TO_KG * GRAVITY_M_PER_S2

    cases = []
    for case_id, hold, horizontal_xy in CASE_INPUTS:
        face_point = geometry["hold_face_datums_global_xyz_mm"][hold]
        midplane_point = geometry["panel_midplane_applicationpoints_global_xyz_mm"][hold]
        normal = geometry["panel_outward_normal_global_xyz"]
        force_point = _add_scaled(face_point, normal, STANDOFF_MM)
        force = [horizontal_xy[0], horizontal_xy[1], vertical_force_n]
        moment = _cross(
            [force_point[i] - midplane_point[i] for i in range(3)],
            force,
        )
        cases.append(
            {
                "case_id": case_id,
                "hold_id": hold,
                "case_inputs": {
                    "horizontal_force_global_xy_n": list(horizontal_xy),
                    "pounds": POUNDS,
                    "dynamic_factor": DYNAMIC_FACTOR,
                },
                "applied_force_global_xyz_n": force,
                "panel_patch": {
                    "size_mm": PANEL_PATCH_SIZE_MM,
                    "center_global_xyz_mm": list(face_point),
                    "scope": "20 mm square panel load patch centered on the explicit hold face datum",
                },
                "standoff": {
                    "distance_mm": STANDOFF_MM,
                    "direction_global_xyz": list(normal),
                    "force_application_point_global_xyz_mm": force_point,
                },
                "panel_midplane_applicationpoint_global_xyz_mm": list(midplane_point),
                "moment_about_panel_midplane_applicationpoint_global_xyz_nmm": moment,
                "applied_wrench": {
                    "reference_point_global_xyz_mm": list(midplane_point),
                    "force_global_xyz_n": list(force),
                    "moment_global_xyz_nmm": list(moment),
                },
            }
        )

    contract: dict[str, Any] = {
        "schema": SCHEMA,
        "candidate": CANDIDATE_ID,
        "geometry_revision_id": GEOMETRY_REVISION_ID,
        "reviewed_repository_commit": REVIEWED_REPOSITORY_COMMIT,
        "load_basis": {
            "pounds": POUNDS,
            "dynamic_factor": DYNAMIC_FACTOR,
            "pounds_to_kg": POUNDS_TO_KG,
            "gravity_m_per_s2": GRAVITY_M_PER_S2,
            "vertical_force_global_z_n": vertical_force_n,
            "horizontal_components": "Global X/Y components exactly as frozen in the six case producer.",
            "patch_size_mm": PANEL_PATCH_SIZE_MM,
            "patch_definition": "20 mm square patch centered at the explicit current hold face datum.",
            "standoff_mm": STANDOFF_MM,
            "standoff_definition": "100 mm from the explicit hold face datum along the explicit outward panel normal.",
            "moment_definition": "(standoff force point - explicit panel-midplane reference point) cross global force; N mm.",
        },
        "current_geometry_inputs": geometry,
        "current_geometry_input_sha256": input_geometry_sha256,
        "source_provenance": provenance,
        "cases": cases,
        "limits": [
            "Applied forces and equivalent global wrenches only; no frame reactions or connection demands are computed.",
            "No joint law, contact law, stiffness, resistance, load sharing, or capacity is assumed by this contract.",
            "The 20 mm patch and 100 mm standoff are distinct: patch center is the hold-face datum; the wrench force point is 100 mm outward from it.",
            "Caller-supplied current global geometry is mandatory and is never inferred from historical T-nut-center coordinates.",
        ],
    }
    contract["contract_sha256"] = _digest_without_contract_hash(contract)
    validate_current_load_contract(contract)
    return contract


def build_current_load_contract_from_datum_file(
    *,
    repository_root: str | Path | None = None,
    datum_path: str | Path = CURRENT_LOAD_DATUMS_PATH,
) -> dict[str, Any]:
    """Build from the saved current global-datum artifact, without CAD access.

    The artifact and every source hash embedded in it are checked against the
    repository before the ordinary explicit-input builder is called. This
    convenience entry point never extracts or transforms geometry itself.
    """
    root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[1]
    relative_datum_path = Path(datum_path)
    if relative_datum_path.is_absolute():
        try:
            relative_datum_path = relative_datum_path.resolve().relative_to(root.resolve())
        except ValueError as error:
            raise ValueError("Current datum artifact must be inside the repository") from error
    if relative_datum_path != CURRENT_LOAD_DATUMS_PATH:
        raise ValueError(f"Expected the reviewed current datum artifact at {CURRENT_LOAD_DATUMS_PATH}")
    artifact_path = root / relative_datum_path
    if not artifact_path.is_file():
        raise ValueError(f"Current datum artifact is missing: {relative_datum_path}")
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    if set(data) != {"revision_id", "holds", "source_sha256", "not_a_load_or_mechanics_result"}:
        raise ValueError("Current datum artifact schema does not match the reviewed explicit-datum file")
    if data.get("revision_id") != GEOMETRY_REVISION_ID:
        raise ValueError("Current datum artifact revision does not match the reviewed WJ24 geometry")
    if data.get("not_a_load_or_mechanics_result") is not True:
        raise ValueError("Current datum artifact must remain explicitly non-mechanics evidence")
    _exact_mapping_keys(data.get("holds"), REQUIRED_HOLDS, "current datum artifact holds")
    dependencies = data.get("source_sha256")
    if not isinstance(dependencies, Mapping) or not dependencies:
        raise ValueError("Current datum artifact is missing its source SHA-256 bindings")
    for relative, expected_sha in dependencies.items():
        if not isinstance(relative, str) or not isinstance(expected_sha, str):
            raise TypeError("Current datum artifact sources must be path-to-hash strings")
        source_path = root / relative
        if not source_path.is_file() or _sha256_file(source_path) != expected_sha:
            raise ValueError(f"Current datum artifact source hash mismatch: {relative}")

    face_datums = {}
    midplane_points = {}
    shared_normal = None
    for hold in REQUIRED_HOLDS:
        row = data["holds"][hold]
        if not isinstance(row, Mapping):
            raise TypeError(f"Current datum row {hold} must be a mapping")
        face_datums[hold] = row.get("face_datum_global_mm")
        midplane_points[hold] = row.get("panel_midplane_reference_global_mm")
        normal = _vector(row.get("outward_normal_global"), f"{hold} outward normal")
        if shared_normal is None:
            shared_normal = normal
        elif not _close_vector(normal, shared_normal, tolerance=_VECTOR_TOLERANCE):
            raise ValueError("Current datum artifact must supply one consistent global panel normal")

    transform_source = {
        "source_id": str(relative_datum_path),
        "sha256": _sha256_file(artifact_path),
        "description": "Reviewed explicit current global hold-face and panel-midplane datums; no T-nut center used.",
        "source_path": str(relative_datum_path),
        "source_sha256": dependencies,
    }
    return build_current_load_contract(
        hold_face_datums_global_xyz_mm=face_datums,
        panel_outward_normal_global_xyz=shared_normal,
        panel_midplane_applicationpoints_global_xyz_mm=midplane_points,
        transform_source=transform_source,
        repository_root=root,
    )


def validate_current_load_contract(contract: Mapping[str, Any]) -> None:
    """Validate exact case identity and independently reconstruct every wrench."""
    if not isinstance(contract, Mapping) or contract.get("schema") != SCHEMA:
        raise ValueError("Unknown current load-contract schema")
    if contract.get("candidate") != CANDIDATE_ID:
        raise ValueError("Load contract candidate does not match current WJ24 geometry")
    if contract.get("geometry_revision_id") != GEOMETRY_REVISION_ID:
        raise ValueError("Load contract geometry revision does not match current WJ24 geometry")
    if contract.get("reviewed_repository_commit") != REVIEWED_REPOSITORY_COMMIT:
        raise ValueError("Load contract reviewed commit does not match the frozen geometry snapshot")
    if contract.get("contract_sha256") != _digest_without_contract_hash(contract):
        raise ValueError("Load contract SHA-256 does not match its contents")

    geometry = contract.get("current_geometry_inputs")
    if not isinstance(geometry, Mapping):
        raise TypeError("Load contract current global geometry inputs must be a mapping")
    normalized = _normalize_geometry(
        geometry.get("hold_face_datums_global_xyz_mm"),
        geometry.get("panel_midplane_applicationpoints_global_xyz_mm"),
        geometry.get("panel_outward_normal_global_xyz"),
    )
    if normalized != geometry:
        raise ValueError("Current global geometry inputs are not normalized finite vectors")
    if contract.get("current_geometry_input_sha256") != _sha256_bytes(_canonical_json_bytes(normalized)):
        raise ValueError("Current geometry input SHA-256 does not match the supplied coordinates")

    basis = contract.get("load_basis")
    expected_basis = {
        "pounds": POUNDS,
        "dynamic_factor": DYNAMIC_FACTOR,
        "pounds_to_kg": POUNDS_TO_KG,
        "gravity_m_per_s2": GRAVITY_M_PER_S2,
        "vertical_force_global_z_n": -DYNAMIC_FACTOR * POUNDS * POUNDS_TO_KG * GRAVITY_M_PER_S2,
        "patch_size_mm": PANEL_PATCH_SIZE_MM,
        "standoff_mm": STANDOFF_MM,
    }
    if not isinstance(basis, Mapping) or any(basis.get(key) != value for key, value in expected_basis.items()):
        raise ValueError("Load contract does not preserve the frozen force, patch, and standoff inputs")

    provenance = contract.get("source_provenance")
    if not isinstance(provenance, Mapping) or provenance.get("geometry_revision_id") != GEOMETRY_REVISION_ID:
        raise ValueError("Load contract source provenance is missing the current geometry binding")
    source_transform = provenance.get("current_transform_source")
    _validate_transform_source(source_transform)
    source_files = provenance.get("files")
    if not isinstance(source_files, Mapping):
        raise TypeError("Load contract source provenance files must be a mapping")
    for relative, row in source_files.items():
        if not isinstance(relative, str) or not isinstance(row, Mapping) or not _SHA256_RE.fullmatch(str(row.get("sha256", ""))):
            raise ValueError("Load contract contains an invalid provenance file hash")

    cases = contract.get("cases")
    expected_ids = [row[0] for row in CASE_INPUTS]
    if not isinstance(cases, list) or [case.get("case_id") if isinstance(case, Mapping) else None for case in cases] != expected_ids:
        raise ValueError("Load contract must contain the exact six frozen case IDs in source order")

    vertical_force_n = -DYNAMIC_FACTOR * POUNDS * POUNDS_TO_KG * GRAVITY_M_PER_S2
    normal = normalized["panel_outward_normal_global_xyz"]
    for case, (case_id, hold, horizontal_xy) in zip(cases, CASE_INPUTS, strict=True):
        face_point = normalized["hold_face_datums_global_xyz_mm"][hold]
        midplane_point = normalized["panel_midplane_applicationpoints_global_xyz_mm"][hold]
        force_point = _add_scaled(face_point, normal, STANDOFF_MM)
        force = [horizontal_xy[0], horizontal_xy[1], vertical_force_n]
        moment = _cross([force_point[i] - midplane_point[i] for i in range(3)], force)
        if case.get("hold_id") != hold:
            raise ValueError(f"Case {case_id} has the wrong explicit hold input")
        inputs = case.get("case_inputs")
        if not isinstance(inputs, Mapping) or inputs != {
            "horizontal_force_global_xy_n": list(horizontal_xy),
            "pounds": POUNDS,
            "dynamic_factor": DYNAMIC_FACTOR,
        }:
            raise ValueError(f"Case {case_id} inputs do not match the frozen load case")
        if not _close_vector(case.get("applied_force_global_xyz_n"), force, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} applied global force does not match the frozen load")
        patch = case.get("panel_patch")
        if not isinstance(patch, Mapping) or patch.get("size_mm") != PANEL_PATCH_SIZE_MM:
            raise ValueError(f"Case {case_id} does not preserve the 20 mm panel patch")
        if not _close_vector(patch.get("center_global_xyz_mm"), face_point, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} patch center is not the explicit hold face datum")
        standoff = case.get("standoff")
        if not isinstance(standoff, Mapping) or standoff.get("distance_mm") != STANDOFF_MM:
            raise ValueError(f"Case {case_id} does not preserve the 100 mm standoff")
        if not _close_vector(standoff.get("direction_global_xyz"), normal, tolerance=_VECTOR_TOLERANCE):
            raise ValueError(f"Case {case_id} standoff direction is not the explicit panel normal")
        if not _close_vector(standoff.get("force_application_point_global_xyz_mm"), force_point, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} force point does not reconstruct from the 100 mm standoff")
        if not _close_vector(case.get("panel_midplane_applicationpoint_global_xyz_mm"), midplane_point, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} has the wrong explicit panel-midplane moment point")
        if not _close_vector(case.get("moment_about_panel_midplane_applicationpoint_global_xyz_nmm"), moment, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} moment does not reconstruct from the global force and points")
        wrench = case.get("applied_wrench")
        if not isinstance(wrench, Mapping):
            raise TypeError(f"Case {case_id} applied wrench must be a mapping")
        if not _close_vector(wrench.get("reference_point_global_xyz_mm"), midplane_point, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} wrench reference point is inconsistent")
        if not _close_vector(wrench.get("force_global_xyz_n"), force, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} wrench force is inconsistent")
        if not _close_vector(wrench.get("moment_global_xyz_nmm"), moment, tolerance=_WRENCH_TOLERANCE):
            raise ValueError(f"Case {case_id} wrench moment is inconsistent")
