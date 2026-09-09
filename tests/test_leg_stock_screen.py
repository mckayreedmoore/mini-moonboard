"""Analytic gross-section checks; no physical capacity assertions."""
import math

import pytest

from fea.leg_stock_screen import STOCK_MM, section, straight_layout, strip_response


def test_current_geometry_comparison_inventory_and_fit():
    from fea.leg_stock_screen import report

    result = report()
    assert result["qualified_for_design"] is False
    assert len(result["rows"]) == 18
    assert len(result["rim_bolts_yz_mm"]) == 4
    rows = {r["stock"]: r for r in result["rows"] if r["foot_extension_from_current_mm"] == 0}
    for name in ("2x6", "2x8", "2x10"):
        assert not rows[name]["direct_straight_attachment_geometry"]["full_bores_inside_side_edges"]
    direct = rows["2x12"]["direct_straight_attachment_geometry"]
    assert direct["full_bores_inside_side_edges"]
    assert direct["centered_width_for_bores_only_mm"] == pytest.approx(239.67611, abs=.001)
    assert direct["minimum_bore_side_ligament_mm"] == pytest.approx(23.03694, abs=.001)
    for name in rows:
        lengths = [r["straight_strip"]["length_mm"] for r in result["rows"] if r["stock"] == name]
        assert lengths == sorted(lengths) and len(set(lengths)) == 3


def test_straight_attachment_fit_is_not_an_assumed_connection():
    points = [(-30., 1000.), (-10., 1000.), (10., 1000.), (30., 1000.)]
    narrow = straight_layout(points, 0., 65., 10.)
    assert narrow["centered_width_for_bores_only_mm"] == pytest.approx(70.)
    assert narrow["minimum_bore_side_ligament_mm"] == pytest.approx(-2.5)
    assert not narrow["full_bores_inside_side_edges"]
    wide = straight_layout(points, 0., 80., 10.)
    assert wide["full_bores_inside_side_edges"]
    assert wide["level_foot_depth_mm"] == pytest.approx(80.)
    shifted = straight_layout([(y+123., z) for y, z in points], 123., 80., 10.)
    assert shifted == wide
    with pytest.raises(ValueError):
        straight_layout([], 0., 80.)


def test_independent_ply_and_stock_axes():
    bonded = section(38.1, 180.)
    independent = section(19.05, 180., 2)
    assert independent["area_mm2"] == bonded["area_mm2"]
    assert independent["in_plane_I_mm4"] == bonded["in_plane_I_mm4"]
    assert independent["out_of_plane_I_mm4"] == pytest.approx(bonded["out_of_plane_I_mm4"]/4)
    assert independent["out_of_plane_S_mm3"] == pytest.approx(bonded["out_of_plane_S_mm3"]/2)
    for width in STOCK_MM.values():
        stock = section(38.1, width)
        assert stock["out_of_plane_I_mm4"]/bonded["out_of_plane_I_mm4"] == pytest.approx(width/180)
        assert stock["in_plane_I_mm4"]/bonded["in_plane_I_mm4"] == pytest.approx((width/180)**3)


def test_response_known_solution_length_and_fixture_scaling():
    props = section(10., 20.)
    a = strip_response(props, 100., 1000.)
    assert a["out_of_plane_unit_cantilever_compliance_mm_per_n"] == pytest.approx(.2)
    assert a["out_of_plane_ideal_euler_n"] == pytest.approx(math.pi**2*1000/6)
    doubled = strip_response(props, 200., 1000.)
    fixed_free = strip_response(props, 100., 1000., 2.)
    for axis in ("out_of_plane", "in_plane"):
        key = axis+"_unit_cantilever_compliance_mm_per_n"
        assert doubled[key] == pytest.approx(8*a[key])
        key = axis+"_ideal_euler_n"
        assert doubled[key] == pytest.approx(a[key]/4)
        assert fixed_free[key] == pytest.approx(a[key]/4)


@pytest.mark.parametrize("bad", [0., -1., math.inf, math.nan])
def test_invalid_dimensions_and_response(bad):
    with pytest.raises(ValueError):
        section(bad, 180.)
    with pytest.raises(ValueError):
        strip_response(section(38.1, 180.), bad)
    with pytest.raises(ValueError):
        strip_response(section(38.1, 180.), 1000., effective_length_factor=bad)
