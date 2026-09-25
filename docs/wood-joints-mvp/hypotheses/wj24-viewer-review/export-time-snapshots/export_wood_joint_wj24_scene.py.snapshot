"""Export the provisional WJ24 composition for a separate diagnostic viewer.

The exporter consumes already composed geometry and its source-bound reports.
It does not build family geometry, run a solver, or change the public candidate
authority. Candidate hardware shapes are CAD occupancy envelopes, not a vendor
selection or a statement about delivered hardware.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from array import array
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "owner_wood_joints_wj24_diagnostic_scene/v1"
LAYOUT_ID = "wj24-twenty-four-duty-integrated-static-v1"
TRIAL_ID = "wj24-wj18-plus-top-center-bottom-pairs-v1"
BASELINE_ID = "compact-floor-flush-kerf-right"
CANDIDATE_ID = "compact-floor-flush-wood-joints-development"
BASELINE_MANIFEST_PATH = Path("site/hybrid/compact-floor-flush-kerf-right/parts.json")
CONTACT_SUPPLEMENT_DIR = Path(
    "docs/wood-joints-mvp/hypotheses/bottom-center-contact-and-hold"
)
CONTACT_SUPPLEMENT_PATH = CONTACT_SUPPLEMENT_DIR / "geometry.json"
CONTACT_SUPPLEMENT_MANIFEST_PATH = CONTACT_SUPPLEMENT_DIR / "manifest.json"
SOURCE_INVENTORY_PATH = Path("docs/wood-joints-mvp/source-inventory.json")
LED_EXTRACTION_DIR = Path("docs/wood-joints-mvp/hypotheses/wj24-led-extraction")
LED_EXTRACTION_PATH = LED_EXTRACTION_DIR / "geometry.json"
LED_EXTRACTION_MANIFEST_PATH = LED_EXTRACTION_DIR / "sha256.json"
WJ24_ARCHIVE_COMPOSITION_PATH = Path(
    "docs/wood-joints-mvp/hypotheses/wj24-integrated-static/composition.json"
)
OUTPUT_PATH = Path("site/owner-wood-joints-wj24-scene.json")

EXPECTED_COUNTS = {
    "target_duties": 24,
    "source_hosts": 16,
    "replaced_source_sds_axes": 144,
    "candidate_bores": 104,
    "candidate_installed_hardware_axes": 104,
    "candidate_installed_hardware_components": 520,
    "candidate_parts": 28,
    "panel_replacements": 3,
    "fixed_panel_axes": 66,
    "retained_frame_bolts": 12,
    "retained_frame_bolt_installed_components": 60,
    "retained_frame_bolt_source_occupied_axes": 12,
    "retained_frame_bolt_shapes": 72,
    "retained_legacy_clips": 0,
    "retained_legacy_sds_axes": 0,
    "additional_finished_source_parts": 0,
    "additional_purchased_panel_receiver_axes": 0,
}
DISPLAY_MESH_TESSELLATION_TOLERANCE_MM = 0.5
DISPLAY_VERTEX_QUANTIZATION_MM = 0.1
DISPLAY_VERTEX_MAX_EUCLIDEAN_ERROR_MM = (3**0.5) * DISPLAY_VERTEX_QUANTIZATION_MM / 2

RELEASE_FLAGS = (
    "candidate_accepted",
    "source_cutting_released",
    "drilling_released",
    "fabrication_released",
    "structural_accepted",
    "assembly_proven",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _plain(value: Any) -> Any:
    """Convert immutable report/dataclass containers to JSON-safe values."""
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_plain(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported JSON evidence value: {type(value).__name__}")


def _require_false_release_flags(report: Mapping[str, Any], label: str) -> dict[str, bool]:
    flags = report.get("release")
    if not isinstance(flags, Mapping):
        raise TypeError(f"{label} must contain a release object")
    if any(flags.get(flag) is not False for flag in RELEASE_FLAGS):
        raise ValueError(f"{label} must retain every WJ24 release flag as false")
    return {flag: False for flag in RELEASE_FLAGS}


def _shape_mesh(shape: Any) -> dict[str, Any]:
    # Tessellate a copy because OCCT may cache/normalize bounds during meshing.
    vertices, triangles = shape.copy().tessellate(
        DISPLAY_MESH_TESSELLATION_TOLERANCE_MM
    )
    bounds = shape.BoundingBox()
    coordinates = [
        round(float(component) / DISPLAY_VERTEX_QUANTIZATION_MM)
        for vertex in vertices
        for component in vertex.toTuple()
    ]
    vertex_component_type = (
        "int16"
        if all(-32768 <= value <= 32767 for value in coordinates)
        else "int32"
    )
    vertex_array = array("h" if vertex_component_type == "int16" else "i", coordinates)
    triangle_indices = [int(index) for triangle in triangles for index in triangle]
    if len(triangle_indices) != 3 * len(triangles) or any(
        index < 0 or index >= len(vertices) for index in triangle_indices
    ):
        raise ValueError("tessellated mesh contains invalid triangle vertex indices")
    triangle_component_type = (
        "uint16"
        if len(vertices) <= 65536 and max(triangle_indices, default=0) <= 65535
        else "uint32"
    )
    triangle_array = array(
        "H" if triangle_component_type == "uint16" else "I", triangle_indices
    )
    if vertex_array.itemsize != (2 if vertex_component_type == "int16" else 4):
        raise RuntimeError("platform array width does not match display vertex encoding")
    if triangle_array.itemsize != (2 if triangle_component_type == "uint16" else 4):
        raise RuntimeError("platform array width does not match display triangle encoding")
    if sys.byteorder != "little":
        vertex_array.byteswap()
        triangle_array.byteswap()
    triangle_bytes = triangle_array.tobytes()
    return {
        "encoding": "base64_typed_arrays_le_v1",
        "vertex_component_type": vertex_component_type,
        "vertex_quantization_mm": DISPLAY_VERTEX_QUANTIZATION_MM,
        "vertex_max_euclidean_error_mm": DISPLAY_VERTEX_MAX_EUCLIDEAN_ERROR_MM,
        "triangle_component_type": triangle_component_type,
        "vertex_count": len(vertices),
        "triangle_count": len(triangles),
        "triangle_topology_sha256": _sha256_bytes(triangle_bytes),
        "bounds_xyz_mm": [
            float(bounds.xmin),
            float(bounds.xmax),
            float(bounds.ymin),
            float(bounds.ymax),
            float(bounds.zmin),
            float(bounds.zmax),
        ],
        "vertices_base64": base64.b64encode(vertex_array.tobytes()).decode("ascii"),
        "triangle_indices_base64": base64.b64encode(triangle_bytes).decode("ascii"),
    }


def _deduplicate_triangle_topologies(
    solids: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Store each exact index topology once; all vertex coordinates stay per solid."""
    topologies: dict[str, dict[str, Any]] = {}
    for solid in solids:
        mesh = solid["mesh"]
        encoded = mesh.pop("triangle_indices_base64")
        binary = base64.b64decode(encoded, validate=True)
        topology_id = _sha256_bytes(binary)
        if topology_id != mesh["triangle_topology_sha256"]:
            raise ValueError("triangle topology digest does not match its binary indices")
        row = {
            "triangle_component_type": mesh["triangle_component_type"],
            "triangle_count": mesh["triangle_count"],
            "index_count": mesh["triangle_count"] * 3,
            "triangle_indices_base64": encoded,
        }
        prior = topologies.setdefault(topology_id, row)
        if prior != row:
            raise ValueError("same triangle topology digest has conflicting encoding metadata")
    return dict(sorted(topologies.items()))


