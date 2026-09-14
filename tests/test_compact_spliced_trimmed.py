import cadquery as cq
import pytest

from mini_moonboard import compact_spliced_trimmed as trimmed


def test_half_space_trim_preserves_existing_short_end_and_removes_only_exterior():
    stock = cq.Solid.makeBox(20., 30., 40.)
    cut = trimmed._clip(stock, {'keep_normal_xyz':(0., 0., -1.), 'offset_mm':-25.})
    assert cut.Volume() == pytest.approx(20.*30.*25.)
    assert cut.BoundingBox().zmax == pytest.approx(25.)
    assert cut.cut(stock).Volume() == pytest.approx(0., abs=1.e-8)
    retained = trimmed._clip(stock, {'keep_normal_xyz':(0., 0., -1.), 'offset_mm':-50.})
    assert retained.Volume() == pytest.approx(stock.Volume())


def test_trim_adapter_preserves_installed_bolt_and_axis_definitions():
    assert trimmed.connections is trimmed.installed.connections
    assert trimmed.bolt_interface_point is trimmed.installed.bolt_interface_point
    assert trimmed.LEG_TOP_PROJECTION_MM == 18.
    assert len(trimmed.TRIMMED_NAMES) == 6


def test_bevel_shear_band_uses_both_edges_and_normal_tolerance():
    import math

    from scripts.compact_end_trim_check import shear_band_ends

    # Right end s = 100-q; remote corner at q=50 is outside this hole band.
    profile = [(0., -50.), (150., -50.), (50., 50.), (0., 50.)]
    assert shear_band_ends(profile, -10., 10., 0.) == pytest.approx([0., 90.])
    assert shear_band_ends(profile, -10., 10., 3.) == pytest.approx([3.,90.-3.*math.sqrt(2.)])
    with pytest.raises(ValueError, match='outside'):
        shear_band_ends(profile, -50., 50., 3.)
