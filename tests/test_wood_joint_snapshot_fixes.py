import hashlib
import json
from pathlib import Path

import cadquery as cq
import pytest

from mini_moonboard import hold_tnut_reinforcement as hold_tnuts
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts.wood_joint_wj03_sequence import (
    SEQUENCE_DEPENDENCIES,
    _moving_panel_assembly,
    _screw_screen,
    _without_moving_panel_tnuts,
)
from scripts.wood_joint_wj04_early_mechanics import build_report as build_wj04_mechanics
from scripts.wood_joints_wj05_center_backer_transfer_probe import (
    BACKER_BOLT_STATIONS,
    BOLT_UNDERHEAD_Z_MM,
    UNDERHEAD_TO_WOOD_END_MM,
    WOOD_GRIP_CAD_MM,
    _fastener_stack_screen,
    _source_and_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_WJ03_SEQUENCE_DEPENDENCIES = frozenset(
    {
        "docs/panel-insert-reference.json",
        "mini_moonboard/base_frame.py",
        "mini_moonboard/connection_geometry.py",
        "mini_moonboard/floor_flush_width.py",
        "mini_moonboard/hold_tnut_reinforcement.py",
        "mini_moonboard/insert_frame.py",
        "mini_moonboard/model.py",
        "mini_moonboard/panel_grid.py",
        "mini_moonboard/panel_grid_v2.py",
        "mini_moonboard/wood_joint_frame.py",
        "mini_moonboard/wood_joint_geometry.py",
        "mini_moonboard/wood_joint_panel_machining.py",
        "scripts/owner_layout_protected.py",
        "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
    }
)


def test_wj03_screw_withdrawal_separates_expected_receiver_from_new_blocker():
    record = {
        "axis_id": "panel_screw_test",
        "panel_member": "panel_test",
        "candidate_finished_receiver_member": "receiver_test",
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "axis_global_xyz": [0.0, 0.0, 1.0],
        "source_occupied_length_mm": 5.0,
        "source_occupied_diameter_mm": 4.0,
        "shop_purchased_length_mm": 10.0,
    }
    receiver = cq.Solid.makeBox(8.0, 8.0, 5.0, cq.Vector(-4.0, -4.0, 0.0))
    new_obstruction = cq.Solid.makeCylinder(
        3.0, 1.0, cq.Vector(0.0, 0.0, 2.0), cq.Vector(0.0, 0.0, 1.0)
    )
    unrelated_wood_obstruction = cq.Solid.makeBox(
        6.0, 6.0, 1.0, cq.Vector(-3.0, -3.0, 2.0)
    )

    result = _screw_screen(
        [record],
        {
            "wood/receiver_test": receiver,
            "wood/other_member": unrelated_wood_obstruction,
            "protected/new_obstruction": new_obstruction,
        },
        "panel_test",
    )["panel_screw_test"]

    intended = result["intended_receiver_path"]
    withdrawal = result["shank_withdrawal_sweep"]
    assert intended["present"]
    assert intended["shaft_receiver_intersection_volume_mm3"] > 0
    assert intended["intersection_volume_is_not_an_engagement_test"]
    assert intended["excluded_from_withdrawal_obstruction_hits"]
    assert intended["engagement_status"] == "not_assessed"
    assert "wood/receiver_test" not in withdrawal["hits"]
    assert "wood/other_member" in withdrawal["hits"]
    assert "protected/new_obstruction" in withdrawal["hits"]
    assert not withdrawal["passes_nominal_screen"]
    assert result["tool_envelope"]["passes_nominal_screen"]


def test_wj03_panel_motion_uses_declared_tnut_owner_and_keeps_led_service_fixed():
    panel = cq.Solid.makeBox(10.0, 10.0, 5.0, cq.Vector(0.0, 0.0, 0.0))
    attached_tnut = cq.Solid.makeBox(
        4.0, 4.0, 1.0, cq.Vector(3.0, 3.0, -0.5)
    )
    tangent_tnut = cq.Solid.makeBox(
        4.0, 4.0, 1.0, cq.Vector(3.0, 3.0, 5.0)
    )
    nearby_tnut = cq.Solid.makeBox(
        4.0, 4.0, 1.0, cq.Vector(12.0, 3.0, -0.5)
    )
    nearby_light = cq.Solid.makeCylinder(
        2.0, 4.0, cq.Vector(5.0, 5.0, -4.0), cq.Vector(0.0, 0.0, 1.0)
    )

    members, carried_tnuts, carried_lights = _moving_panel_assembly(
        "panel_test",
        panel,
        {
            "solids": {
                "tnuts": {
                    "attached": attached_tnut,
                    "tangent": tangent_tnut,
                    "nearby": nearby_tnut,
                },
                "lights": {"separate_service": nearby_light},
            },
        },
        {
            "attached": "panel_test",
            "tangent": "panel_test",
            "nearby": "other_panel",
        },
    )

    assert panel.intersect(tangent_tnut).Volume() == pytest.approx(0.0)
    assert carried_tnuts == ["attached", "tangent"]
    assert carried_lights == []
    assert [name for name, _ in members] == [
        "panel", "tnut/attached", "tnut/tangent",
    ]


def test_wj03_kicker_path_keeps_retained_wall_tnuts_then_removes_staged_wall_tnuts():
    obstacles = {
        "wood/main_lower_right": object(),
        "tnut/wall_a": object(),
        "tnut/wall_b": object(),
        "tnut/kicker_a": object(),
        "tnut/other_panel": object(),
    }

    with_wall_installed = _without_moving_panel_tnuts(
        obstacles, {"kicker_a"},
    )
    after_wall_staged = _without_moving_panel_tnuts(
        with_wall_installed, {"kicker_a", "wall_a", "wall_b"},
    )

    assert "wood/main_lower_right" in with_wall_installed
    assert {"tnut/wall_a", "tnut/wall_b"} <= with_wall_installed.keys()
    assert "tnut/kicker_a" not in with_wall_installed
    assert "wood/main_lower_right" in after_wall_staged
    assert "tnut/wall_a" not in after_wall_staged
    assert "tnut/wall_b" not in after_wall_staged
    assert "tnut/other_panel" in after_wall_staged


def test_wj04_statics_reports_final_couple_tension_and_combined_source_closure():
    report = build_wj04_mechanics()
    max_tension = {name: 0.0 for name in ("rail", "principal")}
    for case in report["cases"]:
        for interface_name in ("rail", "principal"):
            interface = case["interfaces"][interface_name]
            path = interface["bolt_tension_and_face_contact_static_path"]
            summary_normal = report["interface_summary"][interface_name][
                "face_normal_global_xyz"
            ]
            final_forces = path["bolt_forces_on_host_global_xyz_n"]
            rows = path["bolt_rows"]
            for force, row in zip(final_forces, rows, strict=True):
                projected = sum(a * b for a, b in zip(force, summary_normal, strict=True))
                assert row["tension_after_row_moment_couple_n"] == pytest.approx(
                    max(0.0, projected), abs=2e-4,
                )
                assert row["tension_after_row_moment_couple_n"] >= row[
                    "tension_before_row_moment_couple_n"
                ]
                max_tension[interface_name] = max(
                    max_tension[interface_name],
                    row["tension_after_row_moment_couple_n"],
                )
            assert path["row_axis_moment_path"]["resolved_by_face_contact_resultant"]
            assert path["full_wrench_balanced_by_bolts_and_contact"]
            assert path["force_residual_norm_n"] < 1e-6
            # Report serialization rounds witness vectors to 1e-6 units;
            # the generator's explicit numerical balance tolerance is 1e-4.
            assert path["moment_residual_norm_nmm"] <= 1e-4
            assert path["capacity_or_contact_pressure_calculated"] is False

    for name, value in max_tension.items():
        assert report["interface_summary"][name][
            "max_bolt_tension_after_contact_couple_n"
        ] == pytest.approx(value)
    closure = report["two_interface_cleat_free_body_closure"]
    assert len(closure) == 6
    assert all(row["source_ledger_closure_only"] for row in closure)
    assert max(row["legacy_host_actions_on_bracket_force_residual_n"] for row in closure) < 0.02
    assert max(row["legacy_host_actions_on_bracket_moment_residual_nmm"] for row in closure) < 1.0


def test_wj05_bolt_datum_tip_and_nds_thread_band_use_underhead_face():
    assert BOLT_UNDERHEAD_Z_MM == 4.968
    assert UNDERHEAD_TO_WOOD_END_MM == 272.032
    assert WOOD_GRIP_CAD_MM == 270.0
    assert BACKER_BOLT_STATIONS == {
        "left": ((-35.0, -97.0), (-35.0, -63.0)),
        "right": ((41.0, -98.0), (25.0, -76.0)),
    }

    *_, bolts, _, stacks, _, _ = _source_and_candidate()
    bolt = bolts["backer_header_left_1"].BoundingBox()
    top_washer = stacks["backer_header_left_1"]["top_washer"].BoundingBox()
    top_nut = stacks["backer_header_left_1"]["top_nut"].BoundingBox()
    assert round(bolt.zmin, 3) == 4.968
    assert round(bolt.zmax, 3) == 309.768
    assert round(top_washer.zmin, 3) == 277.0
    assert round(top_nut.zmin, 3) == 283.096
    assert round(top_nut.zmax, 3) == 288.836

    triple = _fastener_stack_screen()["basis"]["option_comparison"][2]
    assert triple["asme_smooth_shank_length_range_mm_from_underhead"] == [
        268.478,
        279.4,
    ]
    assert triple["thread_exposure_in_header_mm_at_standard_min_max_smooth_shank"] == [
        3.554,
        0.0,
    ]
    assert triple["nds_nominal_d_limited_thread_rule_passes_over_full_standard_envelope"]
    assert triple[
        "thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead"
    ] == [262.507, 275.918]
    assert triple["minimum_tip_past_nut_mm_from_length_tolerance"] == 16.36
    assert triple["nominal_bolt_tip_global_z_mm"] == 309.768
    assert triple["minimum_delivered_bolt_tip_global_z_mm"] == 305.196
    assert triple["nut_bearing_face_min_nominal_max_global_z_mm"] == [
        280.886,
        281.953,
        283.096,
    ]
    assert triple["thread_transition_interval_global_z_mm"] == [
        267.475,
        280.886,
    ]

    artifact = json.loads(
        (ROOT / "docs/wood-joints-mvp/wj05-center-backer-transfer.json").read_text()
    )
    stack_screen = artifact["topology"]["fastener_stack_screen"]
    dimensions = stack_screen["basis"]["stack_dimensions_mm"]
    assert dimensions["underhead_to_wood_end_mm_including_head_washer"] == 272.032
    assert dimensions["bolt_underhead_z_mm"] == 4.968
    assert dimensions["wood_span_start_z_mm"] == 7.0
    assert dimensions["wood_span_end_z_mm"] == 277.0
    assert dimensions["minimum_underhead_length_with_max_washer_nut_and_thread_projection"] == 287.043
    artifact_triple = stack_screen["basis"]["option_comparison"][2]
    assert artifact_triple[
        "asme_smooth_shank_length_range_mm_from_underhead"
    ] == [268.478, 279.4]
    assert artifact_triple[
        "thread_transition_interval_for_nds_limited_thread_and_full_nut_engagement_mm_from_underhead"
    ] == [262.507, 275.918]
    assert artifact_triple["minimum_tip_past_nut_mm_from_length_tolerance"] == 16.36
    assert artifact_triple["nominal_bolt_tip_global_z_mm"] == 309.768
    assert artifact_triple["minimum_delivered_bolt_tip_global_z_mm"] == 305.196
    assert artifact_triple["nut_bearing_face_min_nominal_max_global_z_mm"] == [
        280.886,
        281.953,
        283.096,
    ]
    assert artifact_triple["thread_transition_interval_global_z_mm"] == [
        267.475,
        280.886,
    ]
    through_bolts = {
        row["id"]: row for row in artifact["topology"]["through_bolts"]
    }
    assert through_bolts["backer_header_right_1"]["axis_start_xyz_mm"] == [
        41.0,
        -98.0,
        4.968,
    ]
    assert through_bolts["backer_header_right_2"]["axis_start_xyz_mm"] == [
        25.0,
        -76.0,
        4.968,
    ]
    assert through_bolts["backer_header_right_1"]["nominal_bolt_tip_global_z_mm"] == 309.768
    assert through_bolts["backer_header_right_2"]["nominal_bolt_tip_global_z_mm"] == 309.768
    service_hits = artifact["screens"][
        "new_backer_and_fastener_geometry_vs_protected_services"
    ]["unintended_hits"]
    assert not any("wire_072_F1_G1" in str(hit) for hit in service_hits.values())
    fastener_status = artifact["topology"]["through_bolts"][0]["fastener_status"]
    assert fastener_status.startswith(
        "12-in partial-thread geometry remains conditional on measuring delivered thread transition"
    )
    assert fastener_status.endswith("no SKU or capacity accepted")
    assert artifact["source_fingerprints_sha256"][
        "scripts/wood_joints_wj05_center_backer_transfer_probe.py"
    ] == hashlib.sha256(
        (ROOT / "scripts/wood_joints_wj05_center_backer_transfer_probe.py").read_bytes()
    ).hexdigest()


def test_wj03_sequence_declares_current_producer_dependencies():
    assert set(SEQUENCE_DEPENDENCIES) == EXPECTED_WJ03_SEQUENCE_DEPENDENCIES


def test_wj03_sequence_snapshot_binds_current_producer_and_inputs():
    report = json.loads(
        (ROOT / "docs/wood-joints-mvp/wj03-sequence-diagnostic.json").read_text()
    )
    binding = report["authority"]
    source_inventory = json.loads(
        (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_text()
    )
    runtime_dependencies = set(
        source_inventory["source_runtime_module_hashes_sha256"]
    )
    assert set(binding["dependency_sha256"]) == (
        EXPECTED_WJ03_SEQUENCE_DEPENDENCIES | runtime_dependencies
    )
    assert binding["producer_sha256"] == hashlib.sha256(
        (ROOT / "scripts/wood_joint_wj03_sequence.py").read_bytes()
    ).hexdigest()
    assert binding["source_inventory_sha256"] == hashlib.sha256(
        (ROOT / "docs/wood-joints-mvp/source-inventory.json").read_bytes()
    ).hexdigest()
    for relative_path, expected in binding["dependency_sha256"].items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected


def test_wj03_staging_carries_panel_tnuts_and_keeps_other_panel_tnuts():
    report = json.loads(
        (ROOT / "docs/wood-joints-mvp/wj03-sequence-diagnostic.json").read_text()
    )
    all_tnut_datums = hold_tnuts.datums(variant(KERF_RIGHT))
    for side, row in report["panel_and_kicker_sequences"].items():
        ownership = row["moving_tnut_source_ownership"]
        stage = row["kicker_translation_after_screws_removed"][
            "adjacent_panel_tnut_obstacle_state"
        ]
        lower_panel = f"main_lower_{side}"
        assert stage["with_adjacent_panel_retained"] == ownership[lower_panel]["ids"]
        assert stage["after_adjacent_panel_staged"] == ownership[lower_panel]["ids"]
        other_panel_tnuts = stage["other_panel_tnuts_retained_after_staging"]
        removed_tnuts = set(ownership[lower_panel]["ids"])
        removed_tnuts.update(ownership[f"kicker_{side}"]["ids"])
        expected_other_panel_tnuts = {
            datum["name"] for datum in all_tnut_datums
        } - removed_tnuts
        assert set(other_panel_tnuts) == expected_other_panel_tnuts
        assert set(stage["after_adjacent_panel_staged"]).isdisjoint(
            other_panel_tnuts
        )


def test_wj03_reverse_route_refastens_kicker_while_lower_panel_is_staged_away():
    report = json.loads(
        (ROOT / "docs/wood-joints-mvp/wj03-sequence-diagnostic.json").read_text()
    )
    for side, row in report["panel_and_kicker_sequences"].items():
        lower = f"main_lower_{side}"
        kicker = f"kicker_{side}"
        route = row["adjacent_lower_panel_extraction"]["staged_reverse_route"]
        assert len(route) == 4
        assert "outer-node connectors" in route[0]
        assert "independently support" in route[0]
        assert "before returning either panel" in route[0]
        assert "capture and retrieve all removed hardware" in route[0]
        assert lower in route[1] and "staged pose" in route[1]
        assert kicker in route[1] and "opposite its +Y extraction direction" in route[1]
        assert lower in route[2] and "still staged" in route[2]
        assert kicker in route[2] and "refasten" in route[2]
        assert "unchanged 9 axes" in route[2]
        assert "WJ-05 diagnostic backer receivers" in route[2]
        assert "real tool access" in route[2] and "service handling" in route[2]
        assert "Then return" in route[3] and lower in route[3]
        assert "opposite its outward extraction direction (+N)" in route[3]
        assert "unchanged 12 axes" in route[3]
        assert "support" in route[3] and "real tool access" in route[3]
        assert "service handling" in route[3]
