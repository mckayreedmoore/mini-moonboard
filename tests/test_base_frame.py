"""Inset base concept: corrected bores and finite bearing, not strength approval."""
import math

import cadquery as cq
import pytest
import test_redesign_mvp as layouts

from mini_moonboard import base_frame as frame
from mini_moonboard import box_frame as b
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard import product_frame as product
from mini_moonboard.box_exports import exact_bounds


@pytest.fixture(scope="module")
def candidate():
    values = frame.parts()
    parts = {p.name: p for p in values}
    assert len(parts) == len(values)
    assert frame.KEY == "base-bearing-concept"
    return frame, parts


test_all_bodies_touch_without_penetrating = layouts.test_body_housings_contact_without_unintended_penetration


def test_no_inherited_connections_or_hardware_in_geometry_concept(candidate):
    model, parts = candidate
    assert model.connections() == ()
    assert not any(name.startswith(("clip_", "fastener_", "wood_", "cheek_")) for name in parts)
    assert layouts.FACES <= parts.keys()
    assert all(part.shape.isValid() and len(part.shape.Solids()) == 1 for part in parts.values())
    assert all("NOT build-ready" in part.description for part in parts.values())
    # Only the faces are drilled; old connection pilots must not survive.
    raw = {p.name: p for p in model.parts(False)}
    for name, part in parts.items():
        if name not in layouts.FACES:
            assert part.shape.Volume() == pytest.approx(raw[name].shape.Volume(), abs=1e-5), name


def test_side_framing_is_inset_and_behind_climbing_faces(candidate):
    _, parts = candidate
    origin, normal = b.point(0, 0, 0), b.normal()
    for side in ("left", "right"):
        rim = parts["base_side_"+side]
        bounds = exact_bounds(rim.shape)
        expected = (-b.HALF, -b.HALF+38.1) if side == "left" else (b.HALF-38.1, b.HALF)
        assert (bounds.xmin, bounds.xmax) == pytest.approx(expected)
        normal_positions = [(v.Center()-origin).dot(normal) for v in rim.shape.Vertices()]
        assert min(normal_positions) == pytest.approx(0., abs=1e-6)
        assert max(normal_positions) == pytest.approx(177.8, abs=1e-6)
        for band in ("lower", "upper"):
            face = parts[f"main_{band}_{side}"].shape
            positions = [(v.Center()-origin).dot(normal) for v in face.Vertices()]
            assert min(positions) == pytest.approx(-18.25625, abs=1e-6)
            assert max(positions) == pytest.approx(0., abs=1e-6)
            assert rim.shape.intersect(face).Volume() < 1e-5


def test_level_header_supports_full_four_member_end_areas(candidate):
    _, parts = candidate
    header = parts["base_header"].shape
    bounds = exact_bounds(header)
    assert (bounds.zmin, bounds.zmax) == pytest.approx((186.9, 225.))
    for name, depth in (("base_side_left", 177.8), ("base_side_right", 177.8),
                        ("base_principal_left", 139.7), ("base_principal_right", 139.7)):
        member = parts[name].shape
        assert exact_bounds(member).zmin == pytest.approx(225.)
        end_faces = [face for face in member.Faces() if
                     abs(exact_bounds(face).zmin-225.) < 1e-6 and
                     abs(exact_bounds(face).zmax-225.) < 1e-6]
        area = 38.1*depth/math.cos(math.radians(40.))
        assert end_faces and all(face.geomType() == "PLANE" for face in end_faces), name
        assert sum(face.Area() for face in end_faces) == pytest.approx(area, rel=1e-7), name
        assert all(face.normalAt().z < -1+1e-7 for face in end_faces), name
        bearing_area = member.translate((0., 0., -.001)).intersect(header).Volume()/.001
        assert bearing_area == pytest.approx(area, rel=1e-5), name
        assert member.intersect(header).Volume() < 1e-5, name


