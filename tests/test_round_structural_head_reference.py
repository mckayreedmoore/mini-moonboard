"""Check published table landmarks, applicability bounds and current provenance."""
import math

import pytest

from fea import round_structural_head_reference as head


@pytest.mark.parametrize('diameter,thickness,gravity,tabulated', [
    (.250, .5, .42, 48), (.312, 23/32, .42, 86),
    (.500, 1.5, .50, 339), (.234, 1.5, .42, 52),
])
def test_matches_independent_published_table_landmarks(diameter, thickness, gravity, tabulated):
    assert round(head.head_pull_through_lbf(diameter, thickness, gravity)) == tabulated


def test_capacity_caps_at_thickness_limit_without_jump():
    diameter = .32
    boundary = 2.5*diameter
    value = head.head_pull_through_lbf(diameter, boundary, .42)
    assert head.head_pull_through_lbf(diameter, 1.5, .42) == value
    assert head.head_pull_through_lbf(diameter, boundary-1e-9, .42) < value


@pytest.mark.parametrize('args', [
    (.233, .5, .42), (.501, .5, .42), (.32, .31, .42),
    (.32, 1.501, .42), (.32, .5, .6),
    (math.nan, .5, .42), (.32, math.inf, .42), (.32, .5, math.nan),
])
def test_no_extrapolation_or_nonfinite_inputs(args):
    with pytest.raises(ValueError):
        head.head_pull_through_lbf(*args)


def test_current_reference_stays_conditional_and_uses_reduced_thickness():
    result = head.references()
    assert result['reference_head_n'] == pytest.approx(304.124547, abs=1e-5)
    assert result['basis']['net_thickness_in'] == pytest.approx(.55875)
    assert result['reference_head_n'] < result['full_thickness_comparison_n']
    for key in ('qualified_for_design', 'current_demands_evaluated',
                'installation_adjustments_applied', 'actual_head_seat_verified',
                'governing_edition_reconciled'):
        assert result[key] is False
    assert 'fea/round_structural_head_reference.py' in result['source_sha256']
    assert result['actual_head_geometry_applicability_unresolved'] is True


def test_rejects_stale_geometry_before_assigning_head_reference(monkeypatch):
    def stale():
        raise ValueError('Stale geometry producer')
    monkeypatch.setattr(head, 'screw_references', stale)
    with pytest.raises(ValueError, match='Stale geometry'):
        head.references()
