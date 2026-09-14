"""Prevent relabeled or stale results from becoming passing viewer evidence."""
import copy

import pytest

from scripts import clear_space_exports as exports
from scripts.clear_space_results import floor_bearing_check


def test_viewer_case_rejects_wrong_load_and_stale_assessment(monkeypatch):
    candidate = 'compact-floor-rail-development'
    report = {'candidate':candidate, 'source_sha256':{'fea/kernel.py':'current'},
              'parameters':{'hold':'A12', 'pounds':250.,
                            'force_xyz_n':[0.,300.,-2.*250.*.45359237*9.80665]}}
    assessment = {'candidate':candidate, 'criteria':{'geometry':True}}
    monkeypatch.setattr(exports, 'checks', lambda report, geometry: assessment)
    assert exports.validate_case(report, {}, assessment, candidate, 'a12-rear',
                                 {'fea/kernel.py':'current'}) == assessment
    with pytest.raises(ValueError, match='named load case'):
        exports.validate_case(report, {}, assessment, candidate, 'a12-forward', {})
    with pytest.raises(ValueError, match='differs from current checks'):
        exports.validate_case(report, {}, {'criteria':{'geometry':False}}, candidate, 'a12-rear', {})
    with pytest.raises(ValueError, match='candidate sources'):
        exports.validate_case(report, {}, assessment, candidate, 'a12-rear', {'fea/kernel.py':'changed'})


def test_floor_bearing_uses_cell_area_and_requires_every_contact():
    names = ['base_floor_left', 'base_floor_right']
    report = {'parameters':{'floor_rail_support':{'members':names, 'grid_yx':[2,2]}},
              'physical_connection_forces':{}, 'bearings':[]}
    geometry = {'members':{name:{'width_mm':40., 'profile_sq_mm':[[-500.,0.],[500.,0.]]}
                           for name in names}}
    for name in names:
        for index in range(4):
            contact = f'floor_{name}_{index}'
            report['physical_connection_forces'][contact] = {'first':name,'second':'floor',
                'scalar_normal':[0.,0.,1.], 'normal_stiffness_fraction':.25}
            report['bearings'].append({'name':contact,'compression_force_n':1000. if index == 0 else 0.,
                                      'active':index == 0})
        report['physical_connection_forces'][f'floor_{name}_friction'] = {'first':name,'second':'floor'}
    result = floor_bearing_check(report, geometry)
    assert result['peak_ratio'] == pytest.approx(1000./(10000.*625*.006894757293168361))
    assert len(result['cells']) == 8
    missing = copy.deepcopy(report)
    del missing['physical_connection_forces']['floor_base_floor_left_3']
    with pytest.raises(ValueError, match='inventory differs'):
        floor_bearing_check(missing, geometry)
