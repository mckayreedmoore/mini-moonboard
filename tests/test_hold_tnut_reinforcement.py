"""Check current hole mapping and rear-flange/front-barrel orientation."""
import math

import cadquery as cq
import pytest

from mini_moonboard import hold_tnut_reinforcement as nuts
from mini_moonboard import panel_grid_v2 as grid
from mini_moonboard import round_structural_frame as model


def test_local_steel_shape_has_measured_flange_and_three_retention_holes():
    shape = nuts.local_shape()
    assert shape.isValid() and len(shape.Solids()) == 1
    bounds = shape.BoundingBox()
    assert bounds.zmin == pytest.approx(-1.86)
    assert bounds.zmax == pytest.approx(12.7)
    expected = (math.pi*(12.7**2-4.**2)*1.86
                +math.pi*(5.5**2-4.**2)*12.7-3*math.pi*1.6**2*1.86)
    assert shape.Volume() == pytest.approx(expected, rel=1.e-8)
    centers = nuts.retention_hole_centers()
    for a, b in zip(centers, (*centers[1:], centers[0]), strict=True):
        assert math.dist(a, b) == pytest.approx(15.98)


def test_142_unique_datums_match_current_grid_without_old_row_offsets():
    rows = nuts.datums(model)
    assert len(rows) == len({r['name'] for r in rows}) == 142
    assert sum(r['panel'].startswith('main_') for r in rows) == 132
    assert sum(r['panel'].startswith('kicker_') for r in rows) == 10
    main = {r['label']: r for r in rows if r['panel'].startswith('main_')}
    for label, (x, s) in grid.main_tnut_datums().items():
        assert main[label]['rear_seating_xyz_mm'] == pytest.approx(
            model.b.point(x-model.b.HALF, s, 0).toTuple())
        assert main[label]['barrel_into_panel_direction'] == pytest.approx(
            (-model.b.normal()).toTuple())
    assert all(r['rear_seating_xyz_mm'][2] == 150.
               and r['barrel_into_panel_direction'] == [0., 1., 0.]
               for r in rows if r['panel'].startswith('kicker_'))


def test_each_world_shape_flange_is_behind_rear_face_and_barrel_inside_panel():
    rows = nuts.datums(model)
    parts = nuts.parts(model)
    assert len(parts) == 142
    for row, part in zip(rows, parts, strict=True):
        assert part.name == row['name']
        origin = cq.Vector(*row['rear_seating_xyz_mm'])
        axis = cq.Vector(*row['barrel_into_panel_direction'])
        coords = [(v.Center()-origin).dot(axis) for v in part.shape.Vertices()]
        assert min(coords) == pytest.approx(-nuts.FLANGE_THICKNESS_MM, abs=1.e-7)
        assert max(coords) == pytest.approx(nuts.BARREL_PROJECTION_MM, abs=1.e-7)
        assert max(coords) < model.wide.PANEL
        assert not part.name.startswith(('bolt_', 'screw_'))