def _load_baseline(
    baseline_manifest: Mapping[str, Any] | None,
    baseline_manifest_bytes: bytes | None,
) -> tuple[dict[str, Any], bytes]:
    if baseline_manifest is None:
        raw = (ROOT / BASELINE_MANIFEST_PATH).read_bytes()
        parsed = json.loads(raw)
    else:
        parsed = _plain(baseline_manifest)
        raw = (
            baseline_manifest_bytes
            if baseline_manifest_bytes is not None
            else json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()
        )
    if baseline_manifest_bytes is not None:
        raw = baseline_manifest_bytes
        try:
            parsed_from_bytes = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError("baseline manifest bytes are not valid JSON") from error
        if parsed_from_bytes != parsed:
            raise ValueError("baseline manifest object and bytes differ")
    design = parsed.get("design", {})
    design_identity = (
        design.get("candidate", design.get("key"))
        if isinstance(design, Mapping)
        else design
    )
    if design_identity not in (None, BASELINE_ID, "compact-floor-flush-development"):
        raise ValueError("baseline manifest is not the pinned kerf-right variant")
    if not isinstance(parsed.get("parts"), list):
        raise TypeError("baseline manifest must contain a parts list")
    return parsed, raw


def _baseline_asset_hashes(
    parts: list[Mapping[str, Any]],
    supplied: Mapping[str, str] | None,
) -> dict[str, str]:
    paths = {str(row["path"]) for row in parts}
    if supplied is None:
        result = {
            path: _sha256_bytes((ROOT / "site" / path).read_bytes())
            for path in sorted(paths)
        }
    else:
        result = {str(path): str(value) for path, value in supplied.items()}
        if set(result) != paths:
            raise ValueError("baseline STL hash map must cover the exact manifest paths")
    if set(result) != paths or any(
        len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower())
        for value in result.values()
    ):
        raise ValueError("baseline asset hashes must be complete SHA-256 values")
    return result


