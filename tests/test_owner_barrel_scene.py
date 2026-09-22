"""The published barrel scene is a complete, explicitly unqualified snapshot."""

import json
from pathlib import Path

from scripts.simple_owner_duty_ledger import selected_duties


def test_published_barrel_scene_inventory_and_release_boundary():
    path = Path(__file__).resolve().parents[1] / "site/owner-barrel-layout-scene.json"
    scene = json.loads(path.read_text())
    duties = set(selected_duties())
    inventory = scene["inventory"]
    assert scene["schema"] == "owner_barrel_layout_scene/v1"
    assert scene["status"] == "complete_layout_concept_not_qualified"
    assert scene["baseline"] == "compact-floor-flush-kerf-right"
    assert set(scene["station_modes"]) == set(scene["station_dispositions"]) == duties
    assert inventory["replaced_angle_duties"] == 24
    assert inventory["removed_structural_sds"] == 144
    assert inventory["direct_joint_duties"] == 20
    assert inventory["mixed_compact_block_duties"] == 4
    assert inventory["barrel_nut_envelopes"] == 48
    assert inventory["new_diagnostic_bolt_axes"] == 48
    assert inventory["fixed_panel_kicker_screw_axes"] == 66
    assert inventory["retained_frame_bolt_axes"] == 12
    assert len(scene["hidden_baseline_visual_names"]) == 170
    assert {row["source_station"] for row in scene["barrel_nut_envelopes"]} == duties
    assert {row["source_station"] for row in scene["diagnostic_bolt_axes"]} == duties
    assert all(row["mesh"]["triangles"] for row in scene["barrel_nut_envelopes"])
    assert scene["cross_family_physical_clash_stations"] == []
    assert all(
        scene[key] is False
        for key in (
            "layout_clearance_approved",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )
