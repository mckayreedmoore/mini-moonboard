"""Portable surface integrals and refusal controls; no recovered geometry needed."""
import copy
import hashlib
import math

import numpy as np
import pytest

from scripts import eoere_cleat_surface_loads as loads


def geometry():
    width, depth, top, slope = 38.1, 139.7, 277.9420943866905, 1.1917535925939935
    bores = [{'id': str(i), 'origin': [g, 0., v], 'radius_mm': 5.159375,
              'interval_mm': [-width/2, width/2]}
             for i, (g, v) in enumerate(((202.3875, -25.4), (202.3875, 25.4), (60.3, -25.4), (60.3, 25.4)))]
    return {'body': 'cleat', 'frame': np.eye(3).tolist(), 'start': [0., 0., 0.],
            'width_mm': width, 'depth_mm': depth, 'bores': bores,
            'planes': [{'normal': [-1., 0., 0.], 'offset': 0.},
                       {'normal': [1., 0., -slope], 'offset': top},
                       *[{'normal': v, 'offset': d} for v, d in
                         (([0., 1., 0.], width/2), ([0., -1., 0.], width/2),
                          ([0., 0., 1.], depth/2), ([0., 0., -1.], depth/2))]],
            'analytic_finished_volume_mm3': width*depth*top-4*math.pi*5.159375**2*width}


@pytest.mark.parametrize('degrees', loads.ANGLES)
@pytest.mark.parametrize('force', [[200., 0., -40.], [-30., 0., 500.], [0., 0., -100.]])
def test_bore_surface_integrates_original_force_moment_and_rigid_work(degrees, force):
    geom = geometry()
    bore = geom['bores'][0]
    source = {'point_mm': [bore['origin'][0], 11., bore['origin'][2]], 'force_n': force}
    band = loads.bore_band(source, geom, bore)
    angular, weights = np.polynomial.legendre.leggauss(32)
    axial, axial_weights = np.polynomial.legendre.leggauss(3)
    low, high = band['axial_interval_mm']
    beta = math.radians(degrees)
    recovered, moment, work = np.zeros(3), np.zeros(3), 0.
    translation, rotation = np.array([.3, -.2, .4]), np.array([.01, -.04, .03])
    for angle, weight in zip(angular*beta, weights*beta, strict=True):
        for u, wu in zip((low+high)/2+axial*(high-low)/2, axial_weights*(high-low)/2, strict=True):
            traction, radial = loads.bore_traction(band, angle, u, degrees)
            point = np.asarray(bore['origin']) + [0., u, 0.] + bore['radius_mm']*radial
            force_element = traction*bore['radius_mm']*weight*wu
            recovered += force_element
            moment += np.cross(point, force_element)
            work += force_element @ (translation+np.cross(rotation, point))
            assert traction @ radial >= 0.
            assert np.linalg.norm(np.cross(traction, radial)) < 1e-12
    expected_moment = np.cross(source['point_mm'], force)
    assert np.allclose(recovered, force, atol=1e-10, rtol=1e-12)
    assert np.allclose(moment, expected_moment, atol=1e-8, rtol=1e-12)
    assert work == pytest.approx(np.dot(force, translation)+expected_moment@rotation, abs=1e-8)


def test_zero_and_outside_bore_tractions():
    geom = geometry()
    source = {'point_mm': [202.3875, 11., -25.4], 'force_n': [0., 0., 0.]}
    band = loads.bore_band(source, geom, geom['bores'][0])
    assert loads.bore_traction(band, 0., 11., 90)[0].tolist() == [0., 0., 0.]
    source['force_n'] = [100., 0., 0.]
    band = loads.bore_band(source, geom, geom['bores'][0])
    assert loads.bore_traction(band, 1., 11., 30)[0].tolist() == [0., 0., 0.]
    assert loads.bore_traction(band, 0., 100., 30)[0].tolist() == [0., 0., 0.]


@pytest.mark.parametrize('point,force', [([202.4, 11., -25.4], [100., 0., 0.]),
                                       ([202.3875, 11., -25.4], [100., 1., 0.]),
                                       ([202.3875, 19.05, -25.4], [100., 0., 0.])])
