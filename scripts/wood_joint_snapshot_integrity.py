"""Read-only coherence audit for wood-joints diagnostic snapshots.

This checks recorded file fingerprints and cross-artifact WJ-04 dimensions.
It does not regenerate artifacts, run CAD, or establish design acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL

ROOT = Path(__file__).resolve().parents[1]
DOCS = "docs/wood-joints-mvp"
MANIFEST = f"{DOCS}/artifact-manifest.json"
WJ04_CONFIG_PATH = "mini_moonboard/wood_joint_wj04_config.py"

# Fixed scope. Active files must match current producers. Historical trials
# must match manifest bytes only; their old producers need not match today.
ACTIVE_WJ04_PATHS = {
    "probe": f"{DOCS}/wj04-probe.json",
    "mechanics": f"{DOCS}/wj04-early-mechanics.json",
    "tool_access": f"{DOCS}/wj04-tool-access.json",
}
WJ04_TOOL_ACCESS_SCHEMA = "wood_joint_wj04_tool_access/v1"
HISTORICAL_WJ04_PATHS = {
    "bolt_tool_screen": f"{DOCS}/wj04-bolt-tool-receiving-screen.json",
    "spacer_screen": f"{DOCS}/wj04-spacer-salvage-screen.json",
}
HISTORICAL_ARTIFACTS = {
    f"{DOCS}/wj04-narrow-3p5in-historical.json",
    f"{DOCS}/wj04-wide-3p75in-rejected.json",
    f"{DOCS}/wj04-wide-4in-rejected.json",
}
HISTORICAL_PATHS = set(HISTORICAL_WJ04_PATHS.values()) | HISTORICAL_ARTIFACTS
WJ04_PATHS = {**ACTIVE_WJ04_PATHS, **HISTORICAL_WJ04_PATHS}
CONTRACT_PATH = "wood-joints-candidate.json"
OUTER_HARDWARE_PATH = f"{DOCS}/hardware.json"
ACTIVE_VIEWER_PATH = "site/owner-wood-joints-layout-scene.json"
ACTIVE_WJ05_RECEIVER_PATH = f"{DOCS}/wj05-receiver-audit.json"
ACTIVE_DUTY_REGISTRY_PATH = f"{DOCS}/duty-registry.json"

PRODUCER_PATHS = {
    f"{DOCS}/interfaces.json": "scripts/wood_joint_clearance.py",
    f"{DOCS}/hardware.json": "scripts/wood_joint_clearance.py",
    f"{DOCS}/clearance.json": "scripts/wood_joint_clearance.py",
    f"{DOCS}/wj03-sequence-diagnostic.json": "scripts/wood_joint_wj03_sequence.py",
    f"{DOCS}/wj04-probe.json": "scripts/wood_joint_wj04_probe.py",
    f"{DOCS}/wj04-early-mechanics.json": "scripts/wood_joint_wj04_early_mechanics.py",
    f"{DOCS}/wj04-tool-access.json": "scripts/wood_joint_wj04_tool_access.py",
    f"{DOCS}/wj05-center-backer-transfer.json": "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
    ACTIVE_WJ05_RECEIVER_PATH: "scripts/wood_joint_wj05_receiver_audit.py",
    ACTIVE_DUTY_REGISTRY_PATH: "scripts/wood_joint_duty_registry.py",
    ACTIVE_VIEWER_PATH: "scripts/export_wood_joint_scene.py",
}

FILE_HASH_MAP_KEYS = {
    "dependency_sha256",
    "input_artifact_sha256",
    "input_sha256",
    "source_fingerprints_sha256",
    "source_hashes_sha256",
    "source_runtime_module_hashes_sha256",
    "source_snapshot_sha256",
    "runtime_module_sha256",
}
SCALAR_FILE_HASH_PATHS = {
    "source_inventory_sha256": f"{DOCS}/source-inventory.json",
    "interfaces_source_inventory_sha256": f"{DOCS}/source-inventory.json",
    "receiver_audit_source_inventory_sha256": f"{DOCS}/source-inventory.json",
    "wj04_source_inventory_sha256": f"{DOCS}/source-inventory.json",
    "config_source_sha256": WJ04_CONFIG_PATH,
}
MANIFEST_IDENTITY_FIELDS = ("candidate", "source_commit")
DIMENSION_TOLERANCE = 1e-3
REQUIRED_MANIFEST_PATHS = (
    set(ACTIVE_WJ04_PATHS.values())
    | set(HISTORICAL_PATHS)
    | {ACTIVE_VIEWER_PATH, ACTIVE_WJ05_RECEIVER_PATH, ACTIVE_DUTY_REGISTRY_PATH}
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def _file_state(root: Path, relative_path: str, declared: Any) -> dict[str, Any]:
    path = root / relative_path
    current = _sha256(path) if path.is_file() else None
    status = (
        "missing"
        if current is None
        else ("consistent" if current == declared else "stale")
    )
    return {
        "path": relative_path,
        "declared_sha256": declared,
        "current_sha256": current,
        "status": status,
    }


def _walk_binding_maps(
    value: Any,
    context: str,
    bindings: list[tuple[str, str, Any]],
) -> None:
    """Collect only known path-to-hash fields; ignore geometric fingerprints."""
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_binding_maps(item, f"{context}[{index}]", bindings)
        return
    if not isinstance(value, dict):
        return
    for key, item in value.items():
        child = f"{context}.{key}" if context else key
        if key in FILE_HASH_MAP_KEYS and isinstance(item, dict):
            for relative_path, digest in item.items():
                if isinstance(relative_path, str):
                    bindings.append((relative_path, child, digest))
        elif key in SCALAR_FILE_HASH_PATHS and isinstance(item, str):
            bindings.append((SCALAR_FILE_HASH_PATHS[key], child, item))
        if isinstance(item, (dict, list)):
            _walk_binding_maps(item, child, bindings)


def _embedded_bindings(
    root: Path, relative_path: str, document: dict[str, Any]
) -> list[dict[str, Any]]:
    if relative_path in HISTORICAL_PATHS:
        return []
    raw: list[tuple[str, str, Any]] = []
    _walk_binding_maps(document, "", raw)

    producer_path = PRODUCER_PATHS.get(relative_path)
    producer_sha = document.get("producer_sha256")
    if producer_path and isinstance(producer_sha, str):
        raw.append((producer_path, "producer_sha256", producer_sha))
    producer = document.get("producer")
    producer_script_sha = (
        producer.get("script_sha256") if isinstance(producer, dict) else None
    )
    if producer_path and isinstance(producer_script_sha, str):
        raw.append((producer_path, "producer.script_sha256", producer_script_sha))
    authority = document.get("authority")
    if producer_path and isinstance(authority, dict):
        authority_sha = authority.get("producer_sha256")
        if isinstance(authority_sha, str):
            raw.append((producer_path, "authority.producer_sha256", authority_sha))

    result = []
    for path, context, digest in raw:
        checked = _file_state(root, path, digest)
        checked["recorded_in"] = relative_path
        checked["field"] = context
        result.append(checked)
    return sorted(
        result, key=lambda row: (row["path"], row["recorded_in"], row["field"])
    )


def _state(rows: list[dict[str, Any]]) -> str:
    statuses = {row.get("status") for row in rows}
    if "missing" in statuses:
        return "missing"
    if "stale" in statuses:
        return "stale"
    return "consistent"


def _same_value(
    actual: Any, expected: Any, tolerance: float = DIMENSION_TOLERANCE
) -> bool:
    if isinstance(actual, (int, float)) and not isinstance(actual, bool):
        return (
            isinstance(expected, (int, float))
            and not isinstance(expected, bool)
            and abs(float(actual) - float(expected)) <= tolerance
        )
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _same_value(left, right, tolerance)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def _dimension_check(
    name: str,
    actual: Any,
    expected: Any,
    *,
    tolerance: float = DIMENSION_TOLERANCE,
) -> dict[str, Any]:
    if actual is None or expected is None:
        status = "missing"
    else:
        status = "consistent" if _same_value(actual, expected, tolerance) else "stale"
    return {
        "check": name,
        "actual": actual,
        "expected": expected,
        "tolerance": tolerance,
        "status": status,
    }


def _distance(first: list[float], second: list[float]) -> float:
    return (
        sum((float(a) - float(b)) ** 2 for a, b in zip(first, second, strict=True))
        ** 0.5
    )


def _mean_point(points: list[list[float]]) -> list[float] | None:
    if not points or any(
        not isinstance(point, list) or len(point) != 3 for point in points
    ):
        return None
    return [
        sum(float(point[index]) for point in points) / len(points) for index in range(3)
    ]


def _plain(value: Any) -> Any:
    """Convert config tuples/dataclasses into JSON-shaped values."""
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _canonical_wj04() -> dict[str, Any]:
    """Return active WJ-04 identity from its CAD-free shared config."""
    config = WJ04_TRIAL
    raw = config.as_dict()
    stacks = {row["stack_id"]: row for row in raw["stacks"]}
    configured_stacks = {stack.stack_id: stack for stack in config.stacks}
    stack_identities = {}
    for stack_id, row in stacks.items():
        configured = configured_stacks[stack_id]
        hardware = configured.hardware_candidate
        stack_identities[stack_id] = {
            "bolt_candidate_id": hardware.candidate_id,
            "bolt_sku": hardware.sku,
            "axis_global_xyz_mm": _plain(row["axis_point_global_mm"]),
            "direction_global_xyz": _plain(row["axis_direction_global"]),
            "grip_mm": row["grip_mm"],
            "nominal_under_head_length_mm": hardware.nominal_length_mm,
            "layers": [_plain(layer) for layer in row["layers"]],
            "cad_envelope": _plain(row["cad_envelope"]),
        }
    fasteners = config.fasteners
    catalog_candidate_ids = {
        "bolts": sorted(candidate.candidate_id for candidate in fasteners.bolts),
        "nut": fasteners.nut.candidate_id,
        "washer": fasteners.washer.candidate_id,
        "tools": sorted(candidate.candidate_id for candidate in fasteners.tools),
    }
    catalog_candidates = [
        {
            "kind": kind,
            "candidate_id": candidate.candidate_id,
            "sku": getattr(candidate, "sku", None),
            "manufacturer": candidate.manufacturer,
            "status": candidate.status,
        }
        for kind, candidates in (
            ("bolt", fasteners.bolts),
            ("nut", (fasteners.nut,)),
            ("washer", (fasteners.washer,)),
            ("tool", fasteners.tools),
        )
        for candidate in candidates
    ]
    cleat = next(member for member in config.members if member.role == "cleat")
    return {
        "trial_id": config.trial_id,
        "trial_config_sha256": config.canonical_sha256,
        "development_candidate_id": config.development_candidate_id,
        "preserved_selected_candidate_id": config.preserved_selected_candidate_id,
        "station_id": config.station_id,
        "source_variant": config.source_variant,
        "source_commit": config.source_commit,
        "source_inventory_sha256": config.source_inventory_sha256,
        "section_x_t_n_mm": _plain(cleat.size_x_t_n_mm),
        "grain_axis": cleat.grain_axis,
        "stacks": stack_identities,
        "catalog_candidate_ids": catalog_candidate_ids,
        "catalog_candidates": catalog_candidates,
        "stock_grade_verified": config.stock_grade_verified,
        "purchase_approved": config.purchase_approved,
        "drilling_released": config.drilling_released,
        "fabrication_released": config.fabrication_released,
        "structural_released": config.structural_released,
        "status": config.status,
    }


def _historical_screen(root: Path, name: str, probe: dict[str, Any]) -> dict[str, Any]:
    relative_path = HISTORICAL_WJ04_PATHS[name]
    document = _read_json(root / relative_path)
    if document is None:
        return {
            "path": relative_path,
            "scope": "historical_reference_only",
            "status": "missing",
        }

    stacks = probe.get("stacks") if isinstance(probe.get("stacks"), dict) else {}
    rail = stacks.get("rail_1") if isinstance(stacks.get("rail_1"), dict) else {}
    section = (
        probe.get("stock", {}).get("section_x_t_n_mm")
        if isinstance(probe.get("stock"), dict)
        else None
    )
    comparisons = [
        {
            "field": "geometry_source",
            "recorded": document.get("geometry_source"),
            "active_probe": ACTIVE_WJ04_PATHS["probe"],
        },
        {
            "field": "station",
            "recorded": document.get("station"),
            "active_probe": probe.get("station"),
        },
        {
            "field": "rail_wood_grip_mm",
            "recorded": document.get("wood_grip_mm"),
            "active_probe": rail.get("grip_mm"),
        },
    ]
    if name == "bolt_tool_screen":
        comparisons.append(
            {
                "field": "cleat_x_t_n_mm",
                "recorded": document.get("cleat_x_t_n_mm"),
                "active_probe": section,
            }
        )
    statuses = [
        "missing"
        if row["recorded"] is None or row["active_probe"] is None
        else "match"
        if _same_value(row["recorded"], row["active_probe"])
        else "different"
        for row in comparisons
    ]
    return {
        "path": relative_path,
        "scope": "historical_reference_only",
        "status": "missing"
        if "missing" in statuses
        else (
            "different_historical_configuration"
            if "different" in statuses
            else "matches_active_probe_dimensions"
        ),
        "candidate": document.get("candidate"),
        "recorded_status": document.get("status"),
        "comparisons": comparisons,
        "claim_limit": "Historical diagnostic comparison; does not stale or validate active configuration.",
    }


def _wj04_dimensions(root: Path) -> dict[str, Any]:
    documents = {
        name: _read_json(root / relative) for name, relative in WJ04_PATHS.items()
    }
    missing = [
        path for name, path in ACTIVE_WJ04_PATHS.items() if documents.get(name) is None
    ]
    probe = documents["probe"] or {}
    mechanics = documents["mechanics"] or {}
    tool_access = documents["tool_access"] or {}
    canonical = _canonical_wj04()
    stock = probe.get("stock") if isinstance(probe.get("stock"), dict) else {}
    section = stock.get("section_x_t_n_mm")
    stacks = probe.get("stacks") if isinstance(probe.get("stacks"), dict) else {}
    rail_ids = ("rail_1", "rail_2")
    principal_ids = ("upright_1", "upright_2")
    checks = [
        _dimension_check(
            "mechanics candidate vs probe",
            mechanics.get("candidate"),
            probe.get("candidate"),
        ),
        _dimension_check(
            "mechanics station vs probe", mechanics.get("station"), probe.get("station")
        ),
        _dimension_check("probe section dimensions present", section, section),
        _dimension_check(
            "probe trial ID vs shared config",
            probe.get("trial_id"),
            canonical["trial_id"],
        ),
        _dimension_check(
            "probe trial config fingerprint vs shared config",
            probe.get("trial_config_sha256"),
            canonical["trial_config_sha256"],
        ),
        _dimension_check(
            "probe source inventory fingerprint vs shared config",
            probe.get("source_inventory_sha256"),
            canonical["source_inventory_sha256"],
        ),
        _dimension_check(
            "probe station vs shared config",
            probe.get("station"),
            canonical["station_id"],
        ),
        _dimension_check(
            "probe source commit vs shared config",
            probe.get("source_commit"),
            canonical["source_commit"],
        ),
        _dimension_check(
            "probe section dimensions vs shared config",
            section,
            canonical["section_x_t_n_mm"],
        ),
        _dimension_check(
            "probe stock grain axis vs shared config",
            stock.get("grain_axis"),
            canonical["grain_axis"],
        ),
        _dimension_check(
            "probe nominal rail bolt length vs shared config",
            probe.get("rail_nominal_partial_thread_bolt_length_mm"),
            canonical["stacks"]["rail_1"]["nominal_under_head_length_mm"],
        ),
        _dimension_check(
            "probe stock grade verification vs shared config",
            stock.get("actual_stock_and_grade_verified"),
            canonical["stock_grade_verified"],
        ),
        _dimension_check(
            "probe purchase approval vs shared config",
            probe.get("purchase_approved"),
            canonical["purchase_approved"],
        ),
        _dimension_check(
            "probe drilling release vs shared config",
            probe.get("drilling_released"),
            canonical["drilling_released"],
        ),
        _dimension_check(
            "probe fabrication release vs shared config",
            probe.get("fabrication_released"),
            canonical["fabrication_released"],
        ),
        _dimension_check(
            "probe structural release vs shared config",
            probe.get("structural_released"),
            canonical["structural_released"],
        ),
    ]

    mechanics_trial = mechanics.get("canonical_trial")
    mechanics_trial = mechanics_trial if isinstance(mechanics_trial, dict) else {}
    checks.extend(
        [
            _dimension_check(
                "mechanics trial ID vs shared config",
                mechanics_trial.get("trial_id"),
                canonical["trial_id"],
            ),
            _dimension_check(
                "mechanics trial config fingerprint vs shared config",
                mechanics_trial.get("trial_config_sha256"),
                canonical["trial_config_sha256"],
            ),
            _dimension_check(
                "mechanics active probe fingerprint vs shared config",
                mechanics_trial.get("active_probe_trial_config_sha256"),
                canonical["trial_config_sha256"],
            ),
            _dimension_check(
                "mechanics source inventory fingerprint vs shared config",
                mechanics_trial.get("source_inventory_sha256"),
                canonical["source_inventory_sha256"],
            ),
            _dimension_check(
                "mechanics cleat section vs shared config",
                mechanics_trial.get("cleat_size_x_t_n_mm"),
                canonical["section_x_t_n_mm"],
            ),
            _dimension_check(
                "mechanics purchase approval vs shared config",
                mechanics_trial.get("purchase_approved"),
                canonical["purchase_approved"],
            ),
            _dimension_check(
                "mechanics drilling release vs shared config",
                mechanics_trial.get("drilling_released"),
                canonical["drilling_released"],
            ),
            _dimension_check(
                "mechanics fabrication release vs shared config",
                mechanics_trial.get("fabrication_released"),
                canonical["fabrication_released"],
            ),
            _dimension_check(
                "mechanics structural release vs shared config",
                mechanics_trial.get("structural_released"),
                canonical["structural_released"],
            ),
        ]
    )
    checks.extend(
        [
            _dimension_check(
                "tool-access schema",
                tool_access.get("schema"),
                WJ04_TOOL_ACCESS_SCHEMA,
            ),
            _dimension_check(
                "tool-access trial ID vs shared config",
                tool_access.get("trial_id"),
                canonical["trial_id"],
            ),
            _dimension_check(
                "tool-access trial config fingerprint vs shared config",
                tool_access.get("trial_config_sha256"),
                canonical["trial_config_sha256"],
            ),
            _dimension_check(
                "tool-access source inventory fingerprint vs shared config",
                tool_access.get("source_inventory_sha256"),
                canonical["source_inventory_sha256"],
            ),
            _dimension_check(
                "tool-access station vs shared config",
                tool_access.get("station_id"),
                canonical["station_id"],
            ),
        ]
    )

    candidate_ids = probe.get("catalog_candidate_ids")
    checks.append(
        _dimension_check(
            "probe catalog candidate IDs vs shared config",
            candidate_ids,
            canonical["catalog_candidate_ids"],
        )
    )

    for stack_id, expected in canonical["stacks"].items():
        actual = stacks.get(stack_id) if isinstance(stacks.get(stack_id), dict) else {}
        for field in (
            "axis_global_xyz_mm",
            "direction_global_xyz",
            "grip_mm",
            "nominal_under_head_length_mm",
            "layers",
            "cad_envelope",
            "bolt_candidate_id",
            "bolt_sku",
        ):
            checks.append(
                _dimension_check(
                    f"{stack_id} {field} vs shared config",
                    actual.get(field),
                    expected[field],
                )
            )

    summaries = mechanics.get("interface_summary")
    summaries = summaries if isinstance(summaries, dict) else {}
    probe_contact_areas = probe.get("contact_area_mm2")
    probe_contact_areas = (
        probe_contact_areas if isinstance(probe_contact_areas, dict) else {}
    )
    for interface, stack_ids, expected_area, expected_span in (
        ("rail", rail_ids, "x_n", "x"),
        ("principal", principal_ids, "t_n", "n"),
    ):
        summary = summaries.get(interface)
        summary = summary if isinstance(summary, dict) else {}
        points = [
            stacks.get(stack_id, {}).get("axis_global_xyz_mm") for stack_id in stack_ids
        ]
        points_valid = all(
            isinstance(point, list) and len(point) == 3 for point in points
        )
        centroid = _mean_point(points) if points_valid else None
        spacing = _distance(points[0], points[1]) if points_valid else None
        if not isinstance(section, list) or len(section) != 3:
            area = span = None
        elif expected_area == "x_n":
            area, span = (
                round(float(section[0]) * float(section[2]), 6),
                float(section[0]),
            )
        else:
            area, span = (
                round(float(section[1]) * float(section[2]), 6),
                float(section[2]),
            )
        probe_area_key = (
            "rail_to_cleat" if interface == "rail" else "principal_to_cleat"
        )
        finite_probe_area = probe_contact_areas.get(probe_area_key)
        if (
            isinstance(finite_probe_area, (int, float))
            and not isinstance(finite_probe_area, bool)
            and isinstance(area, (int, float))
            and not isinstance(area, bool)
            and area != 0
        ):
            finite_minus_rectangle = round(float(finite_probe_area) - float(area), 6)
            finite_to_rectangle_ratio = round(float(finite_probe_area) / float(area), 6)
        else:
            finite_minus_rectangle = finite_to_rectangle_ratio = None
        contact = summary.get("contact_face_geometry")
        contact = contact if isinstance(contact, dict) else {}
        measurement = contact.get("finite_probe_area_measurement")
        measurement = measurement if isinstance(measurement, dict) else {}
        probe_producer = probe.get("producer_sha256")
        finite_probe_source_field = f"active_probe.contact_area_mm2.{probe_area_key}"
        checks.extend(
            [
                _dimension_check(
                    f"{interface} mechanics bolt IDs vs probe stacks",
                    summary.get("group_stack_ids"),
                    list(stack_ids),
                ),
                _dimension_check(
                    f"{interface} mechanics finite-probe area vs probe report",
                    summary.get("finite_probe_contact_area_mm2"),
                    finite_probe_area,
                ),
                _dimension_check(
                    f"{interface} mechanics face finite-probe area vs probe report",
                    contact.get("finite_probe_contact_area_mm2"),
                    finite_probe_area,
                ),
                _dimension_check(
                    f"{interface} mechanics nominal rectangle area vs probe section",
                    summary.get("canonical_bounds_rectangle_area_mm2"),
                    area,
                ),
                _dimension_check(
                    f"{interface} mechanics face rectangle area vs probe section",
                    contact.get("canonical_bounds_rectangle_area_mm2"),
                    area,
                ),
                _dimension_check(
                    f"{interface} mechanics finite-probe area source field",
                    measurement.get("source_field"),
                    finite_probe_source_field,
                ),
                _dimension_check(
                    f"{interface} mechanics finite-probe producer hash vs probe",
                    measurement.get("probe_producer_sha256"),
                    probe_producer,
                ),
                _dimension_check(
                    f"{interface} mechanics finite-probe rectangle difference",
                    summary.get("finite_probe_minus_rectangle_area_mm2"),
                    finite_minus_rectangle,
                ),
                _dimension_check(
                    f"{interface} mechanics face finite-probe rectangle difference",
                    contact.get("finite_probe_minus_rectangle_area_mm2"),
                    finite_minus_rectangle,
                ),
                _dimension_check(
                    f"{interface} mechanics face finite-probe rectangle ratio",
                    contact.get("finite_probe_to_rectangle_area_ratio"),
                    finite_to_rectangle_ratio,
                    tolerance=1e-6,
                ),
                _dimension_check(
                    f"{interface} mechanics row span vs probe section",
                    contact.get("row_span_mm"),
                    span,
                ),
                _dimension_check(
                    f"{interface} mechanics bolt spacing vs probe axes",
                    summary.get("bolt_spacing_mm"),
                    spacing,
                ),
                _dimension_check(
                    f"{interface} mechanics centroid vs probe axes",
                    summary.get("centroid_global_xyz_mm"),
                    centroid,
                ),
            ]
        )

    statuses = {row["status"] for row in checks}
    dimension_status = (
        "stale"
        if "stale" in statuses
        else "missing"
        if missing or "missing" in statuses
        else "consistent"
    )
    return {
        "status": dimension_status,
        "candidate": probe.get("candidate"),
        "source_commit": probe.get("source_commit"),
        "station": probe.get("station"),
        "geometry_identity": {
            "source_path": WJ04_PATHS["probe"],
            "trial_id": probe.get("trial_id"),
            "trial_config_sha256": probe.get("trial_config_sha256"),
            "canonical_trial_config_sha256": canonical["trial_config_sha256"],
            "source_inventory_sha256": probe.get("source_inventory_sha256"),
            "section_x_t_n_mm": section,
            "catalog_candidate_ids": candidate_ids,
            "rail_stacks": {
                stack_id: _stack_identity(stacks.get(stack_id)) for stack_id in rail_ids
            },
            "principal_stacks": {
                stack_id: _stack_identity(stacks.get(stack_id))
                for stack_id in principal_ids
            },
            "rail_grip_mm": (
                stacks.get("rail_1", {}).get("grip_mm")
                if isinstance(stacks.get("rail_1"), dict)
                else None
            ),
            "principal_grip_mm": (
                stacks.get("upright_1", {}).get("grip_mm")
                if isinstance(stacks.get("upright_1"), dict)
                else None
            ),
        },
        "mechanics_identity": {
            interface: {
                "group_stack_ids": summaries.get(interface, {}).get("group_stack_ids")
                if isinstance(summaries.get(interface), dict)
                else None,
                "finite_probe_contact_area_mm2": summaries.get(interface, {}).get(
                    "finite_probe_contact_area_mm2"
                )
                if isinstance(summaries.get(interface), dict)
                else None,
                "canonical_bounds_rectangle_area_mm2": summaries.get(interface, {}).get(
                    "canonical_bounds_rectangle_area_mm2"
                )
                if isinstance(summaries.get(interface), dict)
                else None,
                "finite_probe_minus_rectangle_area_mm2": summaries.get(
                    interface, {}
                ).get("finite_probe_minus_rectangle_area_mm2")
                if isinstance(summaries.get(interface), dict)
                else None,
                "finite_probe_to_rectangle_area_ratio": (
                    summaries[interface]
                    .get("contact_face_geometry", {})
                    .get("finite_probe_to_rectangle_area_ratio")
                    if isinstance(summaries.get(interface), dict)
                    and isinstance(
                        summaries[interface].get("contact_face_geometry"), dict
                    )
                    else None
                ),
                "bolt_spacing_mm": summaries.get(interface, {}).get("bolt_spacing_mm")
                if isinstance(summaries.get(interface), dict)
                else None,
                "centroid_global_xyz_mm": summaries.get(interface, {}).get(
                    "centroid_global_xyz_mm"
                )
                if isinstance(summaries.get(interface), dict)
                else None,
            }
            for interface in ("rail", "principal")
        },
        "tool_access_identity": {
            "path": ACTIVE_WJ04_PATHS["tool_access"],
            "schema": tool_access.get("schema"),
            "trial_id": tool_access.get("trial_id"),
            "trial_config_sha256": tool_access.get("trial_config_sha256"),
            "source_inventory_sha256": tool_access.get("source_inventory_sha256"),
            "station_id": tool_access.get("station_id"),
        },
        "checks": checks,
        "missing_paths": missing,
        "active_shared_configuration": {
            "trial_id": canonical["trial_id"],
            "trial_config_sha256": canonical["trial_config_sha256"],
            "source_inventory_sha256": canonical["source_inventory_sha256"],
            "section_x_t_n_mm": canonical["section_x_t_n_mm"],
            "catalog_candidate_ids": canonical["catalog_candidate_ids"],
        },
        "historical_stack_screens": [
            _historical_screen(root, name, probe) for name in HISTORICAL_WJ04_PATHS
        ],
        "claim_limit": "Dimensional snapshot comparison only; no geometry, mechanics, capacity, or design acceptance is established.",
    }


def _stack_identity(stack: Any) -> dict[str, Any] | None:
    if not isinstance(stack, dict):
        return None
    keys = (
        "axis_global_xyz_mm",
        "direction_global_xyz",
        "grip_mm",
        "nominal_under_head_length_mm",
        "provisional_length_margin_mm",
    )
    return {key: stack[key] for key in keys if key in stack}


def _active_viewer_identity(root: Path, canonical: dict[str, Any]) -> dict[str, Any]:
    document = _read_json(root / ACTIVE_VIEWER_PATH)
    if document is None:
        return {
            "path": ACTIVE_VIEWER_PATH,
            "scope": "active_combined_viewer",
            "status": "missing",
            "checks": [],
        }
    trials = document.get("trials") if isinstance(document.get("trials"), dict) else {}
    wj04 = trials.get("wj04") if isinstance(trials.get("wj04"), dict) else {}
    checks = [
        _dimension_check(
            "combined viewer schema",
            document.get("schema"),
            "owner_wood_joints_layout_scene/v2",
        ),
        _dimension_check(
            "combined viewer WJ04 trial ID vs shared config",
            wj04.get("trial_id"),
            canonical["trial_id"],
        ),
        _dimension_check(
            "combined viewer WJ04 config fingerprint vs shared config",
            wj04.get("config_sha256"),
            canonical["trial_config_sha256"],
        ),
        _dimension_check(
            "combined viewer WJ04 source commit vs shared config",
            wj04.get("source_commit"),
            canonical["source_commit"],
        ),
        _dimension_check(
            "combined viewer WJ04 source inventory fingerprint vs shared config",
            wj04.get("source_inventory_sha256"),
            canonical["source_inventory_sha256"],
        ),
    ]
    freshness = wj04.get("report_freshness")
    stale_paths = freshness.get("stale_paths") if isinstance(freshness, dict) else None
    checks.append(
        _dimension_check(
            "combined viewer WJ04 report freshness",
            stale_paths,
            [],
        )
    )
    checks.append(
        _dimension_check(
            "combined viewer WJ04 report freshness flag",
            freshness.get("fresh") if isinstance(freshness, dict) else None,
            True,
        )
    )
    statuses = {row["status"] for row in checks}
    status = (
        "stale"
        if "stale" in statuses
        else "missing"
        if "missing" in statuses
        else "consistent"
    )
    return {
        "path": ACTIVE_VIEWER_PATH,
        "scope": "active_combined_viewer",
        "schema": document.get("schema"),
        "status": status,
        "wj04_trial_id": wj04.get("trial_id"),
        "wj04_config_sha256": wj04.get("config_sha256"),
        "source_commit": wj04.get("source_commit"),
        "source_inventory_sha256": wj04.get("source_inventory_sha256"),
        "integrated_clearance": document.get("integrated_clearance"),
        "geometry_solid_count": wj04.get("geometry_solid_count"),
        "checks": checks,
        "claim_limit": "Viewer config binding only; rendered geometry and clearance do not establish acceptance or release.",
    }


def _active_configuration_identity(
    root: Path, manifest: dict[str, Any] | None
) -> dict[str, Any]:
    contract = _read_json(root / CONTRACT_PATH)
    probe = _read_json(root / ACTIVE_WJ04_PATHS["probe"]) or {}
    tool_access = _read_json(root / ACTIVE_WJ04_PATHS["tool_access"]) or {}
    hardware = _read_json(root / OUTER_HARDWARE_PATH) or {}
    canonical = _canonical_wj04()
    source = contract.get("source") if isinstance(contract, dict) else None
    source = source if isinstance(source, dict) else {}
    stacks = probe.get("stacks") if isinstance(probe.get("stacks"), dict) else {}
    config_candidate = contract.get("candidate") if isinstance(contract, dict) else None
    config_commit = source.get("repository_commit")
    config_path = root / WJ04_CONFIG_PATH
    config_source_sha = _sha256(config_path) if config_path.is_file() else None
    viewer_identity = _active_viewer_identity(root, canonical)
    active_trial_checks = [
        _dimension_check(
            "probe trial ID vs shared config",
            probe.get("trial_id"),
            canonical["trial_id"],
        ),
        _dimension_check(
            "probe station vs shared config",
            probe.get("station"),
            canonical["station_id"],
        ),
        _dimension_check(
            "probe source commit vs shared config",
            probe.get("source_commit"),
            canonical["source_commit"],
        ),
        _dimension_check(
            "probe trial config fingerprint vs shared config",
            probe.get("trial_config_sha256"),
            canonical["trial_config_sha256"],
        ),
        _dimension_check(
            "probe source inventory fingerprint vs shared config",
            probe.get("source_inventory_sha256"),
            canonical["source_inventory_sha256"],
        ),
        _dimension_check(
            "probe section dimensions vs shared config",
            probe.get("stock", {}).get("section_x_t_n_mm")
            if isinstance(probe.get("stock"), dict)
            else None,
            canonical["section_x_t_n_mm"],
        ),
    ]
    tool_access_checks = [
        _dimension_check(
            "tool-access schema",
            tool_access.get("schema"),
            WJ04_TOOL_ACCESS_SCHEMA,
        ),
        _dimension_check(
            "tool-access trial ID vs shared config",
            tool_access.get("trial_id"),
            canonical["trial_id"],
        ),
        _dimension_check(
            "tool-access trial config fingerprint vs shared config",
            tool_access.get("trial_config_sha256"),
            canonical["trial_config_sha256"],
        ),
        _dimension_check(
            "tool-access source inventory fingerprint vs shared config",
            tool_access.get("source_inventory_sha256"),
            canonical["source_inventory_sha256"],
        ),
        _dimension_check(
            "tool-access station vs shared config",
            tool_access.get("station_id"),
            canonical["station_id"],
        ),
    ]

    conflicts = [
        {
            "field": field,
            "values": sorted({value for value in values if value is not None}),
        }
        for field, values in (
            (
                "candidate",
                [
                    config_candidate,
                    manifest.get("candidate") if isinstance(manifest, dict) else None,
                    probe.get("candidate"),
                    hardware.get("candidate"),
                ],
            ),
            (
                "source_commit",
                [
                    config_commit,
                    manifest.get("source_commit")
                    if isinstance(manifest, dict)
                    else None,
                    probe.get("source_commit"),
                ],
            ),
        )
        if len({value for value in values if value is not None}) > 1
    ]
    active_trial_statuses = {row["status"] for row in active_trial_checks}
    identity_status = (
        "missing"
        if contract is None or config_source_sha is None
        else "stale"
        if conflicts
        or "stale" in active_trial_statuses
        or "stale" in {row["status"] for row in tool_access_checks}
        or viewer_identity["status"] == "stale"
        else "missing"
        if "missing" in active_trial_statuses
        or "missing" in {row["status"] for row in tool_access_checks}
        or viewer_identity["status"] == "missing"
        else "consistent"
    )
    return {
        "status": identity_status,
        "contract": {
            "path": CONTRACT_PATH,
            "present": contract is not None,
            "sha256": _sha256(root / CONTRACT_PATH)
            if (root / CONTRACT_PATH).is_file()
            else None,
            "candidate": config_candidate,
            "status": contract.get("status") if isinstance(contract, dict) else None,
            "source_commit": config_commit,
            "source_variant": source.get("source_variant"),
        },
        "manifest": {
            "candidate": manifest.get("candidate")
            if isinstance(manifest, dict)
            else None,
            "source_commit": manifest.get("source_commit")
            if isinstance(manifest, dict)
            else None,
        },
        "shared_wj04_configuration": {
            "path": WJ04_CONFIG_PATH,
            "present": config_source_sha is not None,
            "source_sha256": config_source_sha,
            "trial_id": canonical["trial_id"],
            "trial_config_sha256": canonical["trial_config_sha256"],
            "source_inventory_sha256": canonical["source_inventory_sha256"],
            "development_candidate_id": canonical["development_candidate_id"],
            "preserved_selected_candidate_id": canonical[
                "preserved_selected_candidate_id"
            ],
            "source_variant": canonical["source_variant"],
        },
        "active_combined_viewer": viewer_identity,
        "active_tool_access_report": {
            "path": ACTIVE_WJ04_PATHS["tool_access"],
            "schema": tool_access.get("schema"),
            "candidate": tool_access.get("candidate"),
            "source_commit": tool_access.get("source_commit"),
            "trial_id": tool_access.get("trial_id"),
            "station_id": tool_access.get("station_id"),
            "source_variant": tool_access.get("source_variant"),
            "source_inventory_sha256": tool_access.get("source_inventory_sha256"),
            "trial_config_sha256": tool_access.get("trial_config_sha256"),
            "configuration_checks": tool_access_checks,
        },
        "wj04_probe": {
            "candidate": probe.get("candidate"),
            "source_commit": probe.get("source_commit"),
            "station": probe.get("station"),
            "trial_id": probe.get("trial_id"),
            "trial_config_sha256": probe.get("trial_config_sha256"),
            "source_inventory_sha256": probe.get("source_inventory_sha256"),
            "section_x_t_n_mm": probe.get("stock", {}).get("section_x_t_n_mm")
            if isinstance(probe.get("stock"), dict)
            else None,
        },
        "outer_hardware_snapshot": {
            "path": OUTER_HARDWARE_PATH,
            "scope": hardware.get("scope"),
            "candidate": hardware.get("candidate"),
            "hardware_selected": hardware.get("hardware_selected"),
            "counts": hardware.get("counts"),
        },
        "active_wj04_hardware_identity": {
            "source_path": ACTIVE_WJ04_PATHS["probe"],
            "product_candidate_status": "catalog_candidates_for_diagnostic_modeling",
            "catalog_candidate_ids": canonical["catalog_candidate_ids"],
            "catalog_candidates": canonical["catalog_candidates"],
            "stacks": {
                name: {
                    **(canonical["stacks"][name]),
                    "report_identity": _stack_identity(stacks.get(name)),
                }
                for name in ("rail_1", "rail_2", "upright_1", "upright_2")
            },
            "acceptance": {
                "accepted_hardware_established": False,
                "stock_grade_verified": canonical["stock_grade_verified"],
                "purchase_approved": canonical["purchase_approved"],
                "drilling_released": canonical["drilling_released"],
                "fabrication_released": canonical["fabrication_released"],
                "structural_released": canonical["structural_released"],
                "capacity_verified": False,
                "catalog_candidate_identity_establishes_acceptance": False,
            },
            "probe_config_checks": active_trial_checks,
        },
        "historical_trials": [
            _historical_trial_identity(root, relative_path)
            for relative_path in sorted(HISTORICAL_ARTIFACTS)
        ],
        "candidate_or_commit_conflicts": conflicts,
    }


def _historical_trial_identity(root: Path, relative_path: str) -> dict[str, Any]:
    document = _read_json(root / relative_path)
    if document is None:
        return {
            "path": relative_path,
            "scope": "historical_manifest_only",
            "status": "missing",
        }
    stock = document.get("stock") if isinstance(document.get("stock"), dict) else {}
    return {
        "path": relative_path,
        "scope": "historical_manifest_only",
        "candidate": document.get("candidate"),
        "source_commit": document.get("source_commit"),
        "trial_id": document.get("trial_id"),
        "recorded_status": document.get("status"),
        "section_x_t_n_mm": stock.get("section_x_t_n_mm"),
        "rail_nominal_partial_thread_bolt_length_mm": document.get(
            "rail_nominal_partial_thread_bolt_length_mm"
        ),
    }


def build_report(root: Path = ROOT) -> dict[str, Any]:
    """Return read-only integrity findings for repository or fixture root."""
    root = Path(root)
    manifest = _read_json(root / MANIFEST)
    manifest_rows = (
        manifest.get("artifact_sha256") if isinstance(manifest, dict) else None
    )
    manifest_rows = manifest_rows if isinstance(manifest_rows, dict) else {}

    artifact_rows = []
    identities: dict[str, dict[str, Any]] = {}
    manifest_paths: set[str] = set()
    for relative_path, declared in sorted(manifest_rows.items()):
        if not isinstance(relative_path, str):
            continue
        manifest_paths.add(relative_path)
        row = _file_state(root, relative_path, declared)
        row["scope"] = (
            "historical_manifest_only"
            if relative_path in HISTORICAL_PATHS
            else "active_snapshot"
        )
        document = _read_json(root / relative_path)
        if document is not None:
            identities[relative_path] = {
                field: document.get(field)
                for field in MANIFEST_IDENTITY_FIELDS
                if field in document
            }
            row["embedded_bindings"] = _embedded_bindings(root, relative_path, document)
        else:
            row["embedded_bindings"] = []
        artifact_rows.append(row)

    for relative_path in sorted(REQUIRED_MANIFEST_PATHS - manifest_paths):
        path = root / relative_path
        artifact_rows.append(
            {
                "path": relative_path,
                "declared_sha256": None,
                "current_sha256": _sha256(path) if path.is_file() else None,
                "status": "missing",
                "scope": "historical_manifest_only"
                if relative_path in HISTORICAL_PATHS
                else "active_snapshot",
                "manifest_entry_missing": True,
                "embedded_bindings": [],
            }
        )

    supplemental_rows = []
    supplemental_paths = set(WJ04_PATHS.values()) | {ACTIVE_VIEWER_PATH}
    for relative_path in sorted(supplemental_paths - manifest_paths):
        document = _read_json(root / relative_path)
        historical = relative_path in HISTORICAL_PATHS
        status = (
            "missing"
            if document is None
            else ("historical_reference_only" if historical else "consistent")
        )
        bindings = []
        if document is not None:
            identities[relative_path] = {
                field: document.get(field)
                for field in MANIFEST_IDENTITY_FIELDS
                if field in document
            }
            if not historical:
                bindings = _embedded_bindings(root, relative_path, document)
                status = _state(bindings)
        supplemental_rows.append(
            {
                "path": relative_path,
                "scope": "historical_reference_only"
                if historical
                else "active_snapshot",
                "status": status,
                "embedded_bindings": bindings,
            }
        )

    embedded = [
        binding
        for artifact in artifact_rows
        for binding in artifact["embedded_bindings"]
    ]
    embedded.extend(
        binding
        for snapshot in supplemental_rows
        for binding in snapshot["embedded_bindings"]
    )
    embedded_state = _state(embedded)
    artifact_state = "missing" if manifest is None else _state(artifact_rows)

    manifest_identity = {
        field: manifest.get(field)
        for field in MANIFEST_IDENTITY_FIELDS
        if isinstance(manifest, dict) and field in manifest
    }
    active_identity = _active_configuration_identity(root, manifest)
    identity_conflicts = []
    for field in MANIFEST_IDENTITY_FIELDS:
        known = {
            row[field]
            for path, row in identities.items()
            if path not in HISTORICAL_PATHS and path not in HISTORICAL_ARTIFACTS
            if row.get(field) is not None
        }
        if manifest_identity.get(field) is not None:
            known.add(manifest_identity[field])
        if len(known) > 1:
            identity_conflicts.append({"field": field, "values": sorted(known)})
    identity_conflicts.extend(active_identity["candidate_or_commit_conflicts"])
    contract = active_identity["contract"]
    if contract["present"]:
        identities[CONTRACT_PATH] = {
            "candidate": contract["candidate"],
            "source_commit": contract["source_commit"],
        }

    wj04 = _wj04_dimensions(root)
    if manifest is None:
        snapshot_state = "missing"
    else:
        snapshot_state = _state(
            [
                {"status": artifact_state},
                {"status": embedded_state},
                {"status": "stale" if identity_conflicts else "consistent"},
                {"status": active_identity["status"]},
                {"status": wj04["status"]},
            ]
        )

    changed: dict[str, dict[str, Any]] = {}
    missing: set[str] = set()
    for row in embedded:
        if row["status"] == "stale":
            path = row["path"]
            item = changed.setdefault(
                path,
                {
                    "path": path,
                    "current_sha256": row["current_sha256"],
                    "declared_sha256": [],
                    "referenced_by": [],
                },
            )
            item["declared_sha256"].append(row["declared_sha256"])
            item["referenced_by"].append(
                {"artifact": row["recorded_in"], "field": row["field"]}
            )
        elif row["status"] == "missing":
            missing.add(row["path"])

    return {
        "schema": "wood_joint_snapshot_integrity/v1",
        "candidate": active_identity["contract"]["candidate"]
        or manifest_identity.get("candidate"),
        "source_commit": active_identity["contract"]["source_commit"]
        or manifest_identity.get("source_commit"),
        "snapshot_state": snapshot_state,
        "artifact_manifest": {
            "path": MANIFEST,
            "present": manifest is not None,
            "candidate": manifest_identity.get("candidate"),
            "source_commit": manifest_identity.get("source_commit"),
            "artifact_state": artifact_state,
            "artifacts": artifact_rows,
        },
        "supplemental_diagnostic_snapshots": supplemental_rows,
        "candidate_identities_by_artifact": identities,
        "candidate_identity_conflicts": identity_conflicts,
        "active_configuration_and_hardware_identity": active_identity,
        "active_combined_viewer": active_identity["active_combined_viewer"],
        "active_tool_access_report": active_identity["active_tool_access_report"],
        "producer_and_input_hashes": {
            "status": embedded_state,
            "bindings": embedded,
            "changed_dependencies": [changed[path] for path in sorted(changed)],
            "missing_dependencies": sorted(missing),
        },
        "wj04_dimensional_configuration": wj04,
        "claim_limit": "Coherence audit only. A consistent snapshot authenticates recorded identities and dimensions, not acceptance, capacity, physical inspection, or release.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="repository or fixture root"
    )
    args = parser.parse_args()
    print(json.dumps(build_report(args.root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
