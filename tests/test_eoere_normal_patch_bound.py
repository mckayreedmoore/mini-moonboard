"""Independent controls for local centroid/continuous normal-contact bounds."""
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

from scripts import eoere_normal_patch_bound as model


def method():
    refs = {
        'definition_loader': 'scripts/eoere_cleat_traction_witness.py',
        'rational': 'scripts/eoere_section_patches.py',
        'polygon': 'scripts/eoere_cleat_section_dual.py',
        'pi': 'scripts/eoere_curved_bend_field.py',
    }
    def ref(path):
        return {'path': path, 'sha256': model.hashlib.sha256((model.ROOT/path).read_bytes()).hexdigest()}
    return model.methods({'definition_loader': ref(refs['definition_loader']),
                          'pure_helpers': {k: ref(v) for k, v in refs.items() if k != 'definition_loader'}}, {})


POLYGON = [(-40, -20), (40, -20), (40, 20), (-40, 20)]
SAMPLES = [(-20, -10), (-20, 10), (20, -10), (20, 10)]
HOLES = [(-12, 0, 5), (12, 0, 5)]


def test_exact_positive_area_witness_independently_reconstructed():
    result = model.witness(POLYGON, HOLES, SAMPLES, F(3, 2), method())
    q = list(map(F, result['gap_coefficients_1_x_y']))
    box = list(map(F, result['inner_material_box_xy_mm']))
    points = [(x, y) for x in box[:2] for y in box[2:]]
    # Evaluate independently, without the producer's value/inside helpers.
    def gap(p):
        return q[0]+q[1]*p[0]+q[2]*p[1]
    assert min(map(gap, SAMPLES)) == F(1, 100)
    assert all(gap(p) < -F(1, 200) for p in points)
    assert all(-40 < x < 40 and -20 < y < 20 for x, y in points)
    for hx, hy, radius in HOLES:
        dx = max(box[0]-hx, hx-box[1], F(0))
        dy = max(box[2]-hy, hy-box[3], F(0))
        assert dx*dx+dy*dy > radius*radius
    area = (box[1]-box[0])*(box[3]-box[2])
    penetration = -max(map(gap, points))
    assert F(result['exact_box_area_mm2']) == area > 0
    assert F(result['exact_distributed_energy_lower_nmm']) == F(3, 4)*area*penetration**2 > 0
    assert F(result['exact_distributed_normal_force_lower_n']) == F(3, 2)*area*penetration > 0
    # Every finite positive spring coefficient still multiplies zero closure.
    for scale in (F(1, 10), F(1, 2), F(2), F(10), F(10**100)):
        assert sum(scale*max(-gap(p), 0)**2 for p in SAMPLES) == 0


def test_scaling_is_exact_and_can_be_arbitrarily_infinitesimal():
    first = model.witness(POLYGON, HOLES, SAMPLES, 3, method())
    scale = F(1, 2**60)
    tiny = model.witness(POLYGON, HOLES, SAMPLES, 3, method(), F(1, 100)*scale)
    assert list(map(F, tiny['gap_coefficients_1_x_y'])) == [scale*F(x) for x in first['gap_coefficients_1_x_y']]
    assert F(tiny['exact_distributed_energy_lower_nmm']) == scale**2*F(first['exact_distributed_energy_lower_nmm'])
    assert F(tiny['exact_distributed_normal_force_lower_n']) == scale*F(first['exact_distributed_normal_force_lower_n'])


def test_affine_coordinate_translation_preserves_control():
    offset = (F(1000, 3), F(-7000, 11))
    shift = lambda p: (F(p[0])+offset[0], F(p[1])+offset[1])
    moved = model.witness(list(map(shift, POLYGON)), [(*shift(h[:2]), h[2]) for h in HOLES],
                          list(map(shift, SAMPLES)), 2, method())
    original = model.witness(POLYGON, HOLES, SAMPLES, 2, method())
    assert F(moved['exact_distributed_energy_lower_nmm']) == F(original['exact_distributed_energy_lower_nmm'])
    assert F(moved['exact_box_area_mm2']) == F(original['exact_box_area_mm2'])


@pytest.mark.parametrize('bad', [0, -1, float('inf'), float('nan'), True])
def test_invalid_stiffness_and_opening_refused(bad):
    with pytest.raises(ValueError):
        model.witness(POLYGON, HOLES, SAMPLES, bad, method())
    with pytest.raises(ValueError):
        model.witness(POLYGON, HOLES, SAMPLES, 1, method(), bad)


