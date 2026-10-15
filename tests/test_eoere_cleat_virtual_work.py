"""Known-answer checks for the compatible volume virtual-work method."""
from fractions import Fraction as F

import numpy as np
import pytest

from fea.floor_recess_mesh import shape20
from fea.wood_joint_reduced_members import shape20_derivatives
from scripts import eoere_cleat_virtual_work as vw


def cube(warp=F(0)):
    return [[F(1, 2)+F(x, 2)+warp*(1-x*x) for x in natural] for natural in vw.NATURAL]


def test_symbolic_shapes_match_the_existing_canonical_element():
    polynomials = vw.shape_polynomials()
    for i, natural in enumerate(vw.NATURAL):
        assert [vw.evaluate(p, natural) for p in polynomials] == [int(i == j) for j in range(20)]
    for point in ((F(1, 3), F(-2, 5), F(3, 7)), (0, 0, 0), (-1, 1, -1)):
        assert sum(vw.evaluate(p, point) for p in polynomials) == 1
        assert np.allclose([float(vw.evaluate(p, point)) for p in polynomials], shape20(point), rtol=0, atol=1e-14)


@pytest.mark.parametrize('warp', [F(0), F(1, 100)])
@pytest.mark.parametrize('component,sign,expected', [(0, 1, F('8.5')), (0, -1, F(17)),
    (1, 1, F('.4')), (1, -1, F('2.2')), (2, 1, F('.4')), (2, -1, F('2.2'))])
def test_exact_uniform_physical_normal_strains_on_affine_and_warped_cells(warp, component, sign, expected):
    positions = cube(warp)
    virtual = [[sign*p[i] if i == component else F(0) for i in range(3)] for p in positions]
    result = vw.element_bound(positions, virtual, vw.BASE_STRENGTHS)
    assert result['lower'] == result['upper'] == expected


@pytest.mark.parametrize('first,second,expected', [(0, 1, F('2.144')), (0, 2, F('2.144')), (1, 2, F('.8'))])
def test_engineering_shear_has_the_correct_work_conjugate_factor(first, second, expected):
    positions = cube(F(1, 100))
    virtual = [[p[second] if i == first else F(0) for i in range(3)] for p in positions]
    result = vw.element_bound(positions, virtual, vw.BASE_STRENGTHS)
    assert result['lower'] == result['upper'] == expected


@pytest.mark.parametrize('mode', range(6))
def test_all_rigid_modes_have_exactly_zero_internal_work(mode):
    positions = cube(F(1, 100))
    if mode < 3:
        virtual = [[F(i == mode) for i in range(3)] for p in positions]
    else:
        axis = mode-3
        virtual = []
        for p in positions:
            unit = [F(i == axis) for i in range(3)]
            virtual.append([unit[1]*p[2]-unit[2]*p[1], unit[2]*p[0]-unit[0]*p[2], unit[0]*p[1]-unit[1]*p[0]])
    result = vw.element_bound(positions, virtual, vw.BASE_STRENGTHS)
    assert result['lower'] == result['upper'] == 0


def test_nonseparable_or_inverted_geometry_cannot_be_silently_affinized():
    positions = cube()
    positions[8][1] += F(1, 100)
    with pytest.raises(ValueError, match='nonseparable'):
        vw.separable_geometry(positions)
    with pytest.raises(ValueError, match='nonpositive'):
        vw.separable_geometry(cube(F(1)))


def test_exact_bernstein_reconstruction_and_convex_enclosure():
    polynomial = {(3, 1, 0): F(2, 3), (0, 2, 2): F(-5, 7), (0, 0, 0): F(1)}
    coefficients = vw.bernstein(polynomial)
    for point in ((F(1, 3), F(2, 5), F(-1, 7)), (-1, -1, -1), (1, 1, 1)):
        value = vw.evaluate(polynomial, point)
        t = [(x+1)/2 for x in map(F, point)]
        result = F(0)
        for coefficient, index in zip(coefficients, vw.product(range(4), repeat=3), strict=True):
            basis = 1
            for k, x in zip(index, t, strict=True):
                basis *= vw.math.comb(3, k)*x**k*(1-x)**(3-k)
            result += coefficient*basis
        assert value == result
        assert min(coefficients) <= value <= max(coefficients)


