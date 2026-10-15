"""Known kinematics, domain coverage and contact-work controls."""
import ast
import hashlib
import math
from fractions import Fraction as F
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import eoere_normal_patch_trace as model


def method():
    def ref(path):
        return {'path': path, 'sha256': hashlib.sha256((model.ROOT/path).read_bytes()).hexdigest()}
    return model.methods({
        'definition_loader': ref('scripts/eoere_cleat_traction_witness.py'),
        'pure_helpers': {'rational': ref('scripts/eoere_section_patches.py'),
                         'polygon': ref('scripts/eoere_cleat_section_dual.py'),
                         'pi': ref('scripts/eoere_curved_bend_field.py')},
        'polynomial_helper': ref('scripts/eoere_cleat_virtual_work.py'),
        'bernstein_helper': ref('scripts/eoere_cleat_section_reference.py')}, {})


def fixture():
    domain = {'origin_xyz_mm': [0, 0, 2], 'basis_rows_xyz': [[1, 0, 0], [0, 1, 0]],
              'polygon': [[-40, -20], [40, -20], [40, 20], [-40, 20]],
              'holes': [[-12, 0, 5], [12, 0, 5]]}
    timber = {'start': [-50, 0, 0], 'axis': [1, 0, 0], 'stations': [0, 100],
              'index': [list(range(6)), list(range(6, 12))]}
    port = {'point_reference_xyz_mm': [0, 0, 0]}
    return domain, timber, port, list(range(12, 18)), [F(0)]*18, [0, 0, 1]


def test_exact_bilinear_term_from_interpolated_twist_and_eccentric_arm():
    domain, timber, port, indices, q, normal = fixture()
    timber['start'] = [0, 0, 0]; timber['stations'] = [0, 10]
    q[9] = F(1000)
    helper = method()
    polynomial = model.gap_polynomial(model.world_polynomials(domain), timber, port, indices,
                                      q, normal, 'interior', 0, helper.poly)
    assert polynomial == {(1, 1): -F(1, 10)}
    assert helper.poly.evaluate(polynomial, (F(7, 3), F(-4, 5))) == F(14, 75)


def test_uniform_contact_known_force_energy_and_work_conjugate_moments():
    args = fixture(); args[4][14] = -F(1, 10)
    result = model.trace(*args, F(3, 2), method())
    actual_area = 3200-50*math.pi
    actual_force = 1.5*actual_area*.1
    actual_energy = .75*actual_area*.01
    assert F(result['exact_normal_force_upper_n']) == 480
    assert F(result['exact_energy_upper_nmm']) == 24
    witness = result['material_witness']
    assert 0 < float(F(witness['exact_normal_force_lower_n'])) < actual_force < 480
    assert 0 < float(F(witness['exact_energy_lower_nmm'])) < actual_energy < 24
    assert result['force_on_first_xyz_interval_n'] == [['0', '0'], ['0', '0'], ['0', '480']]
    for (lo, hi), radius in zip(result['moment_on_first_about_patch_origin_xyz_interval_nmm'], (20, 40, 0), strict=True):
        assert F(lo) == -480*radius and F(hi) == 480*radius


@pytest.mark.parametrize('gap', [F(0), F(1, 10)])
def test_zero_or_open_gap_has_certified_zero_contact(gap):
    args = fixture(); args[4][14] = gap
    result = model.trace(*args, 1, method())
    assert F(result['exact_normal_force_upper_n']) == F(result['exact_energy_upper_nmm']) == 0
    assert result['material_witness'] is None


def test_small_contact_is_not_erased_by_the_witness_search_gate():
    args = fixture(); args[4][14] = -F(1, 2**100)
    result = model.trace(*args, 1, method())
    assert F(result['exact_energy_upper_nmm']) == F(1600, 2**200) > 0
    assert result['material_witness'] is None


def test_actual_affine_pose_opens_all_centroids_but_closes_material():
    domain, timber, port, indices, q, normal = fixture()
    q[14], q[16] = F(3, 100), F(1)
    helper = method()
    for x in (-20, 20):
        for y in (-10, 10):
            assert model.source_gap((x, y, 2), timber, port, indices, q, normal, helper.poly) >= F(1, 100)
    result = model.trace(domain, timber, port, indices, q, normal, 1, helper)
    witness = result['material_witness']
    assert witness and F(witness['exact_penetration_lower_mm']) > 0
    box = list(map(F, witness['box_xy_mm']))
    for x in box[:2]:
        for y in box[2:]:
            assert F(3, 100)-x/1000 < 0
            assert -40 < x < 40 and -20 < y < 20


def test_three_source_segments_and_endpoint_extensions_partition_exact_area():
    domain, timber, *_ = fixture()
    timber['stations'] = [10, 50, 90]
    regions = model.pieces(domain, timber, method().geometry, method().poly)
    assert {r['mode'] for r in regions} == {'interior'}
    assert len(regions) == 2
    domain['polygon'] = [[-50, -20], [50, -20], [50, 20], [-50, 20]]
    regions = model.pieces(domain, timber, method().geometry, method().poly)
    assert [r['mode'] for r in regions] == ['before', 'interior', 'interior', 'after']
    assert sum(r['outer_area'] for r in regions) == 4000


def test_constant_station_on_a_knot_is_not_double_counted():
    domain, timber, *_ = fixture()
    timber.update(start=[0, 0, 0], axis=[0, 0, 1], stations=[0, 2, 4])
    regions = model.pieces(domain, timber, method().geometry, method().poly)
    assert len(regions) == 1 and regions[0]['segment'] == 0
    assert regions[0]['outer_area'] == 3200


