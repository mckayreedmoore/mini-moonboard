"""Regression checks for the actual rearward-widened fresh-stock candidate."""
import json
from pathlib import Path

import pytest

from mini_moonboard import wider_leg_frame as model


def test_actual_pattern_fits_fixed_front_rim_and_plate_envelopes():
    _, _, along, across, rim = model.axes()
    normal = model.previous.b.normal()
    extent = model.PLATE_WIDTH/2*(abs(along.dot(normal))+abs(across.dot(normal)))
    rows = model.drilling_records()
    assert len(rows) == 24
    for row in rows:
        if row['member'].startswith('base_side_'):
            assert extent < row['depth_coordinate_mm'] < model.DEPTH-extent
        else:
            assert model.PLATE_WIDTH/2 < row['depth_coordinate_mm'] < model.DEPTH-model.PLATE_WIDTH/2
            assert model.TOP_EXTENSION-row['grain_station_mm'] >= 7*12.7
    assert abs(along.dot(rim)) < 1


def test_six_complete_catalog_stacks_per_leg_and_other_axes_preserved():
    old = {c.name: c for c in model.previous.connections() if not c.name.startswith('lumber_leg_bolt_')}
    new = {c.name: c for c in model.connections() if not c.name.startswith('lumber_leg_bolt_')}
    assert old == new
    bolts = [c for c in model.connections() if isinstance(c, model.WiderLegBolt)]
    assert len(bolts) == 12
    assert all(c.diameter == 12.7 and c.length == 127 for c in bolts)
    assert all(len(c.components()) == 8 for c in bolts)


def test_export_records_actual_fresh_bores_and_complete_plate_support():
    report = json.loads(Path('docs/wider-leg-review/review.json').read_text())
    assert report['nominal_geometry_pass'], report['failures']
    assert len(report['bore_witnesses']) == 24
    assert all(r['remaining_wood_in_bore_mm3'] < .01 for r in report['bore_witnesses'])
    assert all(r['unsupported_mm3'] < .01 for r in report['plate_support'])
    assert all(r['blank_mm'][1:] == pytest.approx([184.15, 38.1]) for r in report['changed_members'])
    assert report['strength_qualified'] is False
    assert report['selected_variant_changed'] is False


def test_local_cut_inventory_includes_panel_screw_near_third_bolt():
    rows = model.local_rim_cut_records()
    extra = [r for r in rows if not r['is_leg_bolt']]
    assert {r['connection'] for r in extra} == {'round_panel_upper_left_rim_2', 'round_panel_upper_right_rim_2'}
    assert all(r['depth_extent_inside_rim_mm'] == pytest.approx([0, 33.54375]) for r in extra)
    assert len([r for r in rows if r['is_leg_bolt']]) == 12
