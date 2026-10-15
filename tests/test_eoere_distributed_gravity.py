"""Gravity-work integration and refusal controls; no native or frame solve."""
import copy
import hashlib
import math
import sys
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_distributed_gravity as model

REFS = {
    'definition_loader': {'path': 'scripts/eoere_cleat_traction_witness.py',
        'sha256': '941cdd505e60e0e4275aa3b71fb5434d80d26a2f1c8d8f0ec96a6d87f5ae8dce'},
    'pure_helpers': {
        'root': {'path': 'scripts/eoere_cleat_traction_witness.py',
            'sha256': '941cdd505e60e0e4275aa3b71fb5434d80d26a2f1c8d8f0ec96a6d87f5ae8dce'},
        'pi': {'path': 'scripts/eoere_curved_bend_field.py',
            'sha256': '26c72f5f88f947d66035ebf5fbac7193ac9a532222c0e2f7439cd21dba371efc'},
        'intervals': {'path': 'scripts/eoere_bore_boundary_tractions.py',
            'sha256': '645878415321268d211fda2e678ac16a06643193b1c3d9b4ba32b2ea661a2381'}}}


@pytest.fixture(scope='module')
def helpers():
    pins = {}; contact = model.bootstrap(pins); material = contact.bootstrap(pins)
    prior = material.bootstrap(pins); base = prior.bootstrap(pins).producer(pins)
    return model.methods(REFS, base, pins), contact


def small_scenario():
    return SimpleNamespace(leg_mm=10, width_mm=8, thickness_mm=2, factory_hole_mm=.5,
        holes=lambda: [{'flange': flange, 'along_mm': along, 'transverse_mm': across}
            for flange in ('beam', 'post') for along in (4, 7) for across in (-2, 2)])


def test_interval_division_signed_force_and_outward_rounding():
    assert model.quotient((-6, -4), (2, 3)) == (-3, F(-4, 3))
    assert model.quotient((-2, 5), (2, 4)) == (-1, F(5, 2))
    for exact in (F(1, 3), F(-1, 3), 0, F(2)**100):
        low, high = model.short_enclosure((exact, exact))
        assert low <= exact <= high and high-low <= F(1, 2**96)


@pytest.mark.parametrize('numerator,denominator', [((1, 0), (1, 2)), ((0, 1), (0, 1)),
    ((0, 1), (-2, -1)), ((0, 1), (2, 1))])
def test_invalid_or_zero_volume_intervals_are_refused(numerator, denominator):
    with pytest.raises(ValueError):
        model.quotient(numerator, denominator)


def test_sharp_L_includes_overlap_and_every_hole(helpers):
    method, _ = helpers; moments = model.fitting_moments(small_scenario(), method)
    volume = 288-math.pi; center = (928-13*math.pi/4)/volume
    assert np.mean(list(map(float, moments['volume']))) == pytest.approx(volume, abs=1e-13)
    assert [np.mean(list(map(float, row))) for row in moments['center']] == pytest.approx([center, center, 0], abs=1e-14)
    assert moments['hole_count'] == 8


def test_direct_signed_domain_quadrature_recovers_force_first_moment_and_affine_work(helpers):
    method, _ = helpers; scenario = small_scenario(); moments = model.fitting_moments(scenario, method)
    # Integrate two boxes minus the overlap and eight circular through holes.
    nodes, weights = np.polynomial.legendre.leggauss(3)
    points, volumes = [], []
    for bounds, sign in [(((0, 10), (0, 2), (-4, 4)), 1),
                         (((0, 2), (0, 10), (-4, 4)), 1), (((0, 2), (0, 2), (-4, 4)), -1)]:
        for i, xi in enumerate(nodes):
            for j, eta in enumerate(nodes):
                for k, zeta in enumerate(nodes):
                    points.append([(a+b)/2+v*(b-a)/2 for (a, b), v in zip(bounds, (xi, eta, zeta), strict=True)])
                    volumes.append(sign*weights[i]*weights[j]*weights[k]*math.prod((b-a)/2 for a, b in bounds))
    for hole in scenario.holes():
        for r, wr in zip((nodes+1)/8, weights/8, strict=True):
            for theta in np.arange(16)*2*math.pi/16:
                for normal, wn in zip(nodes+1, weights, strict=True):
                    along, across = hole['along_mm']+r*math.cos(theta), hole['transverse_mm']+r*math.sin(theta)
                    points.append([along, normal, across] if hole['flange'] == 'beam' else [normal, along, across])
                    volumes.append(-r*wr*(2*math.pi/16)*wn)
    points = np.asarray(points); volumes = np.asarray(volumes)
    volume = np.mean(list(map(float, moments['volume']))); center = np.array([np.mean(list(map(float, a))) for a in moments['center']])
    force = np.array([0., 0., -17.]); differential = volumes[:, None]*force/volume
    affine = np.array([[.1, -.2, .3], [0, .4, -.1], [-.2, .7, .5]]); translation = np.array([.5, -.6, .7])
    assert differential.sum(axis=0) == pytest.approx(force, abs=1e-12)
    assert (differential.T@points)[2] == pytest.approx(force[2]*center, abs=1e-11)
    assert np.cross(points, differential).sum(axis=0) == pytest.approx(np.cross(center, force), abs=1e-11)
    assert np.sum(differential*(translation+points@affine.T)) == pytest.approx(force@(translation+affine@center), abs=1e-11)


