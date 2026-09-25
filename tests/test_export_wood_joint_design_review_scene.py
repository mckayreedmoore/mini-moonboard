from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import export_wood_joint_design_review_scene as exporter

ROOT = Path(__file__).resolve().parents[1]
BASE_SCENE = ROOT / exporter.BASE_SCENE_PATH


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
        return ([_Vertex(point) for point in self.points], [(0, 1, 2)])

    def BoundingBox(self):
        return _Bounds()


@dataclass(frozen=True)
class _Bore:
    family: str
    station_id: str


def _fixture():
    raw = BASE_SCENE.read_bytes()
    parent = json.loads(raw)
    composition = parent["composition_report"]
    host_id = next(iter(composition["shared_hosts"]))
    part_id = next(iter(composition["candidate_parts"]))
    old_hardware = next(
        row for row in parent["solids"] if row.get("display_class") == "candidate_hardware"
    )
    axis_id = old_hardware["axis_id"]
    role_id = old_hardware["id"].split("/", 1)[1]
    moved_axis = composition["fixed_panel_axes"][-1]
    fixed_axes = composition["fixed_panel_axes"][:-1]
    duty_id = composition["target_duties"][0]["station_id"]
    removed_axis = composition["removed_source_axes"][0]["axis_id"]
    frame = composition["starting_frame_bolts"][0]
    revision_id = "lower-rear-blocks-below-v1"

    inventory = {
        "shared_hosts": {host_id: composition["shared_hosts"][host_id]},
        "candidate_parts": {part_id: composition["candidate_parts"][part_id]},
        "panel_replacements": {"main_lower_left": {}},
        "target_duties": [{"station_id": duty_id}],
        "removed_source_axes": [{"axis_id": removed_axis}],
        "fixed_panel_axes": fixed_axes,
        "moved_panel_axes": [
            {
                "axis_id": moved_axis,
                "visual_name": f"fastener_{moved_axis}",
                "translation_global_xyz_mm": [0.0, 128.557522, 153.208889],
            }
        ],
        "panel_screw_axis_count": 66,
        "starting_frame_bolts": [frame],
        "candidate_axes": {
            axis_id: {
                "family": old_hardware.get("family"),
                "station_id": old_hardware.get("station_id"),
                "installed_role_ids": [role_id],
            }
        },
    }
    geometry = SimpleNamespace(
        layout_id=revision_id,
        trial_id=revision_id,
        source_inventory_sha256=parent["source_binding"]["source_inventory_sha256"],
        target_station_ids=(duty_id,),
        finished_hosts={host_id: _Shape()},
        replaced_source_axis_ids=frozenset({removed_axis}),
        finished_candidate_parts={part_id: _Shape()},
        panel_replacements={"main_lower_left": _Shape()},
        fixed_axes={axis: {} for axis in fixed_axes},
        frame_bolt_records=(frame,),
        candidate_bores={axis_id: _Bore(old_hardware["family"], old_hardware["station_id"])},
        candidate_installed_hardware={axis_id: {role_id: _Shape()}},
    )
    # A revised model carries all retained shapes, even when only a few meshes
    # need regeneration. Absence now denotes an explicitly removed component.
    for row in parent["solids"]:
        name = row["id"]
        if row["display_class"] == "finished_host":
            geometry.finished_hosts.setdefault(name, _Shape())
        elif row["display_class"] == "candidate_part":
            geometry.finished_candidate_parts.setdefault(name, _Shape())
        elif row["display_class"] == "panel_replacement":
            geometry.panel_replacements.setdefault(name, _Shape())
        else:
            axis = row["axis_id"]
            role = name[len(axis) + 1:]
            geometry.candidate_installed_hardware.setdefault(axis, {}).setdefault(role, _Shape())
            geometry.candidate_bores.setdefault(axis, _Bore(row.get("family"), row.get("station_id")))
    report = {
        "schema": "wood_joint_wj24_design_review_test/v1",
        "revision_id": revision_id,
        "source_commit": parent["source_binding"]["source_commit"],
        "source_inventory_sha256": parent["source_binding"]["source_inventory_sha256"],
        "changed_display_solid_ids": {
            "finished_hosts": [host_id],
            "finished_candidate_parts": [part_id],
            "panel_replacements": ["main_lower_left"],
            "candidate_installed_hardware": [old_hardware["id"]],
        },
        "model_inventory": inventory,
        "findings": [{"id": "fresh-revision-finding", "severity": "open_review"}],
        "checks": {"fresh_revision_check": True},
    }
    return raw, parent, geometry, report, report["changed_display_solid_ids"]


