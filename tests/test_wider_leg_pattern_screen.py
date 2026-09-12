import math

from fea.leg_attachment_check import LEG
from fea.leg_bolt_pattern_search import context
from fea.wider_leg_pattern_screen import load_cases


def test_original_depth_reproduces_original_full_contact_equilibrium():
    source, _, leg = context()
    for actual, original in zip(load_cases(139.7, source, leg), source['full_contact_cases'], strict=True):
        assert math.isclose(actual['compression_n'], original['axial_compression_n'], rel_tol=1e-10)
        assert math.isclose(actual['foot'][1], original['foot_pressure_resultant_xyz_mm'][1], abs_tol=1e-8)


def test_wider_foot_and_extra_mass_preserve_global_moment():
    source, _, leg = context()
    narrow, wide = (load_cases(d, source, leg) for d in (139.7, 234.95))
    assert math.isclose(wide[1]['foot'][1]-wide[0]['foot'][1], 234.95/(3*LEG[2]))
    front = -270.95
    for cases in (narrow, wide):
        assert math.isclose(cases[0]['compression_n']*(cases[0]['foot'][1]-front),
                            cases[1]['compression_n']*(cases[1]['foot'][1]-front))
    assert wide[0]['compression_n']*(wide[0]['foot'][1]-front) > narrow[0]['compression_n']*(narrow[0]['foot'][1]-front)
