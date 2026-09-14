import json
import math
from pathlib import Path

import pytest

from fea.compact_rail_checks import hardware_assumptions


def test_quarter_unc_uses_own_steel_and_catalog_washer_references():
    data = json.loads(Path('docs/floor-rail-2x4-hardware-reference.json').read_text())
    bounds = data['washer_resistance_bounds']
    result = hardware_assumptions(6.35, washer_od_mm=bounds['washer_od_mm'],
        hole_diameter_mm=bounds['washer_hole_diameter_mm'],
        washer_thickness_mm=bounds['washer_thickness_mm'])
    assert result['tensile_area_mm2'] == pytest.approx(.0318*25.4**2)
    assert result['shear_area_mm2'] == pytest.approx(math.pi*(.1887*25.4)**2/4)
    assert result['washers'][0]['seat_diameter_mm'] == pytest.approx(.95*.428*25.4)
    assert result['washers'][0]['outer_diameter_mm'] == pytest.approx(.727*25.4)
    assert result['washers'][0]['hole_diameter_mm'] == pytest.approx(.327*25.4)
    assert result['washers'][0]['thickness_mm'] == pytest.approx(.051*25.4)
    assert 'not a delivered' in result['quarter_reference_basis']['root_scope']


def test_quarter_catalog_minimum_thread_does_not_prove_nut_seating():
    data = json.loads(Path('docs/floor-rail-2x4-hardware-reference.json').read_text())
    wmin, wmax = data['washer_catalog_ranges_mm']['thickness']
    for end, grip, nut_side in (('front',76.2,38.1), ('rear',127.,88.9)):
        length_max = data['bolt_catalog'][end+'_length_mm'][1]
        required = grip+wmax-nut_side/4
        available_seat = grip+2*wmin
        assert required == pytest.approx(data['installation_conditions'][end+'_minimum_full_body_mm'])
        assert available_seat == pytest.approx(data['installation_conditions'][end+'_max_usable_thread_start_with_min_washers_mm'])
        assert length_max-data['bolt_catalog']['minimum_thread_length_mm'] > available_seat
        assert required < available_seat
