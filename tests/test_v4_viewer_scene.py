"""The development overlay must follow the maintained PB02/PB03 poses."""

import json
from pathlib import Path

import pytest

from scripts.export_v4_viewer_scene import build_scene


def test_v4_overlay_uses_current_pb02_and_pb03_geometry():
    scene = build_scene()
    assert scene["status"] == "partial_development_visualization"
    assert scene["baseline"] == "compact-floor-flush-kerf-right"
    assert scene["fixed_panel_kicker_screw_axes"] == 66
    assert scene["pb02_variant_id"] == "ligament_priority"
    assert scene["pb02_source_fingerprint"] == (
        "4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb"
    )
    assert scene["pb03_source_id"] == (
        "pb03-lower-service-plus-upper-and-bottom-outer-v1"
    )
    blocks = {part["name"]: part for part in scene["boxes"]}
    assert "PB01 short rail block" not in blocks
    pb03_blocks = {
        name: block for name, block in blocks.items() if block["station"] == "PB03"
    }
    assert set(pb03_blocks) == {
        "pb03_lower_center_left_block",
        "pb03_lower_center_right_block",
        "pb03_lower_outer_left_block",
        "pb03_lower_outer_right_block",
        "pb03_upper_outer_left_block",
        "pb03_upper_outer_right_block",
        "pb03_bottom_outer_left_block",
        "pb03_bottom_outer_right_block",
    }
    assert {tuple(block["size_mm"]) for block in pb03_blocks.values()} == {
        (139.7, 57.15, 300)
    }
    assert pb03_blocks["pb03_lower_center_left_block"]["center_mm"][0] < 0
    assert pb03_blocks["pb03_lower_center_right_block"]["center_mm"][0] > 0
    assert blocks["PB02 post/header block"]["size_mm"] == [88.9, 88.9, 143.9]
    assert blocks["PB02 revised upright-side cleat"]["size_mm"] == pytest.approx(
        [88.9, 61.6, 183]
    )
    assert blocks["PB02 revised header-side cleat"]["origin_mm"][2] == 277
    assert blocks["PB02 revised header-side cleat"]["size_mm"][2] == 67
    assert blocks["PB02 shifted right center post"]["origin_mm"] == [
        88.75,
        -175.7,
        0,
    ]
    rear_cleat = blocks["PB02 rear return block"]
    assert rear_cleat["origin_mm"] == pytest.approx([89.05, -213.8, 5])
    assert rear_cleat["size_mm"] == pytest.approx([88.9, 38.1, 455])
    assert rear_cleat["origin_mm"][2] + rear_cleat["size_mm"][2] == 460
    assert blocks["PB02 kicker backer"]["size_mm"] == [139.7, 88.9, 238.9]
    assert len([axis for axis in scene["axes"] if axis["station"] == "PB02"]) == 10
    assert len([axis for axis in scene["axes"] if axis["station"] == "PB03"]) == 32
    assert {axis["name"] for axis in scene["axes"] if axis["station"] == "PB02"} == {
        "post_cleat_1",
        "post_cleat_2",
        "cleat_header_1",
        "cleat_header_2",
        "header_cleat",
        "cleat_principal",
        "post_low",
        "post_high",
        "upright",
        "cleat_link",
    }
    axes = {axis["name"]: axis for axis in scene["axes"] if axis["station"] == "PB02"}
    assert axes["post_cleat_2"]["start_mm"][2] == 176
    assert axes["post_high"]["start_mm"][2] == 202
    assert axes["cleat_header_1"]["start_mm"][:2] == [208.35, -130.5]
    assert axes["cleat_header_2"]["start_mm"][:2] == [236.0, -117.5]
    assert axes["cleat_link"]["start_mm"][2] == 328.5
    assert axes["upright"]["start_mm"][1:] == [-144.5, 356]
    assert scene["assembly_contract"] == {
        "width_option": "kerf-right",
        "kerf_total_mm": 3.175,
        "kicker_panel_width_mm": 1217.6125,
        "official_kicker_panel_width_mm": 1219.2,
        "outward_shifted_center_supports": 1,
        "inner_kicker_edges_supported": {"left": True, "right": True},
        "pb02_bore_count": 10,
        "pb02_trial_stack_count": 10,
        "pb03_bore_count": 32,
        "pb03_trial_stack_count": 32,
        "pb03_block_count": 8,
        "legacy_station_count": 14,
        "legacy_sds_axis_count": 84,
        "replaced_pb03_legacy_stations": [
            "clip_horizontal_lower_left_2",
            "clip_horizontal_lower_right_1",
            "clip_horizontal_lower_left_1",
            "clip_horizontal_lower_right_2",
            "clip_horizontal_upper_left_1",
            "clip_horizontal_upper_right_2",
            "clip_horizontal_bottom_left_1",
            "clip_horizontal_bottom_right_2",
        ],
        "fixed_panel_kicker_screw_axes": 66,
        "total_connection_count": 194,
        "bolt_kind_connection_count": 44,
    }
    assert len(scene["hidden_legacy_visual_names"]) == 56
    assert set(scene["hidden_legacy_visual_names"]) >= {
        "clip_horizontal_lower_left_2",
        "clip_horizontal_lower_right_1",
    }
    hidden_counts = {
        station: sum(
            name == station or name.startswith(f"fastener_{station}_")
            for name in scene["hidden_legacy_visual_names"]
        )
        for station in scene["assembly_contract"]["replaced_pb03_legacy_stations"]
    }
    assert set(hidden_counts) == set(
        scene["assembly_contract"]["replaced_pb03_legacy_stations"]
    )
    assert set(hidden_counts.values()) == {7}
    assert scene["fabrication_released"] is False


