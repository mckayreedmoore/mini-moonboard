"""WJ-03 integrated nominal clearance, artifacts, and viewer boundary."""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import cadquery as cq
import pytest

from scripts.export_wood_joint_scene import (
    PANEL_GEOMETRY_DEPENDENCIES,
    build_scene,
)
from scripts.wood_joint_clearance import (
    CLEARANCE_OUTPUT,
    HARDWARE_OUTPUT,
    INTERFACES_OUTPUT,
    _floor_plane_clearances,
    _local_extrema,
    _local_n_extents,
    build_clearance_report,
    hardware_document,
    interface_document,
)

ROOT = Path(__file__).resolve().parents[1]
RELEASE_FLAGS = (
    "layout_accepted",
    "geometry_accepted",
    "drilling_released",
    "fabrication_released",
    "structural_released",
    "climbing_released",
)


@pytest.fixture(scope="module")
def clearance():
    return build_clearance_report()


def test_floor_family_minima_keep_each_named_assembly_group_bound():
    def box_at(z_min):
        return cq.Solid.makeBox(1.0, 1.0, 1.0, cq.Vector(0.0, 0.0, z_min))

    result = _floor_plane_clearances(
        [box_at(10.0)],
        [box_at(20.0)],
        [box_at(30.0)],
        [box_at(40.0)],
        [box_at(50.0)],
        {
            "retained_frame_bolt_installed_components": [box_at(60.0)],
            "retained_frame_bolt_tool_sweeps": [box_at(70.0)],
            "retained_frame_bolt_withdrawal_sweeps": [box_at(80.0)],
        },
    )

    assert result == {
        "connector_body": 10.0,
        "installed_hardware_only": 20.0,
        "permanent_body_and_installed_hardware": 10.0,
        "tool_only": 30.0,
        "body_hardware_and_tool": 10.0,
        "bolt_stroke_only": 40.0,
        "body_and_bolt_stroke": 10.0,
        "detached_hardware_only": 50.0,
        "body_hardware_and_detached_path": 10.0,
        "retained_frame_bolt_installed_components": 60.0,
        "retained_frame_bolt_tool_sweeps": 70.0,
        "retained_frame_bolt_withdrawal_sweeps": 80.0,
    }


def test_combined_nodes_clear_after_kicker_removal_with_sequence_still_open(clearance):
    assert len(clearance["original_six_clash_signatures"]) == 6
    assert set(clearance["original_six_clash_signatures"].values()) == {
        "absent_replaced_topology"
    }
    assert clearance["original_six_clashes_absent"] is True
    assert clearance["replacement_nominal_interference_free"] is True
    for side, row in clearance["nodes"].items():
        assert row["nominal_interference_free"] is True
        populated = {
            key: value for key, value in row["failure_groups"].items() if value
        }
        assert populated == {}
        assert len(row["panel_on_detached_path_hits"]) == 2
        assert all(
            key.startswith(f"knee_outer_{side}_bridge_link_")
            and key.endswith(f"/nut_outward|wood/kicker_{side}")
            for key in row["panel_on_detached_path_hits"]
        )
        assert row["kicker_panel_removal_sequence_verified"] is False
        assert row["floor_contact"] is False
        assert all(area > 0 for area in row["contact_areas_mm2"].values())


def test_every_bolt_has_full_envelope_length_and_access_records(clearance):
    for row in clearance["nodes"].values():
        assert len(row["bolt_reports"]) == 10
        for bolt in row["bolt_reports"].values():
            assert bolt["stack_length_passes"] is True
            assert bolt["nut_on_provisional_usable_thread"] is True
            assert set(bolt["installed_envelope_bounds_xyz_mm"]) == {
                "shaft",
                "head",
                "head_washer",
                "nut_washer",
                "nut",
            }
            assert set(bolt["access_sweep_bounds_xyz_mm"]) == {"head", "nut"}
            assert bolt["access_sweep_result"]["passes_nominal_screen"] is True
            stroke = bolt["straight_bolt_insertion_and_reverse_withdrawal"]
            assert set(stroke["sweep_bounds_xyz_mm"]) == {
                "shaft_insertion_and_withdrawal",
                "head_insertion_and_withdrawal",
            }
            assert stroke["passes_nominal_screen"] is True
            assert bolt["hardware_clearance_result"]["passes_nominal_screen"] is True
            assert all(seat["full_seat"] for seat in bolt["washer_support"].values())