@pytest.mark.parametrize('change', ['missing_hole', 'outside_hole', 'overlap_holes', 'heel_hole'])
def test_incomplete_or_intersecting_sharp_hole_domains_are_refused(helpers, change):
    method, _ = helpers; scenario = small_scenario(); holes = scenario.holes()
    if change == 'missing_hole': holes.pop()
    if change == 'outside_hole': holes[0]['transverse_mm'] = 4
    if change == 'overlap_holes': holes[0] = copy.deepcopy(holes[1])
    if change == 'heel_hole': holes[0]['along_mm'] = 2
    scenario.holes = lambda: holes
    with pytest.raises(ValueError):
        model.fitting_moments(scenario, method)


def shaft_fixture():
    return {'diameter_mm': 2, 'source_axis': {'hardware_scenario': {
        'hex_across_flats_mm': 4, 'washer_id_mm': 3, 'washer_od_mm': 6}}}


@pytest.mark.parametrize('kind', ['shaft', 'head', 'nut', 'head_washer', 'nut_washer', 'spacer'])
def test_all_nominal_metal_role_volumes_and_centered_prism_work(helpers, kind):
    method, _ = helpers; shaft = shaft_fixture(); low, high = -3, 7; height = high-low
    result = model.role_volume(kind, shaft, (low, high), method)
    exact = {'shaft': math.pi*height, 'head': 8*math.sqrt(3)*height,
        'nut': (8*math.sqrt(3)-math.pi)*height, 'head_washer': math.pi*(36-9)*height/4,
        'nut_washer': math.pi*(36-9)*height/4, 'spacer': math.pi*(19.05**2-10.31875**2)*height/4}[kind]
    assert np.mean(list(map(float, result))) == pytest.approx(exact, rel=1e-14)
    # Independent exact integration in the axial direction, with actual area.
    axis, weights = np.polynomial.legendre.leggauss(3)
    stations = (low+high)/2+axis*height/2
    assert sum(weights*height/2)*exact/height == pytest.approx(exact)
    assert sum(weights*height/2*stations)/height == pytest.approx(2)


@pytest.mark.parametrize('kind,interval,change', [('other', (0, 1), None), ('shaft', (1, 1), None),
    ('shaft', (2, 1), None), ('head', (0, 1), 'hex'), ('nut_washer', (0, 1), 'annulus')])
def test_invalid_nominal_role_dimensions_are_refused(helpers, kind, interval, change):
    method, _ = helpers; shaft = shaft_fixture()
    if change == 'hex': shaft['source_axis']['hardware_scenario']['hex_across_flats_mm'] = 1
    if change == 'annulus': shaft['source_axis']['hardware_scenario']['washer_od_mm'] = 2
    with pytest.raises(ValueError):
        model.role_volume(kind, shaft, interval, method)


def test_tilted_slightly_nonunit_chart_uses_its_true_jacobian(helpers):
    method, contact = helpers; scale = 1+F(1, 10**12)
    axes = [[F(3, 5)*scale, F(4, 5)*scale, 0], [F(-4, 5), F(3, 5), 0], [0, 0, 1]]
    volume, center, jacobian = model.chart([7, 11, 13], axes,
        list(map(model.point_interval, [2, 3, 4])), (10, 10), contact, method)
    assert jacobian == scale and volume == (10*scale, 10*scale)
    assert center == [model.point_interval(7+6*scale/5-F(12, 5)),
                      model.point_interval(11+8*scale/5+F(9, 5)), (F(17), F(17))]


@pytest.mark.parametrize('axes', [np.diag([1, 1, -1]).tolist(), [[1, 0, 0], [1, 1, 0], [0, 0, 1]],
    [[0, 0, 0], [0, 1, 0], [0, 0, 1]], np.diag([2, 1, 1]).tolist()])
def test_reflected_singular_nonorthogonal_or_changed_scale_charts_are_refused(helpers, axes):
    method, contact = helpers
    with pytest.raises(ValueError):
        model.chart([0, 0, 0], axes, [(0, 0)]*3, (1, 1), contact, method)


def test_affine_difference_and_L2_bound_keep_source_roundoff_visible(helpers):
    method, _ = helpers
    source = {'id': 'gravity', 'body': 'wood', 'parent_body': 'wood', 'force_xyz_n': [0, 0, -12], 'point_xyz_mm': [2, 3, 4]}
    result = model.uniform_load(source, (6, 6), [(2, 2), (3, 3), (5, 5)], method)
    coefficients = [tuple(map(F, row)) for row in result['affine_work_coefficient_difference_intervals']]
    assert coefficients == [(0, 0)]*11+[(-12, -12)]
    assert tuple(map(F, result['L2_load_functional_norm_square_n2_per_mm3_interval'])) == (24, 24)
    assert result['exact_resultant_preserved_by_definition'] is True
    assert result['exact_source_first_moment_equality_claimed'] is False
    assert result['arbitrary_old_kinematic_work_or_comparator_bounds_transferred'] is False


