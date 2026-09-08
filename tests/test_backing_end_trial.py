import cadquery as cq
import pytest
from test_mvp_fasteners import positive_overlap

from mini_moonboard import backing_end_trial as trial
from mini_moonboard import box_frame as b
from mini_moonboard import wide_frame as frame
from mini_moonboard.connection_geometry import material_intervals


def test_eight_proposed_factory_axes_have_full_nominal_receiver_penetration():
    raw = {p.name: p for p in frame.wood_parts(True)}
    screws = list(trial.screws())
    assert len({c.name for c in screws}) == 8
    for c in screws:
        receiver = raw[c.members[1]].shape
        intervals = material_intervals(receiver, c.start, c.direction, 0., c.length)
        assert len(intervals) == 1
        assert intervals[0] == pytest.approx((trial.REFERENCE["thickness_mm"], 38.1), abs=1e-6)
        # Actual shaft, not only its axis, must remain in the designated wood.
        start = c.start+c.direction*trial.REFERENCE["thickness_mm"]
        shaft = cq.Solid.makeCylinder(3.175, 38.1-trial.REFERENCE["thickness_mm"], start, c.direction)
        assert shaft.cut(receiver).Volume() < .01, c.name
    assert len(frame.connections()) == 188  # Trial is not silently installed.


def test_backing_edge_layout_is_from_ml23_not_scaled_ml24():
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    values = []
    for c in trial.screws():
        if c.members[1] == "timber_bottom_backing":
            s = (c.start-b.point(0, 0, 0)).dot(tangent)
            values.append(min(s, 88.9-s))
    assert values == pytest.approx([22.225]*4)
    assert trial.REFERENCE["width_mm"] == 76.2


def test_nominal_bracket_volume_bends_chamfers_and_holes():
    import math
    r = trial.REFERENCE
    t, reach, width = r["thickness_mm"], r["outside_reach_mm"], r["width_mm"]
    outer, inner = r["outside_bend_radius_mm"], r["inside_bend_radius_mm"]
    expected = (2*t*(reach-outer)+math.pi*(outer**2-inner**2)/4)*width
    expected -= 4*r["outer_corner_chamfer_mm"]**2*t/2
    expected -= 4*math.pi*(r["hole_diameter_mm"]/2)**2*t
    parts = list(trial.brackets())
    assert len(parts) == 2
    for p in parts:
        assert p.shape.isValid() and len(p.shape.Solids()) == 1
        assert p.shape.Volume() == pytest.approx(expected, abs=.001)


def test_complete_trial_hardware_records_rejected_collision():
    current = {p.name: p.shape for p in frame.parts()}
    brackets = {p.name: p.shape for p in trial.brackets()}
    existing = {c.name: c.components() for c in frame.connections()}
    screws = {c.name: c for c in trial.screws()}
    added = {name: c.components() for name, c in screws.items()}
    bounds, findings = {}, []
    for name, bracket in brackets.items():
        for other, shape in current.items():
            if positive_overlap(bracket, shape, bounds) > .01:
                findings.append((name, other))
        for other, shapes in existing.items():
            if any(positive_overlap(bracket, shape, bounds) > .01 for shape in shapes):
                findings.append((name, other))
    for name, shapes in added.items():
        for index, shape in enumerate(shapes):
            for other, body in {**current, **brackets}.items():
                if index == 0 and other == screws[name].members[1]:
                    continue  # Only intended shaft-to-wood engagement is exempt.
                if positive_overlap(shape, body, bounds) > .01:
                    findings.append((name, index, other))
            for other, components in {**existing, **added}.items():
                if other == name:
                    continue
                if any(positive_overlap(shape, part, bounds) > .01 for part in components):
                    findings.append((name, index, other))
    # This trial is rejected, not installed. Preserve the discovered interference
    # instead of exempting the base bolts or calling shaft-only fit a full pass.
    assert set(findings) == {
        ("trial_ml23_left", "timber_base_left_1"),
        ("trial_ml23_right", "timber_base_right_1"),
        ("trial_end_left_rim_2", 0, "timber_base_left_1"),
        ("trial_end_left_rim_2", 1, "timber_base_left_1"),
        ("trial_end_right_rim_1", 0, "timber_base_right_1"),
        ("trial_end_right_rim_1", 1, "timber_base_right_1"),
    }


def test_sliding_to_either_full_width_fit_limit_does_not_clear_base_bolts():
    tangent = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
    bolts = {c.name: c.components() for c in frame.connections() if c.name in (
        "timber_base_left_1", "timber_base_right_1")}
    for p in trial.brackets():
        side = "left" if p.name.endswith("left") else "right"
        for offset in (-6.35, 6.35):
            shape = p.shape.translate(tangent*offset)
            assert any(shape.intersect(c).Volume() > .01 for c in bolts[f"timber_base_{side}_1"])
