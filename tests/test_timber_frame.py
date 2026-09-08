"""Lumber-base fit and access checks, not connection or structural approval."""
import math
from itertools import pairwise

import cadquery as cq
import pytest
import test_mvp_fasteners as hardware
import test_redesign_mvp as layouts

from mini_moonboard import base_frame as base
from mini_moonboard import box_frame as b
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard import product_frame as product
from mini_moonboard import timber_frame as frame
from mini_moonboard.box_exports import exact_bounds
from mini_moonboard.connection_geometry import material_intervals


@pytest.fixture(scope="module")
def candidate():
    values = frame.parts()
    parts = {p.name: p for p in values}
    assert len(parts) == len(values)
    assert frame.KEY == "timber-base-development"
    return frame, parts


test_body_contacts_and_collisions = layouts.test_body_housings_contact_without_unintended_penetration
test_heads_washers_and_unrelated_shafts = hardware.test_heads_washers_nuts_and_unrelated_shafts_clear_all_bodies
test_hardware_pair_clearance = hardware.test_distinct_fastener_components_do_not_intersect


def test_real_receivers_and_open_pilots(candidate):
    model, parts = candidate
    raw = {p.name: p for p in model.parts(False)}
    for c in model.connections():
        assert math.isfinite(c.length) and c.length > 0, c.name
        assert c.direction.Length == pytest.approx(1.), c.name
        assert len(c.members) == len(set(c.members)) >= 2, c.name
        core = cq.Solid.makeCylinder(.25, c.length, c.start, c.direction)
        for name in c.members:
            volume = core.intersect(parts[name].shape).Volume()
            assert math.isfinite(volume) and volume < hardware.THRESHOLD_MM3, (c.name, name, volume)
            if name.startswith("clip_timber_"):
                # Factory holes also exist in undrilled purchased connectors.
                witness = cq.Solid.makeCylinder(c.diameter/2+1.5, c.length, c.start, c.direction)
                material = witness.intersect(raw[name].shape).Volume()
                assert math.isfinite(material) and material > 1., (c.name, name, material)
            else:
                assert material_intervals(raw[name].shape, c.start, c.direction, 0., c.length), (c.name, name)


def test_connection_inventory(candidate):
    model, parts = candidate
    connections = model.connections()
    assert len(connections) == len({c.name for c in connections}) == 176
    clips = {name for name in parts if name.startswith("clip_timber_")}
    assert len(clips) == 16
    for prefix, count in (("clip_timber_", 96), ("analysis_leg_wall_bolt_", 8),
                          ("leg_stitch_", 6), ("timber_panel_", 48),
                          ("timber_kicker_", 8), ("timber_backing_bolt_", 2),
                          ("timber_base_", 8)):
        assert sum(c.name.startswith(prefix) for c in connections) == count, prefix
    for clip in clips:
        assert sum(c.members[0] == clip for c in connections) == 6, clip
    for band in ("lower", "upper"):
        for side in ("left", "right"):
            assert sum(c.name.startswith(f"timber_panel_{band}_{side}_") for c in connections) == 12


def test_panel_corner_and_kicker_receiver_end_distances(candidate):
    model, parts = candidate
    kicker = [c for c in model.connections() if c.name.startswith("timber_kicker_")]
    assert len(kicker) == 8
    assert {c.start.z for c in kicker} == {60., 140.}
    for c in kicker:
        bounds = exact_bounds(parts[c.members[1]].shape)
        # Post grain is world-vertical; assess both actual receiver ends.
        assert min(c.start.z-bounds.zmin, bounds.zmax-c.start.z) >= 44.45-1e-6, c.name
    origin = b.point(0, 0, 0)
    uphill = (b.point(0, 1, 0)-origin).normalized()
    corners = [c for c in model.connections()
               if c.name.startswith("timber_panel_upper_")
               and c.members[1].startswith("base_principal_")
               and (c.start-origin).dot(uphill) > b.LENGTH-200.]
    assert len(corners) == 2
    for c in corners:
        station = (c.start-origin).dot(uphill)
        assert b.LENGTH-station == pytest.approx(100.)
        receiver_end = max((v.Center()-origin).dot(uphill)
                           for v in parts[c.members[1]].shape.Vertices())
        assert receiver_end-station == pytest.approx(61.9, abs=1e-6)
        assert receiver_end-station >= 44.45


