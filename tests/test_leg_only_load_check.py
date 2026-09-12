import pytest

from fea.leg_only_load_check import axial_support_force, build


def test_center_load_on_two_support_lines():
    # 1kN at the midpoint: rear vertical reaction 500N; angled leg axial625N.
    assert axial_support_force(downward_n=1000.,horizontal_n=0.,load_y=1000.,
        load_z=2000.,dead_n=0.,dead_y=0.,front_y=0.,rear_y=2000.,
        vertical_cosine=.8) == pytest.approx(625.)


def test_horizontal_force_adds_its_actual_moment():
    args = {'downward_n':1000.,'load_y':1000.,'load_z':2000.,'dead_n':200.,
            'dead_y':500.,'front_y':0.,'rear_y':2000.,'vertical_cosine':.8}
    difference = axial_support_force(horizontal_n=300.,**args)-axial_support_force(horizontal_n=0.,**args)
    assert difference == pytest.approx(375.)


@pytest.mark.parametrize('mass', [-1., float('nan'), float('inf')])
def test_invalid_equipment_allowance_rejected(mass):
    with pytest.raises(ValueError, match='Equipment allowance'):
        build(equipment_mass_kg=mass)
