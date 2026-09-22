"""Bounded real-producer barrel scene inventory check; no release verdict."""

from scripts.owner_barrel_layout_assembly import build_assembly


def test_real_three_producer_whole_frame_inventory():
    scene = build_assembly()
    assert len(scene["station_modes"]) == 24
    assert set(scene["station_dispositions"]) == set(scene["station_modes"])
    assert len(scene["bolts"]) == len(scene["bolt_station"])
    assert len(scene["barrels"]) == len(scene["barrel_station"])
    assert len(scene["removed_legacy_stations"]) == 24
    assert len(scene["removed_legacy_sds"]) == 144
    assert len(scene["panel_connections"]) == 66
    assert len(scene["frame_connections"]) == 12
    assert scene["diagnostics"]["status"] == "REVISE"
    assert not any(scene["release_flags"].values())