def test_complete_cell_profile_and_cylinder_intersection_are_checked():
    geometry = {'planes': [{'normal': [1, 0, 0], 'offset': 4}, {'normal': [-1, 0, 0], 'offset': 0}],
                'bores': [{'axis': [0., 1., 0.], 'origin': [2, 0, 0], 'radius_mm': F(2, 5), 'interval_mm': [-1, 1]}]}
    assert vw.sound_box([(F(12, 5), 3), (-1, 1), (F(-1, 10), F(1, 10))], geometry)
    assert not vw.sound_box([(F(23, 10), 3), (-1, 1), (F(-1, 10), F(1, 10))], geometry)
    assert not vw.sound_box([(3, 5), (-1, 1), (1, 2)], geometry)


def test_variable_sign_normal_strain_is_enclosed_and_exact_after_splitting():
    positions = cube()
    virtual = [[(p[0]-F(1, 2))**2, F(0), F(0)] for p in positions]
    result = vw.element_bound(positions, virtual, vw.BASE_STRENGTHS)
    exact = (vw.BASE_STRENGTHS['tension_parallel']+vw.BASE_STRENGTHS['compression_parallel'])/4
    assert result['lower'] <= exact <= result['upper']
    totals = []
    for start in (F(0), F(1, 2)):
        positions = [[start+p[0]/2, p[1], p[2]] for p in cube()]
        virtual = [[(p[0]-F(1, 2))**2, F(0), F(0)] for p in positions]
        cell = vw.element_bound(positions, virtual, vw.BASE_STRENGTHS)
        assert cell['lower'] == cell['upper']
        totals.append(cell['upper'])
    assert sum(totals) == exact


def test_tiny_nonzero_virtual_strain_is_retained_exactly():
    factor = F(1, 10**80)
    positions = cube()
    virtual = [[F(0), factor*p[1], F(0)] for p in positions]
    result = vw.element_bound(positions, virtual, vw.BASE_STRENGTHS)
    assert result['lower'] == result['upper'] == factor*vw.BASE_STRENGTHS['tension_perpendicular']


def test_boundary_mask_has_no_free_nodes_for_one_element():
    free, boundary = vw.support_nodes([list(range(20))], [True])
    assert free == [] and boundary == list(range(20))


@pytest.mark.parametrize('count', [2, 3])
def test_duplicate_cells_cannot_hide_the_exterior_boundary(count):
    with pytest.raises(ValueError, match='duplicate'):
        vw.support_nodes([list(range(20))]*count, [True]*count)


def test_internal_face_requires_opposite_canonical_sides():
    first, second = list(range(20)), list(range(20, 40))
    for i, natural in enumerate(vw.NATURAL):
        if natural[0] == 1:
            second[i] = first[i]
    with pytest.raises(ValueError, match='opposite canonical sides'):
        vw.support_nodes([first, second], [True, True])


def test_conforming_multicell_mask_has_zero_exterior_and_excluded_cell_traces():
    nodes, elements, selected = {}, [], []
    for cell in vw.product(range(3), repeat=3):
        element = []
        for natural in vw.NATURAL:
            key = tuple(2*c+n+1 for c, n in zip(cell, natural, strict=True))
            element.append(nodes.setdefault(key, len(nodes)))
        elements.append(element)
        selected.append(cell != (0, 0, 0))
    free, boundary = vw.support_nodes(elements, selected)
    assert free and boundary
    assert nodes[(4, 4, 4)] in free
    assert not set(free).intersection(elements[0])
    values = np.zeros((len(nodes), 3))
    values[free] = np.arange(1, 1+3*len(free)).reshape(-1, 3)
    face_points = [(0., 0.), (.31, -.73), (-1., 1.)]
    for cell, element, chosen in zip(vw.product(range(3), repeat=3), elements, selected, strict=True):
        if not chosen:
            assert not np.any(values[element])
            continue
        for axis, side in vw.product(range(3), (-1, 1)):
            neighbor = tuple(c+(side if i == axis else 0) for i, c in enumerate(cell))
            exterior = any(c not in range(3) for c in neighbor) or neighbor == (0, 0, 0)
            if exterior:
                for other in face_points:
                    point = list(other)
                    point.insert(axis, side)
                    assert np.array_equal(shape20(point) @ values[element], np.zeros(3))


