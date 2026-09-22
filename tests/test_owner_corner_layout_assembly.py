"""Contract for the detached 24-duty owner-layout assembly."""

from scripts import owner_layout_bottom_center_pair as bottom
from scripts import owner_layout_bottom_center_revision as revision
from scripts import simple_pb09_owner_layout_screen as pb09
from scripts.owner_corner_layout_assembly import build_assembly


def test_build_assembly_contract():
    assembly = build_assembly()
    assert len(assembly["blocks"]) == 24
    assert len(assembly["removed_legacy_stations"]) == 24
    assert len(assembly["removed_legacy_sds"]) == 144
    assert len(assembly["panel_connections"]) == 66
    assert len(assembly["frame_connections"]) == 12
    assert len(assembly["bolts"]) == len(assembly["stacks"])
    assert len(assembly["bolts"]) == len(set(assembly["bolts"]))
    assert "inner_kicker_backer_left" in assembly["wood"]
    assert "inner_kicker_backer_right" in assembly["wood"]
    assert assembly["release_flags"]["fabrication_released"] is False
    assert "cross_family_hits_mm3" in assembly["diagnostics"]
    for station in bottom.STATIONS:
        assert assembly["blocks"][station].BoundingBox().xlen == revision.BLOCK_X_MM
        assert all(
            assembly["diagnostics"]["bottom_center_complete_bores"][station].values()
        )
    assert (
        assembly["diagnostics"]["bottom_center_revision_source_id"]
        == revision.SOURCE_ID
    )
    assert "bottom_center_two" in assembly["diagnostics"]["local_dispositions"]
    assert assembly["diagnostics"]["bottom_center_open_gates"]
    service_station = pb09.lower.TARGET_STATIONS[0]
    pre_hit = assembly["diagnostics"]["pb09_service_wire_pre_cut_hit_mm3"]
    removed = assembly["diagnostics"]["pb09_service_channel_removed_mm3"]
    assert assembly["diagnostics"]["pb09_service_channel_applied"] == (pre_hit > 0)
    assert (removed > 1) == (pre_hit > 0)
    wire = pb09.protected.inventory()["solids"]["wires"]["wire_054_E6_E7"]
    assert pb09.protected._volume(assembly["blocks"][service_station], wire) <= 1
    assert not assembly["diagnostics"]["cross_family_screen_complete"]
    assert assembly["diagnostics"]["outer_base_full_length_shaft_displayed"] is False
