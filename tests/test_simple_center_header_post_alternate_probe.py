"""One recessed-header PB-02 joint trial must reject lost support."""

from scripts.simple_center_header_post_alternate_probe import (
    probe,
    receivers_preserved,
)


def test_receiver_loss_independently_prevents_geometry_acceptance():
    baseline = {"left": 0.7125, "right": 0.7125}
    assert receivers_preserved({"left": 0.7125, "right": 0.7125}, baseline)
    assert not receivers_preserved({"left": 0.3125, "right": 0.7125}, baseline)
    assert not receivers_preserved({"left": 0.7125}, baseline)


def test_recessed_header_trial():
    trial = probe()
    assert trial["header_bounds_mm"] == [-1219.2, 1219.2, -175.7, -61.4, 238.9, 277.0]
    assert trial["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert trial["full_intended_bore_received"] is True
    assert trial["bore_unintended_wood_hits_mm3"] == {}
    assert trial["bore_fixed_screw_hits_mm3"] == {}
    assert trial["bore_existing_bore_hits_mm3"] == {}
    assert trial["washer_bearing_fraction"] == {"rear": 1, "front": 1}
    assert trial["external_hardware_wood_hits_mm3"] == {"rear": {}, "front": {}}
    assert trial["tool_wood_hits_mm3"] == {"rear": {}, "front": {}}
    assert trial["inner_kicker_edges_supported"]["right"] is False
    assert trial["inner_kicker_edges_supported"]["left"] is False
    assert len(trial["header_screw_receiver_fraction"]) == 10
    assert set(trial["header_screw_receiver_fraction"].values()) == {0.3125}
    assert set(trial["original_header_screw_receiver_fraction"].values()) == {0.7125}
    assert trial["header_screw_receivers_preserved"] is False
    assert trial["header_z_edge_distances_mm"] == [12.7, 25.4]
    assert trial["conditional_one_direction_z_edges_pass"] is True
    assert trial["conditional_reversible_z_edges_pass"] is False
    assert trial["accepted_geometry"] is False
