"""Known pressure integrals, whole-window bounds and strict family decisions."""
import hashlib
import math
import sys
from fractions import Fraction as F
from itertools import pairwise
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_cleat_pressure_family as model


def method():
    def ref(name):
        path = 'scripts/'+name+'.py'
        return {'path': path, 'sha256': hashlib.sha256((model.ROOT/path).read_bytes()).hexdigest()}
    return model.base().methods({'rational': ref('eoere_section_patches'), 'normal': ref('eoere_bore_boundary_tractions'),
                                 'stress': ref('eoere_cleat_virtual_work'), 'pi': ref('eoere_curved_bend_field')}, {})


def band(force=(1, 0, 0)):
    return {'local_force_n': list(force), 'radius_mm': 5, 'axial_interval_mm': [-3, 7]}


def actual_pressure(force, radius, length, degrees, normal):
    force=np.asarray(force,dtype=float)
    magnitude = float(np.linalg.norm(force[[0, 2]]))
    beta = math.radians(degrees)
    phi = math.acos(float(np.clip(np.dot(force[[0, 2]], normal)/magnitude, -1, 1)))
    if phi >= beta:
        return 0.
    # Independent high-order quadrature rather than the implementation's exact endpoint formulas.
    nodes, weights = np.polynomial.legendre.leggauss(80)
    integral = beta*np.dot(weights, np.cos(math.pi*nodes/2)*np.cos(beta*nodes))
    return magnitude*math.cos(math.pi*phi/(2*beta))/(radius*length*integral)


@pytest.mark.parametrize('degrees', [30, 45, 60, 90])
def test_exact_endpoint_normalizations_match_independent_integrals(degrees):
    low, high = model.normalization_bounds(degrees, method())
    beta = math.radians(degrees)
    nodes, weights = np.polynomial.legendre.leggauss(100)
    integral = beta*np.dot(weights, np.cos(math.pi*nodes/2)*np.cos(beta*nodes))
    assert low <= high and abs(float(low)-integral) < 1e-14 and abs(float(high)-integral) < 1e-14
    if degrees == 45:
        assert (3*low/2)**2 <= 2 <= (3*high/2)**2


def test_normalization_is_monotone_throughout_the_declared_family():
    nodes, weights = np.polynomial.legendre.leggauss(80)
    integrals=[]
    for degrees in np.linspace(30, 90, 121):
        beta=math.radians(degrees)
        integrals.append(beta*np.dot(weights, np.cos(math.pi*nodes/2)*np.cos(beta*nodes)))
    assert all(a < b for a, b in pairwise(integrals))


@pytest.mark.parametrize('degrees', [30, 45, 60])
def test_exact_shape_bounds_match_direct_angles(degrees):
    for cosine in (F(99, 100), F(39, 40), F(19, 20)):
        lower = model.shape_lower(degrees, cosine)
        actual = math.cos(math.pi*math.acos(float(cosine))/(2*math.radians(degrees)))
        assert abs(float(lower)-actual) < 2e-15


@pytest.mark.parametrize('window', model.WINDOWS)
def test_finite_arc_pressure_lower_covers_every_intermediate_width(window):
    helper=method(); source=band((F(3, 2), 0, F(1, 10)))
    interval=(F(1, 128), F(3, 128))
    certificate=model.certify(source,window,0,interval,helper)
    lower=F(certificate['exact_pressure_lower_mpa'])
    assert lower > 0 and F(certificate['exact_area_lower_mm2']) > 0
    for width in np.linspace(*window,17):
        for t in np.linspace(float(interval[0]),float(interval[1]),9):
            normal=list(map(float,helper.normal(0,F(float(t)))))
            actual=actual_pressure(source['local_force_n'],5,10,float(width),normal)
            assert float(lower) <= actual+1e-15


def test_scenario_scaling_and_tiny_force_are_exact():
    helper=method(); interval=(F(1,128),F(3,128))
    first=model.certify(band(),(30,45),0,interval,helper)
    second=model.certify(band(),(30,45),0,interval,helper,divisor=F(3),load_factor=F(3,2))
    assert F(second['exact_necessary_index_lower']) == F(first['exact_necessary_index_lower'])*F(9,4)
    tiny=model.certify(band((F(1,2**80),0,0)),(30,45),0,interval,helper)
    assert F(tiny['exact_pressure_lower_mpa']) > 0


@pytest.mark.parametrize('bad', [0, -1, True, float('nan'), float('inf')])
def test_nonpositive_or_nonfinite_scenarios_are_rejected(bad):
    with pytest.raises((ValueError,OverflowError)):
        model.certify(band(),(30,45),0,(F(1,128),F(3,128)),method(),divisor=bad)


def test_outside_arc_and_invalid_geometry_cannot_certify():
    helper=method()
    with pytest.raises(ValueError,match='smallest pressure arc'):
        model.certify(band(),(30,45),0,(F(3,4),F(4,5)),helper)
    with pytest.raises(ValueError,match='band geometry'):
        model.certify(band((0,1,1)),(30,45),0,(F(1,128),F(3,128)),helper)
    with pytest.raises(ValueError,match='window'):
        model.certify(band(),(30,90),0,(F(1,128),F(3,128)),helper)
    with pytest.raises(ValueError,match='normalization endpoint'):
        model.normalization_bounds(35,helper)


def test_preserved_boundary_helper_is_private_and_ignores_cached_module(monkeypatch):
    sentinel=SimpleNamespace(sqrt_bounds=lambda _: 'foreign')
    monkeypatch.setitem(sys.modules,'scripts.eoere_cleat_traction_witness',sentinel)
    model.base.cache_clear()
    try:
        module=model.base()
        assert module is not sentinel and module.sqrt_bounds(F(4)) == (F(2),F(2))
        assert sys.modules['scripts.eoere_cleat_traction_witness'] is sentinel
    finally:
        model.base.cache_clear()


def test_exact_unity_and_neighboring_ratios_keep_the_strict_failure_boundary():
    helper=method(); interval=(F(1,128),F(3,128))
    initial=model.certify(band(),(30,45),0,interval,helper)
    ratio=F(initial['exact_necessary_index_lower'])
    for relative,failed in [(F(1),False),(1-F(1,2**80),True),(1+F(1,2**80),False)]:
        strengths={k:v*ratio*relative for k,v in helper.BASE_STRENGTHS.items()}
        adjusted=SimpleNamespace(**{**vars(helper),'BASE_STRENGTHS':strengths})
        row=model.certify(band(),(30,45),0,interval,adjusted)
        assert F(row['exact_necessary_index_lower']) == 1/relative
        assert row['strict_positive_area_reference_failure'] is failed