def test_pb02_overlay_has_ten_complete_but_non_selected_trial_stacks():
    scene = build_scene()
    stacks = {
        stack["name"]: stack
        for stack in scene["hardware_stacks"]
        if stack["station"] == "PB02"
    }

    assert set(stacks) == {
        axis["name"] for axis in scene["axes"] if axis["station"] == "PB02"
    }
    assert {stack["station"] for stack in stacks.values()} == {"PB02"}
    assert {stack["orientation_selected"] for stack in stacks.values()} == {False}
    assert {stack["hardware_selected"] for stack in stacks.values()} == {False}
    assert {stack["trial_length_in"] for stack in stacks.values()} == {5, 6, 8}
    for stack in stacks.values():
        assert [part["role"] for part in stack["components"]] == [
            "shaft",
            "head",
            "near_washer",
            "far_washer",
            "nut",
        ]
        assert all(part["length_mm"] > 0 for part in stack["components"])
        assert all(part["diameter_mm"] > 0 for part in stack["components"])
    assert scene["hardware_stack_scope"] == (
        "PB02 maintained trial-length envelopes and PB03 source-derived generic "
        "stack envelopes only; no delivered product, thread interval, exact hardware, "
        "or head/nut orientation selected"
    )


def test_pb03_overlay_has_thirty_two_complete_unselected_stacks():
    scene = build_scene()
    stacks = [stack for stack in scene["hardware_stacks"] if stack["station"] == "PB03"]

    assert len(stacks) == 32
    assert {stack["source_station"] for stack in stacks} == {
        "clip_horizontal_lower_left_2",
        "clip_horizontal_lower_right_1",
        "clip_horizontal_lower_left_1",
        "clip_horizontal_lower_right_2",
        "clip_horizontal_upper_left_1",
        "clip_horizontal_upper_right_2",
        "clip_horizontal_bottom_left_1",
        "clip_horizontal_bottom_right_2",
    }
    assert {stack["orientation_selected"] for stack in stacks} == {False}
    assert {stack["hardware_selected"] for stack in stacks} == {False}
    for stack in stacks:
        assert [part["role"] for part in stack["components"]] == [
            "shaft",
            "head",
            "near_washer",
            "far_washer",
            "nut",
        ]
        assert all(part["length_mm"] > 0 for part in stack["components"])
        assert all(part["diameter_mm"] > 0 for part in stack["components"])


def test_viewer_scene_artifact_matches_producer():
    root = Path(__file__).resolve().parents[1]
    scene = build_scene()
    assert json.loads((root / "site/v4-diagnostic-scene.json").read_text()) == scene
    html = (root / "site/index.html").read_text()
    assert "DEVELOPMENT V4 · PB02/PB03 partial 3D scene" in html
    assert "fetch('v4-diagnostic-scene.json')" in html
    assert "data.pb02_variant_id !== 'ligament_priority'" in html
    assert "data.hardware_stacks.length !== 42" in html
    assert "data.hidden_legacy_visual_names?.length !== 56" in html
    assert "data.assembly_contract?.total_connection_count !== 194" in html
    assert "data.assembly_contract?.bolt_kind_connection_count !== 44" in html
    assert "PB03 eight-block/thirty-two-stack service core" in html
    assert "Exactly 14 legacy angle stations and 84 SDS axes remain" in html
    assert "v4ReplacedLegacyStations" in html
    for station in scene["assembly_contract"]["replaced_pb03_legacy_stations"]:
        assert f"'{station}'" in html
    assert "!isV4ReplacedLegacyPart(part.name)" in html
    assert "complete trial stack envelope" in html
