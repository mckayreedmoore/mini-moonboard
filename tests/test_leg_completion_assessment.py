import pytest

from fea.leg_attachment_check import LEG
from fea.leg_completion_assessment import foot_joint_moment, splitting_screen


def test_axis_aligned_foot_zero_moment_without_gravity():
    top = [0.,0.,1000.]
    foot = [0.,-1000*LEG[1]/LEG[2],0.]
    assert foot_joint_moment(compression_n=4000,top=top,foot=foot,
        leg_mass_kg=0,leg_centre=top) == pytest.approx(0.,abs=1e-8)
    shifted = [0.,foot[1]+70.,0.]
    assert foot_joint_moment(compression_n=4000,top=top,foot=shifted,
        leg_mass_kg=0,leg_centre=top) == pytest.approx(70*4000*LEG[2])


def test_gravity_foot_and_centre_moments_both_count():
    assert foot_joint_moment(compression_n=0,top=[0,0,1000],foot=[0,400,0],
        leg_mass_kg=5,leg_centre=[0,200,500]) == pytest.approx(5*9.80665*200)


def test_splitting_does_not_cancel_opposite_bolt_forces():
    one = splitting_screen([[0,1000,0]])
    two = splitting_screen([[0,1000,0],[0,-1000,0]])
    assert two['ratio'] == pytest.approx(2*one['ratio'])