def _flatten(categories):
    return {value for values in categories.values() for value in values}


def test_incremental_scene_preserves_parent_meshes_and_adds_panel_replacement():
    raw, parent, geometry, report, categories = _fixture()
    changed = _flatten(categories)
    scene = exporter.build_design_review_scene(
        geometry,
        report,
        base_scene=parent,
        base_scene_bytes=raw,
    )

    assert scene["schema"] == "owner_wood_joints_design_review_scene/v1"
    assert scene["revision_id"] == "lower-rear-blocks-below-v1"
    assert scene["layout_status"] == "DESIGN_REVIEW"
    assert len(scene["solids"]) == 568
    assert scene["counts"]["rendered_overlay_solids"] == 568
    assert scene["counts"]["baseline_assets"] == 725
    assert scene["counts"]["visible_baseline_assets"] == 537
    assert len(scene["baseline_asset_sha256"]) == 725
    assert scene["baseline_asset_sha256"] == parent["baseline_asset_sha256"]
    assert "main_lower_left" in scene["hidden_baseline_visual_names"]
    assert scene["model_inventory"]["panel_screw_axis_count"] == 66
    assert len(scene["model_inventory"]["fixed_panel_axes"]) == 65
    assert len(scene["model_inventory"]["moved_panel_axes"]) == 1
    assert all(scene[flag] is False for flag in exporter.FALSE_CLAIM_FLAGS)
    assert all(value is False for value in scene["release"].values())
    assert scene["findings"] == report["findings"]
    assert not {
        "composition_report",
        "diagnostic_report",
        "finite_contact_supplement",
        "led_extraction_diagnostic",
    } & set(scene)

    old_by_id = {row["id"]: row for row in parent["solids"]}
    new_by_id = {row["id"]: row for row in scene["solids"]}
    assert set(old_by_id) - changed <= set(new_by_id)
    for solid_id in set(old_by_id) - changed:
        assert new_by_id[solid_id] == old_by_id[solid_id]
    assert "main_lower_left" in new_by_id
    assert new_by_id["main_lower_left"]["role"] == "candidate_panel_replacement"

    referenced = {row["mesh"]["triangle_topology_sha256"] for row in scene["solids"]}
    assert referenced == set(scene["triangle_topologies"])
    assert all(
        len(base64.b64decode(row["triangle_indices_base64"])) == row["index_count"] * 2
        or row["triangle_component_type"] == "uint32"
        for row in scene["triangle_topologies"].values()
    )
    assert scene["source_binding"]["parent_scene_sha256"] == exporter.BASE_SCENE_SHA256
    assert json.loads(exporter.scene_json_bytes(scene))["revision_id"] == scene["revision_id"]


def test_reported_mesh_delta_must_have_revised_geometry_shape():
    raw, parent, geometry, report, _categories = _fixture()
    report["changed_display_solid_ids"]["finished_hosts"].append("missing_host")
    with pytest.raises(ValueError, match="absent from revised geometry"):
        exporter.build_design_review_scene(geometry, report, base_scene=parent, base_scene_bytes=raw)


def test_removed_backer_and_bolt_visuals_require_explicit_removal():
    raw, parent, geometry, report, _categories = _fixture()
    backer = "inner_kicker_backer_left"
    axis = "backer_header_left_2"
    removed = [backer, *(f"{axis}/{role}" for role in geometry.candidate_installed_hardware[axis])]
    del geometry.finished_candidate_parts[backer]
    del geometry.candidate_bores[axis]
    del geometry.candidate_installed_hardware[axis]
    report["model_inventory"]["candidate_axes"].pop(axis, None)
    with pytest.raises(ValueError, match="removed display IDs must exactly match"):
        exporter.build_design_review_scene(geometry, report, base_scene=parent, base_scene_bytes=raw)
    report["removed_display_solid_ids"] = removed
    scene = exporter.build_design_review_scene(geometry, report, base_scene=parent, base_scene_bytes=raw)
    assert not set(removed) & {row["id"] for row in scene["solids"]}
    assert len(scene["solids"]) == 568 - len(removed)
