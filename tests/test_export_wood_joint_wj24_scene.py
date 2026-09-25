from __future__ import annotations

import base64
import json
import struct
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from scripts import export_wood_joint_wj24_scene as exporter


class _Vertex:
    def __init__(self, point):
        self.point = point

    def toTuple(self):
        return self.point


class _Bounds:
    xmin = -1.0
    xmax = 1.0
    ymin = -1.0
    ymax = 1.0
    zmin = -1.0
    zmax = 1.0


class _Shape:
    points = ((0, 0, 0), (1, 0, 0), (0, 1, 0))

    def copy(self):
        return self

    def tessellate(self, _tolerance):
        return (
            [_Vertex(point) for point in self.points],
            [(0, 1, 2)],
        )

    def BoundingBox(self):
        return _Bounds()


@dataclass(frozen=True)
class _Geometry:
    layout_id: str
    trial_id: str
    source_inventory_sha256: str
    source_binding: dict
    target_station_ids: tuple[str, ...]
    finished_hosts: dict
    replaced_source_axis_ids: frozenset[str]
    candidate_bores: dict
    finished_candidate_parts: dict
    panel_replacements: dict
    fixed_axes: dict
    frame_bolt_records: tuple[dict, ...]
    frame_bolt_shapes: dict
    candidate_installed_hardware: dict
    counts: dict