def _expected_hidden_baseline_names(geometry: Any) -> set[str]:
    replaced_axes = set(geometry.replaced_source_axis_ids)
    target_duties = set(geometry.target_station_ids)
    replaced_hosts = set(geometry.finished_hosts)
    replaced_panels = set(geometry.panel_replacements)
    return (
        replaced_hosts
        | target_duties
        | {f"fastener_{axis}" for axis in replaced_axes}
        | replaced_panels
    )


def _validate_composition_identity(
    geometry: Any,
    composition: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
) -> dict[str, set[str]]:
    if geometry.layout_id != LAYOUT_ID or geometry.trial_id != TRIAL_ID:
        raise ValueError("scene export requires the fixed WJ24 composition")
    if composition.get("schema") != "wood_joint_wj24_compositor/v1":
        raise ValueError("composition report schema is not WJ24")
    if composition.get("layout_id") != LAYOUT_ID or composition.get("trial_id") != TRIAL_ID:
        raise ValueError("composition report identity differs from WJ24")
    if diagnostic.get("schema") != "wood_joint_wj24_diagnostic/v1":
        raise ValueError("diagnostic report schema is not WJ24")
    if diagnostic.get("trial_id") != TRIAL_ID:
        raise ValueError("diagnostic report trial differs from WJ24")

    ids = {
        "duties": set(geometry.target_station_ids),
        "hosts": set(geometry.finished_hosts),
        "source_axes": set(geometry.replaced_source_axis_ids),
        "candidate_axes": set(geometry.candidate_bores),
        "candidate_parts": set(geometry.finished_candidate_parts),
        "panels": set(geometry.panel_replacements),
        "fixed_axes": set(geometry.fixed_axes),
        "frame_bolts": {str(row["axis_id"]) for row in geometry.frame_bolt_records},
    }
    expected_report_ids = {
        "duties": {row["station_id"] for row in composition.get("target_duties", ())},
        "hosts": set(composition.get("shared_hosts", {})),
        "source_axes": {row["axis_id"] for row in composition.get("removed_source_axes", ())},
        "candidate_axes": set(composition.get("candidate_axes", {})),
        "candidate_parts": set(composition.get("candidate_parts", {})),
        "panels": set(composition.get("panel_replacements", {})),
        "fixed_axes": set(composition.get("fixed_panel_axes", ())),
        "frame_bolts": {str(row["axis_id"]) for row in composition.get("starting_frame_bolts", ())},
    }
    if ids != expected_report_ids:
        differing = {
            key: {
                "geometry_only": sorted(ids[key] - expected_report_ids[key]),
                "report_only": sorted(expected_report_ids[key] - ids[key]),
            }
            for key in ids
            if ids[key] != expected_report_ids[key]
        }
        raise ValueError(f"composition report IDs do not match geometry: {differing}")

    counts = geometry.counts
    for key, expected in EXPECTED_COUNTS.items():
        if counts.get(key) != expected:
            raise ValueError(f"WJ24 {key} count must be {expected}, got {counts.get(key)}")
    report_counts = composition.get("counts", {})
    if any(report_counts.get(key) != value for key, value in counts.items()):
        raise ValueError("composition report count map differs from composed geometry")
    if len(geometry.frame_bolt_records) != 12 or len(geometry.frame_bolt_shapes) != 72:
        raise ValueError("WJ24 frame-bolt contract must retain 12 bolts and 72 source shapes")
    if len(geometry.candidate_installed_hardware) != 104 or sum(
        len(roles) for roles in geometry.candidate_installed_hardware.values()
    ) != 520:
        raise ValueError("WJ24 candidate hardware must contain 520 modeled role envelopes")

    binding = composition.get("source", {})
    diagnostic_binding = diagnostic.get("source_binding", {})
    inventory_hash = str(geometry.source_inventory_sha256)
    if binding.get("source_inventory_sha256") != inventory_hash:
        raise ValueError("composition report source inventory hash differs from geometry")
    if diagnostic_binding.get("inventory_sha256") != inventory_hash:
        raise ValueError("diagnostic report source inventory hash differs from geometry")
    if diagnostic_binding.get("source_commit") != binding.get("source_commit"):
        raise ValueError("diagnostic and composition source commits differ")
    current_inventory_hash = _sha256_bytes((ROOT / SOURCE_INVENTORY_PATH).read_bytes())
    if current_inventory_hash != inventory_hash:
        raise ValueError("canonical source inventory changed since geometry materialization")
    source_inputs = composition.get("source_input_hashes_sha256", {})
    if not isinstance(source_inputs, Mapping) or not source_inputs:
        raise ValueError("composition report must include its source input hash closure")
    stale_inputs = []
    for relative_path, expected_hash in source_inputs.items():
        path = ROOT / relative_path
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != expected_hash:
            stale_inputs.append(relative_path)
    if stale_inputs:
        raise ValueError(f"composition source inputs changed after materialization: {sorted(stale_inputs)}")
    provenance = diagnostic.get("source_provenance", {})
    for flag in (
        "all_family_producers_bound_and_current",
        "family_input_hashes_current",
        "family_producer_hashes_current",
    ):
        if provenance.get(flag) is False:
            raise ValueError(f"diagnostic source provenance is stale: {flag}")
    _require_false_release_flags(composition, "composition report")
    _require_false_release_flags(diagnostic, "diagnostic report")
    return ids