def test_nominal_layout_requests_named_rear_exception_and_keeps_tolerances_open(
    clearance,
):
    assert clearance["replacement_nominal_interference_free"] is True
    assert clearance["advance_layout"] is False
    assert clearance["tolerance_aware_clearance_complete"] is False
    assert clearance["decision"] == "revise_named_constraint"
    revisions = {
        row["constraint"]: row for row in clearance["named_constraint_revisions"]
    }
    assert revisions["outer-node installed rear envelope"][
        "additional_projection_mm"
    ] == pytest.approx(86.018477)
    assert revisions["outer-node temporary bolt insertion envelope"][
        "additional_projection_mm"
    ] == pytest.approx(175.948756)
    for row in clearance["nodes"].values():
        frame = row["named_clearances"]["local_frame"]
        assert frame["n_global_xyz"] == pytest.approx(
            [0.0, -0.766044443119, 0.642787609687]
        )
        envelopes = row["named_clearances"]["local_n_envelopes_mm"]
        assert envelopes["connector_body"]["n_min_mm"] == pytest.approx(-15.903389)
        assert envelopes["permanent_body_and_installed_hardware"][
            "rearward_projection_mm"
        ] == pytest.approx(225.718477)
        assert envelopes["tool_only"]["rearward_projection_mm"] == pytest.approx(
            197.875857
        )
        assert len(row["connector_part_local_extrema"]) == 3
        assert len(row["changed_source_host_local_extrema"]) == 3
        for part in (
            *row["connector_part_local_extrema"].values(),
            *row["changed_source_host_local_extrema"].values(),
        ):
            assert set(part) == {"X", "T", "N"}
            assert all(axis["span_mm"] > 0 for axis in part.values())
        assert row["named_clearances"][
            "connector_body_to_base_floor_member_vertical_mm"
        ] == pytest.approx(6.35)
        assert row["named_clearances"][
            "connector_body_to_floor_plane_z0_mm"
        ] == pytest.approx(146.05)
        assert row["named_clearances"][
            "connector_and_installed_hardware_to_floor_plane_z0_mm"
        ] == pytest.approx(126.251)
        assert all(
            value > 0
            for value in row["named_clearances"][
                "floor_plane_clearance_by_family_mm"
            ].values()
        )
        assert set(row["named_clearances"]["floor_plane_clearance_by_family_mm"]) == {
            "connector_body",
            "installed_hardware_only",
            "permanent_body_and_installed_hardware",
            "tool_only",
            "body_hardware_and_tool",
            "bolt_stroke_only",
            "body_and_bolt_stroke",
            "detached_hardware_only",
            "body_hardware_and_detached_path",
            "retained_frame_bolt_installed_components",
            "retained_frame_bolt_tool_sweeps",
            "retained_frame_bolt_withdrawal_sweeps",
        }
        assert row["named_clearances"][
            "post_nut_tool_to_shifted_link_exact_mm"
        ] == pytest.approx(19.0)
        assert row["named_clearances"][
            "rear_bridge_to_header_rear_mm"
        ] == pytest.approx(6.35)


def test_local_n_extrema_match_direct_canonical_axis_projection():
    shape = (
        cq.Workplane("XY")
        .box(17.0, 29.0, 41.0)
        .rotate((0, 0, 0), (1, 0, 0), 13.0)
        .translate((11.0, -23.0, 37.0))
        .val()
    )
    datum = cq.Vector(3.0, 5.0, 7.0)
    angle = math.radians(50.0)
    axes = {
        "X": cq.Vector(1.0, 0.0, 0.0),
        "T": cq.Vector(0.0, math.cos(angle), math.sin(angle)),
        "N": cq.Vector(0.0, -math.sin(angle), math.cos(angle)),
    }
    extrema = _local_extrema(shape, datum)
    for name, axis in axes.items():
        projected = [vertex.Center().dot(axis) for vertex in shape.Vertices()]
        datum_projection = datum.dot(axis)
        assert extrema[name]["min_mm"] == pytest.approx(
            min(projected) - datum_projection
        )
        assert extrema[name]["max_mm"] == pytest.approx(
            max(projected) - datum_projection
        )
    n_extrema = _local_n_extents([shape], datum)
    assert n_extrema["n_min_mm"] == pytest.approx(extrema["N"]["min_mm"])
    assert n_extrema["n_max_mm"] == pytest.approx(extrema["N"]["max_mm"])


