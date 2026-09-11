"""Enclosed round passages preserve the fresh timber and retained structural fastener axes."""
from math import pi

import pytest

from mini_moonboard import round_service_frame as model


def test_round_variant_preserves_hardware_and_uses_uncut_source_wood():
    assert model.uncut_wood_parts is model.previous.uncut_wood_parts
    assert sum(isinstance(c, model.timber.PanelScrew) for c in model.connections()) == 56
    assert sum(c.kind == 'bolt' for c in model.connections()) == 8
    assert model.wiring.MEASURED_MAXIMUM_DIAMETER_MM == 12.7
    assert model.wiring.BORE_DIAMETER_MM == 25.4


def test_leg_nuts_face_inside_with_two_washers_and_unchanged_wood_axes():
    from mini_moonboard.selected_hardware import BoltSpec

    original = {c.name: c for c in model.previous.connections()}
    for c in model.connections():
        if isinstance(c, model.timber.PanelScrew):
            assert isinstance(c, model.CountersunkPanelScrew)
            continue
        old = original[c.name]
        if not c.name.startswith('lumber_leg_bolt_'):
            assert c is old
            continue
        assert c.direction.x == (1. if '_left_' in c.name else -1.)
        assert c.start.y == old.start.y and c.start.z == old.start.z
        assert c.grip == old.grip and c.length == old.length
        assert (c.start-old.start).Length == pytest.approx(c.grip+2*model.WASHER)
        shaft, near, far, head, nut = c.components()
        assert near.Volume() > 0. and far.Volume() > 0.
        assert abs(nut.Center().x) < abs(head.Center().x)
        spec = BoltSpec('orientation check', c.length, c.grip, 0.)
        exposed = c.length-c.grip-2*model.WASHER-spec.nut_height_max_mm
        assert exposed >= 2*spec.pitch_mm
        assert c.length-spec.thread_length_reference_mm <= c.grip+2*model.WASHER
        assert shaft.isValid()


def test_passages_are_complete_round_sections_with_front_and_base_ligaments():
    raw = {p.name: p for p in model.uncut_wood_parts()}
    records = model.bore_records()
    assert len(records) == 32
    for row in records:
        cylinder = model.wiring.bore_shape(row)
        removed = raw[row['member']].shape.intersect(cylinder).Volume()
        expected = pi*(row['diameter_mm']/2)**2*(row['member_exit_mm']-row['member_entry_mm'])
        assert removed == pytest.approx(expected, rel=1e-6), row['name']
        assert row['center_n_mm']-row['diameter_mm']/2 == pytest.approx(22.3)
        assert not row['qualified_for_machining']
    bottom = next(row for row in records if row['member'] == 'base_principal_center_right')
    center = model.b.point(bottom['center_x_mm'], bottom['center_s_mm'], bottom['center_n_mm'])
    assert center.z-model.base.HEADER_TOP-bottom['diameter_mm']/2 > 36.
    for part in model.wood_parts():
        assert part.shape.isValid() and len(part.shape.Solids()) == 1, part.name


def test_filleted_route_respects_approximate_path_budget_without_claiming_feeding_approval():
    segments = model.wiring.segments()
    assert len(segments) == 131
    for row in segments:
        assert model.wiring.wire_path(row).Length() == pytest.approx(row['routed_length_mm'])
        assert row['routed_length_mm'] <= row['polyline_length_upper_bound_mm'] <= 304.8
        assert row['within_approximate_budget'] and not row['qualified_for_installation']
        assert not row['additional_slack_accommodation_modeled']


def test_panel_axes_are_mirrored_shared_rows_with_twelve_per_face():
    from collections import Counter

    from mini_moonboard import round_panel_layout as layout

    rows = layout.datums()
    counts = Counter(row['panel'] for row in rows)
    assert counts == {f'main_{band}_{side}': 12 for band in ('lower', 'upper')
                      for side in ('left', 'right')} | {'kicker_left': 4, 'kicker_right': 4}
    indexed = {row['name']: row for row in rows}
    for row in rows:
        other = indexed[row['name'].replace('_left_', '_right_')]
        if '_left_' in row['name']:
            assert row['x'] == -other['x']
            assert row['s'] == other['s']
    for band, offset in (('lower', 0.), ('upper', layout.HALF)):
        for side in ('left', 'right'):
            panel = [r for r in rows if r['panel'] == f'main_{band}_{side}']
            assert [r['s'] for r in panel if r['role'] == 'rim'] == [
                r['s'] for r in panel if r['role'] == 'center']
            assert [r['s']-offset for r in panel if r['role'] == 'rim'] == pytest.approx(layout.FACE_ROWS)
    actual = {c.name: c for c in model.connections() if isinstance(c, model.timber.PanelScrew)}
    for expected in layout.panel_connections():
        assert actual[expected.name].start.toTuple() == expected.start.toTuple()
        assert actual[expected.name].members == expected.members
    assert layout.planar_checks()['service_axis_check_passed']
