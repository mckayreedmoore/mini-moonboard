import math

from fea.leg_attachment_check import LEG
from fea.leg_bolt_pattern_search import (
    bolt_forces,
    candidate,
    context,
    cross_row_minimum,
    group_factor,
    lateral,
    pattern,
)
from fea.leg_completion_assessment import foot_joint_moment


def test_force_group_preserves_force_and_moment():
    points = pattern((0., 1000., 1500.), 90., 60., 4., -8.)
    forces = bolt_forces(points, 4100., -83000.)
    centre = [sum(p[k] for p in points)/4 for k in range(3)]
    assert math.isclose(sum(f[1] for f in forces), 4100*LEG[1])
    assert math.isclose(sum(f[2] for f in forces), 4100*LEG[2])
    moment = sum((p[1]-centre[1])*f[2]-(p[2]-centre[2])*f[1]
                 for p, f in zip(points, forces, strict=True))
    assert math.isclose(moment, -83000.)


def test_diameter_changes_group_stiffness_and_row_spacing():
    assert group_factor(.625, 90.) < group_factor(.5, 90.) < 1
    assert math.isclose(cross_row_minimum(12.7), 39.6875)
    assert math.isclose(cross_row_minimum(15.875), 43.65625)


def test_original_pattern_and_moved_moment():
    source, centre, leg = context()
    result = candidate(.375, 70., 50., 0., 0., source, centre, leg)
    assert result is not None
    for original, actual in zip(source['full_contact_cases'], result['cases'], strict=True):
        assert math.isclose(original['joint_moment_nmm'], actual['joint_moment_nmm'], abs_tol=1e-6)
    case = source['full_contact_cases'][0]
    moved = [centre[0], centre[1]+10., centre[2]]
    moment = foot_joint_moment(compression_n=case['axial_compression_n'], top=moved,
        foot=case['foot_pressure_resultant_xyz_mm'], leg_mass_kg=leg['mass_kg'],
        leg_centre=leg['centre_xyz_mm'])
    assert math.isclose(moment-case['joint_moment_nmm'], -10*case['axial_compression_n']*LEG[2])


def test_larger_bolt_original_pattern_rejected_on_actual_load_directions():
    source, centre, leg = context()
    assert candidate(.5, 70., 50., 0., 0., source, centre, leg) is None
    assert candidate(.625, 70., 50., 0., 0., source, centre, leg) is None


def test_cross_row_spacing_includes_slender_and_stocky_limits():
    assert math.isclose(cross_row_minimum(6.35), 31.75)
    assert math.isclose(cross_row_minimum(25.4), 63.5)


def test_larger_diameter_does_not_inherit_smaller_bolt_wood_bearing():
    forces = [tuple(1000*v for v in LEG)]*4
    small, large = (lateral(forces, d, 70.) for d in (.375, .625))
    # Remove group action to isolate the diameter-dependent bearing effect.
    small_reference = small['bolts'][0]['reference_n']/small['group_factor']
    large_reference = large['bolts'][0]['reference_n']/large['group_factor']
    gain = large_reference/small_reference
    assert 1 < gain < 1.6  # Fixed Fe incorrectly gives a 5/3 gain here.