def test_common_rigid_motion_has_exactly_zero_gap_in_every_piece():
    domain, timber, port, indices, q, normal = fixture()
    omega = [F(1, 100), -F(1, 50), F(3, 100)]
    translation = [F(1), F(2), F(3)]
    cross = lambda a, b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    for node, station in zip(timber['index'], timber['stations'], strict=True):
        center = [F(start)+F(axis)*station for start, axis in zip(timber['start'], timber['axis'], strict=True)]
        values = [a+b for a, b in zip(translation, cross(omega, center), strict=True)]+[1000*w for w in omega]
        for index, value in zip(node, values, strict=True): q[index] = value
    values = [a+b for a, b in zip(translation, cross(omega, port['point_reference_xyz_mm']), strict=True)]+[1000*w for w in omega]
    for index, value in zip(indices, values, strict=True): q[index] = value
    result = model.trace(domain, timber, port, indices, q, normal, 1, method())
    assert F(result['exact_energy_upper_nmm']) == 0
    assert all(not r['gap_polynomial_ij_mm'] for r in result['pieces'])


def test_polynomial_enclosures_cover_curvature_and_refuse_degenerate_boxes():
    helper = method()
    polynomial = {(0, 0): F(1, 4), (2, 0): F(-1), (1, 1): F(1, 3)}
    lower, upper = model.polynomial_bounds(polynomial, (-2, 3, -4, 5), helper)
    for x in range(-2, 4):
        for y in range(-4, 6): assert lower <= F(1, 4)-x*x+F(x*y, 3) <= upper
    with pytest.raises(ValueError, match='positive polynomial'):
        model.polynomial_bounds(polynomial, (0, 0, 0, 1), helper)
    with pytest.raises(ValueError, match='quadratic'):
        model.polynomial_bounds({(3, 0): F(1)}, (0, 1, 0, 1), helper)


def test_a_negative_gap_only_in_a_hole_cannot_supply_material_witness():
    region = {'polygon': [(F(-6), F(-6)), (F(6), F(-6)), (F(6), F(6)), (F(-6), F(6))],
              'polynomial': {(0, 0): -F(25), (2, 0): F(1), (0, 2): F(1)}, 'density': F(1)}
    assert model.material_witness(region, [(F(0), F(0), F(5))], method()) is None


def test_source_point_gap_matches_independent_frozen_kinematic_functions():
    env = {'np': np, 'REFERENCE': np.zeros(3), 'ROTATION_SCALE': 1000.,
           'arithmetic': SimpleNamespace(vector=lambda p: np.asarray(p, dtype=float))}
    for path, names in [('scripts/thin_bolted_frame_mechanics.py', ('cross_matrix', 'point_matrix')),
                        ('scripts/thin_bolted_linear_timber_admission.py', ('point_displacement',))]:
        tree = ast.parse((model.ROOT/path).read_bytes())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), path, 'exec'), env)  # noqa: S102 - pure repository definitions
    _, timber, port, indices, _, _ = fixture()
    q = [F(i-4, 17) for i in range(18)]
    normal = [F(0), F(3, 5), F(4, 5)]
    mapping = {'members': [{'member': 'wood', 'reference_start_xyz_mm': timber['start'],
                            'reference_axis_xyz': timber['axis'], 'reference_stations_mm': timber['stations'],
                            'node_dof_indices': timber['index']}]}
    for x in (-55, -50, -20, 0, 50, 55):
        point = [x, 3, 2]
        fit = env['point_matrix'](point, np.asarray(port['point_reference_xyz_mm']))@np.asarray(list(map(float, q[12:])))
        wood = env['point_displacement'](mapping, 'wood', point, np.asarray(list(map(float, q))))
        expected = np.asarray(list(map(float, normal)))@(fit-wood)
        exact = model.source_gap(point, timber, port, indices, q, normal, method().poly)
        assert abs(float(exact)-expected) < 1e-13


def test_float_pose_values_keep_their_exact_stored_binary_values():
    domain, timber, port, indices, _, normal = fixture()
    q = [float(F(i-4, 17)) for i in range(18)]
    helper = method()
    first = model.gap_polynomial(model.world_polynomials(domain), timber, port, indices,
                                 q, normal, 'interior', 0, helper.poly)
    exact = model.gap_polynomial(model.world_polynomials(domain), timber, port, indices,
                                 list(map(F, q)), normal, 'interior', 0, helper.poly)
    assert first == exact and all(isinstance(v, F) for v in first.values())


def test_adjacent_quadratic_traces_are_exactly_continuous_at_a_beam_knot():
    domain, timber, port, _, _, normal = fixture()
    timber.update(stations=[0, 50, 100], index=[list(range(6*i, 6*i+6)) for i in range(3)])
    indices = list(range(18, 24)); q = [F((i*7) % 13-6, 19) for i in range(24)]
    helper = method()
    result = model.trace(domain, timber, port, indices, q, normal, 1, helper)
    assert len(result['pieces']) == 2
    polynomials = [{(i, j): F(v) for i, j, v in p['gap_polynomial_ij_mm']} for p in result['pieces']]
    for y in (-20, -3, 0, 17, 20):
        assert helper.poly.evaluate(polynomials[0], (F(0), F(y))) == helper.poly.evaluate(polynomials[1], (F(0), F(y)))