def _source_bound_supplement(
    contact_supplement: Mapping[str, Any] | None,
    contact_supplement_manifest: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str, str]:
    if contact_supplement is None:
        supplement_bytes = (ROOT / CONTACT_SUPPLEMENT_PATH).read_bytes()
        supplement = json.loads(supplement_bytes)
    else:
        supplement = _plain(contact_supplement)
        supplement_bytes = json.dumps(
            supplement, sort_keys=True, separators=(",", ":")
        ).encode()
    if contact_supplement_manifest is None:
        manifest_bytes = (ROOT / CONTACT_SUPPLEMENT_MANIFEST_PATH).read_bytes()
        manifest = json.loads(manifest_bytes)
    else:
        manifest = _plain(contact_supplement_manifest)
        manifest_bytes = json.dumps(
            manifest, sort_keys=True, separators=(",", ":")
        ).encode()
    expected = manifest.get("files", {}).get("geometry.json")
    actual = _sha256_bytes(supplement_bytes)
    if expected != actual:
        raise ValueError("finite-contact supplement hash differs from its manifest")
    if supplement.get("release") is not False or supplement.get("native_solve_run") is not False:
        raise ValueError("finite-contact supplement must remain diagnostic-only")
    source_paths = supplement.get("source_sha256", {})
    stale = []
    for recorded_path, expected_hash in source_paths.items():
        path = Path(recorded_path)
        if path.is_absolute():
            try:
                relative = path.resolve().relative_to(ROOT.resolve())
            except ValueError:
                stale.append(recorded_path)
                continue
        else:
            relative = path
        if not (ROOT / relative).is_file() or _sha256_bytes((ROOT / relative).read_bytes()) != expected_hash:
            stale.append(recorded_path)
    producer_hash = supplement.get("producer_sha256")
    producer_path = CONTACT_SUPPLEMENT_DIR / "parent_probe.py.snapshot"
    producer_current = producer_path.is_file() and _sha256_bytes(producer_path.read_bytes()) == producer_hash
    if stale or not producer_current:
        raise ValueError(
            "finite-contact supplement source binding is stale: "
            f"paths={sorted(stale)}, producer_current={producer_current}"
        )
    return supplement, actual, _sha256_bytes(manifest_bytes)