def test_base_and_recessed_backing_bolt_net_grips(candidate):
    model, parts = candidate
    raw = {p.name: p for p in model.parts(False)}
    bolts = [c for c in model.connections() if c.name.startswith(("timber_base_", "timber_backing_bolt_"))]
    assert len(bolts) == 10
    for c in bolts:
        backing = c.name.startswith("timber_backing_bolt_")
        assert c.kind == "bolt" and c.diameter == pytest.approx(9.525)
        assert c.length == pytest.approx(152.4 if backing else 76.2)
        runs = [material_intervals(raw[name].shape, c.start, c.direction, 0., c.length) for name in c.members]
        assert all(len(run) == 1 for run in runs), c.name
        ordered = sorted(run[0] for run in runs)
        if backing:
            # Undrilled stock includes the counterbore. Its seat is N=12.032,
            # independent of declared grip; measure retained wood from there.
            assert (c.start-b.point(0, 0, 0)).dot(b.normal()) == pytest.approx(10.)
            assert ordered[0][0] == pytest.approx(0., abs=1e-6)
            ordered[0] = (2.032, ordered[0][1])
            pocket = cq.Solid.makeCylinder(28.575/2-.01, 12.032,
                c.start-b.normal()*10., b.normal())
            assert parts["timber_bottom_backing"].shape.intersect(pocket).Volume() < 1e-5
        assert ordered[0][0] == pytest.approx(2.032, abs=1e-6), c.name
        assert sum(end-start for start, end in ordered) == pytest.approx(c.grip), c.name
        assert c.grip == pytest.approx(127.668 if backing else 57.15)
        for previous, following in pairwise(ordered):
            assert previous[1] == pytest.approx(following[0], abs=1e-6), c.name


def test_one_piece_lumber_sides_fit_ten_foot_stock(candidate):
    _, parts = candidate
    origin, normal = b.point(0, 0, 0), b.normal()
    for side in ("left", "right"):
        part = parts["base_side_"+side]
        assert part.laminations == 1
        assert part.blank[1:] == pytest.approx((184.15, 38.1))
        assert 2438.4 < part.blank[0] < 3048.
        assert "2x8" in part.description and "10 ft" in part.description
        bounds = exact_bounds(part.shape)
        expected = (-1219.2, -1181.1) if side == "left" else (1181.1, 1219.2)
        assert (bounds.xmin, bounds.xmax) == pytest.approx(expected)
        depths = [(v.Center()-origin).dot(normal) for v in part.shape.Vertices()]
        assert min(depths) == pytest.approx(0., abs=1e-6)
        assert max(depths) == pytest.approx(184.15, abs=1e-6)


def test_bottom_backing_housing_and_remaining_principal_sections(candidate):
    model, parts = candidate
    raw = {p.name: p for p in model.parts(False)}
    rail = raw["timber_bottom_backing"]
    assert rail.blank == pytest.approx((2362.2, 88.9, 38.1))
    assert rail.shape.Volume() == pytest.approx(2362.2*88.9*38.1)
    for side, (x0, x1) in base.UPRIGHTS.items():
        principal = parts["base_principal_"+side].shape
        assert principal.isValid() and len(principal.Solids()) == 1
        assert principal.intersect(parts[rail.name].shape).Volume() < 1e-5
        assert principal.distance(parts[rail.name].shape) < 1e-6
        # Check rear stock beyond the 45 mm service pockets at a station within
        # the housing. Do not claim full front bearing where LED1 cuts through.
        witness = b.block(x0+.1, x1-.1, 50., 60., 45.1, 139.6)
        assert principal.intersect(witness).Volume() == pytest.approx(witness.Volume(), abs=1e-5)


def test_posts_cover_header_depth_and_four_slope_ends_bear(candidate):
    _, parts = candidate
    header = parts["base_header"].shape
    hb = exact_bounds(header)
    posts = [p for name, p in parts.items() if name.startswith("base_post_")]
    assert len(posts) == 4
    for part in posts:
        bounds = exact_bounds(part.shape)
        assert (bounds.ymin, bounds.ymax) == pytest.approx((hb.ymin, hb.ymax))
        assert (bounds.xlen, bounds.ylen, bounds.zmin, bounds.zmax) == pytest.approx((38.1, 285.75, 0., 186.9))
        area = 38.1*285.75
        assert part.shape.translate((0, 0, .001)).intersect(header).Volume()/.001 == pytest.approx(area, rel=1e-5)
        floors = [face for face in part.shape.Faces() if abs(exact_bounds(face).zmin) < 1e-6 and abs(exact_bounds(face).zmax) < 1e-6]
        assert sum(face.Area() for face in floors) == pytest.approx(area)
        assert all(face.normalAt().z < -1+1e-7 for face in floors)
    for name, depth in (("base_side_left", 184.15), ("base_side_right", 184.15),
                        ("base_principal_left", 139.7), ("base_principal_right", 139.7)):
        shape = parts[name].shape
        assert exact_bounds(shape).zmin == pytest.approx(225.)
        assert shape.translate((0, 0, -.001)).intersect(header).Volume()/.001 == pytest.approx(
            38.1*depth/math.cos(math.radians(40)), rel=1e-5), name