def test_bore_rejects_missing_current_surface_mapping(point, force):
    geom = geometry()
    with pytest.raises(ValueError):
        loads.bore_band({'point_mm': point, 'force_n': force}, geom, geom['bores'][0])


def seat():
    geom = geometry()
    action = {'point_mm': [202.3875, -19.05, -25.4], 'force_n': [0., 420., 0.]}
    shaft = {'ends': [{'host': 'cleat', 'washer_id': 'own/nut_washer'}], 'source_axis': {
        'hardware_scenario': {'washer_id_mm': 11.1125, 'washer_od_mm': 26.162}}}
    return action, geom, geom['bores'][0], shaft


def test_uniform_annulus_force_and_first_moments():
    action, geom, bore, shaft = seat()
    row = loads.annular_seat(action, geom, bore, shaft)
    # Integrate the disk difference, retaining the physical hole and outer face.
    x, w = np.polynomial.legendre.leggauss(12)
    total, moment = np.zeros(3), np.zeros(3)
    for radius in (row['outer_radius_mm'], row['inner_radius_mm']):
        sign = 1 if radius == row['outer_radius_mm'] else -1
        for r, wr in zip((x+1)*radius/2, w*radius/2, strict=True):
            for phi in np.arange(32)*2*math.pi/32:
                point = np.array(action['point_mm']) + r*np.array([math.cos(phi), 0., math.sin(phi)])
                force = sign*row['pressure_mpa']*np.array([0., 1., 0.])*r*wr*2*math.pi/32
                total += force
                moment += np.cross(point, force)
    assert np.allclose(total, action['force_n'], atol=1e-10)
    assert np.allclose(moment, np.cross(action['point_mm'], action['force_n']), atol=1e-8)


@pytest.mark.parametrize('fault', ['tension', 'edge', 'bore', 'end'])
def test_seat_refuses_unsupported_annulus(fault):
    action, geom, bore, shaft = seat()
    if fault == 'tension':
        action['force_n'][1] *= -1
    elif fault == 'edge':
        shaft['source_axis']['hardware_scenario']['washer_od_mm'] = 140.
    elif fault == 'bore':
        shaft['source_axis']['hardware_scenario']['washer_id_mm'] = 9.
    else:
        shaft['ends'].append(copy.deepcopy(shaft['ends'][0]))
    with pytest.raises(ValueError):
        loads.annular_seat(action, geom, bore, shaft)


def test_uniform_body_load_uses_finished_centroid_not_gross_midpoint():
    geom = geometry()
    width, depth = geom['width_mm'], geom['depth_mm']
    top = geom['planes'][1]
    q, w = np.polynomial.legendre.leggauss(5)
    volume, moment = 0., np.zeros(3)
    for v, weight in zip(q*depth/2, w*depth/2, strict=True):
        height = top['offset']-top['normal'][2]*v
        dv = width*height*weight
        volume += dv
        moment += dv*np.array([height/2, 0., v])
    for bore in geom['bores']:
        dv = math.pi*bore['radius_mm']**2*width
        volume -= dv
        moment -= dv*np.array(bore['origin'])
    action = {'point_mm': (moment/volume).tolist(), 'force_n': [0., 0., -7.191322212453437]}
    row = loads.uniform_gravity(action, geom)
    assert row['volume_mm3'] == pytest.approx(volume, abs=1e-8)
    assert np.allclose(np.array(row['body_force_n_per_mm3'])*volume, action['force_n'], atol=1e-12)
    action['point_mm'][0] += 1.
    with pytest.raises(ValueError, match='centroid'):
        loads.uniform_gravity(action, geom)


def test_source_capture_rejects_mutation_and_conflicting_binding(tmp_path, monkeypatch):
    monkeypatch.setattr(loads, 'ROOT', tmp_path)
    p = tmp_path/'source.json'
    p.write_bytes(b'{"a": 1}')
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    ref = {'path': 'source.json', 'sha256': digest}
    assert loads.read(ref, {}) == {'a': 1}
    with pytest.raises(ValueError, match='contradictory'):
        loads.read(ref, {'source.json': '0'*64})
    p.write_bytes(b'{"a": 2}')
    with pytest.raises(ValueError, match='source changed'):
        loads.read(ref, {})
