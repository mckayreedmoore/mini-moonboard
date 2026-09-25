"""Build an incremental, non-authoritative design-review scene for WJ24.

This module consumes a geometry revision and its source-bound report. It never
builds CAD geometry, writes the published viewer URL, or imports prior static
findings into the current revision. Untouched overlay meshes and selected-
baseline asset hashes are copied from the durable parent scene byte-for-byte
at the JSON-value level.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from scripts.export_wood_joint_wj24_scene import (
    _plain,
    _shape_mesh,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_SCENE_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/wj24-viewer-review/final-review-snapshots/"
    "owner-wood-joints-wj24-scene.json.snapshot"
)
BASE_SCENE_SHA256 = "b80baec6b4435f4cfad724efdc25df787d04251f1a1b7203ba63782fb4b485f0"
SCHEMA = "owner_wood_joints_design_review_scene/v1"
DEFAULT_REVISION_ID = "lower-rear-blocks-below-v1"
CANDIDATE_ID = "compact-floor-flush-wood-joints-development"
RELEASE_FLAGS = (
    "candidate_accepted",
    "source_cutting_released",
    "drilling_released",
    "fabrication_released",
    "structural_accepted",
    "assembly_proven",
)
FALSE_CLAIM_FLAGS = (
    "integrated_scene_is_accepted",
    "complete_joint_acceptance",
    "capacity_established",
    "installation_proven",
    "candidate_accepted",
    "fabrication_released",
    "structural_released",
    "climbing_released",
)
DISPLAY_MESH_ENCODING = "base64_typed_arrays_le_v1"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _json_value(value: Any) -> Any:
    """Convert geometry/report data to deterministic JSON-safe values."""
    if is_dataclass(value):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [_json_value(item) for item in sorted(value, key=str)]
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported design-review evidence value: {type(value).__name__}")


def _valid_sha(value: Any, label: str, length: int = 64) -> str:
    rendered = str(value)
    if len(rendered) != length or any(ch not in "0123456789abcdef" for ch in rendered.lower()):
        raise ValueError(f"{label} must be a {length}-character hexadecimal digest")
    return rendered.lower()


def _source_value(geometry: Any, report: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        value = getattr(geometry, name, None)
        if value is not None:
            return value
    for parent in (report, report.get("source", {}), report.get("source_binding", {})):
        if isinstance(parent, Mapping):
            for name in names:
                if parent.get(name) is not None:
                    return parent[name]
    return None


def _load_parent_scene(
    base_scene: Mapping[str, Any] | None,
    base_scene_bytes: bytes | None,
) -> tuple[dict[str, Any], bytes, str]:
    if base_scene is None:
        raw = base_scene_bytes if base_scene_bytes is not None else (ROOT / BASE_SCENE_PATH).read_bytes()
        try:
            scene = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("parent scene bytes are not valid JSON") from error
    else:
        scene = _json_value(base_scene)
        raw = base_scene_bytes if base_scene_bytes is not None else _canonical_json_bytes(scene)
        if base_scene_bytes is not None and json.loads(raw) != scene:
            raise ValueError("parent scene object and supplied bytes differ")
    digest = _sha256_bytes(raw)
    if digest != BASE_SCENE_SHA256:
        raise ValueError(f"parent scene is not the pinned durable snapshot: {digest}")
    if scene.get("schema") != "owner_wood_joints_wj24_diagnostic_scene/v1":
        raise ValueError("parent scene schema is not the preserved WJ24 diagnostic snapshot")
    if len(scene.get("solids", ())) != 567:
        raise ValueError("pinned parent scene must contain 567 overlay solids")
    if len(scene.get("baseline_asset_sha256", {})) != 725:
        raise ValueError("pinned parent scene must bind all 725 baseline assets")
    return scene, raw, digest


def _changed_solid_ids(report: Mapping[str, Any]) -> set[str]:
    """Read the revision's explicit display-mesh delta, including grouped maps."""
    raw: Any = report.get("changed_display_solid_ids")
    if raw is None:
        mesh_delta = report.get("mesh_delta", {})
        if isinstance(mesh_delta, Mapping):
            raw = mesh_delta.get("changed_display_solid_ids", mesh_delta.get("changed_solid_ids"))
    if raw is None:
        raw = report.get("display_mesh_changes")
    if isinstance(raw, Mapping):
        flattened: list[str] = []
        for values in raw.values():
            if isinstance(values, str):
                flattened.append(values)
            elif isinstance(values, (Sequence, Mapping)):
                flattened.extend(str(value) for value in values)
            else:
                raise TypeError("changed display-mesh categories must contain ID sequences")
        values = flattened
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        values = [str(value) for value in raw]
    else:
        raise TypeError("revision report must list changed_display_solid_ids")
    result = set(values)
    if not result or len(result) != len(values):
        raise ValueError("changed display solid IDs must be non-empty and unique")
    return result