def test_corrected_main_and_kicker_axes_remain_open(candidate):
    _, parts = candidate
    counts = {"tnut": 0, "led": 0, "kicker": 0}
    assert grid.main_tnut_datums()["A1"][1] == pytest.approx(99.2)
    assert grid.main_tnut_datums()["A7"][1]-grid.main_tnut_datums()["A6"][1] == pytest.approx(220.)
    assert grid.main_led_datums()["A1"][1] == pytest.approx(19.2)
    assert grid.main_led_datums()["A7"][1] == pytest.approx(1199.2)
    for label, datums, diameter in (("tnut", grid.main_tnut_datums(), 11.1125),
                                    ("led", grid.main_led_datums(), 13.)):
        for x, s in datums.values():
            assert s >= 0, "No main-grid LEDs in the kicker"
            name = f"main_{'lower' if s < b.HALF else 'upper'}_{'left' if x < b.HALF else 'right'}"
            probe = cq.Solid.makeCylinder(diameter/2-.01, 20.25625,
                b.point(x-b.HALF, s, -19.25625), b.normal())
            assert parts[name].shape.intersect(probe).Volume() < 1e-5, (name, label, x, s)
            counts[label] += 1
    for x, z in grid.kicker_foothold_datums().values():
        name = "kicker_left" if x < b.HALF else "kicker_right"
        probe = cq.Solid.makeCylinder(11.1125/2-.01, 20.25625,
            cq.Vector(x-b.HALF, product.KICKER_BACK_Y_MM-1, 225.+z), cq.Vector(0, 1, 0))
        assert parts[name].shape.intersect(probe).Volume() < 1e-5, name
        counts["kicker"] += 1
    assert counts == {"tnut": 132, "led": 132, "kicker": 10}


def test_all_corrected_service_reservations_clear_wood_and_hardware(candidate):
    model, parts = candidate
    envelopes = [(f"{kind}_{label}", cq.Solid.makeCylinder(20., 45.,
        b.point(x-b.HALF, s, 0), b.normal()))
        for kind, datums in (("hold", grid.main_tnut_datums()), ("led", grid.main_led_datums()))
        for label, (x, s) in datums.items()]
    envelopes += [("kicker_"+label, cq.Solid.makeCylinder(12.7, 1.86,
        cq.Vector(x-b.HALF, product.KICKER_BACK_Y_MM, 225.+z), cq.Vector(0, -1, 0)))
        for label, (x, z) in grid.kicker_foothold_datums().items()]
    assert len(envelopes) == 274
    objects = [(name, p.shape) for name, p in parts.items() if name not in layouts.FACES]
    objects += [(c.name+f"_{i}", shape) for c in model.connections()
                for i, shape in enumerate(c.components())]
    bounds, findings = {}, []
    for name, shape in objects:
        for label, envelope in envelopes:
            volume = hardware.positive_overlap(shape, envelope, bounds)
            if volume > hardware.THRESHOLD_MM3:
                findings.append((name, label, volume))
    assert not findings, findings


def test_resized_leg_bolts_cross_actual_three_member_grips(candidate):
    model, _ = candidate
    raw = {p.name: p for p in model.parts(False)}
    bolts = [c for c in model.connections() if c.name.startswith(("analysis_leg_wall_bolt_", "leg_stitch_"))]
    assert len(bolts) == 14
    assert sum(c.name.startswith("analysis_leg_wall_bolt_") for c in bolts) == 8
    for c in bolts:
        wall = c.name.startswith("analysis_leg_wall_bolt_")
        assert c.kind == "bolt" and c.diameter == pytest.approx(9.525), c.name
        assert c.length == pytest.approx(95.25 if wall else 63.5), c.name
        assert c.grip == pytest.approx(76.2 if wall else 38.1), c.name
        assert len(c.members) == (3 if wall else 2), c.name
        runs = [material_intervals(raw[name].shape, c.start, c.direction, 0., c.length) for name in c.members]
        assert all(len(run) == 1 for run in runs), c.name
        ordered = sorted(run[0] for run in runs)
        assert ordered[0][0] == pytest.approx(2.032, abs=1e-6), c.name
        assert sum(end-start for start, end in ordered) == pytest.approx(c.grip), c.name
        for index in range(len(ordered)-1):
            assert ordered[index][1] == pytest.approx(ordered[index+1][0], abs=1e-6), c.name