def test_coupled_work_matches_independent_volume_and_boundary_integrals_on_warped_cell():
    # The independent oracle uses the existing numerical derivative kernel and
    # the divergence theorem, not the producer's symbolic Piola polynomials.
    positions, virtual = [], []
    for r, s, t in vw.NATURAL:
        positions.append([1+2*r+F(1, 10)*(1-r*r), -2+3*s-F(1, 5)*(1-s*s),
                          3+5*t+F(1, 4)*(1-t*t)])
        virtual.append([2*r+3*s-t+r*s+r*r*t, -r+4*s+2*t+s*s*r,
                        3*r-2*s+5*t+t*t*s])
    stress = np.array([[2., -.7, 1.1], [-.7, -3., .9], [1.1, .9, .4]])
    xyz, displacements = np.asarray(positions, dtype=float), np.asarray(virtual, dtype=float)
    gauss, weights = np.polynomial.legendre.leggauss(5)
    volume_work, boundary_work = 0., 0.
    for indices in vw.product(range(5), repeat=3):
        point = gauss[list(indices)]
        derivatives = shape20_derivatives(point)
        jacobian = xyz.T @ derivatives
        gradient = displacements.T @ derivatives @ np.linalg.inv(jacobian)
        volume_work += np.sum(stress*gradient)*np.linalg.det(jacobian)*np.prod(weights[list(indices)])
    for axis, side in vw.product(range(3), (-1, 1)):
        first, second = (axis+1) % 3, (axis+2) % 3
        for i, j in vw.product(range(5), repeat=2):
            point = np.zeros(3)
            point[axis], point[first], point[second] = side, gauss[i], gauss[j]
            jacobian = xyz.T @ shape20_derivatives(point)
            area_vector = side*np.cross(jacobian[:, first], jacobian[:, second])
            displacement = shape20(point) @ displacements
            boundary_work += displacement @ stress @ area_vector * weights[i]*weights[j]
    fields, _ = vw.strain_power(positions, virtual)
    integrals = [8*sum(vw.bernstein(p), F(0))/64 for p in fields]
    exact_work = sum(value*F(str(coefficient)) for value, coefficient in
                     zip(integrals, [2., -3., .4, -.7, 1.1, .9], strict=True))
    assert np.isclose(volume_work, float(exact_work), rtol=1e-13, atol=1e-10)
    assert np.isclose(boundary_work, float(exact_work), rtol=1e-13, atol=1e-10)
    assert all(any(vw.evaluate(p, point) for point in ((0, 0, 0), (F(1, 3), F(2, 5), F(-3, 7)))) for p in fields)


@pytest.mark.parametrize('strain,expected', [
    (['-.25', '.3', '-.2', '-.7', '1.2', '-2'], '4.25'),
    (['.1', '.3', '.2', '-.7', '1.2', '-2'], '2.5728'),
    (['0', '-2', '.2', '-.7', '1.2', '-2'], '4.4'),
    (['0', '0', '0', '0', '0', '-2'], '1.6'),
])
def test_mixed_sign_support_matches_independent_strength_axis_vertices(strain, expected):
    assert vw.support(tuple(map(F, strain)), vw.BASE_STRENGTHS) == F(expected)


def test_stored_binary_midpoints_are_not_rounded_or_snapped():
    positions = np.asarray(cube(), dtype=float)
    for index, natural in enumerate(vw.NATURAL):
        if natural[0] == 0:
            positions[index, 0] = np.nextafter(.5, 1.)
    result = vw.separable_geometry(positions)
    assert result['coordinates'][0][vw.ZERO] == F.from_float(np.nextafter(.5, 1.))
    assert result['coordinates'][0][(2, 0, 0)] != 0


def test_virtual_work_respects_asymmetric_normal_strengths():
    # A compressive admissible stress doing negative work on an expansive
    # trial cannot be declared a failure by taking the absolute work.
    assert vw.necessary_index(-17, F('8.5')) == 0
    assert vw.necessary_index(17, 17) == 1
    assert vw.necessary_index(18, 17) > 1
    assert vw.necessary_index(0, 0) == 0
    with pytest.raises(ValueError, match='load-balance'):
        vw.necessary_index(F(1, 10**30), 0)
