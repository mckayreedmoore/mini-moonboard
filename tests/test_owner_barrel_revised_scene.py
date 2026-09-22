"""The owner-facing scene composes trial geometry without a release."""

import json

from scripts.export_owner_barrel_scene import OUTPUT, build_scene, build_viewer_assembly


def test_revised_viewer_assembly_keeps_complete_no_release_inventory():
    assembly = build_viewer_assembly()
    assert len(assembly["station_modes"]) == 24
    assert len(assembly["bolts"]) == 48
    assert len(assembly["barrels"]) == 48
    assert len(assembly["panel_connections"]) == 66
    assert len(assembly["frame_connections"]) == 12
    assert set(assembly["station_dispositions"].values()) == {"REVISE"}
    assert not any(assembly["release_flags"].values())
    assert assembly["hardware_basis"]["bolt_lengths_mm_nominal_trials"] == [
        101.6,
        127.0,
    ]
    producer = assembly["diagnostics"]["producer_diagnostics"]
    assert all(
        "viewer-revision-v1" in producer[family]["source_id"]
        for family in ("rail10", "center6", "outer_top8")
    )
    for station in ("clip_split_base_center_left", "clip_split_base_center_right"):
        bolts = [
            bolt
            for name, bolt in assembly["bolts"].items()
            if assembly["bolt_station"][name] == station
        ]
        assert len(bolts) == 2
        assert all(abs(bolt.length - 101.6) < 1e-6 for bolt in bolts)
    for side in ("left", "right"):
        station = f"clip_timber_header_outer_{side}"
        rows = [
            bolt.start.y
            for name, bolt in assembly["bolts"].items()
            if assembly["bolt_station"][name] == station
        ]
        assert sorted(rows) == [-135.0, -85.0]


def test_published_scene_is_the_exact_current_source_export():
    published = OUTPUT.read_bytes()
    generated = (json.dumps(build_scene(), separators=(",", ":")) + "\n").encode()
    assert published == generated
    scene = json.loads(published)
    assert scene["outer_header_recess_trial"]["forward_row_y_mm"] == -85.0
    assert not scene["layout_clearance_approved"]
    assert not scene["drilling_released"]
