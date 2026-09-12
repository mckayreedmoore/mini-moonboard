import hashlib
import json
import random
from pathlib import Path

import pytest

from fea.round_structural_kicker_prying import pitch_screen

PARAMETERS = {'rows_mm': [60., 60., 140., 140.], 'head_n': 304.124546844244,
              'lateral_max_n': 252.35442732711, 'thickness_mm': 18.25625,
              'downward_n': 1200., 'standoff_mm': 100., 'outward_n': 300.,
              'load_height_mm': 150., 'dead_n': 0., 'dead_y_mm': 18.25625/2}


def test_edge_bearing_does_not_remove_projected_hold_prying():
    r = pitch_screen(**PARAMETERS)
    assert r['most_favorable_residual_pitch_nmm'] == 165000.
    assert r['required_top_row_tension_lower_bound_n'] == pytest.approx(786.26, abs=.01)
    assert r['conditional_pitch_equilibrium_impossible']
    assert r['restricted_2d_witness'] is None
    with_dead = pitch_screen(**(PARAMETERS | {'dead_n': 30.}))
    # Unlike the old no-floor force sum, panel dead weight can stabilize pitch.
    assert with_dead['most_favorable_residual_pitch_nmm'] < r['most_favorable_residual_pitch_nmm']


def test_restricted_pitch_witness_recovers_original_wrench():
    p = PARAMETERS | {'standoff_mm': 0., 'dead_n': 30.}
    r = pitch_screen(**p)
    w = r['restricted_2d_witness']
    assert w is not None
    top, bottom = w['top_row_tension_sum_n'], w['bottom_row_tension_sum_n']
    b25, b200 = w['backing_force_at_z25_n'], w['backing_force_at_z200_n']
    assert top+bottom-b25-b200 == pytest.approx(p['outward_n'])
    support = 140*top+60*bottom-25*b25-200*b200+w['floor_y_from_back_mm']*w['floor_upward_n']
    applied = (p['downward_n']*(p['thickness_mm']+p['standoff_mm'])
               +p['outward_n']*p['load_height_mm']+p['dead_n']*p['dead_y_mm'])
    assert support == pytest.approx(applied)
    assert not r['qualified_for_design']


def test_missing_restricted_witness_is_not_general_infeasibility():
    r = pitch_screen(**(PARAMETERS | {'downward_n': 1334.46648457815, 'outward_n': 0.}))
    assert r['restricted_2d_witness'] is None
    assert not r['conditional_pitch_equilibrium_impossible']


def test_bound_does_not_reject_equilibrated_point_force_box_states():
    rng = random.Random(8042)
    p = PARAMETERS | {'outward_n': 0., 'dead_n': 30.}
    checked = 0
    for _ in range(100):
        tension = [rng.uniform(0., p['head_n']) for _ in range(4)]
        shear = [rng.uniform(-p['lateral_max_n'], p['lateral_max_n']) for _ in range(4)]
        depths = [rng.uniform(0., p['thickness_mm']) for _ in range(4)]
        floor = p['downward_n']+p['dead_n']-sum(shear)
        floor_y = rng.uniform(0., p['thickness_mm'])
        contact_z = rng.uniform(0., 30.)
        support = (sum(z*t+q*s for z, t, q, s in zip(p['rows_mm'], tension, depths, shear, strict=True))
                   -contact_z*sum(tension)+floor_y*floor)
        offset = (support-p['dead_n']*p['dead_y_mm'])/p['downward_n']-p['thickness_mm']
        if offset < 0:
            continue
        r = pitch_screen(**(p | {'standoff_mm': offset}))
        assert not r['conditional_pitch_equilibrium_impossible']
        assert r['required_top_row_tension_lower_bound_n'] <= sum(tension[2:])+1.e-8
        checked += 1
    assert checked >= 20


def test_saved_report_has_current_sources_and_separate_false_release_gates():
    r = json.loads(Path('fea/results/round-structural-kicker-prying-v1.json').read_text())
    assert len(r['cases']) == 45
    for path, sha in r['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == sha, path
    assert not r['qualified_for_design']
    assert not r['edge_bearing_resistance_evaluated']
    assert not r['three_dimensional_equilibrium_evaluated']
