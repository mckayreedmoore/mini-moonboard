"""Change only the climber loads in the retained six-case input bank.

The movement multiplier and horizontal force are declared study assumptions,
not a standard load combination or a climber rating. Gravity and the existing
25 kg accessory allowance are independent of the climber's mass.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import numpy as np

from scripts.eoere_paired_frame_basis import CASES

GRAVITY = 9.80665
KG_PER_LB = .45359237
BASELINE_DOWNWARD_N = 2. * 250. * KG_PER_LB * GRAVITY


@dataclass(frozen=True)
class LoadParameters:
    weight: float = 250.
    unit: str = 'lb'
    downward_multiplier: float = 2.
    horizontal_force_n: float = 300.

    def __post_init__(self):
        if self.unit not in ('kg', 'lb'):
            raise ValueError('weight unit must be kg or lb')
        for name in ('weight', 'downward_multiplier', 'horizontal_force_n'):
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{name} must be finite and nonnegative')
            if name != 'horizontal_force_n' and value == 0:
                raise ValueError(f'{name} must be positive')
        if not math.isfinite(self.downward_force_n):
            raise ValueError('combined downward force must be finite')

    @property
    def mass_kg(self):
        return self.weight * (KG_PER_LB if self.unit == 'lb' else 1.)

    @property
    def downward_force_n(self):
        return self.downward_multiplier * self.mass_kg * GRAVITY

    def record(self):
        return {
            'input_weight': self.weight, 'input_unit': self.unit,
            'climber_mass_kg': self.mass_kg,
            'downward_multiplier': self.downward_multiplier,
            'climber_downward_force_n': self.downward_force_n,
            'horizontal_force_n': self.horizontal_force_n,
            'self_weight_and_accessory_loads_unchanged': True,
            'standard_load_combination_or_climber_rating': False,
        }


def wrench(loads):
    """Sum force and moment at the global origin in the original row order."""
    return sum((np.r_[r['force_xyz_n'], np.cross(r['point_xyz_mm'], r['force_xyz_n'])]
                for r in loads), np.zeros(6))


def parameterize_case(source, parameters):
    """Return a fresh case; reject inputs outside the authenticated load recipe."""
    case = copy.deepcopy(source)
    if case['case_id'] not in CASES or not case['primary_load_basis']:
        raise ValueError('only the six primary retained cases are supported')
    climbers = [r for r in case['loads'] if r['id'].startswith('climber/')]
    if len(climbers) != 1 or case['hold'] is None:
        raise ValueError('one climber load and its hold descriptor are required')
    row, hold = climbers[0], case['hold']
    if (row['force_xyz_n'] != hold['force_xyz_n']
            or row['point_xyz_mm'] != hold['load_point_xyz_mm']
            or row['body'] != hold['panel'] or row['id'] != 'climber/' + hold['label']):
        raise ValueError('climber load and hold descriptor disagree')
    original = np.asarray(row['force_xyz_n'], dtype=float)
    if original[2] != -BASELINE_DOWNWARD_N or np.linalg.norm(original[:2]) != 300.:
        raise ValueError('source must retain the 250 lb, 2.0, 300 N baseline')
    total = wrench(case['loads'])
    if (not np.allclose(total[:3], case['applied_force_xyz_n'], rtol=0., atol=1e-7)
            or not np.allclose(total[3:], case['applied_moment_about_global_origin_xyz_nmm'],
                               rtol=0., atol=1e-5)):
        raise ValueError('source resultant disagrees with its individual loads')
    force = np.r_[original[:2] / 300. * parameters.horizontal_force_n,
                  -parameters.downward_force_n]
    row['force_xyz_n'] = force.tolist()
    hold['force_xyz_n'] = force.tolist()
    arm = np.asarray(hold['load_point_xyz_mm']) - hold['panel_midplane_xyz_mm']
    hold['moment_about_panel_midplane_xyz_nmm'] = np.cross(arm, force).tolist()
    total = wrench(case['loads'])
    case['applied_force_xyz_n'] = total[:3].tolist()
    case['applied_moment_about_global_origin_xyz_nmm'] = total[3:].tolist()
    return case


def parameterize_inputs(source, parameters):
    """Preserve the geometry, support law, load points and all permanent loads."""
    identifiers = [c['case_id'] for c in source['cases']]
    if len(identifiers) != len(CASES) or set(identifiers) != set(CASES):
        raise ValueError('the complete six-case baseline is required')
    selected = source['case']['case_id']
    if source['case'] != next((c for c in source['cases'] if c['case_id'] == selected), None):
        raise ValueError('selected case disagrees with the case bank')
    data = copy.deepcopy(source)
    data['cases'] = [parameterize_case(c, parameters) for c in source['cases']]
    data['case'] = copy.deepcopy(next(c for c in data['cases'] if c['case_id'] == selected))
    data['scenario']['climber_load_parameters'] = parameters.record()
    return data
