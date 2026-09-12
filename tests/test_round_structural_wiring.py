"""Centered passages preserve route endpoints and fit the provisional pitch."""
import cadquery as cq
import pytest

from mini_moonboard import round_structural_frame as model
from mini_moonboard import round_structural_wiring as wiring


def test_centered_routes_preserve_led_order_and_fit_pitch():
    historical = wiring.previous.segments()
    current = wiring.segments()
    assert len(current) == len(historical) == 131
    assert wiring.previous.ROUTING_DEPTH_MM == 35.
    assert wiring.previous.GEOMETRY['routing_plane_N'] == 35.
    for old, new in zip(historical, current, strict=True):
        assert new['datums'] == old['datums']
        assert new['route_local_mm'][0] == old['route_local_mm'][0]
        assert new['route_local_mm'][-1] == old['route_local_mm'][-1]
        assert all(p[2] == 69.85 for p in new['route_local_mm'][1:3])
        assert new['within_approximate_budget']
        assert new['polyline_length_upper_bound_mm'] <= new['approximate_path_budget_mm']
        assert not new['qualified_for_installation']
    assert max(r['routed_length_mm'] for r in current) < 282.


def test_fillets_finish_before_wood_entries_in_both_route_directions():
    segments = {tuple(row['datums']): row for row in wiring.segments()}
    bores = model.bore_records()
    assert len(bores) == 32
    for bore in bores:
        assert bore['center_n_mm'] == pytest.approx(69.85)
        assert bore['diameter_mm'] == pytest.approx(38.1)
        points = [cq.Vector(*p) for p in segments[tuple(bore['datums'])]['route_local_mm']]
        corners = list(wiring.previous._corners(points))
        # Tangent points bound the straight part of the route after rounding.
        straight_start, straight_end = corners[0][2], corners[1][0]
        axis = 'y' if bore['axis_local'] == 'S' else 'x'
        low, high = sorted((getattr(straight_start, axis), getattr(straight_end, axis)))
        assert low < bore['member_entry_mm']
        assert high > bore['member_exit_mm']