def test_combined_scene_keeps_trial_boundaries_and_release_boundary(clearance):
    interfaces = interface_document()
    hardware = hardware_document()
    scene = build_scene(clearance=clearance)
    geometry_module = ROOT / "mini_moonboard/wood_joint_geometry.py"
    geometry_sha256 = hashlib.sha256(geometry_module.read_bytes()).hexdigest()
    for artifact in (interfaces, hardware, clearance, scene):
        assert (
            artifact["producer"]["dependency_sha256"][
                "mini_moonboard/wood_joint_geometry.py"
            ]
            == geometry_sha256
        )
    assert interfaces["counts"] == {
        "legacy_duties": 4,
        "nodes": 2,
        "cut_wood_parts": 6,
        "changed_source_hosts": 5,
        "source_host_bores": 12,
        "interfaces": 12,
    }
    assert hardware["counts"]["bolts_total"] == 20
    assert hardware["counts"]["nominal_length_counts_mm"] == {
        "203.2": 12,
        "152.4": 8,
    }
    assert scene["schema"] == "owner_wood_joints_layout_scene/v2"
    assert set(scene["trials"]) == {"wj03", "wj04", "wj05"}
    assert scene["legacy_duty_summary"]["total"] == 24
    assert scene["legacy_duty_summary"]["trial_geometry_duties"] == 5
    assert scene["legacy_duty_summary"]["remaining_legacy_duties"] == 19
    assert set(scene["trials"]["wj03"]["legacy_duty_ids"]) == {
        "clip_angle_base_left",
        "clip_angle_base_right",
        "clip_timber_header_outer_left",
        "clip_timber_header_outer_right",
    }
    assert scene["trials"]["wj04"]["legacy_duty_ids"] == [
        "clip_horizontal_lower_right_1"
    ]
    assert scene["trials"]["wj05"]["legacy_duty_ids"] == []
    assert (
        scene["legacy_duty_summary"]["wj05_receiver_trial_maps_structural_duty"]
        is False
    )
    assert len(scene["hidden_baseline_visual_names"]) == 47
    panel_replacements = {
        "main_lower_right",
        "main_upper_right",
        "kicker_right",
    }
    assert panel_replacements <= set(scene["hidden_baseline_visual_names"])
    panel_solids = {
        row["name"]: row for row in scene["solids"] if row["role"] == "candidate_panel"
    }
    assert set(panel_solids) == panel_replacements
    assert all(row["family"] == "shared" for row in panel_solids.values())
    assert all(
        row["trial_id"] == "shared_candidate_kerf_right_panel_machining"
        for row in panel_solids.values()
    )
    assert scene["candidate_panel_overlay"] == {
        "family": "shared",
        "trial_id": "shared_candidate_kerf_right_panel_machining",
        "status": "candidate_geometry_only",
        "panel_ids": sorted(panel_replacements),
        "source_commit": scene["source_binding"]["source_commit"],
        "source_inventory_sha256": scene["source_binding"]["source_inventory_sha256"],
        "accepted": False,
    }

    inventory = scene["inventory"]
    assert inventory == {
        "mapped_legacy_duties": 5,
        "removed_legacy_sds_visuals": 30,
        "outer_nodes": 2,
        "connector_cut_parts": 7,
        "candidate_panel_replacements": 3,
        "changed_source_hosts": 9,
        "source_host_bores": 20,
        "provisional_bolts": 28,
        "installed_hardware_component_solids": 140,
        "fixed_panel_kicker_screw_axes": 66,
        "retained_frame_bolt_axes": 12,
        "trial_geometry_solids": 169,
        "baseline_assets": 725,
    }
    assert inventory["trial_geometry_solids"] == len(scene["solids"])
    assert len(scene["baseline_asset_sha256"]) == 725
    assert len(scene["baseline_asset_tree_sha256"]) == 64
    assert all(row["mesh"]["triangles"] for row in scene["solids"])
    for panel_dependency in PANEL_GEOMETRY_DEPENDENCIES:
        assert (
            scene["producer"]["dependency_sha256"][panel_dependency]
            == hashlib.sha256((ROOT / panel_dependency).read_bytes()).hexdigest()
        )

    solids_by_family = Counter(row["family"] for row in scene["solids"])
    axes_by_family = Counter(row["family"] for row in scene["provisional_bolt_axes"])
    assert solids_by_family == {"wj03": 110, "wj04": 23, "wj05": 32, "shared": 4}
    assert axes_by_family == {"wj03": 20, "wj04": 4, "wj05": 4}
    for family in ("wj03", "wj04", "wj05"):
        trial = scene["trials"][family]
        assert trial["geometry_solid_count"] == solids_by_family[family]
        assert all(
            solid["trial_id"] == trial["trial_id"]
            for solid in scene["solids"]
            if solid["family"] == family
        )
    assert (
        sum(
            solid["role"] == "trial_tool_envelope" and solid["family"] == "wj05"
            for solid in scene["solids"]
        )
        == 8
    )

    assert (
        scene["trials"]["wj03"]["local_clearance"]["original_six_clashes_absent"]
        is True
    )
    assert (
        scene["trials"]["wj03"]["local_clearance"][
            "replacement_nominal_interference_free"
        ]
        is True
    )
    assert scene["trials"]["wj03"]["local_clearance"]["decision"] == (
        "revise_named_constraint"
    )
    assert (
        scene["trials"]["wj03"]["local_clearance"][
            "kicker_panel_removal_sequence_verified"
        ]
        is False
    )
    assert (
        scene["trials"]["wj04"]["local_screen"]["full_candidate_clearance"] == "not_run"
    )
    assert scene["trials"]["wj05"]["receiver_status"] == (
        "blocked_center_receiver_path"
    )
    assert len(scene["trials"]["wj05"]["receiver_axis_ids"]) == 4
    assert scene["trials"]["wj05"]["gates"]["receiver_path_resolved"] is False

    assert scene["integrated_clearance"] == {
        "status": "not_run",
        "cross_trial_interference_checked": False,
        "full_candidate_clearance_checked": False,
        "integrated_joint_acceptance": False,
    }
    assert all(scene[flag] is False for flag in RELEASE_FLAGS)
    for trial in scene["trials"].values():
        assert all(trial["gates"][flag] is False for flag in RELEASE_FLAGS)