def test_posts_and_independent_legs_have_flat_floor_faces(candidate):
    _, parts = candidate
    header = parts["base_header"].shape
    posts = [p for name, p in parts.items() if name.startswith("base_post_")]
    legs = [p for name, p in parts.items() if name.startswith("leg_")]
    assert len(posts) == len(legs) == 4
    for post in posts:
        bounds = exact_bounds(post.shape)
        assert (bounds.xlen, bounds.ylen, bounds.zlen, bounds.zmin) == pytest.approx((38.1, 88.9, 186.9, 0.))
        faces = [f for f in post.shape.Faces() if abs(exact_bounds(f).zmin) < 1e-6 and abs(exact_bounds(f).zmax) < 1e-6]
        assert sum(f.Area() for f in faces) == pytest.approx(38.1*88.9), post.name
        assert all(f.normalAt().z < -1+1e-7 for f in faces), post.name
        assert post.shape.translate((0., 0., .001)).intersect(header).Volume()/.001 == pytest.approx(38.1*88.9, rel=1e-5)
    for leg in legs:
        bounds = exact_bounds(leg.shape)
        assert (bounds.zmin, bounds.xlen) == pytest.approx((0., 19.05), abs=1e-6), leg.name
        assert leg.laminations == 1, leg.name
        faces = [f for f in leg.shape.Faces() if abs(exact_bounds(f).zmin) < 1e-6 and abs(exact_bounds(f).zmax) < 1e-6]
        assert faces and all(f.geomType() == "PLANE" and f.normalAt().z < -1+1e-7 for f in faces), leg.name
        assert sum(f.Area() for f in faces) > 19.05*180, leg.name


def test_corrected_grid_is_drilled_at_explicit_panel_edge_datums(candidate):
    model, parts = candidate
    raw = {p.name: p for p in model.parts(False)}
    tnut_rows = (99.2, 299.2, 499.2, 699.2, 899.2, 1099.2,
                 1319.2, 1519.2, 1719.2, 1919.2, 2119.2, 2319.2)
    led_rows = (19.2, 199.2, 399.2, 599.2, 799.2, 999.2,
                1199.2, 1419.2, 1619.2, 1819.2, 2019.2, 2219.2)
    counts = {}
    removed = dict.fromkeys(layouts.FACES, 0.)
    for label, datums, rows, diameter in (("tnut", grid.main_tnut_datums(), tnut_rows, 11.1125),
                                         ("led", grid.main_led_datums(), led_rows, 13.)):
        assert len(datums) == 132
        counts[label] = 0
        for index, column in enumerate("ABCDEFGHIJK", 1):
            for row, s in enumerate(rows, 1):
                x = index*200.
                assert datums[f"{column}{row}"] == pytest.approx((x, s))
                band = "lower" if s < 1219.2 else "upper"
                side = "left" if x < 1219.2 else "right"
                name = f"main_{band}_{side}"
                probe = cq.Solid.makeCylinder(diameter/2-.01, 20.25625,
                    b.point(x-1219.2, s, -19.25625), b.normal())
                assert probe.intersect(parts[name].shape).Volume() < 1e-5, (label, column, row)
                removed[name] += math.pi*(diameter/2)**2*18.25625
                counts[label] += 1
    assert counts == {"tnut": 132, "led": 132}
    kicker = grid.kicker_foothold_datums()
    assert len(kicker) == 10
    for x, z in kicker.values():
        name = "kicker_left" if x < 1219.2 else "kicker_right"
        probe = cq.Solid.makeCylinder(11.1125/2-.01, 20.25625,
            cq.Vector(x-1219.2, product.KICKER_BACK_Y_MM-1, 225.+z), cq.Vector(0, 1, 0))
        assert probe.intersect(parts[name].shape).Volume() < 1e-5, name
        removed[name] += math.pi*(11.1125/2)**2*18.25625
    # Exact removed volume rejects extra old pilot holes or main LEDs in kicker.
    for name in layouts.FACES:
        assert raw[name].shape.Volume()-parts[name].shape.Volume() == pytest.approx(removed[name], abs=1e-4), name
    assert min(s for _, s in grid.main_led_datums().values()) == pytest.approx(19.2)
    assert grid.main_tnut_datums()["A7"][1]-grid.main_tnut_datums()["A6"][1] == pytest.approx(220.)
