"""Replacement-route geometry checks only; no product, glue or capacity approval."""
from types import SimpleNamespace

import cadquery as cq
import pytest
import test_hybrid_frame as gates

from mini_moonboard import clip_frame as baseline
from mini_moonboard import hybrid_frame as h
from mini_moonboard import transition_frame as frame
from mini_moonboard.box_exports import exact_bounds, overlap


def test_additive_profiles_preserve_original_stock_and_two_ply_thickness():
    original = {p.name: p for p in baseline.parts(False)}
    raw = {p.name: p for p in frame.parts(False)}
    assert len(original) == 75 and len(raw) == 87
    for name, part in original.items():
        if not name.startswith("cheek_splice_"):
            assert raw[name] is part
            continue
        plies = [raw[name+suffix] for suffix in ("_inner", "_outer")]
        combined = plies[0].shape.fuse(plies[1].shape)
        assert overlap(plies[0].shape, plies[1].shape) < .01
        assert exact_bounds(combined).xlen == pytest.approx(38.1, abs=1e-6)
        assert overlap(combined, part.shape) == pytest.approx(part.shape.Volume(), abs=1e-5)
        assert combined.Volume() > part.shape.Volume()
        for ply in plies:
            assert exact_bounds(ply.shape).xlen == pytest.approx(19.05, abs=1e-6)
            assert ply.laminations == 1 and "no glue/composite/friction credit" in ply.description


def test_ten_replacement_routes_preserve_other_axes_and_explicit_through_stacks():
    original = {c.name: c for c in baseline.connections()}
    current = {c.name: c for c in frame.connections()}
    assert len(current) == len(frame.connections()) == 278
    removed = {f"analysis_batten_end_{side}_{i}" for side in ("left", "right") for i in range(1, 5)} | {
        f"analysis_kicker_end_{side}_{i}" for side in ("left", "right") for i in (1, 2)}
    assert original.keys()-current.keys() == removed
    for name, old in original.items():
        if name in removed:
            continue
        new = current[name]
        assert (new.start-old.start).Length == 0
        assert new.direction.toTuple() == old.direction.toTuple()
        assert (new.kind, new.length, new.diameter, new.grip) == (old.kind, old.length, old.diameter, old.grip)
        expected = tuple(ply for member in old.members for ply in
                         ((member+"_inner", member+"_outer") if member.startswith("cheek_splice_") else (member,)))
        assert new.members == expected
    added = [c for c in current.values() if c.name not in original]
    assert len(added) == 40 and sum(c.kind == "bolt" for c in added) == 20
    assert sum(c.kind == "screw" for c in current.values()) == 164
    assert sum(c.kind == "bolt" for c in current.values()) == 114
    angles = {p.name for p in frame.parts() if p.name.startswith("transition_")}
    assert angles == {f"transition_{label}_angle_{side}" for side in ("left", "right")
                      for label in ("main", "kicker", "seam", "top", "kicker_bottom")}
    for angle in angles:
        group = [c for c in added if c.members[0] == angle]
        assert len(group) == 4 and sum(c.kind == "bolt" for c in group) == 2
    for c in added:
        assert "UNSELECTED" in c.product_status and "not a rated A21" in c.product_status
        if c.kind == "bolt":
            assert len(c.members) in (2, 4)
            assert c.grip == pytest.approx(6+38.1+(38.1 if len(c.members) == 4 else 0))
            assert c.length == (101.6 if len(c.members) == 4 else 63.5) and c.diameter == 9.525
            assert c.length-c.grip-13 == pytest.approx(6.4)
        else:
            assert (c.length, c.diameter) == (38.1, 4.826)
            assert c.members[1] in ("panel_edge_bottom", "panel_seam_horizontal", "panel_edge_top",
                                    "kicker_batten_top", "kicker_batten_bottom")


@pytest.mark.parametrize("gate", [gates.test_solids_and_collisions, gates.test_tool_led_and_routing_envelopes])
def test_complete_actual_body_head_hardware_bolt_tool_led_gates(monkeypatch, gate):
    monkeypatch.setattr(gates, "h", SimpleNamespace(parts=lambda _: frame.parts(),
        connections=lambda _: frame.connections(), panel_attachments=h.panel_attachments))
    gate(frame.KEY)