def _geometry_display_shapes(geometry: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ID->shape and ID->new-solid metadata maps for current geometry."""
    shapes: dict[str, Any] = {}
    metadata: dict[str, Any] = {}

    def add(name: str, shape: Any, role: str, display_class: str, **extra: Any) -> None:
        if name in shapes:
            raise ValueError(f"duplicate display solid ID in revised geometry: {name}")
        shapes[name] = shape
        metadata[name] = {
            "id": name,
            "name": name,
            "role": role,
            "display_class": display_class,
            "collision_envelope": False,
            "visual_status": "candidate solid geometry; nominal design-review geometry only",
            **extra,
        }

    for name, shape in sorted(getattr(geometry, "finished_hosts", {}).items()):
        add(str(name), shape, "finished_shared_host", "finished_host")
    for name, shape in sorted(getattr(geometry, "finished_candidate_parts", {}).items()):
        add(str(name), shape, "finished_candidate_part", "candidate_part")
    for name, shape in sorted(getattr(geometry, "panel_replacements", {}).items()):
        add(str(name), shape, "candidate_panel_replacement", "panel_replacement")
    bores = getattr(geometry, "candidate_bores", {})
    installed = getattr(geometry, "candidate_installed_hardware", {})
    for axis, roles in sorted(installed.items()):
        bore = bores.get(axis)
        family = str(getattr(bore, "family", "not_recorded"))
        station_id = getattr(bore, "station_id", None)
        for role, shape in sorted(roles.items()):
            name = f"{axis}/{role}"
            add(
                name,
                shape,
                f"candidate_hardware_occupancy/{role}",
                "candidate_hardware",
                collision_envelope=True,
                visual_status="CAD occupied hardware envelope; not a selected or delivered component",
                axis_id=str(axis),
                family=family,
                station_id=station_id,
            )
    return shapes, metadata


def _mesh_with_topology_reference(mesh: Mapping[str, Any], topologies: dict[str, Any]) -> dict[str, Any]:
    result = dict(mesh)
    encoded = result.pop("triangle_indices_base64")
    binary = base64.b64decode(encoded, validate=True)
    topology_id = _sha256_bytes(binary)
    if result.get("triangle_topology_sha256") != topology_id:
        raise ValueError("new mesh triangle topology digest does not match its index data")
    row = {
        "triangle_component_type": result["triangle_component_type"],
        "triangle_count": result["triangle_count"],
        "index_count": result["triangle_count"] * 3,
        "triangle_indices_base64": encoded,
    }
    previous = topologies.get(topology_id)
    if previous is not None and previous != row:
        raise ValueError("triangle topology digest collision has conflicting mesh encoding")
    topologies[topology_id] = row
    return result


def _inventory_source(report: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("model_inventory", "inventory"):
        value = report.get(key)
        if isinstance(value, Mapping):
            return value
    return report


def _inventory_map(source: Mapping[str, Any], key: str, fallback_ids: Sequence[str]) -> dict[str, Any]:
    value = source.get(key)
    if isinstance(value, Mapping):
        return {str(name): _json_value(row) for name, row in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return {str(name): {} for name in value}
    return {str(name): {} for name in fallback_ids}


def _records(source: Mapping[str, Any], key: str, fallback: Sequence[Any], id_key: str) -> list[dict[str, Any]]:
    value = source.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        value = fallback
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in value:
        if isinstance(row, Mapping):
            item = _json_value(row)
        else:
            item = {id_key: str(row)}
        identifier = item.get(id_key)
        if identifier is None:
            raise ValueError(f"{key} row is missing {id_key}")
        identifier = str(identifier)
        if identifier in seen:
            raise ValueError(f"{key} contains duplicate {id_key}: {identifier}")
        item[id_key] = identifier
        seen.add(identifier)
        result.append(item)
    return result


def _axis_ids(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        return sorted(str(key) for key in value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return sorted(str(item) for item in value)
    return []


def _build_model_inventory(geometry: Any, report: Mapping[str, Any]) -> dict[str, Any]:
    source = _inventory_source(report)
    hosts = _inventory_map(source, "shared_hosts", tuple(getattr(geometry, "finished_hosts", {})))
    parts = _inventory_map(source, "candidate_parts", tuple(getattr(geometry, "finished_candidate_parts", {})))
    panels = _inventory_map(source, "panel_replacements", tuple(getattr(geometry, "panel_replacements", {})))
    duties_fallback = [
        {"station_id": str(station)}
        for station in getattr(geometry, "target_station_ids", ())
    ]
    duties = _records(source, "target_duties", duties_fallback, "station_id")
    removed_fallback = [
        {"axis_id": str(axis)}
        for axis in getattr(geometry, "replaced_source_axis_ids", ())
    ]
    removed = _records(source, "removed_source_axes", removed_fallback, "axis_id")
    frame_fallback = list(getattr(geometry, "frame_bolt_records", ()))
    frame = _records(source, "starting_frame_bolts", frame_fallback, "axis_id")
    if not frame and isinstance(source.get("frame_bolts"), Sequence):
        frame = _records(source, "frame_bolts", (), "axis_id")

    moved = source.get("moved_panel_axes", report.get("moved_panel_axes", ()))
    if not isinstance(moved, Sequence) or isinstance(moved, (str, bytes, bytearray)):
        moved = ()
    moved_rows = _records({"rows": moved}, "rows", (), "axis_id")
    moved_ids = {row["axis_id"] for row in moved_rows}

    raw_fixed = source.get("fixed_panel_axes")
    if raw_fixed is None:
        raw_fixed = getattr(geometry, "fixed_axes", ())
    fixed = sorted(set(_axis_ids(raw_fixed)) - moved_ids)
    total_panel_axis_count = int(
        source.get("panel_screw_axis_count", report.get("panel_screw_axis_count", 66))
    )
    if len(set(fixed) | moved_ids) != total_panel_axis_count:
        raise ValueError(
            "fixed and moved panel axis IDs do not preserve the reported panel screw count"
        )

    installed = getattr(geometry, "candidate_installed_hardware", {})
    bores = getattr(geometry, "candidate_bores", {})
    candidate_axes_source = source.get("candidate_axes", {})
    if not isinstance(candidate_axes_source, Mapping):
        candidate_axes_source = {}
    candidate_axes: dict[str, Any] = {}
    axis_ids = {str(axis) for axis in bores} | {str(axis) for axis in installed}
    axis_ids |= {str(axis) for axis in candidate_axes_source}
    for axis in sorted(axis_ids):
        row = _json_value(candidate_axes_source.get(axis, {}))
        if not isinstance(row, dict):
            row = {}
        role_ids = row.get("installed_role_ids")
        if role_ids is None:
            role_ids = row.get("installed_component_roles")
        if role_ids is None:
            role_ids = row.get("installed_cad_role_ids")
        if role_ids is None:
            role_ids = sorted(str(role) for role in installed.get(axis, {}))
        role_ids = sorted({str(role) for role in role_ids})
        row["installed_role_ids"] = role_ids
        row["installed_component_roles"] = role_ids
        row["installed_cad_role_ids"] = role_ids
        if axis not in candidate_axes_source:
            bore = bores.get(axis)
            for attr in ("station_id", "family", "receiver_ids", "trial_id"):
                value = getattr(bore, attr, None)
                if value is not None:
                    row[attr] = _json_value(value)
        candidate_axes[axis] = row

    inventory = {
        "shared_hosts": hosts,
        "candidate_parts": parts,
        "panel_replacements": panels,
        "target_duties": duties,
        "removed_source_axes": removed,
        "fixed_panel_axes": fixed,
        "moved_panel_axes": moved_rows,
        "panel_screw_axis_count": total_panel_axis_count,
        "starting_frame_bolts": frame,
        "frame_bolts": copy.deepcopy(frame),
        "candidate_axes": candidate_axes,
    }
    for key in ("moved_structural_axes", "changed_display_solid_ids"):
        value = source.get(key, report.get(key))
        if value is not None:
            inventory[key] = _json_value(value)
    return inventory


def _baseline_display_translations(
    inventory: Mapping[str, Any], report: Mapping[str, Any]
) -> dict[str, list[float]]:
    supplied = report.get("baseline_display_translations_mm")
    if supplied is None:
        supplied = inventory.get("baseline_display_translations_mm")
    result: dict[str, list[float]] = {}
    if isinstance(supplied, Mapping):
        for name, vector in supplied.items():
            values = [float(component) for component in vector]
            result[str(name)] = values
    else:
        for row in inventory.get("moved_panel_axes", ()):
            name = row.get("visual_name", f"fastener_{row['axis_id']}")
            vector = row.get(
                "translation_global_xyz_mm",
                row.get("translation_mm", row.get("translation_xyz_mm")),
            )
            if vector is None:
                raise ValueError(f"moved panel axis {row['axis_id']} lacks a display translation")
            result[str(name)] = [float(component) for component in vector]
    for name, vector in result.items():
        if len(vector) != 3 or any(not math.isfinite(component) for component in vector):
            raise ValueError(f"baseline display translation for {name} must be finite xyz millimeters")
    return dict(sorted(result.items()))


def _revision_report_bytes(
    report: Mapping[str, Any],
    report_bytes: bytes | None,
    report_path: Path | str | None,
) -> tuple[bytes, str | None]:
    if report_bytes is not None:
        raw = report_bytes
        path_text = Path(report_path).as_posix() if report_path is not None else None
    else:
        declared_path = report_path or report.get("artifact_path") or report.get("report_path")
        path_text = Path(declared_path).as_posix() if declared_path is not None else None
        absolute = None
        if declared_path is not None:
            candidate = Path(declared_path)
            absolute = candidate if candidate.is_absolute() else ROOT / candidate
        if absolute is not None and absolute.is_file():
            raw = absolute.read_bytes()
        else:
            raw = _canonical_json_bytes(report)
            path_text = None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("revision report bytes are not valid JSON") from error
    if parsed != _json_value(report):
        raise ValueError("revision report object differs from its raw artifact bytes")
    return raw, path_text


def build_design_review_scene(
    revised_geometry: Any,
    revision_report: Mapping[str, Any],
    *,
    base_scene: Mapping[str, Any] | None = None,
    base_scene_bytes: bytes | None = None,
    revision_report_bytes: bytes | None = None,
    revision_report_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a WJ24 design-review scene by replacing only report-listed meshes.

    ``changed_display_solid_ids`` is the revision report's explicit mesh delta;
    the exporter relies on that source record instead of re-tessellating every
    retained object. The pinned parent snapshot and all baseline STL digests
    remain independently bound.
    """
    if not isinstance(revision_report, Mapping):
        raise TypeError("revision_report must be a mapping")
    report = _json_value(revision_report)
    if not isinstance(report, Mapping):
        raise TypeError("revision_report must normalize to a mapping")
    revision_id = str(
        report.get("revision_id")
        or getattr(revised_geometry, "trial_id", None)
        or getattr(revised_geometry, "layout_id", None)
        or DEFAULT_REVISION_ID
    )
    if not revision_id:
        raise ValueError("revision ID must be non-empty")
    reported_revision_id = report.get("revision_id")
    for field in ("layout_id", "trial_id"):
        geometry_id = getattr(revised_geometry, field, None)
        if geometry_id is not None and str(geometry_id) != revision_id:
            raise ValueError(f"revised geometry {field} differs from revision report ID")
    if reported_revision_id is not None and str(reported_revision_id) != revision_id:
        raise ValueError("revision report ID differs from geometry revision ID")

    base, _base_raw, parent_sha = _load_parent_scene(base_scene, base_scene_bytes)
    raw_report, report_path_text = _revision_report_bytes(
        report, revision_report_bytes, revision_report_path
    )
    report_sha = _sha256_bytes(raw_report)
    report_canonical_sha = _sha256_bytes(_canonical_json_bytes(report))
    changed_ids = _changed_solid_ids(report)
    shape_map, new_metadata = _geometry_display_shapes(revised_geometry)
    missing_shapes = changed_ids - set(shape_map)
    if missing_shapes:
        raise ValueError(f"revision-listed meshes are absent from revised geometry: {sorted(missing_shapes)}")

    old_solids = {str(row["id"]): row for row in base["solids"]}
    if len(old_solids) != len(base["solids"]):
        raise ValueError("pinned parent scene contains duplicate solid IDs")
    removed_rows = report.get("removed_display_solid_ids", [])
    if not isinstance(removed_rows, list) or any(not isinstance(name, str) for name in removed_rows):
        raise TypeError("removed display solid IDs must be a list of strings")
    removed_ids = set(removed_rows)
    if len(removed_ids) != len(removed_rows) or removed_ids != set(old_solids) - set(shape_map):
        raise ValueError("removed display IDs must exactly match parts absent from revised geometry")
    if removed_ids & changed_ids:
        raise ValueError("a removed display solid cannot also be changed")
    solids = {name: copy.deepcopy(row) for name, row in old_solids.items() if name not in removed_ids}
    new_ids = set(shape_map) - set(old_solids)
    # New overlay IDs must be explicitly included in the report's mesh delta.
    if not new_ids <= changed_ids:
        raise ValueError(f"new overlay IDs are missing from mesh delta: {sorted(new_ids - changed_ids)}")

    topologies = copy.deepcopy(base.get("triangle_topologies", {}))
    for solid_id in sorted(changed_ids):
        fresh_mesh = _shape_mesh(shape_map[solid_id])
        mesh_ref = _mesh_with_topology_reference(fresh_mesh, topologies)
        if solid_id in solids:
            solids[solid_id]["mesh"] = mesh_ref
            # Hardware identity fields are stable IDs but revision metadata can
            # change as receivers move; refresh just those non-mesh descriptors.
            if solid_id in new_metadata and solids[solid_id].get("display_class") == "candidate_hardware":
                for key in ("axis_id", "family", "station_id", "role", "display_class", "collision_envelope", "visual_status"):
                    if key in new_metadata[solid_id]:
                        solids[solid_id][key] = copy.deepcopy(new_metadata[solid_id][key])
        else:
            row = copy.deepcopy(new_metadata[solid_id])
            row["mesh"] = mesh_ref
            solids[solid_id] = row

    ordered_solids = [solids[name] for name in sorted(solids)]
    if len({row["id"] for row in ordered_solids}) != len(ordered_solids):
        raise ValueError("design-review scene solid IDs must be unique")
    referenced_topologies = {row["mesh"].get("triangle_topology_sha256") for row in ordered_solids}
    if None in referenced_topologies:
        raise ValueError("every display mesh must name a triangle topology")
    if not referenced_topologies <= set(topologies):
        raise ValueError("display mesh references a missing triangle topology")
    topologies = {key: topologies[key] for key in sorted(referenced_topologies)}
    for topology_id, row in topologies.items():
        data = base64.b64decode(row["triangle_indices_base64"], validate=True)
        if _sha256_bytes(data) != topology_id or len(data) == 0:
            raise ValueError("triangle topology archive contains a corrupt or empty row")
        if row.get("index_count") != row.get("triangle_count", 0) * 3:
            raise ValueError("triangle topology archive count metadata is inconsistent")

    inventory = _build_model_inventory(revised_geometry, report)
    moved_panel_ids = {row["axis_id"] for row in inventory["moved_panel_axes"]}
    all_panel_axes = set(inventory["fixed_panel_axes"]) | moved_panel_ids
    if len(all_panel_axes) != inventory["panel_screw_axis_count"]:
        raise ValueError("panel screw axis inventory contains duplicates or omissions")
    translations = _baseline_display_translations(inventory, report)
    expected_translation_names = {
        str(row.get("visual_name", f"fastener_{row['axis_id']}"))
        for row in inventory["moved_panel_axes"]
    }
    if set(translations) != expected_translation_names:
        raise ValueError("baseline display translations must cover exactly moved panel screw visuals")

    baseline_assets = dict(base["baseline_asset_sha256"])
    baseline_names = {str(name) for name in base.get("hidden_baseline_visual_names", ())}
    baseline_names.update(inventory["shared_hosts"])
    baseline_names.update(row["station_id"] for row in inventory["target_duties"])
    baseline_names.update(inventory["panel_replacements"])
    baseline_names.update(f"fastener_{row['axis_id']}" for row in inventory["removed_source_axes"])
    retained_panel_axis_names = {f"fastener_{axis}" for axis in all_panel_axes}
    if baseline_names & retained_panel_axis_names:
        raise ValueError("design-review hidden baseline policy would hide retained panel screws")
    if not set(translations) <= retained_panel_axis_names:
        raise ValueError("translated baseline visual is not a retained panel screw")

    frame_bolt_ids = sorted(row["axis_id"] for row in inventory["starting_frame_bolts"])
    baseline_policy = copy.deepcopy(base.get("baseline_scene_policy", {}))
    baseline_policy["retained_fixed_axis_ids"] = inventory["fixed_panel_axes"]
    baseline_policy["retained_fixed_axis_visual_names"] = sorted(retained_panel_axis_names)
    baseline_policy["moved_panel_axis_ids"] = sorted(moved_panel_ids)
    baseline_policy["retained_frame_bolt_ids"] = frame_bolt_ids
    baseline_policy["fixed_axes_and_starting_frame_bolts_rendered_once_from_pinned_baseline"] = True
    panel_names = {f"main_{band}_{side}" for band in ("lower", "upper") for side in ("left", "right")} | {"kicker_left", "kicker_right"}
    baseline_policy["preserved_visual_counts"]["visible_source_panels"] = len(panel_names - baseline_names)
    baseline_policy["hidden_counts"]["replaced_left_panels"] = len({name for name in panel_names & baseline_names if name.endswith("_left")})

    source_commit = _source_value(revised_geometry, report, "source_commit")
    inventory_sha = _source_value(
        revised_geometry, report, "source_inventory_sha256", "inventory_sha256"
    )
    if source_commit is None:
        source_commit = base.get("source_binding", {}).get("source_commit")
    if inventory_sha is None:
        inventory_sha = base.get("source_binding", {}).get("source_inventory_sha256")
    source_commit = str(source_commit)
    inventory_sha = _valid_sha(inventory_sha, "source inventory hash")
    if len(source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in source_commit.lower()):
        raise ValueError("source commit must be a full 40-character commit hash")

    counts = _json_value(getattr(revised_geometry, "counts", report.get("counts", {})))
    if not isinstance(counts, dict):
        counts = {}
    counts["rendered_overlay_solids"] = len(ordered_solids)
    counts["baseline_assets"] = len(baseline_assets)
    counts["visible_baseline_assets"] = len(baseline_assets) - len(baseline_names)
    counts["fixed_panel_axes"] = len(inventory["fixed_panel_axes"])
    counts["moved_panel_axes"] = len(moved_panel_ids)
    counts["panel_screw_axes_total"] = len(all_panel_axes)

    findings = _json_value(report.get("findings", ()))
    if not isinstance(findings, list):
        raise TypeError("revision findings must be a list")
    checks = _json_value(report.get("checks", report.get("revision_checks", {})))
    if checks is None:
        checks = {}

    historical = {
        "parent_scene_sha256": parent_sha,
        "parent_schema": base.get("schema"),
        "parent_layout_id": base.get("layout_id"),
        "parent_trial_id": base.get("trial_id"),
        "parent_source_commit": base.get("source_binding", {}).get("source_commit"),
        "parent_source_inventory_sha256": base.get("source_binding", {}).get("source_inventory_sha256"),
        "parent_composition_report_sha256": base.get("source_binding", {}).get("composition_report_sha256"),
        "parent_diagnostic_report_sha256": base.get("source_binding", {}).get("diagnostic_report_sha256"),
        "parent_manifest_sha256": base.get("baseline_manifest_sha256"),
        "historical_reports_are_not_current_revision_claims": True,
    }
    release = {key: False for key in RELEASE_FLAGS}
    scene = {
        "schema": SCHEMA,
        "candidate": CANDIDATE_ID,
        "baseline": base.get("baseline"),
        "layout_id": revision_id,
        "trial_id": revision_id,
        "revision_id": revision_id,
        "status": f"DESIGN REVIEW — {revision_id}",
        "layout_status": "DESIGN_REVIEW",
        "scope": (
            "Source-bound revised WJ24 geometry for design review. This scene records geometry and "
            "revision findings only; it does not establish acceptance, capacity, installation, or release."
        ),
        **{flag: False for flag in FALSE_CLAIM_FLAGS},
        "release": release,
        "source_binding": {
            "source_commit": source_commit,
            "source_inventory_sha256": inventory_sha,
            "parent_scene_sha256": parent_sha,
            "revision_report_sha256": report_sha,
            "revision_report_canonical_content_sha256": report_canonical_sha,
            "revision_report_path": report_path_text,
        },
        "revision_report_path": report_path_text,
        "revision_report_sha256": report_sha,
        "revision_report": report,
        "revision_checks": checks,
        "model_inventory": inventory,
        "baseline_manifest_path": base.get("baseline_manifest_path"),
        "baseline_manifest_sha256": base.get("baseline_manifest_sha256"),
        "baseline_asset_sha256": baseline_assets,
        "hidden_baseline_visual_names": sorted(baseline_names),
        "baseline_display_translations_mm": translations,
        "baseline_scene_policy": baseline_policy,
        "counts": counts,
        "display_mesh_encoding": {
            **base.get("display_mesh_encoding", {}),
            "encoding": DISPLAY_MESH_ENCODING,
            "unique_triangle_topology_count": len(topologies),
            "cad_geometry_modified": False,
            "incremental_mesh_delta_only": True,
        },
        "solids": ordered_solids,
        "triangle_topologies": topologies,
        "findings": findings,
        "historical_reference": historical,
        "limits": [
            "Design review only: no candidate acceptance, capacity, installation, or assembly proof is established.",
            "The revised blocks, hosts, panel bores, and occupied hardware envelopes are nominal CAD geometry.",
            f"Baseline STL hashes identify unchanged source assets; {len(moved_panel_ids)} panel screw instances are translated in the viewer.",
            "Historical WJ24 static, finite-contact, LED, and diagnostic reports are retained only as provenance references.",
            "No physical inspection, cutting, drilling, fabrication, structural, or climbing release is established.",
        ],
    }
    if any(scene.get(flag) is not False for flag in FALSE_CLAIM_FLAGS):
        raise ValueError("design-review acceptance and release claim flags must all remain false")
    if any(scene["release"].get(flag) is not False for flag in RELEASE_FLAGS):
        raise ValueError("design-review release flags must all remain false")
    return scene


def scene_json_bytes(scene: Mapping[str, Any]) -> bytes:
    """Serialize a completed scene deterministically; the caller chooses its output path."""
    if scene.get("schema") != SCHEMA or scene.get("layout_status") != "DESIGN_REVIEW":
        raise ValueError("only a WJ24 DESIGN_REVIEW scene may be serialized")
    if any(scene.get(flag) is not False for flag in FALSE_CLAIM_FLAGS):
        raise ValueError("design-review release and acceptance claims must remain false")
    return _canonical_json_bytes(scene) + b"\n"