def test_source_binding_and_retained_hardware_are_explicit(clearance):
    assert (
        clearance["source_binding"]["source_commit"]
        == "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
    )
    screen = clearance["source_inventory"]
    assert screen["panel_screw_screen"]["count"] == 66
    assert screen["panel_screw_screen"]["purchased_length_mm"] == 63.5
    assert screen["retained_frame_bolt_screen"]["installed_components"] == 60
    assert screen["retained_frame_bolt_screen"]["tool_sweeps"] == 24
    assert screen["retained_frame_bolt_screen"]["withdrawal_sweeps"] == 24
    assert screen["retained_legacy_screen"] == {
        "connector_bodies": 20,
        "sds_envelopes": 120,
        "removed_target_connector_bodies": 4,
        "removed_target_sds_envelopes": 24,
    }
    assert all(
        not row["failure_groups"]["source_host_retained_hardware"]
        for row in clearance["nodes"].values()
    )


def test_checked_in_wj03_artifacts_match_generators(clearance):
    assert json.loads(INTERFACES_OUTPUT.read_text()) == interface_document()
    assert json.loads(HARDWARE_OUTPUT.read_text()) == hardware_document()
    assert json.loads(CLEARANCE_OUTPUT.read_text()) == clearance
    scene_path = ROOT / "site/owner-wood-joints-layout-scene.json"
    generated_scene_on_wire = json.loads(json.dumps(build_scene(clearance=clearance)))
    assert json.loads(scene_path.read_text()) == generated_scene_on_wire


def test_external_artifact_manifest_hashes_checked_in_outputs():
    manifest = json.loads(
        (ROOT / "docs/wood-joints-mvp/artifact-manifest.json").read_text()
    )
    assert manifest["candidate"] == "compact-floor-flush-wood-joints-development"
    for relative, expected in manifest["artifact_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
