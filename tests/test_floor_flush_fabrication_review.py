"""Guard the independent-error case missed by a nominal spacing comparison."""
import math

from scripts.floor_flush_fabrication_review import build, spacing_budget


def test_front_pair_does_not_survive_recorded_drill_error_envelope():
    result = build()
    assert result['pair_spacing_survives_recorded_independent_drill_errors'] is False
    for side in ('left', 'right'):
        row = result['pair_spacing'][f'base_floor_{side} / base_post_outer_{side}']
        assert math.isclose(row['nominal_margin_mm'], 1.4, abs_tol=1e-8)
        assert math.isclose(row['margin_at_recorded_drill_radius_mm'], -.6, abs_tol=1e-8)
    # Correlated fixture motion cannot replace the documented independent error.
    assert math.isclose(spacing_budget(39.5, 9.525, .7)['margin_at_recorded_drill_radius_mm'], 0., abs_tol=1e-8)
    upper = result['hardware_dimensional_budgets']['upper']
    assert math.isclose(upper['required_full_body_to_first_transition_mm'], 158.9278, abs_tol=1e-8)
