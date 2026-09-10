"""Current CAD mass accounting and finite load-family regression checks."""
from types import SimpleNamespace

import cadquery as cq
import pytest

from fea.selective_floor_screen import current_mass
from fea.timber_floor_screen import HOLDS, cases
from mini_moonboard.box_frame import Part


def test_mass_uses_current_drilled_parts_and_unions_overlapping_fastener_components():
    wood = cq.Solid.makeBox(100., 100., 100.).cut(
        cq.Solid.makeCylinder(5., 100., cq.Vector(50., 50., 0.)))
    clip = cq.Solid.makeBox(10., 10., 10., cq.Vector(100., 0., 10.))
    shaft = cq.Solid.makeCylinder(2., 20., cq.Vector(0., 0., 110.))
    head = cq.Solid.makeCylinder(4., 3., cq.Vector(0., 0., 110.))
    frame = SimpleNamespace(parts=lambda: (
        Part("main_panel", wood, (100., 100., 100.), "wood", 1),
        Part("clip_test", clip, (10., 10., 10.), "steel", 1)),
        connections=lambda: (SimpleNamespace(name="panel_screw", components=lambda: (shaft, head)),))
    state, inventory = current_mass(frame)
    steel = clip.Volume()+shaft.Volume()+head.Volume()-shaft.intersect(head).Volume()
    assert state["mass_kg"] == pytest.approx((wood.Volume()*600+steel*7850)/1e9)
    assert state["part_count"] == 3
    assert inventory[-1]["overlap_removed_mm3"] == pytest.approx(shaft.intersect(head).Volume())
    assert {tuple(p) for p in state["support_polygon_mm"]} == {
        (0., 0.), (100., 0.), (100., 100.), (0., 100.)}


def test_prescribed_floor_family_has_1296_cases_and_current_mass_gravity():
    state = {"mass_kg": 100., "centre_xyz_mm": [0., 0., 500.]}
    points = [(label, [0., 0., 1000.], [0., 1., 0.]) for label in HOLDS]
    rows = list(cases(state, points))
    assert len(rows) == 1296
    assert {row["mass_fraction"] for row in rows} == {.8, 1.}
    assert {row["horizontal_direction_deg"] for row in rows} == {None, *range(0, 360, 45)}
    first = rows[0]
    assert first["wrench_n_nmm"][2] == pytest.approx(-9.80665*(80.+150*.45359237))
