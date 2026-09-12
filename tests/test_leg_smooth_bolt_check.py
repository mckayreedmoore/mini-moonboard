import pytest

from fea.leg_smooth_bolt_check import moment_interval, prying_screen, smooth_bolt_group

POINTS = [(0., y, z) for y,z in ((-40.,-20.),(-20.,40.),(20.,-40.),(40.,20.))]


def test_force_and_couple_recovery():
    from fea.leg_attachment_check import LEG
    rows = smooth_bolt_group(POINTS,4000.,15000.)['bolts']
    assert [sum(r['force_xyz_n'][k] for r in rows) for k in range(3)] == pytest.approx([4000*x for x in LEG])
    assert sum(p[1]*r['force_xyz_n'][2]-p[2]*r['force_xyz_n'][1] for p,r in zip(POINTS,rows,strict=True)) == pytest.approx(15000.)


def test_moment_boundary():
    interval = moment_interval(POINTS,4000.)
    assert interval is not None
    for m in interval:
        assert smooth_bolt_group(POINTS,4000.,m)['peak_lateral_ratio'] == pytest.approx(1.)
        assert smooth_bolt_group(POINTS,4000.,m*1.01)['peak_lateral_ratio'] > 1.


def test_prying_explicit_amplification():
    one = prying_screen(POINTS,4000.,amplification=1.)
    two = prying_screen(POINTS,4000.,amplification=2.)
    assert two['bolt_tension_n'] == pytest.approx([2*f for f in one['bolt_tension_n']])
    assert two['prying_factor_not_an_established_physical_upper_bound']


def test_round_plate_thickness_scaling():
    from fea.leg_smooth_bolt_check import round_plate_screen
    full = round_plate_screen(2675.,thickness_mm=6.35)
    half = round_plate_screen(2675.,thickness_mm=3.175)
    assert half['plate_bending_ratio'] == pytest.approx(4*full['plate_bending_ratio'])
    assert half['wood_bearing_ratio'] == pytest.approx(full['wood_bearing_ratio'])


def test_prying_recovers_both_moments_for_skew_group():
    # Deliberately correlated Y/Z coordinates, translated away from origin.
    points = [(3.,100.+y,200.+z) for y,z in ((-40.,-45.),(-20.,-25.),
                                           (20.,25.),(40.,45.))]
    result = prying_screen(points,4072.)
    signed = result['unamplified_signed_axial_force_n']
    assert sum(signed) == pytest.approx(0.,abs=1e-8)
    moments = [0.,sum((p[2]-200.)*f for p,f in zip(points,signed,strict=True)),
               -sum((p[1]-100.)*f for p,f in zip(points,signed,strict=True))]
    assert moments == pytest.approx(result['target_couple_xyz_nmm'])