def _source_bound_led_extraction(
    led_extraction_report: Mapping[str, Any] | None,
    led_extraction_manifest: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str, str]:
    if led_extraction_report is None:
        report_bytes = (ROOT / LED_EXTRACTION_PATH).read_bytes()
        report = json.loads(report_bytes)
    else:
        report = _plain(led_extraction_report)
        report_bytes = json.dumps(
            report, sort_keys=True, separators=(",", ":")
        ).encode()
    if led_extraction_manifest is None:
        manifest_bytes = (ROOT / LED_EXTRACTION_MANIFEST_PATH).read_bytes()
        manifest = json.loads(manifest_bytes)
    else:
        manifest = _plain(led_extraction_manifest)
        manifest_bytes = json.dumps(
            manifest, sort_keys=True, separators=(",", ":")
        ).encode()
    if manifest.get("geometry.json") != _sha256_bytes(report_bytes):
        raise ValueError("LED extraction report hash differs from its archive manifest")
    if (
        report.get("layout_id") != LAYOUT_ID
        or report.get("status") != "bounded_individual_led_axial_extraction_diagnostic"
        or report.get("release") is not False
        or report.get("native_solve_run") is not False
        or report.get("assembly_proven") is not False
        or report.get("transport_proven") is not False
        or report.get("light_count") != 132
        or report.get("stationary_shape_count") != 842
    ):
        raise ValueError("LED extraction report identity or no-acceptance boundary is invalid")
    input_stale = []
    for relative, expected in report.get("source_input_sha256", {}).items():
        path = ROOT / relative
        if not path.is_file() or _sha256_bytes(path.read_bytes()) != expected:
            input_stale.append(relative)
    source_stale = []
    archive_composition_hash = _sha256_bytes(
        (ROOT / WJ24_ARCHIVE_COMPOSITION_PATH).read_bytes()
    )
    archived_producer_hash = manifest.get("producer.py.snapshot")
    for recorded, expected in report.get("source_sha256", {}).items():
        path = Path(recorded)
        if recorded.endswith("/composition.json"):
            actual = archive_composition_hash
        elif recorded.endswith("/wj24-led-extraction-probe.py"):
            actual = archived_producer_hash
        elif path.is_absolute() and path.exists():
            actual = _sha256_bytes(path.read_bytes())
        elif not path.is_absolute() and (ROOT / path).is_file():
            actual = _sha256_bytes((ROOT / path).read_bytes())
        else:
            actual = None
        if actual != expected:
            source_stale.append(recorded)
    if input_stale or source_stale:
        raise ValueError(
            "LED extraction report source binding is stale: "
            f"inputs={sorted(input_stale)}, sources={sorted(source_stale)}"
        )
    if len(report.get("rows", ())) != 132:
        raise ValueError("LED extraction report must list all 132 individual light axes")
    return report, _sha256_bytes(report_bytes), _sha256_bytes(manifest_bytes)


