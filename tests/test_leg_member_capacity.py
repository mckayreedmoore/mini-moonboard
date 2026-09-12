import pytest

from fea.leg_member_capacity import compression_limit, leg_check


def test_full_stock_unbraced_length_is_more_conservative_than_support_span():
    stock = compression_limit()
    span = compression_limit(effective_length_mm=1612.0462863367457)
    assert stock['compression_n'] < span['compression_n']
    assert stock['NDS_3_9_3_interaction'] == pytest.approx(1.)
    assert not leg_check(stock['compression_n']*1.001)['meets_member_criteria']


def test_eccentricity_reduces_column_capacity_and_net_section_is_actual():
    assert compression_limit()['compression_n'] < compression_limit(
        face_eccentricity_mm=0)['compression_n']
    assert leg_check(1000)['net_area_mm2'] == pytest.approx(4899.18375)
    assert leg_check(1000)['net_centroid_shift_mm'] == pytest.approx(-1.7714886345679017)


def test_invalid_compression_and_unbraced_slenderness():
    with pytest.raises(ValueError):
        leg_check(-1)
    with pytest.raises(ValueError):
        leg_check(float('nan'))
    assert not leg_check(100, effective_length_mm=2000)['meets_member_criteria']


def test_imposed_bending_can_defeat_an_axial_pass():
    axial = leg_check(4000, effective_length_mm=1612.046)
    bent = leg_check(4000, effective_length_mm=1612.046,
                    additional_strong_moment_nmm=400000)
    assert axial['meets_member_criteria']
    assert not bent['meets_member_criteria']
    with pytest.raises(ValueError):
        leg_check(4000, additional_strong_moment_nmm=-1)