def test_all_receivers_and_new_rear_screw_access():
    parts = {p.name: p.shape for p in frame.parts()}
    hardware = {c.name: cq.Compound.makeCompound(c.components()) for c in frame.connections()}
    for c in frame.connections():
        shaft = cq.Solid.makeCylinder(c.diameter/2, c.length, c.start, c.direction)
        probe = cq.Solid.makeCylinder(5.5 if c.kind == "bolt" else 3, c.length, c.start, c.direction)
        core = cq.Solid.makeCylinder(4.9 if c.kind == "bolt" else 1.5, c.length, c.start, c.direction)
        assert all(overlap(probe, parts[name]) > 1 for name in c.members), c.name
        assert all(overlap(core, parts[name]) < .01 for name in c.members), c.name
        assert not [name for name, shape in parts.items() if (c.kind == "bolt" or name not in c.members)
                    and overlap(shaft, shape) > .01], c.name
        if not c.name.startswith("transition_") or c.kind != "screw":
            continue
        # Declared generic Ø10 driver and 25 mm approach, from the support side.
        # No claim this seats a selected screw in 6 mm steel.
        tool = cq.Solid.makeCylinder(5, 25, c.start, -c.direction)
        assert not [name for name, shape in parts.items() if overlap(tool, shape) > .01], c.name
        assert not [name for name, shape in hardware.items() if name != c.name and overlap(tool, shape) > .01], c.name
        outer = cq.Solid.makeCylinder(c.diameter/2, c.length-6, c.start+c.direction*6, c.direction)
        inner = cq.Solid.makeCylinder(1.61, c.length-6, c.start+c.direction*6, c.direction)
        ring = outer.cut(inner)
        assert overlap(ring, parts[c.members[1]]) == pytest.approx(ring.Volume(), abs=1e-5), c.name


def test_pad_bearing_and_floor_are_preserved():
    parts = {p.name: p for p in frame.parts()}
    for side in ("left", "right"):
        for layer in ("inner", "outer"):
            ply = parts[f"cheek_splice_{side}_{layer}"].shape
            assert ply.distance(parts["panel_edge_bottom"].shape) < 1e-5
            assert ply.distance(parts["kicker_batten_top"].shape) < 1e-5
        for label in (f"kicker_cheek_{side}", f"leg_{side}_inner", f"leg_{side}_outer"):
            assert exact_bounds(parts[label].shape).zmin == pytest.approx(0, abs=1e-6)


def test_original_splice_screw_driver_and_withdrawal_paths_remain_open():
    parts = {p.name: p.shape for p in frame.parts()}
    hardware = {c.name: cq.Compound.makeCompound(c.components()) for c in frame.connections()}
    old = [c for c in baseline.connections() if c.name.startswith("cheek_splice_")]
    assert len(old) == 8
    for c in old:
        # Original generic Ø10 head/driver can approach and withdraw the full
        # screw through the added steel. Actual product/tool remains unselected.
        corridor = cq.Solid.makeCylinder(5, max(25, c.length), c.start, -c.direction)
        assert not [name for name, shape in parts.items() if overlap(corridor, shape) > .01], c.name
        assert not [name for name, shape in hardware.items() if name != c.name and overlap(corridor, shape) > .01], c.name


def test_all_twelve_removed_end_screw_bores_are_refilled_in_both_receivers():
    parts = {p.name: p.shape for p in frame.parts()}
    removed = [c for c in baseline.connections() if c.name.startswith(frame.REMOVED_PREFIXES)]
    assert len(removed) == 12
    for c in removed:
        for name, depth in zip(c.members, (10., 50.), strict=True):
            probe = cq.Solid.makeCylinder(.5, 1, c.start+c.direction*depth, c.direction)
            assert overlap(probe, parts[name]) == pytest.approx(probe.Volume(), abs=1e-6), (c.name, name)


def test_every_replacement_leaf_has_contact_and_candidate_graph_is_connected():
    parts = {p.name: p.shape for p in frame.parts()}
    graph = {name: set() for name in parts}
    for c in frame.connections():
        for member in c.members:
            graph[member].update(set(c.members)-{member})
        if c.name.startswith("transition_"):
            for a, other in zip(c.members, c.members[1:]):
                assert parts[a].distance(parts[other]) < 1e-5, (c.name, a, other)
    seen, todo = set(), ["main_lower_left"]
    while todo:
        name = todo.pop()
        if name not in seen:
            seen.add(name)
            todo.extend(graph[name]-seen)
    assert seen == parts.keys()


def test_new_bolt_washers_have_full_nominal_bearing_rings():
    parts = {p.name: p.shape for p in frame.parts()}
    new = [c for c in frame.connections() if c.name.startswith("transition_") and c.kind == "bolt"]
    assert len(new) == 20
    for c in new:
        for name, depth in ((c.members[0], 2.), (c.members[-1], 2+c.grip-.5)):
            start = c.start+c.direction*depth
            ring = cq.Solid.makeCylinder(12.7, .5, start, c.direction).cut(
                cq.Solid.makeCylinder(5.1, .5, start, c.direction))
            assert overlap(ring, parts[name]) == pytest.approx(ring.Volume(), abs=1e-5), (c.name, name)
    # Tight packaging is recorded explicitly, not promoted to an installation
    # tolerance or product edge-distance qualification.
    assert 76.2-63-12.7 == pytest.approx(.5)  # Top steel edge beyond washer.
    assert 63-44.1-18 == pytest.approx(.9)  # Top Ø36 socket to angle return.