def test_void_samples_and_clockwise_or_concave_domains_refused():
    with pytest.raises(ValueError, match='material interior'):
        model.witness(POLYGON, HOLES, [(-12, 0)], 1, method())
    with pytest.raises(ValueError, match='counterclockwise'):
        model.witness(POLYGON[::-1], HOLES, SAMPLES, 1, method())
    with pytest.raises(ValueError, match='counterclockwise'):
        model.witness([(-40, -20), (40, -20), (0, 0), (40, 20), (-40, 20)], HOLES, SAMPLES, 1, method())


def test_hole_intersecting_the_box_refuses_a_false_certificate():
    with pytest.raises(ValueError, match='entirely in material'):
        model.witness(POLYGON, [(36, 0, 4)], SAMPLES, 1, method())


def test_captured_helpers_do_not_require_candidate_assets_or_import_old_solvers():
    import sys

    before = set(sys.modules)
    helper = method()
    assert helper.moments([(F(0), F(0)), (F(4), F(0)), (F(0), F(3))], F(0)) == (F(6), F(8), F(6))
    assert not any(n.startswith(('cadquery', 'scripts.eoere_cleat_section_reference')) for n in set(sys.modules)-before)
    assert Path(model.ROOT/'scripts/eoere_section_patches.py').exists()


def patch_fixture():
    normal = np.array([0., .6, .8])
    basis = np.array([[1., 0., 0.], [0., .8, -.6]])
    origin = np.array([1000., -2000., 3000.])
    def world(point):
        return (origin+np.asarray(point)@basis).tolist()
    edges = [{'curve_type': 'LINE', 'length_mm': float(np.linalg.norm(np.subtract(a, b))),
              'vertex_xyz_mm': [world(a), world(b)]}
             for a, b in zip(POLYGON, POLYGON[1:]+POLYGON[:1], strict=True)]
    edges += [{'curve_type': 'CIRCLE', 'length_mm': 10*model.math.pi,
               'center_xyz_mm': world(hole[:2])} for hole in HOLES]
    signature = {'edge_signatures': edges}
    patch = {'trimmed_region_geometry': signature, 'centroid_xyz_mm': origin.tolist(),
             'normal_from_second_to_first_xyz': normal.tolist(), 'area_mm2': 3200-50*model.math.pi,
             'cells': [{'point_xyz_mm': world(p)} for p in SAMPLES]}
    return resign(patch)


def resign(patch):
    patch['trimmed_region_signature_sha256'] = model.hashlib.sha256(model.json.dumps(
        patch['trimmed_region_geometry'], sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return patch


def test_rotated_translated_signature_retains_holes_area_and_witness():
    data = model.geometry(patch_fixture(), method())
    assert len(data['polygon']) == 4 and len(data['holes']) == 2
    assert data['area_identity_error_mm2'] < 1e-9
    assert data['centroid_identity_error_mm'] < 1e-9
    proof = model.witness(data['polygon'], data['holes'], data['samples'], 1, method())
    assert F(proof['exact_box_area_mm2']) > 100
    assert proof['finite_local_multiplicative_upper_exists'] is False


def test_signature_drift_partial_holes_and_nonconvex_edges_are_refused():
    patch = patch_fixture()
    patch['trimmed_region_geometry']['edge_signatures'][0]['length_mm'] += 1
    with pytest.raises(ValueError, match='signature changed'):
        model.geometry(patch, method())
    patch = patch_fixture()
    patch['trimmed_region_geometry']['edge_signatures'][-1]['length_mm'] /= 2
    with pytest.raises(ValueError, match='full circular'):
        model.geometry(resign(patch), method())
    patch = patch_fixture()
    patch['trimmed_region_geometry']['edge_signatures'][0]['vertex_xyz_mm'][0][0] += 10
    with pytest.raises(ValueError, match='convex hull'):
        model.geometry(resign(patch), method())


def test_captured_definitions_ignore_cached_sibling_helper(monkeypatch):
    import sys
    from types import SimpleNamespace

    def forbidden(*args, **kwargs):
        pytest.fail('cached helper must not execute')
    sentinel = SimpleNamespace(clip=forbidden, moments=forbidden)
    monkeypatch.setitem(sys.modules, 'scripts.eoere_cleat_section_dual', sentinel)
    result = model.witness(POLYGON, HOLES, SAMPLES, 1, method())
    assert F(result['exact_distributed_energy_lower_nmm']) > 0
    assert sys.modules['scripts.eoere_cleat_section_dual'] is sentinel
