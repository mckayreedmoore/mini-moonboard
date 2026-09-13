"""Reduced receiver tabs require explicit per-connection geometry intent."""
import pytest

from scripts.compact_thick_geometry import bearing_length_check


def test_reduced_tab_does_not_silently_accept_unexpected_lost_bearing():
    overrides = {'knee_bolt':{'knee':44.45}}
    assert bearing_length_check(44.45,88.9,'knee_bolt','knee',overrides) == (44.45,True)
    assert bearing_length_check(44.45,88.9,'knee_bolt','host',overrides) == (88.9,False)
    assert bearing_length_check(40.,88.9,'knee_bolt','knee',overrides) == (44.45,False)
    assert bearing_length_check(88.9,88.9,'upper_bolt','host',overrides) == (88.9,True)


@pytest.mark.parametrize('expected',[0.,-1.,float('nan'),float('inf'),100.])
def test_invalid_tab_specification_rejected(expected):
    with pytest.raises(ValueError):
        bearing_length_check(44.45,88.9,'bolt','knee',{'bolt':{'knee':expected}})