def _fixture():
    host_ids = {f"host_{index:02d}" for index in range(16)}
    duty_ids = {f"clip_target_{index:02d}" for index in range(24)}
    old_axes = {f"old_axis_{index:03d}" for index in range(144)}
    axis_ids = {f"candidate_axis_{index:03d}" for index in range(104)}
    candidate_parts = {f"candidate_part_{index:02d}" for index in range(28)}
    panels = {"main_lower_right", "main_upper_right", "kicker_right"}
    fixed_axes = {f"fixed_axis_{index:02d}" for index in range(66)}
    bolt_ids = {f"frame_bolt_{index:02d}" for index in range(12)}
    role_names = ("shaft", "head_washer", "nut_washer", "head", "nut")

    parts = []

    def add(name: str, kind: str) -> None:
        parts.append(
            {
                "name": name,
                "path": f"fixture/{name}.stl",
                "fabrication": {"kind": kind},
            }
        )

    for name in host_ids | duty_ids:
        add(name, "part")
    for name in old_axes | fixed_axes:
        add(f"fastener_{name}", "screw")
    for name in panels | {"main_lower_left", "main_upper_left", "kicker_left"}:
        add(name, "part")
    for name in {f"baseline_part_{index}" for index in range(4)}:
        add(name, "part")
    for axis in bolt_ids:
        for role in ("shaft", "near_washer", "far_washer", "head", "nut"):
            add(f"fastener_{axis}_{role}", "bolt")
    for index in range(142):
        add(f"tnut_{index:03d}", "tnut")
    for index in range(132):
        add(f"light_{index:03d}", "light")
    for index in range(131):
        add(f"wire_{index:03d}", "wire")
    assert len(parts) == 725

    shape = _Shape()
    frame_records = tuple(
        {"axis_id": axis, "installed_component_count": 5} for axis in sorted(bolt_ids)
    )
    candidate_bores = {
        axis: SimpleNamespace(family="test_family", station_id=f"duty_{index:03d}")
        for index, axis in enumerate(sorted(axis_ids))
    }
    hardware = {
        axis: {role: shape for role in role_names} for axis in sorted(axis_ids)
    }
    counts = {
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
    inventory_path = exporter.ROOT / exporter.SOURCE_INVENTORY_PATH
    inventory_sha = exporter._sha256_bytes(inventory_path.read_bytes())
    geometry = _Geometry(
        layout_id=exporter.LAYOUT_ID,
        trial_id=exporter.TRIAL_ID,
        source_inventory_sha256=inventory_sha,
        source_binding={"inventory_sha256": inventory_sha},
        target_station_ids=tuple(sorted(duty_ids)),
        finished_hosts={name: shape for name in sorted(host_ids)},
        replaced_source_axis_ids=frozenset(old_axes),
        candidate_bores=candidate_bores,
        finished_candidate_parts={name: shape for name in sorted(candidate_parts)},
        panel_replacements={name: shape for name in sorted(panels)},
        fixed_axes={name: shape for name in sorted(fixed_axes)},
        frame_bolt_records=frame_records,
        frame_bolt_shapes={f"frame_{index:02d}": shape for index in range(72)},
        candidate_installed_hardware=hardware,
        counts=counts,
    )
    commit = "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
    source = {
        "source_commit": commit,
        "source_inventory_sha256": geometry.source_inventory_sha256,
    }
    composition = {
        "schema": "wood_joint_wj24_compositor/v1",
        "layout_id": exporter.LAYOUT_ID,
        "trial_id": exporter.TRIAL_ID,
        "status": "unaccepted_integrated_hypothesis",
        "source": source,
        "counts": counts,
        "target_duties": [{"station_id": name} for name in sorted(duty_ids)],
        "shared_hosts": dict.fromkeys(sorted(host_ids)),
        "removed_source_axes": [{"axis_id": axis} for axis in sorted(old_axes)],
        "candidate_axes": dict.fromkeys(sorted(axis_ids)),
        "candidate_parts": dict.fromkeys(sorted(candidate_parts)),
        "panel_replacements": dict.fromkeys(sorted(panels)),
        "fixed_panel_axes": sorted(fixed_axes),
        "starting_frame_bolts": list(frame_records),
        "producer_hashes_sha256": {"wj24_compositor": "c" * 64},
        "source_input_hashes_sha256": {
            exporter.SOURCE_INVENTORY_PATH.as_posix(): inventory_sha
        },
        "release": {flag: False for flag in exporter.RELEASE_FLAGS},
    }
    diagnostic = {
        "schema": "wood_joint_wj24_diagnostic/v1",
        "trial_id": exporter.TRIAL_ID,
        "source_binding": {
            "inventory_sha256": geometry.source_inventory_sha256,
            "source_commit": commit,
        },
        "source_provenance": {
            "all_family_producers_bound_and_current": True,
            "family_input_hashes_current": True,
            "family_producer_hashes_current": True,
        },
        "diagnostic_gates": {
            "layout_contract_exact_ids_and_counts_match": True,
            "candidate_body_finished_wood_hits_absent": False,
        },
        "candidate_bodies": {
            "candidate_body_vs_access_envelope_hits_mm3": {
                "right_cleat": {"hold_hole_and_provisional_projection/hold_tnut_main_G1": 745.5},
                "other_cleat": {"hold_hole_and_provisional_projection/hold_tnut_main_G12": 562.7},
            }
        },
        "local_family_diagnostics": {"raw_tool_overlaps_retained": True},
        "release": {flag: False for flag in exporter.RELEASE_FLAGS},
    }
    manifest = {
        "design": {"key": "compact-floor-flush-development"},
        "parts": parts,
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    asset_hashes = {row["path"]: "a" * 64 for row in parts}
    return geometry, composition, diagnostic, manifest, manifest_bytes, asset_hashes


def test_hidden_visual_policy_removes_only_replaced_assets():
    geometry, *_ = _fixture()
    hidden = exporter._expected_hidden_baseline_names(geometry)
    assert len(hidden) == 16 + 24 + 144 + 3
    assert {f"fastener_{axis}" for axis in geometry.fixed_axes} .isdisjoint(hidden)
    assert {f"fastener_{row['axis_id']}_{role}" for row in geometry.frame_bolt_records for role in ("shaft", "near_washer", "far_washer", "head", "nut")} .isdisjoint(hidden)
    assert not any(name.startswith(("tnut_", "light_", "wire_")) for name in hidden)


def test_mesh_encoding_is_compact_little_endian_and_within_named_tolerance():
    shape = _Shape()
    shape.points = ((0.049, 0.051, 0.149), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    mesh = exporter._shape_mesh(shape)
    assert mesh["encoding"] == "base64_typed_arrays_le_v1"
    assert mesh["vertex_component_type"] == "int16"
    assert mesh["triangle_component_type"] == "uint16"
    assert mesh["vertex_quantization_mm"] == 0.1
    assert mesh["vertex_max_euclidean_error_mm"] < 0.5
    coords = struct.unpack("<9h", base64.b64decode(mesh["vertices_base64"]))
    indices = struct.unpack("<3H", base64.b64decode(mesh["triangle_indices_base64"]))
    original = [component for point in shape.points for component in point]
    assert max(
        abs(source - quantized * mesh["vertex_quantization_mm"])
        for source, quantized in zip(original, coords, strict=True)
    ) <= 0.05
    assert indices == (0, 1, 2)
    assert mesh["vertex_count"] == 3 and mesh["triangle_count"] == 1


def test_mesh_encoding_falls_back_to_wide_vertex_and_triangle_indices():
    wide_coordinates = _Shape()
    wide_coordinates.points = ((4000.0, 0, 0), (1, 0, 0), (0, 1, 0))
    wide_vertex_mesh = exporter._shape_mesh(wide_coordinates)
    assert wide_vertex_mesh["vertex_component_type"] == "int32"

    many_vertices = _Shape()
    many_vertices.points = tuple((0, 0, 0) for _ in range(65537))

    def tessellate(_tolerance):
        return (
            [_Vertex(point) for point in many_vertices.points],
            [(0, 1, 65536)],
        )

    many_vertices.tessellate = tessellate
    wide_index_mesh = exporter._shape_mesh(many_vertices)
    assert wide_index_mesh["triangle_component_type"] == "uint32"
    assert struct.unpack(
        "<3I", base64.b64decode(wide_index_mesh["triangle_indices_base64"])
    ) == (0, 1, 65536)


def test_scene_binds_reports_preserves_baseline_hardware_and_shows_open_findings():
    geometry, composition, diagnostic, manifest, raw, assets = _fixture()
    scene = exporter.build_wj24_scene(
        geometry,
        composition,
        diagnostic,
        baseline_manifest=manifest,
        baseline_manifest_bytes=raw,
        baseline_asset_hashes=assets,
        composition_report_sha256="e" * 64,
        diagnostic_report_sha256="f" * 64,
    )

    assert scene["layout_status"] == "REVISE"
    assert scene["integrated_scene_is_accepted"] is False
    assert scene["counts"]["rendered_overlay_solids"] == 567
    assert len(scene["triangle_topologies"]) == 1
    assert scene["display_mesh_encoding"]["triangle_topologies_deduplicated"] is True
    assert scene["baseline_scene_policy"]["preserved_visual_counts"] == {
        "fixed_hillman_axes": 66,
        "frame_bolt_physical_components": 60,
        "tnuts": 142,
        "lights": 132,
        "wires": 131,
        "visible_source_panels": 3,
    }
    assert len(scene["hidden_baseline_visual_names"]) == 187
    assert scene["baseline_scene_policy"]["retained_fixed_axis_visual_names"] == sorted(
        f"fastener_{axis}" for axis in geometry.fixed_axes
    )
    assert scene["baseline_scene_policy"]["retained_frame_bolt_visual_names"] == sorted(
        f"fastener_{row['axis_id']}_{role}"
        for row in geometry.frame_bolt_records
        for role in ("shaft", "near_washer", "far_washer", "head", "nut")
    )
    assert len(scene["baseline_scene_policy"]["retained_fixed_axis_visual_names"]) == 66
    assert len(scene["baseline_scene_policy"]["retained_frame_bolt_visual_names"]) == 60
    assert {row["display_class"] for row in scene["solids"]} == {
        "finished_host",
        "candidate_part",
        "candidate_hardware",
        "panel_replacement",
    }
    assert sum(row["display_class"] == "candidate_hardware" for row in scene["solids"]) == 520
    assert all(
        row["mesh"]["triangle_topology_sha256"] in scene["triangle_topologies"]
        and "triangle_indices_base64" not in row["mesh"]
        for row in scene["solids"]
    )
    assert {row["title"] for row in scene["findings"]} >= {
        "hold_hole_and_provisional_projection/hold_tnut_main_G1 intersects right_cleat",
        "hold_hole_and_provisional_projection/hold_tnut_main_G12 intersects other_cleat",
    }
    assert scene["source_binding"]["composition_report_sha256"] == "e" * 64
    assert scene["source_binding"]["diagnostic_report_sha256"] == "f" * 64
    assert scene["source_binding"]["composition_report_canonical_content_sha256"] == exporter._canonical_sha256(composition)
    assert scene["source_binding"]["diagnostic_report_canonical_content_sha256"] == exporter._canonical_sha256(diagnostic)
    assert scene["bounded_led_extraction_summary"] == {
        "lights_checked": 132,
        "stationary_shapes_checked": 842,
        "individual_sweeps_with_positive_volume_hits": 1,
        "individual_sweeps_without_positive_volume_hits": 131,
        "whole_harness_transport_proven": False,
    }
    assert any("light_G7 axial extraction" in row["title"] for row in scene["findings"])


def test_composition_id_mismatch_rejected_even_when_counts_match():
    geometry, composition, diagnostic, *_ = _fixture()
    composition["target_duties"].pop()
    with pytest.raises(ValueError, match="IDs do not match"):
        exporter._validate_composition_identity(geometry, composition, diagnostic)


def test_release_promotion_rejected():
    geometry, composition, diagnostic, *_ = _fixture()
    diagnostic["release"]["fabrication_released"] = True
    with pytest.raises(ValueError, match="release flag"):
        exporter._validate_composition_identity(geometry, composition, diagnostic)


def test_report_count_drift_rejected():
    geometry, composition, diagnostic, *_ = _fixture()
    composition["counts"] = dict(composition["counts"])
    composition["counts"]["candidate_installed_hardware_components"] = 519
    with pytest.raises(ValueError, match="count map"):
        exporter._validate_composition_identity(geometry, composition, diagnostic)


def test_changed_source_input_is_rejected_before_export():
    geometry, composition, diagnostic, *_ = _fixture()
    composition["source_input_hashes_sha256"] = dict(
        composition["source_input_hashes_sha256"]
    )
    composition["source_input_hashes_sha256"][
        exporter.SOURCE_INVENTORY_PATH.as_posix()
    ] = "0" * 64
    with pytest.raises(ValueError, match="source inputs changed"):
        exporter._validate_composition_identity(geometry, composition, diagnostic)


def test_scene_writer_is_confined_to_new_diagnostic_path(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "ROOT", tmp_path)
    scene = {
        "schema": exporter.SCHEMA,
        "layout_status": "REVISE",
        "integrated_scene_is_accepted": False,
        "complete_joint_acceptance": False,
        "capacity_established": False,
        "installation_proven": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
    }
    with pytest.raises(ValueError, match="writes only"):
        exporter.write_wj24_scene(scene, tmp_path / "current-candidate.json")
    path = exporter.write_wj24_scene(scene, tmp_path / exporter.OUTPUT_PATH)
    assert path == tmp_path / exporter.OUTPUT_PATH
    payload = path.read_text()
    assert payload.count("\n") == 1
    assert json.loads(payload)["layout_status"] == "REVISE"