def _finding_summary(
    diagnostic: Mapping[str, Any],
    supplement: Mapping[str, Any],
    led_extraction: Mapping[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    gates = diagnostic.get("diagnostic_gates", {})
    failed = sorted(key for key, value in gates.items() if value is False)
    if failed:
        findings.append(
            {
                "severity": "open_gate",
                "title": "Full-scene diagnostic has unresolved gates",
                "detail": failed,
            }
        )
    body_hits = (
        diagnostic.get("candidate_bodies", {}).get("candidate_body_vs_access_envelope_hits_mm3", {})
    )
    for body, hits in sorted(body_hits.items()):
        for envelope, overlap in sorted(hits.items()):
            findings.append(
                {
                    "severity": "collision_envelope_overlap",
                    "title": f"{envelope} intersects {body}",
                    "detail": {"overlap_mm3": overlap, "envelope_kind": "provisional access/hold proxy"},
                }
            )
    for item in supplement.get("interfaces", ()):
        nominal = item.get("cleat_planar_area_mm2")
        finite = item.get("finite_common_area_mm2")
        if isinstance(nominal, (int, float)) and isinstance(finite, (int, float)) and finite < nominal - 1e-6:
            findings.append(
                {
                    "severity": "finite_contact_shortfall",
                    "title": f"{item.get('duty_id')} / {item.get('host_id')} finite face",
                    "detail": {
                        "nominal_cleat_face_area_mm2": nominal,
                        "finite_common_area_mm2": finite,
                        "shortfall_mm2": nominal - finite,
                    },
                }
            )
    hold = supplement.get("G1_provisional_hold_projection", {})
    if hold:
        findings.append(
            {
                "severity": "provisional_hold_proxy_overlap",
                "title": "G1 provisional hold projection intersects candidate wood",
                "detail": {
                    "overlap_mm3": hold.get("overlap_volume_mm3"),
                    "diameter_mm": hold.get("proxy_diameter_mm"),
                    "length_mm": hold.get("proxy_length_mm"),
                    "stations_from_panel_rear_mm": hold.get("overlap_stations_from_panel_rear_mm"),
                    "selected_or_approved_hold_bolt": False,
                },
            }
        )
    for row in led_extraction.get("rows", ()):
        for obstacle, overlap in sorted(row.get("positive_volume_hits_mm3", {}).items()):
            findings.append(
                {
                    "severity": "bounded_led_extraction_overlap",
                    "title": f"{row['light_id']} axial extraction intersects {obstacle}",
                    "detail": {
                        "overlap_mm3": overlap,
                        "stroke_mm": row.get("stroke_mm"),
                        "scenario_front_clearance_mm": row.get(
                            "front_end_final_panel_rear_clearance_mm"
                        ),
                        "transport_or_assembly_proven": False,
                    },
                }
            )
    return findings


def build_wj24_scene(
    geometry: Any,
    composition_report: Mapping[str, Any],
    diagnostic_report: Mapping[str, Any],
    *,
    baseline_manifest: Mapping[str, Any] | None = None,
    baseline_manifest_bytes: bytes | None = None,
    baseline_asset_hashes: Mapping[str, str] | None = None,
    contact_supplement: Mapping[str, Any] | None = None,
    contact_supplement_manifest: Mapping[str, Any] | None = None,
    led_extraction_report: Mapping[str, Any] | None = None,
    led_extraction_manifest: Mapping[str, Any] | None = None,
    composition_report_sha256: str | None = None,
    diagnostic_report_sha256: str | None = None,
) -> dict[str, Any]:
    """Build a source-bound, non-authoritative scene from retained WJ24 objects."""
    composition = _plain(composition_report)
    diagnostic = _plain(diagnostic_report)
    ids = _validate_composition_identity(geometry, composition, diagnostic)
    baseline, manifest_bytes = _load_baseline(baseline_manifest, baseline_manifest_bytes)
    parts = baseline["parts"]
    manifest_names = {str(row.get("name")) for row in parts}
    if len(manifest_names) != len(parts):
        raise ValueError("baseline manifest visual names must be unique")
    hidden = _expected_hidden_baseline_names(geometry)
    missing = hidden - manifest_names
    if missing:
        raise ValueError(f"expected replaced baseline visuals are missing: {sorted(missing)}")

    fixed_axis_assets = {f"fastener_{axis}" for axis in ids["fixed_axes"]}
    frame_component_assets = {
        f"fastener_{record['axis_id']}_{role}"
        for record in geometry.frame_bolt_records
        for role in ("shaft", "near_washer", "far_washer", "head", "nut")
    }
    if not fixed_axis_assets <= manifest_names or not frame_component_assets <= manifest_names:
        raise ValueError("pinned baseline lacks fixed Hillman or frame-bolt visuals")
    if hidden & (fixed_axis_assets | frame_component_assets):
        raise ValueError("replacement visual policy would hide retained baseline hardware")
    for name in ("main_lower_left", "main_upper_left", "kicker_left"):
        if name not in manifest_names or name in hidden:
            raise ValueError(f"canonical panel {name} must remain visible")

    kinds = {
        str(row["name"]): row.get("fabrication", {}).get("kind")
        for row in parts
    }
    preserved_baseline_counts = {
        "fixed_hillman_axes": len(fixed_axis_assets),
        "frame_bolt_physical_components": len(frame_component_assets),
        "tnuts": sum(kinds.get(row["name"]) == "tnut" for row in parts if row["name"] not in hidden),
        "lights": sum(kinds.get(row["name"]) == "light" for row in parts if row["name"] not in hidden),
        "wires": sum(kinds.get(row["name"]) == "wire" for row in parts if row["name"] not in hidden),
        "visible_source_panels": sum(
            kinds.get(row["name"]) == "part" and row["name"] in {
                "main_lower_left", "main_upper_left", "kicker_left",
                "main_lower_right", "main_upper_right", "kicker_right",
            }
            for row in parts if row["name"] not in hidden
        ),
    }
    if preserved_baseline_counts != {
        "fixed_hillman_axes": 66,
        "frame_bolt_physical_components": 60,
        "tnuts": 142,
        "lights": 132,
        "wires": 131,
        "visible_source_panels": 3,
    }:
        raise ValueError(f"baseline retained-scene inventory differs: {preserved_baseline_counts}")

    asset_hashes = _baseline_asset_hashes(parts, baseline_asset_hashes)
    supplement, supplement_sha, supplement_manifest_sha = _source_bound_supplement(
        contact_supplement, contact_supplement_manifest
    )
    led_extraction, led_sha, led_manifest_sha = _source_bound_led_extraction(
        led_extraction_report, led_extraction_manifest
    )

    solids: list[dict[str, Any]] = []

    def add_solid(name: str, role: str, shape: Any, display_class: str, *, collision_envelope: bool = False) -> None:
        solids.append(
            {
                "id": name,
                "name": name,
                "role": role,
                "display_class": display_class,
                "collision_envelope": collision_envelope,
                "visual_status": (
                    "CAD occupied hardware envelope; not a selected or delivered component"
                    if collision_envelope
                    else "candidate solid geometry; nominal diagnostic only"
                ),
                "mesh": _shape_mesh(shape),
            }
        )

    for name, shape in sorted(geometry.finished_hosts.items()):
        add_solid(name, "finished_shared_host", shape, "finished_host")
    for name, shape in sorted(geometry.finished_candidate_parts.items()):
        add_solid(name, "finished_candidate_part", shape, "candidate_part")
    for name, shape in sorted(geometry.panel_replacements.items()):
        add_solid(name, "candidate_panel_replacement", shape, "panel_replacement")
    for axis, roles in sorted(geometry.candidate_installed_hardware.items()):
        bore = geometry.candidate_bores[axis]
        family = str(getattr(bore, "family", "not_recorded"))
        station_id = getattr(bore, "station_id", None)
        for role, shape in sorted(roles.items()):
            add_solid(
                f"{axis}/{role}",
                f"candidate_hardware_occupancy/{role}",
                shape,
                "candidate_hardware",
                collision_envelope=True,
            )
            solids[-1]["axis_id"] = axis
            solids[-1]["family"] = family
            solids[-1]["station_id"] = station_id

    if len(solids) != 16 + 28 + 3 + 520:
        raise ValueError(f"renderable WJ24 overlay solid count differs: {len(solids)}")
    if len({row["id"] for row in solids}) != len(solids):
        raise ValueError("renderable WJ24 overlay IDs must be unique")
    triangle_topologies = _deduplicate_triangle_topologies(solids)

    composition_sha = _canonical_sha256(composition)
    diagnostic_sha = _canonical_sha256(diagnostic)
    for label, supplied in (
        ("composition", composition_report_sha256),
        ("diagnostic", diagnostic_report_sha256),
    ):
        if supplied is not None and (
            len(supplied) != 64
            or any(character not in "0123456789abcdef" for character in supplied.lower())
        ):
            raise ValueError(f"{label} artifact hash must be a SHA-256 digest")
    composition_artifact_sha = composition_report_sha256 or composition_sha
    diagnostic_artifact_sha = diagnostic_report_sha256 or diagnostic_sha
    manifest_sha = _sha256_bytes(manifest_bytes)
    source_commit = composition["source"].get("source_commit")
    if not isinstance(source_commit, str) or len(source_commit) != 40:
        raise ValueError("composition report does not include a bound source commit")

    return {
        "schema": SCHEMA,
        "candidate": CANDIDATE_ID,
        "baseline": BASELINE_ID,
        "layout_id": LAYOUT_ID,
        "trial_id": TRIAL_ID,
        "status": "REVISE — provisional integrated geometry study",
        "scope": (
            "Twenty-four-duty source-bound nominal geometry composition and static diagnostics. "
            "This viewer is a review aid, not acceptance or a fabrication release."
        ),
        "layout_status": "REVISE",
        "integrated_scene_is_accepted": False,
        "complete_joint_acceptance": False,
        "capacity_established": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
        "release": _require_false_release_flags(composition, "composition report"),
        "source_binding": {
            "source_commit": source_commit,
            "source_inventory_sha256": geometry.source_inventory_sha256,
            "source_binding": _plain(geometry.source_binding),
            "composition_report_sha256": composition_artifact_sha,
            "diagnostic_report_sha256": diagnostic_artifact_sha,
            "composition_report_canonical_content_sha256": composition_sha,
            "diagnostic_report_canonical_content_sha256": diagnostic_sha,
            "composition_producer_hashes_sha256": composition.get("producer_hashes_sha256", {}),
            "composition_source_input_hashes_sha256": composition.get("source_input_hashes_sha256", {}),
            "diagnostic_provenance": diagnostic.get("source_provenance", {}),
            "baseline_manifest_sha256": manifest_sha,
            "contact_supplement_sha256": supplement_sha,
            "contact_supplement_manifest_sha256": supplement_manifest_sha,
            "led_extraction_report_sha256": led_sha,
            "led_extraction_manifest_sha256": led_manifest_sha,
        },
        "baseline_manifest_path": BASELINE_MANIFEST_PATH.as_posix(),
        "baseline_manifest_sha256": manifest_sha,
        "baseline_asset_sha256": asset_hashes,
        "hidden_baseline_visual_names": sorted(hidden),
        "baseline_scene_policy": {
            "hidden_counts": {
                "rebuilt_shared_hosts": 16,
                "replaced_legacy_clips": 24,
                "replaced_legacy_sds_visuals": 144,
                "replaced_right_panels": 3,
            },
            "preserved_visual_counts": preserved_baseline_counts,
            "retained_fixed_axis_ids": sorted(ids["fixed_axes"]),
            "retained_frame_bolt_ids": sorted(ids["frame_bolts"]),
            "retained_fixed_axis_visual_names": sorted(fixed_axis_assets),
            "retained_frame_bolt_visual_names": sorted(frame_component_assets),
            "retained_frame_bolt_source_occupied_axis_proxy_count": 12,
            "retained_frame_bolt_axis_proxies_rendered": False,
            "fixed_axes_and_starting_frame_bolts_rendered_once_from_pinned_baseline": True,
        },
        "counts": {
            **dict(geometry.counts),
            "rendered_overlay_solids": len(solids),
            "baseline_assets": len(parts),
            "visible_baseline_assets": len(parts) - len(hidden),
        },
        "display_mesh_encoding": {
            "encoding": "base64_typed_arrays_le_v1",
            "triangle_topologies_deduplicated": True,
            "unique_triangle_topology_count": len(triangle_topologies),
            "tessellation_tolerance_mm": DISPLAY_MESH_TESSELLATION_TOLERANCE_MM,
            "vertex_quantization_mm": DISPLAY_VERTEX_QUANTIZATION_MM,
            "maximum_euclidean_vertex_quantization_error_mm": DISPLAY_VERTEX_MAX_EUCLIDEAN_ERROR_MM,
            "cad_geometry_modified": False,
        },
        "solids": solids,
        "triangle_topologies": triangle_topologies,
        "findings": _finding_summary(diagnostic, supplement, led_extraction),
        "finite_contact_supplement": {
            "path": CONTACT_SUPPLEMENT_PATH.as_posix(),
            "manifest_path": CONTACT_SUPPLEMENT_MANIFEST_PATH.as_posix(),
            "sha256": supplement_sha,
            "manifest_sha256": supplement_manifest_sha,
            "report": supplement,
        },
        "led_extraction_diagnostic": {
            "path": LED_EXTRACTION_PATH.as_posix(),
            "manifest_path": LED_EXTRACTION_MANIFEST_PATH.as_posix(),
            "sha256": led_sha,
            "manifest_sha256": led_manifest_sha,
            "report": led_extraction,
        },
        "bounded_led_extraction_summary": {
            "lights_checked": led_extraction["light_count"],
            "stationary_shapes_checked": led_extraction["stationary_shape_count"],
            "individual_sweeps_with_positive_volume_hits": led_extraction[
                "lights_with_positive_volume_hits"
            ],
            "individual_sweeps_without_positive_volume_hits": led_extraction[
                "light_count"
            ]
            - led_extraction["lights_with_positive_volume_hits"],
            "whole_harness_transport_proven": False,
        },
        "composition_report": composition,
        "diagnostic_report": diagnostic,
        "limits": [
            "REVISE only: full-scene static checks include unresolved geometry findings.",
            "G1 and G12 are provisional hold/access proxies, not selected or approved bolt geometry.",
            "Hardware overlays show CAD occupied envelopes; they do not identify delivered hardware.",
            "Baseline Hillman screws, frame bolts, T-nuts, lights, wires, and unchanged panels are shown once from the pinned selected-baseline scene.",
            "Raw tool-envelope overlaps and local family findings remain visible in the diagnostic report; they do not establish an assembly sequence.",
            "No physical inspection, capacity, contact-pressure, movement, installation, fabrication, structural, or climbing acceptance is established.",
        ],
    }


def write_wj24_scene(
    scene: Mapping[str, Any],
    output_path: Path | str = ROOT / OUTPUT_PATH,
) -> Path:
    """Write a deterministic JSON scene without touching authority/history files."""
    if scene.get("schema") != SCHEMA or scene.get("layout_status") != "REVISE":
        raise ValueError("only a WJ24 REVISE diagnostic scene may be exported")
    if any(scene.get(flag) is not False for flag in (
        "integrated_scene_is_accepted",
        "complete_joint_acceptance",
        "capacity_established",
        "installation_proven",
        "fabrication_released",
        "structural_released",
        "climbing_released",
    )):
        raise ValueError("WJ24 scene release and acceptance fields must remain false")
    path = Path(output_path)
    if not path.is_absolute():
        path = ROOT / path
    if path.resolve() != (ROOT / OUTPUT_PATH).resolve():
        raise ValueError("WJ24 exporter writes only its separate diagnostic scene path")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            _plain(scene),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )
    return path
