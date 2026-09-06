"""Development-candidate geometry gates; not product resistance checks."""
from types import SimpleNamespace

import cadquery as cq
import pytest
import test_hybrid_frame as gates

from mini_moonboard import box_frame as b
from mini_moonboard import footprint_frame as baseline
from mini_moonboard import hybrid_frame as h
from mini_moonboard import joint_frame as frame
from mini_moonboard.box_exports import overlap
from mini_moonboard.panel_grid import main_led_datums, main_tnut_datums


@pytest.mark.parametrize("gate", [
    gates.test_solids_and_collisions,
    gates.test_connections_have_receivers_and_connected_graph,
    gates.test_tool_led_and_routing_envelopes,
    gates.test_floor_and_rib_orientation,
])
def test_candidate_existing_geometry_gates(monkeypatch, gate):
    monkeypatch.setattr(gates, "h", SimpleNamespace(
        parts=lambda size: frame.parts(), connections=lambda size: frame.connections(),
        panel_attachments=h.panel_attachments))
    gate("joint-development")


def test_preserved_baseline_and_changed_inventory():
    original = {p.name: p for p in baseline.parts(100, False)}
    candidate = {p.name: p for p in frame.parts(False)}
    assert candidate.keys() == original.keys()
    changed = {name for name in candidate if candidate[name] is not original[name]}
    assert changed == {name for name in original if name.startswith(("rib_", "angle_rib_"))} | {
        "panel_seam_vertical_lower", "panel_seam_vertical_upper"}
    assert len([p for p in candidate if p.startswith("rib_")]) == 12
    for name in ("leg_left", "leg_right", "box_side_left", "box_side_right"):
        assert candidate[name] is original[name]
    original_connections = {c.name: c for c in baseline.connections()}
    candidate_connections = {c.name: c for c in frame.connections()}
    assert len(candidate_connections) == len(frame.connections()) == 220
    assert candidate_connections.keys() == original_connections.keys()
    for name, c in candidate_connections.items():
        assert (c.members, c.kind) == (original_connections[name].members, original_connections[name].kind)


def test_shafts_clear_other_members_and_changed_holes_are_rebuilt():
    parts = {p.name: p.shape for p in frame.parts()}
    collisions = []
    for c in frame.connections():
        probe = cq.Solid.makeCylinder(5 if c.kind == "bolt" else c.diameter/2,
                                     c.length, c.start, c.direction)
        for name, shape in parts.items():
            # Bolt bores must be fully open through their receivers too. Screw
            # threads deliberately interfere with smaller pilot holes instead.
            if (c.kind == "bolt" or name not in c.members) and overlap(probe, shape) > .01:
                collisions.append((c.name, name))
    assert not collisions, collisions
    old = {c.name: c for c in baseline.connections()}
    # Old front screw bore and old rear beam bore are filled, not retained beside
    # the newly positioned holes. Probe well inside the applicable timber.
    for name, member, depth in (
        ("rib_1_mid_left_front", "mid_lower_left", 20),
        ("angle_rib_1_mid_left_beam_1", "rear_cross_1", 20),
    ):
        c = old[name]
        probe = cq.Solid.makeCylinder(1, 2, c.start+c.direction*depth, c.direction)
        assert overlap(probe, parts[member]) == pytest.approx(probe.Volume(), abs=1e-5)
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    for c in frame.connections():
        if c.name.startswith("rib_"):
            row = int(c.name.split("_")[1])
            expected = b.CROSS_STATIONS[row-1] + (30 if "seam_left" in c.name and row != 2 else 0)
            assert (c.start-b.point(0, 0, 0)).dot(tangent) == pytest.approx(expected)


def test_front_screw_internal_relief_screen_and_crossed_bores():
    # Necessary geometry screen, not permission to treat a hole/notch as an
    # exterior edge in a manufacturer's connection resistance calculation.
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    for c in frame.connections():
        if not c.name.startswith("rib_"):
            continue
        s = (c.start-b.point(0, 0, 0)).dot(tangent)
        distance = min(((c.start.x-(x-b.HALF))**2+(s-station)**2)**.5-20
                       for x, station in (*main_led_datums().values(), *main_tnut_datums().values()))
        assert distance >= 25.4, (c.name, distance)
        for bolt in frame.connections():
            if bolt.kind == "bolt" and c.members[1] in bolt.members:
                separation = abs((bolt.start-c.start).dot(tangent))
                assert separation-5-c.diameter/2 >= 25, (c.name, bolt.name)
