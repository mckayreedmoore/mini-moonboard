"""Two inspectable MVP layouts: nominal geometry, never capacity approval.

Body contact is not a bonded joint. These checks deliberately do not qualify
threads, catalog hole patterns, assembly tools or the complete hardware fit.
"""
import math
from importlib import import_module
from itertools import combinations, product

import cadquery as cq
import pytest

from mini_moonboard import box_frame as b
from mini_moonboard.box_exports import exact_bounds, overlap
from mini_moonboard.panel_grid import (
    kicker_foothold_datums,
    main_led_datums,
    main_tnut_datums,
)

FACES = {f"main_{band}_{side}" for band, side in
         product(("lower", "upper"), ("left", "right"))} | {
             "kicker_left", "kicker_right"}


@pytest.fixture(scope="module", params=[
    ("wood_mvp", "wood-first-mvp"),
    ("bracket_mvp", "commercial-bracket-mvp"),
])
def candidate(request):
    module_name, key = request.param
    frame = import_module(f"mini_moonboard.{module_name}")
    assert frame.KEY == key
    values = frame.parts()
    parts = {p.name: p for p in values}
    assert len(parts) == len(values), "Duplicate part names hide bodies"
    return frame, parts


def test_inventory_validity_and_no_custom_steel(candidate):
    frame, parts = candidate
    assert FACES <= parts.keys()
    assert all(not name.startswith(("angle_", "transition_")) for name in parts)
    for name, part in parts.items():
        assert part.shape.isValid(), name
        assert len(part.shape.Solids()) == 1, name
        assert math.isfinite(part.shape.Volume()) and part.shape.Volume() > 0, name
        assert all(math.isfinite(v) and v > 0 for v in part.blank), name
        if "steel" in part.description.lower() or name.startswith("clip_"):
            assert frame.KEY == "commercial-bracket-mvp", name
            assert name.startswith("clip_mvp_") and "ML24Z" in part.description, name
    # Each module owns a separate candidate; neither replaces the earlier key.
    assert frame.__name__ == "mini_moonboard." + (
        "wood_mvp" if frame.KEY == "wood-first-mvp" else "bracket_mvp")


def test_purchased_face_thickness_and_fixed_backing_datums(candidate):
    frame, _ = candidate
    raw = {p.name: p for p in frame.parts(False)}
    origin = b.point(0, 0, 0)
    rear = cq.Vector(0, -math.cos(math.radians(40)), math.sin(math.radians(40)))
    for name in FACES:
        part = raw[name]
        assert part.blank[-1] == pytest.approx(18.25625), name
        if name.startswith("main_"):
            depths = [(v.Center()-origin).dot(rear) for v in part.shape.Vertices()]
            assert (min(depths), max(depths)) == pytest.approx((-18.25625, 0), abs=1e-6), name
            front = [f for f in part.shape.Faces() if f.geomType() == "PLANE"
                     and abs((f.Center()-origin).dot(rear)+18.25625) < 1e-6]
            assert len(front) == 1 and front[0].normalAt().dot(-rear) > 1-1e-7, name
        else:
            bounds = exact_bounds(part.shape)
            assert (bounds.ymin, bounds.ymax, bounds.zmin) == pytest.approx(
                (-36, -17.74375, 0), abs=1e-6), name


def test_all_official_hold_and_led_axes_remain_open(candidate):
    _, parts = candidate
    counts = {"hold": 0, "led": 0}
    for label, datums, diameter in (
            ("hold", main_tnut_datums(), 11.1125),
            ("led", main_led_datums(), 13.)):
        for u, s in datums.values():
            if s < 0:
                continue
            side = "left" if u < b.HALF else "right"
            band = "lower" if s < b.HALF else "upper"
            core = cq.Solid.makeCylinder(diameter/2-.1, 21,
                                        b.point(u-b.HALF, s, -20), b.normal())
            assert overlap(core, parts[f"main_{band}_{side}"].shape) < 1e-5, (label, u, s)
            counts[label] += 1
    for label, datums, diameter in (
            ("hold", kicker_foothold_datums(), 11.1125),
            ("led", {k: v for k, v in main_led_datums().items() if v[1] < 0}, 13.)):
        for u, s in datums.values():
            side = "left" if u < b.HALF else "right"
            core = cq.Solid.makeCylinder(diameter/2-.1, 21,
                cq.Vector(u-b.HALF, -37, b.V1_KICKER_HEIGHT_MM+s), cq.Vector(0, 1, 0))
            assert overlap(core, parts[f"kicker_{side}"].shape) < 1e-5, (label, u, s)
            counts[label] += 1
    assert counts == {"hold": 142, "led": 132}


def test_four_independent_legs_have_flat_floor_faces_and_connected_inventory(candidate):
    frame, parts = candidate
    legs = [p for p in parts.values() if p.name.startswith("leg_")]
    assert len(legs) == 4
    for part in legs:
        bounds = exact_bounds(part.shape)
        assert (bounds.zmin, bounds.xlen) == pytest.approx((0, 19.05), abs=1e-6), part.name
        assert part.laminations == 1, part.name
        floors = [f for f in part.shape.Faces()
                  if abs(exact_bounds(f).zmin) < 1e-6 and abs(exact_bounds(f).zmax) < 1e-6]
        assert floors and all(f.geomType() == "PLANE" for f in floors), part.name
        assert all(f.normalAt().z < -1+1e-7 for f in floors), part.name
        assert sum(f.Area() for f in floors) > 19.05*180, part.name
    connections = frame.connections()
    assert len({c.name for c in connections}) == len(connections) > 0
    adjacency = {name: set() for name in parts}
    for connection in connections:
        members = set(connection.members)
        assert len(members) == len(connection.members) >= 2, connection.name
        assert members <= parts.keys(), connection.name
        for name in members:
            adjacency[name].update(members-{name})
    reached, todo = set(), [legs[0].name]
    while todo:
        name = todo.pop()
        if name not in reached:
            reached.add(name)
            todo.extend(adjacency[name]-reached)
    assert reached == parts.keys(), sorted(parts.keys()-reached)


def test_body_housings_contact_without_unintended_penetration(candidate):
    _, parts = candidate
    bounds = {name: exact_bounds(p.shape) for name, p in parts.items()}
    contacts = set()
    collisions = []
    for (name, part), (other_name, other) in combinations(parts.items(), 2):
        a, z = bounds[name], bounds[other_name]
        if any(getattr(a, axis+"max") < getattr(z, axis+"min")-.02
               or getattr(z, axis+"max") < getattr(a, axis+"min")-.02
               for axis in "xyz"):
            continue
        volume = overlap(part.shape, other.shape)
        assert math.isfinite(volume), (name, other_name)
        if volume > .01:
            collisions.append((name, other_name, volume))
        distance = part.shape.distance(other.shape)
        assert math.isfinite(distance), (name, other_name)
        if distance <= .02:
            contacts.update((name, other_name))
    assert not collisions, collisions
    # No joint stiffness is inferred, and not every connected pair must touch.
    assert contacts == parts.keys(), sorted(parts.keys()-contacts)
