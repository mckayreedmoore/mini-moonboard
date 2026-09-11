"""Measured path budget is approximate; open-front channels retain explicit datums."""
import cadquery as cq
import pytest

from fea.screw_insert_repair_reserve import overlaps
from mini_moonboard import horizontal_service_frame as model
from mini_moonboard import horizontal_service_wiring as wiring


def test_route_has_132_lights_and_131_bent_segments_with_explicit_unmodeled_slack():
    segments = wiring.segments()
    assert len(segments) == 131
    assert segments[0]['datums'][0] == 'A1' and segments[-1]['datums'][-1] == 'K12'
    assert all(row['within_approximate_budget'] for row in segments)
    assert all(row['nominal_budget_remaining_mm'] > 60. for row in segments)
    assert all(not row['additional_slack_accommodation_modeled'] for row in segments)
    for row in segments:
        assert wiring.wire_path(row).Length() == pytest.approx(row['routed_length_mm'])
        assert row['approximate_path_budget_mm'] == 304.8
        assert not row['qualified_for_installation']
    parts = wiring.parts()
    assert sum(p.kind == 'light' for p in parts) == 132
    assert sum(p.kind == 'wire' for p in parts) == 131
    assert all(p.shape.isValid() for p in parts)
    reservations = [cq.Solid.makeCylinder(20., 45., wiring.b.point(x-wiring.b.HALF, s, 0.), wiring.b.normal())
                    for x, s in wiring.timber.grid.main_tnut_datums().values()]
    for part in parts:
        assert all(not overlaps(part.shape, tool) for tool in reservations), part.name
    panel_envelope = wiring.b.block(-wiring.b.HALF, wiring.b.HALF, 0., wiring.b.LENGTH,
                                   -wiring.timber.product.FACE_THICKNESS_MM, 0.)
    connectors = [p for p in parts if p.name.startswith(('wire_050_', 'wire_100_'))]
    assert len(connectors) == 2
    for part in connectors:
        assert len(part.shape.Solids()) == 1
        assert not overlaps(part.shape, panel_envelope), part.name


def test_open_channels_include_bottom_and_top_center_crossings():
    records = model.cutout_records()
    assert records
    bottom = [r for r in records if r['member'] == 'base_principal_center_right']
    top = [r for r in records if r['member'] == 'base_principal_center_left']
    assert any(r['datums'] == ['F1', 'G1'] for r in bottom)
    assert any(r['datums'] == ['E12', 'F12'] for r in top)
    for row in records:
        assert row['entry_face'].startswith('front N=0')
        assert row['depth_mm'] == wiring.CHANNEL_DEPTH_MM
        assert row['x1_mm'] > row['x0_mm'] and row['s1_mm'] > row['s0_mm']
        assert not row['qualified_for_machining']
