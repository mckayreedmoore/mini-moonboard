"""Necessary repair bounds must not become structural or installation approval."""
import math

import pytest

from fea.round_insert_repair_assessment import damage_screen, dimensional_screen


def test_nominal_drill_depth_includes_point_and_leaves_little_recess_allowance():
    row = dimensional_screen()
    assert row['pilot_diameter_mm'] == pytest.approx(23/64*25.4)
    assert row['idealized_drill_tip_length_mm'] == pytest.approx(2.742, abs=.001)
    assert 0.61 < row['remaining_depth_for_recess_and_extra_clearance_mm'] < .63
    assert row['minimum_gross_receiver_reach_before_recess_mm'] == pytest.approx(11.96975)
    assert row['centered_38_1mm_face_side_ligament_mm'] == pytest.approx(12.9794)
    assert row['effective_thread_engagement_mm'] is None
    assert not row['qualified_for_drilling']


@pytest.mark.parametrize(('diameter', 'offset', 'uncertainty', 'split', 'verified', 'passes'), [
    (4.1402, 0., 0., False, True, True),
    (4.1402, 0., 0., False, False, False),
    (4.1402, 0., 0., True, True, False),
    (9.128125, 0., 0., False, True, False),
    (9.2, 0., 0., False, True, False),
    (6., 1.5, .1, False, True, False),
    (6., 1., .1, False, True, True),
])
def test_damage_boundary_rejects_split_oversize_offcenter_or_unknown(diameter, offset, uncertainty,
                                                                  split, verified, passes):
    row = damage_screen(diameter, offset, uncertainty, split=split, verified=verified)
    assert row['necessary_cleanup_condition_passed'] is passes
    assert not row['qualified_repair']


@pytest.mark.parametrize('value', [-1., math.nan, math.inf])
def test_nonphysical_measurements_rejected(value):
    with pytest.raises(ValueError, match='finite and nonnegative'):
        damage_screen(value, 0., 0.)
