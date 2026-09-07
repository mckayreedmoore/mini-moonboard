"""MVP fastener placement, not capacity, tooling or actual product qualification.

Screw major-diameter overlap with declared receivers is intentional thread
engagement. No head/washer/nut or unrelated-member overlap is exempted.
"""
import math
from itertools import combinations

import cadquery as cq
import pytest
import test_redesign_mvp as layouts

from mini_moonboard import box_frame as b
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.connection_geometry import material_intervals
from mini_moonboard.panel_grid import (
    kicker_foothold_datums,
    main_led_datums,
    main_tnut_datums,
)

THRESHOLD_MM3 = .01
candidate = layouts.candidate


def positive_overlap(a, b, bounds):
    for shape in (a, b):
        if id(shape) not in bounds:
            bounds[id(shape)] = exact_bounds(shape)
    aa, bb = bounds[id(a)], bounds[id(b)]
    if any(min(getattr(aa, axis+"max"), getattr(bb, axis+"max"))
           - max(getattr(aa, axis+"min"), getattr(bb, axis+"min")) <= 1e-7 for axis in "xyz"):
        return 0.
    volume = a.intersect(b).Volume()
    assert math.isfinite(volume) and volume >= 0
    return volume


def test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies(candidate):
    frame, parts = candidate
    connections = frame.connections()
    # Retain shapes for the whole check so cached object IDs cannot be reused.
    components = {c.name: c.components() for c in connections}
    assert len(components) == len(connections), "Duplicate fastener identifiers"
    bounds, findings = {}, []
    for c in connections:
        shapes = components[c.name]
        roles = ("shaft", "head_washer", "nut_washer", "head", "nut") if c.kind == "bolt" else ("shaft", "head")
        assert len(shapes) == len(roles), c.name
        assert set(c.members) <= parts.keys(), c.name
        for role, shape in zip(roles, shapes, strict=True):
            assert shape.isValid(), (c.name, role)
            for name, part in parts.items():
                if role == "shaft" and c.kind == "screw" and name in c.members:
                    continue  # Only declared screw-thread/material engagement.
                volume = positive_overlap(shape, part.shape, bounds)
                if volume > THRESHOLD_MM3:
                    findings.append((c.name, role, name, volume))
    assert findings == [], findings


def test_axes_have_real_receivers_and_open_pilot_paths(candidate):
    frame, parts = candidate
    raw = {p.name: p for p in frame.parts(False)}
    findings = []
    for c in frame.connections():
        assert math.isfinite(c.length) and c.length > 0, c.name
        assert c.direction.Length == pytest.approx(1.), c.name
        assert len(c.members) == len(set(c.members)) >= 2, c.name
        # A centerline pilot probe is independent of intentional thread overlap.
        core = cq.Solid.makeCylinder(.25, c.length, c.start, c.direction)
        for name in c.members:
            volume = core.intersect(parts[name].shape).Volume()
            assert math.isfinite(volume), (c.name, name)
            if volume > THRESHOLD_MM3:
                findings.append((c.name, name, "blocked axis", volume))
            if name.startswith("clip_mvp_"):
                # Purchased-connector proxy holes exist even in parts(False).
                # Require surrounding material, not an impossible filled axis.
                witness = cq.Solid.makeCylinder(c.diameter/2+1.5, c.length, c.start, c.direction)
                material = witness.intersect(raw[name].shape).Volume()
                assert math.isfinite(material), (c.name, name)
                if material <= 1.:
                    findings.append((c.name, name, "missing connector material", material))
            else:
                intervals = material_intervals(raw[name].shape, c.start, c.direction, 0., c.length)
                if not intervals:
                    findings.append((c.name, name, "axis never enters raw net receiver"))
    assert findings == [], findings


def test_broadphase_does_not_hide_contained_hardware_overlap():
    body = cq.Solid.makeBox(10, 10, 10)
    contained = cq.Solid.makeCylinder(1, 3, cq.Vector(5, 5, 2))
    outside = contained.translate((20, 0, 0))
    assert positive_overlap(body, contained, {}) == pytest.approx(contained.Volume())
    assert positive_overlap(body, outside, {}) == 0


def test_distinct_fastener_components_do_not_intersect(candidate):
    frame, _ = candidate
    # Keep all component objects alive while the bounds cache uses their IDs.
    components = {c.name: c.components() for c in frame.connections()}
    bounds, findings = {}, []
    for (name, shapes), (other_name, other_shapes) in combinations(components.items(), 2):
        # Only a fastener's own internal component overlaps are excluded.
        for index, shape in enumerate(shapes):
            for other_index, other_shape in enumerate(other_shapes):
                volume = positive_overlap(shape, other_shape, bounds)
                if volume > THRESHOLD_MM3:
                    findings.append((name, index, other_name, other_index, volume))
    assert findings == [], findings


def test_rear_hold_flanges_and_led_reservations_clear_nonface_parts(candidate):
    frame, parts = candidate
    envelopes = []
    for label, (u, s) in main_tnut_datums().items():
        envelopes.append(("hold "+label, cq.Solid.makeCylinder(12.7, 1.86,
            b.point(u-b.HALF, s, 0), b.normal())))
    for label, (u, s) in kicker_foothold_datums().items():
        envelopes.append(("kicker hold "+label, cq.Solid.makeCylinder(12.7, 1.86,
            cq.Vector(u-b.HALF, -36, b.V1_KICKER_HEIGHT_MM+s), cq.Vector(0, -1, 0))))
    for label, (u, s) in main_led_datums().items():
        start, direction = (b.point(u-b.HALF, s, 0), b.normal()) if s >= 0 else (
            cq.Vector(u-b.HALF, -36, b.V1_KICKER_HEIGHT_MM+s), cq.Vector(0, -1, 0))
        # Conservative Ø13 x31 rear reservation: actual reported max body Ø12.7;
        # full 31 mm rear projection is an allowance, not installed geometry.
        envelopes.append(("LED "+label, cq.Solid.makeCylinder(6.5, 31, start, direction)))
    assert len(envelopes) == 142+132
    bounds, findings = {}, []
    for name, part in parts.items():
        if name in layouts.FACES:
            continue  # These reservations begin at the fixed rear face planes.
        for label, envelope in envelopes:
            volume = positive_overlap(part.shape, envelope, bounds)
            if volume > THRESHOLD_MM3:
                findings.append((name, label, volume))
    # Hardware can obstruct a light or insert even when its receiving timber
    # clears the reservation. Retain every shape while caching bounds by ID.
    components = {c.name: c.components() for c in frame.connections()}
    for name, shapes in components.items():
        for index, shape in enumerate(shapes):
            for label, envelope in envelopes:
                volume = positive_overlap(shape, envelope, bounds)
                if volume > THRESHOLD_MM3:
                    findings.append((name, index, label, volume))
    assert findings == [], findings
