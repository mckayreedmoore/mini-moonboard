"""Mass/CG integration distinguishes zinc, steel and wood without CAD."""
import pytest

from fea.round_insert_floor import inventory_state


def test_explicit_density_mass_and_centre_are_weighted_once():
    rows = [{'name': name, 'volume_mm3': 1e9, 'density_kg_m3': density,
             'centre_xyz_mm': [x, 0, 0]}
            for name, density, x in [('wood', 600, 0), ('steel', 7850, 10), ('insert', 6700, 20)]]
    state = inventory_state(rows)
    assert state['mass_kg'] == 15150
    assert state['centre_xyz_mm'][0] == pytest.approx((7850*10+6700*20)/15150)
    with pytest.raises(ValueError, match='uniquely'):
        inventory_state(rows + rows[:1])
    rows[0]['volume_mm3'] = -1
    with pytest.raises(ValueError, match='positive finite'):
        inventory_state(rows)
