"""Analytic necessary-condition proofs must not overclaim LP infeasibility."""
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fea.rigid_floor_screen import solve
from fea.split_center_floor import necessary_conditions, sources, verify_loaded_sources

FLOOR = [[-1000., -1000., 0.], [1000., -1000., 0.],
         [1000., 1000., 0.], [-1000., 1000., 0.]]


@pytest.mark.parametrize('horizontal,proven', [(499., False), (500., False), (501., True)])
def test_circular_translation_bound(horizontal, proven):
    result = necessary_conditions(FLOOR, [horizontal, 0., -1000., 0., 0., 0.], .5)
    assert result['circular_cone_infeasibility_proven'] is proven
    assert result['circular_friction_limit_n'] == 500.


@pytest.mark.parametrize('offset,proven', [(999., False), (1000., False), (1001., True)])
def test_normal_resultant_sign_and_support_boundary(offset, proven):
    result = necessary_conditions(FLOOR, [0., 0., -1000., -100.*1000., offset*1000., 0.], .5)
    assert result['normal_resultant_xy_mm'] == pytest.approx([offset, 100.])
    assert result['circular_cone_infeasibility_proven'] is proven


def test_inscribed_polygon_failure_does_not_become_circular_proof():
    angle = math.pi/16
    magnitude = 500.*(1.+math.cos(angle))/2
    wrench = [magnitude*math.cos(angle), magnitude*math.sin(angle), -1000., 0., 0., 0.]
    assert not solve(FLOOR, wrench, .5)['polygon_feasible']
    assert not necessary_conditions(FLOOR, wrench, .5)['circular_cone_infeasibility_proven']


def test_passing_necessary_conditions_does_not_qualify_yaw():
    wrench = [0., 0., -1000., 0., 0., 800000.]
    assert not necessary_conditions(FLOOR, wrench, .5)['circular_cone_infeasibility_proven']
    assert not solve(FLOOR, wrench, .5)['polygon_feasible']


@pytest.mark.parametrize('wrench', [[0., 0., 1000., 0., 0., 0.], [0., 0., 0., 0., 0., 100.]])
def test_tension_and_zero_normal_moment_are_proven_impossible(wrench):
    assert necessary_conditions(FLOOR, wrench, .5)['circular_cone_infeasibility_proven']


def test_resultant_check_is_invariant_to_floor_translation():
    shift = [400., -250., 0.]
    points = [[p[i]+shift[i] for i in range(3)] for p in FLOOR]
    original = [0., 0., -1000., 0., 1001000., 0.]
    shifted = [0., 0., -1000., 250000., 1401000., 0.]
    a = necessary_conditions(FLOOR, original, .5)
    b = necessary_conditions(points, shifted, .5)
    assert a['circular_cone_infeasibility_proven'] == b['circular_cone_infeasibility_proven'] is True
    assert b['inward_edge_distances_mm'] == pytest.approx(a['inward_edge_distances_mm'])


def test_explicit_source_closure_covers_model_imports_and_rejects_missing_dependency(monkeypatch):
    subprocess.run([sys.executable, '-c',
                    ('from mini_moonboard import split_center_frame; '
                    'from fea.split_center_floor import sources, verify_loaded_sources; '
                    'verify_loaded_sources(sources())')], check=True)
    monkeypatch.setitem(sys.modules, 'mini_moonboard.unrecorded_dependency',
                        SimpleNamespace(__file__=str(Path('mini_moonboard/unrecorded_dependency.py').resolve())))
    with pytest.raises(ValueError, match='unrecorded_dependency'):
        verify_loaded_sources(sources())