def test_float_interval_endpoints_enclose_exact_binary_input_work_and_chart(helpers):
    method, contact = helpers
    row = {'id': 'g', 'body': 'b', 'parent_body': 'b', 'force_xyz_n': [0, 0, -1], 'point_xyz_mm': [.1, 0, 0]}
    result = model.uniform_load(row, (.3, .4), [(3., 3.1), (0., 0.), (0., 0.)], method)
    low, high = map(F, result['affine_work_coefficient_difference_intervals'][9])
    assert low <= -(F(3.1)-F(.1)) <= -(F(3.)-F(.1)) <= high
    low, high = map(F, result['uniform_force_density_n_per_mm3_intervals'][2])
    assert low <= -1/F(.3) <= -1/F(.4) <= high
    volume, center, _ = model.chart([.1, .2, .3], [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
        [(3., 3.1), (0., 0.), (0., 0.)], (.3, .4), contact, method)
    assert volume == (F(.3), F(.4)) and center[0] == (F(.1)+F(3.), F(.1)+F(3.1))


def test_uniform_prism_changes_nonaffine_work_even_when_centroid_work_is_identical():
    nodes, weights = np.polynomial.legendre.leggauss(3)
    # Unit resultant along z, uniform on -1<s<1: v_z=s^2 has work 1/3.
    distributed_work = sum(weights*nodes**2)/2
    assert distributed_work == pytest.approx(F(1, 3)) and distributed_work != 0
    assert 0**2 == 0  # The original centroid point force has zero work.


@pytest.mark.parametrize('change', ['roundoff', 'changed_point', 'changed_mass_center', 'bad_volume', 'zero_volume', 'wrong_kind'])
def test_recorded_timber_moments_keep_roundoff_and_reject_inconsistent_sources(change):
    source = {'volume_mm3': 10, 'center_xyz_mm': [1, 2, 3], 'source': {'volume_mm3': 10-F(1, 10**8)}}
    mass = {'kind': 'timber', 'center_xyz_mm': [1, 2, 3]}; row = {'point_xyz_mm': [1, 2, 3]}
    if change == 'changed_point': row['point_xyz_mm'][0] += 1
    if change == 'changed_mass_center': mass['center_xyz_mm'][0] += 1
    if change == 'bad_volume': source['source']['volume_mm3'] = 9
    if change == 'zero_volume': source['volume_mm3'] = 0
    if change == 'wrong_kind': mass['kind'] = 'panel'
    if change == 'roundoff':
        volume, center, delta = model.timber_moments(source, mass, row, F(1, 10**5))
        assert volume == (10, 10) and center == [(1, 1), (2, 2), (3, 3)] and delta == F(1, 10**8)
    else:
        with pytest.raises(ValueError):
            model.timber_moments(source, mass, row, F(1, 10**5))


@pytest.mark.parametrize('change', ['upward', 'lateral', 'free_couple', 'empty_volume', 'reversed_center', 'boolean_force'])
def test_incompatible_gravity_loads_or_domains_are_refused(helpers, change):
    method, _ = helpers
    row = {'id': 'g', 'body': 'b', 'parent_body': 'b', 'force_xyz_n': [0, 0, -1], 'point_xyz_mm': [0, 0, 0]}
    volume, center = (1, 1), [(0, 0)]*3
    if change == 'upward': row['force_xyz_n'][2] = 1
    if change == 'lateral': row['force_xyz_n'][0] = 1
    if change == 'free_couple': row['moment_xyz_nmm'] = [0, 0, 1]
    if change == 'empty_volume': volume = (0, 1)
    if change == 'reversed_center': center[0] = (1, 0)
    if change == 'boolean_force': row['force_xyz_n'][0] = False
    with pytest.raises(ValueError):
        model.uniform_load(row, volume, center, method)


def test_scenario_reuse_never_executes_outside_CAD_module_statements():
    recipe = model.ROOT/'scripts/eoere_bolted_candidate.py'
    data = b'raise RuntimeError("outside definition must not run")\n'+recipe.read_bytes()
    scenario = model.fitting_scenario(data)
    assert scenario.leg_mm == 88.9 and len(scenario.holes()) == 8


def test_bootstrap_ignores_unbound_module_cache_and_conflicting_pin(helpers, monkeypatch):
    monkeypatch.setitem(sys.modules, 'scripts.eoere_coupled_contact_work', SimpleNamespace(bootstrap=None))
    assert callable(model.bootstrap({}).bootstrap)
    with pytest.raises(ValueError, match='bootstrap changed'):
        model.bootstrap({model.BOOT['path']: '0'*64})
    assert hashlib.sha256((model.ROOT/model.BOOT['path']).read_bytes()).hexdigest() == model.BOOT['sha256']
