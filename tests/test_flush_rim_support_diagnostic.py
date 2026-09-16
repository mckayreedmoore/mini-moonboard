"""Support-edge measurement must not substitute terminal projection."""
import pytest

from scripts.flush_rim_support_diagnostic import section_depth


def test_taper_depth_is_measured_at_the_requested_support_station():
    # A triangular end grows from zero to full depth over 20 grain units.
    profile = [(0., 0.), (20., 10.), (100., 10.), (100., 0.)]
    assert section_depth(profile, 5.) == pytest.approx(2.5)
    assert section_depth(profile, 20.) == pytest.approx(10.)
    assert section_depth(profile, 25.) == pytest.approx(10.)
    assert section_depth([profile[i] for i in (0, 1, 3, 2)], 50.) == pytest.approx(10.)
    with pytest.raises(ValueError, match='does not intersect'):
        section_depth(profile, -1.)
