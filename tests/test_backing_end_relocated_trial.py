import cadquery as cq
import pytest
from test_mvp_fasteners import positive_overlap

from mini_moonboard import backing_end_relocated_trial as trial
from mini_moonboard import backing_end_trial as end
from mini_moonboard import box_frame as b
from mini_moonboard import wide_frame as frame
from mini_moonboard.connection_geometry import material_intervals


def test_only_two_existing_bolt_axes_move_and_receivers_remain_full():
    old = {c.name: c for c in frame.connections()}
    raw = {p.name: p.shape for p in frame.wood_parts(True)}
    new = {c.name: c for c in trial.connections()}
    assert len(new) == 196
    for name, original in old.items():
        c = new[name]
        if name not in trial.MOVED:
            assert c == original
            continue
        assert (c.start-original.start-b.normal()*45).Length < 1e-8
        assert (c.length, c.grip, c.members, c.direction) == (original.length, original.grip, original.members, original.direction)
        for member in c.members:
            intervals = material_intervals(raw[member], c.start, c.direction, 0., c.length)
            assert len(intervals) == 1
            expected = 38.1 if member.startswith("base_side") else 19.05
            assert intervals[0][1]-intervals[0][0] == pytest.approx(expected)
            bore = cq.Solid.makeCylinder(11.1125/2, expected,
                c.start+c.direction*intervals[0][0], c.direction)
            assert bore.cut(raw[member]).Volume() < .01
    for side in ("left", "right"):
        a, z = new[f"timber_base_{side}_1"], new[f"timber_base_{side}_2"]
        assert (a.start-z.start).Length > 60


def test_relocated_and_added_hardware_clears_wood_and_other_hardware():
    # Existing holes are not treated as a proposed manufacturing layout. Raw
    # receiver checks above verify new axes; fresh drilling/export remains open.
    wood = {p.name: p.shape for p in frame.wood_parts(True)}
    bodies = {p.name: p.shape for p in frame.parts() if p.name not in wood}
    brackets = {p.name: p.shape for p in end.brackets()}
    bodies.update(brackets)
    bodies.update(wood)
    connections = {c.name: c for c in trial.connections()}
    components = {name: c.components() for name, c in connections.items()}
    bounds, findings = {}, []
    for name, bracket in brackets.items():
        for other, body in bodies.items():
            if other != name and positive_overlap(bracket, body, bounds) > .01:
                findings.append((name, other))
        for other, shapes in components.items():
            if any(positive_overlap(bracket, shape, bounds) > .01 for shape in shapes):
                findings.append((name, other))
    changed = [c for c in connections.values() if c.name in trial.MOVED or c.name.startswith("trial_end_")]
    for c in changed:
        for i, shape in enumerate(components[c.name]):
            for other, body in bodies.items():
                if other in c.members and other in wood:
                    if i == 0:
                        continue  # Proposed bore/thread engagement, not head exemption.
                    if c.kind == "bolt" and i in (1, 2):
                        # Washer envelopes include a 2.032mm bearing offset in
                        # the nominal start convention; evaluate on bored wood.
                        body = body.cut(cq.Solid.makeCylinder(11.1125/2, c.length+2,
                            c.start-c.direction, c.direction))
                if positive_overlap(shape, body, bounds) > .01:
                    findings.append((c.name, i, other))
            for other, shapes in components.items():
                if other != c.name and any(positive_overlap(shape, s, bounds) > .01 for s in shapes):
                    findings.append((c.name, i, other))
    assert findings == [], findings
